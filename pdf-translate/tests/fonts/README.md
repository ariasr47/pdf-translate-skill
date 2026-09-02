# Test fonts

Empty on purpose. The shaping tests (Arabic joining, Devanagari conjuncts)
need a font that actually carries GSUB tables for those scripts; without one
they SKIP, which is how the shaping gates went unexercised on Linux.

Populate it with:

```bash
python3 tools/fetch_test_fonts.py
```

That downloads four SIL Open Font License 1.1 faces: Noto Sans, Noto Naskh
Arabic, Noto Sans Hebrew and Noto Sans Devanagari. No single Noto face
carries both Arabic and Hebrew (Arial does, which is why these tests only
ever passed on macOS and Windows), so each test asks for a font covering
the characters it actually needs. Nothing here is committed: the repository
carries no font binaries, and the licence stays with the upstream project.

`tests/test_pipeline.py` prefers anything in this directory over the host's
own fonts, so a populated `tests/fonts/` makes the suite behave the same on
every machine.
