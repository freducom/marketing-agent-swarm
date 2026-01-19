from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
import os

try:
    import tomllib  # py311+
except Exception:  # pragma: no cover
    import tomli as tomllib  # type: ignore

@dataclass
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-4.1-mini"
    temperature: float = 0.4
    max_tokens: int = 1800
    timeout_seconds: int = 60

@dataclass
class SwarmConfig:
    max_review_cycles: int = 2
    artifact_dir: str = "out"
    log_jsonl: bool = True

@dataclass
class ProjectConfig:
    name: str = "Marketing Agent Swarm"

@dataclass
class Config:
    llm: LLMConfig
    swarm: SwarmConfig
    project: ProjectConfig

def load_config(config_path: Path) -> Config:
    data: Dict[str, Any] = tomllib.loads(config_path.read_text(encoding="utf-8"))
    llm = data.get("llm", {})
    swarm = data.get("swarm", {})
    proj = data.get("project", {})
    return Config(
        llm=LLMConfig(**llm),
        swarm=SwarmConfig(**swarm),
        project=ProjectConfig(**proj),
    )
