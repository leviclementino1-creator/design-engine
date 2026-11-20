# -*- coding: utf-8 -*-
"""
design-engine / kerning.py - the pair kerning Photoshop ("Metrics") and Illustrator ("Auto") apply, read from the font file.

Pillow's basic layout ignores kerning, so a title measured with it comes out ~2% wider than the apps set it. This reads the
font's own pairs with fontTools: the GPOS 'kern' feature (PairPos formats 1 and 2, default script/language) when the font has
one, else the legacy 'kern' table. Values are in font units; pair(a, b) * size / upm = pixels.
Without fontTools the engine still works: every pair is 0 and `AVAILABLE` is False (measure() says so once).
"""
try:
    from fontTools.ttLib import TTFont
    AVAILABLE = True
except ImportError:                                   # pragma: no cover
    AVAILABLE = False

_CACHE = {}


class Kern:
    def __init__(self, path):
        self.upm, self.cmap, self.pairs, self.classes = 1000, {}, {}, []
        if not AVAILABLE: return
        f = TTFont(path, fontNumber=0, lazy=True)
        self.upm = f["head"].unitsPerEm
        self.cmap = f.getBestCmap() or {}
        if "GPOS" in f and self._gpos(f["GPOS"].table): return
        if "kern" in f:
            for t in f["kern"].kernTables:
                if getattr(t, "coverage", 1) & 1 or not hasattr(t, "coverage"):       # horizontal
                    for (a, b), v in t.kernTable.items(): self.pairs.setdefault((a, b), v)

    def _gpos(self, g):
        if not g.FeatureList or not g.LookupList: return False
        idx = []
        for fr in g.FeatureList.FeatureRecord:
            if fr.FeatureTag == "kern":
                for i in fr.Feature.LookupListIndex:
                    if i not in idx: idx.append(i)
        for i in idx:
            for st in g.LookupList.Lookup[i].SubTable:
                if type(st).__name__ == "ExtensionPos": st = st.ExtSubTable
                if type(st).__name__ != "PairPos": continue
                cov = st.Coverage.glyphs
                if st.Format == 1:
                    for a, ps in zip(cov, st.PairSet):
                        for r in ps.PairValueRecord:
                            v = r.Value1.XAdvance if r.Value1 is not None and hasattr(r.Value1, "XAdvance") else 0
                            if v: self.pairs.setdefault((a, r.SecondGlyph), v)
                elif st.Format == 2:
                    c1 = st.ClassDef1.classDefs if st.ClassDef1 else {}
                    c2 = st.ClassDef2.classDefs if st.ClassDef2 else {}
                    rows = [[(r.Value1.XAdvance if r.Value1 is not None and hasattr(r.Value1, "XAdvance") else 0)
                             for r in c.Class2Record] for c in st.Class1Record]
                    self.classes.append((set(cov), c1, c2, rows))
        return bool(self.pairs or self.classes)

    def units(self, a, b):
        ga, gb = self.cmap.get(ord(a)), self.cmap.get(ord(b))
        if ga is None or gb is None: return 0
        v = self.pairs.get((ga, gb))
        if v is not None: return v
        for cov, c1, c2, rows in self.classes:
            if ga in cov:
                v = rows[c1.get(ga, 0)][c2.get(gb, 0)]
                if v: return v
        return 0


def pair(font_path, a, b, size):
    """kerning between two characters, in px at this size"""
    k = _CACHE.get(font_path)
    if k is None: k = _CACHE[font_path] = Kern(font_path)
    return k.units(a, b) * size / float(k.upm)
