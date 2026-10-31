# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Wrap for IngeTrazo
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
3D Wrap - bend a flat pattern round a chimney (like SketchUp's Flowify), for IngeTrazo
Pick a flat pattern standing upright - a panel of bricks from Brick & Block Studio, boards
from Wood Planking, anything in a group - and a target: a round, square or octagonal
chimney made to size (straight or tapered), or any upright solid you've drawn (the Loft
plugin makes good tapered chimneys). The pattern is bent round it: its width goes round
the girth, its height up the side, and its thickness stands out from the surface. On a
tapered chimney everything gets narrower towards the top, as it does with Flowify.

Or skip the pattern and lay new bricks straight onto the target, course by course: every
course is a whole number of bricks (never longer than a standard brick), so there's no seam.

The flat pattern is left as it was; the wrapped copy is a new group. Ctrl+Alt+U.
"""

import math
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QCheckBox,
                               QDoubleSpinBox, QSpinBox, QPushButton, QLabel, QMessageBox,
                               QTabWidget, QWidget)

PLUGIN_NAME = "3D Wrap"
VERSION = "7"
SCALE = 0.001
Z = (0.0, 0.0, 1.0)

# ---------------------------------------------------------------------------
# Geometry helpers (shared with 3D Wood Planking)
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




# ---------------------------------------------------------------------------
# Reading groups (meshes, with any placement transform), in world metres
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


def _xform_fn(xf):
    if xf is None:
        return None
    try:
        if hasattr(xf, 'isIdentity') and xf.isIdentity():
            return None
    except Exception:
        pass
    if hasattr(xf, 'map'):
        def f(p):
            q = xf.map(QVector3D(*p))
            return (q.x(), q.y(), q.z())
        return f
    return None


def group_faces(g, fn=None, depth=0):
    """[(outer loop, [hole loops])] of a group and its children, in world coordinates."""
    out = []
    if depth > 40:
        return out
    own = _xform_fn(getattr(g, 'xform', None))
    if own is not None and fn is not None:
        f = (lambda p, a=own, b=fn: b(a(p)))
    else:
        f = own or fn or (lambda p: p)
    mesh = getattr(g, 'mesh', None)
    for face in _items(getattr(mesh, 'faces', None)):
        pts = [p for p in (_pos(q) for q in _items(getattr(face, 'vertices', None))) if p is not None]
        if len(pts) < 3:
            continue
        holes = []
        for h in _items(getattr(face, 'holes', None)):
            hp = [p for p in (_pos(q) for q in _items(h)) if p is not None]
            if len(hp) >= 3:
                holes.append([f(p) for p in hp])
        out.append(([f(p) for p in pts], holes))
    for c in _items(getattr(g, 'children', None)):
        out += group_faces(c, f, depth + 1)
    return out


def selected_groups(scene):
    return [e for e in _items(getattr(scene, 'selection', None))
            if getattr(e, 'mesh', None) is not None or getattr(e, 'children', None)]


def group_label(g):
    for a in ('name', 'label'):
        n = getattr(g, a, None)
        if isinstance(n, str) and n:
            return n
    return "group"


# ---------------------------------------------------------------------------
# The pattern's own frame: u along it, v up, w out of its front
# ---------------------------------------------------------------------------
def pattern_frame(faces, target_axis=None, flip=False):
    pts = [p for o, hs in faces for p in o]
    if not pts:
        raise ValueError("The pattern group is empty.")
    n = len(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - cx) ** 2 for p in pts)
    syy = sum((p[1] - cy) ** 2 for p in pts)
    sxy = sum((p[0] - cx) * (p[1] - cy) for p in pts)
    a = 0.5 * math.atan2(2 * sxy, sxx - syy)          # the long way across, seen from above
    U = (math.cos(a), math.sin(a), 0.0)
    W = (-U[1], U[0], 0.0)
    # which side is the front? The back is flat: one big face (a backing), or the most
    # faces lying in its plane (the backs of the bricks; kicked-out bricks only stand
    # out at the front)
    ws_ = [v_dot(p, W) for p in pts]
    lo, hi = min(ws_), max(ws_)
    tol = max(1e-6, (hi - lo) * 0.02)
    us_ = [v_dot(p, (-W[1], W[0], 0.0)) for p in pts]
    panel = (max(us_) - min(us_)) * (max(p[2] for p in pts) - min(p[2] for p in pts)) or 1.0
    score = {}
    for side, wv in (('lo', lo), ('hi', hi)):
        cnt, big = 0, 0.0
        for o, hs in faces:
            if all(abs(v_dot(p, W) - wv) < tol for p in o):
                cnt += 1
                nn = _newell3(o)
                big = max(big, 0.5 * math.sqrt(nn[0] ** 2 + nn[1] ** 2 + nn[2] ** 2))
        score[side] = (big > 0.5 * panel, cnt)
    back_lo = None
    if score['lo'][0] != score['hi'][0]:
        back_lo = score['lo'][0]
    elif score['lo'][1] != score['hi'][1]:
        back_lo = score['lo'][1] > score['hi'][1]
    elif target_axis is not None:
        # can't tell: the front faces away from the target
        back_lo = (cx - target_axis[0]) * W[0] + (cy - target_axis[1]) * W[1] >= 0
    if back_lo is False:
        W = (-W[0], -W[1], 0.0)
    if flip:
        W = (-W[0], -W[1], 0.0)
    U = v_cross(Z, W)                                   # so that u x v = w (right-handed)
    us = [v_dot(p, U) for p in pts]
    vs = [p[2] for p in pts]
    ws = [v_dot(p, W) for p in pts]
    return {'U': U, 'W': W, 'u0': min(us), 'u1': max(us), 'v0': min(vs), 'v1': max(vs),
            'w0': min(ws), 'w1': max(ws), 'c': (cx, cy)}


def to_uvw(p, fr):
    return (v_dot(p, fr['U']) - fr['u0'], p[2] - fr['v0'], v_dot(p, fr['W']) - fr['w0'])


# ---------------------------------------------------------------------------
# Cutting faces on a grid, so they can bend
# ---------------------------------------------------------------------------
def clip3(poly, k, c, keep_below):
    """Clip a 3-D polygon by the plane (coordinate k) = c."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp = (c - p[k]) if keep_below else (p[k] - c)
        fq = (c - q[k]) if keep_below else (q[k] - c)
        if fp >= 0:
            out.append(p)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            out.append(tuple(p[j] + t * (q[j] - p[j]) for j in range(3)))
    return out


def slice_at(polys, k, values):
    """Cut every polygon at k = each of the values."""
    for c in values:
        nxt = []
        for P in polys:
            lo = min(p[k] for p in P)
            hi = max(p[k] for p in P)
            if lo + 1e-12 < c < hi - 1e-12:
                for keep in (True, False):
                    q = clip3(P, k, c, keep)
                    if len(q) >= 3:
                        nxt.append(q)
            else:
                nxt.append(P)
        polys = nxt
    return polys


def slice_axis(polys, k, step):
    """Cut every polygon at k = multiples of step."""
    out = []
    for P in polys:
        lo = min(p[k] for p in P)
        hi = max(p[k] for p in P)
        a = math.floor(lo / step)
        b = math.ceil(hi / step)
        if b - a <= 1:
            out.append(P)
            continue
        for i in range(a, b):
            c0, c1 = i * step, (i + 1) * step
            q = clip3(P, k, c0, False)
            if len(q) >= 3:
                q = clip3(q, k, c1, True)
            if len(q) >= 3:
                out.append(q)
    return out


def face_pieces(outer, holes, du, dv):
    """A (planar) face in pattern coordinates, cut into small planar pieces at the grid
    lines u = i du, v = j dv. Pieces with holes are cut round the holes."""
    pieces = slice_axis(slice_axis([outer], 0, du), 1, dv)
    if not holes:
        return pieces
    # take the holes away: work in the face's own 2-D plane
    n = _newell3(outer)
    k = max(range(3), key=lambda i: abs(n[i]))
    ax = [i for i in range(3) if i != k]

    def to2(p):
        return (p[ax[0]], p[ax[1]])
    d = -v_dot(n, outer[0])

    def to3(q):
        p = [0.0, 0.0, 0.0]
        p[ax[0]], p[ax[1]] = q
        p[k] = -(d + n[ax[0]] * q[0] + n[ax[1]] * q[1]) / n[k]
        return tuple(p)
    hole_parts = [hp for h in holes for hp in convex_parts([to2(p) for p in h])]
    out = []
    for pc in pieces:
        q = clean([to2(p) for p in pc])
        if q is None:
            continue
        parts = [q]
        for hp in hole_parts:
            nxt = []
            for a in parts:
                A, B = bbox(a), bbox(hp)
                if A[1] <= B[0] or B[1] <= A[0] or A[3] <= B[2] or B[3] <= A[2]:
                    nxt.append(a)
                else:
                    nxt += subtract_convex(a, hp)
            parts = nxt
        for a in parts:
            out.append([to3(p) for p in a])
    return out


def _newell3(pts):
    nx = ny = nz = 0.0
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    return (nx, ny, nz)


def _planar(q, rel=1e-5):
    n = _newell3(q)
    L = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
    if L < 1e-18:
        return False
    n = (n[0] / L, n[1] / L, n[2] / L)
    d0 = v_dot(n, q[0])
    size = max(max(abs(a[i] - b[i]) for i in range(3)) for a in q for b in q[:1]) or 1.0
    return all(abs(v_dot(n, p) - d0) <= rel * size + 1e-9 for p in q)


def triangles(piece):
    """A planar piece (convex or not) as triangles, keeping its winding."""
    if len(piece) == 3:
        return [piece]
    n = _newell3(piece)
    k = max(range(3), key=lambda i: abs(n[i]))
    ax = [i for i in range(3) if i != k]
    pts2 = [(p[ax[0]], p[ax[1]]) for p in piece]
    if is_convex(pts2):
        return [[piece[0], piece[i], piece[i + 1]] for i in range(1, len(piece) - 1)]
    idx = {}
    for q, p in zip(pts2, piece):
        idx[q] = p
    flip = area2(pts2) < 0
    poly = pts2[::-1] if flip else pts2
    tris = [[idx[q] for q in t] for t in ear_clip(poly)]
    return [t[::-1] for t in tris] if flip else tris


# ---------------------------------------------------------------------------
# Targets: how far out the surface is, at an angle round the axis and a height
# ---------------------------------------------------------------------------
class ShapeTarget:
    """A made-to-measure chimney (round, square or octagonal, straight or tapered)."""

    def __init__(self, shape, cx, cy, z0, h, bottom, top):
        self.shape, self.cx, self.cy, self.z0, self.h = shape, cx, cy, z0, h
        self.rb, self.rt = bottom / 2.0, top / 2.0

    def half(self, z):
        t = min(1.0, max(0.0, (z - self.z0) / self.h)) if self.h > 0 else 0.0
        return self.rb + (self.rt - self.rb) * t

    def r(self, th, z):
        a = self.half(z)
        if self.shape == 'square':
            return a / max(abs(math.cos(th)), abs(math.sin(th)))
        if self.shape == 'octagon':
            k = (th % (math.pi / 4)) - math.pi / 8
            return a / math.cos(k)
        return a

    def corners(self):
        if self.shape == 'square':
            return [math.pi / 4 + k * math.pi / 2 for k in range(4)]
        if self.shape == 'octagon':
            return [math.pi / 8 + k * math.pi / 4 for k in range(8)]
        return []

    def solid_faces(self, n=48):
        """The chimney itself (world metres), as faces, for adding as its own group."""
        if self.shape == 'square':
            angs = [math.pi / 4 + k * math.pi / 2 for k in range(4)]
        elif self.shape == 'octagon':
            angs = [math.pi / 8 + k * math.pi / 4 for k in range(8)]
        else:
            angs = [2 * math.pi * k / n for k in range(n)]
        z1 = self.z0 + self.h
        lo = [(self.cx + self.r(a, self.z0) * math.cos(a), self.cy + self.r(a, self.z0) * math.sin(a), self.z0) for a in angs]
        hi = [(self.cx + self.r(a, z1) * math.cos(a), self.cy + self.r(a, z1) * math.sin(a), z1) for a in angs]
        faces = [hi, lo[::-1]]
        m = len(angs)
        for i in range(m):
            j = (i + 1) % m
            faces.append([lo[i], lo[j], hi[j], hi[i]])
        return faces


class MeshTarget:
    """Any upright solid you've drawn: it's sliced level at many heights and the outside
    found all the way round, from its upright middle line."""

    def __init__(self, faces, n_ang=180, n_z=None, ignore=0.1):
        tris = []
        for o, hs in faces:
            for t in triangles(o):
                tris.append(t)
        if not tris:
            raise ValueError("The target group has no faces.")
        xs = [p[0] for t in tris for p in t]
        ys = [p[1] for t in tris for p in t]
        zs = [p[2] for t in tris for p in t]
        self.cx, self.cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        self.z0, self.z1 = min(zs), max(zs)
        self.h = self.z1 - self.z0
        if self.h <= 0:
            raise ValueError("The target needs some height (an upright solid, such as a chimney).")
        if n_z is None:
            n_z = int(min(400, max(80, self.h / 0.02)))     # about every 20 mm up the target
        self.na, self.nz = n_ang, n_z
        self._tris = tris
        # a square, octagonal (or any flat-sided) drawn chimney: find its corners, so the
        # sides are laid flat and the corners bonded, as on a made-to-size one
        self._corners = self._find_corners()
        angs = [2 * math.pi * ia / n_ang for ia in range(n_ang)]
        for c in self._corners:
            angs = [a for a in angs if abs((a - c + math.pi) % (2 * math.pi) - math.pi) > 1e-4]
        self.angs = sorted(angs + list(self._corners))
        self.na = len(self.angs)
        grid = []
        for iz in range(n_z + 1):
            z = self.z0 + self.h * (0.002 + 0.996 * iz / n_z)
            grid.append(self._rays(self._slice(z), self.angs))
        self._tris = None
        # fill any misses from the neighbours
        for row in grid:
            if not any(row):
                continue
            na = len(row)
            for i in range(na):
                if row[i] == 0.0:
                    j = 1
                    while j < na and row[(i - j) % na] == 0.0 and row[(i + j) % na] == 0.0:
                        j += 1
                    row[i] = max(row[(i - j) % na], row[(i + j) % na])
        good = [r for r in grid if any(r)]
        if not good:
            raise ValueError("Couldn't find the outside of the target all the way round its middle.")
        # a level where nothing was found takes the nearest levels above and below
        have = [i for i, row in enumerate(grid) if any(row)]
        for i, row in enumerate(grid):
            if any(row):
                continue
            lo = max([j for j in have if j < i], default=None)
            hi = min([j for j in have if j > i], default=None)
            if lo is None or hi is None:
                grid[i] = list(grid[hi if lo is None else lo])
            else:
                t_ = (i - lo) / float(hi - lo)
                grid[i] = [a * (1 - t_) + b * t_ for a, b in zip(grid[lo], grid[hi])]
        # leave out thin rims sticking out (a stray face, a thin disc at a joint): anything
        # standing out over less than `ignore` metres of height is shaved off. Wider bands,
        # steps and tapers stay as they are (a grey 'opening' up each line of the grid).
        dz = self.h / n_z
        k = int(round(ignore / dz / 2.0)) if ignore > 0 else 0
        if k >= 1:
            for ia in range(self.na):
                col = [grid[iz][ia] for iz in range(n_z + 1)]
                ero = [min(col[max(0, i - k):i + k + 1]) for i in range(n_z + 1)]
                opn = [max(ero[max(0, i - k):i + k + 1]) for i in range(n_z + 1)]
                for iz in range(n_z + 1):
                    grid[iz][ia] = opn[iz]
        self.grid = grid

    def _slice(self, z):
        segs = []
        for t in self._tris:
            pts = []
            for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                # half-open test: a corner exactly at this height counts as below, so a
                # slice through a ring of corners still finds the whole outline
                if (a[2] <= z) != (b[2] <= z):
                    s_ = (z - a[2]) / (b[2] - a[2])
                    pts.append((a[0] + s_ * (b[0] - a[0]) - self.cx, a[1] + s_ * (b[1] - a[1]) - self.cy))
            if len(pts) == 2:
                segs.append(pts)
        return segs

    @staticmethod
    def _rays(segs, angs):
        row = []
        for th in angs:
            dx, dy = math.cos(th), math.sin(th)
            best = 0.0
            for (ax_, ay_), (bx_, by_) in segs:
                ex, ey = bx_ - ax_, by_ - ay_
                den = dx * ey - dy * ex
                if abs(den) < 1e-15:
                    continue
                tt = (ax_ * ey - ay_ * ex) / den          # distance along the ray
                ss = (ax_ * dy - ay_ * dx) / den          # where on the segment
                if tt > 0 and -1e-9 <= ss <= 1 + 1e-9:
                    best = max(best, tt)
            row.append(best)
        return row

    def _find_corners(self, n=720):
        """The corners of a flat-sided outline (the same at a few heights), or [] for a
        round or curved one."""
        found = None
        for fz in (0.3, 0.5, 0.7):
            z = self.z0 + self.h * fz
            angs = [2 * math.pi * k / n for k in range(n)]
            rr = self._rays(self._slice(z), angs)
            if not all(rr):
                return []
            P = [(r_ * math.cos(a), r_ * math.sin(a)) for r_, a in zip(rr, angs)]
            d = [math.atan2(P[(k + 1) % n][1] - P[k][1], P[(k + 1) % n][0] - P[k][0]) for k in range(n)]
            turn = [(d[k] - d[k - 1] + math.pi) % (2 * math.pi) - math.pi for k in range(n)]
            sharp = [abs(t_) > math.radians(4.0) for t_ in turn]
            if not any(sharp):
                return []
            # runs of sharp turns are one corner each
            k0 = next(k for k in range(n) if not sharp[k])
            runs, cur = [], []
            for kk in range(n):
                k = (k0 + kk) % n
                if sharp[k]:
                    cur.append(k)
                elif cur:
                    runs.append(cur)
                    cur = []
            if cur:
                runs.append(cur)
            if not 3 <= len(runs) <= 16:
                return []
            cs = []
            for run in runs:
                tot = sum(turn[k] for k in run)
                if abs(tot) < math.radians(15.0):
                    return []                     # a soft bend, not a corner
                a, b = run[0], run[-1]            # straight lines either side of the corner
                p1, p2 = P[(a - 3) % n], P[(a - 1) % n]
                q1, q2 = P[(b + 1) % n], P[(b + 3) % n]
                ux, uy = p2[0] - p1[0], p2[1] - p1[1]
                vx, vy = q2[0] - q1[0], q2[1] - q1[1]
                den = ux * vy - uy * vx
                if abs(den) < 1e-12:
                    return []
                t_ = ((q1[0] - p1[0]) * vy - (q1[1] - p1[1]) * vx) / den
                cx_, cy_ = p1[0] + ux * t_, p1[1] + uy * t_
                ang = math.atan2(cy_, cx_) % (2 * math.pi)
                if 2 * math.pi - ang < 1e-6:
                    ang = 0.0
                cs.append(ang)
            cs.sort()
            # every side must be straight (a D-shaped or curved side isn't a flat side)
            for i in range(len(cs)):
                a0, a1 = cs[i], cs[(i + 1) % len(cs)] + (2 * math.pi if i == len(cs) - 1 else 0.0)
                ks = [k for k in range(n) if a0 + 0.01 < angs[k] + (2 * math.pi if angs[k] < a0 else 0.0) < a1 - 0.01]
                if len(ks) < 3:
                    continue
                pa, pb = P[ks[0]], P[ks[-1]]
                L_ = math.hypot(pb[0] - pa[0], pb[1] - pa[1]) or 1.0
                dev = max(abs((P[k][0] - pa[0]) * (pb[1] - pa[1]) - (P[k][1] - pa[1]) * (pb[0] - pa[0])) / L_
                          for k in ks)
                if dev > max(0.002, 0.004 * L_):
                    return []
            if found is None:
                found = cs
            elif len(found) != len(cs) or any(
                    min(abs((a - b + math.pi) % (2 * math.pi) - math.pi) for b in cs) > math.radians(1.0)
                    for a in found):
                return []                         # the corners twist up the chimney
        return found or []

    def corners(self):
        return list(self._corners)

    def r(self, th, z):
        import bisect
        th = th % (2 * math.pi)
        A = self.angs
        k = bisect.bisect_right(A, th)
        a0i, a1i = (k - 1) % self.na, k % self.na
        a0, a1 = A[a0i], A[a1i]
        span = (a1 - a0) % (2 * math.pi) or 2 * math.pi
        ta = ((th - a0) % (2 * math.pi)) / span
        fz = min(max((z - self.z0) / self.h, 0.0), 1.0) * self.nz
        iz = min(int(math.floor(fz)), self.nz - 1)
        tz = fz - iz
        g = self.grid
        r0 = g[iz][a0i] * (1 - ta) + g[iz][a1i] * ta
        r1 = g[iz + 1][a0i] * (1 - ta) + g[iz + 1][a1i] * ta
        return r0 * (1 - tz) + r1 * tz


# ---------------------------------------------------------------------------
# Wrapping
# ---------------------------------------------------------------------------
def wrap(faces, target, v):
    """Bend the pattern's faces round the target. Returns ([triangles in world metres], info)."""
    fr = pattern_frame(faces, (target.cx, target.cy), v['flip'])
    W_ = fr['u1'] - fr['u0']
    H_ = fr['v1'] - fr['v0']
    D_ = fr['w1'] - fr['w0']
    if W_ <= 0 or H_ <= 0:
        raise ValueError("The pattern needs some width and height (a flat panel, standing up).")
    zb = target.z0 + v['raise'] * SCALE
    rb = max(1e-6, sum(target.r(2 * math.pi * k / 36, zb) for k in range(36)) / 36)
    copies = 1
    if v['fit'] == 'round':
        ku = 2 * math.pi / W_                       # once all the way round
    elif v['fit'] == 'repeat':
        # as many copies side by side as go round, eased a little so they close up exactly
        copies = max(1, int(round(2 * math.pi * rb / W_)))
        ku = 2 * math.pi / (copies * W_)
    else:
        ku = 1.0 / rb                               # true width, measured round the bottom
    if v['height_fit'] == 'stretch':
        kv = (target.z0 + target.h - zb) / H_
    else:
        kv = 1.0
    kw = 1.0 if not v['scale_depth'] else kv
    th0 = math.radians(v['start'])
    lift = v['lift'] * SCALE
    # grid size: small enough to follow the curve
    du = min(max(v['detail'] * SCALE, 1e-5), 2 * math.pi / ku / 24.0 if ku > 0 else W_)
    dv = max(v['detail'] * SCALE, 1e-5) * 4.0

    def surf(th, z):
        r = target.r(th, z)
        return (target.cx + r * math.cos(th), target.cy + r * math.sin(th))

    def place(p):
        u, vv, w = p
        th = th0 + u * ku
        z = zb + vv * kv
        # stand out square to the surface (so flat sides stay flat), mitred at corners
        e = 1e-5
        a, b = surf(th - e, z), surf(th + e, z)
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1.0
        nx, ny = ty / L, -tx / L
        x, y = surf(th, z)
        d = lift + w * kw
        return (x + nx * d, y + ny * d, z)
    # small solids (bricks, pales) stay flat-faced like the real thing: a flat face bent
    # round a cone or cylinder stays flat when it's just moved, not cut. Big ones (a backing,
    # long boards) are cut on a grid so they follow the curve. Decided per solid, so the
    # faces of one solid always meet edge to edge.
    uvw0 = [([to_uvw(p, fr) for p in o], [[to_uvw(p, fr) for p in h] for h in hs]) for o, hs in faces]
    uvw = []
    copy_of = []
    for k in range(copies):
        du_ = k * W_
        uvw += [([(p[0] + du_, p[1], p[2]) for p in o], [[(p[0] + du_, p[1], p[2]) for p in h] for h in hs])
                for o, hs in uvw0]
        copy_of += [k] * len(uvw0)
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    keyed = []
    for (o, hs), ck in zip(uvw, copy_of):
        # (each copy on its own: bricks of two copies touching at a join stay apart)
        ks = [(ck,) + tuple(round(c / 1e-7) for c in p) for p in o]
        keyed.append(ks)
        for k_ in ks[1:]:
            ra, rb_ = find(ks[0]), find(k_)
            if ra != rb_:
                parent[ra] = rb_
    span = {}
    for (o, hs), ks in zip(uvw, keyed):
        r = find(ks[0])
        lo, hi, wl, wh, vl, vh = span.get(r, (1e18, -1e18, 1e18, -1e18, 1e18, -1e18))
        us = [p[0] for p in o]
        ws = [p[2] for p in o]
        vs = [p[1] for p in o]
        span[r] = (min(lo, min(us)), max(hi, max(us)), min(wl, min(ws)), max(wh, max(ws)),
                   min(vl, min(vs)), max(vh, max(vs)))
    flat_max = max(0.0, v.get('flat_max', 300.0)) * SCALE
    # the corners of a square or octagonal chimney: every face is folded there
    cu = []
    period = 2 * math.pi / ku
    for c in (target.corners() if hasattr(target, 'corners') else []):
        u = ((c - th0) % (2 * math.pi)) / ku
        while u < copies * W_ + 1e-12:
            cu.append(u)
            u += period
    cu.sort()
    out = []
    flat_faces = 0
    bent_small = 0
    frames = {}

    def rigid(key, lo, hi, vl, vh):
        """A small part is moved and tilted onto the surface as one piece (so its faces stay
        flat): the frame at its middle - point, along, up the surface, out."""
        if key in frames:
            return frames[key]
        uc, vc = (lo + hi) / 2.0, (vl + vh) / 2.0
        th = th0 + uc * ku
        zc = zb + vc * kv
        e = 1e-5
        a, b = surf(th - e, zc), surf(th + e, zc)
        tx, ty = (b[0] - a[0]) / (2 * e), (b[1] - a[1]) / (2 * e)
        su = math.hypot(tx, ty) * ku                 # mm of surface per mm of pattern, along
        L = math.hypot(tx, ty) or 1.0
        T = (tx / L, ty / L, 0.0)
        # up the surface, measured over the part's own height; where the surface steps in or
        # out (a ledge, an overhang) the part stands upright instead of tipping over
        ez = max(e, (vh - vl) * kv / 2.0)
        c0, c1 = surf(th, zc - ez), surf(th, zc + ez)
        Vd = ((c1[0] - c0[0]) / (2 * ez), (c1[1] - c0[1]) / (2 * ez), 1.0)
        if math.hypot(Vd[0], Vd[1]) > 0.7:          # steeper than a 35 degree batter: a step
            Vd = (0.0, 0.0, 1.0)
        N = v_norm(v_cross(T, Vd))
        x, y = surf(th, zc)
        frames[key] = (uc, vc, (x, y, zc), T, Vd, N, su)
        return frames[key]

    def place_rigid(p, fr_):
        uc, vc, S, T, Vd, N, su = fr_
        du_, dv_ = (p[0] - uc) * su, (p[1] - vc) * kv
        d = lift + p[2] * kw
        return (S[0] + T[0] * du_ + Vd[0] * dv_ + N[0] * d,
                S[1] + T[1] * du_ + Vd[1] * dv_ + N[1] * d,
                S[2] + Vd[2] * dv_ + N[2] * d)
    for (o, hs), ks in zip(uvw, keyed):
        key = find(ks[0])
        lo, hi, wl, wh, vl, vh = span[key]
        # a flat part across a curve sinks in the middle (by the sagitta): only keep it flat
        # while that's a small part of its thickness, otherwise it would vanish into the target
        phi = (hi - lo) * ku
        sag = rb * (1.0 - math.cos(min(phi, math.pi) / 2.0))
        flat_ok = (hi - lo <= flat_max and not hs and sag <= 0.2 * max(wh - wl, 1e-9)
                   and not any(lo + 1e-12 < c < hi - 1e-12 for c in cu))     # not across a corner
        if hi - lo <= flat_max and not hs and not flat_ok:
            bent_small += 1
        if flat_ok:
            fr_ = rigid(key, lo, hi, vl, vh)
            out.append([place_rigid(p, fr_) for p in o])
            flat_faces += 1
            continue
        pieces = face_pieces(o, hs, du, dv)
        if cu:
            pieces = slice_at(pieces, 0, cu)
        for pc in pieces:
            q = [place(p) for p in pc]
            if len(q) == 3 or _planar(q):
                out.append(q)
            else:
                for t in triangles(pc):
                    out.append([place(p) for p in t])
    tris = out
    turns = copies * W_ * ku / (2 * math.pi)
    stretch = ku * rb                                # 1 = bricks keep their width (at the bottom)
    return tris, {'copies': copies, 'turns': turns, 'size': (W_, H_, D_), 'kv': kv, 'rb': rb, 'stretch': stretch,
                  'bent': bent_small, 'girth': 2 * math.pi * rb}


# ---------------------------------------------------------------------------
# Laying new bricks straight onto the target, course by course
# ---------------------------------------------------------------------------
def lay_bricks(target, v):
    """Bricks laid round the target like a real chimney: every course has a whole number
    of bricks (never longer than a standard brick), so there's no seam, and the bond is
    stepped half a brick from course to course. Returns ([faces in world metres], info)."""
    L = max(10.0, v['brick_l']) * SCALE
    H = max(5.0, v['brick_h']) * SCALE
    D = max(1.0, v['brick_d']) * SCALE
    J = max(0.2, v['joint']) * SCALE
    lift = v['lift'] * SCALE
    every = int(v.get('header_every', 0))
    level = bool(v.get('level', True))          # courses laid level, stepping in up a taper
    # some courses can stand out further (oversailing courses, bands, a plinth): a function of
    # the course number and its height, giving the extra depth in metres
    extra_depth = v.get('extra_depth') or (lambda c_, z_: 0.0)
    z0 = target.z0 + v['raise'] * SCALE
    top = target.z0 + target.h if v.get('lay_h', 0) <= 0 else min(target.z0 + target.h, z0 + v['lay_h'] * SCALE)
    th0 = math.radians(v.get('start', 0.0))
    faces = []
    courses = 0
    bricks = 0
    zc = z0
    c = 0

    def surf(th, z):
        r = target.r(th, z)
        return (target.cx + r * math.cos(th), target.cy + r * math.sin(th))
    corners = target.corners() if hasattr(target, 'corners') else []

    def box_faces(S, T, Vd, N, u0, u1, depth, pl0=None, pl1=None):
        def P(u, w, h):
            return (S[0] + T[0] * u + Vd[0] * h + N[0] * w,
                    S[1] + T[1] * u + Vd[1] * h + N[1] * w,
                    S[2] + Vd[2] * h + N[2] * w)

        def onto(X, pl):
            # slide X along the brick (T) until it lies on the plane (X - P).n = d
            if pl is None:
                return X
            P0, n_, d_ = pl
            tn = T[0] * n_[0] + T[1] * n_[1] + T[2] * n_[2]
            if abs(tn) < 0.2:
                return X
            cur = (X[0] - P0[0]) * n_[0] + (X[1] - P0[1]) * n_[1] + (X[2] - P0[2]) * n_[2]
            t_ = (d_ - cur) / tn
            return (X[0] + T[0] * t_, X[1] + T[1] * t_, X[2] + T[2] * t_)
        q = {}
        for iu, uu in enumerate((u0, u1)):
            for ih, hh in enumerate((-H / 2.0, H / 2.0)):
                for iw, ww in enumerate((lift, lift + depth)):
                    q[(iu, ih, iw)] = onto(P(uu, ww, hh), pl0 if iu == 0 else pl1)
        return [[q[(0, 0, 1)], q[(1, 0, 1)], q[(1, 1, 1)], q[(0, 1, 1)]],
                [q[(0, 0, 0)], q[(0, 1, 0)], q[(1, 1, 0)], q[(1, 0, 0)]],
                [q[(0, 1, 0)], q[(0, 1, 1)], q[(1, 1, 1)], q[(1, 1, 0)]],
                [q[(0, 0, 0)], q[(1, 0, 0)], q[(1, 0, 1)], q[(0, 0, 1)]],
                [q[(0, 0, 0)], q[(0, 0, 1)], q[(0, 1, 1)], q[(0, 1, 0)]],
                [q[(1, 0, 0)], q[(1, 1, 0)], q[(1, 1, 1)], q[(1, 0, 1)]]]
    if corners:
        # square or octagonal: each flat side laid on its own, the corners bonded - one side's
        # end brick runs past the corner to cover the other side's end, turn and turn about
        nc = len(corners)
        prev_cuts = {}

        def set_out(a, b, B, unit, side):
            """Cut points from a to b (each brick runs from one to just short of the next).
            Like a bricklayer on a tapered chimney: whole bricks where they'll go, as few cut
            bricks as can be, and every joint kept clear of the joints in the course below
            (no straight joints). Worked out for the whole side at once."""
            # the corners: always two whole bricks set out from each corner, the same every
            # course (turn and turn about), so the corners are neat and regular
            kf = 2
            while kf > 0 and (b - a) < 2 * kf * unit + 0.9 * unit:
                kf -= 1
            head = [a + q * unit for q in range(kf)]
            tail = [b - q * unit for q in range(kf)][::-1]
            a, b = a + kf * unit, b - kf * unit
            if kf:
                mid = set_out_middle(a, b, B, unit)
                return head + mid + tail
            return set_out_middle(a, b, B, unit)

        def set_out_middle(a, b, B, unit):
            total = b - a
            st_ = unit / 45.0                  # a whole brick fits the grid exactly
            m_ = max(2, int(math.ceil(total / st_ - 1e-9)))
            st_ = total / m_                   # (a hair smaller, to fit the side)
            xs = [a + st_ * q for q in range(m_ + 1)]
            clear = 0.4 * unit
            if B:
                pens = [25.0 * (max(0.0, clear - min(abs(x - y) for y in B)) / clear) ** 2 for x in xs]
            else:
                pens = [0.0] * (m_ + 1)
            pens[-1] = 0.0
            qmin = max(1, int(math.ceil(0.45 * unit / st_ - 1e-9)))
            qmax = max(qmin, int(math.floor(unit / st_ + 1e-9)))
            INF = float('inf')
            best = [INF] * (m_ + 1)
            back = [-1] * (m_ + 1)
            best[0] = 0.0
            for q in range(m_):
                bq = best[q]
                if bq == INF:
                    continue
                for r in range(q + qmin, min(m_, q + qmax) + 1):
                    short = (unit - (r - q) * st_) / unit
                    cst = bq + 1.0 + 8.0 * short + (3.0 if short > 0.03 else 0.0) + pens[r]
                    if cst < best[r]:
                        best[r] = cst
                        back[r] = q
            if best[m_] == INF:
                n = max(1, int(math.ceil(total / unit - 1e-9)))
                return [a + total * q / n for q in range(n + 1)]
            out, q = [], m_
            while q > 0:
                out.append(xs[q])
                q = back[q]
            out.append(a)
            return out[::-1]

        while zc + H <= top + 1e-9:
            this_cuts = {}
            zm = zc + H / 2.0
            header = every > 0 and (c % every == every - 1)
            unit = (D if header else L) + J
            depth = (L if header else D) + extra_depth(c, zc)
            frames = []
            for si in range(nc):
                a0, a1 = corners[si], corners[(si + 1) % nc] + (2 * math.pi if si == nc - 1 else 0.0)
                am = (a0 + a1) / 2.0
                ez = H / 2.0
                zb = zm
                if level:
                    # laid level: the back of the course stands where the side is widest over
                    # the brick's height (its foot, on a taper), so each course steps in a little
                    zb = zm - ez if target.r(am, zm - ez) >= target.r(am, zm + ez) else zm + ez
                pa, pb = surf(a0, zb), surf(a1, zb)
                dx, dy = pb[0] - pa[0], pb[1] - pa[1]
                side = math.hypot(dx, dy)
                T = (dx / side, dy / side, 0.0) if side > 0 else (1.0, 0.0, 0.0)
                if level:
                    Vd = (0.0, 0.0, 1.0)
                else:
                    c0, c1 = surf(am, zm - ez), surf(am, zm + ez)
                    Vd = ((c1[0] - c0[0]) / (2 * ez), (c1[1] - c0[1]) / (2 * ez), 1.0)
                N = v_norm(v_cross(T, Vd))
                frames.append(((pa[0], pa[1], zm), T, Vd, N, side))
            for si in range(nc):
                S, T, Vd, N, side = frames[si]
                if side < unit * 0.5:
                    continue
                long_side = (si + c) % 2 == 0
                ext = depth * math.tan(math.pi / nc)     # the corner square (or wedge)
                s0 = -ext if long_side else J
                s1 = side + ext if long_side else side - J
                # like a real chimney: on this course one side's end brick runs on past the
                # corner (covering the other side's end) and the next course the other way round,
                # so the corner is bonded. Each side is set out evenly between its ends, no brick
                # longer than a standard one; swapping the long side each course moves the joints
                # along by about half a brick (running bond).
                # Set out from the course below, as a bricklayer does: each joint goes as near
                # half a brick from the joints below as it can, no brick longer than a standard
                # one, so there are no straight joints even where a tapered side gets a brick
                # fewer (there the bond may close to a quarter brick for a joint or two).
                below = prev_cuts.get(si)
                if below:
                    # joints near the far corner move with that corner (the side is shorter)
                    dl = side - below[1]
                    B = [u if u < below[1] / 2.0 else u + dl for u in below[0]]
                else:
                    B = None
                cuts = set_out(s0, s1 + J, B, unit, side)
                # the joints this course leaves on this face, for the course above (a course
                # that stops short of the corners also has a joint at each end, by the corner brick)
                this_cuts[si] = (cuts[1:-1] if long_side else cuts[:-1] + [cuts[-1] - J], side)
                # the two ends at the corners meet the next sides' faces, which lean differently
                # on a tapered chimney: the brick that runs past the corner finishes flush with
                # the other face, and the one that stops short starts a joint away from it
                Sp, _, _, Np, _ = frames[(si - 1) % nc]
                Sn, _, _, Nn, _ = frames[(si + 1) % nc]
                # (running past: flush with the other side's brick face; stopping short: a joint
                # clear of the other side's chimney face, where that corner brick sits)
                off = (lift + depth) if long_side else (lift - J)
                pl0, pl1 = (Sp, Np, off), (Sn, Nn, off)
                spans = list(zip(cuts[:-1], cuts[1:]))
                for k_, (ca, cb) in enumerate(spans):
                    if cb - J - ca < 0.25 * (L if not header else D) * 0.5:
                        continue
                    faces += box_faces(S, T, Vd, N, ca, cb - J, depth,
                                       pl0 if k_ == 0 else None, pl1 if k_ == len(spans) - 1 else None)
                    bricks += 1
            prev_cuts = this_cuts
            courses += 1
            c += 1
            zc += H + J
        return faces, {'courses': courses, 'bricks': bricks}
    frac_prev, n_prev = 0.0, 0
    prev_ring = None              # the angles of the joints in the course below
    while zc + H <= top + 1e-9:
        zm = zc + H / 2.0
        # the girth at this height, and where each length along it comes round
        n_s = 720
        pts = [surf(th0 + 2 * math.pi * k / n_s, zm) for k in range(n_s + 1)]
        cum = [0.0]
        for k in range(n_s):
            cum.append(cum[-1] + math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]))
        girth = cum[-1]
        header = every > 0 and (c % every == every - 1)
        unit = (D if header else L) + J
        n = max(3, int(math.ceil(girth / unit - 1e-9)))     # never longer than a standard brick
        step = girth / n
        blen = step - J
        # each course starts half a brick on from the one below, so the joints step round
        # (no line of joints where the courses begin)
        frac = frac_prev + (0.5 / n_prev if n_prev else 0.0)
        if header:
            frac = frac_prev + (0.25 / n_prev if n_prev else 0.0)
        frac %= 1.0
        off = frac * girth
        frac_prev, n_prev = frac, n

        def theta_at(sv):
            sv = sv % girth
            lo, hi = 0, n_s
            while hi - lo > 1:
                mid = (lo + hi) // 2
                if cum[mid] <= sv:
                    lo = mid
                else:
                    hi = mid
            t = (sv - cum[lo]) / ((cum[hi] - cum[lo]) or 1.0)
            return th0 + 2 * math.pi * (lo + t) / n_s
        depth = (L if header else D) + extra_depth(c, zc)

        def s_at(th):
            idx = ((th - th0) % (2 * math.pi)) / (2 * math.pi) * n_s
            lo = min(int(idx), n_s - 1)
            return cum[lo] + (idx - lo) * (cum[lo + 1] - cum[lo])
        # where the joints go round this course: shared out evenly to begin with; after that
        # set out from the joints below, as a bricklayer would, so that as the girth shrinks
        # (a brick fewer every course or two on a taper) no joint lands on one below
        ring = [off + i * step for i in range(n + 1)]
        if prev_ring:
            Bs = sorted(s_at(a) for a in prev_ring)
            import bisect

            def near(x):
                x %= girth
                k = bisect.bisect_left(Bs, x)
                a1, a2 = Bs[k % len(Bs)], Bs[(k - 1) % len(Bs)]
                return min((x - a1) % girth, (a1 - x) % girth, (x - a2) % girth, (a2 - x) % girth)
            # start half way between two joints below, near where the even ring would start
            o_ = off % girth
            k = bisect.bisect_left(Bs, o_)
            a1, a2 = Bs[(k - 1) % len(Bs)], Bs[k % len(Bs)]
            gap_ = (a2 - a1) % girth or girth
            s0 = a1 + gap_ / 2.0
            # a grid that a whole brick fits exactly (so whole bricks are possible), then the
            # ring shrunk a hair to close up - no brick ends up longer than a standard one
            st_ = unit / 48.0
            m_ = max(3, int(math.ceil(girth / st_ - 1e-9)))
            fit_ = girth / (m_ * st_)
            clear = 0.4 * unit
            pens = [10.0 * (max(0.0, clear - near(s0 + q * st_ * fit_)) / clear) ** 2 for q in range(m_ + 1)]
            pens[0] = pens[-1] = 0.0
            qmin = max(1, int(math.ceil(0.45 * unit / st_ - 1e-9)))
            qmax = max(qmin, int(math.floor(unit / st_ + 1e-9)))
            INF = float('inf')
            best = [INF] * (m_ + 1)
            back = [-1] * (m_ + 1)
            best[0] = 0.0
            for q in range(m_):
                bq = best[q]
                if bq == INF:
                    continue
                for r in range(q + qmin, min(m_, q + qmax) + 1):
                    short = (unit - (r - q) * st_) / unit
                    cst = bq + 1.0 + 8.0 * short + (3.0 if short > 0.08 else 0.0) + pens[r]
                    if cst < best[r]:
                        best[r] = cst
                        back[r] = q
            if best[m_] < INF:
                out, q = [], m_
                while q > 0:
                    out.append(s0 + q * st_ * fit_)
                    q = back[q]
                out.append(s0)
                ring = out[::-1]
        prev_ring = [theta_at(x) for x in ring[:-1]]

        for i in range(len(ring) - 1):
            # a brick from one angle to the next, its ends square to the surface (radial), so
            # it is slightly wedge-shaped and meets its neighbours joint to joint, no overlap
            ta = theta_at(ring[i] + J / 2.0)
            tb = theta_at(ring[i + 1] - J / 2.0)
            if tb < ta:
                tb += 2 * math.pi
            # built in one frame at the brick's middle, so every face is exactly flat even on a
            # drawn (faceted) target; the ends lean out at the brick's own angle (a wedge)
            tc = (ta + tb) / 2.0
            phi = (tb - ta) / 2.0
            e = 1e-5
            a_, b_ = surf(tc - e, zm), surf(tc + e, zm)
            tx, ty = b_[0] - a_[0], b_[1] - a_[1]
            Lt = math.hypot(tx, ty) or 1.0
            T = (tx / Lt, ty / Lt, 0.0)
            ez = H / 2.0
            zb = zm
            if level:
                # laid level, the back standing where the target is widest over the brick's
                # height, so on a taper each course steps in a little (like a real chimney)
                Vd = (0.0, 0.0, 1.0)
                zb = zm - ez if target.r(tc, zm - ez) >= target.r(tc, zm + ez) else zm + ez
            else:
                c0, c1 = surf(tc, zm - ez), surf(tc, zm + ez)
                Vd = ((c1[0] - c0[0]) / (2 * ez), (c1[1] - c0[1]) / (2 * ez), 1.0)
                if math.hypot(Vd[0], Vd[1]) > 0.7:
                    Vd = (0.0, 0.0, 1.0)
            N = v_norm(v_cross(T, Vd))
            x, y = surf(tc, zb)
            S = (x, y, zm)
            r_ = max(1e-6, target.r(tc, zb))
            half = r_ * math.sin(phi)                      # half the back, along the chord
            flare = math.tan(phi)
            q = {}
            for iu, sg in enumerate((-1.0, 1.0)):
                for ih, hh in enumerate((-H / 2.0, H / 2.0)):
                    for iw, ww in enumerate((lift, lift + depth)):
                        uu = sg * (half + ww * flare)
                        q[(iu, ih, iw)] = (S[0] + T[0] * uu + Vd[0] * hh + N[0] * ww,
                                           S[1] + T[1] * uu + Vd[1] * hh + N[1] * ww,
                                           S[2] + Vd[2] * hh + N[2] * ww)
            faces += [
                [q[(0, 0, 1)], q[(1, 0, 1)], q[(1, 1, 1)], q[(0, 1, 1)]],
                [q[(0, 0, 0)], q[(0, 1, 0)], q[(1, 1, 0)], q[(1, 0, 0)]],
                [q[(0, 1, 0)], q[(0, 1, 1)], q[(1, 1, 1)], q[(1, 1, 0)]],
                [q[(0, 0, 0)], q[(1, 0, 0)], q[(1, 0, 1)], q[(0, 0, 1)]],
                [q[(0, 0, 0)], q[(0, 0, 1)], q[(0, 1, 1)], q[(0, 1, 0)]],
                [q[(1, 0, 0)], q[(1, 1, 0)], q[(1, 1, 1)], q[(1, 0, 1)]],
            ]
            bricks += 1
        courses += 1
        c += 1
        zc += H + J
    return faces, {'courses': courses, 'bricks': bricks}


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------
TARGETS = [("round", "Round (made to size)"), ("square", "Square (made to size)"),
           ("octagon", "Octagonal (made to size)"), ("mesh", "A solid I've drawn")]
FITS = [("repeat", "Repeat round (true size)"),
        ("round", "Once round (stretched)"),
        ("true", "True width, once")]
HFITS = [("stretch", "Stretch to the height"), ("true", "True height")]

DEFAULTS = dict(target='round', bottom=1200.0, top=800.0, height=6000.0, add_core=True,
                fit='repeat', ignore=100.0, source='bricks', brick_l=215.0, brick_h=65.0, brick_d=102.5,
                joint=10.0, header_every=0, lay_h=0.0, height_fit='true', raise_=0.0, start=0.0, lift=0.01, detail=50.0, flat_max=300.0,
                flip=False, scale_depth=False, level=True)


def _narrow(cb, n):
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
    try:
        fl.setHorizontalSpacing(6)
        fl.setVerticalSpacing(4)
    except Exception:
        pass
    return fl


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

EDDY_TIPS = {}
EDDY_TIPS_END = None


class WrapDialog(QDialog):
    def __init__(self, viewport, tool, cur):
        super().__init__(viewport)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.pattern = None
        self.target = None
        lay = QVBoxLayout(self)
        intro = QLabel("Pick what goes on and the target, then click Wrap. Sizes in real mm.")
        intro.setWordWrap(True)
        intro.setToolTip("1. Choose what goes on: new bricks laid course by course, or a flat pattern you've "
                         "made (select it and click 'Use as pattern').\n2. Choose the target: a chimney made "
                         "to size, or select a solid you've drawn and click 'Use as target'.\n3. Click 'Wrap'.")
        lay.addWidget(intro)
        top = QFormLayout()
        self.cb_source = QComboBox()
        self.cb_source.addItem("New bricks", 'bricks')
        self.cb_source.addItem("My own pattern", 'pattern')
        self.cb_source.setToolTip("New bricks: laid course by course - every course has a whole number of "
                                  "bricks, never longer than a standard one, stepped half a brick each course, "
                                  "corners bonded - like a real chimney. My own pattern: bend any flat group "
                                  "round (Flowify-style).")
        _narrow(self.cb_source, 14)
        self.cb_target = QComboBox()
        for k, t in TARGETS:
            self.cb_target.addItem(t, k)
        self.cb_target.setToolTip("What to wrap onto: a round, square or octagonal chimney made to size, or a "
                                  "solid you've drawn yourself (square and many-sided ones get bonded corners).")
        _narrow(self.cb_target, 14)
        top.addRow("Put on", self.cb_source)
        top.addRow("Target", self.cb_target)
        lay.addLayout(top)
        prow = QHBoxLayout()
        b_pat = QPushButton("Use as pattern")
        b_pat.setToolTip("Uses the group you have selected as the pattern to wrap ('My own pattern').")
        self.b_pat = b_pat
        self.b_tgt = QPushButton("Use as target")
        self.b_tgt.setToolTip("Uses the solid you have selected as the target ('A solid I've drawn').")
        prow.addWidget(b_pat)
        prow.addWidget(self.b_tgt)
        lay.addLayout(prow)
        self.lbl_pat = QLabel("Pattern: none yet")
        self.lbl_tgt = QLabel("Target solid: none yet")
        for l_ in (self.lbl_pat, self.lbl_tgt):
            l_.setStyleSheet("color: gray;")
            l_.setWordWrap(True)
            lay.addWidget(l_)

        tabs = QTabWidget()
        self.tabs = tabs
        pages = {}
        for title in ("Chimney", "Bricks", "Pattern"):
            pg = QWidget()
            pages[title] = _form(pg)
            tabs.addTab(pg, title)
        tabs.setTabToolTip(0, "The chimney made to size, and where the bricks or pattern go up it.")
        tabs.setTabToolTip(1, "Brick size, mortar and header courses (New bricks).")
        tabs.setTabToolTip(2, "How your own pattern is fitted and bent round (My own pattern).")
        lay.addWidget(tabs)
        self.sp = {}

        def num(tab, key, label, lo, hi, dec, suf, tip=""):
            s = QDoubleSpinBox()
            s.setDecimals(dec)
            s.setRange(lo, hi)
            s.setSuffix(suf)
            s.setKeyboardTracking(False)
            s.setValue(float(cur.get(key, DEFAULTS[key])))
            lab = QLabel(label)
            if tip:
                s.setToolTip(tip)
                lab.setToolTip(tip)
            pages[tab].addRow(lab, s)
            self.sp[key] = s
        num("Chimney", 'bottom', "Bottom size", 50.0, 20000.0, 0, " mm",
            "Across the bottom (the diameter, or across the flats of a square or octagon).")
        num("Chimney", 'top', "Top size", 10.0, 20000.0, 0, " mm",
            "Across the top. Smaller than the bottom for a taper.")
        num("Chimney", 'height', "Height", 50.0, 100000.0, 0, " mm", "How tall the chimney is.")
        self.cb_core = QCheckBox("Add the chimney core")
        self.cb_core.setToolTip("Also adds the chimney as a solid, just inside the bricks, so there's a core "
                                "to print (made-to-size chimneys).")
        self.cb_core.setChecked(bool(cur.get('add_core', True)))
        pages["Chimney"].addRow(self.cb_core)
        num("Chimney", 'raise_', "Start up", 0.0, 100000.0, 0, " mm",
            "Leaves this much bare at the bottom before the first course.")
        num("Chimney", 'lay_h', "Go up to", 0.0, 100000.0, 0, " mm",
            "Stops at this height above the start. 0 = all the way to the top.")
        num("Chimney", 'start', "Turn round by", -360.0, 360.0, 0, " deg",
            "Where the start of the courses (or the middle of the pattern) comes round the target.")
        num("Chimney", 'ignore', "Ignore rims under", 0.0, 2000.0, 0, " mm",
            "A solid you've drawn: anything sticking out of it over less than this height (a stray "
            "face, a thin disc where two parts meet) is ignored, so the bricks don't follow it out. "
            "0 = follow everything.")
        num("Chimney", 'lift', "Gap off target", 0.0, 5.0, 3, " mm",
            "A hair's gap, so faces don't lie on each other.")

        num("Bricks", 'brick_l', "Length", 10.0, 2000.0, 1, " mm",
            "The length of a brick. No brick is ever longer than this (each course is shared out evenly).")
        num("Bricks", 'brick_h', "Height", 5.0, 1000.0, 1, " mm", "The height of a brick (one course).")
        num("Bricks", 'brick_d', "Depth", 1.0, 1000.0, 1, " mm",
            "How far the bricks stand out from the target. On a target that is the core of the "
            "chimney, the core shows between the bricks as the mortar.")
        num("Bricks", 'joint', "Mortar joint", 0.2, 100.0, 1, " mm",
            "The gap between bricks. For printing use about your nozzle width (32 mm = 0.4 mm at 1:80).")
        self.sp_hdr = QSpinBox()
        self.sp_hdr.setRange(0, 50)
        self.sp_hdr.setValue(int(cur.get('header_every', 0)))
        self.sp_hdr.setToolTip("A course of headers (brick ends) every this many courses. 0 = none.")
        lab = QLabel("Headers every")
        lab.setToolTip(self.sp_hdr.toolTip())
        pages["Bricks"].addRow(lab, self.sp_hdr)
        self.cb_level = QCheckBox("Lay the courses level")
        self.cb_level.setToolTip("Every course is laid level, like a real chimney: on a taper each course "
                                 "is set in a little from the one below, so it steps in. Untick to tilt the "
                                 "bricks back to follow the slope instead.")
        self.cb_level.setChecked(bool(cur.get('level', True)))
        pages["Bricks"].addRow(self.cb_level)

        self.cb_fit = QComboBox()
        for k, t in FITS:
            self.cb_fit.addItem(t, k)
        self.cb_fit.setToolTip("Repeat round: copies of the pattern side by side all the way round, eased a "
                               "little so they close up - the bricks stay their real size. Once round: the "
                               "pattern's width is stretched to the girth (like Flowify). True width: one "
                               "copy at its real width.")
        _narrow(self.cb_fit, 14)
        self.cb_hfit = QComboBox()
        for k, t in HFITS:
            self.cb_hfit.addItem(t, k)
        self.cb_hfit.setToolTip("Stretch the pattern to the target's height, or keep it at its true height.")
        _narrow(self.cb_hfit, 14)
        for lbl, w_ in (("Across", self.cb_fit), ("Up", self.cb_hfit)):
            l_ = QLabel(lbl)
            l_.setToolTip(w_.toolTip())
            pages["Pattern"].addRow(l_, w_)
        num("Pattern", 'detail', "Bend every", 2.0, 1000.0, 0, " mm",
            "Faces are cut into pieces this wide so they bend smoothly. Smaller = smoother, more faces.")
        num("Pattern", 'flat_max', "Keep flat up to", 0.0, 5000.0, 0, " mm",
            "Bricks and other small parts keep flat faces, like real bricks on a round chimney (and no "
            "extra lines across them). Anything longer is bent to follow the curve.")
        self.cb_flip = QCheckBox("Front is the other side")
        self.cb_flip.setToolTip("Tick if the pattern ends up facing inwards.")
        self.cb_flip.setChecked(bool(cur.get('flip', False)))
        pages["Pattern"].addRow(self.cb_flip)
        self.cb_depth = QCheckBox("Stretch its thickness too")
        self.cb_depth.setToolTip("The pattern's thickness grows and shrinks with the stretch, instead of "
                                 "staying the same.")
        self.cb_depth.setChecked(bool(cur.get('scale_depth', False)))
        pages["Pattern"].addRow(self.cb_depth)
        for cb, key in ((self.cb_target, 'target'), (self.cb_fit, 'fit'), (self.cb_hfit, 'height_fit')):
            for i in range(cb.count()):
                if cb.itemData(i) == cur.get(key, DEFAULTS[key]):
                    cb.setCurrentIndex(i)
        self.lbl_report = QLabel()
        self.lbl_report.setWordWrap(True)
        lay.addWidget(self.lbl_report)
        brow = QHBoxLayout()
        b_go = QPushButton("Wrap")
        b_go.setDefault(True)
        b_go.setToolTip("Wraps the bricks or pattern onto the target.")
        b_close = QPushButton("Close")
        brow.addWidget(b_go)
        brow.addStretch(1)
        brow.addWidget(b_close)
        lay.addLayout(brow)
        try:
            self.setMaximumWidth(400)
        except Exception:
            pass
        b_pat.clicked.connect(self.pick_pattern)
        self.b_tgt.clicked.connect(self.pick_target)
        self.cb_target.currentIndexChanged.connect(self.changed)
        self.cb_source.currentIndexChanged.connect(self.changed)
        for i in range(self.cb_source.count()):
            if self.cb_source.itemData(i) == cur.get('source', DEFAULTS['source']):
                self.cb_source.setCurrentIndex(i)
        b_go.clicked.connect(lambda: self.tool.do_wrap(self))
        b_close.clicked.connect(self.close)
        self.changed()
        self.pick_pattern(quiet=True)

    def changed(self, *_):
        mesh = self.cb_target.currentData() == 'mesh'
        for k in ('bottom', 'top', 'height'):
            self.sp[k].setEnabled(not mesh)
        self.sp['ignore'].setEnabled(mesh)
        bricks = self.cb_source.currentData() == 'bricks'
        for k in ('brick_l', 'brick_h', 'brick_d', 'joint', 'lay_h'):
            self.sp[k].setEnabled(bricks)
        self.sp_hdr.setEnabled(bricks)
        self.cb_level.setEnabled(bricks)
        self.b_pat.setEnabled(not bricks)
        for k in ('detail', 'flat_max'):
            self.sp[k].setEnabled(not bricks)
        for w_ in (self.cb_fit, self.cb_hfit, self.cb_flip, self.cb_depth):
            w_.setEnabled(not bricks)
        self.cb_core.setEnabled(not mesh)
        self.b_tgt.setEnabled(mesh)
        self.lbl_pat.setVisible(not bricks)
        self.lbl_tgt.setVisible(mesh)
        try:
            self.tabs.setTabEnabled(1, bricks)
            self.tabs.setTabEnabled(2, not bricks)
            if self.tabs.currentIndex() == (2 if bricks else 1):
                self.tabs.setCurrentIndex(1 if bricks else 2)
        except Exception:
            pass

    def _selected(self):
        scene = getattr(self.viewport, 'scene', None)
        return selected_groups(scene) if scene is not None else []

    def pick_pattern(self, *_, quiet=False):
        gs = self._selected()
        if not gs:
            if not quiet:
                QMessageBox.information(self, PLUGIN_NAME, "Select the pattern group first.")
            return
        self.pattern = gs[0]
        self.lbl_pat.setText("Pattern: " + group_label(gs[0]))

    def pick_target(self, *_):
        gs = [g for g in self._selected() if g is not self.pattern]
        if not gs:
            QMessageBox.information(self, PLUGIN_NAME, "Select the solid to wrap round (not the pattern).")
            return
        self.target = gs[0]
        self.lbl_tgt.setText("Target solid: " + group_label(gs[0]))

    def values(self):
        v = dict(target=self.cb_target.currentData(), fit=self.cb_fit.currentData(),
                 source=self.cb_source.currentData(), header_every=int(self.sp_hdr.value()),
                 height_fit=self.cb_hfit.currentData(), add_core=self.cb_core.isChecked(),
                 flip=self.cb_flip.isChecked(), scale_depth=self.cb_depth.isChecked(),
                 level=self.cb_level.isChecked())
        for k, s in self.sp.items():
            v[k] = float(s.value())
        v['raise'] = v['raise_']
        return v


class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
class WrapTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+U"
    description = "Bends a flat pattern (bricks, boards...) round a chimney or any upright solid, like Flowify."
    _dialog = None
    _saved = None

    def on_activate(self, viewport):
        dlg = WrapTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.raise_()
                    dlg.activateWindow()
                    return
            except Exception:
                pass
        dlg = WrapDialog(viewport, self, dict(DEFAULTS, **(WrapTool._saved or {})))
        WrapTool._dialog = dlg

        def closed(*_):
            WrapTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass

    def do_wrap(self, dlg):
        v = dlg.values()
        WrapTool._saved = dict(v)
        if v['source'] == 'bricks':
            return self.do_bricks(dlg, v)
        if dlg.pattern is None:
            dlg.pick_pattern()
            if dlg.pattern is None:
                return
        faces = group_faces(dlg.pattern)
        if not faces:
            QMessageBox.warning(dlg, PLUGIN_NAME, "The pattern group has no faces.")
            return
        try:
            if v['target'] == 'mesh':
                if dlg.target is None:
                    QMessageBox.information(dlg, PLUGIN_NAME, "Pick the target solid first "
                                                              "('Use selected as target').")
                    return
                target = MeshTarget(group_faces(dlg.target), ignore=v['ignore'] * SCALE)
            else:
                # a chimney made to size, standing behind the pattern so it wraps from where it is
                fr = pattern_frame(faces, None, v['flip'])
                rb = v['bottom'] / 2.0 * SCALE
                cx = fr['c'][0] - fr['W'][0] * (rb + 0.0)
                cy = fr['c'][1] - fr['W'][1] * (rb + 0.0)
                target = ShapeTarget(v['target'], cx, cy, fr['v0'], v['height'] * SCALE,
                                     v['bottom'] * SCALE, v['top'] * SCALE)
            fr = pattern_frame(faces, (target.cx, target.cy), v['flip'])
            # the middle of the pattern faces the way it did
            face_ang = math.atan2(fr['W'][1], fr['W'][0])
            W_ = fr['u1'] - fr['u0']
            zb = target.z0 + v['raise'] * SCALE
            rb_ = max(1e-6, sum(target.r(2 * math.pi * k / 36, zb) for k in range(36)) / 36)
            if v['fit'] == 'round':
                ku = 2 * math.pi / W_
            elif v['fit'] == 'repeat':
                ku = 2 * math.pi / (max(1, int(round(2 * math.pi * rb_ / W_))) * W_)
            else:
                ku = 1.0 / rb_
            v['start'] = math.degrees(face_ang - W_ / 2 * ku) + v['start']
            tris, info = wrap(faces, target, v)
        except ValueError as e:
            QMessageBox.warning(dlg, PLUGIN_NAME, str(e))
            return
        name = "Wrapped - " + group_label(dlg.pattern)
        core = target.solid_faces() if (v['target'] != 'mesh' and v['add_core']) else None
        self._errors = (0, None)
        nf = self.add_to_scene(dlg.viewport, name, tris, core)
        if nf is None:
            return
        msg = "Wrapped '%s': %d faces, %.2f times round" % (group_label(dlg.pattern), nf, info['turns'])
        if info.get('copies', 1) > 1:
            msg += " (%d copies side by side)" % info['copies']
        if v['fit'] == 'true' and info['turns'] > 1.001:
            msg += " (it overlaps itself: make the pattern narrower, or use 'Once all the way round')"
        msg += "."
        st = info['stretch']
        bad = False
        if v['fit'] in ('round', 'repeat') and (st > 1.25 or st < 0.8):
            bad = True
            msg += ("\nThe bricks are %s %.1f times to go round (the girth at the bottom is %.0f mm, the "
                    "pattern %.0f mm wide). For true-size bricks make the pattern about %.0f mm wide, or "
                    "use 'True width'." % ("stretched" if st > 1 else "squashed", st if st > 1 else 1 / st,
                                           info['girth'] / SCALE, info['size'][0] / SCALE, info['girth'] / SCALE))
        if info['bent']:
            msg += "\n%d faces of small parts were bent to follow the curve (kept flat they'd sink into it)." % info['bent']
        if self._errors[0]:
            bad = True
            msg += "\n%d faces could not be made: %s" % self._errors
        msg += "\nThe flat pattern is still there: hide or delete it."
        dlg.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if bad else "#2e7d32"))
        dlg.lbl_report.setText(msg)

    def do_bricks(self, dlg, v):
        try:
            if v['target'] == 'mesh':
                if dlg.target is None:
                    QMessageBox.information(dlg, PLUGIN_NAME, "Pick the target solid first "
                                                              "('Use selected as target').")
                    return
                target = MeshTarget(group_faces(dlg.target), ignore=v['ignore'] * SCALE)
                name = "Brickwork - " + group_label(dlg.target)
            else:
                # a chimney made to size: beside a picked pattern if there is one, else at the origin
                cx = cy = 0.0
                z0 = 0.0
                if dlg.pattern is not None:
                    pf = group_faces(dlg.pattern)
                    if pf:
                        fr = pattern_frame(pf, None, v['flip'])
                        rb = v['bottom'] / 2.0 * SCALE
                        cx, cy = fr['c'][0] - fr['W'][0] * rb, fr['c'][1] - fr['W'][1] * rb
                        z0 = fr['v0']
                target = ShapeTarget(v['target'], cx, cy, z0, v['height'] * SCALE,
                                     v['bottom'] * SCALE, v['top'] * SCALE)
                name = "Brick chimney"
            faces, info = lay_bricks(target, v)
        except ValueError as e:
            QMessageBox.warning(dlg, PLUGIN_NAME, str(e))
            return
        if not faces:
            QMessageBox.warning(dlg, PLUGIN_NAME, "No bricks fitted: is the target tall enough for one course?")
            return
        core = target.solid_faces() if (v['target'] != 'mesh' and v['add_core']) else None
        self._errors = (0, None)
        nf = self.add_to_scene(dlg.viewport, name, faces, core)
        if nf is None:
            return
        msg = "Laid %d bricks in %d courses, %d faces. Every course is a whole number of bricks, so there's " \
              "no seam." % (info['bricks'], info['courses'], nf)
        if self._errors[0]:
            msg += "\n%d faces could not be made: %s" % self._errors
        dlg.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if self._errors[0] else "#2e7d32"))
        dlg.lbl_report.setText(msg)

    def add_to_scene(self, viewport, name, tris, core=None):
        stats = {'faces': 0, 'errors': 0, 'err': None}
        tol = 1e-4 * 0.001

        def mesh_of(polys):
            from core.mesh import Mesh
            mesh = Mesh()
            verts = {}

            def vx(p):
                k = (round(p[0] / tol), round(p[1] / tol), round(p[2] / tol))
                if k not in verts:
                    verts[k] = VertexWrapper(*p)
                return verts[k]
            for t in polys:
                try:
                    mesh.add_face([vx(p) for p in t])
                    stats['faces'] += 1
                except Exception as e:
                    stats['errors'] += 1
                    stats['err'] = e
            return mesh

        def make_group(Group, mesh, nm):
            try:
                g = Group(mesh, name=nm)
            except TypeError:
                g = Group(nm)
                g.mesh = mesh
            try:
                g.name = nm
            except Exception:
                pass
            g.component = False
            return g

        def mutate(scene):
            from core.group import Group
            kids = [make_group(Group, mesh_of(tris), name if not name.startswith("Brick chimney") else "Bricks")]
            if core:
                kids.append(make_group(Group, mesh_of(core), "Chimney"))
            if stats['faces'] == 0:
                raise RuntimeError("No faces could be made (%s)." % stats['err'])
            top = None
            if len(kids) > 1:
                try:
                    top = Group(name=name.replace("Wrapped - ", "Wrapped chimney - ") if name.startswith("Wrapped")
                                else name)
                    if hasattr(top, 'adopt'):
                        top.adopt(kids)
                    else:
                        top.children = kids
                    top.component = False
                except Exception:
                    top = None
            for g in ([top] if top is not None else kids):
                if hasattr(scene, 'add_group') and top is None:
                    scene.add_group(g)
                else:
                    scene.groups.append(g)
        try:
            viewport.history.execute(SnapshotImport(mutate))
        except Exception as e:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not add it:\n%s" % e)
            return None
        try:
            viewport.notify_scene_changed()
        except Exception:
            pass
        self._errors = (stats['errors'], stats['err'])
        return stats['faces']


def run(viewport=None):
    WrapTool().on_activate(viewport)
