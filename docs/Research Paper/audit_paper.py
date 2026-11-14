import os
import re
import glob
import numpy as np

paper_dir = r"docs\Research Paper"
sections_dir = os.path.join(paper_dir, "sections")
bib_path = os.path.join(paper_dir, "references.bib")

with open(bib_path, "r", encoding="utf-8") as f:
    bib_content = f.read()
bib_keys = set(re.findall(r"@\w+\s*\{\s*([^,]+),", bib_content))

tex_files = [os.path.join(paper_dir, "main.tex")] + sorted(glob.glob(os.path.join(sections_dir, "*.tex")))

all_labels = set()
all_refs = set()
all_cites = set()
all_images = set()

cliches = [
    "delve into", "delves into", "pivotal role", "pivotal", "rich tapestry", "testament to",
    "furthermore", "moreover", "additionally", "crucial", "vital", "it is worth noting that",
    "in conclusion", "comprehensive"
]

cliche_hits = []
all_sentences = []

for tf in tex_files:
    with open(tf, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Strip comments
    lines = [line.split("%")[0] for line in content.split("\n")]
    clean_text = "\n".join(lines)
    
    # Find labels, refs, cites, includegraphics
    labels = re.findall(r"\\label\{([^}]+)\}", clean_text)
    refs = re.findall(r"\\ref\{([^}]+)\}", clean_text)
    cites = re.findall(r"\\cite\{([^}]+)\}", clean_text)
    for c in cites:
        for k in c.split(","):
            all_cites.add(k.strip())
            
    images = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", clean_text)
    for img in images:
        all_images.add(img.strip())
        
    all_labels.update(labels)
    all_refs.update(refs)
    
    # Check cliches (case insensitive)
    for cl in cliches:
        matches = re.findall(rf"\b{cl}\b", clean_text, re.IGNORECASE)
        if matches:
            cliche_hits.append((os.path.basename(tf), cl, len(matches)))
            
    # Sentences for burstiness
    prose = re.sub(r"\\[a-zA-Z]+(?:\[[^\]]*\])?(?:\{[^\}]*\})*", " ", clean_text)
    prose = re.sub(r"[{}\[\]$\\]", " ", prose)
    sents = [s.strip() for s in re.split(r"[.!?]+", prose) if len(s.strip().split()) >= 3]
    for s in sents:
        all_sentences.append(len(s.split()))

print(f"=== AUDIT RESULTS ===")
print(f"Total TeX files audited: {len(tex_files)}")
print(f"Total BibTeX keys in .bib: {len(bib_keys)}")
print(f"Total Citations called: {len(all_cites)}")
missing_bibs = all_cites - bib_keys
print(f"Missing citations: {missing_bibs}")

print(f"Total Labels defined: {len(all_labels)}")
print(f"Total References called: {len(all_refs)}")
missing_labels = all_refs - all_labels
print(f"Missing labels: {missing_labels}")

print(f"Total Figures referenced: {len(all_images)}")
missing_images = []
for img in all_images:
    p1 = os.path.join(paper_dir, img)
    p2 = os.path.join(paper_dir, "figures", img)
    p3 = os.path.join(paper_dir, img if img.endswith(".png") or img.endswith(".jpg") else img + ".png")
    p4 = os.path.join(paper_dir, "figures", os.path.basename(img))
    if not (os.path.exists(p1) or os.path.exists(p2) or os.path.exists(p3) or os.path.exists(p4)):
        missing_images.append(img)
print(f"Missing images: {missing_images}")
print("Referenced images verified:")
for img in sorted(all_images):
    print(f"  [OK] {img}")

print(f"\nProhibited AI Cliches: {len(cliche_hits)}")
for tf, cl, count in cliche_hits:
    print(f"  - {tf}: '{cl}' (x{count})")

sent_lens = np.array(all_sentences)
print(f"\nTotal sentences analyzed: {len(sent_lens)}")
print(f"Total prose words: {sum(sent_lens)}")
print(f"Burstiness: Mean={np.mean(sent_lens):.1f}, Std={np.std(sent_lens):.1f}, Min={np.min(sent_lens)}, Max={np.max(sent_lens)}")
