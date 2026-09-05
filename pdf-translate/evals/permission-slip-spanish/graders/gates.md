---
type: regex
weight: 2
target: trace
pattern: "PASS field parity"
match: contains
---

`verify.py`'s field-parity gate passed in this run's own output. This is
the first of the five checks `dev/canary/score.py` reports, read from the
trace rather than re-run: the skill's workflow requires the author to run
`pipeline.py verify`, so a run with no PASS line here either skipped the
gate or failed it, and both are the same verdict.
