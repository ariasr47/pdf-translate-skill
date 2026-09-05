---
type: regex
weight: 2
target: trace
pattern: "PASS authored translations present"
match: contains
---

Every authored target landed verbatim in the output text layer. Without
this a file can look right and be empty of the translation, which is the
failure this whole pipeline exists to refuse.
