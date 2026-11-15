# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Subframe for IngeTrazo
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
3D Subframe - a strengthening frame behind the walls and under the roof, for IngeTrazo
Build the walls (with their window and door openings) and the roof first, then:

  Suggest a frame   Select the building (or just some walls / roof faces) and the frame is
                    worked out for you: plates top and bottom, corner posts, posts, lintels
                    and sills round every opening, studs at a spacing you set, rails, and
                    diagonal braces. Sloping roofs get an eaves plate, ridge, hip and verge
                    rafters, rafters and purlins - on any shape of roof, as it follows the faces.
  Along lines       Draw lines where you want frame bars (IngeTrazo's line tool, snapping to
                    the walls), select them and the bar follows them, with
                    mitred corners.

The frame goes on the inside of the building on its own (or on the side you choose), stops
short at inside corners so walls meeting don't overlap, and every bar is its own group, so
Scale Studio's Pieces page can lay each one flat on the print bed.

Floors (Floors page): type the height of each floor - as many as you like - and a ledge goes
round the inside of the walls under each one, standing out past the frame, for a floor to drop
in and rest on. Tick 'Make the floor panels too' and the floors are cut to fit as well.

Sizes are real-world mm, like the other plugins - Scale Studio takes it down to your
model scale. The presets give the sizes for a 4 mm printed frame in OO and so on. Ctrl+Alt+Y.
"""

import os
import json
import math
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox, QCheckBox,
    QPushButton, QLabel, QMessageBox, QWidget, QInputDialog, QSpinBox, QTabWidget
)

PLUGIN_NAME = "3D Subframe"
VERSION = "1.34"


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


SCALE = 0.001                 # IngeTrazo stores metres; the frame is worked out in real-world mm
PRESET_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Subframe")
Z = (0.0, 0.0, 1.0)
SIDES = [("Inside the building (works it out)", 'auto'),
         ("Front - of a picked face; the outside of a picked wall group", 'front'),
         ("Back - of a picked face; the inside of a picked wall group", 'back')]
GLAZE_MODES = [("In place, with their walls", 'wall'), ("In place, in their own group", 'own'),
               ("Laid out flat beside the building, in their own group", 'flat')]
TRUSS_STYLES = [("King post and struts", 'struts'), ("King post", 'king'), ("Plain (rafters and tie)", 'plain')]
LINE_POS = [("Centre of the bar", 'centre'), ("Edge - bar inside the shape you drew", 'left'),
            ("Edge - bar outside the shape you drew (round an opening)", 'right')]

# sizes are real-world mm (IngeTrazo stores metres); counts as they are
DEFAULTS = dict(
    width=0.0, depth=0.0, spacing=0.0, rafter_spacing=0.0, lintel=0.0, rails=0, purlins=0,
    rebate=0.0, glaze_w=0.0, glaze_t=0.0, glaze_setin=0.0, glaze_inset=0.0, glaze_one=False, min_piece=0.0,
    trusses=False, truss_spacing=0.0, truss_style='struts', truss_overhang=0.0, glaze_mode='wall', gap=0.0, lift=0.0,
    walls=True, roofs=True, flats=False, perimeter=True, openings=True, studs=True, braces=True,
    corners=True, side='auto', line_pos='centre',
    floor_levels='', floor_t=0.0, ledge_h=0.0, ledge_out=0.0, floor_fit=0.0, floor_panels=False,
    boards=False, fascia_h=0.0, board_t=0.0, board_off=0.0, barge_w=0.0, finial_h=0.0, finial_drop=0.0,
    finial_w=0.0, soffits=False, roof_panels=False, roof_t=0.0, roof_over=0.0)
SIZE_KEYS = ('width', 'depth', 'spacing', 'rafter_spacing', 'lintel', 'rebate', 'glaze_w', 'glaze_t', 'glaze_setin',
             'glaze_inset',
             'min_piece', 'gap', 'lift', 'truss_spacing', 'truss_overhang',
             'floor_t', 'ledge_h', 'ledge_out', 'floor_fit',
             'fascia_h', 'board_t', 'board_off', 'barge_w', 'finial_h', 'finial_drop', 'finial_w',
             'roof_t', 'roof_over')

# ready-made sizes for a printed frame (real-world mm: / the scale = printed mm)
BUILTIN_PRESETS = {
    "OO 1:76.2 print - 4 mm bars": dict(
        width=305.0, depth=305.0, spacing=2300.0, rafter_spacing=2300.0, lintel=305.0, rails=0, purlins=1, rebate=150.0, glaze_t=76.0, glaze_inset=15.0, glaze_w=100.0, glaze_setin=30.0),
    "OO 1:76.2 print - light 3 mm bars": dict(
        width=230.0, depth=230.0, spacing=3000.0, rafter_spacing=3000.0, lintel=230.0, rails=0, purlins=1, rebate=150.0, glaze_t=76.0, glaze_inset=15.0, glaze_w=100.0, glaze_setin=30.0),
    "1:80 print - 4 mm bars": dict(
        width=320.0, depth=320.0, spacing=2400.0, rafter_spacing=2400.0, lintel=320.0, rails=0, purlins=1, rebate=160.0, glaze_t=80.0, glaze_inset=16.0, glaze_w=105.0, glaze_setin=32.0),
    "N 1:148 print - 2 mm bars": dict(
        width=296.0, depth=296.0, spacing=2700.0, rafter_spacing=2700.0, lintel=296.0, rails=0, purlins=1, rebate=150.0, glaze_t=111.0, glaze_inset=30.0, glaze_w=90.0, glaze_setin=30.0),
    "O 1:43.5 print - 6 mm bars": dict(
        width=261.0, depth=261.0, spacing=1950.0, rafter_spacing=1950.0, lintel=261.0, rails=1, purlins=1, rebate=130.0, glaze_t=65.0, glaze_inset=9.0, glaze_w=90.0, glaze_setin=25.0),
    "Real timber - 100 x 50 studs at 600": dict(
        width=50.0, depth=100.0, spacing=600.0, rafter_spacing=600.0, lintel=150.0, rails=1, purlins=1, rebate=0.0, glaze_t=0.0, glaze_inset=0.0, glaze_w=0.0, glaze_setin=0.0),
}

# what each kind of bar is called, on walls and on roofs
NAMES = {
    'wall': {'bottom': "Bottom plate", 'top': "Top plate", 'rake': "Gable rail", 'end': "End post",
             'jamb': "Post", 'lintel': "Lintel", 'sill': "Sill", 'stud': "Stud", 'rail': "Rail",
             'brace': "Brace"},
    'roof': {'bottom': "Eaves plate", 'top': "Ridge board", 'rake': "Hip rafter", 'end': "Verge rafter",
             'jamb': "Trimmer", 'lintel': "Trimmer top", 'sill': "Trimmer bottom", 'stud': "Rafter",
             'rail': "Purlin", 'brace': "Wind brace"},
    'flat': {'bottom': "Edge joist", 'top': "Edge joist", 'rake': "Edge joist", 'end': "Edge joist",
             'jamb': "Trimmer", 'lintel': "Trimmer", 'sill': "Trimmer", 'stud': "Joist",
             'rail': "Noggin", 'brace': "Brace"},
}
COLOURS = {'bottom': (150, 104, 64), 'top': (150, 104, 64), 'rake': (165, 112, 66),
           'end': (120, 82, 50), 'glaze': (165, 200, 230), 'jamb': (200, 120, 40), 'lintel': (215, 150, 50),
           'sill': (215, 150, 50), 'stud': (190, 160, 110), 'rail': (170, 140, 95),
           'brace': (120, 140, 90), 'line': (190, 160, 110), 'truss': (165, 112, 66),
           'ledge': (110, 85, 60), 'floor': (205, 185, 150), 'fascia': (235, 235, 228),
           'barge': (235, 235, 228), 'finial': (235, 235, 228), 'soffit': (235, 235, 228),
           'roof': (120, 120, 125)}


def frame_params(v):
    """The window's values, ready to build with (real-world mm)."""
    p = dict(DEFAULTS)
    p.update(v)
    for key in SIZE_KEYS:
        p[key] = float(p[key])
    p['w'] = p['width']
    if p['w'] <= 0 or p['depth'] <= 0:
        raise ValueError("Set the bar width and bar depth first (Sizes page).")
    p['lintel'] = max(p['w'], p['lintel'])
    # floors: a ledge round the inside of the walls under each floor level
    p['_levels'] = parse_levels(p.get('floor_levels', ''))
    p['ledge_h'] = max(p['ledge_h'] if p['ledge_h'] > 0 else p['w'], 0.6 * p['w'])
    p['ledge_out'] = p['ledge_out'] if p['ledge_out'] > 0 else p['w']
    return p


def parse_levels(text):
    """'150, 2850' -> [150.0, 2850.0]: the top of each floor, mm above the bottom of the walls."""
    if isinstance(text, (list, tuple)):
        items = list(text)
    else:
        items = str(text or '').replace(';', ',').replace(' ', ',').split(',')
    out = []
    for it in items:
        it = str(it).strip().lower().replace('mm', '')
        if not it:
            continue
        try:
            out.append(float(it))
        except ValueError:
            raise ValueError("Floor levels: '%s' isn't a number. Type the heights with commas "
                             "between them, like 150, 2850." % it)
    return sorted(set(round(x, 3) for x in out if x >= 0))


def ledge_bands(p):
    """[(ledge bottom, ledge top, name, floor top)] in mm above the bottom of the walls."""
    out = []
    for k, lv in enumerate(p.get('_levels', [])):
        top = lv - p.get('floor_t', 0.0)
        out.append((top - p['ledge_h'], top, "Floor %d ledge" % (k + 1), lv))
    return out


# ---------------------------------------------------------------------------
# Small geometry helpers (x along the face, y up it, z out of it; mm)
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
        # in a straight line (allowing for rounding on long edges): the middle point goes
        tol_ = 1e-9 * max(1.0, math.hypot(b[0] - a[0], b[1] - a[1]) * math.hypot(c[0] - a[0], c[1] - a[1]))
        if abs(cr) < tol_ and (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1]) >= 0:
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




def merged_slab(polys, zbot, ztop, cuts=()):
    """One closed solid over several pieces of a region that touch along their edges
    (as cutting round openings leaves them), so a board cut into convex pieces is still
    one solid with no faces inside it. The pieces are cut into strips at `cuts` (where a
    rounded top changes slope); within a strip both surfaces must be flat."""
    strips = []
    cs = sorted(cuts)
    for pc in polys:
        pc = clean(pc)
        if pc is None:
            continue
        x0, x1, _, _ = bbox(pc)
        inner = [c for c in cs if x0 + 1e-7 < c < x1 - 1e-7]
        edges = [None] + inner + [None]
        for a, b in zip(edges[:-1], edges[1:]):
            q = list(pc)
            if a is not None:
                q = clip_half(q, 1, 0, -a)
            if b is not None and len(q) >= 3:
                q = clip_half(q, -1, 0, b)
            q = clean(q) if len(q) >= 3 else None
            if q:
                strips.append(q)
    if not strips:
        return None
    # snap corners that are the same point, then split edges where another piece's corner
    # lies on them, so neighbouring pieces share whole edges
    tol = 0.002
    keys = {}

    def snap(p):
        k = (round(p[0] / tol), round(p[1] / tol))
        for dx in (0, -1, 1):
            for dy in (0, -1, 1):
                q = keys.get((k[0] + dx, k[1] + dy))
                if q is not None and abs(q[0] - p[0]) <= tol and abs(q[1] - p[1]) <= tol:
                    return q
        keys[k] = (float(p[0]), float(p[1]))
        return keys[k]

    def dedupe(st):
        out = []
        for p in st:
            if not out or p != out[-1]:
                out.append(p)
        while len(out) > 1 and out[0] == out[-1]:
            out.pop()
        return out if len(out) >= 3 and abs(area2(out)) > 1e-6 else None
    strips = [q for q in (dedupe([snap(p) for p in st]) for st in strips) if q]
    def tfix(strips):
        allp = list(keys.values())
        fixed = []
        for st in strips:
            out = []
            n = len(st)
            for i in range(n):
                a, b = st[i], st[(i + 1) % n]
                out.append(a)
                dx, dy = b[0] - a[0], b[1] - a[1]
                L2 = dx * dx + dy * dy
                if L2 < 1e-12:
                    continue
                mids = []
                for p in allp:
                    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2
                    if 1e-9 < t < 1 - 1e-9:
                        cr = abs((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / math.sqrt(L2)
                        if cr < 2e-4:
                            mids.append((t, p))
                out += [p for _, p in sorted(mids)]
            fixed.append(out)
        return fixed
    # where the region only touches itself at a corner (a pinch - usually the tip of a jagged
    # hole), drop the smallest bit there, so every corner of the solid is a clean one
    for _ in range(60):
        fixed = tfix(strips)
        directed = {}
        clash = None
        for si, st in enumerate(fixed):
            for i in range(len(st)):
                e = (st[i], st[(i + 1) % len(st)])
                if e in directed and clash is None:
                    clash = [directed[e], si]          # two bits lying over each other
                directed[e] = si
        if clash:
            del strips[min(clash, key=lambda si: abs(area2(strips[si])))]
            if not strips:
                return None
            continue
        outgoing = {}
        for (a_, b_), si in directed.items():
            if (b_, a_) not in directed:
                outgoing.setdefault(a_, []).append(si)
        pinch = [sis for sis in outgoing.values() if len(sis) > 1]
        if not pinch:
            break
        drop = min(pinch[0], key=lambda si: abs(area2(strips[si])))
        del strips[drop]
        if not strips:
            return None
    directed = set()
    for st in fixed:
        for i in range(len(st)):
            directed.add((st[i], st[(i + 1) % len(st)]))
    s = PSolid()
    # top: one face per flat strip of the profile (so no stray edges between the pieces);
    # bottom: one face for the lot. Each may have holes (the jagged holes, round openings).
    import bisect
    whole, ok = region_loops(fixed)
    if not cs and ok:
        # flat both sides: take out the in-between points left along straight edges where the
        # pieces met, so every face is a clean shape. Left in, a long face along the top of a
        # rafter had points a hair off the line, and drew with a little notch in it.
        def corners_only(loop):
            runs = straight_runs(loop)
            out_ = [r[0] for r in runs] if len(runs) >= 3 else loop
            return out_ if len(out_) >= 3 and abs(area2(out_)) > 1e-6 else loop
        whole = [(corners_only(o), [corners_only(h) for h in hls]) for o, hls in whole]
        for outer, hls in whole:
            s.add([(x, y, ztop(x, y)) for x, y in outer], [[(x, y, ztop(x, y)) for x, y in h] for h in hls])
    else:
        groups = {}
        for st in fixed:
            cx = sum(p[0] for p in st) / len(st)
            groups.setdefault(bisect.bisect(cs, cx), []).append(st)
        for grp in groups.values():
            for outer, hls in region_loops(grp)[0]:
                s.add([(x, y, ztop(x, y)) for x, y in outer], [[(x, y, ztop(x, y)) for x, y in h] for h in hls])
    for outer, hls in whole:
        s.add([(x, y, zbot(x, y)) for x, y in reversed(outer)],
              [[(x, y, zbot(x, y)) for x, y in reversed(h)] for h in hls])
    if ok:
        # the sides: one face for each straight run of the outline
        for outer, hls in whole:
            for loop in [outer] + hls:
                for run in straight_runs(loop):
                    s.add([(x, y, zbot(x, y)) for x, y in run] +
                          [(x, y, ztop(x, y)) for x, y in reversed(run)])
    else:
        for st in fixed:
            for i in range(len(st)):
                a, b = st[i], st[(i + 1) % len(st)]
                if (b, a) in directed:
                    continue                      # an inside edge, shared with the next piece
                s.add([(a[0], a[1], zbot(*a)), (b[0], b[1], zbot(*b)),
                       (b[0], b[1], ztop(*b)), (a[0], a[1], ztop(*a))])
    return s.fix()


def straight_runs(loop):
    """A closed loop split into runs of points along one straight line each
    (every run includes both its end corners)."""
    n = len(loop)

    def turn(i):
        a, b, c = loop[i - 1], loop[i], loop[(i + 1) % n]
        ux, uy = b[0] - a[0], b[1] - a[1]
        vx, vy = c[0] - b[0], c[1] - b[1]
        lu, lv = math.hypot(ux, uy), math.hypot(vx, vy)
        if lu < 1e-12 or lv < 1e-12:
            return False
        return abs(ux * vy - uy * vx) / (lu * lv) > 1e-6 or ux * vx + uy * vy < 0
    corners = [i for i in range(n) if turn(i)]
    if not corners:
        return [[loop[i], loop[(i + 1) % n]] for i in range(n)]
    runs = []
    for k, c in enumerate(corners):
        e = corners[(k + 1) % len(corners)]
        run = [loop[c]]
        i = c
        while True:
            i = (i + 1) % n
            run.append(loop[i])
            if i == e:
                break
        runs.append(run)
    return runs


class PSolid(Solid):
    """A solid whose faces may have holes: holes[i] = loops cut out of faces[i]
    (wound the other way round)."""
    def __init__(self):
        Solid.__init__(self)
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
        s = PSolid()
        s.faces = [[fn(p) for p in f] for f in self.faces]
        s.holes = {i: [[fn(p) for p in h] for h in hs] for i, hs in self.holes.items()}
        for k in ('ridge', 'backing'):
            if hasattr(self, k):
                setattr(s, k, getattr(self, k))
        return s.fix()


def _pip(p, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ay > p[1]) != (by > p[1]):
            if p[0] < ax + (p[1] - ay) * (bx - ax) / (by - ay):
                inside = not inside
    return inside


def region_loops(polys):
    """The outline of a region made of pieces that share whole edges:
    [(outer loop, [hole loops])]. Outer loops run counter-clockwise, holes clockwise."""
    edges = set()
    for st in polys:
        for i in range(len(st)):
            edges.add((st[i], st[(i + 1) % len(st)]))
    nxt = {}
    for a, b in edges:
        if (b, a) not in edges:
            if a in nxt:
                return [(st, []) for st in polys], False      # touches itself: keep the pieces
            nxt[a] = b
    loops = []
    seen = set()
    for start in list(nxt):
        if start in seen:
            continue
        loop, p = [], start
        while p not in seen:
            seen.add(p)
            loop.append(p)
            p = nxt.get(p)
            if p is None:
                return [(st, []) for st in polys], False
        if p != start or len(loop) < 3:
            return [(st, []) for st in polys], False
        loops.append(loop)
    outers = [l for l in loops if area2(l) > 0]
    holes = [l for l in loops if area2(l) <= 0]
    out = [(o, []) for o in outers]
    for h in holes:
        # a point just inside the hole: the middle of its first edge, nudged in
        (ax, ay), (bx, by) = h[0], h[1]
        mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
        L = math.hypot(bx - ax, by - ay) or 1.0
        probe = (mx + (by - ay) / L * 1e-3, my - (bx - ax) / L * 1e-3)   # just inside the hole
        home = [k for k, (o, _) in enumerate(out) if _pip(probe, o)]
        if not home:
            return [(st, []) for st in polys], False
        # the smallest outer loop holding it
        k = min(home, key=lambda k: abs(area2(out[k][0])))
        out[k][1].append(h)
    return out, True


def convex_hull(pts):
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
    return clean(lo[:-1] + hi[:-1])


def grow(poly, d):
    """A convex (counter-clockwise) polygon pushed out by d on every side."""
    poly = clean(poly)
    if poly is None or d <= 0:
        return poly
    n = len(poly)
    lines = []
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        L = math.hypot(bx - ax, by - ay)
        nx, ny = (by - ay) / L, -(bx - ax) / L          # outward for counter-clockwise
        lines.append(((ax + nx * d, ay + ny * d), (bx - ax, by - ay)))
    out = []
    for i in range(n):
        (p, r), (q, s) = lines[i - 1], lines[i]
        den = r[0] * s[1] - r[1] * s[0]
        if abs(den) < 1e-12:
            out.append(q)
            continue
        t = ((q[0] - p[0]) * s[1] - (q[1] - p[1]) * s[0]) / den
        x, y = p[0] + t * r[0], p[1] + t * r[1]
        # don't let a sharp corner make a long spike: cap it at 3 d from the corner
        cx, cy = poly[i]
        k = math.hypot(x - cx, y - cy)
        if k > 3 * d:
            x, y = cx + (x - cx) * 3 * d / k, cy + (y - cy) * 3 * d / k
        out.append((x, y))
    return convex_hull(out)


def rot(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def overlaps(pa, pb):
    A, B = bbox(pa), bbox(pb)
    return not (A[1] <= B[0] or B[1] <= A[0] or A[3] <= B[2] or B[3] <= A[2])


def cut_away(pieces, blockers):
    for hp in blockers:
        nxt = []
        for pc in pieces:
            if overlaps(pc, hp):
                nxt.extend(subtract_convex(pc, hp))
            else:
                nxt.append(pc)
        pieces = nxt
    return pieces


def clip_to(poly, parts):
    out = []
    for pt in parts:
        if overlaps(poly, pt):
            pc = clip_convex(poly, pt)
            if pc:
                out.append(pc)
    return out


def _inside(p, conv):
    """Is point p inside the convex counter-clockwise polygon conv?"""
    n = len(conv)
    for i in range(n):
        (ax, ay), (bx, by) = conv[i], conv[(i + 1) % n]
        if (bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax) < 0:
            return False
    return True


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
            continue
        vs = getattr(e, 'vertices', None)
        if vs is not None and not callable(vs) and len(_items(vs)) >= 3:
            out.append(e)
    return out


def face_frame(face, flip=False, turn=0):
    """(to_world function, outline, holes) for a face: x along, y up the face (mm)."""
    pts = [p for p in (_pos(q) for q in _items(face.vertices)) if p is not None]
    if len(pts) < 3:
        raise ValueError("That face has no corners I can read.")
    n = _newell(pts)
    if flip:
        n = v_mul(n, -1.0)
    if abs(n[2]) < 0.999:
        U = v_norm(v_cross(Z, n))        # level, along the eaves
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


# ---------------------------------------------------------------------------
# Laying out the frame on one face (2D: x along, y up the face; drawing mm)
# ---------------------------------------------------------------------------
def _strip(a, b, w0, w1):
    """A bar along the line a->b, from w0 to w1 to its left (counter-clockwise)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    if L < 1e-9:
        return None
    nx, ny = -dy / L, dx / L
    return clean([(a[0] + nx * w0, a[1] + ny * w0), (b[0] + nx * w0, b[1] + ny * w0),
                  (b[0] + nx * w1, b[1] + ny * w1), (a[0] + nx * w1, a[1] + ny * w1)])


def _box(xa, ya, xb, yb):
    return clean([(xa, ya), (xb, ya), (xb, yb), (xa, yb)])


def _thick_enough(pc, w):
    a = abs(area2(pc))
    n = len(pc)
    L = max(math.hypot(pc[(i + 1) % n][0] - pc[i][0], pc[(i + 1) % n][1] - pc[i][1]) for i in range(n))
    return L > 1e-9 and a / L >= 0.3 * w and a >= 0.25 * w * w


def _axis(poly):
    """Which way a bar runs: along its longest side."""
    n = len(poly)
    a, b = max(((poly[i], poly[(i + 1) % n]) for i in range(n)),
               key=lambda e: math.hypot(e[1][0] - e[0][0], e[1][1] - e[0][1]))
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L)


def _square_bar(pcs, u, w):
    """Goes along a bar after it has been cut, measuring how wide it is. Where something has
    cut it down to a thin strip (less than half its width) that stretch is taken out, so the
    bar is cut square there instead of being left with a notch or a thin tongue. A slanted end
    (a stud under a gable rail) is kept."""
    if not pcs:
        return pcs
    S = lambda q: q[0] * u[0] + q[1] * u[1]
    T = lambda q: -q[0] * u[1] + q[1] * u[0]
    ss = sorted(set(S(q) for pc in pcs for q in pc))

    def width(s):
        tot = 0.0
        for pc in pcs:
            ts = []
            n = len(pc)
            for i in range(n):
                a, b = pc[i], pc[(i + 1) % n]
                sa, sb = S(a), S(b)
                if (sa - s) * (sb - s) <= 0 and abs(sb - sa) > 1e-12:
                    t = (s - sa) / (sb - sa)
                    ts.append(T(a) + (T(b) - T(a)) * t)
            if len(ts) >= 2:
                tot += max(ts) - min(ts)
        return tot
    keep = []
    cut = False
    for a, b in zip(ss, ss[1:]):
        if b - a < 1e-6:
            continue
        e = 1e-3 * (b - a)
        wa, wm, wb = width(a + e), width((a + b) / 2.0), width(b - e)
        if wm >= 0.5 * w or abs(wa - wb) > 0.1 * w:
            if keep and abs(keep[-1][1] - a) < 1e-6:
                keep[-1] = (keep[-1][0], b)
            else:
                keep.append((a, b))
        else:
            cut = True
    if not cut:
        return pcs
    out = []
    for sa, sb in keep:
        for pc in pcs:
            q = clip_half(list(pc), u[0], u[1], -sa)
            if len(q) >= 3:
                q = clip_half(q, -u[0], -u[1], sb)
            q = clean(q) if len(q) >= 3 else None
            if q and abs(area2(q)) > 1e-6 * w * w:
                out.append(q)
    return out


def _touching(pa, pb, tol):
    A, B = bbox(pa), bbox(pb)
    return not (A[1] < B[0] - tol or B[1] < A[0] - tol or A[3] < B[2] - tol or B[3] < A[2] - tol)


def _components(pcs, tol):
    """Bits of one bar that touch each other belong to one piece; bits apart (a stud cut in
    two by a window) are separate pieces."""
    n = len(pcs)
    par = list(range(n))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if _touching(pcs[i], pcs[j], tol):
                par[find(i)] = find(j)
    out = {}
    for i in range(n):
        out.setdefault(find(i), []).append(pcs[i])
    comps = list(out.values())
    comps.sort(key=lambda c: (min(q[1] for pc in c for q in pc), min(q[0] for pc in c for q in pc)))
    return comps


def lay_frame(outline, holes, p, kind='wall', extra=(), ledges=(), ledge_extra=()):
    """The frame for one face: [(name, type, [convex bits of one piece])].
    Placed in order - floor ledges, plates, posts, openings, studs, braces, rails - and each bar
    is cut back by the ones already there, so no two pieces overlap.
    ledges: [(y bottom, y top, name)] in the face's terms - a level ledge right across the wall for
    a floor to rest on (it stands out further than the frame: see solids_for). ledge_extra: what
    other walls' frames and ledges already take up at the ledge's depth."""
    w = p['w']
    gap = max(0.0, p.get('gap', 0.0))
    names = NAMES.get(kind, NAMES['wall'])
    parts = convex_parts(outline)
    if not parts:
        return []
    x0, x1, y0, y1 = bbox(outline)
    if min(x1 - x0, y1 - y0) < 2.2 * w:
        raise ValueError("the face is too small for a frame that size")
    sb = max(0.0, p.get('rebate', 0.0)) if p.get('openings', True) else 0.0
    # ---- the openings, squared off: every window (a hole in the face) and every doorway cut up
    # into the bottom edge is framed as the rectangle round it, whatever its shape (round, arched)
    opens = []                 # (xa, ya, xb, yb, 'window' or 'door', hole outline or None)
    for hl in holes:
        hh = convex_hull(hl)
        if hh:
            bx = bbox(hh)
            opens.append((bx[0], bx[2], bx[1], bx[3], 'window', hh))
    n_ = len(outline)
    tol_ = 1e-3 * w + 1e-6
    on_bottom = [abs(q[1] - y0) < tol_ for q in outline]
    door_edges = set()
    if any(on_bottom):
        st = on_bottom.index(True)
        i = st
        while True:
            j = (i + 1) % n_
            run = [i]
            while not on_bottom[j]:
                run.append(j)
                j = (j + 1) % n_
            if len(run) > 1 and outline[j][0] > outline[i][0] + tol_:
                # up off the bottom and back down further along: a doorway
                pts = [outline[k] for k in run[1:]]
                xs = [q[0] for q in pts] + [outline[i][0], outline[j][0]]
                opens.append((min(xs), y0, max(xs), max(q[1] for q in pts), 'door', None))
                for k in run:
                    door_edges.add(k)
            i = j
            if i == st:
                break
    # room left clear round each opening, so a glazing frame can sit in behind it - but never into
    # the end post: an opening near the end of a wall (closer than about 650 mm) would otherwise cut
    # the end post away, leaving the corner of the frame loose. There the room on that side is
    # trimmed back to the end post, and the opening shares it as its post.
    def ends_at(ya_, yb_):
        st = clip_half(clip_half(list(outline), 0.0, 1.0, -ya_), 0.0, -1.0, yb_)
        st = clean(st) if len(st) >= 3 else None
        return (bbox(st)[0], bbox(st)[1]) if st else (x0, x1)
    hulls = []
    room = []                  # (left limit, right limit) of the clear room round each opening
    for xa, ya, xb, yb, kind_, _h in opens:
        hy0 = (ya - sb) if kind_ == 'window' else (y0 - w - 1.0)
        el, er = ends_at(max(y0, hy0), min(y1, yb + sb))
        L_, R_ = xa - sb, xb + sb
        # room a glazing frame needs beside the window, if this one gets one
        gneed = 0.0
        if kind_ == 'window' and p.get('glaze_t', 0.0) > 0 and p.get('glaze_w', 0.0) > 0:
            si_, fit_ = max(0.0, p.get('glaze_setin', 0.0)), max(0.0, p.get('glaze_inset', 0.0))
            gneed = si_ + fit_ + 0.25 * max(0.0, min(p['glaze_w'], sb - fit_ - si_))
        if kind == 'wall' and p.get('perimeter', True):
            if xa - el >= w + gneed - 1e-6 and L_ < el + w:
                L_ = el + w
                p['_end_post_kept'] = p.get('_end_post_kept', 0) + 1
            elif el - 1e-6 < L_ < el + w:
                # too close for an end post beside it: the room runs right to the end, so no thin
                # sliver of post is left there (that got dropped, leaving the plates and brace
                # sticking out past the end with nothing holding them)
                L_ = el - 1.0
                p['_end_open'] = p.get('_end_open', 0) + 1
            if er - xb >= w + gneed - 1e-6 and R_ > er - w:
                R_ = er - w
                p['_end_post_kept'] = p.get('_end_post_kept', 0) + 1
            elif er - w < R_ < er + 1e-6:
                R_ = er + 1.0
                p['_end_open'] = p.get('_end_open', 0) + 1
        hulls.append(_box(L_, hy0, R_, yb + sb))
        room.append((L_, R_, el, er))
    placed = [b for b in extra if b]      # bars from faces already framed, seen in this face's terms
    bars = []
    uprights = []              # x ranges of posts already there, so studs keep clear of them

    minp_ = max(0.0, p.get('min_piece', 0.0))

    def put(poly, name, typ):
        if not poly:
            return []
        pcs = clip_to(poly, parts)
        pcs = cut_away(pcs, hulls + placed)
        pcs = [pc for pc in pcs if abs(area2(pc)) > 1e-6 * w * w]
        pcs = _square_bar(pcs, _axis(poly), w)
        # leave out bits too small or too thin to be worth making - before they cut anything else,
        # so no other bar is left with a notch or a loose chunk where they would have been
        keep = []
        for c in _components(pcs, 1e-3 * w):
            if sum(abs(area2(pc)) for pc in c) < 0.3 * w * w:
                continue
            if minp_ > 0 and _comp_thick(c) < minp_:
                continue
            keep += c
        pcs = keep
        if not pcs:
            return []
        bars.append((name, typ, pcs))
        for pc in pcs:
            placed.append(grow(pc, gap) if gap > 0 else pc)
        return pcs

    # ---- floor ledges first, right across the wall, so each floor has a level ledge all the way
    # round to sit on (posts and studs stop on it and carry on above, like a real floor between
    # storeys). They stop either side of a doorway or window they cross.
    if kind == 'wall' and ledges:
        n_ex = len(placed)
        placed.extend(b for b in ledge_extra if b)
        for ya, yb, lname in ledges:
            put(_box(x0 - 1.0, ya, x1 + 1.0, yb), lname, 'ledge')
        del placed[n_ex:n_ex + len([b for b in ledge_extra if b])]

    # ---- round the edge of the face: plates first, then sloping edges, then the end posts
    if p.get('perimeter', True):
        edges = []
        for i in range(n_):
            if i in door_edges:
                continue                  # the doorway gets its own square frame below
            a, b = outline[i], outline[(i + 1) % n_]
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L < 1e-6:
                continue
            s_ = abs(b[1] - a[1]) / L
            cls = 0 if s_ < 0.02 else (2 if s_ > 0.98 else 1)
            edges.append((cls, (a[1] + b[1]) / 2.0, a, b))
        # plates first, then the end posts (running up to the roof line), then the sloping rails
        # between them - so a rail ends square against the post, not in a point over the corner
        edges.sort(key=lambda e: ({0: 0, 2: 1, 1: 2}[e[0]], e[1]))
        for cls, ym, a, b in edges:
            if cls == 0:
                typ = 'bottom' if ym < y0 + 0.5 * w else 'top'
            elif cls == 1:
                typ = 'rake'
            else:
                typ = 'end'
            sa, sb_ = a, b
            if cls == 2:
                # an end post runs on up to the roof line (its top slopes with a gable rail),
                # so the rail stops square against it instead of running to a point
                L_ = math.hypot(b[0] - a[0], b[1] - a[1])
                u_ = ((b[0] - a[0]) / L_, (b[1] - a[1]) / L_)
                sa = (a[0] - u_[0] * 3.0 * w, a[1] - u_[1] * 3.0 * w)
                sb_ = (b[0] + u_[0] * 3.0 * w, b[1] + u_[1] * 3.0 * w)
            pcs = put(_strip(sa, sb_, 0.0, w), names[typ], typ)
            if cls == 2 and pcs:
                xs = [q[0] for pc in pcs for q in pc]
                uprights.append((min(xs), max(xs)))

    # ---- round each opening: a post each side, a lintel over and (windows) a sill under
    glazing = []
    if p.get('openings', True):
        lt = p.get('lintel', w)
        nw = nd = 0
        for (xa, ya, xb, yb, kind_, hh), (rl_, rr_, el_, er_) in sorted(zip(opens, room), key=lambda o: o[0][0]):
            if kind_ == 'window':
                nw += 1
                lab = "Window %d - " % nw if kind == 'wall' else "Opening %d - " % nw
            else:
                nd += 1
                lab = "Door %d - " % nd
            ox0, ox1, oy1 = rl_, rr_, yb + sb
            oy0 = ya - sb
            above = kind_ == 'window' and oy0 >= y1 - 1e-6     # up in the gable, over this frame (trusses)
            for pa, pb in ([] if above else ((ox0 - w, ox0), (ox1, ox1 + w))):
                if any(ua - 0.75 * w < pb and pa < ub + 0.75 * w for ua, ub in uprights):
                    continue          # a post is there already (an end post, the next opening's): share it
                if put(_box(pa, y0 - 1.0, pb, y1 + 1.0), lab + names['jamb'], 'jamb'):
                    uprights.append((pa, pb))
            # the lintel and sill reach across to the posts each side, wherever they are
            left = max([ub for ua, ub in uprights if ox0 - 2.0 * w <= ub <= ox0 + 1e-6] or [ox0 - w])
            right = min([ua for ua, ub in uprights if ox1 - 1e-6 <= ua <= ox1 + 2.0 * w] or [ox1 + w])
            put(_box(left, oy1, right, oy1 + lt), lab + names['lintel'], 'lintel')
            if kind_ == 'window' and oy0 - y0 > 1.5 * w:
                put(_box(left, oy0 - w, right, oy0), lab + names['sill'], 'sill')
            # the glazing frame: a flat frame of the width you set, its inside edge set in behind the
            # window's edge (so it can't be seen from outside), kept inside the room round the window
            gt, gw = p.get('glaze_t', 0.0), p.get('glaze_w', 0.0)
            si, fit = max(0.0, p.get('glaze_setin', 0.0)), max(0.0, p.get('glaze_inset', 0.0))
            if kind_ == 'window' and hh and gt > 0 and gw > 0:
                # always a whole frame: where there isn't room all round (a window near the end of
                # the wall, or the floor) it's made narrower all round, never cut open on one side
                lim_l, lim_r = max(rl_, el_), min(rr_, er_)
                if above:
                    lim_b, lim_t = ya - sb, yb + sb      # a loft window: the gable end truss frames round it
                else:
                    # never up past the top of the wall - unless a gable end truss stands on it, which
                    # is framed round the opening's room, so the glazing frame has its room up there
                    lim_b = max(ya - sb, y0)
                    lim_t = yb + sb if p.get('_open_top') else min(yb + sb, y1)
                full = min(gw, sb - fit - si)
                sides = [min(full, xa - si - fit - lim_l), min(full, ya - si - fit - lim_b),
                         min(full, lim_r - fit - si - xb), min(full, lim_t - fit - si - yb)]
                wid = min(sides)
                if wid < gw - 1e-6:
                    p['_glaze_short'] = True
                square_ = abs(area2(hh)) > 0.98 * (xb - xa) * (yb - ya)
                if wid < max(0.25 * full, 0.05):
                    p['_glaze_none'] = p.get('_glaze_none', 0) + 1     # no room for a proper frame
                elif square_:
                    # a square window: each side as wide as there's room for (narrower only where
                    # it has to be), and always a whole frame
                    inner = _box(xa - si, ya - si, xb + si, yb + si)
                    outer = _box(xa - si - sides[0], ya - si - sides[1], xb + si + sides[2], yb + si + sides[3])
                    ring = [q for q in subtract_convex(outer, inner) if abs(area2(q)) > 1e-6] if inner and outer else []
                    if ring:
                        glazing.append((lab + "Glazing frame", 'glaze', ring))
                else:
                    inner = grow(hh, si) if si > 0 else hh
                    outer = grow(hh, si + wid)
                    if inner and outer:
                        ring = [q for q in subtract_convex(outer, inner) if abs(area2(q)) > 1e-6]
                        if ring:
                            glazing.append((lab + "Glazing frame", 'glaze', ring))

    # ---- studs (rafters on a roof) evenly spaced, keeping clear of the posts
    studs = []
    sp = p.get('rafter_spacing' if kind == 'roof' else 'spacing', 0.0)
    if p.get('studs', True) and sp > w:
        cnt = int(round((x1 - x0) / sp)) - 1
        num = 0
        for i in range(1, cnt + 1):
            xc = x0 + (x1 - x0) * i / (cnt + 1.0)
            if any(xa - 0.75 * w < xc + w / 2.0 and xc - w / 2.0 < xb + 0.75 * w for xa, xb in uprights):
                continue
            num += 1
            if put(_box(xc - w / 2.0, y0 - 1.0, xc + w / 2.0, y1 + 1.0), "%s %d" % (names['stud'], num), 'stud'):
                studs.append((xc - w / 2.0, xc + w / 2.0))

    # ---- a diagonal brace in the bay at each end (where there's no opening)
    if p.get('braces', True) and kind == 'wall':
        ups = sorted(uprights + studs)

        def top_at(x):
            st = clip_half(clip_half(list(outline), 1.0, 0.0, -(x - 0.01)), -1.0, 0.0, x + 0.01)
            return max(q[1] for q in st) if len(st) >= 3 else None
        if len(ups) >= 3:
            for k, (a_, b_) in enumerate(((ups[0], ups[1]), (ups[-2], ups[-1]))):
                xa, xb = a_[1], b_[0]
                if xb - xa < 2.0 * w:
                    continue
                if any(bbox(h)[0] < xb and bbox(h)[1] > xa and bbox(h)[2] < y1 - 1e-6 for h in hulls):
                    continue
                mid = (xa + xb) / 2.0
                if not any(_inside((mid, y0 + 1.5 * w), pt) for pt in parts):
                    continue                       # a doorway at the bottom of the bay
                ta, tb = top_at(xa + 0.02), top_at(xb - 0.02)
                if ta is None or tb is None:
                    continue
                hgt = (tb if k == 0 else ta) - y0
                if xb - xa < 0.2 * hgt:
                    continue                       # too steep to be worth it
                if k == 0:
                    a, b = (xa, y0), (xb, tb)
                else:
                    a, b = (xa, ta), (xb, y0)
                put(_strip(a, b, -w / 2.0, w / 2.0), names['brace'] + (" left" if k == 0 else " right"),
                    'brace')

    # ---- rails (purlins on a roof) across the face, between the studs
    nr = int(p.get('purlins' if kind == 'roof' else 'rails', 0))
    for i in range(1, nr + 1):
        yc = y0 + (y1 - y0) * i / (nr + 1.0)
        put(_box(x0 - 1.0, yc - w / 2.0, x1 + 1.0, yc + w / 2.0), "%s %d" % (names['rail'], i), 'rail')

    # ---- one entry per separate piece
    minp = max(0.0, p.get('min_piece', 0.0))
    seen = {}
    for name, _t, _p in bars:
        seen[name] = seen.get(name, 0) + 1
    num = {}
    named = []
    for name, typ, pcs in bars:
        if seen[name] > 1:
            num[name] = num.get(name, 0) + 1
            name = "%s %d" % (name, num[name])
        named.append((name, typ, pcs))
    out = []
    tol = 1e-3 * w + gap * 1.01
    every = [(k, c) for k, (_n, _t, pcs) in enumerate(named) for c in _components(pcs, 1e-3 * w)]

    def floating(k, c):
        # a small bit left on its own, touching no other bar (a stud end cut off under a sill)
        if sum(abs(area2(pc)) for pc in c) > 4.0 * w * w:
            return False
        return not any(_touching(a, b, tol) for k2, c2 in every if c2 is not c for a in c for b in c2)
    keep = {}
    for k, c in every:
        if not floating(k, c):
            keep.setdefault(k, []).extend(c)
    named = [(nm, t, keep[k]) for k, (nm, t, _p) in enumerate(named) if k in keep]
    tol = 1e-3 * w
    for name, typ, pcs in named:
        comps = [c for c in _components(pcs, tol) if minp <= 0 or _comp_thick(c) >= minp]
        if not comps:
            continue                          # thinner than the smallest piece you want
        if len(comps) == 1:
            out.append((name, typ, comps[0]))
        else:
            for j, c in enumerate(comps):
                out.append(("%s (%d)" % (name, j + 1), typ, c))
    out += glazing
    return out


def _comp_thick(c):
    """About how thick a piece is: its area over its length."""
    xs = [q[0] for pc in c for q in pc]
    ys = [q[1] for pc in c for q in pc]
    L = max(max(xs) - min(xs), max(ys) - min(ys), 1e-12)
    return sum(abs(area2(pc)) for pc in c) / L


def solids_for(bars, z0, z1, glaze_t=None, ledge_out=0.0):
    """[(name, type, solid)] in the face's own terms (mm). Glazing frames get their own thickness;
    floor ledges stand out past the frame by ledge_out."""
    out = []
    for name, typ, pcs in bars:
        top = (z0 + glaze_t) if (typ == 'glaze' and glaze_t) else z1
        if typ == 'ledge':
            top = z1 + ledge_out
        so = merged_slab(pcs, lambda x, y: z0, lambda x, y, top=top: top)
        if so is not None:
            out.append((name, typ, so))
    return out


# ---------------------------------------------------------------------------
# Which faces get a frame, and on which side
# ---------------------------------------------------------------------------
def face_kind(n):
    if abs(n[2]) < 0.05:
        return 'wall'
    if abs(n[2]) > 0.995:
        return 'flat'
    return 'roof'


class FaceInfo:
    def __init__(self, face, centre=None):
        self.face = face
        self.pts = [q for q in (_pos(v) for v in _items(getattr(face, 'vertices', None))) if q is not None]
        self.ok = len(self.pts) >= 3
        if self.ok:
            self.n = _newell(self.pts)
            self.c = tuple(sum(q[i] for q in self.pts) / len(self.pts) for i in range(3))
            self.kind = face_kind(self.n)
            self.size = max(v_len(v_sub(a, self.pts[0])) for a in self.pts)
        self.centre = centre
        self.flip = False


def _has_twin(fi, others, thick):
    """Is there a face just behind this one, facing the other way (the other side of a thick
    wall or roof)? The two sides needn't be the same shape: a wall's outside may be split into
    a rectangle and a gable triangle while its inside is one face - they only need to overlap."""
    U = v_norm(v_cross(Z, fi.n)) if abs(fi.n[2]) < 0.999 else (1.0, 0.0, 0.0)
    V = v_cross(fi.n, U)

    def box(f):
        xs = [v_dot(q, U) for q in f.pts]
        ys = [v_dot(q, V) for q in f.pts]
        return min(xs), max(xs), min(ys), max(ys)
    a = box(fi)
    m = 0.05 * max(1e-9, min(a[1] - a[0], a[3] - a[2]))
    for o in others:
        if o is fi or not o.ok:
            continue
        if v_dot(fi.n, o.n) > -0.98:
            continue
        d = v_dot(v_sub(fi.pts[0], o.pts[0]), fi.n)
        if not (1e-9 < d <= thick):
            continue
        b = box(o)
        if a[0] + m < b[1] and b[0] < a[1] - m and a[2] + m < b[3] and b[2] < a[3] - m:
            return True
    return False


def choose_faces(infos, v, p, auto_skip):
    """Decides which faces get a frame and which side it goes. auto_skip: when a whole group
    is picked, leave out the outsides of thick walls/roofs and little faces like reveals."""
    want = {'wall': v.get('walls', True), 'roof': v.get('roofs', True), 'flat': v.get('flats', False)}
    thick = 600.0 * SCALE                  # walls and roofs up to 600 mm thick
    w_m = p['w'] * SCALE
    side = v.get('side', 'auto')
    if auto_skip:
        # a picked group (a whole building, or one wall): front and back mean the outside and the
        # inside of the wall as a whole - never both faces of a thick wall, with the frame of each
        # buried in the wall between them (what 'Back' used to do to a picked wall)
        side = {'back': 'auto', 'front': 'outside'}.get(side, side)
    out = []
    for fi in infos:
        if not fi.ok or not want.get(fi.kind, False):
            continue
        if auto_skip and fi.size < 3.0 * w_m:
            continue
        if side == 'front':
            fi.flip = False
        elif side == 'back':
            fi.flip = True
        else:
            if fi.kind == 'wall':
                c = fi.centre or fi.c
                outward = v_dot(fi.n, v_sub(c, fi.c)) < 0
            else:
                outward = fi.n[2] > 0          # roofs and floors: the frame goes underneath
            if side == 'outside':
                # the frame on the outside of the building: the inner faces are left out
                if not outward and auto_skip and _has_twin(fi, infos, thick):
                    continue
                fi.flip = not outward
            else:
                if outward and auto_skip and _has_twin(fi, infos, thick):
                    continue
                fi.flip = outward
        fi.auto = auto_skip
        out.append(fi)
    return out


_OURS = ("Subframe", "Roof truss", "Glazing frames")


def _save_last_build(faces, v):
    """Keeps a copy of the faces the last frame was made from (and the settings) in the presets
    folder, as last_build.json - so a fault can be looked into on exactly the same building.
    Never stops a build."""
    try:
        os.makedirs(PRESET_DIR, exist_ok=True)
        out = []
        for fi in faces:
            if not getattr(fi, 'ok', False):
                continue
            hl = []
            for h in _items(getattr(fi.face, 'holes', None)):
                hp = [q for q in (_pos(x) for x in _items(h)) if q is not None]
                if hp:
                    hl.append(hp)
            out.append({'pts': fi.pts, 'holes': hl})
        with open(os.path.join(PRESET_DIR, "last_build.json"), "w", encoding="utf-8") as f:
            json.dump({'version': VERSION, 'settings': v, 'faces': out}, f)
    except Exception as e:
        print("%s: couldn't keep a copy of the build: %s" % (PLUGIN_NAME, e))


def _nearby(scene, pts, picked):
    """The rest of the model round a picked group: [FaceInfo] of every face in the groups near it
    (not the frames made already). Used when one wall is picked on its own, to tell which side
    of it the building is - and to find the floor it stands on."""
    if scene is None or not pts:
        return []
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    reach = max(max(xs) - min(xs), max(ys) - min(ys), 1e-3)
    lo = (min(xs) - reach, min(ys) - reach)
    hi = (max(xs) + reach, max(ys) + reach)
    ids = set(id(g) for g in picked)
    out = []
    for g in _items(getattr(scene, 'groups', None)):
        if id(g) in ids or str(getattr(g, 'name', '') or '').startswith(_OURS):
            continue
        try:
            fs = [FaceInfo(f) for f in _world_faces(g)]
        except Exception:
            continue
        fs = [fi for fi in fs if fi.ok]
        if not fs or len(out) + len(fs) > 40000:
            continue
        gx = [q[0] for fi in fs for q in fi.pts]
        gy = [q[1] for fi in fs for q in fi.pts]
        if max(gx) < lo[0] or min(gx) > hi[0] or max(gy) < lo[1] or min(gy) > hi[1]:
            continue
        out += fs
    return out


def _plan_centre(pts):
    if not pts:
        return None
    xs, ys, zs = [q[0] for q in pts], [q[1] for q in pts], [q[2] for q in pts]
    return ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0, (min(zs) + max(zs)) / 2.0)


# 3D Period Windows / 3D Period Doors keep the plain wall (as it was before they were built into it)
# on the wall group. The frame is made from that plain wall, so the windows, doors, steps and heads
# built into it - hundreds of small faces - aren't framed as if they were walls.
OPENINGS_KEY = "ed3d_openings"


class _PlainFace:
    """A face of a plain wall kept by the window and door plugins, in the world."""
    def __init__(self, pts, holes):
        self.vertices = [tuple(p) for p in pts]
        self.holes = [[tuple(p) for p in h] for h in holes]
        self.attrs = {}


def _plain_wall(g):
    ext = getattr(g, 'ext', None)
    if not isinstance(ext, dict):
        return None
    for key in (OPENINGS_KEY, "ed3d_period_windows"):
        rec = ext.get(key)
        if isinstance(rec, dict) and rec.get('orig'):
            return rec['orig']
    return None


def _world_faces_plain(g):
    """Like _world_faces, but a wall with windows or doors built into it gives its plain faces."""
    places = _placements(g)
    if not any(_plain_wall(e) for e, _m in places):
        return None
    out = []
    seen = set()
    for e, m in places:
        mesh = getattr(e, 'mesh', None)
        if mesh is None or id(mesh) in seen:
            continue
        seen.add(id(mesh))
        to_w = _mapper(m)[0]
        plain = _plain_wall(e)
        if plain:
            faces = [([tuple(q) for q in pts], [[tuple(q) for q in h] for h in hls]) for pts, hls in plain]
        else:
            faces = [(pts, hls) for pts, hls, _a in _faces_of(mesh)]
        for pts, hls in faces:
            if len(pts) >= 3:
                out.append(_PlainFace([to_w(q) for q in pts], [[to_w(q) for q in h] for h in hls]))
    return out


def _world_faces(g):
    try:
        plain = _world_faces_plain(g)
        if plain is not None:
            return plain
    except Exception as e:
        print("%s: plain walls not used: %s" % (PLUGIN_NAME, e))
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


# ---------------------------------------------------------------------------
# Dividing walls: after the frame is made, their ends are brought back to meet it
# ---------------------------------------------------------------------------
_DIVIDER = ("inside wall", "divider", "dividing wall")


def _is_divider(e):
    nm = str(getattr(e, 'name', '') or '').lower()
    return any(w in nm for w in _DIVIDER)


def _placements(g):
    """Every group under g (g too) with its matrix to the world: [(group, matrix or None)]."""
    try:
        from core.group import iter_placements
        return list(iter_placements(g))
    except Exception:
        pass
    places = []

    def walk(e, base, depth):
        m = getattr(e, 'xform', None)
        if base is not None:
            m = base if m is None else base * m
        places.append((e, m))
        if depth < 12:
            for c in _items(getattr(e, 'children', None)) + _items(getattr(e, 'groups', None)):
                if getattr(c, 'vertices', None) is None or getattr(c, 'mesh', None) is not None:
                    walk(c, m, depth + 1)
    walk(g, None, 0)
    return places


def _mapper(m):
    """(to world, from world) for a group's matrix (None = it's already in the world)."""
    if m is None:
        return (lambda q: q), (lambda q: q)
    inv = m.inverted()
    inv = inv[0] if isinstance(inv, tuple) else inv

    def go(mat):
        def f(q):
            r = mat.map(QVector3D(*q))
            return (r.x(), r.y(), r.z())
        return f
    return go(m), go(inv)


def _faces_of(mesh):
    """A mesh's faces as [(points, holes, attrs)], in its own terms."""
    out = []
    for f in _items(getattr(mesh, 'faces', None)):
        pts = [q for q in (_pos(v_) for v_ in _items(getattr(f, 'vertices', None))) if q is not None]
        hls = []
        for h in _items(getattr(f, 'holes', None)):
            hp = [q for q in (_pos(x) for x in _items(getattr(h, 'vertices', None) or h)) if q is not None]
            if len(hp) >= 3:
                hls.append(hp)
        if len(pts) >= 3:
            out.append((pts, hls, dict(getattr(f, 'attrs', None) or {})))
    return out


def _mesh_from(face_list):
    """A new mesh from [(points, holes, attrs)]. Returns (mesh, faces that failed)."""
    from core.mesh import Mesh
    mesh = Mesh()
    tol = 1e-7
    verts = {}
    bad = 0

    def vx(q):
        k = (round(q[0] / tol), round(q[1] / tol), round(q[2] / tol))
        if k not in verts:
            verts[k] = VertexWrapper(*q)
        return verts[k]
    for pts, hls, attrs in face_list:
        try:
            outer = [vx(q) for q in pts]
            hs = [[vx(q) for q in h] for h in hls]
            if hs:
                try:
                    f_ = mesh.add_face(outer, hs)
                except TypeError:
                    f_ = mesh.add_face(outer)
                    for h in hs:
                        mesh.add_hole(f_, h)
            else:
                f_ = mesh.add_face(outer)
            if attrs and f_ is not None:
                try:
                    f_.attrs = dict(attrs)
                except Exception:
                    pass
        except Exception as e:
            bad += 1
            print("%s: a face couldn't be made: %s" % (PLUGIN_NAME, e))
    return mesh, bad


def fit_dividers(scene, groups, bars, gap_m=0.0):
    """The dividing walls in and round the building, each end that runs into the new frame
    brought back to stop against it. Only the end face moves (anything cut into the divider stays
    as it is); an end with something cut too close to it is left alone. bars: the wall frame's
    bars as solids in the world. Returns ([(group, old mesh, new mesh)], [notes])."""
    if not bars:
        return [], []
    ids = set(id(g) for g in groups)
    cands = list(groups) + [g for g in _items(getattr(scene, 'groups', None)) if id(g) not in ids and
                            not str(getattr(g, 'name', '') or '').startswith(_OURS)]
    swaps, notes, seen = [], [], set()
    eps = 1e-6
    for g in cands:
        try:
            places = _placements(g)
        except Exception:
            continue
        under = set()
        for e, _m in places:
            if _is_divider(e):
                for e2, _m2 in _placements(e):
                    under.add(id(e2))
        for e, m in places:
            mesh = getattr(e, 'mesh', None)
            if id(e) not in under or mesh is None or id(e) in seen:
                continue
            seen.add(id(e))
            try:
                faces = _faces_of(mesh)
                if not faces:
                    continue
                _to_w, to_l = _mapper(m)
                allv = [q for pts, hls, _a in faces for q in pts + [x for h in hls for x in h]]
                lo = [min(q[k] for q in allv) for k in range(3)]
                hi = [max(q[k] for q in allv) for k in range(3)]
                # each way along it (both ways for a joined cross, T or L from Floor Plan): the ends
                # that run into a bar of the frame come back to stop against it
                moved = []
                for ax in (0, 1):
                    cx = 1 - ax
                    a0, a1 = lo[ax], hi[ax]
                    if (a1 - a0) * 3.0 < (hi[cx] - lo[cx]):
                        continue                                     # its thickness, not a way along
                    mid = (a0 + a1) / 2.0
                    n0, n1 = a0, a1
                    for pts, _edges, (blo, bhi) in bars:
                        lp = [to_l(q) for q in pts]          # the bar's corners in the divider's terms
                        bl = [min(q[k] for q in lp) for k in range(3)]
                        bh = [max(q[k] for q in lp) for k in range(3)]
                        if bh[2] <= lo[2] + eps or bl[2] >= hi[2] - eps:
                            continue                                 # above or below it
                        if bh[ax] <= a0 + eps or bl[ax] >= a1 - eps:
                            continue                                 # past its ends
                        if bl[ax] <= a0 + eps and bh[ax] >= a1 - eps:
                            continue                                 # alongside the whole of it, not at an end
                        end = a0 if (bl[ax] + bh[ax]) / 2.0 < mid else a1
                        ev = [q[cx] for q in allv if abs(q[ax] - end) <= eps]
                        if not ev or bh[cx] <= min(ev) + eps or bl[cx] >= max(ev) - eps:
                            continue                                 # beside that end, not in its way
                        if end == a0:
                            n0 = max(n0, bh[ax] + gap_m)
                        else:
                            n1 = min(n1, bl[ax] - gap_m)
                    if n0 <= a0 + eps and n1 >= a1 - eps:
                        continue                                     # clear of the frame already
                    if n1 - n0 < 0.25 * (a1 - a0):
                        notes.append("%s: left as it is - it would be cut to almost nothing" % e.name)
                        continue
                    coords = sorted(set(round(q[ax] / eps) * eps for q in allv))
                    for end, new, sgn in ((a0, n0, 1.0), (a1, n1, -1.0)):
                        if abs(new - end) <= eps:
                            continue
                        # anything cut into it (a doorway) too close to this end: leave the end alone
                        if any(sgn * (c - end) > eps and sgn * (new - c) > -eps for c in coords):
                            notes.append("%s: one end left as it is - something cut into it is too close to "
                                         "the end" % e.name)
                            continue
                        moved.append((ax, end, new))
                if not moved:
                    continue

                def shift(q):
                    q2 = list(q)
                    for ax_, end, new in moved:
                        if abs(q[ax_] - end) <= eps:
                            q2[ax_] = new
                    return tuple(q2)
                nf = [([shift(q) for q in pts], [[shift(x) for x in h] for h in hls], at)
                      for pts, hls, at in faces]
                new, bad = _mesh_from(nf)
                if bad:
                    notes.append("%s: left as it is - its new shape couldn't be made" % e.name)
                    continue
                swaps.append((e, mesh, new))
            except Exception as ex:
                notes.append("%s: left as it is (%s)" % (getattr(e, 'name', '?'), ex))
    return swaps, notes


def swap_meshes_command(swaps):
    """One undo step: each divider gets its shortened mesh (undo puts the old one back)."""
    try:
        from core.history import Command
    except Exception:
        Command = object

    class FitDividersCommand(Command):
        def _tidy(self, scene):
            try:
                scene.version += 1
            except Exception:
                pass

        def do(self, scene):
            for g, _old, new in swaps:
                g.mesh = new
            self._tidy(scene)

        def undo(self, scene):
            for g, old, _new in swaps:
                g.mesh = old
            self._tidy(scene)
    return FitDividersCommand()


# parts of a building that never get a frame: the base plate (plinth), the top plate, the floors
# and the inside (dividing) walls - from Floor Plan, or any group you name the same way
_NO_FRAME = ("base plate", "top plate", "inside wall", "divider", "dividing wall", "floor slab", "floor panel",
             "ledge")


def _no_frame(g):
    nm = str(getattr(g, 'name', '') or '').lower()
    return any(w in nm for w in _NO_FRAME)


def _framable_faces(g):
    """The faces of a picked group, less those in groups that never get a frame (base plate,
    dividing walls...). Their faces are found in place in the world and left out of the rest."""
    faces = _world_faces(g)
    try:
        try:
            from core.group import iter_placements
            places = list(iter_placements(g))
        except Exception:
            places = []

            def walk(e, base, depth):
                m = getattr(e, 'xform', None)
                if base is not None:
                    m = base if m is None else base * m
                places.append((e, m))
                if depth < 12:
                    for c in _items(getattr(e, 'children', None)) + _items(getattr(e, 'groups', None)):
                        if getattr(c, 'vertices', None) is None or getattr(c, 'mesh', None) is not None:
                            walk(c, m, depth + 1)
            walk(g, None, 0)
        skip_ids = set()

        def mark(e, depth=0):
            skip_ids.add(id(e))
            if depth < 50:
                for c in _items(getattr(e, 'children', None)) + _items(getattr(e, 'groups', None)):
                    mark(c, depth + 1)
        for e, _m in places:
            if _no_frame(e):
                mark(e)
        if not skip_ids:
            return faces

        def key(pts):
            # the face's corners, to 0.02 mm - not just its middle: a dividing wall's end face has
            # the same middle as the wall face it stands against, and that wall face must still be
            # framed (matching middles only left it out, and the wall was framed from outside)
            return frozenset(tuple(round(x / 2e-5) for x in q) for q in pts)
        skip = set()
        for e, m in places:
            if id(e) not in skip_ids:
                continue
            for f in _items(getattr(getattr(e, 'mesh', None), 'faces', None)):
                pts = []
                for v_ in _items(getattr(f, 'vertices', None)):
                    q = _pos(v_)
                    if q is None:
                        continue
                    if m is not None:
                        try:
                            from PySide6.QtGui import QVector3D as _QV
                            r = m.map(_QV(*q))
                            q = (r.x(), r.y(), r.z())
                        except Exception:
                            pass
                    pts.append(q)
                if len(pts) >= 3:
                    skip.add(key(pts))
        out = []
        for f in faces:
            pts = [q for q in (_pos(v_) for v_ in _items(getattr(f, 'vertices', None))) if q is not None]
            if len(pts) >= 3 and key(pts) in skip:
                continue
            out.append(f)
        return out
    except Exception:
        return faces


def _mesh_centre(scene, face):
    m = mesh_of_face(scene, face) if scene is not None else None
    if m is None:
        return None
    pts = [q for q in (_pos(v) for v in _items(getattr(m, 'vertices', None))) if q is not None]
    if not pts:
        for f in _items(getattr(m, 'faces', None)):
            pts += [q for q in (_pos(v) for v in _items(getattr(f, 'vertices', None))) if q is not None]
    return _plan_centre(pts)


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


def _merge_coplanar(ready, p):
    tol = max(1e-3 * p['w'], 1e-4)
    merged = True
    while merged:
        merged = False
        for i, a in enumerate(ready):
            O = a.tw((0.0, 0.0, 0.0))
            Uu = v_norm(v_sub(a.tw((1.0, 0.0, 0.0)), O))
            Vu = v_norm(v_sub(a.tw((0.0, 1.0, 0.0)), O))

            def to_a(P, O=O, Uu=Uu, Vu=Vu):
                d = v_sub(P, O)
                return (v_dot(d, Uu) / SCALE, v_dot(d, Vu) / SCALE)
            for b in ready[i + 1:]:
                if b.kind != a.kind or v_dot(a.N, b.N) < 0.9999:
                    continue
                if abs(v_dot(v_sub(b.tw((0.0, 0.0, 0.0)), O), a.N)) / SCALE > tol:
                    continue
                bo = clean([to_a(b.tw((x, y, 0.0))) for x, y in b.outline])
                if not bo:
                    continue
                u = _join(a.outline, bo, tol)
                if u is None:
                    continue
                a.outline = u
                a.holes = list(a.holes) + [h for h in (clean([to_a(b.tw((x, y, 0.0))) for x, y in hl])
                                                        for hl in b.holes) if h]
                ready.remove(b)
                merged = True
                break
            if merged:
                break


def _opening_spans(outline, holes, tol):
    """Where the openings are along a wall: [(x from, x to)] for every window (a hole in the face)
    and every doorway (cut up into its bottom edge), in the wall's own terms."""
    spans = []
    for hl in holes or ():
        if hl:
            bx = bbox(hl)
            spans.append((bx[0], bx[1]))
    n = len(outline)
    y0 = bbox(outline)[2]
    low = [abs(q[1] - y0) < tol for q in outline]
    for i in range(n):
        j = (i + 1) % n
        if low[i] and not low[j]:
            # up off the bottom edge: walk on to where it comes back down
            k, run = j, []
            while not low[k] and len(run) <= n:
                run.append(outline[k])
                k = (k + 1) % n
            if outline[k][0] > outline[i][0] + tol and len(run) < n:
                spans.append((min(outline[i][0], outline[k][0]), max(outline[i][0], outline[k][0])))
    return spans


def _is_reveal(a, b, w):
    """Is face b just the side of an opening in wall a (a window or door reveal) rather than a
    real wall meeting it? A reveal crosses a's face right in an opening; a real wall can't. Near
    the end of a wall a reveal used to be taken for the wall round the corner, and the frame was
    cut back to it - so it lost its end, and the trusses came out the wrong shape."""
    if b.kind != 'wall' or abs(v_dot(a.N, b.N)) > 0.5:
        return False
    PB, NB = b.tw((0.0, 0.0, 0.0)), b.N

    def f(x, y):
        return v_dot(v_sub(a.tw((x, y, 0.0)), PB), NB) / SCALE
    f0 = f(0.0, 0.0)
    fx, fy = f(1.0, 0.0) - f0, f(0.0, 1.0) - f0
    if abs(fx) < 1e-9:
        return False
    x0, x1, y0, y1 = bbox(a.outline)
    tol = 0.25 * w + 1.0
    # where b's face crosses a's, along a - at the height of b (a door reveal is low down)
    bz = [v_dot(v_sub(b.tw((x_, y_, 0.0)), a.tw((0.0, 0.0, 0.0))),
                v_norm(v_sub(a.tw((0.0, 1.0, 0.0)), a.tw((0.0, 0.0, 0.0))))) / SCALE for x_, y_ in b.outline]
    ym = (max(min(bz), y0) + min(max(bz), y1)) / 2.0
    xs = -(f0 + fy * ym) / fx
    spans = _opening_spans(a.outline, getattr(a, 'holes', ()), 1e-3 * w + 1e-6)
    if not any(xa - tol <= xs <= xb + tol for xa, xb in spans):
        return False
    # and it's no bigger across than a thick wall
    across = [v_dot(v_sub(b.tw((x_, y_, 0.0)), a.tw((0.0, 0.0, 0.0))), a.N) / SCALE for x_, y_ in b.outline]
    return max(across) - min(across) <= 650.0


def _drop_reveals(ready, p):
    """Takes window and door reveals out of the faces to frame: they're too small for a frame of
    their own, and left in they get taken for walls. Returns how many openings were near the end
    of a wall (closer than 650 mm) - those are the ones that went wrong before."""
    w = p['w']
    walls = [fi for fi in ready if fi.kind == 'wall']
    rev = set()
    near = []
    for a in walls:
        x0, x1 = bbox(a.outline)[:2]
        for b in walls:
            if b is not a and id(b) not in rev and _is_reveal(a, b, w):
                rev.add(id(b))
        for xa, xb in _opening_spans(a.outline, getattr(a, 'holes', ()), 1e-3 * w + 1e-6):
            d = min(xa - x0, x1 - xb)
            if d < 650.0:
                near.append(max(0.0, d))
    if rev:
        ready[:] = [fi for fi in ready if id(fi) not in rev]
    return near


def _clip_at_walls(ready):
    """A wall whose face runs on past the inside face of the wall it meets (into or through that
    wall) is cut back to it, so its frame stops at the corner and can't come out the other side."""
    thick = 600.0
    for a in ready:
        if a.kind != 'wall':
            continue
        x0, x1, y0, y1 = bbox(a.outline)
        ym = (y0 + y1) / 2.0
        for b in ready:
            if b is a or b.kind != 'wall' or abs(v_dot(a.N, b.N)) > 0.5:
                continue
            if _is_reveal(a, b, 0.0):
                continue                       # the side of one of a's own windows or doors
            PB, NB = b.tw((0.0, 0.0, 0.0)), b.N

            def f(x, y, PB=PB, NB=NB):
                return v_dot(v_sub(a.tw((x, y, 0.0)), PB), NB) / SCALE
            f0 = f(0.0, 0.0)
            fx, fy = f(1.0, 0.0) - f0, f(0.0, 1.0) - f0
            if abs(fx) < 1e-9:
                continue
            xs = -(f0 + fy * ym) / fx
            at_start = fx > 0 and x0 - 1.0 < xs < x0 + thick
            at_end = fx < 0 and x1 - thick < xs < x1 + 1.0
            if not (at_start or at_end) or not (x0 < xs < x1):
                continue
            # only where wall b is really there, at that end of wall a
            Ob = b.tw((0.0, 0.0, 0.0))
            Ub = v_norm(v_sub(b.tw((1.0, 0.0, 0.0)), Ob))
            Vb = v_norm(v_sub(b.tw((0.0, 1.0, 0.0)), Ob))
            bx = bbox(b.outline)
            P = a.tw((xs, ym, 0.0))
            u_, w_ = v_dot(v_sub(P, Ob), Ub) / SCALE, v_dot(v_sub(P, Ob), Vb) / SCALE
            if not (bx[0] - thick <= u_ <= bx[1] + thick and bx[2] - thick <= w_ <= bx[3] + thick):
                continue
            o = clip_half(list(a.outline), fx, fy, f0)
            o = clean(o) if len(o) >= 3 else None
            if o:
                a.outline = o
                x0, x1, y0, y1 = bbox(o)


def _clip_walls_under_roof(ready, every, w_m_=None):
    """Cuts each wall's frame off at the underside of the roof over it. Walls (and gable
    triangles) are often drawn on up into the roof, or right up to its top, and the frame would
    follow them up through the roof. For a pitched or hipped roof the underside is the lowest of
    the roof's faces at each point, so the wall is cut by each roof face it sits under."""
    roofs = [r for r in every if getattr(r, 'ok', False) and getattr(r, 'kind', '') == 'roof']
    if not roofs:
        return
    for a in ready:
        if a.kind != 'wall':
            continue
        wp = [a.tw((x, y, 0.0)) for x, y in a.outline]
        wx0, wx1 = min(q[0] for q in wp), max(q[0] for q in wp)
        wy0, wy1 = min(q[1] for q in wp), max(q[1] for q in wp)
        wz0 = min(q[2] for q in wp)
        wlen = math.hypot(wx1 - wx0, wy1 - wy0)
        w_m = 0.0 if w_m_ is None else w_m_
        for r in roofs:
            # only real roof slopes: big, and up over the top of the wall - not the sloping
            # reveals round a round or many-sided window, down in the wall itself
            if r.size < 0.25 * wlen:
                continue
            across = [v_dot(q, a.N) for q in r.pts]          # how far it reaches across the wall
            if max(across) - min(across) < max(0.1 * wlen, 4.0 * w_m):
                continue
            rx0, rx1 = min(q[0] for q in r.pts), max(q[0] for q in r.pts)
            ry0, ry1 = min(q[1] for q in r.pts), max(q[1] for q in r.pts)
            m = 1e-4
            if rx1 < wx0 - m or rx0 > wx1 + m or ry1 < wy0 - m or ry0 > wy1 + m:
                continue                       # not over this wall
            if max(q[2] for q in r.pts) <= wz0:
                continue                       # below it
            n = r.n if r.n[2] > 0 else v_mul(r.n, -1.0)
            R0 = r.pts[0]

            def f(x, y, n=n, R0=R0):
                return v_dot(v_sub(a.tw((x, y, 0.0)), R0), n) / SCALE
            vals = [f(x, y) for x, y in a.outline]
            if max(vals) <= 1e-6 or min(vals) >= 0:
                continue                       # all under it already (or all above: not ours)
            f0 = f(0.0, 0.0)
            fx, fy = f(1.0, 0.0) - f0, f(0.0, 1.0) - f0
            o = clip_half(list(a.outline), -fx, -fy, -f0)
            o = clean(o) if len(o) >= 3 else None
            if o and abs(area2(o)) > 1e-6:
                a.outline = o


def _clip_roofs_to_walls(ready):
    """A roof that hangs out past the walls (eaves and verges) only gets its frame over the inside
    of the building - so no bars show under the overhang outside, and nothing is left for the roof
    to sit on but the walls."""
    walls = [b for b in ready if b.kind == 'wall']
    reach = 2500.0                         # roofs overhanging up to 2.5 m
    for a in ready:
        if a.kind not in ('roof', 'flat'):
            continue
        for b in walls:
            PB, NB = b.tw((0.0, 0.0, 0.0)), b.N
            if abs(NB[2]) > 0.05:
                continue

            def f(x, y, PB=PB, NB=NB):
                return v_dot(v_sub(a.tw((x, y, 0.0)), PB), NB) / SCALE
            vals = [f(x, y) for x, y in a.outline]
            if min(vals) >= -1e-6 or min(vals) < -reach or max(vals) <= 0:
                continue                   # all inside this wall, or nowhere near it
            # the wall must be under the roof: along the wall, and the roof up over its lower part
            Ub = v_norm(v_sub(b.tw((1.0, 0.0, 0.0)), PB))
            bx = bbox(b.outline)
            us = [v_dot(v_sub(a.tw((x, y, 0.0)), PB), Ub) / SCALE for x, y in a.outline]
            if max(us) < bx[0] or min(us) > bx[1]:
                continue
            wz = [b.tw((x, y, 0.0))[2] for x, y in b.outline]
            az = min(a.tw((x, y, 0.0))[2] for x, y in a.outline)
            if az < min(wz) + 0.3 * (max(wz) - min(wz)):
                continue
            f0 = f(0.0, 0.0)
            fx, fy = f(1.0, 0.0) - f0, f(0.0, 1.0) - f0
            o = clip_half(list(a.outline), fx, fy, f0)
            o = clean(o) if len(o) >= 3 else None
            if o and abs(area2(o)) > 1e-6:
                a.outline = o
                a.holes = [h for h in a.holes if all(fx * x + fy * y + f0 > 0 for x, y in h)]


def find_floor(every, walls, centre=None):
    """A floor drawn in the building: the biggest level, upward face near the bottom of the walls.
    Its outline, seen from above, is where the inside of the building is. Returns (outline, the
    height of its top) - or (None, None) if there isn't one. A little level face (a window sill)
    doesn't count, nor a floor that isn't under the building (centre: the middle of it)."""
    wl = [fi for fi in walls if getattr(fi, 'kind', '') == 'wall']
    if not wl:
        return None, None
    wx = [q[0] for fi in wl for q in fi.pts]
    wy = [q[1] for fi in wl for q in fi.pts]
    span = max(max(wx) - min(wx), max(wy) - min(wy))
    best_z = None
    zb = min(q[2] for fi in wl for q in fi.pts)
    zt = max(q[2] for fi in wl for q in fi.pts)
    cands = []
    for fi in every:
        if not getattr(fi, 'ok', False) or fi.n[2] < 0.995:
            continue
        z = fi.pts[0][2]
        if not (zb - 1e-6 <= z <= zb + 0.4 * (zt - zb)):
            continue
        poly = clean([(q[0], q[1]) for q in fi.pts])
        if not poly:
            continue
        if abs(area2(poly)) < 0.1 * span * span and abs(area2(poly)) < 1.0:
            continue                   # a sill or a step, not a floor
        if centre is not None and not _pip((centre[0], centre[1]), poly):
            continue                   # not under this building
        cands.append((abs(area2(poly)), z, poly))
    if not cands:
        return None, None
    # a floor panel dropped in on a base plate: the base is a little bigger, but the frame stands
    # on the floor - so of the big ones (at least half the biggest), the highest
    big = max(c[0] for c in cands)
    a_, best_z, best = max((c for c in cands if c[0] >= 0.5 * big), key=lambda c: (c[1], c[0]))
    return best, best_z


def _clip_to_floor(ready, floor, p):
    """Cuts each wall's frame back so it stays over the floor (seen from above) - so it can't run
    on into the next wall or out through the corner."""
    zs = (p.get('lift', 0.0) + 1e-3, p.get('lift', 0.0) + p['depth'] - 1e-3)
    n = len(floor)
    for a in ready:
        if a.kind != 'wall':
            continue
        x0, x1, y0, y1 = bbox(a.outline)
        lo, hi = x0, x1
        for z in zs:
            P0 = a.tw((x0, y0, z))
            P1 = a.tw((x1, y0, z))
            dx, dy = P1[0] - P0[0], P1[1] - P0[1]
            ts = []
            for i in range(n):
                (ax, ay), (bx, by) = floor[i], floor[(i + 1) % n]
                ex, ey = bx - ax, by - ay
                den = dx * ey - dy * ex
                if abs(den) < 1e-15:
                    continue
                t = ((ax - P0[0]) * ey - (ay - P0[1]) * ex) / den
                u = ((ax - P0[0]) * dy - (ay - P0[1]) * dx) / den
                if -1e-9 <= u <= 1 + 1e-9:
                    ts.append(t)
            ts = sorted(set(round(t, 9) for t in ts))
            if len(ts) < 2:
                continue
            # the stretch over the floor that holds the middle of the wall
            mid = 0.5
            spans = [(ts[k], ts[k + 1]) for k in range(len(ts) - 1)
                     if _pip(((P0[0] + dx * (ts[k] + ts[k + 1]) / 2.0), (P0[1] + dy * (ts[k] + ts[k + 1]) / 2.0)),
                             floor)]
            if not spans:
                continue
            ta, tb = min(spans, key=lambda s_: 0.0 if s_[0] <= mid <= s_[1] else min(abs(s_[0] - mid), abs(s_[1] - mid)))
            lo = max(lo, x0 + ta * (x1 - x0))
            hi = min(hi, x0 + tb * (x1 - x0))
        if hi - lo < 1e-6:
            continue
        o = list(a.outline)
        if lo > x0 + 1e-6:
            o = clip_half(o, 1.0, 0.0, -lo)
        if hi < x1 - 1e-6 and len(o) >= 3:
            o = clip_half(o, -1.0, 0.0, hi)
        o = clean(o) if len(o) >= 3 else None
        if o:
            a.outline = o


def _stand_on_floor(ready, zf, p):
    """Walls drawn on down past the top of the floor (standing on the base, with the floor inside
    them) are cut off at the floor's top, so the frame stands on the floor instead of going down
    into it."""
    n = 0
    for a in ready:
        if a.kind != 'wall':
            continue
        Oz = a.tw((0.0, 0.0, 0.0))[2]
        dz = a.tw((0.0, 1.0, 0.0))[2] - Oz          # metres of height per mm up the face
        if dz < 1e-12:
            continue
        yf = (zf - Oz) / dz
        x0, x1, y0, y1 = bbox(a.outline)
        if yf <= y0 + 1e-3 or yf >= y1 - 2.2 * p['w']:
            continue
        o = clip_half(list(a.outline), 0.0, 1.0, -yf)
        o = clean(o) if len(o) >= 3 else None
        if o:
            a.outline = o
            a.holes = [h for h in a.holes if max(q[1] for q in h) > yf]
            n += 1
    if n:
        p['_on_floor'] = n


def _insert_point(poly, q, tol=1e-6):
    """Puts point q into the outline where it lies on an edge (so another outline can share it)."""
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 1e-12:
            continue
        t = ((q[0] - a[0]) * dx + (q[1] - a[1]) * dy) / (L * L)
        off = abs((q[0] - a[0]) * dy - (q[1] - a[1]) * dx) / L
        if off < tol and 1e-9 < t < 1 - 1e-9:
            return poly[:i + 1] + [q] + poly[i + 1:]
    return poly


def _notch(outline, side, xcut, ytop):
    """Cuts the end of a wall back to xcut (side 0: the start, 1: the end) - but only up to ytop,
    the top of the wall it meets. Above that the outline keeps its full width, so a gable's frame
    runs right into the corner over the top of the other wall."""
    sgn = 1.0 if side == 0 else -1.0
    A = clip_half(list(outline), sgn, 0.0, -sgn * xcut)
    A = clean(A) if len(A) >= 3 else None
    if ytop is None or ytop < -1e17 or A is None:
        return A
    B = clip_half(list(outline), -sgn, 0.0, sgn * xcut)
    B = clip_half(B, 0.0, 1.0, -ytop) if len(B) >= 3 else []
    B = clean(B) if len(B) >= 3 else None
    if not B:
        return A
    tol = 1e-6 * (1.0 + max(abs(c) for q in outline for c in q))
    A2 = _insert_point(A, (xcut, ytop), tol)
    u = _join(A2, B, tol * 10.0)
    return u if u else A


def frame_panels(chosen, v, p):
    """Works out every chosen face's frame. Returns ([(panel name, [(name, type, world solid)])],
    problems)."""
    depth, lift = p['depth'], p.get('lift', 0.0)
    panels = []
    for fi in chosen:
        try:
            tw, outline, holes, _up = face_frame(fi.face, fi.flip, 0)
        except Exception as e:
            fi.err = str(e)
            continue
        if outline is None:
            continue
        fi.tw, fi.outline, fi.holes = tw, outline, holes
        o = tw((0.0, 0.0, 0.0))
        fi.U = v_norm(v_sub(tw((1.0, 0.0, 0.0)), o))
        fi.N = v_norm(v_sub(tw((0.0, 0.0, 1.0)), o))
        x0, x1, y0, y1 = bbox(outline)
        fi.ends = [(tw((x0, y0, 0.0)), fi.U), (tw((x1, y0, 0.0)), v_mul(fi.U, -1.0))]
        fi.inset = [0.0, 0.0]
        fi.inset_top = [-1e18, -1e18]
    ready = [fi for fi in chosen if getattr(fi, 'outline', None)]
    # faces in the same plane that share an edge (a gable triangle on the wall under it) are
    # framed as one wall, so posts run right up to the gable rails
    _merge_coplanar(ready, p)
    p['_near_end'] = _drop_reveals(ready, p)
    _clip_at_walls(ready)
    _clip_walls_under_roof(ready, p.get('_all_faces') or ready, p['w'] * SCALE)
    # floor levels are measured up from the bottom of the walls, as drawn
    base0 = [fi.tw((x, y, 0.0))[2] for fi in ready if fi.kind == 'wall' for x, y in fi.outline]
    p['_wall_bottom'] = min(base0) if base0 else None
    if p.get('_floor'):
        _clip_to_floor(ready, p['_floor'], p)
    if p.get('_floor_z') is not None:
        _stand_on_floor(ready, p['_floor_z'], p)
    _clip_roofs_to_walls(ready)
    for fi in ready:
        x0, x1, y0, y1 = bbox(fi.outline)
        fi.ends = [(fi.tw((x0, y0, 0.0)), fi.U), (fi.tw((x1, y0, 0.0)), v_mul(fi.U, -1.0))]
    # inside corners: where two walls' frames would run into each other, the first stops short
    if v.get('corners', True):
        tol = max(1e-6, 0.4 * p['w'] * SCALE)

        def framable(f):
            # the end face of a thin wall (no wider than a bar or two) never gets a frame - it
            # mustn't make a real wall stop short at the corner, or both walls stop short there
            bx_ = bbox(f.outline)
            return min(bx_[1] - bx_[0], bx_[3] - bx_[2]) >= 2.2 * p['w']
        for i, a in enumerate(ready):
            if a.kind != 'wall' or not framable(a):
                continue
            for b in ready[i + 1:]:
                if b.kind != 'wall' or not framable(b):
                    continue
                for ea, (pa, ta) in enumerate(a.ends):
                    for eb, (pb, tb) in enumerate(b.ends):
                        if math.hypot(pa[0] - pb[0], pa[1] - pb[1]) > tol:
                            continue
                        if v_dot(b.N, ta) > 0.2 and v_dot(a.N, tb) > 0.2:
                            # how high the other wall goes, in this wall's terms: above it there's
                            # nothing to keep clear of, so the frame can run right into the corner
                            Oa = a.tw((0.0, 0.0, 0.0))
                            Va = v_norm(v_sub(a.tw((0.0, 1.0, 0.0)), Oa))
                            hb = max(v_dot(v_sub(b.tw((x_, y_, 0.0)), Oa), Va) / SCALE for x_, y_ in b.outline)
                            if hb < bbox(a.outline)[2] + 2.2 * p['w']:
                                continue           # the edge of a floor or a plinth, not a wall
                            a.inset[ea] = max(a.inset[ea], depth + lift + p.get('gap', 0.0))
                            a.inset_top[ea] = max(a.inset_top[ea], hb)
    gables = []
    if p.get('trusses') and p.get('truss_spacing', 0.0) > p['w']:
        # with trusses, each gable wall's own frame stops at the eaves (a top plate along the top
        # of the wall) and a gable end truss stands on it
        gables = find_gables(ready, p)
        for g in gables:
            for wall in (g['a'], g['b']):
                top = _wall_top(wall, ready)
                ye_ = _gable_eaves(wall.outline)
                if ye_ is not None and (top is None or top < ye_ - max(3.0 * p['w'], 0.25 * (bbox(wall.outline)[3] - ye_))):
                    top = ye_                  # as in find_gables: never cut the gable wall down low
                if top is not None:
                    wall.cut_top = top
        if gables:
            # the trusses hold the roof up, so the roof slopes don't get a frame of their own as
            # well - two frames there would only cut each other up
            nr = len([fi for fi in ready if fi.kind == 'roof'])
            if nr:
                ready = [fi for fi in ready if fi.kind != 'roof']
                p['_roof_by_trusses'] = nr
    names = {'wall': "Wall", 'roof': "Roof", 'flat': "Floor"}
    count = {}
    problems = []
    skipped = [0]
    done = []                      # every bar placed so far, as a solid in the world: (points, edges, bbox)
    wall_panel = {}                # a wall -> where its frame is in panels
    order = {'wall': 0, 'flat': 1, 'roof': 2}
    ready.sort(key=lambda fi: order.get(fi.kind, 3))
    # floors: the bottom of the walls is where the floor levels are measured from
    bands = ledge_bands(p) if p.get('_levels') else []
    lo_ = p['ledge_out']
    walls_ = [fi for fi in ready if fi.kind == 'wall']
    if walls_:
        # only the real walls: not the edges of floor or roof slabs, which are upright faces too
        zz = [(min(fi.tw((x, y, 0.0))[2] for x, y in fi.outline), max(fi.tw((x, y, 0.0))[2] for x, y in fi.outline))
              for fi in walls_]
        zlo, zhi = min(z[0] for z in zz), max(z[1] for z in zz)
        walls_ = [fi for fi, (za_, zb_) in zip(walls_, zz)
                  if za_ <= zlo + 0.25 * (zhi - zlo) and zb_ - za_ >= 2.2 * p['w'] * SCALE and
                  bbox(fi.outline)[1] - bbox(fi.outline)[0] >= 2.2 * p['w']] or walls_
    base_z = p.get('_wall_bottom')
    if base_z is None:
        base_z = min((fi.tw((x, y, 0.0))[2] for fi in walls_ for x, y in fi.outline), default=None)
    p['_base_z'] = base_z
    p['_ledges_made'] = 0
    p['_ledge_low'] = []
    for fi in ready:
        count[fi.kind] = count.get(fi.kind, 0) + 1
        title = "%s %d" % (names[fi.kind], count[fi.kind])
        outline = fi.outline
        x0, x1, _, _ = bbox(outline)
        tops = getattr(fi, 'inset_top', [None, None])
        if fi.inset[0] > 0:
            outline = _notch(outline, 0, x0 + fi.inset[0], tops[0])
        if fi.inset[1] > 0 and outline and len(outline) >= 3:
            outline = _notch(outline, 1, x1 - fi.inset[1], tops[1])
        if outline and getattr(fi, 'cut_top', None) is not None and len(outline) >= 3:
            outline = clip_half(list(outline), 0.0, -1.0, fi.cut_top)
        outline = clean(outline) if outline and len(outline) >= 3 else None
        if outline is None:
            continue
        # this wall's floor ledges, in its own terms
        ledges = []
        if bands and fi.kind == 'wall' and base_z is not None:
            Oz = fi.tw((0.0, 0.0, 0.0))[2]
            dz = fi.tw((0.0, 1.0, 0.0))[2] - Oz           # metres of height per mm up the face
            _x0, _x1, fy0, fy1 = bbox(outline)
            if dz > 1e-12 and fy1 - fy0 >= 2.2 * p['w']:      # not a floor's edge or a plinth
                for za, zb, lname, lv in bands:
                    ya = (base_z + za * SCALE - Oz) / dz
                    yb = (base_z + zb * SCALE - Oz) / dz
                    if yb < fy0 + 0.3 * p['ledge_h']:
                        if lv not in p['_ledge_low']:
                            p['_ledge_low'].append(lv)  # sits on the base - nothing to hold it up
                        continue
                    if ya >= fy1:
                        continue                         # above this wall
                    ledges.append((max(ya, fy0), yb, lname))
        try:
            extra = _clearance(fi, done, lift, lift + depth, p)
            lx = _clearance(fi, done, lift, lift + depth + lo_, p) if ledges else []
            p['_open_top'] = getattr(fi, 'cut_top', None) is not None
            bars = lay_frame(outline, fi.holes, p, fi.kind, extra, ledges, lx)
        except ValueError as e:
            if getattr(fi, 'auto', False) and "too small" in str(e):
                skipped[0] += 1                 # edges of walls and roofs, window reveals...
                count[fi.kind] -= 1
            else:
                problems.append("%s: %s" % (title, e))
            continue
        except Exception as e:
            problems.append("%s: %s" % (title, e))
            continue
        for _n, _t, pcs in bars:
            top_ = p.get('glaze_t', 0.0) if _t == 'glaze' else (depth + lo_ if _t == 'ledge' else depth)
            for pc in pcs:
                done.append(_prism(fi.tw, pc, lift, lift + top_))
                if fi.kind == 'wall':
                    p.setdefault('_wall_bars', []).append(done[-1])
            if _t == 'ledge':
                p['_ledges_made'] += 1
        sols = solids_for(bars, lift, lift + depth, p.get('glaze_t', 0.0), lo_)
        if sols:
            items = []
            for nm, typ, so in sols:
                wso = so.mapped(fi.tw)
                if typ == 'glaze':
                    wso.flat = so                # the same frame lying flat, to set out ready to print
                items.append(("%s - %s" % (title, nm), typ, wso))
            panels.append((title, items))
            wall_panel[id(fi)] = len(panels) - 1
    for fi in chosen:
        if getattr(fi, 'err', None):
            problems.append(fi.err)
    if gables:
        tr, tends, tprob = roof_trusses(gables, p, done)
        for wall, (nm, typ, so) in tends:
            k = wall_panel.get(id(wall))
            if k is not None:
                # joined to the end wall's frame: in that wall's group
                panels[k][1].append(("%s - %s" % (panels[k][0], nm), typ, so))
            else:
                tr.insert(0, (nm, typ, so))
        if tr:
            # the trusses standing loose in the middle: a group of their own, apart from the frame
            panels.append(("Roof trusses", tr))
        problems += tprob
    if p.get('boards') or p.get('roof_panels') or p.get('soffits'):
        gb = gables or find_gables(ready if not gables else ready, p)
        if gb:
            bd, bprob = roof_boards(gb, p)
            if not p.get('boards'):
                bd = [b_ for b_ in bd if b_[1] not in ('fascia', 'barge')]
            rf = [b_ for b_ in bd if b_[1] == 'roof']
            bd = [b_ for b_ in bd if b_[1] != 'roof']
            if bd:
                panels.append(("Boards", bd))
            if rf:
                panels.append(("Roof panels", rf))
            problems += bprob
        else:
            problems.append("Boards: no pair of gable walls facing each other in the selection")
    if bands and p.get('floor_panels') and walls_ and base_z is not None:
        fl, fprob = floor_panels(walls_, p, base_z)
        if fl:
            panels.append(("Floor panels", fl))
        problems += fprob
    p['_skipped'] = skipped[0]
    return panels, problems


def floor_panels(walls, p, base_z):
    """A floor panel for each floor level, cut to drop in inside the frame and rest on the ledges.
    Worked out from the inside faces of the walls, so it needs a building whose plan has no
    inside corners (square, oblong, any straight-sided shape that bulges out)."""
    depth, lift = p['depth'], p.get('lift', 0.0)
    fit = max(0.0, p.get('floor_fit', 0.0))
    back = (lift + depth + fit) * SCALE              # floor edge stands this far off each wall
    ft = p.get('floor_t', 0.0)
    out, problems = [], []
    if ft <= 0:
        return [], ["Floor panels: set the floor thickness first (Floors page)."]
    if fit >= p['ledge_out']:
        problems.append("Floor panels: the fit is as big as the ledge, so the floors wouldn't rest on "
                        "it - make the ledge stick out further.")
    pts = [fi.tw((x, y, 0.0)) for fi in walls for x, y in fi.outline]
    tol = 0.5 * p['w'] * SCALE
    for k, (za, zb, lname, lv) in enumerate(ledge_bands(p)):
        if lv in p.get('_ledge_low', []) or zb < 0.3 * p['ledge_h']:
            continue                                     # sits on the base: draw that floor yourself
        zt = base_z + lv * SCALE
        zbot = zt - ft * SCALE
        # the walls that reach this floor
        here = []
        for fi in walls:
            zs = [fi.tw((x, y, 0.0))[2] for x, y in fi.outline]
            if min(zs) - 1e-9 <= zbot and max(zs) >= zt - 1e-9:
                here.append(fi)
        if len(here) < 3:
            problems.append("Floor %d: not enough walls reach %.0f mm to make a floor panel." % (k + 1, lv))
            continue
        # every wall's inside face must have all the others on its room side (no inside corners)
        convex = True
        for fi in here:
            P, N = fi.tw((0.0, 0.0, 0.0)), fi.N
            for q in pts:
                if (q[0] - P[0]) * N[0] + (q[1] - P[1]) * N[1] < -tol:
                    convex = False
                    break
            if not convex:
                break
        if not convex:
            problems.append("Floor %d: the building has inside corners, so the floor panel isn't made - the "
                            "ledges are there for one you draw yourself." % (k + 1))
            continue
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        m = 1.0 + max(max(xs) - min(xs), max(ys) - min(ys))
        poly = [(min(xs) - m, min(ys) - m), (max(xs) + m, min(ys) - m), (max(xs) + m, max(ys) + m),
                (min(xs) - m, max(ys) + m)]
        for fi in here:
            P, N = fi.tw((0.0, 0.0, 0.0)), fi.N
            L = math.hypot(N[0], N[1]) or 1.0
            a, b = N[0] / L, N[1] / L
            poly = clip_half(poly, a, b, -(a * P[0] + b * P[1]) - back)
            if len(poly) < 3:
                break
        poly = clean(poly) if len(poly) >= 3 else None
        if not poly or abs(area2(poly)) < 1e-12:
            problems.append("Floor %d: no room left for a floor panel inside the frame." % (k + 1))
            continue
        so = slab(poly, lambda x, y, z=zbot: z, lambda x, y, z=zt: z)
        if so is not None:
            out.append(("Floor %d panel" % (k + 1), 'floor', so))
    return out, problems


def _truss_bars(tri, w, style, overhang=0.0, wall_t=0.0, ye_wall=None, stud_sp=0.0, under_roof=False):
    """(bits of the truss, its outline, how far it was raised, rafter tails apart from it).
    The rafter ends past the walls are cut square (plumb), ready for a fascia board. Under a roof
    you've drawn the truss can't be raised, so the rafters run out under the roof as they are;
    where the wall is in the way they're cut round it, and a tail left outside the wall on its own
    comes back as a piece of its own (glue it on under the eaves)."""
    bits, region, lift_ = _truss_bars0(tri, w, style, overhang, wall_t, ye_wall, stud_sp, under_roof)
    if not bits or overhang <= 0:
        return bits, region, lift_, []
    x0, x1 = bbox(tri)[0], bbox(tri)[1]
    xl, xr = x0 - overhang, x1 + overhang

    def square(pcs):
        res = []
        for pc in pcs:
            q = clip_half(list(pc), 1.0, 0.0, -xl)
            q = clip_half(q, -1.0, 0.0, xr) if len(q) >= 3 else []
            q = clean(q) if len(q) >= 3 else None
            if q and abs(area2(q)) > 1e-6 * w * w:
                res.append(q)
        return res
    bits = square(bits)
    # and nothing hangs down below the top of the walls: the rafter tails stay level with the wall
    # top on their underside past the wall, with no notch round the wall's outside edge
    yw = bbox(tri)[2] if ye_wall is None else min(ye_wall, bbox(tri)[2])
    flat = []
    for pc in bits:
        q = clip_half(list(pc), 0.0, 1.0, -yw)
        q = clean(q) if len(q) >= 3 else None
        if q and abs(area2(q)) > 1e-6 * w * w:
            flat.append(q)
    bits = flat
    reg = square([region])
    region = reg[0] if reg else region
    tails = []
    if under_roof and wall_t > 0:
        yw = ye_wall if ye_wall is not None else bbox(tri)[2]
        lo = bbox([q for pc in bits for q in pc])[2] - 1.0
        walls = [_box(x0 - wall_t, lo, x0, yw), _box(x1, lo, x1 + wall_t, yw)]
        bits = [pc for pc in cut_away(bits, walls) if abs(area2(pc)) > 1e-6 * w * w]
        comps = _components(bits, 1e-3 * w)
        if len(comps) > 1:
            main = max(comps, key=lambda c: sum(abs(area2(pc)) for pc in c))
            bits = list(main)
            for c in comps:
                if c is main:
                    continue
                cx = bbox([q for pc in c for q in pc])
                if cx[1] <= x0 + 1e-6 or cx[0] >= x1 - 1e-6:
                    if sum(abs(area2(pc)) for pc in c) > 0.15 * w * w:
                        tails.append(c)
                else:
                    bits += c
    return bits, region, lift_, tails


def _truss_bars0(tri, w, style, overhang=0.0, wall_t=0.0, ye_wall=None, stud_sp=0.0, under_roof=False):
    """The bars of one truss, flat in the gable's terms: a tie along the bottom, a rafter up each
    slope and (by style) a king post and struts.

    With an overhang the rafters run on past the walls and down, for the tiles to hang over the
    gutters - in one piece with the rest of the truss, so it prints as one. For a rafter to pass
    over the top of a wall in one piece, its underside has to clear the outside edge of the wall
    top, so the truss is raised just that much, with a packer under each end of the tie standing
    on the wall plate. Returns (bits, outline of the whole truss, how far it was raised)."""
    x0, x1, y0, y1 = bbox(tri)
    top = max(tri, key=lambda q: q[1])
    tol = 1e-6 * (y1 - y0) + 1e-6
    eaves = sorted(q for q in tri if abs(q[1] - y0) < tol)
    if len(eaves) < 2:
        return [], tri, 0.0
    el, er = eaves[0], eaves[-1]
    sl = (top[1] - el[1]) / max(1e-9, top[0] - el[0])
    sr = (top[1] - er[1]) / max(1e-9, er[0] - top[0])
    ye = el[1]
    if ye_wall is None or ye_wall > ye:
        ye_wall = ye
    lift_ = 0.0
    if overhang > 0 and wall_t > 0 and not under_roof:
        need = []
        for s_ in (sl, sr):
            deep = w * math.sqrt(1.0 + s_ * s_)              # the rafter's depth, measured upright
            at_out = ye - wall_t * s_                        # the roof line over the outside of the wall
            need.append(deep - (at_out - ye_wall))
        lift_ = max(0.0, max(need))
    up = lambda q: (q[0], q[1] + lift_)
    el_, er_, top_ = up(el), up(er), up(top)
    region = [up(q) for q in tri]
    tl, tr_ = el_, er_
    if overhang > 0:
        # carry each slope on down past the wall by the overhang - and a bit more, cut off square
        # (plumb) afterwards for the fascia board
        ext = overhang + 3.0 * w
        tl = (el_[0] - ext, el_[1] - ext * sl)
        tr_ = (er_[0] + ext, er_[1] - ext * sr)
        region = clean([tl, tr_, top_])
    tri_reg = region                                      # the rafters' outline (the common truss)
    if style == 'gable':
        # a gable end truss: the same rafters as the common trusses (so the roof line and the
        # overhang match), but filled in down to the end wall's top plate like a framed wall
        region = clean([(el_[0], ye_wall), (er_[0], ye_wall), er_, top_, el_])
        if not region:
            return [], tri_reg, lift_
    parts_r = convex_parts(tri_reg)
    parts_g = convex_parts(region) if style == 'gable' else parts_r
    if not parts_r or not parts_g:
        return [], region, lift_
    placed, out = [], []

    def put(poly, parts=None, clip=True, square=True):
        if not poly:
            return
        pcs = clip_to(poly, parts or parts_r) if clip else [poly]
        pcs = cut_away(pcs, placed)
        pcs = [pc for pc in pcs if abs(area2(pc)) > 1e-6 * w * w]
        if square:
            pcs = _square_bar(pcs, _axis(poly), w)
        out.extend(pcs)
        placed.extend(pcs)
    if style == 'gable':
        # a bottom rail sitting right down on the end wall's top plate
        put(_box(el_[0], ye_wall, er_[0], ye_wall + w), parts_g)
    else:
        put(_box(el_[0], el_[1], er_[0], el_[1] + w))      # the tie, wall to wall
    n = len(tri_reg)
    for i in range(n):                                     # the rafters: the sloping sides
        a, b = tri_reg[i], tri_reg[(i + 1) % n]
        if abs(b[1] - a[1]) > tol and abs(b[0] - a[0]) > tol:
            # never squared off: where the tie or bottom rail takes most of a rafter's depth, what's
            # left of the rafter above it is still needed, or the top of the truss gets a notch
            put(_strip(a, b, 0.0, w), square=False)
    if style in ('king', 'struts'):
        put(_box(top_[0] - w / 2.0, el_[1], top_[0] + w / 2.0, top_[1]))
    if style == 'struts':
        foot = (top_[0], el_[1] + w)
        for eave in (el_, er_):
            # from the foot of the king post up to the middle of each rafter
            mid = ((eave[0] + top_[0]) / 2.0, (eave[1] + top_[1]) / 2.0)
            put(_strip(foot, mid, -w / 2.0, w / 2.0))
    def seat():
        # fill the notch under each rafter where it passes over the wall: the truss sits flat on
        # the whole of the wall top, from the outside edge in, with no gap under the rafter
        if overhang <= 0 or wall_t <= 0 or lift_ <= 1e-3:
            return
        for x_in, s_, sgn in ((el_[0], sl, -1.0), (er_[0], sr, 1.0)):
            deep = w * math.sqrt(1.0 + s_ * s_)
            ex = el_ if sgn < 0 else er_
            under = lambda x: ex[1] - abs(x - x_in) * s_ - deep if sgn * (x - x_in) > 0 else ex[1] - deep
            xo, xi = x_in + sgn * wall_t, x_in - sgn * w
            poly = clean([(xo, ye_wall), (xi, ye_wall), (xi, max(ye_wall, under(xi)) + w),
                          (xo, max(ye_wall, under(xo)) + 0.5 * w)])
            if poly:
                put(poly, clip=False)
    if style == 'gable':
        seat()
        # an end post over each side wall, then upright studs up to the rafters, like a gable wall
        put(_box(el_[0], ye_wall, el_[0] + w, el_[1] + w), parts_g)
        put(_box(er_[0] - w, ye_wall, er_[0], er_[1] + w), parts_g)
        span = er_[0] - el_[0] - 2.0 * w
        cnt = int(round(span / max(stud_sp, 2.0 * w))) - 1
        for k in range(1, cnt + 1):
            xc = el_[0] + w + span * k / (cnt + 1.0)
            put(_box(xc - w / 2.0, ye_wall, xc + w / 2.0, top_[1] + w), parts_g)
        hull = convex_hull([q for pc in out for q in pc]) or region
        return out, hull, lift_
    if el_[1] - ye_wall > 1e-3:
        # packers under the ends of the tie, standing on the wall plates
        put(_box(el_[0], ye_wall, el_[0] + w, el_[1]), clip=False)
        put(_box(er_[0] - w, ye_wall, er_[0], er_[1]), clip=False)
    seat()
    return out, region, lift_


def board_sizes(p):
    """The board sizes, with 0 meaning 'work it out from the bar width'."""
    w = p['w']
    fh = p.get('fascia_h', 0.0) or 1.25 * w
    bt = p.get('board_t', 0.0) or 0.5 * w
    bw = p.get('barge_w', 0.0) or fh
    fnh = p.get('finial_h', 0.0) or 2.0 * w
    fnd = p.get('finial_drop', 0.0) or w
    fnw = p.get('finial_w', 0.0) or 0.8 * w
    return fh, bt, max(0.0, p.get('board_off', 0.0)), bw, fnh, fnd, fnw


def roof_sizes(p):
    """Roof panel thickness and how far it hangs past the fascia into the gutter (0 = worked out)."""
    bt = board_sizes(p)[1]
    return (p.get('roof_t', 0.0) or bt), (p.get('roof_over', 0.0) or bt)


def roof_boards(gables, p):
    """Fascia boards along the eaves and barge boards up the gables, with a finial at each peak.
    Every board stands off the walls by X, leaving room for brick courses (or render) on the walls.
    The fascia sits on the square-cut ends of the truss rafters; the barge boards follow the roof
    line, stand off the gable wall, and cover the ends of the fascia boards. Each one is a piece of
    its own, laid out to print flat. Returns ([(name, type, solid)], problems)."""
    fh, bt, off, bw, fnh, fnd, fnw = board_sizes(p)
    out, problems = [], []
    for k, g in enumerate(gables):
        a, tri, D = g['a'], g['tri'], g['D']
        lift = g.get('lift', 0.0) or 0.0
        ovh = g.get('ovh', max(0.0, p.get('truss_overhang', 0.0))) or 0.0
        wall_t = _wall_thickness(a, p.get('_all_faces')) or 0.0
        x0, x1, y0, y1 = bbox(tri)
        top = max(tri, key=lambda q: q[1])
        eav = sorted(q for q in tri if abs(q[1] - y0) < 1e-6 * (y1 - y0) + 1e-6)
        if len(eav) < 2:
            continue
        el, er = eav[0], eav[-1]
        sl = (top[1] - el[1]) / max(1e-9, top[0] - el[0])
        sr = (top[1] - er[1]) / max(1e-9, er[0] - top[0])
        apex = (top[0], top[1] + lift)

        def T(x):                                   # the top of the roof line (the rafters' top)
            return apex[1] - (apex[0] - x) * sl if x <= apex[0] else apex[1] - (x - apex[0]) * sr
        # the fascia's back: on the ends of the rafters - but never nearer the wall than the stand-off
        need = wall_t + off
        reach = ovh if ovh > 0 else 0.0
        if reach < need - 1e-6:
            if p.get('trusses'):
                problems.append("Boards: the truss overhang (Q %.0f mm) doesn't reach past the wall and the "
                                "stand-off (X) - make Q at least %.0f mm for the fascia to sit on the rafter ends."
                                % (reach, need))
            reach = need
        xl, xr = el[0] - reach, er[0] + reach              # the backs of the two fascia boards
        z_in = -(wall_t + off)                             # the gable end's barge boards stand out here
        zb_in = D + wall_t + off
        # ---- fascia boards, one along each eaves, from barge board to barge board
        yw_ = min(g.get('ye_wall') if g.get('ye_wall') is not None else y0, y0)   # top of the walls
        for side, xb, sgn, xw in (("left", xl, -1.0, el[0] - wall_t - off), ("right", xr, 1.0, er[0] + wall_t + off)):
            ytop = T(xb + sgn * bt)        # its top at the roof line on its outside face, so the roof
                                             # panel (or the tiles) can lie over it
            sec = _box(min(xb, xb + sgn * bt), ytop - fh, max(xb, xb + sgn * bt), ytop)
            secs, nm = [sec], "Fascia board %s (%d)" % (side, k + 1)
            if p.get('soffits') and sgn * (xb - xw) > 1e-6:
                # the soffit joined on: fascia and soffit as one L-shaped piece, ready to print
                st_ = min(yw_, ytop - fh + bt)
                sof = _box(min(xb, xw), st_ - bt, max(xb, xw), st_)
                if sof:
                    secs.append(sof)
                    nm = "Fascia and soffit %s (%d)" % (side, k + 1)
            so = merged_slab([q for q in secs if q], lambda x, y, z=z_in: z, lambda x, y, z=zb_in: z)
            if so is None:
                continue
            out.append((nm, 'fascia', so.mapped(lambda q, a=a: a.tw((q[0], q[1], q[2])))))
        # ---- barge boards and finial, one piece at each gable end
        xa_, xb_ = xl - bt, xr + bt                         # they cover the ends of the fascias
        ext = 3.0 * bw
        L = (xa_ - ext, T(xa_) - ext * sl)
        R = (xb_ + ext, T(xb_) - ext * sr)
        rt, rov = roof_sizes(p)
        up_ = rt if p.get('roof_panels') else 0.0          # with roof panels, the barge boards cover their edge
        pcs = [q for q in (_strip(L, apex, -bw, up_), _strip(apex, R, -bw, up_)) if q]
        # the left strip lies under its line when drawn left to right, so flip the sign if needed
        pcs = [q if any(q_[1] < T(q_[0]) - 1e-6 for q_ in q) else
               _strip(*((L, apex) if i == 0 else (apex, R)), -up_, bw) for i, q in enumerate(pcs)]
        pcs = [q for q in pcs if q]
        cut = []
        for q in pcs:
            q = clip_half(list(q), 1.0, 0.0, -xa_)
            q = clip_half(q, -1.0, 0.0, xb_) if len(q) >= 3 else []
            q = clean(q) if len(q) >= 3 else None
            if q:
                cut.append(q)
        pcs = cut_away([cut[0]], []) + (cut_away(cut[1:], [cut[0]]) if len(cut) > 1 else [])
        # box ends: at the eaves the barge board comes down square round the end of the fascia - its
        # front flush with the fascia's face, its bottom level with the fascia's bottom - instead of
        # ending in a point hanging down past it
        for xo_, sgn_, s_ in ((xa_, 1.0, sl), (xb_, -1.0, sr)):
            fb_ = T(xo_) - fh                                   # the fascia's bottom
            ln_ = bw * math.sqrt(1.0 + s_ * s_) + bt            # how far the box runs in along the slope
            xi_ = xo_ + sgn_ * ln_
            bx_ = clean([(xo_, fb_), (xi_, fb_), (xi_, T(xi_) + up_), (xo_, T(xo_) + up_)])
            keep_ = []
            for q in pcs:                                      # nothing hangs below the fascia there
                if sgn_ * (bbox(q)[0 if sgn_ > 0 else 1] - xi_) < 0:
                    lo_ = clip_half(list(q), 0.0, 1.0, -fb_)
                    lo_ = clean(lo_) if len(lo_) >= 3 else None
                    if lo_:
                        keep_.append(lo_)
                else:
                    keep_.append(q)
            pcs = keep_
            if bx_:
                pcs = cut_away(pcs, [bx_]) + [bx_] if is_convex(bx_) else pcs + [bx_]
        # the finial: a post up through the peak, standing above it and hanging below
        fin = _box(apex[0] - fnw / 2.0, apex[1] - bw * math.sqrt(1 + sl * sl) - fnd,
                   apex[0] + fnw / 2.0, apex[1] + fnh)
        if fin:
            pcs = cut_away(pcs, [fin]) + [fin]
        pcs = [q for q in pcs if q and abs(area2(q)) > 1e-6]
        for end, (za, zb) in (("near", (z_in - bt, z_in)), ("far", (zb_in, zb_in + bt))):
            so = merged_slab(pcs, lambda x, y, z=za: z, lambda x, y, z=zb: z)
            if so is None:
                continue
            out.append(("Barge boards and finial - %s end (%d)" % (end, k + 1), 'barge',
                        so.mapped(lambda q, a=a: a.tw((q[0], q[1], q[2])))))
        mapw = lambda so_, a=a: so_.mapped(lambda q: a.tw((q[0], q[1], q[2])))
        # ---- soffit boards: level boards under the eaves, from the brick face out to the fascia
        if p.get('soffits') and not p.get('boards'):
            # soffits on their own (no fascia boards to join them to)
            yw = min(g.get('ye_wall') if g.get('ye_wall') is not None else y0, y0)   # top of the walls
            for side, xb, xw, sgn in (("left", xl, el[0] - wall_t - off, -1.0),
                                      ("right", xr, er[0] + wall_t + off, 1.0)):
                if sgn * (xb - xw) <= 1e-6:
                    continue                       # the fascia is right on the bricks: no soffit
                ytop_ = min(yw, T(xb + sgn * bt) - fh + bt)
                sec = _box(min(xb, xw), ytop_ - bt, max(xb, xw), ytop_)
                so = merged_slab([sec], lambda x, y, z=z_in: z, lambda x, y, z=zb_in: z) if sec else None
                if so is not None:
                    out.append(("Soffit board %s (%d)" % (side, k + 1), 'soffit', mapw(so)))
        # ---- roof panels: plain boards on the trusses, one each side, to put the tiles on. They
        # follow the slope of the trusses and hang past the fascia into the gutter
        if p.get('roof_panels'):
            for side, xe, s_ in (("left", xl - bt - rov, sl), ("right", xr + bt + rov, sr)):
                h_ = rt * math.sqrt(1.0 + s_ * s_)
                sec = clean([(xe, T(xe)), (apex[0], apex[1]), (apex[0], apex[1] + h_), (xe, T(xe) + h_)])
                so = merged_slab([sec], lambda x, y, z=z_in: z, lambda x, y, z=zb_in: z) if sec else None
                if so is not None:
                    out.append(("Roof panel %s (%d)" % (side, k + 1), 'roof', mapw(so)))
    return out, problems


def _wall_thickness(fi, all_faces):
    """How thick a wall is: the distance to the face on its other side (0 if there isn't one)."""
    best = 0.0
    for o in all_faces or ():
        if not getattr(o, 'ok', False) or o is fi or v_dot(o.n, fi.N) > -0.98:
            continue
        d = v_dot(v_sub(fi.tw((0.0, 0.0, 0.0)), o.pts[0]), o.n) / SCALE
        d = -d
        if 1.0 < d <= 600.0 and (best == 0.0 or d < best):
            best = d
    return best


def _bar_w_guess(a):
    try:
        return float(getattr(a, 'w', 0.0) or 0.0)
    except Exception:
        return 0.0


def _wall_top(a, ready):
    """How high the walls running across the ends of wall a go, in a's terms (None if none)."""
    Oa = a.tw((0.0, 0.0, 0.0))
    Ua = v_norm(v_sub(a.tw((1.0, 0.0, 0.0)), Oa))
    Va = v_norm(v_sub(a.tw((0.0, 1.0, 0.0)), Oa))
    x0, x1, y0, y1 = bbox(a.outline)
    ye = _gable_eaves(a.outline)
    tops = []
    for c_ in ready:
        if c_ is a or c_.kind != 'wall' or abs(v_dot(c_.N, a.N)) >= 0.5:
            continue
        pts = [c_.tw((x_, y_, 0.0)) for x_, y_ in c_.outline]
        hs = [v_dot(v_sub(q, Oa), Va) / SCALE for q in pts]
        xs = [v_dot(v_sub(q, Oa), Ua) / SCALE for q in pts]
        # only real walls: standing on the ground like a, at one of its ends - not the edge of a
        # roof slab at the ridge (that used to count, and stopped the gable being cut at the eaves,
        # so the gable end trusses were cut away by the gable's own frame) or a floor's edge
        if min(hs) > y0 + 0.25 * (y1 - y0) or max(hs) - min(hs) < 0.3 * (y1 - y0):
            continue
        # 1.34: a real side wall runs away from the gable, along the building. The narrow end of the
        # gable wall itself (as thick as the wall) is upright too, and its top rises with the gable over
        # the wall's thickness - counting it stood the trusses up off the real side walls
        ds = [v_dot(v_sub(q, Oa), a.N) / SCALE for q in pts]
        if max(ds) - min(ds) < max(700.0, 3.0 * _bar_w_guess(a)):
            continue
        if min(abs(xm - x0) for xm in (min(xs), max(xs))) > 700.0 and \
                min(abs(xm - x1) for xm in (min(xs), max(xs))) > 700.0:
            continue
        tops.append(max(hs))
    if not tops:
        return None
    top = max(tops)
    if ye is not None and top > ye + 1e-3:
        top = ye                         # never above where the gable's slopes start
    return top


def _gable_eaves(o):
    """If outline o is a gable (sloping edges along its top, up to a peak), the height where the
    slopes start - else None. The curve of an arched opening slopes too, but has wall above it."""
    x0, x1, y0, y1 = bbox(o)
    rake = []
    for k in range(len(o)):
        q1, q2 = o[k], o[(k + 1) % len(o)]
        L_ = math.hypot(q2[0] - q1[0], q2[1] - q1[1])
        if L_ < 1e-9:
            continue
        sl = abs(q2[1] - q1[1]) / L_
        if 0.1 < sl < 0.98 and q2[0] < q1[0] and min(q1[1], q2[1]) > y0 + 0.4 * (y1 - y0):
            rake.append((q1, q2))
    if not rake or max(max(e[0][1], e[1][1]) for e in rake) < y1 - 1e-6:
        return None
    return min(min(e[0][1], e[1][1]) for e in rake)


def find_gables(ready, p):
    """Every pair of gable walls facing each other: [{a, b, tri (a's gable above the eaves),
    ye_wall (top of the side walls), D (how far apart)}]."""
    d = p['depth']
    out, used = [], set()
    for i, a in enumerate(ready):
        if a.kind != 'wall' or id(a) in used:
            continue
        o = a.outline
        x0, x1, y0, y1 = bbox(o)
        ye = _gable_eaves(o)
        if ye is None:
            continue
        Oa = a.tw((0.0, 0.0, 0.0))
        best = None
        for b in ready[i + 1:]:
            if b.kind != 'wall' or id(b) in used or v_dot(a.N, b.N) > -0.99 or _gable_eaves(b.outline) is None:
                continue
            D = v_dot(v_sub(b.tw((0.0, 0.0, 0.0)), Oa), a.N) / SCALE      # how far apart, inside
            if D <= 3.0 * d:
                continue
            ar = abs(area2(b.outline))
            if best is None or ar > best[0]:
                best = (ar, b, D)
        if best is None:
            continue
        _ar, b, D = best
        tri = clip_half(list(o), 0.0, 1.0, -ye)
        tri = clean(tri) if len(tri) >= 3 else None
        if not tri:
            continue
        used.add(id(a))
        used.add(id(b))
        # the trusses stand on the side walls' top plates. If that comes out well down the gable
        # (only something low, like an opening's side, was found across the end) the trusses
        # would sink down into the walls - so they stand on the gable's eaves line instead
        ye_wall = _wall_top(a, ready)
        # 1.33: say what the trusses stand on, so a gap under them can be tracked down
        if ye_wall is None:
            p.setdefault('_truss_seat', []).append("side walls not found - stood on the gable's eaves line")
        elif ye_wall < ye - max(3.0 * p['w'], 0.25 * (y1 - ye)):
            p.setdefault('_truss_seat', []).append(
                "side walls found %.0f mm below the gable's eaves - too far, so stood on the eaves line" % (ye - ye_wall))
        else:
            p.setdefault('_truss_seat', []).append(
                "on the side walls' top, %.0f mm below the gable's eaves" % max(0.0, ye - ye_wall))
        if ye_wall is None or ye_wall < ye - max(3.0 * p['w'], 0.25 * (y1 - ye)):
            ye_wall = ye
        out.append(dict(a=a, b=b, tri=tri, ye_wall=ye_wall, D=D, size=(x1 - x0, y1 - y0), ye=ye))
    return out


def roof_trusses(gables, p, done):
    """Pointed roof trusses for each pair of gables: a gable end truss against each end wall
    (upright studs inside, standing past the gable line like a barge board) and common trusses
    spaced evenly between them - all the same outline, so they line up. Each one flat piece."""
    w, d, lift = p['w'], p['depth'], p.get('lift', 0.0)
    sp = p['truss_spacing']
    style = p.get('truss_style', 'struts')
    ovh = max(0.0, p.get('truss_overhang', 0.0))
    # like real eaves: the rafters pass over the top of the wall in one piece, out to the fascia.
    # Where the roof you've drawn sits right on the walls that means the trusses stand higher than
    # it, so the report says how far to move the roof up to sit on them.
    under_roof = False
    if ovh > 0 and any(getattr(fi, 'ok', False) and fi.kind == 'roof' for fi in p.get('_all_faces') or ()):
        p['_roof_drawn'] = True
    out, problems = [], []
    ends = []                      # (the end wall it stands against, gable end truss)
    num = 0
    for g in gables:
        a, tri, D, ye_wall = g['a'], g['tri'], g['D'], g['ye_wall']
        wall_t = _wall_thickness(a, p.get('_all_faces'))
        el_x, er_x = bbox(tri)[0], bbox(tri)[1]
        ssp = p.get('spacing', 0.0)
        ssp = ssp if ssp > 2.0 * w else max(4.0 * w, (er_x - el_x) / 6.0)
        common, region, raised, tails_c = _truss_bars(tri, w, style, ovh, wall_t, ye_wall, under_roof=under_roof)
        gable_bars, region_g, _r, tails_g = _truss_bars(tri, w, 'gable', ovh, wall_t, ye_wall, ssp, under_roof)
        if tails_c or tails_g:
            p['_truss_tails'] = True
        g['lift'] = raised
        g['ovh'] = ovh
        if raised > 0.5:
            p['_truss_raised'] = raised
        if not common:
            problems.append("Roof trusses: the gable is too small for bars that size")
            continue
        # the end trusses stand in the end walls' frame layer; the common ones evenly between
        z_a, z_b = lift + d / 2.0, D - lift - d / 2.0
        cnt = max(0, int(round((z_b - z_a) / sp)) - 1)
        spots = [(z_a, True)] + [(z_a + (z_b - z_a) * k / (cnt + 1.0), False) for k in range(1, cnt + 1)] + \
                [(z_b, True)]
        for si_, (z, is_end) in enumerate(spots):
            bars, reg = (gable_bars, region_g) if is_end and gable_bars else (common, region)
            if is_end and bars:
                # a window up in the gable (a loft window): the end truss is framed round it
                wall = a if si_ == 0 else g['b']
                bars = _round_loft_openings(bars, reg, _loft_openings(a, wall, ye_wall, p), w, ye_wall)

            def tw(q, z=z, a=a):
                return a.tw((q[0], q[1], q[2] + z - d / 2.0))
            holder = FaceInfo.__new__(FaceInfo)
            holder.tw, holder.outline = tw, reg
            extra = _clearance(holder, done, 0.0, d, p)
            pcs = cut_away(list(bars), extra) if extra else list(bars)
            pcs = [pc for pc in pcs if abs(area2(pc)) > 1e-6 * w * w]
            if not pcs:
                continue
            so = merged_slab(pcs, lambda x, y: 0.0, lambda x, y: d)
            if so is None:
                continue
            # never hand the model anything silly: a truss must sit inside the gable's size
            bx_ = bbox([q for pc in pcs for q in pc])
            if any(abs(c_) > 1e6 for f in so.faces for q in f for c_ in q) or \
                    bx_[1] - bx_[0] > g['size'][0] + 2.0 * ovh + 4.0 * w or \
                    bx_[3] - bx_[2] > g['size'][1] + 2.0 * ovh + 4.0 * w + (raised or 0.0):
                problems.append("Roof trusses: left one out - its shape didn't make sense")
                continue
            if is_end:
                # a gable end truss goes in with its end wall's frame
                ends.append((a if si_ == 0 else g['b'], ("Gable end truss", 'truss', so.mapped(tw))))
            else:
                num += 1
                out.append(("Roof truss %d" % num, 'truss', so.mapped(tw)))
            for pc in pcs:
                done.append(_prism(tw, pc, 0.0, d))
            # rafter tails cut off by the walls (roof drawn on the walls): pieces of their own
            for k_, tl_ in enumerate(tails_g if is_end else tails_c):
                tp = cut_away(list(tl_), extra) if extra else list(tl_)
                tp = [pc for pc in tp if abs(area2(pc)) > 1e-6 * w * w]
                tso = merged_slab(tp, lambda x, y: 0.0, lambda x, y: d) if tp else None
                if tso is None:
                    continue
                side_ = "left" if bbox([q for pc in tp for q in pc])[0] < bbox(reg)[0] + 0.5 * (
                    bbox(reg)[1] - bbox(reg)[0]) else "right"
                if is_end:
                    ends.append((a if si_ == 0 else g['b'], ("Gable end truss - rafter tail %s" % side_, 'truss',
                                                             tso.mapped(tw))))
                else:
                    out.append(("Roof truss %d - rafter tail %s" % (num, side_), 'truss', tso.mapped(tw)))
                for pc in tp:
                    done.append(_prism(tw, pc, 0.0, d))
    if p.get('trusses') and not out and not ends and not problems:
        problems.append("Roof trusses: no pair of gable walls facing each other in the selection")
    return out, ends, problems


def _loft_openings(a, wall, ye_wall, p):
    """The openings in an end wall that reach up above the eaves (into the gable), as boxes in
    wall a's terms (the gable the trusses are laid out on), with the room round them."""
    O = a.tw((0.0, 0.0, 0.0))
    U = v_norm(v_sub(a.tw((1.0, 0.0, 0.0)), O))
    V = v_norm(v_sub(a.tw((0.0, 1.0, 0.0)), O))

    def to_a(q):
        P = wall.tw((q[0], q[1], 0.0))
        d_ = v_sub(P, O)
        return (v_dot(d_, U) / SCALE, v_dot(d_, V) / SCALE)
    sb = max(0.0, p.get('rebate', 0.0)) if p.get('openings', True) else 0.0
    out = []
    for hl in getattr(wall, 'holes', ()) or ():
        pts = [to_a(q) for q in hl]
        if len(pts) < 3:
            continue
        x0, x1, y0, y1 = bbox(pts)
        if y1 + sb <= ye_wall + 1e-3:
            continue                     # down in the wall: the wall's own frame goes round it
        out.append((x0 - sb, y0 - sb, x1 + sb, y1 + sb))
    return out


def _round_loft_openings(bars, region, opens, w, ybase=None):
    """Cuts the gable end truss clear of loft windows, and puts a post each side, a lintel over
    and a sill under each one - all in the one truss piece."""
    if not opens:
        return bars
    parts = convex_parts(region)
    if not parts:
        return bars
    holes = [_box(L, B, R, T) for L, B, R, T in opens]
    out = cut_away(list(bars), holes)
    out = [pc for pc in out if abs(area2(pc)) > 1e-6 * w * w]
    ys = [q[1] for pc in parts for q in pc]
    ylo, yhi = min(ys), max(ys)
    if ybase is not None:
        ylo = max(ylo, ybase)            # the posts stand on the bottom rail, not down past it
    for L, B, R, T in opens:
        for bar in (_box(L - w, ylo, L, yhi), _box(R, ylo, R + w, yhi),
                    _box(L - w, T, R + w, T + w), _box(L - w, B - w, R + w, B)):
            if not bar:
                continue
            pcs = clip_to(bar, parts)
            pcs = cut_away(pcs, holes + out)
            out += [pc for pc in pcs if abs(area2(pc)) > 1e-6 * w * w]
    return out


def _prism(tw, pc, z0, z1):
    """A bar bit as a solid in the world: its corners, its edges and its box."""
    n = len(pc)
    pts = [tw((x, y, z0)) for x, y in pc] + [tw((x, y, z1)) for x, y in pc]
    edges = [(i, (i + 1) % n) for i in range(n)] + [(n + i, n + (i + 1) % n) for i in range(n)] + \
            [(i, n + i) for i in range(n)]
    lo = tuple(min(q[k] for q in pts) for k in range(3))
    hi = tuple(max(q[k] for q in pts) for k in range(3))
    return pts, edges, (lo, hi)


def _clearance(fi, done, z0, z1, p):
    """Where bars already placed on other faces pass through this face's frame layer, as flat
    shapes on this face - the new bars are cut back clear of them, so nothing overlaps where
    walls meet roofs, at the ridge or along hips."""
    if not done:
        return []
    tw = fi.tw
    O = tw((0.0, 0.0, 0.0))
    U, V, N = (v_sub(tw(e), O) for e in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
    su, sv, sn = v_dot(U, U), v_dot(V, V), v_dot(N, N)
    x0, x1, y0, y1 = bbox(fi.outline)
    box = [tw((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    blo = tuple(min(q[k] for q in box) for k in range(3))
    bhi = tuple(max(q[k] for q in box) for k in range(3))
    eps = 1e-9 + 1e-6 * max(abs(c) for c in blo + bhi)
    gap = p.get('gap', 0.0)
    out = []
    for pts, edges, (lo, hi) in done:
        if any(hi[k] < blo[k] - eps or lo[k] > bhi[k] + eps for k in range(3)):
            continue
        loc = [(v_dot(v_sub(q, O), U) / su, v_dot(v_sub(q, O), V) / sv, v_dot(v_sub(q, O), N) / sn) for q in pts]
        # a bar only touching this frame layer (the next wall's plate meeting it at a corner)
        # doesn't count: a hair's breadth in, from rounding, used to cut the corner out of plates
        za, zb = z0 + 0.01, z1 - 0.01
        got = [(q[0], q[1]) for q in loc if za <= q[2] <= zb]
        for i, j in edges:
            a, b = loc[i], loc[j]
            for zc in (za, zb):
                if (a[2] - zc) * (b[2] - zc) < 0:
                    t = (zc - a[2]) / (b[2] - a[2])
                    got.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
        if len(got) < 3:
            continue
        h = convex_hull(got)
        if h:
            # square it off when it's near enough a rectangle (a plate or post from the next wall),
            # so bars are cut square, not at a slant
            bx = bbox(h)
            rect = _box(bx[0], bx[2], bx[1], bx[3])
            if rect and abs(area2(rect)) <= 1.3 * abs(area2(h)):
                h = rect
        if h and abs(area2(h)) > 1e-4 * p['w'] * p['w']:
            out.append(grow(h, gap) if gap > 0 else h)
    return out


# ---------------------------------------------------------------------------
# Along lines: bars following selected lines, butt-jointed at right angles
# ---------------------------------------------------------------------------
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


def runs_of(lines, w):
    """Joins the selected lines into runs: [(points, closed)]. A run carries on through a corner
    that turns only a little (the facets of an arch or a curve, so a curve is one bent bar) and
    straight on through a crossing. It stops at a real corner, and where a long straight line
    meets the short facets of a curve, so a post and the arch on it are separate pieces."""
    tol = 1e-7
    key = lambda q: (round(q[0] / tol), round(q[1] / tol), round(q[2] / tol))
    pos, adj = {}, {}
    segs = []
    for a, b in lines:
        ka, kb = key(a), key(b)
        if ka == kb:
            continue
        pos.setdefault(ka, a)
        pos.setdefault(kb, b)
        i = len(segs)
        segs.append((ka, kb))
        adj.setdefault(ka, []).append(i)
        adj.setdefault(kb, []).append(i)
    wm = w * SCALE

    def other(si, k):
        a, b = segs[si]
        return b if a == k else a

    def direction(k_from, k_to):
        return v_norm(v_sub(pos[k_to], pos[k_from]))

    def length(si):
        a, b = segs[si]
        return v_len(v_sub(pos[b], pos[a]))

    def carries_on(k, si_in, si_out):
        """Does a run coming in along si_in carry on along si_out at node k?"""
        d_in = direction(other(si_in, k), k)
        d_out = direction(k, other(si_out, k))
        c = v_dot(d_in, d_out)
        if c < math.cos(math.radians(30.0)):
            return False                                   # a real corner
        if c > math.cos(math.radians(3.0)):
            return True                                    # straight on
        la, lb = length(si_in), length(si_out)
        if max(la, lb) > 3.0 * min(la, lb) and max(la, lb) > 4.0 * wm:
            return False                                   # a long straight line meeting a curve
        return True

    def next_seg(k, si_in):
        cand = [j for j in adj[k] if j != si_in and not used[j] and carries_on(k, si_in, j)]
        if len(cand) == 1 and (len(adj[k]) == 2 or v_dot(direction(other(si_in, k), k),
                                                          direction(k, other(cand[0], k))) > 0.999):
            return cand[0]
        return None

    used = [False] * len(segs)
    out = []

    def walk(start_k, si):
        ks = [start_k]
        k = start_k
        while si is not None and not used[si]:
            used[si] = True
            k = other(si, k)
            ks.append(k)
            si = next_seg(k, si)
        return ks

    def can_extend_back(k, si):
        return any(not used[j] and j != si and carries_on(k, j, si) for j in adj[k])
    # start where a run can't be carried on backwards (free ends, real corners), then loops
    for si in range(len(segs)):
        if used[si]:
            continue
        a, b = segs[si]
        if not can_extend_back(a, si):
            out.append(walk(a, si))
        elif not any(not used[j] and j != si and carries_on(b, j, si) for j in adj[b]):
            out.append(walk(b, si))
    for si in range(len(segs)):
        if not used[si]:
            out.append(walk(segs[si][0], si))
    res = []
    for ks in out:
        closed = len(ks) > 3 and ks[0] == ks[-1]
        if closed:
            ks = ks[:-1]
        res.append(([pos[k] for k in ks], closed))
    return res



def scene_faces(scene, limit=40000):
    """Every face in the model where it really is: [(points, normal, mesh centre)], to find the
    face a line was drawn on."""
    out = []
    try:
        meshes = []
        m = getattr(scene, 'mesh', None)
        if m is not None:
            meshes.append(list(_items(getattr(m, 'faces', None))))
        for g in _items(getattr(scene, 'groups', None)):
            meshes.append(_world_faces(g))
        for fl in meshes:
            allp = []
            recs = []
            for f in fl:
                pts = [q for q in (_pos(v) for v in _items(getattr(f, 'vertices', None))) if q is not None]
                if len(pts) < 3:
                    continue
                allp += pts
                recs.append(pts)
                if len(out) + len(recs) > limit:
                    break
            c = _plan_centre(allp)
            for pts in recs:
                out.append((pts, _newell(pts), c))
            if len(out) > limit:
                break
    except Exception:
        pass
    return out


def _on_face(pts, faces, tol):
    """The face that all these points lie on (in its plane and inside its outline), if any."""
    for fp, n, c in faces:
        d = v_dot(n, fp[0])
        if any(abs(v_dot(n, q) - d) > tol for q in pts):
            continue
        U = v_norm(v_sub(fp[1], fp[0]))
        V = v_cross(n, U)
        poly = [(v_dot(q, U), v_dot(q, V)) for q in fp]
        x0, x1, y0, y1 = bbox(poly)
        ok = True
        for q in pts:
            x, y = v_dot(q, U), v_dot(q, V)
            if not (x0 - tol <= x <= x1 + tol and y0 - tol <= y <= y1 + tol):
                ok = False
                break
        if ok:
            return n, c
    return None


def _line_point(p, u, off):
    return (p[0] - u[1] * off, p[1] + u[0] * off)


def _meet(p1, u1, p2, u2):
    den = u1[0] * u2[1] - u1[1] * u2[0]
    if abs(den) < 1e-9:
        return None
    t = ((p2[0] - p1[0]) * u2[1] - (p2[1] - p1[1]) * u2[0]) / den
    return (p1[0] + u1[0] * t, p1[1] + u1[1] * t)


def _nl(u):
    return (-u[1], u[0])


def _add2(p, u, t):
    return (p[0] + u[0] * t, p[1] + u[1] * t)


def _needed(u, band, nP, pband):
    """How far a bar end (pointing along u, its edge from band[0] to band[1] to its left) must
    reach past the joint to cover a bar whose band runs pband[0]..pband[1] along nP."""
    k = u[0] * nP[0] + u[1] * nP[1]
    if abs(k) < 0.15:
        return None
    nx = _nl(u)
    c = nx[0] * nP[0] + nx[1] * nP[1]
    return max(0.0, max((e - s * c) / k for s in band for e in pband))


class _Run:
    pass


def _plane_of(run, runs_world, faces, sel_faces, tol):
    """The plane a run of lines lies in: (normal, mesh centre or None, found on a face)."""
    P = run.world
    hit = _on_face(P, faces, tol)
    if hit is not None:
        return hit[0], hit[1], True
    if len(P) >= 3:
        n = _newell(P)
        if v_len(n) > 0.5:
            return n, None, False
    d0 = v_norm(v_sub(P[-1], P[0]))
    for f in sel_faces:
        if abs(v_dot(f.n, d0)) < 0.02:
            return f.n, f.centre, True
    # a straight line: the plane it shares with a line it meets
    ends = [P[0], P[-1]]
    for other in runs_world:
        if other is run:
            continue
        if not any(v_len(v_sub(e, q)) < tol for e in ends for q in other.world):
            continue
        d1 = v_norm(v_sub(other.world[-1], other.world[0]))
        n = v_cross(d0, d1)
        if v_len(n) > 0.1:
            return v_norm(n), None, False
    if abs(d0[2]) < 0.02:
        return Z, None, False
    c = v_cross(Z, d0)
    return (v_norm(c) if v_len(c) > 1e-6 else (1.0, 0.0, 0.0)), None, False


def frame_lines(scene, lines, v, p):
    """Bars along the selected lines: [(name, type, world solid)], problems.
    Square (butt) joints at right-angled corners and where a line ends on another - one bar
    runs through, the other stops against it; mitres at other angles; a curve is one bent bar."""
    w, depth, lift = p['w'], p['depth'], p.get('lift', 0.0)
    pos = v.get('line_pos', 'centre')
    faces = scene_faces(scene)
    allc = [q for ln in lines for q in ln]
    sz = max(max(abs(c) for q in allc for c in q), 1e-3)
    tol = 1e-6 + 1e-6 * sz
    sel_faces = []
    for f in selected_faces(scene):
        fi = FaceInfo(f)
        if fi.ok:
            fi.centre = _mesh_centre(scene, f)
            sel_faces.append(fi)
    side = v.get('side', 'auto')

    runs = []
    for pts, closed in runs_of(lines, w):
        r = _Run()
        r.world, r.closed = pts, closed
        r.length = sum(v_len(v_sub(pts[i + 1], pts[i])) for i in range(len(pts) - 1))
        runs.append(r)
    for r in runs:
        r.n, r.centre, r.on_face = _plane_of(r, runs, faces, sel_faces, tol)

    # ---- runs in the same plane are worked out together, so they can be cut against each other
    groups = []
    ptol = 0.05 * w * SCALE + tol
    for r in runs:
        for g in groups:
            n0 = g[0].n
            if abs(abs(v_dot(n0, r.n)) - 1.0) < 1e-4 and all(abs(v_dot(n0, v_sub(q, g[0].world[0]))) < ptol
                                                              for q in r.world):
                if v_dot(n0, r.n) < 0:
                    r.n = n0
                g.append(r)
                break
        else:
            groups.append([r])

    out, problems = [], []
    done = []
    num = 0
    for g in groups:
        base = next((r for r in g if r.on_face), g[0])
        n = base.n
        centre = next((r.centre for r in g if r.centre is not None), None)
        if side == 'back':
            n = v_mul(n, -1.0)
        elif side == 'auto':
            k_ = face_kind(n)
            if k_ == 'wall':
                if centre is not None and v_dot(n, v_sub(centre, base.world[0])) < 0:
                    n = v_mul(n, -1.0)
            elif k_ == 'roof':
                if n[2] > 0 and base.on_face:
                    n = v_mul(n, -1.0)                       # under a roof
            elif n[2] < 0:
                n = v_mul(n, -1.0)                           # on top of a floor
        if abs(n[2]) < 0.999:
            U = v_norm(v_cross(Z, n))
        else:
            U = (1.0, 0.0, 0.0)
        V = v_cross(n, U)
        O = v_mul(g[0].world[0], 1.0 / SCALE)

        def to2(q, O=O, U=U, V=V):
            d = v_sub(v_mul(q, 1.0 / SCALE), O)
            return (v_dot(d, U), v_dot(d, V))

        def tw(q, O=O, U=U, V=V, n=n):
            return v_mul(v_add(O, v_add(v_mul(U, q[0]), v_add(v_mul(V, q[1]), v_mul(n, q[2])))), SCALE)
        allp = [to2(q) for r in g for q in r.world]
        gc = (sum(q[0] for q in allp) / len(allp), sum(q[1] for q in allp) / len(allp))
        for r in g:
            r.p2 = [to2(q) for q in r.world]
            nseg = len(r.p2) if r.closed else len(r.p2) - 1
            r.dirs = []
            for i in range(nseg):
                a, b = r.p2[i], r.p2[(i + 1) % len(r.p2)]
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                r.dirs.append(((b[0] - a[0]) / L, (b[1] - a[1]) / L) if L > 1e-12 else None)
            r.dirs = [d for d in r.dirs if d] or [(1.0, 0.0)]
            sb = max(0.0, p.get('rebate', 0.0))
            if pos == 'centre':
                r.band = (-w / 2.0, w / 2.0)
            else:
                # 'one edge': the bar goes to the side of the line facing the middle of the lines
                m = len(r.p2) // 2
                a = r.p2[max(0, m - 1)]
                b = r.p2[m] if m > 0 else r.p2[-1]
                cr = (b[0] - a[0]) * (gc[1] - a[1]) - (b[1] - a[1]) * (gc[0] - a[0])
                left = cr >= 0
                if pos == 'right':
                    left = not left
                # set back from the line by the room left for a glazing frame
                r.band = (sb, sb + w) if left else (-sb - w, -sb)
            r.vert = sum(abs(v_dot(v_norm(v_sub(r.world[i + 1], r.world[i])), Z))
                         for i in range(len(r.world) - 1)) / max(1, len(r.world) - 1)
            r.stops = 0
            r.ends = {}
        # ---- the two ends of every open run: (joint, direction out, band in that direction's terms)
        jt = 0.02 * w + 1e-6

        def end_info(r, which):
            if which == 0:
                d = r.dirs[0]
                return r.p2[0], (-d[0], -d[1]), (-r.band[1], -r.band[0])
            return r.p2[-1], r.dirs[-1], r.band

        def on_interior(J, r):
            """Where J lies along the middle of run r: (segment direction, band) or None."""
            if r.closed:
                segs = [(r.p2[i], r.p2[(i + 1) % len(r.p2)]) for i in range(len(r.p2))]
            else:
                segs = [(r.p2[i], r.p2[i + 1]) for i in range(len(r.p2) - 1)]
            for i, (a, b) in enumerate(segs):
                dx, dy = b[0] - a[0], b[1] - a[1]
                L = math.hypot(dx, dy)
                if L < 1e-12:
                    continue
                u = (dx / L, dy / L)
                t = (J[0] - a[0]) * u[0] + (J[1] - a[1]) * u[1]
                off = abs((J[0] - a[0]) * u[1] - (J[1] - a[1]) * u[0])
                if off < jt and -jt <= t <= L + jt:
                    at_end = (not r.closed) and ((i == 0 and t < jt) or (i == len(segs) - 1 and t > L - jt))
                    if not at_end:
                        return u, r.band
            return None

        for r in g:
            if r.closed:
                continue
            for which in (0, 1):
                J, u, band = end_info(r, which)
                ext, shape = 0.0, None
                tee = None
                for o in g:
                    if o is not r:
                        tee = on_interior(J, o)
                        if tee:
                            break
                if tee:
                    e = _needed(u, band, _nl(tee[0]), tee[1])
                    if e is not None:
                        ext = e
                        r.stops += 1
                else:
                    for o in g:
                        if o is r or o.closed:
                            continue
                        for ow in (0, 1):
                            J2, u2, band2 = end_info(o, ow)
                            if math.hypot(J[0] - J2[0], J[1] - J2[1]) > jt:
                                continue
                            c = abs(u[0] * u2[0] + u[1] * u2[1])
                            if c < 0.5:
                                # near enough a right angle: butt joint. The more level bar (then
                                # the longer) runs through; the other stops against it.
                                e = _needed(u, band, _nl(u2), band2)
                                if e is not None:
                                    ext = e
                                    mine = (round(r.vert, 3), -r.length, id(r))
                                    theirs = (round(o.vert, 3), -o.length, id(o))
                                    if mine > theirs:
                                        r.stops += 1
                            else:
                                # a mitre: each edge of this bar meets the matching edge of the other
                                pts_ = []
                                for s in band:
                                    a1 = _add2(J, _nl(u), s)
                                    a2 = _add2(J, _nl(u2), -s)
                                    q = _meet(a1, u, a2, u2)
                                    if q is None or math.hypot(q[0] - J[0], q[1] - J[1]) > 4.0 * w:
                                        pts_ = None
                                        break
                                    pts_.append(q)
                                shape = pts_
                            break
                        else:
                            continue
                        break
                r.ends[which] = (ext, shape)

        # ---- each run as convex bits: one quad per line, mitred between lines of the same run
        for r in g:
            P = r.p2
            m = len(P)
            nseg = m if r.closed else m - 1
            lo, hi = r.band
            segs = []
            for i in range(nseg):
                a, b = P[i], P[(i + 1) % m]
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                if L > 1e-12:
                    segs.append((a, b, ((b[0] - a[0]) / L, (b[1] - a[1]) / L)))
            quads = []
            for i, (a, b, u) in enumerate(segs):
                corners = []
                for end in (0, 1):
                    J = a if end == 0 else b
                    j = i - 1 if end == 0 else i + 1
                    if r.closed:
                        j %= len(segs)
                    pair = []
                    if 0 <= j < len(segs):
                        u2 = segs[j][2]
                        for s in (lo, hi):
                            q = _meet(_add2(J, _nl(u), s), u, _add2(J, _nl(u2), s), u2)
                            if q is None or math.hypot(q[0] - J[0], q[1] - J[1]) > 4.0 * w:
                                q = _add2(J, _nl(u), s)
                            pair.append(q)
                    else:
                        ext, shape = r.ends.get(end, (0.0, None))
                        if shape:
                            # mitre with another run (stored in the end's own terms: lo<->-hi at the start)
                            pair = list(shape) if end == 1 else [shape[1], shape[0]]
                        else:
                            sgn = -1.0 if end == 0 else 1.0
                            K = _add2(J, u, sgn * ext)
                            pair = [_add2(K, _nl(u), lo), _add2(K, _nl(u), hi)]
                    corners.append(pair)
                (s_lo, s_hi), (e_lo, e_hi) = corners
                q = clean([s_lo, e_lo, e_hi, s_hi])
                if q:
                    quads += convex_parts(q)
            r.quads = quads

        # ---- cut each bar back clear of the ones placed before it
        x_ = [q[0] for r in g for pc in r.quads for q in pc]
        y_ = [q[1] for r in g for pc in r.quads for q in pc]
        if not x_:
            continue
        holder = _Run()
        holder.tw = tw
        holder.outline = [(min(x_), min(y_)), (max(x_), min(y_)), (max(x_), max(y_)), (min(x_), max(y_))]
        placed = list(_clearance(holder, done, lift, lift + depth, p))
        gap = p.get('gap', 0.0)
        for r in sorted(g, key=lambda r: (r.stops, round(r.vert, 3), -r.length)):
            pcs = cut_away(list(r.quads), placed)
            pcs = [pc for pc in pcs if abs(area2(pc)) > 1e-6 * w * w]
            minp = max(0.0, p.get('min_piece', 0.0))
            for comp in _components(pcs, 1e-3 * w):
                if sum(abs(area2(pc)) for pc in comp) < 0.3 * w * w:
                    continue
                if minp > 0 and _comp_thick(comp) < minp:
                    continue
                so = merged_slab(comp, lambda x, y: lift, lambda x, y: lift + depth)
                if so is None:
                    continue
                num += 1
                out.append(("Bar %d" % num, 'line', so.mapped(tw)))
                for pc in comp:
                    placed.append(grow(pc, gap) if gap > 0 else pc)
                    done.append(_prism(tw, pc, lift, lift + depth))
    return out, problems

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
    'Frame on': "Inside the building: worked out for you - the frame goes on the inside of the walls and "
                "under the roof. Or put it on the front or back of the faces you picked.",
    'Walls': "Frame the upright faces.",
    'Roof slopes': "Frame the sloping faces: eaves plate, ridge, hip and verge rafters, rafters and purlins.",
    'Floors and flat roofs': "Frame the level faces too (joists underneath).",
    'Plates and corner posts round the edge': "A bar all round the edge of each face: bottom and top "
                                               "plates, gable rails and end posts.",
    'Posts, lintels and sills round openings': "Frames every window and door: a post each side, a "
                                                "lintel over and a sill under.",
    'Studs and rafters': "Upright studs across each wall and rafters up each roof slope, at the spacing "
                         "you set. Over an opening they become short studs above and below it.",
    'Diagonal braces at the ends of walls': "A brace across the bay at each end of a wall (where there's no "
                                            "opening in it), to stop it going out of square.",
    'Stop short at inside corners': "Where two walls meet, one frame stops short by the bar depth, so the "
                                    "two frames meet without overlapping.",
    'Line runs along the': "Along lines: is the line you drew the middle of the bar, or its edge? Drawn "
                           "round a door or window, 'outside the shape' puts the bars in the wall round it.",
    'Suggest frame for selection': "Select the building (or some walls and roof faces) and it works out "
                                   "the frame for you.",
    'Frame along selected lines': "Draw lines with the line tool where you want bars, select them and the "
                                  "bars follow them, mitred at the corners.",
    'Show / hide...': "Opens a small window to hide the roof, the fascia and barge boards, and the "
                      "free-standing trusses - so you can see the frame inside. Untick to hide, tick to show. "
                      "It stays open until you click its X, even with this window closed.",
}
EDDY_TIPS_END = None

# (key, label, min, max, decimals, tip)  - the suffix is the unit picked
FIELDS = [
    ('width', "A   Bar width", 0.1, 5000.0, 2, "How wide each bar is, seen flat against the wall."),
    ('depth', "B   Bar depth", 0.1, 5000.0, 2, "How far each bar stands out from the wall (or down "
                                               "from the roof)."),
    ('spacing', "C   Stud spacing (walls)", 0.0, 50000.0, 1, "About how far apart the studs are. The plugin "
                                                            "spreads them evenly. 0 = no studs."),
    ('rafter_spacing', "D   Rafter spacing (roofs)", 0.0, 50000.0, 1, "About how far apart the rafters are, "
                                                                      "along the eaves."),
    ('lintel', "E   Lintel depth", 0.1, 5000.0, 2, "How deep the lintel over each opening is."),
    ('truss_spacing', "P   Truss spacing", 0.0, 50000.0, 1, "Pointed roof trusses between the gables, about "
                                                               "this far apart (spread evenly along the building). "
                                                               "0 = no trusses. Pick the truss style on 'What to "
                                                               "frame'."),
    ('truss_overhang', "Q   Truss overhang", 0.0, 50000.0, 1, "How far the truss rafters run on past the "
                                                                 "inside of the walls, down over the eaves, so the "
                                                                 "roof tiles hang into the gutters. Where they cross "
                                                                 "the walls they're notched to sit on them. 0 = they "
                                                                 "stop at the walls."),
    ('min_piece', "L   Smallest piece", 0.0, 5000.0, 1, "Pieces thinner than this aren't made - no slivers and "
                                                    "odd little bits. 0 = keep everything."),
    ('gap', "M   Gap between pieces", 0.0, 50.0, 2, "A small gap between bars, if your prints need a bit of "
                                                "room to fit together. 0 = they just touch."),
    ('lift', "N   Gap off the face", 0.0, 50.0, 3, "A gap between the frame and the wall. 0 = it sits on the "
                                               "wall, ready to glue."),
]


# the Glazing page
GFIELDS = [
    ('rebate', "F   Room round openings", 0.0, 5000.0, 1, "How far the frame stands back from the edge of each window "
                                                     "and door, leaving room behind the opening for a glazing "
                                                     "frame. 150 = 2 mm in OO. 0 = right up to the edge."),
    ('glaze_w', "G   Glazing frame width", 0.0, 5000.0, 1, "How wide the border of each glazing frame is. It stays this "
                                                       "width - it's only made narrower if it won't fit in the room "
                                                       "round the opening. 0 = no glazing frames."),
    ('glaze_t', "H   Glazing frame thickness", 0.0, 5000.0, 1, "How thick the glazing frame prints."),
    ('glaze_setin', "J   Set in from the opening", 0.0, 5000.0, 1, "How far the inside edge of the glazing frame is "
                                                              "back from the edge of the window, hidden behind the "
                                                              "wall, so you don't see the frame from outside."),
    ('glaze_inset', "K   Fit (room to spare)", 0.0, 5000.0, 1, "Room left between the outside of the glazing frame and "
                                                           "the subframe round it, so it drops in easily."),
]

# the Boards page (V to AB on the second key drawing). 0 = worked out from the bar width (A)
BFIELDS = [
    ('fascia_h', "V   Fascia board height", 0.0, 5000.0, 1, "How deep the fascia boards along the eaves are. "
                                                             "0 = 1.25 x the bar width."),
    ('board_t', "W   Board thickness", 0.0, 1000.0, 1, "How thick the fascia and barge boards are. 0 = half the "
                                                       "bar width."),
    ('board_off', "X   Stand off the wall", 0.0, 2000.0, 1, "How far the boards stand off the outside of the walls, "
                                                             "leaving room for brick courses, render or "
                                                             "weatherboarding on the walls. The truss overhang (Q) "
                                                             "needs to reach past the wall and this."),
    ('barge_w', "Y   Barge board width", 0.0, 5000.0, 1, "How wide the barge boards up the gables are. 0 = the "
                                                         "same as the fascia."),
    ('finial_h', "Z   Finial height", 0.0, 5000.0, 1, "How far the finial stands up above the peak. 0 = twice "
                                                      "the bar width."),
    ('finial_drop', "AA  Finial drop", 0.0, 5000.0, 1, "How far the finial hangs down below the barge boards "
                                                        "at the peak. 0 = the bar width."),
    ('finial_w', "AB  Finial width", 0.0, 2000.0, 1, "How wide the finial post is. 0 = 0.8 x the bar width."),
    ('roof_t', "AC  Roof panel thickness", 0.0, 2000.0, 1, "How thick the plain roof panels are. 0 = the board "
                                                           "thickness (W)."),
    ('roof_over', "AD  Roof over the gutter", 0.0, 2000.0, 1, "How far the roof panels hang past the fascia, out over "
                                                             "the gutter. 0 = the board thickness (W)."),
]

# the Floors page (R to U on the key drawing)
FFIELDS = [
    ('floor_t', "R   Floor thickness", 0.0, 5000.0, 1, "How thick your floor panels are. The ledge goes this far "
                                                    "below each floor level, so the top of the floor ends up at "
                                                    "the level you typed."),
    ('ledge_h', "S   Ledge height", 0.0, 5000.0, 1, "How tall the ledge is, up the wall. 0 = the same as the bar "
                                                 "width."),
    ('ledge_out', "T   Ledge sticks out", 0.0, 5000.0, 1, "How far the ledge stands out past the frame, for the "
                                                       "floor to rest on. 0 = the same as the bar width."),
    ('floor_fit', "U   Floor fit (room to spare)", 0.0, 500.0, 1, "Room left between the edge of the floor panel and "
                                                               "the frame, so it drops in easily after printing."),
]


INFO_TEXT = ("<b>How to use it</b><br>"
            "Build the walls (with their openings) and the roof first. Then select the building and click "
            "'Suggest frame for selection' - or draw lines where you want bars, select them and click "
            "'Frame along selected lines'.<br><br>"
            "<b>One wall at a time</b><br>"
            "Select just one wall's group: the frame goes on its inside, worked out from the building round "
            "it. 'Frame on: Back' does the same; 'Front' puts it on the outside. For a single face you've "
            "picked (not a group), Front and Back mean the side of that face.<br><br>"
            "<b>Trusses</b><br>"
            "Set a truss spacing (P, on the Sizes page) and the roof is held by trusses. The gable end "
            "trusses go in with their end walls (framed round any loft window); the ones in the middle are "
            "each a group on their own, so you can move or take one out. With an overhang (Q) the rafter ends "
            "are cut square for fascia boards.<br><br>"
            "<b>Fascia and barge boards</b><br>"
            "Tick them on the Boards page. Fascia boards go along the eaves on the ends of the truss rafters, "
            "barge boards up the gables with a finial at each peak - all standing off the walls (X) to leave "
            "room for brick courses. Tick soffit boards for under the eaves, and roof panels for a plain roof on the "
            "trusses, hanging into the gutter, ready for tiles. Their sizes (V to AD) are on the second key page.<br><br>"
            "<b>Show / hide</b><br>"
            "Click 'Show / hide...' for a small window of ticks: untick the roof, the fascia and barge "
            "boards or the free-standing trusses to hide them and see the frame inside. The wall frames "
            "(and the gable end trusses in them) are never hidden. Ctrl+Z, or Edit > Unhide, works "
            "too.<br><br>"
            "<b>Floors</b><br>"
            "If there's a floor in the building, the frame stands on top of it.<br><br>"
            "<b>Printing</b><br>Every bar is its own group: in Scale Studio's Pieces page pick 'Every group with "
            "faces (smallest pieces)' and tick 'Lay each piece flat'.<br><br>"
            "Sizes are real-world mm - Scale Studio takes it down to your model scale.")


# sizes left at 0 are worked out: what each one comes to, from the other settings (shown in its box)
def _auto_sizes(v):
    w = float(v.get('width', 0.0) or 0.0)
    fh = v.get('fascia_h', 0.0) or 1.25 * w
    bt = v.get('board_t', 0.0) or 0.5 * w
    return {'fascia_h': fh, 'board_t': bt, 'barge_w': v.get('barge_w', 0.0) or fh,
            'finial_h': 2.0 * w, 'finial_drop': w, 'finial_w': 0.8 * w,
            'roof_t': bt, 'roof_over': bt, 'ledge_h': w, 'ledge_out': w}


# which settings make each kind of piece - looked up by the piece's name when you click on it
PIECE_KEYS = [
    ("Fascia", ('fascia_h', 'board_t', 'board_off')),
    ("Barge", ('barge_w', 'board_t', 'board_off', 'finial_h', 'finial_drop', 'finial_w')),
    ("Soffit", ('board_t', 'board_off')),
    ("soffit", ('fascia_h', 'board_t', 'board_off')),
    ("Roof panel", ('roof_t', 'roof_over')),
    ("Glazing frame", ('glaze_w', 'glaze_t', 'glaze_setin', 'glaze_inset', 'rebate')),
    ("ledge", ('ledge_h', 'ledge_out', 'floor_t')),
    ("Floor", ('floor_t', 'floor_fit')),
    ("truss", ('truss_spacing', 'truss_overhang', 'width', 'depth')),
    ("Truss", ('truss_spacing', 'truss_overhang', 'width', 'depth')),
    ("Lintel", ('lintel', 'width', 'depth', 'rebate')),
    ("Sill", ('width', 'depth', 'rebate')),
    ("Post", ('width', 'depth', 'rebate')),
    ("Stud", ('spacing', 'width', 'depth')),
    ("Rafter", ('rafter_spacing', 'width', 'depth')),
    ("Purlin", ('rafter_spacing', 'width', 'depth')),
    ("Rail", ('width', 'depth')),
    ("Brace", ('width', 'depth')),
    ("plate", ('width', 'depth')),
    ("End post", ('width', 'depth')),
]


def piece_keys(name):
    """The settings behind a piece of ours, from its name ('Wall 3 - Window 1 - Lintel' -> lintel...)."""
    name = str(name or '')
    if " - " not in name and not name.startswith(("Roof truss", "Fascia", "Barge", "Soffit", "Roof panel",
                                                   "Gable end truss", "Glazing", "Floor")):
        return ()
    for word, keys in PIECE_KEYS:
        if word in name.split(" - ")[-1] or (word in name and word in ("Fascia", "Barge", "Soffit",
                                                                         "Roof panel", "truss", "Truss")):
            return keys
    return ('width', 'depth')


class KeyDrawing(QWidget):
    """A drawing that shows what each lettered size is."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 650)

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QPainterPath, QPolygonF
        from PySide6.QtCore import QPointF, QRectF, Qt
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 246))
        W = float(self.width())
        k = min(W / 360.0, self.height() / 650.0)
        p.scale(k, k)
        wall, bar = QColor(236, 230, 220), QColor(160, 112, 66)
        lint, glz, glass = QColor(215, 150, 50), QColor(120, 175, 225), QColor(200, 225, 245)
        red = QColor(200, 40, 40)
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
            import math as _m
            ang = _m.atan2(y2 - y1, x2 - x1)
            for (x, y, a) in ((x1, y1, ang), (x2, y2, ang + _m.pi)):
                for s in (0.45, -0.45):
                    p.drawLine(QPointF(x, y), QPointF(x + 6 * _m.cos(a + s), y + 6 * _m.sin(a + s)))
            p.setPen(red)
            p.drawText(QRectF(tx - 10, ty - 9, 20, 18), Qt.AlignCenter, letter)

        p.setPen(QColor(60, 60, 60))
        p.drawText(QRectF(10, 4, 340, 18), Qt.AlignLeft, "A wall from the inside (the frame side)")
        # ---- the wall elevation
        X0, Y0, X1, Y1 = 20.0, 30.0, 340.0, 250.0
        box(X0, Y0, X1 - X0, Y1 - Y0, wall)
        b = 12.0
        box(X0, Y1 - b, X1 - X0, b, bar)                 # bottom plate
        box(X0, Y0, X1 - X0, b, bar)                     # top plate
        box(X0, Y0 + b, b, Y1 - Y0 - 2 * b, bar)         # end posts
        box(X1 - b, Y0 + b, b, Y1 - Y0 - 2 * b, bar)
        s1, s2 = 75.0, 135.0
        for sx in (s1, s2):
            box(sx, Y0 + b, b, Y1 - Y0 - 2 * b, bar)     # studs
        # window: opening, glazing frame, posts, lintel, sill
        wx0, wy0, wx1, wy1 = 210.0, 105.0, 285.0, 170.0  # the window opening
        F_, G_, J_ = 26.0, 10.0, 8.0
        ox0, oy0, ox1, oy1 = wx0 - F_, wy0 - F_, wx1 + F_, wy1 + F_
        box(ox0 - b, Y0 + b, b, Y1 - Y0 - 2 * b, bar)
        box(ox1, Y0 + b, b, Y1 - Y0 - 2 * b, bar)
        box(ox0, oy0 - 16, ox1 - ox0, 16, lint)          # lintel (deeper)
        box(ox0, oy1, ox1 - ox0, b, lint)                # sill
        # (y grows downwards on screen: the lintel is above the opening)
        p.setPen(Qt.NoPen)
        p.setBrush(lint)
        gpath = QPainterPath()
        gpath.addRect(QRectF(wx0 - J_ - G_, wy0 - J_ - G_, (wx1 - wx0) + 2 * (J_ + G_), (wy1 - wy0) + 2 * (J_ + G_)))
        gpath.addRect(QRectF(wx0 - J_, wy0 - J_, (wx1 - wx0) + 2 * J_, (wy1 - wy0) + 2 * J_))
        gpath.setFillRule(Qt.OddEvenFill)
        p.setPen(QPen(glz.darker(150), 0.8))
        p.setBrush(glz)
        p.drawPath(gpath)
        p.setPen(QPen(QColor(90, 120, 150), 1.0, Qt.DashLine))
        p.setBrush(glass)
        p.drawRect(QRectF(wx0, wy0, wx1 - wx0, wy1 - wy0))
        p.setPen(QColor(90, 120, 150))
        p.drawText(QRectF(wx0, wy0 + 20, wx1 - wx0, 24), Qt.AlignCenter, "window")
        # ---- the dimensions
        dim(s1, Y1 - 40, s1 + b, Y1 - 40, "A", s1 + 6, Y1 - 52)
        dim(s1 + b / 2, 120, s2 + b / 2, 120, "C", (s1 + s2) / 2 + 6, 110)
        dim(ox0 + 30, oy0 - 16, ox0 + 30, oy0, "E", ox0 + 42, oy0 - 8)
        dim(wx1, (wy0 + wy1) / 2 + 12, ox1, (wy0 + wy1) / 2 + 12, "F", ox1 - 10, (wy0 + wy1) / 2 + 24)
        dim(wx0 - J_ - G_, wy1 + 2, wx0 - J_, wy1 + 2, "G", wx0 - J_ - G_ - 8, wy1 + 12)
        dim(wx0 - J_, wy0 + 12, wx0, wy0 + 12, "J", wx0 + 10, wy0 + 6)
        dim(wx1 + J_ + G_, wy0 - 6, ox1, wy0 - 6, "K", wx1 + J_ + G_ + 4, wy0 - 16)
        # ---- the section: a wall seen end on, with a bar on it
        p.setFont(f)
        p.setPen(QColor(60, 60, 60))
        p.drawText(QRectF(10, 262, 200, 18), Qt.AlignLeft, "The wall seen end on")
        box(30, 285, 26, 130, QColor(200, 196, 188))         # the wall
        box(60, 300, 26, 26, bar)                            # a bar, off the face by N
        box(60, 350, 8, 50, glz)                             # glazing frame, thickness H
        dim(56, 296, 60, 296, "N", 58, 286)
        dim(60, 330, 86, 330, "B", 74, 342)
        dim(60, 405, 68, 405, "H", 75, 418)
        p.setPen(QColor(60, 60, 60))
        f2 = QFont()
        f2.setPointSizeF(8.5)
        p.setFont(f2)
        notes = ["A  bar width (flat on the wall)", "B  bar depth (off the wall)", "C  stud spacing",
                 "D  rafter spacing - like C, up a roof", "E  lintel depth", "F  room round openings",
                 "G  glazing frame width", "H  glazing frame thickness", "J  glazing set in behind the window",
                 "K  glazing fit (room to spare)", "L  smallest piece made", "M  gap between pieces",
                 "N  gap off the face", "P  truss spacing (between the gables)",
                 "Q  truss overhang (past the walls, cut square for a fascia)",
                 "R  floor thickness", "S  ledge height", "T  ledge sticks out past the frame",
                 "U  floor fit (room to spare)"]
        for i, t in enumerate(notes):
            p.drawText(QRectF(125, 274 + i * 10.4, 240, 12), Qt.AlignLeft | Qt.AlignVCenter, t)

        # ---- a floor resting on its ledge, seen end on (Floors page)
        p.setFont(f)
        p.setPen(QColor(60, 60, 60))
        p.drawText(QRectF(10, 482, 120, 18), Qt.AlignLeft, "A floor on its ledge")
        floor_c = QColor(205, 185, 150)
        box(30, 505, 26, 100, QColor(200, 196, 188))         # the wall
        box(60, 505, 26, 100, bar)                           # the frame
        box(60, 560, 44, 14, QColor(110, 85, 60))            # the ledge, standing out past the frame
        box(92, 546, 26, 14, floor_c)                        # the floor panel, resting on it
        dim(122, 546, 122, 560, "R", 132, 553)
        dim(46, 560, 46, 574, "S", 38, 567)
        dim(86, 590, 104, 590, "T", 95, 600)
        dim(86, 538, 92, 538, "U", 89, 528)

        # ---- a truss, its rafters running on past the walls and cut square for a fascia board
        p.setFont(f)
        p.setPen(QColor(60, 60, 60))
        p.drawText(QRectF(150, 482, 210, 18), Qt.AlignLeft, "A truss, end on (Q) - and from the side (P)")
        wl, wr, ye_, top_ = 185.0, 315.0, 560.0, 505.0
        box(wl - 10, ye_, 10, 45, QColor(200, 196, 188))     # the walls under it
        box(wr, ye_, 10, 45, QColor(200, 196, 188))
        q_ = 22.0
        sl_ = (ye_ - top_) / ((wr - wl) / 2.0)
        xl, xr = wl - q_, wr + q_
        yl = ye_ + q_ * sl_
        tr_col = QColor(165, 112, 66)
        p.setPen(QPen(tr_col.darker(160), 0.8))
        p.setBrush(tr_col)
        for xa_, sgn in ((xl, 1.0), (xr, -1.0)):             # the rafters, square-cut ends
            mid = (wl + wr) / 2.0
            p.drawPolygon(QPolygonF([QPointF(xa_, yl), QPointF(mid, top_), QPointF(mid, top_ + 9),
                                     QPointF(xa_, yl + 9)]))
        box(wl, ye_ - 8, wr - wl, 8, tr_col)                  # the tie
        box((wl + wr) / 2.0 - 3, top_ + 6, 6, ye_ - top_ - 14, tr_col)   # king post
        box(xl - 3, yl - 2, 3, 13, QColor(90, 90, 90))       # fascia boards on the cut ends
        box(xr, yl - 2, 3, 13, QColor(90, 90, 90))
        dim(xl, yl + 18, wl, yl + 18, "Q", (xl + wl) / 2.0, yl + 28)
        # from the side: trusses standing along the building, P apart
        box(160, 630, 190, 6, QColor(150, 104, 64))          # the wall plate they stand on
        for i in range(5):
            box(170 + i * 40, 612, 5, 18, tr_col)
        dim(172.5, 606, 212.5, 606, "P", 192, 596)
        p.end()


class KeyDrawing2(QWidget):
    """The second key: the fascia and barge boards and the finial (V to AB)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 560)

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
        from PySide6.QtCore import QPointF, QRectF, Qt
        import math as _m
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 246))
        k = min(float(self.width()) / 360.0, self.height() / 560.0)
        p.scale(k, k)
        red = QColor(200, 40, 40)
        board = QColor(240, 240, 232)
        wallc, brick = QColor(200, 196, 188), QColor(178, 90, 60)
        trc = QColor(165, 112, 66)
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
        p.drawText(QRectF(10, 4, 340, 18), Qt.AlignLeft, "The gable end from outside")
        # ---- the gable end: wall, barge boards, finial
        gx0, gx1, gy, apx, apy = 70.0, 290.0, 215.0, 180.0, 95.0
        poly([(gx0, 300), (gx1, 300), (gx1, gy), (apx, apy), (gx0, gy)], wallc)
        for i in range(6):                                  # brick courses on the wall
            p.setPen(QPen(brick, 0.6))
            p.drawLine(QPointF(gx0, 230 + i * 12), QPointF(gx1, 230 + i * 12))
        bw_, ov = 16.0, 26.0
        s_ = (gy - apy) / (apx - gx0)
        xl, xr = gx0 - ov, gx1 + ov
        yl = gy + ov * s_
        poly([(xl, yl), (apx, apy), (xr, yl), (xr, yl + bw_), (apx, apy + bw_ * 1.3), (xl, yl + bw_)], board)
        box(apx - 6, apy - 40, 12, 40 + 1.3 * bw_ + 18, board)       # the finial
        p.setPen(QPen(QColor(90, 90, 90), 0.8))
        p.drawLine(QPointF(apx - 6, apy - 30), QPointF(apx + 6, apy - 30))
        dim(apx + 22, apy - 40, apx + 22, apy, "Z", apx + 36, apy - 20)
        dim(apx + 22, apy + 1.3 * bw_, apx + 22, apy + 1.3 * bw_ + 18, "AA", apx + 40, apy + 1.3 * bw_ + 9)
        dim(apx - 6, apy - 48, apx + 6, apy - 48, "AB", apx, apy - 60)
        mx, my = (xl + apx) / 2.0, (yl + apy) / 2.0
        nx, ny = s_ / _m.hypot(1, s_), 1 / _m.hypot(1, s_)
        dim(mx, my, mx + nx * bw_, my + ny * bw_, "Y", mx - 14, my + 18)
        # ---- the eaves in section: wall with bricks, rafter tail, fascia, barge board standing off
        p.setPen(QColor(60, 60, 60))
        p.setFont(f)
        p.drawText(QRectF(10, 318, 340, 18), Qt.AlignLeft, "The eaves, end on")
        box(220, 380, 22, 95, wallc)                         # the wall
        box(196, 380, 24, 95, brick)                         # brick courses on its outside
        box(242, 380, 14, 95, trc)                           # the frame inside
        yt = lambda x: 382.7 - (x - 150.0) * 0.45            # the top of the rafter, just clearing the bricks
        poly([(150, yt(150)), (300, yt(300)), (300, yt(300) + 18), (150, yt(150) + 18)], trc)   # square-cut end
        fy = yt(150)
        box(150, fy + 30 - 8, 46, 8, board)                  # the soffit board, fascia back to bricks
        rp = QColor(120, 120, 125)
        rt_ = 9.0
        poly([(122, yt(122)), (300, yt(300)), (300, yt(300) - rt_), (122, yt(122) - rt_)], rp)   # roof panel
        p.setPen(QPen(QColor(90, 90, 90), 1.2))             # the gutter
        p.setBrush(Qt.NoBrush if hasattr(Qt, 'NoBrush') else None)
        p.drawLine(QPointF(112, yt(130)), QPointF(116, yt(130) + 14))
        p.drawLine(QPointF(116, yt(130) + 14), QPointF(136, yt(130) + 14))
        p.drawLine(QPointF(136, yt(130) + 14), QPointF(140, yt(130)))
        dim(122, yt(122) - 22, 140, yt(122) - 22, "AD", 128, yt(122) - 34)
        dim(215, yt(215) - rt_, 215, yt(215), "AC", 228, yt(215) - 20)
        p.setPen(QColor(90, 90, 90))
        p.drawText(QRectF(152, fy + 30, 60, 12), Qt.AlignLeft, "soffit")
        p.setPen(QColor(255, 255, 255))
        p.drawText(QRectF(198, 440, 22, 14), Qt.AlignCenter, "brick")
        box(140, fy, 10, 30, board)                          # the fascia on the rafter ends
        dim(140, fy + 36, 150, fy + 36, "W", 145, fy + 47)
        dim(100, fy, 100, fy + 30, "V", 90, fy + 15)
        p.setPen(QPen(QColor(150, 150, 150), 0.6))
        p.drawLine(QPointF(100, fy), QPointF(140, fy))
        p.drawLine(QPointF(100, fy + 30), QPointF(140, fy + 30))
        dim(150, 455, 220, 455, "X", 185, 445)
        f2 = QFont()
        f2.setPointSizeF(8.5)
        p.setFont(f2)
        p.setPen(QColor(60, 60, 60))
        notes = ["V  fascia board height", "W  board thickness (fascia and barge)",
                 "X  stand off the wall (room for bricks)", "Y  barge board width",
                 "Z  finial height above the peak", "AA finial drop below the peak", "AB finial width",
                 "AC roof panel thickness", "AD roof panel over the gutter", "0 = worked out from the bars"]
        for i, t in enumerate(notes):
            p.drawText(QRectF(10 if i < 5 else 185, 496 + (i % 5) * 12.5, 175, 13), Qt.AlignLeft | Qt.AlignVCenter, t)
        p.end()


class FramePreview(QWidget):
    """A sample gable wall with a window and a door, framed with the settings in the window."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 260)
        self.items = []
        self.msg = ""
        self.caption = ""

    def show_frame(self, v):
        try:
            p = frame_params(v)
            s = max(p['spacing'], p['w'] * 5.0)
            W, H, A = 5.5 * s, 3.0 * s, 1.3 * s
            dw, dh = 0.9 * s, 1.9 * s
            dx = 0.6 * s
            # an arched doorway and a round window, to show the frame squared off round them
            arch = [(dx + dw / 2.0 - dw / 2.0 * math.cos(math.pi * k / 10.0),
                     dh + dw / 2.0 * math.sin(math.pi * k / 10.0)) for k in range(10, -1, -1)]
            outline = [(0.0, 0.0), (dx, 0.0)] + [(dx, dh)] + list(reversed(arch))[1:-1] + \
                      [(dx + dw, dh), (dx + dw, 0.0), (W, 0.0), (W, H), (W / 2.0, H + A), (0.0, H)]
            cx, cy, r = 3.85 * s, 1.65 * s, 0.6 * s
            hole = [(cx + r * math.cos(2 * math.pi * k / 24.0), cy + r * math.sin(2 * math.pi * k / 24.0))
                    for k in range(24)]
            ledges = [(max(za, 0.0), zb, nm) for za, zb, nm, _lv in ledge_bands(p)
                      if zb > 0.3 * p['ledge_h'] and za < H + A]
            bars = lay_frame(clean(outline), [hole], p, 'wall', (), ledges)
            self.items = [(clean(outline), (236, 230, 220))]
            self.items.append((hole, (190, 215, 235)))
            for name, typ, pcs in bars:
                for pc in pcs:
                    self.items.append((pc, COLOURS.get(typ, (180, 150, 100))))
            self.caption = "%d pieces on this sample wall - %.0f x %.0f mm bars" % (
                len(bars), p['w'], p['depth'])
            self.msg = ""
        except Exception as e:
            self.items, self.msg = [], str(e)
        self.update()

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen, QFont
        from PySide6.QtCore import QPointF, Qt
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(246, 246, 242))
        if not self.items:
            p.drawText(self.rect(), Qt.AlignCenter, self.msg or "No preview")
            p.end()
            return
        xs = [q[0] for it in self.items for q in it[0]]
        ys = [q[1] for it in self.items for q in it[0]]
        h_cap = 18
        w, h = self.width() - 20, self.height() - 20 - h_cap
        sc = min(w / ((max(xs) - min(xs)) or 1), h / ((max(ys) - min(ys)) or 1))
        ox = 10 + (w - (max(xs) - min(xs)) * sc) / 2 - min(xs) * sc
        oy = 10 + h_cap + h - (h - (max(ys) - min(ys)) * sc) / 2 + min(ys) * sc
        for k, (pts, rgb) in enumerate(self.items):
            col = QColor(*rgb)
            p.setBrush(col)
            p.setPen(QPen(col.darker(170), 0.9 if k > 1 else 1.2))
            p.drawPolygon(QPolygonF([QPointF(ox + x * sc, oy - y * sc) for x, y in pts]))
        f = QFont()
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(50, 50, 50))
        p.drawText(8, 4, self.width() - 16, h_cap, Qt.AlignLeft | Qt.AlignVCenter, self.caption)
        p.end()


UI_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_subframe.json")


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


# the fascia, barge and soffit boards (and the barge finials) are painted their own colour so
# they stand out from the frame: cream to start with, or a colour you pick
BOARD_TYPES = ('fascia', 'barge', 'soffit')
BOARD_CREAM = (240, 230, 200)
BOARD_MATERIAL = "Eddy - Fascia & barge boards"
BOARD_MODES = [("Cream (the default)", 'cream'), ("My own colour", 'own'),
               ("Leave it to Layers & Colours", 'none')]


def board_colour():
    """(mode, (r, g, b)) - the colour the boards are painted, from your settings."""
    st = _ui_settings()
    mode = st.get('board_mode', 'cream')
    if mode not in [k for _l, k in BOARD_MODES]:
        mode = 'cream'
    try:
        rgb = tuple(int(c) for c in st.get('board_rgb', BOARD_CREAM))[:3]
    except Exception:
        rgb = BOARD_CREAM
    return mode, (rgb if mode == 'own' else BOARD_CREAM)


def _board_attrs(scene, rgb):
    """The face paint for the boards: a material of their own in the document, set to rgb."""
    colour = (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
    mats = getattr(scene, 'materials', None)
    if mats is not None:
        try:
            mat = mats.get(BOARD_MATERIAL)
            if mat is None:
                from core.materials import Material
                mat = mats[BOARD_MATERIAL] = Material(BOARD_MATERIAL, color=colour, opacity=1.0)
            elif hasattr(mat, 'color'):
                mat.color = colour                 # the colour picked in this window wins
            return dict(mat.face_attrs())
        except Exception as e:
            print("%s: board colour: %s" % (PLUGIN_NAME, e))
    return {"color": colour}


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


class FrameDialog(QDialog):
    def __init__(self, cur, viewport, tool):
        super().__init__(viewport)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.user_presets = load_presets()
        self._busy = False
        lay = QVBoxLayout(self)
        # the writing at the top - how to use it, and what the last build did - only shows when the
        # Info button (bottom of the window) is pressed; it's off each time the window opens
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
        self.preview = FramePreview()
        self.left = QTabWidget()
        self.left.addTab(self.preview, "Preview")
        from PySide6.QtWidgets import QScrollArea
        key_scroll = QScrollArea()
        key_scroll.setWidgetResizable(True)
        key_scroll.setWidget(KeyDrawing())
        self.left.addTab(key_scroll, "Key (A, B, C...)")
        key2 = QScrollArea()
        key2.setWidgetResizable(True)
        key2.setWidget(KeyDrawing2())
        self.left.addTab(key2, "Key (V - AD)")
        self.left.setTabToolTip(1, "What each lettered size is.")
        row.addWidget(self.left, 1)
        self.tabs = QTabWidget()
        row.addWidget(self.tabs, 1)
        self.sp = {}
        self.page_of = {}                  # which page each size box is on

        page1 = QWidget()
        form = QFormLayout(page1)
        self.tabs.addTab(page1, "Sizes")
        for key, label, lo, hi, dec, tip in FIELDS:
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
        self.sp_rails = QSpinBox()
        self.sp_rails.setRange(0, 20)
        self.sp_rails.setToolTip("How many level rails (noggins) across each wall, between the studs.")
        form.addRow("Rails across walls", self.sp_rails)
        self.sp_purlins = QSpinBox()
        self.sp_purlins.setRange(0, 20)
        self.sp_purlins.setToolTip("How many purlins across each roof slope, between the rafters.")
        form.addRow("Purlins on roofs", self.sp_purlins)
        conv = QLabel("Sizes are real-world mm. Scale Studio takes the finished frame down to your model "
                      "scale - the presets give the sizes for a printed frame (305 mm = 4 mm in OO).")
        conv.setWordWrap(True)
        conv.setStyleSheet("color: gray;")
        form.addRow(conv)

        pageg = QWidget()
        fg = QFormLayout(pageg)
        self.tabs.addTab(pageg, "Glazing")
        gi = QLabel("Windows get room left round them for a glazing frame (printed separately, glazed with "
                    "film, fitted behind the window). Set the glazing frame width and thickness to make them.")
        gi.setWordWrap(True)
        fg.addRow(gi)
        for key, label, lo, hi, dec, tip in GFIELDS:
            s = QDoubleSpinBox()
            s.setDecimals(dec)
            s.setRange(lo, hi)
            s.setKeyboardTracking(True)
            s.setSuffix(" mm")
            lab = QLabel(label)
            s.setToolTip(tip)
            lab.setToolTip(tip)
            fg.addRow(lab, s)
            self.sp[key] = (s, lab)
            self.page_of[key] = self.tabs.count() - 1
            s.valueChanged.connect(self.changed)
        self.cb_glaze_mode = QComboBox()
        for lab, k in GLAZE_MODES:
            self.cb_glaze_mode.addItem(lab, k)
        self.cb_glaze_mode.setToolTip("Where the glazing frames go: in place behind their windows, in each wall's "
                                      "group; in place but in a 'Glazing frames' group of their own, so you can "
                                      "take them away from the frame; or laid flat in a row beside the building, "
                                      "ready to print.")
        fg.addRow("Glazing frames go", self.cb_glaze_mode)
        self.cb_glaze_mode.currentIndexChanged.connect(self.changed)
        self.lbl_glaze = QLabel()
        self.lbl_glaze.setWordWrap(True)
        self.lbl_glaze.setStyleSheet("color: gray;")
        fg.addRow(self.lbl_glaze)

        pagef = QWidget()
        ff = QFormLayout(pagef)
        self.tabs.addTab(pagef, "Floors")
        fi_ = QLabel("For floors that drop in: a ledge round the inside of the walls under each floor. Type the "
                     "height of the top of each floor, measured up from the bottom of the walls - as many as "
                     "you like, with commas between them (ground floor, first floor, second floor...).")
        fi_.setWordWrap(True)
        ff.addRow(fi_)
        from PySide6.QtWidgets import QLineEdit
        self.ed_levels = QLineEdit()
        self.ed_levels.setPlaceholderText("e.g. 150, 2850, 5550   (empty = no floors)")
        self.ed_levels.setToolTip("The top of each floor, real-world mm up from the bottom of the walls, with "
                                  "commas between them. A floor at 0 sits on the base and needs no ledge.")
        ff.addRow("Floor levels", self.ed_levels)
        self.ed_levels.textChanged.connect(self.changed)
        for key, label, lo, hi, dec, tip in FFIELDS:
            s = QDoubleSpinBox()
            s.setDecimals(dec)
            s.setRange(lo, hi)
            s.setKeyboardTracking(True)
            s.setSuffix(" mm")
            lab = QLabel(label)
            s.setToolTip(tip)
            lab.setToolTip(tip)
            ff.addRow(lab, s)
            self.sp[key] = (s, lab)
            self.page_of[key] = self.tabs.count() - 1
            s.valueChanged.connect(self.changed)
        self.checks_floor = QCheckBox("Make the floor panels too")
        self.checks_floor.setToolTip("Cuts a floor panel for each level, sized to drop in inside the frame and "
                                     "rest on the ledges - a separate piece to print. Straight-sided buildings "
                                     "without inside corners (not L-shaped).")
        ff.addRow(self.checks_floor)
        self.checks_floor.toggled.connect(self.changed)
        self.lbl_floors = QLabel()
        self.lbl_floors.setWordWrap(True)
        self.lbl_floors.setStyleSheet("color: gray;")
        ff.addRow(self.lbl_floors)

        pageb = QWidget()
        fb = QFormLayout(pageb)
        self.tabs.addTab(pageb, "Boards")
        self.check_boards = QCheckBox("Fascia and barge boards, with finials")
        self.check_boards.setToolTip("Fascia boards along the eaves (on the square-cut ends of the truss rafters) "
                                     "and barge boards up the gables, with a finial at each peak - standing off "
                                     "the walls (X) to leave room for brick courses. Each board is its own piece.")
        fb.addRow(self.check_boards)
        self.check_boards.toggled.connect(self.changed)
        self.check_soffits = QCheckBox("Soffit boards under the eaves")
        self.check_soffits.setToolTip("Level boards under the overhang, from the brick face out to the back of the "
                                      "fascia.")
        fb.addRow(self.check_soffits)
        self.check_soffits.toggled.connect(self.changed)
        self.check_roofp = QCheckBox("Roof panels - plain, ready for tiles")
        self.check_roofp.setToolTip("A plain board each side of the roof, lying on the trusses and following their "
                                    "slope, hanging past the fascia into the gutter (AD). Add your tiles on top. "
                                    "The barge boards stand up to cover its edges.")
        fb.addRow(self.check_roofp)
        self.check_roofp.toggled.connect(self.changed)
        # the boards' colour: cream, your own, or left to Layers & Colours
        crow = QHBoxLayout()
        self.cb_bcol = QComboBox()
        for lab_, k_ in BOARD_MODES:
            self.cb_bcol.addItem(lab_, k_)
        self.cb_bcol.setToolTip("The colour the fascia, barge and soffit boards (and the finials) are painted, "
                                "so they stand out from the frame. Cream to start with, or pick your own.")
        self.b_bcol = QPushButton("Pick colour...")
        self.b_bcol.setToolTip("Choose your own colour for the boards.")
        crow.addWidget(self.cb_bcol, 1)
        crow.addWidget(self.b_bcol)
        fb.addRow("Board colour", crow)
        bmode, _brgb = board_colour()
        try:
            self._board_rgb = tuple(int(c) for c in _ui_settings().get('board_rgb', BOARD_CREAM))[:3]
        except Exception:
            self._board_rgb = BOARD_CREAM
        for i_ in range(self.cb_bcol.count()):
            if self.cb_bcol.itemData(i_) == bmode:
                self.cb_bcol.setCurrentIndex(i_)
        self._show_board_colour()
        self.cb_bcol.currentIndexChanged.connect(self._board_mode_changed)
        self.b_bcol.clicked.connect(self._pick_board_colour)
        for key, label, lo, hi, dec, tip in BFIELDS:
            s = QDoubleSpinBox()
            s.setDecimals(dec)
            s.setRange(lo, hi)
            s.setKeyboardTracking(True)
            s.setSuffix(" mm")
            lab = QLabel(label)
            s.setToolTip(tip)
            lab.setToolTip(tip)
            fb.addRow(lab, s)
            self.sp[key] = (s, lab)
            self.page_of[key] = self.tabs.count() - 1
            s.valueChanged.connect(self.changed)
        nb_ = QLabel("0 = worked out from the bar width. The letters are on the 'Key (V - AD)' page. The fascia sits "
                     "on the ends of the truss rafters, so set the truss overhang (Q) to reach past the wall and "
                     "the stand-off (X).")
        nb_.setWordWrap(True)
        nb_.setStyleSheet("color: gray;")
        fb.addRow(nb_)

        page2 = QWidget()
        f2 = QFormLayout(page2)
        self.tabs.addTab(page2, "What to frame")
        self.cb_side = QComboBox()
        for lab, k in SIDES:
            self.cb_side.addItem(lab, k)
        f2.addRow("Frame on", self.cb_side)
        self.checks = {}
        for key, text in (('walls', "Walls"), ('roofs', "Roof slopes"), ('flats', "Floors and flat roofs"),
                          ('perimeter', "Plates and corner posts round the edge"),
                          ('openings', "Posts, lintels and sills round openings"),
                          ('studs', "Studs and rafters"),
                          ('braces', "Diagonal braces at the ends of walls"),
                          ('corners', "Stop short at inside corners")):
            c = QCheckBox(text)
            f2.addRow(c)
            self.checks[key] = c
            c.toggled.connect(self.changed)
        self.cb_truss_style = QComboBox()
        for lab, k in TRUSS_STYLES:
            self.cb_truss_style.addItem(lab, k)
        self.cb_truss_style.setToolTip("What's inside each truss: a king post up the middle and struts out to the "
                                       "rafters, just the king post, or plain - two rafters and a tie.")
        f2.addRow("Truss style", self.cb_truss_style)
        self.cb_truss_style.currentIndexChanged.connect(self.changed)
        note = QLabel("Every bar is its own group. In Scale Studio's Pieces page pick 'Every group with "
                      "faces (smallest pieces)' and tick 'Lay each piece flat' to print them.")
        note.setWordWrap(True)
        note.setStyleSheet("color: gray;")
        f2.addRow(note)


        page3 = QWidget()
        f3 = QFormLayout(page3)
        self.tabs.addTab(page3, "Along lines")
        how = QLabel("1. Draw lines with the line tool where you want bars - snap to the corners of the "
                     "walls, openings and roof.\n2. Select the lines (a line drawn on a wall lies flat "
                     "on that wall).\n3. Click 'Frame along selected lines'. At square corners and where "
                     "a line ends on another, one bar runs through and the other stops square against it. "
                     "A curve (an arch) is one bent bar. Each bar is its own piece.")
        how.setWordWrap(True)
        f3.addRow(how)
        self.cb_linepos = QComboBox()
        for lab, k in LINE_POS:
            self.cb_linepos.addItem(lab, k)
        f3.addRow("Line runs along the", self.cb_linepos)
        how2 = QLabel("Bar size and which side it stands out on come from the other pages.")
        how2.setWordWrap(True)
        how2.setStyleSheet("color: gray;")
        f3.addRow(how2)


        prow = QHBoxLayout()
        prow.addWidget(QLabel("Preset:"))
        self.cb_preset = QComboBox()
        prow.addWidget(self.cb_preset, 1)
        b_up = QPushButton("\u25b2")
        b_up.setToolTip("Moves the preset you have open up the list, so you can put your presets in your own order.")
        b_dn = QPushButton("\u25bc")
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
        self.b_add = QPushButton("Suggest frame for selection")
        self.b_add.setDefault(True)
        self.b_lines = QPushButton("Frame along selected lines")
        b_close = QPushButton("Close")
        self.cb_lasttab = QCheckBox("Open at the last page used")
        self.cb_lasttab.setToolTip("Ticked, the window opens at the page (Sizes, Glazing, Key...) you had open last time.")
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
        brow.addWidget(self.b_lines)
        self.b_showhide = QPushButton("Show / hide...")
        brow.addWidget(self.b_showhide)
        brow.addStretch(1)
        self.b_info = QPushButton("Info")
        self.b_info.setCheckable(True)
        self.b_info.setChecked(False)
        self.b_info.setToolTip("Shows how to use it, and what the last frame you made came out like.")
        self.b_info.toggled.connect(self.toggle_info)
        brow.addWidget(self.b_info)
        brow.addWidget(self.cb_lasttab)
        brow.addWidget(b_close)
        lay.addLayout(brow)

        for w in (self.cb_side, self.cb_linepos):
            w.currentIndexChanged.connect(self.changed)
        self.sp_rails.valueChanged.connect(self.changed)
        self.sp_purlins.valueChanged.connect(self.changed)
        self.cb_preset.currentIndexChanged.connect(self.apply_preset)
        b_save.clicked.connect(self.save_preset)
        b_saveas.clicked.connect(lambda: self.save_preset_as())
        b_del.clicked.connect(self.delete_preset)
        b_dir.clicked.connect(self.open_folder)
        self.b_add.clicked.connect(lambda: self.tool.frame_selection(self))
        self.b_lines.clicked.connect(lambda: self.tool.frame_lines(self))
        self.b_showhide.clicked.connect(self.open_show_hide)
        b_close.clicked.connect(self.close)
        self.refresh_presets()
        self.set_values(cur)
        # click on a piece of the frame in the model and the settings that made it light up here
        self._sel_names = None
        self._lit = []
        try:
            from PySide6.QtCore import QTimer
            self._sel_timer = QTimer(self)
            self._sel_timer.timeout.connect(self.watch_selection)
            self._sel_timer.start(400)
        except Exception:
            pass
        # open on the settings you used last time (set from them in on_activate), showing the
        # preset you last picked - without loading it over the top of your settings
        last = _ui_settings().get('last_preset')
        if last and last in self.preset_order():
            self.refresh_presets(select=last)

    # ---- values ----
    def _show_board_colour(self):
        mode = self.cb_bcol.currentData()
        rgb = self._board_rgb if mode == 'own' else BOARD_CREAM
        self.b_bcol.setEnabled(mode != 'none')
        self.b_bcol.setStyleSheet("" if mode == 'none' else
                                  "background-color: rgb(%d, %d, %d);" % tuple(rgb))

    def _board_mode_changed(self, *_):
        _ui_settings_save(board_mode=self.cb_bcol.currentData())
        self._show_board_colour()

    def _pick_board_colour(self):
        from PySide6.QtWidgets import QColorDialog
        from PySide6.QtGui import QColor
        start = self._board_rgb if self.cb_bcol.currentData() == 'own' else BOARD_CREAM
        c = QColorDialog.getColor(QColor(*start), self, "Board colour")
        if not c.isValid():
            return
        self._board_rgb = (c.red(), c.green(), c.blue())
        _ui_settings_save(board_rgb=list(self._board_rgb), board_mode='own')
        for i_ in range(self.cb_bcol.count()):
            if self.cb_bcol.itemData(i_) == 'own':
                self.cb_bcol.setCurrentIndex(i_)
        self._show_board_colour()

    def open_show_hide(self):
        """The Show / hide pop-up: roof, boards and loose trusses on and off."""
        h = _show_hide_hub()
        if h is not None:
            try:
                h.open_show_hide(self.viewport, 'roof')       # the shared Show / hide window
                return
            except Exception as e:
                print("%s: Show / Hide window didn't open (%s)" % (PLUGIN_NAME, e))
        d = ShowHideDialog._open
        try:
            if d is not None and d.isVisible():
                d.viewport = self.viewport
                d.refresh()
                d.raise_()
                d.activateWindow()
                return
        except Exception:
            pass
        d = ShowHideDialog(self.viewport)
        ShowHideDialog._open = d
        eddy_window(d, PLUGIN_NAME + " - Show / hide", None, place=True)
        d.show()

    def values(self):
        v = dict(side=self.cb_side.currentData() or 'auto',
                 line_pos=self.cb_linepos.currentData() or 'centre',
                 rails=int(self.sp_rails.value()), purlins=int(self.sp_purlins.value()),
                 glaze_mode=self.cb_glaze_mode.currentData() or 'wall', 
                 truss_style=self.cb_truss_style.currentData() or 'struts')
        for key, c in self.checks.items():
            v[key] = c.isChecked()
        for key, (s, _) in self.sp.items():
            v[key] = float(s.value())
        v['trusses'] = v.get('truss_spacing', 0.0) > 0
        v['floor_levels'] = self.ed_levels.text().strip()
        v['floor_panels'] = self.checks_floor.isChecked()
        v['boards'] = self.check_boards.isChecked()
        v['soffits'] = self.check_soffits.isChecked()
        v['roof_panels'] = self.check_roofp.isChecked()
        return v

    def set_values(self, d):
        self._busy = True
        try:
            for cb, key in ((self.cb_side, 'side'), (self.cb_linepos, 'line_pos')):
                if d.get(key) is not None:
                    for i in range(cb.count()):
                        if cb.itemData(i) == d[key]:
                            cb.setCurrentIndex(i)
            for key, c in self.checks.items():
                c.setChecked(bool(d.get(key, DEFAULTS[key])))
            gm_ = d.get('glaze_mode') or ('flat' if d.get('glaze_one') else 'wall')
            self.cb_glaze_mode.setCurrentIndex(max(0, self.cb_glaze_mode.findData(gm_)))
            i_ = self.cb_truss_style.findData(d.get('truss_style', DEFAULTS['truss_style']))
            self.cb_truss_style.setCurrentIndex(max(0, i_))
            self.sp_rails.setValue(int(d.get('rails', DEFAULTS['rails'])))
            self.sp_purlins.setValue(int(d.get('purlins', DEFAULTS['purlins'])))
            for key, (s, _) in self.sp.items():
                s.setValue(float(d.get(key, DEFAULTS[key])))
            lv_ = d.get('floor_levels', DEFAULTS['floor_levels'])
            if isinstance(lv_, (list, tuple)):
                lv_ = ", ".join("%g" % x for x in lv_)
            self.ed_levels.setText(str(lv_ or ""))
            self.checks_floor.setChecked(bool(d.get('floor_panels', DEFAULTS['floor_panels'])))
            self.check_boards.setChecked(bool(d.get('boards', DEFAULTS['boards'])))
            self.check_soffits.setChecked(bool(d.get('soffits', DEFAULTS['soffits'])))
            self.check_roofp.setChecked(bool(d.get('roof_panels', DEFAULTS['roof_panels'])))
        finally:
            self._busy = False
        self.changed()

    def changed(self, *_):
        if self._busy:
            return
        v = self.values()
        # boxes left at 0 show what they come to ('auto 200 mm')
        try:
            for k_, val in _auto_sizes(v).items():
                if k_ in self.sp:
                    self.sp[k_][0].setSpecialValueText("auto  %.0f mm" % val if val > 0 else "auto")
        except Exception:
            pass
        _ui_settings_save(last_values={k: v[k] for k in DEFAULTS if k in v})   # opens like this next time
        self.sp['rafter_spacing'][0].setEnabled(v['roofs'] and v['studs'])
        self.cb_truss_style.setEnabled(v['truss_spacing'] > 0)
        for k_, _l, _a, _b, _c, _t in BFIELDS:
            on_ = v.get('roof_panels') if k_ in ('roof_t', 'roof_over') else (
                v.get('boards') or v.get('soffits') or v.get('roof_panels'))
            self.sp[k_][0].setEnabled(bool(on_))
        self.sp['spacing'][0].setEnabled(v['walls'] and v['studs'])
        self.sp['lintel'][0].setEnabled(v['openings'])
        self.sp['rebate'][0].setEnabled(v['openings'])
        self.sp['glaze_w'][0].setEnabled(v['openings'])
        on = v['openings'] and v['glaze_w'] > 0
        for k in ('glaze_t', 'glaze_setin', 'glaze_inset'):
            self.sp[k][0].setEnabled(on)
        self.cb_glaze_mode.setEnabled(on)
        room = v['rebate'] - v['glaze_setin'] - v['glaze_inset']
        if not v['openings']:
            self.lbl_glaze.setText("Tick 'Posts, lintels and sills round openings' on the What to frame page.")
        elif v['glaze_w'] <= 0:
            self.lbl_glaze.setText("No glazing frames (width 0).")
        elif room < v['glaze_w']:
            self.lbl_glaze.setText("Too wide to fit: room round the opening %.1f - set in %.1f - fit %.1f leaves "
                                   "%.1f mm, so the frames will be %.1f mm wide. Make the room round openings "
                                   "bigger to keep %.1f mm." % (v['rebate'], v['glaze_setin'], v['glaze_inset'],
                                                               max(0.0, room), max(0.0, room), v['glaze_w']))
        else:
            self.lbl_glaze.setText("Glazing frames %.1f mm wide, %.1f mm thick, their inside edge %.1f mm back "
                                   "behind the window edge." % (v['glaze_w'], v['glaze_t'], v['glaze_setin']))
        # the Floors page
        try:
            lv = parse_levels(v['floor_levels'])
            bad_lv = None
        except ValueError as e:
            lv, bad_lv = [], str(e)
        for k in ('floor_t', 'ledge_h', 'ledge_out', 'floor_fit'):
            self.sp[k][0].setEnabled(bool(lv))
        self.checks_floor.setEnabled(bool(lv))
        if bad_lv:
            self.lbl_floors.setText(bad_lv)
        elif not lv:
            self.lbl_floors.setText("No floors - no ledges are made.")
        else:
            lh = v['ledge_h'] if v['ledge_h'] > 0 else v['width']
            lo = v['ledge_out'] if v['ledge_out'] > 0 else v['width']
            txt = "%d floor%s at %s mm. Each ledge %.0f mm tall, standing out %.0f mm past the frame, its top " \
                  "%.0f mm under the floor level." % (len(lv), "s" if len(lv) > 1 else "",
                                                     ", ".join("%g" % x for x in lv), lh, lo, v['floor_t'])
            if v['floor_t'] <= 0:
                txt += " Set the floor thickness, or the floor's top will be level with the ledge."
            if v['floor_panels'] and v['floor_fit'] >= lo:
                txt += " The fit is as big as the ledge - the floors would fall through."
            self.lbl_floors.setText(txt)
        self.preview.show_frame(v)

    def watch_selection(self):
        """Looks at what's selected in the model; for a piece we made, lights up the size boxes that
        set it (and turns to their page)."""
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
        # the report waits behind the Info button; the button says when there's something to read
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
        """Every preset name, in your order (new ones at the end)."""
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
        _ui_settings_save(last_preset=name or None)      # opens on this one next time
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
        _ui_settings_save(last_preset=name)
        return True


# ---------------------------------------------------------------------------
# Show / hide pop-up: the roof, the boards and the loose trusses out of the way,
# so you can see the frame inside. The wall frames themselves are never touched.
# ---------------------------------------------------------------------------
# (key, label, what its groups' names start with)
SHOW_HIDE = [
    ('roof', "Roof - roof panels, tiles, slates, sheeting", ("Roof panel", "Roof - ", "Sheeting - ")),
    ('boards', "Fascia, barge and soffit boards (with finials)", ("Fascia", "Barge", "Soffit")),
    ('trusses', "Free-standing roof trusses", ("Roof truss",)),
]
SHOW_HIDE_TIPS = {
    'roof': "Subframe's roof panels, and roofs from 3D Roof Tiles and 3D Corrugated Iron. Untick to hide "
            "them and see the trusses and frame underneath.",
    'boards': "The fascia boards along the eaves, the barge boards and finials up the gables, and the "
              "soffit boards.",
    'trusses': "The trusses standing in the middle of the roof. The gable end trusses stay - they're part "
               "of their end walls' frames.",
}


def _sh_kids(g):
    return _items(getattr(g, 'children', None))


def _show_hide_hub():
    """3D Show / Hide (the one small window with a tab for each kind of thing), if it's loaded."""
    import sys
    for name, mod in list(sys.modules.items()):
        if mod is not None and (name == "ed3d_show_hide" or name.endswith("_ed3d_show_hide")) \
                and hasattr(mod, 'open_show_hide'):
            return mod
    return None


def show_hide_groups(scene):
    """{key: [groups]} for each line of the Show / hide pop-up. Looks through the whole model, but
    never inside a Subframe group (the wall and roof frames, with their gable end trusses)."""
    found = {k: [] for k, _l, _s in SHOW_HIDE}
    seen = set()

    def walk(groups, depth=0):
        if depth > 12:
            return
        for g in groups:
            if g is None or id(g) in seen:
                continue
            seen.add(id(g))
            name = str(getattr(g, 'name', '') or '')
            if name.startswith("Subframe"):
                continue
            hit = None
            for k, _l, starts in SHOW_HIDE:
                if name.startswith(starts):
                    hit = k
                    break
            if hit:
                found[hit].append(g)
                continue
            walk(_sh_kids(g), depth + 1)
    walk(_items(getattr(scene, 'groups', None)))
    return found


class ShowHideDialog(QWidget):
    """A small window of ticks: ticked is shown, unticked is hidden. Each click is one Ctrl+Z step,
    using IngeTrazo's own Hide, so Edit > Unhide brings things back as well.
    A window of its own: it stays open (even with the Subframe window closed, and Esc or Enter
    don't shut it) until you click its X or Close."""
    _open = None            # the one that's open, kept here so it isn't thrown away

    def __init__(self, viewport):
        from PySide6.QtCore import QTimer, Qt
        top = None
        try:
            top = viewport.window()
        except Exception:
            top = None
        super().__init__(top)
        self.setWindowFlags(Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.viewport = viewport
        self.setWindowTitle("%s - Show / hide" % PLUGIN_NAME)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Ticked = shown. Untick to hide it - the wall frames stay put."))
        self.ticks = {}
        for k, lab, _s in SHOW_HIDE:
            cb = QCheckBox(lab)
            cb.setTristate(False)
            cb.setToolTip(SHOW_HIDE_TIPS.get(k, ""))
            cb.clicked.connect(lambda _on=False, k=k: self.flip(k))
            lay.addWidget(cb)
            self.ticks[k] = (cb, lab)
        row = QHBoxLayout()
        b_all = QPushButton("Show all")
        b_all.setToolTip("Shows everything on this list again.")
        b_close = QPushButton("Close")
        b_close.setToolTip("Closes this window (so does its X). Anything hidden stays hidden.")
        row.addWidget(b_all)
        row.addStretch(1)
        row.addWidget(b_close)
        lay.addLayout(row)
        b_all.clicked.connect(self.show_all)
        b_close.clicked.connect(self.close)
        self._ver = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(700)
        self.refresh()

    def scene(self):
        return getattr(self.viewport, 'scene', None)

    def _poll(self):
        # keeps the ticks right if things are hidden or shown some other way (Edit > Unhide, Ctrl+Z...)
        sc = self.scene()
        v = getattr(sc, 'version', None) if sc is not None else None
        if v != self._ver:
            self.refresh()

    def refresh(self):
        sc = self.scene()
        self._ver = getattr(sc, 'version', None) if sc is not None else None
        found = show_hide_groups(sc) if sc is not None else {}
        for k, (cb, lab) in self.ticks.items():
            gs = found.get(k, [])
            cb.blockSignals(True)
            if not gs:
                cb.setText("%s - none in the model" % lab)
                cb.setChecked(True)
                cb.setEnabled(False)
            else:
                hid = sum(1 for g in gs if getattr(g, 'hidden', False))
                cb.setEnabled(True)
                cb.setText("%s (%d)" % (lab, len(gs)) if hid in (0, len(gs)) else
                           "%s (%d, %d hidden)" % (lab, len(gs), hid))
                cb.setChecked(hid == 0)
            cb.blockSignals(False)

    def _hide(self, groups, hidden):
        groups = [g for g in groups if bool(getattr(g, 'hidden', False)) != hidden]
        if not groups:
            return
        vp = self.viewport
        try:
            from core.history import HideCommand
            vp.history.execute(HideCommand(groups, hidden))
        except Exception as e:
            QMessageBox.warning(self, PLUGIN_NAME, "Couldn't %s them:\n%s" % ("hide" if hidden else "show", e))
            return
        try:
            vp.notify_scene_changed()
        except Exception:
            pass

    def flip(self, key):
        sc = self.scene()
        if sc is None:
            return
        gs = show_hide_groups(sc).get(key, [])
        # shown (or partly shown) -> hide them all; all hidden -> show them all
        hide_them = any(not getattr(g, 'hidden', False) for g in gs)
        self._hide(gs, hide_them)
        self.refresh()

    def show_all(self):
        sc = self.scene()
        if sc is None:
            return
        found = show_hide_groups(sc)
        self._hide([g for gs in found.values() for g in gs], False)
        self.refresh()

    def closeEvent(self, ev):
        try:
            self._timer.stop()
        except Exception:
            pass
        if ShowHideDialog._open is self:
            ShowHideDialog._open = None
        super().closeEvent(ev)


class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
PRINT_NOTE = ("Every bar is its own group: in Scale Studio's Pieces page pick 'Every group with faces "
              "(smallest pieces)' and tick 'Lay each piece flat'.")


class SubframeTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+Y"
    description = "A strengthening frame for model buildings: plates, posts, lintels, studs, braces and " \
                  "roof rafters worked out from the walls and roof, or bars along lines you draw."

    _dialog = None
    _saved = None

    def on_activate(self, viewport):
        dlg = SubframeTool._dialog
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
        if SubframeTool._saved:
            cur.update(SubframeTool._saved)
        last = _ui_settings().get('last_values')
        if isinstance(last, dict):
            cur.update({k: last[k] for k in DEFAULTS if k in last})     # the last settings used
        dlg = FrameDialog(cur, viewport, self)
        SubframeTool._dialog = dlg

        def closed(*_):
            SubframeTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass

    def _start(self, dlg):
        v = dlg.values()
        SubframeTool._saved = dict(v)
        _ui_settings_save(last_values={k: v[k] for k in DEFAULTS if k in v})
        scene = getattr(dlg.viewport, 'scene', None)
        try:
            p = frame_params(v)
        except Exception as e:
            QMessageBox.warning(dlg, PLUGIN_NAME, str(e))
            return None, None, None
        return v, p, scene

    def frame_selection(self, dlg):
        v, p, scene = self._start(dlg)
        if scene is None:
            return
        sel = _items(getattr(scene, 'selection', None))
        groups = [e for e in sel if getattr(e, 'mesh', None) is not None and not hasattr(e, 'loop')]
        if groups and all(_no_frame(e) for e in groups) and not selected_faces(scene):
            QMessageBox.information(dlg, PLUGIN_NAME, "That's a base plate, floor or dividing wall - those don't "
                                    "get a frame. Select the building or its outside walls.")
            return
        faces = selected_faces(scene)
        if not groups and not faces:
            if selected_lines(scene):
                return self.frame_lines(dlg)
            QMessageBox.information(dlg, PLUGIN_NAME, "Select the building (or some of its walls and roof "
                                    "faces) first.")
            return
        infos = []
        every = []                      # every face, to tell how thick the walls are
        gfs = []
        allfs = []                      # every face of what's picked - floors and base plate too
        for g in groups:
            allfs += [FaceInfo(f) for f in _world_faces(g)]
            gfs += [FaceInfo(f) for f in _framable_faces(g)]
        near = []
        bc = None                       # the middle of the building, in plan
        if gfs:
            # the whole building together: its middle tells which side is inside, and the outsides
            # of thick walls are found across all of it - even when each wall is a group of its own.
            # The floors stay in 'every' (the frames stand on them); they just don't get frames.
            every += allfs
            gp = [q for fi in gfs if fi.ok for q in fi.pts]
            c = _plan_centre(gp)
            near = _nearby(scene, gp, groups)
            xs, ys = [q[0] for q in gp], [q[1] for q in gp]
            if gp and min(max(xs) - min(xs), max(ys) - min(ys)) < 0.65 and near:
                # one wall picked on its own: the rest of the building round it says where inside is
                c2 = _plan_centre(gp + [q for fi in near for q in fi.pts])
                if c2:
                    c = (c2[0], c2[1], c[2])
                    p['_one_wall'] = True
            bc = c
            for fi in gfs:
                fi.centre = c
            infos += choose_faces(gfs, v, p, auto_skip=True)
        if faces:
            fis = [FaceInfo(f) for f in faces]
            every += fis
            for fi in fis:
                fi.centre = _mesh_centre(scene, fi.face) or _plan_centre(
                    [q for o in fis if o.ok for q in o.pts])
            infos += choose_faces(fis, v, p, auto_skip=False)
        if not infos:
            QMessageBox.information(dlg, PLUGIN_NAME, "No walls or roof faces to frame in that selection "
                                    "(check the ticks on the 'What to frame' page).")
            return
        p['_floor'], p['_floor_z'] = find_floor(every + near, infos, bc)
        _save_last_build(every, v)
        p['_all_faces'] = every
        panels, problems = frame_panels(infos, v, p)
        if not panels:
            QMessageBox.warning(dlg, PLUGIN_NAME, "\n".join(problems) or "No frame fitted on those faces.")
            return
        n = self.add_to_scene(dlg.viewport, panels, "Subframe", glaze_one=v.get('glaze_mode', 'wall'))
        if n is None:
            return
        # the dividing walls: each end that runs into the new frame is brought back to meet it
        fitted, fit_notes = [], []
        if v.get('fit_dividers', True):
            try:
                fitted, fit_notes = fit_dividers(scene, groups, p.get('_wall_bars') or [],
                                                 p.get('gap', 0.0) * SCALE)
                if fitted:
                    dlg.viewport.history.execute(swap_meshes_command(fitted))
                    try:
                        dlg.viewport.notify_scene_changed()
                    except Exception:
                        pass
            except Exception as e:
                fitted, fit_notes = [], ["Couldn't fit the dividing walls to the frame: %s" % e]
        total = sum(len(b) for _, b in panels)
        kinds = {}
        for t, _ in panels:
            if t in ("Roof trusses", "Floor panels", "Boards", "Roof panels"):
                continue
            kinds[t.split()[0]] = kinds.get(t.split()[0], 0) + 1
        ntr = sum(1 for _t, b in panels for _n, t_, _s in b if t_ == 'truss')
        nmid = sum(len(b) for t, b in panels if t == "Roof trusses")
        msg = "Added %d pieces on %s. %s" % (total, ", ".join("%d %s%s" % (c, k.lower(), "s" if c > 1 else "")
                                                           for k, c in kinds.items()), PRINT_NOTE)
        if fitted:
            msg += "\nBrought %d dividing wall%s back to meet the frame (Ctrl+Z once puts %s back as %s " \
                   "were)." % (len(fitted), "" if len(fitted) == 1 else "s", "it" if len(fitted) == 1 else "them",
                               "it" if len(fitted) == 1 else "they")
        for t_ in fit_notes[:4]:
            msg += "\n" + t_
        if p.get('_floor'):
            msg += "\nKept the frame inside the floor."
        if p.get('_on_floor'):
            msg += " The frame stands on top of the floor, not down into it."
        if p.get('_one_wall'):
            msg += "\nOne wall picked: framed on its %s, worked out from the building round it." % (
                "outside" if v.get('side') == 'front' else "inside")
        if ntr:
            msg += "\n%d roof truss%s - each one flat piece. The gable end trusses are in with their end " \
                   "walls; the %d in the middle are each a group on their own, apart from the frame." % (
                       ntr, "es" if ntr > 1 else "", nmid)
            if p.get('_truss_tails'):
                msg += (" Your roof sits right on the walls, so the overhanging rafter ends couldn't pass over "
                        "them in one piece: they're cut round the walls, and the tails outside are pieces of "
                        "their own ('rafter tail') to glue on under the eaves. Ends cut square for fascia boards.")
            elif v.get('truss_overhang', 0) > 0:
                msg += " Rafter ends cut square for fascia boards."
            ntl = sum(1 for _t, b in panels for n_, t_, _s in b if t_ == 'truss' and 'rafter tail' in n_)
            if ntl:
                ntr -= ntl
            if p.get('_roof_by_trusses'):
                msg += " The trusses hold the roof, so the roof slopes don't get a frame of their own."
            if p.get('_truss_raised'):
                msg += (" Raised %.0f mm (with packers under the tie ends) so the overhanging rafters pass "
                        "over the walls in one piece, like real eaves." % p['_truss_raised'])
                if p.get('_roof_drawn'):
                    msg += (" Your roof sits on the walls, so move it up %.0f mm to sit on the trusses."
                            % p['_truss_raised'])
            if p.get('_truss_seat'):
                msg += " Trusses stand: " + "; ".join(dict.fromkeys(p['_truss_seat'])) + "."
        nb = sum(len(b) for t, b in panels if t == "Boards")
        if nb:
            fh_, bt_, off_, bw_, fnh_, fnd_, fnw_ = board_sizes(p)
            msg += ("\n%d fascia, barge and soffit boards (with a finial at each peak), in a group of their own - "
                    "standing %.0f mm off the walls for brick courses." % (nb, off_))
        nrp = sum(len(b) for t, b in panels if t == "Roof panels")
        if nrp:
            rt_, rov_ = roof_sizes(p)
            msg += ("\n%d plain roof panels on the trusses, %.0f mm thick, hanging %.0f mm past the fascia into the "
                    "gutter - in a 'Roof panels' group, ready for tiles." % (nrp, rt_, rov_))
        if p.get('_levels'):
            nf = sum(len(b) for t, b in panels if t == "Floor panels")
            msg += "\n%d floor ledge%s for %d floor%s" % (
                p.get('_ledges_made', 0), "s" if p.get('_ledges_made', 0) != 1 else "",
                len(p['_levels']), "s" if len(p['_levels']) > 1 else "")
            msg += (", and %d floor panel%s to drop in on them." % (nf, "s" if nf > 1 else "")) if nf else "."
            if p.get('_ledge_low'):
                msg += " Floor at %s mm sits on the base - no ledge needed." % ", ".join(
                    "%g" % x for x in p['_ledge_low'])
        ng = sum(1 for _, b in panels for _n, t_, _s in b if t_ == 'glaze')
        if ng:
            msg += "\n%d glazing frame%s%s." % (ng, "s" if ng > 1 else "",
                                             " - in their own group, 'Glazing frames'" if v.get('glaze_mode') in
                                             ('own', 'flat') else
                                             ", each with its wall")
        if p.get('_glaze_none'):
            msg += ("\n%d window%s too close to the end or top of the wall (or the floor) for a glazing frame - "
                    "glaze %s from the inside instead." % (p['_glaze_none'], "s" if p['_glaze_none'] > 1 else "",
                                                          "them" if p['_glaze_none'] > 1 else "it"))
        if p.get('_glaze_short'):
            msg += "\nSome glazing frames were made narrower to fit - make the room round openings bigger."
        if p.get('_near_end'):
            nn = len(p['_near_end'])
            msg += ("\n%d opening%s closer than 650 mm to the end of %s wall (nearest %.0f mm): fixed - the sides "
                    "of the opening are no longer taken for a wall, so the frame and trusses still run right "
                    "to the corner." % (nn, "s are" if nn > 1 else " is", "their" if nn > 1 else "its",
                                        min(p['_near_end'])))
        if p.get('_end_post_kept'):
            msg += ("\nAn opening near the end of a wall: the room round it was trimmed back on that side, so the "
                    "end post stays whole.")
        if p.get('_skipped'):
            msg += "\nLeft out %d narrow faces (wall and roof edges, reveals) - too small for a frame." % p['_skipped']
        if problems:
            msg += "\n" + "\n".join(problems)
        dlg.show_report(msg, bad=bool(problems))

    def frame_lines(self, dlg):
        v, p, scene = self._start(dlg)
        if scene is None:
            return
        lines = selected_lines(scene)
        if not lines:
            QMessageBox.information(dlg, PLUGIN_NAME, "Select the lines you drew for the bars first.")
            return
        bars, problems = frame_lines(scene, lines, v, p)
        if not bars:
            QMessageBox.warning(dlg, PLUGIN_NAME, "\n".join(problems) or "No bars could be made along those lines.")
            return
        if self.add_to_scene(dlg.viewport, [("Bars along lines", bars)], "Subframe - along lines") is None:
            return
        dlg.show_report("Added %d bars along your lines. %s" % (len(bars), PRINT_NOTE), bad=bool(problems))

    def add_to_scene(self, viewport, panels, top_name, glaze_one=False):
        """A 'Subframe' group, holding a group for each wall or roof face, holding a group for
        each bar - so every bar is a piece of its own."""
        stats = {'faces': 0, 'errors': 0, 'err': None}
        tol = 1e-4 * 0.001
        bmode, brgb = board_colour()
        board_paint = {}

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

        def add_solid(mesh, so):
            verts = {}

            def vx(q):
                k = (round(q[0] / tol), round(q[1] / tol), round(q[2] / tol))
                if k not in verts:
                    verts[k] = VertexWrapper(*q)
                return verts[k]
            hol = getattr(so, 'holes', {})
            made = 0
            for fi, pts in enumerate(so.faces):
                try:
                    hs = [[vx(q) for q in h] for h in hol.get(fi, ())]
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
            return made

        def mutate(scene):
            from core.mesh import Mesh
            from core.group import Group
            panel_groups, loose = [], []
            glaze_group = None
            work = panels
            mode = glaze_one if isinstance(glaze_one, str) else ('flat' if glaze_one else 'wall')
            if mode == 'own':
                # in place behind their windows, but in a group of their own apart from the frame
                gl = [(n_, so) for _pn, bars in panels for n_, typ, so in bars if typ == 'glaze']
                work = [(pn, [b for b in bars if b[1] != 'glaze']) for pn, bars in panels]
                kids = []
                for n_, so in gl:
                    gm = Mesh()
                    if add_solid(gm, so):
                        g = make_group(Group, gm, n_)
                        g.component = False
                        kids.append(g)
                if kids:
                    glaze_group = holder(Group, "Glazing frames (%d)" % len(kids), kids)
                    if glaze_group is None:
                        loose += kids
            elif mode == 'flat':
                # every glazing frame laid flat in a row beside the building, each a piece of its own,
                # all in one group - ready to print as they are
                gl = [(n_, so) for _pn, bars in panels for n_, typ, so in bars if typ == 'glaze']
                work = [(pn, [b for b in bars if b[1] != 'glaze']) for pn, bars in panels]
                if gl:
                    allp = [q for _pn, bars in work for _n, _t, so in bars for f in so.faces for q in f] or \
                           [q for _n, so in gl for f in so.faces for q in f]
                    bx = (max(q[0] for q in allp), min(q[1] for q in allp), min(q[2] for q in allp))
                    sizes = []
                    for _n, so in gl:
                        fl = getattr(so, 'flat', None) or so
                        pts = [q for f in fl.faces for q in f]
                        lo = [min(q[k] for q in pts) for k in range(3)]
                        hi = [max(q[k] for q in pts) for k in range(3)]
                        sizes.append((fl, lo, hi))
                    gap_ = max(0.25 * max(h[1] - l[1] for _f, l, h in sizes), 50.0) * SCALE
                    x = bx[0] + 4.0 * gap_
                    kids = []
                    for (n_, _so), (fl, lo, hi) in zip(gl, sizes):
                        dx, dy, dz = x - lo[0] * SCALE, bx[1] - lo[1] * SCALE, bx[2] - lo[2] * SCALE
                        moved = fl.mapped(lambda q, dx=dx, dy=dy, dz=dz: (q[0] * SCALE + dx, q[1] * SCALE + dy,
                                                                         q[2] * SCALE + dz))
                        x += (hi[0] - lo[0]) * SCALE + gap_
                        gm = Mesh()
                        if add_solid(gm, moved):
                            g = make_group(Group, gm, n_)
                            g.component = False
                            kids.append(g)
                    if kids:
                        glaze_group = holder(Group, "Glazing frames (%d)" % len(kids), kids)
                        if glaze_group is None:
                            loose += kids
            truss_kids = []
            board_groups = []
            for pname, bars in work:
                kids = []
                for name, typ, so in bars:
                    mesh = Mesh()
                    verts = {}

                    def vx(q):
                        k = (round(q[0] / tol), round(q[1] / tol), round(q[2] / tol))
                        if k not in verts:
                            verts[k] = VertexWrapper(*q)
                        return verts[k]
                    hol = getattr(so, 'holes', {})
                    made = 0
                    for fi, pts in enumerate(so.faces):
                        try:
                            hs = [[vx(q) for q in h] for h in hol.get(fi, ())]
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
                    g = make_group(Group, mesh, name)
                    g.component = False
                    if typ in BOARD_TYPES and bmode != 'none':
                        if 'paint' not in board_paint:
                            board_paint['paint'] = _board_attrs(scene, brgb)
                        for f_ in _items(getattr(mesh, 'faces', None)):
                            try:
                                a_ = dict(getattr(f_, 'attrs', None) or {})
                                a_.update(board_paint['paint'])
                                f_.attrs = a_
                            except Exception:
                                pass
                    kids.append(g)
                if not kids:
                    continue
                if pname in ("Boards", "Roof panels") and len(panels) > 1:
                    # fascia, barge and soffit boards - and the roof panels - groups of their own
                    gname = "Fascia and barge boards" if pname == "Boards" else "Roof panels"
                    hg = holder(Group, "%s (%d)" % (gname, len(kids)), kids)
                    if hg is None:
                        loose += kids
                    else:
                        board_groups.append(hg)
                    continue
                if pname == "Roof trusses" and len(panels) > 1:
                    # the trusses in the middle stand apart from the frame, each a group on its own,
                    # so one can be moved or taken out (for a window in the loft) without opening others
                    truss_kids += kids
                    continue
                pg = holder(Group, "%s (%d pieces)" % (pname, len(kids)), kids) if len(panels) > 1 else None
                if pg is not None:
                    panel_groups.append(pg)
                elif len(panels) > 1:
                    loose += kids
                else:
                    panel_groups += kids
            if stats['faces'] == 0:
                raise RuntimeError("No faces could be created (%s)." % stats['err'])
            top = holder(Group, top_name, panel_groups + loose)
            extra_ = [x for x in [glaze_group] + board_groups + truss_kids if x is not None]
            for g in ([top] if top is not None else panel_groups + loose) + extra_:
                _ed3d_organise(scene, g)
                if hasattr(scene, 'add_group') and (top is None or g in extra_):
                    scene.add_group(g)
                else:
                    scene.groups.append(g)
        try:
            viewport.history.execute(SnapshotImport(mutate))
        except Exception as e:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not add the frame:\n%s" % e)
            return None
        try:
            viewport.notify_scene_changed()
        except Exception:
            pass
        return stats['faces']


def run(viewport=None):
    SubframeTool().on_activate(viewport)
