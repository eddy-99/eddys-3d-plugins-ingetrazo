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
3D Wrap - bend a flat pattern round a chimney, for IngeTrazo
Pick a flat pattern standing upright - a panel of bricks from Brick & Block Studio, boards
from Wood Planking, anything in a group - and a target: a round, square or octagonal
chimney made to size (straight or tapered), or any upright solid you've drawn (the Loft
plugin makes good tapered chimneys). The pattern is bent round it: its width goes round
the girth, its height up the side, and its thickness stands out from the surface. On a
tapered chimney everything gets narrower towards the top.

Or skip the pattern and lay new bricks straight onto the target, course by course: every
course is a whole number of bricks (never longer than a standard brick), so there's no seam.

New bricks can lie level (stepping in up a taper) or lean back onto a tapered chimney's face;
the courses can sit on each other with no mortar between them; and there are cant bricks:
cant corners, cant top or bottom courses, and a small bevel on every brick's front edges.

Your own setups can be saved as presets (everything, or the Bricks tab only), and one of
them set as the default that 3D Wrap opens with. They're kept in
Documents\\IngeTrazo Presets\\Wrap.

Beside the settings, a Close-up tab shows a few bricks as they'll be laid (it follows every
change), and a Sizes tab shows what each lettered size (A, B, C ...) measures; the same
letters are next to the boxes.

On square and many-sided chimneys the corners can be bonded (one side's end brick runs past
the corner) or made with special corner bricks: a dog-leg brick made to the corner's own
angle, so it fits exactly even on a tapered chimney.

A solid you've drawn that goes only part way round (a curved wall with two ends) is found
by itself: the bricks go along the wall from end to end, on its outside, inside or both
faces, and its ends are stopped, toothed or returned round the end.

The flat pattern is left as it was; the wrapped copy is a new group. Ctrl+Alt+U.
"""

import math
import os
import json
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QCheckBox,
                               QDoubleSpinBox, QSpinBox, QPushButton, QLabel, QMessageBox,
                               QTabWidget, QWidget, QInputDialog)

PLUGIN_NAME = "3D Wrap"
VERSION = "14"
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


def _in_scene(scene, g):
    """True if the group g is still in the model (at the top or inside another group)."""
    if scene is None or g is None:
        return g is not None
    todo = list(_items(getattr(scene, 'groups', None)))
    seen = 0
    while todo and seen < 200000:
        e = todo.pop()
        seen += 1
        if e is g:
            return True
        todo.extend(_items(getattr(e, 'children', None)))
    return False


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
# A brick, with cant (chamfered) front edges if wanted
# ---------------------------------------------------------------------------
def _box6(q):
    """The six faces of a brick from its eight corners q[(end, bottom/top, back/front)]."""
    return [[q[(0, 0, 1)], q[(1, 0, 1)], q[(1, 1, 1)], q[(0, 1, 1)]],
            [q[(0, 0, 0)], q[(0, 1, 0)], q[(1, 1, 0)], q[(1, 0, 0)]],
            [q[(0, 1, 0)], q[(0, 1, 1)], q[(1, 1, 1)], q[(1, 1, 0)]],
            [q[(0, 0, 0)], q[(1, 0, 0)], q[(1, 0, 1)], q[(0, 0, 1)]],
            [q[(0, 0, 0)], q[(0, 0, 1)], q[(0, 1, 1)], q[(0, 1, 0)]],
            [q[(1, 0, 0)], q[(1, 1, 0)], q[(1, 1, 1)], q[(1, 0, 1)]]]


def _unit(a, b):
    return v_norm(v_sub(b, a))


def brick_faces(q, cant=None, extra=None):
    """The faces of a brick. cant gives the size (metres) of the chamfer on each of its front
    edges: 'top', 'bottom', 'end0', 'end1' (0 or missing = a sharp edge). The brick is made as
    the solid inside its six faces and the chamfer planes, so any mix of cants (and bricks with
    flared or angled ends) closes up neatly, with a little three-sided face where two meet."""
    cant = {k: s for k, s in (cant or {}).items() if s and s > 0}
    box = _box6(q)
    if not cant and not extra:
        return box
    cen = v_mul(v_add(v_add(q[(0, 0, 0)], q[(1, 1, 1)]), v_add(q[(0, 1, 0)], q[(1, 0, 1)])), 0.25)
    planes = []

    def plane(a, b, c):
        n = v_cross(v_sub(b, a), v_sub(c, a))
        L_ = v_len(n)
        if L_ < 1e-14:
            return
        n = v_mul(n, 1.0 / L_)
        d = v_dot(n, a)
        if v_dot(n, cen) > d:
            n, d = v_mul(n, -1.0), -d
        planes.append((n, d))
    for f in box:
        plane(f[0], f[1], f[2])
    # the shortest edges, so a cant never eats a whole face
    span = min(v_len(v_sub(q[(1, 0, 1)], q[(0, 0, 1)])), v_len(v_sub(q[(0, 1, 1)], q[(0, 0, 1)])),
               v_len(v_sub(q[(0, 0, 0)], q[(0, 0, 1)])))
    for edge, s in cant.items():
        s = min(s, 0.45 * span)
        if edge in ('top', 'bottom'):
            ih = 1 if edge == 'top' else 0
            pts = []
            for iu in (0, 1):
                A = q[(iu, ih, 1)]
                pts.append((A, _unit(A, q[(iu, 1 - ih, 1)]), _unit(A, q[(iu, ih, 0)])))
        else:
            iu = 0 if edge == 'end0' else 1
            pts = []
            for ih in (0, 1):
                A = q[(iu, ih, 1)]
                pts.append((A, _unit(A, q[(1 - iu, ih, 1)]), _unit(A, q[(iu, ih, 0)])))
        (A, a1, a2), (B, b1, _) = pts
        plane(v_add(A, v_mul(a1, s)), v_add(B, v_mul(b1, s)), v_add(A, v_mul(a2, s)))
    for a, b, c in (extra or []):         # e.g. one cant face across both legs of a corner brick
        plane(a, b, c)
    # the corners of the solid: where three planes meet, inside all the others
    tol = 1e-9
    verts = []
    m = len(planes)
    for i in range(m):
        for j in range(i + 1, m):
            for k in range(j + 1, m):
                (n1, d1), (n2, d2), (n3, d3) = planes[i], planes[j], planes[k]
                c23 = v_cross(n2, n3)
                det = v_dot(n1, c23)
                if abs(det) < 1e-10:
                    continue
                x = v_mul(v_add(v_add(v_mul(c23, d1), v_mul(v_cross(n3, n1), d2)), v_mul(v_cross(n1, n2), d3)),
                          1.0 / det)
                if all(v_dot(n, x) - d <= 1e-8 for n, d in planes):
                    if not any(v_len(v_sub(x, y)) < 1e-8 for y in verts):
                        verts.append(x)
    faces = []
    for n, d in planes:
        on = [x for x in verts if abs(v_dot(n, x) - d) < 1e-8]
        if len(on) < 3:
            continue
        c = v_mul(on[0], 0.0)
        for x in on:
            c = v_add(c, x)
        c = v_mul(c, 1.0 / len(on))
        e1 = v_norm(v_sub(on[0], c))
        e2 = v_cross(n, e1)
        on.sort(key=lambda x: math.atan2(v_dot(v_sub(x, c), e2), v_dot(v_sub(x, c), e1)))
        faces.append(on)                  # counter-clockwise seen from outside
    return faces if len(faces) >= 4 else box


def _join_faces(f1, f2):
    """Two flat faces sharing an edge (in opposite directions, as neighbours do), as one
    face; None if they don't share one."""
    n1, n2 = len(f1), len(f2)
    for i in range(n1):
        p, q = f1[i], f1[(i + 1) % n1]
        for j in range(n2):
            if f2[j] == q and f2[(j + 1) % n2] == p:
                a = f1[i + 1:] + f1[:i + 1]           # from q round to p
                b = f2[j + 1:] + f2[:j + 1]           # from p round to q
                out = a + b[1:-1]
                # leave out points in the middle of a straight edge
                clean_ = []
                m = len(out)
                for k in range(m):
                    p0, p1, p2 = out[k - 1], out[k], out[(k + 1) % m]
                    if v_len(v_cross(v_sub(p1, p0), v_sub(p2, p1))) > 1e-12:
                        clean_.append(p1)
                return clean_ if len(clean_) >= 3 else None
    return None


def fit_courses(v, z0, top, H, J, Jb, lean_cos):
    """Fit the courses to the height: a whole number of courses, the bed joints (between
    courses) evened out so the last one finishes at the top. Returns (bed joint, courses),
    or (the bed joint as set, 0) when it isn't fitted (turned off, or no bed joints at all)."""
    if not v.get('fit_height', True) or Jb <= 0:
        return Jb, 0
    avail = top - z0
    if avail < H:
        return Jb, 0
    cs = [lean_cos(z0 + avail * (k + 0.5) / 6.0) for k in range(6)]
    cb = sum(cs) / len(cs)
    # the highest point of the last course at the top: leaning back, a brick stands a little
    # less than its height, and its front edge rises above its back by its depth x the slope
    D = max(1.0, v.get('brick_d', 102.5)) * SCALE
    last = H / 2.0 * (1.0 + cb) + D * math.sqrt(max(0.0, 1.0 - cb * cb))
    room = avail - last                 # = (n - 1) * (H + bed) * cb
    n = int(round(room / ((H + J) * cb))) + 1
    while n > 1 and room / ((n - 1) * cb) - H < 0:
        n -= 1
    if n <= 1:
        return Jb, 1
    return room / ((n - 1) * cb) - H, n


def _brick_cant(v, course_cant, end0=0.0, end1=0.0):
    """The cants on one brick's front edges (metres), from the settings."""
    b = max(0.0, v.get('bevel', 0.0)) * SCALE
    return {'top': max(b, course_cant), 'bottom': b, 'end0': max(b, end0), 'end1': max(b, end1)}


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
    Jb = 0.0 if v.get('no_bed') else J           # the bed joint (between courses) can be left out
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

    def lean_cos(zm):
        """Leaning back with the taper, the bricks lie along the slope: a course then rises
        a little less than its height (the cosine of the slope, round the chimney on average)."""
        if level:
            return 1.0
        ez = H / 2.0
        cs = []
        for k in range(12):
            th = th0 + 2 * math.pi * k / 12
            dr = target.r(th, zm + ez) - target.r(th, zm - ez)
            cs.append((2 * ez) / math.hypot(dr, 2 * ez))
        return sum(cs) / len(cs)

    def pitch(zc_):
        return (H + Jb) * lean_cos(zc_ + H / 2.0)
    # the bed joints evened out so the courses finish at the top (Fit the courses to the height)
    Jb, n_fit = fit_courses(v, z0, top, H, J, Jb, lean_cos)
    # how many courses there will be (for a cant course at the top)
    n_courses = 0
    zz = z0
    while ((n_courses < n_fit) if n_fit else (zz + H <= top + 1e-9)) and n_courses < 100000:
        n_courses += 1
        zz += pitch(zz)
    cwhere = v.get('cant_where', 'none')
    csize = max(0.0, v.get('cant_course', 0.0)) * SCALE

    def course_cant(c_):
        if csize <= 0:
            return 0.0
        if c_ == n_courses - 1 and cwhere in ('top', 'both'):
            return csize
        if c_ == 0 and cwhere in ('bottom', 'both'):
            return csize
        return 0.0
    corner_cant = max(0.0, v.get('cant_corner', 0.0)) * SCALE
    each = v.get('_bricks_out')                  # (the close-up wants the bricks one by one)
    # corners of a square or many-sided chimney: bonded (one side's end brick runs past the
    # corner, turn and turn about) or special corner bricks (a dog-leg brick made to the
    # corner's own angle, mitred so it fits exactly, even where a taper leans the faces)
    squint = v.get('corner', 'bonded') == 'squint'

    def tilt(th, zm):
        """Up the face of the chimney at th, along its slope (a unit vector), for bricks that
        lean back with the taper."""
        ez = H / 2.0
        c0, c1 = surf(th, zm - ez), surf(th, zm + ez)
        Vd = v_norm((c1[0] - c0[0], c1[1] - c0[1], 2 * ez))
        if math.hypot(Vd[0], Vd[1]) > 0.7:          # steeper than about 45 degrees: stay upright
            Vd = (0.0, 0.0, 1.0)
        return Vd

    def box_faces(S, T, Vd, N, u0, u1, depth, pl0=None, pl1=None, cant=None, extra=None):
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
        return brick_faces(q, cant, extra)
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

        def mitre(fa, fb):
            """The plane half way between two neighbouring faces (through their corner), in the
            form box_faces slides a brick's end onto: ((0,0,0), unit normal, distance)."""
            Sa, _, _, Na, _ = fa
            Sb, _, _, Nb, _ = fb
            n = v_sub(Na, Nb)
            L_ = v_len(n) or 1.0
            return ((0.0, 0.0, 0.0), v_mul(n, 1.0 / L_), (v_dot(Sa, Na) - v_dot(Sb, Nb)) / L_)

        def corner_chamfer(fa, fb, depth_, cs):
            """Three points on the cant face across a corner brick's outside corner: cs back
            along each face from the corner, the same plane for both legs."""
            Sa, Ta, Va, Na, side_a = fa
            Sb, Tb, Vb, Nb, _ = fb
            out_ = []
            for hh in (-H / 2.0, H / 2.0):
                # the outside corner at this height: on both brick faces, at the course's top/bottom
                rows = [Na, Nb, Va]
                rhs = [v_dot(Sa, Na) + lift + depth_, v_dot(Sb, Nb) + lift + depth_, v_dot(Sa, Va) + hh]
                det = v_dot(rows[0], v_cross(rows[1], rows[2]))
                if abs(det) < 1e-12:
                    X = v_add(v_add(Sa, v_mul(Ta, side_a)), v_add(v_mul(Na, lift + depth_), v_mul(Va, hh)))
                else:
                    X = v_mul(v_add(v_add(v_mul(v_cross(rows[1], rows[2]), rhs[0]),
                                          v_mul(v_cross(rows[2], rows[0]), rhs[1])),
                                    v_mul(v_cross(rows[0], rows[1]), rhs[2])), 1.0 / det)
                out_.append((v_sub(X, v_mul(Ta, cs)), v_add(X, v_mul(Tb, cs))))
            (a0, b0), (a1, _) = out_
            return (a0, a1, b0)

        def join_legs(fa, fb, pl):
            """The two legs of a corner brick as one solid: the faces where they meet (on the
            mitre) are left out when they match exactly; otherwise the two are kept as they are."""
            if not fa or not fb:
                return (fa or []) + (fb or [])
            _, n_, d_ = pl

            def on(f):
                return all(abs(v_dot(p_, n_) - d_) < 1e-7 for p_ in f)
            ma, mb = [f for f in fa if on(f)], [f for f in fb if on(f)]
            if len(ma) == 1 and len(mb) == 1 and len(ma[0]) == len(mb[0]) and all(
                    min(v_len(v_sub(p_, q_)) for q_ in mb[0]) < 1e-7 for p_ in ma[0]):
                snap = {}
                for p_ in mb[0]:                  # the very same points on both sides of the join
                    snap[p_] = min(ma[0], key=lambda q_: v_len(v_sub(p_, q_)))
                ra = [f for f in fa if f is not ma[0]]
                rb = [[snap.get(p_, p_) for p_ in f] for f in fb if f is not mb[0]]
                # faces of the two legs that lie flat together across the join (the top and
                # bottom of a level course, a cant across the corner) become one face, no line
                for i_, f1 in enumerate(ra):
                    n1 = v_norm(_newell3(f1))
                    for j_, f2 in enumerate(rb):
                        if f2 is None or v_dot(n1, v_norm(_newell3(f2))) < 1 - 1e-9:
                            continue
                        u_ = _join_faces(f1, f2)
                        if u_:
                            ra[i_], rb[j_] = u_, None
                            break
                return ra + [f for f in rb if f is not None]
            return fa + fb

        while (c < n_fit) if n_fit else (zc + H <= top + 1e-9):
            this_cuts = {}
            legs = {}
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
                Vd = (0.0, 0.0, 1.0) if level else tilt(am, zm)
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
                if squint:
                    # the corner bricks' legs: a whole brick along this side and half a brick
                    # along the next, swapping round each course, so the bond still steps half a brick
                    s0 = 0.0 if long_side else -unit / 2.0
                    s1 = side if long_side else side + unit / 2.0
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
                if squint:
                    # corner bricks first: a leg of a whole brick (or half a brick) from each
                    # corner, then the side set out between them as usual
                    l0 = l1 = unit if long_side else unit / 2.0
                    x1, x2 = l0, side + J - l1
                    if x2 - x1 < 0.45 * unit:
                        cuts = [0.0, (side + J) / 2.0, side + J]     # room for the corner bricks only
                    else:
                        cuts = [0.0] + set_out_middle(x1, x2, B, unit) + [side + J]
                else:
                    cuts = set_out(s0, s1 + J, B, unit, side)
                # the joints this course leaves on this face, for the course above (a course
                # that stops short of the corners also has a joint at each end, by the corner brick)
                if squint:
                    this_cuts[si] = (cuts[1:-1], side)
                else:
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
                if squint:
                    # the two legs of each corner brick meet on the plane half way between the
                    # two faces (a mitre), so the brick fits the corner exactly
                    pl0 = mitre(frames[(si - 1) % nc], frames[si])
                    pl1 = mitre(frames[si], frames[(si + 1) % nc])
                spans = list(zip(cuts[:-1], cuts[1:]))
                cc = course_cant(c)
                for k_, (ca, cb) in enumerate(spans):
                    if cb - J - ca < 0.25 * (L if not header else D) * 0.5:
                        continue
                    first, last = k_ == 0, k_ == len(spans) - 1
                    extra = []
                    if squint:
                        # a corner brick: no bevel of its own on the corner (it's one brick round
                        # the corner); a cant (or the bevel) is one face across both its legs
                        cant = _brick_cant(v, cc)
                        cs_ = max(corner_cant, max(0.0, v.get('bevel', 0.0)) * SCALE)
                        if first:
                            cant['end0'] = 0.0
                            if cs_ > 0:
                                extra.append(corner_chamfer(frames[(si - 1) % nc], frames[si], depth, cs_))
                        if last:
                            cant['end1'] = 0.0
                            if cs_ > 0:
                                extra.append(corner_chamfer(frames[si], frames[(si + 1) % nc], depth, cs_))
                    else:
                        # a cant brick at the corner: the brick that runs past the corner has its
                        # outside corner cut back
                        cant = _brick_cant(v, cc, corner_cant if (long_side and first) else 0.0,
                                           corner_cant if (long_side and last) else 0.0)
                    bf = box_faces(S, T, Vd, N, ca, cb - J, depth,
                                   pl0 if first else None, pl1 if last else None, cant, extra)
                    if squint and first != last:
                        # the legs of a corner brick: joined into one brick once the course is done
                        if first:
                            legs.setdefault(si, [None, None])[1] = bf
                        else:
                            legs.setdefault((si + 1) % nc, [None, None])[0] = bf
                        continue
                    faces += bf
                    if each is not None:
                        each.append(bf)
                    bricks += 1
            for ci, (la_, lb_) in legs.items():
                # one corner brick: the two legs (each side's end brick) joined on the mitre
                pc = mitre(frames[(ci - 1) % nc], frames[ci])
                bf = join_legs(la_, lb_, pc)
                if bf:
                    faces += bf
                    if each is not None:
                        each.append(bf)
                    bricks += 1
            prev_cuts = this_cuts
            courses += 1
            c += 1
            zc += pitch(zc)
        return faces, {'courses': courses, 'bricks': bricks, 'corners': nc, 'bed': Jb, 'fit': bool(n_fit)}
    frac_prev, n_prev = 0.0, 0
    prev_ring = None              # the angles of the joints in the course below
    while (c < n_fit) if n_fit else (zc + H <= top + 1e-9):
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
                # leaning back with the taper: the brick is turned to lie flat on the slope
                # (its back along the chimney's face, its bed square to it)
                Vd = tilt(tc, zm)
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
            bf = brick_faces(q, _brick_cant(v, course_cant(c)))
            faces += bf
            if each is not None:
                each.append(bf)
            bricks += 1
        courses += 1
        c += 1
        zc += pitch(zc)
    return faces, {'courses': courses, 'bricks': bricks, 'bed': Jb, 'fit': bool(n_fit)}


# ---------------------------------------------------------------------------
# A wall that goes only part way round (a curved wall with two ends)
# ---------------------------------------------------------------------------
def _fit_circle(pts):
    """The circle (cx, cy, r) nearest all the points (least squares)."""
    n = float(len(pts))
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    Sxx = Sxy = Syy = Sx = Sy = Sxz = Syz = Sz = 0.0
    for p in pts:
        x, y = p[0] - mx, p[1] - my
        z = x * x + y * y
        Sxx += x * x
        Sxy += x * y
        Syy += y * y
        Sx += x
        Sy += y
        Sxz += x * z
        Syz += y * z
        Sz += z
    M = [[Sxx, Sxy, Sx], [Sxy, Syy, Sy], [Sx, Sy, n]]
    b = [-Sxz, -Syz, -Sz]

    def det3(m):
        return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
                + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
    d = det3(M)
    if abs(d) < 1e-18:
        raise ValueError("Couldn't find the centre of the curved wall (is it straight?).")
    sol = []
    for k in range(3):
        Mk = [row[:] for row in M]
        for i in range(3):
            Mk[i][k] = b[i]
        sol.append(det3(Mk) / d)
    D_, E_, F_ = sol
    cx, cy = -D_ / 2.0, -E_ / 2.0
    r2 = cx * cx + cy * cy - F_
    if r2 <= 0:
        raise ValueError("Couldn't find the centre of the curved wall.")
    return cx + mx, cy + my, math.sqrt(r2)


def _tris_of(faces):
    tris = []
    for o, hs in faces:
        for t in triangles(o):
            tris.append(t)
    return tris


def _slice_tris(tris, z, cx, cy):
    segs = []
    for t in tris:
        pts = []
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            if (a[2] <= z) != (b[2] <= z):
                s_ = (z - a[2]) / (b[2] - a[2])
                pts.append((a[0] + s_ * (b[0] - a[0]) - cx, a[1] + s_ * (b[1] - a[1]) - cy))
        if len(pts) == 2:
            segs.append(pts)
    return segs


def is_open_wall(faces):
    """True for a solid that doesn't go all the way round its middle (a curved wall with two
    ends, say): looking out from its middle, some directions see nothing."""
    tris = _tris_of(faces)
    if not tris:
        return False
    xs = [p[0] for t in tris for p in t]
    ys = [p[1] for t in tris for p in t]
    zs = [p[2] for t in tris for p in t]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    z = min(zs) + 0.5 * (max(zs) - min(zs))
    angs = [2 * math.pi * k / 180 for k in range(180)]
    row = MeshTarget._rays(_slice_tris(tris, z, cx, cy), angs)
    return sum(1 for r_ in row if r_ == 0.0) > 18


class ArcTarget:
    """A wall that goes part way round a circle: its centre, where its two ends are, and how
    far out its outside and inside faces are, all the way up."""

    def __init__(self, faces):
        tris = _tris_of(faces)
        if not tris:
            raise ValueError("The target group has no faces.")
        zs = [p[2] for t in tris for p in t]
        self.z0, self.z1 = min(zs), max(zs)
        self.h = self.z1 - self.z0
        if self.h <= 0:
            raise ValueError("The wall needs some height.")
        pts = []
        for fz in (0.25, 0.5, 0.75):
            for a, b in _slice_tris(tris, self.z0 + self.h * fz, 0.0, 0.0):
                pts += [a, b]
        if len(pts) < 6:
            raise ValueError("Couldn't find the curved wall's outline.")
        self.cx, self.cy, self.R = _fit_circle(pts)
        # again from the outside face alone (the ends and the inside pull the first try about)
        for _ in range(2):
            outer = [p for p in pts if math.hypot(p[0] - self.cx, p[1] - self.cy) >= self.R]
            if len(outer) >= 6:
                try:
                    self.cx, self.cy, _r = _fit_circle(outer)
                except ValueError:
                    break
        rs = sorted(math.hypot(p[0] - self.cx, p[1] - self.cy) for p in pts)
        self.R = rs[len(rs) // 2]
        # where it starts and stops: the biggest gap in the angles of its outline is the open side
        ang = sorted(math.atan2(p[1] - self.cy, p[0] - self.cx) % (2 * math.pi) for p in pts)
        gaps = [((ang[(i + 1) % len(ang)] - ang[i]) % (2 * math.pi), i) for i in range(len(ang))]
        g, i = max(gaps)
        if g < math.radians(8):
            raise ValueError("The wall goes all the way round.")
        self.a0 = ang[(i + 1) % len(ang)]
        self.a1 = self.a0 + (2 * math.pi - g)
        self.span = self.a1 - self.a0
        na = max(48, int(math.degrees(self.span)))
        e_ = min(1e-3, self.span / (4 * na))
        self.angs = [self.a0 + e_ + (self.span - 2 * e_) * k / na for k in range(na + 1)]
        self.na = len(self.angs)
        self.nz = nz = int(min(300, max(40, self.h / 0.02)))
        go, gi = [], []
        for iz in range(nz + 1):
            z = self.z0 + self.h * (0.002 + 0.996 * iz / nz)
            segs = _slice_tris(tris, z, self.cx, self.cy)
            ro, ri = [], []
            for th in self.angs:
                dx, dy = math.cos(th), math.sin(th)
                lo, hi = 0.0, 0.0
                for (ax_, ay_), (bx_, by_) in segs:
                    ex, ey = bx_ - ax_, by_ - ay_
                    den = dx * ey - dy * ex
                    if abs(den) < 1e-15:
                        continue
                    tt = (ax_ * ey - ay_ * ex) / den
                    ss = (ax_ * dy - ay_ * dx) / den
                    if tt > 0 and -1e-9 <= ss <= 1 + 1e-9:
                        hi = max(hi, tt)
                        lo = tt if lo == 0.0 else min(lo, tt)
                ro.append(hi)
                ri.append(lo)
            go.append(ro)
            gi.append(ri)
        for grid in (go, gi):
            for row in grid:                         # misses: from the neighbours
                for k in range(len(row)):
                    if row[k] == 0.0:
                        near = [row[j] for j in range(len(row)) if row[j] > 0.0]
                        if near:
                            j = min((j for j in range(len(row)) if row[j] > 0.0), key=lambda j: abs(j - k))
                            row[k] = row[j]
            have = [i for i, row in enumerate(grid) if any(row)]
            if not have:
                raise ValueError("Couldn't find the faces of the curved wall.")
            for i, row in enumerate(grid):
                if not any(row):
                    j = min(have, key=lambda j: abs(j - i))
                    grid[i] = list(grid[j])
        self.go, self.gi = go, gi

    def corners(self):
        return []

    def r(self, th, z, side='out'):
        rel = (th - self.a0) % (2 * math.pi)
        if rel > self.span:                           # past an end: the end's own value
            rel = self.span if (rel - self.span) < (2 * math.pi - rel) else 0.0
        th = self.a0 + rel
        A = self.angs
        fa = (th - A[0]) / ((A[-1] - A[0]) or 1.0) * (self.na - 1)
        fa = min(max(fa, 0.0), self.na - 1.0)
        ia = min(int(fa), self.na - 2)
        ta = fa - ia
        fz = min(max((z - self.z0) / self.h, 0.0), 1.0) * self.nz
        iz = min(int(fz), self.nz - 1)
        tz = fz - iz
        g = self.go if side == 'out' else self.gi
        r0 = g[iz][ia] * (1 - ta) + g[iz][ia + 1] * ta
        r1 = g[iz + 1][ia] * (1 - ta) + g[iz + 1][ia + 1] * ta
        return r0 * (1 - tz) + r1 * tz


FACES = [("outside", "Outside"), ("inside", "Inside"), ("both", "Outside and inside")]
WALL_ENDS = [("stopped", "Stopped (whole and half bricks)"), ("toothed", "Toothed (every other course out)"),
             ("return", "Return round the end")]


def lay_arc_bricks(tg, v):
    """Bricks along a part-round wall, course by course, on its outside face, inside face or
    both, from one end to the other in half-brick bond, finished at the ends as chosen.
    Returns ([faces in world metres], info)."""
    L = max(10.0, v['brick_l']) * SCALE
    H = max(5.0, v['brick_h']) * SCALE
    D = max(1.0, v['brick_d']) * SCALE
    J = max(0.2, v['joint']) * SCALE
    lift = v['lift'] * SCALE
    Jb = 0.0 if v.get('no_bed') else J
    every = int(v.get('header_every', 0))
    level = bool(v.get('level', True))
    sides = {'outside': ['out'], 'inside': ['in'], 'both': ['out', 'in']}[v.get('faces', 'outside')]
    ends = v.get('ends', 'stopped')
    each = v.get('_bricks_out')
    z0 = tg.z0 + v['raise'] * SCALE
    top = tg.z0 + tg.h if v.get('lay_h', 0) <= 0 else min(tg.z0 + tg.h, z0 + v['lay_h'] * SCALE)
    a0, a1 = tg.a0, tg.a1
    cx, cy = tg.cx, tg.cy
    faces = []
    bricks = 0

    def surf(th, z, s):
        r = tg.r(th, z, s)
        return (cx + r * math.cos(th), cy + r * math.sin(th))

    def lean_cos(zm):
        if level:
            return 1.0
        ez = H / 2.0
        cs = []
        for k in range(9):
            th = a0 + (a1 - a0) * (k + 0.5) / 9
            dr = tg.r(th, zm + ez) - tg.r(th, zm - ez)
            cs.append((2 * ez) / math.hypot(dr, 2 * ez))
        return sum(cs) / len(cs)

    def pitch(zc_):
        return (H + Jb) * lean_cos(zc_ + H / 2.0)
    Jb, n_fit = fit_courses(v, z0, top, H, J, Jb, lean_cos)
    n_courses = 0
    zz = z0
    while ((n_courses < n_fit) if n_fit else (zz + H <= top + 1e-9)) and n_courses < 100000:
        n_courses += 1
        zz += pitch(zz)
    cwhere = v.get('cant_where', 'none')
    csize = max(0.0, v.get('cant_course', 0.0)) * SCALE

    def course_cant(c_):
        if csize <= 0:
            return 0.0
        if c_ == n_courses - 1 and cwhere in ('top', 'both'):
            return csize
        if c_ == 0 and cwhere in ('bottom', 'both'):
            return csize
        return 0.0

    def add(bf):
        nonlocal faces, bricks
        faces += bf
        if each is not None:
            each.append(bf)
        bricks += 1

    def onto_end(X, T, a_end, outward, off):
        """Slide X along the brick (T) onto the plane off beyond the wall's end at a_end."""
        n_ = (math.sin(a_end), -math.cos(a_end), 0.0) if outward < 0 else (-math.sin(a_end), math.cos(a_end), 0.0)
        tn = T[0] * n_[0] + T[1] * n_[1]
        if abs(tn) < 0.2:
            return X
        cur = (X[0] - cx) * n_[0] + (X[1] - cy) * n_[1]
        t_ = (off - cur) / tn
        return (X[0] + T[0] * t_, X[1] + T[1] * t_, X[2])

    zc = z0
    c = 0
    while (c < n_fit) if n_fit else (zc + H <= top + 1e-9):
        zm = zc + H / 2.0
        ez = H / 2.0
        header = every > 0 and (c % every == every - 1)
        unit = (D if header else L) + J
        depth = D if not header else L
        odd = c % 2 == 1
        cant_c = _brick_cant(v, course_cant(c))
        for s in sides:
            m = 240
            ths = [a0 + (a1 - a0) * k / m for k in range(m + 1)]
            pts = [surf(th, zm, s) for th in ths]
            cum = [0.0]
            for k in range(m):
                cum.append(cum[-1] + math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]))
            S_len = cum[-1]
            r_a0, r_a1 = max(1e-6, tg.r(a0, zm, s)), max(1e-6, tg.r(a1, zm, s))

            def theta_at(sv):
                if sv <= 0:
                    return a0 + sv / r_a0
                if sv >= S_len:
                    return a1 + (sv - S_len) / r_a1
                lo, hi = 0, m
                while hi - lo > 1:
                    mid = (lo + hi) // 2
                    if cum[mid] <= sv:
                        lo = mid
                    else:
                        hi = mid
                t = (sv - cum[lo]) / ((cum[hi] - cum[lo]) or 1.0)
                return a0 + (a1 - a0) * (lo + t) / m
            n = max(1, int(math.ceil(S_len / unit - 1e-9)))
            step = S_len / n
            # the set-out: whole bricks one course; the next a half brick each end (stopped and
            # returned), or a half brick out past each end (toothed), so the bond steps half a brick
            if odd and ends == 'toothed':
                pieces = [(-step / 2 + k * step, step / 2 + k * step) for k in range(n + 1)]
            elif odd:
                pieces = [(0.0, step / 2)] + [(step / 2 + k * step, step / 2 + (k + 1) * step)
                                             for k in range(n - 1)] + [(S_len - step / 2, S_len)]
            else:
                pieces = [(k * step, (k + 1) * step) for k in range(n)]
            ret_run = ends == 'return' and not odd      # face bricks run past the end bricks
            for k_, (pa, pb) in enumerate(pieces):
                first, last = k_ == 0, k_ == len(pieces) - 1
                sa = pa if first else pa + J / 2.0
                sb = pb if last else pb - J / 2.0
                if ends == 'return' and odd:
                    if first:
                        sa += J                       # a joint against the end brick
                    if last:
                        sb -= J
                if sb - sa < 0.2 * unit:
                    continue
                ta, tb = theta_at(sa), theta_at(sb)
                tc = (ta + tb) / 2.0
                phi = (tb - ta) / 2.0
                e = 1e-5
                A_, B_ = surf(tc - e, zm, s), surf(tc + e, zm, s)
                tx, ty = B_[0] - A_[0], B_[1] - A_[1]
                Lt = math.hypot(tx, ty) or 1.0
                T = (tx / Lt, ty / Lt, 0.0)
                zb = zm
                if level:
                    Vd = (0.0, 0.0, 1.0)
                    r_lo, r_hi = tg.r(tc, zm - ez, s), tg.r(tc, zm + ez, s)
                    # the back where the face stands out furthest over the brick's height
                    if s == 'out':
                        zb = zm - ez if r_lo >= r_hi else zm + ez
                    else:
                        zb = zm - ez if r_lo <= r_hi else zm + ez
                else:
                    c0, c1 = surf(tc, zm - ez, s), surf(tc, zm + ez, s)
                    Vd = v_norm((c1[0] - c0[0], c1[1] - c0[1], 2 * ez))
                    if math.hypot(Vd[0], Vd[1]) > 0.7:
                        Vd = (0.0, 0.0, 1.0)
                if s == 'in':
                    T = (-T[0], -T[1], 0.0)           # so the bricks face in, towards the middle
                N = v_norm(v_cross(T, Vd))
                x, y = surf(tc, zb, s)
                S = (x, y, zm)
                r_ = max(1e-6, tg.r(tc, zb, s))
                half = r_ * math.sin(phi)
                flare = math.tan(phi) if s == 'out' else -math.tan(phi)
                q = {}
                for iu, sg in enumerate((-1.0, 1.0)):
                    for ih, hh in enumerate((-H / 2.0, H / 2.0)):
                        for iw, ww in enumerate((lift, lift + depth)):
                            uu = sg * (half + ww * flare)
                            q[(iu, ih, iw)] = (S[0] + T[0] * uu + Vd[0] * hh + N[0] * ww,
                                               S[1] + T[1] * uu + Vd[1] * hh + N[1] * ww,
                                               S[2] + Vd[2] * hh + N[2] * ww)
                # the ends at the wall's ends: flat on the end (or, running past an end brick,
                # flush with the end brick's face)
                stops = not (ends == 'return' and odd)   # (those stop short of the end bricks)
                for at_start, is_end in ((True, first and abs(pa) < 1e-12 and stops),
                                         (False, last and abs(pb - S_len) < 1e-12 and stops)):
                    if not is_end:
                        continue
                    a_end = a0 if at_start else a1
                    outward = -1 if at_start else 1
                    off = (lift + D) if ret_run else 0.0
                    # which of the brick's two ends is this one (the inside bricks run the other way)
                    iu = (0 if at_start else 1) if s == 'out' else (1 if at_start else 0)
                    for ih in (0, 1):
                        for iw in (0, 1):
                            q[(iu, ih, iw)] = onto_end(q[(iu, ih, iw)], T, a_end, outward, off)
                add(brick_faces(q, cant_c))
        # bricks across the ends of the wall (Return round the end)
        if ends == 'return':
            for a_end, outward in ((a0, -1), (a1, 1)):
                a_in = a_end - outward * 1e-3
                r_in, r_out = tg.r(a_in, zm, 'in'), tg.r(a_in, zm, 'out')
                d_out = (lift + depth) if 'out' in sides else 0.0
                d_in = (lift + depth) if 'in' in sides else 0.0
                if odd:                                   # across the ends of the face bricks too
                    lo, hi = r_in - d_in, r_out + d_out
                else:                                     # between the face bricks running past
                    lo = r_in + (J if 'in' in sides else 0.0)
                    hi = r_out - (J if 'out' in sides else 0.0)
                Wd = hi - lo
                if Wd <= 0.2 * L:
                    continue
                k = max(1, int(math.ceil(Wd / (L + J) - 1e-9)))
                seg = Wd / k
                Rv = (math.cos(a_end), math.sin(a_end), 0.0)
                Tn = (math.sin(a_end), -math.cos(a_end), 0.0) if outward < 0 else \
                    (-math.sin(a_end), math.cos(a_end), 0.0)
                T = Rv if outward < 0 else (-Rv[0], -Rv[1], 0.0)
                Vd = (0.0, 0.0, 1.0)
                N = Tn
                for i in range(k):
                    u0 = lo + i * seg + (J / 2.0 if i > 0 else 0.0)
                    u1 = lo + (i + 1) * seg - (J / 2.0 if i < k - 1 else 0.0)
                    if outward > 0:
                        u0, u1 = -u1, -u0
                    q = {}
                    for iu, uu in enumerate((u0, u1)):
                        for ih, hh in enumerate((-H / 2.0, H / 2.0)):
                            for iw, ww in enumerate((lift, lift + D)):
                                q[(iu, ih, iw)] = (cx + T[0] * uu + N[0] * ww, cy + T[1] * uu + N[1] * ww, zm + hh)
                    add(brick_faces(q, cant_c))
        c += 1
        zc += pitch(zc)
    return faces, {'courses': c, 'bricks': bricks, 'span': math.degrees(a1 - a0), 'radius': tg.R, 'bed': Jb,
                   'fit': bool(n_fit)}


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
                flip=False, scale_depth=False, level=True, no_bed=False, bevel=0.0, cant_corner=0.0,
                cant_where='none', cant_course=30.0, corner='squint', faces='outside', ends='stopped',
                fit_height=True)
CANT_WHERE = [("none", "None"), ("top", "Top course"), ("bottom", "Bottom course"), ("both", "Top and bottom")]
COURSE_LAY = [(True, "Level (step in up a taper)"), (False, "Lean back with the taper")]
CORNERS = [("squint", "Special corner bricks"), ("bonded", "Bonded (run past the corner)")]
# what a 'Bricks only' preset keeps
BRICK_KEYS = ('brick_l', 'brick_h', 'brick_d', 'joint', 'header_every', 'level', 'no_bed', 'bevel',
              'cant_corner', 'cant_where', 'cant_course', 'corner', 'faces', 'ends', 'fit_height')

# ---------------------------------------------------------------------------
# Presets: your own setups, saved as files, and one of them as the default
# ---------------------------------------------------------------------------
PRESETS_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Wrap")
DEFAULT_FILE = os.path.join(PRESETS_DIR, "_default.txt")


def load_presets():
    out = []
    try:
        for fn in sorted(os.listdir(PRESETS_DIR), key=str.lower):
            if fn.lower().endswith(".json"):
                try:
                    with open(os.path.join(PRESETS_DIR, fn), "r", encoding="utf-8") as f:
                        d = json.load(f)
                    if isinstance(d, dict):
                        out.append((fn[:-5], d))
                except Exception:
                    pass
    except Exception:
        pass
    return out


def save_preset(name, values):
    os.makedirs(PRESETS_DIR, exist_ok=True)
    safe = "".join(ch for ch in name if ch not in '\\/:*?"<>|').strip().lstrip("_") or "My bricks"
    with open(os.path.join(PRESETS_DIR, safe + ".json"), "w", encoding="utf-8") as f:
        json.dump(values, f, indent=1)
    return safe


def delete_preset(name):
    try:
        os.remove(os.path.join(PRESETS_DIR, name + ".json"))
    except Exception:
        pass
    if default_preset() == name:
        set_default_preset(None)


def default_preset():
    try:
        with open(DEFAULT_FILE, "r", encoding="utf-8") as f:
            name = f.read().strip()
        return name if os.path.exists(os.path.join(PRESETS_DIR, name + ".json")) else None
    except Exception:
        return None


def set_default_preset(name):
    try:
        if name:
            os.makedirs(PRESETS_DIR, exist_ok=True)
            with open(DEFAULT_FILE, "w", encoding="utf-8") as f:
                f.write(name)
        elif os.path.exists(DEFAULT_FILE):
            os.remove(DEFAULT_FILE)
    except Exception:
        pass


def preset_values(name):
    for n, d in load_presets():
        if n == name:
            return {k: v for k, v in d.items() if not k.startswith("_")}
    return {}


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

EDDY_TIPS = {'Close-up': "A few bricks close up, as they'll be laid with the settings in the window. "
                         "It changes as you change them.",
             'Sizes (A, B, C ...)': "What each lettered size (A, B, C ...) measures. The letters are next to "
                                    "the boxes on the right."}
EDDY_TIPS_END = None


# ---------------------------------------------------------------------------
# Close-up and sizes drawings (the two tabs beside the settings)
# ---------------------------------------------------------------------------
# each size has a letter, shown next to its box and on the 'Sizes' drawing
LETTERS = {'bottom': 'A', 'top': 'B', 'height': 'C', 'raise_': 'D', 'lay_h': 'E',
           'brick_l': 'F', 'brick_h': 'G', 'brick_d': 'H', 'joint': 'J', 'bevel': 'K',
           'cant_course': 'L', 'cant_corner': 'M'}
CLOSEUP_COURSES = 5


def closeup_bricks(v):
    """A few courses of the bricks as they'd be laid with these settings, round the front
    of the chimney (at a corner, on a square or many-sided one): ([brick faces...],
    [core faces], the angle looked at, a caption)."""
    mesh = v.get('target') == 'mesh'
    shape = 'round' if mesh else v.get('target', 'round')
    b = 1200.0 if mesh else max(50.0, v['bottom'])
    t_ = 1200.0 if mesh else max(10.0, v['top'])
    h_full = 6000.0 if mesh else max(50.0, v['height'])
    Jb = 0.0 if v.get('no_bed') else v['joint']
    hs = CLOSEUP_COURSES * (v['brick_h'] + Jb) + 0.5 * v['brick_h']
    top_s = b - (b - t_) * min(1.0, hs / h_full)          # the same taper as the real one
    tg = ShapeTarget(shape, 0.0, 0.0, 0.0, hs * SCALE, b * SCALE, top_s * SCALE)
    vv = dict(v)
    vv.update(raise_=0.0, lay_h=0.0, start=0.0)
    vv['raise'] = 0.0
    out = []
    vv['_bricks_out'] = out
    lay_bricks(tg, vv)
    cs = tg.corners()
    focus = cs[0] if cs else 0.0
    if shape == 'square':
        half = math.radians(32)
    elif shape == 'octagon':
        half = math.radians(19)
    else:
        half = min(math.radians(40), 1.9 * v['brick_l'] / (b / 2.0))

    def near(pts):
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        return abs((math.atan2(cy, cx) - focus + math.pi) % (2 * math.pi) - math.pi) <= half
    bricks = [bf for bf in out if near([p for f in bf for p in f])]
    core = [f for f in tg.solid_faces(n=144) if near(f)]
    words = {'round': "round", 'square': "square", 'octagon': "octagonal"}[shape]
    cap = "Close-up: %d courses, %s%s, %s" % (CLOSEUP_COURSES, words, " (a sample)" if mesh else "",
                                             "level" if v.get('level', True) else "leaning back")
    return bricks, core, focus, cap


def closeup_arc(v, tg):
    """The close-up for a curved wall: a few courses at one end of the wall itself."""
    Jb = 0.0 if v.get('no_bed') else v['joint']
    hs = CLOSEUP_COURSES * (v['brick_h'] + Jb) + 0.5 * v['brick_h']
    vv = dict(v)
    vv.update(raise_=0.0, lay_h=hs)
    vv['raise'] = 0.0
    out = []
    vv['_bricks_out'] = out
    lay_arc_bricks(tg, vv)
    a0 = tg.a0
    reach = min(tg.span, 2.6 * v['brick_l'] * SCALE / max(tg.R, 1e-6))

    def ang_of(pts):
        cx_ = sum(p[0] for p in pts) / len(pts) - tg.cx
        cy_ = sum(p[1] for p in pts) / len(pts) - tg.cy
        return (math.atan2(cy_, cx_) - a0 + math.pi) % (2 * math.pi) - math.pi
    bricks = [bf for bf in out if -0.2 < ang_of([p for f in bf for p in f]) < reach]
    # the wall itself, round to the end
    core = []
    z0, z1 = tg.z0, tg.z0 + hs * SCALE
    n = 24
    angs = [a0 + reach * k / n for k in range(n + 1)]

    def P(a, side, z):
        r_ = tg.r(a, z, side)
        return (tg.cx + r_ * math.cos(a), tg.cy + r_ * math.sin(a), z)
    for k in range(n):
        A, B = angs[k], angs[k + 1]
        core.append([P(A, 'out', z0), P(B, 'out', z0), P(B, 'out', z1), P(A, 'out', z1)])
        core.append([P(B, 'in', z0), P(A, 'in', z0), P(A, 'in', z1), P(B, 'in', z1)])
        core.append([P(A, 'in', z1), P(A, 'out', z1), P(B, 'out', z1), P(B, 'in', z1)])
    core.append([P(a0, 'in', z0), P(a0, 'out', z0), P(a0, 'out', z1), P(a0, 'in', z1)][::-1])
    cap = "Close-up: the end of your curved wall, %s, ends %s" % (
        dict(FACES)[v.get('faces', 'outside')].lower(), dict(WALL_ENDS)[v.get('ends', 'stopped')].split(" (")[0].lower())
    return bricks, core, a0 + reach * 0.35, cap


class CloseupView(QWidget):
    """A few bricks, close up and shaded, as they'll be laid with the settings now in the window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            self.setMinimumSize(300, 330)
        except Exception:
            pass
        self.polys = []
        self.msg = ""
        self.cap = ""

    def show_values(self, v, arc=None):
        self.polys, self.msg, self.cap = [], "", ""
        if v.get('source') != 'bricks':
            self.msg = "The close-up shows new bricks.\n\nYour own pattern is bent round as it is."
        else:
            try:
                if arc is not None:
                    bricks, core, focus, self.cap = closeup_arc(v, arc)
                else:
                    bricks, core, focus, self.cap = closeup_bricks(v)
                self.polys = self._project(bricks, core, focus)
                if not self.polys:
                    self.msg = "No bricks fit: check the sizes."
            except Exception as e:
                self.msg = "No close-up: %s" % e
        try:
            self.update()
        except Exception:
            pass

    @staticmethod
    def _project(bricks, core, focus):
        az = focus - math.radians(22)
        el = math.radians(16)
        d = (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))   # to the viewer
        right = (-math.sin(az), math.cos(az), 0.0)
        up = v_cross(d, right)
        light = v_norm((0.45, -0.55, 0.7))
        light = v_norm(v_add(v_mul(d, 0.6), v_mul(light, 0.8)))
        def faces_of(faces, rgb, edge):
            out_ = []
            for f in faces:
                n = v_norm(_newell3(f))
                if v_dot(n, d) <= 1e-6:
                    continue                                   # facing away
                sh = 0.42 + 0.58 * max(0.0, v_dot(n, light))
                out_.append((0.0, [(v_dot(p, right), v_dot(p, up)) for p in f],
                             tuple(int(c * sh) for c in rgb), edge))
            return out_
        # the chimney behind, then the bricks one whole brick at a time, the furthest first
        # (each brick's own visible faces never hide each other)
        out = []
        for f in sorted(core, key=lambda f: sum(v_dot(p, d) for p in f) / len(f)):
            out += faces_of([f], (200, 196, 188), (150, 146, 140))
        keyed = []
        for bf in bricks:
            pts = [p for f in bf for p in f]
            keyed.append((sum(v_dot(p, d) for p in pts) / len(pts), bf))
        keyed.sort(key=lambda z: z[0])
        for _, bf in keyed:
            out += faces_of(bf, (178, 86, 58), (95, 42, 26))
        return out

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen
        from PySide6.QtCore import QPointF, Qt, QRectF
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.Antialiasing)
            p.fillRect(self.rect(), QColor(244, 245, 247))
            if not self.polys:
                p.setPen(QColor(90, 90, 90))
                p.drawText(QRectF(self.rect().adjusted(12, 12, -12, -12)), Qt.AlignCenter | Qt.TextWordWrap,
                           self.msg or "No close-up")
                return
            xs = [x for _, pts, _, _ in self.polys for x, _ in pts]
            ys = [y for _, pts, _, _ in self.polys for _, y in pts]
            W, H = self.width(), self.height()
            sc = min((W - 20) / ((max(xs) - min(xs)) or 1), (H - 40) / ((max(ys) - min(ys)) or 1))
            ox = W / 2 - (max(xs) + min(xs)) / 2 * sc
            oy = (H - 20) / 2 + (max(ys) + min(ys)) / 2 * sc
            for _, pts, rgb, edge in self.polys:
                p.setBrush(QColor(*rgb))
                p.setPen(QPen(QColor(*edge), 0.6))
                p.drawPolygon(QPolygonF([QPointF(ox + x * sc, oy - y * sc) for x, y in pts]))
            p.setPen(QColor(80, 80, 80))
            p.drawText(QRectF(6, H - 20, W - 12, 18), Qt.AlignLeft | Qt.AlignVCenter, self.cap)
        finally:
            p.end()


class SizesView(QWidget):
    """What each lettered size measures: the chimney, a brick from the front, a cut through
    the courses, and a corner seen from above."""

    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            self.setMinimumSize(300, 330)
        except Exception:
            pass
        self.v = dict(DEFAULTS)

    def show_values(self, v):
        self.v = dict(v)
        try:
            self.update()
        except Exception:
            pass

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen, QFont, QBrush
        from PySide6.QtCore import QPointF, Qt, QRectF
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.Antialiasing)
            p.fillRect(self.rect(), QColor(252, 252, 250))
            W, H = self.width(), self.height()
            v = self.v
            BR, BRE, CORE, CE = QColor(196, 104, 72), QColor(110, 50, 30), QColor(214, 210, 202), QColor(150, 146, 140)
            BLUE = QColor(20, 90, 200)
            small = QFont()
            small.setPointSize(7)
            bold = QFont()
            bold.setPointSize(8)
            bold.setBold(True)

            def panel(rect, title, shapes, dims, pad=26):
                """shapes: [(points mm, fill, edge)], dims: [(letter, a, b, side (x, y) away)]."""
                xs = [x for pts, _, _ in shapes for x, _ in pts]
                ys = [y for pts, _, _ in shapes for _, y in pts]
                if not xs:
                    return
                x0, y0, w_, h_ = rect
                sc = min((w_ - 2 * pad) / ((max(xs) - min(xs)) or 1), (h_ - 2 * pad - 12) / ((max(ys) - min(ys)) or 1))
                ox = x0 + w_ / 2 - (max(xs) + min(xs)) / 2 * sc
                oy = y0 + 12 + (h_ - 12) / 2 + (max(ys) + min(ys)) / 2 * sc

                def P(q):
                    return QPointF(ox + q[0] * sc, oy - q[1] * sc)
                for pts, fill, edge in shapes:
                    p.setBrush(fill if fill is not None else Qt.NoBrush)
                    p.setPen(QPen(edge, 0.8))
                    p.drawPolygon(QPolygonF([P(q) for q in pts]))
                p.setFont(small)
                p.setPen(QColor(90, 90, 90))
                p.drawText(QRectF(x0 + 4, y0 + 1, w_ - 8, 12), Qt.AlignLeft, title)
                p.setFont(bold)
                for letter, a, b, side in dims:
                    A, B = P(a), P(b)
                    sx, sy = side[0], -side[1]
                    L_ = math.hypot(sx, sy) or 1.0
                    sx, sy = sx / L_, sy / L_
                    off = 9.0
                    A2 = QPointF(A.x() + sx * off, A.y() + sy * off)
                    B2 = QPointF(B.x() + sx * off, B.y() + sy * off)
                    p.setPen(QPen(BLUE, 0.8))
                    p.drawLine(A, QPointF(A2.x() + sx * 3, A2.y() + sy * 3))
                    p.drawLine(B, QPointF(B2.x() + sx * 3, B2.y() + sy * 3))
                    p.drawLine(A2, B2)
                    dx, dy = B2.x() - A2.x(), B2.y() - A2.y()
                    Ld = math.hypot(dx, dy) or 1.0
                    tx, ty = (dx - dy) / Ld * 3, (dy + dx) / Ld * 3
                    for q in (A2, B2):
                        p.drawLine(QPointF(q.x() - tx, q.y() - ty), QPointF(q.x() + tx, q.y() + ty))
                    mx = (A2.x() + B2.x()) / 2 + sx * 10
                    my = (A2.y() + B2.y()) / 2 + sy * 10
                    r = 7.0
                    p.setBrush(QBrush(QColor(255, 255, 255)))
                    p.drawEllipse(QPointF(mx, my), r, r)
                    p.drawText(QRectF(mx - r, my - r, 2 * r, 2 * r), Qt.AlignCenter, letter)

            bl, bh, bd = max(10.0, v['brick_l']), max(5.0, v['brick_h']), max(1.0, v['brick_d'])
            J = max(0.2, v['joint'])
            Jb = 0.0 if v.get('no_bed') else J
            # K, L and M are always drawn: at their size, or at a sample size if they're off (0)
            bev = max(0.0, v.get('bevel', 0.0)) or 0.1 * min(bh, bd)
            cc = (max(0.0, v.get('cant_course', 0.0)) if v.get('cant_where', 'none') != 'none' else 0.0) \
                or 0.3 * min(bh, bd)
            cm = max(0.0, v.get('cant_corner', 0.0)) or 0.3 * bd
            off = [k for k, on in (('K', v.get('bevel', 0.0) > 0),
                                   ('L', v.get('cant_where', 'none') != 'none' and v.get('cant_course', 0.0) > 0),
                                   ('M', v.get('cant_corner', 0.0) > 0)) if not on]
            hw, hh = W / 2.0, (H - 4) / 2.0

            # 1. the chimney, from the front
            Bw, Tw, Ht = max(50.0, v['bottom']), max(10.0, v['top']), max(50.0, v['height'])
            rs = min(v['raise_'], Ht)
            re_ = Ht if v['lay_h'] <= 0 else min(Ht, rs + v['lay_h'])

            def wid(z):
                return Bw + (Tw - Bw) * z / Ht
            body = [(-Bw / 2, 0), (Bw / 2, 0), (Tw / 2, Ht), (-Tw / 2, Ht)]
            band = [(-wid(rs) / 2, rs), (wid(rs) / 2, rs), (wid(re_) / 2, re_), (-wid(re_) / 2, re_)]
            dims = [('A', (-Bw / 2, 0), (Bw / 2, 0), (0, -1)), ('B', (-Tw / 2, Ht), (Tw / 2, Ht), (0, 1)),
                    ('C', (Bw / 2, 0), (Bw / 2, Ht), (1, 0))]
            if rs > 0:
                dims.append(('D', (-Bw / 2, 0), (-Bw / 2, rs), (-1, 0)))
            if v['lay_h'] > 0:
                dims.append(('E', (-wid(rs) / 2, rs), (-wid(rs) / 2, re_), (-1, 0)) if rs <= 0 else
                            ('E', (-Bw / 2 - 0.0001, rs), (-Bw / 2 - 0.0001, re_), (-1, 0)))
            panel((0, 0, hw, hh), "Chimney", [(body, CORE, CE), (band, BR, BRE)], dims, pad=30)

            # 2. bricks from the front
            shapes = []
            x_off = [0.0, -(bl + J) / 2.0]
            for row in range(2):
                y0 = row * (bh + Jb)
                for k in range(-1, 3):
                    x0 = k * (bl + J) + x_off[row]
                    xa, xb = max(x0, -0.6 * bl), min(x0 + bl, 1.6 * bl + J)
                    if xb - xa < 5:
                        continue
                    shapes.append(([(xa, y0), (xb, y0), (xb, y0 + bh), (xa, y0 + bh)], BR, BRE))
                    if bev > 0:
                        i_ = min(bev, bh * 0.3)
                        shapes.append(([(xa + (i_ if xa == x0 else 0), y0 + i_), (xb - (i_ if xb == x0 + bl else 0), y0 + i_),
                                        (xb - (i_ if xb == x0 + bl else 0), y0 + bh - i_),
                                        (xa + (i_ if xa == x0 else 0), y0 + bh - i_)], None, BRE))
            mort = [(-0.6 * bl, -Jb), (1.6 * bl + J, -Jb), (1.6 * bl + J, 2 * bh + Jb), (-0.6 * bl, 2 * bh + Jb)]
            shapes.insert(0, (mort, CORE, CE))
            dims = [('F', (0, 0), (bl, 0), (0, -1)), ('G', (-0.6 * bl, 0), (-0.6 * bl, bh), (-1, 0)),
                    ('J', (bl, bh), (bl + J, bh), (0, 1))]
            if Jb > 0:
                dims.append(('J', (1.6 * bl + J, bh), (1.6 * bl + J, bh + Jb), (1, 0)))
            i_ = min(bev, bh * 0.3)
            xk = -0.3 * bl
            dims.append(('K', (xk, 2 * bh + Jb - i_), (xk, 2 * bh + Jb), (0, 1)))
            panel((hw, 0, hw, hh), "A brick, from the front", shapes, dims)

            # 3. a cut through three courses (the chimney on the left)
            shapes = [([(-0.35 * bd, -Jb), (0, -Jb), (0, 3 * bh + 2 * Jb), (-0.35 * bd, 3 * bh + 2 * Jb)], CORE, CE)]
            for row in range(3):
                y0 = row * (bh + Jb)
                top_c = cc if row == 2 else 0.0
                tc = min(max(top_c, bev), 0.45 * min(bh, bd))
                bc = min(bev, 0.45 * min(bh, bd))
                pts = [(0, y0), (bd - bc, y0), (bd, y0 + bc), (bd, y0 + bh - tc), (bd - tc, y0 + bh), (0, y0 + bh)]
                shapes.append((pts, BR, BRE))
            y2 = 2 * (bh + Jb)
            c_ = min(max(cc, bev), 0.45 * min(bh, bd))
            dims = [('H', (0, y2 + bh), (bd, y2 + bh), (0, 1)), ('L', (bd, y2 + bh - c_), (bd, y2 + bh), (1, 0))]
            panel((0, hh, hw, hh), "Cut through (top: cant course)", shapes, dims)

            # 4. a corner, from above: the chimney's corner at the origin, one brick running
            # on past the corner (covering the end of the brick on the other side)
            c_ = min(max(cm, bev), 0.45 * bd)
            L2 = 0.9 * bl
            shapes = [([(-1.4 * bl, -1.4 * bl), (0, -1.4 * bl), (0, 0), (-1.4 * bl, 0)], CORE, CE)]
            if v.get('corner', 'bonded') == 'squint':
                # a special corner brick: one leg along each face, round the corner in one piece
                la, lb = bl, bl / 2.0
                shapes.append(([(-la, 0), (0, 0), (0, -lb), (bd, -lb), (bd, bd - c_), (bd - c_, bd), (-la, bd)],
                               BR, BRE))
                shapes.append(([(-la - J - 0.6 * bl, 0), (-la - J, 0), (-la - J, bd), (-la - J - 0.6 * bl, bd)], BR, BRE))
                shapes.append(([(0, -lb - J), (bd, -lb - J), (bd, -lb - J - L2), (0, -lb - J - L2)], BR, BRE))
                dims = [('H', (0, -lb - J - L2), (bd, -lb - J - L2), (0, -1)), ('M', (bd - c_, bd), (bd, bd - c_), (1, 1))]
                title = "Corner from above: special brick"
            else:
                run = [(bd - bl, 0), (bd, 0), (bd, bd - c_), (bd - c_, bd), (bd - bl, bd)]
                shapes.append((run, BR, BRE))
                shapes.append(([(0, -J), (bd, -J), (bd, -J - L2), (0, -J - L2)], BR, BRE))
                dims = [('H', (0, -J - L2), (bd, -J - L2), (0, -1)), ('M', (bd - c_, bd), (bd, bd - c_), (1, 1))]
                title = "Corner, from above"
            panel((hw, hh, hw, hh), title, shapes, dims)
            if off:
                p.setFont(small)
                p.setPen(QColor(120, 120, 120))
                p.drawText(QRectF(4, H - 14, W - 8, 12), Qt.AlignRight,
                           "%s: off (0) - drawn at a sample size" % ", ".join(off))
            p.setPen(QPen(QColor(220, 220, 220), 1))
            p.drawLine(QPointF(hw, 4), QPointF(hw, H - 4))
            p.drawLine(QPointF(4, hh), QPointF(W - 4, hh))
        finally:
            p.end()




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
        self.cb_preset = QComboBox()
        _narrow(self.cb_preset, 16)
        self.cb_preset.setToolTip("Your saved setups. Pick one and the window is filled in. A 'Bricks only' "
                                  "preset changes just the Bricks tab. The one marked (default) is filled in "
                                  "each time 3D Wrap opens.")
        top.addRow("Preset", self.cb_preset)
        brow_p = QHBoxLayout()
        self.b_psave = QPushButton("Save")
        self.b_psave.setToolTip("Updates the preset you have open with what's in the window now (no typing).")
        self.b_psaveas = QPushButton("Save as...")
        self.b_psaveas.setToolTip("Saves a new preset under a name you type: everything in the window, or "
                                  "the Bricks tab only.")
        self.b_pdel = QPushButton("Delete")
        self.b_pdel.setToolTip("Deletes the preset you have open.")
        self.b_pdef = QPushButton("Set as default")
        self.b_pdef.setToolTip("3D Wrap opens with the preset you have open filled in. Click it on "
                               "'(no preset)' to go back to the built-in settings.")
        for b_ in (self.b_psave, self.b_psaveas, self.b_pdel, self.b_pdef):
            brow_p.addWidget(b_)
        top.addRow(brow_p)
        self.cb_source = QComboBox()
        self.cb_source.addItem("New bricks", 'bricks')
        self.cb_source.addItem("My own pattern", 'pattern')
        self.cb_source.setToolTip("New bricks: laid course by course - every course has a whole number of "
                                  "bricks, never longer than a standard one, stepped half a brick each course, "
                                  "corners bonded - like a real chimney. My own pattern: bend any flat group "
                                  "round the target, following its curve.")
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
        row = QHBoxLayout()
        self.views = QTabWidget()
        self.closeup = CloseupView()
        self.sizes = SizesView()
        self.views.addTab(self.closeup, "Close-up")
        self.views.addTab(self.sizes, "Sizes (A, B, C ...)")
        row.addWidget(self.views, 1)
        row.addWidget(tabs, 1)
        lay.addLayout(row)
        self.sp = {}

        def num(tab, key, label, lo, hi, dec, suf, tip=""):
            s = QDoubleSpinBox()
            s.setDecimals(dec)
            s.setRange(lo, hi)
            s.setSuffix(suf)
            s.setKeyboardTracking(False)
            s.setValue(float(cur.get(key, DEFAULTS[key])))
            lab = QLabel(("%s   %s" % (LETTERS[key], label)) if key in LETTERS else label)
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
        self.cb_fith = QCheckBox("Fit the courses to the height")
        self.cb_fith.setToolTip("New bricks: the bed joints (between courses) are evened out a little so a whole "
                                "number of courses finishes right at the top (or at 'Go up to'). The joints "
                                "between the bricks in a course stay as set. Not with 'No mortar between "
                                "courses' (there's no bed joint to adjust).")
        self.cb_fith.setChecked(bool(cur.get('fit_height', True)))
        pages["Chimney"].addRow(self.cb_fith)
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
        self.cb_level = QComboBox()
        for k, t_ in COURSE_LAY:
            self.cb_level.addItem(t_, k)
        self.cb_level.setCurrentIndex(0 if bool(cur.get('level', True)) else 1)
        self.cb_level.setToolTip("Level: every course is laid level, like a real chimney; on a taper each "
                                 "course is set in a little from the one below, so it steps in. Lean back: "
                                 "the bricks lie flat on the sloping face, leaning back onto the chimney, so a "
                                 "tapered one (round especially) has a smooth face with no steps.")
        _narrow(self.cb_level, 16)
        lab = QLabel("Courses")
        lab.setToolTip(self.cb_level.toolTip())
        pages["Bricks"].addRow(lab, self.cb_level)
        self.cb_nobed = QCheckBox("No mortar between courses")
        self.cb_nobed.setToolTip("The courses sit straight on each other (no bed joint), but the joints "
                                 "between the bricks in a course stay.")
        self.cb_nobed.setChecked(bool(cur.get('no_bed', False)))
        pages["Bricks"].addRow(self.cb_nobed)
        num("Bricks", 'bevel', "Bevel brick edges", 0.0, 50.0, 1, " mm",
            "A small slope on the front edges of every brick, so the joints show more clearly (good for "
            "printing). 0 = sharp edges.")
        num("Bricks", 'cant_corner', "Cant corners", 0.0, 500.0, 1, " mm",
            "Square and many-sided chimneys: the corner bricks are cant bricks, their outside corner cut "
            "back this much. 0 = square corners.")
        self.cb_corner = QComboBox()
        for k, t_ in CORNERS:
            self.cb_corner.addItem(t_, k)
        self.cb_corner.setToolTip("Square and many-sided chimneys. Bonded: one side's end brick runs on past "
                                  "the corner, turn and turn about. Special corner bricks: a dog-leg brick made "
                                  "to the corner's own angle (a squint brick), one leg along each face, mitred "
                                  "so it fits exactly even where a taper leans the faces - no bricks sticking out "
                                  "and no gaps. Its legs swap long and short each course, so the bond still steps.")
        _narrow(self.cb_corner, 16)
        lab = QLabel("Corners")
        lab.setToolTip(self.cb_corner.toolTip())
        pages["Bricks"].addRow(lab, self.cb_corner)
        self.cb_faces = QComboBox()
        for k, t_ in FACES:
            self.cb_faces.addItem(t_, k)
        self.cb_faces.setToolTip("A solid you've drawn that goes only part way round (a curved wall with two "
                                 "ends): which of its faces get bricks.")
        _narrow(self.cb_faces, 16)
        lab = QLabel("Curved wall faces")
        lab.setToolTip(self.cb_faces.toolTip())
        pages["Bricks"].addRow(lab, self.cb_faces)
        self.cb_ends = QComboBox()
        for k, t_ in WALL_ENDS:
            self.cb_ends.addItem(t_, k)
        self.cb_ends.setToolTip("How the courses finish at the two ends of a curved wall. Stopped: a neat end, "
                                "whole and half bricks in turn. Toothed: every other course stands out half a "
                                "brick, ready to build on. Return round the end: bricks also cover the end of "
                                "the wall, bonded with the faces.")
        _narrow(self.cb_ends, 16)
        lab = QLabel("Wall ends")
        lab.setToolTip(self.cb_ends.toolTip())
        pages["Bricks"].addRow(lab, self.cb_ends)
        self.cb_cant = QComboBox()
        for k, t_ in CANT_WHERE:
            self.cb_cant.addItem(t_, k)
        self.cb_cant.setToolTip("Cant courses: the top front edge of each brick in the course is sloped "
                                "back (cant bricks), as on a weathered top or a plinth.")
        _narrow(self.cb_cant, 14)
        lab = QLabel("Cant course")
        lab.setToolTip(self.cb_cant.toolTip())
        pages["Bricks"].addRow(lab, self.cb_cant)
        num("Bricks", 'cant_course', "Cant size", 0.0, 500.0, 1, " mm",
            "How far the cant course's top front edge is cut back (down the face and back across the top).")

        self.cb_fit = QComboBox()
        for k, t in FITS:
            self.cb_fit.addItem(t, k)
        self.cb_fit.setToolTip("Repeat round: copies of the pattern side by side all the way round, eased a "
                               "little so they close up - the bricks stay their real size. Once round: the "
                               "pattern's width is stretched to the girth. True width: one "
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
        for cb, key in ((self.cb_target, 'target'), (self.cb_fit, 'fit'), (self.cb_hfit, 'height_fit'),
                        (self.cb_cant, 'cant_where'), (self.cb_corner, 'corner'), (self.cb_faces, 'faces'),
                        (self.cb_ends, 'ends')):
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
            self.setMinimumWidth(700)
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
        self.cb_cant.currentIndexChanged.connect(self.changed)
        # the close-up and sizes follow every change (a moment after, so typing isn't slowed)
        from PySide6.QtCore import QTimer
        self._redraw = QTimer(self)
        self._redraw.setSingleShot(True)
        self._redraw.timeout.connect(self.redraw)
        for s_ in list(self.sp.values()) + [self.sp_hdr]:
            s_.valueChanged.connect(lambda *_: self._redraw.start(150))
        for cb_ in (self.cb_target, self.cb_source, self.cb_level, self.cb_cant, self.cb_corner, self.cb_faces,
                    self.cb_ends):
            cb_.currentIndexChanged.connect(lambda *_: self._redraw.start(150))
        for ck_ in (self.cb_nobed, self.cb_core, self.cb_fith):
            ck_.toggled.connect(lambda *_: self._redraw.start(150))
        self.cb_nobed.toggled.connect(self.changed)
        self.views.currentChanged.connect(lambda *_: self._redraw.start(0))
        self.fill_presets(cur.get('_preset'))
        self.cb_preset.activated.connect(self.preset_picked)
        self.b_psave.clicked.connect(self.preset_save)
        self.b_psaveas.clicked.connect(self.preset_save_as)
        self.b_pdel.clicked.connect(self.preset_delete)
        self.b_pdef.clicked.connect(self.preset_default)
        self.changed()
        self.redraw()
        last = WrapTool._last_target
        if last is not None and _in_scene(getattr(viewport, 'scene', None), last):
            self._set_target(last)
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
        for k in ('bevel', 'cant_corner'):
            self.sp[k].setEnabled(bricks)
        self.cb_nobed.setEnabled(bricks)
        self.cb_fith.setEnabled(bricks and not self.cb_nobed.isChecked())
        self.cb_cant.setEnabled(bricks)
        self.sp['cant_course'].setEnabled(bricks and self.cb_cant.currentData() != 'none')
        self.sp['cant_corner'].setEnabled(bricks and self.cb_target.currentData() != 'round')
        self.cb_corner.setEnabled(bricks and self.cb_target.currentData() != 'round')
        self.cb_faces.setEnabled(bricks and self.cb_target.currentData() == 'mesh')
        self.cb_ends.setEnabled(bricks and self.cb_target.currentData() == 'mesh')
        try:
            name = self.cb_preset.currentData()
            self.b_psave.setEnabled(bool(name))
            self.b_pdel.setEnabled(bool(name))
        except Exception:
            pass
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

    def redraw(self, *_):
        """Brings the close-up (or the sizes drawing, whichever is showing) up to date."""
        try:
            v = self.values()
            if self.views.currentIndex() == 0:
                arc = self.arc_target() if (v.get('target') == 'mesh' and v.get('source') == 'bricks') else None
                self.closeup.show_values(v, arc)
            else:
                self.sizes.show_values(v)
        except Exception as e:
            print("%s: preview (%s)" % (PLUGIN_NAME, e))

    # --- presets ---
    def fill_presets(self, pick=None):
        dflt = default_preset()
        self.cb_preset.blockSignals(True)
        self.cb_preset.clear()
        self.cb_preset.addItem("(no preset)", None)
        for name, d in load_presets():
            label = name + ("  [bricks only]" if d.get('_bricks_only') else "")
            if name == dflt:
                label += "  (default)"
            self.cb_preset.addItem(label, name)
        i = self.cb_preset.findData(pick) if pick else 0
        self.cb_preset.setCurrentIndex(max(0, i))
        self.cb_preset.blockSignals(False)

    def set_values(self, cur):
        for k, s in self.sp.items():
            if k in cur:
                try:
                    s.setValue(float(cur[k]))
                except Exception:
                    pass
        if 'header_every' in cur:
            self.sp_hdr.setValue(int(cur['header_every']))
        for cb, key in ((self.cb_target, 'target'), (self.cb_fit, 'fit'), (self.cb_hfit, 'height_fit'),
                        (self.cb_cant, 'cant_where'), (self.cb_corner, 'corner'), (self.cb_faces, 'faces'),
                        (self.cb_ends, 'ends'), (self.cb_source, 'source')):
            if key in cur:
                i = cb.findData(cur[key])
                if i >= 0:
                    cb.setCurrentIndex(i)
        if 'level' in cur:
            self.cb_level.setCurrentIndex(0 if cur['level'] else 1)
        for cb, key in ((self.cb_core, 'add_core'), (self.cb_flip, 'flip'), (self.cb_depth, 'scale_depth'),
                        (self.cb_nobed, 'no_bed'), (self.cb_fith, 'fit_height')):
            if key in cur:
                cb.setChecked(bool(cur[key]))
        self.changed()

    def _stored(self, bricks_only):
        v = self.values()
        v.pop('raise', None)
        if bricks_only:
            v = {k: v[k] for k in BRICK_KEYS if k in v}
            v['_bricks_only'] = True
        return v

    def preset_picked(self, *_):
        name = self.cb_preset.currentData()
        if name:
            self.set_values(preset_values(name))
        self.changed()

    def preset_save(self, *_):
        name = self.cb_preset.currentData()
        if not name:
            return self.preset_save_as()
        bricks_only = any(n == name and d.get('_bricks_only') for n, d in load_presets())
        save_preset(name, self._stored(bricks_only))
        self.lbl_report.setStyleSheet("color: #2e7d32;")
        self.lbl_report.setText("Saved the preset '%s'." % name)

    def preset_save_as(self, *_):
        name, ok = QInputDialog.getText(self, PLUGIN_NAME, "Name for this preset:")
        if not ok or not str(name).strip():
            return
        box = QMessageBox(self)
        box.setWindowTitle(PLUGIN_NAME)
        box.setText("Save everything in the window, or the Bricks tab only?\n\n"
                    "A 'Bricks only' preset changes just the bricks (size, mortar, cants...) and leaves "
                    "the chimney and pattern settings as they are.")
        b_all = box.addButton("Everything", QMessageBox.AcceptRole)
        b_br = box.addButton("Bricks only", QMessageBox.AcceptRole)
        box.addButton(QMessageBox.Cancel)
        box.exec()
        if box.clickedButton() not in (b_all, b_br):
            return
        safe = save_preset(str(name), self._stored(box.clickedButton() is b_br))
        self.fill_presets(safe)
        self.changed()
        self.lbl_report.setStyleSheet("color: #2e7d32;")
        self.lbl_report.setText("Saved the preset '%s'." % safe)

    def preset_delete(self, *_):
        name = self.cb_preset.currentData()
        if not name:
            return
        if QMessageBox.question(self, PLUGIN_NAME, "Delete the preset '%s'?" % name) != QMessageBox.Yes:
            return
        delete_preset(name)
        self.fill_presets()
        self.changed()

    def preset_default(self, *_):
        name = self.cb_preset.currentData()
        set_default_preset(name)
        self.fill_presets(name)
        self.changed()
        self.lbl_report.setStyleSheet("color: #2e7d32;")
        self.lbl_report.setText(("3D Wrap will open with '%s' filled in." % name) if name else
                                "3D Wrap will open with its built-in settings.")

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

    def _target_choices(self):
        # laying new bricks there is no pattern, so whatever is selected can be the target
        pat = self.pattern if self.cb_source.currentData() == 'pattern' else None
        return [g for g in self._selected() if g is not pat]

    def _set_target(self, g):
        self.target = g
        WrapTool._last_target = g
        self.lbl_tgt.setText("Target solid: " + group_label(g))

    def pick_target(self, *_):
        gs = self._target_choices()
        if not gs:
            QMessageBox.information(self, PLUGIN_NAME, "Select the solid to wrap round first"
                                    + (" (not the pattern)." if self.cb_source.currentData() == 'pattern' else "."))
            return
        self._set_target(gs[0])

    def arc_target(self):
        """The picked solid as a curved wall (worked out once, then kept), or None if it isn't one."""
        g = self.target
        if g is None:
            return None
        cache = getattr(self, '_arc_cache', None)
        if cache is not None and cache[0] is g:
            return cache[1]
        tg = None
        try:
            tf = group_faces(g)
            if is_open_wall(tf):
                tg = ArcTarget(tf)
        except Exception:
            tg = None
        self._arc_cache = (g, tg)
        return tg

    def need_target(self):
        """The solid to wrap round: the one picked (if it's still in the model), else the one
        selected now, else the one used last time. None (and a note) if there's none."""
        scene = getattr(self.viewport, 'scene', None)
        if self.target is not None and _in_scene(scene, self.target):
            return self.target
        gs = self._target_choices()
        if gs:
            self._set_target(gs[0])
            return self.target
        last = WrapTool._last_target
        if last is not None and _in_scene(scene, last):
            self._set_target(last)
            return self.target
        QMessageBox.information(self, PLUGIN_NAME, "Select the solid to wrap round, then click Wrap again "
                                                   "(or click 'Use as target').")
        return None

    def values(self):
        v = dict(target=self.cb_target.currentData(), fit=self.cb_fit.currentData(),
                 source=self.cb_source.currentData(), header_every=int(self.sp_hdr.value()),
                 height_fit=self.cb_hfit.currentData(), add_core=self.cb_core.isChecked(),
                 flip=self.cb_flip.isChecked(), scale_depth=self.cb_depth.isChecked(),
                 level=bool(self.cb_level.currentData()), no_bed=self.cb_nobed.isChecked(),
                 cant_where=self.cb_cant.currentData(), corner=self.cb_corner.currentData(),
                 faces=self.cb_faces.currentData(), ends=self.cb_ends.currentData(),
                 fit_height=self.cb_fith.isChecked())
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
    description = "Bends a flat pattern (bricks, boards...) round a chimney or any upright solid."
    _dialog = None
    _saved = None
    _last_target = None           # the solid wrapped round last, kept while it's in the model

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
        start = dict(DEFAULTS)
        dflt = default_preset()
        if dflt:
            start.update(preset_values(dflt))
            start['_preset'] = dflt
        start.update(WrapTool._saved or {})
        dlg = WrapDialog(viewport, self, start)
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
                if dlg.need_target() is None:
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
                if dlg.need_target() is None:
                    return
                tf = group_faces(dlg.target)
                name = "Brickwork - " + group_label(dlg.target)
                if is_open_wall(tf):
                    # a wall that goes only part way round: along it, end to end
                    target = dlg.arc_target() or ArcTarget(tf)
                    faces, info = lay_arc_bricks(target, v)
                    return self._bricks_done(dlg, v, name, faces, info, None)
                target = MeshTarget(tf, ignore=v['ignore'] * SCALE)
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
        core = target.solid_faces() if (v['target'] != 'mesh' and v['add_core']) else None
        return self._bricks_done(dlg, v, name, faces, info, core)

    def _bricks_done(self, dlg, v, name, faces, info, core):
        if not faces:
            QMessageBox.warning(dlg, PLUGIN_NAME, "No bricks fitted: is the target tall enough for one course?")
            return
        self._errors = (0, None)
        nf = self.add_to_scene(dlg.viewport, name, faces, core)
        if nf is None:
            return
        if 'span' in info:
            msg = ("Laid %d bricks in %d courses, %d faces, along a curved wall that goes %.0f degrees round "
                   "(radius about %.0f mm), %s, ends %s." % (
                       info['bricks'], info['courses'], nf, info['span'], info['radius'] / SCALE,
                       dict(FACES)[v.get('faces', 'outside')].lower() + (" face" if v.get('faces') != 'both' else " faces"),
                       dict(WALL_ENDS)[v.get('ends', 'stopped')].split(" (")[0].lower()))
        else:
            msg = "Laid %d bricks in %d courses, %d faces. Every course is a whole number of bricks, so there's " \
                  "no seam." % (info['bricks'], info['courses'], nf)
        if info.get('fit'):
            msg += " Bed joints %.1f mm, so the courses finish at the top." % (info.get('bed', 0.0) / SCALE)
        warn = bool(self._errors[0])
        if self._errors[0]:
            msg += "\n%d faces could not be made: %s" % self._errors
        if info.get('corners') and not v.get('level', True) and v.get('corner') == 'bonded':
            warn = True
            msg += ("\nTip: leaning back on a tapered chimney, bonded corners can't line up (the two faces "
                    "lean different ways), so the corner bricks step out. Choose Corners: Special corner "
                    "bricks for a neat corner.")
        dlg.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if warn else "#2e7d32"))
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
                    # a face it won't take whole (an L-shaped top of a corner brick, say): as triangles
                    done = False
                    if len(t) > 3:
                        try:
                            for tri in triangles(t):
                                mesh.add_face([vx(p) for p in tri])
                                stats['faces'] += 1
                            done = True
                        except Exception as e2:
                            e = e2
                    if not done:
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
