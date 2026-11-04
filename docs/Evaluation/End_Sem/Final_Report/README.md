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
├── references.bib              # BibLaTeX bibliography (31 references)
├── Thesis.cls                  # IIIT Allahabad thesis class file (engine-adaptive)
├── Chapters/
│   ├── 1_introduction.tex      # Chapter 1: Introduction & Motivation
│   ├── 2_literature.tex        # Chapter 2: Literature Review (with Comparison Table)
│   ├── 3_system_analysis.tex   # Chapter 3: System Analysis and Requirements
│   ├── 4_system_design.tex     # Chapter 4: System Design (DFDs, ER, UML, Algorithms, Wireframes)
│   ├── 5_implementation.tex    # Chapter 5: Implementation (Walkthrough, Code, Challenges)
│   ├── 6_testing_results.tex   # Chapter 6: Testing and Results (Test Cases, Screenshots, Benchmarks)
│   └── 7_conclusion.tex        # Chapter 7: Conclusion and Future Scope (Objectives vs Outcomes)
├── Appendices/
│   ├── AppendixA.tex           # Appendix A: 7-Dimension BIO Label Schema & Examples
│   ├── AppendixB.tex           # Appendix B: Installation & GPU Deployment Guide
│   └── AppendixC.tex           # Appendix C: Complete 195 Automated Test Suite Matrix
└── Figures/
    ├── IIITA_Logo.png          # IIIT Allahabad logo (title page)
    ├── IIITA_Header.png        # IIIT Allahabad header (certificate, declaration)
    ├── dashboard_full.jpg      # Full clinical workstation screenshot (Step 1 Intake)
    ├── chat_suggestions.png    # Dynamic suggestion chips screenshot
    └── intake_progress.png     # FSM intake stepper & persona screenshot
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
2. Upload the zip to [https://overleaf.com](https://overleaf.com) via **New Project $\to$ Upload Project**.
3. Overleaf Settings:
   - **Compiler**: Either **pdfLaTeX** (default) or **XeLaTeX** (for full Devanagari Hindi font support). `Thesis.cls` is engine-adaptive and compiles cleanly under both.
   - **TeX Live version**: 2024 or latest.
4. Click **Recompile** — Overleaf handles all biblatex/biber and document passes automatically.

## Report Structure Summary

| Chapter | Title | Key Contents |
|---|---|---|
| Frontmatter | Title, Certificate (Guide \& HOD), Declaration, Abstract, Acknowledgements, TOC | Official IIITA pre-content pages |
| Chapter 1 | Introduction | Background, Problem Statement, Objectives (O1--O7), Scope, Contributions |
| Chapter 2 | Literature Review | Biomedical PLMs, Clinical NER, Dense Retrieval, LLMs, Critical Comparison Table |
| Chapter 3 | System Analysis and Requirements | Functional (FR1--FR8), Non-Functional (NFR1--NFR5), Feasibility, Tech Justification |
| Chapter 4 | System Design | 6-Tier Architecture, DFD (Levels 0, 1, 2), ER Schemas, UML (Use Case, Class, Sequence), Algorithms, UI Wireframes |
| Chapter 5 | Implementation | 8 Module Walkthroughs, Code Snippets (Subword repair, IoU clustering, NumberedCanvas), 5 Challenges \& Solutions |
| Chapter 6 | Testing and Results | 4-Tier Test Plan, Test Cases (Expected vs Actual), Workstation Screenshots, Master Comparative Benchmark, Latency |
| Chapter 7 | Conclusion and Future Scope | Audit of Achievements vs Objectives (O1--O7), Limitations, Near/Medium/Long-term Roadmap |
| Appendix A | BIO Label Schema | Complete 15-Class BIO Label Definitions with 3 Clinical Examples |
| Appendix B | Installation Guide | Local, Virtualenv, Ollama, ChromaDB, and GPU Server Deployment Instructions |
| Appendix C | Test Suite Verification | Verification Inventory of all 195 Automated Tests across 22 Modules |
| References | Bibliography | 31 Authoritative BibLaTeX Entries |

