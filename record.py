"""Saves one benchmark run: verifies ./project, records the row under the model it ran on,
rewrites results/RESULTS.md, then resets ./project so the next run starts pristine.

    python3 record.py --model claude-sonnet --mode plain
    python3 record.py --model xiaomi/mimo-v2.6-flash --mode cb --wall 92 --tokens 130000 --cost 0.42

--mode plain = run with PROMPT.md, --mode cb = run with PROMPT-CB.md.
--wall/--tokens/--cost are optional, take them from your agent's usage/cost display; the task
check itself is always measured (3 booleans, all must pass for the row to count as 3/3).
"""
import argparse
import json
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE / "project"
RUNS = HERE / "results" / "runs.json"


def check() -> dict:
    p = subprocess.run([sys.executable, str(HERE / "task" / "check.py"), str(PROJECT)],
                       capture_output=True, text=True)
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        return {"vat": False, "phone": False, "token": False}


def reset():
    import shutil
    shutil.rmtree(PROJECT, ignore_errors=True)
    subprocess.run([sys.executable, str(HERE / "task" / "make_project.py"), str(PROJECT)], check=True)


def write_report(history):
    """results/RESULTS.md — every run with the model that served it, so numbers stay attributable
    when the setup changes (other model, other agent, other machine)."""
    def model_of(r):
        if r.get("model"):
            return r["model"]
        return "claude-sonnet" if str(r.get("config", "")).startswith("sonnet") else "bridged model"

    def mode_of(r):
        return r.get("mode") or ("cb" if str(r.get("config", "")).endswith("+cb") else "plain")

    lines = [
        "# Benchmark results",
        "",
        "Written by record.py — one row per run, medians per model+mode. `cost` is what you or your",
        "agent entered; Claude Code cannot price bridged models, take those from your provider dashboard.",
        "",
        "| Date | Model | Mode | Tasks OK | Fresh in+out | Wall s | Cost USD |",
        "|------|-------|------|----------|--------------|--------|----------|",
    ]
    for r in reversed(history):
        lines.append(
            f"| {r.get('ts', '?')[:16]} | {model_of(r)} | {mode_of(r)} "
            f"| {r.get('tasks_ok', '?')}/3 | {r.get('fresh_in_plus_out', '?') or '—'} "
            f"| {r.get('wall_s', '?') or '—'} | {r.get('cost_usd', '?') or '—'} |")

    lines += ["", "## Medians per model and mode", "",
              "| Model | Mode | Runs | Tasks OK | Fresh in+out | Wall s | Cost USD |",
              "|-------|------|------|----------|--------------|--------|----------|"]
    groups = list(dict.fromkeys((model_of(r), mode_of(r)) for r in history))
    for model, mode in groups:
        rows = [r for r in history if model_of(r) == model and mode_of(r) == mode and "error" not in r]
        if not rows:
            continue

        def med(k):
            vals = [r[k] for r in rows if r.get(k) not in (None, "")]
            return statistics.median(vals) if vals else None

        def fmt(v, spec=".0f"):
            return "—" if v is None else format(v, spec)

        lines.append(f"| {model} | {mode} | {len(rows)} | {fmt(med('tasks_ok'), 'g')}/3 "
                     f"| {fmt(med('fresh_in_plus_out'))} | {fmt(med('wall_s'))} | {fmt(med('cost_usd'), '.2f')} |")

    (HERE / "results" / "RESULTS.md").write_text("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="model that served the run, e.g. claude-sonnet")
    ap.add_argument("--mode", required=True, choices=["plain", "cb"], help="plain = PROMPT.md, cb = PROMPT-CB.md")
    ap.add_argument("--wall", type=float, help="wall time in seconds (from your agent's display)")
    ap.add_argument("--tokens", type=int, help="fresh input+output tokens (from your agent's usage display)")
    ap.add_argument("--cost", type=float, help="cost in USD (from your agent's cost display)")
    ap.add_argument("--no-reset", action="store_true", help="keep ./project as the agent left it")
    args = ap.parse_args()

    passed = check()
    row = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": args.model,
        "mode": args.mode,
        "tasks_ok": sum(passed.values()),
        "passed": passed,
        "fresh_in_plus_out": args.tokens,
        "wall_s": args.wall,
        "cost_usd": args.cost,
    }
    history = json.loads(RUNS.read_text()) if RUNS.exists() else []
    history.append(row)
    RUNS.parent.mkdir(exist_ok=True)
    RUNS.write_text(json.dumps(history, indent=2))
    write_report(history)

    if not args.no_reset:
        reset()

    print(json.dumps(row))
    print(f"saved: {HERE / 'results' / 'RESULTS.md'}" + ("" if args.no_reset else "  (project reset for the next run)"))
    sys.exit(0 if row["tasks_ok"] == 3 else 1)


if __name__ == "__main__":
    main()
