# Independent verification — gate 18, conjunct shaping (2026-09-15)

**Verdict: REPRODUCED.** Every command in this pass ran to the exit code
and output the author's doc claims — unit tests (19/19, 0 skipped), my own
independent probe-table script (10/10 rows match), the RED and GREEN CLI
runs (exit 1 / exit 1 / exit 0 with matching FAIL/PASS lines), the visual
difference in the rendered PDFs, the canary silence check, and the full
260+11 test suite. One real gap was found and confirmed by a constructed
test (an unused, merely-embedded broken font can drag a page to FAIL even
though the visible text was drawn by a correct font) — this is a
conservative failure mode (it cannot produce a false PASS, only an
over-cautious FAIL), and the author's doc does not claim to have checked
it, so it does not contradict anything written there.

**Verifier:** Claude Sonnet 5 (`claude-sonnet-5`), a different model from
the author (Fable 5.1, per the author's doc). I did not write any of the
code under test.

Scratch directory: `C:\Users\rodri\AppData\Local\Temp\claude\C--Dev-pdf-translate-skill\f71acf3b-389c-49ff-881b-f6d3f7417505\scratchpad\verify-pass\`.
Interpreter: `C:\Dev\pdf-translate-skill\pdf-translate.venv\Scripts\python.exe`
(confirmed: Python 3.14.0, PyMuPDF 1.28.2). All commands run with
`PYTHONUTF8=1`. Branch confirmed at the start of this pass:

```
$ git log --oneline -6
8c81f8e docs(pdf-translate): gate 18 in gates.md, SKILL.md, fonts.md; version 49
d383743 feat(pdf-translate): gate 18, conjunct shaping attested on the embedded face
525d0c1 feat(pdf-translate): conjunct-shaping probe with a measured table
0266d30 docs: review PR #1 (canary delivery) and PR #2 (core-library packaging)
6d47f63 test(pdf-translate): fetch Thai, Khmer, Tamil, Bengali and Myanmar test faces
4440594 docs: adopt AGENTS.md, DECISIONS.md and the product request inbox

$ git status --short
?? docs/reviews/2026-09-15-conjunct-shaping-gate.md
```

Clean apart from the author's own untracked doc, as expected.

---

## Step 1 — unit tests for the gate

```
$ cd pdf-translate && python -m unittest tests.test_shaping_probe -v
```

Full 19-test list ran, every one `ok`. Tail:

```
----------------------------------------------------------------------
Ran 19 tests in 2.654s

OK
EXIT_CODE=0
```

19 tests, OK, exit 0, 0 skipped. Matches.

## Step 2 — reproducing the probe table myself

I wrote my own script (`my_probe.py`, not copied from `shaping_probe.py`)
that draws each string twice per the task's recipe — `insert_text` with
`fontname='probe'`/`fontfile=path` for the naive arm, `insert_htmlbox`
with a `@font-face` rule pointing at a POSIX path for the shaped arm —
and counts `sum(len(span['chars']) for span in page.get_texttrace())` on
each. Output (`cps`/`naive`/`shaped`, font names collapsed since both arms
always agreed):

```
font                             cps   naive  shaped
NotoSansDevanagari (क्षत्रिय)      8       8       4
NotoSansDevanagari (कमल)          3       3       3
NotoSansBengali    (ক্ষ)           3       3       1
NotoSansTamil      (க்ஷ)           3       3       1
NotoSansKhmer      (ខ្មែរ)         5       5       4
NotoSansMyanmar    (သင်္ဘော)       7       7       5
NotoSansMyanmar    (မြန်မာ)        6       6       6
NotoSansThai       (ป้า)           3       3       3
NotoSansThai       (กำไร)          4       4       5
NotoNaskhArabic    (مكتبة)         5       5       8
EXIT_CODE=0
```

Every one of the ten rows matches the author's expected numbers exactly
(Devanagari 8/4 and 3/3; Bengali 3/1; Tamil 3/1; Khmer 5/4; Myanmar 7/5 and
6/6; Thai 3/3 and 4/5; Arabic 5/8). No mismatches. In both arms, for every
row, the font name in the texttrace span matched the input face's own
family name (`{'NotoSansDevanagari-Regular'}` etc.) — no Helvetica
fallback contaminated any measurement.

## Step 3 — the red run through the documented CLI scripts

All commands run from the scratch directory unless noted, against
`scripts/pipeline.py`, `scripts/prepare_font.py` (the paths SKILL.md
documents).

**3a/3b — fixtures.** `original.pdf`: one page, one line, Latin,
`insert_text((72,80), "May you receive peace and strength", fontsize=14)`.
`no-gsub.ttf`: `tests/fonts/NotoSansDevanagari-Regular.ttf` with fontTools
`del f['GSUB']` (script printed `deleted GSUB`, confirming the table was
present before deletion).

**3c — init:**

```
$ python scripts/pipeline.py init original.pdf --work job
strip: xfa_removed=False dead_buttons=0
1 segments, 1 unique strings to translate, 0 warnings -> segments.json / to_translate.json
elapsed 0.07s -> job
EXIT_CODE=0
```

`job/translations.json` written by hand with the target string; verified
by round-tripping it back through `json.load` — it decodes to exactly
`आपको शांति और शक्ति प्राप्त हो`.

**3d — RED, prepare_font with the GSUB-stripped face:**

```
$ python scripts/prepare_font.py no-gsub.ttf job/translations.json job/font-sub.ttf --sample "आपको शांति"
FAIL conjunct shaping Devanagari: "क्षत्रिय" 8 -> 8 glyphs (NotoSansDevanagari-Regular); no conjunct formed: the Story engine drew 8 glyphs, glyph-by-glyph drew 8; the face has no usable GSUB for Devanagari
FAIL: job/font-sub.ttf does not shape the conjuncts this job draws; a page built with it shows consonant+halant where a conjunct belongs. Use a glyf TTF that carries the script's GSUB tables (references/fonts.md).
EXIT_CODE=1
```

Exact match to the author's claim (exit 1, `FAIL conjunct shaping
Devanagari` with 8 -> 8). Confirmed the subset file existed on disk
despite the failure (`ls -la job/font-sub.ttf` → 12780 bytes).

**3e — RED, second net, pipeline rebuild on the failed subset:**

```
$ python scripts/pipeline.py rebuild --work job original.pdf out-nogsub.pdf --translations job/translations.json --fill-text "आपको" --min-ink 0.1
metadata: /Lang -> hi
canonical text layer: rewrote /ToUnicode on 1 font object(s)
saved ...\out-nogsub.pdf
leak scan: source script Latin; output script Devanagari
fields: 0 original / 0 translated
PASS field parity
SKIP fill round-trip (no fields)
PASS page 1 ink ratio: 0.92
PASS text layer is visible
PASS canonical text layer
FAIL conjunct shaping Devanagari: "क्षत्रिय" 8 -> 8 glyphs (NotoSansDevanagari-Regular); no conjunct formed: the Story engine drew 8 glyphs, glyph-by-glyph drew 8; the face has no usable GSUB for Devanagari [page 1] — every conjunct drawn with this face is broken; do not ship
PASS no untranslated running text
REVIEW isolated source-script tokens: none
PASS no empty translation targets
PASS authored translations present
PASS shaped-script targets carry /ActualText
PASS button captions
PASS caption width
PASS document metadata
PASS scaled runs: none, everything ships at source size
PASS write/find/say identifiers
EXIT_CODE=1
```

Exact match: exit 1, the FAIL conjunct-shaping line, and — as the author
specifically called out — `PASS shaped-script targets carry /ActualText`
printed on the same, broken output (gate 17 and gate 18 check different
things; both fire independently).

**3f — GREEN, real Noto face:**

```
$ python scripts/prepare_font.py tests/fonts/NotoSansDevanagari-Regular.ttf job/translations.json job/font-sub.ttf --sample "आपको शांति"
PASS conjunct shaping Devanagari: "क्षत्रिय" 8 -> 4 glyphs (NotoSansDevanagari-Regular); ksha and tra conjuncts
OK: job/font-sub.ttf (40 KB, 134 chars, render check 432 px)
EXIT_CODE=0

$ python scripts/pipeline.py rebuild --work job original.pdf out-good.pdf --translations job/translations.json --fill-text "आपको" --min-ink 0.1
...
PASS conjunct shaping Devanagari: "क्षत्रिय" 8 -> 4 glyphs (NotoSansDevanagari-Regular); ksha and tra conjuncts [page 1]
...
PASS shaped-script targets carry /ActualText
...
EXIT_CODE=0
```

Exact match on every number the author cites, including the incidental
"40 KB, 134 chars, render check 432 px" line.

**3g — visual pass.** Rendered both outputs at 600 dpi, clipped to the
text line, and looked at the PNGs directly with the Read tool (not
inferred from text extraction).

- `out-nogsub.pdf`: in शक्ति, क carries a visible hooked stroke hanging
  below it (the halant/virama mark drawn as its own glyph — GSUB never
  removed it), त stands as a full separate letter next to it, and the
  small ि loop sits to the right, after त, rather than merged into the
  cluster. In प्राप्त, the first प also carries the same hanging hook and
  is followed by a full-size र (not reduced to a subscript hook), and the
  second प+त pair again shows the hook-under-प with a distinct full त
  next to it — every consonant+halant+consonant sequence stays visually
  three separate marks.
- `out-good.pdf`: शक्ति renders as one compact cluster — no dangling hook
  under क, and a small stroke that reads as the ि vowel sign sits
  attached to the upper-left of the cluster rather than trailing after
  it. In प्राप्त, the first प is followed by a small curved tail
  subjoined under/beside it (consistent with the प्र "ra-vattu" ligature,
  not a full-size र), and the second प/त pair is drawn as one tighter
  merged shape rather than two letters joined by a visible hook.

This agrees with the author's description (explicit halant + separated
consonant + trailing i-matra in the broken render; क्त/प्त conjuncts +
leading i-matra + ra-vattu in the real one). I can tell the two renders
apart clearly and confidently; I did not attempt a stroke-by-stroke
Unicode-glyph-ID identification (I don't have ground truth on this font's
exact glyph IDs), so I'm reporting what I visually see, which is a
materially different glyph shape in both marked words, consistent with
conjunct formation working in one output and not the other.

## Step 4 — the gate stays silent on a Latin/Spanish job

```
$ python C:\Dev\pdf-translate-skill\dev\canary\score.py C:\Dev\pdf-translate-skill\runs\fresh-canary-2026-09-05\fixtures\permission_form.pdf C:\Dev\pdf-translate-skill\runs\fresh-canary-2026-09-05\job --report score.json
===== job =====
  ...
  verify: exit 0, 0 gate(s) failing
  identifiers: 4/4 survived
  qa_check: 0 error(s), 1 warning(s)
  ...
wrote score.json
EXIT_CODE=0
```

Exit 0, as expected. Checked `score.json` directly:
`grep -in "conjunct" score.json` → **no match** (grep exit 1). The
`verify_log` field (full text inspected) contains gates for field parity,
ink ratio, text layer, canonical text layer, untranslated text, empty
targets, authored translations, button captions, caption width, document
metadata, scaled runs, write/find/say identifiers — no conjunct-shaping
line anywhere, because this job's script is Latin only. Confirmed.

## Step 5 — full suite as CI runs it

```
$ python -m unittest tests.test_pipeline tests.test_corpus_verdicts tests.test_import_surface tests.test_shaping_probe -v
...
----------------------------------------------------------------------
Ran 260 tests in 58.436s

OK
EXIT_CODE=0
```

`grep` for `FAILED`/`ERROR`/`skipped` across the captured output: no
matches other than test names that contain the word "skipped" as part of
their own test name (e.g. `test_a_null_core_is_skipped_not_iterated`,
`test_face_without_the_probe_glyphs_is_skipped_not_judged`) — those are
`ok`, not actually-skipped tests. 260 ran, 0 actually skipped, exit 0.

```
$ python -m unittest discover -s ../dev/canary -p test_score.py -v
...
----------------------------------------------------------------------
Ran 11 tests in 0.867s

OK
EXIT_CODE=0
```

260 + 11 = matches the author's "260 + 11 canary, OK, 0 skipped" exactly.

## Step 6 — skeptic's look

Read `pdf_translate/shaping_probe.py` in full and `conjunct_shaping_report`
in `pdf_translate/verify.py`. Concrete points, one of which I built a
reproduction for rather than leaving as a hunch:

1. **Confirmed by test: page-level font attribution is not per-glyph-run,
   and this can produce a false FAIL (never a false PASS).**
   `conjunct_shaping_report` decides a script is "on this page" from
   extracted text, then probes *every* font xref returned by
   `page.get_fonts(full=True)` that covers the probe cluster — it does not
   check which font actually painted the Devanagari glyphs that are
   visibly on the page. I built a page with `page.insert_text(...)` using
   only the **good** Devanagari face to draw क्षत्रिय, then called
   `page.insert_font(fontname="broken", fontfile=no-gsub.ttf)` to embed a
   **second, broken** face into the page's resources without drawing a
   single glyph with it. Calling `conjunct_shaping_report` directly on the
   resulting PDF:
   ```
   fonts on page 0: [(5, ..., 'good', ...), (12, ..., 'broken', ...)]
   status: FAIL
   PASS conjunct shaping Devanagari: ... 8 -> 4 glyphs ... [page 1]
   FAIL conjunct shaping Devanagari: ... 8 -> 8 glyphs ... [page 1] — every conjunct drawn with this face is broken; do not ship
   ```
   The document's overall status is FAIL even though the only visible
   Devanagari run was drawn by the correct face. I then tested the
   reverse — draw the visible run with the **broken** face and embed an
   unused **good** face alongside it — and the aggregate status was still
   FAIL (`if 'FAIL' in statuses: status = 'FAIL'` in the code dominates
   regardless of order), so an unused good font cannot mask a real broken
   render. Net effect: this gap can only make the gate too strict (flag a
   page over an embedded-but-unused broken font), never too lax. Whether
   this scenario is realistic in the actual pipeline (e.g. a job that
   declares a "bold" font in `translations.json` that gets embedded for
   `/DR`/form-field use but never actually drawn as body glyphs) I did not
   test — I only confirmed the mechanism in `verify.py` directly.

2. **Coverage gap, read from the tables, not run:** `scripts_in()` only
   flags scripts present in `SCRIPT_RANGES`. Conjunct-forming scripts
   entirely absent from that table (e.g. Javanese, Balinese, Batak,
   Limbu, Syriac, N'Ko, Mongolian) get *no* signal at all — not PASS, not
   REVIEW, not FAIL — because the module never recognizes them as present
   on the page. This differs from `UNMEASURED_CONJUNCT_SCRIPTS`
   (Gurmukhi, Gujarati, Oriya, Telugu, Kannada, Malayalam, Sinhala,
   Tibetan), which correctly surfaces as REVIEW. I did not build a
   document in one of these missing scripts to confirm; this is read
   directly off `SCRIPT_RANGES` vs `PROBE_FOR`/`BLIND_SCRIPTS`/
   `UNMEASURED_CONJUNCT_SCRIPTS` in `shaping_probe.py`.

3. **Font identity by name string, not by content.**
   `_normalize_font_name` strips the subset-tag prefix and
   whitespace/hyphens/underscores and lowercases, then compares against
   `font_psname(fontfile)` read from the same extracted font program. This
   correctly defends against the documented Helvetica-fallback trap, but
   it is a name match, not a content/hash match — a font program that
   reports the same PostScript name as the real Noto face but has
   different (possibly broken) tables would be trusted. I did not
   construct this scenario; flagging it as a read, not a finding.

4. **Duplicate reporting, read not run:** the same physical font data
   embedded under two different xrefs (e.g. the same face embedded twice,
   or declared separately for `regular`/`bold`) is keyed by
   `(script, xref)` in `judged`, so it is probed and reported once per
   xref — cosmetic duplication in the report, not a correctness bug.

5. **CFF/OTF, not run:** I did not test an embedded CFF-flavored font.
   Reading the code, a font-load failure inside `probe_font_bytes` is
   caught generically and downgraded to REVIEW
   ("could not load the embedded font ...: {exc}"), not a silent PASS —
   so the likely failure mode looks safe, but I have not confirmed this
   with an actual CFF/OTF Devanagari font.

## Step 7 — point-by-point agreement with the author's doc

Read `docs/reviews/2026-09-15-conjunct-shaping-gate.md` only after
finishing steps 1–6.

- **Probe table (Devanagari 8→4, हिन्दी 6→5, कमल 3→3, Bengali 3→1,
  Tamil 3→1, Khmer 5→4, Myanmar 7→5 and 6→6, Thai 3→3 and 4→5, Arabic
  5→8):** the rows the task asked me to check all agree with my
  independent script (step 2). I did not re-measure हिन्दी or Khmer's
  second row (কা, the vowel-sign-ligature example) — these extra rows in
  the author's doc weren't in the task's required pair list, so "agree"
  here is limited to the ten pairs I actually ran — but every one of
  those ten is an exact match.
- **19 tests, written before the code, "watched to fail" history:** I can
  confirm the tests exist and all pass now (step 1); I have no way to
  independently confirm the *history* claim ("watched to fail
  `FAILED (errors=1)`... `failures=7`") since that is about a prior state
  of the branch, not something re-runnable now. Not verified either way —
  a plausible, unfalsifiable-from-here claim.
- **Two hooks, prepare_font and verify, attest twice:** confirmed by
  running both independently in step 3 (3d/3f for prepare_font, 3e/3f for
  verify via `pipeline rebuild`).
- **RED run output (prepare_font FAIL 8→8, exit 1; rebuild FAIL + PASS
  /ActualText, exit 1) and GREEN run output (PASS 8→4, exit 0; rebuild
  PASS + PASS /ActualText, exit 0), including the incidental
  "40 KB, 134 chars, render check 432 px":** all exact matches, verbatim,
  in step 3.
- **"Note what the red run shows about gate 17: PASS shaped-script
  targets carry /ActualText is printed on the broken output too":**
  confirmed exactly in my step 3e output.
- **Visual pass description (explicit halant, separated consonant,
  trailing i-matra vs क्त/प्त conjuncts, leading i-matra, ra-vattu):**
  agrees with what I saw and described independently in step 3g, arrived
  at before I had read this section of the author's doc.
- **Canary/Latin silence ("Latin jobs print nothing"):** the doc's "The
  gate" section states this in passing; I ran it directly as the task's
  step 4 asked and confirmed it — exit 0, no "conjunct" anywhere in the
  report.
- **"260 + 11 canary, OK, 0 skipped":** confirmed exactly in step 5.
- **Khmer reclassification and DECISIONS.md row ("the 15 September
  brief's own table read Khmer coeng 0.80... AGENTS.md's prose was
  corrected the same day"):** I did not take this claim on trust — I
  grepped `AGENTS.md` and `docs/DECISIONS.md` directly.
  `AGENTS.md:77-79` reads "Khmer was listed here on 15 September and
  ... so Khmer is probed" and `docs/DECISIONS.md:33` has a
  2026-09-15 row stating "Khmer **is** probed by glyph count... the
  15 September brief's own table read the same (Khmer coeng 0.80)." Both
  documents corroborate the author's claim as written.
- **The three "design experiments" (retypeset embeds the whole font
  program 243,520 bytes / 845 glyphs; a `prepare_font` subset still
  shapes 27 KB / 8→4; deleting GSUB gives 8→8):** **not verified by me.**
  The author's doc says these come from `scratch/design_experiments.py`,
  "not committed" — that file is not in the repo for me to run, and
  reproducing it was not one of the task's required steps. I neither ran
  nor spot-checked these three numbers; treat them as the author's
  unverified claim.
- **"What this gate does not do" (Thai/Lao/Hebrew niqqud REVIEW;
  Gujarati/Gurmukhi/etc. REVIEW; attests the face not every cluster):**
  consistent with my own reading of `shaping_probe.py` in step 6, and with
  the unit test names (`test_reviews_thai_instead_of_passing_it`,
  `test_reviews_a_blind_script_without_claiming_it`) which passed in
  step 1.

**Net:** every claim in the author's doc that maps to one of this task's
required steps reproduced exactly, command for command, exit code for
exit code, number for number. The two claims I could not independently
verify (the pre-code TDD failure history, and the three uncommitted
design-experiment numbers) are flagged above as unverified rather than
confirmed. The one new thing this pass adds is the page-level
font-attribution gap in step 6, confirmed by a constructed test rather
than by reading — it is a real, reproducible way to get a false FAIL, but
not a way to get a false PASS, so it does not undermine the gate's core
claim that a broken face on a page that actually draws with it will be
caught.
