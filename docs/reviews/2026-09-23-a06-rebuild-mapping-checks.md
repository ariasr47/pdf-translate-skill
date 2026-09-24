# A06: the default legacy rebuild verifies against the mapping it built from

23 September 2026 · branch `fix/a06-rebuild-mapping-checks`, from main
`178a06f` · merged as PR #25; shipped in v61

## The defect, reproduced on main

`pipeline.py rebuild` builds from `DIR/translations.json` and
`DIR/segments.json`, then runs verify with only the flags the caller
forwarded. It adds the mapping for typography mappings only
(`pipeline.py:499-504`). On a legacy job, a default rebuild therefore
verifies with no mapping. The checks that need one — empty targets,
authored-target placement, override markers, identifiers, button captions,
caption width, metadata and scaled runs — never run.

`dev/probes/a06_rebuild_mapping_probe.py` builds a real job directory per
case (source PDF, `run_extract`, `run_strip`, an authored mapping) and runs
`scripts/pipeline.py rebuild` as a subprocess. On `178a06f`:

| Case | Exit | Report | Mapping gates in the report |
|---|---|---|---|
| complete mapping, default flags | 0 | exit 0 | none |
| one target `""`, default flags | **0** | **exit 0** | none |
| one target `"   "`, default flags | **0** | **exit 0** | none |
| one target `null`, default flags | 1 (the build refuses) | removed | — |
| one core absent, default flags | 1 (the build refuses) | removed | — |
| one target `""`, explicit `--translations`/`--segments` | 1 | `empty-targets` FAIL | all eight |
| complete mapping, explicit `--translations` elsewhere | 0 | exit 0 | all eight |
| override that drops the source's `a.` marker, default flags | **0** | **exit 0** | none |

The same override case, rebuilt with explicit `--translations` and
`--segments`, exits 1 with `placement` and `override-markers` FAIL. So the
checks exist and work; the default route skipped them.

## Behaviour, defined before the change

Legacy mappings only; the typography route is unchanged.

1. **Default.** When the caller forwards neither `--translations` nor
   `--segments`, rebuild passes verify the files it built from:
   `--translations DIR/translations.json --segments DIR/segments.json`. Every
   mapping-dependent check runs on every default rebuild.
2. **Explicit override.** A forwarded `--translations PATH` is honoured
   exactly as given, and so is a forwarded `--segments PATH`. The mapping is
   always supplied: when the caller forwards `--segments` alone, rebuild still
   adds `--translations DIR/translations.json`. The default segments come only
   with the default mapping. With the caller's own `--translations` and no
   `--segments`, verify's existing rule applies: it reads `segments.json`
   beside that mapping. Callers who pass both, as the documentation shows, get
   exactly what they get today.
3. **What counts as an override.** Only the exact tokens verify itself
   recognises (`--translations VALUE`, `--segments VALUE`). The
   `--translations=VALUE` spelling was never read by verify. It does not
   suppress the default, so it cannot turn mapping checks off.
4. **No opt-out.** Rebuild has no way to verify a legacy build without a
   mapping. Structure-only checking stays available by running `verify.py` or
   `run_verify` directly without `--translations`, and that result does not
   attest authored-target coverage, as the documentation already says.
5. **Unchanged.** A null or absent target still fails the build before
   verification (retypeset's coverage gate). A03's report invalidation, and
   its protection of the input and output paths, still run before anything
   else. A verify FAIL stays advisory: the PDF is written and rebuild exits 1.

**Consequence to name.** A default legacy rebuild that exited 0 on main can now
exit 1 when the mapping-dependent checks find something: an empty target, a
dropped marker or tail, a translated write/find/say identifier. Those are the
defects these checks exist for, and the workflow has told authors to pass the
mapping since 20 September. The verify console of a default rebuild gains the
mapping gates' lines.

## What changed

`cmd_rebuild` (legacy branch only): when `--translations` is not among the
forwarded tokens, rebuild appends `--translations DIR/translations.json`; when
`--segments` is not among them either, it also appends
`--segments DIR/segments.json`. That is the rule above, and nothing else in
rebuild moved. The skill, README, gates reference and consumer guide carry
the 20 September verification-examples slice. It was routed here from the old
checkout because this change rewrites the sentences it touched. The rebuild
examples drop the mapping flags they no longer need; direct `verify.py` and
`run_verify` examples keep them; final-artifact verification after field fonts
is added.

## Verification

| Check | Result |
|---|---|
| New tests, `tests.test_rebuild_attempt.DefaultMappingVerificationTests` (8, as real rebuild subprocesses) | RED on `178a06f`: 6 failed for the missing feature, and 2 controls passed (a caller's explicit mapping is honoured; a null target refuses the build). GREEN after the fix: the module's 16 tests, including A03's 8, pass. |
| Full discovery on the fix | **GitHub CI, run 35935414545 at `9f9365d` (the fix `55bb44d` plus docs), dispatched after the push:** Linux 678 tests OK in 763.086 s, Windows 678 OK with the existing cross-drive skip in 856.040 s, the canary 15 OK on both, the plugin manifest job green. Two earlier local runs on `55bb44d` had been cut off by crashes of the local machine. The one local run that completed (before the two test updates) failed only on those two tests. |
| Probe after the fix (`dev/probes/a06_rebuild_mapping_probe.py`, fresh directory) | complete default: 0, all eight mapping gates present; empty `""` and `"   "`: 1, `empty-targets` FAIL; dropped marker: 1, `placement` and `override-markers` FAIL; null and absent: 1, build refused, no report (unchanged); explicit flags: 1 (unchanged); explicit mapping elsewhere: 0 (unchanged) |
| Documented examples (`dev/probes/a06_doc_examples_probe.py`, adapted from the 20 September harness) | 7 CLI commands read from README, SKILL and gates (2 rebuild, 5 verify) and 2 `run_verify` calls from the consumer guide, over an empty-target, a complete and a fillable job: 30 expected outcomes, including 3 bare default rebuilds (empty: 1; complete and fillable: 0, with field round-trip PASS) |
| CLI ratchet (`cli_parity_runner.py`, eleven CLIs, `178a06f` vs fix) | byte-identical. Its rebuild already passes `--translations`, which shows explicit callers are untouched. |
| Default route on the ratchet's own correct job, `178a06f` vs fix | exit 0 both; the fix's console gains exactly the seven mapping gates' PASS lines (empty targets, authored translations, button captions, caption width, metadata, scaled runs, identifiers) |

The saved input for the examples probe is the 19 September audit's
`empty-target` case (`runs/public-readiness-audit-2026-09-19/repro/empty-target`
in the original checkout, ignored). Raw logs are in this worktree's ignored
`runs/a06/`, and [sanitised results](data/2026-09-23-a06-rebuild-mapping-checks.json)
are committed.

**AGENTS.md Rule 1.** This changes which flags rebuild passes to verify, and
the documentation; no rendering, shaping, font or layout code. The independent
pass is recorded below regardless.

**Independent verification (a separate pass on another model, with real CLI
runs only, against the baseline export and `55bb44d`): verified with
findings, neither a defect.** It built fresh one-page jobs and ran
`scripts/pipeline.py rebuild` and `scripts/verify.py` as subprocesses. Every
clause of the behaviour defined above held:

| Case | Baseline | Fix |
|---|---|---|
| target `""` or `"   "`, default flags | 0, no mapping gate | 1, `empty-targets` FAIL |
| complete mapping, default flags | 0, no mapping gate | 0, `empty-targets` and `placement` PASS |
| caller's `--translations` pointing at a mapping with an empty target | 1 | 1 (honoured, unchanged) |
| empty target, `--segments` forwarded alone | 0 | 1 |
| empty target, `--translations=VALUE` spelling | 0 | 1 |
| target `null` or core absent | 1, build refused, no PDF | the same |
| direct `verify.py` without a mapping | — | 0, the structure-only mode `gates.md` states |

Seven break-it runs gave no false PASS and no false FAIL: `--work` after the
positional arguments, `--work .`, relative paths, a space in the path, a
custom `--report`, an override that keeps the source's marker, and a `skip`
entry. It read the log of CI run 35935414545 instead of re-running tests. All
eight new tests ran on both operating systems, and the log has no failure,
error or traceback. Two findings, both existing behaviour, identical on the
baseline:

- **Informational.** A custom `--report` removes the job directory's default
  `verify_report.json` rather than leaving it stale. That is A03's report
  invalidation (`_prepare_rebuild_reports`) working as its comment says.
- **Informational.** A core listed under `skip` is exempt from
  `empty-targets` and `placement` by design. The mapping is still supplied
  and every other check runs.

Its report and case directories are in this worktree's ignored
`runs/a06-verifier-2/`; the two earlier attempts, cut off by crashes of the
local machine, left `runs/a06-verifier/`. The first case's own default report
was not kept, because later custom-report runs in the same job directory
removed it (the first finding). Six kept rebuild reports from that same
empty-target job show the fix's exit 1 with `empty-targets` FAIL, and two show
the baseline's exit 0.

## Limits

- Direct `verify.py` and `run_verify` without a mapping still exit 0 on an
  empty target. That is the documented structure-only mode, now stated
  wherever verification is shown. A06 closes the default rebuild route, the
  one that used to look complete.
- `--source-words-from` is not supplied automatically: it tunes the leak
  scan's vocabulary rather than enabling mapping checks, and adding it would
  change leak verdicts on same-script jobs.
- The version stays v60 on this candidate. The integration that lands it
  should bump and name the consequence above: a default legacy rebuild can
  now exit 1 where it exited 0.
