# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Wood Planking for IngeTrazo
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
3D Wood Planking - timber boarding for IngeTrazo
Select a face (a wall, a door, a floor or a platform) and it is covered in boards,
trimmed to the face's outline and round any openings in it (windows and doors).

Board styles: plain boards with grooves, V-jointed tongue and groove, shiplap,
weatherboarding (feather edge), board and batten, and log cabin. The boards can run
upright, level or on the slant, with butt joints, uneven widths, thicker and thinner
boards and the odd missing board for a weathered look - or right down to derelict: rotted,
ragged bottoms, jagged holes and boards hanging skew from one nail. Optional trims: boards
round the openings and corner boards at the ends of the face.

The boards never overlap each other, so the result is ready to print. With a backing
sheet the whole face prints as one piece.

Sizes are real-world millimetres (IngeTrazo stores metres). Ctrl+Alt+O.
"""

import os
import json
import math
import random
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox, QCheckBox,
    QPushButton, QLabel, QMessageBox, QWidget, QInputDialog, QSpinBox
)

PLUGIN_NAME = "3D Wood Planking"
VERSION = "5"
SCALE = 0.001
PRESET_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Wood Planking")
Z = (0.0, 0.0, 1.0)

STYLES = [
    ("flat", "Plain boards (grooves between)"),
    ("vjoint", "Tongue and groove, V-jointed"),
    ("shiplap", "Shiplap (rounded rebate at the top)"),
    ("weather", "Weatherboarding (feather edge)"),
    ("batten", "Board and batten"),
    ("log", "Log cabin (half-round logs)"),
]
STYLE_NAMES = dict(STYLES)
DIRECTIONS = [("Upright", 0.0), ("Level", 90.0), ("Slanting /", 45.0), ("Slanting \\", 135.0)]

DEFAULTS = dict(
    style='flat', angle=0.0, width=150.0, thick=20.0, gap=12.0, depth=8.0,
    thin=6.0, batten_w=60.0, batten_t=20.0, length=0.0, width_var=0.0, thick_var=0.0,
    missing=0.0, rot_h=0.0, holes=0.0, hole_size=120.0, skew_pct=0.0, skew_ang=8.0, seed=1,
    hole_gap=10.0, trims=False, trim_w=100.0, trim_t=25.0,
    corners=False, corner_w=100.0, backing=0.0, lift=0.01, flip=False, remove_face=False)

# ready-made settings for printing at 1:80 with a 0.4 mm nozzle (real-world mm: / 80 = model)
BUILTIN_PRESETS = {
    "1:80 print - upright boards, V-jointed": dict(
        style='vjoint', angle=0.0, width=150.0, thick=24.0, gap=16.0, depth=16.0, length=0.0,
        hole_gap=10.0, backing=40.0, lift=0.01),
    "1:80 print - weatherboarding": dict(
        style='weather', angle=90.0, width=150.0, thick=40.0, thin=8.0, gap=4.0, length=3600.0,
        hole_gap=10.0, trims=True, trim_w=100.0, trim_t=32.0, corners=True, corner_w=100.0,
        backing=40.0, lift=0.01),
    "1:80 print - board and batten": dict(
        style='batten', angle=0.0, width=225.0, thick=24.0, gap=16.0, batten_w=64.0, batten_t=24.0,
        hole_gap=10.0, backing=40.0, lift=0.01),
    "1:80 print - old shed, weathered boards": dict(
        style='flat', angle=0.0, width=175.0, thick=24.0, gap=32.0, length=1800.0, width_var=25.0,
        thick_var=8.0, missing=3.0, seed=7, hole_gap=10.0, backing=40.0, lift=0.01),
    "1:80 print - derelict shed": dict(
        style='flat', angle=0.0, width=175.0, thick=24.0, gap=32.0, length=0.0, width_var=30.0,
        thick_var=8.0, missing=6.0, rot_h=220.0, holes=1.5, hole_size=140.0, skew_pct=12.0,
        skew_ang=9.0, seed=11, hole_gap=10.0, backing=40.0, lift=0.01),
    "1:80 print - log cabin": dict(
        style='log', angle=90.0, width=200.0, thick=16.0, depth=48.0, gap=8.0, length=0.0,
        hole_gap=10.0, corners=True, corner_w=120.0, backing=40.0, lift=0.01),
}
NUM_KEYS = ('width', 'thick', 'gap', 'depth', 'thin', 'batten_w', 'batten_t', 'length', 'width_var',
            'thick_var', 'missing', 'rot_h', 'holes', 'hole_size', 'skew_pct', 'skew_ang', 'hole_gap',
            'trim_w', 'trim_t', 'corner_w', 'backing', 'lift')


# ---------------------------------------------------------------------------
# Small geometry helpers (x along the face, y up it, z out of it; mm)
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


def area2(poly):
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                     for i in range(len(poly)))


def bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), max(xs), min(ys), max(ys)


def clean(poly, eps=1e-6):
    out = []
    for p in poly:
        if not out or abs(p[0] - out[-1][0]) > eps or abs(p[1] - out[-1][1]) > eps:
            out.append((float(p[0]), float(p[1])))
    while len(out) > 1 and abs(out[0][0] - out[-1][0]) <= eps and abs(out[0][1] - out[-1][1]) <= eps:
        out.pop()
    k = 0
    while len(out) > 3 and k < len(out):
        a, b, c = out[k - 1], out[k], out[(k + 1) % len(out)]
        cr = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(cr) < 1e-9 and (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1]) >= 0:
            del out[k]
        else:
            k += 1
    if len(out) < 3 or abs(area2(out)) < 1e-6:
        return None
    return out if area2(out) > 0 else out[::-1]


def clip_half(poly, a, b, c):
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp, fq = a * p[0] + b * p[1] + c, a * q[0] + b * q[1] + c
        if fp >= 0:
            out.append(p)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def clip_convex(poly, conv):
    n = len(conv)
    for i in range(n):
        p, q = conv[i], conv[(i + 1) % n]
        dx, dy = q[0] - p[0], q[1] - p[1]
        poly = clip_half(poly, -dy, dx, dy * p[0] - dx * p[1])
        if len(poly) < 3:
            return None
    return clean(poly)


def subtract_convex(poly, hole):
    """poly minus a convex hole, as convex-ish pieces."""
    out = []
    rest = list(poly)
    n = len(hole)
    for i in range(n):
        p, q = hole[i], hole[(i + 1) % n]
        dx, dy = q[0] - p[0], q[1] - p[1]
        outside = clip_half(rest, dy, -dx, -dy * p[0] + dx * p[1])
        pc = clean(outside) if len(outside) >= 3 else None
        if pc:
            out.append(pc)
        rest = clip_half(rest, -dy, dx, dy * p[0] - dx * p[1])
        if len(rest) < 3:
            break
    return out


def is_convex(poly):
    n = len(poly)
    s = 0
    for i in range(n):
        a, b, c = poly[i], poly[(i + 1) % n], poly[(i + 2) % n]
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(cr) > 1e-9:
            if s == 0:
                s = 1 if cr > 0 else -1
            elif (cr > 0) != (s > 0):
                return False
    return True


def ear_clip(poly):
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
            if cross(a, b, c) <= 1e-12:
                continue
            if any(cross(a, b, p) >= 0 and cross(b, c, p) >= 0 and cross(c, a, p) >= 0
                   for p in rem if p is not a and p is not b and p is not c):
                continue
            found = i
            break
        if found is None:
            break
        tris.append([rem[found - 1], rem[found], rem[(found + 1) % len(rem)]])
        del rem[found]
    if len(rem) == 3:
        tris.append(rem)
    return tris


def convex_parts(poly):
    poly = clean(poly)
    if poly is None:
        return []
    return [poly] if is_convex(poly) else [t for t in (clean(t) for t in ear_clip(poly)) if t]


class Solid:
    def __init__(self):
        self.faces = []

    def volume(self):
        v = 0.0
        for pts in self.faces:
            for j in range(1, len(pts) - 1):
                v += v_dot(pts[0], v_cross(pts[j], pts[j + 1]))
        return v / 6.0

    def fix(self):
        if self.volume() < 0:
            self.faces = [list(reversed(f)) for f in self.faces]
        return self

    def mapped(self, fn):
        s = Solid()
        s.faces = [[fn(p) for p in f] for f in self.faces]
        return s.fix()


def slab(poly, zbot, ztop, cuts=()):
    """A closed solid over a polygon, between two surfaces zbot(x, y) and ztop(x, y).
    The polygon is cut into upright strips at the x positions in `cuts`, so curved
    (wavy) surfaces are made of flat facets. Within a strip both surfaces must be flat:
    true here, as they vary linearly in y and are linear in x between cuts."""
    poly = clean(poly)
    if poly is None:
        return None
    x0, x1, _, _ = bbox(poly)
    cs = sorted(c for c in cuts if x0 + 1e-7 < c < x1 - 1e-7)
    strips = []
    edges = [x0 - 1.0] + cs + [x1 + 1.0]
    for a, b in zip(edges[:-1], edges[1:]):
        pc = clip_half(poly, 1, 0, -a) if a > x0 - 0.5 else list(poly)
        if len(pc) >= 3 and b < x1 + 0.5:
            pc = clip_half(pc, -1, 0, b)
        pc = clean(pc) if len(pc) >= 3 else None
        if pc:
            strips.append(pc)
    if not strips:
        return None
    s = Solid()
    for st in strips:
        s.faces.append([(x, y, ztop(x, y)) for x, y in st])
        s.faces.append([(x, y, zbot(x, y)) for x, y in reversed(st)])
        n = len(st)
        for i in range(n):
            (ax, ay), (bx, by) = st[i], st[(i + 1) % n]
            if any(abs(ax - c) < 1e-7 and abs(bx - c) < 1e-7 for c in cs):
                continue                   # an inside cut shared with the next strip
            s.faces.append([(ax, ay, zbot(ax, ay)), (bx, by, zbot(bx, by)),
                            (bx, by, ztop(bx, by)), (ax, ay, ztop(ax, ay))])
    return s.fix()




def merged_slab(polys, zbot, ztop, cuts=()):
    """One closed solid over several pieces of a region that touch along their edges
    (as cutting round openings leaves them), so a board cut into convex pieces is still
    one solid with no faces inside it. The pieces are cut into strips at `cuts` (where a
    rounded top changes slope); within a strip both surfaces must be flat."""
    strips = []
    cs = sorted(cuts)
    for pc in polys:
        pc = clean(pc)
        if pc is None:
            continue
        x0, x1, _, _ = bbox(pc)
        inner = [c for c in cs if x0 + 1e-7 < c < x1 - 1e-7]
        edges = [None] + inner + [None]
        for a, b in zip(edges[:-1], edges[1:]):
            q = list(pc)
            if a is not None:
                q = clip_half(q, 1, 0, -a)
            if b is not None and len(q) >= 3:
                q = clip_half(q, -1, 0, b)
            q = clean(q) if len(q) >= 3 else None
            if q:
                strips.append(q)
    if not strips:
        return None
    # snap corners that are the same point, then split edges where another piece's corner
    # lies on them, so neighbouring pieces share whole edges
    tol = 0.002
    keys = {}

    def snap(p):
        k = (round(p[0] / tol), round(p[1] / tol))
        for dx in (0, -1, 1):
            for dy in (0, -1, 1):
                q = keys.get((k[0] + dx, k[1] + dy))
                if q is not None and abs(q[0] - p[0]) <= tol and abs(q[1] - p[1]) <= tol:
                    return q
        keys[k] = (float(p[0]), float(p[1]))
        return keys[k]

    def dedupe(st):
        out = []
        for p in st:
            if not out or p != out[-1]:
                out.append(p)
        while len(out) > 1 and out[0] == out[-1]:
            out.pop()
        return out if len(out) >= 3 and abs(area2(out)) > 1e-6 else None
    strips = [q for q in (dedupe([snap(p) for p in st]) for st in strips) if q]
    def tfix(strips):
        allp = list(keys.values())
        fixed = []
        for st in strips:
            out = []
            n = len(st)
            for i in range(n):
                a, b = st[i], st[(i + 1) % n]
                out.append(a)
                dx, dy = b[0] - a[0], b[1] - a[1]
                L2 = dx * dx + dy * dy
                if L2 < 1e-12:
                    continue
                mids = []
                for p in allp:
                    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2
                    if 1e-9 < t < 1 - 1e-9:
                        cr = abs((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / math.sqrt(L2)
                        if cr < 2e-4:
                            mids.append((t, p))
                out += [p for _, p in sorted(mids)]
            fixed.append(out)
        return fixed
    # where the region only touches itself at a corner (a pinch - usually the tip of a jagged
    # hole), drop the smallest bit there, so every corner of the solid is a clean one
    for _ in range(60):
        fixed = tfix(strips)
        directed = {}
        clash = None
        for si, st in enumerate(fixed):
            for i in range(len(st)):
                e = (st[i], st[(i + 1) % len(st)])
                if e in directed and clash is None:
                    clash = [directed[e], si]          # two bits lying over each other
                directed[e] = si
        if clash:
            del strips[min(clash, key=lambda si: abs(area2(strips[si])))]
            if not strips:
                return None
            continue
        outgoing = {}
        for (a_, b_), si in directed.items():
            if (b_, a_) not in directed:
                outgoing.setdefault(a_, []).append(si)
        pinch = [sis for sis in outgoing.values() if len(sis) > 1]
        if not pinch:
            break
        drop = min(pinch[0], key=lambda si: abs(area2(strips[si])))
        del strips[drop]
        if not strips:
            return None
    directed = set()
    for st in fixed:
        for i in range(len(st)):
            directed.add((st[i], st[(i + 1) % len(st)]))
    s = PSolid()
    # top: one face per flat strip of the profile (so no stray edges between the pieces);
    # bottom: one face for the lot. Each may have holes (the jagged holes, round openings).
    import bisect
    groups = {}
    for st in fixed:
        cx = sum(p[0] for p in st) / len(st)
        groups.setdefault(bisect.bisect(cs, cx), []).append(st)
    for grp in groups.values():
        for outer, hls in region_loops(grp)[0]:
            s.add([(x, y, ztop(x, y)) for x, y in outer], [[(x, y, ztop(x, y)) for x, y in h] for h in hls])
    whole, ok = region_loops(fixed)
    for outer, hls in whole:
        s.add([(x, y, zbot(x, y)) for x, y in reversed(outer)],
              [[(x, y, zbot(x, y)) for x, y in reversed(h)] for h in hls])
    if ok:
        # the sides: one face for each straight run of the outline
        for outer, hls in whole:
            for loop in [outer] + hls:
                for run in straight_runs(loop):
                    s.add([(x, y, zbot(x, y)) for x, y in run] +
                          [(x, y, ztop(x, y)) for x, y in reversed(run)])
    else:
        for st in fixed:
            for i in range(len(st)):
                a, b = st[i], st[(i + 1) % len(st)]
                if (b, a) in directed:
                    continue                      # an inside edge, shared with the next piece
                s.add([(a[0], a[1], zbot(*a)), (b[0], b[1], zbot(*b)),
                       (b[0], b[1], ztop(*b)), (a[0], a[1], ztop(*a))])
    return s.fix()


def straight_runs(loop):
    """A closed loop split into runs of points along one straight line each
    (every run includes both its end corners)."""
    n = len(loop)

    def turn(i):
        a, b, c = loop[i - 1], loop[i], loop[(i + 1) % n]
        ux, uy = b[0] - a[0], b[1] - a[1]
        vx, vy = c[0] - b[0], c[1] - b[1]
        lu, lv = math.hypot(ux, uy), math.hypot(vx, vy)
        if lu < 1e-12 or lv < 1e-12:
            return False
        return abs(ux * vy - uy * vx) / (lu * lv) > 1e-6 or ux * vx + uy * vy < 0
    corners = [i for i in range(n) if turn(i)]
    if not corners:
        return [[loop[i], loop[(i + 1) % n]] for i in range(n)]
    runs = []
    for k, c in enumerate(corners):
        e = corners[(k + 1) % len(corners)]
        run = [loop[c]]
        i = c
        while True:
            i = (i + 1) % n
            run.append(loop[i])
            if i == e:
                break
        runs.append(run)
    return runs


class PSolid(Solid):
    """A solid whose faces may have holes: holes[i] = loops cut out of faces[i]
    (wound the other way round)."""
    def __init__(self):
        Solid.__init__(self)
        self.holes = {}

    def add(self, pts, holes=()):
        if holes:
            self.holes[len(self.faces)] = [list(h) for h in holes]
        self.faces.append(list(pts))

    def loops(self):
        for i, f in enumerate(self.faces):
            yield f
            for h in self.holes.get(i, ()):
                yield h

    def volume(self):
        v = 0.0
        for pts in self.loops():
            for j in range(1, len(pts) - 1):
                v += v_dot(pts[0], v_cross(pts[j], pts[j + 1]))
        return v / 6.0

    def fix(self):
        if self.volume() < 0:
            self.faces = [list(reversed(f)) for f in self.faces]
            self.holes = {i: [list(reversed(h)) for h in hs] for i, hs in self.holes.items()}
        return self

    def mapped(self, fn):
        s = PSolid()
        s.faces = [[fn(p) for p in f] for f in self.faces]
        s.holes = {i: [[fn(p) for p in h] for h in hs] for i, hs in self.holes.items()}
        for k in ('ridge', 'backing'):
            if hasattr(self, k):
                setattr(s, k, getattr(self, k))
        return s.fix()


def _pip(p, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ay > p[1]) != (by > p[1]):
            if p[0] < ax + (p[1] - ay) * (bx - ax) / (by - ay):
                inside = not inside
    return inside


def region_loops(polys):
    """The outline of a region made of pieces that share whole edges:
    [(outer loop, [hole loops])]. Outer loops run counter-clockwise, holes clockwise."""
    edges = set()
    for st in polys:
        for i in range(len(st)):
            edges.add((st[i], st[(i + 1) % len(st)]))
    nxt = {}
    for a, b in edges:
        if (b, a) not in edges:
            if a in nxt:
                return [(st, []) for st in polys], False      # touches itself: keep the pieces
            nxt[a] = b
    loops = []
    seen = set()
    for start in list(nxt):
        if start in seen:
            continue
        loop, p = [], start
        while p not in seen:
            seen.add(p)
            loop.append(p)
            p = nxt.get(p)
            if p is None:
                return [(st, []) for st in polys], False
        if p != start or len(loop) < 3:
            return [(st, []) for st in polys], False
        loops.append(loop)
    outers = [l for l in loops if area2(l) > 0]
    holes = [l for l in loops if area2(l) <= 0]
    out = [(o, []) for o in outers]
    for h in holes:
        # a point just inside the hole: the middle of its first edge, nudged in
        (ax, ay), (bx, by) = h[0], h[1]
        mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
        L = math.hypot(bx - ax, by - ay) or 1.0
        probe = (mx + (by - ay) / L * 1e-3, my - (bx - ax) / L * 1e-3)   # just inside the hole
        home = [k for k, (o, _) in enumerate(out) if _pip(probe, o)]
        if not home:
            return [(st, []) for st in polys], False
        # the smallest outer loop holding it
        k = min(home, key=lambda k: abs(area2(out[k][0])))
        out[k][1].append(h)
    return out, True


def convex_hull(pts):
    pts = sorted(set((round(p[0], 6), round(p[1], 6)) for p in pts))
    if len(pts) < 3:
        return None

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
    return clean(lo[:-1] + hi[:-1])


def grow(poly, d):
    """A convex (counter-clockwise) polygon pushed out by d on every side."""
    poly = clean(poly)
    if poly is None or d <= 0:
        return poly
    n = len(poly)
    lines = []
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        L = math.hypot(bx - ax, by - ay)
        nx, ny = (by - ay) / L, -(bx - ax) / L          # outward for counter-clockwise
        lines.append(((ax + nx * d, ay + ny * d), (bx - ax, by - ay)))
    out = []
    for i in range(n):
        (p, r), (q, s) = lines[i - 1], lines[i]
        den = r[0] * s[1] - r[1] * s[0]
        if abs(den) < 1e-12:
            out.append(q)
            continue
        t = ((q[0] - p[0]) * s[1] - (q[1] - p[1]) * s[0]) / den
        x, y = p[0] + t * r[0], p[1] + t * r[1]
        # don't let a sharp corner make a long spike: cap it at 3 d from the corner
        cx, cy = poly[i]
        k = math.hypot(x - cx, y - cy)
        if k > 3 * d:
            x, y = cx + (x - cx) * 3 * d / k, cy + (y - cy) * 3 * d / k
        out.append((x, y))
    return convex_hull(out)


def rot(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def overlaps(pa, pb):
    A, B = bbox(pa), bbox(pb)
    return not (A[1] <= B[0] or B[1] <= A[0] or A[3] <= B[2] or B[3] <= A[2])


def cut_away(pieces, blockers):
    for hp in blockers:
        nxt = []
        for pc in pieces:
            if overlaps(pc, hp):
                nxt.extend(subtract_convex(pc, hp))
            else:
                nxt.append(pc)
        pieces = nxt
    return pieces


def clip_to(poly, parts):
    out = []
    for pt in parts:
        if overlaps(poly, pt):
            pc = clip_convex(poly, pt)
            if pc:
                out.append(pc)
    return out


def profile(style, we, t, v):
    """The top of one board across its width: [(distance from its lower/left edge, height)].
    Straight lines between the points."""
    d = max(0.0, v.get('depth', 0.0))
    if style == 'vjoint':
        c = min(d, 0.45 * we)
        lo = max(0.25 * t, t - c)
        return [(0.0, lo), (c, t), (we - c, t), (we, lo)] if c > 0.01 else [(0.0, t), (we, t)]
    if style == 'shiplap':
        R = min(3.0 * d, 0.4 * we)
        dd = min(d, 0.75 * t)
        if R < 0.01 or dd < 0.01:
            return [(0.0, t), (we, t)]
        pts = [(0.0, t)]
        for k in range(7):
            s = k / 6.0
            pts.append((we - R + s * R, t - dd + dd * math.sqrt(max(0.0, 1.0 - s * s))))
        return pts
    if style == 'weather':
        return [(0.0, t), (we, max(0.2, min(t, v.get('thin', 0.3 * t))))]
    if style == 'log':
        h = d
        n = 12
        return [(we * k / n, t + h * math.sqrt(max(0.0, 1.0 - (2.0 * k / n - 1.0) ** 2))) for k in range(n + 1)]
    return [(0.0, t), (we, t)]


def _inside(p, conv):
    """Is point p inside the convex counter-clockwise polygon conv?"""
    n = len(conv)
    for i in range(n):
        (ax, ay), (bx, by) = conv[i], conv[(i + 1) % n]
        if (bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax) < 0:
            return False
    return True


def lay_boards(outline, holes, v):
    """All solids (local mm) for a face outline (counter-clockwise) with openings.
    Returns ({'boards', 'battens', 'trims', 'backing': [solids]}, board count)."""
    style = v.get('style', 'flat')
    W, t = float(v['width']), float(v['thick'])
    if W < 1 or t <= 0:
        raise ValueError("Board width and thickness must be bigger than that.")
    gap = max(0.2, float(v['gap']))              # never 0: touching faces upset slicers
    lift = max(0.0, v.get('lift', 0.0))
    backing = max(0.0, v.get('backing', 0.0))
    base = lift + backing - (min(0.2, backing * 0.2) if backing > 0 else 0.0)
    rnd = random.Random(int(v.get('seed', 1)))
    wv = min(80.0, max(0.0, v.get('width_var', 0.0))) / 100.0
    tv = max(0.0, v.get('thick_var', 0.0))
    miss = min(90.0, max(0.0, v.get('missing', 0.0))) / 100.0
    Lb = max(0.0, v.get('length', 0.0))
    hg = max(0.0, v.get('hole_gap', 0.0))
    parts = convex_parts(outline)
    x0, x1, y0, y1 = bbox(outline)
    out = {'boards': [], 'battens': [], 'trims': [], 'backing': []}

    # ---- openings, trims round them and corner boards: what the boards keep clear of
    hulls = [h for h in (convex_hull(hl) for hl in holes) if h]
    opening = [grow(h, hg) if hg > 0 else h for h in hulls]          # the gap round each opening
    blockers = list(opening)
    tt = max(0.5, v.get('trim_t', t))
    if v.get('trims'):
        tw = max(1.0, v.get('trim_w', 100.0))
        blockers = []
        for h, op in zip(hulls, opening):
            outer = grow(h, hg + tw)
            ring = [q for pc in (subtract_convex(outer, op) if op else []) for q in clip_to(pc, parts)]
            so = merged_slab(ring, lambda x, y: base, lambda x, y: base + tt)
            if so:
                out['trims'].append(so)
            blockers.append(grow(h, hg + tw + gap))
    # ---- derelict: a rotted, ragged bottom edge and jagged holes, kept clear like openings
    decay = []
    rot_h = max(0.0, v.get('rot_h', 0.0))
    if rot_h > 0:
        step = max(4.0, min(W / 3.0, rot_h / 2.0))
        n = int((x1 - x0) / step) + 3
        hs = []
        for k in range(n + 1):
            h = rot_h * rnd.random() ** 1.6
            if rnd.random() < 0.12:
                h = rot_h * rnd.uniform(0.7, 1.0)          # now and then a deep bite
            hs.append(h)
        for k in range(n):
            xa_, xb_ = x0 - step + k * step, x0 + k * step
            decay.append([(xa_, y0 - 5.0), (xb_, y0 - 5.0), (xb_, y0 + hs[k + 1]), (xa_, y0 + hs[k])])
    nh = max(0.0, v.get('holes', 0.0)) * abs(area2(outline)) / 1e6
    hsz = max(5.0, v.get('hole_size', 120.0))
    tries = 0
    made = 0
    want = int(nh) + (1 if rnd.random() < nh - int(nh) else 0)
    while made < want and tries < want * 30:
        tries += 1
        cx, cy = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        if not any(_inside((cx, cy), p) for p in parts) or any(_inside((cx, cy), op) for op in opening):
            continue
        r = hsz / 2.0 * rnd.uniform(0.6, 1.3)
        k = rnd.randint(7, 11)
        a0 = rnd.uniform(0, math.pi)
        star = []
        for j_ in range(2 * k):
            rr = r * (rnd.uniform(0.8, 1.15) if j_ % 2 == 0 else rnd.uniform(0.4, 0.7))
            an = a0 + math.pi * j_ / k
            # stretched along the grain a little, like real rot
            star.append((cx + rr * math.cos(an) * 0.75, cy + rr * math.sin(an) * 1.25))
        decay += convex_parts(star)
        made += 1
    blockers += decay
    if v.get('corners'):
        cw = max(1.0, v.get('corner_w', 100.0))
        for xa, xb, xs in ((x0, x0 + cw, x0 + cw + gap), (x1 - cw, x1, x1 - cw - gap)):
            rect = [(xa, y0 - 1.0), (xb, y0 - 1.0), (xb, y1 + 1.0), (xa, y1 + 1.0)]
            so = merged_slab(cut_away(clip_to(rect, parts), blockers),
                             lambda x, y: base, lambda x, y: base + tt)
            if so:
                out['trims'].append(so)
            lo_ = min(xa, xs)
            hi_ = max(xb, xs)
            blockers.append([(lo_, y0 - 2.0), (hi_, y0 - 2.0), (hi_, y1 + 2.0), (lo_, y1 + 2.0)])
    if backing > 0:
        so = merged_slab(cut_away(list(parts), opening), lambda x, y: lift, lambda x, y: lift + backing)
        if so:
            out['backing'].append(so)

    # ---- the boards, laid upright in their own frame (rotated by the board angle)
    a = math.radians(float(v.get('angle', 0.0)))
    cparts = [p for p in (clean([rot(q, -a) for q in pt]) for pt in parts) if p]
    cblock = [p for p in (clean([rot(q, -a) for q in b]) for b in blockers if b) if p]
    co = [q for pt in cparts for q in pt]
    X0, X1 = min(q[0] for q in co), max(q[0] for q in co)
    Y0, Y1 = min(q[1] for q in co), max(q[1] for q in co)
    n_est = (X1 - X0) / max(1.0, W * (1 - wv)) * (((Y1 - Y0) / Lb + 1) if Lb > 0 else 1)
    if n_est > 40000:
        raise ValueError("That would be about %d boards - check the sizes (they're real-world mm)." % n_est)

    def back(p):
        x, y = rot((p[0], p[1]), a)
        return (x, y, p[2])

    # ---- pass 1: where every board (or length of board) goes
    segs = []
    edges = []                                     # board edge positions, for battens
    skew_p = min(90.0, max(0.0, v.get('skew_pct', 0.0))) / 100.0
    skew_a = math.radians(min(45.0, max(0.0, v.get('skew_ang', 0.0))))
    xa = X0
    col = 0
    prev_skew = False
    while xa < X1 - 0.5:
        w = W * (1.0 + rnd.uniform(-wv, wv)) if wv > 0 else W
        xb = xa + w
        edges.append(xb)
        lo, hi = xa + gap / 2.0, xb - gap / 2.0
        this_skew = False
        if hi - lo > 0.5:
            # butt joints along the board, staggered from board to board
            if Lb > 0:
                ys, y = [], Y0 - rnd.uniform(0.15, 0.95) * Lb
                while y < Y1:
                    ys.append(y)
                    y += Lb * (1.0 + rnd.uniform(-0.15, 0.15))
                ys.append(y)
            else:
                ys = [Y0 - 1.0, Y1 + 1.0]
            for ya, yb in zip(ys[:-1], ys[1:]):
                sa = ya + (gap / 2.0 if Lb > 0 else 0.0)
                sb = yb - (gap / 2.0 if Lb > 0 else 0.0)
                if sb - sa < 0.5:
                    continue
                if miss > 0 and rnd.random() < miss:
                    continue
                dt = rnd.uniform(-tv, tv) if tv > 0 else 0.0
                sk = 0.0
                if skew_p > 0 and skew_a > 0 and not prev_skew and rnd.random() < skew_p:
                    sk = rnd.choice((-1.0, 1.0)) * skew_a * rnd.uniform(0.4, 1.0)
                    this_skew = True
                segs.append(dict(lo=lo, hi=hi, sa=sa, sb=sb, dt=dt, sk=sk))
        prev_skew = this_skew
        xa = xb
        col += 1

    # skewed boards hang from one nail at the top; their neighbours are cut back clear of them
    def turn_about(p, c, ang):
        x, y = rot((p[0] - c[0], p[1] - c[1]), ang)
        return (x + c[0], y + c[1])
    for sg in segs:
        if not sg['sk']:
            continue
        rect = [(sg['lo'], sg['sa']), (sg['hi'], sg['sa']), (sg['hi'], sg['sb']), (sg['lo'], sg['sb'])]
        flat = cut_away(clip_to(rect, cparts), cblock)
        if not flat:
            sg['sk'] = 0.0
            continue
        top = max(q[1] for pc in flat for q in pc)
        sg['pivot'] = ((sg['lo'] + sg['hi']) / 2.0, top - 0.06 * W)
        sg['foot'] = clean([turn_about(q, sg['pivot'], sg['sk']) for q in rect])
    skews = [sg for sg in segs if sg['sk']]

    # ---- pass 2: the solids
    count = 0
    for sg in segs:
        lo, hi, sa, sb = sg['lo'], sg['hi'], sg['sa'], sg['sb']
        we = hi - lo
        prof = [(lo + u, max(0.25 * z, z + sg['dt'])) for u, z in profile(style, we, t, v)]
        rect = [(lo, sa), (hi, sa), (hi, sb), (lo, sb)]
        others = [grow(o['foot'], gap) for o in skews if o is not sg]
        if sg['sk']:
            # work in the board's own (untilted) frame: bring everything else into it
            c, ang = sg['pivot'], sg['sk']
            into = lambda pl: clean([turn_about(q, c, -ang) for q in pl])
            pieces = cut_away(clip_to(rect, [p for p in map(into, cparts) if p]),
                              [p for p in map(into, cblock + others) if p])
        else:
            near = [o for o in others if overlaps(o, rect)]
            pieces = cut_away(clip_to(rect, cparts), cblock + near)
        pieces = [pc for pc in pieces if abs(area2(pc)) > 1e-3]
        if not pieces:
            continue

        def ztop(x, y, prof=prof):
            for (pa, za), (pb, zb) in zip(prof[:-1], prof[1:]):
                if x <= pb + 1e-9:
                    return base + (za if pb - pa < 1e-12 else za + (zb - za) * (x - pa) / (pb - pa))
            return base + prof[-1][1]
        cuts = [u for u, _ in prof[1:-1]]
        so = merged_slab(pieces, lambda x, y: base, ztop, cuts)
        if not so:
            continue
        if sg['sk']:
            c, ang = sg['pivot'], sg['sk']
            so = so.mapped(lambda p, c=c, ang=ang: turn_about((p[0], p[1]), c, ang) + (p[2],))
        out['boards'].append(so.mapped(back))
        count += 1
    if style == 'batten':
        bw = max(1.0, v.get('batten_w', 60.0))
        bt = max(0.5, v.get('batten_t', t))
        zb0 = base + 0.75 * t
        for xc in edges[:-1]:
            rect = [(xc - bw / 2.0, Y0 - 1.0), (xc + bw / 2.0, Y0 - 1.0), (xc + bw / 2.0, Y1 + 1.0),
                    (xc - bw / 2.0, Y1 + 1.0)]
            pcs = [pc for pc in cut_away(clip_to(rect, cparts), cblock) if abs(area2(pc)) > 1e-3]
            so = merged_slab(pcs, lambda x, y: zb0, lambda x, y: base + t + bt)
            if so:
                out['battens'].append(so.mapped(back))
    return out, count


# ---------------------------------------------------------------------------
# Reading the selected face
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
    for get in (lambda: (v.x(), v.y(), v.z()), lambda: (v.x, v.y, v.z), lambda: (v[0], v[1], v[2])):
        try:
            x, y, z = get()
            return (float(x), float(y), float(z))
        except Exception:
            pass
    return None


def _newell(pts):
    nx = ny = nz = 0.0
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    return v_norm((nx, ny, nz))


def selected_faces(scene):
    out = []
    for e in _items(getattr(scene, 'selection', None)):
        if getattr(e, 'mesh', None) is not None:
            continue
        vs = getattr(e, 'vertices', None)
        if vs is not None and not callable(vs) and len(_items(vs)) >= 3:
            out.append(e)
    return out


def face_frame(face, flip=False, turn=0):
    """(to_world function, outline, holes) for a face: x along, y up the face (mm)."""
    pts = [p for p in (_pos(q) for q in _items(face.vertices)) if p is not None]
    if len(pts) < 3:
        raise ValueError("That face has no corners I can read.")
    n = _newell(pts)
    if flip:
        n = v_mul(n, -1.0)
    if abs(n[2]) < 0.999:
        U = v_norm(v_cross(Z, n))        # level, along the eaves
    else:
        k = max(range(len(pts)), key=lambda i: v_len(v_sub(pts[(i + 1) % len(pts)], pts[i])))
        e = v_sub(pts[(k + 1) % len(pts)], pts[k])
        U = v_norm(v_sub(e, v_mul(n, v_dot(e, n))))
    V = v_cross(n, U)                    # up the slope
    a = math.radians(turn)
    U, V = (v_add(v_mul(U, math.cos(a)), v_mul(V, math.sin(a))),
            v_add(v_mul(U, -math.sin(a)), v_mul(V, math.cos(a))))
    O = pts[0]

    def to2(p):
        d = v_sub(p, O)
        return (v_dot(d, U) / SCALE, v_dot(d, V) / SCALE)
    outline = clean([to2(p) for p in pts])
    holes = []
    for hl in _items(getattr(face, 'holes', None)):
        hp = clean([to2(p) for p in (_pos(q) for q in _items(hl)) if p is not None])
        if hp:
            holes.append(hp)

    def tw(p):
        return v_add(O, v_add(v_mul(U, p[0] * SCALE), v_add(v_mul(V, p[1] * SCALE), v_mul(n, p[2] * SCALE))))
    # 'straight up' in this face's (y, z) terms, for crests and finials
    uy, uz = V[2], n[2]
    L = math.hypot(uy, uz)
    up = (uy / L, uz / L) if L > 1e-9 and uz > 0.05 else (0.0, 1.0)
    return tw, outline, holes, up


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------
def _safe_name(name):
    return "".join(c if c.isalnum() or c in " -_" else "_" for c in name).strip() or "preset"


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


def save_preset(name, values):
    os.makedirs(PRESET_DIR, exist_ok=True)
    d = {'name': name}
    d.update({k: values[k] for k in DEFAULTS if k in values})
    with open(os.path.join(PRESET_DIR, _safe_name(name) + ".json"), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)


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
    """One undo step that adds the board groups and removes faces. Snapshots the
    meshes that change and the group list (like IngeTrazo's own Windowizer)."""
    try:
        from core.history import Command
    except Exception:
        Command = None
    if Command is None or not all(hasattr(m, 'capture_state') for m in meshes):
        return SnapshotImport(mutate)

    class PlankCommand(Command):
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

    return PlankCommand()




# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------
VIEW_DIR = v_norm((-0.30, 0.22, -1.0))       # nearly face-on, a little from the side
LIGHT = v_norm((-0.55, 0.6, 0.55))           # low light from the top left shows the shapes
WOOD = (150, 104, 64)
TRIM = (214, 206, 188)
BACK = (120, 112, 104)


def preview_caption(v):
    txt = "%s - %s, %.0f wide, %.0f thick" % (
        STYLE_NAMES.get(v.get('style'), "Boards").split(" (")[0],
        dict((a, n) for n, a in DIRECTIONS).get(float(v.get('angle', 0.0)), "%.0f deg" % v.get('angle', 0.0)).lower(),
        v['width'], v['thick'])
    if v.get('backing', 0) > 0:
        txt += " - on a backing"
    return txt


def preview_items(v):
    # a close-up: about eight boards across, with a small window
    W = max(10.0, v['width'])
    pw = 8.0 * W
    ph = 6.5 * W
    outline = [(0.0, 0.0), (pw, 0.0), (pw, ph), (0.0, ph)]
    ww, wh = 2.6 * W, 3.2 * W
    wx, wy = pw * 0.55, ph * 0.3
    hole = [(wx, wy), (wx + ww, wy), (wx + ww, wy + wh), (wx, wy + wh)]
    pv = dict(v)
    if pv.get('holes', 0) > 0:
        # the preview is only a small patch: show at least a couple of holes so you can see them
        pv['holes'] = max(pv['holes'], 2.5e6 / (pw * ph))
    res, _ = lay_boards(outline, [hole], pv)
    right = v_norm(v_cross(VIEW_DIR, (0.0, 1.0, 0.0)))
    up = v_cross(right, VIEW_DIR)
    rnd = random.Random(3)
    items = []
    for kind in ('backing', 'boards', 'battens', 'trims'):
        for so in res[kind]:
            if kind == 'backing':
                col = BACK
            elif kind == 'trims':
                col = TRIM
            else:
                k = 1.0 + rnd.uniform(-0.12, 0.12)
                col = tuple(min(255, int(c * k)) for c in WOOD)
            hol = getattr(so, 'holes', {})
            for fi, f in enumerate(so.faces):
                n = _newell(f)
                if v_dot(n, VIEW_DIR) >= 0:
                    continue
                k = 0.5 + 0.5 * max(0.0, v_dot(n, LIGHT))
                depth = sum(v_dot(p, VIEW_DIR) for p in f) / len(f)
                # facets of a rounded top (logs, shiplap) get no outline between them
                edge = not (v.get('style') in ('log', 'shiplap') and abs(n[2]) > 0.2 and abs(n[2]) < 0.999)
                items.append((depth + (1e9 if kind == 'backing' else 0.0),
                              [(v_dot(p, right), -v_dot(p, up)) for p in f],
                              tuple(int(c * k) for c in col), edge,
                              [[(v_dot(p, right), -v_dot(p, up)) for p in h] for h in hol.get(fi, ())]))
    items.sort(key=lambda it: -it[0])
    return items


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

EDDY_TIPS = {'Style': 'The boarding: flat boards, V-jointed, shiplap, weatherboard, board and batten, or '
          'logs.',
 'Boards on the other side of the face': 'Puts the boards on the back of the face instead of '
                                         'the front.',
 'Trim boards round windows and doors': 'Adds a trim board round each opening in the face.',
 'Corner boards at both ends of the face': 'Adds an upright corner board at each end of the '
                                           'face.',
 'Board selected face(s)': 'Boards each face you have selected.',
 'Boards': 'The boards: style, size and which way they run.',
 'Weathering': 'Make it old: odd widths, missing boards, rotted bottoms, holes and skewed '
               'boards.',
 'Trims': 'Trim boards round openings, corner boards and the backing sheet.'}
EDDY_TIPS_END = None


class PlankPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 260)
        self.items = []
        self.msg = ""
        self.caption = ""

    def show_boards(self, v):
        try:
            self.caption = preview_caption(v)
            self.items = preview_items(v)
            self.msg = ""
        except Exception as e:
            self.items, self.msg = [], str(e)
        self.update()

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen, QFont
        from PySide6.QtCore import QPointF, Qt
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(238, 238, 234))
        if not self.items:
            p.drawText(self.rect(), Qt.AlignCenter, self.msg or "No preview")
            p.end()
            return
        xs = [x for it in self.items for x, _ in it[1]]
        ys = [y for it in self.items for _, y in it[1]]
        w, h = self.width() - 16, self.height() - 16
        h_cap = 18
        sc = min(w / ((max(xs) - min(xs)) or 1), (h - h_cap) / ((max(ys) - min(ys)) or 1))
        ox = 8 + (w - (max(xs) - min(xs)) * sc) / 2 - min(xs) * sc
        oy = 8 + h_cap + (h - h_cap - (max(ys) - min(ys)) * sc) / 2 - min(ys) * sc
        from PySide6.QtGui import QPainterPath
        for _, pts, rgb, edge, holes in self.items:
            col = QColor(*rgb)
            p.setBrush(col)
            p.setPen(QPen(col.darker(190), 0.9) if edge else QPen(col, 0.6))
            poly = QPolygonF([QPointF(ox + x * sc, oy + y * sc) for x, y in pts])
            if holes:
                path = QPainterPath()
                path.setFillRule(Qt.OddEvenFill)
                path.addPolygon(poly)
                path.closeSubpath()
                for h in holes:
                    path.addPolygon(QPolygonF([QPointF(ox + x * sc, oy + y * sc) for x, y in h]))
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


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------
# (key, label, min, max, decimals, suffix, tip)
FIELDS = [
    ('width', "A   Board width", 10.0, 2000.0, 1, " mm", "How wide each board is, gap included."),
    ('thick', "B   Board thickness", 0.5, 200.0, 1, " mm", "How far the boards stand out. "
                                                         "24 = 0.3 mm at 1:80."),
    ('gap', "C   Gap between boards", 0.2, 200.0, 2, " mm", "The groove between boards (and at butt "
                                                           "joints). 32 = 0.4 mm at 1:80. Never 0, so no "
                                                           "faces touch."),
    ('depth', "D   V / rebate depth, log height", 0.0, 500.0, 1, " mm",
     "V-jointed: the size of the chamfer on each edge. Shiplap: how deep the rounded rebate is. "
     "Log cabin: how far the logs bulge out."),
    ('thin', "E   Thin edge (weatherboarding)", 0.2, 200.0, 1, " mm",
     "Weatherboarding: how thick the top edge of each board is (the bottom edge is B)."),
    ('batten_w', "F   Batten width", 5.0, 1000.0, 1, " mm", "Board and batten: the batten over each joint."),
    ('batten_t', "G   Batten thickness", 0.5, 200.0, 1, " mm", "How far the battens stand out from the boards."),
    ('length', "H   Board length (0 = full length)", 0.0, 20000.0, 0, " mm",
     "Boards longer than the face is tall (or wide) are made in lengths, with butt joints staggered "
     "from board to board. 0 = one board all the way."),
    ('backing', "I   Backing sheet thickness", 0.0, 500.0, 1, " mm",
     "A solid sheet under the boards, the shape of the face, so it prints as one piece. 0 = none: "
     "the boards sit on the face itself."),
    ('lift', "Gap off the face", 0.0, 5.0, 3, " mm",
     "A hair's gap between the boards and the face, so the slicer doesn't see faces lying exactly on "
     "top of each other. 0.01 mm is plenty."),
]
WFIELDS = [
    ('width_var', "Uneven widths", 0.0, 80.0, 0, " %", "Boards up to this much wider or narrower."),
    ('thick_var', "Thicker and thinner boards", 0.0, 100.0, 1, " mm", "Some boards stand out more, "
                                                                     "some less, by up to this much."),
    ('missing', "Missing boards", 0.0, 90.0, 1, " %", "Leave out this share of boards (or lengths of "
                                                      "board) for a run-down look."),
    ('rot_h', "Rotted bottom edge (how far up)", 0.0, 3000.0, 0, " mm",
     "The bottoms of the boards rotted away into a ragged, jagged edge, up to this high. 0 = none."),
    ('holes', "Jagged holes (per square metre)", 0.0, 50.0, 1, "",
     "Rotted-through holes and broken-out knots in the boards. 0 = none."),
    ('hole_size', "Hole size", 5.0, 2000.0, 0, " mm", "About how big the jagged holes are."),
    ('skew_pct', "Skew boards (hanging off one nail)", 0.0, 60.0, 1, " %",
     "This share of boards hang skew from a nail at the top. The boards beside them are cut back "
     "clear, so nothing overlaps."),
    ('skew_ang', "Skew angle (up to)", 0.0, 45.0, 1, " deg", "How far the skew boards hang over."),
]
TFIELDS = [
    ('hole_gap', "Gap round openings", 0.0, 200.0, 1, " mm",
     "How far the boards stop short of a window or door, so they don't touch its frame."),
    ('trim_w', "Trim width", 5.0, 1000.0, 1, " mm", "The boards framing each opening."),
    ('trim_t', "Trim thickness", 0.5, 200.0, 1, " mm", "Trims and corner boards."),
    ('corner_w', "Corner board width", 5.0, 1000.0, 1, " mm", "Upright boards at each end of the face."),
]


class PlankDialog(QDialog):
    def __init__(self, cur, viewport, tool):
        super().__init__(viewport)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.user_presets = load_presets()
        self._busy = False
        lay = QVBoxLayout(self)
        self.lbl = QLabel("Select a face (a wall, door, floor...), then click 'Board selected face(s)'. "
                          "Sizes are real-world mm.")
        self.lbl.setWordWrap(True)
        self.lbl.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl)
        self.lbl_report = QLabel()
        self.lbl_report.setWordWrap(True)
        self.lbl_report.setVisible(False)
        lay.addWidget(self.lbl_report)

        row = QHBoxLayout()
        lay.addLayout(row)
        self.preview = PlankPreview()
        row.addWidget(self.preview, 1)
        from PySide6.QtWidgets import QTabWidget
        self.tabs = QTabWidget()
        row.addWidget(self.tabs, 1)
        self.sp = {}

        page1 = QWidget()
        form = QFormLayout(page1)
        self.tabs.addTab(page1, "Boards")
        self.cb_style = QComboBox()
        for k, lab in STYLES:
            self.cb_style.addItem(lab, k)
        form.addRow("Style", self.cb_style)
        self.cb_dir = QComboBox()
        for lab, a in DIRECTIONS:
            self.cb_dir.addItem(lab, a)
        self.cb_dir.setToolTip("Which way the boards run. Level weatherboards have their thick edge "
                               "at the bottom.")
        form.addRow("Boards run", self.cb_dir)
        self._fields(form, FIELDS)
        self.cb_flip = QCheckBox("Boards on the other side of the face")
        form.addRow(self.cb_flip)
        self.cb_remove = QCheckBox("Delete the face the boards are on")
        self.cb_remove.setToolTip("Takes the face away once it's boarded, leaving just the boards - for a "
                                  "fence, a gate or a see-through derelict wall (set the backing to 0 so "
                                  "you can see through the holes). Don't use it on the face of a solid "
                                  "wall: that would leave a hole in the wall. Undo puts it back.")
        form.addRow(self.cb_remove)

        page2 = QWidget()
        wf = QFormLayout(page2)
        self.tabs.addTab(page2, "Weathering")
        self._fields(wf, WFIELDS)
        self.sp_seed = QSpinBox()
        self.sp_seed.setRange(1, 9999)
        self.sp_seed.setToolTip("Change this for a different random pattern.")
        wf.addRow("Random pattern", self.sp_seed)

        page3 = QWidget()
        tf = QFormLayout(page3)
        self.tabs.addTab(page3, "Trims")
        self.cb_trims = QCheckBox("Trim boards round windows and doors")
        tf.addRow(self.cb_trims)
        self.cb_corners = QCheckBox("Corner boards at both ends of the face")
        tf.addRow(self.cb_corners)
        self._fields(tf, TFIELDS)

        prow = QHBoxLayout()
        prow.addWidget(QLabel("Preset:"))
        self.cb_preset = QComboBox()
        prow.addWidget(self.cb_preset, 1)
        b_save = QPushButton("Save")
        b_save.setToolTip("Updates the preset you have open (no typing). For a new preset, use Save as.")
        b_saveas = QPushButton("Save as...")
        self.btn_preset_save = b_save
        b_del = QPushButton("Delete")
        b_del.setToolTip("Deletes the preset you have open (your own presets only).")
        b_dir = QPushButton("Folder")
        b_dir.setToolTip("Opens the folder your presets are saved in.")
        for b in (b_save, b_saveas, b_del, b_dir):
            prow.addWidget(b)
        lay.addLayout(prow)
        brow = QHBoxLayout()
        self.b_add = QPushButton("Board selected face(s)")
        self.b_add.setDefault(True)
        b_close = QPushButton("Close")
        brow.addWidget(self.b_add)
        brow.addStretch(1)
        brow.addWidget(b_close)
        lay.addLayout(brow)

        for w in (self.cb_style, self.cb_dir):
            w.currentIndexChanged.connect(self.changed)
        for w in (self.cb_flip, self.cb_trims, self.cb_corners, self.cb_remove):
            w.toggled.connect(self.changed)
        self.sp_seed.valueChanged.connect(self.changed)
        self.cb_preset.currentIndexChanged.connect(self.apply_preset)
        b_save.clicked.connect(self.save_preset)
        b_saveas.clicked.connect(lambda: self.save_preset_as())
        b_del.clicked.connect(self.delete_preset)
        b_dir.clicked.connect(self.open_folder)
        self.b_add.clicked.connect(lambda: self.tool.add_from_dialog(self))
        b_close.clicked.connect(self.close)
        self.refresh_presets()
        self.set_values(cur)

    def _fields(self, form, fields):
        for key, label, lo, hi, dec, suf, tip in fields:
            s = QDoubleSpinBox()
            s.setDecimals(dec)
            s.setRange(lo, hi)
            s.setSuffix(suf)
            s.setKeyboardTracking(True)       # the preview follows as you type
            lab = QLabel(label)
            if tip:
                s.setToolTip(tip)
                lab.setToolTip(tip)
            form.addRow(lab, s)
            self.sp[key] = (s, lab)
            s.valueChanged.connect(self.changed)

    # ---- values ----
    def values(self):
        v = dict(style=self.cb_style.currentData() or 'flat',
                 angle=float(self.cb_dir.currentData() or 0.0),
                 flip=self.cb_flip.isChecked(), trims=self.cb_trims.isChecked(),
                 corners=self.cb_corners.isChecked(), seed=int(self.sp_seed.value()),
                 remove_face=self.cb_remove.isChecked())
        for key, (s, _) in self.sp.items():
            v[key] = float(s.value())
        return v

    def set_values(self, d):
        self._busy = True
        try:
            for cb, key in ((self.cb_style, 'style'), (self.cb_dir, 'angle')):
                if d.get(key) is not None:
                    for i in range(cb.count()):
                        if cb.itemData(i) == d[key]:
                            cb.setCurrentIndex(i)
            for cbx, key in ((self.cb_flip, 'flip'), (self.cb_trims, 'trims'), (self.cb_corners, 'corners'),
                             (self.cb_remove, 'remove_face')):
                cbx.setChecked(bool(d.get(key, DEFAULTS[key])))
            self.sp_seed.setValue(int(d.get('seed', DEFAULTS['seed'])))
            for key, (s, _) in self.sp.items():
                s.setValue(float(d.get(key, DEFAULTS[key])))
        finally:
            self._busy = False
        self.changed()

    def changed(self, *_):
        if self._busy:
            return
        v = self.values()
        st = v['style']
        on = {'depth': st in ('vjoint', 'shiplap', 'log'), 'thin': st == 'weather',
              'batten_w': st == 'batten', 'batten_t': st == 'batten',
              'trim_w': v['trims'], 'trim_t': v['trims'] or v['corners'], 'corner_w': v['corners'],
              'lift': True}
        for key, ok in on.items():
            s, lab = self.sp[key]
            s.setEnabled(ok)
            lab.setEnabled(ok)
        self.preview.show_boards(v)

    def show_report(self, text, bad=False):
        self.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if bad else "#2e7d32"))
        self.lbl_report.setText(text)
        self.lbl_report.setVisible(True)

    # ---- presets ----
    def refresh_presets(self, select=None):
        self.cb_preset.blockSignals(True)
        self.cb_preset.clear()
        self.cb_preset.addItem("-- Custom --", None)
        for name in BUILTIN_PRESETS:
            self.cb_preset.addItem(name + "  (built-in)", name)
        for name in sorted(self.user_presets):
            if name not in BUILTIN_PRESETS:
                self.cb_preset.addItem(name, name)
        for i in range(self.cb_preset.count()):
            if select and self.cb_preset.itemData(i) == select:
                self.cb_preset.setCurrentIndex(i)
        self.cb_preset.blockSignals(False)

    def apply_preset(self, *_):
        name = self.cb_preset.currentData()
        if name and name in BUILTIN_PRESETS:
            self.set_values(BUILTIN_PRESETS[name])
        elif name and name in self.user_presets:
            self.set_values(self.user_presets[name])

    def save_preset(self):
        """Save: updates the preset you have open, with no typing. If it's a built-in one
        (or none is picked), asks for a name instead."""
        name = self.cb_preset.currentData()
        if name and name in self.user_presets and name not in BUILTIN_PRESETS:
            if self.save_preset_as(quiet_name=name):
                self._flash_saved()
        else:
            self.save_preset_as(prefill=(name + " (my copy)") if name else "")

    def _flash_saved(self):
        b = getattr(self, 'btn_preset_save', None)
        if b is None:
            return
        try:
            from PySide6.QtCore import QTimer
            b.setText("Saved")
            QTimer.singleShot(1500, lambda: b.setText("Save"))
        except Exception:
            pass

    def delete_preset(self):
        name = self.cb_preset.currentData()
        if not name or name not in self.user_presets or name in BUILTIN_PRESETS:
            QMessageBox.information(self, PLUGIN_NAME, "Pick one of your own presets to delete "
                                    "(built-in presets can't be deleted).")
            return
        if QMessageBox.question(self, PLUGIN_NAME, "Delete preset '%s'?" % name) != QMessageBox.Yes:
            return
        try:
            os.remove(os.path.join(PRESET_DIR, _safe_name(name) + ".json"))
        except Exception as e:
            QMessageBox.warning(self, PLUGIN_NAME, "Could not delete it:\n%s" % e)
            return
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

    def save_clicked(self):
        self.save_preset()

    def save_preset_as(self, prefill="", quiet_name=None):
        if quiet_name:
            name, ok = quiet_name, True
        else:
            from PySide6.QtWidgets import QLineEdit
            name, ok = QInputDialog.getText(self, "Save preset", "Preset name:", QLineEdit.Normal, prefill)
        name = (name or "").strip()
        if not ok or not name:
            return False
        if name in BUILTIN_PRESETS:
            QMessageBox.warning(self, PLUGIN_NAME, "That name is used by a built-in preset.")
            return False
        if not quiet_name and name in self.user_presets and QMessageBox.question(
                self, PLUGIN_NAME, "Preset '%s' already exists. Overwrite it?" % name) != QMessageBox.Yes:
            return False
        try:
            save_preset(name, self.values())
        except Exception as e:
            QMessageBox.warning(self, PLUGIN_NAME, "Could not save the preset:\n%s" % e)
            return False
        self.user_presets = load_presets()
        self.refresh_presets(select=name)
        return True


class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))




# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
class WoodPlankingTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+O"
    description = "Covers a face with timber boards: plain, V-jointed, shiplap, weatherboarding, " \
                  "board and batten or logs, with trims, round any openings."

    _dialog = None
    _saved = None

    def on_activate(self, viewport):
        dlg = WoodPlankingTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.viewport = viewport
                    dlg.raise_()
                    dlg.activateWindow()
                    return
            except Exception:
                pass
        cur = dict(DEFAULTS)
        if WoodPlankingTool._saved:
            cur.update(WoodPlankingTool._saved)
        dlg = PlankDialog(cur, viewport, self)
        WoodPlankingTool._dialog = dlg

        def closed(*_):
            WoodPlankingTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass

    def add_from_dialog(self, dlg):
        v = dlg.values()
        WoodPlankingTool._saved = dict(v)
        viewport = dlg.viewport
        scene = getattr(viewport, 'scene', None)
        faces = selected_faces(scene) if scene is not None else []
        if not faces:
            QMessageBox.information(dlg, PLUGIN_NAME, "Select a face first.")
            return
        parts, total, problems = [], 0, []
        style = STYLE_NAMES.get(v['style'], "Boards").split(" (")[0]
        many = len(faces) > 1
        for i, f in enumerate(faces):
            try:
                tw, outline, holes, _up = face_frame(f, v['flip'], 0)
                if outline is None:
                    raise ValueError("that face has no area")
                res, count = lay_boards(outline, holes, v)
            except Exception as e:
                problems.append("Face %d: %s" % (i + 1, e))
                continue
            pre = ("Face %d - " % (i + 1)) if many else ""
            for kind, label in (('boards', "Boards - %s - %d boards" % (style, count)),
                                ('battens', "Battens"), ('trims', "Trims"), ('backing', "Backing")):
                if res[kind]:
                    parts.append((pre + label, [s.mapped(tw) for s in res[kind]]))
            total += count
        if not parts:
            QMessageBox.warning(dlg, PLUGIN_NAME, "\n".join(problems) or "No boards fitted on that face.")
            return
        top = "Planking - %s" % style
        done = [f for i, f in enumerate(faces) if not any(p.startswith("Face %d:" % (i + 1)) for p in problems)]
        remove = done if v.get('remove_face') else []
        nf = self.add_to_scene(viewport, parts, top, remove)
        if nf is None:
            return
        msg = "Added %d boards on %d face(s), %d faces." % (total, len(faces) - len(problems), nf)
        if remove:
            msg += " Deleted the face%s under them." % ("s" if len(remove) > 1 else "")
        if len(parts) > 1:
            msg += "\nOne group '%s' holding: %s." % (top, ", ".join(n.split(" - ")[0] if not many else
                                                                     " - ".join(n.split(" - ")[:2])
                                                                     for n, _ in parts))
        if problems:
            msg += "\n" + "\n".join(problems)
        dlg.show_report(msg, bad=bool(problems))

    def add_to_scene(self, viewport, parts, top_name="Planking", remove=()):
        """One parent group holding a child group per part (boards, battens, trims,
        backing). The geometry is already in place, so no transforms are needed."""
        stats = {'faces': 0, 'errors': 0, 'err': None}
        tol = 1e-4 * 0.001

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
            return g

        def mutate(scene):
            from core.mesh import Mesh
            from core.group import Group
            kids = []
            for name, solids in parts:
                mesh = Mesh()
                for so in solids:
                    verts = {}

                    def vx(p):
                        k = (round(p[0] / tol), round(p[1] / tol), round(p[2] / tol))
                        if k not in verts:
                            verts[k] = VertexWrapper(*p)
                        return verts[k]
                    hol = getattr(so, 'holes', {})
                    for fi, pts in enumerate(so.faces):
                        try:
                            hs = [[vx(p) for p in h] for h in hol.get(fi, ())]
                            if hs:
                                try:
                                    mesh.add_face([vx(p) for p in pts], hs)
                                except TypeError:          # an older IngeTrazo: holes one by one
                                    f_ = mesh.add_face([vx(p) for p in pts])
                                    for h in hs:
                                        mesh.add_hole(f_, h)
                            else:
                                mesh.add_face([vx(p) for p in pts])
                            stats['faces'] += 1
                        except Exception as e:
                            stats['errors'] += 1
                            stats['err'] = e
                if stats['faces'] == 0:
                    raise RuntimeError("No faces could be created (%s)." % stats['err'])
                g = make_group(Group, mesh, name)
                g.component = False
                kids.append(g)
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
            viewport.history.execute(make_command(mutate, list({id(m_): m_ for _, m_ in targets}.values()))
                                     if targets else SnapshotImport(mutate))
        except Exception as e:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not add the boards:\n%s" % e)
            return None
        try:
            viewport.notify_scene_changed()
        except Exception:
            pass
        return stats['faces']


def run(viewport=None):
    WoodPlankingTool().on_activate(viewport)
