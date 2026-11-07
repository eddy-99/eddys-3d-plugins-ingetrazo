# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Gutters & Downpipes for IngeTrazo
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
3D Gutters & Downpipes - full-size rainwater goods for IngeTrazo
Half-round, square, ogee and deep-flow gutters with round or square downpipes.
Pick a part, set its sizes, and it is built as a hollow solid in its own group.
Select the open end of a part you already placed and the next part joins onto it.
Settings can be saved as presets (one .json file each) in a presets folder.
"""

import os
import json
import math
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox,
    QMessageBox, QLabel, QPushButton, QInputDialog, QListWidget,
    QListWidgetItem, QGroupBox, QCheckBox, QWidget
)

PLUGIN_NAME = "3D Gutters & Downpipes"


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

PORT_KEY = "drain_port"          # face attribute that marks a connectable open end

PRESET_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets",
                          "Gutters and Downpipes")

GUTTER_PROFILES = [("Half-round", "halfround"), ("Square-line", "square"),
                   ("Ogee", "ogee"), ("Deep-flow", "deepflow")]
PIPE_TYPES = [("Round", "round"), ("Square", "square")]
BEND_DIRS = [("Towards the wall", 0.0), ("Away from the wall", 180.0),
             ("Left", 90.0), ("Right", -90.0)]

# key, label, system, settings it uses
PARTS = [
    ("gutter",    "Gutter length",                  "gutter", ("length",)),
    ("outlet",    "Running outlet",                 "gutter", ("outlet_len",)),
    ("stopend",   "Stop end",                       "gutter", ()),
    ("union",     "Union bracket (joins 2 lengths)", "gutter", ("offset",)),
    ("bracket",   "Fascia bracket",                 "gutter", ("offset",)),
    ("angle90x",  "90 deg angle - external corner", "gutter", ("leg",)),
    ("angle90i",  "90 deg angle - internal corner", "gutter", ("leg",)),
    ("angle135x", "135 deg angle - external corner", "gutter", ("leg",)),
    ("angle135i", "135 deg angle - internal corner", "gutter", ("leg",)),
    ("pipe",      "Downpipe length",                "pipe",   ("length",)),
    ("bend",      "Bend / offset bend",             "pipe",   ("bend_turn", "bend_dir")),
    ("branch",    "Branch (Y junction)",            "pipe",   ("bend_turn", "bend_dir", "branch_len")),
    ("shoe",      "Shoe (bottom outlet)",           "pipe",   ("bend_dir",)),
    ("socket",    "Pipe socket / coupler",          "pipe",   ("offset",)),
    ("clip",      "Pipe clip",                      "pipe",   ("offset",)),
]
PART_INFO = {k: (label, system, uses) for k, label, system, uses in PARTS}

# Sizes are in millimetres (full size)
DEFAULTS = {
    'part': 'gutter', 'units': 'm',      # IngeTrazo stores geometry in metres
    'g_profile': 'halfround', 'g_width': 112.0, 'g_depth': 56.0, 'g_wall': 2.5,
    'p_type': 'round', 'p_size': 68.0, 'p_wall': 2.0,
    'length': 1000.0, 'outlet_len': 150.0, 'leg': 100.0,
    'bend_turn': 67.5, 'bend_dir': 0.0, 'branch_len': 200.0, 'offset': 0.0,
    'solid': False, 'wall_side': 0.0,
    'drop': 25.0, 'wall_gap': 0.0, 'over_left': 0.0, 'over_right': 0.0, 'fit_wall': True,
    'wall_flip': False, 'auto_fix': True, 'g_spacing': 1000.0, 'p_spacing': 1800.0,
    'chunky': False, 'chunk_mult': 3.0,
}
WALL_SIDES = [("Behind the part (+Y)", 0.0), ("On the left (-X)", 90.0),
              ("In front (-Y)", 180.0), ("On the right (+X)", 270.0)]
PRESET_KEYS = ('g_profile', 'g_width', 'g_depth', 'g_wall', 'p_type', 'p_size', 'p_wall',
               'length', 'outlet_len', 'leg', 'bend_turn', 'branch_len', 'solid',
               'drop', 'wall_gap', 'over_left', 'over_right', 'g_spacing', 'p_spacing',
               'chunky', 'chunk_mult')
GUTTER_KEYS = ('g_profile', 'g_width', 'g_depth', 'g_wall', 'solid')
PIPE_KEYS = ('p_type', 'p_size', 'p_wall', 'solid')
OVERLAY_PARTS = ('union', 'bracket', 'socket', 'clip')
END_NAMES = {'out': "far end", 'in': "start", 'down': "outlet spigot", 'branch': "branch end"}

BUILTIN_PRESETS = {
    "UK half-round 112 + round 68": {'g_profile': 'halfround', 'g_width': 112.0, 'g_depth': 56.0,
                                     'g_wall': 2.5, 'p_type': 'round', 'p_size': 68.0, 'p_wall': 2.0},
    "UK square-line 114 + square 65": {'g_profile': 'square', 'g_width': 114.0, 'g_depth': 60.0,
                                       'g_wall': 2.5, 'p_type': 'square', 'p_size': 65.0, 'p_wall': 2.0},
    "Deep-flow 117 + round 68": {'g_profile': 'deepflow', 'g_width': 117.0, 'g_depth': 75.0,
                                 'g_wall': 2.5, 'p_type': 'round', 'p_size': 68.0, 'p_wall': 2.0},
    "Cast iron ogee 115 + round 75": {'g_profile': 'ogee', 'g_width': 115.0, 'g_depth': 75.0,
                                      'g_wall': 5.0, 'p_type': 'round', 'p_size': 75.0, 'p_wall': 5.0},
}

SPIGOT_LEN = 60.0        # outlet spigot below the gutter
SOCKET_LEN = 40.0        # straight ends on bends
CLIP_LEN = 25.0
UNION_LEN = 80.0
BRACKET_LEN = 25.0
SOCKET_COUPLER_LEN = 70.0
STOPEND_SLEEVE = 25.0


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


def rotate(v, axis, ang):
    """Rodrigues rotation of v about a unit axis."""
    c, s = math.cos(ang), math.sin(ang)
    return v_add(v_add(v_mul(v, c), v_mul(v_cross(axis, v), s)), v_mul(axis, v_dot(axis, v) * (1 - c)))


def rot_between(a, b):
    """(axis, angle) turning unit vector a onto unit vector b."""
    ax = v_cross(a, b)
    s = v_len(ax)
    c = max(-1.0, min(1.0, v_dot(a, b)))
    if s < 1e-12:
        if c > 0:
            return None
        # opposite: any perpendicular axis
        p = (1.0, 0.0, 0.0) if abs(a[0]) < 0.9 else (0.0, 1.0, 0.0)
        return v_norm(v_cross(a, p)), math.pi
    return v_mul(ax, 1.0 / s), math.atan2(s, c)


# ---------------------------------------------------------------------------
# Cross-sections, in (a, b): a = towards the wall (left of the run), b = up.
# ---------------------------------------------------------------------------
def gutter_outer(profile, W, D, n_arc=16):
    """Outer edge of the gutter, from the back top (wall side) round to the front top."""
    if profile == 'square':
        return [(W / 2, D), (W / 2, 0.0), (-W / 2, 0.0), (-W / 2, D)]
    if profile == 'ogee':
        D = min(D, W * 0.9)
        r = D / 2.0
        xb = -W / 2 + 2 * r           # where the flat bottom meets the S-curve
        pts = [(W / 2, D), (W / 2, 0.0)]
        for i in range(n_arc // 2 + 1):          # convex lower curve
            f = (math.pi / 2) * i / (n_arc // 2)
            pts.append((xb - r * math.sin(f), r - r * math.cos(f)))
        cx = xb - 2 * r
        for i in range(1, n_arc // 2 + 1):       # concave upper curve
            f = (math.pi / 2) * i / (n_arc // 2)
            pts.append((cx + r * math.cos(f), r + r * math.sin(f)))
        return pts
    if profile == 'deepflow':
        return [(W / 2 * math.cos(math.pi * i / n_arc), D - D * math.sin(math.pi * i / n_arc))
                for i in range(n_arc + 1)]
    R = W / 2.0                                   # half-round
    return [(R * math.cos(math.pi * i / n_arc), R - R * math.sin(math.pi * i / n_arc))
            for i in range(n_arc + 1)]


def offset_open(pts, d):
    """Offsets an open polyline by d to its right (positive d = into the gutter)."""
    n = len(pts)
    norms = []
    for i in range(n - 1):
        dx, dy = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
        L = math.hypot(dx, dy) or 1.0
        norms.append((dy / L, -dx / L))
    out = []
    for i in range(n):
        if i == 0:
            nx, ny = norms[0]
            k = 1.0
        elif i == n - 1:
            nx, ny = norms[-1]
            k = 1.0
        else:
            a, b = norms[i - 1], norms[i]
            nx, ny = a[0] + b[0], a[1] + b[1]
            L = math.hypot(nx, ny) or 1.0
            nx, ny = nx / L, ny / L
            k = 1.0 / max(0.2, nx * a[0] + ny * a[1])
        out.append((pts[i][0] + nx * d * k, pts[i][1] + ny * d * k))
    return out


def gutter_band(s, grow=None, thick=None):
    """Closed U-shaped section of the gutter wall. With grow (a gap, may be 0) it is
    the shape of a part that fits over the outside of the gutter (union, stop end ...)."""
    outer = gutter_outer(s['g_profile'], s['g_width'], s['g_depth'])
    if s.get('solid') and grow is None:
        return outer           # solid for printing: the whole shape filled in
    t = s['g_wall'] if thick is None else thick
    if grow is not None:
        inner = offset_open(outer, -grow)          # outside face of the gutter + gap
        outer = offset_open(outer, -grow - t)
        return outer + list(reversed(inner))
    inner = offset_open(outer, t)
    return outer + list(reversed(inner))


def gutter_low_point(s):
    outer = gutter_outer(s['g_profile'], s['g_width'], s['g_depth'])
    zmin = min(p[1] for p in outer)
    low = [p[0] for p in outer if p[1] - zmin < 1e-6]
    return (min(low) + max(low)) / 2.0, zmin


def pipe_rings(s, grow=None, thick=None, n=32):
    """(outer, inner) loops of the pipe section, matched point for point.
    With grow (a gap, may be 0) it is a sleeve that fits over the pipe."""
    t = s['p_wall'] if thick is None else thick
    sleeve = grow is not None
    solid = s.get('solid') and not sleeve     # solid rod for printing: no bore
    grow = grow or 0.0
    if s['p_type'] == 'square':
        h_out = s['p_size'] / 2 + grow + (t if sleeve else 0.0)
        h_in = s['p_size'] / 2 + grow if sleeve else s['p_size'] / 2 - t
        sq = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
        return ([(x * h_out, y * h_out) for x, y in sq],
                None if solid else [(x * h_in, y * h_in) for x, y in sq])
    r_out = s['p_size'] / 2 + grow + (t if sleeve else 0.0)
    r_in = s['p_size'] / 2 + grow if sleeve else s['p_size'] / 2 - t
    circ = [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i in range(n)]
    return ([(c * r_out, d * r_out) for c, d in circ],
            None if solid else [(c * r_in, d * r_in) for c, d in circ])


# ---------------------------------------------------------------------------
# Sweeping a section along a path (mitred joints)
# ---------------------------------------------------------------------------
def path_frames(path, up0):
    T = [v_norm(v_sub(path[k + 1], path[k])) for k in range(len(path) - 1)]
    up = v_norm(v_sub(up0, v_mul(T[0], v_dot(up0, T[0]))))
    ups = [up]
    for k in range(1, len(T)):
        r = rot_between(T[k - 1], T[k])
        up = rotate(up, r[0], r[1]) if r else up
        up = v_norm(v_sub(up, v_mul(T[k], v_dot(up, T[k]))))
        ups.append(up)
    lefts = [v_cross(ups[k], T[k]) for k in range(len(T))]
    return T, ups, lefts


def sweep_rings(path, up0, loop):
    """Positions of the section at every path point (mitred at the bends)."""
    T, ups, lefts = path_frames(path, up0)
    rings = []
    N = len(path)
    for j in range(N):
        k = min(j, N - 2) if j < N - 1 else N - 2
        kp = j - 1 if j > 0 else 0
        ring = []
        for a, b in loop:
            if 0 < j < N - 1:
                o = v_add(v_mul(lefts[kp], a), v_mul(ups[kp], b))
                m = v_norm(v_add(T[kp], T[j]))
                lam = -v_dot(o, m) / (v_dot(T[kp], m) or 1e-12)
                ring.append(v_add(v_add(path[j], o), v_mul(T[kp], lam)))
            else:
                ring.append(v_add(path[j], v_add(v_mul(lefts[k], a), v_mul(ups[k], b))))
        rings.append(ring)
    return rings, (T, ups, lefts)


class Solid:
    """Faces of one closed solid; each face may carry a port name."""

    def __init__(self):
        self.faces = []        # (list of points, port name or None)

    def add(self, pts, tag=None):
        self.faces.append((list(pts), tag))

    def volume(self):
        v = 0.0
        for pts, _ in self.faces:
            for j in range(1, len(pts) - 1):
                v += v_dot(pts[0], v_cross(pts[j], pts[j + 1]))
        return v / 6.0

    def fix_winding(self):
        if self.volume() < 0:
            self.faces = [(list(reversed(p)), t) for p, t in self.faces]


def sweep_solid(path, up0, loop, inner=None, start_tag=None, end_tag=None):
    """Solid swept along path. With inner (same point count) it is a hollow tube."""
    sol = Solid()
    outer_rings, frames = sweep_rings(path, up0, loop)
    inner_rings = sweep_rings(path, up0, inner)[0] if inner else None
    n = len(loop)
    for rings, sign in ((outer_rings, 1), (inner_rings, -1)):
        if rings is None:
            continue
        for k in range(len(rings) - 1):
            r0, r1 = rings[k], rings[k + 1]
            for i in range(n):
                q = [r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]]
                sol.add(q if sign > 0 else list(reversed(q)))
    if inner:
        o0, i0, o1, i1 = outer_rings[0], inner_rings[0], outer_rings[-1], inner_rings[-1]
        for i in range(n):
            j = (i + 1) % n
            sol.add([o0[j], o0[i], i0[i], i0[j]], start_tag)
            sol.add([o1[i], o1[j], i1[j], i1[i]], end_tag)
    else:
        sol.add(list(reversed(outer_rings[0])), start_tag)
        sol.add(list(outer_rings[-1]), end_tag)
    sol.fix_winding()
    return sol, frames


def box_solid(x0, x1, y0, y1, z0, z1):
    sol = Solid()
    p = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    for f in ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)):
        sol.add([p[i] for i in f])
    sol.fix_winding()
    return sol


def arc_path(start, T, d, R, turn, segs):
    """Points of a bend of radius R turning by `turn` radians from direction T towards d."""
    return [v_add(start, v_add(v_mul(T, R * math.sin(turn * i / segs)),
                               v_mul(d, R * (1 - math.cos(turn * i / segs)))))
            for i in range(segs + 1)]


# ---------------------------------------------------------------------------
# Parts. Built in local millimetres: x = along the run, y = towards the wall,
# z = up. Every part returns (solids, ports); ports are where others can join.
# ---------------------------------------------------------------------------
X, Y, Z = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
NX, NZ = (-1.0, 0.0, 0.0), (0.0, 0.0, -1.0)


def fix_mult(s):
    """How much thicker fittings are made ('Chunky fittings' for 3D printing)."""
    return max(1.0, s.get('chunk_mult', 3.0)) if s.get('chunky') else 1.0


def bracket_dims(s):
    m = fix_mult(s)
    return {'t': s['g_wall'] * m, 'plate': 5.0 * m, 'arm': 4.0 * m,
            'len': BRACKET_LEN * (1 + (m - 1) / 2),
            'gap': 0.0 if s.get('chunky') else 0.5}      # chunky: no gap, prints as one piece


def fit_gap(s, normal=0.5):
    return 0.0 if s.get('chunky') else normal


def port(c, n, u, role, system):
    return {'c': c, 'n': n, 'u': u, 'role': role, 'sys': system}


def bend_vector(deg):
    r = math.radians(deg)
    return (0.0, math.sin(r), math.cos(r))


def build_part(key, s):
    sol = []
    ports = {}
    if key in ('gutter', 'angle90x', 'angle90i', 'angle135x', 'angle135i'):
        band = gutter_band(s)
        if key == 'gutter':
            L = s['length']
            path = [(0, 0, 0), (L, 0, 0)]
        else:
            L = s['leg']
            turn = math.radians(90.0 if '90' in key else 45.0)
            side = 1.0 if key.endswith('x') else -1.0
            path = [(0, 0, 0), (L, 0, 0), (L + L * math.cos(turn), side * L * math.sin(turn), 0)]
        so, (T, ups, _) = sweep_solid(path, Z, band, start_tag='in', end_tag='out')
        sol.append(so)
        ports['in'] = port((0, 0, 0), NX, Z, 'in', 'gutter')
        ports['out'] = port(path[-1], T[-1], ups[-1], 'out', 'gutter')

    elif key == 'outlet':
        L = s['outlet_len']
        so, _ = sweep_solid([(0, 0, 0), (L, 0, 0)], Z, gutter_band(s), start_tag='in', end_tag='out')
        sol.append(so)
        a, zmin = gutter_low_point(s)
        top = (L / 2, a, zmin + s['g_wall'] * 0.5)
        bot = (L / 2, a, zmin - SPIGOT_LEN)
        o, i = pipe_rings(s)
        sp, _ = sweep_solid([top, bot], Y, o, i, end_tag='down')
        sol.append(sp)
        ports['in'] = port((0, 0, 0), NX, Z, 'in', 'gutter')
        ports['out'] = port((L, 0, 0), X, Z, 'out', 'gutter')
        ports['down'] = port(bot, NZ, Y, 'out', 'pipe')

    elif key == 'stopend':
        g = fit_gap(s)
        t = s['g_wall'] * fix_mult(s)
        so, _ = sweep_solid([(-STOPEND_SLEEVE, 0, 0), (0, 0, 0)], Z, gutter_band(s, grow=g, thick=t))
        sol.append(so)
        outer = offset_open(gutter_outer(s['g_profile'], s['g_width'], s['g_depth']), -g - t)
        plate, _ = sweep_solid([(0, 0, 0), (max(3.0, t * 1.5), 0, 0)], Z, outer)
        sol.append(plate)
        ports['in'] = port((0, 0, 0), NX, Z, 'in', 'gutter')

    elif key in ('union', 'bracket'):
        bd = bracket_dims(s)
        g = bd['gap']
        L = UNION_LEN if key == 'union' else bd['len']
        t = bd['t']
        x0, x1 = -L / 2 - s['offset'], L / 2 - s['offset']
        so, _ = sweep_solid([(x0, 0, 0), (x1, 0, 0)], Z, gutter_band(s, grow=g, thick=t), end_tag='copy')
        sol.append(so)
        if key == 'bracket':
            yb = s['g_width'] / 2 + g + t
            a, zmin = gutter_low_point(s)
            zb = zmin - g - t
            zlow = zb - bd['arm']
            sol.append(box_solid(x0 - 10, x1 + 10, yb, yb + bd['plate'], min(zb - 10, zlow),
                                 s['g_depth'] + 10))
            if s.get('chunky'):
                # one solid block: fill everything behind and under the gutter down to the arm
                sleeve = offset_open(gutter_outer(s['g_profile'], s['g_width'], s['g_depth']), -g - t)
                back = [sleeve[0]]
                for p in sleeve[1:]:
                    q = back[-1]
                    if p[0] > a + 1e-9:
                        back.append(p)
                        continue
                    f = (q[0] - a) / ((q[0] - p[0]) or 1e-12)   # cut exactly under the low point
                    back.append((a, q[1] + (p[1] - q[1]) * f))
                    break
                while len(back) > 1 and abs(back[1][0] - yb) < 1e-9:
                    back.pop(0)                                  # straight back wall sits on the plate
                web = back + [(a, zlow), (yb, zlow)]
                if abs(web[0][0] - yb) > 1e-9 or abs(web[0][1] - zlow) < 1e-9:
                    web.append((yb, web[0][1]))
                clean = []
                for p in web:
                    if not clean or math.hypot(p[0] - clean[-1][0], p[1] - clean[-1][1]) > 1e-6:
                        clean.append(p)
                if math.hypot(clean[0][0] - clean[-1][0], clean[0][1] - clean[-1][1]) < 1e-6:
                    clean.pop()
                wsol, _ = sweep_solid([(x0, 0, 0), (x1, 0, 0)], Z, clean)
                sol.append(wsol)
            else:
                sol.append(box_solid(x0, x1, a, yb, zlow, zb))
        ports['in'] = port((0, 0, 0), NX, Z, 'in', 'gutter')

    elif key == 'pipe':
        L = s['length']
        o, i = pipe_rings(s)
        so, _ = sweep_solid([(0, 0, 0), (L, 0, 0)], Z, o, i, 'in', 'out')
        sol.append(so)
        ports['in'] = port((0, 0, 0), NX, Z, 'in', 'pipe')
        ports['out'] = port((L, 0, 0), X, Z, 'out', 'pipe')

    elif key in ('bend', 'shoe'):
        turn = math.radians(s['bend_turn'] if key == 'bend' else 67.5)
        d = bend_vector(s['bend_dir'])
        R = s['p_size'] * 0.8
        lead = SOCKET_LEN if key == 'bend' else 60.0
        tail = SOCKET_LEN if key == 'bend' else 50.0
        segs = max(4, int(math.degrees(turn) / 7.5))
        arc = arc_path((lead, 0, 0), X, d, R, turn, segs)
        Tend = v_add(v_mul(X, math.cos(turn)), v_mul(d, math.sin(turn)))
        path = [(0, 0, 0)] + arc + [v_add(arc[-1], v_mul(Tend, tail))]
        o, i = pipe_rings(s)
        so, (T, ups, _) = sweep_solid(path, Z, o, i, 'in', 'out' if key == 'bend' else None)
        sol.append(so)
        ports['in'] = port((0, 0, 0), NX, Z, 'in', 'pipe')
        if key == 'bend':
            ports['out'] = port(path[-1], T[-1], ups[-1], 'out', 'pipe')

    elif key == 'branch':
        Lm = max(250.0, s['p_size'] * 3.5)
        o, i = pipe_rings(s)
        so, _ = sweep_solid([(0, 0, 0), (Lm, 0, 0)], Z, o, i, 'in', 'out')
        sol.append(so)
        turn = math.radians(s['bend_turn'])
        d = bend_vector(s['bend_dir'])
        # the branch arm angles back up against the flow, like a real Y branch
        dirb = v_add(v_mul(NX, math.cos(turn)), v_mul(d, math.sin(turn)))
        start = (Lm * 0.6, 0, 0)
        end = v_add(start, v_mul(dirb, s['branch_len']))
        r = rot_between(X, dirb)
        upb = rotate(Z, r[0], r[1]) if r else Z
        sb, (T, ups, _) = sweep_solid([start, end], upb, o, i, None, 'branch')
        sol.append(sb)
        ports['in'] = port((0, 0, 0), NX, Z, 'in', 'pipe')
        ports['out'] = port((Lm, 0, 0), X, Z, 'out', 'pipe')
        ports['branch'] = port(end, T[-1], ups[-1], 'out', 'pipe')

    elif key in ('socket', 'clip'):
        m = fix_mult(s)
        L = SOCKET_COUPLER_LEN if key == 'socket' else CLIP_LEN * (1 + (m - 1) / 2)
        g, t = (fit_gap(s), s['p_wall'] * 1.5 * m) if key == 'socket' else (fit_gap(s, 0.3), 3.0 * m)
        x0, x1 = -L / 2 - s['offset'], L / 2 - s['offset']
        o, i = pipe_rings(s, grow=g, thick=t)
        so, _ = sweep_solid([(x0, 0, 0), (x1, 0, 0)], Z, o, i, None, 'copy')
        sol.append(so)
        if key == 'clip':
            r_out = s['p_size'] / 2 + g + t
            hw = 8 * m
            sol.append(box_solid(x0, x1, -hw, hw, r_out - 1, r_out + 35))
            sol.append(box_solid(x0 - 10, x1 + 10, -25 - hw, 25 + hw, r_out + 35, r_out + 35 + 4 * m))
        ports['in'] = port((0, 0, 0), NX, Z, 'in', 'pipe')
    else:
        raise ValueError("Unknown part: %s" % key)
    return sol, ports


# ---------------------------------------------------------------------------
# Placing a part against an open end
# ---------------------------------------------------------------------------
def frame_matrix(n, u):
    n = v_norm(n)
    u = v_norm(v_sub(u, v_mul(n, v_dot(u, n))))
    return n, u, v_cross(n, u)


def placement(part_port, target, scale, mirror):
    """Returns a function mapping local points (mm) to world points so that the
    part's port sits on the target port, facing it."""
    pc, pn, pu = part_port['c'], part_port['n'], part_port['u']
    if mirror:
        pc, pn, pu = (pc[0], -pc[1], pc[2]), (pn[0], -pn[1], pn[2]), (pu[0], -pu[1], pu[2])
    a1, a2, a3 = frame_matrix(pn, pu)
    b1, b2, b3 = frame_matrix(v_mul(target['n'], -1.0), target['u'])
    tc = target['c']

    def to_world(p):
        if mirror:
            p = (p[0], -p[1], p[2])
        q = v_mul(v_sub(p, pc), scale)
        x, y, z = v_dot(q, a1), v_dot(q, a2), v_dot(q, a3)
        return v_add(tc, v_add(v_add(v_mul(b1, x), v_mul(b2, y)), v_mul(b3, z)))

    def vec(v):
        if mirror:
            v = (v[0], -v[1], v[2])
        x, y, z = v_dot(v, a1), v_dot(v, a2), v_dot(v, a3)
        return v_add(v_add(v_mul(b1, x), v_mul(b2, y)), v_mul(b3, z))

    return to_world, vec


def free_target(system, wall_deg=0.0):
    """Where a part goes when no open end is selected: at the origin, gutters
    running along +X with the wall behind (+Y), downpipes running down.
    wall_deg turns the whole thing about the vertical so the wall is on another side."""
    a = math.radians(wall_deg)
    if system == 'gutter':
        return {'c': (0.0, 0.0, 0.0), 'n': rotate(X, Z, a), 'u': Z, 'role': 'out', 'sys': 'gutter'}
    return {'c': (0.0, 0.0, 0.0), 'n': NZ, 'u': rotate(Y, Z, a), 'role': 'out', 'sys': 'pipe'}


def plan_part(key, s, target, free=False):
    """Builds the part and places it on target. Returns (world solids, port data per tag).
    free=True: nothing is joined, so every end of the part stays open for joining."""
    solids, ports = build_part(key, s)
    scale = 0.001        # sizes are in mm; IngeTrazo always stores geometry in metres
    # join with the part's own 'in' end, unless the target is the START of a run,
    # then use the part's 'out' end so the run carries on backwards
    use = 'in'
    if target['role'] == 'in' and 'out' in ports:
        use = 'out'
    mirror = (ports[use]['role'] == 'in') == (target['role'] == 'in')
    to_world, vec = placement(ports[use], target, scale, mirror)

    world = []
    for so in solids:
        w = Solid()
        for pts, tag in so.faces:
            wp = [to_world(p) for p in pts]
            w.add(list(reversed(wp)) if mirror else wp, tag)
        w.fix_winding()
        world.append(w)

    tags = {}
    for name, pd in ports.items():
        if name == use and not free:
            continue
        tags[name] = {'c': list(to_world(pd['c'])), 'n': list(v_norm(vec(pd['n']))),
                      'u': list(v_norm(vec(pd['u']))), 'role': pd['role'], 'sys': pd['sys']}
    # parts that sit over a joint pass the original end on, so you can carry on from them
    if not free:
        tags['copy'] = {k: (list(v) if isinstance(v, tuple) else v) for k, v in target.items()
                        if k in ('c', 'n', 'u', 'role', 'sys')}
    return world, tags


# ---------------------------------------------------------------------------
# Reading an open end from the selection
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


def _face_centroid(f):
    pts = [p for p in (_pos(v) for v in _items(getattr(f, 'vertices', None))) if p is not None]
    if not pts:
        return None
    n = float(len(pts))
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n, sum(p[2] for p in pts) / n)


def selected_port(selection):
    """The open end the user picked, or None. Follows the part if it has been
    moved or rotated since it was placed."""
    for e in selection:
        attrs = getattr(e, 'attrs', None)
        if not isinstance(attrs, dict) or PORT_KEY not in attrs:
            continue
        d = dict(attrs[PORT_KEY])
        c, n, u = tuple(d['c']), tuple(d['n']), tuple(d['u'])
        moved = False
        cur = [p for p in (_pos(v) for v in _items(getattr(e, 'vertices', None))) if p is not None]
        if d.get('fp') and d.get('fi') and len(cur) > max(d['fi']):
            old = [tuple(p) for p in d['fp']]
            new = [cur[i] for i in d['fi']]
            same = all(abs(v_len(v_sub(old[i], old[j])) - v_len(v_sub(new[i], new[j])))
                       < 1e-6 * (1 + v_len(v_sub(old[i], old[j]))) for i, j in ((0, 1), (0, 2), (1, 2)))
            if same:
                fo, fn = _frame3(*old), _frame3(*new)

                def rot(v):
                    return v_add(v_add(v_mul(fn[0], v_dot(v, fo[0])), v_mul(fn[1], v_dot(v, fo[1]))),
                                 v_mul(fn[2], v_dot(v, fo[2])))
                c = v_add(new[0], rot(v_sub(c, old[0])))
                n, u = rot(n), rot(u)
                moved = True
        if not moved:
            fc = _face_centroid(e)
            if fc is not None and d.get('fc'):
                c = v_add(c, v_sub(fc, tuple(d['fc'])))
        d['c'], d['n'], d['u'] = c, n, u
        d.pop('_mine', None)
        return d
    return None


def _frame3(a, b, c):
    e1 = v_norm(v_sub(b, a))
    w = v_sub(c, a)
    e2 = v_norm(v_sub(w, v_mul(e1, v_dot(w, e1))))
    return e1, e2, v_cross(e1, e2)


def same_end(a, b):
    return (v_len(v_sub(tuple(a['c']), tuple(b['c']))) < 1e-7
            and v_dot(tuple(a['n']), tuple(b['n'])) > 0.999)


def make_target(d, vals, label, end):
    """An open end of a part just added, ready to join the next part onto."""
    t = dict(d)
    t['c'], t['n'], t['u'] = tuple(t['c']), tuple(t['n']), tuple(t['u'])
    keys = GUTTER_KEYS if t['sys'] == 'gutter' else PIPE_KEYS
    t['settings'] = {k: vals[k] for k in keys}
    t['units'] = 'm'
    t['label'] = label
    t['end'] = end
    return t


def scene_ports(scene):
    """Every open-end tag still in the model: faces of the scene and of all its groups."""
    out, seen = [], set()

    def walk(e, depth):
        if e is None or id(e) in seen or depth > 60:
            return
        seen.add(id(e))
        m = getattr(e, 'mesh', None)
        for src in ((m,) if m is not None else ()) + (e,):
            if src is not e and id(src) in seen:
                continue
            seen.add(id(src))
            for f in _items(getattr(src, 'faces', None)):
                a = getattr(f, 'attrs', None)
                if isinstance(a, dict) and PORT_KEY in a:
                    out.append(a[PORT_KEY])
        for ch in _items(getattr(e, 'groups', None)) + _items(getattr(e, 'children', None)):
            walk(ch, depth + 1)
    walk(scene, 0)
    return out


def end_in_scene(t, ports):
    try:
        c, n = tuple(t['c']), tuple(t['n'])
    except Exception:
        return True
    for p in ports:
        try:
            if v_len(v_sub(tuple(p['c']), c)) < 1e-6 and v_dot(tuple(p['n']), n) > 0.999:
                return True
        except Exception:
            continue
    return False


class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))


# ---------------------------------------------------------------------------
# Presets (one .json file per preset)
# ---------------------------------------------------------------------------
def _safe_name(name):
    return "".join(c if c.isalnum() or c in " -_+." else "_" for c in name).strip() or "preset"


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
# Starting on a wall, and spacing brackets / clips
# ---------------------------------------------------------------------------
def wall_info(face, flip=False):
    """Reads a picked wall face: which way it faces, its top and its two ends."""
    pts = [p for p in (_pos(v) for v in _items(getattr(face, 'vertices', None))) if p is not None]
    if len(pts) < 3:
        raise ValueError("That face has no corners I can read.")
    n = _newell(pts)
    if flip:
        n = v_mul(n, -1.0)
    if abs(n[2]) > 0.35:
        raise ValueError("Pick an upright wall face (this one is a floor, roof or ceiling).")
    n = v_norm((n[0], n[1], 0.0))
    run = v_norm(v_cross(Z, n))          # along the wall, so the wall is behind the gutter
    ss = [v_dot(p, run) for p in pts]
    return {'n': n, 'run': run, 's0': min(ss), 's1': max(ss),
            'top': max(p[2] for p in pts), 'd': max(v_dot(p, n) for p in pts)}


def wall_target(w, s):
    """Start of a gutter along the top of the wall. Returns (target, wall length in mm)."""
    outer = gutter_outer(s['g_profile'], s['g_width'], s['g_depth'])
    top = max(p[1] for p in outer)
    back = max(p[0] for p in outer)                     # back of the gutter, from its centre
    mm = 0.001
    # far enough out for the fascia brackets to sit on the wall, plus any extra gap
    bd = bracket_dims(s)
    dist = w['d'] + (bd['gap'] + bd['t'] + bd['plate'] + s['wall_gap'] + back) * mm
    s0 = w['s0'] - s['over_left'] * mm
    z = w['top'] - (s['drop'] + top) * mm
    c = v_add(v_add(v_mul(w['run'], s0), v_mul(w['n'], dist)), (0.0, 0.0, z))
    length = (w['s1'] - w['s0']) / mm + s['over_left'] + s['over_right']
    if length < 10.0:
        raise ValueError("The left and right end settings leave no gutter on this wall "
                         "(%.0f mm). Make them less negative." % length)
    return ({'c': c, 'n': w['run'], 'u': Z, 'role': 'out', 'sys': 'gutter',
             'label': "the selected wall", 'end': 'top'}, length)


def fixing_positions(L, spacing, margin=150.0):
    """Even positions along a length L: near each end and never more than spacing apart."""
    if L <= 2 * margin:
        return [L / 2.0]
    inner = L - 2 * margin
    k = max(1, int(math.ceil(inner / max(spacing, 1.0) - 1e-9)))
    return [margin + inner * i / k for i in range(k + 1)]


def fixings(key, s, out_end):
    """Fascia brackets along a gutter length, or clips along a downpipe length."""
    fkey = 'bracket' if key == 'gutter' else 'clip'
    spacing = s['g_spacing'] if key == 'gutter' else s['p_spacing']
    L = s['length']
    world = []
    pos = fixing_positions(L, spacing)
    for x in pos:
        w, _ = plan_part(fkey, dict(s, offset=L - x), out_end)
        world.extend(w)
    return world, len(pos)


def size_text(key, s):
    if PART_INFO[key][1] == 'gutter':
        return "%s %g" % (dict((k, l) for l, k in GUTTER_PROFILES)[s['g_profile']], s['g_width'])
    return "%s %g" % (dict((k, l) for l, k in PIPE_TYPES)[s['p_type']], s['p_size'])


def group_name(key, s):
    name = "%s - %s" % (PART_INFO[key][0], size_text(key, s))
    if key in ('gutter', 'pipe'):
        name += " x %g mm" % s['length']
    return name


# ---------------------------------------------------------------------------
# Live preview of the chosen part
# ---------------------------------------------------------------------------
VIEW_DIR = v_norm((-0.55, 0.8, -0.5))          # looking from the front right, above
LIGHT = v_norm((0.35, -0.55, 0.8))


def _newell(pts):
    nx = ny = nz = 0.0
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    return v_norm((nx, ny, nz))


def preview_items(key, vals):
    """Flat-shaded 2D polygons of the part (plus the wall, and the part it fits
    over, drawn faintly). Returns [(depth, [(x, y)...], (r, g, b), alpha)] far to near."""
    system = PART_INFO[key][1]
    s = dict(vals)
    ref = s['g_width'] if system == 'gutter' else s['p_size']
    s['length'] = min(s['length'], 4.0 * ref)
    s['leg'] = min(s['leg'], 2.5 * ref)
    s['branch_len'] = min(s['branch_len'], 3.0 * ref)
    s['offset'] = 0.0
    start = free_target(system, s.get('wall_side', 0.0))
    ghost = []
    target, free = start, True
    if key in OVERLAY_PARTS or key == 'stopend':
        host = 'gutter' if system == 'gutter' else 'pipe'
        hw, ht = plan_part(host, dict(s, length=2.5 * ref), start, free=True)
        ghost = hw
        target = make_target(ht['out'], s, '', 'out')
        free = False
    main, _ = plan_part(key, s, target, free=free)

    right = v_norm(v_cross(VIEW_DIR, Z))
    up = v_cross(right, VIEW_DIR)
    items = []

    def add_solids(solids, rgb, lo, hi):
        for so in solids:
            for pts, _ in so.faces:
                n = _newell(pts)
                if v_dot(n, VIEW_DIR) >= 0:
                    continue                      # facing away
                k = lo + (hi - lo) * max(0.0, v_dot(n, LIGHT))
                depth = sum(v_dot(p, VIEW_DIR) for p in pts) / len(pts)
                items.append((depth, [(v_dot(p, right), -v_dot(p, up)) for p in pts],
                              tuple(int(c * k) for c in rgb), 255))

    add_solids(ghost, (215, 220, 225), 0.75, 1.0)
    add_solids(main, (110, 150, 175), 0.45, 1.0)

    # the wall, as a see-through panel
    allp = [p for so in main + ghost for f, _ in so.faces for p in f]
    if allp:
        w = rotate(Y, Z, math.radians(s.get('wall_side', 0.0)))
        h = v_cross(Z, w)
        gap = 0.15 * ref * 0.001
        dw = max(v_dot(p, w) for p in allp) + gap
        h0, h1 = min(v_dot(p, h) for p in allp) - gap, max(v_dot(p, h) for p in allp) + gap
        z0, z1 = min(p[2] for p in allp) - gap, max(p[2] for p in allp) + gap
        quad = [v_add(v_add(v_mul(w, dw), v_mul(h, a)), (0, 0, z)) for a, z in
                ((h0, z0), (h1, z0), (h1, z1), (h0, z1))]
        depth = sum(v_dot(p, VIEW_DIR) for p in quad) / 4
        items.append((depth, [(v_dot(p, right), -v_dot(p, up)) for p in quad], (205, 170, 120), 90))
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

EDDY_TIPS = {'@lst': 'The parts to choose from. Pick one to set it up.',
 '@cb_preset': 'Ready-made settings. Pick one and the whole window is filled in.'}
EDDY_TIPS_END = None


class PartPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(260, 190)
        self.items = []

    def show_part(self, key, vals):
        try:
            self.items = preview_items(key, vals)
        except Exception as e:
            self.items = []
            print("%s preview: %s" % (PLUGIN_NAME, e))
        self.update()

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen
        from PySide6.QtCore import QPointF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(248, 248, 246))
        if self.items:
            xs = [x for _, pts, _, _ in self.items for x, _ in pts]
            ys = [y for _, pts, _, _ in self.items for _, y in pts]
            w, h = self.width() - 16, self.height() - 16
            sc = min(w / ((max(xs) - min(xs)) or 1), h / ((max(ys) - min(ys)) or 1))
            ox = 8 + (w - (max(xs) - min(xs)) * sc) / 2 - min(xs) * sc
            oy = 8 + (h - (max(ys) - min(ys)) * sc) / 2 - min(ys) * sc
            for _, pts, rgb, alpha in self.items:
                col = QColor(rgb[0], rgb[1], rgb[2], alpha)
                p.setBrush(col)
                p.setPen(QPen(col.darker(115), 0.6))
                p.drawPolygon(QPolygonF([QPointF(ox + x * sc, oy + y * sc) for x, y in pts]))
        p.end()

# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------
class DrainDialog(QDialog):
    CUSTOM = "-- Custom --"

    def __init__(self, cur, target, viewport, tool):
        super().__init__(viewport)
        self.setWindowTitle(PLUGIN_NAME)
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.target = target
        self.open_ends = []        # every open end added in this window that isn't joined yet
        self.history = []          # window state before each part, for stepping back after a delete
        self.wall = None           # a picked wall the first gutter goes on
        self.wall_face = None
        self.user_presets = load_presets()
        lay = QVBoxLayout(self)

        self.lbl_target = QLabel()
        self.lbl_target.setWordWrap(True)
        self.lbl_target.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl_target)

        self.cb_solid = QCheckBox("Solid (for 3D printing) - no hollow inside")
        self.cb_solid.setChecked(bool(cur.get('solid')))
        self.cb_solid.setToolTip("Fills the gutters and pipes in, so small-scale prints come out "
                                 "strong. Fit-over parts (unions, sockets, clips) stay as sleeves.")
        lay.addWidget(self.cb_solid)


        # ---- presets ----
        row = QHBoxLayout()
        self.cb_preset = QComboBox()
        b_save, b_del, b_open = QPushButton("Save"), QPushButton("Delete"), QPushButton("Open folder")
        b_save.setToolTip("Updates the preset you have open (no typing). For a new preset, use Save as.")
        b_saveas = QPushButton("Save as...")
        self.btn_preset_save = b_save
        row.addWidget(QLabel("Preset:"))
        row.addWidget(self.cb_preset, 1)
        for b in (b_save, b_saveas, b_del, b_open):
            row.addWidget(b)
        lay.addLayout(row)
        b_save.clicked.connect(self.save_preset)
        b_saveas.clicked.connect(lambda: self.save_preset_as())
        b_del.clicked.connect(self.delete_preset)
        b_open.clicked.connect(self.open_folder)

        # ---- part list ----
        self.lst = QListWidget()
        self.lst.setMinimumHeight(260)
        for header, system in (("GUTTER", 'gutter'), ("DOWNPIPE", 'pipe')):
            h = QListWidgetItem(header)
            h.setFlags(h.flags() & ~QtItemFlags.selectable & ~QtItemFlags.enabled)
            self.lst.addItem(h)
            for key, label, sysk, _ in PARTS:
                if sysk != system:
                    continue
                it = QListWidgetItem("   " + label)
                it.setData(QtRole.user, key)
                self.lst.addItem(it)
                if key == cur['part']:
                    self.lst.setCurrentItem(it)
        lay.addWidget(self.lst)

        def mm_spin(val, lo=0.1, hi=100000.0, suffix=" mm", dec=1):
            sp = QDoubleSpinBox()
            sp.setDecimals(dec)
            sp.setRange(lo, hi)
            sp.setSuffix(suffix)
            sp.setValue(val)
            return sp

        # ---- gutter ----
        gb = QGroupBox("Gutter")
        gf = QFormLayout(gb)
        self.cb_gprof = QComboBox()
        for label, key in GUTTER_PROFILES:
            self.cb_gprof.addItem(label, key)
            if key == cur['g_profile']:
                self.cb_gprof.setCurrentIndex(self.cb_gprof.count() - 1)
        self.sp_gw = mm_spin(cur['g_width'], 10.0)
        self.sp_gd = mm_spin(cur['g_depth'], 5.0)
        self.sp_gt = mm_spin(cur['g_wall'], 0.5, 50.0)
        gf.addRow("Profile:", self.cb_gprof)
        gf.addRow("Width:", self.sp_gw)
        gf.addRow("Depth:", self.sp_gd)
        gf.addRow("Wall thickness:", self.sp_gt)

        # ---- downpipe ----
        pb = QGroupBox("Downpipe")
        pf = QFormLayout(pb)
        self.cb_ptype = QComboBox()
        for label, key in PIPE_TYPES:
            self.cb_ptype.addItem(label, key)
            if key == cur['p_type']:
                self.cb_ptype.setCurrentIndex(self.cb_ptype.count() - 1)
        self.sp_ps = mm_spin(cur['p_size'], 10.0)
        self.sp_pt = mm_spin(cur['p_wall'], 0.5, 50.0)
        self.lbl_ps = QLabel()
        pf.addRow("Shape:", self.cb_ptype)
        pf.addRow(self.lbl_ps, self.sp_ps)
        pf.addRow("Wall thickness:", self.sp_pt)

        # ---- part sizes ----
        sb = QGroupBox("This part")
        sf = QFormLayout(sb)
        self.preview = PartPreview()
        sf.addRow(self.preview)
        cap = QLabel("Brown panel = the wall. Pale grey = the part it fits over.")
        cap.setStyleSheet("color: gray; font-size: 9pt;")
        sf.addRow(cap)
        self.sp = {
            'length': mm_spin(cur['length'], 1.0),
            'outlet_len': mm_spin(cur['outlet_len'], 20.0),
            'leg': mm_spin(cur['leg'], 10.0),
            'bend_turn': mm_spin(cur['bend_turn'], 1.0, 135.0, " deg"),
            'branch_len': mm_spin(cur['branch_len'], 20.0),
            'offset': mm_spin(cur['offset'], 0.0),
        }
        self.sp['bend_turn'].setToolTip("How far the pipe turns. A 112.5 deg offset bend turns 67.5; "
                                        "a 92.5 deg bend turns 87.5; a 135 deg bend turns 45.")
        self.sp['offset'].setToolTip("0 = centred on the end you selected. Larger values slide it "
                                     "back along the part.")
        self.cb_dir = QComboBox()
        for label, deg in BEND_DIRS:
            self.cb_dir.addItem(label, deg)
            if abs(deg - cur['bend_dir']) < 1e-6:
                self.cb_dir.setCurrentIndex(self.cb_dir.count() - 1)
        labels = {'length': "Length:", 'outlet_len': "Outlet length:", 'leg': "Leg length (each side):",
                  'bend_turn': "Turn angle:", 'branch_len': "Branch length:",
                  'offset': "Distance back from the end:"}
        self.rows = {}
        for k in ('length', 'outlet_len', 'leg', 'bend_turn', 'branch_len', 'offset'):
            lab = QLabel(labels[k])
            sf.addRow(lab, self.sp[k])
            self.rows[k] = (lab, self.sp[k])
        lab = QLabel("Direction:")
        sf.addRow(lab, self.cb_dir)
        self.rows['bend_dir'] = (lab, self.cb_dir)

        self.cb_wall = QComboBox()
        for label, deg in WALL_SIDES:
            self.cb_wall.addItem(label, deg)
            if abs(deg - cur.get('wall_side', 0.0)) < 1e-6:
                self.cb_wall.setCurrentIndex(self.cb_wall.count() - 1)
        self.cb_wall.setToolTip("Which side the wall is on when a new run starts at the origin. "
                                "Parts joined onto an end follow that end instead.")
        sf.addRow("New run - wall is:", self.cb_wall)


        # ---- start on a wall ----
        wb = QGroupBox("Start a gutter on a wall")
        wf = QFormLayout(wb)
        b_wall = QPushButton("Use selected wall")
        b_wall.setToolTip("Select a wall face, then click this. The next gutter part runs along "
                          "the top of that wall.")
        b_wall.clicked.connect(self.use_selected_wall)
        wf.addRow(b_wall)
        self.sp_drop = mm_spin(cur['drop'], 0.0)
        self.sp_drop.setToolTip("How far the top of the gutter sits below the top of the wall.")
        self.sp_wgap = mm_spin(cur['wall_gap'], 0.0)
        self.sp_wgap.setToolTip("0 = fascia brackets sit flat on the wall. More moves the gutter out.")
        self.sp_ovl = mm_spin(cur['over_left'], -100000.0)
        self.sp_ovr = mm_spin(cur['over_right'], -100000.0)
        self.sp_ovl.setToolTip("How far the gutter runs past the left end of the wall, as you look "
                               "at it from outside. Negative stops short of the end, leaving room "
                               "for a running outlet, angle or stop end.")
        self.sp_ovr.setToolTip("Same for the right end. Negative stops short of the end.")
        self.cb_fit = QCheckBox("Gutter length = wall length")
        self.cb_fit.setChecked(cur['fit_wall'])
        self.cb_flip = QCheckBox("Wrong side? Put it on the other side of the wall")
        self.cb_flip.setChecked(cur['wall_flip'])
        self.cb_flip.toggled.connect(self.reread_wall)
        wf.addRow("Below top of wall:", self.sp_drop)
        wf.addRow("Extra gap from wall:", self.sp_wgap)
        wf.addRow("Past left end:", self.sp_ovl)
        wf.addRow("Past right end:", self.sp_ovr)
        wf.addRow(self.cb_fit)
        wf.addRow(self.cb_flip)

        # ---- brackets and clips ----
        fb = QGroupBox("Brackets and clips")
        ff = QFormLayout(fb)
        self.cb_fix = QCheckBox("Add them evenly with every gutter / downpipe length")
        self.cb_fix.setChecked(cur['auto_fix'])
        self.sp_gsp = mm_spin(cur['g_spacing'], 100.0)
        self.sp_psp = mm_spin(cur['p_spacing'], 100.0)
        self.sp_gsp.setToolTip("Most a fascia bracket can be from the next one. One also goes "
                               "near each end.")
        self.sp_psp.setToolTip("Most a pipe clip can be from the next one. One also goes near each end.")
        ff.addRow(self.cb_fix)
        ff.addRow("Gutter brackets at most:", self.sp_gsp)
        ff.addRow("Pipe clips at most:", self.sp_psp)
        self.cb_chunky = QCheckBox("Chunky fittings (for 3D printing)")
        self.cb_chunky.setChecked(cur['chunky'])
        self.cb_chunky.setToolTip("Makes every bracket, clip, union, socket and stop end thicker "
                                  "and wider so they survive printing at small scales.")
        self.sp_chunk = mm_spin(cur['chunk_mult'], 1.0, 10.0, " x", 1)
        self.sp_chunk.setToolTip("How many times thicker than real fittings.")
        ff.addRow(self.cb_chunky)
        ff.addRow("   Thicker by:", self.sp_chunk)
        self.cb_chunky.toggled.connect(self.sp_chunk.setEnabled)
        self.sp_chunk.setEnabled(self.cb_chunky.isChecked())
        self.cb_chunky.toggled.connect(self.sync)
        self.sp_chunk.valueChanged.connect(self.sync)
        self.cb_fix.toggled.connect(lambda on: (self.sp_gsp.setEnabled(on), self.sp_psp.setEnabled(on)))
        self.sp_gsp.setEnabled(self.cb_fix.isChecked())
        self.sp_psp.setEnabled(self.cb_fix.isChecked())

        cols = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(gb)
        left.addWidget(pb)
        cols.addLayout(left)
        cols.addWidget(sb)
        right = QVBoxLayout()
        right.addWidget(wb)
        right.addWidget(fb)
        right.addStretch(1)
        cols.addLayout(right)
        lay.addLayout(cols)

        brow = QHBoxLayout()
        self.b_add = QPushButton("Add part")
        self.b_add.setDefault(True)
        b_sel = QPushButton("Use selected end")
        b_new = QPushButton("Start at the origin")
        b_close = QPushButton("Close")
        b_sel.setToolTip("Select the open end face of any placed part, then click this to join onto it.")
        for b in (self.b_add, b_sel, b_new):
            brow.addWidget(b)
        brow.addStretch(1)
        brow.addWidget(b_close)
        lay.addLayout(brow)
        self.b_add.clicked.connect(lambda: self.tool.add_from_dialog(self))
        b_sel.clicked.connect(self.use_selected_end)
        b_new.clicked.connect(self.start_at_origin)
        b_close.clicked.connect(self.close)
        self.set_target(target)

        self.refresh_presets()
        self.cb_preset.currentIndexChanged.connect(self.apply_preset)
        self.lst.currentItemChanged.connect(self.sync)
        self.cb_gprof.currentIndexChanged.connect(self.sync)
        self.sp_gw.valueChanged.connect(self.sync)
        self.cb_ptype.currentIndexChanged.connect(self.sync)
        self.cb_solid.toggled.connect(self.sync)
        self.cb_wall.currentIndexChanged.connect(self.sync)
        self.cb_dir.currentIndexChanged.connect(self.sync)
        for w in [self.sp_gd, self.sp_gt, self.sp_ps, self.sp_pt] + list(self.sp.values()):
            w.valueChanged.connect(self.sync)
        self.sync()

    # ---- helpers ----
    def part(self):
        it = self.lst.currentItem()
        k = it.data(QtRole.user) if it is not None else None
        return k or 'gutter'

    def sync(self, *_):
        part = self.part()
        if part != getattr(self, '_last_part', part) and part == 'shoe':
            self.cb_dir.blockSignals(True)
            self.cb_dir.setCurrentIndex(1)      # shoes kick away from the wall
            self.cb_dir.blockSignals(False)
        self._last_part = part
        uses = PART_INFO[part][2]
        for k, (lab, w) in self.rows.items():
            on = k in uses
            lab.setVisible(on)
            w.setVisible(on)
        half = self.cb_gprof.currentData() == 'halfround'
        self.sp_gd.setEnabled(not half)
        if half:
            self.sp_gd.setValue(self.sp_gw.value() / 2)
        self.lbl_ps.setText("Side:" if self.cb_ptype.currentData() == 'square' else "Diameter:")
        if hasattr(self, 'preview'):
            self.preview.show_part(part, self.values())
        hollow = not self.cb_solid.isChecked()
        self.sp_gt.setToolTip("" if hollow else "Solid parts have no wall; this is only used "
                              "for fit-over parts such as unions and stop ends.")
        self.sp_pt.setToolTip(self.sp_gt.toolTip())

    def start_at_origin(self):
        self.wall = None
        self.wall_face = None
        self.set_target(None)

    def use_selected_wall(self):
        scene = getattr(self.viewport, 'scene', None)
        sel = list(getattr(scene, 'selection', None) or [])
        faces = [e for e in sel if hasattr(e, 'vertices') and
                 not (isinstance(getattr(e, 'attrs', None), dict) and PORT_KEY in e.attrs)]
        if not faces:
            QMessageBox.information(self, PLUGIN_NAME, "Select a wall face first, then click "
                                    "'Use selected wall'.")
            return
        self.wall_face = faces[0]
        self.reread_wall()

    def reread_wall(self, *_):
        if self.wall_face is None:
            return
        try:
            self.wall = wall_info(self.wall_face, self.cb_flip.isChecked())
        except ValueError as e:
            self.wall = None
            QMessageBox.information(self, PLUGIN_NAME, str(e))
            return
        self.set_target(None)

    def set_target(self, t, finished=False):
        self.target = t
        if t is None and getattr(self, 'wall', None):
            txt = "Next gutter part goes along the top of the selected wall."
        elif t is None:
            txt = ("Run finished. " if finished else "") + \
                  "Next part goes at the origin. Or select an open end and click 'Use selected end'."
        else:
            where = END_NAMES.get(t.get('end'), "open end")
            what = t.get('label') or ("gutter" if t['sys'] == 'gutter' else "downpipe")
            txt = ("Run finished, moving to the next open end. " if finished else "") + \
                  "Next part joins onto the %s of: %s" % (where, what)
        self.lbl_target.setText(txt)

    def remember(self):
        """The window's state just before a part is added, so it can step back to it
        if that part is later deleted or undone."""
        return {'target': self.target, 'open': list(self.open_ends),
                'wall': {k: getattr(self, k) for k in ('wall', 'wall_face', 'wall_dir')
                         if hasattr(self, k)}}

    def check_ends(self):
        """If parts added from this window have since been deleted or undone, go back to
        the end that is still in the model, as if they had never been added."""
        scene = getattr(self.viewport, 'scene', None)
        if scene is None:
            return False
        try:
            ports = scene_ports(scene)
        except Exception:
            return False

        def gone(e):
            return e is not None and e.get('_mine') and not end_in_scene(e, ports)

        changed = False
        while gone(self.target):
            changed = True
            if self.history:
                h = self.history.pop()
                self.target = h['target']
                self.open_ends = list(h['open'])
                for k, v in h['wall'].items():
                    setattr(self, k, v)
            else:
                self.target = None
        keep = [e for e in self.open_ends if not gone(e)]
        if len(keep) != len(self.open_ends):
            self.open_ends = keep
            changed = True
        if changed:
            self.set_target(self.target)
        return changed

    def changeEvent(self, e):
        try:
            from PySide6.QtCore import QEvent
            if e.type() == QEvent.ActivationChange and self.isActiveWindow():
                self.check_ends()
        except Exception:
            pass
        super().changeEvent(e)

    def use_selected_end(self):
        scene = getattr(self.viewport, 'scene', None)
        t = selected_port(list(getattr(scene, 'selection', None) or []))
        if t is None:
            QMessageBox.information(self, PLUGIN_NAME, "Select the open end face of a part placed "
                                    "by this plugin first, then click 'Use selected end'.")
            return
        self.set_values(t.get('settings') or {})
        self.set_target(t)

    def values(self):
        v = {'part': self.part(), 'units': 'm', 'solid': self.cb_solid.isChecked(),
             'wall_side': self.cb_wall.currentData(),
             'drop': self.sp_drop.value(), 'wall_gap': self.sp_wgap.value(),
             'over_left': self.sp_ovl.value(), 'over_right': self.sp_ovr.value(),
             'fit_wall': self.cb_fit.isChecked(),
             'chunky': self.cb_chunky.isChecked(), 'chunk_mult': self.sp_chunk.value(),
             'wall_flip': self.cb_flip.isChecked(), 'auto_fix': self.cb_fix.isChecked(),
             'g_spacing': self.sp_gsp.value(), 'p_spacing': self.sp_psp.value(),
             'g_profile': self.cb_gprof.currentData(), 'g_width': self.sp_gw.value(),
             'g_depth': self.sp_gd.value(), 'g_wall': self.sp_gt.value(),
             'p_type': self.cb_ptype.currentData(), 'p_size': self.sp_ps.value(),
             'p_wall': self.sp_pt.value(), 'bend_dir': self.cb_dir.currentData()}
        for k, w in self.sp.items():
            v[k] = w.value()
        return v

    def set_values(self, d):
        if 'solid' in d:
            self.cb_solid.setChecked(bool(d['solid']))
        for combo, key in ((self.cb_gprof, 'g_profile'), (self.cb_ptype, 'p_type')):
            if key in d:
                for i in range(combo.count()):
                    if combo.itemData(i) == d[key]:
                        combo.setCurrentIndex(i)
        for w, key in ((self.sp_gw, 'g_width'), (self.sp_gd, 'g_depth'), (self.sp_gt, 'g_wall'),
                       (self.sp_ps, 'p_size'), (self.sp_pt, 'p_wall')):
            if d.get(key) is not None:
                w.setValue(float(d[key]))
        for k, w in self.sp.items():
            if d.get(k) is not None:
                w.setValue(float(d[k]))
        if 'chunky' in d:
            self.cb_chunky.setChecked(bool(d['chunky']))
        for w, key in ((self.sp_drop, 'drop'), (self.sp_wgap, 'wall_gap'), (self.sp_ovl, 'over_left'),
                       (self.sp_ovr, 'over_right'), (self.sp_gsp, 'g_spacing'),
                       (self.sp_psp, 'p_spacing'), (self.sp_chunk, 'chunk_mult')):
            if d.get(key) is not None:
                w.setValue(float(d[key]))
        self.sync()

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
            self.set_values(p)

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


class QtItemFlags:
    selectable = None
    enabled = None


class QtRole:
    user = None


def _init_qt_constants():
    from PySide6.QtCore import Qt
    QtItemFlags.selectable = Qt.ItemIsSelectable
    QtItemFlags.enabled = Qt.ItemIsEnabled
    QtRole.user = Qt.UserRole


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
class GuttersDownpipesTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+G"
    description = "Gutters, downpipes and fittings that join onto each other, with presets."

    _saved = None
    _dialog = None          # the open window (kept so it stays open between parts)

    def on_activate(self, viewport):
        _init_qt_constants()
        scene = getattr(viewport, 'scene', None)
        target = selected_port(list(getattr(scene, 'selection', None) or []))

        dlg = GuttersDownpipesTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    if target:
                        dlg.set_values(target.get('settings') or {})
                        dlg.set_target(target)
                    else:
                        dlg.check_ends()
                    dlg.raise_()
                    dlg.activateWindow()
                    return
            except Exception:
                pass

        cur = dict(DEFAULTS)
        if GuttersDownpipesTool._saved:
            cur.update(GuttersDownpipesTool._saved)
        if target:
            cur.update(target.get('settings') or {})
            if PART_INFO[cur['part']][1] != target['sys']:
                cur['part'] = 'gutter' if target['sys'] == 'gutter' else 'pipe'

        dlg = DrainDialog(cur, target, viewport, self)
        GuttersDownpipesTool._dialog = dlg

        def closed(*_):
            GuttersDownpipesTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass

    def add_from_dialog(self, dlg):
        viewport = dlg.viewport
        vals = dlg.values()
        GuttersDownpipesTool._saved = dict(vals)
        key = vals['part']
        label, system = PART_INFO[key][0], PART_INFO[key][1]

        dlg.check_ends()           # parts deleted or undone since? join onto what is left
        before = dlg.remember()
        t = dlg.target
        free = t is None
        on_wall = False
        if t and t['sys'] != system:
            # e.g. a downpipe after a running outlet: use the outlet's spigot
            t = next((e for e in reversed(dlg.open_ends) if e['sys'] == system), None)
            if t is None:
                QMessageBox.warning(dlg, PLUGIN_NAME, "A %s part can't join onto a %s end. Select a "
                                    "matching end and click 'Use selected end', or start at the origin."
                                    % ("gutter" if system == 'gutter' else "downpipe",
                                       "gutter" if dlg.target['sys'] == 'gutter' else "downpipe"))
                return
            free = False
        if t is None:
            if dlg.wall and system == 'gutter':
                try:
                    t, wall_len = wall_target(dlg.wall, vals)
                except ValueError as e:
                    QMessageBox.warning(dlg, PLUGIN_NAME, str(e))
                    return
                if vals['fit_wall'] and key == 'gutter':
                    vals['length'] = wall_len
                on_wall = True
            else:
                t = free_target(system, vals['wall_side'])
        try:
            world, tags = plan_part(key, vals, t, free=free)
        except Exception as e:
            QMessageBox.warning(dlg, PLUGIN_NAME, "Could not build the part:\n%s" % e)
            return

        parts = [(group_name(key, vals), world, tags)]
        nfix = 0
        if vals['auto_fix'] and key in ('gutter', 'pipe') and 'out' in tags:
            fix_world, nfix = fixings(key, vals, make_target(tags['out'], vals, label, 'out'))
            if nfix:
                fkey = 'bracket' if key == 'gutter' else 'clip'
                parts.append(("%s x%d - %s" % ("Fascia brackets" if fkey == 'bracket' else "Pipe clips",
                                                nfix, size_text(fkey, vals)), fix_world, {}))
        if not self.add_to_scene(viewport, vals, None if (free or on_wall) else t, parts):
            return
        if on_wall:
            dlg.wall = None            # the wall has its gutter now

        # keep track of which open ends are still free
        if not free and not on_wall and key not in OVERLAY_PARTS:
            dlg.open_ends = [e for e in dlg.open_ends if not same_end(e, t)]
        ends = {name: make_target(d, vals, label, name) for name, d in tags.items() if name != 'copy'}
        for name in ('in', 'down', 'branch', 'out'):
            if name in ends:
                dlg.open_ends.append(ends[name])
        finished = False
        if key in OVERLAY_PARTS:
            nxt = None if (free or on_wall) else t      # sits over a joint: carry on from the same end
        elif 'out' in ends:
            nxt = ends['out']
        else:
            # stop end / shoe close this run: move on to the newest end still open
            finished = True
            nxt = dlg.open_ends[-1] if dlg.open_ends else None
        dlg.set_target(nxt, finished=finished)
        # mark the new ends that can be found in the model again, so the window can tell
        # if their part is deleted later
        try:
            ports = scene_ports(getattr(viewport, 'scene', None))
            for e in ends.values():
                if end_in_scene(e, ports):
                    e['_mine'] = True
        except Exception:
            pass
        dlg.history.append(before)

    def add_to_scene(self, viewport, vals, target, parts):
        """parts: list of (group name, world solids, port tags). One undo step for all."""
        stats = {'faces': 0, 'errors': 0, 'err': None, 'ports': 0}
        gset = {k: vals[k] for k in GUTTER_KEYS}
        pset = {k: vals[k] for k in PIPE_KEYS}
        tol = 1e-4 * 0.001

        def port_data(tags, tag, pts):
            d = dict(tags[tag])
            if tag == 'copy' and target:
                d = dict(target)
                d.pop('_mine', None)
                d['c'], d['n'], d['u'] = list(d['c']), list(d['n']), list(d['u'])
            sysk = d['sys']
            d['settings'] = dict(d.get('settings') or (gset if sysk == 'gutter' else pset))
            d['units'] = 'm'
            n = float(len(pts))
            d['fc'] = [sum(p[i] for p in pts) / n for i in range(3)]
            # three corners of the face, so the end can be found again after a rotate
            k = max(range(2, len(pts)), key=lambda j: v_len(v_cross(v_sub(pts[1], pts[0]),
                                                                    v_sub(pts[j], pts[0]))))
            d['fi'] = [0, 1, k]
            d['fp'] = [list(pts[0]), list(pts[1]), list(pts[k])]
            return d

        def mutate(scene):
            from core.mesh import Mesh
            from core.group import Group
            for name, world, tags in parts:
                mesh = Mesh()
                for so in world:
                    verts = {}

                    def vx(p):
                        k = (round(p[0] / tol), round(p[1] / tol), round(p[2] / tol))
                        if k not in verts:
                            verts[k] = VertexWrapper(*p)
                        return verts[k]

                    for pts, tag in so.faces:
                        try:
                            f = mesh.add_face([vx(p) for p in pts])
                            stats['faces'] += 1
                        except Exception as e:
                            stats['errors'] += 1
                            stats['err'] = e
                            continue
                        if tag and tag in tags and f is not None:
                            try:
                                f.attrs[PORT_KEY] = port_data(tags, tag, pts)
                                stats['ports'] += 1
                            except Exception:
                                pass
                if stats['faces'] == 0:
                    raise RuntimeError("No faces could be created (%s)." % stats['err'])
                g = Group(name)
                g.mesh = mesh
                _ed3d_organise(scene, g)
                if hasattr(scene, 'add_group'):
                    scene.add_group(g)
                elif hasattr(scene, 'groups') and isinstance(scene.groups, list):
                    scene.groups.append(g)
                else:
                    raise RuntimeError("Could not add the part to the scene.")

        try:
            viewport.history.execute(SnapshotImport(mutate))
        except Exception as e:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not add the part:\n%s" % e)
            return False
        viewport.notify_scene_changed()
        msg = "%s: %s, %d faces" % (PLUGIN_NAME, ", ".join(p[0] for p in parts), stats['faces'])
        print(msg)
        if stats['errors']:
            print("%s: %d face(s) failed. First error: %s" % (PLUGIN_NAME, stats['errors'], stats['err']))
        if stats['ports'] == 0 and len(parts[0][2]) > 1:
            print("%s: could not mark the open ends, so this part can't be joined onto." % PLUGIN_NAME)
        try:
            viewport.flash_status(msg, 3000)
        except Exception:
            pass
        return True


# ---------------------------------------------------------------------------
# Running from the Python console
# ---------------------------------------------------------------------------
def _find_viewport():
    from PySide6.QtWidgets import QApplication
    for w in QApplication.allWidgets():
        if hasattr(w, 'scene') and hasattr(w, 'history') and hasattr(w, 'notify_scene_changed'):
            return w
    return None


def run(viewport=None):
    """Console entry point: optionally select an open end, then call run()."""
    viewport = viewport or _find_viewport()
    if viewport is None:
        print("%s: could not find the viewport. Call run(<your viewport>) instead." % PLUGIN_NAME)
        return
    GuttersDownpipesTool().on_activate(viewport)
