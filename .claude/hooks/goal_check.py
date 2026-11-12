#!/usr/bin/env python3
"""Stop hook: the verification loop.

If a goal is active (.harness/goal.json), run its check command when the main
agent tries to stop. If the check fails, block the stop (exit 2) and feed the
failure back so the agent keeps working. Gives up after max_iters.
No active goal -> never blocks.
"""
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or pathlib.Path(__file__).resolve().parents[2])
GOAL = ROOT / ".harness" / "goal.json"
LOG = ROOT / ".harness" / "loop.log"
TAIL = 3000


def log(line: str) -> None:
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {line}\n")


def main() -> int:
    try:
        json.load(sys.stdin)  # hook payload; not needed, but drain it
    except Exception:
        pass

    if not GOAL.exists():
        return 0
    goal = json.loads(GOAL.read_text())
    goal["iters"] = goal.get("iters", 0) + 1
    GOAL.write_text(json.dumps(goal, indent=2))

    try:
        check_process = subprocess.run(
            goal["check"], shell=True, cwd=ROOT, capture_output=True, text=True, timeout=840
        )
        check_passed = check_process.returncode == 0
        check_output_tail = (check_process.stdout + check_process.stderr)[-TAIL:]
    except subprocess.TimeoutExpired:
        check_passed = False
        check_output_tail = "check command timed out"

    if check_passed:
        log(f"PASS iter {goal['iters']}: {goal['goal']}")
        GOAL.unlink(missing_ok=True)
        return 0

    if goal["iters"] >= goal["max_iters"]:
        log(f"CAP iter {goal['iters']}: {goal['goal']} still failing, letting agent stop")
        print(
            f"Goal '{goal['goal']}' still failing after {goal['iters']} iterations. "
            "Stopping. Report what is still failing to the human.",
            file=sys.stderr,
        )
        GOAL.unlink(missing_ok=True)
        return 0

    log(f"FAIL iter {goal['iters']}/{goal['max_iters']}: {goal['goal']}")
    print(
        f"Goal not met: {goal['goal']}\n"
        f"Check `{goal['check']}` failed (iteration {goal['iters']}/{goal['max_iters']}).\n"
        f"Output tail:\n{check_output_tail}\n"
        "Keep working on the cause. Do not weaken tests or the check to pass.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
