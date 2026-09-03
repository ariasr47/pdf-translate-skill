# Objective (lane B): the skill installs as a Claude Code plugin

> Hand this to a `/goal` session. Self-contained. Read
> `docs/REVIEW-2026-09-02.md` §3.3 and §5 (P2), `dev/goals/HANDOVER.md`
> §5 ("the installed skill copy is stale") and the Claude Code plugin
> docs (plugins reference; plugin marketplaces). Do not touch
> `pdf-translate/SKILL.md`. Do not rename `pdf-translate/`. Not FL-150.

---

## 1. Compass (not done)

The only installed copy of this skill is a manual copy on a Windows box,
at `metadata.version` 16 against a repository at 35. Every sync is a
person copying a directory and editing a manifest by hand, and the
handover carries the chore as a standing item. A skill nobody runs at
its current version is not a product.

The review measured the fix on this machine (`claude` 2.1.236):
`claude plugin validate --strict` passes a root-as-plugin manifest with
`"skills": ["./"]`, and `claude --plugin-dir <dir> plugin details
pdf-translate` lists the skill from it, always-on about 160 tokens,
on-invoke about 7,300. No restructuring is needed.

## 2. Done when — closed bar

1. **A plugin manifest at the repo root.** `.claude-plugin/plugin.json`:
   name `pdf-translate`, description, `version` equal to
   `metadata.version` as `N.0.0`, author, `license: MIT`, repository,
   keywords, `skills` pointing at the skill directory. The skill
   directory stays `pdf-translate/`.
2. **A marketplace manifest beside it.** `.claude-plugin/marketplace.json`
   with one entry whose source is the repository root, no version of its
   own (so `plugin.json` is the single place a version lives besides
   `SKILL.md`).
3. **Validated and loaded from the repository itself.**
   `claude plugin validate . --strict` exits 0;
   `claude --plugin-dir . plugin details pdf-translate` lists one skill,
   `pdf-translate`.
4. **CI keeps it honest.** A workflow job installs the Claude Code CLI,
   runs `claude plugin validate . --strict`, and fails if `plugin.json`'s
   version and `metadata.version` disagree. The unittest job is untouched.
5. **The install path is written down and the chore is gone.** README:
   `/plugin marketplace add ariasr47/pdf-translate-skill`, then
   `/plugin install pdf-translate@pdf-translate-skill`, then
   `/plugin marketplace update` for every later version (a private
   repository works wherever `git` has GitHub credentials). HANDOVER §5
   drops the re-sync chore and says this instead; the versioning notes
   say `plugin.json` is bumped with `metadata.version`.

## 3. Not done when

- Publishing to any public marketplace
- Renaming or moving `pdf-translate/`
- Changing `SKILL.md` (its frontmatter stays spec-clean; no Claude
  Code-only fields)
- Installing the plugin into this machine's Claude Code configuration
  from the session (that is the user's step, on the box that needs it)

## 4. Method

Write both manifests; validate; load with `--plugin-dir`; add the CI
job; write the README section; delete the chore.

## 5. Invariants

Provider-neutral: the skill directory works as plain instructions with or
without the manifests. Nothing in the skill changes.

## 6. Proof

Validate exit 0; the details inventory; the CI job green after the push;
the version check.

---

## 7. Closing note — 2 September 2026, closed

1. `.claude-plugin/plugin.json`: name `pdf-translate`, version `35.0.0`
   (`metadata.version` is 35; `SKILL.md` untouched), MIT, repository,
   keywords, `"skills": ["./"]` — the root is scanned and
   `pdf-translate/SKILL.md` is the one skill found. The directory keeps
   its name.
2. `.claude-plugin/marketplace.json`: marketplace `pdf-translate-skill`,
   one entry `pdf-translate` with source `./` and no version of its own.
3. From the repository itself: `claude plugin validate . --strict` →
   "Validation passed", exit 0 (it validates the marketplace and the local
   plugin manifest it points at); `claude --plugin-dir . plugin details
   pdf-translate` → one skill, `pdf-translate`, always-on about 164
   tokens.
4. `.github/workflows/tests.yml` gains a `package` job: install the CLI
   with npm, `claude plugin validate . --strict`, and a Python check that
   `plugin.json`'s version equals `metadata.version` as `N.0.0`. The
   unittest job is untouched. **Not yet seen green**: the job runs on the
   next push; if the CLI needs something on a bare runner, that is the
   first thing to fix.
5. README has an Install section; HANDOVER §5's re-sync chore is replaced
   by the install path; PROGRAM's versioning note says to bump both files
   together.

**Not done, as the brief asked:** no public marketplace, no rename, no
change to `SKILL.md`, and no install into this machine's Claude Code
configuration. The install from GitHub (`/plugin marketplace add
ariasr47/pdf-translate-skill` then `/plugin install
pdf-translate@pdf-translate-skill`) is the user's step on the Windows
box; that first install is the proof this row cannot give from here.

174 tests, no skips, green locally; no shipped file changed.
