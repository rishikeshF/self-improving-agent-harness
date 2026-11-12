# QA reports

One file per issue: `NN.md`. Rerun appends a new section; never delete old ones.

```
## QA: PASS | FAIL  (round N, HH:MM)
- [x] criterion 1 — how checked
- [ ] criterion 2 — what failed, file:line, repro
Uncovered cases found: ...
Command: make test  ->  <result line>
```

A single failing criterion means FAIL.
