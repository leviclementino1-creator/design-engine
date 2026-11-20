/*
 design-engine / runtime_ps.jsx - plays an IR inside the OPEN Photoshop. build.py fills __IR__ and __OPT__.

 Rules this file keeps (do not relax them):
  - ES3 and ASCII only: var, no arrow functions, no let/const, no template strings, no Array.map/forEach/indexOf, no JSON object.
  - Always a NEW document. It never touches, saves or closes a document that was already open, and never saves the new one:
    the only file it writes is the check PNG (a copy) and the log.
  - Ruler and type units are set to pixels for the build and put back in the finally.
  - A missing font is a WARN line and the app default, never an abort.
  - Every layer is placed explicitly (first child INSIDE its group, the next ones BEFORE the previous sibling): where Photoshop
    drops a new layer depends on what is selected, so the runtime never relies on it.
*/
var IR = __IR__;
var OPT = __OPT__;
var LOG = [];

function log(s) { LOG.push(String(s)); }
function flush() {
    var f = new File(OPT.log); f.encoding = "UTF-8"; f.lineFeed = "Unix";
    f.open("w"); f.write(LOG.join("\n") + "\n"); f.close();
}
function cid(s) { return charIDToTypeID(s); }
function sid(s) { return stringIDToTypeID(s); }
function rgbDesc(c) {
    var d = new ActionDescriptor();
    d.putDouble(cid("Rd  "), c[0] * 255); d.putDouble(cid("Grn "), c[1] * 255); d.putDouble(cid("Bl  "), c[2] * 255);
    return d;
}
function solid(c) {
    var s = new SolidColor(); s.rgb.red = c[0] * 255; s.rgb.green = c[1] * 255; s.rgb.blue = c[2] * 255; return s;
}
function pxv(d, key, v) { d.putUnitDouble(key, cid("#Pxl"), v); }

// a shape layer: shapeKey/shapeDesc = a live rectangle or ellipse; none = the selected work path becomes the vector mask
function contentLayer(L, shapeKey, shapeDesc) {
    var fill = L.fill, stroke = L.stroke;
    var d = new ActionDescriptor(), r = new ActionReference();
    r.putClass(sid("contentLayer")); d.putReference(cid("null"), r);
    var l = new ActionDescriptor(), c = new ActionDescriptor();
    c.putObject(cid("Clr "), cid("RGBC"), rgbDesc(fill ? fill : (stroke ? stroke : [0, 0, 0])));
    l.putObject(cid("Type"), sid("solidColorLayer"), c);
    if (shapeKey) { l.putObject(cid("Shp "), shapeKey, shapeDesc); }
    var ss = new ActionDescriptor();
    ss.putInteger(sid("strokeStyleVersion"), 2);
    ss.putBoolean(sid("strokeEnabled"), stroke ? true : false);
    ss.putBoolean(sid("fillEnabled"), fill ? true : false);
    pxv(ss, sid("strokeStyleLineWidth"), stroke ? L.stroke_w : 1);
    ss.putEnumerated(sid("strokeStyleLineAlignment"), sid("strokeStyleLineAlignment"), sid("strokeStyleAlignCenter"));
    var sc = new ActionDescriptor();
    sc.putObject(cid("Clr "), cid("RGBC"), rgbDesc(stroke ? stroke : [0, 0, 0]));
    ss.putObject(sid("strokeStyleContent"), sid("solidColorLayer"), sc);
    l.putObject(sid("strokeStyle"), sid("strokeStyle"), ss);
    d.putObject(cid("Usng"), sid("contentLayer"), l);
    executeAction(cid("Mk  "), d, DialogModes.NO);
    return app.activeDocument.activeLayer;
}

function workPath(doc, pts) {
    var arr = [], i, p;
    for (i = 0; i < pts.length; i++) {
        p = new PathPointInfo();
        p.kind = PointKind.CORNERPOINT;
        p.anchor = [pts[i][0], pts[i][1]]; p.leftDirection = p.anchor; p.rightDirection = p.anchor;
        arr.push(p);
    }
    var sp = new SubPathInfo();
    sp.operation = ShapeOperation.SHAPEADD; sp.closed = true; sp.entireSubPath = arr;
    var item = doc.pathItems.add("de_tmp", [sp]);
    item.select();
    return item;
}

function mkRect(doc, L) {
    var b = L.box, r = new ActionDescriptor();
    r.putInteger(sid("unitValueQuadVersion"), 1);
    pxv(r, cid("Top "), b[1]); pxv(r, cid("Left"), b[0]); pxv(r, cid("Btom"), b[1] + b[3]); pxv(r, cid("Rght"), b[0] + b[2]);
    pxv(r, sid("topRight"), L.radius); pxv(r, sid("topLeft"), L.radius);
    pxv(r, sid("bottomLeft"), L.radius); pxv(r, sid("bottomRight"), L.radius);
    return contentLayer(L, cid("Rctn"), r);
}
function mkEllipse(doc, L) {
    var b = L.box, r = new ActionDescriptor();
    pxv(r, cid("Top "), b[1]); pxv(r, cid("Left"), b[0]); pxv(r, cid("Btom"), b[1] + b[3]); pxv(r, cid("Rght"), b[0] + b[2]);
    return contentLayer(L, cid("Elps"), r);
}
function mkPath(doc, L) {
    var tmp = workPath(doc, L.points);
    var lyr = contentLayer(L, null, null);
    tmp.remove();
    return lyr;
}
// a line is a filled quad as wide as the stroke (butt caps): an open work path does not make a shape layer
function mkLine(doc, L) {
    var a = L.points[0], b = L.points[1];
    var dx = b[0] - a[0], dy = b[1] - a[1], n = Math.sqrt(dx * dx + dy * dy), h = L.stroke_w / 2;
    var ox = -dy / n * h, oy = dx / n * h;
    var tmp = workPath(doc, [[a[0] + ox, a[1] + oy], [b[0] + ox, b[1] + oy], [b[0] - ox, b[1] - oy], [a[0] - ox, a[1] - oy]]);
    var lyr = contentLayer({ fill: L.stroke, stroke: null, stroke_w: 0 }, null, null);
    tmp.remove();
    return lyr;
}
function mkText(doc, L) {
    var lyr = doc.artLayers.add();
    lyr.kind = LayerKind.TEXT;
    var t = lyr.textItem;
    t.kind = TextType.POINTTEXT;
    t.contents = L.text.split("\n").join("\r");
    try { t.font = L.font; if (t.font != L.font) { log("WARN font " + L.font + " not installed (layer " + L.name + "): Photoshop used " + t.font); } }
    catch (e) { log("WARN font " + L.font + " not installed (layer " + L.name + ")"); }
    t.size = new UnitValue(L.size, "px");
    t.color = solid(L.fill);
    t.justification = L.align == "center" ? Justification.CENTER : (L.align == "right" ? Justification.RIGHT : Justification.LEFT);
    t.tracking = L.tracking;
    t.useAutoLeading = false;
    t.leading = new UnitValue(L.leading, "px");
    t.position = [new UnitValue(L.pos[0], "px"), new UnitValue(L.pos[1], "px")];
    return lyr;
}
function mkImage(doc, L) {
    var f = new File(L.path);
    if (!f.exists) { log("WARN image missing, layer skipped: " + L.path); return null; }
    var d = new ActionDescriptor();
    d.putPath(cid("null"), f);
    d.putEnumerated(cid("FTcs"), cid("QCSt"), cid("Qcsa"));
    executeAction(cid("Plc "), d, DialogModes.NO);
    var lyr = doc.activeLayer, b = lyr.bounds;
    var bw = b[2].as("px") - b[0].as("px"), bh = b[3].as("px") - b[1].as("px");
    lyr.resize(L.box[2] / bw * 100, L.box[3] / bh * 100, AnchorPosition.TOPLEFT);
    b = lyr.bounds;
    lyr.translate(new UnitValue(L.box[0] - b[0].as("px"), "px"), new UnitValue(L.box[1] - b[1].as("px"), "px"));
    return lyr;
}

function buildInto(doc, parent, layers) {
    var prev = null, i, L, lyr;
    for (i = 0; i < layers.length; i++) {
        L = layers[i]; lyr = null;
        if (L.kind == "group") {
            lyr = (parent ? parent : doc).layerSets.add();
            if (prev) { lyr.move(prev, ElementPlacement.PLACEBEFORE); }
            lyr.name = L.name;
            buildInto(doc, lyr, L.children);
        } else {
            if (L.kind == "rect") { lyr = mkRect(doc, L); }
            else if (L.kind == "ellipse") { lyr = mkEllipse(doc, L); }
            else if (L.kind == "path") { lyr = mkPath(doc, L); }
            else if (L.kind == "line") { lyr = mkLine(doc, L); }
            else if (L.kind == "text") { lyr = mkText(doc, L); }
            else if (L.kind == "image") { lyr = mkImage(doc, L); }
            else { log("WARN unknown kind " + L.kind + " (layer " + L.name + ")"); }
            if (!lyr) { continue; }
            lyr.name = L.name;
            if (prev) { lyr.move(prev, ElementPlacement.PLACEBEFORE); }
            else if (parent) { lyr.move(parent, ElementPlacement.INSIDE); }
        }
        if (L.opacity < 100) { lyr.opacity = L.opacity; }
        prev = lyr;
    }
}

function tree(container, depth, out) {
    var i, l, pad = "";
    for (i = 0; i < depth; i++) { pad += "  "; }
    for (i = container.layers.length - 1; i >= 0; i--) {          // bottom -> top, the IR order
        l = container.layers[i];
        out.push("TREE " + pad + l.name);
        if (l.typename == "LayerSet") { tree(l, depth + 1, out); }
    }
}

(function () {
    var oldRuler = app.preferences.rulerUnits, oldType = app.preferences.typeUnits, oldDialogs = app.displayDialogs;
    try {
        app.preferences.rulerUnits = Units.PIXELS;
        app.preferences.typeUnits = TypeUnits.PIXELS;
        app.displayDialogs = DialogModes.NO;
        log("design-engine " + IR.engine + " / Photoshop " + app.version + " / " + IR.name);
        var doc = app.documents.add(new UnitValue(IR.w, "px"), new UnitValue(IR.h, "px"), 72, IR.name,
                                    NewDocumentMode.RGB, DocumentFill.TRANSPARENT);
        doc.artLayers[0].name = "de_tmp_first";                    // the empty layer a new document comes with
        buildInto(doc, null, IR.layers);
        // fetched again BY NAME: a layer reference taken before other layers were made is not safe to use after them
        // (Photoshop 28 already drops that empty layer when the first shape layer is made: not finding it is fine)
        try { if (doc.layers.length > 1) { doc.artLayers.getByName("de_tmp_first").remove(); } } catch (e0) { }
        var t = []; tree(doc, 0, t); log(t.join("\n"));
        if (OPT.chk) {
            doc.saveAs(new File(OPT.chk), new PNGSaveOptions(), true, Extension.LOWERCASE);
            log("check " + OPT.chk);
        }
        if (OPT.close) { doc.close(SaveOptions.DONOTSAVECHANGES); }  // only the document this run created (test runs)
        log("done");
    } catch (e) {
        log("ERR line " + e.line + ": " + e.message);
    } finally {
        app.preferences.rulerUnits = oldRuler; app.preferences.typeUnits = oldType; app.displayDialogs = oldDialogs;
        flush();
    }
})();
