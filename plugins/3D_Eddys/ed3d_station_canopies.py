# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Station Canopies for IngeTrazo
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
3D Station Canopies - railway platform canopies with fancy valancing for IngeTrazo
Lean-to: select the station building's wall face and the canopy runs the length of it,
sloping down to the front, on a row of columns, with valancing along the front and ends.
Island / umbrella: select the platform's top face; one row of columns down the middle,
the roof falling both ways (or a butterfly roof falling to the middle), valancing both sides.
Ridge and furrow: select a wall face; glazed ridges running out from the wall, with a
boarded gable over the front of each.

Columns: cast iron (plinth, moulded base, shaft, necking, flared capital, abacus) with
pierced spandrel brackets, or square timber posts with knee braces.
Roof: plain (boarded / slated / felted) or glazed, with glazing bars and glass.
Valancing: dagger, rounded, fleur, saw-tooth or plain boards, with pierced holes - one
flat strip per side, so it prints lying down.

Every part is a closed solid, in its own group (columns, brackets, beams, roof, glass,
valance), so they can be printed separately. Sizes are real-world mm. Ctrl+Alt+C.
"""

import math
import os
import json
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QCheckBox,
                               QDoubleSpinBox, QPushButton, QLabel, QMessageBox, QTabWidget, QWidget)

PLUGIN_NAME = "3D Station Canopies"
VERSION = "1"
SCALE = 0.001
Z = (0.0, 0.0, 1.0)

# ---------------------------------------------------------------------------
# Geometry helpers (shared with Wood Planking and Chimneys)
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




# ---------------------------------------------------------------------------
# Solids: a list of faces, each (outer loop, [hole loops])
# ---------------------------------------------------------------------------
def solid_volume(faces):
    v = 0.0
    for outer, holes in faces:
        for loop in [outer] + list(holes):
            for j in range(1, len(loop) - 1):
                v += v_dot(loop[0], v_cross(loop[j], loop[j + 1]))
    return v / 6.0


def fixed(faces):
    """Turned outward if it came out inside out."""
    if solid_volume(faces) < 0:
        return [(list(reversed(o)), [list(reversed(h)) for h in hs]) for o, hs in faces]
    return faces


def box_solid(foot, z0, z1):
    """An upright prism: a convex plan outline (counter-clockwise) from z0 to z1."""
    foot = clean(foot)
    if not foot or z1 - z0 < 1e-9:
        return None
    n = len(foot)
    faces = [([(x, y, z1) for x, y in foot], []), ([(x, y, z0) for x, y in reversed(foot)], [])]
    for i in range(n):
        (ax, ay), (bx, by) = foot[i], foot[(i + 1) % n]
        faces.append(([(ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1)], []))
    return fixed(faces)


def lathe(profile, cx, cy, z0, nseg=24, rot=0.0):
    """Turn a closed profile [(r, z)] (r >= 0) round an upright axis. Flat rings come out as
    one face with a hole, flat discs as one face, so there are no stray edges."""
    angs = [rot + 2 * math.pi * k / nseg for k in range(nseg)]

    def P(r, z, a):
        return (cx + r * math.cos(a), cy + r * math.sin(a), z0 + z)
    faces = []
    m = len(profile)
    for i in range(m):
        (ra, za), (rb, zb) = profile[i], profile[(i + 1) % m]
        if abs(ra - rb) < 1e-12 and abs(za - zb) < 1e-12:
            continue
        if ra < 1e-12 and rb < 1e-12:
            continue                                   # along the axis: nothing
        if abs(za - zb) < 1e-12:
            # flat: wound as the strip of quads [a(t1), b(t1), b(t2), a(t2)] would be
            if rb > ra:
                outer = [P(rb, za, a) for a in angs]
                hole = [P(ra, za, a) for a in reversed(angs)] if ra > 1e-12 else None
            else:
                outer = [P(ra, za, a) for a in reversed(angs)]
                hole = [P(rb, za, a) for a in angs] if rb > 1e-12 else None
            faces.append((outer, [hole] if hole else []))
            continue
        for k in range(nseg):
            a1, a2 = angs[k], angs[(k + 1) % nseg]
            if ra < 1e-12:
                faces.append(([P(0, za, 0), P(rb, zb, a1), P(rb, zb, a2)], []))
            elif rb < 1e-12:
                faces.append(([P(ra, za, a1), P(0, zb, 0), P(ra, za, a2)], []))
            else:
                faces.append(([P(ra, za, a1), P(rb, zb, a1), P(rb, zb, a2), P(ra, za, a2)], []))
    return fixed(faces)





# ---------------------------------------------------------------------------
# Building blocks (local frame: x along the canopy, y out from the wall / across, z up; mm)
# ---------------------------------------------------------------------------
def box(x0, x1, y0, y1, z0, z1):
    if x1 - x0 < 1e-6 or y1 - y0 < 1e-6 or z1 - z0 < 1e-6:
        return None
    return box_solid([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1)


def plate(outline, holes, O, U, V, W, t0, t1):
    """A flat piece: a 2D outline (counter-clockwise, with holes) drawn in the plane through O
    spanned by U and V, standing from t0 to t1 along W. Any outline - it needn't be convex."""
    def P(u, v, w):
        return (O[0] + U[0] * u + V[0] * v + W[0] * w,
                O[1] + U[1] * u + V[1] * v + W[1] * w,
                O[2] + U[2] * u + V[2] * v + W[2] * w)
    if area2(outline) < 0:
        outline = outline[::-1]
    holes = [h if area2(h) < 0 else h[::-1] for h in holes]
    faces = [([P(u, v, t1) for u, v in outline], [[P(u, v, t1) for u, v in h] for h in holes]),
             ([P(u, v, t0) for u, v in reversed(outline)], [[P(u, v, t0) for u, v in reversed(h)] for h in holes])]
    for loop in [outline] + holes:
        n = len(loop)
        for i in range(n):
            (a, b), (c, d) = loop[i], loop[(i + 1) % n]
            faces.append(([P(a, b, t0), P(c, d, t0), P(c, d, t1), P(a, b, t1)], []))
    return fixed(faces)


def sloped_slab(x0, x1, y0, y1, zf, t):
    """A slab over the rectangle x0..x1, y0..y1 whose underside is the plane zf(x, y), t thick."""
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    bot = [(x, y, zf(x, y)) for x, y in pts]
    top = [(x, y, zf(x, y) + t) for x, y in pts]
    faces = [(top, []), (bot[::-1], [])]
    for i in range(4):
        j = (i + 1) % 4
        faces.append(([bot[i], bot[j], top[j], top[i]], []))
    return fixed(faces)


def hole_sides(v):
    """How many sides a pierced hole has: half the round-segments setting (at least 8)."""
    return max(8, int(round(v.get('segments', 24) / 2.0)))


def circle(cx, cy, r, n=14):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


# ---------------------------------------------------------------------------
# Valancing: the cut boards along the canopy's edge
# ---------------------------------------------------------------------------
VALANCES = [("dagger", "Dagger (pointed)"), ("round", "Rounded (scalloped)"), ("fleur", "Fleur (fancy)"),
            ("saw", "Saw-tooth"), ("plain", "Plain (square)")]


def board_bottom(pattern, b, h):
    """The bottom edge of one board, from its left edge to its right: [(u, v)] with v down
    from the top (negative). Plus where its hole goes, if it has one: (u, v, r) or None."""
    if pattern == 'dagger':
        return [(0.0, -0.72 * h), (b / 2, -h), (b, -0.72 * h)], (b / 2, -0.42 * h, b * 0.14)
    if pattern == 'round':
        r = b / 2
        c = -h + r
        pts = [(b / 2 - r * math.cos(math.pi * k / 10), c - r * math.sin(math.pi * k / 10)) for k in range(11)]
        return pts, (b / 2, -0.42 * h, b * 0.18)
    if pattern == 'fleur':
        return [(0.0, -0.58 * h), (0.14 * b, -0.6 * h), (0.2 * b, -0.72 * h), (0.36 * b, -0.7 * h),
                (0.5 * b, -h), (0.64 * b, -0.7 * h), (0.8 * b, -0.72 * h), (0.86 * b, -0.6 * h),
                (b, -0.58 * h)], (b / 2, -0.38 * h, b * 0.16)
    if pattern == 'saw':
        return [(0.0, -h), (b / 2, -0.8 * h), (b, -h)], None
    return [(0.0, -h), (b, -h)], None


def valance_outline(length, v):
    """The whole valance as one outline (top edge along v = 0) and its pierced holes."""
    bw = max(20.0, v['board_w'])
    h = max(50.0, v['val_h'])
    n = max(1, int(round(length / bw)))
    b = length / n
    bottom = []
    holes = []
    for k in range(n):
        pts, hole = board_bottom(v['valance'], b, h)
        for u, w in pts:
            q = (k * b + u, w)
            if not bottom or abs(bottom[-1][0] - q[0]) > 1e-6 or abs(bottom[-1][1] - q[1]) > 1e-6:
                bottom.append(q)
        if hole and v.get('val_holes', True):
            holes.append(circle(k * b + hole[0], hole[1], hole[2], hole_sides(v)))
    outline = bottom + [(length, 0.0), (0.0, 0.0)]
    return outline, holes, n


def valance_outline_raked(length, v, sl):
    """A valance whose top follows a slope (v = sl * u along it), for the open end of a lean-to.
    Each board hangs straight and keeps its true shape and round hole: it is just set up or down
    to the slope as a whole, so there's a small step between one board and the next."""
    bw = max(20.0, v['board_w'])
    h = max(50.0, v['val_h'])
    n = max(1, int(round(length / bw)))
    b = length / n
    bottom, holes = [], []
    for k in range(n):
        lift = sl * (k + 0.5) * b
        pts, hole = board_bottom(v['valance'], b, h)
        for u, w in pts:
            q = (k * b + u, w + lift)
            if not bottom or abs(bottom[-1][0] - q[0]) > 1e-6 or abs(bottom[-1][1] - q[1]) > 1e-6:
                bottom.append(q)
        if hole and v.get('val_holes', True):
            holes.append(circle(k * b + hole[0], hole[1] + lift, hole[2], hole_sides(v)))
    outline = bottom + [(length, sl * length), (0.0, 0.0)]
    return outline, holes, n


# ---------------------------------------------------------------------------
# Columns, posts and brackets
# ---------------------------------------------------------------------------
def column_shape(z0, z1, d):
    """A cast-iron column's outline from z0 (platform) to z1 (under the beam): its turned
    profile [(radius, z above the turning's foot)], the plinth and abacus heights, and rad(z) -
    how far the column's surface is from its centre at height z (the plinth and the square abacus
    measured across their flats)."""
    r = d / 2.0
    H = z1 - z0
    pl = 0.07 * H
    ab = 0.035 * H
    top_turn = z1 - ab
    span = top_turn - (z0 + pl)
    prof = [(0.0, 0.0), (1.12 * r, 0.0), (1.12 * r, 0.02 * H), (r, 0.05 * H), (0.88 * r, H * 0.8),
            (1.05 * r, H * 0.81), (1.05 * r, H * 0.83), (0.85 * r, H * 0.84), (1.0 * r, H * 0.88),
            (1.55 * r, span - 0.002), (0.0, span - 0.002)]
    # keep the turned part strictly between the plinth and the abacus (sunk a hair into each)
    prof = [(rr, min(zz, span)) for rr, zz in prof]
    base = z0 + pl - 0.5
    side = [(rr, base + zz) for rr, zz in prof[1:-1]]          # the outside, bottom to top

    def rad(z):
        if z >= top_turn - 0.5:
            return 1.7 * r
        if z <= z0 + pl:
            return 1.25 * r
        for (ra, za), (rb, zb) in zip(side, side[1:]):
            if za - 1e-9 <= z <= zb + 1e-9:
                return ra if zb - za < 1e-9 else ra + (rb - ra) * (z - za) / (zb - za)
        return r
    return dict(r=r, H=H, pl=pl, ab=ab, top_turn=top_turn, prof=prof, base=base, side=side, rad=rad)


def cast_column(x, y, z0, z1, d, nseg=24):
    """A cast-iron column from z0 (platform) to z1 (under the beam): plinth, moulded base, a
    slightly tapering shaft, necking, a flared capital and its square abacus."""
    c = column_shape(z0, z1, d)
    r = c['r']
    out = []
    b = box(x - 1.25 * r, x + 1.25 * r, y - 1.25 * r, y + 1.25 * r, z0, z0 + c['pl'])
    if b:
        out.append(b)
    out.append(lathe(c['prof'], x, y, c['base'], max(8, int(nseg))))
    a = box(x - 1.7 * r, x + 1.7 * r, y - 1.7 * r, y + 1.7 * r, c['top_turn'] - 0.5, z1)
    if a:
        out.append(a)
    return out


def spandrel(cx, cy, col, zt, S, dirx, diry, t, nseg=24, sl=0.0):
    """A cast-iron spandrel bracket growing out of a column (col: its column_shape) into the
    corner under the beam (underside zt): its inner edge follows the column's outline - shaft,
    necking, capital and abacus - a hair inside it, its top runs along the beam, and a concave
    curve sweeps from the beam down to the shaft, with a pierced roundel. S is how far it reaches
    out from the shaft, t how thick it is; it reaches out along (dirx, diry)."""
    n = max(6, int(round(nseg / 2.0)))
    r = col['r']
    ov = 1.0                                       # sunk 1 mm into the column, so they meet
    w = 0.05 * S                                   # the tips are left this wide (no knife edges)
    R = S - w
    # (u out from the column's centre, v down from the beam) - the curve, beam end to shaft end
    arc = [(r + S - R * math.sin(math.pi / 2 * k / n), -S + R * math.cos(math.pi / 2 * k / n)) for k in range(n + 1)]
    # the inner edge, up the column from the curve's foot to the beam
    zs = sorted({zt - S, zt} | {z for _rr, z in col['side'] if zt - S < z < zt} |
                {col['top_turn'] - 0.5})
    inner = []
    for z in zs:
        if z < zt - S - 1e-9 or z > zt + 1e-9:
            continue
        if abs(z - (col['top_turn'] - 0.5)) < 1e-9 and zt - S < z < zt:
            # the step out to the square abacus
            inner.append((col['rad'](z - 1e-3) - ov, z - zt))
            inner.append((1.7 * r - ov, z - zt))
            continue
        inner.append((col['rad'](z) - ov, z - zt))
    inner = [(u, v) for u, v in inner]
    outline = [(inner[-1][0], 0.0), (r + S, 0.0)] + arc + list(inner[:-1])
    outline = clean(outline) or []
    # every point of the curve must stay outside the column
    if not outline or any(u <= col['rad'](zt + v) for u, v in arc[1:-1]):
        return None
    # the pierced roundel: in the roomiest spot of the bracket (found by trying a grid of spots),
    # a little under half as big as the room there, so a solid ring is left all round it
    def seg_d(p, a_, b_):
        dx, dy = b_[0] - a_[0], b_[1] - a_[1]
        L2 = dx * dx + dy * dy
        t_ = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((p[0] - a_[0]) * dx + (p[1] - a_[1]) * dy) / L2))
        return math.hypot(p[0] - a_[0] - dx * t_, p[1] - a_[1] - dy * t_)

    def inside(p):
        c = False
        for k in range(len(outline)):
            (x1, y1), (x2, y2) = outline[k], outline[(k + 1) % len(outline)]
            if (y1 > p[1]) != (y2 > p[1]) and p[0] < x1 + (p[1] - y1) * (x2 - x1) / (y2 - y1):
                c = not c
        return c
    best = (0.0, None)
    us = [q[0] for q in outline]
    for gi in range(1, 24):
        for gj in range(1, 24):
            p = (min(us) + (max(us) - min(us)) * gi / 24.0, -S * gj / 24.0)
            if not inside(p):
                continue
            dmin = min(seg_d(p, outline[k], outline[(k + 1) % len(outline)]) for k in range(len(outline)))
            if dmin > best[0]:
                best = (dmin, p)
    holes = []
    hc = (r, 0.0)
    if best[1] is not None and best[0] * 0.45 >= 0.035 * S:
        hc, hr = best[1], best[0] * 0.45
        holes = [circle(hc[0], hc[1], hr, max(8, int(round(nseg / 2.0))))]
    # a sloping beam: every point goes up (or down) with the beam above it (the hole as a whole)
    outline = [(u, v + sl * (u - r)) for u, v in outline]
    holes = [[(u, v + sl * (hc[0] - r)) for u, v in h] for h in holes]
    O = (cx, cy, zt)
    U = (dirx, diry, 0.0)
    V = (0.0, 0.0, 1.0)
    W = (-diry, dirx, 0.0)
    return plate(outline, holes, O, U, V, W, -t / 2, t / 2)


def timber_post(x, y, z0, z1, w):
    out = []
    b = box(x - w / 2, x + w / 2, y - w / 2, y + w / 2, z0, z1)
    if b:
        out.append(b)
    return out


def knee_brace(cx, cy, cw, zt, S, dirx, diry, bw, t, sl=0.0):
    """A timber knee brace from the post (half-width cw) up to the beam (underside zt, sloping
    sl per mm along the brace's reach)."""
    a = S
    # a parallelogram strut: foot on the post, head under the beam
    pts = [(0.0, -a), (0.0, -a + bw * 1.414), (a - bw * 1.414, 0.0), (a, 0.0)]
    pts = [(u, v + sl * u) for u, v in pts]
    O = (cx + dirx * cw, cy + diry * cw, zt)
    U = (dirx, diry, 0.0)
    V = (0.0, 0.0, 1.0)
    W = (-diry, dirx, 0.0)
    return plate(pts, [], O, U, V, W, -t / 2, t / 2)


def column_set(v, x, y, z0, zt, along_dirs, out):
    """A column (or post) at (x, y) from the platform z0 up to the beam underside zt, with its
    brackets reaching out along each (dx, dy, slope) in along_dirs - the slope being how much the
    beam over that bracket rises per mm. Everything comes right up to the beam (a true joint)."""
    ztop = zt
    if v['col_style'] == 'timber':
        w = v['post_w']
        out['Columns'].append(timber_post(x, y, z0, ztop, w))
        if v.get('brackets', True):
            for dx, dy, sl in along_dirs:
                out['Brackets'].append(knee_brace(x, y, w / 2, ztop, v['bracket'], dx, dy, w * 0.6,
                                                  max(w * 0.6, v.get('bracket_t', 40.0)), sl))
    else:
        d = v['col_d']
        out['Columns'].append(cast_column(x, y, z0, ztop, d, v.get('segments', 24)))
        if v.get('brackets', True):
            col = column_shape(z0, ztop, d)
            for dx, dy, sl in along_dirs:
                b = spandrel(x, y, col, ztop, v['bracket'], dx, dy, max(5.0, v.get('bracket_t', 40.0)),
                             v.get('segments', 24), sl)
                if b:
                    out['Brackets'].append(b)


def beam_x(x0, x1, y0, y1, zbot, ztop):
    """A beam running along x from x0 to x1, between y0 and y1: flat underneath at zbot, its top
    cut to fit what's on it - ztop(x, y), the roof's underside - so they meet with no gap. A roof
    with a ridge (or a butterfly valley) at y = 0 over the beam gives its top the same ridge."""
    ys = [y0, y1]
    if y0 < 0.0 < y1:
        mid = ztop(0.0, 0.0)
        if abs(mid - (ztop(0.0, y0) + (ztop(0.0, y1) - ztop(0.0, y0)) * (-y0) / (y1 - y0))) > 1e-6:
            ys = [y0, 0.0, y1]
    sec = [(y0, zbot), (y1, zbot)] + [(y, ztop(0.0, y)) for y in reversed(ys)]
    sec = clean(sec)
    if not sec:
        return None
    return plate(sec, [], (x0, 0.0, 0.0), (0, 1, 0), (0, 0, 1), (1, 0, 0), 0.0, x1 - x0)


def cross_beam(x, bw, y0, y1, zf, depth):
    """A beam across the canopy (along y) at x, bw wide, depth deep, its top following the roof's
    underside, so they meet with no gap."""
    return sloped_slab(x - bw / 2, x + bw / 2, min(y0, y1), max(y0, y1), lambda x_, y_: zf(x_, y_) - depth,
                       depth)


def flashing_section(zr, v):
    """The cross-section of a wall flashing, as (y, z): an L of lead, its upstand against the wall
    (at y = 0) and its apron lying down the roof, whose top is zr(y). Lying right on the roof."""
    ft = max(1.0, v.get('flash_t', 32.0))
    up = max(ft * 2, v.get('flash_up', 150.0))
    cw = max(ft * 2, v.get('flash_cover', 150.0))
    g = 0.0

    def a(y):
        return zr(y) + g
    top = a(0.0) + up
    return [(0.0, a(0.0)), (cw, a(cw)), (cw, a(cw) + ft), (ft, a(ft) + ft), (ft, top), (0.0, top)]


def wall_flashing(L, zf, t, v):
    """The lead flashing where a lean-to roof meets the wall, L long."""
    sec = flashing_section(lambda y: zf(0.0, y) + t, v)
    return plate(sec, [], (0.0, 0.0, 0.0), (0, 1, 0), (0, 0, 1), (1, 0, 0), 0.0, L)


# ---------------------------------------------------------------------------
# Roofs
# ---------------------------------------------------------------------------
def roof_mono(x0, x1, y0, y1, zf, v, out, bars_along='y'):
    """A roof slab over x0..x1, y0..y1 with underside zf(x, y): plain, or glazed (glazing bars
    running down the slope, with glass between)."""
    t = max(5.0, v['roof_t'])
    if v['roof'] == 'glazed':
        bw = max(10.0, v['bar_w'])
        sp = max(bw * 3, v['bar_sp'])
        gt = max(2.0, min(t * 0.3, 12.0))
        if bars_along == 'y':
            L = x1 - x0
            n = max(1, int(round(L / sp)))
            step = L / n
            xs = [x0 + step * k for k in range(n + 1)]
            for k, xb in enumerate(xs):
                a, b = max(x0, xb - bw / 2), min(x1, xb + bw / 2)
                s = sloped_slab(a, b, y0, y1, zf, t)
                if s:
                    out['Roof'].append(s)
                if k < n:
                    ga, gb = xb + bw / 2, xs[k + 1] - bw / 2
                    if gb > ga:
                        out['Glass'].append(sloped_slab(ga, gb, y0, y1, lambda x, y: zf(x, y) + t * 0.5, gt))
        else:
            L = y1 - y0
            n = max(1, int(round(L / sp)))
            step = L / n
            ys = [y0 + step * k for k in range(n + 1)]
            for k, yb in enumerate(ys):
                a, b = max(y0, yb - bw / 2), min(y1, yb + bw / 2)
                s = sloped_slab(x0, x1, a, b, zf, t)
                if s:
                    out['Roof'].append(s)
                if k < n:
                    ga, gb = yb + bw / 2, ys[k + 1] - bw / 2
                    if gb > ga:
                        out['Glass'].append(sloped_slab(x0, x1, ga, gb, lambda x, y: zf(x, y) + t * 0.5, gt))
    else:
        s = sloped_slab(x0, x1, y0, y1, zf, t)
        if s:
            out['Roof'].append(s)
        if v['roof'] == 'lead':
            # lead sheet with wood-cored rolls running down the slope, a bay apart
            rr = max(5.0, v.get('roll_d', 50.0)) / 2.0
            sp = max(4 * rr, v.get('roll_sp', 600.0))
            a0, a1 = (x0, x1) if bars_along == 'y' else (y0, y1)
            n = int(round((a1 - a0) / sp))
            for k in range(1, max(1, n)):
                c = a0 + (a1 - a0) * k / n
                r_ = lead_roll(c, (y0, y1) if bars_along == 'y' else (x0, x1), bars_along, zf, t, rr,
                               v.get('segments', 24))
                if r_:
                    out['Roof'].append(r_)


def lead_roll(c, span, along, zf, t, rr, nseg=24):
    """A lead roll running down the slope (along y at x = c, or along x at y = c) over the
    span: a round-topped roll rr across its half-width, standing on the lead (sunk 0.5 mm into
    it, so they join), following the roof's slope."""
    n = max(4, int(round(nseg / 4.0)))
    sec = [(-rr, -0.5)] + [(-rr * math.cos(math.pi * k / n), 0.6 * rr + rr * math.sin(math.pi * k / n))
                           for k in range(n + 1)] + [(rr, -0.5)]
    sec = [(u, w) for i_, (u, w) in enumerate(sec) if i_ == 0 or (u, w) != sec[i_ - 1]]

    def P(u, w, s_):
        if along == 'y':
            x, y = c + u, s_
        else:
            x, y = s_, c + u
        return (x, y, zf(x, y) + t + w)
    a, b = span
    m = len(sec)
    faces = [([P(u, w, a) for u, w in sec], []), ([P(u, w, b) for u, w in reversed(sec)], [])]
    for i_ in range(m):
        (u1, w1), (u2, w2) = sec[i_], sec[(i_ + 1) % m]
        faces.append(([P(u2, w2, a), P(u1, w1, a), P(u1, w1, b), P(u2, w2, b)], []))
    return fixed(faces)


# ---------------------------------------------------------------------------
# The canopies
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# A bell-cast roof: a hipped roof whose four faces sweep out flat at the eaves and rise steep
# to a flat top (a kiosk, bay window, porch or cupola roof), lead-covered with rolls
# ---------------------------------------------------------------------------
def bell_rings(W, D, Wt, Dt, H, sweep, n):
    """The roof as a stack of level rectangles: [(half width, half depth, height)] from the eaves
    (t = 0) to the top (t = 1). sweep 0 = straight hips; more sweeps the eaves out flatter."""
    k = 1.0 + 2.5 * max(0.0, min(1.0, sweep))
    out = []
    for i in range(n + 1):
        t = i / float(n)
        # the height rises slowly at the eaves and fast at the top; the inset goes evenly
        out.append((W / 2.0 - (W - Wt) / 2.0 * t, D / 2.0 - (D - Dt) / 2.0 * t, H * (t ** k)))
    return out


def ring_solid(rings, cx, cy, z0):
    """A closed solid through a stack of level rectangles [(hx, hy, z)], bottom to top."""
    def R(hx, hy, z):
        return [(cx - hx, cy - hy, z0 + z), (cx + hx, cy - hy, z0 + z), (cx + hx, cy + hy, z0 + z),
                (cx - hx, cy + hy, z0 + z)]
    faces = [(list(reversed(R(*rings[0]))), []), (R(*rings[-1]), [])]
    for a, b in zip(rings, rings[1:]):
        ra, rb = R(*a), R(*b)
        for i in range(4):
            j = (i + 1) % 4
            faces.append(([ra[i], ra[j], rb[j], rb[i]], []))
    return fixed(faces)


def swept_roll(path, outward, rr, nseg=24):
    """A round-topped roll (rr across its half-width) swept along path, a list of points on
    the roof, standing out along outward(i) (the roof's outward direction there). Sunk 0.5 mm
    into the roof so they join. Made of triangles (the path curves)."""
    n = max(4, int(round(nseg / 4.0)))
    prof = [(-rr, -0.5)] + [(-rr * math.cos(math.pi * k / n), 0.6 * rr + rr * math.sin(math.pi * k / n))
                            for k in range(n + 1)] + [(rr, -0.5)]
    prof = [q for i, q in enumerate(prof) if i == 0 or q != prof[i - 1]]
    secs = []
    m = len(path)
    for i, P in enumerate(path):
        T = v_norm(v_sub(path[min(m - 1, i + 1)], path[max(0, i - 1)]))
        O = outward(i)
        E = v_norm(v_cross(T, O))
        N = v_norm(v_cross(E, T))
        if v_dot(N, O) < 0:
            N = v_mul(N, -1.0)
        secs.append([v_add(P, v_add(v_mul(E, u), v_mul(N, w))) for u, w in prof])
    faces = [(list(secs[0]), []), (list(reversed(secs[-1])), [])]
    q = len(prof)
    for a, b in zip(secs, secs[1:]):
        for j in range(q):
            k = (j + 1) % q
            faces.append(([a[k], a[j], b[j]], []))
            faces.append(([a[k], b[j], b[k]], []))
    return fixed(faces)


def build_bell(v, cx, cy, out):
    """A bell-cast roof centred on (cx, cy), its eaves W x D. On the platform (z = 0): either
    standing on four columns at the corners (eaves at the centre height), or sitting straight on
    what's under it. Returns info."""
    W = max(500.0, v['bell_w'])
    D = max(500.0, v['bell_d'])
    H = max(100.0, v['bell_h'])
    Wt = max(50.0, min(W * 0.9, v['bell_tw']))
    Dt = max(50.0, min(D * 0.9, v['bell_td']))
    t = max(5.0, v['roof_t'])
    nseg = int(v.get('segments', 24))
    n = max(8, nseg)
    fh = max(0.0, v['bell_fascia'])
    on_cols = bool(v.get('bell_cols'))
    # where the eaves are: on columns, at the centre height; otherwise straight on the face
    z_e = (v['h_centre'] if on_cols else 0.0) + fh + t
    rings = [(W / 2.0, D / 2.0, -t)] + bell_rings(W, D, Wt, Dt, H, v['bell_sweep'] / 100.0, n)
    out['Roof'].append(ring_solid(rings, cx, cy, z_e))
    # the cap on the flat top
    ch = max(0.0, v['bell_cap'])
    if ch > 0:
        lip = min(Wt, Dt) * 0.08
        out['Roof'].append(box(cx - Wt / 2 - lip, cx + Wt / 2 + lip, cy - Dt / 2 - lip, cy + Dt / 2 + lip,
                               z_e + H - 0.5, z_e + H + ch))
    rolls = 0
    if v['roof'] == 'lead':
        rr = max(5.0, v.get('roll_d', 50.0)) / 2.0
        sp = max(4 * rr, v.get('roll_sp', 600.0))
        rg = rings[1:]

        def pt(side, f, r_):
            hx, hy, z = r_
            if side == 0:
                return (cx + f * hx, cy - hy, z_e + z)
            if side == 1:
                return (cx + hx, cy + f * hy, z_e + z)
            if side == 2:
                return (cx - f * hx, cy + hy, z_e + z)
            return (cx - hx, cy - f * hy, z_e + z)
        normals = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        for side in range(4):
            length = W if side % 2 == 0 else D
            nr = int(round(length / sp))
            nx_, ny_ = normals[side]

            def face_out(i, side=side, nx_=nx_, ny_=ny_):
                # square to the roof face there: outward and up by the slope
                a, b = rg[max(0, i - 1)], rg[min(len(rg) - 1, i + 1)]
                dh = (abs(a[0] - b[0]) if side % 2 else abs(a[1] - b[1])) or 1e-9
                dz = abs(b[2] - a[2])
                return v_norm((nx_ * dz, ny_ * dz, dh))
            for j in range(1, max(1, nr)):
                f = -1.0 + 2.0 * j / nr
                path = [pt(side, f, r_) for r_ in rg]
                out['Roof'].append(swept_roll(path, face_out, rr, nseg))
                rolls += 1
        # and one up each hip
        for sx, sy in ((1, -1), (1, 1), (-1, 1), (-1, -1)):
            path = [(cx + sx * r_[0], cy + sy * r_[1], z_e + r_[2]) for r_ in rg]

            def hip_out(i, sx=sx, sy=sy):
                a, b = rg[max(0, i - 1)], rg[min(len(rg) - 1, i + 1)]
                dh = math.hypot(a[0] - b[0], a[1] - b[1]) or 1e-9
                dz = abs(b[2] - a[2])
                return v_norm((sx * 0.7071 * dz, sy * 0.7071 * dz, dh))
            out['Roof'].append(swept_roll(path, hip_out, rr * 1.15, nseg))
            rolls += 1
    # the fascia (and a moulded step below it) round the eaves
    over = max(0.0, v['bell_over'])
    fo_w, fo_d = W - 2 * over, D - 2 * over
    ft_ = max(30.0, v.get('beam_w', 120.0))
    if fh > 0 and fo_w > 2 * ft_ and fo_d > 2 * ft_:
        def ring(hw, hd, th, z0_, z1_):
            outl = [(cx - hw, cy - hd), (cx + hw, cy - hd), (cx + hw, cy + hd), (cx - hw, cy + hd)]
            hole = [(cx - hw + th, cy - hd + th), (cx - hw + th, cy + hd - th), (cx + hw - th, cy + hd - th),
                    (cx + hw - th, cy - hd + th)]
            return plate(outl, [hole], (0.0, 0.0, z0_), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.0, z1_ - z0_)
        zf0 = z_e - t - fh
        out['Beams'].append(ring(fo_w / 2, fo_d / 2, ft_, zf0 + fh * 0.35, z_e - t))
        out['Beams'].append(ring(fo_w / 2 - ft_ * 0.25, fo_d / 2 - ft_ * 0.25, ft_ * 0.75, zf0, zf0 + fh * 0.35))
    # valancing round the eaves, if wanted
    boards = 0
    if v.get('bell_val'):
        vt = max(5.0, v['val_t'])
        ztop = z_e - t
        for (x0, y0, U, Wd, L_) in (((cx - W / 2 - vt), cy - D / 2, (1, 0, 0), (0, -1, 0), W + 2 * vt),
                                    ((cx + W / 2 + vt), cy + D / 2, (-1, 0, 0), (0, 1, 0), W + 2 * vt),
                                    (cx + W / 2, cy - D / 2, (0, 1, 0), (1, 0, 0), D),
                                    (cx - W / 2, cy + D / 2, (0, -1, 0), (-1, 0, 0), D)):
            o2, h2, nb = valance_outline(L_, v)
            out['Valance'].append(plate(o2, h2, (x0, y0, ztop), U, (0, 0, 1), Wd, 0.0, vt))
            boards += nb
    # on columns: one at each corner, under the fascia, with brackets along its sides
    ncol = 0
    if on_cols:
        zt = z_e - t - fh                              # the fascia's underside
        c_in = ft_ / 2.0
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            x_ = cx + sx * (fo_w / 2 - c_in)
            y_ = cy + sy * (fo_d / 2 - c_in)
            column_set(v, x_, y_, 0.0, zt, [(-sx, 0, 0.0), (0, -sy, 0.0)], out)
            ncol += 1
    return dict(columns=ncol, boards=boards, depth=D, rolls=rolls, width=W)


KINDS = [("lean", "Lean-to (off a wall)"), ("island", "Island / umbrella"), ("ridge", "Ridge and furrow"),
         ("bell", "Bell-cast roof (kiosk, bay, porch)")]


def build_canopy(L, v):
    """Every part of a canopy L long (local mm). Returns ({group: [item]}, info), an item being a list of solids."""
    out = {'Columns': [], 'Brackets': [], 'Beams': [], 'Roof': [], 'Glass': [], 'Valance': [], 'Flashing': []}
    kind = v['kind']
    t = max(5.0, v['roof_t'])
    bd = max(50.0, v['beam_d'])
    bwid = max(30.0, v['beam_w'])
    vt = max(5.0, v['val_t'])
    vh = max(50.0, v['val_h'])
    bay = max(500.0, v['bay'])
    end_in = max(0.0, v['end_in'])
    n_b = max(1, int(math.ceil((L - 2 * end_in) / bay - 1e-9)))
    xs = [end_in + (L - 2 * end_in) * k / n_b for k in range(n_b + 1)]
    boards = 0
    # a bracket isn't put where it would stick out past the end of the canopy
    reach = max(0.0, v['bracket']) + (v['post_w'] if v['col_style'] == 'timber' else v['col_d']) / 2.0
    if kind in ('lean', 'ridge'):
        D = max(500.0, v['depth'])
        Hf, Hb = v['h_front'], max(v['h_front'], v['h_back'])
        if kind == 'ridge':
            Hb = Hf

        def zf(x, y):                                  # the roof's underside
            return Hb + (Hf - Hb) * y / D
        yc = D - max(0.0, v['col_set'])
        zt = zf(0, yc) - bd                            # the beam's underside over the columns
        # the beam along the columns, a fascia along the front, a plate on the wall (their tops
        # just under the roof all the way across)
        out['Beams'].append(beam_x(0.0, L, yc - bwid / 2, yc + bwid / 2, zt, zf))
        out['Beams'].append(beam_x(0.0, L, D - bwid, D, zf(0, D) - bd * 0.6, zf))
        out['Beams'].append(beam_x(0.0, L, 0.0, bwid * 0.8, zf(0, 0) - bd * 0.6, zf))
        level = abs(Hf - Hb) < 1e-6                    # a flat roof (ridge and furrow)
        for x in xs:
            dirs = [(1, 0, 0.0), (-1, 0, 0.0)]
            if level:
                # a cross beam at each column, from the wall to the front
                out['Beams'].append(cross_beam(x, bwid, 0.0, D, zf, bd))
                if D - yc >= reach:
                    dirs.append((0, 1, 0.0))
                if yc >= reach + 0.5:
                    dirs.append((0, -1, 0.0))
            else:
                # a sloping roof is framed: a rafter under it from the wall to the front, and a
                # level tie beam from the top of the column straight back to the wall, at right
                # angles to it. The brackets go only under the level beams.
                rd = 0.45 * bd
                out['Beams'].append(cross_beam(x, bwid, 0.0, D, zf, rd))
                tie_top = zf(0, yc + bwid / 2) - rd     # meets the rafter's underside at the column
                out['Beams'].append(box(x - bwid / 2, x + bwid / 2, 0.0, yc + bwid / 2, zt, tie_top))
                # an upright against the wall, from the tie up to the rafter, closing the triangle
                # (the frame stands like an A against the wall)
                y0_, y1_ = 0.0, bwid
                if min(zf(0, y0_), zf(0, y1_)) - rd - tie_top > 0.3 * bwid:
                    # standing on the tie, its top cut to the rafter's slope
                    out['Beams'].append(beam_x(x - bwid / 2, x + bwid / 2, y0_, y1_, tie_top,
                                               lambda x_, y_: zf(x_, y_) - rd))
                if yc >= reach + 0.5:
                    dirs.append((0, -1, 0.0))          # back to the wall, under the tie
            dirs = [d for d in dirs if not (d[0] == -1 and x - reach < -1.0) and not (d[0] == 1 and x + reach > L + 1.0)]
            column_set(v, x, yc, 0.0, zt, dirs, out)
        if kind == 'lean':
            roof_mono(0.0, L, 0.0, D, zf, v, out, 'y')
            z_front_top = zf(0, D) + t
            if v.get('flash'):
                out['Flashing'].append(wall_flashing(L, zf, t, v))
        else:
            # ridge and furrow: glazed ridges running out from the wall, gable ends at the front
            rw = max(500.0, v['rf_w'])
            n_r = max(1, int(round(L / rw)))
            rw = L / n_r
            rise = rw / 2 * math.tan(math.radians(max(5.0, min(60.0, v['rf_pitch']))))
            for k in range(n_r):
                xa, xm, xb = rw * k, rw * (k + 0.5), rw * (k + 1)

                def zl(x, y, xa=xa, xm=xm):
                    return Hf + rise * (x - xa) / (xm - xa)

                def zr(x, y, xm=xm, xb=xb):
                    return Hf + rise * (xb - x) / (xb - xm)
                # each slope's glazing bars run down it (across x), spaced along y
                roof_mono(xa, xm, 0.0, D, zl, v, out, 'x')
                roof_mono(xm, xb, 0.0, D, zr, v, out, 'x')
                # ridge roll and furrow gutter (they sit over the slab edges)
                out['Beams'].append(box(xm - bwid * 0.4, xm + bwid * 0.4, 0.0, D, Hf + rise - t * 0.3,
                                        Hf + rise + t * 1.2))
                # the gable end over the front: a boarded triangle
                tri = [(xa, 0.0), (xb, 0.0), (xm, rise)]
                out['Beams'].append(plate(tri, [], (0.0, D, Hf), (1, 0, 0), (0, 0, 1), (0, -1, 0), 0.0, vt))
            for k in range(n_r + 1):
                x = rw * k
                out['Beams'].append(box(max(0.0, x - bwid / 2), min(L, x + bwid / 2), 0.0, D,
                                        Hf - bd * 0.4, Hf + t * 0.6))
            z_front_top = Hf
        # valancing along the front, hanging from the fascia. With end valances it runs on past
        # each end to cover their ends.
        ends = v.get('val_ends', True) and kind == 'lean'
        ext = vt if ends else 0.0
        outline, holes, nb = valance_outline(L + 2 * ext, v)
        out['Valance'].append(plate(outline, holes, (-ext, D, z_front_top), (1, 0, 0), (0, 0, 1),
                                    (0, 1, 0), 0.0, vt))
        boards += nb
        # and down the open ends, under the roof's edge, from the wall to the front
        if ends:
            sl = (Hf - Hb) / D
            for xe, sgn in ((0.0, -1.0), (L, 1.0)):
                o2, h2, nb2 = valance_outline_raked(D, v, sl)
                out['Valance'].append(plate(o2, h2, (xe, 0.0, Hb + t), (0, 1, 0), (0, 0, 1),
                                            (sgn, 0, 0), 0.0, vt))
                boards += nb2
        info = dict(columns=len(xs), boards=boards, depth=D)
    elif kind == 'bell':
        info = build_bell(v, L / 2.0, 0.0, out)
    else:
        # island: one row of columns down the middle, the roof both ways, valancing both sides
        Wd = max(1000.0, v['width'])
        Hc = v['h_centre']
        pitch = math.radians(v['island_pitch'])
        half = Wd / 2
        butterfly = v.get('island_roof', 'ridge') == 'butterfly'

        def zf(x, y):
            d = abs(y)
            return Hc - d * math.tan(pitch) if not butterfly else Hc - (half - d) * math.tan(pitch)
        z_mid = zf(0, 0)
        zt = z_mid - bd if not butterfly else Hc - half * math.tan(pitch) - bd
        out['Beams'].append(beam_x(0.0, L, -bwid / 2, bwid / 2, zt, zf))
        for sgn in (-1.0, 1.0):
            yy = sgn * half
            y0_, y1_ = min(yy, yy - sgn * bwid), max(yy, yy - sgn * bwid)
            out['Beams'].append(beam_x(0.0, L, y0_, y1_, zf(0, yy) - bd * 0.6, zf))
        sl = (-1.0 if not butterfly else 1.0) * math.tan(pitch)     # the roof's rise per mm outwards
        for x in xs:
            # a cross beam each way from the column out to the eaves, under the roof
            out['Beams'].append(cross_beam(x, bwid, -half, 0.0, zf, bd))
            out['Beams'].append(cross_beam(x, bwid, 0.0, half, zf, bd))
            dirs = [(1, 0, 0.0), (-1, 0, 0.0)]
            if half >= reach and abs(sl) < 1e-9:
                dirs += [(0, 1, 0.0), (0, -1, 0.0)]    # only under level beams
            dirs = [d for d in dirs if not (d[0] == -1 and x - reach < -1.0) and not (d[0] == 1 and x + reach > L + 1.0)]
            column_set(v, x, 0.0, 0.0, zt, dirs, out)
        if butterfly:
            roof_mono(0.0, L, -half, 0.0, zf, v, out, 'y')
            roof_mono(0.0, L, 0.0, half, zf, v, out, 'y')
        else:
            roof_mono(0.0, L, -half, 0.0, zf, v, out, 'y')
            roof_mono(0.0, L, 0.0, half, zf, v, out, 'y')
            out['Beams'].append(box(0.0, L, -bwid * 0.4, bwid * 0.4, z_mid - 0.5, z_mid + t * 1.3))
        for sgn in (-1.0, 1.0):
            outline, holes, nb = valance_outline(L, v)
            yy = sgn * half
            out['Valance'].append(plate(outline, holes, (0.0, yy, zf(0, half) + t), (1, 0, 0), (0, 0, 1),
                                        (0, sgn, 0), 0.0, vt))
            boards += nb
        info = dict(columns=len(xs), boards=boards, depth=Wd)
    # items: each column (with its base and cap), bracket, beam and valance strip is one item,
    # to be its own group; the roof (with any glazing bars) and the glass are one item each
    items = {}
    for k, lst in out.items():
        if k == 'Columns':
            its = [[s_ for s_ in it if s_] for it in lst]
        elif k in ('Roof', 'Glass', 'Flashing'):
            its = [[s_ for s_ in lst if s_]]
        else:
            its = [[s_] for s_ in lst if s_]
        items[k] = [it for it in its if it]
    return items, info


# ---------------------------------------------------------------------------
# Settings and presets
# ---------------------------------------------------------------------------
COL_STYLES = [("castiron", "Cast iron + spandrels"), ("timber", "Timber posts + knee braces")]
ROOFS = [("plain", "Plain (slate / boards)"), ("glazed", "Glazed (bars and glass)"), ("lead", "Lead (with rolls)")]
ISLAND_ROOFS = [("ridge", "Ridged (falls both ways)"), ("butterfly", "Butterfly (falls to the middle)")]

DEFAULTS = dict(kind='lean', length=0.0, depth=3000.0, width=6000.0, h_back=4300.0, h_front=3400.0,
                h_centre=4500.0, island_pitch=8.0, island_roof='ridge', fit_width=False, edge_back=600.0,
                bay=3000.0, end_in=300.0, bracket_t=40.0, segments=24.0, col_set=450.0, z_off=0.0, wall_gap=1.0, flip=False, fit_wall=True,
                col_style='castiron', col_d=150.0, post_w=150.0, brackets=True, bracket=600.0,
                beam_d=250.0, beam_w=120.0,
                roof='plain', roof_t=60.0, bar_w=50.0, bar_sp=600.0, rf_w=3000.0, rf_pitch=26.0,
                valance='dagger', board_w=150.0, val_h=450.0, val_t=25.0, val_holes=True, val_ends=True,
                flash=True, roll_sp=600.0, roll_d=50.0,
                bell_w=3000.0, bell_d=3000.0, bell_over=300.0, bell_h=1500.0, bell_tw=500.0, bell_td=500.0,
                bell_sweep=60.0, bell_cap=120.0, bell_fascia=300.0, bell_fit=True, bell_cols=False, bell_val=False, flash_t=32.0, flash_up=150.0, flash_cover=150.0)

PRESETS = [
    ("GWR lean-to, dagger boards", dict(kind='lean', depth=3000.0, h_back=4300.0, h_front=3400.0, bay=3000.0,
                                       col_style='castiron', roof='plain', valance='dagger', board_w=150.0,
                                       val_h=450.0)),
    ("Big lean-to, glazed, fleur boards", dict(kind='lean', depth=5000.0, h_back=5200.0, h_front=3800.0,
                                               bay=3600.0, col_set=900.0, col_d=180.0, bracket=750.0,
                                               roof='glazed', valance='fleur', board_w=180.0, val_h=550.0)),
    ("Island umbrella, rounded boards", dict(kind='island', width=6000.0, h_centre=4600.0, island_pitch=8.0,
                                             island_roof='ridge', bay=3600.0, valance='round', board_w=180.0,
                                             val_h=450.0)),
    ("Island butterfly, glazed", dict(kind='island', width=7000.0, h_centre=4200.0, island_pitch=6.0,
                                      island_roof='butterfly', roof='glazed', valance='dagger')),
    ("Ridge and furrow, glazed", dict(kind='ridge', depth=4500.0, h_front=3800.0, rf_w=3000.0, rf_pitch=26.0,
                                      roof='glazed', valance='dagger', bay=3000.0, col_set=600.0)),
    ("Country halt, timber, saw-tooth", dict(kind='lean', depth=2400.0, h_back=3600.0, h_front=3000.0,
                                             bay=2400.0, col_style='timber', post_w=150.0, bracket=450.0,
                                             roof='plain', valance='saw', board_w=150.0, val_h=300.0)),
    ("1:80 print - GWR lean-to", dict(kind='lean', depth=3000.0, h_back=4300.0, h_front=3400.0, bay=3000.0,
                                      col_style='castiron', col_d=160.0, bracket=600.0, roof='plain',
                                      roof_t=80.0, valance='dagger', board_w=160.0, val_h=480.0, val_t=40.0)),
    ("1:80 print - island umbrella", dict(kind='island', width=6000.0, h_centre=4600.0, island_pitch=8.0,
                                          col_d=160.0, roof_t=80.0, valance='round', board_w=180.0,
                                          val_h=480.0, val_t=40.0)),
]

PRESETS_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Station Canopies")


def load_presets():
    out = list(PRESETS)
    try:
        for fn in sorted(os.listdir(PRESETS_DIR)):
            if fn.lower().endswith(".json"):
                with open(os.path.join(PRESETS_DIR, fn), "r", encoding="utf-8") as f:
                    out.append((fn[:-5], json.load(f)))
    except Exception:
        pass
    return out


def save_preset(name, values):
    os.makedirs(PRESETS_DIR, exist_ok=True)
    safe = "".join(ch for ch in name if ch not in '\\/:*?"<>|').strip() or "My canopy"
    with open(os.path.join(PRESETS_DIR, safe + ".json"), "w", encoding="utf-8") as f:
        json.dump(values, f, indent=1)
    return safe


def _narrow(cb, n):
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
    return fl


# (tab, key, label, low, high, decimals, suffix, tip) - the letters match the Sizes drawing
FIELDS = [
    ("Canopy", 'length', "Length (0 = the face)", 0.0, 500000.0, 0, " mm",
     "How long the canopy is. 0 = the whole length of the face you selected (or 6 m with nothing "
     "selected). A set length is centred on the face."),
    ("Canopy", 'depth', "A  Depth out from wall", 500.0, 20000.0, 0, " mm",
     "Lean-to and ridge and furrow: how far the canopy reaches out from the wall to its front edge."),
    ("Canopy", 'width', "A  Width (island)", 1000.0, 30000.0, 0, " mm",
     "Island: the canopy's whole width across, edge to edge."),
    ("Canopy", 'edge_back', "Set back from platform edge", 0.0, 5000.0, 0, " mm",
     "Island, with 'Width from the platform' ticked: how far each edge of the canopy stops short of the "
     "platform edge."),
    ("Canopy", 'h_back', "B  Height at the wall", 1500.0, 20000.0, 0, " mm",
     "Lean-to: the underside of the roof where it meets the wall, above the platform."),
    ("Canopy", 'h_front', "C  Height at the front", 1500.0, 20000.0, 0, " mm",
     "Lean-to and ridge and furrow: the underside of the roof at the front edge, above the platform."),
    ("Canopy", 'h_centre', "B  Height at centre (island)", 1500.0, 20000.0, 0, " mm",
     "Island: the underside of the roof over the middle (the ridge, or the edges of a butterfly roof)."),
    ("Canopy", 'island_pitch', "Roof pitch (island)", 0.0, 30.0, 1, " deg",
     "Island: how steeply the roof falls each way. Canopies are low: 5 to 10 degrees."),
    ("Canopy", 'bay', "D  Column spacing", 500.0, 20000.0, 0, " mm",
     "About how far apart the columns are (they're spaced evenly along the length). 3 m is typical."),
    ("Canopy", 'end_in', "E  First column in from end", 0.0, 10000.0, 0, " mm",
     "How far the end columns stand in from the ends of the canopy."),
    ("Canopy", 'col_set', "F  Columns back from front", 0.0, 10000.0, 0, " mm",
     "Lean-to and ridge and furrow: how far the column row stands back from the front edge."),
    ("Canopy", 'z_off', "Platform above face bottom", -5000.0, 20000.0, 0, " mm",
     "Lean-to and ridge and furrow: where the platform is, measured up from the bottom of the wall face. "
     "0 = the platform is at the foot of the wall."),
    ("Canopy", 'wall_gap', "Gap off the wall", 0.0, 50.0, 2, " mm",
     "A hair's gap between the canopy and the wall, so no faces lie on top of each other."),
    ("Columns", 'col_d', "G  Column diameter", 50.0, 1000.0, 0, " mm",
     "Cast iron: across the shaft. 150 mm is typical (1.9 mm at 1:80)."),
    ("Columns", 'post_w', "G  Post size", 50.0, 1000.0, 0, " mm", "Timber: the square post's size."),
    ("Columns", 'bracket', "H  Bracket size", 100.0, 3000.0, 0, " mm",
     "How far the spandrels or knee braces reach along the beam (and down the column)."),
    ("Columns", 'bracket_t', "Bracket thickness", 5.0, 500.0, 0, " mm",
     "How thick the spandrels (and knee braces) are. For printing keep it 32 mm or more at 1:80 "
     "(0.4 mm); 40 is safer."),
    ("Columns", 'segments', "Round segments", 8.0, 96.0, 0, "",
     "How many sides round things have: the columns all the way round, the curve of the spandrels and the "
     "pierced holes (half as many). More is smoother but makes the model bigger. 24 is good; 48 for close-ups "
     "or resin."),
    ("Columns", 'beam_d', "I  Beam depth", 50.0, 2000.0, 0, " mm",
     "The beam along the top of the columns, and the front fascia."),
    ("Columns", 'beam_w', "Beam width", 30.0, 1000.0, 0, " mm", "How thick the beams are."),
    ("Roof", 'roof_t', "J  Roof thickness", 5.0, 1000.0, 0, " mm",
     "The roof covering. For 1:80 printing keep it 60 mm or more (0.75 mm)."),
    ("Roof", 'roll_sp', "Lead rolls every", 200.0, 3000.0, 0, " mm",
     "Lead roofs: how far apart the rolls are - the width of one lead sheet (about 600 mm)."),
    ("Roof", 'roll_d', "Lead roll size", 10.0, 300.0, 0, " mm",
     "Lead roofs: how big round the rolls are (about 50 mm; 0.6 mm at 1:80)."),
    ("Roof", 'bar_w', "Glazing bar width", 10.0, 500.0, 0, " mm", "Glazed roofs: the bars between the panes."),
    ("Roof", 'bar_sp', "Glazing bars every", 100.0, 5000.0, 0, " mm",
     "Glazed roofs: how far apart the bars are (about 600 mm)."),
    ("Roof", 'rf_w', "K  Ridge spacing", 500.0, 20000.0, 0, " mm",
     "Ridge and furrow: from one valley gutter to the next (each ridge's width)."),
    ("Roof", 'rf_pitch', "Ridge pitch", 5.0, 60.0, 1, " deg", "Ridge and furrow: how steep each ridge is."),
    ("Roof", 'flash_t', "N  Flashing thickness", 1.0, 200.0, 1, " mm",
     "Lean-to: how thick the lead flashing against the wall is. For 1:80 printing 32 mm (0.4 mm) or more."),
    ("Roof", 'flash_up', "O  Flashing up the wall", 20.0, 2000.0, 0, " mm",
     "Lean-to: how far the flashing's upstand runs up the wall above the roof."),
    ("Roof", 'flash_cover', "P  Flashing onto the roof", 20.0, 2000.0, 0, " mm",
     "Lean-to: how far the flashing's apron lies down over the roof from the wall."),
    ("Bell roof", 'bell_w', "A  Width at the eaves", 500.0, 30000.0, 0, " mm",
     "How wide the roof is at the eaves (not used when 'Size from the face' is ticked)."),
    ("Bell roof", 'bell_d', "A  Depth at the eaves", 500.0, 30000.0, 0, " mm",
     "How deep the roof is at the eaves, front to back (not used when 'Size from the face' is ticked)."),
    ("Bell roof", 'bell_over', "Overhang", 0.0, 3000.0, 0, " mm",
     "How far the eaves stand out past the face it's built on (and past the fascia)."),
    ("Bell roof", 'bell_h', "H  Rise", 100.0, 20000.0, 0, " mm", "How tall the roof is, eaves to the flat top."),
    ("Bell roof", 'bell_tw', "T  Top width", 50.0, 20000.0, 0, " mm", "The flat top's width."),
    ("Bell roof", 'bell_td', "T  Top depth", 50.0, 20000.0, 0, " mm", "The flat top's depth."),
    ("Bell roof", 'bell_sweep', "Sweep (bell-cast)", 0.0, 100.0, 0, " %",
     "How much the faces sweep: 0 = straight hips, more = flat at the eaves and steep at the top, like a bell."),
    ("Bell roof", 'bell_cap', "Cap on top", 0.0, 2000.0, 0, " mm", "The cap on the flat top. 0 = none."),
    ("Bell roof", 'bell_fascia', "Fascia depth", 0.0, 2000.0, 0, " mm",
     "The fascia (with a moulded step) round under the eaves. 0 = none."),
    ("Valance", 'board_w', "L  Board width", 20.0, 2000.0, 0, " mm",
     "One valance board. They're fitted a whole number to the length, so it may change a little."),
    ("Valance", 'val_h', "M  Valance depth", 50.0, 3000.0, 0, " mm",
     "How far the valance hangs down, to the tips of the boards."),
    ("Valance", 'val_t', "Board thickness", 5.0, 200.0, 0, " mm",
     "How thick the boards are. For 1:80 printing 32 mm or more (0.4 mm); 40 is safer."),
]


# ---------------------------------------------------------------------------
# Preview: a short length in 3D, and a Sizes drawing with the letters
# ---------------------------------------------------------------------------
COLOURS = {'Columns': (60, 84, 72), 'Brackets': (60, 84, 72), 'Beams': (196, 180, 150),
           'Roof': (110, 112, 124), 'Glass': (170, 205, 225), 'Valance': (214, 200, 160),
           'Flashing': (120, 124, 130)}


def preview_items(v):
    """Painter's list for one bay and a bit, seen from the front, a little from above."""
    pv = dict(v)
    bay = max(500.0, pv['bay'])
    end_in = min(max(0.0, pv['end_in']), bay * 0.4)
    pv['end_in'] = end_in
    L = bay * 2 + 2 * end_in
    if pv['kind'] == 'ridge':
        L = max(L, 2 * max(500.0, pv['rf_w']))
    parts, _ = build_canopy(L, pv)
    if pv['kind'] == 'island':
        D = v_norm((0.55, 0.75, -0.38))
    else:
        D = v_norm((0.5, -0.8, -0.32))
    R = v_norm(v_cross(D, Z))
    U = v_cross(R, D)
    light = v_norm((-0.35, -0.55, 0.75))
    items = []
    piece = bay / 4.0

    def split(outer, holes):
        # long plain quads (roof slabs, beams) are cut into short pieces, so they sort properly
        if holes or len(outer) != 4:
            return [outer]
        a, b, c, d = outer
        if v_len(v_sub(b, a)) < v_len(v_sub(c, b)):
            a, b, c, d = b, c, d, a
        k = int(min(40, max(1, math.ceil(v_len(v_sub(b, a)) / piece))))
        if k == 1:
            return [outer]

        def lerp(p, q, t):
            return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, p[2] + (q[2] - p[2]) * t)
        return [[lerp(a, b, i / k), lerp(a, b, (i + 1) / k), lerp(d, c, (i + 1) / k), lerp(d, c, i / k)]
                for i in range(k)]
    for k, sols in parts.items():
        col = COLOURS.get(k, (150, 150, 150))
        for so in [so_ for it in sols for so_ in it]:
            for outer0, holes in so:
                bits = split(outer0, holes)
                for outer in bits:
                    n = _newell(outer)
                    if v_dot(n, D) >= 0:
                        continue
                    sh = 0.42 + 0.58 * max(0.0, v_dot(n, light))
                    d = max(v_dot(p, D) for p in outer) * 0.3 + sum(v_dot(p, D) for p in outer) / len(outer) * 0.7
                    items.append((d, [(v_dot(p, R), -v_dot(p, U)) for p in outer],
                                  tuple(int(c * sh) for c in col),
                                  [[(v_dot(p, R), -v_dot(p, U)) for p in h] for h in holes], len(bits) == 1))
    items.sort(key=lambda it: -it[0])
    return items


def sizes_drawing(v):
    """The end section and a few valance boards, with the letters. Returns (lines, labels):
    lines [(x0, y0, x1, y1, kind)], labels [(x, y, text)], y up, mm."""
    lines, labels = [], []
    kind = v['kind']
    bd = v['beam_d']
    vh = v['val_h']

    def dim(x0, y0, x1, y1, txt, off=(0, 0)):
        lines.append((x0, y0, x1, y1, 'dim'))
        labels.append(((x0 + x1) / 2 + off[0], (y0 + y1) / 2 + off[1], txt))
    if kind in ('lean', 'ridge'):
        D = v['depth']
        Hf = v['h_front']
        Hb = Hf if kind == 'ridge' else max(Hf, v['h_back'])
        yc = D - v['col_set']
        zr = Hf + (Hb - Hf) * (D - yc) / D
        lines += [(0, -200, 0, Hb + 900, 'wall'), (-600, 0, D + 900, 0, 'ground'),
                  (0, Hb, D, Hf, 'roof'), (yc, 0, yc, zr - bd, 'col'), (yc - 60, zr - bd, yc + 60, zr - bd, 'col'),
                  (D, Hf, D, Hf - vh, 'val')]
        dim(0, -350, D, -350, "A", (0, -160))
        if kind == 'lean':
            dim(-300, 0, -300, Hb, "B", (-160, 0))
        dim(D + 350, 0, D + 350, Hf, "C", (160, 0))
        dim(yc, Hf - vh - 250, D, Hf - vh - 250, "F", (0, -160))
        dim(D + 150, Hf, D + 150, Hf - vh, "M", (130, 0))
        dim(yc + 120, zr - bd, yc + 120, zr, "I", (120, 0))
        if kind == 'lean' and v.get('flash'):
            t_ = v['roof_t']
            sec = flashing_section(lambda y: Hb + (Hf - Hb) * y / D + t_, v)
            for p_, q_ in zip(sec, sec[1:] + sec[:1]):
                lines.append((p_[0], p_[1], q_[0], q_[1], 'flash'))
            dim(sec[0][0] + 120 + v['flash_cover'], sec[1][1], sec[0][0] + 120 + v['flash_cover'], sec[-1][1],
                "O", (130, 0))
            dim(0, sec[-1][1] + 120, v['flash_cover'], sec[-1][1] + 120, "P", (0, 130))
            labels.append((v['flash_cover'] * 0.5, sec[1][1] - 220, "N"))
        x_end = D + 900
    elif kind == 'bell':
        W, H = v['bell_w'], v['bell_h']
        ze = (v['h_centre'] if v.get('bell_cols') else 0.0) + v['bell_fascia'] + v['roof_t']
        rg = bell_rings(W, v['bell_d'], min(W * 0.9, v['bell_tw']), v['bell_td'], H, v['bell_sweep'] / 100.0, 24)
        lines.append((-W / 2 - 600, 0, W / 2 + 600, 0, 'ground'))
        for a_, b_ in zip(rg, rg[1:]):
            for sg in (-1, 1):
                lines.append((sg * a_[0], ze + a_[2], sg * b_[0], ze + b_[2], 'roof'))
        lines.append((-rg[-1][0], ze + H, rg[-1][0], ze + H, 'roof'))
        lines.append((-W / 2, ze, W / 2, ze, 'roof'))
        if v['bell_fascia'] > 0:
            fw = W / 2 - v['bell_over']
            lines += [(-fw, ze - v['roof_t'], -fw, ze - v['roof_t'] - v['bell_fascia'], 'val'),
                      (fw, ze - v['roof_t'], fw, ze - v['roof_t'] - v['bell_fascia'], 'val')]
        if v.get('bell_cols'):
            fw = W / 2 - v['bell_over'] - 60
            lines += [(-fw, 0, -fw, ze - v['roof_t'] - v['bell_fascia'], 'col'),
                      (fw, 0, fw, ze - v['roof_t'] - v['bell_fascia'], 'col')]
            dim(-W / 2 - 300, 0, -W / 2 - 300, ze - v['roof_t'] - v['bell_fascia'], "B", (-160, 0))
        dim(-W / 2, -350, W / 2, -350, "A", (0, -160))
        dim(W / 2 + 300, ze, W / 2 + 300, ze + H, "H", (160, 0))
        dim(-rg[-1][0], ze + H + 250, rg[-1][0], ze + H + 250, "T", (0, 150))
        x_end = W / 2 + 900
    else:
        Wd = v['width']
        Hc = v['h_centre']
        drop = Wd / 2 * math.tan(math.radians(v['island_pitch']))
        bf = v.get('island_roof') == 'butterfly'
        He = Hc + drop if bf else Hc - drop
        lines += [(-Wd / 2 - 600, 0, Wd / 2 + 600, 0, 'ground'),
                  (-Wd / 2, He, 0, Hc if not bf else Hc, 'roof'), (0, Hc, Wd / 2, He, 'roof'),
                  (0, 0, 0, Hc - bd, 'col'), (-60, Hc - bd, 60, Hc - bd, 'col'),
                  (-Wd / 2, He, -Wd / 2, He - vh, 'val'), (Wd / 2, He, Wd / 2, He - vh, 'val')]
        dim(-Wd / 2, -350, Wd / 2, -350, "A", (0, -160))
        dim(-250, 0, -250, Hc, "B", (-160, 0))
        dim(Wd / 2 + 150, He, Wd / 2 + 150, He - vh, "M", (130, 0))
        x_end = Wd / 2 + 900
    # three valance boards to one side, at the same scale
    b = v['board_w']
    pts, hole = board_bottom(v['valance'], b, vh)
    x0 = x_end + 300
    top = (v['h_front'] if kind not in ('island', 'bell') else max(v['h_centre'], 1500.0)) * 0.5 + vh / 2
    prev = None
    for k in range(3):
        q = [(x0 + k * b + u, top + w) for u, w in pts]
        if prev is not None:
            lines.append((prev[0], prev[1], q[0][0], q[0][1], 'val'))
        for a, c in zip(q, q[1:]):
            lines.append((a[0], a[1], c[0], c[1], 'val'))
        prev = q[-1]
        lines.append((x0 + k * b, top, x0 + k * b, top - 0.2 * vh, 'joint'))
        if hole and v.get('val_holes', True):
            cx, cy, r = hole
            c = circle(x0 + k * b + cx, top + cy, r, 12)
            for a, e in zip(c, c[1:] + c[:1]):
                lines.append((a[0], a[1], e[0], e[1], 'val'))
    lines += [(x0, top, x0 + 3 * b, top, 'val'), (x0, top, x0, top + pts[0][1], 'val'),
              (x0 + 3 * b, top, x0 + 3 * b, top + pts[-1][1], 'val')]
    dim(x0, top + 150, x0 + b, top + 150, "L", (0, 140))
    dim(x0 + 3 * b + 150, top, x0 + 3 * b + 150, top - vh, "M", (130, 0))
    return lines, labels


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


class CanopyPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(340, 300)
        self.v = None
        self.mode = '3d'
        self.items = []
        self.msg = ""

    def set_values(self, v):
        self.v = dict(v)
        try:
            self.items = preview_items(self.v) if self.mode == '3d' else []
            self.msg = ""
        except Exception as e:
            self.items, self.msg = [], "No preview: %s" % e
        self.update()

    def set_mode(self, mode):
        self.mode = mode
        if self.v:
            self.set_values(self.v)

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen, QPainterPath, QFont
        from PySide6.QtCore import QPointF, Qt
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(238, 238, 234))
        w, h = self.width() - 16, self.height() - 16
        if self.mode == '3d':
            if not self.items:
                p.drawText(self.rect(), Qt.AlignCenter, self.msg or "No preview")
                p.end()
                return
            xs = [x for it in self.items for x, _ in it[1]]
            ys = [y for it in self.items for _, y in it[1]]
            sc = min(w / ((max(xs) - min(xs)) or 1), h / ((max(ys) - min(ys)) or 1))
            ox = 8 + (w - (max(xs) - min(xs)) * sc) / 2 - min(xs) * sc
            oy = 8 + (h - (max(ys) - min(ys)) * sc) / 2 - min(ys) * sc
            for _, pts, rgb, holes, edge in self.items:
                col = QColor(*rgb)
                p.setBrush(col)
                p.setPen(QPen(col.darker(160), 0.6) if edge else QPen(col, 0.8))
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
            p.end()
            return
        try:
            lines, labels = sizes_drawing(self.v)
        except Exception as e:
            p.drawText(self.rect(), Qt.AlignCenter, "No drawing: %s" % e)
            p.end()
            return
        xs = [c for ln in lines for c in (ln[0], ln[2])] + [l[0] for l in labels]
        ys = [c for ln in lines for c in (ln[1], ln[3])] + [l[1] for l in labels]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        sc = min(w / ((x1 - x0) or 1), h / ((y1 - y0) or 1))
        ox = 8 + (w - (x1 - x0) * sc) / 2
        oy = 8 + (h - (y1 - y0) * sc) / 2

        def P(x, y):
            return QPointF(ox + (x - x0) * sc, oy + (y1 - y) * sc)
        pens = {'wall': QPen(QColor(150, 90, 70), 3), 'ground': QPen(QColor(120, 120, 120), 1.5),
                'roof': QPen(QColor(80, 80, 95), 3), 'col': QPen(QColor(50, 80, 65), 2.5),
                'val': QPen(QColor(150, 120, 60), 1.4), 'joint': QPen(QColor(170, 150, 110), 0.8),
                'dim': QPen(QColor(30, 90, 180), 1.0), 'flash': QPen(QColor(90, 95, 105), 1.6)}
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
# Dialog
# ---------------------------------------------------------------------------
class CanopyDialog(QDialog):
    def __init__(self, viewport, tool, cur):
        super().__init__(viewport)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        lay = QVBoxLayout(self)
        intro = QLabel("Lean-to or ridge and furrow: select the wall face. Island: select the platform's top "
                       "face. Then Build. Sizes in real mm.")
        intro.setWordWrap(True)
        lay.addWidget(intro)
        top = QFormLayout()
        self.cb_kind = QComboBox()
        for k, t in KINDS:
            self.cb_kind.addItem(t, k)
        self.cb_kind.setToolTip("Lean-to: off a building's wall, sloping to the front. Island: over an island "
                                "platform, on one row of columns. Ridge and furrow: glazed ridges running out "
                                "from the wall.")
        _narrow(self.cb_kind, 14)
        top.addRow("Make", self.cb_kind)
        self.cb_preset = QComboBox()
        _narrow(self.cb_preset, 14)
        self.cb_preset.setToolTip("Ready-made canopies. Pick one and the window is filled in; your own "
                                  "presets are in the list too.")
        prow = QHBoxLayout()
        prow.addWidget(self.cb_preset, 1)
        b_save = QPushButton("Save as...")
        b_save.setToolTip("Saves everything in this window as your own preset.")
        prow.addWidget(b_save)
        top.addRow("Preset", prow)
        lay.addLayout(top)

        self.preview = CanopyPreview()
        self.preview.setToolTip("A short length of the canopy as it will be built. It changes as you change "
                                "the settings.")
        self.views = QTabWidget()
        self.views.addTab(self.preview, "3D view")
        self.sizes = CanopyPreview()
        self.sizes.mode = 'sizes'
        self.sizes.setToolTip("An end view with the sizes lettered, and three valance boards.")
        self.views.addTab(self.sizes, "Sizes (A, B, C ...)")
        self.views.setTabToolTip(0, "A short length of the canopy in 3D.")
        self.views.setTabToolTip(1, "An end view with the sizes lettered: the letters match the settings.")
        side = QHBoxLayout()                # the picture on the left, the settings beside it
        lay.addLayout(side)
        side.addWidget(self.views, 1)

        self.tabs = QTabWidget()
        pages = {}
        for title in ("Canopy", "Columns", "Roof", "Valance", "Bell roof"):
            pg = QWidget()
            pages[title] = _form(pg)
            self.tabs.addTab(pg, title)
        self.tabs.setTabToolTip(0, "The canopy's shape, size and where the columns go.")
        self.tabs.setTabToolTip(1, "Cast-iron columns or timber posts, their brackets and the beams.")
        self.tabs.setTabToolTip(2, "Plain or glazed roof, and the ridges of a ridge and furrow canopy.")
        self.tabs.setTabToolTip(3, "The valance boards along the edges.")
        self.tabs.setTabToolTip(4, "A bell-cast roof: hipped, sweeping out at the eaves, flat on top - for a kiosk, "
                                   "bay window, porch or cupola. Lead with rolls, or plain.")
        side.addWidget(self.tabs, 1)
        self.w, self.labs = {}, {}
        for tab, key, label, lo, hi, dec, suf, tip in FIELDS:
            s = QDoubleSpinBox()
            s.setDecimals(dec)
            s.setRange(lo, hi)
            s.setSuffix(suf)
            s.setKeyboardTracking(False)
            s.setToolTip(tip)
            lab = QLabel(label)
            lab.setToolTip(tip)
            pages[tab].addRow(lab, s)
            self.w[key] = s
            self.labs[key] = lab

        def combo(page, row, label, items, tip):
            cb = QComboBox()
            for k, t in items:
                cb.addItem(t, k)
            cb.setToolTip(tip)
            _narrow(cb, 12)
            lab = QLabel(label)
            lab.setToolTip(tip)
            page.insertRow(row, lab, cb)
            return cb, lab
        self.cb_iroof, self.lab_iroof = combo(pages["Canopy"], 8, "Island roof", ISLAND_ROOFS,
                                              "Island: a ridged roof falling to both edges, or a butterfly roof "
                                              "falling to a gutter over the columns.")
        self.cb_fit = QCheckBox("Width from the platform (island)")
        self.cb_fit.setToolTip("Island: the canopy is as wide as the selected platform face, less the set back "
                               "at each edge, instead of the width A.")
        pages["Canopy"].insertRow(3, self.cb_fit)
        self.cb_flip = QCheckBox("Build on the other side of the wall face")
        self.cb_flip.setToolTip("Lean-to and ridge and furrow: if the canopy comes out inside the building, tick "
                                "this and build again (undo the first one).")
        pages["Canopy"].addRow(self.cb_flip)
        self.cb_fitwall = QCheckBox("Keep it under the top of the wall")
        self.cb_fitwall.setToolTip("Lean-to and ridge and furrow: if the canopy's roof would stand above the top of "
                                   "the wall face, it's lowered (B and C) so its top meets the wall 25 mm below "
                                   "the top. Untick to build it at the heights you set.")
        pages["Canopy"].addRow(self.cb_fitwall)
        self.cb_col, _ = combo(pages["Columns"], 0, "Columns", COL_STYLES,
                               "Cast iron: turned columns with a flared capital and pierced spandrel brackets. "
                               "Timber: square posts with knee braces.")
        self.cb_brk = QCheckBox("Brackets (spandrels / knee braces)")
        self.cb_brk.setToolTip("The brackets between the tops of the columns and the beams.")
        pages["Columns"].insertRow(2, self.cb_brk)
        self.cb_roof, _ = combo(pages["Roof"], 0, "Roof", ROOFS,
                                "Plain: a solid roof (slate, boards or felt). Glazed: glazing bars running down "
                                "the slope with glass between (a separate 'Glass' group, for clear resin). Lead: lead sheet "
                                "with rolls running down the slope, a sheet's width apart.")
        self.cb_val, _ = combo(pages["Valance"], 0, "Pattern", VALANCES, "The shape cut on the bottom of each board.")
        self.cb_holes = QCheckBox("Pierced holes in the boards")
        self.cb_holes.setToolTip("A round hole cut through each board (dagger, rounded and fleur boards). For "
                                 "1:80 they're about 0.5 mm - fine for resin, may close up on FDM.")
        pages["Valance"].addRow(self.cb_holes)
        self.cb_ends = QCheckBox("Valance down the open ends (lean-to)")
        self.cb_ends.setToolTip("Lean-to: valancing down each open end too, following the roof's slope.")
        pages["Valance"].addRow(self.cb_ends)
        self.cb_bfit = QCheckBox("Size from the selected face (+ overhang)")
        self.cb_bfit.setToolTip("Bell roof: the eaves are the size of the face you selected, plus the overhang all "
                                "round - so it fits the bay or kiosk it sits on.")
        pages["Bell roof"].insertRow(0, self.cb_bfit)
        self.cb_bcols = QCheckBox("On four columns (a kiosk or porch)")
        self.cb_bcols.setToolTip("Bell roof: stands on a column at each corner (the Columns tab's style, with "
                                 "brackets), its eaves at the Canopy tab's centre height. Off: it sits straight on "
                                 "the face.")
        pages["Bell roof"].insertRow(1, self.cb_bcols)
        self.cb_bval = QCheckBox("Valance round the eaves")
        self.cb_bval.setToolTip("Bell roof: the Valance tab's boards hang all round the eaves.")
        pages["Bell roof"].insertRow(2, self.cb_bval)
        self.cb_flash = QCheckBox("Lead flashing against the wall (lean-to)")
        self.cb_flash.setToolTip("Lean-to: an L of lead where the roof meets the wall - up the wall and down over "
                                 "the roof - its own group, its thickness (N) set so it will print.")
        pages["Roof"].insertRow(1, self.cb_flash)

        self.lbl_report = QLabel()
        self.lbl_report.setWordWrap(True)
        lay.addWidget(self.lbl_report)
        brow = QHBoxLayout()
        b_go = QPushButton("Build")
        b_go.setDefault(True)
        b_go.setToolTip("Builds the canopy on the selected face, as one group with a group for each part.")
        b_close = QPushButton("Close")
        brow.addWidget(b_go)
        brow.addStretch(1)
        brow.addWidget(b_close)
        lay.addLayout(brow)
        try:
            self.setMaximumWidth(900)
        except Exception:
            pass
        self.set_values(cur)
        self.fill_presets()
        self.cb_kind.currentIndexChanged.connect(self.changed)
        for s_ in self.w.values():
            s_.valueChanged.connect(self.redraw)
        for cb in (self.cb_iroof, self.cb_col, self.cb_roof, self.cb_val):
            cb.currentIndexChanged.connect(self.changed)
        for ck in (self.cb_fit, self.cb_brk, self.cb_holes, self.cb_ends, self.cb_flip, self.cb_fitwall, self.cb_flash,
                   self.cb_bfit, self.cb_bcols, self.cb_bval):
            ck.toggled.connect(self.changed)
        try:
            self.cb_preset.activated.connect(self.preset_picked)
        except Exception:
            self.cb_preset.currentIndexChanged.connect(self.preset_picked)
        b_save.clicked.connect(self.save_as)
        b_go.clicked.connect(lambda: self.tool.build(self))
        b_close.clicked.connect(self.close)
        self.changed()

    def fill_presets(self):
        self.cb_preset.clear()
        self.cb_preset.addItem("(pick a preset)", None)
        for name, vals in load_presets():
            self.cb_preset.addItem(name, name)
        self._presets = dict(load_presets())

    def preset_picked(self, *_):
        name = self.cb_preset.currentData()
        if not name:
            return
        vals = dict(DEFAULTS)
        vals.update(self._presets.get(name, {}))
        self.set_values(vals)
        self.changed()

    def save_as(self, *_):
        try:
            from PySide6.QtWidgets import QInputDialog
            name, ok = QInputDialog.getText(self, PLUGIN_NAME, "Name for this preset:")
        except Exception:
            return
        if not ok or not str(name).strip():
            return
        safe = save_preset(str(name), self.values())
        self.fill_presets()
        for i in range(self.cb_preset.count()):
            if self.cb_preset.itemData(i) == safe:
                self.cb_preset.setCurrentIndex(i)

    def set_values(self, cur):
        for k, s in self.w.items():
            if k in cur:
                s.setValue(float(cur[k]))
        for cb, key in ((self.cb_kind, 'kind'), (self.cb_iroof, 'island_roof'), (self.cb_col, 'col_style'),
                        (self.cb_roof, 'roof'), (self.cb_val, 'valance')):
            for i in range(cb.count()):
                if cb.itemData(i) == cur.get(key):
                    cb.setCurrentIndex(i)
        for ck, key in ((self.cb_fit, 'fit_width'), (self.cb_brk, 'brackets'), (self.cb_holes, 'val_holes'),
                        (self.cb_ends, 'val_ends'), (self.cb_flip, 'flip'), (self.cb_fitwall, 'fit_wall'),
                        (self.cb_flash, 'flash'), (self.cb_bfit, 'bell_fit'), (self.cb_bcols, 'bell_cols'),
                        (self.cb_bval, 'bell_val')):
            ck.setChecked(bool(cur.get(key, DEFAULTS[key])))

    def redraw(self, *_):
        try:
            v = self.values()
            self.preview.set_values(v)
            self.sizes.set_values(v)
        except Exception:
            pass

    def changed(self, *_):
        v = self.values()
        kind = v['kind']
        isl = kind == 'island'
        bell = kind == 'bell'
        glazed = v['roof'] == 'glazed'
        on = {'depth': not isl, 'width': isl and not v['fit_width'], 'edge_back': isl and v['fit_width'],
              'h_back': kind == 'lean', 'h_front': not isl, 'h_centre': isl, 'island_pitch': isl,
              'col_set': not isl, 'z_off': not isl, 'wall_gap': not isl,
              'col_d': v['col_style'] != 'timber', 'post_w': v['col_style'] == 'timber', 'bracket': v['brackets'],
              'bracket_t': v['brackets'],
              'bar_w': glazed, 'bar_sp': glazed,
              'roll_sp': v['roof'] == 'lead', 'roll_d': v['roof'] == 'lead', 'rf_w': kind == 'ridge', 'rf_pitch': kind == 'ridge',
              'flash_t': kind == 'lean' and v['flash'], 'flash_up': kind == 'lean' and v['flash'],
              'flash_cover': kind == 'lean' and v['flash']}
        if bell:
            # the bell roof uses its own tab, the columns (if on columns) and the lead or plain roof
            on = {k: False for k in on}
            for k in ('col_d', 'post_w', 'bracket', 'bracket_t'):
                on[k] = v['bell_cols'] and {'col_d': v['col_style'] != 'timber', 'post_w': v['col_style'] == 'timber',
                                            'bracket': v['brackets'], 'bracket_t': v['brackets']}[k]
            on.update(h_centre=v['bell_cols'], roll_sp=v['roof'] == 'lead', roll_d=v['roof'] == 'lead')
        for k_ in ('bell_w', 'bell_d'):
            on[k_] = bell and not v['bell_fit']
        for k_ in ('bell_over', 'bell_h', 'bell_tw', 'bell_td', 'bell_sweep', 'bell_cap', 'bell_fascia'):
            on[k_] = bell
        for k, ok in on.items():
            self.w[k].setEnabled(ok)
            self.labs[k].setEnabled(ok)
        for wdg in (self.cb_bfit, self.cb_bcols, self.cb_bval):
            wdg.setEnabled(bell)
        self.tabs.setTabEnabled(4, bell)
        for wdg in (self.cb_iroof, self.lab_iroof, self.cb_fit):
            wdg.setEnabled(isl)
        self.cb_ends.setEnabled(kind == 'lean')
        self.cb_flash.setEnabled(kind == 'lean')
        self.cb_flip.setEnabled(not isl and not bell)
        self.cb_fitwall.setEnabled(not isl and not bell)
        self.redraw()

    def values(self):
        v = {k: float(s.value()) for k, s in self.w.items()}
        v.update(kind=self.cb_kind.currentData() or 'lean', island_roof=self.cb_iroof.currentData() or 'ridge',
                 col_style=self.cb_col.currentData() or 'castiron', roof=self.cb_roof.currentData() or 'plain',
                 valance=self.cb_val.currentData() or 'dagger', fit_width=self.cb_fit.isChecked(),
                 brackets=self.cb_brk.isChecked(), val_holes=self.cb_holes.isChecked(),
                 val_ends=self.cb_ends.isChecked(), flip=self.cb_flip.isChecked(), flash=self.cb_flash.isChecked(),
                 fit_wall=self.cb_fitwall.isChecked(), bell_fit=self.cb_bfit.isChecked(),
                 bell_cols=self.cb_bcols.isChecked(), bell_val=self.cb_bval.isChecked())
        return v


# ---------------------------------------------------------------------------
# Placing it: the canopy's frame from the selected face
# ---------------------------------------------------------------------------
def canopy_frame(pts, v):
    """From a face's corners (world metres): (origin, X, Y, length mm, info). The canopy is
    built with x along X, y along Y, z up, in mm from the origin."""
    kind = v['kind']
    n = _newell(pts)
    upright = abs(n[2]) < 0.5
    if kind in ('lean', 'ridge'):
        if not upright:
            raise ValueError("A lean-to or ridge and furrow canopy goes on a wall: select the wall face it "
                             "runs along (an upright face).")
        nh = v_norm((n[0], n[1], 0.0))
        if v.get('flip'):
            nh = v_mul(nh, -1.0)
        X = v_cross(nh, Z)
        Y = nh
        xs = [v_dot(p, X) for p in pts]
        zb = min(p[2] for p in pts)
        x0, x1 = min(xs), max(xs)
        plane = v_dot(pts[0], Y)
        L = (x1 - x0) / SCALE
        start = x0
        if v['length'] > 0:
            start = (x0 + x1) / 2 - v['length'] * SCALE / 2
            L = v['length']
        O = v_add(v_add(v_mul(X, start), v_mul(Y, plane + v['wall_gap'] * SCALE)), (0.0, 0.0, 0.0))
        O = (O[0], O[1], zb + v['z_off'] * SCALE)
        # how much wall there is above the platform (to keep the canopy under its top)
        return O, X, Y, L, (max(p[2] for p in pts) - zb) / SCALE - v['z_off']
    # island: on top of the platform
    if upright or n[2] < 0:
        raise ValueError("An island canopy stands on the platform: select the platform's top face (a flat, "
                         "upward face).")
    k = max(range(len(pts)), key=lambda i: v_len(v_sub(pts[(i + 1) % len(pts)], pts[i])))
    e = v_sub(pts[(k + 1) % len(pts)], pts[k])
    X = v_norm((e[0], e[1], 0.0))
    Y = v_cross(Z, X)
    xs = [v_dot(p, X) for p in pts]
    ys = [v_dot(p, Y) for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    zt = max(p[2] for p in pts)
    L = (x1 - x0) / SCALE
    start = x0
    if v['length'] > 0:
        start = (x0 + x1) / 2 - v['length'] * SCALE / 2
        L = v['length']
    yc = (y0 + y1) / 2
    O = v_add(v_mul(X, start), v_mul(Y, yc))
    O = (O[0], O[1], zt)
    return O, X, Y, L, (y1 - y0) / SCALE


def map_solid(so, O, X, Y):
    def P(p):
        return (O[0] + (X[0] * p[0] + Y[0] * p[1]) * SCALE,
                O[1] + (X[1] * p[0] + Y[1] * p[1]) * SCALE,
                O[2] + p[2] * SCALE)
    return [([P(q) for q in outer], [[P(q) for q in h] for h in holes]) for outer, holes in so]


def fit_under_wall(v, avail):
    """Lowers a lean-to (or ridge and furrow) whose roof would stand above the top of the wall
    face it's on, so the roof's top meets the wall 25 mm below its top. Returns a note, or ""."""
    t = max(5.0, v['roof_t'])
    if v['kind'] == 'lean':
        top = max(v['h_front'], v['h_back']) + t
        if v.get('flash'):
            top += 0.5 + max(1.0, v.get('flash_up', 150.0))       # the flashing's upstand too
    else:
        rw = max(500.0, v['rf_w'])
        top = v['h_front'] + rw / 2 * math.tan(math.radians(max(5.0, min(60.0, v['rf_pitch'])))) + t * 1.2
    over = top - (avail - 25.0)
    if over <= 0:
        return ""
    if avail < 2300.0:
        raise ValueError("The wall face is only %.0f mm tall above the platform - too low for this canopy. "
                         "Select a taller wall, or untick 'Keep it under the top of the wall'." % avail)
    if v['kind'] == 'lean':
        # lowered as a whole, keeping its slope while the front stays at least 2 m up
        hb = max(v['h_front'], v['h_back']) - over
        v['h_front'] = min(hb, max(2000.0, v['h_front'] - over))
        v['h_back'] = hb
        return (" Lowered to fit under the top of the wall: B is now %.0f mm and C %.0f mm."
                % (v['h_back'], v['h_front']))
    v['h_front'] -= over
    return " Lowered to fit under the top of the wall: C is now %.0f mm." % v['h_front']


class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
class StationCanopiesTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+C"
    description = ("Railway platform canopies - lean-to, island and ridge and furrow - on cast-iron columns "
                   "or timber posts, with dagger, rounded or fleur valancing.")
    _dialog = None
    _saved = None
    _errors = (0, None)
    _timber = False
    _val_names = None

    def on_activate(self, viewport):
        dlg = StationCanopiesTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.viewport = viewport
                    dlg.raise_()
                    dlg.activateWindow()
                    return
            except Exception:
                pass
        dlg = CanopyDialog(viewport, self, dict(DEFAULTS, **(StationCanopiesTool._saved or {})))
        StationCanopiesTool._dialog = dlg

        def closed(*_):
            StationCanopiesTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass

    def _picked(self, viewport):
        scene = getattr(viewport, 'scene', None)
        polys = []
        for f in selected_faces(scene) if scene is not None else []:
            pts = [_pos(p) for p in _items(getattr(f, 'vertices', None))]
            pts = [p for p in pts if p is not None]
            if len(pts) >= 3:
                polys.append(pts)
        return polys

    def build(self, dlg):
        v = dlg.values()
        StationCanopiesTool._saved = dict(v)
        polys = self._picked(dlg.viewport)
        kind = v['kind']
        note = ""
        try:
            if polys:
                O, X, Y, L, plat_w = canopy_frame(polys[0], v)
                if len(polys) > 1:
                    note = " (More than one face was selected: it's on the first.)"
            else:
                O, X, Y = (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
                L = v['length'] if v['length'] > 0 else 6000.0
                plat_w = None
                note = " (Nothing was selected, so it's at the origin, %s.)" % (
                    "the wall along the x axis" if kind != 'island' else "along the x axis")
            if kind == 'bell':
                if v.get('bell_fit') and plat_w:
                    v['bell_w'] = L + 2 * v['bell_over']
                    v['bell_d'] = plat_w + 2 * v['bell_over']
                if not polys:
                    L = 0.0                           # centred on the origin
            elif L < 1000.0:
                raise ValueError("That face is only %.0f mm long - a canopy needs at least 1000 mm." % L)
            if kind == 'island' and v['fit_width'] and plat_w:
                v['width'] = max(1000.0, plat_w - 2 * v['edge_back'])
            if kind in ('lean', 'ridge') and v.get('fit_wall', True) and plat_w is not None:
                note = fit_under_wall(v, plat_w) + note
            parts, info = build_canopy(L, v)
        except ValueError as e:
            QMessageBox.warning(dlg, PLUGIN_NAME, str(e))
            return
        parts = {k: [[map_solid(s, O, X, Y) for s in it] for it in its] for k, its in parts.items() if its}
        name = "Station canopy - %s %.1f m" % (dict(KINDS)[kind].split(" (")[0].split(" /")[0].lower(),
                                                L / 1000.0)
        if kind == 'bell':
            name = "Bell-cast roof - %.1f x %.1f m" % (v['bell_w'] / 1000.0, v['bell_d'] / 1000.0)
        self._timber = v['col_style'] == 'timber'
        nv = len(parts.get('Valance', []))
        if kind == 'island':
            self._val_names = ["Valance - side 1", "Valance - side 2"]
        elif nv == 3:
            self._val_names = ["Valance - front", "Valance - end 1", "Valance - end 2"]
        else:
            self._val_names = ["Valance - front"]
        nf = self.add_to_scene(dlg.viewport, name, parts)
        if nf is None:
            return
        msg = ("Built a %.1f m %s canopy, %.1f m %s: %d %s, %d valance boards, %d faces." % (
            L / 1000.0, dict(KINDS)[kind].split(" (")[0].lower(), info['depth'] / 1000.0,
            "wide" if kind == 'island' else "deep", info['columns'],
            "posts" if v['col_style'] == 'timber' else "columns", info['boards'], nf)) + note
        if kind == 'bell':
            msg = ("Built a %.1f x %.1f m bell-cast roof, %.1f m rise%s%s, %d faces." % (
                v['bell_w'] / 1000.0, v['bell_d'] / 1000.0, v['bell_h'] / 1000.0,
                (", %d lead rolls" % info['rolls']) if info.get('rolls') else "",
                (" on %d columns" % info['columns']) if info['columns'] else "", nf)) + note
        msg += ("\nOne group '%s', with a group for each part, and inside each a group for every "
                "piece, so you can explode any piece out to print it." % name)
        if self._errors[0]:
            msg += "\n%d faces could not be made: %s" % self._errors
        dlg.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if self._errors[0] else "#2e7d32"))
        dlg.lbl_report.setText(msg)

    def add_to_scene(self, viewport, name, parts):
        """One group for the canopy, holding a group for each kind of part (Columns, Brackets...),
        each holding one group per piece (Column 1, Column 2...), so any piece can be split
        off to print on its own."""
        stats = {'faces': 0, 'errors': 0, 'err': None}
        tol = 1e-4 * 0.001
        single = {'Columns': "Post" if self._timber else "Column", 'Brackets': "Bracket", 'Beams': "Beam",
                  'Roof': "Roof", 'Glass': "Glass", 'Valance': "Valance", 'Flashing': "Flashing"}

        def mesh_of(solids):
            from core.mesh import Mesh
            mesh = Mesh()
            verts = {}

            def vx(p):
                k = (round(p[0] / tol), round(p[1] / tol), round(p[2] / tol))
                if k not in verts:
                    verts[k] = VertexWrapper(*p)
                return verts[k]
            for so in solids:
                if not so:
                    continue
                for outer, holes in so:
                    try:
                        if holes:
                            hs = [[vx(p) for p in h] for h in holes]
                            try:
                                mesh.add_face([vx(p) for p in outer], hs)
                            except TypeError:          # an older IngeTrazo: holes one by one
                                f_ = mesh.add_face([vx(p) for p in outer])
                                for h in hs:
                                    mesh.add_hole(f_, h)
                        else:
                            mesh.add_face([vx(p) for p in outer])
                        stats['faces'] += 1
                    except Exception as e:
                        stats['errors'] += 1
                        stats['err'] = e
            return mesh

        def leaf(Group, mesh, nm):
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

        def holder(Group, nm, kids):
            g = Group(name=nm)
            if hasattr(g, 'adopt'):
                g.adopt(kids)
            else:
                g.children = kids
            g.component = False
            return g

        def mutate(scene):
            from core.group import Group
            cats = []
            for cat, items in parts.items():
                kids = []
                for i, it in enumerate(items):
                    nm = single.get(cat, cat) if len(items) == 1 else "%s %d" % (single.get(cat, cat), i + 1)
                    if cat == 'Valance' and self._val_names and len(self._val_names) == len(items):
                        nm = self._val_names[i]
                    kids.append(leaf(Group, mesh_of(it), nm))
                if len(kids) == 1 and cat in ('Roof', 'Glass', 'Flashing'):
                    cats.append(kids[0])
                else:
                    cats.append(holder(Group, "%s (%d)" % (cat, len(kids)), kids))
            if stats['faces'] == 0:
                raise RuntimeError("No faces could be made (%s)." % stats['err'])
            top = holder(Group, name, cats)
            scene.groups.append(top)
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
    StationCanopiesTool().on_activate(viewport)
