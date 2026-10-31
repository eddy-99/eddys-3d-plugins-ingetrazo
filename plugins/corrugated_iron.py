# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Corrugated Iron for IngeTrazo
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
3D Corrugated Iron - corrugated, box-profile and flat sheet cladding for IngeTrazo
Select a face (a wall or a roof slope) and it is covered in sheets, trimmed to the face's
outline and round any openings in it, with the corrugations running up it (down a roof)
or across.

Profiles: classic round corrugated iron, box (trapezoidal) sheet and plain flat sheet.
Two ways of making them:
  * 3D print - a flat back with the corrugations on the front, the sheet joints shown as
    fine lines and the end laps as small steps, so the whole face prints lying flat;
  * real sheets - thin sheets that overlap at the side and end laps, as they're put up,
    standing on rails (purlins) - for full size or big scales.
Weathering: rust holes, a rusted ragged bottom edge, missing sheets (showing the rails
behind), sheets hanging skew off one nail and sheets lifting at the foot. Flashings round
openings and corner trims too.

Sizes are real-world millimetres (IngeTrazo stores metres). Ctrl+Alt+I.
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

PLUGIN_NAME = "3D Corrugated Iron"
VERSION = "1"
SCALE = 0.001
PRESET_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Corrugated Iron")
Z = (0.0, 0.0, 1.0)

PROFILES = [
    ("corrugated", "Corrugated (round)"),
    ("box", "Box profile (trapezoidal)"),
    ("flat", "Plain flat sheet"),
]
PROFILE_NAMES = dict(PROFILES)
MODES = [("print", "3D print - flat back"), ("real", "Real sheets - lapped")]
DIRECTIONS = [("Up the face", 0.0), ("Across the face", 90.0)]

DEFAULTS = dict(
    profile='corrugated', mode='print', thin=False, angle=0.0, pitch=76.0, depth=19.0, rib_top=40.0, rib_base=100.0,
    thick=32.0, sheet_w=760.0, sheet_l=2400.0, gap=0.4, step=16.0, lap=150.0, stagger=0.0,
    rails=False, rail_w=100.0, rail_t=50.0, rail_gap=1000.0,
    missing=0.0, rot_h=0.0, holes=0.0, hole_size=150.0, skew_pct=0.0, skew_ang=8.0,
    lifted_pct=0.0, lifted_mm=40.0, seed=1,
    hole_gap=10.0, trims=False, trim_w=150.0, trim_t=16.0,
    corners=False, corner_w=150.0, backing=0.0, lift=0.01, flip=False, remove_face=False)

# ready-made settings, most for printing at 1:80 with a 0.4 mm nozzle (real mm / 80 = model)
BUILTIN_PRESETS = {
    "1:80 print - corrugated iron shed": dict(
        profile='corrugated', mode='print', angle=0.0, pitch=76.0, depth=24.0, thick=32.0, sheet_w=760.0,
        sheet_l=2400.0, gap=0.4, step=16.0, backing=0.0),
    "1:80 print - corrugated roof": dict(
        profile='corrugated', mode='print', angle=0.0, pitch=76.0, depth=24.0, thick=32.0, sheet_w=760.0,
        sheet_l=1800.0, gap=0.4, step=24.0, backing=0.0),
    "1:80 print - derelict tin shed": dict(
        profile='corrugated', mode='print', angle=0.0, pitch=76.0, depth=24.0, thick=32.0, sheet_w=760.0,
        sheet_l=2400.0, gap=0.4, step=16.0, rails=True, rail_w=100.0, rail_t=32.0, rail_gap=1000.0,
        missing=6.0, rot_h=250.0, holes=1.5, hole_size=180.0, skew_pct=6.0, skew_ang=7.0,
        lifted_pct=10.0, lifted_mm=40.0, seed=5),
    "1:80 print - box profile industrial": dict(
        profile='box', mode='print', angle=0.0, pitch=200.0, depth=35.0, rib_top=40.0, rib_base=100.0,
        thick=32.0, sheet_w=1000.0, sheet_l=0.0, gap=0.4, trims=True, corners=True),
    "1:80 print - flat sheet hut": dict(
        profile='flat', mode='print', angle=90.0, thick=32.0, sheet_w=1200.0, sheet_l=2400.0, gap=8.0,
        step=8.0),
    "1:80 resin - thin corrugated sheets": dict(
        profile='corrugated', mode='print', thin=True, angle=0.0, pitch=76.0, depth=24.0, thick=16.0,
        sheet_w=760.0, sheet_l=2400.0, gap=0.4, step=16.0, backing=0.0),
    "Real sheets - corrugated on rails": dict(
        profile='corrugated', mode='real', angle=0.0, pitch=76.0, depth=19.0, thick=1.0, sheet_w=760.0,
        sheet_l=2400.0, lap=150.0, rails=True, rail_w=100.0, rail_t=50.0, rail_gap=1000.0),
}
NUM_KEYS = ('stagger', 'pitch', 'depth', 'rib_top', 'rib_base', 'thick', 'sheet_w', 'sheet_l', 'gap', 'step', 'lap',
            'rail_w', 'rail_t', 'rail_gap', 'missing', 'rot_h', 'holes', 'hole_size', 'skew_pct',
            'skew_ang', 'lifted_pct', 'lifted_mm', 'hole_gap', 'trim_w', 'trim_t', 'corner_w',
            'backing', 'lift')


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




def merged_slab(polys, zbot, ztop, cuts=(), wavy_bottom=False):
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
        cell = 25.0
        grid = {}
        for p in allp:
            grid.setdefault((int(math.floor(p[0] / cell)), int(math.floor(p[1] / cell))), []).append(p)
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
                gx0, gx1 = int(math.floor(min(a[0], b[0]) / cell)) - 1, int(math.floor(max(a[0], b[0]) / cell)) + 1
                gy0, gy1 = int(math.floor(min(a[1], b[1]) / cell)) - 1, int(math.floor(max(a[1], b[1]) / cell)) + 1
                near_ = []
                if (gx1 - gx0 + 1) * (gy1 - gy0 + 1) > len(grid):
                    near_ = allp
                else:
                    for gx in range(gx0, gx1 + 1):
                        for gy in range(gy0, gy1 + 1):
                            near_ += grid.get((gx, gy), ())
                for p in near_:
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
    if wavy_bottom:
        # the back follows the corrugations too: one face per flat strip, like the front
        for grp in groups.values():
            for outer, hls in region_loops(grp)[0]:
                s.add([(x, y, zbot(x, y)) for x, y in reversed(outer)],
                      [[(x, y, zbot(x, y)) for x, y in reversed(h)] for h in hls])
    else:
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


def _inside(p, conv):
    """Is point p inside the convex counter-clockwise polygon conv?"""
    n = len(conv)
    for i in range(n):
        (ax, ay), (bx, by) = conv[i], conv[(i + 1) % n]
        if (bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax) < 0:
            return False
    return True




# ---------------------------------------------------------------------------
# Sheet profiles: the height of the sheet's front at a distance across it
# ---------------------------------------------------------------------------
def wave_points(prof, P, Dd, rib_top, rib_base, x0, lo, hi):
    """[(x, z)] along a sheet from lo to hi: the corrugations, in step with x0 so they run on
    unbroken from sheet to sheet. Straight lines between the points."""
    if prof == 'flat' or Dd <= 0 or P <= 0:
        return [(lo, 0.0), (hi, 0.0)]
    if prof == 'corrugated':
        n = 12                                        # facets per corrugation
        k0 = int(math.floor((lo - x0) / P * n)) - 1
        pts = [(lo, None)]
        k = k0
        while True:
            x = x0 + k * P / n
            k += 1
            if x <= lo + 1e-6:
                continue
            if x >= hi - 1e-6:
                break
            pts.append((x, None))
        pts.append((hi, None))
        return [(x, Dd * (1.0 - math.cos(2 * math.pi * (x - x0) / P)) / 2.0) for x, _ in pts]
    # box / trapezoidal: a rib in the middle of each pitch, flat pans between
    tw = max(0.0, min(rib_top, P * 0.9))
    bw = max(tw + 1.0, min(rib_base, P * 0.98))
    marks = [(0.0, 0.0), ((P - bw) / 2, 0.0), ((P - tw) / 2, Dd), ((P + tw) / 2, Dd), ((P + bw) / 2, 0.0)]

    def zat(x):
        u = (x - x0) % P
        for (ua, za), (ub, zb) in zip(marks, marks[1:] + [(P, 0.0)]):
            if u <= ub + 1e-9:
                return za if ub - ua < 1e-12 else za + (zb - za) * (u - ua) / (ub - ua)
        return 0.0
    xs = [lo]
    c = math.floor((lo - x0) / P) - 1
    while True:
        base_ = x0 + c * P
        c += 1
        done = False
        for u, _ in marks:
            x = base_ + u
            if x <= lo + 1e-6:
                continue
            if x >= hi - 1e-6:
                done = True
                break
            xs.append(x)
        if done or base_ > hi:
            break
    xs.append(hi)
    return [(x, zat(x)) for x in xs]


def lay_sheets(outline, holes, v):
    """All solids (local mm: x along the face, y up it, z out of it) for a face outline
    (counter-clockwise) with openings. Returns ({'sheets', 'rails', 'trims', 'backing'}, count)."""
    prof = v.get('profile', 'corrugated')
    real = v.get('mode', 'print') == 'real'
    # 3D print with a thin sheet: the back follows the corrugations too, the sheet the true
    # thickness E all over (no flat back) - for resin printing
    thin = bool(v.get('thin')) and not real
    P = max(5.0, float(v['pitch']))
    Dd = max(0.0, float(v['depth']))
    t = max(0.2, float(v['thick']))
    W = max(10.0, float(v['sheet_w']))
    if prof != 'flat':
        W = max(1, int(round(W / P))) * P                # a whole number of corrugations
    Lb = max(0.0, float(v.get('sheet_l', 0.0)))
    gap = 0.0 if real else max(0.2, float(v.get('gap', 0.2)))
    lift = max(0.0, v.get('lift', 0.0))
    backing = max(0.0, v.get('backing', 0.0))
    base = lift + backing - (min(0.2, backing * 0.2) if backing > 0 else 0.0)
    rails_on = bool(v.get('rails'))
    rail_t = max(1.0, v.get('rail_t', 50.0))
    sheet_base = base + (rail_t + 0.3 if (rails_on and real) else 0.0)
    lap_e = max(0.0, v.get('lap', 150.0)) if real else 0.0
    clear = t + 0.5                    # worked out properly once the rows are known
    lap_s = (P if prof != 'flat' else 50.0) if real else 0.0
    step = max(0.0, v.get('step', 16.0)) if not real else clear
    rnd = random.Random(int(v.get('seed', 1)))
    miss = min(90.0, max(0.0, v.get('missing', 0.0))) / 100.0
    lift_p = min(90.0, max(0.0, v.get('lifted_pct', 0.0))) / 100.0
    lift_mm = max(0.0, v.get('lifted_mm', 0.0))
    hg = max(0.0, v.get('hole_gap', 0.0))
    parts = convex_parts(outline)
    x0, x1, y0, y1 = bbox(outline)
    out = {'sheets': [], 'rails': [], 'trims': [], 'backing': []}

    # ---- openings, flashings round them and corner trims
    hulls = [h for h in (convex_hull(hl) for hl in holes) if h]
    opening = [grow(h, hg) if hg > 0 else h for h in hulls]
    blockers = list(opening)
    tt = max(0.5, v.get('trim_t', 25.0))
    if v.get('trims'):
        tw_ = max(1.0, v.get('trim_w', 100.0))
        blockers = []
        for h, op in zip(hulls, opening):
            outer = grow(h, hg + tw_)
            ring = [q for pc in (subtract_convex(outer, op) if op else []) for q in clip_to(pc, parts)]
            so = merged_slab(ring, lambda x, y: base, lambda x, y: base + tt + Dd)
            if so:
                out['trims'].append(so)
            blockers.append(grow(h, hg + tw_ + 1.0))
    rail_block = list(blockers)
    # ---- derelict: a rusted, ragged bottom edge and rust holes
    decay = []
    rot_h = max(0.0, v.get('rot_h', 0.0))
    if rot_h > 0:
        stp = max(4.0, min(P / 1.5, rot_h / 3.0))
        n = int((x1 - x0) / stp) + 3
        hs = []
        for k in range(n + 1):
            h = rot_h * rnd.random() ** 1.4
            if rnd.random() < 0.15:
                h = rot_h * rnd.uniform(0.7, 1.0)
            hs.append(h)
        for k in range(n):
            xa_, xb_ = x0 - stp + k * stp, x0 + k * stp
            decay.append([(xa_, y0 - 5.0), (xb_, y0 - 5.0), (xb_, y0 + hs[k + 1]), (xa_, y0 + hs[k])])
    nh = max(0.0, v.get('holes', 0.0)) * abs(area2(outline)) / 1e6
    hsz = max(5.0, v.get('hole_size', 150.0))
    tries = made = 0
    want = int(nh) + (1 if rnd.random() < nh - int(nh) else 0)
    while made < want and tries < want * 30:
        tries += 1
        cx, cy = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        if not any(_inside((cx, cy), p) for p in parts) or any(_inside((cx, cy), op) for op in opening):
            continue
        r = hsz / 2.0 * rnd.uniform(0.6, 1.3)
        k = rnd.randint(8, 13)
        a0 = rnd.uniform(0, math.pi)
        star = []
        for j_ in range(2 * k):
            rr = r * (rnd.uniform(0.75, 1.15) if j_ % 2 == 0 else rnd.uniform(0.35, 0.7))
            an = a0 + math.pi * j_ / k
            star.append((cx + rr * math.cos(an), cy + rr * math.sin(an)))   # rust: no grain
        decay += convex_parts(star)
        made += 1
    blockers += decay
    if v.get('corners'):
        cw = max(1.0, v.get('corner_w', 100.0))
        for xa, xb, xs in ((x0, x0 + cw, x0 + cw + 1.0), (x1 - cw, x1, x1 - cw - 1.0)):
            rect = [(xa, y0 - 1.0), (xb, y0 - 1.0), (xb, y1 + 1.0), (xa, y1 + 1.0)]
            so = merged_slab(cut_away(clip_to(rect, parts), blockers),
                             lambda x, y: base, lambda x, y: base + tt + Dd)
            if so:
                out['trims'].append(so)
            lo_, hi_ = min(xa, xs), max(xb, xs)
            blk = [(lo_, y0 - 2.0), (hi_, y0 - 2.0), (hi_, y1 + 2.0), (lo_, y1 + 2.0)]
            blockers.append(blk)
            rail_block.append(blk)
    if backing > 0:
        so = merged_slab(cut_away(list(parts), opening), lambda x, y: lift, lambda x, y: lift + backing)
        if so:
            out['backing'].append(so)

    # ---- the sheets, laid in their own frame (corrugations running up it), rotated by the angle
    a = math.radians(float(v.get('angle', 0.0)))
    cparts = [p for p in (clean([rot(q, -a) for q in pt]) for pt in parts) if p]
    cblock = [p for p in (clean([rot(q, -a) for q in b]) for b in blockers if b) if p]
    rblock = [p for p in (clean([rot(q, -a) for q in b]) for b in rail_block if b) if p]
    co = [q for pt in cparts for q in pt]
    X0, X1 = min(q[0] for q in co), max(q[0] for q in co)
    Y0, Y1 = min(q[1] for q in co), max(q[1] for q in co)
    n_est = (X1 - X0) / W * (((Y1 - Y0) / Lb + 1) if Lb > 0 else 1)
    if n_est > 20000:
        raise ValueError("That would be about %d sheets - check the sizes (they're real-world mm)." % n_est)

    def back(p):
        x, y = rot((p[0], p[1]), a)
        return (x, y, p[2])

    # pass 1: where every sheet goes - columns across, rows up. The end laps are in line, or
    # staggered: every other column starts with a shorter sheet, so its laps fall part way up
    stag = min(95.0, max(0.0, float(v.get('stagger', 0.0)))) / 100.0 if Lb > 0 else 0.0

    def rows_for(col):
        if Lb <= 0:
            return [(Y0 - 1.0, Y1 + 1.0)]
        off = (col % 2) * stag * Lb
        out_, y = [], Y0
        first = Lb - off if off > 1.0 else Lb
        nxt = y + first
        while y < Y1 - 1.0:
            out_.append((y, min(Y1 + 1.0, nxt)))
            y = nxt
            nxt = y + Lb
        # a sliver of sheet at the top is joined onto the one below it
        if len(out_) > 1 and out_[-1][1] - out_[-1][0] < 0.25 * Lb:
            out_[-2:] = [(out_[-2][0], out_[-1][1])]
        if len(out_) > 1 and out_[0][1] - out_[0][0] < 0.25 * Lb:
            out_[:2] = [(out_[0][0], out_[1][1])]
        return out_
    skew_p = min(90.0, max(0.0, v.get('skew_pct', 0.0))) / 100.0
    skew_a = math.radians(min(45.0, max(0.0, v.get('skew_ang', 0.0))))
    rows = []
    if Lb > 0:
        y = Y0
        while y < Y1 - 1.0:
            rows.append((y, min(Y1 + 1.0, y + Lb)))
            y += Lb
    else:
        rows = [(Y0 - 1.0, Y1 + 1.0)]
    all_rows = [rows_for(0), rows_for(1)]
    if real and max(len(r_) for r_ in all_rows) > 1:
        # how far a lapping sheet stands off the one under it: leaning out towards its foot, it
        # must still clear the sheet below all along the lap - the shortest sheet decides
        spans = [(yb - ya) + (lap_e if r > 0 else 0.0) for rows in all_rows for r, (ya, yb) in enumerate(rows)
                 if len(rows) > 1]
        sp_min = max(lap_e * 1.5, min(spans))
        clear = (t + 0.5) * sp_min / max(1.0, sp_min - lap_e)
        step = clear
    segs = []
    xa = X0
    col = 0
    while xa < X1 - 0.5:
        xb = xa + W
        rows = rows_for(col)
        for r, (ya, yb) in enumerate(rows):
            if miss > 0 and rnd.random() < miss:
                continue
            lo = xa - (lap_s if col > 0 else 0.0) + gap / 2.0
            hi = xb - gap / 2.0
            sa = ya - (lap_e if r > 0 else 0.0) + (gap / 2.0 if r > 0 else 0.0)
            sb = yb - (gap / 2.0 if r < len(rows) - 1 else 0.0)
            sk = 0.0
            if skew_p > 0 and skew_a > 0 and rnd.random() < skew_p:
                sk = rnd.choice((-1.0, 1.0)) * skew_a * rnd.uniform(0.4, 1.0)
            ex = lift_mm * rnd.uniform(0.5, 1.0) if (lift_p > 0 and rnd.random() < lift_p) else 0.0
            segs.append(dict(lo=lo, hi=hi, sa=sa, sb=sb, sk=sk, ex=ex, col=col, row=r, nrows=len(rows)))
        xa = xb
        col += 1

    ncols = col
    # real sheets: where four sheets meet at the corner of a lap, two of them have that corner
    # cut off (as roofers mitre them), so only two lie over each other there
    for sg in segs:
        sg['crops'] = []
    rows = rows_for(0)
    if real and lap_s > 0 and lap_e > 0 and len(rows) > 1 and stag == 0:
        last = len(rows) - 1
        for sg in segs:
            c, r = sg['col'], sg['row']
            corners = []
            if c > 0 and r < last and c % 2 == 1:                 # right-hand, lower of the four
                corners.append((X0 + c * W, rows[r][1]))
            if c + 1 < ncols and r > 0 and (c + 1) % 2 == 1:      # left-hand, upper
                corners.append((X0 + (c + 1) * W, rows[r - 1][1]))
            if c + 1 < ncols and r < last and (c + 1) % 2 == 0:   # left-hand, lower
                corners.append((X0 + (c + 1) * W, rows[r][1]))
            if c > 0 and r > 0 and c % 2 == 0:                    # right-hand, upper
                corners.append((X0 + c * W, rows[r - 1][1]))
            for cx_, cy_ in corners:
                sg['crops'].append([(cx_ - lap_s - 0.5, cy_ - lap_e - 0.5), (cx_ + 0.5, cy_ - lap_e - 0.5),
                                    (cx_ + 0.5, cy_ + 0.5), (cx_ - lap_s - 0.5, cy_ + 0.5)])

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
        sg['pivot'] = ((sg['lo'] + sg['hi']) / 2.0, top - 0.05 * (sg['sb'] - sg['sa']))
        sg['foot'] = clean([turn_about(q, sg['pivot'], sg['sk']) for q in rect])
    skews = [sg for sg in segs if sg['sk']]

    # pass 2: the solids
    count = 0
    feet = []                                       # where sheets lie, for the rails behind
    for sg in segs:
        lo, hi, sa, sb = sg['lo'], sg['hi'], sg['sa'], sg['sb']
        rect = [(lo, sa), (hi, sa), (hi, sb), (lo, sb)]
        others = [grow(o['foot'], 1.0) for o in skews if o is not sg]
        if sg['sk']:
            c, ang = sg['pivot'], sg['sk']
            into = lambda pl: clean([turn_about(q, c, -ang) for q in pl])
            pieces = cut_away(clip_to(rect, [p for p in map(into, cparts) if p]),
                              [p for p in map(into, cblock + others + sg['crops']) if p])
        else:
            near = [o for o in others if overlaps(o, rect)]
            pieces = cut_away(clip_to(rect, cparts), cblock + near + sg['crops'])
        pieces = [pc for pc in pieces if abs(area2(pc)) > 1e-3]
        if not pieces:
            continue
        wp = wave_points(prof, P, Dd, v.get('rib_top', 40.0), v.get('rib_base', 100.0), X0, lo, hi)
        # stand-off: a sheet lapping over its neighbour stands out a little (real sheets), and every
        # sheet leans out a little towards its foot, so the end laps show as a step
        # staggered real sheets: the odd columns stand clear of a whole end lap of the even ones
        lvl = (sg['col'] % 2) * (clear if stag == 0 else clear + t + 0.5) if real else 0.0
        span = max(1.0, sb - sa)
        lean = (step if sg['nrows'] > 1 else 0.0) + sg['ex']

        def wave(x, wp=wp):
            for (pa, za), (pb, zb) in zip(wp[:-1], wp[1:]):
                if x <= pb + 1e-9:
                    return za if pb - pa < 1e-12 else za + (zb - za) * (x - pa) / (pb - pa)
            return wp[-1][1]

        def ztop(x, y, wave=wave, lvl=lvl, span=span, lean=lean, sb=sb):
            return sheet_base + lvl + t + wave(x) + lean * (sb - y) / span
        if real or thin:
            def zbot(x, y, ztop=ztop):
                return ztop(x, y) - t
        else:
            def zbot(x, y):
                return sheet_base
        cuts = [u for u, _ in wp[1:-1]]
        so = merged_slab(pieces, zbot, ztop, cuts, wavy_bottom=real or thin)
        if not so:
            continue
        if sg['sk']:
            c, ang = sg['pivot'], sg['sk']
            so = so.mapped(lambda p, c=c, ang=ang: turn_about((p[0], p[1]), c, ang) + (p[2],))
            feet += [q for q in (clean([turn_about(pt, c, ang) for pt in pc]) for pc in pieces) if q]
        else:
            feet += pieces
        out['sheets'].append(so.mapped(back))
        count += 1
    # ---- the rails (purlins) the sheets are fixed to, across the corrugations
    if rails_on:
        rw = max(5.0, v.get('rail_w', 100.0))
        rg = max(rw + 50.0, v.get('rail_gap', 1000.0))
        n_r = max(1, int(round((Y1 - Y0) / rg)))
        ys = [Y0 + (Y1 - Y0) * (k + 0.5) / n_r for k in range(n_r)]
        for yc in ys:
            strip = [(X0 - 1.0, yc - rw / 2), (X1 + 1.0, yc - rw / 2), (X1 + 1.0, yc + rw / 2), (X0 - 1.0, yc + rw / 2)]
            pcs = cut_away(clip_to(strip, cparts), rblock)
            if not real:
                # printing: the rails lie on the bed beside the sheets, so they only show where a
                # sheet is missing or rusted through
                pcs = cut_away(pcs, [grow(f, 0.3) for f in feet if overlaps(f, strip)])
            pcs = [pc for pc in pcs if abs(area2(pc)) > 1e-2]
            so = merged_slab(pcs, lambda x, y: base, lambda x, y: base + rail_t)
            if so:
                out['rails'].append(so.mapped(back))
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
    """One undo step that adds the sheet groups and removes faces. Snapshots the
    meshes that change and the group list (like IngeTrazo's own Windowizer)."""
    try:
        from core.history import Command
    except Exception:
        Command = None
    if Command is None or not all(hasattr(m, 'capture_state') for m in meshes):
        return SnapshotImport(mutate)

    class SheetCommand(Command):
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

    return SheetCommand()




# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------
VIEW_DIR = v_norm((-0.30, 0.22, -1.0))       # nearly face-on, a little from the side
LIGHT = v_norm((-0.55, 0.6, 0.55))           # low light from the top left shows the shapes
METAL = (150, 156, 160)
RUST = (150, 92, 58)
TRIM = (190, 192, 188)
BACK = (110, 104, 98)
RAIL = (120, 92, 62)


def preview_caption(v):
    txt = "%s - %s" % (PROFILE_NAMES.get(v.get('profile'), "Sheets").split(" (")[0],
                       "3D print" if v.get('mode') == 'print' else "real sheets")
    if v.get('profile') != 'flat':
        txt += ", %.0f pitch, %.0f deep" % (v['pitch'], v['depth'])
    return txt


def preview_items(v):
    # a close-up: two sheets across and a bit, with a small window
    W = max(100.0, v['sheet_w'])
    pw = 2.4 * W
    ph = 1.9 * W
    outline = [(0.0, 0.0), (pw, 0.0), (pw, ph), (0.0, ph)]
    ww, wh = 0.55 * W, 0.6 * W
    wx, wy = pw * 0.6, ph * 0.35
    hole = [(wx, wy), (wx + ww, wy), (wx + ww, wy + wh), (wx, wy + wh)]
    pv = dict(v)
    if pv.get('sheet_l', 0) > 0:
        pv['sheet_l'] = min(pv['sheet_l'], ph * 0.62)        # show an end lap in the patch
    if pv.get('holes', 0) > 0:
        pv['holes'] = max(pv['holes'], 2.5e6 / (pw * ph))
    if pv.get('rails'):
        pv['rail_gap'] = min(pv.get('rail_gap', 1000.0), ph / 2.0)
    res, _ = lay_sheets(outline, [hole], pv)
    right = v_norm(v_cross(VIEW_DIR, (0.0, 1.0, 0.0)))
    up = v_cross(right, VIEW_DIR)
    rnd = random.Random(3)
    items = []
    for kind in ('backing', 'rails', 'sheets', 'trims'):
        for so in res[kind]:
            if kind == 'backing':
                col = BACK
            elif kind == 'trims':
                col = TRIM
            elif kind == 'rails':
                col = RAIL
            else:
                base_ = RUST if (v.get('rot_h', 0) > 0 or v.get('holes', 0) > 0) and rnd.random() < 0.35 else METAL
                k = 1.0 + rnd.uniform(-0.06, 0.06)
                col = tuple(min(255, int(c * k)) for c in base_)
            hol = getattr(so, 'holes', {})
            for fi, f in enumerate(so.faces):
                n = _newell(f)
                if v_dot(n, VIEW_DIR) >= 0:
                    continue
                k = 0.45 + 0.55 * max(0.0, v_dot(n, LIGHT))
                depth = sum(v_dot(p, VIEW_DIR) for p in f) / len(f)
                # the facets of a round corrugation get no outline between them
                edge = not (v.get('profile') == 'corrugated' and kind == 'sheets' and abs(n[2]) < 0.999 and abs(n[2]) > 0.2)
                items.append((depth + (1e9 if kind == 'backing' else 1e8 if kind == 'rails' else 0.0),
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

EDDY_TIPS = {'Sheets': "The sheets: profile, how they're made, sizes and which way they run.",
 'Profile': 'The sheet: round corrugated iron, box (trapezoidal) profile, or plain flat sheet.',
 'Make': '3D print: flat back, corrugations on the front. Real sheets: thin lapped sheets.',
 'Corrugations run': 'Up the face (and down a roof), or across it.',
 'Random pattern': 'Change this for a different random pattern of rust, missing and skew '
                   'sheets.'}
EDDY_TIPS_END = None


class SheetPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 260)
        self.items = []
        self.msg = ""
        self.caption = ""

    def show_sheets(self, v):
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
# Sizes: the lettered drawing (front of the sheets, a cut across the corrugations,
# and a cut up the sheets through an end lap)
# ---------------------------------------------------------------------------
def sheet_sizes_drawing(v):
    """[panel]: each {'title', 'box': (x0, y0, x1, y1) as parts of the widget, 'polys': [(pts, rgb)],
    'lines': [(p, q, rgb)], 'dims': [(letter, p, q, (ox, oy), off)], 'stretch': x exaggeration}.
    Points in mm, y up."""
    prof, real = v['profile'], v['mode'] == 'real'
    thin = bool(v.get('thin')) and not real
    P = max(5.0, v['pitch'])
    Dd = 0.0 if prof == 'flat' else max(0.0, v['depth'])
    E = max(0.2, v['thick'])
    Fw = max(50.0, v['sheet_w'])
    G = v['sheet_l'] if v['sheet_l'] > 0 else 2.0 * Fw
    H = max(0.2, v['gap'])
    I_ = max(0.0, v['step'])
    J = max(0.0, v['lap'])
    MET, MET2, LINE = (172, 178, 182), (150, 157, 162), (95, 100, 106)
    panels = []

    # --- front: two sheets across, two up ---
    polys, lines, dims = [], [], []
    Hs = max(H, Fw * 0.025)                 # the joint drawn wide enough to see
    rows = [(0.0, G), (G - (J if real else 0.0), 2 * G - (J if real else 0.0))]
    stg = min(95.0, max(0.0, v.get('stagger', 0.0))) / 100.0 * G if v['sheet_l'] > 0 else 0.0
    for r in range(2):
        for c in range(2):
            ya, yb = rows[r]
            if c == 1 and stg > 0:              # the second column's laps are staggered up
                ya = 0.0 if r == 0 else ya - stg
                yb = yb - stg if r == 0 else rows[1][1]
            if real:
                xa = c * (Fw - P * 0.5)            # real sheets lap one corrugation at the sides
            else:
                xa = c * (Fw + Hs)
            polys.append(([(xa, ya), (xa + Fw, ya), (xa + Fw, yb), (xa, yb)], MET if (r + c) % 2 == 0 else MET2))
            if prof != 'flat':
                x = xa + P / 2
                while x < xa + Fw - 1e-6:
                    lines.append(((x, ya), (x, yb), LINE))
                    x += P
    top = rows[1][1]
    dims.append(('F', (0.0, top), (Fw, top), (0, 1), 12))
    if stg > 0:
        xk = (2 * Fw - P * 0.5) if real else (2 * Fw + Hs)
        dims.append(('K', (xk, G - stg), (xk, G), (1, 0), 12 if not real else 30))
    dims.append(('G', (0.0, rows[0][0]), (0.0, rows[0][1]), (-1, 0), 12))
    if real:
        if J > 0:
            xr = 2 * Fw - P * 0.5
            dims.append(('J', (xr, rows[1][0]), (xr, rows[0][1]), (1, 0), 12))
    else:
        dims.append(('H', (Fw, G * 0.5), (Fw + Hs, G * 0.5), (0, -1), 0))
    panels.append({'title': "Front", 'box': (0.0, 0.0, 0.5, 1.0), 'polys': polys, 'lines': lines,
                   'dims': dims, 'stretch': 1.0})

    # --- cut across the corrugations ---
    polys, lines, dims = [], [], []
    W = 2.5 * P if prof != 'flat' else max(P, Fw * 0.25)
    wav = wave_points(prof, P, Dd, v['rib_top'], v['rib_base'], 0.0, 0.0, W)
    if real or thin:
        out = [(x, z + E) for x, z in wav] + [(x, z) for x, z in reversed(wav)]
        polys.append((out, MET))
        dims.append(('E', (0.0, 0.0), (0.0, E), (-1, 0), 12))
    else:
        out = [(x, z + E) for x, z in wav] + [(W, 0.0), (0.0, 0.0)]
        polys.append((out, MET))
        dims.append(('E', (0.0, 0.0), (0.0, E), (-1, 0), 12))
    lines.append(((-P * 0.15, -E * 0.5 if (real or thin) else 0.0), (W + P * 0.15, -E * 0.5 if (real or thin) else 0.0),
                  (150, 150, 150)))
    if prof == 'corrugated':
        dims.append(('A', (P / 2, E + Dd), (1.5 * P, E + Dd), (0, 1), 12))
        dims.append(('B', (2.0 * P, E), (2.0 * P, E + Dd), (1, 0), 8))
    elif prof == 'box':
        tw = max(0.0, min(v['rib_top'], P * 0.9))
        bw = max(tw + 1.0, min(v['rib_base'], P * 0.98))
        dims.append(('A', ((P - tw) / 2, E + Dd), ((3 * P - tw) / 2, E + Dd), (0, 1), 26))
        dims.append(('C', ((P - tw) / 2, E + Dd), ((P + tw) / 2, E + Dd), (0, 1), 8))
        dims.append(('D', ((P - bw) / 2, 0.0), ((P + bw) / 2, 0.0), (0, -1), 10))
        dims.append(('B', ((3 * P + bw) / 2 + 2, E), ((3 * P + bw) / 2 + 2, E + Dd), (1, 0), 8))
    panels.append({'title': "Cut across", 'box': (0.52, 0.0, 1.0, 0.42), 'polys': polys, 'lines': lines,
                   'dims': dims, 'stretch': 1.0})

    # --- cut up the sheets, through the end lap (y up, x out from the face) ---
    polys, lines, dims = [], [], []
    Gs = min(G, max(Fw * 0.6, 600.0))       # only the ends near the lap are drawn
    t_s = E + Dd
    if real:
        lo = [(0.0, G - Gs), (t_s, G - Gs), (t_s, G), (0.0, G)]
        hi = [(t_s, G - J), (2 * t_s, G - J), (2 * t_s, G - J + Gs), (t_s, G - J + Gs)]
        polys += [(lo, MET2), (hi, MET)]
        if J > 0:
            dims.append(('J', (2 * t_s, G - J), (2 * t_s, G), (1, 0), 12))
        if v.get('rails'):
            rt = max(1.0, v['rail_t'])
            polys.append(([(-rt, G - Gs * 0.5 - 50), (0.0, G - Gs * 0.5 - 50), (0.0, G - Gs * 0.5 + 50),
                           (-rt, G - Gs * 0.5 + 50)], (120, 92, 62)))
    else:
        # each sheet stands out I more at its foot than its head
        lo = [(0.0, G - Gs), (t_s + I_ * Gs / G, G - Gs), (t_s, G), (0.0, G)]
        hi = [(0.0, G), (t_s + I_, G), (t_s + I_ * (1 - Gs / G), G + Gs), (0.0, G + Gs)]
        polys += [(lo, MET2), (hi, MET)]
        if I_ > 0:
            dims.append(('I', (t_s, G), (t_s + I_, G), (0, -1), 12))
        dims.append(('E', (0.0, G + Gs * 0.8), (E, G + Gs * 0.8), (0, 1), 10))
    lines.append(((-E * 0.2 if not real else 0.0, G - Gs - 40), (-E * 0.2 if not real else 0.0, G + Gs + 40),
                  (150, 150, 150)))
    width = max(p[0] for pp, _ in polys for p in pp) or 1.0
    panels.append({'title': "Cut up the sheets (across exaggerated)", 'box': (0.52, 0.46, 1.0, 1.0),
                   'polys': polys, 'lines': lines, 'dims': dims, 'stretch': max(1.0, Gs * 0.45 / width)})
    return panels


class SheetSizes(QWidget):
    """The lettered sizes drawing: each size has the letter its box has in the window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 260)
        self.panels = None
        self.msg = ""

    def show_sizes(self, v):
        try:
            self.panels = sheet_sizes_drawing(v)
            self.msg = ""
        except Exception as e:
            self.panels, self.msg = None, str(e)
        self.update()

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen, QFont, QBrush
        from PySide6.QtCore import QPointF, Qt, QRectF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(252, 252, 250))
        if not self.panels:
            p.drawText(self.rect().adjusted(10, 10, -10, -10), Qt.AlignCenter | Qt.TextWordWrap,
                       self.msg or "No drawing")
            p.end()
            return
        Wd, Hd = self.width(), self.height()
        blue = QColor(20, 90, 200)
        f_small = QFont()
        f_small.setPointSize(7)
        f_bold = QFont()
        f_bold.setPointSize(8)
        f_bold.setBold(True)
        for pan in self.panels:
            bx0, by0, bx1, by1 = pan['box']
            M = 26.0
            x0, y0 = bx0 * Wd + M, by0 * Hd + M
            w, h = (bx1 - bx0) * Wd - 2 * M, (by1 - by0) * Hd - 2 * M - 12
            k = pan['stretch']
            pts = [q for pp, _ in pan['polys'] for q in pp]
            pts += [q for a, b, _ in pan['lines'] for q in (a, b)]
            xs = [q[0] * k for q in pts]
            ys = [q[1] for q in pts]
            sc = min(w / ((max(xs) - min(xs)) or 1), h / ((max(ys) - min(ys)) or 1))
            ox = x0 + (w - (max(xs) - min(xs)) * sc) / 2 - min(xs) * sc
            oy = y0 + (h - (max(ys) - min(ys)) * sc) / 2 + max(ys) * sc

            def T(q):
                return QPointF(ox + q[0] * k * sc, oy - q[1] * sc)
            for pp, rgb in pan['polys']:
                col = QColor(*rgb)
                p.setBrush(col)
                p.setPen(QPen(col.darker(150), 0.8))
                p.drawPolygon(QPolygonF([T(q) for q in pp]))
            for a, b, rgb in pan['lines']:
                p.setPen(QPen(QColor(*rgb), 0.7))
                p.drawLine(T(a), T(b))
            p.setFont(f_small)
            p.setPen(QColor(90, 90, 90))
            p.drawText(QRectF(bx0 * Wd + 4, by1 * Hd - 16, (bx1 - bx0) * Wd - 8, 14), Qt.AlignLeft,
                       pan['title'])
            p.setFont(f_bold)
            for letter, p1, p2, o, off in pan['dims']:
                a, b = T(p1), T(p2)
                ox_, oy_ = o[0], -o[1]
                L = math.hypot(ox_, oy_) or 1.0
                ox_, oy_ = ox_ / L, oy_ / L
                a2 = QPointF(a.x() + ox_ * off, a.y() + oy_ * off)
                b2 = QPointF(b.x() + ox_ * off, b.y() + oy_ * off)
                p.setPen(QPen(blue, 0.8))
                if off:
                    p.drawLine(a, QPointF(a2.x() + ox_ * 3, a2.y() + oy_ * 3))
                    p.drawLine(b, QPointF(b2.x() + ox_ * 3, b2.y() + oy_ * 3))
                p.drawLine(a2, b2)
                dx, dy = b2.x() - a2.x(), b2.y() - a2.y()
                Ld = math.hypot(dx, dy) or 1.0
                tx, ty = (dx - dy) / Ld * 3, (dy + dx) / Ld * 3
                for q in (a2, b2):
                    p.drawLine(QPointF(q.x() - tx, q.y() - ty), QPointF(q.x() + tx, q.y() + ty))
                mx = (a2.x() + b2.x()) / 2 + ox_ * 10
                my = (a2.y() + b2.y()) / 2 + oy_ * 10
                r = 7.0
                p.setBrush(QBrush(QColor(255, 255, 255)))
                p.drawEllipse(QPointF(mx, my), r, r)
                p.drawText(QRectF(mx - r, my - r, 2 * r, 2 * r), Qt.AlignCenter, letter)
        p.end()


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------
# (key, label, min, max, decimals, suffix, tip)
FIELDS = [
    ('pitch', "A   Pitch (one corrugation)", 5.0, 2000.0, 1, " mm",
     "From one corrugation (or rib) to the next. Corrugated iron is about 76 mm; box profile 150-200."),
    ('depth', "B   Depth", 0.0, 500.0, 1, " mm",
     "How deep the corrugations (or ribs) are. Real corrugated iron is about 19 mm; for 1:80 printing "
     "24-32 mm shows better."),
    ('rib_top', "C   Rib top width (box)", 1.0, 2000.0, 1, " mm", "Box profile: across the flat top of each rib."),
    ('rib_base', "D   Rib foot width (box)", 2.0, 2000.0, 1, " mm",
     "Box profile: across the foot of each rib (wider than C - the difference is the sloping sides)."),
    ('thick', "E   Thickness", 0.2, 500.0, 1, " mm",
     "3D print: the flat plate behind the corrugations (32 = 0.4 mm at 1:80). 3D print with 'Thin sheet' "
     "ticked, and real sheets: the thickness of the tin itself, the same all over (for resin at 1:80, "
     "16 mm = 0.2 mm)."),
    ('sheet_w', "F   Sheet width", 50.0, 5000.0, 0, " mm",
     "How much of the face each sheet covers across (made a whole number of corrugations)."),
    ('sheet_l', "G   Sheet length (0 = full height)", 0.0, 20000.0, 0, " mm",
     "Sheets come in lengths: taller faces get end laps every this far. 0 = one sheet all the way."),
    ('stagger', "K   Stagger end laps", 0.0, 95.0, 0, " %",
     "Staggers the end laps: every other column of sheets starts with a shorter sheet, so its laps fall "
     "this far up a sheet length from the ones beside it, like brickwork. 50 = half a sheet. 0 = the laps in "
     "line (as usual on roofs). Needs a sheet length (G)."),
    ('gap', "H   Joint line (3D print)", 0.2, 100.0, 2, " mm",
     "3D print: the fine line between sheets side by side. Never 0, so no faces touch."),
    ('step', "I   End lap step (3D print)", 0.0, 200.0, 1, " mm",
     "3D print: each sheet stands out this much more at its foot than its head, so the end laps show "
     "as a small step."),
    ('lap', "J   End lap (real sheets)", 0.0, 1000.0, 0, " mm",
     "Real sheets: how far each sheet laps down over the one below. They also lap one corrugation at "
     "the sides."),
    ('backing', "Backing sheet thickness", 0.0, 500.0, 1, " mm",
     "A solid sheet under it all, the shape of the face, so it prints as one piece. 0 = none."),
    ('lift', "Gap off the face", 0.0, 5.0, 3, " mm",
     "A hair's gap between the sheets and the face, so the slicer doesn't see faces lying exactly on "
     "top of each other. 0.01 mm is plenty."),
]
WFIELDS = [
    ('missing', "Missing sheets", 0.0, 90.0, 1, " %",
     "Leave out this share of sheets for a run-down look (turn the rails on to see them behind)."),
    ('rot_h', "Rusted bottom edge (how far up)", 0.0, 3000.0, 0, " mm",
     "The bottoms of the sheets rusted away into a ragged edge, up to this high. 0 = none."),
    ('holes', "Rust holes (per square metre)", 0.0, 50.0, 1, "", "Ragged holes rusted through. 0 = none."),
    ('hole_size', "Hole size", 5.0, 2000.0, 0, " mm", "About how big the rust holes are."),
    ('skew_pct', "Skew sheets (off one nail)", 0.0, 60.0, 1, " %",
     "This share of sheets hang skew from a nail at the top. The sheets beside them are cut back clear."),
    ('skew_ang', "Skew angle (up to)", 0.0, 45.0, 1, " deg", "How far the skew sheets hang over."),
    ('lifted_pct', "Lifted sheets", 0.0, 90.0, 1, " %", "This share of sheets lift away at the foot."),
    ('lifted_mm', "Lifted by (up to)", 0.0, 500.0, 0, " mm", "How far a lifted sheet stands off at its foot."),
]
TFIELDS = [
    ('rail_w', "Rail width", 5.0, 1000.0, 0, " mm", "The rails (purlins) across the back of the sheets."),
    ('rail_t', "Rail thickness", 1.0, 500.0, 0, " mm", "How far the rails stand out."),
    ('rail_gap', "Rails about every", 100.0, 10000.0, 0, " mm", "How far apart the rails are."),
    ('hole_gap', "Gap round openings", 0.0, 200.0, 1, " mm",
     "How far the sheets stop short of a window or door, so they don't touch its frame."),
    ('trim_w', "Flashing width", 5.0, 1000.0, 1, " mm", "The flashing round each opening."),
    ('trim_t', "Flashing / trim thickness", 0.5, 200.0, 1, " mm", "Flashings and corner trims."),
    ('corner_w', "Corner trim width", 5.0, 1000.0, 1, " mm", "Upright trims at each end of the face."),
]


class SheetDialog(QDialog):
    def __init__(self, cur, viewport, tool):
        super().__init__(viewport)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.user_presets = load_presets()
        self._busy = False
        lay = QVBoxLayout(self)
        self.lbl = QLabel("Select a face (a wall or a roof slope), then click 'Clad selected face(s)'. "
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
        self.preview = SheetPreview()
        from PySide6.QtWidgets import QTabWidget
        self.sizes = SheetSizes()
        self.views = QTabWidget()
        self.views.addTab(self.preview, "3D view")
        self.views.addTab(self.sizes, "Sizes (A, B, C ...)")
        self.views.setTabToolTip(0, "A close-up of the sheets you'll get.")
        self.views.setTabToolTip(1, "The front of the sheets, a cut across the corrugations and a cut up "
                                    "through an end lap, showing what each lettered size is.")
        row.addWidget(self.views, 1)
        self.tabs = QTabWidget()
        row.addWidget(self.tabs, 1)
        self.sp = {}

        page1 = QWidget()
        form = QFormLayout(page1)
        self.tabs.addTab(page1, "Sheets")
        self.cb_style = QComboBox()
        for k, lab in PROFILES:
            self.cb_style.addItem(lab, k)
        self.cb_style.setToolTip("The sheet: round corrugated iron, box (trapezoidal) profile, or plain flat sheet.")
        form.addRow("Profile", self.cb_style)
        self.cb_mode = QComboBox()
        for k, lab in MODES:
            self.cb_mode.addItem(lab, k)
        self.cb_mode.setToolTip("3D print: a flat back with the corrugations on the front, so it prints lying "
                                "flat. Real sheets: thin sheets lapping over each other, for full size or big "
                                "scales.")
        form.addRow("Make", self.cb_mode)
        self.cb_thin = QCheckBox("Thin sheet (no flat back) - resin")
        self.cb_thin.setToolTip("3D print: instead of a flat back, the back follows the corrugations, so each "
                                "sheet is a thin tin sheet of thickness E all over - see-through where it's "
                                "rusted or missing. Best with no backing (0), for resin printing.")
        form.addRow(self.cb_thin)
        self.cb_dir = QComboBox()
        for lab, a in DIRECTIONS:
            self.cb_dir.addItem(lab, a)
        self.cb_dir.setToolTip("Which way the corrugations run: up the face (and down a roof), or across it.")
        form.addRow("Corrugations run", self.cb_dir)
        self._fields(form, FIELDS)
        self.cb_flip = QCheckBox("Sheets on the other side of the face")
        self.cb_flip.setToolTip("Puts the sheets on the back of the face instead of the front.")
        form.addRow(self.cb_flip)
        self.cb_remove = QCheckBox("Delete the face the sheets are on")
        self.cb_remove.setToolTip("Takes the face away once it's clad, leaving just the sheets - for a "
                                  "see-through derelict shed (set the backing to 0). Don't use it on the face "
                                  "of a solid wall. Undo puts it back.")
        form.addRow(self.cb_remove)

        page2 = QWidget()
        wf = QFormLayout(page2)
        self.tabs.addTab(page2, "Weathering")
        self.tabs.setTabToolTip(1, "Make it old: rust holes, a rusted bottom, missing, skew and lifted sheets.")
        self._fields(wf, WFIELDS)
        self.sp_seed = QSpinBox()
        self.sp_seed.setRange(1, 9999)
        self.sp_seed.setToolTip("Change this for a different random pattern.")
        wf.addRow("Random pattern", self.sp_seed)

        page3 = QWidget()
        tf = QFormLayout(page3)
        self.tabs.addTab(page3, "Rails, trims")
        self.tabs.setTabToolTip(2, "The rails behind the sheets, flashings round openings and corner trims.")
        self.cb_rails = QCheckBox("Rails (purlins) behind the sheets")
        self.cb_rails.setToolTip("Rails across the back of the sheets. 3D print: they lie on the bed and show "
                                 "where sheets are missing or rusted through. Real sheets: the sheets stand on them.")
        tf.addRow(self.cb_rails)
        self.cb_trims = QCheckBox("Flashings round windows and doors")
        self.cb_trims.setToolTip("A flat flashing framing each opening.")
        tf.addRow(self.cb_trims)
        self.cb_corners = QCheckBox("Corner trims at both ends of the face")
        self.cb_corners.setToolTip("An upright trim at each end of the face, over the sheet edges.")
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
        self.b_add = QPushButton("Clad selected face(s)")
        self.b_add.setToolTip("Covers each face you have selected in sheets.")
        self.b_add.setDefault(True)
        b_close = QPushButton("Close")
        brow.addWidget(self.b_add)
        brow.addStretch(1)
        brow.addWidget(b_close)
        lay.addLayout(brow)

        for w in (self.cb_style, self.cb_dir, self.cb_mode):
            w.currentIndexChanged.connect(self.changed)
        for w in (self.cb_thin, self.cb_flip, self.cb_trims, self.cb_corners, self.cb_remove, self.cb_rails):
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
        v = dict(profile=self.cb_style.currentData() or 'corrugated', thin=self.cb_thin.isChecked(),
                 mode=self.cb_mode.currentData() or 'print',
                 angle=float(self.cb_dir.currentData() or 0.0),
                 flip=self.cb_flip.isChecked(), trims=self.cb_trims.isChecked(),
                 corners=self.cb_corners.isChecked(), rails=self.cb_rails.isChecked(),
                 seed=int(self.sp_seed.value()), remove_face=self.cb_remove.isChecked())
        for key, (s, _) in self.sp.items():
            v[key] = float(s.value())
        return v

    def set_values(self, d):
        self._busy = True
        try:
            for cb, key in ((self.cb_style, 'profile'), (self.cb_mode, 'mode'), (self.cb_dir, 'angle')):
                if d.get(key) is not None:
                    for i in range(cb.count()):
                        if cb.itemData(i) == d[key]:
                            cb.setCurrentIndex(i)
            for cbx, key in ((self.cb_thin, 'thin'), (self.cb_flip, 'flip'), (self.cb_trims, 'trims'), (self.cb_corners, 'corners'),
                             (self.cb_remove, 'remove_face'), (self.cb_rails, 'rails')):
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
        pr, real = v['profile'], v['mode'] == 'real'
        on = {'pitch': pr != 'flat', 'depth': pr != 'flat', 'rib_top': pr == 'box', 'rib_base': pr == 'box',
              'gap': not real, 'step': not real, 'lap': real,
              'stagger': v['sheet_l'] > 0,
              'rail_w': v['rails'], 'rail_t': v['rails'], 'rail_gap': v['rails'],
              'trim_w': v['trims'], 'trim_t': v['trims'] or v['corners'], 'corner_w': v['corners'],
              'skew_ang': v['skew_pct'] > 0, 'lifted_mm': v['lifted_pct'] > 0,
              'hole_size': v['holes'] > 0}
        for key, ok in on.items():
            s, lab = self.sp[key]
            s.setEnabled(ok)
            lab.setEnabled(ok)
        self.cb_thin.setEnabled(not real)
        self.preview.show_sheets(v)
        self.sizes.show_sizes(v)

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
class CorrugatedIronTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+I"
    description = "Covers a face with corrugated iron, box-profile or flat sheets - flat-backed for " \
                  "printing or real lapped sheets - with rust, missing and skew sheets, round any openings."

    _dialog = None
    _saved = None

    def on_activate(self, viewport):
        dlg = CorrugatedIronTool._dialog
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
        if CorrugatedIronTool._saved:
            cur.update(CorrugatedIronTool._saved)
        dlg = SheetDialog(cur, viewport, self)
        CorrugatedIronTool._dialog = dlg

        def closed(*_):
            CorrugatedIronTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass

    def add_from_dialog(self, dlg):
        v = dlg.values()
        CorrugatedIronTool._saved = dict(v)
        viewport = dlg.viewport
        scene = getattr(viewport, 'scene', None)
        faces = selected_faces(scene) if scene is not None else []
        if not faces:
            QMessageBox.information(dlg, PLUGIN_NAME, "Select a face first.")
            return
        parts, total, problems = [], 0, []
        style = PROFILE_NAMES.get(v['profile'], "Sheets").split(" (")[0]
        many = len(faces) > 1
        for i, f in enumerate(faces):
            try:
                tw, outline, holes, _up = face_frame(f, v['flip'], 0)
                if outline is None:
                    raise ValueError("that face has no area")
                res, count = lay_sheets(outline, holes, v)
            except Exception as e:
                problems.append("Face %d: %s" % (i + 1, e))
                continue
            pre = ("Face %d - " % (i + 1)) if many else ""
            for kind, label in (('sheets', "Sheets - %s - %d sheets" % (style, count)),
                                ('rails', "Rails"), ('trims', "Flashings and trims"), ('backing', "Backing")):
                if res[kind]:
                    parts.append((pre + label, [s.mapped(tw) for s in res[kind]]))
            total += count
        if not parts:
            QMessageBox.warning(dlg, PLUGIN_NAME, "\n".join(problems) or "No sheets fitted on that face.")
            return
        top = "Sheeting - %s" % style
        done = [f for i, f in enumerate(faces) if not any(p.startswith("Face %d:" % (i + 1)) for p in problems)]
        remove = done if v.get('remove_face') else []
        nf = self.add_to_scene(viewport, parts, top, remove)
        if nf is None:
            return
        msg = "Added %d sheets on %d face(s), %d faces." % (total, len(faces) - len(problems), nf)
        if remove:
            msg += " Deleted the face%s under them." % ("s" if len(remove) > 1 else "")
        if len(parts) > 1:
            msg += "\nOne group '%s' holding: %s." % (top, ", ".join(n.split(" - ")[0] if not many else
                                                                     " - ".join(n.split(" - ")[:2])
                                                                     for n, _ in parts))
        if problems:
            msg += "\n" + "\n".join(problems)
        dlg.show_report(msg, bad=bool(problems))

    def add_to_scene(self, viewport, parts, top_name="Sheeting", remove=()):
        """One parent group holding a child group per part (each slope, the ridge, the
        finials). The geometry is already in place, so no transforms are needed."""
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
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not add the sheets:\n%s" % e)
            return None
        try:
            viewport.notify_scene_changed()
        except Exception:
            pass
        return stats['faces']


def run(viewport=None):
    CorrugatedIronTool().on_activate(viewport)
