# Compliance — what the output is, and what it is not

A translated PDF that looks exactly like an official form **is not that
form**. The nearer this pipeline gets to a pixel-faithful copy, the more
important it is that the delivery says so, and that the document itself says
so where a reader could be misled.

## The output is a working copy, not a certified translation

Say this in every delivery, in these terms:

> This is a translated working copy produced from the original PDF. It is
> not a certified translation, and it is not an official issue of the
> document. Where the issuer publishes its own translation, that one
> governs.

A certified translation is a statement signed by a person (see §3). No
script produces one.

## 1. When a notice belongs in the document

Decide this at the **identity step**, from the document class — before you
author any translation.

Add a target-language notice on page 1 when the class is:

- a **court** form, filing, notice or order
- a **government** application, benefit, tax or immigration form
- anything the reader **files with**, **submits to**, or **signs for** an
  authority
- a **medical consent** or other document that records a decision

Do not add one to a brochure, manual, marketing sheet or internal document.

The notice says three things: this is a translation, it is for
understanding only, and what the reader must actually file. Wording to
adapt (target language, always — a notice the reader cannot read is
decoration):

> **Translation for information only.** This is an unofficial translation
> of *{form number / title}*, provided to help you understand the form.
> You must complete and file the official *{source-language}* version.
> If the two differ, the official version governs.

For a document nobody files (a notice, a decision, an information sheet):

> **Unofficial translation.** This document was translated for your
> convenience. The official *{source-language}* version is the one that has
> legal effect.

**Where to put it.** Prefer a line the layout already has room for — the
foot of page 1, or a margin. If nothing fits, say so in the delivery and let
the requester decide; do not shrink the form's own text to make room, and do
not add a page unless the requester asks (a page count change breaks the
"visually indistinguishable" promise and can break a filing).

**What the gates do with it.** The notice names the form in the source
language, so verify's leak scan keeps a run that equals the original's
`/Title` — quote the title as one unit, in the source language, with
target-language words around it — and prints it as a note instead of a
failure. Anything longer that merely contains the title is still a leak,
and a page with a notice is not exempt. A source-language title that is
not the file's `/Title`, or an issuer's multi-word name (`Riverside
Elementary School`), is a decision you made, not something the scan can
know: keep it with `--allow "Riverside Elementary School"` (a phrase
matches that run and nothing else; single words still allowlist
themselves everywhere) and say so in the delivery.

This is a judgment call about *this* job, not a legal opinion. Rules vary by
jurisdiction, issuer and purpose. When the requester needs a filing to be
accepted, tell them to confirm the requirement with the issuer — and say
that in the delivery rather than implying you checked.

## 2. Prior art worth matching

Issuers that publish translations of their own forms almost always carry a
notice like the above. California's Judicial Council supplies translated
forms as informational aids and requires the English form to be filed;
USCIS accepts documents in English and requires a certified translation of
anything else; the EU institutions mark unofficial language versions as
non-authentic. Matching that convention is both honest and familiar to the
reader.

If the issuer has published a translation of *this* document, its notice
wording is the one to reuse — the same rule as terminology.

## 3. Translator's certification (a human signs this)

Where a certified translation is required — an immigration filing, a court
exhibit, a records request — a person attests to it. Give the requester this
template; do not fill in a name, and never sign on someone's behalf.

```
CERTIFICATION OF TRANSLATION

I, ______________________________ , certify that:

1. I am competent to translate from {source language} into {target
   language}.
2. The attached document, "{document title / form number}", consisting of
   ____ pages, is a complete and accurate translation of the original
   document to the best of my knowledge and ability.
3. {Optional: describe any part not translated, and why — e.g. seals,
   signatures, illegible text.}

Signature: ______________________________   Date: ______________

Printed name: ___________________________
Address / organisation: _________________
Contact: ________________________________
```

Notes for the delivery, not for the certificate:

- Some jurisdictions require notarisation, a sworn or court-registered
  translator, or an apostille. Which one is the requester's to confirm.
- A certification covers a specific rendering of a specific document. If the
  translation changes afterwards, the certificate no longer applies.
- The scripts in this skill cannot be the certifying party, and neither can
  a model. Name the human.
