from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from .utils import read_text

@dataclass
class Agent:
    name: str
    system_prompt_path: Path

    def system_prompt(self) -> str:
        return read_text(self.system_prompt_path)

def default_agents(prompts_dir: Path) -> Dict[str, Agent]:
    return {
        "MarketResearcher": Agent("MarketResearcher", prompts_dir / "01_researcher.system.txt"),
        "StrategistPlanner": Agent("StrategistPlanner", prompts_dir / "02_strategist.system.txt"),
        "CopywriterExecutor": Agent("CopywriterExecutor", prompts_dir / "03_copywriter.system.txt"),
        "ChannelManager": Agent("ChannelManager", prompts_dir / "04_channel_manager.system.txt"),
        "AnalystQA": Agent("AnalystQA", prompts_dir / "05_analyst.system.txt"),
        "Reviser": Agent("Reviser", prompts_dir / "06_revisioner.system.txt"),
    }
