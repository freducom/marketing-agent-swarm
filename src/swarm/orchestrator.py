from __future__ import annotations
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .agents import Agent, default_agents
from .config import Config
from .llm_adapters import get_llm
from .utils import iso_now, safe_json_loads, write_text, dump_jsonl

@dataclass
class RunInputs:
    goal: str
    inputs: Dict[str, Any]
    constraints: List[str]

class Orchestrator:
    def __init__(self, config: Config, project_dir: Path) -> None:
        self.config = config
        self.project_dir = project_dir
        self.prompts_dir = project_dir / "prompts"
        self.agents = default_agents(self.prompts_dir)
        self.llm = get_llm(config.llm.provider)

    def _make_envelope(self, task_id: str, sender: str, to: str, msg_type: str,
                       goal: str, inputs: Dict[str, Any], constraints: List[str],
                       artifacts: List[Dict[str, str]], next_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "protocol_version": "1.0",
            "message_id": str(uuid.uuid4()),
            "task_id": task_id,
            "timestamp": iso_now(),
            "from": sender,
            "to": to,
            "type": msg_type,
            "payload": {
                "goal": goal,
                "inputs": inputs,
                "constraints": constraints,
                "artifacts": artifacts,
                "next": next_actions,
            }
        }

    def _chat_agent(self, agent: Agent, envelope: Dict[str, Any]) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": agent.system_prompt()},
            {"role": "user", "content": json.dumps(envelope, ensure_ascii=False)},
        ]
        resp = self.llm.chat(
            messages=messages,
            model=self.config.llm.model,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
            timeout_seconds=self.config.llm.timeout_seconds,
        )
        out = safe_json_loads(resp.text)
        return out

    def run(self, run_inputs: RunInputs) -> Path:
        task_id = str(uuid.uuid4())
        out_dir = self.project_dir / self.config.swarm.artifact_dir / task_id
        out_dir.mkdir(parents=True, exist_ok=True)
        log_path = out_dir / "run.log.jsonl"

        def log(obj: Dict[str, Any]) -> None:
            if self.config.swarm.log_jsonl:
                dump_jsonl(log_path, obj)

        # Seed TASK
        envelope = self._make_envelope(
            task_id=task_id,
            sender="orchestrator",
            to="MarketResearcher",
            msg_type="TASK",
            goal=run_inputs.goal,
            inputs=run_inputs.inputs,
            constraints=run_inputs.constraints,
            artifacts=[],
            next_actions=[{"to": "MarketResearcher", "action": "Produce research brief", "priority": 5}],
        )
        log(envelope)

        # 1) Research
        res = self._chat_agent(self.agents["MarketResearcher"], envelope)
        log({"from": "MarketResearcher", "raw": res})
        research_artifacts = res.get("artifacts", [])
        for a in research_artifacts:
            write_text(out_dir / a["name"], a["content"])

        # 2) Plan (with Analyst review loop)
        plan_env = self._make_envelope(task_id, "orchestrator", "StrategistPlanner", "TASK",
                                       run_inputs.goal, run_inputs.inputs, run_inputs.constraints,
                                       artifacts=research_artifacts, next_actions=[{"to":"StrategistPlanner","action":"Create campaign plan","priority":5}])
        log(plan_env)
        plan = self._chat_agent(self.agents["StrategistPlanner"], plan_env)
        log({"from": "StrategistPlanner", "raw": plan})
        plan_artifacts = plan.get("artifacts", [])
        for a in plan_artifacts:
            write_text(out_dir / a["name"], a["content"])

        # 3) Draft copy + channel plan
        copy_env = self._make_envelope(task_id, "orchestrator", "CopywriterExecutor", "TASK",
                                       run_inputs.goal, run_inputs.inputs, run_inputs.constraints,
                                       artifacts=plan_artifacts, next_actions=[{"to":"CopywriterExecutor","action":"Draft copy pack","priority":5}])
        log(copy_env)
        copy = self._chat_agent(self.agents["CopywriterExecutor"], copy_env)
        log({"from": "CopywriterExecutor", "raw": copy})
        copy_artifacts = copy.get("artifacts", [])
        for a in copy_artifacts:
            write_text(out_dir / a["name"], a["content"])

        ch_env = self._make_envelope(task_id, "orchestrator", "ChannelManager", "TASK",
                                     run_inputs.goal, run_inputs.inputs, run_inputs.constraints,
                                     artifacts=plan_artifacts, next_actions=[{"to":"ChannelManager","action":"Draft channel plan","priority":4}])
        log(ch_env)
        channel = self._chat_agent(self.agents["ChannelManager"], ch_env)
        log({"from": "ChannelManager", "raw": channel})
        channel_artifacts = channel.get("artifacts", [])
        for a in channel_artifacts:
            write_text(out_dir / a["name"], a["content"])

        # 4) Analyst review over bundle
        bundle_artifacts = []
        bundle_artifacts.extend(research_artifacts)
        bundle_artifacts.extend(plan_artifacts)
        bundle_artifacts.extend(copy_artifacts)
        bundle_artifacts.extend(channel_artifacts)

        review_cycles = 0
        final_copy = copy_artifacts
        final_plan = plan_artifacts
        final_channel = channel_artifacts

        while True:
            review_env = self._make_envelope(task_id, "orchestrator", "AnalystQA", "TASK",
                                             run_inputs.goal, run_inputs.inputs, run_inputs.constraints,
                                             artifacts=bundle_artifacts,
                                             next_actions=[{"to":"AnalystQA","action":"Review artifacts and propose revisions","priority":5}])
            log(review_env)
            review = self._chat_agent(self.agents["AnalystQA"], review_env)
            log({"from": "AnalystQA", "raw": review})
            review_artifacts = review.get("artifacts", [])
            for a in review_artifacts:
                write_text(out_dir / a["name"], a["content"])

            review_cycles += 1
            if review_cycles > self.config.swarm.max_review_cycles:
                break

            # Apply revisions using Reviser agent for each artifact category (plan/copy/channel) in a simple way:
            # We'll feed the QA review + existing artifact into Reviser and overwrite.
            qa_md = ""
            if review_artifacts:
                qa_md = review_artifacts[0].get("content", "")

            def revise(target_agent_name: str, artifact_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
                if not artifact_list:
                    return artifact_list
                rev_env = self._make_envelope(task_id, "orchestrator", "Reviser", "TASK",
                                              run_inputs.goal, run_inputs.inputs, run_inputs.constraints,
                                              artifacts=[
                                                  {"name":"qa_review.md","format":"markdown","content":qa_md},
                                                  artifact_list[0]
                                              ],
                                              next_actions=[{"to":"Reviser","action":"Revise the provided artifact based on qa_review.md","priority":4}])
                log(rev_env)
                revised = self._chat_agent(self.agents["Reviser"], rev_env)
                log({"from": "Reviser", "raw": revised, "target": artifact_list[0]["name"]})
                arts = revised.get("artifacts", [])
                if arts:
                    write_text(out_dir / arts[0]["name"], arts[0]["content"])
                    return arts
                return artifact_list

            final_plan = revise("StrategistPlanner", final_plan)
            final_copy = revise("CopywriterExecutor", final_copy)
            final_channel = revise("ChannelManager", final_channel)

            bundle_artifacts = []
            bundle_artifacts.extend(research_artifacts)
            bundle_artifacts.extend(final_plan)
            bundle_artifacts.extend(final_copy)
            bundle_artifacts.extend(final_channel)

            # Re-review once more unless max cycles reached
            if review_cycles >= self.config.swarm.max_review_cycles:
                break

        # 5) Final bundle
        parts = []
        parts.append("# Final Marketing Bundle\n")
        for a in bundle_artifacts:
            parts.append(f"## {a['name']}\n")
            parts.append(a["content"])
            parts.append("\n")
        write_text(out_dir / "final_bundle.md", "\n".join(parts))

        # Write a machine-readable summary
        summary = {
            "task_id": task_id,
            "goal": run_inputs.goal,
            "artifacts": [a["name"] for a in bundle_artifacts] + ["final_bundle.md", "run.log.jsonl"],
            "review_cycles": review_cycles,
        }
        write_text(out_dir / "summary.json", json.dumps(summary, indent=2))
        return out_dir
