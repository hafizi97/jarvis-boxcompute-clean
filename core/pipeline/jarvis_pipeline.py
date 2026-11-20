#!/usr/bin/env python3
"""JARVIS Centralized Command Pipeline.

One entry point that audits the project, compiles every Python file, validates
the JSON configuration, runs the test suite when one exists, and writes a
report.  Exit code is 0 only when every gate passed.

Usage:
    python3 core/pipeline/jarvis_pipeline.py --mode full
    python3 core/pipeline/jarvis_pipeline.py --mode audit
    python3 core/pipeline/jarvis_pipeline.py --mode test
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path("/home/faiz/Jarvis")
PIPELINE_DIR = BASE_DIR / "core" / "pipeline"
LOG_FILE = PIPELINE_DIR / "pipeline_run.log"
REPORT_DIR = BASE_DIR / "reports"

RESULTS: list[tuple[str, bool, str]] = []


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [JARVIS Pipeline] {msg}"
    print(line)
    try:
        PIPELINE_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def run(cmd: list[str], cwd: Path = BASE_DIR, timeout: int = 120) -> tuple[int, str, str]:
    log("Running: " + " ".join(cmd))
    try:
        res = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout,
        )
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout}s"
    if res.stdout.strip():
        log("Output: " + res.stdout.strip()[:2000])
    if res.stderr.strip():
        log("Stderr: " + res.stderr.strip()[:2000])
    return res.returncode, res.stdout, res.stderr


def record(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    log(f"{'PASS' if ok else 'FAIL'} — {name}" + (f" ({detail})" if detail else ""))


def task_management() -> bool:
    """Git state and the repository's basic shape."""
    ok = True
    code, out, _ = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], timeout=20)
    branch = out.strip() or "?"
    if code != 0:
        ok = False
    code, out, _ = run(["git", "status", "--porcelain"], timeout=30)
    dirty = len([ln for ln in out.splitlines() if ln.strip()])
    log(f"Branch {branch}; {dirty} uncommitted path(s)")
    record("git status", ok, f"branch={branch}, changes={dirty}")
    return ok


def task_explore() -> bool:
    """Project health: required paths, inventories, config JSON, free disk."""
    ok = True
    required = [
        BASE_DIR / "main.py",
        BASE_DIR / "core" / "pipeline" / "jarvis_pipeline.py",
        BASE_DIR / "config" / "api_keys.json",
        Path("/home/faiz/.config/opencode/opencode.json"),
    ]
    for path in required:
        exists = path.exists()
        record(f"exists: {path}", exists)
        ok = ok and exists

    py_files = [p for p in BASE_DIR.rglob("*.py")
                if "tools/scrapling" not in p.as_posix()
                and "__pycache__" not in p.as_posix()]
    actions = list((BASE_DIR / "actions").glob("*.py"))
    plugins = list((BASE_DIR / "plugins").glob("*.py"))
    log(f"Inventory: {len(py_files)} Python files, {len(actions)} actions, {len(plugins)} plugins")
    record("inventory", len(py_files) > 0, f"{len(py_files)} py / {len(actions)} actions / {len(plugins)} plugins")

    for cfg in (BASE_DIR / "config" / "api_keys.json",
                Path("/home/faiz/.config/opencode/opencode.json"),
                BASE_DIR / "core" / "config" / "mcp_servers.json"):
        if not cfg.exists():
            continue
        try:
            json.loads(cfg.read_text(encoding="utf-8"))
            record(f"json valid: {cfg.name}", True)
        except Exception as exc:  # noqa: BLE001 — report, never crash the pipeline
            record(f"json valid: {cfg.name}", False, str(exc)[:120])
            ok = False

    free_gb = shutil.disk_usage("/home").free / (1024 ** 3)
    record("disk free > 0.5 GB", free_gb > 0.5, f"{free_gb:.1f} GB")
    ok = ok and free_gb > 0.5
    return ok


def task_lint() -> bool:
    """Compile every Python file; use ruff when it is available."""
    ruff = shutil.which("ruff")
    if ruff:
        code, out, err = run([ruff, "check", "core", "actions", "plugins"], timeout=180)
        record("ruff", code == 0, (err or out).strip().splitlines()[-1] if (err or out).strip() else "")
        return code == 0

    code, out, err = run(
        [sys.executable, "-m", "compileall", "-q", "-x", r"(tools/scrapling|__pycache__)", "."],
        timeout=180,
    )
    detail = "" if code == 0 else (err or out).strip()[:200]
    record("compileall", code == 0, detail)
    return code == 0


def task_tests() -> bool:
    """Run the project's test suite when one exists; otherwise compile gate."""
    search_dirs = [BASE_DIR / "tests", BASE_DIR / "test"]
    tests: list[Path] = []
    for d in search_dirs:
        if d.is_dir():
            tests.extend(d.rglob("test_*.py"))
    tests.extend(BASE_DIR.glob("test_*.py"))
    tests = [p for p in tests if "__pycache__" not in p.as_posix()]

    pytest = shutil.which("pytest") or shutil.which("pytest-3")
    if tests and pytest:
        code, out, err = run([pytest, "-q", *[str(p) for p in tests]], timeout=300)
        tail = (out or err).strip().splitlines()[-1] if (out or err).strip() else ""
        record("pytest", code == 0, tail[:160])
        return code == 0
    if tests and not pytest:
        record("pytest", False, f"{len(tests)} test file(s) but pytest not installed")
        return False
    record("automated tests", True, "no tests/ suite; compile gate used")
    return True


def task_report() -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    path = REPORT_DIR / f"pipeline-{stamp}.md"
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    lines = [
        "# JARVIS Pipeline Report",
        "",
        f"- Time: {datetime.now().isoformat(timespec='seconds')}",
        f"- Result: {passed}/{total} gates passed",
        f"- Host: {os.uname().nodename}",
        "",
        "| Gate | Result | Detail |",
        "|------|--------|--------|",
    ]
    for name, ok, detail in RESULTS:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {detail.replace('|', '/')} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"Report written: {path}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="JARVIS Centralized Command Pipeline")
    parser.add_argument(
        "--mode", default="full", choices=["full", "audit", "test", "lint"],
        help="full = all gates; audit = management + explore; lint/test = single gate",
    )
    args = parser.parse_args()

    started = time.monotonic()
    log(f"Starting pipeline in mode: {args.mode}")

    ok = True
    if args.mode in ("full", "audit"):
        ok = task_management() and ok
        ok = task_explore() and ok
    if args.mode in ("full", "lint", "audit"):
        ok = task_lint() and ok
    if args.mode in ("full", "test"):
        ok = task_tests() and ok

    path = task_report()
    elapsed = time.monotonic() - started
    log(f"Pipeline {'completed' if ok else 'FAILED'} in {elapsed:.1f}s — {path}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
