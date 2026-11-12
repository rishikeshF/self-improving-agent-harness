---
description: Set or clear the loop goal. Usage /goal <goal text> | <check command> [| max_iters]   or   /goal off   or   /goal status
---

Run exactly this (keep the double quotes, the | separators are parsed by the script, not the shell) and show me the output:

```
python3 scripts/goal.py "$ARGUMENTS"
```

If a goal is now active, start working toward it immediately. You will not be allowed to stop until the check command exits 0 (or the iteration cap is hit, in which case stop and report what is still failing).
