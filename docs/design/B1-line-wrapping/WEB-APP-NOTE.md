# B1 decision for the pdf-translator web-app session

Rodrigo approved the B1 design direction: preserve **exactly the source page
count**, with text staying on its original page. Wrapping requires explicit
caller permission per occurrence and a caller-authored fixed box. Preserve the
first baseline and flow downward without moving fields, rules, or neighbors.

Try source-size wrapping first, then shrink within the library's existing
0.7× floor and explicit exceptions. If it still cannot fit, report a build
refusal so the author can revise the wording without losing meaning. Never add
continuation pages, clip or omit text, or silently substitute the source text.
An authored box is not an automatic collision-safety guarantee. Kinsoku findings
remain advisory REVIEW.

**Design approved; not implemented.** The first probe fit 6 of 8 synthetic
stress cases without extra pages, but all six moved the first baseline. A
repeated-label control also selected the wrong occurrence. Neither is an
implemented B1 guarantee. The two saved final translation jobs already built;
we still need representative refused jobs and permissible boxes to measure
customer recovery before sizing a plan. No new consumer API is available yet.

Probe evidence: `docs/reviews/2026-09-19-b1-recovery-probe.md`.

For the next measurement, provide representative failed-job **inputs and
behavioral evidence**: source PDF, authored mapping, required font files,
structured refusal output, and any boxes the author permits. No product source
code is needed. The current synthetic result must not be quoted as a customer
recovery percentage.

Sent request: [original failed-job inputs](FAILED-JOB-REQUEST.md).
The local archive search found final jobs and regression fixtures, but no
complete representative failed-job bundle. Rodrigo authorized sending the
request to **Boot Spire Tech web app**. Its reply reports no replayable real
failed-job bundle and no exported cases. Customer recovery remains unmeasured;
see the [reported result](../../reviews/2026-09-19-b1-product-inputs.md).

The subsequent authorized capture returned a known successful one-page FL-150
replay. Its retained inputs and page/widget geometry passed independent checks,
but it made no B1 wrapping attempt. [Capture audit](../../reviews/2026-09-19-b1-captured-case.md).

Reference: `docs/design/B1-line-wrapping/README.md` and `canvas.png` in
`C:\Dev\pdf-translate-skill`.
