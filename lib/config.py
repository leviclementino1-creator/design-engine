# -*- coding: utf-8 -*-
"""
design-engine / config.py - the one place that knows about this machine and about the active client.

Three sources, later wins:
  1. SETTINGS below                        - neutral defaults
  2. config.local.json at the repo root    - this machine (never committed; start from config.example.json)
  3. DE_<KEY> environment variables        - one run (DE_BRAND=demo python ...)

The client lives in brands/<brand>/brand.py (palette, fonts). The core asks cfg("key") and b("NAME", default) and never
writes a client value or a machine path in lib/.
"""
import json, os, runpy, tempfile

LIB = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(LIB)

SETTINGS = {
    "brand": "demo",                                              # folder name under brands_dir
    "brands_dir": os.path.join(ROOT, "brands"),                   # a private pack may live outside the repo
    "ps_progid": "",                                              # Photoshop COM id ("" = the release, then the Beta)
    "ai_progid": "",                                              # Illustrator COM id ("" = Illustrator.Application)
    "run_dir": os.path.join(tempfile.gettempdir(), "de_run"),     # generated .jsx, logs, check images
    "timeout": 180,                                               # seconds one build may take
}


class _State:
    values = None
    brand = None


def _values():
    if _State.values is None:
        v = dict(SETTINGS)
        local = os.environ.get("DE_CONFIG", os.path.join(ROOT, "config.local.json"))
        if os.path.isfile(local):
            with open(local, encoding="utf-8") as fh:
                for key, val in json.load(fh).items():
                    if key in v and val not in (None, ""): v[key] = val
        for key in v:
            env = os.environ.get("DE_" + key.upper())
            if env: v[key] = env
        os.makedirs(v["run_dir"], exist_ok=True)
        _State.values = v
    return _State.values


def cfg(key):
    """one machine setting"""
    return _values()[key]


def brand():
    """the active brand pack as a dict of its UPPERCASE names (+ NAME and DIR)"""
    if _State.brand is None:
        name = cfg("brand"); folder = os.path.join(cfg("brands_dir"), name); path = os.path.join(folder, "brand.py")
        if not os.path.isfile(path):
            raise SystemExit("design-engine: no brand pack %r (%s). Set \"brand\" in config.local.json or DE_BRAND." % (name, path))
        pack = {k: v for k, v in runpy.run_path(path).items() if k.isupper()}
        pack["NAME"], pack["DIR"] = name, folder
        _State.brand = pack
    return _State.brand


def b(name, default=None):
    """one brand value; a pack only defines what it changes"""
    return brand().get(name, default)
