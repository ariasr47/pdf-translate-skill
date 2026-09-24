# B1 — request for original failed-job inputs

Sent to **Boot Spire Tech web app** after Rodrigo's explicit “yes send it”
authorization. Destination task: `01a0bc1c-cdb2-7b93-8860-0154a450beb4`.
The task replied that no eligible replayable real failed-job bundle was found;
no cases were exported. See the [reported result](../../reviews/2026-09-19-b1-product-inputs.md).

Please export a small, representative batch of existing translation attempts
that refused because the translated text did not fit. Include the available
document types, such as forms and invoices, without choosing only easy cases.
Keep the wording and failure evidence from before any fixes.

For each case, provide:

- The source PDF, exact authored translation mapping, and required font files
  that may be shared for this measurement.
- The structured refusal output, command/options, and library version used.
- The affected occurrence's page and position, plus any fixed box the author
  permits for wrapping. If permission is unknown, say so; do not infer a box.

Place data-only exports in
`C:\Dev\pdf-translate-skill\runs\b1-real-jobs\<case-id>\` and return the paths
with a brief description of how the batch was selected. Include no product
source code, copied implementation, or rewritten algorithms. If these failed
inputs were not retained, report that instead of constructing replacements.

The approved design preserves exactly the source page count, keeps text on its
original page, and refuses an impossible fit. This request is for evidence;
there is no new B1 API or implementation yet. The existing synthetic 6/8 result
is not a customer recovery percentage.
