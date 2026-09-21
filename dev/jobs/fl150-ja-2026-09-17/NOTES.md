# FL-150 → 日本語 — job notes and reviewer checklist (v2, 2026-09-17)

Files delivered (Downloads):

- `FL-150_ja_2026-09-17_v2.pdf` — the translated, fillable working copy (field fonts embedded)
- `FL-150_original_rev2024-09-01.pdf` — the original used (byte-identical to courts.ca.gov fl150.pdf, Rev. September 1, 2024)
- `FL-150_ja_2026-09-17_v2_comparison.html` — every page side by side at 120 dpi
- `FL-150_ja_2026-09-17_v2_translations.json` — the mapping (247 cores, 13 merges, 5 overrides, 1 notice)
- `FL-150_ja_2026-09-17_v2_review.json` — the second-reader review with every finding's resolution
- this file

v1 (same date, no `_v2`) is superseded: it carried 世帯主 for "head of household".
Produced with pdf-translate v56 (branch `fix/cjk-job-gates`, on top of v55).

**This is a translated working copy produced from the original PDF. It is
not a certified translation, and it is not an official issue of the
document. Where the issuer publishes its own translation, that one governs;
the Judicial Council publishes no Japanese FL-150 (checked 2026-09-17).**
Filing acceptance is the requester's to confirm with the court: the
Judicial Council requires the English form to be filed, and the page-1
notice says so in Japanese.

## 1. Identity record (written before authoring)

1. **Class** — California court family-law form: the Income and Expense
   Declaration, the sworn financial disclosure filed in support and
   attorney-fee proceedings. Fillable, 4 pages, 266 fields, hybrid XFA.
2. **Issuer** — Judicial Council of California, form FL-150
   [Rev. September 1, 2024].
3. **Parallel text** — none in Japanese. The issuer offers FL-150 in Chinese
   (Simplified), Korean, Spanish, Tagalog and Vietnamese
   (https://selfhelp.courts.ca.gov/jcc-form/FL-150). Its Chinese rendering
   (fl150c.pdf) was read for the issuer's conventions and followed: the
   footer identity block, the Family Code citation and the URL stay in
   English; the translation is marked "for reference only — do not file
   with the court" inside the FOR COURT USE ONLY box.
4. **Identifiers kept verbatim** — FL-150; FL-150 [Rev. September 1, 2024];
   Form Adopted for Mandatory Use; Judicial Council of California; Family
   Code, §§ 2030–2032, 2100–2113, 3552, 3620–3634, 4050–4076, 4300–4339;
   www.courts.ca.gov; the quoted labels "Question 1—Other Jobs" and
   "Question 10g" (the reader writes them on an attachment the clerk reads);
   Schedule C; TANF, SSI, GA/GR, SDI, FICA, 401(k), IRA; the `$` signs; the
   paper size (8 1/2 × 11, set as 8 1/2×11インチ). Numbers, dates and
   currency are not localized — a US court filing.

## 2. Register and terminology

- Court-form register: です・ます in instructions, noun labels on fields.
  Terms follow established Japanese usage for California family law and US
  tax: 申立人 (Petitioner), 相手方 (Respondent), 他方の親 (the other parent),
  収入・支出申告書 (Income and Expense Declaration), 配偶者扶養料 (spousal
  support), パートナー扶養料 (partner support), 登録パートナーシップ
  (domestic partnership), 養育費 (child support), 控除, 資産, 事件番号,
  裁判所記入欄, カリフォルニア州上位裁判所 (Superior Court of California;
  the legal reference works' rendering, 上級裁判所 being the press form),
  （氏名）の代理人弁護士 (ATTORNEY FOR (name), the Japanese court idiom).
- US tax filing statuses use the terms of the Japanese-language US tax
  guides: 独身, 特定世帯主 (head of household — NOT 世帯主, which a married
  Japanese reader would take to mean themselves), 夫婦個別申告, 夫婦合算申告.
- Second-reader cross-check against the August 2026 bake-off rendering
  (`Downloads/FL-150_ja_v2.pdf`): terminology converges; six phrasings were
  adopted from it (勤務先, 共同経営者, 私の立場, 光熱費 → later 水道光熱費,
  the perjury sentence's word order, 私は週に約). Not adopted: its translated
  footer block, its transliterated スケジュールC and translated
  「質問1―その他の仕事」 (write/find/say identifiers), its re-captioned buttons.
- "(specify):" → （記入）：, "(explain):" → （説明）： throughout; the one
  exception is the item-7 checkbox label "other (specify):" → その他：
  (width). Yes/No → はい／いいえ. "I do / I do not" → あり／なし with the
  subject as a plain label after the boxes. Pay basis: 月給／週給／時給.
- Source slip recorded, not reproduced: item 19b lists "other insured loss"
  under "losses not covered by insurance"; rendered その他の損失.
- Word order across fields: 16b reads 子は私と [__] ％、他方の親と [__]
  ％の時間を過ごします。; 16a reads 私には（人数を記入）：[__] 人の18歳未満の
  子が本件の他方の親との間にいます。

## 3. Structural changes and disclosures

- The XFA layer was removed (hybrid LiveCycle form; Acrobat would otherwise
  render the English XFA layer). `/Perms /UR3` (Reader extensions) was
  deleted. The source's RC4 encryption (empty user password) was not
  re-applied. The structure tree was removed: **the file is no longer
  tagged.** `/Lang` is `ja`; `/Title` is "FL-150 収入・支出申告書".
- The four pushbuttons on page 4 (Print this form, Save this form, Clear
  this form, and the gray privacy note) lost their scripts with the XFA
  layer. They are **hidden**: the fields still exist (266/266 parity) and
  the gray band behind the note is page graphics and stays. They can be
  re-captioned in Japanese and wired to the viewer's standard print / save /
  reset actions on request.
- Fonts: Noto Sans JP (google/fonts variable build), weights 400 and 700
  instanced and subsetted (581 characters each); the fillable fields carry
  the full 400 instance (`/DA` rewired on 321 text objects). Noto Sans JP
  has no italic: the 45 italic runs of the original ship upright.
- Notice, page 1, lower half of the FOR COURT USE ONLY box (below the
  heading so it does not read as court-authored), 7 pt, bold lead:
  【参考訳】裁判所には提出できません。これは「FL-150 INCOME AND EXPENSE
  DECLARATION」の非公式な日本語訳で、書式の内容を理解するためのものです。
  裁判所には正式な英語版の書式に記入して提出してください。両者に相違がある
  場合は、英語版が優先します。
- Scaled runs (16, all at or above 0.88 of the original size; no
  `allow_scale`): Date: 0.88 (two, the full-width colon chosen over a
  half-width one for consistency); ATTORNEY FOR (name): 0.95; California
  0.96; If no, highest grade completed 0.97; (itemize below in 14…) 0.95;
  the Family Code cite and www.courts.ca.gov 0.98; No 0.98–0.99 (five);
  Other (specify): 0.90 (two); I have (specify number): 0.99.
- Widget text: all 118 tooltips authored in Japanese; the form has no
  dropdowns and no defaults.
- Locale adaptations: none.

## 4. Gates and QA (measured on the delivered v2 build)

- `verify.py`: **exit 0**. PASS field parity 266/266; fill round-trip
  (山田太郎 123); ink ratios within band; text layer visible; canonical text
  layer; kinsoku (322 CJK lines); han-forms (Noto Sans JP Regular and Bold,
  own-convention distance 0.000); no untranslated running text (kept as
  allowlisted: Question 1—Other Jobs, Schedule C, and the footer's
  "September Family Code" where the revision stamp adjoins the statute
  cite); authored translations present; button captions; caption width;
  override markers and tails; document metadata; write/find/say
  identifiers. REVIEW: 13 isolated source-language tokens (the kept
  identity block, the quoted title in the notice, the acronyms) and the 16
  scaled runs above.
- `qa_check.py`: 0 errors, 78 warnings — punctuation parity (full-width ：
  and 。 by Japanese convention), 6 "untranslated" warnings for the
  deliberately kept identity block, 1 inconsistency (Other/other, §2).
- Three verify gates FAILed the first build on a correct file and were
  fixed in the skill (v56): wrapped Japanese paragraphs invisible to the
  placement gate; Noto Sans JP's `locl` digit alternates drifting in the
  text layer; hidden pushbuttons counted as chrome. Each is pinned by a test.

## 5. Review (the second-reader step)

- **Model reviser** (Claude Opus, independent session, MQM typology, saw
  only the pairs and the renders): 31 findings — 1 critical, 6 major, 24
  minor; verdict "revise". Resolutions are in `review.json`: 24 accepted
  and applied in v2, 7 rejected with the reason (the court name, kept 上位;
  the hidden privacy-note button, a disclosed decision; "California",
  measured 1.5 pt clear of its checkbox; the item-7 その他：; the source's
  own "other insured loss"; パートナー扶養料, 4.3 pt clear; 時間額, replaced
  by the 月給／週給／時給 set instead).
- **Human second reader**, page 1 only (2026-09-17): agreed with every
  accepted page-1 item, kept 上位裁判所, and asked for the Japanese court's
  own idiom on ATTORNEY FOR (name) → （氏名）の代理人弁護士：. Pages 2–4 have
  not had a human read.
- The critical finding, 世帯主 for "head of household", passed every gate
  and `qa_check`: no script can tell a plausible wrong term from the right
  one. It was caught by the second reader, which is why that step is a
  deliverable and not an option.

## 6. Reviewer checklist (references/review.md)

```
Document class:            California court family-law form — Income and
                           Expense Declaration (FL-150), sworn financial
                           disclosure, fillable, 4 pages
Issuer:                    Judicial Council of California
Parallel text consulted:   none in Japanese; issuer's Chinese rendering
                           (fl150c.pdf) read for conventions only
Language pair / register:  EN -> ja, court form, plain-language public form

TERMINOLOGY
[x] Terms of art match the class's established usage (US tax statuses and
    family-law roles checked against Japanese-language guides after review)
[x] No calques and no words invented on the page (特別な必要 → 特別なニーズ,
    軍手当 → 軍人手当 fixed in v2)
[x] Identifiers the reader must write, hand over or search are unchanged
[ ] Job termbase (glossary.csv), if any, is honoured — none supplied

ACCURACY
[x] Every figure, amount, percentage and deadline matches the source
    (qa_check numbers: 0 errors)
[x] Dates: the revision stamp stays as printed; 2019年1月1日 in the footnote
[x] Nothing added, nothing dropped; conditions survive — the notice is the
    only added text; the hidden buttons are disclosed in §3
[x] Negations survive

FLUENCY AND REGISTER
[x] Reads as a Japanese court form
[x] Consistent: one source term, one target term — one deliberate
    exception (Other/other, §2)
[x] Forms of address match the issuer's register

PRESENTATION (after looking at rendered pages)
[x] Every page rendered next to the original and inspected — four passes
[x] No clipped, over-shrunk or overlapping text; every run in
    scale_report.json listed (§3)
[x] Dot leaders, checkboxes, rules and columns unchanged
[x] Widget tooltips in Japanese; no dropdowns or defaults on this form

STRUCTURE
[x] verify.py exits 0; qa_check.py findings reviewed, each accepted (§4)
[x] Fields fill (round-trip with 山田太郎 123); no links or bookmarks

SIGN-OFF
Reviewed by:               model reviser (all pages) + one human second
                           reader (page 1); no qualified EN→JA legal
                           translator has signed. Name one before anyone
                           relies on pages 2–4.
Qualified in the pair:     human reader: not stated
Date:                      2026-09-17
Remaining risks:           pages 2–4 unreviewed by a human; the hidden
                           buttons and the empty gray band on page 4;
                           the Acrobat rendering of Japanese in fillable
                           fields relies on the embedded full font.
```

## 7. Certification

Not certified. Where a certified translation is required, a qualified
person signs the template in `references/compliance.md` §3 after revising
this rendering; nothing here may be signed on anyone's behalf.
