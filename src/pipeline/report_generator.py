"""Format patient reports into JSON and human-readable clinical Markdown (Phase 5)."""

from __future__ import annotations

import datetime
import json
from typing import Any, Dict, List


def generate_json_report(report_data: Dict[str, Any]) -> str:
    """Serialize report to formatted JSON string."""
    return json.dumps(report_data, indent=2, ensure_ascii=False)


def generate_markdown_report(report_data: Dict[str, Any]) -> str:
    """Format report into structured clinical consultation Markdown.
    
    Args:
        report_data: Dictionary containing patient_id, transcript, dimensions,
                     matched_rubrics, and ranked_remedies.
                     
    Returns:
        Formatted Markdown report suitable for clinical records and UI display.
    """
    patient_id = report_data.get("patient_id", "ANONYMOUS")
    timestamp = report_data.get("timestamp") or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    transcript = report_data.get("transcript", "").strip()
    dims = report_data.get("dimensions", {})
    rubrics = report_data.get("matched_rubrics", [])
    remedies = report_data.get("ranked_remedies", [])

    lines: List[str] = [
        "# Kent-AI — Clinical Repertorization Report",
        "",
        f"> **Patient ID**: `{patient_id}` | **Date**: {timestamp}",
        "",
        "---",
        "",
        "## 1. Patient Intake Narrative",
        "",
        f"> *\"{transcript}\"*",
        "",
        "## 2. Kent's 7-Dimension Analysis",
        "",
        "| Dimension | Clinical Findings |",
        "|---|---|",
        f"| **Location (LOC)** | {', '.join(dims.get('location', [])) or 'None reported'} |",
        f"| **Sensation (SEN)** | {', '.join(dims.get('sensation', [])) or 'None reported'} |",
        f"| **Aggravation (MOD_AGG)** | {', '.join(dims.get('modality_agg', [])) or 'None reported'} |",
        f"| **Amelioration (MOD_AMEL)** | {', '.join(dims.get('modality_amel', [])) or 'None reported'} |",
        f"| **Concomitant (CONC)** | {', '.join(dims.get('concomitant', [])) or 'None reported'} |",
        f"| **Temporal (TEMP)** | {', '.join(dims.get('temporal', [])) or 'None reported'} |",
        f"| **Mental (MENT)** | {', '.join(dims.get('mental', [])) or 'None reported'} |",
        f"| **Negated / Denied** | {', '.join(dims.get('negated', [])) or 'None'} |",
        "",
        "## 3. Matched Kent Repertory Rubrics",
        "",
    ]

    if rubrics:
        lines.extend([
            "| # | Rubric Path | Similarity | Remedies in Book |",
            "|---|---|---|---|",
        ])
        for idx, r in enumerate(rubrics[:10], start=1):
            sim = r.get("similarity", 0.0)
            path = r.get("path", f"Rubric #{r.get('rubric_id')}")
            rem_count = r.get("remedy_count", "-")
            lines.append(f"| {idx} | `{path}` | {sim:.3f} | {rem_count} |")
    else:
        lines.append("_No rubrics matched._")

    lines.extend([
        "",
        "## 4. Totality Remedy Ranking",
        "",
    ])

    if remedies:
        lines.extend([
            "| Rank | Remedy | Abbreviation | Totality Score | Rubrics Covered | Coverage % |",
            "|---|---|---|---|---|---|",
        ])
        for idx, rem in enumerate(remedies[:10], start=1):
            name = rem.get("full_name") or rem.get("abbreviation")
            abbr = rem.get("abbreviation", "")
            score = rem.get("score", 0.0)
            count = rem.get("rubric_count", 0)
            ratio = rem.get("coverage_ratio", 0.0) * 100
            lines.append(f"| {idx} | **{name}** | `{abbr}` | **{score:.2f}** | {count} | {ratio:.0f}% |")

        top = remedies[0]
        top_name = top.get("full_name") or top.get("abbreviation")
        top_abbr = top.get("abbreviation", "")
        lines.extend([
            "",
            "### Primary Simillimum Indication",
            f"Top indicated remedy is **{top_name}** (`{top_abbr}`) covering **{top.get('rubric_count')}** symptom rubrics with a weighted totality score of **{top.get('score')}**.",
        ])
    else:
        lines.append("_No remedy candidates identified._")

    lines.extend([
        "",
        "---",
        "*Report generated autonomously by Kent-AI Clinical Pipeline.*",
        "",
    ])

    return "\n".join(lines)
