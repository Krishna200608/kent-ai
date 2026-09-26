"""Format patient reports into JSON and human-readable clinical Markdown."""

from __future__ import annotations

import json
from typing import Any, Dict


def generate_json_report(report_data: Dict[str, Any]) -> str:
    """Serialize report to formatted JSON string."""
    return json.dumps(report_data, indent=2)


def generate_markdown_report(report_data: Dict[str, Any]) -> str:
    """Format report into clinical consultation Markdown."""
    raise NotImplementedError("Phase 5 implementation pending.")
