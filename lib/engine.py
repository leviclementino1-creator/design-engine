# -*- coding: utf-8 -*-
"""
design-engine / engine.py - a static design written as DATA.

A Doc is a list of layers (the IR). The same list is played three times:
  preview.py        -> a PNG drawn with Pillow (the approval mock, no Adobe app needed)
  runtime_ps.jsx    -> an editable, layered document inside the OPEN Photoshop
  runtime_ai.jsx    -> an editable vector document inside the OPEN Illustrator

Coordinates are pixels, origin top-left, y down. Layers are listed bottom -> top (paint order).
Text is anchored on its BASELINE: (x, y) is the baseline start (align left), middle (center) or end (right).
Colours are "#RRGGBB" or [r, g, b] in 0..1; the IR always stores 0..1.

    from engine import Doc, ACCENT, INK, PAPER
    d = Doc("Thumb", 1920, 1080, bg=INK)
    d.rect("Card", (120, 120, 800, 400), fill=PAPER, radius=32)
    d.text("Title", "WHOEVER TALKS NEXT", (160, 320), size=96, fill=INK, max_w=720)
    d.save("thumb.ir.json")
"""
import json, os, re
import config, kerning

ENGINE = 1


class Overflow(ValueError):
    """text wider than the box it was promised to fit (the 'does it fit' gate)"""


def col(c):
    """'#RRGGBB' or [r, g, b] (0..1) -> [r, g, b] rounded; None stays None"""
    if c is None: return None
    if isinstance(c, str):
        m = re.fullmatch(r"#?([0-9a-fA-F]{6})", c.strip())
        if not m: raise ValueError("colour %r is not #RRGGBB" % (c,))
        h = m.group(1); return [round(int(h[i:i + 2], 16) / 255.0, 4) for i in (0, 2, 4)]
    c = list(c)
    if len(c) != 3 or not all(0 <= float(v) <= 1 for v in c): raise ValueError("colour %r is not three values in 0..1" % (c,))
    return [round(float(v), 4) for v in c]


ACCENT = col(config.b("ACCENT", "#52B8FF"))
INK = col(config.b("INK", "#0E1116"))
PAPER = col(config.b("PAPER", "#F4F1EA"))
MUTED = col(config.b("MUTED", "#737882"))
WHITE = [1.0, 1.0, 1.0]
BLACK = [0.0, 0.0, 0.0]

_FONTS = {}


def font_file(ps_name):
    f = (config.b("FONT_FILES", {}) or {}).get(ps_name)
    if not f or not os.path.exists(f):
        raise ValueError("font %r has no file in the brand's FONT_FILES (needed to measure and preview text)" % ps_name)
    return f


def pil_font(ps_name, size):
    from PIL import ImageFont
    k = (ps_name, round(float(size), 3))
    if k not in _FONTS: _FONTS[k] = ImageFont.truetype(font_file(ps_name), k[1])
    return _FONTS[k]


def layout(text, font=None, size=48, tracking=0):
    """ONE line set the way Photoshop and Illustrator set it -> ([x of each glyph], width in px).
    Pair kerning comes from the font file (kerning.py); tracking (1/1000 em) goes BETWEEN glyphs: the apps do not count the
    space after the last one when they align or measure, so a tracked right-aligned word ends exactly on its anchor."""
    font = font or config.b("FONT_DISPLAY", "Arial-BoldMT")
    f = pil_font(font, size); path = font_file(font); step = tracking * size / 1000.0
    xs, x = [], 0.0
    for i, ch in enumerate(text):
        xs.append(x); x += f.getlength(ch)
        if i < len(text) - 1: x += kerning.pair(path, ch, text[i + 1], size) + step
    return xs, x


def measure(text, font=None, size=48, tracking=0):
    """width in px of ONE line (see layout)"""
    return round(layout(text, font, size, tracking)[1], 2)


def fit_size(text, max_w, font=None, hi=400, lo=8, tracking=0):
    """the largest whole size at which the widest line fits max_w"""
    lines = text.split("\n")
    for s in range(int(hi), int(lo) - 1, -1):
        if max(measure(l, font, s, tracking) for l in lines) <= max_w: return s
    raise Overflow("%r does not fit %spx even at size %s" % (text, max_w, lo))


def wrap(text, max_w, font=None, size=48, tracking=0):
    """greedy word wrap -> text with '\\n'; a single word wider than max_w raises Overflow"""
    out, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if measure(t, font, size, tracking) <= max_w: cur = t; continue
        if not cur: raise Overflow("the word %r is wider than %spx at size %s" % (word, max_w, size))
        out.append(cur); cur = word
        if measure(cur, font, size, tracking) > max_w: raise Overflow("the word %r is wider than %spx at size %s" % (word, max_w, size))
    if cur: out.append(cur)
    return "\n".join(out)


class Doc:
    def __init__(self, name, w, h, bg=None):
        self.name, self.w, self.h = name, int(w), int(h)
        self.layers = []
        self._stack = [self.layers]
        self._ids = set()
        if bg is not None: self.rect("BG", (0, 0, self.w, self.h), fill=bg)

    # ---- plumbing
    def _id(self, name):
        base = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "layer"; i, s = 2, base
        while s in self._ids: s = "%s_%d" % (base, i); i += 1
        self._ids.add(s); return s

    def _add(self, kind, name, opacity, **kw):
        if not 0 <= opacity <= 100: raise ValueError("opacity %r is not 0..100" % (opacity,))
        L = {"id": self._id(name), "kind": kind, "name": name, "opacity": opacity}
        L.update(kw); self._stack[-1].append(L); return L

    @staticmethod
    def _paint(fill, stroke, stroke_w):
        if fill is None and stroke is None: raise ValueError("a shape needs a fill or a stroke")
        if stroke is not None and stroke_w <= 0: raise ValueError("a stroke needs stroke_w > 0")
        return {"fill": col(fill), "stroke": col(stroke), "stroke_w": float(stroke_w) if stroke is not None else 0.0}

    @staticmethod
    def _box(box):
        x, y, w, h = [round(float(v), 3) for v in box]
        if w <= 0 or h <= 0: raise ValueError("box %r has no area" % (box,))
        return [x, y, w, h]

    # ---- layers
    def rect(self, name, box, fill=None, radius=0, stroke=None, stroke_w=0, opacity=100):
        b = self._box(box)
        if radius < 0 or radius > min(b[2], b[3]) / 2.0: raise ValueError("radius %s does not fit a %sx%s box" % (radius, b[2], b[3]))
        return self._add("rect", name, opacity, box=b, radius=float(radius), **self._paint(fill, stroke, stroke_w))

    def ellipse(self, name, box, fill=None, stroke=None, stroke_w=0, opacity=100):
        return self._add("ellipse", name, opacity, box=self._box(box), **self._paint(fill, stroke, stroke_w))

    def line(self, name, p1, p2, stroke, stroke_w=4, opacity=100):
        if stroke_w <= 0: raise ValueError("a line needs stroke_w > 0")
        pts = [[round(float(v), 3) for v in p] for p in (p1, p2)]
        if pts[0] == pts[1]: raise ValueError("a line needs two different points")
        return self._add("line", name, opacity, points=pts, stroke=col(stroke), stroke_w=float(stroke_w))

    def path(self, name, points, fill=None, stroke=None, stroke_w=0, opacity=100):
        """a closed straight-sided polygon"""
        pts = [[round(float(v), 3) for v in p] for p in points]
        if len(pts) < 3: raise ValueError("a path needs at least 3 points")
        return self._add("path", name, opacity, points=pts, **self._paint(fill, stroke, stroke_w))

    def text(self, name, text, pos, size=48, font=None, fill=None, align="left", tracking=0, leading=None, max_w=None, opacity=100):
        """point text on its baseline. '\\n' breaks lines (leading = px between baselines, default 1.2 x size).
        max_w: the width this text was promised to fit; wider = Overflow here, not a surprise inside the app."""
        if align not in ("left", "center", "right"): raise ValueError("align %r is not left/center/right" % (align,))
        if not text.strip(): raise ValueError("empty text")
        font = font or config.b("FONT_DISPLAY", "Arial-BoldMT")
        size = float(size); leading = float(leading) if leading else round(size * 1.2, 3)
        widths = [measure(l, font, size, tracking) for l in text.split("\n")]
        if max_w is not None and max(widths) > max_w:
            raise Overflow("text %r is %.0fpx wide at size %g, the box is %gpx (use fit_size or wrap)" % (name, max(widths), size, max_w))
        return self._add("text", name, opacity, text=text, pos=[round(float(pos[0]), 3), round(float(pos[1]), 3)], size=size, font=font,
                         fill=col(fill if fill is not None else WHITE), align=align, tracking=int(tracking), leading=leading,
                         width=max(widths))

    def image(self, name, path, box, fit="stretch", opacity=100):
        """a placed file. fit: 'stretch' fills the box; 'contain' keeps the aspect and centres inside the box."""
        if not os.path.exists(path): raise ValueError("image not found: %s" % path)
        x, y, w, h = self._box(box)
        if fit == "contain":
            from PIL import Image
            with Image.open(path) as im: iw, ih = im.size
            k = min(w / iw, h / ih); nw, nh = round(iw * k, 3), round(ih * k, 3)
            x, y, w, h = round(x + (w - nw) / 2, 3), round(y + (h - nh) / 2, 3), nw, nh
        elif fit != "stretch": raise ValueError("fit %r is not stretch/contain" % (fit,))
        return self._add("image", name, opacity, path=os.path.abspath(path).replace("\\", "/"), box=[x, y, w, h])

    def group(self, name, opacity=100):
        """with d.group("Header"): ...   (a layer group in Photoshop, a group in Illustrator)"""
        return _Group(self, self._add("group", name, opacity, children=[]))

    # ---- output
    def ir(self):
        def check(ls):
            for L in ls:
                if L["kind"] == "group":
                    if not L["children"]: raise ValueError("group %r is empty" % L["name"])
                    check(L["children"])
        if not self.layers: raise ValueError("the document has no layers")
        check(self.layers)
        return {"engine": ENGINE, "name": self.name, "w": self.w, "h": self.h, "layers": self.layers}

    def save(self, path):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(self.ir(), f, ensure_ascii=False, indent=1, sort_keys=True)
        return path


class _Group:
    def __init__(self, doc, layer): self.doc, self.layer = doc, layer
    def __enter__(self): self.doc._stack.append(self.layer["children"]); return self.layer
    def __exit__(self, *a): self.doc._stack.pop(); return False
