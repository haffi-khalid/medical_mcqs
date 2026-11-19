"""Same as prepare_sources.py but uses PyMuPDF (no poppler needed; for Windows). Usage: python prepare_sources_fitz.py WORK"""
import sys, os, re, json, shutil, warnings
warnings.filterwarnings('ignore')
import pymupdf
from PIL import Image
W = sys.argv[1]
src = os.path.join(W, 'src'); os.makedirs(os.path.join(W, 'pages'), exist_ok=True); os.makedirs(os.path.join(W, 'text'), exist_ok=True)
inv = []
def code_of(name):
    c = re.sub(r'[^A-Za-z0-9]+', '_', os.path.splitext(name)[0]).strip('_').upper()
    return c[:40] or 'FILE'
seen = set()
for f in sorted(os.listdir(src)):
    p = os.path.join(src, f); ext = f.lower().rsplit('.', 1)[-1]
    code = code_of(f)
    while code in seen: code += '_X'
    seen.add(code)
    pdir = os.path.join(W, 'pages', code); os.makedirs(pdir, exist_ok=True)
    rec = {'code': code, 'file': f, 'kind': ext}
    if ext == 'pdf':
        D = pymupdf.open(p); rec['pages'] = len(D); txt = []
        for i, pg in enumerate(D, 1):
            pix = pg.get_pixmap(matrix=pymupdf.Matrix(1.53, 1.53))
            ip = os.path.join(pdir, 'p-%03d.jpg' % i); pix.save(ip, jpg_quality=80)
            I = Image.open(ip)
            if max(I.size) > 2200: I.thumbnail((1600, 2000)); I.save(ip, quality=85)
            txt.append(pg.get_text('text', sort=True))
        t = '\f'.join(txt); open(os.path.join(W, 'text', code + '.txt'), 'w', encoding='utf8').write(t)
        rec['text_chars'] = len(t.strip())
    elif ext == 'docx':
        import docx
        d = docx.Document(p); out = []
        for para in d.paragraphs:
            s = ''
            for r in para.runs:
                t = r.text
                if not t: continue
                hl = None
                try: hl = r.font.highlight_color
                except Exception: hl = 'x'
                if hl is not None: t = '==' + t + '=='
                if r.bold: t = '**' + t + '**'
                s += t
            if s.strip(): out.append(s)
        for tb in d.tables:
            for row in tb.rows: out.append(' | '.join(c.text for c in row.cells))
        open(os.path.join(W, 'text', code + '.md'), 'w', encoding='utf8').write('\n'.join(out))
        rec['pages'] = 0; rec['text_chars'] = sum(map(len, out))
    else:
        rec['note'] = 'unsupported'
    inv.append(rec); print(rec, flush=True)
json.dump(inv, open(os.path.join(W, 'inventory.json'), 'w'), indent=1)
print('files', len(inv), 'pages', sum(r.get('pages', 0) for r in inv))
