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
openings, stone heads and sills, copings (slabs, saddleback, bricks on edge, cock and hen,
upright slates), weathering and bomb-site damage (a broken-down top, blast holes, broken
and missing units, rubble at the foot), and rubble piles. Sizes in real-world mm.
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
VERSION = "2"             # shown in the window title, so you can tell which file is loaded

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
               'kick_mm', 'spall_mm', 'hole_gap')


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
    k = 0
    y = 0.0
    first = None
    while y < H - J and qh > 0:
        top = min(y + qh, H)
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
    and both slopes of a gable). Returns (units [(poly, depth factor)], exclusions)."""
    J = p['joint']
    style = p.get('c_style', 'slab')
    ch = p['c_h']
    if style == 'brick_edge':
        ch = p['header_len']
    units, excl = [], []
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

        def quad(t1, t2, d1, d2, lean=0.0):
            p1 = (a[0] + ex * t1, a[1] + ey * t1)
            p2 = (a[0] + ex * t2, a[1] + ey * t2)
            return [p1, p2,
                    (p2[0] + ix * d2 + ex * lean, p2[1] + iy * d2 + ey * lean),
                    (p1[0] + ix * d1 + ex * lean, p1[1] + iy * d1 + ey * lean)]
        excl.append(quad(-J, L + J, ch + J, ch + J))
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
                # a rounded top: three bands, standing out less towards the top
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

    real_holes = [(h, _bbox(h), _is_convex(h)) for h in holes]

    # ---- copings, quoins and opening dressings come first: the walling fits round them
    placed = []                  # convex shapes that later pieces must keep out of
    cop_units, quo_units, dress_units = [], [], []
    excl_all = []
    if p.get('copings'):
        cu, ce = coping_layout(outline, p, random.Random(rng.random()))
        done = []
        for poly, fd in cu:
            for pc in to_outline(poly):
                for piece in trim_poly(pc, done, subdiv, min_frag * 0.3):
                    cop_units.append((piece, max(th * 0.5, (th + p['c_over']) * fd), 'coping', rng.random()))
            done.append((poly, _bbox(poly), True))
        placed.extend(done)
        for q in ce:
            for part in _convex_parts(_ccw(q)):
                excl_all.append((part, _bbox(part), True))
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
                for piece in trim_poly(pc, placed, subdiv, min_frag):
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
        if p.get('even_ends', True) and real_holes:
            bond_x0 = min(bb[0] for _, bb, _ in real_holes) + J
        rects = bond_layout(A, B, J, p['header_len'], str(p['bond']).lower(), p['header_every'],
                            p['offset_mode'], p['offset_fixed'], p['offset_seq'], p['offset_seed'],
                            p['offset_rmax'], W, H, tiny, segments=runs, min_end=min_end, x0=bond_x0)
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

    def damage(units, can_kick):
        keep = []
        for u in units:
            poly = u[0]
            cx, cy = _centroid(poly)
            gone = False
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
            if gone:
                removed.append((cx, cy, u[2]))
                continue
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
            keep.append(tuple(u))
        return keep

    walling = damage(walling, True)
    quo_units = damage(quo_units, False)
    dress_units = damage(dress_units, False)
    cop_units = damage(cop_units, False)

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
            if _is_convex(outline):
                # a plain or gabled wall: cut the profile to the outline in one go
                pc = prof_poly
                ol = _ccw(list(outline))
                for i in range(len(ol)):
                    pc = _clip_edge(pc, ol[i], ol[(i + 1) % len(ol)], True)
                    if len(pc) < 3:
                        break
                pieces = [_simplify(pc, max(W, H) * 1e-7)] if len(pc) >= 3 else []
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
        cut = [h for h, bb, cv in real_holes]
        if p.get('through'):
            cut += [_ccw(b) for b in blasts]
        for pc in pieces:
            pc = _ccw(pc)
            inner = []
            for h in cut:
                if all(_pip(q[0], q[1], pc) for q in h) and abs(_area(h)) < abs(_area(pc)):
                    inner.append(_ccw(h))
            backing.append((pc, inner))

    stats = {'units': len(walling), 'quoins': len(quo_units) + len(dress_units),
             'copings': len(cop_units), 'removed': len(removed)}
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
        mm = p.get('_mm', 1.0)            # timbers are real sizes, whatever the walling
        L = rng.uniform(1200.0, 3200.0) * mm
        w = rng.uniform(75.0, 225.0) * mm
        return _rect(-L / 2, -w / 2, L / 2, w / 2), w * rng.uniform(0.35, 1.0)
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


def drop_pieces(p, rng, n, sample, inside, max_h, timbers=0, broken=0.4, core=None):
    """Drops n loose pieces one at a time where sample() says, letting each one roll
    down off any piece already there that it would sit too steeply on. Returns a list
    of solids (each a list of faces) in local x, y (ground) and z (up)."""
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
    for kind in kinds:
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
    pieces = drop_pieces(p, rng, p.get('pile_n', 150), sample, inside, Hp,
                         timbers=p.get('pile_timbers', 0), broken=(p.get('pile_broken', 40.0)) / 100.0,
                         core=hfun if core is not None else None)
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


def plain(solid_faces):
    return [(f, []) for f in solid_faces]


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
    """A sample panel for the preview: (W, H, outline, holes)."""
    A, B, J = v['length'], v['height'], v['joint']
    W = 10 * A + 9 * J
    if v.get('ruin') or v.get('holes_n') or v.get('foot'):
        W = max(W, 3200.0 * v.get('_mm', 1.0))      # room to show the damage
    H = 0.62 * W
    if v.get('material', 'brick') == 'brick':
        H = max(1, round(H / (B + J))) * (B + J) - J if B + J > 0 else H
    outline = [(0.0, 0.0), (W, 0.0), (W, H), (0.0, H)]
    holes = []
    if v.get('soldier') or v.get('q_open') or v.get('heads') or v.get('sills'):
        w, h = 0.24 * W, 0.36 * H
        x0, y0 = (W - w) / 2.0, 0.26 * H
        holes = [[(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)]]
    return W, H, outline, holes


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
        for poly, d, kind, shade in res[key]:
            solids.append((unit_solid(poly, 0.0, d), unit_colour(mat, kind, shade)))
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
        kind = 'timber' if kind == 'timber' else ('brick' if mat == 'brick' else 'stone')
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
            if style in ('slab', 'saddle'):
                w, hh = K, Jc
            elif style == 'brick_edge':
                w, hh = B, Jc
            else:
                w, hh = Jc * 0.4, Jc * (1.0 if k % 2 == 0 else 0.7)
            box(x, yc, min(x + w, Wd), yc + hh, 'coping')
            x += w + J
            k += 1
        if style in ('slab', 'saddle'):
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
                    self.items = render_items(solids, (-0.38, 0.3, 1.0), (0, 1, 0), (-0.5, 0.6, 0.65))
                    st = res['stats']
                    self.caption = "%s - %d units" % (MATERIAL_NAMES.get(self.v.get('material'), ""),
                                                      st['units'] + st['quoins'] + st['copings'])
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
             'pile_core', 'pile_seed'}

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
    ("Rubble pile", 'pile_timbers', "Timbers", 0, 50, -1, "",
     "Broken roof or floor timbers lying in the heap."),
    ("Rubble pile", 'pile_seed', "Pile pattern no.", 0, 999999, -1, "",
     "Change this for a different heap."),
]


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
        self.lbl_face = QLabel()
        self.lbl_face.setWordWrap(True)
        self.lbl_face.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl_face)

        # ---- the picture on the left, the settings beside it ----
        side = QHBoxLayout()
        lay.addLayout(side, 1)
        self.views = QTabWidget()
        self.preview = StudioPreview('3d')
        self.preview.setToolTip("A sample piece of wall as it will be built (or the rubble pile, on the "
                                "Rubble pile tab). It changes as you change the settings.")
        self.sizes = StudioPreview('sizes')
        self.sizes.setToolTip("The sizes lettered: the letters match the settings.")
        self.views.addTab(self.preview, "Preview")
        self.views.addTab(self.sizes, "Sizes (A, B, C ...)")
        self.views.setTabToolTip(0, "A sample piece of wall (or the rubble pile) as it will be built.")
        self.views.setTabToolTip(1, "The sizes lettered: the letters match the settings.")
        side.addWidget(self.views, 1)

        self.tabs = QTabWidget()
        self.pages = {}
        for title in TABS:
            pg = QWidget()
            self.pages[title] = _form(pg)
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
        for c in (self.cb_back, self.cb_swap, self.cb_group):
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
        self.cb_cstyle = combo(COPINGS, "Stone slabs, rounded saddleback stones, bricks on edge, cock and hen "
                                        "(upright stones, tall and short in turn, as on a dry-stone wall) or "
                                        "upright slates.")
        F[Q].addRow("   Coping:", self.cb_cstyle)
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
        row(D, 'missing_pct')
        self.cb_ruin = check("Broken-down top (ruin)", "The top of the wall broken down unevenly, in steps "
                                                       "along the joints, like a bombed or derelict building.")
        F[D].addRow(self.cb_ruin)
        row(D, 'ruin_depth')
        row(D, 'ruin_rough')
        row(D, 'broken_pct')
        row(D, 'holes_n')
        row(D, 'hole_size')
        self.cb_through = check("   Holes go right through the backing",
                                "The blast holes are cut through the backing sheet too, so you can see "
                                "through the wall (with the face deleted).")
        F[D].addRow(self.cb_through)
        self.cb_foot = check("Rubble at the foot of the wall", "Loose bricks or stones heaped against the "
                                                               "foot of the wall, under the damage they "
                                                               "fell from.")
        F[D].addRow(self.cb_foot)
        row(D, 'foot_w')
        row(D, 'foot_amt')
        row(D, 'backing')
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
        for k in ('pile_len', 'pile_wid', 'pile_h', 'pile_n', 'pile_broken', 'pile_timbers'):
            row(Rp, k)
        self.cb_core = check("Solid core under the pieces", "A solid mound under the loose pieces, so the "
                                                            "heap looks full and prints as one piece with "
                                                            "far fewer pieces.")
        F[Rp].addRow(self.cb_core)
        row(Rp, 'pile_seed')
        self.tabs.currentChanged.connect(self.changed)

        # ---- presets, report, buttons ----
        prow = QHBoxLayout()
        prow.addWidget(QLabel("Preset:"))
        self.cb_preset = QComboBox()
        _compact_combo(self.cb_preset, 16)
        prow.addWidget(self.cb_preset, 1)
        self.btn_save = QPushButton("Save")
        self.btn_saveas = QPushButton("Save as...")
        self.btn_delete = QPushButton("Delete")
        self.btn_folder = QPushButton("Folder")
        for b_ in (self.btn_save, self.btn_saveas, self.btn_delete, self.btn_folder):
            prow.addWidget(b_)
        lay.addLayout(prow)
        self.lbl_report = QLabel()
        self.lbl_report.setWordWrap(True)
        self.lbl_report.setVisible(False)
        lay.addWidget(self.lbl_report)
        brow = QHBoxLayout()
        self.btn_apply = QPushButton("Apply to face")
        self.btn_apply.setToolTip("Covers the selected face (a wall) with the walling, quoins, copings "
                                  "and damage set here.")
        self.btn_apply.setDefault(True)
        self.btn_pile = QPushButton("Make rubble pile")
        self.btn_pile.setToolTip("Makes a heap of loose bricks or stones (Rubble pile tab) on the selected face.")
        btn_close = QPushButton("Close")
        brow.addWidget(self.btn_apply)
        brow.addWidget(self.btn_pile)
        brow.addStretch(1)
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

    # ---- values ----
    def _sold_unlink(self, *_):
        if not self._busy:
            self._sold_linked = False

    def checks(self):
        return {'back_faces': self.cb_back, 'swap': self.cb_swap, 'new_group': self.cb_group,
                'soldier': self.cb_sold, 'even_ends': self.cb_even, 'quoins_l': self.cb_ql,
                'quoins_r': self.cb_qr, 'q_open': self.cb_qo, 'q_courses': self.cb_qc,
                'heads': self.cb_heads, 'sills': self.cb_sills, 'copings': self.cb_cop,
                'kick': self.cb_kick, 'spall': self.cb_spall, 'ruin': self.cb_ruin,
                'through': self.cb_through, 'foot': self.cb_foot, 'remove_face': self.cb_remove,
                'pile_core': self.cb_core, 'header_on': self.cb_head}

    def combos(self):
        return {'material': self.cb_mat, 'bond': self.cb_bond, 'offset_mode': self.cb_off,
                'c_style': self.cb_cstyle, 'pile_shape': self.cb_pshape}

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

    def changed(self, *_):
        if self._busy:
            return
        if self._sold_linked:
            self._busy = True
            self.sp['soldier_len'][0].setValue(self.sp['length'][0].value())
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
              'c_len': v['copings'] and v['c_style'] in ('slab', 'saddle'), 'c_over': v['copings'],
              'kick_pct': v['kick'], 'kick_mm': v['kick'], 'spall_pct': v['spall'], 'spall_mm': v['spall'],
              'ruin_depth': v['ruin'], 'ruin_rough': v['ruin'], 'hole_size': v['holes_n'] > 0,
              'foot_w': v['foot'], 'foot_amt': v['foot'],
              'pile_wid': v['pile_shape'] != 'face', 'pile_len': v['pile_shape'] != 'face'}
        on['q_short'] = on['q_h'] = on['q_proud'] = on['q_long']
        for key, ok in on.items():
            s, lab = self.sp[key]
            s.setEnabled(bool(ok))
            lab.setEnabled(bool(ok))
        for w_ in (self.cb_bond, self.cb_off, self.cb_head, self.cb_sold, self.cb_even, self.cb_qc):
            w_.setEnabled(brick)
        self.sp_every.setEnabled(brick and self.cb_head.isChecked())
        self.sp_ofix.setEnabled(brick and off == "fixed")
        self.le_seq.setEnabled(brick and off == "sequence")
        self.sp_seed.setEnabled(brick and off == "random")
        self.sp_rmax.setEnabled(brick and off == "random")
        self.cb_cstyle.setEnabled(v['copings'])
        self.cb_through.setEnabled(v['holes_n'] > 0 and v['backing'] > 0)
        self.lst_open.setEnabled(True)
        what = 'pile' if self.tabs.currentIndex() == TABS.index("Rubble pile") else 'wall'
        pv = self.preview_values(v)
        self.preview.set_values(pv, what)
        self.sizes.set_values(pv, what)

    def preview_values(self, v):
        p = dict(v)
        for k, d in DEFAULTS.items():
            if p.get(k) is None and k not in ('soldier_len', 'soldier_holes'):
                p[k] = d
        p['soldier_len'] = p.get('soldier_len') or p['length']
        p['tiny'] = 1.0
        return p

    def show_report(self, text, bad=False):
        self.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if bad else "#2e7d32"))
        self.lbl_report.setText(text)
        self.lbl_report.setVisible(True)

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
                                  "ground, then 'Make rubble pile'.")
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

    def apply_preset(self, _idx=None):
        name = self.cb_preset.currentData()
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
    'bond': 'running',
    'offset_mode': 'bond', 'offset_fixed': 0.5, 'offset_seq': '0, 0.5, 0.25, 0.75',
    'offset_seed': 1, 'offset_rmax': 1.0,
    'header_every': 0, '_header_n': 5,
    'soldier': False, 'soldier_len': None, 'corner_angle': 35.0,
    'subdiv': 4, 'back_faces': True, 'swap': False, 'new_group': True, 'hole_gap': 0.01,
    'even_ends': True, 'min_end_pct': 50.0,
    'quoins_l': False, 'quoins_r': False, 'q_open': False, 'q_courses': True,
    'q_long': 450.0, 'q_short': 225.0, 'q_h': 290.0, 'q_proud': 10.0, 'heads': False, 'sills': False,
    'copings': False, 'c_style': 'slab', 'c_h': 150.0, 'c_len': 600.0, 'c_over': 30.0,
    'kick': False, 'kick_pct': 8.0, 'kick_mm': 3.0, 'spall': False, 'spall_pct': 6.0, 'spall_mm': 3.0,
    'missing_pct': 0.0, 'ruin': False, 'ruin_depth': 900.0, 'ruin_rough': 6, 'broken_pct': 40.0,
    'holes_n': 0, 'hole_size': 700.0, 'through': False, 'foot': False, 'foot_w': 900.0, 'foot_amt': 50.0,
    'backing': 0.0, 'remove_face': False, 'dmg_seed': 1,
    'pile_shape': 'heap', 'pile_len': 2500.0, 'pile_wid': 1800.0, 'pile_h': 900.0, 'pile_n': 220,
    'pile_broken': 40.0, 'pile_timbers': 2, 'pile_core': True, 'pile_seed': 1,
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

        dialog = BrickDialog(cur, openings, preselected, viewport, tool=self, viewport=viewport)
        dialog.wall = wall
        dialog.read_selection()
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
        res = wall_units(p, W, H, fr['outline'], holes, fr['hole_ids'], self._seed(fr))
        to_w = self._mapper(fr)
        mat = p['material']
        mat_name = MATERIAL_NAMES.get(mat, "Walling").split(" (")[0]

        def solids(units):
            out = []
            for poly, d, kind, shade in units:
                faces = unit_solid(poly, 0.0, d)
                if not p['back_faces']:
                    del faces[1]                 # the back face
                out.append(to_w(faces))
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
        remove = [face] if p.get('remove_face') else []
        nf = self.add_to_scene(viewport, parts, top, p['new_group'], remove)
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
        if n_loose:
            msg += "; %d loose pieces at the foot" % n_loose
        msg += ". %d faces." % nf
        if remove:
            msg += " Deleted the face under them."
        elif p.get('ruin') or p.get('holes_n'):
            msg += (" The face is still whole behind the damage: tick 'Delete the face' (with a backing "
                    "sheet) to see the broken top and holes.")
        if self._errors[0]:
            msg += " %d faces could not be made (%s)." % self._errors
        try:
            viewport.flash_status("%s: %d units, %d faces" % (PLUGIN_NAME, st['units'], nf), 3000)
        except Exception:
            pass
        return (msg, bool(self._errors[0]))

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
        loose = [s for k, s in pieces if k != 'timber']
        timbers = [s for k, s in pieces if k == 'timber']
        if loose:
            parts.append(("Loose pieces (%d)" % len(loose), [to_w(plain(s)) for s in loose]))
        if timbers:
            parts.append(("Timbers (%d)" % len(timbers), [to_w(plain(s)) for s in timbers]))
        if not parts:
            return ("No pile could be made: try more pieces, or a taller pile.", True)
        mat_name = MATERIAL_NAMES.get(p['material'], "").split(" (")[0].lower()
        nf = self.add_to_scene(viewport, parts, "Rubble pile - %s" % mat_name, True, [])
        if nf is None:
            return None
        msg = "Rubble pile: %d loose pieces%s, %d faces." % (len(pieces), " on a solid core" if core else "", nf)
        if self._errors[0]:
            msg += " %d faces could not be made (%s)." % self._errors
        return (msg, bool(self._errors[0]))

    def add_to_scene(self, viewport, parts, top_name, new_group=True, remove=()):
        """One parent group holding a child group per part (walling, quoins, copings,
        backing, rubble). The geometry is already in place, so no transforms are needed.
        new_group off: everything goes into the loose geometry, as before."""
        stats = {'faces': 0, 'errors': 0, 'err': None}
        tol = 1e-7

        def fill(mesh, solids):
            for so in solids:
                verts = {}

                def vx(p_):
                    k = (round(p_[0] / tol), round(p_[1] / tol), round(p_[2] / tol))
                    if k not in verts:
                        verts[k] = VertexWrapper(*p_)
                    return verts[k]
                for outer, holes in so:
                    try:
                        if holes:
                            hs = [[vx(q) for q in h] for h in holes]
                            try:
                                mesh.add_face([vx(q) for q in outer], hs)
                            except TypeError:          # an older IngeTrazo: holes one by one
                                f_ = mesh.add_face([vx(q) for q in outer])
                                for h in hs:
                                    mesh.add_hole(f_, h)
                        elif TRIANGULATE_FRONT and len(outer) > 4:
                            vs = [vx(q) for q in outer]
                            for i in range(1, len(vs) - 1):
                                mesh.add_face([vs[0], vs[i], vs[i + 1]])
                        else:
                            mesh.add_face([vx(q) for q in outer])
                        stats['faces'] += 1
                    except Exception as e:
                        stats['errors'] += 1
                        stats['err'] = e

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

        def mutate(scene):
            from core.mesh import Mesh
            from core.group import Group
            if not new_group:
                target = getattr(scene, 'mesh', None) or getattr(viewport, 'mesh', None)
                if target is not None:
                    for _, solids in parts:
                        fill(target, solids)
                    if stats['faces'] == 0:
                        raise RuntimeError("No faces could be created (%s)." % stats['err'])
                    for f, m_ in targets:
                        remove_face(scene, m_, f)
                    return
            kids = []
            for name, solids in parts:
                mesh = Mesh()
                fill(mesh, solids)
                kids.append(make_group(Group, mesh, name))
            if stats['faces'] == 0:
                raise RuntimeError("No faces could be created (%s)." % stats['err'])
            parent = None
            if len(kids) > 1:
                try:
                    parent = Group(name=top_name)
                    if hasattr(parent, 'adopt'):
                        parent.adopt(kids)
                    else:
                        parent.children = kids
                    parent.component = False
                except Exception:
                    parent = None          # an older IngeTrazo: add them side by side
            elif kids:
                try:
                    kids[0].name = top_name
                except Exception:
                    pass
            for g in ([parent] if parent is not None else kids):
                if hasattr(scene, 'add_group') and parent is None:
                    scene.add_group(g)
                else:
                    scene.groups.append(g)
            for f, m_ in targets:
                remove_face(scene, m_, f)

        scene0 = getattr(viewport, 'scene', None)
        targets = [(f, mesh_of_face(scene0, f)) for f in remove] if scene0 is not None else []
        targets = [(f, m_) for f, m_ in targets if m_ is not None]
        try:
            meshes = list({id(m_): m_ for _, m_ in targets}.values())
            if not new_group:
                tm = getattr(scene0, 'mesh', None)
                if tm is not None and all(tm is not m_ for m_ in meshes):
                    meshes.append(tm)
            viewport.history.execute(make_command(mutate, meshes) if targets else SnapshotImport(mutate))
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
