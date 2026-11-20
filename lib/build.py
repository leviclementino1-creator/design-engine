# -*- coding: utf-8 -*-
"""
design-engine / build.py - IR json -> .jsx -> the OPEN Photoshop or Illustrator -> check image -> parity against the preview.

    python lib/build.py scene.ir.json --app ps [--sheet out/scene_ps.jpg]
    python lib/build.py scene.ir.json --app ai [--sheet out/scene_ai.jpg]

Builds a NEW document in the app (it never touches, saves or closes yours, and never saves the new one). The app must already be
open: tools/run_jsx.ps1 refuses otherwise. After the build the runtime exports a check PNG; this file compares it with the Pillow
preview and prints PARITY (how alike they are) and ORDER (the layer tree the app reports against the IR).
"""
import argparse, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
import config, preview

RUNTIME = {"ps": "runtime_ps.jsx", "ai": "runtime_ai.jsx"}
PARITY_MIN = 97.0                      # % of pixels within TOL of the preview; below = the build is reported as different
TOL = 40                               # per-channel difference (0..255) still counted as the same pixel (anti-aliasing, hinting)


def build_jsx(ir, opt, app):
    tpl = open(os.path.join(HERE, RUNTIME[app]), encoding="utf-8").read()
    js = tpl.replace("__IR__", json.dumps(ir, ensure_ascii=True)).replace("__OPT__", json.dumps(opt, ensure_ascii=True))
    assert all(ord(c) < 128 for c in js), "jsx must be ASCII"
    return js


def ir_tree(layers, depth=0):
    out = []
    for L in layers:
        out.append("  " * depth + L["name"])
        if L["kind"] == "group": out += ir_tree(L["children"], depth + 1)
    return out


def run(ir_path, app, close=False):
    """-> (exit code of the dispatcher, log text, check png path)"""
    ir = json.load(open(ir_path, encoding="utf-8"))
    run_dir = config.cfg("run_dir").replace("\\", "/")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", ir["name"])[:40] + "_" + app
    jsx, log, chk = ["%s/%s.%s" % (run_dir, slug, e) for e in ("jsx", "log", "png")]
    if os.path.exists(chk): os.remove(chk)
    with open(jsx, "w", encoding="ascii", newline="\n") as f: f.write(build_jsx(ir, {"log": log, "chk": chk, "close": bool(close)}, app))
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", os.path.join(config.ROOT, "tools", "run_jsx.ps1"),
           "-App", app, "-Jsx", jsx.replace("/", "\\"), "-Log", log.replace("/", "\\"), "-Timeout", str(config.cfg("timeout"))]
    pid = config.cfg(app + "_progid")
    if pid: cmd += ["-ProgId", pid]
    if os.path.exists(log): os.remove(log)
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    text = out.stdout.strip()                          # the dispatcher's own lines (ABORT, COM) come through the console codepage
    if os.path.exists(log):                            # the script's log is UTF-8 on disk: read it there, not through the console
        text = open(log, encoding="utf-8", errors="replace").read().strip()
        text = "\n".join([l for l in out.stdout.splitlines() if l.startswith(("COM:", "ABORT", "NO LOG"))] + [text])
    return out.returncode, text, chk


def order_problem(ir, log_text):
    """None when the app's layer tree equals the IR (names and nesting, bottom -> top), else a line saying where it differs"""
    got = [l[5:] for l in log_text.splitlines() if l.startswith("TREE ")]
    want = ir_tree(ir["layers"])
    if got == want: return None
    for i in range(max(len(got), len(want))):
        g = got[i] if i < len(got) else "<nothing>"; w = want[i] if i < len(want) else "<nothing>"
        if g != w: return "layer %d: the app has %r, the IR has %r" % (i + 1, g.strip(), w.strip())


def parity(ir, chk):
    """-> (% of pixels alike, preview image, app image)"""
    from PIL import Image, ImageChops
    a = preview.render(ir)
    with Image.open(chk) as im:
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        b = Image.alpha_composite(bg, im.convert("RGBA")).convert("RGB")
    if b.size != a.size: b = b.resize(a.size, Image.LANCZOS)
    diff = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > TOL else 0)
    bad = diff.histogram()[255]
    return round(100.0 * (1 - bad / float(a.size[0] * a.size[1])), 2), a, b, diff


def sheet(a, b, diff, out_jpg, label):
    """preview | app | where they differ, side by side"""
    from PIL import Image, ImageDraw
    w = 800; h = max(1, int(round(a.size[1] * w / float(a.size[0]))))
    S = Image.new("RGB", (w * 3, h + 28), (20, 20, 20)); d = ImageDraw.Draw(S)
    red = Image.merge("RGB", (diff, Image.new("L", diff.size, 0), Image.new("L", diff.size, 0)))
    for i, (im, name) in enumerate(((a, "preview (Pillow)"), (b, label), (red, "difference"))):
        S.paste(im.resize((w, h), Image.LANCZOS), (i * w, 28)); d.text((i * w + 8, 8), name, fill=(240, 240, 240))
    os.makedirs(os.path.dirname(os.path.abspath(out_jpg)), exist_ok=True)
    S.save(out_jpg, quality=88); return out_jpg


def main(argv=None):
    ap = argparse.ArgumentParser(description="IR -> the open Photoshop / Illustrator, checked against the preview")
    ap.add_argument("ir"); ap.add_argument("--app", required=True, choices=["ps", "ai"]); ap.add_argument("--sheet")
    ap.add_argument("--close", action="store_true", help="close the document this build created, without saving (test runs)")
    a = ap.parse_args(argv)
    try: sys.stdout.reconfigure(errors="replace")
    except AttributeError: pass
    ir = json.load(open(a.ir, encoding="utf-8"))
    code, log, chk = run(a.ir, a.app, a.close)
    print(log)
    if code != 0: print("BUILD FAILED (exit %d)" % code); return code
    bad = order_problem(ir, log)
    print("ORDER " + ("OK" if not bad else "DIFFERENT - " + bad))
    if not os.path.exists(chk): print("PARITY not measured: the app wrote no check image"); return 1
    pct, pa, pb, diff = parity(ir, chk)
    print("PARITY %.2f%% (%s)" % (pct, "OK" if pct >= PARITY_MIN else "DIFFERENT, look at the sheet"))
    if a.sheet: print("sheet", sheet(pa, pb, diff, a.sheet, {"ps": "Photoshop", "ai": "Illustrator"}[a.app]))
    return 0 if (not bad and pct >= PARITY_MIN) else 1


if __name__ == "__main__":
    sys.exit(main())
