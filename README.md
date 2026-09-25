# codebone-benchmark

Does codebone actually save tokens, time and money? This repo runs the **same task against the same
project** under different agent setups and records the numbers.

The benchmark project is a deliberately messy mini shop backend (`task/make_project.py`): unhelpful
names (`calc2.py`, `h_cust.py`, `tok.py`), dead legacy code, 30 distractor modules — but a clear
folder structure (`web/`, `db/`, `utils/`, `export/`, `auth_stuff/`, `notif/`, `old/`). Without an
architecture map an agent has to grep and read around; with codebone it asks `cb()`.

## The task

One prompt (`task/prompt.txt`), three changes: VAT 19% → 20%, optional `phone` field on customers,
reset token lifetime fix. The result is checked mechanically by `task/check.py` — three booleans,
exit code 1 if anything fails. A run only counts if all three pass.

## Configs

| config      | model                        | codebone context tool (`cb()`) |
|-------------|------------------------------|--------------------------------|
| `sonnet`    | Claude Sonnet (Anthropic)    | no                             |
| `sonnet+cb` | Claude Sonnet (Anthropic)    | yes                            |
| `mimo`      | Mimo (via codebone bridge)   | no                             |
| `mimo+cb`   | Mimo (via codebone bridge)   | yes                            |

`sonnet*` runs switch off the bridge env and `apiKeyHelper` via `--settings`, so they use your
Claude subscription directly. `mimo*` runs use your normal codebone module routing (Mimo module
enabled), so Mimo needs to be the active module in the codebone app.

## Quick start (give this to your agent)

Open this folder in your agent (Claude Code, Cursor, …) and paste:

```text
Run the benchmark in this repository, one config at a time:

  ~/Library/Application\ Support/codebone/venv/bin/python3 run.py --configs sonnet --runs 1
  ~/Library/Application\ Support/codebone/venv/bin/python3 run.py --configs sonnet+cb --runs 1
  ~/Library/Application\ Support/codebone/venv/bin/python3 run.py --configs mimo --runs 1
  ~/Library/Application\ Support/codebone/venv/bin/python3 run.py --configs mimo+cb --runs 1

Then read results/RESULTS.md and give me the comparison: which config is cheapest and fastest
for 3/3 tasks? Note which model served each row.
```

What to expect:

- Each run takes ~2–5 minutes. Every config should reach **3/3 tasks** — a lower score means the
  run failed, not that the config is worse.
- The plain runs (`sonnet`, `mimo`) show what the model does alone; the `+cb` rows show what
  codebone's context saves. Compare tokens first (that is what codebone targets), then time, then cost.
- Numbers move between runs (±10–20%). For real claims use `--runs 3` and the printed medians.

## Run it manually

```bash
# configs that include codebone need the codebone venv (fastapi/uvicorn/mcp):
~/Library/Application\ Support/codebone/venv/bin/python3 run.py --runs 3

# a subset:
~/Library/Application\ Support/codebone/venv/bin/python3 run.py --configs sonnet,sonnet+cb --runs 3
```

- `--configs` picks the configs (default: all four), `--runs` repeats each (medians are printed),
  `--brain builtin` uses the local model instead of the fast regex indexer for the index.
- `CODEBONE_REPO` points at the codebone checkout (default: `../pug`).
- Every raw run is appended to `results/runs.json` (tokens, turns, wall time, cost, pass/fail).

Each run starts a fresh isolated headless codebone on a free port — your menu bar app, MCP configs
and settings are never touched.

## Results

Every run is written to **[results/RESULTS.md](results/RESULTS.md)** automatically — one row per run
with the config, the model that actually served it (read from your live settings for bridged runs),
tasks passed, tokens, wall time and cost, plus medians per config. Raw data for your own tooling:
[results/runs.json](results/runs.json).

So if you run this with a different AI, the row names the model itself — no guessing which number
belongs to which setup. `cost_usd` is Claude Code's own figure; Claude Code cannot price bridged
models, take those from your provider dashboard and add them as a note.

## Verifying yourself

```bash
python3 task/make_project.py /tmp/shop   # generate the project
# ... make your edits in /tmp/shop ...
python3 task/check.py /tmp/shop          # prints the three booleans, exit 1 on failure
```
