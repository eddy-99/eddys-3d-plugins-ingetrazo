# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Brick & Block Studio for IngeTrazo
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
3D Brick & Block Studio - brick, block and stone walling for IngeTrazo
Bricks and blocks in bonds (header and soldier courses, row offsets), stone walling in
coursed ashlar, random rubble, dry-stone and Welsh slate, quoins up the corners and round
openings (doorways too), stone heads and sills, copings (slabs, rounded or stepped saddleback,
bricks on edge, cock and hen, upright slates), weathering and bomb-site damage (worn, kicked-out
and sunk units, a broken-down top, blast holes and missing units that can go right through,
hanging units taken out, rubble at the foot), and rubble piles with planks, barrels, crates and
your own objects. Sizes in real-world mm.
Version 7.9: the level bands of a brick cut round an arch are always joined back up, even where the
general join can't manage it (no more thin stacked strips beside an arch).
Version 7.8: a brick cut round an arch is worked out a sounder way (in level bands, each cut along
the arch's true line, then joined back into one piece), so no overlaps, odd triangles or fans.
Version 7.7: the bits of a brick cut round an arch are joined back into one piece more readily (no
fans of thin wedges), and only really thin slivers are left out, so no brick-sized gaps by the arch.
Version 7.6: no thin slivers of brick left along an arch where it runs almost level with the
courses (near the crown): a cut piece thinner than 'Smallest cut piece' is left out, and the
mortar shows there instead.
Version 7.5: bricks round an arch (or any opening that isn't a plain box) are cut along the arch's
true line, not in little steps of thin slices.
Version 7.4: no more bricks missing round arched windows - an opening is only smoothed over
when its outline really is nearly round (not when an arch ring stands out past the window).
Version 7.3: follows the outside face other plugins mark on their pieces (3D Bridges & Arches), and
leaves out the pieces they mark as not walls (pier linings, end walls, barrels...).
"""

import os
import json
import math
import random
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtCore import Qt
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QDoubleSpinBox, QSpinBox,
    QCheckBox, QComboBox, QDialogButtonBox, QMessageBox, QPushButton,
    QInputDialog, QListWidget, QListWidgetItem, QLineEdit, QLabel, QWidget, QTabWidget
)

PLUGIN_NAME = "3D Brick & Block Studio"
VERSION = "7.9"             # shown in the window title, so you can tell which file is loaded


PLAIN_PAINT = (("walling - brick", (181, 86, 60)), ("walling", (190, 182, 160)), ("quoin", (218, 208, 182)),
               ("heads", (218, 208, 182)), ("coping", (196, 190, 178)), ("backing", (205, 200, 188)))


def _part_attrs(scene, name):
    """The face paint for one part of the walling built into a wall (marked as walling, so the
    Whole building page knows that wall has some)."""
    import sys as _sys
    a = None
    try:
        for _nm, lc in list(_sys.modules.items()):
            if _nm.endswith("ed3d_layers_colours") and hasattr(lc, '_pick_row'):
                pal = lc.load_settings()['palette']
                row = lc._pick_row(pal, [name], PLUGIN_NAME)
                if row is not None:
                    a = dict(lc._paint_attrs(scene, row, False))
                break
    except Exception as _e:
        print("%s: colour %r: %s" % (PLUGIN_NAME, name, _e))
    if a is None:
        low = name.lower()
        rgb = next((c for w, c in PLAIN_PAINT if low.startswith(w) or w in low), (190, 182, 160))
        a = {"color": tuple(c / 255.0 for c in rgb)}
    a[BRICK_MARK] = 1
    return a


def _ed3d_organise(scene, group):
    """Hands a new group to 3D Layers & Colours, if it's there, to put on its layer and colour
    its parts. Never stops a build: if anything goes wrong the group is simply left as it is."""
    import sys as _sys
    try:
        for _nm, _mod in list(_sys.modules.items()):
            if _nm.endswith("ed3d_layers_colours") and hasattr(_mod, "organise"):
                _mod.organise(scene, group, PLUGIN_NAME)
                return
    except Exception as _e:
        print("%s: layers & colours skipped: %s" % (PLUGIN_NAME, _e))


MERGE_PIECES = True
TRIANGULATE_FRONT = False   # True if Mesh.add_face rejects polygons with >4 points

# ---------------------------------------------------------------------------
# Presets: one file each in Documents\IngeTrazo Presets\Brick and Block, like the other
# plugins. The old single presets file is still read, so nothing is lost.
# ---------------------------------------------------------------------------
PRESET_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Brick and Block")
PRESET_FILE = os.path.join(os.path.expanduser("~"), ".brick_block_studio_presets.json")
LEGACY_PRESET_FILES = [
    os.path.join(os.path.expanduser("~"), ".aparejo_presets.json"),
    os.path.join(os.path.expanduser("~"), ".eddys_bricks_presets.json"),
]

# Sizes an older version remembered in metres (turned back into mm)
SIZE_KEYS = ('length', 'height', 'depth', 'joint', 'min_frag', 'header_len', 'soldier_len')

def load_user_presets():
    for path in [PRESET_FILE] + LEGACY_PRESET_FILES:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def save_user_presets(presets):
    try:
        with open(PRESET_FILE, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2)
        return True
    except Exception as e:
        print("Could not save presets:", e)
        return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def vertex_to_vector3d(v):
    if isinstance(v, QVector3D):
        return v
    for get in (lambda: (v.x(), v.y(), v.z()),
                lambda: (v.x, v.y, v.z),
                lambda: (v[0], v[1], v[2])):
        try:
            x, y, z = get()
            return QVector3D(float(x), float(y), float(z))
        except Exception:
            pass
    return QVector3D(0, 0, 0)


class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))

    def toTuple(self):
        return (self.x(), self.y(), self.z())


def _area(poly):
    a = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        a += x1 * y2 - x2 * y1
    return a * 0.5


def _bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return (min(xs), max(xs), min(ys), max(ys))


def _pip(x, y, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _is_convex(poly):
    sign = 0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        x3, y3 = poly[(i + 2) % n]
        cr = (x2 - x1) * (y3 - y2) - (y2 - y1) * (x3 - x2)
        if abs(cr) < 1e-12:
            continue
        s = 1 if cr > 0 else -1
        if sign and s != sign:
            return False
        sign = s
    return True


def _convex_parts(q):
    if _area(q) < 0:
        q = q[::-1]
    if len(q) != 4 or _is_convex(q):
        return [q]
    for i in range(4):
        a, b, c = q[i - 1], q[i], q[(i + 1) % 4]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) < 0:
            return [[q[i], q[(i + 1) % 4], q[(i + 2) % 4]],
                    [q[i], q[(i + 2) % 4], q[(i + 3) % 4]]]
    return [q]


def _clip_edge(poly, p, q, keep_inside):
    dx, dy = q[0] - p[0], q[1] - p[1]
    s = 1.0 if keep_inside else -1.0

    def f(pt):
        return s * (dx * (pt[1] - p[1]) - dy * (pt[0] - p[0]))

    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        fa, fb = f(a), f(b)
        if fa >= 0:
            out.append(a)
        if (fa >= 0) != (fb >= 0):
            t = fa / (fa - fb)
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    return out


def _subtract_convex(poly, hole):
    n = len(hole)
    for i in range(n):
        p, q = hole[i], hole[(i + 1) % n]
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy)
        if L < 1e-12:
            continue
        if all((dx * (pt[1] - p[1]) - dy * (pt[0] - p[0])) / L <= 1e-7 for pt in poly):
            return [poly]
    pieces = []
    rem = poly
    for i in range(n):
        p, q = hole[i], hole[(i + 1) % n]
        out = _clip_edge(rem, p, q, False)
        if len(out) >= 3:
            pieces.append(out)
        rem = _clip_edge(rem, p, q, True)
        if len(rem) < 3:
            break
    return pieces


def _hole_intervals(poly, y):
    xs = []
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 <= y < y2) or (y2 <= y < y1):
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    xs.sort()
    return [[xs[i], xs[i + 1]] for i in range(0, len(xs) - 1, 2)]


def _hole_convex_parts(hole):
    """An opening that isn't convex (an arched window with its brick ring) split into a few convex
    pieces: cut into triangles, then neighbours joined back while they stay convex."""
    h = [tuple(p) for p in hole]
    if _area(h) < 0:
        h = h[::-1]
    parts = [list(t) for t in _ear_clip(h)]
    merged = True
    while merged and len(parts) > 1:
        merged = False
        for a in range(len(parts)):
            A = parts[a]
            for b in range(a + 1, len(parts)):
                B = parts[b]
                joined = None
                for i in range(len(A)):
                    u, v = A[i], A[(i + 1) % len(A)]
                    for j in range(len(B)):
                        if B[j] == v and B[(j + 1) % len(B)] == u:
                            # walk A from v round to u, then B from after u round to before v
                            ra = [A[(i + 1 + k) % len(A)] for k in range(len(A))]
                            rb = [B[(j + 2 + k) % len(B)] for k in range(len(B) - 2)]
                            joined = ra + rb
                            break
                    if joined:
                        break
                if joined and _is_convex(joined) and _area(joined) > 0:
                    parts[a] = joined
                    del parts[b]
                    merged = True
                    break
            if merged:
                break
    return [p for p in parts if len(p) >= 3 and _area(p) > 0]


_PARTS_CACHE = {}


def _subtract_exact(poly, hole):
    """A brick with the opening taken out of it, along the opening's true outline."""
    key = id(hole)
    got = _PARTS_CACHE.get(key)
    if got is None or got[0] is not hole:
        if len(_PARTS_CACHE) > 400:
            _PARTS_CACHE.clear()
        got = (hole, [(p, _bbox(p)) for p in _hole_convex_parts(hole)])
        _PARTS_CACHE[key] = got
    parts = got[1]
    if not parts:
        raise ValueError("opening couldn't be split")
    pieces = [list(poly)]
    for part, (hx1, hx2, hy1, hy2) in parts:
        nxt = []
        for pc in pieces:
            px = [p[0] for p in pc]
            py = [p[1] for p in pc]
            if max(px) <= hx1 or min(px) >= hx2 or max(py) <= hy1 or min(py) >= hy2:
                nxt.append(pc)
            else:
                nxt.extend(q for q in _subtract_convex(pc, part) if len(q) >= 3)
        pieces = nxt
        if not pieces:
            break
    return pieces


def _seg_y_cross(a, b, c, d):
    """The height where segment ab crosses segment cd, or None."""
    r = (b[0] - a[0], b[1] - a[1])
    q = (d[0] - c[0], d[1] - c[1])
    den = r[0] * q[1] - r[1] * q[0]
    if abs(den) < 1e-30:
        return None
    t = ((c[0] - a[0]) * q[1] - (c[1] - a[1]) * q[0]) / den
    u = ((c[0] - a[0]) * r[1] - (c[1] - a[1]) * r[0]) / den
    if 0.0 < t < 1.0 and 0.0 < u < 1.0:
        return a[1] + t * r[1]
    return None


def _subtract_bands(poly, hole):
    """poly with the opening taken out, exactly: cut into level bands at every corner and every
    crossing, so inside each band every edge runs straight across; there the pieces left are
    trapezoids between the edges, and those are joined back up afterwards."""
    pe = [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]
    he = [(hole[i], hole[(i + 1) % len(hole)]) for i in range(len(hole))]
    y_lo = min(p[1] for p in poly)
    y_hi = max(p[1] for p in poly)
    ys = {y_lo, y_hi}
    for p in hole:
        if y_lo < p[1] < y_hi:
            ys.add(p[1])
    for p in poly:
        ys.add(p[1])
    px1, px2 = min(p[0] for p in poly), max(p[0] for p in poly)
    for a, b in pe:
        for c, d in he:
            if max(c[0], d[0]) < min(a[0], b[0]) or min(c[0], d[0]) > max(a[0], b[0]):
                continue
            yc = _seg_y_cross(a, b, c, d)
            if yc is not None and y_lo < yc < y_hi:
                ys.add(yc)
    ys = sorted(ys)
    span = max(y_hi - y_lo, px2 - px1, 1e-12)
    out = []

    def x_at(e, y):
        (x1, y1), (x2, y2) = e
        if abs(y2 - y1) < 1e-300:
            return x1
        return x1 + (y - y1) * (x2 - x1) / (y2 - y1)
    for y0, y1 in zip(ys, ys[1:]):
        if y1 - y0 <= span * 1e-9:
            continue
        ym = (y0 + y1) * 0.5
        cross = []
        for e in pe:
            (ax, ay), (bx, by) = e
            if min(ay, by) <= y0 and max(ay, by) >= y1 and ay != by:
                cross.append((x_at(e, ym), 0, e))
        for e in he:
            (ax, ay), (bx, by) = e
            if min(ay, by) <= y0 and max(ay, by) >= y1 and ay != by:
                cross.append((x_at(e, ym), 1, e))
        cross.sort(key=lambda t: t[0])
        in_p = in_h = False
        for k in range(len(cross) - 1):
            _x, which, e = cross[k]
            if which == 0:
                in_p = not in_p
            else:
                in_h = not in_h
            if in_p and not in_h:
                e2 = cross[k + 1][2]
                l0, l1 = x_at(e, y0), x_at(e, y1)
                r0, r1 = x_at(e2, y0), x_at(e2, y1)
                trap = [(l0, y0), (r0, y0), (r1, y1), (l1, y1)]
                trap = [p for i, p in enumerate(trap)
                        if abs(p[0] - trap[i - 1][0]) > span * 1e-12 or abs(p[1] - trap[i - 1][1]) > span * 1e-12]
                if len(trap) >= 3 and _area(trap) > span * span * 1e-12:
                    out.append(trap)
    return out


def _join_shared(pieces, eps):
    """Joins pieces that share a whole edge (one band on top of the next) into one, again and again
    until none do. Simple and sure: used before the general join, so even if that one gives up the
    bands are already joined."""
    def key(p):
        return (round(p[0] / eps), round(p[1] / eps))
    pcs = [list(p) for p in pieces]
    changed = True
    while changed and len(pcs) > 1:
        changed = False
        edge_of = {}
        for k, pc in enumerate(pcs):
            for i in range(len(pc)):
                edge_of.setdefault((key(pc[i]), key(pc[(i + 1) % len(pc)])), (k, i))
        for k, pc in enumerate(pcs):
            for i in range(len(pc)):
                u, v = key(pc[i]), key(pc[(i + 1) % len(pc)])
                hit = edge_of.get((v, u))
                if hit is None or hit[0] == k:
                    continue
                m, j = hit
                B = pcs[m]
                # this piece from v round to u, then the other from after u round to before v
                ra = [pc[(i + 1 + t) % len(pc)] for t in range(len(pc))]
                rb = [B[(j + 2 + t) % len(B)] for t in range(len(B) - 2)]
                joined = _simplify(ra + rb, eps)
                if len(joined) >= 3 and abs(abs(_area(joined)) - abs(_area(pc)) - abs(_area(B))) <= \
                        1e-6 * (abs(_area(pc)) + abs(_area(B))) + eps * eps:
                    pcs = [p for t, p in enumerate(pcs) if t not in (k, m)] + [joined]
                    changed = True
                    break
            if changed:
                break
    return pcs


def _subtract_concave(poly, hole, subdiv):
    try:
        h = [tuple(p) for p in hole]
        return _subtract_bands([tuple(p) for p in poly], h)
    except Exception:
        pass                    # fall back to slices (the old way)
    return _subtract_concave_slices(poly, hole, subdiv)


def _subtract_concave_slices(poly, hole, subdiv):
    xs = [p[0] for p in poly]
    yv = [p[1] for p in poly]
    bx1, bx2, by1, by2 = min(xs), max(xs), min(yv), max(yv)
    ys = {by1, by2}
    for _, py in hole:
        if by1 < py < by2:
            ys.add(py)
    ys = sorted(ys)
    out = []
    for y0, y1 in zip(ys, ys[1:]):
        for k in range(subdiv):
            a = y0 + (y1 - y0) * k / subdiv
            b = y0 + (y1 - y0) * (k + 1) / subdiv
            if b - a < 1e-9:
                continue
            e = (b - a) * 1e-6
            cuts = []
            for y in (a + e, (a + b) * 0.5, b - e):
                cuts.extend(_hole_intervals(hole, y))
            cuts.sort()
            cur = bx1
            for c0, c1 in cuts:
                if c1 <= cur:
                    continue
                if c0 >= bx2:
                    break
                if c0 > cur:
                    out.append([(cur, a), (c0, a), (c0, b), (cur, b)])
                cur = max(cur, c1)
            if cur < bx2:
                out.append([(cur, a), (bx2, a), (bx2, b), (cur, b)])
    return out


def _simplify(loop, eps):
    out = list(loop)
    changed = True
    while changed and len(out) > 3:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            if abs(cr) < eps * eps * 100:
                del out[i]
                changed = True
                break
    return out


def _merge(pieces, eps):
    if len(pieces) < 2:
        return pieces
    pts = [p for pc in pieces for p in pc]

    def key(p):
        return (round(p[0] / eps), round(p[1] / eps))

    edges = {}
    for pc in pieces:
        n = len(pc)
        for i in range(n):
            a, b = pc[i], pc[(i + 1) % n]
            abx, aby = b[0] - a[0], b[1] - a[1]
            L2 = abx * abx + aby * aby
            if L2 < eps * eps:
                continue
            ka, kb = key(a), key(b)
            mids = []
            for p in pts:
                kp = key(p)
                if kp == ka or kp == kb:
                    continue
                t = ((p[0] - a[0]) * abx + (p[1] - a[1]) * aby) / L2
                if t <= 0 or t >= 1:
                    continue
                dx = a[0] + t * abx - p[0]
                dy = a[1] + t * aby - p[1]
                if dx * dx + dy * dy < (10 * eps) ** 2:
                    mids.append((t, p))
            mids.sort()
            chain = [a] + [m[1] for m in mids] + [b]
            for j in range(len(chain) - 1):
                k1, k2 = key(chain[j]), key(chain[j + 1])
                if k1 == k2:
                    continue
                if (k2, k1) in edges:
                    del edges[(k2, k1)]
                else:
                    edges[(k1, k2)] = (chain[j], chain[j + 1])
    out_map = {}
    for (k1, k2), (p, q) in edges.items():
        out_map.setdefault(k1, []).append((k2, p))
    loops = []
    while out_map:
        k0 = next(iter(out_map))
        loop = []
        k = k0
        while True:
            lst = out_map.get(k)
            if not lst:
                break
            k2, p = lst.pop()
            if not lst:
                del out_map[k]
            loop.append(p)
            k = k2
            if k == k0:
                break
        loop = _simplify(loop, eps)
        if len(loop) >= 3:
            loops.append(loop)
    old = sum(abs(_area(pc)) for pc in pieces)
    new = sum(abs(_area(lp)) for lp in loops)
    if not loops or abs(old - new) > old * 0.01:
        return pieces
    return loops


def _hull(pts):
    pts = sorted(set((round(p[0], 12), round(p[1], 12)) for p in pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def _hull_gap(h, hull):
    """How far the opening's outline comes in from its smooth outline, at the most."""
    worst = 0.0
    m = len(hull)
    for p in h:
        best = None
        for j in range(m):
            a, b = hull[j], hull[(j + 1) % m]
            dx, dy = b[0] - a[0], b[1] - a[1]
            L2 = dx * dx + dy * dy
            t = 0.0 if L2 <= 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
            d = math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)
            if best is None or d < best:
                best = d
        worst = max(worst, best or 0.0)
    return worst


def _smooth_hole(h, tol=None):
    """(hole, box, convex) for an opening. One that is very nearly convex - a round window with
    little teeth round it from a brick ring - is taken as its smooth outline, so the bricks round
    it are cut cleanly instead of in thin slices. Only when the teeth are small (under tol): an
    arched window whose brick ring stands out past the window is cut round properly, or the
    bricks in the corners beside the ring were cut away too, leaving dark gaps."""
    if _is_convex(h):
        return (h, _bbox(h), True)
    hull = _hull(h)
    if len(hull) >= 3 and abs(_area(h)) >= 0.97 * abs(_area(hull)):
        if tol is None or _hull_gap(h, hull) <= tol:
            return (hull, _bbox(hull), True)
    return (h, _bbox(h), False)


def _seg_cross(a, b, c, d):
    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    d1, d2, d3, d4 = o(c, d, a), o(c, d, b), o(a, b, c), o(a, b, d)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and d1 * d2 < 0 and d3 * d4 < 0


def _overlaps(pc, hole):
    """Does a piece (a brick) really overlap an opening - not just its box?"""
    if any(_pip(q[0], q[1], hole) for q in pc):
        return True
    if any(_pip(q[0], q[1], pc) for q in hole):
        return True
    cx = sum(q[0] for q in pc) / len(pc)
    cy = sum(q[1] for q in pc) / len(pc)
    if _pip(cx, cy, hole):
        return True
    bx1, bx2, by1, by2 = _bbox(pc)
    n, m = len(pc), len(hole)
    for j in range(m):
        c, d = hole[j], hole[(j + 1) % m]
        if max(c[0], d[0]) < bx1 or min(c[0], d[0]) > bx2 or max(c[1], d[1]) < by1 or min(c[1], d[1]) > by2:
            continue
        for i in range(n):
            if _seg_cross(pc[i], pc[(i + 1) % n], c, d):
                return True
    return False


def trim_poly(poly, holes, subdiv, min_frag):
    pieces = [list(poly)]
    bx1, bx2, by1, by2 = _bbox(poly)
    ext = max(bx2 - bx1, by2 - by1)
    for hole, (hx1, hx2, hy1, hy2), convex in holes:
        if bx2 <= hx1 or bx1 >= hx2 or by2 <= hy1 or by1 >= hy2:
            continue
        nxt = []
        for pc in pieces:
            px = [p[0] for p in pc]
            py = [p[1] for p in pc]
            if max(px) <= hx1 or min(px) >= hx2 or max(py) <= hy1 or min(py) >= hy2:
                nxt.append(pc)
            elif convex:
                nxt.extend(_subtract_convex(pc, hole))
            elif not _overlaps(pc, hole):
                nxt.append(pc)                  # near an uneven opening but not touching it: left whole
            else:
                nxt.extend(_subtract_concave(pc, hole, subdiv))
        pieces = nxt
        if not pieces:
            break
    if MERGE_PIECES and len(pieces) > 1:
        pieces = _join_shared(pieces, ext * 1e-6)
        if len(pieces) > 1:
            pieces = _merge(pieces, ext * 1e-6)
    min_area = min_frag * min_frag * 0.5
    thin = min_frag * 0.2          # how thin a cut piece may be: 2 x area / perimeter is its width

    def thick_enough(pc):
        per = sum(math.hypot(pc[i][0] - pc[i - 1][0], pc[i][1] - pc[i - 1][1]) for i in range(len(pc)))
        return per <= 0 or 2.0 * abs(_area(pc)) / per >= thin
    return [pc for pc in pieces if len(pc) >= 3 and abs(_area(pc)) >= min_area and thick_enough(pc)]


# ---------------- trimming to the face's own outline ----------------
def _grow(poly, d):
    """A counter-clockwise polygon with every edge moved outwards by d."""
    n = len(poly)
    lines = []
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        L = math.hypot(bx - ax, by - ay) or 1e-12
        ex, ey = (bx - ax) / L, (by - ay) / L
        lines.append(((ax + ey * d, ay - ex * d), (ex, ey)))
    out = []
    for j in range(n):
        (a, ea), (b, eb) = lines[j - 1], lines[j]
        cr = ea[0] * eb[1] - ea[1] * eb[0]
        if abs(cr) < 1e-9:
            out.append(b)
        else:
            t = ((b[0] - a[0]) * eb[1] - (b[1] - a[1]) * eb[0]) / cr
            q = (a[0] + ea[0] * t, a[1] + ea[1] * t)
            px, py = poly[j]
            L = math.hypot(q[0] - px, q[1] - py)
            if L > 4 * d:
                q = (px + (q[0] - px) / L * 4 * d, py + (q[1] - py) / L * 4 * d)
            out.append(q)
    return out


def _ear_clip(poly):
    """Splits a simple polygon (counter-clockwise) into triangles."""
    rem = list(poly)
    tris = []

    def cross(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    guard = 0
    while len(rem) > 3 and guard < 100000:
        guard += 1
        n = len(rem)
        found = None
        for i in range(n):
            a, b, c = rem[i - 1], rem[i], rem[(i + 1) % n]
            if cross(a, b, c) <= 1e-14:
                continue
            if any(cross(a, b, p) >= 0 and cross(b, c, p) >= 0 and cross(c, a, p) >= 0
                   for p in rem if p is not a and p is not b and p is not c):
                continue
            found = i
            break
        if found is None:      # only flat corners left: drop the flattest one
            found = min(range(n), key=lambda i: abs(cross(rem[i - 1], rem[i], rem[(i + 1) % n])))
            del rem[found]
            continue
        tris.append([rem[found - 1], rem[found], rem[(found + 1) % len(rem)]])
        del rem[found]
    if len(rem) == 3 and abs(cross(*rem)) > 1e-14:
        tris.append(rem)
    return tris


def outline_clipper(outline):
    """Returns a function that trims a polygon to the face outline (any shape:
    circle, gable, arch, L-shape ...). Returns a list of pieces."""
    if _area(outline) < 0:
        outline = outline[::-1]
    convex = _is_convex(outline)
    parts = [outline] if convex else _ear_clip(outline)
    boxes = [_bbox(p) for p in parts]
    ext = max(_bbox(outline)[1] - _bbox(outline)[0], _bbox(outline)[3] - _bbox(outline)[2]) or 1.0

    def clip(poly):
        bx1, bx2, by1, by2 = _bbox(poly)
        pieces = []
        for part, (px1, px2, py1, py2) in zip(parts, boxes):
            if bx2 <= px1 or bx1 >= px2 or by2 <= py1 or by1 >= py2:
                continue
            pc = list(poly)
            n = len(part)
            for i in range(n):
                pc = _clip_edge(pc, part[i], part[(i + 1) % n], True)
                if len(pc) < 3:
                    break
            if len(pc) >= 3 and abs(_area(pc)) > ext * ext * 1e-12:
                pieces.append(pc)
        if len(pieces) > 1:
            pieces = _merge(pieces, ext * 1e-7)     # join the triangle pieces back into whole bricks
        return pieces

    return clip


def _level_dirs(pts, normal):
    """Course directions: level along an upright wall, otherwise along the longest edge."""
    if abs(normal.z()) < 0.95:
        u = QVector3D.crossProduct(QVector3D(0, 0, 1), normal).normalized()
        v = QVector3D.crossProduct(normal, u).normalized()
        return u, v
    best = max(range(len(pts)), key=lambda i: (pts[(i + 1) % len(pts)] - pts[i]).length())
    u = (pts[(best + 1) % len(pts)] - pts[best]).normalized()
    v = QVector3D.crossProduct(normal, u).normalized()
    return u, v


# ---------------- soldier course ----------------
def _chain_info(pts, closed):
    n = len(pts)
    cnt = n if closed else n - 1
    segs = []
    total = 0.0
    for i in range(cnt):
        a, b = pts[i], pts[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 1e-12:
            continue
        segs.append((total, L, a, b))
        total += L
    return segs, total


def _at(segs, total, s, closed):
    if closed:
        s = s % total
    else:
        s = min(max(s, 0.0), total)
    for s0, L, a, b in segs:
        if s <= s0 + L:
            t = (s - s0) / L
            return ((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t),
                    ((b[0] - a[0]) / L, (b[1] - a[1]) / L))
    s0, L, a, b = segs[-1]
    return b, ((b[0] - a[0]) / L, (b[1] - a[1]) / L)


def _station(segs, total, s, closed, eps):
    p, t0 = _at(segs, total, s, closed)
    ta = _at(segs, total, s - eps, closed)[1]
    tb = _at(segs, total, s + eps, closed)[1]
    tx, ty = ta[0] + tb[0], ta[1] + tb[1]
    L = math.hypot(tx, ty)
    if L < 1e-9:
        tx, ty = t0
    else:
        tx, ty = tx / L, ty / L
    return p, (tx, ty), (ty, -tx)


def _corner_poly(c, nA, nB, d, R):
    k = R / (1.0 + d)
    return [c,
            (c[0] + nA[0] * R, c[1] + nA[1] * R),
            (c[0] + (nA[0] + nB[0]) * k, c[1] + (nA[1] + nB[1]) * k),
            (c[0] + nB[0] * R, c[1] + nB[1] * R)]


def _soldiers(hole, w, J, S, corner_deg):
    n = len(hole)
    tans = []
    for i in range(n):
        a, b = hole[i], hole[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        tans.append(((b[0] - a[0]) / L, (b[1] - a[1]) / L) if L > 1e-12 else (1.0, 0.0))
    cos_lim = math.cos(math.radians(corner_deg))
    corners = []
    for i in range(n):
        t1, t2 = tans[i - 1], tans[i]
        if t1[0] * t2[0] + t1[1] * t2[1] < cos_lim:
            corners.append((i, (t1[0] * t2[1] - t1[1] * t2[0]) > 0))
    sold, cpolys, excl = [], [], []
    for i, convex in corners:
        if not convex:
            continue
        nA = (tans[i - 1][1], -tans[i - 1][0])
        nB = (tans[i][1], -tans[i][0])
        d = nA[0] * nB[0] + nA[1] * nB[1]
        if 1.0 + d < 0.05:
            continue
        cpolys.append(_corner_poly(hole[i], nA, nB, d, S))
        excl.append(_corner_poly(hole[i], nA, nB, d, S + J))
    chains = []
    if not corners:
        chains.append((list(hole), True))
    else:
        idx = [c[0] for c in corners]
        for k in range(len(idx)):
            i0, i1 = idx[k], idx[(k + 1) % len(idx)]
            pts = [hole[i0]]
            j = i0
            while True:
                j = (j + 1) % n
                pts.append(hole[j])
                if j == i1:
                    break
            chains.append((pts, False))
    R = S + J
    for pts, closed in chains:
        segs, total = _chain_info(pts, closed)
        if not segs or total < w:
            continue
        m = max(1, int(round(total / (w + J))))
        pitch = total / m
        eps = pitch * 0.01
        st = [_station(segs, total, k * pitch, closed, eps) for k in range(m + 1)]
        for k in range(m):
            p0, t0, n0 = st[k]
            p1, t1, n1 = st[k + 1]
            excl.append([p0, (p0[0] + n0[0] * R, p0[1] + n0[1] * R),
                         (p1[0] + n1[0] * R, p1[1] + n1[1] * R), p1])
            a = (p0[0] + t0[0] * J / 2.0, p0[1] + t0[1] * J / 2.0)
            b = (p1[0] - t1[0] * J / 2.0, p1[1] - t1[1] * J / 2.0)
            sold.append([a, (a[0] + n0[0] * S, a[1] + n0[1] * S),
                         (b[0] + n1[0] * S, b[1] + n1[1] * S), b])
    return sold, cpolys, excl


# ---------------- bond patterns and row offsets ----------------
def _course(r, l, hl, J, bond, header_every):
    step = l + J
    if header_every > 0 and (r + 1) % header_every == 0:
        return [hl], 0.0
    if bond == "stack":
        return [l], 0.0
    if bond == "third":
        return [l], (r % 3) * step / 3.0
    if bond == "english":
        if r % 2 == 1:
            return [hl], l + J / 2.0 - hl / 2.0
        return [l], 0.0
    if bond == "flemish":
        return [l, hl], (r % 2) * (l + hl + 2 * J) / 2.0
    return [l], (r % 2) * step / 2.0


def _parse_seq(text):
    vals = []
    for tok in str(text or "").replace(";", ",").replace(" ", ",").split(","):
        tok = tok.strip()
        if not tok:
            continue
        try:
            vals.append(float(tok))
        except Exception:
            pass
    return vals or [0.0]


def _row_offsets(mode, rows, step, fixed, seq_text, seed, rmax):
    """Absolute shift per course, or None to keep the bond's own offsets."""
    if mode == "fixed":
        return [(r % 2) * fixed * step for r in range(rows)]
    if mode == "sequence":
        vals = _parse_seq(seq_text)
        return [vals[r % len(vals)] * step for r in range(rows)]
    if mode == "random":
        rng = random.Random(seed)
        out = []
        prev = None
        for r in range(rows):
            s = 0.0
            for _ in range(40):
                s = rng.uniform(0.0, max(rmax, 0.01)) * step
                if prev is None:
                    break
                d = abs(s - prev) % step
                d = min(d, step - d)
                if d >= 0.12 * step:      # avoid joints lining up with the course below
                    break
            out.append(s)
            prev = s
        return out
    return None


def _even_ends(pcs, J, min_end, near=()):
    """No slivers, and no brick longer than a standard one: when the first or last piece
    of a run is shorter than min_end, it takes some length from its neighbour (which gets
    shorter). Where the joint between them goes is picked to keep it as far as it can from
    the joints in the course below (`near`), so the bond stays staggered."""
    if min_end <= 0 or len(pcs) < 2:
        return pcs
    pcs = list(pcs)

    def place(lo, hi, total, first):
        # length s of the outer piece: both pieces at least min_end, neither longer than before
        smin = max(min_end, total - J - (hi - lo))
        smax = min(total - J - min_end, hi - lo)
        if smax < smin:
            return None
        best, best_d = smin, -1.0
        for k in range(21):
            s_ = smin + (smax - smin) * k / 20.0
            jx = (lo + s_ + J / 2.0) if first else (lo + total - s_ - J / 2.0)
            d = min((abs(jx - q) for q in near), default=1e18)
            if d > best_d + 1e-9:
                best, best_d = s_, d
        return best

    # first piece of the run
    (a0, e0, h0), (a1, e1, h1) = pcs[0], pcs[1]
    if e0 - a0 < min_end:
        total = e1 - a0
        s_ = place(a0, a0 + (e1 - a1), total, True)
        if s_ is not None:
            pcs[0], pcs[1] = (a0, a0 + s_, h1), (a0 + s_ + J, e1, h1)
    # last piece of the run
    if len(pcs) >= 2:
        (a0, e0, h0), (a1, e1, h1) = pcs[-2], pcs[-1]
        if e1 - a1 < min_end:
            total = e1 - a0
            s_ = place(a0, a0 + (e0 - a0), total, False)
            if s_ is not None:
                pcs[-2], pcs[-1] = (a0, e1 - s_ - J, h0), (e1 - s_, e1, h0)
    return pcs


def bond_layout(l, w, J, hl, bond, header_every, offset_mode, offset_fixed, offset_seq,
                offset_seed, offset_rmax, W, H, tiny=0.0, segments=None, min_end=0.0, x0=0.0,
                y0=0.0, r0=0):
    """Every brick rectangle of the bond over a W x H panel, before any trimming:
    [(x1, y1, x2, y2, is_header)]. Used by both the generator and the preview.
    segments(y1, y2) gives the runs of wall a course is laid in (between openings); with
    min_end, the bricks at the two ends of each run are evened up so there are no slivers.
    x0 lines the bond up: a course with no offset has a brick starting there.
    y0 and r0 line the courses up with the walls above and below (so they run on through the
    floor levels): the first course starts y0 below the bottom of the panel (cut off there), and
    it's course number r0 counted from the ground, so the bond carries on where the wall below
    left off."""
    out = []
    prev_joints = []
    step_y = w + J
    y0 = y0 if 0.0 <= y0 < step_y else 0.0
    r0 = max(0, int(r0))
    rows = int(math.ceil((H + y0) / step_y)) + 1
    # when the courses carry on from a wall below, the course just under this wall is laid too
    # (not kept) so the first course here is staggered against it exactly as the wall below did
    first = -1 if r0 > 0 else 0
    offs = _row_offsets(offset_mode, rows + r0, l + J, offset_fixed, offset_seq, offset_seed, offset_rmax)
    for rr in range(first, rows):
        r = rr + r0                       # the course number, counted from the ground
        y = rr * step_y - y0
        if y >= H:
            continue
        cw = w if y + w <= H else max(0.0005, H - y)
        ghost = False
        if y < 0.0:
            if y + w <= tiny:
                ghost = True              # all of this course is in the wall below: joints only
            else:
                cw, y = y + w, 0.0        # the top of a course that started in the wall below
        unit, shift = _course(r, l, hl, J, bond, header_every)
        if offs is not None:
            is_header = header_every > 0 and (r + 1) % header_every == 0
            if bond in ("running", "stack", "third") or is_header:
                shift = offs[r]
            else:
                shift += offs[r]
        period = sum(unit) + len(unit) * J
        x = ((shift + x0) % period) - period
        row = []
        while x < W:
            for L in unit:
                sx, ex = x, x + L
                x = ex + J
                row.append((sx, ex, abs(L - hl) < 1e-9 and abs(hl - l) > 1e-9))
        runs = segments(y, y + cw) if (segments is not None and not ghost) else [(0.0, W)]
        joints = []
        for a, b in runs:
            a, b = max(a, 0.0), min(b, W)
            pcs = [(max(sx, a), min(ex, b), hd) for sx, ex, hd in row if ex > a and sx < b]
            pcs = [pc for pc in pcs if pc[1] - pc[0] >= max(tiny, 1e-12)]
            pcs = _even_ends(pcs, J, min_end, prev_joints)
            for x1, x2, hd in pcs:
                if x2 - x1 >= tiny and not ghost:
                    out.append((x1, y, x2, y + cw, hd))
            joints += [x2 + J / 2.0 for _, x2, _ in pcs[:-1]]
        prev_joints = joints
    return out


def _span(poly, y):
    """(left, right) where a level line at height y crosses a polygon, or None."""
    xs = []
    n = len(poly)
    for i in range(n):
        (px, py), (qx, qy) = poly[i], poly[(i + 1) % n]
        if (py > y) != (qy > y):
            xs.append(px + (y - py) * (qx - px) / (qy - py))
    return (min(xs), max(xs)) if xs else None


def run_finder(outline, holes):
    """segments(y1, y2) for bond_layout: the runs of wall along a course, between the
    openings that the course passes right through."""
    def segments(y1, y2):
        e = (y2 - y1) * 1e-3
        ys = (y1 + e, (y1 + y2) / 2.0, y2 - e)
        sp = [s for s in (_span(outline, y) for y in ys) if s]
        if not sp:
            return []
        A, B = min(s[0] for s in sp), max(s[1] for s in sp)
        blocked = []
        for hole in holes:
            hs = [_span(hole, y) for y in ys]
            if any(h is None for h in hs):
                continue            # the opening only clips this course: trimming does it
            lo, hi = max(h[0] for h in hs), min(h[1] for h in hs)
            if hi > lo:
                blocked.append((lo, hi))
        blocked.sort()
        runs, x = [], A
        for lo, hi in blocked:
            if lo > x:
                runs.append((x, min(lo, B)))
            x = max(x, hi)
        if x < B:
            runs.append((x, B))
        return [r for r in runs if r[1] - r[0] > e]
    return segments


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


# ---------------- finding the openings ----------------
def _face_frame(face):
    pts = [vertex_to_vector3d(v) for v in face.vertices]
    if len(pts) < 3:
        return None
    n_raw = getattr(face, 'normal', None)
    normal = QVector3D(0, 0, 0)
    if n_raw is not None:
        normal = vertex_to_vector3d(n_raw() if callable(n_raw) else n_raw)
    if normal.length() < 0.001:
        normal = QVector3D.crossProduct(pts[1] - pts[0], pts[2] - pts[1])
    normal = normal.normalized() if normal.length() > 0.001 else QVector3D(0, 0, 1)
    origin = pts[0]
    u, v = _level_dirs(pts, normal)
    return pts, normal, origin, u, v


def _extent(face):
    try:
        pts = [vertex_to_vector3d(v) for v in face.vertices]
        xs = [p.x() for p in pts]
        ys = [p.y() for p in pts]
        zs = [p.z() for p in pts]
        return (max(xs) - min(xs)) + (max(ys) - min(ys)) + (max(zs) - min(zs))
    except Exception:
        return 0.0


# A doorway drawn up from the bottom of the wall isn't a hole in the face: it's a notch in the
# face's own outline. These are found here and given ids from NOTCH_BASE up.
NOTCH_BASE = 1000


def _clean_loop(poly, eps):
    out = []
    for q in poly:
        if not out or abs(q[0] - out[-1][0]) > eps or abs(q[1] - out[-1][1]) > eps:
            out.append(q)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) <= eps and abs(out[0][1] - out[-1][1]) <= eps:
        out.pop()
    return out


def outline_notches(outline):
    """Doorways: notches cut up into the bottom edge of the outline (the face's own shape, any
    winding). Returns their polygons (anticlockwise), left to right."""
    if len(outline) < 5:
        return []
    bx0, bx1, by0, by1 = _bbox(outline)
    size = max(bx1 - bx0, by1 - by0) or 1.0
    eps = size * 1e-6
    ol = _clean_loop(_ccw(list(outline)), eps)
    n = len(ol)
    tol = size * 1e-4
    on = [abs(q[1] - by0) <= tol for q in ol]
    if all(on) or not any(on):
        return []
    out = []
    # walk round from a corner ON the bottom line, so every doorway is met from its start (one that
    # began at a corner off the line could be cut in two and joined up wrongly)
    start = (on.index(True) + 1) % n
    i = 0
    while i < n:
        k = (start + i) % n
        if on[k]:
            i += 1
            continue
        run = []
        while i < n and not on[(start + i) % n]:
            run.append(ol[(start + i) % n])
            i += 1
        a = ol[(start + i - len(run) - 1) % n]     # the bottom corners either side of the run
        b = ol[(start + i) % n]
        # anticlockwise, the bottom edge runs left to right: a notch climbs up and comes back
        # down further to the right; the rest of the wall goes round the other way
        if b[0] - a[0] > tol and len(run) >= 2:
            poly = _ccw([a] + run + [b])
            x0, x1, y0, y1 = _bbox(poly)
            if y1 - by0 > tol * 10 and x1 - x0 < 0.95 * (bx1 - bx0) and abs(_area(poly)) > tol * tol:
                out.append(poly)
    out.sort(key=lambda p: _bbox(p)[0])
    return out


def find_openings(wall, others, unit_label, k=1.0):
    """Returns (list of (hole_index, label), preselected set or None).
    k turns the wall's own units into the ones shown (1000 for a wall drawn in metres).
    Doorways cut up into the bottom edge are listed too (ids from NOTCH_BASE)."""
    fr = _face_frame(wall)
    holes = getattr(wall, 'holes', None) or []
    if fr is None:
        return [], None
    pts, normal, origin, u, v = fr
    us = [QVector3D.dotProduct(p - origin, u) for p in pts]
    vs = [QVector3D.dotProduct(p - origin, v) for p in pts]
    min_u, min_v = min(us), min(vs)
    tol = max(max(us) - min_u, max(vs) - min_v) * 0.02
    polys = []
    for hi, hole in enumerate(holes):
        poly = []
        for hv in hole:
            q = vertex_to_vector3d(hv)
            poly.append((QVector3D.dotProduct(q - origin, u), QVector3D.dotProduct(q - origin, v)))
        if len(poly) >= 3:
            polys.append((hi, poly))
    n_holes = len(polys)
    for j, poly in enumerate(outline_notches(list(zip(us, vs)))):
        polys.append((NOTCH_BASE + j, poly))
    if not polys:
        return [], None
    sel = set()
    for f in others:
        try:
            fp = [vertex_to_vector3d(x) for x in f.vertices]
        except Exception:
            continue
        if not fp:
            continue
        c = sum(fp, QVector3D(0, 0, 0)) / float(len(fp))
        d = c - origin
        if abs(QVector3D.dotProduct(d, normal)) > tol:
            continue
        cx, cy = QVector3D.dotProduct(d, u), QVector3D.dotProduct(d, v)
        for hi, poly in polys:
            if _pip(cx, cy, poly):
                sel.add(hi)
    info = []
    for n, (hi, poly) in enumerate(polys):
        x0, x1, y0, y1 = _bbox(poly)
        if hi >= NOTCH_BASE:
            name = "Doorway %d" % (hi - NOTCH_BASE + 1)
        else:
            name = "Opening %d" % (n + 1)
        info.append((hi, "%s: %.0f x %.0f %s, at (%.0f, %.0f)"
                     % (name, (x1 - x0) * k, (y1 - y0) * k, unit_label, (x0 - min_u) * k,
                        (y0 - min_v) * k)))
    return info, (sel if sel else None)


# ---------------------------------------------------------------------------
# Whole building: finding the walls (like the Whole building page in 3D Period Windows)
# Each wall group's outside face is found (the big face with a matching back face behind it),
# taken into the world, and listed with a tick box. Walls that already have walling on them
# are marked, and start unticked.
# ---------------------------------------------------------------------------
REC_KEY = "ed3d_brick_block_studio"
_NOT_WALLS = ("floor", "ledge", "plate", "roof", "chimney", "subframe", "glazing", "gutter", "pipe",
              "tile", "walling", "quoin", "coping", "backing", "rubble", "heads and sills", "brick",
              "stone work", "canopy", "fence", "plank", "step", "sill", "frame", "sash", "post",
              "lintel", "brace", "stud", "rail", "rafter", "purlin", "truss", "nogging", "fascia",
              "barge", "soffit", "finial", "core", "pot", "flaunching")
# words that mean 'not a wall' anywhere in a group's name or the names of the groups it's in
_NEVER_WALLS = ("subframe", "chimney", "barge", "fascia", "soffit", "finial", "gutter", "downpipe",
                "roof", "canopy", "fence", "glazing frame", "truss")
_WALL_MAX = 0.6          # thickest wall looked for, as a fraction of a metre-drawn model (600 mm)


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


BRICK_MARK = 'ed3d_brick'      # set on the faces of walling built into a wall


def _mesh_has_walling(mesh):
    for f in _items(getattr(mesh, 'faces', None)):
        a = getattr(f, 'attrs', None)
        if isinstance(a, dict) and a.get(BRICK_MARK):
            return True
    return False


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


class WorldFace:
    """A wall face taken into the world (its group may be moved or turned), shaped like a mesh
    face so the walling can be laid on it the same way as on a picked face."""
    def __init__(self, pts, holes, obj, mesh):
        self.vertices = [QVector3D(*q) for q in pts]
        self.holes = [[QVector3D(*q) for q in h] for h in holes]
        self.normal = QVector3D(*_unit(_newell(pts)))
        self.obj = obj          # the real face, in its group's mesh
        self.mesh = mesh


def _world_faces(mesh, m):
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
        out.append({'pts': wp, 'holes': hls, 'n': _unit(nv), 'area': area, 'obj': f,
                    'attrs': dict(getattr(f, 'attrs', None) or {})})
    return out


def _split_at(loops, pts, tol):
    """Adds any of pts that lie part way along an edge of a loop into that edge, so faces that
    meet with a corner half way along another face's edge still share whole edges."""
    out = []
    for lp in loops:
        new = []
        n = len(lp)
        for i in range(n):
            a, b = lp[i], lp[(i + 1) % n]
            new.append(a)
            ab = _vsub(b, a)
            L2 = _vdot(ab, ab)
            if L2 < 1e-24:
                continue
            on = []
            for q in pts:
                t = _vdot(_vsub(q, a), ab) / L2
                if 1e-6 < t < 1 - 1e-6:
                    c = (a[0] + ab[0] * t, a[1] + ab[1] * t, a[2] + ab[2] * t)
                    if _vlen(_vsub(q, c)) < tol:
                        on.append((t, q))
            on.sort()
            last = None
            for t, q in on:
                if last is None or t - last > 1e-9:
                    new.append(q)
                    last = t
        out.append(new)
    return out


def _join_flat(faces, n, tol):
    """Joins faces lying flat together into outlines: (outers, holes), 3D loops - outers
    anticlockwise round n, holes the other way. Edges two faces share cancel out."""
    allpts = [q for fd in faces for lp in [fd['pts']] + fd['holes'] for q in lp]
    key = lambda q: (round(q[0] / tol), round(q[1] / tol), round(q[2] / tol))
    pt, edges = {}, {}

    def add_loop(loop, ccw):
        if (_vdot(_newell(loop), n) > 0) != ccw:
            loop = list(reversed(loop))
        ks = [key(q) for q in loop]
        for q, k in zip(loop, ks):
            pt.setdefault(k, q)
        for i in range(len(ks)):
            e = (ks[i], ks[(i + 1) % len(ks)])
            if e[0] != e[1]:
                edges[e] = edges.get(e, 0) + 1
    for fd in faces:
        loops = _split_at([fd['pts']] + fd['holes'], allpts, tol)
        add_loop(loops[0], True)
        for h in loops[1:]:
            add_loop(h, False)
    for e in list(edges):
        r = (e[1], e[0])
        if e in edges and r in edges:
            c = min(edges[e], edges[r])
            edges[e] -= c
            edges[r] -= c
    nxt = {}
    for (a, b), c in edges.items():
        for _ in range(c):
            nxt.setdefault(a, []).append(b)
    loops, guard = [], 0
    while nxt and guard < 200000:
        a0 = next(iter(nxt))
        loop, a = [a0], a0
        while guard < 200000:
            guard += 1
            bs = nxt.get(a)
            if not bs:
                break
            b = bs.pop()
            if not bs:
                del nxt[a]
            if b == a0:
                break
            loop.append(b)
            a = b
        if len(loop) >= 3:
            loops.append(_drop_straight([pt[k] for k in loop], tol))
    outers, holes = [], []
    for lp in loops:
        if len(lp) >= 3:
            (outers if _vdot(_newell(lp), n) > 0 else holes).append(lp)
    return outers, holes


def _drop_straight(loop, tol):
    """Takes out corners that lie on a straight line between their neighbours."""
    out = list(loop)
    changed = True
    while changed and len(out) > 3:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            ac = _vsub(c, a)
            L = _vlen(ac)
            if L < 1e-12:
                continue
            ab = _vsub(b, a)
            cr = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
            if _vlen(cr) / L < tol and 0 < _vdot(ab, ac) < L * L:
                del out[i]
                changed = True
                break
    return out


def _whole_face(faces, fd):
    """The wall's face as one: every face lying flat with it (same plane, same way round, same
    paint) joined together - building windows and doors into a wall can cut its face into
    several pieces. Returns [(outline, holes)], one for each separate piece of face."""
    n = fd['n']
    size = max(_vlen(_vsub(q, fd['pts'][0])) for q in fd['pts']) or 1.0
    tol = size * 1e-6
    same = [g for g in faces if g['area'] > 0 and _vdot(g['n'], n) > 0.9999
            and all(abs(_vdot(_vsub(q, fd['pts'][0]), n)) < tol * 10 for q in g['pts'])
            and g['attrs'] == fd['attrs']]
    if len(same) <= 1:
        return [(fd['pts'], fd['holes'])]
    try:
        outers, holes = _join_flat(same, n, tol)
    except Exception:
        return [(fd['pts'], fd['holes'])]
    if not outers:
        return [(fd['pts'], fd['holes'])]
    # each hole goes with the piece of face round it
    up = (0.0, 0.0, 1.0)
    along = _unit((up[1] * n[2] - up[2] * n[1], up[2] * n[0] - up[0] * n[2], up[0] * n[1] - up[1] * n[0]))
    flat = lambda lp: [(_vdot(q, along), q[2]) for q in lp]
    res = []
    for o in outers:
        fo = flat(o)
        mine = [h for h in holes if _pip(*flat(h)[0], fo) or _pip(*_mid2(flat(h)), fo)]
        res.append((o, mine))
    res.sort(key=lambda r: -abs(_area(flat(r[0]))))
    return res


def _mid2(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def _wall_face(faces, centre, inside=False):
    """The wall's outside face (or inside, if asked): the biggest upright face with a face the
    other way round behind it, up to a wall's thickness away. None if it isn't a wall."""
    up = (0.0, 0.0, 1.0)
    side = [fd for fd in faces if fd['area'] > 0 and abs(_vdot(fd['n'], up)) < 0.05]
    if not side:
        return None
    side.sort(key=lambda fd: -fd['area'])
    size = max(_vlen(_vsub(q, side[0]['pts'][0])) for q in side[0]['pts']) or 1.0
    wall_max = _WALL_MAX * (1.0 if size < 50.0 else 1000.0)
    best = None
    for a in side[:12]:
        for b in side:
            if b is a or _vdot(a['n'], b['n']) > -0.995:
                continue
            d = _vdot(_vsub(a['pts'][0], b['pts'][0]), a['n'])
            if not (0.0 < d <= wall_max):
                continue
            score = min(a['area'], b['area'])
            if best is None or score > best[0]:
                best = (score, a, b, d)
        if best is not None:
            break
    if best is None:
        return None
    _s, a, b, t = best
    outward = _vdot(a['n'], _vsub(_mid(a['pts']), centre)) >= 0
    if outward == bool(inside):
        a, b = b, a
    return a, t


# set on a group by another plugin (3D Bridges & Arches): which way its outside faces, or that it's
# not a wall at all - so the walling goes on the right side even where the middle of the model
# would say otherwise (a splayed wing wall, the inner half of a wall built in two halves)
OUTSIDE_KEY = "ed3d_outside"
NOT_WALL_KEY = "ed3d_not_wall"


def _brick_hint(g):
    """'skip' for a piece marked as not a wall, the outside direction (x, y, z) if one is marked,
    else None."""
    ext = getattr(g, 'ext', None)
    if not isinstance(ext, dict):
        return None
    if ext.get(NOT_WALL_KEY):
        return 'skip'
    d = ext.get(OUTSIDE_KEY)
    try:
        d = tuple(float(c) for c in d)[:3]
        return d if len(d) == 3 and any(abs(c) > 1e-9 for c in d) else None
    except Exception:
        return None


def _brick_records(scene):
    """Walling already made by this plugin: [(centre, normal, size)] - plus the boxes round older
    walling made before it was recorded, as [(lo, hi)]."""
    recs, boxes = [], []
    for top in _items(getattr(scene, 'groups', None)):
        for g, m in _placements(top):
            ext = getattr(g, 'ext', None)
            rec = ext.get(REC_KEY) if isinstance(ext, dict) else None
            if isinstance(rec, dict) and rec.get('at'):
                recs.append((tuple(rec['at']), tuple(rec.get('n') or (0, 0, 0)), float(rec.get('size') or 1.0)))
                continue
            name = str(getattr(g, 'name', '') or '')
            if name.startswith("3D Brick & Block Work") or name.startswith("3D Stone Work"):
                pts = []
                for g2, m2 in _placements(g):
                    for f in _items(getattr(getattr(g2, 'mesh', None), 'faces', None)):
                        for v in _items(getattr(f, 'vertices', None)):
                            q = _pos3(v)
                            if q is not None:
                                pts.append(_wmap(m2, q))
                if pts:
                    boxes.append((tuple(min(q[i] for q in pts) for i in range(3)),
                                  tuple(max(q[i] for q in pts) for i in range(3))))
    return recs, boxes


def _is_ours(g):
    """Walling made by this plugin, or a Subframe (its posts, lintels and braces are never walls)."""
    ext = getattr(g, 'ext', None)
    if isinstance(ext, dict) and REC_KEY in ext:
        return True
    name = str(getattr(g, 'name', '') or '')
    return name.startswith(("3D Brick & Block Work", "3D Stone Work", "Rubble pile", "Subframe",
                            "Glazing frames"))


def _has_walling(fd, recs, boxes):
    c = _mid(fd['pts'])
    size = max(_vlen(_vsub(q, fd['pts'][0])) for q in fd['pts']) or 1.0
    tol = size * 2e-4
    for at, n, _sz in recs:
        if _vlen(_vsub(at, c)) <= tol * 5 and _vdot(n, fd['n']) > 0.99:
            return True
    for lo, hi in boxes:
        if all(lo[i] - tol <= c[i] <= hi[i] + tol for i in range(3)):
            return True
    return False


def find_building_walls(scene, inside_walls=False, inside_faces=False):
    """The walls in the selected building or groups (the whole model if nothing is selected):
    [dict(name, face (WorldFace), group, bricked, length, height, openings)], and how many
    groups were skipped (not walls)."""
    sel = _items(getattr(scene, 'selection', None))
    picked = [e for e in sel if getattr(e, 'mesh', None) is not None or _kids(e)]
    tops = _items(getattr(scene, 'groups', None))
    if picked:
        def in_tree(t, g):
            return any(x is g for x, _ in _placements(t))
        tops = [t for t in tops if any(in_tree(t, g) for g in picked)]
    places, order = {}, []
    for t in tops:
        for g, m in _placements(t):
            if id(g) not in places:
                places[id(g)] = (g, m)
                order.append(id(g))
    parents = {}                          # the names of the groups each group is inside

    def _walk_names(g, above, depth=0):
        if depth > 40:
            return
        for c in _kids(g):
            parents[id(c)] = above + [str(getattr(g, 'name', '') or '')]
            _walk_names(c, parents[id(c)], depth + 1)
    for t in tops:
        _walk_names(t, [])
    if picked:
        want = set()
        for pg in picked:
            for g, _m in _placements(pg):
                want.add(id(g))
        order = [k for k in order if k in want]
    # the middle of the building(s), to tell the outside of a wall from the inside
    allp = []
    for k in order:
        g, m = places[k]
        for f in _items(getattr(getattr(g, 'mesh', None), 'faces', None)):
            for v in _items(getattr(f, 'vertices', None)):
                q = _pos3(v)
                if q is not None:
                    allp.append(_wmap(m, q))
    centre = _mid(allp) if allp else (0.0, 0.0, 0.0)
    recs, boxes = _brick_records(scene)
    ours = set()                          # walling, rubble piles ... made by this plugin: never walls
    for k in order:
        g, _m = places[k]
        if _is_ours(g):
            ours.update(id(x) for x, _ in _placements(g))
    out, skipped = [], 0
    for k in order:
        if k in ours:
            continue
        g, m = places[k]
        mesh = getattr(g, 'mesh', None)
        if mesh is None or not _items(getattr(mesh, 'faces', None)):
            continue
        hint = _brick_hint(g)
        if hint == 'skip':
            continue                          # marked as not a wall by the plugin that made it
        name = str(getattr(g, 'name', '') or 'Wall')
        last = name.lower().split(" - ")[-1]
        if any(w_ in nm_.lower() for nm_ in [name] + parents.get(k, []) for w_ in _NEVER_WALLS):
            continue
        if "inside wall" in last:
            if not inside_walls:
                continue
        elif any(w_ in last for w_ in _NOT_WALLS):
            continue
        faces = _world_faces(mesh, m)
        if hint:
            # the outside this piece is marked with: a 'middle' far behind it that way
            mid_ = _mid([q for fd_ in faces for q in fd_['pts']])
            got = _wall_face(faces, tuple(mid_[i] - hint[i] * 1e6 for i in range(3)), inside_faces)
        else:
            got = _wall_face(faces, centre, inside_faces)
        if got is None:
            skipped += 1
            continue
        fd, t = got
        pieces = _whole_face(faces, fd)
        wf = WorldFace(pieces[0][0], pieces[0][1], fd['obj'], mesh)
        wf.more = [WorldFace(o, h, fd['obj'], mesh) for o, h in pieces[1:]]
        inv = _inverse(m)
        if m is not None and inv is None:
            inv = False                       # can't be turned back: walling goes in a group of its own
        for x_ in [wf] + wf.more:
            x_.into = (mesh, inv)
        n_ = fd['n']
        upd = (0.0, 0.0, 1.0)
        along = _unit((upd[1] * n_[2] - upd[2] * n_[1], upd[2] * n_[0] - upd[0] * n_[2],
                       upd[0] * n_[1] - upd[1] * n_[0]))
        xs = [_vdot(q, along) for q in pieces[0][0]]
        zs = [q[2] for q in pieces[0][0]]
        k_ = 1000.0 if max(max(xs) - min(xs), max(zs) - min(zs)) < 50.0 else 1.0
        n_notch = len(outline_notches([(x, z) for x, z in zip(xs, zs)]))
        out.append({'name': name, 'face': wf, 'group': g, 'fd': fd,
                    'bricked': _mesh_has_walling(mesh) or _has_walling(fd, recs, boxes),
                    'length': (max(xs) - min(xs)) * k_, 'height': (max(zs) - min(zs)) * k_,
                    'openings': len(pieces[0][1]) + n_notch})
    return out, skipped


# ---------------------------------------------------------------------------
# Walling materials: brick and block, stone, dry-stone and Welsh slate
# ---------------------------------------------------------------------------
MATERIALS = [
    ('brick', "Brick or block (bonded)"),
    ('ashlar', "Stone - coursed ashlar"),
    ('rubble', "Stone - random rubble"),
    ('drystone', "Dry-stone walling"),
    ('slate', "Welsh slate walling"),
]
MATERIAL_NAMES = dict(MATERIALS)

# the sizes a material starts with when you pick it (mm)
MATERIAL_SIZES = {
    'brick': {'length': 215.0, 'height': 65.0, 'depth': 20.0, 'joint': 10.0, 'header_len': 102.5,
              'var': 0.0, 'relief': 0.0, 'round': 0.0},
    'ashlar': {'length': 600.0, 'height': 300.0, 'depth': 30.0, 'joint': 6.0,
               'var': 35.0, 'relief': 3.0, 'round': 5.0},
    'rubble': {'length': 380.0, 'height': 240.0, 'depth': 35.0, 'joint': 15.0,
               'var': 45.0, 'relief': 10.0, 'round': 30.0},
    'drystone': {'length': 400.0, 'height': 110.0, 'depth': 40.0, 'joint': 8.0,
                 'var': 50.0, 'relief': 15.0, 'round': 15.0},
    'slate': {'length': 380.0, 'height': 45.0, 'depth': 25.0, 'joint': 5.0,
              'var': 55.0, 'relief': 8.0, 'round': 4.0},
}

COPINGS = [
    ('slab', "Stone slabs"),
    ('saddle', "Saddleback stones (rounded top)"),
    ('stepped', "Saddleback stones (stepped top)"),
    ('brick_edge', "Bricks on edge"),
    ('cock_hen', "Cock and hen (upright stones)"),
    ('slate_up', "Upright slates"),
]

PILE_SHAPES = [
    ('heap', "Round heap"),
    ('long', "Long heap"),
    ('face', "Fill the selected face"),
]

# every size in mm (turned into metres for a wall drawn in metres)
LENGTH_KEYS = ('length', 'height', 'depth', 'joint', 'min_frag', 'header_len', 'soldier_len',
               'relief', 'round', 'q_long', 'q_short', 'q_h', 'q_proud', 'c_h', 'c_len', 'c_over',
               'ruin_depth', 'hole_size', 'foot_w', 'backing', 'pile_len', 'pile_wid', 'pile_h',
               'kick_mm', 'spall_mm', 'hole_gap', 'worn_mm', 'plank_len', 'plank_w', 'plank_t',
               'barrel_d', 'barrel_h', 'crate_size')


def _ccw(poly):
    return poly if _area(poly) >= 0 else poly[::-1]


def _centroid(poly):
    a = _area(poly)
    if abs(a) < 1e-12:
        n = float(len(poly))
        return (sum(p[0] for p in poly) / n, sum(p[1] for p in poly) / n)
    cx = cy = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        c = x1 * y2 - x2 * y1
        cx += (x1 + x2) * c
        cy += (y1 + y2) * c
    return (cx / (6 * a), cy / (6 * a))


def _halfplane(poly, nx, ny, c):
    """The part of a polygon where nx*x + ny*y <= c."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        fa = nx * a[0] + ny * a[1] - c
        fb = nx * b[0] + ny * b[1] - c
        if fa <= 0:
            out.append(a)
        if (fa <= 0) != (fb <= 0):
            t = fa / (fa - fb)
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    return out


def _round_corners(poly, r, passes=1):
    """Knocks the corners off a stone, so it looks worked or worn rather than sawn."""
    if r <= 0 or len(poly) < 3:
        return poly
    for k in range(passes):
        rr = r / (2.0 ** k) if k else r
        out = []
        n = len(poly)
        for i in range(n):
            a, v, b = poly[i - 1], poly[i], poly[(i + 1) % n]
            la = math.hypot(a[0] - v[0], a[1] - v[1])
            lb = math.hypot(b[0] - v[0], b[1] - v[1])
            if la < 1e-12 or lb < 1e-12:
                out.append(v)
                continue
            da = min(rr, 0.3 * la)
            db = min(rr, 0.3 * lb)
            out.append((v[0] + (a[0] - v[0]) * da / la, v[1] + (a[1] - v[1]) * da / la))
            out.append((v[0] + (b[0] - v[0]) * db / lb, v[1] + (b[1] - v[1]) * db / lb))
        poly = out
    return poly


# ---------------- stone layouts (all give polygons over a W x H panel) ----------------
def ashlar_layout(W, H, A, B, J, var, rng):
    """Coursed ashlar: dressed blocks in level courses, lengths (and a little the course
    heights) varying, every joint kept clear of the joints in the course below."""
    out = []
    prev = []
    y = 0.0
    while y < H:
        h = B * (1.0 + 0.4 * var * (2 * rng.random() - 1))
        h = max(h, B * 0.4)
        cw = min(h, H - y)
        x = -rng.random() * A
        joints = []
        while x < W:
            L = A
            for _ in range(10):
                L = max(A * 0.35, A * (1.0 + var * (2 * rng.random() - 1)))
                jx = x + L + J / 2.0
                if all(abs(jx - q) > 0.18 * A for q in prev):
                    break
            out.append([(x, y), (x + L, y), (x + L, y + cw), (x, y + cw)])
            joints.append(x + L + J / 2.0)
            x += L + J
        prev = joints
        y += h + J
    return out


def rubble_layout(W, H, A, B, J, var, rng):
    """Random rubble: irregular stones of all sizes, no courses. Each stone is the patch
    of wall nearer its own seed point than any other (stretched so the stones lie
    longways), shrunk by half a joint all round."""
    jit = 0.15 + 0.3 * var
    pts = {}
    nx = int(W / A) + 3
    ny = int(H / B) + 3
    for j in range(-1, ny):
        for i in range(-1, nx):
            if rng.random() < 0.28 * var:          # missing seeds make the bigger stones
                continue
            px = (i + 0.5 + 0.5 * (j % 2) + jit * (2 * rng.random() - 1)) * A
            py = (j + 0.5 + jit * (2 * rng.random() - 1)) * B
            pts[(i, j)] = (px, py)
    out = []
    for (i, j), (px, py) in pts.items():
        cell = [(px - 2.5 * A, py - 2.5 * B), (px + 2.5 * A, py - 2.5 * B),
                (px + 2.5 * A, py + 2.5 * B), (px - 2.5 * A, py + 2.5 * B)]
        for dj in range(-3, 4):
            for di in range(-3, 4):
                q = pts.get((i + di, j + dj))
                if q is None or (di == 0 and dj == 0):
                    continue
                # the bisector, worked out with x in stone lengths and y in stone heights
                a = 2 * (q[0] - px) / (A * A)
                b = 2 * (q[1] - py) / (B * B)
                c = (q[0] ** 2 - px ** 2) / (A * A) + (q[1] ** 2 - py ** 2) / (B * B)
                L = math.hypot(a, b)
                if L < 1e-15:
                    continue
                cell = _halfplane(cell, a, b, c - L * J / 2.0)
                if len(cell) < 3:
                    break
            if len(cell) < 3:
                break
        if len(cell) >= 3 and abs(_area(cell)) > A * B * 0.02:
            bx = _bbox(cell)
            if bx[1] < 0 or bx[0] > W or bx[3] < 0 or bx[2] > H:
                continue
            out.append(_ccw(cell))
    return out


def course_stones_layout(W, H, A, B, J, var, rng, wobble=0.12, slant=0.3):
    """Dry-stone and slate: flat stones in rough courses. The stones' ends lean one way or
    the other (both stones share the slanted joint), and their tops and bottoms dip a
    little, leaving the dark gaps of a wall laid without mortar."""
    out = []
    y = 0.0
    while y < H:
        h = max(B * 0.35, B * (1.0 + 0.6 * var * (2 * rng.random() - 1)))
        cw = min(h, H - y)
        x = -rng.random() * A
        ends = []
        while x < W + A:
            ends.append((x, slant * cw * (2 * rng.random() - 1)))
            x += max(A * 0.3, A * (1.0 + var * (2 * rng.random() - 1))) + J
        for k in range(len(ends) - 1):
            (xa, sa), (xb, sb) = ends[k], ends[k + 1]
            # the joint line at each end leans by s across the course
            l_b, l_t = xa + sa / 2.0 + J / 2.0, xa - sa / 2.0 + J / 2.0
            r_b, r_t = xb + sb / 2.0 - J / 2.0, xb - sb / 2.0 - J / 2.0
            if min(r_b - l_b, r_t - l_t) < J:
                continue
            d1 = rng.random() * wobble * cw
            d2 = rng.random() * wobble * cw
            d3 = rng.random() * wobble * cw
            d4 = rng.random() * wobble * cw
            out.append([(l_b, y + d1), (r_b, y + d2), (r_t, y + cw - d3), (l_t, y + cw - d4)])
        y += h + J * 0.6
    return out


# ---------------- quoins, opening dressings and copings ----------------
def _rect(x1, y1, x2, y2):
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


def quoin_layout(outline, H, p, left=True, right=True):
    """Quoins up the ends of the wall: long and short faces in turn, the long face
    on the other end at the same course, as at a real corner."""
    qh, J = p['q_h'], p['joint']
    units, excl = [], []
    # lined up with the walls below (courses run on through the floors): start part way through one
    base = p.get('_course_base', 0.0) if p.get('q_courses') else 0.0
    qs = qh + J
    k, y = 0, 0.0
    if base and qs > 0:
        k = int(math.floor(base / qs + 1e-6))
        y = -(base - k * qs)
        if y <= -qs + 1e-6 * qs or y > -1e-6 * qs:
            y = 0.0
    first = None
    while y < H - J and qh > 0:
        top = min(y + qh, H)
        if top <= J * 0.5:
            y = top + J
            k += 1
            continue
        y = max(y, 0.0)
        sp = _span(outline, (y + top) / 2.0)
        if sp:
            xl, xr = sp
            lo = [s for s in (_span(outline, y + 1e-6 * qh), _span(outline, top - 1e-6 * qh)) if s]
            if first is None:
                first = (xl, xr)
            tol = max(J, qh * 0.05)
            # the quoins stop where the end of the wall stops being upright (at the eaves of a gable)
            if any(abs(s[0] - first[0]) > tol for s in lo + [sp]):
                left = False
            if any(abs(s[1] - first[1]) > tol for s in lo + [sp]):
                right = False
            if not (left or right):
                break
            for side, on in (('l', left), ('r', right)):
                if not on:
                    continue
                long_ = (k % 2 == 0) == (side == 'l')
                L = p['q_long'] if long_ else p['q_short']
                if side == 'l':
                    units.append(_rect(xl, y, xl + L, top))
                    excl.append(_rect(xl - J, y - 1e-6, xl + L + J, top + J))
                else:
                    units.append(_rect(xr - L, y, xr, top))
                    excl.append(_rect(xr - L - J, y - 1e-6, xr + J, top + J))
        y = top + J
        k += 1
    return units, excl


def opening_dressings(hole, p):
    """Quoins up both sides of an opening, a stone head over it and a sill under it.
    Returns (quoins, heads, sills, exclusions)."""
    J, qh = p['joint'], p['q_h']
    x0, x1, y0, y1 = _bbox(hole)
    quo, heads, sills, excl = [], [], [], []
    if p.get('q_open') and qh > 0:
        k = 0
        y = y0
        while y < y1 - J * 0.5:
            top = min(y + qh, y1)
            Ll = p['q_long'] if k % 2 == 0 else p['q_short']
            Lr = p['q_short'] if k % 2 == 0 else p['q_long']
            quo.append(_rect(x0 - Ll, y, x0, top))
            quo.append(_rect(x1, y, x1 + Lr, top))
            excl.append(_rect(x0 - Ll - J, y - J, x0, top + J))
            excl.append(_rect(x1, y - J, x1 + Lr + J, top + J))
            y = top + J
            k += 1
    if p.get('heads'):
        ext = p['q_short'] if p.get('q_open') else min(p['q_short'], 0.25 * (x1 - x0) + J)
        heads.append(_rect(x0 - ext, y1, x1 + ext, y1 + qh))
        excl.append(_rect(x0 - ext - J, y1 - J, x1 + ext + J, y1 + qh + J))
    if p.get('sills') and y0 > qh * 0.6:
        sh = max(J, 0.5 * qh)
        ext = min(p['q_short'] * 0.5, 0.15 * (x1 - x0) + J)
        sills.append(_rect(x0 - ext, y0 - sh, x1 + ext, y0))
        excl.append(_rect(x0 - ext - J, y0 - sh - J, x1 + ext + J, y0 + 1e-6))
    return quo, heads, sills, excl


def coping_layout(outline, p, rng):
    """Copings along every edge of the outline that faces upwards (the top of the wall,
    and both slopes of a gable). Returns (units [(poly, depth factor)], exclusions). A rounded
    saddleback stone is (footprint, 'round', (a, e, i, t1, t2, ch)): it's built as a curved solid.
    Bricks: on a level top the coping sits on the last whole course, so any odd bit of
    height left over is a gap at the top of the face, not a gap of cut bricks under it."""
    J = p['joint']
    style = p.get('c_style', 'slab')
    ch = p['c_h']
    if style == 'brick_edge':
        ch = p['header_len']
    units, excl = [], []
    step = p['height'] + J
    on_course = p.get('material', 'brick') == 'brick' and p.get('c_course', True) and step > 0
    n = len(outline)
    for i in range(n):
        a, b = outline[i], outline[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 1e-9:
            continue
        ex, ey = dx / L, dy / L
        ox, oy = ey, -ex                     # outward, the outline running anticlockwise
        if oy < 0.3:
            continue
        ix, iy = -ox, -oy
        drop = 0.0
        if on_course and oy > 0.999:
            # a level top: drop the coping onto the last whole course below it
            base = a[1] - ch + p.get('_course_y0', 0.0)
            k = math.floor(base / step + 1e-6)
            drop = base - k * step
            if drop < 1e-6 * step or drop > step:
                drop = 0.0
        a0 = a
        a = (a[0] + ix * drop, a[1] + iy * drop)

        def quad(t1, t2, d1, d2, lean=0.0, a=a):
            p1 = (a[0] + ex * t1, a[1] + ey * t1)
            p2 = (a[0] + ex * t2, a[1] + ey * t2)
            return [p1, p2,
                    (p2[0] + ix * d2 + ex * lean, p2[1] + iy * d2 + ey * lean),
                    (p1[0] + ix * d1 + ex * lean, p1[1] + iy * d1 + ey * lean)]
        # nothing else goes under the coping, nor in the gap left over above it
        excl.append(quad(-J, L + J, ch + 2 * J + drop, ch + 2 * J + drop, a=(a0[0] - ix * J, a0[1] - iy * J)))
        t = 0.0
        k = 0
        while t < L - J * 0.5:
            if style == 'brick_edge':
                w = p['height']
                d1 = d2 = ch
            elif style == 'cock_hen':
                w = ch * (0.32 + 0.18 * rng.random())
                hh = ch * ((0.95 + 0.05 * rng.random()) if k % 2 == 0 else (0.62 + 0.12 * rng.random()))
                d1 = hh * (0.92 + 0.08 * rng.random())
                d2 = hh * (0.92 + 0.08 * rng.random())
            elif style == 'slate_up':
                w = max(J * 2, ch * (0.07 + 0.08 * rng.random()))
                hh = ch * (0.7 + 0.3 * rng.random())
                d1, d2 = hh, hh * (0.9 + 0.1 * rng.random())
            else:
                w = p['c_len']
                d1 = d2 = ch
            t2 = min(t + w, L)
            if t2 - t < J:
                break
            lean = ch * 0.12 * (0.6 + 0.4 * rng.random()) if style == 'slate_up' else 0.0
            if style == 'saddle':
                # a truly rounded top: built as its own curved solid (rounded_coping_solid)
                units.append((_ccw(quad(t, t2, d1, d2)), 'round', (a, (ex, ey), (ix, iy), t, t2, ch)))
            elif style == 'stepped':
                # a stepped top: three bands, standing out less towards the top
                for f0, f1, fd in ((0.0, 0.22, 0.55), (0.22, 0.5, 0.85), (0.5, 1.0, 1.0)):
                    q = quad(t, t2, d1 * f1, d2 * f1)
                    q = [(q[0][0] + ix * d1 * f0, q[0][1] + iy * d1 * f0),
                         (q[1][0] + ix * d2 * f0, q[1][1] + iy * d2 * f0), q[2], q[3]]
                    units.append((_ccw(q), fd))
            else:
                units.append((_ccw(quad(t, t2, d1, d2, lean)), 1.0))
            t = t2 + J
            k += 1
    return units, excl


# ---------------- damage: the bomb-site look ----------------
def _top_at(outline, x):
    """The top of the outline above x (the wall's top, or the gable's slope)."""
    ys = []
    n = len(outline)
    for i in range(n):
        (ax, ay), (bx, by) = outline[i], outline[(i + 1) % n]
        if (ax <= x <= bx) or (bx <= x <= ax):
            if abs(bx - ax) < 1e-12:
                ys += [ay, by]
            else:
                ys.append(ay + (by - ay) * (x - ax) / (bx - ax))
    return max(ys) if ys else None


def ruin_profile(W, H, p, rng, outline=None):
    """y(x): how high the broken top of a ruined wall stands at x (measured down from
    the top of the wall there, so a gable breaks down along its slopes too)."""
    D = p['ruin_depth']
    n = max(1, int(p.get('ruin_rough', 6)))
    waves = [(rng.uniform(0.6, 1.4) * k, rng.random() * 2 * math.pi, 1.0 / k) for k in range(1, n + 1)]
    tot = sum(w[2] for w in waves)
    lo = 0.08 + 0.25 * rng.random()

    def y(x):
        s = sum(a * math.sin(2 * math.pi * f * x / max(W, 1e-9) + ph) for f, ph, a in waves) / tot
        g = 0.5 + 0.5 * s                      # 0 .. 1
        top = _top_at(outline, x) if outline else None
        return (H if top is None else top) - D * (lo + (1 - lo) * g)
    return y


def blast_holes(W, H, p, rng):
    out = []
    n = int(p.get('holes_n', 0))
    R = p['hole_size'] / 2.0
    for _ in range(n):
        r = R * (0.7 + 0.6 * rng.random())
        cx = rng.uniform(min(r, W / 2), max(W - r, W / 2))
        cy = rng.uniform(min(H * 0.12 + r, H / 2), max(H - r * 0.8, H / 2))
        m = 13
        poly = []
        for k in range(m):
            a = 2 * math.pi * k / m + rng.uniform(-0.15, 0.15)
            rr = r * (0.6 + 0.55 * rng.random())
            poly.append((cx + rr * math.cos(a) * 1.15, cy + rr * math.sin(a) * 0.9))
        out.append(poly)
    return out


def _break_unit(poly, rng, toward):
    """Snaps a unit: cuts it across with one or two rough lines, keeping the part away
    from `toward` (a direction pointing at the damage)."""
    cx, cy = _centroid(poly)
    bx = _bbox(poly)
    size = max(bx[1] - bx[0], bx[3] - bx[2])
    tx, ty = toward
    L = math.hypot(tx, ty) or 1.0
    tx, ty = tx / L, ty / L
    out = poly
    for k in range(1 + (rng.random() < 0.55)):
        a = math.atan2(ty, tx) + rng.uniform(-0.8, 0.8)
        nx, ny = math.cos(a), math.sin(a)
        s = rng.uniform(-0.12, 0.3) * size * (1.0 if k == 0 else 0.6)
        out = _halfplane(out, nx, ny, nx * cx + ny * cy + s)
        if len(out) < 3:
            return None
    if abs(_area(out)) < 0.22 * abs(_area(poly)):
        return None
    return out


def _bottom_at(outline, x):
    """The bottom of the outline below x."""
    ys = []
    n = len(outline)
    for i in range(n):
        (ax, ay), (bx, by) = outline[i], outline[(i + 1) % n]
        if (ax <= x <= bx) or (bx <= x <= ax):
            if abs(bx - ax) < 1e-12:
                ys += [ay, by]
            else:
                ys.append(ay + (by - ay) * (x - ax) / (bx - ax))
    return min(ys) if ys else None


def drop_hanging(walling, copings, fixed, opening_boxes, outline, J, unit_h):
    """Takes out units the damage has left hanging in mid-air: any bit of wall not joined
    (through its joints) to the ground, the quoins or the top of an opening, and any unit
    left dangling with nothing under it and at most one neighbour.
    Returns (walling kept, copings kept, units taken out)."""
    units = [('w', u) for u in walling] + [('c', u) for u in copings]
    if not units:
        return walling, copings, []
    boxes = [_bbox(u[0]) for _, u in units]
    g = max(1.6 * J, unit_h * 0.08, 1e-9)        # how far apart two units can be and still touch
    fboxes = [_bbox(f) for f in fixed]
    cell = max(max(b[1] - b[0] for b in boxes), max(b[3] - b[2] for b in boxes), g) * 1.01
    grid = {}
    for k, b in enumerate(boxes):
        for i in range(int(math.floor(b[0] / cell)), int(math.floor(b[1] / cell)) + 1):
            for j in range(int(math.floor(b[2] / cell)), int(math.floor(b[3] / cell)) + 1):
                grid.setdefault((i, j), []).append(k)

    def touch(a, b):
        """'below' (b holds a up), 'above', 'side' or None."""
        ox = min(a[1], b[1]) - max(a[0], b[0])
        oy = min(a[3], b[3]) - max(a[2], b[2])
        wa, wb = a[1] - a[0], b[1] - b[0]
        ha, hb = a[3] - a[2], b[3] - b[2]
        if ox >= max(0.15 * min(wa, wb), 1e-12) and oy > -g:
            if (b[2] + b[3]) < (a[2] + a[3]):
                return 'below'
            return 'above'
        if oy >= max(0.3 * min(ha, hb), 1e-12) and ox > -g:
            return 'side'
        return None

    nbrs = [dict() for _ in units]
    for k, b in enumerate(boxes):
        seen = set()
        for i in range(int(math.floor((b[0] - g) / cell)), int(math.floor((b[1] + g) / cell)) + 1):
            for j in range(int(math.floor((b[2] - g) / cell)), int(math.floor((b[3] + g) / cell)) + 1):
                for m in grid.get((i, j), ()):
                    if m != k and m not in seen:
                        seen.add(m)
                        t = touch(b, boxes[m])
                        if t:
                            nbrs[k][m] = t

    # an opening is a bridge: what's over it (on the lintel) is joined to what's beside it,
    # but it only holds anything up while there's still wall beside or under it
    n_units = len(units)
    nbrs += [dict() for _ in opening_boxes]
    reach_g = g + unit_h * 0.5
    for oi, ob in enumerate(opening_boxes):
        node = n_units + oi
        for k, b in enumerate(boxes):
            ox = min(b[1], ob[1]) - max(b[0], ob[0])
            oy = min(b[3], ob[3]) - max(b[2], ob[2])
            if ox > 0.15 * (b[1] - b[0]) and ob[3] - reach_g <= b[2] <= ob[3] + reach_g:
                nbrs[k][node] = 'below'                 # on the head
                nbrs[node][k] = 'above'
            elif oy > 0.3 * (b[3] - b[2]) and ox > -reach_g:
                nbrs[k][node] = 'side'                  # the wall beside it (not the sill below)
                if b[3] >= ob[3] - 2.5 * unit_h:      # the top of the jamb, where the head bears
                    nbrs[node][k] = 'L' if (b[0] + b[1]) < (ob[0] + ob[1]) else 'R'
                else:
                    nbrs[node][k] = 'side'

    def held(b):
        """Stood on the ground, or against a quoin."""
        xc = (b[0] + b[1]) / 2.0
        gy = _bottom_at(outline, xc)
        if gy is not None and b[2] <= gy + g:
            return True
        for f in fboxes:
            if touch(b, f):
                return True
        return False

    alive = [True] * len(nbrs)
    # 1. islands: not joined to anything that holds them up. An opening only carries its head
    #    while there's wall still standing on both sides of it (a doorway stands on the ground).
    reach = [False] * len(nbrs)
    stack = [k for k, b in enumerate(boxes) if held(b)]
    for k in stack:
        reach[k] = True
    active = set()
    while True:
        while stack:
            k = stack.pop()
            for m in nbrs[k]:
                if m >= n_units and m not in active:
                    continue
                if not reach[m]:
                    reach[m] = True
                    stack.append(m)
        for oi in range(len(opening_boxes)):
            node = n_units + oi
            if node in active:
                continue
            sides = set(t for m, t in nbrs[node].items() if t in ('L', 'R') and reach[m])
            if sides == {'L', 'R'}:
                active.add(node)
                reach[node] = True
                stack.append(node)
        if not stack:
            break
    for k in range(len(nbrs)):
        if not reach[k]:
            alive[k] = False
    # 2. danglers: nothing under them and at most one neighbour left (a few passes, so a
    #    short run of them hanging off one another goes too)
    for _ in range(4):
        changed = False
        for k in range(len(units)):
            if not alive[k] or held(boxes[k]):
                continue
            live = [t for m, t in nbrs[k].items() if alive[m] and (m < n_units or reach[m])]
            if 'below' not in live and len(live) <= 1:
                alive[k] = False
                changed = True
        if not changed:
            break
    alive = alive[:n_units]
    kw = [u for (w_, u), ok in zip(units, alive) if ok and w_ == 'w']
    kc = [u for (w_, u), ok in zip(units, alive) if ok and w_ == 'c']
    gone = [u for (w_, u), ok in zip(units, alive) if not ok]
    return kw, kc, gone


def wall_units(p, W, H, outline, holes, hole_ids, rng_seed_base=0):
    """Everything that goes on one wall, in the wall's own flat coordinates (x along,
    y up, depth out from the face). `holes` are the openings (already grown by the
    gap round openings), anticlockwise. Returns a dict:
      walling / quoins / dressings / copings: [(poly, depth, kind, shade)]
      backing: [(outer, [holes])], removed: [(cx, cy)], stats."""
    mat = p.get('material', 'brick')
    J = p['joint']
    A, B, th = p['length'], p['height'], p['depth']
    var = (p.get('var') or 0.0) / 100.0
    relief = p.get('relief') or 0.0
    rnd = p.get('round') or 0.0
    subdiv, min_frag = p['subdiv'], p['min_frag']
    to_outline = outline_clipper(outline)
    rng = random.Random(int(p.get('stone_seed', 1)) * 7919 + rng_seed_base)
    chosen = p.get('soldier_holes')
    chosen = None if chosen is None else set(chosen)

    def picked(k):
        return chosen is None or hole_ids[k] in chosen

    # teeth smaller than a third of a brick's height are smoothed over; anything bigger is cut round
    real_holes = [_smooth_hole(h, 0.33 * min(A, B)) for h in holes]

    # ---- copings, quoins and opening dressings come first: the walling fits round them
    placed = []                  # convex shapes that later pieces must keep out of
    cop_units, quo_units, dress_units = [], [], []
    excl_all = []
    cop_excl = []                # under the coping and the gap over it: quoins stop there too
    if p.get('copings'):
        cu, ce = coping_layout(outline, p, random.Random(rng.random()))
        done = []
        for item in cu:
            poly, fd = item[0], item[1]
            if fd == 'round':
                # a rounded stone is built whole (curved), not cut to the outline
                cop_units.append((poly, th + p['c_over'], 'coping', rng.random(), ('round', item[2])))
                done.append((poly, _bbox(poly), True))
                continue
            for pc in to_outline(poly):
                for piece in trim_poly(pc, done, subdiv, min_frag * 0.3):
                    cop_units.append((piece, max(th * 0.5, (th + p['c_over']) * fd), 'coping', rng.random()))
            done.append((poly, _bbox(poly), True))
        placed.extend(done)
        for q in ce:
            for part in _convex_parts(_ccw(q)):
                excl_all.append((part, _bbox(part), True))
                cop_excl.append((part, _bbox(part), True))
    q_left, q_right = p.get('quoins_l'), p.get('quoins_r')
    qp = dict(p)
    if p.get('q_courses') and mat == 'brick':
        step = B + J
        n = max(1, int(round((p['q_h'] + J) / step)))
        qp['q_h'] = n * step - J
    if (q_left or q_right) and qp['q_h'] > 0:
        qu, qe = quoin_layout(outline, H, qp, q_left, q_right)
        for poly in qu:
            for pc in to_outline(poly):
                for piece in trim_poly(pc, placed + cop_excl, subdiv, min_frag):
                    quo_units.append((piece, th + p['q_proud'], 'quoin', rng.random()))
        for q in qe:
            excl_all.append((q, _bbox(q), True))
    if p.get('q_open') or p.get('heads') or p.get('sills'):
        for k, (hole, bb, cv) in enumerate(real_holes):
            if not picked(k):
                continue
            qo, he, si, ex = opening_dressings(hole, qp)
            for kind, lst, extra in (('quoin', qo, p['q_proud']), ('head', he, p['q_proud']),
                                     ('sill', si, 2 * p['q_proud'])):
                for poly in lst:
                    for pc in to_outline(poly):
                        for piece in trim_poly(pc, placed + real_holes, subdiv, min_frag):
                            dress_units.append((piece, th + extra, kind, rng.random()))
            for poly in he + si:
                placed.append((poly, _bbox(poly), True))
            for q in ex:
                excl_all.append((q, _bbox(q), True))

    # ---- soldier courses (bricks only)
    soldier_polys = []
    field_holes = list(real_holes) + excl_all
    if p.get('soldier') and mat == 'brick':
        S = p.get('soldier_len') or A
        for k, (hole, bb, cv) in enumerate(real_holes):
            if not picked(k):
                continue
            sp, cp, ex = _soldiers(hole, B, J, S, p['corner_angle'])
            soldier_polys.extend(cp + sp)
            for q in ex:
                for part in _convex_parts(q):
                    field_holes.append((part, _bbox(part), True))

    # ---- the walling itself
    walling = []
    if mat == 'brick':
        tiny = max(J * 0.1, 1e-9)
        min_end = (p.get('min_end_pct') or 0.0) / 100.0 * A if p.get('even_ends', True) else 0.0
        runs = run_finder(outline, [h for h, _, _ in field_holes]) if min_end > 0 else None
        bond_x0 = 0.0
        if p.get('_course_x0') is not None:
            bond_x0 = p['_course_x0']     # lined up with the walls above and below it
        elif p.get('even_ends', True) and real_holes:
            bond_x0 = min(bb[0] for _, bb, _ in real_holes) + J
        rects = bond_layout(A, B, J, p['header_len'], str(p['bond']).lower(), p['header_every'],
                            p['offset_mode'], p['offset_fixed'], p['offset_seq'], p['offset_seed'],
                            p['offset_rmax'], W, H, tiny, segments=runs, min_end=min_end, x0=bond_x0,
                            y0=p.get('_course_y0', 0.0), r0=p.get('_course_r0', 0))
        raw = [(_rect(x1, y1, x2, y2), 'header' if hd else 'brick') for x1, y1, x2, y2, hd in rects]
    else:
        if mat == 'ashlar':
            polys = ashlar_layout(W, H, A, B, J, var, rng)
            passes = 1
        elif mat == 'rubble':
            polys = rubble_layout(W, H, A, B, J, var, rng)
            passes = 2
        elif mat == 'slate':
            polys = course_stones_layout(W, H, A, B, J, var, rng, wobble=0.1, slant=0.25)
            passes = 1
        else:
            polys = course_stones_layout(W, H, A, B, J, var, rng, wobble=0.16, slant=0.45)
            passes = 2
        raw = [(_round_corners(_ccw(pl), rnd, passes), 'stone') for pl in polys]
        # stones are any shape: a concave opening is cut as convex pieces
        fh = []
        for h, bb, cv in field_holes:
            if cv:
                fh.append((h, bb, cv))
            else:
                for tri in _ear_clip(_ccw(h)):
                    fh.append((tri, _bbox(tri), True))
        field_holes = fh
    for poly, kind in raw:
        for piece in to_outline(poly):
            for pc in trim_poly(piece, field_holes, subdiv, min_frag):
                d = th
                if relief > 0 and kind == 'stone':
                    d = th + relief * (rng.random() - 0.5)
                walling.append([pc, max(d, th * 0.3), kind, rng.random()])
    for poly in soldier_polys:
        for pc in to_outline(poly):
            for piece in trim_poly(pc, real_holes + placed, subdiv, min_frag):
                walling.append([piece, th, 'soldier', rng.random()])
        placed.append((poly, _bbox(poly), True))

    # ---- weathering and damage
    drng = random.Random(int(p.get('dmg_seed', 1)) * 104729 + rng_seed_base)
    removed = []
    ycut = ruin_profile(W, H, p, drng, outline) if p.get('ruin') else None
    blasts = blast_holes(W, H, p, drng) if int(p.get('holes_n', 0)) > 0 else []
    broken_p = (p.get('broken_pct') or 0.0) / 100.0
    unit_h = B if mat == 'brick' else B * 0.8
    missing_polys = []           # units left out here and there (can go right through the backing)

    def damage(units, can_kick):
        keep = []
        for u in units:
            poly = u[0]
            cx, cy = _centroid(poly)
            gone = False
            missing = False
            snap = None
            if ycut is not None:
                lim = ycut(cx) + drng.uniform(-0.5, 0.5) * unit_h
                if cy > lim:
                    gone = True
                elif cy > lim - 1.3 * unit_h and drng.random() < broken_p:
                    snap = (0.0, 1.0)
            if not gone:
                for bl in blasts:
                    inside = sum(1 for q in poly if _pip(q[0], q[1], bl))
                    if _pip(cx, cy, bl):
                        gone = True
                        break
                    if inside:
                        if drng.random() < 0.35:
                            gone = True
                            break
                        if drng.random() < max(broken_p, 0.5):
                            bc = _centroid(bl)
                            snap = (bc[0] - cx, bc[1] - cy)
            if not gone and can_kick and drng.random() * 100.0 < (p.get('missing_pct') or 0.0):
                gone = True
                missing = True
            if gone:
                removed.append((cx, cy, u[2]))
                if missing:
                    missing_polys.append(poly)
                continue
            if snap is not None and len(u) > 4:
                snap = None                  # a rounded coping stone isn't snapped, just left
            if snap is not None:
                np_ = _break_unit(poly, drng, snap)
                if np_ is None:
                    removed.append((cx, cy, u[2]))
                    continue
                removed.append((cx, cy, 'bit'))
                u = list(u)
                u[0] = np_
            if can_kick:
                u = list(u)
                if p.get('kick') and drng.random() * 100.0 < (p.get('kick_pct') or 0.0):
                    u[1] = u[1] + p['kick_mm'] * (0.35 + 0.65 * drng.random())
                elif p.get('spall') and drng.random() * 100.0 < (p.get('spall_pct') or 0.0):
                    u[1] = max(u[1] * 0.25, u[1] - p['spall_mm'] * (0.35 + 0.65 * drng.random()))
                if p.get('worn') and drng.random() * 100.0 < (p.get('worn_pct') or 0.0):
                    # worn: corners rounded off on the face, and the face edges rounded over
                    r = (p.get('worn_mm') or 0.0) * (0.5 + 0.5 * drng.random())
                    if r > 0:
                        u[0] = _round_corners(_ccw(u[0]), r, 2)
                        u = u[:4] + [('worn', r * 0.8)]
            keep.append(tuple(u))
        return keep

    walling = damage(walling, True)
    quo_units = damage(quo_units, False)
    dress_units = damage(dress_units, False)
    cop_units = damage(cop_units, False)

    # ---- hanging units: bits of wall left in mid-air by the damage
    n_hanging = 0
    if p.get('no_hanging') and (ycut is not None or blasts or (p.get('missing_pct') or 0) > 0):
        fixed = [u[0] for u in quo_units + dress_units]
        tops = [bb for k, (h, bb, cv) in enumerate(real_holes)]
        walling, cop_units, gone_units = drop_hanging(walling, cop_units, fixed, tops, outline, J, unit_h)
        n_hanging = len(gone_units)
        for u in gone_units:
            cx, cy = _centroid(u[0])
            removed.append((cx, cy, u[2]))

    # ---- the backing sheet (follows the broken top, open where the wall is blown through)
    backing = []
    if (p.get('backing') or 0) > 0:
        bx0, bx1, by0, by1 = _bbox(outline)
        if ycut is not None:
            n = 160
            xs = [bx0 + (bx1 - bx0) * k / n for k in range(n + 1)]
            for h, bb, cv in real_holes:              # openings broken into from the top
                xs += [bb[0] + 1e-6, bb[1] - 1e-6]
            xs = sorted(set(x for x in xs if bx0 <= x <= bx1))
            top = []
            for x in xs:
                yy = ycut(x) - 0.5 * unit_h          # a little below the units' broken top
                for h, bb, cv in real_holes:
                    if bb[0] < x < bb[1] and bb[3] > ycut(x) - 1e-9:
                        yy = min(yy, bb[2])
                top.append((x, max(yy, by0 + J)))
            prof_poly = _ccw([(bx0 - 1.0, by0 - 1.0), (bx1 + 1.0, by0 - 1.0)] + top[::-1])
            # doorways: fill them in to get the plain wall shape, then cut them out again after
            eps_ = max(W, H) * 1e-7
            ol = _ccw(list(outline))
            door_cuts = [h for k, (h, bb, cv) in enumerate(real_holes) if hole_ids[k] >= NOTCH_BASE]
            if door_cuts:
                tol_ = max(W, H) * 1e-4
                up = set()
                for nt in outline_notches(outline):
                    for q in nt:
                        if q[1] > by0 + tol_:
                            up.add((round(q[0] / eps_), round(q[1] / eps_)))
                ol = [q for q in ol if (round(q[0] / eps_), round(q[1] / eps_)) not in up]
            if len(ol) >= 3 and _is_convex(ol):
                # a plain or gabled wall: cut the profile to the outline in one go
                pc = prof_poly
                for i in range(len(ol)):
                    pc = _clip_edge(pc, ol[i], ol[(i + 1) % len(ol)], True)
                    if len(pc) < 3:
                        break
                pieces = [_simplify(pc, eps_)] if len(pc) >= 3 else []
                for dc in door_cuts:
                    dc = _ccw(dc)
                    for part in ([dc] if _is_convex(dc) else _ear_clip(dc)):
                        nxt = []
                        for pc in pieces:
                            nxt.extend(_subtract_convex(pc, part))
                        pieces = nxt
                if len(pieces) > 1:
                    pieces = _merge(pieces, eps_)
            else:
                # clip the outline by each slice under the broken top, and join them up
                parts = []
                for k in range(len(top) - 1):
                    (xa, ya), (xb, yb) = top[k], top[k + 1]
                    if xb - xa < 1e-9:
                        continue
                    sl = _ccw([(xa, by0 - 1.0), (xb, by0 - 1.0), (xb, yb), (xa, ya)])
                    parts.extend(to_outline(sl))
                pieces = _merge(parts, max(W, H) * 1e-7) if parts else []
        else:
            pieces = [_ccw(list(outline))]
        # doorways are already notches in the outline, so only true holes are cut
        cut = [h for k, (h, bb, cv) in enumerate(real_holes) if hole_ids[k] < NOTCH_BASE]
        if p.get('through'):
            cut += [_ccw(b) for b in blasts]
        if p.get('miss_through') and missing_polys:
            # a missing unit leaves a hole right through, unless it runs into another hole
            m_ = max(J * 0.2, max(W, H) * 1e-5)
            taken = [(_ccw(h), _bbox(h)) for h in cut]
            for mp in missing_polys:
                mp = _ccw(mp)
                bb = _bbox(mp)
                big = _grow(mp, m_)
                clash = False
                for h, t in taken:
                    if bb[1] + m_ <= t[0] or bb[0] >= t[1] + m_ or bb[3] + m_ <= t[2] or bb[2] >= t[3] + m_:
                        continue
                    if any(_pip(q[0], q[1], h) for q in big) or any(_pip(q[0], q[1], big) for q in h) \
                            or _pip(*(_centroid(mp) + (h,))):
                        clash = True
                        break
                if not clash:
                    cut.append(mp)
                    taken.append((mp, bb))
        edge = max(J * 0.25, max(W, H) * 1e-5)     # a hole must keep clear of the sheet's edge
        eps_b = max(W, H) * 1e-7
        if p.get('through') and blasts:
            # a blast hole that breaks out through the edge of the sheet (into the broken top)
            # can't be a hole in it: it's cut out of the sheet's edge instead
            new_pieces = []
            for pc in pieces:
                pc = _ccw(pc)
                work = [pc]
                for bl in blasts:
                    bl = _ccw(bl)
                    g_ = _grow(bl, edge)
                    if all(_pip(q[0], q[1], pc) for q in g_):
                        continue                      # wholly inside: a plain hole, below
                    if not any(_pip(q[0], q[1], pc) for q in bl) and not any(_pip(q[0], q[1], bl) for q in pc):
                        continue                      # nowhere near this piece
                    nxt = []
                    for w_ in work:
                        sub = [w_]
                        for tri in _ear_clip(bl):
                            sub = [r for s_ in sub for r in _subtract_convex(s_, tri)]
                        nxt.extend(sub)
                    nxt = [x for x in nxt if len(x) >= 3 and abs(_area(x)) > eps_b * eps_b * 1e6]
                    merged = _merge(nxt, eps_b) if len(nxt) > 1 else nxt
                    if 0 < len(merged) <= 4:
                        work = merged
                new_pieces.extend(work)
            pieces = new_pieces
        # no slivers, and nothing left floating (every piece stands on the bottom of the wall)
        keep_p = []
        for pc in pieces:
            pb = _bbox(pc)
            if len(pc) < 3 or abs(_area(pc)) < (max(J, unit_h * 0.2)) ** 2 or pb[3] - pb[2] < max(J, 1e-9):
                continue
            if pb[2] > by0 + max(J, unit_h * 0.2):
                continue
            keep_p.append(pc)
        pieces = keep_p
        for pc in pieces:
            pc = _ccw(pc)
            inner = []
            for h in cut:
                hh = _ccw(h)
                if all(_pip(q[0], q[1], pc) for q in _grow(hh, edge)) and abs(_area(h)) < abs(_area(pc)):
                    gh_ = _grow(hh, edge)
                    if any(any(_pip(q[0], q[1], o) for q in gh_) or any(_pip(q[0], q[1], gh_) for q in o)
                           for o in inner):
                        continue                      # holes in one sheet mustn't run into each other
                    inner.append(hh)
            backing.append((pc, inner))

    stats = {'units': len(walling), 'quoins': len(quo_units) + len(dress_units),
             'copings': len(cop_units), 'removed': len(removed), 'hanging': n_hanging}
    return {'walling': walling, 'quoins': quo_units, 'dressings': dress_units,
            'copings': cop_units, 'backing': backing, 'removed': removed, 'stats': stats,
            'ycut': ycut, 'blasts': blasts}


# ---------------------------------------------------------------------------
# Loose pieces: rubble piles, and the rubble at the foot of a damaged wall
# ---------------------------------------------------------------------------
def _rot(yaw, tilt_axis, tilt):
    """A rotation matrix: a turn about the up axis, then a tilt about a level axis."""
    cy, sy = math.cos(yaw), math.sin(yaw)
    Rz = ((cy, -sy, 0.0), (sy, cy, 0.0), (0.0, 0.0, 1.0))
    ax, ay = math.cos(tilt_axis), math.sin(tilt_axis)
    c, s = math.cos(tilt), math.sin(tilt)
    t = 1 - c
    Rt = ((t * ax * ax + c, t * ax * ay, s * ay),
          (t * ax * ay, t * ay * ay + c, -s * ax),
          (-s * ay, s * ax, c))
    return tuple(tuple(sum(Rt[i][k] * Rz[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def _mul(R, v):
    return (R[0][0] * v[0] + R[0][1] * v[1] + R[0][2] * v[2],
            R[1][0] * v[0] + R[1][1] * v[1] + R[1][2] * v[2],
            R[2][0] * v[0] + R[2][1] * v[1] + R[2][2] * v[2])


def prism_faces(poly, z0, z1):
    """A closed solid: a polygon (anticlockwise) stood up from z0 to z1. Faces as
    lists of (x, y, z), wound so they face outwards."""
    top = [(x, y, z1) for x, y in poly]
    bot = [(x, y, z0) for x, y in poly]
    faces = [top, bot[::-1]]
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        faces.append([bot[i], bot[j], top[j], top[i]])
    return faces


def piece_shapes(p, rng, kind):
    """The 2D outline and thickness of one loose piece (centred on 0, 0)."""
    mat = p.get('material', 'brick')
    A, B = p['length'], p['height']
    E = p.get('header_len') or A / 2.0
    if kind == 'timber':
        # planks and timbers: real sizes from the Rubble pile tab, whatever the walling
        mm = p.get('_mm', 1.0)
        Lmax = p.get('plank_len') or 3200.0 * mm
        L = Lmax * rng.uniform(0.4, 1.0)
        w = (p.get('plank_w') or 225.0 * mm) * rng.uniform(0.75, 1.0)
        t = (p.get('plank_t') or 75.0 * mm) * rng.uniform(0.85, 1.15)
        return _rect(-L / 2, -w / 2, L / 2, w / 2), t
    if mat == 'brick':
        if kind == 'whole':
            return _rect(-A / 2, -E / 2, A / 2, E / 2), B
        if kind == 'bat':
            L = A * rng.uniform(0.35, 0.7)
            s = rng.uniform(-0.25, 0.25) * E
            return _ccw([(-L / 2, -E / 2), (L / 2 + s, -E / 2), (L / 2 - s, E / 2), (-L / 2, E / 2)]), B
        r = A * rng.uniform(0.15, 0.3)
    else:
        if mat == 'slate':
            r = A * rng.uniform(0.25, 0.55)
            th = B * rng.uniform(0.4, 0.9)
        else:
            r = A * rng.uniform(0.22, 0.45) * (0.6 if kind == 'bit' else 1.0)
            th = min(B * rng.uniform(0.6, 1.1), r * rng.uniform(0.45, 0.85))
        m = rng.randint(5, 8)
        poly = []
        for k in range(m):
            a = 2 * math.pi * (k + rng.uniform(-0.3, 0.3)) / m
            rr = r * rng.uniform(0.65, 1.0)
            poly.append((rr * math.cos(a) * 1.25, rr * math.sin(a) * 0.85))
        poly = _ccw(poly)
        return _round_corners(poly, r * 0.12) if mat != 'slate' else poly, th
    # brick fragments
    m = rng.randint(4, 6)
    poly = [(r * rng.uniform(0.6, 1.0) * math.cos(2 * math.pi * k / m),
             r * rng.uniform(0.6, 1.0) * math.sin(2 * math.pi * k / m)) for k in range(m)]
    return _ccw(poly), B * rng.uniform(0.6, 1.0)


def barrel_faces(p, rng):
    """An oil drum (straight, two rolling hoops) or a wooden barrel (bulging), centred on 0,
    stood up or lying on its side."""
    D, Hb = p.get('barrel_d') or 585.0, p.get('barrel_h') or 880.0
    r = D / 2.0
    m = 16
    if p.get('barrel_kind', 'drum') == 'barrel':
        rings = [(-0.5, 0.84), (-0.3, 0.95), (0.0, 1.0), (0.3, 0.95), (0.5, 0.84)]
    else:
        h1, h2 = 0.17, 0.2
        rings = [(-0.5, 1.0), (-h2, 1.0), (-h2, 1.035), (-h1, 1.035), (-h1, 1.0),
                 (h1, 1.0), (h1, 1.035), (h2, 1.035), (h2, 1.0), (0.5, 1.0)]
    ang0 = rng.uniform(0, 2 * math.pi)
    loops = [[(r * f * math.cos(ang0 + 2 * math.pi * k / m), r * f * math.sin(ang0 + 2 * math.pi * k / m), z * Hb)
              for k in range(m)] for z, f in rings]
    faces = [loops[-1], loops[0][::-1]]
    for lo, hi in zip(loops, loops[1:]):
        for k in range(m):
            j = (k + 1) % m
            faces.append([lo[k], lo[j], hi[j], hi[k]])
    if rng.random() < 0.5:                       # lying on its side
        faces = [[(q[0], q[2], -q[1]) for q in f] for f in faces]
    return faces


def crate_faces(p, rng):
    """A wooden crate or packing case, a little different in size each time."""
    s = p.get('crate_size') or 600.0
    a, b, c = s * rng.uniform(0.8, 1.2), s * rng.uniform(0.6, 1.0), s * rng.uniform(0.5, 0.9)
    return prism_faces(_rect(-a / 2, -b / 2, a / 2, b / 2), -c / 2, c / 2)


def custom_faces(p, rng):
    """Your own object (picked from the model), centred on 0, at the scale set."""
    src = p.get('_custom') or []
    k = (p.get('custom_scale') or 100.0) / 100.0 * p.get('_mm', 1.0)
    return [([(q[0] * k, q[1] * k, q[2] * k) for q in o], [[(q[0] * k, q[1] * k, q[2] * k) for q in h] for h in hs])
            for o, hs in src]


def object_faces(group, limit=20000):
    """Every face of a group or component (and the groups inside it), placed as it is in the
    model, then centred on 0 and turned into mm. Returns [(outer, [holes])]."""
    out = []

    def mp(m, q):
        v = vertex_to_vector3d(q)
        if m is not None:
            try:
                v = m.map(v)
            except Exception:
                pass
        return (v.x(), v.y(), v.z())

    def walk(g, base, depth=0):
        if depth > 30 or len(out) > limit:
            return
        x = getattr(g, 'xform', None)
        if x is not None and not hasattr(x, 'map'):
            x = None
        m = base if x is None else (x if base is None else base * x)
        mesh = getattr(g, 'mesh', None)
        for f in list(getattr(mesh, 'faces', None) or []):
            try:
                outer = [mp(m, q) for q in f.vertices]
                holes = [[mp(m, q) for q in h] for h in (getattr(f, 'holes', None) or [])]
            except Exception:
                continue
            if len(outer) >= 3:
                out.append((outer, [h for h in holes if len(h) >= 3]))
        for ch in list(getattr(g, 'children', None) or []):
            walk(ch, m, depth + 1)
    walk(group, None)
    if not out:
        return []
    pts = [q for o, _ in out for q in o]
    lo = [min(q[k] for q in pts) for k in range(3)]
    hi = [max(q[k] for q in pts) for k in range(3)]
    c = [(lo[k] + hi[k]) / 2.0 for k in range(3)]
    k = 1000.0 if max(hi[i] - lo[i] for i in range(3)) < 50.0 else 1.0   # drawn in metres
    return [([((q[0] - c[0]) * k, (q[1] - c[1]) * k, (q[2] - c[2]) * k) for q in o],
             [[((q[0] - c[0]) * k, (q[1] - c[1]) * k, (q[2] - c[2]) * k) for q in h] for h in hs])
            for o, hs in out]


def drop_pieces(p, rng, n, sample, inside, max_h, timbers=0, broken=0.4, core=None, extras=()):
    """Drops n loose pieces one at a time where sample() says, letting each one roll
    down off any piece already there that it would sit too steeply on. Returns a list
    of solids (each a list of faces) in local x, y (ground) and z (up).
    extras: [(kind, maker)] objects (barrels, crates, your own), dropped in among the later
    pieces so they sit partly buried, partly on top."""
    A, B = p['length'], p['height']
    cell = max(A * 0.45, 1e-9)
    grid = {}

    def gh(i, j):
        if (i, j) in grid:
            return grid[(i, j)]
        return core(i * cell + cell / 2, j * cell + cell / 2) if core else 0.0
    step = cell * math.tan(math.radians(38))
    solids = []
    kinds = ['timber'] * int(timbers)
    for _ in range(int(n)):
        r = rng.random()
        kinds.append('whole' if r > broken else ('bat' if r > broken * 0.45 else 'bit'))
    rng.shuffle(kinds)
    for ex in extras:
        kinds.insert(rng.randint(len(kinds) // 2, len(kinds)), ex)
    for kind in kinds:
        if isinstance(kind, tuple):
            name, maker = kind
            faces = maker(p, rng)
            if not faces:
                continue
            best = None
            for attempt in range(8):                # roll down to where it can rest; always lands
                x, y = sample()
                i, j = int(math.floor(x / cell)), int(math.floor(y / cell))
                for _ in range(12):
                    h0 = gh(i, j)
                    nb = None
                    for di in (-1, 0, 1):
                        for dj in (-1, 0, 1):
                            if (di or dj) and inside((i + di + 0.5) * cell, (j + dj + 0.5) * cell):
                                h1 = gh(i + di, j + dj)
                                if h1 < h0 - step and (nb is None or h1 < nb[0]):
                                    nb = (h1, i + di, j + dj)
                    if nb is None:
                        break
                    i, j = nb[1], nb[2]
                if best is None or gh(i, j) < best[0]:
                    best = (gh(i, j), i, j)
                if gh(i, j) <= max_h:
                    break
            base, i, j = best
            x = (i + rng.random()) * cell
            y = (j + rng.random()) * cell
            R = _rot(rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi), math.radians(rng.uniform(0, 12)))
            faces = [_map_face(f, lambda q: _mul(R, q)) for f in faces]
            zs = [q[2] for f in faces for q in _face_pts(f)]
            zmin, zmax = min(zs), max(zs)
            lift = max(base - zmin - (zmax - zmin) * 0.12, -zmin)
            faces = [_map_face(f, lambda q: (q[0] + x, q[1] + y, q[2] + lift)) for f in faces]
            solids.append((name, faces))
            top = zmax + lift
            xs = [q[0] for f in faces for q in _face_pts(f)]
            ys = [q[1] for f in faces for q in _face_pts(f)]
            for ii in range(int(math.floor(min(xs) / cell)), int(math.floor(max(xs) / cell)) + 1):
                for jj in range(int(math.floor(min(ys) / cell)), int(math.floor(max(ys) / cell)) + 1):
                    grid[(ii, jj)] = max(gh(ii, jj), base + (top - base) * 0.8)
            continue
        base = None
        for attempt in range(8):                # where it lands, if the heap isn't full there
            x, y = sample()
            i, j = int(math.floor(x / cell)), int(math.floor(y / cell))
            for _ in range(12):                 # roll down to where it can rest
                h0 = gh(i, j)
                best = None
                for di in (-1, 0, 1):
                    for dj in (-1, 0, 1):
                        if (di or dj) and inside((i + di + 0.5) * cell, (j + dj + 0.5) * cell):
                            h1 = gh(i + di, j + dj)
                            if h1 < h0 - step and (best is None or h1 < best[0]):
                                best = (h1, i + di, j + dj)
                if best is None:
                    break
                i, j = best[1], best[2]
            if gh(i, j) <= max_h:
                base = gh(i, j)
                break
        if base is None:
            continue
        x = (i + rng.random()) * cell
        y = (j + rng.random()) * cell
        poly, th = piece_shapes(p, rng, kind)
        z0, z1 = -th / 2.0, th / 2.0
        if kind in ('whole', 'bat') and rng.random() < 0.22:
            # a brick lying on its side
            poly = _rect(-_bbox(poly)[1], -th / 2, _bbox(poly)[1], th / 2)
            th2 = p.get('header_len') or A / 2
            z0, z1 = -th2 / 2.0, th2 / 2.0
        R = _rot(rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi),
                 math.radians(rng.uniform(0, 32 if kind != 'timber' else 14)))
        faces = prism_faces(poly, z0, z1)
        faces = [[_mul(R, q) for q in f] for f in faces]
        zmin = min(q[2] for f in faces for q in f)
        zmax = max(q[2] for f in faces for q in f)
        lift = base - zmin - (zmax - zmin) * 0.25
        lift = max(lift, -zmin + 0.0)         # never below the ground
        faces = [[(q[0] + x, q[1] + y, q[2] + lift) for q in f] for f in faces]
        solids.append((kind, faces))
        top = zmax + lift
        xs = [q[0] for f in faces for q in f]
        ys = [q[1] for f in faces for q in f]
        for ii in range(int(math.floor(min(xs) / cell)), int(math.floor(max(xs) / cell)) + 1):
            for jj in range(int(math.floor(min(ys) / cell)), int(math.floor(max(ys) / cell)) + 1):
                grid[(ii, jj)] = max(gh(ii, jj), base + (top - base) * 0.8)
    return solids


def _ray_radius(outline, c, ang):
    """How far from c to the outline, looking along angle ang."""
    dx, dy = math.cos(ang), math.sin(ang)
    best = None
    n = len(outline)
    for i in range(n):
        (ax, ay), (bx, by) = outline[i], outline[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        den = dx * ey - dy * ex
        if abs(den) < 1e-15:
            continue
        t = ((ax - c[0]) * ey - (ay - c[1]) * ex) / den
        s = ((ax - c[0]) * dy - (ay - c[1]) * dx) / den
        if t > 1e-9 and -1e-9 <= s <= 1 + 1e-9:
            best = t if best is None else min(best, t)
    return best or 0.0


def make_pile(p, outline=None, seed_base=0):
    """A pile of rubble: a solid core mound (optional) with loose pieces dropped over
    it. outline: the selected face in its own flat coordinates (for 'fill the face',
    and to centre the heap). Returns (core solid faces or None, [piece solids])."""
    rng = random.Random(int(p.get('pile_seed', 1)) * 31337 + seed_base)
    shape = p.get('pile_shape', 'heap')
    Hp = p['pile_h']
    if outline:
        c = _centroid(_ccw(outline))
    else:
        c = (0.0, 0.0)
    if shape == 'face' and outline:
        ol = _ccw(outline)

        def R(a):
            return _ray_radius(ol, c, a)
    else:
        if shape == 'long':
            a_, b_ = p['pile_len'] / 2.0, p['pile_wid'] / 4.0
        else:
            a_, b_ = p['pile_len'] / 2.0, p['pile_wid'] / 2.0

        def R(a):
            return 1.0 / math.sqrt((math.cos(a) / a_) ** 2 + (math.sin(a) / b_) ** 2)
    nseg = 36
    radii = [R(2 * math.pi * k / nseg) for k in range(nseg)]

    def rad_at(a):
        f = (a % (2 * math.pi)) / (2 * math.pi) * nseg
        k = int(f) % nseg
        t = f - int(f)
        return radii[k] * (1 - t) + radii[(k + 1) % nseg] * t
    bumps = [(rng.uniform(0, 2 * math.pi), rng.uniform(1, 4), rng.uniform(0.04, 0.12)) for _ in range(5)]
    core_h = Hp * 0.72 if p.get('pile_core', True) else 0.0

    def hfun(x, y):
        dx, dy = x - c[0], y - c[1]
        a = math.atan2(dy, dx)
        rr = rad_at(a)
        if rr <= 1e-9:
            return 0.0
        t = math.hypot(dx, dy) / rr
        if t >= 1:
            return 0.0
        wob = 1 + sum(am * math.sin(f * a + ph) for ph, f, am in bumps)
        return core_h * max(0.0, 1 - t * t) ** 0.85 * wob

    core = None
    if core_h > 0:
        rings = 7
        faces = []
        ring_pts = []
        for r_ in range(1, rings + 1):
            t = r_ / float(rings)
            pts = []
            for k in range(nseg):
                a = 2 * math.pi * k / nseg
                rr = radii[k] * t
                x, y = c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)
                z = hfun(x, y) if r_ < rings else 0.0
                if r_ < rings:
                    z *= 1 + 0.08 * (rng.random() - 0.5)
                pts.append((x, y, z))
            ring_pts.append(pts)
        apex = (c[0], c[1], core_h * (1 + bumps[0][2]))
        first = ring_pts[0]
        for k in range(nseg):
            faces.append([apex, first[k], first[(k + 1) % nseg]])
        for r_ in range(rings - 1):
            a_, b_ = ring_pts[r_], ring_pts[r_ + 1]
            for k in range(nseg):
                k2 = (k + 1) % nseg
                faces.append([a_[k], b_[k], b_[k2]])
                faces.append([a_[k], b_[k2], a_[k2]])
        faces.append(ring_pts[-1][::-1])
        core = faces

    def inside(x, y):
        dx, dy = x - c[0], y - c[1]
        return math.hypot(dx, dy) <= rad_at(math.atan2(dy, dx)) * 1.15

    def sample():
        for _ in range(30):
            a = rng.uniform(0, 2 * math.pi)
            t = min(1.1, abs(rng.gauss(0, 0.45)))
            rr = rad_at(a) * t
            return (c[0] + rr * math.cos(a), c[1] + rr * math.sin(a))
        return c
    extras = [('barrel', barrel_faces)] * int(p.get('pile_barrels') or 0)
    extras += [('crate', crate_faces)] * int(p.get('pile_crates') or 0)
    if p.get('_custom'):
        extras += [('custom', custom_faces)] * int(p.get('pile_custom') or 0)
    pieces = drop_pieces(p, rng, p.get('pile_n', 150), sample, inside, Hp,
                         timbers=p.get('pile_timbers', 0) if p.get('pile_timbers_on', True) else 0,
                         broken=(p.get('pile_broken', 40.0)) / 100.0,
                         core=hfun if core is not None else None, extras=extras)
    return core, pieces


def foot_rubble(p, W, removed, seed_base=0):
    """Loose bricks or stones heaped against the foot of a damaged wall, under the
    damage they fell from. Local x along the wall, y out from it, z up the wall."""
    rng = random.Random(int(p.get('dmg_seed', 1)) * 7 + 11 + seed_base)
    if not removed:
        return []
    n = int(min(500, 15 + len(removed) * (p.get('foot_amt', 50.0) / 100.0)))
    Wf = p['foot_w']
    xs = [r[0] for r in removed]

    def sample():
        x = rng.choice(xs) + rng.gauss(0, Wf * 0.4)
        x = min(max(x, 0.0), W)
        y = abs(rng.gauss(0, Wf * 0.38)) + p['depth'] * 1.2
        return (x, y)

    def inside(x, y):
        return -1e-9 <= x <= W and p['depth'] <= y <= Wf * 1.6
    return drop_pieces(p, rng, n, sample, inside, Wf * 0.9, timbers=0,
                       broken=0.55)


# ---------------------------------------------------------------------------
# Solids: what gets built, as lists of faces (outer points, [hole points])
# ---------------------------------------------------------------------------
def unit_solid(poly, z0, z1):
    return [(f, []) for f in prism_faces(_ccw(poly), z0, z1)]


def slab_with_holes(outer, holes, z0, z1):
    """A closed sheet the shape of `outer` with `holes` right through it."""
    outer = _ccw(outer)
    holes = [_ccw(h) for h in holes]
    top = [(x, y, z1) for x, y in outer]
    bot = [(x, y, z0) for x, y in outer]
    faces = [(top, [[(x, y, z1) for x, y in h[::-1]] for h in holes]),
             (bot[::-1], [[(x, y, z0) for x, y in h] for h in holes])]
    for loop, inward in [(outer, False)] + [(h, True) for h in holes]:
        lp = loop[::-1] if inward else loop
        n = len(lp)
        for i in range(n):
            j = (i + 1) % n
            a, b = lp[i], lp[j]
            faces.append(([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], []))
    return faces


def _orient_out(faces):
    """Turns every face of a convex solid to face outwards."""
    pts = [q for f in faces for q in f]
    if not pts:
        return faces
    c = [sum(q[k] for q in pts) / len(pts) for k in range(3)]
    out = []
    for f in faces:
        nx = ny = nz = 0.0
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            nx += (a[1] - b[1]) * (a[2] + b[2])
            ny += (a[2] - b[2]) * (a[0] + b[0])
            nz += (a[0] - b[0]) * (a[1] + b[1])
        fc = [sum(q[k] for q in f) / len(f) for k in range(3)]
        if nx * (fc[0] - c[0]) + ny * (fc[1] - c[1]) + nz * (fc[2] - c[2]) < 0:
            f = f[::-1]
        out.append(f)
    return out


def rounded_coping_solid(info, D, steps=10):
    """A saddleback coping stone with a truly rounded top: a curved profile (rising from the
    wall face at the top to the full depth D, then straight down the front) run along the edge."""
    a, e, i, t1, t2, ch = info
    prof = [(0.0, 0.0)]
    for k in range(steps + 1):
        r = k / float(steps)
        prof.append((0.65 * ch * r, D * max(0.1, math.sqrt(max(0.0, 1.0 - (1.0 - r) ** 2)))))
    prof += [(ch, D), (ch, 0.0)]

    def P(t, s, z):
        return (a[0] + e[0] * t + i[0] * s, a[1] + e[1] * t + i[1] * s, z)
    faces = [[P(t1, s, z) for s, z in prof], [P(t2, s, z) for s, z in prof]]
    n = len(prof)
    for k in range(n):
        (sa, za), (sb, zb) = prof[k], prof[(k + 1) % n]
        faces.append([P(t1, sa, za), P(t1, sb, zb), P(t2, sb, zb), P(t2, sa, za)])
    return [(f, []) for f in _orient_out(faces)]


def worn_unit_solid(poly, d, c):
    """A worn brick or stone: its face edges rounded off (a sloping band round the face)."""
    poly = _ccw(poly)
    x0, x1, y0, y1 = _bbox(poly)
    w, h = x1 - x0, y1 - y0
    c = min(c, 0.45 * d, 0.3 * min(w, h))
    if c <= 1e-9:
        return unit_solid(poly, 0.0, d)
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    sx, sy = max(0.2, (w - 2 * c) / w), max(0.2, (h - 2 * c) / h)
    inset = [(cx + (x - cx) * sx, cy + (y - cy) * sy) for x, y in poly]
    rings = [[(x, y, 0.0) for x, y in poly], [(x, y, d - c) for x, y in poly],
             [(x, y, d) for x, y in inset]]
    faces = [rings[2], rings[0][::-1]]
    n = len(poly)
    for lo, hi in ((rings[0], rings[1]), (rings[1], rings[2])):
        for k in range(n):
            j = (k + 1) % n
            faces.append([lo[k], lo[j], hi[j], hi[k]])
    return [(f, []) for f in faces]


def unit_faces(u, back=True):
    """The solid for one unit (poly, depth, kind, shade[, extra]): a plain block, a worn one,
    or a rounded coping stone."""
    poly, d = u[0], u[1]
    extra = u[4] if len(u) > 4 else None
    if extra and extra[0] == 'round':
        faces = rounded_coping_solid(extra[1], d)
    elif extra and extra[0] == 'worn':
        faces = worn_unit_solid(poly, d, extra[1])
    else:
        faces = unit_solid(poly, 0.0, d)
    if not back:
        faces = [f for f in faces if not all(abs(q[2]) < 1e-12 for q in f[0])]
    return faces


def _face_pts(f):
    return f[0] if isinstance(f, tuple) else f


def _map_face(f, fn):
    if isinstance(f, tuple):
        return ([fn(q) for q in f[0]], [[fn(q) for q in h] for h in f[1]])
    return [fn(q) for q in f]


def plain(solid_faces):
    return [(f[0], f[1]) if isinstance(f, tuple) else (f, []) for f in solid_faces]


# ---------------------------------------------------------------------------
# Preview: a small 3D picture, painted back to front
# ---------------------------------------------------------------------------
def _v_norm(v):
    L = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / L, v[1] / L, v[2] / L)


def _v_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _v_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def render_items(solids, view, world_up, light):
    """solids: [(faces, rgb)] or [(faces, rgb, layer)]: a lower layer is always painted
    first (the face or backing behind the walling). Returns [(pts2d, rgb, holes2d, edge)]
    in painting order."""
    d = _v_norm(view)
    right = _v_norm(_v_cross(world_up, d))
    up = _v_cross(d, right)
    L = _v_norm(light)
    out = []
    for so in solids:
        faces, rgb = so[0], so[1]
        layer = so[2] if len(so) > 2 else 1
        for outer, holes in faces:
            if len(outer) < 3:
                continue
            # the face's normal (Newell's method, works for any polygon)
            nx = ny = nz = 0.0
            for i in range(len(outer)):
                a, b = outer[i], outer[(i + 1) % len(outer)]
                nx += (a[1] - b[1]) * (a[2] + b[2])
                ny += (a[2] - b[2]) * (a[0] + b[0])
                nz += (a[0] - b[0]) * (a[1] + b[1])
            n = _v_norm((nx, ny, nz))
            if _v_dot(n, d) <= 1e-6:
                continue
            k = 0.5 + 0.6 * max(0.0, _v_dot(n, L))
            col = tuple(max(0, min(255, int(c * k))) for c in rgb)
            cz = sum(_v_dot(q, d) for q in outer) / len(outer)
            pts = [(_v_dot(q, right), -_v_dot(q, up)) for q in outer]
            hs = [[(_v_dot(q, right), -_v_dot(q, up)) for q in h] for h in holes]
            out.append((layer, cz, pts, col, hs))
    out.sort(key=lambda t: (t[0], t[1]))
    return [(pts, col, hs, True) for _, _, pts, col, hs in out]


STONE_RGB = {'ashlar': (206, 192, 160), 'rubble': (150, 145, 136), 'drystone': (146, 136, 118),
             'slate': (84, 92, 106)}
MORTAR_RGB = {'brick': (205, 200, 188), 'ashlar': (200, 196, 186), 'rubble': (190, 185, 172),
              'drystone': (58, 55, 52), 'slate': (48, 50, 56)}


def unit_colour(mat, kind, shade):
    s = shade - 0.5
    if kind in ('quoin', 'head', 'sill'):
        base = (218, 208, 182)
    elif kind == 'coping':
        base = (196, 190, 178) if mat != 'brick' else (166, 76, 52)
    elif kind == 'header':
        base = (142, 64, 44)
    elif kind in ('brick', 'soldier'):
        base = (181, 86, 60)
    elif kind == 'timber':
        base = (66, 52, 40)
    elif kind == 'barrel':
        base = ((128, 62, 38), (52, 78, 58), (70, 84, 108))[int(shade * 2.999)]
    elif kind == 'crate':
        base = (150, 116, 76)
    elif kind == 'custom':
        base = (120, 128, 140)
    elif kind == 'core':
        base = (124, 112, 100)
    else:
        base = STONE_RGB.get(mat, (150, 145, 136))
        if mat == 'rubble':        # some buff, some grey
            g = 0.5 + s
            base = (int(150 + 40 * g), int(145 + 28 * g), int(136 + 8 * g))
        elif mat == 'slate':
            base = (int(84 + 18 * s), int(90 + 10 * s), int(106 + 22 * s))
    k = 1.0 + 0.22 * s
    return tuple(max(0, min(255, int(c * k))) for c in base)


def sample_wall(v):
    """A sample gable wall for the preview, like 3D Subframe's: an arched doorway up from the bottom
    and a window, so the walling, quoins, heads, sills and copings show round them.
    Returns (W, H, outline, holes)."""
    A, B, J = v['length'], v['height'], v['joint']
    W = 12 * A + 11 * J
    if v.get('ruin') or v.get('holes_n') or v.get('foot'):
        W = max(W, 3600.0 * v.get('_mm', 1.0))      # room to show the damage
    H = 0.5 * W
    if v.get('material', 'brick') == 'brick':
        H = max(1, round(H / (B + J))) * (B + J) - J if B + J > 0 else H
    G = 0.24 * W                                     # the gable above the eaves
    outline = [(0.0, 0.0), (W, 0.0), (W, H), (W / 2.0, H + G), (0.0, H)]
    # the doorway: an arched head, cut up from the bottom of the wall
    dw, dh = 0.17 * W, 0.62 * H
    dx = 0.14 * W
    r = dw / 2.0
    door = [(dx, 0.0), (dx + dw, 0.0), (dx + dw, dh - r)]
    door += [(dx + r + r * math.cos(math.pi * k / 10.0), dh - r + r * math.sin(math.pi * k / 10.0))
             for k in range(1, 10)]
    door += [(dx, dh - r)]
    # the window: square, to the right
    ww, wh = 0.22 * W, 0.42 * H
    wx, wy = 0.6 * W, 0.3 * H
    window = [(wx, wy), (wx + ww, wy), (wx + ww, wy + wh), (wx, wy + wh)]
    return W, H + G, outline, [door, window]


def wall_preview_solids(v):
    mat = v.get('material', 'brick')
    W, H, outline, holes = sample_wall(v)
    p = dict(v)
    p['soldier_holes'] = None
    res = wall_units(p, W, H, outline, holes, list(range(len(holes))))
    solids = []
    if res['backing']:
        T = v['backing']
        for outer, inner in res['backing']:
            solids.append((slab_with_holes(outer, inner, -T, 0.0), MORTAR_RGB.get(mat, (200, 195, 185)), 0))
    elif not v.get('remove_face'):
        solids.append(([([(x, y, 0.0) for x, y in outline], [[(x, y, 0.0) for x, y in h[::-1]] for h in holes])],
                       MORTAR_RGB.get(mat, (200, 195, 185)), 0))
    for key in ('walling', 'quoins', 'dressings', 'copings'):
        for u in res[key]:
            solids.append((unit_faces(u), unit_colour(mat, u[2], u[3])))
    if v.get('foot'):
        crng = random.Random(5)
        for _kind, sol in foot_rubble(p, W, res['removed']):
            # rubble: x along, y out, z up  ->  wall: x along, y up, z out
            faces = [([(q[0], q[2], q[1]) for q in f][::-1], []) for f in sol]
            solids.append((faces, unit_colour(mat, 'brick' if mat == 'brick' else 'stone', crng.random())))
    return solids, res


def pile_preview_solids(v):
    mat = v.get('material', 'brick')
    core, pieces = make_pile(v, None)
    v['_placed'] = len(pieces)
    solids = []
    if core:
        solids.append((plain(core), unit_colour(mat, 'core', 0.5)))
    rng = random.Random(3)
    for kind, sol in pieces:
        if kind not in ('timber', 'barrel', 'crate', 'custom'):
            kind = 'brick' if mat == 'brick' else 'stone'
        solids.append((plain(sol), unit_colour(mat, kind, rng.random())))
    return solids


# ---------------------------------------------------------------------------
# The sizes drawing (letters A, B, C ... match the settings)
# ---------------------------------------------------------------------------
def sizes_drawing(v, mode='wall'):
    """Lines [(x1, y1, x2, y2, kind)] and labels [(x, y, text)], y up."""
    lines, labels = [], []

    def box(x1, y1, x2, y2, k):
        lines.extend([(x1, y1, x2, y1, k), (x2, y1, x2, y2, k), (x2, y2, x1, y2, k), (x1, y2, x1, y1, k)])

    def dim_h(x1, x2, y, t, tick):
        lines.append((x1, y, x2, y, 'dim'))
        lines.append((x1, y - tick, x1, y + tick, 'dim'))
        lines.append((x2, y - tick, x2, y + tick, 'dim'))
        labels.append(((x1 + x2) / 2.0, y + tick * 2.2, t))

    def dim_v(x, y1, y2, t, tick):
        lines.append((x, y1, x, y2, 'dim'))
        lines.append((x - tick, y1, x + tick, y1, 'dim'))
        lines.append((x - tick, y2, x + tick, y2, 'dim'))
        labels.append((x - tick * 2.6, (y1 + y2) / 2.0, t))

    if mode == 'pile':
        Lp, Wp, Hp = v['pile_len'], v['pile_wid'], v['pile_h']
        tick = max(Lp, Hp) * 0.025
        pts = [(-Lp / 2 + Lp * k / 24.0, Hp * max(0.0, 1 - (2 * k / 24.0 - 1) ** 2) ** 0.85) for k in range(25)]
        for a, b in zip(pts, pts[1:]):
            lines.append((a[0], a[1], b[0], b[1], 'unit'))
        lines.append((-Lp / 2 - tick * 4, 0, Lp / 2 + tick * 4, 0, 'ground'))
        dim_h(-Lp / 2, Lp / 2, -tick * 5, "M", tick)
        dim_v(-Lp / 2 - tick * 6, 0, Hp, "P", tick)
        # plan view beside it
        ox = Lp * 0.5 + max(Wp, Lp * 0.3) * 0.5 + tick * 16
        a_, b_ = Lp / 2.0, Wp / 2.0 if v.get('pile_shape') != 'long' else Wp / 4.0
        pl = [(ox + b_ * math.cos(2 * math.pi * k / 40), Hp / 2 + a_ * math.sin(2 * math.pi * k / 40) * 0.5)
              for k in range(41)]
        for a, b in zip(pl, pl[1:]):
            lines.append((a[0], a[1], b[0], b[1], 'unit'))
        dim_h(ox - b_, ox + b_, Hp / 2 - a_ * 0.5 - tick * 4, "N", tick)
        return lines, labels

    mat = v.get('material', 'brick')

    def cl(x, lo, hi):
        return min(max(x, lo), hi)
    # a drawing, not to scale: every size kept in a range that reads clearly
    A0 = max(v['length'], 1e-9)
    A = 1.0
    B = cl(v['height'] / A0, 0.22, 0.75)
    J = cl(v['joint'] / A0, 0.03, 0.07)
    E = cl((v.get('header_len') or A0 / 2) / A0, 0.3, 0.6)
    F = cl(v['q_long'] / A0, 1.1, 2.2)
    G = F * cl(v['q_short'] / max(v['q_long'], 1e-9), 0.35, 0.8)
    Hq = cl(v['q_h'] / A0, 2 * B + J, 1.5)
    Jc = cl(v['c_h'] / A0, 0.22, 0.6)
    K = cl(v['c_len'] / A0, 1.2, 2.4)
    if v.get('c_style') == 'brick_edge':
        Jc = E
    C, I, Lc = 0.22, 0.12, 0.14
    tick = 0.06
    rows = max(2, int(round((2 * Hq + J) / (B + J))))
    Hw = rows * (B + J) - J
    Hq = (Hw - J) / 2.0
    x0 = F + J
    Wd = x0 + 2.6 * (A + J)
    # quoins
    for k, (yb, yt) in enumerate(((0.0, Hq), (Hq + J, Hw))):
        box(0, yb, F if k == 0 else G, yt, 'quoin')
    dim_v(-tick * 2, 0.0, Hq, "H", tick)
    dim_h(0, F, -tick * 3, "F", tick)
    dim_h(0, G, Hw - tick * 2.5, "G", tick * 0.7)
    # walling
    for r in range(rows):
        yb = r * (B + J)
        x = x0 - (0.5 * (A + J) if r % 2 else 0.0)
        while x < Wd - 1e-9:
            a, b = max(x, x0), min(x + A, Wd)
            if r == 0 and b >= Wd - 1e-9 and mat == 'brick':
                a = max(a, Wd - E)
            if b - a > J * 0.5:
                box(a, yb, b, yb + B, 'unit')
            x += A + J
    dim_h(x0, x0 + A, -tick * 3, "A", tick)
    jx = x0 + A + J / 2.0
    lines.append((jx, -tick * 6.2, jx, -tick * 0.3, 'dim'))
    labels.append((jx + tick * 1.6, -tick * 6.4, "D"))
    if mat == 'brick':
        dim_h(Wd - E, Wd, -tick * 3, "E", tick * 0.7)
    dim_v(Wd + tick * 2.5, B + J, 2 * B + J, "B", tick)
    # coping
    ytop = Hw
    if v.get('copings'):
        yc = Hw + J
        ytop = yc + Jc
        style = v.get('c_style') or 'slab'
        x = 0.0
        k = 0
        while x < Wd - 1e-9:
            if style in ('slab', 'saddle', 'stepped'):
                w, hh = K, Jc
            elif style == 'brick_edge':
                w, hh = B, Jc
            else:
                w, hh = Jc * 0.4, Jc * (1.0 if k % 2 == 0 else 0.7)
            box(x, yc, min(x + w, Wd), yc + hh, 'coping')
            x += w + J
            k += 1
        if style in ('slab', 'saddle', 'stepped'):
            dim_h(0, min(K, Wd), ytop + tick * 1.5, "K", tick)
        dim_v(-tick * 2, yc, ytop, "J", tick)
    # an end section, drawn larger: the face, and how far each part stands out
    sx = Wd + tick * 10
    z = 2.0
    lines.append((sx, -tick * 2, sx, ytop + tick, 'face'))
    box(sx, 0, sx + (C + I) * z, Hq, 'quoin')
    box(sx, Hq + J, sx + C * z, Hw, 'unit')
    dim_h(sx, sx + C * z, Hq + J + (Hw - Hq - J) * 0.45, "C", tick * 0.6)
    dim_h(sx + C * z, sx + (C + I) * z, -tick * 3, "I", tick * 0.6)
    lines.append((sx + C * z, -tick * 2.4, sx + C * z, Hq, 'dim'))
    if v.get('copings'):
        box(sx, Hw + J, sx + (C + Lc) * z, ytop, 'coping')
        dim_h(sx + C * z, sx + (C + Lc) * z, ytop + tick * 1.5, "L", tick * 0.6)
    return lines, labels


class StudioPreview(QWidget):
    """The 3D preview, or the lettered sizes drawing (mode 'sizes')."""

    def __init__(self, mode='3d', parent=None):
        super().__init__(parent)
        self.setMinimumSize(340, 300)
        self.mode = mode
        self.what = 'wall'
        self.v = None
        self.items = []
        self.caption = ""
        self.msg = ""

    def set_values(self, v, what='wall'):
        self.v = dict(v)
        self.what = what
        self.msg = ""
        if self.mode == '3d':
            try:
                if what == 'pile':
                    solids = pile_preview_solids(self.v)
                    self.items = render_items(solids, (-0.55, -1.0, 0.8), (0, 0, 1), (-0.4, -0.5, 1.0))
                    self.caption = "Rubble pile - %d pieces" % self.v.get('_placed', 0)
                else:
                    solids, res = wall_preview_solids(self.v)
                    self.items = render_items(solids, (-0.2, 0.14, 1.0), (0, 1, 0), (-0.5, 0.6, 0.65))
                    st = res['stats']
                    mat = self.v.get('material')
                    self.caption = "%d units on this sample wall - %.0f x %.0f mm %s" % (
                        st['units'] + st['quoins'] + st['copings'], self.v['length'], self.v['height'],
                        "bricks" if mat == 'brick' else MATERIAL_NAMES.get(mat, "stones").split(" (")[0].lower())
                    if st['removed']:
                        self.caption += ", %d knocked out" % st['removed']
            except Exception as e:
                self.items, self.msg = [], "No preview: %s" % e
        self.update()

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen, QPainterPath, QFont
        from PySide6.QtCore import QPointF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(238, 238, 234))
        w, h = self.width() - 16, self.height() - 16
        if self.mode == '3d':
            if not self.items:
                p.drawText(self.rect(), Qt.AlignCenter, self.msg or "No preview")
                p.end()
                return
            h_cap = 18
            xs = [x for it in self.items for x, _ in it[0]]
            ys = [y for it in self.items for _, y in it[0]]
            sc = min(w / ((max(xs) - min(xs)) or 1), (h - h_cap) / ((max(ys) - min(ys)) or 1))
            ox = 8 + (w - (max(xs) - min(xs)) * sc) / 2 - min(xs) * sc
            oy = 8 + h_cap + (h - h_cap - (max(ys) - min(ys)) * sc) / 2 - min(ys) * sc
            for pts, rgb, holes, edge in self.items:
                col = QColor(*rgb)
                p.setBrush(col)
                p.setPen(QPen(col.darker(150), 0.5))
                poly = QPolygonF([QPointF(ox + x * sc, oy + y * sc) for x, y in pts])
                if holes:
                    path = QPainterPath()
                    path.setFillRule(Qt.OddEvenFill)
                    path.addPolygon(poly)
                    path.closeSubpath()
                    for hh in holes:
                        path.addPolygon(QPolygonF([QPointF(ox + x * sc, oy + y * sc) for x, y in hh]))
                        path.closeSubpath()
                    p.drawPath(path)
                else:
                    p.drawPolygon(poly)
            f = QFont()
            f.setBold(True)
            p.setFont(f)
            p.setPen(QColor(50, 50, 50))
            p.drawText(8, 4, self.width() - 16, h_cap, Qt.AlignLeft | Qt.AlignVCenter, self.caption)
            p.end()
            return
        try:
            lines, labels = sizes_drawing(self.v or {}, self.what)
        except Exception as e:
            p.drawText(self.rect(), Qt.AlignCenter, "No drawing: %s" % e)
            p.end()
            return
        xs = [c for ln in lines for c in (ln[0], ln[2])] + [l[0] for l in labels]
        ys = [c for ln in lines for c in (ln[1], ln[3])] + [l[1] for l in labels]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        m = 14
        sc = min((w - 2 * m) / ((x1 - x0) or 1), (h - 2 * m) / ((y1 - y0) or 1))
        ox = 8 + m + (w - 2 * m - (x1 - x0) * sc) / 2
        oy = 8 + m + (h - 2 * m - (y1 - y0) * sc) / 2

        def P(x, y):
            return QPointF(ox + (x - x0) * sc, oy + (y1 - y) * sc)
        pens = {'unit': QPen(QColor(160, 72, 48), 1.4), 'quoin': QPen(QColor(150, 130, 90), 1.6),
                'coping': QPen(QColor(100, 100, 110), 1.6), 'face': QPen(QColor(90, 90, 90), 2.0),
                'ground': QPen(QColor(120, 120, 120), 1.5), 'dim': QPen(QColor(30, 90, 180), 1.0)}
        for x_a, y_a, x_b, y_b, k in lines:
            p.setPen(pens.get(k, pens['dim']))
            p.drawLine(P(x_a, y_a), P(x_b, y_b))
        f = QFont()
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(30, 90, 180))
        for x, y, t in labels:
            q = P(x, y)
            p.drawText(int(q.x()) - 10, int(q.y()) - 9, 20, 18, Qt.AlignCenter, t)
        p.end()


# ---------------------------------------------------------------------------
# Presets: one file each in Documents\IngeTrazo Presets\Brick and Block
# ---------------------------------------------------------------------------
def _safe_name(name):
    return "".join(c if c.isalnum() or c in " -_()" else "_" for c in name).strip() or "preset"


def load_presets():
    out = {}
    # the old single presets file (sizes only) - still listed, so nothing is lost
    for name, d in load_user_presets().items():
        if isinstance(d, dict):
            dd = dict(d)
            dd['_legacy'] = True
            out[name] = dd
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
    d.update({k: values[k] for k in DEFAULTS if k in values and k != 'soldier_holes'})
    with open(os.path.join(PRESET_DIR, _safe_name(name) + ".json"), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)


def delete_preset_file(name, legacy=False):
    if legacy:
        old = load_user_presets()
        if name in old:
            del old[name]
            save_user_presets(old)
        return
    path = os.path.join(PRESET_DIR, _safe_name(name) + ".json")
    if os.path.exists(path):
        os.remove(path)


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------
def _compact_combo(cb, n):
    """A drop-down list that stays narrow (about n letters wide) whatever is in it."""
    try:
        cb.setMinimumContentsLength(n)
        enum = getattr(QComboBox, 'AdjustToMinimumContentsLengthWithIcon', None)
        if enum is None:
            enum = QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        cb.setSizeAdjustPolicy(enum)
    except Exception:
        pass


def _form(page):
    fl = QFormLayout(page)
    for name, pol, grp in (('setRowWrapPolicy', 'WrapLongRows', 'RowWrapPolicy'),
                           ('setFieldGrowthPolicy', 'AllNonFixedFieldsGrow', 'FieldGrowthPolicy')):
        try:
            enum = getattr(QFormLayout, pol, None)
            if enum is None:
                enum = getattr(getattr(QFormLayout, grp), pol)
            getattr(fl, name)(enum)
        except Exception:
            pass
    fl.setHorizontalSpacing(6)
    fl.setVerticalSpacing(4)
    return fl


# presets with only these in them just change the sizes, and leave everything else alone
SIZE_PRESET_KEYS = {'material', 'length', 'height', 'depth', 'joint', 'header_len', 'min_frag'}
# kept as they are whatever preset is picked
KEEP_KEYS = {'back_faces', 'swap', 'new_group', 'hole_gap', 'subdiv', 'soldier_len', 'soldier_holes',
             'pile_shape', 'pile_len', 'pile_wid', 'pile_h', 'pile_n', 'pile_broken', 'pile_timbers',
             'pile_core', 'pile_seed', 'pile_timbers_on', 'plank_len', 'plank_w', 'plank_t',
             'pile_barrels', 'barrel_kind', 'barrel_d', 'barrel_h', 'pile_crates', 'crate_size',
             'pile_custom', 'custom_scale'}

TABS = ("Walling", "Bond", "Openings", "Quoins && copings", "Damage", "Rubble pile")

# (tab, key, label, low, high, decimals (-1 = whole number), suffix, tip)
# The letters match the Sizes drawing.
FIELDS = [
    ("Walling", 'length', "A   Length", 1.0, 20000.0, 1, " mm",
     "The length of one brick or block. Stone: the length of an average stone."),
    ("Walling", 'height', "B   Height", 1.0, 5000.0, 1, " mm",
     "The height of one brick or block. Stone: an average course (or stone) height."),
    ("Walling", 'depth', "C   Depth", 0.05, 2000.0, 2, " mm",
     "How far the bricks or stones stand out from the wall face."),
    ("Walling", 'joint', "D   Mortar joint", 0.0, 500.0, 2, " mm",
     "The gap between units. Dry-stone and slate: the gaps between stones. For printing, about "
     "your nozzle width or more."),
    ("Walling", 'header_len', "E   Header width", 1.0, 5000.0, 1, " mm",
     "Bricks: the width of a header (the end of a brick). Also used for bricks-on-edge copings."),
    ("Walling", 'var', "Size variation", 0.0, 100.0, 0, " %",
     "Stone: how much the stones vary in size. 0 = all the same."),
    ("Walling", 'relief', "Face relief", 0.0, 500.0, 1, " mm",
     "Stone: some stones stand out more than others, by up to this much in all."),
    ("Walling", 'round', "Rounded corners", 0.0, 500.0, 1, " mm",
     "Stone: how much the corners of each stone are knocked off. More for rubble, less for ashlar."),
    ("Walling", 'stone_seed', "Stone pattern no.", 0, 999999, -1, "",
     "Change this for a different pattern of stones."),
    ("Openings", 'soldier_len', "   Soldier length", 1.0, 5000.0, 1, " mm", "How tall the soldier bricks are."),
    ("Openings", 'corner_angle', "   Corner angle (deg)", 1.0, 89.0, 1, "",
     "Where the outline of an opening turns more sharply than this, it counts as a corner and gets "
     "a corner brick."),
    ("Openings", 'min_frag', "Smallest cut piece", 0.0, 2000.0, 1, " mm",
     "Cut pieces smaller than this are left out."),
    ("Openings", 'hole_gap', "Gap round openings", 0.0, 50.0, 3, " mm",
     "Units stop this far short of every opening (and the window, sill and head in it), so they "
     "don't touch: slicers get confused by faces lying exactly on top of each other. 0.01 mm is plenty."),
    ("Openings", 'min_end_pct', "   Smallest end", 10.0, 90.0, 0, " %",
     "An end piece shorter than this (% of a brick) borrows length from the next brick."),
    ("Openings", 'subdiv', "Subdivisions", 1, 16, -1, "",
     "How finely openings with curved or concave edges are cut round."),
    ("Quoins && copings", 'q_long', "F   Quoin long face", 1.0, 5000.0, 1, " mm",
     "The length of the long quoin stones."),
    ("Quoins && copings", 'q_short', "G   Quoin short face", 1.0, 5000.0, 1, " mm",
     "The length of the short quoin stones, in between the long ones."),
    ("Quoins && copings", 'q_h', "H   Quoin height", 1.0, 5000.0, 1, " mm",
     "The height of each quoin stone (and of the stone heads)."),
    ("Quoins && copings", 'q_proud', "I   Quoins stand out by", 0.0, 500.0, 2, " mm",
     "How much further the quoins (and heads, and sills twice this) stand out than the walling."),
    ("Quoins && copings", 'c_h', "J   Coping height", 1.0, 5000.0, 1, " mm", "How tall the coping is."),
    ("Quoins && copings", 'c_len', "K   Coping stone length", 1.0, 10000.0, 1, " mm",
     "The length of each coping slab or saddleback stone."),
    ("Quoins && copings", 'c_over', "L   Coping overhang", 0.0, 1000.0, 2, " mm",
     "How much further the coping stands out than the walling."),
    ("Damage", 'kick_pct', "   How many", 1.0, 100.0, 0, " %", "The share of units that stick out."),
    ("Damage", 'kick_mm', "   By up to", 0.01, 100.0, 2, " mm",
     "The most a unit sticks out (each one a random amount up to this)."),
    ("Damage", 'spall_pct', "   How many ", 1.0, 100.0, 0, " %", "The share of units sunk back."),
    ("Damage", 'spall_mm', "   Sunk by up to", 0.01, 100.0, 2, " mm",
     "How far their faces are sunk back (frost-blown or spalled faces)."),
    ("Damage", 'worn_pct', "   How many  ", 1.0, 100.0, 0, " %", "The share of units worn round."),
    ("Damage", 'worn_mm', "   Worn by up to", 0.1, 200.0, 1, " mm",
     "How much the corners and face edges are rounded off (each one a random amount up to this)."),
    ("Damage", 'missing_pct', "Missing units", 0.0, 90.0, 1, " %",
     "Units left out here and there, all over the wall."),
    ("Damage", 'ruin_depth', "   Broken down by up to", 1.0, 50000.0, 0, " mm",
     "How far down from the top the wall is broken, at the deepest."),
    ("Damage", 'ruin_rough', "   Jaggedness", 1, 30, -1, "",
     "How many ups and downs along the broken top. 1 = one big dip, 12 = very ragged."),
    ("Damage", 'broken_pct', "Broken units at the edges", 0.0, 100.0, 0, " %",
     "Units along the broken top and round the holes snapped across, not just missing."),
    ("Damage", 'holes_n', "Blast holes", 0, 50, -1, "", "Ragged holes knocked through the wall."),
    ("Damage", 'hole_size', "   Hole size", 10.0, 50000.0, 0, " mm", "About how big the holes are."),
    ("Damage", 'foot_w', "   Spreads out", 10.0, 20000.0, 0, " mm",
     "How far the fallen rubble spreads out from the foot of the wall."),
    ("Damage", 'foot_amt', "   Amount", 1.0, 200.0, 0, " %",
     "How much rubble lies at the foot, against what came off the wall."),
    ("Damage", 'backing', "Backing sheet thickness", 0.0, 5000.0, 1, " mm",
     "A solid sheet behind the units, the shape of the wall but broken down at the top like the "
     "walling (and open where holes go right through). 0 = none: the units sit on the face."),
    ("Damage", 'dmg_seed', "Damage pattern no.", 0, 999999, -1, "",
     "Change this for a different pattern of damage."),
    ("Rubble pile", 'pile_len', "M   Pile length", 10.0, 100000.0, 0, " mm", "How long the heap is."),
    ("Rubble pile", 'pile_wid', "N   Pile width", 10.0, 100000.0, 0, " mm", "How wide the heap is."),
    ("Rubble pile", 'pile_h', "P   Pile height", 10.0, 50000.0, 0, " mm", "How high the heap is, at most."),
    ("Rubble pile", 'pile_n', "Loose pieces", 1, 3000, -1, "",
     "How many loose bricks or stones are dropped on the heap."),
    ("Rubble pile", 'pile_broken', "Broken pieces", 0.0, 100.0, 0, " %",
     "The share of pieces that are halves and broken bits rather than whole."),
    ("Rubble pile", 'pile_timbers', "   How many planks", 0, 200, -1, "",
     "How many planks and timbers lie in the heap."),
    ("Rubble pile", 'plank_len', "   Plank length", 10.0, 20000.0, 0, " mm",
     "The longest plank. Each one is a random length, from 40% of this up to it."),
    ("Rubble pile", 'plank_w', "   Plank width", 1.0, 2000.0, 0, " mm", "How wide the planks are."),
    ("Rubble pile", 'plank_t', "   Plank thickness", 1.0, 1000.0, 0, " mm", "How thick the planks are."),
    ("Rubble pile", 'pile_barrels', "Barrels", 0, 100, -1, "", "Barrels or oil drums in the heap."),
    ("Rubble pile", 'barrel_d', "   Barrel diameter", 10.0, 5000.0, 0, " mm",
     "Across the barrel. An oil drum is about 585 mm."),
    ("Rubble pile", 'barrel_h', "   Barrel height", 10.0, 5000.0, 0, " mm", "An oil drum is about 880 mm tall."),
    ("Rubble pile", 'pile_crates', "Crates", 0, 100, -1, "", "Wooden crates or packing cases in the heap."),
    ("Rubble pile", 'crate_size', "   Crate size", 10.0, 5000.0, 0, " mm",
     "About how big the crates are (each one a little different)."),
    ("Rubble pile", 'pile_custom', "   How many copies", 0, 100, -1, "",
     "How many copies of your own object go in the heap."),
    ("Rubble pile", 'custom_scale', "   Scale", 1.0, 1000.0, 0, " %", "100% = the size it is in the model."),
    ("Rubble pile", 'pile_seed', "Pile pattern no.", 0, 999999, -1, "",
     "Change this for a different heap."),
]


# ---------------------------------------------------------------------------
# The key: a drawing showing what each lettered size is (laid out like 3D Subframe's)
# ---------------------------------------------------------------------------
KEY_NOTES = ["A  brick or stone length", "B  brick or stone height", "C  stands out from the wall",
             "D  mortar joint", "E  header width (brick end)", "F  quoin long face", "G  quoin short face",
             "H  quoin height", "I  quoins stand out further", "J  coping height",
             "K  coping stone length", "L  coping overhang", "M  rubble pile length", "N  rubble pile width",
             "P  rubble pile height"]


class KeyDrawing(QWidget):
    """A drawing that shows what each lettered size is."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 690)

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
        from PySide6.QtCore import QPointF, QRectF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 246))
        k = min(float(self.width()) / 360.0, self.height() / 690.0)
        p.scale(k, k)
        brick, header = QColor(181, 86, 60), QColor(142, 64, 44)
        mortar, wallc = QColor(222, 214, 200), QColor(200, 196, 188)
        stone, coping = QColor(218, 208, 182), QColor(196, 190, 178)
        rubble = QColor(160, 120, 96)
        red = QColor(200, 40, 40)
        f = QFont()
        f.setBold(True)
        f.setPointSizeF(9.5)
        p.setFont(f)

        def poly(pts, col):
            p.setPen(QPen(col.darker(160), 0.8))
            p.setBrush(col)
            p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in pts]))

        def box(x, y, w, h, col):
            poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], col)

        def dim(x1, y1, x2, y2, letter, tx, ty):
            p.setPen(QPen(red, 1.1))
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            ang = math.atan2(y2 - y1, x2 - x1)
            for (x, y, a) in ((x1, y1, ang), (x2, y2, ang + math.pi)):
                for s_ in (0.45, -0.45):
                    p.drawLine(QPointF(x, y), QPointF(x + 6 * math.cos(a + s_), y + 6 * math.sin(a + s_)))
            p.setPen(red)
            p.drawText(QRectF(tx - 10, ty - 9, 20, 18), Qt.AlignCenter, letter)

        def title(x, y, text):
            p.setFont(f)
            p.setPen(QColor(60, 60, 60))
            p.drawText(QRectF(x, y, 340, 18), Qt.AlignLeft, text)

        # ---- the walling from the front: Flemish bond (stretchers and headers in turn)
        title(10, 4, "Walling from the front")
        X0, Y0, X1 = 40.0, 28.0, 340.0
        bh, jg, A_, E_ = 22.0, 6.0, 62.0, 28.0
        rows = 5
        box(X0, Y0, X1 - X0, rows * (bh + jg) - jg, mortar)
        p.save()
        p.setClipRect(QRectF(X0, Y0, X1 - X0, rows * (bh + jg)))
        for r in range(rows):
            y = Y0 + r * (bh + jg)
            x = X0 - (0.0 if r % 2 == 0 else (E_ + jg) / 2.0 + (A_ + jg) / 2.0)
            i = 0
            while x < X1:
                w = A_ if i % 2 == 0 else E_
                box(x, y, w, bh, brick if i % 2 == 0 else header)
                x += w + jg
                i += 1
        p.restore()
        # under the bottom course: stretcher A, header E; up the left end: height B, joint D
        ya = Y0 + rows * (bh + jg) - jg + 8
        dim(X0, ya, X0 + A_, ya, "A", X0 + A_ / 2.0, ya + 12)
        dim(X0 + A_ + jg, ya, X0 + A_ + jg + E_, ya, "E", X0 + A_ + jg + E_ / 2.0, ya + 12)
        dim(X0 - 8, Y0, X0 - 8, Y0 + bh, "B", X0 - 20, Y0 + bh / 2.0)
        dim(X0 - 8, Y0 + bh, X0 - 8, Y0 + bh + jg, "D", X0 - 20, Y0 + bh + jg + 6)

        # ---- the wall seen end on: walling, a quoin, the coping on top
        title(10, 188, "The wall seen end on")
        wx, wtop, wbot = 60.0, 236.0, 430.0
        box(wx, wtop, 40, wbot - wtop, wallc)              # the wall (the face the walling goes on)
        C_, I_, J_, L_ = 16.0, 10.0, 20.0, 12.0
        y = wtop
        while y < 360:                                      # bricks standing out C from the face
            box(wx - C_, y, C_, min(bh * 0.7, 360 - y), brick)
            y += bh * 0.7 + 3
        box(wx - C_ - I_, 364, C_ + I_, 30, stone)          # a quoin, standing out I past the walling
        box(wx - C_ - I_, 397, C_ + I_, 30, stone)
        box(wx - C_ - L_, wtop - J_, 40 + C_ + 2 * L_, J_, coping)    # the coping on the top
        dim(wx - C_, 300, wx, 300, "C", wx - C_ - 14, 300)
        dim(wx - C_ - I_, 412, wx - C_, 412, "I", wx - C_ - I_ / 2.0, 400 + 26)
        xj = wx + 40 + L_ + 8
        dim(xj, wtop - J_, xj, wtop, "J", xj + 12, wtop - J_ / 2.0)
        dim(wx - C_ - L_, wtop - J_ - 8, wx - C_, wtop - J_ - 8, "L", wx - C_ - L_ - 14, wtop - J_ - 8)

        # ---- a corner with quoins, and coping stones along the top
        title(150, 188, "A corner, from the front")
        cx0, cx1, ctop, cbot = 150.0, 330.0, 236.0, 430.0
        box(cx0, ctop, cx1 - cx0, cbot - ctop, mortar)
        y = ctop + 4
        r = 0
        while y + bh * 0.7 <= cbot:                         # walling behind
            x = cx0 + (0 if r % 2 == 0 else -30)
            while x < cx1:
                x0_, x1_ = max(x, cx0), min(x + 56, cx1)
                if x1_ > x0_:
                    box(x0_, y, x1_ - x0_, bh * 0.7, brick)
                x += 60
            y += bh * 0.7 + 4
            r += 1
        F_, G_, H_ = 80.0, 46.0, 34.0
        y = cbot
        i = 0
        while y - H_ >= ctop + 6:                           # quoins up the corner, long and short in turn
            w = F_ if i % 2 == 0 else G_
            box(cx1 - w, y - H_, w, H_ - 3, stone)
            y -= H_
            i += 1
        K_ = 54.0
        x = cx0 - 6
        while x < cx1 + 6:                                  # coping stones along the top
            box(x, ctop - J_, min(K_, cx1 + 6 - x), J_, coping)
            x += K_ + 3
        dim(cx1 - F_, cbot + 10, cx1, cbot + 10, "F", cx1 - F_ / 2.0, cbot + 22)
        dim(cx1 - G_, cbot - H_ - 12, cx1, cbot - H_ - 12, "G", cx1 - G_ - 12, cbot - H_ - 12)
        dim(cx1 + 14, cbot - H_, cx1 + 14, cbot, "H", cx1 + 24, cbot - H_ / 2.0)
        dim(cx0 - 6, ctop - J_ - 8, cx0 - 6 + K_, ctop - J_ - 8, "K", cx0 + K_ + 12, ctop - J_ - 8)

        # ---- the rubble pile: from above and from the side
        title(10, 452, "A rubble pile, from above and from the side")
        ex, ey, ew, eh = 30.0, 480.0, 140.0, 70.0
        p.setPen(QPen(rubble.darker(150), 0.8))
        p.setBrush(rubble)
        p.drawEllipse(QRectF(ex, ey, ew, eh))
        rng = random.Random(4)
        for _ in range(26):                                  # a few loose pieces
            a, rr = rng.random() * 2 * math.pi, math.sqrt(rng.random()) * 0.8
            px, py = ex + ew / 2 + rr * ew / 2 * math.cos(a), ey + eh / 2 + rr * eh / 2 * math.sin(a)
            box(px - 5, py - 2.5, 10, 5, brick)
        dim(ex, ey + eh + 10, ex + ew, ey + eh + 10, "M", ex + ew / 2.0, ey + eh + 22)
        dim(ex - 10, ey, ex - 10, ey + eh, "N", ex - 20, ey + eh / 2.0)
        bx0, bx1, by = 200.0, 340.0, 556.0
        mound = [(bx0, by)] + [(bx0 + (bx1 - bx0) * t / 20.0,
                                by - 62.0 * math.sin(math.pi * t / 20.0) ** 0.8) for t in range(1, 20)] + [(bx1, by)]
        poly(mound, rubble)
        for t in range(3, 18, 3):
            xx = bx0 + (bx1 - bx0) * t / 20.0
            yy = by - 62.0 * math.sin(math.pi * t / 20.0) ** 0.8
            box(xx - 5, yy - 2, 10, 5, brick)
        dim(bx1 + 8, by - 62, bx1 + 8, by, "P", bx1 + 16, by - 31)

        # ---- the notes
        f2 = QFont()
        f2.setPointSizeF(8.5)
        p.setFont(f2)
        p.setPen(QColor(60, 60, 60))
        half = (len(KEY_NOTES) + 1) // 2
        for i, t in enumerate(KEY_NOTES):
            col, row = (0, i) if i < half else (1, i - half)
            p.drawText(QRectF(10 + col * 175, 590 + row * 12.0, 175, 13), Qt.AlignLeft | Qt.AlignVCenter, t)
        p.end()


# which settings make each kind of piece - looked up by a group's name when you click on it
PIECE_KEYS = [
    ("Walling", ('length', 'height', 'depth', 'joint', 'header_len')),
    ("Quoins", ('q_long', 'q_short', 'q_h', 'q_proud')),
    ("Heads and sills", ('q_h', 'q_proud')),
    ("Coping", ('c_h', 'c_len', 'c_over')),
    ("Backing", ('backing',)),
    ("Rubble (", ('foot_w', 'foot_amt')),
    ("Loose pieces", ('pile_len', 'pile_wid', 'pile_h', 'pile_n')),
    ("Rubble core", ('pile_len', 'pile_wid', 'pile_h')),
    ("Rubble pile", ('pile_len', 'pile_wid', 'pile_h', 'pile_n')),
    ("Planks and timbers", ('plank_len', 'plank_w', 'plank_t')),
    ("Barrels", ('barrel_d', 'barrel_h')),
    ("Crates", ('crate_size',)),
]


def piece_keys(name):
    name = str(name or '')
    for word, keys in PIECE_KEYS:
        if name.startswith(word):
            return keys
    return ()


# window settings: the page you were on, your last settings, the preset order
UI_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_brick_block_studio.json")


def _ui_settings():
    try:
        with open(UI_FILE, "r", encoding="utf-8") as f_:
            d = json.load(f_)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _ui_settings_save(**kw):
    d = _ui_settings()
    d.update(kw)
    try:
        with open(UI_FILE, "w", encoding="utf-8") as f_:
            json.dump(d, f_, indent=1)
    except Exception:
        pass


INFO_TEXT = ("<b>How to use it</b><br>"
             "Select a wall face and click 'Apply to face' - the walling, quoins, copings and damage set on "
             "the pages go on it. Or select a floor or the ground and click 'Make rubble pile'.<br><br>"
             "<b>Whole building</b><br>"
             "Select the building (or nothing, for the whole model), click Find on the Whole building page, "
             "tick the walls you want and click 'Brick the ticked walls'. Plain walls start ticked; walls "
             "that already have walling start unticked. One Undo takes them all away.<br><br>"
             "<b>Openings</b><br>"
             "Openings in the face are found for you. On the Openings page, tick the ones that get a "
             "soldier course, quoins, a stone head or a sill.<br><br>"
             "<b>Clicking on walling</b><br>"
             "Click on walling, quoins or coping in the model and the sizes that made it light up here.<br><br>"
             "<b>Printing</b><br>Keep 'Closed units (with backs)' ticked so every unit is a closed solid. "
             "Sizes are real-world mm - Scale Studio takes it down to your model scale.")


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


class BrickDialog(QDialog):
    CUSTOM = "-- Custom --"

    def __init__(self, cur, openings, preselected, parent=None, tool=None, viewport=None):
        super().__init__(parent)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.tool = tool
        self.viewport = viewport
        self.wall = None           # the wall face the openings list belongs to
        self.user_presets = load_presets()
        self._busy = False
        self._sold_linked = cur.get('soldier_len') is None

        lay = QVBoxLayout(self)
        # the writing at the top - how to use it, the face picked and what the last build did - only
        # shows when the Info button (bottom of the window) is pressed; it's off each time it opens
        self.info_box = QWidget()
        ib = QVBoxLayout(self.info_box)
        ib.setContentsMargins(0, 0, 0, 0)
        self.lbl_info = QLabel(INFO_TEXT)
        self.lbl_info.setWordWrap(True)
        ib.addWidget(self.lbl_info)
        self.lbl_face = QLabel()
        self.lbl_face.setWordWrap(True)
        self.lbl_face.setStyleSheet("font-weight: bold;")
        ib.addWidget(self.lbl_face)
        self.lbl_report = QLabel()
        self.lbl_report.setWordWrap(True)
        self.lbl_report.setVisible(False)
        ib.addWidget(self.lbl_report)
        self.info_box.setVisible(False)
        lay.addWidget(self.info_box)

        # ---- the preview and key on the left, the pages beside them ----
        side = QHBoxLayout()
        lay.addLayout(side, 1)
        self.views = QTabWidget()
        self.preview = StudioPreview('3d')
        self.preview.setToolTip("A sample gable wall with a door and a window, as it will be built (or the "
                                "rubble pile, on the Rubble pile page). It changes as you change the settings.")
        self.views.addTab(self.preview, "Preview")
        from PySide6.QtWidgets import QScrollArea
        key_scroll = QScrollArea()
        key_scroll.setWidgetResizable(True)
        key_scroll.setWidget(KeyDrawing())
        self.views.addTab(key_scroll, "Key (A, B, C...)")
        self.views.setTabToolTip(0, "A sample wall (or the rubble pile) as it will be built.")
        self.views.setTabToolTip(1, "What each lettered size is.")
        side.addWidget(self.views, 1)

        self.tabs = TwoRowTabs(2)
        self.pages = {}
        for title in TABS:
            pg = QWidget()
            self.pages[title] = _form(pg)
            try:
                from PySide6.QtWidgets import QScrollArea, QFrame
                sa = QScrollArea()
                sa.setWidgetResizable(True)
                sa.setFrameShape(QFrame.NoFrame)
                sa.setWidget(pg)
                self.tabs.addTab(sa, title)
            except Exception:
                self.tabs.addTab(pg, title)
        tab_tips = ["What the wall is built of, and the sizes of the bricks, blocks or stones.",
                    "Bricks and blocks: the bond, row offsets and header courses.",
                    "Soldier courses, and how the walling is cut round windows and doors.",
                    "Quoins up the corners and round openings, stone heads and sills, and copings "
                    "along the top.",
                    "Make it old, or a bomb site: kicked-out and missing units, a broken-down top, "
                    "blast holes, rubble at the foot.",
                    "Make a heap of loose bricks or stones on the selected face."]
        for i, t in enumerate(tab_tips):
            self.tabs.setTabToolTip(i, t)
        side.addWidget(self.tabs, 1)
        self.sp = {}
        self._key_tab = {}
        F = self.pages

        def combo(items, tip):
            cb = QComboBox()
            for k, t in items:
                cb.addItem(t, k)
            cb.setToolTip(tip)
            _compact_combo(cb, 14)
            cb.currentIndexChanged.connect(self.changed)
            return cb

        def check(text, tip):
            c = QCheckBox(text)
            c.setToolTip(tip)
            c.toggled.connect(self.changed)
            return c

        def fields(tab):
            for t, key, label, lo, hi, dec, suf, tip in FIELDS:
                if t != tab:
                    continue
                if dec < 0:
                    s = QSpinBox()
                    s.setRange(int(lo), int(hi))
                else:
                    s = QDoubleSpinBox()
                    s.setDecimals(dec)
                    s.setRange(lo, hi)
                    s.setSuffix(suf)
                s.setKeyboardTracking(False)
                s.setToolTip(tip)
                lab = QLabel(label)
                lab.setToolTip(tip)
                self.sp[key] = (s, lab)
                self._key_tab[key] = tab
                s.valueChanged.connect(self.changed)
                yield key, lab, s

        self._pending = {t: list(fields(t)) for t in TABS}

        def row(tab, key):
            for k, lab, s in self._pending[tab]:
                if k == key:
                    F[tab].addRow(lab, s)
                    return

        # ---- Walling ----
        self.cb_mat = combo(MATERIALS, "Bricks or blocks in a bond, coursed ashlar, random rubble, dry-stone "
                                       "walling or Welsh slate. Picking one fills in sizes to suit it.")
        self.cb_mat.currentIndexChanged.connect(self.material_changed)
        F["Walling"].addRow("Material:", self.cb_mat)
        for k in ('length', 'height', 'depth', 'joint', 'header_len', 'var', 'relief', 'round', 'stone_seed'):
            row("Walling", k)
        self.cb_back = check("Closed units (with backs)",
                             "Gives every unit a back face so it is a closed solid. Leave this on for 3D "
                             "printing: without it the slicer sees open edges and its repair can damage "
                             "the rest of the model.")
        self.cb_swap = check("Swap axes", "Swap the wall's width and height directions.")
        self.cb_group = check("New group", "Put the walling in a new group of its own (with a group "
                                           "for each part: walling, quoins, copings, rubble, backing).")
        self.cb_join = check("Build the walling into its wall (prints as one piece)",
                             "The bricks or stones become part of the wall's own group, like windows and doors "
                             "built in - so in Scale Studio's Pieces page each wall lays flat and prints as one "
                             "piece, walling and all. They're painted with 3D Layers & Colours' colours. "
                             "Rubble at the foot stays a group of its own. Untick to put the walling in groups "
                             "of its own instead.")
        for c in (self.cb_back, self.cb_swap, self.cb_join, self.cb_group):
            F["Walling"].addRow(c)

        # ---- Bond ----
        self.cb_bond = combo([(k, l) for l, k in (("Running bond", "running"), ("Stack bond", "stack"),
                                                   ("Third bond", "third"), ("English bond", "english"),
                                                   ("Flemish bond", "flemish"))],
                             "The pattern the bricks are laid in: stretcher, English, Flemish and so on.")
        F["Bond"].addRow("Bond:", self.cb_bond)
        self.cb_off = combo([("bond", "Follow the bond"), ("fixed", "Fixed, every 2nd course"),
                             ("sequence", "Custom sequence"), ("random", "Random per course")],
                            "How far each course is moved along: as the bond says, a fixed amount every "
                            "2nd course, your own sequence, or at random.")
        F["Bond"].addRow("Row offsets:", self.cb_off)
        self.sp_ofix = QDoubleSpinBox()
        self.sp_ofix.setDecimals(3)
        self.sp_ofix.setRange(0.0, 1.0)
        self.sp_ofix.setSingleStep(0.05)
        self.sp_ofix.setToolTip("Fixed offset, as a fraction of a unit (length + joint).")
        self.le_seq = QLineEdit()
        self.le_seq.setToolTip("Fractions of a unit (length + joint), repeated down the wall. "
                               "Example: 0, 0.5, 0.25, 0.75")
        self.sp_seed = QSpinBox()
        self.sp_seed.setRange(0, 999999)
        self.sp_rmax = QDoubleSpinBox()
        self.sp_rmax.setDecimals(2)
        self.sp_rmax.setRange(0.05, 1.0)
        self.sp_rmax.setSingleStep(0.05)
        self.sp_rmax.setToolTip("The most a course is offset at random, as a fraction of a unit.")
        F["Bond"].addRow("   Fixed offset:", self.sp_ofix)
        F["Bond"].addRow("   Sequence:", self.le_seq)
        F["Bond"].addRow("   Random seed:", self.sp_seed)
        F["Bond"].addRow("   Max random offset:", self.sp_rmax)
        self.cb_head = check("Header courses", "Puts a course of headers (brick ends) in every so many courses.")
        self.sp_every = QSpinBox()
        self.sp_every.setRange(2, 50)
        self.sp_every.setToolTip("A header course every this many courses.")
        F["Bond"].addRow(self.cb_head)
        F["Bond"].addRow("   Every Nth course:", self.sp_every)
        self.cb_cground = check("Courses run on through the floors",
                                "Counts the courses from the ground (height 0), not from the bottom of each "
                                "wall, so the first floor's bricks carry straight on from the ground floor's - "
                                "no cut bricks or odd joint at the floor line, and the bond keeps going. "
                                "Untick to start each wall with a whole course at its bottom.")
        F["Bond"].addRow(self.cb_cground)
        for w_ in (self.sp_ofix, self.sp_seed, self.sp_rmax, self.sp_every):
            w_.valueChanged.connect(self.changed)
        self.le_seq.textChanged.connect(self.changed)

        # ---- Openings ----
        self.lst_open = QListWidget()
        self.lst_open.setMaximumHeight(90)
        self.lst_open.setToolTip("The openings found in this face. Tick the ones that get a soldier "
                                 "course, quoins, a stone head or a sill.")
        self.fill_openings(openings, preselected)
        self.btn_all = QPushButton("All")
        self.btn_none = QPushButton("None")
        self.btn_all.clicked.connect(lambda: self.set_all(Qt.Checked))
        self.btn_none.clicked.connect(lambda: self.set_all(Qt.Unchecked))
        pick_row = QHBoxLayout()
        pick_row.addWidget(self.btn_all)
        pick_row.addWidget(self.btn_none)
        pick_row.addStretch(1)
        pick_box = QVBoxLayout()
        pick_box.addWidget(QLabel("Openings to dress:"))
        pick_box.addWidget(self.lst_open)
        pick_box.addLayout(pick_row)
        F["Openings"].addRow(pick_box)
        self.cb_sold = check("Soldier course round openings (bricks)",
                             "Bricks stood on end round the openings ticked above.")
        F["Openings"].addRow(self.cb_sold)
        row("Openings", 'soldier_len')
        row("Openings", 'corner_angle')
        row("Openings", 'min_frag')
        row("Openings", 'hole_gap')
        self.cb_even = check("Even up the ends",
                             "Lines the bond up with the first opening (courses beside it end in a whole "
                             "brick and a half brick in turn), and where a course would still end in a thin "
                             "sliver, takes length from the next brick so neither is a sliver. No brick is "
                             "ever made longer than a standard one.")
        F["Openings"].addRow(self.cb_even)
        row("Openings", 'min_end_pct')
        row("Openings", 'subdiv')
        self.sp['soldier_len'][0].valueChanged.connect(self._sold_unlink)

        # ---- Quoins & copings ----
        Q = "Quoins && copings"
        self.cb_ql = check("Quoins at the left end", "Quoin stones up the left end of the wall.")
        self.cb_qr = check("Quoins at the right end", "Quoin stones up the right end of the wall.")
        self.cb_qo = check("Quoins round openings", "Quoin stones up both sides of the openings ticked on "
                                                    "the Openings tab.")
        self.cb_qc = check("Quoin height in whole courses (bricks)",
                           "Bricks: rounds the quoin height to whole brick courses, so the quoins line up "
                           "with the coursing.")
        for c in (self.cb_ql, self.cb_qr, self.cb_qo):
            F[Q].addRow(c)
        for k in ('q_long', 'q_short', 'q_h', 'q_proud'):
            row(Q, k)
        F[Q].addRow(self.cb_qc)
        self.cb_heads = check("Stone heads over openings", "A stone lintel over each opening ticked on the "
                                                           "Openings tab, H high.")
        self.cb_sills = check("Stone sills under openings", "A stone sill under each window ticked on the "
                                                            "Openings tab (not doors).")
        F[Q].addRow(self.cb_heads)
        F[Q].addRow(self.cb_sills)
        self.cb_cop = check("Copings along the top", "Coping along the top of the wall, and up both slopes "
                                                     "of a gable.")
        F[Q].addRow(self.cb_cop)
        self.cb_cstyle = combo(COPINGS, "Stone slabs, saddleback stones (rounded or stepped top), bricks on "
                                        "edge, cock and hen (upright stones, tall and short in turn, as on a "
                                        "dry-stone wall) or upright slates.")
        F[Q].addRow("   Coping:", self.cb_cstyle)
        self.cb_ccourse = check("   Coping sits on a whole course (bricks)",
                                "Bricks: the coping sits on the last whole course of bricks, so any odd bit of "
                                "height left over is a gap at the top of the face, not a row of cut bricks or "
                                "a gap under the coping.")
        F[Q].addRow(self.cb_ccourse)
        for k in ('c_h', 'c_len', 'c_over'):
            row(Q, k)

        # ---- Damage ----
        D = "Damage"
        self.cb_kick = check("Kick-out units", "A few units, picked at random, stand out from the wall a "
                                               "little, like old weathered brickwork. Their backs stay on "
                                               "the wall.")
        F[D].addRow(self.cb_kick)
        row(D, 'kick_pct')
        row(D, 'kick_mm')
        self.cb_spall = check("Sunk (spalled) faces", "A few units have their faces sunk back, as if the "
                                                      "frost has blown them.")
        F[D].addRow(self.cb_spall)
        row(D, 'spall_pct')
        row(D, 'spall_mm')
        self.cb_worn = check("Worn (rounded) units", "A few units have their corners and face edges rounded "
                                                     "off, like old, weathered bricks and stones.")
        F[D].addRow(self.cb_worn)
        row(D, 'worn_pct')
        row(D, 'worn_mm')
        row(D, 'missing_pct')
        self.cb_ruin = check("Broken-down top (ruin)", "The top of the wall broken down unevenly, in steps "
                                                       "along the joints, like a bombed or derelict building.")
        F[D].addRow(self.cb_ruin)
        row(D, 'ruin_depth')
        row(D, 'ruin_rough')
        row(D, 'holes_n')
        row(D, 'hole_size')
        row(D, 'broken_pct')
        self.cb_hang = check("Take out hanging units", "After the damage, takes out any odd units left "
                                                       "hanging in mid-air: bits of wall not joined to the rest, "
                                                       "and units with nothing under them and only one "
                                                       "neighbour.")
        F[D].addRow(self.cb_hang)
        self.cb_foot = check("Rubble at the foot of the wall", "Loose bricks or stones heaped against the "
                                                               "foot of the wall, under the damage they "
                                                               "fell from.")
        F[D].addRow(self.cb_foot)
        row(D, 'foot_w')
        row(D, 'foot_amt')
        row(D, 'backing')
        self.cb_through = check("   Blast holes go right through the backing",
                                "The blast holes are cut through the backing sheet too, so you can see "
                                "right through the wall (delete the face too). Ticking it with no backing "
                                "sheet gives you one.")
        F[D].addRow(self.cb_through)
        self.cb_mthrough = check("   Missing units go right through the backing",
                                 "Where a unit is missing, the backing sheet has a hole the same shape, so you "
                                 "can see right through (delete the face too). Ticking it with no backing "
                                 "sheet gives you one.")
        F[D].addRow(self.cb_mthrough)
        self.cb_remove = check("Delete the face the walling is on",
                               "Takes the face away once the walling is on, so a broken-down top or holes "
                               "show (use a backing sheet so there's still a wall behind). Don't use it on "
                               "the face of a solid you want to keep. Undo puts it back.")
        F[D].addRow(self.cb_remove)
        row(D, 'dmg_seed')

        # ---- Rubble pile ----
        Rp = "Rubble pile"
        note = QLabel("Select a face (the ground, a floor) and click 'Make rubble pile'. The pieces are "
                      "the material and sizes on the Walling tab.")
        note.setWordWrap(True)
        note.setStyleSheet("color: gray;")
        F[Rp].addRow(note)
        self.cb_pshape = combo(PILE_SHAPES, "A round heap, a long heap (along the face's longer side), or a "
                                            "heap filling the whole selected face.")
        F[Rp].addRow("Shape:", self.cb_pshape)
        for k in ('pile_len', 'pile_wid', 'pile_h', 'pile_n', 'pile_broken'):
            row(Rp, k)
        self.cb_core = check("Solid core under the pieces", "A solid mound under the loose pieces, so the "
                                                            "heap looks full and prints as one piece with "
                                                            "far fewer pieces.")
        F[Rp].addRow(self.cb_core)
        self.cb_planks = check("Planks and timbers", "Broken roof or floor timbers and planks lying in the "
                                                     "heap. Untick for none.")
        F[Rp].addRow(self.cb_planks)
        for k in ('pile_timbers', 'plank_len', 'plank_w', 'plank_t'):
            row(Rp, k)
        row(Rp, 'pile_barrels')
        self.cb_bkind = combo([('drum', "Oil drums"), ('barrel', "Wooden barrels")],
                              "Steel oil drums (straight, with two rolling hoops) or bulging wooden barrels. "
                              "Some stand up, some lie on their sides.")
        F[Rp].addRow("   Kind:", self.cb_bkind)
        row(Rp, 'barrel_d')
        row(Rp, 'barrel_h')
        row(Rp, 'pile_crates')
        row(Rp, 'crate_size')
        # your own object, picked from the model
        self._custom = None
        self._custom_name = ""
        self.lbl_custom = QLabel("Your own object: none picked")
        self.lbl_custom.setWordWrap(True)
        self.btn_custom = QPushButton("Use selected object")
        self.btn_custom.setToolTip("Select a group or component in the model (a sack, a wheel, a sign ...), "
                                   "then press this. Copies of it are dropped in the heap. It keeps its "
                                   "own up (Z) direction.")
        self.btn_custom.clicked.connect(self.pick_custom)
        self.btn_custom_clear = QPushButton("Clear")
        self.btn_custom_clear.setToolTip("Forget the object you picked.")
        self.btn_custom_clear.clicked.connect(self.clear_custom)
        crow = QHBoxLayout()
        crow.addWidget(self.btn_custom)
        crow.addWidget(self.btn_custom_clear)
        crow.addStretch(1)
        F[Rp].addRow(self.lbl_custom)
        F[Rp].addRow(crow)
        row(Rp, 'pile_custom')
        row(Rp, 'custom_scale')
        row(Rp, 'pile_seed')
        self._add_building_page()
        self.tabs.currentChanged.connect(self.changed)

        # ---- presets, report, buttons ----
        prow = QHBoxLayout()
        prow.addWidget(QLabel("Preset:"))
        self.cb_preset = QComboBox()
        _compact_combo(self.cb_preset, 16)
        prow.addWidget(self.cb_preset, 1)
        b_up = QPushButton("\u25b2")
        b_up.setToolTip("Moves the preset you have open up the list, so you can put your presets in your own order.")
        b_dn = QPushButton("\u25bc")
        b_dn.setToolTip("Moves the preset you have open down the list.")
        for b_ in (b_up, b_dn):
            b_.setFixedWidth(28)
            prow.addWidget(b_)
        b_up.clicked.connect(lambda: self.move_preset(-1))
        b_dn.clicked.connect(lambda: self.move_preset(1))
        self.btn_save = QPushButton("Save")
        self.btn_saveas = QPushButton("Save as...")
        self.btn_delete = QPushButton("Delete")
        self.btn_folder = QPushButton("Folder")
        for b_ in (self.btn_save, self.btn_saveas, self.btn_delete, self.btn_folder):
            prow.addWidget(b_)
        lay.addLayout(prow)
        brow = QHBoxLayout()
        self.btn_apply = QPushButton("Apply to face")
        self.btn_apply.setToolTip("Covers the selected face (a wall) with the walling, quoins, copings "
                                  "and damage set here.")
        self.btn_apply.setDefault(True)
        self.btn_pile = QPushButton("Make rubble pile")
        self.btn_pile.setToolTip("Makes a heap of loose bricks or stones (Rubble pile tab) on the selected face.")
        btn_close = QPushButton("Close")
        self.cb_lasttab = QCheckBox("Open at the last page used")
        self.cb_lasttab.setToolTip("Ticked, the window opens at the page (Walling, Bond, Whole building...) you "
                                   "had open last time.")
        st = _ui_settings()
        self.cb_lasttab.setChecked(bool(st.get('remember_tab', True)))
        self.b_info = QPushButton("Info")
        self.b_info.setCheckable(True)
        self.b_info.setChecked(False)
        self.b_info.setToolTip("Shows how to use it, the face you've picked, and what the last build came out like.")
        self.b_info.toggled.connect(self.toggle_info)
        brow.addWidget(self.btn_apply)
        brow.addWidget(self.btn_pile)
        brow.addStretch(1)
        brow.addWidget(self.b_info)
        brow.addWidget(self.cb_lasttab)
        brow.addWidget(btn_close)
        lay.addLayout(brow)
        lay.setSpacing(4)
        lay.setContentsMargins(8, 8, 8, 8)

        self.refresh_presets()
        self.cb_preset.currentIndexChanged.connect(self.apply_preset)
        self.btn_save.clicked.connect(self.save_preset)
        self.btn_saveas.clicked.connect(lambda: self.save_preset_as())
        self.btn_delete.clicked.connect(self.delete_preset)
        self.btn_folder.clicked.connect(self.open_folder)
        self.btn_apply.clicked.connect(self.apply_clicked)
        self.btn_pile.clicked.connect(self.pile_clicked)
        btn_close.clicked.connect(self.close)
        self.set_values(cur)
        # open at the page used last time
        if self.cb_lasttab.isChecked():
            try:
                self.tabs.setCurrentIndex(int(st.get('tab', 0)))
            except Exception:
                pass
        self.tabs.currentChanged.connect(lambda i: _ui_settings_save(tab=int(i)))
        self.cb_lasttab.toggled.connect(lambda on: _ui_settings_save(remember_tab=bool(on)))
        # show the preset you last picked - without loading it over the top of your settings
        last = st.get('last_preset')
        if last and last in self.preset_order():
            self.refresh_presets(select=last)
        # click on walling in the model and the sizes that made it light up here
        self._sel_names = None
        self._lit = []
        try:
            from PySide6.QtCore import QTimer
            self._sel_timer = QTimer(self)
            self._sel_timer.timeout.connect(self.watch_selection)
            self._sel_timer.start(400)
        except Exception:
            pass

    # ---- whole building: tick the walls that get walling ----
    def _add_building_page(self):
        from PySide6.QtWidgets import QAbstractItemView
        page = QWidget()
        lay = QVBoxLayout(page)
        info = QLabel("Select the building (or some of its wall groups) and click Find - or click it with "
                      "nothing selected for the whole model. Every wall is listed with a tick box: plain "
                      "walls start ticked, walls that already have walling on them start unticked. Click a "
                      "line to light that wall's face up in the model. Then 'Brick the ticked walls': each "
                      "gets the walling, quoins, copings and damage set on the other pages, round all its "
                      "openings. One Undo takes them all away.")
        info.setWordWrap(True)
        lay.addWidget(info)
        self.btn_find = QPushButton("Find walls in the selected building")
        self.btn_find.setToolTip("Lists the walls in the selected building or groups (or the whole model if "
                                 "nothing is selected), with a tick box for each.")
        lay.addWidget(self.btn_find)
        self.cb_inside_walls = QCheckBox("Include inside walls")
        self.cb_inside_walls.setToolTip("List Floor Plan's inside walls (room dividers) too, so they can have "
                                        "walling on them.")
        self.cb_inside_faces = QCheckBox("Use the inside face of each wall")
        self.cb_inside_faces.setToolTip("Puts the walling on the inside face of the walls (the side facing the "
                                        "middle of the building) instead of the outside.")
        lay.addWidget(self.cb_inside_walls)
        lay.addWidget(self.cb_inside_faces)
        self.lst_walls = QListWidget()
        self.lst_walls.setToolTip("Ticked walls get walling. Click a line to light that wall's face up in "
                                  "the model.")
        self.lst_walls.setSelectionMode(QAbstractItemView.ExtendedSelection)
        lay.addWidget(self.lst_walls, 1)
        trow = QHBoxLayout()
        b_plain = QPushButton("Tick all plain walls")
        b_plain.setToolTip("Ticks every wall that has no walling on it yet.")
        b_none = QPushButton("Untick all")
        b_none.setToolTip("Unticks every wall.")
        trow.addWidget(b_plain)
        trow.addWidget(b_none)
        trow.addStretch(1)
        lay.addLayout(trow)
        self.btn_brick_walls = QPushButton("Brick the ticked walls")
        self.btn_brick_walls.setToolTip("Covers the outside face of every ticked wall with the walling set on "
                                        "the other pages. One Undo takes them all away.")
        lay.addWidget(self.btn_brick_walls)
        self.lbl_walls = QLabel()
        self.lbl_walls.setWordWrap(True)
        lay.addWidget(self.lbl_walls)
        self.found_walls = []
        self.btn_find.clicked.connect(self.find_walls)
        self.cb_inside_walls.toggled.connect(lambda *_: self.find_walls() if self.found_walls else None)
        self.cb_inside_faces.toggled.connect(lambda *_: self.find_walls() if self.found_walls else None)
        b_plain.clicked.connect(lambda: self._tick_walls(True))
        b_none.clicked.connect(lambda: self._tick_walls(False))
        self.lst_walls.itemSelectionChanged.connect(self._wall_picked)
        self.btn_brick_walls.clicked.connect(lambda: self.tool.brick_walls_from_dialog(self)
                                             if self.tool is not None else None)
        self.tabs.addTab(page, "Whole building")
        self.tabs.setTabToolTip(self.tabs.count() - 1, "Find the walls of a building and tick the ones that "
                                                       "get walling.")

    def find_walls(self):
        scene = getattr(self.viewport, 'scene', None)
        if scene is None:
            return
        try:
            self.found_walls, skipped = find_building_walls(scene, self.cb_inside_walls.isChecked(),
                                                            self.cb_inside_faces.isChecked())
        except Exception as e:
            self.found_walls, skipped = [], 0
            QMessageBox.warning(self, PLUGIN_NAME, "Could not look for walls:\n%s" % e)
            return
        self.fill_walls()
        nb = sum(1 for w in self.found_walls if w['bricked'])
        if self.found_walls:
            txt = "Found %d wall%s" % (len(self.found_walls), "" if len(self.found_walls) == 1 else "s")
            txt += (" - %d already ha%s walling (unticked)." % (nb, "s" if nb == 1 else "ve")) if nb else "."
        else:
            txt = ("No walls found. Select the building (the group holding the walls) and click Find again, "
                   "or click Find with nothing selected for the whole model.")
        if skipped:
            txt += " %d group%s didn't look like a wall (no face front and back)." % (skipped,
                                                                                   "" if skipped == 1 else "s")
        self.lbl_walls.setText(txt)

    def fill_walls(self):
        self.lst_walls.blockSignals(True)
        self.lst_walls.clear()
        for i, w in enumerate(self.found_walls):
            txt = "%s  -  %.0f x %.0f mm" % (w['name'], w['length'], w['height'])
            if w['openings']:
                txt += ", %d opening%s" % (w['openings'], "" if w['openings'] == 1 else "s")
            if w['bricked']:
                txt += "  - has walling"
            it = QListWidgetItem(txt)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setData(Qt.UserRole, i)
            if w['bricked']:
                f = it.font()
                f.setBold(True)
                it.setFont(f)
            it.setCheckState(Qt.Unchecked if w['bricked'] else Qt.Checked)
            self.lst_walls.addItem(it)
        self.lst_walls.blockSignals(False)

    def _tick_walls(self, on):
        for i in range(self.lst_walls.count()):
            it = self.lst_walls.item(i)
            w = self.found_walls[i] if i < len(self.found_walls) else None
            it.setCheckState(Qt.Checked if (on and w is not None and not w['bricked']) else Qt.Unchecked)

    def ticked_walls(self):
        out = []
        for i in range(self.lst_walls.count()):
            it = self.lst_walls.item(i)
            if it.checkState() == Qt.Checked and i < len(self.found_walls):
                out.append(self.found_walls[i])
        return out

    def _wall_picked(self):
        """Lights up the faces of the wall lines clicked in the list."""
        scene = getattr(self.viewport, 'scene', None)
        if scene is None:
            return
        rows = sorted({self.lst_walls.row(it) for it in self.lst_walls.selectedItems()})
        if not rows:
            return
        try:
            scene.selection.clear()
            for r in rows:
                if r < len(self.found_walls):
                    scene.selection.add(self.found_walls[r]['face'].obj)
        except Exception:
            return
        self.wall = None
        try:
            self.viewport.notify_scene_changed()
        except Exception:
            try:
                self.viewport.update()
            except Exception:
                pass

    # ---- values ----
    def _sold_unlink(self, *_):
        if not self._busy:
            self._sold_linked = False

    def checks(self):
        return {'back_faces': self.cb_back, 'swap': self.cb_swap, 'new_group': self.cb_group,
                'join_wall': self.cb_join,
                'soldier': self.cb_sold, 'even_ends': self.cb_even, 'quoins_l': self.cb_ql,
                'quoins_r': self.cb_qr, 'q_open': self.cb_qo, 'q_courses': self.cb_qc,
                'heads': self.cb_heads, 'sills': self.cb_sills, 'copings': self.cb_cop,
                'kick': self.cb_kick, 'spall': self.cb_spall, 'ruin': self.cb_ruin,
                'through': self.cb_through, 'foot': self.cb_foot, 'remove_face': self.cb_remove,
                'pile_core': self.cb_core, 'header_on': self.cb_head, 'c_course': self.cb_ccourse,
                'worn': self.cb_worn, 'no_hanging': self.cb_hang, 'miss_through': self.cb_mthrough,
                'pile_timbers_on': self.cb_planks, 'courses_ground': self.cb_cground}

    def combos(self):
        return {'material': self.cb_mat, 'bond': self.cb_bond, 'offset_mode': self.cb_off,
                'c_style': self.cb_cstyle, 'pile_shape': self.cb_pshape, 'barrel_kind': self.cb_bkind}

    def get_values(self):
        v = {}
        for key, (s, _) in self.sp.items():
            v[key] = s.value()
        for key, c in self.checks().items():
            v[key] = c.isChecked()
        for key, cb in self.combos().items():
            v[key] = cb.currentData()
        v['offset_fixed'] = self.sp_ofix.value()
        v['offset_seq'] = self.le_seq.text()
        v['offset_seed'] = self.sp_seed.value()
        v['offset_rmax'] = self.sp_rmax.value()
        v['header_every'] = self.sp_every.value() if v.pop('header_on') else 0
        v['_header_n'] = self.sp_every.value()
        if self._sold_linked:
            v['soldier_len'] = None
        picked = []
        for i in range(self.lst_open.count()):
            it = self.lst_open.item(i)
            if it.data(Qt.UserRole) is not None and it.checkState() == Qt.Checked:
                picked.append(it.data(Qt.UserRole))
        v['soldier_holes'] = picked
        return v

    def set_values(self, d):
        self._busy = True
        try:
            for key, (s, _) in self.sp.items():
                val = d.get(key)
                if key == 'soldier_len':
                    if val is None:
                        self._sold_linked = True
                        val = d.get('length') or self.sp['length'][0].value()
                    else:
                        self._sold_linked = False
                if val is not None:
                    try:
                        s.setValue(int(val) if isinstance(s, QSpinBox) else float(val))
                    except Exception:
                        pass
            for key, c in self.checks().items():
                if key == 'header_on':
                    if 'header_every' in d:
                        c.setChecked(bool(d.get('header_every')))
                elif key in d:
                    c.setChecked(bool(d[key]))
            for key, cb in self.combos().items():
                if d.get(key) is not None:
                    for i in range(cb.count()):
                        if cb.itemData(i) == d[key]:
                            cb.setCurrentIndex(i)
            if 'offset_fixed' in d:
                self.sp_ofix.setValue(float(d['offset_fixed']))
            if 'offset_seq' in d:
                self.le_seq.setText(str(d['offset_seq']))
            if 'offset_seed' in d:
                self.sp_seed.setValue(int(d['offset_seed']))
            if 'offset_rmax' in d:
                self.sp_rmax.setValue(float(d['offset_rmax']))
            if d.get('header_every'):
                self.sp_every.setValue(int(d['header_every']))
            elif d.get('_header_n'):
                self.sp_every.setValue(int(d['_header_n']))
        finally:
            self._busy = False
        self.changed()

    def material_changed(self, *_):
        if self._busy:
            return
        sizes = MATERIAL_SIZES.get(self.cb_mat.currentData())
        if sizes:
            d = dict(sizes)
            if self.cb_mat.currentData() == 'brick':
                d['c_style'] = 'brick_edge' if self.cb_cstyle.currentData() == 'cock_hen' else None
            elif self.cb_mat.currentData() == 'drystone':
                d['c_style'] = 'cock_hen'
            elif self.cb_mat.currentData() == 'slate':
                d['c_style'] = 'slate_up'
            d = {k: v_ for k, v_ in d.items() if v_ is not None}
            self.set_values(d)

    def _row_vis(self, tab, w, on):
        """Shows or hides a whole row (the setting and its label)."""
        fl = self.pages[tab]
        try:
            fl.setRowVisible(w, bool(on))
            return
        except Exception:
            pass
        w.setVisible(bool(on))
        try:
            lab = fl.labelForField(w)
            if lab is not None:
                lab.setVisible(bool(on))
        except Exception:
            pass

    def changed(self, *_):
        if self._busy:
            return
        if self._sold_linked:
            self._busy = True
            self.sp['soldier_len'][0].setValue(self.sp['length'][0].value())
            self._busy = False
        if (self.cb_through.isChecked() or self.cb_mthrough.isChecked()) \
                and self.sp['backing'][0].value() <= 0:
            # holes right through need a backing sheet to be cut through: give it one
            self._busy = True
            self.sp['backing'][0].setValue(102.5)
            self._busy = False
        v = self.get_values()
        mat = v['material']
        brick = mat == 'brick'
        stone = not brick
        off = v['offset_mode']
        on = {'header_len': True, 'var': stone, 'relief': stone, 'round': stone, 'stone_seed': stone,
              'soldier_len': brick and v['soldier'], 'corner_angle': brick and v['soldier'],
              'min_end_pct': brick and v['even_ends'],
              'q_long': v['quoins_l'] or v['quoins_r'] or v['q_open'] or v['heads'] or v['sills'],
              'c_h': v['copings'] and v['c_style'] != 'brick_edge',
              'c_len': v['copings'] and v['c_style'] in ('slab', 'saddle', 'stepped'), 'c_over': v['copings'],
              'pile_wid': v['pile_shape'] != 'face', 'pile_len': v['pile_shape'] != 'face'}
        on['q_short'] = on['q_h'] = on['q_proud'] = on['q_long']
        for key, ok in on.items():
            s, lab = self.sp[key]
            s.setEnabled(bool(ok))
            lab.setEnabled(bool(ok))
        # Damage and Rubble pile: settings that belong to a tick only show when it's ticked
        holes = v['holes_n'] > 0
        missing = (v['missing_pct'] or 0) > 0
        show = {'kick_pct': v['kick'], 'kick_mm': v['kick'], 'spall_pct': v['spall'], 'spall_mm': v['spall'],
                'worn_pct': v['worn'], 'worn_mm': v['worn'],
                'ruin_depth': v['ruin'], 'ruin_rough': v['ruin'], 'hole_size': holes,
                'broken_pct': v['ruin'] or holes,
                'foot_w': v['foot'], 'foot_amt': v['foot'],
                'pile_timbers': v['pile_timbers_on'], 'plank_len': v['pile_timbers_on'],
                'plank_w': v['pile_timbers_on'], 'plank_t': v['pile_timbers_on'],
                'barrel_d': v['pile_barrels'] > 0, 'barrel_h': v['pile_barrels'] > 0,
                'crate_size': v['pile_crates'] > 0, 'custom_scale': v['pile_custom'] > 0}
        for key, ok in show.items():
            s, lab = self.sp[key]
            s.setEnabled(True)
            lab.setEnabled(True)
            self._row_vis(self._key_tab[key], s, ok)
        self._row_vis("Damage", self.cb_through, holes)
        self._row_vis("Damage", self.cb_mthrough, missing)
        self._row_vis("Damage", self.cb_hang, v['ruin'] or holes or missing)
        self._row_vis("Rubble pile", self.cb_bkind, v['pile_barrels'] > 0)
        self.cb_ccourse.setEnabled(brick and v['copings'])
        self.cb_group.setEnabled(not v.get('join_wall'))
        for w_ in (self.cb_bond, self.cb_off, self.cb_head, self.cb_sold, self.cb_even, self.cb_qc):
            w_.setEnabled(brick)
        self.sp_every.setEnabled(brick and self.cb_head.isChecked())
        self.sp_ofix.setEnabled(brick and off == "fixed")
        self.le_seq.setEnabled(brick and off == "sequence")
        self.sp_seed.setEnabled(brick and off == "random")
        self.sp_rmax.setEnabled(brick and off == "random")
        self.cb_cstyle.setEnabled(v['copings'])
        self.lst_open.setEnabled(True)
        what = 'pile' if self.tabs.currentIndex() == TABS.index("Rubble pile") else 'wall'
        # Enter runs the button for the tab you're on: the rubble pile on its tab, walling elsewhere
        try:
            self.btn_apply.setAutoDefault(False)
            self.btn_pile.setAutoDefault(False)
            self.btn_apply.setDefault(what != 'pile')
            self.btn_pile.setDefault(what == 'pile')
        except Exception:
            pass
        pv = self.preview_values(v)
        self.preview.set_values(pv, what)
        _ui_settings_save(last_values={k: v[k] for k in DEFAULTS if k in v and k != 'soldier_holes'})

    def preview_values(self, v):
        p = dict(v)
        for k, d in DEFAULTS.items():
            if p.get(k) is None and k not in ('soldier_len', 'soldier_holes'):
                p[k] = d
        p['soldier_len'] = p.get('soldier_len') or p['length']
        p['tiny'] = 1.0
        if getattr(self, '_custom', None):
            p['_custom'] = self._custom
        return p

    # ---- your own object for the rubble pile ----
    def pick_custom(self, *_):
        scene = getattr(self.viewport, 'scene', None)
        sel = list(getattr(scene, 'selection', None) or [])
        groups = [e for e in sel if getattr(e, 'mesh', None) is not None
                  and 'face' not in type(e).__name__.lower() and not hasattr(e, 'loop')]
        if not groups:
            self.show_report("Select a group or component in the model first (the object you want in the "
                             "heap), then press 'Use selected object'.", True)
            return
        g = groups[0]
        try:
            faces = object_faces(g)
        except Exception as e:
            self.show_report("Couldn't read that object: %s" % e, True)
            return
        if not faces:
            self.show_report("That object has no faces to copy.", True)
            return
        self._custom = faces
        self._custom_name = str(getattr(g, 'name', '') or 'Your object')
        xs = [q[0] for o, _ in faces for q in o]
        ys = [q[1] for o, _ in faces for q in o]
        zs = [q[2] for o, _ in faces for q in o]
        self.lbl_custom.setText("Your own object: %s (%.0f x %.0f x %.0f mm, %d faces)"
                                % (self._custom_name, max(xs) - min(xs), max(ys) - min(ys),
                                   max(zs) - min(zs), len(faces)))
        if self.sp['pile_custom'][0].value() == 0:
            self.sp['pile_custom'][0].setValue(3)
        self.show_report("Picked %s for the rubble pile." % self._custom_name)
        self.changed()

    def clear_custom(self, *_):
        self._custom = None
        self._custom_name = ""
        self.lbl_custom.setText("Your own object: none picked")
        self.changed()

    def show_report(self, text, bad=False):
        self.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if bad else "#2e7d32"))
        self.lbl_report.setText(text)
        self.lbl_report.setVisible(True)
        # the report waits behind the Info button; the button says when there's something to read
        if not self.b_info.isChecked():
            self.b_info.setText("Info (!)" if bad else "Info (new)")
            self.b_info.setStyleSheet("font-weight: bold; color: %s;" % ("#b35900" if bad else "#2e7d32"))

    def toggle_info(self, on):
        self.info_box.setVisible(bool(on))
        if on:
            self.b_info.setText("Info")
            self.b_info.setStyleSheet("")

    def watch_selection(self):
        """Looks at what's selected in the model; for walling we made, lights up the size boxes that
        set it (and turns to their page)."""
        try:
            if not self.isVisible():
                return
            scene = getattr(self.viewport, 'scene', None)
            sel = _items(getattr(scene, 'selection', None)) if scene is not None else []
            names = tuple(str(getattr(e, 'name', '') or '') for e in sel)
        except Exception:
            return
        if names == self._sel_names:
            return
        self._sel_names = names
        keys = []
        for nm in names:
            for k_ in piece_keys(nm):
                if k_ not in keys:
                    keys.append(k_)
        self.light_up(keys)

    def light_up(self, keys):
        for s_, lab_ in self._lit:
            try:
                s_.setStyleSheet("")
                lab_.setStyleSheet("")
            except Exception:
                pass
        self._lit = []
        for k_ in keys:
            if k_ in self.sp:
                s_, lab_ = self.sp[k_]
                s_.setStyleSheet("background-color: #fff3a0;")
                lab_.setStyleSheet("background-color: #fff3a0; font-weight: bold;")
                self._lit.append((s_, lab_))
        if keys and keys[0] in self._key_tab:
            try:
                self.tabs.setCurrentIndex(TABS.index(self._key_tab[keys[0]]))
            except Exception:
                pass

    # ---- openings list ----
    def fill_openings(self, openings, preselected):
        self.lst_open.clear()
        if openings:
            for hi, label in openings:
                it = QListWidgetItem(label)
                it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
                on = (preselected is None) or (hi in preselected)
                it.setCheckState(Qt.Checked if on else Qt.Unchecked)
                it.setData(Qt.UserRole, hi)
                self.lst_open.addItem(it)
        else:
            it = QListWidgetItem("(no openings found in this face)")
            it.setFlags(Qt.NoItemFlags)
            self.lst_open.addItem(it)

    def set_all(self, state):
        for i in range(self.lst_open.count()):
            it = self.lst_open.item(i)
            if it.data(Qt.UserRole) is not None:
                it.setCheckState(state)

    def read_selection(self):
        """Picks up the selected face; refreshes the openings list if it's a new wall."""
        sel = _selected_wall(self.viewport)
        if sel is None:
            self.lbl_face.setText("Select a face (a wall), then click 'Apply to face' - or a floor or the "
                                  "ground, then 'Make rubble pile' - or use the Whole building page to "
                                  "tick the walls of a building.")
            return None
        wall, others, unit_label = sel
        if wall is not self.wall:
            openings, pre = find_openings(wall, others, "mm", 1000.0 if unit_label == "m" else 1.0)
            self.fill_openings(openings, pre)
            self.wall = wall
        n = len(getattr(wall, 'holes', None) or [])
        self.lbl_face.setText("Selected face: %d opening%s. Click 'Apply to face' (or 'Make rubble pile'). "
                              "All sizes are real-world mm." % (n, "" if n == 1 else "s"))
        return sel

    def apply_clicked(self):
        if self.tool is not None:
            self.tool.apply_from_dialog(self)

    def pile_clicked(self):
        if self.tool is not None:
            self.tool.pile_from_dialog(self)

    def changeEvent(self, e):
        try:
            from PySide6.QtCore import QEvent
            if e.type() == QEvent.ActivationChange and self.isActiveWindow():
                self.read_selection()
        except Exception:
            pass
        super().changeEvent(e)

    # ---- presets ----
    def all_presets(self):
        d = dict(BUILTIN_PRESETS)
        d.update(self.user_presets)
        return d

    def preset_order(self):
        """Every preset name, in your order (new ones at the end)."""
        names = list(BUILTIN_PRESETS) + sorted(n for n in self.user_presets if n not in BUILTIN_PRESETS)
        order = [n for n in _ui_settings().get('preset_order', []) if n in names]
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
            _ui_settings_save(preset_order=order)
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
        _ui_settings_save(last_preset=name or None)      # opens on this one next time
        p = self.all_presets().get(name) if name else None
        if not p:
            return
        d = {k: v for k, v in p.items() if k not in ('name', '_legacy')}
        if p.get('_legacy') and 'material' not in d:
            d['material'] = 'brick'
        if not set(d) <= SIZE_PRESET_KEYS:
            # a whole look (stone, quoins, damage ...): anything it doesn't set goes back to
            # the starting settings, so one look doesn't carry over into the next
            base = {k: v for k, v in DEFAULTS.items() if k not in KEEP_KEYS}
            base.update(d)
            d = base
        self.set_values(d)

    def save_preset(self):
        """Save: updates the preset you have open, with no typing. If it's a built-in one
        (or none is picked), asks for a name instead."""
        name = self.cb_preset.currentData()
        if name and name in self.user_presets and name not in BUILTIN_PRESETS:
            if self.save_preset_as(quiet_name=name):
                try:
                    from PySide6.QtCore import QTimer
                    self.btn_save.setText("Saved")
                    QTimer.singleShot(1500, lambda: self.btn_save.setText("Save"))
                except Exception:
                    pass
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
            QMessageBox.warning(self, "Name in use",
                                "That name belongs to a built-in preset. Choose another name.")
            return False
        if name in self.user_presets and not quiet_name:
            r = QMessageBox.question(self, "Overwrite preset",
                                     "Preset '%s' already exists. Overwrite it?" % name)
            if r != QMessageBox.Yes:
                return False
        try:
            old = self.user_presets.get(name) or {}
            save_preset_file(name, self.get_values())
            if old.get('_legacy'):
                delete_preset_file(name, legacy=True)     # it lives in the new folder now
        except Exception as e:
            QMessageBox.warning(self, "Save failed", "Could not save the preset:\n%s" % e)
            return False
        self.user_presets = load_presets()
        self.refresh_presets(select=name)
        _ui_settings_save(last_preset=name)
        return True

    def delete_preset(self):
        name = self.cb_preset.currentData()
        if not name or name in BUILTIN_PRESETS or name not in self.user_presets:
            QMessageBox.information(self, PLUGIN_NAME, "Pick one of your own presets to delete "
                                                       "(built-in presets can't be deleted).")
            return
        r = QMessageBox.question(self, "Delete preset", "Delete preset '%s'?" % name)
        if r != QMessageBox.Yes:
            return
        try:
            delete_preset_file(name, legacy=bool(self.user_presets[name].get('_legacy')))
        except Exception as e:
            QMessageBox.warning(self, PLUGIN_NAME, "Could not delete it:\n%s" % e)
        self.user_presets = load_presets()
        self.refresh_presets()
        if _ui_settings().get('last_preset') == name:
            _ui_settings_save(last_preset=None)

    def open_folder(self):
        try:
            os.makedirs(PRESET_DIR, exist_ok=True)
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(PRESET_DIR))
        except Exception as e:
            QMessageBox.information(self, PLUGIN_NAME, "Presets folder:\n%s\n\n(%s)" % (PRESET_DIR, e))



DEFAULTS = {
    'material': 'brick',
    'length': 210.0, 'height': 65.0, 'depth': 20.0, 'joint': 10.0, 'min_frag': 20.0, 'header_len': 100.0,
    'var': 0.0, 'relief': 0.0, 'round': 0.0, 'stone_seed': 1,
    'bond': 'running', 'courses_ground': True,
    'offset_mode': 'bond', 'offset_fixed': 0.5, 'offset_seq': '0, 0.5, 0.25, 0.75',
    'offset_seed': 1, 'offset_rmax': 1.0,
    'header_every': 0, '_header_n': 5,
    'soldier': False, 'soldier_len': None, 'corner_angle': 35.0,
    'subdiv': 4, 'back_faces': True, 'swap': False, 'new_group': True, 'join_wall': True, 'hole_gap': 0.01,
    'even_ends': True, 'min_end_pct': 50.0,
    'quoins_l': False, 'quoins_r': False, 'q_open': False, 'q_courses': True,
    'q_long': 450.0, 'q_short': 225.0, 'q_h': 290.0, 'q_proud': 10.0, 'heads': False, 'sills': False,
    'copings': False, 'c_style': 'slab', 'c_h': 150.0, 'c_len': 600.0, 'c_over': 30.0, 'c_course': True,
    'kick': False, 'kick_pct': 8.0, 'kick_mm': 3.0, 'spall': False, 'spall_pct': 6.0, 'spall_mm': 3.0,
    'missing_pct': 0.0, 'ruin': False, 'ruin_depth': 900.0, 'ruin_rough': 6, 'broken_pct': 40.0,
    'holes_n': 0, 'hole_size': 700.0, 'through': False, 'foot': False, 'foot_w': 900.0, 'foot_amt': 50.0,
    'worn': False, 'worn_pct': 15.0, 'worn_mm': 15.0, 'no_hanging': True, 'miss_through': False,
    'backing': 0.0, 'remove_face': False, 'dmg_seed': 1,
    'pile_shape': 'heap', 'pile_len': 2500.0, 'pile_wid': 1800.0, 'pile_h': 900.0, 'pile_n': 220,
    'pile_broken': 40.0, 'pile_timbers': 2, 'pile_core': True, 'pile_seed': 1,
    'pile_timbers_on': True, 'plank_len': 3200.0, 'plank_w': 225.0, 'plank_t': 75.0,
    'pile_barrels': 0, 'barrel_kind': 'drum', 'barrel_d': 585.0, 'barrel_h': 880.0,
    'pile_crates': 0, 'crate_size': 600.0, 'pile_custom': 0, 'custom_scale': 100.0,
}


def _with(material, **kw):
    d = {'material': material}
    d.update(MATERIAL_SIZES[material])
    d.update(kw)
    return d


BUILTIN_PRESETS = {
    "Brick slip 210 x 65 x 20": {'material': 'brick', 'length': 210.0, 'height': 65.0, 'depth': 20.0,
                                 'joint': 10.0, 'header_len': 100.0},
    "UK standard brick 215 x 65 x 102.5": {'material': 'brick', 'length': 215.0, 'height': 65.0,
                                           'depth': 102.5, 'joint': 10.0, 'header_len': 102.5},
    "German NF brick 240 x 71 x 115": {'material': 'brick', 'length': 240.0, 'height': 71.0, 'depth': 115.0,
                                       'joint': 10.0, 'header_len': 115.0},
    "US modular brick 194 x 57 x 92": {'material': 'brick', 'length': 194.0, 'height': 57.0, 'depth': 92.0,
                                       'joint': 10.0, 'header_len': 92.0},
    "Concrete block 440 x 215 x 100": {'material': 'brick', 'length': 440.0, 'height': 215.0, 'depth': 100.0,
                                       'joint': 10.0, 'header_len': 215.0},
    "Concrete block 390 x 190 x 190": {'material': 'brick', 'length': 390.0, 'height': 190.0, 'depth': 190.0,
                                       'joint': 10.0, 'header_len': 190.0},
    "Brick wall with stone quoins": _with('brick', depth=20.0, quoins_l=True, quoins_r=True, q_courses=True,
                                          q_long=450.0, q_short=225.0, q_h=290.0, q_proud=10.0),
    "Bomb-damaged brick wall": _with('brick', depth=20.0, ruin=True, ruin_depth=1100.0, ruin_rough=7,
                                     broken_pct=55.0, holes_n=2, hole_size=800.0, missing_pct=3.0,
                                     kick=True, kick_pct=6.0, foot=True, foot_w=900.0, foot_amt=60.0,
                                     backing=100.0, through=True),
    "Coursed ashlar (Bath stone)": _with('ashlar', quoins_l=False, quoins_r=False, copings=True,
                                         c_style='slab', c_h=150.0, c_len=750.0, c_over=40.0),
    "Random rubble with dressed quoins": _with('rubble', quoins_l=True, quoins_r=True, q_open=True,
                                               heads=True, sills=True, q_courses=False, q_long=500.0,
                                               q_short=300.0, q_h=300.0, q_proud=12.0),
    "Dry-stone wall, cock and hen coping": _with('drystone', copings=True, c_style='cock_hen', c_h=380.0,
                                                 c_over=30.0),
    "Welsh slate wall, upright slate coping": _with('slate', copings=True, c_style='slate_up', c_h=320.0,
                                                    c_over=10.0),
    "Derelict rubble-stone wall": _with('rubble', ruin=True, ruin_depth=800.0, ruin_rough=5, broken_pct=30.0,
                                        missing_pct=4.0, foot=True, foot_w=700.0, foot_amt=40.0),
}

EDDY_TIPS = {
    'Material': "Bricks or blocks in a bond, coursed ashlar, random rubble, dry-stone walling or Welsh slate.",
    'Bond': 'The pattern the bricks are laid in: stretcher, English, Flemish and so on.',
    'Row offsets': 'How far each course is moved along: as the bond says, a fixed amount every '
                   '2nd course, your own sequence, or at random.',
    'Openings to dress': 'Tick the openings that get a soldier course, quoins, a stone head or a sill.',
    'Coping': 'The kind of coping along the top of the wall.',
    'Shape': 'The shape of the rubble heap.',
    'All': 'Ticks all the openings.',
    'None': 'Unticks all the openings.',
    'Apply to face': 'Covers the selected face (a wall) with the walling set here.',
    'Make rubble pile': 'Makes a heap of loose bricks or stones on the selected face.',
    'Kind': 'Oil drums or wooden barrels.',
    'Use selected object': 'Select a group or component in the model, then press this to drop copies of it '
                           'in the rubble pile.',
    'Clear': 'Forget the object you picked for the rubble pile.',
    'Tick all plain walls': 'Ticks every wall that has no walling on it yet.',
    'Untick all': 'Unticks every wall.',
    'Brick the ticked walls': 'Covers every ticked wall with the walling set on the other pages, in one Undo.',
}
EDDY_TIPS_END = None


def _selected_wall(viewport):
    """(wall face, other selected faces, unit label) from the selection, or None.
    The wall is the selected face with the most openings (then the biggest); any
    other selected faces are treated as "pick this opening"."""
    scene = getattr(viewport, 'scene', None)
    selection = getattr(scene, 'selection', None) or set()
    faces = [it for it in selection
             if 'face' in type(it).__name__.lower() or hasattr(it, 'loop')]
    if not faces:
        return None
    wall = max(faces, key=lambda f: (len(getattr(f, 'holes', None) or []), _extent(f)))
    others = [f for f in faces if f is not wall]
    pts = [vertex_to_vector3d(v) for v in getattr(wall, 'vertices', [])]
    size = 3.0
    if len(pts) >= 3:
        size = max((pts[1] - pts[0]).length(), (pts[-1] - pts[0]).length())
    return wall, others, ("m" if size < 50.0 else "mm")


def _items(x):
    if x is None:
        return []
    if isinstance(x, dict):
        return list(x.values())
    try:
        return list(x)
    except Exception:
        return []


def _walk_groups(groups, out, depth=0):
    for g in _items(groups):
        if depth > 50:
            return
        out.append(g)
        _walk_groups(getattr(g, 'children', None), out, depth + 1)
        _walk_groups(getattr(g, 'groups', None), out, depth + 1)


def mesh_of_face(scene, face):
    """The mesh a face belongs to: the loose geometry, or a group's mesh."""
    meshes = [getattr(scene, 'mesh', None)]
    gs = []
    _walk_groups(getattr(scene, 'groups', None), gs)
    meshes += [getattr(g, 'mesh', None) for g in gs]
    for m in meshes:
        if m is None:
            continue
        try:
            if face in m.faces:
                return m
        except Exception:
            pass
    return None


def remove_face(scene, mesh, face):
    """Takes the face away, and any of its edges no other face uses."""
    loop = list(getattr(face, 'loop', None) or [])
    try:
        scene.selection.discard(face)
    except Exception:
        pass
    mesh.remove_face(face)
    for i in range(len(loop)):
        try:
            e = mesh.find_edge(loop[i], loop[(i + 1) % len(loop)])
            if e is not None and not e.faces:
                try:
                    scene.selection.discard(e)
                except Exception:
                    pass
                mesh.remove_edge(e)
        except Exception:
            pass
    try:
        mesh.prune_orphan_vertices()
    except Exception:
        pass


def make_command(mutate, meshes):
    """One undo step that adds the groups and removes faces. Snapshots the meshes
    that change and the group list (like IngeTrazo's own Windowizer)."""
    try:
        from core.history import Command
    except Exception:
        Command = None
    if Command is None or not all(hasattr(m, 'capture_state') for m in meshes):
        return SnapshotImport(mutate)

    class StudioCommand(Command):
        def __init__(self):
            self.before = self.after = None

        @staticmethod
        def _capture(scene):
            return {'meshes': [(m, m.capture_state()) for m in meshes],
                    'groups': list(scene.groups)}

        @staticmethod
        def _restore(scene, st):
            for m, snap in st['meshes']:
                m.restore_state(snap)
            scene.groups[:] = st['groups']
            try:
                keep = set(scene.groups)
                for m in meshes:
                    keep |= set(m.faces) | set(m.edges)
                scene.selection.intersection_update(keep)
            except Exception:
                pass

        def _bump(self, scene):
            try:
                scene.version += 1
            except Exception:
                pass

        def do(self, scene):
            if self.after is None:
                self.before = self._capture(scene)
                try:
                    mutate(scene)
                except BaseException:
                    self._restore(scene, self.before)
                    raise
                self.after = self._capture(scene)
            else:
                self._restore(scene, self.after)
            self._bump(scene)

        def undo(self, scene):
            self._restore(scene, self.before)
            self._bump(scene)

    return StudioCommand()


def _full(p):
    """The settings with every key filled in."""
    q = dict(DEFAULTS)
    q.update({k: v for k, v in p.items() if v is not None or k == 'soldier_len'})
    if q.get('soldier_len') is None:
        q['soldier_len'] = None
    return q


def _course_from_ground(p, fr):
    """Courses counted from the ground (height 0), not from the bottom of each wall, so they run
    on through the floor levels: the first floor's courses carry on from the ground floor's, with
    no cut bricks or odd joint where the two walls meet. Upright walls only."""
    p['_course_base'], p['_course_y0'], p['_course_r0'], p['_course_x0'] = 0.0, 0.0, 0, None
    if not p.get('courses_ground', True) or p.get('material', 'brick') != 'brick':
        return
    try:
        if fr['v'].z() < 0.999:
            return                         # not an upright wall (or the courses are turned)
        base = fr['origin'].z()
        o, u = fr['origin'], fr['u']
        # the bond starts from the same place along every wall in line (a floor above or below),
        # so the joints carry on up through the floor levels
        p['_course_x0'] = -(o.x() * u.x() + o.y() * u.y() + o.z() * u.z())
    except Exception:
        return
    step = p['height'] + p['joint']
    if step <= 0 or abs(base) < 1e-9:
        return
    k = int(math.floor(base / step + 1e-6))
    y0 = base - k * step
    if y0 < 1e-6 * step or y0 > step * (1 - 1e-6):
        y0 = 0.0
    p['_course_base'] = base
    p['_course_y0'] = y0
    p['_course_r0'] = k if k >= 0 else k % 3600       # (the bond repeats, so counting on is fine)


def _to_metres(p):
    p = dict(p)
    p['_mm'] = 0.001
    for key in LENGTH_KEYS:
        if p.get(key) is not None:
            p[key] = p[key] * 0.001
    return p


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
class BrickBlockStudioTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Shift+T"
    description = ("Brick and block bonds, stone walling (coursed ashlar, random rubble, dry-stone, Welsh "
                   "slate), quoins, copings, weathering and bomb-site damage, and rubble piles.")

    _saved = None
    _dialog = None          # the open window (it stays open between walls)

    def on_activate(self, viewport):
        dlg = BrickBlockStudioTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.viewport = viewport
                    dlg.read_selection()
                    dlg.raise_()
                    dlg.activateWindow()
                    return
            except Exception:
                pass

        sel = _selected_wall(viewport)
        wall, openings, preselected = None, [], None
        if sel is not None:
            wall, others, unit_label = sel
            openings, preselected = find_openings(wall, others, "mm", 1000.0 if unit_label == "m" else 1.0)

        cur = dict(DEFAULTS)
        if BrickBlockStudioTool._saved:
            saved = dict(BrickBlockStudioTool._saved)
            if saved.pop('unit', 'mm') == 'm':
                # remembered from an older version that worked in metres
                for key in SIZE_KEYS:
                    if saved.get(key) is not None:
                        saved[key] = saved[key] * 1000.0
            cur.update(saved)
        else:
            last = _ui_settings().get('last_values')
            if isinstance(last, dict):
                cur.update({k: last[k] for k in DEFAULTS if k in last})     # the last settings used
        if preselected:
            cur['soldier'] = True      # you picked openings, so you probably want the course

        dialog = BrickDialog(cur, openings, preselected, viewport, tool=self, viewport=viewport)
        dialog.wall = wall
        dialog.read_selection()
        if sel is None:
            # nothing (or a whole building) picked: start on the Whole building page and look for walls
            dialog.tabs.setCurrentIndex(dialog.tabs.count() - 1)
            dialog.find_walls()
        BrickBlockStudioTool._dialog = dialog

        def closed(*_):
            BrickBlockStudioTool._dialog = None
        dialog.finished.connect(closed)
        eddy_window(dialog, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dialog.show()

    def on_deactivate(self, viewport):
        pass

    def _remember(self, vals):
        keep = dict(vals)
        keep.pop('soldier_holes', None)     # opening choice is per wall, don't remember it
        BrickBlockStudioTool._saved = keep

    def apply_from_dialog(self, dialog):
        sel = dialog.read_selection()
        if sel is None:
            QMessageBox.information(dialog, PLUGIN_NAME, "Select a face (a wall) first.")
            return
        wall, others, unit_label = sel
        vals = dialog.get_values()
        self._remember(vals)
        self.active_face = wall
        msg = self.generate_layout(dialog.viewport, vals)
        if msg:
            dialog.show_report(*msg)

    def pile_from_dialog(self, dialog):
        sel = dialog.read_selection()
        if sel is None:
            QMessageBox.information(dialog, PLUGIN_NAME, "Select a face (the ground or a floor) first.")
            return
        vals = dialog.get_values()
        self._remember(vals)
        if getattr(dialog, '_custom', None):
            vals['_custom'] = dialog._custom
            vals['_custom_name'] = dialog._custom_name
        msg = self.make_pile_on(dialog.viewport, sel[0], vals)
        if msg:
            dialog.show_report(*msg)

    # ---- building ----
    @staticmethod
    def _frame(face, swap=False):
        face_pts = [vertex_to_vector3d(v) for v in face.vertices]
        if len(face_pts) < 3:
            return None
        n_raw = getattr(face, 'normal', None)
        normal = QVector3D(0, 0, 0)
        if n_raw is not None:
            normal = vertex_to_vector3d(n_raw() if callable(n_raw) else n_raw)
        if normal.length() < 0.001:
            normal = QVector3D.crossProduct(face_pts[1] - face_pts[0], face_pts[2] - face_pts[1])
        normal = normal.normalized() if normal.length() > 0.001 else QVector3D(0, 0, 1)
        origin = face_pts[0]
        base_u, base_v = _level_dirs(face_pts, normal)     # courses run level on walls
        if swap:
            u_dir, v_dir = base_v, -base_u
        else:
            u_dir, v_dir = base_u, base_v
        left_handed = QVector3D.dotProduct(QVector3D.crossProduct(u_dir, v_dir), normal) < 0
        us = [QVector3D.dotProduct(q - origin, u_dir) for q in face_pts]
        vs = [QVector3D.dotProduct(q - origin, v_dir) for q in face_pts]
        origin = origin + u_dir * min(us) + v_dir * min(vs)
        W = max(us) - min(us)
        H = max(vs) - min(vs)
        outline = [(QVector3D.dotProduct(q - origin, u_dir), QVector3D.dotProduct(q - origin, v_dir))
                   for q in face_pts]
        if len(outline) > 3 and abs(outline[0][0] - outline[-1][0]) < 1e-9 \
                and abs(outline[0][1] - outline[-1][1]) < 1e-9:
            outline.pop()
        if _area(outline) < 0:
            outline.reverse()
        holes, hole_ids = [], []
        for hi, hole in enumerate(getattr(face, 'holes', None) or []):
            poly = []
            for v in hole:
                q = vertex_to_vector3d(v)
                poly.append((QVector3D.dotProduct(q - origin, u_dir), QVector3D.dotProduct(q - origin, v_dir)))
            if len(poly) > 1 and abs(poly[0][0] - poly[-1][0]) < 1e-9 and abs(poly[0][1] - poly[-1][1]) < 1e-9:
                poly.pop()
            if len(poly) < 3:
                continue
            if _area(poly) < 0:
                poly.reverse()
            holes.append(poly)
            hole_ids.append(hi)
        # doorways: notches up into the bottom edge (found the right way up, whatever 'swap' says)
        o0 = face_pts[0]
        base_outline = [(QVector3D.dotProduct(q - o0, base_u), QVector3D.dotProduct(q - o0, base_v))
                        for q in face_pts]
        for j, notch in enumerate(outline_notches(base_outline)):
            poly = []
            for a, b in notch:
                q = o0 + base_u * a + base_v * b
                poly.append((QVector3D.dotProduct(q - origin, u_dir), QVector3D.dotProduct(q - origin, v_dir)))
            if _area(poly) < 0:
                poly.reverse()
            holes.append(poly)
            hole_ids.append(NOTCH_BASE + j)
        return {'origin': origin, 'u': u_dir, 'v': v_dir, 'n': normal, 'left': left_handed,
                'W': W, 'H': H, 'outline': outline, 'holes': holes, 'hole_ids': hole_ids}

    @staticmethod
    def _seed(fr):
        """A number from where the face is, so two walls the same size don't get the very
        same pattern of stones or damage."""
        o = fr['origin']
        try:
            return int(abs(o.x() * 7.31 + o.y() * 13.7 + o.z() * 17.9) * 1000) % 99991
        except Exception:
            return 0

    @staticmethod
    def _mapper(fr, axes=('u', 'v', 'n'), mirror=False):
        """Turns local (a, b, c) solids into world faces along the given frame axes."""
        o = fr['origin']
        e = [fr[a] for a in axes]
        flip = (QVector3D.dotProduct(QVector3D.crossProduct(e[0], e[1]), e[2]) < 0) != bool(mirror)

        def solid(faces):
            out = []
            for outer, holes in faces:
                def w(q):
                    pt = o + e[0] * q[0] + e[1] * q[1] + e[2] * q[2]
                    return (pt.x(), pt.y(), pt.z())
                ow = [w(q) for q in outer]
                hw = [[w(q) for q in h] for h in holes]
                if flip:
                    ow = ow[::-1]
                    hw = [h[::-1] for h in hw]
                out.append((ow, hw))
            return out
        return solid

    def generate_layout(self, viewport, vals):
        face = getattr(self, 'active_face', None)
        if face is None:
            return None
        job = self._layout_parts(face, vals)
        if isinstance(job, tuple):
            return job
        p, res, n_loose, remove = job['p'], job['res'], job['n_loose'], job['remove']
        mat_name = job['mat_name']
        if p.get('join_wall'):
            scene_ = getattr(viewport, 'scene', None)
            m_ = mesh_of_face(scene_, face) if scene_ is not None else None
            if m_ is not None and m_ is not getattr(scene_, 'mesh', None):
                job['into'] = (m_, None)      # a wall in a group: the walling joins that group's mesh
        nf = self.add_jobs(viewport, [job], p['new_group'])
        if nf is None:
            return None
        st = res['stats']
        msg = "%s: %d units" % (mat_name, st['units'])
        if st['quoins']:
            msg += ", %d quoins/heads/sills" % st['quoins']
        if st['copings']:
            msg += ", %d coping pieces" % st['copings']
        if st['removed']:
            msg += "; %d knocked out by the damage" % st['removed']
        if st.get('hanging'):
            msg += " (%d of them left hanging, so taken out)" % st['hanging']
        if n_loose:
            msg += "; %d loose pieces at the foot" % n_loose
        msg += ". %d faces." % nf
        if job.get('into'):
            msg += " Built into the wall's own group."
        if remove:
            msg += " Deleted the face under them."
        elif p.get('ruin') or p.get('holes_n') or p.get('miss_through'):
            msg += (" The face is still whole behind the damage: tick 'Delete the face' (with a backing "
                    "sheet) to see the broken top and holes.")
        if (p.get('through') or p.get('miss_through')) and not p.get('backing'):
            msg += " To see right through, set a backing sheet thickness: the holes are cut through that."
        if self._errors[0]:
            msg += " %d faces could not be made (%s)." % self._errors
        try:
            viewport.flash_status("%s: %d units, %d faces" % (PLUGIN_NAME, st['units'], nf), 3000)
        except Exception:
            pass
        return (msg, bool(self._errors[0]))

    def _layout_parts(self, face, vals):
        """Everything for one wall face, ready to add: dict(parts, top, remove, rec, ...), or
        (message, True) if nothing fits."""
        p = _full(vals)
        fr = self._frame(face, p['swap'])
        if fr is None:
            return ("That face has too few corners.", True)
        W, H = fr['W'], fr['H']
        metres = max(W, H) < 50.0
        if metres:
            p = _to_metres(p)        # every size in the window is in mm; this wall is drawn in metres
        if p.get('soldier_len') is None:
            p['soldier_len'] = p['length']
        gap = p.get('hole_gap') or 0.0
        holes = [_grow(h, gap) if gap > 0 else h for h in fr['holes']]   # units stop a hair short
        _course_from_ground(p, fr)
        res = wall_units(p, W, H, fr['outline'], holes, fr['hole_ids'], self._seed(fr))
        to_w = self._mapper(fr)
        mat = p['material']
        mat_name = MATERIAL_NAMES.get(mat, "Walling").split(" (")[0]

        def solids(units):
            out = []
            for u in units:
                out.append(to_w(unit_faces(u, p['back_faces'])))
            return out
        parts = []
        if res['walling']:
            parts.append(("Walling - %s (%d)" % (mat_name, len(res['walling'])), solids(res['walling'])))
        if res['quoins']:
            parts.append(("Quoins (%d)" % len(res['quoins']), solids(res['quoins'])))
        if res['dressings']:
            parts.append(("Heads and sills (%d)" % len(res['dressings']), solids(res['dressings'])))
        if res['copings']:
            parts.append(("Coping (%d)" % len(res['copings']), solids(res['copings'])))
        if res['backing']:
            T = p['backing']
            ov = min(p['depth'] * 0.3, 0.05 * (0.001 if metres else 1.0))   # just into the units
            parts.append(("Backing", [to_w(slab_with_holes(o_, h_, -T, ov)) for o_, h_ in res['backing']]))
        n_loose = 0
        if p.get('foot') and res['removed']:
            to_f = self._mapper(fr, ('u', 'n', 'v'))
            loose = foot_rubble(p, W, res['removed'], self._seed(fr))
            if loose:
                parts.append(("Rubble (%d)" % len(loose), [to_f(plain(s)) for _, s in loose]))
                n_loose = len(loose)
        if not parts:
            return ("Nothing fitted on that face (is it smaller than one unit?).", True)
        top = "%s - %s" % ("3D Brick & Block Work" if mat == 'brick' else "3D Stone Work", mat_name)
        real = getattr(face, 'obj', face)            # a wall found on the Whole building page
        remove = [real] if p.get('remove_face') else []
        c = _mid([_pos3(vertex_to_vector3d(v)) for v in face.vertices])   # the middle of the face's box
        rec = {'at': [round(c[0], 7), round(c[1], 7), round(c[2], 7)],
               'n': [round(fr['n'].x(), 5), round(fr['n'].y(), 5), round(fr['n'].z(), 5)],
               'size': max(W, H), 'material': mat}
        into = None
        if p.get('join_wall'):
            into = getattr(face, 'into', None)
            if into is not None and into[1] is False:
                into = None
        return {'parts': parts, 'top': top, 'remove': remove, 'rec': rec, 'p': p, 'res': res,
                'n_loose': n_loose, 'mat_name': mat_name, 'into': into}

    def brick_walls_from_dialog(self, dialog):
        """Whole building page: walling on every ticked wall, all in one Undo."""
        walls = dialog.ticked_walls()
        if not walls:
            QMessageBox.information(dialog, PLUGIN_NAME, "Click Find, then tick the walls that get walling.")
            return
        vals = dialog.get_values()
        self._remember(vals)
        vals['soldier_holes'] = None          # every opening in every wall is dressed
        jobs, bad, units = [], [], 0
        for w in walls:
            for k_, face in enumerate([w['face']] + list(getattr(w['face'], 'more', []))):
                try:
                    job = self._layout_parts(face, vals)
                except Exception as e:
                    bad.append("%s (%s)" % (w['name'], e))
                    continue
                if isinstance(job, tuple):
                    if k_ == 0:
                        bad.append("%s (%s)" % (w['name'], job[0]))
                    continue
                job['top'] = "%s - %s" % (job['top'], w['name'])
                if k_ and job.get('rec'):
                    job['rec'] = None             # the main face carries the record
                jobs.append(job)
                units += job['res']['stats']['units']
        if not jobs:
            dialog.show_report("Nothing was built: " + "; ".join(bad), True)
            return
        nf = self.add_jobs(dialog.viewport, jobs, vals.get('new_group', True))
        if nf is None:
            return
        msg = "Walling on %d wall%s: %d units, %d faces." % (len(jobs), "" if len(jobs) == 1 else "s", units, nf)
        if bad:
            msg += " Skipped: " + "; ".join(bad) + "."
        if self._errors[0]:
            msg += " %d faces could not be made (%s)." % self._errors
        dialog.show_report(msg, bool(bad or self._errors[0]))
        dialog.wall = None
        dialog.find_walls()                   # the walls just done now show 'has walling'
        try:
            dialog.viewport.flash_status("%s: %d walls, %d units" % (PLUGIN_NAME, len(jobs), units), 3000)
        except Exception:
            pass

    def make_pile_on(self, viewport, face, vals):
        p = _full(vals)
        fr = self._frame(face, False)
        if fr is None:
            return ("That face has too few corners.", True)
        if max(fr['W'], fr['H']) < 50.0:
            p = _to_metres(p)
        core, pieces = make_pile(p, fr['outline'], self._seed(fr))
        to_w = self._mapper(fr)
        parts = []
        if core:
            parts.append(("Rubble core", [to_w(plain(core))]))
        special = ('timber', 'barrel', 'crate', 'custom')
        loose = [s for k, s in pieces if k not in special]
        if loose:
            parts.append(("Loose pieces (%d)" % len(loose), [to_w(plain(s)) for s in loose]))
        for kind, title in (('timber', "Planks and timbers"), ('barrel', "Barrels"), ('crate', "Crates"),
                            ('custom', vals.get('_custom_name') or "Your object")):
            got = [s for k, s in pieces if k == kind]
            if got:
                parts.append(("%s (%d)" % (title, len(got)), [to_w(plain(s)) for s in got]))
        if not parts:
            return ("No pile could be made: try more pieces, or a taller pile.", True)
        mat_name = MATERIAL_NAMES.get(p['material'], "").split(" (")[0].lower()
        nf = self.add_to_scene(viewport, parts, "Rubble pile - %s" % mat_name, True, [])
        if nf is None:
            return None
        msg = "Rubble pile: %d pieces%s, %d faces." % (len(pieces), " on a solid core" if core else "", nf)
        if int(p.get('pile_custom') or 0) > 0 and not p.get('_custom'):
            msg += " (No object of your own was added: pick one first with 'Use selected object'.)"
        if self._errors[0]:
            msg += " %d faces could not be made (%s)." % self._errors
        return (msg, bool(self._errors[0]))

    def add_to_scene(self, viewport, parts, top_name, new_group=True, remove=(), rec=None):
        """One parent group holding a child group per part (walling, quoins, copings,
        backing, rubble). The geometry is already in place, so no transforms are needed.
        new_group off: everything goes into the loose geometry, as before."""
        return self.add_jobs(viewport, [{'parts': parts, 'top': top_name, 'remove': list(remove), 'rec': rec}],
                             new_group)

    def add_jobs(self, viewport, jobs, new_group=True):
        """Adds the walling for one or more walls in one Undo step: for each, a parent group
        holding a child group per part, marked with where its wall face is (so the Whole
        building page knows that wall has walling)."""
        stats = {'faces': 0, 'errors': 0, 'err': None}
        tol = 1e-7

        def fill(mesh, solids, xf=None, attrs=None):
            for so in solids:
                verts = {}

                def vx(p_):
                    if xf is not None:
                        q_ = xf.map(QVector3D(*p_))
                        p_ = (q_.x(), q_.y(), q_.z())
                    k = (round(p_[0] / tol), round(p_[1] / tol), round(p_[2] / tol))
                    if k not in verts:
                        verts[k] = VertexWrapper(*p_)
                    return verts[k]
                for outer, holes in so:
                    made = []
                    try:
                        if holes:
                            hs = [[vx(q) for q in h] for h in holes]
                            try:
                                made.append(mesh.add_face([vx(q) for q in outer], hs))
                            except TypeError:          # an older IngeTrazo: holes one by one
                                f_ = mesh.add_face([vx(q) for q in outer])
                                for h in hs:
                                    mesh.add_hole(f_, h)
                                made.append(f_)
                        elif TRIANGULATE_FRONT and len(outer) > 4:
                            vs = [vx(q) for q in outer]
                            for i in range(1, len(vs) - 1):
                                made.append(mesh.add_face([vs[0], vs[i], vs[i + 1]]))
                        else:
                            made.append(mesh.add_face([vx(q) for q in outer]))
                        stats['faces'] += 1
                    except Exception as e:
                        stats['errors'] += 1
                        stats['err'] = e
                    if attrs:
                        for f_ in made:
                            try:
                                f_.attrs = dict(attrs)
                            except Exception:
                                pass

        def make_group(Group, mesh, name):
            try:
                g = Group(mesh, name=name)
            except TypeError:
                g = Group(name)
                g.mesh = mesh
            try:
                g.name = name
            except Exception:
                pass
            try:
                g.component = False
            except Exception:
                pass
            return g

        def mark(g, rec):
            if not rec:
                return
            try:
                ext = getattr(g, 'ext', None)
                if not isinstance(ext, dict):
                    g.ext = {}
                    ext = g.ext
                ext[REC_KEY] = dict(rec)
            except Exception:
                pass

        def mutate(scene):
            from core.mesh import Mesh
            from core.group import Group
            if not new_group:
                target = getattr(scene, 'mesh', None) or getattr(viewport, 'mesh', None)
                if target is not None:
                    for job in jobs:
                        into = job.get('into')
                        for name_, solids in job['parts']:
                            if into is not None and not name_.startswith("Rubble ("):
                                fill(into[0], solids, into[1], _part_attrs(scene, name_))
                            else:
                                fill(target, solids)
                    if stats['faces'] == 0:
                        raise RuntimeError("No faces could be created (%s)." % stats['err'])
                    for f, m_ in targets:
                        remove_face(scene, m_, f)
                    return
            to_add = []
            for job in jobs:
                kids = []
                into = job.get('into')
                for name, solids in job['parts']:
                    if into is not None and not name.startswith("Rubble ("):
                        # built into the wall: its own mesh, in its own terms, painted part by part
                        fill(into[0], solids, into[1], _part_attrs(scene, name))
                        continue
                    mesh = Mesh()
                    fill(mesh, solids)
                    kids.append(make_group(Group, mesh, name))
                parent = None
                if len(kids) > 1:
                    try:
                        parent = Group(name=job['top'])
                        if hasattr(parent, 'adopt'):
                            parent.adopt(kids)
                        else:
                            parent.children = kids
                        parent.component = False
                    except Exception:
                        parent = None          # an older IngeTrazo: add them side by side
                elif kids:
                    try:
                        kids[0].name = job['top']
                    except Exception:
                        pass
                for g in ([parent] if parent is not None else kids):
                    to_add.append((g, job.get('rec'), parent is None))
            if stats['faces'] == 0:
                raise RuntimeError("No faces could be created (%s)." % stats['err'])
            for g, rec, loose in to_add:
                mark(g, rec)
                _ed3d_organise(scene, g)
                if hasattr(scene, 'add_group') and loose:
                    scene.add_group(g)
                else:
                    scene.groups.append(g)
            for f, m_ in targets:
                remove_face(scene, m_, f)

        scene0 = getattr(viewport, 'scene', None)
        remove = []
        for job in jobs:
            remove += list(job.get('remove') or [])
        targets = [(f, mesh_of_face(scene0, f)) for f in remove] if scene0 is not None else []
        targets = [(f, m_) for f, m_ in targets if m_ is not None]
        try:
            meshes = list({id(m_): m_ for _, m_ in targets}.values())
            for job in jobs:                       # walls the walling is built into
                if job.get('into') is not None and all(job['into'][0] is not m_ for m_ in meshes):
                    meshes.append(job['into'][0])
            if not new_group:
                tm = getattr(scene0, 'mesh', None)
                if tm is not None and all(tm is not m_ for m_ in meshes):
                    meshes.append(tm)
            viewport.history.execute(make_command(mutate, meshes) if meshes else SnapshotImport(mutate))
        except Exception as e:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not add it:\n%s" % e)
            return None
        try:
            viewport.notify_scene_changed()
        except Exception:
            pass
        self._errors = (stats['errors'], stats['err'])
        return stats['faces']

    _errors = (0, None)


def run(viewport=None):
    BrickBlockStudioTool().on_activate(viewport)
