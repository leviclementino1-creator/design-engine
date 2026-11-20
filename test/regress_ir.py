# -*- coding: utf-8 -*-
"""
design-engine / regress_ir.py - old scenes must keep writing the same IR.

    python test/regress_ir.py write   test/regress_base_demo.json     # after an INTENDED change (say why in the CHANGELOG)
    python test/regress_ir.py compare test/regress_base_demo.json     # before every commit; prints REGRESSION: NONE (identical)

Every test/t_*.py exposes scene() -> Doc. Image paths are reduced to the file name (the baseline must not know the machine).
Text widths are measured from the font file: a different Arial version shows up as a width difference in text layers only.
"""
import glob, hashlib, importlib.util, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))


def _norm(layers):
    for L in layers:
        if "path" in L: L["path"] = os.path.basename(L["path"])
        if L["kind"] == "group": _norm(L["children"])


def scenes():
    out = {}
    for f in sorted(glob.glob(os.path.join(HERE, "t_*.py"))):
        spec = importlib.util.spec_from_file_location(os.path.basename(f)[:-3], f)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        ir = json.loads(json.dumps(m.scene().ir())); _norm(ir["layers"])
        out[os.path.basename(f)] = ir
    return out


def digest(ir):
    return hashlib.sha256(json.dumps(ir, sort_keys=True, ensure_ascii=True).encode("ascii")).hexdigest()[:16]


def flat(layers, pre=""):
    for L in layers:
        yield pre + L["id"], {k: v for k, v in L.items() if k != "children"}
        if L["kind"] == "group": yield from flat(L["children"], pre + L["id"] + "/")


def main(argv):
    if len(argv) != 3 or argv[1] not in ("write", "compare"): sys.exit(__doc__)
    now = scenes()
    if argv[1] == "write":
        with open(argv[2], "w", encoding="utf-8", newline="\n") as f: json.dump(now, f, indent=1, sort_keys=True)
        print("baseline written: %d scenes" % len(now)); return 0
    base = json.load(open(argv[2], encoding="utf-8")); bad = 0
    for name in sorted(set(base) | set(now)):
        if name not in now: print("MISSING scene", name); bad += 1; continue
        if name not in base: print("NEW scene (not in the baseline)", name); bad += 1; continue
        if digest(base[name]) == digest(now[name]): continue
        bad += 1; a, c = dict(flat(base[name]["layers"])), dict(flat(now[name]["layers"]))
        for k in sorted(set(a) | set(c)):
            if a.get(k) != c.get(k):
                keys = sorted(x for x in set(a.get(k) or {}) | set(c.get(k) or {}) if (a.get(k) or {}).get(x) != (c.get(k) or {}).get(x))
                print("CHANGED %s  %s  %s" % (name, k, ", ".join(keys)))
    print("REGRESSION: NONE (identical)" if not bad else "REGRESSION: %d scene(s) differ" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
