"""Benchmark runner: same messy project, same task prompt, several agent configs compared.

    # with codebone (needs fastapi/uvicorn/mcp):
    ~/Library/Application\\ Support/codebone/venv/bin/python3 run.py [--runs 3] [--configs sonnet,sonnet+cb]

Configs:
    sonnet      Claude Code, plain Anthropic auth (subscription OAuth, bridge/env switched off)
    sonnet+cb   same, plus the codebone MCP context tool
    mimo        Claude Code routed through the codebone bridge to Mimo (your normal module setup)
    mimo+cb     same, plus the codebone MCP context tool

Per run it generates a fresh project copy, (cb-configs) starts an isolated headless codebone on a free
port and indexes the copy, runs `claude -p` once, then verifies the tasks with task/check.py.
Records wall time, turns, tokens and cost into results/runs.json; medians are printed at the end.
Isolated on purpose: it never touches your menu bar app, your MCP configs or your settings.json.
"""
import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODEBONE = Path(os.environ.get("CODEBONE_REPO", HERE.parent / "pug"))

CONFIGS = {
    "sonnet":    {"model": "sonnet", "cb": False, "anthropic_auth": True},
    "sonnet+cb": {"model": "sonnet", "cb": True,  "anthropic_auth": True},
    "mimo":      {"model": None,     "cb": False, "anthropic_auth": False},
    "mimo+cb":   {"model": None,     "cb": True,  "anthropic_auth": False},
}


def bridged_model() -> str:
    """The model the codebone bridge actually routes to, read from the user settings — so a run is
    always attributable even when the module is set to something other than Mimo."""
    try:
        env = json.loads((Path.home() / ".claude" / "settings.json").read_text()).get("env", {})
        return env.get("ANTHROPIC_MODEL") or "bridged model"
    except Exception:
        return "bridged model"

# For plain Anthropic auth: drop the bridge env and the codebone apiKeyHelper from the user settings,
# so Claude Code falls back to the subscription OAuth in the keychain (--settings merges over settings.json).
ANTHROPIC_SETTINGS = json.dumps({
    "apiKeyHelper": None,
    "env": {"ANTHROPIC_BASE_URL": None, "ANTHROPIC_MODEL": None, "ANTHROPIC_SMALL_FAST_MODEL": None},
})

CB_CLAUDE_MD = """# Project guidelines
## Shortcut: `cb`
When the prompt starts with `cb`, first call the MCP tool `cb()` to get the project's live architectural context
(domains, models, routes, events, file summaries). Use it instead of reading many files. For focused context call
`cb(domain=...)`, `cb(file=...)` or `cb(query=...)`.
"""


def make_project(dst: Path):
    subprocess.run([sys.executable, str(HERE / "task" / "make_project.py"), str(dst)], check=True)


def start_codebone(project: Path, brain: str, workdir: Path):
    """Headless, isolated codebone: own config/db dir, no MCP-config patching. Returns (port, index_seconds, stop)."""
    sys.path.insert(0, str(CODEBONE))
    import uvicorn
    from src.config import BASE_MODEL_FILE, Config, find_free_port
    from src.providers import FastFallbackProvider
    from src.server import create_app
    from src.service import CodeBoneService

    cfg = Config(config_file=workdir / "cb" / "config.json")
    cfg.set("project_path", str(project))
    cached = Path.home() / "Library" / "Caches" / "codebone-build" / BASE_MODEL_FILE  # left there by build_bundle.sh
    if not Path(cfg.get("model_path", "")).exists() and cached.exists():
        cfg.set("model_path", str(cached))
    service = CodeBoneService(cfg)
    if brain == "fallback" or not service.provider.available:
        service.provider = FastFallbackProvider()
    t0 = time.time()
    service.rescan_all()
    index_s = time.time() - t0

    port = find_free_port(18053)
    cfg.set("active_port", port)
    server = uvicorn.Server(uvicorn.Config(create_app(service), host="127.0.0.1", port=port,
                                            log_level="warning", lifespan="off"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(50):
        if server.started:
            break
        time.sleep(0.1)

    def stop():
        server.should_exit = True
        service.stop()

    return port, index_s, stop


def run_claude(project: Path, prompt: str, cfg, mcp_port):
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--no-session-persistence",
           "--permission-mode", "acceptEdits", "--strict-mcp-config"]
    tools = "Read Edit Write Glob Grep Bash(python3:*) Bash(ls:*) Bash(cat:*) Bash(grep:*) Bash(find:*)"
    if mcp_port:
        mcp = {"mcpServers": {"codebone": {
            "command": sys.executable, "args": ["-m", "codebone_mcp.server"],
            "env": {"CODEBONE_PORT": str(mcp_port), "PYTHONPATH": str(CODEBONE)}}}}
        cfg_path = project.parent / "mcp.json"
        cfg_path.write_text(json.dumps(mcp))
        cmd += ["--mcp-config", str(cfg_path)]
        tools += " mcp__codebone"
    cmd += ["--allowedTools", tools]
    if cfg["anthropic_auth"]:
        cmd += ["--settings", ANTHROPIC_SETTINGS]
    if cfg["model"]:
        cmd += ["--model", cfg["model"]]
    t0 = time.time()
    p = subprocess.run(cmd, cwd=project, capture_output=True, text=True, timeout=1200)
    wall = time.time() - t0
    try:
        out = json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"error": (p.stdout + p.stderr)[-500:], "wall_s": round(wall, 1)}
    u = out.get("usage", {})
    fresh_in = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
    return {
        "wall_s": round(wall, 1),
        "api_s": round(out.get("duration_api_ms", 0) / 1000, 1),
        "turns": out.get("num_turns"),
        "input": u.get("input_tokens", 0),
        "cache_write": u.get("cache_creation_input_tokens", 0),
        "cache_read": u.get("cache_read_input_tokens", 0),
        "output": u.get("output_tokens", 0),
        "fresh_in_plus_out": fresh_in + u.get("output_tokens", 0),
        "cost_usd": round(out.get("total_cost_usd", 0), 4),
    }


def check(project: Path):
    p = subprocess.run([sys.executable, str(HERE / "task" / "check.py"), str(project)],
                       capture_output=True, text=True)
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        return {"vat": False, "phone": False, "token": False}


def one_run(name: str, prompt: str, brain: str):
    cfg = CONFIGS[name]
    tmp = Path(tempfile.mkdtemp(prefix=f"cbbench-{name}-"))
    project = tmp / "shop"
    make_project(project)
    port = stop = None
    index_s = 0.0
    if cfg["cb"]:
        (project / "CLAUDE.md").write_text(CB_CLAUDE_MD)
        port, index_s, stop = start_codebone(project, brain, tmp)
        prompt = "cb: " + prompt
    try:
        res = run_claude(project, prompt, cfg, port)
    finally:
        if stop:
            stop()
    res["config"] = name
    res["model"] = ("claude-" + cfg["model"]) if cfg["anthropic_auth"] else bridged_model()
    res["index_s"] = round(index_s, 1)
    res["passed"] = check(project)
    res["tasks_ok"] = sum(res["passed"].values())
    res["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    shutil.rmtree(tmp, ignore_errors=True)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--configs", default=",".join(CONFIGS), help="comma list: " + ",".join(CONFIGS))
    ap.add_argument("--brain", choices=["fallback", "builtin"], default="fallback",
                    help="fallback = regex indexer (fast, reproducible); builtin = local model")
    args = ap.parse_args()
    names = [n.strip() for n in args.configs.split(",") if n.strip()]
    unknown = [n for n in names if n not in CONFIGS]
    if unknown:
        ap.error(f"unknown config(s): {unknown}")
    prompt = (HERE / "task" / "prompt.txt").read_text().strip()

    results = {n: [] for n in names}
    for i in range(args.runs):
        for name in names:  # interleaved so drift hits every config equally
            print(f"[run {i + 1}/{args.runs}] {name} ...", flush=True)
            r = one_run(name, prompt, args.brain)
            print("   ", r, flush=True)
            results[name].append(r)

    log = HERE / "results" / "runs.json"
    log.parent.mkdir(exist_ok=True)
    history = json.loads(log.read_text()) if log.exists() else []
    history += [r for name in names for r in results[name]]
    log.write_text(json.dumps(history, indent=2))
    write_report(history)

    keys = ["wall_s", "turns", "fresh_in_plus_out", "output", "cache_read", "cost_usd", "tasks_ok"]
    print(f"\nMedian over {args.runs} run(s) per config   (cb configs: index time not counted in wall_s)")
    print(f"{'metric':<20}" + "".join(f"{n:>14}" for n in names))
    for k in keys:
        row = f"{k:<20}"
        for n in names:
            vals = [r[k] for r in results[n] if k in r]
            row += f"{(statistics.median(vals) if vals else float('nan')):>14}"
        print(row)
    print(f"\nRaw runs: {log}")
    print(f"Report:   {HERE / 'results' / 'RESULTS.md'}")


def model_of(r) -> str:
    """Model a recorded run used; old rows without the field are derived from their config."""
    if r.get("model"):
        return r["model"]
    return "claude-sonnet" if str(r.get("config", "")).startswith("sonnet") else bridged_model()


def write_report(history):
    """results/RESULTS.md: every run with the model it actually used, so the numbers stay
    attributable when the setup changes (different module, different model, different machine)."""
    lines = [
        "# Benchmark results",
        "",
        "Generated by run.py — one row per run, plus medians per config. `cost_usd` is what Claude Code",
        "reported; for bridged models Claude Code cannot price the call, so take the real cost from your",
        "provider dashboard and note it in the PR/README you publish.",
        "",
        "| Date | Config | Model | cb | Tasks OK | Fresh in+out | Wall s | Index s | Turns | Cost USD |",
        "|------|--------|-------|----|----------|--------------|--------|---------|-------|----------|",
    ]
    for r in reversed(history):
        lines.append(
            f"| {r.get('ts', '?')[:16]} | {r.get('config', '?')} | {model_of(r)} "
            f"| {'yes' if str(r.get('config', '')).endswith('+cb') else 'no'} "
            f"| {r.get('tasks_ok', '?')}/3 | {r.get('fresh_in_plus_out', '?')} "
            f"| {r.get('wall_s', '?')} | {r.get('index_s', '?')} | {r.get('turns', '?')} "
            f"| {r.get('cost_usd', '?')} |")

    lines += ["", "## Medians per config", "",
              "| Config | Model | Runs | Tasks OK | Fresh in+out | Wall s | Cost USD |",
              "|--------|-------|------|----------|--------------|--------|----------|"]
    configs = list(dict.fromkeys(r.get("config") for r in history if r.get("config")))
    for c in configs:
        rows = [r for r in history if r.get("config") == c and "error" not in r]
        if not rows:
            continue

        def med(k):
            return statistics.median([r[k] for r in rows if k in r])

        lines.append(f"| {c} | {model_of(rows[-1])} | {len(rows)} "
                     f"| {med('tasks_ok'):g}/3 | {med('fresh_in_plus_out'):.0f} "
                     f"| {med('wall_s'):.0f} | {med('cost_usd'):.2f} |")

    (HERE / "results" / "RESULTS.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
