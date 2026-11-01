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
    QComboBox, QMessageBox, QLabel, QPushButton, QLineEdit, QWidget
)

PLUGIN_NAME = "3D Print Scaler"

SCALE_PRESETS = [1, 2, 5, 10, 20, 25, 50, 75, 100, 125, 150, 200, 250, 500, 1000]

# model railway scales (name, 1 : n)
RAIL_SCALES = [
    ("Z  1:220", 220.0), ("N (US, Europe)  1:160", 160.0), ("N (Japan)  1:150", 150.0),
    ("N (UK)  1:148", 148.0), ("TT  1:120", 120.0),
    ("HO  1:87", 87.0), ("1:80 (Eddy's)", 80.0), ("OO / EM / P4 / OO9  1:76.2", 76.2),
    ("S  1:64", 64.0), ("O (US)  1:48", 48.0), ("O (UK) / On30  1:43.5", 43.5), ("O (Europe)  1:45", 45.0),
    ("Gauge 1  1:32", 32.0), ("G / LGB  1:22.5", 22.5), ("Gauge 3 / G 1:20.3", 20.3),
]
# your own scales, and the one the window opens on, are kept here
SCALES_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_print_scaler.json")


def load_scale_settings():
    import json
    d = {'mine': [], 'default': None, 'slicer': '', 'settings': {}}
    try:
        with open(SCALES_FILE, "r", encoding="utf-8") as f:
            got = json.load(f)
        if isinstance(got, dict):
            d['mine'] = [(str(n), float(x)) for n, x in got.get('mine', []) if float(x) > 0]
            d['default'] = float(got['default']) if got.get('default') else None
            d['slicer'] = str(got.get('slicer') or '')
            if isinstance(got.get('settings'), dict):
                d['settings'] = got['settings']
    except Exception:
        pass
    return d


def save_scale_settings(d):
    import json
    try:
        with open(SCALES_FILE, "w", encoding="utf-8") as f:
            json.dump({'mine': d.get('mine', []), 'default': d.get('default'),
                       'slicer': d.get('slicer', ''), 'settings': d.get('settings', {})}, f, indent=1)
    except Exception:
        pass
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
            'check_bed': True, 'bed_x': 220.0, 'bed_y': 220.0, 'bed_z': 250.0,
            'separate': False, 'open_after': False, 'keep_open': False, 'part_gap': 5.0, 'split_depth': 0,
            'lay_flat': True, 'warn_thin': True, 'nozzle': 0.4}

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


def piece_colour(i):
    return PIECE_COLOURS[i % len(PIECE_COLOURS)]


def piece_leaves(entities, with_tris=True):
    """Every smallest part of the selection: [(key, name, kind, [triangles in world metres])].
    key is the part's path of group names (so a plan still fits after the window is reopened),
    kind the name of the group it's in."""
    out, seen = [], {}
    loose = []
    for e in entities:
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
            if lvl < 12:
                for c in _kids(g):
                    walk(c, here, lvl + 1)
        walk(e, [], 0)
    if loose:
        tris = _tris_of(loose) if with_tris else [None]
        if tris:
            out.append(("Selected faces", "Selected faces", "", tris))
    return out


def plan_parts(leaves, plan):
    """Parts from leaves and a plan {'pieces': [names], 'keys': {key: piece name}}: each planned
    piece is all its parts together; parts in no piece print on their own."""
    pieces = list(plan.get('pieces', [])) if plan else []
    keys = plan.get('keys', {}) if plan else {}
    merged = dict((p, []) for p in pieces)
    alone = []
    for key, name, kind, tris in leaves:
        p = keys.get(key)
        if p in merged:
            merged[p] += tris
        else:
            alone.append((name, tris))
    out = [(p, merged[p]) for p in pieces if merged[p]]
    names = {}
    for n, tr in out + alone:
        names[n] = names.get(n, 0) + 1
    seen = {}
    res = []
    for n, tr in out + alone:
        seen[n] = seen.get(n, 0) + 1
        res.append((n if names[n] == 1 else "%s (%d)" % (n, seen[n]), tr))
    return res


def _qt(group, name):
    """A Qt enum value, old or new spelling (Qt.Checked or Qt.CheckState.Checked)."""
    from PySide6.QtCore import Qt
    v = getattr(Qt, name, None)
    return v if v is not None else getattr(getattr(Qt, group), name)


def _prep_part(tris, limit=9000):
    """A part's triangles ready to draw: [(tri, normal, edge flags)] - an edge is drawn as a line
    where the surface folds (or ends), so the part's shape reads clearly, not its triangles."""
    import math
    step = max(1, len(tris) // limit)
    tris = tris[::step]
    out, edges = [], {}

    def k(p):
        return (round(p[0], 7), round(p[1], 7), round(p[2], 7))
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
        for e in range(3):
            key = tuple(sorted((k(t[e]), k(t[(e + 1) % 3]))))
            edges.setdefault(key, []).append((idx, e))
    for lst in edges.values():
        if len(lst) != 2:
            for idx, e in lst:
                out[idx][2][e] = True
            continue
        (i1, e1), (i2, e2) = lst
        n1, n2 = out[i1][1], out[i2][1]
        if n1[0] * n2[0] + n1[1] * n2[1] + n1[2] * n2[2] < 0.94:      # a fold of more than ~20 degrees
            out[i1][2][e1] = True
            out[i2][2][e2] = True
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


class PieceCanvas(QWidget):
    """A picture of the parts, each in its piece's colour, outlined where the surfaces fold.
    Click a part to pick it (Ctrl / Shift for more); the mouse wheel zooms in on the pointer;
    drag with the right (or middle) button to move the picture; double-click to fit it again."""

    def __init__(self, dlg):
        super().__init__(dlg)
        self.dlg = dlg
        self.setMinimumSize(560, 480)
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
            xs = [x for e in items for x, _ in e[2]]
            ys = [y for e in items for _, y in e[2]]
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
        for _d, i, pts, sh, ed in self.items:
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
            if mods & Qt.ShiftModifier:
                mode = 'remove'
            elif mods & Qt.ControlModifier:
                mode = 'add'
        except Exception:
            pass
        self._spin = (mx, my, self.az, self.el, mode, False)


class PiecesDialog(QDialog):
    """Shows every part of the selection; you pick parts and put them into print pieces, each
    piece its own colour. Parts in no piece print on their own."""

    def __init__(self, parent, leaves, plan):
        super().__init__(parent)
        from PySide6.QtWidgets import QTableWidget, QAbstractItemView, QSplitter
        self.setWindowTitle(PLUGIN_NAME + " - Plan the print pieces")
        self.leaves = leaves
        self.pieces = list((plan or {}).get('pieces', []))
        keys = (plan or {}).get('keys', {})
        known = set(k for k, _n, _kd, _t in leaves)
        self.keys = {k: p for k, p in keys.items() if k in known and p in self.pieces}
        lay = QVBoxLayout(self)
        tip = QLabel("Pick parts in the list or click them in the picture (Ctrl+click to pick more, Shift+click to un-pick), then "
                     "put them in a piece. Each piece prints as one and has its own colour; grey parts print "
                     "on their own.")
        tip.setWordWrap(True)
        lay.addWidget(tip)
        row = QHBoxLayout()
        lay.addLayout(row, 1)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Part", "In group", "Print piece"])
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
        left = QVBoxLayout()
        left.addWidget(self.table, 1)
        lp = QLabel("Print pieces - untick to hide them in the picture:")
        left.addWidget(lp)
        self.piece_list = QListWidget()
        self.piece_list.setMaximumHeight(170)
        self.piece_list.setToolTip("Every piece, in its colour, and the parts printing on their own. Untick one "
                                   "to hide it in the picture, so you can see what's behind. (Hidden parts are "
                                   "still printed.)")
        left.addWidget(self.piece_list)
        row.addLayout(left, 2)
        self.canvas = PieceCanvas(self)
        self.canvas.setToolTip("The parts, coloured by the piece they're in (grey: on their own). Click a part to "
                               "pick it - Ctrl+click to pick more, Shift+click to un-pick. Picked parts show yellow.")
        row.addWidget(self.canvas, 3)

        brow = QHBoxLayout()
        b_new = QPushButton("New piece from picked")
        b_new.setToolTip("Makes a new piece (a new colour) holding the parts you've picked.")
        self.cb_piece = QComboBox()
        self.cb_piece.setToolTip("The piece to add the picked parts to.")
        b_add = QPushButton("Add picked to")
        b_add.setToolTip("Puts the picked parts into the piece chosen beside it.")
        b_out = QPushButton("Print on their own")
        b_out.setToolTip("Takes the picked parts out of their piece, so each prints on its own.")
        for w in (b_new, b_add, self.cb_piece, b_out):
            brow.addWidget(w)
        brow.addStretch(1)
        lay.addLayout(brow)
        brow2 = QHBoxLayout()
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
        b_ok = QPushButton("Use these pieces")
        b_ok.setDefault(True)
        b_ok.setToolTip("Keeps this plan: the next export prints these pieces.")
        b_cancel = QPushButton("Cancel")
        for w in (b_kind, b_clear, b_ren, b_turn, self.b_below, b_hide, b_showall):
            brow2.addWidget(w)
        brow2.addWidget(self.lbl, 1)
        brow2.addWidget(b_ok)
        brow2.addWidget(b_cancel)
        lay.addLayout(brow2)
        b_new.clicked.connect(self.new_piece)
        b_add.clicked.connect(self.add_to)
        b_out.clicked.connect(self.take_out)
        b_kind.clicked.connect(self.by_kind)
        b_clear.clicked.connect(self.clear_all)
        b_ren.clicked.connect(self.rename)
        b_ok.clicked.connect(self.accept)
        b_cancel.clicked.connect(self.reject)
        self.table.itemSelectionChanged.connect(self.canvas.update)
        try:
            self.table.viewport().installEventFilter(self)
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
        self.refresh()

    # ---- the plan
    def colour_of(self, i):
        p = self.keys.get(self.leaves[i][0])
        return piece_colour(self.pieces.index(p)) if p in self.pieces else LOOSE_COLOUR

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
                if mods & (Qt.ShiftModifier | Qt.ControlModifier):
                    try:
                        pos = ev.position().toPoint()
                    except Exception:
                        pos = ev.pos()
                    r = self.table.rowAt(pos.y())
                    if r >= 0:
                        self.pick_part(r, 'remove' if mods & Qt.ShiftModifier else 'add')
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
        name = self._unused_name()
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
        self.refresh(new)

    def refresh(self, current=None):
        from PySide6.QtWidgets import QTableWidgetItem
        from PySide6.QtGui import QColor, QBrush
        # pieces nothing's in any more go
        used = set(self.keys.values())
        self.pieces = [p for p in self.pieces if p in used]
        picked = self.picked_rows()
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.leaves))
        for i, (key, name, kind, _t) in enumerate(self.leaves):
            p = self.keys.get(key)
            col = self.colour_of(i)
            light = QColor(int(col[0] * 0.35 + 255 * 0.65), int(col[1] * 0.35 + 255 * 0.65),
                           int(col[2] * 0.35 + 255 * 0.65))
            for c, txt in enumerate((name, kind, p or "(on its own)")):
                it = QTableWidgetItem(("■ " + txt) if c == 2 and p else txt)
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
                it.setBackground(QBrush(light))
                if c == 2 and p:
                    it.setForeground(QBrush(QColor(*col).darker(130)))
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
                li = QListWidgetItem("%s  (%d part%s)" % (p_ or "On their own", n_, "" if n_ == 1 else "s"))
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
        m = QMenu(self)
        rows = [i for i in range(len(self.leaves)) if self.piece_of(i) == name]
        a_pick = m.addAction("Pick its parts")
        a_hide = m.addAction("Show" if name in self.hidden_pieces else "Hide")
        a_only = m.addAction("Show only this")
        a_ren = m.addAction("Rename...")
        a_ren.setEnabled(bool(name))
        a_free = m.addAction("Break up (each part on its own)")
        a_free.setEnabled(bool(name))

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

    def new_piece_and_hide(self, *_):
        """Makes a piece of the picked parts and hides it, so what's left is easier to get at."""
        rows = self.picked_rows()
        if not rows:
            self.lbl.setText("Pick some parts first.")
            return
        name = self._unused_name()
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
        return {'pieces': list(self.pieces), 'keys': dict(self.keys)}


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


INFO_TEXT = (
    "<b>3D Print Scaler</b><br><br>"
    "<b>Export scaled</b> writes the selection straight to a file in millimetres, every detail kept, "
    "however small - the best way for printing. Open it in your slicer as it is: it's already the "
    "right size.<br>"
    "<b>Scale a copy / Scale in place</b> scale inside IngeTrazo. IngeTrazo treats points closer than "
    "0.1 mm as one point, so at small scales tiny details (rivets, thin edges) can be lost - you're told "
    "how many faces were lost. Use Export for printing.<br><br>"
    "<b>Each group as a separate part</b>: every group with faces of its own becomes a separate part "
    "(a canopy: each column, bracket, beam, valance ...), laid out side by side on the bed, 'Gap "
    "between parts' apart. In a 3MF they're separate objects in one file, so the slicer shows them as "
    "separate items. Other file types save one file per part, in a new folder.<br>"
    "<b>Open in the slicer</b>: with the slicer's program set (the .exe file that starts it) "
    "all the files open in it at once; otherwise the file opens in whatever program Windows uses for "
    "that type of file.<br>"
    "<b>Keep this window open</b>: select the next part in the model and press the button again - "
    "the sizes follow what's selected.<br><br>"
    "<b>Checks</b>: every export mends hairline cracks and turns faces that point the wrong way (a solid "
    "inside out) so the slicer sees closed solids. With 'Warn of walls thinner than the nozzle' it also says "
    "which parts have walls, rods or letters thinner than your nozzle once scaled - make them thicker, or print "
    "them in resin. Press Check to see all this before exporting.<br><br>"
    "<b>Model's units</b>: IngeTrazo keeps every model in metres, so this is nearly always Metres. "
    "Only change it for a model that came in 1000 times too big.<br>"
    "<b>Small sizes</b>: under 1 mm is fine detail - good for resin, too small for a 0.4 mm FDM "
    "nozzle. Under 0.05 mm is smaller than a resin printer's pixel: check the units.")


# file types offered when saving: (label shown in the save box, extension, writer)
EXPORTS = [("STL - binary (*.stl)", ".stl", write_stl),
           ("3MF - for slicers (*.3mf)", ".3mf", write_3mf),
           ("OBJ - for 3D programs (*.obj)", ".obj", write_obj),
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
    def __init__(self, cur, size, unit_key, count_text, parent=None, tool=None, viewport=None):
        super().__init__(parent)
        self.setWindowTitle(PLUGIN_NAME)
        self.setModal(False)
        self.size = size
        self.tool = tool
        self.viewport = viewport
        self._sel_key = None
        self._last = ""
        lay = QVBoxLayout(self)
        form = QFormLayout()

        lbl_sel = QLabel(count_text)
        self.lbl_sel = lbl_sel

        self.scales = load_scale_settings()
        self.cb_scale = QComboBox()
        self.cb_scale.setToolTip("The scale to print at: model railway scales, your own saved scales (marked *) "
                                 "and plain ones. The one marked 'default' is what the window opens on.")
        self.fill_scales()
        want = self.scales['default'] or cur['denominator']
        self.select_scale(want)

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

        # export: many parts, opening in the slicer, staying open
        self.cb_sep = QCheckBox("Each group as a separate part (laid out on the bed)")
        self.cb_sep.setChecked(bool(cur.get('separate')))
        self.cb_sep.setToolTip("Every group with faces of its own becomes a separate part - a canopy gives "
                               "one for each column, bracket, beam and valance - laid out side by side on the "
                               "bed. A 3MF keeps them as separate items in one file; other file types save "
                               "one file per part.")
        self.sp_gap = QDoubleSpinBox()
        self.sp_gap.setRange(0.5, 200.0)
        self.sp_gap.setDecimals(1)
        self.sp_gap.setSuffix(" mm")
        self.sp_gap.setValue(float(cur.get('part_gap', 5.0)))
        self.sp_gap.setToolTip("The space left between the parts on the bed (printed mm). The slicer keeps this "
                               "layout - unless you press its Arrange button, which uses its own spacing.")
        self.cb_open = QCheckBox("Open in the slicer after saving")
        self.cb_open.setChecked(bool(cur.get('open_after')))
        self.cb_open.setToolTip("Opens the file as soon as it's saved: in the slicer program below, or (if "
                                "that's empty) in whatever program Windows opens that type of file with.")
        self.ed_slicer = QLineEdit(self.scales.get('slicer', ''))
        self.ed_slicer.setPlaceholderText("(Windows' default program)")
        self.ed_slicer.setToolTip("Your slicer's program (the .exe file that starts it, usually somewhere in "
                                  "C:\\Program Files). With it set, separate files all open in it at once. "
                                  "Empty = the file opens in Windows' default program for it.")
        b_browse = QPushButton("...")
        b_browse.setToolTip("Find your slicer's program.")
        b_browse.setMaximumWidth(32)
        b_browse.clicked.connect(self.browse_slicer)
        self.slicer_row = QHBoxLayout()
        self.slicer_row.addWidget(self.ed_slicer, 1)
        self.slicer_row.addWidget(b_browse)
        self.b_browse = b_browse
        self.cb_flat = QCheckBox("Lay each part flat (biggest flat face down)")
        self.cb_flat.setChecked(bool(cur.get('lay_flat', True)))
        self.cb_flat.setToolTip("Turns each part so its biggest flat face lies on the bed - a sheet on its back, "
                                "a valance or panel flat - and long side along X, the way you'd print it. "
                                "Untick to keep it standing the way it is in the model.")
        self.cb_thin = QCheckBox("Warn of walls thinner than the nozzle")
        self.cb_thin.setChecked(bool(cur.get('warn_thin', True)))
        self.cb_thin.setToolTip("On export (and Check), looks for walls, rods and letters thinner than your "
                                "nozzle once scaled - the slicer may leave them out - and says which parts and "
                                "how thin. Untick for a resin printer, or to skip it.")
        self.sp_nozzle = QDoubleSpinBox()
        self.sp_nozzle.setRange(0.05, 2.0)
        self.sp_nozzle.setDecimals(2)
        self.sp_nozzle.setSingleStep(0.05)
        self.sp_nozzle.setSuffix(" mm")
        self.sp_nozzle.setValue(float(cur.get('nozzle', 0.4)))
        self.sp_nozzle.setToolTip("Your printer's nozzle width (0.4 mm usually). Walls thinner than this get a "
                                  "warning. For resin, try about 0.2 mm.")
        self.cb_thin.toggled.connect(self.sp_nozzle.setEnabled)
        self.sp_nozzle.setEnabled(self.cb_thin.isChecked())
        self.cb_keep = QCheckBox("Keep this window open (for scaling lots of parts)")
        self.cb_keep.setChecked(bool(cur.get('keep_open')))
        self.cb_keep.setToolTip("The window stays open after each export or scale: select the next part in "
                                "the model and press the button again. The sizes follow what's selected.")
        self.lbl_report = QLabel()
        self.lbl_report.setWordWrap(True)
        self.lbl_report.setVisible(False)

        form.addRow(lbl_sel)
        form.addRow("Scale:", self.cb_scale)
        form.addRow("   Custom scale:", self.sp_custom)
        srow = QHBoxLayout()
        b_save = QPushButton("Save scale...")
        b_save.setToolTip("Saves the scale shown as one of your own, under a name you choose "
                          "(for example 'My OO buildings 1:76.2').")
        self.b_del = QPushButton("Delete")
        self.b_del.setToolTip("Deletes the selected scale from your own scales.")
        b_def = QPushButton("Make default")
        b_def.setToolTip("The window will open on this scale every time.")
        for b in (b_save, self.b_del, b_def):
            srow.addWidget(b)
        srow.addStretch(1)
        form.addRow("", srow)
        b_save.clicked.connect(self.save_scale)
        self.b_del.clicked.connect(self.delete_scale)
        b_def.clicked.connect(self.make_default)
        form.addRow("Model's units:", self.cb_unit)
        form.addRow("Scale about:", self.cb_pivot)
        form.addRow("Mode:", self.cb_mode)
        form.addRow(self.cb_bed)
        form.addRow("   Bed size:", bed_row)
        form.addRow(self.cb_sep)
        self.lab_gap = QLabel("   Gap between parts:")
        self.lab_gap.setToolTip(self.sp_gap.toolTip())
        form.addRow(self.lab_gap, self.sp_gap)
        self.cb_depth = QComboBox()
        for lab_, k_ in (("Every group (smallest pieces)", 0), ("Groups 1 level in", 1), ("Groups 2 levels in", 2),
                         ("Groups 3 levels in", 3), ("Groups 4 levels in", 4)):
            self.cb_depth.addItem(lab_, k_)
            if k_ == int(cur.get('split_depth', 0) or 0):
                self.cb_depth.setCurrentIndex(self.cb_depth.count() - 1)
        self.cb_depth.setToolTip(
            "Which groups become the pieces. Every group: each group with faces is a piece (a canopy: every "
            "column, bracket and board). 'n levels in': each group that many levels inside what you selected is "
            "one piece with everything in it - so open a group, group together the bits you'll print as one, "
            "and they come out as one piece while the rest stay separate. For a canopy, '2 levels in' gives a "
            "piece per column, bracket ... with your own groups kept whole; '1 level in' gives one piece per "
            "kind (all the columns together ...).")
        self.lab_depth = QLabel("   Pieces are:")
        self.lab_depth.setToolTip(self.cb_depth.toolTip())
        form.addRow(self.lab_depth, self.cb_depth)
        self.plan = PrintScalerTool._plan
        self.b_plan = QPushButton("Plan the pieces...")
        self.b_plan.setToolTip("Shows every part of what's selected, in a list and a picture. Pick parts and put "
                               "them into pieces - each piece prints as one and gets its own colour. When "
                               "there's a plan, it decides the pieces (instead of 'Pieces are').")
        self.b_plan.clicked.connect(self.plan_pieces)
        self.b_unplan = QPushButton("Forget plan")
        self.b_unplan.setToolTip("Goes back to 'Pieces are' to decide the pieces.")
        self.b_unplan.clicked.connect(self.forget_plan)
        prow_ = QHBoxLayout()
        prow_.addWidget(self.b_plan)
        prow_.addWidget(self.b_unplan)
        prow_.addStretch(1)
        form.addRow("", prow_)
        form.addRow(self.cb_open)
        self.lab_slicer = QLabel("   Slicer program:")
        self.lab_slicer.setToolTip(self.ed_slicer.toolTip())
        form.addRow(self.lab_slicer, self.slicer_row)
        form.addRow(self.cb_flat)
        nrow = QHBoxLayout()
        nrow.addWidget(self.cb_thin)
        nrow.addWidget(self.sp_nozzle)
        nrow.addStretch(1)
        form.addRow(nrow)
        form.addRow(self.cb_keep)
        form.addRow(self.lbl_info)
        form.addRow(self.lbl_report)
        lay.addLayout(form)

        brow = QHBoxLayout()
        b_defaults = QPushButton("Save as default")
        b_defaults.setToolTip("Saves everything in this window (mode, bed size, separate parts, gap, slicer, lay "
                              "flat, keep open ...) as the settings the window opens with every time. The scale's "
                              "own default is set with 'Make default' up by the scale.")
        b_defaults.clicked.connect(self.save_defaults)
        b_info = QPushButton("Info")
        b_info.setToolTip("What each setting does, the warnings explained, and what happened last time.")
        b_check = QPushButton("Check")
        b_check.setToolTip("Checks what's selected for printing problems without saving: faces pointing the "
                           "wrong way, cracks and gaps, walls thinner than the nozzle, solids overlapping. "
                           "Export fixes what it can (faces, cracks) by itself.")
        b_check.clicked.connect(self.check_now)
        self.b_go = QPushButton("Export...")
        self.b_go.setDefault(True)
        self.b_go.setToolTip("Exports (or scales) what's selected now.")
        b_close = QPushButton("Close")
        brow.addWidget(b_info)
        brow.addWidget(b_defaults)
        brow.addStretch(1)
        brow.addWidget(b_check)
        brow.addWidget(self.b_go)
        brow.addWidget(b_close)
        lay.addLayout(brow)
        b_info.clicked.connect(self.show_info)
        self.b_go.clicked.connect(self.go)
        b_close.clicked.connect(self.close)

        for w in (self.cb_scale, self.cb_unit, self.cb_bed, self.cb_mode, self.cb_sep, self.cb_open, self.cb_depth):
            sig = w.currentIndexChanged if isinstance(w, QComboBox) else w.toggled
            sig.connect(self.update_info)
        self.sp_custom.valueChanged.connect(self.update_info)
        for s in self.bed:
            s.valueChanged.connect(self.update_info)
        self.update_info()
        # the sizes follow the selection while the window is open
        try:
            from PySide6.QtCore import QTimer
            self._timer = QTimer(self)
            self._timer.timeout.connect(self.watch_selection)
            self._timer.start(800)
        except Exception:
            self._timer = None

    # ---- the selection, the button, info
    def selection(self):
        scene = getattr(self.viewport, 'scene', None)
        return list(getattr(scene, 'selection', None) or [])

    def watch_selection(self):
        ents = self.selection()
        key = tuple(id(e) for e in ents)
        if key == self._sel_key:
            return
        self._sel_key = key
        self.size, text = selection_size(ents)
        self.lbl_sel.setText(text)
        self._parts = None
        self.update_info()

    def browse_slicer(self, *_):
        from PySide6.QtWidgets import QFileDialog
        start = self.ed_slicer.text() or "C:\\Program Files"
        res = QFileDialog.getOpenFileName(self, "Your slicer's program", start, "Programs (*.exe);;All files (*)")
        path = res[0] if isinstance(res, (tuple, list)) else res
        if path:
            self.ed_slicer.setText(path)

    def save_defaults(self, *_):
        v = self.get_values()
        keep = {k: v[k] for k in DEFAULTS if k in v and k not in ('denominator', 'unit')}
        self.scales['settings'] = keep
        self.scales['slicer'] = self.ed_slicer.text().strip()
        save_scale_settings(self.scales)
        self.report("Saved as your default settings - the window will open like this every time.")

    def report(self, text, bad=False):
        self._last = text
        self.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if bad else "#2e7d32"))
        self.lbl_report.setText(text)
        self.lbl_report.setVisible(True)

    def plan_pieces(self, *_):
        ents = self.selection()
        leaves = piece_leaves(ents)
        if not leaves:
            self.report("Select the object (a group, or its faces) first.", bad=True)
            return
        pdlg = PiecesDialog(self, leaves, self.plan)
        try:
            eddy_window(pdlg, PLUGIN_NAME + " - pieces", EDDY_TIPS, place=True)
        except Exception:
            pass
        if pdlg.exec():
            self.plan = pdlg.plan()
            PrintScalerTool._plan = self.plan
            self.update_info()

    def forget_plan(self, *_):
        self.plan = None
        PrintScalerTool._plan = None
        self.update_info()

    def show_info(self, *_):
        txt = INFO_TEXT
        if self._last:
            txt += "<br><br><b>Last time:</b><br>" + self._last.replace("\n", "<br>")
        box = QMessageBox(self)
        box.setWindowTitle(PLUGIN_NAME + " - Info")
        box.setText(txt)
        box.exec()

    def check_now(self, *_):
        ents = self.selection()
        if not ents:
            self.report("Select the object (a group, or its faces) first.", bad=True)
            return
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            QApplication.setOverrideCursor(Qt.WaitCursor)
        except Exception:
            pass
        try:
            text, bad = self.tool.check_selection(ents, self.get_values())
        except Exception as e:
            text, bad = "Couldn't check it: %s" % e, True
        finally:
            try:
                QApplication.restoreOverrideCursor()
            except Exception:
                pass
        self.report(text, bad)

    def go(self, *_):
        ents = self.selection()
        if not ents:
            self.report("Select the object (a group, or its faces) first.", bad=True)
            return
        vals = self.get_values()
        PrintScalerTool._saved = dict(vals)
        if self.ed_slicer.text().strip() != self.scales.get('slicer', ''):
            self.scales['slicer'] = self.ed_slicer.text().strip()
            save_scale_settings(self.scales)
        res = self.tool.apply_scale(self.viewport, ents, vals) if self.tool else None
        if res is None:                     # cancelled (no file name)
            return
        text, bad = res
        if vals['keep_open']:
            self.report(text, bad)
            self._sel_key = None            # a scale in place changes the size: look again
            self.watch_selection()
            return
        self.close()
        if bad:
            QMessageBox.warning(self.viewport, PLUGIN_NAME, text)
        else:
            try:
                self.viewport.flash_status("%s: %s" % (PLUGIN_NAME, text.split("\n")[0]), 8000)
            except Exception:
                print("%s: %s" % (PLUGIN_NAME, text))

    def fill_scales(self):
        """Model railway scales, your own, the plain ones, then Custom."""
        dflt = self.scales.get('default')
        self.cb_scale.blockSignals(True)
        self.cb_scale.clear()
        self._mine_rows = set()
        self._mine_names = {}

        def label(text, n):
            return text + ("   (default)" if dflt and abs(n - dflt) < 1e-9 else "")
        for name, n in self.scales['mine']:
            self.cb_scale.addItem(label("* %s  1:%g" % (name, n), n), float(n))
            self._mine_rows.add(self.cb_scale.count() - 1)
            self._mine_names[self.cb_scale.count() - 1] = name
        for name, n in RAIL_SCALES:
            self.cb_scale.addItem(label(name, n), float(n))
        for d in SCALE_PRESETS:
            self.cb_scale.addItem(label("1 : %d" % d, float(d)), float(d))
        self.cb_scale.addItem("Custom...", None)
        self.cb_scale.blockSignals(False)

    def select_scale(self, n):
        idx = self.cb_scale.count() - 1                    # Custom, with the number in the box
        for i in range(self.cb_scale.count() - 1):
            if self.cb_scale.itemData(i) is not None and abs(self.cb_scale.itemData(i) - n) < 1e-9:
                idx = i
                break
        self.cb_scale.setCurrentIndex(idx)
        try:
            self.sp_custom.setValue(n)
        except Exception:
            pass

    def save_scale(self, *_):
        from PySide6.QtWidgets import QInputDialog
        n = self.denominator()
        name, ok = QInputDialog.getText(self, PLUGIN_NAME, "A name for 1 : %g:" % n, text="My scale 1:%g" % n)
        if not ok or not str(name).strip():
            return
        name = str(name).strip()
        self.scales['mine'] = [(a, b) for a, b in self.scales['mine'] if a != name] + [(name, n)]
        save_scale_settings(self.scales)
        self.fill_scales()
        for i, nm in self._mine_names.items():
            if nm == name:
                self.cb_scale.setCurrentIndex(i)
        self.update_info()

    def delete_scale(self, *_):
        i = self.cb_scale.currentIndex()
        if i not in self._mine_rows:
            QMessageBox.information(self, PLUGIN_NAME, "Only your own scales (marked *) can be deleted.")
            return
        n = self.cb_scale.itemData(i)
        name = self._mine_names.get(i)
        self.scales['mine'] = [(a, b) for a, b in self.scales['mine'] if a != name]
        save_scale_settings(self.scales)
        self.fill_scales()
        self.select_scale(n)
        self.update_info()

    def make_default(self, *_):
        n = self.denominator()
        self.scales['default'] = n
        save_scale_settings(self.scales)
        self.fill_scales()
        self.select_scale(n)
        self.update_info()

    def denominator(self):
        d = self.cb_scale.currentData()
        return d if d else self.sp_custom.value()

    def update_info(self, *_):
        custom = self.cb_scale.currentData() is None
        self.sp_custom.setEnabled(custom)
        try:
            self.b_del.setEnabled(self.cb_scale.currentIndex() in self._mine_rows)
        except Exception:
            pass
        if not custom:
            # show the chosen scale's number, so switching to Custom starts from it
            self.sp_custom.blockSignals(True)
            self.sp_custom.setValue(self.cb_scale.currentData())
            self.sp_custom.blockSignals(False)
        for s in self.bed:
            s.setEnabled(self.cb_bed.isChecked())
        export = self.cb_mode.currentData() == 'stl'
        for w in (self.cb_sep, self.cb_open, self.cb_flat):
            w.setEnabled(export)
        for w in (self.sp_gap, self.lab_gap):
            w.setEnabled(export and self.cb_sep.isChecked())
        planned = bool(self.plan and self.plan.get('pieces'))
        for w in (self.cb_depth, self.lab_depth):
            w.setEnabled(export and self.cb_sep.isChecked() and not planned)
        self.b_plan.setEnabled(export and self.cb_sep.isChecked())
        self.b_unplan.setEnabled(export and self.cb_sep.isChecked() and planned)
        for w in (self.ed_slicer, self.b_browse, self.lab_slicer):
            w.setEnabled(export and self.cb_open.isChecked())
        self.b_go.setText("Export..." if export else "Scale")
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
        if export and self.cb_sep.isChecked():
            try:
                if self.plan and self.plan.get('pieces'):
                    lv = piece_leaves(self.selection(), with_tris=False)
                    keys = self.plan.get('keys', {})
                    used = {keys[k] for k, _a, _b, _c in lv if keys.get(k) in self.plan['pieces']}
                    alone = sum(1 for k, _a, _b, _c in lv if keys.get(k) not in self.plan['pieces'])
                    txt += "<br>Planned: %d piece%s + %d part%s on their own." % (
                        len(used), "" if len(used) == 1 else "s", alone, "" if alone == 1 else "s")
                else:
                    n = count_parts(self.selection(), self.cb_depth.currentData() or 0)
                    txt += "<br>%d separate part%s." % (n, "" if n == 1 else "s")
            except Exception:
                pass
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
            'separate': self.cb_sep.isChecked(), 'part_gap': self.sp_gap.value(),
            'split_depth': int(self.cb_depth.currentData() or 0), 'plan': self.plan,
            'open_after': self.cb_open.isChecked(), 'slicer': self.ed_slicer.text().strip(),
            'keep_open': self.cb_keep.isChecked(), 'lay_flat': self.cb_flat.isChecked(),
            'warn_thin': self.cb_thin.isChecked(), 'nozzle': self.sp_nozzle.value(),
        }


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
# Tool
# ---------------------------------------------------------------------------
class PrintScalerTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+P"
    description = "Scale the selected object to a chosen scale (1:50, 1:100 ...) for 3D printing."

    _saved = None
    _last_export = None
    _dialog = None
    _plan = None

    def on_activate(self, viewport):
        dlg = PrintScalerTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.viewport = viewport
                    dlg.raise_()
                    dlg.activateWindow()
                    return
            except Exception:
                pass
        scene = getattr(viewport, 'scene', None)
        entities = list(getattr(scene, 'selection', None) or [])
        size, text = selection_size(entities)

        cur = dict(DEFAULTS)
        try:
            cur.update({k: v for k, v in load_scale_settings().get('settings', {}).items() if k in DEFAULTS})
        except Exception:
            pass
        if PrintScalerTool._saved:
            cur.update(PrintScalerTool._saved)
        # IngeTrazo keeps every model in metres, whatever units it shows, so start from metres
        # each time; millimetres is only for a model that came in 1000 times too big (an STL in mm
        # imported as metres)
        unit_key = guess_unit(size) if max(size) > 0 else "m"
        cur['unit'] = None

        dialog = ScaleDialog(cur, size, unit_key, text, viewport, tool=self, viewport=viewport)
        dialog._sel_key = tuple(id(e) for e in entities)
        PrintScalerTool._dialog = dialog

        def closed(*_):
            PrintScalerTool._dialog = None
            try:
                if dialog._timer is not None:
                    dialog._timer.stop()
            except Exception:
                pass
        dialog.finished.connect(closed)
        eddy_window(dialog, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dialog.show()

    def on_deactivate(self, viewport):
        pass

    def apply_scale(self, viewport, entities, p):
        s = 1.0 / p['denominator']
        if p['mode'] == 'stl':
            return self._export_stl(viewport, entities, p)  # (message, warning) or None

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
            return "Scaling failed: %s" % e, True
        viewport.notify_scene_changed()
        if report.get('lost'):
            return ("The copy at 1:%g is missing %d of %d faces: IngeTrazo treats points closer than 0.1 mm as "
                    "one point, so details that small can't be kept in the model. For printing, use 'Export "
                    "scaled' instead - every detail is kept." % (
                        p['denominator'], report['lost'], report['lost'] + report['made'])), True
        return "Scaled %s to 1:%g." % ("a copy" if p['mode'] == 'copy' else "it", p['denominator']), False

    # ------------------------------------------------------------------ STL
    def _export_stl(self, viewport, entities, p):
        """Scale the selection outside the model, at full precision, and write it in mm - no
        detail is lost, however small, and the original isn't touched. Returns (message, warning)
        or None if the save was cancelled."""
        from PySide6.QtWidgets import QFileDialog
        unit_mm = dict((u[2], u[1]) for u in UNITS).get(p.get('unit') or 'm', 1000.0)
        k = unit_mm / p['denominator']                      # model units -> printed mm
        if p.get('separate'):
            plan = p.get('plan')
            if plan and plan.get('pieces'):
                raw = plan_parts(piece_leaves(entities), plan)
            else:
                raw = split_parts(entities, int(p.get('split_depth', 0) or 0))
            parts = [(n, [tuple((c[0] * k, c[1] * k, c[2] * k) for c in t) for t in tr]) for n, tr in raw]
            if not parts:
                return "Nothing to export: select the object (a group, or its faces) first.", True
            mended, left = 0, 0
            fixed_parts = []
            for n_, tr in parts:
                tr, f_, l_ = mend_cracks(tr)
                mended += f_ - l_
                left += l_
                fixed_parts.append((n_, tr))
            parts, checks, thin_warn = check_parts(fixed_parts, p['nozzle'] if p.get('warn_thin') else 0.0)
            if p.get('lay_flat', True):
                parts = [(n, lay_flat(tr)) for n, tr in parts]
            row = p['bed_x'] if p.get('check_bed') else max(
                150.0, 1.4 * sum((max(c[0] for t in tr for c in t) - min(c[0] for t in tr for c in t)) *
                                 (max(c[1] for t in tr for c in t) - min(c[1] for t in tr for c in t))
                                 for _, tr in parts) ** 0.5)
            parts, (sx, sy, sz) = lay_out(parts, row, max(0.5, p.get('part_gap', 5.0)))
            tris = [t for _, tr in parts for t in tr]
        else:
            loops = world_loops(entities)
            if not loops:
                return "Select the object (a group or its faces) first.", True
            tris = []
            for outer, holes, f in loops:
                for t in face_triangles(f):
                    q = [vertex_to_vector3d(v) if not isinstance(v, QVector3D) else v for v in t]
                    if any(x is None for x in q):
                        continue
                    tris.append(tuple((x.x() * k, x.y() * k, x.z() * k) for x in q))
            if not tris:
                return "Those faces couldn't be turned into triangles.", True
            tris, f_, left = mend_cracks(tris)
            mended = f_ - left
            cp_, checks, thin_warn = check_parts([("The model", tris)], p['nozzle'] if p.get('warn_thin') else 0.0)
            tris = cp_[0][1]
            if p.get('lay_flat', True):
                tris = lay_flat(tris)
            # on the print bed: centred, standing on z = 0
            xs = [c[0] for t in tris for c in t]
            ys = [c[1] for t in tris for c in t]
            zs = [c[2] for t in tris for c in t]
            ox, oy, oz = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)
            tris = [tuple((c[0] - ox, c[1] - oy, c[2] - oz) for c in t) for t in tris]
            sx, sy, sz = max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)
            parts = None
        name = "scaled"
        for e in entities:
            if getattr(e, 'name', None):
                name = str(e.name)
                break
        safe = "".join(ch for ch in name if ch not in '\\/:*?"<>|').strip() or "scaled"
        # the file type you used last time comes first (3MF for separate parts)
        last = PrintScalerTool._last_export if PrintScalerTool._last_export in [e[0] for e in EXPORTS] \
            else EXPORTS[0][0]
        if parts and len(parts) > 1 and PrintScalerTool._last_export is None:
            last = EXPORTS[1][0]
        start = os.path.join(os.path.expanduser("~"), "Downloads", "%s 1-%g%s" % (
            safe, p['denominator'], dict((e[0], e[1]) for e in EXPORTS)[last]))
        res = QFileDialog.getSaveFileName(viewport, "Save the scaled model", start,
                                          ";;".join(e[0] for e in EXPORTS), last)
        path, chosen = (res[0], res[1]) if isinstance(res, (tuple, list)) and len(res) > 1 else (res, last)
        if not path:
            return None
        fmt = next((e for e in EXPORTS if e[0] == chosen), None)
        if fmt is None or not path.lower().endswith(fmt[1]):
            # typed an extension of their own: go by that
            fmt = next((e for e in EXPORTS if path.lower().endswith(e[1])), fmt or EXPORTS[0])
        if not path.lower().endswith(fmt[1]):
            path += fmt[1]
        PrintScalerTool._last_export = fmt[0]
        files = [path]
        try:
            if parts and len(parts) > 1 and fmt[1] == '.3mf':
                # a 3MF is placed in the bed's own coordinates: the layout goes in the middle of the bed
                bx, by = p.get('bed_x', 220.0) / 2.0, p.get('bed_y', 220.0) / 2.0
                write_3mf_parts(path, [(n, [tuple((c[0] + bx, c[1] + by, c[2]) for c in t) for t in tr])
                                       for n, tr in parts])
                what = "%d parts (separate objects in one 3MF)" % len(parts)
            elif parts and len(parts) > 1:
                # one file per part, in a folder named after the file
                folder = path[:-len(fmt[1])]
                os.makedirs(folder, exist_ok=True)
                files, used = [], set()
                for pn, ptris in parts:
                    fn = "".join(ch for ch in pn if ch not in '\\/:*?"<>|').strip() or "part"
                    base, i = fn, 2
                    while fn.lower() in used:
                        fn, i = "%s %d" % (base, i), i + 1
                    used.add(fn.lower())
                    fp = os.path.join(folder, fn + fmt[1])
                    fmt[2](fp, ptris, "%s at 1:%g" % (pn, p['denominator']))
                    files.append(fp)
                path = folder
                what = "%d parts, one file each, in the folder" % len(parts)
            else:
                fmt[2](path, tris, "%s at 1:%g" % (name, p['denominator']))
                what = "%d triangles" % len(tris)
        except Exception as e:
            return "Could not write the file: %s" % e, True
        msg = "Saved %s at 1:%g, %.1f x %.1f x %.1f mm:\n%s" % (what, p['denominator'], sx, sy, sz, path)
        if mended:
            msg += "\nMended %d hairline crack%s (open edges) on the way." % (mended, "" if mended == 1 else "s")
        for ln in checks:
            msg += "\n" + ln
        if left:
            msg += ("\n%d open edge%s left - the model itself has a gap there; the slicer's Fix (or Netfabb) "
                    "will close it." % (left, "" if left == 1 else "s"))
        if p.get('open_after'):
            msg += "\n" + open_in_slicer(files, p.get('slicer', ''))
        return msg, bool(thin_warn)

    def check_selection(self, entities, p):
        """The checks the export does, without saving: (report, anything to warn about)."""
        unit_mm = dict((u[2], u[1]) for u in UNITS).get(p.get('unit') or 'm', 1000.0)
        k = unit_mm / p['denominator']
        if p.get('separate'):
            plan = p.get('plan')
            if plan and plan.get('pieces'):
                raw = plan_parts(piece_leaves(entities), plan)
            else:
                raw = split_parts(entities, int(p.get('split_depth', 0) or 0))
        else:
            raw = [("The model", [t for _, tr in split_parts(entities, 0) for t in tr])]
        parts = [(n, [tuple((c[0] * k, c[1] * k, c[2] * k) for c in t) for t in tr]) for n, tr in raw if tr]
        if not parts:
            return "Nothing to check: select the object (a group, or its faces) first.", True
        mended = left = 0
        fixed = []
        for n_, tr in parts:
            tr, f_, l_ = mend_cracks(tr)
            mended += f_ - l_
            left += l_
            fixed.append((n_, tr))
        nz = p['nozzle'] if p.get('warn_thin') else 0.0
        _, lines, warn = check_parts(fixed, nz)
        out = ["Checked %d part%s at 1:%g:" % (len(parts), "" if len(parts) == 1 else "s", p['denominator'])]
        if mended:
            out.append("%d hairline crack%s - mended on export." % (mended, "" if mended == 1 else "s"))
        out += [ln.replace("Turned", "Will turn") for ln in lines]
        if left:
            out.append("%d open edge%s - a real gap in the model; the slicer's Fix will close it." % (
                left, "" if left == 1 else "s"))
            warn = True
        if len(out) == 1:
            out.append("No problems found%s." % (
                " - every wall is at least %.2f mm" % nz if nz > 0 else ""))
        return "\n".join(out), warn

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
