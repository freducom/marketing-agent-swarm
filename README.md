# Marketing Agent Swarm

A small, runnable multi-agent "swarm" for marketing work:
- MarketResearcher
- StrategistPlanner
- CopywriterExecutor
- ChannelManager
- AnalystQA
- Reviser (used for revision loops)

Agents collaborate via a JSON message protocol and exchange only explicit artifacts (markdown/json/text).
LLM provider/model is configurable in `config/config.toml`. OpenAI is the default provider.

## Requirements
- Python 3.10+
- An OpenAI API key in your environment:
  - macOS/Linux: `export OPENAI_API_KEY="..."`
  - Windows (PowerShell): `$env:OPENAI_API_KEY="..."`

## Install
From the project folder:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

## Run (example)
```bash
swarm run --goal "Launch a new B2B webinar series for our product"   --inputs examples/inputs.sample.json   --constraints examples/constraints.sample.txt
```

Outputs land in `out/<task_id>/` as markdown + a JSONL log.

## Configure LLM
Edit `config/config.toml`:

- `[llm].provider` (default: `openai`)
- `[llm].model` (default: `gpt-4.1-mini`)
- temperature/max_tokens/timeouts

## Notes
- This project avoids framework lock-in. It's a clear starting point you can extend (tools, retrieval, parallelism).
- The OpenAI adapter uses the Chat Completions-compatible endpoint and reads `OPENAI_API_KEY` from env.
