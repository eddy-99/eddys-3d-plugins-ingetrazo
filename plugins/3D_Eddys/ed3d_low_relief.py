# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Low Relief for IngeTrazo
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
3D Low Relief - a whole building cut down to a low relief one, for IngeTrazo
Build the whole building as usual (Floor Plan, Openings, Frame, Windows, Doors, Chimneys, Roof,
Bricks, Gutters, Pipes, Colours), then cut it here, just before Scale Studio:

  Keep the front     the front of the building, a set depth back from its front wall (A) - a low
                     relief building to stand against the backscene.
  Keep the back      the back of the building, a set depth in from its back wall (B).
  Keep both          the front and the back, with the middle taken out: two low relief buildings
                     from one (a front for one scene, a back for another).

Every part is cut where it crosses the cut - walls, frame, floors, roof, tiles, gutters, chimneys -
and stays in its own group with its own name and colour, so Show / Hide and Scale Studio's pieces
work as before. Parts wholly behind the cut are taken away. The cut faces are filled in, so each
piece is still a closed solid ready to print, and a backing board can go on the back.
The roof comes out right by itself: its true slope, cut off where the building ends.

Several buildings: select them (a box round them will do), or nothing for the whole model. Each
building is cut on its own, A and B measured from its own walls - or all on one line, for a terrace
that should stay flush. Groups that overlap are one building (its walls, frame, roof, boards...);
a baseboard under more than one building is left whole.
Slivers: where the cut only just catches a part it leaves a sliver too thin to print - those can
be thrown away (anything the cut leaves thinner than a set size).

Sizes are real-world mm, like the other plugins - Scale Studio takes it down to your model scale.
One undo step. Ctrl+Alt+Shift+L.
"""

import os
import json
import math
import bisect
from tools.base import Tool
try:
    from core.history import SnapshotImport
except Exception:                       # (only when tried outside IngeTrazo)
    SnapshotImport = None
from PySide6.QtGui import QVector3D
try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox, QCheckBox,
        QPushButton, QLabel, QMessageBox, QWidget, QInputDialog, QTabWidget, QScrollArea
    )
except Exception:                       # (only when tried outside IngeTrazo)
    QDialog = QWidget = object

PLUGIN_NAME = "3D Low Relief"
VERSION = "1.2"   # 1.2: several buildings picked (or the whole model) - each one is cut on its own, measured from its own front and back walls (or all on one line, for a terrace); the tiny slivers a cut leaves can be thrown away; 1.1: a clearer preview - the building drawn solid in its own colours, with the front, back and what goes labelled; keeping both, the back is its own group ("... - back part") and the front "... - front part", with buttons to pick, show only, or send either part to Scale Studio; 1.0: cut a whole building down to low relief - keep the front, the back, or both with the middle taken out; cut faces filled in, a backing board if you want one

SCALE = 0.001                 # IngeTrazo stores metres; sizes here are real-world mm
EPS = 0.0002                  # m: the cut keeps 0.2 mm clear of any corner (IngeTrazo joins points under 0.1 mm)
KEY_TOL = 1e-6                # m: points closer than this are the same point when joining up the cut
PRESET_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Low Relief")
UI_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_low_relief.json")

KEEPS = [("The front (a low relief building)", 'front'),
         ("The back", 'back'),
         ("The front and the back (the middle taken out)", 'both')]
FRONTS = [("-Y side (IngeTrazo's Front view)", -90.0), ("+Y side", 90.0), ("-X side", 180.0), ("+X side", 0.0)]
MEASURES = [("The front of the walls (works it out)", 'wall'),
            ("The furthest part out (plinth, gutters, steps...)", 'out')]
EACH = [("Each building on its own (its own front and back)", 'each'),
        ("All on one line (a terrace that stays flush)", 'line')]
CAP_COLOURS = [("Like the part that's cut", 'part'), ("Plain grey (easy to see)", 'grey')]
GREY = {"color": (0.62, 0.62, 0.62)}
BOARD_COLOUR = {"color": (0.55, 0.47, 0.38)}

# sizes are real-world mm
DEFAULTS = dict(keep='front', front=-90.0, measure='wall', depth_a=1500.0, depth_b=1500.0,
                fill=True, cap_colour='part', board=False, board_thick=150.0, view='both',
                each='each', slivers=True, sliver_mm=40.0)
SIZE_KEYS = ('depth_a', 'depth_b', 'board_thick', 'sliver_mm')

BUILTIN_PRESETS = {
    "OO low relief - 20 mm deep": dict(keep='front', measure='wall', depth_a=1524.0, fill=True, board=False),
    "OO very low relief - 10 mm deep": dict(keep='front', measure='wall', depth_a=762.0, fill=True, board=False),
    "OO low relief with a 2 mm backing board": dict(keep='front', measure='wall', depth_a=1524.0, fill=True,
                                                    board=True, board_thick=152.0),
    "N low relief - 10 mm deep": dict(keep='front', measure='wall', depth_a=1480.0, fill=True, board=False),
    "O gauge low relief - 30 mm deep": dict(keep='front', measure='wall', depth_a=1305.0, fill=True, board=False),
    "Front and back - two OO low reliefs": dict(keep='both', measure='wall', depth_a=1524.0, depth_b=1524.0,
                                                fill=True, board=False),
}

SCALES_SHOWN = [("OO", 76.2), ("N", 148.0), ("O", 43.5)]


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


# ---------------------------------------------------------------------------
# Small sums
# ---------------------------------------------------------------------------
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _cross(u, v):
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def _dot(u, v):
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


def _len(a):
    return math.sqrt(_dot(a, a))


def _norm(a):
    n = _len(a)
    return (a[0] / n, a[1] / n, a[2] / n) if n > 1e-30 else (0.0, 0.0, 0.0)


def newell(pts):
    """The (unnormalised) normal of a polygon; its length is twice the polygon's area."""
    nx = ny = nz = 0.0
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    return (nx, ny, nz)


def area2d(p):
    s = 0.0
    n = len(p)
    for i in range(n):
        a, b = p[i], p[(i + 1) % n]
        s += a[0] * b[1] - b[0] * a[1]
    return s / 2.0


def point_in_poly(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            xc = xi + (y - yi) * (xj - xi) / (yj - yi)
            if x < xc:
                inside = not inside
        j = i
    return inside


class _Keys:
    """Turns positions into keys, treating points closer than tol as the same point."""

    def __init__(self, tol=KEY_TOL):
        self.tol = tol

    def __call__(self, q):
        t = self.tol
        return (int(round(q[0] / t)), int(round(q[1] / t)), int(round(q[2] / t)))


# ---------------------------------------------------------------------------
# Triangulating a face (from 3D Part Splitter): ear clipping, holes bridged in
# ---------------------------------------------------------------------------
def _seg_cross(p, q, a, b):
    def orient(u, v, w):
        return (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
    d1, d2 = orient(a, b, p), orient(a, b, q)
    d3, d4 = orient(p, q, a), orient(p, q, b)
    return ((d1 > 0 > d2) or (d1 < 0 < d2)) and ((d3 > 0 > d4) or (d3 < 0 < d4))


def _in_cone(a, b, c, p):
    def orient(u, v, w):
        return (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
    if orient(a, b, c) >= 0:
        return orient(b, c, p) >= 0 and orient(a, b, p) >= 0
    return not (orient(b, c, p) < 0 and orient(a, b, p) < 0)


def _bridge_holes(pts, outer, holes):
    ring = list(outer)
    order = sorted(holes, key=lambda h: -max(pts[i][0] for i in h))
    for k, h in enumerate(order):
        m = max(range(len(h)), key=lambda j: (pts[h[j]][0], -pts[h[j]][1]))
        M = pts[h[m]]
        others = [hh for hh in order[k + 1:]]
        cand = sorted(range(len(ring)), key=lambda j: ((pts[ring[j]][0] - M[0]) ** 2 +
                                                       (pts[ring[j]][1] - M[1]) ** 2,
                                                       0 if pts[ring[j]][0] >= M[0] else 1))
        edges = [(ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring))]
        edges += [(hh[i], hh[(i + 1) % len(hh)]) for hh in [h] + others for i in range(len(hh))]
        best = None
        for j in cand[:400]:
            P = pts[ring[j]]
            if P == M:
                best = j
                break
            ok = True
            for a, b in edges:
                if _seg_cross(M, P, pts[a], pts[b]):
                    ok = False
                    break
            if ok:
                n = len(ring)
                A, B, C = pts[ring[j - 1]], P, pts[ring[(j + 1) % n]]
                if _in_cone(A, B, C, M):
                    best = j
                    break
                if best is None:
                    best = -1 - j
        if best is None:
            best = cand[0]
        elif best < 0:
            best = -1 - best
        hole_ring = h[m:] + h[:m]
        ring = ring[:best + 1] + hole_ring + [hole_ring[0], ring[best]] + ring[best + 1:]
    return ring


def triangulate2d(pts, outer, holes=()):
    outer = list(outer)
    if area2d([pts[i] for i in outer]) < 0:
        outer.reverse()
    hs = []
    for h in holes or ():
        h = list(h)
        if len(h) < 3:
            continue
        if area2d([pts[i] for i in h]) > 0:
            h.reverse()
        hs.append(h)
    ring = _bridge_holes(pts, outer, hs) if hs else outer
    clean = []
    for i in ring:
        if clean and pts[clean[-1]] == pts[i]:
            continue
        clean.append(i)
    while len(clean) > 1 and pts[clean[0]] == pts[clean[-1]]:
        clean.pop()
    ring = clean
    n = len(ring)
    if n < 3:
        return []
    if n == 3:
        return [tuple(ring)]
    prv = [(i - 1) % n for i in range(n)]
    nxt = [(i + 1) % n for i in range(n)]
    P = [pts[i] for i in ring]

    def orient(u, v, w):
        return (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])

    def reflex(i):
        return orient(P[prv[i]], P[i], P[nxt[i]]) <= 0

    xs = [p[0] for p in P]
    ys = [p[1] for p in P]
    span = max(max(xs) - min(xs), max(ys) - min(ys)) or 1.0
    cells = max(1, int(math.sqrt(n) / 2))
    cs = span / cells
    x0, y0 = min(xs), min(ys)
    grid = {}

    def cell(p):
        return (int((p[0] - x0) / cs), int((p[1] - y0) / cs))
    alive = [True] * n
    for i in range(n):
        if reflex(i):
            grid.setdefault(cell(P[i]), set()).add(i)

    def is_ear(i):
        a, b, c = P[prv[i]], P[i], P[nxt[i]]
        if orient(a, b, c) <= 0:
            return False
        lo = cell((min(a[0], b[0], c[0]), min(a[1], b[1], c[1])))
        hi = cell((max(a[0], b[0], c[0]), max(a[1], b[1], c[1])))
        for gx in range(lo[0], hi[0] + 1):
            for gy in range(lo[1], hi[1] + 1):
                for j in grid.get((gx, gy), ()):
                    if j in (prv[i], i, nxt[i]) or not alive[j]:
                        continue
                    p = P[j]
                    if p == a or p == b or p == c:
                        continue
                    if orient(a, b, p) >= 0 and orient(b, c, p) >= 0 and orient(c, a, p) >= 0:
                        return False
        return True

    tris = []
    count = n
    i = 0
    stall = 0
    while count > 3:
        if is_ear(i) or stall > count:
            a, c = prv[i], nxt[i]
            if orient(P[a], P[i], P[c]) != 0 or stall <= count:
                tris.append((ring[a], ring[i], ring[c]))
            alive[i] = False
            grid.get(cell(P[i]), set()).discard(i)
            nxt[a], prv[c] = c, a
            count -= 1
            for j in (a, c):
                if reflex(j):
                    grid.setdefault(cell(P[j]), set()).add(j)
                else:
                    grid.get(cell(P[j]), set()).discard(j)
            i = c
            stall = 0
        else:
            i = nxt[i]
            stall += 1
    a, c = prv[i], nxt[i]
    if orient(P[a], P[i], P[c]) != 0:
        tris.append((ring[a], ring[i], ring[c]))
    return tris


def inside_point(p2):
    """A point well inside a 2D polygon (the middle of its biggest triangle)."""
    tris = triangulate2d(p2, list(range(len(p2))))
    if not tris:
        return p2[0]
    best = max(tris, key=lambda t: abs(area2d([p2[t[0]], p2[t[1]], p2[t[2]]])))
    return tuple(sum(p2[i][k] for i in best) / 3.0 for k in range(2))


def _drop_axis(normal):
    ax = max(range(3), key=lambda k: abs(normal[k]))
    return ax, ((ax + 1) % 3, (ax + 2) % 3)


def triangulate_face(outer, holes=()):
    """Triangles for a 3D face (outline + holes), all turned the face's way."""
    if len(outer) < 3:
        return []
    if not holes and len(outer) == 3:
        return [tuple(outer)]
    nrm = newell(outer)
    if _dot(nrm, nrm) < 1e-30:
        return []
    ax, (u, v) = _drop_axis(nrm)
    allp = list(outer) + [q for h in holes for q in h]
    p2 = [(q[u], q[v]) for q in allp]
    oi = list(range(len(outer)))
    his, k = [], len(outer)
    for h in holes:
        his.append(list(range(k, k + len(h))))
        k += len(h)
    out = []
    for a, b, c in triangulate2d(p2, oi, his):
        t = (allp[a], allp[b], allp[c])
        if _dot(_cross(_sub(t[1], t[0]), _sub(t[2], t[0])), nrm) < 0:
            t = (t[0], t[2], t[1])
        out.append(t)
    return out


# ---------------------------------------------------------------------------
# Cutting
# ---------------------------------------------------------------------------
def _edge_point(a, b, da, db):
    """Where the cut crosses edge a-b. Worked out the same way whichever way round the edge is
    given, so the two faces either side of an edge get exactly the same point."""
    if (a, da) > (b, db):
        a, b, da, db = b, a, db, da
    s = da / (da - db)
    return (a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s, a[2] + (b[2] - a[2]) * s)


def clip_face(pts, holes, dfun, up, key):
    """The part of a face (outline + holes, 3D) on the kept side of a cut, done along the cut
    line itself (no triangles), so the face keeps its own corners exactly.
    dfun(q): signed distance past the cut; up: keep d >= 0 (else d <= 0).
    Returns (faces [(outline, [holes])], cut segments [(p, q)])."""
    N = newell(pts)
    nn = _len(N)
    if nn < 1e-18:
        return [], []
    N = _mul(N, 1.0 / nn)
    e1, e2 = _plane_basis(N)

    def to2(q):
        return (_dot(q, e1), _dot(q, e2))
    loops = [list(pts)] + [list(h) for h in holes]
    sgn = 1.0 if up else -1.0
    edges = []                    # directed (p, q) of the kept region's boundary
    cross = []                    # (point, along) where the boundary meets the cut
    for li, lp in enumerate(loops):
        n = len(lp)
        a2 = area2d([to2(q) for q in lp])
        if (li == 0) != (a2 > 0):
            lp = lp[::-1]         # outline anticlockwise, holes clockwise (seen from the front)
        d = [dfun(q) * sgn for q in lp]
        for i in range(n):
            a, b = lp[i], lp[(i + 1) % n]
            da, db = d[i], d[(i + 1) % n]
            ka, kb = da >= 0, db >= 0
            if ka and kb:
                edges.append((a, b))
            elif ka != kb:
                x = _edge_point(a, b, da / sgn, db / sgn)
                if ka:
                    edges.append((a, x))
                else:
                    edges.append((x, b))
                cross.append(x)
    if not edges:
        return [], []
    # along the cut: the stretches inside the face, run with the kept part on their left
    segs = []
    if cross:
        g = _sub(_wmap_dir(dfun, cross[0], N), (0.0, 0.0, 0.0))
        k2 = to2(g)
        k2 = (k2[0] * sgn, k2[1] * sgn)
        L2 = (k2[1], -k2[0])
        cross.sort(key=lambda q: _dot(q, e1) * L2[0] + _dot(q, e2) * L2[1])
        for i in range(0, len(cross) - 1, 2):
            p_, q_ = cross[i], cross[i + 1]
            if key(p_) != key(q_):
                edges.append((p_, q_))
                segs.append((p_, q_))
    # walk the edges into loops
    out_of, pos = {}, {}
    for a, b in edges:
        ka, kb = key(a), key(b)
        if ka == kb:
            continue
        pos.setdefault(ka, a)
        pos.setdefault(kb, b)
        out_of.setdefault(ka, []).append(kb)
    loops_out = []
    for s0 in list(out_of):
        while out_of.get(s0):
            line, cur = [s0], s0
            guard = 0
            while guard < 1000000:
                guard += 1
                nxts = out_of.get(cur)
                if not nxts:
                    break
                nb = nxts.pop()
                if nb == s0:
                    break
                line.append(nb)
                cur = nb
            if len(line) >= 3:
                loops_out.append([pos[k_] for k_ in line])
    outers, hls = [], []
    for lp in loops_out:
        p2 = [to2(q) for q in lp]
        a = area2d(p2)
        if abs(a) < 1e-12:
            continue
        (outers if a > 0 else hls).append((abs(a), lp, p2))
    outers.sort(key=lambda e: e[0])
    faces = [[o[1], [], o[2], o[0]] for o in outers]
    for a, lp, p2 in hls:
        ip = inside_point(p2)
        for f in faces:
            if f[3] > a and point_in_poly(ip, f[2]):
                f[1].append(lp)
                break
    return [(f[0], f[1]) for f in faces], segs


def _wmap_dir(dfun, q, N):
    """Which way the cut's distance grows, along the face (from three nearby points)."""
    h = 0.01
    d0 = dfun(q)
    g = (dfun(_add(q, (h, 0.0, 0.0))) - d0, dfun(_add(q, (0.0, h, 0.0))) - d0, dfun(_add(q, (0.0, 0.0, h))) - d0)
    return _sub(g, _mul(N, _dot(g, N)))


def _loops(segs, key):
    """Closed loops from the cut's line segments. Each segment runs the way round that keeps the
    solid on its left (looking along the cut's direction), so outlines go anticlockwise and holes
    clockwise, and solids pushed into each other still come out right. A line that doesn't quite
    close (a gap in the model) is closed across the gap if the gap is small; otherwise it's left
    (an open sheet, like a pane of glass or a sheet of tin, has nothing to fill)."""
    out_of, pos = {}, {}
    for i, (p, q) in enumerate(segs):
        a, b = key(p), key(q)
        if a == b:
            continue
        pos.setdefault(a, p)
        pos.setdefault(b, q)
        out_of.setdefault(a, []).append((b, i))
    into = {}
    for a, lst in out_of.items():
        for b, i in lst:
            into[b] = into.get(b, 0) + 1
    used = set()
    loops, opened = [], 0

    def walk(s):
        line = [s]
        cur = s
        while True:
            nb = next(((b, i) for b, i in out_of.get(cur, ()) if i not in used), None)
            if nb is None:
                return line, False
            used.add(nb[1])
            if nb[0] == s:
                return line, True
            line.append(nb[0])
            cur = nb[0]

    def take(line, closed):
        nonlocal opened
        pts = [pos[k] for k in line]
        if closed:
            if len(pts) >= 3:
                loops.append(pts)
            return
        if len(pts) < 3:
            return
        per = sum(_len(_sub(pts[i + 1], pts[i])) for i in range(len(pts) - 1))
        gap = _len(_sub(pts[-1], pts[0]))
        if gap < max(0.002, per * 0.05):
            loops.append(pts)
        else:
            opened += 1
    # lines that start where nothing comes in (an open sheet, or a gap) first, from their start
    for s in [k for k in out_of if out_of[k] and into.get(k, 0) == 0]:
        while any(i not in used for _b, i in out_of[s]):
            take(*walk(s))
    for s in list(out_of):
        while any(i not in used for _b, i in out_of[s]):
            take(*walk(s))
    return loops, opened


def _plane_basis(n):
    """(u, v) on the cut, so that anticlockwise in (u, v) faces along n."""
    a = (0.0, 0.0, 1.0) if abs(n[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = _norm(_cross(a, n))
    v = _cross(n, u)
    return u, v


def cap_faces(loops, n, facing_n):
    """Fills the cut. The loops run anticlockwise round solid (outlines) and clockwise round
    holes (seen along n), so each hole goes in the smallest outline round it. Outlines that
    overlap (solids pushed into each other) each get their own face.
    facing_n: the faces look along n (else against it)."""
    u, v = _plane_basis(n)
    outers, holes = [], []
    for lp in loops:
        p2 = [(_dot(q, u), _dot(q, v)) for q in lp]
        a = area2d(p2)
        if abs(a) < 1e-12:
            continue
        (outers if a > 0 else holes).append((abs(a), lp, p2))
    outers.sort(key=lambda e: e[0])
    faces = [[o[1], [], o[2], o[0]] for o in outers]
    for a, lp, p2 in holes:
        p = inside_point(p2)
        for f in faces:                       # the smallest outline round it
            if f[3] > a and point_in_poly(p, f[2]):
                f[1].append(lp)
                break
    out = []
    for outer, hs, _p2, _a in faces:
        outer = list(outer)
        hs = [list(h) for h in hs]
        if not facing_n:
            outer.reverse()
            for h in hs:
                h.reverse()
        out.append((outer, hs))
    return out


def _bodies(faces, key):
    """Which solid each face belongs to (faces that share a corner are one solid): [body id]."""
    parent = {}

    def find(a):
        root = a
        while parent[root] != root:
            root = parent[root]
        while parent[a] != root:
            parent[a], a = root, parent[a]
        return root
    first = []
    for fd in faces:
        ks = [key(q) for q in fd['pts']] + [key(q) for h in fd['holes'] for q in h]
        for k in ks:
            parent.setdefault(k, k)
        r = find(ks[0])
        for k in ks[1:]:
            r2 = find(k)
            if r2 != r:
                parent[r2] = r
        first.append(ks[0])
    return [find(k) for k in first]


def _mode_cuts(keep, t1, t2):
    """The cuts as [(plane value, side kept)]: 'up' keeps t >= value, 'down' keeps t <= value."""
    out = []
    if keep in ('front', 'both'):
        out.append((t1, 'up'))
    if keep in ('back', 'both'):
        out.append((t2, 'down'))
    return out


def _on_kept_side(t, c, side):
    return (t >= c) if side == 'up' else (t <= c)


def cut_faces(faces, tfun, n_local, cuts, fill=True, cap_attrs=None, min_keep=0.0):
    """Cuts one mesh's faces. faces: [dict(pts, holes, attrs)] in the mesh's own coordinates;
    tfun(q): how far forward a point is (world metres); n_local: the forward direction in the
    mesh's own coordinates; cuts: from _mode_cuts.
    Returns dict(faces=[(pts, holes, attrs)] to keep, parts={side: faces} (the same faces, by the
    part they're in: 'up' the front, 'down' the back), cap_list=[(side, outline)], changed,
    kept_any, crossed, opened, caps, slivers).
    min_keep (world metres): a solid the cut leaves thinner than this (front to back, from the cut)
    is thrown away - a sliver too thin to print. Solids the cut doesn't touch are never thrown away."""
    key = _Keys()
    out = []
    tags = []                   # for each face kept: (body, side) - for throwing away slivers
    hit = set()                 # (body, cut index) the cut went through
    parts = {side: [] for _c, side in cuts}
    cap_list = []
    changed = False
    crossed = 0
    segs = {}                   # (body, cut index) -> [(p, q)]
    cap_attr_votes = {}         # body -> {attrs json: (count, attrs)}
    body_of = None
    for fi, fd in enumerate(faces):
        allp = fd['pts'] + [q for h in fd['holes'] for q in h]
        ts = [tfun(q) for q in allp]
        whole = next((side for c, side in cuts if all(_on_kept_side(t, c, side) for t in ts)), None)
        if whole is not None:
            f_ = (fd['pts'], fd['holes'], fd['attrs'])                 # wholly in a kept part
            out.append(f_)
            parts[whole].append(f_)
            if min_keep > 0:
                if body_of is None:
                    body_of = _bodies(faces, key)
                tags.append((body_of[fi], whole))
            continue
        changed = True
        if all(not _on_kept_side(t, c, side) for t in ts for c, side in cuts):
            continue                                                    # wholly in the part taken away
        # it crosses a cut: cut it up, keep the pieces in the kept parts
        crossed += 1
        if body_of is None:
            body_of = _bodies(faces, key)
        b = body_of[fi]
        nt = newell(fd['pts'])
        for ci, (c, side) in enumerate(cuts):
            if all(not _on_kept_side(t, c, side) for t in ts):
                continue
            pieces, cs = clip_face(fd['pts'], fd['holes'], lambda q, c=c: tfun(q) - c, side == 'up', key)
            if pieces:
                hit.add((b, ci))
            for outer, hs in pieces:
                out.append((outer, hs, fd['attrs']))
                parts[side].append(out[-1])
                tags.append((b, side))
            for p_, q_ in cs:
                # run it the way that keeps this solid on its left, seen along n
                if _dot(_cross(n_local, nt), _sub(q_, p_)) < 0:
                    p_, q_ = q_, p_
                segs.setdefault((b, ci), []).append((p_, q_))
        a = dict(fd['attrs'] or {})
        try:
            k_ = json.dumps(a, sort_keys=True, default=str)
        except Exception:
            k_ = repr(sorted(a.items()))
        votes = cap_attr_votes.setdefault(b, {})
        cnt, _ = votes.get(k_, (0, a))
        votes[k_] = (cnt + 1, a)
    caps = 0
    opened = 0
    if fill and segs:
        for (b, ci), sl in segs.items():
            loops, op = _loops(sl, key)
            opened += op
            if not loops:
                continue
            side = cuts[ci][1]
            # the cap looks out of the kept part, towards what was taken away
            facing = side == 'down'
            if cap_attrs is not None:
                attrs = dict(cap_attrs)
            else:
                votes = cap_attr_votes.get(b) or {}
                attrs = max(votes.values(), key=lambda e: e[0])[1] if votes else {}
            for outer, hs in cap_faces(loops, n_local, facing):
                out.append((outer, hs, attrs))
                parts[side].append(out[-1])
                cap_list.append((side, outer))
                tags.append((b, side))
                caps += 1
    slivers = 0
    if min_keep > 0 and hit and len(tags) == len(out):
        # what the cut leaves of each solid it went through: thinner than min_keep is a sliver
        depth = {}
        for (b, ci) in hit:
            c, side = cuts[ci]
            ts_ = [tfun(q) for f_, tg in zip(out, tags) if tg == (b, side) for q in f_[0]]
            if ts_:
                d = (max(ts_) - c) if side == 'up' else (c - min(ts_))
                depth[(b, side)] = min(depth.get((b, side), d), d)
        thin = set(k for k, d in depth.items() if d < min_keep)
        if thin:
            slivers = len(thin)
            drop = set(id(f_) for f_, tg in zip(out, tags) if tg in thin)
            out = [f_ for f_ in out if id(f_) not in drop]
            parts = {sd: [f_ for f_ in fl if id(f_) not in drop] for sd, fl in parts.items()}
            keep_outers = set(id(f_[0]) for f_ in out)
            cap_list = [(sd, o) for sd, o in cap_list if id(o) in keep_outers]
            caps = len(cap_list)
    return {'faces': out, 'parts': parts, 'cap_list': cap_list, 'changed': changed, 'kept_any': bool(out),
            'crossed': crossed, 'opened': opened, 'caps': caps, 'slivers': slivers}


# ---------------------------------------------------------------------------
# Reading the model
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
    for get in (lambda: (v.x(), v.y(), v.z()), lambda: (v.x, v.y, v.z), lambda: (v[0], v[1], v[2]),
                lambda: (v.pos.x(), v.pos.y(), v.pos.z()), lambda: (v.position.x(), v.position.y(), v.position.z())):
        try:
            x, y, z = get()
            return (float(x), float(y), float(z))
        except Exception:
            pass
    return None


KID_ATTRS = ('children', 'groups')


def _kids_of(g):
    out = []
    for attr in KID_ATTRS:
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
            for c in _kids_of(g):
                walk(c, m, depth + 1)
    walk(top, None, 0)
    return out


def _wmap(m, p):
    if m is None:
        return p
    q = m.map(QVector3D(*p))
    return (q.x(), q.y(), q.z())


def _faces_of(mesh):
    """[dict(pts, holes, attrs)] for every face of a mesh (its own coordinates, metres)."""
    out = []
    for f in _items(getattr(mesh, 'faces', None)):
        pts = [q for q in (_pos(v) for v in _items(getattr(f, 'vertices', None))) if q is not None]
        if len(pts) < 3:
            continue
        hls = []
        for h in _items(getattr(f, 'holes', None)):
            hp = [q for q in (_pos(v) for v in _items(h)) if q is not None]
            if len(hp) >= 3:
                hls.append(hp)
        try:
            attrs = dict(getattr(f, 'attrs', None) or {})
        except Exception:
            attrs = {}
        out.append({'pts': pts, 'holes': hls, 'attrs': attrs})
    return out


def _picked(scene):
    return _items(getattr(scene, 'selection', None))


def _in_tree(top, g):
    stack, seen = [top], 0
    while stack and seen < 100000:
        x = stack.pop()
        seen += 1
        if x is g:
            return True
        stack += _kids_of(x)
    return False


def _mesh_has(mesh, face):
    try:
        return face in mesh.faces
    except Exception:
        return False


def tops_to_cut(scene):
    """The buildings to cut: the top-level groups holding what's picked, or every top-level group
    when nothing is picked. Returns (tops, whole model?)."""
    tops = [t for t in _items(getattr(scene, 'groups', None))
            if not getattr(t, 'billboard', False)]          # scale figures are left alone
    picked = _picked(scene)
    if not picked:
        return tops, True
    out = []
    for t in tops:
        if any(t is p for p in picked) or any(_in_tree(t, p) for p in picked if getattr(p, 'mesh', None) is not None
                                              or _kids_of(p)):
            out.append(t)
            continue
        faces = [p for p in picked if getattr(p, 'mesh', None) is None and not _kids_of(p)]
        if faces and any(_mesh_has(getattr(g, 'mesh', None), f) for g, _m in _placements(t) for f in faces
                         if getattr(g, 'mesh', None) is not None):
            out.append(t)
    return (out, False) if out else (tops, True)


def picked_face_normal(scene):
    """The world direction (flat, along the ground) a picked face looks, or None."""
    for e in _picked(scene):
        if getattr(e, 'mesh', None) is not None or _kids_of(e):
            continue
        vs = getattr(e, 'vertices', None)
        if vs is None or callable(vs):
            continue
        pts = [q for q in (_pos(v) for v in _items(vs)) if q is not None]
        if len(pts) < 3:
            continue
        m = None
        for t in _items(getattr(scene, 'groups', None)):
            for g, mm in _placements(t):
                if _mesh_has(getattr(g, 'mesh', None), e):
                    m = mm
                    break
            if m is not None:
                break
        wp = [_wmap(m, q) for q in pts]
        n = newell(wp)
        flat = (n[0], n[1], 0.0)
        if _len(flat) < 1e-12 or _len(flat) < 0.3 * _len(n):
            continue
        return _norm(flat)
    return None


class Leaf:
    """One group with faces of its own, where it is in the world, and what holds it."""
    __slots__ = ('g', 'mesh', 'm', 'owner', 'attr', 'top', 'parent', 'repeat')

    def __init__(self, g, mesh, m, owner, attr, top, parent):
        self.g, self.mesh, self.m, self.owner, self.attr, self.top, self.parent = g, mesh, m, owner, attr, top, parent
        self.repeat = False


def gather(scene, tops):
    """Every group in the buildings (with what holds it), and their world placements.
    Returns (leaves, all groups [(group, owner, attr, top, parent)])."""
    holders = {}
    allg = []
    for t in tops:
        holders[id(t)] = (scene, 'groups', t, None)
        allg.append((t, scene, 'groups', t, None))
        stack = [t]
        guard = 0
        while stack and guard < 200000:
            guard += 1
            g = stack.pop()
            for attr in KID_ATTRS:
                for c in _items(getattr(g, attr, None)):
                    if id(c) not in holders:
                        holders[id(c)] = (g, attr, t, g)
                        allg.append((c, g, attr, t, g))
                        stack.append(c)
    leaves, seen = [], {}
    for t in tops:
        for g, m in _placements(t):
            mesh = getattr(g, 'mesh', None)
            if mesh is None or not _items(getattr(mesh, 'faces', None)):
                continue
            owner, attr, top, parent = holders.get(id(g), (scene, 'groups', t, None))
            lf = Leaf(g, mesh, m, owner, attr, top, parent)
            if id(g) in seen:
                seen[id(g)].repeat = True
                lf.repeat = True
            seen[id(g)] = lf
            leaves.append(lf)
    return leaves, allg


def local_t(m, f):
    """t(world point) = dot(point, f) as a sum in a group's own coordinates:
    (normal in its own terms, offset) so that t = dot(q, n) + o."""
    o = _dot(_wmap(m, (0.0, 0.0, 0.0)), f)
    n = tuple(_dot(_wmap(m, e), f) - o for e in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
    return n, o


class Survey:
    """What the plugin knows about the building: its outline for the preview, and the facts the
    cut needs (every corner's place, which faces look forward), read once."""

    def __init__(self, scene, tops=None):
        self.scene = scene
        if tops is not None:
            self.tops, self.whole = list(tops), False
        else:
            self.tops, self.whole = tops_to_cut(scene) if scene is not None else ([], True)
        self.leaves, self.allg = gather(scene, self.tops) if scene is not None else ([], [])
        # how many groups in the whole model use each mesh (copies of a component share one)
        self.mesh_users = {}
        stack = list(_items(getattr(scene, 'groups', None))) if scene is not None else []
        guard = 0
        while stack and guard < 300000:
            guard += 1
            g = stack.pop()
            m_ = getattr(g, 'mesh', None)
            if m_ is not None:
                self.mesh_users[id(m_)] = self.mesh_users.get(id(m_), 0) + 1
            stack += _kids_of(g)
        self.polys = []              # (world outline, colour, unit normal) for the preview
        self.facing = []             # (flat normal, area, centre) of upright faces, world
        self.points = []             # every world corner (x, y)
        self.zlo = self.zhi = 0.0
        self.nfaces = 0
        zs = []
        cand = []
        # the same facts, top by top (which building each belongs to)
        self.pt_top, self.facing_top, self.box = [], [], {}
        for lf in self.leaves:
            fl = _faces_of(lf.mesh)
            self.nfaces += len(fl)
            tk = id(lf.top)
            bx = self.box.get(tk)
            for fd in fl:
                wp = [_wmap(lf.m, q) for q in fd['pts']]
                for q in wp:
                    self.points.append((q[0], q[1]))
                    self.pt_top.append(tk)
                    zs.append(q[2])
                    if bx is None:
                        bx = self.box[tk] = [q[0], q[0], q[1], q[1], q[2], q[2]]
                    else:
                        if q[0] < bx[0]: bx[0] = q[0]
                        if q[0] > bx[1]: bx[1] = q[0]
                        if q[1] < bx[2]: bx[2] = q[1]
                        if q[1] > bx[3]: bx[3] = q[1]
                        if q[2] < bx[4]: bx[4] = q[2]
                        if q[2] > bx[5]: bx[5] = q[2]
                for h in fd['holes']:
                    for q in h:
                        w = _wmap(lf.m, q)
                        self.points.append((w[0], w[1]))
                        self.pt_top.append(tk)
                n = newell(wp)
                a = _len(n) / 2.0
                if a > 1e-8 and abs(n[2]) < 0.2 * _len(n):
                    c = tuple(sum(q[i] for q in wp) / len(wp) for i in range(3))
                    self.facing.append((_norm((n[0], n[1], 0.0)), a, c))
                    self.facing_top.append(tk)
                if a > 1e-10:
                    col = fd['attrs'].get('color') if isinstance(fd['attrs'], dict) else None
                    try:
                        col = tuple(float(x) for x in col[:3])
                    except Exception:
                        col = (0.82, 0.80, 0.74)
                    cand.append((a, wp, col, _mul(n, 0.5 / a)))
        # the biggest faces for the preview (a model of bricks has more than it needs to show)
        if len(cand) > 60000:
            cand.sort(key=lambda e: -e[0])
            cand = cand[:60000]
        self.polys = [(wp, col, n) for _a, wp, col, n in cand]
        if zs:
            self.zlo, self.zhi = min(zs), max(zs)

    def empty(self):
        return not self.leaves

    def sub(self, tops):
        """The same facts for some of the buildings only (no need to read the model again)."""
        ids = set(id(t) for t in tops)
        o = Survey.__new__(Survey)
        o.scene = self.scene
        o.tops = [t for t in self.tops if id(t) in ids]
        o.whole = False
        o.leaves = [lf for lf in self.leaves if id(lf.top) in ids]
        o.allg = [e for e in self.allg if id(e[3]) in ids]
        o.mesh_users = self.mesh_users
        o.points = [p for p, tk in zip(self.points, self.pt_top) if tk in ids]
        o.pt_top = [tk for tk in self.pt_top if tk in ids]
        o.facing = [e for e, tk in zip(self.facing, self.facing_top) if tk in ids]
        o.facing_top = [tk for tk in self.facing_top if tk in ids]
        o.box = {k: b for k, b in self.box.items() if k in ids}
        o.polys = self.polys
        o.nfaces = self.nfaces
        o.zlo, o.zhi = self.zlo, self.zhi
        return o

    def buildings(self):
        """The buildings among the groups picked: groups whose outlines overlap (seen from above) are
        one building - its walls, frame, roof, boards, chimneys. A low flat group (a baseboard, a yard)
        goes with the one building it's under; under more than one, it is left whole.
        Returns ([[tops] for each building], [tops left whole]). Cached."""
        got = self.__dict__.get('_buildings')
        if got is not None:
            return got
        tops = [t for t in self.tops if id(t) in self.box]
        if len(tops) < 2:
            res = ([tops] if tops else [], [])
            self._buildings = res
            return res
        tall = max(self.box[id(t)][5] - self.box[id(t)][4] for t in tops) or 1.0
        flat = [t for t in tops if self.box[id(t)][5] - self.box[id(t)][4] < 0.2 * tall]
        solid = [t for t in tops if not any(t is x for x in flat)]
        if not solid:
            solid, flat = tops, []
        OV = 0.002                                     # 2 mm: just touching (a terrace) isn't one building

        def over(a, b):
            A, B = self.box[id(a)], self.box[id(b)]
            return min(A[1], B[1]) - max(A[0], B[0]) > OV and min(A[3], B[3]) - max(A[2], B[2]) > OV
        parent = list(range(len(solid)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for i in range(len(solid)):
            for j in range(i + 1, len(solid)):
                if over(solid[i], solid[j]):
                    parent[find(j)] = find(i)
        groups = {}
        for i, t in enumerate(solid):
            groups.setdefault(find(i), []).append(t)
        blds = list(groups.values())
        left = []
        for t in flat:
            under = [b for b in blds if any(over(t, x) for x in b)]
            if len(under) == 1:
                under[0].append(t)
            elif not under:
                blds.append([t])
            else:
                left.append(t)
        order = {id(t): i for i, t in enumerate(self.tops)}
        for b in blds:
            b.sort(key=lambda t: order.get(id(t), 0))
        blds.sort(key=lambda b: order.get(id(b[0]), 0))
        self._buildings = (blds, left)
        return self._buildings

    def building_name(self, tops):
        """A building's name: its biggest group's."""
        def size(t):
            b = self.box.get(id(t)) or [0] * 6
            return (b[1] - b[0]) * (b[3] - b[2]) * (b[5] - b[4])
        t = max(tops, key=size)
        return str(getattr(t, 'name', '') or 'a building')

    def frame(self, f):
        """The facts for one front direction f: dict(lo, hi, wall_front, wall_back), world t."""
        k_ = (round(f[0], 9), round(f[1], 9))
        memo = self.__dict__.setdefault('_frames', {})
        if k_ not in memo:
            memo.clear()
            memo[k_] = self._frame(f)
        return memo[k_]

    def _frame(self, f):
        ts = [p[0] * f[0] + p[1] * f[1] for p in self.points]
        if not ts:
            return None
        lo, hi = min(ts), max(ts)

        def wall(sign):
            bins = {}
            for n, a, c in self.facing:
                if (n[0] * f[0] + n[1] * f[1]) * sign > 0.97:
                    t = c[0] * f[0] + c[1] * f[1]
                    k = int(round(t / 0.005))           # 5 mm steps
                    bins[k] = bins.get(k, 0.0) + a
            if not bins:
                return None
            best = max(bins.values())
            # the biggest face in that direction, nearest the outside if there are several as big
            ks = [k for k, a in bins.items() if a >= best * 0.6]
            k = max(ks) if sign > 0 else min(ks)
            # the faces themselves, for the exact place
            sel = [(c[0] * f[0] + c[1] * f[1], a) for n, a, c in self.facing
                   if (n[0] * f[0] + n[1] * f[1]) * sign > 0.97 and int(round((c[0] * f[0] + c[1] * f[1]) / 0.005)) == k]
            tot = sum(a for _t, a in sel) or 1.0
            return sum(t * a for t, a in sel) / tot
        return {'lo': lo, 'hi': hi, 'wall_front': wall(1.0), 'wall_back': wall(-1.0), 'ts': sorted(ts)}


def front_vector(angle_deg):
    a = math.radians(angle_deg)
    return (math.cos(a), math.sin(a), 0.0)


def _clear(t, ts_sorted, toward):
    """Moves a cut value along (toward = -1 down, +1 up) until no corner is within EPS of it."""
    for _i in range(5000):
        i = bisect.bisect_left(ts_sorted, t - EPS)
        if i < len(ts_sorted) and ts_sorted[i] <= t + EPS:
            if toward < 0:
                t = ts_sorted[i] - EPS * 1.5
            else:
                j = bisect.bisect_right(ts_sorted, t + EPS) - 1
                t = ts_sorted[j] + EPS * 1.5
            continue
        return t
    return t


def plan_cut(survey, v):
    """Where the cuts go, world t values. Returns dict(cuts, f, t1, t2, info) or raises ValueError."""
    f = front_vector(v['front'])
    fr = survey.frame(f)
    if fr is None:
        raise ValueError("There's nothing to cut.")
    if v['measure'] == 'wall':
        front0 = fr['wall_front'] if fr['wall_front'] is not None else fr['hi']
        back0 = fr['wall_back'] if fr['wall_back'] is not None else fr['lo']
    else:
        front0, back0 = fr['hi'], fr['lo']
    keep = v['keep']
    t1 = front0 - v['depth_a'] * SCALE
    t2 = back0 + v['depth_b'] * SCALE
    ts = fr['ts']
    if keep in ('front', 'both'):
        t1 = _clear(t1, ts, -1)
        if t1 <= fr['lo']:
            raise ValueError("The front part (A) is as deep as the whole building or deeper - nothing would be "
                             "cut. Make A smaller.")
    if keep in ('back', 'both'):
        t2 = _clear(t2, ts, +1)
        if t2 >= fr['hi']:
            raise ValueError("The back part (B) is as deep as the whole building or deeper - nothing would be "
                             "cut. Make B smaller.")
    if keep == 'both' and t2 >= t1:
        raise ValueError("A and B together are deeper than the building, so there's no middle to take out. "
                         "Make A or B smaller.")
    return {'cuts': _mode_cuts(keep, t1, t2), 'f': f, 't1': t1, 't2': t2, 'frame': fr,
            'front0': front0, 'back0': back0}


def plan_all(survey, v):
    """plan_cut for what's picked: with several buildings each cut on its own, a plan for each, in
    plan['each'] as [(plan or None, error, lo u, hi u, name, tops)] (u: across the front)."""
    blds, left = survey.buildings()
    if v.get('each', 'each') != 'each' or len(blds) < 2:
        if left:
            sv = survey.sub([t for b in blds for t in b])
            pl = plan_cut(sv, v)
            pl['left'] = left
            return pl
        return plan_cut(survey, v)
    f = front_vector(v['front'])
    r = (-f[1], f[0])
    each, firsts = [], None
    for b in blds:
        sv = survey.sub(b)
        us = [p[0] * r[0] + p[1] * r[1] for p in sv.points]
        lo, hi = (min(us), max(us)) if us else (0.0, 0.0)
        try:
            pl, err = plan_cut(sv, v), ""
        except ValueError as e:
            pl, err = None, str(e)
        each.append((pl, err, lo, hi, survey.building_name(b), b))
        if pl is not None and firsts is None:
            firsts = pl
    if firsts is None:
        raise ValueError(each[0][1] if each else "There's nothing to cut.")
    out = dict(firsts)
    out['each'] = each
    out['left'] = left
    return out


# ---------------------------------------------------------------------------
# Making the change: one undo step
# ---------------------------------------------------------------------------
class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))


def make_mesh(face_list):
    """A new mesh from [(points, holes, attrs)] (metres). Returns (mesh, faces that failed)."""
    from core.mesh import Mesh
    mesh = Mesh()
    tol = 1e-7
    verts = {}
    bad = 0

    def vx(q):
        k = (round(q[0] / tol), round(q[1] / tol), round(q[2] / tol))
        if k not in verts:
            verts[k] = VertexWrapper(*q)
        return verts[k]
    for pts, hls, attrs in face_list:
        try:
            outer = [vx(q) for q in pts]
            hs = [[vx(q) for q in h] for h in hls if len(h) >= 3]
            if hs:
                try:
                    f_ = mesh.add_face(outer, hs)
                except TypeError:
                    f_ = mesh.add_face(outer)
                    for h in hs:
                        mesh.add_hole(f_, h)
            else:
                f_ = mesh.add_face(outer)
            if f_ is None:
                bad += 1
                continue
            if attrs:
                try:
                    f_.attrs = dict(attrs)
                except Exception:
                    pass
        except Exception:
            bad += 1
    return mesh, bad


def _edge_ends(e):
    for get in (lambda: (e.v1, e.v2), lambda: (e.a, e.b), lambda: tuple(_items(getattr(e, 'vertices', None)))[:2],
                lambda: (e.start, e.end)):
        try:
            a, b = get()
            pa, pb = _pos(a), _pos(b)
            if pa is not None and pb is not None:
                return pa, pb
        except Exception:
            pass
    return None


def copy_soft_edges(old, new, mp=None):
    """Softened (smooth) edges stay softened on the parts that are kept. mp: where the old
    mesh's points are in the new one (for a part moved into the world)."""
    key = _Keys(1e-7)
    soft = set()
    for e in _items(getattr(old, 'edges', None)):
        if getattr(e, 'soft', False):
            ends = _edge_ends(e)
            if ends:
                if mp is not None:
                    ends = (mp(ends[0]), mp(ends[1]))
                soft.add(frozenset((key(ends[0]), key(ends[1]))))
    if not soft:
        return
    for e in _items(getattr(new, 'edges', None)):
        ends = _edge_ends(e)
        if ends and frozenset((key(ends[0]), key(ends[1]))) in soft:
            try:
                e.soft = True
            except Exception:
                return


def low_relief_command(swaps, removals, adds, ext_changes, renames=()):
    """One undo step. swaps [(group, old mesh, new mesh)], removals [(list, group)],
    adds [(scene, group)], ext_changes [(group, old ext, new ext)], renames [(group, old, new)]."""
    try:
        from core.history import Command
    except Exception:
        Command = object

    class LowReliefCommand(Command):
        def __init__(self):
            self.where = None
            self.organised = False

        def _tidy(self, scene):
            try:
                scene.selection.clear()
            except Exception:
                pass
            try:
                scene.version += 1
            except Exception:
                pass

        def do(self, scene):
            for g, _old, new in swaps:
                g.mesh = new
            where = []
            for lst, g in removals:
                try:
                    i = next(k for k, x in enumerate(lst) if x is g)
                except StopIteration:
                    where.append(None)
                    continue
                del lst[i]
                where.append(i)
            if self.where is None:
                self.where = where
            for sc, g in adds:
                lst = getattr(sc, 'groups', None)
                if isinstance(lst, list):
                    lst.append(g)
                elif hasattr(sc, 'add_group'):
                    sc.add_group(g)
                if not self.organised:
                    _ed3d_organise(sc, g)          # its layer, like the other plugins' groups
            self.organised = True
            for g, _old, new in ext_changes:
                try:
                    g.ext = new
                except Exception:
                    pass
            for g, _old, new in renames:
                try:
                    g.name = new
                except Exception:
                    pass
            self._tidy(scene)

        def undo(self, scene):
            for sc, g in reversed(adds):
                lst = getattr(sc, 'groups', None)
                if isinstance(lst, list):
                    for k, x in enumerate(lst):
                        if x is g:
                            del lst[k]
                            break
                else:
                    for fn in ('remove_group', 'delete_group'):
                        if callable(getattr(sc, fn, None)):
                            try:
                                getattr(sc, fn)(g)
                                break
                            except Exception:
                                pass
            for (lst, g), i in reversed(list(zip(removals, self.where or []))):
                if i is not None:
                    lst.insert(min(i, len(lst)), g)
            for g, old, _new in swaps:
                g.mesh = old
            for g, old, _new in ext_changes:
                try:
                    g.ext = old
                except Exception:
                    pass
            for g, old, _new in renames:
                try:
                    g.name = old
                except Exception:
                    pass
            self._tidy(scene)

    c = LowReliefCommand()
    c.swaps, c.removals, c.adds = swaps, removals, adds
    return c


def board_faces(lo_u, hi_u, lo_z, hi_z, f, t_face, t_back):
    """A flat board (a box) across the cut: u across the building, z up, from t_face to t_back."""
    r = (-f[1], f[0], 0.0)                 # across the building
    def P(u, t, z):
        return (r[0] * u + f[0] * t, r[1] * u + f[1] * t, z)
    a, b = min(t_face, t_back), max(t_face, t_back)
    c = [P(lo_u, a, lo_z), P(hi_u, a, lo_z), P(hi_u, b, lo_z), P(lo_u, b, lo_z),
         P(lo_u, a, hi_z), P(hi_u, a, hi_z), P(hi_u, b, hi_z), P(lo_u, b, hi_z)]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    out = []
    centre = _mul(_add(c[0], c[6]), 0.5)
    for q in quads:
        pts = [c[i] for i in q]
        n = newell(pts)
        mid = tuple(sum(p[i] for p in pts) / 4.0 for i in range(3))
        if _dot(n, _sub(mid, centre)) < 0:
            pts.reverse()
        out.append((pts, [], dict(BOARD_COLOUR)))
    return out


def _new_group(name, mesh=None, kids=None):
    from core.group import Group
    from core.mesh import Mesh
    try:
        g = Group(mesh if mesh is not None else Mesh(), name=name)
    except TypeError:
        g = Group(name)
        g.mesh = mesh if mesh is not None else Mesh()
    try:
        g.name = name
    except Exception:
        pass
    try:
        g.component = False
    except Exception:
        pass
    if kids:
        if hasattr(g, 'adopt'):
            g.adopt(list(kids))
        else:
            g.children = list(kids)
    return g


def _mark(g, rec):
    try:
        ext = getattr(g, 'ext', None)
        if not isinstance(ext, dict):
            g.ext = {}
            ext = g.ext
        ext['ed3d_low_relief'] = dict(rec)
    except Exception:
        pass


def find_parts(scene):
    """{'front': [groups], 'back': [groups]}: the parts a cut made (top-level groups), found by the
    note each one carries - so it works after the model is saved and opened again."""
    out = {'front': [], 'back': []}
    for g in _items(getattr(scene, 'groups', None)):
        ext = getattr(g, 'ext', None)
        rec = ext.get('ed3d_low_relief') if isinstance(ext, dict) else None
        if isinstance(rec, dict) and rec.get('part') in out:
            out[rec['part']].append(g)
    return out


def select_groups(viewport, gs):
    """Selects the groups in the model (so they light up), whichever way this IngeTrazo does it."""
    sc = getattr(viewport, 'scene', None)
    if sc is None:
        return False
    done = False
    for owner in (sc, viewport):
        for fn in ('set_selection', 'select_only', 'select_entities'):
            m = getattr(owner, fn, None)
            if callable(m) and not done:
                try:
                    m(list(gs))
                    done = True
                except Exception:
                    pass
    if not done:
        sel = getattr(sc, 'selection', None)
        try:
            if hasattr(sel, 'clear') and hasattr(sel, 'add'):
                sel.clear()
                for g in gs:
                    sel.add(g)
            elif hasattr(sel, 'clear') and hasattr(sel, 'extend'):
                sel.clear()
                sel.extend(gs)
            else:
                sc.selection = type(sel)(gs) if sel is not None else list(gs)
            done = True
        except Exception:
            return False
    for owner in (sc, viewport):
        for fn in ('notify_selection_changed', 'notify_scene_changed'):
            m = getattr(owner, fn, None)
            if callable(m):
                try:
                    m()
                except Exception:
                    pass
    return done


def hide_groups(viewport, gs, hidden):
    """Hides (or shows) groups the way IngeTrazo's own Edit > Hide does, so it can be undone."""
    gs = [g for g in gs if bool(getattr(g, 'hidden', False)) != bool(hidden)]
    if not gs:
        return
    try:
        from core.history import HideCommand
        viewport.history.execute(HideCommand(gs, bool(hidden)))
    except Exception:
        pass
    for g in gs:
        if bool(getattr(g, 'hidden', False)) != bool(hidden):
            try:
                g.hidden = bool(hidden)
            except Exception:
                pass
    try:
        viewport.scene.version += 1
    except Exception:
        pass
    try:
        viewport.notify_scene_changed()
    except Exception:
        pass


def run_cut(scene, survey, v):
    """Works out every change, building by building when several are cut each on its own.
    Returns (command or None, report dict)."""
    blds, left = survey.buildings()
    if v.get('each', 'each') != 'each' or len(blds) < 2:
        sv = survey.sub([t for b in blds for t in b]) if left else survey
        parts, rep = _cut_parts(scene, sv, v)
        rep['left'] = [str(getattr(t, 'name', '') or 'a group') for t in left]
        rep['buildings'] = 1
        return (low_relief_command(*parts) if parts else None), rep
    total = None
    allp = [[], [], [], [], []]
    skipped = []
    done = 0
    for b in blds:
        name = survey.building_name(b)
        try:
            parts, rep = _cut_parts(scene, survey.sub(b), v)
        except ValueError as e:
            skipped.append("%s: %s" % (name, e))
            continue
        done += 1
        if parts:
            for i in range(5):
                allp[i] += list(parts[i])
        if total is None:
            total = rep
        else:
            for k_, val in rep.items():
                if isinstance(val, (int, float)) and not isinstance(val, bool) and k_ in total:
                    total[k_] += val
                elif isinstance(val, list) and k_ in total:
                    total[k_] = total[k_] + val
    if total is None:
        raise ValueError("No building could be cut:\n" + "\n".join(skipped))
    total['skipped'] = skipped
    total['left'] = [str(getattr(t, 'name', '') or 'a group') for t in left]
    total['buildings'] = done
    if not any(allp[:3]):
        return None, total
    return low_relief_command(*allp), total


def _cut_parts(scene, survey, v):
    """One building (or all on one line). Returns ((swaps, removals, adds, ext_changes, renames)
    or None, report dict).
    Keeping both: the front stays in the building's own groups (its name gets ' - front part'),
    and the back goes into a new group of its own, '<name> - back part', each part in its own
    group inside it - so either half can be picked, hidden or printed on its own."""
    plan = plan_cut(survey, v)
    cuts, f = plan['cuts'], plan['f']
    both = v['keep'] == 'both'
    cap_attrs = dict(GREY) if v['cap_colour'] == 'grey' else None
    rep = {'cut': 0, 'removed': 0, 'kept': 0, 'caps': 0, 'opened': 0, 'bad': 0, 'repeat': [], 'plan': plan,
           'moved': 0, 'slivers': 0, 'boards': 0}
    min_keep = max(0.0, float(v.get('sliver_mm', 0.0) or 0.0)) * SCALE if v.get('slivers') else 0.0
    swaps, alive, gone = [], {}, set()
    empties = []
    back_kids = {}                              # id(top) -> [new groups for the back part]
    cap_pts = {c[1]: [] for c in cuts}          # side -> world points on the cuts (for the board)
    for lf in survey.leaves:
        nl, o = local_t(lf.m, f)
        nlen = _len(nl) or 1.0
        faces = _faces_of(lf.mesh)

        def tfun(q, nl=nl, o=o):
            return q[0] * nl[0] + q[1] * nl[1] + q[2] * nl[2] + o
        res = cut_faces(faces, tfun, _mul(nl, 1.0 / nlen), cuts, v['fill'], cap_attrs, min_keep)
        rep['slivers'] += res.get('slivers', 0)
        back = res['parts'].get('down', []) if both else []
        stays = res['parts'].get('up', []) if both else res['faces']
        if not res['changed'] and not back:
            alive[id(lf.g)] = True
            rep['kept'] += 1
            continue
        shared = survey.mesh_users.get(id(lf.mesh), 1) > 1 and bool(getattr(lf.g, 'component', False))
        if lf.repeat or (shared and res['kept_any']):
            # a component used more than once: changing it here would change every copy
            alive[id(lf.g)] = True
            rep['repeat'].append(str(getattr(lf.g, 'name', '') or 'a part'))
            continue
        rep['opened'] += res['opened']
        rep['caps'] += res['caps']
        if v.get('board'):
            for side, outer in res['cap_list']:
                cap_pts[side] += [_wmap(lf.m, q) for q in outer]
        if back:
            # the back part: its own group, placed in the world where it was
            mp = lambda q, m=lf.m: _wmap(m, q)
            wf = [([mp(q) for q in pts], [[mp(q) for q in h] for h in hs], attrs) for pts, hs, attrs in back]
            mesh, bad = make_mesh(wf)
            rep['bad'] += bad
            copy_soft_edges(lf.mesh, mesh, mp)
            back_kids.setdefault(id(lf.top), []).append(_new_group(str(getattr(lf.g, 'name', '') or 'Part'), mesh))
            rep['moved'] += 1
        if not stays:
            gone.add(id(lf.g))
            if not back:
                rep['removed'] += 1
            if not shared:
                empties.append(lf)
            continue
        if res['changed'] or back:
            mesh, bad = make_mesh(stays)
            rep['bad'] += bad
            copy_soft_edges(lf.mesh, mesh)
            swaps.append((lf.g, lf.mesh, mesh))
            rep['cut'] += 1
        alive[id(lf.g)] = True
    # groups with nothing left in them (and nothing left in the groups inside them) go
    kids = {}
    for g, owner, attr, top, parent in survey.allg:
        if parent is not None:
            kids.setdefault(id(parent), []).append(g)
    memo = {}

    def has_alive(g, depth=0):
        """Is anything left in this group (or the groups inside it)? Groups that were empty to
        start with are left alone."""
        k = id(g)
        if k in memo:
            return memo[k]
        if k in alive or depth > 60:
            res_ = True
        else:
            ks = kids.get(k, [])
            if k not in gone and not ks:
                res_ = True
            else:
                res_ = any(has_alive(c, depth + 1) for c in ks)
        memo[k] = res_
        return res_
    removals = []
    from core.mesh import Mesh as _Mesh
    for lf in empties:
        swaps.append((lf.g, lf.mesh, _Mesh()))          # its faces go (and the group too, below)
    for g, owner, attr, top, parent in survey.allg:
        if has_alive(g):
            continue
        if parent is not None and not has_alive(parent):
            continue                                     # goes with the group it's in
        lst = getattr(owner, attr, None)
        if isinstance(lst, list):
            removals.append((lst, g))
    if not any(has_alive(t) for t in survey.tops) and not back_kids:
        raise ValueError("Everything would be cut away - check which side is the front, and the depths.")
    rec = {'keep': v['keep'], 'front': v['front'], 'depth_a': v['depth_a'], 'depth_b': v['depth_b'],
           'version': VERSION}
    adds, ext_changes, renames = [], [], []
    front_part = 'back' if v['keep'] == 'back' else 'front'
    with_parts = set(id(lf.top) for lf in survey.leaves)
    for t in survey.tops:
        name = str(getattr(t, 'name', '') or 'Building')
        if has_alive(t) and id(t) in with_parts:
            old = getattr(t, 'ext', None)
            new = dict(old) if isinstance(old, dict) else {}
            new['ed3d_low_relief'] = dict(rec, part=front_part)
            ext_changes.append((t, old, new))
            if both:
                renames.append((t, name, name + " - front part"))
        if back_kids.get(id(t)):
            bg = _new_group(name + " - back part", None, back_kids[id(t)])
            _mark(bg, dict(rec, part='back'))
            adds.append((scene, bg))
    if v.get('board'):
        r = (-f[1], f[0], 0.0)
        th = v['board_thick'] * SCALE
        nb = 0
        for c, side in cuts:
            pts = cap_pts.get(side) or []
            if len(pts) < 3:
                continue
            us = [p[0] * r[0] + p[1] * r[1] for p in pts]
            zs = [p[2] for p in pts]
            back_t = c - th if side == 'up' else c + th
            mesh, bad = make_mesh(board_faces(min(us), max(us), min(zs), max(zs), f, c, back_t))
            part = 'front' if side == 'up' else 'back'
            g = _new_group("Low relief backing board" + (" (%s part)" % part if both else ""), mesh)
            _mark(g, dict(rec, part=part))
            adds.append((scene, g))
            nb += 1
        rep['boards'] = nb
    if not swaps and not removals and not adds:
        return None, rep
    return (swaps, removals, adds, ext_changes, renames), rep


# --- Eddy's 3D plugins: hover help and remembered window places (begin) ---
import os
# The same in each of the plugins. Every box, tick and button gets a pop-up note when
# you hover over it, and each window opens where (and at the size) you last left it.
EDDY_PLACES_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_low_relief_windows.json")
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


# ---------------------------------------------------------------------------
# Settings and presets
# ---------------------------------------------------------------------------
def _ui_settings():
    try:
        with open(UI_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _ui_settings_save(**kw):
    d = _ui_settings()
    d.update(kw)
    try:
        with open(UI_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)
    except Exception:
        pass


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


def delete_preset(name):
    try:
        os.remove(os.path.join(PRESET_DIR, _safe_name(name) + ".json"))
    except Exception:
        pass


def scale_hint(mm):
    return ", ".join("%s %.1f mm" % (nm, mm / s) for nm, s in SCALES_SHOWN)


INFO_TEXT = (
    "<b>%s</b> (version %s)<br><br>"
    "Cuts a whole building down to low relief. Build the building as usual first - Floor plan, Openings, "
    "Frame, Windows, Doors, Chimneys, Roof, Bricks, Gutters, Pipes, Colours - then cut it here, just "
    "before Scale Studio.<br><br>"
    "<b>Keep</b>: the front (a low relief building), the back, or both with the middle taken out.<br>"
    "<b>A</b> is how deep the front part is, measured back from the front of the walls (or from the "
    "furthest part out). <b>B</b> is the same for the back part.<br><br>"
    "Every part that crosses the cut is cut there and stays in its own group, with its name and colour, so "
    "Show / Hide and Scale Studio's pieces work as before. Parts wholly in what's taken away go. The cut "
    "faces are filled in so each piece is still a solid, ready to print. Thin sheets (glass, tin) are just "
    "cut - they have nothing to fill.<br><br>"
    "Select the building first (any part of it will do), or nothing for the whole model. The preview shows "
    "the cut in red and what goes shaded. <b>Ctrl+Z</b> puts it all back.<br><br>"
    "<b>Do it last</b>: if you build windows, doors or bricks again after cutting, those plugins put back the "
    "whole wall they started from. Undo the cut, change the building, then cut again.<br><br>"
    "Sizes are real-world mm (Scale Studio takes them down to your scale). Ctrl+Alt+Shift+L."
    % (PLUGIN_NAME, VERSION))


# ---------------------------------------------------------------------------
# The preview: the building from above and from the side, with the cuts
# ---------------------------------------------------------------------------
class Preview(QWidget):
    """The building drawn solid, in its own colours: from above (front at the bottom) and from the
    side (front on the right). The cuts in red, what's taken away dimmed and hatched, each part
    labelled."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 420)
        self.survey = None
        self.v = dict(DEFAULTS)
        self.plan = None
        self.error = ""
        self.message = "Reading the building..."
        self._cache = {}

    def set_state(self, survey, v, plan, error):
        if survey is not self.survey:
            self._cache = {}
        self.survey, self.v, self.plan, self.error = survey, dict(v), plan, error
        self.update()

    @staticmethod
    def _project(kind, f, q):
        r = (-f[1], f[0])
        t = q[0] * f[0] + q[1] * f[1]
        if kind == 'above':
            return (q[0] * r[0] + q[1] * r[1], t)
        return (t, -q[2])

    IMG_W, IMG_H = 900, 560

    def _pane(self, kind, f):
        """(picture, transform from plan units to the picture, bounds) - drawn once for each view
        and front direction, at a fixed size, and scaled to fit the window."""
        from PySide6.QtGui import QImage, QPainter, QColor, QPen, QPolygonF, QTransform
        from PySide6.QtCore import Qt, QPointF, QRectF
        w, h = self.IMG_W, self.IMG_H
        key = (kind, round(f[0], 6), round(f[1], 6))
        if key in self._cache:
            return self._cache[key]
        sv = self.survey
        lo_x = hi_x = lo_y = hi_y = None
        for wp, _c, _n in sv.polys:
            for q in wp:
                x, y = self._project(kind, f, q)
                if lo_x is None:
                    lo_x = hi_x = x
                    lo_y = hi_y = y
                else:
                    lo_x, hi_x, lo_y, hi_y = min(lo_x, x), max(hi_x, x), min(lo_y, y), max(hi_y, y)
        if lo_x is None:
            return None
        br = QRectF(lo_x, lo_y, max(hi_x - lo_x, 1e-6), max(hi_y - lo_y, 1e-6))
        k = min((w - 40) / br.width(), (h - 40) / br.height())
        tr = QTransform()
        tr.translate(w / 2.0, h / 2.0)
        tr.scale(k, k)
        tr.translate(-br.center().x(), -br.center().y())
        img = QImage(int(w), int(h), QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        p.setTransform(tr)
        r = (-f[1], f[0], 0.0)
        look = (0.0, 0.0, 1.0) if kind == 'above' else (-r[0], -r[1], 0.0)   # towards the viewer
        light = _norm((0.35 * f[0] - 0.25 * r[0], 0.35 * f[1] - 0.25 * r[1], 0.9))
        items = []
        for wp, col, n in sv.polys:
            facing = _dot(n, look)
            if facing < 0.02:
                continue                                   # turned away: hidden
            c = tuple(sum(q[i] for q in wp) / len(wp) for i in range(3))
            items.append((_dot(c, look), wp, col, n))
        items.sort(key=lambda e: e[0])                     # the far ones first
        edge = QPen(QColor(40, 40, 40, 70))
        edge.setCosmetic(True)
        edge.setWidthF(0.6)
        p.setPen(edge)
        for _d, wp, col, n in items:
            sh = 0.62 + 0.38 * abs(_dot(n, light))
            p.setBrush(QColor(*[max(0, min(255, int(255 * c_ * sh))) for c_ in col]))
            p.drawPolygon(QPolygonF([QPointF(*self._project(kind, f, q)) for q in wp]))
        p.end()
        out = (img, tr, br)
        self._cache[key] = out
        return out

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush
        from PySide6.QtCore import Qt, QRectF, QPointF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 246))
        if self.survey is None or self.survey.empty():
            p.setPen(QColor(110, 110, 110))
            p.drawText(self.rect().adjusted(12, 12, -12, -12), Qt.AlignCenter | Qt.TextWordWrap,
                       self.message if self.survey is None else
                       "Nothing to cut. Build the building first, then select it (or nothing for the whole model).")
            p.end()
            return
        f = front_vector(self.v['front'])
        view = self.v.get('view', 'both')
        W, H = self.width(), self.height()
        kinds = [k for k in ('above', 'side') if view in ('both', k)]
        ph = (H - 44) / len(kinds)
        keep = self.v['keep']
        bold = QFont(p.font())
        bold.setBold(True)
        for i, kind in enumerate(kinds):
            top = 4 + i * ph
            p.setFont(bold)
            p.setPen(QColor(60, 60, 60))
            p.drawText(QRectF(10, top, W - 20, 16), Qt.AlignLeft | Qt.AlignVCenter,
                       "From above" if kind == 'above' else "From the side")
            p.setPen(QColor(40, 90, 160))
            p.drawText(QRectF(10, top, W - 20, 16), Qt.AlignRight | Qt.AlignVCenter,
                       "front at the bottom" if kind == 'above' else "front on the right  \u2192")
            p.setFont(QFont())
            box = QRectF(10, top + 18, W - 20, ph - 22)
            pane = self._pane(kind, f)
            if pane is None:
                continue
            img, tr_img, br = pane
            sc_ = min(box.width() / img.width(), box.height() / img.height())
            ox = box.left() + (box.width() - img.width() * sc_) / 2.0
            oy = box.top() + (box.height() - img.height() * sc_) / 2.0
            p.save()
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            p.drawImage(QRectF(ox, oy, img.width() * sc_, img.height() * sc_), img)
            p.restore()
            from PySide6.QtGui import QTransform
            tr = tr_img * QTransform.fromScale(sc_, sc_) * QTransform.fromTranslate(ox, oy)
            p.save()
            p.setTransform(tr)
            spans = []           # (from, to, what) in t - for the labels (one building)
            plans = []           # (plan, lo u, hi u) - each building its own when cut on its own
            if self.plan:
                if self.plan.get('each'):
                    pad = 0.01 * br.width()
                    plans = [(pl, lo_u - pad, hi_u + pad) for pl, _e, lo_u, hi_u, _n, _t in self.plan['each']
                             if pl is not None]
                else:
                    plans = [(self.plan, br.left() - 1, br.right() + 1)]
            for pl, ulo, uhi in plans:
                t1, t2 = pl['t1'], pl['t2']
                lo, hi = pl['frame']['lo'], pl['frame']['hi']
                if keep == 'front':
                    sp_ = [(lo - 1, t1, 'gone'), (t1, hi + 1, 'front')]
                elif keep == 'back':
                    sp_ = [(lo - 1, t2, 'back'), (t2, hi + 1, 'gone')]
                else:
                    sp_ = [(lo - 1, t2, 'back'), (t2, t1, 'gone'), (t1, hi + 1, 'front')]
                if len(plans) == 1:
                    spans = sp_
                for a, b, what in sp_:
                    if what != 'gone':
                        continue
                    if kind == 'above':
                        a_, b_ = max(a, br.top() - 1), min(b, br.bottom() + 1)
                        rect = QRectF(ulo, a_, uhi - ulo, max(0.0, b_ - a_))
                    else:
                        rect = QRectF(a, br.top() - 1, b - a, br.height() + 2)
                    p.setPen(Qt.NoPen)
                    p.setBrush(QBrush(QColor(250, 250, 246, 150 if len(plans) == 1 or kind == 'above' else 70)))
                    p.drawRect(rect)
                    p.setBrush(QBrush(QColor(200, 60, 50, 90), Qt.BDiagPattern))  # and hatched
                    p.drawRect(rect)
                cp = QPen(QColor(200, 30, 30))
                cp.setCosmetic(True)
                cp.setWidthF(2.0)
                cp.setStyle(Qt.DashLine)
                p.setPen(cp)
                for c, _s in pl['cuts']:
                    if kind == 'above':
                        p.drawLine(QPointF(ulo, c), QPointF(uhi, c))
                    else:
                        p.drawLine(QPointF(c, br.top() - 0.3), QPointF(c, br.bottom() + 0.3))
            p.restore()
            # labels on each part, in screen terms
            def at(x, y, tr=tr):
                return tr.map(QPointF(x, y))
            p.setFont(bold)
            for a, b, what in spans:
                a, b = max(a, br.top() if kind == 'above' else br.left()), \
                    min(b, br.bottom() if kind == 'above' else br.right())
                if b <= a:
                    continue
                mid = (a + b) / 2.0
                q = at(br.center().x(), mid) if kind == 'above' else at(mid, br.top())
                if kind == 'above':
                    txt = {'front': "FRONT PART - kept", 'back': "BACK PART - kept", 'gone': "taken away"}[what]
                else:
                    txt = {'front': "front", 'back': "back", 'gone': "gone"}[what]
                    q = QPointF(q.x(), q.y() - 4)
                col = QColor(160, 40, 30) if what == 'gone' else QColor(30, 110, 40)
                fm = p.fontMetrics()
                tw = fm.horizontalAdvance(txt) + 8
                if kind == 'side' and abs(at(b, 0).x() - at(a, 0).x()) < tw:
                    continue                                  # no room for it
                rect = QRectF(q.x() - tw / 2.0, q.y() - 9, tw, 16)
                if kind == 'side':
                    rect.moveTop(max(box.top(), q.y() - 16))
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 255, 255, 215))
                p.drawRoundedRect(rect, 3, 3)
                p.setPen(col)
                p.drawText(rect, Qt.AlignCenter, txt)
            # A and B by their cuts
            if plans:
                p.setPen(QColor(200, 30, 30))
                for pl, ulo, uhi in plans:
                    for c, sd in pl['cuts']:
                        lab = "A" if sd == 'up' else "B"
                        if kind == 'above':
                            q = at(min(uhi, br.right()), c)
                            p.drawText(QPointF(q.x() + 5, q.y() + 5), lab)
                        elif len(plans) == 1:
                            q = at(c, br.bottom())
                            p.drawText(QPointF(q.x() - 4, min(q.y() + 14, box.bottom() + 2)), lab)
            if len(plans) > 1 and kind == 'above':
                # each building's name, in its kept part
                for (pl, ulo, uhi), e in zip(plans, [x for x in self.plan['each'] if x[0] is not None]):
                    t_ = pl['t1'] if keep != 'back' else pl['t2']
                    q = at((ulo + uhi) / 2.0, t_)
                    txt = e[4][:28]
                    fm = p.fontMetrics()
                    tw = fm.horizontalAdvance(txt) + 8
                    rect = QRectF(q.x() - tw / 2.0, q.y() + (6 if keep != 'back' else -22), tw, 16)
                    p.setPen(Qt.NoPen)
                    p.setBrush(QColor(255, 255, 255, 215))
                    p.drawRoundedRect(rect, 3, 3)
                    p.setPen(QColor(30, 110, 40))
                    p.drawText(rect, Qt.AlignCenter, txt)
            p.setFont(QFont())
        if self.error:
            p.setPen(QColor(170, 30, 30))
            p.drawText(QRectF(12, H - 40, W - 24, 36), Qt.AlignLeft | Qt.TextWordWrap, self.error)
        p.end()


class KeyDrawing(QWidget):
    """What A and B are, seen from above."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(340, 400)

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont
        from PySide6.QtCore import QPointF, QRectF, Qt
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 246))
        W = self.width()
        x0, x1, y0, y1 = 50, W - 50, 60, 330
        p.setPen(QColor(60, 60, 60))
        p.drawText(QPointF(12, 22), "From above - the front of the building at the bottom")
        # what goes in the middle (keeping both)
        ya, yb = y1 - 95, y0 + 85
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(200, 70, 60, 45))
        p.drawRect(QRectF(x0 - 10, yb, x1 - x0 + 20, ya - yb))
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(60, 60, 60), 2.0))
        p.drawRect(QRectF(x0, y0, x1 - x0, y1 - y0))                 # the walls
        p.setPen(QPen(QColor(60, 60, 60), 1.0))
        p.drawRect(QRectF(x0 + 10, y0 + 10, x1 - x0 - 20, y1 - y0 - 20))
        p.drawRect(QRectF(x0 + 30, y1 + 1, 80, 8))                   # a plinth / step out in front
        dp = QPen(QColor(200, 30, 30), 2.0)
        dp.setStyle(Qt.DashLine)
        p.setPen(dp)
        p.drawLine(QPointF(x0 - 20, ya), QPointF(x1 + 20, ya))
        p.drawLine(QPointF(x0 - 20, yb), QPointF(x1 + 20, yb))
        p.setPen(QPen(QColor(200, 30, 30), 1.2))
        xa = x1 + 12
        p.drawLine(QPointF(xa, ya), QPointF(xa, y1))
        p.drawText(QPointF(xa + 5, (ya + y1) / 2 + 4), "A")
        xb = x0 - 12
        p.drawLine(QPointF(xb, y0), QPointF(xb, yb))
        p.drawText(QPointF(xb - 14, (y0 + yb) / 2 + 4), "B")
        p.setPen(QColor(40, 90, 160))
        p.drawText(QRectF(x0, y1 + 12, x1 - x0, 16), Qt.AlignCenter, "FRONT")
        p.drawText(QRectF(x0, y0 - 18, x1 - x0, 16), Qt.AlignCenter, "BACK")
        p.setPen(QColor(90, 90, 90))
        f_ = QFont(p.font())
        f_.setPointSize(max(7, f_.pointSize() - 1))
        p.setFont(f_)
        p.drawText(QRectF(x0 + 14, (ya + yb) / 2 - 20, x1 - x0 - 28, 40), Qt.AlignCenter | Qt.TextWordWrap,
                   "Taken away when keeping both (keeping the front, everything behind A goes)")
        p.drawText(QRectF(12, y1 + 34, W - 24, 70), Qt.AlignLeft | Qt.TextWordWrap,
                   "A: how deep the front part is, measured back from the front of the walls (the plinth and "
                   "anything else sticking out in front stays on). B: the same from the back walls. "
                   "Real-world mm - 1524 mm is 20 mm in OO.")
        p.end()


# ---------------------------------------------------------------------------
# The window
# ---------------------------------------------------------------------------
class LowReliefDialog(QDialog):
    def __init__(self, cur, viewport, tool):
        super().__init__(viewport)
        from PySide6.QtCore import QTimer
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.user_presets = load_presets()
        self.survey = None
        self._sel_key = None
        self._busy = False
        self._loading = True              # (until the values are put in)
        lay = QVBoxLayout(self)

        self.info_box = QWidget()
        ib = QVBoxLayout(self.info_box)
        ib.setContentsMargins(0, 0, 0, 0)
        self.lbl_info = QLabel(INFO_TEXT)
        self.lbl_info.setWordWrap(True)
        ib.addWidget(self.lbl_info)
        self.info_box.setVisible(False)
        lay.addWidget(self.info_box)

        row = QHBoxLayout()
        lay.addLayout(row)
        self.preview = Preview()
        self.left = QTabWidget()
        self.left.addTab(self.preview, "Preview")
        key_scroll = QScrollArea()
        key_scroll.setWidgetResizable(True)
        key_scroll.setWidget(KeyDrawing())
        self.left.addTab(key_scroll, "Key (A, B)")
        self.left.setTabToolTip(0, "The building from above and from the side: the cuts in red, what's taken "
                                   "away shaded.")
        self.left.setTabToolTip(1, "What A and B are.")
        row.addWidget(self.left, 1)
        self.tabs = QTabWidget()
        row.addWidget(self.tabs, 1)

        # -- Start here
        ps = QWidget()
        fs = QVBoxLayout(ps)
        steps = QLabel(
            "<b>1.</b> Build the whole building first, as usual - Floor plan to Colours. Low relief is the "
            "last step before Scale & print.<br><br>"
            "<b>2.</b> Select the building (click any part of it), or nothing for the whole model.<br><br>"
            "<b>3.</b> On the <b>Cut</b> page: keep the front, the back or both, say which side is the front, "
            "and how deep (A, B). The preview shows the cut.<br><br>"
            "<b>4.</b> On the <b>Finish</b> page: fill in the cut faces (on, so every piece is solid) and a "
            "backing board if you want one.<br><br>"
            "<b>5.</b> Click <b>Cut the building</b>. Ctrl+Z puts it all back.<br><br>"
            "<b>6.</b> Then Scale Studio, to scale it and lay the pieces on the print bed.")
        steps.setWordWrap(True)
        fs.addWidget(steps)
        self.lbl_sel = QLabel("")
        self.lbl_sel.setWordWrap(True)
        self.lbl_sel.setStyleSheet("color: #2a5a9a;")
        fs.addWidget(self.lbl_sel)
        b_go = QPushButton("Next: the Cut page")
        b_go.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        fs.addWidget(b_go)
        b_scale = QPushButton("Then: open Scale Studio")
        b_scale.setToolTip("Closes this window and opens 3D Scale Studio, to scale the building and lay its "
                           "pieces on the print bed.")
        b_scale.clicked.connect(self.open_scale_studio)
        fs.addWidget(b_scale)
        fs.addStretch(1)
        self.tabs.addTab(ps, "Start here")

        # -- Cut
        pc = QWidget()
        fc = QFormLayout(pc)
        self.cb_keep = QComboBox()
        for lab_, k_ in KEEPS:
            self.cb_keep.addItem(lab_, k_)
        fc.addRow("Keep", self.cb_keep)
        self.cb_front = QComboBox()
        for lab_, a_ in FRONTS:
            self.cb_front.addItem(lab_, a_)
        fc.addRow("The front faces", self.cb_front)
        self.b_pick = QPushButton("Use the face I've picked")
        self.b_pick.setToolTip("Click a face on the front wall (double-click into the building to get at it), "
                               "then this: the front is the way that face looks - for a building that isn't "
                               "square to the model.")
        self.b_pick.clicked.connect(self.use_picked_face)
        fc.addRow("", self.b_pick)
        self.cb_measure = QComboBox()
        for lab_, k_ in MEASURES:
            self.cb_measure.addItem(lab_, k_)
        fc.addRow("Measure A and B from", self.cb_measure)
        self.cb_each = QComboBox()
        for lab_, k_ in EACH:
            self.cb_each.addItem(lab_, k_)
        self.cb_each.setToolTip("With more than one building picked (or nothing picked and several in the model): "
                                "each cut on its own, A and B from its own front and back walls - or one cut line "
                                "for them all, for a terrace that should stay flush.")
        fc.addRow("Several buildings", self.cb_each)
        self.sp = {}

        def spin(key, label, tip, lo=10.0, hi=100000.0):
            s = QDoubleSpinBox()
            s.setDecimals(0)
            s.setRange(lo, hi)
            s.setSingleStep(25.0)
            s.setSuffix(" mm")
            s.setKeyboardTracking(False)
            s.setToolTip(tip)
            lab = QLabel(label)
            lab.setToolTip(tip)
            self.sp[key] = (s, lab)
            s.valueChanged.connect(self.changed)
            return lab, s
        fc.addRow(*spin('depth_a', "A   Front part depth",
                        "How deep the front part is, real-world mm, back from the front of the walls. "
                        "1524 mm = 20 mm in OO, 1480 mm = 10 mm in N."))
        self.lbl_hint_a = QLabel()
        self.lbl_hint_a.setStyleSheet("color: gray;")
        fc.addRow("", self.lbl_hint_a)
        fc.addRow(*spin('depth_b', "B   Back part depth",
                        "How deep the back part is, real-world mm, in from the back of the walls."))
        self.lbl_hint_b = QLabel()
        self.lbl_hint_b.setStyleSheet("color: gray;")
        fc.addRow("", self.lbl_hint_b)
        self.cb_slivers = QCheckBox("Throw away slivers thinner than")
        self.cb_slivers.setToolTip("Where the cut only just catches a part (a rafter end, a tile, a gutter bracket) "
                                   "it leaves a sliver too thin to print. Any piece the cut leaves thinner than "
                                   "this, front to back, is thrown away. Pieces the cut doesn't touch are never "
                                   "thrown away, however thin (glass, window frames).")
        lab_s, s_s = spin('sliver_mm', "", self.cb_slivers.toolTip(), lo=1.0, hi=2000.0)
        s_s.setSingleStep(10.0)
        fc.addRow(self.cb_slivers, s_s)
        self.lbl_hint_s = QLabel()
        self.lbl_hint_s.setStyleSheet("color: gray;")
        fc.addRow("", self.lbl_hint_s)
        self.cb_slivers.toggled.connect(self.changed)
        self.cb_view = QComboBox()
        for lab_, k_ in (("From above and from the side", 'both'), ("From above", 'above'),
                         ("From the side", 'side')):
            self.cb_view.addItem(lab_, k_)
        fc.addRow("Preview", self.cb_view)
        self.lbl_size = QLabel()
        self.lbl_size.setWordWrap(True)
        self.lbl_size.setStyleSheet("color: gray;")
        fc.addRow(self.lbl_size)
        for w_ in (self.cb_keep, self.cb_front, self.cb_measure, self.cb_view, self.cb_each):
            w_.currentIndexChanged.connect(self.changed)
        self.tabs.addTab(pc, "Cut")

        # -- Finish
        pf = QWidget()
        ff = QFormLayout(pf)
        self.cb_fill = QCheckBox("Fill in the cut faces (every piece stays a solid, ready to print)")
        ff.addRow(self.cb_fill)
        self.cb_cap = QComboBox()
        for lab_, k_ in CAP_COLOURS:
            self.cb_cap.addItem(lab_, k_)
        ff.addRow("Colour of the cut faces", self.cb_cap)
        self.cb_board = QCheckBox("Backing board across the back of the cut")
        self.cb_board.setToolTip("A flat board behind the cut, as wide and tall as the cut, so the low relief "
                                 "has a back to glue to the backscene and holds together. Its own group.")
        ff.addRow(self.cb_board)
        lab_t, s_t = spin('board_thick', "Board thickness", "How thick the backing board is, real-world mm. "
                          "152 mm = 2 mm in OO.", lo=10.0, hi=2000.0)
        ff.addRow(lab_t, s_t)
        nf = QLabel("Thin sheets (glass, tin, card) are cut but not filled - they have no inside. "
                    "Anything built more than once from the same part (a copied component) is left whole, "
                    "and the report says which.")
        nf.setWordWrap(True)
        nf.setStyleSheet("color: gray;")
        ff.addRow(nf)
        self.cb_fill.toggled.connect(self.changed)
        self.cb_board.toggled.connect(self.changed)
        self.cb_cap.currentIndexChanged.connect(self.changed)
        self.lbl_report = QLabel()
        self.lbl_report.setWordWrap(True)
        ff.addRow(self.lbl_report)
        hp = QLabel("<b>Printing one part at a time</b> (after cutting). Keeping both, the back is its own "
                    "group - '... - back part' - and the front '... - front part'.")
        hp.setWordWrap(True)
        ff.addRow(hp)
        self.part_buttons = []
        for which, word in (('front', "front"), ('back', "back")):
            row_ = QHBoxLayout()
            b1 = QPushButton("Pick the %s part" % word)
            b1.setToolTip("Selects the %s part (all its groups), so it's the one that's worked on next." % word)
            b1.clicked.connect(lambda _=False, w=which: self.pick_part(w))
            b2 = QPushButton("Show only the %s" % word)
            b2.setToolTip("Hides the other part, so you see just the %s (Show both brings it back)." % word)
            b2.clicked.connect(lambda _=False, w=which: self.show_only(w))
            b3 = QPushButton("%s part to Scale Studio" % word.capitalize())
            b3.setToolTip("Picks the %s part, hides the other, and opens Scale Studio to lay it on the "
                          "print bed." % word)
            b3.clicked.connect(lambda _=False, w=which: self.to_scale_studio(w))
            for b_ in (b1, b2, b3):
                row_.addWidget(b_)
                self.part_buttons.append(b_)
            ff.addRow(row_)
        b_both = QPushButton("Show both parts")
        b_both.clicked.connect(lambda: self.show_only(None))
        ff.addRow(b_both)
        self.tabs.addTab(pf, "Finish")

        # -- presets
        prow = QHBoxLayout()
        prow.addWidget(QLabel("Preset:"))
        self.cb_preset = QComboBox()
        prow.addWidget(self.cb_preset, 1)
        b_up = QPushButton("▲")
        b_up.setToolTip("Moves the preset you have open up the list, so you can put your presets in your own order.")
        b_dn = QPushButton("▼")
        b_dn.setToolTip("Moves the preset you have open down the list.")
        for b_ in (b_up, b_dn):
            b_.setFixedWidth(28)
            prow.addWidget(b_)
        b_up.clicked.connect(lambda: self.move_preset(-1))
        b_dn.clicked.connect(lambda: self.move_preset(1))
        b_save = QPushButton("Save")
        b_saveas = QPushButton("Save as...")
        b_del = QPushButton("Delete")
        b_dir = QPushButton("Folder")
        for b in (b_save, b_saveas, b_del, b_dir):
            prow.addWidget(b)
        b_save.clicked.connect(self.save_current)
        b_saveas.clicked.connect(self.save_as)
        b_del.clicked.connect(self.delete_current)
        b_dir.clicked.connect(self.open_folder)
        self.cb_preset.activated.connect(self.preset_picked)
        lay.addLayout(prow)

        brow = QHBoxLayout()
        self.b_cut = QPushButton("Cut the building")
        self.b_cut.setDefault(True)
        f_ = self.b_cut.font()
        f_.setBold(True)
        self.b_cut.setFont(f_)
        self.b_cut.clicked.connect(self.do_cut)
        self.b_read = QPushButton("Read the building again")
        self.b_read.clicked.connect(lambda: self.read_building(force=True))
        b_info = QPushButton("Info")
        b_info.setCheckable(True)
        b_info.toggled.connect(self.info_box.setVisible)
        b_close = QPushButton("Close")
        b_close.clicked.connect(self.close)
        brow.addWidget(self.b_cut)
        brow.addWidget(self.b_read)
        brow.addStretch(1)
        self.cb_lasttab = QCheckBox("Open at the last page used")
        self.cb_lasttab.setToolTip("Ticked, the window opens at the page (Start here, Cut, Finish) you had open "
                                   "last time.")
        brow.addWidget(self.cb_lasttab)
        brow.addWidget(b_info)
        brow.addWidget(b_close)
        lay.addLayout(brow)

        st = _ui_settings()
        self.cb_lasttab.setChecked(bool(st.get('last_tab_on', True)))
        self.cb_lasttab.toggled.connect(lambda on: _ui_settings_save(last_tab_on=bool(on)))
        if self.cb_lasttab.isChecked():
            try:
                self.tabs.setCurrentIndex(int(st.get('last_tab', 0)))
            except Exception:
                pass
        self.tabs.currentChanged.connect(lambda i: _ui_settings_save(last_tab=int(i)))
        self.fill_presets()
        self.set_values(cur)
        self.resize(980, 640)
        self.timer = QTimer(self)
        self.timer.setInterval(800)
        self.timer.timeout.connect(self.watch_selection)
        self.timer.start()
        QTimer.singleShot(50, lambda: self.read_building(force=True))

    # -- values
    def values(self):
        v = dict(DEFAULTS)
        v['keep'] = self.cb_keep.currentData()
        v['front'] = float(self.cb_front.currentData())
        v['measure'] = self.cb_measure.currentData()
        for k in SIZE_KEYS:
            v[k] = float(self.sp[k][0].value())
        v['fill'] = self.cb_fill.isChecked()
        v['cap_colour'] = self.cb_cap.currentData()
        v['board'] = self.cb_board.isChecked()
        v['view'] = self.cb_view.currentData()
        v['each'] = self.cb_each.currentData() or 'each'
        v['slivers'] = self.cb_slivers.isChecked()
        return v

    def _set_combo(self, cb, value):
        for i in range(cb.count()):
            d = cb.itemData(i)
            if d == value or (isinstance(d, float) and isinstance(value, (int, float)) and abs(d - value) < 1e-6):
                cb.setCurrentIndex(i)
                return True
        return False

    def _front_item(self, angle):
        if not self._set_combo(self.cb_front, angle):
            # a front picked from a face: its own entry
            for i in range(self.cb_front.count() - 1, len(FRONTS) - 1, -1):
                self.cb_front.removeItem(i)
            self.cb_front.addItem("The face I picked (%.0f degrees)" % (angle % 360.0), float(angle))
            self.cb_front.setCurrentIndex(self.cb_front.count() - 1)

    def set_values(self, v):
        self._loading = True
        try:
            full = dict(DEFAULTS)
            full.update(v or {})
            self._set_combo(self.cb_keep, full['keep'])
            self._front_item(float(full['front']))
            self._set_combo(self.cb_measure, full['measure'])
            for k in SIZE_KEYS:
                self.sp[k][0].setValue(float(full[k]))
            self.cb_fill.setChecked(bool(full['fill']))
            self._set_combo(self.cb_cap, full['cap_colour'])
            self.cb_board.setChecked(bool(full['board']))
            self._set_combo(self.cb_view, full.get('view', 'both'))
            self._set_combo(self.cb_each, full.get('each', 'each'))
            self.cb_slivers.setChecked(bool(full.get('slivers', True)))
        finally:
            self._loading = False
        self.changed()

    def changed(self, *_):
        if self._loading:
            return
        v = self.values()
        keep = v['keep']
        for k, on in (('depth_a', keep in ('front', 'both')), ('depth_b', keep in ('back', 'both'))):
            self.sp[k][0].setEnabled(on)
            self.sp[k][1].setEnabled(on)
        self.sp['board_thick'][0].setEnabled(v['board'])
        self.cb_cap.setEnabled(v['fill'])
        self.lbl_hint_a.setText(scale_hint(v['depth_a']))
        self.lbl_hint_b.setText(scale_hint(v['depth_b']))
        self.sp['sliver_mm'][0].setEnabled(v['slivers'])
        self.lbl_hint_s.setText(scale_hint(v['sliver_mm']) if v['slivers'] else "")
        self.refresh_preview()

    def refresh_preview(self):
        v = self.values()
        plan, err = None, ""
        sv = self.survey
        if sv is not None and not sv.empty():
            try:
                plan = plan_all(sv, v)
            except ValueError as e:
                err = str(e)
            except Exception as e:
                err = "Couldn't work out the cut: %s" % e
        if plan and plan.get('each'):
            bad = ["%s: %s" % (nm, e) for _p, e, _l, _h, nm, _t in plan['each'] if e]
            if bad:
                err = "Not cut: " + "  ".join(bad)
        self.preview.set_state(sv, v, plan, err)
        if sv is None or sv.empty():
            self.lbl_size.setText("")
            return
        if plan and plan.get('each'):
            bits = []
            for pl, _e, _l, _h, nm, _t in plan['each']:
                if pl is None:
                    continue
                fr_ = pl['frame']
                if v['keep'] in ('front', 'both'):
                    d = (fr_['hi'] - pl['t1']) / SCALE
                    bits.append("%s %.0f mm (%s)" % (nm, d, scale_hint(d)))
                else:
                    bits.append(nm)
            txt = "%d buildings, each cut on its own." % len(plan['each'])
            if bits and v['keep'] in ('front', 'both'):
                txt += " The front parts come out overall: " + "; ".join(bits) + "."
            if plan.get('left'):
                txt += " Left whole (under more than one building): %s." % ", ".join(
                    str(getattr(t, 'name', '') or 'a group') for t in plan['left'])
            self.lbl_size.setText(txt)
            return
        fr = plan['frame'] if plan else sv.frame(front_vector(v['front']))
        if not fr:
            return
        total = (fr['hi'] - fr['lo']) / SCALE
        txt = "The building is %.0f mm deep overall" % total
        if fr['wall_front'] is not None and fr['wall_back'] is not None:
            txt += ", %.0f mm from the front walls to the back walls" % ((fr['wall_front'] - fr['wall_back']) / SCALE)
        elif v['measure'] == 'wall':
            txt += " (no front wall found - measuring from the furthest part out)"
        txt += "."
        if plan:
            if v['keep'] in ('front', 'both'):
                txt += " The front part comes out %.0f mm deep overall (%s)." % (
                    (fr['hi'] - plan['t1']) / SCALE, scale_hint((fr['hi'] - plan['t1']) / SCALE))
        self.lbl_size.setText(txt)

    # -- the building
    def _scene(self):
        return getattr(self.viewport, 'scene', None)

    def watch_selection(self):
        if self._busy:
            return
        try:
            if not self.isVisible():
                return
        except Exception:
            return
        sc = self._scene()
        if sc is None:
            return
        key = tuple(sorted(id(e) for e in _items(getattr(sc, 'selection', None))))
        if key != self._sel_key:
            self.read_building()

    def read_building(self, force=False):
        sc = self._scene()
        if sc is None:
            return
        self._sel_key = tuple(sorted(id(e) for e in _items(getattr(sc, 'selection', None))))
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                self.survey = Survey(sc)
            finally:
                QApplication.restoreOverrideCursor()
        except Exception as e:
            self.survey = None
            self.preview.message = "Couldn't read the model: %s" % e
            self.preview.update()
            return
        sv = self.survey
        names = [str(getattr(t, 'name', '') or 'a group') for t in sv.tops]
        if sv.empty():
            self.lbl_sel.setText("Nothing to cut yet.")
        elif sv.whole:
            self.lbl_sel.setText("Nothing picked: the whole model will be cut (%d group%s)." % (
                len(sv.tops), "" if len(sv.tops) == 1 else "s"))
        else:
            self.lbl_sel.setText("Cutting: %s" % ", ".join(names[:6]) + (" and %d more" % (len(names) - 6)
                                                                         if len(names) > 6 else ""))
        if not sv.empty():
            blds, _left = sv.buildings()
            if len(blds) > 1:
                bn = [sv.building_name(b) for b in blds]
                self.lbl_sel.setText(self.lbl_sel.text() + "\n%d buildings: %s" % (
                    len(blds), ", ".join(bn[:6]) + (" and %d more" % (len(bn) - 6) if len(bn) > 6 else "")))
        self.refresh_preview()

    def use_picked_face(self):
        sc = self._scene()
        n = picked_face_normal(sc) if sc is not None else None
        if n is None:
            QMessageBox.information(self, PLUGIN_NAME, "Pick a face on the front wall first (an upright face). "
                                    "Double-click into the building's group to get at its faces.")
            return
        ang = math.degrees(math.atan2(n[1], n[0]))
        for _lab, a in FRONTS:
            if abs(((ang - a + 180.0) % 360.0) - 180.0) < 0.5:
                ang = a
        self._front_item(ang)
        self.changed()

    # -- cutting
    def do_cut(self):
        sc = self._scene()
        if sc is None:
            return
        v = self.values()
        _ui_settings_save(last_values={k: v[k] for k in DEFAULTS if k in v})
        self._busy = True
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                self.survey = Survey(sc)
                if self.survey.empty():
                    raise ValueError("There's nothing to cut. Build the building first.")
                cmd, rep = run_cut(sc, self.survey, v)
            finally:
                QApplication.restoreOverrideCursor()
        except ValueError as e:
            self._busy = False
            QMessageBox.warning(self, PLUGIN_NAME, str(e))
            return
        except Exception as e:
            self._busy = False
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, PLUGIN_NAME, "The cut didn't work:\n%s" % e)
            return
        if cmd is None:
            self._busy = False
            QMessageBox.information(self, PLUGIN_NAME, "Nothing crosses the cut, so nothing was changed.")
            return
        try:
            self.viewport.history.execute(cmd)
        except Exception as e:
            self._busy = False
            QMessageBox.warning(self, PLUGIN_NAME, "Could not change the model:\n%s" % e)
            return
        try:
            self.viewport.notify_scene_changed()
        except Exception:
            pass
        self._busy = False
        msg = "Cut %d part%s, took away %d, left %d as they were." % (
            rep['cut'], "" if rep['cut'] == 1 else "s", rep['removed'], rep['kept'])
        if v['fill']:
            msg += " %d cut face%s filled in." % (rep['caps'], "" if rep['caps'] == 1 else "s")
        if rep.get('moved'):
            msg += (" The back is its own group now ('... - back part'), the front '... - front part' - "
                    "use the buttons below to pick or show one part at a time.")
        if rep.get('boards'):
            msg += " Backing board%s added." % ("s" if rep['boards'] > 1 else "")
        if rep.get('buildings', 1) > 1:
            msg += " %d buildings, each cut on its own." % rep['buildings']
        if rep.get('slivers'):
            msg += " %d sliver%s thinner than %.0f mm thrown away." % (
                rep['slivers'], "" if rep['slivers'] == 1 else "s", v['sliver_mm'])
        bad = False
        if rep.get('skipped'):
            bad = True
            msg += "\nNot cut: " + "; ".join(rep['skipped'])
        if rep.get('left'):
            msg += "\nLeft whole (under more than one building): %s." % ", ".join(rep['left'][:6])
        if rep['opened']:
            msg += ("\n%d thin sheet%s (glass, tin...) cut without filling - nothing inside to fill."
                    % (rep['opened'], "" if rep['opened'] == 1 else "s"))
        if rep['repeat']:
            bad = True
            msg += "\nLeft whole (the same part used more than once): %s." % ", ".join(sorted(set(rep['repeat']))[:8])
        if rep['bad']:
            bad = True
            msg += ("\n%d tiny face%s couldn't be made (IngeTrazo treats points under 0.1 mm apart as one)."
                    % (rep['bad'], "" if rep['bad'] == 1 else "s"))
        msg += "\nCtrl+Z puts it all back. Next: Scale Studio."
        self.lbl_report.setText(msg)
        self.lbl_report.setStyleSheet("color: %s;" % ("#a33" if bad else "#2a6a2a"))
        self.tabs.setCurrentIndex(2)
        self.read_building(force=True)

    def _parts(self, which):
        sc = self._scene()
        parts = find_parts(sc) if sc is not None else {'front': [], 'back': []}
        return parts, parts.get(which, []) if which else []

    def pick_part(self, which):
        parts, gs = self._parts(which)
        if not gs:
            QMessageBox.information(self, PLUGIN_NAME, "There's no %s part yet - cut the building first "
                                    "(keeping the %s, or both)." % (which, which))
            return False
        if not select_groups(self.viewport, gs):
            QMessageBox.information(self, PLUGIN_NAME, "Couldn't select it - pick '%s' in Show / Hide."
                                    % gs[0].name)
            return False
        self._sel_key = tuple(sorted(id(e) for e in _items(getattr(self._scene(), 'selection', None))))
        return True

    def show_only(self, which):
        parts, gs = self._parts(which)
        if which and not gs:
            QMessageBox.information(self, PLUGIN_NAME, "There's no %s part yet - cut the building first." % which)
            return
        other = 'back' if which == 'front' else 'front'
        if which is None:
            hide_groups(self.viewport, parts['front'] + parts['back'], False)
        else:
            hide_groups(self.viewport, gs, False)
            hide_groups(self.viewport, parts[other], True)

    def to_scale_studio(self, which):
        if self.pick_part(which):
            self.show_only(which)
            self.pick_part(which)
            self.open_scale_studio()

    def open_scale_studio(self):
        import sys as _sys
        for nm, mod in list(_sys.modules.items()):
            if nm.endswith("ed3d_plugins_toolbar") and hasattr(mod, "find_plugin_action"):
                try:
                    win = self.viewport.window()
                    act = mod.find_plugin_action(win, "3D Scale Studio", "Ctrl+Alt+K")
                    if act is not None:
                        self.close()
                        act.trigger()
                        return
                except Exception:
                    pass
        QMessageBox.information(self, PLUGIN_NAME, "Open 3D Scale Studio from the toolbar (Ctrl+Alt+K).")

    # -- presets
    def _order(self):
        names = list(BUILTIN_PRESETS) + sorted(n for n in self.user_presets if n not in BUILTIN_PRESETS)
        saved = _ui_settings().get('preset_order') or []
        ordered = [n for n in saved if n in names] + [n for n in names if n not in saved]
        return ordered

    def fill_presets(self, select=None):
        self.cb_preset.blockSignals(True)
        self.cb_preset.clear()
        self.cb_preset.addItem("(pick a preset)", None)
        for n in self._order():
            self.cb_preset.addItem(n + ("" if n in BUILTIN_PRESETS else "  (yours)"), n)
        if select:
            i = self.cb_preset.findData(select)
            if i >= 0:
                self.cb_preset.setCurrentIndex(i)
        self.cb_preset.blockSignals(False)

    def preset_picked(self, i):
        n = self.cb_preset.itemData(i)
        if not n:
            return
        d = self.user_presets.get(n) or BUILTIN_PRESETS.get(n)
        if d:
            v = self.values()
            v.update({k: d[k] for k in DEFAULTS if k in d})
            self.set_values(v)

    def save_current(self):
        n = self.cb_preset.currentData()
        if not n or n in BUILTIN_PRESETS:
            self.save_as()
            return
        save_preset(n, self.values())
        self.user_presets = load_presets()

    def save_as(self):
        n, ok = QInputDialog.getText(self, PLUGIN_NAME, "Name for the preset:")
        n = (n or "").strip()
        if not ok or not n:
            return
        if n in BUILTIN_PRESETS:
            n += " (mine)"
        save_preset(n, self.values())
        self.user_presets = load_presets()
        self.fill_presets(select=n)

    def delete_current(self):
        n = self.cb_preset.currentData()
        if not n or n in BUILTIN_PRESETS:
            QMessageBox.information(self, PLUGIN_NAME, "Only your own presets can be deleted.")
            return
        if QMessageBox.question(self, PLUGIN_NAME, "Delete the preset '%s'?" % n) != QMessageBox.Yes:
            return
        delete_preset(n)
        self.user_presets = load_presets()
        self.fill_presets()

    def move_preset(self, step):
        n = self.cb_preset.currentData()
        if not n:
            return
        order = self._order()
        i = order.index(n)
        j = max(0, min(len(order) - 1, i + step))
        order.insert(j, order.pop(i))
        _ui_settings_save(preset_order=order)
        self.fill_presets(select=n)

    def open_folder(self):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        os.makedirs(PRESET_DIR, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(PRESET_DIR))

    def closeEvent(self, ev):
        try:
            self.timer.stop()
            v = self.values()
            _ui_settings_save(last_values={k: v[k] for k in DEFAULTS if k in v})
        except Exception:
            pass
        super().closeEvent(ev)


EDDY_TIPS = {
    'Keep': "The front (a low relief building), the back, or both with the middle taken out.",
    'The front faces': "Which way the front of the building looks. The preview shows FRONT - if it's on the "
                       "wrong side, pick another.",
    'Measure A and B from': "From the front of the walls (the plinth, steps and gutters in front stay on), or "
                            "from the furthest part out.",
    'Preview': "What the preview shows: the building from above, from the side, or both.",
    'Colour of the cut faces': "The cut faces in the colour of the part they're cut from, or plain grey so you "
                               "can see them.",
    'Cut the building': "Cuts it. One undo step - Ctrl+Z puts it all back.",
    'Read the building again': "Reads what's picked again (it does this by itself when you pick something else).",
    'Info': "How it works.",
    'Next: the Cut page': "Goes to the Cut page.",
    '@preview': "The cuts in red, what's taken away shaded. FRONT marks the front.",
}


class LowReliefTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+Shift+L"
    description = "Cuts a whole building down to low relief - keep the front, the back, or both with the middle " \
                  "taken out. Every part is cut and filled in, ready for Scale Studio."

    _dialog = None

    def on_activate(self, viewport):
        dlg = LowReliefTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.viewport = viewport
                    dlg.raise_()
                    dlg.activateWindow()
                    dlg.read_building(force=True)
                    return
            except Exception:
                pass
        cur = dict(DEFAULTS)
        last = _ui_settings().get('last_values')
        if isinstance(last, dict):
            cur.update({k: last[k] for k in DEFAULTS if k in last})
        dlg = LowReliefDialog(cur, viewport, self)
        LowReliefTool._dialog = dlg

        def closed(*_):
            LowReliefTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass


def run(viewport=None):
    LowReliefTool().on_activate(viewport)
