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
  Gables        Gable ends on top of the end walls (or the front and back, or the walls you
                pick), from the roof pitch or the ridge height - each its own piece.
  Roof          A pitched roof on top: gable (ridge along or across), hip (a pyramid on a square),
                mono-pitch / lean-to, saltbox, a flat roof with a fall, or gables on the walls you
                pick. Eaves and verge overhangs, and the gable ends and raised walls under it are
                filled in to meet it. Each slope is its own piece, ready for Subframe to frame and
                Roof Tiles to cover. (Shapes without inside corners for now - L, T and U to come.)

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
VERSION = "2.13"  # 2.13: hiding the roof also hides the tiles 3D Roof Tiles put on it


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
                ("No floors - walls only", 'none'),
                ("Each storey set on the Storeys page (floors and ceilings)", 'storeys')]
GABLE_ON = [("The two ends (left and right) - ridge along the length", 'ends'),
            ("Front and back - ridge across the building", 'sides'),
            ("The walls I pick (by number)", 'pick')]
TOP_MODES = [("On top of the walls (a flat roof)", 'over'),
             ("Inside the walls, sitting on the inside walls (a ceiling)", 'inside')]
ROOF_TYPES = [("Gable - ridge along the length", 'gable_len'),
              ("Gable - ridge across the building", 'gable_across'),
              ("Hip - slopes on every side (a pyramid on a square)", 'hip'),
              ("Mono-pitch / lean-to - one slope", 'mono'),
              ("Saltbox - gable with a different back slope", 'saltbox'),
              ("Flat roof with a fall", 'flat'),
              ("Gables on the walls I pick, slopes on the rest", 'pick')]
ROOF_LOW = [("the front", 'front'), ("the back", 'back'), ("the left", 'left'), ("the right", 'right')]
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
    cross_x='', cross_y='', part_t=0.0, part_room=0.0, part_join=False,
    base=False, base_t=0.0, base_over=0.0, top=False, top_t=0.0, top_over=0.0, top_mode='over', top_room=0.0,
    top_join=False,
    gables=False, gable_on='ends', gable_walls='', gable_pitch=45.0, ridge_h=0.0, gable_join=False,
    roof=False, roof_type='gable_len', roof_low='front', roof_gables='', roof_fill=True,
    roof_pitch=40.0, roof_pitch2=0.0, roof_fall=3.0, eave_over=0.0, verge_over=0.0, roof_t=0.0,
    storey_rows=[], tab_room=0.0, ceil_t=0.0,
    grouping='storeys')
SIZE_KEYS = ('length', 'width', 'cut_l', 'cut_w', 'wall_t', 'split_len', 'gap', 'total_h', 'floor_t', 'fit',
             'lip_h', 'lip_fit', 'ledge_w', 'ledge_h', 'part_t', 'part_room', 'base_t', 'base_over', 'top_t', 'top_over',
             'gable_pitch', 'ridge_h', 'top_room', 'roof_pitch', 'roof_pitch2', 'roof_fall', 'eave_over',
             'verge_over', 'roof_t', 'tab_room', 'ceil_t')

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
    "Cottage with gable ends (45°)": dict(
        shape='rect', length=7000.0, width=5000.0, wall_t=300.0, joint='swap', height_mode='each',
        storey_heights='2600, 2400', storeys=2, floor_style='stacked', floor_t=200.0, lip_h=150.0, lip_fit=20.0,
        cross_x='3500', part_t=150.0, base=True, base_t=150.0, base_over=100.0,
        gables=True, gable_on='ends', gable_pitch=45.0, ridge_h=0.0),
    "Cottage with a gable roof": dict(
        shape='rect', length=7000.0, width=5000.0, wall_t=300.0, joint='swap', height_mode='each',
        storey_heights='2600, 2400', storeys=2, floor_style='stacked', floor_t=200.0, lip_h=150.0, lip_fit=20.0,
        cross_x='3500', part_t=150.0, base=True, base_t=150.0, base_over=100.0,
        roof=True, roof_type='gable_len', roof_pitch=40.0, eave_over=300.0, verge_over=200.0, roof_t=150.0,
        roof_fill=True),
    "House with a hipped roof": dict(
        shape='rect', length=8000.0, width=6000.0, wall_t=300.0, joint='swap', height_mode='each',
        storey_heights='2700, 2600', storeys=2, floor_style='stacked', floor_t=200.0, lip_h=150.0, lip_fit=20.0,
        cross_x='4000', part_t=150.0, base=True, base_t=150.0, base_over=100.0,
        roof=True, roof_type='hip', roof_pitch=35.0, eave_over=400.0, roof_t=150.0, roof_fill=True),
    "Cottage - storeys with floors on tabs (for Subframe)": dict(
        shape='rect', length=7000.0, width=5000.0, wall_t=300.0, joint='pinwheel', height_mode='each',
        storey_heights='2600, 2400', storeys=2, floor_style='storeys', floor_t=200.0, fit=20.0,
        cross_x='3500', part_t=150.0, part_room=160.0, base=True, base_t=150.0, base_over=100.0,
        storey_rows=[dict(floor=True, ceiling=False), dict(floor=True, ceiling=True)],
        roof=True, roof_type='gable_len', roof_pitch=40.0, eave_over=300.0, verge_over=200.0, roof_t=150.0,
        roof_fill=True),
    "Lean-to shed (mono-pitch)": dict(
        shape='rect', length=4000.0, width=2500.0, wall_t=200.0, joint='long', height_mode='each',
        storey_heights='2200', storeys=1, floor_style='none', base=True, base_t=150.0, base_over=50.0,
        roof=True, roof_type='mono', roof_low='front', roof_pitch=15.0, eave_over=250.0, verge_over=150.0,
        roof_t=100.0, roof_fill=True),
}

COLOURS = {'wall': (196, 120, 90), 'wall2': (176, 104, 78), 'slab': (205, 185, 150), 'floor': (215, 195, 160),
           'ledge': (110, 85, 60), 'part': (225, 170, 120), 'base': (150, 150, 145), 'top': (120, 120, 125),
           'lip': (160, 140, 110), 'gable': (186, 96, 70), 'roof': (110, 95, 90)}
STOREY_NAMES = ["Ground floor", "First floor", "Second floor", "Third floor", "Fourth floor", "Fifth floor"]


def storey_rows(rows, n):
    """What each storey has (Storeys page): [{'floor', 'ceiling'}] - one for each storey."""
    out = []
    rows = rows if isinstance(rows, (list, tuple)) else []
    for k in range(n):
        r = rows[k] if k < len(rows) and isinstance(rows[k], dict) else {}
        out.append(dict(floor=bool(r.get('floor', True)), ceiling=bool(r.get('ceiling', k == n - 1 and n > 0))))
    return out


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
    p['_gable_walls'] = []
    if p.get('gables'):
        if p['ridge_h'] <= 0 and not (0 < p['gable_pitch'] < 89):
            raise ValueError("Set the roof pitch (X, on the Gables page) - or the ridge height (Y).")
        if p.get('gable_on') == 'pick':
            nums = parse_list(p.get('gable_walls', ''), "Gable walls")
            if not nums:
                raise ValueError("Type the numbers of the walls to put gables on (Gables page), like 2, 4.")
            p['_gable_walls'] = [int(round(x)) - 1 for x in nums]
    p['roof_t'] = p['roof_t'] if p['roof_t'] > 0 else 0.5 * t
    p['tab_room'] = p['tab_room'] if p['tab_room'] > 0 else (p['floor_t'] or 0.5 * t)
    p['ceil_t'] = p['ceil_t'] if p['ceil_t'] > 0 else (p['floor_t'] or 0.5 * t)
    p['_rows'] = storey_rows(p.get('storey_rows'), len(p['_heights']))
    if p['floor_style'] == 'storeys' and p['floor_t'] <= 0:
        raise ValueError("Set the floor thickness (H, on the Floors page).")
    p['_roof_gables'] = []
    if p.get('roof'):
        if p.get('roof_type') == 'flat':
            if not (0 < p['roof_fall'] < 30):
                raise ValueError("Set the fall of the flat roof (RC, on the Roof page) - a few degrees, like 3.")
        elif not (0 < p['roof_pitch'] < 80):
            raise ValueError("Set the roof pitch (RA, on the Roof page) - between 1 and 80 degrees.")
        if p['roof_pitch2'] and not (0 < p['roof_pitch2'] < 80):
            raise ValueError("The second pitch (RB, on the Roof page) needs to be between 1 and 80 degrees "
                             "(or 0 for the same as the roof pitch).")
        if p.get('roof_type') == 'pick':
            nums = parse_list(p.get('roof_gables', ''), "Gable walls")
            p['_roof_gables'] = [int(round(x)) - 1 for x in nums]
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


def _inset_ok(inner, outer, d):
    """True if every corner of inner is at least d in from every side of outer (an inset that
    hasn't turned itself inside out)."""
    def seg_dist(q, a, b):
        ax, ay = b[0] - a[0], b[1] - a[1]
        L = ax * ax + ay * ay
        t = 0.0 if L <= 0 else max(0.0, min(1.0, ((q[0] - a[0]) * ax + (q[1] - a[1]) * ay) / L))
        return math.hypot(q[0] - a[0] - ax * t, q[1] - a[1] - ay * t)
    n = len(outer)
    return all(seg_dist(q, outer[i], outer[(i + 1) % n]) >= d * 0.999 for q in inner for i in range(n))


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
    room = max(0.0, p.get('part_room', 0.0))      # stops short of the outside walls (room for a frame)
    xs = [q[0] for q in p['_outline']]
    ys = [q[1] for q in p['_outline']]
    x0, y0 = min(xs), min(ys)
    out = []
    xcuts = []
    for c in p['_cross_x']:
        cx = x0 + c
        xcuts.append(cx)
        for a, b in spans_on_line(inner, 0, cx):
            a, b = a + gap + room, b - gap - room
            if b - a > pt:
                out.append(([(cx - pt / 2, a), (cx + pt / 2, a), (cx + pt / 2, b), (cx - pt / 2, b)], 'across'))
    for c in p['_cross_y']:
        cy = y0 + c
        for a, b in spans_on_line(inner, 1, cy):
            a, b = a + room, b - room
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


def join_rects(rects):
    """The inside walls that touch or cross joined into one piece each: [(outline, [holes], kind)].
    Walls that meet nothing stay as they are. A ring of walls (a closed room) keeps its hole."""
    R = [[(round(q[0], 4), round(q[1], 4)) for q in r] for r, _k in rects]
    if not R:
        return []
    xs = sorted(set(q[0] for r in R for q in r))
    ys = sorted(set(q[1] for r in R for q in r))
    boxes = [(min(q[0] for q in r), min(q[1] for q in r), max(q[0] for q in r), max(q[1] for q in r)) for r in R]
    nx_, ny_ = len(xs) - 1, len(ys) - 1

    def covered(i, j):
        if not (0 <= i < nx_ and 0 <= j < ny_):
            return False
        cx, cy = (xs[i] + xs[i + 1]) / 2.0, (ys[j] + ys[j + 1]) / 2.0
        return any(b[0] < cx < b[2] and b[1] < cy < b[3] for b in boxes)
    cov = {(i, j) for i in range(nx_) for j in range(ny_) if covered(i, j)}
    # the edges round the covered cells, counter-clockwise, without the ones between two covered cells
    nxt = {}
    for (i, j) in cov:
        a, b, c, d = (i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)
        for (p0, p1, nb) in ((a, b, (i, j - 1)), (b, c, (i + 1, j)), (c, d, (i, j + 1)), (d, a, (i - 1, j))):
            if nb not in cov:
                nxt.setdefault(p0, []).append(p1)
    loops = []
    while nxt:
        start = next(iter(nxt))
        loop = [start]
        cur = start
        while True:
            outs = nxt.get(cur)
            if not outs:
                break
            nb = outs.pop()
            if not outs:
                del nxt[cur]
            if nb == start:
                break
            loop.append(nb)
            cur = nb
        pts = [(xs[i], ys[j]) for i, j in loop]
        # drop the corners in the middle of a straight run
        changed = True
        while changed and len(pts) > 3:
            changed = False
            for k in range(len(pts)):
                a, b, c = pts[k - 1], pts[k], pts[(k + 1) % len(pts)]
                if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) < 1e-9:
                    pts.pop(k)
                    changed = True
                    break
        if len(pts) >= 3:
            loops.append(pts)
    outers = [l_ for l_ in loops if area2(l_) > 0]
    holes = [l_ for l_ in loops if area2(l_) < 0]

    def inside(q, poly):
        c = False
        for k in range(len(poly)):
            (x1, y1), (x2, y2) = poly[k - 1], poly[k]
            if (y1 > q[1]) != (y2 > q[1]) and q[0] < x1 + (q[1] - y1) * (x2 - x1) / (y2 - y1):
                c = not c
        return c
    out = []
    for o in outers:
        hs = [h for h in holes if inside(((h[0][0] + h[1][0]) / 2.0 + 1e-3 * (h[1][1] - h[0][1]),
                                          (h[0][1] + h[1][1]) / 2.0 - 1e-3 * (h[1][0] - h[0][0])), o)]
        dx = max(q[0] for q in o) - min(q[0] for q in o)
        dy = max(q[1] for q in o) - min(q[1] for q in o)
        if len(o) == 4 and not hs:
            kind = 'across' if dx < dy else 'along'
        else:
            kind = 'joined'
        out.append((o, hs, kind))
    return out


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


def prism_holes(poly, holes, z0, z1):
    """A prism with holes right through it (a ring of inside walls round a room)."""
    s = PSolid()
    s.add([(x, y, z1) for x, y in poly], holes=[[(x, y, z1) for x, y in h] for h in holes])
    s.add([(x, y, z0) for x, y in reversed(poly)], holes=[[(x, y, z0) for x, y in reversed(h)] for h in holes])
    for loop in [poly] + list(holes):
        n = len(loop)
        for i in range(n):
            (ax, ay), (bx, by) = loop[i], loop[(i + 1) % n]
            s.add([(ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1)])
    return s.fix()


def plate_with_walls(plate, z0, z1, feet, zd0):
    """A plate (z0 to z1) with walls standing down from its underside to zd0 - all one piece.
    feet: [(outline, [holes])] of the walls, each well inside the plate."""
    s = PSolid()
    s.add([(x, y, z1) for x, y in plate])
    for i in range(len(plate)):
        (ax, ay), (bx, by) = plate[i], plate[(i + 1) % len(plate)]
        s.add([(ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1)])
    s.add([(x, y, z0) for x, y in reversed(plate)], holes=[[(x, y, z0) for x, y in o] for o, _h in feet])
    for o, hs in feet:
        for h in hs:                                # the plate's underside again, inside a ring of walls
            s.add([(x, y, z0) for x, y in h])
        for loop in [o] + list(hs):
            n = len(loop)
            for i in range(n):
                (ax, ay), (bx, by) = loop[i], loop[(i + 1) % n]
                s.add([(ax, ay, zd0), (bx, by, zd0), (bx, by, z0), (ax, ay, z0)])
        s.add([(x, y, zd0) for x, y in reversed(o)], holes=[[(x, y, zd0) for x, y in reversed(h)] for h in hs])
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
def gable_solid(poly, z0, u, mid, half, tanp, zbase=None):
    """A gable: the wall's plan (poly) standing on z0, its top sloping up from each end of
    the side (mid - half, mid + half along u) to the ridge in the middle. zbase: where the
    slope starts (the top of the walls) when the gable is joined to the wall below it."""
    zb = z0 if zbase is None else zbase

    def s(q):
        return q[0] * u[0] + q[1] * u[1]

    def zt(q):
        return zb + max(0.0, half - abs(s(q) - mid)) * tanp
    pts = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        pts.append(a)
        fa, fb = s(a) - mid, s(b) - mid
        if (fa < -1e-9 and fb > 1e-9) or (fa > 1e-9 and fb < -1e-9):
            t_ = fa / (fa - fb)                     # a corner where the ridge crosses
            pts.append((a[0] + t_ * (b[0] - a[0]), a[1] + t_ * (b[1] - a[1])))

    def face(qs):
        out = []
        for q in qs:
            if not out or max(abs(q[j] - out[-1][j]) for j in range(3)) > 1e-6:
                out.append(q)
        while len(out) > 1 and max(abs(out[0][j] - out[-1][j]) for j in range(3)) <= 1e-6:
            out.pop()
        return out if len(out) >= 3 else None
    S = PSolid()
    S.add([(x, y, z0) for x, y in reversed(poly)])
    # each side one whole face (the ridge corner sits in its top edge, not down its middle), so
    # other plugins - Openings, Subframe - see the wall's front and back as one face each
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        top = [(a[0], a[1], zt(a))]
        fa, fb = s(a) - mid, s(b) - mid
        if (fa < -1e-9 and fb > 1e-9) or (fa > 1e-9 and fb < -1e-9):
            t_ = fa / (fa - fb)
            r = (a[0] + t_ * (b[0] - a[0]), a[1] + t_ * (b[1] - a[1]))
            top.append((r[0], r[1], zt(r)))
        top.append((b[0], b[1], zt(b)))
        f_ = face([(a[0], a[1], z0), (b[0], b[1], z0)] + list(reversed(top)))
        if f_:
            S.add(f_)
    for keep in (lambda q: s(q) <= mid + 1e-6, lambda q: s(q) >= mid - 1e-6):
        f_ = face([(q[0], q[1], zt(q)) for q in pts if keep(q)])
        if f_:
            S.add(f_)
    return S.fix()


# ---------------------------------------------------------------------------
# The roof: one sloping plane for each side that slopes, the roof being the lowest of them
# (on a shape without inside corners that gives the ridges and hips by itself)
# ---------------------------------------------------------------------------
def is_convex(poly):
    """True if a counter-clockwise outline has no inside corners."""
    n = len(poly)
    for i in range(n):
        a, b, c = poly[i - 1], poly[i], poly[(i + 1) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) < -1e-9:
            return False
    return True


def roof_tans(p, outline):
    """For each side of the outline: tan(pitch) if the roof slopes down to it, None for a gable end."""
    n = len(outline)
    us = [_unit(outline[i], outline[(i + 1) % n]) for i in range(n)]
    sides = [side_name(u) for u in us]
    typ = p.get('roof_type', 'gable_len')
    a = math.tan(math.radians(p['roof_pitch'])) if p['roof_pitch'] > 0 else 0.0
    b = math.tan(math.radians(p['roof_pitch2'])) if p['roof_pitch2'] > 0 else a
    low = p.get('roof_low', 'front')
    if typ == 'gable_len':
        out = [a if s in ('front', 'back') else None for s in sides]
    elif typ == 'gable_across':
        out = [a if s in ('left', 'right') else None for s in sides]
    elif typ == 'hip':
        out = [b if s in ('left', 'right') else a for s in sides]
    elif typ == 'mono':
        out = [a if s == low else None for s in sides]
    elif typ == 'flat':
        out = [math.tan(math.radians(p['roof_fall'])) if s == low else None for s in sides]
    elif typ == 'saltbox':
        out = [a if s == 'front' else b if s == 'back' else None for s in sides]
    elif typ == 'pick':
        bad = [i + 1 for i in p['_roof_gables'] if not 0 <= i < n]
        if bad:
            raise ValueError("Roof gable walls: there's no wall %s - this shape has walls 1 to %d."
                             % (", ".join(str(x) for x in bad), n))
        out = [None if i in p['_roof_gables'] else a for i in range(n)]
    else:
        raise ValueError("Unknown roof type.")
    if not any(x for x in out):
        raise ValueError("No side of the roof slopes - with these walls as gables there's nothing to hold it up. "
                         "Pick another roof type (or fewer gable walls).")
    return out


def _side_overhang(outline, ds):
    """The outline with each side moved out by its own distance (ds[i]), its sides kept parallel."""
    n = len(outline)
    lines = []
    for i in range(n):
        a, b = outline[i], outline[(i + 1) % n]
        u = _unit(a, b)
        lines.append(((a[0] + u[1] * ds[i], a[1] - u[0] * ds[i]), u))      # right of the side = outside
    out = []
    for i in range(n):
        q = meet(lines[i - 1][0], lines[i - 1][1], lines[i][0], lines[i][1])
        if q is not None:
            out.append(q)
    return clean(out)


def _clip_plane(poly, A, B):
    """The part of poly where A.q + B >= 0."""
    L2 = A[0] * A[0] + A[1] * A[1]
    if L2 < 1e-18:
        return poly if B >= -1e-9 else []
    q0 = (-B * A[0] / L2, -B * A[1] / L2)
    return clip_half(poly, q0, A)


def _envelope_regions(poly, planes):
    """planes: {key: (gx, gy, c)} for z = gx*x + gy*y + c. Returns {key: region of poly where that
    plane is the lowest} - empty regions left out."""
    out = {}
    for i, (gi0, gi1, ci) in planes.items():
        reg = list(poly)
        for j, (gj0, gj1, cj) in planes.items():
            if j == i or len(reg) < 3:
                continue
            reg = _clip_plane(reg, (gj0 - gi0, gj1 - gi1), cj - ci)
        reg = clean(reg) if len(reg) >= 3 else None
        if reg and abs(area2(reg)) > 1e-3:
            out[i] = reg
    return out


def _plane_z(pl, q):
    return pl[0] * q[0] + pl[1] * q[1] + pl[2]


def slab_on_plane(region, pl, depth):
    """A roof slope: its top on the plane over the region, its underside 'depth' below that, its edges
    upright (plumb), so slopes meeting at a ridge or hip close up with no gap."""
    S = PSolid()
    S.add([(x, y, _plane_z(pl, (x, y))) for x, y in region])
    S.add([(x, y, _plane_z(pl, (x, y)) - depth) for x, y in reversed(region)])
    n = len(region)
    for i in range(n):
        a, b = region[i], region[(i + 1) % n]
        za, zb = _plane_z(pl, a), _plane_z(pl, b)
        S.add([(a[0], a[1], za - depth), (b[0], b[1], zb - depth), (b[0], b[1], zb), (a[0], a[1], za)])
    return S.fix()


def fill_solid(poly, z0, planes):
    """A wall (or the top of one) standing on z0, its top following the underside of the roof: the
    lowest of the planes, so a gable end, a saltbox's lopsided gable or the raised back wall under a
    lean-to roof all come out right. Each side is one whole face."""
    regions = _envelope_regions(poly, planes)
    S = PSolid()
    S.add([(x, y, z0) for x, y in reversed(poly)])

    def under(q):
        return min(_plane_z(pl, q) for pl in planes.values())
    keys = list(planes)
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ts = []
        for x_ in range(len(keys)):
            for y_ in range(x_ + 1, len(keys)):
                p1, p2 = planes[keys[x_]], planes[keys[y_]]
                fa, fb = _plane_z(p1, a) - _plane_z(p2, a), _plane_z(p1, b) - _plane_z(p2, b)
                if (fa < -1e-9 and fb > 1e-9) or (fa > 1e-9 and fb < -1e-9):
                    ts.append((fa / (fa - fb), p1))
        top = [(a[0], a[1], under(a))]
        for t_, p1 in sorted(ts, key=lambda x: x[0]):
            r = (a[0] + t_ * (b[0] - a[0]), a[1] + t_ * (b[1] - a[1]))
            zr = under(r)
            # only where the roof really changes slope (a crossing hidden above another plane isn't a corner)
            if abs(zr - _plane_z(p1, r)) < 1e-6:
                top.append((r[0], r[1], zr))
        top.append((b[0], b[1], under(b)))
        pts = [(a[0], a[1], z0), (b[0], b[1], z0)] + list(reversed(top))
        f_ = []
        for q in pts:
            if not f_ or max(abs(q[j] - f_[-1][j]) for j in range(3)) > 1e-6:
                f_.append(q)
        while len(f_) > 1 and max(abs(f_[0][j] - f_[-1][j]) for j in range(3)) <= 1e-6:
            f_.pop()
        if len(f_) >= 3:
            S.add(f_)
    for k, reg in regions.items():
        S.add([(x, y, _plane_z(planes[k], (x, y))) for x, y in reg])
    return S.fix()


def build_roof(p, outline, zw, us, names):
    """The roof slopes on top of the walls (zw = the top of the walls, or of the top plate):
    ([Piece], under-roof planes {side: plane}, notes)."""
    if not is_convex(outline):
        raise ValueError("The roof can only go on a shape without inside corners for now (a rectangle, or any "
                         "shape with every corner pointing out). L, T and U roofs are coming next.")
    tans = roof_tans(p, outline)
    n = len(outline)
    ds = [p['eave_over'] if tans[i] else p['verge_over'] for i in range(n)]
    eaves = _side_overhang(outline, ds) if any(d != 0 for d in ds) else list(outline)
    if not eaves or len(eaves) < 3:
        raise ValueError("The overhangs (RD, RE) don't leave a roof.")
    tops, unders, depth = {}, {}, {}
    for i in range(n):
        if not tans[i]:
            continue
        u = us[i]
        nx, ny = -u[1], u[0]                         # into the building
        P = outline[i]
        tn = tans[i]
        dv = p['roof_t'] * math.sqrt(1.0 + tn * tn)  # the thickness, measured upright
        # the underside meets the outside of the wall at the top of the wall
        c = zw - tn * (P[0] * nx + P[1] * ny)
        unders[i] = (tn * nx, tn * ny, c)
        tops[i] = (tn * nx, tn * ny, c + dv)
        depth[i] = dv
    regions = _envelope_regions(eaves, tops)
    pieces = []
    zmax = zw
    k = 0
    for i in sorted(regions):
        reg = regions[i]
        k += 1
        nm = "Roof slope %d (%s)" % (k, names[i].split("(", 1)[1].rstrip(")") if "(" in names[i] else names[i])
        zs_ = [_plane_z(tops[i], q) for q in reg]
        pc = Piece(nm, 'roof', -2, reg, min(zs_) - depth[i], max(zs_))
        pc.custom = slab_on_plane(reg, tops[i], depth[i])
        pieces.append(pc)
        zmax = max(zmax, max(zs_))
    notes = dict(slopes=len(pieces), rise=zmax - zw, top=zmax,
                 pitches=sorted(set(round(math.degrees(math.atan(t_)), 1) for t_ in tans if t_)))
    return pieces, unders, notes


def two_row_tabs(tabs, holder, rows=2):
    """Shows a tab window's pages as buttons on `rows` rows (in holder), instead of its own single
    row of tabs. Clicking a button opens that page; the button of the page that's open is pressed."""
    from PySide6.QtWidgets import QGridLayout, QPushButton, QButtonGroup, QSizePolicy
    n = tabs.count()
    if n == 0:
        return
    grid = QGridLayout(holder)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(2)
    grid.setVerticalSpacing(2)
    per = int(math.ceil(n / float(rows)))
    group = QButtonGroup(holder)
    group.setExclusive(True)
    btns = []
    for i in range(n):
        b = QPushButton(tabs.tabText(i).replace("&&", "&").replace("&", "&&"))
        b.setCheckable(True)
        b.setToolTip(tabs.tabToolTip(i) or "")
        b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        b.setStyleSheet("QPushButton { padding: 3px 6px; } QPushButton:checked { font-weight: bold; "
                        "background: #cfe3f7; border: 1px solid #5b8fc7; }")
        grid.addWidget(b, i // per, i % per)
        group.addButton(b, i)
        btns.append(b)
    group.idClicked.connect(tabs.setCurrentIndex)

    def show(i):
        if 0 <= i < len(btns):
            btns[i].setChecked(True)
    tabs.currentChanged.connect(show)
    show(tabs.currentIndex())
    try:
        tabs.tabBar().hide()
    except Exception:
        pass
    holder._tab_buttons = btns


class Piece:
    def __init__(self, name, kind, storey, poly, z0, z1, lip=None, lip_h=0.0, prof=None):
        self.name, self.kind, self.storey = name, kind, storey
        self.poly, self.z0, self.z1, self.lip, self.lip_h = poly, z0, z1, lip, lip_h
        self.prof = prof                            # gables: (u, mid, half, tanp[, zbase])
        self.holes = []                             # joined inside walls round a room
        self.feet = None                            # top plate joined to the walls under it
        self.parts = None                           # [(name, solid)]: made as a group of these
        self.feet_z = 0.0
        self.inside = False                         # top plate inside the walls
        self.custom = None                          # a solid made already (roof slopes, filled gables)

    def solid(self):
        if self.custom is not None:
            return self.custom
        if self.feet:
            return plate_with_walls(self.poly, self.z0, self.z1, self.feet, self.feet_z)
        if self.holes:
            return prism_holes(self.poly, self.holes, self.z0, self.z1)
        if self.prof:
            return gable_solid(self.poly, self.z0, *self.prof)
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
    # gable ends on top of the walls (on the top plate, if there is one)
    gable_notes = []
    roof_notes = None
    if p.get('roof'):
        # a pitched roof on top, and (ticked) the gable ends and raised walls under it filled in
        kg = storeys[-1]
        label = "Walls" if one_piece else storey_name(kg)
        zw = H + (p['top_t'] if p.get('top') and p.get('top_mode') != 'inside' else 0.0)
        roof_pcs, unders, roof_notes = build_roof(p, outline, zw, us, names)
        fills = 0
        if p.get('roof_fill'):
            joined = bool(p.get('gable_join'))
            if joined and p.get('top') and p.get('top_mode') != 'inside':
                raise ValueError("The gable ends can't be joined to their walls with a top plate in the way - "
                                 "untick the top plate (Base & top page) or 'Join each gable to its wall' "
                                 "(Gables page).")
            wall_at = {pc.name: (idx, pc) for idx, pc in enumerate(pieces) if pc.kind == 'wall' and pc.storey == kg}
            drop = set()
            for quad, i in wall_quads(outline, t, p['joint'], kg):
                if i in unders:
                    continue                            # the roof slopes down onto this wall
                parts = split_quad(quad, us[i], p['split_len'], gap)
                for j, pc in enumerate(parts):
                    sol = fill_solid(pc, zw, unders)
                    rise = max(q[2] for f_ in sol.faces for q in f_) - zw
                    if rise <= 1e-6:
                        continue
                    part_txt = (" part %d" % (j + 1)) if len(parts) > 1 else ""
                    below = wall_at.get("%s - %s%s" % (label, names[i], part_txt))
                    if joined and below is not None:
                        drop.add(below[0])
                        g_ = Piece("%s - %s with gable%s" % (label, names[i], part_txt), 'gable', kg, pc,
                                   below[1].z0, zw + rise)
                        g_.custom = fill_solid(pc, below[1].z0, unders)
                    else:
                        g_ = Piece("%s - Gable on %s%s" % (label, names[i], part_txt), 'gable', kg, pc, zw, zw + rise)
                        g_.custom = sol
                    pieces.append(g_)
                    fills += 1
            if drop:
                pieces = [pc for idx, pc in enumerate(pieces) if idx not in drop]
        pieces += roof_pcs
        roof_notes['fills'] = fills
    if p.get('gables') and not p.get('roof'):
        if p.get('gable_join') and p.get('top') and p.get('top_mode') != 'inside':
            raise ValueError("Gables can't be joined to their walls with a top plate in the way - untick the "
                             "top plate (Base & top page) or 'Join each gable to its wall'.")
        kg = storeys[-1]
        joined = bool(p.get('gable_join'))
        wall_at = {pc.name: (idx, pc) for idx, pc in enumerate(pieces) if pc.kind == 'wall' and pc.storey == kg}
        drop = set()
        label = "Walls" if one_piece else storey_name(kg)
        zg = H + (p['top_t'] if p.get('top') and p.get('top_mode') != 'inside' else 0.0)
        on = p.get('gable_on', 'ends')
        if on == 'pick':
            chosen = set(i for i in p['_gable_walls'] if 0 <= i < n_out)
            bad = [i + 1 for i in p['_gable_walls'] if not 0 <= i < n_out]
            if bad:
                raise ValueError("Gable walls: there's no wall %s - this shape has walls 1 to %d."
                                 % (", ".join(str(b) for b in bad), n_out))
        else:
            want = ('left', 'right') if on == 'ends' else ('front', 'back')
            chosen = set(i for i in range(n_out) if side_name(us[i]) in want)
        for quad, i in wall_quads(outline, t, p['joint'], kg):
            if i not in chosen:
                continue
            u = us[i]
            sa = outline[i][0] * u[0] + outline[i][1] * u[1]
            sb = outline[(i + 1) % n_out][0] * u[0] + outline[(i + 1) % n_out][1] * u[1]
            mid, half = (sa + sb) / 2.0, abs(sb - sa) / 2.0
            if half <= 0:
                continue
            tanp = p['ridge_h'] / half if p['ridge_h'] > 0 else math.tan(math.radians(p['gable_pitch']))
            parts = split_quad(quad, u, p['split_len'], gap)
            for j, pc in enumerate(parts):
                ss = [q[0] * u[0] + q[1] * u[1] for q in pc]
                if min(ss) <= mid <= max(ss):
                    rise = half * tanp                  # the ridge is on this piece
                else:
                    rise = max(max(0.0, half - abs(x - mid)) * tanp for x in ss)
                if rise <= 1e-6:
                    continue
                part_txt = (" part %d" % (j + 1)) if len(parts) > 1 else ""
                below = wall_at.get("%s - %s%s" % (label, names[i], part_txt))
                if joined and below is not None:
                    # the gable and the wall under it in one piece
                    drop.add(below[0])
                    nm = "%s - %s with gable%s" % (label, names[i], part_txt)
                    pieces.append(Piece(nm, 'gable', kg, pc, below[1].z0, zg + rise,
                                        prof=(u, mid, half, tanp, zg)))
                else:
                    nm = "%s - Gable on %s%s" % (label, names[i], part_txt)
                    pieces.append(Piece(nm, 'gable', kg, pc, zg, zg + rise, prof=(u, mid, half, tanp)))
            gable_notes.append((i, half * tanp, math.degrees(math.atan(tanp))))
        if drop:
            pieces = [pc for idx, pc in enumerate(pieces) if idx not in drop]
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
        # the floors above the ground floor kept back from the walls by W too, so they drop in inside a
        # subframe (onto its tabs) instead of running through it. The ground floor stays full size:
        # the frame stands on it.
        room = max(0.0, p.get('part_room', 0.0))
        fl_up = offset(inner, p['fit'] + room) if room > 0 else fl
        if fl_up is None or (room > 0 and not _inset_ok(fl_up, inner, p['fit'] + room)):
            raise ValueError("The room for a subframe (W) leaves no floor.")
        for k in range(len(hs)):
            pieces.append(Piece("%s - Floor panel" % storey_name(k), 'floor', k, fl if k == 0 else fl_up,
                                zs[k], zs[k] + ft))
        if p.get('ledges'):
            ledge_ring = wall_quads(inner, p['ledge_w'], 'mitre')
            for k in range(1, len(hs)):
                for j, (q, _i) in enumerate(ledge_ring):
                    pieces.append(Piece("%s - Ledge %d (under the %s)" % (storey_name(k - 1), j + 1,
                                                                         storey_name(k).lower()), 'ledge', k - 1, q,
                                        zs[k] - p['ledge_h'], zs[k]))
    # inside walls, standing on each floor up to the next
    rects = []
    if p['_cross_x'] or p['_cross_y']:
        if p.get('part_join'):
            # joined where they cross: one piece each (a cross, a T, an L...), stood on end to print
            q_ = dict(p)
            q_['gap'] = 0.0                         # the pieces must touch to join
            rects = [(o, hs, kd) for o, hs, kd in join_rects(partition_rects(inner, q_))]
        else:
            rects = [(r, [], kd) for r, kd in partition_rects(inner, p)]
    # each storey as set on the Storeys page: its floor and its ceiling. What holds them up (tabs or a
    # ledge) is Subframe's - on the face of its frame - so room is left under each one for it (TA)
    part_lim = {}                                   # storey -> (inside walls' bottom, top)
    if style == 'storeys':
        rows = p['_rows']
        room = max(0.0, p.get('part_room', 0.0))
        fit = p['fit']
        th = p['tab_room']
        fl0 = offset(inner, fit) if fit > 0 else inner
        fl_up = offset(inner, fit + room) if (fit + room) > 0 else inner
        if fl0 is None or fl_up is None or (fit + room > 0 and not _inset_ok(fl_up, inner, fit + room)):
            raise ValueError("The floor fit (J) and the room for a subframe (W) leave no floor.")
        n_s = len(hs)
        floor_bot = {}                              # storey -> the bottom of the room left under its floor
        for k in range(n_s):
            if not rows[k]['floor']:
                continue
            pieces.append(Piece("%s - Floor panel" % storey_name(k), 'floor', k, fl0 if k == 0 else fl_up,
                                zs[k], zs[k] + ft))
            if k > 0:
                floor_bot[k] = zs[k] - th
        for k in range(n_s):
            lo = zs[k] + (ft if rows[k]['floor'] else 0.0)
            hi = floor_bot.get(k + 1, zs[k + 1])
            if rows[k]['ceiling']:
                c_top = hi
                c_bot = c_top - p['ceil_t']
                if c_bot - th <= lo + 1e-6:
                    raise ValueError("The %s's ceiling doesn't fit between its floor and the one above "
                                     "(TB, TA, H)." % storey_name(k).lower())
                pieces.append(Piece("%s - Ceiling" % storey_name(k), 'floor', k, fl_up, c_bot, c_top))
                hi = c_bot - th
            part_lim[k] = (lo, hi)
    top_in = bool(p.get('top')) and p.get('top_mode') == 'inside'
    top_room = p['top_room']
    tplate = None
    if top_in:
        tplate = offset(inner, top_room) if top_room > 0 else inner
        if tplate is None or area2(tplate) <= 0 or (top_room > 0 and not _inset_ok(tplate, inner, top_room)):
            raise ValueError("The top plate's room for a subframe (Z) leaves no top plate.")
    joined_top = top_in and p.get('top_join') and bool(rects)
    feet = []
    if joined_top:
        # the top floor's inside walls, joined where they cross and stopped just inside the plate's edge
        q_ = dict(p)
        q_['gap'] = 0.0
        q_['part_room'] = max(p['part_room'], top_room) + 0.5
        feet = [(o, h_) for o, h_, _kd in join_rects(partition_rects(inner, q_))]

        def in_plate(q):
            c = False
            for i_ in range(len(tplate)):
                (x1, y1), (x2, y2) = tplate[i_ - 1], tplate[i_]
                if (y1 > q[1]) != (y2 > q[1]) and q[0] < x1 + (q[1] - y1) * (x2 - x1) / (y2 - y1):
                    c = not c
            return c
        if not all(in_plate(q) for o, _h in feet for q in o):
            raise ValueError("An inside wall reaches past the edge of the top plate, so they can't be joined - "
                             "move it further from the outside walls, or untick 'Join the top plate to the "
                             "inside walls'.")
    for k in range(len(hs)):
        z0 = zs[k] + ft
        z1 = zs[k + 1]
        if k in part_lim:
            z0, z1 = part_lim[k]
        if top_in and k == len(hs) - 1:
            z1 -= p['top_t']                        # the top plate sits on them, its top level with the walls
            if joined_top:
                continue                            # they're part of the top plate
        if style == 'stacked' and k < len(hs) - 1 and lip_ok:
            z1 -= p['lip_h']                        # clear of the lip under the floor above
        if style == 'dropin' and k < len(hs) - 1 and p.get('ledges'):
            z1 -= p['ledge_h']
        if z1 - z0 <= 1e-6:
            continue
        for j, (r, hs_, kind) in enumerate(rects):
            pc = Piece("%s - Inside wall %d (%s)" % (storey_name(k), j + 1, kind), 'part', k, r, z0, z1)
            pc.holes = hs_
            pieces.append(pc)
    # base and top plates
    if p.get('base'):
        # stands out (plus) or tucked in under the walls (minus)
        bp = offset(outline, -p['base_over']) if p['base_over'] != 0 else outline
        if len(bp) < 3 or (p['base_over'] < 0 and not _inset_ok(bp, outline, -p['base_over'])):
            bp = outline                            # tucked in too far: it vanished, so keep it flush
        pieces.append(Piece("Base plate", 'base', -1, bp, -p['base_t'], 0.0))
    if top_in:
        zt0 = H - p['top_t']
        if zt0 <= zs[-2] + ft:
            raise ValueError("The top plate (R) is as thick as the top floor is high.")
        if joined_top:
            # a group of two parts - the plate, and the walls under it - so the plate can be hidden on
            # its own to see into the rooms; '(one piece)' tells Scale Studio to print them as one
            pc = Piece("Top plate with walls under it (one piece)", 'top', len(hs), tplate, zt0, H)
            pc.feet, pc.feet_z = feet, zs[-2] + ft
            walls_ = PSolid()
            for o_, h_ in feet:
                w_ = prism_holes(o_, h_, zs[-2] + ft, zt0) if h_ else prism(o_, zs[-2] + ft, zt0)
                base_ = len(walls_.faces)
                walls_.faces += w_.faces
                walls_.holes.update({base_ + i_: hl for i_, hl in w_.holes.items()})
            pc.parts = [("Top plate (joined to the walls under it)", prism(tplate, zt0, H)),
                        ("%s - Inside walls under the top plate" % storey_name(len(hs) - 1), walls_)]
        else:
            pc = Piece("Top plate", 'top', len(hs), tplate, zt0, H)
        pc.inside = True
        pieces.append(pc)
    elif p.get('top'):
        tp = offset(outline, -p['top_over']) if p['top_over'] > 0 else outline
        lp = None
        if lip_ok:
            lp = lip_poly
        pieces.append(Piece("Top plate", 'top', len(hs), tp, H, H + p['top_t'], lip=lp,
                            lip_h=p['lip_h'] if lp else 0.0))
    notes = dict(H=H, zs=zs, inner_area=abs(area2(inner)) / 1e6, outer_area=abs(area2(outline)) / 1e6,
                 walls=len(outline), wall_len=sum(math.hypot(outline[(i + 1) % n_out][0] - outline[i][0],
                                                             outline[(i + 1) % n_out][1] - outline[i][1])
                                                  for i in range(n_out)) / 1000.0,
                 gables=gable_notes, wall_names=names, roof=roof_notes)
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
    'Gable ends': "Pointed gable ends on top of the walls, for a pitched roof to sit on. Each gable is its own "
                  "piece, standing on the top of the walls (or on the top plate, if you have one).",
    'Join each gable to its wall': "The gable and the top floor's wall under it come out as one piece - "
                                   "a wall with a pointed top - so there's no join to glue. Can't be used "
                                   "with a top plate, as the plate sits between them.",
    'Gables on': "Which walls get a gable: the two ends (the roof's ridge runs along the length), the front "
                 "and back (the ridge runs across), or the walls you pick by number.",
    'Walls (by number)': "The numbers of the walls to put gables on, commas between, like 2, 4. The walls are "
                         "numbered as they're named in the model - 'Wall 2 (right)' is 2.",
    'Roof': "A pitched roof on top of the walls - each slope its own piece. Subframe frames it and Roof Tiles "
            "covers it.",
    'Start here': "The building step by step - shape, walls, storeys, roof, base - then build it and open "
                  "Subframe to frame it. Each step fills in the other pages.",
    'Storeys': "Each storey's floor and ceiling - used when Floors (Floors page) is 'Each storey set on the "
               "Storeys page'. Subframe puts the tabs (or a ledge) under them.",
    'Pitched roof on top': "Puts a roof on top of the walls (on the top plate, if it's on top of the walls). "
                           "Each slope is its own piece, ready to print flat.",
    'Roof type': "Gable: two slopes meeting at a ridge, with pointed gable ends. Hip: a slope down to every "
                 "wall (on a square it's a pyramid). Mono-pitch: one slope, the other walls built up to meet it. "
                 "Saltbox: a gable with a different pitch at the back. Flat with a fall: a nearly flat roof that "
                 "sheds the rain one way. Or pick which walls are gables and the rest slope.",
    'Slopes down to': "Mono-pitch and flat roofs: which side the roof slopes down to (the low side, where the "
                      "gutter goes).",
    'Gable walls (by number)': "The walls that are gable ends, commas between, like 2 or 2, 4 - the roof slopes "
                               "down to all the others. 'Wall 2 (right)' is 2.",
    'Fill in under the roof (gable ends and raised walls)': "Builds the gable ends - and the raised walls under a "
                                                             "lean-to or flat roof - up to meet the underside of the "
                                                             "roof, each its own piece (or joined to its wall, with "
                                                             "'Join each gable to its wall' on the Gables page).",
    'Join the inside walls where they cross': "Inside walls that cross or meet are joined into one piece - a "
                                              "cross, a T or an L - instead of being cut where they meet. "
                                              "Scale Studio stands a joined piece on its end to print, so it "
                                              "comes out as the cross shape, upright, with no joins to glue.",
    'Top plate goes': "On top of the walls: a flat roof, standing on them (and past them, with S). Inside the "
                      "walls: a ceiling, sitting on the top floor's inside walls with its top level with the "
                      "outside walls, kept clear of a subframe by Z.",
    'Join the top plate to the inside walls': "The top plate and the top floor's inside walls come out as one "
                                              "piece - print it plate down, with the walls standing up from "
                                              "it. The walls stop just inside the plate's edge (Z), clear of "
                                              "the subframe.",
    'Show floors...': "A small window to hide and show each floor (and the plates), so you can see into the "
                      "rooms to add windows and doors. Close it with its X - it opens where you left it.",
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
    ('part_room', "W   Room for a subframe", 0.0, 10000.0, 1, "The inside walls stop this far short of the "
                                                               "outside walls at each end, so they butt up "
                                                               "against the frame from Subframe instead of "
                                                               "going through it, and the frame stays whole. "
                                                               "Drop-in floors above the ground floor are kept "
                                                               "back this much too, so they drop in inside the "
                                                               "frame onto its tabs. Set it to Subframe's bar "
                                                               "depth (plus its 'lift' if you use one). 0 = right "
                                                               "up to the walls."),
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
    ('base_over', "Q   Base plate stands out", -10000.0, 10000.0, 1, "How far the base plate stands out past "
                                                                     "the walls all round. 0 = flush. Minus = "
                                                                     "tucked in under the walls by that much."),
    ('top_t', "R   Top plate thickness", 0.0, 10000.0, 1, "How thick the top plate is. 0 = the floor thickness."),
    ('top_over', "S   Top plate overhang", 0.0, 10000.0, 1, "How far the top plate hangs past the walls (eaves "
                                                            "of a flat roof). 0 = flush."),
    ('top_room', "Z   Top plate room for a subframe", 0.0, 10000.0, 1, "Inside the walls: the top plate stops "
                                                                       "this far short of the outside walls all "
                                                                       "round, so it clears the frame from "
                                                                       "Subframe. Set it to Subframe's bar depth. "
                                                                       "0 = right up to the walls."),
]
GABLE_FIELDS = [
    ('gable_pitch', "X   Roof pitch", 0.0, 85.0, 1, "The angle of the roof, from level. 45 is a steep cottage "
                                                    "roof, 30 to 35 a typical Victorian slate roof."),
    ('ridge_h', "Y   Ridge height", 0.0, 100000.0, 1, "How high the top of the gable is above the top of the walls. "
                                                       "0 = worked out from the pitch (X). Set it and the pitch "
                                                       "follows from it."),
]
ROOF_FIELDS = [
    ('roof_pitch', "RA   Roof pitch", 0.0, 80.0, 2, "The angle of the roof slopes, from level. 45 is a steep cottage "
                                                     "roof, 30 to 35 a typical Victorian slate roof, 15 a lean-to."),
    ('roof_pitch2', "RB   Second pitch", 0.0, 80.0, 1, "Saltbox: the pitch of the back slope. Hip: the pitch of the "
                                                         "end slopes (left and right), so the hipped ends can be "
                                                         "steeper or flatter than the front and back. 0 = the same "
                                                         "as the roof pitch (RA)."),
    ('roof_fall', "RC   Fall (flat roof)", 0.0, 30.0, 2, "Flat roof with a fall: how much it slopes so the rain runs "
                                                          "off - a few degrees, like 3."),
    ('eave_over', "RD   Eaves overhang", 0.0, 5000.0, 1, "How far the roof hangs out past the walls along its low "
                                                          "edges (the eaves), measured level. 0 = flush with the "
                                                          "walls."),
    ('verge_over', "RE   Verge overhang (gable ends)", 0.0, 5000.0, 1, "How far the roof hangs out past the gable "
                                                                       "ends (the verges). 0 = flush with the "
                                                                       "gable walls."),
    ('roof_t', "RF   Roof thickness", 0.0, 5000.0, 1, "How thick the roof slopes are, square to the slope. 0 = half "
                                                       "the wall thickness. Roof Tiles puts its tiles on top of it."),
]
TAB_FIELDS = [
    ('tab_room', "TA   Room for the tabs", 0.0, 5000.0, 1, "How much room is left under each floor (above the "
                                                         "ground) and each ceiling for Subframe's tabs or ledge "
                                                         "to hold it up - make it at least Subframe's tab height. "
                                                         "The inside walls and the ceilings stop under it. 0 = "
                                                         "the floor thickness."),
    ('ceil_t', "TB   Ceiling thickness", 0.0, 5000.0, 1, "How thick the ceiling panels are. 0 = the floor thickness."),
]
ALL_FIELDS = SHAPE_FIELDS + WALL_FIELDS + FLOOR_FIELDS + PLATE_FIELDS + GABLE_FIELDS + ROOF_FIELDS + TAB_FIELDS

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
             "<b>Inside walls</b><br>Tick 'Join the inside walls where they cross' (Walls page) and the "
             "walls across and along come out as one piece where they meet - a cross, a T or an L - to "
             "print standing on end, with no joins.<br><br>"
             "<b>Top plate inside the walls</b><br>On the Base & top page, 'Top plate goes' can put it "
             "inside the walls as a ceiling, sitting on the top floor's inside walls, its top level with the "
             "walls, kept back from them by Z so a subframe fits. Tick 'Join the top plate to the inside walls' "
             "to print the plate and those walls as one piece, plate down.<br><br>"
             "<b>Show floors</b><br>'Show floors...' opens a little window with two ticks for each storey - "
             "its walls and its floor - and one for each plate. Untick the floors and plates (or click 'Hide "
             "floors & plates') to see down into the rooms with all the walls still there. It uses IngeTrazo's own "
             "Hide, so Edit > Undo works too. Close it with its X - it comes back where you left it.<br><br>"
             "<b>Gable ends</b><br>Tick 'Gable ends' on the Gables page and pick which walls get them. "
             "Give the roof pitch (X) or the ridge height (Y). Each gable is its own piece, standing on the "
             "top of the walls (or on the top plate), split for the print bed like the wall below it. Tick "
             "'Join each gable to its wall' to have the wall and its gable as one piece.<br><br>"
             "<b>Storeys</b><br>Pick 'Each storey set on the Storeys page' in Floors (Floors page). Then on the "
             "Storeys page tick what each storey has - a floor, a ceiling. You only get what you tick, so there "
             "are no doubled-up floors. The ground floor's floor stands on the base and the frame from Subframe "
             "stands on it; the others, and the ceilings, are kept back from the walls by W (Walls page) so they "
             "drop in inside the frame, with room under each (TA) for Subframe's tabs or ledge. Set W to the "
             "frame's bar depth.<br><br>"
             "<b>Roof</b><br>Tick 'Pitched roof on top' on the Roof page and pick the type: gable, hip, "
             "mono-pitch (lean-to), saltbox, flat with a fall, or the walls you pick as gables. Set the pitch "
             "(RA), the overhangs at the eaves (RD) and the gable ends (RE) and the thickness (RF). Each slope "
             "is its own piece, and the gable ends (and the raised walls under a lean-to) are built up to meet "
             "it - the roof makes its own gables, so the Gables page is only used for 'Join each gable to its "
             "wall'. Then frame it with Subframe and cover it with Roof Tiles. For now the roof goes on shapes "
             "without inside corners (rectangles and the like) - L, T and U shapes are coming.<br><br>"
             "Sizes are real-world mm - Scale Studio takes it down to your model scale.")


def _auto_sizes(v):
    t = float(v.get('wall_t', 0.0) or 0.0)
    ft = float(v.get('floor_t', 0.0) or 0.0)
    return {'ledge_w': t, 'ledge_h': t, 'part_t': 0.5 * t, 'base_t': ft or t, 'top_t': ft or t, 'roof_t': 0.5 * t}


PIECE_KEYS = [
    ("Ceiling", ('ceil_t', 'tab_room', 'fit', 'part_room')),
    ("Roof slope", ('roof_pitch', 'roof_pitch2', 'eave_over', 'verge_over', 'roof_t')),
    ("Gable", ('gable_pitch', 'ridge_h', 'wall_t')),
    ("Floor slab", ('floor_t', 'lip_h', 'lip_fit')),
    ("Floor panel", ('floor_t', 'fit')),
    ("Ledge", ('ledge_w', 'ledge_h')),
    ("Inside wall", ('part_t', 'part_room')),
    ("Base plate", ('base_t', 'base_over')),
    ("Top plate", ('top_t', 'top_over', 'lip_h', 'top_room')),
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
        self.setMinimumSize(360, 1015)

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
        from PySide6.QtCore import QPointF, QRectF, Qt
        import math as _m
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 246))
        k = min(float(self.width()) / 360.0, self.height() / 1015.0)
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

        # ---- a gable end, seen from the end
        p.setPen(QColor(60, 60, 60))
        p.setFont(f)
        p.drawText(QRectF(10, 572, 340, 18), Qt.AlignLeft, "Gable end, seen from the end")
        gx0, gx1, gz, gtop = 90.0, 270.0, 670.0, 600.0
        box(gx0, gz, gx1 - gx0, 40, wallc)                                  # the wall below
        poly([(gx0, gz), (gx1, gz), ((gx0 + gx1) / 2, gtop)], QColor(186, 96, 70))   # the gable
        p.setPen(QPen(QColor(120, 70, 50), 1.0, Qt.DashLine))
        p.drawLine(QPointF(gx0, gz), QPointF(gx1, gz))                       # where it stands on the walls
        p.setPen(QPen(red, 1.1))
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(gx0 - 34, gz - 34, 68, 68), 0, int(37.9 * 16))     # the pitch, from level
        p.setPen(red)
        p.drawText(QRectF(gx0 + 34, gz - 22, 20, 16), Qt.AlignCenter, "X")
        dim(gx1 + 20, gz, gx1 + 20, gtop, "Y", gx1 + 32, (gz + gtop) / 2)
        p.setPen(QColor(90, 90, 90))
        p.drawText(QRectF(gx0, gz + 12, gx1 - gx0, 14), Qt.AlignCenter, "end wall")

        f2 = QFont()
        f2.setPointSizeF(8.5)
        p.setFont(f2)
        p.setPen(QColor(60, 60, 60))
        notes = ["A  overall length", "B  overall width", "C  wall thickness", "D, E  cut-out (L, T, U)",
                 "F  a floor's height", "G  total height (divided)", "H  floor thickness",
                 "J  floor fit", "K  locating lip depth", "L  lip fit", "M  ledge width", "N  ledge height",
                 "P  base plate thickness", "Q  base plate stands out", "R  top plate thickness",
                 "S  top plate overhang", "T  inside wall thickness", "U  longest wall piece",
                 "V  gap between pieces", "W  room for a subframe", "X  roof pitch (gables)",
                 "Y  ridge height (gables)", "Z  top plate room (inside)"]
        for i, t_ in enumerate(notes):
            p.drawText(QRectF(10 if i < 12 else 185, 704 + (i % 12) * 9.0, 175, 10),
                       Qt.AlignLeft | Qt.AlignVCenter, t_)

        # ---- the roof, seen from the end (Roof page)
        p.setFont(f)
        p.setPen(QColor(60, 60, 60))
        p.drawText(QRectF(10, 826, 340, 18), Qt.AlignLeft, "Roof, seen from the end")
        rx0, rx1, rz, rtop = 100.0, 260.0, 930.0, 870.0      # walls' outside faces, wall top, ridge
        box(rx0, rz, 16, 30, wallc)
        box(rx1 - 16, rz, 16, 30, wallc)
        poly([(rx0, rz), (rx1, rz), ((rx0 + rx1) / 2, rtop)], QColor(186, 96, 70))   # the gable end
        over, th = 30.0, 9.0
        sl = (rz - rtop) / ((rx1 - rx0) / 2)
        mid_ = (rx0 + rx1) / 2
        rc = QColor(*COLOURS['roof'])
        for sgn in (-1, 1):                                  # each slope, plumb-cut at the eaves
            xe = mid_ + sgn * ((rx1 - rx0) / 2 + over)
            ze = rz + over * sl
            poly([(xe, ze), (mid_, rtop), (mid_, rtop - th * 1.3), (xe, ze - th * 1.3)], rc)
        dim(rx0 - over, rz + 46, rx0, rz + 46, "RD", rx0 - over / 2, rz + 58)
        p.setPen(QPen(red, 1.1))
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(rx1 - 40, rz - 40, 80, 80), int(180 * 16), int(-37 * 16))   # the pitch, from level
        p.setPen(red)
        p.drawText(QRectF(rx1 - 66, rz - 22, 24, 16), Qt.AlignCenter, "RA")
        dim(mid_ + 6, rtop - th * 1.3, mid_ + 6, rtop, "", 0, 0)
        p.setPen(red)
        p.drawText(QRectF(mid_ + 8, rtop - 26, 24, 14), Qt.AlignCenter, "RF")
        p.setFont(f2)
        p.setPen(QColor(60, 60, 60))
        for i, t_ in enumerate(["RA  roof pitch", "RB  second pitch (saltbox back, hip ends)",
                                "RC  fall (flat roof)", "RD  eaves overhang", "RE  verge overhang (past the gables)",
                                "RF  roof thickness"]):
            p.drawText(QRectF(10 if i < 3 else 185, 980 + (i % 3) * 10.0, 175, 10),
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
            if pc.kind in ('base', 'top', 'roof'):
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
        shown = [pc for pc in self.pieces if pc.storey == st or (pc.kind in ('wall', 'gable')
                                                                 and pc.name.startswith("Walls"))]
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
                for h_ in pc.holes:
                    draw(h_, (240, 232, 215))
        for pc in self.pieces:
            if pc.feet and st == len(self.notes['zs']) - 2:
                for o_, h_ in pc.feet:
                    draw(o_, COLOURS['part'])
                    for hh in h_:
                        draw(hh, (240, 232, 215))
        for pc in shown:
            if pc.kind == 'gable':                  # the gables, over the walls they stand on
                draw(pc.poly, COLOURS['gable'], width=1.6)
        for pc in self.pieces:
            if pc.kind == 'roof':                   # the roof slopes, see-through, over it all
                col = QColor(*COLOURS['roof'])
                col.setAlpha(45)
                p.setBrush(col)
                p.setPen(QPen(QColor(*COLOURS['roof']).darker(140), 1.2, Qt.DashLine))
                p.drawPolygon(QPolygonF([P(q) for q in pc.poly]))
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
                x_a = x0 + (wall_w + 4 if pc.kind == 'floor' or pc.inside else
                            (-6 if pc.kind in ('base', 'top') else 0))
                col = QColor(*COLOURS[pc.kind])
                p.setPen(QPen(col.darker(160), 0.8))
                p.setBrush(col)
                p.drawRect(QRectF(x_a, Z(pc.z1), x0 + span - x_a, Z(pc.z0) - Z(pc.z1)))
                if pc.feet:                         # the walls hanging under it, joined on
                    col = QColor(*COLOURS['part'])
                    p.setBrush(col)
                    p.drawRect(QRectF(x0 + wall_w + span * 0.35, Z(pc.z0), span * 0.1, Z(pc.feet_z) - Z(pc.z0)))
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
        rf = [pc for pc in self.pieces if pc.kind == 'roof']
        if rf:                                      # the roof, roughly, seen from the end
            zr0 = min(pc.z0 for pc in rf)
            zr1 = max(pc.z1 for pc in rf)
            col = QColor(*COLOURS['roof'])
            p.setPen(QPen(col.darker(150), 0.8))
            col.setAlpha(170)
            p.setBrush(col)
            if len(rf) == 1:                        # one slope: a wedge
                pts_ = [QPointF(x0 - 6, Z(zr0)), QPointF(x0 + span + 6, Z(zr0)), QPointF(x0 + span + 6, Z(zr1))]
            else:
                pts_ = [QPointF(x0 - 6, Z(zr0)), QPointF(x0 + span + 6, Z(zr0)), QPointF(x0 + span / 2, Z(zr1))]
            p.drawPolygon(QPolygonF(pts_))
        gs = [pc for pc in self.pieces if pc.kind == 'gable' and pc.prof]
        if gs:                                      # the gable, seen from the end, over the walls
            zg0 = gs[0].prof[4] if len(gs[0].prof) > 4 else gs[0].z0
            zg1 = max(pc.z1 for pc in gs)
            col = QColor(*COLOURS['gable'])
            p.setPen(QPen(col.darker(160), 0.8))
            col.setAlpha(170)
            p.setBrush(col)
            p.drawPolygon(QPolygonF([QPointF(x0, Z(zg0)), QPointF(x0 + span, Z(zg0)),
                                     QPointF(x0 + span / 2, Z(zg1))]))
        p.setPen(QColor(90, 90, 90))
        f3 = QFont()
        f3.setPointSizeF(7.5)
        p.setFont(f3)
        for kk in range(len(zs) - 1):
            p.drawText(QRectF(x0 + wall_w + 6, Z(zs[kk + 1]) + 2, span, 12), Qt.AlignLeft,
                       "%s  %.0f" % (storey_name(kk), zs[kk + 1] - zs[kk]))
        p.drawText(QRectF(x0, H - 20, sw, 16), Qt.AlignCenter, "side - %.0f mm high" % zhi)
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
            m = QDoubleSpinBox()
            m.setDecimals(main.decimals())
            m.setRange(main.minimum(), main.maximum())
            m.setSuffix(main.suffix())
            m.setSpecialValueText(main.specialValueText())
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


def roof_top_for(v, angle):
    """How high the top of the roof comes out (mm above the bottom of the walls) with the roof at this
    angle - the pitch, or the fall of a flat roof."""
    d = dict(v)
    d['roof'] = True
    d['roof_fall' if d.get('roof_type') == 'flat' else 'roof_pitch'] = angle
    p = plan_params(d)
    _pcs, notes = build_plan(p, make_outline(p))
    return notes['roof']['top']


def solve_roof_angle(v, target):
    """The roof angle that brings the top of the roof to 'target' mm: (angle, None) or (None, why not)."""
    flat = v.get('roof_type') == 'flat'
    lo, hi = (0.2, 29.5) if flat else (1.0, 79.0)
    try:
        t_lo, t_hi = roof_top_for(v, lo), roof_top_for(v, hi)
    except ValueError as e:
        return None, str(e)
    if target < t_lo - 0.5:
        return None, "That's too low for a roof on these walls - it needs at least %.0f mm." % t_lo
    if target > t_hi + 0.5:
        return None, "That's too high for this roof - at most %.0f mm." % t_hi
    for _ in range(40):
        mid = (lo + hi) / 2.0
        if roof_top_for(v, mid) < target:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2.0, 2), None


def open_openings(dlg):
    """Opens Openings (if it's loaded) - the next step after the floor plan: cutting the window and door
    holes in the walls."""
    import sys
    for name, mod in list(sys.modules.items()):
        if mod is not None and (name == "ed3d_openings" or name.endswith("_ed3d_openings")) and \
                hasattr(mod, 'OpeningsTool'):
            try:
                vp = dlg.viewport
                dlg.close()                         # one window at a time: Floor Plan steps aside
                mod.OpeningsTool().on_activate(vp)
                d2 = getattr(mod.OpeningsTool, '_dialog', None)
                if d2 is not None and hasattr(d2, 'show_start'):
                    d2.show_start()
                return
            except Exception as e:
                QMessageBox.warning(dlg, PLUGIN_NAME, "Couldn't open Openings:\n%s" % e)
                return
    QMessageBox.information(dlg, PLUGIN_NAME, "Openings isn't loaded - put ed3d_openings.py in the plugins "
                            "folder with this one.")


def open_subframe(dlg):
    """Opens Subframe (if it's loaded) at its 'Start here' page, to frame what was just built."""
    import sys
    for name, mod in list(sys.modules.items()):
        if mod is not None and (name == "ed3d_subframe" or name.endswith("_ed3d_subframe")) and \
                hasattr(mod, 'SubframeTool'):
            try:
                mod.SubframeTool().on_activate(dlg.viewport)
                d2 = getattr(mod.SubframeTool, '_dialog', None)
                if d2 is not None and hasattr(d2, 'show_start'):
                    d2.show_start()
                return
            except Exception as e:
                QMessageBox.warning(dlg, PLUGIN_NAME, "Couldn't open Subframe:\n%s" % e)
                return
    QMessageBox.information(dlg, PLUGIN_NAME, "Subframe isn't loaded - put ed3d_subframe.py in the plugins "
                            "folder with this one.")


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
        # the page buttons go on two rows above the pages (one row of tabs was getting crowded)
        tabs_box = QWidget()
        tb_lay = QVBoxLayout(tabs_box)
        tb_lay.setContentsMargins(0, 0, 0, 0)
        tb_lay.setSpacing(2)
        self.tab_rows = QWidget()
        tb_lay.addWidget(self.tab_rows)
        tb_lay.addWidget(self.tabs, 1)
        row.addWidget(tabs_box, 1)
        self.sp = {}
        self.page_of = {}
        # 'Start here' first: the steps are put on it once every other page is made
        self.page_start = QWidget()
        self.tabs.addTab(self.page_start, "Start here")

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
        # how high the building comes out: the walls, and to the top of the roof
        self.lbl_height = QLabel()
        self.lbl_height.setWordWrap(True)
        fs.addRow(self.lbl_height)
        self.lbl_height2 = QLabel()                 # the same, on the Start here page
        self.lbl_height2.setWordWrap(True)

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
        self.ck_join = QCheckBox("Join the inside walls where they cross")
        fw.addRow(self.ck_join)
        self.ck_join.toggled.connect(self.changed)
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

        # ---- Storeys: each storey's floor and ceiling, and what they rest on
        page = QWidget()
        fst = QVBoxLayout(page)
        self.tabs.addTab(page, "Storeys")
        self.lbl_st_head = QLabel("Pick 'Each storey set on the Storeys page' in Floors (Floors page) to use "
                                  "this page.")
        self.lbl_st_head.setWordWrap(True)
        fst.addWidget(self.lbl_st_head)
        from PySide6.QtWidgets import QGridLayout
        self.st_grid_w = QWidget()
        self.st_grid = QGridLayout(self.st_grid_w)
        self.st_grid.setContentsMargins(0, 0, 0, 0)
        fst.addWidget(self.st_grid_w)
        self.st_rows = []                           # [(floor tick, ceiling tick, storey name)]
        self._st_data = []
        fs2 = QFormLayout()
        fst.addLayout(fs2)
        spin_rows(fs2, TAB_FIELDS)
        self.lbl_storeys = QLabel()
        self.lbl_storeys.setWordWrap(True)
        self.lbl_storeys.setStyleSheet("color: gray;")
        fst.addWidget(self.lbl_storeys)
        fst.addStretch(1)

        # ---- Base & top
        page = QWidget()
        fp = QFormLayout(page)
        self.tabs.addTab(page, "Base & top")
        self.ck_base = QCheckBox("Base plate (plinth) under it all")
        fp.addRow(self.ck_base)
        spin_rows(fp, PLATE_FIELDS[:2])
        self.ck_top = QCheckBox("Top plate (flat roof / ceiling)")
        fp.addRow(self.ck_top)
        self.cb_topmode = QComboBox()
        for lab_, k_ in TOP_MODES:
            self.cb_topmode.addItem(lab_, k_)
        fp.addRow("Top plate goes", self.cb_topmode)
        self.cb_topmode.currentIndexChanged.connect(self.changed)
        spin_rows(fp, PLATE_FIELDS[2:])
        self.ck_topjoin = QCheckBox("Join the top plate to the inside walls")
        fp.addRow(self.ck_topjoin)
        self.ck_topjoin.toggled.connect(self.changed)
        for c_ in (self.ck_base, self.ck_top):
            c_.toggled.connect(self.changed)
        np_ = QLabel("0 = the floor thickness (or the wall thickness). On top of the walls, with slabs and a lip "
                     "(K), the top plate gets a lip too, so it sits square. Inside the walls it rests on the top "
                     "floor's inside walls (they're cut down by its thickness) - so add some inside walls for it "
                     "to sit on.")
        np_.setWordWrap(True)
        np_.setStyleSheet("color: gray;")
        fp.addRow(np_)

        # ---- Gables
        page = QWidget()
        fg = QFormLayout(page)
        self.tabs.addTab(page, "Gables")
        self.ck_gables = QCheckBox("Gable ends")
        fg.addRow(self.ck_gables)
        self.cb_gable_on = QComboBox()
        for lab_, k_ in GABLE_ON:
            self.cb_gable_on.addItem(lab_, k_)
        fg.addRow("Gables on", self.cb_gable_on)
        self.ed_gwalls = QLineEdit()
        self.ed_gwalls.setPlaceholderText("e.g. 2, 4")
        self.lbl_gwalls = QLabel("Walls (by number)")
        fg.addRow(self.lbl_gwalls, self.ed_gwalls)
        spin_rows(fg, GABLE_FIELDS)
        self.ck_gjoin = QCheckBox("Join each gable to its wall")
        fg.addRow(self.ck_gjoin)
        self.ck_gjoin.toggled.connect(self.changed)
        self.sp['gable_pitch'][0].setSuffix("°")
        self.sp['ridge_h'][0].setSpecialValueText("from the pitch (X)")
        self.ck_gables.toggled.connect(self.changed)
        self.cb_gable_on.currentIndexChanged.connect(self.changed)
        self.ed_gwalls.textChanged.connect(self.changed)
        self.lbl_gables = QLabel()
        self.lbl_gables.setWordWrap(True)
        self.lbl_gables.setStyleSheet("color: gray;")
        fg.addRow(self.lbl_gables)

        # ---- Roof
        page = QWidget()
        fr = QFormLayout(page)
        self.tabs.addTab(page, "Roof")
        self.ck_roof = QCheckBox("Pitched roof on top")
        fr.addRow(self.ck_roof)
        self.cb_roof_type = QComboBox()
        for lab_, k_ in ROOF_TYPES:
            self.cb_roof_type.addItem(lab_, k_)
        fr.addRow("Roof type", self.cb_roof_type)
        self.cb_roof_low = QComboBox()
        for lab_, k_ in ROOF_LOW:
            self.cb_roof_low.addItem(lab_, k_)
        self.lbl_roof_low = QLabel("Slopes down to")
        fr.addRow(self.lbl_roof_low, self.cb_roof_low)
        self.ed_roof_gables = QLineEdit()
        self.ed_roof_gables.setPlaceholderText("e.g. 2   (the walls that are gable ends)")
        self.lbl_roof_gables = QLabel("Gable walls (by number)")
        fr.addRow(self.lbl_roof_gables, self.ed_roof_gables)
        spin_rows(fr, ROOF_FIELDS)
        for k_ in ('roof_pitch', 'roof_pitch2', 'roof_fall'):
            self.sp[k_][0].setSuffix("°")
        self.sp['roof_pitch2'][0].setSpecialValueText("same as RA")
        self.ck_roof_fill = QCheckBox("Fill in under the roof (gable ends and raised walls)")
        fr.addRow(self.ck_roof_fill)
        for c_ in (self.ck_roof, self.ck_roof_fill):
            c_.toggled.connect(self.changed)
        for cb_ in (self.cb_roof_type, self.cb_roof_low):
            cb_.currentIndexChanged.connect(self.changed)
        self.ed_roof_gables.textChanged.connect(self.changed)
        self.lbl_roof = QLabel()
        self.lbl_roof.setWordWrap(True)
        self.lbl_roof.setStyleSheet("color: gray;")
        fr.addRow(self.lbl_roof)

        # ---- Output
        page = QWidget()
        fo = QFormLayout(page)
        self.tabs.addTab(page, "Output")
        self.cb_group = QComboBox()
        for lab_, k_ in GROUPINGS:
            self.cb_group.addItem(lab_, k_)
        fo.addRow("Pieces go", self.cb_group)
        self.cb_group.currentIndexChanged.connect(self.changed)
        no_ = QLabel("Every piece - each wall section, gable, floor, ledge and plate - is a plain group of its own (not "
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
        two_row_tabs(self.tabs, self.tab_rows)
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
        self.b_floors = QPushButton("Show floors...")
        self.b_floors.setToolTip("A small window to hide and show each floor (and the plates), so you can see "
                                 "into the rooms to add windows and doors. Close it with its X when you're done.")
        self.b_floors.clicked.connect(lambda: open_floors_window(self.viewport, self))
        brow.addWidget(self.b_floors)
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
        self.make_start_here()

    def make_start_here(self):
        """The 'Start here' page: the building step by step, from the basics to cutting the openings."""
        self.cb_ceilings = QComboBox()
        for t_, d_ in (("Under the roof only (the top storey)", 'top'), ("On every storey", 'every'),
                       ("None", 'none')):
            self.cb_ceilings.addItem(t_, d_)
        rows_ = self.storey_values()
        if rows_ and all(r_['ceiling'] for r_ in rows_):
            self.cb_ceilings.setCurrentIndex(1)
        elif rows_ and not any(r_['ceiling'] for r_ in rows_):
            self.cb_ceilings.setCurrentIndex(2)
        self.cb_ceilings.setToolTip("Which storeys get a ceiling panel. Tick or untick them one by one on the "
                                    "Storeys page.")
        self.cb_ceilings.currentIndexChanged.connect(self.set_ceilings)

        def storeys_on():
            i_ = self.cb_fstyle.findData('storeys')
            if self.cb_fstyle.currentIndex() != i_:
                self.cb_fstyle.setCurrentIndex(i_)

        # ---- step 1, the basics: a roof or not, and the building's size - its own boxes, filling in the
        # pages behind (the height with the roof sets the roof's pitch)
        from PySide6.QtWidgets import QDoubleSpinBox as _DS
        self._basics_busy = False
        self.ck_b_roof = QCheckBox("A roof on it")
        self.ck_b_roof.setToolTip("Tick for a pitched roof (the Roof page has the kinds - gable, hip, lean-to...).")

        def mm_box(tip, top=500000.0):
            b = _DS()
            b.setDecimals(0)
            b.setRange(0.0, top)
            b.setSuffix(" mm")
            b.setKeyboardTracking(False)            # worked out when you press Enter or move on
            b.setToolTip(tip)
            return b
        self.sb_len = mm_box("How long the building is, outside the walls, along the front.")
        self.sb_wid = mm_box("How wide the building is, outside the walls, front to back.")
        self.sb_hw = mm_box("From the bottom of the walls to the top of the walls - the roof not counted. "
                            "It's shared out equally between the floors.")
        self.sb_hr = mm_box("From the bottom of the walls to the very top of the roof (the ridge). The roof's "
                            "pitch is worked out to fit it.")
        self.sp_b_floors = QSpinBox()
        self.sp_b_floors.setRange(1, 50)
        self.sp_b_floors.setKeyboardTracking(False)
        self.sp_b_floors.setToolTip("How many floors (storeys) the building has.")
        self.lbl_basics = QLabel()
        self.lbl_basics.setWordWrap(True)
        self.ck_b_roof.toggled.connect(self.apply_basics)
        for b_ in (self.sb_len, self.sb_wid, self.sb_hw, self.sb_hr, self.sp_b_floors):
            b_.valueChanged.connect(self.apply_basics)
        self.refresh_basics()
        steps = [
            ("The basics", "Does it have a roof, and how big is it? Sizes are real-world mm, outside the walls "
                           "- Scale Studio takes it down to your model scale.",
             [('widget', None, self.ck_b_roof), ('widget', "Length", self.sb_len), ('widget', "Width", self.sb_wid),
              ('widget', "Height without the roof", self.sb_hw),
              ('widget', "Height with the roof", self.sb_hr),
              ('widget', "Number of floors", self.sp_b_floors), ('widget', None, self.lbl_basics),
              ('note', "Heights are from the bottom of the walls (a base plate goes under that). Press Enter "
                       "after typing a size to see it in the preview.")]),
            ("Shape", "A plain rectangle - or an L, T or U shape?",
             [('combo', "Shape", self.cb_shape), ('spin', 'cut_l'), ('spin', 'cut_w'),
              ('widget', None, self.lbl_height2),
              ('note', "For any other shape, type its corners on the Shape page - or draw it as a level face "
                       "and use 'Build on selected face' at the 'Build it' step.")]),
            ("Walls", "How thick are the walls, how do the corners meet, and where do the inside walls go?",
             [('spin', 'wall_t'), ('combo', "Wall ends meet", self.cb_joint),
              ('line', "Inside walls across, at", self.ed_cx), ('line', "Inside walls along, at", self.ed_cy),
              ('spin', 'part_room'),
              ('note', "Framing it with Subframe? Set W to its bar depth (160 for 160 mm bars) - the inside "
                       "walls, floors and ceilings then keep clear of the frame.")]),
            ("Floors and ceilings", "Each storey gets a floor. Which get a ceiling? (The Storeys page has a tick "
                                    "for each one.)",
             [('spin', 'floor_t'), ('spin', 'fit'), ('widget', "Ceilings", self.cb_ceilings), ('spin', 'ceil_t'),
              ('spin', 'tab_room'),
              ('note', "Different heights for each floor? Type them on the Floors page.")]),
            ("Roof", "What kind of roof, and how far does it hang over the walls?",
             [('check', self.ck_roof), ('combo', "Roof type", self.cb_roof_type), ('spin', 'roof_pitch'),
              ('spin', 'eave_over'), ('spin', 'verge_over'), ('spin', 'roof_t'), ('check', self.ck_roof_fill)]),
            ("Base", "A base plate (plinth) under it all?",
             [('check', self.ck_base), ('spin', 'base_t'), ('spin', 'base_over')]),
            ("Build it", "Check the preview on the left, then build it.",
             [('button', "Build floor plan", lambda: self.tool.build(self, on_face=False)),
              ('button', "Build on selected face", lambda: self.tool.build(self, on_face=True)),
              ('note', "It's built at the origin of the model (or inside the edge of the face you picked). "
                       "Every piece is its own group, ready for Scale Studio.")]),
            ("Cut the openings", "Next, the window and door holes in the walls - before the frame, so the "
                                 "frame goes round them.",
             [('note', "Open Openings and cut the holes. After that come the windows and doors, then the "
                       "frame (Subframe), as on your toolbar."),
              ('button', "Open Openings", lambda: open_openings(self))]),
        ]
        try:
            self.start = StartHere(self, self.page_start, steps, on_show={0: self.refresh_basics, 3: storeys_on},
                                   intro="Go through the steps with Next - each one fills in the pages to the "
                                         "right, so you can fine-tune them there afterwards.")
        except Exception as e:
            print("%s: 'Start here' page not made: %s" % (PLUGIN_NAME, e))

    def apply_basics(self, *_):
        """The basics step changed: fill in the pages behind it, and work the roof's pitch out from the
        height with the roof."""
        if getattr(self, '_basics_busy', False):
            return
        self._basics_busy = True
        msg, bad = "", False
        try:
            self.ck_roof.setChecked(self.ck_b_roof.isChecked())
            self.sp['length'][0].setValue(self.sb_len.value())
            self.sp['width'][0].setValue(self.sb_wid.value())
            self.cb_hmode.setCurrentIndex(max(0, self.cb_hmode.findData('divide')))
            self.sp_storeys.setValue(int(self.sp_b_floors.value()))
            self.sp['total_h'][0].setValue(self.sb_hw.value())
            if self.ck_b_roof.isChecked() and self.sb_hr.value() > 0:
                v = self.values()
                ang, why = solve_roof_angle(v, self.sb_hr.value())
                if ang is None:
                    msg, bad = why, True
                else:
                    key = 'roof_fall' if v.get('roof_type') == 'flat' else 'roof_pitch'
                    self.sp[key][0].setValue(ang)
        finally:
            self._basics_busy = False
        self.changed()
        self.refresh_basics(msg if bad else None)

    def refresh_basics(self, problem=None):
        """The basics step's boxes, from the pages behind it."""
        if not hasattr(self, 'sb_len') or getattr(self, '_basics_busy', False):
            return
        self._basics_busy = True
        try:
            v = self.values()
            nt = self.preview.notes if self.preview.pieces else {}
            boxes = [(self.sb_len, v['length']), (self.sb_wid, v['width'])]
            try:
                hs = plan_params(v)['_heights']
                boxes += [(self.sp_b_floors, len(hs)), (self.sb_hw, sum(hs))]
            except Exception:
                boxes += [(self.sp_b_floors, int(v.get('storeys') or 1)), (self.sb_hw, v.get('total_h', 0.0))]
            rn = nt.get('roof') if nt else None
            if rn and not problem:
                boxes.append((self.sb_hr, rn['top']))
            for b_, val in boxes:
                b_.blockSignals(True)
                b_.setValue(val)
                b_.blockSignals(False)
            self.ck_b_roof.blockSignals(True)
            self.ck_b_roof.setChecked(bool(v['roof']))
            self.ck_b_roof.blockSignals(False)
            self.sb_hr.setEnabled(bool(v['roof']))
            if problem:
                self.lbl_basics.setText(problem)
                self.lbl_basics.setStyleSheet("color: #b35900;")
            elif not nt:
                self.lbl_basics.setText(self.preview.msg or "")
                self.lbl_basics.setStyleSheet("color: #b35900;")
            elif rn:
                self.lbl_basics.setText("That's a %s roof, %.0f mm high above the walls. %s" % (
                    " and ".join("%g°" % a_ for a_ in rn['pitches']), rn['rise'],
                    "(The roof's kind and overhangs are on the Roof step.)"))
                self.lbl_basics.setStyleSheet("color: #2e7d32;")
            else:
                self.lbl_basics.setText("No roof - the walls are %.0f mm high." % nt['H'])
                self.lbl_basics.setStyleSheet("color: #2e7d32;")
        finally:
            self._basics_busy = False

    def set_ceilings(self, *_):
        """'Ceilings' on the Start here page: ticks the ceilings on the Storeys page to match."""
        mode = self.cb_ceilings.currentData() or 'top'
        n = len(self.st_rows)
        for k, (_cf, cc, _lab) in enumerate(self.st_rows):
            cc.setChecked(mode == 'every' or (mode == 'top' and k == n - 1))

    def show_start(self):
        try:
            self.tabs.setCurrentIndex(0)
            self.start.go(0)
        except Exception:
            pass

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
                 part_join=self.ck_join.isChecked(),
                 base=self.ck_base.isChecked(), top=self.ck_top.isChecked(),
                 gables=self.ck_gables.isChecked(), gable_on=self.cb_gable_on.currentData() or 'ends',
                 gable_walls=self.ed_gwalls.text().strip(), gable_join=self.ck_gjoin.isChecked(),
                 top_mode=self.cb_topmode.currentData() or 'over', top_join=self.ck_topjoin.isChecked(),
                 roof=self.ck_roof.isChecked(), roof_type=self.cb_roof_type.currentData() or 'gable_len',
                 roof_low=self.cb_roof_low.currentData() or 'front',
                 roof_gables=self.ed_roof_gables.text().strip(), roof_fill=self.ck_roof_fill.isChecked(),
                 storey_rows=self.storey_values())
        for key, (s, _) in self.sp.items():
            v[key] = float(s.value())
        return v

    def set_values(self, d):
        self._busy = True
        try:
            for cb, key in ((self.cb_shape, 'shape'), (self.cb_joint, 'joint'), (self.cb_hmode, 'height_mode'),
                            (self.cb_fstyle, 'floor_style'), (self.cb_group, 'grouping'),
                            (self.cb_gable_on, 'gable_on'), (self.cb_topmode, 'top_mode'),
                            (self.cb_roof_type, 'roof_type'), (self.cb_roof_low, 'roof_low')):
                i_ = cb.findData(d.get(key, DEFAULTS[key]))
                cb.setCurrentIndex(max(0, i_))
            self.sp_storeys.setValue(int(d.get('storeys', DEFAULTS['storeys']) or 1))
            self.ed_corners.setPlainText(str(d.get('corners_text', '') or ''))
            for ed, key in ((self.ed_heights, 'storey_heights'), (self.ed_cx, 'cross_x'), (self.ed_cy, 'cross_y'),
                            (self.ed_gwalls, 'gable_walls'), (self.ed_roof_gables, 'roof_gables')):
                val = d.get(key, DEFAULTS[key])
                if isinstance(val, (list, tuple)):
                    val = ", ".join("%g" % x for x in val)
                ed.setText(str(val or ''))
            for c_, key in ((self.ck_ledges, 'ledges'), (self.ck_one, 'one_piece'), (self.ck_join, 'part_join'),
                            (self.ck_base, 'base'),
                            (self.ck_top, 'top'), (self.ck_gables, 'gables'),
                            (self.ck_gjoin, 'gable_join'), (self.ck_topjoin, 'top_join'),
                            (self.ck_roof, 'roof'), (self.ck_roof_fill, 'roof_fill')):
                c_.setChecked(bool(d.get(key, DEFAULTS[key])))
            rows_ = d.get('storey_rows', [])
            self._st_data = [dict(r_) for r_ in rows_] if isinstance(rows_, (list, tuple)) else []
            for w_ in self.st_rows:
                for x_ in w_:
                    try:
                        x_.setParent(None)
                        x_.deleteLater()
                    except Exception:
                        pass
            self.st_rows = []
            for key, (s, _) in self.sp.items():
                try:
                    val = float(d.get(key, DEFAULTS[key]))
                except (TypeError, ValueError):
                    val = float(DEFAULTS[key] or 0.0)
                s.setValue(val)
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
        self.sp['fit'][0].setEnabled(fsy in ('dropin', 'storeys'))
        self.sp['lip_h'][0].setEnabled(fsy == 'stacked')
        self.sp['lip_fit'][0].setEnabled(fsy == 'stacked' and v['lip_h'] > 0)
        self.ck_ledges.setEnabled(fsy == 'dropin')
        self.sp['ledge_w'][0].setEnabled(fsy == 'dropin' and v['ledges'])
        self.sp['ledge_h'][0].setEnabled(fsy == 'dropin' and v['ledges'])
        self.ck_one.setEnabled(fsy != 'stacked')
        self.sp['part_t'][0].setEnabled(bool(v['cross_x'] or v['cross_y']))
        self.sp['part_room'][0].setEnabled(bool(v['cross_x'] or v['cross_y']) or fsy in ('dropin', 'storeys'))
        self.ck_join.setEnabled(bool(v['cross_x'] and v['cross_y']))
        for k_ in ('base_t', 'base_over'):
            self.sp[k_][0].setEnabled(v['base'])
        t_in = v['top'] and v['top_mode'] == 'inside'
        self.cb_topmode.setEnabled(v['top'])
        self.sp['top_t'][0].setEnabled(v['top'])
        self.sp['top_over'][0].setEnabled(v['top'] and not t_in)
        self.sp['top_room'][0].setEnabled(t_in)
        self.ck_topjoin.setEnabled(t_in and bool(v['cross_x'] or v['cross_y']))
        r_on = v['roof']
        g_on = v['gables'] and not r_on              # with a roof, the roof makes its own gables
        self.ck_gables.setEnabled(not r_on)
        self.cb_gable_on.setEnabled(g_on)
        self.ed_gwalls.setEnabled(g_on and v['gable_on'] == 'pick')
        self.lbl_gwalls.setEnabled(g_on and v['gable_on'] == 'pick')
        self.sp['gable_pitch'][0].setEnabled(g_on and v['ridge_h'] <= 0)
        self.sp['ridge_h'][0].setEnabled(g_on)
        self.ck_gjoin.setEnabled((g_on or (r_on and v['roof_fill'])) and not (v['top'] and v['top_mode'] != 'inside'))
        rt = v['roof_type']
        for w_ in (self.cb_roof_type, self.ck_roof_fill):
            w_.setEnabled(r_on)
        for w_ in (self.cb_roof_low, self.lbl_roof_low):
            w_.setEnabled(r_on and rt in ('mono', 'flat'))
        for w_ in (self.ed_roof_gables, self.lbl_roof_gables):
            w_.setEnabled(r_on and rt == 'pick')
        self.sp['roof_pitch'][0].setEnabled(r_on and rt != 'flat')
        self.sp['roof_pitch2'][0].setEnabled(r_on and rt in ('saltbox', 'hip'))
        self.sp['roof_fall'][0].setEnabled(r_on and rt == 'flat')
        for k_ in ('eave_over', 'verge_over', 'roof_t'):
            self.sp[k_][0].setEnabled(r_on)
        # the floors in the 'Floor shown' list
        try:
            n = len(plan_params(v)['_heights'])
        except Exception:
            n = 1
        self._busy = True
        try:
            self.build_storey_rows(n)
        finally:
            self._busy = False
        st_on = fsy == 'storeys'
        self.st_grid_w.setEnabled(st_on)
        for k_, _l, _lo, _hi, _d, _t in TAB_FIELDS:
            self.sp[k_][0].setEnabled(st_on)
        self.lbl_st_head.setText("Tick what each storey has - you only get what you tick. Floors above the "
                                 "ground floor and the ceilings are kept back from the walls by W (Walls page) "
                                 "so they drop in inside the frame - set W to Subframe's bar depth. Subframe "
                                 "puts the tabs (or a ledge) under each one, on the face of its frame." if st_on else
                                 "To use this page, pick 'Each storey set on the Storeys page' in Floors "
                                 "(Floors page).")
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
        if fsy == 'storeys':
            if self.preview.pieces:
                pcs_ = self.preview.pieces
                nfl = sum(1 for pc in pcs_ if pc.name.endswith(" - Floor panel"))
                nce = sum(1 for pc in pcs_ if pc.name.endswith(" - Ceiling"))
                self.lbl_storeys.setText("%d floor%s and %d ceiling%s, each its own piece. Frame it with "
                                         "Subframe: it puts the tabs (or a ledge) under them." % (
                                             nfl, "s" if nfl != 1 else "", nce, "s" if nce != 1 else ""))
                self.lbl_storeys.setStyleSheet("color: gray;")
            else:
                self.lbl_storeys.setText(self.preview.msg)
                self.lbl_storeys.setStyleSheet("color: #b35900;")
        else:
            self.lbl_storeys.setText("")
        rn = nt.get('roof') if nt else None
        if nt:
            H_ = nt['H']
            top_ = max([pc.z1 for pc in self.preview.pieces] + [H_])
            base_ = 0.0
            if v['base']:
                # 0 = worked out, as the build does: the floor thickness, or else the wall thickness
                base_ = v['base_t'] if v['base_t'] > 0 else float(v.get('floor_t') or v.get('wall_t') or 0.0)
            txt_h = "<b>Height:</b> walls %.0f mm" % H_
            if rn:
                txt_h += "; with the roof %.0f mm (to the ridge)" % top_
            elif top_ > H_ + 1e-6:
                txt_h += "; with the gables %.0f mm" % top_
            else:
                txt_h += " (no roof)"
            if base_ > 0:
                txt_h += " - plus the %.0f mm base plate under it (%.0f mm in all)" % (base_, top_ + base_)
            txt_h += "."
        else:
            txt_h = "<b>Height:</b> <span style='color:#b35900'>%s</span>" % (self.preview.msg or "not worked out yet")
        self.lbl_height.setText(txt_h)
        self.lbl_height2.setText(txt_h)
        if hasattr(self, 'start'):
            self.refresh_basics()
        if not r_on:
            self.lbl_roof.setText("No roof - tick 'Pitched roof on top' to put one on.")
            self.lbl_roof.setStyleSheet("color: gray;")
        elif not rn:
            self.lbl_roof.setText(self.preview.msg)
            self.lbl_roof.setStyleSheet("color: #b35900;")
        else:
            txt = "%d slope%s at %s°, the top %.0f mm above the walls." % (
                rn['slopes'], "s" if rn['slopes'] != 1 else "", " and ".join("%g" % a_ for a_ in rn['pitches']),
                rn['rise'])
            if v['roof_fill'] and rn['fills']:
                txt += " %d gable end%s / raised wall%s built up under it%s." % (
                    rn['fills'], "s" if rn['fills'] != 1 else "", "s" if rn['fills'] != 1 else "",
                    ", each joined to its wall" if v['gable_join'] and rn['fills'] else "")
            txt += " Each slope is its own piece - frame it with Subframe, cover it with Roof Tiles."
            self.lbl_roof.setText(txt)
            self.lbl_roof.setStyleSheet("color: gray;")
        if r_on:
            self.lbl_gables.setText("The roof makes its own gable ends (Roof page) - 'Join each gable to its wall' "
                                    "still works for them.")
            self.lbl_gables.setStyleSheet("color: gray;")
        elif not v['gables']:
            self.lbl_gables.setText("No gables - tick 'Gable ends' to put them on.")
            self.lbl_gables.setStyleSheet("color: gray;")
        elif not nt:
            self.lbl_gables.setText(self.preview.msg)
            self.lbl_gables.setStyleSheet("color: #b35900;")
        elif not nt.get('gables'):
            self.lbl_gables.setText("None of the walls picked get a gable - try another choice in 'Gables on'.")
            self.lbl_gables.setStyleSheet("color: #b35900;")
        else:
            lines = ["%s: ridge %.0f mm above the walls, %.1f°" % (nt['wall_names'][i], r, a)
                     for i, r, a in nt['gables']]
            extra = (" They stand on the top plate." if v['top'] and v['top_mode'] != 'inside' else
                     " Each is joined to the wall below it - one piece." if v['gable_join'] else "")
            self.lbl_gables.setText("Gables on:\n" + "\n".join(lines) + "\n" + extra.strip())
            self.lbl_gables.setStyleSheet("color: gray;")
        if nt:
            self.lbl_walls.setText("%d wall sections a floor, %.2f m round the outside. Inside each floor: "
                                   "%.1f m²." % (nt['walls'], nt['wall_len'], nt['inner_area']))
        else:
            self.lbl_walls.setText(self.preview.msg)

    def storey_values(self):
        """The Storeys page, as a list of rows (one per storey)."""
        out = []
        for k, (cf, cc, _lab) in enumerate(self.st_rows):
            out.append(dict(floor=cf.isChecked(), ceiling=cc.isChecked()))
        # storeys not shown just now (fewer floors) keep what they had
        return out + [dict(r_) for r_ in self._st_data[len(out):]]

    def build_storey_rows(self, n):
        """A row on the Storeys page for each storey: Floor [ ] rests on [..]   Ceiling [ ] rests on [..]."""
        if len(self.st_rows) == n:
            return
        keep = self.storey_values() if self.st_rows else list(self._st_data)
        for w_ in self.st_rows:
            for x_ in w_:
                try:
                    x_.setParent(None)
                    x_.deleteLater()
                except Exception:
                    pass
        self.st_rows = []
        rows = storey_rows(keep, n)
        if not self.st_grid.count():
            for c_, txt in ((1, "Floor"), (2, "Ceiling")):
                self.st_grid.addWidget(QLabel("<b>%s</b>" % txt), 0, c_)
        for k in range(n):
            lab = QLabel(storey_name(k))
            cf = QCheckBox()
            cf.setChecked(rows[k]['floor'])
            cc = QCheckBox()
            cc.setChecked(rows[k]['ceiling'])
            for c_, w_ in enumerate((lab, cf, cc)):
                self.st_grid.addWidget(w_, k + 1, c_)
            cf.setToolTip("A floor panel for the %s. The ground floor's stands on the base (the frame stands "
                          "on it); the others drop in inside the walls, kept back by W for a subframe, onto "
                          "Subframe's tabs." % storey_name(k).lower())
            cc.setToolTip("A ceiling panel at the top of the %s, under the room for the next floor's tabs (or "
                          "under the roof, on the top storey). Subframe's tabs hold it up." % storey_name(k).lower())
            for c_ in (cf, cc):
                c_.toggled.connect(self.changed)
            self.st_rows.append((cf, cc, lab))

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


# ---------------------------------------------------------------------------
# Show floors: a little window to hide and show the walls and the floors of each storey
# ---------------------------------------------------------------------------
FLOOR_WORDS = ("Floor slab", "Floor panel", "Ledge", "Ceiling", " tab ", " ledge ")


def _storey_of(name):
    """('Ground floor', 'Wall 1 (front)') for one of our pieces, (label, None) for a holder."""
    nm = str(name or '')
    labels = [storey_name(k) for k in range(len(STOREY_NAMES))]
    if nm.startswith("Floor ") and nm[6:].split(" ")[0].isdigit():
        labels.append("Floor " + nm[6:].split(" ")[0])
    labels.append("Walls")
    for sn in labels:
        if nm.startswith(sn + " - "):
            return sn, nm[len(sn) + 3:]
        if nm == sn or nm.startswith(sn + " ("):
            return sn, None
    return None, None


def _is_hidden(e):
    a = getattr(e, 'attrs', None)
    if isinstance(a, dict) and getattr(e, 'children', None) is None and getattr(e, 'mesh', None) is None:
        return bool(a.get('hidden'))                # a face
    return bool(getattr(e, 'hidden', False))


def _plate_faces(g):
    """The joined top plate's own faces (not the walls under it)."""
    faces = _items(getattr(getattr(g, 'mesh', None), 'faces', None))
    zs_ = {}
    pts_of = []
    for f_ in faces:
        ps = [q for q in (_pos(v) for v in _items(getattr(f_, 'vertices', None))) if q is not None]
        pts_of.append(ps)
        for q in ps:
            zs_[round(q[2], 7)] = q[2]
    levels = sorted(zs_.values())
    if len(levels) < 3:
        return []
    z0 = levels[-2]                                 # the plate's underside (the top is levels[-1])
    return [f_ for f_, ps in zip(faces, pts_of) if ps and min(q[2] for q in ps) >= z0 - 1e-7]


def floor_groups(scene):
    """{label: {'walls': [...], 'floor': [...]}} for every storey (and the plates) in the model,
    and every holder group of ours (so 'Show all' can bring back anything hidden the old way)."""
    rows, holders = {}, []

    def row(lab):
        return rows.setdefault(lab, {'walls': [], 'floor': []})

    def walk(e, depth):
        nm = str(getattr(e, 'name', '') or '')
        if nm.startswith("Top plate with walls"):
            holders.append(e)
            kids = _items(getattr(e, 'children', None))
            if not kids:                             # built by 1.5 to 1.7: one mesh, hide its plate faces
                row("Top plate")['floor'].extend(_plate_faces(e) or [e])
                return
            for c in kids:
                walk(c, depth + 1)
            return
        if nm.startswith("Top plate"):
            row("Top plate")['floor'].append(e)
            return
        if nm.startswith("Base plate"):
            row("Base plate")['floor'].append(e)
            return
        if nm.startswith(("Roof slope", "Tiled - Roof slope")):
            # (3D Roof Tiles puts a roof slope and its tiles in one group: they hide together)
            row("Roof")['floor'].append(e)
            return
        if nm.startswith("Roof ("):
            holders.append(e)
            for c in _items(getattr(e, 'children', None)):
                walk(c, depth + 1)
            return
        lab, piece = _storey_of(nm)
        if lab and piece:
            row("Walls (full height)" if lab == "Walls" else lab)[
                'floor' if any(w in piece for w in FLOOR_WORDS) else 'walls'].append(e)
            return
        if lab or nm == "Floor plan":
            holders.append(e)
        if depth < 8:
            for c in _items(getattr(e, 'children', None)):
                walk(c, depth + 1)
    for g in _items(getattr(scene, 'groups', None)):
        walk(g, 0)
    return rows, holders


def _floor_order(lab):
    if lab == "Base plate":
        return -1
    if lab == "Top plate":
        return 999
    if lab == "Roof":
        return 1000
    if lab == "Walls (full height)":
        return 500
    for k in range(50):
        if lab == storey_name(k):
            return k
    return 600


def set_hidden(viewport, ents, hidden):
    """Hides (or shows) groups or faces the way IngeTrazo's own Edit > Hide does (it can be undone)."""
    ents = [e for e in ents if _is_hidden(e) != bool(hidden)]
    if not ents:
        return
    try:
        from core.history import HideCommand
        viewport.history.execute(HideCommand(ents, bool(hidden)))
    except Exception as e:
        print("%s: hide by hand (%s)" % (PLUGIN_NAME, e))
        for x in ents:
            try:
                a = getattr(x, 'attrs', None)
                if isinstance(a, dict) and getattr(x, 'mesh', None) is None:
                    if hidden:
                        a['hidden'] = True
                    else:
                        a.pop('hidden', None)
                else:
                    x.hidden = bool(hidden)
            except Exception:
                pass
        try:
            viewport.scene._dirty_group_chunks = True
        except Exception:
            pass
        try:
            viewport.scene.version += 1
        except Exception:
            pass
    try:
        viewport.notify_scene_changed()
    except Exception:
        pass
    try:
        viewport.update()
    except Exception:
        pass


class FloorsWindow(QDialog):
    """For each storey a tick for its walls and one for its floor; the plates on their own. Untick to
    hide. Close it with the X - it opens where you left it."""
    def __init__(self, viewport, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QGridLayout
        self.setWindowTitle("Show floors  (Floor Plan %s)" % VERSION)
        self.setModal(False)
        try:
            # a floating tool window: it stays over the model while you click and work there
            from PySide6.QtCore import Qt as _Qt
            self.setWindowFlags(_Qt.Tool | _Qt.WindowTitleHint | _Qt.WindowCloseButtonHint)
            self.setAttribute(_Qt.WA_ShowWithoutActivating, False)
        except Exception:
            pass
        self.viewport = viewport
        self.checks = {}
        self._labels = None
        self._ver = None
        lay = QVBoxLayout(self)
        self.lbl = QLabel()
        self.lbl.setWordWrap(True)
        lay.addWidget(self.lbl)
        self.grid_w = QWidget()
        self.grid = QGridLayout(self.grid_w)
        self.grid.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.grid_w)
        row = QHBoxLayout()
        b_all = QPushButton("Show all")
        b_all.setToolTip("Shows every wall, floor and plate again.")
        b_all.clicked.connect(self.show_all)
        b_fl = QPushButton("Hide floors && plates")
        b_fl.setToolTip("Hides every floor slab, floor panel and plate (and the roof) but keeps all the "
                        "walls - the inside walls too - so you can see every room from above.")
        b_fl.clicked.connect(self.hide_floors)
        row.addWidget(b_all)
        row.addWidget(b_fl)
        lay.addLayout(row)
        self.refresh()
        try:
            from PySide6.QtCore import QTimer
            self._timer = QTimer(self)
            self._timer.timeout.connect(self.watch)
            self._timer.start(1000)                 # keeps up with undo, new builds and deleting
        except Exception:
            pass

    def scene(self):
        return getattr(self.viewport, 'scene', None)

    def watch(self):
        v = getattr(self.scene(), 'version', None)
        if v != self._ver:
            self.refresh()

    def refresh(self):
        sc = self.scene()
        self._ver = getattr(sc, 'version', None)
        rows, _h = floor_groups(sc) if sc is not None else ({}, [])
        labels = sorted(rows, key=_floor_order)
        shape = [(l_, bool(rows[l_]['walls']), bool(rows[l_]['floor'])) for l_ in labels]
        if shape != self._labels:
            self._labels = shape
            while self.grid.count():
                it = self.grid.takeAt(0)
                w = it.widget()
                if w is not None:
                    w.deleteLater()
            self.checks = {}
            from PySide6.QtCore import Qt as _Qt
            mid = _Qt.AlignHCenter | _Qt.AlignVCenter
            self.grid.setColumnMinimumWidth(1, 70)
            self.grid.setColumnMinimumWidth(2, 90)
            if labels:
                for c_, txt in ((1, "Walls"), (2, "Floor / plate")):
                    h = QLabel("<b>%s</b>" % txt)
                    h.setAlignment(mid)
                    self.grid.addWidget(h, 0, c_, mid)
            for r, (lab, has_w, has_f) in enumerate(shape, start=1):
                self.grid.addWidget(QLabel(lab), r, 0, _Qt.AlignLeft | _Qt.AlignVCenter)
                for c_, part, has in ((1, 'walls', has_w), (2, 'floor', has_f)):
                    if not has:
                        continue
                    cb = QCheckBox()
                    cb.setToolTip("Untick to hide the %s %s." % (lab.lower(), "walls" if part == 'walls' else
                                  ("floor" if lab not in ("Top plate", "Base plate", "Roof") else "")))
                    cb.toggled.connect(lambda on, l_=lab, p_=part: self.toggle(l_, p_, on))
                    self.grid.addWidget(cb, r, c_, mid)
                    self.checks[(lab, part)] = cb
        for (lab, part), cb in self.checks.items():
            ents = rows.get(lab, {}).get(part, [])
            cb.blockSignals(True)
            cb.setChecked(not (ents and all(_is_hidden(e) for e in ents)))
            cb.blockSignals(False)
        self.lbl.setText("Untick to hide. To see into the rooms, hide the floors and plates - the walls "
                         "(inside walls too) stay." if labels else
                         "No floor plan in the model yet - build one and its floors show up here.")
        try:
            self.adjustSize()
        except Exception:
            pass

    def toggle(self, lab, part, on):
        sc = self.scene()
        if sc is None:
            return
        rows, _h = floor_groups(sc)
        set_hidden(self.viewport, rows.get(lab, {}).get(part, []), not on)
        self._ver = None

    def show_all(self):
        sc = self.scene()
        if sc is None:
            return
        rows, holders = floor_groups(sc)
        set_hidden(self.viewport, holders + [e for r in rows.values() for e in r['walls'] + r['floor']], False)
        self.refresh()

    def hide_floors(self):
        sc = self.scene()
        if sc is None:
            return
        rows, holders = floor_groups(sc)
        set_hidden(self.viewport, [e for r in rows.values() for e in r['floor']], True)
        set_hidden(self.viewport, holders + [e for r in rows.values() for e in r['walls']], False)
        self.refresh()


def _show_hide_hub():
    """3D Show / Hide (the one small window with a tab for each kind of thing), if it's loaded."""
    import sys
    for name, mod in list(sys.modules.items()):
        if mod is not None and (name == "ed3d_show_hide" or name.endswith("_ed3d_show_hide")) \
                and hasattr(mod, 'open_show_hide'):
            return mod
    return None


def open_floors_window(viewport, parent=None):
    h = _show_hide_hub()
    if h is not None:
        try:
            return h.open_show_hide(viewport, 'floors')     # the shared Show / hide window
        except Exception as e:
            print("%s: Show / Hide window didn't open (%s)" % (PLUGIN_NAME, e))
    w = getattr(FloorPlanTool, '_floors', None)
    try:
        if w is not None and w.isVisible():
            w.viewport = viewport
            w.refresh()
            w.raise_()
            w.activateWindow()
            return w
    except Exception:
        pass
    # it belongs to IngeTrazo's main window (not the Floor Plan window), so it stays on top of the
    # model when you click there, and stays open when the Floor Plan window is closed
    main = None
    try:
        main = viewport.window()
    except Exception:
        main = None
    w = FloorsWindow(viewport, main or parent)
    FloorPlanTool._floors = w
    eddy_window(w, PLUGIN_NAME + " - Show floors", {}, place=True)   # opens where you left it
    w.show()
    return w


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
                  "base and top plates, gable ends and a pitched roof - every piece its own group, ready to print."

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
        for kind, word in (('roof', "roof slopes"), ('gable', "gable pieces"), ('slab', "floor slabs"), ('floor', "drop-in floor panels"), ('ledge', "ledges"),
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
            def mesh_of(solid):
                so = solid.mapped(to_world)
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
                stats['faces'] += made
                return mesh, made

            for pc in pieces:
                if pc.parts:
                    kids = []
                    for nm_, sol_ in pc.parts:
                        m_, n_ = mesh_of(sol_)
                        if n_:
                            k_ = make_group(Group, m_, nm_)
                            k_.component = False
                            kids.append(k_)
                    g = holder(Group, pc.name, kids) if kids else None
                    if g is None:
                        continue
                else:
                    mesh, made = mesh_of(pc.solid())
                    if not made:
                        continue
                    g = make_group(Group, mesh, pc.name)
                g.component = False
                if pc.kind in ('base', 'top'):
                    key = (2, 0)                    # the plates sit in 'Floor plan' itself
                elif pc.kind == 'roof':
                    key = (3, 0)                    # the roof slopes: a 'Roof' group of their own
                elif pc.kind in ('wall', 'gable') and pc.name.startswith("Walls"):
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
                    nm = "%s (%d pieces)" % ("Walls" if k[0] == 0 else "Roof" if k[0] == 3 else storey_name(k[1]),
                                             len(gs))
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
