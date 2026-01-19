# JSON Collaboration Protocol (v1.0)

All agent-to-agent and orchestrator messages use a single envelope:

- `type`: intent of the message (TASK, FINDINGS, PLAN, DRAFT, REVIEW, etc.)
- `payload.goal`: the current goal (same across the run, unless narrowed)
- `payload.inputs`: structured inputs (product, audience, offer, etc.)
- `payload.constraints`: list of constraints (tone, legal, word limits)
- `payload.artifacts`: **the only** content passed between agents (no hidden reasoning)
- `payload.next`: explicit handoffs requested by the sender

## Artifact conventions

Common artifacts:
- `research_brief.md` (Researcher)
- `campaign_plan.md` (Strategist)
- `copy_pack.md` (Copywriter)
- `channel_plan.md` (Channel Manager)
- `qa_review.md` (Analyst)
- `final_bundle.md` (Orchestrator)

## Validation

See `swarm_message.schema.json` for the JSON Schema.
