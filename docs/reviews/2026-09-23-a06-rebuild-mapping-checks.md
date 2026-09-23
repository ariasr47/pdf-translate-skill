# A06: the default legacy rebuild verifies against the mapping it built from

23 September 2026 · local branch `fix/a06-rebuild-mapping-checks`, from main
`178a06f` · nothing pushed or released · version unchanged (v60)

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
