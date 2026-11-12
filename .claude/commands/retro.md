---
description: Hill-climbing loop. Retro agent proposes up to 3 fixes from recent failures; I approve; agent-behaviour changes must pass the eval regression check.
---

1. Launch the `retro` subagent. Wait for its proposal file in `_docs/retros/`.
2. Show me each proposed change (file, old text, new text, evidence) and ask which ones to apply. Do not apply anything before I answer.
3. For each change I approve:
   - Apply it exactly as written.
   - Kind `process`: commit `process: retro - <failure mode>`.
   - Kind `agent-behaviour` (prompts, tool descriptions):
     a. If `evals/results/` has no run from before this change, run `make eval` first (with the change stashed) to get a baseline.
     b. Apply the change, run `make eval`, then `python3 scripts/compare_eval_runs.py`.
     c. NO REGRESSION: commit `process: retro - <failure mode>` and include the pass-rate lines in the commit body.
     d. REGRESSION: revert the change, and note in the proposal file that it was rejected and why.
4. Append the outcome to the proposal file under `## Outcome` (applied / rejected / skipped, per change).
5. Append to `_docs/agent-log.md`: `HH:MM | retro | <N> proposed, <N> applied, <N> rejected | <commit hashes>`.

When to run /retro: after every 2 QA FAILs, after each `make eval`, and once before writing the final README.
