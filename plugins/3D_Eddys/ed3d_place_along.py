# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Place Along Line for IngeTrazo
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
3D Place Along Line - a row of rivets, bolts or any part along a line drawn over a surface.

  * Draw line - select the object the line goes over (a boiler, a cab side, a tender), click
    points on its surface, and the plugin joins them into one line that follows the surface
    between the clicks: over the curve of a boiler, round the corners of a square or hex
    column. Smooth curve through the clicks, or straight from click to click. Tick Closed
    loop and it goes all the way round and joins up.
  * Wrap round - select a round, square or many-sided object (a boiler, a chimney, a dome)
    and click once: the line rings it all the way round through that point.
  * Spacing - so many between the two ends (or so many round a loop), or a pitch in mm
    (fitted so the ends land exactly). A part on every point you clicked and on every
    corner, if you want, with the rest spaced evenly between.
  * Use selected line - your own line: lines you've drawn or offset (select them, joined end to
    end), or a group holding them. The parts stay on your line, facing out of the surface under it.
  * Round selected face - round the edge of a face (or several faces, as one panel), moved in
    from the edge by the inset you give; a window hole gets a ring of its own.
  * Every part stands on the surface: its base on the line and its up (blue) axis square
    out of the surface where it sits, so rivets round a boiler all face out. Sink in until
    there's no gap lets each one down into a curved surface until no gap shows under its edges.
  * The parts come from the 3D Find & Replace parts library (markers, rivets, bolts and your
    own), or any component you select in the model.
The whole row is one group (one Undo). Select it and press Edit selected row to change the
part, the spacing or the line, and it's replaced in place.
"""

import math
import json
import os
import numpy as np
from tools.base import Tool
from PySide6.QtGui import QVector3D, QMatrix4x4
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton, QCheckBox, QGroupBox,
    QComboBox, QDoubleSpinBox, QSpinBox, QRadioButton, QButtonGroup
)

PLUGIN_NAME = "3D Place Along Line"
VERSION = "3"
MM = 1000.0                       # IngeTrazo works in metres; the window shows mm
EXT_TAG = "eddy_place_along"      # on a row this plugin made: the line and settings, to edit it again
EXT_KEY = "eddy_parts"            # tags a part from the Find & Replace parts library


# ---------------------------------------------------------------------------
# Sums on (x, y, z) tuples (no Qt in them, so they can be checked on their own)
# ---------------------------------------------------------------------------
def _sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def _add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def _mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def _dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def _len(a): return math.sqrt(_dot(a, a))
def _lerp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(a):
    L = _len(a)
    return (a[0] / L, a[1] / L, a[2] / L) if L > 1e-15 else None


def _t(p):
    return (float(p[0]), float(p[1]), float(p[2]))


# ---------------------------------------------------------------------------
# The surface: the triangles of the object(s) the line goes over, in model space
# ---------------------------------------------------------------------------
def _safe(x):
    return np.where(np.abs(x) < 1e-30, 1e-30, x)


def closest_on_triangles(p, A, B, C):
    """The closest point on each triangle (A[i], B[i], C[i]) to p, and the squared distances."""
    p = np.asarray(p, dtype=float)
    ab, ac = B - A, C - A
    ap, bp, cp = p - A, p - B, p - C
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    res = np.empty_like(A)
    done = np.zeros(len(A), dtype=bool)

    def put(mask, val):
        m = mask & ~done
        res[m] = val[m]
        done[m] = True
    with np.errstate(divide='ignore', invalid='ignore'):
        put((d1 <= 0) & (d2 <= 0), A)                                   # corner A
        put((d3 >= 0) & (d4 <= d3), B)                                  # corner B
        vc = d1 * d4 - d3 * d2
        put((vc <= 0) & (d1 >= 0) & (d3 <= 0), A + ab * (d1 / _safe(d1 - d3))[:, None])     # edge AB
        put((d6 >= 0) & (d5 <= d6), C)                                  # corner C
        vb = d5 * d2 - d1 * d6
        put((vb <= 0) & (d2 >= 0) & (d6 <= 0), A + ac * (d2 / _safe(d2 - d6))[:, None])     # edge AC
        va = d3 * d6 - d5 * d4
        e43, e56 = d4 - d3, d5 - d6
        put((va <= 0) & (e43 >= 0) & (e56 >= 0), B + (C - B) * (e43 / _safe(e43 + e56))[:, None])  # edge BC
        den = 1.0 / _safe(va + vb + vc)
        put(~done, A + ab * (vb * den)[:, None] + ac * (vc * den)[:, None])                 # inside
    return res, ((res - p) ** 2).sum(1)


class Surface:
    """Triangles (each with the normal of the face it came from) to project onto and slice."""

    def __init__(self, tris, normals):
        T = np.asarray(tris, dtype=float).reshape(-1, 3, 3)
        N = np.asarray(normals, dtype=float).reshape(-1, 3)
        if len(T):
            area = np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1)
            keep = area > 1e-18
            T, N = T[keep], N[keep]
            L = np.linalg.norm(N, axis=1)
            N = N / np.where(L < 1e-30, 1.0, L)[:, None]
        self.T, self.N = T, N
        self.A, self.B, self.C = T[:, 0], T[:, 1], T[:, 2]
        if len(T):
            pts = T.reshape(-1, 3)
            self.lo, self.hi = pts.min(0), pts.max(0)
            self.tlo, self.thi = T.min(1), T.max(1)
        else:
            self.lo = self.hi = np.zeros(3)
            self.tlo = self.thi = np.zeros((0, 3))
        self.diag = float(np.linalg.norm(self.hi - self.lo)) or 1.0

    def __len__(self):
        return len(self.T)

    def near(self, lo, hi):
        """Just the triangles whose box meets the box lo..hi."""
        m = np.all(self.thi >= np.asarray(lo) - 1e-12, axis=1) & np.all(self.tlo <= np.asarray(hi) + 1e-12, axis=1)
        s = Surface.__new__(Surface)
        s.T, s.N = self.T[m], self.N[m]
        s.A, s.B, s.C = s.T[:, 0], s.T[:, 1], s.T[:, 2]
        s.tlo, s.thi = self.tlo[m], self.thi[m]
        s.lo, s.hi, s.diag = self.lo, self.hi, self.diag
        return s

    def closest(self, p, ref=None):
        """(point, normal, distance): the nearest point on the surface to p. ref: a rough normal
        - only faces facing that way count (so a thin sheet's back isn't picked). At an edge or
        corner the normal is the average of the faces that meet there."""
        if not len(self.T):
            return _t(p), (0.0, 0.0, 1.0), float('inf')
        q, d2 = closest_on_triangles(p, self.A, self.B, self.C)
        if ref is not None:
            ok = (self.N @ np.asarray(ref, dtype=float)) > 0.05
            if ok.any():
                d2 = np.where(ok, d2, np.inf)
        i = int(np.argmin(d2))
        d = math.sqrt(max(0.0, float(d2[i])))
        tol = d + 1e-6 * self.diag
        near = np.sqrt(np.maximum(d2, 0.0)) <= tol
        ns = np.unique(np.round(self.N[near], 5), axis=0)
        n = _unit(_t(ns.sum(0))) or _t(self.N[i])
        return _t(q[i]), n, d


# ---------------------------------------------------------------------------
# Slicing the surface with a plane: the lines where it cuts the surface
# ---------------------------------------------------------------------------
def slice_chains(surf, origin, normal):
    """Where the plane through origin (facing normal) cuts the surface, as chains:
    [(points, normals, closed)] - each chain's points in order along it."""
    if not len(surf):
        return []
    o = np.asarray(origin, dtype=float)
    nn = np.asarray(normal, dtype=float)
    eps = 1e-10 * surf.diag
    d = (surf.T - o) @ nn                                     # (T, 3) heights above the plane
    d = np.where(np.abs(d) < eps, eps, d)                     # a corner on the plane counts as above it
    pos = d > 0
    mixed = pos.any(1) & ~pos.all(1)
    idx = np.nonzero(mixed)[0]
    if not len(idx):
        return []
    q = 1e-7 * surf.diag

    def key(p):
        return (int(round(p[0] / q)), int(round(p[1] / q)), int(round(p[2] / q)))
    segs = []
    for i in idx:
        tri, dd = surf.T[i], d[i]
        cut = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            if (dd[a] > 0) != (dd[b] > 0):
                u, v, du, dv = tri[a], tri[b], dd[a], dd[b]
                if tuple(u) > tuple(v):                       # the same sum from both sides of an edge
                    u, v, du, dv = v, u, dv, du
                cut.append(_t(u + (v - u) * (du / (du - dv))))
        if len(cut) == 2 and key(cut[0]) != key(cut[1]):
            segs.append((cut[0], cut[1], _t(surf.N[i])))
    ends = {}
    for k, (a, b, _n) in enumerate(segs):
        ends.setdefault(key(a), []).append(k)
        ends.setdefault(key(b), []).append(k)
    used = [False] * len(segs)
    chains = []

    def other_end(k, kp):
        a, b, _n = segs[k]
        return (b, key(b)) if key(a) == kp else (a, key(a))

    def walk(start_k, from_key):
        """Follows the chain from segment start_k, leaving from from_key."""
        pts, nrs = [], []
        k, kp = start_k, from_key
        while True:
            used[k] = True
            nxt, nk = other_end(k, kp)
            pts.append(nxt)
            nrs.append(segs[k][2])
            cand = [j for j in ends.get(nk, []) if not used[j]]
            if not cand:
                return pts, nrs, nk
            k, kp = cand[0], nk
    for k0 in range(len(segs)):
        if used[k0]:
            continue
        a, b, n0 = segs[k0]
        used[k0] = True
        fwd, fn, kend = [], [], key(b)
        cand = [j for j in ends.get(key(b), []) if not used[j]]
        if cand:
            fwd, fn, kend = walk(cand[0], key(b))
        closed = kend == key(a) and len(fwd) >= 2
        if closed:
            pts = [a, b] + fwd[:-1]
            seg_n = [n0] + fn                              # normal of the segment leaving each point
        else:
            back, bn, _k = [], [], None
            cand = [j for j in ends.get(key(a), []) if not used[j]]
            if cand:
                back, bn, _k = walk(cand[0], key(a))
            pts = list(reversed(back)) + [a, b] + fwd
            seg_n = list(reversed(bn)) + [n0] + fn
        # each point's normal: the average of the segments either side of it
        m = len(pts)
        nrm = []
        for i in range(m):
            before = seg_n[i - 1] if (i > 0 or closed) else None
            after = seg_n[i] if i < len(seg_n) else None
            s = _add(before or (0.0, 0.0, 0.0), after or (0.0, 0.0, 0.0))
            nrm.append(_unit(s) or (after or before or (0.0, 0.0, 1.0)))
        chains.append((pts, nrm, closed))
    return chains


def locate(pts, closed, p):
    """(segment index, fraction along it, distance, the point on the chain) nearest to p."""
    best = None
    m = len(pts)
    nseg = m if closed else m - 1
    for i in range(nseg):
        a, b = pts[i], pts[(i + 1) % m]
        ab = _sub(b, a)
        L2 = _dot(ab, ab)
        t = 0.0 if L2 < 1e-30 else max(0.0, min(1.0, _dot(_sub(p, a), ab) / L2))
        q = _lerp(a, b, t)
        d = _len(_sub(p, q))
        if best is None or d < best[2]:
            best = (i, t, d, q)
    if best is None and m:
        best = (0, 0.0, _len(_sub(p, pts[0])), pts[0])
    return best


def poly_length(pts, closed=False):
    L = sum(_len(_sub(pts[i + 1], pts[i])) for i in range(len(pts) - 1))
    if closed and len(pts) > 1:
        L += _len(_sub(pts[0], pts[-1]))
    return L


def chain_between(chain, a, na, b, nb):
    """The part of a chain from a to b (both on it): (points, normals, length), the shorter way
    round on a closed chain. None if a or b isn't on it."""
    pts, nrm, closed = chain
    if len(pts) < 2:
        return None
    la, lb = locate(pts, closed, a), locate(pts, closed, b)
    m = len(pts)

    def run(ia, ib, step):
        """From a (on segment ia) to b (on segment ib), going forward (step 1) or back (-1)."""
        P, N = [a], [na]
        i = ia if step < 0 else (ia + 1) % m
        guard = 0
        stop = (ib + 1) % m if step < 0 else ib
        if step > 0 and ia == ib and la[1] <= lb[1]:
            return P + [b], N + [nb]
        if step < 0 and ia == ib and lb[1] <= la[1]:
            return P + [b], N + [nb]
        while guard <= m + 1:
            P.append(pts[i])
            N.append(nrm[i])
            if i == stop:
                break
            i = (i + step) % m
            guard += 1
        return P + [b], N + [nb]
    if closed:
        f = run(la[0], lb[0], 1)
        r = run(la[0], lb[0], -1)
        P, N = min((f, r), key=lambda x: poly_length(x[0]))
    else:
        ia, ib = la[0], lb[0]
        if (ia, la[1]) <= (ib, lb[1]):
            P, N = [a] + pts[ia + 1: ib + 1] + [b], [na] + nrm[ia + 1: ib + 1] + [nb]
        else:
            P, N = [a] + list(reversed(pts[ib + 1: ia + 1])) + [b], [na] + list(reversed(nrm[ib + 1: ia + 1])) + [nb]
    # drop points on top of each other
    outP, outN = [P[0]], [N[0]]
    for p, n in zip(P[1:], N[1:]):
        if _len(_sub(p, outP[-1])) > 1e-9:
            outP.append(p)
            outN.append(n)
        else:
            outN[-1] = _unit(_add(outN[-1], n)) or n
    return outP, outN, poly_length(outP)


def surface_hop(surf, a, na, b, nb):
    """The line over the surface from a to b: where the surface is cut by the plane through
    both points and square to the surface. Straight across a flat face, round the curve of a
    boiler, over the corners of a square or hex column. (points, normals) from a to b."""
    if _len(_sub(b, a)) < 1e-12:
        return [a], [na]
    up = _unit(_add(na, nb)) or na
    pn = _unit(_cross(_sub(b, a), up))
    if pn is not None:
        span = _len(_sub(b, a))
        lo = np.minimum(a, b) - span - 1e-6
        hi = np.maximum(a, b) + span + 1e-6
        sub = surf.near(lo, hi)
        best = None
        tol = 1e-5 * surf.diag + 1e-9
        for ch in slice_chains(sub, a, pn):
            la, lb = locate(ch[0], ch[2], a), locate(ch[0], ch[2], b)
            if la is None or lb is None or max(la[2], lb[2]) > tol:
                continue
            got = chain_between(ch, a, na, b, nb)
            if got and (best is None or got[2] < best[2]):
                best = got
        if best is not None:
            return best[0], best[1]
    return hop_by_halving(surf, a, na, b, nb)


def hop_by_halving(surf, a, na, b, nb, step=None, depth=0):
    """Fallback: halve the gap again and again, pulling each middle onto the surface."""
    step = step or surf.diag / 400.0
    if _len(_sub(b, a)) <= step or depth > 12:
        return [a, b], [na, nb]
    m = _lerp(a, b, 0.5)
    pm, nm, _d = surf.closest(m, _unit(_add(na, nb)))
    P1, N1 = hop_by_halving(surf, a, na, pm, nm, step, depth + 1)
    P2, N2 = hop_by_halving(surf, pm, nm, b, nb, step, depth + 1)
    return P1 + P2[1:], N1 + N2[1:]


def catmull_rom(points, closed, per_seg=6):
    """A smooth curve through the points (centripetal Catmull-Rom). Returns (samples, knots):
    knots[i] is where points[i] is in the samples."""
    P = list(points)
    n = len(P)
    if n < 3:
        return P, list(range(n))
    if closed:
        ext = [P[-1]] + P + [P[0], P[1]]
        nseg = n
    else:
        ext = [_sub(_mul(P[0], 2.0), P[1])] + P + [_sub(_mul(P[-1], 2.0), P[-2])]
        nseg = n - 1
    out, knots = [], []

    def tj(ti, a, b):
        return ti + max(1e-9, _len(_sub(b, a))) ** 0.5
    for s in range(nseg):
        p0, p1, p2, p3 = ext[s], ext[s + 1], ext[s + 2], ext[s + 3]
        t0 = 0.0
        t1 = tj(t0, p0, p1)
        t2 = tj(t1, p1, p2)
        t3 = tj(t2, p2, p3)
        knots.append(len(out))
        out.append(p1)
        for k in range(1, per_seg):
            t = t1 + (t2 - t1) * k / per_seg

            def L(pa, pb, ta, tb):
                return _add(_mul(pa, (tb - t) / (tb - ta)), _mul(pb, (t - ta) / (tb - ta)))
            a1, a2, a3 = L(p0, p1, t0, t1), L(p1, p2, t1, t2), L(p2, p3, t2, t3)
            b1, b2 = L(a1, a2, t0, t2), L(a2, a3, t1, t3)
            out.append(L(b1, b2, t1, t2))
    if not closed:
        knots.append(len(out))
        out.append(P[-1])
    return out, knots


def build_line(surf, clicks, closed=False, smooth=True):
    """The line over the surface through the clicked points. Returns (points, normals, knots):
    knots[i] is where click i is in the points. On a closed loop the last point is not the
    first again (the line runs from the last back to the first)."""
    if not clicks:
        return [], [], []
    on = [surf.closest(c) for c in clicks]
    P = [o[0] for o in on]
    N = [o[1] for o in on]
    if len(P) == 1:
        return P, N, [0]
    seeds, sknots = (catmull_rom(P, closed) if smooth and len(P) >= 3 else (P, list(range(len(P)))))
    snrm = []
    if seeds is not P:
        # pull the curve onto the surface, each bit facing about the way the clicks either side face
        k_of = {k: i for i, k in enumerate(sknots)}
        proj = []
        for j, s in enumerate(seeds):
            if j in k_of:
                proj.append((P[k_of[j]], N[k_of[j]]))
                continue
            i0 = max(i for i, k in enumerate(sknots) if k <= j)
            i1 = (i0 + 1) % len(P)
            t = (j - sknots[i0]) / float(((sknots[i0 + 1] if i0 + 1 < len(sknots) else len(seeds)) - sknots[i0]) or 1)
            ref = _unit(_lerp(N[i0], N[i1], t)) or N[i0]
            q, nq, _d = surf.closest(s, ref)
            proj.append((q, nq))
        seeds = [p for p, _n in proj]
        snrm = [n for _p, n in proj]
    else:
        snrm = list(N)
    outP, outN, knots = [seeds[0]], [snrm[0]], []
    kset = {k: i for i, k in enumerate(sknots)}
    if 0 in kset:
        knots.append(0)
    pairs = list(range(len(seeds) - 1)) + ([len(seeds) - 1] if closed else [])
    for j in pairs:
        j2 = (j + 1) % len(seeds)
        hp, hn = surface_hop(surf, seeds[j], snrm[j], seeds[j2], snrm[j2])
        if closed and j2 == 0:
            hp, hn = hp[:-1], hn[:-1]                       # don't come back onto the first point
            outP += hp[1:]
            outN += hn[1:]
            break
        outP += hp[1:]
        outN += hn[1:]
        if j2 in kset:
            knots.append(len(outP) - 1)
    return outP, outN, knots


# ---------------------------------------------------------------------------
# Wrap round: the ring round an object through one point
# ---------------------------------------------------------------------------
AXES = [("auto", "Work it out"), ("x", "Across X (red)"), ("y", "Across Y (green)"), ("z", "Across Z (blue)")]
_AXV = {"x": (1.0, 0.0, 0.0), "y": (0.0, 1.0, 0.0), "z": (0.0, 0.0, 1.0)}


def wrap_ring(surf, click, axis="auto", extra_axes=()):
    """The ring round the object through the clicked point, in the plane square to the axis
    (auto: whichever of X, Y, Z - or the object's own axes - gives the shortest ring through
    the point). Returns (points, normals, axis used) with the ring starting at the click, or None."""
    p, n, _d = surf.closest(click)
    if axis in _AXV:
        cands = [_AXV[axis]]
    else:
        cands = [_AXV["x"], _AXV["y"], _AXV["z"]] + [a for a in extra_axes if a is not None]
        cands = [c for c in cands if abs(_dot(c, n)) < 0.35] or cands
    best = None
    tol = 1e-5 * surf.diag + 1e-9
    for ax in cands:
        for ch in slice_chains(surf, p, ax):
            pts, nrm, closed = ch
            if not closed:
                continue
            loc = locate(pts, closed, p)
            if loc is None or loc[2] > tol:
                continue
            L = poly_length(pts, True)
            if best is None or L < best[0]:
                best = (L, ch, loc, ax)
    if best is None:
        return None
    _L, (pts, nrm, _c), (i, _t_, _dd, q), ax = best
    m = len(pts)
    # start at the click, and go round
    P = [q] + [pts[(i + 1 + k) % m] for k in range(m)]
    N = [n] + [nrm[(i + 1 + k) % m] for k in range(m)]
    if _len(_sub(P[-1], P[0])) < 1e-9:
        P, N = P[:-1], N[:-1]
    if len(P) > 1 and _len(_sub(P[1], P[0])) < 1e-9:
        P, N = [P[0]] + P[2:], [N[0]] + N[2:]
    return P, N, ax


# ---------------------------------------------------------------------------
# Where the parts go along the line
# ---------------------------------------------------------------------------
def cumulative(pts, closed):
    s = [0.0]
    for i in range(1, len(pts)):
        s.append(s[-1] + _len(_sub(pts[i], pts[i - 1])))
    total = s[-1] + (_len(_sub(pts[0], pts[-1])) if closed and len(pts) > 1 else 0.0)
    return s, total


def corner_stations(pts, closed, angle_deg):
    """Arc lengths of the corners: points where the line turns more than angle_deg."""
    s, _L = cumulative(pts, closed)
    m = len(pts)
    out = []
    lim = math.cos(math.radians(angle_deg))
    rng = range(m) if closed else range(1, m - 1)
    for i in rng:
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % m]
        u, v = _unit(_sub(b, a)), _unit(_sub(c, b))
        if u is None or v is None:
            continue
        if _dot(u, v) < lim:
            out.append(s[i])
    return out


def share_out(lengths, total):
    """How many gaps each stretch gets, total gaps in all, every stretch at least one, as even as can be."""
    k = len(lengths)
    total = max(total, k)
    L = sum(lengths) or 1.0
    n = [max(1, int(round(l / L * total))) for l in lengths]
    while sum(n) > total:
        j = max((i for i in range(k) if n[i] > 1), key=lambda i: n[i] / max(lengths[i], 1e-12))
        n[j] -= 1
    while sum(n) < total:
        j = max(range(k), key=lambda i: lengths[i] / n[i])
        n[j] += 1
    return n


def stations(total, closed, anchors, mode, count, pitch):
    """Arc lengths of the parts. anchors: arc lengths that must each get a part (clicked points,
    corners). mode 'count': count between the ends (open) or count in all (closed);
    'pitch': about pitch apart, fitted so they land on the ends and anchors.
    Returns (stations, smallest gap, biggest gap)."""
    if total <= 1e-12:
        return [0.0], 0.0, 0.0
    tol = total * 1e-6
    a = sorted(set(round(x, 12) for x in anchors if -tol <= x <= total + tol))
    a = [min(max(x, 0.0), total) for x in a]
    if closed:
        a = [x for x in a if x < total - tol] or [0.0]
        # round a loop the stretches run from anchor to anchor, the last one back round to the first
        bounds = a + [a[0] + total]
    else:
        bounds = sorted(set([0.0, total] + a))
    merged = [bounds[0]]
    for x in bounds[1:]:
        if x - merged[-1] > tol:
            merged.append(x)
        elif x == bounds[-1]:
            merged[-1] = x
    bounds = merged
    if len(bounds) < 2:
        bounds = [0.0, total]
    lens = [bounds[i + 1] - bounds[i] for i in range(len(bounds) - 1)]
    if mode == "pitch":
        n = [max(1, int(round(l / max(pitch, 1e-9)))) for l in lens]
    else:
        gaps = count + 1 if not closed else max(count, 2)
        n = share_out(lens, gaps)
    out, gaps = [], []
    for b0, l, k in zip(bounds, lens, n):
        for j in range(k):
            x = b0 + l * j / k
            out.append(x - total if closed and x >= total else x)
        gaps.append(l / k)
    if not closed:
        out.append(total)
    return out, min(gaps), max(gaps)


def point_at(pts, nrm, closed, s_cum, total, s):
    """(point, normal, direction) at arc length s along the line."""
    m = len(pts)
    if m == 1:
        return pts[0], nrm[0], (1.0, 0.0, 0.0)
    if closed:
        s = s % total if total > 0 else 0.0
    nseg = m if closed else m - 1
    import bisect
    i = max(0, min(nseg - 1, bisect.bisect_right(s_cum, s) - 1))
    a, b = pts[i], pts[(i + 1) % m]
    L = _len(_sub(b, a))
    t = 0.0 if L < 1e-15 else max(0.0, min(1.0, (s - s_cum[i]) / L))
    d = _unit(_sub(b, a))
    if d is None:
        for k in (i - 1, i + 1):
            if 0 <= k < nseg:
                d = _unit(_sub(pts[(k + 1) % m], pts[k]))
                if d:
                    break
    n = _unit(_lerp(nrm[i], nrm[(i + 1) % m], t)) or nrm[i]
    return _lerp(a, b, t), n, d or (1.0, 0.0, 0.0)


def station_frames(surf, pts, nrm, closed, st, flip=False, keep_on_line=False):
    """For each arc length: (origin, x, y, z) - z square out of the surface, x along the line.
    keep_on_line: a line of your own - the parts stay on it, only facing the surface under it."""
    s_cum, total = cumulative(pts, closed)
    pad = (0.005 * surf.diag + 1e-6) if surf is not None else 0.0
    out = []
    for s in st:
        p, n, d = point_at(pts, nrm, closed, s_cum, total, s)
        if surf is not None and len(surf):
            local = surf.near(np.asarray(p) - pad, np.asarray(p) + pad)
            q, nq, dist = (local if len(local) else surf).closest(p, n)
            if keep_on_line:
                if dist < 0.05 * surf.diag + 1e-7:
                    n = nq
            elif dist < 1e-4 * surf.diag + 1e-7:
                p, n = q, nq
        z = _mul(n, -1.0) if flip else n
        x = _unit(_sub(d, _mul(z, _dot(d, z)))) or _unit(_cross((0.0, 0.0, 1.0), z)) or (1.0, 0.0, 0.0)
        y = _cross(z, x)
        out.append((p, x, y, z))
    return out


def chain_segments(segs, tol=1e-7):
    """Joins line segments [(a, b)] end to end: [(points, closed)], longest first.
    Where three or more lines meet, a chain stops there."""
    def key(p):
        return (int(round(p[0] / tol)), int(round(p[1] / tol)), int(round(p[2] / tol)))
    segs = [(a, b) for a, b in segs if key(a) != key(b)]
    ends = {}
    for k, (a, b) in enumerate(segs):
        ends.setdefault(key(a), []).append(k)
        ends.setdefault(key(b), []).append(k)
    used = [False] * len(segs)

    def step(k, from_key):
        a, b = segs[k]
        return (b, key(b)) if key(a) == from_key else (a, key(a))

    def walk(k, kp):
        out = []
        while True:
            used[k] = True
            p, kp = step(k, kp)
            out.append(p)
            cand = [j for j in ends.get(kp, []) if not used[j]]
            if len(ends.get(kp, [])) != 2 or not cand:
                return out, kp
            k = cand[0]
    chains = []
    # start at loose ends and junctions first, so open lines come out whole
    order = sorted(range(len(segs)), key=lambda k: -max(len(ends[key(segs[k][0])]) != 2,
                                                          len(ends[key(segs[k][1])]) != 2))
    for k0 in order:
        if used[k0]:
            continue
        a, b = segs[k0]
        if len(ends[key(a)]) == 2 and len(ends[key(b)]) != 2:
            a, b = b, a                                   # walk away from the loose end
        used[k0] = True
        fwd, kend = [], key(b)
        cand = [j for j in ends.get(key(b), []) if not used[j]]
        if len(ends.get(key(b), [])) == 2 and cand:
            fwd, kend = walk(cand[0], key(b))
        closed = kend == key(a) and len(fwd) >= 2
        if closed:
            chains.append(([a, b] + fwd[:-1], True))
            continue
        back = []
        cand = [j for j in ends.get(key(a), []) if not used[j]]
        if len(ends.get(key(a), [])) == 2 and cand:
            back, _k = walk(cand[0], key(a))
        chains.append((list(reversed(back)) + [a, b] + fwd, False))
    chains.sort(key=lambda c: -poly_length(c[0], c[1]))
    return chains


def plane_normal(pts):
    """The way a flat outline faces (Newell), or straight up."""
    nx = ny = nz = 0.0
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    return _unit((nx, ny, nz)) or (0.0, 0.0, 1.0)


def line_normals(surf, pts, closed):
    """Which way is 'out' at each point of a line of your own: the surface under it, or, with no
    surface near, the way the outline faces."""
    fall = plane_normal(pts) if closed and len(pts) >= 3 else (0.0, 0.0, 1.0)
    out = []
    for p in pts:
        n = None
        if surf is not None and len(surf):
            q, nq, d = surf.closest(p)
            if d < 0.05 * surf.diag + 1e-7:
                n = nq
        out.append(n or fall)
    return out


def footprint(points, lo, hi, most=48):
    """The outline of the bottom of a part: (x, y) from the middle of its base, in its own axes -
    the corners nearest the bottom, the furthest out in each direction."""
    h = hi[2] - lo[2]
    cx, cy = (lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0
    low = [(p[0] - cx, p[1] - cy) for p in points if p[2] <= lo[2] + max(0.05 * h, 1e-9)]
    if not low:
        return [(0.0, 0.0)]
    bins = {}
    for x, y in low:
        b = int((math.atan2(y, x) + math.pi) / (2 * math.pi) * most) % most
        r = x * x + y * y
        if b not in bins or r > bins[b][0]:
            bins[b] = (r, (x, y))
    return [v[1] for v in bins.values()] + [(0.0, 0.0)]


def auto_sinks(surf, frames, foot, turn=0.0):
    """How far to sink each part so no gap is left under it: on a curve (round a boiler) its flat
    bottom only touches in the middle - this lets it down until every edge of it is in."""
    if surf is None or not len(surf):
        return [0.0] * len(frames)
    c, s = math.cos(math.radians(turn)), math.sin(math.radians(turn))
    reach = max((math.hypot(x, y) for x, y in foot), default=0.0)
    out = []
    for o, x, y, z in frames:
        xr = _add(_mul(x, c), _mul(y, s))
        yr = _add(_mul(x, -s), _mul(y, c))
        pad = reach * 1.5 + 1e-6
        local = surf.near(np.asarray(o) - pad, np.asarray(o) + pad)
        if not len(local):
            out.append(0.0)
            continue
        worst = 0.0
        for u, v in foot:
            w = _add(o, _add(_mul(xr, u), _mul(yr, v)))
            q, _n, d = local.closest(w, z)
            diff = _sub(w, q)
            along = _dot(diff, z)
            side = _len(_sub(diff, _mul(z, along)))
            if along > 0 and side <= 0.25 * _len(diff) + 1e-9:     # the surface is under it, not off an edge
                worst = max(worst, along)
        out.append(worst)
    return out


def side_frames(surf, frames, offset=0.0, tilt=0.0, other=False, stagger=False):
    """Sets each part to one side of the line: moved sideways off it by offset (metres, + to the
    left going along the line, - to the right) and still standing on the surface there; turned
    half round to face the other side (other); leaning over by tilt degrees, turning about the
    line like a hinge. stagger: every other part goes the other way - a zig-zag row."""
    if not (offset or tilt or other or stagger):
        return list(frames)
    c, s = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    out = []
    for i, (o, x, y, z) in enumerate(frames):
        flip = bool(other) != bool(stagger and i % 2 == 1)
        sgn = -1.0 if flip else 1.0
        if offset:
            p = _add(o, _mul(y, offset * sgn))
            n = z
            if surf is not None and len(surf):
                pad = abs(offset) * 0.5 + 0.005 * surf.diag + 1e-6
                local = surf.near(np.asarray(p) - pad, np.asarray(p) + pad)
                q, nq, d = (local if len(local) else surf).closest(p, z)
                if d < abs(offset) + 0.01 * surf.diag:
                    p, n = q, nq
            x = _unit(_sub(x, _mul(n, _dot(x, n)))) or x
            z = n
            y = _cross(z, x)
            o = p
        if flip:
            x, y = _mul(x, -1.0), _mul(y, -1.0)
        if tilt:
            y, z = _add(_mul(y, c), _mul(z, s)), _add(_mul(y, -s), _mul(z, c))
        out.append((o, x, y, z))
    return out


# ---------------------------------------------------------------------------
# 4 x 4 matrices as plain lists (row by row) - the same as 3D Find & Replace
# ---------------------------------------------------------------------------
def m_ident():
    return [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def m_mul(a, b):
    return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)] for r in range(4)]


def m_trans(x, y, z):
    m = m_ident()
    m[0][3], m[1][3], m[2][3] = float(x), float(y), float(z)
    return m


def m_rot_z(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [[c, -s, 0.0, 0.0], [s, c, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def m_apply(m, p):
    return tuple(m[r][0] * p[0] + m[r][1] * p[1] + m[r][2] * p[2] + m[r][3] for r in range(3))


def m_vec(m, v):
    return tuple(m[r][0] * v[0] + m[r][1] * v[1] + m[r][2] * v[2] for r in range(3))


def m_inv(m):
    """Inverse of an affine 4 x 4."""
    a = [row[:3] for row in m[:3]]
    det = (a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
           - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
           + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]))
    if abs(det) < 1e-30:
        raise ValueError("a placement squashed flat")
    inv = [[0.0] * 3 for _ in range(3)]
    for r in range(3):
        for c in range(3):
            r1, r2 = [i for i in range(3) if i != c]
            c1, c2 = [i for i in range(3) if i != r]
            minor = a[r1][c1] * a[r2][c2] - a[r1][c2] * a[r2][c1]
            inv[r][c] = ((-1) ** (r + c)) * minor / det
    t = [m[0][3], m[1][3], m[2][3]]
    it = [-(inv[r][0] * t[0] + inv[r][1] * t[1] + inv[r][2] * t[2]) for r in range(3)]
    return [inv[0] + [it[0]], inv[1] + [it[1]], inv[2] + [it[2]], [0.0, 0.0, 0.0, 1.0]]


def m_frame(o, x, y, z):
    return [[x[0], y[0], z[0], o[0]], [x[1], y[1], z[1], o[1]], [x[2], y[2], z[2], o[2]],
            [0.0, 0.0, 0.0, 1.0]]


def m_from_q(q):
    if q is None:
        return m_ident()
    d = list(q.data())                                 # column by column
    return [[float(d[c * 4 + r]) for c in range(4)] for r in range(4)]


def m_to_q(m):
    return QMatrix4x4(*[float(m[r][c]) for r in range(4) for c in range(4)])


def placement(frame, base, source_axes, turn=0.0, sink=0.0):
    """The xform that stands a part (base: the middle of its bottom, in its own axes) on the
    station frame (origin, x, y, z), turned about its up axis and sunk into the surface."""
    o, x, y, z = frame
    m = m_frame(o, x, y, z)
    if turn:
        m = m_mul(m, m_rot_z(turn))
    if sink:
        m = m_mul(m, m_trans(0.0, 0.0, -sink))
    m = m_mul(m, m_trans(-base[0], -base[1], -base[2]))
    return m_mul(m, m_inv(source_axes))


# ---------------------------------------------------------------------------
# The part: its corners, own axes and the box it fits in (as 3D Find & Replace reads them)
# ---------------------------------------------------------------------------
def _mesh_points(mesh):
    try:
        from core.group import _local_points
        arr = _local_points(mesh)
        if arr is not None:
            return [(float(p[0]), float(p[1]), float(p[2])) for p in arr]
    except Exception:
        pass
    out = []
    for v in list(getattr(mesh, 'vertices', None) or []):
        p = getattr(v, 'position', v)
        try:
            out.append((float(p.x()), float(p.y()), float(p.z())))
        except Exception:
            pass
    return out


def _iter_placements(group, base=None):
    try:
        from core.group import iter_placements
        yield from iter_placements(group, base)
        return
    except ImportError:
        pass
    m = getattr(group, 'xform', None)
    if base is not None:
        m = base if m is None else base * m
    yield group, m
    for ch in getattr(group, 'children', None) or ():
        yield from _iter_placements(ch, m)


def own_points(g):
    pts = list(_mesh_points(g.mesh))
    for ch in getattr(g, 'children', None) or ():
        for pg, q in _iter_placements(ch):
            m = m_from_q(q) if q is not None else None
            for p in _mesh_points(pg.mesh):
                pts.append(m_apply(m, p) if m else p)
    return pts


def axes_of(g):
    a = getattr(g, 'axes', None)
    return m_from_q(a) if a is not None else m_ident()


def local_box(g):
    """(lo, hi): the box the part fits in, along its own axes."""
    inv = m_inv(axes_of(g))
    pts = [m_apply(inv, p) for p in own_points(g)]
    if not pts:
        return (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    return (tuple(min(p[k] for p in pts) for k in range(3)),
            tuple(max(p[k] for p in pts) for k in range(3)))


def base_centre(box):
    lo, hi = box
    return ((lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0, lo[2])


# ---------------------------------------------------------------------------
# The parts library - shared with 3D Find & Replace (read here, edited there)
# ---------------------------------------------------------------------------
LIBRARY_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_eddy_parts.json")


def _ring(n, r, z, rot=0.0):
    return [(r * math.cos(rot + 2 * math.pi * i / n), r * math.sin(rot + 2 * math.pi * i / n), z)
            for i in range(n)]


def hex_r(across_flats):
    return across_flats / (2.0 * math.cos(math.pi / 6.0))


def inradius(n, r):
    return r * math.cos(math.pi / n)


def solid_faces(tiers, dome=None):
    """A closed solid of upright prisms stacked one on another, with an optional dome on top
    (the same as 3D Find & Replace makes its parts)."""
    faces = []

    def down(loop):
        return list(reversed(loop))
    t0 = tiers[0] if tiers else None
    first = (t0[0], t0[1], t0[2], t0[3]) if t0 else (dome[0], dome[1], 0.0, dome[2])
    faces.append((down(_ring(first[0], first[1], first[3], first[2])), []))
    for i, (n, r, rot, z0, z1) in enumerate(tiers):
        b, t = _ring(n, r, z0, rot), _ring(n, r, z1, rot)
        for k in range(n):
            faces.append(([b[k], b[(k + 1) % n], t[(k + 1) % n], t[k]], []))
        if i + 1 < len(tiers):
            nn, rr, rrot, _a, _b = tiers[i + 1]
            nxt = (nn, rr, rrot)
        elif dome is not None:
            nxt = (dome[0], dome[1], 0.0)
        else:
            faces.append((t, []))
            continue
        lo_ring = _ring(n, r, z1, rot)
        hi_ring = _ring(nxt[0], nxt[1], z1, nxt[2])
        if inradius(nxt[0], nxt[1]) <= inradius(n, r):
            faces.append((lo_ring, [down(hi_ring)]))
        else:
            faces.append((down(hi_ring), [lo_ring]))
    if dome is not None:
        n, r, z0, h, rings = dome
        rings = max(1, int(rings))
        prev = _ring(n, r, z0)
        for j in range(1, rings):
            a = (math.pi / 2.0) * j / rings
            cur = _ring(n, r * math.cos(a), z0 + h * math.sin(a))
            for k in range(n):
                faces.append(([prev[k], prev[(k + 1) % n], cur[(k + 1) % n], cur[k]], []))
            prev = cur
        apex = (0.0, 0.0, z0 + h)
        for k in range(n):
            faces.append(([prev[k], prev[(k + 1) % n], apex], []))
    return faces


def part_faces(shape, v):
    n = max(6, int(v.get('sides', 16)))
    if shape == "marker":
        return solid_faces([(6, hex_r(v['af']), 0.0, 0.0, v['h'])])
    if shape == "rivet":
        tiers = []
        if v.get('shank', 0) > 1e-9:
            tiers.append((n, v['shank_d'] / 2.0 / math.cos(math.pi / n), 0.0, -v['shank'], 0.0))
        return solid_faces(tiers, dome=(n, v['d'] / 2.0, 0.0, v['h'], max(2, n // 4)))
    tiers = []
    z = 0.0
    if v.get('washer_t', 0) > 1e-9:
        tiers.append((n, v['washer_d'] / 2.0, 0.0, z, z + v['washer_t']))
        z += v['washer_t']
    tiers.append((6, hex_r(v['af']), 0.0, z, z + v['h']))
    z += v['h']
    if shape == "nut" and v.get('end', 0) > 1e-9:
        tiers.append((n, v['bolt_d'] / 2.0, 0.0, z, z + v['end']))
    return solid_faces(tiers)


def _shape_part(pid, name, shape, sides=12, **mm):
    return dict(id=pid, kind="shape", name=name, shape=shape, sides=sides, sizes=mm)


def default_library():
    """Used until 3D Find & Replace has saved a library of your own."""
    rivets = [_shape_part("std-rivet-%d" % d, "Snap rivet %d mm" % d, "rivet", 12 if d < 25 else 14,
                          d=round(d * 1.75), h=round(d * 0.7), shank=0.0, shank_d=float(d))
              for d in (16, 19, 22, 25)]
    bolts = [_shape_part("std-bolt-%d" % m, "Bolt head M%d" % m, "bolt", 12, af=af, h=head,
                         washer_d=washer, washer_t=0.0)
             for m, af, head, washer in ((12, 18.0, 7.5, 24.0), (16, 24.0, 10.0, 30.0),
                                         (20, 30.0, 12.5, 37.0), (24, 36.0, 15.0, 44.0))]
    return {"tabs": [
        {"name": "Markers", "parts": [_shape_part("std-marker-rivet", "Marker - rivet", "marker", af=30.0, h=2.0),
                                      _shape_part("std-marker-bolt", "Marker - bolt", "marker", af=40.0, h=2.0)]},
        {"name": "Rivets", "parts": rivets},
        {"name": "Bolts & nuts", "parts": bolts},
    ]}


def load_library():
    try:
        with open(LIBRARY_FILE, "r", encoding="utf-8") as f:
            lib = json.load(f)
        if isinstance(lib, dict) and isinstance(lib.get("tabs"), list) and lib["tabs"]:
            return lib
    except Exception:
        pass
    return default_library()


def entry_polys(entry):
    if entry.get("kind") == "shape":
        v = {k: float(x) / MM for k, x in (entry.get("sizes") or {}).items()}
        for k in ('af', 'd', 'h', 'shank', 'shank_d', 'washer_d', 'washer_t', 'bolt_d', 'end'):
            v.setdefault(k, 0.0)
        v['sides'] = int(entry.get("sides", 12))
        return part_faces(entry["shape"], v)
    out = []
    for f in entry.get("faces") or []:
        out.append(([tuple(p) for p in f[0]], [[tuple(p) for p in h] for h in (f[1] if len(f) > 1 else [])]))
    return out


def build_definition(entry):
    """A new component (no turn, at the origin) holding the library part, tagged with its id
    the way 3D Find & Replace tags them, so it knows the part too."""
    from core.mesh import Mesh
    from core.group import Group
    mesh = Mesh()
    colours = entry.get("colours") or {}
    for i, (outline, holes) in enumerate(entry_polys(entry)):
        f = mesh.add_face([QVector3D(*p) for p in outline],
                          [[QVector3D(*p) for p in h] for h in holes] or None)
        c = colours.get(str(i))
        if c is not None:
            try:
                f.attrs["color"] = tuple(c) if isinstance(c, list) else c
            except Exception:
                pass
    g = Group(mesh, name=entry.get("name") or "Part")
    g.xform = QMatrix4x4()
    g.component = True
    try:
        g.ext = {EXT_KEY: {"id": entry.get("id")}}
    except Exception:
        pass
    return g


# ---------------------------------------------------------------------------
# Reading the model
# ---------------------------------------------------------------------------
def _is_face(e):
    return hasattr(e, 'loop') or 'face' in type(e).__name__.lower()


def _is_group(e):
    return (not _is_face(e)) and getattr(e, 'mesh', None) is not None


def _is_row(g):
    ext = getattr(g, 'ext', None)
    return isinstance(ext, dict) and isinstance(ext.get(EXT_TAG), dict)


def _qv(p):
    return (float(p.x()), float(p.y()), float(p.z()))


def _face_tris(f, m=None):
    """A face's triangles (and its normal) in model space, m the placement (rows) or None."""
    try:
        tris = f.triangulate()
        n = _qv(f.normal())
    except Exception:
        return [], None
    out = []
    for a, b, c in tris:
        pa, pb, pc = _qv(a), _qv(b), _qv(c)
        if m is not None:
            pa, pb, pc = m_apply(m, pa), m_apply(m, pb), m_apply(m, pc)
        out.append((pa, pb, pc))
    if m is not None:
        n = m_vec(m, n)
        if out:                                  # keep facing out, whatever the placement did
            tn = _cross(_sub(out[0][1], out[0][0]), _sub(out[0][2], out[0][0]))
            if _dot(tn, n) < 0:
                n = _mul(n, -1.0)
    return out, n


def _pos(v):
    if v is None:
        return None
    p = getattr(v, 'position', v)
    try:
        return (float(p.x()), float(p.y()), float(p.z()))
    except Exception:
        try:
            return (float(p[0]), float(p[1]), float(p[2]))
        except Exception:
            return None


def edge_ends(e):
    """A line's two ends as (x, y, z), or None if it isn't a line."""
    for a, b in (('a', 'b'), ('v0', 'v1'), ('v1', 'v2'), ('start', 'end')):
        try:
            p, q = _pos(getattr(e, a, None)), _pos(getattr(e, b, None))
        except Exception:
            continue
        if p is not None and q is not None:
            return p, q
    return None


def selected_lines(scene, selection):
    """Your own line from the selection: the lines (edges) you've selected, joined end to end. With
    a group selected instead, the loose lines in it (lines not round any face) - so a line you've
    drawn and made into a group, or drawn inside the boiler's group, works too.
    [(points, closed)] in model space."""
    sel = list(selection or [])
    m0 = ctx_world(scene)
    segs = []
    for e in sel:
        if _is_face(e) or _is_group(e):
            continue
        ends = edge_ends(e)
        if ends:
            a, b = ends
            if m0 is not None:
                a, b = m_apply(m0, a), m_apply(m0, b)
            segs.append((a, b))
    if not segs:
        for g in sel:
            if not _is_group(g) or _is_row(g):
                continue
            for pg, q in _iter_placements(g):
                m = m_from_q(q) if q is not None else None
                if m0 is not None:
                    m = m0 if m is None else m_mul(m0, m)
                for e in list(getattr(pg.mesh, 'edges', None) or []):
                    if getattr(e, 'faces', None):
                        continue
                    ends = edge_ends(e)
                    if ends:
                        a, b = ends
                        segs.append((m_apply(m, a), m_apply(m, b)) if m is not None else (a, b))
    if not segs:
        return []
    span = max(_len(_sub(b, a)) for a, b in segs)
    return chain_segments(segs, tol=max(1e-9, span * 1e-7))


def _plane_basis(n):
    u = _unit(_cross(n, (0.0, 0.0, 1.0))) or _unit(_cross(n, (1.0, 0.0, 0.0)))
    return u, _cross(n, u)


def _inside_2d(pt, loop):
    x, y = pt
    inside = False
    j = len(loop) - 1
    for i in range(len(loop)):
        xi, yi = loop[i]
        xj, yj = loop[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-30) + xi:
            inside = not inside
        j = i
    return inside


def face_boundary(faces):
    """The edge of the region the faces make (lines only one of them has - so the joins between
    the faces of a curved panel drop out, and a window hole counts as an edge), each line with the
    way into the region: [(a, b, inward)]. faces: [(outline, [holes], normal)] in model space."""
    found = {}
    tol = 1e-9

    def key(p):
        return (int(round(p[0] / tol)), int(round(p[1] / tol)), int(round(p[2] / tol)))
    for outer, holes, n in faces:
        u, v = _plane_basis(n)
        o = outer[0]

        def flat(p):
            d = _sub(p, o)
            return (_dot(d, u), _dot(d, v))
        f_outer = [flat(p) for p in outer]
        f_holes = [[flat(p) for p in h] for h in holes]

        def inside(p):
            q = flat(p)
            return _inside_2d(q, f_outer) and not any(_inside_2d(q, h) for h in f_holes)
        for loop in [outer] + list(holes):
            for i in range(len(loop)):
                a, b = loop[i], loop[(i + 1) % len(loop)]
                t = _unit(_sub(b, a))
                if t is None:
                    continue
                inward = _unit(_cross(n, t)) or (0.0, 0.0, 0.0)
                L = _len(_sub(b, a))
                probe = _add(_lerp(a, b, 0.5), _mul(inward, max(L * 1e-3, 1e-7)))
                if not inside(probe):
                    inward = _mul(inward, -1.0)
                k = frozenset((key(a), key(b)))
                found.setdefault(k, []).append((a, b, inward))
    return [v[0] for v in found.values() if len(v) == 1]


def inset_chains(boundary, inset, surf=None):
    """The edge of the faces, moved in by inset (metres) - mitred at the corners - and kept on the
    surface. [(points, closed)]"""
    if not boundary:
        return []
    span = max(_len(_sub(b, a)) for a, b, _i in boundary)
    tol = max(1e-9, span * 1e-7)

    def key(p):
        return (int(round(p[0] / tol)), int(round(p[1] / tol)), int(round(p[2] / tol)))
    inward = {frozenset((key(a), key(b))): w for a, b, w in boundary}
    out = []
    for pts, closed in chain_segments([(a, b) for a, b, _w in boundary], tol=tol):
        if abs(inset) < 1e-12:
            out.append((pts, closed))
            continue
        m = len(pts)
        moved = []
        for i in range(m):
            wp = inward.get(frozenset((key(pts[i - 1]), key(pts[i])))) if (i > 0 or closed) else None
            wn = inward.get(frozenset((key(pts[i]), key(pts[(i + 1) % m])))) if (i < m - 1 or closed) else None
            a, b = wp or wn, wn or wp
            if a is None:
                moved.append(pts[i])
                continue
            w = _unit(_add(a, b)) or b
            k = max(_dot(w, b), 0.25)                          # a sharp corner goes in at most 4 x further
            q = _add(pts[i], _mul(w, inset / k))
            if surf is not None and len(surf):
                q = surf.closest(q, None)[0]
            moved.append(q)
        out.append((moved, closed))
    return out


def _face_near(f, m, box):
    lo, hi = box
    pts = [_pos(v) for v in list(getattr(f, 'vertices', None) or [])]
    pts = [m_apply(m, p) if m is not None else p for p in pts if p is not None]
    if not pts:
        return False
    return all(min(p[k] for p in pts) <= hi[k] and max(p[k] for p in pts) >= lo[k] for k in range(3))


def scene_roots(scene):
    """The groups at the level you're working in, and where that level sits in the model (rows,
    or None at the top): inside a group you've opened, its geometry is in its own space."""
    ctx = getattr(scene, 'edit_group', None)
    if ctx is not None and getattr(ctx, 'children', None) is not None:
        return list(ctx.children or []), ctx_world(scene)
    return list(getattr(scene, 'groups', None) or []), None


def ctx_world(scene):
    """Where the open group's own space sits in the model (rows), or None."""
    ctx = getattr(scene, 'edit_group', None)
    if ctx is None:
        return None
    for top in list(getattr(scene, 'groups', None) or []):
        for g, m in _iter_placements(top):
            if g is ctx:
                return m_from_q(m) if m is not None else None
    x = getattr(ctx, 'xform', None)
    return m_from_q(x) if x is not None else None


def _loop_pts(vs, m=None):
    pts = [_pos(v) for v in list(vs or [])]
    pts = [p for p in pts if p is not None]
    return [m_apply(m, p) for p in pts] if m is not None else pts


def gather_surface(scene, selection, limit=400000, within=None):
    """The surface the line goes over: the selected objects and faces, or everything shown if
    nothing is selected. Returns (Surface, what it is, uids of the objects, their own axes)."""
    sel = list(selection or [])
    sel_groups = [e for e in sel if _is_group(e) and not _is_row(e)]
    sel_faces = [e for e in sel if _is_face(e)]
    everything = not sel_groups and not sel_faces
    roots, ctx_x = scene_roots(scene)
    tris, nrms, uids, axes = [], [], [], []
    picked = set(id(g) for g in sel_groups)

    def walk(g, base, inside):
        if getattr(g, 'hidden', False) or _is_row(g):
            return
        inside = inside or id(g) in picked
        x = getattr(g, 'xform', None)
        m = base if x is None else (m_from_q(x) if base is None else m_mul(base, m_from_q(x)))
        if inside:
            for f in list(getattr(g.mesh, 'faces', None) or []):
                if within is not None and not _face_near(f, m, within):
                    continue
                t, n = _face_tris(f, m)
                if n is not None:
                    tris.extend(t)
                    nrms.extend([n] * len(t))
                if len(tris) > limit:
                    raise RuntimeError("too many faces")
        for ch in getattr(g, 'children', None) or ():
            walk(ch, m, inside)
    base = ctx_x
    for r in roots:
        walk(r, base, everything)
    for g in sel_groups:
        uid = getattr(g, 'uid', None)
        if uid:
            uids.append(uid)
        a = getattr(g, 'axes', None)
        if a is not None:
            m = m_mul(m_from_q(getattr(g, 'xform', None)) if getattr(g, 'xform', None) is not None else m_ident(),
                      m_from_q(a))
            for k in range(3):
                v = _unit(m_vec(m, [(1, 0, 0), (0, 1, 0), (0, 0, 1)][k]))
                if v:
                    axes.append(v)
    for f in sel_faces:
        t, n = _face_tris(f, ctx_x)
        if n is not None:
            tris.extend(t)
            nrms.extend([n] * len(t))
    if everything:
        lm = getattr(scene, 'loose_mesh', None) or getattr(scene, 'mesh', None)
        for f in list(getattr(lm, 'faces', None) or []):
            if within is not None and not _face_near(f, ctx_x, within):
                continue
            t, n = _face_tris(f, ctx_x)
            if n is not None:
                tris.extend(t)
                nrms.extend([n] * len(t))
    if everything:
        what = "everything shown (nothing selected)"
    else:
        bits = []
        if sel_groups:
            nm = [str(getattr(g, 'name', '') or 'object') for g in sel_groups]
            bits.append(nm[0] if len(nm) == 1 else "%d objects" % len(nm))
        if sel_faces:
            bits.append("1 face" if len(sel_faces) == 1 else "%d faces" % len(sel_faces))
        what = " and ".join(bits)
    return Surface(tris, nrms), what, uids, axes


def find_by_uids(scene, uids):
    roots, _x = scene_roots(scene)
    want = set(uids or [])
    out = []
    for r in roots:
        for g, _m in _iter_placements(r):
            if getattr(g, 'uid', None) in want:
                out.append(g)
    return out


def find_definition(scene, entry):
    """A copy already in the model of this library part, or None."""
    roots, _x = scene_roots(scene)
    pool = []
    for r in list(getattr(scene, 'groups', None) or []) + roots:
        for g, _m in _iter_placements(r):
            pool.append(g)
    pool += list(getattr(scene, 'kept_components', None) or [])
    for g in pool:
        ext = getattr(g, 'ext', None)
        if isinstance(ext, dict) and (ext.get(EXT_KEY) or {}).get("id") == entry.get("id") \
                and getattr(g, 'xform', None) is not None:
            return g
    return None


def _command_base():
    try:
        from core.history import Command
        return Command
    except Exception:
        return object


class ReplaceRowCommand(_command_base()):
    """Swaps an old row for its new one in the same place in its list (one Undo)."""
    keeps_paint = False
    keeps_groups = True

    def __init__(self, owner, old, new):
        self.owner, self.old, self.new = owner, old, new

    def do(self, scene):
        i = self.owner.index(self.old)
        self.owner[i] = self.new
        try:
            scene.selection.discard(self.old)
            scene.selection.clear()
            scene.selection.add(self.new)
        except Exception:
            pass
        scene.version += 1

    def undo(self, scene):
        if self.new in self.owner:
            self.owner[self.owner.index(self.new)] = self.old
        try:
            scene.selection.discard(self.new)
        except Exception:
            pass
        scene.version += 1


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


EDDY_TIPS = {
    "part": "What goes along the line: a part from your parts library (the one 3D Find & Replace "
            "keeps - markers, rivets, bolts and your own), or a component you've selected in the model.",
    "from the library": "A part from your parts library - the one 3D Find & Replace keeps (markers, rivets, "
                        "bolts and your own).",
    "from the model": "A component from this model, picked with Pick part from selection. It stays the part "
                      "until you pick another - selecting the boiler after doesn't change it.",
    "pick part from selection": "Select your rivet (or any component) in the model, then press this. It becomes "
                                "the part and stays the part - you can then select the boiler, a face or a line "
                                "and it won't change. It stands on the middle of its bottom, its own blue (Z) "
                                "axis square out of the surface.",
    "round selected face": "Select a face (Shift-click for more - a curved panel's faces together count as one), "
                           "press this, and the parts go round its edge, moved in by Inset from edge. A window "
                           "hole in the face gets a ring of its own round it.",
    "inset from edge": "How far in from the edge of the face the line runs, in real mm. Change it and the line "
                       "moves straight away. 0 = on the edge itself.",
    "draw line": "Select the object the line goes over first (a boiler, a cab side), then press this and "
                 "click points on its surface. Backspace takes the last point off; Enter, a double-click "
                 "or Finish ends the line. Nothing selected: it goes over anything you click on.",
    "wrap round": "Select a round, square or many-sided object (a boiler, a chimney, a column), press this "
                  "and click once on it: the line rings it all the way round through that point.",
    "finish": "Ends the line you're drawing (the same as Enter or a double-click).",
    "clear": "Throws the line away, to start again.",
    "smooth curve through the clicks": "Ticked: a smooth curve through your points, following the surface. "
                                       "Unticked: straight from one point to the next over the surface - best "
                                       "for square and hex shapes.",
    "closed loop": "Joins the last point back to the first, so the line goes all the way round. The parts "
                   "are shared evenly round it, with none doubled where the ends meet.",
    "ring goes round": "Which way the Wrap round ring goes. Work it out picks the shortest ring through the "
                       "point - round a boiler, not along it.",
    "how many": "Open line: how many go between the two end ones. Closed loop: how many in all, round it.",
    "pitch": "The gap between centres, in real mm. It's fitted so the ends (and the points and corners "
             "you've asked for) land exactly - the window says the gap it used.",
    "on every point you clicked": "A part on each point you clicked, with the rest spaced evenly between them.",
    "on every corner": "A part on every corner the line goes round (on a square or hex column, say), with the "
                       "rest spaced evenly between. A corner is where it turns more than this.",
    "turn": "Turns every part about its own up axis - to set the flats of a bolt head square to the line.",
    "sink in until there's no gap under it": "On a curve (round a boiler) a flat-bottomed part only touches in "
                                             "the middle, leaving a gap under its edges. Ticked, each one is let "
                                             "down into the surface until every edge is in, so nothing shows "
                                             "behind it and it prints joined on. Worked out for each part, so "
                                             "tighter curves sink more.",
    "sink in a bit more": "Sets each part this much further into the surface (real mm), on top of the no-gap "
                          "amount - 0 for none.",
    "use selected line": "Puts the parts along a line of your own: select the lines (an outline you've offset "
                         "with the Offset tool, an arc, a curve you've drawn) and press this. Joined lines are "
                         "followed end to end; a closed outline goes all the way round. Select a face instead to "
                         "go round its outline. The parts stay on your line and face out of the surface under it.",
    "stand on the back of the surface (inside)": "Stands the parts on the back of the surface - inside a tank "
                                                 "or cab, or where the faces are back to front.",
    "off the line": "Moves every part sideways off the line by this much (real mm), still standing on the "
                    "surface: + to the left going along the line, - to the right. With Staggered, they go "
                    "this far each side - a zig-zag double row.",
    "tilt about the line": "Leans every part over by this angle, turning about the line like a hinge - for a "
                           "part that should lean out, not stand straight up.",
    "other side of the line": "Turns every part half round, so a part that sits to one side of the line (a "
                              "bracket, an angle, a strap end) sits on the other side instead. Also swaps the "
                              "side Off the line and Tilt go to.",
    "every other one on the other side (staggered)": "Every other part goes to the other side of the line - "
                                                     "turned half round, the other way off the line and "
                                                     "leaning the other way. With Off the line, a staggered "
                                                     "(zig-zag) double row of rivets.",
    "edit selected row": "Select a row this plugin made, and press this: its line, part and spacing come "
                         "back here to change. Place then puts the new row in its place.",
    "place": "Puts the parts along the line, as one group (one Undo).",
}
EDDY_TIPS_END = None


def _no_wheel(combo):
    """A list box the mouse wheel only turns once you've clicked in it - so scrolling over the
    window can't change the part behind your back."""
    try:
        from PySide6.QtCore import QObject, QEvent, Qt

        class _F(QObject):
            def eventFilter(self, obj, ev):
                if ev.type() == QEvent.Type.Wheel and not obj.hasFocus():
                    ev.ignore()
                    return True
                return False
        combo.setFocusPolicy(Qt.StrongFocus)
        f = _F(combo)
        combo.installEventFilter(f)
        combo._no_wheel = f
    except Exception:
        pass


def make_line_tool(dlg):
    """The clicking tool, made here (not at module level, so it gets no menu entry of its own)."""
    from PySide6.QtCore import Qt

    class _LineTool(Tool):
        name = "Place Along Line - click points"
        shortcut = None
        uses_snap = True
        wireframe_color = (0.95, 0.45, 0.10, 1.0)

        def __init__(self):
            self.hover = None

        def on_activate(self, viewport):
            self.hover = None

        def on_deactivate(self, viewport):
            self.hover = None
            dlg.tool_gone(self)

        def on_hover(self, ctx):
            try:
                self.hover = _qv(ctx.world)
                ctx.viewport.update()
            except Exception:
                pass

        def on_click(self, ctx):
            dlg.clicked(_qv(ctx.world))

        def on_double_click(self, ctx):
            dlg.finish()

        def on_key(self, viewport, key, modifiers):
            if key == Qt.Key_Escape:
                dlg.stop_tool()
                return True
            if key in (Qt.Key_Return, Qt.Key_Enter):
                dlg.finish()
                return True
            if key == Qt.Key_Backspace:
                dlg.take_last()
                return True
            return False

        def status_clause(self):
            return dlg.status_text()

        def rubber_band_lines(self):
            try:
                return dlg.preview_lines(self.hover)
            except Exception:
                return []
    return _LineTool()


class PlaceAlongDialog(QDialog):
    # remembered while IngeTrazo is open
    state = dict(part=None, mode="count", count=10, pitch=50.0, on_clicks=True, on_corners=True,
                 corner_deg=40.0, smooth=True, closed=False, axis=0, turn=0.0, sink=0.0, flip=False,
                 nogap=True, inset=10.0, offset=0.0, tilt=0.0, other=False, stagger=False)

    def __init__(self, viewport, tool):
        super().__init__(viewport)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.lib = load_library()
        self.model_part = None          # a component picked from the model (it stays until you pick another)
        self.model_part_from = None     # the uid of the object it was picked from
        self._defs = {}                 # library part id -> its definition, made once
        self.surf = None                # the surface the line goes over
        self.surf_what = ""
        self.surf_uids, self.surf_axes = [], []
        self.kind = None                # 'line' or 'wrap'
        self.clicks = []                # what was clicked (model space)
        self.lines = []                 # [(points, normals, knots, closed)] once worked out
        self.chains = []                # a line of your own: [(points, closed)]
        self.boundary = []              # round a face: its edge lines, each with the way in
        self.sinks = []                 # how far each part is let down, worked out on Place
        self.drawing = False
        self.ended = False
        self.wrap_axis = None
        self.pick_tool = None
        self.editing = None             # the row being changed
        self.frames = []
        self._part, self._box = None, None
        lay = QVBoxLayout(self)

        intro = QLabel("Put rivets, bolts or any part along a line over a surface - a boiler, a cab side, "
                       "round a chimney. Every part stands square on the surface.")
        intro.setWordWrap(True)
        lay.addWidget(intro)

        # 1. the part
        box1 = QGroupBox("1. The part - what gets placed (a rivet, a bolt)")
        f1 = QFormLayout(box1)
        self.rb_lib = QRadioButton("From the library:")
        self.rb_model = QRadioButton("From the model:")
        self._part_group_btns = QButtonGroup(self)
        self._part_group_btns.addButton(self.rb_lib)
        self._part_group_btns.addButton(self.rb_model)
        self.cb_part = QComboBox()
        self.cb_part.setMinimumWidth(220)
        _no_wheel(self.cb_part)
        f1.addRow(self.rb_lib, self.cb_part)
        prow = QHBoxLayout()
        self.lbl_model_part = QLabel("(none picked)")
        prow.addWidget(self.lbl_model_part, 1)
        self.b_use = QPushButton("Pick part from selection")
        prow.addWidget(self.b_use)
        f1.addRow(self.rb_model, prow)
        self.lbl_part = QLabel("-")
        self.lbl_part.setWordWrap(True)
        self.lbl_part.setStyleSheet("color: gray;")
        f1.addRow(self.lbl_part)
        lay.addWidget(box1)

        # 2. the line
        box2 = QGroupBox("2. The line - where it goes (select the boiler, a face or a line first)")
        v2 = QVBoxLayout(box2)
        r2 = QHBoxLayout()
        self.b_draw = QPushButton("Draw line")
        self.b_wrap = QPushButton("Wrap round")
        self.b_own = QPushButton("Use selected line")
        for b in (self.b_draw, self.b_wrap, self.b_own):
            r2.addWidget(b)
        v2.addLayout(r2)
        r2d = QHBoxLayout()
        self.b_face = QPushButton("Round selected face")
        r2d.addWidget(self.b_face)
        r2d.addWidget(QLabel("Inset from edge:"))
        self.sp_inset = QDoubleSpinBox()
        self.sp_inset.setRange(-10000.0, 100000.0)
        self.sp_inset.setDecimals(1)
        self.sp_inset.setSuffix(" mm")
        r2d.addWidget(self.sp_inset)
        r2d.addStretch(1)
        v2.addLayout(r2d)
        r2c = QHBoxLayout()
        self.b_finish = QPushButton("Finish")
        self.b_clear = QPushButton("Clear")
        r2c.addWidget(self.b_finish)
        r2c.addWidget(self.b_clear)
        r2c.addStretch(1)
        v2.addLayout(r2c)
        self.cb_smooth = QCheckBox("Smooth curve through the clicks")
        self.cb_closed = QCheckBox("Closed loop")
        r2b = QHBoxLayout()
        r2b.addWidget(self.cb_smooth)
        r2b.addWidget(self.cb_closed)
        r2b.addStretch(1)
        v2.addLayout(r2b)
        f2 = QFormLayout()
        self.cb_axis = QComboBox()
        for _k, t in AXES:
            self.cb_axis.addItem(t)
        f2.addRow("Ring goes round:", self.cb_axis)
        v2.addLayout(f2)
        self.lbl_line = QLabel("No line yet. Select the object the line goes over, then Draw line or Wrap round.")
        self.lbl_line.setWordWrap(True)
        v2.addWidget(self.lbl_line)
        lay.addWidget(box2)

        # 3. spacing
        box3 = QGroupBox("3. Spacing")
        f3 = QFormLayout(box3)
        mrow = QHBoxLayout()
        self.rb_count = QRadioButton("How many")
        self.rb_pitch = QRadioButton("Pitch")
        self._mode_group = QButtonGroup(self)
        self._mode_group.addButton(self.rb_count)
        self._mode_group.addButton(self.rb_pitch)
        mrow.addWidget(self.rb_count)
        self.sp_count = QSpinBox()
        self.sp_count.setRange(0, 5000)
        mrow.addWidget(self.sp_count)
        mrow.addSpacing(12)
        mrow.addWidget(self.rb_pitch)
        self.sp_pitch = QDoubleSpinBox()
        self.sp_pitch.setRange(0.1, 100000.0)
        self.sp_pitch.setDecimals(1)
        self.sp_pitch.setSuffix(" mm")
        mrow.addWidget(self.sp_pitch)
        mrow.addStretch(1)
        f3.addRow(mrow)
        how = EDDY_TIPS["how many"]
        self.rb_count.setToolTip(how)
        self.sp_count.setToolTip(how)
        self.lbl_count_note = QLabel()
        self.lbl_count_note.setStyleSheet("color: gray;")
        f3.addRow(self.lbl_count_note)
        self.cb_clicks = QCheckBox("On every point you clicked")
        f3.addRow(self.cb_clicks)
        crow = QHBoxLayout()
        self.cb_corners = QCheckBox("On every corner")
        crow.addWidget(self.cb_corners)
        crow.addWidget(QLabel("turning more than"))
        self.sp_corner = QDoubleSpinBox()
        self.sp_corner.setRange(5.0, 170.0)
        self.sp_corner.setDecimals(0)
        self.sp_corner.setSuffix("°")
        crow.addWidget(self.sp_corner)
        crow.addStretch(1)
        f3.addRow(crow)
        self.lbl_result = QLabel("-")
        self.lbl_result.setWordWrap(True)
        f3.addRow(self.lbl_result)
        lay.addWidget(box3)

        # 4. how it sits
        box4 = QGroupBox("4. How it sits")
        f4 = QFormLayout(box4)
        self.sp_turn = QDoubleSpinBox()
        self.sp_turn.setRange(-360.0, 360.0)
        self.sp_turn.setDecimals(1)
        self.sp_turn.setSuffix("°")
        f4.addRow("Turn:", self.sp_turn)
        self.cb_nogap = QCheckBox("Sink in until there's no gap under it")
        f4.addRow(self.cb_nogap)
        self.sp_sink = QDoubleSpinBox()
        self.sp_sink.setRange(0.0, 1000.0)
        self.sp_sink.setDecimals(2)
        self.sp_sink.setSuffix(" mm")
        f4.addRow("Sink in a bit more:", self.sp_sink)
        self.sp_offset = QDoubleSpinBox()
        self.sp_offset.setRange(-100000.0, 100000.0)
        self.sp_offset.setDecimals(1)
        self.sp_offset.setSuffix(" mm")
        f4.addRow("Off the line:", self.sp_offset)
        self.sp_tilt = QDoubleSpinBox()
        self.sp_tilt.setRange(-180.0, 180.0)
        self.sp_tilt.setDecimals(1)
        self.sp_tilt.setSuffix("\u00b0")
        f4.addRow("Tilt about the line:", self.sp_tilt)
        self.cb_other = QCheckBox("Other side of the line")
        self.cb_stagger = QCheckBox("Every other one on the other side (staggered)")
        f4.addRow(self.cb_other)
        f4.addRow(self.cb_stagger)
        self.cb_flip = QCheckBox("Stand on the back of the surface (inside)")
        f4.addRow(self.cb_flip)
        lay.addWidget(box4)

        self.lbl_report = QLabel()
        self.lbl_report.setWordWrap(True)
        lay.addWidget(self.lbl_report)
        brow = QHBoxLayout()
        self.b_edit = QPushButton("Edit selected row")
        brow.addWidget(self.b_edit)
        brow.addStretch(1)
        self.b_place = QPushButton("Place")
        self.b_place.setDefault(False)
        self.b_place.setAutoDefault(False)
        brow.addWidget(self.b_place)
        b_close = QPushButton("Close")
        b_close.clicked.connect(self.close)
        brow.addWidget(b_close)
        lay.addLayout(brow)
        for b in (self.b_use, self.b_draw, self.b_wrap, self.b_own, self.b_face, self.b_finish, self.b_clear,
                  self.b_edit, b_close):
            b.setAutoDefault(False)
        try:
            self.setMinimumWidth(440)
        except Exception:
            pass

        # settings as last left
        s = self.state
        self.cb_smooth.setChecked(s['smooth'])
        self.cb_closed.setChecked(s['closed'])
        self.cb_axis.setCurrentIndex(s['axis'])
        (self.rb_pitch if s['mode'] == "pitch" else self.rb_count).setChecked(True)
        self.sp_count.setValue(s['count'])
        self.sp_pitch.setValue(s['pitch'])
        self.cb_clicks.setChecked(s['on_clicks'])
        self.cb_corners.setChecked(s['on_corners'])
        self.sp_corner.setValue(s['corner_deg'])
        self.sp_turn.setValue(s['turn'])
        self.sp_sink.setValue(s['sink'])
        self.cb_nogap.setChecked(s.get('nogap', True))
        self.sp_inset.setValue(s.get('inset', 10.0))
        self.cb_flip.setChecked(s['flip'])
        self.sp_offset.setValue(s.get('offset', 0.0))
        self.sp_tilt.setValue(s.get('tilt', 0.0))
        self.cb_other.setChecked(s.get('other', False))
        self.cb_stagger.setChecked(s.get('stagger', False))
        self.fill_parts(s.get('part'))
        self.rb_lib.setChecked(True)

        self.b_use.clicked.connect(self.use_selected)
        self.b_draw.clicked.connect(lambda: self.start("line"))
        self.b_wrap.clicked.connect(lambda: self.start("wrap"))
        self.b_own.clicked.connect(self.use_line)
        self.b_face.clicked.connect(self.use_face)
        self.sp_inset.valueChanged.connect(self._inset_changed)
        self.b_finish.clicked.connect(self.finish)
        self.b_clear.clicked.connect(self.clear)
        self.b_edit.clicked.connect(self.edit_selected)
        self.b_place.clicked.connect(self.place)
        self.cb_part.currentIndexChanged.connect(self._lib_picked)
        self.rb_lib.toggled.connect(self.part_changed)
        self.cb_closed.toggled.connect(self.shape_changed)
        self.cb_smooth.toggled.connect(self.shape_changed)
        self.cb_axis.currentIndexChanged.connect(self.shape_changed)
        for w in (self.rb_count, self.rb_pitch, self.cb_clicks, self.cb_corners, self.cb_flip, self.cb_nogap,
                  self.cb_other, self.cb_stagger):
            w.toggled.connect(self.settings_changed)
        for w in (self.sp_count, self.sp_pitch, self.sp_corner, self.sp_turn, self.sp_sink, self.sp_offset,
                  self.sp_tilt):
            w.valueChanged.connect(self.settings_changed)
        self.part_changed()
        self.update_buttons()

    # -------------------------------------------------------------- the part
    def fill_parts(self, want=None):
        self.cb_part.blockSignals(True)
        self.cb_part.clear()
        for t in self.lib.get("tabs", []):
            for e in t.get("parts", []):
                self.cb_part.addItem("%s ▸ %s" % (t.get("name", ""), e.get("name", "Part")), "lib:%s" % e.get("id"))
        pick = 0
        if want is not None:
            for i in range(self.cb_part.count()):
                if self.cb_part.itemData(i) == want:
                    pick = i
                    break
        else:
            for i in range(self.cb_part.count()):
                if "rivet" in self.cb_part.itemText(i).lower() and "marker" not in self.cb_part.itemText(i).lower():
                    pick = i
                    break
        self.cb_part.setCurrentIndex(pick)
        self.cb_part.blockSignals(False)

    def _lib_picked(self, *_):
        if not self.rb_lib.isChecked():
            self.rb_lib.setChecked(True)        # choosing from the list means the list's part
        else:
            self.part_changed()

    def _lib_entry(self, pid):
        for t in self.lib.get("tabs", []):
            for e in t.get("parts", []):
                if e.get("id") == pid:
                    return e
        return None

    def part_group(self):
        """The part's definition: the group every copy is made from. None if there's no part."""
        if self.rb_model.isChecked():
            return self.model_part
        data = self.cb_part.currentData()
        if not data:
            return None
        _kind, _c, key = str(data).partition(":")
        e = self._lib_entry(key)
        if e is None:
            return None
        g = find_definition(self.scene(), e)
        if g is not None:
            return g
        g = self._defs.get(e.get("id"))
        if g is None:
            g = build_definition(e)
            self._defs[e.get("id")] = g
        return g

    def part_changed(self, *_):
        if not self.rb_model.isChecked():
            self.state['part'] = self.cb_part.currentData()
        self.rb_model.setEnabled(self.model_part is not None)
        g = None
        try:
            g = self.part_group()
        except Exception as ex:
            self.lbl_part.setText("Couldn't make that part: %s" % ex)
        self._part, self._box = g, None
        if g is not None:
            try:
                self._box = local_box(g)
                lo, hi = self._box
                self.lbl_part.setText("%s mm across, %s mm high" % (
                    _fmt(max(hi[0] - lo[0], hi[1] - lo[1])), _fmt(hi[2] - lo[2])))
            except Exception as ex:
                self.lbl_part.setText("Couldn't read that part: %s" % ex)
        self.settings_changed()

    def use_selected(self, *_):
        """The part from the model: the component selected now. Picked once, it stays - selecting
        the boiler afterwards doesn't change it."""
        gs = [e for e in self.selection() if _is_group(e) and not _is_row(e)]
        if not gs:
            rows = [e for e in self.selection() if _is_row(e)]
            if rows and rows[0].children:
                gs = [rows[0].children[0]]
        if not gs:
            self.report("Select a component in the model first (the rivet or bolt you want along the line).", True)
            return
        g = gs[0]
        self.model_part_from = getattr(g, 'uid', None)
        if getattr(g, 'xform', None) is None:
            # a plain group: one copy of it as a component, so every copy along the line shares it
            from core.group import copy_group
            d = copy_group(g)
            d.xform = QMatrix4x4()
            d.component = True
            g = d
        label = str(getattr(g, 'name', '') or 'Component')
        self._set_model_part(g, label)
        self.report("The part is %s now - it stays the part until you pick another, whatever you select next. "
                    "It stands on the middle of its bottom, its blue (Z) axis out of the surface." % label)

    def _set_model_part(self, g, label):
        self.model_part = g
        self.lbl_model_part.setText(label)
        self.rb_model.blockSignals(True)
        self.rb_model.setChecked(True)
        self.rb_model.blockSignals(False)
        self.part_changed()

    # -------------------------------------------------------------- the line
    def scene(self):
        return getattr(self.viewport, 'scene', None)

    def selection(self):
        sc = self.scene()
        return list(getattr(sc, 'selection', None) or [])

    def start(self, kind):
        try:
            surf, what, uids, axes = gather_surface(self.scene(), self.selection())
        except RuntimeError:
            self.report("That's too much to work over: select just the object the line goes over.", True)
            return
        except Exception as ex:
            self.report("Couldn't read the model: %s" % ex, True)
            return
        if not len(surf):
            self.report("There's nothing to put a line on: select the object it goes over.", True)
            return
        self.surf, self.surf_what, self.surf_uids, self.surf_axes = surf, what, uids, axes
        self.kind = kind
        self.clicks, self.lines, self.frames, self.chains = [], [], [], []
        self.drawing, self.ended = True, False
        self.wrap_axis = None
        self.activate_tool()
        if kind == "wrap":
            self.lbl_line.setText("Click once on %s: the ring goes round it through that point." % what)
        else:
            self.lbl_line.setText("Click points on %s. Backspace takes the last off; Enter, a double-click or "
                                  "Finish ends the line." % what)
        self.update_buttons()
        self.settings_changed()

    def use_line(self, *_):
        """Your own line: the lines selected (an outline you've offset, say), or the loose lines in a
        selected group."""
        sel = self.selection()
        chains = selected_lines(self.scene(), sel)
        if not chains:
            self.report("Select your line first: click it (Shift-click to add more of it). If it's inside a "
                        "group, either select the group (its loose lines are used) or double-click into the "
                        "group and click the line. To go round a face, use Round selected face.", True)
            return
        pts = [p for c, _cl in chains for p in c]
        lo = tuple(min(p[k] for p in pts) for k in range(3))
        hi = tuple(max(p[k] for p in pts) for k in range(3))
        pad = max(_len(_sub(hi, lo)) * 0.05, 0.005)
        box = (_sub(lo, (pad, pad, pad)), _add(hi, (pad, pad, pad)))
        faces = [e for e in sel if _is_face(e)]
        try:
            surf, what, uids, axes = gather_surface(self.scene(), faces, within=box)
        except Exception as ex:
            self.report("Couldn't read the surface under the line: %s" % ex, True)
            return
        self.surf, self.surf_what, self.surf_uids, self.surf_axes = surf, what, uids, axes
        self.kind = "edges"
        self.chains = chains
        self.clicks, self.frames = [], []
        self.drawing, self.ended = False, True
        self.editing = None
        self.rebuild()
        self.activate_tool()            # shows the line and where the parts go
        self.drawing = False
        n = len(chains)
        self._took_line()
        self.report("Using your line%s. %s" % (
            "" if n == 1 else " (%d separate pieces - each gets its own spacing)" % n,
            "" if len(surf) else "There's no surface under it, so the parts stand square to the line's own face."))

    def use_face(self, *_):
        """Round the edge of the selected face(s), moved in by the inset. Several faces together
        (the faces of a curved panel) count as one region: the joins between them drop out, and a
        window hole in them gets its own ring."""
        sel = self.selection()
        m0 = ctx_world(self.scene())
        faces = []
        for f in sel:
            if not _is_face(f):
                continue
            outer = _loop_pts(getattr(f, 'vertices', None), m0)
            holes = [_loop_pts(h, m0) for h in (getattr(f, 'holes', None) or [])]
            if len(outer) < 3:
                continue
            try:
                n = _qv(f.normal())
            except Exception:
                n = plane_normal(outer)
            if m0 is not None:
                n = _unit(m_vec(m0, n)) or n
            faces.append((outer, [h for h in holes if len(h) >= 3], n))
        if not faces:
            self.report("Select the face first (click it). If it's inside a group, double-click into the group "
                        "and click the face. Shift-click to add more faces - a curved panel's faces together "
                        "are gone round as one.", True)
            return
        try:
            surf, what, uids, axes = gather_surface(self.scene(), [f for f in sel if _is_face(f)])
        except Exception as ex:
            self.report("Couldn't read the face: %s" % ex, True)
            return
        self.surf, self.surf_what, self.surf_uids, self.surf_axes = surf, what, uids, axes
        self.boundary = face_boundary(faces)
        self.kind = "face"
        self.clicks, self.frames = [], []
        self.drawing, self.ended = False, True
        self.editing = None
        self.rebuild()
        self.activate_tool()
        self.drawing = False
        self._took_line()
        self.report("Going round %s, %s mm in from the edge. Change Inset from edge to move the line in or out."
                    % (what, _fmt(self.sp_inset.value() / MM)))

    def _inset_changed(self, *_):
        self.state['inset'] = self.sp_inset.value()
        if self.kind == "face":
            self.rebuild()

    def _took_line(self):
        try:
            self.viewport.scene.selection.clear()   # so the line is easy to see
            self.viewport.update()
        except Exception:
            pass

    def activate_tool(self):
        vp = self.viewport
        try:
            if self.pick_tool is None:
                self.pick_tool = make_line_tool(self)
            vp.set_active_tool(self.pick_tool)
            vp.setFocus()
        except Exception as ex:
            self.report("Couldn't start clicking: %s" % ex, True)

    def stop_tool(self):
        """Esc: stop clicking. The line so far is kept to place, if there is one."""
        if self.drawing and self.kind == "line" and len(self.clicks) >= 2:
            self.finish()
            return
        self.drawing = False
        self._back_to_select()
        self.update_buttons()

    def _back_to_select(self):
        try:
            win = self.viewport.window()
            act = getattr(win, "_activate_tool", None)
            if callable(act):
                act("select")
                return
        except Exception:
            pass
        try:
            self.viewport.set_active_tool(None)
        except Exception:
            pass

    def tool_gone(self, tool):
        """Another tool was picked: stop clicking (the line is kept)."""
        if tool is self.pick_tool:
            self.drawing = False
            self.update_buttons()

    def clicked(self, p):
        if self.surf is None:
            return
        if not self.drawing:
            self.report("Press Place to put the parts on, or Draw line / Wrap round to start again.", True)
            return
        q, n, d = self.surf.closest(p)
        if d > max(0.02 * self.surf.diag, 1e-3):
            self.report("That wasn't on %s - click on its surface." % self.surf_what, True)
            return
        if self.kind == "wrap":
            self.clicks = [q]
            self.finish()
            return
        if self.clicks and _len(_sub(q, self.clicks[-1])) < 1e-9:
            return
        self.clicks.append(q)
        self.rebuild()

    def take_last(self):
        if self.clicks and self.drawing:
            self.clicks.pop()
            self.rebuild()

    def finish(self, *_):
        if self.kind == "wrap":
            if not self.clicks:
                return
        elif len(self.clicks) < 2:
            self.report("Click at least two points for a line.", True)
            return
        self.drawing, self.ended = False, True
        self.rebuild()
        self.update_buttons()
        try:
            self.viewport.update()
        except Exception:
            pass

    def clear(self, *_):
        self.clicks, self.lines, self.frames, self.chains = [], [], [], []
        self.ended = False
        if self.drawing and self.kind not in ("edges", "face"):
            self.rebuild()
        else:
            self.drawing = False
            self.kind = None
            self.lbl_line.setText("No line yet. Select the object the line goes over, then Draw line or Wrap round.")
            self._back_to_select()
        self.editing = None
        self.update_buttons()
        self.settings_changed()

    def shape_changed(self, *_):
        self.state.update(smooth=self.cb_smooth.isChecked(), closed=self.cb_closed.isChecked(),
                          axis=self.cb_axis.currentIndex())
        self.rebuild()

    def rebuild(self):
        """Works the line out again from the clicks."""
        self.lines = []
        if self.kind == "face":
            try:
                self.chains = inset_chains(self.boundary, self.sp_inset.value() / MM, self.surf)
            except Exception as ex:
                self.report("Couldn't move the edge in: %s" % ex, True)
                self.chains = []
        if self.kind in ("edges", "face"):
            for pts, closed in self.chains:
                self.lines.append((list(pts), line_normals(self.surf, pts, closed), [], closed))
            self.settings_changed()
            return
        if self.surf is None or not self.clicks:
            self.settings_changed()
            return
        try:
            if self.kind == "wrap":
                ax = AXES[self.cb_axis.currentIndex()][0]
                got = wrap_ring(self.surf, self.clicks[0], ax, self.surf_axes)
                if got is None:
                    self.report("Couldn't find a ring round it through that point - try another way round "
                                "(Ring goes round), or Draw line with Closed loop.", True)
                else:
                    P, N, self.wrap_axis = got
                    self.lines = [(P, N, [0], True)]
            else:
                closed = self.cb_closed.isChecked() and (self.ended or not self.drawing) and len(self.clicks) >= 3
                P, N, knots = build_line(self.surf, self.clicks, closed, self.cb_smooth.isChecked())
                self.lines = [(P, N, knots, closed)]
        except Exception as ex:
            self.report("Couldn't work the line out: %s" % ex, True)
            self.lines = []
        self.settings_changed()

    def line_closed(self):
        if self.kind == "wrap":
            return True
        if self.kind in ("edges", "face"):
            return bool(self.chains) and all(c for _p, c in self.chains)
        return bool(self.cb_closed.isChecked() and (self.ended or not self.drawing) and len(self.clicks) >= 3)

    # -------------------------------------------------------------- spacing
    def settings_changed(self, *_):
        s = self.state
        s.update(mode="pitch" if self.rb_pitch.isChecked() else "count", count=self.sp_count.value(),
                 pitch=self.sp_pitch.value(), on_clicks=self.cb_clicks.isChecked(),
                 on_corners=self.cb_corners.isChecked(), corner_deg=self.sp_corner.value(),
                 turn=self.sp_turn.value(), sink=self.sp_sink.value(), flip=self.cb_flip.isChecked(),
                 offset=self.sp_offset.value(), tilt=self.sp_tilt.value(), other=self.cb_other.isChecked(),
                 stagger=self.cb_stagger.isChecked(),
                 nogap=self.cb_nogap.isChecked())
        closed = self.line_closed()
        self.rb_count.setText("How many in all" if closed else "How many between the ends")
        note = "Round the loop, the first one on the point you clicked." if closed else "Plus one on each end."
        if self.kind in ("edges", "face") and len(self.chains) > 1:
            note = "For each piece of your line: " + note[0].lower() + note[1:]
        self.lbl_count_note.setText(note)
        self.sp_count.setEnabled(self.rb_count.isChecked())
        self.sp_pitch.setEnabled(self.rb_pitch.isChecked())
        self.sp_corner.setEnabled(self.cb_corners.isChecked())
        self.frames = []
        good = [ln for ln in self.lines if len(ln[0]) >= 2]
        if good:
            g0, g1, length = float('inf'), 0.0, 0.0
            for P, N, knots, cl in good:
                s_cum, total = cumulative(P, cl)
                anchors = []
                if self.cb_clicks.isChecked() and self.kind == "line":
                    anchors += [s_cum[k] for k in knots if k < len(s_cum)]
                if self.cb_corners.isChecked():
                    anchors += corner_stations(P, cl, self.sp_corner.value())
                st, a, b = stations(total, cl, anchors, s['mode'], s['count'], s['pitch'] / MM)
                self.frames += station_frames(self.surf, P, N, cl, st, self.cb_flip.isChecked(),
                                              keep_on_line=self.kind in ("edges", "face"))
                g0, g1, length = min(g0, a), max(g1, b), length + total
            self.frames = side_frames(self.surf, self.frames, self.sp_offset.value() / MM, self.sp_tilt.value(),
                                      self.cb_other.isChecked(), self.cb_stagger.isChecked())
            gap = ("%s mm apart" % _fmt(g0)) if abs(g1 - g0) < 1e-7 else ("%s to %s mm apart" % (_fmt(g0), _fmt(g1)))
            self.lbl_result.setText("<b>%d</b> parts, %s, on a line %s mm long%s." % (
                len(self.frames), gap, _fmt(length), " (closed loop)" if closed else ""))
            bad = self.part_problem()
            if bad:
                self.report(bad, True)
            if self.kind == "wrap":
                what = "Ring round %s" % self.surf_what
            elif self.kind == "face":
                what = "Round %s, %s mm in from the edge" % (self.surf_what, _fmt(self.sp_inset.value() / MM))
                if len(good) > 1:
                    what += " (%d rings)" % len(good)
            elif self.kind == "edges":
                what = "Your own line" + ("" if len(good) == 1 else ", %d pieces" % len(good))
            else:
                what = "Line over %s: %d point%s" % (self.surf_what, len(self.clicks),
                                                     "" if len(self.clicks) == 1 else "s")
            if self.drawing:
                what += " - keep clicking, Enter or Finish to end it"
            self.lbl_line.setText(what + ".")
        elif self.lines:
            self.lbl_result.setText("Click another point.")
        else:
            self.lbl_result.setText("-")
        self.update_buttons()
        try:
            self.viewport.update()
        except Exception:
            pass

    def update_buttons(self, *_):
        self.b_finish.setEnabled(self.drawing and self.kind == "line" and len(self.clicks) >= 2)
        self.b_clear.setEnabled(bool(self.clicks or self.chains))
        self.b_place.setEnabled(bool(self.frames) and self._part is not None and not self.drawing)
        self.b_place.setText("Replace row" if self.editing is not None else "Place")
        self.cb_axis.setEnabled(self.kind not in ("line", "edges", "face"))
        self.sp_sink.setEnabled(True)

    # -------------------------------------------------------------- preview
    def status_text(self):
        if self.kind == "wrap":
            return "Click once on the object to ring it"
        return "Backspace = take the last point off, Enter or double-click = finish, Esc = stop"

    def preview_lines(self, hover):
        """The line, a tick out of the surface where each part goes, and (while drawing) a line
        from the last point to the mouse."""
        out = []
        V = QVector3D
        for P, _N, _k, closed in self.lines:
            for i in range(len(P) - 1):
                out.append((V(*P[i]), V(*P[i + 1])))
            if closed and len(P) > 2:
                out.append((V(*P[-1]), V(*P[0])))
        tick = 0.0
        if self._box is not None:
            tick = (self._box[1][2] - self._box[0][2]) * 1.5
        if self.surf is not None:
            tick = min(max(tick, self.surf.diag / 150.0), self.surf.diag / 25.0)
        for o, x, y, z in self.frames[:3000]:
            out.append((V(*o), V(*_add(o, _mul(z, tick)))))
        if self.surf is not None:
            k = self.surf.diag / 250.0
            for c in self.clicks:
                out.append((V(*_sub(c, (k, 0, 0))), V(*_add(c, (k, 0, 0)))))
                out.append((V(*_sub(c, (0, k, 0))), V(*_add(c, (0, k, 0)))))
                out.append((V(*_sub(c, (0, 0, k))), V(*_add(c, (0, 0, k)))))
        if self.drawing and self.kind == "line" and self.clicks and hover is not None:
            out.append((V(*self.clicks[-1]), V(*hover)))
        return out

    # -------------------------------------------------------------- placing
    def make_row(self):
        from core.mesh import Mesh
        from core.group import Group, copy_group
        rep = self._part
        lo, hi = local_box(rep)
        base = base_centre((lo, hi))
        ax = axes_of(rep)
        turn, sink = self.sp_turn.value(), self.sp_sink.value() / MM
        _roots, ctx_x = scene_roots(self.scene())
        inv_ctx = m_inv(ctx_x) if ctx_x is not None else None
        self.sinks = [0.0] * len(self.frames)
        if self.cb_nogap.isChecked() and self.surf is not None:
            inv = m_inv(ax)
            foot = footprint([m_apply(inv, p) for p in own_points(rep)], lo, hi)
            self.sinks = auto_sinks(self.surf, self.frames, foot, turn)
        kids = []
        for fr, extra in zip(self.frames, self.sinks):
            x = placement(fr, base, ax, turn, sink + extra)
            if inv_ctx is not None:
                x = m_mul(inv_ctx, x)
            g = copy_group(rep)
            g.xform = m_to_q(x)
            g.component = True
            g.layer, g.hidden, g.locked, g.material = None, False, False, None
            kids.append(g)
        name = "%s x%d along line" % (str(getattr(rep, 'name', '') or 'Part'), len(kids))
        row = Group(Mesh(), name=name)
        row.children = kids
        data = self.cb_part.currentData()
        row.ext = {EXT_TAG: {
            "kind": self.kind, "clicks": [list(c) for c in self.clicks],
            "closed": self.line_closed(), "smooth": self.cb_smooth.isChecked(),
            "axis": self.cb_axis.currentIndex(), "mode": self.state['mode'], "count": self.sp_count.value(),
            "pitch": self.sp_pitch.value(), "on_clicks": self.cb_clicks.isChecked(),
            "on_corners": self.cb_corners.isChecked(), "corner_deg": self.sp_corner.value(),
            "turn": turn, "sink": self.sp_sink.value(), "flip": self.cb_flip.isChecked(),
            "offset": self.sp_offset.value(), "tilt": self.sp_tilt.value(), "other": self.cb_other.isChecked(),
            "stagger": self.cb_stagger.isChecked(),
            "nogap": self.cb_nogap.isChecked(),
            "chains": [[[list(p) for p in pts], bool(cl)] for pts, cl in self.chains],
            "boundary": [[list(a), list(b), list(w)] for a, b, w in self.boundary] if self.kind == "face" else [],
            "inset": self.sp_inset.value(),
            "part": data if self.rb_lib.isChecked() and data else None,
            "over": list(self.surf_uids), "version": VERSION}}
        return row

    def part_problem(self):
        """Why the part looks wrong for this line, or None."""
        if self._part is None or self._box is None:
            return None
        if self.rb_model.isChecked() and self.model_part_from and self.model_part_from in (self.surf_uids or []):
            return ("The part is %s - the same object the line goes over. Pick your rivet as the part "
                    "(or choose one From the library)." % self.lbl_model_part.text())
        lo, hi = self._box
        size = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
        if self.frames and len(self.frames) > 1:
            gap = min(_len(_sub(self.frames[i + 1][0], self.frames[i][0])) for i in range(len(self.frames) - 1))
            if size > 3.0 * max(gap, 1e-9):
                return ("The part (%s mm) is much bigger than the gap between them (%s mm) - is it the right "
                        "part? A rivet should be a few mm to a few tens of mm." % (_fmt(size), _fmt(gap)))
        return None

    def place(self, *_):
        if not self.frames or self._part is None:
            self.report("Draw a line and pick a part first.", True)
            return
        bad = self.part_problem()
        if bad and "same object" in bad:
            self.report(bad, True)
            return
        if len(self.frames) > 5000:
            self.report("That's %d parts - more than 5000 at once. Make the pitch bigger." % len(self.frames), True)
            return
        try:
            row = self.make_row()
        except Exception as ex:
            self.report("Couldn't make the row: %s" % ex, True)
            return
        h = self.viewport.history
        owner = self._owner_of(self.editing) if self.editing is not None else None
        try:
            if owner is not None:
                cmd = ReplaceRowCommand(owner, self.editing, row)
            else:
                from core.history import InsertGroupCommand
                cmd = InsertGroupCommand(row)
            h.execute(cmd)
            if getattr(h, 'last_error', None):
                raise RuntimeError(h.last_error)
        except Exception as ex:
            self.report("Couldn't place them: %s" % ex, True)
            return
        self._changed()
        n = len(row.children)
        replaced = owner is not None
        self.clicks, self.lines, self.frames, self.chains = [], [], [], []
        self.kind, self.ended, self.drawing, self.editing = None, False, False, None
        self._back_to_select()
        self.lbl_line.setText("No line yet. Select the object the line goes over, then Draw line or Wrap round.")
        self.settings_changed()
        deep = max(self.sinks or [0.0]) + self.sp_sink.value() / MM
        self.report("%s %d parts along the line, as one group (selected)%s. Edit selected row changes it; "
                    "Undo takes it off." % ("Replaced the row with" if replaced else "Placed", n,
                                            (", sunk in up to %s mm" % _fmt(deep)) if deep > 1e-7 else ""))

    def _owner_of(self, g):
        sc = self.scene()
        if g in (getattr(sc, 'groups', None) or []):
            return sc.groups
        for top in getattr(sc, 'groups', None) or []:
            for pg, _m in _iter_placements(top):
                kids = getattr(pg, 'children', None)
                if kids and g in kids:
                    return kids
        return None

    def edit_selected(self, *_):
        rows = [e for e in self.selection() if _is_row(e)]
        if not rows:
            self.report("Select a row this plugin made (click one of its parts with the Select tool).", True)
            return
        row = rows[0]
        d = row.ext[EXT_TAG]
        # the surface it went over: the same objects if they're still there, else everything shown
        over = find_by_uids(self.scene(), d.get("over") or [])
        chains = [([tuple(p) for p in c[0]], bool(c[1])) for c in d.get("chains") or [] if len(c) == 2]
        box = None
        if d.get("kind") == "face" and d.get("boundary"):
            chains = [([tuple(p) for p in seg[:2]], False) for seg in d.get("boundary")]
        if d.get("kind") in ("edges", "face") and chains:
            pts = [p for c, _cl in chains for p in c]
            lo = tuple(min(p[k] for p in pts) for k in range(3))
            hi = tuple(max(p[k] for p in pts) for k in range(3))
            pad = max(_len(_sub(hi, lo)) * 0.05, 0.005)
            box = (_sub(lo, (pad, pad, pad)), _add(hi, (pad, pad, pad)))
        try:
            surf, what, uids, axes = gather_surface(self.scene(), over, within=box)
        except Exception as ex:
            self.report("Couldn't read the model: %s" % ex, True)
            return
        self.surf, self.surf_what, self.surf_uids, self.surf_axes = surf, what, uids, axes
        # the part: the library one, or the row's own
        part = d.get("part")
        found = False
        if part:
            for i in range(self.cb_part.count()):
                if self.cb_part.itemData(i) == part:
                    self.cb_part.blockSignals(True)
                    self.cb_part.setCurrentIndex(i)
                    self.cb_part.blockSignals(False)
                    self.rb_lib.setChecked(True)
                    found = True
                    break
        if not found and row.children:
            self._set_model_part(row.children[0], str(getattr(row.children[0], 'name', '') or 'Part'))
        for w in (self.cb_smooth, self.cb_closed, self.cb_axis, self.rb_count, self.rb_pitch, self.sp_count,
                  self.sp_pitch, self.cb_clicks, self.cb_corners, self.sp_corner, self.sp_turn, self.sp_sink,
                  self.cb_flip, self.cb_part, self.cb_nogap, self.sp_offset, self.sp_tilt, self.cb_other,
                  self.cb_stagger):
            w.blockSignals(True)
        self.cb_smooth.setChecked(bool(d.get("smooth", True)))
        self.cb_closed.setChecked(bool(d.get("closed", False)))
        self.cb_axis.setCurrentIndex(int(d.get("axis", 0)))
        (self.rb_pitch if d.get("mode") == "pitch" else self.rb_count).setChecked(True)
        self.sp_count.setValue(int(d.get("count", 10)))
        self.sp_pitch.setValue(float(d.get("pitch", 50.0)))
        self.cb_clicks.setChecked(bool(d.get("on_clicks", True)))
        self.cb_corners.setChecked(bool(d.get("on_corners", True)))
        self.sp_corner.setValue(float(d.get("corner_deg", 40.0)))
        self.sp_turn.setValue(float(d.get("turn", 0.0)))
        self.sp_sink.setValue(float(d.get("sink", 0.0)))
        self.cb_nogap.setChecked(bool(d.get("nogap", False)))
        self.cb_flip.setChecked(bool(d.get("flip", False)))
        self.sp_offset.setValue(float(d.get("offset", 0.0)))
        self.sp_tilt.setValue(float(d.get("tilt", 0.0)))
        self.cb_other.setChecked(bool(d.get("other", False)))
        self.cb_stagger.setChecked(bool(d.get("stagger", False)))
        for w in (self.cb_smooth, self.cb_closed, self.cb_axis, self.rb_count, self.rb_pitch, self.sp_count,
                  self.sp_pitch, self.cb_clicks, self.cb_corners, self.sp_corner, self.sp_turn, self.sp_sink,
                  self.cb_flip, self.cb_part, self.cb_nogap, self.sp_offset, self.sp_tilt, self.cb_other,
                  self.cb_stagger):
            w.blockSignals(False)
        self.kind = d.get("kind") or "line"
        self.clicks = [tuple(c) for c in d.get("clicks") or []]
        self.chains = chains
        self.boundary = [(tuple(a), tuple(b), tuple(w)) for a, b, w in d.get("boundary") or []]
        self.sp_inset.blockSignals(True)
        self.sp_inset.setValue(float(d.get("inset", self.sp_inset.value())))
        self.sp_inset.blockSignals(False)
        self.drawing, self.ended = False, True
        self.editing = row
        self.part_changed()
        self.rebuild()
        self.activate_tool()            # shows the line
        self.drawing = False
        self.update_buttons()
        self.report("Editing %s. Change anything, then Replace row. Draw line starts the line again." %
                    str(getattr(row, 'name', '') or 'the row'))

    # -------------------------------------------------------------- odds and ends
    def report(self, text, bad=False):
        self.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if bad else "#2e7d32"))
        self.lbl_report.setText(text)

    def _changed(self):
        for name in ('notify_scene_changed', 'update'):
            try:
                getattr(self.viewport, name)()
            except Exception:
                pass

    def closeEvent(self, ev):
        try:
            if self.viewport.active_tool is self.pick_tool and self.pick_tool is not None:
                self._back_to_select()
        except Exception:
            pass
        super().closeEvent(ev)


def _fmt(metres):
    return ("%.1f" % (metres * MM)).replace("-0.0", "0.0")


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
class PlaceAlongTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+S"
    description = ("Puts rivets, bolts or any part along a line drawn over a surface - over a boiler, "
                   "round a chimney - each one standing square on the surface.")
    _dialog = None

    def on_activate(self, viewport):
        dlg = PlaceAlongTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.raise_()
                    dlg.activateWindow()
                    return
            except Exception:
                pass
        dlg = PlaceAlongDialog(viewport, self)
        PlaceAlongTool._dialog = dlg

        def closed(*_):
            PlaceAlongTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass


def run(viewport=None):
    PlaceAlongTool().on_activate(viewport)
