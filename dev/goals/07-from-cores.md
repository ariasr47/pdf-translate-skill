# Objective: scaffold translations.json from to_translate.json cores

> Ease, not quality. No LLM. `pipeline.py init` already strips + extracts.
> Do not auto-merge, auto-skip, or identity-map.

---

## 1. Compass (not done)

After `init`, the author still types a JSON envelope by hand. That is
busywork. Filling values with the source string would let retypeset
PASS an untranslated file. Filling `""` would stamp blank type.
JSON `null` is already “missing” in retypeset (`T.get(core) is None`).
That is the scaffold: keys = cores, values = null, empty merges /
overrides / skip / center, placeholder fonts. `--force` to overwrite.

## 2. Done when — closed bar

1. `pipeline.py from-cores --work DIR` reads `DIR/to_translate.json`,
   writes `DIR/translations.json`. Every core `text` is a key; every
   value is JSON null. `fonts.regular` / `fonts.bold` placeholders.
   `merges`, `overrides`, `center`, `skip`, `allow_scale` empty lists.
   No `mirror`. No vendor call.
2. Existing file → exit 2 unless `--force`.
3. Missing `to_translate.json` → exit 2.
4. Scaffold fed to retypeset → exit 1 listing a real core (not a silent
   empty PDF).
5. `init` unchanged (does not write translations.json).
6. SKILL.md documents the command. Unittest + corpus green.

## 3. Not done when

- Calling a model
- Auto-merge from extractor warnings
- Identity translations
- Folding this into `init`

## 4. Method

Tiny constructed PDF, `pipeline.main`. Import shipped pipeline.

## 5. Invariants

Provider-neutral. No glossary.

## 6. Proof

In-repo from-cores tests + full unittest.
