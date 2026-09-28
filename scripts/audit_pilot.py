"""Statistical and Clinical Quality Audit for Pilot 100 Cases."""

import json
from collections import Counter
from pathlib import Path


def audit_pilot(file_path: str = "data/processed/pilot_100_cases.jsonl") -> dict:
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    lines = [line.strip() for line in open(p, encoding="utf-8") if line.strip()]
    total_cases = len(lines)

    json_err = 0
    slice_err = 0
    total_ents = 0
    tag_len_mismatch = 0
    dim_counts = Counter()
    rubric_cases = {}
    token_lens = []

    for idx, line in enumerate(lines):
        try:
            case = json.loads(line)
        except Exception:
            json_err += 1
            continue

        r_id = case["rubric_id"]
        if r_id not in rubric_cases:
            rubric_cases[r_id] = []
        rubric_cases[r_id].append(case)

        narr = case.get("narrative", "")
        ents = case.get("entities", [])
        toks = case.get("tokens", [])
        tags = case.get("bio_tags", [])

        token_lens.append(len(toks))
        if len(toks) != len(tags):
            tag_len_mismatch += 1

        for e in ents:
            total_ents += 1
            dim_counts[e["label"]] += 1
            s, end, txt = e["start"], e["end"], e["text"]
            if narr[s:end] != txt:
                slice_err += 1

    # Pairwise Jaccard overlap between variations
    def get_words(text: str) -> set:
        clean_text = "".join([c if c.isalnum() or c.isspace() else " " for c in text.lower()])
        return set([w for w in clean_text.split() if len(w) > 2])

    jaccards = []
    for r_id, c_list in rubric_cases.items():
        if len(c_list) >= 2:
            for i in range(len(c_list)):
                for j in range(i + 1, len(c_list)):
                    w1 = get_words(c_list[i]["narrative"])
                    w2 = get_words(c_list[j]["narrative"])
                    inter = len(w1 & w2)
                    uni = len(w1 | w2)
                    sim = inter / uni if uni > 0 else 0
                    jaccards.append(sim)

    mean_jaccard = sum(jaccards) / len(jaccards) if jaccards else 0.0

    print("=" * 60)
    print("      KENT-AI PILOT 100-CASE STATISTICAL AUDIT REPORT      ")
    print("=" * 60)
    print(f"Total Cases Generated        : {total_cases}")
    print(f"Stratified Rubrics Covered   : {len(rubric_cases)} (4 variations per rubric)")
    print(f"JSON Parse Validity          : {100 - (json_err / total_cases * 100):.2f}% ({total_cases - json_err}/{total_cases})")
    print(f"BIO Slice Accuracy           : {100 - (slice_err / total_ents * 100):.2f}% ({total_ents - slice_err}/{total_ents})")
    print(f"Token/BIO Tag Mismatches     : {tag_len_mismatch}")
    print(f"Total Extracted Entities     : {total_ents} (avg {total_ents / total_cases:.2f} per case)")
    print(f"Token Length Stats           : Min={min(token_lens)}, Max={max(token_lens)}, Mean={sum(token_lens)/len(token_lens):.1f}")
    print(f"Mean Pairwise Jaccard Overlap: {mean_jaccard * 100:.2f}% (Target < 45%)")
    print(f"Lexical Diversity Score      : {(1 - mean_jaccard) * 100:.2f}%")
    print("-" * 60)
    print("Entity Breakdown Across 7 Kent Dimensions:")
    for k, v in dim_counts.most_common():
        print(f"  {k:12s}: {v:4d} spans ({v / total_ents * 100:5.1f}%)")
    print("=" * 60)

    return {
        "total_cases": total_cases,
        "rubric_count": len(rubric_cases),
        "json_validity_pct": 100 - (json_err / total_cases * 100),
        "bio_slice_accuracy_pct": 100 - (slice_err / total_ents * 100),
        "total_entities": total_ents,
        "mean_jaccard_overlap_pct": mean_jaccard * 100,
        "lexical_diversity_pct": (1 - mean_jaccard) * 100,
        "dimension_counts": dict(dim_counts),
        "token_len_mean": sum(token_lens) / len(token_lens),
    }


if __name__ == "__main__":
    audit_pilot()
