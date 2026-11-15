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
Or draw lines where the gutters and downpipes go, select them, and the whole lot is built
along them: angles, outlets, unions, stop ends, bends, sockets, brackets and clips.
Or mark the runs with the plugin's own thick line (Mark the run), easy to see on a detailed
building, and build along those.
Version 3: Mark the run - a thick, coloured marker line you can set the size and colour of.
Version 4: arrow keys lock the marker line to an axis (Right = red, Left = green, Up = blue,
Down = free); everything built along lines goes into one group.
Version 5: the window gets out of the way while you mark the runs, and comes back on Esc.
Version 6: smaller preview and key, so the whole window is smaller.
Version 7: Esc ends the line you're on (a second Esc stops marking); the marker snaps to the
ends of lines you've marked and onto them, so a downpipe can start right on the gutter.
Version 8: Esc, Enter, Backspace and the arrow keys are caught by the plugin while marking,
so IngeTrazo can't take them first (Esc wasn't letting go of the line).
Version 9: a downpipe drawn straight down from a gutter on the fascia gets a swan neck (two
bends) that takes it back to the wall under the eaves, then down the wall on its clips; the
clips sit on the front of the bricks (Brick & Block Studio), not the wall behind or a plinth.
Version 10: finds the wall behind the downpipe more surely (faces either way round, a very
detailed model), and says why if it can't make a swan neck.
Version 11: downpipes step out round anything in their way on the way to the ground - a
plinth, a sill, a lean-to roof and its wall - and back in below it where there's wall.
Version 12: right-click ends a line (and again finishes marking), IngeTrazo's window is made
active so Esc and the arrows reach it, and a reminder of the keys shows in the view.
Version 13: Esc also comes in the way IngeTrazo sends it to tools (on_cancel), so it always
ends the line (and again, finishes marking).
Version 14: the one group is named '(one piece)', so Scale Studio prints it as one piece.
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
VERSION = "14"            # shown in the window title, so you can tell which file is loaded


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
    ("hopper",    "Hopper head (old style)",        "pipe",   ()),
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
    'chunky': False, 'chunk_mult': 3.0, 'g_detail': True,
    'g_maxlen': 4000.0, 'p_maxlen': 2500.0, 'r_side': 'right', 'r_flip': False,
    'r_stops': True, 'r_shoe': True, 'r_swan': True, 'r_avoid': True,
}
WALL_SIDES = [("Behind the part (+Y)", 0.0), ("On the left (-X)", 90.0),
              ("In front (-Y)", 180.0), ("On the right (+X)", 270.0)]
PRESET_KEYS = ('g_profile', 'g_width', 'g_depth', 'g_wall', 'p_type', 'p_size', 'p_wall',
               'length', 'outlet_len', 'leg', 'bend_turn', 'branch_len', 'solid',
               'drop', 'wall_gap', 'over_left', 'over_right', 'g_spacing', 'p_spacing',
               'chunky', 'chunk_mult', 'g_detail', 'g_maxlen', 'p_maxlen', 'r_stops', 'r_shoe',
               'r_swan', 'r_avoid')
GUTTER_KEYS = ('g_profile', 'g_width', 'g_depth', 'g_wall', 'solid', 'g_detail')
PIPE_KEYS = ('p_type', 'p_size', 'p_wall', 'solid', 'g_detail')
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


def detailed(s):
    return s.get('g_detail', True)


def _perp_pair(axis):
    a = v_norm(axis)
    p = (1.0, 0.0, 0.0) if abs(a[0]) < 0.9 else (0.0, 1.0, 0.0)
    e1 = v_norm(v_cross(a, p))
    return e1, v_cross(a, e1)


def revolve_profile(c, axis, poly, n=24):
    """Closed solid made by spinning a closed (x, r) outline round an axis through c.
    x runs along the axis; every r must be above zero."""
    a = v_norm(axis)
    e1, e2 = _perp_pair(a)
    circ = [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i in range(n)]
    rings = [[v_add(c, v_add(v_mul(a, x), v_add(v_mul(e1, co * r), v_mul(e2, si * r))))
              for co, si in circ] for x, r in poly]
    sol = Solid()
    k = len(poly)
    for j in range(k):
        r0, r1 = rings[j], rings[(j + 1) % k]
        for i in range(n):
            q = (i + 1) % n
            sol.add([r0[i], r0[q], r1[q], r1[i]])
    sol.fix_winding()
    return sol


def disc(c, axis, r, h, n=16):
    """A round head (screw or bolt) of radius r standing h out of c along axis."""
    return revolve_profile(c, axis, [(0.0, 0.3), (0.0, r), (h, r), (h, 0.3)], n)


def gutter_trim(s):
    """The little extras along a gutter: the rolled bead on the front edge of half-round and
    deep-flow, the turned-out lips of square-line, the flat fillet and bead of an ogee.
    Closed (a, b) outlines in mm, to sweep along the same line as the gutter."""
    if not detailed(s):
        return []
    W, D, t = s['g_width'], s['g_depth'], s['g_wall']
    prof = s['g_profile']
    outer = gutter_outer(prof, W, D)
    fa, fb = outer[-1]               # front top edge
    ba, bb = outer[0]                # back top edge (wall side)

    def circ(ca, cb, r, n=12):
        return [(ca + r * math.cos(2 * math.pi * i / n), cb + r * math.sin(2 * math.pi * i / n))
                for i in range(n)]

    def rect(a0, a1, b0, b1):
        return [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]
    out = []
    if prof in ('halfround', 'deepflow'):
        rb = max(2.5, t * 1.1)
        out.append(circ(fa - rb * 0.55, fb - rb * 0.25, rb))
    elif prof == 'square':
        lip = max(3.0, t * 1.5)
        out.append(rect(fa - lip, fa + t * 0.5, fb - t, fb))
        out.append(rect(ba - t * 0.5, ba + lip * 0.6, bb - t, bb))
    elif prof == 'ogee':
        lip = max(3.0, t)
        out.append(rect(fa - lip, fa + t * 0.5, fb - max(4.0, t * 1.5), fb))
        r = min(D, W * 0.9) / 2.0
        xb = -W / 2 + 2 * r
        rb = max(2.0, t * 0.8)
        out.append(circ(xb - r - rb * 0.5, r, rb))         # bead where the S-curve turns
    return out


def gutter_sweep(path, s, up=Z, start_tag=None, end_tag=None, scale=1.0):
    """The gutter (and its bead or lips) swept along path. scale 0.001 for a path in metres."""
    band = [(a * scale, b * scale) for a, b in gutter_band(s)]
    so, frames = sweep_solid(path, up, band, start_tag=start_tag, end_tag=end_tag)
    out = [so]
    for loop in gutter_trim(s):
        out.append(sweep_solid(path, up, [(a * scale, b * scale) for a, b in loop])[0])
    return out, frames


def gutter_hooks(s, x0, x1, g, t):
    """Lips that hook over the front and back top edges of the gutter (unions, brackets,
    outlets), as on the real clip-in fittings."""
    outer = gutter_outer(s['g_profile'], s['g_width'], s['g_depth'])
    fa, fb = outer[-1]
    ba, bb = outer[0]
    h = max(2.0, t)
    out = [box_solid(x0, x1, fa - g - t - 3.5, fa + 1.0, fb - 1.0, fb + h)]
    out.append(box_solid(x0, x1, ba - 1.0, ba + g + t, bb - 1.0, bb + h))
    return out


def pipe_sleeve(p0, p1, s, grow, thick, up=None):
    """A sleeve (socket, collar, lip) over a pipe between two points."""
    o, i = pipe_rings(s, grow=grow, thick=thick)
    T = v_norm(v_sub(p1, p0))
    want = up or Z
    u = v_sub(want, v_mul(T, v_dot(want, T)))
    if v_len(u) < 1e-6:
        u = v_sub(Y, v_mul(T, v_dot(Y, T)))
    so, _ = sweep_solid([p0, p1], v_norm(u), o, i)
    return so


def socket_dims(s):
    """Length and thickness of a downpipe socket (mm)."""
    m = fix_mult(s)
    return 40.0, max(1.5, s['p_wall'] * 1.2) * m


def build_part(key, s):
    sol = []
    ports = {}
    det = detailed(s)
    if key in ('gutter', 'angle90x', 'angle90i', 'angle135x', 'angle135i'):
        if key == 'gutter':
            L = s['length']
            path = [(0, 0, 0), (L, 0, 0)]
        else:
            L = s['leg']
            turn = math.radians(90.0 if '90' in key else 45.0)
            side = 1.0 if key.endswith('x') else -1.0
            path = [(0, 0, 0), (L, 0, 0), (L + L * math.cos(turn), side * L * math.sin(turn), 0)]
        sols, (T, ups, _) = gutter_sweep(path, s, start_tag='in', end_tag='out')
        sol += sols
        if det and key != 'gutter':
            # socketed ends, like the clip-in ends of a real angle
            g, t = fit_gap(s), s['g_wall'] * fix_mult(s)
            k = min(40.0, L * 0.4)
            sl = gutter_band(s, grow=g, thick=t)
            sol.append(sweep_solid([(0, 0, 0), (k, 0, 0)], Z, sl)[0])
            e1 = v_add(path[-1], v_mul(T[-1], -k))
            sol.append(sweep_solid([e1, path[-1]], Z, sl)[0])
        ports['in'] = port((0, 0, 0), NX, Z, 'in', 'gutter')
        ports['out'] = port(path[-1], T[-1], ups[-1], 'out', 'gutter')

    elif key == 'outlet':
        L = s['outlet_len']
        sols, _ = gutter_sweep([(0, 0, 0), (L, 0, 0)], s, start_tag='in', end_tag='out')
        sol += sols
        a, zmin = gutter_low_point(s)
        top = (L / 2, a, zmin + s['g_wall'] * 0.5)
        bot = (L / 2, a, zmin - SPIGOT_LEN)
        o, i = pipe_rings(s)
        sp, _ = sweep_solid([top, bot], Y, o, i, end_tag='down')
        sol.append(sp)
        if det:
            g, t = fit_gap(s), s['g_wall'] * fix_mult(s)
            k = min(30.0, L * 0.25)
            sl = gutter_band(s, grow=g, thick=t)
            sol.append(sweep_solid([(0, 0, 0), (k, 0, 0)], Z, sl)[0])
            sol.append(sweep_solid([(L - k, 0, 0), (L, 0, 0)], Z, sl)[0])
            sol += gutter_hooks(s, 3.0, k - 3.0, g, t) + gutter_hooks(s, L - k + 3.0, L - 3.0, g, t)
            # a flange round the top of the spigot, under the gutter
            sol.append(pipe_sleeve((L / 2, a, zmin), (L / 2, a, zmin - 6.0), s, 0.0, 4.0 * fix_mult(s), Y))
        ports['in'] = port((0, 0, 0), NX, Z, 'in', 'gutter')
        ports['out'] = port((L, 0, 0), X, Z, 'out', 'gutter')
        ports['down'] = port(bot, NZ, Y, 'out', 'pipe')

    elif key == 'stopend':
        g = fit_gap(s)
        t = s['g_wall'] * fix_mult(s)
        so, _ = sweep_solid([(-STOPEND_SLEEVE, 0, 0), (0, 0, 0)], Z, gutter_band(s, grow=g, thick=t))
        sol.append(so)
        outer0 = gutter_outer(s['g_profile'], s['g_width'], s['g_depth'])
        outer = offset_open(outer0, -g - t)
        pl = max(3.0, t * 1.5)
        plate, _ = sweep_solid([(0, 0, 0), (pl, 0, 0)], Z, outer)
        sol.append(plate)
        if det and s['g_width'] > 20.0:
            # a raised panel on the outside of the end, and a rim round the mouth of the sleeve
            inner = offset_open(outer0, 6.0)
            sol.append(sweep_solid([(pl - 0.5, 0, 0), (pl + 2.0, 0, 0)], Z, inner)[0])
            sol.append(sweep_solid([(-STOPEND_SLEEVE, 0, 0), (-STOPEND_SLEEVE + 4.0, 0, 0)], Z,
                                   gutter_band(s, grow=g + t, thick=1.5 * fix_mult(s)))[0])
        ports['in'] = port((0, 0, 0), NX, Z, 'in', 'gutter')

    elif key in ('union', 'bracket'):
        bd = bracket_dims(s)
        g = bd['gap']
        L = UNION_LEN if key == 'union' else bd['len']
        t = bd['t']
        x0, x1 = -L / 2 - s['offset'], L / 2 - s['offset']
        so, _ = sweep_solid([(x0, 0, 0), (x1, 0, 0)], Z, gutter_band(s, grow=g, thick=t), end_tag='copy')
        sol.append(so)
        yb = s['g_width'] / 2 + g + t
        a, zmin = gutter_low_point(s)
        zb = zmin - g - t
        if key == 'bracket':
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
            if det:
                sol += gutter_hooks(s, x0, x1, g, t)
                # the plate carries on down for a screw under the arm, and one above the gutter
                pb = min(zb - 10, zlow)
                sol.append(box_solid(x0 - 10, x1 + 10, yb, yb + bd['plate'], pb - 14.0, pb + 1.0))
                hr = 3.5 * min(fix_mult(s), 2.0)
                for z in (s['g_depth'] + 5.0, pb - 7.0):
                    sol.append(disc(((x0 + x1) / 2, yb + 0.2, z), (0.0, -1.0, 0.0), hr, 1.5))
        elif det:
            # a union: back plate on the fascia, clips over the front and back edges, and a
            # raised band round the middle where the two lengths meet
            sol.append(box_solid(x0, x1, yb, yb + bd['plate'], zb, s['g_depth'] + 8.0))
            sol += gutter_hooks(s, x0 + 4.0, x1 - 4.0, g, t)
            xm = (x0 + x1) / 2
            sol.append(sweep_solid([(xm - 6.0, 0, 0), (xm + 6.0, 0, 0)], Z,
                                   gutter_band(s, grow=g + t, thick=1.5 * fix_mult(s)))[0])
        ports['in'] = port((0, 0, 0), NX, Z, 'in', 'gutter')

    elif key == 'pipe':
        L = s['length']
        o, i = pipe_rings(s)
        so, _ = sweep_solid([(0, 0, 0), (L, 0, 0)], Z, o, i, 'in', 'out')
        sol.append(so)
        if det and L > 100.0:
            k, t = socket_dims(s)
            sol.append(pipe_sleeve((0, 0, 0), (k, 0, 0), s, fit_gap(s), t))   # socket at the top end
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
        if det:
            k, t = socket_dims(s)
            sol.append(pipe_sleeve((0, 0, 0), (min(k, lead), 0, 0), s, fit_gap(s), t))
            if key == 'shoe':
                # the flared lip of the shoe's mouth
                e = path[-1]
                sol.append(pipe_sleeve(v_add(e, v_mul(Tend, -8.0)), e, s, 0.0, 2.5 * fix_mult(s), ups[-1]))
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
        if det:
            k, t = socket_dims(s)
            sol.append(pipe_sleeve((0, 0, 0), (k, 0, 0), s, fit_gap(s), t))
            if s['branch_len'] > k * 1.5:
                sol.append(pipe_sleeve(v_add(end, v_mul(dirb, -k)), end, s, fit_gap(s), t, upb))
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
        xm = (x0 + x1) / 2
        if key == 'socket' and det:
            # a bead round each end of the coupler
            for a_, b_ in ((x0, x0 + 4.0), (x1 - 4.0, x1)):
                sol.append(pipe_sleeve((a_, 0, 0), (b_, 0, 0), s, g + t, 1.2 * m))
        if key == 'clip':
            r_out = s['p_size'] / 2 + g + t
            hw = 8 * m
            pt = 4 * m
            reach = s.get('reach')           # pipe middle to the wall, when it is known
            back = max(r_out + pt + 2.0, reach) if reach else r_out + 35 + pt
            sol.append(box_solid(x0, x1, -hw, hw, r_out - 1, back - pt))
            sol.append(box_solid(x0 - 10, x1 + 10, -25 - hw, 25 + hw, back - pt, back))
            if det:
                # bolt lugs on the front of the ring, a bolt through them, and two screws in the plate
                lw, ll = 3.0 * m, 9.0 * m
                for sg in (1.0, -1.0):
                    y0, y1 = sorted((sg * 0.6, sg * (0.6 + lw)))
                    sol.append(box_solid(x0, x1, y0, y1, -r_out - ll, -r_out + 1.0))
                yl = 0.6 + lw + 1.2 * m
                zc = -r_out - ll * 0.55
                sol.append(revolve_profile((xm, -yl, zc), Y, [(0.0, 0.3), (0.0, 1.6 * m), (2 * yl, 1.6 * m),
                                                              (2 * yl, 0.3)], 12))
                sol.append(disc((xm, yl, zc), Y, 2.6 * m, 1.4 * m, 6))
                for sy in (1.0, -1.0):
                    sol.append(disc((xm, sy * (18.0 + hw), back - pt + 0.2), NZ, 3.0 * min(m, 2.0), 1.5))
        ports['in'] = port((0, 0, 0), NX, Z, 'in', 'pipe')

    elif key == 'hopper':
        # an old-style hopper head: open-topped flared box, rim band, back plate with
        # fixing ears, and a spigot underneath for the downpipe. Its rim sits 30 mm
        # below the end it is added to; local z points at the wall.
        m = fix_mult(s)
        size = s['p_size']
        o, i = pipe_rings(s)
        g0, t = 30.0, 4.0 * m
        W1, D1, W2, D2, H = max(280.0, size * 3.5), max(200.0, size * 2.6), max(140.0, size * 1.9), \
            max(110.0, size * 1.5), max(220.0, size * 2.8)
        Rp = size / 2 + 15.0                       # back of the hopper, behind the outlet

        def rect(x, hw, z0, z1):
            return [(x, -hw, z0), (x, hw, z0), (x, hw, z1), (x, -hw, z1)]
        R1 = rect(g0, W1 / 2, Rp - D1, Rp)
        R2 = rect(g0 + H, W2 / 2, Rp - D2, Rp)
        r1 = rect(g0, W1 / 2 - t, Rp - D1 + t, Rp - t)
        r2 = rect(g0 + H - t, W2 / 2 - t, Rp - D2 + t, Rp - t)
        cup = Solid()
        for a in range(4):
            b = (a + 1) % 4
            cup.add([R1[a], R1[b], R2[b], R2[a]])          # outside
            cup.add([R1[b], R1[a], r1[a], r1[b]])          # rim
            cup.add([r1[b], r1[a], r2[a], r2[b]])          # inside
        cup.add(list(R2))                                   # underside
        cup.add(list(reversed(r2)))                         # floor
        cup.fix_winding()
        sol.append(cup)
        lip = 8.0 * m
        sol.append(box_solid(g0, g0 + 15, -W1 / 2 - lip, W1 / 2 + lip, Rp - D1 - lip, Rp - D1))
        sol.append(box_solid(g0, g0 + 15, -W1 / 2 - lip, -W1 / 2, Rp - D1, Rp))
        sol.append(box_solid(g0, g0 + 15, W1 / 2, W1 / 2 + lip, Rp - D1, Rp))
        sol.append(box_solid(g0 + 10, g0 + 70, -W1 / 2 - 35, W1 / 2 + 35, Rp, Rp + 6 * m))   # ears
        if detailed(s):
            # a moulded band round the middle of the front, and a bolt in each ear
            zb = g0 + H * 0.45
            wb = W1 / 2 + (W2 / 2 - W1 / 2) * 0.45 + 3.0
            db = D1 + (D2 - D1) * 0.45 + 3.0
            sol.append(box_solid(zb, zb + 10, -wb, wb, Rp - db, Rp - db + 6))
            for sy in (1.0, -1.0):
                sol.append(disc((g0 + 40, sy * (W1 / 2 + 18), Rp - 0.2), NZ, 5.0, 2.0, 6))
        so, _ = sweep_solid([(g0 + H - t * 0.5, 0, 0), (g0 + H + 60.0, 0, 0)], Z, o, i, None, 'out')
        sol.append(so)
        ports['in'] = port((0, 0, 0), NX, Z, 'in', 'pipe')
        ports['out'] = port((g0 + H + 60.0, 0, 0), X, Z, 'out', 'pipe')
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
# Following lines you've drawn. Draw lines where the run is to go (corner to corner),
# select them and the whole run is built along them, bends and fittings and all.
# The wall each line is drawn on is found from the model (or from wall faces you
# select with the lines), so the run stands off the wall by the right amount.
# ---------------------------------------------------------------------------
MM = 0.001                     # sizes are in mm; the model is in metres


def _r_is_group(e):
    return getattr(e, 'mesh', None) is not None and not hasattr(e, 'loop')


def _r_vpos(v):
    p = _pos(v)
    if p is None and v is not None:
        p = _pos(getattr(v, 'position', None)) if getattr(v, 'position', None) is not None else None
    return p


def _r_edge_ends(e):
    """A line's two ends as (x, y, z), or None if it isn't a line."""
    for a, b in (('a', 'b'), ('v0', 'v1'), ('v1', 'v2'), ('start', 'end')):
        pa, pb = getattr(e, a, None), getattr(e, b, None)
        if pa is None or pb is None:
            continue
        p, q = _r_vpos(pa), _r_vpos(pb)
        if p is not None and q is not None:
            return p, q
    return None


def _r_is_face(e):
    if _r_is_group(e):
        return False
    if hasattr(e, 'loop') or 'face' in type(e).__name__.lower():
        return True
    return hasattr(e, 'vertices') and _r_edge_ends(e) is None


def _r_m_from_q(q):
    if q is None:
        return None
    try:
        d = list(q.data())                     # column by column
    except Exception:
        return None
    return [[float(d[c * 4 + r]) for c in range(4)] for r in range(4)]


def _r_m_mul(a, b):
    return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)] for r in range(4)]


def _r_m_apply(m, p):
    if m is None:
        return p
    return tuple(m[r][0] * p[0] + m[r][1] * p[1] + m[r][2] * p[2] + m[r][3] for r in range(3))


def _r_iter_placements(group, base=None):
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
        yield from _r_iter_placements(ch, m)


def _r_ctx_world(scene):
    """Where an open group's own space sits in the model, or None at the top."""
    ctx = getattr(scene, 'edit_group', None)
    if ctx is None:
        return None
    for top in _items(getattr(scene, 'groups', None)):
        for g, m in _r_iter_placements(top):
            if g is ctx:
                return _r_m_from_q(m)
    return _r_m_from_q(getattr(ctx, 'xform', None))


def _r_chain(segs, tol=1e-7):
    """Joins line segments [(a, b)] end to end: [(points, closed)]. Where three or more
    lines meet, a chain stops there."""
    def key(p):
        return (int(round(p[0] / tol)), int(round(p[1] / tol)), int(round(p[2] / tol)))
    segs = [(a, b) for a, b in segs if key(a) != key(b)]
    ends = {}
    for k, (a, b) in enumerate(segs):
        ends.setdefault(key(a), []).append(k)
        ends.setdefault(key(b), []).append(k)
    used = [False] * len(segs)

    def walk(k, kp):
        out = []
        while True:
            used[k] = True
            a, b = segs[k]
            p, kp = (b, key(b)) if key(a) == kp else (a, key(a))
            out.append(p)
            cand = [j for j in ends.get(kp, []) if not used[j]]
            if len(ends.get(kp, [])) != 2 or not cand:
                return out, kp
            k = cand[0]
    chains = []
    order = sorted(range(len(segs)), key=lambda k: -max(len(ends[key(segs[k][0])]) != 2,
                                                          len(ends[key(segs[k][1])]) != 2))
    for k0 in order:
        if used[k0]:
            continue
        a, b = segs[k0]
        if len(ends[key(a)]) == 2 and len(ends[key(b)]) != 2:
            a, b = b, a
        used[k0] = True
        fwd, kend = [], key(b)
        cand = [j for j in ends.get(key(b), []) if not used[j]]
        if len(ends.get(key(b), [])) == 2 and cand:
            fwd, kend = walk(cand[0], key(b))
        if kend == key(a) and len(fwd) >= 2:
            chains.append(([a, b] + fwd[:-1], True))
            continue
        back = []
        cand = [j for j in ends.get(key(a), []) if not used[j]]
        if len(ends.get(key(a), [])) == 2 and cand:
            back, _k = walk(cand[0], key(a))
        chains.append((list(reversed(back)) + [a, b] + fwd, False))
    return chains


def route_lines(scene, selection):
    """The lines you've selected, joined end to end: [(points, closed)] in the model. With a
    group selected instead, the loose lines in it (lines not round any face)."""
    sel = list(selection or [])
    m0 = _r_ctx_world(scene)
    segs = []
    for e in sel:
        if _r_is_group(e) or _r_is_face(e):
            continue
        ends = _r_edge_ends(e)
        if ends:
            segs.append((_r_m_apply(m0, ends[0]), _r_m_apply(m0, ends[1])))
    if not segs:
        for g in sel:
            if not _r_is_group(g):
                continue
            for pg, q in _r_iter_placements(g):
                m = _r_m_from_q(q)
                if m0 is not None:
                    m = m0 if m is None else _r_m_mul(m0, m)
                for e in _items(getattr(getattr(pg, 'mesh', None), 'edges', None)):
                    if _items(getattr(e, 'faces', None)):
                        continue
                    ends = _r_edge_ends(e)
                    if ends:
                        segs.append((_r_m_apply(m, ends[0]), _r_m_apply(m, ends[1])))
    if not segs:
        return []
    span = max(v_len(v_sub(b, a)) for a, b in segs)
    return _r_chain(segs, tol=max(1e-9, span * 1e-7))


ROUTE_STATS = {'limit': False}


def route_faces(scene, selection, near=None, limit=3000000, upright_only=True):
    """Upright faces [(normal, d, points, (lo, hi))] in the model: the faces selected with the
    lines if there are any, otherwise every face near the lines (near = (lo, hi) box)."""
    out = []

    def take(f, m):
        pts = [p for p in (_r_vpos(v) for v in _items(getattr(f, 'vertices', None))) if p is not None]
        if len(pts) < 3:
            return
        if m is not None:
            pts = [_r_m_apply(m, p) for p in pts]
        lo = tuple(min(p[k] for p in pts) for k in range(3))
        hi = tuple(max(p[k] for p in pts) for k in range(3))
        if near is not None and any(lo[k] > near[1][k] or hi[k] < near[0][k] for k in range(3)):
            return
        n = _newell(pts)
        if v_len(n) < 0.5 or (upright_only and abs(n[2]) > 0.35):
            return                                  # floors, roofs and ceilings
        out.append((n, v_dot(n, pts[0]), pts, (lo, hi)))

    sel = list(selection or [])
    m0 = _r_ctx_world(scene)
    faces = [e for e in sel if _r_is_face(e)]
    if faces:
        for f in faces:
            take(f, m0)
        return out
    count = [0]

    def scan(mesh, m):
        for f in _items(getattr(mesh, 'faces', None)):
            count[0] += 1
            if count[0] > limit:
                ROUTE_STATS['limit'] = True
                return
            a = getattr(f, 'attrs', None)
            if isinstance(a, dict) and PORT_KEY in a:
                continue
            take(f, m)
    for top in _items(getattr(scene, 'groups', None)):
        for g, q in _r_iter_placements(top):
            scan(getattr(g, 'mesh', None), _r_m_from_q(q))
    if getattr(scene, 'mesh', None) is not None:
        scan(scene.mesh, None)
    return out


def _r_box(chains, pad=0.5):
    pts = [p for c, _ in chains for p in c]
    lo = tuple(min(p[k] for p in pts) - pad for k in range(3))
    hi = tuple(max(p[k] for p in pts) + pad for k in range(3))
    return lo, hi


def _r_on_face(p, face, tol):
    n, d, pts, (lo, hi) = face
    if abs(v_dot(n, p) - d) > tol:
        return False
    if any(p[k] < lo[k] - tol or p[k] > hi[k] + tol for k in range(3)):
        return False
    u = v_norm(v_cross(n, Z))
    if v_len(u) < 0.5:
        u = v_norm(v_cross(n, X))
    w = v_cross(n, u)
    q = (v_dot(p, u), v_dot(p, w))
    poly = [(v_dot(a, u), v_dot(a, w)) for a in pts]
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        (xi, yi), (xj, yj) = poly[i], poly[j]
        if (yi > q[1]) != (yj > q[1]) and q[0] < (xj - xi) * (q[1] - yi) / ((yj - yi) or 1e-30) + xi:
            inside = not inside
        # on the edge itself counts
        ex, ey = xj - xi, yj - yi
        L2 = ex * ex + ey * ey
        f = max(0.0, min(1.0, ((q[0] - xi) * ex + (q[1] - yi) * ey) / L2)) if L2 > 0 else 0.0
        if math.hypot(xi + ex * f - q[0], yi + ey * f - q[1]) <= tol:
            return True
        j = i
    return inside


def segment_wall(a, b, faces, tol=0.002, flip=False):
    """(outward normal, plane d) of the upright face a line a-b is drawn on, or None. The line
    can run on past the face (a stack going up above the eaves, or down into the ground)."""
    samples = [v_add(a, v_mul(v_sub(b, a), f_)) for f_ in (0.5, 0.25, 0.75, 0.1, 0.9, 0.0, 1.0)]
    for f in faces:
        n, d = f[0], f[1]
        if abs(v_dot(n, a) - d) > tol or abs(v_dot(n, b) - d) > tol:
            continue
        if any(_r_on_face(q, f, tol) for q in samples):
            n = f[0]
            n = v_norm((n[0], n[1], 0.0))
            d = v_dot(n, a)
            if flip:
                n, d = v_mul(n, -1.0), -d
            return n, d
    return None


def _r_offset(cons):
    """The smallest move o with o . n = s for each (n, s) given: where two stand-offs from
    two walls meet (an outside or inside corner), or one stand-off from one wall."""
    keep = []
    for n, s in cons:
        if all(abs(v_dot(n, k[0])) < 0.985 for k in keep):
            keep.append((n, s))
    if not keep:
        return (0.0, 0.0, 0.0)
    if len(keep) == 1:
        return v_mul(keep[0][0], keep[0][1])
    (n1, s1), (n2, s2) = keep[0], keep[1]
    c = v_dot(n1, n2)
    det = 1.0 - c * c
    return v_add(v_mul(n1, (s1 - c * s2) / det), v_mul(n2, (s2 - c * s1) / det))


def _r_clean(pts, min_turn=1.5):
    """Drops repeated points and points where the line hardly turns."""
    P = []
    for p in pts:
        if not P or v_len(v_sub(p, P[-1])) > 1e-5:
            P.append(tuple(p))
    changed = True
    while changed and len(P) > 2:
        changed = False
        for i in range(1, len(P) - 1):
            a, b = v_norm(v_sub(P[i], P[i - 1])), v_norm(v_sub(P[i + 1], P[i]))
            if v_dot(a, b) > math.cos(math.radians(min_turn)):
                del P[i]
                changed = True
                break
    return P


def route_pieces(pts, R, lead):
    """Straights and bends along a centre line (model metres):
    [('pipe', [a, b], seg)] and [('bend', path, turn in deg, seg)]. seg = which stretch of the
    line it's on. Each corner gets a bend of radius R with a straight of `lead` at each end,
    made smaller where the stretches are too short for it."""
    P = _r_clean(pts)
    n = len(P)
    if n < 2:
        return []
    corner = {}
    for i in range(1, n - 1):
        a, b = v_norm(v_sub(P[i], P[i - 1])), v_norm(v_sub(P[i + 1], P[i]))
        th = math.acos(max(-1.0, min(1.0, v_dot(a, b))))
        lin, lout = v_len(v_sub(P[i], P[i - 1])), v_len(v_sub(P[i + 1], P[i]))
        avail = min(lin * (0.5 if i > 1 else 0.9), lout * (0.5 if i < n - 2 else 0.9))
        tn = math.tan(min(th, math.radians(170.0)) / 2.0)
        r, ld = R, lead
        t = r * tn
        if t + ld > avail:
            ld = max(0.0, avail - t)
            if t > avail:
                t, ld = avail, 0.0
                r = t / tn if tn > 1e-9 else R
        corner[i] = (a, b, th, r, t, ld)
    pieces, cur = [], P[0]
    for i in range(1, n):
        if i in corner:
            a, b, th, r, t, ld = corner[i]
            t1 = v_sub(P[i], v_mul(a, t))
            s0 = v_sub(t1, v_mul(a, ld))
            if v_len(v_sub(s0, cur)) > 1e-5:
                pieces.append(('pipe', [cur, s0], i - 1))
            d = v_norm(v_sub(b, v_mul(a, v_dot(a, b))))
            arc = arc_path(t1, a, d, r, th, max(4, int(math.degrees(th) / 7.5)))
            path = ([s0] if ld > 1e-6 else []) + arc
            if ld > 1e-6:
                path.append(v_add(arc[-1], v_mul(b, ld)))
            pieces.append(('bend', path, math.degrees(th), i - 1))
            cur = path[-1]
        elif v_len(v_sub(P[i], cur)) > 1e-5:
            pieces.append(('pipe', [cur, P[i]], i - 1))
            cur = P[i]
    return pieces


def split_lengths(pieces, maxlen):
    """Straights longer than maxlen (metres, 0 = no limit) cut into equal lengths."""
    if maxlen <= 0:
        return pieces
    out = []
    for pc in pieces:
        if pc[0] != 'pipe':
            out.append(pc)
            continue
        a, b = pc[1]
        L = v_len(v_sub(b, a))
        k = max(1, int(math.ceil(L / maxlen - 1e-9)))
        for j in range(k):
            out.append(('pipe', [v_add(a, v_mul(v_sub(b, a), j / float(k))),
                                 v_add(a, v_mul(v_sub(b, a), (j + 1) / float(k)))], pc[2]))
    return out


def piece_dirs(pc):
    """(direction at the start, direction at the end) of a piece."""
    p = pc[1]
    return v_norm(v_sub(p[1], p[0])), v_norm(v_sub(p[-1], p[-2]))


def route_up(T, want=None):
    """A direction square to T, as near to `want` as it can be."""
    for w in (want, Z, X, Y):
        if w is None:
            continue
        u = v_sub(w, v_mul(T, v_dot(w, T)))
        if v_len(u) > 1e-3:
            return v_norm(u)
    return Z


def _mm_loop(loop):
    return [(a * MM, b * MM) for a, b in loop] if loop else None


def end_port(c, n, u, role, system):
    return {'c': list(c), 'n': list(v_norm(n)), 'u': list(v_norm(u)), 'role': role, 'sys': system}


def end_target(c, n, u, role, system, **extra):
    t = {'c': tuple(c), 'n': tuple(v_norm(n)), 'u': tuple(v_norm(u)), 'role': role, 'sys': system}
    t.update(extra)
    return t

# ---------------------------------------------------------------------------
# Gutters and downpipes along drawn lines
# ---------------------------------------------------------------------------
ROUTE_SIDES = [("On the right of the line, as it was drawn", 'right'),
               ("On the left of the line, as it was drawn", 'left')]


def _level(pts, closed):
    P = list(pts) + ([pts[0]] if closed else [])
    for a, b in zip(P[:-1], P[1:]):
        L = v_len(v_sub(b, a))
        if L > 1e-9 and abs(b[2] - a[2]) > 0.1 * L:
            return False
    return True


def gutter_offsets(s):
    """(how far the middle of the gutter is out from the wall, how far its bottom is below
    the top of the wall), in mm - the same as a gutter put on a wall from the On a wall page."""
    outer = gutter_outer(s['g_profile'], s['g_width'], s['g_depth'])
    bd = bracket_dims(s)
    back = max(p[0] for p in outer)
    top = max(p[1] for p in outer)
    return bd['gap'] + bd['t'] + bd['plate'] + s['wall_gap'] + back, s['drop'] + top


def pipe_standoff(s):
    """Pipe middle to the wall, on standard clips (mm)."""
    m = fix_mult(s)
    return s['p_size'] / 2 + fit_gap(s, 0.3) + 3.0 * m + 35 + 4 * m + s['wall_gap']


def _plan_dir(a, b):
    return v_norm((b[0] - a[0], b[1] - a[1], 0.0))


def gutter_line(pts, closed, faces, s):
    """A gutter run from a line drawn along the top outside edge of the wall: its line (the
    bottom middle of the gutter, as the parts are built) with the wall on its left, and for
    each stretch the wall's outward direction and plane. Closed loops start half way along
    their longest side."""
    P = [tuple(p) for p in pts]
    segs = list(zip(P, P[1:] + [P[0]])) if closed else list(zip(P[:-1], P[1:]))
    walls = [segment_wall(a, b, faces, flip=s.get('r_flip', False)) for a, b in segs]
    found = sum(1 for w in walls if w)
    if closed:
        area = sum(a[0] * b[1] - b[0] * a[1] for a, b in segs)
        left = area > 0                          # the walls are inside the loop
    else:
        left = s.get('r_side', 'right') == 'left'
    if s.get('r_flip') and not found:
        left = not left
    N = []
    for (a, b), w in zip(segs, walls):
        if w:
            N.append(w)
            continue
        T = _plan_dir(a, b)
        n = v_cross(T, Z) if left else v_cross(Z, T)
        N.append((n, v_dot(n, a)))
    # the wall has to be on the left of the run, so turn the line round if it isn't
    score = sum(v_dot(v_cross(Z, n), _plan_dir(a, b)) * v_len(v_sub(b, a)) for (a, b), (n, _) in zip(segs, N))
    if score < 0:
        P = list(reversed(P))
        if closed:
            P = P[-1:] + P[:-1]                  # keep each stretch paired with its own wall
            segs = list(zip(P, P[1:] + [P[0]]))
            N = list(reversed(N))
        else:
            segs = list(zip(P[:-1], P[1:]))
            N = list(reversed(N))
    dist, drop = gutter_offsets(s)
    k = len(segs)
    Q = []
    for j in range(len(P)):
        cons = []
        if closed or j > 0:
            cons.append((N[(j - 1) % k][0], dist * MM))
        if closed or j < len(P) - 1:
            cons.append((N[j % k][0], dist * MM))
        o = _r_offset(cons)
        Q.append((P[j][0] + o[0], P[j][1] + o[1], P[j][2] - drop * MM))
    raw = P
    if closed:
        # start and finish half way along the longest side
        L = [v_len(v_sub(Q[(j + 1) % k], Q[j])) for j in range(k)]
        j0 = max(range(k), key=lambda j: L[j])
        mid = v_mul(v_add(Q[j0], Q[(j0 + 1) % k]), 0.5)
        rmid = v_mul(v_add(P[j0], P[(j0 + 1) % k]), 0.5)
        order = [(j0 + 1 + i) % k for i in range(k)]
        Q = [mid] + [Q[j] for j in order] + [mid]
        raw = [rmid] + [P[j] for j in order] + [rmid]
        N = [N[j0]] + [N[j] for j in order]
    cum = [0.0]
    for a, b in zip(Q[:-1], Q[1:]):
        cum.append(cum[-1] + v_len(v_sub(b, a)))
    return {'Q': Q, 'N': N, 'raw': raw, 'cum': cum, 'closed': closed, 'found': found, 'segs': len(segs)}


def _at(run, s_):
    """Point and direction on a run's line, s_ metres along it."""
    Q, cum = run['Q'], run['cum']
    for j in range(len(Q) - 1):
        if s_ <= cum[j + 1] + 1e-12 or j == len(Q) - 2:
            L = (cum[j + 1] - cum[j]) or 1e-12
            f = max(0.0, min(1.0, (s_ - cum[j]) / L))
            return v_add(Q[j], v_mul(v_sub(Q[j + 1], Q[j]), f)), v_norm(v_sub(Q[j + 1], Q[j])), j
    return Q[-1], v_norm(v_sub(Q[-1], Q[-2])), len(Q) - 2


def _sub_line(run, s0, s1):
    Q, cum = run['Q'], run['cum']
    pts = [_at(run, s0)[0]]
    for j in range(1, len(Q) - 1):
        if s0 + 1e-9 < cum[j] < s1 - 1e-9:
            pts.append(Q[j])
    pts.append(_at(run, s1)[0])
    return pts


def _nearest_on_run(run, p):
    """(plan distance, metres along the run) of the nearest point on the run to p."""
    best = (1e30, 0.0)
    Q, cum = run['Q'], run['cum']
    for j in range(len(Q) - 1):
        a, b = Q[j], Q[j + 1]
        ab = (b[0] - a[0], b[1] - a[1])
        L2 = ab[0] ** 2 + ab[1] ** 2
        f = max(0.0, min(1.0, ((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1]) / L2)) if L2 > 0 else 0.0
        q = (a[0] + ab[0] * f, a[1] + ab[1] * f)
        d = math.hypot(p[0] - q[0], p[1] - q[1])
        if d < best[0]:
            best = (d, cum[j] + (cum[j + 1] - cum[j]) * f)
    return best


def _near_raw(run, p):
    """Plan distance and height difference from p to the line as drawn."""
    best = (1e30, 0.0)
    R = run['raw']
    for a, b in zip(R[:-1], R[1:]):
        ab = (b[0] - a[0], b[1] - a[1])
        L2 = ab[0] ** 2 + ab[1] ** 2
        f = max(0.0, min(1.0, ((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1]) / L2)) if L2 > 0 else 0.0
        q = (a[0] + ab[0] * f, a[1] + ab[1] * f, a[2] + (b[2] - a[2]) * f)
        d = math.hypot(p[0] - q[0], p[1] - q[1])
        if d < best[0]:
            best = (d, p[2] - q[2])
    return best


def _corner_name(a, b):
    turn = math.degrees(math.acos(max(-1.0, min(1.0, v_dot(a, b)))))
    side = "external" if v_cross(a, b)[2] > 0 else "internal"
    return turn, "%g deg angle - %s corner" % (round(180.0 - turn, 1), side)


def build_gutter_run(run, outlets, s, sname):
    """The parts of one gutter run. outlets: [metres along the run]. Returns
    (parts, spigots {outlet index: open end of its spigot}, notes)."""
    Q, cum = run['Q'], run['cum']
    total = cum[-1]
    notes = []
    leg = s['leg'] * MM
    special = []
    for j in range(1, len(Q) - 1):
        a, b = v_norm(v_sub(Q[j], Q[j - 1])), v_norm(v_sub(Q[j + 1], Q[j]))
        lg = min(leg, 0.45 * (cum[j] - cum[j - 1]), 0.45 * (cum[j + 1] - cum[j]))
        special.append([cum[j] - lg, cum[j] + lg, 'angle', j])
    Lo = s['outlet_len'] * MM
    for k, so in enumerate(outlets):
        if total < Lo + 0.01:
            notes.append("a gutter run was too short for a running outlet")
            continue
        s0 = so - Lo / 2
        s0 = 0.0 if so < Lo else (total - Lo if total - so < Lo else s0)
        for c0, c1, kind, _j in special:
            if kind == 'angle' and s0 < c1 and s0 + Lo > c0:
                s0 = c1 if so > (c0 + c1) / 2 else c0 - Lo
        s0 = max(0.0, min(total - Lo, s0))
        if any(s0 < c1 - 1e-6 and s0 + Lo > c0 + 1e-6 for c0, c1, _k, _j in special):
            notes.append("a running outlet had no room between the corners, so it was left out")
            continue
        special.append([s0, s0 + Lo, 'outlet', k])
    special.sort(key=lambda x: x[0])
    # straights fill the gaps, cut to the longest length
    pieces, at = [], 0.0
    maxlen = s.get('g_maxlen', 0.0) * MM
    for c0, c1, kind, data in special + [[total, total, 'end', None]]:
        if c0 - at > 0.001:
            k = max(1, int(math.ceil((c0 - at) / maxlen - 1e-9))) if maxlen > 0 else 1
            for i in range(k):
                pieces.append([at + (c0 - at) * i / k, at + (c0 - at) * (i + 1) / k, 'gutter', None])
        if kind != 'end':
            pieces.append([c0, c1, kind, data])
        at = max(at, c1)
    parts, spigots = [], {}
    fix, fix_n, uni, uni_n = [], 0, [], 0
    ends_open = not run['closed']
    stops = ends_open and s.get('r_stops', True)
    for idx, (s0, s1, kind, data) in enumerate(pieces):
        first, last = idx == 0, idx == len(pieces) - 1
        path = _sub_line(run, s0, s1)
        T0 = v_norm(v_sub(path[1], path[0]))
        T1 = v_norm(v_sub(path[-1], path[-2]))
        tags = {}
        st = 'in' if (first and ends_open and not stops) else None
        et = 'out' if (last and ends_open and not stops) else None
        if st:
            tags['in'] = end_port(path[0], v_mul(T0, -1.0), Z, 'in', 'gutter')
        if et:
            tags['out'] = end_port(path[-1], T1, Z, 'out', 'gutter')
        if kind == 'outlet':
            w, tg = plan_part('outlet', dict(s, outlet_len=(s1 - s0) / MM),
                              end_target(path[0], T0, Z, 'out', 'gutter'))
            spigots[data] = tg['down']
            ptags = {'out': tg['out']} if et and 'out' in tg else {}
            parts.append(("Running outlet - %s" % sname, w, ptags))
        elif kind == 'angle':
            sols, _ = gutter_sweep(path, s, Z, st, et, MM)
            turn, name = _corner_name(T0, T1)
            if detailed(s):
                g, t = fit_gap(s), s['g_wall'] * fix_mult(s)
                k = min(0.040, (s1 - s0) * 0.2)
                sl = _mm_loop(gutter_band(s, grow=g, thick=t))
                sols.append(sweep_solid([path[0], v_add(path[0], v_mul(T0, k))], Z, sl)[0])
                sols.append(sweep_solid([v_sub(path[-1], v_mul(T1, k)), path[-1]], Z, sl)[0])
            parts.append(("Gutter %s - %s" % (name, sname), sols, tags))
        else:
            sols, _ = gutter_sweep(path, s, Z, st, et, MM)
            L = (s1 - s0) / MM
            parts.append(("Gutter length - %s x %g mm" % (sname, round(L)), sols, tags))
            if s.get('auto_fix', True):
                for x in fixing_positions(L, s['g_spacing']):
                    w, _ = plan_part('bracket', dict(s, offset=L - x), end_target(path[-1], T1, Z, 'out', 'gutter'))
                    fix += w
                    fix_n += 1
        # a union bracket where this piece meets the next (outlets have their own clip-in ends)
        nxt = pieces[idx + 1] if idx + 1 < len(pieces) else (pieces[0] if run['closed'] else None)
        socketed = detailed(s) and 'angle' in (kind, nxt[2] if nxt else None)   # angles have their own
        if nxt is not None and kind != 'outlet' and nxt[2] != 'outlet' and not socketed:
            w, _ = plan_part('union', dict(s, offset=0.0), end_target(path[-1], T1, Z, 'out', 'gutter'))
            uni += w
            uni_n += 1
    if fix:
        parts.append(("Fascia brackets x%d - %s" % (fix_n, sname), fix, {}))
    if uni:
        parts.append(("Union brackets x%d - %s" % (uni_n, sname), uni, {}))
    if stops:
        p0, T0, _j = _at(run, 0.0)
        p1, T1, _j = _at(run, total)
        w0, _ = plan_part('stopend', s, end_target(p0, v_mul(T0, -1.0), Z, 'in', 'gutter'))
        w1, _ = plan_part('stopend', s, end_target(p1, T1, Z, 'out', 'gutter'))
        parts.append(("Stop ends x2 - %s" % sname, w0 + w1, {}))
    return parts, spigots, notes


def build_downpipe(path, walls, s, sname, connected):
    """The parts of one downpipe down a centre line (top first). walls: (normal, d) of the wall
    for each stretch of the line, or None. Returns (parts, notes)."""
    notes = []
    R = s['p_size'] * 0.8 * MM
    pieces = route_pieces(path, R, SOCKET_LEN * MM)
    if not pieces:
        return [], ["a downpipe line was too short"]

    def wall_of(seg):
        if 0 <= seg < len(walls) and walls[seg]:
            return walls[seg]
        for w in walls:                                  # the nearest stretch that has one
            if w:
                return w
        return None

    def up_of(pc, T):
        w = wall_of(pc[-1])
        return route_up(T, v_mul(w[0], -1.0) if w else None)
    # leave room for a shoe at the bottom
    shoe = None
    if s.get('r_shoe', True) and pieces[-1][0] == 'pipe':
        so, _p = build_part('shoe', dict(s, bend_dir=180.0))
        drop = max(p[0] for x in so for f, _t in x.faces for p in f) * MM
        a, b = pieces[-1][1]
        T = v_norm(v_sub(b, a))
        if v_len(v_sub(b, a)) > drop + 0.05:
            nb = v_sub(b, v_mul(T, drop))
            pieces[-1] = ('pipe', [a, nb], pieces[-1][2])
            shoe = end_target(nb, T, up_of(pieces[-1], T), 'out', 'pipe')
        else:
            notes.append("a downpipe's last stretch was too short for a shoe")
    pieces = split_lengths(pieces, s.get('p_maxlen', 0.0) * MM)
    o, i = pipe_rings(s)
    o, i = _mm_loop(o), _mm_loop(i)
    k_s, t_s = socket_dims(s)
    so_, si_ = pipe_rings(s, grow=fit_gap(s), thick=t_s)
    so_, si_ = _mm_loop(so_), _mm_loop(si_)
    parts, clips, nclip = [], [], 0
    for idx, pc in enumerate(pieces):
        T0, T1 = piece_dirs(pc)
        up = up_of(pc, T0)
        first, last = idx == 0, idx == len(pieces) - 1
        tags = {}
        st = 'in' if first and not connected else None
        et = 'out' if last and shoe is None else None
        if st:
            tags['in'] = end_port(pc[1][0], v_mul(T0, -1.0), up, 'in', 'pipe')
        if et:
            tags['out'] = end_port(pc[1][-1], T1, up_of(pc, T1), 'out', 'pipe')
        sol, _f = sweep_solid(pc[1], up, o, i, st, et)
        sols = [sol]
        if detailed(s):
            L0 = v_len(v_sub(pc[1][1], pc[1][0]))
            k = min(k_s * MM, L0 * 0.5)
            sols.append(sweep_solid([pc[1][0], v_add(pc[1][0], v_mul(T0, k))], up, so_, si_)[0])
        if pc[0] == 'pipe':
            L = v_len(v_sub(pc[1][1], pc[1][0])) / MM
            parts.append(("Downpipe length - %s x %g mm" % (sname, round(L)), sols, tags))
            w = wall_of(pc[2])
            if s.get('auto_fix', True) and w and abs(v_dot(T0, w[0])) < 0.5:
                reach = (v_dot(w[0], pc[1][0]) - w[1]) / MM
                if reach > s['p_size'] / 2:
                    tgt = end_target(pc[1][-1], T0, route_up(T0, v_mul(w[0], -1.0)), 'out', 'pipe')
                    for x in fixing_positions(L, s['p_spacing']):
                        cw, _ = plan_part('clip', dict(s, offset=L - x, reach=reach), tgt)
                        clips += cw
                        nclip += 1
        else:
            parts.append(("Bend %g deg - %s" % (round(pc[2], 1), sname), sols, tags))
    if shoe is not None:
        w, _ = plan_part('shoe', dict(s, bend_dir=180.0), shoe)
        parts.append(("Shoe - %s" % sname, w, {}))
    if clips:
        parts.append(("Pipe clips x%d - %s" % (nclip, sname), clips, {}))
    return parts, notes


def wall_behind(top, bottom, n, faces, reach=2.5):
    """(n, d) of the wall face behind a downpipe line (under the eaves), facing the same way
    as the gutter's wall n, or None. Brickwork from Brick & Block Studio stands proud of the
    wall, so the front of the bricks counts (the outermost face found), not the wall behind
    or the mortar joints. Only looks part way down, so a plinth at the bottom or the fascia
    at the top doesn't push the pipe out. Faces count whichever way round they were made."""
    hits = []
    for f_ in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
        q = v_add(top, v_mul(v_sub(bottom, top), f_))
        near = None
        for face in faces:
            lo, hi = face[3]
            if q[2] < lo[2] - 0.003 or q[2] > hi[2] + 0.003:
                continue
            if any(q[k] < lo[k] - reach or q[k] > hi[k] + reach for k in (0, 1)):
                continue
            fn, fd = face[0], face[1]
            c = v_dot(fn, n)
            if c < -0.94:                       # made the other way round: turn it
                fn, fd = v_mul(fn, -1.0), -fd
            elif c < 0.94:
                continue
            t = v_dot(fn, q) - fd
            if t < 0.005 or t > reach:
                continue
            if (near is None or t < near[0]) and _r_on_face(v_sub(q, v_mul(fn, t)), face, 0.003):
                fp = v_norm((fn[0], fn[1], 0.0))
                near = (t, (fp, v_dot(fp, v_sub(q, v_mul(fn, t)))))
        if near is not None:
            hits.append(near)
    if not hits:
        return None
    # the face nearest the pipe at most heights: the front of the bricks, not the odd joint
    hits.sort(key=lambda h: h[0])
    return hits[min(len(hits) - 1, len(hits) // 3)][1]


SWAN_WHY = []


def swan_neck(path, gwall, faces, s):
    """A downpipe from a gutter outlet that's out from the wall (gutter on a fascia): two bends
    take it back in to the wall, then it runs down the wall. Returns (path, walls) or None."""
    if not gwall or len(path) < 2:
        SWAN_WHY.append("the gutter's wall wasn't known")
        return None
    n = v_norm((gwall[0][0], gwall[0][1], 0.0))
    if v_len(n) < 0.5:
        SWAN_WHY.append("the gutter's wall wasn't known")
        return None
    top, rest = path[0], list(path[1:])
    w = wall_behind(top, rest[-1], n, faces)
    if w is None:
        SWAN_WHY.append("no wall face was found behind the downpipe, between the eaves and the "
                        "ground" + (" (the model is very big - not every face was looked at)"
                                    if ROUTE_STATS.get('limit') else ""))
        return None
    n, dw = w
    ps = pipe_standoff(s) * MM
    off = (v_dot(n, top) - dw) - ps
    if off < 0.025:
        return None                       # the outlet is over where the pipe sits already: no need
    if any(v_dot(n, q) - dw < ps + 0.5 * off for q in rest):
        SWAN_WHY.append("the downpipe line was drawn in to the wall already, so it was followed as drawn")
        return None
    rest = [v_sub(q, v_mul(n, v_dot(n, q) - dw - ps)) for q in rest]
    R = s['p_size'] * 0.8 * MM
    lead = SOCKET_LEN * MM
    a = v_add(top, (0.0, 0.0, -(lead + R + 0.06)))      # a short length of pipe below the outlet
    b = v_add(v_sub(a, v_mul(n, off)), (0.0, 0.0, -off))       # 45 degrees in to the wall
    if b[2] < rest[0][2] + lead + R:
        SWAN_WHY.append("the downpipe was too short for the two bends")
        return None
    out = [top, a, b] + rest
    return out, [(n, dw)] * (len(out) - 1)


def _clip_slab(poly, lo, hi):
    """Cuts a polygon [(s, u, z)] down to lo <= s <= hi."""
    def cut(P, keep, edge):
        out = []
        for i in range(len(P)):
            a, b = P[i - 1], P[i]
            ia, ib = keep(a), keep(b)
            if ib:
                if not ia:
                    f = (edge - a[0]) / ((b[0] - a[0]) or 1e-30)
                    out.append(tuple(a[k] + (b[k] - a[k]) * f for k in range(3)))
                out.append(b)
            elif ia:
                f = (edge - a[0]) / ((b[0] - a[0]) or 1e-30)
                out.append(tuple(a[k] + (b[k] - a[k]) * f for k in range(3)))
        return out
    P = cut(list(poly), lambda p: p[0] >= lo, lo)
    if len(P) < 2:
        return []
    return cut(P, lambda p: p[0] <= hi, hi)


def avoid_obstacles(path, n, dw, all_faces, s, reach=4.0, step=0.01):
    """The bottom straight of a downpipe (path[-2] down to path[-1] on the ground) stepped out
    round anything in its way: a plinth, a sill, a lean-to roof and wall. Out at 45 degrees
    above the thing (or following a roof slope if there isn't the drop for 45), and back in
    below it where there's wall. Returns (new path, what) or (None, why or None)."""
    if len(path) < 2:
        return None, None
    top, bot = path[-2], path[-1]
    if math.hypot(top[0] - bot[0], top[1] - bot[1]) > 0.003 or top[2] - bot[2] < 0.2:
        return None, None                   # only a straight drop to the ground is looked at
    n = v_norm((n[0], n[1], 0.0))
    a_ = (-n[1], n[0], 0.0)                 # along the wall
    x0 = v_dot(a_, bot)
    u0 = v_dot(n, top) - dw                 # how far out the pipe runs now
    ps = pipe_standoff(s) * MM              # pipe middle to whatever it's clipped on
    hw = s['p_size'] * 0.5 * MM + 0.012     # the pipe's half width, and a little more
    z0, zb = top[2], bot[2]
    R = s['p_size'] * 0.8 * MM
    zst = z0 - (2.0 * SOCKET_LEN * MM + R)   # a straight below the top before any bend
    # what's in the way (not the fascia or soffit the outlet sits against, at the very top): every face cut down to the pipe's width, seen from the side (u, z)
    pts = []
    for f in all_faces:
        lo, hi = f[3]
        if hi[2] < zb + 0.004 or lo[2] > z0:
            continue
        P = [(v_dot(a_, p) - x0, v_dot(n, p) - dw, p[2]) for p in f[2]]
        if max(p[0] for p in P) < -hw or min(p[0] for p in P) > hw:
            continue
        if max(p[1] for p in P) < 0.004 or min(p[1] for p in P) > reach:
            continue
        C = _clip_slab(P, -hw, hw)
        for i in range(len(C)):
            p, q = C[i - 1], C[i]
            L = math.hypot(q[1] - p[1], q[2] - p[2])
            k = max(1, int(L / 0.005))
            for j in range(k + 1):
                u = p[1] + (q[1] - p[1]) * j / k
                z = p[2] + (q[2] - p[2]) * j / k
                if 0.004 < u < reach and zb + 0.004 < z < zst:
                    pts.append((u, z))
    if not pts:
        return None, None
    nz = int((z0 - zb) / step) + 1
    zs = [zb + i * (z0 - zb) / (nz - 1) for i in range(nz)]
    # how far out the pipe's middle must be at each height to clear it all by the stand-off
    req = [0.0] * nz
    span = int(ps / ((z0 - zb) / (nz - 1))) + 1
    for u, z in pts:
        c = int(round((z - zb) / (z0 - zb) * (nz - 1)))
        for i in range(max(0, c - span), min(nz, c + span + 1)):
            dz = zs[i] - z
            if abs(dz) <= ps:
                r = u + math.sqrt(ps * ps - dz * dz)
                if r > req[i]:
                    req[i] = r
    if max(req) <= u0 + 0.004:
        return None, None                   # nothing in the way
    # the pipe line: out at 45 degrees above each thing, in at 45 below it; shallower
    # (down to 10 degrees, following a roof) where there isn't the drop above it for 45
    kmax = 1.0 / math.tan(math.radians(10.0))
    U = []
    for i in range(nz):
        best = u0
        for j in range(nz):
            r = req[j]
            if r <= u0:
                continue
            d = zs[i] - zs[j]
            if d >= 0:                      # it's below: step out above it
                k = min(kmax, max(1.0, (r - u0) / max(1e-6, zst - zs[j])))
                v = r - k * d
            else:                           # it's above: back in below it
                v = r + d
            if v > best:
                best = v
        U.append(best)
    if U[-1] > u0 + 0.005:
        return None, "something sticks out too far just under the gutter for the pipe to get round it"
    # to a few points: corners only
    line = [(U[i], zs[i]) for i in range(nz - 1, -1, -1)]          # top first

    def simplify(P, tol):
        if len(P) < 3:
            return P
        a, b = P[0], P[-1]
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz) or 1e-12
        far, k = -1.0, 0
        for i in range(1, len(P) - 1):
            d = abs((P[i][0] - a[0]) * dz - (P[i][1] - a[1]) * dx) / L
            if d > far:
                far, k = d, i
        if far <= tol:
            return [a, b]
        return simplify(P[:k + 1], tol)[:-1] + simplify(P[k:], tol)
    need = 2.0 * (R * 0.45 + SOCKET_LEN * MM)   # room for the bends at both ends of a piece
    tol = 0.004
    S = simplify(line, tol)
    while len(S) > 2 and tol < 0.1 and min(math.hypot(S[i + 1][0] - S[i][0], S[i + 1][1] - S[i][1])
                                         for i in range(len(S) - 1)) < need:
        tol *= 1.6
        S = simplify(line, tol)
    # never inside: push each corner out to clear whatever was found at its height
    def req_at(z):
        i = int(round((z - zb) / (z0 - zb) * (nz - 1)))
        return req[max(0, min(nz - 1, i))]
    S = [(max(u, req_at(z)) if 0 < k < len(S) - 1 else u, z) for k, (u, z) in enumerate(S)]
    # nearly upright pieces made upright (out at the further of their two ends), so the pipe
    # runs straight down past things rather than at a slight lean
    for k in range(len(S) - 1):
        (ua, za), (ub, zb_) = S[k], S[k + 1]
        if abs(ua - ub) < 0.25 * abs(za - zb_) and abs(ua - ub) > 1e-6:
            um = max(ua, ub)
            if k > 0:
                S[k] = (um, za)
            if k + 1 < len(S) - 1:
                S[k + 1] = (um, zb_)
    S2 = [S[0]]
    for q in S[1:]:
        if math.hypot(q[0] - S2[-1][0], q[1] - S2[-1][1]) > 1e-4:
            S2.append(q)
    S = S2
    # always a short straight down out of the top (an outlet's spigot) before the first bend
    if len(S) >= 2 and abs(S[1][0] - S[0][0]) > 1e-4 and S[1][1] < zst - 1e-4:
        S.insert(1, (S[0][0], zst))
    base = v_add(v_mul(a_, x0), v_mul(n, dw))
    new = [(base[0] + n[0] * u, base[1] + n[1] * u, z) for u, z in S]
    new[0], new[-1] = top, (new[-1][0], new[-1][1], bot[2])
    out = list(path[:-2]) + new
    far = max(u for u, _z in S) - u0
    return out, "stepped out %d mm round something in the way" % int(round(far / MM))


def build_routes(chains, faces, s, all_faces=None):
    """Everything along the lines: level lines are gutters along the top of the wall, the
    others downpipes. A downpipe whose top is on a gutter line gets a running outlet there.
    Returns (parts, report)."""
    gsize, psize = size_text('gutter', s), size_text('pipe', s)
    flip = s.get('r_flip', False)
    gut = [(p, c) for p, c in chains if len(p) >= 2 and _level(p, c)]
    pip = [(p, c) for p, c in chains if len(p) >= 2 and not _level(p, c)]
    runs = [gutter_line(p, c, faces, s) for p, c in gut]
    dist, _drop = gutter_offsets(s)
    a_low, _z = gutter_low_point(s)
    outlets = [[] for _ in runs]
    downs = []
    for pts, closed in pip:
        P = [tuple(p) for p in pts] + ([tuple(pts[0])] if closed else [])
        if P[-1][2] > P[0][2]:
            P = list(reversed(P))                     # top first
        walls = [segment_wall(a, b, faces, flip=flip) for a, b in zip(P[:-1], P[1:])]
        # does its top start on one of the gutter lines?
        best = None
        for r, run in enumerate(runs):
            d, dz = _near_raw(run, P[0])
            if d < 0.4 and -0.6 < dz < 0.6 and (best is None or d < best[0]):
                best = (d, r)
        sp = (dist - a_low) if best else pipe_standoff(s)
        Qp = []
        for j in range(len(P)):
            cons = [(walls[k][0], sp * MM) for k in (j - 1, j) if 0 <= k < len(walls) and walls[k]]
            Qp.append(v_add(P[j], _r_offset(cons)))
        item = {'Q': Qp, 'walls': walls, 'run': None}
        if best:
            run = runs[best[1]]
            _d, so = _nearest_on_run(run, Qp[0])
            item['run'] = best[1]
            item['k'] = len(outlets[best[1]])
            outlets[best[1]].append(so)
            j = min(len(run['N']) - 1, _at(run, so)[2])
            item['gwall'] = run['N'][j]
        downs.append(item)
    parts, notes, spig = [], [], {}
    for r, run in enumerate(runs):
        p, sg, nt = build_gutter_run(run, outlets[r], s, gsize)
        parts += p
        notes += nt
        for k, port_ in sg.items():
            spig[(r, k)] = port_
    nd = 0
    nswan = 0
    navoid = 0
    del SWAN_WHY[:]
    for item in downs:
        Qp, walls = item['Q'], list(item['walls'])
        connected = False
        pre_swan = None
        if item['run'] is not None and (item['run'], item['k']) in spig:
            sp_ = spig[(item['run'], item['k'])]
            top = tuple(sp_['c'])
            rest = [q for q in Qp[1:] if q[2] < top[2] - 0.005]
            first = len(Qp) - len(rest)            # which drawn point the pipe heads for first
            path = [top] + rest
            walls = walls[first - 1:] if first >= 1 else walls
            walls = [w or item['gwall'] for w in walls] if walls else [item['gwall']]
            connected = True
            if s.get('r_swan', True):
                try:
                    sw = swan_neck(path, item['gwall'], faces, s)
                except Exception as e:
                    sw = None
                    print("%s: swan neck: %s" % (PLUGIN_NAME, e))
                if sw:
                    pre_swan = path
                    path, walls = sw
                    nswan += 1
        else:
            path = Qp
            if s.get('r_swan', True) and item['run'] is None:
                SWAN_WHY.append("a downpipe didn't start on a gutter line (start it on the gutter: "
                                "the green or blue ring)")
        if len(path) < 2:
            notes.append("a downpipe had nothing below its outlet")
            continue
        if s.get('r_avoid', True) and all_faces:
            try:
                wn = next((w for w in reversed(walls) if w), None) or item.get('gwall')
                wb = None
                if wn:
                    wb = wall_behind(path[-2], path[-1], v_norm((wn[0][0], wn[0][1], 0.0)), faces) or \
                        (v_norm((wn[0][0], wn[0][1], 0.0)), wn[1])
                if wb:
                    newp, why = avoid_obstacles(path, wb[0], wb[1], all_faces, s)
                    if newp and pre_swan is not None:
                        # going out past the outlet anyway (a lean-to): no swan neck in to the
                        # wall first - straight from the outlet, out over it
                        umax = max(v_dot(wb[0], q) - wb[1] for q in newp)
                        uout = v_dot(wb[0], pre_swan[0]) - wb[1]
                        if umax > uout - 0.01:
                            t0 = pre_swan[0]
                            p2, why2 = avoid_obstacles([t0, (t0[0], t0[1], path[-1][2])], wb[0], wb[1],
                                                       all_faces, s)
                            if p2:
                                newp = p2
                                nswan -= 1
                    if newp:
                        path = newp
                        walls = [wb] * (len(path) - 1)
                        navoid += 1
                    elif why:
                        notes.append(why)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print("%s: stepping round things: %s" % (PLUGIN_NAME, e))
        p, nt = build_downpipe(path, walls, s, psize, connected)
        parts += p
        notes += nt
        nd += 1
    msg = []
    if runs:
        msg.append("%d gutter run%s" % (len(runs), "" if len(runs) == 1 else "s"))
    if nd:
        msg.append("%d downpipe%s" % (nd, "" if nd == 1 else "s"))
    nout = sum(len(o) for o in outlets)
    if nout:
        msg.append("%d running outlet%s" % (nout, "" if nout == 1 else "s"))
    if nswan:
        msg.append("%d swan neck%s back to the wall" % (nswan, "" if nswan == 1 else "s"))
    if navoid:
        msg.append("%d downpipe%s stepped round something in the way" % (navoid, "" if navoid == 1 else "s"))
    for why in SWAN_WHY:
        if ("no swan neck: " + why) not in notes:
            notes.append("no swan neck: " + why)
    nowall = sum(run['segs'] - run['found'] for run in runs)
    if runs and nowall:
        notes.append("%d gutter stretch%s had no wall face under the line, so the 'No wall found' "
                     "setting was used" % (nowall, "" if nowall == 1 else "es"))
    return parts, ", ".join(msg), notes


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
 '@cb_preset': 'Ready-made settings. Pick one and the whole window is filled in.',
 'Add part': 'Builds the part picked on the Part page, joined onto the open end (or at the origin, or on '
             'the wall you picked).',
 'Profile': 'The shape of the gutter.',
 'Shape': 'Round or square downpipe.',
 'Direction': 'Which way the bend, branch or shoe turns.'}
EDDY_TIPS_END = None


class PartPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(180, 140)
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

class GutterKey(QWidget):
    """What each lettered size is: the gutter and pipe end on, and a run along a wall."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 345)       # drawn to scale, so it fits whatever size

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
        from PySide6.QtCore import QPointF, QRectF, Qt
        import math as _m
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 246))
        k = min(float(self.width()) / 360.0, self.height() / 565.0)
        p.scale(k, k)
        red = QColor(200, 40, 40)
        gut, wallc, brick = QColor(70, 74, 80), QColor(200, 196, 188), QColor(178, 90, 60)
        f = QFont()
        f.setBold(True)
        f.setPointSizeF(9.5)
        p.setFont(f)

        def box(x, y, w, h, col):
            p.setPen(QPen(col.darker(160), 0.8))
            p.setBrush(col)
            p.drawRect(QRectF(x, y, w, h))

        def dim(x1, y1, x2, y2, letter, tx, ty):
            p.setPen(QPen(red, 1.1))
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            ang = _m.atan2(y2 - y1, x2 - x1)
            for (x, y, a) in ((x1, y1, ang), (x2, y2, ang + _m.pi)):
                for s_ in (0.45, -0.45):
                    p.drawLine(QPointF(x, y), QPointF(x + 6 * _m.cos(a + s_), y + 6 * _m.sin(a + s_)))
            p.setPen(red)
            p.drawText(QRectF(tx - 12, ty - 9, 24, 18), Qt.AlignCenter, letter)

        def title(x, y, t):
            p.setPen(QColor(60, 60, 60))
            p.setFont(f)
            p.drawText(QRectF(x, y, 340, 18), Qt.AlignLeft, t)

        # ---- the gutter end on, on its bracket at the wall
        title(10, 4, "The gutter end on")
        box(20, 30, 26, 120, wallc)                     # the wall
        box(14, 30, 6, 120, brick)
        cx, cy, R, t = 110.0, 60.0, 44.0, 5.0
        path = QPainterPath()
        path.moveTo(cx - R, cy)
        path.arcTo(QRectF(cx - R, cy - R, 2 * R, 2 * R), 180, 180)
        path.lineTo(cx + R - t, cy)
        path.arcTo(QRectF(cx - R + t, cy - R + t, 2 * (R - t), 2 * (R - t)), 0, -180)
        path.closeSubpath()
        p.setPen(QPen(gut.darker(140), 0.8))
        p.setBrush(gut)
        p.drawPath(path)
        dim(cx - R, cy - 12, cx + R, cy - 12, "A", cx, cy - 22)
        dim(cx + R + 10, cy, cx + R + 10, cy + R, "B", cx + R + 22, cy + R / 2)
        dim(cx - 6, cy + R - t, cx - 6, cy + R, "C", cx - 18, cy + R + 10)
        dim(46, cy + R + 22, cx - R, cy + R + 22, "M", (46 + cx - R) / 2, cy + R + 34)
        dim(60, 30, 60, cy, "L", 70, 42)
        p.setPen(QPen(QColor(120, 120, 120), 0.6, Qt.DashLine))
        p.drawLine(QPointF(46, 30), QPointF(70, 30))

        # ---- the downpipe end on
        title(200, 4, "The downpipe end on")
        px, py, pr = 280.0, 75.0, 32.0
        p.setPen(QPen(gut.darker(140), 0.8))
        p.setBrush(gut)
        p.drawEllipse(QPointF(px, py), pr, pr)
        p.setBrush(QColor(250, 250, 246))
        p.drawEllipse(QPointF(px, py), pr - 5, pr - 5)
        dim(px - pr, py + pr + 12, px + pr, py + pr + 12, "D", px, py + pr + 24)
        dim(px + pr - 5, py, px + pr, py, "E", px + pr + 12, py - 8)

        # ---- a run along the wall, from the front
        title(10, 175, "A run along the wall, from the front")
        WX0, WX1, WY = 70.0, 290.0, 215.0
        box(WX0, WY, WX1 - WX0, 150, wallc)            # the wall
        for i in range(7):
            p.setPen(QPen(brick, 0.6))
            p.drawLine(QPointF(WX0, WY + 20 + i * 18), QPointF(WX1, WY + 20 + i * 18))
        gx0, gx1, gy = WX0 - 26, WX1 - 40, WY + 8
        box(gx0, gy, gx1 - gx0, 14, gut)               # the gutter
        box(gx1, gy, 30, 14, QColor(110, 115, 122))    # running outlet
        box(gx1 + 8, gy + 14, 14, 160, gut)            # downpipe
        for bx in (gx0 + 20, gx0 + 110, gx0 + 200):
            box(bx, gy - 3, 5, 20, QColor(30, 30, 30))  # fascia brackets
        for cy_ in (gy + 60, gy + 140):
            box(gx1 + 4, cy_, 22, 5, QColor(30, 30, 30))   # pipe clips
        dim(gx0, gy - 14, WX0, gy - 14, "N", (gx0 + WX0) / 2, gy - 26)
        dim(gx0 + 22.5, gy + 32, gx0 + 112.5, gy + 32, "Q", gx0 + 67, gy + 44)
        dim(gx0, gy + 70, gx1, gy + 70, "F", (gx0 + gx1) / 2, gy + 82)
        dim(gx1, gy - 14, gx1 + 30, gy - 14, "G", gx1 + 15, gy - 26)
        dim(gx1 + 34, gy + 62, gx1 + 34, gy + 142, "R", gx1 + 46, gy + 102)
        dim(WX1, gy + 28, gx1 + 30, gy + 28, "P", (WX1 + gx1 + 30) / 2, gy + 40)

        f2 = QFont()
        f2.setPointSizeF(8.5)
        p.setFont(f2)
        p.setPen(QColor(60, 60, 60))
        notes = ["A  gutter width", "B  gutter depth", "C  gutter wall thickness", "D  downpipe size",
                 "E  downpipe wall thickness", "F  length of a gutter / downpipe", "G  running outlet length",
                 "H  angle leg length (each side)", "J  branch length", "K  distance back from the end",
                 "L  gutter top below the wall top", "M  extra gap from the wall", "N  past the left end",
                 "P  past the right end (minus = short)", "Q  gutter brackets at most", "R  pipe clips at most",
                 "S  longest gutter length", "T  bend turn angle", "U  longest downpipe length"]
        for i, t_ in enumerate(notes):
            p.drawText(QRectF(10 if i < 10 else 185, 400 + (i % 10) * 15.5, 175, 14),
                       Qt.AlignLeft | Qt.AlignVCenter, t_)
        p.end()


UI_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_gutters_downpipes.json")


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


INFO_TEXT = ("<b>Follow lines (the quick way)</b><br>"
             "Draw lines where you want everything to go: along the top outside edge of the wall for each "
             "gutter run (corner to corner, level), and down the wall for each downpipe, starting on the "
             "gutter line. Select all the lines, go to the Follow lines page and click 'Build along selected "
             "lines'. The gutter gets its angles, unions, brackets and stop ends, a running outlet goes where "
             "each downpipe starts, and the downpipes get bends wherever your line turns, sockets, clips and "
             "a shoe at the bottom. With the gutter on a fascia, just draw the downpipe straight down from "
             "the gutter: it gets a swan neck under the eaves that takes it back to the wall, and on the way down "
             "it steps out round a plinth, a sill or a lean-to roof and back in below it.<br><br>"
             "<b>Hard to see the thin lines?</b><br>"
             "Use 'Mark the run' on the Follow lines page instead of drawing lines: click the points and "
             "the plugin draws a thick, bright line (set its thickness and colour there). Enter or "
             "double-click ends a line, Esc again when you've finished; it snaps to the ends of your marked "
             "lines and onto them. Backspace takes a point off. Arrow keys lock the line to an "
             "axis: Right = red, Left = green, Up = blue (up and down the wall), Down = free. "
             "Everything built along lines goes into one group (untick that on the Follow lines page)."
             "<br><br>"
             "<b>One part at a time</b><br>"
             "Pick a part on the Part page and click 'Add part'. The first one goes at the origin - or select "
             "a wall face, click 'Use selected wall' (On a wall page) and the gutter runs along its top. Each "
             "part joins onto the open end of the last one; select the open end of any part you placed and "
             "click 'Use selected end' to carry on from there.<br><br>"
             "<b>Sizes</b><br>The gutter and downpipe sizes are on their own pages; the letters are on the Key "
             "page. Click a part in the model and the settings that made it light up.<br><br>"
             "<b>Printing</b><br>Tick 'Solid' and 'Chunky fittings' for small scales. Sizes are real-world mm "
             "- Scale Studio takes it down to your model scale.")

# which settings make each part, found from its group name when you click it in the model
PIECE_KEYS = [("Fascia brackets", ('g_spacing',)), ("Pipe clips", ('p_spacing',)),
              ("Gutter length", ('length', 'g_width', 'g_depth', 'g_wall')),
              ("Running outlet", ('outlet_len', 'g_width')), ("angle", ('leg', 'g_width')),
              ("Downpipe length", ('length', 'p_size', 'p_wall')), ("Bend", ('bend_turn', 'p_size')),
              ("Branch", ('branch_len', 'bend_turn', 'p_size')), ("Union", ('offset', 'g_width')),
              ("Fascia bracket", ('offset', 'g_width')), ("Pipe socket", ('offset', 'p_size')),
              ("Pipe clip", ('offset', 'p_size')), ("Stop end", ('g_width', 'g_depth')),
              ("Shoe", ('p_size',)), ("Hopper head", ('p_size',)), ("Gutter ", ('leg', 'g_width')),
              ("Union brackets", ('g_width',)), ("Stop ends", ('g_width',))]

# ---------------------------------------------------------------------------
# Mark the run - the plugin's own thick line, drawn over the model so it shows up
# against bricks and tiles. Click the points (IngeTrazo's snapping works as usual),
# Enter or double-click finishes a run, Backspace takes the last point off, Esc stops.
# ---------------------------------------------------------------------------
MARK_DEFAULT_PX = 5
MARK_DEFAULT_RGB = (255, 214, 0)          # bright yellow, with a dark edge round it
AXIS_NAMES = ("red (X)", "green (Y)", "blue (Z, up and down)")
AXIS_RGB = ((230, 40, 40), (40, 170, 60), (40, 90, 235))


def _px(vp, q):
    """Screen position of a world point, or None (behind the camera)."""
    f = getattr(vp, 'world_to_pixel', None) or getattr(vp, '_world_to_pixel', None)
    if f is None:
        return None
    try:
        r = f(q)
    except Exception:
        return None
    if r is None:
        return None
    try:
        return float(r[0]), float(r[1])
    except Exception:
        try:
            return float(r.x()), float(r.y())
        except Exception:
            return None


def _mark_segments_px(vp, segs):
    """World segments [(a, b)] as screen segments, cut to the view."""
    out = []
    clip = getattr(vp, '_clip_pixel_line', None)
    for a, b in segs:
        pa, pb = _px(vp, QVector3D(*a)), _px(vp, QVector3D(*b))
        if pa is None or pb is None:
            continue
        if clip is not None:
            try:
                seg = clip(pa, pb, margin=0.0)
            except Exception:
                seg = (pa, pb)
            if seg is None:
                continue
            pa, pb = seg
        out.append((pa, pb))
    return out


def make_mark_tool(dlg):
    """The clicking tool, made here (not at module level, so it gets no menu entry of its own)."""
    from PySide6.QtCore import Qt

    class _MarkTool(Tool):
        name = "Gutters & Downpipes - mark the run"
        shortcut = None
        uses_snap = True
        wireframe_color = (1.0, 0.84, 0.0, 1.0)

        def on_activate(self, viewport):
            dlg.mark_hover = None

        def on_deactivate(self, viewport):
            dlg.mark_hover = None
            dlg.mark_tool_gone(self)

        def on_hover(self, ctx):
            try:
                q = ctx.world
                dlg.mark_hover = dlg.mark_snap(dlg.mark_constrain((float(q.x()), float(q.y()), float(q.z()))))
                ctx.viewport.update()
            except Exception:
                pass

        def on_click(self, ctx):
            try:
                q = ctx.world
                dlg.mark_clicked(dlg.mark_snap(dlg.mark_constrain((float(q.x()), float(q.y()), float(q.z())))))
            except Exception as e:
                print("%s: marking: %s" % (PLUGIN_NAME, e))

        def on_double_click(self, ctx):
            dlg.mark_finish_run()

        def on_key(self, viewport, key, modifiers):
            return dlg.mark_key(key)

        def on_cancel(self, viewport):
            # IngeTrazo sends Esc to the tool here: end this line, or (again) finished marking
            dlg.mark_key(Qt.Key_Escape)

        def status_clause(self):
            lk = dlg.mark_lock
            t = ("Locked to %s. " % AXIS_NAMES[lk]) if lk is not None else ""
            return (t + "Mark the run: click the points. Arrows lock to an axis (Right = red, Left = green, "
                    "Up = blue, Down = free). Esc, right-click, Enter or double-click = end this line, "
                    "Esc or right-click again = finished marking, Backspace = take the last point off")

        def rubber_band_lines(self):
            return []                 # the plugin draws its own thick line instead
    return _MarkTool()



# ---------------------------------------------------------------------------
# Dialog - laid out like the other plugins: pictures on the left, pages on the right
# ---------------------------------------------------------------------------
class DrainDialog(QDialog):
    CUSTOM = "-- Custom --"

    def __init__(self, cur, target, viewport, tool):
        super().__init__(viewport)
        from PySide6.QtWidgets import QTabWidget, QScrollArea
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.target = target
        self.open_ends = []        # every open end added in this window that isn't joined yet
        self.history = []          # window state before each part, for stepping back after a delete
        self.wall = None           # a picked wall the first gutter goes on
        self.wall_face = None
        self.marks = []            # runs marked with the thick line: lists of world points
        self.mark_run = []         # the run being marked now
        self.mark_hover = None
        self.marking = False
        self.mark_tool = None
        self.mark_lock = None      # 0, 1, 2 = locked to X, Y, Z (arrow keys); None = free
        self._hid_for_marking = False
        self.mark_snapped = None   # (point, 'end' or 'on') when the mouse is on a marked line
        self.user_presets = load_presets()
        lay = QVBoxLayout(self)

        # how to use it - only shows when Info is pressed
        self.info_box = QWidget()
        ib = QVBoxLayout(self.info_box)
        ib.setContentsMargins(0, 0, 0, 0)
        lbl_info = QLabel(INFO_TEXT)
        lbl_info.setWordWrap(True)
        ib.addWidget(lbl_info)
        self.info_box.setVisible(False)
        lay.addWidget(self.info_box)

        self.lbl_target = QLabel()
        self.lbl_target.setWordWrap(True)
        self.lbl_target.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl_target)

        def mm_spin(val, lo=0.1, hi=100000.0, suffix=" mm", dec=1):
            sp = QDoubleSpinBox()
            sp.setDecimals(dec)
            sp.setRange(lo, hi)
            sp.setSuffix(suffix)
            sp.setValue(val)
            return sp

        row = QHBoxLayout()
        lay.addLayout(row)
        # ---- left: the preview and the key
        self.left = QTabWidget()
        pv = QWidget()
        pvl = QVBoxLayout(pv)
        pvl.setContentsMargins(4, 4, 4, 4)
        self.preview = PartPreview()
        self.preview.setMinimumSize(190, 160)
        pvl.addWidget(self.preview, 1)
        cap = QLabel("Brown panel = the wall. Pale grey = the part it fits over.")
        cap.setStyleSheet("color: gray; font-size: 9pt;")
        pvl.addWidget(cap)
        self.left.addTab(pv, "Preview")
        ks = QScrollArea()
        ks.setWidgetResizable(True)
        ks.setWidget(GutterKey())
        self.left.addTab(ks, "Key (A, B, C...)")
        self.left.setTabToolTip(1, "What each lettered size is.")
        self.left.setMaximumWidth(300)    # the preview side stays small; the pages get the room
        row.addWidget(self.left, 2)
        # ---- right: the pages
        self.tabs = QTabWidget()
        row.addWidget(self.tabs, 3)
        self.keyw = {}                    # setting -> (box, label), to light up
        self.page_of = {}

        def add_row(form, key, label, w, tip=None):
            lab = QLabel(label)
            if tip:
                w.setToolTip(tip)
                lab.setToolTip(tip)
            form.addRow(lab, w)
            self.keyw[key] = (w, lab)
            self.page_of[key] = self.tabs.count() - 1
            return lab

        # Part page: what to add next
        page = QWidget()
        sf = QFormLayout(page)
        self.tabs.addTab(page, "Part")
        self.lst = QListWidget()
        self.lst.setMinimumHeight(250)
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
        sf.addRow(self.lst)
        self.sp = {
            'length': mm_spin(cur['length'], 1.0),
            'outlet_len': mm_spin(cur['outlet_len'], 20.0),
            'leg': mm_spin(cur['leg'], 10.0),
            'bend_turn': mm_spin(cur['bend_turn'], 1.0, 135.0, " deg"),
            'branch_len': mm_spin(cur['branch_len'], 20.0),
            'offset': mm_spin(cur['offset'], 0.0),
        }
        tips = {'bend_turn': "How far the pipe turns. A 112.5 deg offset bend turns 67.5; a 92.5 deg bend "
                             "turns 87.5; a 135 deg bend turns 45.",
                'offset': "0 = centred on the end you selected. Larger values slide it back along the part.",
                'length': "How long the gutter or downpipe length is.",
                'outlet_len': "How long the running outlet is, along the gutter.",
                'leg': "How long each leg of the angle is.",
                'branch_len': "How long the branch of the Y junction is."}
        self.cb_dir = QComboBox()
        for label, deg in BEND_DIRS:
            self.cb_dir.addItem(label, deg)
            if abs(deg - cur['bend_dir']) < 1e-6:
                self.cb_dir.setCurrentIndex(self.cb_dir.count() - 1)
        labels = {'length': "F   Length", 'outlet_len': "G   Outlet length", 'leg': "H   Leg length (each side)",
                  'bend_turn': "T   Turn angle", 'branch_len': "J   Branch length",
                  'offset': "K   Distance back from the end"}
        self.rows = {}
        for k in ('length', 'outlet_len', 'leg', 'bend_turn', 'branch_len', 'offset'):
            lab = add_row(sf, k, labels[k], self.sp[k], tips.get(k))
            self.rows[k] = (lab, self.sp[k])
        lab = QLabel("Direction")
        sf.addRow(lab, self.cb_dir)
        self.rows['bend_dir'] = (lab, self.cb_dir)
        self.cb_wall = QComboBox()
        for label, deg in WALL_SIDES:
            self.cb_wall.addItem(label, deg)
            if abs(deg - cur.get('wall_side', 0.0)) < 1e-6:
                self.cb_wall.setCurrentIndex(self.cb_wall.count() - 1)
        self.cb_wall.setToolTip("Which side the wall is on when a new run starts at the origin. "
                                "Parts joined onto an end follow that end instead.")
        sf.addRow("New run - wall is", self.cb_wall)
        self.cb_solid = QCheckBox("Solid (for 3D printing) - no hollow inside")
        self.cb_solid.setChecked(bool(cur.get('solid')))
        self.cb_solid.setToolTip("Fills the gutters and pipes in, so small-scale prints come out "
                                 "strong. Fit-over parts (unions, sockets, clips) stay as sleeves.")
        sf.addRow(self.cb_solid)
        self.cb_detail = QCheckBox("Detailed fittings")
        self.cb_detail.setChecked(bool(cur.get('g_detail', True)))
        self.cb_detail.setToolTip("Adds the real-life bits: the bead along the front of the gutter, clip-in "
                                  "ends and hooks on unions, angles and outlets, screw heads on brackets, "
                                  "sockets on downpipes, bolted pipe clips and a lip on the shoe.")
        sf.addRow(self.cb_detail)

        # Gutter page
        page = QWidget()
        gf = QFormLayout(page)
        self.tabs.addTab(page, "Gutter")
        self.cb_gprof = QComboBox()
        for label, key in GUTTER_PROFILES:
            self.cb_gprof.addItem(label, key)
            if key == cur['g_profile']:
                self.cb_gprof.setCurrentIndex(self.cb_gprof.count() - 1)
        gf.addRow("Profile", self.cb_gprof)
        self.sp_gw = mm_spin(cur['g_width'], 10.0)
        self.sp_gd = mm_spin(cur['g_depth'], 5.0)
        self.sp_gt = mm_spin(cur['g_wall'], 0.5, 50.0)
        add_row(gf, 'g_width', "A   Width", self.sp_gw, "How wide the gutter is, across the top.")
        add_row(gf, 'g_depth', "B   Depth", self.sp_gd, "How deep the gutter is (half the width for half-round).")
        add_row(gf, 'g_wall', "C   Wall thickness", self.sp_gt, "How thick the gutter's wall is.")
        gn = QLabel("Half-round gutters are always half as deep as they're wide.")
        gn.setWordWrap(True)
        gn.setStyleSheet("color: gray;")
        gf.addRow(gn)

        # Downpipe page
        page = QWidget()
        pf = QFormLayout(page)
        self.tabs.addTab(page, "Downpipe")
        self.cb_ptype = QComboBox()
        for label, key in PIPE_TYPES:
            self.cb_ptype.addItem(label, key)
            if key == cur['p_type']:
                self.cb_ptype.setCurrentIndex(self.cb_ptype.count() - 1)
        pf.addRow("Shape", self.cb_ptype)
        self.sp_ps = mm_spin(cur['p_size'], 10.0)
        self.sp_pt = mm_spin(cur['p_wall'], 0.5, 50.0)
        self.lbl_ps = add_row(pf, 'p_size', "D   Diameter", self.sp_ps, "How big the downpipe is across.")
        add_row(pf, 'p_wall', "E   Wall thickness", self.sp_pt, "How thick the pipe's wall is.")

        # On a wall page
        page = QWidget()
        wf = QFormLayout(page)
        self.tabs.addTab(page, "On a wall")
        wi = QLabel("Start a gutter on a wall: select a wall face, then click 'Use selected wall'. The next "
                    "gutter part runs along the top of that wall.")
        wi.setWordWrap(True)
        wf.addRow(wi)
        b_wall = QPushButton("Use selected wall")
        b_wall.setToolTip("Select a wall face, then click this. The next gutter part runs along "
                          "the top of that wall.")
        b_wall.clicked.connect(self.use_selected_wall)
        wf.addRow(b_wall)
        self.sp_drop = mm_spin(cur['drop'], 0.0)
        self.sp_wgap = mm_spin(cur['wall_gap'], 0.0)
        self.sp_ovl = mm_spin(cur['over_left'], -100000.0)
        self.sp_ovr = mm_spin(cur['over_right'], -100000.0)
        add_row(wf, 'drop', "L   Below top of wall", self.sp_drop,
                "How far the top of the gutter sits below the top of the wall.")
        add_row(wf, 'wall_gap', "M   Extra gap from wall", self.sp_wgap,
                "0 = fascia brackets sit flat on the wall. More moves the gutter out.")
        add_row(wf, 'over_left', "N   Past left end", self.sp_ovl,
                "How far the gutter runs past the left end of the wall, as you look at it from outside. "
                "Negative stops short of the end, leaving room for a running outlet, angle or stop end.")
        add_row(wf, 'over_right', "P   Past right end", self.sp_ovr,
                "Same for the right end. Negative stops short of the end.")
        self.cb_fit = QCheckBox("Gutter length = wall length")
        self.cb_fit.setChecked(cur['fit_wall'])
        self.cb_flip = QCheckBox("Wrong side? Put it on the other side of the wall")
        self.cb_flip.setChecked(cur['wall_flip'])
        self.cb_flip.toggled.connect(self.reread_wall)
        wf.addRow(self.cb_fit)
        wf.addRow(self.cb_flip)

        # Brackets & clips page
        page = QWidget()
        ff = QFormLayout(page)
        self.tabs.addTab(page, "Brackets & clips")
        self.cb_fix = QCheckBox("Add them evenly with every gutter / downpipe length")
        self.cb_fix.setChecked(cur['auto_fix'])
        ff.addRow(self.cb_fix)
        self.sp_gsp = mm_spin(cur['g_spacing'], 100.0)
        self.sp_psp = mm_spin(cur['p_spacing'], 100.0)
        add_row(ff, 'g_spacing', "Q   Gutter brackets at most", self.sp_gsp,
                "Most a fascia bracket can be from the next one. One also goes near each end.")
        add_row(ff, 'p_spacing', "R   Pipe clips at most", self.sp_psp,
                "Most a pipe clip can be from the next one. One also goes near each end.")
        self.cb_chunky = QCheckBox("Chunky fittings (for 3D printing)")
        self.cb_chunky.setChecked(cur['chunky'])
        self.cb_chunky.setToolTip("Makes every bracket, clip, union, socket and stop end thicker "
                                  "and wider so they survive printing at small scales.")
        ff.addRow(self.cb_chunky)
        self.sp_chunk = mm_spin(cur['chunk_mult'], 1.0, 10.0, " x", 1)
        add_row(ff, 'chunk_mult', "Thicker by", self.sp_chunk, "How many times thicker than real fittings.")
        self.cb_chunky.toggled.connect(self.sp_chunk.setEnabled)
        self.sp_chunk.setEnabled(self.cb_chunky.isChecked())
        self.cb_chunky.toggled.connect(self.sync)
        self.sp_chunk.valueChanged.connect(self.sync)
        self.cb_fix.toggled.connect(lambda on: (self.sp_gsp.setEnabled(on), self.sp_psp.setEnabled(on)))
        self.sp_gsp.setEnabled(self.cb_fix.isChecked())
        self.sp_psp.setEnabled(self.cb_fix.isChecked())

        # Follow lines page: build the lot along lines you've drawn
        page = QWidget()
        rf = QFormLayout(page)
        self.tabs.addTab(page, "Follow lines")
        ri = QLabel("Draw lines where it all goes: along the top outside edge of the wall for each gutter "
                    "(level, corner to corner) and down the wall for each downpipe, starting on the gutter "
                    "line. Select the lines (you can select the wall faces too) and click the button.")
        ri.setWordWrap(True)
        rf.addRow(ri)
        b_route = QPushButton("Build along lines")
        b_route.setToolTip("Builds gutters along the level lines and downpipes down the others, with all "
                           "their fittings. Uses your marked runs if there are any, otherwise the lines "
                           "you've selected. One undo takes it all away again.")
        b_route.clicked.connect(lambda: self.tool.build_route(self))
        rf.addRow(b_route)
        self.sp_gmax = mm_spin(cur['g_maxlen'], 0.0)
        self.sp_pmax = mm_spin(cur['p_maxlen'], 0.0)
        add_row(rf, 'g_maxlen', "S   Longest gutter length", self.sp_gmax,
                "Longer stretches are cut into lengths no longer than this, joined with union brackets. "
                "0 = one length per stretch.")
        add_row(rf, 'p_maxlen', "U   Longest downpipe length", self.sp_pmax,
                "Longer stretches of downpipe are cut into lengths no longer than this, each with its "
                "socket. 0 = one length per stretch.")
        self.cb_rstops = QCheckBox("Stop ends on the open ends of each gutter")
        self.cb_rstops.setChecked(bool(cur.get('r_stops', True)))
        self.cb_rshoe = QCheckBox("Shoe at the bottom of each downpipe")
        self.cb_rshoe.setChecked(bool(cur.get('r_shoe', True)))
        rf.addRow(self.cb_rstops)
        rf.addRow(self.cb_rshoe)
        self.cb_rswan = QCheckBox("Swan neck back to the wall (gutter on a fascia)")
        self.cb_rswan.setChecked(bool(cur.get('r_swan', True)))
        self.cb_rswan.setToolTip("Draw the downpipe line straight down from the gutter: where the gutter is "
                                 "out on a fascia, the pipe gets two bends under the eaves that take it back "
                                 "to the wall, then runs down the wall on its clips.")
        rf.addRow(self.cb_rswan)
        self.cb_ravoid = QCheckBox("Step out round anything in the way (plinth, sill, lean-to...)")
        self.cb_ravoid.setChecked(bool(cur.get('r_avoid', True)))
        self.cb_ravoid.setToolTip("On the way down to the ground, the downpipe steps out (45 degree bends, or "
                                  "following a roof slope) over anything that sticks out in its way, and back "
                                  "in below it where there's wall to come back to.")
        rf.addRow(self.cb_ravoid)
        self.cb_rside = QComboBox()
        for label, key in ROUTE_SIDES:
            self.cb_rside.addItem(label, key)
            if key == cur.get('r_side', 'right'):
                self.cb_rside.setCurrentIndex(self.cb_rside.count() - 1)
        self.cb_rside.setToolTip("The wall is normally found from the model, under the line. Where it can't "
                                 "be found (a line drawn in mid-air), this says which side the wall is on. "
                                 "A closed loop always has the walls inside it.")
        rf.addRow("No wall found? The wall is", self.cb_rside)
        self.cb_rflip = QCheckBox("Wrong side? Put it on the other side of the wall")
        self.cb_rflip.setChecked(bool(cur.get('r_flip', False)))
        rf.addRow(self.cb_rflip)
        rn = QLabel("Also uses L and M (On a wall page), the gutter and downpipe sizes, and Brackets & clips.")
        rn.setWordWrap(True)
        rn.setStyleSheet("color: gray;")
        rf.addRow(rn)

        # Mark the run: the plugin's own thick line, easy to see on a detailed building
        gm = QGroupBox("Mark the run (thick line, easy to see)")
        gml = QFormLayout(gm)
        mi = QLabel("Instead of drawing thin lines: click 'Mark the run', then click along the top outside "
                    "edge of the wall for a gutter, or down the wall for a downpipe (start on the gutter "
                    "line). The window hides while you mark and comes back when you've finished. Arrow keys lock the line to an axis: Right = red, Left = green, Up = blue (up and "
                    "down the wall), Down = free again. Esc or right-click (or Enter / double-click) ends the line you're "
                    "on - then click to start the next one; it snaps to the ends of your marked lines and "
                    "onto them, so a downpipe starts right on the gutter. Backspace takes the last point "
                    "off. Esc or right-click again when you've finished marking. Then click "
                    "'Build along lines'.")
        mi.setWordWrap(True)
        gml.addRow(mi)
        mrow = QHBoxLayout()
        self.b_mark = QPushButton("Mark the run")
        self.b_mark.setCheckable(True)
        self.b_mark.setToolTip("Starts clicking points. IngeTrazo's snapping works as normal, but the line "
                               "is drawn thick and bright by this plugin.")
        self.b_mark.toggled.connect(lambda on: self.start_marking() if on else self.stop_marking())
        b_mclear = QPushButton("Clear marks")
        b_mclear.setToolTip("Takes all the marked runs away (nothing in the model is changed).")
        b_mclear.clicked.connect(self.clear_marks)
        mrow.addWidget(self.b_mark)
        mrow.addWidget(b_mclear)
        mrow.addStretch(1)
        gml.addRow(mrow)
        mst = _ui_settings()
        from PySide6.QtWidgets import QSpinBox
        self.sp_mark_px = QSpinBox()
        self.sp_mark_px.setRange(1, 20)
        self.sp_mark_px.setSuffix(" px")
        try:
            self.sp_mark_px.setValue(int(mst.get('mark_px', MARK_DEFAULT_PX)))
        except Exception:
            self.sp_mark_px.setValue(MARK_DEFAULT_PX)
        self.sp_mark_px.setToolTip("How thick the marker line is on screen.")
        self.sp_mark_px.valueChanged.connect(lambda v: (_ui_settings_save(mark_px=int(v)),
                                                        self.viewport.update()))
        gml.addRow("Line thickness", self.sp_mark_px)
        try:
            rgb = tuple(int(c) for c in mst.get('mark_rgb', MARK_DEFAULT_RGB))[:3]
            assert len(rgb) == 3
        except Exception:
            rgb = MARK_DEFAULT_RGB
        self.mark_rgb = rgb
        self.b_mark_col = QPushButton()
        self.b_mark_col.setFixedWidth(60)
        self.b_mark_col.setToolTip("Click to pick the marker line's colour.")
        self.b_mark_col.clicked.connect(self.pick_mark_colour)
        self._show_mark_colour()
        gml.addRow("Line colour", self.b_mark_col)
        self.cb_selthick = QCheckBox("Show my selected lines thick too")
        self.cb_selthick.setChecked(bool(mst.get('sel_thick', True)))
        self.cb_selthick.setToolTip("Lines you've drawn and selected are drawn thick in the marker colour "
                                    "(dashed), so you can see what you've picked.")
        self.cb_selthick.toggled.connect(lambda on: (_ui_settings_save(sel_thick=bool(on)),
                                                     self.viewport.update()))
        gml.addRow(self.cb_selthick)
        self.cb_markhide = QCheckBox("Hide this window while marking (it comes back when you've finished)")
        self.cb_markhide.setChecked(bool(mst.get('mark_hide', True)))
        self.cb_markhide.setToolTip("So the window isn't in the way of the building while you click "
                                    "the runs. Press Esc twice when you've finished marking and it comes back.")
        self.cb_markhide.toggled.connect(lambda on: _ui_settings_save(mark_hide=bool(on)))
        gml.addRow(self.cb_markhide)
        self.cb_rgroup = QCheckBox("Put everything built along lines into one group")
        self.cb_rgroup.setChecked(bool(mst.get('route_group', True)))
        self.cb_rgroup.setToolTip("Ticked, the gutters, downpipes and all their fittings from one build go "
                                  "into a single group (each part stays its own group inside it). The group's name has "
                                  "'(one piece)' in it, so Scale Studio prints it as one piece.")
        self.cb_rgroup.toggled.connect(lambda on: _ui_settings_save(route_group=bool(on)))
        rf.addRow(self.cb_rgroup)
        self.lbl_marks = QLabel()
        self.lbl_marks.setStyleSheet("color: gray;")
        gml.addRow(self.lbl_marks)
        rf.addRow(gm)
        self._mark_label()
        self._hook_overlay()
        self.finished.connect(lambda *_: self._unhook_overlay())

        # ---- presets
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
        b_save, b_saveas = QPushButton("Save"), QPushButton("Save as...")
        b_del, b_open = QPushButton("Delete"), QPushButton("Folder")
        self.btn_preset_save = b_save
        for b in (b_save, b_saveas, b_del, b_open):
            prow.addWidget(b)
        lay.addLayout(prow)
        b_save.clicked.connect(self.save_preset)
        b_saveas.clicked.connect(lambda: self.save_preset_as())
        b_del.clicked.connect(self.delete_preset)
        b_open.clicked.connect(self.open_folder)

        # ---- buttons
        brow = QHBoxLayout()
        self.b_add = QPushButton("Add part")
        self.b_add.setDefault(True)
        b_sel = QPushButton("Use selected end")
        b_new = QPushButton("Start at the origin")
        b_close = QPushButton("Close")
        b_sel.setToolTip("Select the open end face of any placed part, then click this to join onto it.")
        b_new.setToolTip("The next part starts a new run at the origin.")
        b_lines = QPushButton("Build along lines")
        b_lines.setToolTip("Builds gutters and downpipes along your marked runs, or along lines you've "
                           "drawn and selected (settings on the Follow lines page).")
        b_lines.clicked.connect(lambda: self.tool.build_route(self))
        for b in (self.b_add, b_sel, b_new, b_lines):
            brow.addWidget(b)
        brow.addStretch(1)
        self.b_info = QPushButton("Info")
        self.b_info.setCheckable(True)
        self.b_info.setToolTip("Shows how to use it.")
        self.b_info.toggled.connect(self.toggle_info)
        brow.addWidget(self.b_info)
        self.cb_lasttab = QCheckBox("Open at the last page used")
        self.cb_lasttab.setToolTip("Ticked, the window opens at the page you had open last time.")
        st = _ui_settings()
        self.cb_lasttab.setChecked(bool(st.get('remember_tab', True)))
        if self.cb_lasttab.isChecked():
            try:
                self.tabs.setCurrentIndex(int(st.get('tab', 0)))
            except Exception:
                pass
        self.tabs.currentChanged.connect(lambda i: _ui_settings_save(tab=int(i)))
        self.cb_lasttab.toggled.connect(lambda on: _ui_settings_save(remember_tab=bool(on)))
        brow.addWidget(self.cb_lasttab)
        brow.addWidget(b_close)
        lay.addLayout(brow)
        self.b_add.clicked.connect(lambda: self.tool.add_from_dialog(self))
        b_sel.clicked.connect(self.use_selected_end)
        b_new.clicked.connect(self.start_at_origin)
        b_close.clicked.connect(self.close)
        self.set_target(target)

        self.refresh_presets(select=st.get('last_preset'))
        self.cb_preset.currentIndexChanged.connect(self.apply_preset)
        self.lst.currentItemChanged.connect(self.sync)
        self.cb_gprof.currentIndexChanged.connect(self.sync)
        self.sp_gw.valueChanged.connect(self.sync)
        self.cb_ptype.currentIndexChanged.connect(self.sync)
        self.cb_solid.toggled.connect(self.sync)
        for c_ in (self.cb_detail, self.cb_rstops, self.cb_rshoe, self.cb_rflip):
            c_.toggled.connect(self.sync)
        self.cb_rside.currentIndexChanged.connect(self.sync)
        self.sp_gmax.valueChanged.connect(self.sync)
        self.sp_pmax.valueChanged.connect(self.sync)
        self.cb_wall.currentIndexChanged.connect(self.sync)
        self.cb_dir.currentIndexChanged.connect(self.sync)
        for w in [self.sp_gd, self.sp_gt, self.sp_ps, self.sp_pt, self.sp_drop, self.sp_wgap, self.sp_ovl,
                  self.sp_ovr, self.sp_gsp, self.sp_psp] + list(self.sp.values()):
            w.valueChanged.connect(self.sync)
        for c in (self.cb_fit, self.cb_flip, self.cb_fix):
            c.toggled.connect(self.sync)
        # click a part in the model and the settings that made it light up
        self._sel_names = None
        self._lit = []
        try:
            from PySide6.QtCore import QTimer
            self._sel_timer = QTimer(self)
            self._sel_timer.timeout.connect(self.watch_selection)
            self._sel_timer.start(400)
        except Exception:
            pass
        self.sync()

    def toggle_info(self, on):
        self.info_box.setVisible(bool(on))
        try:
            self.adjustSize()
        except Exception:
            pass

    def watch_selection(self):
        try:
            if not self.isVisible():
                return
            scene = getattr(self.viewport, 'scene', None)
            sel = _items(getattr(scene, 'selection', None)) if scene is not None else []
            names = tuple(str(getattr(e, 'name', '') or '') for e in sel)
        except Exception:
            return
        if names == self._sel_names:
            return
        self._sel_names = names
        keys = []
        for nm in names:
            for word, ks in PIECE_KEYS:
                if nm.startswith(word) or (word == "angle" and " angle " in nm):
                    keys += [k for k in ks if k not in keys]
                    break
        for w, lab in self._lit:
            try:
                w.setStyleSheet("")
                lab.setStyleSheet("")
            except Exception:
                pass
        self._lit = []
        for k in keys:
            if k in self.keyw:
                w, lab = self.keyw[k]
                w.setStyleSheet("background-color: #fff3a0;")
                lab.setStyleSheet("background-color: #fff3a0; font-weight: bold;")
                self._lit.append((w, lab))
        if keys and keys[0] in self.page_of:
            try:
                self.tabs.setCurrentIndex(self.page_of[keys[0]])
            except Exception:
                pass

    # ---- preset order ----
    def preset_order(self):
        names = list(BUILTIN_PRESETS) + sorted(n for n in self.user_presets if n not in BUILTIN_PRESETS)
        order = [n for n in _ui_settings().get('preset_order', []) if n in names]
        return order + [n for n in names if n not in order]

    def move_preset(self, step):
        name = self.cb_preset.currentData()
        if not name:
            return
        order = self.preset_order()
        i = order.index(name)
        j = i + step
        if 0 <= j < len(order):
            order[i], order[j] = order[j], order[i]
            _ui_settings_save(preset_order=order)
            self.refresh_presets(select=name)

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
        self.lbl_ps.setText("D   Side" if self.cb_ptype.currentData() == 'square' else "D   Diameter")
        try:
            _ui_settings_save(last_values=self.values())       # opens like this next time
        except Exception:
            pass
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

    # -------------------------------------------------------------- mark the run
    def _hook_overlay(self):
        ov = getattr(self.viewport, '_ext_overlays', None)
        if ov is None:
            print("%s: this IngeTrazo can't draw the thick marker line (no overlays)." % PLUGIN_NAME)
            return
        if self.paint_marks not in ov:
            ov.append(self.paint_marks)

    def _unhook_overlay(self):
        try:
            self.stop_marking()
        except Exception:
            pass
        ov = getattr(self.viewport, '_ext_overlays', None)
        try:
            while ov is not None and self.paint_marks in ov:
                ov.remove(self.paint_marks)
            self.viewport.update()
        except Exception:
            pass

    def _show_mark_colour(self):
        r, g, b = self.mark_rgb
        self.b_mark_col.setStyleSheet("background-color: rgb(%d, %d, %d); border: 1px solid #444;"
                                      % (r, g, b))

    def pick_mark_colour(self):
        from PySide6.QtWidgets import QColorDialog
        from PySide6.QtGui import QColor
        c = QColorDialog.getColor(QColor(*self.mark_rgb), self, "Marker line colour")
        if c.isValid():
            self.mark_rgb = (c.red(), c.green(), c.blue())
            _ui_settings_save(mark_rgb=list(self.mark_rgb))
            self._show_mark_colour()
            self.viewport.update()

    def _mark_label(self):
        n = len(self.marks) + (1 if len(self.mark_run) >= 2 else 0)
        if self.marking:
            t = "Marking: %d point(s) in this run. " % len(self.mark_run)
            if self.mark_lock is not None:
                t += "Locked to %s. " % AXIS_NAMES[self.mark_lock]
        else:
            t = ""
        t += "%d run(s) marked." % n if n else "No runs marked yet."
        try:
            self.lbl_marks.setText(t)
        except Exception:
            pass

    def start_marking(self):
        vp = self.viewport
        try:
            if self.mark_tool is None:
                self.mark_tool = make_mark_tool(self)
            self.marking = True
            vp.set_active_tool(self.mark_tool)
            self._grab_keys(True)
            if self.cb_markhide.isChecked():
                self._hid_for_marking = True
                self.hide()
            self._keys_to_view()
            try:
                from PySide6.QtCore import QTimer
                QTimer.singleShot(150, self._keys_to_view)   # again, once Windows has caught up
            except Exception:
                pass
            try:
                vp.scene.selection.clear()      # so nothing else is lit up
            except Exception:
                pass
        except Exception as e:
            self.marking = False
            QMessageBox.warning(self, PLUGIN_NAME, "Couldn't start marking: %s" % e)
        self._sync_mark_button()
        self._mark_label()
        vp.update()

    def stop_marking(self):
        """Esc: stop clicking. A run with two or more points is kept."""
        was = self.marking
        self.marking = False
        try:
            self._grab_keys(False)
        except Exception:
            pass
        if len(self.mark_run) >= 2:
            self.marks.append(self.mark_run)
        self.mark_run = []
        self.mark_hover = None
        self.mark_lock = None
        if was:
            try:
                win = self.viewport.window()
                act = getattr(win, "_activate_tool", None)
                if callable(act):
                    act("select")
                else:
                    self.viewport.set_active_tool(None)
            except Exception:
                pass
        self._sync_mark_button()
        self._mark_label()
        self._come_back()
        try:
            self.viewport.update()
        except Exception:
            pass

    def _come_back(self):
        """Shows the window again if it was hidden for marking."""
        if self._hid_for_marking:
            self._hid_for_marking = False
            try:
                self.show()
                self.raise_()
                self.activateWindow()
            except Exception:
                pass

    def _sync_mark_button(self):
        try:
            self.b_mark.blockSignals(True)
            self.b_mark.setChecked(self.marking)
        finally:
            self.b_mark.blockSignals(False)

    def mark_tool_gone(self, tool):
        """Another tool was picked: stop marking (what's marked is kept)."""
        if tool is self.mark_tool and self.marking:
            self.marking = False
            try:
                self._grab_keys(False)
            except Exception:
                pass
            if len(self.mark_run) >= 2:
                self.marks.append(self.mark_run)
            self.mark_run = []
            self._sync_mark_button()
            self._mark_label()
            self._come_back()

    def mark_key(self, key):
        """A key while marking. True if it was one of ours."""
        from PySide6.QtCore import Qt
        if not self.marking:
            return False
        if key == Qt.Key_Escape:
            if self.mark_run:
                self.mark_finish_run()      # first Esc: end this line, carry on marking
            else:
                self.stop_marking()         # Esc again: finished marking
            return True
        if key in (Qt.Key_Return, Qt.Key_Enter):
            self.mark_finish_run()
            return True
        if key == Qt.Key_Backspace:
            self.mark_take_last()
            return True
        arrows = {Qt.Key_Right: 0, Qt.Key_Left: 1, Qt.Key_Up: 2, Qt.Key_Down: None}
        if key in arrows:
            self.mark_set_lock(arrows[key])
            return True
        return False

    def _grab_keys(self, on):
        """While marking, catch our keys before IngeTrazo does (it uses Esc and the arrows itself)."""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            return
        f = getattr(self, '_key_filter', None)
        if on:
            if f is None:
                from PySide6.QtCore import QObject, QEvent, Qt
                dlg = self
                ours = (Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Backspace,
                        Qt.Key_Right, Qt.Key_Left, Qt.Key_Up, Qt.Key_Down)

                class _Keys(QObject):
                    def eventFilter(self, obj, ev):
                        try:
                            t = ev.type()
                            # a quick right-click (not a drag - IngeTrazo may pan with it) on
                            # the view ends the line; the press and release still go through
                            if t == QEvent.Type.MouseButtonPress and dlg.marking:
                                if ev.button() == Qt.RightButton and dlg._on_view(obj):
                                    import time as _t
                                    p_ = ev.position() if hasattr(ev, 'position') else ev.pos()
                                    dlg._rpress = (p_.x(), p_.y(), _t.time())
                                return False
                            if t == QEvent.Type.MouseButtonRelease and dlg.marking:
                                rp = getattr(dlg, '_rpress', None)
                                if ev.button() == Qt.RightButton and rp is not None:
                                    import time as _t
                                    dlg._rpress = None
                                    p_ = ev.position() if hasattr(ev, 'position') else ev.pos()
                                    if abs(p_.x() - rp[0]) + abs(p_.y() - rp[1]) < 6 and _t.time() - rp[2] < 0.6:
                                        from PySide6.QtCore import QTimer
                                        QTimer.singleShot(0, dlg.mark_right_click)
                                return False
                            if t == QEvent.Type.ContextMenu and dlg.marking and dlg._on_view(obj):
                                return True           # no pop-up menu while marking
                            if t not in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress):
                                return False
                            if not dlg.marking or ev.key() not in ours:
                                return False
                            from PySide6.QtWidgets import QLineEdit, QAbstractSpinBox, QTextEdit
                            if isinstance(obj, (QLineEdit, QAbstractSpinBox, QTextEdit)):
                                return False          # typing in a box somewhere else
                            if t == QEvent.Type.ShortcutOverride:
                                ev.accept()           # don't let a menu shortcut have it
                                return True
                            if ev.isAutoRepeat():
                                return True
                            dlg.mark_key(ev.key())
                            return True
                        except Exception:
                            return False
                f = self._key_filter = _Keys(self)
            try:
                app.removeEventFilter(f)      # never in twice
            except Exception:
                pass
            app.installEventFilter(f)
        elif f is not None:
            app.removeEventFilter(f)

    def _on_view(self, obj):
        """Is obj the 3D view (or inside it)?"""
        vp = self.viewport
        w = obj
        for _ in range(6):
            if w is None:
                return False
            if w is vp:
                return True
            try:
                w = w.parent()
            except Exception:
                return False
        return False

    def mark_right_click(self):
        """Right-click: ends the line you're on; with no line on the go, finished marking."""
        if self.mark_run:
            self.mark_finish_run()
        else:
            self.stop_marking()

    def _keys_to_view(self):
        """Makes IngeTrazo's window the active one with the 3D view taking the keys, so Esc
        and the arrows reach it (with this window hidden, Windows can leave none active)."""
        vp = self.viewport
        try:
            win = vp.window()
            win.raise_()
            win.activateWindow()
        except Exception:
            pass
        try:
            vp.setFocus()
        except Exception:
            pass

    def mark_set_lock(self, axis):
        """Arrow keys: lock to an axis, or free again. The same arrow twice frees it."""
        self.mark_lock = None if (axis is None or axis == self.mark_lock) else axis
        if self.mark_hover is not None and self.mark_run:
            self.mark_hover = self.mark_constrain(self.mark_hover)
        self._mark_label()
        self.viewport.update()

    def mark_constrain(self, p):
        """The point slid onto the locked axis through the last point clicked."""
        if self.mark_lock is None or not self.mark_run:
            return p
        q = list(self.mark_run[-1])
        q[self.mark_lock] = p[self.mark_lock]
        return tuple(q)

    def mark_snap(self, p, end_px=14.0, on_px=9.0):
        """Snaps to the ends of marked lines (and the points clicked), or onto a marked line,
        when the mouse is near one on screen. IngeTrazo can't snap to these, as they're only drawn."""
        self.mark_snapped = None
        vp = self.viewport
        sp = _px(vp, QVector3D(*p))
        if sp is None:
            return p
        runs = [r for r in self.marks]
        cur = list(self.mark_run)
        best = None
        for pt in [q for r in runs for q in r] + cur[:-1]:
            s_ = _px(vp, QVector3D(*pt))
            if s_ is None:
                continue
            d = math.hypot(s_[0] - sp[0], s_[1] - sp[1])
            if d <= end_px and (best is None or d < best[0]):
                best = (d, tuple(pt))
        if best is not None:
            self.mark_snapped = (best[1], 'end')
            return best[1]
        for r in runs:
            for a, b in zip(r[:-1], r[1:]):
                sa, sb = _px(vp, QVector3D(*a)), _px(vp, QVector3D(*b))
                if sa is None or sb is None:
                    continue
                dx, dy = sb[0] - sa[0], sb[1] - sa[1]
                L2 = dx * dx + dy * dy
                if L2 < 1.0:
                    continue
                t = max(0.0, min(1.0, ((sp[0] - sa[0]) * dx + (sp[1] - sa[1]) * dy) / L2))
                d = math.hypot(sa[0] + dx * t - sp[0], sa[1] + dy * t - sp[1])
                if d <= on_px and (best is None or d < best[0]):
                    best = (d, tuple(a[k] + (b[k] - a[k]) * t for k in range(3)))
        if best is not None:
            self.mark_snapped = (best[1], 'on')
            return best[1]
        return p

    def mark_clicked(self, p):
        if self.mark_run and v_len(v_sub(p, self.mark_run[-1])) < 1e-6:
            return                      # the same point again (a double-click)
        self.mark_run.append(p)
        self.mark_lock = None           # each new line starts free again
        try:
            if not self.viewport.hasFocus():
                self._keys_to_view()
        except Exception:
            pass
        self._mark_label()
        self.viewport.update()

    def mark_finish_run(self):
        if len(self.mark_run) >= 2:
            self.marks.append(self.mark_run)
        self.mark_run = []
        self.mark_lock = None
        self._mark_label()
        self.viewport.update()

    def mark_take_last(self):
        if self.mark_run:
            self.mark_run.pop()
        elif self.marks:
            self.mark_run = self.marks.pop()   # back into the last run, to carry on or take more off
            self.mark_run.pop()
        self._mark_label()
        self.viewport.update()

    def clear_marks(self):
        self.marks, self.mark_run = [], []
        self._mark_label()
        self.viewport.update()

    def marked_chains(self):
        """The marked runs, each one on its own (so a downpipe started at the end of a gutter
        stays a downpipe, not part of the gutter). A run ending where it started is a loop."""
        out = []
        for run in self.marks + ([self.mark_run] if len(self.mark_run) >= 2 else []):
            P = [tuple(q) for q in run]
            closed = len(P) >= 4 and v_len(v_sub(P[0], P[-1])) < 1e-6
            if closed:
                P = P[:-1]
            if len(P) >= 2:
                out.append((P, closed))
        return out

    def paint_marks(self, vp, painter):
        """Draws the marked runs (and the selected lines) thick, over the model."""
        if vp is not self.viewport:
            return
        try:
            from PySide6.QtGui import QPen, QColor, QPainter
            from PySide6.QtCore import QPointF, Qt
            w = float(self.sp_mark_px.value())
            col = QColor(*self.mark_rgb)
            dark = QColor(20, 20, 20, 200)
            runs = list(self.marks)
            if self.mark_run:
                runs.append(self.mark_run)
            segs = []
            for run in runs:
                segs += [(run[i], run[i + 1]) for i in range(len(run) - 1)]
            live = []
            if self.marking and self.mark_run and self.mark_hover is not None:
                live = [(self.mark_run[-1], self.mark_hover)]
            sel = []
            if self.cb_selthick.isChecked():
                scene = getattr(vp, 'scene', None)
                items = list(getattr(scene, 'selection', None) or [])
                if items and len(items) < 5000:
                    m0 = _r_ctx_world(scene)
                    for e in items:
                        if _r_is_group(e) or _r_is_face(e):
                            continue
                        ends = _r_edge_ends(e)
                        if ends:
                            sel.append((_r_m_apply(m0, ends[0]), _r_m_apply(m0, ends[1])))
            if not (segs or live or sel or self.marking):
                return
            painter.save()
            if self.marking:
                from PySide6.QtGui import QFont
                from PySide6.QtCore import QRectF
                if self.mark_run:
                    head = "MARKING - line on the go (%d point%s)" % (len(self.mark_run),
                                                                    "" if len(self.mark_run) == 1 else "s")
                else:
                    head = "MARKING - click to start a line"
                if self.mark_lock is not None:
                    head += "   [locked to %s]" % AXIS_NAMES[self.mark_lock]
                lines = [head,
                         "Esc or right-click: end this line   (again: finished marking)",
                         "Arrows: Right red, Left green, Up blue, Down free   Backspace: undo point"]
                fnt = QFont()
                fnt.setPointSizeF(9.5)
                painter.setFont(fnt)
                fm = painter.fontMetrics()
                bw = max(fm.horizontalAdvance(t) for t in lines) + 16
                bh = fm.height() * len(lines) + 12
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(20, 20, 20, 190))
                painter.drawRoundedRect(QRectF(10, 10, bw, bh), 6, 6)
                for i, t in enumerate(lines):
                    painter.setPen(QColor(*self.mark_rgb) if i == 0 else QColor(235, 235, 235))
                    painter.drawText(QPointF(18, 10 + 6 + fm.ascent() + i * fm.height()), t)
                painter.setBrush(Qt.NoBrush)
            painter.setRenderHint(QPainter.Antialiasing, True)

            def draw(screen, width, colour, style=Qt.SolidLine):
                pen = QPen(colour, width, style, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)
                for (x0, y0), (x1, y1) in screen:
                    painter.drawLine(QPointF(x0, y0), QPointF(x1, y1))

            s_sel = _mark_segments_px(vp, sel)
            s_runs = _mark_segments_px(vp, segs)
            s_live = _mark_segments_px(vp, live)
            if s_sel:
                draw(s_sel, w + 3, dark)
                draw(s_sel, w, col, Qt.DashLine)
            if s_runs:
                draw(s_runs, w + 3, dark)
                draw(s_runs, w, col)
            if s_live:
                draw(s_live, w + 3, dark)
                if self.mark_lock is not None:
                    draw(s_live, w, QColor(*AXIS_RGB[self.mark_lock]))
                else:
                    draw(s_live, w, col.lighter(130), Qt.DashLine)
            # where it's snapped to one of the marks: a ring (green = an end, blue = on the line)
            if self.marking and self.mark_snapped is not None:
                q = _px(vp, QVector3D(*self.mark_snapped[0]))
                if q is not None:
                    ring = QColor(30, 200, 60) if self.mark_snapped[1] == 'end' else QColor(30, 140, 255)
                    painter.setBrush(Qt.NoBrush)
                    painter.setPen(QPen(dark, 5.0))
                    painter.drawEllipse(QPointF(q[0], q[1]), w + 7, w + 7)
                    painter.setPen(QPen(ring, 3.0))
                    painter.drawEllipse(QPointF(q[0], q[1]), w + 7, w + 7)
            # a dot on each clicked point
            painter.setPen(QPen(dark, 1.5))
            painter.setBrush(col)
            r = max(3.0, w * 0.9)
            for run in runs:
                for p in run:
                    q = _px(vp, QVector3D(*p))
                    if q is not None:
                        painter.drawEllipse(QPointF(q[0], q[1]), r, r)
            painter.restore()
        except Exception as e:
            try:
                painter.restore()
            except Exception:
                pass
            print("%s: drawing the marker line: %s" % (PLUGIN_NAME, e))

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
             'p_wall': self.sp_pt.value(), 'bend_dir': self.cb_dir.currentData(),
             'g_detail': self.cb_detail.isChecked(), 'g_maxlen': self.sp_gmax.value(),
             'p_maxlen': self.sp_pmax.value(), 'r_stops': self.cb_rstops.isChecked(),
             'r_shoe': self.cb_rshoe.isChecked(), 'r_side': self.cb_rside.currentData(),
             'r_flip': self.cb_rflip.isChecked(), 'r_swan': self.cb_rswan.isChecked(),
             'r_avoid': self.cb_ravoid.isChecked()}
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
        for c, key in ((self.cb_fit, 'fit_wall'), (self.cb_fix, 'auto_fix'), (self.cb_detail, 'g_detail'),
                       (self.cb_rstops, 'r_stops'), (self.cb_rshoe, 'r_shoe'), (self.cb_rswan, 'r_swan'),
                       (self.cb_ravoid, 'r_avoid')):
            if key in d:
                c.setChecked(bool(d[key]))
        for w, key in ((self.sp_drop, 'drop'), (self.sp_wgap, 'wall_gap'), (self.sp_ovl, 'over_left'),
                       (self.sp_ovr, 'over_right'), (self.sp_gsp, 'g_spacing'),
                       (self.sp_psp, 'p_spacing'), (self.sp_chunk, 'chunk_mult'),
                       (self.sp_gmax, 'g_maxlen'), (self.sp_pmax, 'p_maxlen')):
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
        for name in self.preset_order():
            self.cb_preset.addItem(name + ("  (built-in)" if name in BUILTIN_PRESETS else ""), name)
        for i in range(self.cb_preset.count()):
            if select and self.cb_preset.itemData(i) == select:
                self.cb_preset.setCurrentIndex(i)
        self.cb_preset.blockSignals(False)

    def apply_preset(self, *_):
        name = self.cb_preset.currentData()
        _ui_settings_save(last_preset=name or None)      # opens on this one next time
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
        _ui_settings_save(last_preset=name)
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
        last = _ui_settings().get('last_values')
        if isinstance(last, dict):
            cur.update({k: last[k] for k in DEFAULTS if k in last and k != 'units'})
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
        if not _ui_settings().get('compact_v6'):
            # the window remembers its old (bigger) size: shrink it once to the new smaller size
            try:
                dlg.adjustSize()
            except Exception:
                pass
            _ui_settings_save(compact_v6=True)
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

    def build_route(self, dlg):
        """Builds gutters and downpipes along the lines you've selected."""
        viewport = dlg.viewport
        vals = dlg.values()
        GuttersDownpipesTool._saved = dict(vals)
        scene = getattr(viewport, 'scene', None)
        sel = list(getattr(scene, 'selection', None) or [])
        marked = False
        chains = []
        try:
            if dlg.marking:
                dlg.stop_marking()
            chains = dlg.marked_chains()
            marked = bool(chains)
        except Exception as e:
            print("%s: reading the marked runs: %s" % (PLUGIN_NAME, e))
        if marked:
            sel = []                   # find the walls from the model, under the marked runs
        else:
            try:
                chains = route_lines(scene, sel)
            except Exception as e:
                chains = []
                print("%s: reading the lines: %s" % (PLUGIN_NAME, e))
        if not chains:
            QMessageBox.information(dlg, PLUGIN_NAME, "Mark the runs first (Follow lines page, 'Mark the run'), "
                                    "or select the lines you've drawn (Ctrl-click each "
                                    "one, or select a group with the lines in it), then click this again.\n\n"
                                    "Draw a level line along the top outside edge of the wall for each gutter, "
                                    "and a line down the wall for each downpipe, starting on the gutter line.")
            return
        ROUTE_STATS['limit'] = False
        box = _r_box(chains, pad=2.5)
        all_faces = []
        try:
            if vals.get('r_avoid', True) or not any(_r_is_face(e) for e in sel):
                all_faces = route_faces(scene, [], near=box, upright_only=False)
            if any(_r_is_face(e) for e in sel):
                faces = route_faces(scene, sel, near=box)
            else:
                faces = [f for f in all_faces if abs(f[0][2]) <= 0.35]
        except Exception as e:
            faces = []
            print("%s: finding the walls: %s" % (PLUGIN_NAME, e))
        try:
            parts, what, notes = build_routes(chains, faces, vals, all_faces)
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.warning(dlg, PLUGIN_NAME, "Could not build along the lines:\n%s" % e)
            return
        if not parts:
            QMessageBox.information(dlg, PLUGIN_NAME, "Nothing could be built along those lines.\n\n" +
                                    "\n".join(notes))
            return
        holder = None
        try:
            if dlg.cb_rgroup.isChecked() and len(parts) > 1:
                # "one piece" in the name: Scale Studio puts the lot on the print bed as one piece
                holder = "Gutters & downpipes (one piece) - %s" % (what or "%d parts" % len(parts))
        except Exception:
            pass
        if not self.add_to_scene(viewport, vals, None, parts, holder=holder):
            return
        if marked:
            dlg.clear_marks()          # built now - the marks have done their job
        dlg.set_target(None)
        txt = "Built %s along your %s." % (what or "the parts", "marked runs" if marked else "lines")
        if notes:
            txt += " Note: " + "; ".join(notes) + "."
        dlg.lbl_target.setText(txt)

    def add_to_scene(self, viewport, vals, target, parts, holder=None):
        """parts: list of (group name, world solids, port tags). One undo step for all.
        holder: a name to put all the parts into one group of that name (each part stays a group)."""
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
            made = []
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
                made.append(g)
            top = made
            if holder and len(made) > 1:
                h = None
                try:
                    try:
                        h = Group(name=holder)
                    except TypeError:
                        h = Group(holder)
                    try:
                        h.name = holder
                    except Exception:
                        pass
                    if hasattr(h, 'adopt'):
                        h.adopt(made)
                    else:
                        h.children = made
                    try:
                        h.component = False
                    except Exception:
                        pass
                except Exception as e:
                    print("%s: could not make the one group, so the parts go in loose: %s" % (PLUGIN_NAME, e))
                    h = None
                if h is not None:
                    top = [h]
            for g in top:
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
