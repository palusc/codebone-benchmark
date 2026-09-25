# codebone-benchmark

Does codebone actually save tokens, time and money? Same task, same project, different setups —
run it yourself in any agent, every result is recorded with the model that produced it.

## What's in here

- **`project/`** — a deliberately messy mini shop backend. Open this folder in your agent.
  Unhelpful names (`calc2.py`, `h_cust.py`, `tok.py`), dead legacy code, 30 distractor modules, but
  a clear folder structure (`web/`, `db/`, `utils/`, `export/`, `auth_stuff/`, `notif/`, `old/`).
  Without an architecture map an agent has to grep and read around; with codebone it asks `cb()`.
- **`PROMPT.md`** — the task, run without codebone.
- **`PROMPT-CB.md`** — the same task, run with codebone (`cb()` first).
- **`record.py`** — verifies the run, saves the row under your model, resets `project/`.
- **`task/`** — the generator and the checker behind the scenes.
- **`results/RESULTS.md`** — the comparison table, written automatically after every run.

## The task

One prompt, three changes: VAT 19% → 20%, optional `phone` field on customers, reset-token
lifetime fix. The result is checked mechanically by `task/check.py` — three booleans, exit code 1
if anything fails. A run only counts as 3/3 when all three pass.

## How to run a comparison

1. Open **`project/`** in your agent (Claude Code, Cursor, …). In codebone, select the same folder
   (menu bar → *Select Project Folder…*) so `cb()` has it indexed.
2. Pick the model in your agent's model picker.
3. Paste **`PROMPT.md`** (the plain run) and let it finish, then save the result:

   ```bash
   python3 record.py --model <the-model-you-picked> --mode plain --wall <seconds> --tokens <n> --cost <usd>
   ```

4. Paste **`PROMPT-CB.md`** (the codebone run) and save it the same way, with `--mode cb`.
5. Repeat steps 2–4 for every model you want to compare.
6. Read **`results/RESULTS.md`** — one row per run plus medians per model and mode.

Notes:

- `--wall`, `--tokens`, `--cost` are optional — take them from your agent's usage/cost display.
  The task check itself is always measured by `record.py`.
- `record.py` resets `project/` after each run (`--no-reset` to keep it as the agent left it) and
  exits 1 if the run scored below 3/3 — a failed run is a broken run, not a slow model.
- Numbers move between runs (±10–20%). For real claims run each model+mode 3 times; the medians
  table does the math.

## Results

Everything lands in [results/RESULTS.md](results/RESULTS.md) with the model name attached to each
row — so even when you switch agents or providers, the numbers stay attributable. Raw data for
your own tooling: [results/runs.json](results/runs.json).

`cost` is what you enter. Claude Code prices its own runs, but it cannot price bridged models —
take those from your provider dashboard.

## Verifying yourself

```bash
python3 task/make_project.py /tmp/shop   # generate the project
# ... make your edits in /tmp/shop ...
python3 task/check.py /tmp/shop          # prints the three booleans, exit 1 on failure
```
