---
type: regex
weight: 1
target: trace
pattern: "FAIL untranslated running text"
match: not_contains
---

No sentence of the source language survived as running text. A kept run
(the quoted `/Title`, an allowlisted phrase) is printed as a `note:` and
is not a failure; this grader only rejects the FAIL.
