# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Roof Tiles for IngeTrazo
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
3D Roof Tiles - roof coverings for IngeTrazo
Select a roof face (any flat face: sloping, flat or upright) and it is covered in
courses of tiles from its lowest edge (the eaves) up, trimmed to the face's outline
and round any openings in it. On a roof that is there already (Floor Plan's roof
slopes, Subframe's roof panels) the tiles go straight onto it, with no backing sheet,
and each slope's tiles go in a group with that slope ('Tiled - Roof slope 1 ...'), so
the slope and its tiles print as one piece. Or click a whole group - the building, or Subframe's
'Roof panels' group - and every roof piece in it is found and tiled at once, ridge
and all. Each slope comes out as its own group, with its tiles, its half of the ridge,
its finials and its flashing each a piece of their own, ready to print apart. Plain tiles, slates, fishtail, bullnose, beaver tail,
club, pantiles and double Roman tiles.

Two ways to make them:
  * Normal - tiles lap over each other like a real roof (each one tilted up on the
    course below).
  * 3D printing - tiles do NOT overlap: each is just its visible part, lying flat on
    the roof face, flat, with grooves between tiles and courses (or stepped courses).

Sizes are real-world millimetres (IngeTrazo stores metres). Ctrl+Alt+R.
"""

import os
import json
import math
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox, QCheckBox,
    QPushButton, QLabel, QMessageBox, QWidget, QInputDialog
)

PLUGIN_NAME = "3D Roof Tiles"
VERSION = "1.9"  # 1.9: the ridge and hips kept apart last time come off too when the roof is tiled again (they stayed); 1.8: tiling a roof that has tiles already swaps them - the old tiles, ridge and finials come off and the new ones go on (Ctrl+Z puts the old ones back); 1.7: on L, T and U roofs the hip tiles stop the tiles only along the hip (no bare strips), tiles no longer cut into bits on odd-shaped slopes (no stray lines), and a wing's ridge gets tiles on both sides; 1.6: hip roofs get hip tiles (the ridge tiles carried down each hip, each slope with its half) and the tiles stop short of them; 1.5: the finials stay on the ridge tiles - one piece to print, not loose bits; 1.4: on a roof that is already there (Floor Plan's roof slopes, Subframe's roof panels) the tiles go straight onto it - no second roof (backing sheet) under them - and into the same group as that slope, so it prints as one piece; 1.3: version number in the standard x.y style (was 12); 12: clicking the whole building no longer tiles the arched heads of built-in windows and doors (walls are left out)


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
PRESET_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Roof Tiles")
Z = (0.0, 0.0, 1.0)

# tile types: sizes in real mm
#   width = cover width (side by side), length = whole tile, gauge = height of each course
#   shape = bottom edge (flat, fish, round, club), profile = cross-section (None, pantile, roman, corrugated)
TILES = [
    ("plain", "Plain tile (clay)", dict(width=165.0, length=265.0, gauge=100.0, thick=12.0,
                                       shape='flat', depth=0.0, profile=None, wave=0.0, bond=True)),
    ("slate", "Slate (Welsh, 500 x 250)", dict(width=250.0, length=500.0, gauge=212.0, thick=6.0,
                                              shape='flat', depth=0.0, profile=None, wave=0.0, bond=True)),
    ("smallslate", "Slate (small, 400 x 200)", dict(width=200.0, length=400.0, gauge=165.0, thick=5.0,
                                                   shape='flat', depth=0.0, profile=None, wave=0.0,
                                                   bond=True)),
    ("fish", "Fishtail tile", dict(width=165.0, length=265.0, gauge=100.0, thick=12.0,
                                   shape='fish', depth=40.0, profile=None, wave=0.0, bond=True)),
    ("bull", "Bullnose tile", dict(width=165.0, length=265.0, gauge=100.0, thick=12.0,
                                   shape='round', depth=35.0, profile=None, wave=0.0, bond=True)),
    ("beaver", "Beaver tail tile", dict(width=180.0, length=380.0, gauge=150.0, thick=14.0,
                                        shape='round', depth=60.0, profile=None, wave=0.0, bond=True)),
    ("club", "Club tile", dict(width=165.0, length=265.0, gauge=100.0, thick=12.0,
                               shape='club', depth=30.0, profile=None, wave=0.0, bond=True)),
    ("pantile", "Pantile", dict(width=210.0, length=342.0, gauge=250.0, thick=14.0,
                                shape='flat', depth=0.0, profile='pantile', wave=45.0, bond=False)),
    ("roman", "Double Roman tile", dict(width=300.0, length=420.0, gauge=345.0, thick=14.0,
                                        shape='flat', depth=0.0, profile='roman', wave=40.0, bond=False)),
    # 10 corrugations of 76 mm across the cover width; sheets lap 150 mm up the slope
    ("tin", "Tin sheet (corrugated)", dict(width=760.0, length=2440.0, gauge=2290.0, thick=6.0,
                                           shape='flat', depth=0.0, profile='corrugated', wave=19.0,
                                           bond=False)),
]
CORRUGATIONS = 10
TILE_INFO = {k: (lab, d) for k, lab, d in TILES}
TURNS = [("Eaves at the lowest edge", 0), ("Turned a quarter", 90), ("Upside down", 180),
         ("Turned three quarters", 270)]

RIDGES = [("round", "Half-round"), ("angular", "Angular"), ("hog", "Hog-back"), ("roll", "Roll-top")]
CRESTS = [("none", "No crest"), ("spikes", "Spikes"), ("fleur", "Fleur-de-lis"), ("scallop", "Scallops"),
          ("trefoil", "Trefoils")]
FINIALS = [("none", "No finials"), ("spike", "Spike"), ("ball", "Ball"), ("fleur", "Fleur-de-lis")]
FINIAL_ENDS = [("both", "Both ends"), ("left", "Left end"), ("right", "Right end")]
FINIAL_FACES = [("out", "Facing out (seen from the gable end)"), ("along", "Along the ridge (seen from the side)")]
RIDGE_DEFAULTS = dict(ridge=False, ridge_style='round', ridge_w=150.0, ridge_h=110.0, ridge_len=450.0,
                      ridge_gap=10.0, crest='none', crest_h=90.0, crest_t=32.0, finial='none',
                      finial_h=350.0, finial_w=90.0, finial_t=32.0, finial_ends='both',
                      finial_face='out', ridge_apart=True)
DEFAULTS = dict(tile='plain', print_mode=True, round_chimneys=True, stepped=False, step=8.0, gap=2.0, cgap=2.0, lift=0.01, backing=40.0, turn=0, flip=False,
                **dict(TILE_INFO['plain'][1], **RIDGE_DEFAULTS))
# ready-made settings for printing at 1:80 with a 0.4 mm nozzle (real-world mm: x 80 = model)
BUILTIN_PRESETS = {
    "1:80 print - slates, flat with grooves": dict(
        TILE_INFO['slate'][1], tile='slate', print_mode=True, stepped=False, thick=24.0,
        gap=32.0, cgap=32.0, backing=40.0, lift=0.01),
    "1:80 print - small slates, flat with grooves": dict(
        TILE_INFO['smallslate'][1], tile='smallslate', print_mode=True, stepped=False, thick=24.0,
        gap=32.0, cgap=32.0, backing=40.0, lift=0.01),
    "1:80 print - plain tiles, flat with grooves": dict(
        TILE_INFO['plain'][1], tile='plain', print_mode=True, stepped=False, thick=24.0,
        gap=32.0, cgap=32.0, backing=40.0, lift=0.01),
}
NUM_KEYS = ('width', 'length', 'gauge', 'thick', 'step', 'gap', 'cgap', 'depth', 'wave', 'backing', 'lift')


# ---------------------------------------------------------------------------
# Small geometry helpers (x across the roof, y up the slope, z out of it; mm)
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


def subtract_convex(poly, hole):
    """poly minus a convex hole, as convex-ish pieces."""
    out = []
    rest = list(poly)
    n = len(hole)
    for i in range(n):
        p, q = hole[i], hole[(i + 1) % n]
        dx, dy = q[0] - p[0], q[1] - p[1]
        outside = clip_half(rest, dy, -dx, -dy * p[0] + dx * p[1])
        pc = clean(outside) if len(outside) >= 3 else None
        if pc:
            out.append(pc)
        rest = clip_half(rest, -dy, dx, dy * p[0] - dx * p[1])
        if len(rest) < 3:
            break
    return out


def is_convex(poly):
    n = len(poly)
    s = 0
    for i in range(n):
        a, b, c = poly[i], poly[(i + 1) % n], poly[(i + 2) % n]
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(cr) > 1e-9:
            if s == 0:
                s = 1 if cr > 0 else -1
            elif (cr > 0) != (s > 0):
                return False
    return True


def ear_clip(poly):
    rem = list(poly)
    tris = []

    def cross(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    guard = 0
    while len(rem) > 3 and guard < 100000:
        guard += 1
        n = len(rem)
        found = None
        for i in range(n):
            a, b, c = rem[i - 1], rem[i], rem[(i + 1) % n]
            if cross(a, b, c) <= 1e-12:
                continue
            if any(cross(a, b, p) >= 0 and cross(b, c, p) >= 0 and cross(c, a, p) >= 0
                   for p in rem if p is not a and p is not b and p is not c):
                continue
            found = i
            break
        if found is None:
            break
        tris.append([rem[found - 1], rem[found], rem[(found + 1) % len(rem)]])
        del rem[found]
    if len(rem) == 3:
        tris.append(rem)
    return tris


def convex_parts(poly):
    poly = clean(poly)
    if poly is None:
        return []
    return [poly] if is_convex(poly) else [t for t in (clean(t) for t in ear_clip(poly)) if t]


class Solid:
    def __init__(self):
        self.faces = []

    def volume(self):
        v = 0.0
        for pts in self.faces:
            for j in range(1, len(pts) - 1):
                v += v_dot(pts[0], v_cross(pts[j], pts[j + 1]))
        return v / 6.0

    def fix(self):
        if self.volume() < 0:
            self.faces = [list(reversed(f)) for f in self.faces]
        return self

    def mapped(self, fn):
        s = Solid()
        s.faces = [[fn(p) for p in f] for f in self.faces]
        return s.fix()


def slab(poly, zbot, ztop, cuts=()):
    """A closed solid over a polygon, between two surfaces zbot(x, y) and ztop(x, y).
    The polygon is cut into upright strips at the x positions in `cuts`, so curved
    (wavy) surfaces are made of flat facets. Within a strip both surfaces must be flat:
    true here, as they vary linearly in y and are linear in x between cuts."""
    poly = clean(poly)
    if poly is None:
        return None
    x0, x1, _, _ = bbox(poly)
    cs = sorted(c for c in cuts if x0 + 1e-7 < c < x1 - 1e-7)
    strips = []
    edges = [x0 - 1.0] + cs + [x1 + 1.0]
    for a, b in zip(edges[:-1], edges[1:]):
        pc = clip_half(poly, 1, 0, -a) if a > x0 - 0.5 else list(poly)
        if len(pc) >= 3 and b < x1 + 0.5:
            pc = clip_half(pc, -1, 0, b)
        pc = clean(pc) if len(pc) >= 3 else None
        if pc:
            strips.append(pc)
    if not strips:
        return None
    s = Solid()
    for st in strips:
        s.faces.append([(x, y, ztop(x, y)) for x, y in st])
        s.faces.append([(x, y, zbot(x, y)) for x, y in reversed(st)])
        n = len(st)
        for i in range(n):
            (ax, ay), (bx, by) = st[i], st[(i + 1) % n]
            if any(abs(ax - c) < 1e-7 and abs(bx - c) < 1e-7 for c in cs):
                continue                   # an inside cut shared with the next strip
            s.faces.append([(ax, ay, zbot(ax, ay)), (bx, by, zbot(bx, by)),
                            (bx, by, ztop(bx, by)), (ax, ay, ztop(ax, ay))])
    return s.fix()


# ---------------------------------------------------------------------------
# Tile shapes
# ---------------------------------------------------------------------------
def tail(shape, s, d):
    """How far the bottom edge hangs below the butt line, at s = 0..1 across the tile."""
    if shape == 'fish':
        return d * (1.0 - abs(2.0 * s - 1.0))
    if shape == 'round':
        return d * math.sqrt(max(0.0, 1.0 - (2.0 * s - 1.0) ** 2))
    if shape == 'club':
        return d * (1.0 - (2.0 * s - 1.0) ** 6)
    return 0.0


def wave_at(profile, s, h):
    """Height of a profiled tile's surface at s = 0..1 across it."""
    if profile == 'pantile':
        if s < 0.68:                               # the wide trough
            return h * 0.35 * (1.0 - math.sin(math.pi * s / 0.68))
        return h * (0.35 + 0.65 * math.sin(math.pi * (s - 0.68) / 0.32))   # the roll
    if profile == 'roman':
        for a, w in ((0.42, 0.16), (0.84, 0.16)):  # two rolls on flat pans
            if a <= s <= a + w:
                return h * math.sin(math.pi * (s - a) / w)
        return 0.0
    if profile == 'corrugated':                    # even round waves, a whole number per sheet
        return h * 0.5 * (1.0 - math.cos(2.0 * math.pi * CORRUGATIONS * s))
    return 0.0


def _samples(shape):
    return 2 if shape == 'flat' else 17


# ---------------------------------------------------------------------------
# Ridge tiles, crests and finials
# ---------------------------------------------------------------------------
def extrude_x(sec_yz, xa, xb):
    """A solid running along x from xa to xb with a (y, z) cross-section."""
    so = slab(sec_yz, lambda a, b: xa, lambda a, b: xb)
    return so.mapped(lambda q: (q[2], q[0], q[1])) if so else None


def fin(sil, y1, zb, thick, up):
    """A flat upright piece (a crest or finial) standing on the ridge line.
    sil is its outline as (x, height); up = (y, z) of 'straight up' in this face's terms,
    so on a pitched roof it stands truly upright, not square to the slope. It is `thick`
    thick on this face's side of the ridge line: the other slope's half makes up the rest."""
    uy, uz = up
    so = slab(sil, lambda a, b: 0.0, lambda a, b: thick)
    if so is None:
        return None
    return so.mapped(lambda q: (q[0], y1 + q[1] * uy - q[2] * uz, zb + q[1] * uz + q[2] * uy))


def fin_out(sil, xa, xb, y1, zb, up):
    """A flat upright piece turned to face out along the ridge (seen from the gable end).
    sil is its outline as (across, height) with 0 on the ridge line; only this face's
    half (across >= 0, towards this slope) is made, the other slope makes the rest.
    It runs from x = xa to xb along the ridge."""
    uy, uz = up
    half = clean(clip_half(list(sil), 1.0, 0.0, 0.0))
    if half is None:
        return None
    so = slab(half, lambda a, b: xa, lambda a, b: xb)
    if so is None:
        return None
    # slab gives (across, height, x); across goes down this slope, square to straight up
    return so.mapped(lambda q: (q[2], y1 + q[1] * uy - q[0] * uz, zb + q[1] * uz + q[0] * uy))


def ridge_profile(style, s, h, a):
    """Height of the half ridge at s = 0 (the apex) .. 1 (where it meets the tiles)."""
    if style == 'angular':
        return h * (1.0 - s)
    if style == 'hog':
        return h * (1.0 - s * s)
    z = h * math.sqrt(max(0.0, 1.0 - s * s))
    if style == 'roll':
        rr = min(0.3 * a, 0.45 * h)               # a roll along the very top
        u = s * a / rr
        if u < 1.0:
            z += rr * 0.8 * math.sqrt(max(0.0, 1.0 - u * u))
    return z


def _bump(u, c, w):
    return math.sqrt(max(0.0, 1.0 - ((u - c) / w) ** 2))


def crest_top(kind, u, ch):
    """The crest's outline above its base strip, at u = 0..1 along one repeat."""
    if kind == 'spikes':
        return ch * (1.0 - abs(2.0 * u - 1.0))
    if kind == 'scallop':
        return ch * _bump(u, 0.5, 0.5)
    if kind == 'fleur':
        return max(ch * _bump(u, 0.5, 0.16) ** 0.6, 0.55 * ch * _bump(u, 0.24, 0.13),
                   0.55 * ch * _bump(u, 0.76, 0.13))
    if kind == 'trefoil':
        return max(0.8 * ch * _bump(u, 0.5, 0.17), 0.6 * ch * _bump(u, 0.27, 0.14),
                   0.6 * ch * _bump(u, 0.73, 0.14))
    return 0.0


def circle(cx, cz, r, n=20):
    return [(cx + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def finial(kind, xc, fh, fw, place, drop=0.0):
    """A flat finial at x = xc: plinth, stalk and a head (outlines as (x, height));
    place(outline) stands each piece on the ridge. drop: how far the plinth reaches down."""
    pl = 0.14 * fh
    sw = 0.3 * fw
    ts = 0.6 * fh
    shapes = [[(xc - fw / 2, -0.1 * fh - drop), (xc + fw / 2, -0.1 * fh - drop), (xc + fw / 2, pl), (xc - fw / 2, pl)],
              [(xc - sw / 2, pl * 0.5), (xc + sw / 2, pl * 0.5), (xc + sw / 2, ts), (xc - sw / 2, ts)]]
    if kind == 'ball':
        shapes.append(circle(xc, 0.78 * fh, 0.22 * fh))
    elif kind == 'spike':
        shapes.append([(xc, ts - 0.1 * fh), (xc + fw * 0.45, 0.72 * fh), (xc, fh), (xc - fw * 0.45, 0.72 * fh)])
    else:   # fleur-de-lis: a tall middle petal and two curled side petals
        shapes.append([(xc, ts - 0.05 * fh), (xc + fw * 0.28, 0.78 * fh), (xc, fh), (xc - fw * 0.28, 0.78 * fh)])
        for sgn in (-1.0, 1.0):
            shapes.append(circle(xc + sgn * fw * 0.42, 0.72 * fh, 0.12 * fh, 14))
            shapes.append([(xc, ts - 0.02 * fh), (xc + sgn * fw * 0.42, 0.68 * fh),
                           (xc + sgn * fw * 0.30, 0.74 * fh), (xc, ts + 0.08 * fh)])
    return [s_ for s_ in (place(sh) for sh in shapes) if s_]


def top_edges(outline):
    """The level stretches of the outline's top edge: [(x from, x to)] at the highest y."""
    x0, x1, y0, y1 = bbox(outline)
    tol = 1e-3 * (1.0 + y1 - y0)
    out = []
    n = len(outline)
    for i in range(n):
        (ax, ay), (bx, by) = outline[i], outline[(i + 1) % n]
        if abs(ay - y1) < tol and abs(by - y1) < tol and abs(bx - ax) > 1.0:
            out.append((min(ax, bx), max(ax, bx)))
    return out, y1


def build_ridge(outline, v, zr0, up=(0.0, 1.0)):
    """Half ridge tiles along the face's top edge (each roof slope gets its own half, so
    it prints flat with the slope), with crests and finials. Returns (solids, count)."""
    edges, y1 = top_edges(outline)
    if not edges:
        return [], 0
    a, h = max(1.0, v['ridge_w']), max(1.0, v['ridge_h'])
    style = v.get('ridge_style', 'round')
    rl, rg = max(10.0, v['ridge_len']), max(0.0, v['ridge_gap'])
    # the half ridge reaches from the tiles over to the upright plane through the ridge
    # line, so the halves on the two slopes meet in the middle (up = straight up)
    uy, uz = up
    # C: where the upright plane through the ridge line meets the surface the ridge sits on
    s0 = zr0 / uz if uz > 1e-6 else 0.0
    C = (y1 + s0 * uy, zr0)
    foot = (y1 - a, zr0)
    ed = (foot[0] - C[0], 0.0)
    sec = [C]
    for k in range(17):
        sk = k / 16.0
        f = ridge_profile(style, sk, h, a)       # height above C, straight up
        sec.append((C[0] + f * uy + sk * ed[0], C[1] + f * uz))
    sec.append(foot)
    hp = ridge_profile(style, 0.0, h, a)
    apex = (C[0] + hp * uy, C[1] + hp * uz)
    out, count = [], 0
    crest = v.get('crest', 'none')
    ch, ct = max(1.0, v['crest_h']), max(0.5, v['crest_t'])

    # stopped either side of any chimney standing astride the ridge
    for xa, xb, end_a, end_b in split_edges(edges, v.get('_ridge_cuts') or ()):
        n = max(1, int(round((xb - xa) / rl)))
        step = (xb - xa) / n
        for i in range(n):
            sa = xa + i * step + (rg / 2 if i > 0 else 0.0)
            sb = xa + (i + 1) * step - (rg / 2 if i < n - 1 else 0.0)
            if sb - sa < 1.0:
                continue
            so = extrude_x(sec, sa, sb)
            if so:
                out.append(so)
                count += 1
            if crest != 'none':
                reps = max(1, int(round((sb - sa) / max(1.0, 1.2 * ch))))
                base = 0.15 * ch
                sink = 0.25 * h                     # its foot goes down into the ridge
                sil = [(sa, -sink), (sb, -sink)]
                m = 14 * reps
                for k in range(m, -1, -1):
                    x = sa + (sb - sa) * k / m
                    u = ((x - sa) / (sb - sa) * reps) % 1.0 if k not in (0, m) else 0.0
                    sil.append((x, base + crest_top(crest, u, ch)))
                cs = fin(sil, apex[0], apex[1], ct, up)
                if cs:
                    out.append(cs)
        fk = v.get('finial', 'none')
        if fk != 'none':
            ends = v.get('finial_ends', 'both')
            fw = max(5.0, v['finial_w'])
            ft = max(0.5, v['finial_t'])
            fh = max(10.0, v['finial_h'])
            # set in a hair from the ends, so no face of a finial lies flush with the
            # end of the ridge tile it stands on (coincident faces upset slicers)
            ia, ib = xa + 1.0, xb - 1.0
            for xc, which in ((ia + fw / 2, 'left'), (ib - fw / 2, 'right')):
                if not ends in ('both', which):
                    continue
                if not (end_a if which == 'left' else end_b):
                    continue                    # the side of a chimney, not the end of the roof
                if v.get('finial_face', 'out') == 'out':
                    # turned to face out: its flat side looks along the ridge
                    xs = (ia, ia + ft) if which == 'left' else (ib - ft, ib)
                    fs = finial(fk, 0.0, fh, fw,
                                lambda sh, xs=xs: fin_out(sh, xs[0], xs[1], apex[0], apex[1], up),
                                drop=h)
                else:
                    fs = finial(fk, xc, fh, fw, lambda sh: fin(sh, apex[0], apex[1], ft, up))
                for so in fs:
                    so.finial = True
                out += fs
    return out, count


def _union(polys, tol=0.001):
    """Pieces lying side by side joined into outlines (the shared sides taken out)."""
    key = lambda q: (round(q[0] / tol), round(q[1] / tol))
    pts = {}
    for P in polys:
        for q in P:
            pts.setdefault(key(q), q)
    allp = list(pts.values())
    edges = {}
    for P in polys:
        if area2(P) < 0:
            P = list(reversed(P))
        n = len(P)
        for i in range(n):
            a, b = P[i], P[(i + 1) % n]
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L < tol:
                continue
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            mids = []
            for q in allp:
                s_ = (q[0] - a[0]) * ux + (q[1] - a[1]) * uy
                if tol < s_ < L - tol and abs((q[0] - a[0]) * uy - (q[1] - a[1]) * ux) < tol:
                    mids.append((s_, q))
            chain = [a] + [q for s_, q in sorted(mids)] + [b]
            for c, d in zip(chain[:-1], chain[1:]):
                kc, kd = key(c), key(d)
                if kc == kd:
                    continue
                if edges.get((kd, kc), 0) > 0:
                    edges[(kd, kc)] -= 1
                else:
                    edges[(kc, kd)] = edges.get((kc, kd), 0) + 1
    nxt = {}
    for (kc, kd), m in edges.items():
        for _ in range(m):
            nxt.setdefault(kc, []).append(kd)
    loops = []
    while any(nxt.values()):
        start = next(k for k, v_ in nxt.items() if v_)
        loop, k = [start], nxt[start].pop()
        guard = 0
        while k != start and guard < 100000:
            loop.append(k)
            if not nxt.get(k):
                return None                 # didn't close up: keep the bits as they were
            k = nxt[k].pop()
            guard += 1
        poly = [pts[k_] for k_ in loop]
        if area2(poly) <= 0:
            return None                     # a hole: keep the bits as they were
        c_ = clean(poly)
        if c_:
            loops.append(c_)
    return loops


def build_hip(P, Q, m, v, zr0):
    """This slope's half of the hip tiles down the hip from P to Q (local mm, the slope's
    outline counter-clockwise so the slope lies to the left of P->Q). m: the direction
    between the two slopes (x, y, z in this face's terms). The edge is turned to lie level
    along the top, so the ridge's own maker lays the hip tiles."""
    dx, dy = Q[0] - P[0], Q[1] - P[1]
    if math.hypot(dx, dy) < 1.0:
        return [], 0
    phi = math.pi - math.atan2(dy, dx)          # P->Q turned to point along -x
    c, sn = math.cos(phi), math.sin(phi)
    rot = lambda p: (c * p[0] - sn * p[1], sn * p[0] + c * p[1])
    Pr, Qr = rot(P), rot(Q)
    y1 = Pr[1]
    uy, uz = sn * m[0] + c * m[1], m[2]
    L = math.hypot(uy, uz)
    up = (uy / L, uz / L) if L > 1e-9 and uz / L > 0.05 else (0.0, 1.0)
    rect = [Pr, (Qr[0], y1), (Qr[0], y1 - 10.0), (Pr[0], y1 - 10.0)]
    vh = dict(v, crest='none', finial='none', _ridge_cuts=())
    sols, n = build_ridge(rect, vh, zr0, up)
    back = lambda q: (c * q[0] + sn * q[1], -sn * q[0] + c * q[1], q[2])
    out = []
    for so in sols:
        so = so.mapped(back)
        so.hip = True
        out.append(so)
    return out, n


def find_hips(slopes, tol=2.0):
    """The hips: sloping edges two roof slopes share, where the roof turns down (not a valley).
    slopes: [[to_world, outline, ...]]. Returns, per slope, [(P, Q, m)] in its own terms."""
    info = []
    for s_ in slopes:
        tw, outline = s_[0], s_[1]
        O = tw((0.0, 0.0, 0.0))
        U = v_norm(v_sub(tw((1.0, 0.0, 0.0)), O))
        V = v_norm(v_sub(tw((0.0, 1.0, 0.0)), O))
        N = v_norm(v_sub(tw((0.0, 0.0, 1.0)), O))
        W = [tw((x, y, 0.0)) for x, y in outline]
        cx = sum(p[0] for p in W) / len(W)
        cy = sum(p[1] for p in W) / len(W)
        cz = sum(p[2] for p in W) / len(W)
        info.append((U, V, N, W, (cx, cy, cz)))
    near = lambda a, b: v_len(v_sub(a, b)) / SCALE <= tol
    hips = [[] for _ in slopes]
    for i, (U, V, N, W, cen) in enumerate(info):
        n = len(W)
        for k in range(n):
            A, B = W[k], W[(k + 1) % n]
            e = v_sub(B, A)
            le = v_len(e)
            if le / SCALE < 10.0:
                continue
            if abs(e[2]) / le < 0.02:
                # level: this slope's own ridge is done by the ridge; one lower down (where a wing's
                # ridge runs into it) is done like a hip
                ys = [q[1] for q in slopes[i][1]]
                pa, pb = slopes[i][1][k], slopes[i][1][(k + 1) % n]
                if max(pa[1], pb[1]) >= max(ys) - 1.0:
                    continue
            for j, (U2, V2, N2, W2, cen2) in enumerate(info):
                if j == i or v_dot(N, N2) > 0.9999:
                    continue
                m2 = len(W2)
                if not any((near(A, W2[q]) and near(B, W2[(q + 1) % m2])) or
                           (near(B, W2[q]) and near(A, W2[(q + 1) % m2])) for q in range(m2)):
                    continue
                if v_dot(v_sub(cen2, A), N) >= 0:
                    continue                    # the other slope rises above this one: a valley
                mw = v_norm(v_add(N, N2))
                m = (v_dot(mw, U), v_dot(mw, V), v_dot(mw, N))
                hips[i].append((slopes[i][1][k], slopes[i][1][(k + 1) % n], m))
                break
    return hips


# ---------------------------------------------------------------------------
# Laying the tiles
# ---------------------------------------------------------------------------
def lay_tiles(outline, holes, v):
    """All tile solids (local mm) for a roof outline (counter-clockwise, eaves at the
    bottom) with openings. Returns (solids, count)."""
    W, L, g, t = v['width'], v['length'], v['gauge'], v['thick']
    if W <= 1 or g <= 1 or t <= 0:
        raise ValueError("Tile width, gauge and thickness must be bigger than that.")
    shape, prof = v['shape'], v['profile']
    d = min(max(0.0, v['depth']), 0.8 * g)
    h = max(0.0, v['wave']) if prof else 0.0
    gap = max(0.0, v['gap'])                         # between tiles side by side
    cgap = max(0.0, v.get('cgap', gap)) if v['print_mode'] else gap   # between courses
    printing = v['print_mode']
    step = max(0.0, v['step']) if v.get('stepped') else 0.0      # flat unless stepped
    lift = max(0.0, v.get('lift', 0.0)) if printing else 0.0
    backing = max(0.0, v.get('backing', 0.0)) if printing else 0.0
    # the tiles sit on the backing, sunk into it a hair so they overlap rather than touch
    base = lift + backing - (min(0.2, backing * 0.2) if backing > 0 else 0.0)
    if printing and backing <= 0 and v.get('_sink'):
        # straight onto a roof that is there already: sunk into it a hair, so they print as one
        base = -max(0.0, v['_sink'])
    x0, x1, y0, y1 = bbox(outline)
    parts = convex_parts(outline)
    hole_parts = [hp for hl in holes for hp in convex_parts(hl)]
    solids = []
    ridge_count = 0
    tile_parts = parts
    if v.get('ridge') and top_edges(outline)[0]:
        # the tiles stop below the ridge (printing: a groove short of it, so nothing overlaps)
        a = max(1.0, v['ridge_w'])
        stop = y1 - a - (cgap if printing else -0.4 * a)
        tile_parts = [pc for pc in (clean(clip_half(p_, 0, -1, stop)) for p_ in parts) if pc]
        zr0 = base if printing else 2.0 * t
        rs, ridge_count = build_ridge(outline, v, zr0, v.get('_up', (0.0, 1.0)))
        for so in rs:
            so.ridge = True
        solids += rs
    hip_count = 0
    if v.get('ridge') and v.get('_hips'):
        # hip tiles down each hip, the tiles stopped short of them like the ridge
        a = max(1.0, v['ridge_w'])
        stopd = a + (cgap if printing else -0.4 * a)
        zr0 = base if printing else 2.0 * t
        for P, Q, m in v['_hips']:
            dx, dy = Q[0] - P[0], Q[1] - P[1]
            ln = math.hypot(dx, dy)
            if ln < 1.0:
                continue
            nx, ny = -dy / ln, dx / ln              # into the slope (left of P->Q)
            ux, uy = dx / ln, dy / ln
            e = max(stopd, 0.0)
            # only a strip along the hip itself is kept clear of tiles (not the whole slope beyond it)
            strip = [(P[0] - ux * e - nx * e, P[1] - uy * e - ny * e),
                     (Q[0] + ux * e - nx * e, Q[1] + uy * e - ny * e),
                     (Q[0] + ux * e + nx * stopd, Q[1] + uy * e + ny * stopd),
                     (P[0] - ux * e + nx * stopd, P[1] - uy * e + ny * stopd)]
            strip = clean(strip)
            if strip and stopd > 0:
                tile_parts = [pc for pc in (clean(q_) for p_ in tile_parts
                                            for q_ in subtract_convex(p_, strip)) if pc]
            hs, nh = build_hip(P, Q, m, v, zr0)
            for so in hs:
                so.ridge = True
            solids += hs
            hip_count += nh
    lay_tiles.hips = hip_count
    if backing > 0:
        # a solid sheet under the tiles, the shape of the roof (less its openings)
        sheet = list(parts)
        for hp in hole_parts:
            nxt = []
            for pc in sheet:
                hb, pb = bbox(hp), bbox(pc)
                if pb[1] <= hb[0] or pb[0] >= hb[1] or pb[3] <= hb[2] or pb[2] >= hb[3]:
                    nxt.append(pc)
                else:
                    nxt.extend(subtract_convex(pc, hp))
            sheet = nxt
        for pc in sheet:
            so = slab(pc, lambda x, y: lift, lambda x, y: lift + backing)
            if so:
                so.backing = True
                solids.append(so)
    ns = _samples(shape)
    count = 0
    rows = int(math.ceil((y1 - y0) / g)) + 1

    def offset(r):
        return (W / 2.0) * (r % 2) if v['bond'] else 0.0

    for r in range(rows):
        yr = y0 + r * g                            # butt line of this course
        if yr >= y1:
            break
        off = offset(r)
        off_up = offset(r + 1)
        c0 = int(math.floor((x0 - off) / W)) - 1
        c1 = int(math.ceil((x1 - off) / W)) + 1
        for c in range(c0, c1):
            xa = off + c * W
            if xa + W <= x0 or xa >= x1:
                continue
            ua, ub = gap / 2.0, W - gap / 2.0
            us = [ua + (ub - ua) * k / (ns - 1) for k in range(ns)]
            bottom = [(xa + u, yr - tail(shape, u / W, d)) for u in us]
            if printing:
                # top edge: exactly the bottom edges of the tiles above (same points), lowered
                # by the gap, so nothing overlaps
                above = []
                for k in range(int(math.floor((xa - off_up) / W)) - 1, int(math.ceil((xa + W - off_up) / W)) + 1):
                    xb = off_up + k * W
                    above += [(xb + u, yr + g - cgap - tail(shape, u / W, d)) for u in us]
                above.sort()

                def above_y(x):
                    for (pa, ya), (pb, yb) in zip(above[:-1], above[1:]):
                        if pa <= x <= pb:
                            return ya if pb - pa < 1e-12 else ya + (yb - ya) * (x - pa) / (pb - pa)
                    return yr + g - cgap
                lo, hi = xa + ua, xa + ub
                top = [(hi, above_y(hi))] + [q for q in reversed(above) if lo < q[0] < hi] + \
                      [(lo, above_y(lo))]
            else:
                top = [(xa + ub, yr + L), (xa + ua, yr + L)]
            tile = clean(bottom + top)
            if tile is None:
                continue
            # trim to the roof and round openings
            pieces = []
            for pt in tile_parts:
                pc = clip_convex(tile, pt)
                if pc:
                    pieces.append(pc)
            for hp in hole_parts:
                nxt = []
                for pc in pieces:
                    hb = bbox(hp)
                    pb = bbox(pc)
                    if pb[1] <= hb[0] or pb[0] >= hb[1] or pb[3] <= hb[2] or pb[2] >= hb[3]:
                        nxt.append(pc)
                    else:
                        nxt.extend(subtract_convex(pc, hp))
                pieces = nxt
            pieces = [pc for pc in pieces if abs(area2(pc)) > 0.02 * W * g * 0.05]
            if not pieces:
                continue
            if len(pieces) > 1:
                # the bits of one tile cut by the slope's own (hidden) lines joined back into one
                pieces = _union(pieces) or pieces
            nc = 8 * CORRUGATIONS if prof == 'corrugated' else 16
            cuts = [xa + W * k / float(nc) for k in range(1, nc)] if prof else []

            if printing:
                def ztop(x, y, yr=yr, xa=xa):
                    # flat tiles of even thickness; with 'stepped' thicker at the bottom edge
                    k = min(1.25, max(0.0, (yr + g - y) / g)) if step > 0 else 0.0
                    return base + t + step * k + wave_at(prof, ((x - xa) % W) / W, h)

                def zbot(x, y):
                    return base
            else:
                def zbot(x, y, yr=yr, xa=xa):
                    k = min(1.0, max(0.0, 1.0 - (y - yr) / L))     # tilted up on the course below
                    return t * k + wave_at(prof, ((x - xa) % W) / W, h)

                def ztop(x, y, zb=zbot):
                    return zb(x, y) + t
            for pc in pieces:
                so = slab(pc, zbot, ztop, cuts)
                if so:
                    solids.append(so)
            count += 1
    lay_tiles.ridges = ridge_count
    return solids, count


# ---------------------------------------------------------------------------
# Lead flashings where the roof meets a wall
# ---------------------------------------------------------------------------
FLASH_DEFAULTS = dict(flash_top=False, flash_left=False, flash_right=False, flash_t=32.0, flash_up=150.0,
                      flash_cover=150.0)
FLASH_EDGES = (('flash_top', "Top edge (against a wall)",
                "Where the top of the roof meets a wall (a lean-to): the flashing's upstand stands truly upright "
                "against the wall, its apron lies down over the top course."),
               ('flash_left', "Left side (against a wall)",
                "Where the left side of the roof runs along a wall (a gable wall or chimney side): the upstand "
                "against the wall, the apron over the edge of the roof."),
               ('flash_right', "Right side (against a wall)",
                "The same down the right side of the roof."))
FLASH_FIELDS = (('flash_t', "V   Flashing thickness", 1.0, 200.0, 1,
                 "How thick the lead is. For 1:80 printing 32 mm (0.4 mm) or more."),
                ('flash_up', "W   Up the wall", 20.0, 2000.0, 0, "How far the upstand runs up the wall above the roof."),
                ('flash_cover', "X   Onto the roof", 20.0, 2000.0, 0,
                 "How far the apron lies over the roof from the wall."))


def _extrude_along(sec, a, b, axis):
    """A solid with cross-section sec, run along x (sec in (y, z)) or along y (sec in (x, z))
    from a to b."""
    so = slab(sec, lambda p, q: a, lambda p, q: b)
    if so is None:
        return None
    if axis == 'x':
        return so.mapped(lambda q: (q[2], q[0], q[1]))
    return so.mapped(lambda q: (q[0], q[2], q[1]))


def _top_in(solids, test):
    zs = [p[2] for so in solids for f in so.faces for p in f if test(p)]
    return max(zs) if zs else 0.0


def build_flashings(outline, solids, v, up=(0.0, 1.0)):
    """Lead flashings along the chosen edges of a roof face (local mm: x across, y up the
    slope, z out of the face), sitting 0.5 mm clear of whatever is under them (solids).
    up = 'straight up' as (y, z) in this face's terms. Returns ([solids], [notes])."""
    out, notes = [], []
    if not any(v.get(k) for k in ('flash_top', 'flash_left', 'flash_right')):
        return out, notes
    ft = max(1.0, v.get('flash_t', 32.0))
    uph = max(2 * ft, v.get('flash_up', 150.0))
    cw = max(2 * ft, v.get('flash_cover', 150.0))
    g = 0.5
    x0, x1, y0, y1 = bbox(outline)
    tol = max(1.0, 1e-3 * ((x1 - x0) + (y1 - y0)))
    if v.get('flash_top'):
        xs = [p[0] for p in outline if p[1] >= y1 - tol]
        if len(xs) < 2 or max(xs) - min(xs) < 2 * cw:
            notes.append("no level top edge for a top flashing (a pointed or hipped top?)")
        else:
            xa, xb = min(xs), max(xs)
            zt = _top_in(solids, lambda p: p[1] >= y1 - cw - 2 * ft and xa - 1 <= p[0] <= xb + 1) + g
            uy, uz = up
            if uz < 0.15:                     # a wall face: stand the upstand square to it
                uy, uz = 0.0, 1.0
            L = math.hypot(uy, uz)
            uy, uz = uy / L, uz / L
            ny, nz = -uz, uy                  # from the wall in over the roof

            def on(off, z):
                s = (z - off * nz) / uz
                return (y1 + off * ny + s * uy, z)
            p1, p2 = on(g, zt), on(g, zt + ft + uph)
            p3, p4 = on(g + ft, zt + ft + uph), on(g + ft, zt + ft)
            ya = min(p4[0], p1[0]) - cw
            sec = clean([p1, p2, p3, p4, (ya, zt + ft), (ya, zt)])
            so = _extrude_along(sec, xa, xb, 'x') if sec else None
            if so:
                out.append(so)
    for key, side in (('flash_left', -1), ('flash_right', 1)):
        if not v.get(key):
            continue
        xe = x0 if side < 0 else x1
        ys = [p[1] for p in outline if abs(p[0] - xe) <= tol]
        if len(ys) < 2 or max(ys) - min(ys) < 2 * cw:
            notes.append("no straight %s side for a flashing" % ("left" if side < 0 else "right"))
            continue
        ya, yb = min(ys), max(ys)
        zt = _top_in(solids, lambda p: abs(p[0] - xe) <= cw + 2 * ft and ya - 1 <= p[1] <= yb + 1) + g
        d = -side                              # from the wall in over the roof
        w0 = xe + d * g
        w1 = xe + d * (g + ft)
        w2 = xe + d * (g + cw)
        sec = clean([(w0, zt), (w2, zt), (w2, zt + ft), (w1, zt + ft), (w1, zt + ft + uph), (w0, zt + ft + uph)])
        so = _extrude_along(sec, ya, yb, 'y') if sec else None
        if so:
            out.append(so)
    return out, notes


def add_flashing_tab(dlg, tabs, on_change):
    """A 'Flashing' tab for a roofing dialog: which edges, and the lead's sizes."""
    page = QWidget()
    form = QFormLayout(page)
    tabs.addTab(page, "Flashing")
    try:
        tabs.setTabToolTip(tabs.count() - 1, "Lead flashings where the roof meets a wall.")
    except Exception:
        pass
    dlg.fl_cb, dlg.fl_sp = {}, {}
    for key, label, tip in FLASH_EDGES:
        cb = QCheckBox(label)
        cb.setToolTip(tip)
        form.addRow(cb)
        cb.toggled.connect(on_change)
        dlg.fl_cb[key] = cb
    for key, label, lo, hi, dec, tip in FLASH_FIELDS:
        s = QDoubleSpinBox()
        s.setDecimals(dec)
        s.setRange(lo, hi)
        s.setSuffix(" mm")
        s.setKeyboardTracking(False)
        s.setToolTip(tip)
        lab = QLabel(label)
        lab.setToolTip(tip)
        form.addRow(lab, s)
        s.valueChanged.connect(on_change)
        dlg.fl_sp[key] = s
    note = QLabel("Each flashing is a closed solid in its own 'Flashing' group, 0.5 mm clear of the roof.")
    note.setWordWrap(True)
    form.addRow(note)


def flashing_values(dlg):
    v = {k: cb.isChecked() for k, cb in dlg.fl_cb.items()}
    v.update({k: float(s.value()) for k, s in dlg.fl_sp.items()})
    for s in dlg.fl_sp.values():
        s.setEnabled(any(v[k] for k in dlg.fl_cb))
    return v


def set_flashing_values(dlg, d):
    for k, cb in dlg.fl_cb.items():
        cb.setChecked(bool(d.get(k, FLASH_DEFAULTS[k])))
    for k, s in dlg.fl_sp.items():
        s.setValue(float(d.get(k, FLASH_DEFAULTS[k])))
    on = any(cb.isChecked() for cb in dlg.fl_cb.values())
    for s in dlg.fl_sp.values():
        s.setEnabled(on)


DEFAULTS.update(FLASH_DEFAULTS)


# ---------------------------------------------------------------------------
# Reading the selected face
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
            continue
        vs = getattr(e, 'vertices', None)
        if vs is not None and not callable(vs) and len(_items(vs)) >= 3:
            out.append(e)
    return out


def face_frame(face, flip=False, turn=0):
    """(to_world function, outline, holes) for a face: x across, y up the slope (mm)."""
    pts = [p for p in (_pos(q) for q in _items(face.vertices)) if p is not None]
    if len(pts) < 3:
        raise ValueError("That face has no corners I can read.")
    n = _newell(pts)
    if flip:
        n = v_mul(n, -1.0)
    if abs(n[2]) < LEVEL:
        U = v_norm(v_cross(Z, n))        # level, along the eaves (and down the fall of a flat roof)
    else:
        k = max(range(len(pts)), key=lambda i: v_len(v_sub(pts[(i + 1) % len(pts)], pts[i])))
        e = v_sub(pts[(k + 1) % len(pts)], pts[k])
        U = v_norm(v_sub(e, v_mul(n, v_dot(e, n))))
    V = v_cross(n, U)                    # up the slope
    a = math.radians(turn)
    U, V = (v_add(v_mul(U, math.cos(a)), v_mul(V, math.sin(a))),
            v_add(v_mul(U, -math.sin(a)), v_mul(V, math.cos(a))))
    O = pts[0]

    def to2(p):
        d = v_sub(p, O)
        return (v_dot(d, U) / SCALE, v_dot(d, V) / SCALE)
    outline = clean([to2(p) for p in pts])
    holes = []
    for hl in _items(getattr(face, 'holes', None)):
        hp = clean([to2(p) for p in (_pos(q) for q in _items(hl)) if p is not None])
        if hp:
            holes.append(hp)

    def tw(p):
        return v_add(O, v_add(v_mul(U, p[0] * SCALE), v_add(v_mul(V, p[1] * SCALE), v_mul(n, p[2] * SCALE))))
    # 'straight up' in this face's (y, z) terms, for crests and finials
    uy, uz = V[2], n[2]
    L = math.hypot(uy, uz)
    up = (uy / L, uz / L) if L > 1e-9 and uz > 0.05 else (0.0, 1.0)
    return tw, outline, holes, up


# ---------------------------------------------------------------------------
# Going round chimneys: the tiles (or sheets) are cut round any chimney standing on the
# roof, and the ridge stops either side of one that stands astride it
# ---------------------------------------------------------------------------
CHIMNEY_WORDS = ("chimney", "roof vent", "doig")


def _wpos(q, m):
    p = _pos(q)
    if p is None or m is None:
        return p
    try:
        r = m.map(QVector3D(*p))
        return (float(r.x()), float(r.y()), float(r.z()))
    except Exception:
        return p


def find_chimneys(scene):
    """Every chimney in the model, as a list of its corners in world space - one list for
    each group with 'chimney' (or 'roof vent') in its name: ones Chimneys built, or your own."""
    out = []
    for top in _items(getattr(scene, 'groups', None)):
        place = {}
        try:
            for g, m in _placements(top):
                place.setdefault(id(g), m)
        except Exception:
            pass

        def grab(h, pts, lvl):
            m = place.get(id(h))
            for f in _items(getattr(getattr(h, 'mesh', None), 'faces', None)):
                for q in _items(getattr(f, 'vertices', None)):
                    p = _wpos(q, m)
                    if p is not None:
                        pts.append(p)
            if lvl < 12:
                for c in _kids(h):
                    grab(c, pts, lvl + 1)

        def walk(g, lvl):
            nm = str(getattr(g, 'name', '') or '').lower()
            if any(w in nm for w in CHIMNEY_WORDS):
                pts = []
                grab(g, pts, 0)
                if len(pts) >= 3:
                    out.append(pts)
                return
            if lvl < 12:
                for c in _kids(g):
                    walk(c, lvl + 1)
        walk(top, 0)
    return out


def _hull2(pts):
    pts = sorted(set((round(p[0], 6), round(p[1], 6)) for p in pts))
    if len(pts) < 3:
        return None

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    h = lo[:-1] + hi[:-1]
    return h if len(h) >= 3 else None


def _grow_convex(poly, d):
    """A convex outline (counter-clockwise) made d bigger all round."""
    n = len(poly)
    out = []
    for i in range(n):
        a, b, c = poly[i - 1], poly[i], poly[(i + 1) % n]
        e1 = (b[0] - a[0], b[1] - a[1])
        e2 = (c[0] - b[0], c[1] - b[1])
        l1, l2 = math.hypot(*e1) or 1.0, math.hypot(*e2) or 1.0
        n1 = (e1[1] / l1, -e1[0] / l1)
        n2 = (e2[1] / l2, -e2[0] / l2)
        k = 1.0 + n1[0] * n2[0] + n1[1] * n2[1]
        k = max(k, 0.2)
        out.append((b[0] + d * (n1[0] + n2[0]) / k, b[1] + d * (n1[1] + n2[1]) / k))
    return out


def chimney_holes(tw, outline, chims, clear=10.0, reach=300.0):
    """Where each chimney stands on this roof face, in the face's own terms (mm): its outline
    where it meets the roof (taken from the part of it within `reach` mm above the roof, so the
    wider oversailing top and the pots don't count), made `clear` mm bigger all round. Only
    chimneys that are on this face."""
    O = tw((0.0, 0.0, 0.0))
    U = v_norm(v_sub(tw((1.0, 0.0, 0.0)), O))
    V = v_norm(v_sub(tw((0.0, 1.0, 0.0)), O))
    N = v_norm(v_sub(tw((0.0, 0.0, 1.0)), O))
    if N[2] < 0.05:
        return []                                  # an upright face: no chimney stands on it
    x0, x1, y0, y1 = bbox(outline)
    holes = []
    for pts in chims:
        flat = []
        for P in pts:
            hv = v_dot(v_sub(P, O), N) / N[2]      # how far above the roof, straight up (m)
            if hv / SCALE > reach:
                continue
            Q = (P[0], P[1], P[2] - hv)            # straight down onto the roof's plane
            d = v_sub(Q, O)
            flat.append((v_dot(d, U) / SCALE, v_dot(d, V) / SCALE))
        h = _hull2(flat)
        if not h:
            continue
        hb = bbox(h)
        if hb[1] <= x0 or hb[0] >= x1 or hb[3] <= y0 or hb[2] >= y1:
            continue                               # not on this face
        h = clean(_grow_convex(h, clear))
        if h:
            holes.append(h)
    return holes


def ridge_cuts(holes, outline, reach):
    """The stretches along the top edge where a chimney stands astride the ridge: [(x from, x to)]."""
    y1 = bbox(outline)[3]
    out = []
    for h in holes:
        hb = bbox(h)
        if hb[3] >= y1 - reach:
            out.append((hb[0], hb[1]))
    return out


def split_edges(edges, cuts):
    """The ridge's top edges with the chimneys' stretches taken out: [(from, to, real start, real end)]
    - 'real' meaning an end of the roof, not the side of a chimney (finials only go on those)."""
    out = []
    for xa, xb in edges:
        segs = [(xa, xb)]
        for ca, cb in cuts:
            nxt = []
            for a, b in segs:
                if cb <= a or ca >= b:
                    nxt.append((a, b))
                else:
                    if ca > a:
                        nxt.append((a, ca))
                    if cb < b:
                        nxt.append((cb, b))
            segs = nxt
        for a, b in segs:
            if b - a > 1.0:
                out.append((a, b, abs(a - xa) < 1e-6, abs(b - xb) < 1e-6))
    return out


# what you last used and the order of your presets - kept between sessions
UI_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_roof_tiles.json")


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
    except Exception as e:
        print("%s: could not keep your settings: %s" % (PLUGIN_NAME, e))


def remember_last(values):
    """Keeps the settings you used, so the window opens with them next time."""
    keep = {k: val for k, val in values.items()
            if not k.startswith('_') and isinstance(val, (bool, int, float, str, type(None)))}
    _ui_settings_save(last=keep)


def last_used():
    d = _ui_settings().get('last')
    return d if isinstance(d, dict) else {}


# ---------------------------------------------------------------------------
# Finding the roof pieces in a picked group (the building, or Subframe's roof panels)
# ---------------------------------------------------------------------------
# groups never tiled when a whole group is picked: tiles made before, and Subframe's bars
# (its rafters have wide sloping tops, but they're not the roof). Subframe's 'Roof panels'
# group is not in here: it's made to be tiled.
GROUP_SKIP = ("Roof - ", "Sheeting - ", "Subframe", "Roof truss", "Glazing frames", "Fascia and barge boards",
              "Chimney", "Industrial chimney", "Roof vent", "Doig", "Weather vane")
# Floor Plan's gable ends (and walls with their gable on) sit under the roof: their sloping
# tops follow the underside of the roof, so they're never the roof itself
GROUP_SKIP_IN = (" - Gable on ", " with gable", " - Wall ")
# a wall with windows or doors built into it (by 3D Period Windows / Doors): the sloping tops of
# their arched heads, sills and steps are not the roof - its whole group is left out
BUILT_IN_KEYS = ("ed3d_openings", "ed3d_period_windows")


def _has_built_ins(g):
    ext = getattr(g, 'ext', None)
    return isinstance(ext, dict) and any(isinstance(ext.get(k), dict) for k in BUILT_IN_KEYS)


# a roof that is there already: Floor Plan's roof slopes and Subframe's plain roof panels. Tiles go
# straight onto these (no backing sheet - the slope is the backing) and into a group with the slope.
ROOF_HOSTS = ("Roof slope", "Roof panel ")
TILED = "Tiled - "            # the group holding a roof slope and its tiles
TILES_KEY = "ed3d_roof_tiles"


def _is_host(g):
    nm = str(getattr(g, 'name', '') or '')
    return nm.startswith(ROOF_HOSTS) and len(_items(getattr(getattr(g, 'mesh', None), 'faces', None))) > 0


def _is_tiles(g):
    ext = getattr(g, 'ext', None)
    return isinstance(ext, dict) and isinstance(ext.get(TILES_KEY), dict)


def _host_in(chain):
    """The roof slope a face belongs to: the nearest group in its chain (top first) that is one."""
    for g in reversed(chain):
        if _is_host(g):
            return g
    return None


def scene_tree(scene):
    """{id(group): (group, world matrix or None, the list it sits in, the group it's in or None)}
    for every group in the scene."""
    out = {}
    for top in _items(getattr(scene, 'groups', None)):
        place = {}
        for g, m in _placements(top):
            place.setdefault(id(g), m)

        def walk(g, lst, par, lvl):
            if id(g) in out:
                return
            out[id(g)] = (g, place.get(id(g)), lst, par)
            if lvl < 40:
                for attr in ('children', 'groups'):
                    kl = getattr(g, attr, None)
                    if isinstance(kl, list):
                        for c in kl:
                            if not _is_face(c):
                                walk(c, kl, g, lvl + 1)
        walk(top, getattr(scene, 'groups', None), None, 0)
    return out


def face_host(tree, face):
    """The roof slope a picked face is on (or None)."""
    home = None
    for g, _m, _l, _p in tree.values():
        fs = _items(getattr(getattr(g, 'mesh', None), 'faces', None))
        if any(f is face for f in fs):
            home = g
            break
    chain = []
    while home is not None and len(chain) < 60:
        chain.insert(0, home)
        home = tree.get(id(home), (None, None, None, None))[3]
    return _host_in(chain)


def _inverse(m):
    if m is None:
        return None
    try:
        r = m.inverted()
        if isinstance(r, tuple):
            r, ok = r
            if not ok:
                return None
        return r
    except Exception:
        return None


class WorldFace:
    """A face from inside a group, its corners already where they really are (moved groups
    and copies come through their placement)."""
    def __init__(self, pts, holes):
        self.vertices = pts
        self.holes = holes


def _is_face(e):
    return hasattr(e, 'loop') or 'face' in type(e).__name__.lower()


def selected_groups(scene):
    return [e for e in _items(getattr(scene, 'selection', None))
            if getattr(e, 'mesh', None) is not None and not _is_face(e)]


def _kids(g):
    return [c for c in _items(getattr(g, 'children', None)) + _items(getattr(g, 'groups', None))
            if not _is_face(c)]


def _placements(top):
    """(group, world matrix or None) for a group and every group inside it - the same way
    Scale Studio finds where each piece really is."""
    try:
        from core.group import iter_placements
        return list(iter_placements(top))
    except Exception:
        pass
    out = []

    def walk(g, base, depth):
        m = getattr(g, 'xform', None)
        if base is not None:
            m = base if m is None else base * m
        out.append((g, m))
        if depth < 12:
            for c in _kids(g):
                walk(c, m, depth + 1)
    walk(top, None, 0)
    return out


def faces_in_groups(groups):
    """Every face inside the picked groups, in world space: ([WorldFace], [names left out])."""
    out, skipped = [], []
    for top in groups:
        place = {}
        for g, m in _placements(top):
            place.setdefault(id(g), m)

        def wpos(q, m):
            p = _pos(q)
            if p is None or m is None:
                return p
            try:
                r = m.map(QVector3D(*p))
                return (float(r.x()), float(r.y()), float(r.z()))
            except Exception:
                return p

        def walk(g, lvl, chain=()):
            nm = str(getattr(g, 'name', '') or '')
            if any(w in nm for w in GROUP_SKIP_IN) or _has_built_ins(g) or _is_tiles(g):
                return
            if nm.startswith(GROUP_SKIP):
                skipped.append(nm)
                return
            chain = tuple(chain) + (g,)
            host = _host_in(chain)
            m = place.get(id(g))
            for f in _items(getattr(getattr(g, 'mesh', None), 'faces', None)):
                pts = [p for p in (wpos(q, m) for q in _items(getattr(f, 'vertices', None))) if p is not None]
                if len(pts) < 3:
                    continue
                hs = []
                for h in _items(getattr(f, 'holes', None)):
                    hp = [p for p in (wpos(q, m) for q in _items(h)) if p is not None]
                    if len(hp) >= 3:
                        hs.append(hp)
                wf = WorldFace(pts, hs)
                wf.host = host
                out.append(wf)
            if lvl < 12:
                for c in _kids(g):
                    walk(c, lvl + 1, chain)
        walk(top, 0)
    return out, skipped


def _area3(pts):
    nx = ny = nz = 0.0
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    return 0.5 * math.sqrt(nx * nx + ny * ny + nz * nz)


# a face tilted by less than this (cos of about 0.25 degrees) counts as level: a floor or a wall
# top. Anything steeper - down to a flat roof with a fall of a degree or two - is a roof.
LEVEL = 0.99999


def pick_roof_faces(faces, v):
    """The roof pieces among a group's faces: sloping and facing up, and wide enough for a
    course of tiles - so walls, floors, wall tops, the undersides of the roof and the thin edges
    of a thick roof or roof panel are all left out. Flat roofs with a fall count as well."""
    g = min(600.0, max(10.0, v.get('gauge', 100.0)))      # long tin sheets: still no thin edges
    out = []
    for f in faces:
        pts = f.vertices
        n = _newell(pts)
        if not (0.05 < n[2] < LEVEL):
            continue
        area = _area3(pts) / (SCALE * SCALE)
        longest = max(v_len(v_sub(pts[(i + 1) % len(pts)], pts[i])) for i in range(len(pts))) / SCALE
        if area < 1.0 or longest < 1e-6 or area / longest < 0.5 * g:
            continue
        out.append(f)
    return out


def _join(A, B, tol):
    """Two outlines (both counter-clockwise) sharing an edge, joined into one - or None."""
    na, nb = len(A), len(B)
    same = lambda p, q: abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol
    for i in range(na):
        P, Q = A[i], A[(i + 1) % na]
        for k in range(nb):
            if same(B[k], Q) and same(B[(k + 1) % nb], P):
                pa = [A[(i + 1 + j) % na] for j in range(na)]          # Q ... P
                pb = [B[(k + 1 + j) % nb] for j in range(nb)]          # P ... Q
                return clean(pa + pb[1:-1])
    return None


def merge_coplanar(slopes, tol=1.0):
    """A roof slope drawn as several faces (say two triangles) is joined back into one, so its
    courses run straight across it. slopes: [[tw, outline, holes, up]] - changed in place."""
    merged = True
    while merged:
        merged = False
        for i, a in enumerate(slopes):
            O = a[0]((0.0, 0.0, 0.0))
            Uu = v_norm(v_sub(a[0]((1.0, 0.0, 0.0)), O))
            Vu = v_norm(v_sub(a[0]((0.0, 1.0, 0.0)), O))
            Na = v_norm(v_sub(a[0]((0.0, 0.0, 1.0)), O))

            def to_a(P, O=O, Uu=Uu, Vu=Vu):
                d = v_sub(P, O)
                return (v_dot(d, Uu) / SCALE, v_dot(d, Vu) / SCALE)
            for b in slopes[i + 1:]:
                if len(a) > 4 and len(b) > 4 and a[4] is not b[4]:
                    continue            # each roof slope keeps its own tiles
                Ob = b[0]((0.0, 0.0, 0.0))
                Nb = v_norm(v_sub(b[0]((0.0, 0.0, 1.0)), Ob))
                if v_dot(Na, Nb) < 0.9999 or abs(v_dot(v_sub(Ob, O), Na)) / SCALE > tol:
                    continue
                bo = clean([to_a(b[0]((x, y, 0.0))) for x, y in b[1]])
                if not bo:
                    continue
                u = _join(a[1], bo, tol)
                if u is None:
                    continue
                a[1] = u
                a[2] = list(a[2]) + [h for h in (clean([to_a(b[0]((x, y, 0.0))) for x, y in hl])
                                                 for hl in b[2]) if h]
                slopes.remove(b)
                merged = True
                break
            if merged:
                break
    return slopes


# ---------------------------------------------------------------------------
# Presets
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


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------
VIEW_DIR = v_norm((-0.18, 0.32, -1.0))       # nearly face-on, a little from below the eaves
LIGHT = v_norm((-0.45, 0.65, 0.6))           # low light from the top left shows the shapes
COLOURS = {'plain': (176, 84, 56), 'slate': (86, 92, 104), 'smallslate': (98, 104, 116),
           'fish': (170, 80, 54), 'bull': (180, 92, 60), 'beaver': (168, 76, 50), 'club': (174, 86, 58),
           'pantile': (196, 104, 58), 'roman': (150, 140, 132), 'tin': (158, 166, 170)}


def preview_caption(v):
    lab = TILE_INFO.get(v.get('tile'), ("Tile",))[0]
    txt = "%s - %.0f wide, %.0f gauge, %.0f thick" % (lab, v['width'], v['gauge'], v['thick'])
    if v.get('print_mode'):
        txt += " - 3D printing" + (", stepped" if v.get('stepped') else ", flat")
    else:
        txt += " - lapped"
    if v.get('ridge'):
        txt += " - %s ridge" % dict(RIDGES).get(v.get('ridge_style'), '').lower()
    return txt


def preview_items(v):
    # a close-up: about four tiles across and five courses up, sized to the tile
    W = max(10.0, v['width'])
    g = max(10.0, v['gauge'])
    pw = 4.0 * W
    ph = 5.0 * g + (max(v.get('ridge_w', 0.0), 0.0) if v.get('ridge') else 0.0)
    outline = [(0.0, 0.0), (pw, 0.0), (pw, ph), (0.0, ph)]
    sols, _ = lay_tiles(outline, [], v)
    right = v_norm(v_cross(VIEW_DIR, (0.0, 1.0, 0.0)))
    up = v_cross(right, VIEW_DIR)
    rgb = COLOURS.get(v.get('tile'), (170, 90, 60))
    items = []
    for so in sols:
        col = (120, 112, 104) if getattr(so, 'backing', False) else rgb
        for f in so.faces:
            n = _newell(f)
            if v_dot(n, VIEW_DIR) >= 0:
                continue
            k = 0.5 + 0.5 * max(0.0, v_dot(n, LIGHT))
            depth = sum(v_dot(p, VIEW_DIR) for p in f) / len(f)
            # the backing sheet is drawn first: it lies under every tile
            # curved (profiled) tiles are made of narrow facets: no outline between them
            edge = not (v.get('profile') and abs(n[2]) > 0.2)
            items.append((depth + (1e9 if getattr(so, 'backing', False) else 0.0),
                          [(v_dot(p, right), -v_dot(p, up)) for p in f],
                          tuple(int(c * k) for c in col), edge))
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

EDDY_TIPS = {'Tile': 'The tile shape: plain, beaver tail, fish scale, slate and so on.',
 "3D printing - tiles don't overlap, flat on the roof": 'Every tile lies flat on the roof '
                                                        'face, with no overlaps, so it prints '
                                                        'cleanly. Untick for real overlapping, '
                                                        'tilted tiles.',
 'Courses offset by half a tile': 'Each course is moved along half a tile, like a real roof. '
                                  'Untick to line the tiles up.',
 'Tile thickness': 'How thick each tile is.',
 'Tiles on the other side of the face': 'Puts the tiles on the back of the face instead of the '
                                        'front.',
 'Ridge shape': 'The shape of the ridge tiles: half-round, angular, hog-back or roll-top.',
 'Finials': 'An ornament at the ends of the ridge: none, a spike, a ball or a fleur-de-lis.',
 'Finials at': 'Which ends of the ridge get a finial.',
 'Ridge tile length': 'How long each ridge tile is.',
 'Gap between ridge tiles': 'The gap between ridge tiles (never 0, so no faces touch).',
 'Crest height': 'How high the ridge stands above the roof.',
 'Finial height': 'How tall the finials are.',
 'Finial width': 'How wide the finials are.',
 'Finial thickness': 'How thick the finials are.',
 'Tile selected face(s) or group': 'Tiles each roof face you have selected - pick two faces that '
                                   'meet to get a ridge along the top. Or click a whole group (the '
                                   "building, or Subframe's 'Roof panels') and every roof piece in it is "
                                   'tiled at once, ridge and all. Each slope comes out as a group of its '
                                   'own, with the tiles, ridge half, finials and flashing each a separate '
                                   'piece for printing.',
 'Tiles': "The tiles: shape, size and how they're laid.",
 'Ridge': 'Ridge tiles along the top, and the finials at the ends.'}
EDDY_TIPS_END = None


class KeyDrawing(QWidget):
    """The first key: what each lettered tile size is (A to J, and U)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 700)

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF, QPainterPath
        from PySide6.QtCore import QPointF, QRectF, Qt
        import math as _m
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 246))
        k = min(float(self.width()) / 360.0, self.height() / 700.0)
        p.scale(k, k)
        red = QColor(200, 40, 40)
        tile = QColor(186, 92, 62)
        roofc, backc = QColor(200, 196, 188), QColor(150, 142, 134)
        f = QFont()
        f.setBold(True)
        f.setPointSizeF(9.5)

        def poly(pts, col):
            p.setPen(QPen(col.darker(160), 0.8))
            p.setBrush(col)
            p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in pts]))

        def box(x, y, w, h, col):
            poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], col)

        def dim(x1, y1, x2, y2, letter, tx, ty):
            p.setPen(QPen(red, 1.1))
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            ang = _m.atan2(y2 - y1, x2 - x1)
            for (x, y, a) in ((x1, y1, ang), (x2, y2, ang + _m.pi)):
                for s_ in (0.45, -0.45):
                    p.drawLine(QPointF(x, y), QPointF(x + 6 * _m.cos(a + s_), y + 6 * _m.sin(a + s_)))
            p.setPen(red)
            p.drawText(QRectF(tx - 12, ty - 9, 24, 18), Qt.AlignCenter, letter)

        def title(x, y, text):
            p.setFont(f)
            p.setPen(QColor(60, 60, 60))
            p.drawText(QRectF(x, y, 350, 18), Qt.AlignLeft, text)

        # ---- the tiles from above: three courses, half bond, eaves at the bottom
        title(10, 4, "Tiles from above (3D printing) - eaves at the bottom")
        X0, X1, YB = 30.0, 320.0, 200.0
        tw_, gp, gauge, cg = 70.0, 6.0, 56.0, 6.0
        p.save()
        p.setClipRect(QRectF(X0, 20, X1 - X0, YB - 20))
        box(X0, 20, X1 - X0, YB - 20, roofc)
        for r in range(3):
            yb = YB - r * gauge
            off = (tw_ + gp) / 2.0 if r % 2 else 0.0
            x = X0 - off
            while x < X1:
                box(x, yb - (gauge - cg), tw_, gauge - cg, tile)
                x += tw_ + gp
        p.restore()
        # A: one tile wide (bottom course, second tile); F: the gap after it
        ax = X0 + tw_ + gp
        dim(ax, YB + 12, ax + tw_, YB + 12, "A", ax + tw_ / 2, YB + 24)
        dim(ax + tw_, YB - 20, ax + tw_ + gp, YB - 20, "F", ax + tw_ + gp + 12, YB - 30)
        # C: one course to the next (butt to butt); J: the gap between courses
        dim(X1 + 12, YB, X1 + 12, YB - gauge, "C", X1 + 22, YB - gauge / 2)
        jy = YB - (gauge - cg)
        dim(X0 - 12, jy, X0 - 12, jy - cg, "J", X0 - 22, jy - cg / 2)
        p.setPen(QPen(QColor(150, 150, 150), 0.6))
        p.drawLine(QPointF(X0 - 16, jy), QPointF(X0, jy))
        p.drawLine(QPointF(X0 - 16, jy - cg), QPointF(X0, jy - cg))

        # ---- lapped tiles from the side (3D printing off)
        title(10, 228, "Lapped tiles from the side (3D printing off)")
        p.setPen(QPen(QColor(110, 110, 110), 2.0))
        p.drawLine(QPointF(30, 300), QPointF(330, 300))              # the roof face
        tl, gg = 120.0, 50.0
        for i in range(5):
            x0 = 40 + i * gg
            ang = -0.10
            pts = [(x0, 296), (x0 + tl, 296 + tl * ang), (x0 + tl, 290 + tl * ang), (x0, 290)]
            poly(pts, tile.lighter(110 if i % 2 else 100))
        dim(40, 312, 40 + tl, 312, "B", 40 + tl / 2, 324)
        dim(40 + 2 * gg, 262, 40 + 3 * gg, 262, "C", 40 + 2.5 * gg, 250)
        p.setPen(QColor(110, 110, 110))
        p.setFont(QFont())
        p.drawText(QRectF(250, 304, 100, 14), Qt.AlignLeft, "eaves this way →")

        # ---- a course end on, flat and stepped (3D printing)
        title(10, 340, "Courses end on (3D printing) - flat, and stepped")
        base = 440.0
        box(20, base, 150, 18, roofc)                                  # the roof face
        box(20, base - 16, 150, 12, backc)                             # backing sheet (I), U clear
        for i in range(3):                                             # flat tiles: D thick
            box(24 + i * 50, base - 16 - 10, 44, 10, tile)
        dim(10, base - 4, 10, base, "U", 4, base + 10)
        dim(178, base - 16, 178, base - 4, "I", 190, base - 10)
        dim(178, base - 26, 178, base - 16, "D", 190, base - 26)
        box(190 + 10, base, 150, 18, roofc)
        box(200, base - 16, 150, 12, backc)
        for i in range(3):                                             # stepped: thicker at the bottom
            x0 = 204 + i * 50
            poly([(x0, base - 16), (x0 + 44, base - 16), (x0 + 44, base - 30), (x0, base - 24)], tile)
        x0 = 204
        dim(x0 + 47, base - 24, x0 + 47, base - 30, "E", x0 + 47, base - 40)
        p.setPen(QPen(QColor(150, 150, 150), 0.6))
        p.drawLine(QPointF(x0 + 30, base - 24), QPointF(x0 + 50, base - 24))
        p.setPen(QColor(110, 110, 110))
        p.setFont(QFont())
        p.drawText(QRectF(204, base + 20, 150, 14), Qt.AlignLeft, "← up the roof   eaves →")

        # ---- a shaped tile and a pantile
        title(10, 478, "A shaped tile (bullnose)")
        sx, sy, sw, sh, dep = 40.0, 505.0, 80.0, 60.0, 26.0
        path = QPainterPath()
        path.moveTo(sx, sy)
        path.lineTo(sx + sw, sy)
        path.lineTo(sx + sw, sy + sh - dep)
        path.arcTo(QRectF(sx, sy + sh - 2 * dep, sw, 2 * dep), 0, -180)
        path.closeSubpath()
        p.setPen(QPen(tile.darker(160), 0.8))
        p.setBrush(tile)
        p.drawPath(path)
        dim(sx + sw + 12, sy + sh - dep, sx + sw + 12, sy + sh, "G", sx + sw + 22, sy + sh - dep / 2)
        p.setPen(QPen(QColor(150, 150, 150), 0.6))
        p.drawLine(QPointF(sx + sw, sy + sh - dep), QPointF(sx + sw + 16, sy + sh - dep))
        title(180, 478, "A pantile, end on")
        wy, amp = 545.0, 18.0
        top = [(170 + i * 4.0, wy - amp * 0.5 * (1 - _m.cos(i * 4.0 / 80.0 * 2 * _m.pi))) for i in range(41)]
        poly(top + [(330, wy + 6), (170, wy + 6)], tile)
        dim(338, wy, 338, wy - amp, "H", 350, wy - amp / 2)

        # ---- the notes
        f2 = QFont()
        f2.setPointSizeF(8.5)
        p.setFont(f2)
        p.setPen(QColor(60, 60, 60))
        notes = ["A  tile width (cover, side by side)", "B  tile length (lapped tiles)",
                 "C  gauge - course to course", "D  tile thickness", "E  extra at the bottom (stepped)",
                 "F  gap between tiles", "G  tail depth (shaped tiles)", "H  wave height (pantiles, Romans, tin)",
                 "I  backing sheet thickness", "J  gap between courses", "U  gap off the roof face",
                 "K - X  on the next key page"]
        for i, t in enumerate(notes):
            p.drawText(QRectF(10 if i < 6 else 185, 590 + (i % 6) * 14, 175, 14), Qt.AlignLeft | Qt.AlignVCenter, t)
        p.end()


class KeyDrawing2(QWidget):
    """The second key: the ridge, crest and finials (K to T) and the flashing (V to X)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 730)

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
        from PySide6.QtCore import QPointF, QRectF, Qt
        import math as _m
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 246))
        k = min(float(self.width()) / 360.0, self.height() / 730.0)
        p.scale(k, k)
        red = QColor(200, 40, 40)
        tile, ridge = QColor(186, 92, 62), QColor(160, 70, 48)
        roofc, wallc = QColor(200, 196, 188), QColor(214, 208, 198)
        lead = QColor(120, 124, 132)
        f = QFont()
        f.setBold(True)
        f.setPointSizeF(9.5)

        def poly(pts, col):
            p.setPen(QPen(col.darker(160), 0.8))
            p.setBrush(col)
            p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in pts]))

        def box(x, y, w, h, col):
            poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], col)

        def dim(x1, y1, x2, y2, letter, tx, ty):
            p.setPen(QPen(red, 1.1))
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            ang = _m.atan2(y2 - y1, x2 - x1)
            for (x, y, a) in ((x1, y1, ang), (x2, y2, ang + _m.pi)):
                for s_ in (0.45, -0.45):
                    p.drawLine(QPointF(x, y), QPointF(x + 6 * _m.cos(a + s_), y + 6 * _m.sin(a + s_)))
            p.setPen(red)
            p.drawText(QRectF(tx - 12, ty - 9, 24, 18), Qt.AlignCenter, letter)

        def guide(x1, y1, x2, y2):
            p.setPen(QPen(QColor(150, 150, 150), 0.6, Qt.DashLine))
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        def title(x, y, text):
            p.setFont(f)
            p.setPen(QColor(60, 60, 60))
            p.drawText(QRectF(x, y, 350, 18), Qt.AlignLeft, text)

        # ---- the ridge end on: two slopes, a half-round ridge, a crest on top
        title(10, 4, "The ridge end on - each slope has its half")
        ax, ay = 180.0, 120.0                     # the ridge line
        sl = 0.62
        for sgn in (-1, 1):
            poly([(ax, ay), (ax + sgn * 150, ay + 150 * sl), (ax + sgn * 150, ay + 150 * sl + 12),
                  (ax, ay + 12)], tile)
        K_ = 60.0                                 # how far the ridge reaches down each slope
        rh = 34.0
        pts = []
        for i in range(25):
            t = i / 24.0
            x = ax - K_ + 2 * K_ * t
            pts.append((x, ay + abs(x - ax) * sl - rh * _m.sin(_m.pi * t) * 0.9 - 2))
        poly(pts + [(ax + K_, ay + K_ * sl), (ax - K_, ay + K_ * sl)], ridge)
        guide(ax, ay - 70, ax, ay + 40)
        # the crest: an upright fin on top, half each side of the middle
        ct = 5.0
        box(ax - ct, ay - rh - 30, 2 * ct, 32, QColor(90, 90, 96))
        dim(ax - K_, ay + K_ * sl + 14, ax, ay + 14, "K", ax - K_ / 2 - 14, ay + K_ * sl / 2 + 22)
        dim(ax + K_ + 24, ay, ax + K_ + 24, ay - rh, "L", ax + K_ + 36, ay - rh / 2)
        guide(ax, ay, ax + K_ + 28, ay)
        guide(ax, ay - rh, ax + K_ + 28, ay - rh)
        dim(ax - 40, ay - rh, ax - 40, ay - rh - 28, "P", ax - 52, ay - rh - 14)
        guide(ax - 44, ay - rh - 28, ax - ct, ay - rh - 28)
        dim(ax, ay - rh - 40, ax + ct, ay - rh - 40, "Q", ax + 18, ay - rh - 48)
        p.setFont(QFont())
        p.setPen(QColor(110, 110, 110))
        p.drawText(QRectF(ax + 6, ay + 40, 120, 14), Qt.AlignLeft, "middle of the ridge")

        # ---- the ridge from the side: tiles, gaps and a finial at the end
        title(10, 230, "The ridge from the side, with a finial")
        ry = 360.0
        box(20, ry, 330, 14, tile)                # the top course of the slope
        L_, G_ = 82.0, 8.0
        x = 30.0
        for i in range(4):
            box(x, ry - 26, L_, 26, ridge)
            x += L_ + G_
        dim(30, ry + 26, 30 + L_, ry + 26, "M", 30 + L_ / 2, ry + 38)
        dim(30 + L_, ry - 38, 30 + L_ + G_, ry - 38, "N", 30 + L_ + G_ / 2 + 12, ry - 48)
        # a spike finial at the left end
        fx, fw_, fh_ = 34.0, 22.0, 64.0
        poly([(fx, ry - 26), (fx + fw_, ry - 26), (fx + fw_, ry - 26 - fh_ * 0.6),
              (fx + fw_ / 2, ry - 26 - fh_), (fx, ry - 26 - fh_ * 0.6)], QColor(90, 90, 96))
        dim(fx - 12, ry - 26, fx - 12, ry - 26 - fh_, "R", fx - 22, ry - 26 - fh_ / 2)
        dim(fx, ry - 26 - fh_ - 10, fx + fw_, ry - 26 - fh_ - 10, "S", fx + fw_ / 2, ry - 26 - fh_ - 22)
        # the finial seen edge on (its thickness)
        title(250, ry + 20, "Finial edge on")
        ex = 290.0
        poly([(ex, ry - 30), (ex + 8, ry - 30), (ex + 8, ry - 30 - fh_ * 0.6), (ex + 4, ry - 30 - fh_),
              (ex, ry - 30 - fh_ * 0.6)], QColor(90, 90, 96))
        dim(ex, ry - 30 - fh_ - 10, ex + 8, ry - 30 - fh_ - 10, "T", ex + 4 + 16, ry - 30 - fh_ - 20)

        # ---- the flashing: a roof against a wall, end on
        title(10, 410, "Flashing where the roof meets a wall, end on")
        wx0, wx1 = 230.0, 270.0
        box(wx0, 430, wx1 - wx0, 200, wallc)      # the wall
        rsl = 0.45
        ry0 = 550.0
        poly([(40, ry0 + (wx0 - 40) * rsl), (wx0, ry0), (wx0, ry0 + 14), (40, ry0 + (wx0 - 40) * rsl + 14)],
             roofc)
        poly([(40, ry0 + (wx0 - 40) * rsl - 10), (wx0, ry0 - 10), (wx0, ry0), (40, ry0 + (wx0 - 40) * rsl)], tile)
        lt, up_, cov = 6.0, 80.0, 110.0
        x0 = wx0 - 1.0
        yt = ry0 - 10
        poly([(x0, yt - up_), (x0, yt - 1), (x0 - cov, yt - 1 + cov * rsl), (x0 - cov, yt - 1 + cov * rsl - lt),
              (x0 - lt, yt - lt - 1), (x0 - lt, yt - up_)], lead)
        dim(x0 - lt, yt - up_ - 10, x0, yt - up_ - 10, "V", x0 - lt - 14, yt - up_ - 18)
        dim(x0 - 24, yt - lt, x0 - 24, yt - up_, "W", x0 - 36, yt - up_ / 2)
        dim(x0, yt + 18, x0 - cov, yt + 18 + cov * rsl, "X", x0 - cov / 2 + 4, yt + 40 + cov * rsl / 2)
        p.setFont(QFont())
        p.setPen(QColor(90, 90, 90))
        p.drawText(QRectF(wx0 + 2, 610, 40, 14), Qt.AlignCenter, "wall")

        # ---- the notes
        f2 = QFont()
        f2.setPointSizeF(8.5)
        p.setFont(f2)
        p.setPen(QColor(60, 60, 60))
        notes = ["K  ridge width (down the slope)", "L  ridge height", "M  ridge tile length",
                 "N  gap between ridge tiles", "P  crest height", "Q  crest thickness (each half)",
                 "R  finial height", "S  finial width", "T  finial thickness",
                 "V  flashing thickness", "W  flashing up the wall", "X  flashing onto the roof"]
        for i, t in enumerate(notes):
            p.drawText(QRectF(10 if i < 6 else 185, 645 + (i % 6) * 14, 175, 14), Qt.AlignLeft | Qt.AlignVCenter, t)
        p.end()


class TilePreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 260)
        self.items = []
        self.msg = ""
        self.caption = ""

    def show_tiles(self, v):
        try:
            self.caption = preview_caption(v)
            self.items = preview_items(v)
            self.msg = ""
        except Exception as e:
            self.items, self.msg = [], str(e)
        self.update()

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen
        from PySide6.QtCore import QPointF, Qt
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(238, 238, 234))
        if not self.items:
            p.drawText(self.rect(), Qt.AlignCenter, self.msg or "No preview")
            p.end()
            return
        xs = [x for it in self.items for x, _ in it[1]]
        ys = [y for it in self.items for _, y in it[1]]
        w, h = self.width() - 16, self.height() - 16
        sc = min(w / ((max(xs) - min(xs)) or 1), h / ((max(ys) - min(ys)) or 1))
        ox = 8 + (w - (max(xs) - min(xs)) * sc) / 2 - min(xs) * sc
        oy = 8 + (h - (max(ys) - min(ys)) * sc) / 2 - min(ys) * sc
        h_cap = 18
        sc = min(w / ((max(xs) - min(xs)) or 1), (h - h_cap) / ((max(ys) - min(ys)) or 1))
        ox = 8 + (w - (max(xs) - min(xs)) * sc) / 2 - min(xs) * sc
        oy = 8 + h_cap + (h - h_cap - (max(ys) - min(ys)) * sc) / 2 - min(ys) * sc
        for _, pts, rgb, edge in self.items:
            col = QColor(*rgb)
            p.setBrush(col)
            p.setPen(QPen(col.darker(190), 0.9) if edge else QPen(col, 0.6))   # crisp tile edges
            p.drawPolygon(QPolygonF([QPointF(ox + x * sc, oy + y * sc) for x, y in pts]))
        # what you're looking at
        from PySide6.QtGui import QFont
        f = QFont()
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(50, 50, 50))
        p.drawText(8, 4, self.width() - 16, h_cap, Qt.AlignLeft | Qt.AlignVCenter, self.caption)
        p.end()


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------
FIELDS = [
    ('width', "A   Tile width (cover)", 10.0, 2000.0, 1, "How wide each tile covers, side by side."),
    ('length', "B   Tile length", 10.0, 3000.0, 1, "The whole length of a tile (used when tiles lap)."),
    ('gauge', "C   Gauge (course height)", 10.0, 2000.0, 1, "How far apart the courses are up the "
                                                             "roof - the part of each tile you see."),
    ('thick', "D   Tile thickness", 0.5, 100.0, 1, ""),
    ('gap', "F   Gap between tiles (side by side)", 0.0, 100.0, 2, "The groove between tiles next to "
                                                                    "each other in a course."),
    ('cgap', "J   Gap between courses", 0.0, 100.0, 2, "3D printing: the groove between one course and "
                                                       "the next, up the roof."),
    ('step', "E   Extra thickness at the bottom", 0.0, 100.0, 1, "Stepped courses only: each tile is this "
                                                                 "much thicker at its bottom edge."),
    ('depth', "G   Tail depth (shaped tiles)", 0.0, 500.0, 1, "How far the shaped bottom of a fishtail, "
                                                              "bullnose, beaver tail or club tile hangs down."),
    ('wave', "H   Wave height (pantiles, Romans, tin)", 0.0, 500.0, 1, "How high the rolls of a profiled tile are."),
    ('backing', "I   Backing sheet thickness", 0.0, 500.0, 1, "3D printing: a solid sheet under the "
                                                             "tiles, the shape of the roof, so the roof "
                                                             "prints as one piece. 0 = no backing."),
    ('lift', "U   Gap off the roof face", 0.0, 5.0, 3, "3D printing: a hair's gap between the tiles and the "
                                                   "roof face, so the slicer doesn't see faces lying exactly "
                                                   "on top of each other. 0.01 mm is plenty."),
]


RFIELDS = [
    ('ridge_w', "K   Ridge width (down the slope)", 10.0, 2000.0, 1, "How far each half of the ridge "
                                                                  "reaches down its slope."),
    ('ridge_h', "L   Ridge height", 5.0, 2000.0, 1, "How high the ridge stands above the ridge line."),
    ('ridge_len', "M   Ridge tile length", 20.0, 3000.0, 1, ""),
    ('ridge_gap', "N   Gap between ridge tiles", 0.0, 200.0, 1, ""),
    ('crest_h', "P   Crest height", 5.0, 2000.0, 1, ""),
    ('crest_t', "Q   Crest thickness (each half)", 0.5, 500.0, 1, "Half the crest is on each slope, so "
                                                                "the whole crest is twice this. 32 = 0.4 mm "
                                                                "at 1:80."),
    ('finial_h', "R   Finial height", 20.0, 5000.0, 1, ""),
    ('finial_w', "S   Finial width", 5.0, 2000.0, 1, ""),
    ('finial_t', "T   Finial thickness", 0.5, 500.0, 1, ""),
]


class TilesDialog(QDialog):
    def __init__(self, cur, viewport, tool):
        super().__init__(viewport)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.user_presets = load_presets()
        self._busy = False
        lay = QVBoxLayout(self)
        self.lbl = QLabel("Select a roof face - or click the whole building, or Subframe's 'Roof panels' "
                          "group, to tile every roof piece at once - then click 'Tile selected face(s) or "
                          "group'. Sizes are real-world mm.")
        self.lbl.setWordWrap(True)
        self.lbl.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl)
        self.lbl_report = QLabel()
        self.lbl_report.setWordWrap(True)
        self.lbl_report.setVisible(False)
        lay.addWidget(self.lbl_report)

        row = QHBoxLayout()
        lay.addLayout(row)
        from PySide6.QtWidgets import QTabWidget, QScrollArea
        self.preview = TilePreview()
        self.left = QTabWidget()
        self.left.addTab(self.preview, "Preview")
        key1 = QScrollArea()
        key1.setWidgetResizable(True)
        key1.setWidget(KeyDrawing())
        self.left.addTab(key1, "Key (A - J)")
        key2 = QScrollArea()
        key2.setWidgetResizable(True)
        key2.setWidget(KeyDrawing2())
        self.left.addTab(key2, "Key (K - X)")
        self.left.setTabToolTip(1, "What each lettered tile size is.")
        self.left.setTabToolTip(2, "What each lettered ridge, finial and flashing size is.")
        row.addWidget(self.left, 1)
        self.tabs = QTabWidget()
        row.addWidget(self.tabs, 1)
        page1 = QWidget()
        form = QFormLayout(page1)
        self.tabs.addTab(page1, "Tiles")

        self.cb_tile = QComboBox()
        for k, lab, _ in TILES:
            self.cb_tile.addItem(lab, k)
        form.addRow("Tile", self.cb_tile)
        self.cb_print = QCheckBox("3D printing - tiles don't overlap, flat on the roof")
        form.addRow(self.cb_print)
        self.cb_bond = QCheckBox("Courses offset by half a tile")
        form.addRow(self.cb_bond)
        self.cb_step = QCheckBox("Stepped courses (tiles thicker at the bottom edge)")
        self.cb_step.setToolTip("Off: flat tiles of even thickness, with grooves between them - "
                                "the look of a slated roof. On: each course is wedge-shaped.")
        form.addRow(self.cb_step)
        self.sp = {}
        for key, label, lo, hi, dec, tip in FIELDS:
            s = QDoubleSpinBox()
            s.setDecimals(dec)
            s.setRange(lo, hi)
            s.setSuffix(" mm")
            s.setKeyboardTracking(False)
            if tip:
                s.setToolTip(tip)
            lab = QLabel(label)
            if tip:
                lab.setToolTip(tip)
            form.addRow(lab, s)
            self.sp[key] = (s, lab)
            s.valueChanged.connect(self.changed)
        self.cb_turn = QComboBox()
        for lab, a in TURNS:
            self.cb_turn.addItem(lab, a)
        self.cb_turn.setToolTip("Which edge of the face the first course (the eaves) starts from.")
        form.addRow("Courses start", self.cb_turn)
        self.cb_flip = QCheckBox("Tiles on the other side of the face")
        form.addRow(self.cb_flip)
        self.cb_chim = QCheckBox("Go round chimneys")
        self.cb_chim.setToolTip("Tiles are cut round any chimney standing on the roof (one Chimneys built, or "
                                "your own group with 'chimney' in its name), with a groove's room round it, and "
                                "the ridge tiles stop either side of a chimney on the ridge.")
        form.addRow(self.cb_chim)

        # ---- ridge tab ----
        page2 = QWidget()
        rf = QFormLayout(page2)
        self.tabs.addTab(page2, "Ridge")
        self.cb_ridge = QCheckBox("Ridge tiles along the top edge")
        self.cb_ridge.setToolTip("Each roof face gets its half of the ridge (so it prints flat with "
                                 "the slope); the halves on the two slopes meet in the middle.")
        rf.addRow(self.cb_ridge)
        self.cb_rapart = QCheckBox("Ridge as its own piece for printing (not on the slopes)")
        self.cb_rapart.setChecked(True)
        self.cb_rapart.setToolTip("The ridge (both halves, with its finials) comes out as a piece of its "
                                  "own beside the slopes, so it prints on its own and the slopes print "
                                  "flat without it. In Scale Studio's Pieces page 'Groups 1 level in' "
                                  "then gives each slope and the ridge as separate pieces.")
        rf.addRow(self.cb_rapart)
        self.cb_rstyle = QComboBox()
        for k, lab in RIDGES:
            self.cb_rstyle.addItem(lab, k)
        rf.addRow("Ridge shape", self.cb_rstyle)
        self.cb_crest = QComboBox()
        for k, lab in CRESTS:
            self.cb_crest.addItem(lab, k)
        self.cb_crest.setToolTip("A decorative crest along the top of the ridge, like Victorian "
                                 "crested ridge tiles. It stands upright, half on each slope.")
        rf.addRow("Crest", self.cb_crest)
        self.cb_finial = QComboBox()
        for k, lab in FINIALS:
            self.cb_finial.addItem(lab, k)
        rf.addRow("Finials", self.cb_finial)
        self.cb_fends = QComboBox()
        for k, lab in FINIAL_ENDS:
            self.cb_fends.addItem(lab, k)
        rf.addRow("   Finials at", self.cb_fends)
        self.cb_fface = QComboBox()
        for k, lab in FINIAL_FACES:
            self.cb_fface.addItem(lab, k)
        self.cb_fface.setToolTip("Which way the finial's flat side faces. 'Facing out' turns it "
                                 "square to the ridge so you see its shape from the gable end; "
                                 "its thickness (T) then runs along the ridge.")
        rf.addRow("   Finials face", self.cb_fface)
        for key, label, lo, hi, dec, tip in RFIELDS:
            sp_ = QDoubleSpinBox()
            sp_.setDecimals(dec)
            sp_.setRange(lo, hi)
            sp_.setSuffix(" mm")
            sp_.setKeyboardTracking(False)
            if tip:
                sp_.setToolTip(tip)
            lab = QLabel(label)
            if tip:
                lab.setToolTip(tip)
            rf.addRow(lab, sp_)
            self.sp[key] = (sp_, lab)
            sp_.valueChanged.connect(self.changed)
        self.cb_ridge.toggled.connect(self.changed)
        for w_ in (self.cb_rstyle, self.cb_crest, self.cb_finial, self.cb_fends, self.cb_fface):
            w_.currentIndexChanged.connect(self.changed)

        add_flashing_tab(self, self.tabs, self.changed)

        prow = QHBoxLayout()
        prow.addWidget(QLabel("Preset:"))
        self.cb_preset = QComboBox()
        prow.addWidget(self.cb_preset, 1)
        b_up = QPushButton("\u25b2")
        b_dn = QPushButton("\u25bc")
        for b_, tip_ in ((b_up, "Moves the preset you have open up the list."),
                         (b_dn, "Moves the preset you have open down the list.")):
            b_.setToolTip(tip_)
            b_.setFixedWidth(28)
            prow.addWidget(b_)
        b_up.clicked.connect(lambda: self.move_preset(-1))
        b_dn.clicked.connect(lambda: self.move_preset(1))
        b_save = QPushButton("Save")
        b_save.setToolTip("Updates the preset you have open (no typing). For a new preset, use Save as.")
        b_saveas = QPushButton("Save as...")
        self.btn_preset_save = b_save
        prow.addWidget(b_save)
        prow.addWidget(b_saveas)
        b_saveas.clicked.connect(lambda: self.save_preset_as())
        b_del = QPushButton("Delete")
        b_del.setToolTip("Deletes the preset you have open (your own presets only).")
        b_dir = QPushButton("Folder")
        b_dir.setToolTip("Opens the folder your presets are saved in.")
        prow.addWidget(b_del)
        prow.addWidget(b_dir)
        b_del.clicked.connect(self.delete_preset)
        b_dir.clicked.connect(self.open_folder)
        lay.addLayout(prow)
        brow = QHBoxLayout()
        self.b_add = QPushButton("Tile selected face(s) or group")
        self.b_add.setDefault(True)
        b_close = QPushButton("Close")
        brow.addWidget(self.b_add)
        brow.addStretch(1)
        brow.addWidget(b_close)
        lay.addLayout(brow)

        self.cb_tile.currentIndexChanged.connect(self.tile_changed)
        for w in (self.cb_print, self.cb_bond, self.cb_flip, self.cb_step, self.cb_chim):
            w.toggled.connect(self.changed)
        self.cb_turn.currentIndexChanged.connect(self.changed)
        self.cb_preset.currentIndexChanged.connect(self.apply_preset)
        b_save.clicked.connect(self.save_clicked)
        self.b_add.clicked.connect(lambda: self.tool.add_from_dialog(self))
        b_close.clicked.connect(self.close)
        self.refresh_presets()
        self.set_values(cur)

    # ---- values ----
    def values(self):
        k = self.cb_tile.currentData() or 'plain'
        info = TILE_INFO[k][1]
        v = dict(tile=k, shape=info['shape'], profile=info['profile'],
                 print_mode=self.cb_print.isChecked(), bond=self.cb_bond.isChecked(),
                 stepped=self.cb_step.isChecked(),
                 ridge=self.cb_ridge.isChecked(), ridge_style=self.cb_rstyle.currentData() or 'round',
                 crest=self.cb_crest.currentData() or 'none', finial=self.cb_finial.currentData() or 'none',
                 finial_ends=self.cb_fends.currentData() or 'both',
                 finial_face=self.cb_fface.currentData() or 'out',
                 turn=self.cb_turn.currentData() or 0, flip=self.cb_flip.isChecked(),
                 round_chimneys=self.cb_chim.isChecked(), ridge_apart=self.cb_rapart.isChecked())
        for key, (s, _) in self.sp.items():
            v[key] = float(s.value())
        v.update(flashing_values(self))
        return v

    def set_values(self, d):
        self._busy = True
        try:
            if d.get('tile') in TILE_INFO:
                for i in range(self.cb_tile.count()):
                    if self.cb_tile.itemData(i) == d['tile']:
                        self.cb_tile.setCurrentIndex(i)
            self.cb_print.setChecked(bool(d.get('print_mode', True)))
            if 'stepped' in d:
                self.cb_step.setChecked(bool(d['stepped']))
            if 'ridge' in d:
                self.cb_ridge.setChecked(bool(d['ridge']))
            for cb, key in ((self.cb_rstyle, 'ridge_style'), (self.cb_crest, 'crest'),
                            (self.cb_finial, 'finial'), (self.cb_fends, 'finial_ends'),
                            (self.cb_fface, 'finial_face')):
                if d.get(key) is not None:
                    for i in range(cb.count()):
                        if cb.itemData(i) == d[key]:
                            cb.setCurrentIndex(i)
            self.cb_bond.setChecked(bool(d.get('bond', True)))
            self.cb_flip.setChecked(bool(d.get('flip', False)))
            self.cb_chim.setChecked(bool(d.get('round_chimneys', True)))
            self.cb_rapart.setChecked(bool(d.get('ridge_apart', True)))
            for i in range(self.cb_turn.count()):
                if self.cb_turn.itemData(i) == d.get('turn', 0):
                    self.cb_turn.setCurrentIndex(i)
            for key, (s, _) in self.sp.items():
                if d.get(key) is not None:
                    s.setValue(float(d[key]))
            set_flashing_values(self, d)
        finally:
            self._busy = False
        self.changed()

    def tile_changed(self, *_):
        if self._busy:
            return
        k = self.cb_tile.currentData()
        if k in TILE_INFO:
            info = dict(TILE_INFO[k][1])
            info['tile'] = k
            info['print_mode'] = self.cb_print.isChecked()
            info['backing'] = self.sp['backing'][0].value()
            self.set_values(info)

    def changed(self, *_):
        if self._busy:
            return
        v = self.values()
        self.cb_step.setEnabled(v['print_mode'])
        on = {'step': v['print_mode'] and v['stepped'], 'cgap': v['print_mode'],
              'lift': v['print_mode'], 'backing': v['print_mode'],
              'length': not v['print_mode'],
              'depth': v['shape'] != 'flat', 'wave': bool(v['profile'])}
        r = v['ridge']
        on.update({'ridge_w': r, 'ridge_h': r, 'ridge_len': r, 'ridge_gap': r,
                   'crest_h': r and v['crest'] != 'none', 'crest_t': r and v['crest'] != 'none',
                   'finial_h': r and v['finial'] != 'none', 'finial_w': r and v['finial'] != 'none',
                   'finial_t': r and v['finial'] != 'none'})
        for w_ in (self.cb_rstyle, self.cb_crest, self.cb_finial):
            w_.setEnabled(r)
        self.cb_fends.setEnabled(r and v['finial'] != 'none')
        self.cb_fface.setEnabled(r and v['finial'] != 'none')
        for key, ok in on.items():
            s, lab = self.sp[key]
            s.setEnabled(ok)
            lab.setEnabled(ok)
        self.preview.show_tiles(v)

    def show_report(self, text, bad=False):
        self.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if bad else "#2e7d32"))
        self.lbl_report.setText(text)
        self.lbl_report.setVisible(True)

    # ---- presets ----
    def preset_order(self):
        """Every preset's name, in the order you've put them (new ones go at the bottom)."""
        names = list(BUILTIN_PRESETS) + sorted(n for n in self.user_presets if n not in BUILTIN_PRESETS)
        order = [n for n in (_ui_settings().get('order') or []) if n in names]
        return order + [n for n in names if n not in order]

    def move_preset(self, step):
        name = self.cb_preset.currentData()
        if not name:
            QMessageBox.information(self, PLUGIN_NAME, "Pick a preset first, then move it up or down.")
            return
        order = self.preset_order()
        i = order.index(name)
        j = max(0, min(len(order) - 1, i + step))
        if i == j:
            return
        order[i], order[j] = order[j], order[i]
        _ui_settings_save(order=order)
        self.refresh_presets(select=name)

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

    def apply_preset(self, *_):
        name = self.cb_preset.currentData()
        if name and name in BUILTIN_PRESETS:
            self.set_values(BUILTIN_PRESETS[name])
        elif name and name in self.user_presets:
            self.set_values(self.user_presets[name])

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

    def open_folder(self):
        try:
            os.makedirs(PRESET_DIR, exist_ok=True)
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(PRESET_DIR))
        except Exception as e:
            QMessageBox.information(self, PLUGIN_NAME, "Presets folder:\n%s\n\n(%s)" % (PRESET_DIR, e))

    def save_clicked(self):
        self.save_preset()

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
            save_preset(name, self.values())
        except Exception as e:
            QMessageBox.warning(self, PLUGIN_NAME, "Could not save the preset:\n%s" % e)
            return False
        self.user_presets = load_presets()
        self.refresh_presets(select=name)
        return True


class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
class RoofTilesTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+R"
    description = "Covers a roof face with plain tiles, slates, shaped or profiled tiles; overlapping, " \
                  "or flat and non-overlapping for 3D printing."

    _dialog = None
    _saved = None

    def on_activate(self, viewport):
        dlg = RoofTilesTool._dialog
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
        cur.update(RoofTilesTool._saved or last_used())       # opens with what you last used
        dlg = TilesDialog(cur, viewport, self)
        RoofTilesTool._dialog = dlg

        def closed(*_):
            try:
                RoofTilesTool._saved = dict(dlg.values())
                remember_last(RoofTilesTool._saved)
            except Exception:
                pass
            RoofTilesTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass

    def add_from_dialog(self, dlg):
        v = dlg.values()
        RoofTilesTool._saved = dict(v)
        remember_last(v)
        viewport = dlg.viewport
        scene = getattr(viewport, 'scene', None)
        faces = selected_faces(scene) if scene is not None else []
        groups = selected_groups(scene) if scene is not None else []
        if not faces and not groups:
            QMessageBox.information(dlg, PLUGIN_NAME, "Select a roof face first - or click the building "
                                    "(or Subframe's 'Roof panels' group) to tile every roof piece in it.")
            return
        problems, notes = [], []
        # every slope to tile: [to_world, outline, holes, up, picked from a group?]
        slopes = []
        tree = scene_tree(scene) if scene is not None else {}
        for i, f in enumerate(faces):
            try:
                tw, outline, holes, up = face_frame(f, v['flip'], v['turn'])
                if outline is None:
                    raise ValueError("that face has no area")
                host = face_host(tree, f) if tree else None
                slopes.append([tw, outline, holes, up, False, host])
            except Exception as e:
                problems.append("Face %d: %s" % (i + 1, e))
        if groups:
            wf, skipped = faces_in_groups(groups)
            found = []
            for f in pick_roof_faces(wf, v):
                try:
                    # from a group: always on the top of the roof, eaves at the lowest edge
                    tw, outline, holes, up = face_frame(f, False, 0)
                    if outline is not None:
                        found.append([tw, outline, holes, up, getattr(f, 'host', None)])
                except Exception:
                    pass
            merge_coplanar(found)
            slopes += [s_[:4] + [True, s_[4]] for s_ in found]
            if not found:
                problems.append("No roof pieces found in the group you picked - roof pieces are the "
                                "sloping faces facing up, at least half a course wide.")
            if skipped:
                notes.append("Left out (not roof coverings): %s." % ", ".join(sorted(set(skipped))))
            if v.get('flip') or v.get('turn'):
                notes.append("Picked from a group, the tiles go on the top of each roof piece with the "
                             "eaves at its lowest edge ('Courses start' and 'other side' are for single faces).")
        if not slopes:
            QMessageBox.warning(dlg, PLUGIN_NAME, "\n".join(problems) or "No tiles fitted.")
            return
        # one group per slope, holding each piece of it on its own: the tiles (on their backing), its
        # half of the ridge, its finials, its flashing - so they can be printed apart
        slope_parts, total, ridges, nslopes = [], 0, 0, 0
        tile_name = TILE_INFO[v['tile']][0]
        # slates and tiles are named apart so Layers & Colours gives them their own colours;
        # the ridge and finials take the colour of the roof they are on
        slates = v['tile'] in ('slate', 'smallslate')
        tin = v['tile'] == 'tin'
        word = "slates" if slates else "sheets" if tin else "tiles"
        ridge_word = "ridge pieces" if slates else "ridge sheets" if tin else "ridge tiles"
        fin_word = "finials" if (slates or tin) else "tile finials"
        chims = find_chimneys(scene) if (v.get('round_chimneys', True) and scene is not None) else []
        clear = max(10.0, v.get('cgap', 0.0) if v.get('print_mode') else v.get('gap', 0.0))
        went_round = 0
        apart = bool(v.get('ridge_apart', True))
        ridge_sols, fin_sols, hip_sols = [], [], []
        hips_of = find_hips(slopes) if v.get('ridge') else [[] for _ in slopes]
        nhips = 0
        on_roof = 0
        for i, (tw, outline, holes, up, from_group, host) in enumerate(slopes):
            cuts = []
            my_hips = hips_of[i]
            if chims:
                ch = chimney_holes(tw, outline, chims, clear)
                if ch:
                    went_round += len(ch)
                    holes = list(holes) + ch
                    cuts = ridge_cuts(ch, outline, max(1.0, v.get('ridge_w', 0.0)) + clear)
            try:
                vs = dict(v, _up=up, _ridge_cuts=cuts, _hips=my_hips)
                if host is not None:
                    # on a roof that's there already: it is the backing
                    vs.update(backing=0.0, _sink=0.2)
                sols, count = lay_tiles(outline, holes, vs)
                nr = getattr(lay_tiles, 'ridges', 0)
                nh = getattr(lay_tiles, 'hips', 0)
                if v.get('ridge') and not nr and not nh and not from_group:
                    problems.append("Slope %d: no level top edge for a ridge (a hip end?)" % (i + 1))
            except Exception as e:
                problems.append("Slope %d: %s" % (i + 1, e))
                continue
            # split before mapping: the tags don't survive mapped()
            hps = [s for s in sols if getattr(s, 'hip', False)]
            sols = [s for s in sols if not getattr(s, 'hip', False)]
            fins = [s for s in sols if getattr(s, 'finial', False)]
            rids = [s for s in sols if getattr(s, 'ridge', False) and not getattr(s, 'finial', False)]
            tiles = [s for s in sols if not getattr(s, 'ridge', False) and not getattr(s, 'finial', False)]
            fl, fnotes = build_flashings(outline, sols, v, up)
            problems += ["Slope %d (flashing): %s" % (i + 1, n_) for n_ in fnotes]
            if not tiles:
                continue
            nslopes += 1
            k = nslopes
            pieces = [("Slope %d - %s - %s - %d %s" % (k, word, tile_name, count, word), [s.mapped(tw) for s in tiles])]
            # the finials stay with the ridge tiles they stand on: one piece, so they print on it
            if rids:
                if apart:
                    ridge_sols += [s.mapped(tw) for s in rids]
                    fin_sols += [s.mapped(tw) for s in fins]
                else:
                    pieces.append(("Slope %d - ridge half - %d %s%s" % (
                        k, nr, ridge_word, (" with %s" % fin_word) if fins else ""),
                        [s.mapped(tw) for s in rids + fins]))
                ridges += nr
            elif fins:
                if apart:
                    fin_sols += [s.mapped(tw) for s in fins]
                else:
                    pieces.append(("Slope %d - %s" % (k, fin_word), [s.mapped(tw) for s in fins]))
            if hps:
                nhips += nh
                if apart:
                    hip_sols += [s.mapped(tw) for s in hps]
                else:
                    pieces.append(("Slope %d - hip halves - %d hip %s" % (k, nh, word),
                                   [s.mapped(tw) for s in hps]))
            if fl:
                pieces.append(("Slope %d - flashing" % k, [s.mapped(tw) for s in fl]))
            if host is not None:
                on_roof += 1
            slope_parts.append(("Slope %d (%d pieces)" % (k, len(pieces)) if len(pieces) > 1 else None, pieces,
                                host))
            total += count
        if not slope_parts:
            QMessageBox.warning(dlg, PLUGIN_NAME, "\n".join(problems) or "No tiles fitted on that face.")
            return
        if ridge_sols or fin_sols:
            # the ridge on its own, beside the slopes: both halves together, with its finials
            rp = []
            if ridge_sols:
                rp.append(("Ridge - %d %s%s" % (ridges, ridge_word, (" with %s" % fin_word) if fin_sols else ""),
                           ridge_sols + fin_sols))
            elif fin_sols:
                rp.append(("Ridge - %s" % fin_word, fin_sols))
            slope_parts.append(("Ridge (%d pieces)" % len(rp) if len(rp) > 1 else None, rp, None))
        if hip_sols:
            # the hips on their own too, both halves of each together
            slope_parts.append((None, [("Hips - %d hip %s" % (nhips, word), hip_sols)], None))
        top = "Roof - %s%s" % (tile_name, " (for 3D printing)" if v['print_mode'] else "")
        if len(slope_parts) == 1 and slope_parts[0][0] and slope_parts[0][2] is None:
            slope_parts = [(top, slope_parts[0][1], None)]  # one slope: its group is the roof
        nf = self.add_to_scene(viewport, slope_parts, top)
        if nf is None:
            return
        npieces = sum(len(sp_[1]) for sp_ in slope_parts if sp_[2] is None)
        msg = "Added %d tiles%s%s on %d slope(s), %d faces." % (
            total, (" and %d ridge tiles" % ridges) if ridges else "",
            (" and %d hip tiles" % nhips) if nhips else "", nslopes, nf)
        if on_roof:
            msg += ("\nOn the roof that was there already (%d slope%s): no backing sheet, and each slope's "
                    "tiles are in a group with it ('%s...'), so in Scale Studio's Pieces page a slope and its "
                    "tiles come out as one piece." % (on_roof, "" if on_roof == 1 else "s", TILED))
        if npieces > 1:
            msg += ("\nOne group '%s': each slope is a group of its own, with its tiles, ridge half, finials "
                    "and flashing each a separate piece (%d pieces). To print them apart, in Scale Studio's "
                    "Pieces page pick 'Every group with faces (smallest pieces)' and tick 'Lay each piece "
                    "flat' - or 'Groups 1 level in' for each slope as one piece." % (top, npieces))
        if went_round:
            msg += "\nWent round the chimney on %d slope%s - the ridge stops either side of one on the ridge." % (
                went_round, "s" if went_round > 1 else "")
        if notes:
            msg += "\n" + "\n".join(notes)
        if problems:
            msg += "\n" + "\n".join(problems)
        dlg.show_report(msg, bad=bool(problems))

    def add_to_scene(self, viewport, slope_parts, top_name="Roof"):
        """One parent group holding a group per slope, each holding a group per piece of it (its
        tiles, ridge half, finials, flashing). The geometry is already in place, so no transforms
        are needed. slope_parts: [(slope group name or None, [(piece name, solids)])]."""
        stats = {'faces': 0, 'errors': 0, 'err': None}
        tol = 1e-4 * 0.001

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
                return None             # an older IngeTrazo: the pieces go in side by side

        scene = viewport.scene
        tree = scene_tree(scene)
        try:
            from core.mesh import Mesh
            from core.group import Group
        except Exception as e:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not add the tiles:\n%s" % e)
            return None
        rec = {'version': VERSION}

        def build(pieces, inv):
            kids = []
            for name, solids in pieces:
                mesh = Mesh()
                made = 0
                for so in solids:
                    verts = {}

                    def vx(p):
                        if inv is not None:
                            try:
                                r = inv.map(QVector3D(*p))
                                p = (float(r.x()), float(r.y()), float(r.z()))
                            except Exception:
                                pass
                        k = (round(p[0] / tol), round(p[1] / tol), round(p[2] / tol))
                        if k not in verts:
                            verts[k] = VertexWrapper(*p)
                        return verts[k]
                    for pts in so.faces:
                        try:
                            mesh.add_face([vx(p) for p in pts])
                            made += 1
                        except Exception as e:
                            stats['errors'] += 1
                            stats['err'] = e
                if not made:
                    continue
                stats['faces'] += made
                g = make_group(Group, mesh, name)
                g.component = False
                try:
                    ext = dict(getattr(g, 'ext', None) or {})
                    ext[TILES_KEY] = dict(rec)
                    g.ext = ext
                except Exception:
                    pass
                kids.append(g)
            return kids

        tops = []               # new groups of their own (as before)
        into = []               # [(list, host, holder or None to add to, new kids)]
        organise = []
        for entry in slope_parts:
            sname, pieces, host = (tuple(entry) + (None,))[:3]
            info = tree.get(id(host)) if host is not None else None
            if info is not None and isinstance(info[2], list):
                _g, _m, lst, par = info
                inv = _inverse(tree.get(id(par), (None, None))[1]) if par is not None else None
                if par is not None and tree.get(id(par), (None, None))[1] is not None and inv is None:
                    info = None         # can't work out where it is: tiles go in a group of their own
            if info is not None and isinstance(info[2], list):
                kids = build(pieces, inv)
                if not kids:
                    continue
                organise += kids
                if par is not None and str(getattr(par, 'name', '') or '').startswith(TILED) \
                        and isinstance(getattr(par, 'children', None), list):
                    into.append((None, host, par, kids))         # tiled before: these join it
                else:
                    try:
                        h = Group(name=TILED + str(getattr(host, 'name', '') or 'Roof slope'))
                        h.component = False
                    except Exception:
                        h = None
                    if h is None or not isinstance(getattr(h, 'children', None), list):
                        tops.append((sname, kids))               # an older IngeTrazo
                        continue
                    into.append((lst, host, h, kids))
                continue
            kids = build(pieces, None)
            if kids:
                tops.append((sname, kids))
        if stats['faces'] == 0:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not add the tiles:\nNo faces could be created (%s)."
                                % stats['err'])
            return None
        new_tops = []
        for sname, kids in tops:
            h = holder(Group, sname, kids) if (sname and len(kids) > 1) else None
            new_tops += [h] if h is not None else kids
        parent = holder(Group, top_name, new_tops) if len(new_tops) > 1 else None
        add_tops = [parent] if parent is not None else new_tops
        organise = add_tops + organise
        stale = []
        try:
            if any(e[0] is None for e in into):
                stale = old_ridges(getattr(viewport, 'scene', None), [e[1] for e in into if e[0] is None])
        except Exception as e:
            print("%s: old ridge not looked for: %s" % (PLUGIN_NAME, e))
        cmd = tiles_command(add_tops, into, organise, parent is None, stale)
        try:
            viewport.history.execute(cmd)
        except Exception as e:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not add the tiles:\n%s" % e)
            return None
        try:
            viewport.notify_scene_changed()
        except Exception:
            pass
        return stats['faces']


_PARENT_ATTRS = ('parent', '_parent')


def old_ridges(scene, hosts):
    """The ridge and hips made the last time these roof slopes were tiled (kept apart, they're
    groups of their own in the scene): groups of only ridge, hip or finial pieces, over these slopes."""
    def pts_of(g, out, depth=0):
        m = getattr(g, 'mesh', None)
        for v in _items(getattr(m, 'vertices', None)) if m is not None else []:
            p = _pos(v)
            if p is not None:
                out.append(p)
        if depth < 8:
            for c in _kids(g):
                pts_of(c, out, depth + 1)
        return out

    def names(g, depth=0):
        out = [str(getattr(g, 'name', '') or '')]
        if depth < 8:
            for c in _kids(g):
                out += names(c, depth + 1)
        return out
    hp = []
    for h in hosts:
        pts_of(h, hp)
    if not hp or scene is None:
        return []
    lo = [min(p[k] for p in hp) - 0.5 for k in range(3)]
    hi = [max(p[k] for p in hp) + 0.5 for k in range(3)]
    out = []
    for g in list(getattr(scene, 'groups', None) or []):
        nm = names(g)
        if not nm[0].startswith(("Roof - ", "Ridge", "Hips")):
            continue
        parts = [n for n in nm[1:] if n] or nm
        if not all(n.startswith(("Ridge", "Hips", "Roof - ")) for n in parts):
            continue
        gp = pts_of(g, [])
        if gp and all(lo[k] <= p[k] <= hi[k] for p in gp[::max(1, len(gp) // 200)] for k in range(3)):
            out.append(g)
    return out


def tiles_command(add_tops, into, organise, loose, stale=()):
    """One undo step: new groups added to the scene, and roof slopes put in a group with their
    tiles. into: [(the list the slope sits in, slope, its new group, tile groups)] - with no list,
    the group is one tiled before and the tiles join it."""
    try:
        from core.history import Command
    except Exception:
        Command = object
    _none = object()

    class RoofTilesCommand(Command):
        def __init__(self):
            self.done_once = False
            self.saved = []

        def _tidy(self, scene):
            try:
                scene.selection.clear()
            except Exception:
                pass
            try:
                scene.version += 1
            except Exception:
                pass

        def _set_parent(self, g, p):
            for a in _PARENT_ATTRS:
                if hasattr(g, a):
                    try:
                        setattr(g, a, p)
                    except Exception:
                        pass

        def do(self, scene):
            if not self.done_once:
                for g in organise:
                    _ed3d_organise(scene, g)
            self.saved = []
            for lst, host, h, kids in into:
                olds = {a: getattr(host, a, _none) for a in _PARENT_ATTRS}
                old_kids = list(h.children)
                if lst is None:
                    # tiled before: the old tiles (ridge, finials...) come off, the new ones go on -
                    # the roof slope itself stays (Undo puts the old tiles back)
                    h.children[:] = [host] + list(kids) if any(x is host for x in old_kids) else old_kids + list(kids)
                    for k in h.children:
                        self._set_parent(k, h)
                    self.saved.append((None, None, h, old_kids, olds))
                    continue
                i = next((k for k, x in enumerate(lst) if x is host), None)
                if i is None:
                    self.saved.append(None)
                    continue
                h.children[:] = [host] + list(kids)
                for k in h.children:
                    self._set_parent(k, h)
                lst[i] = h
                self.saved.append((lst, i, h, old_kids, olds))
            self.removed = []
            lst_ = getattr(scene, 'groups', None)
            for g in stale:                              # the old ridge and hips, kept apart last time
                if isinstance(lst_, list):
                    for k, x in enumerate(lst_):
                        if x is g:
                            self.removed.append((k, g))
                            del lst_[k]
                            break
            for g in add_tops:
                if hasattr(scene, 'add_group') and loose:
                    scene.add_group(g)
                else:
                    scene.groups.append(g)
            self.done_once = True
            self._tidy(scene)

        def undo(self, scene):
            for g in reversed(add_tops):
                lst = getattr(scene, 'groups', None)
                gone = False
                if isinstance(lst, list):
                    for k, x in enumerate(lst):
                        if x is g:
                            del lst[k]
                            gone = True
                            break
                if not gone:
                    for fn in ('remove_group', 'delete_group'):
                        if callable(getattr(scene, fn, None)):
                            try:
                                getattr(scene, fn)(g)
                                break
                            except Exception:
                                pass
            lst_ = getattr(scene, 'groups', None)
            for k, g in reversed(getattr(self, 'removed', [])):
                if isinstance(lst_, list):
                    lst_.insert(min(k, len(lst_)), g)
            for (lst_, host, h, kids), sv in reversed(list(zip(into, self.saved))):
                if sv is None:
                    continue
                lst, i, h, old_kids, olds = sv
                h.children[:] = old_kids
                if lst is not None and i < len(lst) and lst[i] is h:
                    lst[i] = host
                for a, val in olds.items():
                    if val is not _none:
                        try:
                            setattr(host, a, val)
                        except Exception:
                            pass
            self._tidy(scene)

    return RoofTilesCommand()


def run(viewport=None):
    RoofTilesTool().on_activate(viewport)
