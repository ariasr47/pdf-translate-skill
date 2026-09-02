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
