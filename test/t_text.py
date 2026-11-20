# -*- coding: utf-8 -*-
"""T text: the text helpers - fit_size (largest size that fits), wrap (word wrap to a width), kerning pairs (AV, To, LT),
tracking on the three alignments, two-line leading. Guides are drawn where the text must end."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
from engine import Doc, ACCENT, INK, PAPER, MUTED, fit_size, wrap


def scene():
    d = Doc("T text", 1280, 720, bg=PAPER)
    L, R, W = 100, 1180, 1080
    d.line("Guide left", (L, 40), (L, 680), stroke=ACCENT, stroke_w=2)
    d.line("Guide right", (R, 40), (R, 680), stroke=ACCENT, stroke_w=2)
    head = "AVATAR TO VALLEY"
    s = fit_size(head, W, hi=200)
    d.text("Fit", head, (L, 190), size=s, fill=INK, max_w=W)
    body = wrap("Kerning pairs come from the font file, so the width measured here is the width the app sets.", 700, "ArialMT", 34)
    d.text("Wrapped", body, (L, 280), size=34, font="ArialMT", fill=MUTED, leading=46, max_w=700)
    with d.group("Tracked"):
        d.text("Tracked left", "TRACKED 300", (L, 520), size=40, fill=INK, tracking=300)
        d.text("Tracked center", "TRACKED 300", ((L + R) / 2, 590), size=40, fill=INK, align="center", tracking=300)
        d.text("Tracked right", "TRACKED 300", (R, 660), size=40, fill=INK, align="right", tracking=300)
    return d


if __name__ == "__main__":
    out = os.path.join(HERE, "out"); os.makedirs(out, exist_ok=True)
    print(scene().save(os.path.join(out, "t_text.ir.json")))
