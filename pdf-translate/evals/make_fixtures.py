#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the two PDFs evals.json points at.

They are generated rather than committed so the repo carries no binaries it
does not need, and so anyone can see exactly what the eval is made of.

  python3 evals/make_fixtures.py [--outdir evals/fixtures]

permission_form.pdf  a one-page school permission slip: twelve fillable
                     fields (text, checkbox, dropdown), dot leaders, a
                     signature rule, a pushbutton with a caption.
garden_flyer.pdf     a one-page workshop flyer: a coloured banner with
                     white text, a price, a URL, two wrapped paragraphs.
"""
import os
import sys

import pymupdf

BLUE = (0.10, 0.29, 0.49)
WHITE = (1, 1, 1)


def permission_form(path):
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), 'Riverside Elementary School', fontsize=16)
    page.insert_text((72, 96), 'Field Trip Permission Slip', fontsize=13)
    page.draw_line(pymupdf.Point(72, 106), pymupdf.Point(540, 106), width=1)
    page.insert_text(
        (72, 132),
        'Please complete this form and return it to the school office by',
        fontsize=10)
    page.insert_text((72, 146), 'Friday, May 8. Keep a copy for your records.',
                     fontsize=10)

    rows = [
        ('Student name:', 'StudentName'),
        ('Teacher:', 'Teacher'),
        ('Parent or guardian:', 'Guardian'),
        ('Daytime phone:', 'Phone'),
        ('Emergency contact:', 'Emergency'),
        ('Allergies or medication:', 'Allergies'),
    ]
    y = 180
    for label, name in rows:
        page.insert_text((72, y), label, fontsize=10)
        widget = pymupdf.Widget()
        widget.field_name = name
        widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
        widget.rect = pymupdf.Rect(220, y - 11, 540, y + 3)
        widget.field_label = f'Enter the {label.rstrip(":").lower()}'
        page.add_widget(widget)
        y += 28

    page.insert_text((72, y + 10), 'Grade level:', fontsize=10)
    grade = pymupdf.Widget()
    grade.field_name = 'Grade'
    grade.field_type = pymupdf.PDF_WIDGET_TYPE_COMBOBOX
    grade.rect = pymupdf.Rect(220, y - 1, 340, y + 13)
    grade.choice_values = ['Kindergarten', 'First', 'Second', 'Third']
    grade.field_value = 'First'
    grade.field_label = 'Choose the grade level'
    page.add_widget(grade)

    y += 44
    for label, name in (('I give permission for my child to attend.', 'Yes'),
                        ('My child will ride the school bus.', 'Bus'),
                        ('I have enclosed the $12.00 trip fee.', 'Fee')):
        box = pymupdf.Widget()
        box.field_name = name
        box.field_type = pymupdf.PDF_WIDGET_TYPE_CHECKBOX
        box.rect = pymupdf.Rect(72, y - 10, 84, y + 2)
        page.add_widget(box)
        page.insert_text((94, y), label, fontsize=10)
        y += 22

    y += 16
    page.insert_text((72, y), 'Amount enclosed ' + '.' * 48 + ' $',
                     fontsize=10)
    amount = pymupdf.Widget()
    amount.field_name = 'Amount'
    amount.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    amount.rect = pymupdf.Rect(470, y - 11, 540, y + 3)
    page.add_widget(amount)

    y += 48
    page.draw_line(pymupdf.Point(72, y), pymupdf.Point(320, y), width=0.8)
    page.insert_text((72, y + 12), 'Signature of parent or guardian',
                     fontsize=9)
    page.draw_line(pymupdf.Point(360, y), pymupdf.Point(540, y), width=0.8)
    page.insert_text((360, y + 12), 'Date', fontsize=9)
    sig = pymupdf.Widget()
    sig.field_name = 'SignatureDate'
    sig.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    sig.rect = pymupdf.Rect(360, y - 16, 540, y - 2)
    page.add_widget(sig)

    button = pymupdf.Widget()
    button.field_name = 'PrintButton'
    button.field_type = pymupdf.PDF_WIDGET_TYPE_BUTTON
    button.field_flags = 1 << 16
    button.rect = pymupdf.Rect(470, 700, 540, 722)
    button.button_caption = 'Print'
    page.add_widget(button)

    doc.set_metadata({'title': 'Field Trip Permission Slip'})
    doc.set_language('en-US')
    doc.save(path)
    doc.close()


def garden_flyer(path):
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.draw_rect(pymupdf.Rect(0, 0, 612, 120), color=BLUE, fill=BLUE)
    page.insert_text((48, 62), 'Spring Garden Workshop', fontsize=26,
                     color=WHITE)
    page.insert_text((48, 92), 'Saturday, April 18 — 10:00 to 14:00',
                     fontsize=13, color=WHITE)

    body = [
        'Bring a pair of gloves and learn how to prepare a raised bed for the',
        'growing season. Our gardeners will cover soil testing, composting and',
        'which vegetables do best in a short summer.',
    ]
    y = 170
    for line in body:
        page.insert_text((48, y), line, fontsize=11)
        y += 18

    y += 20
    second = [
        'Places are limited to twenty people, and children under twelve are',
        'welcome when accompanied by an adult. Tea and cake are included.',
    ]
    for line in second:
        page.insert_text((48, y), line, fontsize=11)
        y += 18

    page.draw_rect(pymupdf.Rect(48, 300, 320, 360), color=BLUE, width=1.2)
    page.insert_text((64, 326), 'Tickets', fontsize=13)
    page.insert_text((64, 348), '$15.00 per person', fontsize=13)
    page.insert_text((48, 400), 'Book at https://example.org/garden-workshop',
                     fontsize=11)
    page.insert_text((48, 420), 'Riverside Community Garden, 14 Mill Lane',
                     fontsize=11)

    doc.set_metadata({'title': 'Spring Garden Workshop'})
    doc.set_language('en-US')
    doc.save(path)
    doc.close()


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    outdir = (argv[argv.index('--outdir') + 1] if '--outdir' in argv
              else os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'fixtures'))
    os.makedirs(outdir, exist_ok=True)
    made = []
    for name, build in (('permission_form.pdf', permission_form),
                        ('garden_flyer.pdf', garden_flyer)):
        path = os.path.join(outdir, name)
        build(path)
        made.append(path)
    for path in made:
        print(f'wrote {path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
