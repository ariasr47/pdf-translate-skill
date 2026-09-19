# Queue: the five items the product bubbled, 2026-09-18

Not a design. A reading of five measurements the product took while integrating pdf-translate
54.0.0 (rev `9675c619`), with what this repo already answers, what it does not, and what each one
would cost. **Nothing here is implemented.** B1 needs a design pass before any build.

Licence boundary observed: no product code or product constants are reproduced here. The figures
below are the product's measurements, restated as behaviour. Obstacle-bounded placement (R6) is
still not asked for and nothing here builds toward it.

Read alongside `docs/REQUESTS-from-product.md` (the standing inbox) and
`docs/reviews/2026-09-18-consumer-surface.md` (what v58 just changed).

---

## Status at a glance

| | item | state after v57/v58 |
| --- | --- | --- |
| **B1** | no line breaking, so no kinsoku | **open, and the largest thing on the board.** Needs a design pass |
| **B2** | refusal report truncates the core to 40 chars | **answered for library consumers** in v58; the console is unchanged by design |
| **B3** | refusals printed, not returned | **answered** in v58 |
| **B4** | widget text not translated | **open.** Contained, and the extractor already does half of it |
| **B5** | terminology quality invisible to every gate | **built** in v57 as the review loop; it is a process, not a fix |

Two of the five landed while this was being written, which is luck of timing rather than
foresight — E3 was scoped from the product's own C1–C10 contract, and B2/B3 are that contract's C3
stated from the other side.

---

## B1 — the library never breaks a line

**The measurement, and it is the right one.** Every translated unit is one `TextWriter.append` at
its source baseline. 518 drawn lines on a 4-page fillable form, 32 on an 8-page invoice, and zero
calls to `insert_htmlbox` — the only reflow-capable draw — because that path needs a `merges`
declaration a consumer has no documented way to author.

**The observation worth keeping.** A kinsoku audit returning zero violations is not evidence the
rules are honoured; it is the result of no line-break decision ever being made. That is exactly
right, and it is worth more than a docstring. Gate 19 is real and does run — but it reviews lines
the **source** broke, re-drawn at the same baselines, so on a job with no reflow a clean result
means "nothing here was decided", not "every decision was right". That belongs in
`references/gates.md` beside gate 19 and in the gate's own message. **That much is cheap and should
happen regardless of what B1 becomes.**

**One factual correction, which does not touch the conclusion.** The note says the package "carries
no kinsoku logic at all outside `verify.py::kinsoku_report()`, which nothing calls." It is called:
`run_verify` invokes it at `verify.py:1852`, and it is gate 19, which shipped in v52 — before the
pinned 54.0.0. On the FL-150 job it reviewed **322 CJK lines**. What is true, and is the substantive
point, is that **nothing in `retypeset` consults kinsoku when placing**, because placement makes no
line-break decision to consult it about. The gate audits lines the *source* already broke.

**What is actually true in this repo, stated precisely:**

- `insert_htmlbox` *is* reachable and *is* reflow-capable. `retypeset` uses it for three things
  today: a declared `merges` entry, an authored `notices` entry, and a shaped or RTL run that goes
  through the Story engine. So reflow exists; what does not exist is **automatic** reflow of an
  ordinary single-line segment that will not fit.
- The `merges` declaration is not undocumented — `references/translations-format.md` specifies it
  and `pipeline.py propose-merges` generates candidates in bulk. But it is an **authoring** step
  aimed at a human or a model looking at a rendered page, not an API a service can drive, and the
  product's point stands: a consumer integrating the library has no programmatic route to it.
- The 0.75 figure is the product's floor. This repo's is **0.7** (`retypeset.SCALE_MIN`), below
  which a run is refused rather than shrunk, and `allow_scale` is the per-core opt-out. Two floors
  in two repos for the same phenomenon is itself worth reconciling.

**Why this is the coverage lever.** A long translation in a tight box shrinks; below the floor it
is refused and left in the source language. Wrapping would place text that today is not placed at
all. No other item on this list changes what reaches the reader.

**Why it needs a design pass and not a patch.** Wrapping is not one decision, it is four, and three
of them are user-facing:

1. **When may a segment wrap at all?** A form label in a table cell must not grow into the rule
   below it. A paragraph in a brochure should. The extractor already knows about `narrow-column`
   stacks and inner gaps; whether it knows enough to decide this is an open question, and guessing
   wrong writes text over a line the reader needs.
2. **Where does the extra line go?** Down, pushing nothing (there is nothing to push — the page is
   graphics), or centred on the original baseline, or up. Each is visibly different and none is
   obviously right.
3. **What happens to the box?** A union bbox of source ink is a measurement and runs tight; an
   authored box is an instruction. Row 26 already settled that distinction for merges, and B1 would
   need the same ruling for automatic wrapping — geometry must not choose a box that grows into a
   rule or a field.
4. **What does kinsoku do once there are line breaks?** Gate 19 stops being vacuous and starts
   having opinions. That is the *point*, and it is also the first time this repo will have to be
   right about Japanese line-breaking rather than merely not wrong.

A design canvas is the right next artefact: the failure modes are visual, and every one of the four
decisions above is something an operator should see drawn before it is built. **Recommended order:
canvas → ruling → measured probe on the corpus (how many refused runs would wrapping actually
recover?) → plan.** The probe matters: "the biggest coverage lever" is the product's estimate, and
this repo's habit is to measure before sizing.

**One thing to resist.** The temptation is to make wrapping the default and keep the floor as a
backstop. That inverts the current guarantee — today a run either ships at source size or is
refused, and a reader can trust that nothing was silently reflowed. Whatever B1 becomes, the
opt-in/opt-out shape is a ruling, not an implementation detail.

---

## B2 — the refusal report truncated the core to 40 characters

**Measured cost, and it is a real one:** poisoning a 97-character core reverted 247 of 247 cores
because the consumer's prefix match was ambiguous.

**What v58 does.** `run_retypeset` raises, and the exception carries `refusals` — every refused
item, by kind, **with the core in full**:

```python
except PdfTranslateError as exc:
    for item in exc.refusals['untranslated']:
        item['core']          # the whole key, never abbreviated
```

`glyph_misses` entries carry `page`, `role`, `char`, `codepoint`, `name` and the full `core`.

**What v58 deliberately does not do: change the printed line.** `(key or "")[:40]` stays. That line
is read by a person, the whole core would drown it, and changing it would break console parity —
the ratchet that made the whole 172-site conversion safe. The right resolution is that the console
abbreviates and the data does not; both are now true at once, and the code says so where the
truncation happens.

**If the product still wants the full key on the console**, that is a separate, cheap, and
deliberately-taken decision: one line, one parity-runner update, one version bump. It should be
asked for as a console change, not inherited as a side effect.

---

## B3 — refusals printed, not returned

**The strongest of the five, and the product's phrasing of it is the part to keep:** *a printed
format is an undeclared API that degrades every consumer's job silently when it changes.* That is
now quoted in `references/consumer-guide.md`.

**What v58 does.** Every stage raises a typed exception descending from `PdfTranslateError`, each
carrying structured attributes (`GlyphError.page`, `.char`, `.face`), `refusals`, and a
`to_dict()` with `schema` and `version`. The named example —

```
p0 [regular] U+4E06 CJK UNIFIED IDEOGRAPH-4E06 (丆) in: STATE BAR NUMBER:
```

— is now reachable as data: `exc.refusals['glyph_misses'][0]` has every field in that line plus the
untruncated core, and `exc.page` / `exc.char` / `exc.face` are on the exception itself.

**The failure mode this had, exactly as described, happened here too.** Converting the package's
172 print sites, two `print(a, b)` calls became `log.info(a, b)` — which treats the second argument
as a format parameter, swallows the record, and makes the line **vanish**. Neither was caught by
492 tests or by either parity runner, because both only fire on a failing job. They are now pinned
structurally. A printed format degrading silently is not a hypothetical; it is what this repo did to
itself in one afternoon.

---

## B4 — widget text is not translated

**Measured: 118 fields carrying tooltips, dropdown labels and defaults on page one of one form.**

**What already exists, which is more than half of it.** `extract_segments` writes a
`widget_text.json` **scaffold** listing every `/TU` tooltip, every choice `/Opt` display string and
every text-field `/V` / `/DV` default. `strip_text` applies an authored one, refuses a spec that
would translate a choice `/V` (an export value the form logic depends on), preserves export values
by rewriting `/Opt` entries as `[export, display]`, and exits 2 on a mapping that is unauthored or
wrong. The FL-150 job authored all 118 tooltips in Japanese this way.

**So B4 is not "not implemented" — it is "not integrated".** The gap is that the widget-text pass
is a *separate, manual, second run of `init`*: author the scaffold, then re-run with
`--widget-text`. Nothing in the consumer surface exposes it, `run_strip` does not take it, and the
guide does not mention it. A consumer following the six calls will never translate a tooltip.

**Cost: small, and mostly API design rather than new behaviour.** `run_strip(widget_text=...)` is
already the underlying parameter. What it needs is: the scaffold surfaced on `ExtractResult` (it is
already written to disk and already on the result as `widget_text_path`), one section in the
consumer guide, and a decision about whether an *unauthored* scaffold should be a refusal, a
warning, or silence — which is the only real question, because today a job that never authors one
ships a form whose fields read in the source language and nothing says so.

**Recommendation: fold B4 into the next epic rather than giving it its own.** It is one parameter,
one guide section and one ruling.

---

## B5 — terminology quality

**This is row 32, and it shipped in v57.** The product's evidence and this repo's are the same
evidence: three models and one Claude independently produced 世帯主 for "head of household"; it
passed `verify` at exit 0 and `qa_check` at 0 errors; a second reader found it after delivery.

**What v57 built**, deliberately as a loop and not a model:

- `pipeline.py review --work DIR` writes `review_pairs.md` and an MQM `review_prompt.md`.
- `--ingest review.json` reads the reviser's verdict back and reports every finding.
- `finish` **refuses** while a review is absent or any finding is open; `--no-review` is the only
  way past and marks the delivery, in the console *and* in `review_state.json`.
- Accepted terminology findings with a named `term`/`term_target` grow a per-class `glossary.csv`,
  which `qa_check --glossary` has gated on since long before this loop existed. Proven end to end:
  the next job reverting 世帯主 is caught as an ERROR.
- `references/terminology-failure-modes.md` names the five categories, with the FL-150 instance and
  the transferable rule for each.
- The canary now scores the **reviser**: 15.29 accepted findings per 1,000 source words, and a
  **19% false-positive rate** (6 of 31, two of them in the reviser's own top seven).

**The product's last sentence is the important one: "it may not be a code fix at all."** Agreed, and
that is what the loop encodes — the fix is a required deliverable and a refusal, not an algorithm.
The one thing a script contributes is *memory*: a term got wrong once should not be available to get
wrong again, which is what the termbase is.

**What is still open on B5.** The FL-150's own `review.json` predates the `term`/`term_target`
fields, so it fills no termbase — 0 added, 11 reported as skipped, never guessed. Rodrigo ruled on
2026-09-18 to keep that strict. The loop starts paying on the next reviewed job, not retroactively.

---

## If a priority is wanted

The product's own ordering is right, with two items already closed:

1. **B1** — design canvas first, then a corpus probe to size it, then a plan. Nothing else changes
   what reaches the reader.
2. **B4** — fold into whatever epic follows; one parameter and one ruling.
3. **B2 console** — only if the product asks for the printed line to change, as its own decision.
4. **B5** — nothing to build; watch the canary's false-positive rate and see whether the termbase
   makes the next job cheaper.

And one thing not on the product's list, cheap, and worth doing with B1 or before it: **say in
`references/gates.md` and in gate 19's SKIP message that a kinsoku pass with nothing to review is
not a kinsoku pass.** An audit that returns zero because no decision was made reads exactly like an
audit that returns zero because every decision was right, and only one of those is true today.
