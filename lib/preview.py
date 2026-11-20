# -*- coding: utf-8 -*-
"""
design-engine / preview.py - IR json -> PNG drawn with Pillow. The approval mock: no Adobe app needed.

    python lib/preview.py scene.ir.json out.png

Drawn at 3x and scaled down (anti-aliasing). Strokes are centred on the outline, as in Photoshop and Illustrator.
"""
import json, os, sys
from PIL import Image, ImageDraw
import engine

SS = 3


def _rgba(c, a=255):
    return (int(round(c[0] * 255)), int(round(c[1] * 255)), int(round(c[2] * 255)), a)


def _text(d, L):
    f = engine.pil_font(L["font"], L["size"] * SS)
    x0, y0 = L["pos"][0] * SS, L["pos"][1] * SS
    for i, line in enumerate(L["text"].split("\n")):
        y = y0 + i * L["leading"] * SS
        xs, w = engine.layout(line, L["font"], L["size"] * SS, L["tracking"])     # glyph by glyph: kerning and tracking as the apps
        x = x0 if L["align"] == "left" else (x0 - w / 2.0 if L["align"] == "center" else x0 - w)
        for ch, dx in zip(line, xs):
            if ch != " ": d.text((x + dx, y), ch, font=f, fill=_rgba(L["fill"]), anchor="ls")


def _shape(d, L):
    sw = L.get("stroke_w", 0) * SS; fill = L.get("fill"); stroke = L.get("stroke")
    if L["kind"] == "line":
        (x1, y1), (x2, y2) = L["points"]
        d.line((x1 * SS, y1 * SS, x2 * SS, y2 * SS), fill=_rgba(L["stroke"]), width=max(1, int(round(sw)))); return
    if L["kind"] == "path":
        pts = [(x * SS, y * SS) for x, y in L["points"]]
        if fill: d.polygon(pts, fill=_rgba(fill))
        if stroke: d.line(pts + [pts[0], pts[1]], fill=_rgba(stroke), width=max(1, int(round(sw))), joint="curve")
        return
    x, y, w, h = [v * SS for v in L["box"]]; r = L.get("radius", 0) * SS

    def draw(box, rad, **kw):
        if L["kind"] == "ellipse": d.ellipse(box, **kw)
        elif rad > 0: d.rounded_rectangle(box, radius=rad, **kw)
        else: d.rectangle(box, **kw)
    if fill: draw((x, y, x + w - 1, y + h - 1), r, fill=_rgba(fill))
    if stroke:                                            # outline grows inwards from the box: push the box out by half the stroke
        o = sw / 2.0
        draw((x - o, y - o, x + w - 1 + o, y + h - 1 + o), r + o if r > 0 else 0, outline=_rgba(stroke), width=max(1, int(round(sw))))


def _render(layers, size):
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    for L in layers:
        if L["kind"] == "group": lay = _render(L["children"], size)
        else:
            lay = Image.new("RGBA", size, (0, 0, 0, 0))
            if L["kind"] == "image":
                x, y, w, h = L["box"]
                with Image.open(L["path"]) as im:
                    im = im.convert("RGBA").resize((max(1, int(round(w * SS))), max(1, int(round(h * SS)))), Image.LANCZOS)
                lay.paste(im, (int(round(x * SS)), int(round(y * SS))))
            elif L["kind"] == "text": _text(ImageDraw.Draw(lay), L)
            else: _shape(ImageDraw.Draw(lay), L)
        if L["opacity"] < 100:
            a = lay.getchannel("A").point(lambda v, k=L["opacity"] / 100.0: int(v * k)); lay.putalpha(a)
        out = Image.alpha_composite(out, lay)
    return out


def render(ir, flat=True):
    """IR dict -> PIL image at the document size. flat = on white, as the apps export an empty canvas"""
    big = _render(ir["layers"], (ir["w"] * SS, ir["h"] * SS))
    im = big.resize((ir["w"], ir["h"]), Image.LANCZOS)
    if not flat: return im
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    return Image.alpha_composite(bg, im).convert("RGB")


def save(ir_path, out_png):
    ir = json.load(open(ir_path, encoding="utf-8"))
    os.makedirs(os.path.dirname(os.path.abspath(out_png)), exist_ok=True)
    render(ir).save(out_png); return out_png


if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit("usage: python lib/preview.py scene.ir.json out.png")
    print("preview", save(sys.argv[1], sys.argv[2]))
