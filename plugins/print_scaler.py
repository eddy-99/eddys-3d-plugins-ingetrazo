# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Print Scaler for IngeTrazo
# Copyright (C) 2026 Phillip Edwards (Eddy)
# Written with the help of AI (Claude).
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
# It is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the LICENSE file or <https://www.gnu.org/licenses/> for details.

"""
3D Print Scaler - scale a model down (or up) to a chosen scale for 3D printing, for IngeTrazo
Pick a scale (1:50, 1:100 ...), see the printed size, check it against your print bed.
"""

import os
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QDoubleSpinBox, QCheckBox,
    QComboBox, QDialogButtonBox, QMessageBox, QLabel
)

PLUGIN_NAME = "3D Print Scaler"

SCALE_PRESETS = [1, 2, 5, 10, 20, 25, 50, 75, 100, 125, 150, 200, 250, 500, 1000]
UNITS = [("Metres (m)", 1000.0, "m"), ("Centimetres (cm)", 10.0, "cm"), ("Millimetres (mm)", 1.0, "mm")]
PIVOTS = [("Bottom centre (stays on the print bed)", "bottom"),
          ("Centre of the object", "centre"),
          ("Lowest corner", "corner"),
          ("World origin (0, 0, 0)", "origin")]
MODES = [("Export scaled - STL, 3MF, OBJ, PLY (full detail)", "stl"),
         ("Scale a copy (keep the original)", "copy"),
         ("Scale in place", "inplace")]

# IngeTrazo treats points closer than this as the same point (its weld tolerance, metres):
# a model scaled down so far that its details are smaller than this loses faces in IngeTrazo.
# Exporting scaled keeps every detail, because the scaling is done outside the model.
WELD = 1e-4

DEFAULTS = {'denominator': 50.0, 'pivot': 'bottom', 'mode': 'stl', 'unit': None,
            'check_bed': True, 'bed_x': 220.0, 'bed_y': 220.0, 'bed_z': 250.0}

COPY_GAP = 0.1   # gap between original and copy, as a fraction of the original's width


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def vertex_to_vector3d(v):
    """Returns the vertex position as a QVector3D, or None if it can't be read."""
    if isinstance(v, QVector3D):
        return QVector3D(v.x(), v.y(), v.z())
    for get in (lambda: (v.x(), v.y(), v.z()),
                lambda: (v.x, v.y, v.z),
                lambda: (v[0], v[1], v[2]),
                lambda: (v.pos.x(), v.pos.y(), v.pos.z()),
                lambda: (v.position.x(), v.position.y(), v.position.z())):
        try:
            x, y, z = get()
            return QVector3D(float(x), float(y), float(z))
        except Exception:
            pass
    return None


class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))


def _items(x):
    if x is None:
        return []
    if isinstance(x, dict):
        return list(x.values())
    try:
        return list(x)
    except Exception:
        return []


def _is_face(e):
    return hasattr(e, 'loop') or 'face' in type(e).__name__.lower()


def _is_group(e):
    return (not _is_face(e)) and getattr(e, 'mesh', None) is not None


def _meshes_of(e, out, seen):
    """Collect the meshes of a group, including nested groups."""
    m = getattr(e, 'mesh', None)
    if m is not None and id(m) not in seen:
        seen.add(id(m))
        out.append(m)
    for ch in _items(getattr(e, 'groups', None)) + _items(getattr(e, 'children', None)):
        if getattr(ch, 'mesh', None) is not None:
            _meshes_of(ch, out, seen)


def _face_vertices(f):
    vs = list(_items(getattr(f, 'vertices', None)))
    for hole in _items(getattr(f, 'holes', None)):
        vs.extend(_items(hole))
    return vs


def collect(entities):
    """Returns (unique vertices, unique faces, meshes touched) for the selection.
    Vertices whose position can't be read are left out."""
    verts, faces, meshes = [], [], []
    vseen, fseen, mseen = set(), set(), set()

    def add_v(v):
        if id(v) not in vseen:
            vseen.add(id(v))
            if vertex_to_vector3d(v) is not None:
                verts.append(v)

    def add_f(f):
        if id(f) in fseen:
            return
        fseen.add(id(f))
        faces.append(f)
        for v in _face_vertices(f):
            add_v(v)

    for e in entities:
        if _is_group(e):
            ms = []
            _meshes_of(e, ms, mseen)
            for m in ms:
                meshes.append(m)
                for v in _items(getattr(m, 'vertices', None)):
                    add_v(v)
                for f in _items(getattr(m, 'faces', None)):
                    add_f(f)
        elif _is_face(e):
            add_f(e)
        else:
            vs = [getattr(e, a) for a in ('v1', 'v2', 'a', 'b', 'start', 'end')
                  if getattr(e, a, None) is not None]
            vs += _items(getattr(e, 'vertices', None))
            if vs:
                for v in vs:
                    add_v(v)
            else:
                add_v(e)
    return verts, faces, meshes


def world_loops(entities):
    """The selection's faces in world space, as [(outer [QVector3D], [holes], face)]: component
    instances and moved groups come through their placement (as IngeTrazo's own STL export
    does), so a copy or an STL comes out where - and the way round - the object really is."""
    out = []
    seen = set()
    try:
        from core.group import world_mesh
    except Exception:
        world_mesh = None

    def pos(v):
        return vertex_to_vector3d(v)

    def add(f):
        if id(f) in seen:
            return
        seen.add(id(f))
        outer = [pos(v) for v in _items(getattr(f, 'vertices', None))]
        if len(outer) < 3 or any(q is None for q in outer):
            return
        holes = []
        for h in _items(getattr(f, 'holes', None)):
            hl = [pos(v) for v in _items(h)]
            if len(hl) >= 3 and all(q is not None for q in hl):
                holes.append(hl)
        out.append((outer, holes, f))
    for e in entities:
        if _is_group(e):
            m = None
            if world_mesh is not None:
                try:
                    m = world_mesh(e)
                except Exception:
                    m = None
            if m is None:
                ms = []
                _meshes_of(e, ms, set())
                for m_ in ms:
                    for f in _items(getattr(m_, 'faces', None)):
                        add(f)
            else:
                for f in _items(getattr(m, 'faces', None)):
                    add(f)
        elif _is_face(e):
            add(e)
    return out


def loops_bounds(loops):
    pts = [q for o, hs, _ in loops for q in o]
    lo = QVector3D(min(q.x() for q in pts), min(q.y() for q in pts), min(q.z() for q in pts))
    hi = QVector3D(max(q.x() for q in pts), max(q.y() for q in pts), max(q.z() for q in pts))
    return lo, hi


def face_triangles(face):
    """A face's triangles (world space), as IngeTrazo's own STL export makes them."""
    try:
        from formats.meshexport import export_triangles
        return list(export_triangles(face))
    except Exception:
        pass
    try:
        return list(face.triangulate())
    except Exception:
        return []


def write_stl(path, tris, name="scaled"):
    """A binary STL: tris = [((x, y, z), (x, y, z), (x, y, z))] in mm."""
    import struct
    with open(path, "wb") as fh:
        head = ("IngeTrazo %s - %s" % (PLUGIN_NAME, name)).encode("ascii", "replace")[:80]
        fh.write(head + b" " * (80 - len(head)))
        fh.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            L = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
            fh.write(struct.pack("<12fH", nx / L, ny / L, nz / L, *a, *b, *c, 0))


def weld(tris, decimals=6):
    """Shared corners for formats that list vertices once (3MF, OBJ, PLY): (points, triangles
    as index triples). Points are welded only where they are the same to a millionth of a mm, so
    nothing small is merged."""
    pts, idx, out = [], {}, []
    for t in tris:
        tri = []
        for c in t:
            k = (round(c[0], decimals), round(c[1], decimals), round(c[2], decimals))
            if k not in idx:
                idx[k] = len(pts)
                pts.append(c)
            tri.append(idx[k])
        if len(set(tri)) == 3:
            out.append(tuple(tri))
    return pts, out


def write_stl_ascii(path, tris, name="scaled"):
    with open(path, "w", encoding="ascii", errors="replace") as fh:
        fh.write("solid %s\n" % name.replace(" ", "_"))
        for a, b, c in tris:
            ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            L = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
            fh.write(" facet normal %.6e %.6e %.6e\n  outer loop\n" % (nx / L, ny / L, nz / L))
            for q in (a, b, c):
                fh.write("   vertex %.9g %.9g %.9g\n" % q)
            fh.write("  endloop\n endfacet\n")
        fh.write("endsolid %s\n" % name.replace(" ", "_"))


def write_obj(path, tris, name="scaled"):
    pts, faces = weld(tris)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# %s - %s (millimetres)\n" % (PLUGIN_NAME, name))
        fh.write("o %s\n" % name.replace(" ", "_"))
        for q in pts:
            fh.write("v %.9g %.9g %.9g\n" % q)
        for a, b, c in faces:
            fh.write("f %d %d %d\n" % (a + 1, b + 1, c + 1))


def write_ply(path, tris, name="scaled"):
    import struct
    pts, faces = weld(tris)
    with open(path, "wb") as fh:
        fh.write(("ply\nformat binary_little_endian 1.0\ncomment %s - %s (millimetres)\n"
                  "element vertex %d\nproperty float x\nproperty float y\nproperty float z\n"
                  "element face %d\nproperty list uchar int vertex_indices\nend_header\n"
                  % (PLUGIN_NAME, name, len(pts), len(faces))).encode("ascii", "replace"))
        for q in pts:
            fh.write(struct.pack("<3f", *q))
        for f in faces:
            fh.write(struct.pack("<B3i", 3, *f))


def write_3mf(path, tris, name="scaled"):
    """A 3MF (what PrusaSlicer, Bambu, Cura ... like best): one object, units millimetres."""
    import zipfile
    from xml.sax.saxutils import escape
    pts, faces = weld(tris)
    vs = "".join('<vertex x="%.9g" y="%.9g" z="%.9g"/>' % q for q in pts)
    ts = "".join('<triangle v1="%d" v2="%d" v3="%d"/>' % f for f in faces)
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             '<metadata name="Application">IngeTrazo %s</metadata>'
             '<resources><object id="1" name="%s" type="model"><mesh><vertices>%s</vertices>'
             '<triangles>%s</triangles></mesh></object></resources>'
             '<build><item objectid="1"/></build></model>' % (escape(PLUGIN_NAME), escape(name), vs, ts))
    types = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
             '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)


# file types offered when saving: (label shown in the save box, extension, writer)
EXPORTS = [("STL - binary (*.stl)", ".stl", write_stl),
           ("3MF - PrusaSlicer, Bambu, Cura (*.3mf)", ".3mf", write_3mf),
           ("OBJ - Rhino, ZBrush, Blender (*.obj)", ".obj", write_obj),
           ("PLY (*.ply)", ".ply", write_ply),
           ("STL - text / ASCII (*.stl)", ".stl", write_stl_ascii)]


def bounds(verts):
    pts = [p for p in (vertex_to_vector3d(v) for v in verts) if p is not None]
    if not pts:
        raise RuntimeError("Could not read the position of any selected vertex.")
    lo = QVector3D(min(p.x() for p in pts), min(p.y() for p in pts), min(p.z() for p in pts))
    hi = QVector3D(max(p.x() for p in pts), max(p.y() for p in pts), max(p.z() for p in pts))
    return lo, hi


def pivot_point(kind, lo, hi):
    if kind == "origin":
        return QVector3D(0, 0, 0)
    if kind == "corner":
        return QVector3D(lo.x(), lo.y(), lo.z())
    if kind == "centre":
        return QVector3D((lo.x() + hi.x()) / 2, (lo.y() + hi.y()) / 2, (lo.z() + hi.z()) / 2)
    return QVector3D((lo.x() + hi.x()) / 2, (lo.y() + hi.y()) / 2, lo.z())   # bottom centre


def set_vertex(v, p):
    """Moves a vertex to p using whichever mechanism the vertex object supports.
    Returns True only if the vertex is verifiably at p afterwards."""
    x, y, z = p.x(), p.y(), p.z()
    attempts = []
    if isinstance(v, QVector3D):
        attempts.append(lambda: (v.setX(x), v.setY(y), v.setZ(z)))
    for name in ('pos', 'position', 'co'):
        if hasattr(v, name):
            attempts.append(lambda n=name: setattr(v, n, QVector3D(x, y, z)))
            attempts.append(lambda n=name: getattr(v, n).setX(x) or getattr(v, n).setY(y) or getattr(v, n).setZ(z))
    if all(hasattr(v, a) and not callable(getattr(v, a)) for a in 'xyz'):
        attempts.append(lambda: (setattr(v, 'x', x), setattr(v, 'y', y), setattr(v, 'z', z)))
    if callable(getattr(v, 'set', None)):
        attempts.append(lambda: v.set(x, y, z))
    tol = 1e-6 * (1.0 + abs(x) + abs(y) + abs(z))
    for attempt in attempts:
        try:
            attempt()
        except Exception:
            continue
        q = vertex_to_vector3d(v)
        if q is not None and abs(q.x() - x) < tol and abs(q.y() - y) < tol and abs(q.z() - z) < tol:
            return True
    return False


def refresh_meshes(meshes):
    for m in meshes:
        for name in ('recompute_normals', 'update_normals', 'rebuild', 'invalidate'):
            fn = getattr(m, name, None)
            if callable(fn):
                try:
                    fn()
                except Exception:
                    pass


def guess_unit(size):
    """IngeTrazo stores models in metres. Only something over 500 'metres' long is taken to be a
    model that came in from millimetres without being converted."""
    return "m" if max(size) < 500.0 else "mm"


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------


# --- Eddy's 3D plugins: hover help and remembered window places (begin) ---
import os
# The same in each of the plugins. Every box, tick and button gets a pop-up note when
# you hover over it, and each window opens where (and at the size) you last left it.
EDDY_PLACES_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_eddy_windows.json")
EDDY_COMMON_TIPS = {
    "preset": "Ready-made settings. Pick one and the whole window is filled in. Your own "
              "presets are in the list too.",
    "save": "Updates the preset you have open (no typing). For a new preset, use Save as.",
    "save as...": "Saves everything in this window as a new preset, under a name you type.",
    "delete": "Deletes the preset you have open (your own presets only).",
    "folder": "Opens the folder your presets are saved in.",
    "open folder": "Opens the folder your presets are saved in.",
    "close": "Closes this window. Next time it opens in the same place, at the same size.",
    "random seed": "Change this for a different random pattern.",
    "seed": "Change this for a different random pattern.",
}


def _eddy_key(text):
    import re
    t = (text or "").replace("&", " ")                # "Step && head" = "Step & head"
    t = t.split("\t")[0].strip()
    t = re.sub(r"^[A-Z]{1,2}\s{2,}", "", t)          # "A   Height" -> "Height"
    t = t.strip().rstrip(":").strip()
    return " ".join(t.split()).lower()


def eddy_tips(root, tips=None):
    """Gives every label, box, tick, button and tab in the window its pop-up note:
    from the plugin's own list, matched by the words on it (or '@name' for a box with
    no words of its own). Anything that already has a note keeps it."""
    from PySide6.QtWidgets import (QLabel, QAbstractButton, QGroupBox, QTabWidget,
                                   QFormLayout, QBoxLayout, QLayout)
    table = dict(EDDY_COMMON_TIPS)
    table.update({_eddy_key(k): v for k, v in (tips or {}).items() if not k.startswith("@")})

    def tip_for(text):
        return table.get(_eddy_key(text))

    def give(w, t):
        try:
            if w is not None and t and not w.toolTip():
                w.setToolTip(t)
        except Exception:
            pass
    for k, v in (tips or {}).items():
        if k.startswith("@"):
            w = getattr(root, k[1:], None)
            for one in (w if isinstance(w, (list, tuple)) else [w]):
                give(one, v)
    for lab in root.findChildren(QLabel):
        t = tip_for(lab.text()) or lab.toolTip()
        if t:
            give(lab, t)
            try:
                give(lab.buddy(), t)
            except Exception:
                pass
    for b in root.findChildren(QAbstractButton):
        give(b, tip_for(b.text()))
    for g in root.findChildren(QGroupBox):
        give(g, tip_for(g.title()))
    for tw in root.findChildren(QTabWidget):
        for i in range(tw.count()):
            t = tip_for(tw.tabText(i))
            if t and not tw.tabToolTip(i):
                tw.setTabToolTip(i, t)
    # a label and the box it names share one note (form rows, and 'Label: [box]' rows)
    try:
        lrole, frole = QFormLayout.ItemRole.LabelRole, QFormLayout.ItemRole.FieldRole
    except AttributeError:
        lrole, frole = QFormLayout.LabelRole, QFormLayout.FieldRole
    for lay in root.findChildren(QLayout):
        try:
            if isinstance(lay, QFormLayout):
                for r in range(lay.rowCount()):
                    li, fi = lay.itemAt(r, lrole), lay.itemAt(r, frole)
                    lw = li.widget() if li is not None else None
                    fw = fi.widget() if fi is not None else None
                    if isinstance(lw, QLabel) and fw is not None:
                        give(fw, lw.toolTip())
                        give(lw, fw.toolTip())
            elif isinstance(lay, QBoxLayout):
                ws = [lay.itemAt(i).widget() for i in range(lay.count())]
                for a, b in zip(ws, ws[1:]):
                    if isinstance(a, QLabel) and b is not None and not isinstance(b, QLabel):
                        give(b, a.toolTip())
                        give(a, b.toolTip())
        except Exception:
            pass


def _eddy_places():
    import json
    try:
        with open(EDDY_PLACES_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def eddy_place(dlg, key):
    """Opens the window where it was last left (if that's still on a screen), and
    keeps note of where it's moved to, so you can stack the windows as you like."""
    from PySide6.QtCore import QObject, QEvent, QTimer, QPoint
    from PySide6.QtGui import QGuiApplication
    if getattr(dlg, "_eddy_place", None) is not None:
        return
    g = _eddy_places().get(key)
    if g:
        try:
            x, y, w, h = [int(v) for v in g[:4]]
            if QGuiApplication.screenAt(QPoint(x + 60, y + 15)) is not None:
                if w > 50 and h > 50:
                    dlg.resize(w, h)
                dlg.move(x, y)
        except Exception:
            pass

    class _Keeper(QObject):
        shown = False

        def eventFilter(self, obj, ev):
            try:
                t = ev.type()
                if t == QEvent.Type.Show:
                    self.shown = True
                elif t in (QEvent.Type.Move, QEvent.Type.Resize):
                    if self.shown:
                        self.timer.start(500)
                elif t in (QEvent.Type.Hide, QEvent.Type.Close):
                    self.save()
            except Exception:
                pass
            return False

        def save(self):
            import json
            if not self.shown:
                return
            try:
                p = dlg.pos()
                d = _eddy_places()
                d[key] = [p.x(), p.y(), dlg.width(), dlg.height()]
                with open(EDDY_PLACES_FILE, "w", encoding="utf-8") as f:
                    json.dump(d, f, indent=1)
            except Exception:
                pass
    k = _Keeper(dlg)
    k.timer = QTimer(k)
    k.timer.setSingleShot(True)
    k.timer.timeout.connect(k.save)
    dlg.installEventFilter(k)
    dlg._eddy_place = k


def eddy_window(dlg, key, tips=None, place=True):
    """Pop-up notes on everything in the window, and the window back where you left it."""
    try:
        eddy_tips(dlg, tips)
    except Exception:
        pass
    if place:
        try:
            eddy_place(dlg, key)
        except Exception:
            pass
# --- Eddy's 3D plugins: hover help and remembered window places (end) ---

EDDY_TIPS = {'Scale': 'The scale to print at, e.g. 1 : 80.',
 'Custom scale': "Your own scale: pick 'Custom...' above, then type it here.",
 'Scale about': 'The point that stays put while the model shrinks.',
 'Mode': 'Export scaled: writes the scaled model straight to a file in mm - STL, 3MF, OBJ or '
         'PLY - every detail kept (best for printing small scales). Scale a copy: a scaled '
         'copy beside the original. Scale in place: the model itself. IngeTrazo merges points '
         'closer than 0.1 mm, so very small details can be lost in a copy or in place - the '
         'STL keeps them.',
 'Check against print bed (mm)': "Warns you if the scaled model won't fit on your print bed.",
 '@bed': 'Your print bed size in mm: width, depth and height.'}
EDDY_TIPS_END = None


def _mm(x):
    """A size in mm, with enough figures to read: 1234, 12.3, 0.20, 0.0057."""
    a = abs(x)
    if a >= 100:
        return "%.0f" % x
    if a >= 1:
        return "%.1f" % x
    if a >= 0.01:
        return "%.2f" % x
    return "%.2g" % x


class ScaleDialog(QDialog):
    def __init__(self, cur, size, unit_key, count_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(PLUGIN_NAME)
        self.size = size
        lay = QVBoxLayout(self)
        form = QFormLayout()

        lbl_sel = QLabel(count_text)

        self.cb_scale = QComboBox()
        for d in SCALE_PRESETS:
            self.cb_scale.addItem("1 : %d" % d, float(d))
        self.cb_scale.addItem("Custom...", None)
        idx = self.cb_scale.count() - 1
        for i in range(self.cb_scale.count() - 1):
            if abs(self.cb_scale.itemData(i) - cur['denominator']) < 1e-9:
                idx = i
        self.cb_scale.setCurrentIndex(idx)

        self.sp_custom = QDoubleSpinBox()
        self.sp_custom.setDecimals(3)
        self.sp_custom.setRange(0.001, 1000000.0)
        self.sp_custom.setValue(cur['denominator'])
        self.sp_custom.setPrefix("1 : ")

        self.cb_unit = QComboBox()
        for label, mm, key in UNITS:
            self.cb_unit.addItem(label, mm)
            if key == unit_key:
                self.cb_unit.setCurrentIndex(self.cb_unit.count() - 1)
        self.unit_guessed = True
        self.cb_unit.setToolTip("IngeTrazo keeps every model in metres, whatever units it shows you, so "
                                "this is nearly always Metres. Only change it for a model that came in 1000 "
                                "times too big (an STL in millimetres imported as metres).")

        self.cb_pivot = QComboBox()
        for label, key in PIVOTS:
            self.cb_pivot.addItem(label, key)
            if key == cur['pivot']:
                self.cb_pivot.setCurrentIndex(self.cb_pivot.count() - 1)

        self.cb_mode = QComboBox()
        for label, key in MODES:
            self.cb_mode.addItem(label, key)
            if key == cur['mode']:
                self.cb_mode.setCurrentIndex(self.cb_mode.count() - 1)

        self.cb_bed = QCheckBox("Check against print bed (mm)")
        self.cb_bed.setChecked(cur['check_bed'])
        self.bed = []
        bed_row = QHBoxLayout()
        for key, axis in (('bed_x', 'X'), ('bed_y', 'Y'), ('bed_z', 'Z')):
            s = QDoubleSpinBox()
            s.setRange(1.0, 100000.0)
            s.setDecimals(1)
            s.setPrefix(axis + " ")
            s.setSuffix(" mm")
            s.setValue(cur[key])
            self.bed.append(s)
            bed_row.addWidget(s)

        self.lbl_info = QLabel()
        self.lbl_info.setWordWrap(True)

        form.addRow(lbl_sel)
        form.addRow("Scale:", self.cb_scale)
        form.addRow("   Custom scale:", self.sp_custom)
        form.addRow("Model's units:", self.cb_unit)
        form.addRow("Scale about:", self.cb_pivot)
        form.addRow("Mode:", self.cb_mode)
        form.addRow(self.cb_bed)
        form.addRow("   Bed size:", bed_row)
        form.addRow(self.lbl_info)
        lay.addLayout(form)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

        for w in (self.cb_scale, self.cb_unit, self.cb_bed):
            sig = w.currentIndexChanged if isinstance(w, QComboBox) else w.toggled
            sig.connect(self.update_info)
        self.sp_custom.valueChanged.connect(self.update_info)
        for s in self.bed:
            s.valueChanged.connect(self.update_info)
        self.update_info()

    def denominator(self):
        d = self.cb_scale.currentData()
        return d if d else self.sp_custom.value()

    def update_info(self, *_):
        custom = self.cb_scale.currentData() is None
        self.sp_custom.setEnabled(custom)
        if not custom:
            # show the chosen scale's number, so switching to Custom starts from it
            self.sp_custom.blockSignals(True)
            self.sp_custom.setValue(self.cb_scale.currentData())
            self.sp_custom.blockSignals(False)
        for s in self.bed:
            s.setEnabled(self.cb_bed.isChecked())
        den = self.denominator()
        unit_mm = self.cb_unit.currentData()
        sx, sy, sz = [d * unit_mm / den for d in self.size]
        rx, ry, rz = [d * unit_mm for d in self.size]
        txt = ("Full size: %s x %s x %s mm<br>"
               "<b>Printed size: %s x %s x %s mm</b>" % (
                   _mm(rx), _mm(ry), _mm(rz), _mm(sx), _mm(sy), _mm(sz)))
        color = ""
        big = max(sx, sy, sz)
        if big < 0.05:
            txt += ("<br>That's under 0.05 mm - smaller than even a resin printer's pixel. If it should be "
                    "bigger, check the model's units (IngeTrazo works in metres).")
            color = "color: #b35900;"
        elif big < 1.0:
            txt += "<br>Fine detail: good for resin printing; too small for a 0.4 mm FDM nozzle."
        if self.cb_bed.isChecked():
            bx, by, bz = [s.value() for s in self.bed]
            fits = sz <= bz and ((sx <= bx and sy <= by) or (sy <= bx and sx <= by))
            if fits:
                txt += "<br>Fits on the print bed."
            else:
                txt += "<br>Too big for the print bed. Use a smaller scale."
                color = "color: #c0392b;"
        self.lbl_info.setStyleSheet(color)
        self.lbl_info.setText(txt)

    def get_values(self):
        return {
            'denominator': self.denominator(),
            'pivot': self.cb_pivot.currentData(),
            'mode': self.cb_mode.currentData(),
            'unit': UNITS[self.cb_unit.currentIndex()][2],
            'check_bed': self.cb_bed.isChecked(),
            'bed_x': self.bed[0].value(), 'bed_y': self.bed[1].value(), 'bed_z': self.bed[2].value(),
        }


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
class PrintScalerTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+P"
    description = "Scale the selected object to a chosen scale (1:50, 1:100 ...) for 3D printing."

    _saved = None
    _last_export = None

    def on_activate(self, viewport):
        scene = getattr(viewport, 'scene', None)
        entities = list(getattr(scene, 'selection', None) or [])
        verts, faces, meshes = collect(entities)

        if not verts:
            QMessageBox.warning(viewport, "Nothing Selected",
                                "Select the object (a group, or all of its faces) before running %s."
                                % PLUGIN_NAME)
            return

        lo, hi = bounds(verts)
        try:
            wl = world_loops(entities)             # a moved or turned component: its real size
            if wl:
                lo, hi = loops_bounds(wl)
        except Exception:
            pass
        size = (hi.x() - lo.x(), hi.y() - lo.y(), hi.z() - lo.z())

        cur = dict(DEFAULTS)
        if PrintScalerTool._saved:
            cur.update(PrintScalerTool._saved)
        # IngeTrazo keeps every model in metres, whatever units it shows, so start from metres
        # each time; millimetres is only for a model that came in 1000 times too big (an STL in mm
        # imported as metres)
        unit_key = guess_unit(size)
        cur['unit'] = None

        text = "Selected: %d vertices, %d faces" % (len(verts), len(faces))
        dialog = ScaleDialog(cur, size, unit_key, text, viewport)
        eddy_window(dialog, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        if dialog.exec() == QDialog.Accepted:
            vals = dialog.get_values()
            PrintScalerTool._saved = dict(vals)
            self.apply_scale(viewport, entities, vals)

    def on_deactivate(self, viewport):
        pass

    def apply_scale(self, viewport, entities, p):
        s = 1.0 / p['denominator']
        if p['mode'] == 'stl':
            return self._export_stl(viewport, entities, p)

        report = {}

        def mutate(scene):
            from core.mesh import Mesh
            from core.group import Group

            if p['mode'] == 'copy':
                loops = world_loops(entities)
                if not loops:
                    raise RuntimeError("Copy mode needs faces in the selection.")
                lo, hi = loops_bounds(loops)
                pv = pivot_point(p['pivot'], lo, hi)

                def scaled(pt):
                    return pv + (pt - pv) * s
                report.update(self._make_copy(scene, Mesh, Group, loops, lo, hi, scaled, p['denominator']))
                return

            verts, faces, meshes = collect(entities)
            if not verts:
                raise RuntimeError("Nothing to scale.")
            lo, hi = bounds(verts)
            pv = pivot_point(p['pivot'], lo, hi)
            size_max = max(hi.x() - lo.x(), hi.y() - lo.y(), hi.z() - lo.z(), 1e-9)
            tol = size_max * 1e-7

            def key(q):
                return (round(q.x() / tol), round(q.y() / tol), round(q.z() / tol))

            def scaled(pt):
                return pv + (pt - pv) * s
            self._scale_in_place(scene, verts, faces, meshes, scaled, key)

        try:
            viewport.history.execute(SnapshotImport(mutate))
        except Exception as e:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Scaling failed:\n%s" % e)
            return
        viewport.notify_scene_changed()
        if report.get('lost'):
            QMessageBox.warning(
                viewport, PLUGIN_NAME,
                "The copy at 1:%g is missing %d of %d faces.\n\nIngeTrazo treats points closer than 0.1 mm "
                "as the same point, so details smaller than that can't be kept once the model is scaled down "
                "this far.\n\nFor printing, use 'Export scaled (full detail)' instead: it writes the "
                "scaled model straight to a file (STL, 3MF, OBJ or PLY), every detail kept." % (
                    p['denominator'], report['lost'], report['lost'] + report['made']))
        try:
            viewport.flash_status("%s: scaled to 1:%g" % (PLUGIN_NAME, p['denominator']), 3000)
        except Exception:
            pass

    # ------------------------------------------------------------------ STL
    def _export_stl(self, viewport, entities, p):
        """Scale the selection outside the model, at full precision, and write it as an STL in mm
        - no detail is lost, however small, and the original isn't touched."""
        from PySide6.QtWidgets import QFileDialog
        loops = world_loops(entities)
        if not loops:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Select the object (a group or its faces) first.")
            return
        unit_mm = dict((u[2], u[1]) for u in UNITS).get(p.get('unit') or 'm', 1000.0)
        k = unit_mm / p['denominator']                      # model units -> printed mm
        tris = []
        for outer, holes, f in loops:
            for t in face_triangles(f):
                q = [vertex_to_vector3d(v) if not isinstance(v, QVector3D) else v for v in t]
                if any(x is None for x in q):
                    continue
                tris.append(tuple((x.x() * k, x.y() * k, x.z() * k) for x in q))
        if not tris:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Those faces couldn't be turned into triangles.")
            return
        # on the print bed: centred, standing on z = 0
        xs = [c[0] for t in tris for c in t]
        ys = [c[1] for t in tris for c in t]
        zs = [c[2] for t in tris for c in t]
        ox, oy, oz = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)
        tris = [tuple((c[0] - ox, c[1] - oy, c[2] - oz) for c in t) for t in tris]
        name = "scaled"
        for e in entities:
            if getattr(e, 'name', None):
                name = str(e.name)
                break
        safe = "".join(ch for ch in name if ch not in '\\/:*?"<>|').strip() or "scaled"
        # the file type you used last time comes first
        last = PrintScalerTool._last_export if PrintScalerTool._last_export in [e[0] for e in EXPORTS] \
            else EXPORTS[0][0]
        start = os.path.join(os.path.expanduser("~"), "Downloads", "%s 1-%g%s" % (
            safe, p['denominator'], dict((e[0], e[1]) for e in EXPORTS)[last]))
        res = QFileDialog.getSaveFileName(viewport, "Save the scaled model", start,
                                          ";;".join(e[0] for e in EXPORTS), last)
        path, chosen = (res[0], res[1]) if isinstance(res, (tuple, list)) and len(res) > 1 else (res, last)
        if not path:
            return
        fmt = next((e for e in EXPORTS if e[0] == chosen), None)
        if fmt is None or not path.lower().endswith(fmt[1]):
            # typed an extension of their own: go by that
            fmt = next((e for e in EXPORTS if path.lower().endswith(e[1])), fmt or EXPORTS[0])
        if not path.lower().endswith(fmt[1]):
            path += fmt[1]
        PrintScalerTool._last_export = fmt[0]
        try:
            fmt[2](path, tris, "%s at 1:%g" % (name, p['denominator']))
        except Exception as e:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not write the file:\n%s" % e)
            return
        QMessageBox.information(
            viewport, PLUGIN_NAME,
            "Saved %d triangles at 1:%g, %.1f x %.1f x %.1f mm, in millimetres:\n%s\n\nOpen it in your slicer "
            "(or Rhino, ZBrush...) as it is - it's already the right size, in mm." % (len(tris), p['denominator'], max(xs) - min(xs),
                                                          max(ys) - min(ys), max(zs) - min(zs), path))

    # ------------------------------------------------------------------ copy
    def _make_copy(self, scene, Mesh, Group, loops, lo, hi, scaled, den):
        # Put the copy beside the original (along +X) so it isn't hidden inside it.
        width = hi.x() - lo.x()
        scaled_lo = scaled(QVector3D(lo))
        offset = QVector3D(hi.x() + width * COPY_GAP - scaled_lo.x(), 0, 0)

        def P(q):
            n = scaled(q) + offset
            return VertexWrapper(n.x(), n.y(), n.z())
        target = Mesh()
        made = lost = 0
        for outer, holes, f in loops:
            try:
                nf = target.add_face([P(q) for q in outer], [[P(q) for q in h] for h in holes] or None)
            except TypeError:                          # an older IngeTrazo: holes one by one
                try:
                    nf = target.add_face([P(q) for q in outer])
                    for h in holes:
                        target.add_hole(nf, [P(q) for q in h])
                except Exception:
                    lost += 1
                    continue
            except Exception:
                lost += 1                              # too small to keep: its corners merged
                continue
            if nf is None:
                lost += 1
                continue
            made += 1
            try:
                col = getattr(f, 'attrs', {}).get('color')
                if col is not None:
                    nf.attrs['color'] = col
            except Exception:
                pass
        if made == 0:
            raise RuntimeError("None of the faces could be made at this scale (they're all smaller than "
                               "IngeTrazo's 0.1 mm). Use 'Export scaled' instead.")
        try:
            g = Group(target, name="Scaled 1:%g" % den)
        except TypeError:
            g = Group("Scaled 1:%g" % den)
            g.mesh = target
        try:
            g.name = "Scaled 1:%g" % den
        except Exception:
            pass
        if hasattr(scene, 'add_group'):
            scene.add_group(g)
        elif hasattr(scene, 'groups') and isinstance(scene.groups, list):
            scene.groups.append(g)
        else:
            raise RuntimeError("Could not add the scaled copy to the scene.")
        refresh_meshes([target])
        return {'made': made, 'lost': lost}

    # -------------------------------------------------------------- in place
    def _scale_in_place(self, scene, verts, faces, meshes, scaled, key):
        # Points of the selection, grouped by position (faces may hold their own
        # copies of a vertex, so every object at a position moves together).
        groups = {}
        for v in verts:
            q = vertex_to_vector3d(v)
            groups.setdefault(key(q), {'pos': q, 'objs': []})['objs'].append(v)

        seen_ids = set(id(v) for v in verts)
        sm = getattr(scene, 'mesh', None)
        if sm is not None and not any(sm is m for m in meshes):
            # Loose faces selected from the main scene mesh. Refuse if they share any
            # point with faces that are NOT selected: moving those points would drag
            # the neighbouring geometry, and not moving them would tear the mesh.
            face_ids = set(id(f) for f in faces)
            shared = set()
            for f in _items(getattr(sm, 'faces', None)):
                if id(f) in face_ids:
                    continue
                for v in _face_vertices(f):
                    q = vertex_to_vector3d(v)
                    if q is not None and key(q) in groups:
                        shared.add(key(q))
            if shared:
                raise RuntimeError(
                    "The selection is joined to other geometry at %d point(s), so scaling it "
                    "in place would distort its neighbours. Make it a group first, or use "
                    "'Scale a copy' mode." % len(shared))
            # Safe now: any main-mesh vertex at a selected position belongs only to the selection.
            for v in _items(getattr(sm, 'vertices', None)):
                if id(v) in seen_ids:
                    continue
                q = vertex_to_vector3d(v)
                if q is not None and key(q) in groups:
                    seen_ids.add(id(v))
                    groups[key(q)]['objs'].append(v)

        # Compute every destination before anything moves, and remember where
        # everything was so a failure can be undone.
        plan = [(g['objs'], g['pos'], scaled(g['pos'])) for g in groups.values()]
        moved = []
        failed = 0
        for objs, oldpos, newpos in plan:
            ok = True
            for o in objs:
                moved.append((o, oldpos))
                if not set_vertex(o, newpos):
                    ok = False
            if not ok:
                failed += 1

        if failed:
            for o, oldpos in moved:
                set_vertex(o, oldpos)
            raise RuntimeError(
                "Could not move %d of %d points, so the model was put back as it was. "
                "Use 'Scale a copy' mode instead." % (failed, len(plan)))

        touched = list(meshes)
        if sm is not None and not any(sm is m for m in touched):
            touched.append(sm)
        refresh_meshes(touched)
        print("%s: scaled %d points" % (PLUGIN_NAME, len(plan)))


# ---------------------------------------------------------------------------
# Running from the Python console
# ---------------------------------------------------------------------------
def _find_viewport():
    """Finds the IngeTrazo viewport: the widget that has a scene and an undo history."""
    from PySide6.QtWidgets import QApplication
    for w in QApplication.allWidgets():
        if hasattr(w, 'scene') and hasattr(w, 'history') and hasattr(w, 'notify_scene_changed'):
            return w
    return None


def run(viewport=None):
    """Console entry point: select the object, then call run()."""
    viewport = viewport or _find_viewport()
    if viewport is None:
        print("%s: could not find the viewport. Call run(<your viewport>) instead." % PLUGIN_NAME)
        return
    sel = list(getattr(getattr(viewport, 'scene', None), 'selection', None) or [])
    print("%s: viewport found, %d item(s) selected" % (PLUGIN_NAME, len(sel)))
    try:
        tool = PrintScalerTool()
    except TypeError:
        tool = PrintScalerTool.__new__(PrintScalerTool)
    tool.on_activate(viewport)
