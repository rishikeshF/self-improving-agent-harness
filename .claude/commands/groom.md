---
description: Groom all open issues in parallel, one pm subagent per issue.
---

1. List issue files with `Status: open` in `_docs/issues/` (skip README.md).
2. Launch one `pm` subagent per issue, all in the same message so they run in parallel. Give each only its file path.
3. When all return, print a table: issue, lane, criteria count, open questions.
4. Check lane ownership: if two issues in different lanes list the same file in Constraints, tell me and propose a fix. Do not start implementation.
5. Append to `_docs/agent-log.md`: `HH:MM | orchestrator | groomed N issues in parallel | -`.
6. Commit: `process: groom backlog`.
