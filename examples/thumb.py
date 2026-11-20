# -*- coding: utf-8 -*-
"""A YouTube thumbnail (1280x720) written as data. Run it, look at the preview, then send it to the open app:

    python examples/thumb.py
    python lib/build.py examples/out/thumb.ir.json --app ps --sheet examples/out/thumb_ps.jpg
    python lib/build.py examples/out/thumb.ir.json --app ai --sheet examples/out/thumb_ai.jpg
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
from engine import Doc, ACCENT, INK, PAPER, MUTED, fit_size
import preview

TITLE = "WHOEVER TALKS\nNEXT, BUYS."
KICKER = "NEGOTIATION / 03"

d = Doc("Thumb", 1280, 720, bg=INK)
d.rect("Accent band", (0, 0, 28, 720), fill=ACCENT)
with d.group("Card"):
    d.rect("Card bg", (88, 96, 760, 528), fill=PAPER, radius=36)
    d.text("Kicker", KICKER, (136, 176), size=26, fill=MUTED, tracking=180, max_w=664)
    s = fit_size(TITLE, 664, hi=120)                      # the largest size at which the widest line fits the card
    d.text("Title", TITLE, (136, 300), size=s, fill=INK, leading=s * 1.08, max_w=664)
    d.line("Rule", (136, 470), (396, 470), stroke=ACCENT, stroke_w=8)
    d.text("Note", "Silence is a move.", (136, 550), size=34, font="ArialMT", fill=MUTED, max_w=664)
with d.group("Mark"):
    d.ellipse("Halo", (910, 190, 340, 340), fill=ACCENT, opacity=18)
    d.ellipse("Disc", (950, 230, 260, 260), fill=ACCENT)
    d.path("Play", [(1045, 300), (1045, 420), (1150, 360)], fill=INK)

out = os.path.join(HERE, "out"); os.makedirs(out, exist_ok=True)
ir = d.save(os.path.join(out, "thumb.ir.json"))
print(ir); print(preview.save(ir, os.path.join(out, "thumb_preview.png")))
