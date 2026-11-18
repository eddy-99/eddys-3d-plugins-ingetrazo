# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Period Windows for IngeTrazo
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
3D Period Windows - old-fashioned windows for IngeTrazo
Select any flat face (a shape drawn on a wall or a sloping roof, or a face with
openings in it) and the window is made to fit its outline: square, round-topped, segmental, pointed
or round. Sash, casement and fixed / industrial styles, panes in columns and
rows, windows that can be shown open, optional glass, stone or brick sills and
heads, and keystones. Ctrl+Alt+N.

Whole building page: select a building and click Find - every opening in the outside walls
lights up and is listed. Build puts a window in each ticked one and joins it into its own wall
section, flat with the back of the wall, so each wall lays flat and prints as one piece.
"""

import re
import os
import json
import math
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QDoubleSpinBox, QSpinBox, QComboBox,
    QCheckBox, QPushButton, QLabel, QMessageBox, QInputDialog, QWidget, QTabWidget
)

PLUGIN_NAME = "3D Period Windows"
VERSION = "2.5"  # shown in the window title, so you can tell which file is loaded. 2.5: a door built into the same wall keeps its own colours when the windows are built again


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

PRESET_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Windows")
SCALE = 0.001            # sizes are in mm; IngeTrazo stores geometry in metres

STYLES = [("sash", "Sash (sliding)"), ("casement", "Casement"), ("fixed", "Fixed / industrial")]
TOPS = [("face", "Follow the face shape"), ("flat", "Square top"),
        ("semi", "Round top (semicircle)"), ("segment", "Segmental (shallow arch)"),
        ("gothic", "Pointed (gothic)"), ("circle", "Round (bull's-eye)")]
ARCH_BARS = [("fan", "Fan bars in the arch"), ("grid", "Grid carries on into the arch"),
             ("plain", "Plain glass in the arch")]
SILLS = [("stone", "Stone sill"), ("brick", "Brick-on-edge sill"), ("none", "No sill")]
SILL_SHAPES = [("weathered", "Weathered (sloping top)"), ("square", "Square"),
               ("chamfer", "Chamfered front edge")]
HEADS = [("stone", "Stone lintel / stone arch"), ("brick", "Brick soldier course / brick arch"),
         ("none", "No head")]

DEFAULTS = {
    'style': 'sash', 'top': 'face', 'rise': 150.0, 'flip': False, 'flat': True, 'bars_back': True, 'remove_face': True, 'join': True, 'cut': True, 'lift': 0.01,
    'frame_w': 60.0, 'frame_d': 100.0,
    'sash_w': 45.0, 'sash_d': 40.0, 'bottom_rail': 70.0, 'meet_w': 35.0, 'meet': 50.0,
    'bar_w': 18.0, 'bar_d': 25.0,
    'cols': 3, 'rows': 2, 'cols_b': 3, 'rows_b': 2, 'arch_bars': 'fan',
    'leaves': 2, 'mullion_w': 60.0, 'transom': 0.0,
    'pivot': False, 'pivot_col': 2, 'pivot_row': 2,
    'open': False, 'sash_open': 40.0, 'open_angle': 50.0,
    'glass': False, 'glass_t': 4.0,
    'sill': 'stone', 'sill_shape': 'weathered', 'sill_h': 75.0, 'sill_p': 50.0, 'horn': 100.0,
    'head': 'brick', 'head_h': 215.0, 'head_p': 10.0, 'bearing': 100.0,
    'keystone': False, 'key_w': 150.0, 'key_up': 40.0, 'key_p': 15.0,
    'brick_w': 102.5, 'brick_t': 65.0, 'joint': 10.0,
}
INT_KEYS = ('cols', 'rows', 'cols_b', 'rows_b', 'leaves', 'pivot_col', 'pivot_row')
CHOICE_KEYS = ('style', 'top', 'arch_bars', 'sill', 'sill_shape', 'head')
BOOL_KEYS = ('flip', 'flat', 'bars_back', 'remove_face', 'join', 'cut', 'pivot', 'open', 'glass', 'keystone')
PRESET_KEYS = tuple(DEFAULTS)

BUILTIN_PRESETS = {
    "Victorian sash - 2 over 2": dict(style='sash', top='face', cols=2, rows=1, cols_b=2, rows_b=1,
                                      sill='stone', head='stone', keystone=False),
    "Georgian sash - 6 over 6": dict(style='sash', top='face', cols=3, rows=2, cols_b=3, rows_b=2,
                                     sill='stone', head='brick', keystone=False),
    "Round-top sash with fan": dict(style='sash', top='semi', cols=2, rows=2, cols_b=2, rows_b=2,
                                    arch_bars='fan', sill='stone', head='brick', keystone=True),
    "Cottage casement - 2 leaves": dict(style='casement', top='face', leaves=2, cols=2, rows=3,
                                        transom=0.0, sill='brick', head='brick', keystone=False),
    "Casement with top lights": dict(style='casement', top='face', leaves=3, cols=1, rows=2,
                                     cols_b=1, rows_b=1, transom=75.0, sill='stone', head='stone'),
    "Industrial cast iron - segmental": dict(style='fixed', top='segment', rise=150.0, cols=5, rows=6,
                                             bar_w=25.0, bar_d=35.0, frame_w=50.0, arch_bars='grid',
                                             pivot=True, pivot_col=3, pivot_row=3,
                                             sill='brick', head='brick', keystone=False),
    "Gothic chapel": dict(style='fixed', top='gothic', cols=2, rows=4, arch_bars='grid',
                          sill='stone', head='stone', keystone=False),
    "Bull's-eye": dict(style='fixed', top='circle', cols=2, rows=2, arch_bars='grid',
                       sill='none', head='brick', keystone=True),
    "1:80 print - 0.4 mm nozzle (sash)": dict(style='sash', flat=True, bars_back=True,
                                              bar_w=32.0, bar_d=32.0, frame_w=64.0, frame_d=80.0,
                                              sash_w=40.0, sash_d=24.0, bottom_rail=56.0, meet_w=32.0,
                                              glass_t=32.0),
    "Chunky for OO printing (sash)": dict(style='sash', frame_w=90.0, frame_d=120.0, sash_w=70.0,
                                          sash_d=50.0, bottom_rail=90.0, meet_w=55.0,
                                          bar_w=50.0, bar_d=40.0, glass_t=10.0),
}

Z = (0.0, 0.0, 1.0)


# ---------------------------------------------------------------------------
# Vector helpers (plain tuples)
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


# ---------------------------------------------------------------------------
# 2D polygons (x across the wall, y up, in mm)
# ---------------------------------------------------------------------------
def area2(poly):
    a = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        a += x1 * y2 - x2 * y1
    return a * 0.5


def bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), max(xs), min(ys), max(ys)


def clean(poly, eps=1e-6):
    """Drops repeated points; returns a counter-clockwise polygon or None."""
    out = []
    for p in poly:
        if not out or abs(p[0] - out[-1][0]) > eps or abs(p[1] - out[-1][1]) > eps:
            out.append((float(p[0]), float(p[1])))
    while len(out) > 1 and abs(out[0][0] - out[-1][0]) <= eps and abs(out[0][1] - out[-1][1]) <= eps:
        out.pop()
    # drop points that sit on a straight line between their neighbours
    k = 0
    while len(out) > 3 and k < len(out):
        a, b, c = out[k - 1], out[k], out[(k + 1) % len(out)]
        cr = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(cr) < 1e-9 * (1.0 + abs(b[0] - a[0]) + abs(b[1] - a[1])) ** 2 and \
                (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1]) >= 0:
            del out[k]
        else:
            k += 1
    if len(out) < 3:
        return None
    a = area2(out)
    if abs(a) < 1e-6:
        return None
    return out if a > 0 else out[::-1]


def clip_half(poly, a, b, c):
    """Keeps the part of poly where a*x + b*y + c >= 0."""
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


def clip_rect(poly, x0, x1, y0, y1):
    for a, b, c in ((1, 0, -x0), (-1, 0, x1), (0, 1, -y0), (0, -1, y1)):
        poly = clip_half(poly, a, b, c)
        if len(poly) < 3:
            return None
    return clean(poly)


def clip_convex(poly, conv):
    """Clips poly by a convex counter-clockwise polygon."""
    n = len(conv)
    for i in range(n):
        p, q = conv[i], conv[(i + 1) % n]
        dx, dy = q[0] - p[0], q[1] - p[1]
        poly = clip_half(poly, -dy, dx, dy * p[0] - dx * p[1])
        if len(poly) < 3:
            return None
    return clean(poly)


def offset_poly(poly, d):
    """Moves every edge of a counter-clockwise polygon inwards by d (a number, or
    one distance per edge). Keeps the same number of points."""
    n = len(poly)
    ds = list(d) if isinstance(d, (list, tuple)) else [float(d)] * n
    lines = []
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        ex, ey = q[0] - p[0], q[1] - p[1]
        L = math.hypot(ex, ey) or 1e-12
        ex, ey = ex / L, ey / L
        nx, ny = -ey, ex
        lines.append(((p[0] + nx * ds[i], p[1] + ny * ds[i]), (ex, ey), (nx, ny)))
    out = []
    lim = 4.0 * max(max(ds), 1e-9)
    for j in range(n):
        (a, ea, na), (b, eb, nb) = lines[j - 1], lines[j]
        cr = ea[0] * eb[1] - ea[1] * eb[0]
        P = poly[j]
        if abs(cr) < 1e-9:
            pt = (P[0] + nb[0] * ds[j], P[1] + nb[1] * ds[j])
        else:
            t = ((b[0] - a[0]) * eb[1] - (b[1] - a[1]) * eb[0]) / cr
            pt = (a[0] + ea[0] * t, a[1] + ea[1] * t)
        dx, dy = pt[0] - P[0], pt[1] - P[1]
        L = math.hypot(dx, dy)
        if L > lim:
            pt = (P[0] + dx / L * lim, P[1] + dy / L * lim)
        out.append(pt)
    return out


def _seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 < 1e-18 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def poly_dist(p, poly):
    return min(_seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def poly_dev(a, b):
    """How far apart two outlines are (largest point-to-outline distance either way)."""
    return max(max(poly_dist(p, b) for p in a), max(poly_dist(p, a) for p in b))


def edge_widths(poly, side, bottom=None, top=None):
    """A width per edge: `bottom` on the flat bottom edge, `top` on a flat top edge."""
    x0, x1, y0, y1 = bbox(poly)
    tol = 1e-3 * (1.0 + y1 - y0)
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        w = side
        if abs(q[1] - p[1]) <= tol and abs(q[0] - p[0]) > tol:
            ym = (p[1] + q[1]) / 2
            if bottom is not None and abs(ym - y0) <= tol:
                w = bottom
            elif top is not None and abs(ym - y1) <= tol:
                w = top
        out.append(w)
    return out


# ---------------------------------------------------------------------------
# Solids (closed lists of faces, in local mm: x across, y up, z out of the wall)
# ---------------------------------------------------------------------------
class Solid:
    def __init__(self):
        self.faces = []

    def add(self, pts):
        self.faces.append([tuple(p) for p in pts])

    def volume(self):
        v = 0.0
        for pts in self.faces:
            for j in range(1, len(pts) - 1):
                v += v_dot(pts[0], v_cross(pts[j], pts[j + 1]))
        return v / 6.0

    def fix(self):
        if self.volume() < 0:
            self.faces = [list(reversed(p)) for p in self.faces]
        return self

    def mapped(self, fn):
        s = Solid()
        s.faces = [[fn(p) for p in f] for f in self.faces]
        s.kind = getattr(self, 'kind', 'part')
        s.mortar = getattr(self, 'mortar', False)
        s.part = getattr(self, 'part', None)
        s.paint = getattr(self, 'paint', None)
        s.paint_kind = getattr(self, 'paint_kind', None)
        return s.fix()


def prism(poly, z0, z1):
    poly = clean(poly)
    if poly is None or z1 - z0 < 1e-9:
        return None
    s = Solid()
    s.kind = "block (%d sides)" % len(poly)
    s.add([(x, y, z1) for x, y in poly])
    s.add([(x, y, z0) for x, y in reversed(poly)])
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        s.add([(ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1)])
    return s.fix()


def band(inner, outer, z0, z1, closed=False):
    """A solid strip between two matching lines of points (a frame when closed).
    Walking along the lines, `outer` is on the right."""
    n = len(inner)
    s = Solid()
    s.kind = ("frame ring (%d sides)" if closed else "curved strip (%d steps)") % n
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        j = (i + 1) % n
        a, b, c, d = inner[i], inner[j], outer[j], outer[i]
        s.add([(d[0], d[1], z1), (c[0], c[1], z1), (b[0], b[1], z1), (a[0], a[1], z1)])
        s.add([(a[0], a[1], z0), (b[0], b[1], z0), (c[0], c[1], z0), (d[0], d[1], z0)])
        s.add([(d[0], d[1], z0), (c[0], c[1], z0), (c[0], c[1], z1), (d[0], d[1], z1)])
        s.add([(a[0], a[1], z1), (b[0], b[1], z1), (b[0], b[1], z0), (a[0], a[1], z0)])
    if not closed:
        a, d = inner[0], outer[0]
        s.add([(a[0], a[1], z0), (d[0], d[1], z0), (d[0], d[1], z1), (a[0], a[1], z1)])
        a, d = inner[-1], outer[-1]
        s.add([(a[0], a[1], z1), (d[0], d[1], z1), (d[0], d[1], z0), (a[0], a[1], z0)])
    return s.fix()


def ring(outer, inner, z0, z1):
    """A frame between a counter-clockwise outline and its inward offset."""
    return band(inner, outer, z0, z1, closed=True)


def along_x(section_zy, x0, x1):
    """A solid running along x from x0 to x1 with a (z, y) cross-section."""
    sec = clean(section_zy)
    if sec is None:
        return None
    p = prism(sec, x0, x1)          # built with (z, y, x) ...
    if p is None:
        return None
    p = p.mapped(lambda q: (q[2], q[1], q[0]))   # ... then turned
    p.kind = "sill profile"
    return p


# ---------------------------------------------------------------------------
# Window outline shapes
# ---------------------------------------------------------------------------
def arc_pts(cx, cy, R, a0, a1):
    n = max(4, int(math.ceil(abs(a1 - a0) / (math.pi / 24))))
    return [(cx + R * math.cos(a0 + (a1 - a0) * i / n), cy + R * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def make_shape(kind, x0, x1, y0, y1, rise=0.0):
    """A window outline. Arcs are (cx, cy, R, from angle, to angle), running from the right
    springing over the top to the left. Raises ValueError if it doesn't fit."""
    w, h = x1 - x0, y1 - y0
    cx = (x0 + x1) / 2
    sh = {'kind': kind, 'arcs': [], 'ys': None, 'cx': cx, 'flat_bottom': True}
    if kind == 'flat':
        sh['poly'] = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    elif kind == 'semi':
        ys = y1 - w / 2
        if ys < y0 + 0.05 * h:
            raise ValueError("This opening isn't tall enough for a semicircular top "
                             "(it needs to be taller than half its width). Try Segmental.")
        sh['arcs'] = [(cx, ys, w / 2, 0.0, math.pi)]
        sh['ys'] = ys
    elif kind == 'segment':
        r = max(1.0, min(rise, w / 2, h * 0.95))
        R = (w * w / 4 + r * r) / (2 * r)
        cy = y1 - R
        ys = y1 - r
        a = math.atan2(ys - cy, x1 - cx)
        sh['arcs'] = [(cx, cy, R, a, math.pi - a)]
        sh['ys'] = ys
    elif kind == 'gothic':
        ys = y1 - w * math.sin(math.pi / 3)
        if ys < y0 + 0.05 * h:
            raise ValueError("This opening isn't tall enough for a pointed top "
                             "(it needs to be taller than 0.87 x its width).")
        sh['arcs'] = [(x0, ys, w, 0.0, math.pi / 3), (x1, ys, w, 2 * math.pi / 3, math.pi)]
        sh['ys'] = ys
    elif kind == 'circle':
        R = min(w, h) / 2
        cy = (y0 + y1) / 2
        sh['arcs'] = [(cx, cy, R, -math.pi / 2, 1.5 * math.pi)]
        sh['poly'] = arc_pts(cx, cy, R, -math.pi / 2, 1.5 * math.pi)[:-1]
        sh['flat_bottom'] = False
        sh['closed'] = True
    else:
        raise ValueError("Unknown top shape")
    if 'poly' not in sh:
        pts = [(x0, y0), (x1, y0)]
        for k, (acx, acy, R, a0, a1) in enumerate(sh['arcs']):
            ap = arc_pts(acx, acy, R, a0, a1)
            pts.extend(ap if k == 0 else ap[1:])
        sh['poly'] = pts
    sh['poly'] = clean(sh['poly'])
    sh['box'] = bbox(sh['poly'])
    return sh


def fit_shape(poly, top, rise):
    """Works out the window outline for an opening. With 'face' the face's own outline
    is used, and recognised as square, round, segmental, pointed or circular if it is
    one, so the head can follow it."""
    poly = clean(poly)
    if poly is None:
        raise ValueError("That face has no area.")
    x0, x1, y0, y1 = bbox(poly)
    w, h = x1 - x0, y1 - y0
    if w < 1.0 or h < 1.0:
        raise ValueError("That opening is too small.")
    if top != 'face':
        return make_shape(top, x0, x1, y0, y1, rise)
    tol = max(2.0, 0.015 * max(w, h))
    cands = ['flat', 'semi', 'gothic', 'circle']
    right = [p[1] for p in poly if abs(p[0] - x1) < tol]
    ys_r = max(right) if right else y1
    if y1 - ys_r > tol:
        cands.append(('segment', y1 - ys_r))
    best, best_dev = None, None
    for c in cands:
        kind, r = (c if isinstance(c, tuple) else (c, rise))
        try:
            sh = make_shape(kind, x0, x1, y0, y1, r)
        except ValueError:
            continue
        dev = poly_dev(poly, sh['poly'])
        if dev < tol and (best_dev is None or dev < best_dev):
            best, best_dev = sh, dev
    if best is not None:
        return best
    # any other shape: use the outline as it is, with a flat head over it
    return {'kind': 'poly', 'arcs': [], 'ys': None, 'cx': (x0 + x1) / 2, 'poly': poly,
            'box': (x0, x1, y0, y1),
            'flat_bottom': sum(1 for p in poly if abs(p[1] - y0) < tol) >= 2}


# ---------------------------------------------------------------------------
# Glazing bars
# ---------------------------------------------------------------------------
def grid_lines(G, cols, rows, mode, sh, bw):
    """Where the bars go: (x positions, y positions, top of the grid, arch springing or None)."""
    x0, x1, y0, y1 = bbox(G)
    ys = sh.get('ys')
    spring = None
    ylim = y1
    if ys is not None and mode != 'grid' and y0 + bw < ys < y1 - bw:
        spring = ys
        ylim = ys
    xs = [x0 + (x1 - x0) * i / cols for i in range(1, cols)]
    yl = [y0 + (ylim - y0) * j / rows for j in range(1, rows)]
    return xs, yl, ylim, spring


def bars(G, cols, rows, mode, sh, bw, z0, z1, embed=0.0):
    """Glazing bars laid out over G. With embed, their ends run that far into the frame
    round G, so bar and frame overlap instead of just touching (clean for booleans)."""
    out = []
    cols, rows = max(1, int(cols)), max(1, int(rows))
    x0, x1, y0, y1 = bbox(G)
    xs, yl, ylim, spring = grid_lines(G, cols, rows, mode, sh, bw)
    if embed > 0:
        Gc = clean(offset_poly(G, -embed))
        if Gc:
            G = Gc
    top = ylim + bw / 2 if spring is not None else y1 + 1
    pieces = []
    for xc in xs:
        pieces.append(clip_rect(G, xc - bw / 2, xc + bw / 2, y0 - 1, top))
    for yc in yl:
        pieces.append(clip_rect(G, x0 - 1, x1 + 1, yc - bw / 2, yc + bw / 2))
    if spring is not None:
        pieces.append(clip_rect(G, x0 - 1, x1 + 1, spring - bw / 2, spring + bw / 2))
        if mode == 'fan':
            cx = sh['cx']
            k = cols + 1
            L = 2.0 * (x1 - x0 + y1 - y0)
            above = clip_half(G, 0, 1, -spring)
            for i in range(1, k):
                a = math.pi * i / k
                dx, dy = math.cos(a), math.sin(a)
                nx, ny = -dy * bw / 2, dx * bw / 2
                sp = [(cx - nx, spring - ny), (cx + dx * L - nx, spring + dy * L - ny),
                      (cx + dx * L + nx, spring + dy * L + ny), (cx + nx, spring + ny)]
                sp = clean(sp)
                if sp and len(above) >= 3:
                    pieces.append(clip_convex(above, sp))
    for pc in pieces:
        if pc:
            s = prism(pc, z0, z1)
            if s:
                out.append(s)
    return out


def sash(R, side, bottom, top, cols, rows, mode, sh, v, z0, z1, grow=0.0):
    """A sash or leaf: its frame, bars and glass. Returns (solids, glass solids).
    grow pushes its outside edge that far into whatever surrounds it, so parts overlap
    rather than meet face to face."""
    G = offset_poly(R, edge_widths(R, side, bottom, top))
    if clean(G) is None or area2(G) <= 0:
        raise ValueError("The panes don't fit: the sash or frame widths are too big for this opening.")
    Rg = offset_poly(R, -grow) if grow > 0 else R
    flat = v.get('flat', True)
    base = v.get('_base', 0.0)
    bd = min(v['bar_d'], z1 - z0)
    zm = (z0 + z1) / 2
    embed = min(v['bar_w'] * 0.4, side * 0.4)
    if flat:
        # printed flat: every part goes right down to the base (the face, or the back of the wall)
        sol = [ring(Rg, G, base, z1)]
        if v.get('bars_back', True):
            # glazing bars as one thin layer at the very back, lying on the print bed
            sol += bars(G, cols, rows, mode, sh, v['bar_w'], base, base + v['bar_d'], embed)
        else:
            sol += bars(G, cols, rows, mode, sh, v['bar_w'], base, zm + bd / 2, embed)
    else:
        sol = [ring(Rg, G, z0, z1)]
        sol += bars(G, cols, rows, mode, sh, v['bar_w'], zm - bd / 2, zm + bd / 2, embed)
    glass = []
    if v['glass']:
        if flat:
            t = min(v['glass_t'], z1 - base)
            g = prism(offset_poly(G, -min(5.0, side * 0.3)), base, base + t)
        else:
            t = min(v['glass_t'], (z1 - z0) * 0.8)
            g = prism(offset_poly(G, -min(5.0, side * 0.3)), zm - t / 2, zm + t / 2)
        if g:
            glass.append(g)
    return sol, glass


# ---------------------------------------------------------------------------
# Moving opening parts
# ---------------------------------------------------------------------------
def swing_vertical(xh, zh, ang, right_hinge):
    """Turns a side-hung leaf about an upright hinge at x = xh, so it swings outwards."""
    a = -ang if right_hinge else ang
    c, s = math.cos(a), math.sin(a)

    def f(p):
        rx, rz = p[0] - xh, p[2] - zh
        return (xh + rx * c - rz * s, p[1], zh + rx * s + rz * c)
    return f


def swing_horizontal(yh, zh, ang):
    """Turns a part about a level axis at y = yh: below the axis moves outwards."""
    c, s = math.cos(ang), math.sin(ang)

    def f(p):
        ry, rz = p[1] - yh, p[2] - zh
        return (p[0], yh + ry * c + rz * s, zh - ry * s + rz * c)
    return f


# ---------------------------------------------------------------------------
# The window itself
# ---------------------------------------------------------------------------
def build_window(sh, v):
    """Returns {'window': [...], 'glass': [...], 'sill': [...], 'head': [...]} in local mm."""
    P = sh['poly']
    fw = v['frame_w']
    sd = v['sash_d']
    style = v['style']
    fd = v['frame_d']
    if style == 'sash':
        fd = max(fd, 2 * sd + 25.0)
    elif style == 'casement':
        fd = max(fd, sd + 5.0)
    zf = fd                 # the front of the frame
    base = v.get('_base', 0.0)          # the back: the face, or the back of the wall
    ov = min(2.0, fw * 0.25)            # how far neighbouring parts overlap
    win, glass = [], []
    O = offset_poly(P, fw)
    if clean(O) is None or area2(O) <= 0:
        raise ValueError("The frame width is too big for this opening.")
    win.append(ring(P, O, base, zf))
    O = clean(O)
    ox0, ox1, oy0, oy1 = bbox(O)
    mode = v['arch_bars']
    opened = v['open']

    if style == 'sash':
        mw = v['meet_w']
        ym = oy0 + (oy1 - oy0) * v['meet'] / 100.0
        if sh.get('ys') is not None:
            ym = min(ym, sh['ys'] - mw)
        T = clip_rect(O, ox0 - 1, ox1 + 1, ym - mw / 2, oy1 + 1)
        B = clip_rect(O, ox0 - 1, ox1 + 1, oy0 - 1, ym + mw / 2)
        if not T or not B:
            raise ValueError("The meeting rail is outside the window: change 'Meeting rail height'.")
        s1, g1 = sash(T, v['sash_w'], mw, None, v['cols'], v['rows'], mode, sh, v,
                      zf - 10 - sd, zf - 10, grow=ov)
        s2, g2 = sash(B, v['sash_w'], v['bottom_rail'], mw, v['cols_b'], v['rows_b'], mode, sh, v,
                      zf - 15 - 2 * sd, zf - 15 - sd, grow=ov * 0.5)
        if opened and v['sash_open'] > 0:
            stop = sh['ys'] if sh.get('ys') is not None else oy1
            travel = max(0.0, stop - (ym + mw / 2)) * min(100.0, v['sash_open']) / 100.0
            up = (lambda p: (p[0], p[1] + travel, p[2]))
            s2 = [s.mapped(up) for s in s2]
            g2 = [s.mapped(up) for s in g2]
        win += s1 + s2
        glass += g1 + g2

    elif style == 'casement':
        L = max(1, int(v['leaves']))
        mw = v['mullion_w']
        yt = oy0 + (oy1 - oy0) * v['transom'] / 100.0 if v['transom'] > 0 else None
        cw = (ox1 - ox0) / L
        Og = clean(offset_poly(O, -ov)) or O       # mullions run into the frame
        for i in range(1, L):
            xm = ox0 + cw * i
            pc = clip_rect(Og, xm - mw / 2, xm + mw / 2, oy0 - 1 - ov, oy1 + 1 + ov)
            if pc:
                win.append(prism(pc, base, zf))
        if yt is not None:
            pc = clip_rect(Og, ox0 - 1 - ov, ox1 + 1 + ov, yt - mw / 2, yt + mw / 2)
            if pc:
                win.append(prism(pc, base, zf))
        # leaves only swing open when the window isn't being made flat for printing
        ang = math.radians(v['open_angle']) if (opened and not v.get('flat', True)) else 0.0
        for i in range(L):
            cx0 = ox0 + cw * i + (mw / 2 if i > 0 else -1)
            cx1 = ox0 + cw * (i + 1) - (mw / 2 if i < L - 1 else -1)
            low_top = (yt - mw / 2) if yt is not None else oy1 + 1
            cells = [('leaf', clip_rect(O, cx0, cx1, oy0 - 1, low_top))]
            if yt is not None:
                cells.append(('light', clip_rect(O, cx0, cx1, yt + mw / 2, oy1 + 1)))
            for what, R in cells:
                if not R:
                    continue
                if what == 'leaf':
                    so, gl = sash(R, v['sash_w'], v['sash_w'], None, v['cols'], v['rows'],
                                  mode, sh, v, zf - sd, zf, grow=ov)
                else:
                    so, gl = sash(R, v['sash_w'], None, None, v['cols_b'], v['rows_b'],
                                  mode, sh, v, zf - sd, zf, grow=ov)
                if ang > 0:
                    rx0, rx1, ry0, ry1 = bbox(R)
                    if what == 'leaf':
                        right = (L > 1 and i == L - 1)
                        f = swing_vertical(rx1 if right else rx0, zf, ang, right)
                    else:
                        f = swing_horizontal(ry1, zf, ang * 0.5)
                    so = [s.mapped(f) for s in so]
                    gl = [s.mapped(f) for s in gl]
                win += so
                glass += gl

    else:   # fixed / industrial
        bd = v['bar_d']
        bw = v['bar_w']
        z1 = zf - 5.0 if zf > 10.0 else zf
        z0 = max(0.0, z1 - bd)
        bd = z1 - z0
        zm = (z0 + z1) / 2
        flat = v.get('flat', True)
        if flat and v.get('bars_back', True):
            win += bars(O, v['cols'], v['rows'], mode, sh, bw, base, base + bd, ov)
        else:
            win += bars(O, v['cols'], v['rows'], mode, sh, bw, base if flat else z0, z1, ov)
        cell = None
        if v['pivot']:
            cols, rows = max(1, int(v['cols'])), max(1, int(v['rows']))
            xs, yl, ylim, spring = grid_lines(O, cols, rows, mode, sh, bw)
            c = min(max(1, int(v['pivot_col'])), cols) - 1
            r = min(max(1, int(v['pivot_row'])), rows) - 1
            xe = [ox0] + xs + [ox1]
            ye = [oy0] + yl + [ylim]
            cx0 = xe[c] + (bw / 2 if c > 0 else 0.0)
            cx1 = xe[c + 1] - (bw / 2 if c < cols - 1 else 0.0)
            cy0 = ye[r] + (bw / 2 if r > 0 else 0.0)
            cy1 = ye[r + 1] - (bw / 2 if (r < rows - 1 or spring is not None) else 0.0)
            R = clip_rect(O, cx0, cx1, cy0, cy1)
            if R:
                cell = bbox(R)
                so, gl = sash(R, bw * 0.8, None, None, 1, 1, 'grid', sh, v, z0, z1, grow=bw * 0.3)
                if opened and not flat:
                    f = swing_horizontal((cell[2] + cell[3]) / 2, zm, math.radians(v['open_angle']))
                    so = [s.mapped(f) for s in so]
                    gl = [s.mapped(f) for s in gl]
                win += so
                glass += gl
        if v['glass']:
            t = min(v['glass_t'], z1 if flat else bd * 0.8)
            gz0, gz1 = (base, base + t) if flat else (zm - t / 2, zm + t / 2)
            if cell is None:
                parts = [O]
            else:
                a0, a1, b0, b1 = cell
                parts = [clip_rect(O, ox0 - 1, a0, oy0 - 1, oy1 + 1),
                         clip_rect(O, a1, ox1 + 1, oy0 - 1, oy1 + 1),
                         clip_rect(O, a0, a1, oy0 - 1, b0),
                         clip_rect(O, a0, a1, b1, oy1 + 1)]
            for pc in parts:
                g = prism(pc, gz0, gz1) if pc else None
                if g:
                    glass.append(g)

    has_sill = v['sill'] != 'none' and sh.get('flat_bottom')
    sill = build_sill(sh, v, fd) if has_sill else []
    head = build_head(sh, v, fd) if v['head'] != 'none' else []
    # small blocks bridging the frame to the sill and head, so they overlap instead of
    # meeting face to face (these sit inside both, so they don't show)
    x0, x1, y0, y1 = sh['box']
    hb = v.get('_base_sh', base)
    if has_sill:
        win.append(prism([(x0 + ov, y0 - ov), (x1 - ov, y0 - ov), (x1 - ov, y0 + ov), (x0 + ov, y0 + ov)],
                         max(base, hb), zf - ov))
    if head:
        if sh['arcs']:
            L = _arch_len(sh)
            inner, outer = [], []
            n = max(4, int(L / 40.0))
            for i in range(n + 1):
                k, a = _arch_at(sh, ov + (L - 2 * ov) * i / n)
                cx, cy, R, _, _ = sh['arcs'][k]
                inner.append((cx + (R - ov) * math.cos(a), cy + (R - ov) * math.sin(a)))
                outer.append((cx + (R + ov) * math.cos(a), cy + (R + ov) * math.sin(a)))
            win.append(band(inner, outer, max(base, hb), zf - ov))
        else:
            win.append(prism([(x0 + ov, y1 - ov), (x1 - ov, y1 - ov), (x1 - ov, y1 + ov),
                              (x0 + ov, y1 + ov)], max(base, hb), zf - ov))
    return {'window': [s for s in win if s], 'glass': [s for s in glass if s],
            'sill': [s for s in sill if s], 'head': [s for s in head if s],
            'info': {'fd': fd, 'O': bbox(O), 'ym': locals().get('ym')}}


# ---------------------------------------------------------------------------
# Sills
# ---------------------------------------------------------------------------
def build_sill(sh, v, fd):
    """Under the opening, from the wall face out past the front of the frame."""
    x0, x1, y0, _ = sh['box']
    F = fd + v['sill_p']               # front of the sill
    xa, xb = x0 - v['horn'], x1 + v['horn']
    out = []
    h = v['sill_h'] if v['sill'] == 'stone' else v['brick_w']
    # back on the wall face, flat under the frame, then weathered (sloped) down to the front,
    # or square, or square with the top front edge chamfered
    b = v.get('_base_sh', v.get('_base', 0.0))
    shape = v.get('sill_shape', 'weathered')
    c = min(0.35 * h, 0.5 * max(1.0, F - b))          # the chamfer
    if shape == 'square':
        sec = [(b, y0 - h), (F, y0 - h), (F, y0), (b, y0)]
    elif shape == 'chamfer':
        sec = [(b, y0 - h), (F, y0 - h), (F, y0 - c), (F - c, y0), (b, y0)]
    else:
        sec = [(b, y0 - h), (F, y0 - h), (F, y0 - 0.3 * h), (fd, y0), (b, y0)]
    if v['sill'] == 'stone':
        out.append(along_x(sec, xa, xb))
        return out
    # brick on edge: bricks standing across the sill, laid out evenly from the middle
    J = v['joint']
    unit = v['brick_t'] + J
    n = max(1, int(round((xb - xa + J) / unit)))
    bw = (xb - xa + J) / n - J
    for i in range(n):
        a = xa + i * (bw + J)
        out.append(along_x(sec, a, a + bw))
    # mortar behind the joints, set back so the joints show
    k = 3.0
    if shape == 'square':
        mort = [(b, y0 - h + 1.0), (F - k, y0 - h + 1.0), (F - k, y0 - k), (b, y0 - k)]
    elif shape == 'chamfer':
        mort = [(b, y0 - h + 1.0), (F - k, y0 - h + 1.0), (F - k, y0 - c - 0.4 * k),
                (F - c - 0.4 * k, y0 - k), (b, y0 - k)]
    else:
        slope = 0.7 * h / max(1e-6, F - fd)
        mort = [(b, y0 - h + 1.0), (F - k, y0 - h + 1.0), (F - k, y0 - 0.3 * h - k + slope * k),
                (fd, y0 - k), (b, y0 - k)]
    out.append(_mortar(along_x(mort, xa + 1.0, xb - 1.0)))
    return out


def _mortar(s):
    if s is not None:
        s.mortar = True          # left out of the preview drawing (it sits behind the joints)
    return s


# ---------------------------------------------------------------------------
# Heads: lintels, soldier courses and arches
# ---------------------------------------------------------------------------
def _arch_len(sh):
    return sum(R * abs(a1 - a0) for _, _, R, a0, a1 in sh['arcs'])


def _arch_at(sh, s):
    """(arc index, angle) at distance s along the intrados from the right springing."""
    for k, (cx, cy, R, a0, a1) in enumerate(sh['arcs']):
        L = R * abs(a1 - a0)
        if s <= L + 1e-9 or k == len(sh['arcs']) - 1:
            return k, a0 + (a1 - a0) * min(1.0, max(0.0, s / L if L else 0.0))
        s -= L
    return len(sh['arcs']) - 1, sh['arcs'][-1][4]


def _arch_pts(sh, s, hh):
    """Intrados and extrados points at distance s along the arch. On a pointed arch the
    extrados is cut off at the centre line so the two sides meet in a point."""
    k, a = _arch_at(sh, s)
    cx, cy, R, a0, a1 = sh['arcs'][k]
    inner = (cx + R * math.cos(a), cy + R * math.sin(a))
    ao = a
    if sh['kind'] == 'gothic':
        # stretch the extrados so both sides reach the centre line at the same height
        lim = math.acos(max(-1.0, min(1.0, (R / 2) / (R + hh))))
        ao = a * lim / (math.pi / 3) if k == 0 else math.pi - (math.pi - a) * lim / (math.pi / 3)
    outer = (cx + (R + hh) * math.cos(ao), cy + (R + hh) * math.sin(ao))
    return inner, outer


def _arch_ranges(sh, key_half):
    """Stretches of the arch (in distance along it) left after the keystone, split at the
    joins between arcs so no stone crosses one."""
    L = _arch_len(sh)
    mid = L / 2
    cuts = [0.0]
    acc = 0.0
    for _, _, R, a0, a1 in sh['arcs'][:-1]:
        acc += R * abs(a1 - a0)
        cuts.append(acc)
    cuts.append(L)
    out = []
    for a, b in zip(cuts[:-1], cuts[1:]):
        if key_half > 0:
            for lo, hi in ((a, min(b, mid - key_half)), (max(a, mid + key_half), b)):
                if hi - lo > 1e-6:
                    out.append((lo, hi))
        else:
            out.append((a, b))
    return out


def _band_piece(sh, s0, s1, hh, z0, z1, inset=0.0):
    # all the way round a round window: a closed ring, not a strip whose two ends meet
    whole = sh.get('closed') and s0 <= 1e-6 and s1 >= _arch_len(sh) - 1e-6
    n = max(2, int(math.ceil((s1 - s0) / 40.0)) + 1)
    inner, outer = [], []
    for i in range(n - 1 if whole else n):
        s = s0 + (s1 - s0) * i / (n - 1)
        a, b = _arch_pts(sh, s, hh - inset)
        if inset:
            k, ang = _arch_at(sh, s)
            cx, cy, R, _, _ = sh['arcs'][k]
            a = (cx + (R + inset) * math.cos(ang), cy + (R + inset) * math.sin(ang))
        inner.append(a)
        outer.append(b)
    return band(inner, outer, z0, z1, closed=bool(whole))


def _radial(sh, s):
    """Unit direction out from the arch centre through the intrados at distance s.
    A pointed arch uses the middle of its springing line, so its keystone is even."""
    pt = _arch_pts(sh, s, 0.0)[0]
    if sh['kind'] == 'gothic':
        c = (sh['cx'], sh['ys'])
    else:
        k, _ = _arch_at(sh, _arch_len(sh) / 2)
        c = sh['arcs'][k][:2]
    dx, dy = pt[0] - c[0], pt[1] - c[1]
    L = math.hypot(dx, dy) or 1.0
    return (dx / L, dy / L)


def _keystone_arch(sh, v, hh, zb, zfront):
    return prism(_arch_key_poly(sh, v, hh), zb, zfront + v['key_p'])


def _arch_key_poly(sh, v, hh):
    """A tapered keystone: its bottom follows the arch, its sides run straight out from the
    arch centre (wider at the top), and it stands above the arch by key_up."""
    L = _arch_len(sh)
    mid = L / 2
    kh = v['key_w'] / 2
    bottom = [_arch_pts(sh, mid - kh + 2 * kh * i / 8, hh)[0] for i in range(9)]   # right to left
    up = hh + v['key_up']
    (rx, ry), (lx, ly) = _radial(sh, mid - kh), _radial(sh, mid + kh)
    tr = (bottom[0][0] + rx * up, bottom[0][1] + ry * up)
    tl = (bottom[-1][0] + lx * up, bottom[-1][1] + ly * up)
    # level the top off at the height of the higher corner
    ytop = max(tr[1], tl[1])
    tr = (bottom[0][0] + rx * up * (ytop - bottom[0][1]) / max(1e-6, tr[1] - bottom[0][1]), ytop)
    tl = (bottom[-1][0] + lx * up * (ytop - bottom[-1][1]) / max(1e-6, tl[1] - bottom[-1][1]), ytop)
    return bottom + [tl, tr]


def _flat_key_poly(cx, y1, hh, v):
    kb = v['key_w'] / 2
    kt = kb * 1.35
    top = y1 + hh + v['key_up']
    return [(cx - kb, y1), (cx + kb, y1), (cx + kt, top), (cx - kt, top)]


def _flat_keystone(cx, y1, hh, v, zb, zfront):
    return prism(_flat_key_poly(cx, y1, hh, v), zb, zfront + v['key_p'])


def _soldiers(xa, xb, unit, J):
    """Brick positions filling xa..xb with joints between, as near as possible to `unit`."""
    n = max(1, int(round((xb - xa + J) / unit)))
    bw = (xb - xa + J) / n - J
    return [(xa + i * (bw + J), xa + i * (bw + J) + bw) for i in range(n)]


def build_head(sh, v, fd):
    """Over the opening, from the wall face out past the front of the frame."""
    x0, x1, _, y1 = sh['box']
    hh = v['head_h']
    zb = v.get('_base_sh', v.get('_base', 0.0))
    zfront = fd + v['head_p']
    out = []
    key = v['keystone']
    if sh['arcs']:
        kh = v['key_w'] / 2 if key else 0.0
        ranges = _arch_ranges(sh, kh)
        if v['head'] == 'stone':
            for a, b in ranges:
                out.append(_band_piece(sh, a, b, hh, zb, zfront))
        else:
            J = v['joint']
            unit = v['brick_t'] + J
            for a, b in ranges:
                n = max(1, int(round((b - a) / unit)))
                step = (b - a) / n
                for i in range(n):
                    s0 = a + i * step + (J / 2 if (i > 0 or a > 1e-6) else 0.0)
                    s1 = a + (i + 1) * step - (J / 2 if (i < n - 1 or b < _arch_len(sh) - 1e-6) else 0.0)
                    if s1 - s0 < 1.0:
                        continue
                    i0, o0 = _arch_pts(sh, s0, hh)
                    i1, o1 = _arch_pts(sh, s1, hh)
                    out.append(band([i0, i1], [o0, o1], zb, zfront))
                # mortar behind the joints
                out.append(_mortar(_band_piece(sh, a, b, hh - 1.0, zb, zfront - 3.0, inset=1.0)))
        if key:
            out.append(_keystone_arch(sh, v, hh, zb, zfront))
        return out

    # flat head
    xa, xb = x0 - v['bearing'], x1 + v['bearing']
    cx = (x0 + x1) / 2
    kw = v['key_w'] / 2
    if v['head'] == 'stone':
        out.append(prism([(xa, y1), (xb, y1), (xb, y1 + hh), (xa, y1 + hh)], zb, zfront))
    else:
        J = v['joint']
        unit = v['brick_t'] + J
        if key:      # the same number of bricks each side of the keystone
            runs = _soldiers(xa, cx - kw - J, unit, J) + _soldiers(cx + kw + J, xb, unit, J)
        else:
            runs = _soldiers(xa, xb, unit, J)
        for a, b in runs:
            out.append(prism([(a, y1), (b, y1), (b, y1 + hh), (a, y1 + hh)], zb, zfront))
        out.append(_mortar(prism([(xa + 1, y1), (xb - 1, y1), (xb - 1, y1 + hh - 3),
                                  (xa + 1, y1 + hh - 3)], zb, zfront - 3.0)))
    if key:
        out.append(_flat_keystone(cx, y1, hh, v, zb, zfront))
    return out


# ---------------------------------------------------------------------------
# Reading the selected faces
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
            continue                      # a group, not a face
        vs = getattr(e, 'vertices', None)
        if vs is not None and not callable(vs) and len(_items(vs)) >= 3:
            out.append(e)
    return out


def face_openings(face, flip=False):
    """(frame, [opening outlines in mm]) for a face: its holes if it has any,
    otherwise its own outline. frame = (origin, right, up, out) in metres."""
    pts = [p for p in (_pos(v) for v in _items(face.vertices)) if p is not None]
    if len(pts) < 3:
        raise ValueError("That face has no corners I can read.")
    n = _newell(pts)
    if flip:
        n = v_mul(n, -1.0)
    if v_len(n) < 0.5:
        raise ValueError("That face isn't flat enough to read.")
    if abs(n[2]) < 0.999:
        # a wall or a sloping roof: 'up' runs up the slope, 'across' is level
        U = v_norm(v_cross(Z, n))
    else:
        # a flat roof or floor: line the window up with the face's longest edge
        k = max(range(len(pts)), key=lambda i: v_len(v_sub(pts[(i + 1) % len(pts)], pts[i])))
        e = v_sub(pts[(k + 1) % len(pts)], pts[k])
        U = v_norm(v_sub(e, v_mul(n, v_dot(e, n))))
    V = v_cross(n, U)
    O = pts[0]
    loops = []
    for h in _items(getattr(face, 'holes', None)):
        hp = [p for p in (_pos(v) for v in _items(h)) if p is not None]
        if len(hp) >= 3:
            loops.append(hp)
    if not loops:
        loops = [pts]
    polys = []
    for lp in loops:
        q = clean([(v_dot(v_sub(p, O), U) / SCALE, v_dot(v_sub(p, O), V) / SCALE) for p in lp])
        if q:
            polys.append(q)
    return (O, U, V, n), polys


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


WALL_MAX = 2.0         # metres: the back of the wall must be nearer than this


def _pip3(pt, poly, U, V):
    """Is a point inside a polygon (both in the same plane, using in-plane axes U, V)?"""
    q = (v_dot(pt, U), v_dot(pt, V))
    pp = [(v_dot(p, U), v_dot(p, V)) for p in poly]
    inside = False
    j = len(pp) - 1
    for i in range(len(pp)):
        (xi, yi), (xj, yj) = pp[i], pp[j]
        if (yi > q[1]) != (yj > q[1]) and q[0] < (xj - xi) * (q[1] - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def find_back(mesh, pts, n, exclude=None):
    """(face, depth): the nearest face behind the points (facing the other way) that the
    whole outline fits on, i.e. the back of the wall. None if there isn't one."""
    U = v_norm(v_sub(pts[1], pts[0]))
    V = v_cross(n, U)
    best = None
    for f in _items(getattr(mesh, 'faces', None)):
        if f is exclude:
            continue
        fp = [p for p in (_pos(v) for v in _items(getattr(f, 'vertices', None))) if p is not None]
        if len(fp) < 3 or v_dot(_newell(fp), n) > -0.999:
            continue
        depth = v_dot(v_sub(pts[0], fp[0]), n)
        if depth <= 1e-7 or depth > WALL_MAX or (best is not None and depth >= best[1]):
            continue
        back = [v_sub(p, v_mul(n, depth)) for p in pts]
        if not all(_pip3(p, fp, U, V) for p in back):
            continue
        holes = [[p for p in (_pos(v) for v in _items(h)) if p is not None]
                 for h in _items(getattr(f, 'holes', None))]
        if any(len(h) >= 3 and _pip3(p, h, U, V) for h in holes for p in back):
            continue
        best = (f, depth)
    return best


def through_info(mesh, face):
    """For a face drawn on the front of a solid wall: the face's corners, its outward
    direction, the back face of the wall behind it and the wall thickness. None when
    there's no back face close behind (a single sheet, or the far side of a building)."""
    outer = [p for p in (_pos(v) for v in _items(face.vertices)) if p is not None]
    if len(outer) < 3:
        return None
    n = _newell(outer)
    best = find_back(mesh, outer, n, face)
    if best is None:
        return None
    return {'outer': outer, 'n': n, 'back': best[0], 'depth': best[1],
            'attrs': dict(getattr(face, 'attrs', None) or {})}


def find_host(mesh, face, info):
    """(wall face, hole index): the front wall face that has the drawn face as a hole."""
    outer, n = info['outer'], info['n']
    tol = 1e-7
    for f in _items(getattr(mesh, 'faces', None)):
        if f is face:
            continue
        fp = [p for p in (_pos(v) for v in _items(getattr(f, 'vertices', None))) if p is not None]
        if len(fp) < 3 or v_dot(_newell(fp), n) < 0.999 or abs(v_dot(v_sub(fp[0], outer[0]), n)) > 1e-6:
            continue
        for k, h in enumerate(_items(getattr(f, 'holes', None))):
            hp = [p for p in (_pos(v) for v in _items(h)) if p is not None]
            if len(hp) == len(outer) and all(min(v_len(v_sub(a, b)) for b in hp) < tol for a in outer):
                return f, k
    return None


def cut_through(scene, mesh, info, host=None, outline=None):
    """Opens the wall behind a removed front face. With `host` (the wall face round it)
    and a bigger `outline`, the hole in the wall face is first made that shape, so the
    sill and head go through the wall too. Then: sides from the front to the back of the
    wall, and the same hole in the back face."""
    n, depth = info['n'], info['depth']
    if host is not None and outline:
        f, k = host
        loops = _items(getattr(f, 'hole_loops', None))
        old = loops[k] if k < len(loops) else None
        if old is None:
            outline = None
        else:
            edges = []
            for i in range(len(old)):
                try:
                    e = mesh.find_edge(old[i], old[(i + 1) % len(old)])
                    if e is not None:
                        edges.append(e)
                except Exception:
                    pass
            mesh.remove_hole(f, old)
            mesh.add_hole(f, [QVector3D(*p) for p in outline])
            for e in edges:
                try:
                    if not e.faces:
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
    else:
        outline = None
    outer = outline or info['outer']
    shift = v_mul(n, -depth)
    inner = [v_add(p, shift) for p in outer]
    k = len(outer)
    for i in range(k):
        a, b = outer[i], outer[(i + 1) % k]
        q = [a, b, v_add(b, shift), v_add(a, shift)]
        into = v_cross(n, v_sub(b, a))              # towards the middle of the opening
        if v_dot(_newell(q), into) < 0:
            q.reverse()
        f = mesh.add_face([QVector3D(*p) for p in q])
        try:
            if info['attrs']:
                f.attrs = dict(info['attrs'])
        except Exception:
            pass
    mesh.add_hole(info['back'], [QVector3D(*p) for p in reversed(inner)])
    return outline is not None


def cut_outline(sh, v):
    """The shape to cut out of the wall: the window plus its sill and head (and keystone),
    as one outline (local mm, counter-clockwise)."""
    P = sh['poly']
    if sh['kind'] == 'poly':
        return list(P)
    x0, x1, y0, y1 = sh['box']
    has_sill = v['sill'] != 'none' and sh.get('flat_bottom')
    has_head = v['head'] != 'none'
    hh = v['head_h']
    key = has_head and v['keystone']

    def extrados(s0, s1):
        n = max(2, int(math.ceil((s1 - s0) / 30.0)) + 1)
        return [_arch_pts(sh, s0 + (s1 - s0) * i / (n - 1), hh)[1] for i in range(n)]

    if sh['kind'] == 'circle':
        if not has_head:
            return list(P)
        L = _arch_len(sh)
        if key:
            kp = _arch_key_poly(sh, v, hh)
            kh = v['key_w'] / 2
            pts = extrados(0.0, L / 2 - kh) + [kp[-1], kp[-2]] + extrados(L / 2 + kh, L)
        else:
            pts = extrados(0.0, L)
        return clean(pts[:-1]) or list(P)

    out = []
    if has_sill:
        h = v['sill_h'] if v['sill'] == 'stone' else v['brick_w']
        xa, xb = x0 - v['horn'], x1 + v['horn']
        out += [(xa, y0 - h), (xb, y0 - h), (xb, y0), (x1, y0)]
    else:
        out += [(x0, y0), (x1, y0)]
    if sh['arcs']:
        if has_head:
            L = _arch_len(sh)
            out.append((x1, sh['ys']))
            if key:
                kp = _arch_key_poly(sh, v, hh)
                kh = v['key_w'] / 2
                out += extrados(0.0, L / 2 - kh) + [kp[-1], kp[-2]] + extrados(L / 2 + kh, L)
            else:
                out += extrados(0.0, L)
            out.append((x0, sh['ys']))
        else:
            out += list(P[2:])
    else:
        if has_head:
            xa, xb = x0 - v['bearing'], x1 + v['bearing']
            top = y1 + hh
            out += [(x1, y1), (xb, y1), (xb, top)]
            if key and v['key_up'] > 0:
                cx = (x0 + x1) / 2
                kp = _flat_key_poly(cx, y1, hh, v)
                kb, kt = v['key_w'] / 2, kp[2][0] - cx
                xk = kb + (kt - kb) * hh / (hh + v['key_up'])
                out += [(cx + xk, top), kp[2], kp[3], (cx - xk, top)]
            out += [(xa, top), (xa, y1), (x0, y1)]
        else:
            out += [(x1, y1), (x0, y1)]
    if has_sill:
        out += [(x0, y0), (x0 - v['horn'], y0)]
    return clean(out) or list(P)


def make_command(mutate, meshes):
    """One undo step that adds the window groups and removes faces. Snapshots the
    meshes that change and the group list (like IngeTrazo's own Windowizer)."""
    try:
        from core.history import Command
    except Exception:
        Command = None
    if Command is None or not all(hasattr(m, 'capture_state') for m in meshes):
        return SnapshotImport(mutate)

    class WindowsCommand(Command):
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

    return WindowsCommand()


def to_world(frame):
    O, U, V, N = frame

    def f(p):
        return v_add(O, v_add(v_mul(U, p[0] * SCALE), v_add(v_mul(V, p[1] * SCALE), v_mul(N, p[2] * SCALE))))
    return f


def describe(sh, v):
    """A group name such as 'Round top sash window, 6 over 6 - 900 x 1500 mm'."""
    x0, x1, y0, y1 = sh['box']
    name = {'sash': "sash window", 'casement': "casement window", 'fixed': "fixed window"}[v['style']]
    if v['style'] == 'sash':
        panes = "%d over %d" % (v['cols'] * v['rows'], v['cols_b'] * v['rows_b'])
    elif v['style'] == 'casement':
        panes = "%d leaves" % v['leaves'] if v['leaves'] != 1 else "1 leaf"
    else:
        panes = "%d x %d" % (v['cols'], v['rows'])      # not 'panes': Layers & Colours would paint it as glass
    top = {'semi': "round top ", 'segment': "segmental ", 'gothic': "pointed ",
           'circle': "round "}.get(sh['kind'], "")
    text = top + name
    return "%s, %s - %d x %d mm" % (text[0].upper() + text[1:], panes, round(x1 - x0), round(y1 - y0))


# ---------------------------------------------------------------------------
# Presets (one .json file per preset)
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
                        data = json.load(f)
                    if isinstance(data, dict):
                        out[data.get('name') or fn[:-5]] = data
                except Exception:
                    pass
    except Exception:
        pass
    return out


def save_preset_file(name, values):
    os.makedirs(PRESET_DIR, exist_ok=True)
    data = {'name': name}
    data.update({k: values[k] for k in PRESET_KEYS if k in values})
    with open(os.path.join(PRESET_DIR, _safe_name(name) + ".json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def delete_preset_file(name):
    path = os.path.join(PRESET_DIR, _safe_name(name) + ".json")
    if os.path.exists(path):
        os.remove(path)


LAST_FILE = os.path.join(PRESET_DIR, "_last_used.cfg")     # the preset and settings you used last
ORDER_FILE = os.path.join(PRESET_DIR, "_order.json")    # the order you've arranged the presets in


def load_order():
    try:
        with open(ORDER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [str(n) for n in data] if isinstance(data, list) else []
    except Exception:
        return []


def QTimer_remember(dlg):
    """Remembers the settings just after a preset has been loaded into the boxes."""
    try:
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, dlg.remember)
    except Exception:
        dlg.remember()


def load_last():
    try:
        with open(LAST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_last(preset, values):
    try:
        os.makedirs(PRESET_DIR, exist_ok=True)
        with open(LAST_FILE, "w", encoding="utf-8") as f:
            json.dump({'preset': preset, 'values': {k: values[k] for k in PRESET_KEYS if k in values}},
                      f, indent=1)
    except Exception as e:
        print("%s: could not remember the last settings: %s" % (PLUGIN_NAME, e))


def save_order(names):
    try:
        os.makedirs(PRESET_DIR, exist_ok=True)
        with open(ORDER_FILE, "w", encoding="utf-8") as f:
            json.dump(list(names), f, indent=1)
    except Exception as e:
        print("%s: could not save the preset order: %s" % (PLUGIN_NAME, e))


# ---------------------------------------------------------------------------
# Live preview
# ---------------------------------------------------------------------------
VIEW_DIR = v_norm((-0.35, -0.25, -1.0))      # from the front, a little right and above
LIGHT = v_norm((0.4, 0.6, 0.8))
COLOURS = {'window': (242, 242, 236), 'glass': (160, 205, 235), 'stone': (205, 198, 182),
           'brick': (170, 82, 60), 'wall': (215, 185, 150)}


def preview_items(sh, v):
    """[(layer, depth, [(x, y)...], (r, g, b), alpha)]: layer 0 behind the wall face,
    1 the wall, 2 in front."""
    parts = build_window(sh, v)
    right = v_norm(v_cross(VIEW_DIR, (0.0, 1.0, 0.0)))
    up = v_cross(right, VIEW_DIR)

    def proj(p):
        return (v_dot(p, right), -v_dot(p, up))

    items = []
    for grp, sols in parts.items():
        if grp == 'info':
            continue
        if grp == 'glass':
            rgb, alpha = COLOURS['glass'], 110
        elif grp == 'window':
            rgb, alpha = COLOURS['window'], 255
        else:
            rgb, alpha = COLOURS.get(v['sill'] if grp == 'sill' else v['head'], COLOURS['stone']), 255
        for s in sols:
            if getattr(s, 'mortar', False):
                continue
            for f in s.faces:
                n = _newell(f)
                if v_dot(n, VIEW_DIR) >= 0:
                    continue
                k = 0.55 + 0.45 * max(0.0, v_dot(n, LIGHT))
                depth = sum(v_dot(p, VIEW_DIR) for p in f) / len(f)
                layer = 2 if max(p[2] for p in f) > 0.5 else 0
                items.append((layer, depth, [proj(p) for p in f],
                              tuple(int(c * k) for c in rgb), alpha))
    # the wall face, with the opening cut out of it
    x0, x1, y0, y1 = sh['box']
    m = 0.35 * max(x1 - x0, y1 - y0)
    wall = [proj((x, y, 0.0)) for x, y in ((x0 - m, y0 - m), (x1 + m, y0 - m),
                                           (x1 + m, y1 + m), (x0 - m, y1 + m))]
    hole = [proj((x, y, 0.0)) for x, y in sh['poly']]
    items.append((1, 0.0, (wall, hole), COLOURS['wall'], 255))
    items.sort(key=lambda it: (it[0], -it[1]))
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

EDDY_TIPS = {'Glass thickness': 'How thick the glass is. For printing use your nozzle width at your scale.',
 'Glazing bar width': 'How wide the glazing bars between the panes are.',
 'Glazing bar depth': 'How far the glazing bars stand out from the glass.',
 'Head sticks out': 'How far the stone head over the opening stands out from the wall.',
 'Keystone': 'Adds a keystone in the middle of the head.',
 'Keystone width': 'How wide the keystone is.',
 'Keystone rises above head': 'How far the keystone stands up above the top of the head.',
 'Keystone sticks out more': 'How much further the keystone stands out than the head.',
 'Mortar joint': 'The joint round the stone sill / step and head, where they meet the wall.',
 '3D view': "A 3D look at what you'll get.",
 'Key (A, B, C...)': 'A drawing showing what each lettered size (A, B, C ...) measures, with what each is set to now.',
 'Sizes': 'The lettered sizes, A, B, C ... (see the Sizes drawing).',
 'Preview selected face': "Shows the selected face's shape in the preview, without adding "
                          'anything.',
 'Bottom sash panes across': 'How many panes across the bottom sash.',
 'Bottom sash panes up': 'How many panes up the bottom sash.',
 'Mullion / transom width': 'How wide the upright mullions and level transoms are (casements).',
 'Sill': 'The sill under the window: stone, timber or none.',
 'Stone sill height': 'The height (thickness) of a stone sill.',
 'Frame depth': 'How far the frame reaches back into the wall.',
 'Sash / leaf thickness': 'How thick each sash or casement leaf is.',
 'Meeting rail': 'The depth of the rails where the two sashes meet in the middle.',
 'Add window to selected face(s)': 'Puts a window into each face you have selected.',
 'Window': "The window style, its top shape and how it's placed.",
 'Panes': 'How many panes, and the glazing bars.',
 'Sill & head': 'The sill under the window, and the head and keystone over it.'}
EDDY_TIPS_END = None


class WindowPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 340)
        self.items = []
        self.msg = ""

    def show_window(self, sh, v):
        try:
            self.items = preview_items(sh, v)
            self.msg = ""
        except Exception as e:
            self.items = []
            self.msg = str(e)
        self.update()

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen, QPainterPath
        from PySide6.QtCore import QPointF, Qt
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(248, 248, 246))
        if not self.items:
            p.drawText(self.rect().adjusted(10, 10, -10, -10), Qt.AlignCenter | Qt.TextWordWrap,
                       self.msg or "No preview")
            p.end()
            return
        pts_all = []
        for it in self.items:
            if it[0] == 1:
                pts_all.extend(it[2][0])
            else:
                pts_all.extend(it[2])
        xs = [q[0] for q in pts_all]
        ys = [q[1] for q in pts_all]
        w, h = self.width() - 16, self.height() - 16
        sc = min(w / ((max(xs) - min(xs)) or 1), h / ((max(ys) - min(ys)) or 1))
        ox = 8 + (w - (max(xs) - min(xs)) * sc) / 2 - min(xs) * sc
        oy = 8 + (h - (max(ys) - min(ys)) * sc) / 2 - min(ys) * sc

        def poly(pts):
            return QPolygonF([QPointF(ox + x * sc, oy + y * sc) for x, y in pts])

        for layer, _, pts, rgb, alpha in self.items:
            col = QColor(rgb[0], rgb[1], rgb[2], alpha)
            p.setBrush(col)
            p.setPen(QPen(col.darker(125), 0.6))
            if layer == 1:
                path = QPainterPath()
                path.addPolygon(poly(pts[0]))
                path.addPolygon(poly(pts[1]))
                path.setFillRule(Qt.OddEvenFill)
                p.drawPath(path)
            else:
                p.drawPolygon(poly(pts))
        p.end()


# ---------------------------------------------------------------------------
# Sizes drawing: front view and a cut through the middle, with the size letters
# ---------------------------------------------------------------------------
def _slice_x(solids, xc):
    """Line segments (z, y) where the plane x = xc cuts the solids."""
    segs = []
    for so in solids:
        for f in so.faces:
            pts = []
            n = len(f)
            for i in range(n):
                a, b = f[i], f[(i + 1) % n]
                da, db = a[0] - xc, b[0] - xc
                if (da < 0) != (db < 0):
                    t = da / (da - db)
                    pts.append((a[2] + t * (b[2] - a[2]), a[1] + t * (b[1] - a[1])))
            if len(pts) >= 2:
                if len(pts) > 2:
                    d0 = (pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
                    pts.sort(key=lambda q: q[0] * d0[0] + q[1] * d0[1])
                for i in range(0, len(pts) - 1, 2):
                    segs.append((pts[i], pts[i + 1]))
    return segs


def sizes_drawing(sh, v):
    """{'front': [(depth, pts, rgb)], 'cut': {group: segments}, 'dims': [...], 'xc': x}
    Dims are (letter, view, p1, p2, (ox, oy), offset px); view 'F' uses (x, y), 'C' (z, y)."""
    v = dict(v, open=False)
    parts = build_window(sh, v)
    info = parts['info']
    fd = info['fd']
    ox0, ox1, oy0, oy1 = info['O']
    x0, x1, y0, y1 = sh['box']
    H = y1 - y0
    st = v['style']
    cols = max(1, int(v['cols']))
    cx = (x0 + x1) / 2
    pane = (ox1 - ox0) / cols
    xc = cx + (pane / 2 if cols % 2 == 0 else 0.0)

    front = []
    cut = {}
    for grp in ('window', 'glass', 'sill', 'head'):
        sols = [s for s in parts[grp] if not getattr(s, 'mortar', False)]
        if grp == 'glass':
            rgb = COLOURS['glass']
        elif grp == 'window':
            rgb = COLOURS['window']
        else:
            rgb = COLOURS.get(v['sill'] if grp == 'sill' else v['head'], COLOURS['stone'])
        for so in sols:
            for f in so.faces:
                if _newell(f)[2] > 0.5:
                    front.append((sum(p[2] for p in f) / len(f), [(p[0], p[1]) for p in f], rgb))
        cut[grp] = _slice_x(sols, xc)
    front.sort(key=lambda it: it[0])

    D = []

    def dim(letter, view, p1, p2, o, off=0.0):
        D.append((letter, view, p1, p2, o, off))

    fw, sw, mw = v['frame_w'], v['sash_w'], v['meet_w']
    ytop = sh['ys'] if sh.get('ys') is not None else y1
    dim('A', 'F', (x0, y0 + 0.25 * H), (x0 + fw, y0 + 0.25 * H), (0, 1))
    dim('B', 'C', (0.0, y0 + fw * 0.5), (fd, y0 + fw * 0.5), (0, 1))
    if st != 'fixed':
        dim('C', 'F', (ox0, y0 + 0.7 * (ytop - y0)), (ox0 + sw, y0 + 0.7 * (ytop - y0)), (0, 1))
    if st == 'sash':
        ym = info['ym']
        br = v['bottom_rail']
        cb = max(1, int(v['cols_b']))
        xe = ox0 + (ox1 - ox0) * 0.5 / cb
        dim('E', 'F', (xe, oy0), (xe, oy0 + br), (1, 0))
        xf = ox1 - (ox1 - ox0) * 0.5 / cols
        dim('F', 'F', (xf, ym - mw / 2), (xf, ym + mw / 2), (1, 0))
        dim('D', 'C', (fd - 10 - v['sash_d'], ym + mw / 4), (fd - 10, ym + mw / 4), (0, 1), 14)
    elif st == 'casement':
        dim('D', 'C', (fd - v['sash_d'], oy0 + sw / 2), (fd, oy0 + sw / 2), (0, 1), 14)
        L = max(1, int(v['leaves']))
        if L > 1:
            xm = ox0 + (ox1 - ox0) / L
            jm = v['mullion_w']
            dim('J', 'F', (xm - jm / 2, y0 + 0.15 * H), (xm + jm / 2, y0 + 0.15 * H), (0, 1))
    # glazing bars
    bw = v['bar_w']
    if st == 'fixed':
        gx0, gx1 = ox0, ox1
    elif st == 'sash':
        gx0, gx1 = ox0 + sw, ox1 - sw
    else:
        L = max(1, int(v['leaves']))
        gx0 = ox0 + sw
        gx1 = (ox0 + (ox1 - ox0) / L - (v['mullion_w'] / 2 if L > 1 else 0.0)) - sw
    if cols > 1:
        xb = gx0 + (gx1 - gx0) / cols
        yb = y0 + 0.42 * H
        dim('G', 'F', (xb - bw / 2, yb), (xb + bw / 2, yb), (0, 1))
    # bar depth and glass in the cut: find a level bar the cut goes through
    bars_y = sorted(set(round(q[1], 3) for a, b in cut['window'] for q in (a, b)))
    if st == 'fixed':
        z1b = fd - 5.0 if fd > 10.0 else fd
        z0b = max(0.0, z1b - v['bar_d'])
    elif st == 'sash':
        zmid = fd - 15 - 1.5 * v['sash_d']
        bdep = min(v['bar_d'], v['sash_d'])
        z0b, z1b = zmid - bdep / 2, zmid + bdep / 2
    else:
        zmid = fd - v['sash_d'] / 2
        bdep = min(v['bar_d'], v['sash_d'])
        z0b, z1b = zmid - bdep / 2, zmid + bdep / 2
    if v.get('flat', True) and v.get('bars_back', True):
        z0b, z1b = 0.0, v['bar_d']          # bars lie at the back
    dim('H', 'C', (z0b, y0 + 0.33 * H), (z1b, y0 + 0.33 * H), (0, 1), 14)
    if v['glass']:
        t = v['glass_t']
        zg = (z0b + z1b) / 2
        dim('K', 'C', (zg - t / 2, y0 + 0.5 * H), (zg + t / 2, y0 + 0.5 * H), (0, 1), 14)
    if sh['kind'] == 'segment':
        dim('L', 'F', (x0, sh['ys']), (x0, y1), (-1, 0), 22)
    # sill
    if v['sill'] != 'none' and sh.get('flat_bottom'):
        h = v['sill_h'] if v['sill'] == 'stone' else v['brick_w']
        xa = x0 - v['horn']
        dim('M' if v['sill'] == 'stone' else 'W', 'F', (x1 + v['horn'], y0 - h), (x1 + v['horn'], y0),
            (1, 0), 18)
        dim('P', 'F', (x1, y0 - h), (x1 + v['horn'], y0 - h), (0, -1), 16)
        dim('N', 'C', (fd, y0 - h), (fd + v['sill_p'], y0 - h), (0, -1), 16)
        if v['sill'] == 'brick':
            J = v['joint']
            a, b = _soldiers(xa, x1 + v['horn'], v['brick_t'] + J, J)[0]
            dim('X', 'F', (a, y0 - h), (b, y0 - h), (0, -1), 16)
            dim('Y', 'F', (b, y0 - h), (b + J, y0 - h), (0, -1), 34)
    # head
    if v['head'] != 'none':
        hh = v['head_h']
        hp = v['head_p']
        key = v['keystone']
        if sh['arcs']:
            i0, o0 = _arch_pts(sh, 0.0, hh)
            dx, dy = o0[0] - i0[0], o0[1] - i0[1]
            L0 = math.hypot(dx, dy) or 1.0
            dim('Q', 'F', i0, o0, (dy / L0, -dx / L0), 16)
            mid = _arch_len(sh) / 2
            htop = max(_arch_pts(sh, mid, hh)[1][1], _arch_pts(sh, mid, hh)[0][1] + hh * 0.5)
            if v['head'] == 'brick':
                J = v['joint']
                a, b = _arch_ranges(sh, v['key_w'] / 2 if key else 0.0)[0]
                n = max(1, int(round((b - a) / (v['brick_t'] + J))))
                s1 = a + (b - a) / n - J / 2
                e0, e1 = _arch_pts(sh, a, hh)[1], _arch_pts(sh, s1, hh)[1]
                e2 = _arch_pts(sh, s1 + J, hh)[1]
                ex, ey = e1[0] - e0[0], e1[1] - e0[1]
                Le = math.hypot(ex, ey) or 1.0
                dim('X', 'F', e0, e1, (ey / Le, -ex / Le), 14)
                dim('Y', 'F', e1, e2, (ey / Le, -ex / Le), 30)
            if key:
                kp = _arch_key_poly(sh, v, hh)
                dim('T', 'F', kp[0], kp[8], (0, -1))
                ktop = max(q[1] for q in kp)
                rx = max(q[0] for q in kp)
                dim('U', 'F', (rx, ktop - v['key_up']), (rx, ktop), (1, 0), 12)
                dim('V', 'C', (fd + hp, ktop), (fd + hp + v['key_p'], ktop), (0, 1), 26)
                htop = ktop - v['key_up']
            dim('R', 'C', (fd, htop), (fd + hp, htop), (0, 1), 12)
        else:
            xa, xb = x0 - v['bearing'], x1 + v['bearing']
            dim('Q', 'F', (xb, y1), (xb, y1 + hh), (1, 0), 18)
            dim('S', 'F', (x1, y1 + hh), (xb, y1 + hh), (0, 1), 16)
            dim('R', 'C', (fd, y1 + hh), (fd + hp, y1 + hh), (0, 1), 12)
            if v['head'] == 'brick':
                J = v['joint']
                a, b = _soldiers(xa, (cx - v['key_w'] / 2 - J) if key else xb, v['brick_t'] + J, J)[0]
                dim('X', 'F', (a, y1 + hh), (b, y1 + hh), (0, 1), 16)
                dim('Y', 'F', (b, y1 + hh), (b + J, y1 + hh), (0, 1), 34)
            if key:
                kp = _flat_key_poly(cx, y1, hh, v)
                dim('T', 'F', kp[0], kp[1], (0, -1))
                dim('U', 'F', (kp[2][0], y1 + hh), kp[2], (1, 0), 12)
                dim('V', 'C', (fd + hp, kp[2][1]), (fd + hp + v['key_p'], kp[2][1]), (0, 1), 26)
    return {'front': front, 'cut': cut, 'dims': D, 'xc': xc, 'fd': fd}


class SizesDiagram(QWidget):
    """Front view and a cut through the window, with each size marked by its letter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 340)
        self.d = None
        self.msg = ""

    def show_window(self, sh, v):
        try:
            self.d = sizes_drawing(sh, v)
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
        cz = [q[0] for segs in d['cut'].values() for a, b in segs for q in (a, b)] + [0.0]
        cy = [q[1] for segs in d['cut'].values() for a, b in segs for q in (a, b)]
        if not fx:
            p.end()
            return
        M = 40.0                                  # room for the size marks
        W, Hh = self.width(), self.height()
        fw_mm, cw_mm = max(fx) - min(fx), max(cz) - min(cz) + 150.0
        ylo, yhi = min(fy + cy), max(fy + cy)
        sc = min((W - 3 * M - 20) / (fw_mm + cw_mm), (Hh - 2 * M - 16) / ((yhi - ylo) or 1))
        fx0 = M - min(fx) * sc
        cx0 = M + fw_mm * sc + M + 20 + 150.0 * sc - min(cz) * sc
        ybase = Hh - M - 16

        def F(q):
            return QPointF(fx0 + q[0] * sc, ybase - (q[1] - ylo) * sc)

        def C(q):
            return QPointF(cx0 + q[0] * sc, ybase - (q[1] - ylo) * sc)

        # front view
        for _, pts, rgb in d['front']:
            col = QColor(*rgb)
            p.setBrush(col)
            p.setPen(QPen(col.darker(140), 0.6))
            p.drawPolygon(QPolygonF([F(q) for q in pts]))
        # where the cut is taken
        pen = QPen(QColor(120, 120, 200), 1, Qt.DashLine)
        p.setPen(pen)
        p.drawLine(F((d['xc'], yhi)), F((d['xc'], ylo)))
        # cut view: wall face, then the cut outlines
        p.setPen(QPen(QColor(150, 150, 150), 1))
        p.setBrush(QColor(225, 220, 212))
        p.drawRect(QRectF(C((-150.0, yhi)), C((0.0, ylo))))
        cols = {'window': QColor(60, 60, 60), 'glass': QColor(70, 140, 200),
                'sill': QColor(120, 100, 80), 'head': QColor(150, 60, 40)}
        for grp, segs in d['cut'].items():
            p.setPen(QPen(cols[grp], 1.2))
            for a, b in segs:
                p.drawLine(C(a), C(b))
        f = QFont()
        f.setPointSize(7)
        p.setFont(f)
        p.setPen(QColor(90, 90, 90))
        p.drawText(QRectF(M, Hh - 18, W / 2, 16), Qt.AlignLeft, "Front")
        p.drawText(QRectF(cx0 - 150.0 * sc, Hh - 18, W / 2, 16), Qt.AlignLeft,
                   "Cut through (wall face on the left)")

        # size marks
        fb = QFont()
        fb.setPointSize(8)
        fb.setBold(True)
        p.setFont(fb)
        blue = QColor(20, 90, 200)
        for letter, view, p1, p2, o, off in d['dims']:
            T = F if view == 'F' else C
            a, b = T(p1), T(p2)
            ox, oy = o[0], -o[1]                  # screen y runs down
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
            tx, ty = (dx - dy) / Ld * 3, (dy + dx) / Ld * 3     # little slashes at the ends
            for q in (a2, b2):
                p.drawLine(QPointF(q.x() - tx, q.y() - ty), QPointF(q.x() + tx, q.y() + ty))
            mx = (a2.x() + b2.x()) / 2 + ox * 10
            my = (a2.y() + b2.y()) / 2 + oy * 10
            r = 7.0
            p.setBrush(QBrush(QColor(255, 255, 255)))
            p.drawEllipse(QPointF(mx, my), r, r)
            p.drawText(QRectF(mx - r, my - r, 2 * r, 2 * r), Qt.AlignCenter, letter)
        p.end()


# ---- what this plugin builds into the walls (used by the Whole building part below)
WB_KIND = 'window'
WB_WORDS = {'n': 'window', 'N': 'Window', 'ns': 'windows', 'o': 'door', 'os': 'doors',
            'other_plugin': '3D Period Doors', 'sill': 'sill'}


def fit_kind_shape(poly, v):
    return fit_shape(poly, v['top'], v['rise'])


def kind_parts(sh, vv):
    built = build_window(sh, vv)
    out = []
    for grp in ('window', 'sill', 'head'):
        for so in built[grp]:
            so.part = grp                  # which part it is, for colouring it when it's built into a wall
            out.append(so)
    return out


# ---------------------------------------------------------------------------
# Whole building: find every opening in the walls and build the windows / doors into
# their wall sections, so each wall prints flat as one piece with them.
# (This part is the same in 3D Period Windows and 3D Period Doors: they share what's kept on a wall.)
# ---------------------------------------------------------------------------
WB_DEFAULT_OVERLAP = 10.0      # mm: how far each window or door reaches into the wall round it, so they join


def _kids_of(g):
    out = []
    for attr in ('children', 'groups'):
        out += _items(getattr(g, attr, None))
    return out


def _as_matrix(m):
    """A group's placement as a QMatrix4x4 (or None for 'where it is')."""
    if m is None:
        return None
    if hasattr(m, 'map'):
        return m
    try:
        from PySide6.QtGui import QMatrix4x4
        vals = [float(x) for x in m]
        if len(vals) == 16:
            return QMatrix4x4(*vals).transposed()       # stored column by column
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


def _wvec(m, d):
    if m is None:
        return d
    try:
        q = m.mapVector(QVector3D(*d))
        return v_norm((q.x(), q.y(), q.z()))
    except Exception:
        a, b = _wmap(m, (0.0, 0.0, 0.0)), _wmap(m, d)
        return v_norm(v_sub(b, a))


def _in_tree(top, g):
    seen = []
    _walk_groups([top], seen)
    return any(x is g for x in seen)


def _tops_for(scene, picked):
    """The top-level groups holding what's picked (the whole building each one is part of)."""
    tops = _items(getattr(scene, 'groups', None))
    if not picked:
        return tops
    out = []
    for t in tops:
        if any(_in_tree(t, g) for g in picked) and all(t is not o for o in out):
            out.append(t)
    return out


def _picked_groups(scene):
    return [e for e in _items(getattr(scene, 'selection', None)) if hasattr(e, 'mesh')]


def _wall_meshes(scene):
    """[(group, mesh, world matrix)] for every group with faces in what's picked
    (or the whole model when nothing is picked), and the middle of the building(s)."""
    picked = _picked_groups(scene)
    tops = _tops_for(scene, picked)
    skip = _plugin_built(tops)
    every = []
    for t in tops:
        for g, m in _placements(t):
            if id(g) in skip:
                continue
            mesh = getattr(g, 'mesh', None)
            if mesh is not None and _items(getattr(mesh, 'faces', None)):
                every.append((g, mesh, m))
    if picked:
        want = []
        for p in picked:
            want += [g for g in ([p] + _walk_seen(p))]
        use = [x for x in every if any(x[0] is w for w in want)]
    else:
        use = every
    # the middle of the whole building(s), from every corner of every face
    pts = []
    for g, mesh, m in every:
        for f in _items(getattr(mesh, 'faces', None)):
            for v in _items(getattr(f, 'vertices', None)):
                p = _pos(v)
                if p is not None:
                    pts.append(_wmap(m, p))
    if pts:
        xs, ys, zs = [p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts]
        centre = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)
    else:
        centre = (0.0, 0.0, 0.0)
    return use, centre


# groups the plugins build (and everything inside them) aren't walls: the subframe and its glazing
# frames and trusses, windows, doors and so on - their holes aren't openings to fill
NOT_WALLS = ("subframe", "glazing", "truss", "window", "door", "gutter", "downpipe", "chimney",
             "canopy", "fence", "gate", "pipe", "barge", "finial", "fascia", "soffit")


def _plugin_built(tops):
    skip = set()

    def walk(g, inside, depth):
        nm = (getattr(g, 'name', '') or '').lower()
        inside = inside or any(w in nm for w in NOT_WALLS)
        if inside:
            skip.add(id(g))
        if depth < 30:
            for c in _kids_of(g):
                walk(c, inside, depth + 1)
    for t in tops:
        walk(t, False, 0)
    return skip


def _walk_seen(g):
    seen = []
    _walk_groups(_kids_of(g), seen)
    return seen


def _group_of_mesh(scene, mesh):
    gs = []
    _walk_groups(getattr(scene, 'groups', None), gs)
    for g in gs:
        if getattr(g, 'mesh', None) is mesh:
            return g
    return None


# what's kept on a wall group (saved with the model) once windows or doors are built into it: the plain
# wall as it was before (so it can be built again), and each window's / door's opening, settings and
# shape. Both plugins use the same record, so each one keeps the other's work when it builds a wall again.
REC_KEY = "ed3d_openings"
OLD_REC_KEYS = ("ed3d_period_windows",)


def wall_record(g):
    ext = getattr(g, 'ext', None)
    if not isinstance(ext, dict):
        return None
    rec = ext.get(REC_KEY)
    if isinstance(rec, dict) and rec.get('orig'):
        return rec
    for old in OLD_REC_KEYS:                      # kept by an earlier version (windows only)
        o = ext.get(old)
        if isinstance(o, dict) and o.get('orig'):
            return {'orig': o['orig'], 'items': [dict(w, kind='window') for w in o.get('windows', [])]}
    return None


def set_wall_record(g, rec):
    ext = getattr(g, 'ext', None)
    if not isinstance(ext, dict):
        if rec is None:
            return
        try:
            g.ext = {}
        except Exception:
            return
        ext = g.ext
    for old in OLD_REC_KEYS:
        ext.pop(old, None)
    if rec is None:
        ext.pop(REC_KEY, None)
    else:
        ext[REC_KEY] = rec


def solids_to_rec(solids):
    return [[[[round(c, 7) for c in p] for p in f] for f in so.faces] for so in solids]


def solids_from_rec(data):
    out = []
    for faces in data or []:
        so = Solid()
        so.faces = [[tuple(p) for p in f] for f in faces]
        out.append(so)
    return out


_KEEP_TAGS = ('part', 'kind', 'mortar')


def tagged_to_rec(solids):
    """Like solids_to_rec, but keeps what each solid is (its part - frame, sill, head... - and kind),
    so a window or door kept on a wall is still coloured part by part when the other plugin builds
    that wall again."""
    out = []
    for so in solids:
        tags = {}
        for a in _KEEP_TAGS:
            val = getattr(so, a, None)
            if isinstance(val, (str, bool, int, float)):
                tags[a] = val
        out.append({'f': [[[round(c, 7) for c in p] for p in f] for f in so.faces], 't': tags})
    return out


def tagged_from_rec(data):
    """Reads solids kept by tagged_to_rec - or by the older solids_to_rec (faces only, no tags)."""
    out = []
    for rec in data or []:
        faces, tags = (rec.get('f') or [], rec.get('t') or {}) if isinstance(rec, dict) else (rec, {})
        so = Solid()
        so.faces = [[tuple(p) for p in f] for f in faces]
        for k, val in tags.items():
            setattr(so, k, val)
        out.append(so)
    return out


def item_solids(item, own_kind):
    """The solids of a window or door kept on a wall: made again from its settings if it's this
    plugin's own kind, otherwise its shape as it was kept (or, failing that, made by the other plugin)."""
    if item.get('kind') == own_kind:
        vv = dict(DEFAULTS)
        vv.update(item.get('values') or {})
        sols, _t = build_into_wall(item, vv, item.get('overlap', WB_DEFAULT_OVERLAP))
        item['solids'] = tagged_to_rec(sols)
        return sols
    kept = tagged_from_rec(item['solids']) if item.get('solids') else None
    # kept with its parts named (frame, sill, head...): use it as it is
    if kept and all(getattr(so, 'part', None) for so in kept):
        return kept
    # kept by an older version (shape only, no part names), or not kept: made again by the other
    # plugin, so each part gets its own colour (an untagged one was all painted as the frame)
    import sys as _sys
    want = "ed3d_period_doors" if item.get('kind') == 'door' else "ed3d_period_windows"
    for nm, mod in list(_sys.modules.items()):
        if nm.endswith(want) and hasattr(mod, 'build_into_wall'):
            try:
                vv = dict(mod.DEFAULTS)
                vv.update(item.get('values') or {})
                sols, _t = mod.build_into_wall(item, vv, item.get('overlap', WB_DEFAULT_OVERLAP))
                got = tagged_from_rec(tagged_to_rec(sols))
                item['solids'] = tagged_to_rec(got)
                return got
            except Exception as e:
                if kept:
                    print("%s: %s kept as it was (%s)" % (PLUGIN_NAME, item.get('name', 'an opening'), e))
                    return kept
                raise
    if kept:
        return kept
    raise ValueError("it was made by %s, which isn't loaded" %
                     ("3D Period Doors" if item.get('kind') == 'door' else "3D Period Windows"))


class _PlainFace:
    """A face of the plain wall kept in a record (points only)."""
    def __init__(self, pts, holes):
        self.vertices = [tuple(p) for p in pts]
        self.holes = [[tuple(p) for p in h] for h in holes]


class _PlainMesh:
    def __init__(self, faces):
        self.faces = faces


def _numbered_faces(mesh):
    """(index, face) for the faces of a mesh, numbered the same way as _faces_of_mesh."""
    out = []
    i = 0
    for f in _items(getattr(mesh, 'faces', None)):
        pts = [p for p in (_pos(v) for v in _items(getattr(f, 'vertices', None))) if p is not None]
        if len(pts) < 3:
            continue
        out.append((i, f))
        i += 1
    return out


def _wall_faces(g, mesh):
    """(mesh to look in, [(index, face)], record): a wall with windows already built into it is
    looked at as it was before them (its openings are where they were), otherwise as it is."""
    rec = wall_record(g) if g is not None else None
    if rec:
        faces = [_PlainFace(pts, hls) for pts, hls in rec['orig']]
        return _PlainMesh(faces), list(enumerate(faces)), rec
    return mesh, _numbered_faces(mesh), None


def _group_of_mesh(scene, mesh):
    gs = []
    _walk_groups(getattr(scene, 'groups', None), gs)
    for g in gs:
        if getattr(g, 'mesh', None) is mesh:
            return g
    return None


def find_building_openings(scene, flip=False, door_tol=15.0):
    """Every opening in what's picked: [dict(group, mesh, face, fi, k, poly (mm, on the face), frame,
    depth (m), door, w, h, name, built)]. Picked faces (a wall face, even one inside a group): just
    their openings, the window going on that face. Otherwise every hole in the outside faces of the
    walls of the picked building (or groups). Doors are the openings that reach the bottom of their
    wall. 'built' is the window already built into an opening (its settings), or None."""
    found = []
    faces = selected_faces(scene)
    if faces:
        done = []
        for i, face in enumerate(faces):
            mesh = mesh_of_face(scene, face)
            if mesh is None:
                continue
            g = _group_of_mesh(scene, mesh)
            gname = getattr(g, 'name', None) or ("Face %d" % (i + 1))
            look, numbered, rec = _wall_faces(g, mesh)
            if rec:
                # windows are built into this wall already: show its openings as a whole
                if any(d is g for d in done):
                    continue
                done.append(g)
                count = [0]
                for fi, f in numbered:
                    if _is_wall_face(f, None):
                        _face_openings_into(found, g, mesh, look, f, fi, rec, gname, door_tol, count,
                                            only_built=True)
                continue
            fi = next((n for n, f in numbered if f is face), None)
            _face_openings_into(found, g, mesh, look, face, fi, None, gname, door_tol, [0])
        return found
    use, centre = _wall_meshes(scene)
    wall_no = 0
    for g, mesh, m in use:
        wall_no += 1
        gname = getattr(g, 'name', None) or ("Wall %d" % wall_no)
        count = [0]
        look, numbered, rec = _wall_faces(g, mesh)
        for fi, face in numbered:
            pts = [p for p in (_pos(v) for v in _items(face.vertices)) if p is not None]
            if len(pts) < 3:
                continue
            nw = _wvec(m, _newell(pts))
            if abs(nw[2]) > 0.5:
                continue                               # a roof or floor, not a wall
            c = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts),
                 sum(p[2] for p in pts) / len(pts))
            cw = _wmap(m, c)
            out = nw[0] * (cw[0] - centre[0]) + nw[1] * (cw[1] - centre[1])
            if (out <= 0) != bool(flip) and not (rec and _built_on(rec, fi)):
                continue                               # the inside face of the wall
            _face_openings_into(found, g, mesh, look, face, fi, rec, gname, door_tol, count)
    return _drop_doubles(found)


def _drop_doubles(found, tol=0.03):
    """The same opening can turn up twice in one wall (on two faces of it lying over each other, or
    the inside face as well as the outside one): same size, same place along the wall. Keeps one -
    the one with a window/door built in, otherwise the one with the back of the wall found - and
    numbers the openings of that wall again."""
    def middle(op):
        x0, x1, y0, y1 = bbox(op['poly'])
        return to_world(op['frame'])(((x0 + x1) / 2, (y0 + y1) / 2, 0.0))

    def score(op):
        return (1 if op.get('built') else 0, 1 if op.get('depth') is not None else 0)

    keep, redo = [], set()
    for op in found:
        c = middle(op)
        twin = None
        for i, o in enumerate(keep):
            if o['group'] is not op['group'] or abs(o['w'] - op['w']) > 2.0 or abs(o['h'] - op['h']) > 2.0:
                continue
            _O, U, V, N = o['frame']
            if abs(v_dot(N, op['frame'][3])) < 0.99:
                continue
            d = v_sub(c, middle(o))
            if abs(v_dot(d, U)) < tol and abs(v_dot(d, V)) < tol and abs(v_dot(d, N)) < WALL_MAX:
                twin = i
                break
        if twin is None:
            keep.append(op)
            continue
        redo.add(id(op['group']))
        if score(op) > score(keep[twin]):
            keep[twin] = op
    for gid in redo:
        n = 0
        for op in keep:
            if id(op['group']) == gid:
                n += 1
                op['name'] = re.sub(r'(Door|Window) \d+$', lambda m: "%s %d" % (m.group(1), n), op['name'])
    return keep


def _built_on(rec, fi):
    return any(w.get('fi') == fi for w in (rec or {}).get('items', []))


def _is_wall_face(face, m):
    pts = [p for p in (_pos(v) for v in _items(face.vertices)) if p is not None]
    return len(pts) >= 3 and abs(_wvec(m, _newell(pts))[2]) <= 0.5


NOTCH_K = 1000          # openings cut up from the bottom edge of a wall (doorways) count from here
DOOR_UP_MAX = 600.0     # mm: a tall opening starting no higher than this up the wall is a door (one with
                        # a step up, or a wall face that runs on down past the floor) - not a window


def _is_door(up, h, tol):
    """Is an opening a door? up = how far its bottom is above the bottom of the wall face, h its height
    (mm). Right at the bottom, or a little way up (less than a quarter of its own height, and no more
    than DOOR_UP_MAX) - a window's sill is always well up compared with how tall the window is."""
    return up <= tol or (up <= DOOR_UP_MAX and up < h * 0.25)


def _bottom_notches(poly, tol):
    """Doorways in a wall face's own outline: gaps in its bottom edge, where the outline goes up,
    across and back down. [(outline of the opening, [indices of its corners in poly])]."""
    n = len(poly)
    if n < 6:
        return []
    ybot = min(p[1] for p in poly)
    on = [abs(p[1] - ybot) < tol for p in poly]
    spans = []
    for i in range(n):
        j = (i + 1) % n
        if on[i] and on[j]:
            spans.append((min(poly[i][0], poly[j][0]), max(poly[i][0], poly[j][0])))
    if len(spans) < 2:
        return []
    spans.sort()
    merged = [list(spans[0])]
    for a, b in spans[1:]:
        if a <= merged[-1][1] + tol:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    out = []
    for (_a0, xa), (xb, _b1) in zip(merged, merged[1:]):
        if xb - xa < tol:
            continue
        ia = next((i for i in range(n) if on[i] and abs(poly[i][0] - xa) < tol), None)
        ib = next((i for i in range(n) if on[i] and abs(poly[i][0] - xb) < tol), None)
        if ia is None or ib is None:
            continue
        best = None
        for step in (1, -1):
            path, i = [ia], ia
            while i != ib and len(path) <= n:
                i = (i + step) % n
                path.append(i)
            inner = path[1:-1]
            if inner and all(xa - tol <= poly[q][0] <= xb + tol and poly[q][1] > ybot + tol * 0.5
                             for q in inner):
                if best is None or len(path) < len(best):
                    best = path
        if best is None:
            continue
        pts = [poly[q] for q in best]
        if area2(pts) < 0:
            pts = list(reversed(pts))
        q = clean(pts)
        if q:
            out.append((q, best))
    return out


def _face_openings_into(found, g, mesh, look, face, fi, rec, gname, door_tol, count, only_built=False):
    """Adds the openings (holes) of one face to `found`, the window to go on that face.
    `look` is the mesh the face is in (the plain wall, for a wall with windows built in)."""
    holes = _items(getattr(face, 'holes', None))
    pts = [p for p in (_pos(v) for v in _items(face.vertices)) if p is not None]
    if len(pts) < 3:
        return
    built_here = {w.get('k'): w for w in (rec or {}).get('items', []) if w.get('fi') == fi}
    if only_built and not built_here:
        return
    try:
        frame, _polys = face_openings(face, False)
    except ValueError:
        return
    O, U, V, N = frame
    ybot = min(v_dot(v_sub(p, O), V) / SCALE for p in pts)
    tw0 = to_world(frame)
    face_area = abs(area2([(v_dot(v_sub(p, O), U) / SCALE, v_dot(v_sub(p, O), V) / SCALE) for p in pts]))
    for k, h in enumerate(holes):
        hp = [p for p in (_pos(v) for v in _items(h)) if p is not None]
        if len(hp) < 3:
            continue
        poly = clean([(v_dot(v_sub(p, O), U) / SCALE, v_dot(v_sub(p, O), V) / SCALE) for p in hp])
        if not poly:
            continue
        if area2(poly) < 0:
            poly = list(reversed(poly))
        if face_area > 0 and area2(poly) > face_area * 0.88 and k not in built_here:
            continue                                   # the inside of a frame or trim, not an opening
        x0, x1, y0, y1 = bbox(poly)
        try:
            back = _back_depth(look, [tw0((x, y, 0.0)) for x, y in poly], N, face)
        except Exception:
            back = None
        count[0] += 1
        door = _is_door(y0 - ybot, y1 - y0, door_tol)
        found.append(dict(group=g, mesh=mesh, face=face if rec is None else None, fi=fi, k=k,
                          poly=poly, frame=frame, depth=back[1] if back else None, door=door,
                          w=x1 - x0, h=y1 - y0, built=built_here.get(k),
                          name="%s - %s %d" % (gname, "Door" if door else "Window", count[0])))
    # doorways: cut up from the bottom edge of the wall, so they're part of its outline, not holes
    outline = [(v_dot(v_sub(p, O), U) / SCALE, v_dot(v_sub(p, O), V) / SCALE) for p in pts]
    for j, (poly, path) in enumerate(_bottom_notches(outline, max(1.0, door_tol * 0.2))):
        k = NOTCH_K + j
        x0, x1, y0, y1 = bbox(poly)
        try:
            back = _back_depth(look, [tw0((x, y, 0.0)) for x, y in poly], N, face)
        except Exception:
            back = None
        count[0] += 1
        found.append(dict(group=g, mesh=mesh, face=face if rec is None else None, fi=fi, k=k,
                          path=path, poly=poly, frame=frame, depth=back[1] if back else None,
                          door=True, w=x1 - x0, h=y1 - y0, built=built_here.get(k),
                          name="%s - Door %d" % (gname, count[0])))


def _back_depth(mesh, pts, n, exclude):
    """(face, depth): the back of the wall behind an opening - the nearest face facing the other
    way whose outline goes round the middle of the opening (it has the same opening in it)."""
    c = v_mul(tuple(sum(p[i] for p in pts) for i in range(3)), 1.0 / len(pts))
    U = v_norm(v_sub(pts[1], pts[0]))
    V = v_cross(n, U)
    best = None
    for f in _items(getattr(mesh, 'faces', None)):
        if f is exclude:
            continue
        fp = [p for p in (_pos(v) for v in _items(getattr(f, 'vertices', None))) if p is not None]
        if len(fp) < 3 or v_dot(_newell(fp), n) > -0.999:
            continue
        depth = v_dot(v_sub(c, fp[0]), n)
        if depth <= 1e-7 or depth > WALL_MAX or (best is not None and depth >= best[1]):
            continue
        q = v_sub(c, v_mul(n, depth))
        if not _pip3(q, fp, U, V):
            # a doorway's middle is in a gap in the outline: inside the face's extent will do
            us = [v_dot(p, U) for p in fp]
            vs = [v_dot(p, V) for p in fp]
            if not (min(us) - 1e-6 <= v_dot(q, U) <= max(us) + 1e-6
                    and min(vs) - 1e-6 <= v_dot(q, V) <= max(vs) + 1e-6):
                continue
        best = (f, depth)
    return best


def _world_matrix(scene, g):
    for t in _items(getattr(scene, 'groups', None)):
        for gg, m in _placements(t):
            if gg is g:
                return m
    return None


def _cam_eye(cam):
    for name in ('eye', 'position', 'eye_position', 'eye_pos'):
        a = getattr(cam, name, None)
        if a is None:
            continue
        try:
            a = a() if callable(a) else a
        except Exception:
            continue
        p = _pos(a)
        if p is not None:
            return p
    return None


def zoom_to_opening(viewport, op):
    """Turns the view to look at an opening from outside and comes in towards it - not all the way:
    the window fills about a quarter of the view, with the wall round it."""
    cam = getattr(viewport, 'camera', None)
    scene = getattr(viewport, 'scene', None)
    if cam is None or scene is None:
        return
    O, U, V, N = op['frame']
    x0, x1, y0, y1 = bbox(op['poly'])
    tw = to_world(op['frame'])
    m = _world_matrix(scene, op['group'])
    c = _wmap(m, tw(((x0 + x1) / 2, (y0 + y1) / 2, 0.0)))
    nw = _wvec(m, tuple(N))
    size = math.hypot(x1 - x0, y1 - y0) * SCALE
    t = getattr(cam, 'target', None)
    if t is not None and hasattr(t, 'setX'):
        cam.target = QVector3D(*c)
    elif isinstance(t, list):
        cam.target = list(c)
    else:
        try:
            cam.target = QVector3D(*c)
        except Exception:
            cam.target = tuple(c)
    if hasattr(cam, 'distance'):
        cam.distance = max(4.0 * size, 2.0)
    # face it from outside, if the camera says where it is
    yaw0 = getattr(cam, 'yaw', None)
    if isinstance(yaw0, (int, float)) and _cam_eye(cam) is not None:
        best = (None, yaw0)
        for step in range(36):
            cam.yaw = yaw0 + step * 10.0
            e = _cam_eye(cam)
            if e is None:
                break
            d = v_norm(v_sub(e, c))
            score = d[0] * nw[0] + d[1] * nw[1]
            if best[0] is None or score > best[0]:
                best = (score, cam.yaw)
        cam.yaw = best[1]
    for nm in ('notify_scene_changed', 'update'):
        f = getattr(viewport, nm, None)
        if callable(f):
            try:
                f()
            except Exception:
                pass


def opening_edges(op):
    """The edges round an opening, to light it up."""
    mesh, face, k = op['mesh'], op['face'], op['k']
    if face is None:
        return []                       # a wall with windows built in: its openings are filled
    if op.get('path') is not None:
        vs = _items(getattr(face, 'loop', None)) or _items(getattr(face, 'vertices', None))
        lp = [vs[i] for i in op['path'] if i < len(vs)]
        out = []
        for i in range(len(lp) - 1):
            try:
                e = mesh.find_edge(lp[i], lp[i + 1])
                if e is not None:
                    out.append(e)
            except Exception:
                pass
        return out
    loops = _items(getattr(face, 'hole_loops', None))
    if k >= len(loops):
        return []
    lp = _items(loops[k])
    out = []
    for i in range(len(lp)):
        try:
            e = mesh.find_edge(lp[i], lp[(i + 1) % len(lp)])
            if e is not None:
                out.append(e)
        except Exception:
            pass
    return out


def build_into_wall(op, v, overlap):
    """The window or door for one opening, as solids in the wall's own (local) metres, made a little
    bigger all round and sunk into the wall so it joins on. Flat at the back of the wall."""
    if op['depth'] is None:
        raise ValueError("no back of the wall found behind it (a wall needs a thickness)")
    depth_mm = op['depth'] / SCALE
    ov = max(0.0, min(overlap, 0.4 * depth_mm, 0.25 * v['frame_w']))
    poly = [tuple(p) for p in op['poly']]
    grown = clean(offset_poly(poly, -ov)) if ov > 0 else poly
    grown = grown or poly
    vv = dict(v)
    vv['flat'] = True                      # the back = the back of the wall
    vv['_base'] = -depth_mm
    vv['_base_sh'] = -min(max(ov, 1.0), 0.5 * depth_mm)   # sill / step and head sunk into the wall face
    sh = fit_kind_shape(grown, v)
    sols = kind_parts(sh, vv)
    tw = to_world(op['frame'])
    return [so.mapped(tw) for so in sols], describe(sh, v)


def _mesh_from(faces_lists):
    """A new mesh from [(outer points, [hole points])] in metres."""
    from core.mesh import Mesh
    mesh = Mesh()
    tol = 1e-4 * 0.001
    verts = {}
    bad = [0]

    def vx(p):
        key = (round(p[0] / tol), round(p[1] / tol), round(p[2] / tol))
        if key not in verts:
            verts[key] = VertexWrapper(*p)
        return verts[key]

    for pts, hls in faces_lists:
        try:
            outer = [vx(p) for p in pts]
            hs = [[vx(p) for p in h] for h in hls if len(h) >= 3]
            if hs:
                try:
                    mesh.add_face(outer, hs)
                except TypeError:
                    f_ = mesh.add_face(outer)
                    for h in hs:
                        mesh.add_hole(f_, h)
            else:
                mesh.add_face(outer)
        except Exception:
            bad[0] += 1
    return mesh, bad[0]


def _faces_of_mesh(mesh):
    out = []
    for f in _items(getattr(mesh, 'faces', None)):
        pts = [p for p in (_pos(v) for v in _items(getattr(f, 'vertices', None))) if p is not None]
        if len(pts) < 3:
            continue
        hls = []
        for h in _items(getattr(f, 'holes', None)):
            hp = [p for p in (_pos(v) for v in _items(h)) if p is not None]
            if len(hp) >= 3:
                hls.append(hp)
        out.append((pts, hls))
    return out


def _faces_of_solids(solids):
    return [(list(pts), []) for so in solids for pts in so.faces]


def join_into_wall(mesh, solids):
    """(new mesh for the wall, joined?) - the wall and its windows as one solid with IngeTrazo's
    Solid Tools Union; if that can't be done, the windows simply go into the wall's piece."""
    try:
        from core import solids as solid_tools
        from core.group import Group
        pieces = []
        g = Group("wall")
        g.mesh, _ = _mesh_from(_faces_of_mesh(mesh))
        pieces.append(g)
        for so in solids:
            gw = Group("window part")
            gw.mesh, _ = _mesh_from(_faces_of_solids([so]))
            pieces.append(gw)
        _removed, created = solid_tools.run(solid_tools.UNION, pieces)
        created = [c for c in (created or []) if c is not None and getattr(c, 'mesh', None) is not None]
        if len(created) == 1 and _items(getattr(created[0].mesh, 'faces', None)):
            # the Union cuts every flat face into triangles: join them back into whole faces
            try:
                tidy, bad = _mesh_from(_merge_flat_faces(_faces_of_mesh(created[0].mesh)))
                if not bad and _items(getattr(tidy, 'faces', None)):
                    return tidy, True, None
            except Exception as e:
                print("%s: couldn't tidy the wall's faces (%s)" % (PLUGIN_NAME, e))
            return created[0].mesh, True, None
        why = "the join came out as %d pieces" % len(created)
    except Exception as e:
        why = str(e) or e.__class__.__name__
    new, _bad = _mesh_from(_faces_of_mesh(mesh) + _faces_of_solids(solids))
    return new, False, why


def _merge_flat_faces(faces, ptol=1e-5, ktol=1e-6):
    """The Union (joining windows or doors into a wall) hands back each flat face cut into a fan of
    triangles - the lines across the wall. This joins the faces that lie flat in the same plane and
    touch back into one face each (with the openings as holes), so the wall reads cleanly.
    faces = [(outer points, [hole points])] in metres. Any plane that doesn't come out right is
    left as it was, so nothing can be lost."""
    def key(p):
        return (round(p[0] / ktol), round(p[1] / ktol), round(p[2] / ktol))

    def raw_area(pts, n):
        s = (0.0, 0.0, 0.0)
        for i in range(len(pts)):
            s = v_add(s, v_cross(pts[i], pts[(i + 1) % len(pts)]))
        return 0.5 * v_dot(s, n)

    planes = []                                  # [normal, point on it, [face indices]]
    norms = []
    for i, (pts, _h) in enumerate(faces):
        n = _newell(pts) if len(pts) >= 3 else (0.0, 0.0, 0.0)
        norms.append(n)
        if v_len(n) < 0.5:
            planes.append([n, None, [i]])
            continue
        for pl in planes:
            if pl[1] is not None and v_dot(pl[0], n) > 1.0 - 1e-7 and abs(v_dot(v_sub(pts[0], pl[1]), pl[0])) < ptol:
                pl[2].append(i)
                break
        else:
            planes.append([n, pts[0], [i]])
    out = []
    for n, p0, idx in planes:
        if p0 is None or len(idx) < 2:
            out += [faces[i] for i in idx]
            continue
        try:
            got = _merge_plane([faces[i] for i in idx], n, key, raw_area)
        except Exception:
            got = None
        out += got if got else [faces[i] for i in idx]
    return out


def _merge_plane(group, n, key, raw_area):
    """One plane's faces joined: [(outer, [holes])], or None if it can't be done cleanly."""
    pos = {}
    edges = {}
    want = 0.0
    for pts, hls in group:
        loops = [list(pts) if raw_area(pts, n) > 0 else list(reversed(pts))]
        want += abs(raw_area(pts, n))
        for h in hls:
            if len(h) >= 3:
                loops.append(list(h) if raw_area(h, n) < 0 else list(reversed(h)))
                want -= abs(raw_area(h, n))
        for lp in loops:
            ks = [key(p) for p in lp]
            for p, k in zip(lp, ks):
                pos.setdefault(k, p)
            for i in range(len(ks)):
                a, b = ks[i], ks[(i + 1) % len(ks)]
                if a == b:
                    continue
                if edges.get((b, a), 0) > 0:          # the same edge the other way: inside, so it goes
                    edges[(b, a)] -= 1
                    if not edges[(b, a)]:
                        del edges[(b, a)]
                else:
                    edges[(a, b)] = edges.get((a, b), 0) + 1
    nxt = {}
    for (a, b), c in edges.items():
        nxt.setdefault(a, []).extend([b] * c)
    loops = []
    guard = 0
    while nxt:
        a0 = next(iter(nxt))
        lp = [a0]
        cur = a0
        while True:
            guard += 1
            if guard > 200000:
                return None
            outs = nxt.get(cur)
            if not outs:
                return None                          # doesn't close up: leave this plane alone
            b = outs.pop()
            if not outs:
                del nxt[cur]
            if b == a0:
                break
            lp.append(b)
            cur = b
        if len(lp) >= 3:
            loops.append([pos[k] for k in lp])
    outers = [lp for lp in loops if raw_area(lp, n) > 0]
    holes = [lp for lp in loops if raw_area(lp, n) <= 0]
    got = sum(raw_area(lp, n) for lp in loops)
    if not outers or abs(got - want) > 1e-6 * max(1.0, abs(want)) + 1e-9:
        return None
    U = v_norm(v_sub(outers[0][1], outers[0][0]))
    V = v_cross(n, U)

    def flat(lp):
        return [(v_dot(p, U), v_dot(p, V)) for p in lp]

    def inside(q, poly):
        x, y = q
        c = False
        j = len(poly) - 1
        for i in range(len(poly)):
            (xi, yi), (xj, yj) = poly[i], poly[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                c = not c
            j = i
        return c
    res = [(o, []) for o in outers]
    fl = [flat(o) for o in outers]
    for h in holes:
        hf = flat(h)
        q = ((hf[0][0] + hf[1][0]) * 0.5, (hf[0][1] + hf[1][1]) * 0.5)
        home = [i for i in range(len(outers)) if inside(q, fl[i])]
        if not home:
            return None
        # the smallest outline round it
        i = min(home, key=lambda i: abs(raw_area(outers[i], n)))
        res[i][1].append(h)
    return res


def _fill_opening(rec, op):
    """Fills a window opening (a hole) back in, in the plain wall kept on the record: the hole goes
    from the front and back faces and its reveals go. Faces and holes are emptied, not removed, so
    the other windows' and doors' numbers stay right. False for a doorway cut up from the bottom."""
    fi, k = op['fi'], op['k']
    orig = rec['orig']
    if k >= NOTCH_K or fi is None or fi >= len(orig) or k >= len(orig[fi][1]):
        return False
    O, U, V, N = op['frame']
    O, U, V, N = tuple(O), tuple(U), tuple(V), tuple(N)

    def mm(p):
        d = v_sub(tuple(p), O)
        return (v_dot(d, U) / SCALE, v_dot(d, V) / SCALE, v_dot(d, N) / SCALE)
    x0, x1, y0, y1 = bbox(op['poly'])
    d_mm = (op['depth'] or 0.0) / SCALE
    tol = 1.0
    orig[fi][1][k] = []
    for j, (pts, hls) in enumerate(orig):
        if j == fi or len(pts) < 3:
            continue
        # the same hole in the back face
        for hi, h in enumerate(hls):
            if len(h) < 3:
                continue
            q = [mm(p) for p in h]
            hb = bbox([(a, b) for a, b, _c in q])
            if all(abs(c + d_mm) < tol for _a, _b, c in q) and all(
                    abs(a_ - b_) < tol for a_, b_ in zip(hb, (x0, x1, y0, y1))):
                hls[hi] = []
        # its reveals: faces across the wall, wholly inside the opening's outline
        q = [mm(p) for p in pts]
        if hls and any(len(h) >= 3 for h in hls):
            continue
        n = _newell([tuple(p) for p in pts])
        if abs(v_dot(n, N)) > 0.1:
            continue
        zs = [c for _a, _b, c in q]
        if (all(x0 - tol <= a <= x1 + tol and y0 - tol <= b <= y1 + tol for a, b, _c in q)
                and min(zs) > -d_mm - tol and max(zs) < tol and max(zs) - min(zs) > 0.5 * d_mm):
            orig[j] = [[], []]
    return True


def wall_swap_command(swaps):
    """One undo step that gives each wall group its new mesh (with its windows), and the record
    of its windows: swaps = [(group, old mesh, new mesh, old record, new record)]."""
    try:
        from core.history import Command
    except Exception:
        Command = object

    class WallWindowsCommand(Command):
        def _set(self, scene, which):
            for g, old, new, old_rec, new_rec in swaps:
                g.mesh = new if which else old
                set_wall_record(g, json.loads(json.dumps(new_rec if which else old_rec))
                                if (new_rec if which else old_rec) else None)
            try:
                scene.selection.clear()
            except Exception:
                pass
            try:
                scene.version += 1
            except Exception:
                pass

        def do(self, scene):
            self._set(scene, True)

        def undo(self, scene):
            self._set(scene, False)

    return WallWindowsCommand()



# ---------------------------------------------------------------------------
# Colours for windows and doors built into their walls (just for looks: they don't change the print).
# Each face of the new wall is painted by the part it lies on - with 3D Layers & Colours' colours when
# that plugin is loaded, otherwise plain ones - and the wall's own faces keep the colour they had.
# (The same in 3D Period Windows and 3D Period Doors.)
# ---------------------------------------------------------------------------
PAINT_RGB = (("mortar", (200, 194, 178)), ("knob", (40, 40, 44)), ("hinge", (40, 40, 44)),
             ("rail", (40, 40, 44)), ("hanger", (40, 40, 44)), ("brick", (170, 82, 60)),
             ("stone", (205, 198, 182)), ("door", (52, 96, 72)), ("window", (242, 242, 236)))


def paint_name(so, kind, vals):
    """What a part of a built-in window or door is called, for picking its colour."""
    if getattr(so, 'mortar', False):
        return "mortar"
    grp = getattr(so, 'part', None)
    if grp == 'glass':
        return "glass"
    if grp in ('step', 'sill', 'head'):
        m = vals.get(grp, 'stone')
        return m if m in ('stone', 'brick') else 'stone'
    k = getattr(so, 'kind', '') or ''
    return ("%s %s" % (kind, k)).strip() if k != 'part' else kind


def tag_parts(built, kind, vals):
    """Marks each solid of a built window / door with its part and colour name, so its faces can be
    coloured part by part even when the whole thing is joined into one solid."""
    for grp, sols in built.items():
        if grp == 'info' or not isinstance(sols, list):
            continue
        for so in sols:
            so.part = grp
            so.paint = paint_name(so, kind, vals)
            so.paint_kind = kind


def _plain_rgb(name):
    low = name.lower()
    for word, rgb in PAINT_RGB:
        if word in low:
            return rgb
    return (200, 200, 200)


def _face_axes(pts, n):
    for i in range(len(pts)):
        e = v_sub(pts[(i + 1) % len(pts)], pts[i])
        if v_dot(e, e) > 1e-14:
            U = v_norm(e)
            return U, v_cross(n, U)
    return None, None


def _face_samples(pts, hls, n, U, V, most=24):
    """Points just inside a face (off the middle of its edges), not in its holes."""
    out = []
    step = max(1, len(pts) // most)
    for i in range(0, len(pts), step):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        e = v_sub(b, a)
        if v_dot(e, e) < 1e-14:
            continue
        q = v_add(v_mul(v_add(a, b), 0.5), v_mul(v_norm(v_cross(n, e)), 1e-4))
        if _pip3(q, pts, U, V) and not any(_pip3(q, h, U, V) for h in hls):
            out.append(q)
    return out


def paint_wall(scene, new_mesh, old_mesh, sols):
    """Colours the faces of a wall with its windows / doors built in. Returns the faces painted."""
    import sys as _sys
    lc = None
    for nm, mod in list(_sys.modules.items()):
        if nm.endswith("ed3d_layers_colours") and hasattr(mod, '_pick_row'):
            lc = mod
            break
    palette = None
    if lc is not None:
        try:
            palette = lc.load_settings()['palette']
        except Exception:
            lc = None
    cache = {}

    def attrs_for(name, kind):
        if (name, kind) in cache:
            return cache[(name, kind)]
        a = None
        if lc is not None:
            try:
                row = lc._pick_row(palette, [name], "3D Period Doors" if kind == 'door' else "3D Period Windows")
                if row is not None:
                    # a colour changed in 3D Layers & Colours' own table is used even when the model
                    # already has that material (otherwise the model's material, which may be yours, stays)
                    std = next((r for r in getattr(lc, 'DEFAULT_PALETTE', []) if r[0] == row[0]), None)
                    changed = std is not None and (tuple(row[1]) != tuple(std[1]) or
                                                   abs(float(row[2]) - float(std[2])) > 1e-6)
                    a = lc._paint_attrs(scene, row, changed)
            except Exception as e:
                print("%s: colour %r: %s" % (PLUGIN_NAME, name, e))
        if a is None:
            a = {"color": tuple(c / 255.0 for c in _plain_rgb(name))}
        cache[(name, kind)] = a
        return a

    def pts_of(f):
        pts = [p for p in (_pos(v) for v in _items(getattr(f, 'vertices', None))) if p is not None]
        hls = []
        for h in _items(getattr(f, 'holes', None)):
            hp = [p for p in (_pos(v) for v in _items(h)) if p is not None]
            if len(hp) >= 3:
                hls.append(hp)
        return pts, hls

    planes = []
    for so in sols:
        name = getattr(so, 'paint', None)
        if not name:
            continue
        for f in so.faces:
            if len(f) >= 3:
                n = _newell(f)
                planes.append((n, v_dot(n, f[0]), f, name, getattr(so, 'paint_kind', 'window')))
    olds = []
    for f in _items(getattr(old_mesh, 'faces', None)):
        a = getattr(f, 'attrs', None)
        if not a:
            continue
        pts, hls = pts_of(f)
        if len(pts) >= 3:
            n = _newell(pts)
            olds.append((n, v_dot(n, pts[0]), pts, hls, dict(a)))
    if not planes and not olds:
        return 0
    TOL = 2e-5
    count = 0
    for f in _items(getattr(new_mesh, 'faces', None)):
        pts, hls = pts_of(f)
        if len(pts) < 3:
            continue
        n = _newell(pts)
        d = v_dot(n, pts[0])
        U, V = _face_axes(pts, n)
        if U is None:
            continue
        qs = _face_samples(pts, hls, n, U, V)
        if not qs:
            continue
        cand = [p for p in planes if v_dot(p[0], n) > 0.999 and abs(p[1] - d) < TOL]
        votes = {}
        for q in qs:
            hit = next(((nm, kd) for _n, _d, pf, nm, kd in cand if _pip3(q, pf, U, V)), None)
            votes[hit] = votes.get(hit, 0) + 1
        best = max(votes.items(), key=lambda kv: kv[1])[0]
        a = None
        if best is not None:
            a = attrs_for(*best)
        else:
            for on, od, opts, ohs, oa in olds:
                if v_dot(on, n) > 0.999 and abs(od - d) < TOL and any(
                        _pip3(q, opts, U, V) and not any(_pip3(q, h, U, V) for h in ohs) for q in qs[:6]):
                    a = oa
                    break
        if a is None:
            continue
        try:
            f.attrs = dict(a)
            count += 1
        except Exception:
            pass
    return count


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------
CHOICES = {'style': STYLES, 'top': TOPS, 'arch_bars': ARCH_BARS, 'sill': SILLS, 'sill_shape': SILL_SHAPES,
           'head': HEADS}

# key: (label, low, high, decimals, suffix, tip)
FIELDS = {
    'style': ("Window style", "Sash: two sliding sashes. Casement: hinged leaves with mullions. "
                              "Fixed / industrial: one grid of glazing bars."),
    'top': ("Top shape", "Follow the face shape uses the outline of the face you picked (round, "
                         "segmental, pointed and round tops are recognised). The others make that "
                         "shape inside the face's width and height."),
    'rise': ("Arch rise", 0.0, 5000.0, 0, " mm", "How high a segmental arch rises above its springing."),
    'flat': ("Flat back for 3D printing", "Every part of the window (frame, sashes, bars, glass, sill "
                                          "and head) goes right down to the face, so it prints flat "
                                          "with the wall. Casements and pivot lights can't be shown "
                                          "open like this; sliding sashes can."),
    'remove_face': ("Remove the face", "Takes away the face the window is placed on, so the window "
                                       "replaces it. (A face with openings in it is kept: the windows "
                                       "go into the openings.)"),
    'bars_back': ("Glazing bars at the back (on the print bed)",
                  "The glazing bars are one thin layer at the back of the window, H (bar depth) "
                  "thick, lying on the print bed, while the frame and sashes stand out at the "
                  "front. Set G and H to your nozzle width at your scale (0.4 mm at 1:80 = 32 mm)."),
    'join': ("Join into one solid", "Uses IngeTrazo's own Union (the Solid Tools) so the window, "
                                    "its sill and its head come out as one clean, watertight solid "
                                    "(glass stays separate). Best for exporting to a slicer."),
    'cut': ("Cut through the wall", "When the face is drawn on a solid wall, the window, sill and "
                                    "head are cut right through it, and they all sit flush with the "
                                    "back of the wall. The wall face is left clean for bricks."),
    'lift': ("Gap round the window", 0.0, 5.0, 3, " mm", "A tiny gap between the window (with its sill "
                                                        "and head) and the wall, so slicers don't get "
                                                        "confused by faces lying exactly on top of each "
                                                        "other. 0.01 mm is plenty."),
    'flip': ("Window faces the other way", "Tick if the window, sill and head come out on the wrong "
                                           "side of the wall or roof."),
    'open': ("Show the window open", "Sashes slide up, casements swing out, top lights and "
                                     "pivot lights tilt."),
    'sash_open': ("Sash open", 0.0, 100.0, 0, " %", "How far the bottom sash is slid up."),
    'open_angle': ("Opening angle", 0.0, 120.0, 0, " deg", "How far casements and pivot lights open."),
    'glass': ("Glass", "Adds glass as its own group (so you can hide it or print it in clear)."),
    'glass_t': ("Glass thickness", 0.1, 50.0, 1, " mm", ""),
    'cols': ("Panes across", 1, 20, None, "", "Columns of panes (per sash or leaf)."),
    'rows': ("Panes up", 1, 20, None, "", "Rows of panes (per sash or leaf)."),
    'cols_b': ("Bottom sash panes across", 1, 20, None, "", ""),
    'rows_b': ("Bottom sash panes up", 1, 20, None, "", ""),
    'arch_bars': ("Bars in the arch", "What the glazing bars do above the springing of an arched top."),
    'meet': ("Meeting rail height", 10.0, 90.0, 0, " %", "Where the two sashes meet, as a "
                                                         "percentage of the window height."),
    'leaves': ("Casement leaves", 1, 8, None, "", "How many hinged leaves side by side."),
    'mullion_w': ("Mullion / transom width", 5.0, 500.0, 0, " mm", ""),
    'transom': ("Transom height", 0.0, 95.0, 0, " %", "Height of the transom as a percentage of the "
                                                      "window (0 = no transom or top lights)."),
    'pivot': ("Pivoting opening light", "One pane of the grid turns on a level pivot (shown tilted "
                                         "when the window is open)."),
    'pivot_col': ("Pivot pane: column", 1, 20, None, "", "Counted from the left."),
    'pivot_row': ("Pivot pane: row", 1, 20, None, "", "Counted from the bottom."),
    'sill': ("Sill", ""),
    'sill_shape': ("Sill shape", "Weathered: the top slopes down to the front, like a real stone sill. "
                                 "Square: a plain block. Chamfered: square with the top front edge "
                                 "cut off at 45 degrees."),
    'sill_h': ("Stone sill height", 10.0, 500.0, 0, " mm", ""),
    'sill_p': ("Sill sticks out", 0.0, 500.0, 0, " mm", "How far the sill stands out from the wall face."),
    'horn': ("Sill runs past opening", 0.0, 500.0, 0, " mm", "How far the sill goes into the wall at "
                                                             "each side."),
    'head': ("Head", "A lintel or soldier course over a square top; an arch of stones or bricks "
                     "over a round, segmental, pointed or round window."),
    'head_h': ("Head depth", 20.0, 1000.0, 0, " mm", "Height of the lintel or soldier course, or "
                                                     "the depth of the arch."),
    'head_p': ("Head sticks out", 0.0, 200.0, 0, " mm", ""),
    'bearing': ("Lintel runs past opening", 0.0, 500.0, 0, " mm", "Flat heads only, each side."),
    'keystone': ("Keystone", ""),
    'key_w': ("Keystone width", 20.0, 1000.0, 0, " mm", ""),
    'key_up': ("Keystone rises above head", 0.0, 500.0, 0, " mm", ""),
    'key_p': ("Keystone sticks out more", 0.0, 200.0, 0, " mm", ""),
    'frame_w': ("Frame width", 5.0, 500.0, 0, " mm", "Face width of the outer frame."),
    'frame_d': ("Frame depth", 5.0, 500.0, 0, " mm", ""),
    'sash_w': ("Sash / leaf stiles", 5.0, 300.0, 0, " mm", "Width of the sides and top of each sash or leaf."),
    'sash_d': ("Sash / leaf thickness", 5.0, 200.0, 0, " mm", ""),
    'bottom_rail': ("Bottom rail", 5.0, 300.0, 0, " mm", "Width of the bottom rail of a sash."),
    'meet_w': ("Meeting rail", 5.0, 200.0, 0, " mm", ""),
    'bar_w': ("Glazing bar width", 1.0, 200.0, 1, " mm", ""),
    'bar_d': ("Glazing bar depth", 1.0, 200.0, 1, " mm", ""),
    'brick_w': ("Sill brick height", 30.0, 300.0, 1, " mm", "Height of a brick-on-edge sill "
                                                                 "(a brick's width)."),
    'brick_t': ("Brick thickness", 20.0, 200.0, 1, " mm", "Width of each brick as seen in a soldier "
                                                          "course, brick arch or brick sill."),
    'joint': ("Mortar joint", 0.0, 30.0, 1, " mm", ""),
}

# each size has a letter, shown next to its box and on the 'Sizes' drawing
LETTERS = {'frame_w': 'A', 'frame_d': 'B', 'sash_w': 'C', 'sash_d': 'D', 'bottom_rail': 'E',
           'meet_w': 'F', 'bar_w': 'G', 'bar_d': 'H', 'mullion_w': 'J', 'glass_t': 'K', 'rise': 'L',
           'sill_h': 'M', 'sill_p': 'N', 'horn': 'P', 'head_h': 'Q', 'head_p': 'R', 'bearing': 'S',
           'key_w': 'T', 'key_up': 'U', 'key_p': 'V', 'brick_w': 'W', 'brick_t': 'X', 'joint': 'Y'}

TABS = [
    ("Window", ('style', 'top', 'rise', 'flat', 'bars_back', 'join', 'remove_face', 'cut', 'lift', 'flip', 'open', 'sash_open', 'open_angle',
                'glass', 'glass_t')),
    ("Panes", ('cols', 'rows', 'cols_b', 'rows_b', 'arch_bars', 'meet', 'leaves', 'mullion_w',
               'transom', 'pivot', 'pivot_col', 'pivot_row')),
    ("Sill && head", ('sill', 'sill_shape', 'sill_h', 'sill_p', 'horn', 'head', 'head_h', 'head_p', 'bearing',
                      'keystone', 'key_w', 'key_up', 'key_p')),
    ("Sizes", ('frame_w', 'frame_d', 'sash_w', 'sash_d', 'bottom_rail', 'meet_w', 'bar_w', 'bar_d',
               'brick_w', 'brick_t', 'joint')),
]


# ---------------------------------------------------------------------------
# The key: what each lettered size (A, B, C ...) measures, drawn like the Subframe key,
# with the size each one is set to now beside it
# ---------------------------------------------------------------------------
KEY_NOTES = [('A', 'frame_w', "frame width"), ('B', 'frame_d', "frame stands out from the wall"),
             ('C', 'sash_w', "sash / leaf stiles"), ('D', 'sash_d', "sash / leaf thickness"),
             ('E', 'bottom_rail', "bottom rail (sash)"), ('F', 'meet_w', "meeting rail (sash)"),
             ('G', 'bar_w', "glazing bar width"), ('H', 'bar_d', "glazing bar depth"),
             ('J', 'mullion_w', "mullion / transom (casement)"), ('K', 'glass_t', "glass thickness"),
             ('L', 'rise', "arch rise (segmental)"), ('M', 'sill_h', "stone sill height"),
             ('N', 'sill_p', "sill sticks out"), ('P', 'horn', "sill runs past the opening"),
             ('Q', 'head_h', "head depth"), ('R', 'head_p', "head sticks out"),
             ('S', 'bearing', "lintel runs past the opening"), ('T', 'key_w', "keystone width"),
             ('U', 'key_up', "keystone rises above the head"), ('V', 'key_p', "keystone sticks out more"),
             ('W', 'brick_w', "sill brick height"), ('X', 'brick_t', "brick thickness"),
             ('Y', 'joint', "mortar joint")]


class WindowKey(QWidget):
    """A drawing that shows what each lettered size is, with what it's set to now."""
    W_, H_ = 360.0, 1040.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(int(self.W_), int(self.H_))
        self.v = dict(DEFAULTS)
        self.d, self.msg = None, ""

    def show_window(self, sh, v):
        self.v = dict(v)
        self.update()

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
        from PySide6.QtCore import QPointF, QRectF, Qt
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 246))
        k = min(float(self.width()) / self.W_, float(self.height()) / self.H_)
        p.scale(k, k)
        red = QColor(200, 40, 40)
        wallc, paint, glass = QColor(214, 196, 170), QColor(244, 242, 234), QColor(200, 225, 245)
        stone, brick, ink = QColor(204, 196, 178), QColor(178, 90, 60), QColor(60, 60, 60)
        bold = QFont()
        bold.setBold(True)
        bold.setPointSizeF(9.5)
        small = QFont()
        small.setPointSizeF(8.5)

        def poly(pts, col, pen=None):
            p.setPen(pen or QPen(col.darker(160), 0.8))
            p.setBrush(col)
            p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in pts]))

        def box(x, y, w, h, col):
            poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], col)

        def dim(x1, y1, x2, y2, letter, tx, ty):
            p.setFont(bold)
            p.setPen(QPen(red, 1.1))
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            ang = math.atan2(y2 - y1, x2 - x1)
            for (x, y, a) in ((x1, y1, ang), (x2, y2, ang + math.pi)):
                for s_ in (0.45, -0.45):
                    p.drawLine(QPointF(x, y), QPointF(x + 6 * math.cos(a + s_), y + 6 * math.sin(a + s_)))
            p.setPen(red)
            p.drawText(QRectF(tx - 10, ty - 9, 20, 18), Qt.AlignCenter, letter)

        def title(y, text):
            p.setFont(bold)
            p.setPen(ink)
            p.drawText(QRectF(10, y, 340, 18), Qt.AlignLeft, text)

        # ---- 1. the window from the front (a sash window, stone sill, lintel and keystone)
        title(4, "The window from the front")
        box(20, 26, 320, 290, wallc)
        ox0, ox1, oy0, oy1 = 110.0, 250.0, 95.0, 265.0          # the opening
        A_, C_, E_, F_, G_ = 12.0, 9.0, 14.0, 8.0, 4.0
        box(85, 67, 190, 28, stone)                              # lintel (Q deep, S past each side)
        poly([(169, 95), (191, 95), (194, 57), (166, 57)], stone.darker(108))   # keystone
        box(ox0, oy0, ox1 - ox0, oy1 - oy0, paint)               # the frame (A)
        ix0, ix1, iy0, iy1 = ox0 + A_, ox1 - A_, oy0 + A_, oy1 - A_
        ym = (iy0 + iy1) / 2.0
        box(ix0, iy0, ix1 - ix0, ym - iy0, paint.darker(104))   # top sash
        box(ix0, ym, ix1 - ix0, iy1 - ym, paint.darker(104))    # bottom sash
        for (y0_, y1_, bot) in ((iy0, ym, F_), (ym, iy1, E_)):
            top = F_ if y0_ == ym else C_
            gx0, gx1, gy0, gy1 = ix0 + C_, ix1 - C_, y0_ + top, y1_ - bot
            box(gx0, gy0, gx1 - gx0, gy1 - gy0, glass)
            p.setPen(QPen(paint.darker(150), 0.6))
            p.setBrush(paint)
            for i in (1, 2):                                     # 3 x 2 panes
                bx = gx0 + (gx1 - gx0) * i / 3.0
                p.drawRect(QRectF(bx - G_ / 2, gy0, G_, gy1 - gy0))
            byy = (gy0 + gy1) / 2.0
            p.drawRect(QRectF(gx0, byy - G_ / 2, gx1 - gx0, G_))
        poly([(88, oy1), (272, oy1), (272, oy1 + 16), (88, oy1 + 16)], stone)   # the sill
        dim(ox0, 140, ox0 + A_, 140, "A", ox0 - 8, 130)
        dim(ix0, 205, ix0 + C_, 205, "C", ix0 + 16, 196)
        dim(205, iy1 - E_, 205, iy1, "E", 216, iy1 - 7)
        dim(150, ym - F_, 150, ym + F_, "F", 140, ym)
        bx = ix0 + C_ + (ix1 - ix0 - 2 * C_) / 3.0
        dim(bx - G_ / 2, 150, bx + G_ / 2, 150, "G", bx, 160)
        dim(282, oy1, 282, oy1 + 16, "M", 294, oy1 + 8)
        dim(ox1, oy1 + 26, 272, oy1 + 26, "P", 261, oy1 + 37)
        dim(78, 67, 78, 95, "Q", 66, 81)
        dim(85, 104, ox0, 104, "S", 97, 114)
        dim(166, 48, 194, 48, "T", 180, 38)
        dim(204, 57, 204, 67, "U", 215, 58)

        # ---- 2. seen end on: a slice up through the middle of the window
        title(330, "Seen end on (outside on the left)")
        fx, bxk = 170.0, 212.0                                   # wall face, back of the wall
        box(fx, 360, bxk - fx, 62, wallc)                        # wall above the opening
        box(fx, 510, bxk - fx, 50, wallc)                        # wall below
        p.setPen(ink)
        p.setFont(small)
        p.drawText(QRectF(fx, 548, bxk - fx, 12), Qt.AlignCenter, "wall")
        B_, D_, H_, K_ = 38.0, 10.0, 6.0, 3.0
        front = fx - B_
        poly([(bxk, 408), (front - 6, 408), (front - 6, 422), (bxk, 422)], stone)        # head (R)
        poly([(bxk, 396), (front - 12, 396), (front - 12, 408), (bxk, 408)], stone.darker(108))  # keystone (V)
        box(front, 422, bxk - front, 10, paint)                  # frame head
        box(front, 488, bxk - front, 10, paint)                  # frame bottom
        box(front + 6, 432, D_, 30, paint.darker(104))           # top sash
        box(front + 6 + D_ + 2, 462, D_, 26, paint.darker(104))  # bottom sash
        box(bxk - H_, 432, H_, 56, paint.darker(112))            # glazing bars, at the back
        box(bxk - H_ - K_, 432, K_, 56, glass)                   # glass
        poly([(bxk, 498), (front - 20, 498), (front - 20, 510), (bxk, 510)], stone)      # sill (N)
        dim(front, 444, fx, 444, "B", (front + fx) / 2, 454)
        dim(front + 6, 474, front + 6 + D_, 474, "D", front + 11, 484)
        dim(bxk - H_, 476, bxk, 476, "H", bxk + 10, 476)
        dim(bxk - H_ - K_, 440, bxk - H_, 440, "K", bxk - H_ - K_ - 10, 440)
        dim(front - 20, 520, front, 520, "N", front - 10, 531)
        dim(front - 6, 380, front, 380, "R", front - 3, 370)
        dim(front - 12, 392, front - 6, 392, "V", front - 9 - 14, 392)
        p.setPen(QPen(QColor(150, 150, 150), 0.6, Qt.DashLine))
        p.drawLine(QPointF(front - 6, 380), QPointF(front - 6, 408))
        p.drawLine(QPointF(front, 380), QPointF(front, 422))
        p.setPen(ink)
        p.setFont(small)
        p.drawText(QRectF(222, 430, 130, 70), Qt.AlignLeft | Qt.TextWordWrap,
                   "With 'Flat back for 3D printing' everything goes down to the back, so the "
                   "window prints flat with the wall.")

        # ---- 3. casement mullion, segmental arch, brick sill and soldier course
        title(572, "Casement (J)")
        p.drawText(QRectF(135, 572, 100, 18), Qt.AlignLeft, "Arch (L)")
        p.drawText(QRectF(250, 572, 110, 18), Qt.AlignLeft, "Bricks (W, X, Y)")
        box(20, 600, 90, 100, paint)                             # a 2-leaf casement
        box(28, 608, 32, 84, glass)
        box(70, 608, 32, 84, glass)
        dim(60, 704, 70, 704, "J", 65, 714)
        ax0, ax1, ay = 135.0, 225.0, 650.0                       # a segmental arch window
        rise = 16.0
        cx, half = (ax0 + ax1) / 2.0, (ax1 - ax0) / 2.0
        R = (half * half + rise * rise) / (2 * rise)
        a0 = math.asin(half / R)
        pts = [(ax0, 700), (ax1, 700), (ax1, ay)]
        for i in range(17):
            a = a0 - 2 * a0 * i / 16.0
            pts.append((cx + R * math.sin(a), ay + R - rise - R * math.cos(a)))
        pts.append((ax0, ay))
        poly(pts, glass, QPen(paint.darker(160), 1.0))
        p.setPen(QPen(QColor(150, 150, 150), 0.6, Qt.DashLine))
        p.drawLine(QPointF(ax0 - 8, ay), QPointF(ax1 + 8, ay))
        dim(ax1 + 12, ay, ax1 + 12, ay - rise, "L", ax1 + 24, ay - 8)
        bx0, by = 250.0, 690.0                                   # bricks on edge under, soldiers over
        bw, bj = 12.0, 3.0
        for i in range(6):
            box(bx0 + i * (bw + bj), by, bw, 16, brick)
            box(bx0 + i * (bw + bj), 600, bw, 26, brick)
        box(bx0, 626, 6 * (bw + bj) - bj, 64, glass)
        dim(bx0 - 8, by, bx0 - 8, by + 16, "W", bx0 - 18, by + 8)
        dim(bx0, by + 24, bx0 + bw, by + 24, "X", bx0 + 6, by + 35)
        dim(bx0 + bw, by + 24, bx0 + bw + bj, by + 24, "Y", bx0 + bw + bj + 12, by + 35)

        # ---- the notes, with the size each one is set to now
        title(728, "Sizes - set now (real-world mm)")
        p.setFont(small)
        for i, (letter, key, text) in enumerate(KEY_NOTES):
            col, row = 0, i
            val = self.v.get(key)
            sval = ("%g mm" % round(float(val), 1)) if isinstance(val, (int, float)) else ""
            p.setPen(red)
            p.drawText(QRectF(10 + col * 175, 750 + row * 12.2, 14, 12), Qt.AlignLeft | Qt.AlignVCenter, letter)
            p.setPen(ink)
            p.drawText(QRectF(24, 750 + row * 12.2, 230, 12), Qt.AlignLeft | Qt.AlignVCenter, text)
            p.drawText(QRectF(260, 750 + row * 12.2, 90, 12), Qt.AlignLeft | Qt.AlignVCenter, sval)
        p.end()


class WindowsDialog(QDialog):
    CUSTOM = "-- Custom --"

    def __init__(self, cur, viewport, tool):
        super().__init__(viewport)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.user_presets = load_presets()
        self.sel_shape = None          # the first selected opening, for the preview
        self._busy = False
        lay = QVBoxLayout(self)

        self.lbl_sel = QLabel()
        self.lbl_sel.setWordWrap(True)
        self.lbl_sel.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl_sel)
        # what happened last time 'Add window' was clicked
        self.lbl_report = QLabel()
        self.lbl_report.setWordWrap(True)
        try:
            from PySide6.QtCore import Qt
            self.lbl_report.setTextInteractionFlags(Qt.TextSelectableByMouse)
        except Exception:
            pass
        self.lbl_report.setVisible(False)
        lay.addWidget(self.lbl_report)

        row = QHBoxLayout()
        lay.addLayout(row)
        self.views = QTabWidget()
        self.preview = WindowPreview()
        self.sizes = WindowKey()
        from PySide6.QtWidgets import QScrollArea
        key_scroll = QScrollArea()
        key_scroll.setWidget(self.sizes)
        key_scroll.setWidgetResizable(True)
        self.views.addTab(self.preview, "3D view")
        self.views.addTab(key_scroll, "Key (A, B, C...)")
        row.addWidget(self.views, 1)
        self.tabs = QTabWidget()
        row.addWidget(self.tabs, 1)

        self.w = {}
        self.labels = {}
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
                    wdg.setKeyboardTracking(False)
                    wdg.valueChanged.connect(self.changed)
                if tip:
                    wdg.setToolTip(tip)
                lab = QLabel(("%s   %s" % (LETTERS[k], spec[0])) if k in LETTERS else spec[0])
                if tip:
                    lab.setToolTip(tip)
                form.addRow(lab, wdg)
                self.w[k] = wdg
                self.labels[k] = lab
            self.tabs.addTab(page, title)
        self._add_building_page()
        self.tabs.setUsesScrollButtons(False)
        self.views.setUsesScrollButtons(False)

        # presets
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
        b_up = QPushButton("\u25b2")
        b_down = QPushButton("\u25bc")
        b_up.setToolTip("Move the preset you have open up the list.")
        b_down.setToolTip("Move the preset you have open down the list.")
        for b in (b_up, b_down):
            b.setFixedWidth(30)
        for b in (b_up, b_down, b_save, b_saveas, b_del, b_dir):
            prow.addWidget(b)
        lay.addLayout(prow)
        b_up.clicked.connect(lambda: self.move_preset(-1))
        b_down.clicked.connect(lambda: self.move_preset(1))
        b_save.clicked.connect(self.save_preset)
        b_saveas.clicked.connect(lambda: self.save_preset_as())
        b_del.clicked.connect(self.delete_preset)
        b_dir.clicked.connect(self.open_folder)
        self.cb_preset.currentIndexChanged.connect(self.apply_preset)

        brow = QHBoxLayout()
        self.b_add = QPushButton("Add window to selected face(s)")
        self.b_add.setDefault(True)
        b_refresh = QPushButton("Preview selected face")
        b_close = QPushButton("Close")
        brow.addWidget(self.b_add)
        brow.addWidget(b_refresh)
        brow.addStretch(1)
        brow.addWidget(b_close)
        lay.addLayout(brow)
        self.b_add.clicked.connect(lambda: self.tool.add_from_dialog(self))
        b_refresh.clicked.connect(self.read_selection)
        b_close.clicked.connect(self.close)

        self.refresh_presets()
        self.set_values(cur)
        self.read_selection()

    # ---- whole building ----
    def _add_building_page(self):
        from PySide6.QtWidgets import QListWidget
        page = QWidget()
        lay = QVBoxLayout(page)
        info = QLabel(("Select the building, some of its wall groups, or just a wall face (the outside "
                       "face - the %(ns)s go on the face you pick), and click Find. Every opening in "
                       "the outside of the walls lights up and is listed here. Untick any you don't "
                       "want, then Build: each %(n)s, with its %(sill)s and head, is joined into its own "
                       "wall section, flat with the back of the wall - so in Scale Studio's Pieces "
                       "page each wall lays flat and prints as one piece, %(ns)s and all. The %(n)s "
                       "is made from the settings on the other pages.") % WB_WORDS)
        info.setWordWrap(True)
        lay.addWidget(info)
        self.b_find = QPushButton("Find openings in the selected building, group or face")
        self.b_find.setToolTip("Lights up every opening in the outside walls of the selected building "
                               "or groups, or in the selected face(s) - or the whole model if nothing is "
                               "selected - and lists them below.")
        lay.addWidget(self.b_find)
        self.lst_open = QListWidget()
        self.lst_open.setToolTip(("Ticked openings get a %(n)s (%(os)s start unticked). Click a line to "
                                  "light that opening up in the model and look at it; pick a wall in the "
                                  "model and its openings light up here.") % WB_WORDS)
        lay.addWidget(self.lst_open, 1)
        row = QHBoxLayout()
        b_all = QPushButton("Tick all empty %(n)s openings" % WB_WORDS)
        b_none = QPushButton("Untick all")
        row.addWidget(b_all)
        row.addWidget(b_none)
        lay.addLayout(row)
        form = QFormLayout()
        self.sp_overlap = QDoubleSpinBox()
        self.sp_overlap.setDecimals(1)
        self.sp_overlap.setRange(0.0, 200.0)
        self.sp_overlap.setSuffix(" mm")
        self.sp_overlap.setValue(WB_DEFAULT_OVERLAP)
        self.sp_overlap.setToolTip(("How far each %(n)s reaches into the wall round the opening, so "
                                    "they join into one solid. Real-world mm, like the other sizes. It "
                                    "never goes more than a quarter of the frame width (A).") % WB_WORDS)
        form.addRow("%(N)s reaches into the wall" % WB_WORDS, self.sp_overlap)
        lay.addLayout(form)
        self.b_build = QPushButton("Build %(ns)s into their walls" % WB_WORDS)
        self.b_takeout = QPushButton("Take out ticked %(ns)s" % WB_WORDS)
        self.b_takeout.setToolTip(("Takes the ticked %(ns)s (the ones marked 'has a %(n)s') out of their "
                                   "walls again, leaving the openings as they were.") % WB_WORDS)
        self.b_build.setToolTip(("Puts a %(n)s into every ticked opening and joins it into its wall "
                                 "section. One Undo takes them all away again.") % WB_WORDS)
        brow2 = QHBoxLayout()
        brow2.addWidget(self.b_build, 2)
        brow2.addWidget(self.b_takeout, 1)
        lay.addLayout(brow2)
        self.cb_fill = QCheckBox("Taking out also fills the opening in (so a new one can be cut)")
        self.cb_fill.setToolTip(("With this ticked, 'Take out ticked %(ns)s' also closes up the opening - the "
                                 "hole and its reveals go and the wall is solid there again - so you can cut "
                                 "a new opening somewhere else with 3D Openings. Works on empty openings "
                                 "too. (A doorway cut up from the bottom of the wall can't be filled this "
                                 "way.) One Undo puts it all back.") % WB_WORDS)
        lay.addWidget(self.cb_fill)
        self.cb_colour = QCheckBox("Colour the %(ns)s when building (just for looks - prints the same)" % WB_WORDS)
        self.cb_colour.setChecked(True)
        self.cb_colour.setToolTip(("Paints each part of the %(ns)s built into the walls - frame, door or sash, "
                                   "step or sill, head, knob - in its own colour, so the model looks the "
                                   "part. With 3D Layers & Colours loaded its colours are used (change "
                                   "them there); the wall keeps its own colour.") % WB_WORDS)
        lay.addWidget(self.cb_colour)
        self.lbl_found = QLabel()
        self.lbl_found.setWordWrap(True)
        lay.addWidget(self.lbl_found)
        self.found = []
        self._sel_sig = None
        self._syncing = False
        from PySide6.QtWidgets import QAbstractItemView
        from PySide6.QtCore import QTimer
        self.lst_open.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lst_open.itemSelectionChanged.connect(self._list_picked)
        # keep an eye on what's selected in the model, to light up its openings in the list
        self._sel_timer = QTimer(self)
        self._sel_timer.setInterval(400)
        self._sel_timer.timeout.connect(self._watch_selection)
        self._sel_timer.start()
        self.b_find.clicked.connect(self.find_openings)
        self.b_build.clicked.connect(lambda: self.tool.build_into_walls(self))
        self.b_takeout.clicked.connect(lambda: self.tool.build_into_walls(self, take_out=True))
        b_all.clicked.connect(lambda: self._tick(True))
        b_none.clicked.connect(lambda: self._tick(False))
        self.tabs.addTab(page, "Whole building")

    @staticmethod
    def _wants(op):
        """Is this an empty opening of the kind this plugin fills (a doorway for doors)?"""
        return (not op.get('built') and op['depth'] is not None
                and bool(op['door']) == (WB_KIND == 'door'))

    def _tick(self, on):
        from PySide6.QtCore import Qt
        for i in range(self.lst_open.count()):
            it = self.lst_open.item(i)
            want = i < len(self.found) and self._wants(self.found[i])
            it.setCheckState(Qt.Checked if (on and want) else Qt.Unchecked)

    def find_openings(self):
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QListWidgetItem
        scene = getattr(self.viewport, 'scene', None)
        if scene is None:
            return
        try:
            self.found = find_building_openings(scene, self.w['flip'].isChecked())
        except Exception as e:
            self.found = []
            QMessageBox.warning(self, PLUGIN_NAME, "Could not look for openings:\n%s" % e)
            return
        # this plugin only: door openings (and doors built in) for doors, the rest for windows
        self.found = [op for op in self.found
                      if (op['built'].get('kind', 'window') == WB_KIND if op.get('built')
                          else bool(op['door']) == (WB_KIND == 'door'))]
        self.lst_open.clear()
        for op in self.found:
            txt = "%s  -  %.0f x %.0f mm" % (op['name'], op['w'], op['h'])
            if op.get('built'):
                txt += "  - has a %s" % op['built'].get('kind', 'window')
            elif op['depth'] is None:
                txt += "  (no back of the wall found)"
            it = QListWidgetItem(txt)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            if op.get('built'):
                f = it.font()
                f.setBold(True)
                it.setFont(f)
            it.setCheckState(Qt.Checked if self._wants(op) else Qt.Unchecked)
            self.lst_open.addItem(it)
        # light them up in the model
        edges = []
        for op in self.found:
            edges += opening_edges(op)
        try:
            scene.selection.clear()
            for e in edges:
                scene.selection.add(e)
        except Exception:
            pass
        try:
            self.viewport.notify_scene_changed()
        except Exception:
            try:
                self.viewport.update()
            except Exception:
                pass
        self._sel_sig = self._selection_sig(scene)
        mine = sum(1 for op in self.found if self._wants(op))
        nb = sum(1 for op in self.found if op.get('built'))
        if self.found:
            pl = lambda n: "" if n == 1 else "s"
            self.lbl_found.setText(("Found %d empty %s opening%s and %d %s%s already built in (in bold - "
                                    "click one to load its settings, change them, tick it and Build to "
                                    "make it again).")
                                   % (mine, WB_WORDS['n'], pl(mine), nb, WB_WORDS['n'], pl(nb)))
        else:
            self.lbl_found.setText(("No %(n)s openings found. Select the building or its walls (groups), "
                                    "with the openings already cut. If the %(ns)s would go on the "
                                    "inside, tick '%(N)s faces the other way' on the %(N)s page and "
                                    "Find again.") % WB_WORDS)

    def _selection_sig(self, scene):
        return frozenset(id(e) for e in _items(getattr(scene, 'selection', None)))

    def _watch_selection(self):
        """Something picked in the model (a wall, the building, a wall face or an opening's edges):
        its openings are lit up in the list, and the list scrolls to the first one."""
        if not self.found or not self.isVisible():
            return
        scene = getattr(self.viewport, 'scene', None)
        if scene is None:
            return
        try:
            sel = _items(scene.selection)
            sig = frozenset(id(e) for e in sel)
        except Exception:
            return
        if sig == self._sel_sig:
            return
        self._sel_sig = sig
        groups = [e for e in sel if hasattr(e, 'mesh')]
        ids = set(sig)
        rows = []
        for i, op in enumerate(self.found):
            hit = id(op['face']) in ids or any(g is op['group'] or _in_tree(g, op['group']) for g in groups)
            if not hit:
                try:
                    hit = any(id(e) in ids for e in opening_edges(op))
                except Exception:
                    hit = False
            if hit:
                rows.append(i)
        self._syncing = True
        try:
            self.lst_open.clearSelection()
            for i in rows:
                if i < self.lst_open.count():
                    self.lst_open.item(i).setSelected(True)
            if rows and rows[0] < self.lst_open.count():
                self.lst_open.scrollToItem(self.lst_open.item(rows[0]))
        finally:
            self._syncing = False

    def _list_picked(self):
        """Clicking openings in the list lights just those up in the model (and one is looked at)."""
        if self._syncing or not self.found:
            return
        scene = getattr(self.viewport, 'scene', None)
        if scene is None:
            return
        rows = sorted(self.lst_open.row(it) for it in self.lst_open.selectedItems())
        if len(rows) == 1 and rows[0] < len(self.found) and self.found[rows[0]].get('built'):
            item = self.found[rows[0]]['built']
            if item.get('kind', 'window') == WB_KIND:
                # one of ours already built in: its settings into the boxes, ready to change
                vals = dict(DEFAULTS)
                vals.update(item.get('values') or {})
                self.cb_preset.blockSignals(True)
                self.cb_preset.setCurrentIndex(0)
                self.cb_preset.blockSignals(False)
                self.set_values(vals)
                self.sp_overlap.setValue(item.get('overlap', WB_DEFAULT_OVERLAP))
                self.lbl_found.setText("Settings of %s loaded. Change them, tick it and click Build to make "
                                       "it again." % self.found[rows[0]]['name'])
            else:
                self.lbl_found.setText("%s has a %s - open %s to change it (or tick it and Build to put a "
                                       "%s there instead)." % (self.found[rows[0]]['name'], item.get('kind'),
                                                               WB_WORDS['other_plugin'], WB_WORDS['n']))
        edges = []
        for i in rows:
            if i < len(self.found):
                op = self.found[i]
                got = opening_edges(op)
                # a window or door built into its wall has no opening edges left: light up its wall
                edges += got if got else [op['group']]
        try:
            scene.selection.clear()
            for e in edges:
                scene.selection.add(e)
            self._sel_sig = self._selection_sig(scene)
        except Exception:
            return
        if len(rows) == 1 and rows[0] < len(self.found):
            try:
                zoom_to_opening(self.viewport, self.found[rows[0]])
            except Exception as e:
                print("%s: couldn't zoom: %s" % (PLUGIN_NAME, e))
        try:
            self.viewport.notify_scene_changed()
        except Exception:
            try:
                self.viewport.update()
            except Exception:
                pass

    def ticked_openings(self):
        from PySide6.QtCore import Qt
        out = []
        for i in range(min(self.lst_open.count(), len(self.found))):
            if self.lst_open.item(i).checkState() == Qt.Checked:
                out.append(self.found[i])
        return out

    # ---- values ----
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
                if d.get(k) is None:
                    continue
                if k in CHOICES:
                    for i in range(wdg.count()):
                        if wdg.itemData(i) == d[k]:
                            wdg.setCurrentIndex(i)
                elif k in BOOL_KEYS:
                    wdg.setChecked(bool(d[k]))
                elif k in INT_KEYS:
                    wdg.setValue(int(d[k]))
                else:
                    wdg.setValue(float(d[k]))
        finally:
            self._busy = False
        self.changed()

    def changed(self, *_):
        if self._busy:
            return
        v = self.values()
        st = v['style']
        en = {
            'rise': v['top'] == 'segment',
            'sash_open': v['open'] and st == 'sash',
            'open_angle': v['open'] and st != 'sash' and not v['flat'],
            'cut': v['remove_face'],
            'bars_back': v['flat'],
            'glass_t': v['glass'],
            'cols_b': st == 'sash' or (st == 'casement' and v['transom'] > 0),
            'rows_b': st == 'sash' or (st == 'casement' and v['transom'] > 0),
            'meet': st == 'sash', 'bottom_rail': st == 'sash', 'meet_w': st == 'sash',
            'leaves': st == 'casement', 'mullion_w': st == 'casement', 'transom': st == 'casement',
            'pivot': st == 'fixed', 'pivot_col': st == 'fixed' and v['pivot'],
            'pivot_row': st == 'fixed' and v['pivot'],
            'sash_w': st != 'fixed', 'sash_d': st != 'fixed',
            'sill_shape': v['sill'] != 'none',
            'sill_h': v['sill'] == 'stone', 'sill_p': v['sill'] != 'none', 'horn': v['sill'] != 'none',
            'head_h': v['head'] != 'none', 'head_p': v['head'] != 'none',
            'bearing': v['head'] != 'none', 'keystone': v['head'] != 'none',
            'key_w': v['keystone'] and v['head'] != 'none',
            'key_up': v['keystone'] and v['head'] != 'none',
            'key_p': v['keystone'] and v['head'] != 'none',
        }
        for k, on in en.items():
            self.w[k].setEnabled(bool(on))
            self.labels[k].setEnabled(bool(on))
        if st == 'sash':
            names = ("Top sash panes across", "Top sash panes up",
                     "Bottom sash panes across", "Bottom sash panes up")
        elif st == 'casement':
            names = ("Panes across (each leaf)", "Panes up (each leaf)",
                     "Top light panes across", "Top light panes up")
        else:
            names = ("Panes across", "Panes up", "-", "-")
        for k, t in zip(('cols', 'rows', 'cols_b', 'rows_b'), names):
            self.labels[k].setText(t)
        self.update_preview(v)

    def update_preview(self, v=None):
        v = v or self.values()
        try:
            if self.sel_shape is not None:
                poly = self.sel_shape
            elif v['top'] == 'circle':
                poly = [(0, 0), (900, 0), (900, 900), (0, 900)]
            else:
                poly = [(0, 0), (900, 0), (900, 1500), (0, 1500)]
            sh = fit_shape(poly, v['top'], v['rise'])
        except Exception as e:
            self.preview.items, self.preview.msg = [], str(e)
            self.preview.update()
            self.sizes.d, self.sizes.msg = None, str(e)
            self.sizes.update()
            return
        self.preview.show_window(sh, v)
        self.sizes.show_window(sh, v)

    def show_report(self, lines):
        """Shows the result of the last 'Add window' under the selection line
        (the text can be selected and copied)."""
        if not lines:
            self.lbl_report.setVisible(False)
            return
        bad = any(l.startswith("NOT") or l.startswith("Could not") or "couldn't" in l
                  or "could not" in l for l in lines)
        self.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if bad else "#2e7d32"))
        self.lbl_report.setText("Last window added:\n" + "\n".join(lines))
        self.lbl_report.setVisible(True)

    def read_selection(self, *_):
        scene = getattr(self.viewport, 'scene', None)
        faces = selected_faces(scene) if scene is not None else []
        flip = self.w['flip'].isChecked()
        polys = []
        for f in faces:
            try:
                polys += face_openings(f, flip)[1]
            except Exception:
                pass
        if polys:
            x0, x1, y0, y1 = bbox(polys[0])
            self.sel_shape = [(x - x0, y - y0) for x, y in polys[0]]
            self.lbl_sel.setText("Selected: %d face%s, %d opening%s (first one %d x %d mm). "
                                 "Click 'Add window' to fit a window into each."
                                 % (len(faces), "" if len(faces) == 1 else "s", len(polys),
                                    "" if len(polys) == 1 else "s", round(x1 - x0), round(y1 - y0)))
        else:
            self.sel_shape = None
            self.lbl_sel.setText("Select a face drawn on a wall or roof (or a face with openings in "
                                 "it), then click 'Add window'. The preview shows a 900 x 1500 mm window.")
        self.update_preview()

    def changeEvent(self, e):
        try:
            from PySide6.QtCore import QEvent
            if e.type() == QEvent.ActivationChange and self.isActiveWindow():
                self.read_selection()
        except Exception:
            pass
        super().changeEvent(e)

    # ---- presets ----
    def all_presets(self):
        p = dict(BUILTIN_PRESETS)
        p.update(self.user_presets)
        return p

    def refresh_presets(self, select=None):
        self.cb_preset.blockSignals(True)
        self.cb_preset.clear()
        self.cb_preset.addItem(self.CUSTOM, None)
        for name in self.preset_names():
            self.cb_preset.addItem(name + "  (built-in)" if name in BUILTIN_PRESETS else name, name)
        for i in range(self.cb_preset.count()):
            if select and self.cb_preset.itemData(i) == select:
                self.cb_preset.setCurrentIndex(i)
        self.cb_preset.blockSignals(False)

    def remember(self):
        """Keeps the preset you have open and the settings, for next time (even after a restart)."""
        try:
            name = self.cb_preset.currentData() or getattr(self, '_last_preset', None)
            save_last(name, self.values())
        except Exception:
            pass

    def show_preset_name(self, name):
        """Puts a preset's name in the list without loading it over the settings."""
        if not name:
            return
        self.cb_preset.blockSignals(True)
        for i in range(self.cb_preset.count()):
            if self.cb_preset.itemData(i) == name:
                self.cb_preset.setCurrentIndex(i)
        self.cb_preset.blockSignals(False)

    def preset_names(self):
        """Every preset, built-in and your own, in the order you've arranged them."""
        names = list(BUILTIN_PRESETS) + [n for n in sorted(self.user_presets) if n not in BUILTIN_PRESETS]
        order = load_order()
        return [n for n in order if n in names] + [n for n in names if n not in order]

    def move_preset(self, step):
        """Moves the preset you have open up (-1) or down (+1) the list, and remembers the order."""
        name = self.cb_preset.currentData()
        if not name:
            QMessageBox.information(self, PLUGIN_NAME, "Pick a preset in the list first, then move it.")
            return
        names = self.preset_names()
        i = names.index(name) if name in names else -1
        j = i + step
        if i < 0 or j < 0 or j >= len(names):
            return
        names[i], names[j] = names[j], names[i]
        save_order(names)
        self.refresh_presets(select=name)

    def apply_preset(self, *_):
        name = self.cb_preset.currentData()
        p = self.all_presets().get(name) if name else None
        if p:
            self._last_preset = name
            QTimer_remember(self)
        if p:
            # built-in presets are complete windows: start them from the defaults
            self.set_values(dict(DEFAULTS, **p) if name in BUILTIN_PRESETS else p)

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
            save_preset_file(name, self.values())
        except Exception as e:
            QMessageBox.warning(self, PLUGIN_NAME, "Could not save the preset:\n%s" % e)
            return False
        self.user_presets = load_presets()
        self.refresh_presets(select=name)
        self._last_preset = name
        self.remember()
        return True

    def delete_preset(self):
        name = self.cb_preset.currentData()
        if not name or name not in self.user_presets:
            QMessageBox.information(self, PLUGIN_NAME, "Pick one of your own presets to delete "
                                    "(built-in presets can't be deleted).")
            return
        if QMessageBox.question(self, PLUGIN_NAME, "Delete preset '%s'?" % name) != QMessageBox.Yes:
            return
        delete_preset_file(name)
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


class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
class PeriodWindowsTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+N"
    description = ("Old-fashioned sash, casement and industrial windows that fit the selected face, "
                   "with round tops, panes, sills, heads and keystones.")

    _saved = None
    _dialog = None
    _join = True
    _cut = True
    last_report = []

    def on_activate(self, viewport):
        dlg = PeriodWindowsTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.read_selection()
                    dlg.raise_()
                    dlg.activateWindow()
                    return
            except Exception:
                pass
        # always open with the preset you used last (as it's saved); failing that, the settings
        # as you left them
        cur = dict(DEFAULTS)
        last = load_last()
        pname = last.get('preset')
        presets = dict(BUILTIN_PRESETS)
        presets.update(load_presets())
        if pname and pname in presets:
            cur.update({k: x for k, x in presets[pname].items() if k in DEFAULTS})
        elif PeriodWindowsTool._saved:
            cur.update(PeriodWindowsTool._saved)
        elif isinstance(last.get('values'), dict):
            cur.update({k: x for k, x in last['values'].items() if k in DEFAULTS})
        dlg = WindowsDialog(cur, viewport, self)
        PeriodWindowsTool._dialog = dlg
        dlg._last_preset = pname if (pname and pname in presets) else None
        dlg.show_preset_name(dlg._last_preset)

        def closed(*_):
            try:
                PeriodWindowsTool._saved = dlg.values()
                dlg.remember()
            except Exception:
                pass
            PeriodWindowsTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass

    def add_from_dialog(self, dlg):
        v = dlg.values()
        PeriodWindowsTool._saved = dict(v)
        dlg.remember()
        viewport = dlg.viewport
        scene = getattr(viewport, 'scene', None)
        faces = selected_faces(scene) if scene is not None else []
        if not faces:
            QMessageBox.information(dlg, PLUGIN_NAME, "Select a face first: a shape drawn on a wall "
                                    "or roof, or a face with openings in it.")
            return
        parts, problems, used, cuts = self.plan(faces, v, scene)
        if problems and not parts:
            QMessageBox.warning(dlg, PLUGIN_NAME, "\n".join(problems))
            return
        remove = used if v.get('remove_face', True) else []
        self._join = v.get('join', True)
        self._cut = v.get('cut', True)
        self.last_report = []
        ok = self.add_to_scene(viewport, parts, remove, cuts)
        if ok:
            dlg.read_selection()
            dlg.show_report(self.last_report)
        if ok and problems:
            QMessageBox.information(dlg, PLUGIN_NAME, "Some openings were skipped:\n" + "\n".join(problems))

    @staticmethod
    def plan(faces, v, scene=None):
        """[(group name, world solids)] for every opening of the faces, any problems,
        the faces to replace, and {face: outline to cut through the wall}."""
        parts, problems, used, cuts = [], [], [], {}
        n = 0
        gap = max(0.0, v.get('lift', 0.0))
        for face in faces:
            made = False
            try:
                frame, polys = face_openings(face, v['flip'])
            except ValueError as e:
                problems.append(str(e))
                continue
            tw0 = to_world(frame)
            mesh = mesh_of_face(scene, face) if scene is not None else None
            holes = _items(getattr(face, 'holes', None))
            info = None
            if (not holes and mesh is not None and v.get('remove_face', True) and v.get('cut', True)
                    and not v['flip']):
                try:
                    info = through_info(mesh, face)
                except Exception:
                    info = None
            for poly in polys:
                n += 1
                vv = dict(v)
                zlift = gap                     # no wall behind: just sit a hair off the face
                if info is not None:
                    # cut right through: everything sits on the back of the wall
                    vv['_base'] = vv['_base_sh'] = -info['depth'] / SCALE
                    zlift = 0.0
                elif holes and mesh is not None:
                    # an opening already there: the window fills it from the back of the wall,
                    # a hair smaller so it doesn't touch the sides
                    try:
                        wp = [tw0((x, y, 0.0)) for x, y in poly]
                        back = find_back(mesh, wp, frame[3], face)
                    except Exception:
                        back = None
                    if back is not None:
                        vv['_base'] = -back[1] / SCALE
                        vv['_base_sh'] = gap
                        poly = clean(offset_poly(poly, gap)) or poly if gap > 0 else poly
                        zlift = 0.0

                def tw(p, tw0=tw0, zl=zlift):
                    return tw0((p[0], p[1], p[2] + zl))
                try:
                    sh = fit_shape(poly, v['top'], v['rise'])
                    built = build_window(sh, vv)
                except ValueError as e:
                    problems.append("Opening %d: %s" % (n, e))
                    continue
                tag_parts(built, 'window', vv)
                if info is not None:
                    ol = cut_outline(sh, vv)
                    if gap > 0:
                        ol = clean(offset_poly(ol, -gap)) or ol        # a hair bigger all round
                    cuts[face] = [tw0((x, y, 0.0)) for x, y in ol]
                title = describe(sh, v)
                if v.get('join', True):
                    groups = [(title, built['window'] + built['sill'] + built['head']),
                              ("Glass - " + title, built['glass'])]
                else:
                    groups = [(title, built['window']), ("Glass - " + title, built['glass']),
                              ("%s - %s" % (dict(SILLS)[v['sill']], title), built['sill']),
                              ("%s - %s" % ("Keystone head" if v['keystone'] else "Head", title),
                               built['head'])]
                for name, sols in groups:
                    if sols:
                        parts.append((name, [s.mapped(tw) for s in sols]))
                made = True
            # a drawn face (no openings in it) is replaced by its window
            if made and not holes:
                used.append(face)
        return parts, problems, used, cuts

    def build_into_walls(self, dlg, take_out=False):
        """Whole building page: a window / door in every ticked opening (one already there is made
        again with the settings as they are now), joined into its wall section. With take_out, the
        ticked ones are taken out again instead. Each wall is built again from the plain wall kept
        with it, with everything in it (the other plugin's windows or doors kept as they were)."""
        v = dlg.values()
        type(self)._saved = dict(v)
        dlg.remember()
        ops = dlg.ticked_openings()
        fill = bool(take_out and getattr(dlg, 'cb_fill', None) is not None and dlg.cb_fill.isChecked())
        if take_out and not fill:
            ops = [op for op in ops if op.get('built')]
        if not ops:
            QMessageBox.information(dlg, PLUGIN_NAME, ("Tick the ones you want taken out (marked 'has a "
                                    "window' or 'has a door')." if take_out else "Click 'Find openings' "
                                    "first, and tick the openings you want %s in." % WB_WORDS['ns']))
            return
        filled, cant_fill = 0, []
        overlap = dlg.sp_overlap.value()
        stale = [op for op in ops if getattr(op['group'], 'mesh', None) is not op['mesh']
                 or (op['face'] is not None
                     and all(op['face'] is not f for f in _items(getattr(op['mesh'], 'faces', None))))]
        if stale:
            QMessageBox.information(dlg, PLUGIN_NAME, "The model has changed since Find. Click "
                                    "'Find openings' again.")
            return
        keep_v = {k: v[k] for k in PRESET_KEYS if k in v}
        walls = []                                   # [(group, mesh, record)]
        for op in ops:
            for w in walls:
                if w[0] is op['group']:
                    rec = w[2]
                    break
            else:
                old = wall_record(op['group'])
                rec = json.loads(json.dumps(old)) if old else {
                    'orig': [[list(map(list, pts)), [list(map(list, h)) for h in hls]]
                             for pts, hls in _faces_of_mesh(op['mesh'])],
                    'items': []}
                walls.append((op['group'], op['mesh'], rec))
            rec['items'] = [w_ for w_ in rec['items'] if not (w_['fi'] == op['fi'] and w_['k'] == op['k'])]
            if fill:
                if _fill_opening(rec, op):
                    filled += 1
                else:
                    cant_fill.append(op['name'])
            if not take_out:
                O, U, V_, N = op['frame']
                rec['items'].append({
                    'kind': WB_KIND, 'fi': op['fi'], 'k': op['k'], 'name': op['name'],
                    'poly': [list(p) for p in op['poly']], 'depth': op['depth'],
                    'frame': [list(O), list(U), list(V_), list(N)],
                    'values': dict(keep_v), 'overlap': overlap})
        swaps, problems, loose = [], [], []
        for g, mesh, rec in walls:
            plain, _bad = _mesh_from([(pts, hls) for pts, hls in rec['orig'] if len(pts) >= 3])
            sols, kept = [], []
            for w_ in rec['items']:
                try:
                    got = item_solids(w_, WB_KIND)
                    vals = dict(DEFAULTS)
                    vals.update(w_.get('values') or {})
                    for so in got:
                        so.paint = paint_name(so, w_.get('kind', 'window'), vals)
                        so.paint_kind = w_.get('kind', 'window')
                    sols += got
                    kept.append(w_)
                except ValueError as e:
                    problems.append("%s: %s" % (w_.get('name', 'an opening'), e))
                    if w_.get('kind') != WB_KIND:
                        kept.append(w_)          # not ours: never lose it
            rec['items'] = kept
            if sols:
                new, ok, why = join_into_wall(plain, sols)
                if not ok:
                    loose.append("%s (%s)" % (getattr(g, 'name', 'a wall'), why))
                new_rec = rec
            else:
                new, new_rec = plain, None           # nothing left in it: the plain wall again
            try:
                want = getattr(dlg, 'cb_colour', None) is None or dlg.cb_colour.isChecked()
                paint_wall(getattr(dlg.viewport, 'scene', None), new, mesh, sols if want else [])
            except Exception as e:
                print("%s: couldn't colour %s: %s" % (PLUGIN_NAME, getattr(g, 'name', 'a wall'), e))
            old_rec = wall_record(g)
            swaps.append((g, mesh, new, json.loads(json.dumps(old_rec)) if old_rec else None, new_rec))
        try:
            dlg.viewport.history.execute(wall_swap_command(swaps))
        except Exception as e:
            QMessageBox.warning(dlg, PLUGIN_NAME, "Could not change the walls:\n%s" % e)
            return
        try:
            dlg.viewport.notify_scene_changed()
        except Exception:
            pass
        pl = lambda n: "" if n == 1 else "s"
        if take_out:
            nb = sum(1 for op in ops if op.get('built'))
            lines = ["%d taken out." % nb] if nb else []
            if fill:
                lines.append("%d opening%s filled in - the wall is solid there again." % (filled, pl(filled)))
                if cant_fill:
                    lines.append("Not filled (doorways cut up from the bottom of the wall): " +
                                 ", ".join(cant_fill))
        else:
            lines = ["%d %s%s built into %d wall section%s." % (len(ops), WB_WORDS['n'], pl(len(ops)),
                                                               len(swaps), pl(len(swaps)))]
        if loose:
            lines.append("Couldn't join into one solid, so they're in the wall's piece but "
                         "overlapping it (slicers join them when printing): " + "; ".join(loose))
        lines.append("Close the plugin whenever you like: Find picks these up again to change them. "
                     "To print: Scale Studio's Pieces page, 'Every group with faces', tick 'Lay each "
                     "piece flat'.")
        dlg.lst_open.clear()
        dlg.found = []
        dlg.lbl_found.setText("\n".join(lines))
        dlg.show_report(lines)
        if problems:
            QMessageBox.information(dlg, PLUGIN_NAME, "Some were skipped:\n" + "\n".join(problems))

    def add_to_scene(self, viewport, parts, remove=(), cuts=None):
        """Adds the groups and takes away the faces in `remove`, as one undo step."""
        stats = {'faces': 0, 'errors': 0, 'err': None, 'removed': 0, 'joined': 0, 'join_err': None,
                 'cut': 0, 'cut_err': None, 'small_cut': 0, 'join_fails': []}
        cut = self._cut
        scene0 = viewport.scene
        targets = []
        for f in remove:
            m = mesh_of_face(scene0, f)
            if m is not None:
                targets.append((f, m))
        meshes = []
        for m in [getattr(scene0, 'mesh', None)] + [m for _, m in targets]:
            if m is not None and all(m is not x for x in meshes):
                meshes.append(m)
        tol = 1e-4 * 0.001

        join = self._join

        def make_mesh(solids):
            from core.mesh import Mesh
            mesh = Mesh()
            for so in solids:
                verts = {}

                def vx(p):
                    k = (round(p[0] / tol), round(p[1] / tol), round(p[2] / tol))
                    if k not in verts:
                        verts[k] = VertexWrapper(*p)
                    return verts[k]

                for pts in so.faces:
                    try:
                        mesh.add_face([vx(p) for p in pts])
                        stats['faces'] += 1
                    except Exception as e:
                        stats['errors'] += 1
                        stats['err'] = e
            return mesh

        def describe_piece(so):
            pts = [p for f in so.faces for p in f]
            span = [max(p[k] for p in pts) - min(p[k] for p in pts) for k in range(3)]
            dims = sorted(span, reverse=True)
            return "%s, %d faces, %.0f x %.0f x %.1f mm" % (getattr(so, 'kind', 'part'), len(so.faces),
                                                         dims[0] / SCALE, dims[1] / SCALE, dims[2] / SCALE)

        def is_closed(solid_tools, g):
            """IngeTrazo's own test of one piece: True, False, or None if it can't say."""
            for arg in (g.mesh, g):
                try:
                    r = solid_tools.solid_report(arg)
                    return bool(r[0] if isinstance(r, (tuple, list)) else r)
                except Exception:
                    continue
            return None

        def joined(name, solids):
            """One solid from many, with IngeTrazo's Solid Tools Union (manifold3d).
            Returns (result groups, leftover solids that couldn't be joined), or None."""
            if not join or len(solids) < 2:
                return None
            try:
                from core import solids as solid_tools
                from core.group import Group
            except Exception as e:
                stats['join_fails'].append((name, "IngeTrazo's Solid Tools aren't available (%s)" % e))
                return None
            pieces = []
            for so in solids:
                g = Group(name)
                g.mesh = make_mesh([so])
                pieces.append((g, so))
            try:
                _removed, created = solid_tools.run(solid_tools.UNION, [g for g, _ in pieces])
                left = []
            except Exception as e:
                # find the pieces IngeTrazo doesn't count as closed, and join the rest
                bad = [(g, so) for g, so in pieces if is_closed(solid_tools, g) is False]
                good = [g for g, so in pieces if all(g is not b for b, _ in bad)]
                if not bad:
                    stats['join_fails'].append((name, "%s (all %d pieces pass IngeTrazo's own solid "
                                                      "check)" % (e, len(pieces))))
                    return None
                kinds = {}
                for _, so in bad:
                    kinds.setdefault(getattr(so, 'kind', 'part'), []).append(so)
                text = "; ".join("%d x %s" % (len(v), describe_piece(v[0])) for v in kinds.values())
                stats['join_fails'].append((name, "%d of %d pieces aren't closed solids to IngeTrazo: %s"
                                            % (len(bad), len(pieces), text)))
                if len(good) < 2:
                    return None
                try:
                    _removed, created = solid_tools.run(solid_tools.UNION, good)
                except Exception as e2:
                    stats['join_fails'].append((name, "the rest still wouldn't join: %s" % e2))
                    return None
                left = [so for _, so in bad]
            created = [g for g in (created or []) if g is not None]
            if not created:
                return None
            for g in created:
                for attr in ('name', 'label'):      # so the joined window keeps its name
                    try:
                        setattr(g, attr, name)
                    except Exception:
                        pass
            stats['joined'] += 1
            return created, left

        def mutate(scene):
            from core.group import Group
            for name, solids in parts:
                res = joined(name, solids)
                groups = None
                if res is not None:
                    groups, left = res
                    if left:
                        g = Group(name + " - pieces not joined")
                        g.mesh = make_mesh(left)
                        groups = groups + [g]
                if groups is None:
                    before = stats['faces']
                    mesh = make_mesh(solids)
                    if stats['faces'] == before:
                        raise RuntimeError("No faces could be created (%s)." % stats['err'])
                    g = Group(name)
                    g.mesh = mesh
                    groups = [g]
                for g in groups:
                    try:
                        # each part its own colour (frame, sill, head...) before Layers & Colours
                        # colours whatever is left by the window's name
                        paint_wall(scene, g.mesh, None, solids)
                    except Exception as e:
                        print("%s: couldn't colour %s: %s" % (PLUGIN_NAME, name, e))
                    _ed3d_organise(scene, g)
                    if hasattr(scene, 'add_group'):
                        scene.add_group(g)
                    elif hasattr(scene, 'groups') and isinstance(scene.groups, list):
                        scene.groups.append(g)
                    else:
                        raise RuntimeError("Could not add the window to the scene.")
            for f, m in targets:
                info = through_info(m, f) if (cut and cuts and f in cuts) else None
                host = None
                if info is not None:
                    try:
                        host = find_host(m, f, info)
                    except Exception:
                        host = None
                remove_face(scene, m, f)
                stats['removed'] += 1
                if info is not None:
                    try:
                        if not cut_through(scene, m, info, host, cuts.get(f)):
                            stats['small_cut'] += 1
                        stats['cut'] += 1
                    except Exception as e:
                        stats['cut_err'] = e

        hist = viewport.history
        try:
            hist.execute(make_command(mutate, meshes) if targets else SnapshotImport(mutate))
        except Exception as e:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not add the window:\n%s" % e)
            return False
        err = getattr(hist, 'last_error', None)
        if err and stats['faces'] == 0:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not add the window:\n%s" % err)
            return False
        try:
            viewport.notify_scene_changed()
        except Exception:
            pass
        rep = ["Added %d group(s), %d faces. Join into one solid: %s. Cut through: %s. "
               "Faces replaced: %d." % (len(parts), stats['faces'], "on" if join else "off",
                                         "on" if cut else "off", stats['removed'])]
        if stats['cut']:
            rep.append("Cut %d opening(s) through the wall." % stats['cut'])
        if stats['small_cut']:
            rep.append("%d opening(s) were cut to the window only: the wall face round them "
                       "couldn't be found, so the sill and head sit on the wall." % stats['small_cut'])
        if stats['cut_err'] is not None:
            rep.append("Could not cut an opening through the wall: %s" % stats['cut_err'])
        if stats['removed'] and not stats['cut'] and cut and stats['cut_err'] is None:
            rep.append("No back of the wall was found behind the face, so the face was just "
                       "replaced (nothing cut through).")
        if stats['joined']:
            rep.append("Joined into one solid: %d." % stats['joined'])
        elif join and not stats['join_fails']:
            rep.append("Nothing needed joining.")
        for name, err in stats['join_fails']:
            rep.append("NOT joined (added as separate pieces): %s - %s" % (name, err))
        if stats['errors']:
            rep.append("%d faces could not be made (%s)." % (stats['errors'], stats['err']))
        self.last_report = rep
        for line in rep:
            print("%s: %s" % (PLUGIN_NAME, line))
        return True
