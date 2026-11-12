# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Scale Studio for IngeTrazo (was 3D Scale Converter)
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
3D Scale Studio - scale, repair and export, for IngeTrazo
One window with pages (tabs) and a live 3D preview of what's selected:

  Converter  real sizes (ft / in / mm) to model sizes at any scale, as before.
  Scale      scales the selected object in the work area: to a model scale (1:76.2 ...),
             by a percentage, to a size you type (width, depth, height, kept in proportion
             or not), or from one model scale to another. In place or as a copy.
  Pieces     splits it into pieces (one per group, or your own plan), shown in colour in
             the preview, laid out on the bed. In the plan: 'Everything left' makes the grey
             parts still showing one piece; open pieces can have their holes closed when
             printed; each piece can go to its own slicer (FDM one way, resin the other).
  3D print   print bed, nozzle, thin-wall warnings, lay flat, slicer.
  Repair     checks for cracks, holes, faces the wrong way, thin walls; mends them.
  Export     3D printing (STL, 3MF), other 3D programs (OBJ with colours, PLY), web, games
             and AR (GLB / glTF), CAD (DXF), electronics (VRML), laser cutting and drawings
             (DXF / SVG outlines), and a picture (PNG).

Scale + next can gather objects onto one bed and send them to the slicer together.
Scale & Print  click an object, see it on the print bed, add it, click the next - then send
             the bed to your printer. Coloured buttons pick the printer.

Ctrl+Alt+K opens the window. The quick converter bar along the top of the main window is
still there (turn it on or off on the Converter page).
"""

import os
import json
import math
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout, QDoubleSpinBox, QSpinBox,
    QComboBox, QLabel, QFrame, QDialog, QPushButton, QCheckBox, QLineEdit, QMessageBox,
    QTabWidget, QSplitter, QRadioButton, QButtonGroup, QGroupBox, QPlainTextEdit,
    QTableWidget, QTableWidgetItem, QScrollArea
)

PLUGIN_NAME = "3D Scale Studio"
TOOLBAR_NAME = "ScaleConverterToolbar"
MM_PER_INCH = 25.4
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_scale_converter.json")

SCALES = [("OO / EM / P4  1:76.2", 76.2), ("1:80", 80.0), ("HO  1:87", 87.1), ("TT  1:120", 120.0),
          ("N (UK)  1:148", 148.0), ("N (Japan)  1:150", 150.0), ("N  1:160", 160.0),
          ("Z  1:220", 220.0), ("S  1:64", 64.0), ("O (UK)  1:43.5", 43.5), ("O (Europe)  1:45", 45.0),
          ("O (US)  1:48", 48.0), ("Gauge 1  1:32", 32.0), ("G  1:22.5", 22.5), ("Gauge 3  1:20.3", 20.3),
          ("1:12", 12.0), ("1:24", 24.0), ("1:50", 50.0), ("1:100", 100.0), ("1:200", 200.0),
          ("1:500", 500.0), ("1:1000", 1000.0), ("Custom", None)]

REAL_MAX_MM = 10000000.0                     # 10 km: the biggest real size the boxes take
REAL_MAX_FT = int(REAL_MAX_MM / MM_PER_INCH // 12) - 1   # leaves room for the inches

# (shown in the list, saved in settings)
REAL_UNITS = [("ft in", "ftin"), ("mm", "mm"), ("Both", "both")]
MODEL_UNITS = [("mm", "mm"), ("in", "in"), ("Both", "both")]

DEFAULTS = {'scale': 76.2, 'real_mm': 112.0, 'visible': True,
            'real_units': 'both', 'model_units': 'both', 'studio': {}}

# the model's own units: IngeTrazo keeps every model in metres
UNITS = [("Metres (m)", 1000.0, "m"), ("Centimetres (cm)", 10.0, "cm"), ("Millimetres (mm)", 1.0, "mm")]
# units sizes are shown and typed in: (label, mm in one)
SHOW_UNITS = [("mm", 1.0), ("cm", 10.0), ("m", 1000.0), ("in", MM_PER_INCH), ("ft", MM_PER_INCH * 12)]
PIVOTS = [("Bottom centre (stays on the ground)", "bottom"),
          ("Centre of the object", "centre"),
          ("Lowest corner", "corner"),
          ("World origin (0, 0, 0)", "origin")]
SCALE_MODES = [("To a model scale (1:76.2, 1:148 ...)", "scale"),
               ("By a percentage", "percent"),
               ("To a size I type", "size"),
               ("From one model scale to another", "rescale")]
SPLITS = [("One piece (everything selected together)", -1),
          ("Every group with faces (smallest pieces)", 0), ("Groups 1 level in", 1),
          ("Groups 2 levels in", 2), ("Groups 3 levels in", 3), ("Groups 4 levels in", 4)]
BEDS = [("Your own size", None),
        ("Small FDM  180 x 180 x 180", (180.0, 180.0, 180.0)),
        ("Medium FDM  220 x 220 x 250", (220.0, 220.0, 250.0)),
        ("Medium FDM  250 x 210 x 220", (250.0, 210.0, 220.0)),
        ("Large FDM  256 x 256 x 256", (256.0, 256.0, 256.0)),
        ("Extra large FDM  350 x 350 x 400", (350.0, 350.0, 400.0)),
        ("Small resin  130 x 80 x 160", (130.0, 80.0, 160.0)),
        ("Medium resin  220 x 125 x 250", (220.0, 125.0, 250.0))]
# file units: (label, mm in one unit)
FILE_UNITS = [("Millimetres", 1.0, "mm"), ("Centimetres", 10.0, "cm"), ("Metres", 1000.0, "m"),
              ("Inches", MM_PER_INCH, "in"), ("Tenths of an inch (electronics 3D models)", 2.54, "tenth")]
VIEWS = [("Seen from above (plan)", "top"), ("Seen from the front", "front"),
         ("Seen from the side", "side"), ("All three, side by side", "all")]

STUDIO_DEFAULTS = {
    'tab': 1, 'unit': 'm', 'show_unit': 'mm', 'mode': 'scale', 'scale': 76.2, 'percent': 50.0,
    'from_scale': 76.2, 'to_scale': 148.0, 'lock': True, 'pivot': 'bottom',
    'split': -1, 'gap': 5.0, 'lay_flat': True,
    'bed': True, 'bed_x': 220.0, 'bed_y': 220.0, 'bed_z': 250.0, 'nozzle': 0.4, 'warn_thin': True,
    'slicer': '', 'slicers': [], 'open_after': False,
    'fix_clean': True, 'fix_cracks': True, 'fix_holes': True, 'hole_edges': 60, 'fix_winding': True,
    'purpose': 'print', 'format': '3mf', 'file_unit': 'mm', 'y_up': False, 'use_scale': True,
    'per_piece': True, 'layout': 'bed', 'colours': True, 'apply_fixes': True, 'view': 'top',
    'png_size': 2000, 'follow': True, 'preview': 'model', 'last_folder': '', 'show_preview': True, 'beside': True, 'next_how': 'slicer', 'print_folder': '',
    'pv_width': 320, 'printers': [], 'printer': '', 'kind': 'fdm', 'print_format': '3mf',
    'before_fit': None, 'project_folder': '',
}

COPY_GAP = 0.1   # gap between original and copy, as a fraction of the original's width


# ---------------------------------------------------------------------------
# Sums (no Qt, so they can be checked on their own)
# ---------------------------------------------------------------------------
def ft_in_to_mm(ft, inch):
    return (ft * 12.0 + inch) * MM_PER_INCH


def mm_to_ft_in(mm):
    """(feet, inches) with inches under 12, rounded to 1/1000 in."""
    total = round(abs(mm) / MM_PER_INCH, 3)
    ft = int(total // 12)
    inch = round(total - ft * 12, 3)
    if inch >= 12.0:
        ft, inch = ft + 1, 0.0
    return ft, inch


def load_settings():
    s = dict(DEFAULTS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            s.update(json.load(f))
    except Exception:
        pass
    st = dict(STUDIO_DEFAULTS)
    if isinstance(s.get('studio'), dict):
        st.update({k: v for k, v in s['studio'].items() if k in STUDIO_DEFAULTS})
    s['studio'] = st
    return s


def save_settings(s):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=1)
    except Exception:
        pass


def update_settings(**changes):
    """Changes only the settings named, keeping all the others."""
    s = load_settings()
    s.update(changes)
    save_settings(s)



# ---------------------------------------------------------------------------
# Geometry: reading the selection, files for printing, mending, the piece pictures
# (the same as in 3D Print Scaler, so this file works on its own)
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
    """A 3MF (what most slicers like best): one object, units millimetres."""
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


def write_3mf_parts(path, parts):
    """A 3MF with each part a separate object (they open as separate items in the slicer).
    parts = [(name, tris)] in mm, already laid out on the bed."""
    import zipfile
    from xml.sax.saxutils import escape
    objs, items = [], []
    for i, (name, tris) in enumerate(parts):
        pts, faces = weld(tris)
        # each object is stored round its own centre and put in its place by the build item's
        # transform - the way slicers expect, so they keep the layout (and the gaps) as made
        cx = (min(q[0] for q in pts) + max(q[0] for q in pts)) / 2.0
        cy = (min(q[1] for q in pts) + max(q[1] for q in pts)) / 2.0
        cz = min(q[2] for q in pts)
        vs = "".join('<vertex x="%.9g" y="%.9g" z="%.9g"/>' % (q[0] - cx, q[1] - cy, q[2] - cz) for q in pts)
        ts = "".join('<triangle v1="%d" v2="%d" v3="%d"/>' % f for f in faces)
        objs.append('<object id="%d" name="%s" type="model"><mesh><vertices>%s</vertices>'
                    '<triangles>%s</triangles></mesh></object>' % (i + 1, escape(name), vs, ts))
        items.append('<item objectid="%d" transform="1 0 0 0 1 0 0 0 1 %.9g %.9g %.9g"/>' % (i + 1, cx, cy, cz))
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             '<metadata name="Application">IngeTrazo %s</metadata>'
             '<resources>%s</resources><build>%s</build></model>' % (escape(PLUGIN_NAME), "".join(objs),
                                                                     "".join(items)))
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


def _kids(g):
    return [c for c in _items(getattr(g, 'children', None)) + _items(getattr(g, 'groups', None))
            if not _is_face(c)]


def _placements(top):
    """(group, world matrix or None) for a group and every group inside it."""
    try:
        from core.group import iter_placements
        return list(iter_placements(top))
    except Exception:
        pass
    out = []

    def walk(g, base, depth):
        m = getattr(g, 'xform', None)
        if base is not None:
            m = base if m is None else base * m
        out.append((g, m))
        if depth < 12:
            for c in _kids(g):
                walk(c, m, depth + 1)
    walk(top, None, 0)
    return out


def _tris_of(faces, m=None):
    tris = []
    for f in faces:
        for t in face_triangles(f):
            q = [vertex_to_vector3d(v) if not isinstance(v, QVector3D) else v for v in t]
            if any(x is None for x in q):
                continue
            if m is not None:
                q = [m.map(x) for x in q]
            tris.append(tuple((x.x(), x.y(), x.z()) for x in q))
    return tris


def _piece_groups(e, depth):
    """The groups under a selected group e that each make one piece: [(group, [(group, matrix)])],
    the second list being every group (with its world placement) whose faces go into that piece.
    depth 0: every group with faces of its own is a piece. depth n: each group n levels in is a
    piece with everything inside it (so a group you made, holding several, prints as one); a
    group with faces nearer the top than that is a piece of its own."""
    place = {}
    for g, m in _placements(e):
        place.setdefault(id(g), m)
    out = []

    def faces_of(g):
        return _items(getattr(getattr(g, 'mesh', None), 'faces', None))

    def subtree(g, acc, lvl=0):
        acc.append((g, place.get(id(g), getattr(g, 'xform', None))))
        if lvl < 12:
            for c in _kids(g):
                subtree(c, acc, lvl + 1)
        return acc

    def walk(g, lvl):
        kids = _kids(g)
        if depth and lvl >= depth:
            out.append((g, subtree(g, [])))
            return
        if faces_of(g):
            out.append((g, [(g, place.get(id(g), getattr(g, 'xform', None)))]))
        if lvl < 12:
            for c in kids:
                walk(c, lvl + 1)
    walk(e, 0)
    return out


def split_parts(entities, depth=0):
    """The selection as separate parts: [(name, [triangles in world metres])]. With depth 0
    every group that has faces of its own is a part (a canopy gives a part per column, bracket,
    valance ...); with depth n, each group n levels in is one part with all that's inside it.
    Faces picked on their own make one part."""
    parts, loose, names = [], [], {}
    for e in entities:
        if _is_face(e):
            loose.append(e)
            continue
        for g, members in _piece_groups(e, depth):
            tris = []
            for h, m in members:
                tris += _tris_of(_items(getattr(getattr(h, 'mesh', None), 'faces', None)), m)
            if not tris:
                continue
            nm = str(getattr(g, 'name', '') or "Part")
            names[nm] = names.get(nm, 0) + 1
            parts.append((nm if names[nm] == 1 else "%s (%d)" % (nm, names[nm]), tris))
    if loose:
        tris = _tris_of(loose)
        if tris:
            parts.append(("Selected faces", tris))
    return parts


def count_parts(entities, depth=0):
    """How many parts 'Each group as a separate part' would make (cheap: no triangles)."""
    n, loose = 0, False
    for e in entities:
        if _is_face(e):
            loose = True
            continue
        for g, members in _piece_groups(e, depth):
            if any(_items(getattr(getattr(h, 'mesh', None), 'faces', None)) for h, _m in members):
                n += 1
    return n + (1 if loose else 0)


def _turn_to_down(n):
    """The rotation (3x3) that turns direction n to point straight down."""
    import math
    tx, ty, tz = 0.0, 0.0, -1.0
    ax, ay, az = n[1] * tz - n[2] * ty, n[2] * tx - n[0] * tz, n[0] * ty - n[1] * tx
    s = math.sqrt(ax * ax + ay * ay + az * az)
    cth = n[0] * tx + n[1] * ty + n[2] * tz
    if s < 1e-9:
        if cth > 0:
            return ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        return ((1, 0, 0), (0, -1, 0), (0, 0, -1))      # facing straight up: over on its back
    ax, ay, az = ax / s, ay / s, az / s
    C = 1 - cth
    return ((cth + ax * ax * C, ax * ay * C - az * s, ax * az * C + ay * s),
            (ay * ax * C + az * s, cth + ay * ay * C, ay * az * C - ax * s),
            (az * ax * C - ay * s, az * ay * C + ax * s, cth + az * az * C))


def lay_flat(tris):
    """Turns a part to print: on its biggest flat face if that face really carries it (a sheet's
    flat back, a panel, a column's square cap), otherwise - a thin wavy tin sheet, say - on its
    thinnest side, so it lies flat rather than standing on an edge. Then spins it round so it
    takes up the least room, long side along X. tris in mm."""
    import math
    pts = list({p for t in tris for p in t})
    if len(pts) < 3:
        return tris
    sample = pts if len(pts) <= 6000 else pts[::max(1, len(pts) // 6000)]
    planes, dirs = {}, {}
    for a, b, c in tris:
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        L = math.sqrt(nx * nx + ny * ny + nz * nz)
        if L < 1e-12:
            continue
        nx, ny, nz = nx / L, ny / L, nz / L
        d = nx * a[0] + ny * a[1] + nz * a[2]
        key = (round(nx, 3), round(ny, 3), round(nz, 3), round(d, 2))
        e = planes.setdefault(key, [0.0, (nx, ny, nz), d])
        e[0] += L / 2.0
        dk = (round(nx, 2), round(ny, 2), round(nz, 2))
        f = dirs.setdefault(dk, [0.0, (nx, ny, nz)])
        f[0] += L / 2.0
    if not planes:
        return tris

    def frame(n):
        u = (0.0, -n[2], n[1]) if abs(n[0]) < 0.9 else (-n[2], 0.0, n[0])
        L = math.sqrt(u[0] ** 2 + u[1] ** 2 + u[2] ** 2)
        u = (u[0] / L, u[1] / L, u[2] / L)
        w = (n[1] * u[2] - n[2] * u[1], n[2] * u[0] - n[0] * u[2], n[0] * u[1] - n[1] * u[0])
        return u, w

    def dots(n):
        return [n[0] * p[0] + n[1] * p[1] + n[2] * p[2] for p in sample]

    def footprint(n):
        u, w = frame(n)
        a_, b_ = dots(u), dots(w)
        return (max(a_) - min(a_)) * (max(b_) - min(b_))
    chosen = None

    def ext(n):
        ds = dots(n)
        return max(ds) - min(ds)
    # 0. a thin plate (a sheet, a valance, a strip) always lies down on its thinnest side
    # ways to try: the faces' own directions, the three axes, and each direction averaged with
    # its neighbours (a wavy sheet's facets lean both ways; their average is the sheet's own)
    tops = sorted(dirs.values(), key=lambda e: -e[0])[:60]
    cands = [e[1] for e in tops] + [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]
    for _a, n0 in tops[:12]:
        sx_ = sy_ = sz_ = 0.0
        for a_, n1 in dirs.values():
            if n0[0] * n1[0] + n0[1] * n1[1] + n0[2] * n1[2] > 0.5:
                sx_, sy_, sz_ = sx_ + n1[0] * a_, sy_ + n1[1] * a_, sz_ + n1[2] * a_
        L_ = math.sqrt(sx_ * sx_ + sy_ * sy_ + sz_ * sz_)
        if L_ > 1e-12:
            cands.append((sx_ / L_, sy_ / L_, sz_ / L_))
    thin = min(cands, key=ext)
    u_, w_ = frame(thin)
    plate = ext(thin) < 0.2 * min(ext(u_), ext(w_))
    # 1. the biggest flat faces that are on the outside (the part could stand on them) and cover
    #    a good share of the part's footprint that way down
    biggest = max(e[0] for e in planes.values())
    for area, n, d in sorted(planes.values(), key=lambda e: -e[0])[:8]:
        if area < 0.3 * biggest:
            break                                      # a small face: not one to lay it on
        if d < max(dots(n)) - 1e-3:
            continue                                   # not on the outside: it can't stand on it
        if plate and ext(n) > 1.5 * ext(thin):
            continue                                   # a plate isn't stood on its edge
        if area >= 0.25 * footprint(n):
            chosen = n
            break
    if chosen is None:
        # 2. no face to stand on: the thinnest way through, so it lies down
        n = thin
        # the side with more surface facing that way goes down (a sheet's back, not its front)
        out_ = sum(e[0] for e in dirs.values() if sum(a * b for a, b in zip(e[1], n)) > 0.5)
        in_ = sum(e[0] for e in dirs.values() if sum(a * b for a, b in zip(e[1], n)) < -0.5)
        chosen = n if out_ >= in_ else (-n[0], -n[1], -n[2])
    # one already lying face down wins if it does as well (no turning for nothing)
    if chosen[2] > -0.999 and not (plate and ext((0.0, 0.0, 1.0)) > 1.5 * ext(thin)):
        for area, n, d in planes.values():
            if n[2] < -0.999 and d >= max(dots(n)) - 1e-3 and area >= 0.95 * max(e[0] for e in planes.values()):
                chosen = n
                break
    R = _turn_to_down(chosen)

    def turn(p):
        return (R[0][0] * p[0] + R[0][1] * p[1] + R[0][2] * p[2],
                R[1][0] * p[0] + R[1][1] * p[1] + R[1][2] * p[2],
                R[2][0] * p[0] + R[2][1] * p[1] + R[2][2] * p[2])
    out = [tuple(turn(p) for p in t) for t in tris]
    # spin about z for the smallest footprint (long side along x)
    xy = list({(round(p[0], 3), round(p[1], 3)) for t in out for p in t})
    if len(xy) > 4000:
        xy = xy[::max(1, len(xy) // 4000)]
    best_a, best_area = 0.0, None
    for k in range(0, 90, 2):
        a = math.radians(k)
        ca, sa = math.cos(a), math.sin(a)
        xs = [x * ca - y * sa for x, y in xy]
        ys = [x * sa + y * ca for x, y in xy]
        area = (max(xs) - min(xs)) * (max(ys) - min(ys))
        if best_area is None or area < best_area - 1e-9:
            best_a, best_area = a, area
    ca, sa = math.cos(best_a), math.sin(best_a)
    xs = [x * ca - y * sa for x, y in xy]
    ys = [x * sa + y * ca for x, y in xy]
    if max(ys) - min(ys) > max(xs) - min(xs):
        best_a += math.pi / 2
        ca, sa = math.cos(best_a), math.sin(best_a)
    return [tuple((p[0] * ca - p[1] * sa, p[0] * sa + p[1] * ca, p[2]) for p in t) for t in out]


def mend_cracks(tris, tol=2e-4):
    """Mends hairline cracks: where a corner of one face sits part way along an edge of the face
    next to it (a 'T-junction'), the slicer sees open edges. Each such edge is split at that corner
    so every edge is shared by exactly two triangles. tris in mm.
    Returns (tris, open edges found, open edges left)."""
    import math
    pts, idx, tri = [], {}, []
    for t in tris:
        f = []
        for c in t:
            k = (round(c[0], 6), round(c[1], 6), round(c[2], 6))
            if k not in idx:
                idx[k] = len(pts)
                pts.append(c)
            f.append(idx[k])
        if len(set(f)) == 3:
            tri.append(f)

    def open_edges(tri):
        cnt = {}
        for a, b, c in tri:
            for e in ((a, b), (b, c), (c, a)):
                cnt[e] = cnt.get(e, 0) + 1
        return [e for e, n in cnt.items() if cnt.get((e[1], e[0]), 0) != n]
    first = open_edges(tri)
    if not first:
        return tris, 0, 0
    for _round in range(3):
        bad = open_edges(tri)
        if not bad:
            break
        on = sorted({v for e in bad for v in e})
        span = max(max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)) or 1.0
        cell = max(span / 256.0, 10 * tol)
        grid = {}
        for v in on:
            p = pts[v]
            grid.setdefault((int(math.floor(p[0] / cell)), int(math.floor(p[1] / cell)),
                             int(math.floor(p[2] / cell))), []).append(v)
        bad_set = set(bad)
        new, changed = [], False
        for f in tri:
            splits = {}
            for i in range(3):
                a, b = f[i], f[(i + 1) % 3]
                if (a, b) not in bad_set:
                    continue
                A, B = pts[a], pts[b]
                d = (B[0] - A[0], B[1] - A[1], B[2] - A[2])
                L2 = d[0] ** 2 + d[1] ** 2 + d[2] ** 2
                if L2 < 1e-18:
                    continue
                lo = [int(math.floor(min(A[j], B[j]) / cell)) - 1 for j in range(3)]
                hi = [int(math.floor(max(A[j], B[j]) / cell)) + 1 for j in range(3)]
                if (hi[0] - lo[0] + 1) * (hi[1] - lo[1] + 1) * (hi[2] - lo[2] + 1) > 4 * len(grid):
                    cand = on
                else:
                    cand = [v for gx in range(lo[0], hi[0] + 1) for gy in range(lo[1], hi[1] + 1)
                            for gz in range(lo[2], hi[2] + 1) for v in grid.get((gx, gy, gz), ())]
                found = []
                for v in cand:
                    if v in (a, b):
                        continue
                    P = pts[v]
                    t_ = ((P[0] - A[0]) * d[0] + (P[1] - A[1]) * d[1] + (P[2] - A[2]) * d[2]) / L2
                    if t_ <= 1e-7 or t_ >= 1 - 1e-7:
                        continue
                    q = (A[0] + d[0] * t_ - P[0], A[1] + d[1] * t_ - P[1], A[2] + d[2] * t_ - P[2])
                    if q[0] ** 2 + q[1] ** 2 + q[2] ** 2 <= tol * tol:
                        found.append((t_, v))
                if found:
                    splits[i] = [v for _, v in sorted(found)]
            if not splits:
                new.append(f)
                continue
            changed = True
            # the triangle's outline with the extra corners, fanned from a corner not on a split edge
            ring = []
            for i in range(3):
                ring.append(f[i])
                ring += splits.get(i, [])
            if len(splits) == 1:
                # one edge split: fan from the corner across from it
                i = list(splits)[0]
                v0 = f[(i + 2) % 3]
                start = ring.index(v0)
                ring = ring[start:] + ring[:start]
                for k in range(1, len(ring) - 1):
                    new.append([ring[0], ring[k], ring[k + 1]])
            else:
                # more than one: fan from the middle of the triangle
                c = len(pts)
                pts.append(tuple(sum(pts[v][j] for v in f) / 3.0 for j in range(3)))
                for k in range(len(ring)):
                    new.append([ring[k], ring[(k + 1) % len(ring)], c])
        tri = new
        if not changed:
            break
    left = len(open_edges(tri))
    return [tuple(pts[v] for v in f) for f in tri], len(first), left


# ---------------------------------------------------------------------------
# Planning the print pieces: which parts print together, colour coded
# ---------------------------------------------------------------------------
PIECE_COLOURS = [(230, 90, 70), (60, 140, 220), (90, 180, 80), (240, 170, 40), (160, 90, 200), (40, 180, 180),
                 (220, 100, 170), (140, 110, 60), (120, 160, 40), (90, 90, 200), (200, 60, 110), (60, 120, 90)]
LOOSE_COLOUR = (175, 175, 172)


# ---------------------------------------------------------------------------
# Checks before printing: faces the wrong way, walls thinner than the nozzle, overlaps
# ---------------------------------------------------------------------------
import math


def _shells(tris, decimals=4):
    """Welded corners and the triangles' shells: (keys, [[tri index]]) where a shell is
    triangles joined edge to edge (an edge shared by exactly two)."""
    keys = [tuple((round(c[0], decimals), round(c[1], decimals), round(c[2], decimals)) for c in t) for t in tris]
    edges = {}
    for i, k in enumerate(keys):
        for j in range(3):
            a, b = k[j], k[(j + 1) % 3]
            if a != b:
                edges.setdefault((a, b) if a < b else (b, a), []).append(i)
    nbr = [[] for _ in tris]
    for e, ts in edges.items():
        if len(ts) == 2 and ts[0] != ts[1]:
            nbr[ts[0]].append((ts[1], e))
            nbr[ts[1]].append((ts[0], e))
    seen = [False] * len(tris)
    shells = []
    for s in range(len(tris)):
        if seen[s]:
            continue
        seen[s] = True
        comp, stack = [], [s]
        while stack:
            i = stack.pop()
            comp.append(i)
            for j, _ in nbr[i]:
                if not seen[j]:
                    seen[j] = True
                    stack.append(j)
        shells.append(comp)
    return keys, nbr, shells


def _runs(k, a, b):
    """True if the triangle (corner keys k) runs a -> b."""
    for j in range(3):
        if k[j] == a and k[(j + 1) % 3] == b:
            return True
    return False


def fix_winding(tris):
    """Turns faces that point the wrong way: inside each closed shell every triangle is made to
    agree with its neighbours, then the whole shell is turned outward if it came out inside out.
    tris in mm. Returns (tris, triangles turned, shells turned inside-out)."""
    if not tris:
        return tris, 0, 0
    keys, nbr, shells = _shells(tris)
    flip = [None] * len(tris)
    for comp in shells:
        flip[comp[0]] = False
        stack = [comp[0]]
        while stack:
            i = stack.pop()
            for j, (a, b) in nbr[i]:
                if flip[j] is not None:
                    continue
                # the edge as triangle i runs it (after its own flip)
                ia = _runs(keys[i], a, b) != flip[i]
                ja = _runs(keys[j], a, b)
                flip[j] = (ja == ia)          # both run it the same way: turn j
                stack.append(j)
    # whichever way most of a shell's faces point is taken as meant (the first face might be
    # the odd one out)
    for comp in shells:
        if sum(1 for i in comp if flip[i]) * 2 > len(comp):
            for i in comp:
                flip[i] = not flip[i]
    out = [tuple(reversed(t)) if flip[i] else t for i, t in enumerate(tris)]
    turned_shells = 0
    for comp in shells:
        if len(comp) < 4 or any(len(nbr[i]) != 3 for i in comp):
            continue                  # not closed: its inside and outside can't be told
        vol = 0.0
        for i in comp:
            a, b, c = out[i]
            vol += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                    + a[2] * (b[0] * c[1] - b[1] * c[0]))
        if vol < 0:
            turned_shells += 1
            for i in comp:
                out[i] = tuple(reversed(out[i]))
                flip[i] = not flip[i]
    return out, sum(1 for f in flip if f), turned_shells


def _tri_n(t):
    a, b, c = t
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    L = (nx * nx + ny * ny + nz * nz) ** 0.5
    return (nx / L, ny / L, nz / L, L / 2.0) if L > 1e-15 else None


def _ray_hit(o, d, t):
    """Distance along ray o + s*d to triangle t, or None (Moller-Trumbore)."""
    a, b, c = t
    e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    p = (d[1] * e2[2] - d[2] * e2[1], d[2] * e2[0] - d[0] * e2[2], d[0] * e2[1] - d[1] * e2[0])
    det = e1[0] * p[0] + e1[1] * p[1] + e1[2] * p[2]
    if abs(det) < 1e-14:
        return None
    inv = 1.0 / det
    s = (o[0] - a[0], o[1] - a[1], o[2] - a[2])
    u = (s[0] * p[0] + s[1] * p[1] + s[2] * p[2]) * inv
    if u < -1e-9 or u > 1 + 1e-9:
        return None
    q = (s[1] * e1[2] - s[2] * e1[1], s[2] * e1[0] - s[0] * e1[2], s[0] * e1[1] - s[1] * e1[0])
    w = (d[0] * q[0] + d[1] * q[1] + d[2] * q[2]) * inv
    if w < -1e-9 or u + w > 1 + 1e-9:
        return None
    return (e2[0] * q[0] + e2[1] * q[1] + e2[2] * q[2]) * inv


def thin_walls(tris, nozzle, samples=4000):
    """How much of a part is thinner than the nozzle: a ray goes in from each face (a sample of
    them) and looks for the far side of the wall within one nozzle width (3 % allowed over, so a
    wall made exactly the nozzle's width passes). tris in printed mm, facing outward. Returns
    (the usual thickness where it's thin, or None; share of the surface that is thin)."""
    if not tris or nozzle <= 0:
        return None, 0.0
    # each solid on its own: a wall is measured to its own far side, not into a neighbour
    shell_of = [0] * len(tris)
    for k_, comp in enumerate(_shells(tris)[2]):
        for i in comp:
            shell_of[i] = k_
    cell = max(nozzle * 2.0, 1e-3)
    grid, big = {}, []
    info = []
    for i, t in enumerate(tris):
        n = _tri_n(t)
        info.append(n)
        if n is None:
            continue
        lo = [int(math.floor(min(c[k] for c in t) / cell)) for k in range(3)]
        hi = [int(math.floor(max(c[k] for c in t) / cell)) for k in range(3)]
        if (hi[0] - lo[0] + 1) * (hi[1] - lo[1] + 1) * (hi[2] - lo[2] + 1) > 3000:
            big.append(i)
            continue
        for x in range(lo[0], hi[0] + 1):
            for y in range(lo[1], hi[1] + 1):
                for z in range(lo[2], hi[2] + 1):
                    grid.setdefault((x, y, z), []).append(i)
    idx = [i for i in range(len(tris)) if info[i]]
    step = max(1, len(idx) // samples)
    area = thin = 0.0
    hits = []
    for i in idx[::step]:
        nx, ny, nz, A = info[i]
        t = tris[i]
        cx = (t[0][0] + t[1][0] + t[2][0]) / 3.0
        cy = (t[0][1] + t[1][1] + t[2][1]) / 3.0
        cz = (t[0][2] + t[1][2] + t[2][2]) / 3.0
        d = (-nx, -ny, -nz)
        area += A
        e = (cx + d[0] * nozzle, cy + d[1] * nozzle, cz + d[2] * nozzle)
        cand = set(big)
        for x in range(int(math.floor(min(cx, e[0]) / cell)), int(math.floor(max(cx, e[0]) / cell)) + 1):
            for y in range(int(math.floor(min(cy, e[1]) / cell)), int(math.floor(max(cy, e[1]) / cell)) + 1):
                for z in range(int(math.floor(min(cz, e[2]) / cell)), int(math.floor(max(cz, e[2]) / cell)) + 1):
                    cand.update(grid.get((x, y, z), ()))
        best = None
        for j in cand:
            if j == i or shell_of[j] != shell_of[i]:
                continue
            nj = info[j]
            # only the far side of the wall, roughly facing the other way (not a sloping face
            # met at a sharp edge, which isn't the wall's thickness)
            if nj is None or nj[0] * d[0] + nj[1] * d[1] + nj[2] * d[2] <= 0.8:
                continue
            s = _ray_hit((cx, cy, cz), d, tris[j])
            if s is not None and 1e-5 < s < nozzle * 0.97 and (best is None or s < best):
                best = s
        if best is not None:
            thin += A
            hits.append((best, A))
    if not hits:
        return None, 0.0
    # the thickness over most of the thin area (not a sliver at a sharp edge)
    hits.sort()
    half, acc = thin / 2.0, 0.0
    usual = hits[-1][0]
    for th, A in hits:
        acc += A
        if acc >= half:
            usual = th
            break
    return usual, (thin / area if area > 0 else 0.0)


def overlapping_solids(tris, limit=400):
    """How many closed solids in a part reach inside another one (they print fine - the slicer
    merges them - but some slicers mention it). tris in mm, facing outward."""
    keys, nbr, shells = _shells(tris)
    shells = [s for s in shells if len(s) >= 4][:limit]
    if len(shells) < 2:
        return 0
    boxes = []
    for comp in shells:
        pts = [c for i in comp for c in tris[i]]
        boxes.append([min(p[k] for p in pts) for k in range(3)] + [max(p[k] for p in pts) for k in range(3)])
    d = (0.5773, 0.5774, 0.5772)
    hit = set()
    work = 0
    for a in range(len(shells)):
        for b in range(len(shells)):
            if a == b or a in hit:
                continue
            A, B = boxes[a], boxes[b]
            if any(A[k] >= B[k + 3] - 1e-3 or B[k] >= A[k + 3] - 1e-3 for k in range(3)):
                continue
            # a few points just inside a: is any inside b?
            comp = shells[a]
            for i in comp[::max(1, len(comp) // 12)]:
                n = _tri_n(tris[i])
                if n is None:
                    continue
                t = tris[i]
                o = tuple((t[0][k] + t[1][k] + t[2][k]) / 3.0 - n[k] * 0.02 for k in range(3))
                if not all(B[k] < o[k] < B[k + 3] for k in range(3)):
                    continue
                work += len(shells[b])
                if work > 3000000:
                    return len(hit)
                cross = sum(1 for j in shells[b] if (lambda s_: s_ is not None and s_ > 1e-7)(_ray_hit(o, d, tris[j])))
                if cross % 2 == 1:
                    hit.add(a)
                    break
    return len(hit)


def check_parts(parts, nozzle=0.0):
    """Checks parts [(name, tris)] in printed mm before printing. Returns (parts with faces
    turned the right way, [lines of report], anything worth a warning)."""
    lines, warn = [], False
    out = []
    turned = inside = 0
    for name, tr in parts:
        tr, f_, s_ = fix_winding(tr)
        turned += f_
        inside += s_
        out.append((name, tr))
        if nozzle > 0:
            th, share = thin_walls(tr, nozzle)
            if th is not None and share > 0.005:
                warn = True
                lines.append("%s: %d%% of it is thinner than the %.2f mm nozzle (about %.2f mm thick)." % (
                    name, int(round(share * 100)) or 1, nozzle, th))
        ov = overlapping_solids(tr)
        if ov:
            lines.append("%s: %d solid%s overlap another (fine - the slicer joins them)." % (
                name, ov, "" if ov == 1 else "s"))
    if turned:
        lines.insert(0, "Turned %d face%s that pointed the wrong way%s." % (
            turned, "" if turned == 1 else "s",
            " (%d solid%s inside out)" % (inside, "" if inside == 1 else "s") if inside else ""))
    return out, lines, warn


# words in a slicer's program name that mean it's for resin printers (they want STL)
RESIN_SLICERS = ('chitubox', 'lychee', 'photon', 'halot', 'voxeldance', 'tango', 'elegoo', 'uniformation',
                 'formware', 'ameralabs', 'nova3d', 'phrozen')

PRINTER_COLOURS = [(46, 139, 87), (142, 68, 173), (211, 120, 20), (41, 128, 185), (192, 57, 43)]


def piece_colour(i):
    return PIECE_COLOURS[i % len(PIECE_COLOURS)]


def piece_leaves(entities, with_tris=True, tops_out=None):
    """Every smallest part of the selection: [(key, name, kind, [triangles in world metres])].
    key is the part's path of group names (so a plan still fits after the window is reopened),
    kind the name of the group it's in. tops_out: filled with the number of the selected object
    each part belongs to (-1: loose faces)."""
    out, seen = [], {}
    loose = []
    for ei, e in enumerate(entities):
        if _is_face(e):
            loose.append(e)
            continue
        place = {}
        for g, m in _placements(e):
            place.setdefault(id(g), m)

        def walk(g, path, lvl):
            nm = str(getattr(g, 'name', '') or "Group")
            here = path + [nm]
            faces = _items(getattr(getattr(g, 'mesh', None), 'faces', None))
            if faces:
                tris = _tris_of(faces, place.get(id(g), getattr(g, 'xform', None))) if with_tris else [None]
                if tris:
                    key = "/".join(here)
                    seen[key] = seen.get(key, 0) + 1
                    if seen[key] > 1:
                        key += "#%d" % seen[key]
                    # the group it's in - or, straight under what you selected, its own name
                    kind = path[-1] if len(path) >= 2 else nm
                    out.append((key, nm, kind, tris))
                    if tops_out is not None:
                        tops_out.append(ei)
            if lvl < 12:
                for c in _kids(g):
                    walk(c, here, lvl + 1)
        walk(e, [], 0)
    if loose:
        tris = _tris_of(loose) if with_tris else [None]
        if tris:
            out.append(("Selected faces", "Selected faces", "", tris))
            if tops_out is not None:
                tops_out.append(-1)
    return out


_FLOW = []


def flow_layout(spacing=6):
    """A row of buttons that wraps onto more lines when the window is too narrow for them all."""
    if not _FLOW:
        from PySide6.QtWidgets import QLayout
        from PySide6.QtCore import QRect, QSize, QPoint

        class FlowLayout(QLayout):
            def __init__(self, parent=None, sp=6):
                super().__init__(parent)
                self._items = []
                self._sp = sp
                self.setContentsMargins(0, 0, 0, 0)

            def addItem(self, item):
                self._items.append(item)

            def count(self):
                return len(self._items)

            def itemAt(self, i):
                return self._items[i] if 0 <= i < len(self._items) else None

            def takeAt(self, i):
                return self._items.pop(i) if 0 <= i < len(self._items) else None

            def expandingDirections(self):
                from PySide6.QtCore import Qt
                try:
                    return Qt.Orientation(0)
                except Exception:
                    return Qt.Orientations(0)

            def hasHeightForWidth(self):
                return True

            def heightForWidth(self, w):
                return self._place(QRect(0, 0, w, 0), True)

            def setGeometry(self, r):
                super().setGeometry(r)
                self._place(r, False)

            def sizeHint(self):
                return self.minimumSize()

            def minimumSize(self):
                sz = QSize()
                for it in self._items:
                    sz = sz.expandedTo(it.minimumSize())
                return sz

            def _place(self, r, test):
                x, y, line = r.x(), r.y(), 0
                for it in self._items:
                    h = it.sizeHint()
                    nx = x + h.width() + self._sp
                    if nx - self._sp > r.right() + 1 and line > 0:
                        x, y = r.x(), y + line + self._sp
                        nx, line = x + h.width() + self._sp, 0
                    if not test:
                        it.setGeometry(QRect(QPoint(x, y), h))
                    x = nx
                    line = max(line, h.height())
                return y + line - r.y()
        _FLOW.append(FlowLayout)
    return _FLOW[0](None, spacing)


def plan_parts(leaves, plan, with_piece=False):
    """Parts from leaves and a plan {'pieces': [names], 'keys': {key: piece name}}: each planned
    piece is all its parts together; parts in no piece print on their own.
    with_piece: (name, tris, the plan's piece it is - "" for a part on its own)."""
    pieces = list(plan.get('pieces', [])) if plan else []
    keys = plan.get('keys', {}) if plan else {}
    skip = set(plan.get('skip', [])) if plan else set()
    merged = dict((p, []) for p in pieces)
    alone = []
    for key, name, kind, tris in leaves:
        if key in skip:
            continue                             # taken out of the print
        p = keys.get(key)
        if p in merged:
            merged[p] += tris
        else:
            alone.append((name, tris, ""))
    out = [(p, merged[p], p) for p in pieces if merged[p]]
    names = {}
    for n, tr, _p in out + alone:
        names[n] = names.get(n, 0) + 1
    seen = {}
    res = []
    for n, tr, p in out + alone:
        seen[n] = seen.get(n, 0) + 1
        nm = n if names[n] == 1 else "%s (%d)" % (n, seen[n])
        res.append((nm, tr, p) if with_piece else (nm, tr))
    return res


def piece_state(tris):
    """'ok' (closed - prints solid), 'open' (holes: the slicer may leave it out or fill it
    wrongly) or 'flat' (a sheet with no thickness - needs thickness to print)."""
    if not tris:
        return 'ok'
    s = tris_size(tris)
    big = max(s) or 1.0
    if min(s) <= big * 1e-6:
        return 'flat'
    opened, _many = edge_report(tris)
    return 'open' if opened else 'ok'


def close_all_holes(tris):
    """Closes every hole, whatever its size (a missing bottom, an open end), so the piece is a
    closed solid the slicer can print. Returns (tris, holes closed, holes that couldn't be)."""
    tris, filled, left = fill_holes(tris, 10 ** 9)
    if filled:
        tris, _t, _i = fix_winding(tris)
    return tris, filled, left


def _qt(group, name):
    """A Qt enum value, old or new spelling (Qt.Checked or Qt.CheckState.Checked)."""
    from PySide6.QtCore import Qt
    v = getattr(Qt, name, None)
    return v if v is not None else getattr(getattr(Qt, group), name)


def _prep_part(tris, limit=200000):
    """A part's triangles ready to draw: [(tri, normal, edge flags)] - an edge is drawn as a line
    where the surface folds (or ends), so the part's shape reads clearly, not its triangles.
    Every triangle is kept (leaving some out makes holes and stripes in the picture), up to a very
    big model. A part whose faces don't all agree which way is out (an STL with faces written the
    wrong way round) gets each face both ways round, so none goes missing from the picture."""
    import math
    step = max(1, int(math.ceil(len(tris) / float(limit))))
    if step > 1:
        tris = tris[::step]
    out, edges = [], {}

    def k(p):
        return (round(p[0], 7), round(p[1], 7), round(p[2], 7))
    directed = {}
    for t in tris:
        a, b, c = t
        u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        w = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        L = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
        if L < 1e-18:
            continue
        n = (n[0] / L, n[1] / L, n[2] / L)
        idx = len(out)
        out.append([t, n, [False, False, False]])
        ks = (k(a), k(b), k(c))
        for e in range(3):
            p_, q_ = ks[e], ks[(e + 1) % 3]
            edges.setdefault(tuple(sorted((p_, q_))), []).append((idx, e))
            directed[(p_, q_)] = directed.get((p_, q_), 0) + 1
    # do the faces agree? each edge run one way by one face and back the other way by the next
    mixed = any(directed.get((q_, p_), 0) != n_ for (p_, q_), n_ in directed.items())
    for lst in edges.values():
        if len(lst) != 2:
            for idx, e in lst:
                out[idx][2][e] = True
            continue
        (i1, e1), (i2, e2) = lst
        n1, n2 = out[i1][1], out[i2][1]
        d = n1[0] * n2[0] + n1[1] * n2[1] + n1[2] * n2[2]
        if (abs(d) if mixed else d) < 0.94:      # a fold of more than ~20 degrees
            out[i1][2][e1] = True
            out[i2][2][e2] = True
    if mixed:
        out += [[(t[0], t[2], t[1]), (-n[0], -n[1], -n[2]), [fl[2], fl[1], fl[0]]] for t, n, fl in out]
    return out


def _split_big(prepped, size):
    """Big triangles cut into smaller ones (each edge no longer than size), so they sort
    properly against their neighbours in the picture. The fold lines stay on the outer edges."""
    out = []
    stack = list(prepped)
    while stack:
        t, n, fl = stack.pop()
        a, b, c = t
        L = [sum((t[(e + 1) % 3][k] - t[e][k]) ** 2 for k in range(3)) for e in range(3)]
        if max(L) <= size * size or len(out) + len(stack) > 60000:
            out.append((t, n, fl))
            continue
        ab = tuple((a[k] + b[k]) / 2 for k in range(3))
        bc = tuple((b[k] + c[k]) / 2 for k in range(3))
        ca = tuple((c[k] + a[k]) / 2 for k in range(3))
        stack += [((a, ab, ca), n, [fl[0], False, fl[2]]), ((ab, b, bc), n, [fl[0], fl[1], False]),
                  ((ca, bc, c), n, [False, fl[1], fl[2]]), ((ab, bc, ca), n, [False, False, False])]
    return out


def _view_axes(az, el=32.0):
    import math
    a, e = math.radians(az), math.radians(el)
    D = (math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), -math.sin(e))   # looking along D
    R = (D[1], -D[0], 0.0)
    L = math.sqrt(R[0] ** 2 + R[1] ** 2) or 1.0
    R = (R[0] / L, R[1] / L, 0.0)
    U = (R[1] * D[2] - R[2] * D[1], R[2] * D[0] - R[0] * D[2], R[0] * D[1] - R[1] * D[0])
    return D, R, U


LIGHT = (-0.3, -0.45, 0.84)


def _project(prepped, D, R, U, leaf=0):
    """[(depth, leaf, pts2d, shade, [(p, q) feature edges in 2d])], front faces only."""
    out = []
    LIGHT = (-0.3, -0.45, 0.84) if D[2] <= 0 else (-0.3, -0.45, -0.84)     # lit from the side you look
    for t, n, fl in prepped:
        if n[0] * D[0] + n[1] * D[1] + n[2] * D[2] >= 0:
            continue
        sh = 0.5 + 0.5 * max(0.0, n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2])
        pts = [(p[0] * R[0] + p[1] * R[1] + p[2] * R[2], -(p[0] * U[0] + p[1] * U[1] + p[2] * U[2])) for p in t]
        d = sum(p[0] * D[0] + p[1] * D[1] + p[2] * D[2] for p in t) / 3.0
        ed = [(pts[e], pts[(e + 1) % 3]) for e in range(3) if fl[e]]
        out.append((d, leaf, pts, sh, ed))
    return out


def part_thumbnail(prepped, colour, size, az):
    """A small picture of one part on its own, in its piece's colour."""
    from PySide6.QtGui import QPixmap, QPainter, QColor, QPolygonF, QPen
    from PySide6.QtCore import QPointF
    pm = QPixmap(size, size)
    pm.fill(QColor(255, 255, 255))
    D, R, U = _view_axes(az)
    items = sorted(_project(prepped, D, R, U), key=lambda e: -e[0])
    if not items:
        return pm
    xs = [x for e in items for x, _ in e[2]]
    ys = [y for e in items for _, y in e[2]]
    m = 4
    sc = min((size - 2 * m) / ((max(xs) - min(xs)) or 1), (size - 2 * m) / ((max(ys) - min(ys)) or 1))
    ox = m + (size - 2 * m - (max(xs) - min(xs)) * sc) / 2 - min(xs) * sc
    oy = m + (size - 2 * m - (max(ys) - min(ys)) * sc) / 2 - min(ys) * sc
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    edge = QPen(QColor(40, 40, 40), 0.8)
    for _d, _i, pts, sh, ed in items:
        col = QColor(int(colour[0] * sh), int(colour[1] * sh), int(colour[2] * sh))
        p.setBrush(col)
        p.setPen(QPen(col, 0.6))
        p.drawPolygon(QPolygonF([QPointF(ox + x * sc, oy + y * sc) for x, y in pts]))
        if ed:
            p.setPen(edge)
            for a, b in ed:
                p.drawLine(QPointF(ox + a[0] * sc, oy + a[1] * sc), QPointF(ox + b[0] * sc, oy + b[1] * sc))
    p.end()
    return pm


# ---------------------------------------------------------------------------
# Repairs (triangles in mm, no Qt)
# ---------------------------------------------------------------------------
def _canon(k):
    """A triangle's corner keys turned so the smallest comes first (same direction kept)."""
    i = k.index(min(k))
    return k[i:] + k[:i]


def clean_triangles(tris, decimals=6):
    """Takes out triangles with no area (corners on top of each other or in a straight line)
    and doubled faces: the same triangle twice is kept once; two the same but facing opposite
    ways (a wall with nothing in it, back to back) are both taken out.
    Returns (tris, no-area removed, doubles removed)."""
    keyed, zero = [], 0
    for t in tris:
        k = tuple((round(c[0], decimals), round(c[1], decimals), round(c[2], decimals)) for c in t)
        if k[0] == k[1] or k[1] == k[2] or k[0] == k[2]:
            zero += 1
            continue
        a, b, c = t
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        L2 = nx * nx + ny * ny + nz * nz
        e2 = max(ux * ux + uy * uy + uz * uz, vx * vx + vy * vy + vz * vz, 1e-30)
        if L2 < 1e-18 or L2 / e2 < 1e-14:
            zero += 1
            continue
        keyed.append((t, _canon(k)))
    first = {}
    drop = set()
    dup = 0
    for i, (t, ck) in enumerate(keyed):
        if ck in first:
            drop.add(i)
            dup += 1
            continue
        rk = _canon((ck[0], ck[2], ck[1]))
        if rk in first and first[rk] not in drop:
            drop.add(i)
            drop.add(first[rk])
            dup += 2
            continue
        first[ck] = i
    return [t for i, (t, _ck) in enumerate(keyed) if i not in drop], zero, dup


def _welded(tris, decimals=6):
    pts, idx, tri = [], {}, []
    for t in tris:
        f = []
        for c in t:
            k = (round(c[0], decimals), round(c[1], decimals), round(c[2], decimals))
            if k not in idx:
                idx[k] = len(pts)
                pts.append(c)
            f.append(idx[k])
        if len(set(f)) == 3:
            tri.append(tuple(f))
    return pts, tri


def edge_report(tris):
    """(open edges, edges shared by more than two faces) for triangles in mm."""
    _pts, tri = _welded(tris)
    cnt = {}
    for a, b, c in tri:
        for e in ((a, b), (b, c), (c, a)):
            k = (e[0], e[1]) if e[0] < e[1] else (e[1], e[0])
            cnt[k] = cnt.get(k, 0) + 1
    return sum(1 for n in cnt.values() if n == 1), sum(1 for n in cnt.values() if n > 2)


def open_edge_segments(tris, limit=4000):
    """The open edges (gaps) as [(p, q)] lines, for showing in red."""
    pts, tri = _welded(tris)
    cnt = {}
    for a, b, c in tri:
        for e in ((a, b), (b, c), (c, a)):
            k = (e[0], e[1]) if e[0] < e[1] else (e[1], e[0])
            cnt[k] = cnt.get(k, 0) + 1
    out = [(pts[a], pts[b]) for (a, b), n in cnt.items() if n == 1]
    return out[:limit]


def fill_holes(tris, max_edges=60):
    """Closes holes: every loop of open edges no longer than max_edges round is filled (a fan
    from its middle), facing the same way as the faces round it. Bigger openings are left -
    they're more likely meant. Returns (tris, holes filled, holes left)."""
    pts, tri = _welded(tris)
    cnt, owner = {}, {}
    for a, b, c in tri:
        for e in ((a, b), (b, c), (c, a)):
            k = (e[0], e[1]) if e[0] < e[1] else (e[1], e[0])
            cnt[k] = cnt.get(k, 0) + 1
            owner[k] = e
    # each open edge (on one face only) runs a->b on its face: the hole runs b->a
    nxt, many = {}, set()
    for k, n_ in cnt.items():
        if n_ != 1:
            continue
        a, b = owner[k]
        if b in nxt:
            many.add(b)
        nxt[b] = a
    used = set()
    new, filled, left = [], 0, 0
    for s in list(nxt):
        if s in used or s in many:
            continue
        loop, v, ok = [s], nxt[s], True
        while v != s:
            if v in many or v not in nxt or v in used or len(loop) > max_edges:
                ok = False
                break
            loop.append(v)
            v = nxt[v]
        for q in loop:
            used.add(q)
        if not ok or len(loop) < 3:
            left += 1
            continue
        if len(loop) == 3:
            new.append(tuple(pts[q] for q in loop))
        else:
            c = tuple(sum(pts[q][k] for q in loop) / len(loop) for k in range(3))
            for i in range(len(loop)):
                new.append((pts[loop[i]], pts[loop[(i + 1) % len(loop)]], c))
        filled += 1
    out = [tuple(pts[q] for q in f) for f in tri] + new
    return out, filled, left


def repair_part(tris, opts):
    """Runs the repairs ticked on the Repair page over one part (mm). Returns (tris, counts)."""
    n = {'zero': 0, 'dup': 0, 'cracks': 0, 'holes': 0, 'holes_left': 0, 'turned': 0, 'inside': 0}
    if opts.get('fix_clean', True):
        tris, n['zero'], n['dup'] = clean_triangles(tris)
    if opts.get('fix_cracks', True):
        tris, f_, l_ = mend_cracks(tris)
        n['cracks'] = max(0, f_ - l_)
    if opts.get('fix_winding', True):
        tris, n['turned'], n['inside'] = fix_winding(tris)
    if opts.get('fix_holes', True):
        tris, n['holes'], n['holes_left'] = fill_holes(tris, int(opts.get('hole_edges', 60) or 60))
        if n['holes'] and opts.get('fix_winding', True):
            tris, t_, i_ = fix_winding(tris)          # a filled solid may now be closed, and inside out
            n['inside'] += i_
    return tris, n


# ---------------------------------------------------------------------------
# Writers for other uses (parts = [(name, (r, g, b), tris)] in the file's own units)
# ---------------------------------------------------------------------------
def _safe(name, keep=" -_."):
    return "".join(ch if (ch.isalnum() or ch in keep) else "_" for ch in str(name)).strip() or "part"


def write_obj_parts(path, parts, colours=True):
    """OBJ with each piece its own object, and (with colours) a .mtl file beside it."""
    base = os.path.splitext(os.path.basename(path))[0]
    mtl = os.path.splitext(path)[0] + ".mtl"
    off = 1
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# %s\n" % PLUGIN_NAME)
        if colours:
            fh.write("mtllib %s.mtl\n" % base)
        for i, (name, col, tris) in enumerate(parts):
            pts, faces = weld(tris)
            fh.write("o %s\n" % _safe(name, "-_."))
            if colours:
                fh.write("usemtl piece_%d\n" % (i + 1))
            for q in pts:
                fh.write("v %.9g %.9g %.9g\n" % tuple(q))
            for a, b, c in faces:
                fh.write("f %d %d %d\n" % (a + off, b + off, c + off))
            off += len(pts)
    if colours:
        with open(mtl, "w", encoding="utf-8") as fh:
            for i, (name, col, _t) in enumerate(parts):
                r, g, b = [x / 255.0 for x in col]
                fh.write("newmtl piece_%d\nKd %.4f %.4f %.4f\nKa 0 0 0\nKs 0.1 0.1 0.1\nd 1\nillum 2\n\n" % (
                    i + 1, r, g, b))
    return [path, mtl] if colours else [path]


def write_ply_parts(path, parts, colours=True):
    """Binary PLY, every piece in one file, each corner in its piece's colour."""
    import struct
    allp, allf = [], []
    for name, col, tris in parts:
        pts, faces = weld(tris)
        o = len(allp)
        allp += [(q, col) for q in pts]
        allf += [(a + o, b + o, c + o) for a, b, c in faces]
    with open(path, "wb") as fh:
        head = ("ply\nformat binary_little_endian 1.0\ncomment %s\nelement vertex %d\n"
                "property float x\nproperty float y\nproperty float z\n" % (PLUGIN_NAME, len(allp)))
        if colours:
            head += "property uchar red\nproperty uchar green\nproperty uchar blue\n"
        head += "element face %d\nproperty list uchar int vertex_indices\nend_header\n" % len(allf)
        fh.write(head.encode("ascii"))
        for q, col in allp:
            fh.write(struct.pack("<3f", *q))
            if colours:
                fh.write(struct.pack("<3B", *[int(max(0, min(255, x))) for x in col]))
        for f in allf:
            fh.write(struct.pack("<B3i", 3, *f))
    return [path]


def _gltf_doc(parts, colours=True):
    """The glTF 2.0 JSON and its binary data: a node, mesh and material for each piece."""
    import struct
    binb = bytearray()
    views, accs, meshes, nodes, mats = [], [], [], [], []
    for name, col, tris in parts:
        pts, faces = weld(tris)
        if not faces:
            continue
        o = len(binb)
        for q in pts:
            binb += struct.pack("<3f", *q)
        views.append({'buffer': 0, 'byteOffset': o, 'byteLength': len(pts) * 12, 'target': 34962})
        accs.append({'bufferView': len(views) - 1, 'componentType': 5126, 'count': len(pts), 'type': 'VEC3',
                     'min': [min(float(q[k]) for q in pts) for k in range(3)],
                     'max': [max(float(q[k]) for q in pts) for k in range(3)]})
        pa = len(accs) - 1
        o = len(binb)
        for f in faces:
            binb += struct.pack("<3I", *f)
        views.append({'buffer': 0, 'byteOffset': o, 'byteLength': len(faces) * 12, 'target': 34963})
        accs.append({'bufferView': len(views) - 1, 'componentType': 5125, 'count': len(faces) * 3, 'type': 'SCALAR'})
        ia = len(accs) - 1
        c = col if colours else (200, 200, 200)
        mats.append({'name': str(name), 'doubleSided': False,
                     'pbrMetallicRoughness': {'baseColorFactor': [round((x / 255.0) ** 2.2, 5) for x in c] + [1.0],
                                              'metallicFactor': 0.0, 'roughnessFactor': 0.8}})
        meshes.append({'name': str(name), 'primitives': [{'attributes': {'POSITION': pa}, 'indices': ia,
                                                          'material': len(mats) - 1}]})
        nodes.append({'name': str(name), 'mesh': len(meshes) - 1})
    while len(binb) % 4:
        binb += b"\0"
    doc = {'asset': {'version': '2.0', 'generator': 'IngeTrazo ' + PLUGIN_NAME},
           'scene': 0, 'scenes': [{'nodes': list(range(len(nodes)))}], 'nodes': nodes, 'meshes': meshes,
           'materials': mats, 'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': len(binb)}]}
    return doc, bytes(binb)


def write_glb(path, parts, colours=True):
    """GLB: glTF 2.0 in one binary file (web pages, games, AR and VR viewers)."""
    import struct
    doc, binb = _gltf_doc(parts, colours)
    js = json.dumps(doc, separators=(",", ":")).encode("utf-8")
    while len(js) % 4:
        js += b" "
    total = 12 + 8 + len(js) + 8 + len(binb)
    with open(path, "wb") as fh:
        fh.write(struct.pack("<III", 0x46546C67, 2, total))
        fh.write(struct.pack("<II", len(js), 0x4E4F534A))
        fh.write(js)
        fh.write(struct.pack("<II", len(binb), 0x004E4942))
        fh.write(binb)
    return [path]


def write_gltf(path, parts, colours=True):
    """glTF 2.0 as a text file with the data inside it."""
    import base64
    doc, binb = _gltf_doc(parts, colours)
    doc['buffers'][0]['uri'] = "data:application/octet-stream;base64," + base64.b64encode(binb).decode("ascii")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    return [path]


def write_vrml(path, parts, colours=True):
    """VRML 2.0 (.wrl), each piece a shape in its own colour - the 3D model format electronics
    design programs use for parts on a circuit board."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("#VRML V2.0 utf8\n# %s\n" % PLUGIN_NAME)
        for name, col, tris in parts:
            pts, faces = weld(tris)
            if not faces:
                continue
            r, g, b = [x / 255.0 for x in (col if colours else (200, 200, 200))]
            fh.write("DEF %s Shape {\n appearance Appearance { material Material { diffuseColor %.4f %.4f %.4f "
                     "specularColor 0.1 0.1 0.1 shininess 0.2 } }\n" % (_safe(name, "_"), r, g, b))
            fh.write(" geometry IndexedFaceSet {\n  creaseAngle 0.5\n  coord Coordinate { point [\n")
            fh.write(",\n".join("   %.7g %.7g %.7g" % tuple(q) for q in pts))
            fh.write("\n  ] }\n  coordIndex [\n")
            fh.write(",\n".join("   %d, %d, %d, -1" % f for f in faces))
            fh.write("\n  ]\n }\n}\n")
    return [path]


def _dxf_head(units_code):
    return ("0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n9\n$INSUNITS\n70\n%d\n0\nENDSEC\n"
            "0\nSECTION\n2\nENTITIES\n" % units_code)


DXF_UNITS = {'mm': 4, 'cm': 5, 'm': 6, 'in': 1, 'tenth': 0}


def _dxf_layer(name):
    return _safe(name, "-_")[:60]


def write_dxf_faces(path, parts, units='mm'):
    """DXF with every triangle as a 3D face, each piece on its own layer (CAD programs)."""
    with open(path, "w", encoding="ascii", errors="replace") as fh:
        fh.write(_dxf_head(DXF_UNITS.get(units, 4)))
        for name, col, tris in parts:
            lay = _dxf_layer(name)
            for a, b, c in tris:
                fh.write("0\n3DFACE\n8\n%s\n" % lay)
                for i, q in enumerate((a, b, c, c)):
                    fh.write("1%d\n%.9g\n2%d\n%.9g\n3%d\n%.9g\n" % (i, q[0], i, q[1], i, q[2]))
        fh.write("0\nENDSEC\n0\nEOF\n")
    return [path]


# ---------------------------------------------------------------------------
# Flat drawings: the edges of each piece seen from one side (laser cutting, plans, elevations)
# ---------------------------------------------------------------------------
def feature_edges(tris, fold=0.94):
    """The lines that show a part's shape: edges where the surface folds by more than about
    20 degrees, or ends. [(p, q)] in the part's own units."""
    import math as _m
    edges = {}

    def k(p):
        return (round(p[0], 6), round(p[1], 6), round(p[2], 6))
    norms = []
    for i, t in enumerate(tris):
        a, b, c = t
        u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        w = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        L = _m.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) or 1.0
        norms.append((n[0] / L, n[1] / L, n[2] / L))
        for e in range(3):
            p, q = t[e], t[(e + 1) % 3]
            kp, kq = k(p), k(q)
            key = (kp, kq) if kp < kq else (kq, kp)
            edges.setdefault(key, [p, q, []])[2].append(i)
    out = []
    for p, q, ts in edges.values():
        if len(ts) != 2:
            out.append((p, q))
            continue
        n1, n2 = norms[ts[0]], norms[ts[1]]
        if n1[0] * n2[0] + n1[1] * n2[1] + n1[2] * n2[2] < fold:
            out.append((p, q))
    return out


def project_view(segs, view):
    """3D lines to flat ones for a view: plan (from above), front or side. 2D y points up."""
    if view == 'front':
        f = lambda p: (p[0], p[2])
    elif view == 'side':
        f = lambda p: (p[1], p[2])
    else:
        f = lambda p: (p[0], p[1])
    out, seen = [], set()
    for p, q in segs:
        a, b = f(p), f(q)
        ka = (round(a[0], 4), round(a[1], 4))
        kb = (round(b[0], 4), round(b[1], 4))
        if ka == kb:
            continue
        key = (ka, kb) if ka < kb else (kb, ka)
        if key in seen:
            continue
        seen.add(key)
        out.append((a, b))
    return out


def drawing_sheets(parts, view, gap=10.0):
    """The flat drawings laid side by side: [(name, colour, [(a, b)] in mm, (x0, y0) offset)],
    and the total (width, height)."""
    views = ['top', 'front', 'side'] if view == 'all' else [view]
    out = []
    x = 0.0
    height = 0.0
    for v in views:
        y = 0.0
        colw = 0.0
        for name, col, tris in parts:
            lines = project_view(feature_edges(tris), v)
            if not lines:
                continue
            xs = [c[0] for ln in lines for c in ln]
            ys = [c[1] for ln in lines for c in ln]
            w, h = max(xs) - min(xs), max(ys) - min(ys)
            dx, dy = x - min(xs), y - min(ys)
            out.append(("%s - %s" % (name, v) if view == 'all' else name, col,
                        [((a[0] + dx, a[1] + dy), (b[0] + dx, b[1] + dy)) for a, b in lines]))
            y += h + gap
            colw = max(colw, w)
        height = max(height, y - gap)
        x += colw + gap * 2
    return out, (max(0.0, x - gap * 2), max(0.0, height))


def write_dxf_lines(path, parts, view='top', units='mm'):
    """A flat DXF of each piece's edges (laser cutters, CNC, 2D CAD), each piece on its layer."""
    sheets, _size = drawing_sheets(parts, view)
    with open(path, "w", encoding="ascii", errors="replace") as fh:
        fh.write(_dxf_head(DXF_UNITS.get(units, 4)))
        for name, col, lines in sheets:
            lay = _dxf_layer(name)
            for a, b in lines:
                fh.write("0\nLINE\n8\n%s\n10\n%.9g\n20\n%.9g\n30\n0\n11\n%.9g\n21\n%.9g\n31\n0\n" % (
                    lay, a[0], a[1], b[0], b[1]))
        fh.write("0\nENDSEC\n0\nEOF\n")
    return [path]


def write_svg_lines(path, parts, view='top', units='mm', colours=True, title="", scale_note=""):
    """An SVG drawing at true size (it prints the right size at 100 %), each piece in a group of
    its own, with a 10 mm (or 1 inch) bar to check the size."""
    from xml.sax.saxutils import escape
    sheets, (W, H) = drawing_sheets(parts, view)
    unit = {'mm': 'mm', 'cm': 'cm', 'in': 'in'}.get(units, 'mm')
    m = 8.0 if unit == 'mm' else (0.8 if unit == 'cm' else 0.3)
    bar = 10.0 if unit == 'mm' else (1.0 if unit in ('cm', 'in') else 10.0)
    W2, H2 = W + 2 * m, H + 2 * m + 3 * m
    lw = {'mm': 0.1, 'cm': 0.01, 'in': 0.004}.get(unit, 0.1)
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="%.4f%s" height="%.4f%s" viewBox="0 0 %.4f %.4f">'
           % (W2, unit, H2, unit, W2, H2),
           '<title>%s</title>' % escape(title or PLUGIN_NAME)]
    for name, col, lines in sheets:
        c = "rgb(%d,%d,%d)" % tuple(int(x * 0.7) for x in col) if colours else "black"
        out.append('<g id="%s" fill="none" stroke="%s" stroke-width="%.4f" stroke-linecap="round">'
                   % (escape(_safe(name, "-_")), c, lw))
        for a, b in lines:
            out.append('<line x1="%.5f" y1="%.5f" x2="%.5f" y2="%.5f"/>' % (
                a[0] + m, H + m - a[1], b[0] + m, H + m - b[1]))
        out.append('</g>')
    y = H + m + 2 * m
    out.append('<g stroke="black" stroke-width="%.4f"><line x1="%.4f" y1="%.4f" x2="%.4f" y2="%.4f"/>'
               '<line x1="%.4f" y1="%.4f" x2="%.4f" y2="%.4f"/><line x1="%.4f" y1="%.4f" x2="%.4f" y2="%.4f"/></g>'
               % (lw * 2, m, y, m + bar, y, m, y - m * 0.3, m, y + m * 0.3, m + bar, y - m * 0.3, m + bar, y + m * 0.3))
    out.append('<text x="%.4f" y="%.4f" font-family="sans-serif" font-size="%.4f">%g %s%s</text>' % (
        m + bar + m * 0.5, y + m * 0.25, m * 0.6, bar, unit, ("   " + escape(scale_note)) if scale_note else ""))
    out.append('</svg>')
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    return [path]


def _one_file_writer(fn):
    """Wraps a printing writer (one lot of triangles) to take pieces: all in one file."""
    def w(path, parts, **_kw):
        fn(path, [t for _n, _c, tr in parts for t in tr], os.path.splitext(os.path.basename(path))[0])
        return [path]
    return w


def _3mf_writer(path, parts, **_kw):
    if len(parts) > 1:
        write_3mf_parts(path, [(n, tr) for n, _c, tr in parts])
    else:
        write_3mf(path, parts[0][2], parts[0][0])
    return [path]


# key: (label, extension, writer, kind, what it's for)
#   kind: 'mesh' (3D), 'lines' (flat drawing), 'picture'
FORMATS = [
    ('3mf', "3MF - for slicers (pieces stay separate)", ".3mf", _3mf_writer, 'mesh',
     "3D printing. Most slicers like 3MF best: one file, every piece a separate item, in mm."),
    ('stl', "STL - binary", ".stl", _one_file_writer(write_stl), 'mesh',
     "3D printing, and almost any 3D program. Shape only - no colours, no names. With pieces split "
     "and 'Each piece in its own file' ticked, one STL per piece in a new folder."),
    ('stla', "STL - text (ASCII)", ".stl", _one_file_writer(write_stl_ascii), 'mesh',
     "The same as STL, as readable text - for older programs that want it. Much bigger files."),
    ('obj', "OBJ + MTL - with piece colours", ".obj", write_obj_parts, 'mesh',
     "Other 3D modelling, rendering and animation programs. Each piece is a named object with its "
     "colour (in a .mtl file saved beside it). Most of them expect Y up."),
    ('ply', "PLY - with piece colours", ".ply", write_ply_parts, 'mesh',
     "3D scanning and mesh-repair programs. Colours stored on the corners."),
    ('glb', "GLB - web, games, AR and VR", ".glb", write_glb, 'mesh',
     "One small file for web pages, game engines, phone AR viewers and VR. Pieces are named, with "
     "colours. The format is in metres with Y up, so pick Metres and Y up."),
    ('gltf', "glTF - web and games (text)", ".gltf", write_gltf, 'mesh',
     "The same as GLB as a text file - easier to look inside. Metres, Y up."),
    ('wrl', "VRML (.wrl) - electronics 3D models", ".wrl", write_vrml, 'mesh',
     "VRML 2.0 with colours. Circuit-board design programs use it for the 3D look of parts "
     "(they usually want tenths of an inch, Z up). Also opens in many older 3D viewers."),
    ('dxf3d', "DXF - 3D faces (CAD)", ".dxf", write_dxf_faces, 'mesh',
     "CAD programs. Every triangle as a 3D face, each piece on its own layer."),
    ('dxf2d', "DXF - flat outline drawing (laser, CNC, 2D CAD)", ".dxf", write_dxf_lines, 'lines',
     "Laser cutters, vinyl and CNC cutters, 2D CAD. The edges of each piece seen from one side, "
     "true size. For cutting, tick 'Lay each piece flat' (Pieces page) and use 'Seen from above'. "
     "Every edge is drawn, as if the part were glass."),
    ('svg', "SVG - flat outline drawing (true size)", ".svg", write_svg_lines, 'lines',
     "Laser cutters and cutting machines, drawing programs, and printing on paper: prints at true "
     "size at 100 %, with a 10 mm bar to check. Plans, elevations, templates."),
    ('png', "PNG - picture of the preview", ".png", None, 'picture',
     "A picture of the preview as it is now - for web pages, forums, video thumbnails."),
]
FMT = {f[0]: f for f in FORMATS}

# what it's for -> the settings that suit it
PURPOSES = [
    ("3D printing (FDM, filament)", 'print', {'format': '3mf', 'file_unit': 'mm', 'y_up': False, 'use_scale': True,
                                              'layout': 'bed', 'apply_fixes': True, 'colours': False}),
    ("3D printing (resin)", 'resin', {'format': 'stl', 'file_unit': 'mm', 'y_up': False, 'use_scale': True,
                                      'layout': 'bed', 'apply_fixes': True, 'colours': False}),
    ("Other 3D modelling and rendering programs", 'model3d', {'format': 'obj', 'file_unit': 'm', 'y_up': True,
                                                              'use_scale': False, 'layout': 'keep',
                                                              'apply_fixes': False, 'colours': True}),
    ("Web pages, games, AR and VR", 'web', {'format': 'glb', 'file_unit': 'm', 'y_up': True, 'use_scale': False,
                                            'layout': 'centre', 'apply_fixes': True, 'colours': True}),
    ("CAD (3D)", 'cad', {'format': 'dxf3d', 'file_unit': 'mm', 'y_up': False, 'use_scale': False,
                         'layout': 'keep', 'apply_fixes': False, 'colours': False}),
    ("Laser cutting / CNC (flat outlines)", 'laser', {'format': 'dxf2d', 'file_unit': 'mm', 'y_up': False,
                                                      'use_scale': True, 'layout': 'bed', 'apply_fixes': False,
                                                      'colours': False, 'view': 'top', 'lay_flat': True}),
    ("Drawings: plan, front and side (SVG)", 'drawing', {'format': 'svg', 'file_unit': 'mm', 'y_up': False,
                                                         'use_scale': True, 'layout': 'keep',
                                                         'apply_fixes': False, 'colours': True, 'view': 'all'}),
    ("Electronics: 3D model of a part (VRML)", 'pcb', {'format': 'wrl', 'file_unit': 'tenth', 'y_up': False,
                                                       'use_scale': False, 'layout': 'centre',
                                                       'apply_fixes': True, 'colours': True}),
    ("A picture of it (PNG)", 'picture', {'format': 'png'}),
    ("My own choice", 'own', {}),
]


def to_file(parts, unit_mm, y_up):
    """Pieces in mm, Z up -> the file's units, and Y up if asked (turned, not mirrored)."""
    s = 1.0 / unit_mm
    out = []
    for name, col, tris in parts:
        if y_up:
            tr = [tuple((c[0] * s, c[2] * s, -c[1] * s) for c in t) for t in tris]
        else:
            tr = [tuple((c[0] * s, c[1] * s, c[2] * s) for c in t) for t in tris]
        out.append((name, col, tr))
    return out


def tris_size(tris):
    if not tris:
        return (0.0, 0.0, 0.0)
    return tuple(max(c[k] for t in tris for c in t) - min(c[k] for t in tris for c in t) for k in range(3))


def stand_centred(tris):
    """Centred on the origin, standing on z = 0."""
    if not tris:
        return tris
    xs = [c[0] for t in tris for c in t]
    ys = [c[1] for t in tris for c in t]
    zs = [c[2] for t in tris for c in t]
    ox, oy, oz = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)
    return [tuple((c[0] - ox, c[1] - oy, c[2] - oz) for c in t) for t in tris]


def scale_tris(tris, f):
    fx, fy, fz = f
    return [tuple((c[0] * fx, c[1] * fy, c[2] * fz) for c in t) for t in tris]


def biggest_that_fits(size_mm, bed):
    """The biggest factor that fits size_mm (x, y, z) on the bed (x, y, z), either way round."""
    sx, sy, sz = [max(1e-12, v) for v in size_mm]
    bx, by, bz = bed
    flat = max(min(bx / sx, by / sy), min(bx / sy, by / sx))
    return min(flat, bz / sz)


# words found in the names of slicer programs (FDM and resin): used only to look for them
SLICER_HINTS = ("slicer", "cura", "chitubox", "lychee", "bambu", "orca", "simplify3d", "ideamaker",
                "voxeldance", "photon", "halot", "anycubic", "elegoo", "flashprint", "creality", "kisslicer")


def find_slicer_programs(limit=40):
    """Slicer programs in the usual program folders (a few levels down): their full paths."""
    roots = []
    for var in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432", "LOCALAPPDATA"):
        d = os.environ.get(var)
        if d:
            roots.append(d if var != "LOCALAPPDATA" else os.path.join(d, "Programs"))
    if os.name != 'nt':
        roots += ["/usr/bin", "/opt", "/Applications", os.path.expanduser("~/Applications")]
    found, seen = [], set()
    skip = ("uninstall", "unins", "update", "crash", "helper", "console", "engine", "setup")
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirs, files in os.walk(root):
            depth = dirpath[len(root):].count(os.sep)
            if depth >= 3:
                dirs[:] = []
            here = dirpath.lower()
            for fn in files:
                low = fn.lower()
                if not (low.endswith(".exe") or os.name != 'nt') or any(k in low for k in skip):
                    continue
                if any(h in low for h in SLICER_HINTS) or (any(h in here for h in SLICER_HINTS)
                                                           and low.endswith(".exe")
                                                           and os.path.splitext(low)[0] in here):
                    full = os.path.join(dirpath, fn)
                    if full.lower() not in seen:
                        seen.add(full.lower())
                        found.append(full)
                        if len(found) >= limit:
                            return found
    return sorted(found, key=lambda x: os.path.basename(x).lower())


def lay_out_packed(parts, bed_w, bed_d, gap):
    """Lays pieces (mm, already standing as they'll print) close together in the middle of the bed:
    biggest first, in rows only as wide as a tidy block needs (not stretched across the whole bed),
    each standing on z = 0, the block centred on the origin. Returns (parts moved, (w, d, h))."""
    info = []
    for name, tris in parts:
        xs = [c[0] for t in tris for c in t]
        ys = [c[1] for t in tris for c in t]
        zs = [c[2] for t in tris for c in t]
        info.append((name, tris, min(xs), min(ys), min(zs), max(xs) - min(xs), max(ys) - min(ys)))
    if not info:
        return [], (0.0, 0.0, 0.0)
    area = sum((w + gap) * (d + gap) for *_x, w, d in info)
    widest = max(w for *_x, w, d in info)
    row_w = max(widest, min(bed_w if bed_w > 0 else 1e9, math.sqrt(area) * 1.15))
    order = sorted(range(len(info)), key=lambda i: (-info[i][6], -info[i][5]))   # deepest first: neat rows
    placed = [None] * len(info)
    x = y = row_d = 0.0
    for i in order:
        name, tris, x0, y0, z0, w, d = info[i]
        if x > 0 and x + w > row_w + 1e-9:
            x, y, row_d = 0.0, y + row_d + gap, 0.0
        dx, dy, dz = x - x0, y - y0, -z0
        placed[i] = (name, [tuple((c[0] + dx, c[1] + dy, c[2] + dz) for c in t) for t in tris])
        x += w + gap
        row_d = max(row_d, d)
    allx = [c[0] for _n, tr in placed for t in tr for c in t]
    ally = [c[1] for _n, tr in placed for t in tr for c in t]
    allz = [c[2] for _n, tr in placed for t in tr for c in t]
    cx, cy = (min(allx) + max(allx)) / 2, (min(ally) + max(ally)) / 2
    placed = [(n, [tuple((c[0] - cx, c[1] - cy, c[2]) for c in t) for t in tr]) for n, tr in placed]
    return placed, (max(allx) - min(allx), max(ally) - min(ally), max(allz) - min(allz))


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


# ---------------------------------------------------------------------------
# The converter: a strip in the toolbar, and the same as a page in the window
# ---------------------------------------------------------------------------
EDDY_TIPS = {'@cb_scale': "The model scale to convert to. Pick 'Custom' to type your own.",
             '@cb_real_units': "Which real-world units to show: feet and inches, mm, or both.",
             '@cb_model_units': "Which model units to show: mm, inches, or both."}
EDDY_TIPS_END = None

_CONVERTERS = []          # every converter open, so typing in one shows in the others


class ConverterStrip(QWidget):
    def __init__(self, cur, parent=None, page=False, studio_button=False):
        super().__init__(parent)
        self._busy = False
        self.page = page

        def dspin(val, dec, hi, suffix, width):
            s = QDoubleSpinBox()
            s.setDecimals(dec)
            s.setRange(0.0, hi)
            s.setSuffix(suffix)
            s.setValue(val)
            s.setKeyboardTracking(False)
            s.setMinimumWidth(width)
            if not page:
                s.setButtonSymbols(QDoubleSpinBox.NoButtons)
            return s

        def unit_list(options, current):
            cb = QComboBox()
            for text, key in options:
                cb.addItem(text, key)
            i = cb.findData(current)
            cb.setCurrentIndex(i if i >= 0 else len(options) - 1)
            return cb

        self.cb_scale = QComboBox()
        for text, n in SCALES:
            self.cb_scale.addItem(text, n)
        idx = len(SCALES) - 1
        for i, (_, n) in enumerate(SCALES):
            if n is not None and abs(n - cur['scale']) < 1e-9:
                idx = i
        self.cb_scale.setCurrentIndex(idx)
        self.sp_custom = dspin(cur['scale'], 2, 10000.0, "", 60)
        self.sp_custom.setRange(1.0, 10000.0)
        self.sp_custom.setPrefix("1:")
        self.sp_custom.setToolTip("The scale as a number. Picking a scale in the list fills it in; type your own "
                                  "here and the list changes to Custom.")
        self.sp_ft = QSpinBox()
        self.sp_ft.setRange(0, REAL_MAX_FT)          # matches the mm box's limit
        self.sp_ft.setSuffix(" ft")
        self.sp_ft.setKeyboardTracking(False)
        if not page:
            self.sp_ft.setButtonSymbols(QSpinBox.NoButtons)
        self.sp_ft.setMinimumWidth(55)
        self.sp_in = dspin(0.0, 3, 11.999, " in", 70)
        self.sp_real = dspin(cur['real_mm'], 1, REAL_MAX_MM, " mm", 90)
        self.sp_ft.setToolTip("Real-world size: feet")
        self.sp_in.setToolTip("Real-world size: inches")
        self.sp_real.setToolTip("Real-world size in millimetres")
        self.cb_real_units = unit_list(REAL_UNITS, cur.get('real_units'))
        self.sp_model = dspin(0.0, 3, 100000.0, " mm", 85)
        self.sp_model_in = dspin(0.0, 4, 10000.0, " in", 80)
        self.sp_model.setToolTip("Size on the model in millimetres")
        self.sp_model_in.setToolTip("Size on the model in inches")
        self.cb_model_units = unit_list(MODEL_UNITS, cur.get('model_units'))

        if page:
            # each row: its boxes side by side from the left (hidden ones take no room), then the units
            form = QFormLayout(self)
            try:
                form.setRowWrapPolicy(getattr(QFormLayout, 'DontWrapRows', None) or
                                      QFormLayout.RowWrapPolicy.DontWrapRows)
            except Exception:
                pass

            def line(*ws):
                h = QHBoxLayout()
                h.setSpacing(6)
                for w in ws:
                    h.addWidget(w)
                h.addStretch(1)
                return h
            for w in (self.sp_ft, self.sp_in, self.sp_real, self.sp_model, self.sp_model_in, self.sp_custom):
                w.setMinimumWidth(90)
            self.cb_real_units.setToolTip("Which real-world units to show: feet and inches, mm, or both.")
            self.cb_model_units.setToolTip("Which model units to show: mm, inches, or both.")
            form.addRow("Scale:", line(self.cb_scale, self.sp_custom))
            form.addRow("Real size:", line(self.sp_ft, self.sp_in, self.sp_real))
            form.addRow("   show in:", line(self.cb_real_units))
            form.addRow("Model size:", line(self.sp_model, self.sp_model_in))
            form.addRow("   show in:", line(self.cb_model_units))
            note = QLabel("Type in any box and the others follow. Real sizes are the full-size thing; "
                          "model sizes are what you make or print at the scale above.")
            note.setWordWrap(True)
            form.addRow(note)
        else:
            row = QHBoxLayout(self)
            row.setContentsMargins(4, 0, 4, 0)
            row.setSpacing(4)

            def sep():
                line = QFrame()
                line.setFrameShape(QFrame.VLine)
                line.setFrameShadow(QFrame.Sunken)
                row.addWidget(line)
            row.addWidget(QLabel("Scale:"))
            row.addWidget(self.cb_scale)
            row.addWidget(self.sp_custom)
            sep()
            row.addWidget(QLabel("Real:"))
            for w in (self.sp_ft, self.sp_in, self.sp_real, self.cb_real_units):
                row.addWidget(w)
            sep()
            row.addWidget(QLabel("Model:"))
            for w in (self.sp_model, self.sp_model_in, self.cb_model_units):
                row.addWidget(w)
            if studio_button:
                sep()
                b = QPushButton("Studio...")
                b.setToolTip("Opens the %s window: scale objects in the work area, split them into "
                             "pieces, repair and export them (Ctrl+Alt+K)." % PLUGIN_NAME)
                b.clicked.connect(lambda *_: open_studio())
                row.addWidget(b)

        self.cb_real_units.currentIndexChanged.connect(self.units_changed)
        self.cb_model_units.currentIndexChanged.connect(self.units_changed)
        self.units_changed()
        self.cb_scale.currentIndexChanged.connect(self.scale_changed)
        self.sp_custom.valueChanged.connect(self.custom_typed)
        self.sp_ft.valueChanged.connect(lambda *_: self.edited('ftin'))
        self.sp_in.valueChanged.connect(lambda *_: self.edited('ftin'))
        self.sp_real.valueChanged.connect(lambda *_: self.edited('real'))
        self.sp_model.valueChanged.connect(lambda *_: self.edited('model'))
        self.sp_model_in.valueChanged.connect(lambda *_: self.edited('model_in'))
        self.scale_changed()
        _CONVERTERS.append(self)

    def units_changed(self, *_):
        """Shows only the boxes for the units picked. Hidden boxes still keep up,
        so switching back shows the right numbers straight away."""
        r = self.cb_real_units.currentData()
        m = self.cb_model_units.currentData()
        self.sp_ft.setVisible(r in ('ftin', 'both'))
        self.sp_in.setVisible(r in ('ftin', 'both'))
        self.sp_real.setVisible(r in ('mm', 'both'))
        self.sp_model.setVisible(m in ('mm', 'both'))
        self.sp_model_in.setVisible(m in ('in', 'both'))
        update_settings(real_units=r, model_units=m)

    def scale(self):
        n = self.cb_scale.currentData()
        return n if n else self.sp_custom.value()

    def custom_typed(self, v):
        """A scale typed in the box: the list shows it (by name if it has one, else Custom)."""
        if self._busy:
            return
        n = self.cb_scale.currentData()
        if n is None or abs(n - v) > 1e-9:
            j = next((i for i, (_t, x) in enumerate(SCALES) if x is not None and abs(x - v) < 1e-9),
                     len(SCALES) - 1)
            self.cb_scale.blockSignals(True)
            self.cb_scale.setCurrentIndex(j)
            self.cb_scale.blockSignals(False)
        self.edited('real')

    def scale_changed(self, *_):
        n = self.cb_scale.currentData()
        if n:
            self.sp_custom.blockSignals(True)
            self.sp_custom.setValue(n)
            self.sp_custom.blockSignals(False)
        self.edited('real')          # keep the real size, work out the new model size

    def show_values(self, scale, real_mm):
        """Shows another converter's scale and size (no saving, no passing on)."""
        if self._busy:
            return
        self._busy = True
        try:
            idx = len(SCALES) - 1
            for i, (_, n) in enumerate(SCALES):
                if n is not None and abs(n - scale) < 1e-9:
                    idx = i
            self.cb_scale.blockSignals(True)
            self.cb_scale.setCurrentIndex(idx)
            self.cb_scale.blockSignals(False)
            self.sp_custom.blockSignals(True)
            self.sp_custom.setValue(scale)
            self.sp_custom.blockSignals(False)
            ft, inch = mm_to_ft_in(real_mm)
            self.sp_ft.setValue(ft)
            self.sp_in.setValue(inch)
            self.sp_real.setValue(real_mm)
            self.sp_model.setValue(real_mm / scale)
            self.sp_model_in.setValue(real_mm / scale / MM_PER_INCH)
        finally:
            self._busy = False

    def edited(self, which):
        if self._busy:
            return
        self._busy = True
        try:
            n = self.scale()
            if which == 'ftin':
                real = ft_in_to_mm(self.sp_ft.value(), self.sp_in.value())
            elif which == 'real':
                real = self.sp_real.value()
            elif which == 'model':
                real = self.sp_model.value() * n
            else:
                real = self.sp_model_in.value() * MM_PER_INCH * n
            ft, inch = mm_to_ft_in(real)
            if which != 'ftin':
                self.sp_ft.setValue(ft)
                self.sp_in.setValue(inch)
            if which != 'real':
                self.sp_real.setValue(real)
            if which != 'model':
                self.sp_model.setValue(real / n)
            if which != 'model_in':
                self.sp_model_in.setValue(real / n / MM_PER_INCH)
        finally:
            self._busy = False
        update_settings(scale=self.scale(), real_mm=self.sp_real.value())
        for other in list(_CONVERTERS):
            if other is not self:
                try:
                    other.show_values(self.scale(), self.sp_real.value())
                except Exception:          # closed (its window has gone): forget it
                    try:
                        _CONVERTERS.remove(other)
                    except Exception:
                        pass


# ---------------------------------------------------------------------------
# Planning the pieces (the same window as in 3D Print Scaler)
# ---------------------------------------------------------------------------
class PieceCanvas(QWidget):
    """A picture of the parts, each in its piece's colour, outlined where the surfaces fold.
    Click a part to pick it (Ctrl / Shift for more); the mouse wheel zooms in on the pointer;
    drag with the right (or middle) button to move the picture; double-click to fit it again."""

    def __init__(self, dlg):
        super().__init__(dlg)
        self.dlg = dlg
        self.setMinimumSize(200, 180)          # small enough for a narrow window
        self.az = 52.0
        self.el = 32.0                  # negative: looking up from underneath
        self.zoom, self.pan = 1.0, (0.0, 0.0)
        self._drag = None
        self._spin = None
        self.prep = [_prep_part(lf[3]) for lf in dlg.leaves]
        # for the big picture, big triangles are cut smaller so they sort properly
        pts = [q for pp in self.prep for t, _n, _f in pp for q in t]
        span = max(max(q[k] for q in pts) - min(q[k] for q in pts) for k in range(3)) if pts else 1.0
        size = span / 15.0
        for _try in range(5):                  # no more pieces than the picture can draw quickly
            self.big = [_split_big(pp, size) for pp in self.prep]
            if sum(len(b) for b in self.big) <= 30000:
                break
            size *= 1.6
        # the model's middle and size: the picture keeps the same scale and centre however it's turned
        import math
        if pts:
            c3 = tuple((max(q[k] for q in pts) + min(q[k] for q in pts)) / 2.0 for k in range(3))
            self.centre = c3
            self.radius = max(1e-9, max(math.sqrt(sum((q[k] - c3[k]) ** 2 for k in range(3))) for q in pts[::max(1, len(pts) // 5000)]))
        else:
            self.centre, self.radius = (0.0, 0.0, 0.0), 1.0
        self.items = []
        self.boxes = None
        self.moving = False             # while the mouse is turning or moving it: a quick picture
        self._need_view = False
        self._settle_n = 0
        self.view()

    def _start_moving(self):
        """Quick pictures while the mouse moves; the full one a moment after it stops."""
        self.moving = True
        self._settle_n += 1
        n = self._settle_n
        try:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(220, lambda: self._settle(n))
        except Exception:
            pass

    def _settle(self, n):
        if n != self._settle_n or self._spin is not None:
            return
        self.moving = False
        self._need_view = True
        self.update()

    def view(self, fast=False):
        """Works out the picture. fast: a thinned-out one, quick enough to follow the mouse while
        you turn the model (the full one is drawn when you let go)."""
        import math
        D, R, U = _view_axes(self.az, self.el)
        self.axes = (D, R, U)
        items = []
        # the same pieces while moving as when still, so the picture looks the same as it turns
        # (only the smoothing is left off while it moves, which is what makes it quick)
        for i, pp in enumerate(self.big):
            items += _project(pp, D, R, U, i)
        items.sort(key=lambda e: -e[0])
        self.items = items
        if items:
            # frame what's showing (one object on its own fills the picture)
            try:
                vis = [e for e in items if self.dlg.shown(e[1])] or items
            except Exception:
                vis = items
            xs = [x for e in vis for x, _ in e[2]]
            ys = [y for e in vis for _, y in e[2]]
            self.boxes = (min(xs), max(xs), min(ys), max(ys))

    def _map(self):
        # scaled to the model's size and centred on its middle - the same however it's turned,
        # so it turns smoothly in place instead of jumping about
        _D, R, U = self.axes
        c = self.centre
        cx = c[0] * R[0] + c[1] * R[1] + c[2] * R[2]
        cy = -(c[0] * U[0] + c[1] * U[1] + c[2] * U[2])
        w, h = self.width() - 20, self.height() - 20
        sc = min(w, h) / (2.0 * self.radius) * 1.05 * self.zoom
        ox = 10 + w / 2 - cx * sc + self.pan[0]
        oy = 10 + h / 2 - cy * sc + self.pan[1]
        return sc, ox, oy

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen, QLinearGradient, QBrush
        from PySide6.QtCore import QPointF, Qt
        if self._need_view:
            self._need_view = False
            self.view(fast=self.moving)
        p = QPainter(self)
        if not self.moving:
            p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0.0, QColor(252, 252, 250))
        g.setColorAt(1.0, QColor(222, 226, 230))
        p.fillRect(self.rect(), QBrush(g))
        if not self.items:
            p.drawText(self.rect(), Qt.AlignCenter, "Nothing to show")
            p.end()
            return
        sc, ox, oy = self._map()
        picked = set(self.dlg.picked_rows())
        edge = QPen(QColor(35, 35, 35), 0.9)
        edge_pick = QPen(QColor(0, 0, 0), 1.6)
        quick = max(1, len(self.items) // 25000) if self.moving else 1
        for n_, (_d, i, pts, sh, ed) in enumerate(self.items):
            if quick > 1 and n_ % quick:
                continue
            if not self.dlg.shown(i):
                continue
            base = self.dlg.colour_of(i)
            if i in picked:
                base = (255, 225, 40)              # the parts you've picked show up bright yellow
            col = QColor(int(base[0] * sh), int(base[1] * sh), int(base[2] * sh))
            p.setBrush(col)
            p.setPen(QPen(col, 0.7))
            p.drawPolygon(QPolygonF([QPointF(ox + x * sc, oy + y * sc) for x, y in pts]))
            if ed:
                p.setPen(edge_pick if i in picked else edge)
                for a, b in ed:
                    p.drawLine(QPointF(ox + a[0] * sc, oy + a[1] * sc), QPointF(ox + b[0] * sc, oy + b[1] * sc))
        p.setPen(QColor(90, 90, 90))
        p.drawText(8, self.height() - 8, "Left-drag: turn   Wheel: zoom   Right-drag: move   Right-click: menu   "
                                         "Double-click: fit   Click: pick   Ctrl+click: pick more   "
                                         "Shift+click: un-pick")
        p.end()

    def _pos(self, ev):
        try:
            q = ev.position()
            return q.x(), q.y()
        except Exception:
            return ev.x(), ev.y()

    def wheelEvent(self, ev):
        if not self.boxes:
            return
        try:
            dy = ev.angleDelta().y()
        except Exception:
            dy = 0
        if not dy:
            return
        mx, my = self._pos(ev)
        sc, ox, oy = self._map()
        wx, wy = (mx - ox) / sc, (my - oy) / sc          # the point under the pointer stays put
        f = 1.15 ** (dy / 120.0)
        self.zoom = max(0.3, min(60.0, self.zoom * f))
        sc2, ox2, oy2 = self._map()
        self.pan = (self.pan[0] + mx - (ox2 + wx * sc2), self.pan[1] + my - (oy2 + wy * sc2))
        self._start_moving()
        self.update()

    def mouseDoubleClickEvent(self, ev):
        self.zoom, self.pan = 1.0, (0.0, 0.0)
        self.update()

    def mouseMoveEvent(self, ev):
        mx, my = self._pos(ev)
        if self._spin is not None:
            x0_, y0_, az0, el0, add, moved = self._spin
            if not moved and abs(mx - x0_) + abs(my - y0_) <= 4:
                return
            self._spin = (x0_, y0_, az0, el0, add, True)
            # left-drag turns the model: across turns it round, up and down tilts it
            self.az = (az0 - (mx - x0_) * 0.45) % 360.0
            self.el = max(-85.0, min(85.0, el0 + (my - y0_) * 0.35))
            self.moving = True
            self._need_view = True           # worked out when it's drawn: only once however many moves
            self.update()
            return
        if self._drag is None:
            return
        self.pan = (self._drag[2] + mx - self._drag[0], self._drag[3] + my - self._drag[1])
        self._start_moving()
        self.update()

    def mouseReleaseEvent(self, ev):
        sp, self._spin = self._spin, None
        if sp is not None:
            if sp[5]:
                self.moving = False
                self._need_view = True         # the full picture again
                self.update()
                try:
                    self.dlg.b_below.setText("Look from above" if self.el < 0 else "Look from below")
                except Exception:
                    pass
            else:
                i = self.part_at(sp[0], sp[1])  # a click, not a turn: pick what's under it
                if i is not None:
                    self.dlg.pick_part(i, sp[4])
            return
        d, self._drag = self._drag, None
        if d is None or len(d) < 5 or not d[4]:
            return
        mx, my = self._pos(ev)
        if abs(mx - d[0]) + abs(my - d[1]) <= 4:
            # a right-click (not a drag): pick the part under the pointer if it isn't picked, then the menu
            i = self.part_at(mx, my)
            if i is not None and i not in set(self.dlg.picked_rows()):
                self.dlg.pick_row(i, False)
            try:
                gp = ev.globalPosition().toPoint()
            except Exception:
                gp = ev.globalPos()
            self.dlg.context_menu(gp)

    def part_at(self, mx, my):
        """The nearest shown part under the pointer, or None."""
        if not self.items:
            return None
        sc, ox, oy = self._map()
        x, y = (mx - ox) / sc, (my - oy) / sc

        def inside(pts):
            (ax, ay), (bx, by), (cx, cy) = pts
            d1 = (x - bx) * (ay - by) - (ax - bx) * (y - by)
            d2 = (x - cx) * (by - cy) - (bx - cx) * (y - cy)
            d3 = (x - ax) * (cy - ay) - (cx - ax) * (y - ay)
            return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))
        for _d, i, pts, _sh, _ed in reversed(self.items):
            if self.dlg.shown(i) and inside(pts):
                return i
        return None

    def mousePressEvent(self, ev):
        if not self.items:
            return
        from PySide6.QtCore import Qt
        mx, my = self._pos(ev)
        try:
            btn = ev.button()
            if btn in (Qt.RightButton, Qt.MiddleButton):
                # the last flag: a right button that doesn't move opens the menu on release
                self._drag = (mx, my, self.pan[0], self.pan[1], btn == Qt.RightButton)
                return
        except Exception:
            pass
        # Ctrl+click picks more, Shift+click un-picks, a plain click picks just that one
        mode = 'only'
        try:
            mods = ev.modifiers()
            if mods & (Qt.ShiftModifier | Qt.AltModifier):
                mode = 'remove'
            elif mods & Qt.ControlModifier:
                mode = 'add'
        except Exception:
            pass
        self._spin = (mx, my, self.az, self.el, mode, False)


class PiecesDialog(QDialog):
    """Shows every part of the selection; you pick parts and put them into print pieces, each
    piece its own colour. Parts in no piece print on their own."""

    def __init__(self, parent, leaves, plan, targets=None, objects=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QTableWidget, QAbstractItemView, QSplitter
        self.setWindowTitle(PLUGIN_NAME + " - Plan the print pieces")
        self.leaves = leaves
        self.pieces = list((plan or {}).get('pieces', []))
        keys = (plan or {}).get('keys', {})
        known = set(k for k, _n, _kd, _t in leaves)
        self.keys = {k: p for k, p in keys.items() if k in known and p in self.pieces}
        # pieces to close the holes in, and which slicer each piece goes to ("" = parts on their own)
        self.close = set((plan or {}).get('close', []))
        # which printer each piece prints on: {piece: printer key} - not there: the first printer
        self.slicer_of = dict((plan or {}).get('printer', {}))
        # [(printer key, "Printer - Slicer")] - the printer on the 3D print page first (key "")
        self.targets = list(targets or []) or [("", "This printer")]
        # parts you've taken out of the print (still in your model): their keys
        self.skip = set(k for k in (plan or {}).get('skip', []) if k in known)
        self.by_printer = bool(self.slicer_of)
        self._state = {}
        self._undo, self._redo, self._restoring = [], [], False
        lay = QVBoxLayout(self)
        tip = QLabel("Pick parts in the list or click them in the picture (Ctrl+click to pick more, Shift+click to un-pick), then "
                     "put them in a piece. Each piece prints as one and has its own colour; grey parts print "
                     "on their own.")
        tip.setWordWrap(True)
        lay.addWidget(tip)
        # several objects selected: work on them one at a time
        self.objects = list(objects or [])          # [(object number, name, [part numbers])]
        self.cur_obj, self.done_objs = None, set()
        self.cb_obj = None
        if len(self.objects) > 1:
            orow = QHBoxLayout()
            orow.addWidget(QLabel("<b>Object:</b>"))
            self.cb_obj = QComboBox()
            self.cb_obj.setToolTip("You selected several objects: pick one to work on just that one - the others are "
                                   "hidden. Plan its pieces and printers, then 'Scale & next' puts it on the gathered "
                                   "bed and moves on to the next object.")
            orow.addWidget(self.cb_obj)
            self.lbl_obj = QLabel()
            orow.addWidget(self.lbl_obj, 1)
            lay.addLayout(orow)
        from PySide6.QtCore import Qt as _Qt
        row = QSplitter(_Qt.Horizontal)           # drag the bars to make the boxes bigger or smaller
        row.setChildrenCollapsible(False)
        row.setHandleWidth(7)
        lay.addWidget(row, 1)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Part", "In group", "Print piece", "Prints on"])
        try:
            self.table.setSelectionBehavior(getattr(QAbstractItemView, 'SelectRows', None) or
                                            QAbstractItemView.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(getattr(QAbstractItemView, 'ExtendedSelection', None) or
                                        QAbstractItemView.SelectionMode.ExtendedSelection)
            self.table.setEditTriggers(getattr(QAbstractItemView, 'NoEditTriggers', None) or
                                       QAbstractItemView.EditTrigger.NoEditTriggers)
            self.table.verticalHeader().setVisible(False)
            self.table.horizontalHeader().setStretchLastSection(True)
        except Exception:
            pass
        self.table.setToolTip("Every part of what you selected. Pick some (Ctrl+click for more, Shift+click to un-pick), then use the "
                              "buttons below.")
        try:
            from PySide6.QtCore import QSize
            self.table.setIconSize(QSize(64, 64))
            self.table.verticalHeader().setDefaultSectionSize(70)
            self.table.setColumnWidth(0, 230)
            self.table.setColumnWidth(1, 140)
        except Exception:
            pass
        from PySide6.QtWidgets import QListWidget
        self.hidden_parts, self.hidden_pieces = set(), set()
        vsplit = QSplitter(_Qt.Vertical)
        vsplit.setChildrenCollapsible(False)
        vsplit.setHandleWidth(7)
        vsplit.setToolTip("Drag the bar between the parts and the print pieces to make either box bigger.")
        vsplit.addWidget(self.table)
        lower = QWidget()
        left = QVBoxLayout(lower)
        left.setContentsMargins(0, 0, 0, 0)
        lp = QLabel("Print pieces - untick to hide them in the picture, right-click for holes and slicer "
                    "(drag the bar above to make this box bigger):")
        lp.setWordWrap(True)
        left.addWidget(lp)
        self.piece_list = QListWidget()
        self.piece_list.setMinimumHeight(60)
        try:
            from PySide6.QtWidgets import QAbstractItemView as _AIV
            self.piece_list.setSelectionMode(getattr(_AIV, 'ExtendedSelection', None) or
                                             _AIV.SelectionMode.ExtendedSelection)
        except Exception:
            pass
        self.piece_list.setToolTip("Every piece, in its colour, and the parts printing on their own. Untick one "
                                   "to hide it in the picture, so you can see what's behind. (Hidden parts are "
                                   "still printed.)")
        left.addWidget(self.piece_list, 1)
        vsplit.addWidget(lower)
        row.addWidget(vsplit)
        self.canvas = PieceCanvas(self)
        self.canvas.setToolTip("The parts, coloured by the piece they're in (grey: on their own). Click a part to "
                               "pick it - Ctrl+click to pick more, Shift+click to un-pick. Picked parts show yellow.")
        row.addWidget(self.canvas)
        self.hsplit, self.vsplit = row, vsplit
        try:
            sz = load_settings().get('plan_splits') or {}
            row.setSizes([int(x) for x in sz.get('h', [520, 780])])
            vsplit.setSizes([int(x) for x in sz.get('v', [520, 220])])
        except Exception:
            pass

        brow = flow_layout()                   # the buttons wrap onto more lines in a narrow window
        b_new = QPushButton("New piece from picked")
        b_new.setToolTip("Makes a new piece (a new colour) holding the parts you've picked.")
        self.cb_piece = QComboBox()
        self.cb_piece.setToolTip("The piece to add the picked parts to.")
        b_add = QPushButton("Add picked to")
        b_add.setToolTip("Puts the picked parts into the piece chosen beside it.")
        b_out = QPushButton("Print on their own")
        b_out.setToolTip("Takes the picked parts out of their piece, so each prints on its own.")
        b_rest = QPushButton("Everything left: new piece and hide")
        b_rest.setToolTip("Puts every grey part still showing (on its own, not hidden) into one new piece and "
                          "hides it - for when lots of little bits are left that will print fine together.")
        b_rest.clicked.connect(self.rest_piece_and_hide)
        b_holes = QPushButton("Close holes in open pieces")
        b_holes.setToolTip("Every piece marked 'open' (holes - it won't print as a solid) gets its holes closed "
                           "when it's printed. Right-click a piece in the pieces list to do just that one. Your "
                           "model isn't changed.")
        b_holes.clicked.connect(self.close_all_open)
        for w in (b_new, b_add, self.cb_piece, b_out, b_rest, b_holes):
            brow.addWidget(w)
        lay.addLayout(brow)
        brow2 = flow_layout()
        b_kind = QPushButton("A piece for each group")
        b_kind.setToolTip("Quick start: one piece per group the parts are in - all the columns together, all "
                          "the brackets together and so on.")
        b_clear = QPushButton("Clear all")
        b_clear.setToolTip("Every part on its own again.")
        b_turn = QPushButton("Turn picture")
        b_turn.setToolTip("Turns the picture a quarter of the way round, to see the other side.")
        b_turn.clicked.connect(self.turn)
        self.b_below = QPushButton("Look from below")
        self.b_below.setToolTip("Looks up at the model from underneath (press again to look from above).")
        self.b_below.clicked.connect(self.flip_view)
        b_hide = QPushButton("Hide picked")
        b_hide.setToolTip("Hides the picked parts in the picture (they still print). Tick them again in the list "
                          "to bring them back.")
        b_hide.clicked.connect(self.hide_picked)
        b_showall = QPushButton("Show all")
        b_showall.setToolTip("Shows every part and piece again.")
        b_showall.clicked.connect(self.show_all)
        b_ren = QPushButton("Rename piece...")
        b_ren.setToolTip("Gives the piece chosen above a name of your own (it's the name the slicer shows).")
        self.lbl = QLabel()
        # ---- which printer each piece prints on: a big button for each of your printers
        pbox = QGroupBox("Print on - pick parts (in the list or picture), then click the printer they print on")
        pbl = QVBoxLayout(pbox)
        brow3 = flow_layout()
        self.printer_buttons_ = []
        for k_, (key, lab) in enumerate(self.targets):
            b_ = QPushButton(lab)
            col = PRINTER_COLOURS[k_ % len(PRINTER_COLOURS)]
            b_.setStyleSheet("QPushButton{background:rgb(%d,%d,%d);color:white;font-weight:bold;"
                             "padding:6px 12px;border-radius:4px}QPushButton:pressed{background:rgb(%d,%d,%d)}"
                             % (col + tuple(int(c * 0.75) for c in col)))
            b_.setToolTip("The picked parts (or the pieces picked in the pieces list) print on %s. Parts not "
                          "in a piece are made into one new piece first.%s" % (
                              lab, " Anything you don't give a printer prints on this one." if k_ == 0 else ""))
            b_.clicked.connect(lambda *_a, key=key: self.send_picked(key))
            brow3.addWidget(b_)
            self.printer_buttons_.append(b_)
        if len(self.targets) > 1:
            self.b_else = QPushButton("Everything else \u25be")
            self.b_else.setStyleSheet("QPushButton{font-weight:bold;padding:6px 12px}")
            self.b_else.setToolTip("Every part you haven't given a printer yet (the pieces with no \u2192 and the "
                                   "grey parts) - pick the printer they all print on. Or just pick them to see them.")
            self.b_else.clicked.connect(lambda *_: self.everything_else_menu(self.b_else))
            brow3.addWidget(self.b_else)
        # then: keep the plan, and keep the plan + Scale + next - all four buttons in one row
        def big(text, col, tip, fn):
            b_ = QPushButton(text)
            b_.setStyleSheet("QPushButton{background:rgb(%d,%d,%d);color:white;font-weight:bold;"
                             "padding:6px 12px;border-radius:4px}QPushButton:pressed{background:rgb(%d,%d,%d)}"
                             % (col + tuple(int(c * 0.75) for c in col)))
            b_.setToolTip(tip)
            b_.clicked.connect(lambda *_a: fn())
            brow3.addWidget(b_)
            return b_
        big("\u2714 Use these pieces", (90, 100, 110), "Keeps this plan now - the window stays open so you can "
            "carry on (the preview and the Pieces page behind show it). 'Done' closes.", self.apply_now)
        big("Scale & next \u25b6", (200, 70, 50), "Puts the object on the gathered bed at the scale on the Scale "
            "page - each piece on its own printer's bed. With several objects selected it's the one picked under "
            "'Object' (the window stays open and moves on to the next one); with one object the window closes and "
            "the preview shows the gathered bed.", self.use_and_scale_next)
        brow3b = flow_layout()
        b_sl_clear = QPushButton("All on %s" % self.targets[0][1].split(" - ")[0])
        b_sl_clear.setToolTip("Puts every piece back on the first printer.")
        b_sl_clear.clicked.connect(self.clear_slicers)
        brow3b.addWidget(b_sl_clear)
        self.cb_byp = QCheckBox("Colour the picture by printer")
        self.cb_byp.setChecked(self.by_printer)
        self.cb_byp.setToolTip("Ticked: each part shows in its printer's colour (the colour of its button). "
                               "Unticked: the piece colours.")
        self.cb_byp.toggled.connect(self.colour_by_printer)
        brow3b.addWidget(self.cb_byp)
        pbl.addLayout(brow3)
        pbl.addLayout(brow3b)
        self.lbl_sl = QLabel()
        self.lbl_sl.setWordWrap(True)
        pbl.addWidget(self.lbl_sl)
        if len(self.targets) < 2:
            na = QLabel("Only one printer: to print some pieces on another, save that printer (with its slicer) "
                        "on the 3D print page.")
            na.setWordWrap(True)
            pbl.addWidget(na)
        lay.addWidget(pbox)
        self.send_after = False
        b_ok = QPushButton("Done")
        b_ok.setDefault(True)
        b_ok.setToolTip("Keeps this plan and closes the window: the next export prints these pieces.")
        b_go = QPushButton("Use and send to the printers")
        b_go.setToolTip("Keeps this plan and sends it straight away: each printer's slicer opens once, with its "
                        "own pieces on its own bed.")
        b_go.clicked.connect(self.use_and_send)
        b_cancel = QPushButton("Cancel")
        b_cancel.setToolTip("Closes without keeping changes made since you last pressed 'Use these pieces'.")
        self.b_undo = QPushButton("Undo")
        self.b_undo.setToolTip("Takes back the last change to the pieces (Ctrl+Z). Ctrl+Y puts it back again.")
        self.b_undo.clicked.connect(self.undo)
        self.b_redo = QPushButton("Redo")
        self.b_redo.setToolTip("Puts back what Undo took back (Ctrl+Y).")
        self.b_redo.clicked.connect(self.redo)
        try:
            from PySide6.QtGui import QShortcut, QKeySequence
            for seq, fn in (("Ctrl+Z", self.undo), ("Ctrl+Y", self.redo), ("Ctrl+Shift+Z", self.redo),
                            ("Delete", self.delete_key)):
                sc = QShortcut(QKeySequence(seq), self)
                sc.activated.connect(fn)
        except Exception:
            pass
        for w in (self.b_undo, self.b_redo, b_kind, b_clear, b_ren, b_turn, self.b_below, b_hide, b_showall):
            brow2.addWidget(w)
        lay.addLayout(brow2)
        self.lbl.setWordWrap(True)
        lay.addWidget(self.lbl)
        okrow = QHBoxLayout()
        okrow.addStretch(1)
        for w in (b_ok, b_go, b_cancel):
            okrow.addWidget(w)
        lay.addLayout(okrow)
        b_new.clicked.connect(self.new_piece)
        b_add.clicked.connect(self.add_to)
        b_out.clicked.connect(self.take_out)
        b_kind.clicked.connect(self.by_kind)
        b_clear.clicked.connect(self.clear_all)
        b_ren.clicked.connect(self.rename)
        b_ok.clicked.connect(self.accept)
        b_cancel.clicked.connect(self.reject)
        self.table.itemSelectionChanged.connect(self.canvas.update)
        self._pick_source, self._syncing = 'parts', False
        self.table.itemSelectionChanged.connect(self.parts_picked)
        self.piece_list.itemSelectionChanged.connect(self.piece_list_picked)
        try:
            self.table.viewport().installEventFilter(self)
            self.piece_list.viewport().installEventFilter(self)
        except Exception:
            pass
        self.table.itemChanged.connect(self.part_ticked)
        self.piece_list.itemChanged.connect(self.piece_ticked)
        try:
            pol = _qt('ContextMenuPolicy', 'CustomContextMenu')
            self.table.setContextMenuPolicy(pol)
            self.table.customContextMenuRequested.connect(
                lambda pos: self.context_menu(self.table.viewport().mapToGlobal(pos)))
            self.piece_list.setContextMenuPolicy(pol)
            self.piece_list.customContextMenuRequested.connect(
                lambda pos: self.piece_menu(self.piece_list.itemAt(pos), self.piece_list.viewport().mapToGlobal(pos)))
        except Exception:
            pass
        try:
            from PySide6.QtWidgets import QApplication
            scr = QApplication.primaryScreen().availableGeometry()
            self.resize(int(scr.width() * 0.85), int(scr.height() * 0.85))
            self.setSizeGripEnabled(True)
        except Exception:
            pass
        if self.cb_obj is not None:
            self.fill_objects()
            self.cb_obj.currentIndexChanged.connect(self.object_picked)
            self.cb_obj.setCurrentIndex(0)                # start with all of them (pick one to work on it alone)
        self.refresh()

    # ---- the plan
    def colour_of(self, i):
        if self.leaves[i][0] in getattr(self, 'skip', ()):
            return (95, 95, 95)                  # left out of the print: dark grey
        p = self.keys.get(self.leaves[i][0])
        if getattr(self, 'by_printer', False):
            return self.printer_colour(self.slicer_of.get(p if p in self.pieces else "", ""))
        return piece_colour(self.pieces.index(p)) if p in self.pieces else LOOSE_COLOUR

    def printer_colour(self, key):
        keys = [k for k, _l in self.targets]
        return PRINTER_COLOURS[(keys.index(key) if key in keys else 0) % len(PRINTER_COLOURS)]

    def colour_by_printer(self, on):
        self.by_printer = bool(on)
        self.refresh()

    def picked_rows(self):
        try:
            return sorted({ix.row() for ix in self.table.selectionModel().selectedRows()})
        except Exception:
            return []

    def pick_part(self, i, mode='only'):
        """mode 'only': pick just this part; 'add': pick it as well (Ctrl); 'remove': un-pick it (Shift)."""
        if mode == 'remove':
            try:
                from PySide6.QtCore import QItemSelectionModel
                sm = self.table.selectionModel()
                flag = getattr(QItemSelectionModel, 'Deselect', None) or QItemSelectionModel.SelectionFlag.Deselect
                rows = getattr(QItemSelectionModel, 'Rows', None) or QItemSelectionModel.SelectionFlag.Rows
                sm.select(self.table.model().index(i, 0), flag | rows)
            except Exception:
                pass
            self.canvas.update()
            return
        self.pick_row(i, mode == 'add')

    def eventFilter(self, obj, ev):
        # the parts list works the same way as the picture: Ctrl+click picks more, Shift+click
        # un-picks (instead of Qt's usual 'Shift picks a run of rows')
        try:
            from PySide6.QtCore import QEvent, Qt
            if obj is self.table.viewport() and ev.type() == QEvent.MouseButtonPress and \
                    ev.button() == Qt.LeftButton:
                mods = ev.modifiers()
                if mods & (Qt.ShiftModifier | Qt.ControlModifier | Qt.AltModifier):
                    try:
                        pos = ev.position().toPoint()
                    except Exception:
                        pos = ev.pos()
                    r = self.table.rowAt(pos.y())
                    if r >= 0:
                        self.pick_part(r, 'remove' if mods & (Qt.ShiftModifier | Qt.AltModifier) else 'add')
                    return True
            # the pieces list: Alt+click (or Shift+click) un-picks a piece, Ctrl+click picks more
            if obj is self.piece_list.viewport() and ev.type() == QEvent.MouseButtonPress and \
                    ev.button() == Qt.LeftButton and ev.modifiers() & (Qt.AltModifier | Qt.ShiftModifier):
                try:
                    pos = ev.position().toPoint()
                except Exception:
                    pos = ev.pos()
                it = self.piece_list.itemAt(pos)
                if it is not None:
                    it.setSelected(False)
                    self.piece_list_picked()
                return True
        except Exception:
            pass
        return super().eventFilter(obj, ev)

    def pick_row(self, i, add=False):
        try:
            from PySide6.QtCore import QItemSelectionModel
            sm = self.table.selectionModel()
            flag = getattr(QItemSelectionModel, 'Select', None) or QItemSelectionModel.SelectionFlag.Select
            rows = getattr(QItemSelectionModel, 'Rows', None) or QItemSelectionModel.SelectionFlag.Rows
            if not add:
                self.table.clearSelection()
            sm.select(self.table.model().index(i, 0), flag | rows)
            self.table.scrollToItem(self.table.item(i, 0))
        except Exception:
            self.table.selectRow(i)
        self.canvas.update()

    def suggest_name(self, rows):
        """A name for a new piece from its parts: the part's own name, the group they're all in, or
        the object they're from - else 'Piece n'."""
        rows = list(rows)
        if len(rows) == 1:
            nm = self.leaves[rows[0]][1]
        else:
            kinds = set(self.leaves[r][2] for r in rows)
            nm = kinds.pop() if len(kinds) == 1 else ""
            if not nm:
                objs = set(o[1] for o in getattr(self, 'objects', []) for r in rows if r in o[2])
                nm = objs.pop() if len(objs) == 1 else ""
        nm = str(nm or "").strip() or self._unused_name()
        return self.unique_name(nm)

    def unique_name(self, nm):
        if nm not in self.pieces:
            return nm
        k = 2
        while "%s %d" % (nm, k) in self.pieces:
            k += 1
        return "%s %d" % (nm, k)

    def name_new_piece(self, rows):
        """Asks for the new piece's name; Cancel (or nothing typed) keeps the name it's given from
        its parts."""
        sug = self.suggest_name(rows)
        try:
            from PySide6.QtWidgets import QInputDialog
            res = QInputDialog.getText(self, PLUGIN_NAME + " - new piece",
                                       "A name for the new piece (%d part%s) - the slicer shows it.\n"
                                       "Cancel keeps '%s'." % (len(rows), "" if len(rows) == 1 else "s", sug),
                                       text=sug)
            new, ok = (res[0], res[1]) if isinstance(res, (tuple, list)) else (res, bool(res))
        except Exception:
            new, ok = sug, False
        new = str(new or "").strip()
        if not ok or not new:
            return sug
        return new if new == sug else self.unique_name(new)

    def _unused_name(self):
        k = len(self.pieces) + 1
        while "Piece %d" % k in self.pieces:
            k += 1
        return "Piece %d" % k

    def new_piece(self, *_):
        rows = self.picked_rows()
        if not rows:
            self.lbl.setText("Pick some parts first.")
            return
        name = self.name_new_piece(rows)
        self.pieces.append(name)
        for r in rows:
            self.keys[self.leaves[r][0]] = name
        self.refresh(name)

    def add_to(self, *_):
        rows = self.picked_rows()
        name = self.cb_piece.currentData()
        if not rows or not name:
            self.lbl.setText("Pick some parts, and a piece to add them to.")
            return
        for r in rows:
            self.keys[self.leaves[r][0]] = name
        self.refresh(name)

    def take_out(self, *_):
        for r in self.picked_rows():
            self.keys.pop(self.leaves[r][0], None)
        self.refresh()

    def by_kind(self, *_):
        self.pieces, self.keys = [], {}
        for key, _n, kind, _t in self.leaves:
            nm = kind or "Parts"
            if nm not in self.pieces:
                self.pieces.append(nm)
            self.keys[key] = nm
        self.refresh()

    def clear_all(self, *_):
        self.pieces, self.keys = [], {}
        self.refresh()

    def rename(self, *_):
        from PySide6.QtWidgets import QInputDialog
        old = self.cb_piece.currentData()
        if not old:
            return
        new, ok = QInputDialog.getText(self, PLUGIN_NAME, "A name for %s:" % old, text=old)
        new = str(new).strip() if ok else ""
        if not new or new == old or new in self.pieces:
            return
        self.pieces[self.pieces.index(old)] = new
        for k, p in list(self.keys.items()):
            if p == old:
                self.keys[k] = new
        if old in self.close:
            self.close.discard(old)
            self.close.add(new)
        if old in self.slicer_of:
            self.slicer_of[new] = self.slicer_of.pop(old)
        self.refresh(new)

    def refresh(self, current=None):
        from PySide6.QtWidgets import QTableWidgetItem
        from PySide6.QtGui import QColor, QBrush
        # pieces nothing's in any more go
        used = set(self.keys.values())
        self.pieces = [p for p in self.pieces if p in used]
        self.close &= set(self.pieces) | {""}
        self.slicer_of = {p: s for p, s in self.slicer_of.items() if (p in self.pieces or p == "") and s}
        picked = self.picked_rows()
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.leaves))
        for i, (key, name, kind, _t) in enumerate(self.leaves):
            p = self.keys.get(key)
            col = self.colour_of(i)
            light = QColor(int(col[0] * 0.35 + 255 * 0.65), int(col[1] * 0.35 + 255 * 0.65),
                           int(col[2] * 0.35 + 255 * 0.65))
            got = self.slicer_of.get(p if p in self.pieces else "", "")
            on = ("\u2714 " + self.slicer_name(got)) if got else ""
            if key in self.skip:
                on = "\u2716 not printed"
            for c, txt in enumerate((name, kind, p or "(on its own)", on)):
                it = QTableWidgetItem(("■ " + txt) if (c == 2 and p) or (c == 3 and txt) else txt)
                if c == 0:
                    try:
                        it.setFlags(it.flags() | _qt('ItemFlag', 'ItemIsUserCheckable'))
                        it.setCheckState(_qt('CheckState', 'Unchecked') if key in self.hidden_parts
                                         else _qt('CheckState', 'Checked'))
                        it.setToolTip("Untick to hide this part in the picture (it still prints).")
                    except Exception:
                        pass
                    try:
                        from PySide6.QtGui import QIcon
                        it.setIcon(QIcon(part_thumbnail(self.canvas.prep[i], col, 64, self.canvas.az)))
                    except Exception:
                        pass
                told = self.slicer_of.get(p if p in self.pieces else "", "")
                if told:
                    # given a printer: the row in that printer's colour, bold, so you can see it's done
                    pc_ = self.printer_colour(told)
                    it.setBackground(QBrush(QColor(int(pc_[0] * 0.3 + 255 * 0.7), int(pc_[1] * 0.3 + 255 * 0.7),
                                                   int(pc_[2] * 0.3 + 255 * 0.7))))
                    try:
                        f_ = it.font()
                        f_.setBold(True)
                        it.setFont(f_)
                    except Exception:
                        pass
                else:
                    it.setBackground(QBrush(light))
                if c == 2 and p:
                    it.setForeground(QBrush(QColor(*col).darker(130)))
                if c == 3:
                    pc_ = self.printer_colour(self.slicer_of.get(p if p in self.pieces else "", ""))
                    it.setForeground(QBrush(QColor(*pc_).darker(115)))
                self.table.setItem(i, c, it)
        self.table.blockSignals(False)
        for r in picked:
            self.pick_row(r, True)
        self.cb_piece.clear()
        for k, p in enumerate(self.pieces):
            self.cb_piece.addItem("■ " + p, p)
        if current in self.pieces:
            self.cb_piece.setCurrentIndex(self.pieces.index(current))
        self.hidden_pieces &= set(self.pieces) | {""}
        try:
            from PySide6.QtWidgets import QListWidgetItem
            from PySide6.QtGui import QPixmap, QIcon
            self.piece_list.blockSignals(True)
            self.piece_list.clear()
            for k_, p_ in enumerate(self.pieces + [""]):
                n_ = sum(1 for kk, _n, _kd, _t in self.leaves if (self.keys.get(kk) or "") == p_)
                if p_ == "" and not n_:
                    continue
                li = QListWidgetItem("%s  (%d part%s)%s" % (p_ or "On their own", n_, "" if n_ == 1 else "s",
                                                            self.piece_note(p_)))
                li.setToolTip(self.piece_tip(p_))
                pm = QPixmap(16, 16)
                pm.fill(QColor(*(piece_colour(k_) if p_ else LOOSE_COLOUR)))
                li.setIcon(QIcon(pm))
                li.setData(_qt('ItemDataRole', 'UserRole'), p_)
                li.setFlags(li.flags() | _qt('ItemFlag', 'ItemIsUserCheckable'))
                li.setCheckState(_qt('CheckState', 'Unchecked') if p_ in self.hidden_pieces
                                 else _qt('CheckState', 'Checked'))
                self.piece_list.addItem(li)
            self.piece_list.blockSignals(False)
        except Exception:
            pass
        self.remember()
        try:
            if len(self.targets) > 1:
                self.lbl_sl.setText(self.printer_summary())
        except Exception:
            pass
        n_alone = sum(1 for k, _n, _kd, _t in self.leaves if k not in self.keys)
        self.lbl.setText("%d piece%s, %d part%s on their own - %d to print." % (
            len(self.pieces), "" if len(self.pieces) == 1 else "s", n_alone, "" if n_alone == 1 else "s",
            len(self.pieces) + n_alone))
        self.canvas.update()

    def context_menu(self, gpos):
        """Right-click on the parts (in the list or the picture): what to do with the picked ones."""
        from PySide6.QtWidgets import QMenu
        rows = self.picked_rows()
        n = len(rows)
        m = QMenu(self)
        what = ("%d picked part%s" % (n, "" if n == 1 else "s")) if n else "nothing picked"
        t = m.addAction(what)
        t.setEnabled(False)
        m.addSeparator()
        # first: make a piece of them and hide it, so you work your way round the model
        a_nh = m.addAction("New piece and hide it")
        a_nh.setEnabled(n > 0)
        try:
            f_ = a_nh.font()
            f_.setBold(True)
            a_nh.setFont(f_)
            m.setDefaultAction(a_nh)
        except Exception:
            pass
        sub_h = m.addMenu("Add to piece and hide")
        sub_h.setEnabled(n > 0 and bool(self.pieces))
        for p_ in self.pieces:
            act = sub_h.addAction("\u25a0 " + p_)
            act.triggered.connect(lambda _=False, p_=p_: self._add_to(p_, hide=True))
        a_h1 = m.addAction("Hide picked")
        a_h1.setEnabled(n > 0)
        a_h1.triggered.connect(self.hide_picked)
        a_nh.triggered.connect(self.new_piece_and_hide)
        n_left = len(self.left_rows())
        a_rest = m.addAction("Everything left (%d part%s): new piece and hide" % (n_left, "" if n_left == 1 else "s"))
        a_rest.setEnabled(n_left > 0)
        a_rest.triggered.connect(self.rest_piece_and_hide)
        a_pl = m.addAction("Pick everything left")
        a_pl.setEnabled(n_left > 0)
        a_pl.triggered.connect(self.pick_left)
        m.addSeparator()
        sub_ps = m.addMenu("Print picked on")
        sub_ps.setEnabled(n > 0)
        self.fill_slicer_menu(sub_ps, self.send_picked)
        sub_pr = m.addMenu("Everything else on")
        self.fill_slicer_menu(sub_pr, self.send_rest)
        m.addSeparator()
        a_new = m.addAction("New piece from picked")
        a_new.setEnabled(n > 0)
        sub = m.addMenu("Add picked to")
        sub.setEnabled(n > 0 and bool(self.pieces))
        for p_ in self.pieces:
            act = sub.addAction("\u25a0 " + p_)
            act.triggered.connect(lambda _=False, p_=p_: self._add_to(p_))
        a_out = m.addAction("Print on their own")
        a_out.setEnabled(n > 0 and any(self.leaves[r][0] in self.keys for r in rows))
        m.addSeparator()
        a_del = m.addAction("\u2716 Don't print picked (Delete)")
        a_del.setEnabled(n > 0 and any(self.leaves[r][0] not in self.skip for r in rows))
        a_del.triggered.connect(lambda _=False: self.leave_out([self.leaves[r][0] for r in rows], True))
        a_back = m.addAction("Print picked again")
        a_back.setEnabled(n > 0 and any(self.leaves[r][0] in self.skip for r in rows))
        a_back.triggered.connect(lambda _=False: self.leave_out([self.leaves[r][0] for r in rows], False))
        m.addSeparator()
        a_only = m.addAction("Show only picked")
        a_only.setEnabled(n > 0)
        a_show = m.addAction("Show all")
        m.addSeparator()
        a_below = m.addAction("Look from above" if self.canvas.el < 0 else "Look from below")
        a_turn = m.addAction("Turn picture")
        a_new.triggered.connect(self.new_piece)
        a_out.triggered.connect(self.take_out)
        a_only.triggered.connect(self.show_only_picked)
        a_show.triggered.connect(self.show_all)
        a_below.triggered.connect(self.flip_view)
        a_turn.triggered.connect(self.turn)
        m.exec(gpos)

    def piece_menu(self, item, gpos):
        """Right-click on a piece in the pieces list."""
        from PySide6.QtWidgets import QMenu
        if item is None:
            return
        name = item.data(_qt('ItemDataRole', 'UserRole'))
        sel = self.selected_pieces()
        names = sel if name in sel and len(sel) > 1 else [name]
        m = QMenu(self)
        if len(names) > 1:
            t_ = m.addAction("%d pieces picked" % len(names))
            t_.setEnabled(False)
            m.addSeparator()
        rows = [i for i in range(len(self.leaves)) if self.piece_of(i) == name]
        a_pick = m.addAction("Pick its parts")
        a_hide = m.addAction("Show" if name in self.hidden_pieces else "Hide")
        a_only = m.addAction("Show only this")
        a_ren = m.addAction("Rename...")
        a_ren.setEnabled(bool(name))
        a_free = m.addAction("Break up (each part on its own)")
        a_free.setEnabled(bool(name))
        m.addSeparator()
        keys_ = [self.leaves[i][0] for i in range(len(self.leaves)) if self.piece_of(i) in names]
        all_out = bool(keys_) and all(k in self.skip for k in keys_)
        a_del = m.addAction("Print %s again" % ("these" if len(names) > 1 else "it") if all_out else
                            "\u2716 Don't print %s (Delete)" % ("these" if len(names) > 1 else "it"))
        a_del.setEnabled(bool(keys_))
        a_del.triggered.connect(lambda _=False: self.leave_out(keys_, not all_out))
        m.addSeparator()
        st_ = self.state_of(name)
        a_close = m.addAction("Close its holes when printing")
        a_close.setCheckable(True)
        a_close.setChecked(all(n_ in self.close for n_ in names))
        a_close.setEnabled(any(n_ in self.close or self.state_of(n_) == 'open' for n_ in names))
        a_close.setToolTip("Closes every hole (any size) in the print file so it prints as a solid. Your model "
                           "isn't changed.")
        a_close.triggered.connect(lambda on=False: [self.set_close(n_, bool(on)) for n_ in names])
        sub_s = m.addMenu("Print %s on" % ("these" if len(names) > 1 else "it"))
        self.fill_slicer_menu(sub_s, lambda p_: self.set_slicers_for(names, p_),
                              self.slicer_of.get(name, "") if len(names) == 1 else None)
        sub_r = m.addMenu("Everything else on")
        self.fill_slicer_menu(sub_r, self.send_rest)
        try:
            m.setToolTipsVisible(True)
            sub_s.setToolTipsVisible(True)
        except Exception:
            pass

        def pick():
            self.table.clearSelection()
            for r in rows:
                self.pick_row(r, True)

        def hide():
            if name in self.hidden_pieces:
                self.hidden_pieces.discard(name)
            else:
                self.hidden_pieces.add(name)
            self.refresh()

        def only():
            self.hidden_parts = set()
            self.hidden_pieces = (set(self.pieces) | {""}) - {name}
            self.refresh()

        def ren():
            for i in range(self.cb_piece.count()):
                if self.cb_piece.itemData(i) == name:
                    self.cb_piece.setCurrentIndex(i)
            self.rename()

        def free():
            for k, p_ in list(self.keys.items()):
                if p_ == name:
                    del self.keys[k]
            self.refresh()
        a_pick.triggered.connect(pick)
        a_hide.triggered.connect(hide)
        a_only.triggered.connect(only)
        a_ren.triggered.connect(ren)
        a_free.triggered.connect(free)
        m.exec(gpos)

    def _add_to(self, name, hide=False):
        rows = self.picked_rows()
        if not rows or name not in self.pieces:
            return
        for r in rows:
            self.keys[self.leaves[r][0]] = name
        if hide:
            self.hidden_pieces.add(name)
            self.table.clearSelection()
        self.refresh(name)

    def new_piece_and_hide(self, *_a, rows=None):
        """Makes a piece of the picked parts and hides it, so what's left is easier to get at."""
        rows = self.picked_rows() if rows is None else rows
        if not rows:
            self.lbl.setText("Pick some parts first.")
            return
        name = self.name_new_piece(rows)
        self.pieces.append(name)
        for r in rows:
            self.keys[self.leaves[r][0]] = name
        self.hidden_pieces.add(name)
        self.table.clearSelection()
        self.refresh(name)
        self.lbl.setText("%s made (%d part%s) and hidden - tick it in the pieces list to see it again." % (
            name, len(rows), "" if len(rows) == 1 else "s"))

    def show_only_picked(self, *_):
        picked = set(self.picked_rows())
        self.hidden_pieces = set()
        self.hidden_parts = {self.leaves[i][0] for i in range(len(self.leaves)) if i not in picked}
        self.refresh()

    def piece_of(self, i):
        p = self.keys.get(self.leaves[i][0])
        return p if p in self.pieces else ""

    def shown(self, i):
        return self.leaves[i][0] not in self.hidden_parts and self.piece_of(i) not in self.hidden_pieces

    def part_ticked(self, it):
        if it.column() != 0:
            return
        key = self.leaves[it.row()][0]
        if it.checkState() == _qt('CheckState', 'Checked'):
            self.hidden_parts.discard(key)
        else:
            self.hidden_parts.add(key)
        self.canvas.update()

    def piece_ticked(self, it):
        name = it.data(_qt('ItemDataRole', 'UserRole'))
        if it.checkState() == _qt('CheckState', 'Checked'):
            self.hidden_pieces.discard(name)
        else:
            self.hidden_pieces.add(name)
        self.canvas.update()

    def hide_picked(self, *_):
        for r in self.picked_rows():
            self.hidden_parts.add(self.leaves[r][0])
        self.table.clearSelection()
        self.refresh()

    def show_all(self, *_):
        self.hidden_parts, self.hidden_pieces = set(), set()
        self.refresh()

    def flip_view(self, *_):
        self.canvas.el = -self.canvas.el
        self.b_below.setText("Look from above" if self.canvas.el < 0 else "Look from below")
        self.canvas.view()
        self.canvas.update()

    def turn(self, *_):
        self.canvas.az = (self.canvas.az + 90.0) % 360.0
        self.canvas.view()
        self.refresh()

    def plan(self):
        return {'pieces': list(self.pieces), 'keys': dict(self.keys), 'close': sorted(self.close),
                'printer': dict(self.slicer_of), 'skip': sorted(self.skip)}

    # ---- undo and redo (Ctrl+Z, Ctrl+Y)
    def snapshot(self):
        return (tuple(self.pieces), tuple(sorted(self.keys.items())), tuple(sorted(self.close)),
                tuple(sorted(self.slicer_of.items())), tuple(sorted(self.hidden_pieces)),
                tuple(sorted(self.hidden_parts)), tuple(sorted(self.skip)))

    def remember(self):
        """Called after every change (refresh): keeps the state so Ctrl+Z can go back to it."""
        if self._restoring:
            return
        now = self.snapshot()
        if not self._undo or self._undo[-1] != now:
            self._undo.append(now)
            del self._undo[:-200]
            self._redo = []
        self.undo_buttons()

    def undo_buttons(self):
        try:
            self.b_undo.setEnabled(len(self._undo) > 1)
            self.b_redo.setEnabled(bool(self._redo))
        except Exception:
            pass

    def restore(self, snap):
        pcs, keys, close, sl, hp, hparts, skip = snap
        self.pieces, self.keys, self.close, self.skip = list(pcs), dict(keys), set(close), set(skip)
        self.slicer_of, self.hidden_pieces, self.hidden_parts = dict(sl), set(hp), set(hparts)
        self._restoring = True
        try:
            self.refresh()
        finally:
            self._restoring = False
        self.undo_buttons()

    def undo(self, *_):
        if len(self._undo) < 2:
            self.lbl.setText("Nothing to undo.")
            return
        self._redo.append(self._undo.pop())
        self.restore(self._undo[-1])
        self.lbl.setText("Undone. " + self.lbl.text())

    def redo(self, *_):
        if not self._redo:
            self.lbl.setText("Nothing to redo.")
            return
        snap = self._redo.pop()
        self._undo.append(snap)
        self.restore(snap)
        self.lbl.setText("Redone. " + self.lbl.text())

    def done(self, r):
        self.keep_splits()                 # the box sizes, for next time
        super().done(r)

    def keep_splits(self):
        try:
            update_settings(plan_splits={'h': list(self.hsplit.sizes()), 'v': list(self.vsplit.sizes())})
        except Exception:
            pass

    # ---- everything left
    def left_rows(self):
        """The parts still showing in the picture that aren't in a piece (the grey ones)."""
        return [i for i in range(len(self.leaves)) if not self.piece_of(i) and self.shown(i)]

    def pick_left(self, *_):
        rows = self.left_rows()
        self.table.clearSelection()
        for r in rows:
            self.pick_row(r, True)
        self.lbl.setText("Picked the %d part%s left." % (len(rows), "" if len(rows) == 1 else "s"))

    def rest_piece_and_hide(self, *_):
        """Every grey part still showing goes into one new piece, which is hidden."""
        rows = self.left_rows()
        if not rows:
            self.lbl.setText("Nothing's left showing on its own.")
            return
        self.new_piece_and_hide(rows=rows)

    # ---- holes and slicers, piece by piece
    def piece_tris(self, name):
        """The triangles of a piece ("" : each part on its own, as a list of parts)."""
        if name:
            return [t for k, _n, _kd, tr in self.leaves if self.keys.get(k) == name for t in tr]
        return None

    def state_of(self, name):
        """'ok', 'open' or 'flat' for a piece; for the parts on their own, the worst of them."""
        if name:
            sig = (name, tuple(sorted(k for k, p in self.keys.items() if p == name)))
            if sig not in self._state:
                try:
                    self._state[sig] = piece_state(self.piece_tris(name))
                except Exception:
                    self._state[sig] = 'ok'
            return self._state[sig]
        worst = 'ok'
        for k, _n, _kd, tr in self.leaves:
            if self.keys.get(k) in self.pieces:
                continue
            sig = ("", k)
            if sig not in self._state:
                try:
                    self._state[sig] = piece_state(tr)
                except Exception:
                    self._state[sig] = 'ok'
            if self._state[sig] == 'open':
                return 'open'
            if self._state[sig] == 'flat':
                worst = 'flat'
        return worst

    def slicer_label(self, key):
        key = "" if key == "*" else key
        for k, lab in self.targets:
            if k == key:
                return lab
        return self.targets[0][1]

    def piece_note(self, name):
        bits = []
        rows_ = [i for i in range(len(self.leaves)) if self.piece_of(i) == name]
        out_ = sum(1 for i in rows_ if self.leaves[i][0] in self.skip)
        if out_:
            bits.append("\u2716 not printed" if out_ == len(rows_) else "%d left out" % out_)
        st = self.state_of(name)
        if name in self.close:
            bits.append("holes closed")
        elif st == 'open':
            bits.append("\u26a0 open - won't print solid")
        elif st == 'flat':
            bits.append("\u26a0 flat - no thickness")
        if self.slicer_of.get(name):            # only once you've told it which printer
            bits.append("\u2192 " + self.slicer_label(self.slicer_of[name]).split(" - ")[0])
        return ("   " + ", ".join(bits)) if bits else ""

    def piece_tip(self, name):
        st = self.state_of(name)
        t = {'ok': "Closed all round - it prints as a solid.",
             'open': "Has holes (open edges) - the slicer may leave bits out or fill it wrongly. Right-click: "
                     "'Close its holes when printing'.",
             'flat': "A flat sheet with no thickness - it needs thickness to print (closing holes won't help)."}[st]
        if name in self.close:
            t = ("Its holes are closed in the print file, so it prints as a solid (your model isn't changed). "
                 "Right-click to turn that off.")
        t += " Prints on %s." % self.slicer_label(self.slicer_of.get(name, ""))
        return t

    def set_close(self, name, on):
        if on:
            self.close.add(name)
        else:
            self.close.discard(name)
        self.refresh(name or None)

    def close_all_open(self, *_):
        n = 0
        for p_ in self.pieces + [""]:
            if p_ not in self.close and self.state_of(p_) == 'open':
                self.close.add(p_)
                n += 1
        self.refresh()
        self.lbl.setText(("Holes will be closed in %d piece%s when printed." % (n, "" if n == 1 else "s"))
                         if n else "No open pieces - nothing to close.")

    # ---- slicers: picked pieces to one, everything else to another
    def selected_pieces(self):
        try:
            return [it.data(_qt('ItemDataRole', 'UserRole')) for it in self.piece_list.selectedItems()]
        except Exception:
            return []

    def fill_slicer_menu(self, menu, apply, current=None):
        """Your printers as menu items; picking one calls apply(printer key)."""
        cur_ = ("" if current == "*" else current) if current else None
        for k, lab in self.targets:
            act = menu.addAction(lab)
            if current is not None:
                act.setCheckable(True)
                act.setChecked(cur_ == k)
            act.triggered.connect(lambda _=False, k_=k: apply(k_))
        if len(self.targets) < 2:
            na = menu.addAction("(save your other printer on the 3D print page)")
            na.setEnabled(False)

    def slicer_popup(self, button, apply):
        from PySide6.QtWidgets import QMenu
        m = QMenu(self)
        self.fill_slicer_menu(m, apply)
        try:
            m.exec(button.mapToGlobal(button.rect().bottomLeft()))
        except Exception:
            m.exec()

    def piece_list_picked(self, *_):
        """Pieces clicked in the print pieces list: they're what the printer buttons act on, and
        their parts light up in the picture."""
        names = self.selected_pieces()
        if not names:
            if getattr(self, '_pick_source', '') == 'list':
                self._syncing = True
                try:
                    self.table.clearSelection()
                finally:
                    self._syncing = False
                self.canvas.update()
            return
        self._pick_source = 'list'
        self._syncing = True
        try:
            self.table.clearSelection()
            for i in range(len(self.leaves)):
                if self.piece_of(i) in names:
                    self.pick_row(i, True)
        finally:
            self._syncing = False
        self.canvas.update()

    def parts_picked(self, *_):
        """Parts picked in the list or picture: they're what the printer buttons act on now."""
        if self._syncing:
            return
        self._pick_source = 'parts'
        try:
            self.piece_list.blockSignals(True)
            self.piece_list.clearSelection()
        finally:
            self.piece_list.blockSignals(False)

    def picked_pieces(self, make=True):
        """The pieces of the picked parts (picked in the list or picture), or else the pieces picked in
        the pieces list. Picked parts on their own are made into one new piece first (make)."""
        if getattr(self, '_pick_source', 'parts') == 'list':
            names = self.selected_pieces()
            if names:
                return names
        rows = self.picked_rows()
        if not rows:
            return self.selected_pieces()
        names = []
        loose = [r for r in rows if not self.piece_of(r)]
        for r in rows:
            p_ = self.piece_of(r)
            if p_ and p_ not in names:
                names.append(p_)
        if loose and make:
            nm = self.name_new_piece(loose)
            self.pieces.append(nm)
            for r in loose:
                self.keys[self.leaves[r][0]] = nm
            names.append(nm)
        return names

    def slicer_name(self, key):
        return self.slicer_label(key).split(" - ")[0]

    def printer_summary(self):
        """How many parts print on each printer, in words."""
        cnt = {}
        for i in range(len(self.leaves)):
            k = self.slicer_of.get(self.piece_of(i), "")
            k = "" if k == "*" else k
            cnt[k] = cnt.get(k, 0) + 1
        out = []
        for k, lab in self.targets:
            if cnt.get(k):
                out.append("%s: %d part%s" % (lab.split(" - ")[0], cnt[k], "" if cnt[k] == 1 else "s"))
        return "   \u2022   ".join(out)

    def send_picked(self, key):
        names = self.picked_pieces()
        if not names:
            self.lbl_sl.setText("Pick some parts first (click them in the picture or the list - Ctrl+click for "
                                "more), then click the printer.")
            return
        self.set_slicers_for(names, key)
        if not self.by_printer:
            self.cb_byp.setChecked(True)          # show it: each part in its printer's colour
        self.table.clearSelection()
        n_parts = sum(1 for i in range(len(self.leaves)) if self.piece_of(i) in names)
        self.lbl_sl.setText("\u2714 %s (%d part%s) now print%s on %s - see 'Prints on' in the list.   All:  %s" % (
            ", ".join(n_ or "Parts on their own" for n_ in names), n_parts, "" if n_parts == 1 else "s",
            "s" if len(names) == 1 else "", self.slicer_name(key), self.printer_summary()))

    def rest_pieces(self):
        """The pieces with no printer told yet ("" = the grey parts on their own, if there are any)."""
        rest = [p_ for p_ in self.pieces + [""] if not self.slicer_of.get(p_)]
        if "" in rest and not any(not self.piece_of(i) for i in range(len(self.leaves))):
            rest.remove("")
        return rest

    def everything_else_menu(self, button):
        from PySide6.QtWidgets import QMenu
        rest = self.rest_pieces()
        n = sum(1 for i in range(len(self.leaves)) if self.piece_of(i) in rest)
        m = QMenu(self)
        t = m.addAction("Everything else: %d part%s with no printer yet" % (n, "" if n == 1 else "s"))
        t.setEnabled(False)
        m.addSeparator()
        for k, lab in self.targets:
            act = m.addAction("All on " + lab)
            act.setEnabled(n > 0)
            act.triggered.connect(lambda _=False, k_=k: self.send_rest(k_))
        m.addSeparator()
        a_pick = m.addAction("Just pick them (to see them)")
        a_pick.setEnabled(n > 0)
        a_pick.triggered.connect(self.pick_rest)
        try:
            m.exec(button.mapToGlobal(button.rect().bottomLeft()))
        except Exception:
            m.exec()

    def pick_rest(self, *_):
        rest = self.rest_pieces()
        self.table.clearSelection()
        for i in range(len(self.leaves)):
            if self.piece_of(i) in rest:
                self.pick_row(i, True)
        self.lbl_sl.setText("Picked everything with no printer yet - click a printer button to put them on it.")

    def send_rest(self, key):
        rest = [p_ for p_ in self.pieces + [""] if not self.slicer_of.get(p_)]
        if "" in rest and not any(not self.piece_of(i) for i in range(len(self.leaves))):
            rest.remove("")
        if not rest:
            self.lbl_sl.setText("Every piece already has a printer.")
            return
        self.set_slicers_for(rest, key)
        if not self.by_printer:
            self.cb_byp.setChecked(True)
        self.lbl_sl.setText("\u2714 Everything else \u2192 %s.   All:  %s" % (self.slicer_name(key), self.printer_summary()))

    def set_slicers_for(self, names, key):
        first = self.targets[0][0]
        for n_ in names:
            # "*": you chose the first printer for it (shown as chosen, prints on the 3D print page's printer)
            self.slicer_of[n_] = key if (key and key != first) else "*"
        self.refresh(names[0] if len(names) == 1 and names[0] else None)

    def clear_slicers(self, *_):
        self.slicer_of = {}
        self.refresh()
        self.lbl_sl.setText("Everything prints on %s." % self.slicer_name(self.targets[0][0]))

    def apply_now(self, *_):
        """'Use these pieces': keeps the plan without closing the window."""
        fn = getattr(self, 'on_apply', None)
        if fn is not None:
            try:
                fn(self.plan())
            except Exception as e:
                self.lbl_sl.setText("Couldn't use the plan: %s" % e)
                return
        self.lbl_sl.setText("\u2714 Kept - this plan is in use now (the preview behind shows it).   %s   Next: "
                            "'Scale & next' puts this object on the gathered bed, or 'Done' to close." %
                            self.printer_summary())

    def leave_out(self, keys, out=True):
        """Takes parts out of the print (they stay in your model), or puts them back. Ctrl+Z undoes."""
        keys = [k for k in keys if k]
        if not keys:
            return
        if out:
            self.skip |= set(keys)
        else:
            self.skip -= set(keys)
        self.table.clearSelection()
        self.refresh()
        n = len(keys)
        self.lbl.setText(("\u2716 %d part%s won't be printed (still in your model) - right-click > 'Print picked "
                          "again', or Ctrl+Z, to put %s back." % (n, "" if n == 1 else "s", "it" if n == 1 else "them"))
                         if out else "%d part%s will be printed again." % (n, "" if n == 1 else "s"))

    def delete_key(self, *_):
        """The Delete key: the picked parts (or pieces picked in the pieces list) aren't printed."""
        rows = self.picked_rows()
        if rows:
            self.leave_out([self.leaves[r][0] for r in rows], True)
            return
        names = self.selected_pieces()
        if names:
            self.leave_out([self.leaves[i][0] for i in range(len(self.leaves)) if self.piece_of(i) in names], True)

    def use_and_send(self, *_):
        self.send_after = True
        self.accept()

    def use_and_scale_next(self, *_):
        if len(self.objects) < 2 or getattr(self, 'on_scale_next', None) is None:
            self.scale_next_after = True
            self.accept()
            return
        # several objects: this one (or, with 'All objects', every one not done yet) onto the bed
        if self.cur_obj is not None and self.cur_obj in self.done_objs:
            self.lbl_sl.setText("'%s' is on the gathered bed already. To redo it, use 'Take one off' on the Scale "
                                "page first, or pick another object under 'Object'." % self.objects[self.cur_obj][1])
            return
        todo = [self.cur_obj] if self.cur_obj is not None else \
            [j for j in range(len(self.objects)) if j not in self.done_objs]
        if not todo:
            self.lbl_sl.setText("Every object is on the bed already - press Done, then 'Preview the bed' or "
                                "'Send the bed to slicer'.")
            return
        said = []
        for j in todo:
            t, nm, _rows = self.objects[j]
            ok, words = self.on_scale_next(self.plan(), t, nm)
            if not ok:
                self.lbl_sl.setText("Couldn't put '%s' on the bed: %s" % (nm, words))
                return
            self.done_objs.add(j)
            said.append(words)
        self.fill_objects()
        left = [j for j in range(len(self.objects)) if j not in self.done_objs]
        if left:
            self.cb_obj.setCurrentIndex(left[0] + 1)      # on to the next object
            nxt = "Now '%s'." % self.objects[left[0]][1]
        else:
            nxt = "All %d objects are on the bed - press Done, then 'Preview the bed' or 'Send the bed to slicer'." % (
                len(self.objects))
        self.lbl_sl.setText("\u2714 " + " ".join(said) + "  " + nxt)

    # ---- several objects: one at a time
    def fill_objects(self):
        if self.cb_obj is None:
            return
        keep = self.cb_obj.currentIndex()
        self.cb_obj.blockSignals(True)
        self.cb_obj.clear()
        self.cb_obj.addItem("All objects (%d)" % len(self.objects))
        for j, (_t, nm, rows) in enumerate(self.objects):
            self.cb_obj.addItem("%s%d. %s  (%d part%s)" % ("\u2714 " if j in self.done_objs else "", j + 1, nm,
                                                         len(rows), "" if len(rows) == 1 else "s"))
        self.cb_obj.setCurrentIndex(max(0, keep))
        self.cb_obj.blockSignals(False)
        n = len(self.done_objs)
        self.lbl_obj.setText("%d of %d on the gathered bed (\u2714)" % (n, len(self.objects)) if n else "")

    def object_picked(self, i):
        """Object list: 0 = all of them, else just that object (the others hidden)."""
        j = i - 1
        if not (0 <= j < len(self.objects)):
            self.cur_obj = None
            self.hidden_parts = set()
        else:
            self.cur_obj = j
            mine = set(self.objects[j][2])
            self.hidden_parts = {self.leaves[r][0] for r in range(len(self.leaves)) if r not in mine}
        self.hidden_pieces = set()
        self.table.clearSelection()
        self.refresh()
        try:
            self.canvas.view()
        except Exception:
            pass

    def set_slicer(self, name, key):
        self.set_slicers_for([name], key)


def lay_out(parts, row_width, gap):
    """Lays the parts (already in mm) side by side on the bed in rows, each standing on z = 0,
    the whole lot centred on the origin. Returns the parts moved, and the total size."""
    placed = []
    x = y = row_h = 0.0
    for name, tris in parts:
        xs = [c[0] for t in tris for c in t]
        ys = [c[1] for t in tris for c in t]
        zs = [c[2] for t in tris for c in t]
        w, d = max(xs) - min(xs), max(ys) - min(ys)
        if x > 0 and x + w > row_width:
            x, y, row_h = 0.0, y + row_h + gap, 0.0
        dx, dy, dz = x - min(xs), y - min(ys), -min(zs)
        placed.append((name, [tuple((c[0] + dx, c[1] + dy, c[2] + dz) for c in t) for t in tris]))
        x += w + gap
        row_h = max(row_h, d)
    allx = [c[0] for _, tr in placed for t in tr for c in t]
    ally = [c[1] for _, tr in placed for t in tr for c in t]
    allz = [c[2] for _, tr in placed for t in tr for c in t]
    cx, cy = (min(allx) + max(allx)) / 2, (min(ally) + max(ally)) / 2
    placed = [(n, [tuple((c[0] - cx, c[1] - cy, c[2]) for c in t) for t in tr]) for n, tr in placed]
    return placed, (max(allx) - min(allx), max(ally) - min(ally), max(allz) - min(allz))


def open_in_slicer(files, slicer=""):
    """Opens the saved file(s): in the slicer you named (all at once, so they load together),
    or else in whatever program Windows opens that type of file with. Returns a note."""
    import subprocess
    import sys
    files = [f for f in files if f]
    if not files:
        return ""
    try:
        if slicer and os.path.exists(slicer):
            subprocess.Popen([slicer] + files)
            return "Opened in %s." % os.path.basename(slicer)
        target = os.path.dirname(files[0]) if len(files) > 1 else files[0]
        if hasattr(os, 'startfile'):
            os.startfile(target)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', target])
        else:
            subprocess.Popen(['xdg-open', target])
        if len(files) > 1:
            return ("Opened the folder (%d files). Set your slicer's program in the window to have them "
                    "all opened in it at once." % len(files))
        return "Opened it with your default program for that type of file."
    except Exception as e:
        return "Couldn't open it (%s)." % e



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



def selection_size(entities):
    """((x, y, z) size in model units, 'Selected: ...' text) for what's selected."""
    verts, faces, meshes = collect(entities)
    if not verts:
        return (0.0, 0.0, 0.0), "Nothing selected - select the object (a group, or its faces)."
    lo, hi = bounds(verts)
    try:
        wl = world_loops(entities)             # a moved or turned component: its real size
        if wl:
            lo, hi = loops_bounds(wl)
    except Exception:
        pass
    return (hi.x() - lo.x(), hi.y() - lo.y(), hi.z() - lo.z()), \
        "Selected: %d vertices, %d faces" % (len(verts), len(faces))


# ---------------------------------------------------------------------------
# The preview box: the selection (or its pieces) in 3D, turned with the mouse
# ---------------------------------------------------------------------------
class PreviewCanvas(QWidget):
    """Shows the pieces [(name, colour, tris)] shaded, outlined where the surfaces fold.
    Left-drag turns it, the wheel zooms on the pointer, right-drag moves it, double-click fits it
    again, a click on a piece names it. A print bed (x, y in mm) can be drawn under it, and red
    lines (gaps found by a check)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 300)
        self.az, self.el = 52.0, 30.0
        self.zoom, self.pan = 1.0, (0.0, 0.0)
        self.parts, self.big, self.items = [], [], []
        self.bed = None
        self.marks = []
        self.lines_2d = []
        self.overlay = []
        self.picked = None
        self.on_pick = None
        self.empty_text = "Select an object (a group, or its faces)"
        self._spin = self._drag = None
        self.moving = False
        self._need_view = False
        self._n = 0
        self.centre, self.radius = (0.0, 0.0, 0.0), 1.0
        self.axes = _view_axes(self.az, self.el)

    # ---- what's shown
    def set_parts(self, parts, bed=None, marks=None, keep_view=True):
        self.parts = parts or []
        self.bed = bed
        self.marks = marks or []
        self.picked = None
        total = sum(len(t) for _n, _c, t in self.parts) or 1
        # every triangle drawn (thinning them out made holes and stripes), up to a very big model
        keep = min(1.0, 250000.0 / total)
        prep = [_prep_part(t, max(1, int(len(t) * keep) + 1)) for _n, _c, t in self.parts]
        pts = [q for pp in prep for t, _n, _f in pp for q in t]
        if self.bed:
            bx, by = self.bed[0] / 2.0, self.bed[1] / 2.0
            pts += [(-bx, -by, 0.0), (bx, by, 0.0)]
        if pts:
            span = max(max(q[k] for q in pts) - min(q[k] for q in pts) for k in range(3)) or 1.0
            size = span / 12.0
            for _try in range(5):
                self.big = [_split_big(pp, size) for pp in prep]
                if sum(len(b) for b in self.big) <= 24000:
                    break
                size *= 1.6
            c3 = tuple((max(q[k] for q in pts) + min(q[k] for q in pts)) / 2.0 for k in range(3))
            self.centre = c3
            self.radius = max(1e-12, max(math.sqrt(sum((q[k] - c3[k]) ** 2 for k in range(3)))
                                         for q in pts[::max(1, len(pts) // 5000)] + pts[-2:]))
        else:
            self.big = []
            self.centre, self.radius = (0.0, 0.0, 0.0), 1.0
        if not keep_view:
            self.zoom, self.pan = 1.0, (0.0, 0.0)
        self.view()
        self.update()

    def set_marks(self, marks):
        self.marks = marks or []
        self.update()

    def set_view(self, az, el):
        self.az, self.el = az, el
        self.zoom, self.pan = 1.0, (0.0, 0.0)
        self.view()
        self.update()

    def view(self):
        D, R, U = _view_axes(self.az, self.el)
        self.axes = (D, R, U)
        items = []
        for i, pp in enumerate(self.big):
            items += _project(pp, D, R, U, i)
        items.sort(key=lambda e: -e[0])
        self.items = items

    def _map(self):
        _D, R, U = self.axes
        c = self.centre
        cx = c[0] * R[0] + c[1] * R[1] + c[2] * R[2]
        cy = -(c[0] * U[0] + c[1] * U[1] + c[2] * U[2])
        w, h = self.width() - 20, self.height() - 20
        sc = min(w, h) / (2.0 * self.radius) * 1.05 * self.zoom
        return sc, 10 + w / 2 - cx * sc + self.pan[0], 10 + h / 2 - cy * sc + self.pan[1]

    def _to2d(self, p, sc, ox, oy):
        _D, R, U = self.axes
        x = p[0] * R[0] + p[1] * R[1] + p[2] * R[2]
        y = -(p[0] * U[0] + p[1] * U[1] + p[2] * U[2])
        return ox + x * sc, oy + y * sc

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen, QLinearGradient, QBrush
        from PySide6.QtCore import QPointF, Qt
        if self._need_view:
            self._need_view = False
            self.view()
        p = QPainter(self)
        if not self.moving:
            p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0.0, QColor(252, 252, 250))
        g.setColorAt(1.0, QColor(214, 220, 226))
        p.fillRect(self.rect(), QBrush(g))
        sc, ox, oy = self._map()
        if self.bed:
            bx, by = self.bed[0] / 2.0, self.bed[1] / 2.0
            corners = [(-bx, -by, 0.0), (bx, -by, 0.0), (bx, by, 0.0), (-bx, by, 0.0)]
            poly = QPolygonF([QPointF(*self._to2d(c, sc, ox, oy)) for c in corners])
            p.setBrush(QColor(236, 238, 242))
            p.setPen(QPen(QColor(120, 130, 145), 1.2))
            p.drawPolygon(poly)
            p.setPen(QPen(QColor(200, 205, 214), 0.6))
            step = 10.0 if max(bx, by) <= 200 else 50.0
            x = -bx + step
            while x < bx - 1e-6:
                p.drawLine(QPointF(*self._to2d((x, -by, 0), sc, ox, oy)), QPointF(*self._to2d((x, by, 0), sc, ox, oy)))
                x += step
            y = -by + step
            while y < by - 1e-6:
                p.drawLine(QPointF(*self._to2d((-bx, y, 0), sc, ox, oy)), QPointF(*self._to2d((bx, y, 0), sc, ox, oy)))
                y += step
        if not self.items:
            p.setPen(QColor(90, 90, 90))
            p.drawText(self.rect(), Qt.AlignCenter, self.empty_text)
        edge = QPen(QColor(35, 35, 35), 0.9)
        quick = max(1, len(self.items) // 25000) if self.moving else 1
        for n_, (_d, i, pts, sh, ed) in enumerate(self.items):
            if quick > 1 and n_ % quick:
                continue
            base = self.parts[i][1] if i < len(self.parts) else (180, 180, 180)
            if i == self.picked:
                base = (255, 225, 40)
            col = QColor(int(base[0] * sh), int(base[1] * sh), int(base[2] * sh))
            p.setBrush(col)
            p.setPen(QPen(col, 0.7))
            p.drawPolygon(QPolygonF([QPointF(ox + x * sc, oy + y * sc) for x, y in pts]))
            if ed:
                p.setPen(edge)
                for a, b in ed:
                    p.drawLine(QPointF(ox + a[0] * sc, oy + a[1] * sc), QPointF(ox + b[0] * sc, oy + b[1] * sc))
        if self.marks:
            p.setPen(QPen(QColor(220, 20, 30), 2.2))
            for a, b in self.marks:
                p.drawLine(QPointF(*self._to2d(a, sc, ox, oy)), QPointF(*self._to2d(b, sc, ox, oy)))
        # the words over the top: sizes, the picked piece
        p.setPen(QColor(30, 30, 30))
        y = 18
        for ln in self.overlay:
            p.drawText(10, y, ln)
            y += 16
        if self.picked is not None and self.picked < len(self.parts):
            nm = self.parts[self.picked][0]
            sz = getattr(self, 'piece_sizes', {}).get(self.picked, "")
            p.drawText(10, y + 4, "Picked: %s  %s" % (nm, sz))
        if getattr(self, '_quiet', False):
            p.end()
            return
        p.setPen(QColor(100, 100, 100))
        p.drawText(8, self.height() - 8, "Left-drag: turn   Wheel: zoom   Right-drag: move   "
                                         "Double-click: fit   Click: name a piece")
        p.end()

    # ---- the mouse
    def _pos(self, ev):
        try:
            q = ev.position()
            return q.x(), q.y()
        except Exception:
            return ev.x(), ev.y()

    def _start_moving(self):
        self.moving = True
        self._n += 1
        n = self._n
        try:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(220, lambda: self._settle(n))
        except Exception:
            pass

    def _settle(self, n):
        if n != self._n or self._spin is not None:
            return
        self.moving = False
        self.update()

    def wheelEvent(self, ev):
        try:
            dy = ev.angleDelta().y()
        except Exception:
            dy = 0
        if not dy:
            return
        mx, my = self._pos(ev)
        sc, ox, oy = self._map()
        wx, wy = (mx - ox) / sc, (my - oy) / sc
        self.zoom = max(0.2, min(80.0, self.zoom * 1.15 ** (dy / 120.0)))
        sc2, ox2, oy2 = self._map()
        self.pan = (self.pan[0] + mx - (ox2 + wx * sc2), self.pan[1] + my - (oy2 + wy * sc2))
        self._start_moving()
        self.update()

    def mouseDoubleClickEvent(self, ev):
        self.zoom, self.pan = 1.0, (0.0, 0.0)
        self.update()

    def mousePressEvent(self, ev):
        from PySide6.QtCore import Qt
        mx, my = self._pos(ev)
        try:
            if ev.button() in (Qt.RightButton, Qt.MiddleButton):
                self._drag = (mx, my, self.pan[0], self.pan[1])
                return
        except Exception:
            pass
        self._spin = (mx, my, self.az, self.el, False)

    def mouseMoveEvent(self, ev):
        mx, my = self._pos(ev)
        if self._spin is not None:
            x0, y0, az0, el0, moved = self._spin
            if not moved and abs(mx - x0) + abs(my - y0) <= 4:
                return
            self._spin = (x0, y0, az0, el0, True)
            self.az = (az0 - (mx - x0) * 0.45) % 360.0
            self.el = max(-89.0, min(89.0, el0 + (my - y0) * 0.35))
            self.moving = True
            self._need_view = True
            self.update()
            return
        if self._drag is not None:
            self.pan = (self._drag[2] + mx - self._drag[0], self._drag[3] + my - self._drag[1])
            self._start_moving()
            self.update()

    def mouseReleaseEvent(self, ev):
        sp, self._spin = self._spin, None
        self._drag = None
        if sp is None:
            return
        if sp[4]:
            self.moving = False
            self._need_view = True
            self.update()
            return
        i = self.part_at(sp[0], sp[1])
        self.picked = i
        self.update()
        if self.on_pick is not None:
            try:
                self.on_pick(i)
            except Exception:
                pass

    def part_at(self, mx, my):
        if not self.items:
            return None
        sc, ox, oy = self._map()
        x, y = (mx - ox) / sc, (my - oy) / sc

        def inside(pts):
            (ax, ay), (bx, by), (cx, cy) = pts
            d1 = (x - bx) * (ay - by) - (ax - bx) * (y - by)
            d2 = (x - cx) * (by - cy) - (bx - cx) * (y - cy)
            d3 = (x - ax) * (cy - ay) - (cx - ax) * (y - ay)
            return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))
        for _d, i, pts, _sh, _ed in reversed(self.items):
            if inside(pts):
                return i
        return None

    def picture(self, size):
        """A picture of the preview as it is now, size pixels across (for PNG export)."""
        from PySide6.QtGui import QPixmap
        from PySide6.QtCore import QSize
        keep = self.overlay, self.picked
        self.overlay, self.picked = [], None
        self._quiet = True
        try:
            w, h = max(1, self.width()), max(1, self.height())
            k = size / float(max(w, h))
            pm = QPixmap(QSize(int(w * k), int(h * k)))
            try:
                pm.setDevicePixelRatio(k)
            except Exception:
                pass
            self.render(pm)
            return pm
        finally:
            self.overlay, self.picked = keep
            self._quiet = False


# ---------------------------------------------------------------------------
# The window: pages (tabs) on the left, the preview on the right
# ---------------------------------------------------------------------------
INFO_TEXT = (
    "<b>%s</b> - scale, repair and export<br><br>"
    "<b>Converter</b>: real sizes to model sizes at any scale. The same as the bar along the top "
    "of the window (turn that on or off here).<br>"
    "<b>Scale</b>: changes the selected object in the work area - to a model scale, by a "
    "percentage, to a size you type (width, depth and height, in proportion or each its own), "
    "or from one model scale to another (an OO model to N). <i>Scale in place</i> changes the object "
    "itself (Undo puts it back); <i>Scale a copy</i> leaves it and puts a scaled copy beside it. "
    "<i>Scale + next</i> does the same to one object after another; set to <i>Adds it to one bed</i>, "
    "it gathers them and <i>Send the bed to slicer</i> opens them all in one slicer window, on one bed. "
    "IngeTrazo treats points closer than 0.1 mm as one, so details that small are lost when a "
    "model is made very small in the work area - the Export page keeps every detail.<br>"
    "<b>Scale &amp; Print</b>: the quick way to fill a print bed. Click an object in the work area and it shows "
    "on the bed in yellow, where it will go; <i>Add to bed</i> puts it there at the scale picked; click the "
    "next one and add it too. The coloured printer buttons pick whose bed it goes on; <i>Send</i> opens "
    "that bed in its slicer. It's the same bed as Scale + next. Your model isn't changed.<br>"
    "<b>Pieces</b>: splits what's selected into pieces - one per group, or your own plan - each "
    "in its own colour in the preview. Laid flat and side by side on the bed for printing. In "
    "<i>Plan the pieces</i>, <i>Everything left: new piece and hide</i> puts every grey part still "
    "showing into one piece; a piece marked <i>open</i> won't print as a solid - right-click it to close "
    "its holes when printing; right-click <i>Send to slicer</i> sends a piece to any of your slicers "
    "(each slicer opens once, with its own pieces on its own printer's bed).<br>"
    "<b>3D print</b>: your print bed (it says if it fits, and the biggest scale that does), "
    "nozzle, thin walls, and your slicer.<br>"
    "<b>Repair</b>: <i>Check</i> looks for faces with no area, doubled faces, hairline cracks, "
    "holes, faces pointing the wrong way and walls thinner than the nozzle, and shows any gaps "
    "left in red. The ticked repairs are made in every exported file - your model isn't changed. "
    "<i>Put a repaired copy in the model</i> makes a mended copy (as triangles) beside it.<br>"
    "<b>Export</b>: pick what it's for and the right file type and settings are picked for you. "
    "<i>Save pieces by slicer</i> saves your planned pieces in that file type, one file for each slicer, "
    "and can send each to its slicer. In <i>Plan the pieces</i>, Ctrl+Z undoes a change (Ctrl+Y redoes) "
    "and the bars between the boxes drag to make them bigger. "
    "3MF and STL for printing; OBJ (with colours) and PLY for other 3D programs; GLB / glTF for web "
    "pages, games, AR and VR; DXF 3D faces for CAD; VRML for electronics 3D models; flat DXF and "
    "SVG drawings for laser cutting and plans; a PNG picture of the preview.<br><br>"
    "<b>Preview</b>: left-drag turns it, the wheel zooms, right-drag moves it, double-click fits it. "
    "Click a piece to see its name and size. <i>Laid out on the print bed</i> shows the pieces as "
    "they'll be printed.<br><br>"
    "<b>Model's units</b>: IngeTrazo keeps every model in metres, so this is nearly always Metres. "
    "Only change it for a model that came in 1000 times too big." % PLUGIN_NAME)


def _fmt_mm(x):
    a = abs(x)
    if a >= 100:
        return "%.0f" % x
    if a >= 1:
        return "%.1f" % x
    if a >= 0.01:
        return "%.2f" % x
    return "%.2g" % x


def fmt_len(mm, unit):
    """A length for showing, in the unit picked (ft shows feet and inches)."""
    if unit == 'ft':
        ft, inch = mm_to_ft_in(mm)
        return "%d' %.1f\"" % (ft, inch) if ft else "%.2f\"" % inch
    k = dict(SHOW_UNITS).get(unit, 1.0)
    v = mm / k
    if unit == 'mm':
        return _fmt_mm(v) + " mm"
    return ("%.4g" % v) + " " + unit


def fmt_size(mm3, unit):
    return " x ".join(fmt_len(v, unit) for v in mm3)


class _ModePages(QWidget):
    """Like a stack of pages, but only the page shown takes up room (so a short one leaves no gap)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._pages = []

    def addWidget(self, w):
        self._lay.addWidget(w)
        self._pages.append(w)
        w.setVisible(len(self._pages) == 1)

    def setCurrentIndex(self, i):
        for j, w in enumerate(self._pages):
            w.setVisible(j == i)


def colour_button_style(col):
    """The big coloured buttons: white bold words on a colour, darker when pressed."""
    col = tuple(col)
    return ("QPushButton{background:rgb(%d,%d,%d);color:white;font-weight:bold;"
            "padding:8px 14px;border-radius:4px}"
            "QPushButton:pressed{background:rgb(%d,%d,%d)}"
            "QPushButton:disabled{background:rgb(200,200,200);color:rgb(245,245,245)}"
            % (col + tuple(int(c * 0.75) for c in col)))


class StudioDialog(QDialog):
    _plan = None
    _gathered = []          # the gathered bed, kept while IngeTrazo is open (closing the window keeps it)
    _taken = []             # what was taken off it, newest last, so 'Put back' can undo: [(place, item)]

    def __init__(self, viewport, tool, parent=None):
        super().__init__(parent or viewport)
        self.setWindowTitle(PLUGIN_NAME)
        self.setModal(False)
        self.viewport, self.tool = viewport, tool
        self.settings = load_settings()
        st = self.st = dict(self.settings['studio'])
        self.plan = StudioDialog._plan
        self._sel_key = None
        self.ents = []
        self.size = (0.0, 0.0, 0.0)
        self._raw = None
        self._marks = []
        self._busy = False
        self._last = ""
        self._done = 0
        self._waiting = False
        self._done_key = None
        self._bed = StudioDialog._gathered   # objects gathered by Scale + next: [(name, scale, parts, printers)]
        self._bed_view = 0      # which slicer's bed the preview shows
        self._plan_view = 0     # the same for your planned pieces ('On the print bed')
        self._bed_note = []     # lines over the preview: which bed, does it fit
        self._last_files = []
        self._raw_pieces = []
        self._typed = False
        self._drive_ax = 0
        self._shown = None
        self._shown_unit = 'mm'
        self._quiet = False
        from PySide6.QtCore import Qt, QTimer

        lay = QVBoxLayout(self)
        # ---- along the top: what's selected, the units
        self.lbl_sel = QLabel("Nothing selected")
        self.lbl_sel.setWordWrap(True)
        self.lbl_sel.setToolTip("What's selected in the work area now, and its size.")
        lay.addWidget(self.lbl_sel)
        top = QHBoxLayout()
        top.addWidget(QLabel("Sizes in:"))
        self.cb_show = QComboBox()
        for lab, _k in SHOW_UNITS:
            self.cb_show.addItem(lab, lab)
        self.cb_show.setCurrentIndex(max(0, self.cb_show.findData(st['show_unit'])))
        self.cb_show.setToolTip("The units sizes are shown and typed in, all through this window.")
        top.addWidget(self.cb_show)
        top.addWidget(QLabel("Model:"))
        self.cb_unit = QComboBox()
        for lab, mm, key in UNITS:
            self.cb_unit.addItem(lab, key)
        self.cb_unit.setCurrentIndex(max(0, self.cb_unit.findData(st['unit'])))
        self.cb_unit.setToolTip("IngeTrazo keeps every model in metres, whatever units it shows you, so this "
                                "is nearly always Metres. Only change it for a model that came in 1000 times "
                                "too big (a file in millimetres brought in as metres).")
        top.addWidget(self.cb_unit)
        self.cb_follow = QCheckBox("Follow selection")
        self.cb_follow.setChecked(bool(st['follow']))
        self.cb_follow.setToolTip("Sizes and the preview change as you select other things in the work area. "
                                  "Untick to keep working on what was selected (big models: quicker).")
        top.addWidget(self.cb_follow)
        b_ref = QPushButton("Refresh")
        b_ref.setToolTip("Reads the selection again and redraws the preview.")
        b_ref.clicked.connect(lambda *_: self.watch_selection(force=True))
        top.addWidget(b_ref)
        b_sv = QPushButton("Save project...")
        b_sv.setToolTip("Saves this job to a file - the piece plan, the gathered bed (every printer's) and the "
                        "scale - so you can work on something else and come back to it, even after closing "
                        "IngeTrazo.")
        b_sv.clicked.connect(lambda *_: self.save_project())
        top.addWidget(b_sv)
        b_op = QPushButton("Open project...")
        b_op.setToolTip("Opens a job saved with 'Save project...': its piece plan, gathered bed and scale come back. "
                        "(The plan fits when the same model is selected.)")
        b_op.clicked.connect(lambda *_: self.open_project())
        top.addWidget(b_op)
        top.addStretch(1)
        self.cb_pv = QCheckBox("Preview")
        self.cb_pv.setChecked(bool(st.get('show_preview', True)))
        self.cb_pv.setToolTip("Shows or hides the 3D preview, to make the window smaller.")
        top.addWidget(self.cb_pv)
        self.b_big = QPushButton("Bigger")
        self.b_big.setToolTip("Fills the screen with the window (press again for its usual size). You can also "
                              "drag its edges to any size - it opens at that size next time.")
        self.b_big.clicked.connect(self.toggle_big)
        top.addWidget(self.b_big)
        lay.addLayout(top)

        split = QSplitter(Qt.Horizontal)
        lay.addWidget(split, 1)
        self.tabs = QTabWidget()
        split.addWidget(self.tabs)
        right = self.right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self.canvas = PreviewCanvas(right)
        self.canvas.on_pick = self.piece_picked
        self.canvas.setToolTip("A preview of what's selected. Left-drag to turn it, wheel to zoom, right-drag to "
                               "move, double-click to fit. Click a piece to see its name and size.")
        rl.addWidget(self.canvas, 1)
        vrow = QHBoxLayout()
        self.cb_preview = QComboBox()
        self.cb_preview.addItem("As in the model", 'model')
        self.cb_preview.addItem("On the print bed", 'bed')
        self.cb_preview.setCurrentIndex(max(0, self.cb_preview.findData(st['preview'])))
        self._gathered_on = False       # 'Preview the bed' (Scale page) shows the gathered bed until you pick here
        self.cb_preview.activated.connect(self.preview_picked)
        self.cb_preview.setToolTip("As in the model: the object (or its pieces in colour) where they are. "
                                   "Laid out on the print bed: the pieces scaled, laid flat and side by side, the "
                                   "way they'll print, on your bed.")
        vrow.addWidget(self.cb_preview, 1)
        self.b_nextbed = QPushButton("Next bed \u25b8")
        self.b_nextbed.setToolTip("When your pieces go to more than one slicer, each printer has its own bed: "
                                  "this shows the next one (PrusaSlicer's bed, then Chitubox's...).")
        self.b_nextbed.clicked.connect(self.next_bed)
        self.b_nextbed.setMaximumWidth(110)
        self.b_nextbed.setVisible(False)
        vrow.addWidget(self.b_nextbed)
        for lab, az, el, tip in (("3D", 52.0, 30.0, "A view from above and to one side."),
                                 ("Top", 270.0, 89.0, "Looking straight down."),
                                 ("Front", 90.0, 0.0, "Looking at the front."),
                                 ("Side", 180.0, 0.0, "Looking at the side."),
                                 ("Below", 52.0, -45.0, "Looking up from underneath.")):
            b = QPushButton(lab)
            b.setMaximumWidth(46)
            b.setToolTip(tip)
            b.clicked.connect(lambda *_a, a=az, e=el: self.canvas.set_view(a, e))
            vrow.addWidget(b)
        rl.addLayout(vrow)
        split.addWidget(right)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setChildrenCollapsible(False)
        split.setHandleWidth(7)
        split.setToolTip("Drag the bar between the pages and the preview to make the preview wider. Pull the "
                         "window's right edge and the preview grows.")
        self.split = split

        self.build_converter_page()
        self.build_scale_page()
        self.build_print_next_page()
        self.build_pieces_page()
        self.build_print_page()
        self.build_repair_page()
        self.build_export_page()
        self.pn_ready()
        # the page you were on last time - by its name, so a new page doesn't change which one opens
        names = [self.tabs.tabText(i) for i in range(self.tabs.count())]
        want = st.get('tab_name')
        if want in names:
            self.tabs.setCurrentIndex(names.index(want))
        else:
            self.tabs.setCurrentIndex(int(st.get('tab', 1)) if 0 <= int(st.get('tab', 1)) < self.tabs.count() else 1)

        self.lbl_report = QLabel()
        self.lbl_report.setWordWrap(True)
        self.lbl_report.setVisible(False)
        try:
            self.lbl_report.setTextInteractionFlags(Qt.TextSelectableByMouse)
        except Exception:
            pass
        lay.addWidget(self.lbl_report)
        brow = QHBoxLayout()
        b_info = QPushButton("Info")
        b_info.setToolTip("What each page does, and what happened last time.")
        b_info.clicked.connect(self.show_info)
        b_close = QPushButton("Close")
        b_close.clicked.connect(self.close)
        brow.addWidget(b_info)
        brow.addStretch(1)
        # the buttons that do the work: they change with the page you're on, always in view
        self.page_buttons = {}

        def btn(page, text, tip, fn, default=False, colour=None):
            b = QPushButton(text)
            b.setToolTip(tip)
            if colour:
                b.setStyleSheet(colour_button_style(colour))
            b.clicked.connect(lambda *_: fn())
            brow.addWidget(b)
            self.page_buttons.setdefault(page, []).append(b)
            return b
        btn(3, "Plan the pieces...", "Pick parts and put them into pieces of your own.", self.plan_pieces)
        self.b_send2 = btn(3, "Send to printer", "Saves the pieces at the new size (no save box - into the folder "
                           "on the 3D print page) and opens them: each piece in the slicer your plan gives it (see "
                           "the Printing column) - each slicer opens once, with its own pieces on one bed. Your "
                           "model isn't changed.", lambda: self.send_to_slicer_pick(self.b_send2),
                           colour=(41, 128, 185))
        self.b_save2 = btn(3, "Save and send to printer...", "The same as 'Send to printer', but you pick where "
                           "the print files are saved first (a save box), then they open in the slicer.",
                           lambda: self.send_to_slicer_pick(self.b_save2, save_as=True), colour=(142, 68, 173))
        self.b_send3 = btn(4, "Send to slicer", "Saves it at the new size (no save box) and opens it in this "
                           "printer's slicer - with more than one, you pick which suits this model. Your model "
                           "isn't changed.", lambda: self.send_to_slicer_pick(self.b_send3))
        btn(4, "Export for printing...", "Saves it for printing: at the new size, in mm, repaired, the pieces laid "
            "out on the bed - you pick where. Your model isn't changed.", self.export_print, True)
        btn(5, "Check", "Checks what's selected at the new size, without saving anything. Gaps left after the "
            "repairs show red in the preview.", self.check_now, True)
        btn(5, "Repaired copy", "Puts a mended copy (as triangles, full size) beside the original in the work "
            "area.", self.repaired_copy)
        btn(6, "Export...", "Saves what's selected with these settings. Your model isn't changed.",
            self.export, True)
        btn(6, "Save pieces by slicer...", "Saves your planned pieces with these settings, one file for each "
            "slicer, and sends each to its slicer if ticked.", self.export_by_slicer)
        brow.addWidget(b_close)
        lay.addLayout(brow)
        self.tabs.currentChanged.connect(self.page_shown)

        # anything changed: sizes again, preview (a moment later), remember it
        self._pv_timer = QTimer(self)
        self._pv_timer.setSingleShot(True)
        self._pv_timer.timeout.connect(self.refresh_preview)
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self.save_now)
        self.connect_changes()
        try:
            from PySide6.QtWidgets import QComboBox as _QC
            from PySide6.QtWidgets import QSizePolicy as _SP
            pol = getattr(_QC, 'AdjustToContents', None) or _QC.SizeAdjustPolicy.AdjustToContents
            fixed = getattr(_SP, 'Fixed', None) or _SP.Policy.Fixed
            for cb in self.findChildren(_QC):
                cb.setSizeAdjustPolicy(pol)
                cb.setSizePolicy(fixed, fixed)
        except Exception:
            pass
        try:
            self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        except Exception:
            pass
        # Enter in a box must never scale or save anything by itself
        for b in self.findChildren(QPushButton):
            try:
                b.setAutoDefault(False)
                b.setDefault(False)
            except Exception:
                pass
        self.canvas.setMinimumSize(280, 260)
        self.right.setVisible(self.cb_pv.isChecked())
        self.cb_pv.toggled.connect(self.toggle_preview)
        self.page_shown(self.tabs.currentIndex())
        self.resize(760 if self.cb_pv.isChecked() else 440, 560)
        self.watch_selection(force=True)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.watch_selection)
        self._timer.timeout.connect(self._pn_tick)
        self._timer.start(800)

    # ------------------------------------------------------------------ pages
    def _page(self, title, tip=None):
        w = QWidget()
        v = QVBoxLayout(w)
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setWidget(w)
        try:
            from PySide6.QtCore import Qt
            sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        except Exception:
            pass
        try:
            sa.setFrameShape(QFrame.NoFrame)
        except Exception:
            pass
        i = self.tabs.addTab(sa, title)
        if tip:
            self.tabs.setTabToolTip(i, tip)
        return v

    def _form(self, parent=None):
        f = QFormLayout(parent) if parent is not None else QFormLayout()
        try:
            f.setRowWrapPolicy(getattr(QFormLayout, 'WrapLongRows', None) or QFormLayout.RowWrapPolicy.WrapLongRows)
        except Exception:
            pass
        try:
            f.setFieldGrowthPolicy(getattr(QFormLayout, 'FieldsStayAtSizeHint', None) or
                                   QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        except Exception:
            pass
        return f

    def _dspin(self, val, lo, hi, dec=2, suffix="", prefix="", tip=""):
        s = QDoubleSpinBox()
        s.setRange(lo, hi)
        s.setDecimals(dec)
        s.setSuffix(suffix)
        s.setPrefix(prefix)
        s.setValue(val)
        s.setKeyboardTracking(False)
        if tip:
            s.setToolTip(tip)
        return s

    def _scale_list(self, value, tip=""):
        cb = QComboBox()
        for text, n in SCALES:
            cb.addItem(text, n)
        idx = len(SCALES) - 1
        for i, (_t, n) in enumerate(SCALES):
            if n is not None and abs(n - value) < 1e-9:
                idx = i
        cb.setCurrentIndex(idx)
        sp = self._dspin(value, 0.001, 1000000.0, 3, prefix="1 : ",
                         tip="The scale as a number. Picking a scale in the list fills it in; type your own "
                             "here (1 : 50, 1 : 33.3 ...) and the list changes to Custom.")

        def picked(*_):
            n = cb.currentData()
            if n:
                sp.blockSignals(True)
                sp.setValue(n)
                sp.blockSignals(False)

        def typed(v):
            n = cb.currentData()
            if n is not None and abs(n - v) < 1e-9:
                return
            j = next((i for i, (_t, x) in enumerate(SCALES) if x is not None and abs(x - v) < 1e-9),
                     len(SCALES) - 1)
            cb.blockSignals(True)
            cb.setCurrentIndex(j)
            cb.blockSignals(False)
        cb.currentIndexChanged.connect(picked)
        sp.valueChanged.connect(typed)
        if tip:
            cb.setToolTip(tip)
        row = QHBoxLayout()
        row.addWidget(cb)
        row.addWidget(sp)
        row.addStretch(1)
        return cb, sp, row

    def build_converter_page(self):
        v = self._page("Converter", "Real sizes (ft / in / mm) to model sizes at any scale.")
        self.conv = ConverterStrip(self.settings, page=True)
        try:
            eddy_tips(self.conv, EDDY_TIPS)
        except Exception:
            pass
        v.addWidget(self.conv)
        self.cb_bar = QCheckBox("Converter bar along the top")
        tb = find_toolbar()
        self.cb_bar.setChecked(bool(tb is not None and tb.isVisible()))
        self.cb_bar.setToolTip("The same converter as a bar along the top of IngeTrazo's window, always to hand.")
        self.cb_bar.toggled.connect(show_toolbar)
        v.addWidget(self.cb_bar)
        b = QPushButton("Use this scale on the Scale page")
        b.setToolTip("Sets the Scale page to 'To a model scale' at the scale picked here.")
        b.clicked.connect(self.use_converter_scale)
        row = QHBoxLayout()
        row.addWidget(b)
        row.addStretch(1)
        v.addLayout(row)
        v.addStretch(1)

    def build_scale_page(self):
        st = self.st
        v = self._page("Scale", "Scale the selected object in the work area: to a scale, a percentage or a size.")
        form = self._form()
        self.cb_mode = QComboBox()
        for lab, key in SCALE_MODES:
            self.cb_mode.addItem(lab, key)
        self.cb_mode.setCurrentIndex(max(0, self.cb_mode.findData(st['mode'])))
        self.cb_mode.setToolTip("How the new size is worked out.")
        form.addRow("Scale it:", self.cb_mode)
        self.stack = _ModePages()
        # a model scale
        w = QWidget()
        f = self._form(w)
        f.setContentsMargins(0, 0, 0, 0)
        self.cb_scale, self.sp_scale, r = self._scale_list(st['scale'], "The scale to make it: 1:76.2 makes it "
                                                           "76.2 times smaller than it is in the model.")
        f.addRow("Model scale:", r)
        self.stack.addWidget(w)
        # a percentage
        w = QWidget()
        f = self._form(w)
        f.setContentsMargins(0, 0, 0, 0)
        self.sp_pct = self._dspin(st['percent'], 0.001, 100000.0, 3, " %",
                                  tip="100 % keeps the size; 50 % is half the size; 200 % twice the size.")
        prow = QHBoxLayout()
        prow.addWidget(self.sp_pct)
        for p in (10, 25, 50, 75, 150, 200):
            b = QPushButton("%d%%" % p)
            b.setMaximumWidth(52)
            b.setToolTip("%d %%" % p)
            b.clicked.connect(lambda *_a, p=p: self.sp_pct.setValue(p))
            prow.addWidget(b)
        prow.addStretch(1)
        f.addRow("Percentage:", prow)
        self.stack.addWidget(w)
        # a size
        w = QWidget()
        g = QGridLayout(w)
        g.setContentsMargins(0, 0, 0, 0)
        self.sp_w = self._dspin(0, 0, 1e9, 3, tip="The new width (along X).")
        self.sp_d = self._dspin(0, 0, 1e9, 3, tip="The new depth (along Y).")
        self.sp_h = self._dspin(0, 0, 1e9, 3, tip="The new height (along Z).")
        self.lbl_now = [QLabel(), QLabel(), QLabel()]
        for i, (lab, sp) in enumerate((("Width (X):", self.sp_w), ("Depth (Y):", self.sp_d),
                                       ("Height (Z):", self.sp_h))):
            g.addWidget(QLabel(lab), i, 0)
            g.addWidget(sp, i, 1)
            g.addWidget(self.lbl_now[i], i, 2)
        self.cb_lock = QCheckBox("Keep in proportion")
        self.cb_lock.setChecked(bool(st['lock']))
        self.cb_lock.setToolTip("Ticked: the shape stays the same - type any one size and the others follow. Unticked: each size is "
                                "its own, so you can stretch or squash it (taller, narrower ...).")
        g.addWidget(self.cb_lock, 3, 0, 1, 3)
        b = QPushButton("Back to its size now")
        b.setToolTip("Puts the boxes back to the object's size as it is.")
        b.clicked.connect(self.reset_size_boxes)
        g.addWidget(b, 4, 0, 1, 2)
        self.stack.addWidget(w)
        # one scale to another
        w = QWidget()
        f = self._form(w)
        f.setContentsMargins(0, 0, 0, 0)
        self.cb_from, self.sp_from, r1 = self._scale_list(st['from_scale'], "The scale the model is made at now.")
        self.cb_to, self.sp_to, r2 = self._scale_list(st['to_scale'], "The scale you want it at.")
        f.addRow("It's made at:", r1)
        f.addRow("Make it:", r2)
        self.stack.addWidget(w)
        form.addRow(self.stack)
        self.cb_pivot = QComboBox()
        for lab, key in PIVOTS:
            self.cb_pivot.addItem(lab, key)
        self.cb_pivot.setCurrentIndex(max(0, self.cb_pivot.findData(st['pivot'])))
        self.cb_pivot.setToolTip("The point that stays put while it changes size.")
        form.addRow("Scale about:", self.cb_pivot)
        v.addLayout(form)
        self.lbl_scale_info = QLabel()
        self.lbl_scale_info.setWordWrap(True)
        try:
            from PySide6.QtCore import Qt
            self.lbl_scale_info.setTextFormat(Qt.RichText)
        except Exception:
            pass
        v.addWidget(self.lbl_scale_info)
        f2 = self._form()
        self.cb_beside = QCheckBox("Scale in place: move it beside where it was")
        self.cb_beside.setChecked(bool(st.get('beside', True)))
        self.cb_beside.setToolTip("Scale in place: the scaled object is moved to one side of where it stood, so "
                                  "it isn't left inside (or under) the space it took up. Untick to leave it where "
                                  "it is.")
        f2.addRow(self.cb_beside)
        self.cb_next = QComboBox()
        self.cb_next.addItem("Sends it to the slicer (model kept)", 'slicer')
        self.cb_next.addItem("Adds it to one bed - send them all together (model kept)", 'bed')
        self.cb_next.addItem("Makes a scaled copy (original kept)", 'copy')
        self.cb_next.addItem("Scales it in place", 'inplace')
        self.cb_next.setCurrentIndex(max(0, self.cb_next.findData(st.get('next_how', 'slicer'))))
        self.cb_next.setToolTip("What 'Scale + next' does to each object before getting ready for the next one. "
                                "'Adds it to one bed': each object is scaled and kept here; when they're all "
                                "done, 'Send the bed to slicer' lays them out side by side and opens them in "
                                "one slicer window, on one bed.")
        f2.addRow("Scale + next:", self.cb_next)
        v.addLayout(f2)
        srow = flow_layout()                  # wraps in a narrow window, nothing cut off
        for text, tip, fn in (
                ("Send to slicer", "Leaves your model as it is: saves it at the new size as a print file (no "
                 "save box - into the folder set on the 3D print page) and opens it in your printer's slicer. "
                 "The preview shows it as it goes on the bed. With more than one slicer for this printer, "
                 "you pick which suits this model.", 'send'),
                ("Scale a copy", "Leaves the object as it is and puts a scaled copy beside it.",
                 lambda: self.scale_model('copy')),
                ("Scale in place", "Changes the selected object itself (moved beside where it was, if that's "
                 "ticked). Edit > Undo puts it back.", lambda: self.scale_model('inplace')),
                ("Scale + next", "Does what 'Scale + next' is set to above (send to the slicer, a copy, or in "
                 "place), then gets ready for the next object: select the next one and press this again.",
                 self.scale_and_next)):
            b = QPushButton(text)
            b.setToolTip(tip)
            if fn == 'send':
                b.clicked.connect(lambda *_a, b=b: self.send_to_slicer_pick(b))
            else:
                b.clicked.connect(lambda *_a, fn=fn: fn())
            srow.addWidget(b)

        v.addLayout(srow)
        brow_ = flow_layout()
        self.b_sendbed = QPushButton("Send the bed to slicer")
        self.b_sendbed.setToolTip("Lays every object gathered by 'Scale + next' (set to 'Adds it to one bed') side "
                                  "by side on your print bed and opens them all in this printer's slicer - one "
                                  "window, one bed. Then the bed is emptied, ready for the next lot.")
        self.b_sendbed.clicked.connect(lambda *_: self.send_bed(self.b_sendbed))
        self.b_takeoff = QPushButton("Take one off \u25be")
        self.b_takeoff.setToolTip("Takes one object off the bed (the last one added, or any one you pick) - for "
                                  "one added by mistake. Nothing else on the bed changes.")
        self.b_takeoff.clicked.connect(lambda *_: self.take_off_menu(self.b_takeoff))
        self.b_putback = QPushButton("Put back \u21b6")
        self.b_putback.setToolTip("Puts back the last object taken off the bed (or everything, after 'Empty the "
                                  "bed') - in case you took off the wrong one. Press again for the one before.")
        self.b_putback.clicked.connect(self.put_back)
        self.b_emptybed = QPushButton("Empty the bed")
        self.b_emptybed.setToolTip("Forgets the objects gathered so far (nothing is saved or sent).")
        self.b_emptybed.clicked.connect(self.empty_bed)
        self.b_seebed = QPushButton("Preview the bed")
        self.b_seebed.setToolTip("Shows the objects gathered so far laid out on your bed in the preview, as "
                                 "they'll go to the slicer (each object its own colour). Pick 'As in the model' "
                                 "under the preview to go back.")
        self.b_seebed.clicked.connect(self.show_gathered)
        brow_.addWidget(self.b_seebed)
        brow_.addWidget(self.b_sendbed)
        brow_.addWidget(self.b_takeoff)
        brow_.addWidget(self.b_putback)
        brow_.addWidget(self.b_emptybed)
        b_again = QPushButton("Start again")
        b_again.setToolTip("Empties the gathered bed (every printer's) and forgets your piece plan - a clean start. "
                           "Your model isn't changed.")
        b_again.clicked.connect(self.start_again)
        brow_.addWidget(b_again)

        v.addLayout(brow_)
        self.bed_buttons()
        self.lbl_count = QLabel()
        self.lbl_count.setWordWrap(True)
        v.addWidget(self.lbl_count)
        note = QLabel("The Export page uses this size too, without changing your model.")
        note.setWordWrap(True)
        v.addWidget(note)
        v.addStretch(1)
        self.stack.setCurrentIndex(self.cb_mode.currentIndex())

    def build_pieces_page(self):
        st = self.st
        v = self._page("Pieces", "Split it into pieces, shown in colour in the preview.")
        form = self._form()
        self.cb_split = QComboBox()
        for lab, key in SPLITS:
            self.cb_split.addItem(lab, key)
        self.cb_split.setCurrentIndex(max(0, self.cb_split.findData(st['split'])))
        self.cb_split.setToolTip(
            "Which groups become the pieces. One piece: everything together. Every group: each group with "
            "faces of its own is a piece (a canopy: every column, bracket and board). 'n levels in': each group "
            "that many levels inside what you selected is one piece with everything in it - so group together "
            "the bits you'll print as one and they come out as one.")
        form.addRow("Pieces:", self.cb_split)
        prow = flow_layout()
        self.b_plan = QPushButton("Plan the pieces...")
        self.b_plan.setToolTip("Shows every part in a list and a picture: pick parts and put them into pieces of "
                               "your own, each its own colour. A plan decides the pieces (instead of the list "
                               "above).")
        self.b_plan.clicked.connect(self.plan_pieces)
        self.b_unplan = QPushButton("Forget plan")
        self.b_unplan.setToolTip("Goes back to the list above to decide the pieces.")
        self.b_unplan.clicked.connect(self.forget_plan)
        prow.addWidget(self.b_plan)
        b_again2 = QPushButton("Start again")
        b_again2.setToolTip("Empties the gathered bed (every printer's) and forgets your piece plan - a clean start. "
                            "Your model isn't changed.")
        b_again2.clicked.connect(self.start_again)
        prow.addWidget(self.b_unplan)
        prow.addWidget(b_again2)

        form.addRow("", prow)
        self.sp_gap = self._dspin(st['gap'], 0.2, 200.0, 1, " mm",
                                  tip="The space left between the pieces when they're laid out on the bed "
                                      "(printed mm).")
        form.addRow("Gap between pieces:", self.sp_gap)
        self.cb_flat = QCheckBox("Lay each piece flat")
        self.cb_flat.setChecked(bool(st['lay_flat']))
        self.cb_flat.setToolTip("Turns each piece so its biggest flat face lies on the bed - a panel or sheet on its "
                                "back - long side along X, the way you'd print or cut it. Untick to keep pieces "
                                "standing as they are in the model.")
        form.addRow(self.cb_flat)
        v.addLayout(form)
        self.lbl_pieces = QLabel()
        self.lbl_pieces.setWordWrap(True)
        v.addWidget(self.lbl_pieces)
        self.tbl = QTableWidget(0, 4)
        self.tbl.setHorizontalHeaderLabels(["Piece", "Size (new)", "Faces", "Printing"])
        self.tbl.setToolTip("The pieces, in their preview colours, at the new size. Click one to show it in the "
                            "preview.")
        try:
            from PySide6.QtWidgets import QAbstractItemView
            self.tbl.setEditTriggers(getattr(QAbstractItemView, 'NoEditTriggers', None) or
                                     QAbstractItemView.EditTrigger.NoEditTriggers)
            self.tbl.setSelectionBehavior(getattr(QAbstractItemView, 'SelectRows', None) or
                                          QAbstractItemView.SelectionBehavior.SelectRows)
            self.tbl.verticalHeader().setVisible(False)
            self.tbl.horizontalHeader().setStretchLastSection(True)
            self.tbl.setColumnWidth(0, 140)
            self.tbl.setColumnWidth(1, 150)
        except Exception:
            pass
        self.tbl.itemSelectionChanged.connect(self.piece_row_picked)
        v.addWidget(self.tbl, 1)

    def build_print_page(self):
        st = self.st
        v = self._page("3D print", "Your printers: bed, nozzle or resin, slicer.")
        # ---- the printer: your own (in your order) first, then the ready-made sizes
        prow = QHBoxLayout()
        prow.addWidget(QLabel("Printer:"))
        self.cb_bedp = QComboBox()
        self.cb_bedp.setToolTip("Your own printers first (in the order you put them), then ready-made bed sizes. "
                                "Pick one and the page is filled in.")
        prow.addWidget(self.cb_bedp)
        prow.addStretch(1)
        v.addLayout(prow)
        brow = flow_layout()
        for text, tip, fn in (
                ("Save as new...", "Saves everything on this page as a printer of your own, under a name you type. "
                 "It goes at the top of the list.", self.printer_save_as),
                ("Save", "Updates the printer you have picked (your own printers only) with what's on this page.",
                 self.printer_save),
                ("Delete", "Deletes the printer you have picked (your own printers only).", self.printer_delete),
                ("Up", "Moves your printer up the list.", lambda: self.printer_move(-1)),
                ("Down", "Moves your printer down the list.", lambda: self.printer_move(1))):
            b = QPushButton(text)
            b.setToolTip(tip)
            if text in ("Up", "Down"):
                b.setMaximumWidth(52)
            b.clicked.connect(lambda *_a, fn=fn: fn())
            brow.addWidget(b)
            setattr(self, 'b_pr_' + text.split()[0].lower().rstrip('.'), b)

        v.addLayout(brow)
        form = self._form()
        self.cb_kind = QComboBox()
        for lab, key in (("FDM (filament)", 'fdm'), ("Resin", 'resin'), ("Other", 'other')):
            self.cb_kind.addItem(lab, key)
        self.cb_kind.setToolTip("What kind of printer it is. Resin: thin-wall warnings use the smallest detail it "
                                "prints instead of a nozzle, and the file is STL.")
        form.addRow("Kind:", self.cb_kind)
        self.cb_bed = QCheckBox("Check it fits on the print bed")
        self.cb_bed.setChecked(bool(st['bed']))
        self.cb_bed.setToolTip("Says whether the new size fits on your bed, and the biggest scale that does.")
        form.addRow(self.cb_bed)
        bedrow = QHBoxLayout()
        self.bed = []
        for key, axis in (('bed_x', 'X'), ('bed_y', 'Y'), ('bed_z', 'Z')):
            s_ = self._dspin(st[key], 1.0, 100000.0, 1, " mm", axis + " ",
                             "Your print bed (or resin vat) size in mm: width, depth and height.")
            self.bed.append(s_)
            bedrow.addWidget(s_)
        form.addRow("Bed size:", bedrow)
        self.lbl_fit = QLabel()
        self.lbl_fit.setWordWrap(True)
        form.addRow(self.lbl_fit)
        frow = QHBoxLayout()
        self.b_fit = QPushButton("Use the biggest that fits")
        self.b_fit.setToolTip("Sets the Scale page to the biggest size that still fits on your bed.")
        self.b_fit.clicked.connect(self.use_biggest)
        frow.addWidget(self.b_fit)
        self.b_unfit = QPushButton("Back to the scale before")
        self.b_unfit.setToolTip("Puts the Scale page back the way it was before 'Use the biggest that fits'.")
        self.b_unfit.clicked.connect(self.scale_back)
        frow.addWidget(self.b_unfit)
        frow.addStretch(1)
        form.addRow(frow)
        nrow = QHBoxLayout()
        self.cb_thin = QCheckBox("Warn of walls thinner than")
        self.cb_thin.setChecked(bool(st['warn_thin']))
        self.cb_thin.setToolTip("Looks for walls, rods and letters thinner than this once scaled - the slicer may "
                                "leave them out. FDM: your nozzle width. Resin: the thinnest detail it prints.")
        self.sp_nozzle = self._dspin(st['nozzle'], 0.01, 2.0, 2, " mm",
                                     tip="FDM: your nozzle width (0.4 mm usually). Resin: the thinnest wall it "
                                         "prints (about 0.2 mm).")
        self.sp_nozzle.setSingleStep(0.05)
        nrow.addWidget(self.cb_thin)
        nrow.addWidget(self.sp_nozzle)
        nrow.addStretch(1)
        form.addRow(nrow)
        self.cb_pfmt = QComboBox()
        for key in ('3mf', 'stl', 'stla'):
            self.cb_pfmt.addItem(FMT[key][1], key)
        self.cb_pfmt.setToolTip("The file 'Export for printing' saves. 3MF keeps the pieces as separate items in one "
                                "file (most FDM slicers); STL is the shape only and reads the right size in every "
                                "slicer - use it for resin (some older resin slicers read 3MF too small).")
        form.addRow("Print file:", self.cb_pfmt)
        v.addLayout(form)
        # ---- the slicer for this printer
        v.addWidget(QLabel("<b>Slicers for this printer</b>"))
        self.cb_slicer = QComboBox()
        self.cb_slicer.setEditable(True)
        self.cb_slicer.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        # don't grow to fit long program paths (that pushed the buttons off the right edge)
        self.cb_slicer.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.cb_slicer.setMinimumContentsLength(12)
        self.cb_slicer.setMinimumWidth(80)
        self.ed_slicer = self.cb_slicer.lineEdit()
        self.ed_slicer.setPlaceholderText("(the computer's usual program for the file)")
        self.cb_slicer.setToolTip("The slicers for this printer (the files that start them) - FDM slicers, resin "
                                  "slicers or any other program. Add as many as you like with Browse... or Find "
                                  "slicers; the one showing is the one used. With more than one, 'Send to slicer' "
                                  "asks which suits this model. Each of your printers keeps its own list. Empty: "
                                  "files open in the computer's usual program for that type of file.")
        self.set_slicers(st.get('slicers') or [], st.get('slicer', ''))
        v.addWidget(self.cb_slicer)          # the path on its own line, the buttons under it
        srow = flow_layout()
        b_browse = QPushButton("Browse...")
        b_browse.setToolTip("Find a slicer's program yourself and add it to this printer's list.")
        b_browse.clicked.connect(self.browse_slicer)
        b_find = QPushButton("Find slicers")
        b_find.setToolTip("Looks in the usual program folders for slicers on this computer and lists them to pick "
                          "from (picked ones are added to this printer's list).")
        b_find.clicked.connect(lambda *_: self.find_slicers(b_find))
        b_rem = QPushButton("Remove")
        b_rem.setToolTip("Takes the slicer showing off this printer's list (the program itself isn't touched).")
        b_rem.clicked.connect(self.remove_slicer)
        for b in (b_browse, b_find, b_rem):
            srow.addWidget(b)

        v.addLayout(srow)
        self.cb_open = QCheckBox("Open it in the slicer straight after saving")
        self.cb_open.setChecked(bool(st['open_after']))
        self.cb_open.setToolTip("After 'Export for printing' (or Export), the file opens by itself: printing files in "
                                "this printer's slicer, others in the computer's usual program for them.")
        v.addWidget(self.cb_open)
        frow2 = QHBoxLayout()
        v.addWidget(QLabel("Print files go in:"))
        self.lbl_pfolder = QLabel(self.st.get('print_folder') or os.path.join(os.path.expanduser("~"), "Downloads",
                                                                             "3D Scale Studio"))
        self.lbl_pfolder.setWordWrap(True)
        self.lbl_pfolder.setMinimumWidth(80)
        self.lbl_pfolder.setToolTip("Where 'Send to slicer' saves the print files (no save box each time).")
        v.addWidget(self.lbl_pfolder)
        b_pf = QPushButton("Change...")
        b_pf.setToolTip("Pick the folder 'Send to slicer' saves into.")
        b_pf.clicked.connect(self.browse_print_folder)
        frow2.addWidget(b_pf)
        frow2.addStretch(1)
        v.addLayout(frow2)
        self.lbl_printer = QLabel()
        self.lbl_printer.setWordWrap(True)
        v.addWidget(self.lbl_printer)
        v.addStretch(1)
        self.cb_kind.setCurrentIndex(max(0, self.cb_kind.findData(st.get('kind', 'fdm'))))
        self.cb_pfmt.setCurrentIndex(max(0, self.cb_pfmt.findData(st.get('print_format', '3mf'))))
        self.fill_printers(st.get('printer', ''))
        self.fit_buttons()

    def build_repair_page(self):
        st = self.st
        v = self._page("Repair", "Check for problems and mend them.")
        intro = QLabel("The ticked repairs are made in every file you export (when 'Make the repairs' is "
                       "ticked on the Export page). Your model in the work area isn't changed.")
        intro.setWordWrap(True)
        v.addWidget(intro)
        self.cb_fclean = QCheckBox("Take out flat and doubled faces")
        self.cb_fclean.setChecked(bool(st['fix_clean']))
        self.cb_fclean.setToolTip("Faces squashed to a line or a point, the same face twice, and two faces back to "
                                  "back with nothing between them - they confuse slicers.")
        self.cb_fcracks = QCheckBox("Mend hairline cracks")
        self.cb_fcracks.setChecked(bool(st['fix_cracks']))
        self.cb_fcracks.setToolTip("Where a corner of one face sits part way along the edge of the next, the "
                                   "slicer sees a crack. The edge is split there so they join properly.")
        hrow = QHBoxLayout()
        self.cb_fholes = QCheckBox("Fill holes up to")
        self.cb_fholes.setChecked(bool(st['fix_holes']))
        self.cb_fholes.setToolTip("Closes small holes in a solid (a missing face). Bigger openings are left, as "
                                  "they're more likely meant. For solids - leave it off for single sheets.")
        self.sp_hole = QSpinBox()
        self.sp_hole.setRange(3, 5000)
        self.sp_hole.setValue(int(st['hole_edges']))
        self.sp_hole.setSuffix(" edges round")
        self.sp_hole.setToolTip("The biggest hole to fill, by how many edges go round it.")
        hrow.addWidget(self.cb_fholes)
        hrow.addWidget(self.sp_hole)
        hrow.addStretch(1)
        self.cb_fwind = QCheckBox("Turn faces the right way out")
        self.cb_fwind.setChecked(bool(st['fix_winding']))
        self.cb_fwind.setToolTip("Every face of a solid should face out. Faces that don't are turned round.")
        for w in (self.cb_fclean, self.cb_fcracks):
            v.addWidget(w)
        v.addLayout(hrow)
        v.addWidget(self.cb_fwind)
        self.txt_check = QPlainTextEdit()
        self.txt_check.setReadOnly(True)
        self.txt_check.setPlaceholderText("Press Check to see what's wrong (if anything).")
        v.addWidget(self.txt_check, 1)

    def build_export_page(self):
        st = self.st
        v = self._page("Export", "Save it for printing, other 3D programs, web, CAD, laser cutting or drawings.")
        form = self._form()
        self.cb_purpose = QComboBox()
        for lab, key, _s in PURPOSES:
            self.cb_purpose.addItem(lab, key)
        self.cb_purpose.setCurrentIndex(max(0, self.cb_purpose.findData(st['purpose'])))
        self.cb_purpose.setToolTip("What the file is for. Picking one sets the file type and the settings below "
                                   "to suit it - you can still change them.")
        form.addRow("What it's for:", self.cb_purpose)
        self.cb_fmt = QComboBox()
        for f in FORMATS:
            self.cb_fmt.addItem(f[1], f[0])
        self.cb_fmt.setCurrentIndex(max(0, self.cb_fmt.findData(st['format'])))
        self.cb_fmt.setToolTip("The type of file to save.")
        form.addRow("File type:", self.cb_fmt)
        self.lbl_fmt = QLabel()
        self.lbl_fmt.setWordWrap(True)
        self.lbl_fmt.setStyleSheet("color: #555;")
        form.addRow(self.lbl_fmt)
        self.cb_funit = QComboBox()
        for lab, _mm, key in FILE_UNITS:
            self.cb_funit.addItem(lab, key)
        self.cb_funit.setCurrentIndex(max(0, self.cb_funit.findData(st['file_unit'])))
        self.cb_funit.setToolTip("The units the numbers in the file are in. Printing: millimetres. Web, games "
                                 "and most 3D programs: metres.")
        form.addRow("Units in the file:", self.cb_funit)
        self.cb_up = QComboBox()
        self.cb_up.addItem("Z up (printing, CAD)", False)
        self.cb_up.addItem("Y up (games, web, 3D programs)", True)
        self.cb_up.setCurrentIndex(1 if st['y_up'] else 0)
        self.cb_up.setToolTip("Which way is up in the file. It's turned, not mirrored.")
        form.addRow("Up is:", self.cb_up)
        self.cb_usescale = QCheckBox("At the new size (Scale page)")
        self.cb_usescale.setChecked(bool(st['use_scale']))
        self.cb_usescale.setToolTip("Ticked: the file is the new size (the model isn't changed). Unticked: the "
                                    "size it is in the model.")
        form.addRow(self.cb_usescale)
        self.cb_perpiece = QCheckBox("Keep the pieces separate")
        self.cb_perpiece.setChecked(bool(st['per_piece']))
        self.cb_perpiece.setToolTip("Each piece a separate named object (3MF, OBJ, GLB, VRML), layer (DXF) or group "
                                    "(SVG) - for STL and PLY, one file each in a new folder. Untick: all as one.")
        form.addRow(self.cb_perpiece)
        self.cb_layout = QComboBox()
        self.cb_layout.addItem("Side by side (on the bed)", 'bed')
        self.cb_layout.addItem("Centred on the ground", 'centre')
        self.cb_layout.addItem("Where they are", 'keep')
        self.cb_layout.setCurrentIndex(max(0, self.cb_layout.findData(st['layout'])))
        self.cb_layout.setToolTip("Where the pieces go in the file. Side by side: laid flat if ticked on the Pieces "
                                  "page, the gap between them set there.")
        form.addRow("Place them:", self.cb_layout)
        self.cb_colours = QCheckBox("Piece colours")
        self.cb_colours.setChecked(bool(st['colours']))
        self.cb_colours.setToolTip("For files that keep colours: OBJ, PLY, GLB / glTF, VRML, SVG.")
        form.addRow(self.cb_colours)
        self.cb_fixes = QCheckBox("Make the repairs (Repair page)")
        self.cb_fixes.setChecked(bool(st['apply_fixes']))
        form.addRow(self.cb_fixes)
        self.cb_view = QComboBox()
        for lab, key in VIEWS:
            self.cb_view.addItem(lab, key)
        self.cb_view.setCurrentIndex(max(0, self.cb_view.findData(st['view'])))
        self.cb_view.setToolTip("For flat drawings (DXF outline, SVG): which way the pieces are seen.")
        self.lab_view = QLabel("Drawing:")
        form.addRow(self.lab_view, self.cb_view)
        self.sp_png = QSpinBox()
        self.sp_png.setRange(200, 8000)
        self.sp_png.setSingleStep(200)
        self.sp_png.setValue(int(st['png_size']))
        self.sp_png.setSuffix(" pixels across")
        self.sp_png.setToolTip("How big the picture is. It's the preview as it is now - turn and zoom it first.")
        self.lab_png = QLabel("Picture size:")
        form.addRow(self.lab_png, self.sp_png)
        v.addLayout(form)
        # ---- your planned pieces, each lot to its own slicer, in the file type picked above
        box = QGroupBox("Your planned pieces (Pieces page)")
        bl = QVBoxLayout(box)
        self.lbl_exp_plan = QLabel()
        self.lbl_exp_plan.setWordWrap(True)
        bl.addWidget(self.lbl_exp_plan)
        self.cb_exp_send = QCheckBox("Send each lot to its slicer after saving (3MF and STL)")
        self.cb_exp_send.setChecked(True)
        self.cb_exp_send.setToolTip("After saving, each file opens in the slicer its pieces are planned for - one "
                                    "window per slicer. Other file types are just saved.")
        bl.addWidget(self.cb_exp_send)
        hb = flow_layout()
        self.b_exp_pieces = QPushButton("Save pieces by slicer...")
        self.b_exp_pieces.setToolTip("Saves your planned pieces with the settings above (file type, units, "
                                     "layout, repairs): one file for each slicer, in a folder you pick. Then "
                                     "sends each to its slicer if that's ticked. Your model isn't changed.")
        self.b_exp_pieces.clicked.connect(lambda *_: self.export_by_slicer())
        b_plan5 = QPushButton("Plan the pieces...")
        b_plan5.setToolTip("Pick parts, put them into pieces and choose each piece's slicer.")
        b_plan5.clicked.connect(lambda *_: self.plan_pieces())
        hb.addWidget(self.b_exp_pieces)
        hb.addWidget(b_plan5)

        bl.addLayout(hb)
        v.addWidget(box)
        v.addStretch(1)

    # ------------------------------------------------------------------ wiring
    def connect_changes(self):
        upd = self.changed
        self._shown_unit = self.show_unit()
        self.cb_show.currentIndexChanged.connect(lambda *_: self.reset_size_boxes(keep=True))
        self.cb_unit.currentIndexChanged.connect(lambda *_: self.reset_size_boxes())
        for cb in (self.cb_show, self.cb_unit, self.cb_mode, self.cb_scale, self.cb_from, self.cb_to,
                   self.cb_pivot, self.cb_split, self.cb_fmt, self.cb_funit, self.cb_up, self.cb_layout,
                   self.cb_view, self.cb_preview):
            cb.currentIndexChanged.connect(upd)
        for sp in [self.sp_scale, self.sp_pct, self.sp_from, self.sp_to, self.sp_gap, self.sp_nozzle,
                   self.sp_hole, self.sp_png] + self.bed:
            sp.valueChanged.connect(upd)
        self.cb_next.currentIndexChanged.connect(upd)
        for c in (self.cb_beside, self.cb_lock, self.cb_flat, self.cb_bed, self.cb_thin, self.cb_open, self.cb_fclean,
                  self.cb_fcracks, self.cb_fholes, self.cb_fwind, self.cb_usescale, self.cb_perpiece,
                  self.cb_colours, self.cb_fixes, self.cb_follow):
            c.toggled.connect(upd)
        self.ed_slicer.textChanged.connect(upd)
        self.cb_mode.currentIndexChanged.connect(lambda i: self.stack.setCurrentIndex(i))
        self.cb_purpose.currentIndexChanged.connect(self.purpose_picked)
        self.cb_fmt.currentIndexChanged.connect(self.format_picked)
        self.cb_bedp.currentIndexChanged.connect(self.printer_picked)
        self.cb_kind.currentIndexChanged.connect(upd)
        self.cb_pfmt.currentIndexChanged.connect(upd)
        self.tabs.currentChanged.connect(upd)
        for sp, ax in ((self.sp_w, 0), (self.sp_d, 1), (self.sp_h, 2)):
            sp.valueChanged.connect(lambda _v, ax=ax: self.size_typed(ax))
        self.format_picked(user=False)

    def changed(self, *_):
        if self._busy:
            return
        self.update_info()
        self._raw_ok = False
        self._pv_timer.start(350)
        self._save_timer.start(1200)

    def save_now(self):
        st = self.st
        st.update({
            'tab': self.tabs.currentIndex(), 'tab_name': self.tabs.tabText(self.tabs.currentIndex()), 'unit': self.cb_unit.currentData(),
            'show_unit': self.cb_show.currentData(), 'mode': self.cb_mode.currentData(),
            'scale': self.sp_scale.value(), 'percent': self.sp_pct.value(),
            'from_scale': self.sp_from.value(), 'to_scale': self.sp_to.value(),
            'lock': self.cb_lock.isChecked(), 'pivot': self.cb_pivot.currentData(),
            'split': self.cb_split.currentData(), 'gap': self.sp_gap.value(), 'lay_flat': self.cb_flat.isChecked(),
            'bed': self.cb_bed.isChecked(), 'bed_x': self.bed[0].value(), 'bed_y': self.bed[1].value(),
            'bed_z': self.bed[2].value(), 'nozzle': self.sp_nozzle.value(), 'warn_thin': self.cb_thin.isChecked(),
            'slicer': self.ed_slicer.text().strip(), 'slicers': self.slicers(),
            'open_after': self.cb_open.isChecked(),
            'printers': self.printers(), 'printer': self.cb_bedp.currentData() or '',
            'kind': self.cb_kind.currentData(), 'print_format': self.cb_pfmt.currentData(),
            'fix_clean': self.cb_fclean.isChecked(), 'fix_cracks': self.cb_fcracks.isChecked(),
            'fix_holes': self.cb_fholes.isChecked(), 'hole_edges': self.sp_hole.value(),
            'fix_winding': self.cb_fwind.isChecked(), 'purpose': self.cb_purpose.currentData(),
            'format': self.cb_fmt.currentData(), 'file_unit': self.cb_funit.currentData(),
            'y_up': bool(self.cb_up.currentData()), 'use_scale': self.cb_usescale.isChecked(),
            'per_piece': self.cb_perpiece.isChecked(), 'layout': self.cb_layout.currentData(),
            'colours': self.cb_colours.isChecked(), 'apply_fixes': self.cb_fixes.isChecked(),
            'view': self.cb_view.currentData(), 'png_size': self.sp_png.value(),
            'follow': self.cb_follow.isChecked(), 'preview': self.cb_preview.currentData(),
            'show_preview': self.cb_pv.isChecked(), 'beside': self.cb_beside.isChecked(),
            'next_how': self.cb_next.currentData(), 'before_fit': self.st.get('before_fit'),
            'project_folder': self.st.get('project_folder', '')})
        update_settings(studio=dict(st))

    def closeEvent(self, ev):
        try:
            self._timer.stop()
            self.save_now()
        except Exception:
            pass
        super().closeEvent(ev)

    # ---- export page: what it's for, the file type
    def purpose_picked(self, *_):
        key = self.cb_purpose.currentData()
        sets = next((s for _l, k, s in PURPOSES if k == key), {})
        if not sets:
            return
        self._busy = True
        try:
            if 'format' in sets:
                self.cb_fmt.setCurrentIndex(max(0, self.cb_fmt.findData(sets['format'])))
            if 'file_unit' in sets:
                self.cb_funit.setCurrentIndex(max(0, self.cb_funit.findData(sets['file_unit'])))
            if 'y_up' in sets:
                self.cb_up.setCurrentIndex(1 if sets['y_up'] else 0)
            for k, w in (('use_scale', self.cb_usescale), ('apply_fixes', self.cb_fixes),
                         ('colours', self.cb_colours), ('lay_flat', self.cb_flat)):
                if k in sets:
                    w.setChecked(bool(sets[k]))
            if 'layout' in sets:
                self.cb_layout.setCurrentIndex(max(0, self.cb_layout.findData(sets['layout'])))
            if 'view' in sets:
                self.cb_view.setCurrentIndex(max(0, self.cb_view.findData(sets['view'])))
        finally:
            self._busy = False
        self.format_picked(user=False)
        self.changed()

    def format_picked(self, *_a, user=True):
        f = FMT.get(self.cb_fmt.currentData(), FORMATS[0])
        self.lbl_fmt.setText(f[5])
        lines, pic = f[4] == 'lines', f[4] == 'picture'
        self.cb_view.setEnabled(lines)
        self.lab_view.setEnabled(lines)
        self.sp_png.setEnabled(pic)
        self.lab_png.setEnabled(pic)
        for w in (self.cb_funit, self.cb_up, self.cb_usescale, self.cb_perpiece, self.cb_layout, self.cb_fixes):
            w.setEnabled(not pic)
        self.cb_up.setEnabled(f[4] == 'mesh')
        self.cb_colours.setEnabled(f[0] in ('obj', 'ply', 'glb', 'gltf', 'wrl', 'svg'))
        if user and not self._busy:
            # picked by hand: 'What it's for' no longer says what was picked
            own = self.cb_purpose.findData('own')
            want = next((k for _l, k, s in PURPOSES if s.get('format') == f[0]), None)
            if want != self.cb_purpose.currentData() and own >= 0:
                self.cb_purpose.blockSignals(True)
                self.cb_purpose.setCurrentIndex(own)
                self.cb_purpose.blockSignals(False)

    # ---- printers: your own, in your order, then the ready-made sizes
    def printers(self):
        own = self.st.get('printers')
        if not isinstance(own, list):
            own = self.st['printers'] = []
        return own

    def fill_printers(self, select=None):
        """The printer list: your own printers (key 'own:<name>') in your order, a line, then the
        ready-made sizes (key 'preset:<n>')."""
        cb = self.cb_bedp
        keep = select if select is not None else cb.currentData()
        cb.blockSignals(True)
        cb.clear()
        for p in self.printers():
            cb.addItem("%s  (%s)" % (p.get('name', '?'), {'resin': 'resin', 'other': 'other'}.get(p.get('kind'), 'FDM')),
                       "own:" + str(p.get('name', '')))
        if self.printers():
            cb.insertSeparator(cb.count())
        for i, (lab, size) in enumerate(BEDS):
            cb.addItem(lab, "preset:%d" % i)
        j = cb.findData(keep) if keep else -1
        cb.setCurrentIndex(j if j >= 0 else 0)
        cb.blockSignals(False)
        self.printer_buttons()

    def picked_printer(self):
        """(your printer's dict, its place in your list) or (None, None) for a ready-made one."""
        key = self.cb_bedp.currentData() or ""
        if key.startswith("own:"):
            name = key[4:]
            for i, p in enumerate(self.printers()):
                if p.get('name') == name:
                    return p, i
        return None, None

    def printer_buttons(self):
        p, i = self.picked_printer()
        mine = p is not None
        for b in ('save', 'delete', 'up', 'down'):
            w = getattr(self, 'b_pr_' + b, None)
            if w is not None:
                w.setEnabled(mine)
        if mine:
            self.b_pr_up.setEnabled(i > 0)
            self.b_pr_down.setEnabled(i < len(self.printers()) - 1)

    def printer_picked(self, *_):
        p, _i = self.picked_printer()
        key = self.cb_bedp.currentData() or ""
        self._busy = True
        try:
            if p is not None:
                for s_, val in zip(self.bed, p.get('bed', (220, 220, 250))):
                    s_.setValue(float(val))
                self.cb_kind.setCurrentIndex(max(0, self.cb_kind.findData(p.get('kind', 'fdm'))))
                self.sp_nozzle.setValue(float(p.get('nozzle', 0.4)))
                self.cb_thin.setChecked(bool(p.get('warn_thin', True)))
                self.cb_pfmt.setCurrentIndex(max(0, self.cb_pfmt.findData(p.get('format', '3mf'))))
                self.set_slicers(p.get('slicers') or [], str(p.get('slicer', '')))
                if p.get('gap'):
                    self.sp_gap.setValue(float(p['gap']))
                self.cb_open.setChecked(bool(p.get('open_after', False)))
                self.lbl_printer.setText("Your printer '%s'. Change anything here and press Save to keep it." %
                                         p.get('name'))
            elif key.startswith("preset:"):
                lab, size = BEDS[int(key[7:])]
                if size:
                    for s_, val in zip(self.bed, size):
                        s_.setValue(val)
                resin = 'resin' in lab.lower()
                if size:
                    self.cb_kind.setCurrentIndex(self.cb_kind.findData('resin' if resin else 'fdm'))
                    self.sp_nozzle.setValue(0.2 if resin else 0.4)
                    self.cb_pfmt.setCurrentIndex(self.cb_pfmt.findData('stl' if resin else '3mf'))
                    self.sp_gap.setValue(2.0 if resin else 5.0)
                self.lbl_printer.setText("A ready-made size. To keep your own printer - its bed, nozzle and "
                                         "slicer - set this page up and press 'Save as new...'.")
        finally:
            self._busy = False
        self.printer_buttons()
        self.changed()

    def printer_now(self, name):
        return {'name': name, 'kind': self.cb_kind.currentData(), 'gap': self.sp_gap.value(),
                'bed': [s_.value() for s_ in self.bed], 'nozzle': self.sp_nozzle.value(),
                'warn_thin': self.cb_thin.isChecked(), 'format': self.cb_pfmt.currentData(),
                'slicer': self.ed_slicer.text().strip(), 'slicers': self.slicers(),
                'open_after': self.cb_open.isChecked()}

    def printer_save_as(self):
        from PySide6.QtWidgets import QInputDialog
        p, _i = self.picked_printer()
        normal = QLineEdit.EchoMode.Normal if hasattr(QLineEdit, 'EchoMode') else QLineEdit.Normal
        res = QInputDialog.getText(self, "New printer", "A name for this printer:", normal,
                                   (p.get('name', '') + " copy") if p else "My printer")
        name, ok = (res[0], res[1]) if isinstance(res, (tuple, list)) else (res, bool(res))
        name = (name or "").strip()
        if not ok or not name:
            return
        own = self.printers()
        old = next((j for j, q in enumerate(own) if q.get('name') == name), None)
        if old is not None:
            if QMessageBox.question(self, PLUGIN_NAME, "You already have a printer called '%s'. Replace it?" % name) \
                    != QMessageBox.StandardButton.Yes:
                return
            own[old] = self.printer_now(name)
        else:
            own.insert(0, self.printer_now(name))          # new ones go at the top
        self.fill_printers("own:" + name)
        self.printer_picked()
        self.save_now()
        self.report("Saved your printer '%s'. Use Up and Down to put your printers in the order you like." % name)

    def printer_save(self):
        p, i = self.picked_printer()
        if p is None:
            return
        self.printers()[i] = self.printer_now(p.get('name'))
        self.fill_printers("own:" + p.get('name'))
        self.save_now()
        self.report("Updated your printer '%s'." % p.get('name'))

    def printer_delete(self):
        p, i = self.picked_printer()
        if p is None:
            return
        if QMessageBox.question(self, PLUGIN_NAME, "Delete your printer '%s'?" % p.get('name')) \
                != QMessageBox.StandardButton.Yes:
            return
        del self.printers()[i]
        self.fill_printers()
        self.printer_picked()
        self.save_now()

    def printer_move(self, d):
        p, i = self.picked_printer()
        own = self.printers()
        if p is None or not (0 <= i + d < len(own)):
            return
        own[i], own[i + d] = own[i + d], own[i]
        self.fill_printers("own:" + p.get('name'))
        self.save_now()

    def find_slicers(self, button=None):
        """Looks in the usual program folders for slicers; a menu of what's found to pick from."""
        from PySide6.QtWidgets import QMenu, QApplication
        from PySide6.QtCore import Qt
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            found = find_slicer_programs()
        finally:
            QApplication.restoreOverrideCursor()
        if not found:
            self.report("No slicers found in the usual program folders - use Browse... to find yours.", bad=True)
            return
        menu = QMenu(self)
        for path in found:
            act = menu.addAction(path)
            act.triggered.connect(lambda *_a, p=path: self.add_slicer(p))
        try:
            menu.exec(button.mapToGlobal(button.rect().bottomLeft()) if button is not None else None)
        except Exception:
            menu.exec()

    def use_converter_scale(self, *_):
        n = self.conv.scale()
        self.cb_mode.setCurrentIndex(max(0, self.cb_mode.findData('scale')))
        idx = self.cb_scale.count() - 1
        for i in range(self.cb_scale.count()):
            d = self.cb_scale.itemData(i)
            if d is not None and abs(d - n) < 1e-9:
                idx = i
        self.cb_scale.setCurrentIndex(idx)
        self.sp_scale.setValue(n)
        self.tabs.setCurrentIndex(1)

    def browse_slicer(self, *_):
        from PySide6.QtWidgets import QFileDialog
        start = self.ed_slicer.text() or ("C:\\Program Files" if os.name == 'nt' else os.path.expanduser("~"))
        res = QFileDialog.getOpenFileName(self, "Your slicer's program", start, "Programs (*.exe);;All files (*)")
        path = res[0] if isinstance(res, (tuple, list)) else res
        if path:
            self.add_slicer(os.path.normpath(path))

    # ------------------------------------------------------------------ this printer's slicers
    def slicers(self):
        """This printer's slicers (full paths), the one showing included."""
        out = []
        for i in range(self.cb_slicer.count()):
            out.append(self.cb_slicer.itemData(i) or self.cb_slicer.itemText(i))
        now = self.ed_slicer.text().strip()
        if now:
            out.append(now)
        seen, keep = set(), []
        for x in out:
            x = str(x or "").strip()
            if x and os.path.normcase(x) not in seen:
                seen.add(os.path.normcase(x))
                keep.append(x)
        return keep

    def set_slicers(self, paths, current=""):
        """Fills the slicer list (a printer's old single slicer counts as a list of one)."""
        from PySide6.QtCore import Qt
        paths = [str(x).strip() for x in (paths or []) if str(x or "").strip()]
        current = str(current or "").strip()
        if current and os.path.normcase(current) not in [os.path.normcase(x) for x in paths]:
            paths.insert(0, current)
        cb = self.cb_slicer
        cb.blockSignals(True)
        cb.clear()
        for x in paths:
            cb.addItem(x, x)
            cb.setItemData(cb.count() - 1, x, Qt.ItemDataRole.ToolTipRole)
        cb.blockSignals(False)
        self.ed_slicer.setText(current or (paths[0] if paths else ""))

    def add_slicer(self, path):
        path = str(path or "").strip()
        if not path:
            return
        self.set_slicers(self.slicers() + [path], path)
        self.report("Added %s to this printer's slicers (%d now). Save the printer to keep it." %
                    (os.path.basename(path), len(self.slicers())))

    def remove_slicer(self, *_):
        now = self.ed_slicer.text().strip()
        if not now:
            return
        rest = [x for x in self.slicers() if os.path.normcase(x) != os.path.normcase(now)]
        self.set_slicers(rest, rest[0] if rest else "")
        self.report("Took %s off this printer's slicers." % os.path.basename(now))

    def pick_slicer(self, button=None):
        """With more than one slicer: a menu to pick the one that suits this model. True to carry on."""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QCursor
        many = self.slicers()
        if len(many) < 2:
            return True
        now = os.path.normcase(self.ed_slicer.text().strip())
        menu = QMenu(self)
        menu.addSection("Send it to which slicer?")
        for path in many:
            name = os.path.splitext(os.path.basename(path))[0] or path
            act = menu.addAction(name)
            act.setToolTip(path)
            act.setCheckable(True)
            act.setChecked(os.path.normcase(path) == now)
            act.setData(path)
        try:
            menu.setToolTipsVisible(True)
        except Exception:
            pass
        at = button.mapToGlobal(button.rect().bottomLeft()) if button is not None else QCursor.pos()
        chosen = menu.exec(at)
        if chosen is None or not chosen.data():
            return False
        self.ed_slicer.setText(str(chosen.data()))
        return True

    def send_to_slicer_pick(self, button=None, save_as=False):
        """'Send to slicer' button: asks which slicer first when this printer has more than one
        (not when your plan already says where every piece goes)."""
        own = ((self.plan or {}).get('printer') or {}) if self.plan_on() else {}
        pcs = self.raw_piece_names() if own else []
        all_set = bool(pcs) and all(pc is not None and self.norm_target(own.get(pc or "", "")) for pc in pcs)
        if not all_set and not self.pick_slicer(button):
            return False
        return self.send_to_slicer(save_as)

    # ------------------------------------------------------------------ the selection
    def selection(self):
        scene = getattr(self.viewport, 'scene', None)
        return list(getattr(scene, 'selection', None) or [])

    def watch_selection(self, force=False):
        if not force and not self.cb_follow.isChecked():
            return
        try:
            ents = self.selection()
        except Exception:
            return
        key = tuple(id(e) for e in ents)
        if key == self._sel_key and not force:
            return
        if not force and not ents and self.ents:
            return              # clicked off it: keep showing what was selected
        if not force and key == self._sel_key:
            return
        self._sel_key = key
        self.ents = ents
        self._waiting = False
        try:
            self.size, text = selection_size(ents)
        except Exception as e:
            self.size, text = (0.0, 0.0, 0.0), "Couldn't read the selection: %s" % e
        self._sel_text = text
        self._raw = None
        self._marks = []
        if getattr(self, '_typed', False) and self.cb_mode.currentData() == 'size':
            self.follow_typed_size()          # the size you typed, for this object too
        else:
            self.reset_size_boxes()
        self.update_info()
        self.refresh_preview()

    def name(self):
        for e in self.ents:
            if getattr(e, 'name', None):
                return str(e.name)
        return "model"

    def unit_mm(self):
        key = self.cb_unit.currentData()
        return dict((u[2], u[1]) for u in UNITS).get(key, 1000.0)

    def show_unit(self):
        return self.cb_show.currentData() or 'mm'

    def size_mm(self):
        k = self.unit_mm()
        return tuple(v * k for v in self.size)

    # ---- the new size
    def _den(self, cb, sp):
        n = cb.currentData()
        return n if n else sp.value()

    def factors(self):
        """How much each way (x, y, z) the Scale page makes it bigger (or smaller)."""
        mode = self.cb_mode.currentData()
        if mode == 'scale':
            f = 1.0 / max(1e-12, self._den(self.cb_scale, self.sp_scale))
            return (f, f, f)
        if mode == 'percent':
            f = self.sp_pct.value() / 100.0
            return (f, f, f)
        if mode == 'rescale':
            f = self._den(self.cb_from, self.sp_from) / max(1e-12, self._den(self.cb_to, self.sp_to))
            return (f, f, f)
        k = dict(SHOW_UNITS).get(self.show_unit(), 1.0)
        now = self.size_mm()
        want = (self.sp_w.value() * k, self.sp_d.value() * k, self.sp_h.value() * k)
        fs = [w / n if n > 1e-12 else None for w, n in zip(want, now)]
        if self.cb_lock.isChecked():
            ax = getattr(self, '_drive_ax', 0)
            f = fs[ax] if fs[ax] is not None else next((x for x in fs if x is not None), 1.0)
            return (f, f, f)
        return tuple(1.0 if x is None else x for x in fs)

    def describe(self):
        """The new size in words: '1:76.2', '50 %', '120 x 40 x 60 mm'."""
        mode = self.cb_mode.currentData()
        if mode == 'scale':
            return "1:%g" % self._den(self.cb_scale, self.sp_scale)
        if mode == 'percent':
            return "%g %%" % self.sp_pct.value()
        if mode == 'rescale':
            return "1:%g to 1:%g" % (self._den(self.cb_from, self.sp_from), self._den(self.cb_to, self.sp_to))
        f = self.factors()
        if abs(f[0] - f[1]) < 1e-9 and abs(f[1] - f[2]) < 1e-9:
            return "%g %%" % round(f[0] * 100, 4)
        return "%g x %g x %g %%" % tuple(round(x * 100, 3) for x in f)

    def new_size_mm(self):
        f = self.factors()
        return tuple(v * x for v, x in zip(self.size_mm(), f))

    def reset_size_boxes(self, *_a, keep=False):
        """The size boxes show the object's size now (or, keep: the size typed, in the new units)."""
        u = self.show_unit()
        k = dict(SHOW_UNITS).get(u, 1.0)
        old_k = dict(SHOW_UNITS).get(getattr(self, '_shown_unit', u), 1.0)
        now = self.size_mm()
        self._busy = True
        try:
            for i, sp in enumerate((self.sp_w, self.sp_d, self.sp_h)):
                mm = sp.value() * old_k if keep else now[i]
                sp.setDecimals(3 if k < 25 else 4)
                sp.setSuffix(" " + u)
                sp.setValue(mm / k)
                self.lbl_now[i].setText("now " + fmt_len(now[i], u))
            self._shown_unit = u
            if not keep:
                self._typed = False
        finally:
            self._busy = False
        self.update_info()

    def follow_typed_size(self):
        """A new object selected after typing a size: keeps the size typed (in proportion: the one you
        typed, the others worked out for this object's shape)."""
        now = self.size_mm()
        for i in range(3):
            self.lbl_now[i].setText("now " + fmt_len(now[i], self.show_unit()))
        if self.cb_lock.isChecked():
            self.size_typed(getattr(self, '_drive_ax', 0), quiet=True)
        self.update_info()

    def size_typed(self, ax, quiet=False):
        if self._busy:
            return
        self._typed = True
        self._drive_ax = ax
        if self.cb_lock.isChecked():
            now = self.size_mm()
            k = dict(SHOW_UNITS).get(self.show_unit(), 1.0)
            sps = (self.sp_w, self.sp_d, self.sp_h)
            if now[ax] > 1e-12:
                f = sps[ax].value() * k / now[ax]
                self._busy = True
                try:
                    for i, sp in enumerate(sps):
                        if i != ax:
                            sp.setValue(now[i] * f / k)
                finally:
                    self._busy = False
        if not quiet:
            self.changed()

    # ------------------------------------------------------------------ sizes and words
    def update_info(self, *_):
        u = self.show_unit()
        now = self.size_mm()
        new = self.new_size_mm()
        has = max(now) > 0
        sel = getattr(self, '_sel_text', "Nothing selected")
        if self._waiting:
            self.lbl_sel.setText("<b>%s</b>" % sel)
        else:
            self.lbl_sel.setText("<b>%s</b>   %s" % (self.name() if self.ents else "", sel) +
                                 ("   -   size %s" % fmt_size(now, u) if has else ""))
        f = self.factors()
        txt = ("Now: %s<br><b>New size: %s</b>  (%s)" % (fmt_size(now, u), fmt_size(new, u), self.describe())
               if has else "Select the object (a group, or its faces) in the work area.")
        small = [v for v in new if v > 0]
        if has and small and max(new) < 0.1:
            txt += ("<br><span style='color:#b35900'>Under 0.1 mm: IngeTrazo merges points closer than that, "
                    "so scaling it this small in the work area loses it. Export keeps every detail.</span>")
        elif has and small and min(f) < 1.0 and min(small) < 1.0:
            txt += "<br>Some of it is under 1 mm - fine detail: good for resin, too small for a 0.4 mm nozzle."
        elif has and 0 < min(f) < 0.05:
            txt += ("<br>Small details (under about %s at full size) end up under 0.1 mm - in the work area "
                    "IngeTrazo merges them; Export keeps them." % fmt_len(0.1 / min(f), u))
        self.lbl_scale_info.setText(txt)
        # print page: does it fit
        if self.cb_bed.isChecked() and has:
            bed = tuple(s.value() for s in self.bed)
            sx, sy, sz = new
            fits = sz <= bed[2] and ((sx <= bed[0] and sy <= bed[1]) or (sy <= bed[0] and sx <= bed[1]))
            big = biggest_that_fits(now, bed)
            n_fit = 1.0 / big if big > 0 else 0
            t = ("<b>This object at the new size: %s</b><br>" % fmt_size(new, 'mm'))
            t += ("<span style='color:#2e7d32'>It fits on the print bed.</span>" if fits else
                  "<span style='color:#c0392b'>Too big for the print bed (as it stands; laying pieces flat "
                  "may help).</span>")
            t += "<br>Biggest that fits as it stands: 1:%s (%s %% of full size)." % (
                ("%.1f" % n_fit) if n_fit >= 10 else ("%.3g" % n_fit), "%.3g" % (big * 100))
            self.lbl_fit.setText(t + self.gathered_fit_html())
            self.b_fit.setEnabled(True)
        else:
            self.lbl_fit.setText(("" if has else "Select the object first.") + self.gathered_fit_html())
            self.b_fit.setEnabled(False)
        for w in self.bed:
            w.setEnabled(self.cb_bed.isChecked())
        self.sp_nozzle.setEnabled(self.cb_thin.isChecked())
        self.sp_hole.setEnabled(self.cb_fholes.isChecked())
        planned = self.plan_on()
        self.cb_split.setEnabled(not planned)
        self.b_unplan.setEnabled(bool(self.plan and self.plan.get('pieces')))
        on_pn = getattr(self, '_pn_index', -1) == self.tabs.currentIndex()
        self.canvas.overlay = (["Now: " + fmt_size(now, u), "New: %s  (%s)" % (fmt_size(new, u), self.describe())]
                               if has and not (on_pn and self._waiting) else []) + list(getattr(self, '_bed_note', None) or [])
        self.canvas.update()

    def use_biggest(self, *_):
        bed = tuple(s.value() for s in self.bed)
        big = biggest_that_fits(self.size_mm(), bed)
        if big <= 0:
            return
        n = 1.0 / big
        n = math.ceil(n * 10.0 - 1e-9) / 10.0 if n >= 1 else n     # a round number that still fits
        self.st['before_fit'] = self.scale_state()                  # so 'Back to the scale before' can undo it
        self.cb_mode.setCurrentIndex(max(0, self.cb_mode.findData('scale')))
        self.cb_scale.setCurrentIndex(self.cb_scale.count() - 1)       # Custom
        self.sp_scale.setValue(n)
        self.report("Set the scale to 1:%g - the biggest that fits on your bed as it stands. 'Back to the scale "
                    "before' (3D print page) undoes it." % n)
        self.fit_buttons()
        self.save_now()

    # ------------------------------------------------------------------ projects
    def project_folder(self):
        d = self.st.get('project_folder') or os.path.join(os.path.expanduser("~"), "Documents",
                                                            "3D Scale Studio projects")
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass
        return d

    def save_project(self):
        from PySide6.QtWidgets import QFileDialog

        def tr_out(tris):
            return [[[round(c, 4) for c in p] for p in t] for t in tris]
        name = "".join(ch for ch in self.name() if ch not in '\\/:*?"<>|').strip() or "My project"
        res = QFileDialog.getSaveFileName(self, "Save project", os.path.join(self.project_folder(), name + ".json"),
                                          "3D Scale Studio project (*.json)")
        path = res[0] if isinstance(res, (tuple, list)) else res
        if not path:
            return False
        if not path.lower().endswith(".json"):
            path += ".json"
        cur, _i = self.picked_printer()
        data = {'kind': '3D Scale Studio project', 'version': 1,
                'plan': self.plan, 'scale': self.scale_state(), 'before_fit': self.st.get('before_fit'),
                'printer': cur.get('name') if cur else '',
                'pieces': {'split': self.cb_split.currentData(), 'gap': self.sp_gap.value(),
                           'lay_flat': self.cb_flat.isChecked()},
                'bed': [{'name': nm, 'scale': sc, 'printers': list(ds),
                         'parts': [{'name': n, 'colour': list(c), 'tris': tr_out(tr)} for n, c, tr in parts]}
                        for nm, sc, parts, ds in self._bed]}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            self.report("Couldn't save the project: %s" % e, bad=True)
            return False
        self.st['project_folder'] = os.path.dirname(path)
        self.save_now()
        n = len(self._bed)
        self.report("Saved the project:\n%s\n(%s, %d object%s on the gathered bed, scale %s)" % (
            path, "a piece plan" if self.plan else "no piece plan", n, "" if n == 1 else "s", self.describe()))
        return True

    def open_project(self):
        from PySide6.QtWidgets import QFileDialog
        res = QFileDialog.getOpenFileName(self, "Open project", self.project_folder(),
                                          "3D Scale Studio project (*.json);;All files (*)")
        path = res[0] if isinstance(res, (tuple, list)) else res
        if not path:
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get('kind') != '3D Scale Studio project':
                raise ValueError("that isn't a 3D Scale Studio project")
            bed = []
            for b in data.get('bed') or []:
                parts = [(str(p.get('name', 'Piece')), tuple(p.get('colour') or (200, 200, 200)),
                          [tuple(tuple(c) for c in t) for t in p.get('tris') or []]) for p in b.get('parts') or []]
                bed.append((str(b.get('name', 'Object')), str(b.get('scale', '')), parts,
                            list(b.get('printers') or [""] * len(parts))))
        except Exception as e:
            self.report("Couldn't open the project: %s" % e, bad=True)
            return False
        if self._bed:
            StudioDialog._taken.append((None, list(self._bed)))     # 'Put back' brings the old bed back
        del self._bed[:]
        self._bed.extend(bed)
        self.plan = data.get('plan') or None
        StudioDialog._plan = self.plan
        self._raw = None
        self._busy = True
        try:
            self.set_scale_state(data.get('scale'))
            pc = data.get('pieces') or {}
            if 'split' in pc:
                self.cb_split.setCurrentIndex(max(0, self.cb_split.findData(pc['split'])))
            if pc.get('gap'):
                self.sp_gap.setValue(float(pc['gap']))
            if 'lay_flat' in pc:
                self.cb_flat.setChecked(bool(pc['lay_flat']))
        finally:
            self._busy = False
        self.st['before_fit'] = data.get('before_fit')
        if data.get('printer'):
            j = self.cb_bedp.findData("own:" + data['printer'])
            if j >= 0:
                self.cb_bedp.setCurrentIndex(j)
        self.st['project_folder'] = os.path.dirname(path)
        self._bed_view = self._plan_view = 0
        self.fit_buttons()
        self.bed_buttons()
        self.changed()
        self.refresh_preview()
        n = len(bed)
        self.report("Opened the project %s: %s, %d object%s on the gathered bed, scale %s.%s" % (
            os.path.basename(path), "its piece plan" if self.plan else "no piece plan", n, "" if n == 1 else "s",
            self.describe(), " Select the same model for the plan to fit." if self.plan else ""))
        return True

    def scale_state(self):
        """How the Scale page is set (to save and put back)."""
        return {'mode': self.cb_mode.currentData(), 'scale': self.sp_scale.value(),
                'scale_item': self.cb_scale.currentIndex(), 'percent': self.sp_pct.value(),
                'from_scale': self.sp_from.value(), 'to_scale': self.sp_to.value()}

    def set_scale_state(self, d):
        if not d:
            return
        self.cb_mode.setCurrentIndex(max(0, self.cb_mode.findData(d.get('mode', 'scale'))))
        i = int(d.get('scale_item', -1))
        if 0 <= i < self.cb_scale.count():
            self.cb_scale.setCurrentIndex(i)
        self.sp_scale.setValue(float(d.get('scale', self.sp_scale.value())))
        self.sp_pct.setValue(float(d.get('percent', self.sp_pct.value())))
        self.sp_from.setValue(float(d.get('from_scale', self.sp_from.value())))
        self.sp_to.setValue(float(d.get('to_scale', self.sp_to.value())))

    def scale_back(self, *_):
        d = self.st.get('before_fit')
        if not d:
            self.report("There's no scale to go back to.")
            return
        self.set_scale_state(d)
        self.st['before_fit'] = None
        self.fit_buttons()
        self.changed()
        self.save_now()
        self.report("Back to %s, the scale before 'Use the biggest that fits'." % self.describe())

    def fit_buttons(self):
        d = self.st.get('before_fit')
        try:
            self.b_unfit.setVisible(bool(d))
            if d:
                self.b_unfit.setText("Back to 1:%g" % float(d.get('scale', 0)) if d.get('mode') == 'scale'
                                     else "Back to the scale before")
        except Exception:
            pass

    # ------------------------------------------------------------------ pieces
    def split_depth(self):
        return self.cb_split.currentData()

    def plan_on(self):
        """True when there's a plan and it was made for what's selected now (a plan made for the
        canopy mustn't be used on a cylinder selected later)."""
        if not (self.plan and self.plan.get('pieces')) or not self.ents:
            return False
        sig = (self._sel_key, id(self.plan))
        fit = getattr(self, '_plan_fit', None)
        if fit and fit[0] == sig:
            return fit[1]
        try:
            known = set(k for k, _n, _kd, _t in piece_leaves(self.ents, with_tris=False))
        except Exception:
            known = set()
        ok = bool(set((self.plan.get('keys') or {}).keys()) & known)
        self._plan_fit = (sig, ok)
        return ok

    def raw_parts(self):
        """The pieces in the model's units: [(name, colour, tris)]."""
        planned = self.plan_on()
        key = (self._sel_key, self.split_depth(), id(self.plan) if planned else None,
               getattr(self, '_only_top', None))
        if self._raw is not None and self._raw[0] == key:
            return self._raw[1]
        ents = self.ents
        out = []
        self._raw_pieces = []
        if ents:
            if planned:
                tops = []
                leaves = piece_leaves(ents, tops_out=tops)
                only = getattr(self, '_only_top', None)
                if only is not None:
                    leaves = [lf for lf, t in zip(leaves, tops) if t == only]
                raw3 = plan_parts(leaves, self.plan, with_piece=True)
                raw = [(n, tr) for n, tr, _p in raw3]
                self._raw_pieces = [p_ for n, tr, p_ in raw3 if tr]
            elif getattr(self, '_only_top', None) is not None:
                # one of the selected objects on its own (no plan): its parts as the Pieces list says
                tops = []
                leaves = [lf for lf, t in zip(piece_leaves(ents, tops_out=tops), tops) if t == self._only_top]
                if self.split_depth() is not None and self.split_depth() >= 0:
                    raw = [(nm, tr) for _k, nm, _kd, tr in leaves]
                else:
                    raw = [("Object", [t for lf in leaves for t in lf[3]])] if leaves else []
            elif self.split_depth() is not None and self.split_depth() >= 0:
                raw = split_parts(ents, int(self.split_depth()))
            else:
                tris = []
                for outer, holes, f in world_loops(ents):
                    for t in face_triangles(f):
                        q = [vertex_to_vector3d(v) if not isinstance(v, QVector3D) else v for v in t]
                        if any(x is None for x in q):
                            continue
                        tris.append(tuple((x.x(), x.y(), x.z()) for x in q))
                raw = [(self.name(), tris)] if tris else []
            single = len(raw) == 1
            out = [(n, (206, 172, 120) if single else piece_colour(i), tr) for i, (n, tr) in enumerate(raw) if tr]
        self._raw = (key, out)
        return out

    def raw_piece_names(self):
        """The plan's piece for each part raw_parts gives ("" on its own; None without a plan)."""
        raw = self.raw_parts()
        pcs = list(getattr(self, '_raw_pieces', None) or [])
        return pcs if len(pcs) == len(raw) else [None] * len(raw)

    def plan_pieces(self, *_):
        tops = []
        leaves = piece_leaves(self.ents, tops_out=tops)
        if not leaves:
            self.report("Select the object (a group, or its faces) first.", bad=True)
            return
        # the objects you selected, so you can work on them one at a time
        objects = []
        for t in sorted(set(tops), key=lambda x: (x < 0, x)):
            if t >= 0:
                e = self.ents[t]
                nm = str(getattr(e, 'name', '') or "Object %d" % (t + 1))
            else:
                nm = "Selected faces"
            objects.append((t, nm, [i for i, x in enumerate(tops) if x == t]))
        pdlg = PiecesDialog(self, leaves, self.plan, [(k, lab) for k, lab, _p, _pr in self.printer_targets()],
                            objects=objects)
        pdlg.on_apply = self.apply_plan
        pdlg.on_scale_next = self.scale_next_object
        try:
            eddy_window(pdlg, PLUGIN_NAME + " - pieces", EDDY_TIPS, place=True)
        except Exception:
            pass
        if pdlg.exec():
            self.plan = pdlg.plan()
            StudioDialog._plan = self.plan
            self._raw = None
            self.changed()
            self.refresh_preview()
            if getattr(pdlg, 'send_after', False):
                self.send_to_slicer_pick()
            elif getattr(pdlg, 'scale_next_after', False):
                # straight onto the gathered bed, and show it, so you can see where each piece went
                self.scale_and_next('bed', force=True)
                if self._bed:
                    self._bed_view = 0
                    self.show_gathered()

    def scale_next_object(self, plan, top, name):
        """Plan window, several objects selected: puts just this one on the gathered bed, at the
        scale on the Scale page. Returns (it worked, words)."""
        self.apply_plan(plan)
        ok = self.add_to_bed(top=top, name=name)
        if not ok:
            return False, self._last
        self._done += 1
        n = len(self._bed)
        try:
            self.lbl_count.setText("On the bed: %d object%s." % (n, "" if n == 1 else "s"))
        except Exception:
            pass
        words = "'%s' is on the gathered bed at %s - %s." % (name, self.describe(), getattr(self, '_bed_split', ""))
        self.report(words + " (%d on the bed)" % n)
        return True, words

    def apply_plan(self, plan):
        """'Use these pieces' in the plan window: the plan is used at once, the window stays open."""
        self.plan = plan
        StudioDialog._plan = plan
        self._raw = None
        self.changed()
        self.refresh_preview()

    def forget_plan(self, *_):
        self.plan = None
        StudioDialog._plan = None
        self._raw = None
        self.changed()
        self.refresh_preview()

    def fill_piece_table(self, parts):
        from PySide6.QtGui import QPixmap, QColor, QIcon
        u = self.show_unit()
        f = self.factors()
        k = self.unit_mm()
        self.tbl.setRowCount(len(parts))
        sizes = {}
        # what your plan says for each piece: holes closed, which slicer
        notes = []
        pcs = self.raw_piece_names() if len(parts) == len(self.raw_parts()) else [None] * len(parts)
        own_s = ((self.plan or {}).get('printer') or {}) if self.plan_on() else {}
        close = set((self.plan or {}).get('close', []))
        for pc in pcs:
            bits = []
            if pc is not None and pc in close:
                bits.append("holes closed")
            if pc is not None and own_s.get(pc or ""):
                bits.append("\u2192 " + self.target_name(own_s.get(pc or "", "")).split(" - ")[0])
            notes.append(", ".join(bits))
        for r, (n, col, tr) in enumerate(parts):
            s = tris_size(tr)
            s = (s[0] * k * f[0], s[1] * k * f[1], s[2] * k * f[2])
            sizes[r] = fmt_size(s, u)
            pm = QPixmap(14, 14)
            pm.fill(QColor(*col))
            it = QTableWidgetItem(QIcon(pm), str(n))
            self.tbl.setItem(r, 0, it)
            self.tbl.setItem(r, 1, QTableWidgetItem(sizes[r]))
            self.tbl.setItem(r, 2, QTableWidgetItem(str(len(tr))))
            self.tbl.setItem(r, 3, QTableWidgetItem(notes[r] if r < len(notes) else ""))
        self.canvas.piece_sizes = sizes
        planned = self.plan_on()
        other = bool(self.plan and self.plan.get('pieces')) and not planned and bool(self.ents)
        self.lbl_pieces.setText("%d piece%s%s." % (len(parts), "" if len(parts) == 1 else "s",
                                                   " (your plan)" if planned else
                                                   " - your plan is for another object, so it isn't used here"
                                                   if other else ""))
        try:
            self.lbl_exp_plan.setText(self.plan_words())
        except Exception:
            pass

    def piece_row_picked(self, *_):
        rows = sorted({ix.row() for ix in self.tbl.selectionModel().selectedRows()}) \
            if self.tbl.selectionModel() else []
        if rows:
            self.canvas.picked = rows[0]
            self.canvas.update()

    def piece_picked(self, i):
        if i is None:
            return
        try:
            self.tbl.blockSignals(True)
            self.tbl.selectRow(i)
        finally:
            self.tbl.blockSignals(False)

    # ------------------------------------------------------------------ preview
    def refresh_preview(self):
        if getattr(self, '_pn_index', -1) == self.tabs.currentIndex():
            try:
                self.preview_print_next()
            except Exception as e:
                self.canvas.set_parts([], None)
                self.report("Couldn't draw the bed: %s" % e, bad=True)
            self.update_info()
            return
        if getattr(self, '_gathered_on', False):
            self.preview_gathered()
            if self.ents:
                try:
                    self.fill_piece_table(self.raw_parts())
                except Exception:
                    pass
            self.update_info()
            return
        if not self.ents:
            self._bed_note = []
            self.b_nextbed.setVisible(False)
            self.canvas.set_parts([], None)
            self._shown = None
            self.fill_piece_table([])
            return
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            raw = self.raw_parts()
            self.fill_piece_table(raw)
            groups = self.planned_slicers() if self.cb_preview.currentData() == 'bed' else None
            if groups:
                self.preview_planned_bed(groups)
            elif self.cb_preview.currentData() == 'bed':
                self.b_nextbed.setVisible(False)
                self._bed_note = []
                parts, _notes, _w = self.make_parts({'use_scale': True, 'layout': 'bed', 'apply_fixes': False,
                                                    'per_piece': True})
                bed = (self.bed[0].value(), self.bed[1].value()) if self.cb_bed.isChecked() else None
                if bed is None and parts:
                    s = tris_size([t for _n, _c, tr in parts for t in tr])
                    bed = (s[0] * 1.15 + 10, s[1] * 1.15 + 10)
                self.canvas.empty_text = "Nothing to show"
                self.canvas.set_parts(parts, bed, None)
                self._shown = None
            else:
                self.b_nextbed.setVisible(False)
                self._bed_note = []
                shown = (id(raw), len(self._marks), 'model')
                if getattr(self, '_shown', None) != shown:
                    self.canvas.set_parts(raw, None, self._marks)
                    self._shown = shown
        except Exception as e:
            self.canvas.set_parts([], None)
            self.report("Couldn't draw the preview: %s" % e, bad=True)
        finally:
            QApplication.restoreOverrideCursor()
        self.update_info()

    # ------------------------------------------------------------------ making the pieces
    def repair_opts(self):
        return {'fix_clean': self.cb_fclean.isChecked(), 'fix_cracks': self.cb_fcracks.isChecked(),
                'fix_holes': self.cb_fholes.isChecked(), 'hole_edges': self.sp_hole.value(),
                'fix_winding': self.cb_fwind.isChecked()}

    def make_parts(self, o):
        """The pieces in mm ready for a file: scaled, repaired, laid out. Returns (parts, notes,
        anything worth a warning)."""
        notes, warn = [], False
        if o.get('parts') is not None:
            # ready-made pieces (in mm, already scaled and mended) - the objects gathered on one bed
            parts = list(o['parts'])
        else:
            raw = self.raw_parts()
            pcs = self.raw_piece_names()
            k = self.unit_mm()
            f = self.factors() if o.get('use_scale', True) else (1.0, 1.0, 1.0)
            only = o.get('only')
            close = set((self.plan or {}).get('close', [])) if self.plan and self.plan.get('pieces') else set()
            parts = []
            for i, (n, c, tr) in enumerate(raw):
                if only is not None and i not in only:
                    continue
                tr = scale_tris(tr, (k * f[0], k * f[1], k * f[2]))
                if pcs[i] is not None and pcs[i] in close:
                    tr, filled, left = close_all_holes(tr)
                    if filled or left:
                        notes.append("%s: closed %d hole%s%s." % (
                            n, filled, "" if filled == 1 else "s",
                            (" (%d couldn't be - edges shared by more than two faces)" % left) if left else ""))
                parts.append((n, c, tr))
            if not o.get('per_piece', True) and len(parts) > 1 and o.get('layout', 'keep') != 'bed':
                # all as one, where they are (on the bed they're laid out first, then joined - below)
                parts = [(o.get('name') or self.name(), parts[0][1], [t for _n, _c, tr in parts for t in tr])]
        if o.get('apply_fixes') and o.get('parts') is None:
            tot = {}
            fixed = []
            for n, c, tr in parts:
                tr, cnt = repair_part(tr, self.repair_opts())
                for kk, vv in cnt.items():
                    tot[kk] = tot.get(kk, 0) + vv
                fixed.append((n, c, tr))
            parts = fixed
            notes += repair_lines(tot)
        if o.get('thin') and self.cb_thin.isChecked():
            nz = self.sp_nozzle.value()
            resin = self.cb_kind.currentData() == 'resin'
            if resin and nz >= 0.25:
                nz = 0.05            # a resin printer saved with an FDM nozzle size: check against resin detail
            what = "the %.2f mm smallest detail this resin printer does" % nz if resin else "the %.2f mm nozzle" % nz
            for n, c, tr in parts:
                try:
                    th, share = thin_walls(tr, nz)
                except Exception:
                    continue
                if th is not None and share > 0.005:
                    warn = True
                    notes.append("%s: %d%% of it is thinner than %s (about %.2f mm thick)." % (
                        n, int(round(share * 100)) or 1, what, th))
        parts = [p for p in parts if p[2]]
        lay = o.get('layout', 'keep')
        if lay == 'bed':
            parts = self.lay_on_bed(parts, flat=self.cb_flat.isChecked() and o.get('parts') is None)
            if not o.get('per_piece', True) and len(parts) > 1:
                # one file holding them all (resin STL): laid out side by side on the plate first
                parts = [(o.get('name') or self.name(), parts[0][1], [t for _n, _c, tr in parts for t in tr])]
        elif lay == 'centre' and parts:
            allt = stand_centred([t for _n, _c, tr in parts for t in tr])
            i = 0
            out = []
            for n, c, tr in parts:
                out.append((n, c, allt[i:i + len(tr)]))
                i += len(tr)
            parts = out
        return [p for p in parts if p[2]], notes, warn

    def lay_on_bed(self, parts, flat=True):
        """Pieces (mm) laid flat if asked, side by side in the middle of the bed."""
        if flat:
            parts = [(n, c, lay_flat(tr)) for n, c, tr in parts]
        if len(parts) > 1:
            bw = self.bed[0].value() if self.cb_bed.isChecked() else 0.0
            bd = self.bed[1].value() if self.cb_bed.isChecked() else 0.0
            placed, _size = lay_out_packed([(n, tr) for n, _c, tr in parts], bw, bd,
                                           max(0.2, self.sp_gap.value()))
            parts = [(n, c, tr) for (n, tr), (_n, c, _t) in zip(placed, parts)]
        elif parts:
            parts = [(parts[0][0], parts[0][1], stand_centred(parts[0][2]))]
        return parts

    # ------------------------------------------------------------------ the window itself
    def page_shown(self, i):
        for page, bs in self.page_buttons.items():
            for b in bs:
                b.setVisible(page == i)

    def toggle_preview(self, on):
        """Shows or hides the preview; the window grows or shrinks by its width."""
        w = self.right.width() if self.right.isVisible() else max(300, int(self.st.get('pv_width', 320)))
        if not on and self.right.isVisible():
            self.st['pv_width'] = self.right.width()
        self.right.setVisible(bool(on))
        if not self.isMaximized():
            self.resize(max(420, self.width() + (w if on else -w)), self.height())
        if on:
            self._shown = None
            self.refresh_preview()
        self._save_timer.start(1200)

    def toggle_big(self, *_):
        if self.isMaximized():
            self.showNormal()
            self.b_big.setText("Bigger")
        else:
            self.showMaximized()
            self.b_big.setText("Smaller")

    def print_opts(self):
        resin = self.cb_kind.currentData() == 'resin'
        fmt = self.cb_pfmt.currentData() or ('stl' if resin else '3mf')
        # resin slicers want one plain STL in mm, standing in the middle of the plate
        return {'format': fmt, 'file_unit': 'mm', 'y_up': False, 'use_scale': True,
                'layout': 'bed', 'apply_fixes': True, 'per_piece': not (resin and fmt != '3mf')}

    def export_print(self):
        groups = self.planned_slicers() if self.ents else None
        if groups:
            # pieces going to different slicers: one file for each slicer, in a folder you pick
            from PySide6.QtWidgets import QFileDialog
            start = self.st.get('last_folder') or os.path.join(os.path.expanduser("~"), "Downloads")
            d = QFileDialog.getExistingDirectory(self, "Save the print files in", start)
            if not d:
                return
            self.st['last_folder'] = d
            self.send_split(groups, to_path=self.folder_namer(d), open_them=self.cb_open.isChecked())
            return
        self.export(self.print_opts())
        self.warn_resin_3mf()

    def warn_resin_3mf(self):
        if self.cb_kind.currentData() == 'resin' and self.cb_pfmt.currentData() == '3mf':
            self.report(self._last + "\nNote: some resin slicers read 3MF files too small - if it comes in the "
                        "wrong size, set 'Print file' to STL on the 3D print page.", True)

    def print_folder(self):
        d = self.st.get('print_folder') or os.path.join(os.path.expanduser("~"), "Downloads", "3D Scale Studio")
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            d = os.path.expanduser("~")
        return d

    def print_path(self, name, ext):
        """A new file name in the print folder (never over an old one)."""
        folder = self.print_folder()
        path = os.path.join(folder, name + ext)
        n = 2
        while os.path.exists(path):
            path = os.path.join(folder, "%s (%d)%s" % (name, n, ext))
            n += 1
        return path

    # ---- every slicer you have, and the printer each belongs to
    def slicer_targets(self):
        """[(label, slicer program, your printer it's on - None: the 3D print page as it is now)]:
        this printer's slicers first, then your other printers' slicers."""
        out, seen = [], set()
        cur, _i = self.picked_printer()

        def add(path, p, where):
            path = str(path or "").strip()
            if not path or os.path.normcase(path) in seen:
                return
            seen.add(os.path.normcase(path))
            nm = os.path.splitext(os.path.basename(path))[0] or path
            out.append(("%s  (%s)" % (nm, where), path, p))
        for path in self.slicers():
            add(path, None, (cur.get('name') if cur else "this printer"))
        for p in self.printers():
            if cur is not None and p.get('name') == cur.get('name'):
                continue
            for path in list(p.get('slicers') or []) + [p.get('slicer', '')]:
                add(path, p, p.get('name', '?'))
        return out

    def printer_of_slicer(self, path):
        """The printer whose settings (bed, resin or FDM, file type) suit this slicer: the 3D print
        page as it is (None) if the slicer's on its list, else your first printer that has it."""
        for _lab, p_, pr in self.slicer_targets():
            if os.path.normcase(p_) == os.path.normcase(path):
                return pr
        return None

    def run_as_printer(self, printer, slicer, fn):
        """Runs fn() with the 3D print page set up as that printer (bed, kind, nozzle, file type,
        gap) and that slicer showing, then puts the page back just as it was."""
        if printer is None:
            keep = self.ed_slicer.text()
            self._busy = True
            try:
                self.ed_slicer.setText(slicer)
            finally:
                self._busy = False
            try:
                return fn()
            finally:
                self._busy = True
                try:
                    self.ed_slicer.setText(keep)
                finally:
                    self._busy = False
        was = self.printer_now("")
        self._busy = True
        try:
            for s_, val in zip(self.bed, printer.get('bed', was['bed'])):
                s_.setValue(float(val))
            self.cb_kind.setCurrentIndex(max(0, self.cb_kind.findData(printer.get('kind', 'fdm'))))
            self.sp_nozzle.setValue(float(printer.get('nozzle', was['nozzle'])))
            self.cb_thin.setChecked(bool(printer.get('warn_thin', was['warn_thin'])))
            self.cb_pfmt.setCurrentIndex(max(0, self.cb_pfmt.findData(printer.get('format', '3mf'))))
            if printer.get('gap'):
                self.sp_gap.setValue(float(printer['gap']))
            self.ed_slicer.setText(slicer)
        finally:
            self._busy = False
        try:
            return fn()
        finally:
            self._busy = True
            try:
                for s_, val in zip(self.bed, was['bed']):
                    s_.setValue(float(val))
                self.cb_kind.setCurrentIndex(max(0, self.cb_kind.findData(was['kind'])))
                self.sp_nozzle.setValue(float(was['nozzle']))
                self.cb_thin.setChecked(bool(was['warn_thin']))
                self.cb_pfmt.setCurrentIndex(max(0, self.cb_pfmt.findData(was['format'])))
                self.sp_gap.setValue(float(was['gap']))
                self.set_slicers(was['slicers'], was['slicer'])
            finally:
                self._busy = False
            self.save_now()

    # ---- printers the pieces print on (each with its own slicer and bed)
    def printer_targets(self):
        """[(key, label, slicer, printer or None)]: the printer on the 3D print page first (key "" -
        its settings as they are now), then your other saved printers."""
        cur, _i = self.picked_printer()
        sl_now = self.ed_slicer.text().strip()
        nm_now = os.path.splitext(os.path.basename(sl_now))[0] if sl_now else "usual program"
        out = [("", "%s - %s" % (cur.get('name') if cur else "This printer (3D print page)", nm_now), sl_now, None)]
        for p in self.printers():
            if cur is not None and p.get('name') == cur.get('name'):
                continue
            path = str(p.get('slicer') or (list(p.get('slicers') or []) + [""])[0] or "").strip()
            nm = os.path.splitext(os.path.basename(path))[0] if path else "usual program"
            out.append((p.get('name', '?'), "%s - %s" % (p.get('name', '?'), nm), path, p))
        return out

    def norm_target(self, key):
        """"" for the printer on the 3D print page (by name too), else the saved printer's name."""
        cur, _i = self.picked_printer()
        if not key or (cur is not None and key == cur.get('name')):
            return ""
        if not any(p.get('name') == key for p in self.printers()):
            return ""                       # a printer that's been deleted: the one on the page
        return key

    def target(self, key):
        """(slicer, printer or None) for a printer key."""
        key = self.norm_target(key)
        for k, _lab, path, pr in self.printer_targets():
            if k == key:
                return path, pr
        return self.ed_slicer.text().strip(), None

    def target_name(self, key):
        key = self.norm_target(key)
        for k, lab, _path, _pr in self.printer_targets():
            if k == key:
                return lab
        return key

    def planned_slicers(self):
        """With a plan that puts pieces on different printers: [(slicer, [part numbers], printer
        or None)] in the order they come (pieces with no printer go on the 3D print page's). Else None."""
        if not (self.plan and self.plan.get('pieces') is not None and self.plan.get('printer')) or \
                not self.plan_on():
            return None
        own = self.plan.get('printer') or {}
        pcs = self.raw_piece_names()
        groups, order = {}, []
        for i, pc in enumerate(pcs):
            k = self.norm_target(own.get(pc or "", "") if pc is not None else "")
            if k not in groups:
                path, pr = self.target(k)
                groups[k] = (path, [], pr)
                order.append(k)
            groups[k][1].append(i)
        if order == [""]:
            return None
        return [groups[k] for k in order]

    def plan_words(self):
        """Where the pieces go, in words (for the Export page)."""
        if not self.ents:
            return "Select the object first."
        raw = self.raw_parts()
        groups = self.planned_slicers()
        if not groups:
            return ("%d piece%s, all on %s. To print some pieces on another printer, use 'Plan the pieces...' "
                    "and the 'Print on' buttons." % (len(raw), "" if len(raw) == 1 else "s", self.target_name("")))
        return "; ".join("%d piece%s \u2192 %s" % (len(idx), "" if len(idx) == 1 else "s",
                                                    (pr.get('name') if pr else self.target_name("").split(" - ")[0]))
                         for p_, idx, pr in groups) + "."

    def ask_folder(self, title="Save the print files in"):
        """A folder picked in a box (remembered for next time), or "" if you cancel."""
        from PySide6.QtWidgets import QFileDialog
        start = self.st.get('last_folder') or os.path.join(os.path.expanduser("~"), "Downloads")
        d = QFileDialog.getExistingDirectory(self, title, start)
        if d:
            self.st['last_folder'] = d
        return d or ""

    def folder_namer(self, d):
        def where(name, ext):
            path = os.path.join(d, name + ext)
            n = 2
            while os.path.exists(path):
                path = os.path.join(d, "%s (%d)%s" % (name, n, ext))
                n += 1
            return path
        return where

    def export_by_slicer(self):
        """Export page: the planned pieces, one file per slicer, in the file type picked there."""
        if not self.ents:
            self.report("Select the object (a group, or its faces) first.", bad=True)
            return False
        raw = self.raw_parts()
        groups = self.planned_slicers() or [(self.ed_slicer.text().strip(), list(range(len(raw))), None)]
        from PySide6.QtWidgets import QFileDialog
        start = self.st.get('last_folder') or os.path.join(os.path.expanduser("~"), "Downloads")
        d = QFileDialog.getExistingDirectory(self, "Save the files in", start)
        if not d:
            return False
        self.st['last_folder'] = d
        printing = self.cb_fmt.currentData() in ('3mf', 'stl', 'stla')
        return self.send_split(groups, to_path=self.folder_namer(d),
                               open_them=printing and self.cb_exp_send.isChecked(), use_export=True)

    def for_slicer(self, o, path, pr):
        """Settings for a file a slicer opens: always millimetres, Z up (slicers read numbers as mm -
        a file in metres or inches comes in tiny). Resin slicers (Chitubox, Lychee, Photon
        Workshop...) read 3MF too small, so they get STL."""
        o = dict(o)
        if o.get('format') not in ('3mf', 'stl', 'stla'):
            return o
        o['file_unit'] = 'mm'
        o['y_up'] = False
        nm = os.path.basename(str(path or "")).lower()
        resin = (pr.get('kind') == 'resin') if pr else (self.cb_kind.currentData() == 'resin')
        if any(w in nm for w in RESIN_SLICERS):
            resin = True
        if resin and o.get('format') == '3mf':
            o['format'] = 'stl'
            o['per_piece'] = False             # one STL holding the pieces, laid out on the plate
        return o

    def send_split(self, groups, to_path=None, open_them=True, use_export=False):
        """Each slicer gets its own pieces, laid out on its own printer's bed, in one go: one
        window per slicer, not one per piece."""
        lines, bad, sent = [], False, 0
        base = "".join(ch for ch in self.name() if ch not in '\\/:*?"<>|').strip() or "model"
        base += " " + self.describe().replace(":", "-").replace("%", "pc").replace(" ", "")
        for path, idx, pr in groups:
            nm = (os.path.splitext(os.path.basename(path))[0] if path else "") or "usual program"

            def one(path=path, idx=idx, nm=nm):
                o_ = dict(self.export_opts() if use_export else self.print_opts(), only=set(idx),
                          name="%s - %s" % (base, nm))
                ok = self.export(self.for_slicer(o_, path, pr),
                                 to_path=to_path or self.print_path, open_it=False)
                return ok, self._last, list(getattr(self, '_last_files', []) or [])
            ok, text, files = self.run_as_printer(pr, path, one)
            if not ok:
                bad = True
                lines.append("%s: %s" % (nm, text))
                continue
            sent += 1
            note = open_in_slicer(files, path) if open_them else ("Saved: " + ", ".join(
                os.path.basename(x) for x in files))
            lines.append("%s: %d piece%s%s. %s" % (nm, len(idx), "" if len(idx) == 1 else "s",
                                                  (" (on %s's bed)" % pr.get('name')) if pr else "", note))
        head = ("Sent to %d slicer%s - each slicer gets its own pieces on one bed:" if open_them else
                "Saved a file for each of %d slicer%s - each with its own pieces on one bed:") % (
            sent, "" if sent == 1 else "s")
        self.report(head + "\n" + "\n".join(lines) + "\nYour model in the work area is just as it was.", bad)
        if sent and self.cb_preview.currentData() != 'bed':
            self.cb_preview.setCurrentIndex(self.cb_preview.findData('bed'))
        return sent > 0

    def send_to_slicer(self, save_as=False):
        """Saves the object at its new size as a print file (no save box) and opens it in this
        printer's slicer. The model in the work area is left exactly as it is. With a plan that
        sends pieces to different slicers, each slicer gets its own pieces."""
        live = self.selection()
        if not live:
            self.report("Select the object (a group, or its faces) first.", bad=True)
            return False
        # always read it afresh: it may have been grouped or changed since it was last read
        self._waiting = False
        self.watch_selection(force=True)
        groups = self.planned_slicers()
        if groups:
            to = None
            if save_as:
                d = self.ask_folder()
                if not d:
                    return False
                to = self.folder_namer(d)
            return self.send_split(groups, to_path=to)
        where = None if save_as else self.print_path       # None: a save box
        ok = self.export(self.for_slicer(self.print_opts(), self.ed_slicer.text().strip(), None),
                         to_path=where, open_it=True)
        if ok:
            self.warn_resin_3mf()
        if ok and self.cb_preview.currentData() != 'bed':
            self.cb_preview.setCurrentIndex(self.cb_preview.findData('bed'))   # show what went to the slicer
        return ok

    def browse_print_folder(self, *_):
        from PySide6.QtWidgets import QFileDialog
        d = QFileDialog.getExistingDirectory(self, "Save print files in", self.print_folder())
        if d:
            self.st['print_folder'] = d
            self.lbl_pfolder.setText(d)
            self.save_now()

    # ------------------------------------------------------------------ scaling in the work area
    def scale_model(self, how):
        # always what's selected NOW in the work area (never one already done by Scale + next)
        live = self.selection()
        if not live:
            self.report("Select the object (a group, or its faces) first.", bad=True)
            return False
        # always read it afresh: it may have been grouped or changed since it was last read
        self._waiting = False
        self.watch_selection(force=True)
        f = self.factors()
        if any(x <= 0 for x in f):
            self.report("The new size can't be nothing - type a size above 0.", bad=True)
            return False
        res = self.tool.scale_selection(self.viewport, self.ents, f, self.cb_pivot.currentData(), how,
                                        self.describe(), beside=self.cb_beside.isChecked())
        text, bad = res
        self.report(text, bad)
        self._sel_key = None
        self.watch_selection(force=True)
        return not bad

    def scale_and_next(self, how=None, force=False):
        """Scales what's selected, then clears the selection ready for the next object. The
        preview keeps showing the one just scaled until you select the next. how: 'bed' etc. (else
        what 'Scale + next' is set to); force: even if it's the one just done."""
        live = self.selection()
        if not live:
            self.report("Select the object in the work area first, then press Scale + next.", bad=True)
            return
        if not force and self._waiting and tuple(id(e) for e in live) == self._done_key:
            self.report("That one's done - select the next object in the work area, then press Scale + next.",
                        bad=True)
            return
        how = how or self.cb_next.currentData()
        if how == 'bed':
            ok = self.add_to_bed()
        else:
            ok = self.send_to_slicer() if how == 'slicer' else self.scale_model(how)
        if not ok:
            return
        name = self.name()
        self._done += 1
        self._done_key = self._sel_key
        self.tool.clear_selection(self.viewport)
        try:
            self._sel_key = tuple(id(e) for e in self.selection())
        except Exception:
            self._sel_key = ()
        self._waiting = True
        self._sel_text = "Done: %s, now %s. Select the next object." % (name, fmt_size(self.size_mm(), self.show_unit()))
        self.update_info()
        if how == 'bed':
            n_ = len(self._bed)
            self.lbl_count.setText("On the bed: %d object%s. Select the next one and press Scale + next - or "
                                   "'Send the bed to slicer' when they're all on." % (n_, "" if n_ == 1 else "s"))
            self.report("Put '%s' on the bed at %s (%d on it) - its pieces: %s. Select the next object, then press "
                        "Scale + next again - or 'Send the bed to slicer'." % (
                            name, self.describe(), n_, getattr(self, '_bed_split', "")))
            return
        self.lbl_count.setText("Done: %d object%s this time. Select the next one and press Scale + next." % (
            self._done, "" if self._done == 1 else "s"))
        self.report("Scaled '%s' to %s (%d done). Select the next object, then press Scale + next again." % (
            name, self.describe(), self._done))

    # ---- one bed for many objects (Scale + next)
    def bed_buttons(self):
        n = len(self._bed)
        self.b_sendbed.setText("Send the bed to slicer (%d)" % n if n else "Send the bed to slicer")
        self.b_sendbed.setEnabled(n > 0)
        self.b_emptybed.setEnabled(n > 0)
        try:
            self.update_info()
        except Exception:
            pass
        try:
            self.b_takeoff.setEnabled(n > 0)
            t = StudioDialog._taken
            self.b_putback.setEnabled(bool(t))
            if t:
                last = t[-1][1]
                self.b_putback.setText("Put back %s \u21b6" % (
                    ("'%s'" % last[0]) if t[-1][0] is not None else "all %d" % len(last)))
            else:
                self.b_putback.setText("Put back \u21b6")
            self.b_seebed.setEnabled(n > 0)
            if getattr(self, '_gathered_on', False):
                self._pv_timer.start(200)
        except Exception:
            pass
        try:
            self.pn_refresh_list()
            if getattr(self, '_pn_index', -1) == self.tabs.currentIndex():
                self._pn_cache = None
                self._pv_timer.start(30)
        except Exception:
            pass

    def add_to_bed(self, top=None, name=None):
        """Scales what's selected (mended, as it will print) and keeps it for the one bed. The
        model in the work area isn't changed. With a plan that sends pieces to different slicers,
        each piece remembers its slicer: the bed is sent as one bed per slicer."""
        live = self.selection()
        if not live:
            self.report("Select the object (a group, or its faces) first.", bad=True)
            return False
        # always read it afresh: it may have been grouped or changed since it was last read
        self._waiting = False
        if top is None:
            self.watch_selection(force=True)
        else:
            self._only_top = top           # just one of the objects selected (from the plan window)
            self._raw = None
        try:
            o = dict(self.print_opts(), layout='keep', per_piece=True)
            groups = self.planned_slicers()
            parts, dests = [], []
            if groups:
                for path, idx, pr in groups:
                    p_, _n, _w = self.make_parts(dict(o, only=set(idx)))
                    parts += p_
                    dests += [pr.get('name') if pr else self.norm_target("")] * len(p_)
            else:
                parts, _n, _w = self.make_parts(o)
                dests = [""] * len(parts)          # "": the printer on the 3D print page when it's sent
        except Exception as e:
            self.report("Couldn't put it on the bed: %s" % e, bad=True)
            return False
        finally:
            if top is not None:
                self._only_top = None
                self._raw = None
        if not parts:
            self.report("There's nothing to put on the bed - select the object (a group, or its faces).", bad=True)
            return False
        if self.cb_flat.isChecked():
            parts = [(n, c, lay_flat(tr)) for n, c, tr in parts]
        self._bed.append((name or self.name(), self.describe(), parts, dests))
        self._bed_view = 0
        self._bed_split = self.split_words(dests)
        self.bed_buttons()
        return True

    def split_words(self, dests):
        """'12 pieces on Ender 3 V3 SE, 3 on Mars 2 Pro' - which printer's bed the pieces went on."""
        cnt, order = {}, []
        for d in dests:
            k = self.norm_target(d)
            if k not in cnt:
                order.append(k)
            cnt[k] = cnt.get(k, 0) + 1
        return ", ".join("%d on %s" % (cnt[k], self.target_name(k).split(" - ")[0]) for k in order)

    def take_off_menu(self, button=None):
        """A menu of the objects on the bed: pick one to take it off."""
        from PySide6.QtWidgets import QMenu
        if not self._bed:
            return
        m = QMenu(self)
        last = m.addAction("The last one added (%s)" % self._bed[-1][0])
        last.triggered.connect(lambda _=False: self.take_off(len(self._bed) - 1))
        m.addSeparator()
        for i, (name, sc, parts, _d) in enumerate(self._bed):
            sz = tris_size([t for _n, _c, tr in parts for t in tr])
            act = m.addAction("%d. %s - %s, %s mm" % (i + 1, name, sc, " x ".join(_fmt_mm(v) for v in sz)))
            act.triggered.connect(lambda _=False, i=i: self.take_off(i))
        try:
            m.exec(button.mapToGlobal(button.rect().bottomLeft()))
        except Exception:
            m.exec()

    def take_off(self, i):
        if not (0 <= i < len(self._bed)):
            return
        item = self._bed.pop(i)
        name = item[0]
        StudioDialog._taken.append((i, item))
        del StudioDialog._taken[:-20]
        self._done = max(0, self._done - 1)
        self._waiting = False              # so the same object can be put back on
        self._bed_view = 0
        self.bed_buttons()
        n = len(self._bed)
        self.lbl_count.setText("On the bed: %d object%s." % (n, "" if n == 1 else "s") if n else "")
        self.report("Took '%s' off the bed (%d left on it). Wrong one? Press 'Put back'." % (name, n))

    def put_back(self, *_):
        """Undoes the last 'Take one off' (or 'Empty the bed')."""
        t = StudioDialog._taken
        if not t:
            self.report("Nothing to put back.")
            return
        place, item = t.pop()
        if place is None:                      # a whole bed emptied: all of it back
            self._bed.extend(item)
            what = "all %d object%s" % (len(item), "" if len(item) == 1 else "s")
        else:
            self._bed.insert(min(place, len(self._bed)), item)
            what = "'%s'" % item[0]
        self._bed_view = 0
        self.bed_buttons()
        n = len(self._bed)
        self.lbl_count.setText("On the bed: %d object%s." % (n, "" if n == 1 else "s"))
        self.report("Put %s back on the bed (%d on it now)." % (what, n))

    def start_again(self, *_):
        """Empties the gathered bed and forgets the plan: back to a clean start."""
        n = len(self._bed)
        if n:
            StudioDialog._taken.append((None, list(self._bed)))
        del self._bed[:]
        self._bed_view = self._plan_view = 0
        self._done = 0
        self._waiting = False
        self._bed_note = []
        self.bed_buttons()
        try:
            self.lbl_count.setText("")
        except Exception:
            pass
        self.plan = None
        StudioDialog._plan = None
        self._raw = None
        if self.cb_preview.currentData() != 'model':
            self.cb_preview.setCurrentIndex(self.cb_preview.findData('model'))
        self.changed()
        self.refresh_preview()
        back = ""
        if self.st.get('before_fit'):
            self.set_scale_state(self.st['before_fit'])
            self.st['before_fit'] = None
            self.fit_buttons()
            back = " The scale is back to %s (from before 'Use the biggest that fits')." % self.describe()
        self.report("Started again: the gathered bed is empty%s and the piece plan is forgotten.%s 'Put back' "
                    "brings the bed back." % ((" (%d object%s taken off)" % (n, "" if n == 1 else "s")) if n else "",
                                              back))

    def empty_bed(self, *_):
        n = len(self._bed)
        if n:
            StudioDialog._taken.append((None, list(self._bed)))
        del self._bed[:]
        self._bed_view = 0
        self.bed_buttons()
        self._done = 0
        self.lbl_count.setText("")
        if n:
            self.report("Emptied the bed (%d object%s taken off). Didn't mean to? Press 'Put back'." % (
                n, "" if n == 1 else "s"))

    # ---- the gathered bed, one bed for each slicer
    def bed_slicers(self, default=None):
        """The printers the gathered pieces go on, in order: keys ("" = the one on the 3D print page)."""
        out = []
        for _n, _sc, _p, dests in self._bed:
            for d in dests:
                k = self.norm_target(d)
                if k not in out:
                    out.append(k)
        return out

    def printer_settings(self, pr):
        """(bed x, y, z, gap, pieces kept separate) for one of your printers - None: the 3D print page."""
        if pr is None:
            o = self.print_opts()
            return (self.bed[0].value(), self.bed[1].value(), self.bed[2].value(), self.sp_gap.value(),
                    o.get('per_piece', True))
        b = list(pr.get('bed') or [s.value() for s in self.bed]) + [250.0, 250.0, 250.0]
        resin = pr.get('kind') == 'resin'
        fmt = pr.get('format') or ('stl' if resin else '3mf')
        return (float(b[0]), float(b[1]), float(b[2]), float(pr.get('gap') or self.sp_gap.value()),
                not (resin and fmt != '3mf'))

    def bed_items(self, o=None, colour_each=False, dest=None, default=None, per_piece=None):
        """dest: a printer key - only the pieces going on that printer."""
        """The gathered objects as pieces for the file: [(name, colour, tris)] (mm, not laid out).
        colour_each: each object in its own colour (for the preview). dest: only the pieces going
        to that slicer."""
        o = o or self.print_opts()
        keep = o.get('per_piece', True) if per_piece is None else per_piece
        default = self.ed_slicer.text().strip() if default is None else default
        items = []
        for k, (name, _sc, parts, dests) in enumerate(self._bed):
            if dest is not None:
                want = self.norm_target(dest)
                parts = [p for p, d in zip(parts, dests) if self.norm_target(d) == want]
            if not parts:
                continue
            if colour_each:
                parts = [(n, piece_colour(k), tr) for n, _c, tr in parts]
            if not keep and len(parts) > 1:
                # resin: each object stays in one piece, laid out with the others, all in one STL
                allt = [t for _n, _c, tr in parts for t in tr]
                parts = [(name, parts[0][1], allt)]
            for n, c, tr in parts:
                items.append((n if len(parts) == 1 else "%s - %s" % (name, n), c, tr))
        names = {}
        for n, _c, _t in items:
            names[n] = names.get(n, 0) + 1
        seen, uniq = {}, []
        for n, c, tr in items:
            seen[n] = seen.get(n, 0) + 1
            uniq.append((n if names[n] == 1 else "%s (%d)" % (n, seen[n]), c, tr))
        return uniq

    def bed_for_slicer(self, key, colour_each=False):
        """(pieces laid out on that printer's bed, (bed x, y, z), printer or None)."""
        _path, pr = self.target(key)
        bx, by, bz, gap, keep = self.printer_settings(pr)
        items = self.bed_items(colour_each=colour_each, dest=key, per_piece=keep)
        parts = items
        if len(items) > 1:
            placed, _s = lay_out_packed([(n, tr) for n, _c, tr in items],
                                        bx if self.cb_bed.isChecked() else 0.0,
                                        by if self.cb_bed.isChecked() else 0.0, max(0.2, gap))
            parts = [(n, c, tr) for (n, tr), (_n, c, _t) in zip(placed, items)]
        elif items:
            parts = [(items[0][0], items[0][1], stand_centred(items[0][2]))]
        return parts, (bx, by, bz), pr

    def bed_fit_words(self, key):
        parts, bed, pr = self.bed_for_slicer(key)
        path, _pr = self.target(key)
        if not parts:
            return "", True
        s = tris_size([t for _n, _c, tr in parts for t in tr])
        fits = (not self.cb_bed.isChecked()) or (s[0] <= bed[0] + 1e-6 and s[1] <= bed[1] + 1e-6 and
                                                 s[2] <= bed[2] + 1e-6)
        nm = os.path.splitext(os.path.basename(path))[0] if path else "your usual program"
        where = ("%s's bed" % pr.get('name')) if pr else "the bed on the 3D print page"
        t = "%s: %d piece%s, %s mm altogether, on %s (%s x %s mm)" % (
            nm, len(parts), "" if len(parts) == 1 else "s", " x ".join(_fmt_mm(v) for v in s), where,
            _fmt_mm(bed[0]), _fmt_mm(bed[1]))
        t += " - fits." if fits else " - TOO BIG: take something off, or send fewer at a time."
        return t, fits

    def gathered_fit_html(self):
        """For the 3D print page: the gathered bed (everything Scale + next has put on it), laid out
        the way it will be sent - not just the object selected."""
        if not self._bed or not self.cb_bed.isChecked():
            return ""
        key = (tuple(id(x) for x in self._bed), tuple(s_.value() for s_ in self.bed), self.sp_gap.value(),
               self.ed_slicer.text(), self.cb_kind.currentData(), self.cb_pfmt.currentData())
        c = getattr(self, '_fit_cache', None)
        if c and c[0] == key:
            return c[1]
        out = []
        try:
            for path in self.bed_slicers():
                t, fits = self.bed_fit_words(path)
                if t:
                    out.append("<span style='color:%s'>%s</span>" % ("#2e7d32" if fits else "#c0392b", t))
        except Exception as e:
            out.append("Couldn't lay out the gathered bed: %s" % e)
        html = ("<br><br><b>The gathered bed (Scale + next) - all of it, laid out:</b><br>" + "<br>".join(out)) \
            if out else ""
        self._fit_cache = (key, html)
        return html

    def next_bed(self, *_):
        """The preview's 'Next bed' button: the next printer's bed."""
        if getattr(self, '_gathered_on', False):
            self._bed_view = getattr(self, '_bed_view', 0) + 1
        else:
            self._plan_view = getattr(self, '_plan_view', 0) + 1
        self.refresh_preview()

    def lay_for_printer(self, parts, pr):
        """Pieces (mm, already flat if wanted) laid out on one printer's bed. Returns (parts, bed)."""
        bx, by, bz, gap, _keep = self.printer_settings(pr)
        if len(parts) > 1:
            placed, _s = lay_out_packed([(n, tr) for n, _c, tr in parts],
                                        bx if self.cb_bed.isChecked() else 0.0,
                                        by if self.cb_bed.isChecked() else 0.0, max(0.2, gap))
            parts = [(n, c, tr) for (n, tr), (_n, c, _t) in zip(placed, parts)]
        elif parts:
            parts = [(parts[0][0], parts[0][1], stand_centred(parts[0][2]))]
        return parts, (bx, by, bz)

    def fit_words(self, parts, bed, path, pr):
        s = tris_size([t for _n, _c, tr in parts for t in tr]) if parts else (0.0, 0.0, 0.0)
        fits = (not self.cb_bed.isChecked()) or (s[0] <= bed[0] + 1e-6 and s[1] <= bed[1] + 1e-6 and
                                                 s[2] <= bed[2] + 1e-6)
        nm = os.path.splitext(os.path.basename(path))[0] if path else "your usual program"
        where = ("%s's bed" % pr.get('name')) if pr else "the bed on the 3D print page"
        t = "%s: %d piece%s, %s mm altogether, on %s (%s x %s mm)" % (
            nm, len(parts), "" if len(parts) == 1 else "s", " x ".join(_fmt_mm(v) for v in s), where,
            _fmt_mm(bed[0]), _fmt_mm(bed[1]))
        t += " - fits." if fits else " - TOO BIG for that bed."
        return t, fits

    def bed_note(self, parts, bed, path, pr, i, n):
        """Two short lines over the preview: which printer's bed, and does it all fit."""
        s = tris_size([t for _n, _c, tr in parts for t in tr]) if parts else (0.0, 0.0, 0.0)
        fits = (not self.cb_bed.isChecked()) or (s[0] <= bed[0] + 1e-6 and s[1] <= bed[1] + 1e-6 and
                                                 s[2] <= bed[2] + 1e-6)
        nm = os.path.splitext(os.path.basename(path))[0] if path else "usual program"
        who = pr.get('name') if pr else self.target_name("").split(" - ")[0]
        return ["Bed %d of %d: %s  (%s, %s x %s mm)" % (i + 1, n, nm, who, _fmt_mm(bed[0]), _fmt_mm(bed[1])),
                "%d piece%s, %s mm - %s" % (len(parts), "" if len(parts) == 1 else "s",
                                            " x ".join(_fmt_mm(v) for v in s),
                                            "fits" if fits else "TOO BIG for this bed")]

    def preview_planned_bed(self, groups):
        """'On the print bed' when your plan sends pieces to more than one slicer: each printer's own
        bed, one at a time ('Next bed' shows the next)."""
        i = getattr(self, '_plan_view', 0) % len(groups)
        path, idx, pr = groups[i]
        _bx, _by, _bz, _gap, keep = self.printer_settings(pr)
        parts, _n, _w = self.make_parts({'use_scale': True, 'layout': 'keep', 'apply_fixes': False,
                                         'per_piece': True, 'only': set(idx)})
        if self.cb_flat.isChecked():
            parts = [(n, c, lay_flat(tr)) for n, c, tr in parts]
        parts, bed = self.lay_for_printer(parts, pr)
        shown_bed = (bed[0], bed[1])
        if not self.cb_bed.isChecked() and parts:
            s = tris_size([t for _n, _c, tr in parts for t in tr])
            shown_bed = (s[0] * 1.15 + 10, s[1] * 1.15 + 10)
        self.canvas.empty_text = "Nothing to show"
        self.canvas.set_parts(parts, shown_bed, None)
        self._shown = None
        self.b_nextbed.setVisible(len(groups) > 1)
        self._bed_note = self.bed_note(parts, bed, path, pr, i, len(groups))

    def preview_gathered(self):
        """Shows the gathered objects laid out on the bed, as they'll be sent. With pieces going to
        more than one slicer, each press of 'Preview the bed' shows the next slicer's bed."""
        if not self._bed:
            self.b_nextbed.setVisible(False)
            self._bed_note = []
            self.canvas.empty_text = ("The bed's empty - set Scale + next to 'Adds it to one bed', then select "
                                      "each object and press Scale + next.")
            self.canvas.set_parts([], None)
            self._shown = None
            return
        sl = self.bed_slicers()
        self.b_nextbed.setVisible(len(sl) > 1)
        i = getattr(self, '_bed_view', 0) % max(1, len(sl))
        key = sl[i] if sl else ""
        path, _p0 = self.target(key)
        parts, bed, _pr = self.bed_for_slicer(key, colour_each=True)
        if not self.cb_bed.isChecked() and parts:
            s = tris_size([t for _n, _c, tr in parts for t in tr])
            bed = (s[0] * 1.15 + 10, s[1] * 1.15 + 10, s[2])
        self.canvas.empty_text = "Nothing to show"
        self.canvas.set_parts(parts, (bed[0], bed[1]), None)
        self._shown = None
        pr = _pr
        bx, by, bz, _g, _k = self.printer_settings(pr)
        self._bed_note = ["The gathered bed (%d object%s) - pick under the preview to go back" % (
            len(self._bed), "" if len(self._bed) == 1 else "s")] + \
            self.bed_note(parts, (bx, by, bz), path, pr, i, max(1, len(sl)))

    def preview_picked(self, *_):
        """Picking under the preview (even the one already showing) leaves the gathered bed."""
        if getattr(self, '_gathered_on', False):
            self._gathered_on = False
            self._bed_note = []
            self.refresh_preview()

    def show_gathered(self, *_):
        """'Preview the bed': the gathered bed in the preview (pick anything under the preview to go back)."""
        if not getattr(self, '_gathered_on', False):
            self._gathered_on = True
            self._bed_view = 0
        else:
            self._bed_view = getattr(self, '_bed_view', 0) + 1   # the next printer's bed
        self.refresh_preview()
        if not self.cb_pv.isChecked():
            self.cb_pv.setChecked(True)

    def send_bed(self, button=None, only=None, save_as=False):
        """Every object gathered on the bed, laid out side by side and opened at once: one bed (and
        one window) for each slicer the pieces go to. only: just these printers' beds (keys) - the
        rest stay on the bed."""
        if not self._bed:
            self.report("The bed's empty: set 'Scale + next' to 'Adds it to one bed', then select each object "
                        "and press Scale + next.", bad=True)
            return False
        only = None if only is None else [self.norm_target(k) for k in only]
        sl = [k for k in self.bed_slicers() if only is None or k in only]
        if not sl:
            self.report("Nothing on that printer's bed to send.", bad=True)
            return False
        if "" in sl and not self.pick_slicer(button):
            return False
        to = self.print_path
        if save_as:
            d = self.ask_folder()
            if not d:
                return False
            to = self.folder_namer(d)
        default = self.ed_slicer.text().strip()
        going = [it for it in self._bed if any(self.norm_target(d) in sl for d in it[3])]
        scales = sorted(set(sc for _n, sc, _p, _d in going))
        words = scales[0] if len(scales) == 1 else "mixed scales"
        n_obj = len(going)
        done_keys = []
        lines, sent, bad = [], 0, False
        for key in sl:
            path, pr = self.target(key)
            nm = (pr.get('name') if pr else "") or (os.path.splitext(os.path.basename(path))[0] if path else "") \
                or "usual program"

            def one(key=key, nm=nm):
                o = self.for_slicer(self.print_opts(), path, pr)
                uniq = self.bed_items(o, dest=key, default=default)
                o.update({'parts': uniq, 'apply_fixes': False, 'scale_words': words,
                          'name': "Bed of %d - %s%s" % (n_obj, words.replace(":", "-").replace("%", "pc").replace(
                              " ", ""), (" - " + nm) if len(sl) > 1 else "")})
                ok = self.export(o, to_path=to, open_it=False)
                return ok, self._last, list(getattr(self, '_last_files', []) or []), len(uniq)
            ok, text, files, n_p = self.run_as_printer(pr, path, one)
            if not ok:
                bad = True
                lines.append("%s: %s" % (nm, text))
                continue
            sent += 1
            done_keys.append(key)
            note = open_in_slicer(files, path)
            lines.append("%s: %d piece%s%s. %s" % (nm, n_p, "" if n_p == 1 else "s",
                                                  (" on %s's bed" % pr.get('name')) if pr else "", note))
        if sent:
            if only is None and len(done_keys) == len(sl):
                del self._bed[:]
            else:
                # just the pieces that went: the rest (other printers' beds) stay on
                left = []
                for name, sc, parts, dests in self._bed:
                    kept = [(p, d) for p, d in zip(parts, dests) if self.norm_target(d) not in done_keys]
                    if kept:
                        left.append((name, sc, [p for p, _d in kept], [d for _p, d in kept]))
                self._bed[:] = left
            self._bed_view = 0
            self._done = 0
            self.bed_buttons()
            self.lbl_count.setText("Sent %d object%s to %d slicer%s.%s" % (
                n_obj, "" if n_obj == 1 else "s", sent, "" if sent == 1 else "s",
                " The bed's empty again." if not self._bed else " %d still on the bed." % len(self._bed)))
        self.report("Sent the gathered bed (%d object%s) - one bed for each slicer:\n" % (
            n_obj, "" if n_obj == 1 else "s") + "\n".join(lines), bad)
        return sent > 0

    # ------------------------------------------------------------------ Scale & Print page
    # One page for the everyday job: click an object in the work area, it shows on the print bed
    # (in yellow, where it will go), press Add to bed, click the next one ... then send the bed.
    # It uses the same gathered bed as Scale + next, so the two work together.
    PN_NEW_COLOUR = (250, 205, 20)        # the object selected now, not on the bed yet

    def build_print_next_page(self):
        from PySide6.QtWidgets import QListWidget
        v = self._page("Scale && Print", "Click an object, see it on the print bed, add it - then the next one. "
                                       "Send the bed to your printer when it's full.")
        self._pn_index = self.tabs.count() - 1
        self._pn_key = None
        self._pn_cache = None
        self._pn_targets = None
        how = QLabel("<b>1.</b> Click an object in the work area - it shows on the bed in "
                     "<span style='background:#fad014'>&nbsp;yellow&nbsp;</span>.<br>"
                     "<b>2.</b> Press <b>Add to bed</b>. <b>3.</b> Click the next object, and again.<br>"
                     "<b>4.</b> Press <b>Send</b> when the bed's full. Your model isn't changed.")
        how.setWordWrap(True)
        v.addWidget(how)

        # the scale - the same as the Scale page
        form = self._form()
        self.pn_cb_scale, self.pn_sp_scale, r = self._scale_list(
            self.sp_scale.value(), "The scale it prints at - the same as on the Scale page.")
        form.addRow("Scale:", r)
        v.addLayout(form)
        self.pn_lbl_scale = QLabel()
        self.pn_lbl_scale.setWordWrap(True)
        v.addWidget(self.pn_lbl_scale)
        self.pn_sp_scale.valueChanged.connect(self.pn_scale_typed)
        self.sp_scale.valueChanged.connect(lambda *_: self.pn_sync_scale())
        self.cb_mode.currentIndexChanged.connect(lambda *_: self.pn_sync_scale())

        # the printer the next objects go on: one coloured button for each
        v.addWidget(QLabel("<b>Print on:</b>"))
        self.pn_prow = flow_layout()
        v.addLayout(self.pn_prow)
        self.pn_pbuttons = []

        # the big coloured buttons
        def big(text, col, tip, fn):
            b_ = QPushButton(text)
            b_.setStyleSheet(colour_button_style(col))
            b_.setToolTip(tip)
            b_.clicked.connect(lambda *_a: fn())
            return b_
        crow = QHBoxLayout()
        crow.addWidget(QLabel("How many:"))
        self.pn_sp_copies = QSpinBox()
        self.pn_sp_copies.setRange(1, 200)
        self.pn_sp_copies.setValue(1)
        self.pn_sp_copies.setToolTip("How many of the selected object 'Add to bed' puts on the bed - 4 for four "
                                     "of the same chimney, say. Each is laid out on its own.")
        crow.addWidget(self.pn_sp_copies)
        crow.addStretch(1)
        v.addLayout(crow)
        self.pn_sp_copies.valueChanged.connect(lambda *_: self._pv_timer.start(250))
        row1 = flow_layout()
        self.pn_b_add = big("➕ Add to bed", (46, 139, 87),
                            "Puts the object selected in the work area on the bed at this scale (your model "
                            "isn't changed), then gets ready for the next one: click it and press this again.",
                            self.pn_add)
        self.pn_b_dup = big("⧉ Duplicate", (60, 140, 220),
                            "Puts one more of the object picked in the list below on the bed (or of the "
                            "last one added, if none is picked).", self.pn_duplicate)
        self.pn_b_off = big("Take off", (211, 120, 20),
                            "Takes the object picked in the list below off the bed (or the last one added, "
                            "if none is picked).", self.pn_take_off)
        self.pn_b_back = big("Put back ↶", (120, 130, 140),
                             "Puts back the last object taken off (or the whole bed after 'Empty').",
                             self.put_back)
        self.pn_b_empty = big("Empty", (150, 150, 150), "Takes everything off the bed (nothing is sent). "
                              "'Put back' brings it back.", self.empty_bed)
        for b_ in (self.pn_b_add, self.pn_b_dup, self.pn_b_off, self.pn_b_back, self.pn_b_empty):
            row1.addWidget(b_)
        v.addLayout(row1)
        row2 = flow_layout()
        self.pn_b_send = big("Send to printer", (41, 128, 185),
                             "Lays out this printer's bed and opens it in its slicer - one window, one bed. "
                             "Then those objects come off the bed, ready for the next lot.",
                             lambda: self.pn_send(False))
        self.pn_b_sendall = big("Send every printer's bed", (142, 68, 173),
                                "Sends each printer's bed to its own slicer, all at once.",
                                lambda: self.pn_send(True))
        self.pn_b_save = big("Save and send...", (40, 160, 150),
                             "The same as Send, but you pick where the print file is saved first (a "
                             "folder box), then it opens in the slicer.", lambda: self.pn_send(False, True))
        row2.addWidget(self.pn_b_send)
        row2.addWidget(self.pn_b_save)
        row2.addWidget(self.pn_b_sendall)
        v.addLayout(row2)

        # what's on the bed
        self.pn_lbl_fit = QLabel()
        self.pn_lbl_fit.setWordWrap(True)
        v.addWidget(self.pn_lbl_fit)
        self.pn_list = QListWidget()
        self.pn_list.setToolTip("Everything on the bed, in the colour it has in the preview. Pick one and "
                                "press 'Take off' to take it off.")
        self.pn_list.setMinimumHeight(120)
        v.addWidget(self.pn_list, 1)

    def pn_ready(self):
        """Once every page is built: the printer buttons, the scale and the list."""
        self._pn_ok = True
        self.pn_fill_printers()
        self.pn_sync_scale()
        self.pn_refresh_list()

    # ---- the scale, kept the same as the Scale page
    def pn_scale_typed(self, val):
        if self._busy:
            return
        i = self.cb_mode.findData('scale')
        if self.cb_mode.currentIndex() != i:
            self.cb_mode.setCurrentIndex(i)
        if abs(self.sp_scale.value() - val) > 1e-9:
            self.sp_scale.setValue(val)
        self.pn_sync_scale()

    def pn_sync_scale(self):
        if not hasattr(self, 'pn_sp_scale'):
            return
        val = self.sp_scale.value()
        if abs(self.pn_sp_scale.value() - val) > 1e-9:
            self.pn_sp_scale.blockSignals(True)
            self.pn_sp_scale.setValue(val)
            self.pn_sp_scale.blockSignals(False)
            j = next((i for i, (_t, x) in enumerate(SCALES) if x is not None and abs(x - val) < 1e-9),
                     len(SCALES) - 1)
            self.pn_cb_scale.blockSignals(True)
            self.pn_cb_scale.setCurrentIndex(j)
            self.pn_cb_scale.blockSignals(False)
        if self.cb_mode.currentData() == 'scale':
            self.pn_lbl_scale.setText("")
            self.pn_lbl_scale.setVisible(False)
        else:
            self.pn_lbl_scale.setText("<span style='color:#b35900'>The Scale page is set to %s - that's what "
                                      "'Add to bed' uses. Pick a scale here to use a model scale instead.</span>"
                                      % self.describe())
            self.pn_lbl_scale.setVisible(True)

    # ---- the printers
    def pn_fill_printers(self):
        """One coloured button for each printer (the one on the 3D print page first)."""
        from PySide6.QtWidgets import QButtonGroup
        targets = [(k, lab) for k, lab, _p, _pr in self.printer_targets()]
        if targets == self._pn_targets and self.pn_pbuttons:
            return
        self._pn_targets = targets
        for b_ in self.pn_pbuttons:
            self.pn_prow.removeWidget(b_)
            b_.deleteLater()
        self.pn_pbuttons = []
        self.pn_group = QButtonGroup(self)
        self.pn_group.setExclusive(True)
        want = self.norm_target(self.st.get('pn_printer', ""))
        for i, (key, lab) in enumerate(targets):
            col = PRINTER_COLOURS[i % len(PRINTER_COLOURS)]
            b_ = QPushButton(lab)
            b_.setCheckable(True)
            b_.setAutoDefault(False)
            b_.setStyleSheet("QPushButton{padding:6px 10px;border-radius:4px;border:2px solid rgb(%d,%d,%d);"
                             "color:rgb(%d,%d,%d);font-weight:bold;background:white}"
                             "QPushButton:checked{background:rgb(%d,%d,%d);color:white}" % (col + col + col))
            b_.setToolTip("Objects you add go on %s's bed, and the preview shows that bed." % lab.split(" - ")[0])
            b_.setProperty('pn_key', key)
            b_.setChecked(key == want)
            b_.clicked.connect(lambda *_a: self.pn_printer_picked())
            self.pn_group.addButton(b_)
            self.pn_prow.addWidget(b_)
            self.pn_pbuttons.append(b_)
        if self.pn_pbuttons and not any(b_.isChecked() for b_ in self.pn_pbuttons):
            self.pn_pbuttons[0].setChecked(True)

    def pn_printer(self):
        """The printer key picked on this page ("" = the one on the 3D print page)."""
        for b_ in getattr(self, 'pn_pbuttons', []):
            if b_.isChecked():
                return self.norm_target(b_.property('pn_key') or "")
        return ""

    def pn_printer_picked(self):
        self.st['pn_printer'] = self.pn_printer()
        self._save_timer.start(1200)
        self.pn_refresh_list()
        self.refresh_preview()

    # ---- adding, taking off, sending
    def pn_add(self):
        live = self.selection()
        if not live:
            self.report("Click an object in the work area first (a group, or its faces), then press Add to bed.",
                        bad=True)
            return
        key = tuple(id(e) for e in live)
        if self._waiting and key == self._done_key:
            self.report("That one's on the bed already - click the next object, then press Add to bed.", bad=True)
            return
        n_before = len(self._bed)
        if not self.add_to_bed():
            return
        dest = self.pn_printer()
        if len(self._bed) > n_before:
            name, sc, parts, dests = self._bed[-1]
            if all(not self.norm_target(d) for d in dests):     # no plan saying where pieces go
                self._bed[-1] = (name, sc, parts, [dest] * len(parts))
                self._bed_split = self.split_words(self._bed[-1][3])
            many = max(1, int(self.pn_sp_copies.value()))
            for _k in range(many - 1):
                self._bed.append(self._bed[-1])
        name = self._bed[-1][0]
        many = len(self._bed) - n_before
        self._done += 1
        self._done_key = key
        self.tool.clear_selection(self.viewport)
        try:
            self._sel_key = tuple(id(e) for e in self.selection())
        except Exception:
            self._sel_key = ()
        self._waiting = True
        self._sel_text = "Added %s to the bed. Click the next object." % name
        self._pn_key = None
        self.bed_buttons()
        self.update_info()
        n = len(self._bed)
        self.report("Put %s'%s' on the bed at %s (%d on it) - %s. Click the next object and press Add to bed, "
                    "or Send when the bed's full." % ("%d x " % many if many > 1 else "", name, self.describe(), n,
                                                      getattr(self, '_bed_split', "")))
        self.refresh_preview()

    def pn_duplicate(self):
        """One more of the object picked in the list (or the last one added), right after it."""
        if not self._bed:
            self.report("The bed's empty - add an object first.", bad=True)
            return
        row = self.pn_list.currentRow()
        i = row if 0 <= row < len(self._bed) else len(self._bed) - 1
        self._bed.insert(i + 1, self._bed[i])
        self.bed_buttons()
        self.pn_list.setCurrentRow(i + 1)
        self.report("One more '%s' on the bed (%d on it)." % (self._bed[i][0], len(self._bed)))

    def pn_take_off(self):
        if not self._bed:
            self.report("The bed's empty.")
            return
        row = self.pn_list.currentRow()
        self.take_off(row if 0 <= row < len(self._bed) else len(self._bed) - 1)
        self.refresh_preview()

    def pn_send(self, every, save_as=False):
        if not self._bed:
            self.report("The bed's empty - click an object in the work area and press Add to bed first.", bad=True)
            return
        if every:
            self.send_bed(self.pn_b_sendall, save_as=save_as)
        else:
            key = self.pn_printer()
            if key not in self.bed_slicers():
                self.report("Nothing's on %s's bed yet." % self.target_name(key).split(" - ")[0], bad=True)
                return
            self.send_bed(self.pn_b_save if save_as else self.pn_b_send, only=[key], save_as=save_as)
        self.refresh_preview()

    # ---- the list, the buttons, the bed in the preview
    def pn_refresh_list(self):
        if not getattr(self, '_pn_ok', False):
            return
        from PySide6.QtGui import QPixmap, QColor, QIcon
        self.pn_fill_printers()
        keep = self.pn_list.currentRow()
        self.pn_list.clear()
        many = len(self.bed_slicers()) > 1 or len(self._pn_targets or []) > 1
        for k, (name, sc, parts, dests) in enumerate(self._bed):
            sz = tris_size([t for _n, _c, tr in parts for t in tr])
            where = ""
            if many:
                where = "  -  " + ", ".join(sorted(set(self.target_name(d).split(" - ")[0] for d in dests)))
            pm = QPixmap(14, 14)
            pm.fill(QColor(*piece_colour(k)))
            self.pn_list.addItem("%d. %s  -  %s, %s mm%s" % (k + 1, name, sc, " x ".join(_fmt_mm(x) for x in sz),
                                                             where))
            self.pn_list.item(k).setIcon(QIcon(pm))
        if 0 <= keep < self.pn_list.count():
            self.pn_list.setCurrentRow(keep)
        n = len(self._bed)
        key = self.pn_printer()
        on_this = sum(1 for _n, _s, _p, ds in self._bed if any(self.norm_target(d) == key for d in ds))
        who = self.target_name(key).split(" - ")[0]
        self.pn_b_send.setText("Send to %s (%d)" % (who, on_this) if on_this else "Send to %s" % who)
        self.pn_b_send.setEnabled(on_this > 0)
        self.pn_b_save.setEnabled(on_this > 0)
        sl = self.bed_slicers()
        self.pn_b_sendall.setText("Send every printer's bed (%d)" % len(sl))
        self.pn_b_sendall.setVisible(len(sl) > 1)
        self.pn_b_off.setEnabled(n > 0)
        self.pn_b_empty.setEnabled(n > 0)
        self.pn_b_back.setEnabled(bool(StudioDialog._taken))
        try:
            t, fits = self.bed_fit_words(key) if on_this else ("", True)
        except Exception as e:
            t, fits = "Couldn't lay out the bed: %s" % e, False
        if n:
            head = "<b>On the bed: %d object%s</b>" % (n, "" if n == 1 else "s")
            self.pn_lbl_fit.setText(head + (("<br><span style='color:%s'>%s</span>" % (
                "#2e7d32" if fits else "#c0392b", t)) if t else ""))
        else:
            self.pn_lbl_fit.setText("<b>The bed's empty.</b>")

    def pn_ghost(self):
        """The object selected now, scaled and laid flat the way 'Add to bed' would put it: [(name,
        colour, tris)] - or [] when nothing new is selected."""
        live = self.selection()
        if not live or not self.ents:
            return []
        key = tuple(id(e) for e in live)
        if key != self._sel_key or (self._waiting and key == self._done_key):
            return []
        ck = (key, self.describe(), self.unit_mm(), self.cb_flat.isChecked(), len(self._marks),
              id(self.plan), self.cb_split.currentData())
        if self._pn_cache and self._pn_cache[0] == ck:
            return self._pn_cache[1]
        parts, _n, _w = self.make_parts({'use_scale': True, 'layout': 'keep', 'apply_fixes': False,
                                         'per_piece': True})
        if self.cb_flat.isChecked():
            parts = [(n, c, lay_flat(tr)) for n, c, tr in parts]
        parts = [(n, self.PN_NEW_COLOUR, tr) for n, _c, tr in parts]
        self._pn_cache = (ck, parts)
        return parts

    def preview_print_next(self):
        """This page's preview: the picked printer's bed - what's on it in colour, the object selected
        now in yellow, all laid out the way they'll be sent."""
        self.b_nextbed.setVisible(False)
        key = self.pn_printer()
        _path, pr = self.target(key)
        bx, by, bz, gap, keep = self.printer_settings(pr)
        items = self.bed_items(colour_each=True, dest=key, per_piece=keep)
        try:
            ghost = self.pn_ghost()
        except Exception as e:
            ghost = []
            self.report("Couldn't read the selected object: %s" % e, bad=True)
        if ghost and not keep and len(ghost) > 1:
            ghost = [(ghost[0][0], self.PN_NEW_COLOUR, [t for _n, _c, tr in ghost for t in tr])]
        many = max(1, int(self.pn_sp_copies.value())) if ghost else 0
        ghost = [("NEW: " + n, c, tr) for n, c, tr in ghost] * many
        allp = items + ghost
        who = pr.get('name') if pr else self.target_name("").split(" - ")[0]
        if not allp:
            self._bed_note = ["%s's bed (%s x %s mm) - empty" % (who, _fmt_mm(bx), _fmt_mm(by))]
            self.canvas.empty_text = "Click an object in the work area - it shows here, on the bed, ready to add."
            self.canvas.set_parts([], (bx, by) if self.cb_bed.isChecked() else None)
            self._shown = None
            return
        use_bed = self.cb_bed.isChecked()
        if len(allp) > 1:
            placed, _s = lay_out_packed([(n, tr) for n, _c, tr in allp], bx if use_bed else 0.0,
                                        by if use_bed else 0.0, max(0.2, gap))
            allp = [(n, c, tr) for (n, tr), (_n, c, _t) in zip(placed, allp)]
        else:
            allp = [(allp[0][0], allp[0][1], stand_centred(allp[0][2]))]
        s = tris_size([t for _n, _c, tr in allp for t in tr])
        fits = (not use_bed) or (s[0] <= bx + 1e-6 and s[1] <= by + 1e-6 and s[2] <= bz + 1e-6)
        shown = (bx, by) if use_bed else (s[0] * 1.15 + 10, s[1] * 1.15 + 10)
        self.canvas.empty_text = "Nothing to show"
        self.canvas.set_parts(allp, shown, None)
        self._shown = None
        n_on = len(set(i for i, (_n, _s, _p, ds) in enumerate(self._bed)
                       if any(self.norm_target(d) == key for d in ds)))
        self._bed_note = ["%s's bed (%s x %s mm): %d on it%s" % (
            who, _fmt_mm(bx), _fmt_mm(by), n_on, ("  + %d to add (yellow)" % many) if ghost else ""),
            "%s mm altogether - %s" % (" x ".join(_fmt_mm(v) for v in s),
                                       "fits" if fits else "TOO BIG for this bed")]

    def _pn_tick(self):
        """Every moment while this page shows: the preview follows what's selected, even with
        'Follow selection' off, and clears when you click off."""
        if getattr(self, '_pn_index', -1) != self.tabs.currentIndex() or not self.right.isVisible():
            return
        try:
            live = self.selection()
        except Exception:
            return
        key = tuple(id(e) for e in live)
        if key == self._pn_key:
            return
        self._pn_key = key
        if live and key != self._sel_key:
            self.watch_selection(force=True)
        else:
            self._pv_timer.start(60)

    # ------------------------------------------------------------------ checking and repairing
    def check_now(self, *_):
        if not self.ents:
            self.report("Select the object (a group, or its faces) first.", bad=True)
            return
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            text, bad, marks = self.run_check()
        except Exception as e:
            text, bad, marks = "Couldn't check it: %s" % e, True, []
        finally:
            QApplication.restoreOverrideCursor()
        self.txt_check.setPlainText(text)
        self._marks = marks
        if marks and self.cb_preview.currentData() != 'model':
            self.cb_preview.setCurrentIndex(self.cb_preview.findData('model'))
        self._shown = None
        self.refresh_preview()
        self.report(text.split("\n")[0] + (" - see the Repair page." if bad else ""), bad)

    def run_check(self):
        raw = self.raw_parts()
        k = self.unit_mm()
        f = self.factors()
        kk = (k * f[0], k * f[1], k * f[2])
        parts = [(n, c, scale_tris(tr, kk)) for n, c, tr in raw]
        if not parts:
            return "Nothing to check: select the object (a group, or its faces) first.", True, []
        before_open = sum(edge_report(tr)[0] for _n, _c, tr in parts)
        tot, lines, marks, warn = {}, [], [], False
        ntri = shells = many = 0
        nz = self.sp_nozzle.value() if self.cb_thin.isChecked() else 0.0
        for n, c, tr in parts:
            tr, cnt = repair_part(tr, self.repair_opts())
            for a, b in cnt.items():
                tot[a] = tot.get(a, 0) + b
            ntri += len(tr)
            try:
                shells += len([s for s in _shells(tr)[2] if len(s) >= 2])
            except Exception:
                pass
            op, mn = edge_report(tr)
            many += mn
            if op:
                marks += [(tuple(p[i] / kk[i] for i in range(3)), tuple(q[i] / kk[i] for i in range(3)))
                          for p, q in open_edge_segments(tr)]
            if nz > 0:
                th, share = thin_walls(tr, nz)
                if th is not None and share > 0.005:
                    warn = True
                    lines.append("%s: %d%% of it is thinner than the %.2f mm nozzle (about %.2f mm thick)." % (
                        n, int(round(share * 100)) or 1, nz, th))
            ov = overlapping_solids(tr)
            if ov:
                lines.append("%s: %d solid%s overlap another (fine for printing - the slicer joins them)." % (
                    n, ov, "" if ov == 1 else "s"))
        size = tris_size([t for _n, _c, tr in parts for t in tr])
        out = ["Checked %d piece%s at %s - %s mm." % (len(parts), "" if len(parts) == 1 else "s", self.describe(),
                                                   " x ".join(_fmt_mm(v) for v in size)),
               "%d triangles, %d solid%s. Open edges before repairs: %d." % (
                   ntri, shells, "" if shells == 1 else "s", before_open)]
        rl = repair_lines(tot, will=True)
        out += rl if rl else ["Nothing needed mending with the repairs ticked."]
        if marks:
            warn = True
            out.append("%d open edge%s left - real gaps, shown in red in the preview (As in the model). Try "
                       "'Fill holes' with more edges, or mend the model there." % (len(marks), "" if len(marks) == 1 else "s"))
        else:
            out.append("No gaps: every piece is closed (watertight).")
        if many:
            out.append("%d edge%s shared by more than two faces - solids touching along an edge. Usually fine; "
                       "some slicers mention it." % (many, "" if many == 1 else "s"))
        out += lines
        if nz > 0 and not any("thinner" in ln for ln in lines):
            out.append("Every wall is at least %.2f mm (your nozzle)." % nz)
        return "\n".join(out), warn, marks

    def repaired_copy(self, *_):
        if not self.ents:
            self.report("Select the object (a group, or its faces) first.", bad=True)
            return
        try:
            k = self.unit_mm()
            tris = [t for _n, _c, tr in self.raw_parts() for t in tr]
            mm = scale_tris(tris, (k, k, k))
            mm, cnt = repair_part(mm, self.repair_opts())
            back = scale_tris(mm, (1.0 / k, 1.0 / k, 1.0 / k))
            text, bad = self.tool.add_triangles_copy(self.viewport, back, "Repaired copy of %s" % self.name())
            if not bad:
                lines = repair_lines(cnt)
                text += (" " + " ".join(lines)) if lines else " (nothing needed mending)"
        except Exception as e:
            text, bad = "Couldn't make the copy: %s" % e, True
        self.report(text, bad)

    # ------------------------------------------------------------------ export
    def export_opts(self):
        return {'format': self.cb_fmt.currentData(), 'file_unit': self.cb_funit.currentData(),
                'y_up': bool(self.cb_up.currentData()), 'use_scale': self.cb_usescale.isChecked(),
                'per_piece': self.cb_perpiece.isChecked(), 'layout': self.cb_layout.currentData(),
                'colours': self.cb_colours.isChecked(), 'apply_fixes': self.cb_fixes.isChecked(),
                'view': self.cb_view.currentData(), 'png_size': self.sp_png.value()}

    def export(self, override=None, to_path=None, open_it=None):
        """Saves what's selected (the model itself is never changed). to_path: save there with no
        save box. open_it: open it afterwards (None: as ticked). Returns True if it was saved."""
        from PySide6.QtWidgets import QFileDialog, QApplication
        from PySide6.QtCore import Qt
        o = self.export_opts()
        o.update(override or {})
        self._last_files = []
        if not self.ents and o.get('parts') is None:
            self.report("Select the object (a group, or its faces) first.", bad=True)
            return False
        fmt = FMT.get(o['format'], FORMATS[0])
        key, label, ext, writer, kind = fmt[0], fmt[1], fmt[2], fmt[3], fmt[4]
        safe = "".join(ch for ch in (o.get('name') or self.name()) if ch not in '\\/:*?"<>|').strip() or "model"
        if o.get('use_scale') and kind != 'picture' and not o.get('name'):
            safe += " " + self.describe().replace(":", "-").replace("%", "pc").replace(" ", "")
        folder = self.st.get('last_folder') or os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.isdir(folder):
            folder = os.path.expanduser("~")
        if to_path:
            path = to_path(safe, ext)
        else:
            res = QFileDialog.getSaveFileName(self, "Save as %s" % label, os.path.join(folder, safe + ext),
                                              "%s (*%s);;All files (*)" % (label, ext))
            path = res[0] if isinstance(res, (tuple, list)) else res
            if not path:
                return False
            if not path.lower().endswith(ext):
                path += ext
            self.st['last_folder'] = os.path.dirname(path)
        if kind == 'picture':
            try:
                ok = self.canvas.picture(int(o.get('png_size', 2000))).save(path, "PNG")
            except Exception as e:
                ok, path = False, "%s (%s)" % (path, e)
            self.report(("Saved the picture:\n%s" % path) if ok else "Couldn't save the picture %s" % path, not ok)
            if ok and (self.cb_open.isChecked() if open_it is None else open_it):
                open_in_slicer([path], "")
            return bool(ok)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            o['thin'] = key in ('3mf', 'stl', 'stla') and bool(o.get('use_scale'))
            parts, notes, warn = self.make_parts(o)
            if not parts:
                raise RuntimeError("there's nothing to save - select the object (a group, or its faces).")
            if not o.get('colours'):
                parts = [(n, (200, 200, 200), tr) for n, _c, tr in parts]
            size = tris_size([t for _n, _c, tr in parts for t in tr])
            unit_key = o.get('file_unit', 'mm')
            umm = dict((u[2], u[1]) for u in FILE_UNITS).get(unit_key, 1.0)
            if key == '3mf':
                umm, unit_key = 1.0, 'mm'                     # 3MF is always millimetres
                if o.get('layout') == 'bed' and len(parts) > 1:
                    bx, by = self.bed[0].value() / 2.0, self.bed[1].value() / 2.0
                    parts = [(n, c, [tuple((q[0] + bx, q[1] + by, q[2]) for q in t) for t in tr])
                             for n, c, tr in parts]
            if key == 'svg' and unit_key not in ('mm', 'cm', 'in'):
                umm, unit_key = 1.0, 'mm'                     # a drawing: mm, cm or inches
            if kind == 'lines':
                fparts = to_file(parts, umm, False)
                files = writer(path, fparts, view=o.get('view', 'top'), units=unit_key) if key == 'dxf2d' else \
                    writer(path, fparts, view=o.get('view', 'top'), units=unit_key, colours=o.get('colours'),
                           title=self.name(), scale_note=self.describe() if o.get('use_scale') else "full size")
                what = "a drawing of %d piece%s" % (len(parts), "" if len(parts) == 1 else "s")
            else:
                fparts = to_file(parts, umm, bool(o.get('y_up')))
                if key in ('stl', 'stla') and o.get('per_piece') and len(fparts) > 1:
                    folder = path[:-len(ext)]
                    os.makedirs(folder, exist_ok=True)
                    files, used = [], set()
                    for pn, pc, ptr in fparts:
                        fn = "".join(ch for ch in pn if ch not in '\\/:*?"<>|').strip() or "piece"
                        base, i = fn, 2
                        while fn.lower() in used:
                            fn, i = "%s %d" % (base, i), i + 1
                        used.add(fn.lower())
                        fp = os.path.join(folder, fn + ext)
                        writer(fp, [(pn, pc, ptr)])
                        files.append(fp)
                    path = folder
                    what = "%d pieces, one file each, in the folder" % len(fparts)
                elif key in ('obj', 'ply', 'glb', 'gltf', 'wrl'):
                    files = writer(path, fparts, colours=bool(o.get('colours')))
                    what = "%d piece%s" % (len(fparts), "" if len(fparts) == 1 else "s")
                elif key == 'dxf3d':
                    files = writer(path, fparts, units=unit_key)
                    what = "%d piece%s as 3D faces" % (len(fparts), "" if len(fparts) == 1 else "s")
                else:
                    files = writer(path, fparts)
                    what = "%d piece%s" % (len(fparts), "" if len(fparts) == 1 else "s")
        except Exception as e:
            QApplication.restoreOverrideCursor()
            self.report("Couldn't export it: %s" % e, bad=True)
            return False
        QApplication.restoreOverrideCursor()
        self._last_files = list(files)
        msg = "Saved %s, %s mm (%s):\n%s" % (what, " x ".join(_fmt_mm(v) for v in size),
                                              o.get('scale_words') or (self.describe() if o.get('use_scale')
                                                                       else "full size"), path)
        for ln in notes:
            msg += "\n" + ln
        if self.cb_open.isChecked() if open_it is None else open_it:
            printing = key in ('3mf', 'stl', 'stla')
            msg += "\n" + open_in_slicer(files[:1] if not printing else files,
                                         self.ed_slicer.text().strip() if printing else "")
        msg += "\nYour model in the work area is just as it was."
        self.report(msg, warn)
        self.save_now()
        return True

    # ------------------------------------------------------------------ odds and ends
    def report(self, text, bad=False):
        self._last = text
        self.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if bad else "#2e7d32"))
        self.lbl_report.setText(text)
        self.lbl_report.setVisible(True)

    def show_info(self, *_):
        txt = INFO_TEXT
        if self._last:
            txt += "<br><br><b>Last time:</b><br>" + self._last.replace("\n", "<br>")
        box = QMessageBox(self)
        box.setWindowTitle(PLUGIN_NAME + " - Info")
        box.setText(txt)
        box.exec()


def repair_lines(n, will=False):
    """What the repairs did, in words."""
    out = []
    if n.get('zero'):
        out.append("%s %d face%s with no area." % ("Will take out" if will else "Took out", n['zero'],
                                                   "" if n['zero'] == 1 else "s"))
    if n.get('dup'):
        out.append("%s %d doubled face%s." % ("Will take out" if will else "Took out", n['dup'],
                                              "" if n['dup'] == 1 else "s"))
    if n.get('cracks'):
        out.append("%s %d hairline crack%s." % ("Will mend" if will else "Mended", n['cracks'],
                                                "" if n['cracks'] == 1 else "es"))
    if n.get('holes'):
        out.append("%s %d hole%s." % ("Will fill" if will else "Filled", n['holes'], "" if n['holes'] == 1 else "s"))
    if n.get('holes_left'):
        out.append("%d opening%s too big to fill (left open)." % (n['holes_left'], "" if n['holes_left'] == 1 else "s"))
    if n.get('turned'):
        out.append("%s %d face%s that pointed the wrong way%s." % (
            "Will turn" if will else "Turned", n['turned'], "" if n['turned'] == 1 else "s",
            " (%d solid%s inside out)" % (n['inside'], "" if n['inside'] == 1 else "s") if n.get('inside') else ""))
    return out


# ---------------------------------------------------------------------------
# The converter bar on IngeTrazo's main window
# ---------------------------------------------------------------------------
def _main_window():
    from PySide6.QtWidgets import QApplication, QMainWindow
    app = QApplication.instance()
    if app is None:
        return None
    wins = [w for w in app.topLevelWidgets() if isinstance(w, QMainWindow)]
    shown = [w for w in wins if w.isVisible()]
    return (shown or wins or [None])[0]


def find_toolbar(win=None):
    from PySide6.QtWidgets import QToolBar
    win = win or _main_window()
    return win.findChild(QToolBar, TOOLBAR_NAME) if win is not None else None


def install_toolbar(win=None):
    """Adds the converter bar along the top of the main window (once)."""
    from PySide6.QtWidgets import QToolBar
    from PySide6.QtCore import Qt
    win = win or _main_window()
    if win is None:
        return None
    tb = find_toolbar(win)
    if tb is not None:
        return tb
    cur = load_settings()
    tb = QToolBar("Scale Converter", win)
    tb.setObjectName(TOOLBAR_NAME)
    tb.setToolTip("Scale converter (%s)" % PLUGIN_NAME)
    strip = ConverterStrip(cur, tb, studio_button=True)
    eddy_window(strip, PLUGIN_NAME, EDDY_TIPS, place=False)
    tb.addWidget(strip)
    win.addToolBar(Qt.TopToolBarArea, tb)

    def vis_changed(on):
        update_settings(visible=bool(on))
    tb.visibilityChanged.connect(vis_changed)
    tb.setVisible(bool(cur.get('visible', True)))
    return tb


def show_toolbar(on=True):
    tb = find_toolbar() or (install_toolbar() if on else None)
    if tb is not None:
        tb.setVisible(bool(on))
    update_settings(visible=bool(on))


def _install_when_ready(tries=0):
    """IngeTrazo loads plugins before its window is up, so wait for the window."""
    try:
        from PySide6.QtCore import QTimer
        win = _main_window()
        if win is None or not win.isVisible():
            if tries < 240:
                QTimer.singleShot(500, lambda: _install_when_ready(tries + 1))
            return
        if load_settings().get('visible', True):
            install_toolbar(win)
    except Exception as e:
        print("%s: could not add the converter bar (%s)." % (PLUGIN_NAME, e))


try:
    _install_when_ready()
except Exception:
    pass


def _find_viewport():
    """Finds the IngeTrazo viewport: the widget that has a scene and an undo history."""
    from PySide6.QtWidgets import QApplication
    for w in QApplication.allWidgets():
        if hasattr(w, 'scene') and hasattr(w, 'history') and hasattr(w, 'notify_scene_changed'):
            return w
    return None


def open_studio(viewport=None):
    """Opens the window (or brings it to the front if it's open)."""
    dlg = ScaleStudioTool._dialog
    if dlg is not None:
        try:
            if dlg.isVisible():
                if viewport is not None:
                    dlg.viewport = viewport
                dlg.raise_()
                dlg.activateWindow()
                return dlg
        except Exception:
            pass
    viewport = viewport or _find_viewport()
    if viewport is None:
        print("%s: could not find the work area." % PLUGIN_NAME)
        return None
    try:
        tool = ScaleStudioTool()
    except TypeError:
        tool = ScaleStudioTool.__new__(ScaleStudioTool)
    dlg = StudioDialog(viewport, tool)
    ScaleStudioTool._dialog = dlg

    def closed(*_):
        ScaleStudioTool._dialog = None
        try:
            dlg._timer.stop()
        except Exception:
            pass
    dlg.finished.connect(closed)
    eddy_window(dlg, PLUGIN_NAME + " window", EDDY_TIPS, place=True)
    dlg.show()
    return dlg


# ---------------------------------------------------------------------------
# Scaling in the work area the way IngeTrazo's own Scale tool does it
# ---------------------------------------------------------------------------
try:
    from core.history import Command as _Cmd
except Exception:
    _Cmd = object


class StudioTransformCommand(_Cmd):
    """Puts the selected groups (and any loose faces) through the matrix m - scale about the
    pivot, then over to one side. A component (a group with a placement) just has its placement
    changed; a plain group has every vertex of its mesh moved (and the groups inside it). Each
    mesh is snapshotted, so Undo and Redo put back exactly what was there."""
    keeps_paint = True

    def __init__(self, groups, points, m):
        self.groups = list(groups)
        self.points = [QVector3D(p) for p in points]
        self.m = m
        self._targets = None
        self._before = self._after = None

    def _find(self):
        out = []

        def walk(g, depth=0):
            if getattr(g, 'xform', None) is not None:
                out.append((g, 'x'))           # its placement carries everything inside it
                return
            if getattr(g, 'mesh', None) is not None:
                out.append((g, 'm'))
            if depth < 16:
                for c in (getattr(g, 'children', None) or ()):
                    walk(c, depth + 1)
        for g in self.groups:
            walk(g)
        return out

    def _snap(self, scene):
        from PySide6.QtGui import QMatrix4x4
        shots = []
        for g, kind in self._targets:
            if kind == 'x':
                shots.append(QMatrix4x4(g.xform))
            else:
                shots.append((g.mesh.capture_state(), getattr(g, 'axes', None)))
        loose = scene.mesh.capture_state() if self.points else None
        return shots, loose

    def _put(self, scene, snap):
        from PySide6.QtGui import QMatrix4x4
        shots, loose = snap
        for (g, kind), v in zip(self._targets, shots):
            if kind == 'x':
                g.xform = QMatrix4x4(v)
            else:
                g.mesh.restore_state(v[0])
                try:
                    g.axes = v[1]
                except Exception:
                    pass
        if loose is not None:
            scene.mesh.restore_state(loose)
        scene.version += 1

    def do(self, scene):
        if self._after is not None:                 # redo
            self._put(scene, self._after)
            return
        self._targets = self._find()
        self._before = self._snap(scene)
        m = self.m
        for g, kind in self._targets:
            if kind == 'x':
                g.xform = m * g.xform
                continue
            gm = g.mesh
            for v in list(gm.vertices):
                gm.move_vertex(v, m.map(v.position) - v.position)
            try:
                from core.group import _remap_uvws
                _remap_uvws(gm, m)                  # textures follow
            except Exception:
                pass
            try:
                from core.group import carry_axes
                carry_axes(g, m)                    # and its own axes
            except Exception:
                pass
        if self.points:
            try:
                from core.history import _key
            except Exception:
                from core.mesh import _key
            keys = {_key(p) for p in self.points}
            for v in [v for v in scene.mesh.vertices if _key(v.position) in keys]:
                scene.mesh.move_vertex(v, m.map(v.position) - v.position)
            try:
                from core.topology import fold_nonplanar_faces
                fold_nonplanar_faces(scene.mesh)
            except Exception:
                pass
        self._after = self._snap(scene)
        scene.version += 1

    def undo(self, scene):
        if self._before is not None:
            self._put(scene, self._before)


# ---------------------------------------------------------------------------
# Tool: Ctrl+Alt+K opens the window
# ---------------------------------------------------------------------------
class ScaleStudioTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+K"
    description = ("Scale, repair and export: scales the selected object in the work area (to a model "
                   "scale, a percentage or a size), splits it into pieces with a live preview, mends it "
                   "and exports it for printing, other 3D programs, web, CAD, laser cutting or drawings. "
                   "With the real-to-model size converter.")
    _dialog = None

    def on_activate(self, viewport):
        open_studio(viewport)

    def on_deactivate(self, viewport):
        pass

    def scale_selection(self, viewport, entities, f, pivot, how, words, beside=True):
        """Scales the selection by f = (fx, fy, fz) about the pivot, in place or as a copy beside it.
        In place with beside: it's moved along X to stand just beside where it was.
        Returns (message, warning)."""
        report = {}
        fx, fy, fz = f

        def mutate(scene):
            from core.mesh import Mesh
            from core.group import Group
            if how == 'copy':
                loops = world_loops(entities)
                if not loops:
                    raise RuntimeError("A copy needs faces in the selection.")
                lo, hi = loops_bounds(loops)
                pv = pivot_point(pivot, lo, hi)

                def scaled(pt):
                    return QVector3D(pv.x() + (pt.x() - pv.x()) * fx, pv.y() + (pt.y() - pv.y()) * fy,
                                     pv.z() + (pt.z() - pv.z()) * fz)
                report.update(self._make_copy(scene, Mesh, Group, loops, lo, hi, scaled, "Scaled %s" % words))
                return
            verts, faces, meshes = collect(entities)
            if not verts:
                raise RuntimeError("Nothing to scale.")
            lo, hi = bounds(verts)
            pv = pivot_point(pivot, lo, hi)
            # (older IngeTrazo only: the vertices are moved one by one)
            size_max = max(hi.x() - lo.x(), hi.y() - lo.y(), hi.z() - lo.z(), 1e-9)
            tol = size_max * 1e-7

            def key(q):
                return (round(q.x() / tol), round(q.y() / tol), round(q.z() / tol))

            # beside: the scaled one's left side a little past where its right side was
            dx = 0.0
            if beside:
                width = hi.x() - lo.x()
                dx = hi.x() + width * COPY_GAP - (pv.x() + (lo.x() - pv.x()) * fx)

            def scaled(pt):
                return QVector3D(pv.x() + (pt.x() - pv.x()) * fx + dx, pv.y() + (pt.y() - pv.y()) * fy,
                                 pv.z() + (pt.z() - pv.z()) * fz)
            self._scale_in_place(scene, verts, faces, meshes, scaled, key)

        try:
            if how != 'copy' and _Cmd is not object:
                # IngeTrazo's own way: groups move as a whole (their meshes told they changed, so the
                # work area redraws straight away), undo puts every group back
                loops = world_loops(entities)
                if loops:
                    lo, hi = loops_bounds(loops)
                else:
                    lo, hi = bounds(collect(entities)[0])
                pv = pivot_point(pivot, lo, hi)
                dx = 0.0
                if beside:
                    width = hi.x() - lo.x()
                    dx = hi.x() + width * COPY_GAP - (pv.x() + (lo.x() - pv.x()) * fx)
                from PySide6.QtGui import QMatrix4x4
                m = QMatrix4x4()
                m.translate(QVector3D(pv.x() + dx, pv.y(), pv.z()))
                m.scale(float(fx), float(fy), float(fz))
                m.translate(QVector3D(-pv.x(), -pv.y(), -pv.z()))
                groups = [e for e in entities if _is_group(e)]
                points = []
                for e in entities:
                    if _is_group(e):
                        continue
                    if _is_face(e):
                        points += [q for q in (vertex_to_vector3d(v) for v in _face_vertices(e)) if q is not None]
                    else:
                        for a in ('a', 'b', 'v1', 'v2', 'start', 'end'):
                            q = vertex_to_vector3d(getattr(e, a, None)) if getattr(e, a, None) is not None else None
                            if q is not None:
                                points.append(q)
                if not groups and not points:
                    raise RuntimeError("Nothing to scale.")
                self._run(viewport, StudioTransformCommand(groups, points, m))
            else:
                self._run(viewport, SnapshotImport(mutate))
        except Exception as e:
            return "Scaling failed: %s" % e, True
        try:
            viewport.notify_scene_changed()
        except Exception:
            pass
        try:
            viewport.update()
        except Exception:
            pass
        if report.get('lost'):
            return ("The copy at %s is missing %d of %d faces: IngeTrazo treats points closer than 0.1 mm as "
                    "one point, so details that small can't be kept in the model. To print it, use the "
                    "Export page instead - every detail is kept." % (
                        words, report['lost'], report['lost'] + report['made'])), True
        return "Scaled %s to %s%s. (Edit > Undo puts it back.)" % (
            "a copy" if how == 'copy' else "it", words,
            ", beside where it was" if (how != 'copy' and beside) else ""), False

    @staticmethod
    def _run(viewport, cmd):
        """Runs a command through the undo history. IngeTrazo keeps quiet when one fails (it puts
        the model back and notes why): that note is turned into an error here."""
        h = viewport.history
        for a in ('last_error', 'last_rejected'):
            try:
                setattr(h, a, None)
            except Exception:
                pass
        h.execute(cmd)
        err = getattr(h, 'last_error', None) or getattr(h, 'last_rejected', None)
        if err:
            raise RuntimeError(str(err))

    def clear_selection(self, viewport):
        """Nothing selected, ready for the next object (whichever way this IngeTrazo does it)."""
        scene = getattr(viewport, 'scene', None)
        done = False
        for fn in ('clear_selection', 'deselect_all', 'select_none'):
            m = getattr(scene, fn, None) or getattr(viewport, fn, None)
            if callable(m):
                try:
                    m()
                    done = True
                    break
                except Exception:
                    pass
        if not done:
            try:
                sel = getattr(scene, 'selection', None)
                if hasattr(sel, 'clear'):
                    sel.clear()
                else:
                    scene.selection = []
            except Exception:
                pass
        for fn in ('notify_selection_changed', 'notify_scene_changed', 'update'):
            m = getattr(viewport, fn, None)
            if callable(m):
                try:
                    m()
                except Exception:
                    pass

    def add_triangles_copy(self, viewport, tris, name):
        """Puts triangles (model units) into the model as a new group beside the selection."""
        loops = [([QVector3D(*a), QVector3D(*b), QVector3D(*c)], [], None) for a, b, c in tris]
        if not loops:
            return "Nothing to copy.", True
        report = {}

        def mutate(scene):
            from core.mesh import Mesh
            from core.group import Group
            lo, hi = loops_bounds(loops)
            report.update(self._make_copy(scene, Mesh, Group, loops, lo, hi, lambda q: QVector3D(q), name))
        try:
            self._run(viewport, SnapshotImport(mutate))
        except Exception as e:
            return "Couldn't make the copy: %s" % e, True
        try:
            viewport.notify_scene_changed()
        except Exception:
            pass
        msg = "Put '%s' beside it (%d faces)." % (name, report.get('made', 0))
        if report.get('lost'):
            msg += " %d tiny faces couldn't be made in the model." % report['lost']
        return msg, bool(report.get('lost'))

    # ------------------------------------------------------------------ copy
    def _make_copy(self, scene, Mesh, Group, loops, lo, hi, scaled, den):
        # den: the name the copy gets
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
                               "IngeTrazo's 0.1 mm). Use the Export page instead.")
        try:
            g = Group(target, name=den)
        except TypeError:
            g = Group(den)
            g.mesh = target
        try:
            g.name = den
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
                    "'Scale a copy'." % len(shared))
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
                "Use 'Scale a copy' instead." % (failed, len(plan)))

        touched = list(meshes)
        if sm is not None and not any(sm is m for m in touched):
            touched.append(sm)
        refresh_meshes(touched)
        print("%s: scaled %d points" % (PLUGIN_NAME, len(plan)))


# ---------------------------------------------------------------------------


def run(viewport=None):
    """Console entry point: run() opens the window."""
    return open_studio(viewport)
