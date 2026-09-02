# Recommendations after the bakeoff (skill text, then gates)

Not a `/goal`. Do not implement a gate in the same sitting as a bakeoff.
Do not put a model winner in `SKILL.md`. Do not ship a terminology glossary.

Evidence: Claude handover (skill v1/v2, Fable 5, Opus/Sonnet/Haiku), Grok 4.6,
ChatGPT Sol/Terra/Luna at High and Extra High, independent `verify.py`, and
the original FL-150 core list (251 unique strings). Quality explainer:
`quality-bakeoff.html`.

PROGRAM 01–07 are closed. This document is the candidate queue **after** that,
split by *what kind of change* it is. Skill-design rules still apply: one home
per fact, no one-off bandaids, constructed tests not FL-150.

---

## What the evidence actually says

1. **The scripts are not the bottleneck.** Three labs drove strip → extract →
   map → retypeset → verify. Opus high v2, Sonnet v2, and all six ChatGPT runs
   exit 0 on today’s gates (266 fields, Japanese fill, captions except Haiku).
   Haiku v2 fails leftover English chrome. Grok 4.6 fails the *current* caption
   gate because it hid T23. Fable 5 “gold” added three widgets (`266→269`).

2. **Instruction moved lookup strings more than model ID.** Skill v1: most
   Claude runs wrote スケジュールC and translated `"Question 1—Other Jobs"`.
   Skill v2: every Claude run kept `Schedule C`; Opus/Sonnet kept the quoted
   label. Same models. ChatGPT on the current skill kept both from High.

3. **Extra reasoning is for visual rounds, not vocabulary.** Opus max ≈ Opus
   high on the 9-check rubric (+6 minutes). ChatGPT Extra High bought Sol’s
   上級 fix, Terra’s no-`allow_scale`, Luna’s 所得→収入 — layout craft and a
   few register nits, not a new legal lexicon.

4. **Gates cannot see meaning.** Haiku v2 titled page 4 養子支援情報
   (adoption support) and still passed structure. Luna High titled the form
   所得 (taxable income). Sol High and Sonnet v2 wrote 上位裁判所. A grep for
   養育費 would not catch Haiku: it also wrote 養育費 four inches below the
   wrong heading.

5. **Fluency review cannot see write/find/say.** Fable 5 was bilingual-approved
   and still transliterated Schedule C and translated the attachment label.

6. **A public glossary would not have saved Haiku.** The session prompt already
   named 申立人 / 相手方 / 養育費. Haiku coined 養子支援 anyway. PROGRAM is
   right: wrong terms are a reason not to use that model as author, not a
   reason to maintain per-domain dictionaries the skill cannot keep current.

---

## How professionals actually work (and what we should steal)

These are not JC-only. They generalize to any issuing-body form.

**Issuing-body parallel text (ISO 17100 “reference material”; JC contract
language).** California publishes FL-150 in Spanish, Chinese, Korean, Tagalog,
and Vietnamese (`FL-150 S/C/K/T/V`). JC’s translation contract says: Spanish
must follow the Council glossary; other languages must follow *existing
translations of Judicial Council forms in that language*; format must match
English; no machine translation for official work. There is **no official
Japanese FL-150**. The transferable rule is: *if the issuer published this
document in the target language, that file is the terminology source.* Search
before authoring. Do not bake FL-150 Spanish into the skill.

**Write/find/say / foreignization of identifiers (legal translation: keep a
trace of source-system names).** Form numbers, IRS/USCIS form names, quoted
copy-me labels, program acronyms, URLs, statute numbers stay in the source
language (or bilingual: `家族法（Family Code）`). Transliteration
(ファミリーコード, スケジュールC) is the failure mode. Domestication
(申立人, 上級裁判所, 養育費) is for *roles and institutions that have a
target-language equivalent*, not for documents the reader must fetch.

**Two products, do not confuse them.** This skill localizes a fillable form
into a monolingual target-language working copy. It is not a USCIS/EOIR
certified synoptic translation and not an official JC bilingual form (FL-110
style). Certified work wants four-eyes (ISO 17100 reviser; ISO 20771 legal
competence). The skill can *name* that; the scripts cannot be the second
linguist.

**Functional equivalence, then a check against the page.** 収入 vs 所得,
上級 vs 上位, 扶養料 vs 扶養費, 審理 vs 公判, 面会交流 vs 訪問. No script
will rank these. A second pair of eyes will. The visual pass already exists;
extend its checklist, do not pretend it is a gate.

---

## A. Skill text (do first; no new gate)

One home: `SKILL.md` extract/translate section + a short addition to
`failure-modes.md`. No FL-150-only examples if a generic one exists; keep at
most one cited illustration per class.

| Change | Why | Not |
|---|---|---|
| **Parallel text, one paragraph.** After extract: if the issuing body (or a court/agency of jurisdiction) publishes this form in the target language, open that file and match its terms of art. Search the issuer site by form number. If none exists, proceed with write/find/say + register. | JC contract and ISO 17100 both start from existing translations. Haiku/Luna would still need a human; Opus/Sol would stop inventing 所得/上位 when an official file exists. | A glossary in the repo. Linking `fl150s.pdf`. |
| **Write/find/say: fourth kind.** Paper size the filer must use (`8 1/2-by-11-inch` → do not convert to A4); currency symbols the court expects (`$` stays `$` on a US form). Revision *number/code* stays; the calendar date may localize (`FL-150［2024年9月1日改訂］`). | Luna/Haiku/Sonnet identity-mapped the whole rev stamp; others over-localized paper size in running text. | A list of form numbers. |
| **Quoted payload vs instruction.** Translate “Write … at the top”; do not translate the quoted payload. Extractor already warns; the skill should say the warning is a halt-and-confirm, not a suggestion. | Grok and Fable translated `"Question 1—Other Jobs"`. | Hard-coding those two quotes. |
| **Transliteration is a defect for lookup names.** ファミリーコード / スケジュールC class: neither meaning nor search. Prefer source token or `target (Source)`. | Haiku v1; Fable; Opus v1. v2 prose already fixed most Claude runs. | Banning all katakana. |
| **Narrow columns are one note.** Consecutive cores that share a skinny bbox are one stacked instruction or one override with `max_width`. Do not translate English line breaks independently. | Every ChatGPT run failed the pay-stub box; Sol Extra High was merely the least bad. | Auto-merge by x (swallows list siblings). |
| **Overrides keep list letters and `$`.** | Terra/Luna Extra High dropped `d.` on TANF; Claude v2 did not. | |
| **`--captions` must fit the widget rect.** Prefer three-character chrome (`印刷` / `保存` / `消去`) over a sentence in a 17-pt-tall button. Rewriting `/CA` and leaving a clipped string still PASSes gate 02 (Terra High). | Layout, not structure. | A new “clip” gate until we can measure it. |
| **`allow_scale` is last resort.** Reword, then look, then opt in. Terra High used eight entries down to 0.59×. Extra High reworded. | Gate 03 already exists; the skill should not invite the escape hatch. | Removing `allow_scale`. |
| **Empty targets are not translations.** Terra High `are living with me` → `""` still passed `--translations`. | Fix in verify (B), mention in format doc. | |
| **Author canary.** A model that will not inspect PNGs, or that fails write/find/say after the extractor warned, should not author `translations.json`. Haiku-class: evals only. Extra High/max: visual iteration, not “better Japanese.” | PROGRAM already says this; SKILL.md visual-pass paragraph can point at it once. | Naming Sol or Opus as required. |

Do **not** add: 上級裁判所, 養育費, 申立人 as skill text. Those are Japanese
family-law facts. The general fact is “use the issuer’s term of art in the
target legal system; do not calque.”

---

## B. Script / gate candidates (separate `/goal`s, constructed fixtures)

Queue these **one session each**. Constructed LTR PDFs, not FL-150. Existing
unittest + corpus stay green.

| # | Title | Closed done bar | Evidence it is a class |
|---|---|---|---|
| **08** | Quoted / named identifiers round-trip | A constructed form contains `Write "Attachment A" at the top` and `attach Schedule Q`. If the output’s text layer lacks the exact quoted span / `Schedule Q`, verify fails (unless the mapping listed them as translated *and* NOTES records why). Extractor already emits write/find/say; this *checks* the author honored it. | Fable, Grok, Claude v1 vs v2 |
| **09** | Empty and whitespace-only targets fail | `--translations`: non-passthrough target `len≥2` after strip; `""` and `" "` fail named. | Terra High |
| **10** | Caption string vs widget width | After `--captions`, measure `/MK /CA` text width at the widget’s font size against rect width (with a small pad). FAIL listing the field if it overflows. Constructed: a 60-pt-wide button whose caption is 40 letters. | Terra High clip; Haiku English leftover already caught by 02 |
| **11** | Override must not drop sibling markers | Constructed inner-gap row `d. Label      [widget]     .... $`. If override parts omit `d.` or `$` that existed on the source span, fail or warn. | ChatGPT Terra/Luna Extra High vs Claude v2 |
| **12** | Consecutive cores in a narrow column | Extractor warning: N cores, same page, width < W, adjacent y. Skill already says look; a warning is enough unless we later want a merge suggestion. **Prefer warning over auto-merge.** | Pay-stub box, all ChatGPT runs |

Non-goals for this queue (leave them non-goals):

- Semantic term checker (養子 vs 養育費). False confidence.
- OCR implementation.
- Official JC glossary dump.
- Combining any of 08–12 with a bakeoff in one sitting.

---

## C. Process (harness / humans, not SKILL.md sprawl)

ISO 17100 TEP (translate → revise → proof) and JC “no MT for official filings”
are **product** rules for a court contractor. For this skill:

1. **Mapping author inspects PNGs.** Already required. Session prompts should
   say “pdf-translate only” so Codex does not wander into writing-plans (Sol
   High, Luna Extra High).
2. **Second reader when the user is shipping to a court.** One paragraph in
   Deliver: if a second linguist is available, they check write/find/say hits
   and terms of art against any issuer translation; the scripts will not.
3. **Eval canary, not author.** Keep Haiku (and anyone who leaves English
   chrome or coins 養子-class errors) in the bakeoff grid. Do not recommend
   them in SKILL.md.
4. **Parallel-text lookup is recon, 30 seconds.** Form number + issuer domain.
   For FL-150 JA there is no official file; for FL-150 ES there is
   `fl150s.pdf`. The skill speaks in that generality.

---

## Suggested order

1. **Skill-text pass (A)** — one session, no new gate, no bakeoff. Tightens
   write/find/say, parallel text, captions-fit, narrow columns, empty
   targets-as-docs, `allow_scale` last resort. Update `failure-modes.md` only
   if a silent class is new (quoted payload; caption clip).
2. **`/goal` 08** — quoted/named identifier round-trip on a constructed PDF.
3. **`/goal` 09** — empty targets.
4. **`/goal` 10** — caption vs rect (needs a width measurement you trust).
5. **`/goal` 11** — override markers.
6. Extractor warning for narrow-column stacks (12) can ride with 08 or 11 if
   it is warn-only; do not auto-merge.

After 08, re-run a **canary** (not a gate) on one strong and one weak model
with the same fixture. Do not mix that canary into the gate session.

---

## Explicitly rejected

| Idea | Why not |
|---|---|
| In-repo JA glossary (申立人, 養育費, 上級) | Cannot maintain; would not have stopped Haiku; PROGRAM forbids it; JC glossaries are for *official* JC work in specific languages. |
| Grep-gate for 養子 / 所得 | One-off, language-pair-specific, Haiku also used 養育費 on the same page. |
| Require Extra High / Opus max | Measured: max did not beat high; Extra High helps eyes, not terms. |
| Name a winner model in SKILL.md | Provider-neutral. Sol Extra High won *this* layout canary; Opus high v2 won *Claude’s* Japanese probes. Different skill versions, different PNG depth. |
| Treat Fable 5 as structure gold | Extra widgets; write/find/say misses. Fluency gold only. |
| Convert US Letter / `$` / FL-150 | Breaks the court’s matching rules. |

---

## Still unknown (do not plan as if known)

- Opus high v2 page PNGs (pay-stub, page-2 gaps, caption clip).
- Grok 4.6 on the *current* skill (`--captions` vs hide).
- Native-speaker ranking of 困窮 vs 困難, 収入・支出申告書 vs 収入および支出に関する申告書.
- Token/$ cost. Wall-clock is not price.
- Whether 投資所得 on Haiku’s income table is acceptable compounding or a
  register leak. Flag for a linguist, not a gate.
