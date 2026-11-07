# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Period Doors for IngeTrazo
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
3D Period Doors - old-fashioned doors for IngeTrazo
Select any flat face (a shape drawn on a wall, or a face with openings in it) and the door
is made to fit its outline: square, round-topped, segmental or pointed.

Panelled doors (raised and fielded or flat panels, 4-panel, 6-panel...), half-glazed doors,
ledged and braced, framed ledged and braced, stable doors, double doors and sliding goods
doors. Fanlights over the door, a stone or brick doorstep, stone or brick heads and arches,
keystones, strap hinges and a door knob.

Like 3D Period Windows it cuts right through a solid wall, prints flat (everything down to
the back), and can join it all into one clean solid. Ctrl+Alt+D.
"""

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

PLUGIN_NAME = "3D Period Doors"
VERSION = "2"             # shown in the window title, so you can tell which file is loaded


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

PRESET_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Doors")
SCALE = 0.001            # sizes are in mm; IngeTrazo stores geometry in metres

STYLES = [("panel", "Panelled"), ("glazed", "Half-glazed (panels below)"),
          ("ledged", "Ledged and braced (boarded)"), ("framed", "Framed, ledged and braced"),
          ("stable", "Stable door (split top and bottom)"), ("sliding", "Sliding goods door")]
TOPS = [("face", "Follow the face shape"), ("flat", "Square top"),
        ("semi", "Round top (semicircle)"), ("segment", "Segmental (shallow arch)"),
        ("gothic", "Pointed (gothic)")]
PANELS = [("raised", "Raised and fielded"), ("flat", "Flat (sunk) panels")]
HINGES = [("left", "Hinged on the left"), ("right", "Hinged on the right")]
FANLIGHTS = [("none", "No fanlight"), ("plain", "Plain glass"), ("bars", "Upright glazing bars"),
             ("fan", "Fan (bars spreading out)")]
ARCH_BARS = [("grid", "Grid carries on into the arch"), ("fan", "Fan bars in the arch"),
             ("plain", "Plain glass in the arch")]
STEPS = [("stone", "Stone doorstep"), ("brick", "Brick-on-edge step"), ("none", "No step")]
HEADS = [("stone", "Stone lintel / stone arch"), ("brick", "Brick soldier course / brick arch"),
         ("none", "No head")]

DEFAULTS = {
    'style': 'panel', 'top': 'face', 'rise': 150.0, 'flip': False, 'flat': True, 'bars_back': True,
    'remove_face': True, 'join': True, 'cut': True, 'lift': 0.01,
    'leaves': 1, 'hinge': 'left', 'open': False, 'open_angle': 60.0,
    'frame_w': 75.0, 'frame_d': 110.0, 'leaf_t': 45.0, 'leaf_set': 20.0,
    'stile_w': 110.0, 'top_rail': 110.0, 'bottom_rail': 220.0, 'lock_w': 200.0, 'lock_y': 1000.0,
    'muntin_w': 100.0,
    'cols': 2, 'rows': 1, 'cols_b': 2, 'rows_b': 1,
    'panel': 'raised', 'panel_d': 12.0, 'bevel': 40.0,
    'bar_w': 20.0, 'bar_d': 25.0, 'glass': False, 'glass_t': 4.0, 'arch_bars': 'grid',
    'board_w': 125.0, 'board_gap': 8.0, 'groove_d': 6.0, 'board_set': 15.0,
    'ledges': True, 'ledge_h': 150.0, 'ledge_t': 25.0, 'braces': True, 'brace_w': 125.0,
    'straps': False, 'strap_w': 45.0, 'strap_t': 8.0,
    'knob': True, 'knob_d': 60.0, 'knob_p': 55.0,
    'fanlight': 'none', 'fan_h': 400.0, 'transom_w': 75.0, 'fan_cols': 3,
    'slide_over': 100.0, 'rail_h': 60.0,
    'step': 'stone', 'step_h': 150.0, 'step_p': 250.0, 'horn': 100.0,
    'head': 'brick', 'head_h': 215.0, 'head_p': 10.0, 'bearing': 100.0,
    'keystone': False, 'key_w': 150.0, 'key_up': 40.0, 'key_p': 15.0,
    'brick_w': 102.5, 'brick_t': 65.0, 'joint': 10.0,
}
INT_KEYS = ('cols', 'rows', 'cols_b', 'rows_b', 'leaves', 'fan_cols')
CHOICE_KEYS = ('style', 'top', 'panel', 'hinge', 'fanlight', 'arch_bars', 'step', 'head')
BOOL_KEYS = ('flip', 'flat', 'bars_back', 'remove_face', 'join', 'cut', 'open', 'glass', 'ledges',
             'braces', 'straps', 'knob', 'keystone')
PRESET_KEYS = tuple(DEFAULTS)

BUILTIN_PRESETS = {
    "Victorian 4-panel": dict(style='panel', cols=2, rows=1, cols_b=2, rows_b=1, panel='raised',
                              fanlight='bars', fan_h=350.0, fan_cols=3, step='stone', head='stone'),
    "Georgian 6-panel, fanlight": dict(style='panel', top='semi', cols=2, rows=2, cols_b=2, rows_b=1,
                                       panel='raised', fanlight='fan', fan_cols=6, step='stone',
                                       head='brick', keystone=True),
    "Half-glazed, 4 panes": dict(style='glazed', cols=2, rows=2, cols_b=2, rows_b=1, panel='flat',
                                 step='stone', head='brick'),
    "Ledged and braced (shed, platform)": dict(style='ledged', ledges=True, braces=True, straps=True,
                                               knob=True, step='none', head='brick'),
    "Framed, ledged and braced": dict(style='framed', ledges=True, braces=True, straps=True, knob=True,
                                      step='brick', head='brick'),
    "Stable door": dict(style='stable', ledges=True, braces=True, straps=True, knob=True,
                        step='stone', head='stone'),
    "Double doors - goods shed": dict(style='framed', top='segment', rise=200.0, leaves=2,
                                      ledges=True, braces=True, straps=True, knob=False,
                                      step='none', head='brick', keystone=False),
    "Sliding goods door": dict(style='sliding', ledges=True, braces=True, knob=False,
                               slide_over=120.0, step='none', head='brick'),
    "1:80 print - 4-panel": dict(style='panel', cols=2, rows=1, cols_b=2, rows_b=1, panel='raised',
                                 frame_w=64.0, frame_d=80.0, leaf_t=40.0, leaf_set=16.0, stile_w=96.0,
                                 top_rail=96.0, bottom_rail=192.0, lock_w=160.0, muntin_w=80.0,
                                 panel_d=16.0, bevel=32.0, knob_d=64.0, knob_p=48.0,
                                 bar_w=32.0, bar_d=32.0, step='stone', head='stone'),
    "1:80 print - ledged and braced": dict(style='ledged', frame_w=64.0, frame_d=80.0, leaf_t=40.0,
                                           leaf_set=16.0, board_w=150.0, board_gap=32.0, groove_d=16.0,
                                           ledge_h=160.0, ledge_t=24.0, brace_w=128.0, straps=True,
                                           strap_w=48.0, strap_t=16.0, knob_d=64.0, knob_p=48.0,
                                           step='none', head='brick'),
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
# Door outline shapes
# ---------------------------------------------------------------------------
def arc_pts(cx, cy, R, a0, a1):
    n = max(4, int(math.ceil(abs(a1 - a0) / (math.pi / 24))))
    return [(cx + R * math.cos(a0 + (a1 - a0) * i / n), cy + R * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def make_shape(kind, x0, x1, y0, y1, rise=0.0):
    """A door outline. Arcs are (cx, cy, R, from angle, to angle), running from the right
    springing over the top to the left. Raises ValueError if it doesn't fit."""
    w, h = x1 - x0, y1 - y0
    cx = (x0 + x1) / 2
    sh = {'kind': kind, 'arcs': [], 'ys': None, 'cx': cx, 'flat_bottom': True}
    if kind == 'flat':
        sh['poly'] = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    elif kind == 'semi':
        ys = y1 - w / 2
        if ys < y0 + 0.05 * h:
            raise ValueError("This door isn't tall enough for a semicircular top "
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
            raise ValueError("This door isn't tall enough for a pointed top "
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
    """Works out the door outline for an opening. With 'face' the face's own outline
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
    cands = ['flat', 'semi', 'gothic']
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


def fit_door(poly, v):
    """The outline of the whole door. With a fanlight, the face you drew is the door
    itself and the fanlight is an extra piece on top of it (square, or round, segmental or
    pointed if that top shape is chosen). If you drew the arch yourself (a round-topped
    face with 'Follow the face shape'), the fanlight fills that arch as before."""
    if v['fanlight'] == 'none' or v['style'] == 'sliding':
        return fit_shape(poly, v['top'], v['rise'])
    drawn = fit_shape(poly, 'face', v['rise'])
    if drawn['kind'] not in ('flat',):
        if v['top'] == 'face' or drawn['kind'] in ('poly', 'circle'):
            return drawn
    x0, x1, y0, y1 = drawn['box']
    w = x1 - x0
    fw = v['frame_w']
    tw = max(5.0, v['transom_w'])
    kind = 'flat' if v['top'] == 'face' else v['top']
    yt = y1 - fw + tw / 2              # transom where the door's frame head would be
    r = v['rise']
    if kind == 'semi':
        top = yt + w / 2
    elif kind == 'segment':
        r = max(1.0, min(v['rise'], w / 2))
        top = yt + r
    elif kind == 'gothic':
        top = yt + w * math.sin(math.pi / 3)
    else:
        kind = 'flat'
        top = y1 + tw + max(50.0, v['fan_h'])
    sh = make_shape(kind, x0, x1, y0, top, r)
    sh['fan_yt'] = yt
    sh['door_top'] = y1
    return sh


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
# Door parts
# ---------------------------------------------------------------------------
def frustum(lo, hi, z0, z1, kind="raised panel"):
    """A solid from polygon lo at z0 up to polygon hi (same number of points) at z1."""
    n = len(lo)
    if n < 3 or len(hi) != n or z1 - z0 < 1e-9:
        return None
    s = Solid()
    s.kind = kind
    s.add([(x, y, z1) for x, y in hi])
    s.add([(x, y, z0) for x, y in reversed(lo)])
    for i in range(n):
        j = (i + 1) % n
        s.add([(lo[i][0], lo[i][1], z0), (lo[j][0], lo[j][1], z0),
               (hi[j][0], hi[j][1], z1), (hi[i][0], hi[i][1], z1)])
    return s.fix()


def _bottom_index(P):
    """The index i of the bottom edge P[i] -> P[i+1] (running left to right), or None."""
    _, _, y0, y1 = bbox(P)
    tol = 1e-3 * (1.0 + y1 - y0)
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        if abs(a[1] - y0) < tol and abs(b[1] - y0) < tol and b[0] > a[0]:
            return i
    return None


def open_frame(P, w, z0, z1):
    """A door frame: the sides and top of P, w wide, with no bottom. Returns (solid, inside)."""
    P = clean(P)
    i = _bottom_index(P)
    if i is None:
        O = offset_poly(P, w)
        return ring(P, O, z0, z1), clean(O)
    O = offset_poly(P, edge_widths(P, w, bottom=0.0))
    n = len(P)
    order = [(i + 1 + k) % n for k in range(n)]        # bottom right, round the top, bottom left
    so = band([O[k] for k in order], [P[k] for k in order], z0, z1)
    so.kind = "door frame (%d steps)" % n
    return so, clean(O)


def fan_bars(F, n, bw, cx, yb, z0, z1):
    """n - 1 bars spreading out from (cx, yb) across the region F."""
    out = []
    x0, x1, y0, y1 = bbox(F)
    L = 2.0 * (x1 - x0 + y1 - y0)
    for i in range(1, max(2, n)):
        a = math.pi * i / max(2, n)
        dx, dy = math.cos(a), math.sin(a)
        nx, ny = -dy * bw / 2, dx * bw / 2
        sp = clean([(cx - nx, yb - ny), (cx + dx * L - nx, yb + dy * L - ny),
                    (cx + dx * L + nx, yb + dy * L + ny), (cx + nx, yb + ny)])
        if sp:
            pc = clip_convex(F, sp)
            if pc:
                out.append(prism(pc, z0, z1))
    return [s for s in out if s]


def knob(xc, yc, d, z0, z1):
    r = d / 2.0
    pts = [(xc + r * math.cos(2 * math.pi * k / 12), yc + r * math.sin(2 * math.pi * k / 12)) for k in range(12)]
    s = prism(pts, z0, z1)
    if s:
        s.kind = "door knob"
    return s


def _inside_pt(p, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ay > p[1]) != (by > p[1]):
            if p[0] < ax + (p[1] - ay) * (bx - ax) / (by - ay):
                inside = not inside
    return inside


def panel_leaf(R, v, sh, zb, zf, glazed, ov):
    """A panelled (or half-glazed) leaf over polygon R, from zb (back) to zf (front).
    Returns (solids, glass, info)."""
    sw, tr, br = v['stile_w'], v['top_rail'], v['bottom_rail']
    G = clean(offset_poly(R, edge_widths(R, sw, br, tr)))
    if G is None or area2(G) <= 0:
        raise ValueError("The panels don't fit: the stiles and rails are too wide for this door.")
    Gg = clean(offset_poly(G, -ov)) or G          # rails and panels run into the stiles
    pd = max(0.5, min(v['panel_d'], (zf - zb) * 0.6))
    zp = zf - pd                                   # the face of the panels
    out, glass = [ring(R, G, zb, zf)], []
    gx0, gx1, gy0, gy1 = bbox(G)
    rx0, rx1, ry0, ry1 = bbox(R)
    mw, lw = v['muntin_w'], v['lock_w']
    yl = ry0 + v['lock_y']
    if not (gy0 + lw < yl < gy1 - lw):
        yl = None
    if yl is not None:
        pc = clip_rect(Gg, gx0 - ov - 1, gx1 + ov + 1, yl - lw / 2, yl + lw / 2)
        if pc:
            out.append(prism(pc, zb, zf))
        sections = [(gy0, yl - lw / 2, int(v['rows_b']), int(v['cols_b']), False),
                    (yl + lw / 2, gy1, int(v['rows']), int(v['cols']), glazed)]
    else:
        sections = [(gy0, gy1, int(v['rows']), int(v['cols']), glazed)]
    flat = v.get('flat', True)
    base = v.get('_base', zb)
    for ya, yb, nr, nc, is_glass in sections:
        nr, nc = max(1, nr), max(1, nc)
        if yb - ya < 1.0:
            continue
        top = yb + 1 if yb >= gy1 - 1e-6 else yb
        S = clip_rect(G, gx0 - 1, gx1 + 1, ya, top)
        if not S:
            continue
        if is_glass:
            # glazing bars over the glass, like a window sash
            embed = min(v['bar_w'] * 0.4, sw * 0.4)
            if flat and v.get('bars_back', True):
                z0, z1 = base, base + min(v['bar_d'], zf - base)
            else:
                zm = (zb + zf) / 2
                bd = min(v['bar_d'], zf - zb)
                z0, z1 = (base if flat else zm - bd / 2), zm + bd / 2
            Sg = clean(offset_poly(S, -embed)) or S
            out += bars(S, nc, nr, v['arch_bars'], sh, v['bar_w'], z0, z1, embed)
            # the rail under the glass runs into it a little
            if v['glass']:
                t = min(v['glass_t'], zf - zb)
                gz0, gz1 = (base, base + t) if flat else ((zb + zf) / 2 - t / 2, (zb + zf) / 2 + t / 2)
                g = prism(offset_poly(S, -min(5.0, sw * 0.3)), gz0, gz1)
                if g:
                    glass.append(g)
            continue
        # a sunk panel all over the section, with muntins and rails standing up round it
        plate = clip_rect(Gg, gx0 - ov - 1, gx1 + ov + 1, ya - ov, top + (ov if top < gy1 else 0))
        if plate:
            out.append(prism(plate, zb, zp))
        xs = [gx0 + (gx1 - gx0) * i / nc for i in range(1, nc)]
        ys = [ya + (yb - ya) * j / nr for j in range(1, nr)]
        for xc in xs:
            pc = clip_rect(Gg, xc - mw / 2, xc + mw / 2, ya - ov, top + ov)
            if pc:
                out.append(prism(pc, zb, zf))
        for yc in ys:
            pc = clip_rect(Gg, gx0 - ov - 1, gx1 + ov + 1, yc - mw / 2, yc + mw / 2)
            if pc:
                out.append(prism(pc, zb, zf))
        if v['panel'] == 'raised':
            xe = [gx0] + xs + [gx1]
            ye = [ya] + ys + [top]
            for i in range(nc):
                for j in range(nr):
                    cell = clip_rect(G, xe[i] + (mw / 2 if i > 0 else 0.0), xe[i + 1] - (mw / 2 if i < nc - 1 else 0.0),
                                     ye[j] + (mw / 2 if j > 0 else 0.0), ye[j + 1] - (mw / 2 if j < nr - 1 else 0.0))
                    cell = clean(cell) if cell else None
                    if not cell:
                        continue
                    c0, c1, d0, d1 = bbox(cell)
                    b = min(v['bevel'], 0.3 * (c1 - c0), 0.3 * (d1 - d0))
                    if b < 0.5:
                        continue
                    # a pointed or narrow panel: shrink the bevel until the raised middle fits
                    hi = None
                    for _ in range(4):
                        h_ = offset_poly(cell, b)
                        if area2(h_) > 0 and all(_inside_pt(q, cell) for q in h_):
                            hi = h_
                            break
                        b *= 0.5
                    if hi is None:
                        continue
                    f = frustum(cell, hi, zp - ov, zp + min(pd * 0.75, max(0.5, pd - 0.5)))
                    if f and f.volume() > 0:
                        out.append(f)
    return [s for s in out if s], glass, {'yl': yl, 'G': bbox(G)}


def boarded_leaf(R, v, zb, zf, style, hinge_right, ov):
    """A boarded leaf (ledged, framed or stable; sliding uses framed). Returns (solids, info)."""
    out = []
    framed = style in ('framed', 'sliding')
    rx0, rx1, ry0, ry1 = bbox(R)
    region = R
    zfb = zf
    if framed:
        sw, tr = v['stile_w'], v['top_rail']
        bw_ = v['bottom_rail'] if style == 'sliding' else 0.0
        if style == 'sliding':
            G = clean(offset_poly(R, edge_widths(R, sw, bw_, tr)))
            if G is None:
                raise ValueError("The frame of the door is too wide for it.")
            out.append(ring(R, G, zb, zf))
        else:
            fr, G = open_frame(R, sw, zb, zf)
            fr.kind = "door stiles and top rail"
            if G is None:
                raise ValueError("The frame of the door is too wide for it.")
            # the top rail is wider than the stiles
            if tr > sw:
                gx0, gx1, gy0, gy1 = bbox(G)
                pc = clip_rect(clean(offset_poly(G, -ov)) or G, gx0 - ov - 1, gx1 + ov + 1, gy1 - (tr - sw), gy1 + 1)
                if pc:
                    out.append(prism(pc, zb, zf))
                G = clip_rect(G, gx0 - 1, gx1 + 1, gy0 - 1, gy1 - (tr - sw)) or G
            out.append(fr)
        region = clean(G)
        zfb = zf - max(0.0, min(v['board_set'], (zf - zb) * 0.5))
    groove = max(0.2, min(v['groove_d'], (zfb - zb) * 0.5))
    Rg = clean(offset_poly(region, -ov)) if framed else region
    out.append(prism(Rg or region, zb, zfb - groove))
    x0, x1, y0, y1 = bbox(region)
    W = x1 - x0
    n = max(1, int(round(W / max(10.0, v['board_w']))))
    bw = W / n
    g = max(0.2, v['board_gap'])
    split = None
    if style == 'stable':
        split = y0 + min(max(v['lock_y'], 0.2 * (y1 - y0)), 0.8 * (y1 - y0))
    bands = [(y0 - 1, y1 + 1)] if split is None else [(y0 - 1, split - g / 2), (split + g / 2, y1 + 1)]
    for k in range(n):
        a = x0 + k * bw + (g / 2 if k > 0 else 0.0)
        b = x0 + (k + 1) * bw - (g / 2 if k < n - 1 else 0.0)
        for ya, yb in bands:
            pc = clip_rect(region, a, b, ya, yb)
            if pc:
                s = prism(pc, zfb - groove - ov, zfb)
                if s:
                    s.kind = "board"
                    out.append(s)
    info = {'zfb': zfb, 'region': bbox(region), 'boards': (x0, bw), 'split': split, 'ledges': []}
    # ledges, braces and strap hinges on the front
    lt = max(0.5, v['ledge_t'])
    lh = max(5.0, v['ledge_h'])
    H = y1 - y0
    if style == 'stable' and split is not None:
        fr = [0.1, (split - y0) / H - 0.09, (split - y0) / H + 0.09, 0.9]
    elif style == 'sliding':
        fr = [0.5]
    else:
        fr = [0.1, 0.5, 0.88]
    ys = [y0 + f * H for f in fr]
    inset = min(25.0, 0.05 * W) if not framed else -ov
    xa, xb = x0 + inset, x1 - inset
    zl0, zl1 = zfb - ov, zfb + lt
    if v['ledges']:
        for yc in ys:
            pc = clip_rect(region, xa, xb, yc - lh / 2, yc + lh / 2)
            if pc:
                s = prism(pc, zl0, zl1)
                if s:
                    s.kind = "ledge"
                    out.append(s)
        info['ledges'] = ys
        if v['braces']:
            pairs = list(zip(ys[:-1], ys[1:]))
            if style == 'stable' and len(ys) == 4:
                pairs = [(ys[0], ys[1]), (ys[2], ys[3])]
            if style == 'sliding':
                pairs = [(y0, ys[0]), (ys[0], y1)]
            bw2 = max(5.0, v['brace_w'])
            for ya, yb in pairs:
                # from low on the hinge side up to high on the latch side
                xl, xr = xa + bw2 * 0.6, xb - bw2 * 0.6
                p1 = (xr, ya) if hinge_right else (xl, ya)
                p2 = (xl, yb) if hinge_right else (xr, yb)
                dx, dy = p2[0] - p1[0], p2[1] - p1[1]
                L = math.hypot(dx, dy) or 1.0
                nx, ny = -dy / L * bw2 / 2, dx / L * bw2 / 2
                ex, ey = dx / L * bw2, dy / L * bw2          # run past the ends, under the ledges
                quad = clean([(p1[0] - nx - ex, p1[1] - ny - ey), (p2[0] - nx + ex, p2[1] - ny + ey),
                              (p2[0] + nx + ex, p2[1] + ny + ey), (p1[0] + nx - ex, p1[1] + ny - ey)])
                if not quad:
                    continue
                lo_, hi_ = (ya if style != 'sliding' or ya > y0 else y0 - 1), (yb if style != 'sliding' or yb < y1 else y1 + 1)
                box = clip_rect(region, xa, xb, lo_, hi_)
                if box:
                    pc = clip_convex(box, quad)
                    if pc:
                        s = prism(pc, zl0, zl1)
                        if s:
                            s.kind = "brace"
                            out.append(s)
    if v['straps'] and style != 'sliding':
        sw_ = max(5.0, v['strap_w'])
        st = max(0.5, v['strap_t'])
        zs0 = (zl1 if v['ledges'] else zfb) - ov
        Ls = 0.62 * W
        for yc in (ys if v['ledges'] else [y0 + 0.12 * H, y0 + 0.88 * H]):
            if hinge_right:
                xs0, sgn = x1 + ov, -1.0
            else:
                xs0, sgn = x0 - ov, 1.0
            tip = xs0 + sgn * Ls
            pts = [(xs0, yc - sw_ / 2), (tip - sgn * sw_ * 0.3, yc - sw_ * 0.22),
                   (tip, yc), (tip - sgn * sw_ * 0.3, yc + sw_ * 0.22), (xs0, yc + sw_ / 2)]
            s = prism(clean(pts) or pts, zs0, zs0 + ov + st)
            if s:
                s.kind = "strap hinge"
                out.append(s)
    return [s for s in out if s], info


def build_step(sh, v, fd):
    """A doorstep in the bottom of the opening, standing out from the wall."""
    x0, x1, y0, _ = sh['box']
    F = fd + v['step_p']
    xa, xb = x0 - v['horn'], x1 + v['horn']
    h = v['step_h'] if v['step'] == 'stone' else v['brick_w']
    b = v.get('_base_sh', v.get('_base', 0.0))
    sec = [(b, y0), (F, y0), (F, y0 + h), (b, y0 + h)]
    if v['step'] == 'stone':
        return [along_x(sec, xa, xb)]
    out = []
    J = v['joint']
    for a, c in _soldiers(xa, xb, v['brick_t'] + J, J):
        out.append(along_x(sec, a, c))
    k = 3.0
    mort = [(b, y0 + 1.0), (F - k, y0 + 1.0), (F - k, y0 + h - k), (b, y0 + h - k)]
    out.append(_mortar(along_x(mort, xa + 1.0, xb - 1.0)))
    return out


def build_door(sh, v):
    """Returns {'door': [...], 'glass': [...], 'step': [...], 'head': [...], 'info': {...}} in local mm."""
    P = sh['poly']
    x0, x1, y0, y1 = sh['box']
    style = v['style']
    fw = v['frame_w']
    fd = max(v['frame_d'], 5.0)
    zf = fd
    base = v.get('_base', 0.0)
    ov = min(2.0, fw * 0.25)
    flat = v.get('flat', True)
    door, glass = [], []
    has_step = v['step'] != 'none' and sh.get('flat_bottom')
    hs = (v['step_h'] if v['step'] == 'stone' else v['brick_w']) if has_step else 0.0
    if hs >= y1 - y0 - 50:
        raise ValueError("The step is taller than the door opening.")
    info = {'fd': fd, 'hs': hs}

    if style == 'sliding':
        # in front of the wall: a framed, boarded door hanging from a rail over the opening
        over = max(0.0, v['slide_over'])
        # cut through the wall: the head is flush with the wall face; on a plain wall face it
        # stands 1 mm proud. The door hangs a hair in front of that.
        zh = 0.0 if v.get('_base_sh', base) < -0.5 else 1.0
        z0 = zh + max(0.01, v.get('lift', 0.01))
        z1 = z0 + max(5.0, v['leaf_t'])
        top = y1 + over
        yb = y0 + hs + (2.0 if hs > 0 else 0.0)        # clear of the step
        R = [(x0 - over, yb), (x1 + over, yb), (x1 + over, top), (x0 - over, top)]
        sols, binfo = boarded_leaf(R, v, z0, z1, 'sliding', False, ov)
        door += sols
        rh = max(10.0, v['rail_h'])
        W = x1 - x0 + 2 * over
        rail = prism([(x0 - over - 40, top + 30), (x1 + over + W, top + 30), (x1 + over + W, top + 30 + rh),
                      (x0 - over - 40, top + 30 + rh)], z0, z0 + min(40.0, z1 - z0))
        if rail:
            rail.kind = "door rail"
            door.append(rail)
        # two hangers from the rail down onto the door
        for xh in (x0 - over + W * 0.18, x1 + over - W * 0.18):
            hg = prism([(xh - 25, top - 40), (xh + 25, top - 40), (xh + 25, top + 30 + rh * 0.7),
                        (xh - 25, top + 30 + rh * 0.7)], z1 - ov, z1 + 10.0)
            if hg:
                hg.kind = "hanger"
                door.append(hg)
        info.update({'O': (x0, x1, y0 + hs, y1), 'L': bbox(R), 'leaf_z': (z0, z1), 'boarded': binfo,
                     'zf': z1})
        step = build_step(sh, v, 0.0) if has_step else []
        # the head stays flush with the wall, behind the door
        head = build_head(sh, dict(v, head_p=zh, key_p=0.0), 0.0) if v['head'] != 'none' else []
        return {'door': [s for s in door if s], 'glass': [], 'step': [s for s in step if s],
                'head': [s for s in head if s], 'info': info}

    P2 = clip_rect(P, x0 - 1, x1 + 1, y0 + hs, y1 + 1) if hs > 0 else P
    P2 = clean(P2)
    if P2 is None:
        raise ValueError("The door opening is too small.")
    fr, O = open_frame(P2, fw, base, zf)
    if O is None or area2(O) <= 0:
        raise ValueError("The frame width is too big for this opening.")
    door.append(fr)
    Og = clean(offset_poly(O, -ov)) or O
    ox0, ox1, oy0, oy1 = bbox(O)
    info['O'] = (ox0, ox1, oy0, oy1)
    # fanlight over a transom
    yt = None
    if v['fanlight'] != 'none':
        tw = max(5.0, v['transom_w'])
        if sh.get('fan_yt') is not None:
            yt = sh['fan_yt']                  # the fanlight sits on top of the door
        elif sh.get('ys') is not None and oy0 + 400 < sh['ys'] < oy1:
            yt = sh['ys']
        else:
            yt = oy1 - max(50.0, v['fan_h']) - tw / 2
        if yt - tw / 2 < oy0 + 400:
            raise ValueError("The fanlight leaves no room for the door: make it lower (Z).")
        pc = clip_rect(Og, ox0 - ov - 1, ox1 + ov + 1, yt - tw / 2, yt + tw / 2)
        if pc:
            door.append(prism(pc, base, zf))
        Fl = clip_rect(O, ox0 - 1, ox1 + 1, yt + tw / 2, oy1 + 1)
        if Fl:
            bw = v['bar_w']
            if flat and v.get('bars_back', True):
                bz0, bz1 = base, base + v['bar_d']
            else:
                zm = zf / 2
                bz0, bz1 = (base if flat else zm - v['bar_d'] / 2), zm + v['bar_d'] / 2
            Fe = clean(offset_poly(Fl, -min(bw * 0.4, 2 * ov))) or Fl
            if v['fanlight'] == 'bars':
                n = max(1, int(v['fan_cols']))
                fx0, fx1, fy0, fy1 = bbox(Fl)
                for i in range(1, n):
                    xc = fx0 + (fx1 - fx0) * i / n
                    pc = clip_rect(Fe, xc - bw / 2, xc + bw / 2, fy0 - 2 * ov, fy1 + 2 * ov)
                    if pc:
                        door.append(prism(pc, bz0, bz1))
            elif v['fanlight'] == 'fan':
                door += fan_bars(Fe, max(2, int(v['fan_cols'])), bw, (ox0 + ox1) / 2, yt + tw / 2, bz0, bz1)
            if v['glass']:
                t = min(v['glass_t'], zf - base)
                gz0, gz1 = (base, base + t) if flat else (zf / 2 - t / 2, zf / 2 + t / 2)
                g = prism(Fl, gz0, gz1)
                if g:
                    glass.append(g)
        L = clip_rect(O, ox0 - 1, ox1 + 1, oy0 - 1, yt - tw / 2)
    else:
        L = O
    L = clean(L)
    if L is None:
        raise ValueError("There's no room for the door leaf.")
    info['yt'] = yt
    info['L'] = bbox(L)
    # the leaf (or leaves), set back in the frame
    zl1 = zf - max(0.0, min(v['leaf_set'], zf * 0.6))
    zl0 = base if flat else zl1 - max(5.0, v['leaf_t'])
    info['leaf_z'] = (zl0, zl1)
    nl = 2 if int(v['leaves']) >= 2 else 1
    lx0, lx1, ly0, ly1 = bbox(L)
    gap = max(3.0, 2.5 * ov)
    spans = [(lx0 - ov, lx1 + ov)] if nl == 1 else [(lx0 - ov, (lx0 + lx1) / 2 - gap / 2),
                                                     ((lx0 + lx1) / 2 + gap / 2, lx1 + ov)]
    Lg = clean(offset_poly(L, -ov)) or L
    ang = math.radians(v['open_angle']) if (v['open'] and not flat) else 0.0
    for k, (a, b) in enumerate(spans):
        # the bottom runs into the step, but never below the opening
        R = clip_rect(Lg, a, b, ly0 - (ov if has_step else 0.0), ly1 + ov + 1)
        R = clean(R) if R else None
        if R is None:
            continue
        hinge_right = (v['hinge'] == 'right') if nl == 1 else (k == 1)
        if style in ('panel', 'glazed'):
            sols, gl, pinfo = panel_leaf(R, v, sh, zl0, zl1, style == 'glazed', ov)
            info['panel'] = pinfo
        else:
            sols, binfo = boarded_leaf(R, v, zl0, zl1, style, hinge_right, ov)
            gl = []
            info['boarded'] = binfo
        if v['knob'] and style != 'sliding':
            rx0, rx1, ry0, ry1 = bbox(R)
            yk = ry0 + min(v['lock_y'], 0.8 * (ry1 - ry0))
            xk = (rx0 + 75.0) if hinge_right else (rx1 - 75.0)
            if nl == 2:
                xk = (rx1 - 75.0) if k == 0 else (rx0 + 75.0)
            zk0 = zl1 - ov
            kn = knob(xk, yk, max(5.0, v['knob_d']), zk0, zl1 + max(1.0, v['knob_p']))
            if kn:
                sols.append(kn)
        if ang > 0:
            rx0, rx1, _, _ = bbox(R)
            f = swing_vertical(rx1 if hinge_right else rx0, zl1, ang, hinge_right)
            sols = [s.mapped(f) for s in sols]
            gl = [s.mapped(f) for s in gl]
        door += sols
        glass += gl

    step = build_step(sh, v, fd) if has_step else []
    head = build_head(sh, v, fd) if v['head'] != 'none' else []
    # small blocks bridging the frame to the step and head, so they overlap instead of
    # meeting face to face (these sit inside both, so they don't show)
    hb = v.get('_base_sh', base)
    if has_step:
        for xa, xb in ((x0 + ov, x0 + fw - ov), (x1 - fw + ov, x1 - ov)):
            door.append(prism([(xa, y0 + hs - ov), (xb, y0 + hs - ov), (xb, y0 + hs + ov), (xa, y0 + hs + ov)],
                              max(base, hb), zf - ov))
    if head:
        if sh['arcs']:
            Lh = _arch_len(sh)
            inner, outer = [], []
            n = max(4, int(Lh / 40.0))
            for i in range(n + 1):
                k, a = _arch_at(sh, ov + (Lh - 2 * ov) * i / n)
                cx, cy, R, _, _ = sh['arcs'][k]
                inner.append((cx + (R - ov) * math.cos(a), cy + (R - ov) * math.sin(a)))
                outer.append((cx + (R + ov) * math.cos(a), cy + (R + ov) * math.sin(a)))
            door.append(band(inner, outer, max(base, hb), zf - ov))
        else:
            door.append(prism([(x0 + ov, y1 - ov), (x1 - ov, y1 - ov), (x1 - ov, y1 + ov),
                               (x0 + ov, y1 + ov)], max(base, hb), zf - ov))
    info['zf'] = zf
    return {'door': [s for s in door if s], 'glass': [s for s in glass if s],
            'step': [s for s in step if s], 'head': [s for s in head if s], 'info': info}


def cut_outline(sh, v):
    """The shape to cut out of the wall: the door plus its step and head (and keystone),
    as one outline (local mm, counter-clockwise)."""
    P = sh['poly']
    if sh['kind'] == 'poly':
        return list(P)
    x0, x1, y0, y1 = sh['box']
    has_step = v['step'] != 'none' and sh.get('flat_bottom')
    has_head = v['head'] != 'none'
    hh = v['head_h']
    key = has_head and v['keystone']

    def extrados(s0, s1):
        n = max(2, int(math.ceil((s1 - s0) / 30.0)) + 1)
        return [_arch_pts(sh, s0 + (s1 - s0) * i / (n - 1), hh)[1] for i in range(n)]

    out = []
    h = (v['step_h'] if v['step'] == 'stone' else v['brick_w']) if has_step else 0.0
    if has_step:
        xa, xb = x0 - v['horn'], x1 + v['horn']
        out += [(xa, y0), (xb, y0), (xb, y0 + h), (x1, y0 + h)]
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
            xa_, xb_ = x0 - v['bearing'], x1 + v['bearing']
            top = y1 + hh
            out += [(x1, y1), (xb_, y1), (xb_, top)]
            if key and v['key_up'] > 0:
                cx = (x0 + x1) / 2
                kp = _flat_key_poly(cx, y1, hh, v)
                kb, kt = v['key_w'] / 2, kp[2][0] - cx
                xk = kb + (kt - kb) * hh / (hh + v['key_up'])
                out += [(cx + xk, top), kp[2], kp[3], (cx - xk, top)]
            out += [(xa_, top), (xa_, y1), (x0, y1)]
        else:
            out += [(x1, y1), (x0, y1)]
    if has_step:
        out += [(x0, y0 + h), (x0 - v['horn'], y0 + h)]
    return clean(out) or list(P)


# ---------------------------------------------------------------------------
# Heads: lintels, soldier courses and arches
# ---------------------------------------------------------------------------
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
        # a flat roof or floor: line the door up with the face's longest edge
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
        # test points a hair inside the outline, so a door standing on the bottom edge of
        # the wall (its corners right on the edge of the back face) still counts as on it
        c = v_mul(back[0], 0.0)
        for p in back:
            c = v_add(c, v_mul(p, 1.0 / len(back)))
        back = [v_add(p, v_mul(v_sub(c, p), 0.002)) for p in back]
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


# ---------------------------------------------------------------------------
# Cutting a door through the wall when the door reaches the edge of the wall face
# (a door standing on the bottom of the wall, or a head that goes above the top):
# every wall face the opening passes through has the opening taken out of it.
# ---------------------------------------------------------------------------
def _in_loop(q, loop):
    inside = False
    j = len(loop) - 1
    for i in range(len(loop)):
        (xi, yi), (xj, yj) = loop[i], loop[j]
        if (yi > q[1]) != (yj > q[1]) and q[0] < (xj - xi) * (q[1] - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _in_region(q, region):
    """region = (outer, [holes])."""
    outer, holes = region
    return _in_loop(q, outer) and not any(_in_loop(q, h) for h in holes)


def _split_edge(a, b, others, tol):
    """The edge a-b cut at the points where it meets the edges of `others`: [(p, q)...]."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    if L2 < tol * tol:
        return []
    ts = [0.0, 1.0]
    for op in others:
        m = len(op)
        for j in range(m):
            c, d = op[j], op[(j + 1) % m]
            ex, ey = d[0] - c[0], d[1] - c[1]
            # the other edge's ends lying on this edge
            for pt in (c, d):
                t = ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / L2
                if 0.0 < t < 1.0:
                    px, py = a[0] + dx * t, a[1] + dy * t
                    if (px - pt[0]) ** 2 + (py - pt[1]) ** 2 < tol * tol:
                        ts.append(t)
            den = dx * ey - dy * ex
            if abs(den) < 1e-12:
                continue
            t = ((c[0] - a[0]) * ey - (c[1] - a[1]) * ex) / den
            u = ((c[0] - a[0]) * dy - (c[1] - a[1]) * dx) / den
            if 0.0 < t < 1.0 and -1e-9 <= u <= 1.0 + 1e-9:
                ts.append(t)
    ts.sort()
    out = []
    for t0, t1 in zip(ts[:-1], ts[1:]):
        if (t1 - t0) * math.sqrt(L2) > tol:
            out.append(((a[0] + dx * t0, a[1] + dy * t0), (a[0] + dx * t1, a[1] + dy * t1)))
    return out


def _split_segments(loops, others, tol):
    """Every edge of `loops`, cut at the points where it meets the edges of `others`."""
    segs = []
    for lp in loops:
        n = len(lp)
        for i in range(n):
            segs += _split_edge(lp[i], lp[(i + 1) % n], others, tol)
    return segs


def poly_minus(region, cut, tol=1e-3):
    """2D: region (outer, [holes]) take away the polygon `cut`. Returns a list of
    (outer, [holes]) pieces, counter-clockwise outers and clockwise holes; [] if nothing
    is left. Copes with edges that lie along each other (a door on the bottom edge)."""
    outer, holes = region
    sub_loops = [outer] + list(holes)
    segs = _split_segments(sub_loops, [cut], tol) + _split_segments([cut], sub_loops, tol)
    eps = tol * 5.0

    def inside(q):
        return _in_region(q, region) and not _in_loop(q, cut)

    def key(p):
        return (round(p[0] / tol), round(p[1] / tol))

    pts = {}
    out_edges = {}
    seen = set()
    for a, b in segs:
        ka, kb = key(a), key(b)
        if ka == kb or (ka, kb) in seen or (kb, ka) in seen:
            continue
        seen.add((ka, kb))
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L * eps, dx / L * eps
        left, right = inside((mx + nx, my + ny)), inside((mx - nx, my - ny))
        if left == right:
            continue
        if right:
            a, b, ka, kb = b, a, kb, ka
        pts.setdefault(ka, a)
        pts.setdefault(kb, b)
        out_edges.setdefault(ka, []).append(kb)
    loops = []
    while any(out_edges.values()):
        start = next(k for k, v in out_edges.items() if v)
        loop, prev, cur = [start], None, start
        for _guard in range(100000):
            nxt = out_edges.get(cur) or []
            if not nxt:
                break
            if len(nxt) > 1 and prev is not None:
                # where two pieces touch at a corner: take the sharpest right turn
                pa, pc = pts[prev], pts[cur]
                ang_in = math.atan2(pc[1] - pa[1], pc[0] - pa[0])

                def turn(k):
                    q = pts[k]
                    a = math.atan2(q[1] - pc[1], q[0] - pc[0]) - ang_in
                    while a <= -math.pi:
                        a += 2 * math.pi
                    while a > math.pi:
                        a -= 2 * math.pi
                    return a
                k2 = min(nxt, key=turn)
            else:
                k2 = nxt[0]
            nxt.remove(k2)
            prev, cur = cur, k2
            if cur == start:
                break
            loop.append(cur)
        if len(loop) >= 3:
            loops.append([pts[k] for k in loop])
    outs, hls = [], []
    for lp in loops:
        c = clean(lp, tol * 0.1)
        if c is None:
            continue
        if area2(lp) > 0:
            outs.append(c)
        else:
            hls.append(c[::-1])                     # clockwise
    pieces = [(o, []) for o in outs]
    for h in hls:
        q = h[0]
        best = None
        for k, (o, _) in enumerate(pieces):
            # a point just inside the hole edge, outside the hole itself
            if _in_loop(((h[0][0] + h[1][0]) / 2, (h[0][1] + h[1][1]) / 2), o) or _in_loop(q, o):
                if best is None or abs(area2(o)) < abs(area2(pieces[best][0])):
                    best = k
        if best is not None:
            pieces[best][1].append(h)
    return pieces


def _region_area(region):
    outer, holes = region
    return abs(area2(outer)) - sum(abs(area2(h)) for h in holes)


def _line_ranges(cut, a, b, c, tol):
    """Where the line a*u + b*v = c crosses the polygon `cut` (counting an edge lying
    along the line): [(s0, s1)] along the line direction (-b, a), from the foot point."""
    L = math.hypot(a, b)
    a, b, c = a / L, b / L, c / L
    ranges = []
    for off in (tol * 4, -tol * 4):
        cc = c + off
        ss = []
        n = len(cut)
        for i in range(n):
            p, q = cut[i], cut[(i + 1) % n]
            fp, fq = a * p[0] + b * p[1] - cc, a * q[0] + b * q[1] - cc
            if (fp > 0) != (fq > 0):
                t = fp / (fp - fq)
                x, y = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
                ss.append(-b * x + a * y)
        ss.sort()
        ranges += [(ss[i], ss[i + 1]) for i in range(0, len(ss) - 1, 2)]
    ranges.sort()
    merged = []
    for r in ranges:
        if merged and r[0] <= merged[-1][1] + tol:
            merged[-1] = (merged[-1][0], max(merged[-1][1], r[1]))
        else:
            merged.append(r)
    return [r for r in merged if r[1] - r[0] > tol]


def _face_loops(f):
    outer = [p for p in (_pos(v) for v in _items(getattr(f, 'vertices', None))) if p is not None]
    holes = []
    for h in _items(getattr(f, 'holes', None)):
        hp = [p for p in (_pos(v) for v in _items(h)) if p is not None]
        if len(hp) >= 3:
            holes.append(hp)
    return outer, holes


def cut_through_all(scene, mesh, info, outline):
    """Cuts the opening (outline: world points on the front of the wall) right through
    the wall, taking it out of the front and back faces and out of any face of the wall
    it passes through (the bottom of the wall under a door, the top over a tall head).
    Then lines the opening with sides where there is wall beside it."""
    n, depth = info['n'], info['depth']
    P0 = outline[0]
    U = v_norm(v_sub(outline[1], outline[0]))
    V = v_cross(n, U)
    D = depth / SCALE
    tol = 1e-3                                     # mm

    def uv(p):
        d = v_sub(p, P0)
        return (v_dot(d, U) / SCALE, v_dot(d, V) / SCALE)

    def dn(p):
        return v_dot(v_sub(p, P0), n) / SCALE

    cut = clean([uv(p) for p in outline], 1e-6)
    if cut is None:
        raise ValueError("The opening has no area.")
    cx0, cx1, cy0, cy1 = bbox(cut)
    front_regions = []
    jobs = []                    # (face, to_world, region, cut polygons in the face's 2D)
    for f in list(_items(getattr(mesh, 'faces', None))):
        outer, holes = _face_loops(f)
        if len(outer) < 3:
            continue
        nf = _newell(outer)
        k = v_dot(nf, n)
        ds = [dn(p) for p in outer]
        if abs(k) > 0.999:
            d0 = ds[0]
            on_front = k > 0 and abs(d0) < 0.01
            on_back = k < 0 and abs(d0 + D) < 0.01
            if not (on_front or on_back):
                continue
            sgn = 1.0 if k > 0 else -1.0           # keep the face counter-clockwise in 2D
            o2 = [(x, sgn * y) for x, y in (uv(p) for p in outer)]
            h2 = [[(x, sgn * y) for x, y in (uv(p) for p in h)] for h in holes]
            region = (o2, h2)
            if on_front:
                front_regions.append(([(x, y) for x, y in (uv(p) for p in outer)],
                                      [[uv(p) for p in h] for h in holes]))
            fx0, fx1, fy0, fy1 = bbox(o2)
            c2 = clean([(x, sgn * y) for x, y in cut], 1e-6)
            bx0, bx1, by0, by1 = bbox(c2)
            if bx1 < fx0 or bx0 > fx1 or by1 < fy0 or by0 > fy1:
                continue

            def tw(q, sgn=sgn, d0=d0):
                return v_add(P0, v_add(v_mul(U, q[0] * SCALE),
                                       v_add(v_mul(V, sgn * q[1] * SCALE), v_mul(n, d0 * SCALE))))
            jobs.append((f, tw, region, [c2]))
        elif abs(k) < 0.001:
            # a face across the wall (its bottom, top or end): must lie within the wall
            if min(ds) < -D - 0.01 or max(ds) > 0.01:
                continue
            a, b = v_dot(nf, U), v_dot(nf, V)
            L = math.hypot(a, b)
            if L < 0.5:
                continue
            a, b = a / L, b / L
            c = (a * uv(outer[0])[0] + b * uv(outer[0])[1])
            rngs = _line_ranges(cut, a, b, c, tol)
            if not rngs:
                continue
            T = v_add(v_mul(U, -b), v_mul(V, a))     # along the face, across the wall front
            F0 = v_add(P0, v_add(v_mul(U, a * c * SCALE), v_mul(V, b * c * SCALE)))

            def st(p, F0=F0, T=T):
                d = v_sub(p, F0)
                return (v_dot(d, T) / SCALE, v_dot(d, n) / SCALE)
            o2 = [st(p) for p in outer]
            sgn = 1.0 if area2(o2) > 0 else -1.0
            o2 = [(x, sgn * y) for x, y in o2]
            h2 = [[(x, sgn * y) for x, y in (st(p) for p in h)] for h in holes]
            cuts2 = []
            for s0, s1 in rngs:
                r = clean([(s0, sgn * (-D - 1.0)), (s1, sgn * (-D - 1.0)), (s1, sgn * 1.0),
                           (s0, sgn * 1.0)], 1e-6)
                if r:
                    cuts2.append(r)

            def tw(q, sgn=sgn, F0=F0, T=T):
                return v_add(F0, v_add(v_mul(T, q[0] * SCALE), v_mul(n, sgn * q[1] * SCALE)))
            jobs.append((f, tw, (o2, h2), cuts2))
    # work out what's left of each face first, so nothing changes if that fails
    todo = []
    for f, tw, region, cuts in jobs:
        pieces = [region]
        for c2 in cuts:
            nxt = []
            for pc in pieces:
                nxt += poly_minus(pc, c2, tol)
            pieces = nxt
        before = _region_area(region)
        after = sum(_region_area(pc) for pc in pieces)
        if abs(before - after) < 1e-3:
            continue
        if after > before + 1.0:
            raise ValueError("The cut through the wall came out wrong, so it was left alone.")
        todo.append((f, tw, pieces))
    if not todo:
        raise ValueError("The opening didn't meet any face of the wall.")
    # then replace each face with what's left of it
    for f, tw, pieces in todo:
        attrs = dict(getattr(f, 'attrs', None) or {})
        remove_face(scene, mesh, f)
        for o2, h2 in pieces:
            nf = mesh.add_face([QVector3D(*tw(q)) for q in o2])
            try:
                if attrs:
                    nf.attrs = dict(attrs)
            except Exception:
                pass
            for h in h2:
                mesh.add_hole(nf, [QVector3D(*tw(q)) for q in reversed(h)])
    # the sides of the opening, wherever there's wall beside it
    shift = v_mul(n, -depth)
    loops = [lp for r in front_regions for lp in [r[0]] + list(r[1])]
    spans = []
    for i in range(len(cut)):
        # the parts of this edge with wall beside it (in one piece where they run on)
        run = None
        for a2, b2 in _split_edge(cut[i], cut[(i + 1) % len(cut)], loops, tol):
            ex, ey = b2[0] - a2[0], b2[1] - a2[1]
            L = math.hypot(ex, ey)
            probe = ((a2[0] + b2[0]) / 2 + ey / L * 0.5, (a2[1] + b2[1]) / 2 - ex / L * 0.5)
            if any(_in_region(probe, r) for r in front_regions):
                run = (run[0], b2) if run else (a2, b2)
            elif run:
                spans.append(run)
                run = None
        if run:
            spans.append(run)
    for a2, b2 in spans:
        a = v_add(P0, v_add(v_mul(U, a2[0] * SCALE), v_mul(V, a2[1] * SCALE)))
        b = v_add(P0, v_add(v_mul(U, b2[0] * SCALE), v_mul(V, b2[1] * SCALE)))
        q = [a, b, v_add(b, shift), v_add(a, shift)]
        into = v_cross(n, v_sub(b, a))
        if v_dot(_newell(q), into) < 0:
            q.reverse()
        f = mesh.add_face([QVector3D(*p) for p in q])
        try:
            if info['attrs']:
                f.attrs = dict(info['attrs'])
        except Exception:
            pass
    try:
        mesh.prune_orphan_vertices()
    except Exception:
        pass
    return True


def make_command(mutate, meshes):
    """One undo step that adds the door groups and removes faces. Snapshots the
    meshes that change and the group list (like IngeTrazo's own Windowizer)."""
    try:
        from core.history import Command
    except Exception:
        Command = None
    if Command is None or not all(hasattr(m, 'capture_state') for m in meshes):
        return SnapshotImport(mutate)

    class DoorsCommand(Command):
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

    return DoorsCommand()


def to_world(frame):
    O, U, V, N = frame

    def f(p):
        return v_add(O, v_add(v_mul(U, p[0] * SCALE), v_add(v_mul(V, p[1] * SCALE), v_mul(N, p[2] * SCALE))))
    return f


def describe(sh, v):
    """A group name such as 'Round top 4-panel door - 900 x 2100 mm'."""
    x0, x1, y0, y1 = sh['box']
    st = v['style']
    if st in ('panel', 'glazed'):
        n = int(v['cols']) * int(v['rows']) + int(v['cols_b']) * int(v['rows_b'])
        name = ("%d-panel door" % n) if st == 'panel' else "half-glazed door"
    else:
        name = {'ledged': "ledged and braced door", 'framed': "framed, ledged and braced door",
                'stable': "stable door", 'sliding': "sliding goods door"}[st]
    if int(v['leaves']) >= 2 and st != 'sliding':
        name = "pair of " + name.replace("door", "doors")
    top = {'semi': "round top ", 'segment': "segmental ", 'gothic': "pointed "}.get(sh['kind'], "")
    text = top + name
    if v['fanlight'] != 'none' and st != 'sliding':
        text += " with fanlight"
    return "%s - %d x %d mm" % (text[0].upper() + text[1:], round(x1 - x0), round(y1 - y0))


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


# ---------------------------------------------------------------------------
# Live preview
# ---------------------------------------------------------------------------
VIEW_DIR = v_norm((-0.35, -0.25, -1.0))      # from the front, a little right and above
LIGHT = v_norm((0.4, 0.6, 0.8))
COLOURS = {'painted': (52, 96, 72), 'wood': (150, 106, 66), 'frame': (236, 234, 226),
           'glass': (160, 205, 235), 'stone': (205, 198, 182), 'brick': (170, 82, 60),
           'wall': (215, 185, 150), 'iron': (40, 40, 44)}


def _door_rgb(v, so):
    k = getattr(so, 'kind', '')
    if k in ('strap hinge', 'door knob', 'door rail', 'hanger'):
        return COLOURS['iron']
    if k.startswith('door frame'):
        return COLOURS['frame']
    return COLOURS['painted'] if v['style'] in ('panel', 'glazed') else COLOURS['wood']


def preview_items(sh, v):
    """[(layer, depth, [(x, y)...], (r, g, b), alpha)]: layer 0 behind the wall face,
    1 the wall, 2 in front."""
    parts = build_door(sh, v)
    right = v_norm(v_cross(VIEW_DIR, (0.0, 1.0, 0.0)))
    up = v_cross(right, VIEW_DIR)

    def proj(p):
        return (v_dot(p, right), -v_dot(p, up))

    items = []
    for grp, sols in parts.items():
        if grp == 'info':
            continue
        for s in sols:
            if getattr(s, 'mortar', False):
                continue
            if grp == 'glass':
                rgb, alpha = COLOURS['glass'], 110
            elif grp == 'door':
                rgb, alpha = _door_rgb(v, s), 255
            else:
                rgb, alpha = COLOURS.get(v['step'] if grp == 'step' else v['head'], COLOURS['stone']), 255
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
    wall = [proj((x, y, 0.0)) for x, y in ((x0 - m, y0), (x1 + m, y0),
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
 'Sizes (A, B, C ...)': 'A drawing showing what each lettered size (A, B, C ...) measures.',
 'Sizes': 'The lettered sizes, A, B, C ... (see the Sizes drawing).',
 'Preview selected face': "Shows the selected face's shape in the preview, without adding "
                          'anything.',
 'Opening angle': 'How far the door is swung open (0 = shut).',
 'Top rail': 'The depth of the rail across the top of the door.',
 'Bottom rail': 'The depth of the rail across the bottom of the door.',
 'Top panels across': 'How many panels (or panes) across the top half of the door.',
 'Top panels up': 'How many panels (or panes) up the top half of the door.',
 'Bottom panels across': 'How many panels across the bottom half of the door.',
 'Bottom panels up': 'How many panels up the bottom half of the door.',
 'Groove depth': 'How deep the grooves between the boards are.',
 'Ledge width': 'The depth of the ledges (the boards across the back of a ledged door).',
 'Brace width': 'The width of the diagonal braces between the ledges.',
 'Strap hinge width': 'How wide the iron strap hinges are.',
 'Strap hinge thickness': 'How thick the strap hinges are (how far they stand off the boards).',
 'Door knob': 'Adds a door knob.',
 'Knob size': 'The width across the knob.',
 'Knob sticks out': 'How far the knob stands out from the door.',
 'Stone step height': 'The height of the stone step under the door.',
 'Add door to selected face(s)': 'Puts a door into each face you have selected.',
 'Door': "The door style, leaves, frame and how it's placed.",
 'Panels': 'Panels and glazing.',
 'Boards': 'Boards, ledges, braces and strap hinges (ledged, framed and stable doors).',
 'Fanlight, knob': 'The fanlight over the door, and the door knob.',
 'Step & head': 'The stone step under the door, and the head and keystone over it.'}
EDDY_TIPS_END = None


class DoorPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 340)
        self.items = []
        self.msg = ""

    def show_door(self, sh, v):
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
    parts = build_door(sh, v)
    info = parts['info']
    fd = info['fd']
    x0, x1, y0, y1 = sh['box']
    H = y1 - y0
    st = v['style']
    lx0, lx1, ly0, ly1 = info['L']
    zl0, zl1 = info['leaf_z']
    nl = 2 if (int(v['leaves']) >= 2 and st != 'sliding') else 1
    lw = (lx1 - lx0) / nl
    # cut through the first panel (or the middle of a board)
    if st in ('panel', 'glazed'):
        cols = max(1, int(v['cols_b']))
        gx0, gx1, _, _ = info['panel']['G']
        xc = gx0 + (gx1 - gx0) / nl / cols / 2 if nl == 2 else gx0 + (gx1 - gx0) / cols / 2
    else:
        b = info['boarded']
        bx0, bw = b['boards']
        xc = bx0 + bw * 1.5 if (b['region'][1] - bx0) > 2 * bw else bx0 + bw / 2

    front = []
    cut = {}
    for grp in ('door', 'glass', 'step', 'head'):
        sols = [s for s in parts[grp] if not getattr(s, 'mortar', False)]
        for so in sols:
            if grp == 'glass':
                rgb = COLOURS['glass']
            elif grp == 'door':
                rgb = _door_rgb(v, so)
            else:
                rgb = COLOURS.get(v['step'] if grp == 'step' else v['head'], COLOURS['stone'])
            for f in so.faces:
                if _newell(f)[2] > 0.5:
                    front.append((sum(p[2] for p in f) / len(f), [(p[0], p[1]) for p in f], rgb))
        cut[grp] = _slice_x(sols, xc)
    front.sort(key=lambda it: it[0])
    cut['window'] = cut.pop('door')
    cut['sill'] = cut.pop('step')

    D = []

    def dim(letter, view, p1, p2, o, off=0.0):
        D.append((letter, view, p1, p2, o, off))

    fw = v['frame_w']
    if st != 'sliding':
        dim('A', 'F', (x0, y0 + 0.62 * H), (x0 + fw, y0 + 0.62 * H), (0, 1))
        dim('B', 'C', (0.0, y0 + 0.9 * H), (fd, y0 + 0.9 * H), (0, 1), 14)
    dim('D', 'C', (zl0, ly0 + 0.3 * (ly1 - ly0)), (zl1, ly0 + 0.3 * (ly1 - ly0)), (0, 1), 26)
    if st in ('panel', 'glazed'):
        sw = v['stile_w']
        dim('C', 'F', (lx0, ly0 + 0.75 * (ly1 - ly0)), (lx0 + sw, ly0 + 0.75 * (ly1 - ly0)), (0, 1))
        xe = lx0 + lw * 0.5
        dim('E', 'F', (xe, ly0), (xe, ly0 + v['bottom_rail']), (1, 0))
        yl = info['panel']['yl']
        if yl is not None:
            dim('F', 'F', (lx0 + lw * 0.7, yl - v['lock_w'] / 2), (lx0 + lw * 0.7, yl + v['lock_w'] / 2), (1, 0))
        if sh['kind'] in ('flat', 'poly') and info.get('yt') is None:
            dim('G', 'F', (lx0 + lw * 0.3, ly1 - v['top_rail']), (lx0 + lw * 0.3, ly1), (1, 0))
        if int(v['cols_b']) > 1:
            gx0, gx1, _, _ = info['panel']['G']
            xm = gx0 + (gx1 - gx0) / nl / int(v['cols_b']) if nl == 2 else gx0 + (gx1 - gx0) / int(v['cols_b'])
            yb = ly0 + v['bottom_rail'] + 60
            dim('H', 'F', (xm - v['muntin_w'] / 2, yb), (xm + v['muntin_w'] / 2, yb), (0, -1), 12)
        dim('J', 'C', (zl1 - v['panel_d'], ly0 + 0.18 * (ly1 - ly0)), (zl1, ly0 + 0.18 * (ly1 - ly0)), (0, -1), 26)
    else:
        b = info['boarded']
        bx0, bw = b['boards']
        yk = ly0 + 0.3 * (ly1 - ly0)
        dim('K', 'F', (bx0 + bw, yk), (bx0 + 2 * bw, yk), (0, 1))
    if sh['kind'] == 'segment':
        dim('L', 'F', (x0, sh['ys']), (x0, y1), (-1, 0), 22)
    if info.get('yt') is not None and sh.get('ys') is None:
        ox0, ox1, oy0, oy1 = info['O']
        dim('Z', 'F', (ox1, info['yt'] + v['transom_w'] / 2), (ox1, oy1), (1, 0), 14)
    # step
    if v['step'] != 'none' and sh.get('flat_bottom'):
        h = v['step_h'] if v['step'] == 'stone' else v['brick_w']
        fz = fd if st != 'sliding' else 0.0
        dim('M' if v['step'] == 'stone' else 'W', 'F', (x1 + v['horn'], y0), (x1 + v['horn'], y0 + h),
            (1, 0), 18)
        dim('P', 'F', (x1, y0), (x1 + v['horn'], y0), (0, -1), 16)
        dim('N', 'C', (fz, y0), (fz + v['step_p'], y0), (0, -1), 16)
    # head
    if v['head'] != 'none':
        hh = v['head_h']
        hp = v['head_p'] if st != 'sliding' else 0.0
        fz = fd if st != 'sliding' else 0.0
        key = v['keystone']
        if sh['arcs']:
            i0, o0 = _arch_pts(sh, 0.0, hh)
            dx, dy = o0[0] - i0[0], o0[1] - i0[1]
            L0 = math.hypot(dx, dy) or 1.0
            dim('Q', 'F', i0, o0, (dy / L0, -dx / L0), 16)
            mid = _arch_len(sh) / 2
            htop = max(_arch_pts(sh, mid, hh)[1][1], _arch_pts(sh, mid, hh)[0][1] + hh * 0.5)
            if key:
                kp = _arch_key_poly(sh, v, hh)
                dim('T', 'F', kp[0], kp[8], (0, -1))
                ktop = max(q[1] for q in kp)
                rx = max(q[0] for q in kp)
                dim('U', 'F', (rx, ktop - v['key_up']), (rx, ktop), (1, 0), 12)
                htop = ktop - v['key_up']
            dim('R', 'C', (fz, htop), (fz + hp, htop), (0, 1), 12)
        else:
            xb = x1 + v['bearing']
            dim('Q', 'F', (xb, y1), (xb, y1 + hh), (1, 0), 18)
            dim('S', 'F', (x1, y1 + hh), (xb, y1 + hh), (0, 1), 16)
            dim('R', 'C', (fz, y1 + hh), (fz + hp, y1 + hh), (0, 1), 12)
            if key:
                cx = (x0 + x1) / 2
                kp = _flat_key_poly(cx, y1, hh, v)
                dim('T', 'F', kp[0], kp[1], (0, -1))
                dim('U', 'F', (kp[2][0], y1 + hh), kp[2], (1, 0), 12)
    return {'front': front, 'cut': cut, 'dims': D, 'xc': xc, 'fd': fd}


class SizesDiagram(QWidget):
    """Front view and a cut through the door, with each size marked by its letter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 340)
        self.d = None
        self.msg = ""

    def show_door(self, sh, v):
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


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------
CHOICES = {'style': STYLES, 'top': TOPS, 'panel': PANELS, 'hinge': HINGES, 'fanlight': FANLIGHTS,
           'arch_bars': ARCH_BARS, 'step': STEPS, 'head': HEADS}

# key: (label, low, high, decimals, suffix, tip)
FIELDS = {
    'style': ("Door style", "Panelled, half-glazed, boarded (ledged and braced, framed, stable) or a "
                            "sliding goods door hung on a rail in front of the wall."),
    'top': ("Top shape", "Follow the face shape uses the outline of the face you picked (round, "
                         "segmental and pointed tops are recognised). The others make that shape "
                         "inside the face's width and height."),
    'rise': ("Arch rise", 0.0, 5000.0, 0, " mm", "How high a segmental arch rises above its springing."),
    'flat': ("Flat back for 3D printing", "Every part of the door (frame, leaf, panels, bars, step and "
                                          "head) goes right down to the back, so it prints flat with the "
                                          "wall. Doors can't be shown open like this."),
    'remove_face': ("Remove the face", "Takes away the face the door is placed on, so the door "
                                       "replaces it. (A face with openings in it is kept: the doors "
                                       "go into the openings.)"),
    'bars_back': ("Glazing bars at the back (on the print bed)",
                  "Glazing bars in the glass and the fanlight are one thin layer at the back, lying "
                  "on the print bed. Set the bar width and depth to your nozzle width at your scale "
                  "(0.4 mm at 1:80 = 32 mm)."),
    'join': ("Join into one solid", "Uses IngeTrazo's own Union (the Solid Tools) so the door, its "
                                    "step and its head come out as one clean, watertight solid "
                                    "(glass stays separate). Best for exporting to a slicer."),
    'cut': ("Cut through the wall", "When the face is drawn on a solid wall, the door, step and head "
                                    "are cut right through it, and they all sit flush with the back "
                                    "of the wall. The wall face is left clean for bricks or boards."),
    'lift': ("Gap round the door", 0.0, 5.0, 3, " mm", "A tiny gap between the door (with its step and "
                                                      "head) and the wall, so slicers don't get confused "
                                                      "by faces lying exactly on top of each other. "
                                                      "0.01 mm is plenty."),
    'flip': ("Door faces the other way", "Tick if the door comes out on the wrong side of the wall."),
    'leaves': ("Leaves", 1, 2, None, "", "1 = a single door, 2 = a pair of doors meeting in the middle."),
    'hinge': ("Hinge side", "Which side a single door is hung on (where the braces start and the "
                            "strap hinges go; the knob goes on the other side)."),
    'open': ("Show the door open", "Swings the door (or doors) open. Not when printing flat."),
    'open_angle': ("Opening angle", 0.0, 120.0, 0, " deg", ""),
    'frame_w': ("Frame width", 5.0, 500.0, 0, " mm", "Face width of the door frame (sides and top)."),
    'frame_d': ("Frame depth", 5.0, 500.0, 0, " mm", "How far the frame stands out (from the back when "
                                                     "cut through the wall)."),
    'leaf_t': ("Door thickness", 5.0, 200.0, 0, " mm", "Thickness of the door leaf (when not flat)."),
    'leaf_set': ("Door set back in the frame", 0.0, 200.0, 0, " mm", "How far the front of the door is "
                                                                     "behind the front of the frame."),
    'stile_w': ("Stiles", 10.0, 500.0, 0, " mm", "Width of the sides of the door (and of the frame of a "
                                                 "framed door)."),
    'top_rail': ("Top rail", 10.0, 500.0, 0, " mm", ""),
    'bottom_rail': ("Bottom rail", 10.0, 800.0, 0, " mm", ""),
    'lock_w': ("Lock rail", 10.0, 500.0, 0, " mm", "The middle rail, at the height of the knob."),
    'lock_y': ("Lock rail / knob / split height", 100.0, 3000.0, 0, " mm",
               "Height of the middle of the lock rail and the knob above the bottom of the door. "
               "On a stable door, where the top and bottom halves meet."),
    'muntin_w': ("Muntins", 10.0, 500.0, 0, " mm", "The upright bars between panels (and rails between "
                                                   "rows of panels)."),
    'cols': ("Top panels across", 1, 8, None, "", ""),
    'rows': ("Top panels up", 1, 8, None, "", ""),
    'cols_b': ("Bottom panels across", 1, 8, None, "", ""),
    'rows_b': ("Bottom panels up", 1, 8, None, "", ""),
    'panel': ("Panels", "Raised and fielded: a sloping bevel round a raised middle. Flat: plain sunk panels."),
    'panel_d': ("Panel sunk by", 0.5, 100.0, 1, " mm", "How far the panels sit back from the stiles and "
                                                       "rails. 16 = 0.2 mm at 1:80."),
    'bevel': ("Raised panel bevel", 1.0, 300.0, 0, " mm", "Width of the sloping border of a raised panel."),
    'bar_w': ("Glazing bar width", 1.0, 200.0, 1, " mm", ""),
    'bar_d': ("Glazing bar depth", 1.0, 200.0, 1, " mm", ""),
    'glass': ("Glass", "Adds glass as its own group (so you can hide it or print it in clear)."),
    'glass_t': ("Glass thickness", 0.1, 50.0, 1, " mm", ""),
    'arch_bars': ("Bars in an arched top", "Half-glazed doors with a round top: what the bars do in the arch."),
    'board_w': ("Board width", 10.0, 1000.0, 0, " mm", "Boarded doors: boards are evened out to fill the door."),
    'board_gap': ("Groove between boards", 0.2, 100.0, 1, " mm", "32 = 0.4 mm at 1:80."),
    'groove_d': ("Groove depth", 0.2, 100.0, 1, " mm", ""),
    'board_set': ("Boards set back in the frame", 0.0, 100.0, 0, " mm", "Framed doors: how far the boards "
                                                                       "are behind the frame."),
    'ledges': ("Ledges on the front", "The level bars across a boarded door."),
    'ledge_h': ("Ledge width", 10.0, 500.0, 0, " mm", ""),
    'ledge_t': ("Ledge thickness", 0.5, 200.0, 1, " mm", "How far ledges and braces stand out from the boards."),
    'braces': ("Braces", "Diagonal braces between the ledges, rising from the hinge side (a Z)."),
    'brace_w': ("Brace width", 10.0, 500.0, 0, " mm", ""),
    'straps': ("Strap hinges", "Long iron strap hinges on the ledges."),
    'strap_w': ("Strap hinge width", 5.0, 300.0, 0, " mm", ""),
    'strap_t': ("Strap hinge thickness", 0.5, 100.0, 1, " mm", ""),
    'knob': ("Door knob", ""),
    'knob_d': ("Knob size", 5.0, 300.0, 0, " mm", ""),
    'knob_p': ("Knob sticks out", 1.0, 300.0, 0, " mm", ""),
    'fanlight': ("Fanlight", "A light on top of the door, above a transom. The face you drew is the "
                             "door; the fanlight is added on top of it (with a round, segmental or "
                             "pointed top shape it's an arched fanlight). If you drew a round-topped "
                             "face yourself, the fanlight fills its arch."),
    'fan_h': ("Fanlight height", 50.0, 3000.0, 0, " mm", "Square fanlights: the height of the glass "
                                                          "above the transom."),
    'transom_w': ("Transom", 5.0, 500.0, 0, " mm", "The bar between the door and the fanlight."),
    'fan_cols': ("Fanlight bars", 2, 16, None, "", "How many lights the fanlight is split into."),
    'slide_over': ("Door overlaps the opening", 0.0, 1000.0, 0, " mm",
                   "Sliding doors: how far the door covers the wall past the sides and top of the opening."),
    'rail_h': ("Rail height", 10.0, 500.0, 0, " mm", "Sliding doors: the rail the door hangs from."),
    'step': ("Step", "A doorstep in the bottom of the opening, standing out from the wall."),
    'step_h': ("Stone step height", 10.0, 1000.0, 0, " mm", ""),
    'step_p': ("Step sticks out", 0.0, 1000.0, 0, " mm", "How far the step stands out in front of the frame."),
    'horn': ("Step runs past opening", 0.0, 500.0, 0, " mm", "How far the step goes into the wall at each side."),
    'head': ("Head", "A lintel or soldier course over a square top; an arch of stones or bricks "
                     "over a round, segmental or pointed door."),
    'head_h': ("Head depth", 20.0, 1000.0, 0, " mm", "Height of the lintel or soldier course, or "
                                                     "the depth of the arch."),
    'head_p': ("Head sticks out", 0.0, 200.0, 0, " mm", ""),
    'bearing': ("Lintel runs past opening", 0.0, 500.0, 0, " mm", "Flat heads only, each side."),
    'keystone': ("Keystone", ""),
    'key_w': ("Keystone width", 20.0, 1000.0, 0, " mm", ""),
    'key_up': ("Keystone rises above head", 0.0, 500.0, 0, " mm", ""),
    'key_p': ("Keystone sticks out more", 0.0, 200.0, 0, " mm", ""),
    'brick_w': ("Step brick height", 30.0, 300.0, 1, " mm", "Height of a brick-on-edge step (a brick's width)."),
    'brick_t': ("Brick thickness", 20.0, 200.0, 1, " mm", "Width of each brick as seen in a soldier "
                                                          "course, brick arch or brick step."),
    'joint': ("Mortar joint", 0.0, 30.0, 1, " mm", ""),
}

# each size has a letter, shown next to its box and on the 'Sizes' drawing
LETTERS = {'frame_w': 'A', 'frame_d': 'B', 'stile_w': 'C', 'leaf_t': 'D', 'bottom_rail': 'E',
           'lock_w': 'F', 'top_rail': 'G', 'muntin_w': 'H', 'panel_d': 'J', 'board_w': 'K', 'rise': 'L',
           'step_h': 'M', 'step_p': 'N', 'horn': 'P', 'head_h': 'Q', 'head_p': 'R', 'bearing': 'S',
           'key_w': 'T', 'key_up': 'U', 'key_p': 'V', 'brick_w': 'W', 'brick_t': 'X', 'joint': 'Y',
           'fan_h': 'Z'}

TABS = [
    ("Door", ('style', 'top', 'rise', 'leaves', 'hinge', 'flat', 'bars_back', 'join', 'remove_face',
              'cut', 'lift', 'flip', 'open', 'open_angle', 'glass', 'glass_t')),
    ("Panels", ('cols', 'rows', 'cols_b', 'rows_b', 'panel', 'panel_d', 'bevel', 'stile_w', 'top_rail',
                'bottom_rail', 'lock_w', 'lock_y', 'muntin_w', 'arch_bars', 'bar_w', 'bar_d')),
    ("Boards", ('board_w', 'board_gap', 'groove_d', 'board_set', 'ledges', 'ledge_h', 'ledge_t',
                'braces', 'brace_w', 'straps', 'strap_w', 'strap_t', 'slide_over', 'rail_h')),
    ("Fanlight, knob", ('fanlight', 'fan_h', 'transom_w', 'fan_cols', 'knob', 'knob_d', 'knob_p')),
    ("Step && head", ('step', 'step_h', 'step_p', 'horn', 'head', 'head_h', 'head_p', 'bearing',
                      'keystone', 'key_w', 'key_up', 'key_p')),
    ("Sizes", ('frame_w', 'frame_d', 'leaf_t', 'leaf_set', 'brick_w', 'brick_t', 'joint')),
]


class DoorsDialog(QDialog):
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
        # what happened last time 'Add door' was clicked
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
        self.preview = DoorPreview()
        self.sizes = SizesDiagram()
        self.views.addTab(self.preview, "3D view")
        self.views.addTab(self.sizes, "Sizes (A, B, C ...)")
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
        for b in (b_save, b_saveas, b_del, b_dir):
            prow.addWidget(b)
        lay.addLayout(prow)
        b_save.clicked.connect(self.save_preset)
        b_saveas.clicked.connect(lambda: self.save_preset_as())
        b_del.clicked.connect(self.delete_preset)
        b_dir.clicked.connect(self.open_folder)
        self.cb_preset.currentIndexChanged.connect(self.apply_preset)

        brow = QHBoxLayout()
        self.b_add = QPushButton("Add door to selected face(s)")
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
        panelled = st in ('panel', 'glazed')
        boarded = not panelled
        fan = v['fanlight'] != 'none' and st != 'sliding'
        en = {
            'rise': v['top'] == 'segment',
            'open_angle': v['open'] and not v['flat'],
            'open': not v['flat'] and st != 'sliding',
            'cut': v['remove_face'],
            'bars_back': v['flat'],
            'glass_t': v['glass'],
            'leaves': st not in ('sliding', 'stable'), 'hinge': st != 'sliding',
            'cols': panelled, 'rows': panelled, 'cols_b': panelled, 'rows_b': panelled,
            'panel': panelled, 'panel_d': panelled, 'bevel': panelled and v['panel'] == 'raised',
            'top_rail': st in ('panel', 'glazed', 'framed', 'sliding'),
            'bottom_rail': st in ('panel', 'glazed', 'sliding'),
            'stile_w': st in ('panel', 'glazed', 'framed', 'sliding'),
            'lock_w': panelled, 'lock_y': st != 'sliding', 'muntin_w': panelled,
            'arch_bars': st == 'glazed', 'bar_w': st == 'glazed' or fan, 'bar_d': st == 'glazed' or fan,
            'board_w': boarded, 'board_gap': boarded, 'groove_d': boarded,
            'board_set': st in ('framed', 'sliding'),
            'ledges': boarded, 'ledge_h': boarded and v['ledges'], 'ledge_t': boarded and v['ledges'],
            'braces': boarded and v['ledges'], 'brace_w': boarded and v['ledges'] and v['braces'],
            'straps': boarded and st != 'sliding', 'strap_w': boarded and v['straps'] and st != 'sliding',
            'strap_t': boarded and v['straps'] and st != 'sliding',
            'slide_over': st == 'sliding', 'rail_h': st == 'sliding',
            'fanlight': st != 'sliding', 'fan_h': fan, 'transom_w': fan,
            'fan_cols': fan and v['fanlight'] in ('bars', 'fan'),
            'knob': st != 'sliding', 'knob_d': v['knob'] and st != 'sliding',
            'knob_p': v['knob'] and st != 'sliding',
            'leaf_set': st != 'sliding',
            'frame_w': st != 'sliding', 'frame_d': st != 'sliding',
            'step_h': v['step'] == 'stone', 'step_p': v['step'] != 'none', 'horn': v['step'] != 'none',
            'brick_w': v['step'] == 'brick',
            'head_h': v['head'] != 'none', 'head_p': v['head'] != 'none' and st != 'sliding',
            'bearing': v['head'] != 'none', 'keystone': v['head'] != 'none',
            'key_w': v['keystone'] and v['head'] != 'none',
            'key_up': v['keystone'] and v['head'] != 'none',
            'key_p': v['keystone'] and v['head'] != 'none' and st != 'sliding',
        }
        for k, on in en.items():
            self.w[k].setEnabled(bool(on))
            self.labels[k].setEnabled(bool(on))
        if st == 'glazed':
            names = ("Panes across (glass)", "Panes up (glass)", "Bottom panels across", "Bottom panels up")
        else:
            names = ("Top panels across", "Top panels up", "Bottom panels across", "Bottom panels up")
        for k, t in zip(('cols', 'rows', 'cols_b', 'rows_b'), names):
            self.labels[k].setText(t)
        self.update_preview(v)

    def update_preview(self, v=None):
        v = v or self.values()
        try:
            if self.sel_shape is not None:
                poly = self.sel_shape
            else:
                poly = [(0, 0), (900, 0), (900, 2100), (0, 2100)]
            sh = fit_door(poly, v)
        except Exception as e:
            self.preview.items, self.preview.msg = [], str(e)
            self.preview.update()
            self.sizes.d, self.sizes.msg = None, str(e)
            self.sizes.update()
            return
        self.preview.show_door(sh, v)
        self.sizes.show_door(sh, v)

    def show_report(self, lines):
        """Shows the result of the last 'Add door' under the selection line
        (the text can be selected and copied)."""
        if not lines:
            self.lbl_report.setVisible(False)
            return
        bad = any(l.startswith("NOT") or l.startswith("Could not") or "couldn't" in l
                  or "could not" in l for l in lines)
        self.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if bad else "#2e7d32"))
        self.lbl_report.setText("Last door added:\n" + "\n".join(lines))
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
                                 "Click 'Add door' to fit a door into each."
                                 % (len(faces), "" if len(faces) == 1 else "s", len(polys),
                                    "" if len(polys) == 1 else "s", round(x1 - x0), round(y1 - y0)))
        else:
            self.sel_shape = None
            self.lbl_sel.setText("Select a face drawn on a wall (or a face with openings in it), "
                                 "then click 'Add door'. The preview shows a 900 x 2100 mm door.")
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
        p = self.all_presets().get(name) if name else None
        if p:
            # built-in presets are complete doors: start them from the defaults
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
class PeriodDoorsTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+D"
    description = ("Period doors that fit the selected face: panelled, half-glazed, ledged and braced, "
                   "stable and sliding goods doors, with fanlights, steps, heads and keystones.")

    _saved = None
    _dialog = None
    _join = True
    _cut = True
    last_report = []

    def on_activate(self, viewport):
        dlg = PeriodDoorsTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.read_selection()
                    dlg.raise_()
                    dlg.activateWindow()
                    return
            except Exception:
                pass
        cur = dict(DEFAULTS)
        if PeriodDoorsTool._saved:
            cur.update(PeriodDoorsTool._saved)
        dlg = DoorsDialog(cur, viewport, self)
        PeriodDoorsTool._dialog = dlg

        def closed(*_):
            PeriodDoorsTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass

    def add_from_dialog(self, dlg):
        v = dlg.values()
        PeriodDoorsTool._saved = dict(v)
        viewport = dlg.viewport
        scene = getattr(viewport, 'scene', None)
        faces = selected_faces(scene) if scene is not None else []
        if not faces:
            QMessageBox.information(dlg, PLUGIN_NAME, "Select a face first: a shape drawn on a wall, "
                                    "or a face with openings in it.")
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
                    # an opening already there: the door fills it from the back of the wall,
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
                    sh = fit_door(poly, v)
                    built = build_door(sh, vv)
                except ValueError as e:
                    problems.append("Opening %d: %s" % (n, e))
                    continue
                if info is not None:
                    ol = cut_outline(sh, vv)
                    if gap > 0:
                        ol = clean(offset_poly(ol, -gap)) or ol        # a hair bigger all round
                    cuts[face] = [tw0((x, y, 0.0)) for x, y in ol]
                title = describe(sh, v)
                if v.get('join', True) and v['style'] != 'sliding':
                    groups = [(title, built['door'] + built['step'] + built['head']),
                              ("Glass - " + title, built['glass'])]
                elif v.get('join', True):
                    # a sliding door hangs clear of the wall: keep it apart from the step and head
                    groups = [(title, built['door']), ("Glass - " + title, built['glass']),
                              ("Step and head - " + title, built['step'] + built['head'])]
                else:
                    groups = [(title, built['door']), ("Glass - " + title, built['glass']),
                              ("%s - %s" % (dict(STEPS)[v['step']], title), built['step']),
                              ("%s - %s" % ("Keystone head" if v['keystone'] else "Head", title),
                               built['head'])]
                for name, sols in groups:
                    if sols:
                        parts.append((name, [s.mapped(tw) for s in sols]))
                made = True
            # a drawn face (no openings in it) is replaced by its door
            if made and not holes:
                used.append(face)
        return parts, problems, used, cuts

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
                for attr in ('name', 'label'):      # so the joined door keeps its name
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
                    _ed3d_organise(scene, g)
                    if hasattr(scene, 'add_group'):
                        scene.add_group(g)
                    elif hasattr(scene, 'groups') and isinstance(scene.groups, list):
                        scene.groups.append(g)
                    else:
                        raise RuntimeError("Could not add the door to the scene.")
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
                        if host is None and cuts.get(f):
                            # the door reaches the edge of the wall face (it stands on the
                            # bottom of the wall): cut every face of the wall it goes through
                            cut_through_all(scene, m, info, cuts.get(f))
                        elif not cut_through(scene, m, info, host, cuts.get(f)):
                            stats['small_cut'] += 1
                        stats['cut'] += 1
                    except Exception as e:
                        stats['cut_err'] = e

        hist = viewport.history
        try:
            hist.execute(make_command(mutate, meshes) if targets else SnapshotImport(mutate))
        except Exception as e:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not add the door:\n%s" % e)
            return False
        err = getattr(hist, 'last_error', None)
        if err and stats['faces'] == 0:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not add the door:\n%s" % err)
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
            rep.append("%d opening(s) were cut to the door only: the wall face round them "
                       "couldn't be found, so the step and head sit on the wall." % stats['small_cut'])
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
