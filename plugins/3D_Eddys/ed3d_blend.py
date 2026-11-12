# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Blend for IngeTrazo
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
3D Blend - blends one object smoothly into another, for IngeTrazo.

Select two objects that overlap - a dome sitting in a boiler, a post standing in a plinth,
a handle on a mug, a branch on a trunk - and Blend fills the corner where they meet with a
smooth curve, like a fillet. Or it puts a collar round the join instead - round or square,
following the base's curve - with nuts, bolt heads, rivets or a fixing of your own round the top. The blend is a closed solid in its own group: it sinks a little
into both objects, so in the slicer the three print as one piece.

Shape: Round (a quarter circle), Flared (spreads further along the base, like a loco dome),
Soft cove (a gentler curve) or Straight (a sloped fillet).
Every place they meet: both ends of a handle get their blend.
The colour: like the object, like the base, or its own.
Ctrl+Shift+B opens the window.
"""

import os
import json
import math
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtGui import QVector3D

PLUGIN_NAME = "3D Blend"
VERSION = "1"
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_blend.json")

UNITS = [("Metres (m)", 1000.0, "m"), ("Centimetres (cm)", 10.0, "cm"),
         ("Millimetres (mm) - drawn 1000 times big", 1.0, "mm")]
SHAPE_CHOICES = [("Round - a smooth quarter curve", "round"),
                 ("Flared - spreads out along the base", "flared"),
                 ("Soft cove - a gentler curve", "cove"),
                 ("Straight - a sloped fillet", "straight")]
SMOOTHNESS = [("Low (quick)", 48, 5), ("Medium", 96, 8), ("High (smoothest)", 160, 12)]
COLOURS = [("Same as the object", "object"), ("Same as the base", "base"),
           ("Its own colour (easy to see)", "own")]
OWN_COLOUR = (0.93, 0.55, 0.25)

JOINS = [("Smooth blend (a curved fillet)", "blend"), ("Round collar", "round"), ("Square collar", "square")]
FIXING_CHOICES = [("None", "none"), ("Nuts (bolt end showing)", "nuts"), ("Hex bolt heads", "bolts"),
                  ("Round rivets", "rivets")]

DEFAULTS = {'shape': 'round', 'spread': 100, 'smooth': 1, 'all_loops': True, 'soften': True,
            'colour': 'object', 'replace': True, 'size_frac': 0.12, 'join': 'blend', 'fixings': 'nuts',
            'count': 8, 'ch_frac': 0.06, 'cw_frac': 0.15, 'fs_frac': 0.06}


def load_settings():
    d = dict(DEFAULTS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            got = json.load(f)
        if isinstance(got, dict):
            for k, v in got.items():
                if k in DEFAULTS:
                    d[k] = v
    except Exception:
        pass
    return d


def save_settings(d):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({k: d[k] for k in DEFAULTS if k in d}, f, indent=1)
    except Exception:
        pass


def vertex_to_vector3d(v):
    """Returns the vertex position as a QVector3D, or None if it can't be read."""
    if isinstance(v, QVector3D):
        return QVector3D(v.x(), v.y(), v.z())
    for get in (lambda: (v.x(), v.y(), v.z()),
                lambda: (v.x, v.y, v.z),
                lambda: (v[0], v[1], v[2]),
                lambda: (v.pos.x(), v.pos.y(), v.pos.z()),
                lambda: (v.position.x(), v.position.y(), v.position.z())):
        try:
            x, y, z = get()
            return QVector3D(float(x), float(y), float(z))
        except Exception:
            pass
    return None


class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))


def _items(x):
    if x is None:
        return []
    if isinstance(x, dict):
        return list(x.values())
    try:
        return list(x)
    except Exception:
        return []


def _val(obj, name):
    """Reads an attribute that may be a plain value or a method."""
    x = getattr(obj, name, None)
    if callable(x):
        try:
            x = x()
        except Exception:
            return None
    return x


def _is_face(e):
    return hasattr(e, 'loop') or 'face' in type(e).__name__.lower()


def _is_group(e):
    return (not _is_face(e)) and getattr(e, 'mesh', None) is not None


def _meshes_of(e, out, seen):
    """Collect the meshes of a group, including nested groups."""
    m = getattr(e, 'mesh', None)
    if m is not None and id(m) not in seen:
        seen.add(id(m))
        out.append(m)
    for ch in _items(getattr(e, 'groups', None)) + _items(getattr(e, 'children', None)):
        if getattr(ch, 'mesh', None) is not None:
            _meshes_of(ch, out, seen)



# ---------------------------------------------------------------------------
# Faces into triangles (the same as in Part Splitter)
# ---------------------------------------------------------------------------
def world_loops(entities):
    """The selection's faces in world space, as [(outer [QVector3D], [holes], face)]: component
    instances and moved groups come through their placement, so the parts come out where - and
    the way round - the object really is."""
    out = []
    seen = set()
    try:
        from core.group import world_mesh
    except Exception:
        world_mesh = None

    def pos(v):
        return vertex_to_vector3d(v)

    def add(f):
        if id(f) in seen:
            return
        seen.add(id(f))
        outer = [pos(v) for v in _items(getattr(f, 'vertices', None))]
        if len(outer) < 3 or any(q is None for q in outer):
            return
        holes = []
        for h in _items(getattr(f, 'holes', None)):
            hl = [pos(v) for v in _items(h)]
            if len(hl) >= 3 and all(q is not None for q in hl):
                holes.append(hl)
        out.append((outer, holes, f))
    for e in entities:
        if _is_group(e):
            m = None
            if world_mesh is not None:
                try:
                    m = world_mesh(e)
                except Exception:
                    m = None
            if m is None:
                ms = []
                _meshes_of(e, ms, set())
                for m_ in ms:
                    for f in _items(getattr(m_, 'faces', None)):
                        add(f)
            else:
                for f in _items(getattr(m, 'faces', None)):
                    add(f)
        elif _is_face(e):
            add(e)
    return out



def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(u, v):
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def _dot(u, v):
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


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


# ---------------------------------------------------------------- triangulating
def _seg_cross(p, q, a, b):
    """True if segments p-q and a-b cross at a point inside both (touching ends don't count)."""
    def orient(u, v, w):
        return (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
    d1, d2 = orient(a, b, p), orient(a, b, q)
    d3, d4 = orient(p, q, a), orient(p, q, b)
    return ((d1 > 0 > d2) or (d1 < 0 < d2)) and ((d3 > 0 > d4) or (d3 < 0 < d4))


def _bridge_holes(pts, outer, holes):
    """Joins each hole to the outline by a cut, so outline + holes become one ring of indices.
    pts: all 2D points; outer: indices (anticlockwise); holes: lists of indices (clockwise)."""
    ring = list(outer)
    order = sorted(holes, key=lambda h: -max(pts[i][0] for i in h))
    for k, h in enumerate(order):
        m = max(range(len(h)), key=lambda j: (pts[h[j]][0], -pts[h[j]][1]))
        M = pts[h[m]]
        others = [hh for hh in order[k + 1:]]
        # the ring's corners nearest the hole first; the first one that can be seen is the bridge
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
                # the bridge must leave the ring's corner into the inside of the ring
                n = len(ring)
                A, B, C = pts[ring[j - 1]], P, pts[ring[(j + 1) % n]]
                if _in_cone(A, B, C, M):
                    best = j
                    break
                if best is None:
                    best = -1 - j          # visible but outside the cone: a fallback
        if best is None:
            best = cand[0]
        elif best < 0:
            best = -1 - best
        hole_ring = h[m:] + h[:m]
        ring = ring[:best + 1] + hole_ring + [hole_ring[0], ring[best]] + ring[best + 1:]
    return ring


def _in_cone(a, b, c, p):
    """True if p is inside the angle a-b-c of an anticlockwise ring (at corner b)."""
    def orient(u, v, w):
        return (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
    if orient(a, b, c) >= 0:           # convex corner
        return orient(b, c, p) >= 0 and orient(a, b, p) >= 0
    return not (orient(b, c, p) < 0 and orient(a, b, p) < 0)


def triangulate2d(pts, outer, holes=()):
    """Triangles (index triples) filling the outline with its holes. Ear clipping.
    pts: 2D points; outer, holes: index lists. Any winding."""
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
    # drop corners repeated one after the other
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

    # a grid of the corners, so finding corners inside an ear is quick
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


def _drop_axis(normal):
    """Which axis to leave out to flatten a face (the one it faces most), and the other two in
    the order that keeps anticlockwise = facing that axis's + direction."""
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


def make_face(outer, holes=(), colour=None, tris=None):
    holes = [list(h) for h in holes if len(h) >= 3]
    return {'o': list(outer), 'h': holes, 't': tris if tris is not None else triangulate_face(outer, holes),
            'c': colour}



# ---------------------------------------------------------------------------
# The blend itself: plain Python, no extra libraries
# ---------------------------------------------------------------------------
# Positions are (x, y, z) tuples in the model's units, in the world.
# 'Object' = the thing that sits on or pokes into the 'base' (a dome on a boiler, a post on
# a plinth, a handle on a mug). The blend is a ring-shaped solid that fills the corner where
# they meet with a smooth curve. It sinks a little into both, so once printed they're one.

def v_add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def v_sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def v_mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def v_dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def v_len(a): return math.sqrt(v_dot(a, a))


def v_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def v_norm(a):
    L = v_len(a)
    return (a[0] / L, a[1] / L, a[2] / L) if L > 1e-300 else (0.0, 0.0, 0.0)


def tri_normal(t):
    return v_norm(v_cross(v_sub(t[1], t[0]), v_sub(t[2], t[0])))


def bounds(tris):
    xs = [p[0] for t in tris for p in t]
    ys = [p[1] for t in tris for p in t]
    zs = [p[2] for t in tris for p in t]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def centroid(tris):
    """Area-weighted middle of the surface."""
    sx = sy = sz = sa = 0.0
    for t in tris:
        a = v_len(v_cross(v_sub(t[1], t[0]), v_sub(t[2], t[0])))
        c = ((t[0][0] + t[1][0] + t[2][0]) / 3.0, (t[0][1] + t[1][1] + t[2][1]) / 3.0,
             (t[0][2] + t[1][2] + t[2][2]) / 3.0)
        sx += c[0] * a
        sy += c[1] * a
        sz += c[2] * a
        sa += a
    if sa <= 0:
        lo, hi = bounds(tris)
        return tuple((lo[i] + hi[i]) / 2.0 for i in range(3))
    return (sx / sa, sy / sa, sz / sa)


class TriGrid:
    """Triangles sorted into boxes in space, so only the nearby ones are looked at."""

    def __init__(self, tris):
        self.tris = tris
        lo, hi = bounds(tris)
        diag = v_len(v_sub(hi, lo)) or 1.0
        edges = sorted(v_len(v_sub(t[1], t[0])) for t in tris)
        med = edges[len(edges) // 2] if edges else diag
        self.cell = max(med * 1.5, diag / 150.0, 1e-12)
        self.g = {}
        self.big = []
        c = self.cell
        for i, t in enumerate(tris):
            a = [int(math.floor(min(p[k] for p in t) / c)) for k in range(3)]
            b = [int(math.floor(max(p[k] for p in t) / c)) for k in range(3)]
            n = (b[0] - a[0] + 1) * (b[1] - a[1] + 1) * (b[2] - a[2] + 1)
            if n > 2000:
                self.big.append(i)
                continue
            for x in range(a[0], b[0] + 1):
                for y in range(a[1], b[1] + 1):
                    for z in range(a[2], b[2] + 1):
                        self.g.setdefault((x, y, z), []).append(i)

    def near(self, lo, hi):
        c = self.cell
        a = [int(math.floor(lo[k] / c)) for k in range(3)]
        b = [int(math.floor(hi[k] / c)) for k in range(3)]
        out = set(self.big)
        if (b[0] - a[0] + 1) * (b[1] - a[1] + 1) * (b[2] - a[2] + 1) > 200000:
            return set(range(len(self.tris)))
        g = self.g
        for x in range(a[0], b[0] + 1):
            for y in range(a[1], b[1] + 1):
                for z in range(a[2], b[2] + 1):
                    got = g.get((x, y, z))
                    if got:
                        out.update(got)
        return out

    def closest(self, p, reach):
        """The nearest point on the surface to p (looking up to 'reach' away), its triangle's
        index, and the distance. (None, -1, inf) if nothing is that close."""
        best = (None, -1, float('inf'))
        r = reach
        for _ in range(4):
            ids = self.near(v_sub(p, (r, r, r)), v_add(p, (r, r, r)))
            for i in ids:
                q = closest_on_tri(p, self.tris[i])
                d = v_len(v_sub(p, q))
                if d < best[2]:
                    best = (q, i, d)
            if best[0] is not None and best[2] <= r:
                return best
            r *= 2.5
        return best


def closest_on_tri(p, t):
    """Closest point to p on triangle t (Ericson's method)."""
    a, b, c = t
    ab, ac, ap = v_sub(b, a), v_sub(c, a), v_sub(p, a)
    d1, d2 = v_dot(ab, ap), v_dot(ac, ap)
    if d1 <= 0 and d2 <= 0:
        return a
    bp = v_sub(p, b)
    d3, d4 = v_dot(ab, bp), v_dot(ac, bp)
    if d3 >= 0 and d4 <= d3:
        return b
    vc = d1 * d4 - d3 * d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        v = d1 / (d1 - d3)
        return v_add(a, v_mul(ab, v))
    cp = v_sub(p, c)
    d5, d6 = v_dot(ab, cp), v_dot(ac, cp)
    if d6 >= 0 and d5 <= d6:
        return c
    vb = d5 * d2 - d1 * d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        w = d2 / (d2 - d6)
        return v_add(a, v_mul(ac, w))
    va = d3 * d6 - d5 * d4
    if va <= 0 and (d4 - d3) >= 0 and (d5 - d6) >= 0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        return v_add(b, v_mul(v_sub(c, b), w))
    den = 1.0 / (va + vb + vc)
    v, w = vb * den, vc * den
    return v_add(a, v_add(v_mul(ab, v), v_mul(ac, w)))


def _seg_hits_tri(p, q, t):
    """Where the line p-q passes through triangle t, or None."""
    e1, e2 = v_sub(t[1], t[0]), v_sub(t[2], t[0])
    d = v_sub(q, p)
    h = v_cross(d, e2)
    a = v_dot(e1, h)
    scale = v_len(e1) * v_len(e2) * v_len(d)
    if scale <= 0 or abs(a) < 1e-12 * scale:
        return None                                  # in line with the triangle
    f = 1.0 / a
    s = v_sub(p, t[0])
    u = f * v_dot(s, h)
    if u < -1e-9 or u > 1 + 1e-9:
        return None
    qq = v_cross(s, e1)
    v = f * v_dot(d, qq)
    if v < -1e-9 or u + v > 1 + 1e-9:
        return None
    k = f * v_dot(e2, qq)
    if k < -1e-9 or k > 1 + 1e-9:
        return None
    return v_add(p, v_mul(d, k))


def tri_tri(a, b, tol):
    """The short line where triangles a and b cross, as (p, q), or None."""
    pts = []
    for t1, t2 in ((a, b), (b, a)):
        for i in range(3):
            x = _seg_hits_tri(t1[i], t1[(i + 1) % 3], t2)
            if x is not None and all(v_len(v_sub(x, y)) > tol for y in pts):
                pts.append(x)
    if len(pts) < 2:
        return None
    best, pair = -1.0, None
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = v_len(v_sub(pts[i], pts[j]))
            if d > best:
                best, pair = d, (pts[i], pts[j])
    return pair if best > tol else None


def meeting_lines(obj, base, gbase, tol):
    """Every short line where the object's surface crosses the base's."""
    segs = []
    for t in obj:
        lo = tuple(min(p[k] for p in t) - tol for k in range(3))
        hi = tuple(max(p[k] for p in t) + tol for k in range(3))
        for i in gbase.near(lo, hi):
            u = base[i]
            if (max(p[0] for p in u) < lo[0] or min(p[0] for p in u) > hi[0] or
                    max(p[1] for p in u) < lo[1] or min(p[1] for p in u) > hi[1] or
                    max(p[2] for p in u) < lo[2] or min(p[2] for p in u) > hi[2]):
                continue
            s = tri_tri(t, u, tol)
            if s is not None:
                segs.append(s)
    return segs


def chain_lines(segs, tol):
    """Joins the short lines end to end into loops (closed) and chains (open).
    Returns [(points, closed)], longest first."""
    cell = tol * 4.0
    ends = {}

    def key(p):
        return (int(math.floor(p[0] / cell)), int(math.floor(p[1] / cell)), int(math.floor(p[2] / cell)))

    for i, (p, q) in enumerate(segs):
        for e, pt in ((0, p), (1, q)):
            ends.setdefault(key(pt), []).append((i, e))

    def touching(pt, used):
        k = key(pt)
        best = None
        bd = tol * 4.0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for i, e in ends.get((k[0] + dx, k[1] + dy, k[2] + dz), ()):
                        if used[i]:
                            continue
                        d = v_len(v_sub(segs[i][e], pt))
                        if d <= bd:
                            bd, best = d, (i, e)
        return best

    used = [False] * len(segs)
    out = []
    for s0 in range(len(segs)):
        if used[s0]:
            continue
        used[s0] = True
        line = [segs[s0][0], segs[s0][1]]
        for direction in (0, 1):
            while True:
                tip = line[-1] if direction == 0 else line[0]
                nxt = touching(tip, used)
                if nxt is None:
                    break
                i, e = nxt
                used[i] = True
                far = segs[i][1 - e]
                if direction == 0:
                    line.append(far)
                else:
                    line.insert(0, far)
        clean = [line[0]]
        for p in line[1:]:
            if v_len(v_sub(p, clean[-1])) > tol:
                clean.append(p)
        if len(clean) < 2:
            continue
        length = sum(v_len(v_sub(clean[i + 1], clean[i])) for i in range(len(clean) - 1))
        closed = len(clean) > 3 and v_len(v_sub(clean[0], clean[-1])) <= max(tol * 8.0, length * 0.02)
        if closed and v_len(v_sub(clean[0], clean[-1])) <= tol * 2:
            clean.pop()
        out.append((clean, closed, length))
    out.sort(key=lambda c: -c[2])
    return [(c[0], c[1]) for c in out]


def resample(pts, closed, n):
    """n points evenly spaced along the line (for a loop, without repeating the first)."""
    P = list(pts) + ([pts[0]] if closed else [])
    seg = [v_len(v_sub(P[i + 1], P[i])) for i in range(len(P) - 1)]
    total = sum(seg)
    if total <= 0:
        return list(pts)
    count = n if closed else n + 1
    step = total / (n if closed else n)
    out, i, run = [], 0, 0.0
    for k in range(count):
        d = min(k * step, total)
        while i < len(seg) - 1 and run + seg[i] < d:
            run += seg[i]
            i += 1
        f = 0.0 if seg[i] <= 0 else min(1.0, max(0.0, (d - run) / seg[i]))
        out.append(v_add(P[i], v_mul(v_sub(P[i + 1], P[i]), f)))
    return out


def _smooth_dirs(dirs, closed, passes=2):
    for _ in range(passes):
        n = len(dirs)
        new = []
        for i in range(n):
            a = dirs[(i - 1) % n] if (closed or i > 0) else dirs[i]
            b = dirs[(i + 1) % n] if (closed or i < n - 1) else dirs[i]
            new.append(v_norm(v_add(v_add(a, b), v_mul(dirs[i], 2.0))))
        dirs = new
    return dirs


def surface_normal(grid, p, reach, near_n=None):
    """The surface's facing direction at p: the triangles within a little of p, averaged."""
    q, i, d = grid.closest(p, reach)
    if i < 0:
        return None
    r = max(d, reach * 0.25)
    acc = (0.0, 0.0, 0.0)
    ref = tri_normal(grid.tris[i])
    for j in grid.near(v_sub(p, (r, r, r)), v_add(p, (r, r, r))):
        t = grid.tris[j]
        if v_len(v_sub(closest_on_tri(p, t), p)) <= r * 1.01:
            n = tri_normal(t)
            if v_dot(n, ref) < 0:           # faces turned the wrong way round still count
                n = v_mul(n, -1.0)
            area = v_len(v_cross(v_sub(t[1], t[0]), v_sub(t[2], t[0])))
            acc = v_add(acc, v_mul(n, area))
    n = v_norm(acc) if v_len(acc) > 0 else ref
    return n


SHAPES = {'round': (0.7071, 1.0), 'flared': (1.0, 1.8), 'straight': (0.0, 1.0), 'cove': (0.35, 1.0)}


def _bezier(a, c, b, w, t):
    """A point on the curve from a to b, pulled towards corner c (rational quadratic:
    w = 0.707 is a true quarter circle on a square corner, 0 is a straight line)."""
    u = 1.0 - t
    k0, k1, k2 = u * u, 2.0 * u * t * w, t * t
    s = k0 + k1 + k2
    return ((a[0] * k0 + c[0] * k1 + b[0] * k2) / s,
            (a[1] * k0 + c[1] * k1 + b[1] * k2) / s,
            (a[2] * k0 + c[2] * k1 + b[2] * k2) / s)


def signed_volume(tris):
    v = 0.0
    for a, b, c in tris:
        v += v_dot(a, v_cross(b, c))
    return v / 6.0


def find_joins(obj, base, opt):
    """Where the object meets the base: (lines, tol, grid of the base, grid of the object).
    lines = [(points, closed)], the biggest first."""
    if not obj or not base:
        raise ValueError("Select two objects: the one to blend in, and what it sits on.")
    lo, hi = bounds(obj + base)
    diag = v_len(v_sub(hi, lo)) or 1.0
    tol = diag * 1e-7
    gbase = TriGrid(base)
    gobj = TriGrid(obj)
    segs = meeting_lines(obj, base, gbase, tol)
    if not segs:
        raise ValueError("The two objects don't cross each other, so there's nowhere to blend.\n\n"
                         "Push the object a little way into the base (so they overlap), then try again.")
    lines = chain_lines(segs, tol * 50.0)
    lines = [l for l in lines if len(l[0]) >= 3]
    if not lines:
        raise ValueError("Couldn't follow the line where they meet. Try pushing the object a little "
                         "further into the base.")
    if not opt.get('all_loops'):
        lines = lines[:1]
    else:
        # every separate place they meet (both ends of a handle), but not a loop inside
        # another one (the inside of a hollow tube)
        kept = []
        for line, closed in lines:
            c = v_mul(tuple(map(sum, zip(*line))), 1.0 / len(line))
            rad = sum(v_len(v_sub(p, c)) for p in line) / len(line)
            inside = False
            for kc, krad, kclosed, _ in kept:
                if kclosed and closed and rad < krad and v_len(v_sub(c, kc)) < krad * 0.6:
                    inside = True
                    break
            if not inside:
                kept.append((c, rad, closed))
                kept_line = (line, closed)
                kept[-1] = kept[-1] + (kept_line,)
        lines = [k[3] for k in kept]
    return lines, tol, gbase, gobj


def build_blend(obj, base, opt, report=None):
    """The blend between the object and the base, as (points, faces) - faces are lists of
    point numbers, every one a triangle. opt: 'size' (up the object, model units),
    'spread' (how far along the base, x size), 'shape', 'stations', 'steps', 'all_loops'.
    Raises ValueError with a message for the user when it can't be done."""
    report = report if report is not None else {}
    lines, tol, gbase, gobj = find_joins(obj, base, opt)
    size = float(opt['size'])
    if size <= 0:
        raise ValueError("The blend size must be more than 0.")
    w, shape_spread = SHAPES.get(opt.get('shape', 'round'), SHAPES['round'])
    spread = float(opt.get('spread', 1.0)) * shape_spread
    r_up, r_out = size, size * spread
    steps = max(2, int(opt.get('steps', 8)))
    if w == 0.0:
        steps = 1
    cobj = centroid(obj)
    pts, faces = [], []
    report['loops'] = len(lines)
    report['open'] = 0
    report['too_big'] = False
    for line, closed in lines:
        length = sum(v_len(v_sub(line[(i + 1) % len(line)], line[i]))
                     for i in range(len(line) if closed else len(line) - 1))
        n = int(opt.get('stations', 96))
        n = max(12 if closed else 4, min(n, int(length / (tol * 2000)) or n))
        P = resample(line, closed, n)
        mid = (sum(p[0] for p in P) / len(P), sum(p[1] for p in P) / len(P), sum(p[2] for p in P) / len(P))
        up = v_norm(v_sub(cobj, mid))
        if closed:
            # a loop much smaller than the blend can't take it all the way round
            rad = sum(v_len(v_sub(p, mid)) for p in P) / len(P)
            if r_out > rad * 1.5 or r_up > rad * 1.5:
                report['too_big'] = True
        reach = max(r_up, r_out) * 0.5
        nA, nB = [], []
        for p in P:
            a = surface_normal(gobj, p, reach)
            b = surface_normal(gbase, p, reach)
            if a is None or b is None:
                raise ValueError("Couldn't read the surfaces where they meet.")
            out_dir = v_sub(p, mid)
            # the object's surface faces away from the middle of the join...
            if closed and v_len(out_dir) > tol:
                if v_dot(a, out_dir) < 0:
                    a = v_mul(a, -1.0)
            elif v_dot(a, v_sub(p, cobj)) < 0:
                a = v_mul(a, -1.0)
            # ...and the base's surface faces the object
            if v_dot(b, up) < 0:
                b = v_mul(b, -1.0)
            nA.append(a)
            nB.append(b)
        # keep neighbours facing the same way, then smooth out the facets
        for arr in (nA, nB):
            for i in range(1, len(arr)):
                if v_dot(arr[i], arr[i - 1]) < 0:
                    arr[i] = v_mul(arr[i], -1.0)
        nA = _smooth_dirs(nA, closed)
        nB = _smooth_dirs(nB, closed)
        rings = []
        for i, p in enumerate(P):
            a, b = nA[i], nB[i]
            c = v_dot(a, b)
            tB = v_sub(a, v_mul(b, c))       # along the base, away from the object
            tA = v_sub(b, v_mul(a, c))       # up the object, away from the base
            if v_len(tB) < 1e-6 or v_len(tA) < 1e-6:
                tB = v_norm(v_cross(b, v_cross(a, b))) if v_len(tB) < 1e-6 else v_norm(tB)
                tA = v_norm(v_cross(a, v_cross(b, a))) if v_len(tA) < 1e-6 else v_norm(tA)
            else:
                tB, tA = v_norm(tB), v_norm(tA)
            eb = v_add(p, v_mul(tB, r_out))
            q, _, d = gbase.closest(eb, r_out)
            if q is not None and d < r_out * 0.6:
                eb = q
            ea = v_add(p, v_mul(tA, r_up))
            q, _, d = gobj.closest(ea, r_up)
            if q is not None and d < r_up * 0.6:
                ea = q
            eb = v_sub(eb, v_mul(b, 0.02 * r_out))     # tucked just under the surfaces, so the
            ea = v_sub(ea, v_mul(a, 0.02 * r_up))      # edges don't flicker against them
            depth = 0.3 * min(r_up, r_out)
            ring = [_bezier(eb, p, ea, w, k / float(steps)) for k in range(steps + 1)]
            bis = v_norm(v_add(a, b))
            ring += [v_sub(ea, v_mul(a, depth)), v_sub(p, v_mul(bis, depth * 1.4)), v_sub(eb, v_mul(b, depth))]
            rings.append(ring)
        m = len(rings[0])
        start = len(pts)
        for ring in rings:
            pts.extend(ring)

        def ix(r, j):
            return start + (r % len(rings)) * m + (j % m)
        made = []
        last = len(rings) if closed else len(rings) - 1
        for r in range(last):
            for j in range(m):
                a0, a1 = ix(r, j), ix(r, j + 1)
                b0, b1 = ix(r + 1, j), ix(r + 1, j + 1)
                made.append([a0, a1, b1])
                made.append([a0, b1, b0])
        if not closed:
            report['open'] += 1
            # close both ends with a flat face (fanned from the corner point, inside the solids)
            for r, flip in ((0, True), (len(rings) - 1, False)):
                hub = ix(r, m - 2)
                for j in range(m):
                    if j in (m - 2, m - 3) or (j + 1) % m == m - 2:
                        continue
                    tri = [hub, ix(r, j), ix(r, j + 1)]
                    made.append(tri[::-1] if flip else tri)
        faces.extend(made)
    # all faces turned outwards
    tris = [(pts[f[0]], pts[f[1]], pts[f[2]]) for f in faces]
    if signed_volume(tris) < 0:
        faces = [f[::-1] for f in faces]
    report['rings'] = len(pts) // max(1, (steps + 4))
    return pts, faces


# ---------------------------------------------------------------------------
# A collar where they meet (round or square), with nuts, bolt heads or rivets on top
# ---------------------------------------------------------------------------
def _ray_down(grid, top, down, length):
    """The first place a line from 'top', heading 'down' for 'length', meets the surface."""
    end = v_add(top, v_mul(down, length))
    lo = tuple(min(top[k], end[k]) for k in range(3))
    hi = tuple(max(top[k], end[k]) for k in range(3))
    best, bd = None, float('inf')
    for i in grid.near(lo, hi):
        x = _seg_hits_tri(top, end, grid.tris[i])
        if x is not None:
            d = v_len(v_sub(x, top))
            if d < bd:
                bd, best = d, x
    return best


def _frame(up):
    """Two directions across 'up', lined up with the model's axes where possible."""
    ref = (1.0, 0.0, 0.0) if abs(up[0]) < 0.9 else (0.0, 1.0, 0.0)
    u = v_norm(v_sub(ref, v_mul(up, v_dot(ref, up))))
    return u, v_cross(up, u)


def _add_solid(pts, faces, rings, closed=True, cap_top=None, cap_bottom=None):
    """Lofts closed cross-sections (rings of points) into faces. cap_*: a single point each
    end is fanned to (for solids round an axis); ends of open paths are not used here."""
    m = len(rings[0])
    start = len(pts)
    for r in rings:
        pts.extend(r)

    def ix(r, j):
        return start + (r % len(rings)) * m + (j % m)
    last = len(rings) if closed else len(rings) - 1
    for r in range(last):
        for j in range(m):
            a0, a1, b0, b1 = ix(r, j), ix(r, j + 1), ix(r + 1, j), ix(r + 1, j + 1)
            faces.append([a0, a1, b1])
            faces.append([a0, b1, b0])


def _prism(pts, faces, centre, up, u, radius, sides, height, sink, turn=0.0, dome=False):
    """A nut, bolt head or rivet standing on 'centre', facing 'up' - a closed solid."""
    v = v_cross(up, u)
    rows = []
    bottom = v_sub(centre, v_mul(up, sink))
    if dome:
        prof = [(1.0, -sink)] + [(math.cos(a), math.sin(a) * height)
                                 for a in [k * (math.pi / 2) / 4 for k in range(4)]]
    else:
        prof = [(1.0, -sink), (1.0, height)]
    ring_pts = []
    for rr, hh in prof:
        ring = []
        for k in range(sides):
            a = turn + 2.0 * math.pi * k / sides
            d = v_add(v_mul(u, math.cos(a) * radius * rr), v_mul(v, math.sin(a) * radius * rr))
            ring.append(v_add(v_add(centre, d), v_mul(up, hh)))
        ring_pts.append(ring)
    s0 = len(pts)
    for ring in ring_pts:
        pts.extend(ring)
    pts.append(bottom)
    bot = len(pts) - 1
    pts.append(v_add(centre, v_mul(up, height)))
    top = len(pts) - 1
    n = sides
    for r in range(len(ring_pts) - 1):
        for k in range(n):
            a0, a1 = s0 + r * n + k, s0 + r * n + (k + 1) % n
            b0, b1 = s0 + (r + 1) * n + k, s0 + (r + 1) * n + (k + 1) % n
            faces.append([a0, a1, b1])
            faces.append([a0, b1, b0])
    lastr = s0 + (len(ring_pts) - 1) * n
    for k in range(n):
        faces.append([bot, s0 + (k + 1) % n, s0 + k])
        if not dome:
            faces.append([top, lastr + k, lastr + (k + 1) % n])
    if dome:
        # the tip of the rivet: a small flat top ring closed to the centre
        for k in range(n):
            faces.append([top, lastr + k, lastr + (k + 1) % n])


def _orient_shells(pts, faces, first):
    """Every new solid (from face 'first' on) turned outward."""
    tris = [(pts[f[0]], pts[f[1]], pts[f[2]]) for f in faces[first:]]
    if tris and signed_volume(tris) < 0:
        faces[first:] = [f[::-1] for f in faces[first:]]


FIXINGS = ('none', 'nuts', 'bolts', 'rivets')


def own_fixing_from(tris):
    """Your own fixing, made ready to use: stood on its base (the lowest point), centred,
    and sized so it's 1 across. It's taken the way up it is in the model (Z up)."""
    if not tris:
        raise ValueError("The fixing has no faces.")
    lo, hi = bounds(tris)
    cx, cy = (lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0
    across = max(hi[0] - lo[0], hi[1] - lo[1])
    if across <= 0:
        raise ValueError("The fixing is flat - it needs some width.")
    return [tuple(((p[0] - cx) / across, (p[1] - cy) / across, (p[2] - lo[2]) / across) for p in t)
            for t in tris]


def _place_own(pts, faces, own, centre, up, u, turn, size):
    """A copy of your own fixing standing on 'centre', 'size' across, its front facing out.
    It sinks a little into the collar so it's held."""
    v0 = v_cross(up, u)
    c, s_ = math.cos(turn), math.sin(turn)
    uu = v_add(v_mul(u, c), v_mul(v0, s_))
    vv = v_cross(up, uu)
    sink = 0.05 * size
    index = {}
    for t in own:
        f = []
        for x, y, z in t:
            key = (round(x, 9), round(y, 9), round(z, 9))
            k = index.get(key)
            if k is None:
                q = v_add(centre, v_add(v_add(v_mul(uu, x * size), v_mul(vv, y * size)),
                                        v_mul(up, z * size - sink)))
                pts.append(q)
                k = index[key] = len(pts) - 1
            f.append(k)
        if len(set(f)) == 3:
            faces.append(f)


def build_collar(obj, base, opt, report=None):
    """A collar round the object where it meets the base: opt 'collar' = 'round' or 'square',
    'height' (up from the base), 'width' (how far it sticks out from the object), and
    'fixings' (none / nuts / bolts / rivets), 'count', 'fix_size' - all in model units.
    The bottom follows the base's curve and sinks into it. Returns (points, faces)."""
    report = report if report is not None else {}
    lines, tol, gbase, gobj = find_joins(obj, base, opt)
    h, w = float(opt.get('height', 0)), float(opt.get('width', 0))
    if h <= 0 or w <= 0:
        raise ValueError("The collar's height and width must both be more than 0.")
    cobj = centroid(obj)
    pts, faces = [], []
    report['loops'] = 0
    report['open'] = 0
    report['fixings'] = 0
    for line, closed in lines:
        if not closed:
            report['open'] += 1
            continue
        report['loops'] += 1
        P = resample(line, True, 128)
        mid = v_mul(tuple(map(sum, zip(*P))), 1.0 / len(P))
        # 'up': the way the base faces where the object stands
        acc = (0.0, 0.0, 0.0)
        ref = v_norm(v_sub(cobj, mid))
        for p in P[::8]:
            nb = surface_normal(gbase, p, w)
            if nb is not None:
                acc = v_add(acc, nb if v_dot(nb, ref) >= 0 else v_mul(nb, -1.0))
        up = v_norm(acc) if v_len(acc) > 0 else ref
        u, v = _frame(up)
        flat = [(v_dot(v_sub(p, mid), u), v_dot(v_sub(p, mid), v)) for p in P]
        if opt.get('collar') == 'square':
            hu = max(abs(a) for a, _ in flat) + w
            hv = max(abs(b) for _, b in flat) + w
            corners = [(hu, hv), (-hu, hv), (-hu, -hv), (hu, -hv)]
            outline = []
            per = 24
            for k in range(4):
                a, b = corners[k], corners[(k + 1) % 4]
                for t in range(per):
                    f = t / float(per)
                    outline.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
            fix_path = []
            for k in range(4):
                a = (corners[k][0] - w / 2.0 * (1 if corners[k][0] > 0 else -1),
                     corners[k][1] - w / 2.0 * (1 if corners[k][1] > 0 else -1))
                b = (corners[(k + 1) % 4][0] - w / 2.0 * (1 if corners[(k + 1) % 4][0] > 0 else -1),
                     corners[(k + 1) % 4][1] - w / 2.0 * (1 if corners[(k + 1) % 4][1] > 0 else -1))
                fix_path.append(a)
                fix_path.append(b)
            fix_path = [fix_path[i] for i in range(0, len(fix_path), 2)]
        else:
            # round: the object's own outline (seen from above), pushed out by the width
            outline, fix_path = [], []
            for a, b in flat:
                r = math.hypot(a, b) or 1e-12
                outline.append((a * (r + w) / r, b * (r + w) / r))
                fix_path.append((a * (r + w * 0.5) / r, b * (r + w * 0.5) / r))
        span = max(math.hypot(a, b) for a, b in outline) * 2.0 + h * 4.0
        # how high the base is under each point of the outline
        lift = []
        for a, b in outline:
            o = v_add(mid, v_add(v_mul(u, a), v_mul(v, b)))
            hit = _ray_down(gbase, v_add(o, v_mul(up, span)), v_mul(up, -1.0), span * 2.0)
            lift.append(v_dot(v_sub(hit, mid), up) if hit is not None else None)
        known = [x for x in lift if x is not None]
        if not known:
            raise ValueError("Couldn't find the base under the collar.")
        low = min(known)
        lift = [x if x is not None else low for x in lift]
        sink = max(h * 0.4, w * 0.3)

        def footprint(ang):
            """How far the object reaches from the middle, in a direction (seen from above)."""
            best, bd = None, 9.0
            for a, b in flat:
                d = abs(math.atan2(math.sin(math.atan2(b, a) - ang), math.cos(math.atan2(b, a) - ang)))
                if d < bd:
                    bd, best = d, math.hypot(a, b)
            return best or 0.0
        # the top: a flat-topped band from the outer edge in to just inside the object
        inner = []
        for a, b in outline:
            ang = math.atan2(b, a)
            r = footprint(ang) * 0.85
            inner.append((math.cos(ang) * r, math.sin(ang) * r))
        lift_in = []
        for a, b in inner:
            o = v_add(mid, v_add(v_mul(u, a), v_mul(v, b)))
            hit = _ray_down(gbase, v_add(o, v_mul(up, span)), v_mul(up, -1.0), span * 2.0)
            lift_in.append(v_dot(v_sub(hit, mid), up) if hit is not None else None)
        lift_in = [x if x is not None else low for x in lift_in]
        bot_c = v_add(mid, v_mul(up, low - sink))
        first = len(faces)
        start = len(pts)
        n = len(outline)
        for k, (a, b) in enumerate(outline):
            o = v_add(mid, v_add(v_mul(u, a), v_mul(v, b)))
            i_ = v_add(mid, v_add(v_mul(u, inner[k][0]), v_mul(v, inner[k][1])))
            pts.append(v_add(o, v_mul(up, lift[k] - sink)))      # under the base
            pts.append(v_add(o, v_mul(up, lift[k] + h)))         # the collar's top, outer edge
            pts.append(v_add(i_, v_mul(up, lift_in[k] + h)))     # inner edge, inside the object
        pts.append(bot_c)
        bc = len(pts) - 1
        for k in range(n):
            b0, t0, i0 = start + 3 * k, start + 3 * k + 1, start + 3 * k + 2
            k1 = (k + 1) % n
            b1, t1, i1 = start + 3 * k1, start + 3 * k1 + 1, start + 3 * k1 + 2
            faces.append([b0, b1, t1])
            faces.append([b0, t1, t0])
            faces.append([t0, t1, i1])
            faces.append([t0, i1, i0])
            faces.append([i0, i1, bc])
            faces.append([b1, b0, bc])
        _orient_shells(pts, faces, first)
        # the fixings, evenly round the middle of the collar's top
        kind = opt.get('fixings', 'none')
        count = int(opt.get('count', 0))
        fs = float(opt.get('fix_size', 0))
        own = opt.get('own_fixing') if kind == 'own' else None
        if (kind in FIXINGS[1:] or own) and count > 0 and fs > 0:
            path = fix_path + [fix_path[0]]
            seg = [math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]) for i in range(len(path) - 1)]
            total = sum(seg)
            for c in range(count):
                d = total * c / float(count)
                i, run = 0, 0.0
                while i < len(seg) - 1 and run + seg[i] < d:
                    run += seg[i]
                    i += 1
                f = 0.0 if seg[i] <= 0 else (d - run) / seg[i]
                a = path[i][0] + (path[i + 1][0] - path[i][0]) * f
                b = path[i][1] + (path[i + 1][1] - path[i][1]) * f
                o = v_add(mid, v_add(v_mul(u, a), v_mul(v, b)))
                hit = _ray_down(gbase, v_add(o, v_mul(up, span)), v_mul(up, -1.0), span * 2.0)
                base_h = v_dot(v_sub(hit, mid), up) if hit is not None else low
                centre = v_add(o, v_mul(up, base_h + h))
                # stand it square to the collar's top just there (the top follows the base's curve)
                nl = surface_normal(gbase, hit, fs) if hit is not None else None
                if nl is None:
                    nl = up
                elif v_dot(nl, up) < 0:
                    nl = v_mul(nl, -1.0)
                ul = v_sub(u, v_mul(nl, v_dot(u, nl)))
                ul = v_norm(ul) if v_len(ul) > 1e-9 else _frame(nl)[0]
                # the collar's top is h above the base along 'up': a sloping top needs a deeper seat
                slope = max(0.2, v_dot(nl, up))
                centre = v_add(hit, v_mul(nl, h * slope)) if hit is not None else centre
                ff = len(faces)
                if own:
                    _place_own(pts, faces, own, centre, nl, ul, math.atan2(b, a), fs)
                    report['fixings'] += 1
                    continue
                if kind == 'rivets':
                    _prism(pts, faces, centre, nl, ul, fs * 0.5, 10, fs * 0.45, fs * 0.2, dome=True)
                else:
                    turn = math.atan2(b, a)
                    nut_h = fs * (0.8 if kind == 'nuts' else 0.65)
                    _prism(pts, faces, centre, nl, ul, fs * 0.9, 6, nut_h, fs * 0.15, turn=turn)
                    if kind == 'nuts':     # the bolt's end poking out of the nut
                        _orient_shells(pts, faces, ff)
                        ff = len(faces)
                        top = v_add(centre, v_mul(nl, nut_h * 0.9))
                        _prism(pts, faces, top, nl, ul, fs * 0.5, 10, fs * 0.45, 0.0)
                _orient_shells(pts, faces, ff)
                report['fixings'] += 1
    if not faces:
        raise ValueError("A collar needs the object to stand wholly on the base (the join must go "
                         "all the way round).")
    return pts, faces


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


# ---------------------------------------------------------------------------
# Reading the two objects
# ---------------------------------------------------------------------------
def read_object(entity):
    """One selected group (or face) as (triangles, name, colour attrs of its first face)."""
    tris, attrs = [], None
    for outer, holes, f in world_loops([entity]):
        o = [(q.x(), q.y(), q.z()) for q in outer]
        hs = [[(q.x(), q.y(), q.z()) for q in h] for h in holes]
        tris.extend(triangulate_face(o, hs))
        if attrs is None:
            try:
                attrs = dict(getattr(f, 'attrs', None) or {})
            except Exception:
                attrs = {}
    name = str(getattr(entity, 'name', '') or '') or "Object"
    return tris, name, attrs or {}


def guess_unit(size):
    """IngeTrazo keeps models in metres. Only something over 500 'metres' across is taken to
    be a model drawn 1000 times big (millimetres drawn as metres)."""
    return "m" if max(size) < 500.0 else "mm"


def _face_normal(f):
    pts = []
    for v in _items(_val(f, 'vertices')):
        q = vertex_to_vector3d(v)
        if q is not None:
            pts.append((q.x(), q.y(), q.z()))
    return v_norm(newell(pts)) if len(pts) >= 3 else None


def soften_edges(mesh, faces_made, max_angle):
    """Softens (hides and smooths) every edge whose two faces meet at less than max_angle
    degrees, so the curve looks smooth. Sharp edges stay visible."""
    edges = _items(_val(mesh, 'edges'))
    if not edges:
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
    soft = 0
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
    return soft


OWN_DIR = os.path.join(os.path.expanduser("~"), ".ingetrazo_blend_fixings")


def _own_path(name):
    safe = "".join(ch for ch in name if ch not in '\\/:*?"<>|').strip() or "fixing"
    return os.path.join(OWN_DIR, safe + ".json")


def own_fixing_names():
    try:
        names = []
        for fn in sorted(os.listdir(OWN_DIR)):
            if fn.lower().endswith(".json"):
                names.append(fn[:-5])
        return names
    except Exception:
        return []


def save_own_fixing(name, tris):
    try:
        os.makedirs(OWN_DIR, exist_ok=True)
        path = _own_path(name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({'name': name, 'tris': [[list(p) for p in t] for t in tris]}, f)
        return os.path.basename(path)[:-5]
    except Exception:
        return None


def load_own_fixing(name):
    try:
        with open(_own_path(name), "r", encoding="utf-8") as f:
            d = json.load(f)
        return [tuple(tuple(float(c) for c in p) for p in t) for t in d.get('tris', [])]
    except Exception:
        return None


def delete_own_fixing(name):
    try:
        os.remove(_own_path(name))
    except Exception:
        pass


def _remove_group(scene, g):
    for fn in ('remove_group', 'delete_group', 'remove'):
        m = getattr(scene, fn, None)
        if callable(m):
            try:
                m(g)
                return True
            except Exception:
                pass
    lst = getattr(scene, 'groups', None)
    if isinstance(lst, list) and g in lst:
        lst.remove(g)
        return True
    return False


def make_in_model(viewport, pts, faces, name, paint, soften, replace=None):
    """The blend becomes a group of its own. One undo step. Returns (group, message, warning)."""
    stats = {'faces': 0, 'errors': 0, 'err': None, 'group': None, 'replaced': False}

    def mutate(scene):
        from core.mesh import Mesh
        from core.group import Group
        if replace is not None:
            stats['replaced'] = _remove_group(scene, replace)
        target = Mesh()
        V = [VertexWrapper(*p) for p in pts]       # shared corners, so faces share edges
        made = []
        for f in faces:
            if len(set(f)) < 3:
                continue
            try:
                nf = target.add_face([V[k] for k in f])
            except Exception as e:
                stats['errors'] += 1
                stats['err'] = e
                continue
            if nf is None:
                stats['errors'] += 1
                continue
            made.append(nf)
            stats['faces'] += 1
            if paint:
                try:
                    nf.attrs = dict(paint)
                except Exception:
                    pass
        if not made:
            raise RuntimeError("none of the faces could be made (%s)" % stats['err'])
        try:
            g = Group(target, name=name)
        except TypeError:
            g = Group(name)
            g.mesh = target
        try:
            g.name = name
        except Exception:
            pass
        if hasattr(scene, 'add_group'):
            scene.add_group(g)
        elif hasattr(scene, 'groups') and isinstance(scene.groups, list):
            scene.groups.append(g)
        else:
            raise RuntimeError("could not add the blend to the scene")
        stats['group'] = g
        for fn in ('recompute_normals', 'update_normals', 'rebuild', 'invalidate'):
            m = getattr(target, fn, None)
            if callable(m):
                try:
                    m()
                except Exception:
                    pass
        if soften:
            try:
                soften_edges(target, made, 40)
            except Exception:
                pass
    try:
        viewport.history.execute(SnapshotImport(mutate))
    except Exception as e:
        return None, "Making the blend failed: %s" % e, True
    try:
        viewport.notify_scene_changed()
    except Exception:
        pass
    msg = "Made '%s' (%d faces). Undo takes it away again." % (name, stats['faces'])
    if stats['replaced']:
        msg = "Replaced the last one. " + msg
    warn = False
    if stats['errors']:
        warn = True
        msg += ("\n%d tiny face%s couldn't be made: IngeTrazo treats points closer than 0.1 mm as one. "
                "Try a lower Smoothness, or a bigger blend." % (stats['errors'], "" if stats['errors'] == 1 else "s"))
    return stats['group'], msg, warn


# ---------------------------------------------------------------------------
# The window
# ---------------------------------------------------------------------------
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
                               QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox, QPushButton, QGroupBox)

EDDY_TIPS = {
    'Blend in': "The object that sits on or pokes into the base (the dome, the post, the handle). "
                "Swap changes which is which.",
    'Into': "What the object sits on (the boiler, the plinth, the mug).",
    'Swap': "Swaps the two over: which one is the object and which is the base.",
    'Shape': "The shape of the curve in the corner. Round is a quarter circle; Flared spreads further "
             "along the base, like a loco dome; Soft cove is gentler; Straight is a sloped fillet.",
    'Size': "How far the blend goes up the object, in mm (real size, before any scaling).",
    "Model's units": "IngeTrazo keeps models in metres, so this is nearly always Metres. Pick Millimetres "
                     "for a model drawn 1000 times big (1 metre in the model = 1 mm).",
    'Spread along the base': "How far the blend reaches out along the base, compared with how far up "
                             "the object it goes. 100% is even; more spreads it out wider.",
    'Smoothness': "How many steps make up the curve. Higher is smoother but has more faces.",
    'Every place they meet (both ends of a handle)': "Blends every separate place the two meet. "
                                                     "Untick to blend only the biggest one.",
    'Smooth finish (soften edges)': "Hides the edges between the blend's faces, so the curve looks smooth.",
    'Colour': "The blend's colour: like the object, like the base, or a colour of its own so it's easy to see.",
    'Making it again replaces the last blend': "Ticked: change a setting and press Make blend again to "
                                               "swap the last blend for the new one.",
    'Make blend': "Makes the blend in its own group. Undo takes it away again.",
    'Make collar': "Makes the collar (and its fixings) in its own group. Undo takes it away again.",
    'Join with': "A smooth blend (a curved fillet), or a collar round the object: round (following its "
                 "shape) or square. A collar can have nuts, bolt heads or rivets on top.",
    'Collar height': "How thick the collar is, above the base (real size, in mm).",
    'Collar width': "How far the collar sticks out from the object (real size, in mm).",
    'Fixings': "Nuts (with the bolt's end showing), hex bolt heads or round rivets, spaced evenly round the "
               "top of the collar.",
    'How many': "How many fixings, spaced evenly round the collar.",
    'Add my own fixing...': "Select something you've made (one group, standing upright the way it sits on "
                            "the collar), then click this. It's saved, and shows in the Fixings list as "
                            "'Mine: ...' for every collar from then on.",
    'Remove it': "Takes your own fixing that's picked in the Fixings list out of the list.",
    'Fixing size': "The bolt's size (its thread), in mm. The nut is about one and a half times that across. "
                   "For your own fixing: how wide it is across.",
    'Close': "Closes this window. Next time it opens in the same place, at the same size.",
}


class BlendDialog(QDialog):
    def __init__(self, viewport, tool=None):
        super().__init__(viewport)
        self.viewport = viewport
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.s = load_settings()
        self.objs = []           # [(tris, name, attrs, entity)]: [object, base]
        self._sel_key = None
        self._last = None
        self._loading = True
        lay = QVBoxLayout(self)

        self.lbl_help = QLabel("Select the two objects (Ctrl+click): the one to blend in, and what it "
                               "sits on. They need to overlap a little.")
        self.lbl_help.setWordWrap(True)
        lay.addWidget(self.lbl_help)

        pick = QGroupBox("The two objects")
        pf = QFormLayout(pick)
        self.lbl_obj = QLabel("-")
        self.lbl_base = QLabel("-")
        row = QHBoxLayout()
        row.addWidget(self.lbl_base, 1)
        self.b_swap = QPushButton("Swap")
        self.b_swap.clicked.connect(self.swap)
        row.addWidget(self.b_swap)
        pf.addRow("Blend in:", self.lbl_obj)
        pf.addRow("Into:", row)
        lay.addWidget(pick)

        jbox = QGroupBox("At the join")
        jf = QFormLayout(jbox)
        self.cb_join = QComboBox()
        for label, _ in JOINS:
            self.cb_join.addItem(label)
        jkeys = [k for _, k in JOINS]
        self.cb_join.setCurrentIndex(jkeys.index(self.s['join']) if self.s['join'] in jkeys else 0)
        jf.addRow("Join with:", self.cb_join)
        self.cb_unit = QComboBox()
        for label, _, _ in UNITS:
            self.cb_unit.addItem(label)
        jf.addRow("Model's units:", self.cb_unit)
        lay.addWidget(jbox)

        box = QGroupBox("The blend")
        self.box_blend = box
        form = QFormLayout(box)
        self.cb_shape = QComboBox()
        for label, _ in SHAPE_CHOICES:
            self.cb_shape.addItem(label)
        shapes = [k for _, k in SHAPE_CHOICES]
        self.cb_shape.setCurrentIndex(shapes.index(self.s['shape']) if self.s['shape'] in shapes else 0)
        form.addRow("Shape:", self.cb_shape)
        self.sp_size = QDoubleSpinBox()
        self.sp_size.setRange(0.01, 100000.0)
        self.sp_size.setDecimals(2)
        self.sp_size.setSuffix(" mm")
        self.sp_size.setValue(10.0)
        form.addRow("Size:", self.sp_size)
        self.sp_spread = QSpinBox()
        self.sp_spread.setRange(25, 400)
        self.sp_spread.setSuffix(" %")
        self.sp_spread.setValue(int(self.s['spread']))
        form.addRow("Spread along the base:", self.sp_spread)
        self.cb_smooth = QComboBox()
        for label, _, _ in SMOOTHNESS:
            self.cb_smooth.addItem(label)
        self.cb_smooth.setCurrentIndex(min(len(SMOOTHNESS) - 1, max(0, int(self.s['smooth']))))
        form.addRow("Smoothness:", self.cb_smooth)
        self.cb_col = QComboBox()
        for label, _ in COLOURS:
            self.cb_col.addItem(label)
        keys = [k for _, k in COLOURS]
        self.cb_col.setCurrentIndex(keys.index(self.s['colour']) if self.s['colour'] in keys else 0)
        form.addRow("Colour:", self.cb_col)
        lay.addWidget(box)

        cbox = QGroupBox("The collar")
        self.box_collar = cbox
        cf = QFormLayout(cbox)
        self.sp_ch = QDoubleSpinBox()
        self.sp_cw = QDoubleSpinBox()
        self.sp_fs = QDoubleSpinBox()
        for sp in (self.sp_ch, self.sp_cw, self.sp_fs):
            sp.setRange(0.01, 100000.0)
            sp.setDecimals(2)
            sp.setSuffix(" mm")
        cf.addRow("Collar height:", self.sp_ch)
        cf.addRow("Collar width:", self.sp_cw)
        self.cb_fix = QComboBox()
        self._fill_fixings(self.s['fixings'])
        cf.addRow("Fixings:", self.cb_fix)
        frow = QHBoxLayout()
        self.b_own = QPushButton("Add my own fixing...")
        self.b_own.clicked.connect(self.add_own)
        self.b_del_own = QPushButton("Remove it")
        self.b_del_own.clicked.connect(self.remove_own)
        frow.addWidget(self.b_own)
        frow.addWidget(self.b_del_own)
        cf.addRow(frow)
        self.sp_count = QSpinBox()
        self.sp_count.setRange(1, 200)
        self.sp_count.setValue(int(self.s['count']))
        cf.addRow("How many:", self.sp_count)
        cf.addRow("Fixing size:", self.sp_fs)
        lay.addWidget(cbox)

        obox = QGroupBox("Both")
        form = QFormLayout(obox)
        self.ck_all = QCheckBox("Every place they meet (both ends of a handle)")
        self.ck_all.setChecked(bool(self.s['all_loops']))
        form.addRow(self.ck_all)
        self.ck_soft = QCheckBox("Smooth finish (soften edges)")
        self.ck_soft.setChecked(bool(self.s['soften']))
        form.addRow(self.ck_soft)
        self.ck_replace = QCheckBox("Making it again replaces the last blend")
        self.ck_replace.setChecked(bool(self.s['replace']))
        form.addRow(self.ck_replace)
        lay.addWidget(obox)

        self.lbl_msg = QLabel("")
        self.lbl_msg.setWordWrap(True)
        lay.addWidget(self.lbl_msg)
        btns = QHBoxLayout()
        self.b_make = QPushButton("Make blend")
        self.b_make.setDefault(True)
        self.b_make.clicked.connect(self.make)
        b_close = QPushButton("Close")
        b_close.clicked.connect(self.close)
        btns.addStretch(1)
        btns.addWidget(self.b_make)
        btns.addWidget(b_close)
        lay.addLayout(btns)

        self.cb_unit.currentIndexChanged.connect(self._unit_changed)
        self.cb_join.currentIndexChanged.connect(self._join_changed)
        self.cb_fix.currentIndexChanged.connect(self._join_changed)
        self._join_changed()
        self._loading = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.watch_selection)
        self.timer.start(700)
        self.watch_selection(force=True)

    # ---- selection
    def selection(self):
        scene = getattr(self.viewport, 'scene', None)
        return list(getattr(scene, 'selection', None) or [])

    def watch_selection(self, force=False):
        try:
            if not force and not self.isVisible():
                return
        except Exception:
            pass
        ents = [e for e in self.selection() if _is_group(e)]
        key = tuple(id(e) for e in ents)
        if key == self._sel_key and not force:
            return
        self._sel_key = key
        self.objs = []
        if len(ents) != 2:
            self.lbl_obj.setText("-")
            self.lbl_base.setText("-")
            self.lbl_msg.setText("Select two objects (groups): Ctrl+click the second one." if len(ents) < 2 else
                                 "Select just two objects: the one to blend in, and what it sits on.")
            self.b_make.setEnabled(False)
            return
        try:
            got = []
            for e in ents:
                tris, name, attrs = read_object(e)
                got.append((tris, name, attrs, e))
        except Exception as e:
            self.lbl_msg.setText("Couldn't read the selection: %s" % e)
            self.b_make.setEnabled(False)
            return
        if not got[0][0] or not got[1][0]:
            self.lbl_msg.setText("One of the two has no faces to blend.")
            self.b_make.setEnabled(False)
            return

        def vol(t):
            lo, hi = bounds(t)
            return (hi[0] - lo[0]) * (hi[1] - lo[1]) * (hi[2] - lo[2])
        got.sort(key=lambda g: vol(g[0]))      # the smaller one is blended into the bigger one
        self.objs = got
        lo, hi = bounds(got[0][0] + got[1][0])
        self._loading = True
        self.cb_unit.setCurrentIndex([u[2] for u in UNITS].index(guess_unit([hi[i] - lo[i] for i in range(3)])))
        self._loading = False
        self._last = None
        self._suggest_size()
        self._show_names()
        self.lbl_msg.setText("")
        self.b_make.setEnabled(True)

    def _show_names(self):
        if len(self.objs) == 2:
            self.lbl_obj.setText(self.objs[0][1])
            self.lbl_base.setText(self.objs[1][1])

    def swap(self):
        if len(self.objs) == 2:
            self.objs.reverse()
            self._last = None
            self._show_names()
            self._suggest_size()

    def _mm_per_unit(self):
        return UNITS[self.cb_unit.currentIndex()][1]

    def _suggest_size(self):
        """A blend about an eighth of the object's width, to start with."""
        if len(self.objs) != 2:
            return
        lo, hi = bounds(self.objs[0][0])
        w = sorted([hi[i] - lo[i] for i in range(3)])[1]
        k = w * self._mm_per_unit()
        self.sp_size.setValue(max(0.01, round(k * float(self.s.get('size_frac', 0.12)), 2)))
        self.sp_ch.setValue(max(0.01, round(k * float(self.s.get('ch_frac', 0.06)), 2)))
        self.sp_cw.setValue(max(0.01, round(k * float(self.s.get('cw_frac', 0.15)), 2)))
        self.sp_fs.setValue(max(0.01, round(k * float(self.s.get('fs_frac', 0.06)), 2)))

    def _join_changed(self, *_):
        j = JOINS[self.cb_join.currentIndex()][1]
        self.box_blend.setVisible(j == 'blend')
        self.box_collar.setVisible(j != 'blend')
        fx = self._fix_key() != 'none'
        self.sp_count.setEnabled(fx)
        self.sp_fs.setEnabled(fx)
        self.b_del_own.setEnabled(self._fix_key().startswith('own:'))
        self.b_make.setText("Make blend" if j == 'blend' else "Make collar")
        try:
            self.adjustSize()
        except Exception:
            pass

    # ---- your own fixings
    def _fill_fixings(self, want=None):
        self._loading_fix = True
        self.fix_items = [(label, key) for label, key in FIXING_CHOICES]
        for name in own_fixing_names():
            self.fix_items.append(("Mine: %s" % name, "own:" + name))
        try:
            self.cb_fix.clear()
        except Exception:
            self.cb_fix.items = []
        for label, _ in self.fix_items:
            self.cb_fix.addItem(label)
        keys = [k for _, k in self.fix_items]
        self.cb_fix.setCurrentIndex(keys.index(want) if want in keys else 0)
        self._loading_fix = False

    def _fix_key(self):
        i = self.cb_fix.currentIndex()
        return self.fix_items[i][1] if 0 <= i < len(self.fix_items) else 'none'

    def add_own(self):
        from PySide6.QtWidgets import QInputDialog
        ents = [e for e in self.selection() if _is_group(e)]
        if len(ents) != 1:
            self.lbl_msg.setText("To add your own fixing: select just the fixing (one group, standing upright "
                                 "the way it sits on the collar), then click Add my own fixing.")
            return
        try:
            tris, name, _ = read_object(ents[0])
            own = own_fixing_from(tris)
        except Exception as e:
            self.lbl_msg.setText("Couldn't use that as a fixing: %s" % e)
            return
        text, ok = QInputDialog.getText(self, PLUGIN_NAME, "A name for this fixing:", text=name)
        if not ok or not str(text).strip():
            return
        name = save_own_fixing(str(text).strip(), own)
        if not name:
            self.lbl_msg.setText("Couldn't save the fixing.")
            return
        self._fill_fixings("own:" + name)
        self._join_changed()
        self.lbl_msg.setText("Saved '%s' (%d faces). It's in the Fixings list now, for every collar. "
                             "Select your two objects again to make one." % (name, len(own)))

    def remove_own(self):
        key = self._fix_key()
        if not key.startswith('own:'):
            return
        delete_own_fixing(key[4:])
        self._fill_fixings('none')
        self._join_changed()
        self.lbl_msg.setText("Removed '%s' from the list." % key[4:])

    def _unit_changed(self, *_):
        if not self._loading:
            self._suggest_size()

    # ---- making it
    def _read(self):
        s = dict(self.s)
        s['shape'] = SHAPE_CHOICES[self.cb_shape.currentIndex()][1]
        s['spread'] = self.sp_spread.value()
        s['smooth'] = self.cb_smooth.currentIndex()
        s['colour'] = COLOURS[self.cb_col.currentIndex()][1]
        s['all_loops'] = self.ck_all.isChecked()
        s['soften'] = self.ck_soft.isChecked()
        s['replace'] = self.ck_replace.isChecked()
        s['join'] = JOINS[self.cb_join.currentIndex()][1]
        s['fixings'] = self._fix_key()
        s['count'] = self.sp_count.value()
        return s

    def make(self):
        if len(self.objs) != 2:
            return
        s = self._read()
        obj, base = self.objs
        mmu = self._mm_per_unit()
        size = self.sp_size.value() / mmu
        _, stations, steps = SMOOTHNESS[s['smooth']]
        opt = {'size': size, 'spread': s['spread'] / 100.0, 'shape': s['shape'], 'stations': stations,
               'steps': steps, 'all_loops': s['all_loops'], 'collar': s['join'],
               'height': self.sp_ch.value() / mmu, 'width': self.sp_cw.value() / mmu,
               'fixings': s['fixings'], 'count': s['count'], 'fix_size': self.sp_fs.value() / mmu}
        if s['fixings'].startswith('own:'):
            opt['fixings'] = 'own'
            opt['own_fixing'] = load_own_fixing(s['fixings'][4:])
            if not opt['own_fixing']:
                self.lbl_msg.setText("Couldn't load your fixing '%s'." % s['fixings'][4:])
                return
        report = {}
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            if s['join'] == 'blend':
                pts, faces = build_blend(obj[0], base[0], opt, report)
            else:
                pts, faces = build_collar(obj[0], base[0], opt, report)
        except ValueError as e:
            self.lbl_msg.setText(str(e))
            return
        except Exception as e:
            self.lbl_msg.setText("Couldn't make the blend: %s" % e)
            return
        finally:
            QApplication.restoreOverrideCursor()
        # remember the settings (and the size as a share of the object, for next time)
        lo, hi = bounds(obj[0])
        w = sorted([hi[i] - lo[i] for i in range(3)])[1]
        if w > 0:
            if s['join'] == 'blend':
                s['size_frac'] = max(0.01, min(1.0, size / w))
            else:
                s['ch_frac'] = max(0.005, min(1.0, opt['height'] / w))
                s['cw_frac'] = max(0.005, min(1.0, opt['width'] / w))
                s['fs_frac'] = max(0.005, min(1.0, opt['fix_size'] / w))
        self.s = s
        save_settings(s)
        paint = None
        if s['colour'] == 'own':
            paint = {"color": OWN_COLOUR}
        else:
            src = obj[2] if s['colour'] == 'object' else base[2]
            paint = dict(src) if src else None
        replace = self._last if s['replace'] else None
        g, msg, warn = make_in_model(self.viewport, pts, faces, "%s %s" % (obj[1], "blend" if s['join'] == 'blend'
                                                                             else "collar"), paint, s['soften'], replace)
        if g is not None:
            self._last = g
        notes = []
        if report.get('loops', 0) > 1:
            notes.append("Blended %d places where they meet." % report['loops'])
        if report.get('open'):
            notes.append("The object runs off the edge of the base, so the blend has flat ends there."
                         if s['join'] == 'blend' else
                         "Where the object runs off the edge of the base there's no collar (it needs to go "
                         "all the way round).")
        if report.get('too_big'):
            notes.append("The blend is big for the object: if it looks crumpled, make the Size smaller.")
        self.lbl_msg.setText(msg + ("\n" + "\n".join(notes) if notes else ""))
        # keep the same two objects picked (the new blend may now be selected)
        self._sel_key = tuple(id(e) for e in self.selection() if _is_group(e))

    def closeEvent(self, ev):
        try:
            self.timer.stop()
        except Exception:
            pass
        try:
            save_settings(self._read())
        except Exception:
            pass
        super().closeEvent(ev)


class BlendTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Shift+B"
    description = ("Blends one object smoothly into another where they meet - a dome into a boiler, "
                   "a post into a plinth, a handle onto a mug - with a curved fillet, ready to print.")
    _dialog = None

    def on_activate(self, viewport):
        dlg = BlendTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.raise_()
                    dlg.activateWindow()
                    dlg.watch_selection(force=True)
                    return
            except Exception:
                pass
        dlg = BlendDialog(viewport, self)
        BlendTool._dialog = dlg

        def closed(*_):
            BlendTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass


def _find_viewport():
    """Finds the IngeTrazo viewport: the widget that has a scene and an undo history."""
    for w in QApplication.allWidgets():
        if hasattr(w, 'scene') and hasattr(w, 'history') and hasattr(w, 'notify_scene_changed'):
            return w
    return None


def run(viewport=None):
    """Console entry point: select the two objects, then call run()."""
    viewport = viewport or _find_viewport()
    if viewport is None:
        print("%s: could not find the viewport. Call run(<your viewport>) instead." % PLUGIN_NAME)
        return
    BlendTool().on_activate(viewport)
