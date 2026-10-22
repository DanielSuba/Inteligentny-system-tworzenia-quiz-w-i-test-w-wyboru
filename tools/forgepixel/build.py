# buduje font ForgePixel (TTF + WOFF) z glifow pikselowych
import sys
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

from glyphs import ACCENTED, CAPS, DIGITS, LOWER, PUNCT

PX = 100          # jeden piksel w jednostkach fontu
UPM = 1200        # 12 px na em
ASC, DESC = 10, 2  # piksele nad i pod linia bazowa

# domyslnie zapisuje do fontow frontendu
out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "frontend/src/assets/fonts"


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$ Zbieranie pikseli $$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

# zamienia wiersze na zbior pikseli (x, y)
def toPixels(top, rows):
    pts = set()
    for i, row in enumerate(rows):
        y = top - 1 - i
        for x, ch in enumerate(row):
            if ch == "#":
                pts.add((x, y))
    return pts, max(len(r) for r in rows)


# dodaje znak diakrytyczny do litery bazowej
def addMark(pts, w, top, mark):
    cx = w // 2
    res = set(pts)
    if mark == "acute":
        y = top + 1
        res |= {(cx, y), (cx + 1, y + 1)}
    elif mark == "dot":
        res.add((cx, top + 1))
    elif mark == "ogonek":
        res |= {(w - 2, -1), (w - 1, -2)}
    return res


glyphs = {}  # znak -> (piksele, szerokosc)

for ch, rows in {**CAPS, **DIGITS}.items():
    glyphs[ch] = toPixels(7, rows)
for ch, (top, rows) in {**LOWER, **PUNCT}.items():
    glyphs[ch] = toPixels(top, rows)
for ch, (base, mark) in ACCENTED.items():
    top = 7 if base.isupper() else 5
    pts, w = glyphs[base]
    glyphs[ch] = (addMark(pts, w, top, mark), w)


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$ Obrys z pikseli $$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

# laczy piksele w jeden obrys (wspolne krawedzie znikaja)
def outline(pts):
    edges = {}
    for x, y in pts:
        # kwadrat zgodnie z ruchem wskazowek zegara (zewnetrzny obrys w TrueType)
        sq = [(x, y), (x, y + 1), (x + 1, y + 1), (x + 1, y)]
        for i in range(4):
            a, b = sq[i], sq[(i + 1) % 4]
            if (b, a) in edges:
                del edges[(b, a)]
            else:
                edges[(a, b)] = True
    nxt = {}
    for a, b in edges:
        nxt.setdefault(a, []).append(b)
    loops = []
    while nxt:
        start = next(iter(nxt))
        loop, cur = [start], start
        while True:
            b = nxt[cur].pop()
            if not nxt[cur]:
                del nxt[cur]
            if b == start:
                break
            loop.append(b)
            cur = b
        # usuwa punkty lezace na prostej
        clean = []
        n = len(loop)
        for i in range(n):
            p, c, q = loop[i - 1], loop[i], loop[(i + 1) % n]
            if (c[0] - p[0]) * (q[1] - c[1]) != (c[1] - p[1]) * (q[0] - c[0]):
                clean.append(c)
        loops.append(clean)
    return loops


def drawGlyph(pts):
    pen = TTGlyphPen(None)
    for loop in outline(pts):
        pen.moveTo((loop[0][0] * PX, loop[0][1] * PX))
        for x, y in loop[1:]:
            pen.lineTo((x * PX, y * PX))
        pen.closePath()
    return pen.glyph()


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$$$ Zapis fontu $$$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

def build():
    order = [".notdef", "space"]
    cmap = {32: "space"}
    ttGlyphs = {".notdef": drawGlyph({(x, y) for x in range(4) for y in range(7) if x in (0, 3) or y in (0, 6)}),
                "space": TTGlyphPen(None).glyph()}
    metrics = {".notdef": (5 * PX, 0), "space": (4 * PX, 0)}

    for ch, (pts, w) in sorted(glyphs.items()):
        name = "uni%04X" % ord(ch)
        order.append(name)
        cmap[ord(ch)] = name
        ttGlyphs[name] = drawGlyph(pts)
        metrics[name] = ((w + 1) * PX, min(x for x, _ in pts) * PX)

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(ttGlyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASC * PX, descent=-DESC * PX)
    fb.setupNameTable({"familyName": "ForgePixel", "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=ASC * PX, sTypoDescender=-DESC * PX, sTypoLineGap=0,
                usWinAscent=ASC * PX, usWinDescent=DESC * PX, sxHeight=5 * PX, sCapHeight=7 * PX,
                fsSelection=0x40 | 0x80, version=4)
    fb.setupPost()
    out.mkdir(parents=True, exist_ok=True)
    fb.font.save(out / "ForgePixel.ttf")
    fb.font.flavor = "woff2"
    fb.font.save(out / "ForgePixel.woff2")
    print("glifow:", len(order), "| zapisano w:", out)


build()
