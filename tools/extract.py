#!/usr/bin/env python3
"""课件抽取：PDF / PPTX / PPT / KEY(先转 PDF) → 逐页文本 + 页面图 + 覆盖清单骨架。

用法：python3 extract.py <输出目录> <文件1> [文件2 ...] [--dpi 70] [--ocr]
输出：
  <out>/<文件序号>_<短名>/pages/p001.txt      每页文本（pdftotext -layout；PPTX 含表格与演讲者备注）
  <out>/<文件序号>_<短名>/img/p-<页码>.png    每页缩略图（位数随总页数补零，如 p-01 / p-001；用 ls 查看实际文件名）
  <out>/inventory.md                          覆盖清单骨架：每页一行，写网页时逐页勾选
  <out>/summary.json                          页数、低文字页（需看图）、疑似公式页
"""
import json, os, re, shutil, subprocess, sys

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def to_pdf(path, outdir):
    """PPT/PPTX/KEY/DOC 等用 LibreOffice 转 PDF，用于逐页渲染。"""
    exe = shutil.which('soffice') or shutil.which('libreoffice')
    if not exe:
        return None
    r = run([exe, '--headless', '--convert-to', 'pdf', '--outdir', outdir, path], timeout=600)
    pdf = os.path.join(outdir, os.path.splitext(os.path.basename(path))[0] + '.pdf')
    return pdf if os.path.exists(pdf) else None

def pdf_pages(pdf):
    r = run(['pdfinfo', pdf]); m = re.search(r'Pages:\s+(\d+)', r.stdout)
    return int(m.group(1)) if m else 0

def pdf_text(pdf, n, pages_dir):
    texts = []
    for i in range(1, n + 1):
        r = run(['pdftotext', '-layout', '-f', str(i), '-l', str(i), pdf, '-'])
        t = r.stdout.replace('\f', '').rstrip()
        texts.append(t)
        open(os.path.join(pages_dir, f'p{i:03d}.txt'), 'w', encoding='utf-8').write(t)
    return texts

def pptx_text(path, pages_dir):
    from pptx import Presentation
    prs = Presentation(path); texts = []
    for i, slide in enumerate(prs.slides, 1):
        parts = []
        for shp in slide.shapes:
            if getattr(shp, 'has_text_frame', False) and shp.has_text_frame:
                s = '\n'.join(p.text for p in shp.text_frame.paragraphs if p.text.strip())
                if s.strip(): parts.append(s)
            if getattr(shp, 'has_table', False) and shp.has_table:
                rows = [' | '.join(c.text.strip() for c in r.cells) for r in shp.table.rows]
                parts.append('[表格]\n' + '\n'.join(rows))
            if shp.shape_type == 13:
                parts.append('[图片]')
        if slide.has_notes_slide:
            note = slide.notes_slide.notes_text_frame.text.strip()
            if note: parts.append('[演讲者备注]\n' + note)
        t = '\n\n'.join(parts); texts.append(t)
        open(os.path.join(pages_dir, f'p{i:03d}.txt'), 'w', encoding='utf-8').write(t)
    return texts

def render(pdf, img_dir, dpi):
    run(['pdftoppm', '-r', str(dpi), '-png', pdf, os.path.join(img_dir, 'p')], timeout=1200)

def ocr_pages(img_dir, texts, pages_dir):
    try:
        import pytesseract
        from PIL import Image
    except Exception:
        return texts
    langs = pytesseract.get_languages(config='')
    lang = '+'.join([l for l in ('chi_sim', 'eng') if l in langs]) or 'eng'
    imgs = sorted(f for f in os.listdir(img_dir) if f.endswith('.png'))
    for k, f in enumerate(imgs):
        if k < len(texts) and len(texts[k].strip()) < 20:
            t = pytesseract.image_to_string(Image.open(os.path.join(img_dir, f)), lang=lang)
            texts[k] = '[OCR]\n' + t
            open(os.path.join(pages_dir, f'p{k+1:03d}.txt'), 'w', encoding='utf-8').write(texts[k])
    return texts

MATH = re.compile(r'[=∫∑√≤≥≈→⇒∞αβγδεζηθλμξπσφωΔΦΩ]|\b(lim|sin|cos|exp|log)\b|[a-zA-Z]\s*\(\s*[a-zA-Z]\s*\)')

def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__); sys.exit(1)
    dpi = 70; ocr = False
    if '--dpi' in args:
        k = args.index('--dpi'); dpi = int(args[k + 1]); del args[k:k + 2]
    if '--ocr' in args:
        args.remove('--ocr'); ocr = True
    out, files = args[0], args[1:]
    os.makedirs(out, exist_ok=True)
    inv = ['# 覆盖清单（逐页勾选：已写入网页的位置 / 合并说明 / 勘误 / 拓展）', '',
           '状态：☐ 未处理  ☑ 已写入  ⊕ 已合并到其他页  ✎ 有勘误  ＋ 有拓展', '']
    summary = []
    for fi, path in enumerate(files, 1):
        name = re.sub(r'[^\w\u4e00-\u9fff]+', '_', os.path.splitext(os.path.basename(path))[0])[:24]
        d = os.path.join(out, f'{fi:02d}_{name}'); pages_dir = os.path.join(d, 'pages'); img_dir = os.path.join(d, 'img')
        os.makedirs(pages_dir, exist_ok=True); os.makedirs(img_dir, exist_ok=True)
        ext = os.path.splitext(path)[1].lower()
        if ext == '.pdf':
            pdf = path; n = pdf_pages(pdf); texts = pdf_text(pdf, n, pages_dir)
        else:
            texts = pptx_text(path, pages_dir) if ext == '.pptx' else []
            pdf = to_pdf(path, d)
            if pdf and not texts:
                texts = pdf_text(pdf, pdf_pages(pdf), pages_dir)
        if pdf:
            render(pdf, img_dir, dpi)
        if ocr and pdf:
            texts = ocr_pages(img_dir, texts, pages_dir)
        low = [i + 1 for i, t in enumerate(texts) if len(re.sub(r'\s', '', t)) < 40]
        mathy = [i + 1 for i, t in enumerate(texts) if len(MATH.findall(t)) >= 3]
        summary.append({'file': path, 'dir': d, 'pages': len(texts), 'low_text_pages': low, 'math_pages': mathy, 'pdf_for_images': pdf})
        inv += [f'## 文件 {fi}：{os.path.basename(path)}（{len(texts)} 页）', '']
        for i, t in enumerate(texts, 1):
            first = next((l.strip() for l in t.splitlines() if l.strip()), '（无文字）')[:40]
            flags = ('｜看图' if i in low else '') + ('｜公式' if i in mathy else '')
            inv.append(f'- ☐ P{i:03d} {first}{flags} → 网页位置：')
        inv.append('')
    open(os.path.join(out, 'inventory.md'), 'w', encoding='utf-8').write('\n'.join(inv))
    json.dump(summary, open(os.path.join(out, 'summary.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for s in summary:
        print(f"{s['file']}: {s['pages']} 页；低文字页 {len(s['low_text_pages'])}；疑似公式页 {len(s['math_pages'])} → {s['dir']}")

if __name__ == '__main__':
    main()
