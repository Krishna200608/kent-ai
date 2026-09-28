---
name: chromadb-rubric-tester
description: Validates ChromaDB persistent vector index over 74,513 Kent rubrics, executing golden retrieval benchmark queries, measuring latency, and recording collection metrics in Context/DATA.md.
triggers:
  - "build_embeddings.py"
  - "chromadb"
  - "rubric embeddings"
  - "vector store"
  - "semantic search test"
author: "kent-ai-team"
version: "1.0.0"
---

# ChromaDB Rubric Tester Skill

## Overview

In `kent-ai`, Phase 2 establishes dense vector semantic retrieval across the entire 74,513 Kent Repertory rubric corpus.
The vector search architecture consists of:
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, unit normalized)
- **Index Engine**: ChromaDB persistent collection with HNSW index
- **Distance Metric**: Cosine distance ($d \in [0, 2]$, similarity $= 1.0 - d$)
- **Collection Name**: `kent_rubrics`
- **Storage Location**: `data/embeddings/kent_rubrics/`
- **Core Wrapper**: `src/search/vector_store.py` (`RubricVectorStore`)
- **Embedder Utility**: `src/search/embedder.py` (`RubricEmbedder`)

This skill validates index health, measures query latency in milliseconds, checks retrieval rankings against golden clinical queries, and updates `Context/DATA.md`.

---

## Benchmarking & Validation Routine

Run the automated ChromaDB inspection and golden query benchmark:

```powershell
.venv\Scripts\python.exe -c @'
import time
import sys
from pathlib import Path
from src.search.vector_store import RubricVectorStore

print("=== ChromaDB Rubric Index Validation ===")

store = RubricVectorStore()
count = store.count()
print(f"Collection Name : {store.collection_name}")
print(f"Distance Metric : {store.distance_metric}")
print(f"Storage Path    : {store.persist_dir}")
print(f"Total Rubrics   : {count:,} / 74,513")

if count != 74513:
    print(f"\n[WARNING] Collection count {count:,} does not match expected 74,513!")
else:
    print("[PASS] Collection count verified at exactly 74,513 rubrics.")

# Benchmark Golden Queries
benchmarks = [
    {
        "query": "splitting headache from sun",
        "expected_substrings": ["HEAD", "PAIN", "sun"],
        "target_desc": "HEAD > PAIN > Sun, from exposure to",
    },
    {
        "query": "fear of being alone in the dark",
        "expected_substrings": ["MIND", "FEAR", "alone"],
        "target_desc": "MIND > FEAR > alone, of being",
    },
]

print("\n=== Executing Golden Retrieval Benchmarks ===")

all_passed = True
for b in benchmarks:
    q = b["query"]
    t0 = time.perf_counter()
    results = store.query(q, top_k=5)
    latency_ms = (time.perf_counter() - t0) * 1000

    print(f"\nBenchmark Query: \"{q}\"")
    print(f"Target Concept : {b['target_desc']}")
    print(f"Latency        : {latency_ms:.2f} ms (SLA < 500ms)")

    matched_top5 = False
    print("| Rank | Distance | Cosine Sim | Rubric Path | Remedies |")
    print("|---|---|---|---|---|")
    for rank, r in enumerate(results, 1):
        dist = r.get("distance", 0.0)
        sim = r.get("similarity", 0.0)
        path = r.get("path", "")
        rems = r.get("remedy_count", 0)
        print(f"| {rank} | {dist:.4f} | {sim:.4f} | `{path}` | {rems} |")

        # Verify semantic relevance in top 5
        path_lower = path.lower()
        if all(sub.lower() in path_lower for sub in b["expected_substrings"]):
            matched_top5 = True

    if matched_top5:
        print(f"[PASS] Relevant rubric retrieved in Top-5 for \"{q}\".")
    else:
        print(f"[FAIL] Expected semantic concept not found in Top-5 for \"{q}\"!")
        all_passed = False

if all_passed:
    print("\n[ALL BENCHMARKS PASSED] ChromaDB index is production ready.")
else:
    print("\n[BENCHMARK WARNING] Retrieval did not meet strict golden criteria.")
'@
```

---

## Golden Query Target Specifications

| Query | Expected Target Concept / Keywords | Target Section | Minimum Cosine Similarity | SLA Latency |
|---|---|---|---|---|
| `"splitting headache from sun"` | `HEAD > PAIN ... > sun, from exposure to` or `HEAD > SUNSTROKE` | Section 3 (`HEAD`) | $\ge 0.65$ | $< 500$ ms |
| `"fear of being alone in the dark"` | `MIND > FEAR > alone, of being` or `MIND > FEAR > dark` | Section 1 (`MIND`) | $\ge 0.65$ | $< 500$ ms |

---

## Automatic Sync to `Context/DATA.md`

Whenever index metrics are confirmed or updated, record the verified numbers into `Context/DATA.md` under `## Embeddings & Vector Index (Phase 2)`:

```markdown
## Embeddings & Vector Index (Phase 2)

| Property | Value |
|---|---|
| Collection Name | `kent_rubrics` |
| Record Count | 74,513 rubrics |
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Embedding Dimensions | 384 |
| Distance Metric | Cosine (HNSW space) |
| On-Disk Location | `data/embeddings/kent_rubrics/` |
| Retrieval Latency | ~45–120 ms (top-K=20) |
```

---

## Safety Gates & Regression Alerts

If any of the following conditions occur during testing:
1. **Count Discrepancy**: Collection record count $< 74,513$.
   - **Action**: Alert `[REGRESSION WARNING]: ChromaDB collection incomplete. Run python scripts/build_embeddings.py --batch-size 256 to rebuild.`
2. **Missing Golden Targets**: Golden query fails to return relevant rubrics in the Top 5.
   - **Action**: Verify that query embeddings are properly normalized and check that HNSW cosine distance metadata was initialized properly.
3. **High Latency**: Query latency $> 500$ ms on repeated calls.
   - **Action**: Ensure persistent client is reused rather than recreating the client on every request.
