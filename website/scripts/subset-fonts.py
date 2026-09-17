"""Optional asset regeneration: fontTools + brotli and Debian's fonts-noto-cjk.

Run after changing Chinese copy. The generated WOFF2 assets are committed so
normal builds and Cloudflare deploys do not depend on Python or system fonts.
"""
from pathlib import Path
from fontTools.ttLib import TTCollection
from fontTools import subset
import shutil

root = Path(__file__).resolve().parents[1]
text = ''.join(p.read_text() for p in (root / 'src').glob('*.mjs'))
text += ''.join(chr(i) for i in range(32, 127))
out = root / 'public/assets/fonts'
out.mkdir(parents=True, exist_ok=True)
for style in ['Regular', 'Medium', 'Bold']:
    collection = TTCollection(f'/usr/share/fonts/opentype/noto/NotoSansCJK-{style}.ttc')
    font = next(f for f in collection.fonts if f['name'].getDebugName(1).startswith('Noto Sans CJK SC'))
    options = subset.Options()
    options.flavor = 'woff2'
    options.name_IDs = ['*']
    options.name_legacy = True
    options.name_languages = ['*']
    sub = subset.Subsetter(options=options)
    sub.populate(text=text)
    sub.subset(font)
    # Give this website subset its own family name while keeping all license
    # and copyright metadata. Glyph outlines and metrics remain unmodified.
    for rec in font['name'].names:
        if rec.nameID in [1, 4, 6, 16]:
            value = f'AvenWebNoto-{style}' if rec.nameID == 6 else 'Aven Web Noto'
            rec.string = value.encode(rec.getEncoding())
    font.flavor = 'woff2'
    font.save(out / f'aven-noto-{style.lower()}.woff2')
    print(style, (out / f'aven-noto-{style.lower()}.woff2').stat().st_size, 'bytes')
shutil.copyfile('/usr/share/doc/fonts-noto-cjk/copyright', out / 'LICENSE.txt')
