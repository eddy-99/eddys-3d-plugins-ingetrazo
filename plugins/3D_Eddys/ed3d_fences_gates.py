# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Fences & Gates for IngeTrazo
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
3D Fences & Gates - fences, railings and gates for IngeTrazo
Select what the fence follows:
  * an upright face (a rectangle drawn standing up): the fence fills it, along its
    bottom edge and as high as the face;
  * a flat face on the ground (a yard, a plot): the fence runs round its edges;
  * or edges: a fence along each one.
Posts are spaced out evenly, so there's never an odd short panel at the end.

Picket, close-boarded, panel (level boards), post and rail, post and wire, steel
palisade and iron railings on a dwarf wall. Gates: matching the fence, or a five-bar
field gate, single or double. Weathering: missing, broken, skew and rotted pales and
jagged holes - from tidy to derelict.

Sizes are real-world millimetres (IngeTrazo stores metres). Ctrl+Alt+F.
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

PLUGIN_NAME = "3D Fences & Gates"
VERSION = "1"
SCALE = 0.001
PRESET_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Fences")
Z = (0.0, 0.0, 1.0)

TYPES = [
    ("picket", "Picket (pales on two rails)"),
    ("close", "Close-boarded"),
    ("panel", "Panel (level boards)"),
    ("post_rail", "Post and rail"),
    ("wire", "Post and wire"),
    ("palisade", "Steel palisade"),
    ("railings", "Iron railings on a dwarf wall"),
]
TYPE_NAMES = dict(TYPES)
PALE_TOPS = [("pointed", "Pointed"), ("round", "Rounded"), ("gothic", "Gothic (pointed arch)"),
             ("flat", "Flat")]
POST_TOPS = [("flat", "Flat"), ("pointed", "Pointed (weathered)"), ("ball", "Ball")]
GATES = [("none", "No gate"), ("match", "Gate to match the fence"), ("field", "Five-bar field gate")]
EDGES = [("all", "All the edges"), ("open", "All but the last edge (left open)"),
         ("longest", "The longest edge only")]

DEFAULTS = dict(
    type='picket', height=1000.0, bay=1800.0, post_w=100.0, post_top='flat', post_above=50.0,
    rails=2, rail_h=75.0, rail_t=38.0, clear=50.0,
    pale_w=75.0, pale_gap=50.0, pale_t=20.0, pale_top='pointed', board_w=125.0, board_gap=6.0, gravel_h=150.0,
    wire_d=6.0, bar_w=20.0, bar_gap=110.0, wall_h=450.0, wall_t=225.0, coping_h=75.0, coping_over=40.0,
    gate='none', gate_edge=1, gate_pos=50.0, gate_w=1000.0, gate_h=0.0, gate_post=150.0, gate_stile=90.0,
    gate_clear=60.0, gate_double=False, gate_open=0.0,
    missing=0.0, broken=0.0, skew_pct=0.0, skew_ang=8.0, rot_h=0.0, holes=0.0, hole_size=120.0,
    height_var=0.0, seed=1,
    edges='all', use_face_h=True, flip=False, flat=True, lift=0.01, remove_face=True)

# ready-made settings for printing at 1:80 with a 0.4 mm nozzle (real-world mm: / 80 = model)
BUILTIN_PRESETS = {
    "Garden picket fence": dict(type='picket', height=1000.0, pale_top='pointed', post_top='pointed',
                                gate='match'),
    "Close-boarded garden fence": dict(type='close', height=1800.0, post_top='pointed', bay=1830.0, rails=3,
                                       gate='match', gate_h=1800.0),
    "Railway lineside post and wire": dict(type='wire', height=1100.0, rails=4, bay=2700.0, post_w=125.0,
                                           post_top='pointed', gate='field', gate_w=3000.0, gate_post=200.0,
                                           gate_h=1200.0),
    "Occupation crossing, post and rail": dict(type='post_rail', height=1200.0, rails=3, bay=2400.0,
                                               gate='field', gate_w=3600.0, gate_post=200.0, gate_double=True),
    "Station railings on a dwarf wall": dict(type='railings', height=1100.0, bay=2400.0, post_w=60.0,
                                             rail_h=40.0, rail_t=20.0, gate='match', gate_w=1200.0,
                                             gate_post=90.0, gate_double=True),
    "Steel palisade (goods yard)": dict(type='palisade', height=2400.0, pale_w=70.0, pale_gap=55.0, bay=2750.0,
                                        post_w=100.0, rail_h=50.0, pale_t=8.0, gate='match', gate_w=3000.0,
                                        gate_double=True),
    "Derelict picket fence": dict(type='picket', height=1000.0, pale_top='pointed', missing=12.0, broken=15.0,
                                  skew_pct=15.0, skew_ang=10.0, rot_h=120.0, height_var=40.0, seed=5),
    "Derelict close-boarded": dict(type='close', height=1800.0, rails=3, missing=6.0, broken=10.0,
                                   skew_pct=10.0, skew_ang=8.0, rot_h=250.0, holes=1.0, hole_size=160.0,
                                   height_var=30.0, seed=9),
    "1:80 print - close-boarded": dict(type='close', height=1800.0, rails=3, board_w=125.0, board_gap=24.0,
                                       pale_t=24.0, rail_h=64.0, rail_t=32.0, post_w=96.0, post_top='pointed',
                                       gate='match', gate_h=1800.0),
    "1:80 print - picket fence": dict(type='picket', height=1000.0, pale_w=64.0, pale_gap=48.0, pale_t=24.0,
                                      rail_h=64.0, rail_t=32.0, post_w=96.0, post_top='pointed', gate='match'),
    "1:80 print - post and wire": dict(type='wire', height=1100.0, rails=4, wire_d=32.0, post_w=96.0,
                                       bay=2700.0, post_top='pointed', gate='field', gate_w=3000.0,
                                       gate_post=160.0, gate_stile=96.0, rail_h=64.0, rail_t=32.0),
}

# ---------------------------------------------------------------------------
# Small geometry helpers (shared with 3D Wood Planking)
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


def _inside(p, conv):
    """Is point p inside the convex counter-clockwise polygon conv?"""
    n = len(conv)
    for i in range(n):
        (ax, ay), (bx, by) = conv[i], conv[(i + 1) % n]
        if (bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax) < 0:
            return False
    return True




# ---------------------------------------------------------------------------
# Building blocks, in a run's own frame (mm): u along the fence, v up, w out (front)
# ---------------------------------------------------------------------------
def slabw(polys, w0, w1, kind="part"):
    """Pieces of a shape in the (u, v) plane, made thick from w0 to w1 (one solid)."""
    polys = [p for p in (clean(q) for q in polys if q) if p]
    if not polys or w1 - w0 < 1e-6:
        return None
    so = merged_slab(polys, lambda x, y: w0, lambda x, y: w1)
    if so is not None:
        so.kind = kind
    return so


def rect(u0, u1, v0, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def arc(cx, cy, r, a0, a1, n):
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def pale_shape(top, u0, u1, v0, v1):
    """The outline of one pale (or bar) from v0 to its top v1, as convex pieces that
    share whole edges."""
    w = u1 - u0
    uc = (u0 + u1) / 2.0
    if top == 'pointed':
        h = min(0.6 * w, 0.4 * (v1 - v0))
        return [[(u0, v0), (u1, v0), (u1, v1 - h), (uc, v1), (u0, v1 - h)]]
    if top == 'round':
        r = w / 2.0
        if v1 - r <= v0:
            return [rect(u0, u1, v0, v1)]
        return [[(u0, v0), (u1, v0)] + arc(uc, v1 - r, r, 0.0, math.pi, 10)]
    if top == 'gothic':
        h = min(0.9 * w, 0.4 * (v1 - v0))
        pts = [(u0, v0), (u1, v0), (u1, v1 - h)] + \
              [(u1 - (w / 2) * (t * t), v1 - h + h * t) for t in (0.25, 0.5, 0.75)] + [(uc, v1)] + \
              [(u0 + (w / 2) * (t * t), v1 - h + h * t) for t in (0.75, 0.5, 0.25)] + [(u0, v1 - h)]
        return [pts]
    if top == 'triple':
        # steel palisade: three points across the pale
        h = min(0.5 * w, 0.3 * (v1 - v0))
        base = v1 - h
        out = [rect(u0, u1, v0, base)]
        for k in range(3):
            a, b = u0 + w * k / 3.0, u0 + w * (k + 1) / 3.0
            tip = v1 if k == 1 else v1 - 0.15 * h
            out.append([(a, base), (b, base), ((a + b) / 2.0, tip)])
        return out
    if top == 'spear':
        sw = w * 2.2
        sh = max(w * 2.0, 1.0)
        if v1 - sh <= v0:
            return [rect(u0, u1, v0, v1)]
        head = [(u0, v1 - sh), (u1, v1 - sh), (uc + sw / 2, v1 - 0.55 * sh), (uc, v1), (uc - sw / 2, v1 - 0.55 * sh)]
        return [rect(u0, u1, v0, v1 - sh), head]
    return [rect(u0, u1, v0, v1)]


def jag_line(rnd, u0, u1, step, depth, below, vline):
    """Convex bits cutting away everything below (or above) a ragged line near vline."""
    out = []
    n = max(1, int(math.ceil((u1 - u0) / step)))
    hs = []
    for k in range(n + 1):
        h = depth * rnd.random() ** 1.4
        if rnd.random() < 0.15:
            h = depth * rnd.uniform(0.7, 1.0)
        hs.append(h)
    for k in range(n):
        a, b = u0 + (u1 - u0) * k / n, u0 + (u1 - u0) * (k + 1) / n
        if below:
            out.append([(a, vline - 1e5), (b, vline - 1e5), (b, vline + hs[k + 1]), (a, vline + hs[k])])
        else:
            out.append([(a, vline - hs[k]), (b, vline - hs[k + 1]), (b, vline + 1e5), (a, vline + 1e5)])
    return out


def jagged_hole(rnd, cx, cy, size):
    r = size / 2.0 * rnd.uniform(0.6, 1.3)
    k = rnd.randint(7, 11)
    a0 = rnd.uniform(0, math.pi)
    star = []
    for j in range(2 * k):
        rr = r * (rnd.uniform(0.8, 1.15) if j % 2 == 0 else rnd.uniform(0.4, 0.7))
        an = a0 + math.pi * j / k
        star.append((cx + rr * math.cos(an) * 0.75, cy + rr * math.sin(an) * 1.25))
    return convex_parts(star)


def turn_about(p, c, ang):
    x, y = rot((p[0] - c[0], p[1] - c[1]), ang)
    return (x + c[0], y + c[1])


# ---------------------------------------------------------------------------
# One run of fence
# ---------------------------------------------------------------------------
STEEL = ('palisade', 'railings', 'wire')


def post_solids(top, uc, pw, v0, H, w0, w1, flat=False):
    """A post from v0 up to H (and its top: flat, pointed or a ball)."""
    out = []
    if top == 'pointed':
        out.append(slabw([[(uc - pw / 2, v0), (uc + pw / 2, v0), (uc + pw / 2, H), (uc, H + pw * 0.5),
                           (uc - pw / 2, H)]], w0, w1, "post"))
    else:
        out.append(slabw([rect(uc - pw / 2, uc + pw / 2, v0, H)], w0, w1, "post"))
    if top == 'ball':
        r = pw * 0.62
        ball = arc(uc, H + r * 0.85, r, -math.pi / 2, 1.5 * math.pi, 16)[:-1]
        if flat:          # flat back: the ball's back lies on the back of the post too
            out.append(slabw([ball], w0, w0 + (w1 - w0) * 0.8, "post ball"))
        else:
            out.append(slabw([ball], w0 * 0.8, w1 * 0.8, "post ball"))
    return out


def build_run(L, v, rnd, gate=None, posts_at=(True, True), skip_post=None):
    """All solids of one straight run of fence, L mm long, in its own frame.
    gate = (centre u, width) or None. posts_at = posts at the start / end.
    skip_post(u) -> True to leave a post out (one already stands there).
    Returns {'posts', 'rails', 'pales', 'gate', 'wall'} lists and a count of pales."""
    out = {'posts': [], 'rails': [], 'pales': [], 'gate': [], 'wall': []}
    kind = v['type']
    H = max(100.0, v['height'])
    pt = max(10.0, v['post_w'])
    ov = min(2.0, pt * 0.05)
    flat = v.get('flat', True)
    wback = -pt / 2.0
    rt = min(max(5.0, v['rail_t']), pt)
    rh = max(5.0, v['rail_h'])
    # railings stand on a dwarf wall
    base = 0.0
    if kind == 'railings' and v['wall_h'] > 0:
        wt = max(pt + 20.0, v['wall_t'])
        ch = max(0.0, v['coping_h'])
        co = max(0.0, v['coping_over'])
        wall = slabw([rect(-pt / 2 if posts_at[0] else 0.0, L + (pt / 2 if posts_at[1] else 0.0),
                           0.0, v['wall_h'])], (wback if flat else -wt / 2), (wback + wt if flat else wt / 2),
                     "dwarf wall")
        out['wall'].append(wall)
        if ch > 0:
            cop = slabw([rect(-pt / 2 - co if posts_at[0] else 0.0, L + (pt / 2 + co if posts_at[1] else 0.0),
                              v['wall_h'] - ov, v['wall_h'] + ch)],
                        (wback if flat else -wt / 2 - co), (wback + wt + co if flat else wt / 2 + co), "coping")
            out['wall'].append(cop)
        base = v['wall_h'] + ch
    top_v = base + H
    # where the posts go: evenly spaced, never an odd short bay
    segs = []
    if gate is not None:
        gc, gw = gate
        gp = max(pt, v['gate_post'])
        a = gc - gw / 2 - gp / 2
        b = gc + gw / 2 + gp / 2
        if a > pt and b < L - pt:
            segs = [(0.0, a), (b, L)]
        else:
            gate = None
    if gate is None:
        segs = [(0.0, L)]
    posts = []
    bay = max(200.0, v['bay'])
    for si, (s0, s1) in enumerate(segs):
        n = max(1, int(math.ceil((s1 - s0) / bay - 1e-6)))
        for k in range(n + 1):
            u = s0 + (s1 - s0) * k / n
            is_gate_post = gate is not None and ((si == 0 and k == n) or (si == 1 and k == 0))
            if (u < 1e-6 and not posts_at[0]) or (u > L - 1e-6 and not posts_at[1]):
                posts.append((u, False, is_gate_post))
                continue
            posts.append((u, True, is_gate_post))
    count = 0
    pale_t = max(1.0, v['pale_t'])
    # posts
    for u, made, gpost in posts:
        if not made or (skip_post is not None and skip_post(u)):
            continue
        w_ = max(pt, v['gate_post']) if gpost else pt
        ptop = 'ball' if (kind == 'railings') else v['post_top']
        hpost = top_v + (v['post_above'] if kind != 'railings' else 0.0)
        # with a flat back every post (a heavier gate post too) has its back on the back plane
        pw0 = wback if flat else -w_ / 2
        out['posts'] += post_solids(ptop, u, w_, (base - ov) if base > 0 else 0.0, hpost, pw0, pw0 + w_, flat)
    # the bays between posts
    plist = [(u, gp) for u, _, gp in posts]
    for (ua, ga), (ub, gb_) in zip(plist[:-1], plist[1:]):
        if gate is not None and ga and gb_:
            continue                                  # the gateway
        wa = (max(pt, v['gate_post']) if ga else pt) / 2.0
        wb = (max(pt, v['gate_post']) if gb_ else pt) / 2.0
        count += build_bay(out, kind, ua, ub, wa, wb, base, top_v, v, rnd, ov, wback, flat)
    if gate is not None:
        gc, gw = gate
        build_gate(out, kind, gc - gw / 2, gc + gw / 2, base, top_v, v, ov, wback, flat)
    for k in out:
        out[k] = [s for s in out[k] if s]
    return out, count


def build_bay(out, kind, ua, ub, wa, wb, base, top_v, v, rnd, ov, wback, flat):
    """Rails and pales (or boards, bars, wires) between two posts."""
    pt = max(10.0, v['post_w'])
    rt = min(max(5.0, v['rail_t']), pt)
    rh = max(5.0, v['rail_h'])
    H = top_v - base
    a, b = ua + wa, ub - wb                      # the faces of the posts
    if b - a < 5.0:
        return 0
    ra, rb = ua, ub                               # rails run into the posts (to their middles)
    pale_t = max(1.0, v['pale_t'])
    w_rail = (wback if flat else -rt / 2, rt / 2)
    w_pale = (wback if flat else rt / 2 - ov, rt / 2 + pale_t)
    count = 0
    nr = max(1, int(v['rails']))
    clear = max(0.0, v['clear'])

    def rails_at(fracs, layer=w_rail, h=rh):
        for f in fracs:
            vc = base + clear + (H - clear) * f
            out['rails'].append(slabw([rect(ra, rb, vc - h / 2, vc + h / 2)], layer[0], layer[1], "rail"))

    if kind == 'wire':
        wd = max(1.0, v['wire_d'])
        for k in range(nr):
            vc = base + clear + (H - clear - wd) * (k + 1) / nr
            out['rails'].append(slabw([rect(ra, rb, vc - wd / 2, vc + wd / 2)],
                                      wback if flat else -wd / 2, wd / 2, "wire"))
        return 0
    if kind == 'post_rail':
        for k in range(nr):
            vc = base + H * (k + 1) / (nr + 0.4)
            out['rails'].append(slabw([rect(ra, rb, vc - rh / 2, vc + rh / 2)], w_rail[0], w_rail[1], "rail"))
        return 0
    # pales, boards or bars
    if kind == 'railings':
        bw = max(2.0, v['bar_w'])
        gap = max(5.0, v['bar_gap'])
        top_rail_v = top_v - max(bw * 2.0, 1.0) - 60.0
        bot_rail_v = base + 100.0
        for vc in (bot_rail_v, top_rail_v):
            out['rails'].append(slabw([rect(ra, rb, vc - rh / 2, vc + rh / 2)], wback if flat else -rt / 2, rt / 2, "rail"))
        n = max(1, int(round((b - a - gap) / (bw + gap))))
        sp = (b - a) / n
        for k in range(n):
            uc = a + sp * (k + 0.5)
            shape = pale_shape('spear', uc - bw / 2, uc + bw / 2, base - ov, top_v)
            out['pales'].append(slabw(shape, wback if flat else -bw / 2, bw / 2, "bar"))
            count += 1
        return count
    if kind == 'close':
        rails_at([0.12, 0.5, 0.88] if nr >= 3 else [0.15, 0.85])
        gb = max(0.0, v['gravel_h'])
        if gb > 0:
            out['pales'].append(slabw([rect(a, b, base, base + gb)], w_pale[0], w_pale[1], "gravel board"))
        v0 = base + gb + (max(0.2, v['board_gap']) if gb > 0 else 0.0)
        pw = max(10.0, v['board_w'])
        g = max(0.2, v['board_gap'])
        n = max(1, int(round((b - a) / pw)))
        pw = (b - a) / n
        slots = [(a + k * pw + (g / 2 if k > 0 else 0.0), a + (k + 1) * pw - (g / 2 if k < n - 1 else 0.0)) for k in range(n)]
        top = 'flat'
    elif kind == 'panel':
        # horizontal boards between the posts, with a capping rail
        g = max(0.2, v['board_gap'])
        bh = max(10.0, v['board_w'])
        n = max(1, int(round(H / bh)))
        bh = H / n
        for k in range(n):
            y0 = base + k * bh + (g / 2 if k > 0 else 0.0)
            y1 = base + (k + 1) * bh - (g / 2 if k < n - 1 else 0.0)
            pcs = cut_away([rect(a - ov, b + ov, y0, y1)], _decay(v, rnd, a, b, base, top_v, boards=True))
            so = slabw(pcs, w_pale[0] if flat else -pale_t / 2, pale_t / 2, "board")
            if so:
                out['pales'].append(so)
                count += 1
        return count
    else:
        # picket or palisade: two (or more) rails and pales in front
        fr = [0.2, 0.78] if nr <= 2 else [0.12 + 0.76 * k / (nr - 1) for k in range(nr)]
        rails_at(fr)
        pw = max(5.0, v['pale_w'])
        g = max(0.2, v['pale_gap'])
        n = max(1, int(round((b - a - g) / (pw + g))))
        sp = (b - a - g) / n
        slots = [(a + g + k * sp, a + g + k * sp + sp - g) for k in range(n)]
        v0 = base + clear
        top = 'triple' if kind == 'palisade' else v['pale_top']
    # pales or upright boards, with weathering
    blockers = _decay(v, rnd, a, b, base, top_v, boards=(kind == 'close'))
    miss = min(90.0, max(0.0, v['missing'])) / 100.0
    brk = min(90.0, max(0.0, v['broken'])) / 100.0
    skp = min(60.0, max(0.0, v['skew_pct'])) / 100.0
    ska = math.radians(min(45.0, max(0.0, v['skew_ang'])))
    hv = max(0.0, v['height_var'])
    items = []
    prev_skew = False
    for (s0, s1) in slots:
        if miss > 0 and rnd.random() < miss:
            prev_skew = False
            continue
        vt = top_v + (rnd.uniform(-hv, hv) if hv > 0 else 0.0)
        shape = pale_shape(top, s0, s1, v0, vt)
        own = []
        if brk > 0 and rnd.random() < brk:
            vb = v0 + (vt - v0) * rnd.uniform(0.45, 0.85)
            own = jag_line(rnd, s0 - 1, s1 + 1, max(4.0, (s1 - s0) / 3.0), (s1 - s0) * 0.9, False, vb)
        sk = 0.0
        if skp > 0 and ska > 0 and not prev_skew and rnd.random() < skp:
            sk = rnd.choice((-1.0, 1.0)) * ska * rnd.uniform(0.4, 1.0)
        prev_skew = bool(sk)
        items.append({'shape': shape, 'own': own, 'sk': sk, 'slot': (s0, s1), 'vt': vt})
    # skewed pales hang from the top rail; the ones beside them are cut back clear
    pivot_v = base + clear + (H - clear) * 0.78
    for it in items:
        if it['sk']:
            c = ((it['slot'][0] + it['slot'][1]) / 2.0, min(pivot_v, it['vt'] - 30.0))
            it['shape'] = [[turn_about(q, c, it['sk']) for q in pc] for pc in it['shape']]
            it['own'] = [[turn_about(q, c, it['sk']) for q in pc] for pc in it['own']]
            pts = [q for pc in it['shape'] for q in pc]
            it['foot'] = convex_hull(pts)
    bay_box = rect(a, b, base - 1.0, top_v + 1e4)
    for it in items:
        others = [grow(o['foot'], max(0.2, g * 0.5)) for o in items if o is not it and o.get('foot')]
        pcs = []
        for pc in it['shape']:
            q = clip_convex(pc, bay_box) if it['sk'] else clean(pc)
            if q:
                pcs.append(q)
        pcs = cut_away(pcs, blockers + it['own'] + [o for o in others if o])
        pcs = [p for p in pcs if abs(area2(p)) > 1e-3]
        so = slabw(pcs, w_pale[0], w_pale[1], "pale" if kind != 'close' else "board")
        if so:
            out['pales'].append(so)
            count += 1
    return count


def _decay(v, rnd, a, b, base, top_v, boards):
    """Rot along the bottom and jagged holes, as convex bits to cut away."""
    out = []
    rh_ = max(0.0, v['rot_h'])
    if rh_ > 0:
        out += jag_line(rnd, a - 5, b + 5, max(4.0, min(40.0, rh_ / 2.0)), rh_, True, base)
    nh = max(0.0, v['holes']) * (b - a) * (top_v - base) / 1e6 if boards else 0.0
    want = int(nh) + (1 if rnd.random() < nh - int(nh) else 0)
    for _ in range(want):
        cx, cy = rnd.uniform(a + 20, b - 20), rnd.uniform(base + 0.1 * (top_v - base), top_v - 0.1 * (top_v - base))
        out += jagged_hole(rnd, cx, cy, max(5.0, v['hole_size']))
    return out


def build_gate(out, kind, ga, gb, base, top_v, v, ov, wback, flat):
    """A gate (or pair of gates) filling the gateway between the gate posts' faces."""
    gp = max(v['post_w'], v['gate_post'])
    a, b = ga + 12.0, gb - 12.0                   # hinge and latch clearance
    if b - a < 100:
        return
    gtype = v['gate']
    hg = max(300.0, v['gate_h'] if v['gate_h'] > 0 else top_v - base)
    v0 = base + max(0.0, v['gate_clear'])
    v1 = base + hg
    leaves = [(a, b)] if not v['gate_double'] else [(a, (a + b) / 2 - 6.0), ((a + b) / 2 + 6.0, b)]
    pt = max(10.0, v['post_w'])
    rt = min(max(5.0, v['rail_t']), pt)
    st = max(20.0, v['gate_stile'])
    gt = max(10.0, rt * 1.2)
    ang = math.radians(v['gate_open']) if (v['gate_open'] > 0 and not flat) else 0.0
    for li, (la, lb) in enumerate(leaves):
        hinge_left = (li == 0)
        sols = []
        w0 = wback if flat else -gt / 2
        if gtype == 'field' or kind in ('wire', 'post_rail'):
            # a five-bar field gate: stiles, five bars and a diagonal brace
            sols.append(slabw([rect(la, la + st * 1.3 if hinge_left else la + st, v0, v1)], w0, gt / 2, "gate stile"))
            sols.append(slabw([rect(lb - (st if hinge_left else st * 1.3), lb, v0, v1)], w0, gt / 2, "gate stile"))
            nb = 5
            bh = max(20.0, v['rail_h'] * 0.9)
            for k in range(nb):
                vc = v0 + bh / 2 + (v1 - v0 - bh) * k / (nb - 1)
                hh = bh * (1.6 if k == nb - 1 else 1.0)
                sols.append(slabw([rect(la + st - ov, lb - st + ov, vc - hh / 2, vc + min(hh / 2, v1 - vc))],
                                  w0, gt / 2 - 2.0, "gate bar"))
            sols.append(_brace(la + st, lb - st, v0 + bh, v1 - bh * 1.6, bh, hinge_left, gt / 2 - 2.0 - ov,
                               gt / 2 + rt * 0.6, w0 if flat else None))
        else:
            # the same infill as the fence, on a ledged and braced frame
            lw = max(20.0, v['rail_h'])
            for vc in (v0 + 0.12 * (v1 - v0), v0 + 0.85 * (v1 - v0)):
                sols.append(slabw([rect(la, lb, vc - lw / 2, vc + lw / 2)], w0, rt / 2, "gate ledge"))
            sols.append(_brace(la + 20, lb - 20, v0 + 0.12 * (v1 - v0) + lw / 2, v0 + 0.85 * (v1 - v0) - lw / 2,
                               lw * 0.9, hinge_left, -rt / 2 if not flat else wback, rt / 2, None))
            pale_t = max(1.0, v['pale_t'])
            wp0 = wback if flat else rt / 2 - ov
            if kind == 'railings':
                bw = max(2.0, v['bar_w'])
                gap = max(5.0, v['bar_gap'])
                n = max(1, int(round((lb - la - gap) / (bw + gap))))
                sp = (lb - la) / n
                for k in range(n):
                    uc = la + sp * (k + 0.5)
                    sols.append(slabw(pale_shape('spear', uc - bw / 2, uc + bw / 2, v0, v1),
                                      wback if flat else -bw / 2, bw / 2, "gate bar"))
            elif kind in ('close', 'panel'):
                pw = max(10.0, v['board_w'])
                g = max(0.2, v['board_gap'])
                n = max(1, int(round((lb - la) / pw)))
                pw = (lb - la) / n
                for k in range(n):
                    s0 = la + k * pw + (g / 2 if k > 0 else 0.0)
                    s1 = la + (k + 1) * pw - (g / 2 if k < n - 1 else 0.0)
                    sols.append(slabw([rect(s0, s1, v0, v1)], wp0, rt / 2 + pale_t, "gate board"))
            else:
                pw = max(5.0, v['pale_w'])
                g = max(0.2, v['pale_gap'])
                n = max(1, int(round((lb - la + g) / (pw + g))))
                sp = (lb - la + g) / n
                top = 'triple' if kind == 'palisade' else v['pale_top']
                for k in range(n):
                    s0 = la + k * sp
                    s1 = s0 + sp - g
                    sols.append(slabw(pale_shape(top, s0, s1, v0, v1), wp0, rt / 2 + pale_t, "gate pale"))
        sols = [s for s in sols if s]
        if ang > 0:
            uh = la if hinge_left else lb
            sgn = 1.0 if hinge_left else -1.0
            c, s_ = math.cos(ang * sgn), math.sin(ang * sgn)

            def f(p, uh=uh, c=c, s_=s_):
                du, dw = p[0] - uh, p[2]
                return (uh + du * c - dw * s_, p[1], du * s_ + dw * c)
            sols = [so.mapped(f) for so in sols]
        out['gate'] += sols


def _brace(ua, ub, va, vb, w, hinge_left, z0, z1, zflat):
    """A diagonal brace from low on the hinge side to high on the latch side, clipped
    between va and vb (its ends run under the bars or ledges)."""
    p1 = (ua + w * 0.6, va) if hinge_left else (ub - w * 0.6, va)
    p2 = (ub - w * 0.6, vb) if hinge_left else (ua + w * 0.6, vb)
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    ex, ey = dx / L * w, dy / L * w
    quad = clean([(p1[0] - nx - ex, p1[1] - ny - ey), (p2[0] - nx + ex, p2[1] - ny + ey),
                  (p2[0] + nx + ex, p2[1] + ny + ey), (p1[0] + nx - ex, p1[1] + ny - ey)])
    if not quad:
        return None
    pc = clip_convex(rect(ua, ub, va, vb), quad)
    if not pc:
        return None
    return slabw([pc], zflat if zflat is not None else z0, z1, "brace")


# ---------------------------------------------------------------------------
# Reading the selection
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
    """One undo step that adds the fence groups and removes faces. Snapshots the
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
# What the fence follows
# ---------------------------------------------------------------------------
def selected_edges(scene):
    """Selected edges (anything with exactly two vertices), as pairs of world points."""
    out = []
    for e in _items(getattr(scene, 'selection', None)):
        if getattr(e, 'mesh', None) is not None:
            continue
        vs = None
        for name in ('vertices', 'verts'):
            vs = getattr(e, name, None)
            if vs is not None and not callable(vs):
                break
            vs = None
        if vs is None:
            ab = [getattr(e, n, None) for n in ('v1', 'v2')]
            if all(x is not None for x in ab):
                vs = ab
            else:
                ab = [getattr(e, n, None) for n in ('a', 'b')]
                vs = ab if all(x is not None for x in ab) else None
        pts = [p for p in (_pos(q) for q in _items(vs)) if p is not None] if vs is not None else []
        if len(pts) == 2:
            out.append((pts[0], pts[1]))
    return out


def make_run(p0, p1, up, height=None, posts=(True, True)):
    """A straight run from p0 to p1 (world metres), standing up along `up`."""
    d = v_sub(p1, p0)
    d = v_sub(d, v_mul(up, v_dot(d, up)))
    L = v_len(d)
    if L < 1e-4:
        return None
    U = v_mul(d, 1.0 / L)
    W = v_norm(v_cross(U, up))
    return {'O': p0, 'U': U, 'V': up, 'W': W, 'L': L / SCALE, 'posts': posts, 'height': height}


def runs_from_selection(scene, v):
    """[(label, [runs], face to remove or None)] from the selected faces and edges."""
    out = []
    for i, f in enumerate(selected_faces(scene)):
        pts = [p for p in (_pos(q) for q in _items(f.vertices)) if p is not None]
        if len(pts) < 3:
            continue
        n = _newell(pts)
        if abs(n[2]) < 0.5:
            # an upright face: the fence fills it, along its bottom edge
            tw, outline, _holes, _up = face_frame(f, v['flip'], 0)
            if outline is None:
                continue
            x0, x1, y0, y1 = bbox(outline)
            p0, p1 = tw((x0, y0, 0.0)), tw((x1, y0, 0.0))
            top = tw((x0, y1, 0.0))
            up = v_norm(v_sub(top, p0))
            r = make_run(p0, p1, up, (y1 - y0) if v['use_face_h'] else None)
            if r:
                # out of the face is the front
                nn = v_mul(n, -1.0) if v['flip'] else n
                if v_dot(r['W'], nn) < 0:
                    r = make_run(p1, p0, up, r['height'])
                out.append(("Face %d" % (i + 1), [r], f))
            continue
        # a flat face: the fence runs round its edges (counter-clockwise from above, so
        # the front of the fence faces out)
        if n[2] < 0:
            pts = pts[::-1]
        m = len(pts)
        edges = [(pts[k], pts[(k + 1) % m]) for k in range(m)]
        mode = v['edges']
        if mode == 'longest':
            k = max(range(m), key=lambda k: v_len(v_sub(edges[k][1], edges[k][0])))
            edges = [edges[k]]
            flags = [(True, True)]
        elif mode == 'open':
            edges = edges[:-1]
            flags = [(True, True)] * len(edges)
        else:
            flags = [(True, True)] * len(edges)
        runs = [r for r in (make_run(a, b, Z, None, fl) for (a, b), fl in zip(edges, flags)) if r]
        if v['flip']:
            runs = [make_run(r['O'], v_add(r['O'], v_mul(r['U'], r['L'] * SCALE)), Z, None, r['posts']) for r in runs]
            for r in runs:
                r['W'] = v_mul(r['W'], -1.0)
        if runs:
            out.append(("Face %d" % (i + 1), runs, None))
    es = selected_edges(scene)
    if es:
        runs = [r for r in (make_run(a, b, Z, None) for a, b in es) if r]
        if runs:
            out.append(("Edges", runs, None))
    return out


def build_fence(runs, v):
    """World solids for a list of runs: {'posts', 'rails', 'pales', 'gate', 'wall'}, and
    the number of pales (or boards, bars)."""
    rnd = random.Random(int(v.get('seed', 1)))
    parts = {'posts': [], 'rails': [], 'pales': [], 'gate': [], 'wall': []}
    placed = []                                 # post positions already made (world)
    total = 0
    lift = max(0.0, v.get('lift', 0.0))
    for ri, r in enumerate(runs):
        vv = dict(v)
        if r.get('height'):
            # fence the face's height: the posts reach its top
            above = 0.0 if v['type'] == 'railings' else max(0.0, v['post_above'])
            if v['type'] == 'railings' and v['wall_h'] > 0:
                above += v['wall_h'] + max(0.0, v['coping_h'])
            vv['height'] = max(100.0, r['height'] - above - lift)
        L = r['L']
        gate = None
        if v['gate'] != 'none' and int(v['gate_edge']) == ri + 1:
            gw = max(300.0, v['gate_w'])
            gc = L * min(100.0, max(0.0, v['gate_pos'])) / 100.0
            gp = max(v['post_w'], v['gate_post'])
            lo, hi = gw / 2 + gp + v['post_w'], L - gw / 2 - gp - v['post_w']
            if hi > lo:
                gate = (min(max(gc, lo), hi), gw)
        O, U, V, W = r['O'], r['U'], r['V'], r['W']
        z_up = lift

        def world(p, O=O, U=U, V=V, W=W):
            return v_add(O, v_add(v_mul(U, p[0] * SCALE), v_add(v_mul(V, (p[1] + z_up) * SCALE),
                                                                    v_mul(W, p[2] * SCALE))))

        def skip(u, world=world):
            q = world((u, 0.0, 0.0))
            for p in placed:
                if v_len(v_sub(p, q)) < 0.5 * max(v['post_w'], 10.0) * SCALE:
                    return True
            placed.append(q)
            return False
        res, n = build_run(L, vv, rnd, gate, r['posts'], skip)
        total += n
        for k, sols in res.items():
            parts[k] += [s.mapped(world) for s in sols]
    return parts, total


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------
VIEW_DIR = v_norm((-0.45, -0.18, -1.0))      # from the front, a little from the left and above
LIGHT = v_norm((-0.5, 0.6, 0.6))
COLOURS = {'wood': (150, 104, 64), 'steel': (70, 78, 74), 'iron': (34, 34, 38), 'brick': (168, 80, 58),
           'stone': (205, 198, 182), 'post': (130, 92, 58)}


def part_rgb(v, kind, so):
    k = getattr(so, 'kind', '')
    if k == 'dwarf wall':
        return COLOURS['brick']
    if k == 'coping':
        return COLOURS['stone']
    t = v['type']
    if t == 'railings':
        return COLOURS['iron']
    if t == 'palisade':
        return COLOURS['steel']
    if t == 'wire' and k == 'wire':
        return COLOURS['iron']
    return COLOURS['post'] if kind == 'posts' else COLOURS['wood']


def preview_caption(v):
    t = TYPE_NAMES.get(v['type'], "Fence").split(" (")[0]
    txt = "%s - %.0f high, posts every %.0f" % (t, v['height'], v['bay'])
    if v['gate'] != 'none':
        txt += " - " + ("pair of gates" if v['gate_double'] else "gate")
    return txt


def preview_items(v):
    L = max(3000.0, 2.2 * v['bay'])
    gate = None
    if v['gate'] != 'none':
        L = max(L, v['gate_w'] + 2 * v['bay'] + 2 * v['gate_post'])
        gate = (L / 2, max(300.0, v['gate_w']))
    res, _ = build_run(L, v, random.Random(int(v.get('seed', 1))), gate, (True, True))
    right = v_norm(v_cross(VIEW_DIR, (0.0, 1.0, 0.0)))
    up = v_cross(right, VIEW_DIR)
    items = []
    for kind, sols in res.items():
        for so in sols:
            rgb = part_rgb(v, kind, so)
            hol = getattr(so, 'holes', {})
            for fi, f in enumerate(so.faces):
                n = _newell(f)
                if v_dot(n, VIEW_DIR) >= 0:
                    continue
                k = 0.5 + 0.5 * max(0.0, v_dot(n, LIGHT))
                depth = sum(v_dot(p, VIEW_DIR) for p in f) / len(f)
                items.append((depth, [(v_dot(p, right), -v_dot(p, up)) for p in f],
                              tuple(int(c * k) for c in rgb), True,
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

EDDY_TIPS = {'Fence': 'The kind of fence: picket, close-boarded, panel, post and rail, post and wire, '
          'steel palisade, or iron railings on a dwarf wall.',
 'Post tops': 'How the tops of the posts are finished: flat, pointed (weathered to shed the '
              'rain) or a ball.',
 'Posts stand above the fence': 'How far the posts stick up above the top of the pales or '
                                'boards.',
 'Rails (or wires)': 'How many rails run between the posts (or how many wires, for post and '
                     'wire).',
 'Rail depth': 'The height of each rail, top to bottom.',
 'Rail thickness': 'How thick the rails are, front to back.',
 'Pale width': 'How wide each pale (upright board) is.',
 'Pale / board thickness': 'How thick the pales and boards are. For printing keep it at least '
                           'your nozzle (32 mm = 0.4 mm at 1:80).',
 'Pale tops': 'How the top of each pale is cut: pointed, rounded, gothic (pointed arch) or '
              'flat.',
 'Gate': 'No gate, a gate made to match the fence, or a five-bar field gate.',
 'Gate height (0 = fence height)': 'How tall the gate is. 0 makes it the same height as the '
                                   'fence.',
 'Gate post size': 'The posts each side of the gate (square). Usually heavier than the fence '
                   'posts.',
 'Field gate stiles': 'The width of the upright end pieces (stiles) of a five-bar field gate.',
 'Gap under the gate': 'How far the bottom of the gate stops above the ground.',
 'A pair of gates': 'Two gates meeting in the middle instead of one.',
 'Missing pales / boards': 'The share of pales or boards that have fallen off and are left '
                           'out.',
 'Broken pales (snapped off, jagged)': 'The share of pales that have snapped off part way up, '
                                       'with a jagged top.',
 'Skew angle (up to)': 'The most a skewed (loose) pale leans over.',
 'Hole size': 'About how big the rotted holes are.',
 'Uneven heights (up to)': 'Pales and boards are cut a little shorter at random, by up to this '
                           'much.',
 'Railing bar size': 'The thickness of each iron railing bar (square).',
 'Gap between railing bars': 'The clear space between one railing bar and the next.',
 'Dwarf wall thickness': 'How thick the low wall under the railings is.',
 'Coping height': 'The height of the coping stones on top of the dwarf wall (0 = no coping).',
 'Coping overhang': 'How far the coping sticks out past each face of the wall.',
 'Add fence': 'Builds the fence on the face, edges or ground you have selected.',
 'Weathering': 'Make it old: missing, broken, skewed and rotted pales, and uneven heights.',
 'Wire, railings': 'Sizes for post-and-wire fences, iron railings and their dwarf wall.',
 'Placing': 'Where the fence goes and which side of the line it stands.'}
EDDY_TIPS_END = None


class FencePreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(380, 260)
        self.items = []
        self.msg = ""
        self.caption = ""

    def show_fence(self, v):
        try:
            self.caption = preview_caption(v)
            self.items = preview_items(v)
            self.msg = ""
        except Exception as e:
            self.items, self.msg = [], str(e)
        self.update()

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen, QFont, QPainterPath
        from PySide6.QtCore import QPointF, Qt
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(238, 240, 234))
        if not self.items:
            p.drawText(self.rect(), Qt.AlignCenter | Qt.TextWordWrap, self.msg or "No preview")
            p.end()
            return
        xs = [x for it in self.items for x, _ in it[1]]
        ys = [y for it in self.items for _, y in it[1]]
        w, h = self.width() - 16, self.height() - 16
        h_cap = 18
        sc = min(w / ((max(xs) - min(xs)) or 1), (h - h_cap) / ((max(ys) - min(ys)) or 1))
        ox = 8 + (w - (max(xs) - min(xs)) * sc) / 2 - min(xs) * sc
        oy = 8 + h_cap + (h - h_cap - (max(ys) - min(ys)) * sc) / 2 - min(ys) * sc
        for _, pts, rgb, edge, holes in self.items:
            col = QColor(*rgb)
            p.setBrush(col)
            p.setPen(QPen(col.darker(170), 0.7))
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


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------
CHOICES = {'type': TYPES, 'pale_top': PALE_TOPS, 'post_top': POST_TOPS, 'gate': GATES, 'edges': EDGES}
INT_KEYS = ('rails', 'gate_edge', 'seed')
BOOL_KEYS = ('gate_double', 'use_face_h', 'flip', 'flat', 'remove_face')

# key: (label, low, high, decimals, suffix, tip)   or (label, tip) for choices and ticks
FIELDS = {
    'type': ("Fence", ""),
    'height': ("A   Height", 100.0, 10000.0, 0, " mm", "Height of the pales, boards or railings."),
    'use_face_h': ("Use the face's height (upright faces)", "When you pick an upright face, the fence "
                                                            "is as high as the face (the posts reach "
                                                            "its top). Untick to use A."),
    'bay': ("B   Posts no further apart than", 200.0, 20000.0, 0, " mm",
            "Posts are spaced out evenly along each run, as near this as they can be without going over."),
    'post_w': ("C   Post size", 10.0, 1000.0, 0, " mm", "Posts are square."),
    'post_top': ("Post tops", ""),
    'post_above': ("D   Posts stand above the fence", 0.0, 1000.0, 0, " mm", ""),
    'rails': ("Rails (or wires)", 1, 8, None, "", ""),
    'rail_h': ("E   Rail depth", 5.0, 500.0, 0, " mm", ""),
    'rail_t': ("F   Rail thickness", 5.0, 300.0, 0, " mm", ""),
    'clear': ("Gap under the fence", 0.0, 500.0, 0, " mm", "How far the pales stop above the ground."),
    'pale_w': ("G   Pale width", 5.0, 500.0, 0, " mm", ""),
    'pale_gap': ("H   Gap between pales", 0.2, 1000.0, 1, " mm", "Never 0, so no faces touch."),
    'pale_t': ("J   Pale / board thickness", 1.0, 200.0, 1, " mm", ""),
    'pale_top': ("Pale tops", ""),
    'board_w': ("K   Board width", 10.0, 1000.0, 0, " mm", "Close-boarded and panel fences."),
    'board_gap': ("L   Gap between boards", 0.2, 200.0, 1, " mm", "Close-boarded and panel fences. "
                                                               "Never 0, so no faces touch."),
    'gravel_h': ("Gravel board", 0.0, 1000.0, 0, " mm", "Close-boarded: the board along the bottom "
                                                        "(0 = none)."),
    'wire_d': ("Wire thickness", 1.0, 100.0, 1, " mm", "Post and wire. Real wire is about 4 mm; "
                                                       "for printing use your nozzle (32 = 0.4 mm at 1:80)."),
    'bar_w': ("Railing bar size", 2.0, 200.0, 1, " mm", ""),
    'bar_gap': ("Gap between railing bars", 5.0, 1000.0, 0, " mm", ""),
    'wall_h': ("Dwarf wall height", 0.0, 3000.0, 0, " mm", "Railings stand on it (0 = no wall)."),
    'wall_t': ("Dwarf wall thickness", 50.0, 1000.0, 0, " mm", ""),
    'coping_h': ("Coping height", 0.0, 500.0, 0, " mm", ""),
    'coping_over': ("Coping overhang", 0.0, 300.0, 0, " mm", ""),
    'gate': ("Gate", ""),
    'gate_edge': ("Gate in run (edge) number", 1, 99, None, "", "Which run gets the gate, counting the "
                                                                "edges of the face in order."),
    'gate_pos': ("Gate position along it", 0.0, 100.0, 0, " %", "50 = in the middle."),
    'gate_w': ("Gateway width", 300.0, 20000.0, 0, " mm", "Between the gate posts."),
    'gate_h': ("Gate height (0 = fence height)", 0.0, 5000.0, 0, " mm", ""),
    'gate_post': ("Gate post size", 10.0, 1000.0, 0, " mm", ""),
    'gate_stile': ("Field gate stiles", 20.0, 500.0, 0, " mm", ""),
    'gate_clear': ("Gap under the gate", 0.0, 500.0, 0, " mm", ""),
    'gate_double': ("A pair of gates", ""),
    'gate_open': ("Gate open by", 0.0, 120.0, 0, " deg", "Not when printing flat."),
    'missing': ("Missing pales / boards", 0.0, 90.0, 1, " %", ""),
    'broken': ("Broken pales (snapped off, jagged)", 0.0, 90.0, 1, " %", ""),
    'skew_pct': ("Skew pales (hanging off one nail)", 0.0, 60.0, 1, " %",
                 "The pales beside them are cut back clear, so nothing overlaps."),
    'skew_ang': ("Skew angle (up to)", 0.0, 45.0, 1, " deg", ""),
    'rot_h': ("Rotted bottoms (how far up)", 0.0, 2000.0, 0, " mm", "Ragged, rotted-away bottoms."),
    'holes': ("Jagged holes (per square metre)", 0.0, 50.0, 1, "", "Close-boarded and panel fences."),
    'hole_size': ("Hole size", 5.0, 2000.0, 0, " mm", ""),
    'height_var': ("Uneven heights (up to)", 0.0, 500.0, 0, " mm", ""),
    'seed': ("Random pattern", 1, 9999, None, "", "Change this for a different random pattern."),
    'edges': ("Round a flat face, fence", "Which edges of a flat (ground) face get fenced."),
    'flip': ("Fence faces the other way", "Turns the front of the fence round (for a flat face: "
                                          "fences the inside face of the edges)."),
    'flat': ("Flat back for 3D printing", "Every part goes back to the back of the posts, so the fence "
                                          "prints lying flat. Gates can't be shown open like this."),
    'lift': ("Gap off the ground", 0.0, 5.0, 3, " mm", "A hair's gap under the fence, so the slicer "
                                                       "doesn't see faces lying on top of each other."),
    'remove_face': ("Delete an upright face once fenced", "The face you drew to show where the fence "
                                                          "goes is taken away (undo puts it back). "
                                                          "Flat (ground) faces are always kept."),
}
TABS = [
    ("Fence", ('type', 'height', 'use_face_h', 'bay', 'post_w', 'post_top', 'post_above', 'rails', 'rail_h',
               'rail_t', 'clear', 'pale_w', 'pale_gap', 'pale_t', 'pale_top', 'board_w', 'board_gap', 'gravel_h')),
    ("Gate", ('gate', 'gate_edge', 'gate_pos', 'gate_w', 'gate_h', 'gate_post', 'gate_stile', 'gate_clear',
              'gate_double', 'gate_open')),
    ("Weathering", ('missing', 'broken', 'skew_pct', 'skew_ang', 'rot_h', 'holes', 'hole_size', 'height_var',
                    'seed')),
    ("Wire, railings", ('wire_d', 'bar_w', 'bar_gap', 'wall_h', 'wall_t', 'coping_h', 'coping_over')),
    ("Placing", ('edges', 'flip', 'flat', 'lift', 'remove_face')),
]


# ---------------------------------------------------------------------------
# Sizes: a front view and a cut through the fence, each size marked by its letter
# ---------------------------------------------------------------------------
def fence_sizes_drawing(v):
    """{'front': [(kind, pts, rgb)], 'cut': [(pts, rgb)], 'dims': [(letter, view, p1, p2, out, off)],
    'xc': where the cut is taken} - all in mm."""
    t = v['type']
    POST, RAIL, PALE, WALL = (120, 86, 52), (150, 108, 66), (176, 132, 84), (190, 182, 172)
    if t in ('palisade', 'railings'):
        POST, RAIL, PALE = (70, 74, 80), (90, 94, 100), (110, 114, 120)
    A = max(100.0, v['height'])
    B = max(200.0, v['bay'])
    C = max(10.0, v['post_w'])
    Dab = v['post_above'] if t != 'railings' else 0.0
    E = max(5.0, v['rail_h'])
    F = min(max(5.0, v['rail_t']), C)
    G, Hg = max(5.0, v['pale_w']), max(0.2, v['pale_gap'])
    J = max(1.0, v['pale_t'])
    K, Lg = max(10.0, v['board_w']), max(0.2, v['board_gap'])
    flat = v.get('flat', True)
    clear = max(0.0, v.get('clear', 0.0))
    base = 0.0
    front, cut, dims = [], [], []

    def rect(x0, y0, x1, y1, rgb, view='F'):
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        (front if view == 'F' else cut).append(('poly', pts, rgb) if view == 'F' else (pts, rgb))
    # railings stand on a dwarf wall
    if t == 'railings' and v['wall_h'] > 0:
        wt = max(C + 20.0, v['wall_t'])
        rect(-C, 0, B + C, v['wall_h'], WALL)
        base = v['wall_h'] + max(0.0, v['coping_h'])
        if v['coping_h'] > 0:
            rect(-C - 20, v['wall_h'], B + C + 20, base, (205, 200, 192))
        w0 = -C / 2 if flat else -wt / 2
        rect(w0, 0, w0 + wt, v['wall_h'], WALL, 'C')
        co = v['coping_over']
        rect(w0 if flat else w0 - co, v['wall_h'], w0 + wt + co, base, (205, 200, 192), 'C')
    top = base + A
    # posts: one each end of the bay
    for x in (0.0, B):
        rect(x - C / 2, base, x + C / 2, top + Dab, POST)
    # rails
    rails = []
    n_r = max(1, int(v['rails'])) if t in ('picket', 'palisade', 'close', 'post_rail', 'wire') else 0
    if t == 'railings':
        n_r = 2
    if n_r:
        lo, hi = base + clear + max(E, A * 0.12), top - max(E, A * 0.12)
        for k in range(n_r):
            y = (lo + hi) / 2 if n_r == 1 else lo + (hi - lo) * k / (n_r - 1)
            rails.append(y)
            hh = v['wire_d'] if t == 'wire' else E
            rect(C / 2, y - hh / 2, B - C / 2, y + hh / 2, RAIL)
    # pales, boards or bars across the bay
    xa, xb = C / 2, B - C / 2
    pw, gap = (G, Hg) if t in ('picket', 'palisade') else (K, Lg) if t in ('close', 'panel') else \
        (max(2.0, v['bar_w']), max(5.0, v['bar_gap'])) if t == 'railings' else (0, 0)
    first = None
    if pw:
        x = xa + gap
        while x + pw <= xb - gap * 0.3 + 1e-6:
            pts = [(x, base + clear), (x + pw, base + clear), (x + pw, top), (x, top)]
            if t in ('picket', 'palisade') and v.get('pale_top', 'pointed') != 'flat':
                pts = [(x, base + clear), (x + pw, base + clear), (x + pw, top - pw * 0.5),
                       (x + pw / 2, top), (x, top - pw * 0.5)]
            front.append(('poly', pts, PALE))
            if first is None:
                first = x
            x += pw + gap
    # the cut through, side on: front of the fence to the right
    wb = -C / 2
    rect(wb if flat else -C / 2, base, (wb if flat else -C / 2) + C, top + Dab, POST, 'C')
    w_rail = (wb if flat else -F / 2, F / 2)
    for y in rails:
        hh = v['wire_d'] if t == 'wire' else E
        rect(w_rail[0], y - hh / 2, w_rail[1] if t != 'wire' else w_rail[0] + v['wire_d'], y + hh / 2, RAIL, 'C')
    if pw:
        if t == 'railings':
            w_p = (wb if flat else -pw / 2, pw / 2)
        else:
            w_p = (wb if flat else F / 2 - 1, F / 2 + J)
        rect(w_p[0], base + clear, w_p[1], top, PALE, 'C')
    # the size marks
    dims.append(('A', 'F', (xa - C / 2 - C, base + clear), (xa - C / 2 - C, top), (-1, 0), 14))
    dims.append(('B', 'F', (0.0, 0.0), (B, 0.0), (0, -1), 16))
    dims.append(('C', 'F', (-C / 2, top + Dab), (C / 2, top + Dab), (0, 1), 12))
    if Dab > 0:
        dims.append(('D', 'F', (B + C / 2, top), (B + C / 2, top + Dab), (1, 0), 10))
    if rails and t != 'wire':
        y = rails[-1]
        dims.append(('E', 'C', (w_rail[1], y - E / 2), (w_rail[1], y + E / 2), (1, 0), 10))
        dims.append(('F', 'C', (w_rail[0], y + E / 2), (w_rail[1], y + E / 2), (0, 1), 10))
    if pw and first is not None and t != 'railings':
        l1, l2 = ('G', 'H') if t in ('picket', 'palisade') else ('K', 'L')
        p2 = first + pw + gap                      # the second pale (or board)
        ymid = base + clear + (A - clear) * 0.42
        dims.append((l1, 'F', (p2, ymid), (p2 + pw, ymid), (0, 1), 0))
        dims.append((l2, 'F', (first + pw, ymid - A * 0.18), (p2, ymid - A * 0.18), (0, -1), 0))
        dims.append(('J', 'C', (w_p[0] if flat else F / 2, top - A * 0.05),
                     (w_p[1], top - A * 0.05), (0, 1), 10))
    return {'front': front, 'cut': cut, 'dims': dims, 'xc': B * 0.5 + (pw / 2 if pw else 0)}


class FenceSizes(QWidget):
    """Front view and a cut through the fence, with each size marked by its letter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.d = None
        self.msg = ""

    def show_fence(self, v):
        try:
            self.d = fence_sizes_drawing(v)
            self.msg = ""
        except Exception as e:
            self.d, self.msg = None, str(e)
        self.update()

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen, QFont, QBrush
        from PySide6.QtCore import QPointF, Qt, QRectF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(252, 252, 250))
        d = self.d
        if not d:
            p.drawText(self.rect().adjusted(10, 10, -10, -10), Qt.AlignCenter | Qt.TextWordWrap,
                       self.msg or "No drawing")
            p.end()
            return
        fx = [q[0] for _, pts, _ in d['front'] for q in pts]
        fy = [q[1] for _, pts, _ in d['front'] for q in pts]
        cz = [q[0] for pts, _ in d['cut'] for q in pts]
        cy = [q[1] for pts, _ in d['cut'] for q in pts]
        M = 40.0
        W, Hh = self.width(), self.height()
        fw_mm = max(fx) - min(fx)
        cw_mm = max(cz) - min(cz)
        ylo, yhi = min(fy + cy + [0.0]), max(fy + cy)
        # the cut is narrow: drawn bigger than the front if it would be tiny
        sc = min((W - 3 * M - 20) / (fw_mm + max(cw_mm, fw_mm * 0.15)), (Hh - 2 * M - 16) / ((yhi - ylo) or 1))
        csc = min(sc * max(1.0, fw_mm * 0.15 / max(cw_mm, 1.0)), (W - 3 * M - 20 - fw_mm * sc) / max(cw_mm, 1.0))
        fx0 = M - min(fx) * sc
        cx0 = M + fw_mm * sc + M + 20 - min(cz) * csc
        ybase = Hh - M - 16

        def F(q):
            return QPointF(fx0 + q[0] * sc, ybase - (q[1] - ylo) * sc)

        def Cv(q):
            return QPointF(cx0 + q[0] * csc, ybase - (q[1] - ylo) * sc)
        p.setPen(QPen(QColor(150, 150, 150), 1))
        p.drawLine(F((min(fx), 0)), F((max(fx), 0)))
        p.drawLine(Cv((min(cz) - 20, 0)), Cv((max(cz) + 20, 0)))
        for _, pts, rgb in d['front']:
            col = QColor(*rgb)
            p.setBrush(col)
            p.setPen(QPen(col.darker(140), 0.6))
            p.drawPolygon(QPolygonF([F(q) for q in pts]))
        p.setPen(QPen(QColor(120, 120, 200), 1, Qt.DashLine))
        p.drawLine(F((d['xc'], yhi)), F((d['xc'], ylo)))
        for pts, rgb in d['cut']:
            col = QColor(*rgb)
            p.setBrush(col)
            p.setPen(QPen(col.darker(150), 0.8))
            p.drawPolygon(QPolygonF([Cv(q) for q in pts]))
        f = QFont()
        f.setPointSize(7)
        p.setFont(f)
        p.setPen(QColor(90, 90, 90))
        p.drawText(QRectF(M, Hh - 18, W / 2, 16), Qt.AlignLeft, "Front")
        p.drawText(QRectF(cx0 + min(cz) * csc - 10, Hh - 18, W / 2, 16), Qt.AlignLeft, "Cut (back on the left)")
        fb = QFont()
        fb.setPointSize(8)
        fb.setBold(True)
        p.setFont(fb)
        blue = QColor(20, 90, 200)
        for letter, view, p1, p2, o, off in d['dims']:
            T = F if view == 'F' else Cv
            a, b = T(p1), T(p2)
            ox, oy = o[0], -o[1]
            L = math.hypot(ox, oy) or 1.0
            ox, oy = ox / L, oy / L
            a2 = QPointF(a.x() + ox * off, a.y() + oy * off)
            b2 = QPointF(b.x() + ox * off, b.y() + oy * off)
            p.setPen(QPen(blue, 0.8))
            if off:
                p.drawLine(a, QPointF(a2.x() + ox * 3, a2.y() + oy * 3))
                p.drawLine(b, QPointF(b2.x() + ox * 3, b2.y() + oy * 3))
            p.drawLine(a2, b2)
            dx, dy = b2.x() - a2.x(), b2.y() - a2.y()
            Ld = math.hypot(dx, dy) or 1.0
            tx, ty = (dx - dy) / Ld * 3, (dy + dx) / Ld * 3
            for q in (a2, b2):
                p.drawLine(QPointF(q.x() - tx, q.y() - ty), QPointF(q.x() + tx, q.y() + ty))
            mx = (a2.x() + b2.x()) / 2 + ox * 10
            my = (a2.y() + b2.y()) / 2 + oy * 10
            r = 7.0
            p.setBrush(QBrush(QColor(255, 255, 255)))
            p.drawEllipse(QPointF(mx, my), r, r)
            p.drawText(QRectF(mx - r, my - r, 2 * r, 2 * r), Qt.AlignCenter, letter)
        p.end()


class FenceDialog(QDialog):
    def __init__(self, cur, viewport, tool):
        super().__init__(viewport)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.user_presets = load_presets()
        self._busy = False
        lay = QVBoxLayout(self)
        self.lbl = QLabel("Select an upright face (the fence fills it), a flat face on the ground (the "
                          "fence runs round it) or edges, then click 'Add fence'. Sizes are real-world mm.")
        self.lbl.setWordWrap(True)
        self.lbl.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl)
        self.lbl_report = QLabel()
        self.lbl_report.setWordWrap(True)
        self.lbl_report.setVisible(False)
        lay.addWidget(self.lbl_report)
        row = QHBoxLayout()
        lay.addLayout(row)
        from PySide6.QtWidgets import QTabWidget
        self.preview = FencePreview()
        self.sizes = FenceSizes()
        self.views = QTabWidget()
        self.views.addTab(self.preview, "3D view")
        self.views.addTab(self.sizes, "Sizes (A, B, C ...)")
        self.views.setTabToolTip(0, "A 3D look at the fence you'll get.")
        self.views.setTabToolTip(1, "A front view and a cut through the fence, showing what each lettered "
                                    "size (A, B, C ...) measures.")
        row.addWidget(self.views, 1)
        self.tabs = QTabWidget()
        row.addWidget(self.tabs, 1)
        self.w, self.labels = {}, {}
        for title, keys in TABS:
            page = QWidget()
            form = QFormLayout(page)
            for k in keys:
                spec = FIELDS[k]
                tip = spec[-1]
                if k in CHOICES:
                    wdg = QComboBox()
                    for key, text in CHOICES[k]:
                        wdg.addItem(text, key)
                    wdg.currentIndexChanged.connect(self.changed)
                elif k in BOOL_KEYS:
                    wdg = QCheckBox()
                    wdg.toggled.connect(self.changed)
                elif k in INT_KEYS:
                    wdg = QSpinBox()
                    wdg.setRange(int(spec[1]), int(spec[2]))
                    wdg.valueChanged.connect(self.changed)
                else:
                    wdg = QDoubleSpinBox()
                    wdg.setDecimals(spec[3])
                    wdg.setRange(spec[1], spec[2])
                    wdg.setSuffix(spec[4])
                    wdg.setKeyboardTracking(True)
                    wdg.valueChanged.connect(self.changed)
                lab = QLabel(spec[0])
                if tip:
                    wdg.setToolTip(tip)
                    lab.setToolTip(tip)
                form.addRow(lab, wdg)
                self.w[k] = wdg
                self.labels[k] = lab
            self.tabs.addTab(page, title)

        prow = QHBoxLayout()
        prow.addWidget(QLabel("Preset:"))
        self.cb_preset = QComboBox()
        prow.addWidget(self.cb_preset, 1)
        b_save = QPushButton("Save")
        b_save.setToolTip("Updates the preset you have open (no typing). For a new preset, use Save as.")
        b_saveas = QPushButton("Save as...")
        self.btn_preset_save = b_save
        b_del = QPushButton("Delete")
        b_dir = QPushButton("Folder")
        for b in (b_save, b_saveas, b_del, b_dir):
            prow.addWidget(b)
        lay.addLayout(prow)
        brow = QHBoxLayout()
        self.b_add = QPushButton("Add fence")
        self.b_add.setDefault(True)
        b_close = QPushButton("Close")
        brow.addWidget(self.b_add)
        brow.addStretch(1)
        brow.addWidget(b_close)
        lay.addLayout(brow)
        self.cb_preset.currentIndexChanged.connect(self.apply_preset)
        b_save.clicked.connect(self.save_preset)
        b_saveas.clicked.connect(lambda: self.save_preset_as())
        b_del.clicked.connect(self.delete_preset)
        b_dir.clicked.connect(self.open_folder)
        self.b_add.clicked.connect(lambda: self.tool.add_from_dialog(self))
        b_close.clicked.connect(self.close)
        self.refresh_presets()
        self.set_values(cur)

    def values(self):
        v = {}
        for k, wdg in self.w.items():
            if k in CHOICES:
                v[k] = wdg.currentData()
            elif k in BOOL_KEYS:
                v[k] = wdg.isChecked()
            elif k in INT_KEYS:
                v[k] = int(wdg.value())
            else:
                v[k] = float(wdg.value())
        for k, d in DEFAULTS.items():
            if v.get(k) is None:
                v[k] = d
        return v

    def set_values(self, d):
        self._busy = True
        try:
            for k, wdg in self.w.items():
                val = d.get(k, DEFAULTS.get(k))
                if val is None:
                    continue
                if k in CHOICES:
                    for i in range(wdg.count()):
                        if wdg.itemData(i) == val:
                            wdg.setCurrentIndex(i)
                elif k in BOOL_KEYS:
                    wdg.setChecked(bool(val))
                elif k in INT_KEYS:
                    wdg.setValue(int(val))
                else:
                    wdg.setValue(float(val))
        finally:
            self._busy = False
        self.changed()

    def changed(self, *_):
        if self._busy:
            return
        v = self.values()
        t = v['type']
        g = v['gate'] != 'none'
        en = {
            'pale_w': t in ('picket', 'palisade'), 'pale_top': t == 'picket',
            'pale_gap': t in ('picket', 'palisade'), 'board_gap': t in ('close', 'panel'),
            'pale_t': t in ('picket', 'palisade', 'close', 'panel'),
            'board_w': t in ('close', 'panel'), 'gravel_h': t == 'close',
            'rails': t in ('picket', 'palisade', 'close', 'post_rail', 'wire'),
            'post_top': t != 'railings', 'post_above': t != 'railings',
            'wire_d': t == 'wire', 'bar_w': t == 'railings', 'bar_gap': t == 'railings',
            'wall_h': t == 'railings', 'wall_t': t == 'railings', 'coping_h': t == 'railings',
            'coping_over': t == 'railings',
            'gate_edge': g, 'gate_pos': g, 'gate_w': g, 'gate_h': g, 'gate_post': g,
            'gate_stile': g and (v['gate'] == 'field' or t in ('wire', 'post_rail')),
            'gate_clear': g, 'gate_double': g, 'gate_open': g and not v['flat'],
            'holes': t in ('close', 'panel'), 'skew_ang': v['skew_pct'] > 0,
        }
        for k, on in en.items():
            self.w[k].setEnabled(bool(on))
            self.labels[k].setEnabled(bool(on))
        self.preview.show_fence(v)
        try:
            self.sizes.show_fence(v)
        except Exception:
            pass

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
            self.set_values(dict(DEFAULTS, **BUILTIN_PRESETS[name]))
        elif name and name in self.user_presets:
            self.set_values(dict(DEFAULTS, **self.user_presets[name]))

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
class FencesGatesTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+F"
    description = "Fences, railings and gates along an upright face, round a flat face or along edges."

    _dialog = None
    _saved = None

    def on_activate(self, viewport):
        dlg = FencesGatesTool._dialog
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
        if FencesGatesTool._saved:
            cur.update(FencesGatesTool._saved)
        dlg = FenceDialog(cur, viewport, self)
        FencesGatesTool._dialog = dlg

        def closed(*_):
            FencesGatesTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass

    def add_from_dialog(self, dlg):
        v = dlg.values()
        FencesGatesTool._saved = dict(v)
        viewport = dlg.viewport
        scene = getattr(viewport, 'scene', None)
        sel = runs_from_selection(scene, v) if scene is not None else []
        if not sel:
            QMessageBox.information(dlg, PLUGIN_NAME, "Select an upright face, a flat face on the ground, "
                                                      "or some edges first.")
            return
        runs = [r for _, rs, _ in sel for r in rs]
        try:
            parts, total = build_fence(runs, v)
        except ValueError as e:
            QMessageBox.warning(dlg, PLUGIN_NAME, str(e))
            return
        kind = TYPE_NAMES.get(v['type'], "Fence").split(" (")[0]
        names = {'posts': "Posts", 'rails': "Rails" if v['type'] != 'wire' else "Wires",
                 'pales': {'close': "Boards", 'panel': "Boards", 'railings': "Bars"}.get(v['type'], "Pales"),
                 'gate': "Gates" if v['gate_double'] else "Gate", 'wall': "Dwarf wall"}
        groups = [(names[k], parts[k]) for k in ('posts', 'rails', 'pales', 'gate', 'wall') if parts[k]]
        if not groups:
            QMessageBox.warning(dlg, PLUGIN_NAME, "Nothing was made: is the fence long enough?")
            return
        length = sum(r['L'] for r in runs) / 1000.0
        top = "Fence - %s - %.1f m" % (kind, length)
        remove = [f for _, _, f in sel if f is not None] if v.get('remove_face') else []
        nf = self.add_to_scene(viewport, groups, top, remove)
        if nf is None:
            return
        gate_ok = bool(parts['gate'])
        msg = "Added %.1f m of %s fence (%d run%s, %d pales / boards / bars), %d faces." % (
            length, kind.lower(), len(runs), "" if len(runs) == 1 else "s", total, nf)
        if v['gate'] != 'none':
            msg += " Gate: " + ("in run %d." % int(v['gate_edge']) if gate_ok else
                                "NOT made - run %d is missing or too short for it." % int(v['gate_edge']))
        if remove:
            msg += " Deleted the upright face%s." % ("s" if len(remove) > 1 else "")
        msg += "\nOne group '%s' holding: %s." % (top, ", ".join(n for n, _ in groups))
        dlg.show_report(msg, bad=(v['gate'] != 'none' and not gate_ok))

    def add_to_scene(self, viewport, parts, top_name="Fence", remove=()):
        """One parent group holding a child group per part (posts, rails, pales,
        gate, wall). The geometry is already in place, so no transforms are needed."""
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
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not add the fence:\n%s" % e)
            return None
        try:
            viewport.notify_scene_changed()
        except Exception:
            pass
        return stats['faces']


def run(viewport=None):
    FencesGatesTool().on_activate(viewport)
