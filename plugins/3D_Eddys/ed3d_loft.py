# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Loft for IngeTrazo
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
3D Loft - build a solid between two or more profile faces, for IngeTrazo
Select the profiles (for example a square with a circle above it), run Loft,
and it makes a closed, printable solid in a new group.
"""

import math
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QSpinBox, QCheckBox, QComboBox,
    QDialogButtonBox, QMessageBox, QLabel, QLineEdit
)

PLUGIN_NAME = "3D Loft"

PATHS = [("Smooth S-curve (sides meet each profile square-on)", "scurve"),
         ("Straight between profiles", "straight"),
         ("Smooth curve through all profiles (3 or more)", "smooth")]
AUTO_SECTIONS = {'straight': 1, 'scurve': 32, 'smooth': 24}
AUTO_MIN_POINTS = 64     # Auto points: at least this many around each profile (curved lofts)
SPLITS = [("Auto (split twisted sides into triangles)", "auto"),
          ("Always triangles", "always"),
          ("Never (quads only)", "never")]

DEFAULTS = {'points': 0, 'sections': 0, 'path': 'scurve', 'align': True, 'twist': 0,
            'cap_start': True, 'cap_end': True, 'split': 'auto', 'name': 'Loft',
            'soften': True, 'soft_angle': 30}


# ---------------------------------------------------------------------------
# Small vector helpers (plain tuples, so the geometry has no Qt dependency)
# ---------------------------------------------------------------------------
def v_add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def v_sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def v_mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def v_dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def v_len(a): return math.sqrt(v_dot(a, a))


def v_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def v_norm(a):
    L = v_len(a)
    return (a[0] / L, a[1] / L, a[2] / L) if L > 1e-15 else (0.0, 0.0, 0.0)


def v_avg(pts):
    n = float(len(pts))
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n, sum(p[2] for p in pts) / n)


# ---------------------------------------------------------------------------
# Reading the scene
# ---------------------------------------------------------------------------
def _items(x):
    if x is None:
        return []
    if isinstance(x, dict):
        return list(x.values())
    try:
        return list(x)
    except Exception:
        return []


def _pos(v):
    """Vertex position as an (x, y, z) tuple, or None if it can't be read."""
    for get in (lambda: (v.x(), v.y(), v.z()),
                lambda: (v.x, v.y, v.z),
                lambda: (v[0], v[1], v[2]),
                lambda: (v.pos.x(), v.pos.y(), v.pos.z()),
                lambda: (v.position.x(), v.position.y(), v.position.z())):
        try:
            x, y, z = get()
            return (float(x), float(y), float(z))
        except Exception:
            pass
    return None


def _is_face(e):
    return hasattr(e, 'loop') or 'face' in type(e).__name__.lower()


def face_profile(face):
    """Outer loop of a face as a clean list of points (no repeats, no closing point)."""
    pts = [p for p in (_pos(v) for v in _items(getattr(face, 'vertices', None))) if p is not None]
    if len(pts) < 3:
        return pts
    size = max(v_len(v_sub(p, pts[0])) for p in pts) or 1.0
    tol = size * 1e-9
    out = []
    for p in pts:
        if not out or v_len(v_sub(p, out[-1])) > tol:
            out.append(p)
    if len(out) > 1 and v_len(v_sub(out[0], out[-1])) <= tol:
        out.pop()
    return out


def _val(obj, name):
    """Reads an attribute that may be a plain value or a method."""
    x = getattr(obj, name, None)
    if callable(x):
        try:
            x = x()
        except Exception:
            return None
    return x


def _face_normal(f):
    pts = [p for p in (_pos(v) for v in _items(_val(f, 'vertices'))) if p is not None]
    return newell_normal(pts) if len(pts) >= 3 else None


def soften_edges(mesh, faces_made, max_angle):
    """Softens (hides and smooths) every edge whose two faces meet at less than
    max_angle degrees, like SketchUp's Soften Edges. Sharp edges stay visible."""
    edges = _items(_val(mesh, 'edges'))
    if not edges:
        # no edge list on the mesh: look the edges up from the faces instead
        seen = set()
        for f in faces_made:
            vs = _items(_val(f, 'vertices'))
            for i in range(len(vs)):
                try:
                    e = mesh.find_edge(vs[i], vs[(i + 1) % len(vs)])
                except Exception:
                    e = None
                if e is not None and id(e) not in seen:
                    seen.add(id(e))
                    edges.append(e)
    cos_lim = math.cos(math.radians(max_angle))
    soft = hard = 0
    for e in edges:
        fs = _items(_val(e, 'faces'))
        if len(fs) != 2:
            continue
        n1, n2 = _face_normal(fs[0]), _face_normal(fs[1])
        if n1 is None or n2 is None:
            continue
        if v_dot(n1, n2) >= cos_lim:
            try:
                e.soft = True
                soft += 1
            except Exception:
                pass
        else:
            hard += 1
    return soft, hard, len(edges)


class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))


# ---------------------------------------------------------------------------
# Loft geometry
# ---------------------------------------------------------------------------
def newell_normal(pts):
    nx = ny = nz = 0.0
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    return v_norm((nx, ny, nz))


def resample(pts, n):
    """Returns exactly n points around the loop. Every original corner is kept and
    the extra points are shared out along the edges in proportion to their length."""
    k = len(pts)
    if n <= k:
        return list(pts)
    lens = [v_len(v_sub(pts[(i + 1) % k], pts[i])) for i in range(k)]
    total = sum(lens)
    ideal = [L / total * n for L in lens]
    counts = [max(1, int(math.floor(x))) for x in ideal]
    while sum(counts) < n:
        i = max(range(k), key=lambda j: ideal[j] - counts[j])
        counts[i] += 1
    while sum(counts) > n:
        i = min((j for j in range(k) if counts[j] > 1), key=lambda j: ideal[j] - counts[j])
        counts[i] -= 1
    out = []
    for i in range(k):
        a, b = pts[i], pts[(i + 1) % k]
        for j in range(counts[i]):
            out.append(v_add(a, v_mul(v_sub(b, a), j / float(counts[i]))))
    return out


def best_shift(a, b):
    """Start index for loop b that lines it up best with loop a (least twist).
    Both loops are centred and scaled to the same size first, so a square and
    a circle of different sizes still line up by shape."""
    n = len(a)
    ca, cb = v_avg(a), v_avg(b)
    ra = math.sqrt(sum(v_dot(v_sub(p, ca), v_sub(p, ca)) for p in a) / n) or 1.0
    rb = math.sqrt(sum(v_dot(v_sub(p, cb), v_sub(p, cb)) for p in b) / n) or 1.0
    an = [v_mul(v_sub(p, ca), 1.0 / ra) for p in a]
    bn = [v_mul(v_sub(p, cb), 1.0 / rb) for p in b]
    best, best_s = None, 0
    for s in range(n):
        d = 0.0
        for i in range(n):
            q = bn[(i + s) % n]
            p = an[i]
            d += (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2
            if best is not None and d >= best:
                break
        if best is None or d < best:
            best, best_s = d, s
    return best_s


def order_profiles(profiles):
    """Sorts 3+ profiles along the line between the two that are furthest apart."""
    if len(profiles) < 3:
        return profiles
    cs = [v_avg(p) for p in profiles]
    i0, i1, far = 0, 1, -1.0
    for i in range(len(cs)):
        for j in range(i + 1, len(cs)):
            d = v_len(v_sub(cs[i], cs[j]))
            if d > far:
                i0, i1, far = i, j, d
    axis = v_sub(cs[i1], cs[i0])
    idx = sorted(range(len(profiles)), key=lambda k: v_dot(v_sub(cs[k], cs[i0]), axis))
    return [profiles[k] for k in idx]


def _catmull(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return tuple(0.5 * ((2 * p1[i]) + (-p0[i] + p2[i]) * t
                        + (2 * p0[i] - 5 * p1[i] + 4 * p2[i] - p3[i]) * t2
                        + (-p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]) * t3) for i in range(3))


def _ear_clip(loop, pts, normal):
    """Triangulates a flat polygon (indices into pts). Used only if the app
    won't accept the cap as one polygon."""
    ax = max(range(3), key=lambda i: abs(normal[i]))
    u, w = [(1, 2), (2, 0), (0, 1)][ax]
    sgn = 1.0 if normal[ax] >= 0 else -1.0

    def p2(k):
        return (pts[k][u], pts[k][w])

    def cross(a, b, c):
        return sgn * ((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))

    def inside(p, a, b, c):
        return cross(a, b, p) >= 0 and cross(b, c, p) >= 0 and cross(c, a, p) >= 0

    rem = list(loop)
    tris = []
    guard = 0
    while len(rem) > 3 and guard < 100000:
        guard += 1
        n = len(rem)
        found = None
        for i in range(n):
            ia, ib, ic = rem[i - 1], rem[i], rem[(i + 1) % n]
            a, b, c = p2(ia), p2(ib), p2(ic)
            if cross(a, b, c) <= 1e-14:
                continue
            if any(inside(p2(k), a, b, c) for k in rem if k not in (ia, ib, ic)):
                continue
            found = i
            break
        if found is None:
            # only flat corners left: clip the flattest one so we always finish
            found = min(range(n), key=lambda i: abs(cross(p2(rem[i - 1]), p2(rem[i]), p2(rem[(i + 1) % n]))))
        n = len(rem)
        tris.append([rem[found - 1], rem[found], rem[(found + 1) % n]])
        del rem[found]
    tris.append(list(rem))
    return tris


def build_loft(profiles, opt):
    """profiles: list of point loops. Returns (points, faces, caps, info) where faces
    are lists of point indices, caps are (index loop, outward normal) pairs."""
    if len(profiles) < 2:
        raise ValueError("Select at least two profile faces.")
    for p in profiles:
        if len(p) < 3:
            raise ValueError("One of the selected faces has fewer than 3 corners.")

    profiles = order_profiles(profiles)
    m = len(profiles)
    cents = [v_avg(p) for p in profiles]
    span = max(v_len(v_sub(cents[i + 1], cents[i])) for i in range(m - 1))
    if span < 1e-9:
        raise ValueError("The profiles are in the same place. Move one of them away "
                         "(for example straight up) and try again.")

    # Wind every profile the same way round, facing along the loft.
    loops = []
    for k, p in enumerate(profiles):
        d = v_norm(v_sub(cents[min(k + 1, m - 1)], cents[max(k - 1, 0)]))
        nrm = newell_normal(p)
        c = v_dot(nrm, d)
        if abs(c) < 0.1:
            raise ValueError("Profile %d lies side-on to the loft direction. Profiles must "
                             "face each other, e.g. one above the other." % (k + 1))
        loops.append(list(p) if c > 0 else list(reversed(p)))

    n = max(opt.get('points') or 0, max(len(p) for p in loops))
    if not opt.get('points') and opt.get('path', 'scurve') != 'straight':
        n = max(n, AUTO_MIN_POINTS)
    rings = [resample(p, n) for p in loops]

    if opt.get('align', True):
        for k in range(1, m):
            s = best_shift(rings[k - 1], rings[k])
            rings[k] = rings[k][s:] + rings[k][:s]

    tw = int(opt.get('twist') or 0)
    if tw:
        for k in range(1, m):
            s = int(round(tw * k / float(m - 1))) % n
            rings[k] = rings[k][s:] + rings[k][:s]

    # Sections along the loft
    path = opt.get('path', 'scurve')
    if path == 'smooth' and m < 3:
        path = 'scurve'          # a curve "through" two profiles is the S-curve
    S = int(opt.get('sections') or 0) or AUTO_SECTIONS.get(path, 1)
    smooth = path == 'smooth'
    scurve = path == 'scurve'
    # direction each profile faces (the loops are already wound to face along the loft)
    normals = [newell_normal(r) for r in rings]
    all_rings = []
    for k in range(m - 1):
        L = v_len(v_sub(v_avg(rings[k + 1]), v_avg(rings[k])))
        T0, T1 = v_mul(normals[k], L), v_mul(normals[k + 1], L)
        for j in range(S):
            t = j / float(S)
            if scurve:
                # Hermite curve per point: leaves each profile straight out along its
                # facing direction, so the sides blend in without a crease
                h00 = 2 * t ** 3 - 3 * t ** 2 + 1
                h10 = t ** 3 - 2 * t ** 2 + t
                h01 = -2 * t ** 3 + 3 * t ** 2
                h11 = t ** 3 - t ** 2
                all_rings.append([v_add(v_add(v_mul(a, h00), v_mul(T0, h10)),
                                        v_add(v_mul(b, h01), v_mul(T1, h11)))
                                  for a, b in zip(rings[k], rings[k + 1])])
            elif smooth:
                p0 = rings[k - 1] if k > 0 else [v_sub(v_mul(a, 2), b) for a, b in zip(rings[0], rings[1])]
                p3 = rings[k + 2] if k + 2 < m else [v_sub(v_mul(a, 2), b) for a, b in zip(rings[-1], rings[-2])]
                all_rings.append([_catmull(p0[i], rings[k][i], rings[k + 1][i], p3[i], t) for i in range(n)])
            else:
                all_rings.append([v_add(a, v_mul(v_sub(b, a), t)) for a, b in zip(rings[k], rings[k + 1])])
    all_rings.append(list(rings[-1]))

    R = len(all_rings)
    pts = [p for ring in all_rings for p in ring]

    def ix(r, i):
        return r * n + (i % n)

    size = max(v_len(v_sub(p, pts[0])) for p in pts) or 1.0
    split = opt.get('split', 'auto')
    faces = []
    for r in range(R - 1):
        for i in range(n):
            a0, a1, b1, b0 = ix(r, i), ix(r, i + 1), ix(r + 1, i + 1), ix(r + 1, i)
            quad = [a0, a1, b1, b0]
            do_split = split == 'always'
            if split == 'auto':
                # only split quads that are clearly bent: out of plane by more than
                # 2% of the quad's own size (slightly bent quads shade more evenly whole)
                pn = v_cross(v_sub(pts[a1], pts[a0]), v_sub(pts[b1], pts[a0]))
                L = v_len(pn)
                qsize = min(v_len(v_sub(pts[a1], pts[a0])), v_len(v_sub(pts[b0], pts[a0])),
                            v_len(v_sub(pts[b1], pts[b0])), v_len(v_sub(pts[b1], pts[a1])))
                if L < 1e-15 or abs(v_dot(v_sub(pts[b0], pts[a0]), pn)) / L > max(qsize * 0.02, size * 1e-6):
                    do_split = True
            if do_split:
                # always the same diagonal, so the shading doesn't zig-zag
                faces += [[a0, a1, b1], [a0, b1, b0]]
            else:
                faces.append(quad)

    caps = []
    if opt.get('cap_start', True):
        caps.append([ix(0, i) for i in range(n - 1, -1, -1)])
    if opt.get('cap_end', True):
        caps.append([ix(R - 1, i) for i in range(n)])

    # Make sure the faces point outwards (positive volume); flip everything if not.
    if opt.get('cap_start', True) and opt.get('cap_end', True):
        vol = 0.0
        for f in faces + caps:
            for j in range(1, len(f) - 1):
                vol += v_dot(pts[f[0]], v_cross(pts[f[j]], pts[f[j + 1]]))
        if vol < 0:
            faces = [list(reversed(f)) for f in faces]
            caps = [list(reversed(c)) for c in caps]

    caps = [(c, newell_normal([pts[k] for k in c])) for c in caps]
    info = {'points': n, 'rings': R, 'profiles': m, 'sections': S}
    return pts, faces, caps, info


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

EDDY_TIPS = {'Path': 'How the sides run from profile to profile: a smooth S-curve, straight, or one smooth '
         'curve through all of them.',
 'Line profiles up automatically (least twist)': 'Turns the profiles so the sides twist as '
                                                 'little as possible.',
 'Cap the first profile': 'Closes the first end with a face.',
 'Cap the last profile': 'Closes the last end with a face.',
 'Side faces': 'Whether twisted side faces are split into triangles (so they stay flat).',
 'Group name': 'The name of the group the loft goes in.',
 'Smooth finish (soften edges, like SketchUp)': 'Hides the edges between the side faces, so '
                                                'the curve looks smooth.'}
EDDY_TIPS_END = None


class LoftDialog(QDialog):
    def __init__(self, cur, counts, parent=None):
        super().__init__(parent)
        self.setWindowTitle(PLUGIN_NAME)
        self.counts = counts
        lay = QVBoxLayout(self)
        form = QFormLayout()

        form.addRow(QLabel("Profiles: %d  (%s corners)" %
                           (len(counts), ", ".join(str(c) for c in counts))))

        self.cb_path = QComboBox()
        for label, key in PATHS:
            self.cb_path.addItem(label, key)
            if key == cur['path']:
                self.cb_path.setCurrentIndex(self.cb_path.count() - 1)

        path = self.path()
        self.sp_points = QSpinBox()
        self.sp_points.setRange(max(3, max(counts)), 4096)
        self.sp_points.setValue(cur['points'] or self.default_points(path))
        self.sp_points.setToolTip("Points around each profile (it can't be fewer than the profile with "
                                  "the most corners). Suggested: %d for curved lofts, %d for Straight."
                                  % (self.default_points('scurve'), self.default_points('straight')))

        self.sp_sect = QSpinBox()
        self.sp_sect.setRange(1, 200)
        self.sp_sect.setValue(cur['sections'] or AUTO_SECTIONS.get(path, 1))
        self.sp_sect.setToolTip("Bands between each pair of profiles. More bands = smoother curve. "
                                "Suggested: 1 for Straight, 32 for S-curve, 24 for Smooth.")

        self.cb_align = QCheckBox("Line profiles up automatically (least twist)")
        self.cb_align.setChecked(cur['align'])

        self.sp_twist = QSpinBox()
        self.sp_twist.setRange(-2048, 2048)
        self.sp_twist.setValue(cur['twist'])
        self.sp_twist.setToolTip("Turns the last profile by this many points (positive or negative). "
                                 "Use it to fix a twist, or add one on purpose.")

        self.cb_start = QCheckBox("Cap the first profile")
        self.cb_start.setChecked(cur['cap_start'])
        self.cb_end = QCheckBox("Cap the last profile")
        self.cb_end.setChecked(cur['cap_end'])

        self.cb_split = QComboBox()
        for label, key in SPLITS:
            self.cb_split.addItem(label, key)
            if key == cur['split']:
                self.cb_split.setCurrentIndex(self.cb_split.count() - 1)

        self.le_name = QLineEdit(cur['name'])

        self.cb_soft = QCheckBox("Smooth finish (soften edges, like SketchUp)")
        self.cb_soft.setChecked(cur['soften'])
        self.sp_soft = QSpinBox()
        self.sp_soft.setRange(0, 180)
        self.sp_soft.setSuffix(" deg")
        self.sp_soft.setValue(cur['soft_angle'])
        self.sp_soft.setToolTip("Edges where faces meet at less than this angle are softened. "
                                "Sharper edges (like the rims of the caps) stay visible.")
        self.cb_soft.toggled.connect(self.sp_soft.setEnabled)
        self.sp_soft.setEnabled(self.cb_soft.isChecked())

        self.lbl_info = QLabel()
        self.lbl_info.setWordWrap(True)

        form.addRow("Points per profile:", self.sp_points)
        form.addRow("Sections between profiles:", self.sp_sect)
        form.addRow("Path:", self.cb_path)
        form.addRow(self.cb_align)
        form.addRow("Extra twist (points):", self.sp_twist)
        form.addRow(self.cb_start)
        form.addRow(self.cb_end)
        form.addRow("Side faces:", self.cb_split)
        form.addRow(self.cb_soft)
        form.addRow("   Soften edges up to:", self.sp_soft)
        form.addRow("Group name:", self.le_name)
        form.addRow(self.lbl_info)
        lay.addLayout(form)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

        for s in (self.sp_points, self.sp_sect):
            s.valueChanged.connect(self.update_info)
        self.cb_path.currentIndexChanged.connect(self.path_changed)
        for c in (self.cb_start, self.cb_end):
            c.toggled.connect(self.update_info)
        self.update_info()

    def path(self):
        p = self.cb_path.currentData()
        return 'scurve' if (p == 'smooth' and len(self.counts) < 3) else p

    def default_points(self, path):
        n = max(self.counts)
        return n if path == 'straight' else max(n, AUTO_MIN_POINTS)

    def path_changed(self, *_):
        # a new path gets that path's suggested numbers
        path = self.path()
        self.sp_points.setValue(self.default_points(path))
        self.sp_sect.setValue(AUTO_SECTIONS.get(path, 1))
        self.update_info()

    def update_info(self, *_):
        n = self.sp_points.value()
        sect = self.sp_sect.value()
        bands = sect * (len(self.counts) - 1)
        txt = "About %d side faces, %d points per ring." % (n * bands, n)
        if not (self.cb_start.isChecked() and self.cb_end.isChecked()):
            txt += "<br>An open end means the result is not a closed solid (not printable)."
        self.lbl_info.setText(txt)

    def get_values(self):
        return {
            'points': self.sp_points.value(),
            'sections': self.sp_sect.value(),
            'path': self.cb_path.currentData(),
            'align': self.cb_align.isChecked(),
            'twist': self.sp_twist.value(),
            'cap_start': self.cb_start.isChecked(),
            'cap_end': self.cb_end.isChecked(),
            'split': self.cb_split.currentData(),
            'name': self.le_name.text().strip() or "Loft",
            'soften': self.cb_soft.isChecked(),
            'soft_angle': self.sp_soft.value(),
        }


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
class LoftTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+L"
    description = "Make a solid between two or more profile faces (e.g. a square into a circle)."

    _saved = None

    def on_activate(self, viewport):
        scene = getattr(viewport, 'scene', None)
        faces = [e for e in (getattr(scene, 'selection', None) or []) if _is_face(e)]
        if len(faces) < 2:
            QMessageBox.warning(viewport, PLUGIN_NAME,
                                "Select two or more profile faces first, for example a square "
                                "and a circle above it.")
            return

        profiles = [face_profile(f) for f in faces]
        if any(getattr(f, 'holes', None) for f in faces):
            print("%s: holes in the profiles are ignored; only the outer edge is lofted." % PLUGIN_NAME)

        cur = dict(DEFAULTS)
        if LoftTool._saved:
            cur.update(LoftTool._saved)

        dialog = LoftDialog(cur, [len(p) for p in profiles], viewport)
        eddy_window(dialog, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        if dialog.exec() != QDialog.Accepted:
            return
        opt = dialog.get_values()
        LoftTool._saved = dict(opt)

        try:
            pts, side_faces, caps, info = build_loft(profiles, opt)
        except ValueError as e:
            QMessageBox.warning(viewport, PLUGIN_NAME, str(e))
            return

        self.make_group(viewport, pts, side_faces, caps, info, opt)

    def on_deactivate(self, viewport):
        pass

    def make_group(self, viewport, pts, side_faces, caps, info, opt):
        name = opt['name']
        stats = {'faces': 0, 'errors': 0, 'err': None, 'split_caps': 0, 'soft': None}
        made = []

        def mutate(scene):
            from core.mesh import Mesh
            from core.group import Group

            target = Mesh()
            # one shared vertex object per point, so neighbouring faces share edges
            V = [VertexWrapper(*p) for p in pts]

            def emit(idx):
                try:
                    f = target.add_face([V[k] for k in idx])
                    if f is not None:
                        made.append(f)
                    stats['faces'] += 1
                    return True
                except Exception as e:
                    stats['errors'] += 1
                    stats['err'] = e
                    return False

            for f in side_faces:
                emit(f)
            for loop, normal in caps:
                try:
                    f = target.add_face([V[k] for k in loop])
                    if f is not None:
                        made.append(f)
                    stats['faces'] += 1
                except Exception:
                    # the app didn't take the cap as one polygon: use triangles instead
                    stats['split_caps'] += 1
                    for tri in _ear_clip(loop, pts, normal):
                        emit(tri)

            if stats['faces'] == 0:
                raise RuntimeError("No faces could be created (%s)." % stats['err'])

            g = Group(name)
            g.mesh = target
            if hasattr(scene, 'add_group'):
                scene.add_group(g)
            elif hasattr(scene, 'groups') and isinstance(scene.groups, list):
                scene.groups.append(g)
            else:
                raise RuntimeError("Could not add the loft group to the scene.")
            for fn_name in ('recompute_normals', 'update_normals', 'rebuild', 'invalidate'):
                fn = getattr(target, fn_name, None)
                if callable(fn):
                    try:
                        fn()
                    except Exception:
                        pass
            if opt.get('soften'):
                stats['soft'] = soften_edges(target, made, opt.get('soft_angle', 30))

        try:
            viewport.history.execute(SnapshotImport(mutate))
        except Exception as e:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Loft failed:\n%s" % e)
            return
        viewport.notify_scene_changed()

        msg = "%s: %d faces, %d points per ring, %d rings" % (
            PLUGIN_NAME, stats['faces'], info['points'], info['rings'])
        print(msg)
        if stats['split_caps']:
            print("%s: %d cap(s) were made from triangles." % (PLUGIN_NAME, stats['split_caps']))
        if stats['soft'] is not None:
            s_n, h_n, e_n = stats['soft']
            if e_n == 0:
                print("%s: could not find the mesh's edges, so nothing was softened." % PLUGIN_NAME)
            else:
                print("%s: softened %d edges, kept %d sharp edges." % (PLUGIN_NAME, s_n, h_n))
        if stats['errors']:
            print("%s: %d face(s) failed. First error: %s" % (PLUGIN_NAME, stats['errors'], stats['err']))
        try:
            viewport.flash_status(msg, 3000)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Running from the Python console
# ---------------------------------------------------------------------------
def _find_viewport():
    from PySide6.QtWidgets import QApplication
    for w in QApplication.allWidgets():
        if hasattr(w, 'scene') and hasattr(w, 'history') and hasattr(w, 'notify_scene_changed'):
            return w
    return None


def run(viewport=None):
    """Console entry point: select the profile faces, then call run()."""
    viewport = viewport or _find_viewport()
    if viewport is None:
        print("%s: could not find the viewport. Call run(<your viewport>) instead." % PLUGIN_NAME)
        return
    LoftTool().on_activate(viewport)
