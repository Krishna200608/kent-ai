import os
import re
import base64
import subprocess
import pypandoc
import fitz

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MD_FILE = os.path.join(BASE_DIR, "Project_Proposal.md")
PDF_OUT = os.path.join(BASE_DIR, "Project_Proposal.pdf")
HTML_OUT = os.path.join(BASE_DIR, "Project_Proposal.html")

with open(MD_FILE, "r", encoding="utf-8") as f:
    raw_md = f.read()

# 1. Extract and placeholder Mermaid blocks with layout optimizations
mermaid_blocks = []
def replace_mermaid(match):
    idx = len(mermaid_blocks)
    code = match.group(1).strip()
    
    # Optimize diagrams to balanced multi-row layouts so they fit gracefully with crisp typography
    if "PatientLayer" in code:
        code = """flowchart TD
    subgraph TopRow["1. Patient Interaction & 2. NLP / ML Extraction Pipeline"]
        direction LR
        P["Patient"] -->|Natural dialogue| CB["Empathetic Chatbot\\n(Local LLaMA 3 8B)"]
        CB -->|Transcript| SE["Symptom Extraction\\n(ClinicalBERT NER)"]
        SE -->|Structured JSON| RM["Rubric Matching\\n(Sentence Transformers)"]
        RM -->|Ranked Rubrics| RG["Pre-Consultation\\nReport Generator"]
    end
    
    subgraph BottomRow["3. Knowledge Base & 4. Doctor Dashboard"]
        direction LR
        subgraph KBLayer["Knowledge Base Layer"]
            DB[("Kent Repertory DB\\n74,513 rubrics (SQLite)")]
            VDB[("ChromaDB Vector Store\\nRubric Embeddings")]
        end
        subgraph DoctorLayer["Doctor Interface Layer"]
            DD["Doctor Dashboard\\n(Streamlit Web App)"]
        end
    end
    
    RM -.->|Vector Search| VDB
    RM -.->|Keyword Validation| DB
    RG ==>|Structured Summary| DD
    DD -.->|Repertory Explorer| DB"""

    if "stateDiagram-v2" in code or "ChiefComplaint" in code:
        code = """flowchart TD
    subgraph Row1["Phase 1: Intake & Chief Complaint"]
        direction LR
        S(["Start"]) --> G["1. Greeting & Rapport"] --> CC["2. Chief Complaint Identification"] --> LOC["3. Anatomical Location Exploration"]
    end
    subgraph Row2["Phase 2: Symptom Characterization & Report Synthesis"]
        direction LR
        LOC --> SEN["4. Sensation Characterization"] --> MOD["5. Modalities (Better / Worse)"] --> CON["6. Concomitant Symptoms"] --> CLAR["7. Clarification"] --> REP["8. Report Generation"] --> E(["Done"])
    end
    
    style S fill:#1e40af,color:#fff
    style E fill:#16a34a,color:#fff"""
        
    mermaid_blocks.append(code)
    return f"\n\n<!-- MERMAID_BLOCK_{idx} -->\n\n"

processed_md = re.sub(r'```mermaid\s*\n(.*?)\n```', replace_mermaid, raw_md, flags=re.DOTALL)

# 2. Extract and placeholder Images
image_blocks = []
def replace_image(match):
    idx = len(image_blocks)
    caption = match.group(1)
    img_path = match.group(2).replace('/', os.sep)
    image_blocks.append((caption, img_path))
    return f"\n\n<!-- IMAGE_BLOCK_{idx} -->\n\n"

processed_md = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_image, processed_md)

# 3. Strip original header and duplicate footer
sec1_idx = processed_md.find("## 1. Executive Summary")
if sec1_idx != -1:
    body_md = processed_md[sec1_idx:]
else:
    body_md = processed_md

# Strip trailing duplicate markdown attribution
body_md = re.sub(r'---\s*\n+\*Prepared by Team.*$', '', body_md, flags=re.DOTALL)

# Convert body_md with pandoc
body_html = pypandoc.convert_text(body_md, 'html5', format='gfm')

# Substitute Mermaid blocks back
for i, m_code in enumerate(mermaid_blocks):
    escaped_m = m_code
    block_html = f'''
    <div class="figure-wrapper diagram-figure">
        <div class="mermaid">
{escaped_m}
        </div>
    </div>'''
    body_html = body_html.replace(f"<!-- MERMAID_BLOCK_{i} -->", block_html)

# Substitute Image blocks back
for i, (caption, img_path) in enumerate(image_blocks):
    if os.path.exists(img_path):
        with open(img_path, "rb") as img_f:
            b64_data = base64.b64encode(img_f.read()).decode("utf-8")
        img_src = f"data:image/jpeg;base64,{b64_data}"
    else:
        img_src = ""
    block_html = f'''
    <div class="figure-wrapper image-figure">
        <img src="{img_src}" alt="{caption}" />
        <div class="figure-caption"><strong>Figure:</strong> {caption}</div>
    </div>'''
    body_html = body_html.replace(f"<!-- IMAGE_BLOCK_{i} -->", block_html)

# Build Full Academic HTML
full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI-Powered Clinical Assistant for Homeopathic Repertorization</title>
    <style>
        @page {{
            size: A4 portrait;
            margin: 18mm 16mm 20mm 16mm;
            @bottom-right {{
                content: counter(page);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 8pt;
                color: #64748b;
            }}
            @bottom-left {{
                content: "IIIT Allahabad • Dept. of IT • Project Proposal";
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 8pt;
                color: #64748b;
            }}
        }}

        *, *::before, *::after {{
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            font-size: 9.3pt;
            line-height: 1.55;
            color: #1e293b;
            background: #ffffff;
            margin: 0;
            padding: 0;
        }}

        /* Academic Header / Title Banner */
        .academic-header {{
            border-bottom: 2.5px solid #1e3a8a;
            padding-bottom: 16px;
            margin-bottom: 22px;
            page-break-after: avoid;
        }}

        .institution-badge {{
            display: inline-block;
            background: #eff6ff;
            color: #1e40af;
            font-size: 8pt;
            font-weight: 700;
            letter-spacing: 0.8px;
            text-transform: uppercase;
            padding: 3px 10px;
            border-radius: 4px;
            border: 1px solid #bfdbfe;
            margin-bottom: 8px;
        }}

        .institution-name {{
            font-size: 13pt;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.2px;
            margin: 0 0 2px 0;
        }}

        .department-name {{
            font-size: 10pt;
            color: #475569;
            font-weight: 500;
            margin: 0 0 12px 0;
        }}

        .proposal-title {{
            font-size: 18pt;
            font-weight: 800;
            color: #1e3a8a;
            line-height: 1.25;
            margin: 0 0 14px 0;
        }}

        .metadata-grid {{
            display: grid;
            grid-template-columns: 1.1fr 1fr;
            gap: 12px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px 16px;
        }}

        .meta-col h4 {{
            margin: 0 0 6px 0;
            font-size: 8pt;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #64748b;
        }}

        .meta-col p {{
            margin: 2px 0;
            font-size: 8.8pt;
            color: #1e293b;
        }}

        .member-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}

        .member-list li {{
            font-size: 8.8pt;
            margin-bottom: 3px;
        }}

        .member-list strong {{
            color: #0f172a;
        }}

        .repo-badge {{
            margin-top: 6px;
            display: inline-block;
            font-size: 8pt;
            color: #2563eb;
            text-decoration: none;
            background: #eff6ff;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid #dbeafe;
        }}

        /* Section Headings */
        h1 {{
            font-size: 14pt;
            font-weight: 700;
            color: #1e3a8a;
            border-bottom: 1.5px solid #cbd5e1;
            padding-bottom: 4px;
            margin: 22px 0 10px 0;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        h2 {{
            font-size: 12.5pt;
            font-weight: 700;
            color: #1e3a8a;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 4px;
            margin: 20px 0 10px 0;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        h3 {{
            font-size: 10.5pt;
            font-weight: 600;
            color: #0f172a;
            margin: 16px 0 6px 0;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        h4 {{
            font-size: 9.8pt;
            font-weight: 600;
            color: #334155;
            margin: 12px 0 4px 0;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        p, ul, ol {{
            margin: 0 0 8px 0;
        }}

        li {{
            margin-bottom: 3px;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 8.5pt;
            margin: 10px 0 14px 0;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            background: #ffffff;
            border-radius: 6px;
            overflow: hidden;
            border: 1px solid #cbd5e1;
        }}

        thead tr {{
            background: #1e3a8a !important;
            color: #ffffff !important;
            font-weight: 600;
            text-align: left;
        }}

        th {{
            padding: 6px 9px;
            border: 1px solid #1e3a8a;
            color: #ffffff;
            font-weight: 600;
        }}

        td {{
            padding: 5px 9px;
            border: 1px solid #e2e8f0;
            vertical-align: top;
        }}

        tbody tr:nth-child(even) {{
            background: #f8fafc;
        }}

        tr {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }}

        /* Figures & Images */
        .figure-wrapper {{
            margin: 10px 0;
            text-align: center;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }}

        .figure-wrapper img {{
            max-width: 95%;
            max-height: 330px;
            width: auto;
            height: auto;
            border-radius: 6px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06);
            display: inline-block;
        }}

        .figure-caption {{
            font-size: 7.8pt;
            color: #64748b;
            margin-top: 5px;
            font-style: italic;
        }}

        /* Mermaid Box */
        .mermaid {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 8px 12px;
            display: inline-block;
            max-width: 100%;
            margin: 0 auto;
            text-align: center;
        }}

        .mermaid svg {{
            max-height: 320px;
            max-width: 100%;
            display: block;
            margin: 0 auto;
        }}

        /* Code and Pre */
        pre {{
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 8px 12px;
            font-family: Consolas, "Courier New", monospace;
            font-size: 8pt;
            line-height: 1.35;
            overflow-x: auto;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            margin: 8px 0;
        }}

        code {{
            font-family: Consolas, "Courier New", monospace;
            font-size: 8.3pt;
            background: #f1f5f9;
            padding: 1px 4px;
            border-radius: 3px;
            color: #0f172a;
        }}

        pre code {{
            background: none;
            padding: 0;
        }}

        /* Callout / Blockquote */
        blockquote {{
            margin: 8px 0;
            padding: 7px 12px;
            background: #eff6ff;
            border-left: 3.5px solid #2563eb;
            color: #1e3a8a;
            border-radius: 0 6px 6px 0;
            font-size: 9pt;
        }}

        /* Links */
        a {{
            color: #2563eb;
            text-decoration: none;
        }}

        /* Section divider */
        hr {{
            border: none;
            border-top: 1px solid #e2e8f0;
            margin: 14px 0;
        }}

        /* Footer Note */
        .footer-attribution {{
            margin-top: 24px;
            padding-top: 10px;
            border-top: 1px solid #cbd5e1;
            font-size: 7.8pt;
            color: #64748b;
            text-align: center;
            page-break-inside: avoid;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }},
            themeVariables: {{
                fontSize: '12px'
            }}
        }});
    </script>
</head>
<body>

    <!-- Academic Header -->
    <div class="academic-header">
        <div class="institution-badge">Research Project Proposal</div>
        <h2 class="institution-name">Indian Institute of Information Technology, Allahabad</h2>
        <div class="department-name">Department of Information Technology</div>

        <h1 class="proposal-title">AI-Powered Clinical Assistant for Homeopathic Repertorization Using Kent's Repertory</h1>

        <div class="metadata-grid">
            <div class="meta-col">
                <h4>Supervisor</h4>
                <p><strong>Dr. Nikhilanand Arya</strong></p>
                <p>Assistant Professor, Department of IT</p>
                <p>IIIT Allahabad</p>
                <div style="margin-top: 6px;">
                    <h4>Repository</h4>
                    <a class="repo-badge" href="https://github.com/su4532/kent-repertory-explorer">🔗 github.com/su4532/kent-repertory-explorer</a>
                </div>
            </div>
            <div class="meta-col">
                <h4>Project Team</h4>
                <ul class="member-list">
                    <li><strong>Krishna Sikheriya</strong> (IIT2023139) — <em>Team Leader</em></li>
                    <li><strong>Lokesh Bawariya</strong> (IIT2023138) — <em>Team Member</em></li>
                    <li><strong>Naitik Jain</strong> (IIB2023036) — <em>Team Member</em></li>
                </ul>
                <div style="margin-top: 6px;">
                    <h4>Submission Date</h4>
                    <p>September 2026</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="proposal-content">
{body_html}
    </div>

    <div class="footer-attribution">
        <p><em>Prepared by Krishna Sikheriya, Lokesh Bawariya, Naitik Jain • Under the supervision of Dr. Nikhilanand Arya, IIIT Allahabad • September 2026</em></p>
    </div>

</body>
</html>"""

with open(HTML_OUT, "w", encoding="utf-8") as out_f:
    out_f.write(full_html)

print("HTML written to:", HTML_OUT, "Size:", os.path.getsize(HTML_OUT))

# Check if target PDF is locked; if locked, generate Project_Proposal_Updated.pdf
actual_pdf_out = PDF_OUT
if os.path.exists(PDF_OUT):
    try:
        os.remove(PDF_OUT)
    except Exception:
        actual_pdf_out = r"d:\Research Project\Kent\Project_Proposal_Updated.pdf"
        print("Note: Project_Proposal.pdf is currently open in Acrobat. Generating to:", actual_pdf_out)

# Run Chrome Headless to generate PDF
chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
cmd = [
    chrome,
    "--headless=new",
    "--disable-gpu",
    "--run-all-compositor-stages-before-draw",
    "--virtual-time-budget=6000",
    f"--print-to-pdf={actual_pdf_out}",
    "--no-pdf-header-footer",
    HTML_OUT
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("Chrome exit code:", res.returncode)
if os.path.exists(actual_pdf_out):
    doc = fitz.open(actual_pdf_out)
    print("SUCCESS: PDF Generated at:", actual_pdf_out)
    print("Page Count:", len(doc))
    print("PDF Size:", os.path.getsize(actual_pdf_out), "bytes")
    doc.close()
