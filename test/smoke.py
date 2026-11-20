# -*- coding: utf-8 -*-
"""
design-engine / smoke.py - builds every core scene (test/t_*.py) inside the OPEN apps and reports order and parity.

    python test/smoke.py            # Photoshop and Illustrator, whichever is open
    python test/smoke.py ps         # only one

Each scene becomes a new document that is closed again without saving (only the document the run created). The sheets
(preview | app | difference) go to test/out/smoke_<scene>_<app>.jpg. Run it on your own app versions before a PR that
touches a runtime, and paste the summary.
"""
import glob, importlib.util, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
import build

OUT = os.path.join(HERE, "out")


def main(argv):
    apps = argv[1:] or ["ps", "ai"]; os.makedirs(OUT, exist_ok=True); rows = []; bad = 0
    for f in sorted(glob.glob(os.path.join(HERE, "t_*.py"))):
        name = os.path.basename(f)[:-3]
        spec = importlib.util.spec_from_file_location(name, f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        ir_path = m.scene().save(os.path.join(OUT, name + ".ir.json")); ir = json.load(open(ir_path, encoding="utf-8"))
        for app in apps:
            code, log, chk = build.run(ir_path, app, close=True)
            head = (log.splitlines() or ["?"])[0]
            if code == 2: rows.append((name, app, "SKIPPED (app not open)", "")); continue
            warn = [l for l in log.splitlines() if l.startswith(("WARN", "ERR", "COM:", "ABORT", "NO LOG"))]
            if code != 0 or not os.path.exists(chk): rows.append((name, app, "FAILED", "; ".join(warn) or head)); bad += 1; continue
            order = build.order_problem(ir, log); pct, a, b, diff = build.parity(ir, chk)
            build.sheet(a, b, diff, os.path.join(OUT, "smoke_%s_%s.jpg" % (name, app)), {"ps": "Photoshop", "ai": "Illustrator"}[app])
            ok = (not order) and pct >= build.PARITY_MIN
            bad += 0 if ok else 1
            rows.append((name, app, "%s  order %s  parity %.2f%%" % ("OK  " if ok else "DIFF", "ok" if not order else "DIFFERENT", pct),
                         "; ".join([head] + warn)))
    print("\n== smoke")
    for r in rows: print("%-10s %-3s %s   %s" % r)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
