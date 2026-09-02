# The reviser step — what a second reader checks, and how to record it

Every gate in this skill checks the **file**: fields, layout, placement, the
text layer, the export values, the code points. `qa_check.py` checks the
**mapping** for the mechanical defects a reviser catches first: a figure that
moved, a line left in the source language, one label named two ways, a
missing colon.

None of that can read. 養子支援 ("adoption support") on a child-support page
passes every gate in this repository, because the page is beautiful and the
string is present. A wrong term of art is invisible to software and obvious
to a native reader of that document class.

So the review step is a **deliverable**, not an optional extra. Produce it
for every job.

## 1. Reviewer checklist (required deliverable)

Copy this into the delivery. Answer every line; "not checked" is an answer.

```
Document class:            (one sentence a librarian could file)
Issuer:                    (or none / unknown)
Parallel text consulted:   (URL/path of THIS document in the target
                            language, or none, or not searched)
Language pair / register:  (e.g. EN -> es-MX, plain-language public form)

TERMINOLOGY
[ ] Terms of art match the parallel text, or the class's established usage
[ ] No calques and no words invented on the page
[ ] Identifiers the reader must write, hand over or search are unchanged
    (form and schedule names, statutes, case numbers, URLs, paper size)
[ ] Job termbase (glossary.csv), if any, is honoured

ACCURACY
[ ] Every figure, amount, percentage and deadline matches the source
[ ] Dates: order is right for the locale AND the document is not telling
    the reader to write a particular format
[ ] Nothing added, nothing dropped; conditions ("if", "unless", "only")
    survive
[ ] Negations survive

FLUENCY AND REGISTER
[ ] Reads as this document class does in the target language
[ ] Consistent: one source term, one target term throughout
[ ] Forms of address and formality match the issuer's own register

PRESENTATION (after looking at rendered pages, not before)
[ ] Every page rendered next to the original and inspected
[ ] No clipped, over-shrunk or overlapping text; allow_scale cores listed
[ ] Dot leaders, checkboxes, rules and columns unchanged
[ ] Widget tooltips, dropdown labels and defaults are in the target language

STRUCTURE
[ ] verify.py exits 0; qa_check.py findings reviewed, each accepted or fixed
[ ] Fields fill and submit; links and bookmarks work

SIGN-OFF
Reviewed by:               (name, role)
Qualified in the pair:     (yes / no)
Date:
Remaining risks:
```

## 2. Who the reviser should be

For court, government, medical and legal filings, name a **qualified human
reviser** in the delivery, and say plainly that the scripts are not that
person. This is the professional standard, not a courtesy: ISO 17100 defines
translation as translation *plus* revision by a second person, and courts
that accept translated filings expect a human to stand behind them (in
California, the Judicial Council's own translated forms are prepared and
reviewed by people, and are supplied as informational aids — see
`compliance.md`).

If no human reviser is available, say that too, in those words. A delivery
that quietly implies review happened is worse than one that admits it did
not.

## 3. Optional: a model as a first-pass reviser

Any model can run a review pass; it does not replace the human one, and it
must not be presented as if it did. If you use one, use a real error
typology rather than "does this look good" — MQM (Multidimensional Quality
Metrics) is the standard one, and its top-level categories are what the
checklist above is organised around.

Prompt template (fill the four identity facts first — a reviser who does not
know what the document *is* cannot judge register):

```
You are revising a translation of a {document class} issued by {issuer},
from {source language} into {target language}, register: {register}.
A published translation of this same document {exists at URL / does not
exist / was not searched}.

For each segment below, report every error you find. Use the MQM
categories: terminology, accuracy (mistranslation, omission, addition,
untranslated), linguistic conventions (grammar, spelling, punctuation),
style, locale conventions (number, date, currency, address format),
audience appropriateness. Severity: critical (changes what the reader
must do), major, minor.

Do not rewrite anything you cannot justify. If a term is a form name,
statute, case number or anything the reader must write down, hand over or
search for, it is CORRECT for it to remain in {source language}: do not
report it.

Return JSON only, matching this schema:
{schema}

Segments:
{source} -> {target}   (one per line, or as JSON)
```

## 4. `review.json` schema

```jsonc
{
  "document": {
    "class": "string",
    "issuer": "string|null",
    "parallel_text": "string|null",
    "pair": "en->es-MX",
    "register": "string"
  },
  "reviewer": {
    "kind": "human|model",
    "name": "string",
    "qualified_in_pair": true
  },
  "findings": [
    {
      "core": "source string as it appears in translations.json",
      "target": "the translation reviewed",
      "category": "terminology|accuracy|linguistic-conventions|style|"
                  "locale-conventions|audience-appropriateness",
      "subtype": "mistranslation|omission|addition|untranslated|...",
      "severity": "critical|major|minor",
      "detail": "what is wrong",
      "suggestion": "proposed target, or null",
      "resolution": "accepted|rejected|open"
    }
  ],
  "summary": {
    "critical": 0, "major": 0, "minor": 0,
    "verdict": "ship|revise|do-not-ship",
    "remaining_risks": "string"
  }
}
```

Keep `review.json` beside `translations.json`. Nothing in the pipeline reads
it — it is for the humans who accept the work, and for the next person who
has to touch this document.
