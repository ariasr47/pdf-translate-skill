# Wild corpus — sources

Public, born-digital PDFs fetched on 2 September 2026 into `dev/wild/files/`
(gitignored; re-fetch with the URLs below). Chosen to cover the classes the
skill claims: federal tax and immigration forms, a state court form, a
federal personnel form, a medical reporting form, a passport form built on
XFA, an EU regulation, a two-column scientific paper, a consumer handbook
and a hardware datasheet. Sizes are the bytes curl received.

| File | Issuer / class | Bytes | Source |
|---|---|---|---|
| `irs-w9.pdf` | IRS W-9, fillable tax form | 140,815 | https://www.irs.gov/pub/irs-pdf/fw9.pdf |
| `irs-w4.pdf` | IRS W-4, fillable tax form | 208,845 | https://www.irs.gov/pub/irs-pdf/fw4.pdf |
| `irs-1040es.pdf` | IRS 1040-ES, instructions plus payment vouchers | 331,490 | https://www.irs.gov/pub/irs-pdf/f1040es.pdf |
| `irs-i1040gi.pdf` | IRS Form 1040 instructions, long multi-column booklet | 4,434,643 | https://www.irs.gov/pub/irs-pdf/i1040gi.pdf |
| `uscis-i9.pdf` | USCIS I-9, employment eligibility (AcroForm) | 524,095 | https://www.uscis.gov/sites/default/files/document/forms/i-9.pdf |
| `uscis-i864.pdf` | USCIS I-864, affidavit of support (hybrid XFA per third parties) | 542,861 | https://www.uscis.gov/sites/default/files/document/forms/i-864.pdf |
| `uscis-n400.pdf` | USCIS N-400, naturalization (hybrid XFA per third parties) | 776,244 | https://www.uscis.gov/sites/default/files/document/forms/n-400.pdf |
| `uscis-g28.pdf` | USCIS G-28, attorney appearance | 396,003 | https://www.uscis.gov/sites/default/files/document/forms/g-28.pdf |
| `cajc-fl100.pdf` | California Judicial Council FL-100, dissolution petition | 192,902 | https://courts.ca.gov/sites/default/files/courts/default/2024-11/fl100.pdf (redirected from `www.courts.ca.gov/documents/fl100.pdf`) |
| `cajc-fl300.pdf` | California Judicial Council FL-300, request for order | 320,347 | https://courts.ca.gov/system/files?file=2025-07/fl300.pdf (redirected from `www.courts.ca.gov/documents/fl300.pdf`) |
| `opm-sf15.pdf` | OPM SF-15, veterans' preference (fillable) | 1,155,287 | https://www.opm.gov/forms/pdf_fill/sf15.pdf |
| `state-ds11.pdf` | US State Department DS-11, passport application (XFA-based) | 2,568,395 | https://eforms.state.gov/Forms/ds11_pdf.pdf |
| `fda-3500.pdf` | FDA MedWatch 3500, adverse-event report (fillable) | 921,232 | https://www.fda.gov/media/76299/download |
| `eu-gdpr.pdf` | EU Regulation 2016/679 (GDPR), Official Journal PDF, two columns | 982,296 | https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32016R0679 |
| `arxiv-babeldoc.pdf` | arXiv 2605.10845, the BabelDOC paper, two-column with math | 1,586,580 | https://arxiv.org/pdf/2605.10845 |
| `medicare-handbook.pdf` | CMS "Medicare & You" handbook, consumer brochure | 4,064,150 | https://www.medicare.gov/publications/10050-medicare-and-you.pdf |
| `rpi4-datasheet.pdf` | Raspberry Pi 4 datasheet, hardware manual | 413,147 | https://pip-assets.raspberrypi.com/categories/545-raspberry-pi-4-model-b/documents/RP-008341-DS-1-raspberry-pi-4-datasheet.pdf (redirected from `datasheets.raspberrypi.com/rpi4/raspberry-pi-4-datasheet.pdf`) |

Wanted and not fetched (bot protection or a moved URL; fetch by hand in a
browser if the class matters):

| Class | URL tried | Result |
|---|---|---|
| SSA-1 and SSA-16, benefit applications | https://www.ssa.gov/forms/ssa-1.pdf , https://www.ssa.gov/forms/ssa-16.pdf | 403 for non-browser clients |
| CDC vaccine information statement (two-column health leaflet) | https://www.cdc.gov/vaccines/hcp/current-vis/downloads/flu.pdf | 403 for non-browser clients |
| IRCC IMM 5257 / IMM 5406, Canadian visa forms (dynamic XFA, the "Please wait" class) | https://www.canada.ca/content/dam/ircc/migration/ircc/english/pdf/kits/forms/imm5257e.pdf | connection dropped twice |
| NIMH depression brochure | https://www.nimh.nih.gov/.../depression.pdf | the URL now serves an HTML page |
