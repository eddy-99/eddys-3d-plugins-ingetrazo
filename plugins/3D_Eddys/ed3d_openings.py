# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Openings for IngeTrazo
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
3D Openings - window and door holes cut through the walls, for IngeTrazo

  Set out       Select one or more walls (or the whole building) and type the openings along
                each wall - W for a window, D for a door, like "W D W". They're spread evenly
                along the wall, bunched in the middle, or put where you type. Windows at a sill
                height you set, doors up from the bottom of the wall (or a step up off it).
                Square, segmental-arch or round tops.
  Tape measure  Click the corner or edge of a wall, move along it, type how far and press Enter:
                the window or door goes in there (a pop-up asks its size as soon as you click the
                edge, and the preview shows that shape while you measure).
  Drawn shapes  Draw a shape on a wall with IngeTrazo's rectangle, circle or line tools,
                select it and it's cut right through the wall - any shape you like.

Windows come out as holes in the wall and doorways are cut up from the bottom edge, with
reveals all round, so the wall stays one solid piece that prints flat. That's the way
3D Subframe (posts, lintels and sills round every opening, room for the glazing frames) and
the Whole building pages of 3D Period Windows and 3D Period Doors (a window or door in every
opening) read the walls - so cut the openings first, then put them in and frame them.

Works on plain walls: a slab with a face front and back (like the walls 3D Floor Plan makes),
before bricks are added. Sizes are real-world mm, like the other plugins - Scale Studio takes
it down to your model scale. Ctrl+Shift+O.
"""

import os
import json
import math
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox, QCheckBox,
    QPushButton, QLabel, QMessageBox, QWidget, QInputDialog, QTabWidget, QLineEdit
)

PLUGIN_NAME = "3D Openings"
VERSION = "1.3"


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


SCALE = 0.001                 # IngeTrazo stores metres; the openings are worked out in real-world mm
PRESET_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Openings")
UI_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_openings.json")
Z = (0.0, 0.0, 1.0)
WALL_MAX = 600.0              # mm: walls up to this thick
TOPS = [("Square top", 'square'), ("Segmental arch (shallow)", 'segment'), ("Round top (half circle)", 'round'),
        ("Round window (a circle, A across)", 'circle')]
DOOR_TOPS = TOPS[:3]
SPREADS = [("Spread evenly along the wall", 'even'), ("Bunched in the middle, gap L between them", 'bunched'),
           ("Where I type (centres, from the left end)", 'typed')]
SIDES = [("The outside of the building (works it out)", 'auto'), ("The other side", 'flip')]
WHICH = [("Outside walls (inside walls left out)", 'outside'), ("Every wall picked", 'all')]

# sizes are real-world mm (IngeTrazo stores metres)
DEFAULTS = dict(
    win_w=900.0, win_h=1350.0, sill=900.0, win_top='square', win_rise=150.0,
    door_w=900.0, door_h=2050.0, step=0.0, door_top='square', door_rise=150.0,
    layout='W D W', spread='even', positions='', ends=650.0, top_keep=150.0, gap=600.0,
    side='auto', which='outside', remove_shapes=True,
    tape_kind='window', tape_to='near', tape_ask=True, tape_count=1)
SIZE_KEYS = ('win_w', 'win_h', 'sill', 'win_rise', 'door_w', 'door_h', 'step', 'door_rise',
             'ends', 'top_keep', 'gap')

BUILTIN_PRESETS = {
    "Cottage - window, door, window": dict(
        win_w=900.0, win_h=1350.0, sill=900.0, win_top='square', door_w=900.0, door_h=2050.0, step=0.0,
        door_top='square', layout='W D W', spread='even', ends=650.0, top_keep=150.0),
    "Terrace front - door and window": dict(
        win_w=1200.0, win_h=1600.0, sill=750.0, win_top='segment', win_rise=150.0, door_w=900.0,
        door_h=2100.0, step=0.0, door_top='square', layout='D W', spread='even', ends=450.0, top_keep=300.0),
    "Station building - round-top windows": dict(
        win_w=1050.0, win_h=2100.0, sill=900.0, win_top='round', door_w=1200.0, door_h=2700.0, step=0.0,
        door_top='round', layout='W W D W W', spread='even', ends=700.0, top_keep=300.0),
    "Goods shed - big doors": dict(
        win_w=1200.0, win_h=900.0, sill=2100.0, win_top='segment', win_rise=200.0, door_w=3000.0,
        door_h=3600.0, step=0.0, door_top='square', layout='W D W', spread='even', ends=900.0, top_keep=300.0),
    "Signal box - row of windows": dict(
        win_w=1100.0, win_h=1000.0, sill=1000.0, win_top='square', layout='W W W W', spread='bunched',
        gap=150.0, ends=450.0, top_keep=150.0),
    "Workshop - arched windows": dict(
        win_w=1500.0, win_h=1800.0, sill=1000.0, win_top='segment', win_rise=250.0, door_w=2400.0,
        door_h=3000.0, door_top='segment', door_rise=250.0, step=0.0, layout='W W D W W', spread='even',
        ends=700.0, top_keep=300.0),
}


def open_params(v):
    """The window's values, ready to use (real-world mm)."""
    p = dict(DEFAULTS)
    p.update(v)
    for key in SIZE_KEYS:
        p[key] = float(p[key])
    p['_kinds'] = parse_layout(p.get('layout', ''))
    return p


def parse_layout(text):
    """'W D W' -> ['window', 'door', 'window']. A number in front repeats it: '10W' is ten windows,
    '3W D 3W' three windows, a door and three more. Spaces, commas and dashes don't matter."""
    out = []
    num = ''
    for ch in str(text or '').upper():
        if ch.isdigit():
            num += ch
            continue
        if ch in 'WD':
            n = int(num) if num else 1
            if n > 200:
                raise ValueError("Openings along the wall: %d is too many in one go." % n)
            out += ['window' if ch == 'W' else 'door'] * n
            num = ''
        elif ch.isalnum():
            raise ValueError("Openings along the wall: '%s' isn't W (a window) or D (a door)." % ch)
    if num:
        raise ValueError("Openings along the wall: put W or D after the %s (like %sW)." % (num, num))
    return out


def parse_numbers(text, what):
    out = []
    for it in str(text or '').replace(';', ',').replace(' ', ',').split(','):
        it = it.strip().lower().replace('mm', '')
        if not it:
            continue
        try:
            out.append(float(it))
        except ValueError:
            raise ValueError("%s: '%s' isn't a number. Type them with commas between, like 900, 2400." % (what, it))
    return out


# ---------------------------------------------------------------------------
# Small geometry helpers
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
    return (a[0] / L, a[1] / L, a[2] / L) if L > 1e-12 else (0.0, 0.0, 0.0)


def area2(poly):
    s = 0.0
    n = len(poly)
    for i in range(n):
        s += poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1]
    return s / 2.0


def bbox(poly):
    xs = [q[0] for q in poly]
    ys = [q[1] for q in poly]
    return min(xs), max(xs), min(ys), max(ys)


def clean(poly, eps=1e-6):
    """Drops repeated corners and corners in the middle of a straight side. None if nothing's left."""
    if not poly:
        return None
    out = []
    for q in poly:
        if not out or abs(q[0] - out[-1][0]) > eps or abs(q[1] - out[-1][1]) > eps:
            out.append((q[0], q[1]))
    while len(out) > 1 and abs(out[0][0] - out[-1][0]) <= eps and abs(out[0][1] - out[-1][1]) <= eps:
        out.pop()
    changed = True
    while changed and len(out) >= 3:
        changed = False
        n = len(out)
        for i in range(n):
            a, b, c = out[i - 1], out[i], out[(i + 1) % n]
            cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            L = math.hypot(c[0] - a[0], c[1] - a[1]) or 1.0
            if abs(cr) / L <= eps * 10:
                out.pop(i)
                changed = True
                break
    return out if len(out) >= 3 and abs(area2(out)) > eps * eps else None


def clip_half(poly, a, b, c):
    """The part of a polygon where a*x + b*y + c >= 0."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp, fq = a * p[0] + b * p[1] + c, a * q[0] + b * q[1] + c
        if fp >= 0:
            out.append(p)
        if (fp >= 0) != (fq >= 0) and abs(fp - fq) > 1e-15:
            t = fp / (fp - fq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def pip(p, poly):
    """Is the point inside the polygon?"""
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        (xi, yi), (xj, yj) = poly[i][:2], poly[j][:2]
        if (yi > p[1]) != (yj > p[1]) and p[0] < (xj - xi) * (p[1] - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _seg_cross(a, b, c, d):
    """Do segments a-b and c-d properly cross (not just touch)?"""
    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    d1, d2, d3, d4 = o(c, d, a), o(c, d, b), o(a, b, c), o(a, b, d)
    return ((d1 > 1e-9 and d2 < -1e-9) or (d1 < -1e-9 and d2 > 1e-9)) and \
           ((d3 > 1e-9 and d4 < -1e-9) or (d3 < -1e-9 and d4 > 1e-9))


def polys_cross(pa, pb):
    na, nb = len(pa), len(pb)
    for i in range(na):
        for j in range(nb):
            if _seg_cross(pa[i], pa[(i + 1) % na], pb[j], pb[(j + 1) % nb]):
                return True
    return False


def inside_poly(inner, outer):
    """Is the whole of `inner` inside `outer` (no corner out, no sides crossing)?"""
    return all(pip(q, outer) for q in inner) and not polys_cross(inner, outer)


def boxes_touch(a, b, gap=0.0):
    return not (a[1] + gap <= b[0] or b[1] + gap <= a[0] or a[3] + gap <= b[2] or b[3] + gap <= a[2])


def _newell(pts):
    nx = ny = nz = 0.0
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    return (nx, ny, nz)


# ---------------------------------------------------------------------------
# The shape of each opening (x along the wall, y up it; mm)
# ---------------------------------------------------------------------------
ARC_STEPS = 16


def opening_poly(x0, y0, w, h, top, rise):
    """An opening's outline, counter-clockwise, from its bottom left corner (x0, y0)."""
    x1, y1 = x0 + w, y0 + h
    if top == 'circle':
        r = w / 2.0                                   # a round (bull's-eye) window: as tall as it's wide
        cx, cy = x0 + r, y0 + r
        n = 2 * ARC_STEPS
        return [(cx + r * math.cos(-math.pi / 2 + 2 * math.pi * k / n), cy + r * math.sin(-math.pi / 2 + 2 * math.pi * k / n))
                for k in range(n)]
    if top == 'round':
        r = w / 2.0
        if h < r + 1e-6:
            raise ValueError("a round top needs the height to be at least half the width (%.0f mm)" % r)
        ys, cx = y1 - r, x0 + r
        arc = [(cx + r * math.cos(math.pi * k / ARC_STEPS), ys + r * math.sin(math.pi * k / ARC_STEPS))
               for k in range(ARC_STEPS + 1)]
        return [(x0, y0), (x1, y0)] + arc
    if top == 'segment' and rise > 1e-6:
        c = w / 2.0
        R = min(rise, c, h - 1.0)
        if R <= 1e-6:
            return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        ys = y1 - R                                   # where the arch springs
        rr = (c * c + R * R) / (2.0 * R)              # the arch's radius
        cx, cy = x0 + c, y1 - rr
        a0 = math.atan2(ys - cy, c)
        a1 = math.pi - a0
        arc = [(cx + rr * math.cos(a0 + (a1 - a0) * k / ARC_STEPS), cy + rr * math.sin(a0 + (a1 - a0) * k / ARC_STEPS))
               for k in range(ARC_STEPS + 1)]
        return [(x0, y0), (x1, y0)] + arc
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def lay_out(p, x_lo, x_hi, y_bot):
    """The openings along one wall: [(kind, outline)], set out with the settings.
    x_lo..x_hi is the length of wall they can go in (both faces), y_bot the bottom of the wall."""
    kinds = p['_kinds']
    if not kinds:
        raise ValueError("Type the openings along the wall on the Placing page - W for a window, D for "
                         "a door, like W D W.")
    widths = [p['win_w'] if k == 'window' else p['door_w'] for k in kinds]
    if min(widths) <= 0:
        raise ValueError("Set the window width (A) and the door width (E) first.")
    L = x_hi - x_lo
    ends = max(0.0, p['ends'])
    tot = sum(widths)
    n = len(kinds)
    xs = []
    if p['spread'] == 'typed':
        cs = parse_numbers(p.get('positions', ''), "Positions")
        if len(cs) < n:
            raise ValueError("%d opening%s along the wall but %d position%s typed - type the middle of "
                             "each one, from the left end of the wall." % (n, "s" if n > 1 else "", len(cs),
                                                                          "s" if len(cs) != 1 else ""))
        xs = [c - w / 2.0 for c, w in zip(cs, widths)]
    elif p['spread'] == 'bunched':
        gap = max(0.0, p['gap'])
        run = tot + gap * (n - 1)
        x = x_lo + (L - run) / 2.0
        for w in widths:
            xs.append(x)
            x += w + gap
    else:
        pier = (L - tot) / (n + 1)
        end = pier
        if pier < ends and n > 1:
            end = ends
            pier = (L - tot - 2.0 * ends) / (n - 1)
        x = x_lo + end
        for w in widths:
            xs.append(x)
            x += w + pier
    if p['spread'] != 'typed' and tot + (n - 1) * (max(0.0, p['gap']) if p['spread'] == 'bunched' else 0.0) \
            + 2.0 * ends > L + 0.5:
        raise ValueError("the openings don't fit - they need %.0f mm with %.0f mm (J) at each end, and the wall "
                         "has %.0f mm. Fewer or narrower openings, or a smaller J." % (
                             tot + 2.0 * ends + (n - 1) * (p['gap'] if p['spread'] == 'bunched' else 0.0), ends, L))
    out = []
    for k, x, w in zip(kinds, xs, widths):
        if k == 'window':
            poly = opening_poly(x, y_bot + p['sill'], w, p['win_h'], p['win_top'], p['win_rise'])
        else:
            poly = opening_poly(x, y_bot + max(0.0, p['step']), w, p['door_h'], p['door_top'], p['door_rise'])
        out.append((k, poly))
    # too near the ends of the wall?
    for k, poly in out:
        x0, x1 = bbox(poly)[:2]
        if x0 < x_lo + ends - 0.5 or x1 > x_hi - ends + 0.5:
            raise ValueError("an opening comes closer than %.0f mm (J) to the end of the wall (it can go from "
                             "%.0f to %.0f mm along it)" % (ends, x_lo + ends, x_hi - ends))
    for (ka, pa), (kb, pb) in zip(out, out[1:]):
        if bbox(pa)[1] > bbox(pb)[0] - 1.0:
            raise ValueError("the openings overlap each other - they need more room along the wall")
    return out


# ---------------------------------------------------------------------------
# Reading the model
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


def _kids_of(g):
    out = []
    for attr in ('children', 'groups'):
        out += _items(getattr(g, attr, None))
    return out


def _walk_groups(groups, out, depth=0):
    for g in _items(groups):
        if depth > 50:
            return
        out.append(g)
        _walk_groups(_kids_of(g), out, depth + 1)


def _as_matrix(m):
    """A group's placement as a QMatrix4x4 (or None for 'where it is')."""
    if m is None:
        return None
    if hasattr(m, 'map'):
        return m
    try:
        from PySide6.QtGui import QMatrix4x4
        vals = [float(x) for x in m]
        if len(vals) == 16:
            return QMatrix4x4(*vals).transposed()       # stored column by column
    except Exception:
        pass
    return None


def _placements(top):
    """(group, world matrix or None) for a group and every group inside it."""
    try:
        from core.group import iter_placements
        return [(g, _as_matrix(m)) for g, m in iter_placements(top)]
    except Exception:
        pass
    out = []

    def walk(g, base, depth):
        m = _as_matrix(getattr(g, 'xform', None))
        if base is not None:
            m = base if m is None else base * m
        out.append((g, m))
        if depth < 30:
            for c in _kids_of(g):
                walk(c, m, depth + 1)
    walk(top, None, 0)
    return out


def _wmap(m, p):
    if m is None:
        return p
    q = m.map(QVector3D(*p))
    return (q.x(), q.y(), q.z())


def _inverse(m):
    if m is None:
        return None
    try:
        inv = m.inverted()
        if isinstance(inv, tuple):
            inv, ok = inv
            if not ok:
                return None
        return inv
    except Exception:
        return None


def _lvec(inv, d):
    """A direction in the world, in a group's own terms."""
    if inv is None:
        return d
    try:
        q = inv.mapVector(QVector3D(*d))
        return v_norm((q.x(), q.y(), q.z()))
    except Exception:
        a, b = _wmap(inv, (0.0, 0.0, 0.0)), _wmap(inv, d)
        return v_norm(v_sub(b, a))


def _faces_of(mesh):
    """[dict(pts, holes, attrs, obj)] for every face of a mesh (its own coordinates, metres)."""
    out = []
    for f in _items(getattr(mesh, 'faces', None)):
        pts = [q for q in (_pos(v) for v in _items(getattr(f, 'vertices', None))) if q is not None]
        if len(pts) < 3:
            continue
        hls = []
        for h in _items(getattr(f, 'holes', None)):
            hp = [q for q in (_pos(v) for v in _items(h)) if q is not None]
            if len(hp) >= 3:
                hls.append(hp)
        out.append({'pts': pts, 'holes': hls, 'attrs': dict(getattr(f, 'attrs', None) or {}), 'obj': f})
    return out


def _face_area(fd):
    n = _newell(fd['pts'])
    a = v_len(n) / 2.0
    for h in fd['holes']:
        a -= v_len(_newell(h)) / 2.0
    return a


def selected_faces(scene):
    out = []
    for e in _items(getattr(scene, 'selection', None)):
        if getattr(e, 'mesh', None) is not None:
            continue
        vs = getattr(e, 'vertices', None)
        if vs is not None and not callable(vs) and len(_items(vs)) >= 3:
            out.append(e)
    return out


def _picked_groups(scene):
    return [e for e in _items(getattr(scene, 'selection', None))
            if getattr(e, 'mesh', None) is not None or _kids_of(e)]


def _in_tree(top, g):
    seen = []
    _walk_groups([top], seen)
    return any(x is g for x in seen)


def _tops_for(scene, picked):
    """The top-level groups holding what's picked (the whole building each one is part of)."""
    out = []
    for t in _items(getattr(scene, 'groups', None)):
        if any(_in_tree(t, g) for g in picked) and all(t is not o for o in out):
            out.append(t)
    return out


def _has_record(g):
    """Has 3D Period Windows or Doors already built windows or doors into this wall?"""
    ext = getattr(g, 'ext', None)
    return isinstance(ext, dict) and any(isinstance(ext.get(k), dict) and ext.get(k).get('orig')
                                         for k in ("ed3d_openings", "ed3d_period_windows"))


_NOT_WALLS = ("inside wall", "floor", "ledge", "plate", "roof", "chimney", "subframe", "glazing", "window",
              "door", "gutter", "pipe", "tile")


class Wall:
    """One wall slab (a group's mesh): its front and back faces, and the way it lies.
    x along the wall from its left end (looking at the front), y up from its bottom, z out of the
    front - all mm."""
    pass


def _centre(pts):
    xs, ys, zs = [q[0] for q in pts], [q[1] for q in pts], [q[2] for q in pts]
    return ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0, (min(zs) + max(zs)) / 2.0)


def union_loops(faces, n):
    """Joins faces lying flat together (sharing corners) into one outline: (outers, holes), each
    a list of 3D loops - outers counter-clockwise round n, holes the other way."""
    tol = 1e-7
    key = lambda q: (round(q[0] / tol), round(q[1] / tol), round(q[2] / tol))
    pt = {}
    edges = {}

    def add_loop(loop, ccw):
        a = v_dot(_newell(loop), n)
        if (a > 0) != ccw:
            loop = list(reversed(loop))
        ks = [key(q) for q in loop]
        for q, k in zip(loop, ks):
            pt.setdefault(k, q)
        for i in range(len(ks)):
            e = (ks[i], ks[(i + 1) % len(ks)])
            if e[0] != e[1]:
                edges[e] = edges.get(e, 0) + 1
    for fd in faces:
        add_loop(fd['pts'], True)
        for h in fd['holes']:
            add_loop(h, False)
    for e in list(edges):
        r = (e[1], e[0])
        if e in edges and r in edges:
            c = min(edges[e], edges[r])
            edges[e] -= c
            edges[r] -= c
    nxt = {}
    for (a, b), c in edges.items():
        for _ in range(c):
            nxt.setdefault(a, []).append(b)
    loops = []
    guard = 0
    while nxt and guard < 100000:
        a0 = next(iter(nxt))
        loop = [a0]
        a = a0
        while guard < 100000:
            guard += 1
            bs = nxt.get(a)
            if not bs:
                break
            b = bs.pop()
            if not bs:
                del nxt[a]
            if b == a0:
                break
            loop.append(b)
            a = b
        if len(loop) >= 3:
            loops.append([pt[k] for k in loop])
    outers, holes = [], []
    for lp in loops:
        (outers if v_dot(_newell(lp), n) > 0 else holes).append(lp)
    return outers, holes


def read_wall(faces, centre, up, flip=False, shapes_in=()):
    """Finds the wall slab in a mesh's faces: Wall, or raises ValueError saying why not.
    centre: the middle of the building (the mesh's own terms), to tell the outside from the inside.
    shapes_in: faces of this mesh that are shapes drawn on the wall (joined back into it)."""
    info = []
    for i, fd in enumerate(faces):
        nv = _newell(fd['pts'])
        L = v_len(nv)
        if L < 1e-12:
            continue
        nn = v_mul(nv, 1.0 / L)
        if abs(v_dot(nn, up)) > 0.05:
            continue                                   # level or sloping: not the side of a wall
        info.append((i, nn, _face_area(fd)))
    info.sort(key=lambda t: -t[2])
    best = None
    for ia, na, aa in info[:12]:
        pa = faces[ia]['pts'][0]
        for ib, nb, ab in info:
            if ib == ia or v_dot(na, nb) > -0.995:
                continue
            d = v_dot(v_sub(pa, faces[ib]['pts'][0]), na) / SCALE
            if not (0.5 < d <= WALL_MAX):
                continue
            score = min(aa, ab)
            if best is None or score > best[0]:
                best = (score, ia, ib, na, d)
        if best is not None:
            break
    if best is None:
        raise ValueError("no wall found - it needs a face front and back, up to %.0f mm apart" % WALL_MAX)
    _s, ia, ib, na, t = best
    ca = _centre(faces[ia]['pts'])
    outward = v_dot(na, v_sub(ca, centre)) >= 0
    if outward == bool(flip):
        ia, ib, na = ib, ia, v_mul(na, -1.0)
    w = Wall()
    w.t = t
    w.n = na
    w.U = v_norm(v_cross(up, na))                     # along the wall, left to right seen from the front
    w.V = v_cross(na, w.U)                            # up
    fpts = faces[ia]['pts']
    O = fpts[0]
    xs = [v_dot(v_sub(q, O), w.U) for q in fpts]
    ys = [v_dot(v_sub(q, O), w.V) for q in fpts]
    w.O = v_add(O, v_add(v_mul(w.U, min(xs)), v_mul(w.V, min(ys))))
    w.front_i, w.back_i = ia, ib
    # shapes drawn on the wall in this mesh: joined back into the face they're on
    fr, bk = [faces[ia]], [faces[ib]]
    w.joined = set()
    for si in shapes_in:
        if si in (ia, ib):
            continue
        q0 = faces[si]['pts'][0]
        dz = v_dot(v_sub(q0, w.O), w.n) / SCALE
        nn = v_norm(_newell(faces[si]['pts']))
        if abs(dz) < 0.05 and v_dot(nn, w.n) > 0.99:
            fr.append(faces[si])
            w.joined.add(si)
        elif abs(dz + t) < 0.05 and v_dot(nn, w.n) < -0.99:
            bk.append(faces[si])
            w.joined.add(si)
    w.front = _side(w, fr, w.n, "front")
    w.back = _side(w, bk, v_mul(w.n, -1.0), "back")
    w.attrs = faces[ia]['attrs']
    w.front_attrs, w.back_attrs = faces[ia]['attrs'], faces[ib]['attrs']
    fo = [q[:2] for q in w.front['outer']]
    bo = [q[:2] for q in w.back['outer']]
    w.y0 = min(q[1] for q in fo)
    w.x_lo = max(min(q[0] for q in fo), min(q[0] for q in bo))
    w.x_hi = min(max(q[0] for q in fo), max(q[0] for q in bo))
    w.height = max(q[1] for q in fo) - w.y0
    w.length = max(q[0] for q in fo) - min(q[0] for q in fo)
    # the faces along the bottom (split under a doorway)
    w.bottom_i = []
    for i, fd in enumerate(faces):
        if i in (ia, ib):
            continue
        if all(abs(v_dot(v_sub(q, w.O), w.V) / SCALE - w.y0) < 0.05 for q in fd['pts']):
            w.bottom_i.append(i)
    return w


def to2(w, q):
    d = v_sub(q, w.O)
    return (v_dot(d, w.U) / SCALE, v_dot(d, w.V) / SCALE, v_dot(d, w.n) / SCALE)


def to3(w, x, y, z):
    return v_add(w.O, v_add(v_mul(w.U, x * SCALE), v_add(v_mul(w.V, y * SCALE), v_mul(w.n, z * SCALE))))


def _side(w, fds, n, which):
    """One side of the wall (front or back), joined into one outline: dict(outer, holes), each
    corner (x, y, original 3D point). Outlines counter-clockwise seen from the front."""
    if len(fds) > 1:
        outers, holes = union_loops(fds, n)
    else:
        outers, holes = [fds[0]['pts']], list(fds[0]['holes'])
    if len(outers) != 1:
        raise ValueError("its %s isn't one flat face (%d pieces)" % (which, len(outers)))

    def conv(loop, ccw):
        pts = [(to2(w, q)[0], to2(w, q)[1], q) for q in loop]
        if (area2(pts) > 0) != ccw:
            pts.reverse()
        return pts
    return {'outer': conv(outers[0], True), 'holes': [conv(h, False) for h in holes]}


# ---------------------------------------------------------------------------
# Cutting the openings
# ---------------------------------------------------------------------------
def check_openings(w, ops, p):
    """Sorts the openings into holes (windows) and notches (doorways up from the bottom edge),
    and checks each one fits. Returns (holes, notches, problems): holes [(name, poly)],
    notches [(name, poly clipped at the bottom, xa, xb)]."""
    keep_top = max(0.0, p.get('top_keep', 0.0))
    fo = [q[:2] for q in w.front['outer']]
    bo = [q[:2] for q in w.back['outer']]
    old = [bbox([q[:2] for q in h]) for side in (w.front, w.back) for h in side['holes']]
    holes, notches, problems, taken = [], [], [], []
    tol = 0.5
    for name, poly in ops:
        poly = clean(poly)
        if not poly:
            continue
        if area2(poly) < 0:
            poly = list(reversed(poly))
        bx = bbox(poly)
        if any(boxes_touch(bx, b, 1.0) for b in taken):
            problems.append("%s overlaps another opening - left out" % name)
            continue
        same = [b for b in old if abs(b[0] - bx[0]) < tol and abs(b[1] - bx[1]) < tol and
                abs(b[2] - bx[2]) < tol and abs(b[3] - bx[3]) < tol]
        if not same and any(boxes_touch(bx, b, 1.0) for b in old):
            problems.append("%s runs into an opening that's already there - left out" % name)
            continue
        top = [(x, y + keep_top) for x, y in poly if y > bx[3] - 1e-6] or [(bx[0], bx[3] + keep_top)]
        top = [(min(max(x, bx[0] + 1.0), bx[1] - 1.0), y) for x, y in top]
        if bx[2] <= w.y0 + tol:
            # a doorway, cut up from the bottom edge
            cut = clean(clip_half(poly, 0.0, 1.0, -w.y0))
            if not cut:
                continue
            xa, xb = bbox(cut)[:2]
            if not all(_on_bottom(o, w.y0, xa, xb) for o in (fo, bo)):
                problems.append("%s: the bottom of the wall isn't straight there - left out" % name)
                continue
            if not all(pip(q, o) for q in top for o in (fo, bo)) or \
                    not all(pip(((xa + xb) / 2.0, w.y0 + 1.0), o) for o in (fo, bo)):
                problems.append("%s is too tall or too near the end for this wall - left out" % name)
                continue
            notches.append((name, cut, xa, xb))
        else:
            if not (inside_poly(poly, fo) and inside_poly(poly, bo)) or \
                    not all(pip(q, o) for q in top for o in (fo, bo)):
                problems.append("%s doesn't fit inside the wall (front and back) with %.0f mm (K) above it - "
                                "left out" % (name, keep_top))
                continue
            holes.append((name, poly, bool(same)))
        taken.append(bx)
    return holes, notches, problems


def _on_bottom(outline, y0, xa, xb):
    """Does the outline have a straight bottom edge, along y0, right across xa..xb (and past it)?"""
    n = len(outline)
    spans = []
    for i in range(n):
        a, b = outline[i], outline[(i + 1) % n]
        if abs(a[1] - y0) < 0.05 and abs(b[1] - y0) < 0.05:
            spans.append((min(a[0], b[0]), max(a[0], b[0])))
    spans.sort()
    run = None
    for lo, hi in spans:
        if run is not None and lo <= run[1] + 0.05:
            run[1] = max(run[1], hi)
        else:
            if run is not None and run[0] < xa - 0.05 and run[1] > xb + 0.05:
                return True
            run = [lo, hi]
    return run is not None and run[0] < xa - 0.05 and run[1] > xb + 0.05


def _insert_notch(outer, y0, cut, xa, xb, z, w):
    """The outline (counter-clockwise corners (x, y, 3D)) with a doorway cut up into its bottom edge.
    Corners along the bottom inside the doorway go (they're in the gap now)."""
    on = lambda q: abs(q[1] - y0) < 0.05
    n = len(outer)
    k = next((i for i in range(n) if not on(outer[i])), None)
    if k is None:
        raise ValueError("no straight bottom edge for the doorway")
    ring = outer[k:] + outer[:k]                       # starts off the bottom: the bottom run is in one piece
    i = max((j for j in range(n) if on(ring[j]) and ring[j][0] <= xa + 0.05 and
             (j + 1 < n and on(ring[j + 1]))), default=None, key=lambda j: ring[j][0])
    if i is None:
        raise ValueError("no straight bottom edge for the doorway")
    j = i + 1
    while j < n and on(ring[j]) and ring[j][0] < xb - 0.05:
        j += 1
    if j >= n or not on(ring[j]):
        raise ValueError("no straight bottom edge for the doorway")
    path = [(x, y, to3(w, x, y, z)) for x, y in _notch_path(cut, y0)]
    if abs(path[0][0] - ring[i][0]) < 0.05:
        path = path[1:]
    if abs(path[-1][0] - ring[j][0]) < 0.05:
        path = path[:-1]
    return ring[:i + 1] + path + ring[j:]


def _notch_path(cut, y0):
    """A doorway's outline as the wall's edge goes round it: from its left foot, up, over and down
    to its right foot."""
    k = min(range(len(cut)), key=lambda i: (abs(cut[i][1] - y0) > 0.05, cut[i][0]))
    ring = cut[k:] + cut[:k]                          # starts at the left foot, counter-clockwise
    return [ring[0]] + list(reversed(ring[1:]))


def cut_wall(faces, w, holes, notches):
    """The wall's faces with the openings cut through: [(points, holes, attrs)] (mesh terms)."""
    t = w.t
    skip = set([w.front_i, w.back_i]) | set(w.joined) | set(w.bottom_i if notches else [])
    out = [(fd['pts'], fd['holes'], fd['attrs']) for i, fd in enumerate(faces) if i not in skip]
    attrs = w.attrs
    # front and back outlines (counter-clockwise seen from the front)
    fo, bo = list(w.front['outer']), list(w.back['outer'])
    for _nm, cut, xa, xb in sorted(notches, key=lambda r: -r[2]):
        fo = _insert_notch(fo, w.y0, cut, xa, xb, 0.0, w)
        bo = _insert_notch(bo, w.y0, cut, xa, xb, -t, w)
    keep_f = [h for h in w.front['holes']]
    keep_b = [h for h in w.back['holes']]

    def drop_same(hs, poly):
        bx = bbox(poly)
        return [h for h in hs if not all(abs(a - b) < 0.5 for a, b in zip(bbox([q[:2] for q in h]), bx))]
    for _nm, poly, same in holes:
        if same:
            keep_f = drop_same(keep_f, poly)
            keep_b = drop_same(keep_b, poly)
    fh = [[q[2] for q in h] for h in keep_f]
    bh = [[q[2] for q in reversed(h)] for h in keep_b]       # the other way round to the back face
    for _nm, poly, _same in holes:
        fh.append([to3(w, x, y, 0.0) for x, y in reversed(poly)])       # the other way round to the face
        bh.append([to3(w, x, y, -t) for x, y in poly])
    out.append(([q[2] for q in fo], fh, dict(w.front_attrs)))
    out.append(([q[2] for q in reversed(bo)], bh, dict(w.back_attrs)))
    # the bottom, split either side of each doorway
    if notches:
        for i in w.bottom_i:
            fd = faces[i]
            pieces = [[to2(w, q) for q in fd['pts']]]
            for _nm, _cut, xa, xb in notches:
                nxt = []
                for pc in pieces:
                    xz = [(q[0], q[2]) for q in pc]
                    for a, b, c in ((-1.0, 0.0, xa), (1.0, 0.0, -xb)):
                        part = clean(clip_half(xz, a, b, c))
                        if part:
                            nxt.append([(x, w.y0, z) for x, z in part])
                pieces = nxt
            for pc in pieces:
                pts = [to3(w, x, y, z) for x, y, z in pc]
                if v_dot(_newell(pts), w.V) > 0:
                    pts.reverse()                       # facing down
                out.append((pts, [], fd['attrs']))
    # reveals: round every opening, from the front of the wall to the back
    for _nm, poly, _same in holes:
        out += _reveals(w, poly, True, attrs)
    for _nm, cut, xa, xb in notches:
        out += _reveals(w, _notch_path(cut, w.y0), False, attrs)
    return out


def _reveals(w, path, closed, attrs):
    """The sides of an opening, facing into it."""
    t = w.t
    pts = list(path)
    n = len(pts)
    out = []
    c2 = (sum(q[0] for q in pts) / n, sum(q[1] for q in pts) / n)
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        a, b = pts[i], pts[(i + 1) % n]
        if math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-6:
            continue
        q = [to3(w, a[0], a[1], 0.0), to3(w, b[0], b[1], 0.0), to3(w, b[0], b[1], -t), to3(w, a[0], a[1], -t)]
        # into the opening: to the left of a counter-clockwise outline, to the right of a doorway's edge
        dx, dy = b[0] - a[0], b[1] - a[1]
        into = (-dy, dx) if closed else (dy, -dx)
        want = v_add(v_mul(w.U, into[0]), v_mul(w.V, into[1]))
        if v_dot(_newell(q), want) < 0:
            q.reverse()
        out.append((q, [], attrs))
    return out


# ---------------------------------------------------------------------------
# Which walls, and the openings in each one
# ---------------------------------------------------------------------------
def _world_pts(mesh, m):
    out = []
    for f in _items(getattr(mesh, 'faces', None)):
        for v in _items(getattr(f, 'vertices', None)):
            q = _pos(v)
            if q is not None:
                out.append(_wmap(m, q))
    return out


def _building_centre(tops):
    pts = []
    for t in tops:
        for g, m in _placements(t):
            mesh = getattr(g, 'mesh', None)
            if mesh is not None:
                pts += _world_pts(mesh, m)
    return _centre(pts) if pts else (0.0, 0.0, 0.0)


def find_walls(scene, which):
    """[(group, mesh, world matrix, picked on its own?)] for the walls in what's picked, and the
    middle of the building(s) they're in (world)."""
    picked = _picked_groups(scene)
    tops = _tops_for(scene, picked)
    places = {}
    for t in tops:
        for g, m in _placements(t):
            places[id(g)] = m
    out, seen = [], set()
    for pg in picked:
        mesh = getattr(pg, 'mesh', None)
        if mesh is not None and _items(getattr(mesh, 'faces', None)):
            if id(pg) not in seen:
                seen.add(id(pg))
                out.append((pg, mesh, places.get(id(pg)), True))
        kids = []
        _walk_groups(_kids_of(pg), kids)
        for g in kids:
            mesh = getattr(g, 'mesh', None)
            if mesh is None or not _items(getattr(mesh, 'faces', None)) or id(g) in seen:
                continue
            name = str(getattr(g, 'name', '') or '').lower().split(" - ")[-1]   # 'Ground floor - Wall 1'
            if which == 'outside' and any(w_ in name for w_ in _NOT_WALLS):
                continue
            seen.add(id(g))
            out.append((g, mesh, places.get(id(g)), False))
    return out, _building_centre(tops) if tops else (0.0, 0.0, 0.0)


def _local(m, centre_w):
    inv = _inverse(m)
    return (_wmap(inv, centre_w) if inv is not None else centre_w), _lvec(inv, Z), inv


def named_ops(laid):
    out, nw, nd = [], 0, 0
    for kind, poly in laid:
        if kind == 'window':
            nw += 1
            out.append(("Window %d" % nw, poly))
        else:
            nd += 1
            out.append(("Door %d" % nd, poly))
    return out


def plan_wall(mesh, m, centre_w, p):
    """(Wall, new faces, holes, notches, problems) for one wall with the set-out openings."""
    centre, up, _inv = _local(m, centre_w)
    faces = _faces_of(mesh)
    w = read_wall(faces, centre, up, p.get('side') == 'flip')
    laid = lay_out(p, w.x_lo, w.x_hi, w.y0)
    holes, notches, problems = check_openings(w, named_ops(laid), p)
    new = cut_wall(faces, w, holes, notches) if (holes or notches) else None
    return w, new, holes, notches, problems


def make_mesh(face_list):
    """A new mesh from [(points, holes, attrs)] (metres). Returns (mesh, faces that failed)."""
    from core.mesh import Mesh
    mesh = Mesh()
    tol = 1e-4 * 0.001
    verts = {}
    bad = [0]

    def vx(q):
        k = (round(q[0] / tol), round(q[1] / tol), round(q[2] / tol))
        if k not in verts:
            verts[k] = VertexWrapper(*q)
        return verts[k]
    for pts, hls, attrs in face_list:
        try:
            outer = [vx(q) for q in pts]
            hs = [[vx(q) for q in h] for h in hls if len(h) >= 3]
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
            bad[0] += 1
            print("%s: a face couldn't be made: %s" % (PLUGIN_NAME, e))
    return mesh, bad[0]


def mesh_of_face(scene, face):
    """(mesh, group or None, world matrix) the face belongs to: the loose geometry, or a group's mesh."""
    m0 = getattr(scene, 'mesh', None)
    try:
        if m0 is not None and face in m0.faces:
            return m0, None, None
    except Exception:
        pass
    for t in _items(getattr(scene, 'groups', None)):
        for g, m in _placements(t):
            mesh = getattr(g, 'mesh', None)
            try:
                if mesh is not None and face in mesh.faces:
                    return mesh, g, m
            except Exception:
                pass
    return None, None, None


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


def openings_command(swaps, removals):
    """One undo step: each wall group gets its new mesh (with the openings cut), and the shapes
    drawn for them are taken away. swaps = [(group, old mesh, new mesh)], removals =
    [(mesh, [faces])]."""
    try:
        from core.history import Command
    except Exception:
        Command = object
    snap_ok = all(hasattr(m, 'capture_state') and hasattr(m, 'restore_state') for m, _f in removals)
    removals = removals if snap_ok else []

    class OpeningsCommand(Command):
        def __init__(self):
            self.before = self.after = None

        def _tidy(self, scene):
            try:
                scene.selection.clear()
            except Exception:
                pass
            try:
                scene.version += 1
            except Exception:
                pass

        def do(self, scene):
            if self.before is None:
                self.before = [(m, m.capture_state()) for m, _f in removals]
                for m, fs in removals:
                    for f in fs:
                        try:
                            remove_face(scene, m, f)
                        except Exception as e:
                            print("%s: couldn't take a drawn shape away: %s" % (PLUGIN_NAME, e))
                self.after = [(m, m.capture_state()) for m, _f in removals]
            else:
                for m, st in self.after:
                    m.restore_state(st)
            for g, _old, new in swaps:
                g.mesh = new
            self._tidy(scene)

        def undo(self, scene):
            for g, old, _new in swaps:
                g.mesh = old
            for m, st in self.before or []:
                m.restore_state(st)
            self._tidy(scene)

    return OpeningsCommand(), snap_ok


def shapes_to_walls(scene, faces, p):
    """Shapes drawn on walls: {id(wall group): [group, mesh, matrix, Wall, faces, [(name, poly)],
    [shape faces]]}, the shapes not on any wall, and problems."""
    walls = {}
    lost = []
    problems = []
    cands = []
    for t in _items(getattr(scene, 'groups', None)):
        centre_t = None
        for g, m in _placements(t):
            mesh = getattr(g, 'mesh', None)
            if mesh is None or not _items(getattr(mesh, 'faces', None)):
                continue
            pts = _world_pts(mesh, m)
            if not pts:
                continue
            lo = tuple(min(q[i] for q in pts) for i in range(3))
            hi = tuple(max(q[i] for q in pts) for i in range(3))
            if centre_t is None:
                centre_t = _building_centre([t])
            cands.append((g, mesh, m, lo, hi, centre_t))
    count = {}
    for face in faces:
        fm, fg, fmx = mesh_of_face(scene, face)
        pts = [q for q in (_pos(v) for v in _items(getattr(face, 'vertices', None))) if q is not None]
        if fm is None or len(pts) < 3:
            continue
        wpts = [_wmap(fmx, q) for q in pts]
        c = _centre(wpts)
        placed = False
        for g, mesh, m, lo, hi, centre_t in cands:
            if not all(lo[i] - 0.01 <= c[i] <= hi[i] + 0.01 for i in range(3)):
                continue
            key = id(g)
            if key in walls:
                entry = walls[key]
            else:
                try:
                    centre, up, inv = _local(m, centre_t)
                    fds = _faces_of(mesh)
                    same = [i for i, fd in enumerate(fds) if any(fd['obj'] is f for f in faces)]
                    w = read_wall(fds, centre, up, p.get('side') == 'flip', same)
                except ValueError:
                    continue
                entry = [g, mesh, m, w, fds, [], [], inv]
            w, inv = entry[3], entry[7]
            lp = [_wmap(inv, q) if inv is not None else q for q in wpts]
            q2 = [to2(w, q) for q in lp]
            zs = [q[2] for q in q2]
            if not (all(abs(z) < 0.5 for z in zs) or all(abs(z + w.t) < 0.5 for z in zs)):
                continue
            poly = clean([(q[0], q[1]) for q in q2])
            if not poly:
                continue
            walls[key] = entry
            door = bbox(poly)[2] <= w.y0 + 0.5
            k = (key, door)
            count[k] = count.get(k, 0) + 1
            entry[5].append(("%s %d" % ("Doorway" if door else "Opening", count[k]), poly))
            if fm is not mesh:
                entry[6].append((fm, face))
            placed = True
            break
        if not placed:
            lost.append(face)
    if lost:
        problems.append("%d shape%s not lying flat on the front or back of a plain wall - left as %s" % (
            len(lost), "s" if len(lost) > 1 else "", "they are" if len(lost) > 1 else "it is"))
    return walls, problems


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
    'Window top': "The shape of the top of each window: square, a shallow segmental arch (rise D), a round "
                  "top (a half circle as wide as the window), or a round window - a circle A across (the height "
                  "B isn't used; C is up to the bottom of the circle).",
    'Door top': "The shape of the top of each door: square, a shallow segmental arch (rise H), or a round top.",
    'Openings along the wall': "W for a window, D for a door, in order from the left end of the wall (looking "
                               "at the outside). 'W D W' = window, door, window. A number in front repeats it: "
                               "'10W' = ten windows, '3W D 3W' = three windows, a door, three windows. Every "
                               "wall you pick gets the same.",
    'Spacing': "Spread evenly: the same gap between the openings and (at least J) at the ends. Bunched: all "
               "together in the middle, gap L between them. Where I type: the middle of each one, from the "
               "left end of the wall.",
    'Positions': "For 'Where I type': the middle of each opening, mm from the left end of the wall (looking at "
                 "the outside), with commas between - one for each W or D.",
    'Measure from': "The outside of the building: worked out from the building round the wall, so the left end "
                    "is on your left as you look at the outside. Or the other side.",
    'Walls': "Picking a whole building: just the outside walls (inside walls, floors and plates from 3D Floor "
             "Plan are left out), or every wall in it. A wall picked on its own always gets openings.",
    'Take the drawn shapes away': "The shapes you drew are taken away once the openings are cut (they'd be left "
                                  "sitting in the hole).",
    'Cut openings in selected walls': "Cuts the openings set out on the Windows, Doors and Placing pages through "
                                      "each wall you've picked (or each wall of the building you've picked).",
    'Cut drawn shapes through': "Cuts each shape you've drawn on a wall (and selected) right through it - any "
                                "shape you like. A shape that reaches the bottom of the wall is a doorway.",
}
EDDY_TIPS.update({
    'Tape measure': "Click the corner or edge of a wall, move along it, type how far and press Enter - the "
                    "window or door goes in there. Esc stops. (The Tape measure page says more.)",
    'What goes in': "A window or a door - its size comes from the Windows or Doors page (or the pop-up).",
    'Measure to': "What the distance you type is measured to: the near side of the opening (like a real tape "
                  "from the corner to the edge of the window), or its middle.",
    'Ask for the size each time (pop-up)': "Ticked, a pop-up asks window or door and its size as soon as you click the "
                                           "edge (filled in from the Windows and Doors pages) and the preview shows "
                                           "that shape - then measure and press Enter to cut it. "
                                           "Not ticked, it's cut straight away with those sizes.",
    'Distance': "If typing in the model doesn't work for you: after clicking the corner, type the distance here "
                "and press Enter.",
})
EDDY_TIPS_END = None

# (key, label, min, max, decimals, tip)
WFIELDS = [
    ('win_w', "A   Window width", 1.0, 50000.0, 1, "How wide each window opening is."),
    ('win_h', "B   Window height", 1.0, 50000.0, 1, "How tall each window opening is, from the sill to the very "
                                                    "top (the top of the arch)."),
    ('sill', "C   Sill height", 0.0, 50000.0, 1, "How high the bottom of each window is, up from the bottom of "
                                                  "the wall."),
    ('win_rise', "D   Arch rise", 0.0, 5000.0, 1, "For a segmental arch: how far the middle of the arch rises "
                                                  "above where it springs from the sides."),
]
DFIELDS = [
    ('door_w', "E   Door width", 1.0, 50000.0, 1, "How wide each doorway is."),
    ('door_h', "F   Door height", 1.0, 50000.0, 1, "How tall each doorway is, to the very top (the top of the "
                                                  "arch)."),
    ('step', "G   Step up off the bottom", 0.0, 5000.0, 1, "0 = the doorway is cut right up from the bottom of "
                                                          "the wall. More than 0 = the door is that far up, a hole "
                                                          "in the wall (3D Period Doors puts steps down to it)."),
    ('door_rise', "H   Arch rise", 0.0, 5000.0, 1, "For a segmental arch: how far the middle of the arch rises "
                                                   "above where it springs from the sides."),
]
PFIELDS = [
    ('ends', "J   Keep from the wall ends", 0.0, 50000.0, 1, "No opening closer than this to the end of the wall - "
                                                             "room for the corner, the wall meeting it and the "
                                                             "subframe's end post. 650 suits 3D Subframe."),
    ('top_keep', "K   Keep below the top", 0.0, 50000.0, 1, "At least this much wall left above every opening, "
                                                            "for the lintel. Openings that would come closer are "
                                                            "left out."),
    ('gap', "L   Gap between (bunched)", 0.0, 50000.0, 1, "For 'Bunched in the middle': the gap between the "
                                                          "openings (the piers)."),
]

INFO_TEXT = ("<b>How to use it</b><br>"
             "Make the walls first (3D Floor Plan, or your own) - plain walls, before the bricks go on. Select "
             "one wall, several, or the whole building, type the openings along the wall on the Placing page "
             "(W D W) and click 'Cut openings in selected walls'.<br><br>"
             "<b>Your own shapes</b><br>"
             "Draw a rectangle, circle or any shape on a wall with IngeTrazo's tools, select it (and as many "
             "more as you like) and click 'Cut drawn shapes through'. A shape reaching the bottom of the wall "
             "becomes a doorway.<br><br>"
             "<b>Then</b><br>"
             "Windows are holes in the wall and doorways are cut up from its bottom edge, with reveals all "
             "round - the way 3D Subframe (posts, lintels, sills, room for the glazing frames) and the Whole "
             "building pages of 3D Period Windows and 3D Period Doors find them. Each wall stays one solid "
             "piece that prints flat.<br><br>"
             "Ctrl+Z puts the walls back. Sizes are real-world mm - Scale Studio takes it down to your model "
             "scale.")


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


class KeyDrawing(QWidget):
    """A drawing that shows what each lettered size is."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(340, 420)

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
        from PySide6.QtCore import QPointF, QRectF, Qt
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 246))
        k = min(float(self.width()) / 360.0, self.height() / 430.0)
        p.scale(k, k)
        wall, hole, red = QColor(196, 120, 90), QColor(250, 250, 246), QColor(200, 40, 40)
        f = QFont()
        f.setBold(True)
        f.setPointSizeF(9.5)
        p.setFont(f)

        def poly(pts, col):
            p.setPen(QPen(col.darker(160), 0.8))
            p.setBrush(col)
            p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in pts]))

        def dim(x1, y1, x2, y2, letter, tx, ty):
            p.setPen(QPen(red, 1.1))
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            ang = math.atan2(y2 - y1, x2 - x1)
            for (x, y, a) in ((x1, y1, ang), (x2, y2, ang + math.pi)):
                for s_ in (0.45, -0.45):
                    p.drawLine(QPointF(x, y), QPointF(x + 6 * math.cos(a + s_), y + 6 * math.sin(a + s_)))
            p.setPen(red)
            p.drawText(QRectF(tx - 12, ty - 9, 24, 18), Qt.AlignCenter, letter)

        def opening(x0, yb, w, h, top, rise):
            pts = opening_poly(x0, 0.0, w, h, top, rise)
            return [(x, yb - y) for x, y in pts]

        p.setPen(QColor(60, 60, 60))
        p.drawText(QRectF(10, 4, 340, 18), Qt.AlignLeft, "A wall from the outside")
        X0, X1, YT, YB = 30.0, 330.0, 60.0, 250.0
        poly([(X0, YB), (X1, YB), (X1, YT), (X0, YT)], wall)
        # window (segmental), door (square, a step up), window (round top)
        wx, ww, wsill, wh = 75.0, 52.0, 70.0, 80.0
        poly(opening(wx, YB - wsill, ww, wh, 'segment', 14.0), hole)
        dx, dw, dh, dstep = 160.0, 46.0, 130.0, 0.0
        poly(opening(dx, YB - dstep, dw, dh, 'square', 0.0), hole)
        rx = 238.0
        poly(opening(rx, YB - wsill, ww, wh, 'round', 0.0), hole)
        # sizes
        dim(wx, YB - wsill - wh - 12, wx + ww, YB - wsill - wh - 12, "A", wx + ww / 2, YB - wsill - wh - 24)
        dim(wx - 10, YB - wsill, wx - 10, YB - wsill - wh, "B", wx - 20, YB - wsill - wh / 2)
        dim(wx + ww / 2, YB, wx + ww / 2, YB - wsill, "C", wx + ww / 2 + 10, YB - wsill / 2)
        dim(wx + ww + 8, YB - wsill - wh + 14, wx + ww + 8, YB - wsill - wh, "D", wx + ww + 18, YB - wsill - wh + 4)
        dim(dx, YB - dh - 12, dx + dw, YB - dh - 12, "E", dx + dw / 2, YB - dh - 24)
        dim(dx + dw + 10, YB, dx + dw + 10, YB - dh, "F", dx + dw + 20, YB - dh / 2)
        dim(X0, YB + 16, wx, YB + 16, "J", (X0 + wx) / 2, YB + 28)
        dim(rx + ww, YB + 16, X1, YB + 16, "J", (rx + ww + X1) / 2, YB + 28)
        dim(rx + ww / 2, YT, rx + ww / 2, YB - wsill - wh, "K", rx + ww / 2 + 10, (YT + YB - wsill - wh) / 2)
        dim(dx + dw, YB - 40, rx, YB - 40, "L", (dx + dw + rx) / 2, YB - 52)
        p.setPen(QColor(90, 90, 90))
        p.drawText(QRectF(X0, YB + 34, X1 - X0, 16), Qt.AlignCenter, "left end            (W D W)            right end")
        # a door up off the bottom, with its step G and a segmental arch H
        Y2B = 400.0
        poly([(X0, Y2B), (X1, Y2B), (X1, Y2B - 110), (X0, Y2B - 110)], wall)
        sx, sw, sh, sg = 140.0, 60.0, 80.0, 18.0
        poly(opening(sx, Y2B - sg, sw, sh, 'segment', 16.0), hole)
        dim(sx + sw + 10, Y2B, sx + sw + 10, Y2B - sg, "G", sx + sw + 20, Y2B - sg / 2)
        dim(sx - 10, Y2B - sg - sh + 16, sx - 10, Y2B - sg - sh, "H", sx - 20, Y2B - sg - sh + 6)
        p.setPen(QColor(60, 60, 60))
        p.drawText(QRectF(X0, Y2B - 132, X1 - X0, 18), Qt.AlignLeft, "A door up off the bottom (G), arched top")
        p.setPen(QColor(110, 110, 110))
        p.drawText(QRectF(X0, Y2B + 6, X1 - X0, 20), Qt.AlignLeft,
                   "B and F go to the very top of the arch. L is for 'Bunched'.")
        p.end()


def _sample_wall(p=None):
    """A plain wall for the preview when no wall is picked: 7000 x 2900 mm, or bigger to fit the
    openings set out."""
    w = Wall()
    L, H = 7000.0, 2900.0
    try:
        kinds = p['_kinds']
        ws = [p['win_w'] if k == 'window' else p['door_w'] for k in kinds]
        hs = [p['sill'] + p['win_h'] if k == 'window' else max(0.0, p['step']) + p['door_h'] for k in kinds]
        gaps = (len(ws) - 1) * (p['gap'] if p['spread'] == 'bunched' else 600.0)
        L = max(L, math.ceil((sum(ws) + gaps + 2.0 * p['ends'] + 400.0) / 500.0) * 500.0)
        H = max(H, math.ceil((max(hs) + p['top_keep'] + 200.0) / 100.0) * 100.0)
    except Exception:
        pass
    rect = [(0.0, 0.0, None), (L, 0.0, None), (L, H, None), (0.0, H, None)]
    w.front = {'outer': rect, 'holes': []}
    w.back = {'outer': rect, 'holes': []}
    w.y0, w.x_lo, w.x_hi, w.length, w.height, w.t = 0.0, 0.0, L, L, H, 230.0
    w.name = "A sample wall, %.0f x %.0f mm" % (L, H)
    return w


class OpeningsPreview(QWidget):
    """The wall picked (or a sample wall), from the outside, with the openings set out on it."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 240)
        self.wall = None
        self.items = []
        self.caption = ""
        self.msg = ""
        self.bad = False

    def show_openings(self, v):
        try:
            p = open_params(v)
        except Exception:
            p = None
        w = self.wall or _sample_wall(p)
        self.items = [([q[:2] for q in w.front['outer']], (196, 120, 90), "")]
        for h in w.front['holes']:
            self.items.append(([q[:2] for q in h], (246, 246, 242), ""))
        try:
            p = open_params(v)
            laid = lay_out(p, w.x_lo, w.x_hi, w.y0)
            holes, notches, problems = check_openings(w, named_ops(laid), p)
            for nm, poly, _s in holes:
                self.items.append((poly, (190, 215, 235), nm))
            for nm, cut, _a, _b in notches:
                self.items.append((cut, (225, 205, 170), nm))
            nn = len(holes) + len(notches)
            self.caption = "%s: %d opening%s" % (getattr(w, 'name', 'This wall'), nn, "s" if nn != 1 else "")
            self.msg = "; ".join(problems)
            self.bad = bool(problems)
        except Exception as e:
            self.caption = getattr(w, 'name', '')
            self.msg = str(e)
            self.bad = True
        self.update()

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen, QFont
        from PySide6.QtCore import QPointF, Qt, QRectF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(246, 246, 242))
        h_cap = 18
        h_msg = 40 if self.msg else 0
        if not self.items:
            p.drawText(self.rect(), Qt.AlignCenter | Qt.TextWordWrap, self.msg or "No preview")
            p.end()
            return
        xs = [q[0] for it in self.items for q in it[0]]
        ys = [q[1] for it in self.items for q in it[0]]
        w, h = self.width() - 20, self.height() - 20 - h_cap - h_msg
        sc = min(w / ((max(xs) - min(xs)) or 1), h / ((max(ys) - min(ys)) or 1))
        ox = 10 + (w - (max(xs) - min(xs)) * sc) / 2 - min(xs) * sc
        oy = 10 + h_cap + h - (h - (max(ys) - min(ys)) * sc) / 2 + min(ys) * sc
        f = QFont()
        f.setPointSizeF(8.0)
        p.setFont(f)
        for pts, rgb, label in self.items:
            col = QColor(*rgb)
            p.setBrush(col)
            p.setPen(QPen(col.darker(170), 1.0))
            p.drawPolygon(QPolygonF([QPointF(ox + x * sc, oy - y * sc) for x, y in pts]))
            if label:
                x0, x1, y0, y1 = bbox(pts)
                p.setPen(QColor(60, 60, 60))
                p.drawText(QRectF(ox + x0 * sc - 20, oy - y1 * sc - 16, (x1 - x0) * sc + 40, 14),
                           Qt.AlignCenter, label)
        f.setBold(True)
        f.setPointSizeF(9.0)
        p.setFont(f)
        p.setPen(QColor(50, 50, 50))
        p.drawText(8, 4, self.width() - 16, h_cap, Qt.AlignLeft | Qt.AlignVCenter, self.caption)
        if self.msg:
            f.setBold(False)
            p.setFont(f)
            p.setPen(QColor(179, 89, 0) if self.bad else QColor(46, 125, 50))
            p.drawText(QRectF(8, self.height() - h_msg - 4, self.width() - 16, h_msg),
                       Qt.AlignLeft | Qt.TextWordWrap, self.msg)
        p.end()


class OpeningsDialog(QDialog):
    def __init__(self, cur, viewport, tool):
        super().__init__(viewport)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.user_presets = load_presets()
        self._busy = False
        lay = QVBoxLayout(self)
        # how to use it, and what the last cut did - only shows when the Info button is pressed
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
        self.preview = OpeningsPreview()
        self.left = QTabWidget()
        self.left.addTab(self.preview, "Preview")
        from PySide6.QtWidgets import QScrollArea
        key_scroll = QScrollArea()
        key_scroll.setWidgetResizable(True)
        key_scroll.setWidget(KeyDrawing())
        self.left.addTab(key_scroll, "Key (A, B, C...)")
        self.left.setTabToolTip(0, "The wall you've picked (or a sample wall) from the outside, with the openings "
                                   "set out on it.")
        self.left.setTabToolTip(1, "What each lettered size is.")
        row.addWidget(self.left, 1)
        self.tabs = QTabWidget()
        row.addWidget(self.tabs, 1)
        self.sp = {}
        self.page_of = {}

        def size_rows(form, fields):
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

        def tops_box(tops=TOPS):
            cb = QComboBox()
            for lab_, k_ in tops:
                cb.addItem(lab_, k_)
            cb.currentIndexChanged.connect(self.changed)
            return cb

        pw = QWidget()
        fw = QFormLayout(pw)
        self.tabs.addTab(pw, "Windows")
        size_rows(fw, WFIELDS)
        self.cb_win_top = tops_box()
        fw.addRow("Window top", self.cb_win_top)
        nw = QLabel("The sill height (C) is up from the bottom of each wall - so on an upper storey from 3D Floor "
                    "Plan it's from that floor.")
        nw.setWordWrap(True)
        nw.setStyleSheet("color: gray;")
        fw.addRow(nw)

        pd = QWidget()
        fd = QFormLayout(pd)
        self.tabs.addTab(pd, "Doors")
        size_rows(fd, DFIELDS)
        self.cb_door_top = tops_box(DOOR_TOPS)
        fd.addRow("Door top", self.cb_door_top)
        nd = QLabel("A doorway is cut up from the bottom of the wall (G = 0), so the wall's bottom edge goes round "
                    "it - the way 3D Subframe and 3D Period Doors look for doors.")
        nd.setWordWrap(True)
        nd.setStyleSheet("color: gray;")
        fd.addRow(nd)

        pp = QWidget()
        fp = QFormLayout(pp)
        self.tabs.addTab(pp, "Placing")
        self.ed_layout = QLineEdit()
        self.ed_layout.setPlaceholderText("e.g.  W D W    or  10W  for ten windows")
        fp.addRow("Openings along the wall", self.ed_layout)
        self.ed_layout.textChanged.connect(self.changed)
        self.cb_spread = QComboBox()
        for lab_, k_ in SPREADS:
            self.cb_spread.addItem(lab_, k_)
        fp.addRow("Spacing", self.cb_spread)
        self.cb_spread.currentIndexChanged.connect(self.changed)
        self.ed_pos = QLineEdit()
        self.ed_pos.setPlaceholderText("e.g.  1200, 3500, 5800   (mm, the middle of each)")
        fp.addRow("Positions", self.ed_pos)
        self.ed_pos.textChanged.connect(self.changed)
        size_rows(fp, PFIELDS)
        self.cb_side = QComboBox()
        for lab_, k_ in SIDES:
            self.cb_side.addItem(lab_, k_)
        fp.addRow("Measure from", self.cb_side)
        self.cb_side.currentIndexChanged.connect(self.changed)
        self.cb_which = QComboBox()
        for lab_, k_ in WHICH:
            self.cb_which.addItem(lab_, k_)
        fp.addRow("Walls", self.cb_which)
        self.cb_which.currentIndexChanged.connect(self.changed)
        self.lbl_place = QLabel()
        self.lbl_place.setWordWrap(True)
        self.lbl_place.setStyleSheet("color: gray;")
        fp.addRow(self.lbl_place)

        pt_ = QWidget()
        ft = QFormLayout(pt_)
        self.tabs.addTab(pt_, "Tape measure")
        how_t = QLabel("1. Click 'Tape measure' (below).\n2. Click the corner or edge of the wall to measure "
                       "from - it snaps to the corners.\n3. The pop-up comes up straight away: say what goes in and "
                       "its size - the preview then shows that shape.\n4. Move along the wall the way the opening "
                       "goes, type the distance (mm) and press Enter - or just click - and it's cut. Then click the "
                       "next corner for another, or Esc to stop.")
        how_t.setWordWrap(True)
        ft.addRow(how_t)
        self.cb_tape_kind = QComboBox()
        for lab_, k_ in TAPE_KINDS:
            self.cb_tape_kind.addItem(lab_, k_)
        ft.addRow("What goes in", self.cb_tape_kind)
        self.cb_tape_to = QComboBox()
        for lab_, k_ in TAPE_TO:
            self.cb_tape_to.addItem(lab_, k_)
        ft.addRow("Measure to", self.cb_tape_to)
        from PySide6.QtWidgets import QSpinBox
        self.sp_tape_count = QSpinBox()
        self.sp_tape_count.setRange(1, 200)
        self.sp_tape_count.setToolTip("How many openings go in a row from where you measure to, each the gap L "
                                      "(Placing page) from the next - 10 = ten windows in a row.")
        ft.addRow("How many in a row", self.sp_tape_count)
        self.sp_tape_count.valueChanged.connect(self.changed)
        self.cb_tape_ask = QCheckBox("Ask for the size each time (pop-up)")
        ft.addRow(self.cb_tape_ask)
        for w_ in (self.cb_tape_kind, self.cb_tape_to):
            w_.currentIndexChanged.connect(self.changed)
        self.cb_tape_ask.toggled.connect(self.changed)
        self.ed_tape = QLineEdit()
        self.ed_tape.setPlaceholderText("or type it here and press Enter")
        self.ed_tape.returnPressed.connect(self._tape_typed)
        ft.addRow("Distance", self.ed_tape)
        nt = QLabel("Heights come from the Windows and Doors pages (sill height C, step G), up from the bottom of "
                    "the wall you measure on. K (keep below the top) still applies.")
        nt.setWordWrap(True)
        nt.setStyleSheet("color: gray;")
        ft.addRow(nt)

        ps = QWidget()
        fs = QFormLayout(ps)
        self.tabs.addTab(ps, "Drawn shapes")
        how = QLabel("1. Draw the opening on the wall with IngeTrazo's rectangle, circle or line tools - on the "
                     "outside or the inside face, any shape.\n2. Select the shapes (as many as you like, on as "
                     "many walls as you like).\n3. Click 'Cut drawn shapes through'. Each one is cut right through "
                     "the wall, with reveals round it. A shape that reaches the bottom of the wall becomes a "
                     "doorway.")
        how.setWordWrap(True)
        fs.addRow(how)
        self.cb_remove = QCheckBox("Take the drawn shapes away")
        fs.addRow(self.cb_remove)
        self.cb_remove.toggled.connect(self.changed)
        hs_ = QLabel("Sizes on the other pages aren't used for drawn shapes - only 'Measure from'.")
        hs_.setWordWrap(True)
        hs_.setStyleSheet("color: gray;")
        fs.addRow(hs_)

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
        self.b_cut = QPushButton("Cut openings in selected walls")
        self.b_cut.setDefault(True)
        self.b_shapes = QPushButton("Cut drawn shapes through")
        self.b_tape = QPushButton("Tape measure")
        self.b_tape.setCheckable(True)
        self.tape = TapeState(self)
        self.tape_tool = None
        b_close = QPushButton("Close")
        self.cb_lasttab = QCheckBox("Open at the last page used")
        self.cb_lasttab.setToolTip("Ticked, the window opens at the page (Windows, Doors, Placing...) you had open "
                                   "last time.")
        st = _ui_settings()
        self.cb_lasttab.setChecked(bool(st.get('remember_tab', True)))
        if self.cb_lasttab.isChecked():
            try:
                self.tabs.setCurrentIndex(int(st.get('tab', 0)))
            except Exception:
                pass
        self.tabs.currentChanged.connect(lambda i: _ui_settings_save(tab=int(i)))
        self.cb_lasttab.toggled.connect(lambda on: _ui_settings_save(remember_tab=bool(on)))
        brow.addWidget(self.b_cut)
        brow.addWidget(self.b_shapes)
        brow.addWidget(self.b_tape)
        brow.addStretch(1)
        self.b_info = QPushButton("Info")
        self.b_info.setCheckable(True)
        self.b_info.setChecked(False)
        self.b_info.setToolTip("Shows how to use it, and what the last openings you cut came out like.")
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
        self.b_cut.clicked.connect(lambda: self.tool.cut_selected(self))
        self.b_shapes.clicked.connect(lambda: self.tool.cut_shapes(self))
        self.b_tape.toggled.connect(self._tape_button)
        b_close.clicked.connect(self.close)
        self.refresh_presets()
        self.set_values(cur)
        # the wall you pick shows in the preview
        self._sel_key = None
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
        v = dict(win_top=self.cb_win_top.currentData() or 'square',
                 door_top=self.cb_door_top.currentData() or 'square',
                 layout=self.ed_layout.text().strip(), positions=self.ed_pos.text().strip(),
                 spread=self.cb_spread.currentData() or 'even', side=self.cb_side.currentData() or 'auto',
                 which=self.cb_which.currentData() or 'outside', remove_shapes=self.cb_remove.isChecked(),
                 tape_kind=self.cb_tape_kind.currentData() or 'window',
                 tape_to=self.cb_tape_to.currentData() or 'near', tape_ask=self.cb_tape_ask.isChecked(),
                 tape_count=int(self.sp_tape_count.value()))
        for key, (s, _) in self.sp.items():
            v[key] = float(s.value())
        return v

    def set_values(self, d):
        self._busy = True
        try:
            for cb, key in ((self.cb_win_top, 'win_top'), (self.cb_door_top, 'door_top'),
                            (self.cb_spread, 'spread'), (self.cb_side, 'side'), (self.cb_which, 'which'),
                            (self.cb_tape_kind, 'tape_kind'), (self.cb_tape_to, 'tape_to')):
                i_ = cb.findData(d.get(key, DEFAULTS[key]))
                cb.setCurrentIndex(max(0, i_))
            self.ed_layout.setText(str(d.get('layout', DEFAULTS['layout']) or ''))
            self.ed_pos.setText(str(d.get('positions', DEFAULTS['positions']) or ''))
            self.cb_remove.setChecked(bool(d.get('remove_shapes', DEFAULTS['remove_shapes'])))
            self.cb_tape_ask.setChecked(bool(d.get('tape_ask', DEFAULTS['tape_ask'])))
            self.sp_tape_count.setValue(int(d.get('tape_count', DEFAULTS['tape_count']) or 1))
            for key, (s, _) in self.sp.items():
                s.setValue(float(d.get(key, DEFAULTS[key])))
        finally:
            self._busy = False
        self.changed()

    def changed(self, *_):
        if self._busy:
            return
        v = self.values()
        _ui_settings_save(last_values={k: v[k] for k in DEFAULTS if k in v})   # opens like this next time
        self.sp['win_rise'][0].setEnabled(v['win_top'] == 'segment')
        self.sp['win_h'][0].setEnabled(v['win_top'] != 'circle')
        self.sp['gap'][0].setEnabled(v['spread'] == 'bunched' or v.get('tape_count', 1) > 1)
        self.sp['door_rise'][0].setEnabled(v['door_top'] == 'segment')
        self.ed_pos.setEnabled(v['spread'] == 'typed')
        try:
            kinds = parse_layout(v['layout'])
            nw, nd = kinds.count('window'), kinds.count('door')
            txt = "%d window%s and %d door%s along each wall, left to right looking at the outside." % (
                nw, "s" if nw != 1 else "", nd, "s" if nd != 1 else "")
            if v['spread'] == 'typed':
                cs = parse_numbers(v['positions'], "Positions")
                if len(cs) < len(kinds):
                    txt += " Type %d position%s - %d so far." % (len(kinds), "s" if len(kinds) > 1 else "",
                                                                len(cs))
            if not kinds:
                txt = "Type W for each window and D for each door, like W D W."
        except ValueError as e:
            txt = str(e)
        self.lbl_place.setText(txt)
        self.preview.show_openings(v)

    def watch_selection(self):
        """The wall you've picked shows in the preview (or the sample wall)."""
        try:
            if not self.isVisible():
                return
            scene = getattr(self.viewport, 'scene', None)
            sel = _items(getattr(scene, 'selection', None)) if scene is not None else []
            key = tuple(id(e) for e in sel)
        except Exception:
            return
        if key == self._sel_key:
            return
        self._sel_key = key
        wall = None
        try:
            v = self.values()
            walls, centre = find_walls(scene, v['which'])
            for g, mesh, m, _direct in walls:
                try:
                    c, up, _inv = _local(m, centre)
                    wall = read_wall(_faces_of(mesh), c, up, v['side'] == 'flip')
                    wall.name = "%s (%.0f mm long)" % (str(getattr(g, 'name', '') or 'The wall'), wall.length)
                    if len(walls) > 1:
                        wall.name += " - and %d more" % (len(walls) - 1)
                    break
                except ValueError:
                    continue
        except Exception:
            wall = None
        self.preview.wall = wall
        self.preview.show_openings(self.values())

    # ---- the tape measure ----
    def scene(self):
        return getattr(self.viewport, 'scene', None)

    def _tape_button(self, on):
        if on:
            self.start_tape()
        else:
            self.stop_tape()

    def start_tape(self):
        try:
            if self.tape_tool is None:
                self.tape_tool = make_tape_tool(self)
            self.viewport.set_active_tool(self.tape_tool)
            self.viewport.setFocus()
        except Exception as e:
            self.show_report("Couldn't start the tape measure: %s" % e, bad=True)
            self.b_tape.blockSignals(True)
            self.b_tape.setChecked(False)
            self.b_tape.blockSignals(False)
            return
        self.b_tape.blockSignals(True)
        self.b_tape.setChecked(True)
        self.b_tape.blockSignals(False)

    def stop_tape(self):
        self.tape.reset()
        try:
            act = getattr(self.viewport.window(), "_activate_tool", None)
            if callable(act):
                act("select")
            else:
                self.viewport.set_active_tool(None)
        except Exception:
            pass
        self.tape_gone(self.tape_tool)

    def tape_gone(self, tool):
        if tool is self.tape_tool:
            try:
                self.b_tape.blockSignals(True)
                self.b_tape.setChecked(False)
                self.b_tape.blockSignals(False)
            except Exception:
                pass

    def _tape_typed(self):
        txt = self.ed_tape.text().strip().lower().replace('mm', '').strip()
        if self.tape.p0 is None:
            self.show_report("Start the tape measure and click the corner or edge of the wall first, then type "
                             "the distance.", bad=True)
            QMessageBox.information(self, PLUGIN_NAME, "Click 'Tape measure', then the corner or edge of the wall "
                                                       "to measure from - then type the distance.")
            return
        try:
            float(txt.replace(',', '.'))
        except ValueError:
            QMessageBox.information(self, PLUGIN_NAME, "Type the distance as a number of mm, like 1200.")
            return
        self.ed_tape.clear()
        self.tape.commit(txt)
        try:
            self.viewport.update()
        except Exception:
            pass

    def show_report(self, text, bad=False):
        self.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if bad else "#2e7d32"))
        self.lbl_report.setText(text)
        self.lbl_report.setVisible(True)
        if not self.b_info.isChecked():
            self.b_info.setText("Info (!)" if bad else "Info (new)")
            self.b_info.setStyleSheet("font-weight: bold; color: %s;" % ("#b35900" if bad else "#2e7d32"))
        self._sel_key = None                       # the walls have changed: look again

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


class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
NEXT_NOTE = ("Next: 3D Period Windows and 3D Period Doors (Whole building page) to put windows and doors in, "
             "and 3D Subframe to frame round them.")


class OpeningsTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Shift+O"
    description = "Window and door openings cut through the walls - set out along each wall (W D W), or any " \
                  "shape you draw on a wall - ready for 3D Subframe, Period Windows and Period Doors."

    _dialog = None

    def on_activate(self, viewport):
        dlg = OpeningsTool._dialog
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
        dlg = OpeningsDialog(cur, viewport, self)
        OpeningsTool._dialog = dlg

        def closed(*_):
            OpeningsTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass

    def _apply(self, dlg, swaps, removals):
        cmd, snap_ok = openings_command(swaps, removals)
        try:
            dlg.viewport.history.execute(cmd)
        except Exception as e:
            QMessageBox.warning(dlg, PLUGIN_NAME, "Could not change the walls:\n%s" % e)
            return None
        try:
            dlg.viewport.notify_scene_changed()
        except Exception:
            pass
        return snap_ok

    def cut_selected(self, dlg):
        v = dlg.values()
        _ui_settings_save(last_values={k: v[k] for k in DEFAULTS if k in v})
        scene = getattr(dlg.viewport, 'scene', None)
        if scene is None:
            return
        try:
            p = open_params(v)
        except ValueError as e:
            QMessageBox.warning(dlg, PLUGIN_NAME, str(e))
            return
        walls, centre = find_walls(scene, p['which'])
        if not walls:
            QMessageBox.information(dlg, PLUGIN_NAME, "Select the walls first (or the whole building).")
            return
        swaps, problems = [], []
        nw = nd = 0
        not_walls = 0
        for g, mesh, m, direct in walls:
            name = str(getattr(g, 'name', '') or 'A wall')
            if _has_record(g):
                problems.append("%s already has windows or doors built in (3D Period Windows / Doors) - take them "
                                "out first, cut the openings, then put them back" % name)
                continue
            try:
                w, new, holes, notches, probs = plan_wall(mesh, m, centre, p)
            except ValueError as e:
                if direct:
                    problems.append("%s: %s" % (name, e))
                else:
                    not_walls += 1
                continue
            problems += ["%s - %s" % (name, x) for x in probs]
            if new is None:
                continue
            nm_, bad = make_mesh(new)
            if bad:
                problems.append("%s: %d face%s couldn't be made - left as it was" % (name, bad, "s" if bad > 1 else ""))
                continue
            swaps.append((g, mesh, nm_))
            nw += sum(1 for x in holes if x[0].startswith("Window"))
            nd += len(notches) + sum(1 for x in holes if x[0].startswith("Door"))
        if not swaps:
            QMessageBox.warning(dlg, PLUGIN_NAME, "No openings were cut.\n" + "\n".join(problems[:12]))
            if problems:
                dlg.show_report("\n".join(problems), bad=True)
            return
        if self._apply(dlg, swaps, []) is None:
            return
        msg = "Cut %d window%s and %d door%s in %d wall%s. %s" % (
            nw, "s" if nw != 1 else "", nd, "s" if nd != 1 else "", len(swaps), "s" if len(swaps) != 1 else "",
            NEXT_NOTE)
        if not_walls:
            msg += "\nLeft out %d part%s that aren't plain walls." % (not_walls, "s" if not_walls > 1 else "")
        if problems:
            msg += "\n" + "\n".join(problems)
        dlg.show_report(msg, bad=bool(problems))

    def cut_shapes(self, dlg):
        v = dlg.values()
        scene = getattr(dlg.viewport, 'scene', None)
        if scene is None:
            return
        p = dict(DEFAULTS)
        p.update(v)
        p['top_keep'] = 0.0                        # a drawn shape goes where it's drawn
        faces = selected_faces(scene)
        if not faces:
            QMessageBox.information(dlg, PLUGIN_NAME, "Draw the openings on the walls, then select them first.")
            return
        walls, problems = shapes_to_walls(scene, faces, p)
        swaps, removals = [], {}
        n = 0
        for key, (g, mesh, m, w, fds, ops, others, _inv) in walls.items():
            name = str(getattr(g, 'name', '') or 'A wall')
            if _has_record(g):
                problems.append("%s already has windows or doors built in (3D Period Windows / Doors) - take them "
                                "out first" % name)
                continue
            holes, notches, probs = check_openings(w, ops, p)
            problems += ["%s - %s" % (name, x) for x in probs]
            if not (holes or notches):
                continue
            new = cut_wall(fds, w, holes, notches)
            nm_, bad = make_mesh(new)
            if bad:
                problems.append("%s: %d face%s couldn't be made - left as it was" % (name, bad, "s" if bad > 1 else ""))
                continue
            swaps.append((g, mesh, nm_))
            n += len(holes) + len(notches)
            if v.get('remove_shapes', True):
                for fm, face in others:
                    removals.setdefault(id(fm), (fm, []))[1].append(face)
        if not swaps:
            QMessageBox.warning(dlg, PLUGIN_NAME, "No openings were cut.\n" + "\n".join(problems[:12]))
            if problems:
                dlg.show_report("\n".join(problems), bad=True)
            return
        snap_ok = self._apply(dlg, swaps, list(removals.values()))
        if snap_ok is None:
            return
        msg = "Cut %d opening%s through %d wall%s. %s" % (n, "s" if n != 1 else "", len(swaps),
                                                         "s" if len(swaps) != 1 else "", NEXT_NOTE)
        if removals and not snap_ok:
            msg += "\nThe drawn shapes couldn't be taken away - delete them yourself."
            problems.append("")
        if problems:
            msg += "\n" + "\n".join(x for x in problems if x)
        dlg.show_report(msg, bad=bool(problems))


def run(viewport=None):
    OpeningsTool().on_activate(viewport)


# ---------------------------------------------------------------------------
# Tape measure: click the corner or edge of a wall, then type how far along the opening goes
# ---------------------------------------------------------------------------
TAPE_KINDS = [("Window", 'window'), ("Door", 'door')]
TAPE_TO = [("The near side of the opening", 'near'), ("The middle of the opening", 'middle')]


def walls_at(scene, pt, centres=None):
    """Every plain wall whose front or back face the point (world) lies on:
    [dict(group, mesh, m, inv, wall, z)] - z is 0 on the front, -thickness on the back."""
    out = []
    centres = {} if centres is None else centres
    for t in _items(getattr(scene, 'groups', None)):
        for g, m in _placements(t):
            mesh = getattr(g, 'mesh', None)
            if mesh is None or not _items(getattr(mesh, 'faces', None)) or _has_record(g):
                continue
            pts = _world_pts(mesh, m)
            if not pts or not all(min(q[i] for q in pts) - 0.002 <= pt[i] <= max(q[i] for q in pts) + 0.002
                                  for i in range(3)):
                continue
            if id(t) not in centres:
                centres[id(t)] = _building_centre([t])
            try:
                centre, up, inv = _local(m, centres[id(t)])
                w = read_wall(_faces_of(mesh), centre, up, False)
            except ValueError:
                continue
            lp = _wmap(inv, pt) if inv is not None else pt
            x, y, z = to2(w, lp)
            if abs(z) < 1.0:
                zs = 0.0
            elif abs(z + w.t) < 1.0:
                zs = -w.t
            else:
                continue
            if -1.0 <= x <= w.length + 1.0 and w.y0 - 1.0 <= y <= w.y0 + w.height + 1.0:
                out.append(dict(group=g, mesh=mesh, m=m, inv=inv, wall=w, z=zs, x0=x))
    return out


class TapeState:
    """What the tape measure is doing: the point measured from, the walls it could be on, and the
    distance typed so far."""
    def __init__(self, dlg):
        self.dlg = dlg
        self.p0 = None
        self.cands = []
        self.hover = None
        self.typed = ""
        self.last = None              # (wall entry, x of the opening's left side, distance) under the mouse

    def reset(self):
        self.p0, self.cands, self.hover, self.typed, self.last = None, [], None, "", None

    def settings(self):
        v = self.dlg.values()
        p = dict(DEFAULTS)
        p.update(v)
        for key in SIZE_KEYS:
            p[key] = float(p[key])
        return v, p

    def pick_wall(self, hp):
        """Of the walls the first point is on (two at a corner), the one the mouse is along."""
        if not self.cands:
            return None
        if hp is None or len(self.cands) == 1:
            return self.cands[0]
        best, score = None, None
        for c in self.cands:
            w = c['wall']
            lp = _wmap(c['inv'], hp) if c['inv'] is not None else hp
            x, y, z = to2(w, lp)
            off = abs(z - c['z'])                                      # off this wall's face
            s = off - 0.01 * abs(x - c['x0'])
            if score is None or s < score:
                best, score = c, s
        return best

    def opening_at(self, d, hp, p):
        """(wall entry, kind, [outlines in the wall's terms], direction) for the openings d mm along the
        wall from the first point, towards the mouse - one, or a row of them (gap L between)."""
        c = self.pick_wall(hp)
        if c is None:
            return None
        w = c['wall']
        sign = 1.0
        if hp is not None:
            lp = _wmap(c['inv'], hp) if c['inv'] is not None else hp
            sign = 1.0 if to2(w, lp)[0] >= c['x0'] else -1.0
        kind = p.get('tape_kind', 'window')
        width = p['win_w'] if kind == 'window' else p['door_w']
        count = max(1, int(p.get('tape_count', 1) or 1))
        step = width + max(0.0, p['gap'])
        if p.get('tape_to', 'near') == 'middle':
            xl = c['x0'] + sign * d - width / 2.0
        else:
            xl = c['x0'] + d if sign > 0 else c['x0'] - d - width
        polys = []
        try:
            for k in range(count):
                x = xl + sign * k * step
                if kind == 'window':
                    polys.append(opening_poly(x, w.y0 + p['sill'], width, p['win_h'], p['win_top'], p['win_rise']))
                else:
                    top = p['door_top'] if p['door_top'] != 'circle' else 'square'
                    polys.append(opening_poly(x, w.y0 + max(0.0, p['step']), width, p['door_h'], top,
                                              p['door_rise']))
        except ValueError:
            return None
        if sign < 0:
            polys.reverse()                           # left to right along the wall
        return c, kind, polys, sign

    def distance_to(self, hp):
        c = self.pick_wall(hp)
        if c is None or hp is None:
            return None
        lp = _wmap(c['inv'], hp) if c['inv'] is not None else hp
        return abs(to2(c['wall'], lp)[0] - c['x0'])

    # ---- what the tool shows
    def lines(self):
        if self.p0 is None:
            return []
        _v, p = self.settings()
        d = self._dist()
        if d is None:
            return []
        got = self.opening_at(d, self.hover, p)
        if got is None:
            return []
        c, kind, polys, sign = got
        w = c['wall']
        V = QVector3D

        def W(x, y):
            q = to3(w, x, y, c['z'])
            return V(*(_wmap(c['m'], q) if c['m'] is not None else q))
        out = []
        for poly in polys:
            n = len(poly)
            for i in range(n):
                out.append((W(*poly[i]), W(*poly[(i + 1) % n])))
        # the tape: along the wall from the first point to the side (or middle) of the opening
        lp0 = _wmap(c['inv'], self.p0) if c['inv'] is not None else self.p0
        y0 = to2(w, lp0)[1]
        x1 = c['x0'] + sign * d
        out.append((W(c['x0'], y0), W(x1, y0)))
        out.append((W(x1, y0 - 60.0), W(x1, y0 + 60.0)))
        return out

    def _dist(self):
        if self.typed:
            try:
                return float(self.typed.replace(',', '.'))
            except ValueError:
                return None
        return self.distance_to(self.hover)

    def status(self):
        if self.p0 is None:
            return "Tape: click the corner or edge of the wall to measure from (Esc = stop)"
        d = self._dist()
        vv = self.dlg.values()
        what = "the middle" if vv.get('tape_to') == 'middle' else "the side"
        what += " of the opening" if int(vv.get('tape_count', 1) or 1) <= 1 else \
            " of the first opening (%d in a row)" % int(vv['tape_count'])
        if self.typed:
            return "Tape: %s mm to %s - Enter to cut it, Backspace to change (Esc = start again)" % (
                self.typed, what)
        return "Tape: %s mm to %s - type a distance and press Enter, or click (Esc = start " \
               "again)" % ("%.0f" % d if d is not None else "-", what)

    # ---- what you do
    def click(self, pt):
        if self.p0 is None:
            cands = walls_at(self.dlg.scene(), pt)
            if not cands:
                self.dlg.show_report("The tape needs to start on the front or back of a plain wall - click its "
                                     "corner or edge.", bad=True)
                return
            self.p0, self.cands, self.typed = pt, cands, ""
            v, _p = self.settings()
            if v.get('tape_ask', True):
                # ask the size now, so the preview follows what's set in the pop-up
                if not ask_opening(self.dlg, v.get('tape_kind', 'window')):
                    self.reset()
                    self.dlg.show_report("Tape: cancelled - click the corner or edge of a wall to start again.")
                    return
            self.dlg.show_report("Tape: now move along the wall, type the distance and press Enter (or click).")
            return
        self.hover = pt
        self.commit()

    def key(self, ch):
        if self.p0 is None:
            return False
        if ch == 'back':
            self.typed = self.typed[:-1]
        elif ch in '0123456789' or (ch in '.,' and not any(c in self.typed for c in '.,')):
            self.typed += ch
        else:
            return False
        return True

    def commit(self, typed=None):
        if self.p0 is None:
            return
        if typed is not None:
            self.typed = str(typed)
        d = self._dist()
        if d is None:
            return
        _v, p = self.settings()          # the size was asked when the edge was clicked
        got = self.opening_at(d, self.hover, p)
        if got is None:
            self.dlg.show_report("That opening can't be made (check its sizes).", bad=True)
            return
        c, kind, polys, _sign = got
        cut_one(self.dlg, c, kind, polys, p)
        self.reset()                    # ready for the next one


def cut_one(dlg, c, kind, polys, p):
    """Cuts the opening (or the row of them) through one wall."""
    w = c['wall']
    name = str(getattr(c['group'], 'name', '') or 'The wall')
    faces = _faces_of(c['mesh'])
    n = len(polys)
    ops = [("The %s" % kind if n == 1 else "%s %d" % (kind.capitalize(), k + 1), pl) for k, pl in enumerate(polys)]
    holes, notches, probs = check_openings(w, ops, p)
    if not (holes or notches):
        dlg.show_report("%s: %s" % (name, "; ".join(probs) or "nothing to cut"), bad=True)
        try:
            QMessageBox.information(dlg, PLUGIN_NAME, "%s:\n%s" % (name, "\n".join(probs) or "nothing to cut"))
        except Exception:
            pass
        return False
    nm_, bad = make_mesh(cut_wall(faces, w, holes, notches))
    if bad:
        dlg.show_report("%s: %d faces couldn't be made - left as it was." % (name, bad), bad=True)
        return False
    if dlg.tool._apply(dlg, [(c['group'], c['mesh'], nm_)], []) is None:
        return False
    made = [pl for _n, pl, *_r in holes] + [cut for _n, cut, _a, _b in notches]
    x0 = min(bbox(pl)[0] for pl in made)
    x1 = max(bbox(pl)[1] for pl in made)
    what = "a %s" % kind if len(made) == 1 else "%d %ss in a row" % (len(made), kind)
    msg = "Cut %s in %s, from %.0f to %.0f mm along it. %s" % (
        what, name, x0, x1, "Click the next corner or edge to measure another, or Esc.")
    if probs:
        msg += "\n" + "\n".join(probs)
    dlg.show_report(msg, bad=bool(probs))
    return True


def ask_opening(dlg, kind):
    """The pop-up: window or door, and its size, filled in from the Windows and Doors pages. OK keeps
    the sizes there for next time."""
    box = QDialog(dlg)
    box.setWindowTitle("%s - the opening" % PLUGIN_NAME)
    f = QFormLayout(box)
    v = dlg.values()
    cb = QComboBox()
    for lab_, k_ in TAPE_KINDS:
        cb.addItem(lab_, k_)
    cb.setCurrentIndex(max(0, cb.findData(kind)))
    f.addRow("Opening", cb)
    sp = {}
    for key, label in (('w', "Width"), ('h', "Height"), ('y', "Sill height")):
        s = QDoubleSpinBox()
        s.setDecimals(1)
        s.setRange(0.0, 50000.0)
        s.setSuffix(" mm")
        f.addRow(label, s)
        sp[key] = s
    tops = QComboBox()
    f.addRow("Top", tops)
    from PySide6.QtWidgets import QSpinBox
    cnt = QSpinBox()
    cnt.setRange(1, 200)
    cnt.setValue(int(v.get('tape_count', 1) or 1))
    f.addRow("How many in a row", cnt)
    gap = QDoubleSpinBox()
    gap.setDecimals(1)
    gap.setRange(0.0, 50000.0)
    gap.setSuffix(" mm")
    gap.setValue(v['gap'])
    f.addRow("Gap between them", gap)
    gap.setEnabled(cnt.value() > 1)
    cnt.valueChanged.connect(lambda n: gap.setEnabled(n > 1))
    ylab = f.labelForField(sp['y'])
    hlab = f.labelForField(sp['h'])

    def round_one(*_):
        on = tops.currentData() == 'circle'
        sp['h'].setEnabled(not on)
        if ylab is not None and cb.currentData() == 'window':
            ylab.setText("Up to the bottom" if on else "Sill height")
        if hlab is not None:
            hlab.setText("Height (not used)" if on else "Height")
    tops.currentIndexChanged.connect(round_one)

    def fill(*_):
        k = cb.currentData()
        tops.blockSignals(True)
        tops.clear()
        for lab_, k_ in (TOPS if k == 'window' else DOOR_TOPS):
            tops.addItem(lab_, k_)
        tops.blockSignals(False)
        if k == 'window':
            sp['w'].setValue(v['win_w'])
            sp['h'].setValue(v['win_h'])
            sp['y'].setValue(v['sill'])
            tops.setCurrentIndex(max(0, tops.findData(v['win_top'])))
            if ylab is not None:
                ylab.setText("Sill height")
        else:
            sp['w'].setValue(v['door_w'])
            sp['h'].setValue(v['door_h'])
            sp['y'].setValue(v['step'])
            tops.setCurrentIndex(max(0, tops.findData(v['door_top'])))
            if ylab is not None:
                ylab.setText("Step up off the bottom")
        round_one()
    cb.currentIndexChanged.connect(fill)
    fill()
    row = QHBoxLayout()
    ok, cancel = QPushButton("Cut it"), QPushButton("Cancel")
    ok.setDefault(True)
    row.addStretch(1)
    row.addWidget(ok)
    row.addWidget(cancel)
    f.addRow(row)
    ok.clicked.connect(box.accept)
    cancel.clicked.connect(box.reject)
    try:
        sp['w'].setFocus()
        sp['w'].selectAll()
    except Exception:
        pass
    if not box.exec():
        return False
    k = cb.currentData()
    d = dlg.values()
    d['tape_kind'] = k
    d['tape_count'] = int(cnt.value())
    d['gap'] = gap.value()
    if k == 'window':
        d.update(win_w=sp['w'].value(), win_h=sp['h'].value(), sill=sp['y'].value(), win_top=tops.currentData())
    else:
        d.update(door_w=sp['w'].value(), door_h=sp['h'].value(), step=sp['y'].value(),
                 door_top=tops.currentData())
    dlg.set_values(d)
    return True


_KEY_CHARS = None


def _key_char(key):
    global _KEY_CHARS
    if _KEY_CHARS is None:
        from PySide6.QtCore import Qt
        _KEY_CHARS = {_key_int(getattr(Qt, 'Key_%d' % i)): str(i) for i in range(10)}
        _KEY_CHARS[_key_int(Qt.Key_Period)] = '.'
        _KEY_CHARS[_key_int(Qt.Key_Comma)] = ','
        _KEY_CHARS[_key_int(Qt.Key_Backspace)] = 'back'
    return _KEY_CHARS.get(_key_int(key))


def _key_int(k):
    for get in (lambda: int(k), lambda: int(k.value)):
        try:
            return get()
        except Exception:
            pass
    return None


def make_tape_tool(dlg):
    """The tape measure tool, made here (not at module level, so it gets no menu entry of its own)."""
    from PySide6.QtCore import Qt
    st = dlg.tape

    class _TapeTool(Tool):
        name = "Openings - tape measure"
        shortcut = None
        uses_snap = True
        wireframe_color = (0.85, 0.20, 0.15, 1.0)

        def on_activate(self, viewport):
            st.reset()

        def on_deactivate(self, viewport):
            st.reset()
            dlg.tape_gone(self)

        def on_hover(self, ctx):
            try:
                q = ctx.world
                st.hover = (float(q.x()), float(q.y()), float(q.z()))
                ctx.viewport.update()
            except Exception:
                pass

        def on_click(self, ctx):
            try:
                q = ctx.world
                st.click((float(q.x()), float(q.y()), float(q.z())))
                ctx.viewport.update()
            except Exception as e:
                dlg.show_report("Tape: %s" % e, bad=True)

        def on_key(self, viewport, key, modifiers):
            if key == Qt.Key_Escape:
                if st.p0 is not None:
                    st.reset()
                else:
                    dlg.stop_tape()
                viewport.update()
                return True
            if key in (Qt.Key_Return, Qt.Key_Enter):
                if st.p0 is not None:
                    st.commit()
                    viewport.update()
                    return True
                return False
            ch = _key_char(key)
            if ch is not None and st.key(ch):
                viewport.update()
                return True
            return False

        def status_clause(self):
            return st.status()

        def rubber_band_lines(self):
            try:
                return st.lines()
            except Exception:
                return []
    return _TapeTool()
