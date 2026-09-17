# Session log — 2026-09-17 — FL-150 → Japanese, three gate fixes, the review loop

**This log is a reconstruction from within the session, not a raw transcript.**
The session had been compacted once before the turns below; the earlier
part of the day (PRs #6–#10, gates 19–21) is summarised from the compaction
summary and is marked as such. User prompts after the compaction are
verbatim.

- **Date:** 2026-09-17 (late evening, Pacific)
- **Session type:** a real translation job through the pdf-translate skill
  (California FL-150 → Japanese), the three skill defects it surfaced, an
  independent quality review, and the decision to turn the lesson into a
  workflow change.
- **Input files:** `C:/Dev/pdf-translate-provider-neutral/fl150_original.pdf`
  (byte-identical to the Judicial Council's `fl150.pdf`, Rev. 2024-09-01);
  the skill repo at `main` v54 with `feat/cjk-leak-tell` (v55) open as PR #10.
- **Final deliverables:** `Downloads/FL-150_ja_2026-09-17_v2.pdf`,
  `_v2_comparison.html`, `_v2_NOTES.md`, `_v2_translations.json`,
  `_v2_review.json`, `FL-150_page1_side-by-side_2026-09-17_v2.png`,
  `FL-150_original_rev2024-09-01.pdf`; in the repo: branch
  `fix/cjk-job-gates` (v56), `dev/goals/32-terminology-loop.md`,
  `dev/jobs/fl150-ja-2026-09-17/`, `docs/E3-surface-inventory-2026-09-17.md`,
  this log, the HANDOVER section.
- **Continues in:** the next session, starting from `dev/goals/HANDOVER.md`
  ("Start here — 17 September 2026, late"): operator pushes and merges
  #10/#11, then row 32 (design before build), then E3.

## Before the compaction (summarised, not verbatim)

The product's work order of 2026-09-16 was assessed and transcribed
(`docs/REQUESTS-from-product.md`); PRs #6 (kinsoku, v52), #7 (stale
report, v53), #8 (han-forms, v54) and #9 (requests) were merged on the
operator's "yes merge all"; task F was measured and built as gate 21
`leak-cjk` (v55) on `feat/cjk-leak-tell`, pushed as PR #10 (CI 5/5 green)
on "push"; a background inventory of the library surface for E3 was
launched. The operator's prompts in that stretch were, in order: the work
order paste; "also can you do the following as well in parallel, push
fix/stale-verify-report and open PR #7 against feat/kinsoku-gate…";
"push"; "What's next?"; the product's review of PRs #6–#9; "push"; "yes
merge all"; "push"; "psuh"; "push".

## Turn by turn (after the compaction)

**Prompt:** `Can you translate the FL-150 to Japanese`

Response: located the original (no copy in this repo; the earlier
Japanese outputs in Downloads were August bake-off runs), ran the skill's
workflow: recon (4 pages, 266 fields, Arial + Times Italic, hybrid XFA,
`/Perms /UR3`, RC4 with an empty user password, tagged), identity record,
parallel-text search (no Japanese FL-150 from the issuer; its Chinese
rendering `fl150c.pdf` read for conventions), strip + extract (372
segments, 247 cores, 118 tooltips, 48 warnings), authored the mapping by
a builder script (13 merges, 5 overrides, notice in the court-use box),
Noto Sans JP 400/700 instanced and subsetted, first build. Verify failed
on three gate gaps: wrapped Japanese merges invisible to the placement
gate, `locl` digit alternates drifting (`FL-150` → `FL-Ɍɐɋ`), hidden dead
buttons counted as chrome. Fixed each red-first on `fix/cjk-job-gates`
(v56, stacked on v55), suite 401 OK, committed 5e7864f. Three visual
passes; delivered v1 to Downloads and sent the files.

**Prompt:** `Didn't we already have a translation of this form somewhere that we deemed perfect?`

Response: yes — August bake-off outputs (Downloads `FL-150_ja.pdf`,
`_v2.pdf`; six runs in `pdf-translate-provider-neutral/runs/`), scored 9/9
on the then-rubric; the repo's own docs withdrew "gold" (three added
widgets, transliterated Schedule C, translated quoted label). Used v2 as a
second reader: terminology converged; six phrasings adopted.

**Prompt:** `What happened to my translation and comparison that i asked for what's happening?`

Response: explained the delay (the gate fixes), finished the build and
delivered v1 (verify exit 0, qa 0 errors).

**Prompt:** `What are the best practices on translating here? What should and should not be translated?`

Response: the write/find/say rule and the keep list; issuer conventions
win; established usage; no localisation on a filing; structure over
wording; disclosure; FL-150 examples.

**Prompt:** `What about the name of the court?`

Response: translated by rule and by the issuer's own practice;
カリフォルニア州上位裁判所 is the legal-literature term (上級 the press
form; 高等 would be wrong); bilingual tooltip offered.

**Prompt:** `Judge this translation as if you were an expert translator with expertise in translating pdf documents and translation best practices`

Response: dispatched an independent Opus reviser with the MQM protocol
from `references/review.md` (pairs + renders only): 31 findings — 1
critical (世帯主 for head of household), 6 major, 24 minor, verdict
"revise". Judged the review: accepted the critical and three majors,
rejected two majors on measurement (the "lost" privacy note is a hidden
dead button; "California" clears its checkbox by 1.5 pt), downgraded one
(上位/上級 both attested), accepted 18 minors, rejected 5 with reasons.

**Prompt:** `What about what should be translated and what shouldnt? The quality of translation is an issue of the underlying model is it not or is it due to our skill not being designed in a proper way? We can't just fix every pdf document like this all the time it has to be perfect each time`

Response: the keep/translate axis had zero findings and is enforced by
gates; the misses are terms of art, a process gap (the reviser step can
be skipped) more than a model gap; proposed review-before-delivery, a
terminology failure-modes reference, a termbase per class and language,
and a corpus; the three gate bugs were first-Japanese-job bugs, pinned.

**Prompt:** `Can i get a side-by-side comparison of the japanese and english just page 1`

Response: composed page 1 of the original and the translation into one
PNG at 150 dpi (`FL-150_page1_side-by-side_2026-09-17.png`) and sent it.

**Prompt:** `What were some things you flagged from this page regarding translation quality or correctness?`

Response: listed the page-1 findings with source and resolution.

**Prompt:** `Format your findings as if you were explaining it to someone who is familiar with translation work and you want them to chime in, use simple plain english`

Response: a plain-English note for a fellow translator, nine numbered
points plus the kept-in-English list.

**Prompt:** `format it in a way that works well with a discord dm and retains some of the formatting`

Response: the same note as two Discord-ready messages under 2000
characters each, in fenced blocks for copying.

**Prompt (verbatim, the operator's brother's review pasted back):**
`I asked my brother to review, this is what i got back:` followed by the
note with the reviewer's replies — "Agree", "Agree. Switch.", "Keep 上位",
"Change to 最終修了学年", "Yes, match.", "Agree.", "Agree.", "Ok, match.",
"Use JP form.", "Understood.", "Should be Japanese court version.", "Ok,
to leave in English." — and `the numbered list didn't transfer back
correctly`.

Response: applied every agreed item plus the pages-2–4 items the reviser
and I had accepted (24 in all; 7 rejected with reasons recorded in
`review.json`), including the new one — ATTORNEY FOR (name) in the
Japanese court idiom, （氏名）の代理人弁護士：. Rebuilt: verify exit 0, qa 0
errors, 16 scaled runs all ≥ 0.88, fourth visual pass clean. Delivered v2
(PDF, comparison, notes, mapping, review, page-1 side-by-side) and noted
that Discord drops "1." numbering on copy-back.

**Prompt:** `One thought that I had is that this will only improve the translation quality and correctness for this one page however we want all possible pages to be translated correctly and at high quality all the time, therefore we must generalize it so it applies to all and learn from this, essentially self-improvement and reinforcement training so it produces higher quality with other translation work, do you agree and what do you recommend?`

Response: agreed on the goal, not the mechanism: no model training;
a measured loop — reviser required before `finish`, a terminology
failure-modes reference (five transferable categories), a termbase per
class and language grown from every `review.json`, a canary scored on
terminology and on the reviewer's false-positive rate. Asked A/B/C.

**Prompt:** `Can you put this in the backlog and open threads so that it can be resurfaced as the top priority later? Do you agree, also create a handover, I will move on to a different session and potentially a new machine.`

Response: this log, row 32 (P0) in `dev/goals/PROGRAM.md` with the brief
`dev/goals/32-terminology-loop.md`, a "Start here — 17 September 2026,
late" section at the top of `dev/goals/HANDOVER.md` carrying the open
threads (the repo's convention: `PROGRAM.md` queues, `HANDOVER.md`
cold-starts, nothing else lists open rows), the job archived under
`dev/jobs/fl150-ja-2026-09-17/`, the E3 inventory brought into `docs/`,
a handoff zip in Downloads, and a docs commit on the fix branch. Agreed:
top priority after the two pending merges.

## Artifact inventory

| File | Status | Contents |
|---|---|---|
| `Downloads/FL-150_ja_2026-09-17_v2.pdf` | **Current deliverable** | fillable Japanese working copy, field fonts embedded, verify exit 0 |
| `Downloads/FL-150_ja_2026-09-17_v2_comparison.html` | **Current deliverable** | all four pages side by side at 120 dpi |
| `Downloads/FL-150_ja_2026-09-17_v2_NOTES.md` | **Current deliverable** | identity record, disclosures, gates, review, reviewer checklist |
| `Downloads/FL-150_ja_2026-09-17_v2_translations.json` | **Current deliverable** | the mapping |
| `Downloads/FL-150_ja_2026-09-17_v2_review.json` | **Current deliverable** | 31 findings with resolutions; human page-1 read recorded |
| `Downloads/FL-150_page1_side-by-side_2026-09-17_v2.png` | **Current deliverable** | page 1, English left, Japanese right, 150 dpi |
| `Downloads/FL-150_original_rev2024-09-01.pdf` | Input (copy) | the original used |
| `Downloads/FL-150_ja_2026-09-17.pdf` and siblings without `_v2` | Superseded | v1: carried 世帯主; kept for the record |
| `Downloads/FL-150_page1_side-by-side_2026-09-17.png` | Superseded | v1 page 1 |
| `Downloads/Handoff_Package_2026-09-17_FL150_Japanese.zip` | **Current deliverable** | this log, the v2 deliverables, the input, the handover section, a README |
| repo `dev/jobs/fl150-ja-2026-09-17/` | **Current** | mapping, widget text, review, notes, builder script, README with the fetch and rebuild recipe |
| repo `dev/goals/32-terminology-loop.md` | **Current** | the P0 brief |
| repo `dev/goals/PROGRAM.md`, `dev/goals/HANDOVER.md` | **Current** | row 32 queued; cold-start section |
| repo `docs/E3-surface-inventory-2026-09-17.md` | **Current** | the E3 inventory (was scratchpad-only) |
| repo branch `fix/cjk-job-gates` (5e7864f + docs commit) | **Current, unpushed** | the three gate fixes, v56, suite 401 OK |
| scratchpad `fl150-ja/` | Working files | build dir; reproducible from the job folder in three seconds |

## Key decisions

- **Follow the issuer's own conventions** (its Chinese FL-150): footer
  identity block, statute cite and URL stay in English; "for reference
  only, do not file" notice in the court-use box. Not FL-150 "J": no
  invented form number.
- **Hide the four dead XFA buttons** rather than recaption them: the
  scripts died with the XFA layer, Japanese captions would risk tofu in
  Acrobat's regenerated appearances, and no widget may be added. Disclosed;
  re-wiring offered.
- **Fix the skill's gates, not the job**, when verify failed a correct file:
  three defects, each red-first, on a branch stacked on the open PR so the
  versions stay in order (55 → 56). Reviewer's amended-test contract:
  single-substitution alternates now map to their base character.
- **Earlier "gold" outputs are second readers, not answers:** the repo's
  own record had withdrawn the label (added widgets, transliterations).
- **Review is a deliverable and must move before delivery** (row 32): no
  gate can see a plausible wrong term; the second reader can, and the
  reviewer itself needs measuring (two of its seven top findings were
  wrong on the facts).
- **上位裁判所 kept** over the reviser's 上級: both attested; the legal
  literature uses 上位; the human reader agreed.
- **No fine-tuning, no shipped glossary**: the loop is skill-level
  (reference, required step, termbase per job class, measured canary).

## Where this moves next

1. Operator: push `fix/cjk-job-gates`, open PR #11 (body in the zip's
   README and `docs/sessions/`), merge #10 then #11. Delete merged
   branches if wanted.
2. Row 32 (`dev/goals/32-terminology-loop.md`), design before build.
3. E3 step-2 readiness, design before build (`docs/REQUESTS-from-product.md`,
   `docs/E3-surface-inventory-2026-09-17.md`).
4. FL-150 job follow-ups if asked: re-wire the buttons; human read of
   pages 2–4; bilingual tooltip for the court name.

The next session should end by producing its own log in this format under
`docs/sessions/` and a dated section at the top of `dev/goals/HANDOVER.md`.

## Known gaps

- Pages 2–4 of the Japanese FL-150 have had a model review but no human
  read.
- The suite ran locally (401 OK); CI has not run on `fix/cjk-job-gates`
  because it is unpushed.
- `dev/jobs/…/build_translations.py` was written against the scratchpad
  layout; its README says how to run it from the job folder.
