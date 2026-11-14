# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Floor Plan for IngeTrazo
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
3D Floor Plan - the shell of a building from its floor plan, for IngeTrazo

  Shape         Rectangle, L, T or U shape from the overall floor size, your own corners
                typed in, or the outline of a level face you pick in the model.
  Walls         Set inside the outline by the wall thickness - one wall section for each side
                (4 for a rectangle, more for other shapes). The ends meet flat (butt joints:
                pick which walls run through) or angled (mitred) to meet the next wall.
                Long walls can be split into pieces that fit your print bed.
  Floors        Type each floor's height, or give the total height and how many floors to
                divide it into. The walls are split at each floor. Floors can be slabs the
                storeys stand on (with a locating lip under each one so the storeys sit square),
                panels that drop in inside the walls (on ledges), or none.
  Extras        Inside walls across or along the building, a base plate (plinth) under it all
                and a top plate (flat roof / ceiling) on top.

Every wall section, floor and plate is its own plain group, so Scale Studio's Pieces page
can lay each one flat on the print bed. Sizes are real-world mm, like the other plugins -
Scale Studio takes it down to your model scale. Ctrl+Alt+Shift+F.
"""

import os
import json
import math
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox, QCheckBox,
    QPushButton, QLabel, QMessageBox, QWidget, QInputDialog, QSpinBox, QTabWidget, QLineEdit,
    QPlainTextEdit
)

PLUGIN_NAME = "3D Floor Plan"
VERSION = "1.0"


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


SCALE = 0.001                 # IngeTrazo stores metres; the plan is worked out in real-world mm
PRESET_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Floor Plan")

SHAPES = [("Rectangle (4 walls)", 'rect'), ("L shape (6 walls)", 'L'), ("T shape (8 walls)", 'T'),
          ("U shape (8 walls)", 'U'), ("My own corners (typed in)", 'custom')]
JOINTS = [("Flat - the long walls run through", 'long'),
          ("Flat - the short walls run through", 'short'),
          ("Flat - swap at each floor (corners interlock)", 'swap'),
          ("Flat - each wall runs through at one end (pinwheel)", 'pinwheel'),
          ("Angled - mitred to meet the next wall", 'mitre')]
HEIGHT_MODES = [("Each floor its own height", 'each'), ("Divide the total height by the floors", 'divide')]
FLOOR_STYLES = [("Slabs - each storey stands on its floor", 'stacked'),
                ("Drop-in panels inside the walls", 'dropin'),
                ("No floors - walls only", 'none')]
GROUPINGS = [("A group for each floor, inside 'Floor plan'", 'storeys'),
             ("Every piece in one 'Floor plan' group", 'one'),
             ("Every piece a plain group on its own (no holder)", 'loose')]

# sizes are real-world mm (IngeTrazo stores metres); counts and words as they are
DEFAULTS = dict(
    shape='rect', length=0.0, width=0.0, cut_l=0.0, cut_w=0.0, corners_text='',
    wall_t=0.0, joint='long', split_len=0.0, gap=0.0,
    height_mode='each', storey_heights='', total_h=0.0, storeys=1,
    floor_style='stacked', floor_t=0.0, fit=0.0, lip_h=0.0, lip_fit=0.0,
    ledges=False, ledge_w=0.0, ledge_h=0.0, one_piece=False,
    cross_x='', cross_y='', part_t=0.0,
    base=False, base_t=0.0, base_over=0.0, top=False, top_t=0.0, top_over=0.0,
    grouping='storeys')
SIZE_KEYS = ('length', 'width', 'cut_l', 'cut_w', 'wall_t', 'split_len', 'gap', 'total_h', 'floor_t', 'fit',
             'lip_h', 'lip_fit', 'ledge_w', 'ledge_h', 'part_t', 'base_t', 'base_over', 'top_t', 'top_over')

BUILTIN_PRESETS = {
    "Two-storey house 7.5 x 6 m": dict(
        shape='rect', length=7500.0, width=6000.0, wall_t=300.0, joint='swap', height_mode='each',
        storey_heights='2700, 2600', storeys=2, floor_style='stacked', floor_t=200.0, lip_h=150.0, lip_fit=20.0,
        cross_x='3750', cross_y='', part_t=150.0, base=True, base_t=150.0, base_over=150.0, top=False),
    "Signal box - 2 floors": dict(
        shape='rect', length=6000.0, width=3600.0, wall_t=230.0, joint='long', height_mode='each',
        storey_heights='2400, 3000', storeys=2, floor_style='dropin', floor_t=150.0, fit=20.0, ledges=True,
        ledge_w=150.0, ledge_h=150.0, cross_x='', cross_y='', base=True, base_t=150.0, base_over=100.0),
    "L-shaped station building": dict(
        shape='L', length=18000.0, width=8000.0, cut_l=8000.0, cut_w=4000.0, wall_t=300.0, joint='long',
        height_mode='each', storey_heights='3600', storeys=1, floor_style='stacked', floor_t=200.0,
        lip_h=0.0, cross_x='6000', cross_y='', part_t=150.0, base=True, base_t=300.0, base_over=200.0),
    "Goods shed - long walls split for the print bed": dict(
        shape='rect', length=24000.0, width=10000.0, wall_t=350.0, joint='long', split_len=6000.0,
        height_mode='each', storey_heights='5500', storeys=1, floor_style='none', base=True, base_t=300.0,
        base_over=0.0),
    "Town house - 3 floors from total height": dict(
        shape='rect', length=5500.0, width=9000.0, wall_t=300.0, joint='swap', height_mode='divide',
        total_h=8400.0, storeys=3, floor_style='stacked', floor_t=200.0, lip_h=150.0, lip_fit=20.0,
        cross_x='', cross_y='4500', part_t=150.0, base=False, top=True, top_t=200.0, top_over=150.0),
    "U-shaped works round a yard": dict(
        shape='U', length=30000.0, width=15000.0, cut_l=14000.0, cut_w=8000.0, wall_t=350.0, joint='mitre',
        split_len=8000.0, height_mode='each', storey_heights='4000, 3500', storeys=2, floor_style='stacked',
        floor_t=250.0, lip_h=150.0, lip_fit=25.0, base=True, base_t=300.0, base_over=200.0),
}

COLOURS = {'wall': (196, 120, 90), 'wall2': (176, 104, 78), 'slab': (205, 185, 150), 'floor': (215, 195, 160),
           'ledge': (110, 85, 60), 'part': (225, 170, 120), 'base': (150, 150, 145), 'top': (120, 120, 125),
           'lip': (160, 140, 110)}
STOREY_NAMES = ["Ground floor", "First floor", "Second floor", "Third floor", "Fourth floor", "Fifth floor"]


def storey_name(k):
    return STOREY_NAMES[k] if k < len(STOREY_NAMES) else "Floor %d" % (k + 1)


def parse_list(text, what):
    """'2700, 2600' -> [2700.0, 2600.0]"""
    if isinstance(text, (list, tuple)):
        items = list(text)
    else:
        items = str(text or '').replace(';', ',').replace('\n', ',').replace(' ', ',').split(',')
    out = []
    for it in items:
        it = str(it).strip().lower().replace('mm', '')
        if not it:
            continue
        try:
            out.append(float(it))
        except ValueError:
            raise ValueError("%s: '%s' isn't a number. Type them with commas between, like 2700, 2600." % (what, it))
    return out


def parse_corners(text):
    """'0,0; 6000,0; 6000,4000; 0,4000' (or one corner a line) -> [(x, y)...]"""
    t = str(text or '').replace('\n', ';').replace('(', '').replace(')', '')
    out = []
    for part in t.split(';'):
        part = part.strip()
        if not part:
            continue
        bits = [b for b in part.replace(',', ' ').split() if b]
        if len(bits) != 2:
            raise ValueError("Corners: '%s' should be two numbers, x and y, like 6000, 4000." % part)
        try:
            out.append((float(bits[0]), float(bits[1])))
        except ValueError:
            raise ValueError("Corners: '%s' isn't two numbers." % part)
    return out


def plan_params(v):
    """The window's values, ready to build with (real-world mm)."""
    p = dict(DEFAULTS)
    p.update(v)
    for key in SIZE_KEYS:
        p[key] = float(p.get(key) or 0.0)
    p['storeys'] = max(1, int(p.get('storeys') or 1))
    t = p['wall_t']
    if t <= 0:
        raise ValueError("Set the wall thickness first (C, on the Walls page).")
    # sizes left at 0 are worked out from the wall thickness
    p['floor_t'] = p['floor_t'] if p['floor_t'] > 0 else 0.0
    p['ledge_w'] = p['ledge_w'] if p['ledge_w'] > 0 else t
    p['ledge_h'] = p['ledge_h'] if p['ledge_h'] > 0 else t
    p['part_t'] = p['part_t'] if p['part_t'] > 0 else 0.5 * t
    p['base_t'] = p['base_t'] if p['base_t'] > 0 else (p['floor_t'] or t)
    p['top_t'] = p['top_t'] if p['top_t'] > 0 else (p['floor_t'] or t)
    # the floor heights
    if p['height_mode'] == 'divide':
        if p['total_h'] <= 0:
            raise ValueError("Set the total height (G, on the Floors page).")
        p['_heights'] = [p['total_h'] / p['storeys']] * p['storeys']
    else:
        hs = parse_list(p.get('storey_heights', ''), "Floor heights")
        if not hs:
            raise ValueError("Type the height of each floor (F, on the Floors page), like 2700, 2600.")
        if any(h <= 0 for h in hs):
            raise ValueError("Every floor height needs to be more than 0.")
        p['_heights'] = hs
    if p['floor_style'] == 'stacked' and p['floor_t'] <= 0:
        raise ValueError("Set the floor thickness (H) - the storeys stand on their floor slabs.")
    if p['floor_style'] == 'stacked' and min(p['_heights']) <= p['floor_t']:
        raise ValueError("A floor is lower than the floor slab is thick (H).")
    p['_cross_x'] = parse_list(p.get('cross_x', ''), "Inside walls across")
    p['_cross_y'] = parse_list(p.get('cross_y', ''), "Inside walls along")
    return p


# ---------------------------------------------------------------------------
# 2D geometry (plan: x along the length, y across the width; mm)
# ---------------------------------------------------------------------------
def area2(poly):
    a = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        a += x1 * y2 - x2 * y1
    return a / 2.0


def clean(poly, eps=1e-6):
    """No repeated corners, no corners in the middle of a straight side; counter-clockwise."""
    if not poly:
        return None
    pts = []
    for q in poly:
        q = (float(q[0]), float(q[1]))
        if not pts or math.hypot(q[0] - pts[-1][0], q[1] - pts[-1][1]) > eps:
            pts.append(q)
    if len(pts) > 1 and math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) <= eps:
        pts.pop()
    changed = True
    while changed and len(pts) >= 3:
        changed = False
        for i in range(len(pts)):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
            cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            la = math.hypot(b[0] - a[0], b[1] - a[1])
            lc = math.hypot(c[0] - b[0], c[1] - b[1])
            if la < eps or lc < eps or abs(cr) <= 1e-9 * la * lc:
                pts.pop(i)
                changed = True
                break
    if len(pts) < 3:
        return None
    if area2(pts) < 0:
        pts.reverse()
    return pts


def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    return (dx / L, dy / L) if L > 0 else (1.0, 0.0)


def meet(p, u, q, w):
    """Where the line through p (direction u) crosses the line through q (direction w)."""
    den = u[0] * w[1] - u[1] * w[0]
    if abs(den) < 1e-12:
        return None
    s = ((q[0] - p[0]) * w[1] - (q[1] - p[1]) * w[0]) / den
    return (p[0] + s * u[0], p[1] + s * u[1])


def offset(poly, d):
    """The outline moved in by d (out, if d is less than 0), keeping its sides parallel."""
    n = len(poly)
    lines = []
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        u = _unit(a, b)
        nl = (-u[1], u[0])                          # left of the side = inside (counter-clockwise)
        lines.append(((a[0] + nl[0] * d, a[1] + nl[1] * d), u))
    out = []
    for i in range(n):
        q = meet(lines[i - 1][0], lines[i - 1][1], lines[i][0], lines[i][1])
        if q is not None:
            out.append(q)
    return clean(out)


def clip_half(poly, q, d):
    """The part of poly on the side of the line through q that d points to."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        fa = (a[0] - q[0]) * d[0] + (a[1] - q[1]) * d[1]
        fb = (b[0] - q[0]) * d[0] + (b[1] - q[1]) * d[1]
        if fa >= 0:
            out.append(a)
        if (fa >= 0) != (fb >= 0):
            t = fa / (fa - fb)
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    return out


def spans_on_line(poly, axis, c):
    """Where the line x = c (axis 0) or y = c (axis 1) is inside poly: [(from, to)...] along the other axis."""
    o = 1 - axis
    hits = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[axis] <= c < b[axis]) or (b[axis] <= c < a[axis]):
            t = (c - a[axis]) / (b[axis] - a[axis])
            hits.append(a[o] + t * (b[o] - a[o]))
    hits.sort()
    return [(hits[i], hits[i + 1]) for i in range(0, len(hits) - 1, 2) if hits[i + 1] - hits[i] > 1e-6]


def side_name(u):
    """Which way a wall faces, from the way its outline runs (counter-clockwise)."""
    nx, ny = u[1], -u[0]                           # outward
    if abs(ny) >= abs(nx):
        return "front" if ny < 0 else "back"
    return "right" if nx > 0 else "left"


# ---------------------------------------------------------------------------
# The outline
# ---------------------------------------------------------------------------
def make_outline(p):
    """The outside of the building, counter-clockwise, in mm. The front is along y = 0."""
    L, W, cl, cw = p['length'], p['width'], p['cut_l'], p['cut_w']
    s = p['shape']
    t = p['wall_t']
    if s == 'custom':
        pts = parse_corners(p.get('corners_text', ''))
        if len(pts) < 3:
            raise ValueError("Type at least 3 corners on the Shape page, like 0,0; 6000,0; 6000,4000; 0,4000.")
        o = clean(pts)
        if o is None:
            raise ValueError("Those corners don't make a shape (they're all in a line).")
        return o
    if L <= 0 or W <= 0:
        raise ValueError("Set the length and width first (A and B, on the Shape page).")
    if L <= 2 * t or W <= 2 * t:
        raise ValueError("The building is too small for walls %.0f mm thick." % t)
    if s == 'rect':
        return clean([(0, 0), (L, 0), (L, W), (0, W)])
    if cl <= 0 or cw <= 0:
        raise ValueError("Set the cut-out sizes (D and E, on the Shape page) for this shape.")
    if s == 'L':
        if cl >= L - 2 * t or cw >= W - 2 * t:
            raise ValueError("The cut-out (D x E) leaves no room for the walls - make it smaller.")
        return clean([(0, 0), (L, 0), (L, W - cw), (L - cl, W - cw), (L - cl, W), (0, W)])
    if s == 'T':
        if 2 * cl >= L - 2 * t or cw >= W - 2 * t:
            raise ValueError("The cut-outs (D x E, one each side) leave no room for the stem - make them smaller.")
        return clean([(cl, 0), (L - cl, 0), (L - cl, cw), (L, cw), (L, W), (0, W), (0, cw), (cl, cw)])
    if s == 'U':
        a = (L - cl) / 2.0
        if a <= 2 * t or cw >= W - 2 * t:
            raise ValueError("The yard (D x E) leaves no room for the arms - make it smaller.")
        return clean([(0, 0), (a, 0), (a, cw), (a + cl, cw), (a + cl, 0), (L, 0), (L, W), (0, W)])
    raise ValueError("Unknown shape.")


# ---------------------------------------------------------------------------
# The walls: one section per side, their ends flat or angled
# ---------------------------------------------------------------------------
def _joint(rule, a, b, us, lens, storey):
    """At the corner between wall a and the next wall b: 'm' mitre, 'a' or 'b' runs through."""
    if rule == 'mitre':
        return 'm'
    if rule == 'pinwheel':
        return 'b'
    r = rule
    if rule == 'swap':
        r = 'long' if storey % 2 == 0 else 'short'
    la, lb = lens[a], lens[b]
    if abs(la - lb) < 1e-3:
        # the same length (a square): the front and back run through for 'long', the sides for 'short'
        ha, hb = abs(us[a][0]), abs(us[b][0])
        a_wins = ha >= hb
    else:
        a_wins = la > lb
    if r == 'short':
        a_wins = not a_wins
    return 'a' if a_wins else 'b'


def wall_quads(outline, t, rule, storey=0):
    """[(quad, side index)]: each side's wall, inside the outline, ends meeting as the rule says."""
    n = len(outline)
    us = [_unit(outline[i], outline[(i + 1) % n]) for i in range(n)]
    lens = [math.hypot(outline[(i + 1) % n][0] - outline[i][0], outline[(i + 1) % n][1] - outline[i][1])
            for i in range(n)]
    outer = [(outline[i], us[i]) for i in range(n)]
    inner = [((outline[i][0] - us[i][1] * t, outline[i][1] + us[i][0] * t), us[i]) for i in range(n)]
    ends = [None] * n      # (outer point, inner point) at the end of each wall
    starts = [None] * n

    def m(l1, l2):
        return meet(l1[0], l1[1], l2[0], l2[1])

    def along(pt, origin, u):
        return (pt[0] - origin[0]) * u[0] + (pt[1] - origin[1]) * u[1]

    for k in range(n):
        a, b = (k - 1) % n, k
        P = outline[k]
        j = _joint(rule, a, b, us, lens, storey)
        if j == 'm':
            e = (m(outer[a], outer[b]), m(inner[a], inner[b]))
            ends[a], starts[b] = e, e
            continue
        # the two lines of b (its outside and inside faces), as wall a reaches them
        cand_a = sorted((along(m(outer[a], lb), P, us[a]), lb) for lb in (outer[b], inner[b])
                        if m(outer[a], lb) is not None)
        cand_b = sorted((along(m(outer[b], la), P, us[b]), la) for la in (outer[a], inner[a])
                        if m(outer[b], la) is not None)
        if j == 'a':          # a runs right through the corner, b stops against it
            lb = cand_a[-1][1]
            la = cand_b[-1][1]
        else:                 # b runs through, a stops against it
            lb = cand_a[0][1]
            la = cand_b[0][1]
        ends[a] = (m(outer[a], lb), m(inner[a], lb))
        starts[b] = (m(outer[b], la), m(inner[b], la))
    out = []
    for i in range(n):
        (so, si), (eo, ei) = starts[i], ends[i]
        q = clean([so, eo, ei, si])
        if q:
            out.append((q, i))
    return out


def split_quad(quad, u, max_len, gap):
    """A wall cut into equal pieces no longer than max_len along u (0 = not cut); gap/2 off each end."""
    s = [q[0] * u[0] + q[1] * u[1] for q in quad]
    s0, s1 = min(s), max(s)
    L = s1 - s0
    k = int(math.ceil(L / max_len - 1e-9)) if max_len > 0 else 1
    k = max(1, k)
    pieces = []
    for i in range(k):
        a = s0 + L * i / k + (gap / 2.0 if gap > 0 else 0.0)
        b = s0 + L * (i + 1) / k - (gap / 2.0 if gap > 0 else 0.0)
        pc = list(quad)
        if i > 0 or gap > 0:
            pc = clip_half(pc, (u[0] * a, u[1] * a), u)
        if (i < k - 1 or gap > 0) and len(pc) >= 3:
            pc = clip_half(pc, (u[0] * b, u[1] * b), (-u[0], -u[1]))
        pc = clean(pc) if len(pc) >= 3 else None
        if pc:
            pieces.append(pc)
    return pieces


def partition_rects(inner, p):
    """The inside walls: across the building at each x, along it at each y (from the outline's corner)."""
    pt, gap = p['part_t'], p['gap']
    xs = [q[0] for q in p['_outline']]
    ys = [q[1] for q in p['_outline']]
    x0, y0 = min(xs), min(ys)
    out = []
    xcuts = []
    for c in p['_cross_x']:
        cx = x0 + c
        xcuts.append(cx)
        for a, b in spans_on_line(inner, 0, cx):
            a, b = a + gap, b - gap
            if b - a > pt:
                out.append(([(cx - pt / 2, a), (cx + pt / 2, a), (cx + pt / 2, b), (cx - pt / 2, b)], 'across'))
    for c in p['_cross_y']:
        cy = y0 + c
        for a, b in spans_on_line(inner, 1, cy):
            # broken where an across wall runs through it
            cuts = sorted(x for x in xcuts if a < x < b)
            pieces = []
            lo = a
            for x in cuts:
                pieces.append((lo, x - pt / 2))
                lo = x + pt / 2
            pieces.append((lo, b))
            for a2, b2 in pieces:
                a2, b2 = a2 + gap, b2 - gap
                if b2 - a2 > pt:
                    out.append(([(a2, cy - pt / 2), (b2, cy - pt / 2), (b2, cy + pt / 2), (a2, cy + pt / 2)], 'along'))
    return [(clean(r), k) for r, k in out if clean(r)]


# ---------------------------------------------------------------------------
# Solids
# ---------------------------------------------------------------------------
class PSolid:
    """A closed solid: faces (lists of 3D corners), holes[i] = loops cut out of faces[i]."""
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
            x0, y0, z0 = pts[0]
            for j in range(1, len(pts) - 1):
                (x1, y1, z1), (x2, y2, z2) = pts[j], pts[j + 1]
                v += x0 * (y1 * z2 - z1 * y2) - y0 * (x1 * z2 - z1 * x2) + z0 * (x1 * y2 - y1 * x2)
        return v / 6.0

    def fix(self):
        if self.volume() < 0:
            self.faces = [list(reversed(f)) for f in self.faces]
            self.holes = {i: [list(reversed(h)) for h in hs] for i, hs in self.holes.items()}
        return self

    def mapped(self, fn):
        s = PSolid()
        s.faces = [[fn(q) for q in f] for f in self.faces]
        s.holes = {i: [[fn(q) for q in h] for h in hs] for i, hs in self.holes.items()}
        return s.fix()


def prism(poly, z0, z1):
    """A solid standing on a counter-clockwise outline, from z0 up to z1."""
    s = PSolid()
    s.add([(x, y, z1) for x, y in poly])
    s.add([(x, y, z0) for x, y in reversed(poly)])
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        s.add([(ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1)])
    return s.fix()


def stepped(poly, z0, z1, lip, lip_h):
    """A slab from z0 to z1 with a lip (a smaller outline) standing down lip_h underneath it."""
    s = PSolid()
    s.add([(x, y, z1) for x, y in poly])
    s.add([(x, y, z0) for x, y in reversed(poly)], holes=[[(x, y, z0) for x, y in lip]])
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        s.add([(ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1)])
    zl = z0 - lip_h
    m = len(lip)
    for i in range(m):
        (ax, ay), (bx, by) = lip[i], lip[(i + 1) % m]
        s.add([(ax, ay, zl), (bx, by, zl), (bx, by, z0), (ax, ay, z0)])
    s.add([(x, y, zl) for x, y in reversed(lip)])
    return s.fix()


# ---------------------------------------------------------------------------
# The whole building
# ---------------------------------------------------------------------------
class Piece:
    def __init__(self, name, kind, storey, poly, z0, z1, lip=None, lip_h=0.0):
        self.name, self.kind, self.storey = name, kind, storey
        self.poly, self.z0, self.z1, self.lip, self.lip_h = poly, z0, z1, lip, lip_h

    def solid(self):
        if self.lip and self.lip_h > 0:
            return stepped(self.poly, self.z0, self.z1, self.lip, self.lip_h)
        return prism(self.poly, self.z0, self.z1)


def build_plan(p, outline):
    """Every piece of the building: [Piece], and notes for the report."""
    outline = clean(outline)
    if outline is None:
        raise ValueError("That outline doesn't make a shape.")
    p['_outline'] = outline
    t = p['wall_t']
    inner = offset(outline, t)
    if inner is None or area2(inner) <= 0:
        raise ValueError("The walls are too thick for this shape - nothing is left inside.")
    p['_inner'] = inner
    hs = p['_heights']
    style = p['floor_style']
    ft = p['floor_t'] if style != 'none' else 0.0
    gap = p['gap']
    zs = [sum(hs[:k]) for k in range(len(hs) + 1)]
    H = zs[-1]
    pieces = []
    n_out = len(outline)
    us = [_unit(outline[i], outline[(i + 1) % n_out]) for i in range(n_out)]
    names = {}
    seen = {}
    for i, u in enumerate(us):
        sn = side_name(u)
        seen[sn] = seen.get(sn, 0) + 1
    count = {}
    for i, u in enumerate(us):
        sn = side_name(u)
        count[sn] = count.get(sn, 0) + 1
        names[i] = "Wall %d (%s%s)" % (i + 1, sn, (" %d" % count[sn]) if seen[sn] > 1 else "")
    one_piece = p.get('one_piece') and style != 'stacked'
    storeys = [0] if one_piece else list(range(len(hs)))
    lip_ok = style == 'stacked' and p['lip_h'] > 0
    lip_poly = offset(inner, p['lip_fit']) if lip_ok else None

    # walls
    for k in storeys:
        if one_piece:
            wz0, wz1, label = 0.0, H, "Walls"
        else:
            wz0 = zs[k] + (ft if style == 'stacked' else 0.0)
            wz1 = zs[k + 1]
            label = storey_name(k)
        for quad, i in wall_quads(outline, t, p['joint'], k):
            parts = split_quad(quad, us[i], p['split_len'], gap)
            for j, pc in enumerate(parts):
                nm = "%s - %s%s" % (label, names[i], (" part %d" % (j + 1)) if len(parts) > 1 else "")
                pieces.append(Piece(nm, 'wall', k, pc, wz0, wz1))
    # floors
    ledge_ring = None
    if style == 'stacked':
        for k in range(len(hs)):
            lp = lip_poly if (k > 0 and lip_ok) else None
            pieces.append(Piece("%s - Floor slab" % storey_name(k), 'slab', k, outline, zs[k], zs[k] + ft,
                                lip=lp, lip_h=p['lip_h'] if lp else 0.0))
    elif style == 'dropin':
        fl = offset(inner, p['fit'])
        if fl is None:
            raise ValueError("The floor fit (J) leaves no floor.")
        for k in range(len(hs)):
            pieces.append(Piece("%s - Floor panel" % storey_name(k), 'floor', k, fl, zs[k], zs[k] + ft))
        if p.get('ledges'):
            ledge_ring = wall_quads(inner, p['ledge_w'], 'mitre')
            for k in range(1, len(hs)):
                for j, (q, _i) in enumerate(ledge_ring):
                    pieces.append(Piece("%s - Ledge %d (under the %s)" % (storey_name(k - 1), j + 1,
                                                                         storey_name(k).lower()), 'ledge', k - 1, q,
                                        zs[k] - p['ledge_h'], zs[k]))
    # inside walls, standing on each floor up to the next
    rects = partition_rects(inner, p) if (p['_cross_x'] or p['_cross_y']) else []
    for k in range(len(hs)):
        z0 = zs[k] + ft
        z1 = zs[k + 1]
        if style == 'stacked' and k < len(hs) - 1 and lip_ok:
            z1 -= p['lip_h']                        # clear of the lip under the floor above
        if style == 'dropin' and k < len(hs) - 1 and p.get('ledges'):
            z1 -= p['ledge_h']
        if z1 - z0 <= 1e-6:
            continue
        for j, (r, kind) in enumerate(rects):
            pieces.append(Piece("%s - Inside wall %d (%s)" % (storey_name(k), j + 1, kind), 'part', k, r, z0, z1))
    # base and top plates
    if p.get('base'):
        bp = offset(outline, -p['base_over']) if p['base_over'] > 0 else outline
        pieces.append(Piece("Base plate", 'base', -1, bp, -p['base_t'], 0.0))
    if p.get('top'):
        tp = offset(outline, -p['top_over']) if p['top_over'] > 0 else outline
        lp = None
        if lip_ok:
            lp = lip_poly
        pieces.append(Piece("Top plate", 'top', len(hs), tp, H, H + p['top_t'], lip=lp,
                            lip_h=p['lip_h'] if lp else 0.0))
    notes = dict(H=H, zs=zs, inner_area=abs(area2(inner)) / 1e6, outer_area=abs(area2(outline)) / 1e6,
                 walls=len(outline), wall_len=sum(math.hypot(outline[(i + 1) % n_out][0] - outline[i][0],
                                                             outline[(i + 1) % n_out][1] - outline[i][1])
                                                  for i in range(n_out)) / 1000.0)
    return pieces, notes


# ---------------------------------------------------------------------------
# Reading a level face from the model (for 'Build on selected face')
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


def _world_faces(g):
    try:
        from core.group import world_mesh
        m = world_mesh(g)
        if m is not None:
            return list(_items(getattr(m, 'faces', None)))
    except Exception:
        pass
    out = []
    seen = set()

    def walk(e, depth=0):
        if depth > 50:
            return
        m = getattr(e, 'mesh', None)
        if m is not None and id(m) not in seen:
            seen.add(id(m))
            out.extend(_items(getattr(m, 'faces', None)))
        for ch in _items(getattr(e, 'children', None)) + _items(getattr(e, 'groups', None)):
            walk(ch, depth + 1)
    walk(g)
    return out


def selected_level_outline(scene):
    """The biggest level face in the selection (a face, or in a picked group): (outline mm, z mm)."""
    faces = []
    for e in _items(getattr(scene, 'selection', None)):
        if getattr(e, 'mesh', None) is not None:
            faces += _world_faces(e)
            continue
        vs = getattr(e, 'vertices', None)
        if vs is not None and not callable(vs) and len(_items(vs)) >= 3:
            faces.append(e)
    best = None
    for f in faces:
        pts = [q for q in (_pos(v) for v in _items(getattr(f, 'vertices', None))) if q is not None]
        if len(pts) < 3:
            continue
        zs = [q[2] for q in pts]
        if max(zs) - min(zs) > 1e-6:
            continue                                   # not level
        poly = clean([(q[0] / SCALE, q[1] / SCALE) for q in pts])
        if poly is None:
            continue
        key = (round(abs(area2(poly)), 0), zs[0])
        if best is None or key > best[0]:
            best = (key, poly, zs[0] / SCALE)
    if best is None:
        return None, None
    return best[1], best[2]


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
    'Shape': "The shape of the building in plan. A rectangle has 4 walls; L, T and U shapes have more. "
             "'My own corners' takes any shape you type in.",
    'Corners': "Each corner of the outside of the building, x and y in real-world mm, one a line or with ';' "
               "between them - going round the building either way. The front is along y = 0.",
    'Wall ends meet': "Flat ends: one wall runs right through the corner and the other stops square against it. "
                      "Angled: both ends cut at the angle, meeting in a mitre.",
    'Heights': "Type each floor's height, or give the total height and the number of floors and it's "
               "divided equally.",
    'Number of floors': "How many floors to divide the total height (G) into.",
    'Floors': "Slabs: every storey stands on its floor slab (print each storey on its own and stack them). "
              "Drop-in: the walls go up in storeys and the floor panels drop in inside them, onto ledges. "
              "Or no floors at all.",
    'Ledges under the drop-in floors': "A ledge round the inside of the walls under each upper floor, for "
                                       "the floor panel to rest on (each side its own piece).",
    'Walls in one piece, full height': "The walls aren't split at the floors - one piece each, from the "
                                       "bottom to the top (drop-in floors or no floors).",
    'Base plate (plinth) under it all': "A plate under the whole building, standing out past the walls (Q) - "
                                        "a plinth, or a base to fix it down.",
    'Top plate (flat roof / ceiling)': "A plate on top of the walls: a flat roof, or a ceiling for the "
                                       "roof to sit on.",
    'Pieces go': "How the pieces are grouped. Every piece is always its own plain group (not a component), "
                 "so Scale Studio can lay each one flat.",
    'Build floor plan': "Builds it at the origin of the model, from the Shape page.",
    'Build on selected face': "Pick a level face (or a group with a floor or base in it) and the walls go "
                              "up round its edge - any shape you've drawn.",
    'Floor shown': "Which floor the plan view shows.",
}
EDDY_TIPS_END = None

# (key, label, min, max, decimals, tip)
SHAPE_FIELDS = [
    ('length', "A   Length (overall)", 0.0, 500000.0, 1, "The overall length of the building, outside the "
                                                         "walls, along the front."),
    ('width', "B   Width (overall)", 0.0, 500000.0, 1, "The overall width, outside the walls, front to back."),
    ('cut_l', "D   Cut-out length", 0.0, 500000.0, 1, "L: the corner taken out at the back right, along the "
                                                      "length. T: each corner taken out at the front. U: "
                                                      "how wide the yard in the front is."),
    ('cut_w', "E   Cut-out width", 0.0, 500000.0, 1, "How deep the cut-out (or the yard) goes, front to back."),
]
WALL_FIELDS = [
    ('wall_t', "C   Wall thickness", 0.0, 10000.0, 1, "How thick the walls are. They're set in from the outline "
                                                      "by this much. 300 = 4 mm printed in OO."),
    ('split_len', "U   Longest wall piece", 0.0, 500000.0, 0, "Walls longer than this are cut into equal pieces "
                                                              "that fit your print bed (real-world mm: in OO a "
                                                              "200 mm bed = 15240). 0 = never cut."),
    ('gap', "V   Gap between pieces", 0.0, 100.0, 2, "A small gap where pieces meet, if your prints need a bit "
                                                     "of room to fit together. 0 = they just touch."),
    ('part_t', "T   Inside wall thickness", 0.0, 10000.0, 1, "How thick the inside walls are. 0 = half the wall "
                                                             "thickness."),
]
FLOOR_FIELDS = [
    ('total_h', "G   Total height", 0.0, 500000.0, 1, "The height from the bottom of the walls to the top, "
                                                      "divided equally between the floors."),
    ('floor_t', "H   Floor thickness", 0.0, 10000.0, 1, "How thick the floor slabs or panels are. With slabs, "
                                                        "it's part of each floor's height."),
    ('fit', "J   Floor fit (room to spare)", 0.0, 1000.0, 1, "Drop-in floors: room left between the floor panel "
                                                             "and the walls, so it drops in easily."),
    ('lip_h', "K   Locating lip depth", 0.0, 5000.0, 1, "Slabs: a lip under each upper slab (and the top plate) "
                                                         "that drops inside the walls below, so the storeys "
                                                         "sit square. 0 = no lip."),
    ('lip_fit', "L   Lip fit (room to spare)", 0.0, 1000.0, 1, "Room left between the lip and the walls."),
    ('ledge_w', "M   Ledge width", 0.0, 5000.0, 1, "How far the ledges stand out from the walls. 0 = the wall "
                                                   "thickness."),
    ('ledge_h', "N   Ledge height", 0.0, 5000.0, 1, "How tall the ledges are. 0 = the wall thickness."),
]
PLATE_FIELDS = [
    ('base_t', "P   Base plate thickness", 0.0, 10000.0, 1, "How thick the base plate is. 0 = the floor "
                                                            "thickness."),
    ('base_over', "Q   Base plate stands out", 0.0, 10000.0, 1, "How far the base plate stands out past the "
                                                                "walls all round. 0 = flush."),
    ('top_t', "R   Top plate thickness", 0.0, 10000.0, 1, "How thick the top plate is. 0 = the floor thickness."),
    ('top_over', "S   Top plate overhang", 0.0, 10000.0, 1, "How far the top plate hangs past the walls (eaves "
                                                            "of a flat roof). 0 = flush."),
]
ALL_FIELDS = SHAPE_FIELDS + WALL_FIELDS + FLOOR_FIELDS + PLATE_FIELDS

INFO_TEXT = ("<b>How to use it</b><br>"
             "Pick a shape and type the overall size (Shape page), the wall thickness (Walls page) and the "
             "floor heights (Floors page), then click 'Build floor plan'. It's built at the origin. Or draw "
             "any outline as a level face, select it and click 'Build on selected face' - the walls go up "
             "inside its edge.<br><br>"
             "<b>Wall ends</b><br>"
             "Flat: one wall runs through each corner and the other stops square against it - pick the long "
             "walls, the short walls, swapped at each floor so the corners interlock like brickwork, or the "
             "pinwheel (every wall through at one end, so walls of the same length come out the same). "
             "Angled: mitred ends meeting at the corner.<br><br>"
             "<b>Floors</b><br>"
             "Slabs: each storey stands on its own floor slab, with a locating lip under it (K) - print each "
             "storey and stack them. Drop-in: the floor panels drop in inside the walls onto ledges.<br><br>"
             "<b>Printing</b><br>Every piece is its own plain group: in Scale Studio's Pieces page pick 'Every "
             "group with faces (smallest pieces)' and tick 'Lay each piece flat'. Long walls can be cut to fit "
             "your print bed (U). Add the windows and doors with Period Windows and Period Doors, and the "
             "frame with Subframe.<br><br>"
             "Sizes are real-world mm - Scale Studio takes it down to your model scale.")


def _auto_sizes(v):
    t = float(v.get('wall_t', 0.0) or 0.0)
    ft = float(v.get('floor_t', 0.0) or 0.0)
    return {'ledge_w': t, 'ledge_h': t, 'part_t': 0.5 * t, 'base_t': ft or t, 'top_t': ft or t}


PIECE_KEYS = [
    ("Floor slab", ('floor_t', 'lip_h', 'lip_fit')),
    ("Floor panel", ('floor_t', 'fit')),
    ("Ledge", ('ledge_w', 'ledge_h')),
    ("Inside wall", ('part_t',)),
    ("Base plate", ('base_t', 'base_over')),
    ("Top plate", ('top_t', 'top_over', 'lip_h')),
    ("Wall", ('wall_t', 'split_len', 'gap', 'length', 'width')),
]


def piece_keys(name):
    name = str(name or '')
    for word, keys in PIECE_KEYS:
        if word in name:
            if word == "Wall" and not (" - Wall " in name):
                continue
            return keys
    return ()


class KeyDrawing(QWidget):
    """A drawing that shows what each lettered size is."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 660)

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
        from PySide6.QtCore import QPointF, QRectF, Qt
        import math as _m
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 246))
        k = min(float(self.width()) / 360.0, self.height() / 660.0)
        p.scale(k, k)
        red = QColor(200, 40, 40)
        wallc, inside = QColor(196, 120, 90), QColor(240, 232, 215)
        slab, floor_c = QColor(205, 185, 150), QColor(215, 195, 160)
        f = QFont()
        f.setBold(True)
        f.setPointSizeF(9.5)
        p.setFont(f)

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

        p.setPen(QColor(60, 60, 60))
        p.drawText(QRectF(10, 4, 340, 18), Qt.AlignLeft, "The plan, from above (an L shape)")
        # ---- the plan: an L, walls inside the outline, front at the bottom
        X0, X1, Y0, Y1 = 40.0, 320.0, 40.0, 230.0      # screen: y grows down, the front is at Y1
        cx, cy = 210.0, 110.0                          # the cut-out corner (back right)
        out = [(X0, Y1), (X1, Y1), (X1, cy), (cx, cy), (cx, Y0), (X0, Y0)]
        t = 14.0
        inn = [(X0 + t, Y1 - t), (X1 - t, Y1 - t), (X1 - t, cy + t), (cx - t, cy + t), (cx - t, Y0 + t), (X0 + t, Y0 + t)]
        poly(out, wallc)
        poly(inn, inside)
        p.setPen(QPen(QColor(120, 70, 50), 0.9))      # flat joints: the long walls run through
        for (a, b) in (((X0, Y1 - t), (X0 + t, Y1 - t)), ((X1, Y1 - t), (X1 - t, Y1 - t)),
                       ((X0, Y0 + t), (X0 + t, Y0 + t)), ((cx, Y0 + t), (cx - t, Y0 + t)),
                       ((X1, cy + t), (X1 - t, cy + t)), ((cx - t, cy), (cx - t, cy + t))):
            p.drawLine(QPointF(*a), QPointF(*b))
        box(130, Y0 + t, 7, Y1 - Y0 - 2 * t, QColor(225, 170, 120))   # an inside wall across
        p.setPen(QColor(90, 90, 90))
        p.drawText(QRectF(X0, Y1 + 2, X1 - X0, 14), Qt.AlignCenter, "front")
        dim(X0, Y1 + 22, X1, Y1 + 22, "A", (X0 + X1) / 2, Y1 + 34)
        dim(X0 - 18, Y0, X0 - 18, Y1, "B", X0 - 28, (Y0 + Y1) / 2)
        dim(X1 - t, 175, X1, 175, "C", X1 - 7, 163)
        dim(cx, Y0 - 12, X1, Y0 - 12, "D", (cx + X1) / 2, Y0 - 24)
        dim(X1 + 14, Y0, X1 + 14, cy, "E", X1 + 26, (Y0 + cy) / 2)
        dim(X0, 150, 130, 150, "", 0, 0)
        p.setPen(red)
        p.drawText(QRectF(70, 136, 40, 14), Qt.AlignCenter, "across")
        dim(130, 200, 137, 200, "T", 133.5, 188)

        # ---- slabs: two storeys stacked, end on
        p.setPen(QColor(60, 60, 60))
        p.setFont(f)
        p.drawText(QRectF(10, 282, 170, 18), Qt.AlignLeft, "Slabs, end on")
        bx, wt = 40.0, 22.0
        box(bx - 14, 520, 120, 12, QColor(150, 150, 145))   # base plate
        box(bx, 500, 100, 20, slab)                         # ground slab
        box(bx, 400, wt, 100, wallc)                        # ground wall
        lip_x = bx + wt + 4
        poly([(bx, 380), (bx + 100, 380), (bx + 100, 400), (lip_x, 400), (lip_x, 412), (bx + 100, 412),
              (bx + 100, 400), (bx, 400)], slab)
        box(lip_x, 400, 74, 12, QColor(160, 140, 110))      # the lip under the first floor slab
        box(bx, 380, 100, 20, slab)                         # first floor slab
        box(bx, 310, wt, 70, wallc)                         # first floor wall
        box(bx - 10, 298, 110, 12, QColor(120, 120, 125))   # top plate
        dim(bx + 110, 500, bx + 110, 400, "F", bx + 122, 450)
        dim(bx + 110, 380, bx + 110, 400, "H", bx + 122, 390)
        dim(bx + 60, 400, bx + 60, 412, "K", bx + 70, 422)
        dim(bx + wt, 418, lip_x, 418, "L", bx + wt - 6, 428)
        dim(bx - 14, 545, bx, 545, "Q", bx - 7, 556)
        dim(bx - 22, 520, bx - 22, 532, "P", bx - 32, 526)
        dim(bx - 10, 292, bx, 292, "S", bx - 18, 284)
        dim(bx + 110, 298, bx + 110, 310, "R", bx + 122, 304)
        dim(10, 520, 10, 310, "G", 20, 330)

        # ---- drop-in floor on its ledge
        p.setPen(QColor(60, 60, 60))
        p.drawText(QRectF(190, 282, 170, 18), Qt.AlignLeft, "Drop-in floor, end on")
        wx = 210.0
        box(wx, 310, wt, 210, wallc)                        # the wall, two storeys
        p.setPen(QPen(QColor(120, 70, 50), 1.0, Qt.DashLine))
        p.drawLine(QPointF(wx, 420), QPointF(wx + wt, 420))  # where the walls are split
        box(wx + wt, 420, 18, 18, QColor(110, 85, 60))      # ledge
        box(wx + wt + 6, 402, 110, 18, floor_c)             # floor panel, on the ledge
        dim(wx + wt, 450, wx + wt + 18, 450, "M", wx + wt + 9, 462)
        dim(wx + wt + 26, 420, wx + wt + 26, 438, "N", wx + wt + 38, 430)
        dim(wx + wt, 394, wx + wt + 6, 394, "J", wx + wt + 3, 384)

        f2 = QFont()
        f2.setPointSizeF(8.5)
        p.setFont(f2)
        p.setPen(QColor(60, 60, 60))
        notes = ["A  overall length", "B  overall width", "C  wall thickness", "D, E  cut-out (L, T, U)",
                 "F  a floor's height", "G  total height (divided)", "H  floor thickness",
                 "J  floor fit", "K  locating lip depth", "L  lip fit", "M  ledge width", "N  ledge height",
                 "P  base plate thickness", "Q  base plate stands out", "R  top plate thickness",
                 "S  top plate overhang", "T  inside wall thickness", "U  longest wall piece",
                 "V  gap between pieces"]
        for i, t_ in enumerate(notes):
            p.drawText(QRectF(10 if i < 10 else 185, 570 + (i % 10) * 9.0, 175, 10),
                       Qt.AlignLeft | Qt.AlignVCenter, t_)
        p.end()


class PlanPreview(QWidget):
    """The plan of one floor from above, and the storeys from the side."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(340, 300)
        self.pieces = []
        self.notes = {}
        self.msg = ""
        self.caption = ""
        self.storey = 0
        self.outline = None

    def show_plan(self, v, storey=0, outline=None):
        self.storey = storey
        try:
            p = plan_params(v)
            ol = outline if outline else make_outline(p)
            self.pieces, self.notes = build_plan(p, ol)
            self.outline = p['_outline']
            self.inner = p['_inner']
            nw = sum(1 for pc in self.pieces if pc.kind == 'wall')
            self.caption = "%d pieces - %d walls a floor, inside %.1f m² a floor" % (
                len(self.pieces), self.notes['walls'], self.notes['inner_area'])
            self.msg = ""
        except Exception as e:
            self.pieces, self.msg = [], str(e)
        self.update()

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen, QFont
        from PySide6.QtCore import QPointF, QRectF, Qt
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(246, 246, 242))
        if not self.pieces:
            p.setPen(QColor(150, 60, 0))
            p.drawText(QRectF(10, 10, self.width() - 20, self.height() - 20), Qt.AlignCenter | Qt.TextWordWrap,
                       self.msg or "No preview")
            p.end()
            return
        h_cap = 18
        W, H = self.width(), self.height()
        f = QFont()
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(50, 50, 50))
        p.drawText(8, 2, W - 16, h_cap, Qt.AlignLeft | Qt.AlignVCenter, self.caption)
        # ---- the plan (left two thirds)
        pw = W * 0.68
        xs = [q[0] for q in self.outline]
        ys = [q[1] for q in self.outline]
        for pc in self.pieces:
            if pc.kind in ('base', 'top'):
                xs += [q[0] for q in pc.poly]
                ys += [q[1] for q in pc.poly]
        bw, bh = (max(xs) - min(xs)) or 1.0, (max(ys) - min(ys)) or 1.0
        sc = min((pw - 24) / bw, (H - h_cap - 34) / bh)
        ox = 12 + (pw - 24 - bw * sc) / 2 - min(xs) * sc
        oy = h_cap + 10 + (H - h_cap - 34 + bh * sc) / 2 + min(ys) * sc

        def P(q):
            return QPointF(ox + q[0] * sc, oy - q[1] * sc)

        def draw(poly_, rgb, width=0.8, alpha=255):
            col = QColor(*rgb)
            col.setAlpha(alpha)
            p.setBrush(col)
            p.setPen(QPen(QColor(*rgb).darker(170), width))
            p.drawPolygon(QPolygonF([P(q) for q in poly_]))

        st = self.storey
        for pc in self.pieces:
            if pc.kind == 'base':
                draw(pc.poly, COLOURS['base'])
        draw(self.inner, (240, 232, 215))
        shown = [pc for pc in self.pieces if pc.storey == st or (pc.kind == 'wall' and pc.name.startswith("Walls"))]
        for pc in shown:
            if pc.kind in ('slab', 'floor'):
                draw(pc.poly, COLOURS[pc.kind], alpha=110)
        k = 0
        for pc in shown:
            if pc.kind == 'wall':
                draw(pc.poly, COLOURS['wall'] if k % 2 == 0 else COLOURS['wall2'])
                k += 1
            elif pc.kind in ('part', 'ledge'):
                draw(pc.poly, COLOURS[pc.kind])
        p.setPen(QColor(110, 110, 110))
        p.setFont(QFont())
        p.drawText(QRectF(12, H - 20, pw - 24, 16), Qt.AlignCenter, "front - %s" % (
            "walls (one piece, full height)" if any(pc.name.startswith("Walls") for pc in self.pieces)
            else storey_name(st)))
        # ---- the storeys from the side (right third): a section through the front wall
        x0 = pw + 8
        sw = W - x0 - 10
        zs = self.notes['zs']
        zlo = min(min(pc.z0 - (pc.lip_h or 0) for pc in self.pieces), 0.0)
        zhi = max(pc.z1 for pc in self.pieces)
        vs = (H - h_cap - 40) / ((zhi - zlo) or 1.0)
        zb = H - 26

        def Z(z):
            return zb - (z - zlo) * vs
        wall_w = sw * 0.22
        span = sw * 0.9
        for pc in self.pieces:
            if pc.kind in ('slab', 'base', 'top', 'floor'):
                x_a = x0 + (wall_w + 4 if pc.kind == 'floor' else (-6 if pc.kind in ('base', 'top') else 0))
                col = QColor(*COLOURS[pc.kind])
                p.setPen(QPen(col.darker(160), 0.8))
                p.setBrush(col)
                p.drawRect(QRectF(x_a, Z(pc.z1), x0 + span - x_a, Z(pc.z0) - Z(pc.z1)))
                if pc.lip and pc.lip_h > 0:
                    col = QColor(*COLOURS['lip'])
                    p.setBrush(col)
                    p.drawRect(QRectF(x0 + wall_w + 3, Z(pc.z0), span - wall_w - 3, Z(pc.z0 - pc.lip_h) - Z(pc.z0)))
        drawn = set()
        for pc in self.pieces:
            if pc.kind == 'wall' and (pc.storey, pc.z0) not in drawn:
                drawn.add((pc.storey, pc.z0))
                col = QColor(*COLOURS['wall'])
                p.setPen(QPen(col.darker(160), 0.8))
                p.setBrush(col)
                p.drawRect(QRectF(x0, Z(pc.z1), wall_w, Z(pc.z0) - Z(pc.z1)))
            elif pc.kind == 'ledge' and ('l', pc.storey) not in drawn:
                drawn.add(('l', pc.storey))
                col = QColor(*COLOURS['ledge'])
                p.setPen(QPen(col.darker(160), 0.8))
                p.setBrush(col)
                p.drawRect(QRectF(x0 + wall_w, Z(pc.z1), wall_w * 0.6, Z(pc.z0) - Z(pc.z1)))
        p.setPen(QColor(90, 90, 90))
        f3 = QFont()
        f3.setPointSizeF(7.5)
        p.setFont(f3)
        for kk in range(len(zs) - 1):
            p.drawText(QRectF(x0 + wall_w + 6, Z(zs[kk + 1]) + 2, span, 12), Qt.AlignLeft,
                       "%s  %.0f" % (storey_name(kk), zs[kk + 1] - zs[kk]))
        p.drawText(QRectF(x0, H - 20, sw, 16), Qt.AlignCenter, "side - %.0f mm high" % zs[-1])
        p.end()


UI_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_floor_plan.json")


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


class PlanDialog(QDialog):
    def __init__(self, cur, viewport, tool):
        super().__init__(viewport)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.user_presets = load_presets()
        self._busy = False
        lay = QVBoxLayout(self)
        # how to use it, and what the last build did - only shows when Info is pressed
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
        self.left = QTabWidget()
        prev_page = QWidget()
        pv = QVBoxLayout(prev_page)
        pv.setContentsMargins(0, 0, 0, 0)
        self.preview = PlanPreview()
        pv.addWidget(self.preview, 1)
        srow = QHBoxLayout()
        srow.addWidget(QLabel("Floor shown"))
        self.cb_show = QComboBox()
        srow.addWidget(self.cb_show, 1)
        pv.addLayout(srow)
        self.cb_show.currentIndexChanged.connect(self.changed)
        self.left.addTab(prev_page, "Preview")
        from PySide6.QtWidgets import QScrollArea
        key_scroll = QScrollArea()
        key_scroll.setWidgetResizable(True)
        key_scroll.setWidget(KeyDrawing())
        self.left.addTab(key_scroll, "Key (A, B, C...)")
        self.left.setTabToolTip(1, "What each lettered size is.")
        row.addWidget(self.left, 1)
        self.tabs = QTabWidget()
        row.addWidget(self.tabs, 1)
        self.sp = {}
        self.page_of = {}

        def spin_rows(form, fields):
            for key, label, lo, hi, dec, tip in fields:
                s = QDoubleSpinBox()
                s.setDecimals(dec)
                s.setRange(lo, hi)
                s.setKeyboardTracking(True)
                s.setSuffix(" mm")
                lab = QLabel(label)
                s.setToolTip(tip)
                lab.setToolTip(tip)
                form.addRow(lab, s)
                self.sp[key] = (s, lab)
                self.page_of[key] = self.tabs.count() - 1
                s.valueChanged.connect(self.changed)

        # ---- Shape
        page = QWidget()
        fs = QFormLayout(page)
        self.tabs.addTab(page, "Shape")
        self.cb_shape = QComboBox()
        for lab_, k_ in SHAPES:
            self.cb_shape.addItem(lab_, k_)
        fs.addRow("Shape", self.cb_shape)
        self.cb_shape.currentIndexChanged.connect(self.changed)
        spin_rows(fs, SHAPE_FIELDS)
        self.ed_corners = QPlainTextEdit()
        self.ed_corners.setPlaceholderText("0, 0\n6000, 0\n6000, 4000\n0, 4000")
        self.ed_corners.setFixedHeight(90)
        self.lbl_corners = QLabel("Corners")
        fs.addRow(self.lbl_corners, self.ed_corners)
        self.ed_corners.textChanged.connect(self.changed)
        n1 = QLabel("Sizes are outside the walls. Or draw any outline as a level face, select it and click "
                    "'Build on selected face'.")
        n1.setWordWrap(True)
        n1.setStyleSheet("color: gray;")
        fs.addRow(n1)

        # ---- Walls
        page = QWidget()
        fw = QFormLayout(page)
        self.tabs.addTab(page, "Walls")
        spin_rows(fw, WALL_FIELDS[:1])
        self.cb_joint = QComboBox()
        for lab_, k_ in JOINTS:
            self.cb_joint.addItem(lab_, k_)
        fw.addRow("Wall ends meet", self.cb_joint)
        self.cb_joint.currentIndexChanged.connect(self.changed)
        spin_rows(fw, WALL_FIELDS[1:3])
        hdr = QLabel("<b>Inside walls</b>")
        fw.addRow(hdr)
        self.ed_cx = QLineEdit()
        self.ed_cx.setPlaceholderText("e.g. 3000, 6500   (empty = none)")
        self.ed_cx.setToolTip("Inside walls across the building (front to back), this far along from its left "
                              "end - the middle of the wall, real-world mm, commas between.")
        fw.addRow("Across, at (along A)", self.ed_cx)
        self.ed_cy = QLineEdit()
        self.ed_cy.setPlaceholderText("e.g. 2500   (empty = none)")
        self.ed_cy.setToolTip("Inside walls along the building (left to right), this far back from the front.")
        fw.addRow("Along, at (back from front)", self.ed_cy)
        for e_ in (self.ed_cx, self.ed_cy):
            e_.textChanged.connect(self.changed)
        spin_rows(fw, WALL_FIELDS[3:])
        self.lbl_walls = QLabel()
        self.lbl_walls.setWordWrap(True)
        self.lbl_walls.setStyleSheet("color: gray;")
        fw.addRow(self.lbl_walls)

        # ---- Floors
        page = QWidget()
        ff = QFormLayout(page)
        self.tabs.addTab(page, "Floors")
        self.cb_hmode = QComboBox()
        for lab_, k_ in HEIGHT_MODES:
            self.cb_hmode.addItem(lab_, k_)
        ff.addRow("Heights", self.cb_hmode)
        self.cb_hmode.currentIndexChanged.connect(self.changed)
        self.ed_heights = QLineEdit()
        self.ed_heights.setPlaceholderText("e.g. 2700, 2600   (ground floor first)")
        self.ed_heights.setToolTip("The height of each floor, ground floor first, floor to floor - as many as "
                                   "you like, commas between.")
        self.lbl_heights = QLabel("F   Floor heights")
        self.lbl_heights.setToolTip(self.ed_heights.toolTip())
        ff.addRow(self.lbl_heights, self.ed_heights)
        self.ed_heights.textChanged.connect(self.changed)
        self.sp_storeys = QSpinBox()
        self.sp_storeys.setRange(1, 50)
        ff.addRow("Number of floors", self.sp_storeys)
        self.sp_storeys.valueChanged.connect(self.changed)
        spin_rows(ff, FLOOR_FIELDS[:1])
        self.cb_fstyle = QComboBox()
        for lab_, k_ in FLOOR_STYLES:
            self.cb_fstyle.addItem(lab_, k_)
        ff.addRow("Floors", self.cb_fstyle)
        self.cb_fstyle.currentIndexChanged.connect(self.changed)
        spin_rows(ff, FLOOR_FIELDS[1:])
        self.ck_ledges = QCheckBox("Ledges under the drop-in floors")
        ff.addRow(self.ck_ledges)
        self.ck_one = QCheckBox("Walls in one piece, full height")
        ff.addRow(self.ck_one)
        for c_ in (self.ck_ledges, self.ck_one):
            c_.toggled.connect(self.changed)
        self.lbl_floors = QLabel()
        self.lbl_floors.setWordWrap(True)
        self.lbl_floors.setStyleSheet("color: gray;")
        ff.addRow(self.lbl_floors)

        # ---- Base & top
        page = QWidget()
        fp = QFormLayout(page)
        self.tabs.addTab(page, "Base & top")
        self.ck_base = QCheckBox("Base plate (plinth) under it all")
        fp.addRow(self.ck_base)
        spin_rows(fp, PLATE_FIELDS[:2])
        self.ck_top = QCheckBox("Top plate (flat roof / ceiling)")
        fp.addRow(self.ck_top)
        spin_rows(fp, PLATE_FIELDS[2:])
        for c_ in (self.ck_base, self.ck_top):
            c_.toggled.connect(self.changed)
        np_ = QLabel("0 = the floor thickness (or the wall thickness). With slabs and a lip (K), the top plate "
                     "gets a lip too, so it sits square.")
        np_.setWordWrap(True)
        np_.setStyleSheet("color: gray;")
        fp.addRow(np_)

        # ---- Output
        page = QWidget()
        fo = QFormLayout(page)
        self.tabs.addTab(page, "Output")
        self.cb_group = QComboBox()
        for lab_, k_ in GROUPINGS:
            self.cb_group.addItem(lab_, k_)
        fo.addRow("Pieces go", self.cb_group)
        self.cb_group.currentIndexChanged.connect(self.changed)
        no_ = QLabel("Every piece - each wall section, floor, ledge and plate - is a plain group of its own (not "
                     "a component), named for its floor and side, like 'First floor - Wall 2 (right)'. In Scale "
                     "Studio's Pieces page pick 'Every group with faces (smallest pieces)' and tick 'Lay each "
                     "piece flat' to print them.")
        no_.setWordWrap(True)
        no_.setStyleSheet("color: gray;")
        fo.addRow(no_)

        # ---- presets and buttons
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
        self.b_add = QPushButton("Build floor plan")
        self.b_add.setDefault(True)
        self.b_face = QPushButton("Build on selected face")
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
        brow.addWidget(self.b_add)
        brow.addWidget(self.b_face)
        brow.addStretch(1)
        self.b_info = QPushButton("Info")
        self.b_info.setCheckable(True)
        self.b_info.setChecked(False)
        self.b_info.setToolTip("Shows how to use it, and what the last floor plan you built came out like.")
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
        self.b_add.clicked.connect(lambda: self.tool.build(self, on_face=False))
        self.b_face.clicked.connect(lambda: self.tool.build(self, on_face=True))
        b_close.clicked.connect(self.close)
        self.refresh_presets()
        self.set_values(cur)
        # click on a piece of ours in the model and the settings that made it light up here
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

    # ---- values ----
    def values(self):
        v = dict(shape=self.cb_shape.currentData() or 'rect', joint=self.cb_joint.currentData() or 'long',
                 height_mode=self.cb_hmode.currentData() or 'each',
                 floor_style=self.cb_fstyle.currentData() or 'stacked',
                 grouping=self.cb_group.currentData() or 'storeys',
                 storeys=int(self.sp_storeys.value()),
                 corners_text=self.ed_corners.toPlainText().strip(),
                 storey_heights=self.ed_heights.text().strip(),
                 cross_x=self.ed_cx.text().strip(), cross_y=self.ed_cy.text().strip(),
                 ledges=self.ck_ledges.isChecked(), one_piece=self.ck_one.isChecked(),
                 base=self.ck_base.isChecked(), top=self.ck_top.isChecked())
        for key, (s, _) in self.sp.items():
            v[key] = float(s.value())
        return v

    def set_values(self, d):
        self._busy = True
        try:
            for cb, key in ((self.cb_shape, 'shape'), (self.cb_joint, 'joint'), (self.cb_hmode, 'height_mode'),
                            (self.cb_fstyle, 'floor_style'), (self.cb_group, 'grouping')):
                i_ = cb.findData(d.get(key, DEFAULTS[key]))
                cb.setCurrentIndex(max(0, i_))
            self.sp_storeys.setValue(int(d.get('storeys', DEFAULTS['storeys']) or 1))
            self.ed_corners.setPlainText(str(d.get('corners_text', '') or ''))
            for ed, key in ((self.ed_heights, 'storey_heights'), (self.ed_cx, 'cross_x'), (self.ed_cy, 'cross_y')):
                val = d.get(key, DEFAULTS[key])
                if isinstance(val, (list, tuple)):
                    val = ", ".join("%g" % x for x in val)
                ed.setText(str(val or ''))
            for c_, key in ((self.ck_ledges, 'ledges'), (self.ck_one, 'one_piece'), (self.ck_base, 'base'),
                            (self.ck_top, 'top')):
                c_.setChecked(bool(d.get(key, DEFAULTS[key])))
            for key, (s, _) in self.sp.items():
                s.setValue(float(d.get(key, DEFAULTS[key]) or 0.0))
        finally:
            self._busy = False
        self.changed()

    def changed(self, *_):
        if self._busy:
            return
        v = self.values()
        try:
            for k_, val in _auto_sizes(v).items():
                if k_ in self.sp:
                    self.sp[k_][0].setSpecialValueText("auto  %.0f mm" % val if val > 0 else "auto")
        except Exception:
            pass
        _ui_settings_save(last_values={k: v[k] for k in DEFAULTS if k in v})
        shape, hm, fsy = v['shape'], v['height_mode'], v['floor_style']
        custom = shape == 'custom'
        for k_ in ('length', 'width'):
            self.sp[k_][0].setEnabled(not custom)
        for k_ in ('cut_l', 'cut_w'):
            self.sp[k_][0].setEnabled(shape in ('L', 'T', 'U'))
        self.ed_corners.setVisible(custom)
        self.lbl_corners.setVisible(custom)
        self.ed_heights.setEnabled(hm == 'each')
        self.sp_storeys.setEnabled(hm == 'divide')
        self.sp['total_h'][0].setEnabled(hm == 'divide')
        self.sp['floor_t'][0].setEnabled(fsy != 'none')
        self.sp['fit'][0].setEnabled(fsy == 'dropin')
        self.sp['lip_h'][0].setEnabled(fsy == 'stacked')
        self.sp['lip_fit'][0].setEnabled(fsy == 'stacked' and v['lip_h'] > 0)
        self.ck_ledges.setEnabled(fsy == 'dropin')
        self.sp['ledge_w'][0].setEnabled(fsy == 'dropin' and v['ledges'])
        self.sp['ledge_h'][0].setEnabled(fsy == 'dropin' and v['ledges'])
        self.ck_one.setEnabled(fsy != 'stacked')
        self.sp['part_t'][0].setEnabled(bool(v['cross_x'] or v['cross_y']))
        for k_ in ('base_t', 'base_over'):
            self.sp[k_][0].setEnabled(v['base'])
        for k_ in ('top_t', 'top_over'):
            self.sp[k_][0].setEnabled(v['top'])
        # the floors in the 'Floor shown' list
        try:
            n = len(plan_params(v)['_heights'])
        except Exception:
            n = 1
        if self.cb_show.count() != n:
            cur = max(0, self.cb_show.currentIndex())
            self.cb_show.blockSignals(True)
            self.cb_show.clear()
            for k in range(n):
                self.cb_show.addItem(storey_name(k))
            self.cb_show.setCurrentIndex(min(cur, n - 1))
            self.cb_show.blockSignals(False)
        self.preview.show_plan(v, max(0, self.cb_show.currentIndex()))
        # notes under the pages
        try:
            p = plan_params(v)
            hs = p['_heights']
            txt = "%d floor%s: %s mm, %.0f mm high in all." % (
                len(hs), "s" if len(hs) > 1 else "", ", ".join("%.0f" % h for h in hs), sum(hs))
            if fsy == 'stacked':
                txt += " Each storey stands on its %.0f mm slab (part of its height)." % p['floor_t']
            elif fsy == 'dropin':
                txt += " Floor panels drop in %.0f mm clear of the walls." % p['fit']
                if v['ledges'] and p['fit'] >= p['ledge_w']:
                    txt += " The fit is as big as the ledge - the floors would fall through."
            self.lbl_floors.setText(txt)
            self.lbl_floors.setStyleSheet("color: gray;")
        except ValueError as e:
            self.lbl_floors.setText(str(e))
            self.lbl_floors.setStyleSheet("color: #b35900;")
        nt = self.preview.notes if self.preview.pieces else {}
        if nt:
            self.lbl_walls.setText("%d wall sections a floor, %.2f m round the outside. Inside each floor: "
                                   "%.1f m²." % (nt['walls'], nt['wall_len'], nt['inner_area']))
        else:
            self.lbl_walls.setText(self.preview.msg)

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
            d = dict(DEFAULTS)                      # a built-in preset starts from a clean slate
            d['grouping'] = self.values().get('grouping', 'storeys')
            d.update(BUILTIN_PRESETS[name])
        elif name and name in self.user_presets:
            d = dict(self.user_presets[name])
            cur = self.values()
            for k in cur:
                d.setdefault(k, cur[k])
        if d is None:
            return
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


class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
PRINT_NOTE = ("Every piece is its own group: in Scale Studio's Pieces page pick 'Every group with faces "
              "(smallest pieces)' and tick 'Lay each piece flat'.")


class FloorPlanTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+Shift+F"
    description = "The shell of a building from its floor plan: walls set in from the outline, flat or " \
                  "mitred corners, split at each floor, with floor slabs or drop-in floors, inside walls " \
                  "and base and top plates - every piece its own group, ready to print."

    _dialog = None

    def on_activate(self, viewport):
        dlg = FloorPlanTool._dialog
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
            cur.update({k: last[k] for k in DEFAULTS if k in last})
        else:
            cur.update(BUILTIN_PRESETS["Two-storey house 7.5 x 6 m"])    # something to look at first time
        dlg = PlanDialog(cur, viewport, self)
        FloorPlanTool._dialog = dlg

        def closed(*_):
            FloorPlanTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass

    def build(self, dlg, on_face=False):
        v = dlg.values()
        _ui_settings_save(last_values={k: v[k] for k in DEFAULTS if k in v})
        scene = getattr(dlg.viewport, 'scene', None)
        if scene is None:
            return
        try:
            p = plan_params(v)
            z_base = 0.0
            if on_face:
                outline, z_base = selected_level_outline(scene)
                if outline is None:
                    QMessageBox.information(dlg, PLUGIN_NAME, "Select a level face (or a group with a floor or "
                                            "base in it) first - the walls go up inside its edge.")
                    return
            else:
                outline = make_outline(p)
            pieces, notes = build_plan(p, outline)
        except ValueError as e:
            QMessageBox.warning(dlg, PLUGIN_NAME, str(e))
            return
        n = self.add_to_scene(dlg.viewport, pieces, v.get('grouping', 'storeys'), z_base)
        if n is None:
            return
        hs = p['_heights']
        nw = sum(1 for pc in pieces if pc.kind == 'wall')
        msg = "Added %d pieces: %d wall sections (%d a floor%s)" % (
            len(pieces), nw, notes['walls'], ", some split to fit the print bed" if p['split_len'] > 0 and
            nw > notes['walls'] * (1 if p.get('one_piece') and p['floor_style'] != 'stacked' else len(hs)) else "")
        for kind, word in (('slab', "floor slabs"), ('floor', "drop-in floor panels"), ('ledge', "ledges"),
                           ('part', "inside walls"), ('base', "base plate"), ('top', "top plate")):
            c = sum(1 for pc in pieces if pc.kind == kind)
            if c:
                msg += ", %d %s" % (c, word) if kind not in ('base', 'top') else ", a %s" % word
        msg += ". %d floor%s, %.0f mm high; inside each floor %.1f m²." % (
            len(hs), "s" if len(hs) > 1 else "", notes['H'], notes['inner_area'])
        if on_face:
            msg += " Built inside the edge of the face you picked."
        else:
            msg += " Built at the origin - move it where you want it."
        msg += "\n" + PRINT_NOTE
        dlg.show_report(msg)

    def add_to_scene(self, viewport, pieces, grouping, z_base=0.0):
        """Each piece a plain group of its own; held in a group per floor, one group, or loose."""
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
                return None

        def to_world(q):
            return (q[0] * SCALE, q[1] * SCALE, (q[2] + z_base) * SCALE)

        def mutate(scene):
            from core.mesh import Mesh
            from core.group import Group
            by_storey = {}
            order = []
            for pc in pieces:
                so = pc.solid().mapped(to_world)
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
                g = make_group(Group, mesh, pc.name)
                g.component = False
                if pc.kind in ('base', 'top'):
                    key = (2, 0)                    # the plates sit in 'Floor plan' itself
                elif pc.kind == 'wall' and pc.name.startswith("Walls"):
                    key = (0, -1)                   # full-height walls: a group of their own
                else:
                    key = (1, pc.storey)
                if key not in by_storey:
                    by_storey[key] = []
                    order.append(key)
                by_storey[key].append(g)
            if stats['faces'] == 0:
                raise RuntimeError("No faces could be created (%s)." % stats['err'])
            tops = []
            if grouping == 'loose':
                tops = [g for k in order for g in by_storey[k]]
            elif grouping == 'one':
                h = holder(Group, "Floor plan", [g for k in sorted(order) for g in by_storey[k]])
                tops = [h] if h is not None else [g for k in order for g in by_storey[k]]
            else:
                kids = []
                for k in sorted(order):
                    gs = by_storey[k]
                    if k[0] == 2:
                        kids += gs
                        continue
                    nm = "%s (%d pieces)" % ("Walls" if k[0] == 0 else storey_name(k[1]), len(gs))
                    h = holder(Group, nm, gs)
                    if h is None:
                        kids += gs
                    else:
                        kids.append(h)
                h = holder(Group, "Floor plan", kids)
                tops = [h] if h is not None else kids
            for g in tops:
                _ed3d_organise(scene, g)
                if hasattr(scene, 'add_group'):
                    scene.add_group(g)
                else:
                    scene.groups.append(g)
        try:
            viewport.history.execute(SnapshotImport(mutate))
        except Exception as e:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not add the floor plan:\n%s" % e)
            return None
        try:
            viewport.notify_scene_changed()
        except Exception:
            pass
        return stats['faces']


def run(viewport=None):
    FloorPlanTool().on_activate(viewport)
