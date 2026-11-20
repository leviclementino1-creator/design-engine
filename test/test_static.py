# -*- coding: utf-8 -*-
"""
design-engine / test_static.py - everything that can be checked without an Adobe app.   python test/test_static.py

  - the runtimes are ES3 and ASCII (ExtendScript parses neither let/const, arrows, template strings nor Array.map/forEach)
  - a built .jsx is ASCII and node can parse it (when node is installed)
  - the engine's gates refuse what they must: overflow, bad colour, empty group, bad radius, missing image
  - kerning and tracking measure the way the apps set text
  - build.order_problem reads the layer tree of a log
"""
import json, os, re, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "lib")
sys.path.insert(0, LIB)
import build, engine, kerning
from engine import Doc, Overflow

FAIL = []


def check(name, ok, why=""):
    print(("ok   " if ok else "FAIL ") + name + ((" - " + why) if (why and not ok) else ""))
    if not ok: FAIL.append(name)


def refuses(name, fn, exc=ValueError):
    try: fn()
    except exc: check(name, True); return
    except Exception as e: check(name, False, "raised %r instead" % (e,)); return
    check(name, False, "nothing raised")


ES3_BANNED = [(r"\blet\s", "let"), (r"\bconst\s", "const"), (r"=>", "arrow function"), (r"`", "template string"),
              (r"\.(map|forEach|indexOf|filter|reduce)\(", "ES5 array method"), (r"\bJSON\.", "JSON object"),
              (r"\?[^:;\n]*:[^;\n]*\?[^;\n]*:", "chained ternary without parentheses")]


def strip_comments(js):
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    return re.sub(r"//[^\n]*", "", js)


for rt in ("runtime_ps.jsx", "runtime_ai.jsx"):
    src = open(os.path.join(LIB, rt), encoding="utf-8").read()
    check(rt + " is ASCII", all(ord(c) < 128 for c in src))
    code = re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', strip_comments(src))
    for pat, what in ES3_BANNED:
        m = re.search(pat, code)
        if what == "chained ternary without parentheses" and m and "(" in m.group(0): m = None      # a ? b : (c ? d : e) is fine
        check("%s has no %s" % (rt, what), m is None, m.group(0) if m else "")

d = Doc("unit", 400, 200, bg="#101010")
with d.group("G"):
    d.text("Word", "Ol\u00e1 mundo", (20, 100), size=40)
ir = d.ir()
for app, rt in build.RUNTIME.items():
    js = build.build_jsx(ir, {"log": "C:/x.log", "chk": "C:/x.png", "close": False}, app)
    check("built %s jsx is ASCII with a non-ASCII text" % app, all(ord(c) < 128 for c in js) and "__IR__" not in js)
    node = shutil.which("node")
    if node:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="ascii") as f: f.write(js); tmp = f.name
        r = subprocess.run([node, "--check", tmp], capture_output=True, text=True); os.remove(tmp)
        check("node parses the built %s jsx" % app, r.returncode == 0, r.stderr[:200])

refuses("text wider than max_w", lambda: Doc("o", 300, 100).text("T", "A VERY LONG TITLE", (0, 50), size=80, max_w=200), Overflow)
refuses("a word wider than the wrap width", lambda: engine.wrap("Extraordinarily", 40, size=60), Overflow)
refuses("bad colour", lambda: Doc("o", 10, 10, bg="#12345"))
refuses("colour out of 0..1", lambda: Doc("o", 10, 10, bg=[255, 0, 0]))
refuses("shape with no fill and no stroke", lambda: Doc("o", 10, 10).rect("R", (0, 0, 5, 5)))
refuses("radius larger than the box", lambda: Doc("o", 100, 100).rect("R", (0, 0, 20, 20), fill="#ffffff", radius=30))
refuses("box with no area", lambda: Doc("o", 100, 100).ellipse("E", (0, 0, 0, 20), fill="#ffffff"))
refuses("missing image", lambda: Doc("o", 100, 100).image("I", "nope.png", (0, 0, 10, 10)))
refuses("empty document", lambda: Doc("o", 100, 100).ir())


def _empty_group():
    e = Doc("o", 100, 100, bg="#000000")
    with e.group("Empty"): pass
    e.ir()


refuses("empty group", _empty_group)

x = Doc("ids", 100, 100); a = x.rect("Box", (0, 0, 10, 10), fill="#ffffff"); c = x.rect("Box", (0, 0, 10, 10), fill="#ffffff")
check("duplicate names get different ids", a["id"] != c["id"])
check("hex and 0..1 colours agree", engine.col("#FF8000") == engine.col([1, 0.502, 0]))

if kerning.AVAILABLE:
    plain = sum(engine.pil_font("Arial-BoldMT", 100).getlength(ch) for ch in "AVATAR")
    check("AVATAR is kerned tighter than its advances", engine.measure("AVATAR", "Arial-BoldMT", 100) < plain - 5)
else:
    print("skip kerning (fontTools not installed)")
w0 = engine.measure("ABCD", size=100); w1 = engine.measure("ABCD", size=100, tracking=100)
check("tracking is added between glyphs, not after the last", abs((w1 - w0) - 30.0) < 0.05, "%s" % (w1 - w0))
check("fit_size result fits", engine.measure("HELLO WORLD", size=engine.fit_size("HELLO WORLD", 500)) <= 500)
check("wrap keeps every line inside", all(engine.measure(l, size=40) <= 300 for l in engine.wrap("one two three four five six", 300, size=40).split("\n")))

log = "x\nTREE BG\nTREE G\nTREE   Word\ndone"
check("order_problem: same tree", build.order_problem(ir, log) is None)
check("order_problem: swapped tree", build.order_problem(ir, "TREE G\nTREE   Word\nTREE BG") is not None)

print("\n%s" % ("ALL OK" if not FAIL else "%d FAILED: %s" % (len(FAIL), ", ".join(FAIL))))
sys.exit(1 if FAIL else 0)
