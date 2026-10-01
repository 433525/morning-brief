"""Subset bundled OFL fonts to common Chinese; native fallback covers the rest."""
from pathlib import Path
from fontTools import subset

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT/'my-entry/morning-brief/bundle/fonts'
SOURCE = ROOT/'.local-tools/font-original'
SOURCE.mkdir(exist_ok=True)
characters = set(range(0x20,0x250)) | set(range(0x2000,0x2070)) | set(range(0x3000,0x3040)) | set(range(0xff00,0xfff0))
for first in range(0xa1,0xf8):
    for second in range(0xa1,0xff):
        try: characters.add(ord(bytes([first,second]).decode('gb2312')))
        except UnicodeDecodeError: pass
characters.update(map(ord,(ROOT/'my-entry/morning-brief/bundle/main.splash').read_text(encoding='utf-8')))
for filename in ['NotoSansSC-Regular.otf','NotoSansSC-Bold.otf']:
    original = SOURCE/filename
    if not original.exists(): original.write_bytes((FONTS/filename).read_bytes())
    options = subset.Options()
    options.hinting = False
    font = subset.load_font(original,options)
    worker = subset.Subsetter(options=options)
    worker.populate(unicodes=characters)
    worker.subset(font)
    subset.save_font(font,FONTS/filename,options)
    print(filename,(FONTS/filename).stat().st_size)
