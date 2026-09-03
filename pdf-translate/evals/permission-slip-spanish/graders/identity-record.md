---
type: llm
weight: 2
---

Before authoring any translation, the run wrote down four identity facts
about the document, and they are visible in its notes or its delivery:

1. **Class** — one sentence a librarian could file it under.
2. **Issuer** — who published it, or an explicit `none` / `unknown`.
3. **Parallel text** — a URL or path for this same document in the target
   language, or an explicit `none`, or `not searched`.
4. **Identifiers** — the names on this PDF the reader must still write,
   find or say in the source language.

PASS if all four are present and the parallel-text answer is explicit
(naming `none` or `not searched` counts; silence does not). FAIL if the
run went straight to translating, or if it asserted a parallel text it
did not actually look for.

Do not judge the quality of the translation here, and do not reward or
penalise which model produced it.
