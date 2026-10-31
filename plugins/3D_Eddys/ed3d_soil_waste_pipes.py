# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Soil & Waste Pipes for IngeTrazo
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
3D Soil & Waste Pipes - full-size soil stacks and outside sink waste pipes for IngeTrazo
Soil pipe (110 / 82 mm) and waste pipe (32 / 40 / 50 mm) with bends, branches, tees,
access pipes, boss connectors, vents, drain connectors, gullies, sockets and clips.
Pick a part, set its sizes, and it is built in its own group. Select the open end of a
part you placed and the next part joins onto it. Presets are saved as .json files.
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

PLUGIN_NAME = "3D Soil & Waste Pipes"
PORT_KEY = "soilwaste_port"      # face attribute that marks a connectable open end

PRESET_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets",
                          "Soil and Waste")

# 0 = bend down (horizontal pipes) / towards the wall (upright pipes)
BEND_DIRS = [("Down / towards the wall", 0.0), ("Up / away from the wall", 180.0),
             ("Left", 90.0), ("Right", -90.0)]

# key, label, system, settings it uses
PARTS = [
    ("s_pipe",   "Soil pipe length",                 "soil",  ("length",)),
    ("s_bend",   "Bend",                             "soil",  ("bend_turn", "bend_dir")),
    ("s_swan",   "Swan neck / offset",               "soil",  ("bend_turn", "bend_dir", "swan_len")),
    ("s_rest",   "Rest bend (base of stack)",        "soil",  ("bend_dir",)),
    ("s_branch", "Branch",                           "soil",  ("bend_turn", "bend_dir", "branch_len")),
    ("s_cross",  "Double branch",                    "soil",  ("bend_turn", "bend_dir", "branch_len")),
    ("s_access", "Access pipe (rodding door)",       "soil",  ("bend_dir",)),
    ("s_bosspipe", "Boss pipe (2 waste outlets)",    "soil",  ("bend_dir",)),
    ("s_boss",   "Boss connector (for a waste pipe)", "soil", ("bend_dir", "offset")),
    ("s_socket", "Socket / coupler",                 "soil",  ("offset",)),
    ("s_clip",   "Pipe clip",                        "soil",  ("bend_dir", "offset")),
    ("s_vent",   "Vent cowl (top of stack)",         "soil",  ()),
    ("s_drain",  "Drain adaptor (into the ground)",   "soil", ()),
    ("w_pipe",   "Waste pipe length",                "waste", ("length",)),
    ("w_bend",   "Bend",                             "waste", ("bend_turn", "bend_dir")),
    ("w_swan",   "Swan neck / offset",               "waste", ("bend_turn", "bend_dir", "swan_len")),
    ("w_tee",    "Tee (90 deg)",                     "waste", ("bend_dir", "branch_len")),
    ("w_branch", "Branch (angled)",                  "waste", ("bend_turn", "bend_dir", "branch_len")),
    ("w_socket", "Socket / coupler",                 "waste", ("offset",)),
    ("w_clip",   "Pipe clip",                        "waste", ("bend_dir", "offset")),
    ("w_adaptor", "Boss adaptor (rubber seal)",      "waste", ("offset",)),
    ("w_hopper", "Hopper head (old style)",          "waste", ()),
    ("w_shoe",   "Shoe (into a gully)",              "waste", ("bend_dir",)),
    ("w_gully",  "Gully with grid (end of the run)", "waste", ()),
    ("w_bigully", "Back-inlet gully (end of the run)", "waste", ()),
]
PART_INFO = {k: (label, system, uses) for k, label, system, uses in PARTS}
SYSTEM_NAMES = {'soil': "soil pipe", 'waste': "waste pipe"}

# Sizes are in millimetres (full size)
DEFAULTS = {
    'part': 's_pipe', 'units': 'm',      # IngeTrazo stores geometry in metres
    's_size': 110.0, 's_wall': 3.2, 'w_size': 40.0, 'w_wall': 1.9,
    'length': 1000.0, 'bend_turn': 87.5, 'bend_dir': 0.0, 'branch_len': 150.0, 'offset': 0.0,
    'solid': False, 'wall_side': 0.0,
    'along': 500.0, 'drop': 0.0, 'below': 0.0, 'w_height': 750.0, 'wall_gap': 0.0,
    'fit_wall': True, 'wall_flip': False,
    'auto_fix': True, 's_spacing': 1800.0, 'w_spacing': 500.0,
    'chunky': False, 'chunk_mult': 3.0, 'detail': True, 'pipe_socket': True,
    'ears': False, 'swan_len': 150.0,
}
WALL_SIDES = [("Behind the part (+Y)", 0.0), ("On the left (-X)", 90.0),
              ("In front (-Y)", 180.0), ("On the right (+X)", 270.0)]
PRESET_KEYS = ('s_size', 's_wall', 'w_size', 'w_wall', 'length', 'bend_turn', 'branch_len',
               'solid', 'along', 'drop', 'below', 'w_height', 'wall_gap',
               's_spacing', 'w_spacing', 'chunky', 'chunk_mult', 'detail', 'pipe_socket',
               'ears', 'swan_len')
SYSTEM_KEYS = {'soil': ('s_size', 's_wall', 'solid'), 'waste': ('w_size', 'w_wall', 'solid')}
OVERLAY = ('socket', 'clip', 'boss', 'adaptor')          # sit over a joint or along a pipe
CLOSERS = ('vent', 'drain', 'gully', 'shoe', 'bigully')          # finish a run
END_NAMES = {'out': "far end", 'in': "start", 'branch': "branch end", 'boss': "boss outlet",
             'boss2': "second boss outlet", 'branch2': "second branch end"}

BUILTIN_PRESETS = {
    "UK 110 soil + 40 waste": {'s_size': 110.0, 's_wall': 3.2, 'w_size': 40.0, 'w_wall': 1.9},
    "UK 110 soil + 32 waste": {'s_size': 110.0, 's_wall': 3.2, 'w_size': 32.0, 'w_wall': 1.8},
    "UK 82 soil + 50 waste": {'s_size': 82.0, 's_wall': 3.2, 'w_size': 50.0, 'w_wall': 2.0},
    "UK 110 soil + 50 waste": {'s_size': 110.0, 's_wall': 3.2, 'w_size': 50.0, 'w_wall': 2.0},
}

SOCKET_LEN = 40.0        # straight ends on bends
CLIP_LEN = 25.0
BRACKET_LEN = 25.0
SOCKET_COUPLER_LEN = 70.0
BOSS_LEN = 80.0
ACCESS_LEN = 300.0

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



def revolve_solid(stations, n=32, start_tag=None, end_tag=None):
    """Solid of revolution about local x: stations = [(x, radius), ...]. Ends are capped."""
    sol = Solid()
    circ = [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i in range(n)]
    rings = [[(x, c * r, d * r) for c, d in circ] for x, r in stations]
    for k in range(len(rings) - 1):
        r0, r1 = rings[k], rings[k + 1]
        if stations[k] == stations[k + 1]:
            continue
        for i in range(n):
            j = (i + 1) % n
            sol.add([r0[i], r0[j], r1[j], r1[i]])
    sol.add(list(reversed(rings[0])), start_tag)
    sol.add(list(rings[-1]), end_tag)
    sol.fix_winding()
    return sol


def rect_sweep(x0, x1, d, e, r0, r1, half):
    """A block running from x0 to x1 that sticks out of the pipe in direction d
    (from radius r0 to r1) and is 2*half wide across direction e."""
    loop = [(d[0] * r0 + e[0] * half, d[1] * r0 + e[1] * half),
            (d[0] * r1 + e[0] * half, d[1] * r1 + e[1] * half),
            (d[0] * r1 - e[0] * half, d[1] * r1 - e[1] * half),
            (d[0] * r0 - e[0] * half, d[1] * r0 - e[1] * half)]
    so, _ = sweep_solid([(x0, 0, 0), (x1, 0, 0)], Z, loop)
    return so


def block(x0, x1, corners):
    """A block running along x from x0 to x1 with a 4-corner (a=y, b=z) section."""
    so, _ = sweep_solid([(x0, 0, 0), (x1, 0, 0)], Z, list(corners))
    return so


def _perp_pair(axis):
    a = v_norm(axis)
    p = (1.0, 0.0, 0.0) if abs(a[0]) < 0.9 else (0.0, 1.0, 0.0)
    e1 = v_norm(v_cross(a, p))
    return e1, v_cross(a, e1)


def revolve_profile(c, axis, poly, n=32):
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


def socket_dims(D):
    """Sizes of a socket collar for a pipe of outside diameter D (mm)."""
    ts = max(2.5, D * 0.08)           # collar thickness
    Ls = max(20.0, D * 0.6)           # collar length
    return ts, Ls, Ls


_COLLARS = []        # mouths of the socket collars on the part being built


def collar(c, into, D):
    """A thick, square-ended socket collar whose mouth is at c, running into the
    fitting along `into`."""
    ts, Ls, _ = socket_dims(D)
    R0 = D / 2.0
    _COLLARS.append(tuple(c))
    return revolve_profile(c, into, [(0.0, R0), (0.0, R0 + ts), (Ls, R0 + ts), (Ls, R0)])


def detailed(s):
    return s.get('detail', True)


# ---------------------------------------------------------------------------
# Parts. Built in local millimetres: x = along the run, y = left, z = the pipe's
# reference side (towards the wall on upright pipes, down on horizontal waste).
# ---------------------------------------------------------------------------
X, Y, Z = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
NX, NZ = (-1.0, 0.0, 0.0), (0.0, 0.0, -1.0)


def fix_mult(s):
    """How much thicker clips and fittings are made ('Chunky fittings' for 3D printing)."""
    return max(1.0, s.get('chunk_mult', 3.0)) if s.get('chunky') else 1.0


def fit_gap(s, normal=0.5):
    return 0.0 if s.get('chunky') else normal


def port(c, n, u, role, system):
    return {'c': c, 'n': n, 'u': u, 'role': role, 'sys': system}


def roll_dirs(deg):
    """Direction d at this roll angle round the pipe (in the a=y, b=z section plane)
    and the direction e square to it."""
    r = math.radians(deg)
    return (math.sin(r), math.cos(r)), (math.cos(r), -math.sin(r))


def view(s, system):
    """The settings with this system's pipe size, as the shared pipe code reads them."""
    d = dict(s)
    d['p_type'] = 'round'
    d['p_size'] = s['s_size'] if system == 'soil' else s['w_size']
    d['p_wall'] = s['s_wall'] if system == 'soil' else s['w_wall']
    return d


def build_part(key, s):
    """Builds a part and marks which of its ends already have a socket collar, so a
    pipe joined onto that end doesn't get a second socket of its own."""
    del _COLLARS[:]
    sol, ports = _build_part(key, s)
    for pd in ports.values():
        pd['sock'] = any(v_len(v_sub(tuple(pd['c']), cc)) < 1e-6 for cc in _COLLARS)
    del _COLLARS[:]
    return sol, ports


def _build_part(key, s):
    system = PART_INFO[key][1]
    kind = key[2:]
    v = view(s, system)
    size = v['p_size']
    sol, ports = [], {}
    o, i = pipe_rings(v)
    m = fix_mult(s)

    if kind == 'pipe':
        L = s['length']
        so, _ = sweep_solid([(0, 0, 0), (L, 0, 0)], Z, o, i, 'in', 'out')
        sol.append(so)
        if detailed(s) and s.get('pipe_socket', True) and L > socket_dims(size)[1] * 1.5:
            sol.append(collar((0, 0, 0), X, size))       # socket on the start (top) end
            if s.get('ears'):
                # cast-iron style ears: two lugs on the socket, backs flush towards the wall
                ts, Ls, _ = socket_dims(size)
                d, e = roll_dirs(s.get('ear_roll', 0.0))
                R0 = size / 2 + ts
                th = 8.0 * m
                for sg in (1.0, -1.0):
                    ee = (e[0] * sg, e[1] * sg)
                    pts = [(ee[0] * a + d[0] * b, ee[1] * a + d[1] * b) for a, b in
                           ((size * 0.25, R0 - th), (R0 + 30.0, R0 - th), (R0 + 30.0, R0),
                            (size * 0.25, R0))]
                    sol.append(block(5.0, Ls - 5.0, pts))
        ports['in'] = port((0, 0, 0), NX, Z, 'in', system)
        ports['out'] = port((L, 0, 0), X, Z, 'out', system)

    elif kind == 'cross':
        # a double branch: two arms on opposite sides at the same height
        Lm = max(250.0 if system == 'soil' else 120.0, size * 3.5)
        so, _ = sweep_solid([(0, 0, 0), (Lm, 0, 0)], Z, o, i, 'in', 'out')
        sol.append(so)
        turn = math.radians(s['bend_turn'])
        dd, _ = roll_dirs(s['bend_dir'])
        start = (Lm * 0.6, 0, 0)
        if detailed(s):
            sol.append(collar((0, 0, 0), X, size))
            sol.append(collar((Lm, 0, 0), NX, size))
        for name, sgn in (('branch', 1.0), ('branch2', -1.0)):
            d = (0.0, sgn * dd[0], sgn * dd[1])
            dirb = v_add(v_mul(NX, math.cos(turn)), v_mul(d, math.sin(turn)))
            end = v_add(start, v_mul(dirb, s['branch_len'] + size / 2))
            r = rot_between(X, dirb)
            upb = rotate(Z, r[0], r[1]) if r else Z
            sb, (T, ups, _) = sweep_solid([start, end], upb, o, i, None, name)
            sol.append(sb)
            if detailed(s):
                sol.append(collar(end, v_mul(dirb, -1.0), size))
            ports[name] = port(end, T[-1], ups[-1], 'out', system)
        ports['in'] = port((0, 0, 0), NX, Z, 'in', system)
        ports['out'] = port((Lm, 0, 0), X, Z, 'out', system)

    elif kind == 'bend':
        turn = math.radians(s['bend_turn'])
        dd, _ = roll_dirs(s['bend_dir'])
        d = (0.0, dd[0], dd[1])
        R = size * 0.8
        segs = max(4, int(math.degrees(turn) / 7.5))
        lead = max(SOCKET_LEN, socket_dims(size)[2] + 5.0) if detailed(s) else SOCKET_LEN
        arc = arc_path((lead, 0, 0), X, d, R, turn, segs)
        Tend = v_add(v_mul(X, math.cos(turn)), v_mul(d, math.sin(turn)))
        path = [(0, 0, 0)] + arc + [v_add(arc[-1], v_mul(Tend, lead))]
        so, (T, ups, _) = sweep_solid(path, Z, o, i, 'in', 'out')
        sol.append(so)
        if detailed(s):
            sol.append(collar((0, 0, 0), X, size))
            sol.append(collar(path[-1], v_mul(T[-1], -1.0), size))
        ports['in'] = port((0, 0, 0), NX, Z, 'in', system)
        ports['out'] = port(path[-1], T[-1], ups[-1], 'out', system)

    elif kind in ('branch', 'tee'):
        Lm = max(250.0 if system == 'soil' else 120.0, size * 3.5)
        so, _ = sweep_solid([(0, 0, 0), (Lm, 0, 0)], Z, o, i, 'in', 'out')
        sol.append(so)
        turn = math.radians(90.0 if kind == 'tee' else s['bend_turn'])
        dd, _ = roll_dirs(s['bend_dir'])
        d = (0.0, dd[0], dd[1])
        # the arm angles back up against the flow, like a real branch
        dirb = v_add(v_mul(NX, math.cos(turn)), v_mul(d, math.sin(turn)))
        start = (Lm * (0.5 if kind == 'tee' else 0.6), 0, 0)
        end = v_add(start, v_mul(dirb, s['branch_len'] + size / 2))
        r = rot_between(X, dirb)
        upb = rotate(Z, r[0], r[1]) if r else Z
        sb, (T, ups, _) = sweep_solid([start, end], upb, o, i, None, 'branch')
        sol.append(sb)
        if detailed(s):
            sol.append(collar((0, 0, 0), X, size))
            sol.append(collar((Lm, 0, 0), NX, size))
            sol.append(collar(end, v_mul(dirb, -1.0), size))
        ports['in'] = port((0, 0, 0), NX, Z, 'in', system)
        ports['out'] = port((Lm, 0, 0), X, Z, 'out', system)
        ports['branch'] = port(end, T[-1], ups[-1], 'out', system)

    elif kind == 'access':
        L = ACCESS_LEN
        so, _ = sweep_solid([(0, 0, 0), (L, 0, 0)], Z, o, i, 'in', 'out')
        sol.append(so)
        d, e = roll_dirs(s['bend_dir'])
        r = size / 2
        if detailed(s):
            sol.append(collar((0, 0, 0), X, size))
            sol.append(collar((L, 0, 0), NX, size))
            # a round rodding eye with a screw cap and four bolt bosses
            dd = (0.0, d[0], d[1])
            ee = (0.0, e[0], e[1])
            cx = (L / 2, 0, 0)
            dr = size * 0.32
            sol.append(revolve_profile(cx, dd, [(r * 0.5, dr), (r + 6 * m, dr),
                                                (r + 6 * m, dr + 4), (r + 12 * m, dr + 4),
                                                (r + 12 * m, dr * 0.5), (r * 0.5, dr * 0.5)]))
            top = r + 12 * m                     # face of the screw cap
            for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                bc = v_add(v_add(cx, v_mul(X, sx * dr * 0.55)), v_mul(ee, sy * dr * 0.55))
                sol.append(revolve_profile(bc, dd, [(top - 1.0, 4.0), (top + 3.0 * m, 4.0),
                                                    (top + 3.0 * m, 1.5), (top - 1.0, 1.5)], n=12))
        else:
            sol.append(rect_sweep(L * 0.3, L * 0.7, d, e, r * 0.6, r + 8 * m, r * 0.55))
        ports['in'] = port((0, 0, 0), NX, Z, 'in', system)
        ports['out'] = port((L, 0, 0), X, Z, 'out', system)

    elif kind == 'bosspipe':
        # a soil pipe section with socketed waste bosses on two opposite sides
        L = max(ACCESS_LEN, size * 3.0)
        so, _ = sweep_solid([(0, 0, 0), (L, 0, 0)], Z, o, i, 'in', 'out')
        sol.append(so)
        r = size / 2
        wv = view(s, 'waste')
        wo, wi = pipe_rings(wv)
        Dw = wv['p_size']
        d, _ = roll_dirs(s['bend_dir'])
        sides = (('boss', (0.0, d[0], d[1])), ('boss2', (0.0, -d[0], -d[1])))
        xc = L * 0.45
        for name, dd in sides:
            a = v_add((xc, 0, 0), v_mul(dd, r * 0.5))
            b = v_add((xc, 0, 0), v_mul(dd, r + Dw * 0.9 + 10.0))
            sb, _ = sweep_solid([a, b], X, wo, wi, None, name)
            sol.append(sb)
            if detailed(s):
                sol.append(collar(b, v_mul(dd, -1.0), Dw))
            ports[name] = port(b, dd, X, 'out', 'waste')
        if detailed(s):
            sol.append(collar((0, 0, 0), X, size))
            ts = socket_dims(size)[0]
            sol.append(revolve_profile((L - 25.0, 0, 0), X, [(0.0, r), (0.0, r + ts), (10.0, r + ts),
                                                             (10.0, r)]))
        ports['in'] = port((0, 0, 0), NX, Z, 'in', system)
        ports['out'] = port((L, 0, 0), X, Z, 'out', system)

    elif kind in ('socket', 'clip', 'boss'):
        L = {'socket': SOCKET_COUPLER_LEN, 'clip': CLIP_LEN * (1 + (m - 1) / 2), 'boss': BOSS_LEN}[kind]
        g = fit_gap(s, 0.3 if kind == 'clip' else 0.5)
        t = {'socket': v['p_wall'] * 1.5 * m, 'clip': 3.0 * m, 'boss': v['p_wall'] * 1.5 * m}[kind]
        if kind == 'socket' and detailed(s):
            L = 2 * socket_dims(size)[2]
        x0, x1 = -L / 2 - s['offset'], L / 2 - s['offset']
        if kind == 'socket' and detailed(s):
            # a coupler: two thick collars back to back
            c1 = collar((x1, 0, 0), NX, size)
            c0 = collar((x0, 0, 0), X, size)
            c1.faces = [(f, 'copy' if all(abs(p[0] - x1) < 1e-6 for p in f) else t_)
                        for f, t_ in c1.faces]
            sol += [c0, c1]
        else:
            so_, si_ = pipe_rings(v, grow=g, thick=t)
            so, _ = sweep_solid([(x0, 0, 0), (x1, 0, 0)], Z, so_, si_, None, 'copy')
            sol.append(so)
        r_out = size / 2 + g + t
        d, e = roll_dirs(s['bend_dir'])
        if kind == 'clip':
            hw = 8 * m
            sol.append(rect_sweep(x0, x1, d, e, r_out - 1, r_out + 35, hw))
            sol.append(rect_sweep(x0 - 10, x1 + 10, d, e, r_out + 35, r_out + 35 + 4 * m, 25 + hw))
            if detailed(s):
                # hinged clip: a hinge knuckle on one side, bolt ears on the other
                ee = (0.0, e[0], e[1])
                rk = 3.0 * m
                kc = v_mul(ee, r_out + rk * 0.6)
                sol.append(revolve_profile(kc, X, [(x0, 0.6), (x0, rk), (x1, rk), (x1, 0.6)], n=12))
                me = (-e[0], -e[1])
                sol.append(rect_sweep(x0, x1, me, (d[0], d[1]), r_out - 1, r_out + 9 * m, 3.0 * m))
        if kind == 'boss':
            # a waste-size spigot out of the side of the soil pipe
            wv = view(s, 'waste')
            wo, wi = pipe_rings(wv)
            xc = (x0 + x1) / 2
            dd = (0.0, d[0], d[1])
            a = v_add((xc, 0, 0), v_mul(dd, size * 0.25))
            b = v_add((xc, 0, 0), v_mul(dd, r_out + 45.0))
            sb, _ = sweep_solid([a, b], X, wo, wi, None, 'boss')
            sol.append(sb)
            if detailed(s):
                sol.append(collar(b, v_mul(dd, -1.0), wv['p_size']))
            # the waste pipe hangs from it with its reference side along the stack
            ports['boss'] = port(b, dd, X, 'out', 'waste')
        ports['in'] = port((0, 0, 0), NX, Z, 'in', system)

    elif kind == 'swan':
        # a swan neck: two bends with a straight between, stepping the pipe sideways
        turn = math.radians(s['bend_turn'])
        dd, _ = roll_dirs(s['bend_dir'])
        d = (0.0, dd[0], dd[1])
        R = size * 0.8
        segs = max(4, int(math.degrees(turn) / 7.5))
        lead = max(SOCKET_LEN, socket_dims(size)[2] + 5.0) if detailed(s) else SOCKET_LEN
        arc1 = arc_path((lead, 0, 0), X, d, R, turn, segs)
        T1 = v_add(v_mul(X, math.cos(turn)), v_mul(d, math.sin(turn)))
        mid = v_add(arc1[-1], v_mul(T1, s['swan_len']))
        back = v_sub(v_mul(X, math.sin(turn)), v_mul(d, math.cos(turn)))
        arc2 = arc_path(mid, T1, back, R, turn, segs)
        path = [(0, 0, 0)] + arc1 + arc2 + [v_add(arc2[-1], v_mul(X, lead))]
        so, (T, ups, _) = sweep_solid(path, Z, o, i, 'in', 'out')
        sol.append(so)
        if detailed(s):
            sol.append(collar((0, 0, 0), X, size))
            sol.append(collar(path[-1], NX, size))
        ports['in'] = port((0, 0, 0), NX, Z, 'in', system)
        ports['out'] = port(path[-1], T[-1], ups[-1], 'out', system)

    elif kind == 'rest':
        # a rest bend: long-radius bend at the foot of a stack, with a foot under its heel
        turn = math.radians(87.5)
        dd, _ = roll_dirs(s['bend_dir'])
        d = (0.0, dd[0], dd[1])
        R = size * 2.0
        lead = max(SOCKET_LEN, socket_dims(size)[2] + 5.0) if detailed(s) else SOCKET_LEN
        arc = arc_path((lead, 0, 0), X, d, R, turn, 14)
        Tend = v_add(v_mul(X, math.cos(turn)), v_mul(d, math.sin(turn)))
        path = [(0, 0, 0)] + arc + [v_add(arc[-1], v_mul(Tend, lead))]
        so, (T, ups, _) = sweep_solid(path, Z, o, i, 'in', 'out')
        sol.append(so)
        r = size / 2
        heel = lead + R + r                      # lowest point of the outside of the bend
        c = (dd[0] * R * 0.75, dd[1] * R * 0.75)
        e = (dd[1], -dd[0])
        h = size * 0.45
        sol.append(block(heel - 25.0, heel + 15.0,
                         [(c[0] + e[0] * h + dd[0] * h, c[1] + e[1] * h + dd[1] * h),
                          (c[0] - e[0] * h + dd[0] * h, c[1] - e[1] * h + dd[1] * h),
                          (c[0] - e[0] * h - dd[0] * h, c[1] - e[1] * h - dd[1] * h),
                          (c[0] + e[0] * h - dd[0] * h, c[1] + e[1] * h - dd[1] * h)]))
        if detailed(s):
            sol.append(collar((0, 0, 0), X, size))
            sol.append(collar(path[-1], v_mul(T[-1], -1.0), size))
        ports['in'] = port((0, 0, 0), NX, Z, 'in', system)
        ports['out'] = port(path[-1], T[-1], ups[-1], 'out', system)

    elif kind == 'shoe':
        # a shoe: kicks the end of a pipe out, e.g. over a gully
        turn = math.radians(67.5)
        dd, _ = roll_dirs(s['bend_dir'])
        d = (0.0, dd[0], dd[1])
        R = size * 0.8
        arc = arc_path((60.0, 0, 0), X, d, R, turn, 9)
        Tend = v_add(v_mul(X, math.cos(turn)), v_mul(d, math.sin(turn)))
        path = [(0, 0, 0)] + arc + [v_add(arc[-1], v_mul(Tend, 40.0))]
        so, _ = sweep_solid(path, Z, o, i, 'in', None)
        sol.append(so)
        if detailed(s):
            sol.append(collar((0, 0, 0), X, size))
        ports['in'] = port((0, 0, 0), NX, Z, 'in', system)

    elif kind == 'bigully':
        # a back-inlet gully: the pipe goes down into a socket at the back, below the
        # grid; the grid sits in front, towards the room side (away from the wall)
        ts = socket_dims(size)[0]
        r = size / 2
        Tb = 60.0                                  # top of the gully body
        sol.append(revolve_profile((0, 0, 0), X, [(0.0, r), (0.0, r + ts), (Tb, r + ts), (Tb, r)]))
        back, front = r + ts + 15.0, -(r + ts + 170.0)
        sol.append(box_solid(Tb, Tb + 240.0, -85.0, 85.0, front, back))       # body
        g0, g1 = Tb - 12.0, Tb
        gz0, gz1 = front, -(r + ts + 5.0)
        for y0, y1, z0, z1 in ((-85, 85, gz0, gz0 + 12), (-85, 85, gz1 - 12, gz1),
                               (-85, -73, gz0 + 12, gz1 - 12), (73, 85, gz0 + 12, gz1 - 12)):
            sol.append(box_solid(g0, g1, y0, y1, z0, z1))
        n_bars = 4
        for k in range(n_bars):
            zc = gz0 + 12 + (gz1 - gz0 - 24) * (k + 0.5) / n_bars
            sol.append(box_solid(g0, g1, -73, 73, zc - 4, zc + 4))
        ports['in'] = port((0, 0, 0), NX, Z, 'in', system)

    elif kind == 'vent':
        r0 = size / 2 + fit_gap(s)
        r1 = r0 + 3.0 * m
        if detailed(s):
            # a cage vent cowl: sleeve over the pipe, ribs, then a domed top
            H = size * 0.55                                  # height of the cage
            rc = r1 + size * 0.04
            sol.append(revolve_profile((0, 0, 0), X, [(-40.0, r0), (-40.0, r1), (8.0, r1),
                                                      (8.0, rc), (16.0, rc), (16.0, r0)]))
            for k in range(8):
                d, e = roll_dirs(k * 45.0)
                sol.append(rect_sweep(15.0, 16.0 + H + 1.0, d, e, rc - 4.0 * m, rc, 2.5 * m))
            top = 16.0 + H
            sol.append(revolve_profile((0, 0, 0), X, [(top, 2.0), (top, rc), (top + 6.0, rc),
                                                      (top + 6.0 + size * 0.22, 2.0)]))
        else:
            sol.append(revolve_solid([(-40.0, r1), (20.0, r1), (20.0, r1 * 1.15),
                                      (20.0 + size * 0.6, 2.0)]))
        ports['in'] = port((0, 0, 0), NX, Z, 'in', system)

    elif kind == 'drain':
        r0 = size / 2 + fit_gap(s)
        r1 = r0 + 3.0 * m
        if detailed(s):
            # a stepped drain adaptor: sleeve over the pipe, a wide collar at ground
            # level, then a bigger spigot that goes into the underground drain
            rs = size / 2 + 25.0
            sol.append(revolve_profile((0, 0, 0), X, [(-40.0, r0), (-40.0, r1), (0.0, r1),
                                                      (0.0, size / 2 + 40), (12.0, size / 2 + 40),
                                                      (12.0, rs), (150.0, rs), (150.0, r0)]))
        else:
            sol.append(revolve_solid([(-40.0, r1), (0.0, r1), (0.0, size / 2 + 40), (12.0, size / 2 + 40),
                                      (12.0, r1), (150.0, r1)]))
        ports['in'] = port((0, 0, 0), NX, Z, 'in', system)

    elif kind == 'adaptor':
        # a rubber boss adaptor: a sleeve with a lip that seats in the end it goes on
        r0 = size / 2 + fit_gap(s, 0.2)
        ts = socket_dims(size)[0]
        Ls = socket_dims(size)[1]
        x0 = -s['offset']
        sol.append(revolve_profile((x0, 0, 0), X, [(-Ls * 0.8, r0), (-Ls * 0.8, r0 + ts * 0.6),
                                                   (0.0, r0 + ts * 0.6), (0.0, r0 + ts + 4.0),
                                                   (5.0, r0 + ts + 4.0), (5.0, r0)]))
        ports['in'] = port((0, 0, 0), NX, Z, 'in', system)

    elif kind == 'hopper':
        # an old-style hopper head: open-topped flared box, rim band, back plate with
        # fixing ears, and a spigot underneath for the downpipe. Its rim sits 30 mm
        # below the pipe end it is added to; local z points at the wall.
        g0, t = 30.0, 4.0 * m
        W1, D1, W2, D2, H = 280.0, 200.0, 140.0, 110.0, 220.0
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
        so, _ = sweep_solid([(g0 + H - t * 0.5, 0, 0), (g0 + H + 60.0, 0, 0)], Z, o, i, None, 'out')
        sol.append(so)
        ports['in'] = port((0, 0, 0), NX, Z, 'in', system)
        ports['out'] = port((g0 + H + 60.0, 0, 0), X, Z, 'out', system)

    elif kind == 'gully':
        # a trapped gully under the pipe end: grid 30 mm below the end, body under it
        g0 = 30.0
        sol.append(box_solid(g0 + 12, g0 + 250, -75, 75, -75, 75))            # body
        for y0, y1, z0, z1 in ((-85, 85, -85, -70), (-85, 85, 70, 85),         # grid frame
                               (-85, -70, -70, 70), (70, 85, -70, 70)):
            sol.append(box_solid(g0, g0 + 12, y0, y1, z0, z1))
        for zc in (-45.0, -15.0, 15.0, 45.0):                                  # grid bars
            sol.append(box_solid(g0, g0 + 12, -70, 70, zc - 5, zc + 5))
        ports['in'] = port((0, 0, 0), NX, Z, 'in', system)
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
    """Where a part goes when no open end is selected: at the origin with the wall
    behind (+Y). Soil pipes run down the wall; waste pipes come straight out of it.
    wall_deg turns everything about the vertical so the wall is on another side."""
    w = rotate(Y, Z, math.radians(wall_deg))
    if system == 'soil':
        return {'c': (0.0, 0.0, 0.0), 'n': NZ, 'u': w, 'role': 'out', 'sys': 'soil'}
    return {'c': (0.0, 0.0, 0.0), 'n': v_mul(w, -1.0), 'u': NZ, 'role': 'out', 'sys': 'waste'}


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
                      'u': list(v_norm(vec(pd['u']))), 'role': pd['role'], 'sys': pd['sys'],
                      'sock': bool(pd.get('sock'))}
    # parts that sit over a joint pass the original end on, so you can carry on from them
    if not free:
        tags['copy'] = {k: (list(v) if isinstance(v, tuple) else v) for k, v in target.items()
                        if k in ('c', 'n', 'u', 'role', 'sys', 'sock')}
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
    t['settings'] = {k: vals[k] for k in SYSTEM_KEYS[t['sys']]}
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


# ---------------------------------------------------------------------------
# Starting on a wall, and spacing clips
# ---------------------------------------------------------------------------
def wall_info(face, flip=False):
    """Reads a picked wall face: which way it faces, its top, bottom and two ends."""
    pts = [p for p in (_pos(v) for v in _items(getattr(face, 'vertices', None))) if p is not None]
    if len(pts) < 3:
        raise ValueError("That face has no corners I can read.")
    n = _newell(pts)
    if flip:
        n = v_mul(n, -1.0)
    if abs(n[2]) > 0.35:
        raise ValueError("Pick an upright wall face (this one is a floor, roof or ceiling).")
    n = v_norm((n[0], n[1], 0.0))
    run = v_norm(v_cross(Z, n))          # along the wall, left to right seen from outside
    ss = [v_dot(p, run) for p in pts]
    return {'n': n, 'run': run, 's0': min(ss), 's1': max(ss),
            'top': max(p[2] for p in pts), 'bottom': min(p[2] for p in pts),
            'd': max(v_dot(p, n) for p in pts)}


def clip_standoff(s, system):
    """Distance from the pipe centre to the back of its clip plate (mm)."""
    v = view(s, system)
    m = fix_mult(s)
    return v['p_size'] / 2 + fit_gap(s, 0.3) + 3.0 * m + 35 + 4 * m


def wall_target(w, s, system, kind=''):
    """Where a run starts on a picked wall. Soil: the top of a stack running down the
    wall. Waste: coming straight out of the wall; a hopper head stands on the wall.
    Returns (target, fitted length in mm)."""
    mm = 0.001
    along = w['s0'] + s['along'] * mm
    if along > w['s1'] + 1e-9:
        raise ValueError("'Along the wall' is past the right-hand end of this wall "
                         "(it is %.0f mm long)." % ((w['s1'] - w['s0']) / mm))
    if system == 'soil':
        dist = w['d'] + (clip_standoff(s, 'soil') + s['wall_gap']) * mm
        z = w['top'] - s['drop'] * mm
        c = v_add(v_add(v_mul(w['run'], along), v_mul(w['n'], dist)), (0.0, 0.0, z))
        length = (z - w['bottom']) / mm + s['below']
        if length < 10.0:
            raise ValueError("The stack settings leave no pipe on this wall.")
        return ({'c': c, 'n': NZ, 'u': v_mul(w['n'], -1.0), 'role': 'out', 'sys': 'soil',
                 'label': "the selected wall", 'end': 'top'}, length)
    z = w['bottom'] + s['w_height'] * mm
    if z > w['top'] + 1e-9:
        raise ValueError("The waste height is above the top of this wall.")
    if kind == 'hopper':
        # the hopper's back plate sits on the wall, its rim at the waste height
        dist = w['d'] + (s['w_size'] / 2 + 15.0 + 6.0 * fix_mult(s) + s['wall_gap']) * mm
        c = v_add(v_add(v_mul(w['run'], along), v_mul(w['n'], dist)), (0.0, 0.0, z + 0.030))
        return ({'c': c, 'n': NZ, 'u': v_mul(w['n'], -1.0), 'role': 'out', 'sys': 'waste',
                 'label': "the selected wall", 'end': 'top'}, None)
    c = v_add(v_add(v_mul(w['run'], along), v_mul(w['n'], w['d'])), (0.0, 0.0, z))
    return ({'c': c, 'n': w['n'], 'u': NZ, 'role': 'out', 'sys': 'waste',
             'label': "the selected wall", 'end': 'wall'}, None)


def fixing_positions(L, spacing, margin=150.0):
    """Even positions along a length L: near each end and never more than spacing apart."""
    if L <= 2 * margin:
        return [L / 2.0]
    inner = L - 2 * margin
    k = max(1, int(math.ceil(inner / max(spacing, 1.0) - 1e-9)))
    return [margin + inner * i / k for i in range(k + 1)]


def roll_towards(end, wall_dir):
    """Roll angle (deg) round a pipe end that points a clip's lug at the wall."""
    n, u = v_norm(tuple(end['n'])), v_norm(tuple(end['u']))
    w = v_sub(wall_dir, v_mul(n, v_dot(wall_dir, n)))
    if v_len(w) < 1e-6:
        return 0.0
    side = v_cross(v_mul(n, -1.0), u)
    return math.degrees(math.atan2(v_dot(w, side), v_dot(w, u)))


def fixings(key, s, out_end, wall_dir):
    """Clips along a soil or waste pipe length, lugs pointing at the wall."""
    system = PART_INFO[key][1]
    ckey = 's_clip' if system == 'soil' else 'w_clip'
    spacing = s['s_spacing'] if system == 'soil' else s['w_spacing']
    L = s['length']
    roll = roll_towards(out_end, wall_dir)
    world = []
    pos = fixing_positions(L, spacing)
    for x in pos:
        w, _ = plan_part(ckey, dict(s, offset=L - x, bend_dir=roll), out_end)
        world.extend(w)
    return world, len(pos)


def size_text(key, s):
    system = PART_INFO[key][1]
    return "%s %g" % ("Soil" if system == 'soil' else "Waste",
                      s['s_size'] if system == 'soil' else s['w_size'])


def group_name(key, s):
    name = "%s - %s" % (PART_INFO[key][0], size_text(key, s))
    if key in ('s_pipe', 'w_pipe'):
        name += " x %g mm" % s['length']
    return name

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
    """Flat-shaded 2D polygons of the part (plus the wall, and the pipe it fits
    over, drawn faintly). Returns [(depth, [(x, y)...], (r, g, b), alpha)] far to near."""
    system = PART_INFO[key][1]
    kind = key[2:]
    s = dict(vals)
    ref = s['s_size'] if system == 'soil' else s['w_size']
    s['length'] = min(s['length'], 4.0 * ref)
    s['branch_len'] = min(s['branch_len'], 3.0 * ref)
    s['offset'] = 0.0
    wdir = rotate(Y, Z, math.radians(s.get('wall_side', 0.0)))
    start = free_target(system, s.get('wall_side', 0.0))
    if kind in ('gully', 'hopper', 'bigully', 'shoe'):   # these go on a pipe coming down
        start = {'c': (0.0, 0.0, 0.0), 'n': NZ, 'u': wdir, 'role': 'out', 'sys': system}
    ghost = []
    target, free = start, True
    if kind in OVERLAY or kind in CLOSERS or kind == 'hopper':
        host = 's_pipe' if system == 'soil' else 'w_pipe'
        hw, ht = plan_part(host, dict(s, length=2.5 * ref), start, free=True)
        ghost = hw
        end = 'in' if kind == 'vent' else 'out'       # a vent goes on the top of the stack
        target = make_target(ht[end], s, '', end)
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
    add_solids(main, (95, 105, 115) if system == 'soil' else (225, 228, 232), 0.45, 1.0)

    # the wall, as a see-through panel
    allp = [p for so in main + ghost for f, _ in so.faces for p in f]
    if allp:
        w = wdir
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
class SoilWasteDialog(QDialog):
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
        self.wall = None           # a picked wall the next run starts on
        self.wall_face = None
        self.wall_dir = None       # which way the wall is, for pointing clips at it
        self.user_presets = load_presets()
        lay = QVBoxLayout(self)

        self.lbl_target = QLabel()
        self.lbl_target.setWordWrap(True)
        self.lbl_target.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl_target)

        self.cb_solid = QCheckBox("Solid (for 3D printing) - no hollow inside")
        self.cb_solid.setChecked(bool(cur.get('solid')))
        self.cb_solid.setToolTip("Fills the pipes in, so small-scale prints come out strong. "
                                 "Fit-over parts (sockets, clips, bosses) stay as sleeves.")
        lay.addWidget(self.cb_solid)
        self.cb_detail = QCheckBox("Detailed fittings (socket collars, rodding eye, bosses)")
        self.cb_detail.setChecked(bool(cur.get('detail', True)))
        self.cb_detail.setToolTip("Gives fittings thick socket collars at their ends, a round rodding "
                                  "eye with cap and bolts on access pipes, and collars on boss outlets.")
        lay.addWidget(self.cb_detail)
        self.cb_psock = QCheckBox("Pipe lengths have a socket on the start (top) end")
        self.cb_psock.setChecked(bool(cur.get('pipe_socket', True)))
        self.cb_psock.setToolTip("Like real soil and waste pipe: one plain end and one socket end. "
                                 "A pipe that joins onto a bend, branch, boss or coupler goes in "
                                 "plain-ended, as that fitting has the socket. "
                                 "Only used with Detailed fittings.")
        self.cb_detail.toggled.connect(self.cb_psock.setEnabled)
        self.cb_psock.setEnabled(self.cb_detail.isChecked())
        lay.addWidget(self.cb_psock)
        self.cb_ears = QCheckBox("Cast-iron style ears on pipe sockets (instead of clips)")
        self.cb_ears.setChecked(bool(cur.get('ears', False)))
        self.cb_ears.setToolTip("Puts two fixing lugs on each pipe length's socket, facing the wall, "
                                "like Victorian cast-iron pipe. Pipe clips are then left off.")
        self.cb_psock.toggled.connect(self.cb_ears.setEnabled)
        self.cb_ears.setEnabled(self.cb_psock.isChecked() and self.cb_detail.isChecked())
        lay.addWidget(self.cb_ears)

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
        self.lst.setMinimumHeight(300)
        for header, system in (("SOIL PIPE", 'soil'), ("WASTE PIPE", 'waste')):
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

        def mm_spin(val, lo=0.1, hi=100000.0, suffix=" mm", dec=1):
            sp = QDoubleSpinBox()
            sp.setDecimals(dec)
            sp.setRange(lo, hi)
            sp.setSuffix(suffix)
            sp.setValue(val)
            return sp

        # ---- pipe sizes ----
        pb = QGroupBox("Pipe sizes")
        pf = QFormLayout(pb)
        self.sp_ss = mm_spin(cur['s_size'], 20.0)
        self.sp_st = mm_spin(cur['s_wall'], 0.5, 50.0)
        self.sp_ws = mm_spin(cur['w_size'], 10.0)
        self.sp_wt = mm_spin(cur['w_wall'], 0.5, 50.0)
        self.sp_ss.setToolTip("Outside diameter of the soil pipe: 110 mm is standard, 82 mm is also used.")
        self.sp_ws.setToolTip("Outside diameter of the waste pipe: 32 mm for basins, 40 mm for sinks "
                              "and baths, 50 mm for longer runs.")
        pf.addRow("Soil pipe diameter:", self.sp_ss)
        pf.addRow("Soil pipe wall:", self.sp_st)
        pf.addRow("Waste pipe diameter:", self.sp_ws)
        pf.addRow("Waste pipe wall:", self.sp_wt)

        left = QVBoxLayout()
        left.addWidget(self.lst)
        left.addWidget(pb)

        # ---- this part ----
        sb = QGroupBox("This part")
        sf = QFormLayout(sb)
        self.preview = PartPreview()
        sf.addRow(self.preview)
        cap = QLabel("Brown panel = the wall. Pale grey = the pipe it fits over.")
        cap.setStyleSheet("color: gray; font-size: 9pt;")
        sf.addRow(cap)
        self.sp = {
            'length': mm_spin(cur['length'], 1.0),
            'bend_turn': mm_spin(cur['bend_turn'], 1.0, 135.0, " deg"),
            'branch_len': mm_spin(cur['branch_len'], 10.0),
            'offset': mm_spin(cur['offset'], 0.0),
            'swan_len': mm_spin(cur['swan_len'], 0.0),
        }
        self.sp['swan_len'].setToolTip("Length of the straight between the two bends of a swan neck.")
        self.sp['bend_turn'].setToolTip("How far the pipe turns. A 92.5 deg bend or branch turns 87.5; "
                                        "a 112.5 deg turns 67.5; a 135 deg turns 45; a 90 deg turns 90.")
        self.sp['offset'].setToolTip("0 = centred on the end you selected. Larger values slide it "
                                     "back along the pipe.")
        self.cb_dir = QComboBox()
        for label, deg in BEND_DIRS:
            self.cb_dir.addItem(label, deg)
            if abs(deg - cur['bend_dir']) < 1e-6:
                self.cb_dir.setCurrentIndex(self.cb_dir.count() - 1)
        self.cb_dir.setToolTip("Which way the bend, branch, boss, access door or clip faces. "
                               "On a pipe coming out of a wall 'Down' bends it down; on an upright "
                               "pipe it turns towards the wall.")
        labels = {'length': "Length:", 'bend_turn': "Turn angle:", 'branch_len': "Branch length:",
                  'offset': "Distance back from the end:", 'swan_len': "Offset length:"}
        self.rows = {}
        for k in ('length', 'bend_turn', 'branch_len', 'offset', 'swan_len'):
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
        wb = QGroupBox("Start on a wall")
        wf = QFormLayout(wb)
        b_wall = QPushButton("Use selected wall")
        b_wall.setToolTip("Select a wall face, then click this. A soil part starts a stack down the "
                          "wall; a waste part comes straight out of the wall.")
        b_wall.clicked.connect(self.use_selected_wall)
        wf.addRow(b_wall)
        self.sp_along = mm_spin(cur['along'], 0.0)
        self.sp_along.setToolTip("Distance from the left end of the wall, as you look at it from outside.")
        self.sp_drop = mm_spin(cur['drop'], -100000.0)
        self.sp_drop.setToolTip("Soil stack: how far its top sits below the top of the wall. "
                                "Negative takes it above the wall, e.g. to vent above the eaves.")
        self.sp_below = mm_spin(cur['below'], -100000.0)
        self.sp_below.setToolTip("Soil stack: how far it carries on below the bottom of the wall "
                                 "(into the ground). Negative stops short.")
        self.sp_wh = mm_spin(cur['w_height'], 0.0)
        self.sp_wh.setToolTip("Waste pipe: height above the bottom of the wall where it comes out.")
        self.sp_wgap = mm_spin(cur['wall_gap'], 0.0)
        self.sp_wgap.setToolTip("Soil stack: 0 = clips sit flat on the wall. More moves the stack out.")
        self.cb_fit = QCheckBox("Soil pipe length = wall height")
        self.cb_fit.setChecked(cur['fit_wall'])
        self.cb_flip = QCheckBox("Wrong side? Put it on the other side of the wall")
        self.cb_flip.setChecked(cur['wall_flip'])
        self.cb_flip.toggled.connect(self.reread_wall)
        wf.addRow("Along the wall:", self.sp_along)
        wf.addRow("Soil - below top of wall:", self.sp_drop)
        wf.addRow("Soil - below bottom of wall:", self.sp_below)
        wf.addRow("Waste - height on the wall:", self.sp_wh)
        wf.addRow("Extra gap from wall:", self.sp_wgap)
        wf.addRow(self.cb_fit)
        wf.addRow(self.cb_flip)

        # ---- clips ----
        fb = QGroupBox("Pipe clips")
        ff = QFormLayout(fb)
        self.cb_fix = QCheckBox("Add them evenly with every pipe length")
        self.cb_fix.setChecked(cur['auto_fix'])
        self.sp_ssp = mm_spin(cur['s_spacing'], 100.0)
        self.sp_wsp = mm_spin(cur['w_spacing'], 100.0)
        self.sp_ssp.setToolTip("Most a soil pipe clip can be from the next one. One also goes near each end.")
        self.sp_wsp.setToolTip("Most a waste pipe clip can be from the next one. One also goes near each end.")
        ff.addRow(self.cb_fix)
        ff.addRow("Soil clips at most:", self.sp_ssp)
        ff.addRow("Waste clips at most:", self.sp_wsp)
        self.cb_chunky = QCheckBox("Chunky fittings (for 3D printing)")
        self.cb_chunky.setChecked(cur['chunky'])
        self.cb_chunky.setToolTip("Makes every clip, socket, boss and vent thicker with no gap to the "
                                  "pipe, so they survive printing at small scales.")
        self.sp_chunk = mm_spin(cur['chunk_mult'], 1.0, 10.0, " x", 1)
        self.sp_chunk.setToolTip("How many times thicker than real fittings.")
        ff.addRow(self.cb_chunky)
        ff.addRow("   Thicker by:", self.sp_chunk)
        self.cb_chunky.toggled.connect(self.sp_chunk.setEnabled)
        self.sp_chunk.setEnabled(self.cb_chunky.isChecked())
        self.cb_fix.toggled.connect(lambda on: (self.sp_ssp.setEnabled(on), self.sp_wsp.setEnabled(on)))
        self.sp_ssp.setEnabled(self.cb_fix.isChecked())
        self.sp_wsp.setEnabled(self.cb_fix.isChecked())

        cols = QHBoxLayout()
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
        for c in (self.cb_solid, self.cb_chunky, self.cb_detail, self.cb_psock, self.cb_ears):
            c.toggled.connect(self.sync)
        for c in (self.cb_wall, self.cb_dir):
            c.currentIndexChanged.connect(self.sync)
        for w in [self.sp_ss, self.sp_st, self.sp_ws, self.sp_wt, self.sp_chunk] + list(self.sp.values()):
            w.valueChanged.connect(self.sync)
        self.sync()

    # ---- helpers ----
    def part(self):
        it = self.lst.currentItem()
        k = it.data(QtRole.user) if it is not None else None
        return k or 's_pipe'

    def sync(self, *_):
        part = self.part()
        uses = PART_INFO[part][2]
        for k, (lab, w) in self.rows.items():
            on = k in uses
            lab.setVisible(on)
            w.setVisible(on)
        if hasattr(self, 'preview'):
            self.preview.show_part(part, self.values())

    def current_wall_dir(self):
        if self.wall_dir is not None:
            return self.wall_dir
        return rotate(Y, Z, math.radians(self.cb_wall.currentData() or 0.0))

    def start_at_origin(self):
        self.wall = None
        self.wall_face = None
        self.wall_dir = None
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
        self.wall_dir = v_mul(self.wall['n'], -1.0)
        self.set_target(None)

    def set_target(self, t, finished=False):
        self.target = t
        if t is None and getattr(self, 'wall', None):
            txt = ("Next part starts on the selected wall: a soil part runs down from the top, "
                   "a waste part comes out of the wall.")
        elif t is None:
            txt = ("Run finished. " if finished else "") + \
                  "Next part goes at the origin. Or select an open end and click 'Use selected end'."
        else:
            where = END_NAMES.get(t.get('end'), "open end")
            what = t.get('label') or SYSTEM_NAMES.get(t['sys'], "pipe")
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
             's_size': self.sp_ss.value(), 's_wall': self.sp_st.value(),
             'w_size': self.sp_ws.value(), 'w_wall': self.sp_wt.value(),
             'along': self.sp_along.value(), 'drop': self.sp_drop.value(),
             'below': self.sp_below.value(), 'w_height': self.sp_wh.value(),
             'wall_gap': self.sp_wgap.value(), 'fit_wall': self.cb_fit.isChecked(),
             'wall_flip': self.cb_flip.isChecked(), 'auto_fix': self.cb_fix.isChecked(),
             's_spacing': self.sp_ssp.value(), 'w_spacing': self.sp_wsp.value(),
             'chunky': self.cb_chunky.isChecked(), 'chunk_mult': self.sp_chunk.value(),
             'bend_dir': self.cb_dir.currentData(), 'detail': self.cb_detail.isChecked(),
             'pipe_socket': self.cb_psock.isChecked(), 'ears': self.cb_ears.isChecked()}
        for k, w in self.sp.items():
            v[k] = w.value()
        return v

    def set_values(self, d):
        if 'solid' in d:
            self.cb_solid.setChecked(bool(d['solid']))
        if 'chunky' in d:
            self.cb_chunky.setChecked(bool(d['chunky']))
        if 'detail' in d:
            self.cb_detail.setChecked(bool(d['detail']))
        if 'pipe_socket' in d:
            self.cb_psock.setChecked(bool(d['pipe_socket']))
        if 'ears' in d:
            self.cb_ears.setChecked(bool(d['ears']))
        for w, key in ((self.sp_ss, 's_size'), (self.sp_st, 's_wall'), (self.sp_ws, 'w_size'),
                       (self.sp_wt, 'w_wall'), (self.sp_along, 'along'), (self.sp_drop, 'drop'),
                       (self.sp_below, 'below'), (self.sp_wh, 'w_height'), (self.sp_wgap, 'wall_gap'),
                       (self.sp_ssp, 's_spacing'), (self.sp_wsp, 'w_spacing'),
                       (self.sp_chunk, 'chunk_mult')):
            if d.get(key) is not None:
                w.setValue(float(d[key]))
        for k, w in self.sp.items():
            if d.get(k) is not None:
                w.setValue(float(d[k]))
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
class SoilWastePipesTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+W"
    description = "Soil stacks and outside waste pipes with fittings that join onto each other, with presets."

    _saved = None
    _dialog = None          # the open window (kept so it stays open between parts)

    def on_activate(self, viewport):
        _init_qt_constants()
        scene = getattr(viewport, 'scene', None)
        target = selected_port(list(getattr(scene, 'selection', None) or []))

        dlg = SoilWastePipesTool._dialog
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
        if SoilWastePipesTool._saved:
            cur.update(SoilWastePipesTool._saved)
        if target:
            cur.update(target.get('settings') or {})
            if PART_INFO[cur['part']][1] != target['sys']:
                cur['part'] = 's_pipe' if target['sys'] == 'soil' else 'w_pipe'

        dlg = SoilWasteDialog(cur, target, viewport, self)
        SoilWastePipesTool._dialog = dlg

        def closed(*_):
            SoilWastePipesTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass

    def add_from_dialog(self, dlg):
        viewport = dlg.viewport
        vals = dlg.values()
        SoilWastePipesTool._saved = dict(vals)
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
                QMessageBox.warning(dlg, PLUGIN_NAME, "A %s part can't join onto a %s end. Add a boss "
                                    "connector for a waste pipe, select a matching end and click "
                                    "'Use selected end', or start at the origin."
                                    % (SYSTEM_NAMES[system], SYSTEM_NAMES[dlg.target['sys']]))
                return
            free = False
        if t is None:
            if dlg.wall:
                try:
                    t, wall_len = wall_target(dlg.wall, vals, system, key[2:])
                except ValueError as e:
                    QMessageBox.warning(dlg, PLUGIN_NAME, str(e))
                    return
                if wall_len and vals['fit_wall'] and key == 's_pipe':
                    vals['length'] = wall_len
                on_wall = True
            else:
                t = free_target(system, vals['wall_side'])
                if key[2:] in ('hopper', 'gully', 'bigully'):   # these stand upright
                    t = {'c': (0.0, 0.0, 0.0), 'n': NZ, 'role': 'out', 'sys': system,
                         'u': rotate(Y, Z, math.radians(vals['wall_side']))}
        if vals.get('ears') and key[2:] == 'pipe':
            vals['ear_roll'] = roll_towards(t, dlg.current_wall_dir())
        bvals = vals
        if (key[2:] == 'pipe' and not free and not on_wall and t.get('sock')
                and t.get('role') != 'in'):
            # joining onto a fitting's socket (a bend, branch, boss...): the pipe goes in
            # plain-ended, so it doesn't get a second socket of its own
            bvals = dict(vals, pipe_socket=False)
        try:
            world, tags = plan_part(key, bvals, t, free=free)
        except Exception as e:
            QMessageBox.warning(dlg, PLUGIN_NAME, "Could not build the part:\n%s" % e)
            return

        parts = [(group_name(key, vals), world, tags)]
        ears = bvals.get('ears') and bvals.get('detail', True) and bvals.get('pipe_socket', True)
        if vals['auto_fix'] and not ears and key in ('s_pipe', 'w_pipe') and 'out' in tags:
            fix_world, nfix = fixings(key, vals, make_target(tags['out'], vals, label, 'out'),
                                      dlg.current_wall_dir())
            if nfix:
                parts.append(("Pipe clips x%d - %s" % (nfix, size_text(key, vals)), fix_world, {}))
        if not self.add_to_scene(viewport, vals, None if (free or on_wall) else t, parts):
            return
        if on_wall:
            dlg.wall = None            # the run has started; carry on from its end

        # keep track of which open ends are still free
        kind = key[2:]
        if not free and not on_wall and kind not in OVERLAY:
            dlg.open_ends = [e for e in dlg.open_ends if not same_end(e, t)]
        ends = {name: make_target(d, vals, label, name) for name, d in tags.items() if name != 'copy'}
        for name in ('in', 'boss2', 'boss', 'branch2', 'branch', 'out'):
            if name in ends:
                dlg.open_ends.append(ends[name])
        finished = False
        if kind in OVERLAY:
            nxt = None if (free or on_wall) else t      # sits over a joint: carry on from the same end
            if nxt is not None and kind == 'socket' and vals.get('detail', True):
                nxt = dict(nxt, sock=True)               # the coupler is the socket for the next pipe
        elif 'out' in ends:
            nxt = ends['out']
        else:
            # a vent, drain connector or gully closes this run: move on to the newest end still open
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
        sysset = {k: {kk: vals[kk] for kk in v} for k, v in SYSTEM_KEYS.items()}
        tol = 1e-4 * 0.001

        def port_data(tags, tag, pts):
            d = dict(tags[tag])
            if tag == 'copy' and target:
                d = dict(target)
                d.pop('_mine', None)
                d['c'], d['n'], d['u'] = list(d['c']), list(d['n']), list(d['u'])
            sysk = d['sys']
            d['settings'] = dict(d.get('settings') or sysset[sysk])
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
    SoilWastePipesTool().on_activate(viewport)
