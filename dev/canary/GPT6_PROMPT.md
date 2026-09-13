# Canary prompt for GPT 6 — Windows or macOS, unattended

Paste the fenced block below into the harness that runs GPT 6, verbatim.
It is the canary's one-line job (`README.md`) with the two paths made
repo-relative, plus the environment steps runs 1–3 got by hand, plus two
things those runs did not have because a person was at the keyboard: the
setup at the top (clone, venv, fixture, run directory) and the scoring
block at the bottom, fenced off by the rule that nothing under `dev/`
may be read before `DELIVERY.md` is final. Nothing in it says what the
translation should contain. Record both additions in the run file.

The repository is private: sign the machine in to GitHub once (`gh auth
login` or Git Credential Manager) before starting, or the clone step will
stop and say so. A harness without image viewing scores 0 on the visual
pass for harness reasons; `RUN-INFO.md` is where that gets recorded.

Afterwards a person scores axes 1, 2, 4 and 5 from the run directory and
writes `dev/canary/runs/<date>-gpt-6.md` with the five scores, the harness,
the cost and this prompt verbatim.

````
You are working on a machine that is either Windows or macOS. Detect which, and follow the matching commands below. Use whatever shell your harness provides.

SETUP, in this order, before anything else:

1. The repository. It should be at %USERPROFILE%\dev\pdf-translate-skill on Windows or ~/dev/pdf-translate-skill on macOS. If it is not there, clone it into that parent directory:
   git clone https://github.com/ariasr47/pdf-translate-skill
   The repository is private. If the clone asks for a username, password or token, stop immediately and report that GitHub credentials are needed on this machine. Do not enter any credentials yourself.
   Make the repository root your working directory for every command that follows. Every path below is relative to it. Do not commit, push, or change anything git tracks.

2. Python. The scripts need Python 3.10 or newer with the packages in pdf-translate/requirements.txt, in a virtual environment at pdf-translate/.venv.
   - If pdf-translate/.venv already exists, use it.
   - Otherwise create it. Windows: py -3 -m venv pdf-translate\.venv (use the py launcher, not bare python, which is the Store alias). macOS: use the newest python3.X on PATH that is 3.10 or newer, not bare python3, which is Apple's 3.9. Then install: <venv python> -m pip install -r pdf-translate/requirements.txt
   - The interpreter to use for every script from here on is pdf-translate\.venv\Scripts\python.exe on Windows or pdf-translate/.venv/bin/python on macOS. Call it PY. Confirm PY --version prints 3.10 or newer, and that PY -c "import pymupdf, pikepdf, fontTools" succeeds. If either fails, stop and report why.

3. Set the environment variable PYTHONUTF8 to 1 for every command you run (PowerShell: $env:PYTHONUTF8=1; cmd: set PYTHONUTF8=1; bash or zsh: export PYTHONUTF8=1).

4. Regenerate the fixture: PY dev/canary/make_fixture.py
   It writes dev/canary/fixtures/permission_form.pdf. Confirm the file exists and has 2 pages.

5. Create an empty run directory: runs/gpt-6-2026-09-04 under the repository root. If it already exists, append -2, -3 and so on until you can create a new empty one. Everything you write goes inside it and nowhere else.

6. Read only the following outside your run directory: the fixture PDF from step 4 and the skill directory named in the job below. Do not open anything else under dev/ until the last block of this prompt tells you to.

THE JOB:

Translate dev/canary/fixtures/permission_form.pdf into Spanish, keeping the layout and every form field working. Use the pdf-translate skill at pdf-translate.

Work in the run directory from step 5. Do not write anywhere outside it. When you are finished, leave a DELIVERY.md in it with your delivery.

AFTER DELIVERY.md IS WRITTEN AND FINAL, and only then:

7. Run this exact command once, from the repository root, and save its complete output to <run directory>/SCORE.txt:
   PY dev/canary/score.py dev/canary/fixtures/permission_form.pdf <run directory>
   Do not modify any file in the run directory after this command has run, whatever it reports.

8. Write <run directory>/RUN-INFO.md containing, as plain facts: the operating system; the output of PY --version; the model identifier you are running as; the name of the harness or tool that is running you and whether it let you view images, run shell commands and use the web; the total tokens and wall-clock time the job took if you can see them; the number of tool calls; and this entire prompt, verbatim, in a fenced block.

Then stop.
````
