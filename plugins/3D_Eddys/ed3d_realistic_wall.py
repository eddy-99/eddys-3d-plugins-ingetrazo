# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Realistic Wall for IngeTrazo
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
3D Realistic Wall - a real stone (or brick) face from a picture of a wall
Pick the walls (tick them in the list, or click them in the picture of the building), pick a
picture of a wall from your pictures folder, and it opens your 3D program with the walls carved: light parts of the picture stand out, dark parts (the joints) sink in.
The finished walls can then be brought back into the model.
Sizes in real-world mm - Scale Studio takes it down to your model scale.
Version 1.0: first version (with 'Hide the repeats', so a small picture doesn't show its repeats).
Version 1.1: a Realistic Wall panel in the 3D program (N sidebar) to change the settings there and
carve again, and to send the walls back with any changes made there; the Sizes page shows the detail
each wall really gets, and 'Most points per wall' can be raised.
Version 1.2: K Crisp edges (sharper joints); a quick 1 m test patch; picking a colour photo uses its
height picture from the same folder; the slow cut is no longer used by itself on a big wall; the
Sizes page shows how fine the detail comes out on the print; starts at detail 300.
Version 1.3: walls are joined up into closed solids before cutting (arches meeting straight walls), so
the quick cut works and a whole wall takes seconds; flat shading in the 3D program (no streaks).
Version 1.4: the colour photo shown on the walls in the 3D program, lined up with the carving (just for
looking - 'Show the colours' turns it on and off).
Version 1.5: walls come back into the model properly - the tilted bits of the stones come back as
triangles (IngeTrazo wants flat faces), and the plain parts as whole faces, not fans of triangles.
Version 1.6: settings changed in the 3D program are kept - its file is saved on Re-carve and Send, and
'Bring the walls back' takes them into this window for next time.
Version 1.7: a choice for the plain walls when the carved ones come back - leave them, hide them, or
replace them (the carved wall goes in the plain wall's place in the building, with its name).
"""

import os
import json
import math
import time
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtCore import Qt, QPointF, QRectF, QSize, QTimer
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QDoubleSpinBox, QSpinBox, QCheckBox, QComboBox,
    QMessageBox, QPushButton, QInputDialog, QListWidget, QListWidgetItem, QLineEdit, QLabel, QWidget,
    QTabWidget, QFileDialog
)

PLUGIN_NAME = "3D Realistic Wall"
VERSION = "1.7"             # shown in the window title, so you can tell which file is loaded

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_realistic_wall.json")
PRESET_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Realistic Wall")
WORK_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Realistic Walls")
PICTURE_TYPES = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".tga", ".exr", ".webp")
DONE_KEY = "ed3d_realistic_wall"      # set on a wall group brought back with its stone face

# sizes in real-world mm
SIZE_KEYS = ('depth', 'tile_w', 'tile_h', 'off_x', 'off_y')
DEFAULTS = {
    'depth': 30.0, 'tile_w': 2500.0, 'tile_h': 2500.0, 'detail': 300, 'blur': 0, 'light_out': True,
    'off_x': 0.0, 'off_y': 0.0, 'mix': 60, 'seed': 1, 'max_pts': 1000, 'crisp': 50,
}
BUILTIN_PRESETS = {
    "Stone wall (2 x 2 m picture)": dict(DEFAULTS, tile_w=2000.0, tile_h=2000.0),
    "Rough stone (deep joints)": dict(DEFAULTS, depth=50.0, blur=1, crisp=30),
    "Brick wall (2.5 x 2.5 m picture)": dict(DEFAULTS, depth=25.0, detail=450, max_pts=2000, mix=30, crisp=60),
    "Brick wall (1 x 1 m picture)": dict(DEFAULTS, depth=12.0, tile_w=1000.0, tile_h=1000.0, detail=200,
                                         mix=30, crisp=60),
    "Dressed stone (shallow)": dict(DEFAULTS, depth=15.0),
}
# what the window remembers between times (besides the sizes)
KEEP = {'folder': '', 'picture': '', 'blender': '', 'work_dir': WORK_DIR, 'keep_blend': True,
        'patch': False, 'allow_slow': False, 'colour': True, 'back_mode': 'hide',
        'inside_walls': False, 'inside_faces': False, 'tab': 0, 'remember_tab': True, 'last_preset': None,
        'preset_order': [], 'last_job': ''}


def load_settings():
    d = dict(DEFAULTS)
    d.update(KEEP)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            got = json.load(f)
        if isinstance(got, dict):
            d.update({k: v for k, v in got.items() if k in d})
    except Exception:
        pass
    return d


def save_settings(**kw):
    d = load_settings()
    d.update(kw)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)
    except Exception:
        pass


def _safe_name(name):
    return "".join(c if c.isalnum() or c in " -_()" else "_" for c in name).strip() or "preset"


def load_presets():
    out = {}
    try:
        for fn in sorted(os.listdir(PRESET_DIR)):
            if fn.lower().endswith(".json"):
                try:
                    with open(os.path.join(PRESET_DIR, fn), "r", encoding="utf-8") as f:
                        d = json.load(f)
                    if isinstance(d, dict):
                        out[d.get('name') or fn[:-5]] = d
                except Exception:
                    pass
    except Exception:
        pass
    return out


def save_preset_file(name, values):
    os.makedirs(PRESET_DIR, exist_ok=True)
    d = {'name': name}
    d.update({k: values[k] for k in DEFAULTS if k in values})
    with open(os.path.join(PRESET_DIR, _safe_name(name) + ".json"), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)


def delete_preset_file(name):
    path = os.path.join(PRESET_DIR, _safe_name(name) + ".json")
    if os.path.exists(path):
        os.remove(path)


# ---------------------------------------------------------------------------
# Finding Blender
# ---------------------------------------------------------------------------
def _version_key(path):
    import re
    nums = re.findall(r"\d+", os.path.basename(os.path.dirname(path)))
    return tuple(int(n) for n in nums[:3]) or (0,)


def _main_exe(prog):
    """Blender's launcher hands over to blender.exe: start that one."""
    if prog and os.path.basename(prog).lower().startswith("blender"):
        main = os.path.join(os.path.dirname(prog), "blender.exe" if os.name == 'nt' else "blender")
        if os.path.isfile(main):
            return main
    return prog


def find_blender(saved=""):
    """The Blender to open: the one set in the window, else the one 3D Pieces In was set to, else
    the newest one installed in the usual places. '' if none is found."""
    if saved and os.path.isfile(saved):
        return _main_exe(saved)
    try:
        with open(os.path.join(os.path.expanduser("~"), ".ingetrazo_pieces_in.json"), "r", encoding="utf-8") as f:
            p = json.load(f).get('open_prog', '')
        if p and os.path.isfile(p) and "blender" in os.path.basename(p).lower():
            return _main_exe(p)
    except Exception:
        pass
    found = []
    bases = [os.environ.get(k, "") for k in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432")]
    bases.append(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"))
    for base in [b for b in bases if b]:
        bf = os.path.join(base, "Blender Foundation")
        try:
            for d in os.listdir(bf):
                exe = os.path.join(bf, d, "blender.exe")
                if os.path.isfile(exe):
                    found.append(exe)
        except Exception:
            pass
    found.sort(key=_version_key, reverse=True)
    steam = os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Steam", "steamapps", "common", "Blender",
                         "blender.exe")
    if os.path.isfile(steam):
        found.append(steam)
    if not found:
        try:
            import shutil
            w = shutil.which("blender")
            if w:
                found.append(w)
        except Exception:
            pass
    return found[0] if found else ""


# ---------------------------------------------------------------------------
# Finding the walls (the same way 3D Brick & Block Studio does)
# ---------------------------------------------------------------------------
_NOT_WALLS = ("floor", "ledge", "plate", "roof", "chimney", "subframe", "glazing", "gutter", "pipe",
              "tile", "walling", "quoin", "coping", "backing", "rubble", "heads and sills", "brick",
              "stone work", "canopy", "fence", "plank", "step", "sill", "frame", "sash", "post",
              "lintel", "brace", "stud", "rail", "rafter", "purlin", "truss", "nogging", "fascia",
              "barge", "soffit", "finial", "core", "pot", "flaunching")
_NEVER_WALLS = ("subframe", "chimney", "barge", "fascia", "soffit", "finial", "gutter", "downpipe",
                "roof", "canopy", "fence", "glazing frame", "truss")
_WALL_MAX = 0.6          # thickest wall looked for, as a fraction of a metre-drawn model (600 mm)
NOT_WALL_KEY = "ed3d_not_wall"


def _items(x):
    if x is None:
        return []
    if isinstance(x, dict):
        return list(x.values())
    try:
        return list(x)
    except Exception:
        return []


def _pos3(v):
    for get in (lambda: (v.x(), v.y(), v.z()), lambda: (v.x, v.y, v.z), lambda: (v[0], v[1], v[2])):
        try:
            x, y, z = get()
            return (float(x), float(y), float(z))
        except Exception:
            pass
    return None


def _kids(g):
    out = []
    for attr in ('children', 'groups'):
        out += _items(getattr(g, attr, None))
    return out


def _as_matrix(m):
    if m is None:
        return None
    if hasattr(m, 'map'):
        return m
    try:
        from PySide6.QtGui import QMatrix4x4
        vals = [float(x) for x in m]
        if len(vals) == 16:
            return QMatrix4x4(*vals).transposed()
    except Exception:
        pass
    return None


def _placements(top):
    """(group, world matrix or None) for a group and every group inside it."""
    try:
        from core.group import iter_placements
        return [(g, _as_matrix(m)) for g, m in iter_placements(top)]
    except Exception:
        pass
    out = []

    def walk(g, base, depth):
        m = _as_matrix(getattr(g, 'xform', None))
        if base is not None:
            m = base if m is None else base * m
        out.append((g, m))
        if depth < 30:
            for c in _kids(g):
                walk(c, m, depth + 1)
    walk(top, None, 0)
    return out


def _wmap(m, p):
    if m is None:
        return p
    q = m.map(QVector3D(*p))
    return (q.x(), q.y(), q.z())


def _vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _vdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _vlen(a):
    return math.sqrt(_vdot(a, a))


def _newell(pts):
    nx = ny = nz = 0.0
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    return (nx, ny, nz)


def _unit(a):
    L = _vlen(a)
    return (a[0] / L, a[1] / L, a[2] / L) if L > 1e-12 else (0.0, 0.0, 0.0)


def _mid(pts):
    xs, ys, zs = [q[0] for q in pts], [q[1] for q in pts], [q[2] for q in pts]
    return ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0, (min(zs) + max(zs)) / 2.0)


def face_triangles(face):
    """A face's triangles (holes left out), as IngeTrazo's own STL export makes them."""
    try:
        from formats.meshexport import export_triangles
        tris = list(export_triangles(face))
        if tris:
            return tris
    except Exception:
        pass
    try:
        tris = list(face.triangulate())
        if tris:
            return tris
    except Exception:
        pass
    vs = _items(getattr(face, 'vertices', None))
    return [(vs[0], vs[k], vs[k + 1]) for k in range(1, len(vs) - 1)]


def _wall_polys(mesh, m):
    """Every face of a wall in the world: dict(pts, holes, n, area, obj)."""
    out = []
    for f in _items(getattr(mesh, 'faces', None)):
        pts = [q for q in (_pos3(v) for v in _items(getattr(f, 'vertices', None))) if q is not None]
        if len(pts) < 3:
            continue
        hls = []
        for h in _items(getattr(f, 'holes', None)):
            hp = [q for q in (_pos3(v) for v in _items(h)) if q is not None]
            if len(hp) >= 3:
                hls.append([_wmap(m, q) for q in hp])
        wp = [_wmap(m, q) for q in pts]
        nv = _newell(wp)
        area = _vlen(nv) / 2.0 - sum(_vlen(_newell(h)) / 2.0 for h in hls)
        out.append({'pts': wp, 'holes': hls, 'n': _unit(nv), 'area': area, 'obj': f})
    return out


def _main_faces(polys, centre, inside=False):
    """(front, back) - the wall's two big upright faces, front being the outside one (or the inside
    one, if asked) - or None if it isn't shaped like a wall."""
    up = (0.0, 0.0, 1.0)
    side = [i for i, fd in enumerate(polys) if fd['area'] > 0 and abs(_vdot(fd['n'], up)) < 0.05]
    if not side:
        return None
    side.sort(key=lambda i: -polys[i]['area'])
    big = polys[side[0]]
    size = max(_vlen(_vsub(q, big['pts'][0])) for q in big['pts']) or 1.0
    wall_max = _WALL_MAX * (1.0 if size < 50.0 else 1000.0)
    best = None
    for ia in side[:12]:
        a = polys[ia]
        for ib in side:
            b = polys[ib]
            if ib == ia or _vdot(a['n'], b['n']) > -0.995:
                continue
            d = _vdot(_vsub(a['pts'][0], b['pts'][0]), a['n'])
            if not (0.0 < d <= wall_max):
                continue
            score = min(a['area'], b['area'])
            if best is None or score > best[0]:
                best = (score, ia, ib)
        if best is not None:
            break
    if best is None:
        return None
    _s, ia, ib = best
    a = polys[ia]
    outward = _vdot(a['n'], _vsub(_mid(a['pts']), centre)) >= 0
    if outward == bool(inside):
        ia, ib = ib, ia
    return ia, ib


def find_walls(scene, inside_walls=False, inside_faces=False):
    """The walls in the selected building or groups (the whole model if nothing is selected).
    [dict(name, group, m, polys, front, back, face, k, length, height, done)]"""
    sel = _items(getattr(scene, 'selection', None))
    picked = [e for e in sel if getattr(e, 'mesh', None) is not None or _kids(e)]
    tops = _items(getattr(scene, 'groups', None))
    if picked:
        def in_tree(t, g):
            return any(x is g for x, _ in _placements(t))
        tops = [t for t in tops if any(in_tree(t, g) for g in picked)]
    places, order, parents = {}, [], {}

    def walk_names(g, above, depth=0):
        if depth > 40:
            return
        for c in _kids(g):
            parents[id(c)] = above + [str(getattr(g, 'name', '') or '')]
            walk_names(c, parents[id(c)], depth + 1)
    for t in tops:
        walk_names(t, [])
        for g, m in _placements(t):
            if id(g) not in places:
                places[id(g)] = (g, m)
                order.append(id(g))
    if picked:
        want = set()
        for pg in picked:
            for g, _m in _placements(pg):
                want.add(id(g))
        order = [k for k in order if k in want]
    allp = []
    for k in order:
        g, m = places[k]
        for f in _items(getattr(getattr(g, 'mesh', None), 'faces', None)):
            for v in _items(getattr(f, 'vertices', None)):
                q = _pos3(v)
                if q is not None:
                    allp.append(_wmap(m, q))
    centre = _mid(allp) if allp else (0.0, 0.0, 0.0)
    out = []
    for k in order:
        g, m = places[k]
        mesh = getattr(g, 'mesh', None)
        if mesh is None or not _items(getattr(mesh, 'faces', None)):
            continue
        ext = getattr(g, 'ext', None)
        if isinstance(ext, dict) and ext.get(NOT_WALL_KEY):
            continue
        name = str(getattr(g, 'name', '') or 'Wall')
        last = name.lower().split(" - ")[-1]
        if any(w_ in nm_.lower() for nm_ in [name] + parents.get(k, []) for w_ in _NEVER_WALLS):
            continue
        if "inside wall" in last:
            if not inside_walls:
                continue
        elif any(w_ in last for w_ in _NOT_WALLS):
            continue
        polys = _wall_polys(mesh, m)
        got = _main_faces(polys, centre, inside_faces)
        if got is None:
            continue
        front, back = got
        fd = polys[front]
        n_ = fd['n']
        along = _unit((-n_[1], n_[0], 0.0))
        xs = [_vdot(q, along) for q in fd['pts']]
        zs = [q[2] for q in fd['pts']]
        allq = [q for p in polys for q in p['pts']]
        size = max(max(q[i] for q in allq) - min(q[i] for q in allq) for i in range(3))
        k_ = 0.001 if size < 50.0 else 1.0           # model units for each real mm
        out.append({'name': name, 'group': g, 'm': m, 'mesh': mesh, 'polys': polys, 'front': front,
                    'back': back, 'face': front, 'k': k_,
                    'length': (max(xs) - min(xs)) / k_, 'height': (max(zs) - min(zs)) / k_,
                    'done': bool(isinstance(ext, dict) and ext.get(DONE_KEY)) or "realistic wall" in name.lower()})
    return out


def wall_mesh_data(wall):
    """The wall's triangles in the world, as (points, triangles) with shared corners."""
    pts, tris, index = [], [], {}
    m = wall['m']

    def key_of(p):
        return (round(p[0], 7), round(p[1], 7), round(p[2], 7))
    for f in _items(getattr(wall['mesh'], 'faces', None)):
        for t in face_triangles(f):
            q = [_pos3(v) for v in t]
            if len(q) != 3 or any(x is None for x in q):
                continue
            ids = []
            for p in q:
                p = _wmap(m, p)
                kk = key_of(p)
                i = index.get(kk)
                if i is None:
                    i = index[kk] = len(pts)
                    pts.append([p[0], p[1], p[2]])
                ids.append(i)
            if len(set(ids)) == 3:
                tris.append(ids)
    return pts, tris


# ---------------------------------------------------------------------------
# Bringing the finished walls back in
# ---------------------------------------------------------------------------
class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))

    def toTuple(self):
        return (self.x(), self.y(), self.z())


def read_obj(path):
    """[(name, points, faces)], one per object in the file Blender wrote."""
    objs, verts = [], []
    cur = None
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.split()
            if not parts or parts[0].startswith('#'):
                continue
            if parts[0] == 'o':
                cur = [line.strip()[1:].strip() or "Wall", []]
                objs.append(cur)
            elif parts[0] == 'v' and len(parts) >= 4:
                verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif parts[0] == 'f' and len(parts) >= 4:
                if cur is None:
                    cur = ["Wall", []]
                    objs.append(cur)
                cur[1].append([int(t.split('/')[0]) - 1 for t in parts[1:]])
    return [(name, verts, faces) for name, faces in objs]


BACK_MODES = [("Leave the plain walls as they are", 'leave'), ("Hide the plain walls", 'hide'),
              ("Replace the plain walls with the carved ones", 'replace')]


def _inverse(m):
    if m is None:
        return None
    try:
        inv = m.inverted()
        if isinstance(inv, tuple):
            inv, ok = inv
            if not ok:
                return None
        return inv
    except Exception:
        return None


def _owner_list(scene, g):
    """The list a group sits in (the model's top list, or the children of the group it's in)."""
    try:
        from core.history import group_owner_list
        return group_owner_list(scene, g)
    except Exception:
        pass
    if g in _items(getattr(scene, 'groups', None)):
        return scene.groups
    for top in _items(getattr(scene, 'groups', None)):
        for pg, _m in _placements(top):
            for attr in ('children', 'groups'):
                kids = getattr(pg, attr, None)
                if isinstance(kids, list) and any(k is g for k in kids):
                    return kids
    return None


def find_plain_wall(scene, name, lo, hi):
    """The plain wall a carved wall was made from: same name, and the carved wall fits inside it.
    (group, world matrix) or None."""
    base = name
    if base.endswith(")") and " (" in base:
        head, tail = base.rsplit(" (", 1)
        if tail[:-1].isdigit():
            base = head
    span = max(hi[i] - lo[i] for i in range(3)) or 1.0
    tol = span * 0.03
    best = None
    for top in _items(getattr(scene, 'groups', None)):
        for g, m in _placements(top):
            if str(getattr(g, 'name', '') or '') != base:
                continue
            ext = getattr(g, 'ext', None)
            if isinstance(ext, dict) and ext.get(DONE_KEY):
                continue
            pts = [_wmap(m, q) for f in _items(getattr(getattr(g, 'mesh', None), 'faces', None))
                   for q in (_pos3(v) for v in _items(getattr(f, 'vertices', None))) if q is not None]
            if not pts:
                continue
            glo = [min(q[i] for q in pts) for i in range(3)]
            ghi = [max(q[i] for q in pts) for i in range(3)]
            if any(lo[i] < glo[i] - tol or hi[i] > ghi[i] + tol for i in range(3)):
                continue
            score = sum(abs(lo[i] - glo[i]) + abs(hi[i] - ghi[i]) for i in range(3))
            if best is None or score < best[0]:
                best = (score, g, m)
    return (best[1], best[2]) if best else None


def bring_back(viewport, path, mode='leave'):
    """Puts the finished walls in the model, one group each, where the plain walls are, and leaves,
    hides or replaces the plain walls (mode). Returns (message, warning)."""
    objs = read_obj(path)
    report = {'groups': 0, 'faces': 0, 'lost': 0, 'replaced': 0, 'unmatched': 0}
    to_hide = []

    def mutate(scene):
        from core.mesh import Mesh
        from core.group import Group
        for name, verts, faces in objs:
            target = Mesh()

            def P(i):
                return VertexWrapper(*verts[i])
            made = 0
            span = max((max(q[i] for q in verts) - min(q[i] for q in verts)) for i in range(3)) if verts else 1.0
            flat_tol = max(span * 1e-6, 1e-9) * 10
            split = []
            for f in faces:                                   # a face that isn't flat: as its triangles
                if len(f) > 3:
                    pts = [verts[i] for i in f]
                    nrm = _unit(_newell(pts))
                    c0 = pts[0]
                    if any(abs(_vdot(_vsub(q, c0), nrm)) > flat_tol for q in pts):
                        split += [[f[0], f[k], f[k + 1]] for k in range(1, len(f) - 1)]
                        continue
                split.append(f)
            for f in split:
                nf = None
                try:
                    nf = target.add_face([P(i) for i in f])
                except Exception:
                    nf = None
                if nf is None and len(f) > 3:
                    for k in range(1, len(f) - 1):          # IngeTrazo wouldn't take it whole: triangles
                        try:
                            if target.add_face([P(f[0]), P(f[k]), P(f[k + 1])]) is not None:
                                made += 1
                            else:
                                report['lost'] += 1
                        except Exception:
                            report['lost'] += 1
                    continue
                if nf is None:
                    report['lost'] += 1
                else:
                    made += 1
            if not made:
                continue
            used = sorted(set(i for f in split for i in f))
            lo = [min(verts[i][k] for i in used) for k in range(3)]
            hi = [max(verts[i][k] for i in used) for k in range(3)]
            plain = find_plain_wall(scene, name, lo, hi) if mode in ('hide', 'replace') else None
            if mode in ('hide', 'replace') and plain is None:
                report['unmatched'] += 1
            owner = _owner_list(scene, plain[0]) if (plain and mode == 'replace') else None
            gname = (str(plain[0].name) if owner is not None else "Realistic wall - %s" % name)
            try:
                g = Group(target, name=gname)
            except TypeError:
                g = Group(gname)
                g.mesh = target
            try:
                g.name = gname
                ext = getattr(g, 'ext', None)
                if isinstance(ext, dict):
                    ext[DONE_KEY] = 1
            except Exception:
                pass
            if owner is not None:
                old, m_old = plain
                # the carved wall is in the model's places: turn it back by what the groups it's
                # going into do, so it lands where the plain wall was
                own = _as_matrix(getattr(old, 'xform', None))
                ok_ = True
                if m_old is None:
                    parent = None                       # nothing moved or turned: no change needed
                elif own is None:
                    parent = m_old
                else:
                    io = _inverse(own)
                    parent = (m_old * io) if io is not None else None
                    ok_ = io is not None
                inv = _inverse(parent) if parent is not None else None
                if parent is not None and inv is None:
                    ok_ = False
                if ok_:
                    if inv is not None:
                        try:
                            g.xform = inv
                        except Exception:
                            pass
                    for attr in ('layer', 'material'):
                        try:
                            setattr(g, attr, getattr(old, attr))
                        except Exception:
                            pass
                    idx = next(i for i, x in enumerate(owner) if x is old)
                    owner[idx] = g
                    try:
                        scene.selection.discard(old)
                    except Exception:
                        pass
                    report['replaced'] += 1
                    owner = 'done'
            if owner != 'done':
                if hasattr(scene, 'add_group'):
                    scene.add_group(g)
                elif hasattr(scene, 'groups') and isinstance(scene.groups, list):
                    scene.groups.append(g)
                else:
                    raise RuntimeError("Could not add the wall to the model.")
                if plain is not None and mode in ('hide', 'replace'):
                    to_hide.append(plain[0])
            report['groups'] += 1
            report['faces'] += made
            for fn in ('recompute_normals', 'update_normals', 'rebuild', 'invalidate'):
                mm = getattr(target, fn, None)
                if callable(mm):
                    try:
                        mm()
                    except Exception:
                        pass
        if not report['groups']:
            raise RuntimeError("None of the faces could be made.")

    h = viewport.history
    for a in ('last_error', 'last_rejected'):
        try:
            setattr(h, a, None)
        except Exception:
            pass
    try:
        h.execute(SnapshotImport(mutate))
        err = getattr(h, 'last_error', None) or getattr(h, 'last_rejected', None)
        if err:
            raise RuntimeError(str(err))
    except Exception as e:
        return "Bringing the wall back failed: %s" % e, True
    hidden = 0
    if to_hide:
        try:
            from core.history import HideCommand
            h.execute(HideCommand(to_hide, True))
        except Exception as e:
            print("%s: Hide didn't take (%s) - doing it by hand" % (PLUGIN_NAME, e))
        for e in to_hide:
            if not getattr(e, 'hidden', False):
                try:
                    e.hidden = True
                except Exception:
                    pass
            hidden += bool(getattr(e, 'hidden', False))
    try:
        viewport.scene.version += 1
    except Exception:
        pass
    try:
        viewport.notify_scene_changed()
    except Exception:
        pass
    n = report['groups']
    msg = "Brought back %d wall%s (%d faces)." % (n, "" if n == 1 else "s", report['faces'])
    if report['replaced']:
        msg += " Replaced %d plain wall%s (Undo puts %s back)." % (
            report['replaced'], "" if report['replaced'] == 1 else "s", "it" if report['replaced'] == 1 else "them")
    if hidden:
        msg += " Hid %d plain wall%s (Show/Hide or Undo shows %s again)." % (
            hidden, "" if hidden == 1 else "s", "it" if hidden == 1 else "them")
    if mode == 'leave':
        msg += " The plain wall%s still there." % (" is" if n == 1 else "s are")
    if report['unmatched']:
        msg += " %d plain wall%s couldn't be found (renamed or moved?) - %s left as %s." % (
            report['unmatched'], "" if report['unmatched'] == 1 else "s",
            "it's" if report['unmatched'] == 1 else "they're", "it was" if report['unmatched'] == 1 else "they were")
    if report['lost']:
        msg += " %d tiny faces were too small for IngeTrazo and left out." % report['lost']
    return msg, False


# ---------------------------------------------------------------------------
# The Blender side: written beside each job and run by Blender
# ---------------------------------------------------------------------------
BLENDER_SCRIPT = '# Eddy\'s Model Works - Realistic Wall, Blender side.\n# Run by the Realistic Wall plugin:  blender --python ed3d_realistic_wall_blender.py -- job.json\n# Works the same way as the "My realistic wall" Geometry Nodes file: a fine grid is pushed\n# in and out by the wall picture (light = stands out, dark = sunk in), then that shape is\n# cut out of the wall face. Openings, ends and edges keep the stone shape.\n# Works with Blender 3.x to 5.x (no importers/exporters used - the mesh comes in as JSON).\n\nimport json, math, os, sys\n\ntry:\n    import bpy, bmesh\n    import numpy as np\n    IN_BLENDER = True\nexcept ImportError:          # lets the maths be tested without Blender\n    import numpy as np\n    IN_BLENDER = False\n\nMAX_POINTS = 600_000         # most points per wall, unless the job says otherwise\n\n\n# ---------------------------------------------------------------- maths (no Blender)\ndef unit(v):\n    v = np.asarray(v, float)\n    n = np.linalg.norm(v)\n    return v / n if n > 1e-12 else v\n\n\ndef face_axes(normal):\n    """u runs along the wall, v runs up it, n points out of the face."""\n    n = unit(normal)\n    up = np.array([0.0, 0.0, 1.0])\n    if abs(n @ up) > 0.95:               # face lying flat (top of a wall) - use Y as \'up\'\n        up = np.array([0.0, 1.0, 0.0])\n    u = unit(np.cross(up, n))\n    v = np.cross(n, u)\n    return u, v, n\n\n\ndef face_extent(verts, normal, plane_point, tol):\n    """Corners (in u, v) of all wall points lying in the chosen face\'s plane."""\n    u, v, n = face_axes(normal)\n    P = np.asarray(verts, float)\n    d0 = float(np.asarray(plane_point, float) @ n)\n    on = np.abs(P @ n - d0) < tol\n    if not on.any():\n        raise ValueError("No wall points found on the chosen face")\n    pu, pv = P[on] @ u, P[on] @ v\n    return (pu.min(), pu.max(), pv.min(), pv.max()), d0\n\n\ndef gray_from_rgba(px):\n    """px: (h, w, 4) floats 0..1 -> (h, w) brightness."""\n    return px[..., 0] * 0.299 + px[..., 1] * 0.587 + px[..., 2] * 0.114\n\n\ndef box_blur(img, r):\n    if r <= 0:\n        return img\n    k = 2 * r + 1\n    pad = np.pad(img, r, mode="wrap")\n    c = pad.cumsum(0).cumsum(1)\n    c = np.pad(c, ((1, 0), (1, 0)))\n    s = c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]\n    return s / (k * k)\n\n\ndef sample_wrap(img, x, y):\n    """Bilinear sample, repeating picture. x, y in picture widths (any value)."""\n    h, w = img.shape\n    fx = (x % 1.0) * w - 0.5\n    fy = (y % 1.0) * h - 0.5\n    x0 = np.floor(fx).astype(int); y0 = np.floor(fy).astype(int)\n    tx = fx - x0; ty = fy - y0\n    x0 %= w; y0 %= h\n    x1 = (x0 + 1) % w; y1 = (y0 + 1) % h\n    a = img[y0, x0] * (1 - tx) + img[y0, x1] * tx\n    b = img[y1, x0] * (1 - tx) + img[y1, x1] * tx\n    return a * (1 - ty) + b * ty\n\n\ndef normalise(img):\n    lo, hi = np.percentile(img, 1), np.percentile(img, 99)\n    if hi - lo < 1e-6:\n        return np.zeros_like(img)\n    return np.clip((img - lo) / (hi - lo), 0, 1)\n\n\ndef protect_mask(tris, axes, d0, depth, gu, gv):\n    """Grid points behind anything standing out of the face (a window or sill built in, a pier):\n    the face is left plain there, so nothing gets cut loose. tris: (T, 3, 3) wall triangles."""\n    u, v, n = axes\n    nu, nv = len(gu), len(gv)\n    mask = np.zeros((nv, nu), bool)\n    if tris is None or len(tris) == 0:\n        return mask\n    tol = max(depth * 0.05, 1e-9)\n    dn = tris @ n                                           # (T, 3) how far out each corner is\n    out_ = (dn > d0 + tol).any(1)                           # stands out of the face\n    shallow = ((dn < d0 - tol) & (dn > d0 - depth - tol)).all(1)   # sunk in less than the stones go\n    pick = tris[out_ | shallow]\n    if len(pick) == 0:\n        return mask\n    du = (gu[-1] - gu[0]) / max(nu - 1, 1)\n    dv = (gv[-1] - gv[0]) / max(nv - 1, 1)\n    PU, PV = pick @ u, pick @ v                             # (T, 3) each\n    for a, b in zip(PU, PV):\n        i0 = max(0, int(math.floor((a.min() - gu[0]) / du)) - 1)\n        i1 = min(nu - 1, int(math.ceil((a.max() - gu[0]) / du)) + 1)\n        j0 = max(0, int(math.floor((b.min() - gv[0]) / dv)) - 1)\n        j1 = min(nv - 1, int(math.ceil((b.max() - gv[0]) / dv)) + 1)\n        if i1 < i0 or j1 < j0:\n            continue\n        X, Y = np.meshgrid(gu[i0:i1 + 1], gv[j0:j1 + 1])\n        x0, y0 = a[0], b[0]\n        e1 = (a[1] - x0, b[1] - y0); e2 = (a[2] - x0, b[2] - y0)\n        det = e1[0] * e2[1] - e1[1] * e2[0]\n        if abs(det) < 1e-18:                                 # edge-on (a sill\'s top, say): its box\n            mask[j0:j1 + 1, i0:i1 + 1] = True\n            continue\n        px, py = X - x0, Y - y0\n        l1 = (px * e2[1] - py * e2[0]) / det\n        l2 = (e1[0] * py - e1[1] * px) / det\n        slack = 1.0 * max(du, dv) / max(math.sqrt(abs(det)), 1e-12)\n        inside = (l1 >= -slack) & (l2 >= -slack) & (l1 + l2 <= 1 + slack)\n        mask[j0:j1 + 1, i0:i1 + 1] |= inside\n    # one more point all round, so the stones don\'t undercut its edges\n    m = mask.copy()\n    m[1:, :] |= mask[:-1, :]; m[:-1, :] |= mask[1:, :]\n    m[:, 1:] |= mask[:, :-1]; m[:, :-1] |= mask[:, 1:]\n    return m\n\n\ndef value_noise(x, y, seed):\n    """Smooth random values 0..1 (one blob about every 1 unit of x, y)."""\n    rng = np.random.default_rng(int(seed) + 12345)\n    N = 64\n    table = rng.random((N, N))\n    xi = np.floor(x).astype(int); yi = np.floor(y).astype(int)\n    tx = x - xi; ty = y - yi\n    tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty)\n    xi %= N; yi %= N\n    x1 = (xi + 1) % N; y1 = (yi + 1) % N\n    a = table[yi, xi] * (1 - tx) + table[yi, x1] * tx\n    b = table[y1, xi] * (1 - tx) + table[y1, x1] * tx\n    return a * (1 - ty) + b * ty\n\n\ndef hide_repeats(img, sx, sy, amount, seed, want_mix=False):\n    """The picture, with a second copy (moved and mirrored) mixed in in big soft patches, so the\n    repeats don\'t show. Where the copies meet, the higher stone wins (no blurry mush).\n    With want_mix, also how much of the second copy shows at each point (for the colours)."""\n    h1 = sample_wrap(img, sx, sy)\n    if amount <= 0:\n        return (h1, np.zeros_like(h1)) if want_mix else h1\n    h2 = sample_wrap(img, -sx + MIRROR_SHIFT, sy)                   # mirrored and slid along (courses stay level)\n    n = value_noise(sx / 1.7 + 3.1, sy / 1.7 + 7.3, seed)   # patches about 1.7 pictures across\n    n = n * 0.6 + value_noise(sx / 0.7, sy / 0.7, seed + 1) * 0.4\n    w2 = np.clip((n - (1.0 - amount * 0.5)) / 0.08 + 0.5, 0.0, 1.0)   # amount 1: about half each\n    w1 = 1.0 - w2\n    a, b = h1 + w1, h2 + w2\n    top = np.maximum(a, b) - 0.25\n    r1 = np.maximum(a - top, 0.0); r2 = np.maximum(b - top, 0.0)\n    h = (h1 * r1 + h2 * r2) / (r1 + r2 + 1e-9)\n    return (h, r2 / (r1 + r2 + 1e-9)) if want_mix else h\n\n\nMIRROR_SHIFT = 0.37      # the second copy: mirrored, and slid along this much of a picture\n\n\ndef colour_picture_for(path):\n    """For a height picture (name_disp_4k.png) with its colour photo beside it (name_diff_4k.jpg),\n    the colour photo\'s path - else None."""\n    folder, fn = os.path.split(path)\n    low = fn.lower()\n    for w in HEIGHT_WORDS:\n        i = low.find(w)\n        if i < 0:\n            continue\n        stem, rest = low[:i], os.path.splitext(low[i + len(w):])[0]\n        try:\n            names = os.listdir(folder)\n        except Exception:\n            return None\n        best = None\n        for other in names:\n            o = other.lower()\n            if not o.startswith(stem) or other == fn:\n                continue\n            for cw in COLOUR_WORDS:\n                if o.startswith(stem + cw) and o.endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp")):\n                    score = (os.path.splitext(o[len(stem + cw):])[0] == rest, o.endswith((".jpg", ".jpeg")))\n                    if best is None or score > best[0]:\n                        best = (score, os.path.join(folder, other))\n        return best[1] if best else None\n    return None\n\n\n_mids = {}\n\n\ndef otsu_level(img):\n    """The brightness that best splits the picture into joints (dark) and bricks (light)."""\n    key = (id(img), img.shape)\n    if key in _mids:\n        return _mids[key]\n    hist, edges = np.histogram(img[::4, ::4], bins=128, range=(0.0, 1.0))\n    p = hist / max(hist.sum(), 1)\n    w = np.cumsum(p)\n    mu = np.cumsum(p * (edges[:-1] + edges[1:]) / 2)\n    between = (mu[-1] * w - mu) ** 2 / np.maximum(w * (1 - w), 1e-12)\n    level = float((edges[:-1] + edges[1:])[int(np.argmax(between))] / 2)\n    _mids.clear()\n    _mids[key] = level\n    return level\n\n\ndef crisp_picture(img, amount):\n    """Sharper steps from the bricks down into the joints, flatter brick faces - judged against the\n    wall round each brick, so big hollows and bulges in the wall stay. amount 0..1."""\n    if amount <= 0:\n        return img\n    key = ("crisp", id(img), img.shape, round(amount, 3))\n    if key in _mids:\n        return _mids[key]\n    r = max(3, img.shape[1] // 48)                         # about a brick or two across\n    low = box_blur(img, r)\n    high = img - low\n    sd = float(high.std()) or 1e-6\n    g = 1.0 + 5.0 * amount\n    sharp = np.tanh(g * high / (1.5 * sd)) * (1.5 * sd)\n    out = normalise((1.0 - amount) * img + amount * (low + sharp))\n    for k_ in [k for k in _mids if k[0] == "crisp"]:\n        del _mids[k_]\n    _mids[key] = out\n    return out\n\n\nHEIGHT_WORDS = ("_disp", "_displacement", "_height", "_heightmap", "_bump")\nCOLOUR_WORDS = ("_diff", "_diffuse", "_col", "_color", "_colour", "_albedo", "_basecolor", "_base_color")\n\n\ndef height_picture_for(path):\n    """For a colour photo (name_diff_4k.jpg) with its height picture beside it (name_disp_4k.png),\n    the height picture\'s path - else None."""\n    folder, fn = os.path.split(path)\n    low = fn.lower()\n    for w in COLOUR_WORDS:\n        i = low.find(w)\n        if i < 0:\n            continue\n        stem, rest = low[:i], os.path.splitext(low[i + len(w):])[0]\n        try:\n            names = os.listdir(folder)\n        except Exception:\n            return None\n        best = None\n        for other in names:\n            o = other.lower()\n            if not o.startswith(stem) or other == fn:\n                continue\n            for hw in HEIGHT_WORDS:\n                if o.startswith(stem + hw):\n                    score = (os.path.splitext(o[len(stem + hw):])[0] == rest, o.endswith((".png", ".tif", ".tiff", ".exr")))\n                    if best is None or score > best[0]:\n                        best = (score, os.path.join(folder, other))\n        return best[1] if best else None\n    return None\n\n\ndef build_cutter(extent, d0, axes, img, job, tris=None):\n    """Closed block: top is the stone relief, it reaches out past the face.\n    Returns verts (N,3) and faces (list of tuples)."""\n    u, v, n = axes\n    u0, u1, v0, v1 = extent\n    depth = float(job["depth"])\n    tw, th = float(job["tile_width"]), float(job["tile_height"])\n    res = max(8, int(job.get("detail", 120)))            # points across one picture\n    margin = max(depth, 1e-6) * 0.5\n    u0 -= margin; u1 += margin; v0 -= margin; v1 += margin\n    nu = max(2, int(math.ceil((u1 - u0) / tw * res)) + 1)\n    nv = max(2, int(math.ceil((v1 - v0) / th * res)) + 1)\n    cap_pts = int(job.get("max_points") or MAX_POINTS)\n    if nu * nv > cap_pts:                                 # keep it to a sensible size\n        s = math.sqrt(cap_pts / (nu * nv))\n        nu = max(2, int(nu * s)); nv = max(2, int(nv * s))\n    gu = np.linspace(u0, u1, nu)\n    gv = np.linspace(v0, v1, nv)\n    UU, VV = np.meshgrid(gu, gv)                          # (nv, nu)\n    sx = (UU - float(job.get("offset_x", 0.0))) / tw\n    sy = (VV - float(job.get("offset_y", 0.0))) / th\n    img = crisp_picture(img, float(job.get("crisp", 0.0)))\n    h = hide_repeats(img, sx, sy, float(job.get("mix", 0.0)), job.get("seed", 1))\n    if job.get("invert"):\n        h = 1.0 - h\n    keep = protect_mask(tris, axes, d0, depth, gu, gv)\n    h[keep] = 1.0                                         # plain face behind things that stand out\n    eps = depth * 0.01\n    W = d0 + eps - depth * (1.0 - h)                      # white stays at the face, black is sunk in\n    top = d0 + depth * 0.5                                # cutter reaches just past the face\n    grid = (UU[..., None] * u + VV[..., None] * v + W[..., None] * n).reshape(-1, 3)\n\n    # ring of boundary points, raised to \'top\'\n    ring = ([(0, i) for i in range(nu)] + [(j, nu - 1) for j in range(1, nv)] +\n            [(nv - 1, i) for i in range(nu - 2, -1, -1)] + [(j, 0) for j in range(nv - 2, 0, -1)])\n    ring_idx = [j * nu + i for j, i in ring]\n    cap = grid[ring_idx] + 0.0\n    cap = cap - np.outer(cap @ n, n) + top * n\n    verts = np.vstack([grid, cap])\n    base = len(grid)\n    # relief surface (faces into the wall), as an array of quads\n    J, I = np.meshgrid(np.arange(nv - 1), np.arange(nu - 1), indexing="ij")\n    r0 = (J * nu + I).ravel()\n    quads = np.stack([r0, r0 + nu, r0 + nu + 1, r0 + 1], 1)\n    m = len(ring_idx)\n    ri = np.array(ring_idx)\n    k = np.arange(m)\n    sides = np.stack([ri, ri[(k + 1) % m], base + (k + 1) % m, base + k], 1)   # sides\n    faces = [quads, sides, np.arange(base, base + m)[None, :]]                  # + flat top cap\n    across = (nu - 1) / max((u1 - u0) / tw, 1e-9)        # the detail it really came out at\n    return verts, faces, (nu, nv, int(keep.sum()), across)\n\n\n# ---------------------------------------------------------------- Blender part\n# Each carved wall keeps its plain wall (hidden, in the "Realistic Wall - plain walls" collection),\n# so it can be carved again with new settings from the Realistic Wall panel (N sidebar).\nPLAIN_COLL = "Realistic Wall - plain walls"\n_pictures = {}\n\n\ndef load_picture(path, blur):\n    key = (os.path.normcase(os.path.abspath(path)), int(blur))\n    if key in _pictures:\n        return _pictures[key]\n    im = bpy.data.images.load(path, check_existing=True)\n    w, h = im.size\n    px = np.empty(w * h * 4, dtype=np.float32)\n    im.pixels.foreach_get(px)\n    g = gray_from_rgba(px.reshape(h, w, 4))\n    g = normalise(box_blur(g, int(blur)))\n    _pictures.clear()\n    _pictures[key] = g\n    return g\n\n\ndef build_mesh(name, verts, faces):\n    """A mesh from points and faces. faces: a list of tuples, or a list of numpy arrays each\n    holding faces with the same number of corners (fast, for big grids)."""\n    me = bpy.data.meshes.new(name)\n    verts = np.asarray(verts, dtype=np.float64)\n    if faces and isinstance(faces[0], np.ndarray):\n        loops = np.concatenate([f.ravel() for f in faces]).astype(np.int32)\n        sizes = np.concatenate([np.full(len(f), f.shape[1], np.int32) for f in faces])\n    else:\n        loops = np.array([i for f in faces for i in f], np.int32)\n        sizes = np.array([len(f) for f in faces], np.int32)\n    starts = np.concatenate([[0], np.cumsum(sizes)[:-1]]).astype(np.int32)\n    try:\n        me.vertices.add(len(verts))\n        me.vertices.foreach_set("co", verts.astype(np.float32).ravel())\n        me.loops.add(len(loops))\n        me.loops.foreach_set("vertex_index", loops)\n        me.polygons.add(len(sizes))\n        me.polygons.foreach_set("loop_start", starts)\n        try:\n            me.polygons.foreach_set("loop_total", sizes)      # Blender 3.x needs this\n        except Exception:\n            pass\n        me.update(calc_edges=True)\n    except Exception as e:                                    # the slow way\n        print("Realistic Wall: quick mesh build failed (%s), using from_pydata" % e)\n        bpy.data.meshes.remove(me)\n        me = bpy.data.meshes.new(name)\n        fl = [tuple(int(i) for i in loops[s_:s_ + n_]) for s_, n_ in zip(starts, sizes)]\n        me.from_pydata([tuple(p) for p in verts], [], fl)\n    me.validate()\n    me.update()\n    return me\n\n\ndef make_object(name, me, coll=None):\n    ob = bpy.data.objects.new(name, me)\n    (coll or bpy.context.scene.collection).objects.link(ob)\n    return ob\n\n\ndef tidy_mesh(me, recalc=True):\n    bm = bmesh.new()\n    bm.from_mesh(me)\n    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)\n    if recalc:\n        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)\n    bm.to_mesh(me)\n    bm.free()\n\n\ndef close_gaps(me):\n    """Joins a wall\'s edges up where one face has a corner part way along another face\'s edge (an\n    arch meeting a straight wall, say), so the wall is a closed solid and Blender\'s quick cut works\n    on it. Returns how many edges are still open (0 = closed)."""\n    bm = bmesh.new()\n    bm.from_mesh(me)\n    try:\n        co = [v.co for v in bm.verts]\n        size = max((max(c[i] for c in co) - min(c[i] for c in co)) for i in range(3)) if co else 1.0\n        tol = max(size * 2e-6, 1e-9)\n        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=tol)\n        for _round in range(4):\n            bnd = [e for e in bm.edges if len(e.link_faces) == 1]\n            if not bnd or len(bnd) > 4000:\n                break\n            pts = list({v for e in bnd for v in e.verts})\n            splits = 0\n            for e in bnd:\n                if not e.is_valid:\n                    continue\n                va, vb = e.verts\n                a, b = va.co.copy(), vb.co.copy()\n                ab = b - a\n                L2 = ab.length_squared\n                if L2 < tol * tol:\n                    continue\n                on = []\n                for v in pts:\n                    if not v.is_valid or v is va or v is vb:\n                        continue\n                    t = (v.co - a).dot(ab) / L2\n                    if t <= 1e-6 or t >= 1 - 1e-6:\n                        continue\n                    if (a + ab * t - v.co).length < tol * 5:\n                        on.append((t, v))\n                if not on:\n                    continue\n                on.sort(key=lambda x: x[0])\n                cur, origin, done_t = e, va, 0.0\n                for t, v in on:\n                    fac = (t - done_t) / max(1.0 - done_t, 1e-12)\n                    ne, nv = bmesh.utils.edge_split(cur, origin, fac)\n                    nv.co = v.co.copy()\n                    cur = ne if vb in ne.verts else cur\n                    if vb not in cur.verts:\n                        cur = next((x for x in nv.link_edges if vb in x.verts), cur)\n                    origin, done_t = nv, t\n                    splits += 1\n            if not splits:\n                break\n            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=tol * 5)\n        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)\n        still = sum(1 for e in bm.edges if not e.is_manifold)\n        bm.to_mesh(me)\n    except Exception as ex:\n        print("Realistic Wall: closing gaps:", ex)\n        still = -1\n    bm.free()\n    me.update()\n    return still\n\n\ndef shade_flat(me):\n    try:\n        me.shade_flat()                                   # Blender 4.1 and later\n        return\n    except Exception:\n        pass\n    try:\n        me.polygons.foreach_set("use_smooth", [False] * len(me.polygons))\n    except Exception:\n        pass\n\n\ndef mesh_triangles(me):\n    try:\n        me.calc_loop_triangles()\n    except Exception:\n        pass                                # Blender works them out by itself now\n    n = len(me.loop_triangles)\n    idx = np.empty(n * 3, dtype=np.int32)\n    me.loop_triangles.foreach_get("vertices", idx)\n    co = np.empty(len(me.vertices) * 3, dtype=np.float64)\n    me.vertices.foreach_get("co", co)\n    return co.reshape(-1, 3)[idx.reshape(-1, 3)]\n\n\ndef mesh_points(me):\n    co = np.empty(len(me.vertices) * 3, dtype=np.float64)\n    me.vertices.foreach_get("co", co)\n    return co.reshape(-1, 3)\n\n\nSLOW_OK = 400_000      # the slow cut is only used by itself on a cutter smaller than this\n\n\ndef carve(ob, cut, allow_slow=False):\n    """Cuts the stone shape into the wall. Tries Blender\'s quick Manifold cut first (Blender 4.5\n    and later, needs a closed wall). The slow Exact cut is only used on a small cutter, or if\n    allowed. Returns \'quick\', \'slow\', \'too slow\' or \'\'."""\n    before = len(ob.data.polygons)\n    for solver in ("MANIFOLD", "EXACT"):\n        if solver == "EXACT" and len(cut.data.vertices) > SLOW_OK and not allow_slow:\n            return "too slow"\n        mod = ob.modifiers.new("Realistic face", "BOOLEAN")\n        mod.operation = "DIFFERENCE"\n        mod.object = cut\n        try:\n            mod.solver = solver\n        except Exception:\n            ob.modifiers.remove(mod)\n            continue\n        if solver == "EXACT":\n            try:\n                mod.use_hole_tolerant = True\n            except Exception:\n                pass\n        try:\n            dg = bpy.context.evaluated_depsgraph_get()\n            me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))\n        except Exception as e:\n            print("Realistic Wall:", solver, e)\n            ob.modifiers.remove(mod)\n            continue\n        ob.modifiers.remove(mod)\n        if len(me.polygons) > before:                     # it has the stones in it\n            old = ob.data\n            ob.data = me\n            bpy.data.meshes.remove(old)\n            print("Realistic Wall: cut with", solver)\n            return "quick" if solver == "MANIFOLD" else "slow"\n        bpy.data.meshes.remove(me)\n    return ""\n\n\ndef stone_material():\n    mat = bpy.data.materials.get("Realistic wall") or bpy.data.materials.new("Realistic wall")\n    mat.diffuse_color = (0.62, 0.58, 0.52, 1.0)\n    return mat\n\n\ndef add_colour(ob, img, job, colour_path):\n    """Puts the colour photo on the wall, lined up with the carving (the same repeats and the same\n    mixed-in patches). For looking at only - the shape doesn\'t change."""\n    me = ob.data\n    nl = len(me.loops)\n    if not nl:\n        return\n    vi = np.empty(nl, dtype=np.int32)\n    me.loops.foreach_get("vertex_index", vi)\n    P = mesh_points(me)[vi]\n    u, v, n = face_axes(list(ob.get("rw_normal", (0, -1, 0))))\n    tw, th = float(job["tile_width"]), float(job["tile_height"])\n    sx = (P @ u - float(job.get("offset_x", 0.0))) / tw\n    sy = (P @ v - float(job.get("offset_y", 0.0))) / th\n    _h, mix = hide_repeats(crisp_picture(img, float(job.get("crisp", 0.0))), sx, sy,\n                           float(job.get("mix", 0.0)), job.get("seed", 1), want_mix=True)\n    for name, uv in (("RW picture", np.stack([sx, sy], 1)), ("RW mirrored", np.stack([-sx + MIRROR_SHIFT, sy], 1))):\n        lay = me.uv_layers.get(name) or me.uv_layers.new(name=name)\n        lay.data.foreach_set("uv", uv.astype(np.float32).ravel())\n    att = me.attributes.get("rw_mix")\n    if att is not None and (att.domain != \'CORNER\' or att.data_type != \'FLOAT\'):\n        me.attributes.remove(att)\n        att = None\n    if att is None:\n        att = me.attributes.new("rw_mix", \'FLOAT\', \'CORNER\')\n    att.data.foreach_set("value", mix.astype(np.float32))\n    try:\n        me.uv_layers.active = me.uv_layers["RW picture"]\n    except Exception:\n        pass\n    me.materials.clear()\n    me.materials.append(colour_material(colour_path))\n\n\ndef colour_material(path):\n    im = bpy.data.images.load(path, check_existing=True)\n    name = "Realistic wall colour - %s" % os.path.basename(path)\n    mat = bpy.data.materials.get(name)\n    if mat is not None:\n        return mat\n    mat = bpy.data.materials.new(name)\n    mat.diffuse_color = (0.55, 0.35, 0.28, 1.0)\n    mat.use_nodes = True\n    nt = mat.node_tree\n    nt.nodes.clear()\n    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (700, 0)\n    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (420, 0)\n    try:\n        bsdf.inputs["Roughness"].default_value = 0.9\n    except Exception:\n        pass\n    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])\n    texs = []\n    for i, uvname in enumerate(("RW picture", "RW mirrored")):\n        uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = uvname; uvn.location = (-500, 150 - i * 300)\n        tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = im; tex.location = (-280, 150 - i * 300)\n        nt.links.new(uvn.outputs[0], tex.inputs["Vector"])\n        texs.append(tex)\n    att = nt.nodes.new("ShaderNodeAttribute"); att.attribute_name = "rw_mix"; att.location = (-280, 350)\n    try:\n        att.attribute_type = \'GEOMETRY\'\n    except Exception:\n        pass\n    try:\n        mix = nt.nodes.new("ShaderNodeMix")\n        mix.data_type = \'RGBA\'\n        fac = next(i for i in mix.inputs if i.name == "Factor" and i.type == \'VALUE\')\n        a = next(i for i in mix.inputs if i.name == "A" and i.type == \'RGBA\')\n        b = next(i for i in mix.inputs if i.name == "B" and i.type == \'RGBA\')\n        res = next(o for o in mix.outputs if o.name == "Result" and o.type == \'RGBA\')\n    except Exception:\n        mix = nt.nodes.new("ShaderNodeMixRGB")               # older Blender\n        fac, a, b, res = mix.inputs[0], mix.inputs[1], mix.inputs[2], mix.outputs[0]\n    mix.location = (120, 100)\n    nt.links.new(att.outputs["Fac"], fac)\n    nt.links.new(texs[0].outputs["Color"], a)\n    nt.links.new(texs[1].outputs["Color"], b)\n    nt.links.new(res, bsdf.inputs["Base Color"])\n    nt.nodes.active = texs[0]\n    return mat\n\n\ndef colour_path_for(st):\n    if not st.colour_picture or not os.path.isfile(bpy.path.abspath(st.colour_picture)):\n        pic = bpy.path.abspath(st.picture) if st.picture else ""\n        cp = colour_picture_for(pic) if pic else None\n        st.busy = True\n        st.colour_picture = cp or pic\n        st.busy = False\n    p = bpy.path.abspath(st.colour_picture) if st.colour_picture else ""\n    return p if p and os.path.isfile(p) else ""\n\n\ndef apply_colours(context):\n    """Colours on (or off) every carved wall, without carving again."""\n    st = context.scene.rw\n    walls = carved_walls(context.scene)\n    if not walls:\n        return\n    cp = colour_path_for(st) if st.show_colour else ""\n    img = load_picture(bpy.path.abspath(st.picture), st.blur) if (cp and st.picture) else None\n    job = settings_job(st)\n    for ob, _p in walls:\n        if cp and img is not None:\n            add_colour(ob, img, job, cp)\n        else:\n            ob.data.materials.clear()\n            ob.data.materials.append(stone_material())\n    set_view(st.show_colour and bool(cp))\n\n\ndef set_view(colour):\n    try:\n        for win in bpy.context.window_manager.windows:\n            for area in win.screen.areas:\n                if area.type == "VIEW_3D":\n                    sh = area.spaces[0].shading\n                    if colour:\n                        sh.type = "MATERIAL"\n                    else:\n                        sh.type = "SOLID"\n                        sh.show_cavity = True\n                        sh.cavity_type = "BOTH"\n                        sh.light = "STUDIO"\n    except Exception as e:\n        print("view:", e)\n\n\ndef settings_job(st):\n    """The panel\'s settings (real mm) as the sizes the cutting works in (model units)."""\n    k = st.k or 1.0\n    return {"depth": st.depth * k, "tile_width": st.tile_w * k, "tile_height": st.tile_h * k,\n            "offset_x": st.off_x * k, "offset_y": st.off_y * k, "detail": st.detail,\n            "max_points": st.max_points * 1000, "mix": st.mix / 100.0, "seed": st.seed,\n            "invert": not st.light_out, "crisp": st.crisp / 100.0, "patch": st.patch,\n            "allow_slow": st.allow_slow}\n\n\ndef carve_one(ob, plain, img, job):\n    """Gives ob a fresh copy of its plain wall, carved. Returns a note for the panel."""\n    me = plain.data.copy()\n    old = ob.data\n    ob.data = me\n    if old is not None and old.users == 0:\n        bpy.data.meshes.remove(old)\n    tidy_mesh(ob.data)\n    shade_flat(ob.data)\n    normal = list(ob.get("rw_normal", (0, -1, 0)))\n    point = list(ob.get("rw_point", (0, 0, 0)))\n    axes = face_axes(normal)\n    tol = max(float(job["depth"]) * 0.05, 1e-6)\n    extent, d0 = face_extent(mesh_points(ob.data), normal, point, tol)\n    if job.get("patch"):                                   # just a 1 m square in the middle\n        half = 500.0 * (bpy.context.scene.rw.k or 1.0)\n        cu, cv = (extent[0] + extent[1]) / 2, (extent[2] + extent[3]) / 2\n        extent = (max(extent[0], cu - half), min(extent[1], cu + half),\n                  max(extent[2], cv - half), min(extent[3], cv + half))\n    import time as _t\n    t0 = _t.time()\n    verts, faces, size = build_cutter(extent, d0, axes, img, job, mesh_triangles(ob.data))\n    cut = make_object(ob.name + " cutter", build_mesh(ob.name + " cutter", verts, faces))\n    tidy_mesh(cut.data)\n    how = carve(ob, cut, job.get("allow_slow"))\n    ok = how in ("quick", "slow")\n    me_cut = cut.data\n    bpy.data.objects.remove(cut, do_unlink=True)\n    bpy.data.meshes.remove(me_cut)\n    ob.data.materials.clear()\n    ob.data.materials.append(stone_material())\n    shade_flat(ob.data)\n    st = bpy.context.scene.rw\n    if ok and st.show_colour:\n        cp = colour_path_for(st)\n        if cp:\n            try:\n                add_colour(ob, img, job, cp)\n            except Exception as e:\n                print("Realistic Wall: colours:", e)\n    limited = size[3] < job["detail"] - 0.5\n    note = "detail %d%s, %s cut, %.0f s%s" % (round(size[3]), " (limited)" if limited else "", how or "no",\n                                            _t.time() - t0, " - test patch" if job.get("patch") else "")\n    gaps = int(plain.get("rw_open", 0))\n    if how == "too slow":\n        note = "quick cut didn\'t work - tick \'Allow the slow cut\' or lower J"\n    if how in ("slow", "too slow") and gaps > 0:\n        note += " (wall has %d open edges)" % gaps\n    elif not ok:\n        note = "could not cut"\n    ob["rw_note"] = note\n    print("Realistic Wall: %s - %s, %d kept plain" % (ob.name, note, size[2]))\n    return ok, note, limited\n\n\ndef carved_walls(scene):\n    out = []\n    for ob in scene.objects:\n        plain = bpy.data.objects.get(ob.get("rw_plain", "")) if ob.get("rw_plain") else None\n        if plain is not None:\n            out.append((ob, plain))\n    return out\n\n\ndef recarve_all(context, only_selected=False):\n    st = context.scene.rw\n    if not st.picture or not os.path.isfile(bpy.path.abspath(st.picture)):\n        return "Pick the picture first"\n    hp = height_picture_for(bpy.path.abspath(st.picture))\n    if hp:                                                  # a colour photo: use its height picture\n        st.busy = True\n        st.picture = hp\n        st.busy = False\n    img = load_picture(bpy.path.abspath(st.picture), st.blur)\n    job = settings_job(st)\n    walls = carved_walls(context.scene)\n    if only_selected:\n        walls = [w for w in walls if w[0].select_get()]\n    if not walls:\n        return "No carved walls here"\n    lim = bad = 0\n    for ob, plain in walls:\n        ok, note, limited = carve_one(ob, plain, img, job)\n        lim += bool(limited)\n        bad += not ok\n    st.last_note = (("Test patch carved." if st.patch else\n                     "Carved %d wall%s." % (len(walls), "" if len(walls) == 1 else "s")) +\n                    ("  Detail limited on %d - raise J." % lim if lim else "") +\n                    ("  %d not cut - see below." % bad if bad else ""))\n    return None\n\n\ndef clean_for_ingetrazo(ob):\n    """The wall\'s faces as IngeTrazo likes them, in the model\'s places: flat areas joined back into\n    whole faces (no fans of thin triangles), and any face that isn\'t quite flat (the tilted bits of\n    the stones) split into triangles, which always are. Returns (points, faces)."""\n    bm = bmesh.new()\n    bm.from_mesh(ob.data)\n    bm.transform(ob.matrix_world)\n    co = [v.co for v in bm.verts]\n    size = max((max(c[i] for c in co) - min(c[i] for c in co)) for i in range(3)) if co else 1.0\n    tol = max(size * 1e-6, 1e-9)\n    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=tol)\n    try:\n        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.3), use_dissolve_boundaries=False,\n                                 verts=bm.verts[:], edges=bm.edges[:])\n    except Exception as e:\n        print("Realistic Wall: joining flat faces:", e)\n    bent = []\n    for f in bm.faces:\n        if len(f.verts) <= 3:\n            continue\n        c = f.calc_center_median()\n        nrm = f.normal\n        if any(abs((v.co - c).dot(nrm)) > tol * 10 for v in f.verts):\n            bent.append(f)\n    if bent:\n        bmesh.ops.triangulate(bm, faces=bent)\n    bm.verts.index_update()\n    pts = [tuple(v.co) for v in bm.verts]\n    faces = [[v.index for v in f.verts] for f in bm.faces]\n    bm.free()\n    return pts, faces\n\n\ndef write_obj(path, obs):\n    with open(path, "w") as f:\n        f.write("# Eddy\'s Model Works - Realistic Wall\\n")\n        off = 1\n        for ob in obs:\n            pts, faces = clean_for_ingetrazo(ob)\n            f.write("o %s\\n" % ob.name)\n            f.write("".join("v %.7f %.7f %.7f\\n" % p for p in pts))\n            f.write("".join("f " + " ".join(str(i + off) for i in fc) + "\\n" for fc in faces))\n            off += len(pts)\n            print("Realistic Wall: sent %s - %d faces" % (ob.name, len(faces)))\n\n\nSETTINGS_NAME = "realistic wall settings.json"\n\n\ndef keep_settings(context, save_file=True):\n    """Writes the panel\'s settings beside the carved walls (the plugin in IngeTrazo picks them up), and\n    saves this Blender file so they are here next time it\'s opened."""\n    st = context.scene.rw\n    d = {"depth": st.depth, "tile_w": st.tile_w, "tile_h": st.tile_h, "detail": st.detail, "blur": st.blur,\n         "off_x": st.off_x, "off_y": st.off_y, "mix": st.mix, "seed": st.seed, "max_pts": st.max_points,\n         "crisp": st.crisp, "light_out": bool(st.light_out), "picture": bpy.path.abspath(st.picture),\n         "colour": bool(st.show_colour), "allow_slow": bool(st.allow_slow)}\n    if st.out_obj:\n        try:\n            with open(os.path.join(os.path.dirname(st.out_obj), SETTINGS_NAME), "w", encoding="utf-8") as f:\n                json.dump(d, f, indent=1)\n        except Exception as e:\n            print("Realistic Wall: settings not kept:", e)\n    if save_file and bpy.data.filepath:\n        try:\n            bpy.ops.wm.save_mainfile()\n        except Exception as e:\n            print("Realistic Wall: Blender file not saved:", e)\n\n\n# ---- the panel ----\ndef _auto(self, context):\n    if self.auto and not self.busy:\n        self.busy = True\n        try:\n            recarve_all(context)\n        finally:\n            self.busy = False\n\n\nif IN_BLENDER:\n    from bpy.props import FloatProperty, IntProperty, BoolProperty, StringProperty, PointerProperty\n\n    class RW_Settings(bpy.types.PropertyGroup):\n        picture: StringProperty(name="Picture", subtype=\'FILE_PATH\', update=_auto)\n        depth: FloatProperty(name="A  Depth of the joints (mm)", default=30.0, min=0.5, max=500.0, update=_auto)\n        tile_w: FloatProperty(name="B  Picture covers across (mm)", default=2000.0, min=50.0, max=20000.0,\n                              update=_auto)\n        tile_h: FloatProperty(name="C  Picture covers up (mm)", default=2000.0, min=50.0, max=20000.0,\n                              update=_auto)\n        detail: IntProperty(name="D  Detail (resolution)", default=300, min=20, max=2000, update=_auto,\n                            description="Points across one picture. More is sharper but slower")\n        blur: IntProperty(name="E  Smooth the picture", default=1, min=0, max=10, update=_auto)\n        off_x: FloatProperty(name="F  Move picture along (mm)", default=0.0, update=_auto)\n        off_y: FloatProperty(name="G  Move picture up (mm)", default=0.0, update=_auto)\n        mix: IntProperty(name="H  Hide the repeats (%)", default=60, min=0, max=100, update=_auto)\n        seed: IntProperty(name="I  Pattern number", default=1, min=1, max=999, update=_auto)\n        max_points: IntProperty(name="J  Most points per wall (thousands)", default=600, min=50, max=20000,\n                                update=_auto, description="Limits the detail on a big wall so the cut "\n                                "doesn\'t take too long. Raise it if your PC can cope")\n        light_out: BoolProperty(name="Light parts stand out", default=True, update=_auto)\n        crisp: IntProperty(name="K  Crisp edges (%)", default=50, min=0, max=100, update=_auto,\n                           description="Flatter brick faces and sharper steps down into the joints")\n        patch: BoolProperty(name="Just a 1 m test patch (quick)", default=False, update=_auto,\n                            description="Carves only a 1 m square in the middle of each wall, to try settings")\n        show_colour: BoolProperty(name="Show the colours", default=True,\n                                  update=lambda self, context: None if self.busy else apply_colours(context),\n                                  description="Puts the colour photo on the walls, lined up with the "\n                                  "carving - just for looking, the shape doesn\'t change")\n        colour_picture: StringProperty(name="Colour", subtype=\'FILE_PATH\',\n                                       update=lambda self, context: None if self.busy else apply_colours(context),\n                                       description="The colour photo (found beside the height picture)")\n        allow_slow: BoolProperty(name="Allow the slow cut", default=False,\n                                 description="If the quick cut doesn\'t work on a wall (it isn\'t a closed "\n                                 "solid), use the slow one anyway - can take a long time on a big wall")\n        auto: BoolProperty(name="Update as I change", default=False,\n                           description="Carve again every time a setting changes (slow on big walls)")\n        k: FloatProperty(default=1.0)\n        out_obj: StringProperty(default="")\n        last_note: StringProperty(default="")\n        busy: BoolProperty(default=False)\n\n    class RW_OT_recarve(bpy.types.Operator):\n        bl_idname = "eddy_rw.recarve"\n        bl_label = "Re-carve the walls"\n        bl_description = "Carves the walls again from the plain walls, with these settings (hand edits are lost)"\n\n        def execute(self, context):\n            msg = recarve_all(context)\n            if msg:\n                self.report({\'WARNING\'}, msg)\n                return {\'CANCELLED\'}\n            keep_settings(context)\n            self.report({\'INFO\'}, context.scene.rw.last_note)\n            return {\'FINISHED\'}\n\n    class RW_OT_send(bpy.types.Operator):\n        bl_idname = "eddy_rw.send"\n        bl_label = "Send to IngeTrazo"\n        bl_description = ("Saves the carved walls as they are now (with any changes you made here) for "\n                          "\'Bring the walls back\' in IngeTrazo")\n\n        def execute(self, context):\n            st = context.scene.rw\n            walls = [ob for ob, _p in carved_walls(context.scene)]\n            if not walls or not st.out_obj:\n                self.report({\'WARNING\'}, "No carved walls to send")\n                return {\'CANCELLED\'}\n            if context.object is not None and context.object.mode != \'OBJECT\':\n                bpy.ops.object.mode_set(mode=\'OBJECT\')          # takes in edits made in Edit/Sculpt Mode\n            write_obj(st.out_obj, walls)\n            st.last_note = "Sent (settings kept) - click \'Bring the walls back\' in IngeTrazo."\n            keep_settings(context)\n            self.report({\'INFO\'}, st.last_note)\n            return {\'FINISHED\'}\n\n    class RW_PT_panel(bpy.types.Panel):\n        bl_label = "Realistic Wall"\n        bl_space_type = \'VIEW_3D\'\n        bl_region_type = \'UI\'\n        bl_category = "Realistic Wall"\n\n        def draw(self, context):\n            st = context.scene.rw\n            col = self.layout.column()\n            col.prop(st, "picture")\n            col.prop(st, "light_out")\n            row = col.row()\n            row.prop(st, "show_colour")\n            if st.show_colour:\n                col.prop(st, "colour_picture")\n            for name in ("depth", "tile_w", "tile_h", "detail", "blur", "off_x", "off_y", "mix", "seed",\n                         "max_points", "crisp"):\n                col.prop(st, name)\n            col.separator()\n            col.prop(st, "patch")\n            col.prop(st, "allow_slow")\n            col.prop(st, "auto")\n            col.operator("eddy_rw.recarve", icon=\'MOD_BOOLEAN\')\n            col.operator("eddy_rw.send", icon=\'EXPORT\')\n            if st.last_note:\n                col.label(text=st.last_note)\n            for ob, _p in carved_walls(context.scene):\n                if ob.get("rw_note"):\n                    box = col.box()\n                    box.label(text=ob.name, icon=\'MESH_PLANE\')\n                    box.label(text=ob["rw_note"])\n\n    CLASSES = (RW_Settings, RW_OT_recarve, RW_OT_send, RW_PT_panel)\n\n\ndef register():\n    for c in CLASSES:\n        try:\n            bpy.utils.unregister_class(c)\n        except Exception:\n            pass\n        bpy.utils.register_class(c)\n    bpy.types.Scene.rw = bpy.props.PointerProperty(type=RW_Settings)\n\n\ndef view_nicely():\n    try:\n        for win in bpy.context.window_manager.windows:\n            for area in win.screen.areas:\n                if area.type == "VIEW_3D":\n                    sp = area.spaces[0]\n                    sh = sp.shading\n                    sh.type = "SOLID"\n                    sh.show_cavity = True\n                    sh.cavity_type = "BOTH"\n                    sh.light = "STUDIO"\n                    if bpy.context.scene.rw.show_colour and bpy.context.scene.rw.colour_picture:\n                        sh.type = "MATERIAL"\n                    try:\n                        sp.show_region_ui = True             # the N sidebar, with the panel in it\n                    except Exception:\n                        pass\n                    with bpy.context.temp_override(window=win, area=area,\n                                                   region=[r for r in area.regions if r.type == "WINDOW"][0]):\n                        bpy.ops.view3d.view_selected()\n    except Exception as e:\n        print("view:", e)\n    return None\n\n\ndef run(job_path):\n    job = json.load(open(job_path))\n    register()\n    for ob in list(bpy.data.objects):                 # start from an empty scene\n        bpy.data.objects.remove(ob, do_unlink=True)\n    sc = bpy.context.scene\n    st = sc.rw\n    k = float(job.get("k") or 1.0)\n    st.busy = True                                    # don\'t carve while filling in the settings\n    st.k = k\n    st.picture = job["picture"]\n    st.depth = job["depth"] / k\n    st.tile_w, st.tile_h = job["tile_width"] / k, job["tile_height"] / k\n    st.off_x, st.off_y = job.get("offset_x", 0.0) / k, job.get("offset_y", 0.0) / k\n    st.detail = int(job.get("detail", 150))\n    st.blur = int(job.get("blur", 1))\n    st.mix = int(round(float(job.get("mix", 0.0)) * 100))\n    st.seed = int(job.get("seed", 1))\n    st.max_points = max(50, int(job.get("max_points", MAX_POINTS)) // 1000)\n    st.light_out = not job.get("invert")\n    st.crisp = int(round(float(job.get("crisp", 0.0)) * 100))\n    st.patch = bool(job.get("patch"))\n    st.allow_slow = bool(job.get("allow_slow"))\n    st.show_colour = bool(job.get("colour", True))\n    st.colour_picture = ""\n    st.out_obj = job.get("out_obj", "")\n    st.busy = False\n\n    plains = bpy.data.collections.get(PLAIN_COLL) or bpy.data.collections.new(PLAIN_COLL)\n    if plains.name not in sc.collection.children:\n        sc.collection.children.link(plains)\n    walls = []\n    for wall in job["walls"]:\n        me = build_mesh(wall["name"] + " (plain)", wall["verts"], [tuple(f) for f in wall["faces"]])\n        tidy_mesh(me)\n        gaps = close_gaps(me)\n        shade_flat(me)\n        print("Realistic Wall: %s - %s" % (wall["name"], "closed solid" if gaps == 0 else\n                                           "%d open edges left" % gaps))\n        plain = make_object(wall["name"] + " (plain)", me, plains)\n        plain["rw_open"] = gaps\n        ob = make_object(wall["name"], plain.data.copy())\n        ob["rw_plain"] = plain.name\n        ob["rw_normal"] = list(wall["normal"])\n        ob["rw_point"] = list(wall["point"])\n        walls.append(ob)\n    plains.hide_viewport = True\n    plains.hide_render = True\n    msg = recarve_all(bpy.context)\n    if msg:\n        print("Realistic Wall:", msg)\n    for ob in walls:\n        ob.select_set(True)\n    if walls:\n        bpy.context.view_layer.objects.active = walls[0]\n    if st.out_obj:\n        write_obj(st.out_obj, walls)\n        keep_settings(bpy.context, save_file=False)\n    # keep this script in the Blender file, so the panel is there when it\'s opened again\n    try:\n        src = open(__file__, encoding="utf-8").read()\n        t = bpy.data.texts.get("realistic_wall.py") or bpy.data.texts.new("realistic_wall.py")\n        t.clear()\n        t.write(src)\n        t.use_module = True\n    except Exception as e:\n        print("Realistic Wall: script not kept in the file:", e)\n    blend = job.get("out_blend")\n    if blend:\n        bpy.ops.wm.save_as_mainfile(filepath=blend)\n    bpy.app.timers.register(view_nicely, first_interval=0.5)\n    print("Realistic Wall: done")\n\n\nif IN_BLENDER:\n    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []\n    if __name__ == "__main__" and argv:\n        run(argv[0])\n    else:\n        register()             # opened again from a saved file: just put the panel back\n'


HEIGHT_WORDS = ("_disp", "_displacement", "_height", "_heightmap", "_bump")
COLOUR_WORDS = ("_diff", "_diffuse", "_col", "_color", "_colour", "_albedo", "_basecolor", "_base_color")


def height_picture_for(path):
    """For a colour photo (name_diff_4k.jpg) with its height picture beside it (name_disp_4k.png),
    the height picture's path - else None."""
    folder, fn = os.path.split(path)
    low = fn.lower()
    for w in COLOUR_WORDS:
        i = low.find(w)
        if i < 0:
            continue
        stem, rest = low[:i], os.path.splitext(low[i + len(w):])[0]
        try:
            names = os.listdir(folder)
        except Exception:
            return None
        best = None
        for other in names:
            o = other.lower()
            if not o.startswith(stem) or other == fn:
                continue
            for hw in HEIGHT_WORDS:
                if o.startswith(stem + hw):
                    score = (os.path.splitext(o[len(stem + hw):])[0] == rest,
                             o.endswith((".png", ".tif", ".tiff", ".exr")))
                    if best is None or score > best[0]:
                        best = (score, os.path.join(folder, other))
        return best[1] if best else None
    return None


def make_job(walls, values, picture, work_dir, keep_blend):
    """Writes everything Blender needs into a new folder. Returns (job file, script file, obj file)."""
    stamp = time.strftime("%Y-%m-%d %H%M%S")
    folder = os.path.join(work_dir, "Realistic wall %s" % stamp)
    os.makedirs(folder, exist_ok=True)
    k = min(w['k'] for w in walls)
    job = {
        'picture': picture,
        'depth': values['depth'] * k, 'tile_width': values['tile_w'] * k, 'tile_height': values['tile_h'] * k,
        'offset_x': values['off_x'] * k, 'offset_y': values['off_y'] * k,
        'detail': int(values['detail']), 'blur': int(values['blur']), 'invert': not values['light_out'],
        'mix': values.get('mix', 0) / 100.0, 'seed': int(values.get('seed', 1)),
        'max_points': int(values.get('max_pts', 600)) * 1000, 'k': k,
        'crisp': values.get('crisp', 0) / 100.0, 'patch': bool(values.get('patch')),
        'allow_slow': bool(values.get('allow_slow')), 'colour': bool(values.get('colour', True)),
        'out_obj': os.path.join(folder, "realistic wall.obj"),
        'out_blend': os.path.join(folder, "realistic wall.blend") if keep_blend else "",
        'walls': [],
    }
    used = {}
    for w in walls:
        pts, tris = wall_mesh_data(w)
        fd = w['polys'][w['face']]
        nm = w['name']
        used[nm] = used.get(nm, 0) + 1
        if used[nm] > 1:
            nm = "%s (%d)" % (nm, used[nm])
        job['walls'].append({'name': nm, 'verts': pts, 'faces': tris, 'normal': list(fd['n']),
                             'point': list(fd['pts'][0])})
    jp = os.path.join(folder, "job.json")
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(job, f)
    sp = os.path.join(folder, "realistic_wall_blender.py")
    with open(sp, "w", encoding="utf-8") as f:
        f.write(BLENDER_SCRIPT)
    return jp, sp, job['out_obj']


def open_blender(prog, script, job):
    import subprocess
    prog = _main_exe(prog)
    if not prog or not os.path.isfile(prog):
        return "The 3D program wasn't found - set where it is on the Program page.", True
    try:
        subprocess.Popen([prog, "--python", script, "--", job], cwd=os.path.dirname(job))
    except Exception as e:
        return "Couldn't open the 3D program: %s" % e, True
    return ("Opening the 3D program... It carves the walls, then shows them. A big wall can take a minute "
            "or two."), False


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

EDDY_TIPS = {
    "find walls in the selected building": "Lists the walls in the selected building or groups (or the whole "
                                            "model if nothing is selected), with a tick box for each.",
    "include inside walls": "List Floor Plan's inside walls (room dividers) too.",
    "use the inside face of each wall": "Carves the inside face of the walls (the side facing the middle of "
                                         "the building) instead of the outside.",
    "tick all": "Ticks every wall that hasn't been given a stone face yet.",
    "untick all": "Unticks every wall.",
    "choose folder...": "Pick the folder your wall pictures are in.",
    "open folder": "Opens the folder in Windows, so you can add pictures to it.",
    "light parts stand out": "Ticked: light parts of the picture stand out and dark parts (the joints) sink "
                             "in. Untick it if your picture is the other way round.",
    "carve the walls": "Sends the ticked walls and the picture to your 3D program, which opens with the "
                       "walls carved.",
    "bring the walls back": "Puts the carved walls into the model, where the plain walls are.",
    "find it": "Looks for the 3D program in the usual places (the newest version first).",
    "keep the 3d program's file": "Saves the 3D program's own file beside the carved walls, so you can open "
                                  "it again later.",
    "info": "Shows how to use it.",
    "open at the last page used": "Ticked, the window opens at the page you had open last time.",
}

INFO_TEXT = ("<b>How to use it</b><br>"
             "1. <b>Walls</b>: select the building (or nothing, for the whole model) and click Find. Tick the "
             "walls in the list, or click them in the picture on the left. Click the other side of a ticked "
             "wall to carve that side instead (the side that gets the stone is drawn brown).<br>"
             "2. <b>Picture</b>: choose the folder your wall pictures are in, and click a picture. Light parts "
             "stand out, dark parts (the joints) sink in. A height map (grey picture) works best, but a photo "
             "works too.<br>"
             "3. <b>Sizes</b>: how deep the joints go, and how big a piece of wall the picture shows (a picture "
             "called '2x2' is usually 2 x 2 m). 'Hide the repeats' stops the same stones showing over and "
             "over on a long wall.<br>"
             "4. Tick <b>1 m test patch</b> to try the settings quickly on a small square, then untick it and click "
             "<b>Carve the walls</b> for the whole wall. Your 3D program opens with the walls carved. Its <b>Realistic Wall</b> "
             "panel (press N) has the same settings: change them and click Re-carve, or tick 'Update as I "
             "change'. Edit or sculpt the walls there if you like, then click <b>Send to IngeTrazo</b>.<br>"
             "5. Back here, click <b>Bring the walls back</b> to put them in the model. The Program page says "
             "what happens to the plain walls: left, hidden, or replaced by the carved ones.<br><br>"
             "Anything that stands out of the wall (a window or sill built in) is left alone, with plain wall "
             "behind it. Sizes are real-world mm - Scale Studio takes it down to your model scale.")


# ---------------------------------------------------------------------------
# The walls, drawn so you can click them
# ---------------------------------------------------------------------------
class WallPicker(QWidget):
    """The walls found, drawn in 3D. Click a wall to tick it; click the other side of a ticked wall
    to carve that side. Drag to turn it round, the wheel to zoom."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.walls = []
        self.ticked = set()
        self.yaw, self.pitch, self.zoom = -35.0, 25.0, 1.0
        self.on_pick = None
        self._press = None
        self._drawn = []          # (path, wall index, face index), back to front
        self.setMinimumSize(320, 300)
        self.setMouseTracking(True)
        self.hover = None

    def set_walls(self, walls, ticked):
        self.walls = walls
        self.ticked = set(ticked)
        self.update()

    def _project(self):
        pts = [q for w in self.walls for p in w['polys'] for q in p['pts']]
        if not pts:
            return None
        c = _mid(pts)
        cy, sy = math.cos(math.radians(self.yaw)), math.sin(math.radians(self.yaw))
        cp, sp = math.cos(math.radians(self.pitch)), math.sin(math.radians(self.pitch))

        def rot(q):
            x, y, z = q[0] - c[0], q[1] - c[1], q[2] - c[2]
            x, y = x * cy - y * sy, x * sy + y * cy
            y, z = y * cp + z * sp, -y * sp + z * cp
            return x, y, z
        rp = [rot(q) for q in pts]
        span = max(max(abs(r[0]) for r in rp), max(abs(r[2]) for r in rp)) or 1.0
        s = min(self.width(), self.height() - 30) / (2.2 * span) * self.zoom
        ox, oy = self.width() / 2.0, (self.height() + 24) / 2.0
        return rot, s, ox, oy, (cy, sy, cp, sp)

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath, QBrush
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(236, 238, 240))
        p.setPen(QColor(70, 70, 70))
        p.drawText(QRectF(6, 4, self.width() - 12, 22), Qt.AlignLeft | Qt.AlignVCenter,
                   "Click a wall to tick it. Drag to turn, wheel to zoom." if self.walls else
                   "Click 'Find walls' on the Walls page to see the walls here.")
        pr = self._project()
        self._drawn = []
        if pr is None:
            p.end()
            return
        rot, s, ox, oy, (cy, sy, cp, sp) = pr
        view = (sy * cp * 0 + 0.0, 0.0, 0.0)
        items = []
        for wi, w in enumerate(self.walls):
            for fi, poly in enumerate(w['polys']):
                rr = [rot(q) for q in poly['pts']]
                depth = sum(r[1] for r in rr) / len(rr)
                n = poly['n']
                # the face's normal turned the same way (towards the viewer is -y after turning)
                nx, ny = n[0] * cy - n[1] * sy, n[0] * sy + n[1] * cy
                ny, nz = ny * cp + n[2] * sp, -ny * sp + n[2] * cp
                items.append((depth, wi, fi, rr, poly, ny))
        items.sort(key=lambda t: -t[0])          # far ones first
        for depth, wi, fi, rr, poly, facing in items:
            path = QPainterPath()
            path.setFillRule(Qt.OddEvenFill)
            path.moveTo(ox + rr[0][0] * s, oy - rr[0][2] * s)
            for r in rr[1:]:
                path.lineTo(ox + r[0] * s, oy - r[2] * s)
            path.closeSubpath()
            for h in poly['holes']:
                hh = [rot(q) for q in h]
                path.moveTo(ox + hh[0][0] * s, oy - hh[0][2] * s)
                for r in hh[1:]:
                    path.lineTo(ox + r[0] * s, oy - r[2] * s)
                path.closeSubpath()
            w = self.walls[wi]
            light = 0.65 + 0.35 * min(1.0, abs(facing))
            if wi in self.ticked and fi == w['face']:
                base = (176, 112, 62)                     # the side that gets the stone face
            elif wi in self.ticked:
                base = (222, 205, 170)
            elif w.get('done'):
                base = (160, 175, 160)
            else:
                base = (200, 200, 204)
            col = QColor(*[int(min(255, c * light)) for c in base])
            p.setBrush(QBrush(col))
            pen = QPen(QColor(40, 90, 200) if wi == self.hover else QColor(90, 90, 90),
                       2.0 if wi == self.hover else 0.8)
            p.setPen(pen)
            p.drawPath(path)
            if wi in self.ticked and fi == w['face']:
                p.setBrush(QBrush(QColor(90, 55, 30), Qt.DiagCrossPattern))
                p.setPen(Qt.NoPen)
                p.drawPath(path)
            self._drawn.append((path, wi, fi))
        p.end()

    def _hit(self, pos):
        for path, wi, fi in reversed(self._drawn):
            if path.contains(QPointF(pos)):
                return wi, fi
        return None

    def mousePressEvent(self, ev):
        self._press = (ev.position() if hasattr(ev, 'position') else ev.pos(), self.yaw, self.pitch)

    def mouseMoveEvent(self, ev):
        pos = ev.position() if hasattr(ev, 'position') else ev.pos()
        if self._press is not None and ev.buttons():
            p0, y0, t0 = self._press
            self.yaw = y0 + (pos.x() - p0.x()) * 0.5
            self.pitch = max(-89.0, min(89.0, t0 + (pos.y() - p0.y()) * 0.5))
            self.update()
            return
        hit = self._hit(pos)
        hv = hit[0] if hit else None
        if hv != self.hover:
            self.hover = hv
            self.setToolTip(self.walls[hv]['name'] if hv is not None else "")
            self.update()

    def mouseReleaseEvent(self, ev):
        pos = ev.position() if hasattr(ev, 'position') else ev.pos()
        if self._press is None:
            return
        p0 = self._press[0]
        self._press = None
        if abs(pos.x() - p0.x()) + abs(pos.y() - p0.y()) > 4:
            return                                     # it was a drag, not a click
        hit = self._hit(pos)
        if hit and self.on_pick:
            self.on_pick(*hit)

    def wheelEvent(self, ev):
        d = ev.angleDelta().y()
        self.zoom = max(0.3, min(8.0, self.zoom * (1.15 if d > 0 else 1 / 1.15)))
        self.update()


class KeyDrawing(QWidget):
    """What each lettered size is."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 490)

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath, QFont
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 248))
        dark = QPen(QColor(40, 40, 40), 1.2)
        red = QPen(QColor(200, 40, 40), 1.4)
        f = QFont(p.font())
        f.setBold(True)

        def letter(x, y, t):
            p.setFont(f)
            p.setPen(QColor(200, 40, 40))
            p.drawText(QRectF(x - 10, y - 10, 20, 20), Qt.AlignCenter, t)
            p.setFont(QFont())

        # ---- across the wall: the stone face cut in (A) ----
        p.setPen(dark)
        p.drawText(QRectF(10, 6, 300, 18), Qt.AlignLeft, "Looking down on the wall")
        x0, y0, W = 30.0, 40.0, 260.0
        path = QPainterPath()
        path.moveTo(x0, y0)
        import random
        rnd = random.Random(3)
        x = x0
        while x < x0 + W:
            seg = rnd.uniform(30, 55)
            x2 = min(x0 + W, x + seg)
            path.lineTo(x + 3, y0)
            path.lineTo(x + 6, y0 + 3)
            path.lineTo(x2 - 7, y0 + 3)
            path.lineTo(x2 - 3, y0)
            path.lineTo(x2, y0)
            if x2 < x0 + W:
                path.lineTo(x2, y0 + 14)
                path.lineTo(x2 + 4, y0 + 14)
                path.lineTo(x2 + 4, y0)
            x = x2 + 4
        path.lineTo(x0 + W, y0 + 60)
        path.lineTo(x0, y0 + 60)
        path.closeSubpath()
        p.setBrush(QColor(205, 195, 175))
        p.drawPath(path)
        p.setPen(red)
        jx = x0 + 60
        p.drawLine(QPointF(jx - 22, y0), QPointF(jx - 22, y0 + 14))
        p.drawLine(QPointF(jx - 26, y0), QPointF(jx - 18, y0))
        p.drawLine(QPointF(jx - 26, y0 + 14), QPointF(jx - 18, y0 + 14))
        letter(jx - 34, y0 + 7, "A")
        p.setPen(dark)
        p.drawText(QRectF(10, y0 + 66, 300, 34), Qt.AlignLeft | Qt.TextWordWrap,
                   "A  how deep the joints (the darkest parts of the picture) go.")

        # ---- the wall face: the picture repeated (B, C) and moved (F, G) ----
        top = 160.0
        p.drawText(QRectF(10, top, 300, 18), Qt.AlignLeft, "The wall face")
        fx, fy, fw, fh = 30.0, top + 30, 260.0, 170.0
        tw, th = 100.0, 80.0
        p.setBrush(QColor(228, 222, 210))
        p.setPen(dark)
        p.drawRect(QRectF(fx, fy, fw, fh))
        p.setPen(QPen(QColor(150, 140, 120), 1.0, Qt.DashLine))
        for i in range(1, 3):
            p.drawLine(QPointF(fx + i * tw, fy), QPointF(fx + i * tw, fy + fh))
        for j in range(1, 3):
            p.drawLine(QPointF(fx, fy + fh - j * th), QPointF(fx + fw, fy + fh - j * th))
        p.setBrush(QColor(176, 112, 62, 90))
        p.setPen(Qt.NoPen)
        p.drawRect(QRectF(fx, fy + fh - th, tw, th))
        p.setPen(red)
        p.drawLine(QPointF(fx, fy + fh + 12), QPointF(fx + tw, fy + fh + 12))
        letter(fx + tw / 2, fy + fh + 24, "B")
        p.drawLine(QPointF(fx - 12, fy + fh), QPointF(fx - 12, fy + fh - th))
        letter(fx - 22, fy + fh - th / 2, "C")
        p.setPen(dark)
        p.drawText(QRectF(10, fy + fh + 36, 310, 118), Qt.AlignLeft | Qt.TextWordWrap,
                   "B, C  how big a piece of wall one picture covers (shaded). It repeats across the "
                   "wall.\nF, G  move the picture along and up the wall.\nD  detail: points across one "
                   "picture.  E  smooths a grainy photo.\nH  hides the repeats (patches of a\nsecond copy).  I  a different set of patches.\nJ  most points per wall (limits D on a big wall).\nK  crisp edges: flatter faces, sharper joints.")
        p.end()


class TwoRowTabs(QWidget):
    """Pages with their tabs on two rows, so they all show without scrolling across.
    Works like a QTabWidget: addTab, setTabToolTip, currentIndex, setCurrentIndex, currentChanged."""
    try:
        from PySide6.QtCore import Signal as _Signal
        currentChanged = _Signal(int)
    except Exception:
        currentChanged = None

    def __init__(self, rows=2, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QGridLayout, QStackedWidget, QButtonGroup
        self._rows = rows
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self._grid = QGridLayout()
        self._grid.setSpacing(2)
        lay.addLayout(self._grid)
        self._stack = QStackedWidget()
        try:
            from PySide6.QtWidgets import QFrame
            self._stack.setFrameShape(QFrame.StyledPanel)
        except Exception:
            pass
        lay.addWidget(self._stack, 1)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons = []
        self._group.idClicked.connect(self.setCurrentIndex)

    def _relayout(self):
        n = len(self._buttons)
        per = max(1, -(-n // self._rows))         # tabs on each row
        for b in self._buttons:
            self._grid.removeWidget(b)
        for i, b in enumerate(self._buttons):
            self._grid.addWidget(b, i // per, i % per)

    def addTab(self, widget, title):
        b = QPushButton(title.replace("&&", "&"))
        b.setCheckable(True)
        b.setStyleSheet("QPushButton { padding: 3px 8px; }"
                        "QPushButton:checked { font-weight: bold; background-color: palette(base); "
                        "border: 1px solid palette(mid); border-bottom: 2px solid palette(highlight); }")
        i = len(self._buttons)
        self._group.addButton(b, i)
        self._buttons.append(b)
        self._stack.addWidget(widget)
        self._relayout()
        if i == 0:
            b.setChecked(True)
        return i

    def setTabToolTip(self, i, tip):
        if 0 <= i < len(self._buttons):
            self._buttons[i].setToolTip(tip)

    def tabText(self, i):
        return self._buttons[i].text() if 0 <= i < len(self._buttons) else ""

    def count(self):
        return len(self._buttons)

    def currentIndex(self):
        return self._stack.currentIndex()

    def setCurrentIndex(self, i):
        try:
            i = int(i)
        except Exception:
            return
        if not 0 <= i < len(self._buttons) or i == self._stack.currentIndex() and self._buttons[i].isChecked():
            return
        self._buttons[i].setChecked(True)
        self._stack.setCurrentIndex(i)
        try:
            self.currentChanged.emit(i)
        except Exception:
            pass


def _form(page):
    fl = QFormLayout(page)
    fl.setHorizontalSpacing(6)
    fl.setVerticalSpacing(4)
    return fl


class RealWallDialog(QDialog):
    CUSTOM = "-- Custom --"

    def __init__(self, viewport, tool=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.found = []
        self.user_presets = load_presets()
        self._busy = False
        self._job_obj = None
        self._job_started = 0.0
        st = load_settings()

        lay = QVBoxLayout(self)
        self.info_box = QLabel(INFO_TEXT)
        self.info_box.setWordWrap(True)
        self.info_box.setVisible(False)
        lay.addWidget(self.info_box)

        side = QHBoxLayout()
        lay.addLayout(side, 1)
        self.views = QTabWidget()
        self.picker = WallPicker()
        self.picker.on_pick = self.picked_in_view
        self.views.addTab(self.picker, "Walls")
        self.lbl_big = QLabel("No picture chosen yet.")
        self.lbl_big.setAlignment(Qt.AlignCenter)
        self.lbl_big.setMinimumSize(320, 300)
        self.views.addTab(self.lbl_big, "Picture")
        from PySide6.QtWidgets import QScrollArea
        ks = QScrollArea()
        ks.setWidgetResizable(True)
        ks.setWidget(KeyDrawing())
        self.views.addTab(ks, "Key (A, B, C...)")
        self.views.setTabToolTip(0, "The walls found. Click one to tick it; click the other side of a ticked "
                                    "wall to carve that side.")
        self.views.setTabToolTip(1, "The picture you've chosen.")
        self.views.setTabToolTip(2, "What each lettered size is.")
        side.addWidget(self.views, 1)

        self.tabs = TwoRowTabs(1)
        side.addWidget(self.tabs, 1)
        self._walls_page()
        self._picture_page(st)
        self._sizes_page()
        self._blender_page(st)
        tips = ["Find the walls and tick the ones that get a stone face.",
                "Choose the picture of a wall.",
                "How deep the joints go and how big the picture is on the wall.",
                "Where your 3D program is, and where the carved walls are saved."]
        for i, t in enumerate(tips):
            self.tabs.setTabToolTip(i, t)

        # ---- presets ----
        prow = QHBoxLayout()
        prow.addWidget(QLabel("Preset:"))
        self.cb_preset = QComboBox()
        try:
            self.cb_preset.setMinimumContentsLength(16)
            self.cb_preset.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        except Exception:
            pass
        prow.addWidget(self.cb_preset, 1)
        b_up = QPushButton("▲")
        b_up.setToolTip("Moves the preset you have open up the list.")
        b_dn = QPushButton("▼")
        b_dn.setToolTip("Moves the preset you have open down the list.")
        for b_ in (b_up, b_dn):
            b_.setFixedWidth(28)
            prow.addWidget(b_)
        self.btn_save = QPushButton("Save")
        b_saveas = QPushButton("Save as...")
        b_del = QPushButton("Delete")
        b_fold = QPushButton("Folder")
        for b_ in (self.btn_save, b_saveas, b_del, b_fold):
            prow.addWidget(b_)
        lay.addLayout(prow)

        brow = QHBoxLayout()
        self.btn_make = QPushButton("Carve the walls")
        self.btn_make.setDefault(True)
        self.btn_back = QPushButton("Bring the walls back")
        self.b_info = QPushButton("Info")
        self.b_info.setCheckable(True)
        self.b_info.toggled.connect(self.info_box.setVisible)
        self.cb_lasttab = QCheckBox("Open at the last page used")
        self.cb_lasttab.setChecked(bool(st.get('remember_tab', True)))
        b_close = QPushButton("Close")
        self.cb_patch = QCheckBox("1 m test patch")
        self.cb_patch.setToolTip("Carves just a 1 m square in the middle of each ticked wall - quick, to try the "
                                 "settings. Untick it for the whole wall.")
        self.cb_patch.setChecked(bool(st.get('patch')))
        self.cb_patch.toggled.connect(lambda on: save_settings(patch=bool(on)))
        brow.addWidget(self.btn_make)
        brow.addWidget(self.cb_patch)
        brow.addWidget(self.btn_back)
        brow.addStretch(1)
        brow.addWidget(self.b_info)
        brow.addWidget(self.cb_lasttab)
        brow.addWidget(b_close)
        lay.addLayout(brow)
        self.lbl_status = QLabel()
        self.lbl_status.setWordWrap(True)
        lay.addWidget(self.lbl_status)
        lay.setSpacing(4)
        lay.setContentsMargins(8, 8, 8, 8)

        self.refresh_presets()
        self.set_values(st)
        self.cb_preset.currentIndexChanged.connect(self.apply_preset)
        b_up.clicked.connect(lambda: self.move_preset(-1))
        b_dn.clicked.connect(lambda: self.move_preset(1))
        self.btn_save.clicked.connect(self.save_preset)
        b_saveas.clicked.connect(lambda: self.save_preset_as())
        b_del.clicked.connect(self.delete_preset)
        b_fold.clicked.connect(lambda: self._open_in_windows(PRESET_DIR))
        self.btn_make.clicked.connect(self.make_it)
        self.btn_back.clicked.connect(self.bring_back_clicked)
        b_close.clicked.connect(self.close)
        if self.cb_lasttab.isChecked():
            try:
                self.tabs.setCurrentIndex(int(st.get('tab', 0)))
            except Exception:
                pass
        self.tabs.currentChanged.connect(lambda i: save_settings(tab=int(i)))
        self.cb_lasttab.toggled.connect(lambda on: save_settings(remember_tab=bool(on)))
        last = st.get('last_preset')
        if last and last in self.preset_order():
            self.refresh_presets(select=last)
        # when Blender has finished, say so
        self._watch = QTimer(self)
        self._watch.timeout.connect(self.watch_job)
        self._watch.start(2000)
        if st.get('last_job') and os.path.isfile(st['last_job']):
            self._job_obj = st['last_job']

    # ---- pages ----
    def _page(self, title):
        from PySide6.QtWidgets import QScrollArea, QFrame
        pg = QWidget()
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setFrameShape(QFrame.NoFrame)
        sa.setWidget(pg)
        self.tabs.addTab(sa, title)
        return pg

    def _walls_page(self):
        from PySide6.QtWidgets import QAbstractItemView
        lay = QVBoxLayout(self._page("Walls"))
        info = QLabel("Select the building (or nothing, for the whole model) and click Find. Tick the walls "
                      "that get a stone face - here, or by clicking them in the picture on the left. The side "
                      "that gets the stone is drawn brown: click the other side of a ticked wall to swap.")
        info.setWordWrap(True)
        lay.addWidget(info)
        b_find = QPushButton("Find walls in the selected building")
        lay.addWidget(b_find)
        self.cb_inside_walls = QCheckBox("Include inside walls")
        self.cb_inside_faces = QCheckBox("Use the inside face of each wall")
        lay.addWidget(self.cb_inside_walls)
        lay.addWidget(self.cb_inside_faces)
        self.lst_walls = QListWidget()
        self.lst_walls.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lst_walls.setToolTip("Ticked walls get a stone face. Click a line to light the wall up in the model.")
        lay.addWidget(self.lst_walls, 1)
        row = QHBoxLayout()
        b_all = QPushButton("Tick all")
        b_none = QPushButton("Untick all")
        row.addWidget(b_all)
        row.addWidget(b_none)
        row.addStretch(1)
        lay.addLayout(row)
        self.lbl_walls = QLabel()
        self.lbl_walls.setWordWrap(True)
        lay.addWidget(self.lbl_walls)
        b_find.clicked.connect(self.find)
        self.cb_inside_walls.toggled.connect(lambda *_: self.find() if self.found else None)
        self.cb_inside_faces.toggled.connect(lambda *_: self.find() if self.found else None)
        b_all.clicked.connect(lambda: self._tick_all(True))
        b_none.clicked.connect(lambda: self._tick_all(False))
        self.lst_walls.itemChanged.connect(lambda *_: self._sync_picker())
        self.lst_walls.itemSelectionChanged.connect(self._light_up)

    def _picture_page(self, st):
        lay = QVBoxLayout(self._page("Picture"))
        info = QLabel("Choose the folder your wall pictures are in, then click a picture. Light parts stand "
                      "out, dark parts sink in.")
        info.setWordWrap(True)
        lay.addWidget(info)
        self.ed_folder = QLineEdit()
        self.ed_folder.setReadOnly(True)
        lay.addWidget(self.ed_folder)
        row = QHBoxLayout()
        b_choose = QPushButton("Choose folder...")
        b_open = QPushButton("Open folder")
        row.addWidget(b_choose)
        row.addWidget(b_open)
        row.addStretch(1)
        lay.addLayout(row)
        from PySide6.QtWidgets import QListView
        self.lst_pics = QListWidget()
        self.lst_pics.setViewMode(QListView.IconMode)
        self.lst_pics.setIconSize(QSize(96, 96))
        self.lst_pics.setGridSize(QSize(116, 128))
        self.lst_pics.setResizeMode(QListView.Adjust)
        self.lst_pics.setMovement(QListView.Static)
        self.lst_pics.setWordWrap(True)
        self.lst_pics.setToolTip("Click the picture to use.")
        lay.addWidget(self.lst_pics, 1)
        self.lbl_pic = QLabel("No picture chosen.")
        self.lbl_pic.setWordWrap(True)
        self.lbl_pic.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl_pic)
        self.cb_light = QCheckBox("Light parts stand out")
        lay.addWidget(self.cb_light)
        self.picture = st.get('picture', '')
        b_choose.clicked.connect(self.choose_folder)
        b_open.clicked.connect(lambda: self._open_in_windows(self.ed_folder.text()))
        self.lst_pics.itemClicked.connect(self.picture_clicked)
        self.set_folder(st.get('folder', ''))

    def _sizes_page(self):
        fl = _form(self._page("Sizes"))
        self.sp = {}

        def dbl(key, label, lo, hi, step, dec=0, suffix=" mm", tip=""):
            s = QDoubleSpinBox()
            s.setRange(lo, hi)
            s.setDecimals(dec)
            s.setSingleStep(step)
            s.setSuffix(suffix)
            s.setToolTip(tip)
            lab = QLabel(label)
            lab.setToolTip(tip)
            fl.addRow(lab, s)
            self.sp[key] = s

        def num(key, label, lo, hi, tip=""):
            s = QSpinBox()
            s.setRange(lo, hi)
            s.setToolTip(tip)
            lab = QLabel(label)
            lab.setToolTip(tip)
            fl.addRow(lab, s)
            self.sp[key] = s
        dbl('depth', "A   Depth of the joints", 1, 500, 5, 1,
            tip="How deep the darkest parts of the picture (the joints) are cut into the wall, in real mm. "
                "30 mm is about 0.4 mm on an OO model.")
        dbl('tile_w', "B   Picture covers - across", 50, 20000, 100,
            tip="How wide a piece of real wall the picture shows. A picture called '2x2' is usually 2000 mm. "
                "Bigger is better: the fewer times it repeats, the less it shows.")
        dbl('tile_h', "C   Picture covers - up", 50, 20000, 100,
            tip="How tall a piece of real wall the picture shows.")
        num('detail', "D   Detail (points across the picture)", 20, 2000,
            tip="How many points across one picture - the resolution. More is sharper but slower, and a "
                "bigger file. 150 is a point every 17 mm on a 2.5 m picture, 300 every 8 mm.")
        num('blur', "E   Smooth the picture", 0, 10,
            tip="Smooths a grainy photo before it's used. 0 for a clean height map.")
        dbl('off_x', "F   Move picture along", -20000, 20000, 50,
            tip="Slides the picture along the wall, to line the stones up with a corner or an opening.")
        dbl('off_y', "G   Move picture up", -20000, 20000, 50,
            tip="Slides the picture up the wall, to line a course up with the ground.")
        num('mix', "H   Hide the repeats (%)", 0, 100,
            tip="A small picture repeated across a big wall shows the same stones over and over. This "
                "mixes in a second copy (slid along and mirrored, courses kept level) in big random "
                "patches, so the repeats don't show. 0 = off.")
        num('seed', "I   Pattern number", 1, 999,
            tip="Change this for a different set of mixed-in patches.")
        num('max_pts', "J   Most points per wall (thousands)", 50, 20000,
            tip="Limits how many points a wall's stone face is made of, so the cut doesn't take too long. "
                "On a big wall this can bring the detail (D) down - the note below says when. Raise it if "
                "your PC can cope: 600 is quick, 3000 takes a few minutes.")
        num('crisp', "K   Crisp edges (%)", 0, 100,
            tip="Flatter brick and stone faces and sharper steps down into the joints, judged against the "
                "wall round each one (big hollows stay). 50 is a good start; 100 is very sharp.")
        self.lbl_detail = QLabel()
        self.lbl_detail.setWordWrap(True)
        fl.addRow(self.lbl_detail)
        for s in self.sp.values():
            s.valueChanged.connect(self.changed)

    def _blender_page(self, st):
        lay = QVBoxLayout(self._page("Program"))
        info = QLabel("Your 3D program carves the walls and opens with them, ready to look at. When it has "
                      "finished, click 'Bring the walls back' to put them in the model.")
        info.setWordWrap(True)
        lay.addWidget(info)
        lay.addWidget(QLabel("The 3D program that carves the walls:"))
        self.ed_blender = QLineEdit()
        self.ed_blender.setPlaceholderText("Not found yet - click Find it or Choose...")
        lay.addWidget(self.ed_blender)
        row = QHBoxLayout()
        b_find = QPushButton("Find it")
        b_pick = QPushButton("Choose...")
        b_pick.setToolTip("Pick the program yourself.")
        row.addWidget(b_find)
        row.addWidget(b_pick)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addWidget(QLabel("Carved walls are saved in:"))
        self.ed_work = QLineEdit()
        self.ed_work.setReadOnly(True)
        lay.addWidget(self.ed_work)
        row2 = QHBoxLayout()
        b_work = QPushButton("Choose...")
        b_work.setToolTip("Pick the folder the carved walls are saved in.")
        b_wopen = QPushButton("Open folder")
        row2.addWidget(b_work)
        row2.addWidget(b_wopen)
        row2.addStretch(1)
        lay.addLayout(row2)
        self.cb_keep = QCheckBox("Keep the 3D program's file")
        lay.addWidget(self.cb_keep)
        self.cb_slow = QCheckBox("Allow the slow cut")
        self.cb_slow.setToolTip("The quick cut needs each wall to be a closed solid. If it isn't, the slow cut "
                                "can be used instead - but on a big wall it can take a very long time, so it "
                                "only happens by itself on small walls unless this is ticked.")
        self.cb_slow.setChecked(bool(st.get('allow_slow')))
        self.cb_slow.toggled.connect(lambda on: save_settings(allow_slow=bool(on)))
        lay.addWidget(self.cb_slow)
        self.cb_colour = QCheckBox("Show the colours in the 3D program")
        self.cb_colour.setToolTip("Puts the colour photo (found beside the height picture) on the carved walls, "
                                  "lined up with the bricks - just for looking, the shape doesn't change.")
        self.cb_colour.setChecked(bool(st.get('colour', True)))
        self.cb_colour.toggled.connect(lambda on: save_settings(colour=bool(on)))
        lay.addWidget(self.cb_colour)
        lay.addWidget(QLabel("When the carved walls come back:"))
        self.cb_back = QComboBox()
        for label, key in BACK_MODES:
            self.cb_back.addItem(label, key)
        self.cb_back.setToolTip("What happens to the plain walls when 'Bring the walls back' brings in the carved "
                                "ones. Hide: they're hidden (Show/Hide shows them again). Replace: the carved wall "
                                "takes the plain wall's place in the building, with its name. Undo works for both.")
        i = max(0, self.cb_back.findData(st.get('back_mode', 'hide')))
        self.cb_back.setCurrentIndex(i)
        self.cb_back.currentIndexChanged.connect(lambda *_: save_settings(back_mode=self.cb_back.currentData()))
        lay.addWidget(self.cb_back)
        lay.addStretch(1)
        self.ed_blender.setText(find_blender(st.get('blender', '')))
        self.ed_work.setText(st.get('work_dir') or WORK_DIR)
        self.cb_keep.setChecked(bool(st.get('keep_blend', True)))
        b_find.clicked.connect(self.find_blender_clicked)
        b_pick.clicked.connect(self.pick_blender)
        b_work.clicked.connect(self.pick_work)
        b_wopen.clicked.connect(lambda: self._open_in_windows(self.ed_work.text()))
        self.ed_blender.editingFinished.connect(lambda: save_settings(blender=self.ed_blender.text().strip()))
        self.cb_keep.toggled.connect(lambda on: save_settings(keep_blend=bool(on)))

    # ---- walls ----
    def find(self):
        scene = getattr(self.viewport, 'scene', None)
        if scene is None:
            return
        save_settings(inside_walls=self.cb_inside_walls.isChecked(), inside_faces=self.cb_inside_faces.isChecked())
        try:
            self.found = find_walls(scene, self.cb_inside_walls.isChecked(), self.cb_inside_faces.isChecked())
        except Exception as e:
            self.found = []
            QMessageBox.warning(self, PLUGIN_NAME, "Could not look for walls:\n%s" % e)
        self.lst_walls.blockSignals(True)
        self.lst_walls.clear()
        for i, w in enumerate(self.found):
            txt = "%s  -  %.0f x %.0f mm" % (w['name'], w['length'], w['height'])
            if w['done']:
                txt += "  - has a stone face"
            it = QListWidgetItem(txt)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Unchecked)
            self.lst_walls.addItem(it)
        self.lst_walls.blockSignals(False)
        if self.found:
            self.lbl_walls.setText("Found %d wall%s. Tick the ones to carve." % (
                len(self.found), "" if len(self.found) == 1 else "s"))
        else:
            self.lbl_walls.setText("No walls found. Select the building (the group holding the walls) and "
                                   "click Find again, or click Find with nothing selected for the whole model.")
        self._sync_picker()
        self.views.setCurrentIndex(0)

    def _tick_all(self, on):
        self.lst_walls.blockSignals(True)
        for i in range(self.lst_walls.count()):
            w = self.found[i] if i < len(self.found) else None
            self.lst_walls.item(i).setCheckState(
                Qt.Checked if on and w is not None and not w['done'] else Qt.Unchecked)
        self.lst_walls.blockSignals(False)
        self._sync_picker()

    def ticked(self):
        return [i for i in range(self.lst_walls.count())
                if self.lst_walls.item(i).checkState() == Qt.Checked and i < len(self.found)]

    def _sync_picker(self):
        self.picker.set_walls(self.found, self.ticked())
        self.changed()

    def picked_in_view(self, wi, fi):
        """A click on a wall in the picture: ticks it, or swaps the side, or unticks it."""
        w = self.found[wi]
        it = self.lst_walls.item(wi)
        if it.checkState() != Qt.Checked:
            it.setCheckState(Qt.Checked)
            if fi in (w['front'], w['back']):
                w['face'] = fi
        elif fi == w['face']:
            it.setCheckState(Qt.Unchecked)
        elif fi in (w['front'], w['back']) or abs(w['polys'][fi]['area']) > 0.2 * abs(w['polys'][w['face']]['area']):
            w['face'] = fi                    # carve this side instead
            self._sync_picker()
        else:
            it.setCheckState(Qt.Unchecked)
        self.lst_walls.setCurrentRow(wi)

    def _light_up(self):
        scene = getattr(self.viewport, 'scene', None)
        rows = sorted({self.lst_walls.row(it) for it in self.lst_walls.selectedItems()})
        if scene is None or not rows:
            return
        try:
            scene.selection.clear()
            for r in rows:
                if r < len(self.found):
                    w = self.found[r]
                    scene.selection.add(w['polys'][w['face']]['obj'])
            self.viewport.notify_scene_changed()
        except Exception:
            try:
                self.viewport.update()
            except Exception:
                pass

    # ---- the picture ----
    def choose_folder(self):
        start = self.ed_folder.text() or os.path.join(os.path.expanduser("~"), "Pictures")
        try:
            opts = QFileDialog.Option.DontUseNativeDialog | QFileDialog.Option.ShowDirsOnly
        except Exception:
            opts = QFileDialog.DontUseNativeDialog | QFileDialog.ShowDirsOnly
        d = QFileDialog.getExistingDirectory(self, "The folder your wall pictures are in", start, opts)
        if d:
            self.set_folder(os.path.normpath(d))
            save_settings(folder=os.path.normpath(d))

    def set_folder(self, folder):
        from PySide6.QtGui import QIcon, QPixmap
        self.ed_folder.setText(folder or "")
        self.lst_pics.clear()
        if not folder or not os.path.isdir(folder):
            self._show_picture()
            return
        try:
            names = sorted(fn for fn in os.listdir(folder) if fn.lower().endswith(PICTURE_TYPES))
        except Exception:
            names = []
        for fn in names:
            path = os.path.join(folder, fn)
            it = QListWidgetItem(os.path.splitext(fn)[0])
            it.setData(Qt.UserRole, path)
            it.setToolTip(path)
            pm = QPixmap(path)
            if not pm.isNull():
                it.setIcon(QIcon(pm.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
            self.lst_pics.addItem(it)
            if os.path.normcase(path) == os.path.normcase(self.picture or ""):
                it.setSelected(True)
        if not names:
            self.lst_pics.addItem(QListWidgetItem("(no pictures in this folder)"))
        self._show_picture()

    def picture_clicked(self, it):
        path = it.data(Qt.UserRole)
        if not path:
            return
        hp = height_picture_for(path)
        if hp:
            self.say("That's a colour photo - using its height picture %s instead (it gives the bricks their "
                     "proper depth)." % os.path.basename(hp))
            path = hp
            for i in range(self.lst_pics.count()):
                x = self.lst_pics.item(i)
                x.setSelected(os.path.normcase(x.data(Qt.UserRole) or "") == os.path.normcase(hp))
        self.picture = path
        save_settings(picture=path)
        self._show_picture()
        self.views.setCurrentIndex(1)

    def _show_picture(self):
        from PySide6.QtGui import QPixmap
        if self.picture and os.path.isfile(self.picture):
            self.lbl_pic.setText("Picture: %s" % os.path.basename(self.picture))
            pm = QPixmap(self.picture)
            if pm.isNull():
                self.lbl_big.setPixmap(QPixmap())
                self.lbl_big.setText("%s\n\n(IngeTrazo can't show this kind of picture, but the 3D program can "
                                     "use it.)" % os.path.basename(self.picture))
            else:
                self.lbl_big.setPixmap(pm.scaled(360, 360, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.lbl_pic.setText("No picture chosen.")
            self.lbl_big.setPixmap(QPixmap())
            self.lbl_big.setText("No picture chosen yet.")

    # ---- Blender ----
    def find_blender_clicked(self):
        p = find_blender("")
        if p:
            self.ed_blender.setText(p)
            save_settings(blender=p)
            self.say("Found it: %s" % p)
        else:
            self.say("It wasn't found in the usual places - click Choose... and pick the program.", True)

    def pick_blender(self):
        start = self.ed_blender.text() or os.environ.get("ProgramFiles", "")
        try:
            opt = QFileDialog.Option.DontUseNativeDialog
        except Exception:
            opt = QFileDialog.DontUseNativeDialog
        p, _f = QFileDialog.getOpenFileName(self, "The 3D program", start, "Programs (*.exe);;All files (*)",
                                            options=opt)
        if p:
            p = _main_exe(os.path.normpath(p))
            self.ed_blender.setText(p)
            save_settings(blender=p)

    def pick_work(self):
        try:
            opts = QFileDialog.Option.DontUseNativeDialog | QFileDialog.Option.ShowDirsOnly
        except Exception:
            opts = QFileDialog.DontUseNativeDialog | QFileDialog.ShowDirsOnly
        d = QFileDialog.getExistingDirectory(self, "Save the carved walls in", self.ed_work.text(), opts)
        if d:
            self.ed_work.setText(os.path.normpath(d))
            save_settings(work_dir=os.path.normpath(d))

    def make_it(self):
        walls = [self.found[i] for i in self.ticked()]
        if not walls:
            self.tabs.setCurrentIndex(0)
            QMessageBox.information(self, PLUGIN_NAME, "Tick the walls to carve first (Walls page), or click "
                                                       "them in the picture on the left.")
            return
        if not self.picture or not os.path.isfile(self.picture):
            self.tabs.setCurrentIndex(1)
            QMessageBox.information(self, PLUGIN_NAME, "Choose a picture of a wall first (Picture page).")
            return
        prog = self.ed_blender.text().strip() or find_blender("")
        if not prog or not os.path.isfile(prog):
            self.tabs.setCurrentIndex(3)
            QMessageBox.information(self, PLUGIN_NAME, "The 3D program wasn't found. Click Find it, or "
                                                       "Choose... and pick it (Program page).")
            return
        vals = self.get_values()
        save_settings(**vals)
        vals['patch'] = self.cb_patch.isChecked()
        vals['allow_slow'] = self.cb_slow.isChecked()
        vals['colour'] = self.cb_colour.isChecked()
        try:
            job, script, obj = make_job(walls, vals, self.picture, self.ed_work.text() or WORK_DIR,
                                        self.cb_keep.isChecked())
        except Exception as e:
            self.say("Couldn't get the walls ready: %s" % e, True)
            return
        msg, warn = open_blender(prog, script, job)
        self.say(msg, warn)
        if not warn:
            self._job_obj = obj
            self._job_started = time.time()
            self._seen = None
            save_settings(last_job=obj)

    def watch_job(self):
        if not self._job_obj:
            return
        try:
            if not os.path.isfile(self._job_obj):
                return
            t = os.path.getmtime(self._job_obj)
        except Exception:
            return
        if self._job_started and t >= self._job_started - 1:
            self._job_started = 0.0
            self._seen = t
            self.say("The walls are carved. Have a look in the 3D program (its Realistic Wall panel, N key, "
                     "changes them there), then click 'Bring the walls back' to put them in the model.")
        elif not self._job_started and getattr(self, '_seen', None) and t > self._seen + 0.5:
            self._seen = t
            self.say("The walls were sent again from the 3D program. Click 'Bring the walls back' to put "
                     "them in the model.")

    def bring_back_clicked(self):
        path = self._job_obj
        if not path or not os.path.isfile(path):
            try:
                opt = QFileDialog.Option.DontUseNativeDialog
            except Exception:
                opt = QFileDialog.DontUseNativeDialog
            path, _f = QFileDialog.getOpenFileName(self, "Carved walls to bring back", self.ed_work.text(),
                                                   "Carved walls (*.obj)", options=opt)
            if not path:
                if self._job_started:
                    self.say("The 3D program hasn't finished carving yet - wait for it, then try again.", True)
                return
        self.say("Bringing the walls back... (a big wall can take a little while)")
        try:
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
        except Exception:
            pass
        msg, warn = bring_back(self.viewport, path, self.cb_back.currentData() or 'leave')
        if not warn and self._take_settings(path):
            msg += " The settings from the 3D program are kept here for next time."
        self.say(msg, warn)
        if not warn:
            self.find() if self.found else None

    def _take_settings(self, obj_path):
        """Takes in the settings the 3D program left beside the carved walls (changed there with its
        Realistic Wall panel). True if there were some."""
        try:
            with open(os.path.join(os.path.dirname(obj_path), "realistic wall settings.json"), "r",
                      encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            return False
        if not isinstance(d, dict):
            return False
        vals = {k: d[k] for k in DEFAULTS if k in d}
        self.set_values(vals)
        keep = dict(vals)
        pic = d.get('picture')
        if pic and os.path.isfile(pic):
            self.picture = pic
            keep['picture'] = pic
            self._show_picture()
        for key, box in (('colour', getattr(self, 'cb_colour', None)), ('allow_slow', getattr(self, 'cb_slow', None))):
            if key in d and box is not None:
                box.setChecked(bool(d[key]))
                keep[key] = bool(d[key])
        save_settings(**keep)
        return True

    def say(self, text, bad=False):
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet("color: #b00;" if bad else "color: #050;")

    def _open_in_windows(self, folder):
        try:
            if folder:
                os.makedirs(folder, exist_ok=True)
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        except Exception as e:
            QMessageBox.information(self, PLUGIN_NAME, "Folder:\n%s\n\n(%s)" % (folder, e))

    # ---- values ----
    def get_values(self):
        v = {k: (float(s.value()) if isinstance(s, QDoubleSpinBox) else int(s.value())) for k, s in self.sp.items()}
        v['light_out'] = self.cb_light.isChecked()
        return v

    def set_values(self, d):
        self._busy = True
        for k, s in self.sp.items():
            if k in d and d[k] is not None:
                s.setValue(d[k])
        if 'light_out' in d:
            self.cb_light.setChecked(bool(d['light_out']))
        if 'inside_walls' in d:
            self.cb_inside_walls.setChecked(bool(d['inside_walls']))
        if 'inside_faces' in d:
            self.cb_inside_faces.setChecked(bool(d['inside_faces']))
        self._busy = False
        self.changed()

    def changed(self, *_):
        if self._busy:
            return
        n = len(self.ticked()) if hasattr(self, 'lst_walls') else 0
        try:
            self._detail_note()
        except Exception:
            pass
        try:
            v = self.get_values()
            self.btn_make.setToolTip("Carves %d ticked wall%s %.0f mm deep, with the picture covering %.0f x %.0f mm."
                                     % (n, "" if n == 1 else "s", v['depth'], v['tile_w'], v['tile_h']))
        except Exception:
            pass

    def _detail_note(self):
        """Says what detail the ticked walls really get (a big wall can be held back by J)."""
        if not hasattr(self, 'lbl_detail'):
            return
        v = self.get_values()
        walls = [self.found[i] for i in self.ticked()]
        if not walls:
            self.lbl_detail.setText("Tick some walls to see the detail they'll get.")
            return
        cap = v['max_pts'] * 1000.0
        worst, worst_w = None, None
        for w in walls:
            nu = w['length'] / v['tile_w'] * v['detail'] + 1
            nv = w['height'] / v['tile_h'] * v['detail'] + 1
            got = v['detail'] * min(1.0, math.sqrt(cap / max(nu * nv, 1.0)))
            if worst is None or got < worst:
                worst, worst_w = got, w
        spacing = v['tile_w'] / max(worst, 1.0)
        printed = (" On the print that's %.2f mm at OO (1:76.2), %.2f mm at HO (1:87), %.2f mm at N (1:148) "
                   "- a resin printer shows about 0.05 mm, a filament printer about 0.4 mm."
                   % (spacing / 76.2, spacing / 87.0, spacing / 148.0))
        if worst < v['detail'] - 0.5:
            need = int(math.ceil((worst_w['length'] / v['tile_w'] * v['detail'] + 1) *
                                 (worst_w['height'] / v['tile_h'] * v['detail'] + 1) / 1000.0))
            self.lbl_detail.setText("<span style='color:#b00'>Detail is held back to about %d on '%s' (a point "
                                    "every %.0f mm) by J. For the full %d, set J to %d.</span>"
                                    % (worst, worst_w['name'], spacing, v['detail'], need) + printed)
        else:
            self.lbl_detail.setText("Every ticked wall gets the full detail: a point every %.0f mm of real wall."
                                    % spacing + printed)

    # ---- presets ----
    def all_presets(self):
        d = dict(BUILTIN_PRESETS)
        d.update(self.user_presets)
        return d

    def preset_order(self):
        names = list(BUILTIN_PRESETS) + sorted(n for n in self.user_presets if n not in BUILTIN_PRESETS)
        order = [n for n in load_settings().get('preset_order', []) if n in names]
        return order + [n for n in names if n not in order]

    def move_preset(self, step):
        name = self.cb_preset.currentData()
        if not name:
            return
        order = self.preset_order()
        i = order.index(name)
        j = i + step
        if 0 <= j < len(order):
            order[i], order[j] = order[j], order[i]
            save_settings(preset_order=order)
            self.refresh_presets(select=name)

    def refresh_presets(self, select=None):
        self.cb_preset.blockSignals(True)
        self.cb_preset.clear()
        self.cb_preset.addItem(self.CUSTOM, None)
        for name in self.preset_order():
            self.cb_preset.addItem(name + ("  (built-in)" if name in BUILTIN_PRESETS else ""), name)
        if select:
            for i in range(self.cb_preset.count()):
                if self.cb_preset.itemData(i) == select:
                    self.cb_preset.setCurrentIndex(i)
                    break
        self.cb_preset.blockSignals(False)

    def apply_preset(self, _idx=None):
        name = self.cb_preset.currentData()
        save_settings(last_preset=name or None)
        p = self.all_presets().get(name) if name else None
        if p:
            self.set_values({k: v for k, v in p.items() if k in DEFAULTS})

    def save_preset(self):
        name = self.cb_preset.currentData()
        if name and name in self.user_presets and name not in BUILTIN_PRESETS:
            if self.save_preset_as(quiet_name=name):
                self.btn_save.setText("Saved")
                QTimer.singleShot(1500, lambda: self.btn_save.setText("Save"))
        else:
            self.save_preset_as(prefill=(name + " (my copy)") if name else "")

    def save_preset_as(self, prefill="", quiet_name=None):
        if quiet_name:
            name, ok = quiet_name, True
        else:
            name, ok = QInputDialog.getText(self, "Save preset", "Preset name:", QLineEdit.Normal, prefill)
        name = (name or "").strip()
        if not ok or not name:
            return False
        if name in BUILTIN_PRESETS:
            QMessageBox.warning(self, "Name in use", "That name belongs to a built-in preset. Choose another name.")
            return False
        if name in self.user_presets and not quiet_name:
            if QMessageBox.question(self, "Overwrite preset",
                                    "Preset '%s' already exists. Overwrite it?" % name) != QMessageBox.Yes:
                return False
        try:
            save_preset_file(name, self.get_values())
        except Exception as e:
            QMessageBox.warning(self, "Save failed", "Could not save the preset:\n%s" % e)
            return False
        self.user_presets = load_presets()
        self.refresh_presets(select=name)
        save_settings(last_preset=name)
        return True

    def delete_preset(self):
        name = self.cb_preset.currentData()
        if not name or name in BUILTIN_PRESETS or name not in self.user_presets:
            QMessageBox.information(self, PLUGIN_NAME, "Pick one of your own presets to delete "
                                                       "(built-in presets can't be deleted).")
            return
        if QMessageBox.question(self, "Delete preset", "Delete preset '%s'?" % name) != QMessageBox.Yes:
            return
        try:
            delete_preset_file(name)
        except Exception as e:
            QMessageBox.warning(self, PLUGIN_NAME, "Could not delete it:\n%s" % e)
        self.user_presets = load_presets()
        self.refresh_presets()


class RealisticWallTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Shift+W"
    description = ("A real stone or brick face on your walls from a picture of a wall: pick the walls and the "
                   "picture, and your 3D program carves them.")

    _dialog = None

    def on_activate(self, viewport):
        dlg = RealisticWallTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.viewport = viewport
                    dlg.raise_()
                    dlg.activateWindow()
                    return
            except Exception:
                pass
        dialog = RealWallDialog(viewport, tool=self, parent=viewport)
        RealisticWallTool._dialog = dialog

        def closed(*_):
            RealisticWallTool._dialog = None
        dialog.finished.connect(closed)
        eddy_window(dialog, PLUGIN_NAME, EDDY_TIPS, place=True)
        dialog.show()
        dialog.find()

    def on_deactivate(self, viewport):
        pass
