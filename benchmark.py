#!/usr/bin/env python3
"""One-command, two-arm codebone benchmark.

The runner creates two fresh copies of the same generated SaaS project, launches the same coding
agent once without codebone and once with context built from codebone's architecture graph, checks
both results mechanically, and writes a plain-English verdict.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
TASK_PROMPT = ROOT / "task" / "prompt.txt"
CHECKER = ROOT / "task" / "check.py"
GENERATOR = ROOT / "task" / "make_project.py"
CONTEXT_BUILDER = ROOT / "task" / "index_context.py"
RESULTS_DIR = ROOT / "results"
RUNS_FILE = RESULTS_DIR / "runs.json"
VERDICT_FILE = RESULTS_DIR / "VERDICT.md"


def run(command: list[str], *, cwd: Path | None = None, stdin: str | None = None,
        timeout: int = 1200, check: bool = False, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    child = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True, env=env, start_new_session=True)
    try:
        stdout, stderr = child.communicate(stdin, timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        # Stop the agent's command children too, before removing its temporary project.
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.communicate()
        raise
    process = subprocess.CompletedProcess(command, child.returncode, stdout, stderr)
    if check and process.returncode:
        tail = (process.stdout + "\n" + process.stderr)[-4000:]
        raise RuntimeError(f"command failed ({process.returncode}): {' '.join(command)}\n{tail}")
    return process


def detect_agent(requested: str) -> str:
    if requested != "auto":
        if not shutil.which(requested):
            raise RuntimeError(f"{requested!r} is not installed or not on PATH")
        return requested
    for name in ("codex", "claude"):
        if shutil.which(name):
            return name
    raise RuntimeError("No supported agent CLI found. Install Codex or Claude Code, or pass --agent.")


def discover_codebone() -> tuple[Path, Path]:
    source_candidates = []
    if os.environ.get("CODEBONE_REPO"):
        source_candidates.append(Path(os.environ["CODEBONE_REPO"]).expanduser())
    source_candidates += [
        Path("/Applications/codebone.app/Contents/Resources/src"),
        Path.home() / "Applications/codebone.app/Contents/Resources/src",
        ROOT.parent / "codebone",
    ]
    python_candidates = []
    if os.environ.get("CODEBONE_PYTHON"):
        python_candidates.append(Path(os.environ["CODEBONE_PYTHON"]).expanduser())
    python_candidates += [
        Path("/Applications/codebone.app/Contents/Resources/venv/bin/python3"),
        Path.home() / "Applications/codebone.app/Contents/Resources/venv/bin/python3",
        Path.home() / "Library/Application Support/codebone/venv/bin/python3",
    ]
    source = next((path.resolve() for path in source_candidates if (path / "src" / "service.py").exists()), None)
    # Keep the venv entrypoint: resolving its symlink can bypass pyvenv.cfg.
    python = next((path.absolute() for path in python_candidates if path.exists()), None)
    if source is None or python is None:
        raise RuntimeError(
            "codebone runtime not found. Install the current macOS app, or set CODEBONE_REPO and CODEBONE_PYTHON."
        )
    return source, python


def initialise_project(project: Path) -> None:
    run([sys.executable, str(GENERATOR), str(project)], check=True)
    run(["git", "init", "-q"], cwd=project, check=True)
    run(["git", "config", "user.email", "benchmark@codeb.one"], cwd=project, check=True)
    run(["git", "config", "user.name", "codebone benchmark"], cwd=project, check=True)
    run(["git", "add", "."], cwd=project, check=True)
    run(["git", "commit", "-qm", "benchmark baseline"], cwd=project, check=True)


def build_codebone_context(project: Path, work: Path, source: Path, python: Path) -> dict[str, Any]:
    started = time.monotonic()
    output = project / "CODEBONE_CONTEXT.md"
    process = run([
        str(python), str(CONTEXT_BUILDER), "--source", str(source), "--project", str(project),
        "--output", str(output), "--work", str(work / "codebone"),
    ], timeout=1200, check=True)
    meta = json.loads(process.stdout.strip().splitlines()[-1])
    run(["git", "add", "CODEBONE_CONTEXT.md"], cwd=project, check=True)
    run(["git", "commit", "-qm", "add generated codebone context"], cwd=project, check=True)
    meta["scan_s"] = meta["index_s"]
    meta["index_s"] = round(time.monotonic() - started, 3)
    return meta


def codex_usage(events: list[dict[str, Any]]) -> dict[str, Any]:
    usages = [event.get("usage", {}) for event in events if isinstance(event.get("usage"), dict)]
    usage = usages[-1] if usages else {}
    input_tokens = usage.get("input_tokens") or usage.get("input") or 0
    cached = usage.get("cached_input_tokens") or usage.get("cached_input") or 0
    output_tokens = usage.get("output_tokens") or usage.get("output") or 0
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached,
        "output_tokens": output_tokens,
        "fresh_tokens": max(0, input_tokens - cached) + output_tokens if input_tokens or output_tokens else None,
        "total_tokens": input_tokens + output_tokens if input_tokens or output_tokens else None,
    }


def run_codex(project: Path, prompt: str, model: str | None, timeout: int) -> dict[str, Any]:
    command = [
        "codex", "exec", "--ignore-user-config", "--ephemeral", "--skip-git-repo-check",
        "--approve-for-me", "--cd", str(project), "--json", "-",
    ]
    if model:
        command[2:2] = ["--model", model]
    started = time.monotonic()
    process = run(command, cwd=project, stdin=prompt, timeout=timeout)
    wall = time.monotonic() - started
    events = []
    for line in process.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    final_messages = [
        event.get("item", {}).get("text", "")
        for event in events
        if event.get("type") == "item.completed" and event.get("item", {}).get("type") == "agent_message"
    ]
    result = {
        "exit_code": process.returncode,
        "wall_s": round(wall, 2),
        "model": model or "Codex default",
        "response": final_messages[-1] if final_messages else "",
        "stderr_tail": process.stderr[-1500:],
    }
    result.update(codex_usage(events))
    return result


def run_claude(project: Path, prompt: str, model: str | None, timeout: int) -> dict[str, Any]:
    command = [
        "claude", "-p", prompt, "--output-format", "json", "--no-session-persistence",
        "--safe-mode",
        "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
        "--permission-mode", "acceptEdits", "--allowedTools", "Read,Edit,Write,Glob,Grep,Bash",
    ]
    if model:
        command += ["--model", model]
    started = time.monotonic()
    child_env = os.environ.copy()
    # Each run has a separate project and no persistent session. Allow the documented
    # one-prompt workflow when the parent orchestrator itself is Claude Code.
    child_env.pop("CLAUDECODE", None)
    process = run(command, cwd=project, timeout=timeout, env=child_env)
    wall = time.monotonic() - started
    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError:
        payload = {}
    usage = payload.get("usage", {})
    fresh_input = (usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0))
    output = usage.get("output_tokens", 0)
    model_usage = payload.get("modelUsage", {})
    detected_model = model or (next(iter(model_usage)) if model_usage else "Claude default")
    return {
        "exit_code": process.returncode or (1 if payload.get("is_error") else 0),
        "wall_s": round(wall, 2),
        "model": detected_model,
        "response": payload.get("result", ""),
        "input_tokens": usage.get("input_tokens"),
        "cached_input_tokens": usage.get("cache_read_input_tokens"),
        "output_tokens": output or None,
        "fresh_tokens": fresh_input + output if fresh_input or output else None,
        "total_tokens": (usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)
                         + usage.get("cache_read_input_tokens", 0) + output) or None,
        "cost_usd": payload.get("total_cost_usd"),
        "turns": payload.get("num_turns"),
        "stderr_tail": process.stderr[-1500:],
    }


def run_agent(agent: str, project: Path, prompt: str, model: str | None, timeout: int) -> dict[str, Any]:
    if agent == "codex":
        return run_codex(project, prompt, model, timeout)
    if agent == "claude":
        return run_claude(project, prompt, model, timeout)
    raise RuntimeError(f"unsupported agent: {agent}")


def check_project(project: Path) -> dict[str, Any]:
    process = run([sys.executable, str(CHECKER), str(project)], timeout=60)
    try:
        return json.loads(process.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {"passed": {}, "details": {"checker": process.stderr[-1000:]}, "tasks_ok": 0, "tasks_total": 4}


def changed_files(project: Path) -> list[str]:
    process = run(["git", "status", "--porcelain"], cwd=project, timeout=30)
    return [line[3:] for line in process.stdout.splitlines() if len(line) > 3]

def trial(mode: str, agent: str, model: str | None, timeout: int, source: Path, python: Path,
          keep: bool, run_id: str, trial_index: int) -> dict[str, Any]:
    work = Path(tempfile.mkdtemp(prefix=f"codebone-benchmark-{mode}-"))
    project = work / "northstar"
    started = time.monotonic()
    row = {
        "run_id": run_id, "trial": trial_index,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": mode, "agent": agent, "model": model or "CLI default (unresolved)",
        "context_mode": "static-fallback-with-task-derived-queries",
        "index_s": 0.0, "indexed_files": 0, "context_chars": 0,
        "tasks_ok": 0, "tasks_total": 4, "passed": {}, "details": {},
        "exit_code": 1, "wall_s": 0.0, "first_run_s": 0.0,
    }
    try:
        initialise_project(project)
        checker_hash = hashlib.sha256(CHECKER.read_bytes()).hexdigest()
        if mode == "codebone":
            row.update(build_codebone_context(project, work, source, python))
            prefix = (
                "Before editing, read CODEBONE_CONTEXT.md. It was generated by codebone from this exact project copy. "
                "Use its architecture map and focused results to go directly to the relevant runtime paths.\n\n"
            )
        else:
            prefix = (
                "Solve this run using only the coding agent's normal repository search and file tools. "
                "Do not call codebone or use any prebuilt architecture context.\n\n"
            )
        prefix += "Work only inside this project. Do not inspect or modify the external benchmark harness.\n\n"
        prompt = prefix + TASK_PROMPT.read_text(encoding="utf-8")
        print(f"  {mode}: launching {agent} …", flush=True)
        row.update(run_agent(agent, project, prompt, model, timeout))
        if hashlib.sha256(CHECKER.read_bytes()).hexdigest() != checker_hash:
            raise RuntimeError("External checker changed during the run; results are invalid.")
        check = check_project(project)
        row.update(check)
        row["changed_files"] = changed_files(project)
        row["first_run_s"] = round(row["wall_s"] + row["index_s"], 2)
    except (Exception, KeyboardInterrupt) as exc:
        row["exit_code"] = 130 if isinstance(exc, KeyboardInterrupt) else 1
        row["error"] = f"{type(exc).__name__}: {exc}"
        row["wall_s"] = round(time.monotonic() - started, 2)
        row["first_run_s"] = row["wall_s"]
        row["details"] = {"runner": row["error"]}
    finally:
        if keep:
            row["workdir"] = str(work)
        else:
            shutil.rmtree(work)
    return row


def median(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [row[key] for row in rows if isinstance(row.get(key), (int, float))]
    return statistics.median(values) if values else None


def saving(before: float | None, after: float | None) -> float | None:
    if before in (None, 0) or after is None:
        return None
    return (before - after) / before * 100


def fmt(value: float | None, suffix: str = "", digits: int = 1) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}{suffix}"


def efficiency_label(value: float | None, better: str, worse: str) -> str:
    if value is None:
        return "n/a"
    return f"{abs(value):.1f}% {better if value >= 0 else worse}"


def verdict_for(plain: list[dict[str, Any]], codebone: list[dict[str, Any]]) -> tuple[str, str, dict[str, Any]]:
    metrics = {
        "plain_tasks": median(plain, "tasks_ok"),
        "codebone_tasks": median(codebone, "tasks_ok"),
        "plain_tokens": median(plain, "fresh_tokens"),
        "codebone_tokens": median(codebone, "fresh_tokens"),
        "plain_agent_s": median(plain, "wall_s"),
        "codebone_agent_s": median(codebone, "wall_s"),
        "codebone_index_s": median(codebone, "index_s"),
        "plain_first_s": median(plain, "first_run_s"),
        "codebone_first_s": median(codebone, "first_run_s"),
    }
    metrics["token_saving_pct"] = saving(metrics["plain_tokens"], metrics["codebone_tokens"])
    metrics["agent_time_saving_pct"] = saving(metrics["plain_agent_s"], metrics["codebone_agent_s"])
    metrics["first_run_saving_pct"] = saving(metrics["plain_first_s"], metrics["codebone_first_s"])
    pt, ct = metrics["plain_tasks"], metrics["codebone_tasks"]
    token_gain = metrics["token_saving_pct"]
    time_gain = metrics["agent_time_saving_pct"]
    failed = [row for row in plain + codebone if row.get("exit_code") not in (None, 0)]
    if failed:
        return "INCONCLUSIVE", "At least one agent process failed, so no product verdict was calculated.", metrics
    if pt is None or ct is None or len(plain) != len(codebone):
        return "INCONCLUSIVE", "A complete pair of runs was not recorded.", metrics
    if ct > pt:
        return "HELPS", f"codebone completed more verified tasks ({ct:g}/4 vs {pt:g}/4).", metrics
    if ct < pt:
        return "DOES NOT HELP", f"codebone completed fewer verified tasks ({ct:g}/4 vs {pt:g}/4).", metrics
    if ct < 4:
        return "INCONCLUSIVE", f"both modes completed only {ct:g}/4 tasks; correctness is not high enough for an efficiency claim.", metrics
    gains = [value for value in (token_gain, time_gain) if value is not None]
    if gains and max(gains) >= 10 and not any(value < -20 for value in gains):
        return "HELPS", "both modes passed 4/4 and codebone reduced measured agent work by at least 10%.", metrics
    if gains and all(value <= -10 for value in gains):
        return "DOES NOT HELP", "both modes passed 4/4, but codebone used at least 10% more measured agent work.", metrics
    return "MIXED", "both modes passed 4/4, but the measured efficiency difference is below the decision threshold.", metrics


def write_verdict(rows: list[dict[str, Any]], run_id: str, agent: str, model: str | None, runs: int) -> None:
    current = [row for row in rows if row.get("run_id") == run_id]
    plain = [row for row in current if row["mode"] == "plain"]
    codebone = [row for row in current if row["mode"] == "codebone"]
    verdict, reason, metrics = verdict_for(plain, codebone)
    task_names = ["vat_policy", "customer_phone", "reset_token_ttl", "webhook_idempotency"]
    lines = [
        "# codebone benchmark verdict",
        "",
        f"## {verdict}",
        "",
        reason,
        "",
        f"Run `{run_id}` · {agent} · {model or 'default model'} · {runs} paired trial(s)",
        "",
        "| Metric | Plain | With codebone | Difference |",
        "|---|---:|---:|---:|",
        f"| Verified tasks | {fmt(metrics['plain_tasks'], '/4', 0)} | {fmt(metrics['codebone_tasks'], '/4', 0)} | {fmt((metrics['codebone_tasks'] or 0) - (metrics['plain_tasks'] or 0), '', 0)} |",
        f"| Fresh agent tokens | {fmt(metrics['plain_tokens'], '', 0)} | {fmt(metrics['codebone_tokens'], '', 0)} | {efficiency_label(metrics['token_saving_pct'], 'less', 'more')} |",
        f"| Agent time | {fmt(metrics['plain_agent_s'], ' s')} | {fmt(metrics['codebone_agent_s'], ' s')} | {efficiency_label(metrics['agent_time_saving_pct'], 'faster', 'slower')} |",
        f"| Context preparation incl. indexing | 0.0 s | {fmt(metrics['codebone_index_s'], ' s')} | — |",
        f"| First run incl. indexing | {fmt(metrics['plain_first_s'], ' s')} | {fmt(metrics['codebone_first_s'], ' s')} | {efficiency_label(metrics['first_run_saving_pct'], 'faster', 'slower')} |",
        "",
        "## Mechanical task checks",
        "",
        "| Task | Plain | With codebone |",
        "|---|:---:|:---:|",
    ]
    for task in task_names:
        plain_passes = sum(bool(row.get("passed", {}).get(task)) for row in plain)
        cb_passes = sum(bool(row.get("passed", {}).get(task)) for row in codebone)
        lines.append(f"| `{task}` | {plain_passes}/{len(plain)} | {cb_passes}/{len(codebone)} |")
    lines += [
        "",
        "## Interpretation",
        "",
        "- Correctness is checked by code outside both editable project copies.",
        "- Both modes use the same generated project, task, agent and model in fresh sessions.",
        "- The codebone arm receives context generated from that exact project copy immediately before the run.",
        "- Scope: static fallback graph plus four fixed task-derived queries. No live MCP calls or local model synthesis are measured.",
        "- This is a generated sample application, not a production-scale codebase. Query selection is provided by the harness.",
        "- Fresh tokens exclude cached inputs and include outputs; they are not a bill or a cost estimate.",
        "- Agent time excludes context preparation; the separate first-run row includes indexing, context generation and setup.",
        "- One paired run is a personal smoke test, not a publishable universal claim. Use `--runs 3` or more for medians.",
        "",
        f"Raw data: [`runs.json`](runs.json)",
    ]
    errors = [row for row in current if row.get("exit_code")]
    if errors:
        lines += ["", "## Run errors", ""]
        for row in errors:
            lines.append(f"- {row['mode']}: {row.get('error') or row.get('stderr_tail') or 'Agent exited unsuccessfully'}")
    RESULTS_DIR.mkdir(exist_ok=True)
    VERDICT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an automatic plain-vs-codebone benchmark")
    parser.add_argument("--agent", choices=["auto", "codex", "claude"], default="auto")
    parser.add_argument("--model", help="optional model override passed to both isolated runs")
    parser.add_argument("--runs", type=int, default=1, help="paired trials; use 3+ for stable medians")
    parser.add_argument("--timeout", type=int, default=1200, help="seconds allowed per agent run")
    parser.add_argument("--keep-workdirs", action="store_true", help="keep isolated projects for inspection")
    parser.add_argument("--dry-run", action="store_true", help="validate generation, checker and codebone indexing only")
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs must be at least 1")
    if args.timeout < 1:
        parser.error("--timeout must be at least 1")

    agent = detect_agent(args.agent)
    source, python = discover_codebone()
    print(f"Agent: {agent}{' (' + args.model + ')' if args.model else ''}")
    print(f"codebone: {source}")

    if args.dry_run:
        work = Path(tempfile.mkdtemp(prefix="codebone-benchmark-dry-"))
        try:
            project = work / "northstar"
            initialise_project(project)
            baseline = check_project(project)
            context = build_codebone_context(project, work, source, python)
            print(json.dumps({"baseline": baseline, "context": context}, indent=2))
            return 0 if baseline.get("tasks_ok") == 0 and context.get("indexed_files", 0) >= 100 else 1
        finally:
            shutil.rmtree(work, ignore_errors=True)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    RESULTS_DIR.mkdir(exist_ok=True)
    history = json.loads(RUNS_FILE.read_text()) if RUNS_FILE.exists() else []
    for trial_index in range(1, args.runs + 1):
        print(f"\nPaired trial {trial_index}/{args.runs}", flush=True)
        order = ("plain", "codebone") if trial_index % 2 else ("codebone", "plain")
        for mode in order:
            row = trial(mode, agent, args.model, args.timeout, source, python, args.keep_workdirs, run_id, trial_index)
            history.append(row)
            # Persist each arm, so interruptions cannot erase the completed half.
            pending = RUNS_FILE.with_suffix(".tmp")
            pending.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")
            pending.replace(RUNS_FILE)
            write_verdict(history, run_id, agent, args.model, args.runs)
            print(f"  {mode}: {row['tasks_ok']}/4 tasks · {row['wall_s']} s · {row.get('fresh_tokens') or 'n/a'} fresh tokens", flush=True)
            if row.get("exit_code"):
                print(f"  Run failed; diagnostic report: {VERDICT_FILE}", file=sys.stderr)
                return row["exit_code"]

    print(f"\nVerdict: {VERDICT_FILE}")
    print(VERDICT_FILE.read_text(encoding="utf-8").splitlines()[2])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nBenchmark interrupted.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"\nBenchmark failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
