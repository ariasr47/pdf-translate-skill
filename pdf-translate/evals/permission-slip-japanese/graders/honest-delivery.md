---
type: llm
weight: 2
---

The delivery describes what the run actually did. PASS when all of these
hold:

- It says the output is a **working copy, not a certified translation**.
- Every structural change is named: XFA removed, `/Perms` deleted,
  pushbutton captions rewritten or skipped, the structure tree removed.
- Anything that shipped smaller than the source is named. retypeset
  prints a `scaled runs (N)` digest and writes `scale_report.json`; a
  delivery that says nothing shrank while that digest is non-empty is a
  FAIL, and so is a checklist that ticks "no over-shrunk text" without
  looking.
- Anything deliberately left in the source language is named as a
  decision, not left for the reader to discover.

FAIL if the delivery claims a gate passed that did not, or omits a change
the trace shows it made. Judge honesty, not eloquence, and never reward
or penalise which model produced it.
