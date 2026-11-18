# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Bridges & Arches for IngeTrazo
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
3D Bridges & Arches - masonry arch bridges and viaducts for IngeTrazo
One arch or a long run of them: piers, abutments, face walls, arch rings (brick rings or
stone voussoirs, with a keystone), barrels, deck, parapets with copings, a string course,
pillars at the parapet ends, cutwaters on the piers, end walls and wing walls.

  Arch shapes   Semicircular, segmental, elliptical, pointed (Gothic), Tudor, horseshoe and
                flat (jack) arch.
  Skew          Set a skew angle and the bridge crosses at an angle, the piers and barrels
                running with the road or river underneath, like a railway skew bridge.
  Arch infill   Fill any of the arches with a plain wall - flush or set back - with the door,
                window and fanlight holes already cut, like the railway arches used as workshops,
                garages and shops. Brick it with Brick & Block Studio and put your Period Windows
                and Period Doors in the holes. 'Add infill only' fills more arches afterwards with
                a different front.
  Where         Select a line along the middle of the bridge and it's built along it (and can be
                stretched to fit it); with nothing selected it's built at the middle of the model.

Every piece is its own group, so Scale Studio's Pieces page can lay each one flat on the print
bed: the face walls, the arch rings (one flat piece each, with their joints), the barrels (they
print standing on their end, no supports), the pier sides, deck, parapets and copings...

Sizes are real-world mm, like the other plugins - Scale Studio takes it down to your model
scale. Ctrl+Alt+Shift+B.

Version 1: arches, viaducts, skew arches and arch infill.
Version 1.1: the page tabs on two rows, so they all show at once.
Version 1.2: every piece straight in the bridge's group (not grouped by kind), so Scale Studio lays
each one flat on its own; wing walls in two halves (outer and inner), to brick both sides and glue
back to back.
Version 1.3: the arch rings built into the face walls (one piece); each piece tells Brick & Block
Studio (7.3) which side is its outside - wing wall halves both face out, the infill and pier sides
face the opening - and the hidden pieces (end walls, barrels, deck...) are marked as not walls.
Version 1.4: parapets as one piece with a flat back (wall, pillars and coping together); the end
walls get bricks on their outside.
Version 1.5: coping stones along the sloping tops of the wing walls (half on each half, so each half
keeps its flat back).
Version 1.6: parapets back to pillars and coping standing out both sides, but in two halves like the
wing walls - each half one piece (wall, half the pillars, half the coping) with a flat glue face,
bricked on its own side.
Version 1.7: decorative copings (saddleback, half-round, chamfered or flat, with drip grooves) in one
piece on top of both halves, covering the glue line - on the parapets and the wing walls - and caps
on the pillars; an arch lining, laid out flat beside the bridge, thin enough to warm and bend into
the arch (with brick courses, and the right shape for a skew arch).
Version 1.8: the arch lining plain (to finish as you like); copings made of separate-looking stones
with a recessed joint between them (2.5 x the joint G, at least 20 mm), still one piece; no drip
grooves.
"""

import os
import json
import math
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox, QCheckBox,
    QPushButton, QLabel, QMessageBox, QWidget, QInputDialog, QSpinBox, QTabWidget, QLineEdit
)

PLUGIN_NAME = "3D Bridges & Arches"
VERSION = "1.8"           # shown in the window title, so you can tell which file is loaded

OUTSIDE_KEY = "ed3d_outside"        # read by 3D Brick & Block Studio (7.3): the way a piece's outside looks
NOT_WALL_KEY = "ed3d_not_wall"      # ... and pieces that get no walling at all
SCALE = 0.001             # IngeTrazo stores metres; the bridge is worked out in real-world mm
PRESET_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Bridges & Arches")


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


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
SHAPES = [("Semicircular", 'semi'), ("Segmental (part of a circle)", 'segmental'),
          ("Elliptical", 'elliptical'), ("Pointed (Gothic)", 'pointed'), ("Tudor (four-centred)", 'tudor'),
          ("Horseshoe", 'horseshoe'), ("Flat (jack arch)", 'flat')]
RING_STYLES = [("Brick rings", 'brick'), ("Stone voussoirs", 'stone'), ("Plain band", 'plain'),
               ("No ring", 'none')]
FILL_SIDES = [("Front", 'front'), ("Back", 'back'), ("Both sides", 'both')]
DOOR_POS = [("In the middle", 'centre'), ("To the left", 'left'), ("To the right", 'right')]
WINGS = [("None", 'none'), ("Straight on (in line with the faces)", 'straight'),
         ("Splayed out", 'splayed')]
COPE_STYLES = [("Saddleback (ridged)", 'saddle'), ("Half-round", 'round'), ("Chamfered", 'chamfer'),
               ("Flat", 'flat')]
LINE_AT = [("Ground level (the bottom of the piers)", 'ground'), ("Deck level (the top of the deck)", 'deck')]

DEFAULTS = dict(
    shape='semi', arches=3, span=9000.0, rise=0.0, height=6000.0, pier_w=1800.0, abut_len=3000.0,
    skew=0.0, cutwaters=False, cut_out=0.0, cut_h=0.0,
    ring_style='brick', rings=3, ring_depth=225.0, vous_w=75.0, joint=10.0, ring_proud=40.0,
    keystone=False, key_w=0.0, key_up=0.0,
    width=8500.0, cover=600.0, deck_t=300.0, par_h=1100.0, par_t=450.0, cope_t=150.0, cope_over=75.0,
    string=True, str_h=300.0, str_out=75.0, pillars=False, pil_w=900.0, pil_up=300.0,
    end_walls=True, wing_halves=True, rings_in_walls=True, par_halves=True, wing_cope=True, cope_style='saddle', cope_len=900.0,
    pil_caps=True, lining=True, lin_t=40.0, wing='none', wing_len=6000.0, wing_ang=30.0, wing_end=600.0,
    fill='', fill_side='front', fill_back=0.0, fill_t=225.0,
    door_w=1500.0, door_h=2400.0, door_pos='centre', door_side=600.0,
    win_n=1, win_w=1200.0, win_h=1500.0, win_sill=900.0,
    fanlight=True, fan_border=225.0, fan_bottom=0.0,
    wall_t=300.0, barrel_t=300.0, side_t=300.0, end_t=300.0, split_barrel=False,
    line_at='ground', fit_line=True, paint=True)

# the keys that shape the bridge itself (kept with the last bridge, for 'Add infill only')
INFILL_KEYS = ('fill', 'fill_side', 'fill_back', 'fill_t', 'door_w', 'door_h', 'door_pos', 'door_side',
               'win_n', 'win_w', 'win_h', 'win_sill', 'fanlight', 'fan_border', 'fan_bottom', 'paint')

BUILTIN_PRESETS = {
    "Brick viaduct - double track, 9 m arches": dict(
        shape='semi', arches=5, span=9000.0, rise=0.0, height=9000.0, pier_w=1800.0, abut_len=3000.0, skew=0.0,
        cutwaters=False, ring_style='brick', rings=3, ring_depth=225.0, vous_w=75.0, joint=10.0, keystone=False,
        width=8500.0, cover=600.0, par_h=1100.0, par_t=450.0, string=True, pillars=True, end_walls=True,
        wing='splayed', fill=''),
    "Stone viaduct - tall, with cutwaters": dict(
        shape='semi', arches=4, span=12000.0, rise=0.0, height=18000.0, pier_w=2700.0, abut_len=4000.0,
        skew=0.0, cutwaters=True, ring_style='stone', rings=1, ring_depth=900.0, vous_w=500.0, joint=12.0,
        keystone=True, width=8000.0, cover=900.0, par_h=1100.0, par_t=500.0, string=True, pillars=False,
        end_walls=True, wing='straight', fill=''),
    "Brick overbridge - skew segmental arch": dict(
        shape='segmental', arches=1, span=10000.0, rise=2500.0, height=4500.0, pier_w=1800.0,
        abut_len=4500.0, skew=30.0, cutwaters=False, ring_style='brick', rings=4, ring_depth=225.0,
        vous_w=75.0, joint=10.0, keystone=False, width=9000.0, cover=500.0, par_h=1200.0, par_t=450.0,
        string=True, pillars=True, end_walls=True, wing='splayed', wing_len=7000.0, wing_ang=30.0, fill=''),
    "Railway arches - town viaduct with workshops": dict(
        shape='semi', arches=6, span=7500.0, rise=0.0, height=3000.0, pier_w=1350.0, abut_len=2500.0,
        skew=0.0, cutwaters=False, ring_style='brick', rings=3, ring_depth=225.0, vous_w=75.0, joint=10.0,
        keystone=False, width=8500.0, cover=450.0, par_h=1200.0, par_t=450.0, string=True, pillars=False,
        end_walls=True, wing='none', fill='all', fill_side='front', fill_back=225.0, door_w=1500.0,
        door_h=2400.0, door_pos='left', door_side=600.0, win_n=1, win_w=2000.0, win_h=1500.0,
        win_sill=900.0, fanlight=True, fan_border=225.0),
    "River bridge - stone, elliptical arches": dict(
        shape='elliptical', arches=3, span=15000.0, rise=4500.0, height=2500.0, pier_w=3000.0,
        abut_len=5000.0, skew=0.0, cutwaters=True, ring_style='stone', rings=1, ring_depth=900.0,
        vous_w=600.0, joint=12.0, keystone=True, width=10000.0, cover=750.0, par_h=1000.0, par_t=500.0,
        string=True, pillars=True, end_walls=True, wing='splayed', wing_len=8000.0, wing_ang=35.0, fill=''),
    "Gothic arcade - pointed arches": dict(
        shape='pointed', arches=5, span=4000.0, rise=0.0, height=2500.0, pier_w=900.0, abut_len=1200.0,
        skew=0.0, cutwaters=False, ring_style='stone', rings=1, ring_depth=450.0, vous_w=350.0, joint=10.0,
        keystone=False, width=3000.0, cover=450.0, par_h=900.0, par_t=300.0, string=True, pillars=False,
        end_walls=True, wing='none', fill=''),
}


def _f(v, k):
    try:
        return float(v.get(k, DEFAULTS[k]))
    except Exception:
        return float(DEFAULTS[k])


def _i(v, k):
    try:
        return int(v.get(k, DEFAULTS[k]))
    except Exception:
        return int(DEFAULTS[k])


def parse_fill(text, n):
    """The arches to fill from what's typed: 'all', '1, 3, 5', '2-4' - numbered from the start of
    the bridge. Returns (sorted list, problem or None)."""
    t = (text or "").strip().lower()
    if not t or t in ("none", "0", "-"):
        return [], None
    if t in ("all", "every", "*"):
        return list(range(1, n + 1)), None
    out = []
    for part in t.replace(";", ",").replace(" ", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            if "-" in part:
                a, b = part.split("-", 1)
                a, b = int(a), int(b)
                out += list(range(min(a, b), max(a, b) + 1))
            else:
                out.append(int(part))
        except ValueError:
            return [], "'%s' isn't an arch number - type 'all', or numbers like 1, 3, 5 or 2-4." % part
    bad = [k for k in out if k < 1 or k > n]
    out = sorted(set(k for k in out if 1 <= k <= n))
    return out, ("There are only %d arches - left out %s." % (n, ", ".join(str(b) for b in sorted(set(bad))))
                 if bad else None)


# ---------------------------------------------------------------------------
# Little geometry helpers (x along the bridge, y across it, z up; 2D work is in x, z)
# ---------------------------------------------------------------------------
def v_add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def v_sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def v_dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def v_len(a): return math.sqrt(v_dot(a, a))


def v_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def area2(poly):
    a = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        a += x0 * y1 - x1 * y0
    return a / 2.0


def ccw(poly):
    poly = clean(poly)
    return poly if area2(poly) > 0 else list(reversed(poly))


def cw(poly):
    poly = clean(poly)
    return poly if area2(poly) < 0 else list(reversed(poly))


def clean(poly, eps=1e-6):
    out = []
    for p in poly:
        if not out or abs(p[0] - out[-1][0]) > eps or abs(p[1] - out[-1][1]) > eps:
            out.append((float(p[0]), float(p[1])))
    while len(out) > 1 and abs(out[0][0] - out[-1][0]) <= eps and abs(out[0][1] - out[-1][1]) <= eps:
        out.pop()
    return out


def pip(p, poly):
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xc = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xc > x:
                inside = not inside
    return inside


def rect(x0, z0, x1, z1):
    return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]


class Solid:
    """Closed solid: faces[i] is a loop of 3D points, holes[i] loops cut out of faces[i]."""
    def __init__(self):
        self.faces = []
        self.holes = {}

    def add(self, pts, holes=()):
        if holes:
            self.holes[len(self.faces)] = [list(h) for h in holes]
        self.faces.append(list(pts))

    def loops(self):
        for i, f in enumerate(self.faces):
            yield f
            for h in self.holes.get(i, ()):
                yield h

    def volume(self):
        v = 0.0
        for pts in self.loops():
            for j in range(1, len(pts) - 1):
                v += v_dot(pts[0], v_cross(pts[j], pts[j + 1]))
        return v / 6.0

    def fix(self):
        if self.volume() < 0:
            self.faces = [list(reversed(f)) for f in self.faces]
            self.holes = {i: [list(reversed(h)) for h in hs] for i, hs in self.holes.items()}
        return self

    def mapped(self, fn):
        s = Solid()
        s.faces = [[fn(p) for p in f] for f in self.faces]
        s.holes = {i: [[fn(p) for p in h] for h in hs] for i, hs in self.holes.items()}
        return s.fix()

    def merged(self, other):
        """Two bodies in one piece (one mesh) - a ring plate and its raised blocks, say."""
        n = len(self.faces)
        self.faces += [list(f) for f in other.faces]
        for i, hs in other.holes.items():
            self.holes[n + i] = [list(h) for h in hs]
        return self


def prism(poly, y0, y1, holes=()):
    """A flat plate: the (x, z) outline (with any holes) standing from y0 to y1."""
    poly = ccw(poly)
    holes = [cw(h) for h in holes if len(clean(h)) >= 3]
    if len(poly) < 3:
        return None
    s = Solid()
    s.add([(x, y0, z) for x, z in poly], [[(x, y0, z) for x, z in h] for h in holes])
    s.add([(x, y1, z) for x, z in reversed(poly)], [[(x, y1, z) for x, z in reversed(h)] for h in holes])
    for loop in [poly] + holes:
        n = len(loop)
        for i in range(n):
            (ax, az), (bx, bz) = loop[i], loop[(i + 1) % n]
            s.add([(ax, y0, az), (ax, y1, az), (bx, y1, bz), (bx, y0, bz)])
    return s.fix()


def box(x0, y0, z0, x1, y1, z1):
    return prism(rect(x0, z0, x1, z1), min(y0, y1), max(y0, y1))


# ---------------------------------------------------------------------------
# Arch shapes: the inside curve (intrados) from the left springing to the right, each point
# with its normal pointing out into the ring. z = 0 at the springing.
# ---------------------------------------------------------------------------
HORSESHOE_DEG = 25.0


def _norm2(x, z):
    d = math.hypot(x, z) or 1.0
    return (x / d, z / d)


def arch_curve(shape, S, R, n=48):
    """(points, normals, rise) for an arch of clear span S. R is the rise (0 = the usual for
    the shape). n (even) is how many straight pieces the curve is made of; the crown is
    point n // 2 on the symmetric shapes."""
    n = max(8, int(n) // 2 * 2)
    S = float(S)
    R = float(R or 0.0)
    pts, nrm = [], []
    if shape == 'segmental':
        R = min(max(R if R > 0 else S / 4.0, S * 0.02), S / 2.0)
        r = (S * S / 4.0 + R * R) / (2.0 * R)
        zc = R - r
        b = math.asin(min(1.0, (S / 2.0) / r))
        for k in range(n + 1):
            t = math.pi / 2.0 + b - 2.0 * b * k / n
            pts.append((S / 2.0 + r * math.cos(t), zc + r * math.sin(t)))
            nrm.append((math.cos(t), math.sin(t)))
        pts[0], pts[-1] = (0.0, 0.0), (S, 0.0)
        return pts, nrm, R
    if shape == 'elliptical':
        a, b = S / 2.0, (R if R > 0 else S / 3.0)
        for k in range(n + 1):
            t = math.pi - math.pi * k / n
            pts.append((a + a * math.cos(t), b * math.sin(t)))
            nrm.append(_norm2(math.cos(t) / a, math.sin(t) / b))
        return pts, nrm, b
    if shape == 'pointed':
        R = max(R if R > 0 else S * math.sqrt(3.0) / 2.0, S / 2.0)
        r = (R * R + S * S / 4.0) / S
        ta = math.atan2(R, S / 2.0 - r)
        h = n // 2
        for k in range(h + 1):
            t = math.pi - (math.pi - ta) * k / h
            pts.append((r + r * math.cos(t), r * math.sin(t)))
            nrm.append((math.cos(t), math.sin(t)))
        pts[h] = (S / 2.0, R)
        nrm[h] = (0.0, 1.0)
        for k in range(h - 1, -1, -1):
            x, z = pts[k]
            nx, nz = nrm[k]
            pts.append((S - x, z))
            nrm.append((-nx, nz))
        return pts, nrm, R
    if shape == 'tudor':
        R = min(max(R if R > 0 else S / 3.0, S / 6.0), S / 2.0)
        r1 = min(S / 4.0, R * 0.75)
        al = math.radians(45.0)
        E = (r1 - r1 * math.cos(al), r1 * math.sin(al))
        u = (math.cos(al), -math.sin(al))
        P = (S / 2.0, R)
        dx, dz = E[0] - P[0], E[1] - P[1]
        den = 2.0 * (u[0] * dx + u[1] * dz)
        r2 = -(dx * dx + dz * dz) / den if abs(den) > 1e-9 else -1.0
        if r2 <= r1:
            return arch_curve('segmental', S, R, n)
        C2 = (E[0] + u[0] * r2, E[1] + u[1] * r2)
        tE = math.atan2(E[1] - C2[1], E[0] - C2[0])
        tP = math.atan2(P[1] - C2[1], P[0] - C2[0])
        if not tP < tE:
            return arch_curve('segmental', S, R, n)
        h = n // 2
        k1 = max(2, h // 3)
        half_p, half_n = [], []
        for k in range(k1 + 1):
            t = math.pi - al * k / k1
            half_p.append((r1 + r1 * math.cos(t), r1 * math.sin(t)))
            half_n.append((math.cos(t), math.sin(t)))
        for k in range(1, h - k1 + 1):
            t = tE - (tE - tP) * k / (h - k1)
            half_p.append((C2[0] + r2 * math.cos(t), C2[1] + r2 * math.sin(t)))
            half_n.append((math.cos(t), math.sin(t)))
        half_p[-1] = (S / 2.0, R)
        half_n[-1] = (0.0, 1.0)
        pts, nrm = list(half_p), list(half_n)
        for k in range(h - 1, -1, -1):
            x, z = half_p[k]
            nx, nz = half_n[k]
            pts.append((S - x, z))
            nrm.append((-nx, nz))
        return pts, nrm, R
    if shape == 'horseshoe':
        a = math.radians(HORSESHOE_DEG)
        r = S / (2.0 * math.cos(a))
        zc = r * math.sin(a)
        for k in range(n + 1):
            t = math.pi + a - (math.pi + 2.0 * a) * k / n
            pts.append((S / 2.0 + r * math.cos(t), zc + r * math.sin(t)))
            nrm.append((math.cos(t), math.sin(t)))
        pts[0], pts[-1] = (0.0, 0.0), (S, 0.0)
        return pts, nrm, zc + r
    if shape == 'flat':
        F = (S / 2.0, -S * 0.866)               # the joints all point back to here (60 degree skewbacks)
        for k in range(n + 1):
            x = S * k / n
            pts.append((x, 0.0))
            nrm.append(_norm2(x - F[0], -F[1]))
        return pts, nrm, 0.0
    # semicircular
    r = S / 2.0
    for k in range(n + 1):
        t = math.pi - math.pi * k / n
        pts.append((r + r * math.cos(t), r * math.sin(t)))
        nrm.append((math.cos(t), math.sin(t)))
    pts[0], pts[-1], pts[n // 2] = (0.0, 0.0), (S, 0.0), (S / 2.0, r)
    return pts, nrm, r


def horseshoe_out(shape, S):
    """How far a horseshoe arch bulges out past its jambs, each side."""
    if shape != 'horseshoe':
        return 0.0
    a = math.radians(HORSESHOE_DEG)
    return S / (2.0 * math.cos(a)) - S / 2.0


def offset_line(pts, nrm, d):
    return [(x + d * nx, z + d * nz) for (x, z), (nx, nz) in zip(pts, nrm)]


def _at(pts, nrm, s):
    """The point and normal part-way along the curve: s is a point number, with a fraction."""
    n = len(pts) - 1
    s = min(max(s, 0.0), float(n))
    i = min(int(s), n - 1)
    f = s - i
    (x0, z0), (x1, z1) = pts[i], pts[i + 1]
    (a0, b0), (a1, b1) = nrm[i], nrm[i + 1]
    return (x0 + f * (x1 - x0), z0 + f * (z1 - z0)), (a0 + f * (a1 - a0), b0 + f * (b1 - b0))


def _lengths(line):
    out = [0.0]
    for (x0, z0), (x1, z1) in zip(line[:-1], line[1:]):
        out.append(out[-1] + math.hypot(x1 - x0, z1 - z0))
    return out


def _param_at(cum, L):
    """The point number (with a fraction) a length L along a line whose running lengths are cum."""
    if L <= 0:
        return 0.0
    if L >= cum[-1]:
        return float(len(cum) - 1)
    lo, hi = 0, len(cum) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        if cum[m] <= L:
            lo = m
        else:
            hi = m
    seg = cum[hi] - cum[lo]
    return lo + ((L - cum[lo]) / seg if seg > 0 else 0.0)


def band(pts, nrm, s0, s1, d0, d1):
    """The piece of ring between points s0 and s1 along the curve, d0 to d1 out from the
    intrados - an outline (x, z), following the curve."""
    inner, outer = [], []
    ks = [s0] + [float(k) for k in range(int(math.floor(s0)) + 1, int(math.ceil(s1)))] + [s1]
    for s in ks:
        (x, z), (nx, nz) = _at(pts, nrm, s)
        inner.append((x + d0 * nx, z + d0 * nz))
        outer.append((x + d1 * nx, z + d1 * nz))
    return inner + list(reversed(outer))


# ---------------------------------------------------------------------------
# The bridge, worked out flat first (the front face, in x and z), then built
# ---------------------------------------------------------------------------
class Layout:
    pass


def bridge_layout(v, span=None):
    """Everything about the bridge that the build and the preview both need. Square to the
    bridge (the skew is put on when it's built). x = 0 at the start, y = 0 the front face."""
    L_ = Layout()
    L_.problems = []
    shape = v.get('shape', 'semi')
    n = max(1, _i(v, 'arches'))
    S = float(span if span is not None else _f(v, 'span'))
    if S < 300.0:
        raise ValueError("The span is too small (%.0f mm) - at least 300 mm." % S)
    P = max(_f(v, 'pier_w'), 1.0)
    A = max(_f(v, 'abut_len'), 1.0)
    H = max(_f(v, 'height'), 0.0)
    W = max(_f(v, 'width'), 500.0)
    out = horseshoe_out(shape, S)
    if n > 1 and P < 2.0 * out + 50.0:
        L_.problems.append("Horseshoe arches bulge %.0f mm past their jambs - the piers were made %.0f mm "
                           "wide so they don't meet." % (out, 2.0 * out + 300.0))
        P = 2.0 * out + 300.0
    if A < out + 50.0:
        A = out + 300.0
    pts, nrm, rise = arch_curve(shape, S, _f(v, 'rise'), 48 if S < 20000 else 72)
    style = v.get('ring_style', 'brick')
    rings = 1 if style == 'stone' else max(1, _i(v, 'rings'))
    rd = max(_f(v, 'ring_depth'), 1.0)
    ring_tot = rings * rd
    wt = max(_f(v, 'wall_t'), 1.0)
    bt = max(_f(v, 'barrel_t'), 1.0)
    cover = max(_f(v, 'cover'), 0.0)
    dt = max(_f(v, 'deck_t'), 1.0)
    Zd = H + rise + ring_tot + cover
    crown_top = H + rise + bt
    if crown_top > Zd - dt + 1e-6:
        L_.problems.append("The barrel (%.0f mm thick) comes up through the deck - more cover over the "
                           "crown (P), a thinner barrel or a thinner deck." % bt)
    L = 2.0 * A + n * S + (n - 1) * P
    xs = [A + k * (S + P) for k in range(n)]
    L_.__dict__.update(dict(shape=shape, n=n, S=S, P=P, A=A, H=H, W=W, pts=pts, nrm=nrm, rise=rise,
                            style=style, rings=rings, rd=rd, ring_tot=ring_tot, wt=min(wt, W / 3.0),
                            bt=bt, cover=cover, dt=dt, Zd=Zd, L=L, xs=xs,
                            skew=max(-60.0, min(60.0, _f(v, 'skew')))))
    # the face wall: the whole side of the bridge, with the arches cut out of the bottom
    face = [(0.0, 0.0)]
    for x0 in xs:
        face.append((x0, 0.0))
        face += [(x0 + x, H + z) for x, z in pts]
        face.append((x0 + S, 0.0))
    face += [(L, 0.0), (L, Zd), (0.0, Zd)]
    L_.face = clean(face)
    # the openings, each on its own (for the infill)
    L_.openings = [clean([(x0, 0.0)] + [(x0 + x, H + z) for x, z in pts] + [(x0 + S, 0.0)]) for x0 in xs]
    # the arch ring: a backing band, raised blocks with joints between, and a keystone
    L_.ring_band = band(pts, nrm, 0.0, float(len(pts) - 1), 0.0, ring_tot)
    blocks, key = [], None
    j = max(_f(v, 'joint'), 0.0)
    if style in ('brick', 'stone'):
        kpar = None
        if v.get('keystone') and shape != 'flat':
            kw = _f(v, 'key_w') or (max(_f(v, 'vous_w') * (1.6 if style == 'stone' else 6.0), rd * 0.6))
            ku = _f(v, 'key_up') or ring_tot * 0.2
            outer = offset_line(pts, nrm, ring_tot)
            cum = _lengths(outer)
            kc = cum[-1] / 2.0
            ka, kb = _param_at(cum, kc - kw / 2.0), _param_at(cum, kc + kw / 2.0)
            kpar = (ka, kb)
            key = band(pts, nrm, ka, kb, 0.0, ring_tot + ku)
        vw = max(_f(v, 'vous_w'), j + 5.0)
        for r in range(rings):
            d0 = r * rd + (j / 2.0 if r > 0 else 0.0)
            d1 = (r + 1) * rd - (j / 2.0 if r < rings - 1 else 0.0)
            mid = offset_line(pts, nrm, (d0 + d1) / 2.0)
            cum = _lengths(mid)
            if kpar:
                # the left half, from the springing to the keystone (less a joint), mirrored
                La = _length_to(cum, kpar[0]) - j / 2.0
                halves = [(0.0, La, False), (cum[-1] - La, cum[-1], True)]
            else:
                halves = [(0.0, cum[-1], None)]
            for a, b, _right in halves:
                if b - a < 1.0:
                    continue
                nb = max(1, int(round((b - a) / vw)))
                if style == 'stone' and not kpar and nb % 2 == 0:
                    nb += 1                         # a stone in the middle at the crown
                step = (b - a) / nb
                for k in range(nb):
                    la = a + k * step + (j / 2.0 if (k > 0 or a > 0) else 0.0)
                    lb = a + (k + 1) * step - (j / 2.0 if (k < nb - 1 or b < cum[-1]) else 0.0)
                    if lb - la < 0.5:
                        continue
                    blocks.append(band(pts, nrm, _param_at(cum, la), _param_at(cum, lb), d0, d1))
    L_.blocks = blocks
    L_.key = key
    # cutwaters: on the piers between arches
    L_.cutwaters = []
    if v.get('cutwaters') and n > 1:
        co = _f(v, 'cut_out') or P / 2.0
        ch = _f(v, 'cut_h') or H
        for k in range(n - 1):
            xa, xb = xs[k] + S, xs[k + 1]
            L_.cutwaters.append((xa, xb, co, min(ch, Zd - 10.0)))
    return L_


def _length_to(cum, s):
    """The running length at point s (with a fraction)."""
    i = min(int(s), len(cum) - 2)
    f = s - i
    return cum[i] + f * (cum[i + 1] - cum[i])


def clip_half(poly, a, b, c):
    """Keeps the part of the outline where a*x + b*z + c >= 0."""
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
    return clean(out)


# ---------------------------------------------------------------------------
# Arch infill: a plain wall in the arch, with the door, window and fanlight holes cut
# ---------------------------------------------------------------------------
def infill_front(L_, v, k):
    """(outline, holes, notes) for the infill of arch k (0 = the first), on the front face.
    Doors are cut up from the bottom edge; windows and the fanlight are holes."""
    x0, S, H = L_.xs[k], L_.S, L_.H
    notes = []
    opening = L_.openings[k]
    dw, dh = max(_f(v, 'door_w'), 0.0), max(_f(v, 'door_h'), 0.0)
    m = 100.0                                  # the least wall left round any hole
    doors = []
    if dw > 0 and dh > 0:
        pos = v.get('door_pos', 'centre')
        side = max(_f(v, 'door_side'), m)
        if pos == 'left':
            dx0 = x0 + side
        elif pos == 'right':
            dx0 = x0 + S - side - dw
        else:
            dx0 = x0 + (S - dw) / 2.0
        dx0 = max(x0 + m, min(dx0, x0 + S - m - dw))
        ok = dw <= S - 2 * m and all(pip(q, opening) for q in ((dx0 - m, dh + m), (dx0 + dw + m, dh + m),
                                                                (dx0 + dw / 2.0, dh + m)))
        if ok:
            doors.append((dx0, dx0 + dw))
        else:
            notes.append("The door (%.0f x %.0f mm) doesn't fit in the arch - left out." % (dw, dh))
    outline = list(opening)
    for a, b in doors:                         # the bottom edge runs right to left, back to the start
        outline += [(b, 0.0), (b, dh), (a, dh), (a, 0.0)]
    outline = clean(outline)
    holes = []
    tops = [dh] if doors else []
    nw = max(0, _i(v, 'win_n'))
    ww, wh, ws = _f(v, 'win_w'), _f(v, 'win_h'), _f(v, 'win_sill')
    if nw and ww > 0 and wh > 0:
        if doors:
            regions = [(x0 + m, doors[0][0] - m), (doors[0][1] + m, x0 + S - m)]
        else:
            regions = [(x0 + m, x0 + S - m)]
        left_out = 0
        for ra, rb in regions:
            room = rb - ra
            if room < ww + 2 * m:
                continue                       # no room this side of the door (a door near the jamb)
            cnt = nw
            while cnt and cnt * ww + (cnt + 1) * m > room + 1e-6:
                cnt -= 1
            left_out += nw - cnt
            for i in range(cnt):
                cx = ra + room * (i + 0.5) / cnt
                r_ = rect(cx - ww / 2.0, ws, cx + ww / 2.0, ws + wh)
                if all(pip((qx + sx * m, qz + sz * m), outline)
                       for (qx, qz), (sx, sz) in zip(r_, ((-1, -1), (1, -1), (1, 1), (-1, 1)))):
                    holes.append(r_)
                    tops.append(ws + wh)
                else:
                    left_out += 1
        if left_out:
            notes.append("%d window%s didn't fit in arch %d - left out (narrower or lower windows, or fewer)."
                         % (left_out, "" if left_out == 1 else "s", k + 1))
    if v.get('fanlight', True):
        bd = max(_f(v, 'fan_border'), 20.0)
        # just in the curve of the arch, unless it's set lower - and always over the door and windows
        zf = _f(v, 'fan_bottom') or max(H, (max(tops) if tops else 0.0) + bd)
        if tops and max(tops) > zf - bd + 1e-6:
            notes.append("The fanlight bottom (AP) is below the top of the door or windows - no fanlight.")
        else:
            inset = [(x0 + x - bd * nx, H + z - bd * nz) for (x, z), (nx, nz) in zip(L_.pts, L_.nrm)]
            poly = [(x0 + bd, min(zf, H) - 1.0)] + inset + [(x0 + S - bd, min(zf, H) - 1.0)]
            poly = clip_half(poly, 0.0, 1.0, -zf)
            if len(poly) >= 3 and abs(area2(poly)) > (bd * bd):
                holes.append(poly)
            elif zf < H + L_.rise - 2 * bd and L_.shape != 'flat':
                notes.append("No room for a fanlight in arch %d." % (k + 1))
    return outline, holes, notes


# ---------------------------------------------------------------------------
# Building it: every piece a closed solid, in real-world mm, square to the bridge
# ---------------------------------------------------------------------------
def _shift(poly, dx, dz):
    return [(x + dx, z + dz) for x, z in poly]


def ring_piece(L_, v, x0, into=0.0):
    """The arch ring on the front face of one arch: a flat piece standing out from the wall,
    with the joints cut in (brick rings or stone voussoirs) and the keystone standing out more."""
    proud = max(_f(v, 'ring_proud'), 1.0)
    H = L_.H
    if L_.style == 'none':
        return None
    if L_.style == 'plain' or not L_.blocks:
        return prism(_shift(L_.ring_band, x0, H), -proud, into)
    groove = min(max(_f(v, 'joint') * 1.5, proud * 0.3), proud * 0.6)
    back = proud - groove
    s = prism(_shift(L_.ring_band, x0, H), -back, into)        # 'into': a little way into the wall
    for b in L_.blocks:
        so = prism(_shift(b, x0, H), -proud, -back * 0.5)
        if so is not None:
            s.merged(so)
    if L_.key:
        so = prism(_shift(L_.key, x0, H), -proud * 1.5, -back * 0.5)
        if so is not None:
            s.merged(so)
    return s


def cutwater(xa, xb, out, h):
    """A pointed cutwater on the front of a pier, with a sloping cap."""
    xm = (xa + xb) / 2.0
    a, b, c = (xa, 0.0), (xm, -out), (xb, 0.0)
    cap = out
    apex = (xm, 0.0, h + cap)
    s = Solid()
    tri = [a, b, c]                                     # in plan (x, y)
    s.add([(x, y, 0.0) for x, y in tri])
    for (p, q) in ((a, b), (b, c), (c, a)):
        s.add([(p[0], p[1], 0.0), (q[0], q[1], 0.0), (q[0], q[1], h), (p[0], p[1], h)])
    for (p, q) in ((a, b), (b, c), (c, a)):
        s.add([(p[0], p[1], h), (q[0], q[1], h), apex])
    return _fix_outward(s)


def _fix_outward(s):
    """Turns each face to face out of the solid (for small convex solids)."""
    pts = [q for f in s.faces for q in f]
    c = tuple(sum(q[k] for q in pts) / len(pts) for k in range(3))
    faces = []
    for f in s.faces:
        n = (0.0, 0.0, 0.0)
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            n = (n[0] + (a[1] - b[1]) * (a[2] + b[2]), n[1] + (a[2] - b[2]) * (a[0] + b[0]),
                 n[2] + (a[0] - b[0]) * (a[1] + b[1]))
        fc = tuple(sum(q[k] for q in f) / len(f) for k in range(3))
        faces.append(f if v_dot(n, v_sub(fc, c)) >= 0 else list(reversed(f)))
    s.faces = faces
    return s


def _back(so, W):
    """The same piece on the back face (mirrored across the bridge)."""
    return so.mapped(lambda p: (p[0], W - p[1], p[2])) if so is not None else None


def wing_frame(end, side, phi, L, W):
    """(start point, along, inwards) in plan for a wing wall."""
    c, s = math.cos(phi), math.sin(phi)
    if end == 'start':
        if side == 'front':
            base, d = (0.0, 0.0), (-c, -s)
            m = (d[1], -d[0])
        else:
            base, d = (0.0, W), (-c, s)
            m = (-d[1], d[0])
    else:
        if side == 'front':
            base, d = (L, 0.0), (c, -s)
            m = (-d[1], d[0])
        else:
            base, d = (L, W), (c, s)
            m = (d[1], -d[0])
    return base, d, m


def wing_poly(L_, v):
    Lw = max(_f(v, 'wing_len'), 100.0)
    he = min(max(_f(v, 'wing_end'), 0.0), L_.Zd)
    return [(0.0, 0.0), (Lw, 0.0), (Lw, he), (0.0, L_.Zd)]


def coping_profile(style, Wc, H, over, drip=True):
    """The cross-section of a coping, (u, z): u across it (0 to Wc), z up from its bottom (0 to H).
    Drip grooves under the overhangs, so rain drips off rather than running down the wall."""
    H = max(H, 1.0)
    if style == 'saddle':
        top = [(Wc, H * 0.45), (Wc / 2.0, H), (0.0, H * 0.45)]
    elif style == 'round':
        top = [(Wc / 2.0 + Wc / 2.0 * math.cos(math.pi * k / 12.0),
                H * 0.4 + H * 0.6 * math.sin(math.pi * k / 12.0)) for k in range(13)]
    elif style == 'chamfer':
        c = min(H * 0.35, Wc * 0.15)
        top = [(Wc, H - c), (Wc - c, H), (c, H), (0.0, H - c)]
    else:
        top = [(Wc, H), (0.0, H)]
    bottom = [(0.0, 0.0)]
    g = min(over * 0.4, 40.0)
    if drip and over > 30.0 and g > 5.0:
        d = min(g * 0.6, H * 0.3)
        a = over / 2.0 - g / 2.0
        bottom += [(a, 0.0), (a, d), (a + g, d), (a + g, 0.0),
                   (Wc - a - g, 0.0), (Wc - a - g, d), (Wc - a, d), (Wc - a, 0.0)]
    bottom.append((Wc, 0.0))
    return clean(bottom + top)


def coping_bar(v, length, Wc, H, over):
    """A run of coping stones, length long, as one piece: (u across, l along, z up). Each stone is the
    full shape, with a joint between them; a slimmer core runs through underneath, so the joints
    look like recessed mortar but it all stays one piece."""
    prof = coping_profile(v.get('cope_style', 'saddle'), Wc, H, over, False)
    # the joint between stones: wider than a brick joint, so it still shows once it's scaled down
    j = max(_f(v, 'joint') * 2.5, 20.0) if _f(v, 'joint') > 0 else 0.0
    sl = max(_f(v, 'cope_len'), 0.0)
    if j <= 0 or sl <= 0 or length < 2.0 * sl:
        return prism(prof, 0.0, length)
    n = max(1, int(round(length / sl)))
    step = length / n
    jd = min(max(j * 1.5, 8.0), H * 0.3, Wc * 0.2)    # how far the joint goes in
    edge = min([z for u, z in prof if (u <= 1e-6 or u >= Wc - 1e-6) and z > 0] or [H])
    core = prism(rect(jd, 0.0, Wc - jd, max(edge - jd, H * 0.25)), 0.0, length)
    for k in range(n):
        a = k * step + (j / 2.0 if k > 0 else 0.0)
        b = (k + 1) * step - (j / 2.0 if k < n - 1 else 0.0)
        core.merged(prism(prof, a, b))
    return core


def coping_along(v, x0, x1, y0, Wc, zb, H, over):
    """A straight coping from x0 to x1, across y0 to y0 + Wc, its bottom at zb - one piece."""
    so = coping_bar(v, x1 - x0, Wc, H, over)          # (u, l, z)
    return so.mapped(lambda p: (x0 + p[1], y0 + p[0], zb + p[2]))


def pillar_cap(v, x0, y0, w, zb, H, over):
    """A cap on a square pillar w across: a slab hanging 'over' past it, with a pyramid on top
    (a plain slab for flat copings)."""
    style = v.get('cope_style', 'saddle')
    a0, b0, a1, b1 = x0 - over, y0 - over, x0 + w + over, y0 + w + over
    if style == 'flat':
        return box(a0, b0, zb, a1, b1, zb + H)
    hs = H * 0.45
    s = box(a0, b0, zb, a1, b1, zb + hs)
    top = Solid()                                     # the pyramid (a frustum for chamfered)
    cx, cy = (a0 + a1) / 2.0, (b0 + b1) / 2.0
    inset = (a1 - a0) * (0.3 if style == 'chamfer' else 0.5)
    q = [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]
    r = [(a0 + inset, b0 + inset), (a1 - inset, b0 + inset), (a1 - inset, b1 - inset), (a0 + inset, b1 - inset)]
    z1, z2 = zb + hs * 0.98, zb + H
    top.add([(x, y, z1) for x, y in reversed(q)])
    if inset >= (a1 - a0) / 2.0 - 1e-6:
        for i in range(4):
            top.add([(q[i][0], q[i][1], z1), (q[(i + 1) % 4][0], q[(i + 1) % 4][1], z1), (cx, cy, z2)])
    else:
        top.add([(x, y, z2) for x, y in r])
        for i in range(4):
            j = (i + 1) % 4
            top.add([(q[i][0], q[i][1], z1), (q[j][0], q[j][1], z1), (r[j][0], r[j][1], z2), (r[i][0], r[i][1], z2)])
    return s.merged(_fix_outward(top))


def _flat(poly, z0, z1):
    """A plate lying flat: the outline in (x, y), from z0 up to z1."""
    so = prism(poly, z0, z1)                          # (x, y-as-z...) then turned to lie down
    return so.mapped(lambda p: (p[0], p[2], p[1])) if so is not None else None


def lining_layout(L_, v):
    """The inside of the arch (the barrel's underside) opened out flat: (outline, bricks) in
    (s, a) - s round the arch, a along the barrel - and its size. On a skew arch the barrel runs at
    an angle, so the opened-out shape is skewed and curved at the ends, worked out from the barrel."""
    t = math.tan(math.radians(L_.skew))
    k = math.sqrt(1.0 + t * t)
    pts = L_.pts
    ss, aa = [0.0], [pts[0][0] * t / k]
    for (x0, z0), (x1, z1) in zip(pts[:-1], pts[1:]):
        dx, dz = x1 - x0, z1 - z0
        along = dx * t / k
        ss.append(ss[-1] + math.sqrt(max(dx * dx + dz * dz - along * along, 0.0)))
        aa.append(x1 * t / k)
    y0, y1 = L_.wt * k, (L_.W - L_.wt) * k
    lo = min(aa) + y0
    low = [(s_, a_ + y0 - lo) for s_, a_ in zip(ss, aa)]
    up = [(s_, a_ + y1 - lo) for s_, a_ in zip(ss, aa)]
    outline = clean(low + list(reversed(up)))

    def edge(line, s_):
        for (sa, aa_), (sb, ab) in zip(line[:-1], line[1:]):
            if sa - 1e-9 <= s_ <= sb + 1e-9:
                f = (s_ - sa) / (sb - sa) if sb > sa else 0.0
                return aa_ + f * (ab - aa_)
        return line[-1][1] if s_ > line[-1][0] else line[0][1]
    bricks = []
    rel = 0.0                                          # plain: finish it as you like
    if rel > 0:
        j = max(_f(v, 'joint'), 1.0)
        ch, bl = 65.0 + j, 215.0 + j                  # a course, a brick (stretchers along the barrel)
        r = 0
        while r * ch < ss[-1] - 1.0:
            sa, sb = r * ch + j / 2.0, min((r + 1) * ch - j / 2.0, ss[-1] - j / 2.0)
            if sb - sa > 5.0:
                la, lb, ua, ub = edge(low, sa), edge(low, sb), edge(up, sa), edge(up, sb)
                off = (bl / 2.0) * (r % 2)
                a_ = math.floor((min(la, lb) - off) / bl) * bl + off
                while a_ < max(ua, ub):
                    q = [(sa, a_ + j / 2.0), (sb, a_ + j / 2.0), (sb, a_ + bl - j / 2.0), (sa, a_ + bl - j / 2.0)]
                    # keep the part between the two ends of the barrel
                    q = clip_half(q, -(lb - la), (sb - sa), (lb - la) * sa - (sb - sa) * la)
                    if len(q) >= 3:
                        q = clip_half(q, (ub - ua), -(sb - sa), -(ub - ua) * sa + (sb - sa) * ua)
                    if len(q) >= 3 and abs(area2(q)) > 20.0:
                        bricks.append(q)
                    a_ += bl
            r += 1
    return outline, bricks, ss[-1], max(p[1] for p in outline)


def lining_piece(L_, v):
    """The arch lining, printed flat and bent into the arch: a thin backing with the bricks standing
    up on it. Lies flat in the model, out in front of the bridge."""
    outline, bricks, s_len, a_len = lining_layout(L_, v)
    th = max(_f(v, 'lin_t'), 1.0)
    rel = 0.0
    so = _flat(outline, 0.0, th)
    for b in bricks:
        bs = _flat(b, th * 0.5, th + rel)
        if bs is not None:
            so.merged(bs)
    return so, s_len, a_len


def _mark(so, outside=None):
    """Tells Brick & Block Studio about a piece: outside = the way its outside face looks (square to
    the bridge), or None for a piece that's not a wall (no walling on it)."""
    if so is not None:
        so.outside = outside
        so.wall = outside is not None
    return so


def bridge_pieces(L_, v, parts=True, infill=True, fill_list=None):
    """[(kind, [(name, type, solid)])], notes. parts: the bridge itself; infill: the arch infill."""
    out, notes = [], []
    W, L, H, Zd = L_.W, L_.L, L_.H, L_.Zd
    wt, S = L_.wt, L_.S
    n = L_.n
    FRONT, BACK = (0.0, -1.0, 0.0), (0.0, 1.0, 0.0)
    if parts:
        f = prism(L_.face, 0.0, wt)
        rings = []
        in_walls = v.get('rings_in_walls', True)
        for k, x0 in enumerate(L_.xs):
            r = ring_piece(L_, v, x0, into=min(1.0, wt * 0.25) if in_walls else 0.0)
            if r is None:
                continue
            if in_walls:
                f.merged(r)                     # built into the face wall: one piece, attached
            else:
                rings.append(("Arch %d - ring front" % (k + 1), 'ring', _mark(r)))
                rings.append(("Arch %d - ring back" % (k + 1), 'ring', _mark(_back(r, W))))
        out.append(("Face walls", [("Face wall - front", 'face', _mark(f, FRONT)),
                                   ("Face wall - back", 'face', _mark(_back(f, W), BACK))]))
        if rings:
            out.append(("Arch rings", rings))
        barrels = []
        m = (len(L_.pts) - 1) // 2
        for k, x0 in enumerate(L_.xs):
            np_ = len(L_.pts) - 1
            if v.get('split_barrel') and L_.shape != 'flat':
                for nm, (a, b) in (("left", (0.0, float(m))), ("right", (float(m), float(np_)))):
                    bb = _shift(band(L_.pts, L_.nrm, a, b, 0.0, L_.bt), x0, H)
                    barrels.append(("Arch %d - barrel %s half" % (k + 1, nm), 'barrel',
                                    _mark(prism(bb, wt, W - wt))))
            else:
                bb = _shift(band(L_.pts, L_.nrm, 0.0, float(np_), 0.0, L_.bt), x0, H)
                barrels.append(("Arch %d - barrel" % (k + 1), 'barrel', _mark(prism(bb, wt, W - wt))))
        out.append(("Barrels", barrels))
        if v.get('lining', True) and L_.shape != 'flat':
            # one lining fits every arch (they're all the same): print one for each
            lin, s_len, a_len = lining_piece(L_, v)
            gap = 3000.0 + (_f(v, 'wing_len') if v.get('wing', 'none') != 'none' else 0.0)
            lin = lin.mapped(lambda p: (L_.xs[0] + p[1], -gap - p[0], p[2]))
            lin.flat_world = True                 # laid out flat, not skewed with the bridge
            out.append(("Arch lining", [("Arch lining - print %d, bend into %s (%.0f x %.0f)" % (
                L_.n, "each arch" if L_.n > 1 else "the arch", s_len, a_len), 'lining', _mark(lin))]))
        ts = min(max(_f(v, 'side_t'), 1.0), L_.P / 2.0 - 1.0, L_.A - 1.0)
        sides = []
        if H > 1.0:
            for k, x0 in enumerate(L_.xs):
                # their outside faces into the arch, where you see them
                sides.append(("Arch %d - pier side left" % (k + 1), 'side',
                              _mark(box(x0 - ts, wt, 0.0, x0, W - wt, H), (1.0, 0.0, 0.0))))
                sides.append(("Arch %d - pier side right" % (k + 1), 'side',
                              _mark(box(x0 + S, wt, 0.0, x0 + S + ts, W - wt, H), (-1.0, 0.0, 0.0))))
            out.append(("Pier sides", sides))
        if L_.cutwaters:
            cws = []
            for k, (xa, xb, co, ch) in enumerate(L_.cutwaters):
                c_ = cutwater(xa, xb, co, ch)
                cws.append(("Pier %d - cutwater front" % (k + 1), 'cutwater', c_))
                cws.append(("Pier %d - cutwater back" % (k + 1), 'cutwater', _back(c_, W)))
            out.append(("Cutwaters", cws))
        out.append(("Bridge deck", [("Deck", 'deck', box(0.0, wt, Zd - L_.dt, L, W - wt, Zd))]))
        if v.get('end_walls', True):
            te = min(max(_f(v, 'end_t'), 1.0), L_.A)
            out.append(("End walls", [
                ("End wall - start", 'end', _mark(box(0.0, wt, 0.0, te, W - wt, Zd - L_.dt), (-1.0, 0.0, 0.0))),
                ("End wall - finish", 'end', _mark(box(L - te, wt, 0.0, L, W - wt, Zd - L_.dt), (1.0, 0.0, 0.0)))]))
        par = []
        ph, pt = max(_f(v, 'par_h'), 0.0), max(_f(v, 'par_t'), 1.0)
        ct, co = max(_f(v, 'cope_t'), 0.0), max(_f(v, 'cope_over'), 0.0)
        pw = max(_f(v, 'pil_w'), pt) if v.get('pillars') else 0.0
        if ph > ct + 1.0 and v.get('par_halves', True):
            # two halves each side, like the wing walls: the outer half (the face of the bridge) and the
            # inner half (the deck side), each one piece - its wall, half of each pillar and half the
            # coping - flat on the glue face down the middle. Brick each on its own side, glue together.
            pu = max(_f(v, 'pil_up'), 0.0)
            hm = pt / 2.0                                   # the glue face
            # The coping and the pillar caps are one piece each, on top of both halves - over the glue line.
            for nm, y0, y1, py0, py1, way in (("outer half", 0.0, hm, hm - pw / 2.0, hm, FRONT),
                                              ("inner half", hm, pt, hm, hm + pw / 2.0, BACK)):
                half = box(pw, y0, Zd, L - pw, y1, Zd + ph - ct)
                if pw:
                    for xa in (0.0, L - pw):
                        half.merged(box(xa, py0, Zd, xa + pw, py1, Zd + ph + pu))
                par += [("Parapet - front (%s)" % nm, 'parapet', _mark(half, way)),
                        ("Parapet - back (%s)" % nm, 'parapet', _mark(_back(half, W), (0.0, -way[1], 0.0)))]
            if ct > 0:
                c_ = coping_along(v, pw, L - pw, -co, pt + 2.0 * co, Zd + ph - ct, ct, co)
                par += [("Coping - front", 'coping', _mark(c_)), ("Coping - back", 'coping', _mark(_back(c_, W)))]
            if pw and v.get('pil_caps', True) and ct > 0:
                for nm, xa in (("start", 0.0), ("finish", L - pw)):
                    q = pillar_cap(v, xa, hm - pw / 2.0, pw, Zd + ph + pu, ct, min(co, pw * 0.15))
                    par += [("Pillar cap %s - front" % nm, 'coping', _mark(q)),
                            ("Pillar cap %s - back" % nm, 'coping', _mark(_back(q, W)))]
        elif ph > ct + 1.0:
            p_ = box(pw, 0.0, Zd, L - pw, pt, Zd + ph - ct)
            par += [("Parapet - front", 'parapet', _mark(p_, FRONT)),
                    ("Parapet - back", 'parapet', _mark(_back(p_, W), BACK))]
            if ct > 0:
                c_ = coping_along(v, pw, L - pw, -co, pt + 2.0 * co, Zd + ph - ct, ct, co)
                par += [("Coping - front", 'coping', c_), ("Coping - back", 'coping', _back(c_, W))]
            if pw:
                pu = max(_f(v, 'pil_up'), 0.0)
                for nm, xa in (("start", 0.0), ("finish", L - pw)):
                    q = box(xa, pt / 2.0 - pw / 2.0, Zd, xa + pw, pt / 2.0 + pw / 2.0, Zd + ph + pu)
                    par += [("Pillar %s - front" % nm, 'pillar', q), ("Pillar %s - back" % nm, 'pillar', _back(q, W))]
                    if v.get('pil_caps', True) and ct > 0:
                        cp = pillar_cap(v, xa, pt / 2.0 - pw / 2.0, pw, Zd + ph + pu, ct, min(co, pw * 0.15))
                        par += [("Pillar cap %s - front" % nm, 'coping', cp),
                                ("Pillar cap %s - back" % nm, 'coping', _back(cp, W))]
        if v.get('string', True):
            sh, so = max(_f(v, 'str_h'), 1.0), max(_f(v, 'str_out'), 1.0)
            s_ = box(0.0, -so, Zd - sh, L, 0.0, Zd)
            par += [("String course - front", 'string', s_), ("String course - back", 'string', _back(s_, W))]
        if par:
            out.append(("Bridge parapets", par))
        if v.get('wing', 'none') != 'none':
            phi = math.radians(max(0.0, min(80.0, _f(v, 'wing_ang')))) if v.get('wing') == 'splayed' else 0.0
            poly = wing_poly(L_, v)
            # the coping along the sloping top: T thick (square to the slope), hanging U over each face
            ct_w, co_w = max(_f(v, 'cope_t'), 0.0), max(_f(v, 'cope_over'), 0.0)
            if v.get('wing_halves', True):
                # two skins, each half the thickness: brick each one on its own face (the outer half on
                # the outside, the inner half on the embankment side), glue them back to back
                plates = [(" (outer half)", prism(poly, 0.0, wt / 2.0), -1.0),
                          (" (inner half)", prism(poly, wt / 2.0, wt), 1.0)]
            else:
                plates = [("", prism(poly, 0.0, wt), -1.0)]
            if v.get('wing_cope', True) and ct_w > 0:
                # one piece down the sloping top, over both halves (and the glue line between them)
                (s0, z0), (s1, z1) = poly[3], poly[2]
                ln = math.hypot(s1 - s0, z1 - z0) or 1.0
                e_ = ((s1 - s0) / ln, (z1 - z0) / ln)
                n_ = (-e_[1], e_[0])                          # square to the slope, upwards
                cs = coping_bar(v, ln, wt + 2.0 * co_w, ct_w, co_w).mapped(
                    lambda p: (s0 + e_[0] * p[1] + n_[0] * p[2], -co_w + p[0], z0 + e_[1] * p[1] + n_[1] * p[2]))
                plates.append((" coping", cs, None))
            ws = []
            for end in ('start', 'finish'):
                for side in ('front', 'back'):
                    base, d, mm = wing_frame('start' if end == 'start' else 'end', side, phi, L, W)

                    def to(p, base=base, d=d, mm=mm):
                        s_, t_, z_ = p
                        return (base[0] + d[0] * s_ + mm[0] * t_, base[1] + d[1] * s_ + mm[1] * t_, z_)
                    for tail, plate, way in plates:
                        ws.append(("Wing wall - %s %s%s" % (end, side, tail), 'coping' if way is None else 'wing',
                                   _mark(plate.mapped(to), None if way is None else
                                         (mm[0] * way, mm[1] * way, 0.0))))
            out.append(("Bridge wing walls", ws))
    if infill:
        want, why = parse_fill(v.get('fill', ''), n) if fill_list is None else (fill_list, None)
        if why:
            notes.append(why)
        fs = []
        side = v.get('fill_side', 'front')
        ti = max(_f(v, 'fill_t'), 1.0)
        yb = min(max(_f(v, 'fill_back'), 0.0), W / 2.0 - ti)
        for k in want:
            outline, holes, nts = infill_front(L_, v, k - 1)
            notes += nts
            pl = prism(outline, yb, yb + ti, holes)
            if pl is None:
                continue
            if side in ('front', 'both'):
                fs.append(("Arch %d - infill front" % k, 'infill', _mark(pl, FRONT)))
            if side in ('back', 'both'):
                fs.append(("Arch %d - infill back" % k, 'infill', _mark(_back(pl, W), BACK)))
        if fs:
            out.append(("Arch infill", fs))
    out = [(kind, [b for b in bs if b[2] is not None]) for kind, bs in out]
    return [(kind, bs) for kind, bs in out if bs], notes


def world_mapper(L_, place, skew=True):
    """Square-to-the-bridge mm -> the model, in metres: the skew, then turned and moved onto
    the line (or the middle of the model). place = (x, y, z, angle) in mm and radians."""
    ox, oy, oz, ang = place
    t = math.tan(math.radians(L_.skew)) if skew else 0.0
    W = L_.W
    ca, sa = math.cos(ang), math.sin(ang)

    def fn(p):
        x, y, z = p
        yc = y - W / 2.0
        x = x + yc * t
        return ((ox + ca * x - sa * yc) * SCALE, (oy + sa * x + ca * yc) * SCALE, (oz + z) * SCALE)
    return fn


class AutoSpin(QDoubleSpinBox):
    """A size box where 0 means 'auto'. The box itself only ever holds a plain number, so you can
    type straight into it; what auto comes to is shown in the label beside it ('auto 320 mm').
    The up arrow from 0 starts at the auto size instead of 1 mm."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._auto = None

    def stepBy(self, steps):
        if steps > 0 and self.value() <= self.minimum() and self._auto:
            self.setValue(min(self.maximum(), round(self._auto, self.decimals())))
            return
        super().stepBy(steps)



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



# ---------------------------------------------------------------------------
# The window
# ---------------------------------------------------------------------------
MM, DEG = " mm", " °"

# (key, label, min, max, decimals, tip, unit)
ARCH_FIELDS = [
    ('span', "A   Span", 300.0, 200000.0, 0, "The clear span of each arch - from pier to pier, along the face "
                                             "of the bridge. On a skew bridge it's measured along the face.", MM),
    ('rise', "B   Rise", 0.0, 100000.0, 0, "How high the arch rises above the springing (where the curve "
                                           "starts). Semicircular and horseshoe arches set their own. "
                                           "0 = the usual rise for the shape.", MM),
    ('ring_depth', "E   Ring depth", 1.0, 5000.0, 0, "How deep each ring of the arch is, out from the inside "
                                                    "curve - 225 for a ring of bricks laid on end (headers), "
                                                    "600 to 1000 for stone voussoirs.", MM),
    ('vous_w', "F   Brick / voussoir width", 5.0, 5000.0, 0, "How wide each brick or stone looks on the face of "
                                                            "the ring, joint included. 75 for bricks.", MM),
    ('joint', "G   Joint", 0.0, 200.0, 1, "The mortar joint between the bricks or stones (and between the "
                                         "rings). 0 = no joints showing.", MM),
    ('ring_proud', "H   Ring stands out", 1.0, 1000.0, 0, "How far the arch ring stands out from the face wall. "
                                                         "The joints are cut part way into it.", MM),
    ('key_w', "J   Keystone width", 0.0, 5000.0, 0, "How wide the keystone at the top of the arch is. "
                                                   "0 = worked out from the bricks or stones.", MM),
    ('key_up', "K   Keystone above the ring", 0.0, 5000.0, 0, "How far the keystone stands up past the top of "
                                                             "the ring. 0 = a fifth of the ring depth.", MM),
]
LINING_FIELDS = [
    ('lin_t', "Lining thickness", 1.0, 1000.0, 1, "How thick the arch lining's backing is - thin, so it can be "
                                                   "warmed and bent into the arch. 40 = about 0.5 mm in OO.", MM),
]
PIER_FIELDS = [
    ('height', "C   Height to the springing", 0.0, 100000.0, 0, "From the ground up to where the arches start "
                                                               "to curve (the springing) - the height of the "
                                                               "piers. On a flat arch it's the height of the "
                                                               "opening.", MM),
    ('pier_w', "D   Pier width", 50.0, 50000.0, 0, "How wide each pier between the arches is, along the "
                                                   "bridge.", MM),
    ('abut_len', "L   Abutment length", 50.0, 100000.0, 0, "How much solid wall there is at each end, past "
                                                            "the end arches.", MM),
    ('skew', "AD  Skew angle", -60.0, 60.0, 1, "0 = square. Set an angle and the bridge crosses at a slant: the "
                                              "piers and barrels run at this angle, with the road, railway "
                                              "or river underneath, like a skew bridge. Minus for the other "
                                              "way.", DEG),
    ('cut_out', "M   Cutwater sticks out", 0.0, 20000.0, 0, "How far the pointed cutwaters stand out from the "
                                                            "faces of the piers. 0 = half the pier width.", MM),
    ('cut_h', "N   Cutwater height", 0.0, 100000.0, 0, "How high the cutwaters go before their sloping caps. "
                                                       "0 = up to the springing.", MM),
]
DECK_FIELDS = [
    ('width', "W   Deck width", 500.0, 100000.0, 0, "How wide the bridge is, from the outside of one parapet to "
                                                    "the outside of the other - about 4500 for single track, "
                                                    "8500 for double track.", MM),
    ('cover', "P   Cover over the crown", 0.0, 20000.0, 0, "How much there is between the top of the arch ring and "
                                                           "the top of the deck.", MM),
    ('deck_t', "Q   Deck thickness", 1.0, 5000.0, 0, "How thick the deck plate is.", MM),
    ('par_h', "R   Parapet height", 0.0, 10000.0, 0, "How high the parapet walls stand above the deck, coping "
                                                     "included. 0 = no parapets.", MM),
    ('par_t', "S   Parapet thickness", 1.0, 5000.0, 0, "How thick the parapet walls are.", MM),
    ('cope_t', "T   Coping thickness", 0.0, 2000.0, 0, "How thick the coping stones on top of the parapets are. "
                                                       "0 = no coping.", MM),
    ('cope_over', "U   Coping overhang", 0.0, 2000.0, 0, "How far the coping hangs over each side of the "
                                                         "parapet.", MM),
    ('str_h', "V   String course height", 1.0, 5000.0, 0, "How tall the string course is - the band along the "
                                                           "face at deck level.", MM),
    ('str_out', "X   String course stands out", 1.0, 2000.0, 0, "How far the string course stands out from the "
                                                                "face.", MM),
    ('pil_w', "Y   Pillar width", 1.0, 10000.0, 0, "How wide the square pillars at the ends of the parapets "
                                                    "are.", MM),
    ('pil_up', "Z   Pillar above the coping", 0.0, 10000.0, 0, "How far the pillars stand up past the top of the "
                                                               "parapet.", MM),
]
END_FIELDS = [
    ('wing_len', "AA  Wing wall length", 100.0, 100000.0, 0, "How long each wing wall is, out from the corner of "
                                                            "the bridge.", MM),
    ('wing_ang', "AB  Splay angle", 0.0, 80.0, 1, "Splayed wing walls: how far they turn out from the line of "
                                                 "the faces. 0 = straight on.", DEG),
    ('wing_end', "AC  Height at the far end", 0.0, 100000.0, 0, "The wing walls slope down from deck level to "
                                                               "this height at their far end, like the "
                                                               "embankment.", MM),
]
INFILL_FIELDS = [
    ('fill_back', "AE  Set back", 0.0, 20000.0, 0, "How far the infill wall is set back from the face. 0 = flush "
                                                  "with the face.", MM),
    ('fill_t', "AF  Infill thickness", 1.0, 5000.0, 0, "How thick the infill wall is.", MM),
    ('door_w', "AG  Door width", 0.0, 50000.0, 0, "How wide the door hole is. 0 = no door.", MM),
    ('door_h', "AH  Door height", 0.0, 50000.0, 0, "How tall the door hole is.", MM),
    ('door_side', "AJ  Door from the side", 0.0, 50000.0, 0, "With the door to the left or right: how far it is "
                                                            "from the side of the arch.", MM),
    ('win_w', "AK  Window width", 0.0, 50000.0, 0, "How wide each window hole is.", MM),
    ('win_h', "AL  Window height", 0.0, 50000.0, 0, "How tall each window hole is.", MM),
    ('win_sill', "AM  Sill height", 0.0, 50000.0, 0, "How high the bottom of the windows is, off the ground.", MM),
    ('fan_border', "AN  Fanlight border", 20.0, 5000.0, 0, "How much wall is left round the fanlight, inside the "
                                                         "arch.", MM),
    ('fan_bottom', "AP  Fanlight bottom", 0.0, 100000.0, 0, "How high the bottom of the fanlight is, off the "
                                                           "ground. 0 = at the springing (or over the door and "
                                                           "windows if they're higher). Set it low for one big "
                                                           "glazed arch.", MM),
]
PRINT_FIELDS = [
    ('wall_t', "Face wall thickness", 1.0, 5000.0, 0, "How thick the two face walls (the sides of the bridge) "
                                                     "are. 300 = 4 mm in OO.", MM),
    ('barrel_t', "Barrel thickness", 1.0, 5000.0, 0, "How thick the barrel (the curved underside of each arch) "
                                                    "is.", MM),
    ('side_t', "Pier side thickness", 1.0, 5000.0, 0, "How thick the plates down the sides of the piers, under "
                                                     "the arches, are.", MM),
    ('end_t', "End wall thickness", 1.0, 5000.0, 0, "How thick the walls closing the ends of the bridge are.", MM),
]
ALL_FIELDS = ARCH_FIELDS + PIER_FIELDS + DECK_FIELDS + END_FIELDS + INFILL_FIELDS + PRINT_FIELDS

# ready-made infill fronts: they fill in the boxes on the Arch infill page
FRONTS = [
    ("Workshop - door, a window each side", dict(door_w=1500.0, door_h=2400.0, door_pos='centre', win_n=1,
                                                  win_w=1200.0, win_h=1500.0, win_sill=900.0, fanlight=True,
                                                  fan_bottom=0.0)),
    ("Garage - wide double doors", dict(door_w=3600.0, door_h=3000.0, door_pos='centre', win_n=0,
                                        fanlight=True, fan_bottom=0.0)),
    ("Shop - big window beside a door", dict(door_w=1000.0, door_h=2200.0, door_pos='right', door_side=600.0,
                                             win_n=1, win_w=3000.0, win_h=1800.0, win_sill=600.0, fanlight=True,
                                             fan_bottom=0.0)),
    ("Glazed arch - one big window", dict(door_w=0.0, win_n=0, fanlight=True, fan_bottom=300.0)),
    ("Lock-up - small door only", dict(door_w=1200.0, door_h=2200.0, door_pos='centre', win_n=0,
                                       fanlight=False)),
    ("Bricked up - no holes", dict(door_w=0.0, win_n=0, fanlight=False)),
]

EDDY_TIPS = {
    'Start here': "Building a bridge step by step: what kind, its size, the skew and rings, any infill, "
                  "where it goes - then build it. Each step fills in the other pages.",
    'Arch shape': "The shape of the arches. The rise (B) sets how high segmental, elliptical, pointed and "
                  "Tudor arches go.",
    'Ring': "What the arch ring on the face looks like: rings of bricks, stone voussoirs, a plain band, or "
            "none.",
    'Rings of bricks': "How many rings of bricks, one outside the other (most brick arches have 2 to 5).",
    'Arch lining': "A thin plain lining for the underside of the arch, laid out flat in front of the bridge so "
                   "it prints flat: warm it and bend it into the arch. Plain, so you can finish it as you like. "
                   "On a skew arch it's the right skewed shape. One fits every arch - print one for each.",
    'Coping': "The shape of the coping stones on the parapets and wing walls - each one a single piece "
              "sitting on top of both halves, over the glue line.",
    'Coping stone length': "How long each coping stone looks. The joints between them are recessed like "
                           "mortar (2.5 x the joint G, so it still shows when scaled down), but the "
                           "coping is still one piece. 0 = no joints.",
    'Caps on the pillars': "A cap on each pillar, hanging over it, shaped to go with the coping (a pyramid "
                           "for saddleback or half-round, a plain slab for flat). One piece over both halves.",
    'Rings built into the face walls': "Ticked, each arch ring is part of its face wall - one piece, so it's "
                                       "attached and prints with the wall. Unticked, the rings are pieces of "
                                       "their own to glue on.",
    'Keystone': "A keystone at the top of each arch, standing out more than the ring.",
    'Arches': "How many arches. 1 for a single arch bridge.",
    'Cutwaters on the piers': "Pointed cutwaters on both faces of each pier, with sloping caps - for a "
                              "river bridge.",
    'String course along the faces': "A band standing out along each face at deck level, under the parapets.",
    'Parapets in two halves': "Each parapet in two pieces, like the wing walls: the outer half (the face of "
                              "the bridge) and the inner half (the deck side). Each is one piece - its wall, "
                              "half of each pillar and half the coping - with a flat glue face, so it lies "
                              "flat on the bed. Brick each on its own side, then glue them together.",
    'Pillars at the parapet ends': "Square pillars at each end of each parapet.",
    'End walls (close the ends)': "Walls across each end of the bridge, under the deck, closing it in.",
    'Coping on the wing walls': "Coping stones along the sloping top of each wing wall - the same thickness "
                                "(T) and overhang (U) as the parapet coping. In two halves, each half carries "
                                "its half of the coping, so it still lies flat on its glue face.",
    'Wing walls in two halves': "Each wing wall in two pieces, each half as thick: an outer half and an inner "
                                "half. Brick each one on its own face with Brick & Block Studio, then glue them "
                                "back to back - bricks both sides.",
    'Wing walls': "Walls out from the corners of the bridge, holding back the embankment: in line with the "
                  "faces, or splayed out.",
    'Arches to fill': "Which arches get an infill wall: 'all', or their numbers (1, 3, 5 or 2-4), counted "
                      "from the start of the bridge. Empty = none.",
    'Fill on the': "Which face the infill goes on: the front, the back, or both.",
    'Door': "Where the door is: in the middle, or to the left or right (AJ from the side).",
    'Windows each side of the door': "How many windows each side of the door (with no door, across the "
                                     "arch). Windows that don't fit are left out and you're told.",
    'Fanlight in the arch': "A window following the curve of the arch, over the door and windows.",
    'Quick front': "Fills in the door, windows and fanlight for a kind of front. Then fine-tune them.",
    'Split each barrel at the crown': "Each barrel in two halves, for big arches that won't fit the print "
                                      "bed in one.",
    'Paint the pieces': "Stone, brick and infill colours, so the pieces are easy to tell apart. Untick to "
                        "leave the colours to Layers & Colours.",
    'Line is at': "If you select a line along the middle of the bridge: is it on the ground, or at the top "
                  "of the deck (along the track)?",
    'Make it as long as the line': "Works out the span (A) so the bridge, abutments and all, is as long as "
                                   "the line you selected.",
    'Build the bridge': "Builds the bridge - along the line you selected (along the middle of the bridge), "
                        "or at the middle of the model with nothing selected.",
    'Add infill only': "Fills the arches listed on the Arch infill page of the last bridge you built, with "
                       "the front set there now - so different arches can have different fronts.",
    'Show / hide...': "Opens the Show / Hide window on its Bridges tab: hide the deck, parapets, face walls "
                      "or infill to get at the rest.",
}

INFO_TEXT = ("<b>How to use it</b><br>"
             "Go through 'Start here', or set the pages and click 'Build the bridge'. Select a line first "
             "(drawn along the middle of the bridge, from one end to the other) and it's built along it - "
             "ticked, 'Make it as long as the line' works out the span to fit. With nothing selected it's "
             "built at the middle of the model.<br><br>"
             "<b>Skew</b><br>"
             "A skew angle (AD) slants the piers and barrels, for a bridge crossing a road, railway or "
             "river at an angle. The span (A) is measured along the face.<br><br>"
             "<b>Arch infill</b><br>"
             "List the arches to fill on the Arch infill page. Each fill is a plain wall with the door, "
             "window and fanlight holes cut - brick it with Brick & Block Studio, and put your Period Doors "
             "and Period Windows in the holes. For different fronts: build the bridge, then pick another "
             "front, list the other arches and click 'Add infill only' - it fits the last bridge you built.<br><br>"
             "<b>Printing</b><br>"
             "Every piece is its own group: in Scale Studio's Pieces page pick 'Every group with faces "
             "(smallest pieces)' and tick 'Lay each piece flat'. The arch rings print flat, joints up; the "
             "barrels print standing on their end, with no supports.<br><br>"
             "Sizes are real-world mm - Scale Studio takes it down to your model scale.")

PRINT_NOTE = ("Every piece is its own group, straight in the bridge's group: in Scale Studio's Pieces page "
              "pick 'Every group with faces (smallest pieces)' or 'Groups 1 level in', and tick 'Lay each "
              "piece flat'.")

# which settings make each kind of piece - looked up by the piece's name when you click on it
PIECE_KEYS = [
    ("ring", ('ring_depth', 'vous_w', 'joint', 'ring_proud', 'key_w', 'key_up')),
    ("barrel", ('barrel_t', 'span', 'rise')),
    ("pier side", ('side_t', 'height')),
    ("cutwater", ('cut_out', 'cut_h', 'pier_w')),
    ("deck", ('deck_t', 'width', 'cover')),
    ("end wall", ('end_t',)),
    ("parapet", ('par_h', 'par_t')),
    ("coping", ('cope_t', 'cope_over')),
    ("string course", ('str_h', 'str_out')),
    ("pillar", ('pil_w', 'pil_up')),
    ("wing wall", ('wing_len', 'wing_ang', 'wing_end')),
    ("infill", ('fill_back', 'fill_t', 'door_w', 'door_h', 'win_w', 'win_h', 'win_sill', 'fan_border')),
    ("face wall", ('wall_t', 'height', 'span', 'pier_w', 'abut_len')),
]
_PIECE_STARTS = ("Arch ", "Pier ", "Face wall", "Deck", "End wall", "Parapet", "Coping", "String course",
                 "Pillar", "Wing wall")


def piece_keys(name):
    name = str(name or '')
    if not name.startswith(_PIECE_STARTS):
        return ()
    low = name.lower()
    for word, keys in PIECE_KEYS:
        if word in low:
            return keys
    return ()


def _auto_sizes(v):
    """What the boxes left at 0 come to."""
    S = _f(v, 'span')
    shape = v.get('shape', 'semi')
    rise = {'semi': S / 2.0, 'segmental': S / 4.0, 'elliptical': S / 3.0, 'pointed': S * math.sqrt(3.0) / 2.0,
            'tudor': S / 3.0, 'horseshoe': None, 'flat': None}.get(shape)
    style = v.get('ring_style', 'brick')
    rd = _f(v, 'ring_depth')
    tot = rd * (1 if style == 'stone' else max(1, _i(v, 'rings')))
    return {'rise': rise, 'key_w': max(_f(v, 'vous_w') * (1.6 if style == 'stone' else 6.0), rd * 0.6),
            'key_up': tot * 0.2, 'cut_out': _f(v, 'pier_w') / 2.0, 'cut_h': _f(v, 'height'),
            'fan_bottom': _f(v, 'height')}


UI_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_bridges_arches.json")


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


def _safe_name(name):
    return "".join(c if c.isalnum() or c in " -_" else "_" for c in name).strip() or "preset"


def load_presets():
    out = {}
    try:
        for fn in sorted(os.listdir(PRESET_DIR)):
            if fn.lower().endswith(".json"):
                try:
                    with open(os.path.join(PRESET_DIR, fn), "r", encoding="utf-8") as f:
                        d = json.load(f)
                    if isinstance(d, dict):
                        out[d.get('name') or fn[:-5]] = d
                except Exception:
                    pass
    except Exception:
        pass
    return out


def save_preset(name, values):
    os.makedirs(PRESET_DIR, exist_ok=True)
    d = {'name': name}
    d.update({k: values[k] for k in DEFAULTS if k in values})
    with open(os.path.join(PRESET_DIR, _safe_name(name) + ".json"), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)


# colours: what each kind of piece is painted (if 'Paint the pieces' is ticked)
PAINT = {'face': ("Stonework", (196, 178, 150)), 'side': ("Stonework", (196, 178, 150)),
         'end': ("Stonework", (196, 178, 150)), 'wing': ("Stonework", (196, 178, 150)),
         'deck': ("Deck", (120, 118, 112)), 'barrel': ("Barrel", (170, 160, 145)),
         'ring': ("Arch ring", (168, 86, 60)), 'cutwater': ("Dressed stone", (214, 204, 184)),
         'parapet': ("Stonework", (196, 178, 150)), 'coping': ("Dressed stone", (214, 204, 184)),
         'string': ("Dressed stone", (214, 204, 184)), 'pillar': ("Dressed stone", (214, 204, 184)),
         'infill': ("Arch infill", (226, 214, 192))}
STONE_RING = ("Stone ring", (214, 204, 184))


# ---------------------------------------------------------------------------
# The preview: the front of the bridge, and the plan underneath
# ---------------------------------------------------------------------------
class BridgePreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 260)
        self.elev, self.plan = [], []
        self.msg = ""
        self.caption = ""

    def show_bridge(self, v):
        try:
            L_ = bridge_layout(v)
            el, pl = [], []
            stone, ring, keyc = (221, 210, 188), (176, 98, 70), (232, 196, 150)
            if v.get('ring_style') == 'stone':
                ring, keyc = (200, 188, 166), (226, 214, 190)
            Zd, L, W = L_.Zd, L_.L, L_.W
            # the wing walls, seen from the front (out past each end)
            if v.get('wing', 'none') != 'none':
                phi = math.radians(_f(v, 'wing_ang')) if v.get('wing') == 'splayed' else 0.0
                lw = _f(v, 'wing_len') * math.cos(phi)
                he = min(_f(v, 'wing_end'), Zd)
                el.append(([(0.0, 0.0), (-lw, 0.0), (-lw, he), (0.0, Zd)], (205, 196, 176), []))
                el.append(([(L, 0.0), (L + lw, 0.0), (L + lw, he), (L, Zd)], (205, 196, 176), []))
            el.append((L_.face, stone, []))
            for x0 in L_.xs:
                if L_.style != 'none':
                    el.append((_shift(L_.ring_band, x0, L_.H), ring, []))
                for b in L_.blocks:
                    el.append((_shift(b, x0, L_.H), tuple(min(255, c + 22) for c in ring), []))
                if L_.key:
                    el.append((_shift(L_.key, x0, L_.H), keyc, []))
            for xa, xb, co, ch in L_.cutwaters:
                el.append(([(xa, 0.0), (xb, 0.0), (xb, ch), ((xa + xb) / 2.0, ch + co), (xa, ch)],
                           (232, 224, 206), []))
            want, _why = parse_fill(v.get('fill', ''), L_.n)
            if v.get('fill_side', 'front') != 'back':
                for k in want:
                    o, h, _n = infill_front(L_, v, k - 1)
                    el.append((o, (238, 230, 212), h))
            ph, pt, ct = _f(v, 'par_h'), _f(v, 'par_t'), _f(v, 'cope_t')
            pw = max(_f(v, 'pil_w'), pt) if v.get('pillars') else 0.0
            if v.get('string', True):
                el.append((rect(0.0, Zd - _f(v, 'str_h'), L, Zd), (230, 222, 204), []))
            if ph > ct + 1.0:
                el.append((rect(pw, Zd, L - pw, Zd + ph - ct), stone, []))
                if ct > 0:
                    el.append((rect(pw, Zd + ph - ct, L - pw, Zd + ph),
                               (236, 230, 216), []))
                if pw:
                    top = Zd + ph + _f(v, 'pil_up')
                    el.append((rect(0.0, Zd, pw, top), (236, 230, 216), []))
                    el.append((rect(L - pw, Zd, L, top), (236, 230, 216), []))
            # the plan: the bridge from above, with the skew; the front face at the bottom
            t = math.tan(math.radians(L_.skew))

            def sk(x, y):
                return (x + (y - W / 2.0) * t, y)
            pl.append(([sk(0.0, 0.0), sk(L, 0.0), sk(L, W), sk(0.0, W)], stone, []))
            for x0 in L_.xs:
                lo = -horseshoe_out(L_.shape, L_.S)
                pl.append(([sk(x0 + lo, L_.wt), sk(x0 + L_.S - lo, L_.wt), sk(x0 + L_.S - lo, W - L_.wt),
                            sk(x0 + lo, W - L_.wt)], (150, 140, 128), []))
            for xa, xb, co, ch in L_.cutwaters:
                pl.append(([sk(xa, 0.0), sk((xa + xb) / 2.0, -co), sk(xb, 0.0)], (232, 224, 206), []))
                pl.append(([sk(xa, W), sk((xa + xb) / 2.0, W + co), sk(xb, W)], (232, 224, 206), []))
            if v.get('wing', 'none') != 'none':
                phi = math.radians(_f(v, 'wing_ang')) if v.get('wing') == 'splayed' else 0.0
                lw = _f(v, 'wing_len')
                for end in ('start', 'end'):
                    for side in ('front', 'back'):
                        base, d, m = wing_frame(end, side, phi, L, W)
                        wt = L_.wt
                        q = [base, (base[0] + d[0] * lw, base[1] + d[1] * lw),
                             (base[0] + d[0] * lw + m[0] * wt, base[1] + d[1] * lw + m[1] * wt),
                             (base[0] + m[0] * wt, base[1] + m[1] * wt)]
                        pl.append(([sk(*p) for p in q], (205, 196, 176), []))
            self.elev, self.plan = el, pl
            np_ = sum(len(b) for _k, b in bridge_pieces(L_, v, parts=True, infill=True)[0]) \
                if L_.n <= 12 else None
            self.caption = "%d arch%s - %.1f m long, %.1f m to the deck%s" % (
                L_.n, "" if L_.n == 1 else "es", L / 1000.0, Zd / 1000.0,
                (" - %d pieces" % np_) if np_ else "")
            self.msg = ""
        except Exception as e:
            self.elev, self.plan, self.msg = [], [], str(e)
        self.update()

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen, QFont, QPainterPath
        from PySide6.QtCore import QPointF, Qt
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bg = QColor(246, 246, 242)
        p.fillRect(self.rect(), bg)
        if not self.elev:
            p.drawText(self.rect(), Qt.AlignCenter, self.msg or "No preview")
            p.end()
            return
        ex = [q[0] for it in self.elev for q in it[0]]
        ez = [q[1] for it in self.elev for q in it[0]]
        px = [q[0] for it in self.plan for q in it[0]]
        py = [q[1] for it in self.plan for q in it[0]]
        x0, x1 = min(ex + px), max(ex + px)
        eh, ph = (max(ez) - min(ez)) or 1.0, (max(py) - min(py)) or 1.0
        h_cap, gap = 18, 22
        w, h = self.width() - 20, self.height() - 20 - h_cap - gap
        sc = min(w / ((x1 - x0) or 1.0), h / (eh + ph))
        ox = 10 + (w - (x1 - x0) * sc) / 2.0 - x0 * sc
        top = 10 + h_cap

        def draw(items, oy):
            for k, (pts, rgb, holes) in enumerate(items):
                col = QColor(*rgb)
                path = QPainterPath()
                path.addPolygon(QPolygonF([QPointF(ox + x * sc, oy - y * sc) for x, y in pts]))
                path.closeSubpath()
                for hl in holes:
                    path.addPolygon(QPolygonF([QPointF(ox + x * sc, oy - y * sc) for x, y in hl]))
                    path.closeSubpath()
                path.setFillRule(Qt.OddEvenFill)
                p.setBrush(col)
                p.setPen(QPen(col.darker(165), 0.7))
                p.drawPath(path)
        draw(self.elev, top + max(ez) * sc)
        oy2 = top + eh * sc + gap + max(py) * sc
        # the plan is drawn with the front face at the bottom
        flipped = [([(x, -y) for x, y in pts], rgb, h) for pts, rgb, h in self.plan]
        draw(flipped, oy2 - (max(py) + min(py)) * sc)
        f = QFont()
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(50, 50, 50))
        p.drawText(8, 4, self.width() - 16, h_cap, Qt.AlignLeft | Qt.AlignVCenter, self.caption)
        f.setBold(False)
        p.setFont(f)
        p.setPen(QColor(110, 110, 110))
        p.drawText(8, int(top + eh * sc + 2), 200, gap, Qt.AlignLeft | Qt.AlignVCenter, "Plan (from above)")
        p.end()


# ---------------------------------------------------------------------------
# The keys: what each lettered size is
# ---------------------------------------------------------------------------
def _key_tools(p):
    from PySide6.QtGui import QColor, QPen
    from PySide6.QtCore import QPointF, QRectF, Qt
    red = QColor(200, 40, 40)

    def dim(x1, y1, x2, y2, letter, tx, ty):
        p.setPen(QPen(red, 1.1))
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        ang = math.atan2(y2 - y1, x2 - x1)
        for (x, y, a) in ((x1, y1, ang), (x2, y2, ang + math.pi)):
            for s in (0.45, -0.45):
                p.drawLine(QPointF(x, y), QPointF(x + 6 * math.cos(a + s), y + 6 * math.sin(a + s)))
        p.setPen(red)
        p.drawText(QRectF(tx - 12, ty - 9, 24, 18), Qt.AlignCenter, letter)

    def label(x, y, letter):
        p.setPen(red)
        p.drawText(QRectF(x - 12, y - 9, 24, 18), Qt.AlignCenter, letter)
    return dim, label


class KeyDrawing(QWidget):
    """The bridge from the front and from above, with the lettered sizes."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 560)

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath, QPolygonF
        from PySide6.QtCore import QPointF, QRectF, Qt
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 246))
        k = min(self.width() / 360.0, self.height() / 560.0)
        p.scale(k, k)
        f = QFont()
        f.setBold(True)
        f.setPointSizeF(8.5)
        p.setFont(f)
        dim, label = _key_tools(p)
        stone, ring = QColor(225, 214, 192), QColor(176, 98, 70)
        p.setPen(QColor(60, 60, 60))
        p.drawText(QRectF(10, 2, 340, 16), Qt.AlignLeft, "From the front")
        # ground at y = 250, springing at 175, arch radius 45 (span 90), deck top at 95
        G, SP, R = 250.0, 175.0, 45.0
        xa = [60.0, 60.0 + 90 + 30]                      # two arches
        DK = 95.0
        path = QPainterPath()
        path.moveTo(20, G)
        for x in xa:
            path.lineTo(x, G)
            path.lineTo(x, SP)
            path.arcTo(QRectF(x, SP - R, 2 * R, 2 * R), 180, -180)
            path.lineTo(x + 2 * R, G)
        path.lineTo(320, G)
        path.lineTo(320, DK)
        path.lineTo(20, DK)
        path.closeSubpath()
        p.setPen(QPen(QColor(120, 110, 95), 0.8))
        p.setBrush(stone)
        p.drawPath(path)
        for x in xa:                                     # the rings
            rp = QPainterPath()
            rp.arcMoveTo(QRectF(x - 14, SP - R - 14, 2 * R + 28, 2 * R + 28), 180)
            rp.arcTo(QRectF(x - 14, SP - R - 14, 2 * R + 28, 2 * R + 28), 180, -180)
            rp.lineTo(x + 2 * R, SP)
            rp.arcTo(QRectF(x, SP - R, 2 * R, 2 * R), 0, 180)
            rp.closeSubpath()
            p.setBrush(ring)
            p.drawPath(rp)
        cx = xa[1] + R                                   # keystone on the second arch
        p.setBrush(QColor(232, 196, 150))
        p.drawRect(QRectF(cx - 6, SP - R - 20, 12, 22))
        # parapet, coping, string course, pillar
        p.setBrush(stone)
        p.drawRect(QRectF(44, DK - 34, 276, 34))
        p.setBrush(QColor(236, 230, 216))
        p.drawRect(QRectF(44, DK - 40, 276, 6))
        p.drawRect(QRectF(20, DK - 48, 24, 48))
        p.drawRect(QRectF(20, DK, 300, 7))
        # cutwater on the pier between
        px0, px1 = xa[0] + 2 * R, xa[1]
        p.drawPolygon(QPolygonF([QPointF(px0 + 2, G), QPointF(px1 - 2, G), QPointF(px1 - 2, SP + 22),
                                 QPointF((px0 + px1) / 2.0, SP + 8), QPointF(px0 + 2, SP + 22)]))
        p.setFont(f)
        dim(xa[0], G - 8, xa[0] + 2 * R, G - 8, "A", xa[0] + R, G - 18)
        dim(xa[0] + 2 * R + 14, SP, xa[0] + 2 * R + 14, SP - R, "", 0, 0)
        label(xa[0] + R, SP - 20, "B")
        p.setPen(QPen(QColor(200, 40, 40), 0.8, Qt.DashLine))
        p.drawLine(QPointF(xa[0], SP), QPointF(xa[0] + 2 * R, SP))
        dim(30, G, 30, SP, "C", 30, SP + 18)
        dim(px0, G + 10, px1, G + 10, "D", (px0 + px1) / 2.0, G + 20)
        dim(xa[0] - 8, SP + 1, xa[0] - 8 - 0.01, SP + 1, "", 0, 0)
        label(xa[0] - 9, SP - 7, "E")
        label(xa[0] + 26, SP - R + 10, "F")
        label(xa[0] + 10, SP - R + 2, "G")
        label(xa[0] + 2 * R + 6, SP + 8, "H")
        dim(cx - 6, SP - R - 26, cx + 6, SP - R - 26, "J", cx, SP - R - 36)
        label(cx + 16, SP - R - 14, "K")
        dim(20, G + 10, xa[0], G + 10, "L", 40, G + 20)
        label((px0 + px1) / 2.0, SP - 2, "N")
        dim(cx + 30, SP - R - 14, cx + 30, DK, "P", cx + 42, SP - R - 34)
        dim(300, DK, 300, DK + 7, "", 0, 0)
        label(310, DK + 14, "V")
        dim(330, DK, 330, DK - 40, "R", 340, DK - 20)
        label(32, DK - 54, "Z")
        label(32, DK - 24, "Y")
        label(250, DK - 46, "T")
        # ---- the plan
        p.setPen(QColor(60, 60, 60))
        p.drawText(QRectF(10, 290, 340, 16), Qt.AlignLeft, "From above (the plan)")
        Y0, Y1 = 330.0, 440.0                            # back face, front face
        t = 0.35

        def sk(x, y):
            return QPointF(x + ((Y0 + Y1) / 2.0 - y) * t, y)
        p.setPen(QPen(QColor(120, 110, 95), 0.8))
        p.setBrush(stone)
        p.drawPolygon(QPolygonF([sk(60, Y1), sk(300, Y1), sk(300, Y0), sk(60, Y0)]))
        p.setBrush(QColor(150, 140, 128))
        for x in (100.0, 210.0):
            p.drawPolygon(QPolygonF([sk(x, Y1 - 8), sk(x + 60, Y1 - 8), sk(x + 60, Y0 + 8), sk(x, Y0 + 8)]))
        p.setBrush(QColor(232, 224, 206))
        p.drawPolygon(QPolygonF([sk(160, Y1), sk(185, Y1 + 18), sk(210, Y1)]))
        p.setBrush(QColor(205, 196, 176))                # wing walls
        p.drawPolygon(QPolygonF([sk(60, Y1), sk(60 - 40, Y1 + 28), sk(60 - 45, Y1 + 22), sk(60 - 6, Y1 - 6)]))
        p.drawPolygon(QPolygonF([sk(300, Y1), sk(300 + 40, Y1 + 28), sk(300 + 45, Y1 + 22),
                                 sk(300 + 6, Y1 - 6)]))
        p.setBrush(QColor(236, 230, 216))
        p.drawRect(QRectF(sk(60, Y1).x(), Y1 - 2, 240, 6))
        q0, q1 = sk(70, Y1), sk(70, Y0)
        dim(q1.x() - 14, Y0, q0.x() - 14, Y1, "W", q0.x() - 4, (Y0 + Y1) / 2.0)
        p.setPen(QPen(QColor(200, 40, 40), 0.8, Qt.DashLine))
        p.drawLine(QPointF(sk(160, Y1).x(), Y1), QPointF(sk(160, Y1).x(), Y0))
        label(sk(160, Y1).x() + 14, Y0 + 14, "AD")
        label(186, Y1 + 26, "M")
        label(28, Y1 + 34, "AA")
        label(60 + 6, Y1 + 34, "AB")
        label(sk(300, Y1).x() - 20, Y1 + 12, "X")
        label(sk(300, Y1).x() - 46, Y1 + 12, "U")
        label(sk(300, Y1).x() - 70, Y1 + 12, "S")
        p.setPen(QColor(90, 90, 90))
        f.setBold(False)
        f.setPointSizeF(8.0)
        p.setFont(f)
        p.drawText(QRectF(10, 470, 340, 90), Qt.TextWordWrap,
                   "Q deck thickness and AC (the height at the far end of the wing walls) aren't drawn. "
                   "E is the depth of one ring, F the width of one brick or stone, G the joint. "
                   "The front face is at the bottom of the plan.")
        p.end()


class KeyDrawing2(QWidget):
    """An arch with its infill: the door, windows and fanlight."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 420)

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
        from PySide6.QtCore import QPointF, QRectF, Qt
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 246))
        k = min(self.width() / 360.0, self.height() / 420.0)
        p.scale(k, k)
        f = QFont()
        f.setBold(True)
        f.setPointSizeF(8.5)
        p.setFont(f)
        dim, label = _key_tools(p)
        p.setPen(QColor(60, 60, 60))
        p.drawText(QRectF(10, 2, 340, 16), Qt.AlignLeft, "An arch with its infill, from the front")
        G, SP, R, X = 300.0, 160.0, 120.0, 60.0
        # the infill: the arch opening, with the door cut up from the bottom
        path = QPainterPath()
        path.moveTo(X, G)
        path.lineTo(X, SP)
        path.arcTo(QRectF(X, SP - R, 2 * R, 2 * R), 180, -180)
        path.lineTo(X + 2 * R, G)
        dx0, dx1, dh = X + 95, X + 145, G - 110
        path.lineTo(dx1, G)
        path.lineTo(dx1, dh)
        path.lineTo(dx0, dh)
        path.lineTo(dx0, G)
        path.closeSubpath()
        bd = 16.0
        fan = QPainterPath()
        fan.moveTo(X + bd, SP)
        fan.arcTo(QRectF(X + bd, SP - R + bd, 2 * R - 2 * bd, 2 * R - 2 * bd), 180, -180)
        fan.closeSubpath()
        w0 = (X + 25, G - 140, 50, 70)
        w1 = (X + 2 * R - 75, G - 140, 50, 70)
        for x_, y_, ww, hh in (w0, w1):
            path.addRect(QRectF(x_, y_, ww, hh))
        path.addPath(fan)
        path.setFillRule(Qt.OddEvenFill)
        p.setPen(QPen(QColor(120, 110, 95), 0.9))
        p.setBrush(QColor(238, 230, 212))
        p.drawPath(path)
        # the ring round it
        p.setBrush(QColor(176, 98, 70))
        rp = QPainterPath()
        rp.arcMoveTo(QRectF(X - 18, SP - R - 18, 2 * R + 36, 2 * R + 36), 180)
        rp.arcTo(QRectF(X - 18, SP - R - 18, 2 * R + 36, 2 * R + 36), 180, -180)
        rp.lineTo(X + 2 * R, SP)
        rp.arcTo(QRectF(X, SP - R, 2 * R, 2 * R), 0, 180)
        rp.closeSubpath()
        p.drawPath(rp)
        p.setPen(QPen(QColor(120, 110, 95), 0.8))
        p.drawLine(QPointF(10, G), QPointF(350, G))
        dim(dx0, dh - 8, dx1, dh - 8, "AG", (dx0 + dx1) / 2.0, dh - 18)
        dim(dx1 + 8, G, dx1 + 8, dh, "AH", dx1 + 22, (G + dh) / 2.0 + 20)
        dim(X, G - 10, dx0, G - 10, "AJ", (X + dx0) / 2.0, G - 20)
        dim(w0[0], w0[1] - 8, w0[0] + w0[2], w0[1] - 8, "AK", w0[0] + w0[2] / 2.0, w0[1] - 18)
        dim(w1[0] + w1[2] + 8, w1[1], w1[0] + w1[2] + 8, w1[1] + w1[3], "AL", w1[0] + w1[2] + 22, w1[1] + 30)
        dim(w0[0] - 8, G, w0[0] - 8, w0[1] + w0[3], "AM", w0[0] - 22, G - 20)
        dim(X + R, SP - R, X + R, SP - R + bd, "", 0, 0)
        label(X + R + 16, SP - R + 8, "AN")
        dim(X + 2 * R + 30, G, X + 2 * R + 30, SP, "AP", X + 2 * R + 44, (G + SP) / 2.0)
        # a section through the arch, to show the set back and the thickness
        p.setPen(QColor(60, 60, 60))
        p.drawText(QRectF(10, 318, 340, 16), Qt.AlignLeft, "Seen from the side, through the arch")
        Y0 = 350.0
        p.setPen(QPen(QColor(120, 110, 95), 0.8))
        p.setBrush(QColor(225, 214, 192))
        p.drawRect(QRectF(40, Y0, 280, 12))              # the barrel over
        p.setBrush(QColor(238, 230, 212))
        p.drawRect(QRectF(80, Y0 + 12, 14, 50))          # the infill
        p.drawLine(QPointF(40, Y0 + 62), QPointF(320, Y0 + 62))
        dim(40, Y0 + 70, 80, Y0 + 70, "AE", 60, Y0 + 80)
        dim(80, Y0 + 30, 94, Y0 + 30, "", 0, 0)
        label(108, Y0 + 30, "AF")
        p.setPen(QColor(90, 90, 90))
        f.setBold(False)
        p.setFont(f)
        p.drawText(QRectF(140, Y0 + 14, 210, 40), Qt.TextWordWrap, "The face of the bridge is on the left.")
        p.end()


# --- Eddy's 3D plugins: the 'Start here' page - a few steps, one at a time, with Back and Next ---
class StartHere:
    """The 'Start here' page: steps to go through one at a time. Each step has its own copies of the boxes
    from the other pages ('mirrors'), kept in step with them both ways - so filling in a step fills in the
    page it belongs to, and the other pages are still there to fine-tune afterwards.
    steps: [(title, words, [item...])] where an item is one of
      ('spin', key_in_dlg_sp)              a size box from dlg.sp
      ('combo', label, combo)              a drop-down list
      ('check', tick)                      a tick box
      ('line', label, line_edit)           a text box
      ('spinint', label, int_spin_box)     a whole-number box
      ('note', words)                      a grey note
      ('button', words, callback)          a button
      ('widget', label, widget)            any widget of its own (not mirrored)
    on_show: {step number: callback} - run when that step is shown."""

    def __init__(self, dlg, page, steps, on_show=None, intro=""):
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton, QWidget
        self.dlg = dlg
        self.on_show = on_show or {}
        self.pages = []
        self._sync = False
        lay = QVBoxLayout(page)
        if intro:
            li = QLabel(intro)
            li.setWordWrap(True)
            li.setStyleSheet("color: gray;")
            lay.addWidget(li)
        self.lbl_step = QLabel()
        self.lbl_step.setWordWrap(True)
        lay.addWidget(self.lbl_step)
        for title, words, items in steps:
            w = QWidget()
            fl = QFormLayout(w)
            if words:
                lw = QLabel(words)
                lw.setWordWrap(True)
                fl.addRow(lw)
            for it in items:
                try:
                    self._add(fl, it)
                except Exception as e:
                    print("Start here: a box left out: %s" % e)
            lay.addWidget(w)
            w.setVisible(False)
            self.pages.append((title, w))
        lay.addStretch(1)
        row = QHBoxLayout()
        self.b_back = QPushButton("< Back")
        self.b_next = QPushButton("Next >")
        self.b_back.clicked.connect(lambda: self.go(self.at - 1))
        self.b_next.clicked.connect(lambda: self.go(self.at + 1))
        row.addWidget(self.b_back)
        row.addStretch(1)
        row.addWidget(self.b_next)
        lay.addLayout(row)
        self.at = 0
        self.go(0)

    def _add(self, fl, it):
        from PySide6.QtWidgets import QLabel, QPushButton, QCheckBox, QComboBox, QDoubleSpinBox, QLineEdit, QSpinBox
        kind = it[0]
        if kind == 'note':
            n_ = QLabel(it[1])
            n_.setWordWrap(True)
            n_.setStyleSheet("color: gray;")
            fl.addRow(n_)
        elif kind == 'button':
            b = QPushButton(it[1])
            b.clicked.connect(lambda *_a, f=it[2]: f())
            fl.addRow(b)
        elif kind == 'widget':
            if it[1]:
                fl.addRow(it[1], it[2])
            else:
                fl.addRow(it[2])
        elif kind == 'spin':
            main, lab = self.dlg.sp[it[1]]
            m = AutoSpin()
            m.setDecimals(main.decimals())
            m.setRange(main.minimum(), main.maximum())
            m.setSuffix(main.suffix())
            m.setValue(main.value())
            m.setToolTip(main.toolTip())
            ml = QLabel(lab.text())
            ml.setToolTip(main.toolTip())
            fl.addRow(ml, m)
            self._pair(m.valueChanged, lambda v, mn=main: mn.setValue(v),
                       main.valueChanged, lambda v, mi=m: mi.setValue(v), m)
            self._enable(m, main, ml)
        elif kind == 'spinint':
            main = it[2]
            m = QSpinBox()
            m.setRange(main.minimum(), main.maximum())
            m.setValue(main.value())
            m.setToolTip(main.toolTip())
            fl.addRow(it[1], m)
            self._pair(m.valueChanged, lambda v, mn=main: mn.setValue(v),
                       main.valueChanged, lambda v, mi=m: mi.setValue(v), m)
            self._enable(m, main)
        elif kind == 'combo':
            main = it[2]
            m = QComboBox()
            for i in range(main.count()):
                m.addItem(main.itemText(i), main.itemData(i))
            m.setCurrentIndex(main.currentIndex())
            m.setToolTip(main.toolTip())
            fl.addRow(it[1], m)
            self._pair(m.currentIndexChanged, lambda i, mn=main: mn.setCurrentIndex(i),
                       main.currentIndexChanged, lambda i, mi=m: mi.setCurrentIndex(i), m)
            self._enable(m, main)
        elif kind == 'check':
            main = it[1]
            m = QCheckBox(main.text())
            m.setChecked(main.isChecked())
            m.setToolTip(main.toolTip())
            fl.addRow(m)
            self._pair(m.toggled, lambda on, mn=main: mn.setChecked(on),
                       main.toggled, lambda on, mi=m: mi.setChecked(on), m)
            self._enable(m, main)
        elif kind == 'line':
            main = it[2]
            m = QLineEdit()
            m.setText(main.text())
            m.setPlaceholderText(main.placeholderText())
            m.setToolTip(main.toolTip())
            fl.addRow(it[1], m)
            self._pair(m.textChanged, lambda t, mn=main: mn.setText(t) if mn.text() != t else None,
                       main.textChanged, lambda t, mi=m: mi.setText(t) if mi.text() != t else None, m)
            self._enable(m, main)

    def _pair(self, sig_m, to_main, sig_main, to_m, m):
        """Keeps a mirror and the box it copies in step, both ways, without going round in circles."""
        def a(*args):
            if self._sync:
                return
            self._sync = True
            try:
                to_main(*args)
            finally:
                self._sync = False

        def b(*args):
            if self._sync:
                return
            self._sync = True
            try:
                m.blockSignals(True)
                to_m(*args)
            finally:
                m.blockSignals(False)
                self._sync = False
        sig_m.connect(a)
        sig_main.connect(b)

    def _enable(self, m, main, lab=None):
        """Greyed out when the box it copies is (checked whenever the step is shown)."""
        self._en = getattr(self, '_en', [])
        self._en.append((m, main, lab))

    def refresh_enabled(self):
        for m, main, lab in getattr(self, '_en', []):
            try:
                on = main.isEnabled()
                m.setEnabled(on)
                if lab is not None:
                    lab.setEnabled(on)
            except Exception:
                pass

    def go(self, k):
        k = max(0, min(len(self.pages) - 1, k))
        self.at = k
        for i, (_t, w) in enumerate(self.pages):
            w.setVisible(i == k)
        self.lbl_step.setText("<b>Step %d of %d: %s</b>" % (k + 1, len(self.pages), self.pages[k][0]))
        self.b_back.setEnabled(k > 0)
        self.b_next.setEnabled(k < len(self.pages) - 1)
        f = self.on_show.get(k)
        if f:
            try:
                f()
            except Exception as e:
                print("Start here: %s" % e)
        self.refresh_enabled()
# --- 'Start here' page (end) ---


class TwoRowTabs(QWidget):
    """Pages with their tabs on two rows, so they all show without scrolling across.
    Works like a QTabWidget: addTab, setTabToolTip, currentIndex, setCurrentIndex, currentChanged."""
    try:
        from PySide6.QtCore import Signal as _Signal
        currentChanged = _Signal(int)
    except Exception:
        currentChanged = None

    def __init__(self, rows=2, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QGridLayout, QStackedWidget, QButtonGroup
        self._rows = rows
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self._grid = QGridLayout()
        self._grid.setSpacing(2)
        lay.addLayout(self._grid)
        self._stack = QStackedWidget()
        try:
            from PySide6.QtWidgets import QFrame
            self._stack.setFrameShape(QFrame.StyledPanel)
        except Exception:
            pass
        lay.addWidget(self._stack, 1)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons = []
        self._group.idClicked.connect(self.setCurrentIndex)

    def _relayout(self):
        n = len(self._buttons)
        per = max(1, -(-n // self._rows))         # tabs on each row
        for b in self._buttons:
            self._grid.removeWidget(b)
        for i, b in enumerate(self._buttons):
            self._grid.addWidget(b, i // per, i % per)

    def addTab(self, widget, title):
        b = QPushButton(title.replace("&&", "&"))
        b.setCheckable(True)
        b.setStyleSheet("QPushButton { padding: 3px 8px; }"
                        "QPushButton:checked { font-weight: bold; background-color: palette(base); "
                        "border: 1px solid palette(mid); border-bottom: 2px solid palette(highlight); }")
        i = len(self._buttons)
        self._group.addButton(b, i)
        self._buttons.append(b)
        self._stack.addWidget(widget)
        self._relayout()
        if i == 0:
            b.setChecked(True)
        return i

    def setTabToolTip(self, i, tip):
        if 0 <= i < len(self._buttons):
            self._buttons[i].setToolTip(tip)

    def tabText(self, i):
        return self._buttons[i].text() if 0 <= i < len(self._buttons) else ""

    def count(self):
        return len(self._buttons)

    def currentIndex(self):
        return self._stack.currentIndex()

    def setCurrentIndex(self, i):
        try:
            i = int(i)
        except Exception:
            return
        if not 0 <= i < len(self._buttons) or i == self._stack.currentIndex() and self._buttons[i].isChecked():
            return
        self._buttons[i].setChecked(True)
        self._stack.setCurrentIndex(i)
        try:
            self.currentChanged.emit(i)
        except Exception:
            pass


class BridgeDialog(QDialog):
    def __init__(self, cur, viewport, tool):
        super().__init__(viewport)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.user_presets = load_presets()
        self._busy = False
        lay = QVBoxLayout(self)
        # how to use it, and what the last build did - only shown when Info is pressed
        self.info_box = QWidget()
        ib = QVBoxLayout(self.info_box)
        ib.setContentsMargins(0, 0, 0, 0)
        self.lbl_info = QLabel(INFO_TEXT)
        self.lbl_info.setWordWrap(True)
        ib.addWidget(self.lbl_info)
        self.lbl_report = QLabel()
        self.lbl_report.setWordWrap(True)
        self.lbl_report.setVisible(False)
        ib.addWidget(self.lbl_report)
        self.info_box.setVisible(False)
        lay.addWidget(self.info_box)

        row = QHBoxLayout()
        lay.addLayout(row)
        self.preview = BridgePreview()
        self.left = QTabWidget()
        self.left.addTab(self.preview, "Preview")
        from PySide6.QtWidgets import QScrollArea
        for w_, t_ in ((KeyDrawing(), "Key (A - AD)"), (KeyDrawing2(), "Key (infill)")):
            sc_ = QScrollArea()
            sc_.setWidgetResizable(True)
            sc_.setWidget(w_)
            self.left.addTab(sc_, t_)
        self.left.setTabToolTip(1, "What each lettered size is.")
        self.left.setTabToolTip(2, "The lettered sizes of the arch infill.")
        row.addWidget(self.left, 1)
        self.tabs = TwoRowTabs(2)              # the pages' tabs on two rows, so they all show
        row.addWidget(self.tabs, 1)
        self.sp = {}
        self.page_of = {}
        self.page_start = QWidget()
        self.tabs.addTab(self.page_start, "Start here")

        def page(title):
            w = QWidget()
            fl = QFormLayout(w)
            self.tabs.addTab(w, title)
            return fl

        def spins(fl, fields):
            for key, label, lo, hi, dec, tip, unit in fields:
                s = AutoSpin()
                s.setDecimals(dec)
                s.setRange(lo, hi)
                s.setKeyboardTracking(True)
                s.setSuffix(unit)
                lab = QLabel(label)
                s.setToolTip(tip)
                lab.setToolTip(tip)
                fl.addRow(lab, s)
                self.sp[key] = (s, lab)
                self.page_of[key] = self.tabs.count() - 1
                s.valueChanged.connect(self.changed)

        def combo(fl, label, items, tip):
            c = QComboBox()
            for lab, k in items:
                c.addItem(lab, k)
            c.setToolTip(tip)
            lb = QLabel(label)
            lb.setToolTip(tip)
            fl.addRow(lb, c)
            c.currentIndexChanged.connect(self.changed)
            return c

        def check(fl, text, tip):
            c = QCheckBox(text)
            c.setToolTip(tip)
            fl.addRow(c)
            c.toggled.connect(self.changed)
            return c

        def intspin(fl, label, lo, hi, tip):
            s = QSpinBox()
            s.setRange(lo, hi)
            s.setToolTip(tip)
            lb = QLabel(label)
            lb.setToolTip(tip)
            fl.addRow(lb, s)
            s.valueChanged.connect(self.changed)
            return s

        def note(fl, text):
            n_ = QLabel(text)
            n_.setWordWrap(True)
            n_.setStyleSheet("color: gray;")
            fl.addRow(n_)
            return n_

        # ---- Arch
        fa = page("Arch")
        self.cb_shape = combo(fa, "Arch shape", SHAPES, EDDY_TIPS['Arch shape'])
        self.cb_ring = combo(fa, "Ring", RING_STYLES, EDDY_TIPS['Ring'])
        self.sp_rings = intspin(fa, "Rings of bricks", 1, 8, EDDY_TIPS['Rings of bricks'])
        spins(fa, ARCH_FIELDS)
        self.ck_key = check(fa, "Keystone", EDDY_TIPS['Keystone'])
        self.ck_inwall = check(fa, "Rings built into the face walls", EDDY_TIPS['Rings built into the face walls'])
        self.ck_lining = check(fa, "Arch lining (printed flat, bent in)", EDDY_TIPS['Arch lining'])
        spins(fa, LINING_FIELDS)
        note(fa, "Sizes are real-world mm - Scale Studio takes the finished bridge down to your model scale.")
        # ---- Spans & piers
        fp = page("Spans & piers")
        self.sp_arches = intspin(fp, "Arches", 1, 60, EDDY_TIPS['Arches'])
        spins(fp, PIER_FIELDS[:4])
        self.ck_cut = check(fp, "Cutwaters on the piers", EDDY_TIPS['Cutwaters on the piers'])
        spins(fp, PIER_FIELDS[4:])
        self.lbl_len = note(fp, "")
        # ---- Deck & parapets
        fd = page("Deck & parapets")
        spins(fd, DECK_FIELDS[:7])
        self.ck_string = check(fd, "String course along the faces", EDDY_TIPS['String course along the faces'])
        spins(fd, DECK_FIELDS[7:9])
        self.ck_pil = check(fd, "Pillars at the parapet ends", EDDY_TIPS['Pillars at the parapet ends'])
        self.ck_parone = check(fd, "Parapets in two halves (brick both sides)",
                               EDDY_TIPS['Parapets in two halves'])
        self.cb_cope = combo(fd, "Coping", COPE_STYLES, EDDY_TIPS['Coping'])
        spins(fd, [('cope_len', "Coping stone length", 0.0, 10000.0, 0, EDDY_TIPS['Coping stone length'], MM)])
        self.ck_caps = check(fd, "Caps on the pillars", EDDY_TIPS['Caps on the pillars'])
        spins(fd, DECK_FIELDS[9:])
        # ---- Ends & wing walls
        fe = page("Ends & wing walls")
        self.ck_ends = check(fe, "End walls (close the ends)", EDDY_TIPS['End walls (close the ends)'])
        self.cb_wing = combo(fe, "Wing walls", WINGS, EDDY_TIPS['Wing walls'])
        self.ck_halves = check(fe, "Wing walls in two halves (brick both sides)",
                               EDDY_TIPS['Wing walls in two halves'])
        self.ck_wcope = check(fe, "Coping on the wing walls", EDDY_TIPS['Coping on the wing walls'])
        spins(fe, END_FIELDS)
        note(fe, "The wing walls slope from deck level down to AC at their far end. In two halves, each half "
                 "is a flat piece to brick on its own face - then glue the halves back to back.")
        # ---- Arch infill
        fi = page("Arch infill")
        self.ed_fill = QLineEdit()
        self.ed_fill.setPlaceholderText("e.g. all   or   1, 3, 5   or   2-4   (empty = none)")
        self.ed_fill.setToolTip(EDDY_TIPS['Arches to fill'])
        lb_ = QLabel("Arches to fill")
        lb_.setToolTip(EDDY_TIPS['Arches to fill'])
        fi.addRow(lb_, self.ed_fill)
        self.ed_fill.textChanged.connect(self.changed)
        self.cb_side = combo(fi, "Fill on the", FILL_SIDES, EDDY_TIPS['Fill on the'])
        self.cb_front = QComboBox()
        self.cb_front.addItem("-- pick one to fill in the boxes --", None)
        for lab, d in FRONTS:
            self.cb_front.addItem(lab, lab)
        self.cb_front.setToolTip(EDDY_TIPS['Quick front'])
        lq = QLabel("Quick front")
        lq.setToolTip(EDDY_TIPS['Quick front'])
        fi.addRow(lq, self.cb_front)
        self.cb_front.currentIndexChanged.connect(self.quick_front)
        spins(fi, INFILL_FIELDS[:2])
        self.cb_door = combo(fi, "Door", DOOR_POS, EDDY_TIPS['Door'])
        spins(fi, INFILL_FIELDS[2:5])
        self.sp_win = intspin(fi, "Windows each side of the door", 0, 6, EDDY_TIPS['Windows each side of the door'])
        spins(fi, INFILL_FIELDS[5:8])
        self.ck_fan = check(fi, "Fanlight in the arch", EDDY_TIPS['Fanlight in the arch'])
        spins(fi, INFILL_FIELDS[8:])
        self.lbl_fill = note(fi, "")
        # ---- Place & print
        fz = page("Place & print")
        note(fz, "Select a line along the middle of the bridge, from one end to the other, and it's built "
                 "along it. With nothing selected it's built at the middle of the model.")
        self.cb_line = combo(fz, "Line is at", LINE_AT, EDDY_TIPS['Line is at'])
        self.ck_fit = check(fz, "Make it as long as the line (works out the span)",
                            EDDY_TIPS['Make it as long as the line'])
        spins(fz, PRINT_FIELDS)
        self.ck_split = check(fz, "Split each barrel at the crown", EDDY_TIPS['Split each barrel at the crown'])
        self.ck_paint = check(fz, "Paint the pieces (stone, brick, infill)", EDDY_TIPS['Paint the pieces'])
        note(fz, PRINT_NOTE + " The arch rings print flat, joints up; the barrels standing on their end.")

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
        b_save = QPushButton("Save")
        b_saveas = QPushButton("Save as...")
        self.btn_preset_save = b_save
        b_del = QPushButton("Delete")
        b_dir = QPushButton("Folder")
        for b in (b_save, b_saveas, b_del, b_dir):
            prow.addWidget(b)
        lay.addLayout(prow)
        brow = QHBoxLayout()
        self.b_build = QPushButton("Build the bridge")
        self.b_build.setDefault(True)
        self.b_infill = QPushButton("Add infill only")
        b_close = QPushButton("Close")
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
        brow.addWidget(self.b_build)
        brow.addWidget(self.b_infill)
        self.b_showhide = QPushButton("Show / hide...")
        brow.addWidget(self.b_showhide)
        brow.addStretch(1)
        self.b_info = QPushButton("Info")
        self.b_info.setCheckable(True)
        self.b_info.setChecked(False)
        self.b_info.setToolTip("Shows how to use it, and what the last bridge you built came out like.")
        self.b_info.toggled.connect(self.toggle_info)
        brow.addWidget(self.b_info)
        brow.addWidget(self.cb_lasttab)
        brow.addWidget(b_close)
        lay.addLayout(brow)

        self.cb_preset.currentIndexChanged.connect(self.apply_preset)
        b_save.clicked.connect(self.save_preset)
        b_saveas.clicked.connect(lambda: self.save_preset_as())
        b_del.clicked.connect(self.delete_preset)
        b_dir.clicked.connect(self.open_folder)
        self.b_build.clicked.connect(lambda: self.tool.build(self))
        self.b_infill.clicked.connect(lambda: self.tool.infill_only(self))
        self.b_showhide.clicked.connect(self.open_show_hide)
        b_close.clicked.connect(self.close)
        self.refresh_presets()
        self.set_values(cur)
        self._sel_names = None
        self._lit = []
        try:
            from PySide6.QtCore import QTimer
            self._sel_timer = QTimer(self)
            self._sel_timer.timeout.connect(self.watch_selection)
            self._sel_timer.start(400)
        except Exception:
            pass
        last = _ui_settings().get('last_preset')
        if last and last in self.preset_order():
            self.refresh_presets(select=last)
        self.make_start_here()

    def make_start_here(self):
        """The 'Start here' page: a bridge in six steps."""
        self.lbl_picked = QLabel()
        self.lbl_picked.setWordWrap(True)

        def picked():
            try:
                scene = getattr(self.viewport, 'scene', None)
                n = len(selected_lines(scene)) if scene is not None else 0
            except Exception:
                n = 0
            if n:
                self.lbl_picked.setText("A line is selected - the bridge goes along it.")
                self.lbl_picked.setStyleSheet("color: #2e7d32;")
            else:
                self.lbl_picked.setText("No line selected - it'll go at the middle of the model.")
                self.lbl_picked.setStyleSheet("color: #b35900;")
        try:
            from PySide6.QtCore import QTimer
            self._pick_timer = QTimer(self)
            self._pick_timer.timeout.connect(picked)
            self._pick_timer.start(700)
        except Exception:
            pass
        picked()
        steps = [
            ("What kind of bridge", "Pick a preset to start from, or the arch shape and how many arches.",
             [('combo', "Preset", self.cb_preset), ('combo', "Arch shape", self.cb_shape),
              ('spinint', "Arches", self.sp_arches)]),
            ("How big", "The span of each arch, how high the piers are, and how wide the bridge is.",
             [('spin', 'span'), ('spin', 'rise'), ('spin', 'height'), ('spin', 'width')]),
            ("Skew and rings", "Square, or crossing at an angle? And what the arch rings look like.",
             [('spin', 'skew'), ('combo', "Ring", self.cb_ring), ('spinint', "Rings of bricks", self.sp_rings)]),
            ("Arch infill (if you want it)", "Fill some of the arches with a wall, the door and window holes "
                                             "already cut. Leave it empty for open arches.",
             [('line', "Arches to fill", self.ed_fill), ('combo', "Quick front", self.cb_front),
              ('combo', "Fill on the", self.cb_side),
              ('note', "Fine-tune the door, windows and fanlight on the Arch infill page.")]),
            ("Where it goes", "Select a line along the middle of the bridge (from one end to the other), or "
                              "nothing for the middle of the model.",
             [('widget', None, self.lbl_picked), ('combo', "Line is at", self.cb_line),
              ('check', self.ck_fit)]),
            ("Build it", "Build the bridge.",
             [('button', "Build the bridge", lambda: self.tool.build(self)),
              ('note', "What it made shows under Info. Next: brick the face walls, wing walls and infill "
                       "with Brick & Block Studio, put Period Doors and Period Windows in the infill holes, "
                       "then Scale Studio to print.")]),
        ]
        try:
            self.start = StartHere(self, self.page_start, steps, on_show={4: picked},
                                   intro="Go through the steps with Next - each one fills in the pages to the "
                                         "right, so you can fine-tune them there afterwards.")
        except Exception as e:
            print("%s: 'Start here' page not made: %s" % (PLUGIN_NAME, e))

    def quick_front(self, *_):
        name = self.cb_front.currentData()
        for lab, d in FRONTS:
            if lab == name:
                cur = self.values()
                cur.update(d)
                self.set_values(cur)
                break

    def open_show_hide(self):
        h = _show_hide_hub()
        if h is not None:
            try:
                h.open_show_hide(self.viewport, 'bridges')
                return
            except Exception as e:
                print("%s: Show / Hide window didn't open (%s)" % (PLUGIN_NAME, e))
        QMessageBox.information(self, PLUGIN_NAME, "3D Show / Hide isn't loaded. Edit > Hide works too, or "
                                                   "Ctrl+Z after hiding.")

    # ---- values ----
    def values(self):
        v = dict(shape=self.cb_shape.currentData() or 'semi', ring_style=self.cb_ring.currentData() or 'brick',
                 rings=int(self.sp_rings.value()), arches=int(self.sp_arches.value()),
                 keystone=self.ck_key.isChecked(), rings_in_walls=self.ck_inwall.isChecked(), cutwaters=self.ck_cut.isChecked(),
                 string=self.ck_string.isChecked(), pillars=self.ck_pil.isChecked(),
                 par_halves=self.ck_parone.isChecked(), cope_style=self.cb_cope.currentData() or 'saddle',
                 pil_caps=self.ck_caps.isChecked(),
                 lining=self.ck_lining.isChecked(),
                 end_walls=self.ck_ends.isChecked(), wing_halves=self.ck_halves.isChecked(),
                 wing_cope=self.ck_wcope.isChecked(), wing=self.cb_wing.currentData() or 'none',
                 fill=self.ed_fill.text().strip(), fill_side=self.cb_side.currentData() or 'front',
                 door_pos=self.cb_door.currentData() or 'centre', win_n=int(self.sp_win.value()),
                 fanlight=self.ck_fan.isChecked(), line_at=self.cb_line.currentData() or 'ground',
                 fit_line=self.ck_fit.isChecked(), split_barrel=self.ck_split.isChecked(),
                 paint=self.ck_paint.isChecked())
        for key, (s, _) in self.sp.items():
            v[key] = float(s.value())
        return v

    def set_values(self, d):
        self._busy = True
        try:
            for cb, key in ((self.cb_shape, 'shape'), (self.cb_ring, 'ring_style'), (self.cb_wing, 'wing'),
                            (self.cb_cope, 'cope_style'),
                            (self.cb_side, 'fill_side'), (self.cb_door, 'door_pos'), (self.cb_line, 'line_at')):
                i_ = cb.findData(d.get(key, DEFAULTS[key]))
                cb.setCurrentIndex(max(0, i_))
            for sb, key in ((self.sp_rings, 'rings'), (self.sp_arches, 'arches'), (self.sp_win, 'win_n')):
                sb.setValue(int(d.get(key, DEFAULTS[key])))
            for c, key in ((self.ck_key, 'keystone'), (self.ck_cut, 'cutwaters'), (self.ck_string, 'string'),
                           (self.ck_pil, 'pillars'), (self.ck_ends, 'end_walls'), (self.ck_fan, 'fanlight'),
                           (self.ck_halves, 'wing_halves'), (self.ck_inwall, 'rings_in_walls'),
                           (self.ck_parone, 'par_halves'),
                           (self.ck_caps, 'pil_caps'), (self.ck_lining, 'lining'), (self.ck_wcope, 'wing_cope'),
                           (self.ck_fit, 'fit_line'), (self.ck_split, 'split_barrel'), (self.ck_paint, 'paint')):
                c.setChecked(bool(d.get(key, DEFAULTS[key])))
            self.ed_fill.setText(str(d.get('fill', DEFAULTS['fill']) or ""))
            for key, (s, _) in self.sp.items():
                s.setValue(float(d.get(key, DEFAULTS[key])))
        finally:
            self._busy = False
        self.changed()

    def changed(self, *_):
        if self._busy:
            return
        v = self.values()
        # boxes left at 0 show what they come to
        try:
            if not hasattr(self, '_lab_base'):
                self._lab_base = {}
            for k_, val in _auto_sizes(v).items():
                box_, lab_ = self.sp[k_]
                base_ = self._lab_base.setdefault(k_, lab_.text())
                box_._auto = val
                t_ = ("auto %.0f mm" % val) if val else "auto"
                if k_ == 'fan_bottom':
                    t_ = "at the springing"
                want_ = base_ + ("   (0 = %s)" % t_ if box_.value() <= box_.minimum() else "")
                if lab_.text() != want_:
                    lab_.setText(want_)
        except Exception:
            pass
        _ui_settings_save(last_values={k: v[k] for k in DEFAULTS if k in v})   # opens like this next time
        style = v['ring_style']
        self.sp_rings.setEnabled(style in ('brick', 'plain'))
        for k in ('vous_w', 'joint'):
            self.sp[k][0].setEnabled(style in ('brick', 'stone'))
        self.sp['ring_proud'][0].setEnabled(style != 'none')
        self.ck_key.setEnabled(style in ('brick', 'stone') and v['shape'] != 'flat')
        for k in ('key_w', 'key_up'):
            self.sp[k][0].setEnabled(self.ck_key.isEnabled() and v['keystone'])
        self.sp['rise'][0].setEnabled(v['shape'] in ('segmental', 'elliptical', 'pointed', 'tudor'))
        for k in ('cut_out', 'cut_h'):
            self.sp[k][0].setEnabled(v['cutwaters'] and v['arches'] > 1)
        self.ck_cut.setEnabled(v['arches'] > 1)
        for k in ('str_h', 'str_out'):
            self.sp[k][0].setEnabled(v['string'])
        for k in ('pil_w', 'pil_up'):
            self.sp[k][0].setEnabled(v['pillars'])
        for k in ('wing_len', 'wing_end'):
            self.sp[k][0].setEnabled(v['wing'] != 'none')
        self.sp['wing_ang'][0].setEnabled(v['wing'] == 'splayed')
        self.ck_halves.setEnabled(v['wing'] != 'none')
        self.ck_wcope.setEnabled(v['wing'] != 'none')
        self.sp['end_t'][0].setEnabled(v['end_walls'])
        self.sp['door_side'][0].setEnabled(v['door_pos'] != 'centre' and v['door_w'] > 0)
        self.sp['door_h'][0].setEnabled(v['door_w'] > 0)
        for k in ('win_w', 'win_h', 'win_sill'):
            self.sp[k][0].setEnabled(v['win_n'] > 0)
        for k in ('fan_border', 'fan_bottom'):
            self.sp[k][0].setEnabled(v['fanlight'])
        self.ck_split.setEnabled(v['shape'] != 'flat')
        self.ck_lining.setEnabled(v['shape'] != 'flat')
        for k in ('lin_t',):
            self.sp[k][0].setEnabled(v['lining'] and v['shape'] != 'flat')
        self.ck_caps.setEnabled(v['pillars'])
        try:
            L_ = bridge_layout(v)
            self.lbl_len.setText("The bridge is %.0f mm long (%.1f m), %.0f mm to the top of the deck. A skew "
                                 "slants the piers - the span is measured along the face." % (
                                     L_.L, L_.L / 1000.0, L_.Zd) + ("\n" + "\n".join(L_.problems)
                                                                     if L_.problems else ""))
            want, why = parse_fill(v['fill'], L_.n)
            if why:
                self.lbl_fill.setText(why)
            elif not want:
                self.lbl_fill.setText("No arches listed - they're left open.")
            else:
                notes = []
                for k in want:
                    notes += infill_front(L_, v, k - 1)[2]
                self.lbl_fill.setText("Filling arch%s %s on the %s." % (
                    "" if len(want) == 1 else "es", ", ".join(str(k) for k in want),
                    {'front': "front", 'back': "back", 'both': "front and back"}[v['fill_side']]) +
                    ("\n" + "\n".join(dict.fromkeys(notes)) if notes else ""))
        except Exception as e:
            self.lbl_len.setText(str(e))
        self.preview.show_bridge(v)

    def watch_selection(self):
        """For a piece of ours selected in the model, lights up the boxes that set it."""
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
            for k_ in piece_keys(nm):
                if k_ not in keys:
                    keys.append(k_)
        self.light_up(keys)

    def light_up(self, keys):
        for s_, lab_ in self._lit:
            try:
                s_.setStyleSheet("")
                lab_.setStyleSheet("")
            except Exception:
                pass
        self._lit = []
        for k_ in keys:
            if k_ in self.sp:
                s_, lab_ = self.sp[k_]
                s_.setStyleSheet("background-color: #fff3a0;")
                lab_.setStyleSheet("background-color: #fff3a0; font-weight: bold;")
                self._lit.append((s_, lab_))
        if keys and keys[0] in self.page_of:
            try:
                self.tabs.setCurrentIndex(self.page_of[keys[0]])
            except Exception:
                pass

    def show_report(self, text, bad=False):
        self.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if bad else "#2e7d32"))
        self.lbl_report.setText(text)
        self.lbl_report.setVisible(True)
        if not self.b_info.isChecked():
            self.b_info.setText("Info (!)" if bad else "Info (new)")
            self.b_info.setStyleSheet("font-weight: bold; color: %s;" % ("#b35900" if bad else "#2e7d32"))

    def toggle_info(self, on):
        self.info_box.setVisible(bool(on))
        if on:
            self.b_info.setText("Info")
            self.b_info.setStyleSheet("")
        try:
            self.adjustSize()
        except Exception:
            pass

    # ---- presets ----
    def preset_order(self):
        names = list(BUILTIN_PRESETS) + sorted(n for n in self.user_presets if n not in BUILTIN_PRESETS)
        order = [n for n in _ui_settings().get('preset_order', []) if n in names]
        return order + [n for n in names if n not in order]

    def refresh_presets(self, select=None):
        self.cb_preset.blockSignals(True)
        self.cb_preset.clear()
        self.cb_preset.addItem("-- Custom --", None)
        for name in self.preset_order():
            self.cb_preset.addItem(name + ("  (built-in)" if name in BUILTIN_PRESETS else ""), name)
        for i in range(self.cb_preset.count()):
            if select and self.cb_preset.itemData(i) == select:
                self.cb_preset.setCurrentIndex(i)
        self.cb_preset.blockSignals(False)

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

    def apply_preset(self, *_):
        name = self.cb_preset.currentData()
        _ui_settings_save(last_preset=name or None)
        d = None
        if name and name in BUILTIN_PRESETS:
            d = dict(BUILTIN_PRESETS[name])
        elif name and name in self.user_presets:
            d = dict(self.user_presets[name])
        if d is None:
            return
        cur = self.values()
        for k in cur:
            d.setdefault(k, cur[k])
        self.set_values(d)

    def save_preset(self):
        name = self.cb_preset.currentData()
        if name and name in self.user_presets and name not in BUILTIN_PRESETS:
            if self.save_preset_as(quiet_name=name):
                try:
                    from PySide6.QtCore import QTimer
                    self.btn_preset_save.setText("Saved")
                    QTimer.singleShot(1500, lambda: self.btn_preset_save.setText("Save"))
                except Exception:
                    pass
        else:
            self.save_preset_as(prefill=(name + " (my copy)") if name else "")

    def delete_preset(self):
        name = self.cb_preset.currentData()
        if not name or name not in self.user_presets or name in BUILTIN_PRESETS:
            QMessageBox.information(self, PLUGIN_NAME, "Pick one of your own presets to delete "
                                    "(built-in presets can't be deleted).")
            return
        if QMessageBox.question(self, PLUGIN_NAME, "Delete preset '%s'?" % name) != QMessageBox.Yes:
            return
        try:
            os.remove(os.path.join(PRESET_DIR, _safe_name(name) + ".json"))
        except Exception as e:
            QMessageBox.warning(self, PLUGIN_NAME, "Could not delete it:\n%s" % e)
            return
        self.user_presets = load_presets()
        self.refresh_presets()
        if _ui_settings().get('last_preset') == name:
            _ui_settings_save(last_preset=None)

    def open_folder(self):
        try:
            os.makedirs(PRESET_DIR, exist_ok=True)
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(PRESET_DIR))
        except Exception as e:
            QMessageBox.information(self, PLUGIN_NAME, "Presets folder:\n%s\n\n(%s)" % (PRESET_DIR, e))

    def save_preset_as(self, prefill="", quiet_name=None):
        if quiet_name:
            name, ok = quiet_name, True
        else:
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
            save_preset(name, self.values())
        except Exception as e:
            QMessageBox.warning(self, PLUGIN_NAME, "Could not save the preset:\n%s" % e)
            return False
        self.user_presets = load_presets()
        self.refresh_presets(select=name)
        _ui_settings_save(last_preset=name)
        return True


# ---------------------------------------------------------------------------
# Show / hide: the lines on the Bridges tab of the 3D Show / Hide window
# ---------------------------------------------------------------------------
SHOW_HIDE = [
    ('deck', "Deck", ("deck",)),
    ('parapets', "Parapets, copings, string courses and pillars", ("parapet", "coping", "string course", "pillar")),
    ('faces', "Face walls and arch rings", ("face wall", " - ring ")),
    ('ends', "End walls and wing walls", ("end wall", "wing wall")),
    ('infill', "Arch infill", ("infill",)),
]
SHOW_HIDE_TIPS = {
    'deck': "The deck plate on top, so you can see down inside the bridge.",
    'parapets': "The parapet walls, their copings, the string courses and the pillars.",
    'faces': "Both face walls with their arch rings - to see the barrels and piers inside.",
    'ends': "The walls across the ends of the bridge, and the wing walls.",
    'infill': "The walls filling the arches - with the bridge, and any added afterwards.",
}


def _items(x):
    if x is None:
        return []
    if isinstance(x, dict):
        return list(x.values())
    try:
        return list(x)
    except Exception:
        return []


def _show_hide_hub():
    """3D Show / Hide (the one small window with a tab for each kind of thing), if it's loaded."""
    import sys
    for name, mod in list(sys.modules.items()):
        if mod is not None and (name == "ed3d_show_hide" or name.endswith("_ed3d_show_hide")) \
                and hasattr(mod, 'open_show_hide'):
            return mod
    return None


def show_hide_groups(scene):
    """{key: [groups]} for each line of the Bridges tab: looks inside every bridge we built, and at the
    infill added on its own."""
    found = {k: [] for k, _l, _s in SHOW_HIDE}
    seen = set()

    def match(g):
        name = str(getattr(g, 'name', '') or '').lower()
        for k, _l, words in SHOW_HIDE:
            if any(w in name for w in words):
                found[k].append(g)
                return True
        return False

    def walk(groups, inside, depth=0):
        if depth > 12:
            return
        for g in groups:
            if g is None or id(g) in seen:
                continue
            seen.add(id(g))
            name = str(getattr(g, 'name', '') or '')
            if name.startswith("Bridge - "):
                walk(_items(getattr(g, 'children', None)), True, depth + 1)
                continue
            if inside:
                if match(g):
                    continue
            elif name.startswith("Arch infill"):
                found['infill'].append(g)
                continue
            walk(_items(getattr(g, 'children', None)), inside, depth + 1)
    walk(_items(getattr(scene, 'groups', None)), False)
    return found


# ---------------------------------------------------------------------------
# Lines picked in the model
# ---------------------------------------------------------------------------
def _pos(v):
    for get in (lambda: (v.x(), v.y(), v.z()), lambda: (v.x, v.y, v.z), lambda: (v[0], v[1], v[2])):
        try:
            x, y, z = get()
            return (float(x), float(y), float(z))
        except Exception:
            pass
    return None


def _edge_ends(e):
    for a, b in (('v1', 'v2'), ('a', 'b'), ('start', 'end')):
        pa, pb = getattr(e, a, None), getattr(e, b, None)
        if pa is not None and pb is not None:
            pa, pb = _pos(pa), _pos(pb)
            if pa is not None and pb is not None:
                return pa, pb
    vs = _items(getattr(e, 'vertices', None))
    if len(vs) == 2:
        pa, pb = _pos(vs[0]), _pos(vs[1])
        if pa is not None and pb is not None:
            return pa, pb
    return None


def selected_lines(scene):
    out = []
    for e in _items(getattr(scene, 'selection', None)):
        if getattr(e, 'mesh', None) is not None or hasattr(e, 'loop'):
            continue
        vs = getattr(e, 'vertices', None)
        if vs is not None and not callable(vs) and len(_items(vs)) >= 3:
            continue
        ends = _edge_ends(e)
        if ends and v_len(v_sub(ends[0], ends[1])) > 1e-9:
            out.append(ends)
    return out


def _paint_attrs(scene, name, rgb):
    """The face paint for a kind of piece: a material of its own in the document, set to rgb."""
    colour = (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
    mname = "Eddy - Bridge " + name
    mats = getattr(scene, 'materials', None)
    if mats is not None:
        try:
            mat = mats.get(mname)
            if mat is None:
                from core.materials import Material
                mat = mats[mname] = Material(mname, color=colour, opacity=1.0)
            return dict(mat.face_attrs())
        except Exception as e:
            print("%s: colour: %s" % (PLUGIN_NAME, e))
    return {"color": colour}


class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
class BridgesArchesTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+Shift+B"
    description = "Masonry arch bridges and viaducts: arches of any shape, skew arches, piers, cutwaters, " \
                  "parapets, wing walls - and arches filled in with door and window holes, like railway arches."

    _dialog = None

    def on_activate(self, viewport):
        dlg = BridgesArchesTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.viewport = viewport
                    dlg.raise_()
                    dlg.activateWindow()
                    return
            except Exception:
                pass
        cur = dict(DEFAULTS)
        last = _ui_settings().get('last_values')
        if isinstance(last, dict):
            cur.update({k: last[k] for k in DEFAULTS if k in last})     # the last settings used
        dlg = BridgeDialog(cur, viewport, self)
        BridgesArchesTool._dialog = dlg

        def closed(*_):
            BridgesArchesTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass

    def build(self, dlg):
        v = dlg.values()
        _ui_settings_save(last_values={k: v[k] for k in DEFAULTS if k in v})
        scene = getattr(dlg.viewport, 'scene', None)
        if scene is None:
            return
        lines = selected_lines(scene)
        span, where, fitted = None, "at the middle of the model", ""
        try:
            if lines:
                a, b = lines[0]
                a = (a[0] / SCALE, a[1] / SCALE, a[2] / SCALE)
                b = (b[0] / SCALE, b[1] / SCALE, b[2] / SCALE)
                run_ = math.hypot(b[0] - a[0], b[1] - a[1])
                if run_ < 1.0:
                    QMessageBox.information(dlg, PLUGIN_NAME, "The line you selected goes straight up - draw it "
                                                              "along the middle of the bridge, from end to end.")
                    return
                ang = math.atan2(b[1] - a[1], b[0] - a[0])
                if v.get('fit_line', True):
                    n, P, A = max(1, _i(v, 'arches')), _f(v, 'pier_w'), _f(v, 'abut_len')
                    span = (run_ - 2.0 * A - (n - 1) * P) / n
                    if span < 300.0:
                        QMessageBox.warning(dlg, PLUGIN_NAME, "The line is %.0f mm long - too short for %d arches "
                                                              "with %.0f mm piers and %.0f mm abutments. Fewer "
                                                              "arches, narrower piers or shorter abutments - or "
                                                              "untick 'Make it as long as the line'." % (
                                                                  run_, n, P, A))
                        return
                    fitted = " The span was worked out to fit the line: %.0f mm." % span
                L_ = bridge_layout(v, span)
                oz = a[2] - (L_.Zd if v.get('line_at') == 'deck' else 0.0)
                place = (a[0], a[1], oz, ang)
                where = "along your line"
            else:
                L_ = bridge_layout(v)
                place = (-L_.L / 2.0, 0.0, 0.0, 0.0)
            parts, notes = bridge_pieces(L_, v, parts=True, infill=True)
        except Exception as e:
            QMessageBox.warning(dlg, PLUGIN_NAME, "Couldn't work out the bridge:\n%s" % e)
            return
        top = "Bridge - %d arch%s%s" % (L_.n, "" if L_.n == 1 else "es",
                                       " (viaduct)" if L_.n > 2 else "")
        n_made = self.add_to_scene(dlg.viewport, parts, top, world_mapper(L_, place), v,
                                   world_mapper(L_, place, skew=False))
        if n_made is None:
            return
        keep = {k: v[k] for k in DEFAULTS if k in v}
        keep['_span'] = L_.S
        keep['_place'] = list(place)
        _ui_settings_save(last_bridge=keep)
        total = sum(len(b) for _k, b in parts)
        msg = ("Built a bridge of %d arch%s %s: %.1f m long, %.1f m to the top of the deck - %d pieces.%s" % (
            L_.n, "" if L_.n == 1 else "es", where, L_.L / 1000.0, L_.Zd / 1000.0, total, fitted))
        if L_.skew:
            msg += " Skew %.1f degrees." % L_.skew
        nf = sum(len(b) for k, b in parts if k == "Arch infill")
        if nf:
            msg += ("\n%d infill wall%s, the door and window holes cut - brick %s with Brick & Block Studio and put "
                    "Period Doors and Period Windows in the holes." % (nf, "" if nf == 1 else "s",
                                                                        "it" if nf == 1 else "them"))
        msg += "\n" + PRINT_NOTE
        probs = list(dict.fromkeys(L_.problems + notes))
        if probs:
            msg += "\n" + "\n".join(probs)
        dlg.show_report(msg, bad=bool(probs))

    def infill_only(self, dlg):
        v = dlg.values()
        _ui_settings_save(last_values={k: v[k] for k in DEFAULTS if k in v})
        last = _ui_settings().get('last_bridge')
        if not isinstance(last, dict) or '_place' not in last:
            QMessageBox.information(dlg, PLUGIN_NAME, "Build a bridge first - the infill is fitted to the last "
                                                      "bridge you built.")
            return
        gv = dict(DEFAULTS)
        gv.update({k: last[k] for k in DEFAULTS if k in last})
        gv.update({k: v[k] for k in INFILL_KEYS if k in v})
        try:
            L_ = bridge_layout(gv, last.get('_span'))
            want, why = parse_fill(gv.get('fill', ''), L_.n)
            if not want:
                QMessageBox.information(dlg, PLUGIN_NAME, why or "Type which arches to fill on the Arch infill "
                                                                 "page (for example 2, 4 or all).")
                return
            parts, notes = bridge_pieces(L_, gv, parts=False, infill=True, fill_list=want)
        except Exception as e:
            QMessageBox.warning(dlg, PLUGIN_NAME, "Couldn't work out the infill:\n%s" % e)
            return
        if not parts:
            QMessageBox.warning(dlg, PLUGIN_NAME, "\n".join(notes) or "No infill could be made.")
            return
        place = tuple(last['_place'])
        top = "Arch infill - added (arch%s %s)" % ("" if len(want) == 1 else "es", ", ".join(str(k) for k in want))
        if self.add_to_scene(dlg.viewport, parts, top, world_mapper(L_, place), gv) is None:
            return
        nf = sum(len(b) for _k, b in parts)
        msg = ("Added %d infill wall%s to arch%s %s of the last bridge you built, with this front. %s" % (
            nf, "" if nf == 1 else "s", "" if len(want) == 1 else "es", ", ".join(str(k) for k in want),
            PRINT_NOTE))
        notes = list(dict.fromkeys(notes))
        if notes:
            msg += "\n" + "\n".join(notes)
        dlg.show_report(msg, bad=bool(notes))

    def add_to_scene(self, viewport, parts, top_name, mapper, v, flat_mapper=None):
        """A top group (the bridge) holding a group for each piece - so every piece is one of its own
        for Scale Studio, and lies flat on the bed by itself."""
        stats = {'faces': 0, 'errors': 0, 'err': None}
        tol = 1e-7
        paint = bool(v.get('paint', True))
        stone_ring = v.get('ring_style') == 'stone'

        def make_group(Group, mesh, name):
            try:
                g = Group(mesh, name=name)
            except TypeError:
                g = Group(name)
                g.mesh = mesh
            try:
                g.name = name
            except Exception:
                pass
            return g

        def holder(Group, name, kids):
            try:
                h = Group(name=name)
                if hasattr(h, 'adopt'):
                    h.adopt(kids)
                else:
                    h.children = kids
                h.component = False
                return h
            except Exception:
                return None

        def mutate(scene):
            from core.mesh import Mesh
            from core.group import Group
            attrs = {}
            kinds = []
            loose = []
            for kind, pieces in parts:
                kids = []
                for name, typ, so in pieces:
                    # which way its outside looks, in the model - for Brick & Block Studio
                    out_ = getattr(so, 'outside', None) if getattr(so, 'wall', False) else None
                    if out_ is not None:
                        o0, o1 = mapper((0.0, 0.0, 0.0)), mapper(out_)
                        out_ = [o1[i] - o0[i] for i in range(3)]
                    so = so.mapped(flat_mapper if (flat_mapper and getattr(so, 'flat_world', False)) else mapper)
                    mesh = Mesh()
                    verts = {}

                    def vx(q):
                        k = (round(q[0] / tol), round(q[1] / tol), round(q[2] / tol))
                        if k not in verts:
                            verts[k] = VertexWrapper(*q)
                        return verts[k]
                    made = 0
                    for fi, pts in enumerate(so.faces):
                        try:
                            hs = [[vx(q) for q in h] for h in so.holes.get(fi, ())]
                            if hs:
                                try:
                                    mesh.add_face([vx(q) for q in pts], hs)
                                except TypeError:
                                    f_ = mesh.add_face([vx(q) for q in pts])
                                    for h in hs:
                                        mesh.add_hole(f_, h)
                            else:
                                mesh.add_face([vx(q) for q in pts])
                            made += 1
                        except Exception as e:
                            stats['errors'] += 1
                            stats['err'] = e
                    if not made:
                        continue
                    stats['faces'] += made
                    if paint:
                        pn, rgb = STONE_RING if (typ == 'ring' and stone_ring) else PAINT.get(typ, PAINT['face'])
                        if pn not in attrs:
                            attrs[pn] = _paint_attrs(scene, pn, rgb)
                        for f_ in _items(getattr(mesh, 'faces', None)):
                            try:
                                a_ = dict(getattr(f_, 'attrs', None) or {})
                                a_.update(attrs[pn])
                                f_.attrs = a_
                            except Exception:
                                pass
                    g = make_group(Group, mesh, name)
                    g.component = False
                    try:
                        if not isinstance(getattr(g, 'ext', None), dict):
                            g.ext = {}
                        if out_ is not None:
                            g.ext[OUTSIDE_KEY] = out_      # Brick & Block Studio walls this face
                        else:
                            g.ext[NOT_WALL_KEY] = True     # hidden or not a wall: no walling on it
                    except Exception:
                        pass
                    kids.append(g)
                # straight in the bridge's group, not grouped by kind: each piece is a piece on its own
                # for Scale Studio (four wing walls at different angles can't lie flat as one)
                loose += kids
            if stats['faces'] == 0:
                raise RuntimeError("No faces could be created (%s)." % stats['err'])
            top = holder(Group, top_name, kinds + loose)
            for g in ([top] if top is not None else kinds + loose):
                _ed3d_organise(scene, g)
                # a group holding others goes straight in the list (as Subframe and Brick & Block do)
                if hasattr(scene, 'add_group') and top is None and g in loose:
                    scene.add_group(g)
                else:
                    scene.groups.append(g)
        try:
            viewport.history.execute(SnapshotImport(mutate))
        except Exception as e:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not add the bridge:\n%s" % e)
            return None
        try:
            viewport.notify_scene_changed()
        except Exception:
            pass
        if stats['errors']:
            print("%s: %d faces couldn't be made (%s)" % (PLUGIN_NAME, stats['errors'], stats['err']))
        return stats['faces']


def run(viewport=None):
    BridgesArchesTool().on_activate(viewport)
