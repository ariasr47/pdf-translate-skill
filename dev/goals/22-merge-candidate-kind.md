# Objective: a merge candidate says what it is

> Hand this to a `/goal` session. Self-contained. Read
> `scripts/extract_segments.py` (`merge_candidate_warnings`, and the
> `[kind]` print in `main`), `scripts/pipeline.py` (`propose_merges`) and
> `dev/wild/ANALYSIS.md` §3. Fifteen-minute row; do it alone anyway. Not
> FL-150.

---

## 1. Compass (not done)

Every warning the extractor emits carries a `kind` — `inner-gap`,
`write-find-say`, `right-aligned`, `narrow-column`, `image-region`,
`no-text-layer`, `invisible-text` — except the one that matters most on a
manual or a regulation: `merge_candidate_warnings` writes `page`, `ids`,
`why` and `lines` and no `kind`. `propose_merges` therefore selects
candidates with `kind in (None, 'narrow-column')`, `extract_segments.main`
prints them with no tag, and anything else keyed on `kind` mislabels them.
The wild-corpus probe did exactly that on its first run: 2,484 paragraph
proposals across seventeen documents (528 on the GDPR, 976 on the Medicare
handbook) were counted as something else until a human read one.

## 2. Done when — closed bar

1. Every merge candidate carries `kind: "merge-candidate"`.
2. `propose_merges` accepts that kind **and still accepts `None`**, with a
   comment saying why: a `segments.json` written by an earlier version
   must not stop a rebuild.
3. `extract_segments.main` prints `[merge-candidate]` like every other
   kind.
4. A test locks both: the kind on a constructed wrapped paragraph, and
   `propose_merges` on a hand-written `segments.json` whose candidate has
   no `kind`.
5. `extract_segments.py` header and `translations-format.md` name the
   kind. Full unittest + corpus green. `metadata.version` bumped.

## 3. Not done when

- Changing the candidate heuristic (open sentence, same column, stacked)
- Touching `right-aligned` (row 21)
- Any new warning kind

## 4. Method

Constructed two-line paragraph; import shipped extract; assert the kind;
then the compatibility test on a stale file.

## 5. Invariants

Provider-neutral. Nothing merges by itself. Old work directories keep
working.

## 6. Proof

The kind on the fixture; the stale-file test; the corpus probe's warning
table showing `merge-candidate` by name; full unittest + corpus.

---

## 7. Closing note — 2 September 2026, closed

**Reproduced first.** On the paragraph fixture the extractor's proposals
had no `kind`; `extract_segments.main` printed them untagged; and a
candidate hand-written *with* `kind: "merge-candidate"` was silently
dropped by `propose_merges`, whose filter was `kind in (None,
'narrow-column')`. All three new tests failed before the change.

**Done bar, item by item.**

1. `merge_candidate_warnings` emits `kind: "merge-candidate"`.
2. `propose_merges` accepts `merge-candidate`, `narrow-column` **and
   `None`**, with a comment: a `segments.json` from an earlier extractor
   must keep proposing its paragraphs.
3. `extract_segments.main` prints `[merge-candidate]` through the same
   `[kind]` tag every other warning uses; no print code changed.
4. `MergeCandidateKindTests`: the kind on a constructed paragraph and no
   nameless warning left; the tag in `main`'s output; `propose_merges` on
   hand-written files — no kind proposes, the new kind proposes, and a
   `right-aligned` warning with the same shape proposes nothing.
5. Header comment and `translations-format.md` name the kind; `SKILL.md`
   step 3 calls the groups by it. 169 tests, no skips, green locally;
   corpus table unchanged. `metadata.version` 32 → 33.

**Wild corpus, re-run with the change** into a scratch directory: 17/17
`translate`, zero segment, core, warning or verdict differences against
the committed run, **zero warnings without a kind, 2,484 merge candidates
by name** — the same 2,484 the probe once miscounted. `dev/wild/probe.py`
keeps its fallback label for older files.

Not done, as the brief asked: the candidate heuristic, `right-aligned`
(row 21) and every other kind are untouched.
