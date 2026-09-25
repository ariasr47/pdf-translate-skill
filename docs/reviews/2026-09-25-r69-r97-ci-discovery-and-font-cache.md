# R-69 with R-97: CI discovers its tests, and the font cache follows the fetcher — 25 September 2026

**Assignment.** R-69 with R-97 is the next of the review's quick wins,
priority 5 of the assignment. The request of record is the app's
`REQUEST-to-skill-review-2026-09-24`. The findings are R-69 and R-97 in
`docs/REVIEW-2026-09-24.md`, and the assigned behaviour reads "CI discovers
its tests and keys the font cache on the fetcher".

Both change only `.github/workflows/tests.yml` and a test under `dev/repo/`.
Nothing shipped changes, so there is **no version bump**; the branch stays
at v69. That follows the precedent of the earlier CI-only commits `b39079f`
and `f7326cf`. The bump rule covers shipped behaviour, and an installed
plugin sees no difference from a CI change. It sits on `7e04250`, the head of #38 (R-47), which merged into
`main` as `19252b7`.

## The defects

**R-69.** The suite step named its 22 modules by hand. A new module ran
nowhere until someone added it to that line: `test_retypeset_capture` went
about 38 hours unrun on main. The canary and repository steps each named a
single file with `-p`, so a second test file there would not run either.

**R-97.** The font cache key was the literal `noto-fonts-v3`, and
`actions/cache` never re-saves on a hit. Main's CI run on `aa54158`, both
legs:
- restored `noto-fonts-v3`, holding 11 fonts;
- fetched the 9 faces the fetcher gained on 20 September, 42,585 KB per leg;
- and ended with "Cache hit occurred on the primary key noto-fonts-v3, not
  saving cache".

The two cache entries (17.4 MB each) date from 17 September.

**Found while fixing R-97.** Keying on the fetcher alone would not be
enough. The combined `actions/cache` saves at the end of the job, after the
suite has run, and the suite writes into `tests/fonts`: `han_forms.
reference_face` caches instanced copies such as `NotoSansJP-VF-wght400.ttf`
beside their source, 32.7 MB for the four. It returns an existing copy
without checking it (`han_forms.py:144-147`). A job-end save would carry
those instances into later runs, and a change to the instancing code would
then go unexercised in CI.

## The change

`.github/workflows/tests.yml`:
- **The font cache is split into restore and save.** The restore step's key
  is `noto-fonts-${{ hashFiles('pdf-translate/tools/fetch_test_fonts.py') }}`,
  so it changes whenever the fetcher does.
- **The save runs right after the fetch and its check, before the suite,**
  and only on a miss. So the cache holds exactly what the fetcher
  downloaded.
- **The suite step is `python -m unittest discover -s tests -t . -v`,** the
  command both READMEs already give (`README.md:74`,
  `pdf-translate/README.md:122`).
- **The canary and repository steps discover with the default `test*.py`
  pattern** instead of naming one file.

## Red, then green

`dev/repo/test_ci_workflow.py` reads the workflow as text; PyYAML is not a
dependency. It has three tests:
- **A new test file beside any existing one would run.** For every directory
  holding a tracked test file, a `test_zz_new_module.py` there must be
  loaded by some CI `discover` step: its start directory, its pattern, and
  package recursion.
- **The cache key contains `hashFiles('pdf-translate/tools/fetch_test_fonts.py')`.**
- **The cache is saved before the suite runs,** and the combined
  `actions/cache` action is not used.

**Red** on the old workflow, all three fail:
- `['dev/canary', 'dev/repo', 'pdf-translate/tests']` would miss a new file;
- the only key is `noto-fonts-v3`;
- the combined action is in use.

**Green** on the branch: the repository step now runs 6 tests, the three
binary-integrity tests and these three.

**Same tests, new order.** Discovery collects exactly the 736 test IDs the
hand list named, with none extra, none missing, no duplicates and no import
failures. It runs them in module order rather than the hand order.

## Suite

These are CI's new commands, run locally on macOS from `pdf-translate/`,
exactly as the workflow writes them:

| step | command | result |
|---|---|---|
| suite | `discover -s tests -t . -v` | 736 tests: 1 failure, 1 expected failure |
| canary | `discover -s ../dev/canary -v` | 15 tests, OK |
| repository | `discover -s ../dev/repo -v` | 6 tests, OK |
| eval fixtures | `make_fixtures.py` | exit 0 |

- The failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`.
- The expected failure is item 3's right-to-left source pin.
- The module order changed, from the hand order to alphabetical. No test
  depends on it: the outcome is the same as under the hand list (734 tests
  there, before the two R-47 characterization tests).

**No independent pass.** Rule 1 covers rendering, shaping, fonts and layout,
and the bar lists the items that need it. This change is to CI
configuration. Its observable outcome is CI's own log, recorded below.

## On CI

**The PR's first run**, 36091040027 on `e7e2492`, passed on both legs and
on the plugin manifest. The key was
`noto-fonts-bbc69b99550b07be847137a860c9d46547327cd15887fe4cfb686536ffe4fb37`.

| | ubuntu | windows |
|---|---|---|
| restore | "Cache not found for input keys" | the same |
| fetch | 20 faces, 70,964 KB | the same |
| save | "Cache saved with key", after the fetch check and before the suite | the same |
| suite | 736 tests, OK (1 expected failure) | 736 tests, OK (1 skipped, 1 expected failure) |
| canary | 15, OK | 15, OK |
| repository | 6, OK | 6, OK |

- **The suite count is the local run's 736.** Main's last run on `aa54158`
  had 733, before R-47's three tests.
- **The Windows skip** ("temp dir on another drive") is the same one main
  has.
- **The saved entries** are 42.9 MB (ubuntu) and 42.7 MB (windows)
  compressed. That is the 20 fetched faces, 71 MB raw. The old
  `noto-fonts-v3` entries were 17.4 MB for 11 faces. The instanced faces the
  suite writes came after the save, so they are not in the entries.
- These entries belong to the PR's ref. After the merge, `main`'s first run
  misses once and saves its own.

**The next run** restores this key and should fetch nothing: this commit's
run. It is recorded with the next item.
