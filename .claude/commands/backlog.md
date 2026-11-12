---
description: Orchestrator loop. Work through all open issues until none are left, using the PM -> Engineer -> QA lifecycle with parallel lanes.
---

You are the orchestrator. Follow `_docs/process.md` lifecycle. You do not groom, implement or test yourself.

First set the loop goal so you cannot stop early:
`python3 scripts/goal.py "backlog empty and tests green | python3 scripts/backlog_done.py && make test | 12"`

Then loop:
1. Find issues not `closed`. Any still `open` -> run the /groom flow for them.
2. Pick up to 3 groomed issues whose `Depends on` are all closed and whose lanes differ.
3. Run the /lanes flow for them (engineers in parallel, QA per lane, FAIL loops back).
4. Merge PASSed lanes one at a time (auto-merge allowed in this mode), `make test` after each, close the issue.
5. Repeat.

Stop when `scripts/backlog_done.py` exits 0 and `make test` passes. Then `python3 scripts/goal.py off` and give me a summary table: issue, rounds, verdict, commits.
