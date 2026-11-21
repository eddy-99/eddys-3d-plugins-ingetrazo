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
Version 1.8: what comes back is thinned to 'L Most faces brought back' (150 thousand to start) so
IngeTrazo doesn't seize up - the wall in the 3D program keeps all its detail; a warning before
bringing in a very big wall.
Version 1.9: thinning joins the flat faces up first (no detail lost), and only takes points out of
the rest if it's still too big - more detail kept in the joints for the same number of faces.
Version 2.0: 'Show what goes back' in the 3D program's panel shows the thinned copy, and changing L
redoes it there and then - lower L until you're happy with how it looks.
Version 2.1: the stone looks smooth in IngeTrazo - its gentle edges are softened (as Gutters & Downpipes
does), so no black mesh of lines, while the edges of the bricks stay crisp; M Smooth the stone smooths
the joints and broken bits of what goes back.
Version 2.2: 'Send to my printer' in the 3D program's panel - the carved walls at full detail, at
Scale Studio's scale, laid flat, straight into your printer's slicer (no need to bring them back).
Version 2.3: 'Send to my printer' always prints the full detail - M Smoothing is only used for what goes
back to IngeTrazo.
Version 2.4: 'Get wall pictures online...' on the Picture page - browse Poly Haven's free (CC0) wall,
brick and stone pictures, download one into your wall pictures folder, and it's picked, with B and C
set to the size of wall it shows.
Version 2.5: the carved wall keeps the colours of the plain wall - windows, doors and frames built into
it come back in their own colours, and the stone in the wall's colour.
Version 2.6: walls with windows, doors and sills built in are carved - the wall itself is carved and the
pieces built onto it put back (the quick cut couldn't work with them on); the slow cut is used by itself
on walls up to about a gable end's size.
Version 2.7: windows and doors built into a wall are their own part in the 3D program - not carved, no
photo on them, quicker - and still come back (and print) with the wall; the plain wall kept behind them
follows their real outline (no blocky steps round an arch).
Version 2.8: the online pictures stay tidy in their rows while they load (each has its own square), and
floors and pavements are left out of the wall lists.
Version 2.9: windows and doors built into a wall are told apart by their colour (painted differently
from the wall), so they're kept off the stone and out of the cut even where they share corners with the
wall - quick again, and no photo on them.
Version 3.0: a new way of carving - the wall's front face is rebuilt with the stone shape (joined to its
edges and openings), instead of cutting a block out of the wall. It doesn't need the wall to be a closed
solid, so walls with windows built in carve in seconds, not minutes. The old cut is kept as a backup.
Version 3.1: no more straight lines across the stone (from how the flat face had been split into
triangles) - only the wall's real outline and openings are kept, the stone fills the rest freely.
Version 3.2: windows and doors are kept off the stone again (the wall had a few doubled-up triangles,
which threw the window marks out); quicker into the 3D program - the copy for IngeTrazo is only made
when you click Send to IngeTrazo, the 3D program's file is saved once the wall is showing, no points are
made behind windows, and the colours are worked out with a sixth of the work.
Version 3.3: in the 3D program's panel the picture settings are in their own Picture section, rolled up
to start with.
Version 3.4: a simpler window - pick the walls and the picture here (with how big a piece of wall the
picture shows), carve, and do all the fine tuning in the 3D program's panel, where you can see it. The
settings used there last are taken in for the next carve.
Version 3.5: window and door openings go right through the wall again (they were being filled in when
the windows were lifted off for carving).
Version 3.6: you pick the building to work on (a Building list at the top of the Walls page - the
selected one is picked for you), so with several models in the scene only that building's walls are
listed, and each wall's outside face is worked out from the middle of its own building.
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
VERSION = "4.1"             # shown in the window title, so you can tell which file is loaded

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
        'patch': False, 'allow_slow': False, 'colour': True, 'back_mode': 'hide', 'max_faces': 150, 'smooth': 2,
        'inside_walls': False, 'inside_faces': False, 'tab': 0, 'remember_tab': True, 'last_preset': None,
        'preset_order': [], 'last_job': '', 'hidden_pics': []}


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


def _model_size(top):
    """How big a model is (the floor area its box covers), to tell a building from a figure beside it."""
    lo, hi = [1e18] * 3, [-1e18] * 3
    try:
        for g, m in _placements(top):
            mesh = getattr(g, 'mesh', None)
            for f in _items(getattr(mesh, 'faces', None)):
                for v in _items(getattr(f, 'vertices', None)):
                    p = _pos3(v)
                    if p is None:
                        continue
                    xyz = _wmap(m, p)
                    for k in range(3):
                        lo[k] = min(lo[k], xyz[k])
                        hi[k] = max(hi[k], xyz[k])
    except Exception:
        return 0.0
    if hi[0] < lo[0]:
        return 0.0
    d = sorted(hi[k] - lo[k] for k in range(3))
    return d[1] * d[2]


def building_of(scene, g):
    """The building (top-level group of the model) that a group is in, or None."""
    for t in _items(getattr(scene, 'groups', None)):
        if any(x is g for x, _ in _placements(t)):
            return t
    return None


def find_walls(scene, inside_walls=False, inside_faces=False, top=None):
    """The walls of one building (top), or of the selected building or groups (the whole model if
    nothing is selected). [dict(name, group, m, polys, front, back, face, k, length, height, done)]"""
    sel = _items(getattr(scene, 'selection', None))
    picked = [e for e in sel if getattr(e, 'mesh', None) is not None or _kids(e)]
    tops = _items(getattr(scene, 'groups', None))
    if top is not None:
        tops, picked = [top], []
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


def _paint_key(f):
    a = getattr(f, 'attrs', None)
    if not isinstance(a, dict):
        return None
    c = a.get('color') or a.get('colour')
    try:
        c = tuple(round(float(x), 3) for x in c) if c is not None else None
    except Exception:
        c = str(c)
    m = a.get('material')
    return (c, str(m) if m is not None else None)


def wall_mesh_data(wall):
    """The wall's triangles in the world, as (points, triangles, extra) with shared corners. extra is
    1 for a triangle of something built onto the wall - painted differently from the wall's face
    (windows, doors, sills, arches) - else 0."""
    pts, tris, extra, index = [], [], [], {}
    m = wall['m']
    main = _paint_key(wall['polys'][wall['face']]['obj'])

    def key_of(p):
        return (round(p[0], 7), round(p[1], 7), round(p[2], 7))
    for f in _items(getattr(wall['mesh'], 'faces', None)):
        is_extra = 1 if _paint_key(f) != main else 0
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
                extra.append(is_extra)
    return pts, tris, extra


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


def _flat2(pts, n):
    """Corners turned into 2D on the face's own plane (dropping the biggest part of its normal)."""
    ax = max(range(3), key=lambda i: abs(n[i]))
    a, b = [i for i in range(3) if i != ax]
    return [(q[a], q[b]) for q in pts]


def _inside(x, y, poly):
    ins = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-30) + xi:
            ins = not ins
        j = i
    return ins


def copy_colours(plain, new_faces, verts):
    """Gives each face of the carved wall the colour (face paint) it had on the plain wall: faces
    that are still where they were (windows, doors, frames, the wall's ends) take their own colour,
    the new stone takes the wall's. Returns how many faces were given a colour."""
    g, m = plain
    orig, biggest = [], None
    for f in _items(getattr(getattr(g, 'mesh', None), 'faces', None)):
        a = getattr(f, 'attrs', None)
        a = dict(a) if isinstance(a, dict) else {}
        pts = [_wmap(m, q) for q in (_pos3(v) for v in _items(getattr(f, 'vertices', None))) if q is not None]
        if len(pts) < 3:
            continue
        holes = [[_wmap(m, q) for q in (_pos3(v) for v in _items(h)) if q is not None]
                 for h in _items(getattr(f, 'holes', None))]
        nv = _newell(pts)
        area = _vlen(nv) / 2.0
        n = _unit(nv)
        orig.append((n, _vdot(n, pts[0]), _flat2(pts, n), [_flat2(h, n) for h in holes if len(h) >= 3], a))
        if biggest is None or area > biggest[0]:
            biggest = (area, a)
    if not orig:
        return 0
    allq = [q for o in orig for q in o[2]]
    span = max(max(q[i] for q in allq) - min(q[i] for q in allq) for i in range(2)) or 1.0
    tol = span * 1e-4
    buckets = {}
    for o in orig:
        key = (round(o[0][0], 2), round(o[0][1], 2), round(o[0][2], 2), round(o[1] / tol))
        buckets.setdefault(key, []).append(o)
    wall_paint = biggest[1] if biggest else {}
    done = 0
    for nf, idx in new_faces:
        pts = [verts[i] for i in idx]
        n = _unit(_newell(pts))
        d = _vdot(n, pts[0])
        c = (sum(q[0] for q in pts) / len(pts), sum(q[1] for q in pts) / len(pts), sum(q[2] for q in pts) / len(pts))
        paint = None
        k0 = (round(n[0], 2), round(n[1], 2), round(n[2], 2))
        for dk in (0, -1, 1):
            for o in buckets.get(k0 + (round(d / tol) + dk,), ()):
                cx, cy = _flat2([c], o[0])[0]
                if _inside(cx, cy, o[2]) and not any(_inside(cx, cy, h) for h in o[3]):
                    paint = o[4]
                    break
            if paint is not None:
                break
        if paint is None:
            paint = wall_paint
        if paint:
            try:
                nf.attrs = dict(paint)
                done += 1
            except Exception:
                pass
    return done


def soften_edges(mesh, max_angle=30.0):
    """Softens (hides and smooths) the edges between faces meeting at less than max_angle degrees -
    the crinkles in the stone - so it looks smooth, not a black mesh of lines. The edges round the
    bricks and joints, and the wall's corners, stay sharp. (As Gutters & Downpipes does it.)"""
    def val(o, name):
        x = getattr(o, name, None)
        if callable(x):
            try:
                x = x()
            except Exception:
                return None
        return x
    normals = {}

    def normal_of(f):
        k = id(f)
        if k not in normals:
            pts = [q for q in (_pos3(v) for v in _items(val(f, 'vertices'))) if q is not None]
            nrm = _unit(_newell(pts)) if len(pts) >= 3 else None
            if nrm is None or _vlen(nrm) < 0.5:
                q = _pos3(val(f, 'normal')) if val(f, 'normal') is not None else None
                nrm = _unit(q) if q else None
            normals[k] = nrm
        return normals[k]
    cos_lim = math.cos(math.radians(max_angle))
    soft = 0
    for e in _items(val(mesh, 'edges')):
        fs = _items(val(e, 'faces'))
        if len(fs) != 2:
            continue
        n1, n2 = normal_of(fs[0]), normal_of(fs[1])
        if n1 is None or n2 is None:
            continue
        if _vdot(n1, n2) >= cos_lim:
            try:
                e.soft = True
                soft += 1
            except Exception:
                pass
    return soft


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
            shared = {}

            def P(i):
                # one corner shared by every face that uses it, so IngeTrazo knows which faces meet
                v = shared.get(i)
                if v is None:
                    v = shared[i] = VertexWrapper(*verts[i])
                return v
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
            new_faces = []                                  # (face, its corners) - for the colours
            for f in split:
                nf = None
                try:
                    nf = target.add_face([P(i) for i in f])
                except Exception:
                    nf = None
                if nf is None and len(f) > 3:
                    for k in range(1, len(f) - 1):          # IngeTrazo wouldn't take it whole: triangles
                        tri = [f[0], f[k], f[k + 1]]
                        try:
                            tf = target.add_face([P(i) for i in tri])
                            if tf is not None:
                                made += 1
                                new_faces.append((tf, tri))
                            else:
                                report['lost'] += 1
                        except Exception:
                            report['lost'] += 1
                    continue
                if nf is None:
                    report['lost'] += 1
                else:
                    made += 1
                    new_faces.append((nf, f))
            if not made:
                continue
            used = sorted(set(i for f in split for i in f))
            lo = [min(verts[i][k] for i in used) for k in range(3)]
            hi = [max(verts[i][k] for i in used) for k in range(3)]
            plain = find_plain_wall(scene, name, lo, hi)
            if mode in ('hide', 'replace') and plain is None:
                report['unmatched'] += 1
            if plain is not None:
                try:
                    report['coloured'] = report.get('coloured', 0) + copy_colours(plain, new_faces, verts)
                except Exception as e:
                    print("%s: colours: %s" % (PLUGIN_NAME, e))
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
            try:
                report['soft'] = report.get('soft', 0) + soften_edges(target)
            except Exception as e:
                print("%s: softening: %s" % (PLUGIN_NAME, e))
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
# Wall pictures online: Poly Haven's free (CC0) textures, through its public API
# ---------------------------------------------------------------------------
PH_API = "https://api.polyhaven.com"
PH_AGENT = "EddysModelWorks-RealisticWall/%s (IngeTrazo plugin)" % VERSION
PH_KINDS = [("Walls", ("wall",)), ("Brick", ("brick",)), ("Stone and rock", ("rock", "cobblestone", "sandstone")),
            ("Plaster and concrete", ("plaster-concrete", "plaster", "concrete")), ("Roofing", ("roofing",)),
            ("Wood", ("wood",)), ("Everything", ())]
PH_SIZES = [("2K (quick)", "2k"), ("4K (good)", "4k"), ("8K (very fine, big files)", "8k")]
DEFAULT_PICTURES = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Wall Pictures")


def ph_get(url, timeout=30):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": PH_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def ph_list():
    """{id: info} of every texture on Poly Haven."""
    return json.loads(ph_get(PH_API + "/assets?t=textures").decode("utf-8"))


def ph_thumb_url(aid, size=128):
    return "https://cdn.polyhaven.com/asset_img/thumbs/%s.png?width=%d&height=%d" % (aid, size, size)


def ph_pick(entries, kind_cats, words):
    """The ids to show: in one of kind_cats (or all), with every typed word in the name or tags,
    most downloaded first."""
    words = [w for w in (words or "").lower().split() if w]
    out = []
    for aid, e in entries.items():
        cats = [c.lower() for c in (e.get("categories") or [])]
        if kind_cats and not any(c in cats for c in kind_cats):
            continue
        if kind_cats and ("floor" in cats or "road" in cats) and "wall" not in cats:
            continue                                     # floors and pavements: no use on a wall
        text = " ".join([aid, str(e.get("name", ""))] + [str(t) for t in (e.get("tags") or [])] + cats).lower()
        if all(w in text for w in words):
            out.append(aid)
    out.sort(key=lambda a: -int(entries[a].get("download_count") or 0))
    return out


def ph_download(aid, res, folder, progress=None):
    """Downloads the height picture (and the colour photo, if there is one) into folder.
    Returns (height picture path, colour photo path or None)."""
    files = json.loads(ph_get(PH_API + "/files/" + aid).decode("utf-8"))

    def url_of(kind, fmts):
        k = files.get(kind) or {}
        r = k.get(res) or k.get("4k") or k.get("2k") or (list(k.values())[0] if k else {})
        for f in fmts:
            if isinstance(r, dict) and isinstance(r.get(f), dict) and r[f].get("url"):
                return r[f]["url"]
        return None
    disp = url_of("Displacement", ("png", "jpg", "exr"))
    diff = url_of("Diffuse", ("jpg", "png"))
    if not disp:
        raise RuntimeError("That one has no height picture to carve from - pick another.")
    os.makedirs(folder, exist_ok=True)
    got = []
    for url in (disp, diff):
        if not url:
            got.append(None)
            continue
        path = os.path.join(folder, url.split("/")[-1].split("?")[0])
        if not os.path.isfile(path):
            if progress:
                progress("Downloading %s..." % os.path.basename(path))
            data = ph_get(url, timeout=120)
            tmp = path + ".part"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, path)
        got.append(path)
    return got[0], got[1]


class OnlinePictures(QDialog):
    """Browse Poly Haven's free wall pictures and download one."""
    def __init__(self, folder, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QListView
        import queue
        self.setWindowTitle("Wall pictures online - Poly Haven (free, CC0)")
        self.resize(760, 620)
        self.folder = folder
        self.entries = {}
        self.result = None            # (height picture, colour photo, [width, height] mm)
        self.q = queue.Queue()
        self._busy = False
        self._thumbs_wanted = []
        lay = QVBoxLayout(self)
        info = QLabel("Free wall, brick and stone pictures from polyhaven.com (CC0 - free for anything). Click "
                      "one and click Download: the height picture and its colour photo go into your wall "
                      "pictures folder, and it's picked for you.")
        info.setWordWrap(True)
        lay.addWidget(info)
        row = QHBoxLayout()
        self.cb_kind = QComboBox()
        for label, _c in PH_KINDS:
            self.cb_kind.addItem(label)
        self.ed_find = QLineEdit()
        self.ed_find.setPlaceholderText("Search (castle, old, red, rough...)")
        self.cb_size = QComboBox()
        for label, key in PH_SIZES:
            self.cb_size.addItem(label, key)
        self.cb_size.setCurrentIndex(1)
        row.addWidget(QLabel("Show:"))
        row.addWidget(self.cb_kind)
        row.addWidget(self.ed_find, 1)
        row.addWidget(QLabel("Size:"))
        row.addWidget(self.cb_size)
        lay.addLayout(row)
        self.lst = QListWidget()
        self.lst.setViewMode(QListView.IconMode)
        self.lst.setIconSize(QSize(128, 128))
        self.lst.setGridSize(QSize(146, 168))
        self.lst.setResizeMode(QListView.Adjust)
        self.lst.setMovement(QListView.Static)
        self.lst.setWordWrap(True)
        self.lst.setUniformItemSizes(True)
        self.lst.setSpacing(4)
        lay.addWidget(self.lst, 1)
        self.lbl = QLabel("Getting the list...")
        self.lbl.setWordWrap(True)
        lay.addWidget(self.lbl)
        brow = QHBoxLayout()
        self.b_get = QPushButton("Download")
        self.b_get.setDefault(True)
        b_close = QPushButton("Close")
        brow.addStretch(1)
        brow.addWidget(self.b_get)
        brow.addWidget(b_close)
        lay.addLayout(brow)
        self.b_get.clicked.connect(self.download)
        self.lst.itemDoubleClicked.connect(lambda *_: self.download())
        self.lst.currentItemChanged.connect(self.show_info)
        b_close.clicked.connect(self.reject)
        self.cb_kind.currentIndexChanged.connect(self.fill)
        self.ed_find.textChanged.connect(self.fill)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)
        self.timer.start(100)
        self.run(lambda: ("list", ph_list()))

    def run(self, job):
        import threading

        def work():
            try:
                self.q.put(job())
            except Exception as e:
                self.q.put(("error", e))
        threading.Thread(target=work, daemon=True).start()

    def poll(self):
        from PySide6.QtGui import QIcon, QPixmap
        import queue
        for _ in range(20):
            try:
                kind, data = self.q.get_nowait()
            except queue.Empty:
                break
            if kind == "list":
                self.entries = data
                self.fill()
            elif kind == "thumb":
                aid, raw = data
                pm = QPixmap()
                if raw and pm.loadFromData(raw):
                    pm = self._square(pm)
                    for i in range(self.lst.count()):
                        it = self.lst.item(i)
                        if it.data(Qt.UserRole) == aid:
                            it.setIcon(QIcon(pm))
                            break
            elif kind == "say":
                self.lbl.setText(data)
            elif kind == "done":
                self._busy = False
                self.b_get.setEnabled(True)
                self.result = data
                self.accept()
            elif kind == "error":
                self._busy = False
                self.b_get.setEnabled(True)
                self.lbl.setText("<span style='color:#b00'>Couldn't reach Poly Haven: %s. Check the internet "
                                 "connection and try again.</span>" % data)

    def _square(self, pm, side=128):
        """The picture fitted into a square of its own, so every slot is the same size."""
        from PySide6.QtGui import QPixmap, QPainter
        out = QPixmap(side, side)
        out.fill(Qt.transparent)
        sc = pm.scaled(side, side, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        p = QPainter(out)
        p.drawPixmap((side - sc.width()) // 2, (side - sc.height()) // 2, sc)
        p.end()
        return out

    def _blank(self, side=128):
        from PySide6.QtGui import QPixmap, QPainter, QColor
        if getattr(self, '_blank_pm', None) is None:
            pm = QPixmap(side, side)
            pm.fill(Qt.transparent)
            p = QPainter(pm)
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(215, 215, 215))
            p.drawEllipse(8, 8, side - 16, side - 16)
            p.end()
            self._blank_pm = pm
        return self._blank_pm

    def fill(self, *_):
        from PySide6.QtGui import QIcon
        if not self.entries:
            return
        cats = PH_KINDS[max(0, self.cb_kind.currentIndex())][1]
        ids = ph_pick(self.entries, cats, self.ed_find.text())
        self.lst.clear()
        for aid in ids[:300]:
            e = self.entries[aid]
            it = QListWidgetItem(QIcon(self._blank()), str(e.get("name") or aid))
            it.setData(Qt.UserRole, aid)
            it.setSizeHint(QSize(146, 168))
            it.setTextAlignment(Qt.AlignHCenter | Qt.AlignTop)
            dims = e.get("dimensions") or []
            if len(dims) >= 2:
                it.setToolTip("%s - %.1f x %.1f m of wall" % (e.get("name", aid), dims[0] / 1000.0, dims[1] / 1000.0))
            self.lst.addItem(it)
        self.lbl.setText("%d pictures. Click one to see more about it." % len(ids))
        wanted = list(ids[:300])

        def thumbs():
            for aid in wanted:
                try:
                    self.q.put(("thumb", (aid, ph_get(ph_thumb_url(aid), timeout=20))))
                except Exception:
                    pass
            return ("say", "%d pictures. Click one to see more about it." % len(wanted))
        self.run(thumbs)

    def show_info(self, it, *_):
        if it is None:
            return
        e = self.entries.get(it.data(Qt.UserRole)) or {}
        dims = e.get("dimensions") or []
        size = " - shows %.1f x %.1f m of wall" % (dims[0] / 1000.0, dims[1] / 1000.0) if len(dims) >= 2 else ""
        self.lbl.setText("<b>%s</b>%s<br>%s" % (e.get("name", ""), size, e.get("description", "")))

    def download(self):
        it = self.lst.currentItem()
        if it is None or self._busy:
            if it is None:
                self.lbl.setText("Click a picture first.")
            return
        aid = it.data(Qt.UserRole)
        res = self.cb_size.currentData() or "4k"
        folder = self.folder
        dims = (self.entries.get(aid) or {}).get("dimensions") or []
        self._busy = True
        self.b_get.setEnabled(False)
        self.lbl.setText("Downloading %s (%s)..." % (it.text(), res.upper()))

        def job():
            disp, diff = ph_download(aid, res, folder, progress=lambda t: self.q.put(("say", t)))
            return ("done", (disp, diff, dims))
        self.run(job)


# ---------------------------------------------------------------------------
# The Blender side: written beside each job and run by Blender
# ---------------------------------------------------------------------------
BLENDER_SCRIPT = '# Eddy\'s Model Works - Realistic Wall, Blender side.\n# Run by the Realistic Wall plugin:  blender --python ed3d_realistic_wall_blender.py -- job.json\n# Works the same way as the "My realistic wall" Geometry Nodes file: a fine grid is pushed\n# in and out by the wall picture (light = stands out, dark = sunk in), then that shape is\n# cut out of the wall face. Openings, ends and edges keep the stone shape.\n# Works with Blender 3.x to 5.x (no importers/exporters used - the mesh comes in as JSON).\n\nimport json, math, os, sys\n\ntry:\n    import bpy, bmesh\n    import numpy as np\n    IN_BLENDER = True\nexcept ImportError:          # lets the maths be tested without Blender\n    import numpy as np\n    IN_BLENDER = False\n\nMAX_POINTS = 600_000         # most points per wall, unless the job says otherwise\n\n\n# ---------------------------------------------------------------- maths (no Blender)\ndef unit(v):\n    v = np.asarray(v, float)\n    n = np.linalg.norm(v)\n    return v / n if n > 1e-12 else v\n\n\ndef face_axes(normal):\n    """u runs along the wall, v runs up it, n points out of the face."""\n    n = unit(normal)\n    up = np.array([0.0, 0.0, 1.0])\n    if abs(n @ up) > 0.95:               # face lying flat (top of a wall) - use Y as \'up\'\n        up = np.array([0.0, 1.0, 0.0])\n    u = unit(np.cross(up, n))\n    v = np.cross(n, u)\n    return u, v, n\n\n\ndef face_extent(verts, normal, plane_point, tol):\n    """Corners (in u, v) of all wall points lying in the chosen face\'s plane."""\n    u, v, n = face_axes(normal)\n    P = np.asarray(verts, float)\n    d0 = float(np.asarray(plane_point, float) @ n)\n    on = np.abs(P @ n - d0) < tol\n    if not on.any():\n        raise ValueError("No wall points found on the chosen face")\n    pu, pv = P[on] @ u, P[on] @ v\n    return (pu.min(), pu.max(), pv.min(), pv.max()), d0\n\n\ndef gray_from_rgba(px):\n    """px: (h, w, 4) floats 0..1 -> (h, w) brightness."""\n    return px[..., 0] * 0.299 + px[..., 1] * 0.587 + px[..., 2] * 0.114\n\n\ndef box_blur(img, r):\n    if r <= 0:\n        return img\n    k = 2 * r + 1\n    pad = np.pad(img, r, mode="wrap")\n    c = pad.cumsum(0).cumsum(1)\n    c = np.pad(c, ((1, 0), (1, 0)))\n    s = c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]\n    return s / (k * k)\n\n\ndef sample_wrap(img, x, y):\n    """Bilinear sample, repeating picture. x, y in picture widths (any value)."""\n    h, w = img.shape\n    fx = (x % 1.0) * w - 0.5\n    fy = (y % 1.0) * h - 0.5\n    x0 = np.floor(fx).astype(int); y0 = np.floor(fy).astype(int)\n    tx = fx - x0; ty = fy - y0\n    x0 %= w; y0 %= h\n    x1 = (x0 + 1) % w; y1 = (y0 + 1) % h\n    a = img[y0, x0] * (1 - tx) + img[y0, x1] * tx\n    b = img[y1, x0] * (1 - tx) + img[y1, x1] * tx\n    return a * (1 - ty) + b * ty\n\n\ndef normalise(img):\n    lo, hi = np.percentile(img, 1), np.percentile(img, 99)\n    if hi - lo < 1e-6:\n        return np.zeros_like(img)\n    return np.clip((img - lo) / (hi - lo), 0, 1)\n\n\ndef protect_mask(tris, axes, d0, depth, gu, gv):\n    """Grid points behind anything standing out of the face (a window or sill built in, a pier):\n    the face is left plain there, so nothing gets cut loose. tris: (T, 3, 3) wall triangles."""\n    u, v, n = axes\n    nu, nv = len(gu), len(gv)\n    mask = np.zeros((nv, nu), bool)\n    if tris is None or len(tris) == 0:\n        return mask\n    tol = max(depth * 0.05, 1e-9)\n    dn = tris @ n                                           # (T, 3) how far out each corner is\n    out_ = (dn > d0 + tol).any(1)                           # stands out of the face\n    shallow = ((dn < d0 - tol) & (dn > d0 - depth - tol)).all(1)   # sunk in less than the stones go\n    pick = tris[out_ | shallow]\n    if len(pick) == 0:\n        return mask\n    du = (gu[-1] - gu[0]) / max(nu - 1, 1)\n    dv = (gv[-1] - gv[0]) / max(nv - 1, 1)\n    PU, PV = pick @ u, pick @ v                             # (T, 3) each\n    for a, b in zip(PU, PV):\n        i0 = max(0, int(math.floor((a.min() - gu[0]) / du)) - 1)\n        i1 = min(nu - 1, int(math.ceil((a.max() - gu[0]) / du)) + 1)\n        j0 = max(0, int(math.floor((b.min() - gv[0]) / dv)) - 1)\n        j1 = min(nv - 1, int(math.ceil((b.max() - gv[0]) / dv)) + 1)\n        if i1 < i0 or j1 < j0:\n            continue\n        X, Y = np.meshgrid(gu[i0:i1 + 1], gv[j0:j1 + 1])\n        x0, y0 = a[0], b[0]\n        e1 = (a[1] - x0, b[1] - y0); e2 = (a[2] - x0, b[2] - y0)\n        det = e1[0] * e2[1] - e1[1] * e2[0]\n        if abs(det) < 1e-9 * max(du, dv) ** 2:              # edge-on (seen side-on): along its edges\n            for k in range(3):\n                ax_, ay_ = a[k], b[k]\n                bx_, by_ = a[(k + 1) % 3], b[(k + 1) % 3]\n                steps = int(max(abs(bx_ - ax_) / du, abs(by_ - ay_) / dv) * 2) + 2\n                t = np.linspace(0.0, 1.0, steps)\n                ii = np.clip(np.round((ax_ + (bx_ - ax_) * t - gu[0]) / du).astype(int), 0, nu - 1)\n                jj = np.clip(np.round((ay_ + (by_ - ay_) * t - gv[0]) / dv).astype(int), 0, nv - 1)\n                mask[jj, ii] = True\n            continue\n        px, py = X - x0, Y - y0\n        l1 = (px * e2[1] - py * e2[0]) / det\n        l2 = (e1[0] * py - e1[1] * px) / det\n        slack = 0.5 * max(du, dv) / max(math.sqrt(abs(det)), 1e-12)\n        inside = (l1 >= -slack) & (l2 >= -slack) & (l1 + l2 <= 1 + slack)\n        mask[j0:j1 + 1, i0:i1 + 1] |= inside\n    # one more point all round, so the stones don\'t undercut its edges\n    m = mask.copy()\n    m[1:, :] |= mask[:-1, :]; m[:-1, :] |= mask[1:, :]\n    m[:, 1:] |= mask[:, :-1]; m[:, :-1] |= mask[:, 1:]\n    return m\n\n\ndef value_noise(x, y, seed):\n    """Smooth random values 0..1 (one blob about every 1 unit of x, y)."""\n    rng = np.random.default_rng(int(seed) + 12345)\n    N = 64\n    table = rng.random((N, N))\n    xi = np.floor(x).astype(int); yi = np.floor(y).astype(int)\n    tx = x - xi; ty = y - yi\n    tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty)\n    xi %= N; yi %= N\n    x1 = (xi + 1) % N; y1 = (yi + 1) % N\n    a = table[yi, xi] * (1 - tx) + table[yi, x1] * tx\n    b = table[y1, xi] * (1 - tx) + table[y1, x1] * tx\n    return a * (1 - ty) + b * ty\n\n\ndef hide_repeats(img, sx, sy, amount, seed, want_mix=False):\n    """The picture, with a second copy (moved and mirrored) mixed in in big soft patches, so the\n    repeats don\'t show. Where the copies meet, the higher stone wins (no blurry mush).\n    With want_mix, also how much of the second copy shows at each point (for the colours)."""\n    h1 = sample_wrap(img, sx, sy)\n    if amount <= 0:\n        return (h1, np.zeros_like(h1)) if want_mix else h1\n    h2 = sample_wrap(img, -sx + MIRROR_SHIFT, sy)                   # mirrored and slid along (courses stay level)\n    n = value_noise(sx / 1.7 + 3.1, sy / 1.7 + 7.3, seed)   # patches about 1.7 pictures across\n    n = n * 0.6 + value_noise(sx / 0.7, sy / 0.7, seed + 1) * 0.4\n    w2 = np.clip((n - (1.0 - amount * 0.5)) / 0.08 + 0.5, 0.0, 1.0)   # amount 1: about half each\n    w1 = 1.0 - w2\n    a, b = h1 + w1, h2 + w2\n    top = np.maximum(a, b) - 0.25\n    r1 = np.maximum(a - top, 0.0); r2 = np.maximum(b - top, 0.0)\n    h = (h1 * r1 + h2 * r2) / (r1 + r2 + 1e-9)\n    return (h, r2 / (r1 + r2 + 1e-9)) if want_mix else h\n\n\nMIRROR_SHIFT = 0.37      # the second copy: mirrored, and slid along this much of a picture\n\n\ndef colour_picture_for(path):\n    """For a height picture (name_disp_4k.png) with its colour photo beside it (name_diff_4k.jpg),\n    the colour photo\'s path - else None."""\n    folder, fn = os.path.split(path)\n    low = fn.lower()\n    for w in HEIGHT_WORDS:\n        i = low.find(w)\n        if i < 0:\n            continue\n        stem, rest = low[:i], os.path.splitext(low[i + len(w):])[0]\n        try:\n            names = os.listdir(folder)\n        except Exception:\n            return None\n        best = None\n        for other in names:\n            o = other.lower()\n            if not o.startswith(stem) or other == fn:\n                continue\n            for cw in COLOUR_WORDS:\n                if o.startswith(stem + cw) and o.endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp")):\n                    score = (os.path.splitext(o[len(stem + cw):])[0] == rest, o.endswith((".jpg", ".jpeg")))\n                    if best is None or score > best[0]:\n                        best = (score, os.path.join(folder, other))\n        return best[1] if best else None\n    return None\n\n\n_mids = {}\n\n\ndef otsu_level(img):\n    """The brightness that best splits the picture into joints (dark) and bricks (light)."""\n    key = (id(img), img.shape)\n    if key in _mids:\n        return _mids[key]\n    hist, edges = np.histogram(img[::4, ::4], bins=128, range=(0.0, 1.0))\n    p = hist / max(hist.sum(), 1)\n    w = np.cumsum(p)\n    mu = np.cumsum(p * (edges[:-1] + edges[1:]) / 2)\n    between = (mu[-1] * w - mu) ** 2 / np.maximum(w * (1 - w), 1e-12)\n    level = float((edges[:-1] + edges[1:])[int(np.argmax(between))] / 2)\n    _mids.clear()\n    _mids[key] = level\n    return level\n\n\ndef crisp_picture(img, amount):\n    """Sharper steps from the bricks down into the joints, flatter brick faces - judged against the\n    wall round each brick, so big hollows and bulges in the wall stay. amount 0..1."""\n    if amount <= 0:\n        return img\n    key = ("crisp", id(img), img.shape, round(amount, 3))\n    if key in _mids:\n        return _mids[key]\n    r = max(3, img.shape[1] // 48)                         # about a brick or two across\n    low = box_blur(img, r)\n    high = img - low\n    sd = float(high.std()) or 1e-6\n    g = 1.0 + 5.0 * amount\n    sharp = np.tanh(g * high / (1.5 * sd)) * (1.5 * sd)\n    out = normalise((1.0 - amount) * img + amount * (low + sharp))\n    for k_ in [k for k in _mids if k[0] == "crisp"]:\n        del _mids[k_]\n    _mids[key] = out\n    return out\n\n\nHEIGHT_WORDS = ("_disp", "_displacement", "_height", "_heightmap", "_bump")\nCOLOUR_WORDS = ("_diff", "_diffuse", "_col", "_color", "_colour", "_albedo", "_basecolor", "_base_color")\n\n\ndef height_picture_for(path):\n    """For a colour photo (name_diff_4k.jpg) with its height picture beside it (name_disp_4k.png),\n    the height picture\'s path - else None."""\n    folder, fn = os.path.split(path)\n    low = fn.lower()\n    for w in COLOUR_WORDS:\n        i = low.find(w)\n        if i < 0:\n            continue\n        stem, rest = low[:i], os.path.splitext(low[i + len(w):])[0]\n        try:\n            names = os.listdir(folder)\n        except Exception:\n            return None\n        best = None\n        for other in names:\n            o = other.lower()\n            if not o.startswith(stem) or other == fn:\n                continue\n            for hw in HEIGHT_WORDS:\n                if o.startswith(stem + hw):\n                    score = (os.path.splitext(o[len(stem + hw):])[0] == rest, o.endswith((".png", ".tif", ".tiff", ".exr")))\n                    if best is None or score > best[0]:\n                        best = (score, os.path.join(folder, other))\n        return best[1] if best else None\n    return None\n\n\ndef loose_parts(loop_start, loop_total, vidx, nverts):\n    """Which separate piece each face belongs to (faces sharing a corner are one piece): an array\n    of labels, one per face."""\n    parent = np.arange(nverts)\n\n    def find(a):\n        root = a\n        while parent[root] != root:\n            root = parent[root]\n        while parent[a] != root:\n            parent[a], a = root, parent[a]\n        return root\n    for s0, n0 in zip(loop_start, loop_total):\n        vs = vidx[s0:s0 + n0]\n        r0 = find(int(vs[0]))\n        for v in vs[1:]:\n            r = find(int(v))\n            if r != r0:\n                parent[r] = r0\n    return np.array([find(int(vidx[s0])) for s0 in loop_start])\n\n\ndef body_label(labels, face_pts, normal, d0, tol):\n    """The piece that is the wall itself: the one with the most face lying flat on the face being\n    carved (windows, doors and sills built onto it are the other pieces)."""\n    n = np.asarray(normal, float)\n    best, score = None, {}\n    for lab, pts in zip(labels, face_pts):\n        P = np.asarray(pts, float)\n        if len(P) < 3 or np.abs(P @ n - d0).max() > tol:\n            continue\n        a = np.zeros(3)\n        for i in range(1, len(P) - 1):\n            a += np.cross(P[i] - P[0], P[i + 1] - P[0])\n        score[lab] = score.get(lab, 0.0) + abs(float(a @ n)) / 2.0\n    if score:\n        best = max(score, key=score.get)\n    return best\n\n\ndef relief_grid(extent, d0, axes, img, job, tris=None):\n    """The stone surface as heights on a grid over the face: (gu, gv, W, kept plain, detail got).\n    W is how far along the normal each point is (d0 = the wall\'s face, d0 - depth = deepest)."""\n    u0, u1, v0, v1 = extent\n    depth = float(job["depth"])\n    tw, th = float(job["tile_width"]), float(job["tile_height"])\n    res = max(8, int(job.get("detail", 120)))\n    nu = max(2, int(math.ceil((u1 - u0) / tw * res)) + 1)\n    nv = max(2, int(math.ceil((v1 - v0) / th * res)) + 1)\n    cap_pts = int(job.get("max_points") or MAX_POINTS)\n    if nu * nv > cap_pts:\n        s_ = math.sqrt(cap_pts / (nu * nv))\n        nu = max(2, int(nu * s_)); nv = max(2, int(nv * s_))\n    gu = np.linspace(u0, u1, nu)\n    gv = np.linspace(v0, v1, nv)\n    UU, VV = np.meshgrid(gu, gv)\n    sx = (UU - float(job.get("offset_x", 0.0))) / tw\n    sy = (VV - float(job.get("offset_y", 0.0))) / th\n    img = crisp_picture(img, float(job.get("crisp", 0.0)))\n    h = hide_repeats(img, sx, sy, float(job.get("mix", 0.0)), job.get("seed", 1))\n    if job.get("invert"):\n        h = 1.0 - h\n    keep = protect_mask(tris, axes, d0, depth, gu, gv)\n    h[keep] = 1.0\n    W = d0 - depth * (1.0 - h)\n    across = (nu - 1) / max((u1 - u0) / tw, 1e-9)\n    relief_grid.keep = keep\n    return gu, gv, W, int(keep.sum()), across\n\n\ndef near_edges(gu, gv, segs, reach=0.6):\n    """Grid points closer than \'reach\' of a step to any of the 2D segments (the face\'s own edges) -\n    left out so no point lands on an edge."""\n    nu, nv = len(gu), len(gv)\n    du = (gu[-1] - gu[0]) / max(nu - 1, 1)\n    dv = (gv[-1] - gv[0]) / max(nv - 1, 1)\n    mask = np.zeros((nv, nu), bool)\n    for (ax, ay), (bx, by) in segs:\n        steps = int(max(abs(bx - ax) / du, abs(by - ay) / dv) * 3) + 2\n        t = np.linspace(0.0, 1.0, steps)\n        x = ax + (bx - ax) * t\n        y = ay + (by - ay) * t\n        fi = (x - gu[0]) / du\n        fj = (y - gv[0]) / dv\n        for oi in (0, 1):\n            for oj in (0, 1):\n                ii = np.floor(fi).astype(int) + oi\n                jj = np.floor(fj).astype(int) + oj\n                ok = (ii >= 0) & (ii < nu) & (jj >= 0) & (jj < nv)\n                ii, jj = ii[ok], jj[ok]\n                close = (np.abs(gu[ii] - x[ok]) < du * reach) & (np.abs(gv[jj] - y[ok]) < dv * reach)\n                mask[jj[close], ii[close]] = True\n    return mask\n\n\ndef build_cutter(extent, d0, axes, img, job, tris=None):\n    """Closed block: top is the stone relief, it reaches out past the face.\n    Returns verts (N,3) and faces (list of tuples)."""\n    u, v, n = axes\n    u0, u1, v0, v1 = extent\n    depth = float(job["depth"])\n    tw, th = float(job["tile_width"]), float(job["tile_height"])\n    res = max(8, int(job.get("detail", 120)))            # points across one picture\n    margin = max(depth, 1e-6) * 0.5\n    u0 -= margin; u1 += margin; v0 -= margin; v1 += margin\n    nu = max(2, int(math.ceil((u1 - u0) / tw * res)) + 1)\n    nv = max(2, int(math.ceil((v1 - v0) / th * res)) + 1)\n    cap_pts = int(job.get("max_points") or MAX_POINTS)\n    if nu * nv > cap_pts:                                 # keep it to a sensible size\n        s = math.sqrt(cap_pts / (nu * nv))\n        nu = max(2, int(nu * s)); nv = max(2, int(nv * s))\n    gu = np.linspace(u0, u1, nu)\n    gv = np.linspace(v0, v1, nv)\n    UU, VV = np.meshgrid(gu, gv)                          # (nv, nu)\n    sx = (UU - float(job.get("offset_x", 0.0))) / tw\n    sy = (VV - float(job.get("offset_y", 0.0))) / th\n    img = crisp_picture(img, float(job.get("crisp", 0.0)))\n    h = hide_repeats(img, sx, sy, float(job.get("mix", 0.0)), job.get("seed", 1))\n    if job.get("invert"):\n        h = 1.0 - h\n    keep = protect_mask(tris, axes, d0, depth, gu, gv)\n    h[keep] = 1.0                                         # plain face behind things that stand out\n    eps = depth * 0.01\n    W = d0 + eps - depth * (1.0 - h)                      # white stays at the face, black is sunk in\n    top = d0 + depth * 0.5                                # cutter reaches just past the face\n    grid = (UU[..., None] * u + VV[..., None] * v + W[..., None] * n).reshape(-1, 3)\n\n    # ring of boundary points, raised to \'top\'\n    ring = ([(0, i) for i in range(nu)] + [(j, nu - 1) for j in range(1, nv)] +\n            [(nv - 1, i) for i in range(nu - 2, -1, -1)] + [(j, 0) for j in range(nv - 2, 0, -1)])\n    ring_idx = [j * nu + i for j, i in ring]\n    cap = grid[ring_idx] + 0.0\n    cap = cap - np.outer(cap @ n, n) + top * n\n    verts = np.vstack([grid, cap])\n    base = len(grid)\n    # relief surface (faces into the wall), as an array of quads\n    J, I = np.meshgrid(np.arange(nv - 1), np.arange(nu - 1), indexing="ij")\n    r0 = (J * nu + I).ravel()\n    quads = np.stack([r0, r0 + nu, r0 + nu + 1, r0 + 1], 1)\n    m = len(ring_idx)\n    ri = np.array(ring_idx)\n    k = np.arange(m)\n    sides = np.stack([ri, ri[(k + 1) % m], base + (k + 1) % m, base + k], 1)   # sides\n    faces = [quads, sides, np.arange(base, base + m)[None, :]]                  # + flat top cap\n    across = (nu - 1) / max((u1 - u0) / tw, 1e-9)        # the detail it really came out at\n    return verts, faces, (nu, nv, int(keep.sum()), across)\n\n\n# ---------------------------------------------------------------- Blender part\n# Each carved wall keeps its plain wall (hidden, in the "Realistic Wall - plain walls" collection),\n# so it can be carved again with new settings from the Realistic Wall panel (N sidebar).\nPLAIN_COLL = "Realistic Wall - plain walls"\n_pictures = {}\n\n\ndef load_picture(path, blur):\n    key = (os.path.normcase(os.path.abspath(path)), int(blur))\n    if key in _pictures:\n        return _pictures[key]\n    im = bpy.data.images.load(path, check_existing=True)\n    w, h = im.size\n    px = np.empty(w * h * 4, dtype=np.float32)\n    im.pixels.foreach_get(px)\n    g = gray_from_rgba(px.reshape(h, w, 4))\n    g = normalise(box_blur(g, int(blur)))\n    _pictures.clear()\n    _pictures[key] = g\n    return g\n\n\ndef build_mesh(name, verts, faces, face_ints=None):\n    """A mesh from points and faces. faces: a list of tuples, or a list of numpy arrays each\n    holding faces with the same number of corners (fast, for big grids). face_ints: {name: one\n    number per face} kept with the faces (set before Blender tidies the mesh)."""\n    me = bpy.data.meshes.new(name)\n    verts = np.asarray(verts, dtype=np.float64)\n    if faces and isinstance(faces[0], np.ndarray):\n        loops = np.concatenate([f.ravel() for f in faces]).astype(np.int32)\n        sizes = np.concatenate([np.full(len(f), f.shape[1], np.int32) for f in faces])\n    else:\n        loops = np.array([i for f in faces for i in f], np.int32)\n        sizes = np.array([len(f) for f in faces], np.int32)\n    starts = np.concatenate([[0], np.cumsum(sizes)[:-1]]).astype(np.int32)\n    try:\n        me.vertices.add(len(verts))\n        me.vertices.foreach_set("co", verts.astype(np.float32).ravel())\n        me.loops.add(len(loops))\n        me.loops.foreach_set("vertex_index", loops)\n        me.polygons.add(len(sizes))\n        me.polygons.foreach_set("loop_start", starts)\n        try:\n            me.polygons.foreach_set("loop_total", sizes)      # Blender 3.x needs this\n        except Exception:\n            pass\n        me.update(calc_edges=True)\n    except Exception as e:                                    # the slow way\n        print("Realistic Wall: quick mesh build failed (%s), using from_pydata" % e)\n        bpy.data.meshes.remove(me)\n        me = bpy.data.meshes.new(name)\n        fl = [tuple(int(i) for i in loops[s_:s_ + n_]) for s_, n_ in zip(starts, sizes)]\n        me.from_pydata([tuple(p) for p in verts], [], fl)\n    for an, vals in (face_ints or {}).items():\n        if len(vals) == len(me.polygons):\n            try:\n                at = me.attributes.new(an, \'INT\', \'FACE\')\n                at.data.foreach_set("value", np.asarray(vals, dtype=np.int32))\n            except Exception as e:\n                print("Realistic Wall: %s: %s" % (an, e))\n    me.validate()\n    me.update()\n    return me\n\n\ndef make_object(name, me, coll=None):\n    ob = bpy.data.objects.new(name, me)\n    (coll or bpy.context.scene.collection).objects.link(ob)\n    return ob\n\n\ndef tidy_mesh(me, recalc=True):\n    bm = bmesh.new()\n    bm.from_mesh(me)\n    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)\n    if recalc:\n        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)\n    bm.to_mesh(me)\n    bm.free()\n\n\ndef close_gaps(me):\n    """Joins a wall\'s edges up where one face has a corner part way along another face\'s edge (an\n    arch meeting a straight wall, say), so the wall is a closed solid and Blender\'s quick cut works\n    on it. Returns how many edges are still open (0 = closed)."""\n    bm = bmesh.new()\n    bm.from_mesh(me)\n    try:\n        co = [v.co for v in bm.verts]\n        size = max((max(c[i] for c in co) - min(c[i] for c in co)) for i in range(3)) if co else 1.0\n        tol = max(size * 2e-6, 1e-9)\n        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=tol)\n        for _round in range(4):\n            bnd = [e for e in bm.edges if len(e.link_faces) == 1]\n            if not bnd or len(bnd) > 4000:\n                break\n            pts = list({v for e in bnd for v in e.verts})\n            splits = 0\n            for e in bnd:\n                if not e.is_valid:\n                    continue\n                va, vb = e.verts\n                a, b = va.co.copy(), vb.co.copy()\n                ab = b - a\n                L2 = ab.length_squared\n                if L2 < tol * tol:\n                    continue\n                on = []\n                for v in pts:\n                    if not v.is_valid or v is va or v is vb:\n                        continue\n                    t = (v.co - a).dot(ab) / L2\n                    if t <= 1e-6 or t >= 1 - 1e-6:\n                        continue\n                    if (a + ab * t - v.co).length < tol * 5:\n                        on.append((t, v))\n                if not on:\n                    continue\n                on.sort(key=lambda x: x[0])\n                cur, origin, done_t = e, va, 0.0\n                for t, v in on:\n                    fac = (t - done_t) / max(1.0 - done_t, 1e-12)\n                    ne, nv = bmesh.utils.edge_split(cur, origin, fac)\n                    nv.co = v.co.copy()\n                    cur = ne if vb in ne.verts else cur\n                    if vb not in cur.verts:\n                        cur = next((x for x in nv.link_edges if vb in x.verts), cur)\n                    origin, done_t = nv, t\n                    splits += 1\n            if not splits:\n                break\n            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=tol * 5)\n        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)\n        still = sum(1 for e in bm.edges if not e.is_manifold)\n        bm.to_mesh(me)\n    except Exception as ex:\n        print("Realistic Wall: closing gaps:", ex)\n        still = -1\n    bm.free()\n    me.update()\n    return still\n\n\ndef shade_flat(me):\n    try:\n        me.shade_flat()                                   # Blender 4.1 and later\n        return\n    except Exception:\n        pass\n    try:\n        me.polygons.foreach_set("use_smooth", [False] * len(me.polygons))\n    except Exception:\n        pass\n\n\ndef mesh_triangles(me):\n    try:\n        me.calc_loop_triangles()\n    except Exception:\n        pass                                # Blender works them out by itself now\n    n = len(me.loop_triangles)\n    idx = np.empty(n * 3, dtype=np.int32)\n    me.loop_triangles.foreach_get("vertices", idx)\n    co = np.empty(len(me.vertices) * 3, dtype=np.float64)\n    me.vertices.foreach_get("co", co)\n    return co.reshape(-1, 3)[idx.reshape(-1, 3)]\n\n\ndef split_body(me, normal, point_or_d0, tol):\n    """(the wall itself, everything built onto it) as two meshes - or (None, None) if the wall is\n    all one piece."""\n    np_ = len(me.polygons)\n    if not np_:\n        return None, None\n    att = me.attributes.get("rw_extra")\n    if att is not None and att.domain == \'FACE\':\n        marks = np.empty(np_, np.int32)\n        att.data.foreach_get("value", marks)\n        if 0 < marks.sum() < np_:\n            print("Realistic Wall: %d faces painted as windows and doors kept aside" % int(marks.sum()))\n            return (_part(me, marks == 0, me.name + " body"),     # openings stay open\n                    _part(me, marks != 0, me.name + " extras"))\n    ls = np.empty(np_, np.int32); lt = np.empty(np_, np.int32)\n    me.polygons.foreach_get("loop_start", ls)\n    me.polygons.foreach_get("loop_total", lt)\n    vi = np.empty(len(me.loops), np.int32)\n    me.loops.foreach_get("vertex_index", vi)\n    labels = loose_parts(ls, lt, vi, len(me.vertices))\n    if len(set(labels.tolist())) < 2:\n        return None, None\n    co = mesh_points(me)\n    d0 = float(point_or_d0)\n    face_pts = [co[vi[a:a + b]] for a, b in zip(ls, lt)]\n    n = np.array(face_axes(normal)[2])\n    body = body_label(labels, face_pts, n, d0, tol)\n    if body is None:\n        return None, None\n    keep = labels == body\n    print("Realistic Wall: %d pieces built onto the wall kept aside while it\'s carved" %\n          (len(set(labels.tolist())) - 1))\n    return _part(me, keep, me.name + " body"), _part(me, ~keep, me.name + " extras")\n\n\ndef _part(me, mask, name, fill=False):\n    """The faces of me picked by mask, as a new mesh. With fill, holes left where other faces were\n    taken away (behind a window\'s frame or arch) are filled flat, so the wall is a closed solid."""\n    bm = bmesh.new()\n    bm.from_mesh(me)\n    bm.faces.ensure_lookup_table()\n    gone = [f for f, k in zip(bm.faces, mask) if not k]\n    bmesh.ops.delete(bm, geom=gone, context=\'FACES\')\n    loose = [v for v in bm.verts if not v.link_faces]\n    if loose:\n        bmesh.ops.delete(bm, geom=loose, context=\'VERTS\')\n    if fill:\n        try:\n            bnd = [e for e in bm.edges if e.is_boundary]\n            if bnd:\n                made = bmesh.ops.holes_fill(bm, edges=bnd, sides=0).get("faces", [])\n                if made:\n                    bmesh.ops.triangulate(bm, faces=made)\n                bmesh.ops.recalc_face_normals(bm, faces=bm.faces)\n                print("Realistic Wall: filled %d holes behind windows and doors" % len(made))\n        except Exception as e:\n            print("Realistic Wall: filling holes:", e)\n    out = bpy.data.meshes.new(name)\n    bm.to_mesh(out)\n    bm.free()\n    return out\n\n\ndef mesh_points(me):\n    co = np.empty(len(me.vertices) * 3, dtype=np.float64)\n    me.vertices.foreach_get("co", co)\n    return co.reshape(-1, 3)\n\n\ndef inside_grid(gu, gv, segs):\n    """Which grid points are inside the face\'s outline (its edges as 2D segments, even-odd rule,\n    so window openings count as outside)."""\n    nu, nv = len(gu), len(gv)\n    inside = np.zeros((nv, nu), bool)\n    if not segs:\n        return inside\n    S = np.array(segs, float)                       # (k, 2, 2)\n    ax, ay, bx, by = S[:, 0, 0], S[:, 0, 1], S[:, 1, 0], S[:, 1, 1]\n    for j, y in enumerate(gv):\n        hit = (ay > y) != (by > y)\n        if not hit.any():\n            continue\n        xs = np.sort(ax[hit] + (y - ay[hit]) * (bx[hit] - ax[hit]) / (by[hit] - ay[hit]))\n        inside[j] = (np.searchsorted(xs, gu) % 2) == 1\n    return inside\n\n\ndef _point_inside(x, y, segs):\n    c = 0\n    for (ax, ay), (bx, by) in segs:\n        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):\n            c += 1\n    return c % 2 == 1\n\n\ndef front_rebuild(co, polys, pnormals, axes, d0, tol, gu, gv, W, cdt):\n    """The wall with its front face rebuilt from the relief grid. Only the face\'s real outline (its\n    edges and openings) is kept as it was - inside it the stone runs freely (no straight lines across\n    it from how the flat face was split into triangles). co: points (N,3); polys: index arrays;\n    cdt(points, edges, eps) -> (out points, out faces, where each came from). Returns (points, face\n    blocks, new points count) - or None if there\'s no front face."""\n    u, v, n = axes\n    nV = len(co)\n    d = co @ n\n    front, rest = [], []\n    for idx, pn in zip(polys, pnormals):\n        if pn @ n > 0.999 and np.abs(d[idx] - d0).max() < tol:\n            front.append(idx)\n        else:\n            rest.append(idx)\n    if not front:\n        return None\n    count = {}\n    for idx in front:\n        for a, b in zip(idx, np.roll(idx, -1)):\n            key = (min(int(a), int(b)), max(int(a), int(b)))\n            count[key] = count.get(key, 0) + 1\n    outline = [k for k, c in count.items() if c == 1]\n    fv = sorted({int(i) for idx in front for i in idx})\n    U = co @ u\n    Vv = co @ v\n    segs = [((U[a], Vv[a]), (U[b], Vv[b])) for a, b in outline]\n    keep = inside_grid(gu, gv, segs) & ~near_edges(gu, gv, segs)\n    plain = getattr(relief_grid, "keep", None)\n    if plain is not None and plain.shape == keep.shape and plain.any():\n        inner = plain.copy()                         # plain behind windows: flat, no points needed\n        inner[1:, :] &= plain[:-1, :]; inner[:-1, :] &= plain[1:, :]\n        inner[:, 1:] &= plain[:, :-1]; inner[:, :-1] &= plain[:, 1:]\n        keep &= ~inner\n    UU, VV = np.meshgrid(gu, gv)\n    pick = keep.ravel()\n    gx, gy, gw = UU.ravel()[pick], VV.ravel()[pick], W.ravel()[pick]\n    nf = len(fv)\n    fv_arr = np.array(fv, dtype=np.int64)\n    pts2 = [(float(U[i]), float(Vv[i])) for i in fv] + list(zip(gx.tolist(), gy.tolist()))\n    where = {i: j for j, i in enumerate(fv)}\n    edges_in = [(where[a], where[b]) for a, b in outline]\n    eps = max((gu[-1] - gu[0]), (gv[-1] - gv[0])) * 1e-7\n    o_co, o_faces, o_orig_v = cdt(pts2, edges_in, eps)\n    src = np.fromiter((min(x) if x else -1 for x in o_orig_v), dtype=np.int64, count=len(o_orig_v))\n    is_orig = (src >= 0) & (src < nf)\n    is_grid = src >= nf\n    vmap = np.empty(len(src), np.int64)\n    vmap[is_orig] = fv_arr[src[is_orig]]\n    newi = np.flatnonzero(~is_orig)\n    vmap[newi] = nV + np.arange(len(newi))\n    new_pts = np.empty((len(newi), 3))\n    g_of_new = is_grid[newi]\n    g = src[newi[g_of_new]] - nf\n    new_pts[g_of_new] = (gx[g][:, None] * u + gy[g][:, None] * v + gw[g][:, None] * n)\n    for k in np.flatnonzero(~g_of_new):              # a point the triangulation added on the face\n        c2 = o_co[newi[k]]\n        new_pts[k] = c2[0] * u + c2[1] * v + d0 * n\n    T = np.array([f for f in o_faces if len(f) == 3], dtype=np.int64).reshape(-1, 3)\n    touch = is_grid[T].any(1)\n    ok_rows = touch.copy()\n    for r in np.flatnonzero(~touch):                 # only the face\'s own corners: inside or a hole?\n        f = T[r]\n        cx = (o_co[f[0]][0] + o_co[f[1]][0] + o_co[f[2]][0]) / 3.0\n        cy = (o_co[f[0]][1] + o_co[f[1]][1] + o_co[f[2]][1]) / 3.0\n        ok_rows[r] = _point_inside(cx, cy, segs)\n    new_faces = vmap[T[ok_rows]]\n    verts = np.vstack([co, new_pts]) if len(new_pts) else co\n    blocks = [new_faces] if len(new_faces) else []\n    by_len = {}\n    for idx in rest:\n        by_len.setdefault(len(idx), []).append(list(idx))\n    blocks += [np.array(v_, dtype=np.int64) for v_ in by_len.values()]\n    return verts, blocks, len(new_pts)\n\n\ndef blender_cdt(pts2, edges_in, eps):\n    from mathutils.geometry import delaunay_2d_cdt\n    try:\n        out = delaunay_2d_cdt(pts2, edges_in, [], 0, eps)          # plain pairs of numbers: quicker\n    except Exception:\n        from mathutils import Vector\n        out = delaunay_2d_cdt([Vector(p) for p in pts2], edges_in, [], 0, eps)\n    return out[0], out[2], out[3]\n\n\ndef carve_front(ob, img, job, keep_tris, normal, d0, extent, tol):\n    """Carves the wall by rebuilding its front face: fine points pushed in by the picture, joined to\n    the wall\'s own edges and openings (Blender\'s constrained triangulation). Needs no closed solid and\n    no cut, so it\'s quick whatever is built onto the wall. Returns (ok, size)."""\n    axes = face_axes(normal)\n    me = ob.data\n    co = mesh_points(me)\n    np_ = len(me.polygons)\n    ls = np.empty(np_, np.int32); lt = np.empty(np_, np.int32)\n    me.polygons.foreach_get("loop_start", ls)\n    me.polygons.foreach_get("loop_total", lt)\n    vi = np.empty(len(me.loops), np.int32)\n    me.loops.foreach_get("vertex_index", vi)\n    pn = np.empty(np_ * 3, np.float64)\n    me.polygons.foreach_get("normal", pn)\n    polys = [vi[a:a + b] for a, b in zip(ls, lt)]\n    gu, gv, W, kept, across = relief_grid(extent, d0, axes, img, job, keep_tris)\n    res = front_rebuild(co, polys, pn.reshape(-1, 3), axes, d0, tol, gu, gv, W, blender_cdt)\n    if res is None:\n        return False, (0, 0, 0, 0)\n    verts, blocks, added = res\n    built = build_mesh(ob.name, verts, blocks)\n    old = ob.data\n    ob.data = built\n    if old.users == 0:\n        bpy.data.meshes.remove(old)\n    print("Realistic Wall: front face rebuilt - %d points" % added)\n    return True, (len(gu), len(gv), kept, across)\n\n\nSLOW_OK = 1_200_000    # the slow cut is only used by itself on a cutter up to this size (a couple of minutes)\n\n\ndef carve(ob, cut, allow_slow=False):\n    """Cuts the stone shape into the wall. Tries Blender\'s quick Manifold cut first (Blender 4.5\n    and later, needs a closed wall). The slow Exact cut is only used on a small cutter, or if\n    allowed. Returns \'quick\', \'slow\', \'too slow\' or \'\'."""\n    before = len(ob.data.polygons)\n    for solver in ("MANIFOLD", "EXACT"):\n        if solver == "EXACT" and len(cut.data.vertices) > SLOW_OK and not allow_slow:\n            return "too slow"\n        mod = ob.modifiers.new("Realistic face", "BOOLEAN")\n        mod.operation = "DIFFERENCE"\n        mod.object = cut\n        try:\n            mod.solver = solver\n        except Exception:\n            ob.modifiers.remove(mod)\n            continue\n        if solver == "EXACT":\n            try:\n                mod.use_hole_tolerant = True\n            except Exception:\n                pass\n        try:\n            dg = bpy.context.evaluated_depsgraph_get()\n            me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))\n        except Exception as e:\n            print("Realistic Wall:", solver, e)\n            ob.modifiers.remove(mod)\n            continue\n        ob.modifiers.remove(mod)\n        if len(me.polygons) > before:                     # it has the stones in it\n            old = ob.data\n            ob.data = me\n            bpy.data.meshes.remove(old)\n            print("Realistic Wall: cut with", solver)\n            return "quick" if solver == "MANIFOLD" else "slow"\n        bpy.data.meshes.remove(me)\n    return ""\n\n\ndef fitting_material():\n    mat = bpy.data.materials.get("Windows and doors") or bpy.data.materials.new("Windows and doors")\n    mat.diffuse_color = (0.92, 0.91, 0.88, 1.0)\n    return mat\n\n\ndef extras_of(ob):\n    """The windows and doors kept beside a carved wall (their own part), or None."""\n    name = ob.get("rw_extras")\n    return bpy.data.objects.get(name) if name else None\n\n\ndef stone_material():\n    mat = bpy.data.materials.get("Realistic wall") or bpy.data.materials.new("Realistic wall")\n    mat.diffuse_color = (0.62, 0.58, 0.52, 1.0)\n    return mat\n\n\ndef add_colour(ob, img, job, colour_path):\n    """Puts the colour photo on the wall, lined up with the carving (the same repeats and the same\n    mixed-in patches). For looking at only - the shape doesn\'t change."""\n    me = ob.data\n    nl = len(me.loops)\n    if not nl:\n        return\n    vi = np.empty(nl, dtype=np.int32)\n    me.loops.foreach_get("vertex_index", vi)\n    P = mesh_points(me)\n    u, v, n = face_axes(list(ob.get("rw_normal", (0, -1, 0))))\n    tw, th = float(job["tile_width"]), float(job["tile_height"])\n    px = (P @ u - float(job.get("offset_x", 0.0))) / tw\n    py = (P @ v - float(job.get("offset_y", 0.0))) / th\n    _h, pmix = hide_repeats(crisp_picture(img, float(job.get("crisp", 0.0))), px, py,\n                            float(job.get("mix", 0.0)), job.get("seed", 1), want_mix=True)\n    sx, sy, mix = px[vi], py[vi], pmix[vi]\n    for name, uv in (("RW picture", np.stack([sx, sy], 1)), ("RW mirrored", np.stack([-sx + MIRROR_SHIFT, sy], 1))):\n        lay = me.uv_layers.get(name) or me.uv_layers.new(name=name)\n        lay.data.foreach_set("uv", uv.astype(np.float32).ravel())\n    att = me.attributes.get("rw_mix")\n    if att is not None and (att.domain != \'CORNER\' or att.data_type != \'FLOAT\'):\n        me.attributes.remove(att)\n        att = None\n    if att is None:\n        att = me.attributes.new("rw_mix", \'FLOAT\', \'CORNER\')\n    att.data.foreach_set("value", mix.astype(np.float32))\n    try:\n        me.uv_layers.active = me.uv_layers["RW picture"]\n    except Exception:\n        pass\n    me.materials.clear()\n    me.materials.append(colour_material(colour_path))\n\n\ndef colour_material(path):\n    im = bpy.data.images.load(path, check_existing=True)\n    name = "Realistic wall colour - %s" % os.path.basename(path)\n    mat = bpy.data.materials.get(name)\n    if mat is not None:\n        return mat\n    mat = bpy.data.materials.new(name)\n    mat.diffuse_color = (0.55, 0.35, 0.28, 1.0)\n    mat.use_nodes = True\n    nt = mat.node_tree\n    nt.nodes.clear()\n    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (700, 0)\n    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (420, 0)\n    try:\n        bsdf.inputs["Roughness"].default_value = 0.9\n    except Exception:\n        pass\n    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])\n    texs = []\n    for i, uvname in enumerate(("RW picture", "RW mirrored")):\n        uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = uvname; uvn.location = (-500, 150 - i * 300)\n        tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = im; tex.location = (-280, 150 - i * 300)\n        nt.links.new(uvn.outputs[0], tex.inputs["Vector"])\n        texs.append(tex)\n    att = nt.nodes.new("ShaderNodeAttribute"); att.attribute_name = "rw_mix"; att.location = (-280, 350)\n    try:\n        att.attribute_type = \'GEOMETRY\'\n    except Exception:\n        pass\n    try:\n        mix = nt.nodes.new("ShaderNodeMix")\n        mix.data_type = \'RGBA\'\n        fac = next(i for i in mix.inputs if i.name == "Factor" and i.type == \'VALUE\')\n        a = next(i for i in mix.inputs if i.name == "A" and i.type == \'RGBA\')\n        b = next(i for i in mix.inputs if i.name == "B" and i.type == \'RGBA\')\n        res = next(o for o in mix.outputs if o.name == "Result" and o.type == \'RGBA\')\n    except Exception:\n        mix = nt.nodes.new("ShaderNodeMixRGB")               # older Blender\n        fac, a, b, res = mix.inputs[0], mix.inputs[1], mix.inputs[2], mix.outputs[0]\n    mix.location = (120, 100)\n    nt.links.new(att.outputs["Fac"], fac)\n    nt.links.new(texs[0].outputs["Color"], a)\n    nt.links.new(texs[1].outputs["Color"], b)\n    nt.links.new(res, bsdf.inputs["Base Color"])\n    nt.nodes.active = texs[0]\n    return mat\n\n\ndef colour_path_for(st):\n    if not st.colour_picture or not os.path.isfile(bpy.path.abspath(st.colour_picture)):\n        pic = bpy.path.abspath(st.picture) if st.picture else ""\n        cp = colour_picture_for(pic) if pic else None\n        st.busy = True\n        st.colour_picture = cp or pic\n        st.busy = False\n    p = bpy.path.abspath(st.colour_picture) if st.colour_picture else ""\n    return p if p and os.path.isfile(p) else ""\n\n\ndef apply_colours(context):\n    """Colours on (or off) every carved wall, without carving again."""\n    st = context.scene.rw\n    walls = carved_walls(context.scene)\n    if not walls:\n        return\n    cp = colour_path_for(st) if st.show_colour else ""\n    img = load_picture(bpy.path.abspath(st.picture), st.blur) if (cp and st.picture) else None\n    job = settings_job(st)\n    for ob, _p in walls:\n        if cp and img is not None:\n            add_colour(ob, img, job, cp)\n        else:\n            ob.data.materials.clear()\n            ob.data.materials.append(stone_material())\n    set_view(st.show_colour and bool(cp))\n\n\ndef set_view(colour):\n    try:\n        for win in bpy.context.window_manager.windows:\n            for area in win.screen.areas:\n                if area.type == "VIEW_3D":\n                    sh = area.spaces[0].shading\n                    if colour:\n                        sh.type = "MATERIAL"\n                    else:\n                        sh.type = "SOLID"\n                        sh.show_cavity = True\n                        sh.cavity_type = "BOTH"\n                        sh.light = "STUDIO"\n    except Exception as e:\n        print("view:", e)\n\n\ndef settings_job(st):\n    """The panel\'s settings (real mm) as the sizes the cutting works in (model units)."""\n    k = st.k or 1.0\n    return {"depth": st.depth * k, "tile_width": st.tile_w * k, "tile_height": st.tile_h * k,\n            "offset_x": st.off_x * k, "offset_y": st.off_y * k, "detail": st.detail,\n            "max_points": st.max_points * 1000, "mix": st.mix / 100.0, "seed": st.seed,\n            "invert": not st.light_out, "crisp": st.crisp / 100.0, "patch": st.patch,\n            "allow_slow": st.allow_slow}\n\n\ndef carve_one(ob, plain, img, job):\n    """Gives ob a fresh copy of its plain wall, carved. Returns a note for the panel."""\n    me = plain.data.copy()\n    old = ob.data\n    ob.data = me\n    if old is not None and old.users == 0:\n        bpy.data.meshes.remove(old)\n    tidy_mesh(ob.data)\n    shade_flat(ob.data)\n    normal = list(ob.get("rw_normal", (0, -1, 0)))\n    point = list(ob.get("rw_point", (0, 0, 0)))\n    axes = face_axes(normal)\n    tol = max(float(job["depth"]) * 0.05, 1e-6)\n    extent, d0 = face_extent(mesh_points(ob.data), normal, point, tol)\n    if job.get("patch"):                                   # just a 1 m square in the middle\n        half = 500.0 * (bpy.context.scene.rw.k or 1.0)\n        cu, cv = (extent[0] + extent[1]) / 2, (extent[2] + extent[3]) / 2\n        extent = (max(extent[0], cu - half), min(extent[1], cu + half),\n                  max(extent[2], cv - half), min(extent[3], cv + half))\n    import time as _t\n    t0 = _t.time()\n    # windows, doors and sills built onto the wall are separate pieces: they become their own part\n    # (not carved, no photo on them), and only the wall itself is carved - a clean solid, so the\n    # quick cut works. They go back to IngeTrazo, and to the printer, with the wall.\n    body, extras = split_body(ob.data, normal, d0, tol)\n    old_x = bpy.data.objects.get(ob.get("rw_extras", "")) if ob.get("rw_extras") else None\n    if old_x is not None:\n        me_x = old_x.data\n        bpy.data.objects.remove(old_x, do_unlink=True)\n        if me_x.users == 0:\n            bpy.data.meshes.remove(me_x)\n        del ob["rw_extras"]\n    if body is not None and extras is not None:\n        keep_tris = mesh_triangles(extras)\n        old = ob.data\n        ob.data = body\n        if old.users == 0:\n            bpy.data.meshes.remove(old)\n        shade_flat(extras)\n        extras.materials.append(fitting_material())\n        x_ob = make_object(ob.name + " - windows and doors", extras)\n        x_ob.matrix_world = ob.matrix_world.copy()\n        ob["rw_extras"] = x_ob.name\n    else:\n        keep_tris = mesh_triangles(ob.data)\n    how, cut = "", None\n    try:\n        done, size = carve_front(ob, img, job, keep_tris, normal, d0, extent, tol)\n        if done:\n            how = "quick"\n    except Exception as e:\n        print("Realistic Wall: rebuilding the face didn\'t work (%s) - cutting instead" % e)\n    if how != "quick":\n        verts, faces, size = build_cutter(extent, d0, axes, img, job, keep_tris)\n        cut = make_object(ob.name + " cutter", build_mesh(ob.name + " cutter", verts, faces))\n        tidy_mesh(cut.data)\n        how = carve(ob, cut, job.get("allow_slow"))\n    ok = how in ("quick", "slow")\n    if cut is not None:\n        me_cut = cut.data\n        bpy.data.objects.remove(cut, do_unlink=True)\n        bpy.data.meshes.remove(me_cut)\n    ob.data.materials.clear()\n    ob.data.materials.append(stone_material())\n    shade_flat(ob.data)\n    st = bpy.context.scene.rw\n    if ok and st.show_colour:\n        cp = colour_path_for(st)\n        if cp:\n            try:\n                add_colour(ob, img, job, cp)\n            except Exception as e:\n                print("Realistic Wall: colours:", e)\n    limited = size[3] < job["detail"] - 0.5\n    note = "detail %d%s, %s cut, %.0f s%s" % (round(size[3]), " (limited)" if limited else "", how or "no",\n                                            _t.time() - t0, " - test patch" if job.get("patch") else "")\n    gaps = int(plain.get("rw_open", 0))\n    if how == "too slow":\n        note = "quick cut didn\'t work - tick \'Allow the slow cut\' or lower J"\n    if how in ("slow", "too slow") and gaps > 0:\n        note += " (wall has %d open edges)" % gaps\n    elif not ok:\n        note = "could not cut"\n    ob["rw_note"] = note\n    print("Realistic Wall: %s - %s, %d kept plain" % (ob.name, note, size[2]))\n    return ok, note, limited\n\n\ndef carved_walls(scene):\n    out = []\n    for ob in scene.objects:\n        plain = bpy.data.objects.get(ob.get("rw_plain", "")) if ob.get("rw_plain") else None\n        if plain is not None:\n            out.append((ob, plain))\n    return out\n\n\ndef recarve_all(context, only_selected=False):\n    st = context.scene.rw\n    if not st.picture or not os.path.isfile(bpy.path.abspath(st.picture)):\n        return "Pick the picture first"\n    hp = height_picture_for(bpy.path.abspath(st.picture))\n    if hp:                                                  # a colour photo: use its height picture\n        st.busy = True\n        st.picture = hp\n        st.busy = False\n    img = load_picture(bpy.path.abspath(st.picture), st.blur)\n    job = settings_job(st)\n    if st.show_back:\n        st.busy = True\n        st.show_back = False\n        st.busy = False\n        show_what_goes_back(context, False)\n    walls = carved_walls(context.scene)\n    if only_selected:\n        walls = [w for w in walls if w[0].select_get()]\n    if not walls:\n        return "No carved walls here"\n    lim = bad = 0\n    for ob, plain in walls:\n        ok, note, limited = carve_one(ob, plain, img, job)\n        lim += bool(limited)\n        bad += not ok\n    st.last_note = (("Test patch carved." if st.patch else\n                     "Carved %d wall%s." % (len(walls), "" if len(walls) == 1 else "s")) +\n                    ("  Detail limited on %d - raise J." % lim if lim else "") +\n                    ("  %d not cut - see below." % bad if bad else ""))\n    return None\n\n\ndef _bm_tris(bm):\n    return sum(len(f.verts) - 2 for f in bm.faces)\n\n\ndef _join_flat(bm, tol):\n    """Planar: faces lying flat together joined into one (no detail lost)."""\n    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=tol)\n    try:\n        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.3), use_dissolve_boundaries=False,\n                                 verts=bm.verts[:], edges=bm.edges[:])\n    except Exception as e:\n        print("Realistic Wall: joining flat faces:", e)\n\n\ndef _collapse(bm, max_faces):\n    """Collapse: thins the bmesh to about max_faces triangles with Blender\'s Decimate, keeping the\n    shape. Returns a new bmesh (the old one is freed)."""\n    tris = _bm_tris(bm)\n    me = bpy.data.meshes.new("rw thin")\n    bm.to_mesh(me)\n    bm.free()\n    tmp = bpy.data.objects.new("rw thin", me)\n    bpy.context.scene.collection.objects.link(tmp)\n    out = None\n    try:\n        mod = tmp.modifiers.new("Thin", "DECIMATE")\n        mod.decimate_type = \'COLLAPSE\'\n        mod.ratio = max(0.01, min(1.0, 0.95 * max_faces / float(tris)))\n        try:\n            mod.use_collapse_triangulate = True\n        except Exception:\n            pass\n        dg = bpy.context.evaluated_depsgraph_get()\n        out = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))\n    except Exception as e:\n        print("Realistic Wall: thinning:", e)\n    bpy.data.objects.remove(tmp, do_unlink=True)\n    nb = bmesh.new()\n    nb.from_mesh(out if out is not None else me)\n    bpy.data.meshes.remove(me)\n    if out is not None:\n        bpy.data.meshes.remove(out)\n    print("Realistic Wall: thinned from %d to %d faces for IngeTrazo" % (tris, _bm_tris(nb)))\n    return nb\n\n\ndef full_mesh(ob):\n    """The wall\'s full-detail mesh (while \'Show what goes back\' is on, the wall shows a thinned copy)."""\n    name = ob.get("rw_full")\n    me = bpy.data.meshes.get(name) if name else None\n    return me if me is not None else ob.data\n\n\ndef show_what_goes_back(context, on):\n    """Swaps each carved wall to the thinned copy that goes back to IngeTrazo (on), or back to its\n    full detail (off)."""\n    st = context.scene.rw\n    total = 0\n    walls = [ob for ob, _p in carved_walls(context.scene)]\n    shares = face_shares(walls, st.max_faces * 1000)\n    for ob, share in zip(walls, shares):\n        full = full_mesh(ob)\n        if on:\n            pts, faces = clean_for_ingetrazo(ob, share, st.smooth)\n            inv = np.linalg.inv(np.array(ob.matrix_world))\n            P = np.array(pts) @ inv[:3, :3].T + inv[:3, 3]\n            me = build_mesh(ob.name + " (what goes back)", P, [tuple(f) for f in faces])\n            shade_flat(me)\n            for m in full.materials:\n                me.materials.append(m)\n            if not ob.get("rw_full"):\n                full.use_fake_user = True\n                ob["rw_full"] = full.name\n            old = ob.data\n            ob.data = me\n            if old is not full and old.users == 0:\n                bpy.data.meshes.remove(old)\n            ob["rw_back_faces"] = len(faces)\n            total += len(faces)\n        elif ob.get("rw_full"):\n            old = ob.data\n            ob.data = full\n            full.use_fake_user = False\n            del ob["rw_full"]\n            if old is not full and old.users == 0:\n                bpy.data.meshes.remove(old)\n    st.last_note = ("Showing what goes back: %d faces. Lower L until it starts to look worse." % total\n                    if on else "Showing the full-detail wall.")\n\n\ndef _back_changed(self, context):\n    if not self.busy:\n        show_what_goes_back(context, self.show_back)\n\n\ndef _faces_changed(self, context):\n    if not self.busy and self.show_back:\n        show_what_goes_back(context, True)\n\n\ndef _smooth_relief(bm, ob, times):\n    """Smooths the cut-in parts (joints, broken bits) a few times; the flat faces of the bricks, the\n    wall\'s own corners and the openings\' edges stay as they are."""\n    if times <= 0:\n        return\n    n = np.array(face_axes(list(ob.get("rw_normal", (0, -1, 0))))[2])\n    mw = np.array(ob.matrix_world)\n    p0 = np.array(ob.get("rw_point", (0, 0, 0)), float)\n    p0 = mw[:3, :3] @ p0 + mw[:3, 3]\n    n = mw[:3, :3] @ n\n    n = n / (np.linalg.norm(n) or 1.0)\n    d0 = float(p0 @ n)\n    depth = float(bpy.context.scene.rw.depth) * (bpy.context.scene.rw.k or 1.0)\n    tol = max(depth * 0.02, 1e-9)\n    sunk = [v for v in bm.verts if (d0 - depth * 1.5) < float(np.dot(v.co, n)) < d0 - tol and not v.is_boundary]\n    if not sunk:\n        return\n    for _ in range(int(times)):\n        try:\n            bmesh.ops.smooth_vert(bm, verts=sunk, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)\n        except Exception as e:\n            print("Realistic Wall: smoothing:", e)\n            return\n\n\ndef clean_for_ingetrazo(ob, max_faces=0, smooth=0):\n    """The wall\'s faces as IngeTrazo likes them, in the model\'s places: flat areas joined into whole\n    faces first (Planar - no fans of thin triangles, no detail lost), then thinned with Collapse only\n    if it\'s still over max_faces triangles, and any face that isn\'t quite flat (the tilted bits of the\n    stones) split into triangles, which always are. Returns (points, faces)."""\n    bm = bmesh.new()\n    bm.from_mesh(full_mesh(ob))\n    bm.transform(ob.matrix_world)\n    co = [v.co for v in bm.verts]\n    size = max((max(c[i] for c in co) - min(c[i] for c in co)) for i in range(3)) if co else 1.0\n    tol = max(size * 1e-6, 1e-9)\n    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=tol)\n    _smooth_relief(bm, ob, smooth)\n    _join_flat(bm, tol)\n    if max_faces and _bm_tris(bm) > max_faces:\n        bm = _collapse(bm, max_faces)\n        _join_flat(bm, tol)\n    bent = []\n    for f in bm.faces:\n        if len(f.verts) <= 3:\n            continue\n        c = f.calc_center_median()\n        nrm = f.normal\n        if any(abs((v.co - c).dot(nrm)) > tol * 10 for v in f.verts):\n            bent.append(f)\n    if bent:\n        bmesh.ops.triangulate(bm, faces=bent)\n    bm.verts.index_update()\n    pts = [tuple(v.co) for v in bm.verts]\n    faces = [[v.index for v in f.verts] for f in bm.faces]\n    bm.free()\n    return pts, faces\n\n\ndef face_shares(obs, total):\n    """\'L\' is for all the walls together: each wall gets its share, by how many faces it has."""\n    if not total:\n        return [0] * len(obs)\n    sizes = []\n    for ob in obs:\n        try:\n            sizes.append(max(1, len(full_mesh(ob).polygons)))\n        except Exception:\n            sizes.append(1)\n    tot = float(sum(sizes))\n    return [max(2000, int(total * n / tot)) for n in sizes]\n\n\ndef write_obj(path, obs, max_faces=0, smooth=0):\n    sent = 0\n    shares = face_shares(obs, max_faces)\n    with open(path, "w") as f:\n        f.write("# Eddy\'s Model Works - Realistic Wall\\n")\n        off = 1\n        for ob, share in zip(obs, shares):\n            pts, faces = clean_for_ingetrazo(ob, share, smooth)\n            x = extras_of(ob)\n            if x is not None:                              # the windows and doors go with it (not thinned)\n                xp, xf = clean_for_ingetrazo(x, 0, 0)\n                faces = faces + [[i + len(pts) for i in fc] for fc in xf]\n                pts = pts + xp\n            sent += len(faces)\n            f.write("o %s\\n" % ob.name)\n            f.write("".join("v %.7f %.7f %.7f\\n" % p for p in pts))\n            f.write("".join("f " + " ".join(str(i + off) for i in fc) + "\\n" for fc in faces))\n            off += len(pts)\n            print("Realistic Wall: sent %s - %d faces" % (ob.name, len(faces)))\n    return sent\n\n\nSETTINGS_NAME = "realistic wall settings.json"\nSCALE_STUDIO_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_scale_converter.json")\n\n\ndef scale_studio():\n    """Scale Studio\'s own settings: (scale, printers, the printer it has picked, its slicer, its bed,\n    its print folder). The scale and printers are only ever set in Scale Studio."""\n    try:\n        with open(SCALE_STUDIO_FILE, "r", encoding="utf-8") as f:\n            d = json.load(f)\n    except Exception:\n        d = {}\n    st = d.get("studio") if isinstance(d.get("studio"), dict) else {}\n    try:\n        scale = float(st.get("scale") or d.get("scale") or 76.2)\n    except Exception:\n        scale = 76.2\n    printers = [p for p in (st.get("printers") or []) if isinstance(p, dict) and p.get("name")]\n    picked = str(st.get("printer") or "")\n    picked = picked.split(":", 1)[1] if picked.startswith("own:") else ""\n    bed = [float(st.get(k, v)) for k, v in (("bed_x", 220.0), ("bed_y", 220.0), ("bed_z", 250.0))]\n    folder = st.get("print_folder") or os.path.join(os.path.expanduser("~"), "Downloads", "3D Scale Studio")\n    return {"scale": scale, "printers": printers, "picked": picked, "slicer": str(st.get("slicer") or ""),\n            "slicers": list(st.get("slicers") or []), "bed": bed, "folder": folder}\n\n\ndef _printer_items(self, context):\n    ss = scale_studio()\n    items = [(p["name"], p["name"], "A printer set up in Scale Studio") for p in ss["printers"]]\n    if not items:\n        items = [("_", "Scale Studio\'s printer", "The printer and slicer set in Scale Studio")]\n    _printer_items.keep = items           # Blender needs the list kept\n    return items\n\n\ndef printer_setup(name):\n    """(slicer program, bed size [x, y, z] mm) for a Scale Studio printer."""\n    ss = scale_studio()\n    p = next((x for x in ss["printers"] if x.get("name") == name), None)\n    if p is None:\n        p = next((x for x in ss["printers"] if x.get("name") == ss["picked"]), None)\n    slicer, bed = ss["slicer"] or (ss["slicers"] + [""])[0], ss["bed"]\n    if p is not None:\n        slicer = str(p.get("slicer") or (list(p.get("slicers") or []) + [""])[0] or slicer)\n        try:\n            bed = [float(x) for x in (p.get("bed") or bed)][:3]\n        except Exception:\n            pass\n    return slicer, bed\n\n\ndef print_triangles(ob, smooth):\n    """The wall at full detail as triangles, in the model\'s places (no thinning - it\'s going to the\n    printer, not IngeTrazo)."""\n    bm = bmesh.new()\n    bm.from_mesh(full_mesh(ob))\n    bm.transform(ob.matrix_world)\n    co = [v.co for v in bm.verts]\n    size = max((max(c[i] for c in co) - min(c[i] for c in co)) for i in range(3)) if co else 1.0\n    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=max(size * 1e-6, 1e-9))\n    _smooth_relief(bm, ob, smooth)\n    bmesh.ops.triangulate(bm, faces=bm.faces[:])\n    tris = np.array([[tuple(v.co) for v in f.verts] for f in bm.faces], dtype=np.float64)\n    bm.free()\n    return tris\n\n\ndef lay_flat(tris, normal):\n    """Turns the wall so its stone face points straight up, and sits it on the bed (z = 0)."""\n    n = np.array(normal, float)\n    n = n / (np.linalg.norm(n) or 1.0)\n    z = np.array([0.0, 0.0, 1.0])\n    c = float(n @ z)\n    if c < -0.9999:\n        R = np.diag([1.0, -1.0, -1.0])\n    else:\n        v = np.cross(n, z)\n        K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])\n        R = np.eye(3) + K + K @ K / (1.0 + c)\n    return tris @ R.T\n\n\ndef write_stl(path, tris):\n    """Binary STL (mm)."""\n    t = tris.astype(np.float32)\n    nrm = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])\n    ln = np.linalg.norm(nrm, axis=1, keepdims=True)\n    nrm = (nrm / np.where(ln > 0, ln, 1)).astype(np.float32)\n    rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])\n    rec["n"], rec["v"] = nrm, t\n    with open(path, "wb") as f:\n        f.write(b"Eddy\'s Model Works - Realistic Wall".ljust(80, b" "))\n        f.write(np.uint32(len(t)).tobytes())\n        f.write(rec.tobytes())\n\n\ndef print_walls(context):\n    """Saves each carved wall at Scale Studio\'s scale, laid flat, and opens them in the printer\'s\n    slicer. Returns (message, warning)."""\n    import subprocess\n    st = context.scene.rw\n    walls = carved_walls(context.scene)\n    if not walls:\n        return "No carved walls to print", True\n    ss = scale_studio()\n    slicer, bed = printer_setup(st.printer)\n    k = st.k or 1.0\n    to_mm = 1.0 / k / ss["scale"]               # model units -> real mm -> printed mm\n    folder = ss["folder"]\n    os.makedirs(folder, exist_ok=True)\n    files, big = [], []\n    label = ("%g" % ss["scale"]).replace(".", ".")\n    for ob, _p in walls:\n        tris = print_triangles(ob, 0)                   # full detail: M smoothing is only for IngeTrazo\n        x = extras_of(ob)\n        if x is not None:\n            tris = np.concatenate([tris, print_triangles(x, 0)])\n        tris = tris * to_mm\n        if st.print_flat:\n            mw = np.array(ob.matrix_world)\n            tris = lay_flat(tris, mw[:3, :3] @ np.array(face_axes(list(ob.get("rw_normal", (0, -1, 0))))[2]))\n        lo, hi = tris.reshape(-1, 3).min(0), tris.reshape(-1, 3).max(0)\n        tris = tris - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])   # middle of the bed, on it\n        size = hi - lo\n        if size[0] > bed[0] or size[1] > bed[1] or size[2] > bed[2]:\n            if size[1] <= bed[0] and size[0] <= bed[1] and size[2] <= bed[2]:\n                tris = tris[..., [1, 0, 2]] * np.array([1, -1, 1])        # fits turned round\n            else:\n                big.append("%s (%.0f x %.0f x %.0f mm)" % (ob.name, size[0], size[1], size[2]))\n        safe = "".join(ch if ch.isalnum() or ch in " -_()" else "_" for ch in ob.name).strip() or "Wall"\n        path = os.path.join(folder, "%s - realistic 1-%s.stl" % (safe, label))\n        write_stl(path, tris)\n        files.append(path)\n        print("Realistic Wall: %s - %d triangles, %.1f x %.1f x %.1f mm -> %s"\n              % (ob.name, len(tris), size[0], size[1], size[2], path))\n    try:\n        if slicer and os.path.isfile(slicer):\n            subprocess.Popen([slicer] + files)\n            how = "opened in %s" % os.path.splitext(os.path.basename(slicer))[0]\n        elif hasattr(os, "startfile"):\n            os.startfile(files[0] if len(files) == 1 else folder)\n            how = "opened"\n        else:\n            how = "saved"\n    except Exception as e:\n        return "Saved, but couldn\'t open the slicer: %s" % e, True\n    msg = "%d wall%s at 1:%s %s (saved in %s)." % (len(files), "" if len(files) == 1 else "s", label, how, folder)\n    if big:\n        msg += " Bigger than the bed: %s - split it in Scale Studio." % ", ".join(big)\n    return msg, bool(big)\n\n\ndef keep_settings(context, save_file=True):\n    """Writes the panel\'s settings beside the carved walls (the plugin in IngeTrazo picks them up), and\n    saves this Blender file so they are here next time it\'s opened."""\n    st = context.scene.rw\n    d = {"depth": st.depth, "tile_w": st.tile_w, "tile_h": st.tile_h, "detail": st.detail, "blur": st.blur,\n         "off_x": st.off_x, "off_y": st.off_y, "mix": st.mix, "seed": st.seed, "max_pts": st.max_points,\n         "crisp": st.crisp, "light_out": bool(st.light_out), "picture": bpy.path.abspath(st.picture),\n         "colour": bool(st.show_colour), "allow_slow": bool(st.allow_slow), "max_faces": st.max_faces,\n         "smooth": st.smooth}\n    if st.out_obj:\n        try:\n            with open(os.path.join(os.path.dirname(st.out_obj), SETTINGS_NAME), "w", encoding="utf-8") as f:\n                json.dump(d, f, indent=1)\n        except Exception as e:\n            print("Realistic Wall: settings not kept:", e)\n    if save_file and bpy.data.filepath:\n        try:\n            bpy.ops.wm.save_mainfile()\n        except Exception as e:\n            print("Realistic Wall: Blender file not saved:", e)\n\n\n# the settings the Reset button puts back (the same as the plugin in IngeTrazo starts with);\n# the picture itself is kept\nRESET = {"depth": 30.0, "tile_w": 2500.0, "tile_h": 2500.0, "detail": 300, "blur": 0, "off_x": 0.0, "off_y": 0.0,\n         "mix": 60, "seed": 1, "max_points": 1000, "crisp": 50, "light_out": True, "smooth": 2, "max_faces": 150,\n         "patch": False, "allow_slow": False, "auto": False, "show_colour": True}\n\n\ndef reset_settings(context):\n    st = context.scene.rw\n    st.busy = True\n    try:\n        for k, v in RESET.items():\n            setattr(st, k, v)\n    finally:\n        st.busy = False\n    keep_settings(context)\n\n\n# ---- the panel ----\ndef _auto(self, context):\n    if self.auto and not self.busy:\n        self.busy = True\n        try:\n            recarve_all(context)\n        finally:\n            self.busy = False\n\n\nif IN_BLENDER:\n    from bpy.props import FloatProperty, IntProperty, BoolProperty, StringProperty, PointerProperty, EnumProperty\n\n    class RW_Settings(bpy.types.PropertyGroup):\n        picture: StringProperty(name="Picture", subtype=\'FILE_PATH\', update=_auto,\n                                description="The wall picture the stone shape comes from - light parts stand "\n                                "out, dark parts sink in")\n        depth: FloatProperty(name="A  Depth of the joints (mm)", default=30.0, min=0.5, max=500.0, update=_auto,\n                              description="How far the darkest parts (the joints) are cut into the wall, in "\n                              "real-size mm")\n        tile_w: FloatProperty(name="B  Picture covers across (mm)", default=2000.0, min=50.0, max=20000.0,\n                              update=_auto, description="How wide a piece of real wall one picture covers - "\n                              "bigger makes the stones bigger")\n        tile_h: FloatProperty(name="C  Picture covers up (mm)", default=2000.0, min=50.0, max=20000.0,\n                              update=_auto, description="How tall a piece of real wall one picture covers - "\n                              "bigger makes the stones taller")\n        detail: IntProperty(name="D  Detail (resolution)", default=300, min=20, max=2000, update=_auto,\n                            description="Points across one picture. More is sharper but slower")\n        blur: IntProperty(name="E  Smooth the picture", default=1, min=0, max=10, update=_auto,\n                          description="Softens the picture before carving - takes out speckles and grain "\n                          "(0 = as it is)")\n        off_x: FloatProperty(name="F  Move picture along (mm)", default=0.0, update=_auto,\n                             description="Slides the stone pattern along the wall, to line a joint up with a "\n                             "corner or an opening")\n        off_y: FloatProperty(name="G  Move picture up (mm)", default=0.0, update=_auto,\n                             description="Slides the stone pattern up the wall, to put a course on the "\n                             "ground or under a window sill")\n        mix: IntProperty(name="H  Hide the repeats (%)", default=60, min=0, max=100, update=_auto,\n                         description="Mixes in a mirrored copy of the picture in big patches so you can\'t see "\n                         "it repeating along the wall (0 = plain repeats)")\n        seed: IntProperty(name="I  Pattern number", default=1, min=1, max=999, update=_auto,\n                          description="A different number gives a different spread of the patches from H")\n        max_points: IntProperty(name="J  Most points per wall (thousands)", default=600, min=50, max=20000,\n                                update=_auto, description="Limits the detail on a big wall so the cut "\n                                "doesn\'t take too long. Raise it if your PC can cope")\n        light_out: BoolProperty(name="Light parts stand out", default=True, update=_auto,\n                                description="Ticked: light parts of the picture stand out and dark parts sink "\n                                "in. Untick it if your photo has light mortar between darker bricks")\n        smooth: IntProperty(name="M  Smooth the stone (times)", default=2, min=0, max=10, update=_faces_changed,\n                            description="Smooths the cut-in parts (joints, broken bits) of what goes back to "\n                            "IngeTrazo - less crinkly there. Never used for printing: the printer gets full detail")\n        printer: EnumProperty(name="Printer", items=_printer_items,\n                              description="Your printers from Scale Studio (each opens its own slicer)")\n        print_flat: BoolProperty(name="Lay it flat, face up", default=True,\n                                 description="The stone face points straight up, the back of the wall on the bed")\n        show_back: BoolProperty(name="Show what goes back", default=False, update=_back_changed,\n                                description="Shows the thinned copy that goes back to IngeTrazo, so you can "\n                                "lower L until you\'re happy with it. Untick it to see (and edit) the full wall")\n        max_faces: IntProperty(name="L  Most faces brought back (thousands, all walls)", default=150, min=5, max=5000,\n                               update=_faces_changed,\n                               description="What goes back to IngeTrazo is thinned to about this many "\n                               "triangles for all the walls together, keeping the shape - IngeTrazo slows right down with too many. "\n                               "The wall here keeps all its detail")\n        crisp: IntProperty(name="K  Crisp edges (%)", default=50, min=0, max=100, update=_auto,\n                           description="Flatter brick faces and sharper steps down into the joints")\n        patch: BoolProperty(name="Just a 1 m test patch (quick)", default=False, update=_auto,\n                            description="Carves only a 1 m square in the middle of each wall, to try settings")\n        show_colour: BoolProperty(name="Show the colours", default=True,\n                                  update=lambda self, context: None if self.busy else apply_colours(context),\n                                  description="Puts the colour photo on the walls, lined up with the "\n                                  "carving - just for looking, the shape doesn\'t change")\n        colour_picture: StringProperty(name="Colour", subtype=\'FILE_PATH\',\n                                       update=lambda self, context: None if self.busy else apply_colours(context),\n                                       description="The colour photo (found beside the height picture)")\n        allow_slow: BoolProperty(name="Allow the slow cut", default=False,\n                                 description="If the quick cut doesn\'t work on a wall (it isn\'t a closed "\n                                 "solid), use the slow one anyway - can take a long time on a big wall")\n        auto: BoolProperty(name="Update as I change", default=False,\n                           description="Carve again every time a setting changes (slow on big walls)")\n        k: FloatProperty(default=1.0)\n        out_obj: StringProperty(default="")\n        last_note: StringProperty(default="")\n        busy: BoolProperty(default=False)\n\n    class RW_OT_recarve(bpy.types.Operator):\n        bl_idname = "eddy_rw.recarve"\n        bl_label = "Re-carve the walls"\n        bl_description = "Carves the walls again from the plain walls, with these settings (hand edits are lost)"\n\n        def execute(self, context):\n            msg = recarve_all(context)\n            if msg:\n                self.report({\'WARNING\'}, msg)\n                return {\'CANCELLED\'}\n            keep_settings(context)\n            self.report({\'INFO\'}, context.scene.rw.last_note)\n            return {\'FINISHED\'}\n\n    class RW_OT_reset(bpy.types.Operator):\n        bl_idname = "eddy_rw.reset"\n        bl_label = "Reset to defaults"\n        bl_description = ("Puts all the settings back to how they start (the picture is kept). "\n                          "Then Re-carve the walls to see them")\n\n        def invoke(self, context, event):\n            return context.window_manager.invoke_confirm(self, event)\n\n        def execute(self, context):\n            reset_settings(context)\n            context.scene.rw.last_note = "Settings back to defaults - click Re-carve the walls to see them."\n            self.report({\'INFO\'}, "Realistic Wall: settings back to defaults")\n            return {\'FINISHED\'}\n\n    class RW_OT_send(bpy.types.Operator):\n        bl_idname = "eddy_rw.send"\n        bl_label = "Send to IngeTrazo"\n        bl_description = ("Only if you really need them in the model: saves the carved walls (thinned to L) for "\n                          "\'Bring the walls back\' in IngeTrazo. Carved walls can slow IngeTrazo right down - "\n                          "printing from here is best")\n\n        def invoke(self, context, event):\n            wm = context.window_manager\n            try:\n                return wm.invoke_confirm(self, event, title="Send to IngeTrazo?",\n                                         message="Carved walls are very detailed and can slow IngeTrazo right "\n                                                 "down. Printing from here is best. Send them anyway?",\n                                         confirm_text="Send anyway", icon=\'WARNING\')\n            except TypeError:                                  # older Blender\n                return wm.invoke_confirm(self, event)\n\n        def execute(self, context):\n            st = context.scene.rw\n            walls = [ob for ob, _p in carved_walls(context.scene)]\n            if not walls or not st.out_obj:\n                self.report({\'WARNING\'}, "No carved walls to send")\n                return {\'CANCELLED\'}\n            if context.object is not None and context.object.mode != \'OBJECT\':\n                bpy.ops.object.mode_set(mode=\'OBJECT\')          # takes in edits made in Edit/Sculpt Mode\n            n = write_obj(st.out_obj, walls, st.max_faces * 1000, st.smooth)\n            st.last_note = "Sent %d faces - \'Bring the walls back\' in IngeTrazo (it may slow it down)." % n\n            keep_settings(context)\n            self.report({\'INFO\'}, st.last_note)\n            return {\'FINISHED\'}\n\n    class RW_OT_print(bpy.types.Operator):\n        bl_idname = "eddy_rw.print"\n        bl_label = "Send to my printer"\n        bl_description = ("Saves the carved walls at full detail, at Scale Studio\'s scale, laid flat, and opens "\n                          "them in the printer\'s slicer")\n\n        def execute(self, context):\n            if context.object is not None and context.object.mode != \'OBJECT\':\n                bpy.ops.object.mode_set(mode=\'OBJECT\')\n            msg, bad = print_walls(context)\n            context.scene.rw.last_note = msg\n            self.report({\'WARNING\'} if bad else {\'INFO\'}, msg)\n            keep_settings(context)\n            return {\'FINISHED\'}\n\n    class RW_PT_panel(bpy.types.Panel):\n        bl_label = "Realistic Wall"\n        bl_space_type = \'VIEW_3D\'\n        bl_region_type = \'UI\'\n        bl_category = "Realistic Wall"\n\n        def draw(self, context):\n            st = context.scene.rw\n            col = self.layout.column()\n            for name in ("depth", "tile_w", "tile_h", "detail", "blur", "off_x", "off_y", "mix", "seed",\n                         "max_points", "crisp"):\n                col.prop(st, name)\n            col.separator()\n            col.prop(st, "patch")\n            col.prop(st, "allow_slow")\n            col.prop(st, "auto")\n            col.operator("eddy_rw.recarve", icon=\'MOD_BOOLEAN\')\n            col.operator("eddy_rw.reset", icon=\'LOOP_BACK\')\n            pbox = col.box()\n            pbox.label(text="Print it (scale 1:%g from Scale Studio)" % scale_studio()["scale"], icon=\'MOD_SOLIDIFY\')\n            pbox.prop(st, "printer")\n            pbox.prop(st, "print_flat")\n            pbox.operator("eddy_rw.print", icon=\'FILE_3D\')\n            if st.last_note:\n                col.label(text=st.last_note)\n            for ob, _p in carved_walls(context.scene):\n                if ob.get("rw_note"):\n                    box = col.box()\n                    box.label(text=ob.name, icon=\'MESH_PLANE\')\n                    box.label(text=ob["rw_note"])\n\n    class RW_PT_picture(bpy.types.Panel):\n        """The picture settings - rolled up to start with (they\'re usually set in IngeTrazo)."""\n        bl_label = "Picture"\n        bl_space_type = \'VIEW_3D\'\n        bl_region_type = \'UI\'\n        bl_category = "Realistic Wall"\n        bl_parent_id = "RW_PT_panel"\n        bl_options = {\'DEFAULT_CLOSED\'}\n\n        def draw(self, context):\n            st = context.scene.rw\n            col = self.layout.column()\n            col.prop(st, "picture")\n            col.prop(st, "light_out")\n            col.prop(st, "show_colour")\n            if st.show_colour:\n                col.prop(st, "colour_picture")\n\n    class RW_PT_back(bpy.types.Panel):\n        """Bringing the walls back into IngeTrazo - rolled up: only if you really need to."""\n        bl_label = "Back to IngeTrazo (only if you need to)"\n        bl_space_type = \'VIEW_3D\'\n        bl_region_type = \'UI\'\n        bl_category = "Realistic Wall"\n        bl_parent_id = "RW_PT_panel"\n        bl_options = {\'DEFAULT_CLOSED\'}\n\n        def draw(self, context):\n            st = context.scene.rw\n            col = self.layout.column()\n            warn = col.box().column(align=True)\n            warn.label(text="Carved walls are very detailed and can", icon=\'ERROR\')\n            warn.label(text="slow IngeTrazo right down. Printing")\n            warn.label(text="from here (Send to my printer) is best.")\n            col.prop(st, "max_faces")\n            col.prop(st, "smooth")\n            col.prop(st, "show_back")\n            if st.show_back:\n                col.label(text="Untick to edit or re-carve the full wall")\n            col.operator("eddy_rw.send", icon=\'EXPORT\')\n\n    CLASSES = (RW_Settings, RW_OT_recarve, RW_OT_reset, RW_OT_send, RW_OT_print, RW_PT_panel, RW_PT_picture, RW_PT_back)\n\n\ndef register():\n    for c in CLASSES:\n        try:\n            bpy.utils.unregister_class(c)\n        except Exception:\n            pass\n        bpy.utils.register_class(c)\n    bpy.types.Scene.rw = bpy.props.PointerProperty(type=RW_Settings)\n\n\ndef view_nicely():\n    try:\n        for win in bpy.context.window_manager.windows:\n            for area in win.screen.areas:\n                if area.type == "VIEW_3D":\n                    sp = area.spaces[0]\n                    sh = sp.shading\n                    sh.type = "SOLID"\n                    sh.show_cavity = True\n                    sh.cavity_type = "BOTH"\n                    sh.light = "STUDIO"\n                    if bpy.context.scene.rw.show_colour and bpy.context.scene.rw.colour_picture:\n                        sh.type = "MATERIAL"\n                    try:\n                        sp.show_region_ui = True             # the N sidebar, with the panel in it\n                    except Exception:\n                        pass\n                    with bpy.context.temp_override(window=win, area=area,\n                                                   region=[r for r in area.regions if r.type == "WINDOW"][0]):\n                        bpy.ops.view3d.view_selected()\n    except Exception as e:\n        print("view:", e)\n    return None\n\n\ndef run(job_path):\n    job = json.load(open(job_path))\n    register()\n    for ob in list(bpy.data.objects):                 # start from an empty scene\n        bpy.data.objects.remove(ob, do_unlink=True)\n    sc = bpy.context.scene\n    st = sc.rw\n    k = float(job.get("k") or 1.0)\n    st.busy = True                                    # don\'t carve while filling in the settings\n    st.k = k\n    st.picture = job["picture"]\n    st.depth = job["depth"] / k\n    st.tile_w, st.tile_h = job["tile_width"] / k, job["tile_height"] / k\n    st.off_x, st.off_y = job.get("offset_x", 0.0) / k, job.get("offset_y", 0.0) / k\n    st.detail = int(job.get("detail", 150))\n    st.blur = int(job.get("blur", 1))\n    st.mix = int(round(float(job.get("mix", 0.0)) * 100))\n    st.seed = int(job.get("seed", 1))\n    st.max_points = max(50, int(job.get("max_points", MAX_POINTS)) // 1000)\n    st.light_out = not job.get("invert")\n    st.crisp = int(round(float(job.get("crisp", 0.0)) * 100))\n    st.patch = bool(job.get("patch"))\n    st.allow_slow = bool(job.get("allow_slow"))\n    st.show_colour = bool(job.get("colour", True))\n    st.max_faces = max(5, int(job.get("max_faces", 150)))\n    st.smooth = int(job.get("smooth", 2))\n    st.colour_picture = ""\n    st.out_obj = job.get("out_obj", "")\n    st.busy = False\n\n    plains = bpy.data.collections.get(PLAIN_COLL) or bpy.data.collections.new(PLAIN_COLL)\n    if plains.name not in sc.collection.children:\n        sc.collection.children.link(plains)\n    walls = []\n    for wall in job["walls"]:\n        ex = list(wall.get("extra") or [])\n        faces, marks, seen = [], [], set()\n        for k, f in enumerate(wall["faces"]):           # the same triangle twice: keep it once\n            key = tuple(sorted(f))\n            if key in seen:\n                continue\n            seen.add(key)\n            faces.append(tuple(f))\n            marks.append(ex[k] if k < len(ex) else 0)\n        me = build_mesh(wall["name"] + " (plain)", wall["verts"], faces,\n                        {"rw_extra": marks} if any(marks) else None)\n        tidy_mesh(me)\n        gaps = close_gaps(me)\n        shade_flat(me)\n        print("Realistic Wall: %s - %s" % (wall["name"], "closed solid" if gaps == 0 else\n                                           "%d open edges left" % gaps))\n        plain = make_object(wall["name"] + " (plain)", me, plains)\n        plain["rw_open"] = gaps\n        ob = make_object(wall["name"], plain.data.copy())\n        ob["rw_plain"] = plain.name\n        ob["rw_normal"] = list(wall["normal"])\n        ob["rw_point"] = list(wall["point"])\n        walls.append(ob)\n    plains.hide_viewport = True\n    plains.hide_render = True\n    msg = recarve_all(bpy.context)\n    if msg:\n        print("Realistic Wall:", msg)\n    for ob in walls:\n        ob.select_set(True)\n    if walls:\n        bpy.context.view_layer.objects.active = walls[0]\n    if st.out_obj:\n        keep_settings(bpy.context, save_file=False)       # tells the plugin the carving is done\n    # keep this script in the Blender file, so the panel is there when it\'s opened again\n    try:\n        src = open(__file__, encoding="utf-8").read()\n        t = bpy.data.texts.get("realistic_wall.py") or bpy.data.texts.new("realistic_wall.py")\n        t.clear()\n        t.write(src)\n        t.use_module = True\n    except Exception as e:\n        print("Realistic Wall: script not kept in the file:", e)\n    blend = job.get("out_blend")\n    bpy.app.timers.register(view_nicely, first_interval=0.5)\n    if blend:\n        def save_later():                                  # once the wall is on screen\n            try:\n                bpy.ops.wm.save_as_mainfile(filepath=blend)\n            except Exception as e:\n                print("Realistic Wall: Blender file not saved:", e)\n            return None\n        bpy.app.timers.register(save_later, first_interval=2.0)\n    print("Realistic Wall: done")\n\n\nif IN_BLENDER:\n    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []\n    if __name__ == "__main__" and argv:\n        run(argv[0])\n    else:\n        register()             # opened again from a saved file: just put the panel back\n'


HEIGHT_WORDS = ("_disp", "_displacement", "_height", "_heightmap", "_bump")
COLOUR_WORDS = ("_diff", "_diffuse", "_col", "_color", "_colour", "_albedo", "_basecolor", "_base_color")


def colour_picture_for(path):
    """For a height picture (name_disp_4k.png) with its colour photo beside it (name_diff_4k.jpg),
    the colour photo's path - else None."""
    folder, fn = os.path.split(path)
    low = fn.lower()
    for w in HEIGHT_WORDS:
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
            for cw in COLOUR_WORDS:
                if o.startswith(stem + cw) and o.endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp")):
                    score = (os.path.splitext(o[len(stem + cw):])[0] == rest, o.endswith((".jpg", ".jpeg")))
                    if best is None or score > best[0]:
                        best = (score, os.path.join(folder, other))
        return best[1] if best else None
    return None


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
        'max_faces': int(values.get('max_faces', 150)), 'smooth': int(values.get('smooth', 2)),
        'out_obj': os.path.join(folder, "realistic wall.obj"),
        'out_blend': os.path.join(folder, "realistic wall.blend") if keep_blend else "",
        'walls': [],
    }
    used = {}
    for w in walls:
        pts, tris, extra = wall_mesh_data(w)
        fd = w['polys'][w['face']]
        nm = w['name']
        used[nm] = used.get(nm, 0) + 1
        if used[nm] > 1:
            nm = "%s (%d)" % (nm, used[nm])
        # only worth telling apart if some of it is the wall's own paint and some isn't
        if not (0 < sum(extra) < len(extra)):
            extra = []
        job['walls'].append({'name': nm, 'verts': pts, 'faces': tris, 'normal': list(fd['n']),
                             'point': list(fd['pts'][0]), 'extra': extra})
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
             "1. <b>Walls</b>: pick the building to work on from the Building list (the selected one is picked for "
             "you). Tick the "
             "walls in the list, or click them in the picture on the left. Click the other side of a ticked "
             "wall to carve that side instead (the side that gets the stone is drawn brown).<br>"
             "2. <b>Picture</b>: choose the folder your wall pictures are in, and click a picture. Light parts "
             "stand out, dark parts (the joints) sink in. A height map (grey picture) works best, but a photo "
             "works too.<br>"
             "Set how big a piece of wall the picture shows (a picture called '2x2' is usually 2 x 2 m; "
             "'Get wall pictures online' sets it for you).<br>"
             "3. Click <b>Carve the walls</b>. Your 3D program opens with the walls carved. Its <b>Realistic "
             "Wall</b> panel (press N) has all the settings - depth, detail, crisp edges, hide the repeats, a "
             "quick 1 m test patch: change them and click Re-carve. Edit or sculpt the walls there if you like.<br>"
             "4. To print, click <b>Send to my printer</b> in the 3D program's panel: full detail, at Scale "
             "Studio's scale, straight into your slicer. That's the best way.<br>"
             "5. Only if you really need them in the model: in the panel's rolled-up <b>Back to IngeTrazo</b> "
             "section click <b>Send to IngeTrazo</b>, then <b>Bring the walls back</b> here. Carved walls are very "
             "detailed and can slow IngeTrazo right down. The Program page says what happens to the plain "
             "walls: left, hidden, or replaced by the carved ones.<br><br>"
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
                   "Pick the building on the Walls page to see its walls here.")
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
        self._key_view = ks                               # (sizes are set in the 3D program now)
        self.views.setTabToolTip(0, "The walls found. Click one to tick it; click the other side of a ticked "
                                    "wall to carve that side.")
        self.views.setTabToolTip(1, "The picture you've chosen.")

        side.addWidget(self.views, 1)

        self.tabs = TwoRowTabs(1)
        side.addWidget(self.tabs, 1)
        self._walls_page()
        self._picture_page(st)
        self._sizes_page()
        self._blender_page(st)
        tips = ["Find the walls and tick the ones that get a stone face.",
                "Choose the picture of a wall, and how big a piece of wall it shows.",
                "Where your 3D program is, where the carved walls are saved, and what happens to the plain "
                "walls when the carved ones come back."]
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
        self.preset_bar = QWidget()
        self.preset_bar.setLayout(prow)
        lay.addWidget(self.preset_bar)
        self.preset_bar.setVisible(False)                 # sizes are tuned in the 3D program now

        brow = QHBoxLayout()
        self.btn_make = QPushButton("Carve the walls")
        self.btn_make.setDefault(True)
        self.btn_back = QPushButton("Bring the walls back...")
        self.btn_back.setToolTip("Only if you really need the carved walls in the model - they're very detailed and "
                                 "can slow IngeTrazo right down. Printing from the 3D program is best.")
        self.b_info = QPushButton("Info")
        self.b_info.setCheckable(True)
        self.b_info.toggled.connect(self.info_box.setVisible)
        self.cb_lasttab = QCheckBox("Open at the last page used")
        self.cb_lasttab.setChecked(bool(st.get('remember_tab', True)))
        b_close = QPushButton("Close")
        self.b_reset = QPushButton("Reset to defaults")
        self.b_reset.setToolTip("Puts all the carving settings back to how they start (the picture you've "
                                "picked is kept). The 3D program has the same button in its panel.")
        self.cb_patch = QCheckBox("1 m test patch")
        self.cb_patch.setToolTip("Carves just a 1 m square in the middle of each ticked wall - quick, to try the "
                                 "settings. Untick it for the whole wall.")
        self.cb_patch.setChecked(bool(st.get('patch')))
        self.cb_patch.toggled.connect(lambda on: save_settings(patch=bool(on)))
        brow.addWidget(self.btn_make)
        brow.addWidget(self.cb_patch)
        self.cb_patch.setVisible(False)                   # the test patch is in the 3D program's panel
        brow.addWidget(self.btn_back)
        brow.addStretch(1)
        brow.addWidget(self.b_reset)
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
        self.b_reset.clicked.connect(self.reset_defaults)
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
        QTimer.singleShot(150, self._first_find)

    def _first_find(self):
        """When the window opens: picks the building (the selected one, else the biggest model)
        and finds its walls straight away."""
        try:
            self.refresh_buildings()
            self.find()
        except Exception as e:
            print("%s: couldn't find the walls by itself: %s" % (PLUGIN_NAME, e))

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
        info = QLabel("Pick the building to work on, then tick the walls that get a stone face - here, or by "
                      "clicking them in the picture on the left. The side that gets the stone is drawn brown: "
                      "click the other side of a ticked wall to swap.")
        info.setWordWrap(True)
        lay.addWidget(info)
        brow_ = QHBoxLayout()
        brow_.addWidget(QLabel("Building:"))
        self.cb_building = QComboBox()
        self.cb_building.setToolTip("The building (model) to work on. If you've selected something in the model, "
                                    "its building is picked for you.")
        brow_.addWidget(self.cb_building, 1)
        b_sel = QPushButton("Use the selected one")
        b_sel.setToolTip("Picks the building you've selected in the model.")
        brow_.addWidget(b_sel)
        lay.addLayout(brow_)
        b_find = QPushButton("Find walls again")
        b_find.setToolTip("Looks at the building again (after you've changed it).")
        lay.addWidget(b_find)
        self._tops = []
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
        b_sel.clicked.connect(lambda: (self.refresh_buildings(True), self.find()))
        self.cb_building.currentIndexChanged.connect(lambda *_: None if self._busy else self.find())
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
        b_online = QPushButton("Get wall pictures online...")
        b_online.setToolTip("Browse free wall, brick and stone pictures from Poly Haven (CC0) and download one "
                            "into this folder - it's picked for you, with B and C set to its size.")
        row.addWidget(b_choose)
        row.addWidget(b_open)
        row.addWidget(b_online)
        row.addStretch(1)
        lay.addLayout(row)
        b_online.clicked.connect(self.get_online)
        from PySide6.QtWidgets import QListView
        self.lst_pics = QListWidget()
        self.lst_pics.setViewMode(QListView.IconMode)
        self.lst_pics.setIconSize(QSize(96, 96))
        self.lst_pics.setGridSize(QSize(116, 128))
        self.lst_pics.setResizeMode(QListView.Adjust)
        self.lst_pics.setMovement(QListView.Static)
        self.lst_pics.setWordWrap(True)
        self.lst_pics.setToolTip("Click the picture to use. Right-click one to take it off the list or delete it.")
        self.lst_pics.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lst_pics.customContextMenuRequested.connect(self._pics_menu)
        lay.addWidget(self.lst_pics, 1)
        drow = QHBoxLayout()
        b_hide = QPushButton("Take off the list")
        b_hide.setToolTip("Hides the clicked picture here - the file stays in the folder. 'Show hidden ones' "
                          "brings it back.")
        b_del = QPushButton("Delete the file...")
        b_del.setToolTip("Deletes the clicked picture's file (it goes to the Recycle Bin, so you can get it back "
                         "from there).")
        self.b_unhide = QPushButton("Show hidden ones")
        self.b_unhide.setToolTip("Puts the pictures you've taken off the list back on it.")
        drow.addWidget(b_hide)
        drow.addWidget(b_del)
        drow.addWidget(self.b_unhide)
        drow.addStretch(1)
        lay.addLayout(drow)
        b_hide.clicked.connect(lambda: self.hide_picture(self._clicked_pic()))
        b_del.clicked.connect(lambda: self.delete_picture(self._clicked_pic()))
        self.b_unhide.clicked.connect(self.unhide_pictures)
        self.lbl_pic = QLabel("No picture chosen.")
        self.lbl_pic.setWordWrap(True)
        self.lbl_pic.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl_pic)
        self.cb_light = QCheckBox("Light parts stand out")
        lay.addWidget(self.cb_light)
        self.cb_light.setVisible(False)                   # set in the 3D program's Picture section
        self._pic_lay = lay
        self.picture = st.get('picture', '')
        b_choose.clicked.connect(self.choose_folder)
        b_open.clicked.connect(lambda: self._open_in_windows(self.ed_folder.text()))
        self.lst_pics.itemClicked.connect(self.picture_clicked)
        self.set_folder(st.get('folder', ''))

    def _sizes_page(self):
        self._sizes_holder = QWidget()                    # not shown: the sizes are tuned in the 3D program
        fl = _form(self._sizes_holder)
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
        # B and C on the Picture page: how big a piece of wall the picture shows
        pf = QFormLayout()
        lab_b = QLabel("Picture covers - across")
        lab_c = QLabel("Picture covers - up")
        for lab_, key in ((lab_b, 'tile_w'), (lab_c, 'tile_h')):
            lab_.setToolTip(self.sp[key].toolTip())
            pf.addRow(lab_, self.sp[key])
            self.sp[key].valueChanged.connect(self._touched)
        note = QLabel("Everything else (depth, detail, crisp edges...) is set in the 3D program's Realistic "
                      "Wall panel, where you can see it.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #555;")
        pf.addRow(note)
        self._pic_lay.addLayout(pf)
        for s in self.sp.values():
            s.valueChanged.connect(self.changed)

    def _blender_page(self, st):
        lay = QVBoxLayout(self._page("Program"))
        info = QLabel("Your 3D program carves the walls and opens with them, ready to look at and print "
                      "(Send to my printer). Bringing them back into the model is only for when you really need "
                      "to - they can slow IngeTrazo right down.")
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
                                "is used instead - by itself on walls up to about a gable end's size (a couple "
                                "of minutes); tick this to allow it on bigger walls too (it can take a long time).")
        self.cb_slow.setChecked(bool(st.get('allow_slow')))
        self.cb_slow.toggled.connect(lambda on: save_settings(allow_slow=bool(on)))
        lay.addWidget(self.cb_slow)
        self.cb_slow.setVisible(False)                    # in the 3D program's panel
        self.cb_colour = QCheckBox("Show the colours in the 3D program")
        self.cb_colour.setToolTip("Puts the colour photo (found beside the height picture) on the carved walls, "
                                  "lined up with the bricks - just for looking, the shape doesn't change.")
        self.cb_colour.setChecked(bool(st.get('colour', True)))
        self.cb_colour.toggled.connect(lambda on: save_settings(colour=bool(on)))
        lay.addWidget(self.cb_colour)
        self.cb_colour.setVisible(False)                  # in the 3D program's Picture section
        row3 = QHBoxLayout()
        lab_mf = QLabel("L   Most faces brought back (thousands)")
        self.sp_faces = QSpinBox()
        self.sp_faces.setRange(5, 5000)
        self.sp_faces.setValue(int(st.get('max_faces', 150)))
        tip = ("What comes back to IngeTrazo is thinned to about this many triangles, keeping the bricks and "
               "joints - IngeTrazo slows right down (or seizes up) with too many. The wall in the 3D program keeps "
               "all its detail. 150 is safe; try 300 if your PC copes.")
        self.sp_faces.setToolTip(tip)
        lab_mf.setToolTip(tip)
        self.sp_faces.valueChanged.connect(lambda v: save_settings(max_faces=int(v)))
        row3.addWidget(lab_mf)
        row3.addWidget(self.sp_faces)
        lab_mf.setVisible(False)                          # L and M are in the 3D program's panel
        self.sp_faces.setVisible(False)
        row3.addStretch(1)
        lay.addLayout(row3)
        row4 = QHBoxLayout()
        lab_sm = QLabel("M   Smooth the stone (times)")
        self.sp_smooth = QSpinBox()
        self.sp_smooth.setRange(0, 10)
        self.sp_smooth.setValue(int(st.get('smooth', 2)))
        tip = ("Smooths the cut-in parts (joints, broken bits) of what comes back into IngeTrazo, so it's less "
               "crinkly there. Never used for printing - 'Send to my printer' always gets the full detail. 0 = off.")
        self.sp_smooth.setToolTip(tip)
        lab_sm.setToolTip(tip)
        self.sp_smooth.valueChanged.connect(lambda v: save_settings(smooth=int(v)))
        row4.addWidget(lab_sm)
        row4.addWidget(self.sp_smooth)
        lab_sm.setVisible(False)
        self.sp_smooth.setVisible(False)
        row4.addStretch(1)
        lay.addLayout(row4)
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
    def refresh_buildings(self, use_selected=False):
        """Fills the Building list with the models in the scene, picking the selected one (or the only
        one) if there is one."""
        scene = getattr(self.viewport, 'scene', None)
        if scene is None:
            return
        tops = [t for t in _items(getattr(scene, 'groups', None)) if _kids(t) or getattr(t, 'mesh', None) is not None]
        was = self.cb_building.currentData()
        chosen = None
        sel = [e for e in _items(getattr(scene, 'selection', None)) if getattr(e, 'mesh', None) is not None or _kids(e)]
        mine = []
        for e in sel:
            b = building_of(scene, e)
            if b is not None and all(b is not x for x in mine):
                mine.append(b)
        if mine:
            chosen = max(mine, key=_model_size)
        if chosen is None and not use_selected and was is not None and was < len(self._tops):
            old = self._tops[was]
            chosen = next((t for t in tops if t is old), None)
        if chosen is None and tops:
            chosen = max(tops, key=_model_size)     # a figure or a tree beside it isn't the building
        self._busy = True
        self._tops = tops
        self.cb_building.clear()
        self.cb_building.addItem("-- pick a building --", None)
        used = {}
        for i, t in enumerate(tops):
            nm = str(getattr(t, 'name', '') or "Model %d" % (i + 1))
            used[nm] = used.get(nm, 0) + 1
            self.cb_building.addItem(nm if used[nm] == 1 else "%s (%d)" % (nm, used[nm]), i)
        if chosen is not None:
            self.cb_building.setCurrentIndex(1 + next(i for i, t in enumerate(tops) if t is chosen))
        self._busy = False

    def find(self):
        scene = getattr(self.viewport, 'scene', None)
        if scene is None:
            return
        if self.cb_building.count() == 0 or self.cb_building.currentData() is None:
            self.refresh_buildings()
        idx = self.cb_building.currentData()
        top = self._tops[idx] if idx is not None and idx < len(self._tops) else None
        if top is None:
            self.found = []
            self.lst_walls.clear()
            self.lbl_walls.setText("There's more than one model here: pick the building to work on from the "
                                   "Building list (or select it in the model and click 'Use the selected one').")
            self._sync_picker()
            return
        save_settings(inside_walls=self.cb_inside_walls.isChecked(), inside_faces=self.cb_inside_faces.isChecked())
        try:
            self.found = find_walls(scene, self.cb_inside_walls.isChecked(), self.cb_inside_faces.isChecked(), top)
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
            self.lbl_walls.setText("No walls found in that building. Pick another building, or make sure its "
                                   "walls are plain (not already bricked).")
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
        hidden = set(load_settings().get('hidden_pics') or [])
        n_all = len(names)
        names = [fn for fn in names if os.path.normcase(os.path.join(folder, fn)) not in hidden]
        n_hid = n_all - len(names)
        self.b_unhide.setText("Show hidden ones (%d)" % n_hid if n_hid else "Show hidden ones")
        self.b_unhide.setEnabled(bool(n_hid))
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

    def _clicked_pic(self):
        it = self.lst_pics.currentItem()
        p = it.data(Qt.UserRole) if it is not None else None
        if not p:
            QMessageBox.information(self, PLUGIN_NAME, "Click a picture first.")
        return p

    def _pics_menu(self, pos):
        from PySide6.QtWidgets import QMenu
        it = self.lst_pics.itemAt(pos)
        p = it.data(Qt.UserRole) if it is not None else None
        if not p:
            return
        self.lst_pics.setCurrentItem(it)
        m = QMenu(self)
        a_hide = m.addAction("Take off the list (the file stays)")
        a_del = m.addAction("Delete the file...")
        got = m.exec(self.lst_pics.viewport().mapToGlobal(pos))
        if got is a_hide:
            self.hide_picture(p)
        elif got is a_del:
            self.delete_picture(p)

    def _forget_picture(self, p):
        if self.picture and os.path.normcase(self.picture) == os.path.normcase(p):
            self.picture = ''
            save_settings(picture='')

    def hide_picture(self, p):
        """Takes a picture off the list here; the file stays in the folder."""
        if not p:
            return
        hidden = list(load_settings().get('hidden_pics') or [])
        if os.path.normcase(p) not in hidden:
            hidden.append(os.path.normcase(p))
        save_settings(hidden_pics=hidden)
        self._forget_picture(p)
        self.set_folder(self.ed_folder.text())
        self.say("%s is off the list (the file is still in the folder)." % os.path.basename(p))

    def unhide_pictures(self):
        folder = os.path.normcase(self.ed_folder.text() or "")
        hidden = [h for h in (load_settings().get('hidden_pics') or []) if os.path.dirname(h) != folder]
        save_settings(hidden_pics=hidden)
        self.set_folder(self.ed_folder.text())

    def delete_picture(self, p):
        """Deletes a picture's file - to the Recycle Bin if it can - and its partner (the colour photo of a
        height picture, or the other way round) if you tick the box."""
        from PySide6.QtCore import QFile
        if not p or not os.path.isfile(p):
            return
        mate = colour_picture_for(p) or height_picture_for(p)
        box = QMessageBox(QMessageBox.Question, PLUGIN_NAME,
                          "Delete this picture?\n\n%s\n\nIt goes to the Recycle Bin, so you can get it back from "
                          "there." % p, QMessageBox.Yes | QMessageBox.No, self)
        box.setDefaultButton(QMessageBox.No)
        cb = None
        if mate and os.path.isfile(mate):
            cb = QCheckBox("Delete its partner too: %s" % os.path.basename(mate))
            cb.setChecked(True)
            box.setCheckBox(cb)
        if box.exec() != QMessageBox.Yes:
            return
        files = [p] + ([mate] if cb is not None and cb.isChecked() else [])
        done, bad = [], []
        for f in files:
            ok = False
            try:
                ok = bool(QFile.moveToTrash(f))
            except Exception:
                ok = False
            if not ok:
                if QMessageBox.question(self, PLUGIN_NAME, "%s couldn't go to the Recycle Bin.\n\nDelete it for "
                                        "good (it can't be got back)?" % os.path.basename(f)) == QMessageBox.Yes:
                    try:
                        os.remove(f)
                        ok = True
                    except Exception as e:
                        bad.append("%s (%s)" % (os.path.basename(f), e))
            if ok:
                done.append(os.path.basename(f))
                self._forget_picture(f)
        self.set_folder(self.ed_folder.text())
        if done:
            self.say("Deleted %s." % ", ".join(done) + (" Couldn't delete %s." % "; ".join(bad) if bad else ""),
                     bool(bad))
        elif bad:
            self.say("Couldn't delete %s." % "; ".join(bad), True)

    def get_online(self):
        folder = self.ed_folder.text() or DEFAULT_PICTURES
        dlg = OnlinePictures(folder, self)
        if dlg.exec() != QDialog.Accepted or not dlg.result:
            return
        disp, diff, dims = dlg.result
        if os.path.normcase(folder) != os.path.normcase(self.ed_folder.text() or ""):
            save_settings(folder=folder)
        self.picture = disp
        save_settings(picture=disp)
        self._touch = time.time()
        self.set_folder(folder)
        self._show_picture()
        if len(dims) >= 2:
            self.sp['tile_w'].setValue(float(dims[0]))
            self.sp['tile_h'].setValue(float(dims[1]))
        self.say("Got %s - it's picked%s." % (os.path.basename(disp),
                 ", and B and C are set to %.0f x %.0f mm" % (dims[0], dims[1]) if len(dims) >= 2 else ""))
        self.views.setCurrentIndex(1)

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
        self._touch = time.time()
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
            self.tabs.setCurrentIndex(2)
            QMessageBox.information(self, PLUGIN_NAME, "The 3D program wasn't found. Click Find it, or "
                                                       "Choose... and pick it (Program page).")
            return
        self._take_latest()
        vals = self.get_values()
        save_settings(**vals)
        vals['patch'] = False                             # the test patch is chosen in the 3D program
        vals['allow_slow'] = self.cb_slow.isChecked()
        vals['colour'] = self.cb_colour.isChecked()
        vals['max_faces'] = self.sp_faces.value()
        vals['smooth'] = self.sp_smooth.value()
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
        done_file = os.path.join(os.path.dirname(self._job_obj), "realistic wall settings.json")
        try:
            if self._job_started and os.path.isfile(done_file) and \
                    os.path.getmtime(done_file) >= self._job_started - 1:
                self._job_started = 0.0
                self._seen = os.path.getmtime(self._job_obj) if os.path.isfile(self._job_obj) else 0.0
                self.say("The walls are carved. To print them, click Send to my printer in the 3D program's "
                         "Realistic Wall panel (N key).")
                return
            if not os.path.isfile(self._job_obj):
                return
            t = os.path.getmtime(self._job_obj)
        except Exception:
            return
        if not self._job_started and getattr(self, '_seen', None) is not None and t > self._seen + 0.5:
            self._seen = t
            self.say("The walls were sent from the 3D program. 'Bring the walls back' puts them in the model "
                     "(they may slow IngeTrazo down).")

    def bring_back_clicked(self):
        path = self._job_obj
        if path and not os.path.isfile(path) and os.path.isdir(os.path.dirname(path)):
            self.say("Nothing sent yet: in the 3D program's Realistic Wall panel (N key), click 'Send to "
                     "IngeTrazo' first, then click this again.", True)
            return
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
        try:
            nf = 0
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if line.startswith("f "):
                        nf += 1
        except Exception:
            nf = 0
        big = nf > 400000
        box = QMessageBox(QMessageBox.Warning, PLUGIN_NAME,
                          ("Bring the carved walls into the model?\n\n"
                           "They have about %d thousand faces. Carved walls are very detailed and can slow IngeTrazo "
                           "right down%s.\n\nOnly do this if you really need them in the model - to print them, "
                           "click 'Send to my printer' in the 3D program instead.")
                          % (max(1, nf // 1000), " - this many may make it seize up" if big else ""),
                          QMessageBox.Yes | QMessageBox.No, self)
        box.button(QMessageBox.Yes).setText("Bring them back anyway")
        box.button(QMessageBox.No).setText("Don't")
        box.setDefaultButton(QMessageBox.No)
        if box.exec() != QMessageBox.Yes:
            self.say("Not brought back. Print them from the 3D program with 'Send to my printer'.")
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

    def _touched(self, *_):
        if not self._busy:
            self._touch = time.time()

    def _take_latest(self):
        """Before carving: takes in the settings last used in the 3D program (changed in its panel), but
        not the picture or its size if they've been changed here since."""
        if not self._job_obj:
            return
        f = os.path.join(os.path.dirname(self._job_obj), "realistic wall settings.json")
        try:
            t = os.path.getmtime(f)
        except Exception:
            return
        keep_here = t < getattr(self, '_touch', 0.0)
        pic, tw, th = self.picture, self.sp['tile_w'].value(), self.sp['tile_h'].value()
        self._take_settings(self._job_obj)
        if keep_here:
            self.picture = pic
            self._busy = True
            self.sp['tile_w'].setValue(tw)
            self.sp['tile_h'].setValue(th)
            self._busy = False
            save_settings(picture=pic, tile_w=tw, tile_h=th)
            self._show_picture()

    def reset_defaults(self):
        """Every carving setting back to how it starts; the picture is kept. The settings the 3D program
        left from last time are set back too, so they aren't taken in again on the next carve."""
        if QMessageBox.question(self, PLUGIN_NAME, "Put all the carving settings back to how they start?\n"
                                "(The picture you've picked is kept.)") != QMessageBox.Yes:
            return
        extra = {'colour': True, 'allow_slow': False, 'max_faces': 150, 'smooth': 2, 'patch': False}
        self.set_values(dict(DEFAULTS, inside_walls=False, inside_faces=False))
        for key, box in (('colour', getattr(self, 'cb_colour', None)), ('allow_slow', getattr(self, 'cb_slow', None)),
                         ('patch', getattr(self, 'cb_patch', None))):
            if box is not None:
                box.setChecked(extra[key])
        if hasattr(self, 'sp_smooth'):
            self.sp_smooth.setValue(2)
        if hasattr(self, 'sp_faces'):
            self.sp_faces.setValue(150)
        save_settings(inside_walls=False, inside_faces=False, **dict(DEFAULTS, **extra))
        if self._job_obj:
            f = os.path.join(os.path.dirname(self._job_obj), "realistic wall settings.json")
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    d = json.load(fh)
            except Exception:
                d = None
            if isinstance(d, dict):
                d.update(DEFAULTS)
                d.update(extra)
                try:
                    with open(f, "w", encoding="utf-8") as fh:
                        json.dump(d, fh, indent=1)
                except Exception:
                    pass
        self._touch = time.time()
        self.say("Settings back to defaults (the picture is kept).")

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
        if 'smooth' in d and hasattr(self, 'sp_smooth'):
            self.sp_smooth.setValue(int(d['smooth']))
            keep['smooth'] = int(d['smooth'])
        if 'max_faces' in d and hasattr(self, 'sp_faces'):
            self.sp_faces.setValue(int(d['max_faces']))
            keep['max_faces'] = int(d['max_faces'])
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
