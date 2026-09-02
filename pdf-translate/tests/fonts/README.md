# Test fonts

Empty on purpose. The shaping tests (Arabic joining, Devanagari conjuncts)
need a font that actually carries GSUB tables for those scripts; without one
they SKIP, which is how the shaping gates went unexercised on Linux.

Populate it with:

```bash
python3 tools/fetch_test_fonts.py
```

That downloads three SIL Open Font License 1.1 faces (Noto Sans, Noto Naskh
Arabic, Noto Sans Devanagari) from pinned commits. Nothing here is committed:
the repository carries no font binaries, and the licence stays with the
upstream project.

`tests/test_pipeline.py` prefers anything in this directory over the host's
own fonts, so a populated `tests/fonts/` makes the suite behave the same on
every machine.
