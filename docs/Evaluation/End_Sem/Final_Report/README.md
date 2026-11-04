# Kent-AI Final Report — LaTeX Source

This directory contains the complete LaTeX source for the **Kent-AI B.Tech Final Project Report** submitted to the Department of Information Technology, IIIT Allahabad.

## Report Details

| Field | Value |
|---|---|
| **Title** | Kent-AI: An AI-Powered Conversational Clinical Assistant for Homeopathic Case-Taking and Dense Semantic Repertorization |
| **Degree** | Bachelor of Technology |
| **Institution** | IIIT Allahabad |
| **Supervisor** | Dr. Nikhilanand Arya |
| **Authors** | Krishna Sikheriya (IIT2023139), Lokesh Bawariya (IIT2023138), Naitik Jain (IIB2023036) |
| **Year** | 2026–2027 |

## File Structure

```
Final_Report/
├── main.tex                    # Root LaTeX file (compile this)
├── frontmatter.tex             # Title page, certificate, declaration, abstract, acknowledgements
├── references.bib              # BibLaTeX bibliography (30+ references)
├── Thesis.cls                  # IIIT Allahabad thesis class file
├── Chapters/
│   ├── 1_introduction.tex      # Chapter 1: Introduction & Motivation
│   ├── 2_literature.tex        # Chapter 2: Literature Review
│   ├── 3_system_design.tex     # Chapter 3: System Design & Architecture
│   ├── 4_implementation.tex    # Chapter 4: Implementation
│   ├── 5_experiments.tex       # Chapter 5: Experimental Setup
│   ├── 6_results.tex           # Chapter 6: Results & Analysis
│   └── 7_conclusion.tex        # Chapter 7: Conclusion & Future Work
├── Appendices/
│   ├── AppendixA.tex           # 7-Dimension BIO Label Schema & Examples
│   └── AppendixB.tex           # Installation & Deployment Guide
└── Figures/
    ├── IIITA_Logo.png          # IIIT Allahabad logo (title page)
    └── IIITA_Header.png        # IIIT Allahabad header (certificate, declaration)
```

## Compilation Instructions

### Prerequisites

Install one of:
- **MiKTeX** (Windows): https://miktex.org/download
- **TeX Live** (Linux/Mac): `sudo apt install texlive-full`

Required LaTeX packages: `babel`, `geometry`, `biblatex`, `csquotes`, `array`, `booktabs`, `multirow`, `graphicx`, `amsmath`, `amssymb`, `xcolor`, `listings`, `algorithm`, `algpseudocode`, `subcaption`, `hyperref`, `mathpazo`, `fontenc`, `inputenc`.

### Compile Command Sequence

```bash
cd docs/Evaluation/End_Sem/Final_Report/

# Step 1: First LaTeX pass (generates .aux, .toc)
pdflatex main.tex

# Step 2: Biber bibliography pass
biber main

# Step 3: Second LaTeX pass (resolves references)
pdflatex main.tex

# Step 4: Third LaTeX pass (finalizes TOC, LOF, LOT)
pdflatex main.tex
```

The final compiled PDF will be at `main.pdf`.

### Using Overleaf (Recommended)

1. Zip this entire `Final_Report/` directory.
2. Upload to [https://overleaf.com](https://overleaf.com) as a new project.
3. Set compiler to **pdfLaTeX** and bibliography tool to **Biber**.
4. Click **Compile** — Overleaf handles all passes automatically.

> **Note**: The `Thesis.cls` class file uses the `hindi` environment for the IIIT Allahabad Hindi text on the title page. If your LaTeX distribution does not support Hindi, comment out the `\begin{hindi}...\end{hindi}` block in `frontmatter.tex`.

## Report Structure Summary

| Chapter | Title | Pages (est.) |
|---|---|---|
| Frontmatter | Title, Certificate, Declaration, Abstract, Acknowledgements, TOC | 10 |
| Chapter 1 | Introduction | 8 |
| Chapter 2 | Literature Review | 7 |
| Chapter 3 | System Design & Architecture | 10 |
| Chapter 4 | Implementation | 10 |
| Chapter 5 | Experimental Setup | 6 |
| Chapter 6 | Results & Analysis | 10 |
| Chapter 7 | Conclusion & Future Work | 7 |
| Appendix A | BIO Label Schema | 4 |
| Appendix B | Installation Guide | 3 |
| References | Bibliography | 4 |
| **Total** | | **~79 pages** |
