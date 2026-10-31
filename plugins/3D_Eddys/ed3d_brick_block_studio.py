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
3D Brick & Block Studio - Brickwork Generator for IngeTrazo
Bonds, header courses, selectable soldier courses, row offset control, brick and block size presets.
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
    QInputDialog, QListWidget, QListWidgetItem, QLineEdit, QLabel, QWidget
)

PLUGIN_NAME = "3D Brick & Block Studio"

MERGE_PIECES = True
TRIANGULATE_FRONT = False   # True if Mesh.add_face rejects polygons with >4 points

# ---------------------------------------------------------------------------
# Presets (stored in millimetres, converted to the wall's unit when used)
# ---------------------------------------------------------------------------
PRESET_FILE = os.path.join(os.path.expanduser("~"), ".brick_block_studio_presets.json")
# older preset files are read if the new one does not exist yet, so nothing is lost
LEGACY_PRESET_FILES = [
    os.path.join(os.path.expanduser("~"), ".aparejo_presets.json"),
    os.path.join(os.path.expanduser("~"), ".eddys_bricks_presets.json"),
]

BUILTIN_PRESETS = {
    "Brick slip 210 x 65 x 20": {'length': 210.0, 'height': 65.0, 'depth': 20.0, 'joint': 10.0, 'header_len': 100.0},
    "UK standard brick 215 x 65 x 102.5": {'length': 215.0, 'height': 65.0, 'depth': 102.5, 'joint': 10.0, 'header_len': 102.5},
    "German NF brick 240 x 71 x 115": {'length': 240.0, 'height': 71.0, 'depth': 115.0, 'joint': 10.0, 'header_len': 115.0},
    "US modular brick 194 x 57 x 92": {'length': 194.0, 'height': 57.0, 'depth': 92.0, 'joint': 10.0, 'header_len': 92.0},
    "Concrete block 440 x 215 x 100": {'length': 440.0, 'height': 215.0, 'depth': 100.0, 'joint': 10.0, 'header_len': 215.0},
    "Concrete block 390 x 190 x 190": {'length': 390.0, 'height': 190.0, 'depth': 190.0, 'joint': 10.0, 'header_len': 190.0},
}


# Sizes the generator uses when nothing else is set (millimetres)
DEFAULT_SIZES_MM = {'length': 210.0, 'height': 65.0, 'depth': 20.0, 'joint': 10.0,
                    'min_frag': 20.0, 'header_len': 100.0}
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


def _subtract_concave(poly, hole, subdiv):
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
            else:
                nxt.extend(_subtract_concave(pc, hole, subdiv))
        pieces = nxt
        if not pieces:
            break
    if MERGE_PIECES and len(pieces) > 1:
        pieces = _merge(pieces, ext * 1e-7)
    min_area = min_frag * min_frag * 0.5
    return [pc for pc in pieces if len(pc) >= 3 and abs(_area(pc)) >= min_area]


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
                offset_seed, offset_rmax, W, H, tiny=0.0, segments=None, min_end=0.0, x0=0.0):
    """Every brick rectangle of the bond over a W x H panel, before any trimming:
    [(x1, y1, x2, y2, is_header)]. Used by both the generator and the preview.
    segments(y1, y2) gives the runs of wall a course is laid in (between openings); with
    min_end, the bricks at the two ends of each run are evened up so there are no slivers.
    x0 lines the bond up: a course with no offset has a brick starting there."""
    out = []
    prev_joints = []
    step_y = w + J
    rows = int(math.ceil(H / step_y)) + 1
    offs = _row_offsets(offset_mode, rows, l + J, offset_fixed, offset_seq, offset_seed, offset_rmax)
    for r in range(rows):
        y = r * step_y
        if y >= H:
            continue
        cw = w if y + w <= H else max(0.0005, H - y)
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
        runs = segments(y, y + cw) if segments is not None else [(0.0, W)]
        joints = []
        for a, b in runs:
            a, b = max(a, 0.0), min(b, W)
            pcs = [(max(sx, a), min(ex, b), hd) for sx, ex, hd in row if ex > a and sx < b]
            pcs = [pc for pc in pcs if pc[1] - pc[0] >= max(tiny, 1e-12)]
            pcs = _even_ends(pcs, J, min_end, prev_joints)
            for x1, x2, hd in pcs:
                if x2 - x1 >= tiny:
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

EDDY_TIPS = {'Length': 'The length of one brick or block.',
 'Height': 'The height of one brick or block.',
 'Depth': 'How far the bricks stand out from the wall.',
 'Mortar joint': 'The gap between bricks. For printing use about your nozzle width.',
 'Bond': 'The pattern the bricks are laid in: stretcher, English, Flemish and so on.',
 'Row offsets': 'How far each course is moved along: as the bond says, a fixed amount every '
                '2nd course, your own sequence, or at random.',
 'Header courses': 'Puts a course of headers (brick ends) in every so many courses.',
 'Header width': 'The width of a header (the end of a brick).',
 'Soldier course round openings': 'Bricks stood on end round the openings you tick below.',
 'Soldier length': 'How tall the soldier bricks are.',
 'Corner angle (deg)': 'Where the outline of an opening turns more sharply than this, it '
                       'counts as a corner and gets a corner brick.',
 'Soldier course over': 'Tick the openings that get a soldier course.',
 '@lst_open': 'The openings found in this face. Tick the ones that get a soldier course.',
 'All': 'Ticks all the openings.',
 'None': 'Unticks all the openings.',
 'Bricks': 'Brick size, mortar and presets.',
 'Openings': 'Soldier courses round windows and doors.',
 'Weathering': 'Make it old: bricks kicked out of line.'}
EDDY_TIPS_END = None


class BondPreview(QWidget):
    """A small elevation of the bond: bricks on mortar, header bricks darker."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 170)
        self.rects, self.W, self.H = [], 1.0, 1.0

    def set_layout(self, rects, W, H):
        self.rects, self.W, self.H = rects, W, H
        self.update()

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen
        from PySide6.QtCore import QRectF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(245, 245, 243))
        m = 6
        sc = min((self.width() - 2 * m) / self.W, (self.height() - 2 * m) / self.H)
        ox = (self.width() - self.W * sc) / 2
        oy = (self.height() + self.H * sc) / 2
        p.fillRect(QRectF(ox, oy - self.H * sc, self.W * sc, self.H * sc), QColor(215, 209, 196))
        p.setPen(QPen(QColor(110, 52, 35), 0.6))
        for x1, y1, x2, y2, head in self.rects:
            p.setBrush(QColor(140, 62, 42) if head else QColor(181, 86, 60))
            p.drawRect(QRectF(ox + x1 * sc, oy - y2 * sc, (x2 - x1) * sc, (y2 - y1) * sc))
        p.end()


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


def find_openings(wall, others, unit_label, k=1.0):
    """Returns (list of (hole_index, label), preselected set or None).
    k turns the wall's own units into the ones shown (1000 for a wall drawn in metres)."""
    fr = _face_frame(wall)
    holes = getattr(wall, 'holes', None) or []
    if fr is None or not holes:
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
        info.append((hi, "Opening %d: %.0f x %.0f %s, at (%.0f, %.0f)"
                     % (n + 1, (x1 - x0) * k, (y1 - y0) * k, unit_label, (x0 - min_u) * k,
                        (y0 - min_v) * k)))
    return info, (sel if sel else None)


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


class _TabForms:
    """Rows for a form, put on named tabs: tab("Name") picks the tab the next rows go on."""

    def __init__(self):
        from PySide6.QtWidgets import QTabWidget
        self.tabs = QTabWidget()
        self.pages = {}
        self.cur = None

    def tab(self, title):
        if title not in self.pages:
            page = QWidget()
            fl = QFormLayout(page)
            for name, pol in (('setRowWrapPolicy', 'WrapLongRows'),      # stays narrow: long rows wrap
                              ('setFieldGrowthPolicy', 'AllNonFixedFieldsGrow')):
                try:
                    enum = getattr(QFormLayout, pol, None)
                    if enum is None:
                        grp = 'RowWrapPolicy' if pol == 'WrapLongRows' else 'FieldGrowthPolicy'
                        enum = getattr(getattr(QFormLayout, grp), pol)
                    getattr(fl, name)(enum)
                except Exception:
                    pass
            fl.setHorizontalSpacing(6)
            fl.setVerticalSpacing(4)
            self.pages[title] = fl
            self.tabs.addTab(page, title)
        self.cur = self.pages[title]

    def addRow(self, *args):
        if self.cur is None:
            self.tab("Settings")
        self.cur.addRow(*args)


class BrickDialog(QDialog):
    CUSTOM = "-- Custom --"

    def __init__(self, cur, unit_label, openings, preselected, parent=None, tool=None, viewport=None):
        super().__init__(parent)
        self.setWindowTitle("%s (%s)" % (PLUGIN_NAME, unit_label))
        self.setModal(False)
        self.tool = tool
        self.viewport = viewport
        self.wall = None           # the wall face the openings list belongs to
        self.unit_factor = 0.001 if unit_label == "m" else 1.0
        self.user_presets = load_user_presets()

        lay = QVBoxLayout(self)
        form = _TabForms()             # the settings go on tabs, like the windows plugin

        f = self.unit_factor
        mm_units = unit_label != "m"
        self.unit_label = unit_label

        def default(key):
            return DEFAULT_SIZES_MM[key] * f

        def dsp(val, key, allow_zero=False):
            s = QDoubleSpinBox()
            s.setDecimals(1 if mm_units else 4)
            s.setRange(0.0 if allow_zero else (0.1 if mm_units else 0.0001), 100000.0)
            s.setSuffix(" " + unit_label)
            s.setValue(val if val is not None else default(key))
            return s

        self.sp_len = dsp(cur['length'], 'length')
        self.sp_hgt = dsp(cur['height'], 'height')
        self.sp_dep = dsp(cur['depth'], 'depth')
        self.sp_joint = dsp(cur['joint'], 'joint', allow_zero=True)
        self.sp_frag = dsp(cur['min_frag'], 'min_frag', allow_zero=True)

        # ---- preset row ----
        self.cb_preset = QComboBox()
        self.btn_save = QPushButton("Save")
        self.btn_save.setToolTip("Updates the preset you have open (no typing). For a new preset, "
                                 "use Save as.")
        self.btn_saveas = QPushButton("Save as...")
        self.btn_delete = QPushButton("Delete")
        preset_row = QVBoxLayout()
        preset_row.addWidget(self.cb_preset)
        prow2 = QHBoxLayout()
        for b_ in (self.btn_save, self.btn_saveas, self.btn_delete):
            prow2.addWidget(b_)
        prow2.addStretch(1)
        preset_row.addLayout(prow2)
        _compact_combo(self.cb_preset, 14)
        self.refresh_presets()
        self.cb_preset.currentIndexChanged.connect(self.apply_preset)
        self.btn_save.clicked.connect(self.save_preset)
        self.btn_saveas.clicked.connect(lambda: self.save_preset_as())
        self.btn_delete.clicked.connect(self.delete_preset)

        # ---- bond ----
        self.cb_bond = QComboBox()
        self.bonds = [("Running bond", "running"), ("Stack bond", "stack"),
                      ("Third bond", "third"), ("English bond", "english"),
                      ("Flemish bond", "flemish")]
        for i, (label, key) in enumerate(self.bonds):
            self.cb_bond.addItem(label, key)
            if key == cur['bond']:
                self.cb_bond.setCurrentIndex(i)

        # ---- row offsets ----
        self.cb_off = QComboBox()
        self.offmodes = [("Follow the bond", "bond"),
                         ("Fixed, every 2nd course", "fixed"),
                         ("Custom sequence", "sequence"),
                         ("Random per course", "random")]
        for i, (label, key) in enumerate(self.offmodes):
            self.cb_off.addItem(label, key)
            if key == cur['offset_mode']:
                self.cb_off.setCurrentIndex(i)
        self.sp_ofix = QDoubleSpinBox()
        self.sp_ofix.setDecimals(3)
        self.sp_ofix.setRange(0.0, 1.0)
        self.sp_ofix.setSingleStep(0.05)
        self.sp_ofix.setValue(cur['offset_fixed'])
        self.le_seq = QLineEdit(cur['offset_seq'])
        self.le_seq.setToolTip("Fractions of a unit (length + joint), repeated down the wall. Example: 0, 0.5, 0.25, 0.75")
        self.sp_seed = QSpinBox()
        self.sp_seed.setRange(0, 999999)
        self.sp_seed.setValue(cur['offset_seed'])
        self.sp_rmax = QDoubleSpinBox()
        self.sp_rmax.setDecimals(2)
        self.sp_rmax.setRange(0.05, 1.0)
        self.sp_rmax.setSingleStep(0.05)
        self.sp_rmax.setValue(cur['offset_rmax'])

        def sync_off(_i=None):
            m = self.cb_off.currentData()
            self.sp_ofix.setEnabled(m == "fixed")
            self.le_seq.setEnabled(m == "sequence")
            self.sp_seed.setEnabled(m == "random")
            self.sp_rmax.setEnabled(m == "random")
        self.cb_off.currentIndexChanged.connect(sync_off)
        sync_off()

        # ---- headers ----
        self.cb_head = QCheckBox("Header courses")
        self.cb_head.setChecked(bool(cur['header_every']))
        self.sp_every = QSpinBox()
        self.sp_every.setRange(2, 50)
        self.sp_every.setValue(cur['header_every'] or 5)
        self.sp_hlen = dsp(cur['header_len'], 'header_len')

        def sync_head(on):
            self.sp_every.setEnabled(on)
            self.sp_hlen.setEnabled(on)
        self.cb_head.toggled.connect(sync_head)
        sync_head(self.cb_head.isChecked())

        # ---- soldier course + opening picker ----
        self.cb_sold = QCheckBox("Soldier course round openings")
        self.cb_sold.setChecked(bool(cur['soldier']))
        # Soldier length follows the unit length until you change it yourself
        self.sp_slen = dsp(cur['soldier_len'] if cur['soldier_len'] is not None else self.sp_len.value(),
                           'length')
        self._sold_linked = cur['soldier_len'] is None
        self._syncing = False

        def len_changed(v):
            if self._sold_linked:
                self._syncing = True
                self.sp_slen.setValue(v)
                self._syncing = False

        def slen_changed(_v):
            if not self._syncing:
                self._sold_linked = False
        self.sp_len.valueChanged.connect(len_changed)
        self.sp_slen.valueChanged.connect(slen_changed)
        self.sp_ang = QDoubleSpinBox()
        self.sp_ang.setRange(1.0, 89.0)
        self.sp_ang.setValue(cur['corner_angle'])

        self.lst_open = QListWidget()
        self.lst_open.setMaximumHeight(80)
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
        pick_box.addWidget(QLabel("Soldier course over:"))
        pick_box.addWidget(self.lst_open)
        pick_box.addLayout(pick_row)

        def sync_sold(on):
            self.sp_slen.setEnabled(on)
            self.sp_ang.setEnabled(on)
            self.lst_open.setEnabled(on)
            self.btn_all.setEnabled(on)
            self.btn_none.setEnabled(on)
        self.cb_sold.toggled.connect(sync_sold)
        sync_sold(self.cb_sold.isChecked())

        self.sp_sub = QSpinBox()
        self.sp_sub.setRange(1, 16)
        self.sp_sub.setValue(cur['subdiv'])
        self.cb_back = QCheckBox()
        self.cb_back.setChecked(cur['back_faces'])
        self.cb_swap = QCheckBox()
        self.cb_swap.setChecked(cur['swap'])
        self.cb_group = QCheckBox()
        self.cb_group.setChecked(cur['new_group'])

        form.tab("Bricks")
        form.addRow("Preset:", preset_row)
        form.tab("Bond")
        form.addRow("Bond:", self.cb_bond)
        form.addRow("Row offsets:", self.cb_off)
        self.sp_ofix.setToolTip("Fixed offset, as a fraction of a unit (length + joint).")
        self.sp_rmax.setToolTip("The most a course is offset at random, as a fraction of a unit.")
        form.addRow("   Fixed offset:", self.sp_ofix)
        form.addRow("   Sequence:", self.le_seq)
        form.addRow("   Random seed:", self.sp_seed)
        form.addRow("   Max random offset:", self.sp_rmax)
        self.preview = BondPreview()
        self.preview.setMinimumSize(240, 130)
        self.preview.setMaximumHeight(170)
        cap = QLabel("Bond preview (darker = headers)")
        cap.setStyleSheet("color: gray;")
        form.addRow(self.cb_head)
        self.sp_every.setToolTip("A header course every this many courses.")
        form.addRow("   Every Nth course:", self.sp_every)
        form.addRow("   Header width:", self.sp_hlen)
        form.tab("Openings")
        form.addRow(self.cb_sold)
        form.addRow(pick_box)
        form.addRow("   Soldier length:", self.sp_slen)
        form.addRow("   Corner angle (deg):", self.sp_ang)
        form.tab("Bricks")
        form.addRow("Length:", self.sp_len)
        form.addRow("Height:", self.sp_hgt)
        form.addRow("Depth:", self.sp_dep)
        form.addRow("Mortar joint:", self.sp_joint)
        form.tab("Openings")
        self.sp_frag.setToolTip("Cut pieces of brick smaller than this are left out.")
        form.addRow("Smallest cut piece:", self.sp_frag)
        self.sp_hgap = QDoubleSpinBox()
        self.sp_hgap.setDecimals(3)
        self.sp_hgap.setRange(0.0, 50.0)
        self.sp_hgap.setSuffix(" mm")
        self.sp_hgap.setValue(cur.get('hole_gap', 0.01) if cur.get('hole_gap') is not None else 0.01)
        self.sp_hgap.setToolTip("Bricks stop this far short of every opening (and the window, sill "
                                "and head in it), so they don't touch: slicers get confused by faces "
                                "lying exactly on top of each other. 0.01 mm is plenty.")
        form.addRow("Gap round openings:", self.sp_hgap)

        self.cb_even = QCheckBox()
        self.cb_even.setChecked(bool(cur.get('even_ends', True)))
        self.cb_even.setToolTip("Lines the bond up with the first opening (courses beside it end in a "
                                "whole brick and a half brick in turn), and where a course would still "
                                "end in a thin sliver, takes length from the next brick so neither is "
                                "a sliver. No brick is ever made longer than a standard one.")
        self.sp_mine = QDoubleSpinBox()
        self.sp_mine.setDecimals(0)
        self.sp_mine.setRange(10.0, 90.0)
        self.sp_mine.setSuffix(" %")
        self.sp_mine.setValue(float(cur.get('min_end_pct', 50.0) or 50.0))
        self.sp_mine.setToolTip("An end piece shorter than this (% of a brick) borrows length from the next brick.")
        self.cb_even.toggled.connect(self.sp_mine.setEnabled)
        self.sp_mine.setEnabled(self.cb_even.isChecked())
        form.addRow("Even up the ends:", self.cb_even)
        form.addRow("   Smallest end:", self.sp_mine)

        self.cb_kick = QCheckBox()
        self.cb_kick.setChecked(bool(cur.get('kick', False)))
        self.cb_kick.setToolTip("A few bricks, picked at random, stand out from the wall a little, "
                                "like old weathered brickwork. Their backs stay on the wall.")
        self.sp_kpct = QDoubleSpinBox()
        self.sp_kpct.setDecimals(0)
        self.sp_kpct.setRange(1.0, 100.0)
        self.sp_kpct.setSuffix(" %")
        self.sp_kpct.setValue(float(cur.get('kick_pct', 8.0) or 8.0))
        self.sp_kmm = QDoubleSpinBox()
        self.sp_kmm.setDecimals(2)
        self.sp_kmm.setRange(0.01, 100.0)
        self.sp_kmm.setSuffix(" mm")
        self.sp_kmm.setValue(float(cur.get('kick_mm', 3.0) or 3.0))
        self.sp_kmm.setToolTip("The most a brick sticks out (each one is a random amount up to this).")
        self.sp_kseed = QSpinBox()
        self.sp_kseed.setRange(0, 999999)
        self.sp_kseed.setValue(int(cur.get('kick_seed', 1) or 0))
        self.sp_kseed.setToolTip("Change this for a different random pick of bricks.")

        def sync_kick(on):
            for w_ in (self.sp_kpct, self.sp_kmm, self.sp_kseed):
                w_.setEnabled(on)
        self.cb_kick.toggled.connect(sync_kick)
        sync_kick(self.cb_kick.isChecked())
        form.tab("Weathering")
        self.sp_kpct.setToolTip("The share of bricks that stick out.")
        form.addRow("Kick-out bricks:", self.cb_kick)
        form.addRow("   How many:", self.sp_kpct)
        form.addRow("   By up to:", self.sp_kmm)
        form.addRow("   Pattern no.:", self.sp_kseed)
        form.tab("Openings")
        self.sp_sub.setToolTip("How finely openings with curved or concave edges are cut round.")
        form.addRow("Subdivisions:", self.sp_sub)
        self.cb_back.setToolTip("Gives every brick a back face so it is a closed solid. Leave this on "
                                "for 3D printing: without it the slicer sees open edges and its "
                                "repair can damage the rest of the model.")
        form.tab("Bricks")
        self.cb_swap.setToolTip("Swap the wall's width and height directions.")
        self.cb_group.setToolTip("Put the bricks in a new group of their own.")
        form.addRow("Closed bricks:", self.cb_back)
        form.addRow("Swap axes:", self.cb_swap)
        form.addRow("New group:", self.cb_group)
        # what's selected goes at the top, the preview on the left, the tabs on the right
        self.lbl_face = QLabel()
        self.lbl_face.setWordWrap(True)
        self.lbl_face.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl_face)
        lay.addWidget(self.preview)
        lay.addWidget(cap)
        lay.addWidget(form.tabs, 1)
        lay.setSpacing(4)
        lay.setContentsMargins(8, 8, 8, 8)
        for cb_ in (self.cb_bond, self.cb_off):
            _compact_combo(cb_, 12)
        self.setMaximumWidth(460)
        self.select_matching_preset()

        # keep the preview up to date
        for w_ in (self.cb_bond, self.cb_off):
            w_.currentIndexChanged.connect(self.update_preview)
        for w_ in (self.sp_ofix, self.sp_seed, self.sp_rmax, self.sp_every, self.sp_hlen,
                   self.sp_len, self.sp_hgt, self.sp_joint):
            w_.valueChanged.connect(self.update_preview)
        self.le_seq.textChanged.connect(self.update_preview)
        self.cb_head.toggled.connect(self.update_preview)
        self.cb_even.toggled.connect(self.update_preview)
        self.sp_mine.valueChanged.connect(self.update_preview)
        self.update_preview()

        # the window stays open: select a face, click Apply, select the next one ...
        brow = QHBoxLayout()
        self.btn_apply = QPushButton("Apply to face")
        self.btn_apply.setToolTip("Fills the selected face (a wall) with bricks or blocks.")
        self.btn_apply.setDefault(True)
        btn_close = QPushButton("Close")
        brow.addWidget(self.btn_apply)
        brow.addStretch(1)
        brow.addWidget(btn_close)
        lay.addLayout(brow)
        self.btn_apply.clicked.connect(self.apply_clicked)
        btn_close.clicked.connect(self.close)

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

    def read_selection(self):
        """Picks up the selected face; refreshes the openings list if it's a new wall."""
        sel = _selected_wall(self.viewport)
        if sel is None:
            self.lbl_face.setText("Select a face (a wall), then click 'Apply to face'.")
            return None
        wall, others, unit_label = sel
        if wall is not self.wall:
            openings, pre = find_openings(wall, others, "mm", 1000.0 if unit_label == "m" else 1.0)
            self.fill_openings(openings, pre)
            self.wall = wall
        n = len(getattr(wall, 'holes', None) or [])
        self.lbl_face.setText("Selected face: %d opening%s. Click 'Apply to face'. "
                              "All sizes are in mm." % (n, "" if n == 1 else "s"))
        return sel

    def apply_clicked(self):
        if self.tool is not None:
            self.tool.apply_from_dialog(self)

    def changeEvent(self, e):
        try:
            from PySide6.QtCore import QEvent
            if e.type() == QEvent.ActivationChange and self.isActiveWindow():
                self.read_selection()
        except Exception:
            pass
        super().changeEvent(e)

    def update_preview(self, *_):
        l, w, J = self.sp_len.value(), self.sp_hgt.value(), self.sp_joint.value()
        hl = self.sp_hlen.value()
        W = 6 * (l + J) - J               # a sample panel about 6 bricks wide, 12 courses high
        H = 12 * (w + J) - J
        try:
            rects = bond_layout(l, w, J, hl, self.cb_bond.currentData(),
                                self.sp_every.value() if self.cb_head.isChecked() else 0,
                                self.cb_off.currentData(), self.sp_ofix.value(), self.le_seq.text(),
                                self.sp_seed.value(), self.sp_rmax.value(), W, H,
                                min_end=(self.sp_mine.value() / 100.0 * l) if self.cb_even.isChecked() else 0.0)
        except Exception:
            rects = []
        self.preview.set_layout(rects, W, H)

    def set_all(self, state):
        for i in range(self.lst_open.count()):
            it = self.lst_open.item(i)
            if it.data(Qt.UserRole) is not None:
                it.setCheckState(state)

    # ---- preset handling ----
    def all_presets(self):
        d = dict(BUILTIN_PRESETS)
        d.update(self.user_presets)
        return d

    def refresh_presets(self, select=None):
        self.cb_preset.blockSignals(True)
        self.cb_preset.clear()
        self.cb_preset.addItem(self.CUSTOM, None)
        for name in BUILTIN_PRESETS:
            self.cb_preset.addItem(name + "  (built-in)", name)
        for name in sorted(self.user_presets):
            if name not in BUILTIN_PRESETS:
                self.cb_preset.addItem(name, name)
        if select:
            for i in range(self.cb_preset.count()):
                if self.cb_preset.itemData(i) == select:
                    self.cb_preset.setCurrentIndex(i)
                    break
        self.cb_preset.blockSignals(False)

    def select_matching_preset(self):
        """Shows the preset name if the current sizes match one."""
        f = self.unit_factor
        cur = {'length': self.sp_len.value(), 'height': self.sp_hgt.value(),
               'depth': self.sp_dep.value(), 'joint': self.sp_joint.value(),
               'header_len': self.sp_hlen.value()}
        for i in range(self.cb_preset.count()):
            name = self.cb_preset.itemData(i)
            p = self.all_presets().get(name) if name else None
            if not p:
                continue
            if all(abs((p.get(k) or DEFAULT_SIZES_MM[k]) * f - cur[k]) < 0.01 * f for k in cur):
                self.cb_preset.blockSignals(True)
                self.cb_preset.setCurrentIndex(i)
                self.cb_preset.blockSignals(False)
                return

    def apply_preset(self, _idx=None):
        name = self.cb_preset.currentData()
        if not name:
            return
        p = self.all_presets().get(name)
        if not p:
            return
        f = self.unit_factor
        for spin, key in ((self.sp_len, 'length'), (self.sp_hgt, 'height'),
                          (self.sp_dep, 'depth'), (self.sp_joint, 'joint'),
                          (self.sp_hlen, 'header_len')):
            v = p.get(key) or DEFAULT_SIZES_MM[key]
            spin.setValue(v * f)

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
        f = self.unit_factor

        def mm(spin):
            return spin.value() / f

        self.user_presets[name] = {
            'length': mm(self.sp_len), 'height': mm(self.sp_hgt),
            'depth': mm(self.sp_dep), 'joint': mm(self.sp_joint),
            'header_len': mm(self.sp_hlen),
        }
        if not save_user_presets(self.user_presets):
            QMessageBox.warning(self, "Save failed",
                                "Could not write the preset file:\n" + PRESET_FILE)
        self.refresh_presets(select=name)
        return True

    def delete_preset(self):
        name = self.cb_preset.currentData()
        if not name:
            return
        if name in BUILTIN_PRESETS or name not in self.user_presets:
            QMessageBox.information(self, "Cannot delete", "Built-in presets cannot be deleted.")
            return
        r = QMessageBox.question(self, "Delete preset", "Delete preset '%s'?" % name)
        if r != QMessageBox.Yes:
            return
        del self.user_presets[name]
        save_user_presets(self.user_presets)
        self.refresh_presets()

    def get_values(self):
        def au(s):
            return s.value()
        picked = []
        for i in range(self.lst_open.count()):
            it = self.lst_open.item(i)
            if it.data(Qt.UserRole) is not None and it.checkState() == Qt.Checked:
                picked.append(it.data(Qt.UserRole))
        return {
            'length': au(self.sp_len), 'height': au(self.sp_hgt),
            'depth': au(self.sp_dep), 'joint': au(self.sp_joint),
            'min_frag': au(self.sp_frag),
            'hole_gap': self.sp_hgap.value(),
            'even_ends': self.cb_even.isChecked(), 'min_end_pct': self.sp_mine.value(),
            'kick': self.cb_kick.isChecked(), 'kick_pct': self.sp_kpct.value(),
            'kick_mm': self.sp_kmm.value(), 'kick_seed': self.sp_kseed.value(),
            'bond': self.cb_bond.currentData(),
            'offset_mode': self.cb_off.currentData(),
            'offset_fixed': self.sp_ofix.value(),
            'offset_seq': self.le_seq.text(),
            'offset_seed': self.sp_seed.value(),
            'offset_rmax': self.sp_rmax.value(),
            'header_every': self.sp_every.value() if self.cb_head.isChecked() else 0,
            'header_len': au(self.sp_hlen),
            'soldier': self.cb_sold.isChecked(),
            'soldier_holes': picked,
            # None = keep following the unit length
            'soldier_len': None if self._sold_linked else self.sp_slen.value(),
            'corner_angle': self.sp_ang.value(),
            'subdiv': self.sp_sub.value(),
            'back_faces': self.cb_back.isChecked(),
            'swap': self.cb_swap.isChecked(),
            'new_group': self.cb_group.isChecked(),
            'unit': self.unit_label,
        }


DEFAULTS = {
    'length': None, 'height': None, 'depth': None, 'joint': None, 'min_frag': None,
    'bond': 'running',
    'offset_mode': 'bond', 'offset_fixed': 0.5, 'offset_seq': '0, 0.5, 0.25, 0.75',
    'offset_seed': 1, 'offset_rmax': 1.0,
    'header_every': 0, 'header_len': None,
    'soldier': False, 'soldier_len': None, 'corner_angle': 35.0,
    'subdiv': 4, 'back_faces': True, 'swap': False, 'new_group': True, 'hole_gap': 0.01,
    'even_ends': True, 'min_end_pct': 50.0, 'kick': False, 'kick_pct': 8.0, 'kick_mm': 3.0, 'kick_seed': 1,
}


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


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
class BrickBlockStudioTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Shift+T"
    description = "3D brick and block work with bonds, row offsets, header courses, selectable soldier courses, presets and exact opening cuts."

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
        if sel is None:
            QMessageBox.warning(viewport, "No Face Selected",
                                "Please select a flat surface (face) before running %s." % PLUGIN_NAME)
            return
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
        if preselected:
            cur['soldier'] = True      # you picked openings, so you probably want the course

        dialog = BrickDialog(cur, "mm", openings, preselected, viewport,
                             tool=self, viewport=viewport)
        dialog.wall = wall
        dialog.read_selection()
        BrickBlockStudioTool._dialog = dialog

        def closed(*_):
            BrickBlockStudioTool._dialog = None
        dialog.finished.connect(closed)
        eddy_window(dialog, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dialog.show()

    def apply_from_dialog(self, dialog):
        sel = dialog.read_selection()
        if sel is None:
            QMessageBox.information(dialog, PLUGIN_NAME, "Select a face (a wall) first.")
            return
        wall, others, unit_label = sel
        vals = dialog.get_values()
        keep = dict(vals)
        keep.pop('soldier_holes', None)     # opening choice is per wall, don't remember it
        BrickBlockStudioTool._saved = keep
        self.active_face = wall
        self.generate_layout(dialog.viewport, vals)

    def on_deactivate(self, viewport):
        pass

    def generate_layout(self, viewport, p):
        p = dict(p)                 # our own copy: its sizes may be turned into metres below
        face = getattr(self, 'active_face', None)
        if face is None:
            return

        def mutate(scene):
            from core.mesh import Mesh
            from core.group import Group

            face_pts = [vertex_to_vector3d(v) for v in face.vertices]
            if len(face_pts) < 3:
                print("Face has too few vertices.")
                return

            n_raw = getattr(face, 'normal', None)
            normal = QVector3D(0, 0, 0)
            if n_raw is not None:
                normal = vertex_to_vector3d(n_raw() if callable(n_raw) else n_raw)
            if normal.length() < 0.001:
                normal = QVector3D.crossProduct(face_pts[1] - face_pts[0],
                                                face_pts[2] - face_pts[1])
            normal = normal.normalized() if normal.length() > 0.001 else QVector3D(0, 0, 1)

            origin = face_pts[0]
            base_u, base_v = _level_dirs(face_pts, normal)     # courses run level on walls

            if p['swap']:
                u_dir, v_dir = base_v, -base_u
            else:
                u_dir, v_dir = base_u, base_v

            left_handed = QVector3D.dotProduct(
                QVector3D.crossProduct(u_dir, v_dir), normal) < 0

            us = [QVector3D.dotProduct(q - origin, u_dir) for q in face_pts]
            vs = [QVector3D.dotProduct(q - origin, v_dir) for q in face_pts]
            origin = origin + u_dir * min(us) + v_dir * min(vs)
            W = max(us) - min(us)
            H = max(vs) - min(vs)

            # the face's own outline, so any shape works (circle, gable, arch, L-shape ...)
            outline = [(QVector3D.dotProduct(q - origin, u_dir), QVector3D.dotProduct(q - origin, v_dir))
                       for q in face_pts]
            if len(outline) > 3 and abs(outline[0][0] - outline[-1][0]) < 1e-9 \
                    and abs(outline[0][1] - outline[-1][1]) < 1e-9:
                outline.pop()
            to_outline = outline_clipper(outline)

            metres = max(W, H) < 50.0
            if metres and not p.get('_in_metres'):
                # every size in the window is in mm; this wall is drawn in metres
                for key in SIZE_KEYS:
                    if p.get(key) is not None:
                        p[key] = p[key] * 0.001
                p['_in_metres'] = True
            l = p['length'] or (0.21 if metres else 210.0)
            w = p['height'] or (0.065 if metres else 65.0)
            th = p['depth'] or (0.02 if metres else 20.0)
            joint = p['joint'] if p['joint'] is not None else (0.01 if metres else 10.0)
            min_frag = p['min_frag'] if p['min_frag'] is not None else (0.02 if metres else 20.0)
            hl = p['header_len'] or (0.1 if metres else 100.0)
            S = p['soldier_len'] or l
            bond = str(p['bond']).lower()
            subdiv = p['subdiv']
            tiny = 0.001 if metres else 1.0
            header_every = p['header_every']

            real_holes = []
            hole_ids = []
            for hi, hole in enumerate(getattr(face, 'holes', None) or []):
                poly = []
                for v in hole:
                    q = vertex_to_vector3d(v)
                    poly.append((QVector3D.dotProduct(q - origin, u_dir),
                                 QVector3D.dotProduct(q - origin, v_dir)))
                if len(poly) > 1 and abs(poly[0][0] - poly[-1][0]) < 1e-9 \
                        and abs(poly[0][1] - poly[-1][1]) < 1e-9:
                    poly.pop()
                if len(poly) < 3:
                    continue
                if _area(poly) < 0:
                    poly.reverse()
                gap = (p.get('hole_gap') or 0.0) * (0.001 if metres else 1.0)
                if gap > 0:
                    poly = _grow(poly, gap)      # bricks stop a hair short of the opening
                real_holes.append((poly, _bbox(poly), _is_convex(poly)))
                hole_ids.append(hi)

            chosen = p.get('soldier_holes')
            chosen = None if chosen is None else set(chosen)

            field_holes = list(real_holes)
            soldier_polys = []
            n_sold_holes = 0
            if p['soldier']:
                for k, (hole, bb, cv) in enumerate(real_holes):
                    if chosen is not None and hole_ids[k] not in chosen:
                        continue
                    n_sold_holes += 1
                    sp, cp, ex = _soldiers(hole, w, joint, S, p['corner_angle'])
                    soldier_polys.extend(cp + sp)
                    for q in ex:
                        for part in _convex_parts(q):
                            field_holes.append((part, _bbox(part), True))

            print("Wall %.3f x %.3f (%s), holes: %d, soldier course on %d, bond: %s, offsets: %s, headers every %d"
                  % (W, H, "m" if metres else "mm", len(real_holes), n_sold_holes,
                     bond, p['offset_mode'], header_every))

            # Target mesh
            target = None
            if p['new_group']:
                try:
                    target = Mesh()
                    g = Group("3D Brick & Block Work")
                    g.mesh = target
                    if hasattr(scene, 'add_group'):
                        scene.add_group(g)
                    elif hasattr(scene, 'groups') and isinstance(scene.groups, list):
                        scene.groups.append(g)
                except Exception as e:
                    print("Could not create group (%s); using active mesh." % e)
                    target = None
            if target is None:
                target = getattr(scene, 'mesh', None) or getattr(viewport, 'mesh', None)
                if target is None:
                    target = Mesh()
                    g = Group("3D Brick & Block Work")
                    g.mesh = target
                    if hasattr(scene, 'add_group'):
                        scene.add_group(g)
                    else:
                        scene.groups.append(g)

            def to_world(lx, ly, lz):
                pt = origin + u_dir * lx + v_dir * ly + normal * lz
                return VertexWrapper(pt.x(), pt.y(), pt.z())

            stats = {'faces': 0, 'bricks': 0, 'errors': 0, 'err': None}

            def emit(verts):
                if left_handed:
                    verts = verts[::-1]
                try:
                    target.add_face(verts)
                    stats['faces'] += 1
                except Exception as e:
                    stats['errors'] += 1
                    stats['err'] = e

            def add_brick(poly, depth=None):
                n = len(poly)
                front = [to_world(x, y, th if depth is None else depth) for x, y in poly]
                back = [to_world(x, y, 0) for x, y in poly]
                if TRIANGULATE_FRONT and n > 3:
                    for i in range(1, n - 1):
                        emit([front[0], front[i], front[i + 1]])
                else:
                    emit(front)
                for i in range(n):
                    j = (i + 1) % n
                    emit([back[i], back[j], front[j], front[i]])
                if p['back_faces']:
                    emit(back[::-1])
                stats['bricks'] += 1

            mm = 0.001 if metres else 1.0
            min_end = (p.get('min_end_pct') or 0.0) / 100.0 * l if p.get('even_ends', True) else 0.0
            runs = run_finder(outline, [h for h, _, _ in field_holes]) if min_end > 0 else None
            # line the bond up with the left side of the first opening, so the courses
            # beside it end in a whole brick and a half brick in turn, as a bricklayer would
            bond_x0 = 0.0
            if p.get('even_ends', True) and real_holes:
                bond_x0 = min(bb[0] for _, bb, _ in real_holes) + joint   # a brick ends at the reveal
            kick_rng = random.Random(int(p.get('kick_seed') or 0) + 7)
            kick_on = p.get('kick') and (p.get('kick_pct') or 0) > 0 and (p.get('kick_mm') or 0) > 0
            for x1, y1, x2, y2, _head in bond_layout(
                    l, w, joint, hl, bond, header_every, p['offset_mode'], p['offset_fixed'],
                    p['offset_seq'], p['offset_seed'], p['offset_rmax'], W, H, tiny,
                    segments=runs, min_end=min_end, x0=bond_x0):
                rect = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
                depth = None
                if kick_on and kick_rng.random() < p['kick_pct'] / 100.0:
                    # this one sticks out a little (the back stays on the wall)
                    depth = th + p['kick_mm'] * mm * (0.35 + 0.65 * kick_rng.random())
                for piece in to_outline(rect):
                    for poly in trim_poly(piece, field_holes, subdiv, min_frag):
                        add_brick(poly, depth)

            placed = []
            nsold = 0
            for poly in soldier_polys:
                for pc in to_outline(poly):
                    for piece in trim_poly(pc, real_holes + placed, subdiv, min_frag):
                        add_brick(piece)
                        nsold += 1
                placed.append((poly, _bbox(poly), True))

            print("Done: %d units (%d soldier/corner), %d faces, %d errors"
                  % (stats['bricks'], nsold, stats['faces'], stats['errors']))
            if stats['errors']:
                print("First error:", stats['err'], "-> try TRIANGULATE_FRONT = True")
            try:
                viewport.flash_status("%s: %d units, %d faces"
                                      % (PLUGIN_NAME, stats['bricks'], stats['faces']), 3000)
            except Exception:
                pass

        viewport.history.execute(SnapshotImport(mutate))
        viewport.notify_scene_changed()