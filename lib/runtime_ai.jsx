/*
 design-engine / runtime_ai.jsx - plays an IR inside the OPEN Illustrator. build.py fills __IR__ and __OPT__.

 Rules this file keeps (do not relax them):
  - ES3 and ASCII only: var, no arrow functions, no let/const, no template strings, no Array.map/forEach/indexOf, no JSON object.
  - Always a NEW document. It never touches, saves or closes a document that was already open, and never saves the new one:
    the only file it writes is the check PNG (an export) and the log.
  - The IR is y-down from the top-left of the artboard; Illustrator is y-up. Every point goes through P().
  - New items land at the FRONT of their container, so building bottom -> top keeps the IR order.
  - A missing font is a WARN line and the app default, never an abort.
*/
var IR = __IR__;
var OPT = __OPT__;
var LOG = [];
var X0 = 0, Y0 = 0;

function log(s) { LOG.push(String(s)); }
function flush() {
    var f = new File(OPT.log); f.encoding = "UTF-8"; f.lineFeed = "Unix";
    f.open("w"); f.write(LOG.join("\n") + "\n"); f.close();
}
function P(x, y) { return [X0 + x, Y0 - y]; }
function rgb(c) {
    var k = new RGBColor(); k.red = c[0] * 255; k.green = c[1] * 255; k.blue = c[2] * 255; return k;
}
function paint(item, L) {
    if (L.fill) { item.filled = true; item.fillColor = rgb(L.fill); } else { item.filled = false; }
    if (L.stroke) { item.stroked = true; item.strokeColor = rgb(L.stroke); item.strokeWidth = L.stroke_w; } else { item.stroked = false; }
}
function pts(list) {
    var out = [], i;
    for (i = 0; i < list.length; i++) { out.push(P(list[i][0], list[i][1])); }
    return out;
}

function mkText(box, L) {
    var t = box.textFrames.pointText(P(L.pos[0], L.pos[1]));
    t.contents = L.text.split("\n").join("\r");
    var ca = t.textRange.characterAttributes;
    try { ca.textFont = app.textFonts.getByName(L.font); }
    catch (e) { log("WARN font " + L.font + " not installed (layer " + L.name + ")"); }
    ca.size = L.size;
    ca.fillColor = rgb(L.fill);
    ca.tracking = L.tracking;
    ca.autoLeading = false;
    ca.leading = L.leading;
    t.textRange.paragraphAttributes.justification =
        L.align == "center" ? Justification.CENTER : (L.align == "right" ? Justification.RIGHT : Justification.LEFT);
    return t;
}
function mkImage(box, L) {
    var f = new File(L.path);
    if (!f.exists) { log("WARN image missing, layer skipped: " + L.path); return null; }
    var it = box.placedItems.add();
    it.file = f;
    it.width = L.box[2]; it.height = L.box[3];
    it.position = P(L.box[0], L.box[1]);
    return it;
}

function buildInto(box, layers) {
    var i, L, it, b, p;
    for (i = 0; i < layers.length; i++) {
        L = layers[i]; it = null; b = L.box;
        if (L.kind == "group") { it = box.groupItems.add(); it.name = L.name; buildInto(it, L.children); }
        else if (L.kind == "rect") {
            p = P(b[0], b[1]);
            it = L.radius > 0 ? box.pathItems.roundedRectangle(p[1], p[0], b[2], b[3], L.radius, L.radius)
                              : box.pathItems.rectangle(p[1], p[0], b[2], b[3]);
            paint(it, L);
        }
        else if (L.kind == "ellipse") { p = P(b[0], b[1]); it = box.pathItems.ellipse(p[1], p[0], b[2], b[3]); paint(it, L); }
        else if (L.kind == "path") { it = box.pathItems.add(); it.setEntirePath(pts(L.points)); it.closed = true; paint(it, L); }
        else if (L.kind == "line") {
            it = box.pathItems.add(); it.setEntirePath(pts(L.points)); it.closed = false;
            paint(it, { fill: null, stroke: L.stroke, stroke_w: L.stroke_w });
        }
        else if (L.kind == "text") { it = mkText(box, L); }
        else if (L.kind == "image") { it = mkImage(box, L); }
        else { log("WARN unknown kind " + L.kind + " (layer " + L.name + ")"); }
        if (!it) { continue; }
        it.name = L.name;
        if (L.opacity < 100) { it.opacity = L.opacity; }
    }
}

function tree(box, depth, out) {
    var i, it, pad = "";
    for (i = 0; i < depth; i++) { pad += "  "; }
    for (i = box.pageItems.length - 1; i >= 0; i--) {             // bottom -> top, the IR order
        it = box.pageItems[i];
        if (it.parent != box) { continue; }                       // pageItems of a layer also lists the grandchildren
        out.push("TREE " + pad + it.name);
        if (it.typename == "GroupItem") { tree(it, depth + 1, out); }
    }
}

(function () {
    var oldLevel = app.userInteractionLevel;
    try {
        app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;
        log("design-engine " + IR.engine + " / Illustrator " + app.version + " / " + IR.name);
        var doc = app.documents.add(DocumentColorSpace.RGB, IR.w, IR.h);
        var ab = doc.artboards[0].artboardRect;                   // [left, top, right, bottom]
        X0 = ab[0]; Y0 = ab[1];
        var layer = doc.layers[0];
        layer.name = IR.name;
        buildInto(layer, IR.layers);
        var t = []; tree(layer, 0, t); log(t.join("\n"));
        if (OPT.chk) {
            var o = new ExportOptionsPNG24();
            o.artBoardClipping = true; o.antiAliasing = true; o.transparency = false;
            o.horizontalScale = 100; o.verticalScale = 100;
            doc.exportFile(new File(OPT.chk), ExportType.PNG24, o);
            log("check " + OPT.chk);
        }
        if (OPT.close) { doc.close(SaveOptions.DONOTSAVECHANGES); }  // only the document this run created (test runs)
        log("done");
    } catch (e) {
        log("ERR line " + e.line + ": " + e.message);
    } finally {
        app.userInteractionLevel = oldLevel;
        flush();
    }
})();
