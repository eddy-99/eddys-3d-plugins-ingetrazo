# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Chimneys for IngeTrazo
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
3D Chimneys - brick chimney stacks, industrial chimneys and chimney pots for IngeTrazo
House stack: select a roof face (or the two faces either side of the ridge) and click
Build. The stack stands on the roof, every brick and its core cut exactly to the slope, in
bonded brickwork with oversailing courses at the top, a sloping mortar flaunching and a
row of chimney pots.
Industrial chimney: a tall mill, factory or engine-house chimney - square, octagonal or
round, tapered, with a plinth, bands, a corbelled cap and a coping - on a selected flat
face or at the origin.
Pots only: a row of chimney pots (plain, tapered, cannon, crown, square, octagonal) to
stand on a stack you've drawn.
Sizes are real-world mm; every part is a closed solid. Ctrl+Alt+H.
"""

import math
import os
import json
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QCheckBox,
                               QDoubleSpinBox, QSpinBox, QPushButton, QLabel, QMessageBox,
                               QTabWidget, QWidget)

PLUGIN_NAME = "3D Chimneys"
VERSION = "1"


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

SCALE = 0.001

# ---------------------------------------------------------------------------
# Geometry helpers (shared with Wood Planking and Wrap)
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



# ---------------------------------------------------------------------------
# Laying bricks (shared with 3D Wrap)
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
# Solids: a list of faces, each (outer loop, [hole loops]) in world metres
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


# ---------------------------------------------------------------------------
# The roof under a stack: one plane, or two meeting at a ridge (or in a valley)
# ---------------------------------------------------------------------------
class Roof:
    """planes: [(a, b, c)] with z = a*x + b*y + c. kind 'min' for a ridge (the roof is the
    lower of the planes), 'max' for a valley."""

    def __init__(self, planes, kind='min'):
        self.planes = list(planes)
        self.kind = kind

    def z(self, x, y):
        zs = [a * x + b * y + c for a, b, c in self.planes]
        return min(zs) if self.kind == 'min' else max(zs)


def _half(poly, a, b, c):
    """The part of a convex polygon where a*x + b*y + c >= 0."""
    if not poly:
        return None
    out = clip_half(poly, a, b, c)
    return clean(out) if len(out) >= 3 else None


def _on_seg(p, a, b, eps=1e-9):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    if L2 < 1e-24:
        return None
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2
    if t < -1e-9 or t > 1 + 1e-9:
        return None
    qx, qy = a[0] + t * dx, a[1] + t * dy
    if (qx - p[0]) ** 2 + (qy - p[1]) ** 2 > eps * eps * 1e6:
        return None
    return t


def _union(polys):
    """Outlines of the union of convex polygons that meet edge to edge (a partition)."""
    polys = [p for p in polys if p]
    if not polys:
        return []
    pts = [q for p in polys for q in p]
    key = lambda q: (round(q[0] * 1e7), round(q[1] * 1e7))
    edges = []
    for p in polys:
        n = len(p)
        for i in range(n):
            a, b = p[i], p[(i + 1) % n]
            # split at any other polygon's corner lying on this edge (no T-junctions)
            mids = []
            for q in pts:
                if key(q) in (key(a), key(b)):
                    continue
                t = _on_seg(q, a, b)
                if t is not None and 1e-9 < t < 1 - 1e-9:
                    mids.append((t, q))
            chain = [a] + [q for _, q in sorted(mids)] + [b]
            for u, w in zip(chain, chain[1:]):
                if key(u) != key(w):
                    edges.append((u, w))
    count = {}
    for u, w in edges:
        count[(key(u), key(w))] = count.get((key(u), key(w)), 0) + 1
    bound = [(u, w) for u, w in edges if (key(w), key(u)) not in count]
    nxt = {}
    for u, w in bound:
        nxt.setdefault(key(u), []).append((u, w))
    loops = []
    used = set()
    for u, w in bound:
        if (key(u), key(w)) in used:
            continue
        loop = [u]
        cu, cw = u, w
        guard = 0
        while guard < 10000:
            guard += 1
            used.add((key(cu), key(cw)))
            if key(cw) == key(loop[0]):
                break
            loop.append(cw)
            cand = [e for e in nxt.get(key(cw), []) if (key(e[0]), key(e[1])) not in used]
            if not cand:
                break
            cu, cw = cand[0]
        c = clean(loop)
        if c:
            loops.append(c)
    return loops


def roof_prism(foot, z0, z1, roof):
    """The part of an upright prism (convex plan `foot`, z0..z1) above a roof, as one closed
    solid per piece: its bottom follows the roof (several flat faces at a ridge), its top is
    one face. [] if it's all under the roof."""
    foot = clean(foot)
    if not foot:
        return []
    P = roof.planes
    f_at = [max(z0, roof.z(x, y)) for x, y in foot]
    if max(f_at) <= z0 + 1e-9:
        s = box_solid(foot, z0, z1)
        return [s] if s else []
    if min(roof.z(x, y) for x, y in foot) >= z1 - 1e-9:
        return []
    # regions where one plane is the roof (active), split where it is above or below z0
    regions = []        # (polygon, plane or None for flat z0)
    flats = []
    for k, (a, b, c) in enumerate(P):
        reg = foot
        for j, (a2, b2, c2) in enumerate(P):
            if j == k:
                continue
            # active: on a ridge the lower plane, in a valley the higher
            s_ = 1.0 if roof.kind == 'min' else -1.0
            reg = _half(reg, s_ * (a2 - a), s_ * (b2 - b), s_ * (c2 - c))
            if reg is None:
                break
        if reg is None:
            continue
        up = _half(reg, a, b, c - z0)                     # plane at or above z0
        if up is not None:
            up = _half(up, -a, -b, z1 - c)                # and not above the top
            if up is not None:
                regions.append((up, (a, b, c)))
        lo = _half(reg, -a, -b, z0 - c)                   # plane below z0: flat at z0
        if lo is not None:
            flats.append(lo)
    for fl in _union(flats):
        regions.append((fl, None))
    if not regions:
        return []

    def zf(pl, x, y):
        return z0 if pl is None else pl[0] * x + pl[1] * y + pl[2]
    tops = _union([r for r, _ in regions])
    # the pieces (more than one where the roof rises above the top in the middle)
    out = []
    for top in tops:
        mine = [(r, pl) for r, pl in regions if _pip_c(_centroid(r), top)]
        faces = [([(x, y, z1) for x, y in top], [])]
        for r, pl in mine:
            faces.append(([(x, y, zf(pl, x, y)) for x, y in reversed(r)], []))
        # walls along the outline's edges, wherever the solid has height
        n = len(top)
        allpts = [(q, pl) for r, pl in mine for q in r]
        for i in range(n):
            a, b = top[i], top[(i + 1) % n]
            onseg = []
            for q, pl in allpts:
                t = _on_seg(q, a, b)
                if t is not None:
                    onseg.append((t, q, zf(pl, q[0], q[1])))
            onseg.sort(key=lambda e: e[0])
            chain = []
            for t, q, z in onseg:
                if chain and abs(t - chain[-1][0]) < 1e-9:
                    continue
                chain.append((t, q, z))
            if len(chain) < 2:
                continue
            bot = [(q[0], q[1], z) for _, q, z in chain]
            if all(z1 - p[2] < 1e-9 for p in bot):
                continue                                   # a pinch: top meets bottom here
            wall = bot + [(b[0], b[1], z1), (a[0], a[1], z1)]
            wall = _clean3(wall)
            if wall and len(wall) >= 3:
                faces.append((wall, []))
        out.append(fixed(faces))
    return out


def _centroid(poly):
    return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))


def _pip_c(p, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[1] > p[1]) != (b[1] > p[1]):
            x = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x > p[0]:
                inside = not inside
    return inside


def _clean3(loop, eps=1e-9):
    out = []
    for p in loop:
        if not out or v_len(v_sub(p, out[-1])) > eps:
            out.append(p)
    while len(out) > 1 and v_len(v_sub(out[0], out[-1])) <= eps:
        out.pop()
    return out if len(out) >= 3 else None


def bricks_to_solids(faces6):
    """lay_bricks' output (6 faces a brick) as solids."""
    return [fixed([(f, []) for f in faces6[i:i + 6]]) for i in range(0, len(faces6), 6)]


def brick_above_roof(brick, roof):
    """A brick (one of lay_bricks', laid level) with whatever is under the roof cut away."""
    pts = [p for f, _ in brick for p in f]
    z0, z1 = min(p[2] for p in pts), max(p[2] for p in pts)
    top = [f for f, _ in brick if all(abs(p[2] - z1) < 1e-9 for p in f)]
    if not top:
        return [brick]
    foot = clean([(p[0], p[1]) for p in top[0]])
    if not foot:
        return [brick]
    if max(roof.z(x, y) for x, y in foot) <= z0 + 1e-9:
        return [brick]
    return roof_prism(foot, z0, z1, roof)


# ---------------------------------------------------------------------------
# Turned (lathe) solids: chimney pots, round coping
# ---------------------------------------------------------------------------
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


POT_STYLES = [("plain", "Plain"), ("tapered", "Tapered"), ("cannon", "Cannon (roll top)"),
              ("crown", "Crown (castellated)"), ("square", "Square"), ("octagon", "Octagonal")]


def pot_profile(style, height, dia, wall):
    """A pot's turned profile [(r, z)] (outside up, over the rim, down the bore), and how many
    sides it is turned with: (profile, sides, turn)."""
    R = dia / 2.0
    H = height
    w = max(wall, 0.002)
    bore = H * 0.55                                        # how far down the hole goes
    seg, rot = 24, 0.0
    if style == 'square':
        seg, rot = 4, math.pi / 4
        R = R * math.sqrt(2)
    elif style == 'octagon':
        seg, rot = 8, math.pi / 8
        R = R / math.cos(math.pi / 8)
    if style in ('plain', 'square', 'octagon', 'crown'):
        rt = R * 0.92                                      # a slight taper
        prof = [(0, 0), (R * 1.08, 0), (R * 1.08, H * 0.06), (R, H * 0.08), (rt, H * 0.88),
                (rt * 1.06, H * 0.9), (rt * 1.06, H), (rt - w, H), (rt - w, H - bore), (0, H - bore)]
    elif style == 'tapered':
        rt = R * 0.62
        prof = [(0, 0), (R, 0), (rt, H * 0.92), (rt * 1.1, H * 0.94), (rt * 1.1, H), (rt - w, H),
                (rt - w, H - bore), (0, H - bore)]
    else:                                                  # cannon: waist and a rolled top
        rw = R * 0.72
        prof = [(0, 0), (R, 0), (R, H * 0.1), (rw, H * 0.35), (rw, H * 0.8), (rw * 1.12, H * 0.84),
                (rw * 1.18, H * 0.9), (rw * 1.12, H * 0.96), (rw * 1.04, H), (rw - w, H),
                (rw - w, H - bore), (0, H - bore)]
    return prof, seg, rot


def pot_solids(style, cx, cy, z0, height, dia, wall):
    """One chimney pot standing at (cx, cy, z0): [solids]."""
    prof, seg, rot = pot_profile(style, height, dia, wall)
    H = height
    w = max(wall, 0.002)
    R = dia / 2.0
    if style == 'square':
        R = R * math.sqrt(2)
    elif style == 'octagon':
        R = R / math.cos(math.pi / 8)
    out = [lathe(prof, cx, cy, z0, seg, rot)]
    if style == 'crown':
        # castellations round the rim: little blocks standing on it (sunk in a hair)
        rt = R * 0.92 * 1.06
        n = 6
        bw = 2 * math.pi * (rt - w / 2) / (2 * n)
        hh = H * 0.1
        for k in range(n):
            a = 2 * math.pi * k / n
            c_, s_ = math.cos(a), math.sin(a)
            u, vv = (-s_, c_), (c_, s_)
            r0, r1 = rt - w * 0.9, rt
            foot = [(cx + vv[0] * r0 - u[0] * bw / 2, cy + vv[1] * r0 - u[1] * bw / 2),
                    (cx + vv[0] * r1 - u[0] * bw / 2, cy + vv[1] * r1 - u[1] * bw / 2),
                    (cx + vv[0] * r1 + u[0] * bw / 2, cy + vv[1] * r1 + u[1] * bw / 2),
                    (cx + vv[0] * r0 + u[0] * bw / 2, cy + vv[1] * r0 + u[1] * bw / 2)]
            b = box_solid(foot, z0 + H - 0.0005, z0 + H + hh)
            if b:
                out.append(b)
    return out


def frustum(bot, z0, top, z1):
    """A solid from a convex outline at z0 to another (same number of corners) at z1."""
    bot, top = clean(bot), clean(top)
    if not bot or not top or len(bot) != len(top):
        return None
    n = len(bot)
    faces = [([(x, y, z1) for x, y in top], []), ([(x, y, z0) for x, y in reversed(bot)], [])]
    for i in range(n):
        j = (i + 1) % n
        faces.append(([(bot[i][0], bot[i][1], z0), (bot[j][0], bot[j][1], z0),
                       (top[j][0], top[j][1], z1), (top[i][0], top[i][1], z1)], []))
    return fixed(faces)


# ---------------------------------------------------------------------------
# Targets for the brick layer
# ---------------------------------------------------------------------------
class RectTarget:
    """A rectangular stack (plan half-sizes hx along `ang`, hy across), for lay_bricks."""

    def __init__(self, cx, cy, ang, hx, hy, z0, h):
        self.cx, self.cy, self.ang, self.hx, self.hy, self.z0, self.h = cx, cy, ang, hx, hy, z0, h

    def r(self, th, z):
        t = th - self.ang
        c, s = abs(math.cos(t)), abs(math.sin(t))
        return min(self.hx / c if c > 1e-12 else 1e18, self.hy / s if s > 1e-12 else 1e18)

    def corners(self):
        a = math.atan2(self.hy, self.hx)
        return sorted((self.ang + x) % (2 * math.pi) for x in (a, math.pi - a, math.pi + a, 2 * math.pi - a))

    def outline(self, grow=0.0):
        ca, sa = math.cos(self.ang), math.sin(self.ang)
        hx, hy = self.hx + grow, self.hy + grow
        return [(self.cx + ca * x - sa * y, self.cy + sa * x + ca * y)
                for x, y in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))]


def brick_v(v, n_courses, extra=None):
    """The settings lay_bricks wants, for exactly n courses from the target's foot."""
    return dict(brick_l=v['brick_l'], brick_h=v['brick_h'], brick_d=v['brick_d'], joint=v['joint'],
                lift=0.01, header_every=0, lay_h=0.0, start=0.0, level=v.get('level', True),
                extra_depth=extra, **{'raise': 0.0})


# ---------------------------------------------------------------------------
# House stack
# ---------------------------------------------------------------------------
def roof_from_faces(polys):
    """The roof from one or two picked faces (world metres): (Roof, frame) where frame holds
    the ridge (or top edge) direction, the up-slope direction and the faces' extent."""
    planes = []
    for pts in polys:
        n = _newell(pts)
        if n[2] < 0:
            n = (-n[0], -n[1], -n[2])
        if n[2] < 0.05:
            raise ValueError("Pick roof faces: a face that slopes, not an upright wall.")
        c = pts[0]
        d = v_dot(n, c)
        planes.append((-n[0] / n[2], -n[1] / n[2], d / n[2]))
    if len(polys) == 1:
        roof = Roof(planes)
        a, b, _ = planes[0]
        up = (-a, -b)                                   # uphill, in plan
        L = math.hypot(*up)
        if L < 1e-9:
            along, up = (1.0, 0.0), (0.0, 1.0)          # a flat roof
        else:
            up = (up[0] / L, up[1] / L)
            along = (up[1], -up[0])
        return roof, {'along': along, 'up': up, 'pts': polys[0], 'ridge': None}
    # two faces: they should share an edge (the ridge, or a valley)
    key = lambda p: (round(p[0], 5), round(p[1], 5), round(p[2], 5))
    common = [p for p in polys[0] if key(p) in {key(q) for q in polys[1]}]
    if len(common) < 2:
        raise ValueError("The two roof faces don't meet: pick the two faces either side of the ridge.")
    a0, a1 = common[0], common[-1]
    if v_len(v_sub(a1, a0)) < 1e-6 and len(common) > 2:
        a1 = common[1]
    c0 = _centroid([(p[0], p[1]) for p in polys[0]])
    z_c0 = sum(p[2] for p in polys[0]) / len(polys[0])
    p2 = planes[1]
    kind = 'min' if z_c0 <= p2[0] * c0[0] + p2[1] * c0[1] + p2[2] + 1e-9 else 'max'
    roof = Roof(planes, kind)
    d = (a1[0] - a0[0], a1[1] - a0[1])
    L = math.hypot(*d) or 1.0
    along = (d[0] / L, d[1] / L)
    return roof, {'along': along, 'up': (-along[1], along[0]), 'pts': polys[0] + polys[1],
                  'ridge': (a0, a1)}


def stack_size(v):
    """The stack's size (mm) once widened to take the pots, and the pots' rows: (W, D, rows,
    per_row, widened)."""
    W, Dp = v['width'], v['depth']
    npots = int(v['pots'])
    rows = max(1, min(2, int(v.get('pot_rows', 1)))) if npots > 1 else 1
    per_row = int(math.ceil(npots / float(rows))) if npots else 0
    pot_d = v['pot_dia']
    foot, gap, edge = pot_d * 1.12, max(50.0, pot_d * 0.25), max(60.0, pot_d * 0.25)
    widened = False
    if npots and v.get('fit_pots', True):
        half_unit = (v['brick_l'] + v['joint']) / 2.0
        need_w = per_row * foot + (per_row - 1) * gap + 2 * edge
        need_d = rows * foot + (rows - 1) * gap + 2 * edge
        if need_w > W + 1e-6:
            W, widened = math.ceil(need_w / half_unit - 1e-9) * half_unit, True
        if need_d > Dp + 1e-6:
            Dp, widened = math.ceil(need_d / half_unit - 1e-9) * half_unit, True
    return W, Dp, rows, per_row, widened


def house_stack(v, roof, frame):
    """All the parts of a house chimney stack: {group name: [solids]}, and a report."""
    S = SCALE
    # the stack's size, made big enough for the pots, and the pots' rows
    Wmm, Dmm, rows, per_row, widened = stack_size(v)
    W, Dp = Wmm * S, Dmm * S
    npots = int(v['pots'])
    pot_d = v['pot_dia'] * S
    foot = pot_d * 1.12
    gap = max(0.05, pot_d * 0.25)
    bd = v['brick_d'] * S
    H, J = v['brick_h'] * S, v['joint'] * S
    course = H + J
    along = frame['along']
    ang = math.atan2(along[1], along[0])
    # where it stands: on the ridge (two faces) or on the face, by the fractions given
    if frame['ridge'] is not None:
        a0, a1 = frame['ridge']
        t = v['along'] / 100.0
        cx, cy = a0[0] + (a1[0] - a0[0]) * t, a0[1] + (a1[1] - a0[1]) * t
    else:
        pts = frame['pts']
        up = frame['up']
        us = [p[0] * along[0] + p[1] * along[1] for p in pts]
        ss = [p[0] * up[0] + p[1] * up[1] for p in pts]
        u = min(us) + W / 2 + (max(us) - min(us) - W) * v['along'] / 100.0
        s_lo, s_hi = min(ss) + Dp / 2, max(ss) - Dp / 2
        s = s_lo + (s_hi - s_lo) * v['up'] / 100.0 if s_hi > s_lo else (min(ss) + max(ss)) / 2
        cx, cy = along[0] * u + up[0] * s, along[1] * u + up[1] * s
    # the core inside the brick skin
    hx, hy = W / 2 - bd, Dp / 2 - bd
    if hx <= 0.01 or hy <= 0.01:
        raise ValueError("The stack is too small for the bricks: make it at least two bricks deep.")
    outer = RectTarget(cx, cy, ang, W / 2, Dp / 2, 0, 1).outline()
    lows = [roof.z(x, y) for x, y in outer]
    z_low, z_high = min(lows), max(lows)
    # the roof may rise higher inside the footprint (a ridge under the middle of the stack)
    for k in range(1, 8):
        for (x0, y0), (x1, y1) in zip(outer, outer[1:] + outer[:1]):
            t = k / 8.0
            z_high = max(z_high, roof.z(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    z_high = max(z_high, roof.z(cx, cy))
    z_start = z_low - course                            # start under the roof, cut to it
    top_wanted = z_high + v['height'] * S
    n_courses = max(2, int(math.ceil((top_wanted - z_start) / course - 1e-9)))
    n_over = max(0, min(int(v['oversail']), n_courses - 1))
    proj = v['oversail_out'] * S
    first_over = n_courses - n_over

    def extra(c_, z_):
        return proj * (c_ - first_over + 1) if c_ >= first_over else 0.0
    tgt = RectTarget(cx, cy, ang, hx, hy, z_start, n_courses * course)
    faces6, info = lay_bricks(tgt, brick_v(v, n_courses, extra))
    bricks = []
    for b in bricks_to_solids(faces6):
        bricks += brick_above_roof(b, roof)
    z_top = z_start + n_courses * course - J            # top of the last course
    core = roof_prism(tgt.outline(), z_start - 1.0, z_top, roof)
    parts = {'Bricks': bricks, 'Core': core}
    # flaunching: a sloping mortar cap, from just in from the edge up round the pots
    out_half = bd + proj * n_over
    fl_h = v['flaunch'] * S
    rect_out = RectTarget(cx, cy, ang, hx + out_half - 0.01, hy + out_half - 0.01, 0, 1)
    spread = W / max(1, per_row)
    row_off = (foot + gap) / 2.0 if rows == 2 else 0.0
    if fl_h > 0:
        ix = max(pot_d * 0.75, min(hx + out_half - 0.02, (per_row - 1) * spread / 2 + pot_d * 0.75)) \
            if npots else (hx + out_half) * 0.5
        iy = max(0.02, min(hy + out_half - 0.02, row_off + pot_d * 0.75)) if npots else (hy + out_half) * 0.5
        rect_in = RectTarget(cx, cy, ang, ix, iy, 0, 1)
        fl = frustum(rect_out.outline(), z_top - 0.0005, rect_in.outline(), z_top + fl_h)
        parts['Flaunching'] = [fl] if fl else []
    # the pots, in a row (or two) along the stack, sunk a little into the flaunching
    pots = []
    across = (-along[1], along[0])
    if npots:
        k_ = 0
        for r in range(rows):
            n_r = min(per_row, npots - r * per_row)
            off = (r - (rows - 1) / 2.0) * 2 * row_off
            sp = W / max(1, n_r) if n_r < per_row else spread
            for k in range(n_r):
                u = -sp * n_r / 2.0 + sp * (k + 0.5)
                px = cx + along[0] * u + across[0] * off
                py = cy + along[1] * u + across[1] * off
                pots += pot_solids(v['pot_style'], px, py, z_top + max(0.0, fl_h * 0.6),
                                   v['pot_h'] * S, pot_d, v['pot_wall'] * S)
                k_ += 1
        parts['Pots'] = pots
    rep = {'bricks': len(bricks), 'courses': n_courses, 'above': (z_top - z_high) / S,
           'oversail': n_over, 'width': W / S, 'depth': Dp / S, 'widened': widened, 'rows': rows}
    return parts, rep


# ---------------------------------------------------------------------------
# Industrial (mill / factory / engine-house) chimney
# ---------------------------------------------------------------------------
IND_SHAPES = [("square", "Square"), ("octagon", "Octagonal"), ("round", "Round")]


def industrial(v, cx, cy, z0):
    S = SCALE
    H, J = v['brick_h'] * S, v['joint'] * S
    course = H + J
    bd = v['brick_d'] * S
    total = v['ind_height'] * S
    n_courses = max(4, int(round(total / course)))
    shape = v['ind_shape']
    # the target is the core: the bricks stand outside it, so the sizes given are overall
    rb = v['ind_bottom'] * S / 2.0 - bd
    rt = v['ind_top'] * S / 2.0 - bd
    if rt <= 0.02 or rb <= 0.02:
        raise ValueError("The chimney is too small for the bricks.")
    tgt = ShapeTarget(shape, cx, cy, z0, n_courses * course, 2 * rb, 2 * rt)
    n_plinth = int(round(v['plinth_h'] * S / course)) if v['plinth_h'] > 0 else 0
    p_out = v['plinth_out'] * S
    band_every = v['band_every'] * S
    band_c = max(1, int(v['band_courses']))
    b_out = v['band_out'] * S
    n_cap = max(0, int(v['cap_courses']))
    c_out = v['cap_out'] * S
    first_cap = n_courses - n_cap
    every_c = int(round(band_every / course)) if band_every > 0 else 0

    def extra(c_, z_):
        if c_ < n_plinth:
            return p_out
        if c_ >= first_cap:
            return c_out * (c_ - first_cap + 1)
        if every_c > 0 and c_ > n_plinth + 2:
            k = (c_ - n_plinth) % every_c
            if k < band_c and c_ < first_cap - 3:
                return b_out
        return 0.0
    faces6, info = lay_bricks(tgt, brick_v(v, n_courses, extra))
    bricks = bricks_to_solids(faces6)
    z_top = z0 + n_courses * course - J
    core_faces = tgt.solid_faces()
    core = fixed([(f, []) for f in core_faces])
    # the core stops at the top course
    parts = {'Bricks': bricks, 'Core': [core]}
    cop_h = v['coping_h'] * S
    if cop_h > 0:
        r_out = rt + bd + c_out * n_cap + v['coping_over'] * S
        r_in = max(0.02, rt * 0.6)
        seg, rot, kf = 32, 0.0, 1.0
        if shape == 'square':
            seg, rot, kf = 4, math.pi / 4, math.sqrt(2)
        elif shape == 'octagon':
            seg, rot, kf = 8, math.pi / 8, 1.0 / math.cos(math.pi / 8)
        prof = [(r_in * kf, 0), (r_out * kf, 0), (r_out * kf, cop_h), (r_in * kf, cop_h)]
        parts['Coping'] = [lathe(prof, cx, cy, z_top - 0.0005, seg, rot)]
    return parts, {'bricks': len(bricks), 'courses': n_courses, 'height': (z_top + cop_h - z0)}


def pots_only(v, cx, cy, z0, along=(1.0, 0.0)):
    S = SCALE
    n = max(1, int(v['pots']))
    gap = v['pot_dia'] * S * 1.25
    out = []
    for k in range(n):
        u = (k - (n - 1) / 2.0) * gap
        out += pot_solids(v['pot_style'], cx + along[0] * u, cy + along[1] * u, z0 - 0.005,
                          v['pot_h'] * S + 0.005, v['pot_dia'] * S, v['pot_wall'] * S)
    return {'Pots': out}, {'pots': n}


# ---------------------------------------------------------------------------
# Roof ventilators: Charles Doig's pagoda ventilator on a distillery kiln, or a plain louvred
# roof vent; and weather vanes. Built in local mm (x along, y across, z up), then placed.
# ---------------------------------------------------------------------------
VENT_STYLES = [("doig", "Doig pagoda (distillery kiln)"), ("pyramid", "Louvred, pyramid cap")]
VANE_STYLES = [("arrow", "Arrow"), ("banner", "Banner")]


def sweep_rings(hx0, hy0, hx1, hy1, H, sweep, n, reach=0.25):
    """Level rectangles [(half x, half y, z)] from (hx0, hy0) at z = 0 to (hx1, hy1) at z = H:
    a straight steep slope that kicks out flatter at the eaves (the pagoda look). sweep 0 = a
    straight pyramid; reach = how far up the kick runs (a fraction of the way)."""
    a = 0.92 * max(0.0, min(1.0, sweep))
    tau = max(0.05, reach)
    norm = 1.0 - a * tau * (1.0 - math.exp(-1.0 / tau))
    out = []
    for i in range(n + 1):
        t = i / float(n)
        # the slope grows from (1 - a) at the eaves to full a little way up
        f = (t - a * tau * (1.0 - math.exp(-t / tau))) / norm
        out.append((hx0 + (hx1 - hx0) * t, hy0 + (hy1 - hy0) * t, H * f))
    return out


def ring_stack(rings, z0=0.0):
    """A closed solid through a stack of level rectangles [(hx, hy, z)] centred on the axis."""
    def R(hx, hy, z):
        return [(-hx, -hy, z0 + z), (hx, -hy, z0 + z), (hx, hy, z0 + z), (-hx, hy, z0 + z)]
    faces = [(list(reversed(R(*rings[0]))), []), (R(*rings[-1]), [])]
    for a, b in zip(rings, rings[1:]):
        if abs(a[2] - b[2]) < 1e-9 and abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9:
            continue
        ra, rb = R(*a), R(*b)
        for i in range(4):
            j = (i + 1) % 4
            faces.append(([ra[i], ra[j], rb[j], rb[i]], []))
    return fixed(faces)


def box3(x0, x1, y0, y1, z0, z1):
    return box_solid([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1)


def prism(poly, O, U, V, N, t):
    """A flat plate: poly [(u, w)] in the plane O + u*U + w*V, t thick along N (centred)."""
    poly = clean(poly)
    if not poly or t <= 0:
        return None
    if area2(poly) < 0:
        poly = list(reversed(poly))

    def P(u, w, s):
        return tuple(O[i] + U[i] * u + V[i] * w + N[i] * s for i in range(3))
    a = [P(u, w, -t / 2.0) for u, w in poly]
    b = [P(u, w, t / 2.0) for u, w in poly]
    faces = [(list(reversed(a)), []), (b, [])]
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        faces.append(([a[i], a[j], b[j], b[i]], []))
    return fixed(faces)


def _meet(p1, p2, p3, p4):
    """Where line p1-p2 crosses line p3-p4."""
    d = (p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0])
    if abs(d) < 1e-12:
        return p2
    t = ((p3[0] - p1[0]) * (p4[1] - p3[1]) - (p3[1] - p1[1]) * (p4[0] - p3[0])) / d
    return (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)


def letter_outline(ch, w, h, s):
    """A block capital N, E, S or W as one outline [(u, z)], w wide, h tall, strokes s thick."""
    s = min(s, w * 0.3, h * 0.2)
    if ch == 'N':
        d = min(h * 0.4, s * 1.6)
        return [(0, 0), (s, 0), (s, h - d), (w - s, 0), (w, 0), (w, h), (w - s, h), (w - s, d), (s, h), (0, h)]
    if ch == 'E':
        m0, m1 = h / 2 - s / 2, h / 2 + s / 2
        return [(0, 0), (w, 0), (w, s), (s, s), (s, m0), (w * 0.8, m0), (w * 0.8, m1), (s, m1), (s, h - s),
                (w, h - s), (w, h), (0, h)]
    if ch == 'S':
        m0, m1 = h / 2 - s / 2, h / 2 + s / 2
        return [(0, 0), (w, 0), (w, m1), (s, m1), (s, h - s), (w, h - s), (w, h), (0, h), (0, m0), (w - s, m0),
                (w - s, s), (0, s)]
    # W: four strokes
    a, sw, pk = w * 0.18, s * 1.15, h * 0.7
    c0, c1 = (w / 2 - sw / 2, pk), (w / 2 + sw / 2, pk)
    X = _meet((a + sw, 0), c1, c0, (w - a - sw, 0))
    Y = _meet((w - sw, h), (w - a - sw, 0), c1, (w - a, 0))
    Z = _meet((a, 0), c0, (sw, h), (a + sw, 0))
    return [(0, h), (a, 0), (a + sw, 0), X, (w - a - sw, 0), (w - a, 0), (w, h), (w - sw, h), Y, c1, c0, Z,
            (sw, h)]


def ball_arc(r_from, r_ball, zc, r_to, n=8):
    """Points round a ball (centre on the axis at zc) from where it is r_from across below the
    middle to where it is r_to across above it (0 = the very top). [(r, z)]."""
    a_lo = -math.acos(max(0.0, min(0.999, r_from / r_ball)))
    a_hi = math.acos(max(0.0, min(1.0, r_to / r_ball)))
    return [(r_ball * math.cos(a_lo + (a_hi - a_lo) * k / n), zc + r_ball * math.sin(a_lo + (a_hi - a_lo) * k / n))
            for k in range(n + 1)]


def ball_profile(r_neck, r_ball, h_neck, r_top, n=8):
    """A turned finial: a neck, then a ball, ending flat r_top across (0 = round top).
    Returns ([(r, z)], height)."""
    r_ball = max(r_ball, r_neck * 1.2)
    zc = h_neck + math.sqrt(r_ball ** 2 - r_neck ** 2)
    arc = ball_arc(r_neck, r_ball, zc, r_top, n)
    prof = [(0.0, 0.0), (r_neck, 0.0)] + arc
    top = arc[-1][1]
    if arc[-1][0] > 1e-6:
        prof.append((0.0, top))
    else:
        prof[-1] = (0.0, top)
    return prof, top


def vane_parts(v, z0=0.0, base_plate=False):
    """A weather vane on an upright rod standing at (0, 0, z0), local mm: [solids], height."""
    rr = max(10.0, v['vane_rod']) / 2.0
    H = max(300.0, v['vane_h'])
    L = max(200.0, v['vane_len'])
    t = max(8.0, v['vane_t'])
    out = []
    z = z0
    if base_plate:
        bp = max(4 * rr, 150.0)
        out.append(box3(-bp / 2, bp / 2, -bp / 2, bp / 2, z, z + t))
        z += t
    # the cardinal arms, with N E S W on their ends, about 40 % of the way up
    zc = z + H * 0.4
    al = max(rr * 3, v['vane_arms'] / 2.0)
    aw = max(t, rr * 1.0)
    # the rod up to the arms, with a ball on it half way
    br = rr * 2.2
    zb = z + (zc - z) * 0.5
    nb = 8
    prof = [(0.0, z), (rr, z)] + ball_arc(rr, br, zb, rr, nb) + [(rr, zc), (0.0, zc)]
    prof = [(r_, z_ - z) for r_, z_ in prof]
    out.append(lathe(prof, 0.0, 0.0, z, 16))
    arms = [(-al, -aw / 2), (-aw / 2, -aw / 2), (-aw / 2, -al), (aw / 2, -al), (aw / 2, -aw / 2), (al, -aw / 2),
            (al, aw / 2), (aw / 2, aw / 2), (aw / 2, al), (-aw / 2, al), (-aw / 2, aw / 2), (-al, aw / 2)]
    out.append(prism(arms, (0.0, 0.0, zc + t / 2), (1, 0, 0), (0, 1, 0), (0, 0, 1), t))
    if v.get('vane_letters', True):
        lh = max(60.0, v['vane_letter'])
        lw = lh * 0.8
        ls = max(t, lh * 0.16)
        zl = zc + t
        # each letter stands on its arm's end, in the arm's own upright plane
        for ch, O, U, N in (('E', (al - lw, 0.0, zl), (1, 0, 0), (0, 1, 0)),
                            ('W', (-al, 0.0, zl), (1, 0, 0), (0, 1, 0)),
                            ('N', (0.0, al - lw, zl), (0, 1, 0), (1, 0, 0)),
                            ('S', (0.0, -al, zl), (0, 1, 0), (1, 0, 0))):
            out.append(prism(letter_outline(ch, lw, lh, ls), O, U, (0, 0, 1), N, aw))
    # the rod on up through the pointer to a spike
    za = z + H
    sh = max(t * 2, v['vane_len'] * 0.08)
    zt = za + sh + rr * 4
    out.append(lathe([(0.0, 0.0), (rr, 0.0), (rr, zt - zc - t - rr * 2), (0.0, zt - zc - t)],
                     0.0, 0.0, zc + t, 16))
    # the pointer, turning on the rod: an arrow, or a banner with an arrow-head
    cz = sh / 2
    if v['vane_style'] == 'banner':
        bh = sh * 3.0
        hl, hh = L * 0.25, bh * 0.6
        cz = bh / 2
        poly = [(-hl, cz), (0, cz - hh / 2), (0, 0), (L, 0), (L - bh * 0.4, cz), (L, bh), (0, bh), (0, cz + hh / 2)]
        sft = -(L - hl) / 2.0
        poly = [(u + sft, w) for u, w in poly]
        zp = za - bh / 2 + sh / 2
    else:
        a_, d_ = -L / 2, L / 2
        tl, hl = L * 0.22, L * 0.18
        th, hh = sh * 3.2, sh * 2.6
        poly = [(a_ + tl * 0.45, cz), (a_, cz - th / 2), (a_ + tl, 0), (d_ - hl, 0), (d_ - hl, cz - hh / 2), (d_, cz),
                (d_ - hl, cz + hh / 2), (d_ - hl, sh), (a_ + tl, sh), (a_, cz + th / 2)]
        zp = za
    out.append(prism(poly, (0.0, 0.0, zp), (1, 0, 0), (0, 0, 1), (0, 1, 0), t))
    return [s_ for s_ in out if s_], zt - z0


def vent_parts(v, kiln=None, kerb=True):
    """The ventilator in local mm, its foot (the kerb's underside) at z = 0, or the kiln
    roof's eaves at z = 0 if kiln = (width, depth). Returns ({part: [solids]}, info)."""
    parts = {}
    vw = max(300.0, v['vent_w'])
    c = vw / 2.0
    z = 0.0
    if kiln:
        KW, KD = kiln
        kh = max(500.0, v['kiln_h'])
        et = max(20.0, v['kiln_eave'])
        top = c + max(0.0, v['kiln_top'])
        if top * 2 >= min(KW, KD) - 1.0:
            raise ValueError("The ventilator is too big for the kiln roof.")
        n = max(6, int(v.get('segments', 16)))
        rings = [(KW / 2, KD / 2, 0.0)] + [(hx, hy, et + z_) for hx, hy, z_ in
                                          sweep_rings(KW / 2, KD / 2, top, top, kh, v['kiln_sweep'] / 100.0, n)]
        parts['Kiln roof'] = [ring_stack(rings)]
        z = et + kh
    vent = []
    kb = max(0.0, v['vent_kerb'])
    if kerb and kb > 0:
        vent.append(box3(-c, c, -c, c, z, z + kb))
        z += kb
    vh = max(200.0, v['vent_h'])
    ld = max(20.0, min(c * 0.4, v['louvre_d']))
    lt = max(8.0, v['louvre_t'])
    nl = max(1, int(v['louvres']))
    ci = c - ld
    # the dark core behind the louvres, and a post at each corner
    vent.append(box3(-ci, ci, -ci, ci, z, z + vh))
    for sx in (-1, 1):
        for sy in (-1, 1):
            xa, xb = sorted((sx * ci, sx * c))
            ya, yb = sorted((sy * ci, sy * c))
            vent.append(box3(xa, xb, ya, yb, z, z + vh))
    # the louvre boards on each side, sloping down and out, between the posts
    p = vh / nl
    dr = max(0.0, min(ld * 0.9, p - lt - 1.0))
    for side in range(4):
        ang = side * math.pi / 2
        n_ = (math.cos(ang), math.sin(ang), 0.0)
        u_ = (-math.sin(ang), math.cos(ang), 0.0)
        for k in range(nl):
            zk = z + p * k
            sec = [(0.0, zk + dr), (ld, zk), (ld, zk + lt), (0.0, zk + dr + lt)]
            O = (n_[0] * ci, n_[1] * ci, 0.0)
            vent.append(prism(sec, (O[0], O[1], 0.0), n_, (0, 0, 1), u_, 2 * ci))
    parts['Ventilator'] = [s_ for s_ in vent if s_]
    z += vh
    # the cap: flared pagoda eaves (Doig) or a plain pyramid, then a finial
    co = max(0.0, v['cap_over'])
    ct = max(20.0, v['cap_t'])
    chh = max(100.0, v['cap_h'])
    sweep = v['cap_sweep'] / 100.0 if v['vent_style'] == 'doig' else 0.0
    fr = max(20.0, v['finial'] * 0.25)
    rr = max(10.0, v['vane_rod']) / 2.0
    tr = max(fr * 0.6, rr * 1.2)
    n = max(6, int(v.get('segments', 16)))
    rings = [(c + co, c + co, 0.0)] + [(hx, hy, ct + z_) for hx, hy, z_ in
                                      sweep_rings(c + co, c + co, tr, tr, chh, sweep, n, 0.35)]
    cap = [ring_stack(rings, z)]
    z += ct + chh
    fh = max(0.0, v['finial'])
    if fh > 0:
        prof, top = ball_profile(tr * 0.9, max(fr, fh * 0.3), fh * 0.25, rr * 1.05 if v.get('vane') else 0.0)
        cap.append(lathe(prof, 0.0, 0.0, z, 16))
        z += top
    parts['Cap'] = [s_ for s_ in cap if s_]
    vh_ = 0.0
    if v.get('vane'):
        vs, vh_ = vane_parts(v, z)
        parts['Weather vane'] = vs
    return parts, {'height': z + vh_, 'louvres': nl * 4, 'width': vw}


def place_parts(parts, cx, cy, z0, along):
    """Local mm parts (x along, y across, z up) to the scene: turned to `along`, at (cx, cy, z0) m."""
    ax, ay = along
    S = SCALE

    def f(p):
        return (cx + (p[0] * ax - p[1] * ay) * S, cy + (p[0] * ay + p[1] * ax) * S, z0 + p[2] * S)
    return {k: [[([f(q) for q in o], [[f(q) for q in h] for h in hs]) for o, hs in so] for so in sols]
            for k, sols in parts.items()}


def vent_on_roof(v, roof, frame):
    """A ventilator standing on a roof face, or astride the ridge of two: its kerb cut to the
    roof. Returns (parts, info)."""
    S = SCALE
    along = frame['along']
    if frame['ridge'] is not None:
        a0, a1 = frame['ridge']
        t = v['vent_along'] / 100.0
        cx, cy = a0[0] + (a1[0] - a0[0]) * t, a0[1] + (a1[1] - a0[1]) * t
    else:
        pts = frame['pts']
        cx, cy = _centroid([(p[0], p[1]) for p in pts])
    c = v['vent_w'] / 2.0 * S
    ax, ay = along
    foot = [(cx + u * ax - w * ay, cy + u * ay + w * ax) for u, w in ((-c, -c), (c, -c), (c, c), (-c, c))]
    zs = [roof.z(cx, cy)]
    for (x0, y0), (x1, y1) in zip(foot, foot[1:] + foot[:1]):
        for k in range(8):
            t = k / 8.0
            zs.append(roof.z(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    z_low, z_high = min(zs), max(zs)
    zk = z_high + max(50.0, v['vent_kerb']) * S
    kerb = roof_prism(foot, z_low - 1.0, zk, roof)
    parts, info = vent_parts(v, None, kerb=False)
    parts = place_parts(parts, cx, cy, zk, along)
    parts['Ventilator'] = kerb + parts['Ventilator']
    info['height'] += (zk - z_low) / S
    return parts, info


# ---------------------------------------------------------------------------
# Settings and presets
# ---------------------------------------------------------------------------
KINDS = [("house", "House stack on a roof"), ("industrial", "Industrial chimney"), ("pots", "Chimney pots only"),
         ("vent", "Roof vent / Doig ventilator"), ("vane", "Weather vane only")]

DEFAULTS = dict(kind='house', width=900.0, depth=450.0, height=900.0, along=50.0, up=100.0,
                oversail=2, oversail_out=28.0, flaunch=60.0,
                pots=2, pot_rows=1, fit_pots=True, pot_style='plain', pot_h=600.0, pot_dia=240.0, pot_wall=32.0,
                brick_l=215.0, brick_h=65.0, brick_d=102.5, joint=10.0, level=True,
                ind_shape='square', ind_bottom=2400.0, ind_top=1400.0, ind_height=18000.0,
                plinth_h=2000.0, plinth_out=56.0, band_every=6000.0, band_courses=2, band_out=56.0,
                cap_courses=4, cap_out=28.0, coping_h=150.0, coping_over=40.0,
                vent_style='doig', kiln=True, kiln_fit=False, vent_w=2400.0, vent_h=1600.0, louvres=6,
                louvre_d=150.0, louvre_t=40.0, vent_kerb=200.0, cap_h=1600.0, cap_over=500.0, cap_sweep=80.0,
                cap_t=100.0, finial=500.0, vent_along=50.0,
                kiln_w=7000.0, kiln_d=7000.0, kiln_h=6000.0, kiln_sweep=60.0, kiln_eave=150.0, kiln_top=150.0,
                vane=True, vane_style='arrow', vane_letters=True, vane_h=1500.0, vane_len=1000.0, vane_t=30.0,
                vane_rod=40.0, vane_arms=900.0, vane_letter=250.0)

PRESETS = [
    ("Cottage stack, 2 pots", dict(kind='house', width=900.0, depth=450.0, height=900.0, oversail=2,
                                   pots=2, pot_style='plain', pot_h=600.0)),
    ("Terrace party-wall stack, 4 pots", dict(kind='house', width=1350.0, depth=450.0, height=1000.0,
                                              oversail=3, pots=4, pot_style='tapered', pot_h=750.0)),
    ("Victorian villa stack, crown pots", dict(kind='house', width=1125.0, depth=560.0, height=1200.0,
                                               oversail=3, oversail_out=40.0, pots=3, pot_style='crown',
                                               pot_h=900.0, pot_dia=280.0)),
    ("Small single-flue stack", dict(kind='house', width=560.0, depth=450.0, height=700.0, oversail=1,
                                     pots=1, pot_style='cannon', pot_h=500.0)),
    ("Mill chimney, square", dict(kind='industrial', ind_shape='square', ind_bottom=2400.0, ind_top=1400.0,
                                  ind_height=18000.0, plinth_h=2000.0, band_every=6000.0, cap_courses=4)),
    ("Factory chimney, octagonal", dict(kind='industrial', ind_shape='octagon', ind_bottom=3000.0,
                                        ind_top=1800.0, ind_height=36000.0, plinth_h=4000.0,
                                        band_every=8000.0, cap_courses=5)),
    ("Engine-house chimney, round", dict(kind='industrial', ind_shape='round', ind_bottom=1800.0,
                                         ind_top=1200.0, ind_height=15000.0, plinth_h=0.0,
                                         band_every=0.0, cap_courses=3)),
    ("Doig kiln ventilator (distillery)", dict(kind='vent', vent_style='doig', kiln=True, vent_w=2400.0,
                                               vent_h=1600.0, louvres=6, cap_h=1600.0, cap_over=500.0,
                                               cap_sweep=80.0, kiln_w=7000.0, kiln_d=7000.0, kiln_h=6000.0,
                                               kiln_sweep=60.0, vane=True, vane_style='arrow')),
    ("Doig ventilator only (no kiln roof)", dict(kind='vent', vent_style='doig', kiln=False, vent_w=2400.0,
                                                 vent_h=1600.0, louvres=6, cap_h=1600.0, cap_over=500.0,
                                                 cap_sweep=80.0, vane=False)),
    ("Goods shed ridge vent", dict(kind='vent', vent_style='pyramid', kiln=False, vent_w=1200.0, vent_h=600.0,
                                   louvres=3, louvre_d=100.0, cap_h=400.0, cap_over=150.0, cap_t=60.0,
                                   finial=0.0, vane=False, vent_kerb=150.0)),
    ("Stable louvre with weather vane", dict(kind='vent', vent_style='doig', kiln=False, vent_w=1500.0,
                                             vent_h=900.0, louvres=4, louvre_d=110.0, cap_h=1000.0,
                                             cap_over=250.0, cap_sweep=50.0, finial=350.0, vane=True,
                                             vane_style='banner', vane_h=1100.0, vane_len=800.0)),
    ("1:80 print - Doig kiln ventilator", dict(kind='vent', vent_style='doig', kiln=True, vent_w=2400.0,
                                               vent_h=1600.0, louvres=5, louvre_d=160.0, louvre_t=48.0,
                                               cap_t=120.0, vane=True, vane_t=40.0, vane_rod=60.0,
                                               vane_letter=320.0)),
    ("Weather vane, arrow", dict(kind='vane', vane_style='arrow', vane_letters=True, vane_h=1500.0,
                                 vane_len=1000.0)),
    ("1:80 print - cottage stack", dict(kind='house', width=900.0, depth=450.0, height=900.0, oversail=2,
                                        oversail_out=40.0, pots=2, pot_style='plain', pot_wall=40.0,
                                        joint=16.0)),
]

PRESETS_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Chimneys")


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
    safe = "".join(ch for ch in name if ch not in '\\/:*?"<>|').strip() or "My chimney"
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


# (tab, key, label, low, high, decimals, suffix, tip)
FIELDS = [
    ("Stack", 'width', "Width (along ridge)", 200.0, 10000.0, 0, " mm",
     "How long the stack is, along the ridge (or along the roof). 900 = 4 bricks."),
    ("Stack", 'depth', "Depth (front to back)", 200.0, 5000.0, 0, " mm",
     "How deep the stack is, front to back. 450 = 2 bricks."),
    ("Stack", 'height', "Height above roof", 100.0, 10000.0, 0, " mm",
     "How far the brickwork stands above the highest point of the roof under it (to the top course)."),
    ("Stack", 'along', "Along the roof", 0.0, 100.0, 0, " %",
     "Where it stands along the ridge (two faces) or along the face: 0 = one end, 50 = the middle, "
     "100 = the other end."),
    ("Stack", 'up', "Up the slope", 0.0, 100.0, 0, " %",
     "One roof face only: how far up the slope, 0 = the eaves, 100 = against the top edge."),
    ("Stack", 'oversail', "Oversailing courses", 0, 6, None, "",
     "Courses at the top that stand out, each one further than the one below (the corbelled top)."),
    ("Stack", 'oversail_out', "Each stands out", 0.0, 200.0, 0, " mm",
     "How much further each oversailing course stands out. A quarter brick is about 56 mm."),
    ("Stack", 'flaunch', "Flaunching height", 0.0, 400.0, 0, " mm",
     "The sloping mortar cap on top, round the pots. 0 = none."),
    ("Pots", 'pots', "Pots", 0, 12, None, "", "How many chimney pots, in a row along the stack. 0 = none."),
    ("Pots", 'pot_rows', "Pot rows", 1, 2, None, "",
     "One row of pots along the stack, or two rows side by side (a deeper stack, for lots of pots)."),
    ("Pots", 'pot_h', "Pot height", 100.0, 3000.0, 0, " mm", "How tall each pot is."),
    ("Pots", 'pot_dia', "Pot width", 80.0, 1000.0, 0, " mm", "Across the foot of each pot."),
    ("Pots", 'pot_wall', "Pot wall", 5.0, 200.0, 0, " mm",
     "How thick the pot's wall is at the top. For 1:80 printing keep it at least 32 mm (0.4 mm)."),
    ("Industrial", 'ind_bottom', "Size at the bottom", 500.0, 20000.0, 0, " mm",
     "Across the bottom of the shaft (across the flats of a square or octagon), bricks included."),
    ("Industrial", 'ind_top', "Size at the top", 300.0, 20000.0, 0, " mm",
     "Across the top of the shaft. Smaller than the bottom for a taper."),
    ("Industrial", 'ind_height', "Height", 2000.0, 200000.0, 0, " mm", "How tall the chimney is."),
    ("Industrial", 'plinth_h', "Plinth height", 0.0, 20000.0, 0, " mm",
     "A thicker base at the bottom. 0 = none."),
    ("Industrial", 'plinth_out', "Plinth stands out", 0.0, 500.0, 0, " mm", "How far the plinth stands out."),
    ("Industrial", 'band_every', "Bands every", 0.0, 50000.0, 0, " mm",
     "A projecting band of brick every so far up the shaft. 0 = none."),
    ("Industrial", 'band_courses', "Band courses", 1, 6, None, "", "How many courses deep each band is."),
    ("Industrial", 'band_out', "Bands stand out", 0.0, 300.0, 0, " mm", "How far the bands stand out."),
    ("Industrial", 'cap_courses', "Cap courses", 0, 12, None, "",
     "Courses at the top that step out, each further than the one below (the corbelled cap)."),
    ("Industrial", 'cap_out', "Each steps out", 0.0, 200.0, 0, " mm", "How much each cap course steps out."),
    ("Industrial", 'coping_h', "Coping height", 0.0, 1000.0, 0, " mm",
     "The stone or iron coping ring on top. 0 = none."),
    ("Industrial", 'coping_over', "Coping overhang", 0.0, 500.0, 0, " mm", "How far the coping overhangs."),
    ("Vent", 'vent_w', "Ventilator width", 300.0, 10000.0, 0, " mm",
     "Across the louvred box (it's square), outside the corner posts."),
    ("Vent", 'vent_h', "Louvred height", 200.0, 10000.0, 0, " mm", "How tall the louvred part is."),
    ("Vent", 'louvres', "Louvres each side", 1, 30, None, "", "How many sloping louvre boards up each side."),
    ("Vent", 'louvre_d', "Louvre depth", 20.0, 1000.0, 0, " mm",
     "How far the louvre boards stand out from the dark core behind them (also the corner posts' size)."),
    ("Vent", 'louvre_t', "Louvre thickness", 8.0, 200.0, 0, " mm",
     "How thick each louvre board is. For 1:80 printing 32 mm (0.4 mm) or more."),
    ("Vent", 'vent_kerb', "Kerb under it", 0.0, 2000.0, 0, " mm",
     "A plain base under the louvres. On a roof it is cut to the slope and stands this far above the "
     "highest point under it."),
    ("Vent", 'cap_h', "Cap height", 100.0, 10000.0, 0, " mm", "How tall the cap roof is, eaves to top."),
    ("Vent", 'cap_over', "Cap overhang", 0.0, 3000.0, 0, " mm", "How far the cap's eaves stand out past the louvres."),
    ("Vent", 'cap_sweep', "Pagoda sweep", 0.0, 100.0, 0, " %",
     "Doig: how much the cap's eaves sweep out flat (the pagoda look). 0 = a straight pyramid."),
    ("Vent", 'cap_t', "Cap eaves thickness", 20.0, 500.0, 0, " mm", "How thick the cap is at its eaves."),
    ("Vent", 'finial', "Finial", 0.0, 3000.0, 0, " mm", "A turned ball finial on top of the cap. 0 = none."),
    ("Vent", 'vent_along', "Along the ridge", 0.0, 100.0, 0, " %",
     "On two roof faces at the ridge: where it stands along the ridge, 0 = one end, 50 = the middle."),
    ("Kiln", 'kiln_w', "Kiln roof width", 1000.0, 50000.0, 0, " mm",
     "Across the kiln roof at its eaves (left to right)."),
    ("Kiln", 'kiln_d', "Kiln roof depth", 1000.0, 50000.0, 0, " mm", "Front to back at its eaves."),
    ("Kiln", 'kiln_h', "Kiln roof height", 500.0, 50000.0, 0, " mm",
     "From the eaves up to the top, where the ventilator stands. Doig's kiln roofs are steep."),
    ("Kiln", 'kiln_sweep', "Kiln roof sweep", 0.0, 100.0, 0, " %",
     "How much the kiln roof sweeps out at its eaves. 0 = a straight pyramid."),
    ("Kiln", 'kiln_eave', "Eaves thickness", 20.0, 1000.0, 0, " mm", "The upright edge round the kiln roof's eaves."),
    ("Kiln", 'kiln_top', "Flat round the vent", 0.0, 2000.0, 0, " mm",
     "How far the kiln roof's flat top reaches past the ventilator's kerb."),
    ("Vane", 'vane_h', "Rod height", 300.0, 10000.0, 0, " mm",
     "How tall the rod is, from its foot up to the pointer."),
    ("Vane", 'vane_len', "Pointer length", 200.0, 10000.0, 0, " mm", "Tip to tail of the arrow or banner."),
    ("Vane", 'vane_t', "Plate thickness", 8.0, 200.0, 0, " mm",
     "How thick the pointer, arms and letters are. For 1:80 resin printing 24 mm (0.3 mm) or more."),
    ("Vane", 'vane_rod', "Rod thickness", 10.0, 300.0, 0, " mm", "Across the upright rod."),
    ("Vane", 'vane_arms', "Arms across", 100.0, 10000.0, 0, " mm", "End to end of the N-S (and E-W) arms."),
    ("Vane", 'vane_letter', "Letter height", 60.0, 2000.0, 0, " mm", "How tall the N, E, S and W letters are."),
    ("Bricks", 'brick_l', "Length", 50.0, 1000.0, 1, " mm", "The length of a brick. No brick is longer."),
    ("Bricks", 'brick_h', "Height", 20.0, 500.0, 1, " mm", "The height of a brick (one course)."),
    ("Bricks", 'brick_d', "Depth", 20.0, 500.0, 1, " mm",
     "How far the bricks stand out from the core (the core shows between them as mortar)."),
    ("Bricks", 'joint', "Mortar joint", 1.0, 100.0, 1, " mm",
     "The gap between bricks. For 1:80 printing use about 16-32 mm (0.2-0.4 mm)."),
]


# ---------------------------------------------------------------------------
# Preview: a front view of what will be built, drawn as the settings change
# ---------------------------------------------------------------------------


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


class ChimneyPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.v = dict(DEFAULTS)
        try:
            self.setMinimumHeight(170)
        except Exception:
            pass

    def set_values(self, v):
        self.v = dict(v)
        try:
            self.update()
        except Exception:
            pass

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QPolygonF
        from PySide6.QtCore import QPointF, QRectF
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.Antialiasing)
            w, h = self.width(), self.height()
            p.fillRect(0, 0, w, h, QColor(236, 238, 242))
            shapes, cap = self.drawing()
            xs = [x for kind, pts, c in shapes for x, _ in pts]
            ys = [y for kind, pts, c in shapes for _, y in pts]
            if not xs:
                return
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            sc = min((w - 16) / max(1.0, x1 - x0), (h - 30) / max(1.0, y1 - y0))
            ox = w / 2 - (x0 + x1) / 2 * sc
            oy = h - 20 + y0 * sc

            def P(x, y):
                return QPointF(ox + x * sc, oy - y * sc)
            for kind, pts, col in shapes:
                if kind == 'line':
                    p.setPen(QPen(QColor(*col), 1.0))
                    p.drawLine(P(*pts[0]), P(*pts[1]))
                else:
                    p.setPen(QPen(QColor(60, 40, 30), 0.8))
                    p.setBrush(QColor(*col))
                    p.drawPolygon(QPolygonF([P(x, y) for x, y in pts]))
            p.setPen(QColor(80, 80, 80))
            p.drawText(QRectF(4, h - 18, w - 8, 16), 0x0084, cap)
        finally:
            p.end()

    def drawing(self):
        """[(kind, points, colour)] in mm, front view, and a caption."""
        v = self.v
        kind = v.get('kind', 'house')
        BR, MO, FL, PO, RF = (178, 92, 66), (205, 200, 192), (196, 192, 184), (196, 112, 66), (110, 118, 132)
        Hc = v['brick_h'] + v['joint']
        out = []

        def rect(x0, y0, x1, y1, col):
            out.append(('poly', [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], col))

        def courses(x0, x1, y0, y1, step_off=0.0):
            # mortar lines and staggered joints, so it reads as brickwork
            n = int((y1 - y0) / Hc)
            unit = v['brick_l'] + v['joint']
            for k in range(1, n + 1):
                y = y0 + k * Hc
                if y < y1 - 1:
                    out.append(('line', [(x0, y), (x1, y)], (120, 60, 40)))
            for k in range(n + 1):
                yb, yt = y0 + k * Hc, min(y1, y0 + (k + 1) * Hc)
                x = x0 + (unit / 2 if k % 2 else 0) + unit
                while x < x1 - 20:
                    out.append(('line', [(x, yb), (x, yt)], (120, 60, 40)))
                    x += unit

        def pots(row_n, W, base, dia, ph, style):
            if not row_n:
                return
            prof, seg, rot = pot_profile(style, ph, dia, v['pot_wall'])
            first_top = next(i for i, (r, z) in enumerate(prof) if abs(z - ph) < 1e-6)
            sil = prof[1:first_top + 1]
            sp = W / row_n
            for k in range(row_n):
                cx = -W / 2 + sp * (k + 0.5)
                pts = [(cx + r, base + z) for r, z in sil] + [(cx - r, base + z) for r, z in reversed(sil)]
                out.append(('poly', pts, PO))
                if style == 'crown':
                    rt = sil[-1][0]
                    for j in (-2, 0, 2):
                        bx = cx + rt * 0.33 * j
                        rect(bx - rt * 0.12, base + ph, bx + rt * 0.12, base + ph * 1.1, PO)
        if kind == 'house':
            W, D, rows, per_row, widened = stack_size(v)
            vis = v['height'] + 250.0                    # what shows above the roof, and a bit
            n_over = int(v['oversail'])
            body = vis - n_over * Hc
            pr = v['oversail_out']
            # the roof running across the foot of the stack
            out.append(('poly', [(-W * 1.1, -250), (W * 1.1, -250), (W * 1.1, -40), (-W * 1.1, 160)], RF))
            rect(-W / 2, -200, W / 2, body, BR)
            courses(-W / 2, W / 2, -200, body)
            y = body
            for i in range(n_over):
                e = pr * (i + 1)
                rect(-W / 2 - e, y, W / 2 + e, y + Hc, BR)
                courses(-W / 2 - e, W / 2 + e, y, y + Hc)
                y += Hc
            fl = v['flaunch']
            top = y
            if fl > 0:
                e = pr * n_over - 10
                out.append(('poly', [(-W / 2 - e, top), (W / 2 + e, top), (W / 2 - 40, top + fl),
                                     (-W / 2 + 40, top + fl)], FL))
            pots(per_row, W, top + fl * 0.6, v['pot_dia'], v['pot_h'], v['pot_style'])
            cap = "Stack %.0f x %.0f mm, %d pot%s%s%s" % (W, D, int(v['pots']), "" if int(v['pots']) == 1 else "s",
                                                       " in 2 rows" if rows == 2 else "",
                                                       " (widened to fit)" if widened else "")
        elif kind == 'industrial':
            Hh = v['ind_height']
            bw, tw = v['ind_bottom'], v['ind_top']
            ph = v['plinth_h']
            pts_ = [(-bw / 2, 0), (bw / 2, 0), (tw / 2, Hh), (-tw / 2, Hh)]
            out.append(('poly', pts_, BR))
            if ph > 0:
                e = v['plinth_out']
                wb = bw + 2 * e
                wt = bw - (bw - tw) * ph / Hh + 2 * e
                out.append(('poly', [(-wb / 2, 0), (wb / 2, 0), (wt / 2, ph), (-wt / 2, ph)], BR))
            be = v['band_every']
            if be > 0:
                z = ph + be
                while z < Hh - v['cap_courses'] * Hc - 3 * Hc:
                    wz = bw - (bw - tw) * z / Hh + 2 * v['band_out']
                    rect(-wz / 2, z, wz / 2, z + v['band_courses'] * Hc, BR)
                    z += be
            z = Hh - v['cap_courses'] * Hc
            for i in range(int(v['cap_courses'])):
                wz = tw + 2 * v['cap_out'] * (i + 1)
                rect(-wz / 2, z, wz / 2, z + Hc, BR)
                z += Hc
            if v['coping_h'] > 0:
                wz = tw + 2 * v['cap_out'] * int(v['cap_courses']) + 2 * v['coping_over']
                rect(-wz / 2, Hh, wz / 2, Hh + v['coping_h'], MO)
            cap = "%s chimney, %.1f m high" % (dict(IND_SHAPES).get(v['ind_shape'], ''), Hh / 1000.0)
        elif kind in ('vent', 'vane'):
            # the real solids, seen from the front: back faces first, the core dark
            if kind == 'vent':
                kiln = (v['kiln_w'], v['kiln_d']) if v.get('kiln') else None
                try:
                    parts, info = vent_parts(dict(v, segments=10), kiln)
                except ValueError as e:
                    return [], str(e)
            else:
                vs, hh = vane_parts(v, 0.0, True)
                parts, info = {'Weather vane': vs}, {'height': hh}
            cols = {'Kiln roof': (110, 118, 132), 'Ventilator': (196, 186, 166), 'Cap': (120, 128, 140),
                    'Weather vane': (60, 64, 70)}
            ci = v['vent_w'] / 2.0 - max(20.0, min(v['vent_w'] / 2.0 * 0.4, v['louvre_d']))
            faces = []
            for nm, sols in parts.items():
                for so in sols:
                    xs_ = [q[0] for f, _ in so for q in f]
                    core = nm == 'Ventilator' and abs((max(xs_) - min(xs_)) / 2.0 - ci) < 1e-6
                    for f, _ in so:
                        nrm = _newell(f)
                        L = v_len(nrm) or 1.0
                        ny = nrm[1] / L
                        if ny > -1e-6:
                            continue
                        sh = 0.6 + 0.4 * min(1.0, -ny + max(0.0, nrm[2] / L) * 0.5)
                        c0 = (40, 34, 30) if core else cols.get(nm, (150, 150, 150))
                        col = tuple(int(min(255, c_ * sh)) for c_ in c0)
                        faces.append((sum(q[1] for q in f) / len(f), [(q[0], q[2]) for q in f], col))
            faces.sort(key=lambda t_: -t_[0])
            out += [('poly', pts, col) for _, pts, col in faces]
            if kind == 'vent':
                cap = "%s ventilator %.1f m across, %d louvres a side, %.1f m tall" % (
                    "Doig" if v['vent_style'] == 'doig' else "Louvred", v['vent_w'] / 1000.0, int(v['louvres']),
                    info['height'] / 1000.0)
            else:
                cap = "Weather vane, %.1f m tall" % (info['height'] / 1000.0)
        else:
            n = max(1, int(v['pots']))
            W = n * v['pot_dia'] * 1.25
            pots(n, W, 0, v['pot_dia'], v['pot_h'], v['pot_style'])
            cap = "%d %s pot%s" % (n, dict(POT_STYLES).get(v['pot_style'], '').lower(), "" if n == 1 else "s")
        return out, cap


class ChimneyDialog(QDialog):
    def __init__(self, viewport, tool, cur):
        super().__init__(viewport)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        lay = QVBoxLayout(self)
        intro = QLabel("Select a roof face (or both faces at the ridge) for a stack, or a flat face for a "
                       "chimney, pots, vent or vane, then Build. Sizes in real mm.")
        intro.setWordWrap(True)
        lay.addWidget(intro)
        top = QFormLayout()
        self.cb_kind = QComboBox()
        for k, t in KINDS:
            self.cb_kind.addItem(t, k)
        self.cb_kind.setToolTip("House stack: stands on the roof faces you pick, cut to the slope. Industrial: "
                                "a tall mill or factory chimney on a flat face (or the origin). Pots only: a row "
                                "of pots to stand on a stack you've drawn. Roof vent: a louvred ventilator (Doig's "
                                "pagoda on a distillery kiln) on a flat face or astride a ridge. Weather vane: "
                                "a vane on its own.")
        _narrow(self.cb_kind, 14)
        top.addRow("Make", self.cb_kind)
        self.cb_preset = QComboBox()
        _narrow(self.cb_preset, 14)
        self.cb_preset.setToolTip("Ready-made chimneys. Pick one and the window is filled in; your own "
                                  "presets are in the list too.")
        prow = QHBoxLayout()
        prow.addWidget(self.cb_preset, 1)
        b_save = QPushButton("Save as...")
        b_save.setToolTip("Saves everything in this window as your own preset.")
        prow.addWidget(b_save)
        top.addRow("Preset", prow)
        lay.addLayout(top)

        self.preview = ChimneyPreview()
        self.preview.setToolTip("A front view of what will be built. It changes as you change the settings.")
        lay.addWidget(self.preview)
        self.tabs = QTabWidget()
        pages = {}
        for title in ("Stack", "Pots", "Industrial", "Bricks", "Vent", "Kiln", "Vane"):
            pg = QWidget()
            pages[title] = _form(pg)
            self.tabs.addTab(pg, title)
        self.tabs.setTabToolTip(0, "The house stack: its size, where it stands and its top.")
        self.tabs.setTabToolTip(1, "The chimney pots.")
        self.tabs.setTabToolTip(2, "The industrial chimney: shaft, plinth, bands and cap.")
        self.tabs.setTabToolTip(3, "Brick size and mortar.")
        self.tabs.setTabToolTip(4, "The roof ventilator: louvred box, cap and finial.")
        self.tabs.setTabToolTip(5, "The distillery kiln's steep swept roof the Doig ventilator stands on.")
        self.tabs.setTabToolTip(6, "The weather vane.")
        lay.addWidget(self.tabs)
        self.w = {}
        for tab, key, label, lo, hi, dec, suf, tip in FIELDS:
            if dec is None:
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
            pages[tab].addRow(lab, s)
            self.w[key] = s
        self.cb_style = QComboBox()
        for k, t in POT_STYLES:
            self.cb_style.addItem(t, k)
        self.cb_style.setToolTip("The shape of the pots.")
        lab = QLabel("Pot style")
        lab.setToolTip(self.cb_style.toolTip())
        pages["Pots"].insertRow(1, lab, self.cb_style)
        self.cb_shape = QComboBox()
        for k, t in IND_SHAPES:
            self.cb_shape.addItem(t, k)
        self.cb_shape.setToolTip("The shape of the industrial chimney's shaft.")
        lab = QLabel("Shape")
        lab.setToolTip(self.cb_shape.toolTip())
        pages["Industrial"].insertRow(0, lab, self.cb_shape)
        self.cb_fit = QCheckBox("Widen the stack to fit the pots")
        self.cb_fit.setToolTip("Makes the stack longer (and deeper, with two rows) when the pots wouldn't fit "
                               "on it, with a gap between each, in whole half-bricks so the bond stays neat.")
        pages["Pots"].addRow(self.cb_fit)
        self.cb_vstyle = QComboBox()
        for k, t in VENT_STYLES:
            self.cb_vstyle.addItem(t, k)
        self.cb_vstyle.setToolTip("Doig: Charles Doig's pagoda ventilator, its cap's eaves sweeping out flat. "
                                  "Pyramid: a plain louvred vent with a straight pyramid cap.")
        _narrow(self.cb_vstyle, 12)
        lab = QLabel("Style")
        lab.setToolTip(self.cb_vstyle.toolTip())
        pages["Vent"].insertRow(0, lab, self.cb_vstyle)
        self.cb_kiln = QCheckBox("With the kiln roof under it")
        self.cb_kiln.setToolTip("On a flat face: builds the steep swept kiln roof too (Kiln tab), with the "
                                "ventilator on top. Pick the top of the kiln's walls first.")
        pages["Kiln"].insertRow(0, self.cb_kiln)
        self.cb_kfit = QCheckBox("Fit the kiln roof to the picked face")
        self.cb_kfit.setToolTip("Makes the kiln roof's eaves the size of the face you picked (the top of the "
                                "walls), instead of the width and depth below.")
        pages["Kiln"].insertRow(1, self.cb_kfit)
        self.cb_vane = QCheckBox("Weather vane on top")
        self.cb_vane.setToolTip("Stands a weather vane (Vane tab) on the ventilator's finial.")
        pages["Vent"].addRow(self.cb_vane)
        self.cb_vanest = QComboBox()
        for k, t in VANE_STYLES:
            self.cb_vanest.addItem(t, k)
        self.cb_vanest.setToolTip("The pointer: an arrow with a feathered tail, or a banner with an arrow-head.")
        lab = QLabel("Pointer")
        lab.setToolTip(self.cb_vanest.toolTip())
        pages["Vane"].insertRow(0, lab, self.cb_vanest)
        self.cb_letters = QCheckBox("N, E, S, W arms and letters")
        self.cb_letters.setToolTip("The cross of arms under the pointer with a letter on each end. Tiny at "
                                   "1:80: best printed in resin.")
        pages["Vane"].insertRow(1, self.cb_letters)
        self.cb_level = QCheckBox("Lay the courses level")
        self.cb_level.setToolTip("On a tapered chimney every course is laid level and set in a little from "
                                 "the one below, like a real one. Untick to tilt the bricks to the slope.")
        pages["Bricks"].addRow(self.cb_level)

        self.lbl_report = QLabel()
        self.lbl_report.setWordWrap(True)
        lay.addWidget(self.lbl_report)
        brow = QHBoxLayout()
        b_go = QPushButton("Build")
        b_go.setDefault(True)
        b_go.setToolTip("Builds it on the selected face(s), as one group with a group for each part.")
        b_close = QPushButton("Close")
        brow.addWidget(b_go)
        brow.addStretch(1)
        brow.addWidget(b_close)
        lay.addLayout(brow)
        try:
            self.setMaximumWidth(400)
        except Exception:
            pass
        self.set_values(cur)
        self.fill_presets()
        self.cb_kind.currentIndexChanged.connect(self.changed)
        for s_ in self.w.values():
            s_.valueChanged.connect(self.redraw)
        for cb in (self.cb_style, self.cb_shape, self.cb_vstyle, self.cb_vanest):
            cb.currentIndexChanged.connect(self.changed)
        for ck in (self.cb_fit, self.cb_level, self.cb_kiln, self.cb_kfit, self.cb_vane, self.cb_letters):
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
        vals = dict(self.values())
        vals.update(self._presets.get(name, {}))
        self.set_values(vals)
        self.changed()
        self.redraw()

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
                s.setValue(int(cur[k]) if isinstance(s, QSpinBox) else float(cur[k]))
        for cb, key in ((self.cb_kind, 'kind'), (self.cb_style, 'pot_style'), (self.cb_shape, 'ind_shape'),
                        (self.cb_vstyle, 'vent_style'), (self.cb_vanest, 'vane_style')):
            for i in range(cb.count()):
                if cb.itemData(i) == cur.get(key):
                    cb.setCurrentIndex(i)
        self.cb_level.setChecked(bool(cur.get('level', True)))
        self.cb_fit.setChecked(bool(cur.get('fit_pots', True)))
        for ck, key in ((self.cb_kiln, 'kiln'), (self.cb_kfit, 'kiln_fit'), (self.cb_vane, 'vane'),
                        (self.cb_letters, 'vane_letters')):
            ck.setChecked(bool(cur.get(key, DEFAULTS[key])))

    def redraw(self, *_):
        try:
            self.preview.set_values(self.values())
        except Exception:
            pass

    def changed(self, *_):
        self.redraw()
        kind = self.cb_kind.currentData()
        try:
            self.tabs.setTabEnabled(0, kind == 'house')
            self.tabs.setTabEnabled(1, kind in ('house', 'pots'))
            self.tabs.setTabEnabled(2, kind == 'industrial')
            self.tabs.setTabEnabled(3, kind in ('house', 'industrial'))
            self.tabs.setTabEnabled(4, kind == 'vent')
            self.tabs.setTabEnabled(5, kind == 'vent')
            self.tabs.setTabEnabled(6, kind == 'vane' or (kind == 'vent' and self.cb_vane.isChecked()))
            want = {'house': 0, 'industrial': 2, 'pots': 1, 'vent': 4, 'vane': 6}[kind]
            if not self.tabs.isTabEnabled(self.tabs.currentIndex()):
                self.tabs.setCurrentIndex(want)
            kiln = self.cb_kiln.isChecked()
            self.w['cap_sweep'].setEnabled(self.cb_vstyle.currentData() == 'doig')
            self.cb_kfit.setEnabled(kiln)
            for k in ('kiln_h', 'kiln_sweep', 'kiln_eave', 'kiln_top'):
                self.w[k].setEnabled(kiln)
            for k in ('kiln_w', 'kiln_d'):
                self.w[k].setEnabled(kiln and not self.cb_kfit.isChecked())
            for k in ('vane_arms', 'vane_letter'):
                self.w[k].setEnabled(self.cb_letters.isChecked())
        except Exception:
            pass

    def values(self):
        v = {k: (int(s.value()) if isinstance(s, QSpinBox) else float(s.value())) for k, s in self.w.items()}
        v.update(kind=self.cb_kind.currentData(), pot_style=self.cb_style.currentData(),
                 ind_shape=self.cb_shape.currentData(), level=self.cb_level.isChecked(),
                 fit_pots=self.cb_fit.isChecked(), vent_style=self.cb_vstyle.currentData(),
                 vane_style=self.cb_vanest.currentData(), kiln=self.cb_kiln.isChecked(),
                 kiln_fit=self.cb_kfit.isChecked(), vane=self.cb_vane.isChecked(),
                 vane_letters=self.cb_letters.isChecked())
        return v


class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
class ChimneysTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+H"
    description = ("Brick chimney stacks cut to the roof, with oversailing courses, flaunching and pots; "
                   "industrial chimneys; chimney pots; louvred roof vents and Doig's pagoda kiln ventilators; "
                   "and weather vanes.")
    _dialog = None
    _saved = None

    def on_activate(self, viewport):
        dlg = ChimneysTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.raise_()
                    dlg.activateWindow()
                    return
            except Exception:
                pass
        dlg = ChimneyDialog(viewport, self, dict(DEFAULTS, **(ChimneysTool._saved or {})))
        ChimneysTool._dialog = dlg

        def closed(*_):
            ChimneysTool._dialog = None
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
        ChimneysTool._saved = dict(v)
        polys = self._picked(dlg.viewport)
        kind = v['kind']
        try:
            if kind == 'house':
                if not polys or len(polys) > 2:
                    QMessageBox.information(dlg, PLUGIN_NAME, "Select a roof face (or the two faces either "
                                                              "side of the ridge) first.")
                    return
                roof, frame = roof_from_faces(polys[:2])
                parts, rep = house_stack(v, roof, frame)
                name = "Chimney stack - %.0f x %.0f" % (rep['width'], rep['depth'])
                msg = ("Built a %.0f x %.0f mm stack: %d bricks in %d courses (cut to the roof), %d oversailing, "
                       "%.0f mm above the roof, %d pots%s." % (rep['width'], rep['depth'], rep['bricks'],
                                                              rep['courses'], rep['oversail'], rep['above'],
                                                              int(v['pots']),
                                                              " in two rows" if rep['rows'] == 2 else ""))
                if rep['widened']:
                    msg += " (Made bigger to fit the pots.)"
            elif kind == 'vent' and polys and any(abs(v_norm(_newell(p_))[2]) < 0.999 for p_ in polys[:2]):
                # on a sloping roof face, or astride the ridge of two
                roof, frame = roof_from_faces(polys[:2])
                parts, rep = vent_on_roof(v, roof, frame)
                name = "Roof vent - %.0f" % rep['width']
                msg = ("Built a %.0f mm %s ventilator %s, its kerb cut to the roof, %d louvres%s." % (
                    rep['width'], "Doig" if v['vent_style'] == 'doig' else "louvred",
                    "astride the ridge" if frame['ridge'] is not None else "on the roof face", rep['louvres'],
                    ", with a weather vane" if v['vane'] else ""))
                if v['kiln']:
                    msg += " (No kiln roof: that goes on a flat face, the top of the kiln's walls.)"
            else:
                cx = cy = z0 = 0.0
                along = (1.0, 0.0)
                if polys:
                    pts = polys[0]
                    cx = sum(p[0] for p in pts) / len(pts)
                    cy = sum(p[1] for p in pts) / len(pts)
                    z0 = max(p[2] for p in pts)
                    best = max(range(len(pts)), key=lambda i: v_len(v_sub(pts[(i + 1) % len(pts)], pts[i])))
                    e = v_sub(pts[(best + 1) % len(pts)], pts[best])
                    L = math.hypot(e[0], e[1])
                    if L > 1e-9:
                        along = (e[0] / L, e[1] / L)
                if kind == 'industrial':
                    parts, rep = industrial(v, cx, cy, z0)
                    shape = dict(IND_SHAPES).get(v['ind_shape'], '')
                    name = "Industrial chimney - %s %.0f m" % (shape.lower(), v['ind_height'] / 1000.0)
                    msg = "Built a %.1f m %s chimney: %d bricks in %d courses." % (
                        rep['height'], shape.lower(), rep['bricks'], rep['courses'])
                elif kind == 'vent':
                    kiln = None
                    if v['kiln']:
                        kiln = (v['kiln_w'], v['kiln_d'])
                        if v['kiln_fit'] and polys:
                            acr = (-along[1], along[0])
                            us = [p[0] * along[0] + p[1] * along[1] for p in pts]
                            ws = [p[0] * acr[0] + p[1] * acr[1] for p in pts]
                            kiln = ((max(us) - min(us)) / SCALE, (max(ws) - min(ws)) / SCALE)
                            uc, wc = (max(us) + min(us)) / 2.0, (max(ws) + min(ws)) / 2.0
                            cx, cy = along[0] * uc + acr[0] * wc, along[1] * uc + acr[1] * wc
                    parts, rep = vent_parts(v, kiln)
                    parts = place_parts(parts, cx, cy, z0, along)
                    what = "Doig" if v['vent_style'] == 'doig' else "louvred"
                    name = ("Doig kiln ventilator" if kiln else "Roof vent") + " - %.0f" % rep['width']
                    msg = "Built a %.0f mm %s ventilator%s, %d louvres%s, %.1f m tall." % (
                        rep['width'], what, " on a %.0f x %.0f mm kiln roof" % kiln if kiln else "",
                        rep['louvres'], ", with a weather vane" if v['vane'] else "", rep['height'] / 1000.0)
                elif kind == 'vane':
                    vs, hh = vane_parts(v, 0.0, True)
                    parts = place_parts({'Weather vane': vs}, cx, cy, z0, along)
                    name = "Weather vane"
                    msg = "Built a %.1f m weather vane." % (hh / 1000.0)
                else:
                    if int(v['pots']) < 1:
                        v['pots'] = 1
                    parts, rep = pots_only(v, cx, cy, z0, along)
                    name = "Chimney pots - %d" % rep['pots']
                    msg = "Added %d pots." % rep['pots']
                if not polys:
                    msg += " (Nothing was selected, so it's at the origin.)"
        except ValueError as e:
            QMessageBox.warning(dlg, PLUGIN_NAME, str(e))
            return
        nf = self.add_to_scene(dlg.viewport, name, parts)
        if nf is None:
            return
        msg += " %d faces." % nf
        if self._errors[0]:
            msg += "\n%d faces could not be made: %s" % self._errors
        dlg.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if self._errors[0] else "#2e7d32"))
        dlg.lbl_report.setText(msg)

    def add_to_scene(self, viewport, name, parts):
        stats = {'faces': 0, 'errors': 0, 'err': None}
        tol = 1e-4 * 0.001

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
            kids = [make_group(Group, mesh_of(sol), nm) for nm, sol in parts.items() if sol]
            if stats['faces'] == 0:
                raise RuntimeError("No faces could be made (%s)." % stats['err'])
            top = None
            try:
                top = Group(name=name)
                if hasattr(top, 'adopt'):
                    top.adopt(kids)
                else:
                    top.children = kids
                top.component = False
            except Exception:
                top = None
            for g in ([top] if top is not None else kids):
                _ed3d_organise(scene, g)
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
    ChimneysTool().on_activate(viewport)
