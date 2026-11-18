"""Step 11 (optional). Build a topic-sorted PDF (mega + one per section) with answers, explanations and amber key notes.
Usage: INTRO="one paragraph" python build_pdf.py WORK "Label"
Writes WORK/out/*.pdf. Needs reportlab and DejaVu fonts (fonts-dejavu-core).

Original: Build mega PDF + per-section PDFs from /home/claude/work/final/<chapter>.json files.
Final item schema: {"stem","options":{A..E},"answer":"C","explanation":"...","key_note":"...","figure":""}
"""
import json, os, glob, re, sys
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer,
                                KeepTogether, PageBreak, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FD = '/usr/share/fonts/truetype/dejavu/'
pdfmetrics.registerFont(TTFont('DV', FD + 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DVB', FD + 'DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DVI', FD + 'DejaVuSans-Oblique.ttf'))
pdfmetrics.registerFont(TTFont('DVBI', FD + 'DejaVuSans-BoldOblique.ttf'))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily('DV', normal='DV', bold='DVB', italic='DVI', boldItalic='DVBI')

import sys
W = sys.argv[1] if len(sys.argv) > 1 else '.'
TAX = json.load(open(f'{W}/taxonomy.json'))
NAVY = colors.HexColor('#1F3A5F'); TEAL = colors.HexColor('#0F766E')
GREEN_BG = colors.HexColor('#E8F5EE'); GREEN = colors.HexColor('#166534')
AMBER_BG = colors.HexColor('#FFF4E0'); AMBER = colors.HexColor('#9A5B00')
GREY = colors.HexColor('#555555')
SEC_COL = ['#7C3AED', '#C2410C', '#4338CA', '#BE185D', '#0369A1', '#6D28D9', '#B45309', '#4D7C0F', '#15803D', '#334155']

st = {
 'title': ParagraphStyle('t', fontName='DVB', fontSize=24, leading=30, textColor=NAVY, spaceAfter=10),
 'sub': ParagraphStyle('s', fontName='DV', fontSize=11, leading=15, textColor=GREY),
 'sec': ParagraphStyle('sec', fontName='DVB', fontSize=18, leading=24, textColor=colors.white),
 'ch': ParagraphStyle('ch', fontName='DVB', fontSize=13.5, leading=18, textColor=NAVY, spaceBefore=10, spaceAfter=6),
 'q': ParagraphStyle('q', fontName='DV', fontSize=9.6, leading=13.2, spaceAfter=2),
 'opt': ParagraphStyle('o', fontName='DV', fontSize=9.4, leading=12.4, leftIndent=16),
 'ans': ParagraphStyle('a', fontName='DV', fontSize=9.2, leading=12.6, textColor=colors.black),
 'note': ParagraphStyle('n', fontName='DVI', fontSize=8.6, leading=11.5, textColor=AMBER),
 'toc0': ParagraphStyle('toc0', fontName='DVB', fontSize=11, leading=16, spaceBefore=6),
 'toc1': ParagraphStyle('toc1', fontName='DV', fontSize=9.5, leading=13, leftIndent=14),
}

def P(t, s): return Paragraph(t, st[s])
def E(t): return escape(str(t or '')).replace('\n', '<br/>')

class Doc(BaseDocTemplate):
    def __init__(self, fn, label, **kw):
        super().__init__(fn, pagesize=A4, leftMargin=16*mm, rightMargin=16*mm, topMargin=16*mm, bottomMargin=15*mm, **kw)
        self.label = label
        fr = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id='f')
        self.addPageTemplates([PageTemplate('p', [fr], onPage=self._deco)])
    def _deco(self, c, d):
        c.saveState(); c.setFont('DV', 7.5); c.setFillColor(GREY)
        c.drawString(16*mm, 8*mm, self.label)
        c.drawRightString(A4[0]-16*mm, 8*mm, str(d.page)); c.restoreState()
    def afterFlowable(self, f):
        if hasattr(f, 'toc_level'):
            self.notify('TOCEntry', (f.toc_level, f.toc_text, self.page))

def sec_banner(i, sec):
    t = Table([[P(E(f"{sec['title']}"), 'sec')]], colWidths=[178*mm])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(SEC_COL[i % 10])),
                           ('LEFTPADDING', (0, 0), (-1, -1), 10), ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8)]))
    t.toc_level = 0; t.toc_text = sec['title']
    return t

def q_block(n, it):
    fl = [P(f'<b>{n}.</b> ' + ('<font color="#0F766E" size="7.5">[NEW BANK]</font> ' if it.get('_new') else '') + E(it['stem']), 'q')]
    if it.get('figure'):
        fl.append(P('<i>[Figure in original paper: ' + E(it['figure']) + ']</i>', 'opt'))
    for k in sorted(it.get('options', {})):
        fl.append(P(f'<b>{k}.</b> ' + E(it['options'][k]), 'opt'))
    a = it.get('answer') or '?'
    atxt = it.get('options', {}).get(a, '') if a in it.get('options', {}) else ''
    if not atxt and it.get('answer_text'):
        lab = E(it['answer_text']) if a == '?' else E(a) + '. ' + E(it['answer_text'])
    else:
        lab = E(a) + ((". " + E(atxt)) if atxt else "")
    inner = [P(f'<font color="#166534"><b>Answer: {lab}</b></font>', 'ans')]
    if it.get('explanation'):
        inner.append(P('<b>Why:</b> ' + E(it['explanation']), 'ans'))
    if it.get('key_note'):
        inner.append(P('⚠ ' + E(it['key_note']), 'note'))
    box = Table([[inner]], colWidths=[172*mm])
    box.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), GREEN_BG), ('LEFTPADDING', (0, 0), (-1, -1), 6),
                             ('RIGHTPADDING', (0, 0), (-1, -1), 6), ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                             ('LINEBEFORE', (0, 0), (0, -1), 2.2, GREEN)]))
    fl += [Spacer(1, 3), box, Spacer(1, 9)]
    return KeepTogether(fl)

DATA_DIR = os.environ.get('DATA_DIR', f'{W}/final')
INTRO = os.environ.get('INTRO', '')
def load_ch(code):
    p = f'{DATA_DIR}/{code}.json'
    return json.load(open(p)) if os.path.exists(p) else []

def build(fn, label, sections, mega):
    doc = Doc(fn, label)
    story = []
    total = sum(len(load_ch(c[0])) for _, s in sections for c in s['chapters'])
    story += [Spacer(1, 40*mm), P(E(label), 'title'),
              P(f'{total} unique MCQs, sorted by topic, each with the answer and a short explanation.', 'sub'), Spacer(1, 4),
              P(INTRO, 'sub'),
              PageBreak()]
    toc = TableOfContents(); toc.levelStyles = [st['toc0'], st['toc1']]
    story += [P('Contents', 'ch'), toc, PageBreak()]
    qn = 0
    for i, sec in sections:
        chs = [(c, load_ch(c[0])) for c in sec['chapters']]
        if not any(items for _, items in chs):
            continue
        story.append(sec_banner(i, sec)); story.append(Spacer(1, 6))
        for (code, name), items in chs:
            if not items: continue
            h = P(E(f"{'Ch ' + code + ': ' if code[0].isdigit() else ''}{name}  ({len(items)})"), 'ch')
            h.toc_level = 1; h.toc_text = f"{name} ({len(items)})"
            story.append(h)
            for it in items:
                qn += 1
                story.append(q_block(qn, it))
        story.append(PageBreak())
    doc.multiBuild(story)
    return total


if __name__ == '__main__':
    label = sys.argv[2] if len(sys.argv) > 2 else 'MCQ bank'
    out = f'{W}/out'; os.makedirs(out, exist_ok=True)
    secs = list(enumerate(TAX['sections']))
    print('mega', build(f'{out}/{label} - Complete.pdf', label, secs, True))
    for i, s in secs:
        safe = re.sub(r'[^A-Za-z0-9&,\- ]', '', s['title'].split('(')[0]).strip()
        print(s['title'], build(f'{out}/{label} - {i+1:02d} {safe}.pdf', f"{label}: {s['title']}", [(i, s)], False))
