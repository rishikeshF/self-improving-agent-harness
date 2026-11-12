#!/usr/bin/env python3
"""Set, clear or show the loop goal enforced by .claude/hooks/goal_check.py.

Usage:
  python3 scripts/goal.py "<goal text> | <check command> [| max_iters]"
  python3 scripts/goal.py off
  python3 scripts/goal.py status
"""
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOAL = ROOT / ".harness" / "goal.json"
DEFAULT_MAX = 8


def main() -> int:
    arg = " ".join(sys.argv[1:]).strip()
    if not arg or arg == "status":
        if GOAL.exists():
            print(GOAL.read_text())
        else:
            print("no active goal")
        return 0
    if arg == "off":
        GOAL.unlink(missing_ok=True)
        print("goal cleared")
        return 0

    parts = [p.strip() for p in arg.split(" | ")]
    if len(parts) < 2 or not parts[1]:
        print('error: need "<goal text> | <check command> [| max_iters]"', file=sys.stderr)
        return 1
    max_iters = DEFAULT_MAX
    if len(parts) >= 3 and parts[-1].isdigit():
        max_iters = int(parts[-1])
        check = " | ".join(parts[1:-1])
    else:
        check = " | ".join(parts[1:])
    goal = {
        "goal": parts[0],
        "check": check,
        "max_iters": max_iters,
        "iters": 0,
        "set_at": time.strftime("%H:%M:%S"),
    }
    GOAL.parent.mkdir(exist_ok=True)
    GOAL.write_text(json.dumps(goal, indent=2))
    print(f"goal set: {goal['goal']}\ncheck: {check}\nmax iterations: {max_iters}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
