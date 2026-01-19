from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from .config import load_config
from .orchestrator import Orchestrator, RunInputs

def _read_constraints(path: Path | None) -> List[str]:
    if not path:
        return []
    txt = path.read_text(encoding="utf-8")
    lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
    return lines

def main() -> None:
    parser = argparse.ArgumentParser(prog="swarm", description="Run the Marketing Agent Swarm.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Run the swarm on a goal and inputs.")
    run.add_argument("--goal", required=True, help="Goal for the marketing swarm.")
    run.add_argument("--inputs", required=False, help="Path to JSON inputs.", default=None)
    run.add_argument("--constraints", required=False, help="Path to a text file of constraints.", default=None)
    run.add_argument("--config", required=False, help="Path to config TOML.", default="config/config.toml")

    args = parser.parse_args()

    project_dir = Path(__file__).resolve().parents[2]
    cfg = load_config(project_dir / args.config)

    inputs: Dict[str, Any] = {}
    if args.inputs:
        inputs = json.loads((project_dir / args.inputs).read_text(encoding="utf-8"))

    constraints = _read_constraints(project_dir / args.constraints) if args.constraints else []

    orch = Orchestrator(cfg, project_dir)
    out_dir = orch.run(RunInputs(goal=args.goal, inputs=inputs, constraints=constraints))

    print(str(out_dir))

if __name__ == "__main__":
    main()
