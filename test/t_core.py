# -*- coding: utf-8 -*-
"""T core: every layer kind once - rect (sharp, rounded, stroked), ellipse, line, path, text (three aligns, tracking, two lines),
image, nested groups, opacity. The scene the smoke test and the IR regression lean on."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
from engine import Doc, ACCENT, INK, PAPER, MUTED, WHITE


def scene():
    d = Doc("T core", 1280, 720, bg=INK)
    d.rect("Panel", (60, 60, 560, 600), fill=PAPER, radius=28)
    d.rect("Frame", (680, 60, 540, 300), stroke=ACCENT, stroke_w=6, radius=16)
    d.rect("Bar", (680, 400, 540, 24), fill=MUTED)
    d.rect("Bar fill", (680, 400, 360, 24), fill=ACCENT)
    with d.group("Badge"):
        d.ellipse("Dot", (100, 100, 96, 96), fill=ACCENT)
        d.ellipse("Ring", (92, 92, 112, 112), stroke=INK, stroke_w=4)
        d.text("Number", "7", (148, 168), size=64, fill=INK, align="center")
    d.line("Rule", (100, 250), (580, 250), stroke=INK, stroke_w=4)
    d.path("Arrow", [(700, 480), (820, 480), (820, 450), (900, 510), (820, 570), (820, 540), (700, 540)], fill=WHITE)
    with d.group("Copy"):
        d.text("Title", "DESIGN AS DATA", (100, 340), size=52, fill=INK, max_w=480)
        d.text("Body", "One scene in Python,\nthree players.", (100, 410), size=30, font="ArialMT", fill=MUTED, leading=40)
        with d.group("Tags"):
            d.text("Tag left", "LEFT", (100, 600), size=22, fill=INK, tracking=200)
            d.text("Tag center", "CENTER", (340, 600), size=22, fill=INK, align="center", tracking=200)
            d.text("Tag right", "RIGHT", (580, 600), size=22, fill=INK, align="right", tracking=200)
    d.image("Swatch", os.path.join(HERE, "assets", "swatch.png"), (960, 440, 240, 200), fit="contain")
    d.rect("Veil", (680, 60, 540, 300), fill=ACCENT, radius=16, opacity=20)
    return d


if __name__ == "__main__":
    out = os.path.join(HERE, "out"); os.makedirs(out, exist_ok=True)
    print(scene().save(os.path.join(out, "t_core.ir.json")))
