from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def safe_json_loads(s: str) -> Dict[str, Any]:
    """Parse a JSON object from model output, with a small amount of robustness."""
    s = s.strip()
    # If the model wrapped JSON in code fences, strip them.
    if s.startswith("```"):
        s = s.split("```", 2)[1] if "```" in s else s
    # Attempt to locate the first '{' and last '}'.
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        s = s[start:end+1]
    return json.loads(s)

def dump_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
