"""Step 1. Inventory every source file and make it readable for agents.
Usage: python prepare_sources.py WORK
  WORK/src/        <- put the user's PDFs / .docx / images here
Produces:
  WORK/pages/<CODE>/p-NNN.jpg   page images (agents MUST look at these: answers are often highlights/ticks)
  WORK/text/<CODE>.txt          text layer (pdftotext -layout), empty for scans
  WORK/text/<CODE>.md           for .docx: text with **bold** and ==highlighted== runs preserved
  WORK/inventory.json           [{code, file, kind, pages, text_chars}]
Needs: poppler-utils (pdftoppm, pdftotext, pdfinfo), python-docx, Pillow.
"""
import sys, os, re, json, subprocess, shutil
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
        info = subprocess.run(['pdfinfo', p], capture_output=True, text=True).stdout
        rec['pages'] = int(re.search(r'Pages:\s+(\d+)', info).group(1)) if 'Pages:' in info else 0
        subprocess.run(['pdftoppm', '-r', '110', '-jpeg', '-jpegopt', 'quality=80', p, os.path.join(pdir, 'p')])
        subprocess.run(['pdftotext', '-layout', p, os.path.join(W, 'text', code + '.txt')])
        rec['text_chars'] = len(open(os.path.join(W, 'text', code + '.txt'), errors='ignore').read().strip())
        # shrink giant phone-photo pages so agents can read them
        from PIL import Image
        for im in os.listdir(pdir):
            ip = os.path.join(pdir, im); I = Image.open(ip)
            if max(I.size) > 2200: I.thumbnail((1600, 2000)); I.save(ip, quality=85)
    elif ext in ('docx',):
        import docx
        d = docx.Document(p); out = []
        for para in d.paragraphs:
            s = ''
            for r in para.runs:
                t = r.text
                if not t: continue
                if r.font.highlight_color is not None: t = '==' + t + '=='
                if r.bold: t = '**' + t + '**'
                s += t
            if s.strip(): out.append(s)
        for tb in d.tables:
            for row in tb.rows: out.append(' | '.join(c.text for c in row.cells))
        open(os.path.join(W, 'text', code + '.md'), 'w').write('\n'.join(out))
        rec['pages'] = 0; rec['text_chars'] = sum(map(len, out))
    elif ext in ('jpg', 'jpeg', 'png', 'webp', 'heic'):
        shutil.copy(p, os.path.join(pdir, 'p-001.' + ext)); rec['pages'] = 1; rec['text_chars'] = 0
    else:
        rec['note'] = 'unsupported type, convert manually (e.g. libreoffice --headless --convert-to pdf)'
    inv.append(rec); print(rec)
json.dump(inv, open(os.path.join(W, 'inventory.json'), 'w'), indent=1)
print('files', len(inv), 'pages', sum(r.get('pages', 0) for r in inv))
