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
part you placed and the next part joins onto it. Or draw lines where the runs go, select
them, and each run is built along its line with bends, collars, clips and end fittings.
Or mark the runs with the plugin's own thick line (Mark the run), easy to see on a detailed
building, and build along those.
Presets are saved as .json files.
Version 3: Mark the run - a thick marker line (size and colour to suit) that snaps to its own
ends; arrow keys lock it to an axis; Esc or right-click ends a line (again: finished); the
window hides while you mark. Everything built along lines goes into one group, and pipes
going down to the ground step out round anything in the way (a plinth, a sill, a lean-to).
Smaller preview.
Version 4.2: like the downpipes - mark a stack from the fascia (or gutter) straight down to the
ground and it gets a swan neck (two 45 degree bends) back to the wall under the eaves, the vent
above the eaves, down the wall on its clips, and out round the plinth at the bottom.
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
VERSION = "5.1"           # 5.1: the drain adaptor\'s spigot finishes level with the bottom of the plinth (it hung below); 5.0: the stack stops at the bottom of the plinth it comes down in front of (the drain adaptor at the ground), not where the line was marked below it; 4.9: soft edges really work (from the edges themselves - 4.8 softened none); 4.8: the edges are softened once the pipes are in the model (as 3D Blend does); 4.7: pipes look smooth - the lines round and along them are softened, so they show their real colour from a distance; 4.6: on a gable wall the vent goes just above the verge at the pipe (not above the ridge), and a stack marked below the ground stops at the bottom of the wall/plinth; 4.5: choose what goes on the end of a waste into the stack (left open, into the wall, or a tee into the wall with the run carrying on), and a tee at each corner clicked along it for another sink; 4.4: the vent goes just above the eaves (not up a roof slope or gable beside it), and the stack's clips sit on the front of the bricks; 4.3: the swan-necked stack's vent stops just above the eaves (Vent above the eaves setting), and a 40 mm waste marked into it gets its boss on the stack at the wall; 4.2: a stack marked straight down from the fascia gets a swan neck back to the wall under the eaves (like the downpipes), then steps round the plinth; 4.1: both sides of each pipe clip show (one side was inside out); 4.0: the sink waste meets the boss again (3.9 pushed its end off the wall); 3.9: clips all the way up the stack and along the waste (they were going on the wrong wall); 3.7: clips all the way up a stack stood off on quoins; 3.6: bigger clips you can see, clips come back (only left off where the stack stands right out past the eaves), and the report counts them; 3.5: saddle pipe clips (strap round the pipe, fixed to the wall each side); 3.4: no clips on the stack above the wall top; 3.3: the vent stands right out past the eaves; 3.2: a stack stepping out round the eaves stays out and vents just above them; 3.1: a waste marked from a stack gets a boss and dog-legs into it; shown in the window title, so you can tell which file is loaded


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
    'r_system': 'soil', 'r_top': 'vent', 'r_bot': 'drain', 's_maxlen': 3000.0, 'w_maxlen': 3000.0,
    'r_flip': False, 'r_avoid': True, 'r_swan': True, 'vent_above': 150.0, 'w_end': 'none',
}
WALL_SIDES = [("Behind the part (+Y)", 0.0), ("On the left (-X)", 90.0),
              ("In front (-Y)", 180.0), ("On the right (+X)", 270.0)]
PRESET_KEYS = ('s_size', 's_wall', 'w_size', 'w_wall', 'length', 'bend_turn', 'branch_len',
               'solid', 'along', 'drop', 'below', 'w_height', 'wall_gap',
               's_spacing', 'w_spacing', 'chunky', 'chunk_mult', 'detail', 'pipe_socket',
               'ears', 'swan_len', 's_maxlen', 'w_maxlen', 'r_avoid', 'r_swan', 'vent_above', 'w_end')
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
CLIP_LEN = 45.0
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
        t = {'socket': v['p_wall'] * 1.5 * m, 'clip': 5.0 * m, 'boss': v['p_wall'] * 1.5 * m}[kind]
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
            # a saddle clip: a strap round the pipe, both sides running straight back to the
            # wall, with a fixing foot on each side flat on the wall
            reach = s.get('reach')           # pipe middle to the wall, when it is known
            back = max(r_out + 4.0 * m, reach) if reach else r_out + 35 + 4 * m
            tl = 5.0 * m                     # strap thickness
            tf = 5.0 * m                     # foot thickness
            fw = 25.0 * m                    # how far each foot reaches out sideways

            def P(dd, ee, sg):
                return (d[0] * dd + e[0] * ee * sg, d[1] * dd + e[1] * ee * sg)
            for sg in (1.0, -1.0):
                # the far side is a mirror image, so its corners go round the other way
                # (or its faces would point inwards and it wouldn't show)
                strap = [P(0.0, r_out - tl, sg), P(back, r_out - tl, sg), P(back, r_out, sg), P(0.0, r_out, sg)]
                foot = [P(back - tf, r_out, sg), P(back, r_out, sg), P(back, r_out + fw, sg), P(back - tf, r_out + fw, sg)]
                if sg < 0:
                    strap, foot = strap[::-1], foot[::-1]
                sol.append(block(x0, x1, strap))
                sol.append(block(x0, x1, foot))
                if detailed(s):
                    # a screw head on each foot
                    sc = v_add((xc_ := (x0 + x1) / 2, 0.0, 0.0), (0.0, *P(back - tf, r_out + fw * 0.55, sg)))
                    sol.append(revolve_profile(sc, (0.0, -d[0], -d[1]),
                                               [(0.0, 0.3), (0.0, 5.0 * m), (2.0 * m, 5.0 * m), (2.0 * m, 0.3)], n=12))
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
DEBUG_LOG = []


def _dbg(*a):
    try:
        DEBUG_LOG.append(" ".join(str(x) for x in a))
    except Exception:
        pass


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
# Soil and waste pipes along drawn lines
# ---------------------------------------------------------------------------
ROUTE_SYSTEMS = [("Soil pipe", 'soil'), ("Waste pipe", 'waste')]
W_ENDS = [("Left open", 'none'), ("Into the wall", 'wall'),
          ("Tee - into the wall, carry on to the next sink", 'tee')]
ROUTE_TOPS = {'soil': [("Left open", 'none'), ("Vent cowl", 'vent')],
              'waste': [("Left open", 'none'), ("Hopper head", 'hopper')]}
ROUTE_BOTS = {'soil': [("Left open", 'none'), ("Drain adaptor (into the ground)", 'drain')],
              'waste': [("Left open", 'none'), ("Gully with grid", 'gully'),
                        ("Back-inlet gully", 'bigully'), ("Shoe", 'shoe')]}


def collar_world(c, into, D):
    """A socket collar (model metres) whose mouth is at c, running into the fitting along `into`."""
    ts, Ls, _ = socket_dims(D)
    R0 = D / 2.0
    return revolve_profile(c, into, [(0.0, R0 * MM), (0.0, (R0 + ts) * MM), (Ls * MM, (R0 + ts) * MM),
                                     (Ls * MM, R0 * MM)])


def wall_behind(top, bottom, n, faces, reach=2.5):
    """(n, d) of the wall face behind a pipe line going down, facing the same way as the
    wall n, or None. Brickwork from Brick & Block Studio stands proud of the
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
    """The bottom straight of a pipe (path[-2] down to path[-1] on the ground) stepped out
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
    ps = s['_ps_mm'] * MM                   # pipe middle to whatever it's clipped on
    hw = s['_size_mm'] * 0.5 * MM + 0.012   # the pipe's half width, and a little more
    z0, zb = top[2], bot[2]
    R = s['_size_mm'] * 0.8 * MM
    zst = z0 - (s.get('_top_straight', 0.0) + 0.5 * R)   # room for the bend at the top
    if s.get('_zcap') is not None:
        zst = min(zst, s['_zcap'])          # only below the top of the wall: not the eaves
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
        return None, "something sticks out too far just below where the pipe turns down for it to get round"
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


def wall_top_at(p, w, faces, near=0.15):
    """The top of the wall behind point p (the highest upright face in the wall's plane, give
    or take the brickwork, at p along the wall), or None. A stack going up past the eaves
    mustn't step out round the fascia, soffit or roof."""
    n, d = w
    a_ = (-n[1], n[0], 0.0)
    x = v_dot(a_, p)
    top = None
    for f in faces:
        fn = v_norm((f[0][0], f[0][1], 0.0))
        if abs(v_dot(fn, n)) < 0.94:
            continue
        P = f[2]
        if min(abs(v_dot(n, q) - d) for q in P) > near:
            continue
        xs = [v_dot(a_, q) for q in P]
        if min(xs) - 0.01 > x or max(xs) + 0.01 < x:
            continue
        # the top of this face right at p along the wall (a gable's top there, not its ridge)
        C = _clip_slab([(v_dot(a_, q) - x, 0.0, q[2]) for q in P], -0.06, 0.06)
        hz = max(c[2] for c in C) if C else f[3][1][2]
        if top is None or hz > top:
            top = hz
    return top


def _r_branches(chains, tol=0.25):
    """Splits marked soil runs into stacks and branches. A branch is a run along the wall
    (no real rise or fall) with one end on an upright stretch of another run - a sink
    waste going into the stack. Returns (stack chains, [(branch points from the stack end,
    stack chain, segment index)])."""
    def flat(pts):
        segs = list(zip(pts[:-1], pts[1:]))
        return segs and all(abs(b[2] - a[2]) < 0.3 * max(v_len(v_sub(b, a)), 1e-9) for a, b in segs)

    def upright(a, b):
        L = v_len(v_sub(b, a))
        return L > 1e-6 and abs(b[2] - a[2]) > 0.9 * L

    stacks, branches = [], []
    flags = [(not closed) and len(pts) >= 2 and flat([tuple(p) for p in pts]) for pts, closed in chains]
    for ci, (pts, closed) in enumerate(chains):
        if not flags[ci]:
            stacks.append((pts, closed))
            continue
        P = [tuple(p) for p in pts]
        hit = None
        for E, rev in ((P[0], False), (P[-1], True)):
            for cj, (qts, qc) in enumerate(chains):
                if cj == ci or flags[cj]:
                    continue
                Q = [tuple(q) for q in qts]
                for k, (a, b) in enumerate(zip(Q[:-1], Q[1:])):
                    if not upright(a, b):
                        continue
                    lo, hi = min(a[2], b[2]), max(a[2], b[2])
                    if not (lo - 0.05 <= E[2] <= hi + 0.05):
                        continue
                    if math.hypot(E[0] - a[0], E[1] - a[1]) < tol:
                        hit = (list(reversed(P)) if rev else P, Q, k)
                        break
                if hit:
                    break
            if hit:
                break
        if hit:
            branches.append(hit)
        else:
            stacks.append((pts, closed))
    return stacks, branches


def _r_vent_out(Q, walls, wb, zcap, clear=0.3):
    """A stack that steps out round the eaves stays out: straight up from there a little way
    to clear them, with the vent on top - no bending back in over the roof.
    Q is top first; walls[i] goes with the stretch Q[i]-Q[i+1]."""
    if len(Q) < 3 or zcap is None or Q[0][2] < zcap + 0.05:
        return Q, walls
    n, d = wb
    us = [v_dot(n, q) - d for q in Q]
    base = us[0]
    k = next((i for i in range(1, len(Q)) if us[i] > base + 0.02), None)
    if k is None or k >= len(Q) - 1 or Q[k][2] < zcap - 0.05:
        return Q, walls                     # not stepping out round the eaves at the top
    j = k                                   # the outermost point of that step (fully out)
    while j + 1 < len(Q) - 1 and us[j + 1] > base + 0.02:
        j += 1
    umax = max(us[k:j + 1])
    k = next(i for i in range(k, j + 1) if us[i] > umax - 0.003)
    top = (Q[k][0], Q[k][1], max(Q[k][2] + clear, zcap + 0.45))      # clear of the eaves
    nw = ([walls[k]] if k < len(walls) else []) + list(walls[k:])
    return [top] + list(Q[k:]), nw


def _r_brick_front(top, bottom, n, faces):
    """The plane (d along n) of the front of the bricks behind a pipe line going down: the
    nearest face found at many heights, taking the front fifth (bricks stand proud of the
    mortar; a sill, quoin or band sticking out at a few heights is left out)."""
    hits = []
    for i in range(40):
        f_ = 0.2 + 0.65 * i / 39.0
        q = v_add(top, v_mul(v_sub(bottom, top), f_))
        near = None
        for face in faces:
            lo, hi = face[3]
            if q[2] < lo[2] - 0.003 or q[2] > hi[2] + 0.003:
                continue
            fn, fd = face[0], face[1]
            c = v_dot(fn, n)
            if c < -0.94:
                fn, fd = v_mul(fn, -1.0), -fd
            elif c < 0.94:
                continue
            tt = v_dot(fn, q) - fd
            if tt < 0.005 or tt > 2.5:
                continue
            if near is not None and tt >= near:
                continue
            if _r_on_face(v_sub(q, v_mul(fn, tt)), face, 0.003):
                near = tt
        if near is not None:
            hits.append(v_dot(n, q) - near)          # the plane's d along n
    if len(hits) < 5:
        return None
    hits.sort(reverse=True)                          # furthest out first
    return hits[len(hits) // 5]


def _r_stack_swan(P, Q, walls, faces, s, sp, R, lead, top_k, size, all_faces=None):
    """A soil stack marked straight down from the fascia (or the gutter) to the ground, like a
    downpipe: out past the eaves at the top (clear of the fascia, gutter and roof edge, with the
    vent above them), two 45 degree bends back in to the wall under the eaves, then down the
    wall on its clips. P is the marked line and Q the pipe line (top first).
    Returns (new Q, walls, the wall) or None to build it as marked."""
    if len(P) < 2 or len(_r_clean(P)) != 2:
        return None                                  # only one straight line down
    top, bot = P[0], P[-1]
    if math.hypot(top[0] - bot[0], top[1] - bot[1]) > 0.003 or top[2] - bot[2] < 1.0:
        return None
    # which way the wall faces: the face the line is on (fascia or gutter), or look all round
    cands = [walls[0][0]] if walls and walls[0] else [(1.0, 0.0, 0.0), (-1.0, 0.0, 0.0),
                                                       (0.0, 1.0, 0.0), (0.0, -1.0, 0.0)]
    best = None
    for n_ in cands:
        w = wall_behind(Q[0], Q[-1], n_, faces)
        if w is None:
            continue
        u = v_dot(w[0], Q[0]) - w[1]
        if u > 0.005 and (best is None or u < best[0]):
            best = (u, w)
    if best is None:
        return None
    n, dw = best[1]
    fb = _r_brick_front(Q[0], Q[-1], n, faces)
    if fb is not None and abs(fb - dw) < 0.06:
        dw = fb                                      # the front of the bricks, not the mortar behind
        best = (v_dot(n, Q[0]) - dw, (n, dw))
    ps = sp * MM
    r = size * 0.5 * MM
    try:                                             # what's behind the pipe at a few heights (debug file)
        _dbg("swan: wall", tuple(round(c, 3) for c in n), round(dw, 4), "line out", round(best[0], 4),
             "upright faces", len(faces))
        for f_ in (0.3, 0.5, 0.7):
            q = v_add(Q[0], v_mul(v_sub(Q[-1], Q[0]), f_))
            ts = []
            for face in faces:
                lo, hi = face[3]
                if q[2] < lo[2] - 0.003 or q[2] > hi[2] + 0.003:
                    continue
                fn, fd = face[0], face[1]
                c = v_dot(fn, n)
                if c < -0.94:
                    fn, fd = v_mul(fn, -1.0), -fd
                elif c < 0.94:
                    continue
                tt = v_dot(fn, q) - fd
                if 0.0 < tt < 2.5 and _r_on_face(v_sub(q, v_mul(fn, tt)), face, 0.003):
                    ts.append(round(tt, 4))
            _dbg("swan: z", round(q[2], 2), "faces behind (m from line)", sorted(set(ts))[:8])
        _dbg("swan: brick front", round(dw, 4))
    except Exception as e:
        _dbg("swan: debug failed", e)
    if best[0] - ps < 0.025:
        return None                                  # marked on the wall already: build as marked
    zcap = wall_top_at(Q[-1], (n, dw), faces)        # top of the wall (under the eaves)
    if zcap is None:
        return None
    # what's at the eaves around the pipe: fascia, soffit, gutter, roof edge
    a_ = (-n[1], n[0], 0.0)
    x0 = v_dot(a_, Q[0])
    hw = r + 0.03
    low, out_u, high = None, None, None
    cut = []                                         # each face cut down to the pipe's own column
    for f in (all_faces or faces):
        lo, hi = f[3]
        if hi[2] < zcap - 0.3 or lo[2] > max(Q[0][2], zcap) + 3.0:
            continue
        if abs(f[0][2]) <= 0.35 and lo[2] < zcap - 0.6:
            continue                                 # an upright face running down the wall
        C = _clip_slab([(v_dot(a_, p) - x0, v_dot(n, p) - dw, p[2]) for p in f[2]], -hw, hw)
        if not C:
            continue
        us = [c[1] for c in C]
        if max(us) < 0.03 or min(us) > best[0] + 0.6:
            continue                                 # the wall or its bricks, or well out in front
        cut.append(C)
        low = lo[2] if low is None else min(low, max(min(c[2] for c in C), zcap - 0.6))
        out_u = max(us) if out_u is None else max(out_u, max(us))
    for C in cut:                                    # the top of the eaves at their outer edge
        for c in C:
            if c[1] > out_u - 0.15 and c[2] <= zcap + 0.8:   # not the roof slope or a gable going up
                high = c[2] if high is None else max(high, c[2])
    eaves_low = min(zcap, low) if low is not None else zcap
    u_pipe = best[0]
    if top_k == 'vent' or Q[0][2] > eaves_low:
        if out_u is not None:
            u_pipe = max(u_pipe, out_u + r + 0.015)  # out past the gutter and roof edge
    t0 = v_add(Q[0], v_mul(n, u_pipe - best[0]))
    if top_k == 'vent':
        above = s.get('vent_above', 150.0) * MM
        zt = (high if high is not None else zcap) + above
        if top[2] > zt + 0.02 and top[2] > Q[-1][2]:
            zt = top[2]                              # marked higher on purpose: go up to there
        t0 = (t0[0], t0[1], max(zt, zcap + 0.05))    # the vent just above the eaves
    off = u_pipe - ps                                # how far in the pipe has to come
    drop = lead + R + 0.06
    za = min(t0[2] - drop, eaves_low - 2.0 * r - 0.42 * R - 0.02)   # below the eaves
    a = (t0[0], t0[1], za)
    b = v_add(v_sub(a, v_mul(n, off)), (0.0, 0.0, -off))          # 45 degrees in to the wall
    g = v_sub(Q[-1], v_mul(n, best[0] - ps))         # down the wall to the ground
    base = None                                      # the bottom of the wall / plinth behind it
    for f in faces:
        if f[3][0][2] > g[2] + 1.5:
            continue
        us = [v_dot(n, p) - dw for p in f[2]]
        if max(us) < -0.05 or min(us) > ps + 0.4:
            continue
        C = _clip_slab([(v_dot(a_, p) - x0, 0.0, p[2]) for p in f[2]], -r, r)
        if C:
            zb = min(c[2] for c in C)
            base = zb if base is None else min(base, zb)
    if base is not None and g[2] < base - 0.01:
        _dbg("swan: stack bottom", round(g[2], 3), "up to the bottom of the wall", round(base, 3))
        g = (g[0], g[1], base)                       # the drain adaptor sits at the ground
    if b[2] < g[2] + lead + R + 0.3 or t0[2] < a[2] + lead + R:
        return None                                  # too short for the bends
    out = [t0, a, b, g]
    return out, [(n, dw)] * (len(out) - 1), (n, dw)


def build_soil_route(chains, faces, s, all_faces=None):
    """Soil or waste pipe runs along the lines (each line a run, top first), with bends where
    the line turns, socket collars, clips to the wall and the ends finished off.
    Returns (parts, report, notes)."""
    system = s.get('r_system', 'soil')
    pre = 's_' if system == 'soil' else 'w_'
    v = view(s, system)
    size = v['p_size']
    det = detailed(s)
    sname = size_text(pre + 'pipe', s)
    flip = s.get('r_flip', False)
    sp = clip_standoff(s, system) + s['wall_gap']
    R = size * 0.8 * MM
    lead = (max(SOCKET_LEN, socket_dims(size)[2] + 5.0) if det else SOCKET_LEN) * MM
    maxlen = s.get(pre + 'maxlen', 0.0) * MM
    o, i = pipe_rings(v)
    o, i = _mm_loop(o), _mm_loop(i)
    top_k = s.get('r_top', 'none')
    bot_k = s.get('r_bot', 'none')
    if top_k not in [k for _l, k in ROUTE_TOPS[system]]:
        top_k = 'none'
    if bot_k not in [k for _l, k in ROUTE_BOTS[system]]:
        bot_k = 'none'
    parts, notes, nruns, nowall = [], [], 0, 0
    navoid = 0
    nswan = 0
    swung = {}
    branches = []
    if system == 'soil':
        # a waste marked from the stack: a boss on the stack, the waste dog-legging into it
        chains, branches = _r_branches(chains)
    for pts, closed in chains:
        P = [tuple(p) for p in pts] + ([tuple(pts[0])] if closed else [])
        if len(P) < 2:
            continue
        if P[-1][2] > P[0][2] + 1e-6:
            P = list(reversed(P))                         # top first
        walls = [segment_wall(a, b, faces, flip=flip) for a, b in zip(P[:-1], P[1:])]
        zw_run = None                               # top of the wall the run is on
        if system == 'soil':
            try:
                w0 = next((w for w in reversed(walls) if w), None)
                zw_run = wall_top_at(P[-1], w0, faces) if w0 else None
            except Exception:
                zw_run = None
        if not any(walls):
            nowall += 1
        wall0 = next((w for w in walls if w), None) or s.get('_wall')   # the real wall the run was drawn on
        if wall0 is not None and system == 'soil' and '_stack_wall' not in s:
            s = dict(s, _stack_wall=wall0)
        Q = []
        for j in range(len(P)):
            cons = [(walls[k][0], sp * MM) for k in (j - 1, j) if 0 <= k < len(walls) and walls[k]]
            Q.append(v_add(P[j], _r_offset(cons)))
        did_swan = False
        # a stack marked straight down from the fascia: swan neck back to the wall under the eaves
        if system == 'soil' and s.get('r_swan', True):
            try:
                sw = _r_stack_swan(P, Q, walls, faces, s, sp, R, lead, top_k, size, all_faces)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print("%s: swan neck: %s" % (PLUGIN_NAME, e))
                sw = None
            if sw:
                if not any(walls):
                    nowall -= 1                     # it found the wall after all
                Q, walls, wall0 = sw
                did_swan = True
                s = dict(s, _stack_wall=wall0)
                nswan += 1
                swung[_r_key(P)] = wall0                # wastes into this stack go to the wall too
        # going down to the ground: step out round anything in the way (plinth, sill, lean-to)
        if s.get('r_avoid', True) and all_faces and len(Q) >= 2:
            try:
                wn = walls[-1] or next((w for w in reversed(walls) if w), None)
                if wn:
                    nn = v_norm((wn[0][0], wn[0][1], 0.0))
                    wb_ = wall_behind(Q[-2], Q[-1], nn, faces) or (nn, wn[1])
                    sa = dict(s, _ps_mm=sp, _size_mm=size, _top_straight=lead if len(Q) > 2 else 0.0,
                              _zcap=wall_top_at(Q[-1], wb_, faces))
                    newq, why = avoid_obstacles(Q, wb_[0], wb_[1], all_faces, sa)
                    if newq:
                        extra = len(newq) - len(Q)
                        Q = newq
                        # each new stretch is clipped to whatever it runs past, at the usual distance
                        nb = len(walls) - 1
                        walls = walls[:nb]
                        for a_, b_ in zip(Q[nb:-1], Q[nb + 1:]):
                            u_ = v_dot(wb_[0], a_) - wb_[1]
                            walls.append((wb_[0], wb_[1] + u_ - sp * MM))
                        navoid += 1
                        if system == 'soil' and top_k == 'vent':
                            Q, walls = _r_vent_out(Q, walls, wb_, sa.get('_zcap'))
                    elif why:
                        notes.append(why)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print("%s: stepping round things: %s" % (PLUGIN_NAME, e))
        # the stack ends at the bottom of what it comes down in front of (the plinth), where the
        # drain adaptor goes into the ground - not below it, where it was marked
        if did_swan and len(Q) >= 2 and walls and walls[-1]:
            try:
                a_, b_ = Q[-2], Q[-1]
                if math.hypot(a_[0] - b_[0], a_[1] - b_[1]) < 0.003 and a_[2] > b_[2]:
                    pn, pd = walls[-1]
                    pn = v_norm((pn[0], pn[1], 0.0))
                    plane = pd                                # the face the pipe runs down in front of
                    ax = (-pn[1], pn[0], 0.0)
                    x0_ = v_dot(ax, b_)
                    rr = size * 0.5 * MM
                    base = None
                    for f in faces:
                        if abs(v_dot(v_norm((f[0][0], f[0][1], 0.0)), pn)) < 0.94:
                            continue
                        if max(abs(v_dot(pn, p) - plane) for p in f[2]) > 0.006:
                            continue
                        C = _clip_slab([(v_dot(ax, p) - x0_, 0.0, p[2]) for p in f[2]], -rr, rr)
                        if C:
                            zb = min(c[2] for c in C)
                            base = zb if base is None else min(base, zb)
                    _dbg("stack bottom: marked", round(b_[2], 3), "face bottom", base)
                    if base is not None:
                        # a drain adaptor's spigot (150 mm into the drain) mustn't hang below it either
                        want = base + (0.150 if bot_k == 'drain' else 0.0)
                        if b_[2] < want - 0.005 and want < a_[2] - 0.1:
                            Q = Q[:-1] + [(b_[0], b_[1], want)]
                            _dbg("stack bottom: raised to", round(want, 3))
            except Exception as e:
                print("%s: stack bottom: %s" % (PLUGIN_NAME, e))
        # how far out the run hugs its wall (stepped round quoins or not); clips go on anything
        # near that, and are left off only where it stands right out (past the eaves)
        dhug = min((v_dot(wall0[0], q) - wall0[1]) / MM for q in Q) if wall0 is not None else 0.0
        pieces = split_lengths(route_pieces(Q, R, lead), maxlen)
        if not pieces:
            notes.append("a line was too short for a pipe")
            continue
        nruns += 1

        def wall_of(seg):
            if 0 <= seg < len(walls) and walls[seg]:
                return walls[seg]
            for w in walls:
                if w:
                    return w
            return None

        def up_of(seg, T):
            w = wall_of(seg)
            return route_up(T, v_mul(w[0], -1.0) if w else (NZ if system == 'waste' else None))
        clips, nclip = [], 0
        for idx, pc in enumerate(pieces):
            T0, T1 = piece_dirs(pc)
            up = up_of(pc[-1], T0)
            first, last = idx == 0, idx == len(pieces) - 1
            prev = pieces[idx - 1][0] if idx else None
            sock0 = det and ((pc[0] == 'bend') or (s.get('pipe_socket', True) and prev != 'bend'))
            if first and top_k == 'vent':
                sock0 = False                             # the cowl's sleeve goes over the plain end
            tags = {}
            st = 'in' if first and top_k == 'none' else None
            et = 'out' if last and bot_k == 'none' else None
            if st:
                tags['in'] = dict(end_port(pc[1][0], v_mul(T0, -1.0), up, 'in', system), sock=bool(sock0))
            if et:
                tags['out'] = dict(end_port(pc[1][-1], T1, up_of(pc[-1], T1), 'out', system),
                                   sock=bool(det and pc[0] == 'bend'))
            sol, _f = sweep_solid(pc[1], up, o, i, st, et)
            sols = [sol]
            if sock0:
                sols.append(collar_world(pc[1][0], T0, size))
            if det and pc[0] == 'bend':
                sols.append(collar_world(pc[1][-1], v_mul(T1, -1.0), size))
            if pc[0] == 'pipe':
                L = v_len(v_sub(pc[1][1], pc[1][0])) / MM
                parts.append(("%s length - %s x %g mm" % ("Soil pipe" if system == 'soil' else "Waste pipe",
                                                          sname, round(L)), sols, tags))
                w = wall_of(pc[2])
                if wall0 is not None and abs(v_dot(T0, wall0[0])) < 0.5 and \
                        (v_dot(wall0[0], pc[1][0]) - wall0[1]) / MM <= dhug + 100.0:
                    w = wall0                           # hugging the wall it was drawn on: clip to that
                _dbg(system, "piece seg", pc[2], "L", round(L), "z", round(pc[1][0][2], 3), round(pc[1][-1][2], 3),
                     "wall", w and (tuple(round(c, 3) for c in w[0]), round(w[1], 4)),
                     "Tn", w and round(v_dot(T0, w[0]), 3),
                     "reach", w and round((v_dot(w[0], pc[1][0]) - w[1]) / MM, 1),
                     "real", wall0 and round((v_dot(wall0[0], pc[1][0]) - wall0[1]) / MM, 1), "dhug", round(dhug, 1),
                     "fix", fixing_positions(L, s['s_spacing'] if system == 'soil' else s['w_spacing']))
                if not (s.get('auto_fix', True) and w and abs(v_dot(T0, w[0])) < 0.5):
                    ROUTE_STATS['clip_nowall'] = ROUTE_STATS.get('clip_nowall', 0) + 1
                if s.get('auto_fix', True) and w and abs(v_dot(T0, w[0])) < 0.5 and L >= 150.0:
                    reach = (v_dot(w[0], pc[1][0]) - w[1]) / MM
                    if reach <= size / 2:
                        ROUTE_STATS['clip_close'] = ROUTE_STATS.get('clip_close', 0) + 1
                    if reach > size / 2:
                        tgt = end_target(pc[1][-1], T0, route_up(T0, v_mul(w[0], -1.0)), 'out', system)
                        spacing = s['s_spacing'] if system == 'soil' else s['w_spacing']
                        for x in fixing_positions(L, spacing):
                            f_ = (x / L) if L else 0.0
                            pt = v_add(pc[1][0], v_mul(v_sub(pc[1][-1], pc[1][0]), f_))
                            if wall0 is not None and (v_dot(wall0[0], pt) - wall0[1]) / MM > dhug + 100.0:
                                ROUTE_STATS['clip_out'] = ROUTE_STATS.get('clip_out', 0) + 1
                                continue                    # stood right out (past the eaves): nothing to fix to
                            cw, _ = plan_part(pre + 'clip', dict(s, offset=L - x, bend_dir=0.0, reach=reach), tgt)
                            clips += cw
                            nclip += 1
            else:
                parts.append(("Bend %g deg - %s" % (round(pc[2], 1), sname), sols, tags))
        a0, T0 = pieces[0][1][0], piece_dirs(pieces[0])[0]
        b1, T1 = pieces[-1][1][-1], piece_dirs(pieces[-1])[1]
        if top_k != 'none':
            w, _ = plan_part(pre + top_k, s, end_target(a0, v_mul(T0, -1.0), up_of(pieces[0][-1], T0), 'in',
                                                        system, sock=False))
            parts.append(("%s - %s" % (PART_INFO[pre + top_k][0], sname), w, {}))
        if bot_k != 'none':
            w, _ = plan_part(pre + bot_k, s, end_target(b1, T1, up_of(pieces[-1][-1], T1), 'out', system))
            parts.append(("%s - %s" % (PART_INFO[pre + bot_k][0], sname), w, {}))
        if clips:
            parts.append(("Pipe clips x%d - %s" % (nclip, sname), clips, {}))
    nboss = 0
    for P, Q, k in branches:
        try:
            got = _r_boss_waste(P, Q, k, faces, s, sp, sname, flip, swung.get(_r_key(Q)))
        except Exception as e:
            import traceback
            traceback.print_exc()
            got = None
            notes.append("a waste into the stack could not be built (%s)" % e)
        if got:
            parts += got
            nboss += 1
        elif got is not None:
            notes.append("a waste was too short to reach the stack's boss")
    if nowall:
        notes.append("%d line%s had no wall face under it, so the pipe runs right on the line, "
                     "with no clips" % (nowall, "" if nowall == 1 else "s"))
    what = "%d %s run%s" % (nruns, SYSTEM_NAMES[system], "" if nruns == 1 else "s")
    ncl = sum(int(p_[0].split(' x', 1)[1].split(' ')[0]) for p_ in parts
              if p_[0].startswith("Pipe clips x") and p_[0].split(' x', 1)[1].split(' ')[0].isdigit())
    what += ", %d clip%s" % (ncl, "" if ncl == 1 else "s")
    if nswan:
        what += ", %d swan neck%s back to the wall" % (nswan, "" if nswan == 1 else "s")
    if navoid:
        what += ", %d stepped round something in the way" % navoid
    if nboss:
        what += ", %d waste%s into %s boss" % (nboss, "" if nboss == 1 else "s", "a" if nboss == 1 else "its")
    return parts, what, notes


def _r_key(P):
    """Which marked line a run came from (either way round)."""
    a, b = tuple(round(c, 5) for c in P[0]), tuple(round(c, 5) for c in P[-1])
    return (a, b) if a <= b else (b, a)


def _r_boss_waste(P, Q, k, faces, s, sp, sname, flip, stack_wall=None):
    """A boss on the stack where a marked waste starts on it, and the waste pipe from the far
    end along the wall on its own clips, dog-legging out into the boss outlet.
    P: the waste line from the stack end; Q, k: the stack line and the stretch it meets.
    Returns the parts, [] if the waste is too short, or None if it can't be placed."""
    E, F = P[0], P[-1]
    a, b = Q[k], Q[k + 1]
    t = (E[2] - a[2]) / (b[2] - a[2]) if abs(b[2] - a[2]) > 1e-9 else 0.0
    J = v_add(a, v_mul(v_sub(b, a), max(0.0, min(1.0, t))))
    if stack_wall:
        # the stack was marked out on the fascia and taken back to the wall (swan neck): the
        # boss and the waste go on the wall, not out where the lines were marked
        n_, d_ = stack_wall
        J = v_sub(J, v_mul(n_, v_dot(n_, J) - d_))
        F = v_sub(F, v_mul(n_, v_dot(n_, F) - d_))
        w = stack_wall
    else:
        w = segment_wall(a, b, faces, flip=flip)
    Jc = v_add(J, _r_offset([(w[0], sp * MM)])) if w else J
    Fh = (F[0], F[1], J[2])                               # the waste runs level
    D = v_norm((Fh[0] - J[0], Fh[1] - J[1], 0.0))
    if v_len(D) < 0.5:
        return None
    bw, btags = plan_part('s_boss', dict(s, offset=0.0, bend_dir=0.0), end_target(Jc, Z, D, 'out', 'soil'))
    out = [("Boss connector - %s" % sname, bw, {})]
    if 'boss' not in btags:
        return out
    B = tuple(btags['boss']['c'])                         # the boss outlet, where the waste goes in
    wsz = s['w_size']
    into = max(60.0, 1.5 * wsz) * MM                      # straight into the boss
    dog = max(120.0, 3.0 * wsz) * MM                      # the dog leg out from the wall
    reach = v_dot(v_sub(B, J), D)
    dist = v_dot(v_sub(Fh, J), D)
    if dist < reach + into + dog + 0.05:
        return []
    M = v_add(B, v_mul(D, into))
    K = v_add(Fh, v_mul(D, (reach + into + dog) - dist))
    s2 = dict(s, r_system='waste', r_top='none', r_bot='none', r_avoid=False)
    wn = w or s.get('_stack_wall')
    wsoff = clip_standoff(s, 'waste') + s['wall_gap']      # waste pipe middle to the wall (mm)
    if wn:
        s2['_wall'] = (wn[0], v_dot(wn[0], F))            # the wall the waste was drawn on (for its clips)
        # the waste stands off that wall on its clips; the dog leg takes it out to the boss
        off = v_mul(wn[0], wsoff * MM)
        Fh, K = v_add(Fh, off), v_add(K, off)
    end_k = s.get('w_end', 'none') if wn else 'none'
    into_wall = (wsoff + 40.0) * MM                       # how far a waste goes into the wall
    path = [Fh, K, M, B]
    if end_k == 'wall':
        path = [v_sub(Fh, v_mul(wn[0], into_wall))] + path   # bends and goes into the wall
    # the points are placed already, so no wall faces: the end has to land right in the boss
    wparts, _w, _n = build_soil_route([(path, False)], [], s2, None)
    out += wparts

    def tee_at(d, keep_end):
        """A tee on the waste, its branch at distance d from the stack going into the wall
        (another sink), the run carrying on past it. keep_end: leave its far end open."""
        C = v_add(Fh, v_mul(D, d - dist))                 # on the pipe's middle line
        st = dict(s, bend_dir=0.0, branch_len=max(10.0, wsoff + 40.0 - wsz / 2.0))
        _x, tg = plan_part('w_tee', st, end_target(C, D, v_mul(wn[0], -1.0), 'out', 'waste'))
        if 'branch' in tg:                                # slide it so the branch is right at d
            shift = v_dot(v_sub(C, tuple(tg['branch']['c'])), D)
            C = v_add(C, v_mul(D, shift))
        tw, tg = plan_part('w_tee', st, end_target(C, D, v_mul(wn[0], -1.0), 'out', 'waste'))
        tags = {'out': tg['out']} if keep_end and 'out' in tg else {}
        _dbg("waste tee at", round(d, 3), "branch", tg.get('branch', {}).get('c'), "out", tg.get('out', {}).get('c'))
        return ("Tee (90 deg) - %s x %g mm" % ("Waste", wsz), tw, tags)

    if wn:
        # a corner clicked along the waste (level, along the wall) is another sink: a tee there
        for S in P[1:-1]:
            Sw = v_sub(S, v_mul(wn[0], v_dot(wn[0], S) - v_dot(wn[0], J))) if stack_wall else S
            dS = v_dot(v_sub((Sw[0], Sw[1], J[2]), J), D)
            if reach + into + dog + 0.08 < dS < dist - 0.06:
                out.append(tee_at(dS, False))
        if end_k == 'tee':
            out.append(tee_at(dist, True))
    return out


# ---------------------------------------------------------------------------
# Live preview of the chosen part
# ---------------------------------------------------------------------------
VIEW_DIR = v_norm((-0.55, 0.8, -0.5))          # looking from the front right, above
LIGHT = v_norm((0.35, -0.55, 0.8))



def _soften_pipe_edges(mesh, made_faces, max_angle=30.0):
    """Softens (hides and smooths) the edges between faces that meet at less than max_angle
    degrees - round the pipes and along the bends - so a pipe looks smooth and shows its
    real colour from a distance (all its lines made it look black). Sharp edges stay.
    made_faces: [(face, normal)] as they were added. (As 3D Blend does it.)"""
    def items(x):
        if x is None:
            return []
        if isinstance(x, dict):
            return list(x.values())
        try:
            return list(x)
        except Exception:
            return []

    def val(o, name):
        x = getattr(o, name, None)
        if callable(x):
            try:
                x = x()
            except Exception:
                return None
        return x

    def xyz(p):
        if p is None:
            return None
        try:
            if callable(getattr(p, 'x', None)):
                return (float(p.x()), float(p.y()), float(p.z()))
            if hasattr(p, 'x'):
                return (float(p.x), float(p.y), float(p.z))
            return (float(p[0]), float(p[1]), float(p[2]))
        except Exception:
            return None

    normals = {}

    def normal_of(f):
        k = id(f)
        if k not in normals:
            nrm = None
            pts = [xyz(v) for v in items(val(f, 'vertices'))]
            pts = [q for q in pts if q is not None]
            if len(pts) >= 3:
                nrm = v_norm(_newell(pts))
            if nrm is None or v_len(nrm) < 0.5:
                nrm = xyz(val(f, 'normal'))
                nrm = v_norm(nrm) if nrm else None
            normals[k] = nrm
        return normals[k]

    # IngeTrazo's edges know their faces and have a 'soft' setting (like SketchUp's)
    cos_lim = math.cos(math.radians(max_angle))
    soft = 0
    for e in items(val(mesh, 'edges')):
        fs = items(val(e, 'faces'))
        if len(fs) != 2:
            continue
        n1, n2 = normal_of(fs[0]), normal_of(fs[1])
        if n1 is None or n2 is None:
            continue
        if v_dot(n1, n2) >= cos_lim:
            try:
                e.soft = True
                soft += 1
            except Exception:
                pass
    return soft


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
 '@cb_preset': 'Ready-made settings. Pick one and the whole window is filled in.',
 'Add part': 'Builds the part picked on the Part page, joined onto the open end (or at the origin, or on '
             'the wall you picked).',
 'Direction': 'Which way the bend, branch, boss, access door or clip faces.',
 'The lines are': 'Whether the lines you selected are soil pipe or waste pipe runs.'}
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



class SoilKey(QWidget):
    """What each lettered size is: the pipes end on, and a stack and a waste on a wall."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 415)       # drawn to scale, so it fits whatever size

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont
        from PySide6.QtCore import QPointF, QRectF, Qt
        import math as _m
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 246))
        k = min(float(self.width()) / 360.0, self.height() / 680.0)
        p.scale(k, k)
        red = QColor(200, 40, 40)
        soil, waste = QColor(70, 74, 80), QColor(200, 204, 210)
        wallc, brick = QColor(200, 196, 188), QColor(178, 90, 60)
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

        def ring(cx, cy, r, t, col):
            p.setPen(QPen(col.darker(150), 0.8))
            p.setBrush(col)
            p.drawEllipse(QPointF(cx, cy), r, r)
            p.setBrush(QColor(250, 250, 246))
            p.drawEllipse(QPointF(cx, cy), r - t, r - t)

        # ---- the pipes end on
        title(10, 4, "Soil pipe end on")
        ring(80, 70, 40, 6, soil)
        dim(40, 122, 120, 122, "A", 80, 134)
        dim(114, 70, 120, 70, "B", 132, 62)
        title(200, 4, "Waste pipe end on")
        ring(270, 70, 18, 4, waste)
        dim(252, 100, 288, 100, "C", 270, 112)
        dim(284, 70, 288, 70, "D", 300, 62)

        # ---- a wall from the front: a soil stack and a waste coming out into a gully
        title(10, 150, "On a wall, from the front")
        WX0, WX1, WY0, WY1 = 40.0, 320.0, 200.0, 400.0
        box(WX0, WY0, WX1 - WX0, WY1 - WY0, wallc)
        for i in range(10):
            p.setPen(QPen(brick, 0.5))
            p.drawLine(QPointF(WX0, WY0 + 18 + i * 19), QPointF(WX1, WY0 + 18 + i * 19))
        p.setPen(QPen(QColor(90, 70, 50), 1.2))
        p.drawLine(QPointF(10, WY1), QPointF(350, WY1))                 # ground
        sx = 130.0
        box(sx - 9, WY0 + 18, 18, WY1 - WY0 + 12, soil)                   # the stack
        box(sx - 12, WY0 + 6, 24, 12, QColor(110, 115, 122))              # vent cowl
        for cy_ in (WY0 + 60, WY0 + 140):
            box(sx - 13, cy_, 26, 5, QColor(30, 30, 30))                  # clips
        dim(WX0, WY0 - 12, sx, WY0 - 12, "G", (WX0 + sx) / 2, WY0 - 24)
        dim(sx + 22, WY0, sx + 22, WY0 + 18, "H", sx + 34, WY0 + 9)
        dim(sx + 22, WY1, sx + 22, WY1 + 30, "L", sx + 34, WY1 + 15)
        dim(sx - 26, WY0 + 62, sx - 26, WY0 + 142, "Q", sx - 38, WY0 + 102)
        wy = WY1 - 90.0
        box(230, wy - 4, 60, 8, waste)                                    # waste out of the wall
        box(286, wy - 4, 8, 78, waste)                                    # down to the gully
        box(276, WY1 - 10, 28, 10, QColor(90, 90, 90))                    # gully
        for cy_ in (wy + 20, wy + 50):
            box(283, cy_, 14, 3, QColor(30, 30, 30))
        dim(220, wy, 220, WY1, "M", 208, (wy + WY1) / 2)
        dim(306, wy + 21, 306, wy + 51, "R", 318, wy + 36)

        # ---- from above: how far out from the wall
        title(10, 440, "From above")
        box(40, 462, 120, 14, wallc)
        ring(100, 476 + 20 + 12, 12, 3, soil)
        box(97, 476, 6, 20, QColor(30, 30, 30))
        dim(70, 476, 70, 496, "N", 58, 486)

        f2 = QFont()
        f2.setPointSizeF(8.5)
        p.setFont(f2)
        p.setPen(QColor(60, 60, 60))
        notes = ["A  soil pipe diameter", "B  soil pipe wall", "C  waste pipe diameter", "D  waste pipe wall",
                 "F  length of a pipe", "G  along the wall", "H  stack top below wall top",
                 "J  branch length", "K  distance back from the end", "L  stack below the wall",
                 "M  waste height on the wall", "N  extra gap from the wall", "Q  soil clips at most",
                 "R  waste clips at most", "S  swan neck offset", "T  bend turn angle",
                 "U  longest soil length", "V  longest waste length"]
        for i, t_ in enumerate(notes):
            p.drawText(QRectF(185 if i >= 9 else 10, 520 + (i % 9) * 15.5, 175, 14),
                       Qt.AlignLeft | Qt.AlignVCenter, t_)
        p.end()


UI_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_soil_waste.json")


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


INFO_TEXT = ("<b>Mark the run (easy to see)</b><br>"
             "On the Follow lines page click 'Mark the run' and click the corners of each run: a thick, "
             "bright line you can see on a detailed building (set its thickness and colour there). Arrow keys "
             "lock it to an axis (Right = red, Left = green, Up = blue, Down = free). Esc or right-click ends a "
             "line; again when you've finished marking. It snaps to the ends of your marked lines and onto "
             "them. Then 'Build along lines' - everything goes into one group, and pipes going down to the "
             "ground step out round a plinth, a sill or a lean-to.<br><br>"
             "<b>Soil stack like a downpipe</b><br>"
             "Mark the stack from the fascia (or the gutter) straight down to the ground - one line. "
             "The vent stays out above the eaves, two 45 degree bends take it back to the wall under the "
             "eaves, it runs down the wall on its clips and steps out round the plinth at the bottom. "
             "For a sink waste into it, mark the waste from the stack line (it snaps on) level along "
             "the wall: it gets a boss on the stack and dog-legs into it.<br><br>"
             "<b>Follow lines (the quick way)</b><br>"
             "Draw a line where each pipe run goes, corner to corner - down the wall for a soil stack, or out "
             "of the wall and down for a waste. Select the lines, go to the Follow lines page, pick soil or "
             "waste and what goes on each end, and click 'Build along selected lines'. You get bends wherever "
             "the line turns, socket collars, clips to the wall, and the vent, gully or drain on the ends. "
             "Lines drawn on a wall stand the pipe off it on its clips; lines in mid-air are the middle of "
             "the pipe.<br><br>"
             "<b>One part at a time</b><br>"
             "Pick a part on the Part page and click 'Add part'. The first one goes at the origin - or select "
             "a wall face, click 'Use selected wall' (On a wall page): a soil part starts a stack down the wall "
             "and a waste part comes out of it. Each part joins onto the open end of the last one; select the "
             "open end of any part you placed and click 'Use selected end' to carry on from there.<br><br>"
             "<b>Sizes</b><br>The pipe sizes are on the Pipes page; the letters are on the Key page. Click a "
             "part in the model and the settings that made it light up.<br><br>"
             "<b>Printing</b><br>Tick 'Solid' and 'Chunky fittings' for small scales. Sizes are real-world mm "
             "- Scale Studio takes it down to your model scale.")

# which settings make each part, found from its group name when you click it in the model
PIECE_KEYS = [("Pipe clips", ('s_spacing', 'w_spacing')), ("Soil pipe length", ('length', 's_size', 's_wall')),
              ("Waste pipe length", ('length', 'w_size', 'w_wall')), ("Swan neck", ('bend_turn', 'swan_len')),
              ("Double branch", ('bend_turn', 'branch_len')), ("Branch", ('bend_turn', 'branch_len')),
              ("Tee", ('branch_len',)), ("Bend", ('bend_turn',)), ("Rest bend", ('s_size',)),
              ("Socket", ('offset',)), ("Pipe clip", ('offset',)), ("Boss connector", ('offset',)),
              ("Boss adaptor", ('offset',)), ("Boss pipe", ('s_size', 'w_size')),
              ("Access pipe", ('s_size',)), ("Vent cowl", ('s_size',)), ("Drain adaptor", ('s_size',)),
              ("Hopper head", ('w_size',)), ("Shoe", ('w_size',)), ("Gully", ('w_size',)),
              ("Back-inlet gully", ('w_size',))]


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
        name = "Soil & Waste Pipes - mark the run"
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
class SoilWasteDialog(QDialog):
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
        self.wall = None           # a picked wall the next run starts on
        self.wall_face = None
        self.wall_dir = None       # which way the wall is, for pointing clips at it
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
        cap = QLabel("Brown panel = the wall. Pale grey = the pipe it fits over.")
        cap.setStyleSheet("color: gray; font-size: 9pt;")
        pvl.addWidget(cap)
        self.left.addTab(pv, "Preview")
        ks = QScrollArea()
        ks.setWidgetResizable(True)
        ks.setWidget(SoilKey())
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
        sf.addRow(self.lst)
        self.sp = {
            'length': mm_spin(cur['length'], 1.0),
            'bend_turn': mm_spin(cur['bend_turn'], 1.0, 135.0, " deg"),
            'branch_len': mm_spin(cur['branch_len'], 10.0),
            'offset': mm_spin(cur['offset'], 0.0),
            'swan_len': mm_spin(cur['swan_len'], 0.0),
        }
        tips = {'length': "How long the pipe length is.",
                'bend_turn': "How far the pipe turns. A 92.5 deg bend or branch turns 87.5; a 112.5 deg turns "
                             "67.5; a 135 deg turns 45; a 90 deg turns 90.",
                'branch_len': "How long the branch arm is.",
                'offset': "0 = centred on the end you selected. Larger values slide it back along the pipe.",
                'swan_len': "Length of the straight between the two bends of a swan neck."}
        labels = {'length': "F   Length", 'bend_turn': "T   Turn angle", 'branch_len': "J   Branch length",
                  'offset': "K   Distance back from the end", 'swan_len': "S   Swan neck offset"}
        self.rows = {}
        for k in ('length', 'bend_turn', 'branch_len', 'offset', 'swan_len'):
            lab = add_row(sf, k, labels[k], self.sp[k], tips[k])
            self.rows[k] = (lab, self.sp[k])
        self.cb_dir = QComboBox()
        for label, deg in BEND_DIRS:
            self.cb_dir.addItem(label, deg)
            if abs(deg - cur['bend_dir']) < 1e-6:
                self.cb_dir.setCurrentIndex(self.cb_dir.count() - 1)
        self.cb_dir.setToolTip("Which way the bend, branch, boss, access door or clip faces. "
                               "On a pipe coming out of a wall 'Down' bends it down; on an upright "
                               "pipe it turns towards the wall.")
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
        self.cb_solid.setToolTip("Fills the pipes in, so small-scale prints come out strong. "
                                 "Fit-over parts (sockets, clips, bosses) stay as sleeves.")
        sf.addRow(self.cb_solid)

        # Pipes page: the sizes
        page = QWidget()
        pf = QFormLayout(page)
        self.tabs.addTab(page, "Pipes")
        self.sp_ss = mm_spin(cur['s_size'], 20.0)
        self.sp_st = mm_spin(cur['s_wall'], 0.5, 50.0)
        self.sp_ws = mm_spin(cur['w_size'], 10.0)
        self.sp_wt = mm_spin(cur['w_wall'], 0.5, 50.0)
        add_row(pf, 's_size', "A   Soil pipe diameter", self.sp_ss,
                "Outside diameter of the soil pipe: 110 mm is standard, 82 mm is also used.")
        add_row(pf, 's_wall', "B   Soil pipe wall", self.sp_st, "How thick the soil pipe's wall is.")
        add_row(pf, 'w_size', "C   Waste pipe diameter", self.sp_ws,
                "Outside diameter of the waste pipe: 32 mm for basins, 40 mm for sinks and baths, "
                "50 mm for longer runs.")
        add_row(pf, 'w_wall', "D   Waste pipe wall", self.sp_wt, "How thick the waste pipe's wall is.")

        # Fittings page: how much detail
        page = QWidget()
        df = QFormLayout(page)
        self.tabs.addTab(page, "Fittings")
        self.cb_detail = QCheckBox("Detailed fittings (socket collars, rodding eye, bosses)")
        self.cb_detail.setChecked(bool(cur.get('detail', True)))
        self.cb_detail.setToolTip("Gives fittings thick socket collars at their ends, a round rodding "
                                  "eye with cap and bolts on access pipes, collars on boss outlets, "
                                  "hinged clips with bolt lugs and a cage vent cowl.")
        df.addRow(self.cb_detail)
        self.cb_psock = QCheckBox("Pipe lengths have a socket on the start (top) end")
        self.cb_psock.setChecked(bool(cur.get('pipe_socket', True)))
        self.cb_psock.setToolTip("Like real soil and waste pipe: one plain end and one socket end. "
                                 "A pipe that joins onto a bend, branch, boss or coupler goes in "
                                 "plain-ended, as that fitting has the socket. "
                                 "Only used with Detailed fittings.")
        self.cb_detail.toggled.connect(self.cb_psock.setEnabled)
        self.cb_psock.setEnabled(self.cb_detail.isChecked())
        df.addRow(self.cb_psock)
        self.cb_ears = QCheckBox("Cast-iron style ears on pipe sockets (instead of clips)")
        self.cb_ears.setChecked(bool(cur.get('ears', False)))
        self.cb_ears.setToolTip("Puts two fixing lugs on each pipe length's socket, facing the wall, "
                                "like Victorian cast-iron pipe. Pipe clips are then left off. "
                                "(Not used by Follow lines, which always uses clips.)")
        self.cb_psock.toggled.connect(self.cb_ears.setEnabled)
        self.cb_ears.setEnabled(self.cb_psock.isChecked() and self.cb_detail.isChecked())
        df.addRow(self.cb_ears)

        # On a wall page
        page = QWidget()
        wf = QFormLayout(page)
        self.tabs.addTab(page, "On a wall")
        wi = QLabel("Start a run on a wall: select a wall face, then click 'Use selected wall'. A soil part "
                    "starts a stack down the wall; a waste part comes straight out of it.")
        wi.setWordWrap(True)
        wf.addRow(wi)
        b_wall = QPushButton("Use selected wall")
        b_wall.setToolTip("Select a wall face, then click this. A soil part starts a stack down the "
                          "wall; a waste part comes straight out of the wall.")
        b_wall.clicked.connect(self.use_selected_wall)
        wf.addRow(b_wall)
        self.sp_along = mm_spin(cur['along'], 0.0)
        self.sp_drop = mm_spin(cur['drop'], -100000.0)
        self.sp_below = mm_spin(cur['below'], -100000.0)
        self.sp_wh = mm_spin(cur['w_height'], 0.0)
        self.sp_wgap = mm_spin(cur['wall_gap'], 0.0)
        add_row(wf, 'along', "G   Along the wall", self.sp_along,
                "Distance from the left end of the wall, as you look at it from outside.")
        add_row(wf, 'drop', "H   Stack top below wall top", self.sp_drop,
                "Soil stack: how far its top sits below the top of the wall. "
                "Negative takes it above the wall, e.g. to vent above the eaves.")
        add_row(wf, 'below', "L   Stack below the wall", self.sp_below,
                "Soil stack: how far it carries on below the bottom of the wall "
                "(into the ground). Negative stops short.")
        add_row(wf, 'w_height', "M   Waste height on the wall", self.sp_wh,
                "Waste pipe: height above the bottom of the wall where it comes out.")
        add_row(wf, 'wall_gap', "N   Extra gap from the wall", self.sp_wgap,
                "0 = clips sit flat on the wall. More moves the pipe out. Follow lines uses it too.")
        self.cb_fit = QCheckBox("Soil pipe length = wall height")
        self.cb_fit.setChecked(cur['fit_wall'])
        self.cb_flip = QCheckBox("Wrong side? Put it on the other side of the wall")
        self.cb_flip.setChecked(cur['wall_flip'])
        self.cb_flip.toggled.connect(self.reread_wall)
        wf.addRow(self.cb_fit)
        wf.addRow(self.cb_flip)

        # Clips page
        page = QWidget()
        ff = QFormLayout(page)
        self.tabs.addTab(page, "Clips")
        self.cb_fix = QCheckBox("Add them evenly with every pipe length")
        self.cb_fix.setChecked(cur['auto_fix'])
        ff.addRow(self.cb_fix)
        self.sp_ssp = mm_spin(cur['s_spacing'], 100.0)
        self.sp_wsp = mm_spin(cur['w_spacing'], 100.0)
        add_row(ff, 's_spacing', "Q   Soil clips at most", self.sp_ssp,
                "Most a soil pipe clip can be from the next one. One also goes near each end.")
        add_row(ff, 'w_spacing', "R   Waste clips at most", self.sp_wsp,
                "Most a waste pipe clip can be from the next one. One also goes near each end.")
        self.cb_chunky = QCheckBox("Chunky fittings (for 3D printing)")
        self.cb_chunky.setChecked(cur['chunky'])
        self.cb_chunky.setToolTip("Makes every clip, socket, boss and vent thicker with no gap to the "
                                  "pipe, so they survive printing at small scales.")
        ff.addRow(self.cb_chunky)
        self.sp_chunk = mm_spin(cur['chunk_mult'], 1.0, 10.0, " x", 1)
        add_row(ff, 'chunk_mult', "Thicker by", self.sp_chunk, "How many times thicker than real fittings.")
        self.cb_chunky.toggled.connect(self.sp_chunk.setEnabled)
        self.sp_chunk.setEnabled(self.cb_chunky.isChecked())
        self.cb_fix.toggled.connect(lambda on: (self.sp_ssp.setEnabled(on), self.sp_wsp.setEnabled(on)))
        self.sp_ssp.setEnabled(self.cb_fix.isChecked())
        self.sp_wsp.setEnabled(self.cb_fix.isChecked())

        # Follow lines page: build a run along lines you've drawn
        page = QWidget()
        rf = QFormLayout(page)
        self.tabs.addTab(page, "Follow lines")
        ri = QLabel("Draw a line where each run goes, corner to corner (down the wall for a stack; out of "
                    "the wall and down for a waste). Select the lines (you can select the wall faces too), "
                    "set what's on the ends and click the button.")
        ri.setWordWrap(True)
        rf.addRow(ri)
        b_route = QPushButton("Build along lines")
        b_route.setToolTip("Builds a pipe run along each marked run (or each selected line if nothing is "
                           "marked), with bends where it turns, socket collars, clips and the end fittings. "
                           "One undo takes it all away again.")
        b_route.clicked.connect(lambda: self.tool.build_route(self))
        rf.addRow(b_route)
        self.cb_rsys = QComboBox()
        for label, key in ROUTE_SYSTEMS:
            self.cb_rsys.addItem(label, key)
            if key == cur.get('r_system', 'soil'):
                self.cb_rsys.setCurrentIndex(self.cb_rsys.count() - 1)
        rf.addRow("The lines are", self.cb_rsys)
        self.cb_rtop = QComboBox()
        self.cb_rbot = QComboBox()
        self.cb_rtop.setToolTip("What goes on the top end of each run.")
        self.cb_rbot.setToolTip("What goes on the bottom end of each run.")
        rf.addRow("Top end", self.cb_rtop)
        rf.addRow("Bottom end", self.cb_rbot)
        self._route_ends(cur.get('r_top', 'vent'), cur.get('r_bot', 'drain'))
        self.cb_rsys.currentIndexChanged.connect(lambda *_: self._route_ends())
        self.sp_smax = mm_spin(cur['s_maxlen'], 0.0)
        self.sp_wmax = mm_spin(cur['w_maxlen'], 0.0)
        add_row(rf, 's_maxlen', "U   Longest soil length", self.sp_smax,
                "Longer stretches of soil pipe are cut into lengths no longer than this, each with its "
                "socket. 0 = one length per stretch.")
        add_row(rf, 'w_maxlen', "V   Longest waste length", self.sp_wmax,
                "The same for waste pipe.")
        self.cb_rflip = QCheckBox("Wrong side? Put it on the other side of the wall")
        self.cb_rflip.setChecked(bool(cur.get('r_flip', False)))
        self.cb_rflip.setToolTip("The wall a line is drawn on is found from the model. If the pipes come "
                                 "out inside the wall, tick this.")
        rf.addRow(self.cb_rflip)
        self.cb_ravoid = QCheckBox("Step out round anything in the way (plinth, sill, lean-to...)")
        self.cb_ravoid.setChecked(bool(cur.get('r_avoid', True)))
        self.cb_ravoid.setToolTip("On the way down to the ground, the pipe steps out (bends) over anything "
                                  "that sticks out in its way, and back in below it where there's wall.")
        rf.addRow(self.cb_ravoid)
        self.cb_rswan = QCheckBox("Stack marked from the fascia: swan neck back to the wall under the eaves")
        self.cb_rswan.setChecked(bool(cur.get('r_swan', True)))
        self.cb_rswan.setToolTip("Mark a soil stack from the fascia (or the gutter) straight down to the "
                                 "ground, like a downpipe: the vent stays out above the eaves, two 45 degree "
                                 "bends take it back to the wall, and it runs down the wall on its clips.")
        rf.addRow(self.cb_rswan)
        self.sp_vabove = mm_spin(cur.get('vent_above', 150.0), 0.0)
        self.sp_vabove.setToolTip("How far the vent goes up above the top of the gutter and roof edge, "
                                  "on a stack marked from the fascia. Mark the top higher if you want it taller.")
        rf.addRow("Vent above the eaves", self.sp_vabove)
        self.cb_wend = QComboBox()
        for label, key in W_ENDS:
            self.cb_wend.addItem(label, key)
            if key == cur.get('w_end', 'none'):
                self.cb_wend.setCurrentIndex(self.cb_wend.count() - 1)
        self.cb_wend.setToolTip("What goes on the far end of a waste marked into the stack (it gets a boss "
                                "on the stack). Each corner you click along the waste on the way gets a tee "
                                "into the wall too - one for each sink.")
        rf.addRow("End of a waste into the stack", self.cb_wend)
        rn = QLabel("Lines drawn on a wall stand the pipe off it on its clips (plus N). Lines in mid-air "
                    "are the middle of the pipe. Uses the sizes, Fittings and Clips pages too.")
        rn.setWordWrap(True)
        rn.setStyleSheet("color: gray;")
        rf.addRow(rn)

        # Mark the run: the plugin's own thick line, easy to see on a detailed building
        gm = QGroupBox("Mark the run (thick line, easy to see)")
        gml = QFormLayout(gm)
        mi = QLabel("Instead of drawing thin lines: click 'Mark the run', then click where each run goes, "
                    "corner to corner - down the wall for a soil stack, out of the wall and down for a "
                    "waste (snapping works as usual). The window hides while you mark and comes back when you've finished. Arrow keys lock the line to an axis: Right = red, Left = green, Up = blue (up and "
                    "down the wall), Down = free again. Esc or right-click (or Enter / double-click) ends the line you're "
                    "on - then click to start the next one; it snaps to the ends of your marked lines and "
                    "onto them, so a waste can start right on a stack. Backspace takes the last point "
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
        self.cb_rgroup.setToolTip("Ticked, the pipes and all their fittings from one build go "
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
        b_lines = QPushButton("Build along lines")
        b_close = QPushButton("Close")
        b_sel.setToolTip("Select the open end face of any placed part, then click this to join onto it.")
        b_new.setToolTip("The next part starts a new run at the origin.")
        b_lines.setToolTip("Builds pipe runs along your marked runs, or along lines you've drawn and "
                           "selected (settings on the Follow lines page).")
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
        b_lines.clicked.connect(lambda: self.tool.build_route(self))
        b_close.clicked.connect(self.close)
        self.set_target(target)

        self.refresh_presets(select=st.get('last_preset'))
        self.cb_preset.currentIndexChanged.connect(self.apply_preset)
        self.lst.currentItemChanged.connect(self.sync)
        for c in (self.cb_solid, self.cb_chunky, self.cb_detail, self.cb_psock, self.cb_ears, self.cb_fit,
                  self.cb_flip, self.cb_fix, self.cb_rflip):
            c.toggled.connect(self.sync)
        for c in (self.cb_wall, self.cb_dir, self.cb_rsys, self.cb_rtop, self.cb_rbot):
            c.currentIndexChanged.connect(self.sync)
        for w in [self.sp_ss, self.sp_st, self.sp_ws, self.sp_wt, self.sp_chunk, self.sp_along, self.sp_drop,
                  self.sp_below, self.sp_wh, self.sp_wgap, self.sp_ssp, self.sp_wsp, self.sp_smax,
                  self.sp_wmax] + list(self.sp.values()):
            w.valueChanged.connect(self.sync)
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

    def _route_ends(self, top=None, bot=None):
        """Fills the end choices for soil or waste, keeping what was picked where it can."""
        system = self.cb_rsys.currentData() or 'soil'
        for combo, opts, want in ((self.cb_rtop, ROUTE_TOPS[system], top), (self.cb_rbot, ROUTE_BOTS[system], bot)):
            keep = want if want is not None else combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            for label, key in opts:
                combo.addItem(label, key)
            idx = 0
            for i in range(combo.count()):
                if combo.itemData(i) == keep:
                    idx = i
            if keep not in [k for _l, k in opts] and len(opts) > 1:
                idx = 1                                # a new system: its usual end fitting
            combo.setCurrentIndex(idx)
            combo.blockSignals(False)

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
                if nm.startswith(word):
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
        return k or 's_pipe'

    def sync(self, *_):
        part = self.part()
        uses = PART_INFO[part][2]
        for k, (lab, w) in self.rows.items():
            on = k in uses
            lab.setVisible(on)
            w.setVisible(on)
        try:
            _ui_settings_save(last_values=self.values())       # opens like this next time
        except Exception:
            pass
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
        """The marked runs, each one on its own (each is a pipe run). A run ending where it
        started is a loop."""
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
             's_size': self.sp_ss.value(), 's_wall': self.sp_st.value(),
             'w_size': self.sp_ws.value(), 'w_wall': self.sp_wt.value(),
             'along': self.sp_along.value(), 'drop': self.sp_drop.value(),
             'below': self.sp_below.value(), 'w_height': self.sp_wh.value(),
             'wall_gap': self.sp_wgap.value(), 'fit_wall': self.cb_fit.isChecked(),
             'wall_flip': self.cb_flip.isChecked(), 'auto_fix': self.cb_fix.isChecked(),
             's_spacing': self.sp_ssp.value(), 'w_spacing': self.sp_wsp.value(),
             'chunky': self.cb_chunky.isChecked(), 'chunk_mult': self.sp_chunk.value(),
             'bend_dir': self.cb_dir.currentData(), 'detail': self.cb_detail.isChecked(),
             'pipe_socket': self.cb_psock.isChecked(), 'ears': self.cb_ears.isChecked(),
             'r_system': self.cb_rsys.currentData(), 'r_top': self.cb_rtop.currentData(),
             'r_bot': self.cb_rbot.currentData(), 's_maxlen': self.sp_smax.value(),
             'w_maxlen': self.sp_wmax.value(), 'r_flip': self.cb_rflip.isChecked(),
             'r_avoid': self.cb_ravoid.isChecked(), 'r_swan': self.cb_rswan.isChecked(),
             'vent_above': self.sp_vabove.value(), 'w_end': self.cb_wend.currentData()}
        for k, w in self.sp.items():
            v[k] = w.value()
        return v

    def set_values(self, d):
        for c, key in ((self.cb_solid, 'solid'), (self.cb_chunky, 'chunky'), (self.cb_detail, 'detail'),
                       (self.cb_psock, 'pipe_socket'), (self.cb_ears, 'ears'), (self.cb_fit, 'fit_wall'),
                       (self.cb_fix, 'auto_fix'), (self.cb_rflip, 'r_flip'), (self.cb_ravoid, 'r_avoid'),
                       (self.cb_rswan, 'r_swan')):
            if key in d:
                c.setChecked(bool(d[key]))
        for w, key in ((self.sp_ss, 's_size'), (self.sp_st, 's_wall'), (self.sp_ws, 'w_size'),
                       (self.sp_wt, 'w_wall'), (self.sp_along, 'along'), (self.sp_drop, 'drop'),
                       (self.sp_below, 'below'), (self.sp_wh, 'w_height'), (self.sp_wgap, 'wall_gap'),
                       (self.sp_ssp, 's_spacing'), (self.sp_wsp, 'w_spacing'),
                       (self.sp_chunk, 'chunk_mult'), (self.sp_smax, 's_maxlen'), (self.sp_wmax, 'w_maxlen'),
                       (self.sp_vabove, 'vent_above')):
            if d.get(key) is not None:
                w.setValue(float(d[key]))
        if d.get('w_end') is not None:
            i = self.cb_wend.findData(d['w_end'])
            if i >= 0:
                self.cb_wend.setCurrentIndex(i)
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
        last = _ui_settings().get('last_values')
        if isinstance(last, dict):
            cur.update({k: last[k] for k in DEFAULTS if k in last and k != 'units'})
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
        if not _ui_settings().get('compact_v3'):
            # the window remembers its old (bigger) size: shrink it once to the new smaller size
            try:
                dlg.adjustSize()
            except Exception:
                pass
            _ui_settings_save(compact_v3=True)
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

    def build_route(self, dlg):
        """Builds soil or waste pipe runs along the marked runs, or the lines you've selected."""
        viewport = dlg.viewport
        vals = dlg.values()
        SoilWastePipesTool._saved = dict(vals)
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
                                    "Draw a line corner to corner where each pipe run goes - down the wall "
                                    "for a soil stack, out of the wall and down for a waste.")
            return
        ROUTE_STATS['limit'] = False
        for k_ in ('clip_out', 'clip_nowall', 'clip_close'):
            ROUTE_STATS[k_] = 0
        del DEBUG_LOG[:]
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
            parts, what, notes = build_soil_route(chains, faces, vals, all_faces if vals.get('r_avoid', True) else None)
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.warning(dlg, PLUGIN_NAME, "Could not build along the lines:\n%s" % e)
            return
        try:                                   # what it found, for sorting out problems
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ed3d_soil_debug.txt"),
                      "w", encoding="utf-8") as fh:
                fh.write("version %s\n%s\n%s\n" % (VERSION, what if parts else "nothing built",
                                                    "\n".join(DEBUG_LOG)))
        except Exception:
            pass
        if not parts:
            QMessageBox.information(dlg, PLUGIN_NAME, "Nothing could be built along those lines.\n\n" +
                                    "\n".join(notes))
            return
        holder = None
        try:
            if dlg.cb_rgroup.isChecked() and len(parts) > 1:
                # "one piece" in the name: Scale Studio puts the lot on the print bed as one piece
                holder = "%s (one piece) - %s" % ("Soil pipes" if vals.get('r_system') == 'soil' else "Waste pipes",
                                                  what)
        except Exception:
            pass
        if not self.add_to_scene(viewport, vals, None, parts, holder=holder):
            return
        if marked:
            dlg.clear_marks()          # built now - the marks have done their job
        dlg.set_target(None)
        txt = "Built %s along your %s." % (what, "marked runs" if marked else "lines")
        if notes:
            txt += " Note: " + "; ".join(notes) + "."
        dlg.lbl_target.setText(txt)

    def add_to_scene(self, viewport, vals, target, parts, holder=None):
        """parts: list of (group name, world solids, port tags). One undo step for all.
        holder: a name to put all the parts into one group of that name (each part stays a group)."""
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
            made = []
            to_soften = []
            for name, world, tags in parts:
                mesh = Mesh()
                soft_faces = []
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
                            try:
                                soft_faces.append((f, v_norm(_newell(pts))))
                            except Exception:
                                pass
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
                to_soften.append((mesh, soft_faces))
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
            soft_log = []
            for mesh, soft_faces in to_soften:
                for fn_ in ('recompute_normals', 'update_normals', 'rebuild', 'invalidate'):
                    m_ = getattr(mesh, fn_, None)
                    if callable(m_):
                        try:
                            m_()
                        except Exception:
                            pass
                try:
                    soft_log.append(_soften_pipe_edges(mesh, soft_faces))
                except Exception as e:
                    soft_log.append("error %s" % e)
            try:                                   # what happened, for sorting out problems
                m0 = to_soften[0][0] if to_soften else None
                info = {'mesh': type(m0).__name__, 'find_edge': callable(getattr(m0, 'find_edge', None)),
                        'edges': type(getattr(m0, 'edges', None)).__name__}
                es = getattr(m0, 'edges', None)
                es = es() if callable(es) else es
                e0 = None
                try:
                    e0 = next(iter(es.values() if isinstance(es, dict) else es))
                except Exception:
                    pass
                info['edge_attrs'] = sorted(a for a in dir(e0) if not a.startswith('__'))[:60] if e0 is not None else None
                f0 = to_soften[0][1][0][0] if to_soften and to_soften[0][1] else None
                info['face_attrs'] = sorted(a for a in dir(f0) if not a.startswith('__'))[:60] if f0 is not None else None
                info['mesh_attrs'] = sorted(a for a in dir(m0) if not a.startswith('__'))[:80] if m0 is not None else None
                with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ed3d_soften_debug.txt"),
                          "w", encoding="utf-8") as fh:
                    fh.write("%s %s\nsoftened per part: %s\n%s\n" % (PLUGIN_NAME, VERSION, soft_log, info))
            except Exception as e:
                print("%s: soften log: %s" % (PLUGIN_NAME, e))

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
