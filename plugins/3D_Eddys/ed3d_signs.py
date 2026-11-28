# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Signs & Boards for IngeTrazo
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
3D Signs & Boards - station name boards, running-in boards on posts, enamel signs and plain
boards for IngeTrazo.

Select a wall face and click Build: the board goes on it, standing off the wall, centred along the
face. Or select a flat face (the platform) for a board on two posts. Nothing selected: it goes at
the origin.

  * The board, with a raised border round it (or none).
  * The words - type or paste them in (Ctrl+V), one line or more. Raised letters in a font from
    your computer, sized to fit the board - or no letters, for a printed paper sign glued on.
  * Lamps along the top: brass lamps on short stems, as many as you like, spaced evenly.
  * Each part a group of its own (board, border, letters, each lamp, posts), so each can be
    coloured and printed on its own. Ctrl+Alt+Shift+N.
"""

import math
import os
import json
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QCheckBox,
                               QDoubleSpinBox, QSpinBox, QPushButton, QLabel, QMessageBox, QWidget,
                               QPlainTextEdit, QInputDialog, QTabWidget)

PLUGIN_NAME = "3D Signs & Boards"
VERSION = "1.8"  # 1.8: the totem humps have rounded sides, not straight sloping ones; 1.7: the totem in three panels like a BR totem - the border runs between the bar and each hump, the humps lean in with rounded top corners, the top and bottom words the same size; 1.6: the totem humps are flat on top with curved-in shoulders, wider and lower, like a BR totem; 1.5: names put right - the shape with humps is the Railway totem, the bar across a circle is a Roundel; 1.4: Station sign shape - round ends and a low hump top and bottom; three lines of words put the first small on the top hump, the name big on the bar and the last small on the bottom hump (Buckley Station style); 1.3: letters made with far fewer faces (their curves in 2% steps - the Llanfair board had 12,000 faces of letters, which slowed Scale Studio); 1.2: railway totems - Shape: Railway totem (a bar right across a circle, the name on the bar), a Railway totem preset, and Gill Sans for the lettering; 1.1: laid out like the other 3D plugins - a 3D view and a Key on the left, Board, Words, Picture, Lamps and Posts pages on the right, presets (Save, Save as, Delete, Folder) and Build along the bottom; 1.0: black and white pictures (any photo or drawing, its dark parts raised) above, beside or filling the board - posters; station name boards, running-in boards on posts, enamel signs and plain boards, with raised lettering (pasted in, more than one line), a border and brass lamps

SCALE = 0.001            # sizes are in mm; IngeTrazo stores geometry in metres


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
MOUNTS = [("wall", "On a wall"), ("posts", "On two posts")]
SHAPES = [("rect", "Board (rectangle)"), ("station", "Railway totem (round ends, a hump top and bottom)"),
          ("totem", "Roundel (bar across a circle)")]
FONTS = [("gill", "Gill Sans (railway signs)"), ("serif", "Serif (like Times)"), ("sans", "Plain (like Arial)"), ("slab", "Slab serif (like Rockwell)"),
         ("fancy", "Fancy (Old English)")]
LETTERING = [("raised", "Raised letters"), ("none", "No letters (stick a printed sign on)")]
FONT_FAMILIES = {'gill': ["Gill Sans MT", "Gill Sans", "Gill Sans Nova", "Arial", "DejaVu Sans"],
                 'serif': ["Times New Roman", "Georgia", "DejaVu Serif", "Liberation Serif", "serif"],
                 'sans': ["Arial", "Helvetica", "DejaVu Sans", "Liberation Sans", "sans-serif"],
                 'slab': ["Rockwell", "Clarendon", "Courier New", "DejaVu Serif"],
                 'fancy': ["Old English Text MT", "Algerian", "Times New Roman"]}

DEFAULTS = dict(text="STATION NAME", shape='rect', totem_bar=40.0, mount='wall', width=0.0, height=450.0, thick=40.0, stand_off=60.0,
                up=0.0, border=40.0, border_out=10.0, lettering='raised', font='sans', bold=True,
                letter_h=0.0, letter_out=10.0, margin=120.0,
                lamps=0, lamp_h=420.0, lamp_dia=260.0, stem=250.0,
                posts_h=1500.0, post_w=120.0, flip=False,
                picture="", pic_pos='above', pic_h=0.0, pic_res=80, pic_threshold=128, pic_dark=True,
                pic_out=10.0)
PIC_POS = [("above", "Above the words"), ("left", "Left of the words"), ("fill", "Fill the board (no words)")]

PRESETS = [
    ("Station name board on the wall, 5 lamps", dict(text="LLANFAIRPWLLGWYNGYLLGOGERYCHWYRNDROBWLLLLANTYSILIOGOGOGOCH",
                                                    mount='wall', width=0.0, height=450.0, border=40.0,
                                                    lettering='raised', font='sans', bold=True, lamps=5,
                                                    lamp_h=420.0, lamp_dia=260.0, stem=250.0)),
    ("Running-in board on two posts", dict(text="STATION NAME", mount='posts', width=0.0, height=900.0,
                                           border=60.0, font='sans', bold=True, lamps=0, posts_h=1500.0,
                                           post_w=150.0)),
    ("Roundel", dict(text="STATION NAME", shape='totem', mount='wall', width=0.0, height=900.0,
                           totem_bar=40.0, thick=25.0, stand_off=20.0, border=30.0, border_out=8.0,
                           lettering='raised', font='gill', bold=False, margin=60.0, lamps=0)),
    ("Railway totem (small words above and below)", dict(text="FLINTSHIRE\nBUCKLEY STATION\nEST. 1890",
                                                     shape='station', mount='wall', width=0.0, height=500.0,
                                                     totem_bar=50.0, thick=25.0, stand_off=20.0, border=15.0,
                                                     border_out=6.0, lettering='raised', font='serif',
                                                     bold=False, margin=40.0, lamps=0)),
    ("Enamel sign (small plate)", dict(text="WAY OUT", mount='wall', width=900.0, height=300.0, thick=20.0,
                                       stand_off=10.0, border=25.0, font='sans', bold=True, lamps=0)),
    ("Poster with a picture", dict(text="LINE ONE\nLINE TWO\nLINE THREE", mount='wall', width=1500.0,
                                   height=2000.0, thick=20.0, stand_off=10.0, border=40.0, font='serif',
                                   bold=True, lamps=0, pic_pos='above', pic_h=0.0, pic_res=80)),
    ("Plain board for a printed sign", dict(text="", mount='wall', width=3000.0, height=450.0, border=0.0,
                                            lettering='none', lamps=0)),
]

UI_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_signs.json")
PRESETS_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Signs")


# ---------------------------------------------------------------------------
# Small helpers
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
    a = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        a += x1 * y2 - x2 * y1
    return a * 0.5


def clean(poly, eps=1e-6):
    out = []
    for p in poly:
        if not out or abs(p[0] - out[-1][0]) > eps or abs(p[1] - out[-1][1]) > eps:
            out.append((float(p[0]), float(p[1])))
    while len(out) > 1 and abs(out[0][0] - out[-1][0]) <= eps and abs(out[0][1] - out[-1][1]) <= eps:
        out.pop()
    return out if len(out) >= 3 and abs(area2(out)) > 1e-9 else None


def _inside_pt(p, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ay > p[1]) != (by > p[1]):
            if p[0] < ax + (p[1] - ay) * (bx - ax) / (by - ay):
                inside = not inside
    return inside


def _items(x):
    if x is None:
        return []
    if callable(x):
        try:
            x = x()
        except Exception:
            return []
    try:
        return list(x)
    except Exception:
        return []


def _pos(v):
    for get in (lambda q: (q.x(), q.y(), q.z()), lambda q: (q.x, q.y, q.z), lambda q: tuple(q)[:3]):
        try:
            p = get(v)
            return (float(p[0]), float(p[1]), float(p[2]))
        except Exception:
            continue
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
            pts = [p for p in (_pos(q) for q in _items(vs)) if p is not None]
            if len(pts) >= 3:
                out.append(pts)
    return out


# ---------------------------------------------------------------------------
# Solids, in the sign's own mm: x along the board, y up, z out from the wall.
# A solid is a list of faces (outer points, [holes]).
# ---------------------------------------------------------------------------
def prism(outer, holes, z0, z1):
    """A solid from a 2D outline (with holes) between z0 and z1."""
    outer = clean(outer)
    if outer is None or z1 - z0 < 1e-9:
        return None
    if area2(outer) < 0:
        outer = list(reversed(outer))
    hs = []
    for h in holes or []:
        h = clean(h)
        if h is None:
            continue
        if area2(h) > 0:
            h = list(reversed(h))
        hs.append(h)
    faces = [([(x, y, z1) for x, y in outer], [[(x, y, z1) for x, y in h] for h in hs]),
             ([(x, y, z0) for x, y in reversed(outer)], [[(x, y, z0) for x, y in reversed(h)] for h in hs])]
    for loop in [outer] + hs:
        n = len(loop)
        for i in range(n):
            (ax, ay), (bx, by) = loop[i], loop[(i + 1) % n]
            faces.append(([(ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1)], []))
    return faces


def box(x0, x1, y0, y1, z0, z1):
    return prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], [], z0, z1)


def lathe(profile, cx, cy, cz, nseg=20):
    """A turned solid about an upright axis at (cx, cz), y up: profile [(radius, y)] from the bottom
    up. Each ring is a band of faces; a ring of radius 0 closes it to a point."""
    rings = []
    for r, y in profile:
        if r <= 1e-6:
            rings.append([(cx, cy + y, cz)])
        else:
            rings.append([(cx + r * math.cos(2 * math.pi * k / nseg), cy + y,
                           cz - r * math.sin(2 * math.pi * k / nseg)) for k in range(nseg)])
    faces = []
    if len(rings[0]) > 1:
        faces.append((list(reversed(rings[0])), []))
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for k in range(nseg):
                faces.append(([a[0], b[k], b[(k + 1) % nseg]], []))
        elif len(b) == 1:
            for k in range(nseg):
                faces.append(([a[k], a[(k + 1) % nseg], b[0]], []))
        else:
            for k in range(nseg):
                faces.append(([a[k], a[(k + 1) % nseg], b[(k + 1) % nseg], b[k]], []))
    if len(rings[-1]) > 1:
        faces.append((list(rings[-1]), []))
    return _outward(faces)


def _outward(faces):
    """The faces turned to face outwards (by the solid's volume)."""
    vol = 0.0
    for outer, _h in faces:
        o = outer[0]
        for i in range(1, len(outer) - 1):
            vol += v_dot(o, v_cross(outer[i], outer[i + 1]))
    if vol < 0:
        return [(list(reversed(outer)), [list(reversed(h)) for h in hs]) for outer, hs in faces]
    return faces


def lamp_solids(cx, y0, cz, v):
    """A brass lamp on a short stem: a little base, the stem, a cap and the bulb-shaped lamp."""
    H, D, st = v['lamp_h'], v['lamp_dia'], v['stem']
    r = D / 2.0
    rs = max(8.0, D * 0.08)
    prof = [(rs * 2.2, 0.0), (rs * 2.2, rs * 0.8), (rs, rs * 0.8), (rs, st),            # base and stem
            (r * 0.45, st), (r * 0.45, st + H * 0.08),                                    # the cap
            (r * 0.95, st + H * 0.30), (r, st + H * 0.48), (r * 0.85, st + H * 0.68),    # the bulb
            (r * 0.45, st + H * 0.86), (r * 0.2, st + H * 0.95), (0.0, st + H)]
    return lathe(prof, cx, y0, cz)


# ---------------------------------------------------------------------------
# Letters, from a font on this computer
# ---------------------------------------------------------------------------
def text_loops(text, font='sans', bold=True):
    """The outlines of the letters of one line of text (y up, font units)."""
    from PySide6.QtGui import QPainterPath, QFont
    fams = FONT_FAMILIES.get(font, FONT_FAMILIES['sans'])
    f = QFont(fams[0])
    try:
        f.setFamilies(fams)
    except Exception:
        pass
    f.setPixelSize(200)
    f.setBold(bool(bold))
    path = QPainterPath()
    path.addText(0.0, 0.0, f, text)
    try:
        path = path.simplified()
    except Exception:
        pass
    loops = []
    for poly in path.toSubpathPolygons():
        pts = [(float(p.x()), -float(p.y())) for p in poly]
        if len(pts) > 1 and abs(pts[0][0] - pts[-1][0]) < 1e-6 and abs(pts[0][1] - pts[-1][1]) < 1e-6:
            pts.pop()
        q = clean(pts, 1e-3)
        if q and abs(area2(q)) > 1e-3:
            loops.append(q)
    return loops


def group_loops(loops):
    """[(outline, [holes])]: a loop inside an odd number of others is a hole in the smallest one."""
    info = []
    for i, lp in enumerate(loops):
        a = abs(area2(lp))
        inside = [j for j, other in enumerate(loops) if j != i and abs(area2(other)) > a
                  and _inside_pt(lp[0], other)]
        info.append((i, inside))
    outers = {i: [] for i, inside in info if len(inside) % 2 == 0}
    for i, inside in info:
        if len(inside) % 2 == 1:
            parents = [j for j in inside if j in outers]
            if parents:
                outers[min(parents, key=lambda j: abs(area2(loops[j])))].append(loops[i])
    return [(loops[i], hs) for i, hs in outers.items()]


def thin(pts, tol):
    """Fewer points on a curved outline (far finer than any print still)."""
    if len(pts) < 8:
        return pts
    out = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) >= tol:
            out.append(p)
    return out if len(out) >= 3 and abs(area2(out)) > 0.5 * abs(area2(pts)) else pts


def lines_of(text):
    return [ln.strip() for ln in (text or "").replace("\r", "").split("\n") if ln.strip()]


def text_size(lines, font, bold):
    """(widest line, line height) of the text in font units, and the loops of each line."""
    per = []
    for ln in lines:
        lp = text_loops(ln, font, bold)
        if lp:
            xs = [p[0] for l_ in lp for p in l_]
            per.append((lp, min(xs), max(xs)))
        else:
            per.append(([], 0.0, 0.0))
    widest = max([b - a for _lp, a, b in per] or [0.0])
    return per, widest, 145.0           # 200 px font: capitals about 145 high


# ---------------------------------------------------------------------------
# The sign
# ---------------------------------------------------------------------------
def picture_pixels(path, cols, threshold=128, dark=True):
    """The picture as rows of raised (True) / flat pixels, cols across: (rows, aspect h/w)."""
    from PySide6.QtGui import QImage
    img = QImage(path)
    if img.isNull():
        raise ValueError("couldn't open the picture %s" % path)
    cols = max(8, int(cols))
    rows = max(1, int(round(cols * img.height() / float(max(1, img.width())))))
    small = img.scaled(cols, rows)
    out = []
    for y in range(rows):
        row = []
        for x in range(cols):
            c = small.pixelColor(x, y)
            grey = 0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()
            if c.alpha() < 128:
                row.append(False)
            else:
                row.append((grey < threshold) if dark else (grey >= threshold))
        out.append(row)
    return out, img.height() / float(max(1, img.width()))


def picture_solids(px, box_, z0, z1):
    """Raised blocks for the picture's raised pixels, fitted (aspect kept) and centred in box_:
    each run of raised pixels along a row is one block. Returns (solids, (x0, x1, y0, y1) used)."""
    rows = len(px)
    cols = len(px[0]) if rows else 0
    if not rows or not cols:
        return [], None
    bx0, bx1, by0, by1 = box_
    cell = min((bx1 - bx0) / cols, (by1 - by0) / rows)
    w, h = cell * cols, cell * rows
    x0 = (bx0 + bx1) / 2 - w / 2
    ytop = (by0 + by1) / 2 + h / 2
    out = []
    for r, row in enumerate(px):
        c = 0
        while c < cols:
            if row[c]:
                c1 = c
                while c1 < cols and row[c1]:
                    c1 += 1
                out.append(box(x0 + c * cell, x0 + c1 * cell, ytop - (r + 1) * cell, ytop - r * cell, z0, z1))
                c = c1
            else:
                c += 1
    return [so for so in out if so], (x0, x0 + w, ytop - h, ytop)


def fit_text(per, widest, line_h, region, want):
    """The scale for the words to fill region (x0, x1, y0, y1), or to be want mm tall."""
    n = len(per)
    rw, rh = region[1] - region[0], region[3] - region[2]
    if want > 0:
        s = want / line_h
    else:
        s = 0.62 * rh / (n + 0.35 * (n - 1)) / line_h
    if rw <= 0 or rh <= 0:
        return 1e-9
    if widest * s > rw:
        s = rw / widest
    return max(1e-9, s)


def text_solids(per, s, line_h, region, z0, z1):
    n = len(per)
    lh = line_h * s
    gap = 0.35 * lh
    total = n * lh + (n - 1) * gap
    cx = (region[0] + region[1]) / 2
    ytop = (region[2] + region[3]) / 2 + total / 2
    tol = max(0.5, 0.02 * lh)      # curves in steps of 2% of the letter: still smooth in print, far fewer faces
    out = []
    for k, (lp, a, b) in enumerate(per):
        if not lp:
            continue
        ybase = ytop - (k + 1) * lh - k * gap          # this line's base (capitals sit on it)
        mx = (a + b) / 2
        for outer, holes in group_loops(lp):
            o = thin([(cx + (p[0] - mx) * s, ybase + p[1] * s) for p in outer], tol)
            hs = [thin([(cx + (p[0] - mx) * s, ybase + p[1] * s) for p in h], tol) for h in holes]
            so = prism(o, hs, z0, z1)
            if so:
                out.append(so)
    return out


def totem_outline(W, H, bar, inset=0.0, n=28):
    """A railway totem: a bar right across a circle. W long, H across the circle, the bar bar% of H
    tall; inset brings it all in (for the inside of the border)."""
    R = H / 2.0 - inset
    hb = H * bar / 200.0 - inset
    xe = W / 2.0 - inset
    cy = H / 2.0
    if R <= 0 or hb <= 0 or xe <= 0 or hb >= R:
        return None
    xi = math.sqrt(R * R - hb * hb)
    a0 = math.asin(hb / R)
    pts = [(xe, cy - hb), (xe, cy + hb), (xi, cy + hb)]
    for k in range(1, n):
        a = a0 + (math.pi - 2 * a0) * k / n
        pts.append((R * math.cos(a), cy + R * math.sin(a)))
    pts += [(-xi, cy + hb), (-xe, cy + hb), (-xe, cy - hb), (-xi, cy - hb)]
    for k in range(1, n):
        a = math.pi + a0 + (math.pi - 2 * a0) * k / n
        pts.append((R * math.cos(a), cy + R * math.sin(a)))
    pts.append((xi, cy - hb))
    return pts


def _stadium(xe, y0, y1, n=14):
    """A bar from -xe to xe, y0 to y1, with round ends (anticlockwise)."""
    r = (y1 - y0) / 2.0
    cy = (y0 + y1) / 2.0
    if r <= 0 or xe <= r:
        return None
    pts = []
    for k in range(n + 1):
        a = -math.pi / 2 + math.pi * k / n
        pts.append((xe - r + r * math.cos(a), cy + r * math.sin(a)))
    for k in range(n + 1):
        a = math.pi / 2 + math.pi * k / n
        pts.append((-xe + r + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _hump(wb, wt, y0, y1, rc=0.0, n=16):
    """A hump standing on y0: wb half-wide at the foot, flat on top (wt half-wide) at y1, its sides a
    rounded curve (a quarter ellipse) from the foot up to the top. Right foot first, anticlockwise,
    ending at the left foot."""
    rx = max(1e-6, wb - wt)
    ry = y1 - y0
    out = []
    for k in range(n + 1):
        a = (math.pi / 2) * k / n
        out.append((wt + rx * math.cos(a), y0 + ry * math.sin(a)))
    return out + [(-x, y) for x, y in reversed(out)]


def station_shape(W, H, bar, hump_w):
    """A railway totem in three panels: a bar with round ends, and a hump on its top and bottom.
    Returns the outline and the three inner panels (bar, top, bottom) for a border B wide; the
    border runs round the edge and between the panels, like a BR totem."""
    cy = H / 2.0
    hb = H * bar / 200.0                                 # half the bar
    hh = H / 2.0 - hb                                    # a hump's height
    xe = W / 2.0
    wb = W * hump_w / 200.0                              # half a hump's foot
    wt = wb - hh * 1.1                                   # half its flat top: the sides curve in
    rc = hh * 0.45                                       # its top corners
    if hb <= 0 or hh <= 0 or wb >= xe - hb or wt <= 0:
        return None
    bar_pts = _stadium(xe, cy - hb, cy + hb)
    n = len(bar_pts) // 2
    right, left = bar_pts[:n], bar_pts[n:]
    top = _hump(wb, wt, cy + hb, H, rc)
    bot = [(-x, 2 * cy - y) for x, y in _hump(wb, wt, cy + hb, H, rc)]
    return right + top + left + bot, (hb, hh, wb, wt, rc)


def station_panels(W, H, bar, hump_w, B):
    """The three panels inside a border B wide (bar, top hump, bottom hump), or None."""
    sh = station_shape(W, H, bar, hump_w)
    if sh is None or B <= 0:
        return None
    hb, hh, wb, wt, rc = sh[1]
    cy = H / 2.0
    pb = _stadium(W / 2.0 - B, cy - hb + B, cy + hb - B)
    t_y1 = H - B
    if pb is None or t_y1 - (cy + hb) < B or wt - B <= B:
        return None
    pt = _hump(wb - B * 1.1, wt - B, cy + hb, t_y1, max(rc - B, rc * 0.4))
    pbt = [(-x, 2 * cy - y) for x, y in pt]
    return pb, pt, pbt


def station_parts(v):
    """A railway totem: three panels, each with its own words - with three lines of words the first
    goes small on the top hump, the middle big on the bar and the last small on the bottom hump.
    Two lines: the first on the top hump."""
    lines = lines_of(v['text']) if v['lettering'] == 'raised' else []
    H = max(20.0, v['height'])
    T = max(2.0, v['thick'])
    B = max(0.0, v['border'])
    M = max(0.0, v['margin'])
    bar = max(30.0, min(80.0, v.get('totem_bar', 50.0) if v.get('totem_bar', 50.0) > 40.0 else 50.0))
    hump_w = 66.0
    top = bot = None
    main = lines
    if len(lines) >= 3:
        top, main, bot = lines[0], lines[1:-1], lines[-1]
    elif len(lines) == 2:
        top, main = lines[0], lines[1:]
    cy = H / 2.0
    hb = H * bar / 200.0
    hh = H / 2.0 - hb
    per, widest, line_h = text_size(main, v['font'], v['bold']) if main else ([], 0.0, 145.0)
    s = fit_text(per, widest, line_h, (0.0, 1e9, 0.0, 2 * hb - 2 * B - M * 0.2), v['letter_h']) if main else 0.0
    W = v['width']
    if W <= 0:
        W = max((widest * s if main else 0.0) + 2 * hb + 2 * B + 2 * M, H * 2.7)
    sh = station_shape(W, H, bar, hump_w)
    if sh is None:
        raise ValueError("the sign is too short for its height - make it longer")
    ol = sh[0]
    hb, hh, wb, wt, rc = sh[1]
    z0 = v['stand_off'] if v['mount'] == 'wall' else -T / 2
    zf = z0 + T
    parts = {'Sign board': [prism(ol, [], z0, zf)]}
    panels = station_panels(W, H, bar, hump_w, B)
    if panels is not None and v['border_out'] > 0:
        parts['Sign lettering - border'] = [prism(ol, list(panels), zf - 0.5, zf + v['border_out'])]
    letters = []
    if main:
        r = hb - B
        reg = (-W / 2 + B + r * 0.7 + M * 0.5, W / 2 - B - r * 0.7 - M * 0.5,
               cy - hb + B + M * 0.1, cy + hb - B - M * 0.1)
        s = fit_text(per, widest, line_h, reg, v['letter_h'])
        letters += text_solids(per, s, line_h, reg, zf - 0.5, zf + v['letter_out'])
    # the small words: the same size top and bottom, inside each hump's panel
    ty0, ty1 = cy + hb, H - B
    pad = (ty1 - ty0) * 0.12
    hx = (wt - B) * 0.9
    smalls = []
    for txt, flip in ((top, False), (bot, True)):
        if txt and ty1 - ty0 > 1.0:
            p2, w2, lh2 = text_size([txt], v['font'], v['bold'])
            smalls.append((p2, w2, lh2, flip))
    if smalls:
        s2 = min(fit_text(p2, w2, lh2, (-hx, hx, ty0 + pad, ty1 - pad), 0.0) for p2, w2, lh2, f in smalls)
        for p2, w2, lh2, flip in smalls:
            y0, y1 = (ty0 + pad, ty1 - pad) if not flip else (2 * cy - ty1 + pad, 2 * cy - ty0 - pad)
            reg = (-hx, hx, y0, y1)
            letters += text_solids(p2, s2, lh2, reg, zf - 0.5, zf + v['letter_out'])
    if letters:
        parts['Sign lettering'] = letters
    if v['mount'] == 'posts':
        pw = max(20.0, v['post_w'])
        ph = max(0.0, v['posts_h'])
        px = W / 2 - max(pw, W * 0.12)
        parts['Posts'] = [box(cx - pw / 2, cx + pw / 2, -ph, H * 0.5, z0 - pw, z0) for cx in (-px, px)]
    rep = {'width': W, 'height': H, 'lines': len(lines), 'letter_h': line_h * s if main else 0.0,
           'lamps': 0, 'picture': 0}
    return {k: [so for so in sol if so] for k, sol in parts.items() if sol}, rep


def sign_parts(v):
    """{group name: [solids]} in mm (x along, y up from the board's foot, z out from the wall), and a
    report."""
    if v.get('shape') == 'station':
        return station_parts(v)
    lines = lines_of(v['text']) if v['lettering'] == 'raised' else []
    H = max(20.0, v['height'])
    T = max(2.0, v['thick'])
    B = max(0.0, v['border'])
    M = max(0.0, v['margin'])
    pic = None
    if (v.get('picture') or "").strip():
        pic, aspect = picture_pixels(v['picture'].strip(), v.get('pic_res', 80), v.get('pic_threshold', 128),
                                     v.get('pic_dark', True))
    pos = v.get('pic_pos', 'above')
    if pic is not None and pos == 'fill':
        lines = []
    per, widest, line_h = ([], 0.0, 145.0)
    if lines:
        per, widest, line_h = text_size(lines, v['font'], v['bold'])
    inner_h = H - 2 * B - M * 0.5                       # inside the border, a little space top and bottom
    # how much room the picture takes (up and down for 'above', along for 'left')
    pic_h = pic_w = 0.0
    if pic is not None:
        if pos == 'above':
            pic_h = v.get('pic_h', 0.0) or (inner_h * 0.55 if lines else inner_h)
            pic_h = min(pic_h, inner_h)
            pic_w = pic_h / aspect
        elif pos == 'left':
            pic_h = min(v.get('pic_h', 0.0) or inner_h, inner_h)
            pic_w = pic_h / aspect
        else:
            pic_h = inner_h
            pic_w = pic_h / aspect
    text_h = inner_h - (pic_h + M * 0.25 if pos == 'above' and pic is not None else 0.0)
    s = fit_text(per, widest, line_h, (0.0, 1e9, 0.0, text_h), v['letter_h']) if lines else 0.0
    totem = v.get('shape') == 'totem'
    if totem:                                            # the words go on the bar
        hb = H * max(10.0, min(90.0, v.get('totem_bar', 40.0))) / 100.0
        text_h = hb - 2 * B - M * 0.2
        pic = None
        if lines:
            s = fit_text(per, widest, line_h, (0.0, 1e9, 0.0, text_h), v['letter_h'])
    W = v['width']
    if W <= 0:                                           # as long as the words (and picture) need
        tw = widest * s if lines else 0.0
        if pic is not None and pos == 'left':
            W = pic_w + (M + tw if lines else 0.0) + 2 * B + 2 * M
        else:
            W = max(tw, pic_w if pic is not None else 0.0) + 2 * B + 2 * M
        if W <= 2 * B + 2 * M + 1.0:
            W = 2000.0
        if totem:
            W = max(W, H * 1.4)
    x0, x1 = -W / 2, W / 2
    ix0, ix1 = x0 + B + M, x1 - B - M                    # inside the border, less the end space
    iy0, iy1 = B + M * 0.25, H - B - M * 0.25
    z0 = v['stand_off'] if v['mount'] == 'wall' else -T / 2
    zf = z0 + T
    parts = {}
    if totem:
        ol = totem_outline(W, H, max(10.0, min(90.0, v.get('totem_bar', 40.0))))
        if ol is None:
            raise ValueError("the totem's bar must be narrower than its circle")
        parts['Sign board'] = [prism(ol, [], z0, zf)]
        il = totem_outline(W, H, max(10.0, min(90.0, v.get('totem_bar', 40.0))), B) if B > 0 else None
        if il is not None and v['border_out'] > 0:
            parts['Sign lettering - border'] = [prism(ol, [il], zf - 0.5, zf + v['border_out'])]
        hb = H * max(10.0, min(90.0, v.get('totem_bar', 40.0))) / 200.0
        ix0, ix1 = x0 + B + M, x1 - B - M
        iy0, iy1 = H / 2 - hb + B + M * 0.1, H / 2 + hb - B - M * 0.1
    elif True:
        parts['Sign board'] = [box(x0, x1, 0.0, H, z0, zf)]
    if not totem and B > 0 and v['border_out'] > 0 and x1 - x0 > 2 * B and H > 2 * B:
        outer = [(x0, 0.0), (x1, 0.0), (x1, H), (x0, H)]
        hole = [(x0 + B, B), (x1 - B, B), (x1 - B, H - B), (x0 + B, H - B)]
        parts['Sign lettering - border'] = [prism(outer, [hole], zf - 0.5, zf + v['border_out'])]
    text_region = (ix0, ix1, iy0, iy1)
    if totem:
        pass
    pic_n = 0
    if pic is not None:
        if pos == 'above':
            pbox = (ix0, ix1, iy1 - pic_h, iy1)
            text_region = (ix0, ix1, iy0, iy1 - pic_h - M * 0.25)
        elif pos == 'left':
            if lines:
                pic_w = min(pic_w, 0.5 * (ix1 - ix0))       # room left for the words
            pbox = (ix0, min(ix1, ix0 + pic_w), iy0, iy1)
            text_region = (min(ix1, ix0 + pic_w + M), ix1, iy0, iy1)
        else:
            pbox = (ix0, ix1, iy0, iy1)
        sols, _used = picture_solids(pic, pbox, zf - 0.5, zf + max(0.5, v.get('pic_out', v['letter_out'])))
        if sols:
            parts['Sign lettering - picture'] = sols
            pic_n = len(sols)
    if lines:
        s = fit_text(per, widest, line_h, text_region, v['letter_h'])
        letters = text_solids(per, s, line_h, text_region, zf - 0.5, zf + v['letter_out'])
        if letters:
            parts['Sign lettering'] = letters
    nl = int(v['lamps'])
    if nl > 0:
        inset = max(v['lamp_dia'], W * 0.06)
        for k in range(nl):
            cx = 0.0 if nl == 1 else x0 + inset + (W - 2 * inset) * k / (nl - 1)
            parts['Lamp %d' % (k + 1)] = [lamp_solids(cx, H - 1.0, (z0 + zf) / 2, v)]
    if v['mount'] == 'posts':
        pw = max(20.0, v['post_w'])
        ph = max(0.0, v['posts_h'])
        px = W / 2 - max(pw, W * 0.08)
        parts['Posts'] = [box(cx - pw / 2, cx + pw / 2, -ph, H + pw * 0.3, z0 - pw, z0) for cx in (-px, px)]
    rep = {'width': W, 'height': H, 'lines': len(lines),
           'letter_h': line_h * s if lines else 0.0, 'lamps': nl, 'picture': pic_n}
    return {k: [so for so in sol if so] for k, sol in parts.items() if sol}, rep


def frame_for(polys, v):
    """(origin, along, up, out, foot) in world metres for the sign: on a wall face, on a flat face
    (posts), or at the origin."""
    up = (0.0, 0.0, 1.0)
    if not polys:
        return (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), up, (0.0, -1.0, 0.0), 0.0
    pts = polys[0]
    n = _newell(pts)
    if v.get('flip'):
        n = v_mul(n, -1.0)
    zs = [p[2] for p in pts]
    if abs(n[2]) > 0.7:                                   # a flat face: the sign stands on it
        best = max(range(len(pts)), key=lambda i: v_len(v_sub(pts[(i + 1) % len(pts)], pts[i])))
        e = v_sub(pts[(best + 1) % len(pts)], pts[best])
        along = v_norm((e[0], e[1], 0.0))
        out = v_cross(along, up)
        c = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts), max(zs))
        return c, along, up, out, c[2]
    out = v_norm((n[0], n[1], 0.0))
    along = v_cross(up, out)                              # reads left to right, seen from the front
    us = [v_dot(p, along) for p in pts]
    ws = [v_dot(p, out) for p in pts]
    uc = (min(us) + max(us)) / 2
    w = sum(ws) / len(ws)
    c = v_add(v_mul(along, uc), v_mul(out, w))
    return (c[0], c[1], 0.0), along, up, out, min(zs), max(zs)


def place(parts, frame, y_base):
    """The parts in world metres: x along, y up from y_base (world z), z out."""
    O, along, up, out = frame[0], frame[1], frame[2], frame[3]
    S = SCALE

    def P(p):
        return (O[0] + along[0] * p[0] * S + out[0] * p[2] * S,
                O[1] + along[1] * p[0] * S + out[1] * p[2] * S,
                y_base + p[1] * S)
    res = {}
    for nm, sols in parts.items():
        res[nm] = [[([P(p) for p in outer], [[P(p) for p in h] for h in hs]) for outer, hs in so] for so in sols]
    return res


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
    keep = {k: val for k, val in values.items()
            if not k.startswith('_') and isinstance(val, (bool, int, float, str, type(None)))}
    _ui_settings_save(last=keep)


def last_used():
    d = _ui_settings().get('last')
    return d if isinstance(d, dict) else {}


def load_presets():
    out = list(PRESETS)
    try:
        for fn in sorted(os.listdir(PRESETS_DIR)):
            if fn.lower().endswith(".json"):
                with open(os.path.join(PRESETS_DIR, fn), "r", encoding="utf-8") as f:
                    out.append((fn[:-5], json.load(f)))
    except Exception:
        pass
    return out


def save_preset(name, values):
    os.makedirs(PRESETS_DIR, exist_ok=True)
    safe = "".join(ch for ch in name if ch not in '\\/:*?"<>|').strip() or "My sign"
    with open(os.path.join(PRESETS_DIR, safe + ".json"), "w", encoding="utf-8") as f:
        json.dump(values, f, indent=1)
    return safe


def _narrow(cb, n):
    try:
        cb.setMinimumContentsLength(n)
        enum = getattr(QComboBox, 'AdjustToMinimumContentsLengthWithIcon', None)
        if enum is None:
            enum = QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        cb.setSizeAdjustPolicy(enum)
    except Exception:
        pass


def _form(page):
    fl = QFormLayout(page)
    for name, pol, grp in (('setRowWrapPolicy', 'WrapLongRows', 'RowWrapPolicy'),
                           ('setFieldGrowthPolicy', 'AllNonFixedFieldsGrow', 'FieldGrowthPolicy')):
        try:
            enum = getattr(QFormLayout, pol, None)
            if enum is None:
                enum = getattr(getattr(QFormLayout, grp), pol)
            getattr(fl, name)(enum)
        except Exception:
            pass
    return fl



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

EDDY_TIPS = {}


# ---------------------------------------------------------------------------
# The window - laid out like the other 3D plugins: preview and key on the left, the settings
# pages on the right, presets and Build along the bottom
# ---------------------------------------------------------------------------
MAKES = [("wall", "Sign on a wall"), ("posts", "Sign on two posts")]

# (tab, key, label, low, high, decimals, suffix, tip)
FIELDS = [
    ("Board", 'width', "A   Width (0 = fit the words)", 0.0, 50000.0, 0, " mm",
     "How long the board is. 0 makes it just long enough for the words (and picture)."),
    ("Board", 'height', "B   Height", 20.0, 20000.0, 0, " mm", "How tall the board is."),
    ("Board", 'thick', "C   Thickness", 2.0, 500.0, 0, " mm", "How thick the board is."),
    ("Board", 'stand_off', "D   Stands off the wall", 0.0, 1000.0, 0, " mm", "On a wall: the gap behind the board."),
    ("Board", 'up', "E   Up from the bottom (0 = middle)", 0.0, 50000.0, 0, " mm",
     "On a wall: how far up the face the bottom of the board is. 0 puts it in the middle, up and down."),
    ("Board", 'totem_bar', "Totem / roundel: bar height", 10.0, 90.0, 0, " %",
     "How tall the bar is, as a part of the whole height: on a totem the rest is the humps (about 50%); "
     "on a roundel, the circle (about 40%)."),
    ("Board", 'border', "F   Border width", 0.0, 1000.0, 0, " mm", "The raised border round the edge. 0 = none."),
    ("Board", 'border_out', "G   Border stands out", 0.0, 100.0, 0, " mm", "How far the border stands out."),
    ("Words", 'letter_h', "H   Letter height (0 = fit)", 0.0, 5000.0, 0, " mm",
     "How tall the capitals are. 0 makes them fill the space."),
    ("Words", 'letter_out', "J   Letters stand out", 0.5, 100.0, 1, " mm", "How far the letters stand out."),
    ("Words", 'margin', "K   Space round the words", 0.0, 5000.0, 0, " mm",
     "Between the words (and picture) and the border."),
    ("Picture", 'pic_h', "L   Picture height (0 = fit)", 0.0, 50000.0, 0, " mm",
     "How tall the picture is. 0 makes it fit: over half the board above the words, or all of it."),
    ("Picture", 'pic_res', "Detail (dots across)", 8, 400, None, "",
     "How many dots across the picture is made of. More = finer, but many more faces (80 is a good start)."),
    ("Picture", 'pic_threshold', "Dark below", 1, 254, None, "",
     "How dark a dot must be to stand out (0 black - 255 white). Lower it for less, raise it for more."),
    ("Picture", 'pic_out', "M   Picture stands out", 0.5, 100.0, 1, " mm", "How far the picture stands out."),
    ("Lamps", 'lamps', "Lamps along the top", 0, 30, None, "", "How many lamps stand along the top. 0 = none."),
    ("Lamps", 'lamp_h', "N   Lamp height", 50.0, 3000.0, 0, " mm", "From the cap to the top of the lamp."),
    ("Lamps", 'lamp_dia', "P   Lamp width", 30.0, 2000.0, 0, " mm", "Across the widest part of the lamp."),
    ("Lamps", 'stem', "Q   Stem", 0.0, 3000.0, 0, " mm", "The stem between the board and the lamp."),
    ("Posts", 'posts_h', "R   Board up from the ground", 0.0, 10000.0, 0, " mm",
     "On posts: how high the bottom of the board is above the face it stands on."),
    ("Posts", 'post_w', "S   Post size", 20.0, 1000.0, 0, " mm", "How thick each post is."),
]


class SignPreview(QWidget):
    """A front view of the sign as it will be built."""

    def __init__(self):
        super().__init__()
        self.v = dict(DEFAULTS)
        self.setMinimumSize(380, 300)
        self._pic_key = None
        self._pic = None

    def set_values(self, v):
        self.v = dict(v)
        self.update()

    def _pixels(self, v):
        key = (v.get('picture'), int(v.get('pic_res', 80)), int(v.get('pic_threshold', 128)), bool(v.get('pic_dark', True)))
        if key != self._pic_key:
            self._pic_key = key
            self._pic = None
            if (v.get('picture') or "").strip():
                try:
                    self._pic = picture_pixels(v['picture'].strip(), key[1], key[2], key[3])
                except Exception:
                    self._pic = None
        return self._pic

    def paintEvent(self, _e):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont
        from PySide6.QtCore import QRectF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(236, 236, 232))
        v = self.v
        try:
            parts, rep = sign_parts(dict(v, picture="") if self._pixels(v) is None else v)
        except Exception as e:
            p.drawText(10, 20, "(%s)" % e)
            return
        # everything seen from the front: x along, y up
        xs, ys = [], []
        for sols in parts.values():
            for so in sols:
                for outer, _h in so:
                    for q in outer:
                        xs.append(q[0])
                        ys.append(q[1])
        if not xs:
            return
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        m = 14
        sc = min((self.width() - 2 * m) / max(1.0, x1 - x0), (self.height() - 2 * m - 18) / max(1.0, y1 - y0))
        ox = self.width() / 2 - (x0 + x1) / 2 * sc
        oy = self.height() / 2 + (y0 + y1) / 2 * sc + 9

        def X(x):
            return ox + x * sc

        def Y(y):
            return oy - y * sc
        cols = {'Sign board': QColor(110, 36, 52), 'Posts': QColor(140, 102, 66)}
        order = ['Posts', 'Sign board'] + [k for k in parts if k not in ('Posts', 'Sign board')]
        p.setPen(QPen(QColor(40, 20, 20), 0.6))
        for nm in order:
            if nm not in parts:
                continue
            col = cols.get(nm, QColor(196, 156, 64) if nm.startswith('Lamp') else QColor(240, 236, 224))
            p.setBrush(col)
            for so in parts[nm]:
                # draw the front-most face of each solid (its outline, seen from the front)
                best = max(so, key=lambda f: sum(q[2] for q in f[0]) / len(f[0]))
                if nm.startswith('Lamp'):
                    lx = [q[0] for f in so for q in f[0]]
                    ly = [q[1] for f in so for q in f[0]]
                    p.drawEllipse(QRectF(X(min(lx)), Y(max(ly)), (max(lx) - min(lx)) * sc,
                                         (max(ly) - min(ly)) * sc))
                    continue
                from PySide6.QtGui import QPolygonF
                from PySide6.QtCore import QPointF
                outer, holes = best
                if holes:
                    from PySide6.QtGui import QPainterPath
                    path = QPainterPath()
                    path.addPolygon(QPolygonF([QPointF(X(q[0]), Y(q[1])) for q in outer]))
                    path.closeSubpath()
                    for h in holes:
                        path.addPolygon(QPolygonF([QPointF(X(q[0]), Y(q[1])) for q in h]))
                        path.closeSubpath()
                    p.drawPath(path)
                else:
                    p.drawPolygon(QPolygonF([QPointF(X(q[0]), Y(q[1])) for q in outer]))
        p.setPen(QColor(60, 60, 60))
        f = QFont()
        f.setPointSize(8)
        p.setFont(f)
        p.drawText(8, self.height() - 6, "%.0f x %.0f mm" % (rep['width'], rep['height']) +
                   ("  -  letters %.0f mm" % rep['letter_h'] if rep['lines'] else ""))


class SignKey(QWidget):
    """What each lettered size is."""

    def __init__(self):
        super().__init__()
        self.setMinimumSize(380, 300)

    def paintEvent(self, _e):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont
        from PySide6.QtCore import QRectF, QPointF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 247))
        W, H = self.width(), self.height()
        bx0, bx1, by0, by1 = W * 0.14, W * 0.86, H * 0.42, H * 0.70
        p.setPen(QPen(QColor(40, 20, 20), 1))
        p.setBrush(QColor(110, 36, 52))
        p.drawRect(QRectF(bx0, by0, bx1 - bx0, by1 - by0))
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(240, 236, 224), 3))
        p.drawRect(QRectF(bx0 + 5, by0 + 5, bx1 - bx0 - 10, by1 - by0 - 10))
        f = QFont()
        f.setBold(True)
        f.setPointSize(13)
        p.setFont(f)
        p.drawText(QRectF(bx0, by0, bx1 - bx0, by1 - by0), Qt.AlignCenter, "STATION")
        p.setPen(QPen(QColor(120, 90, 30), 1))
        p.setBrush(QColor(214, 178, 84))
        for x in (bx0 + 30, (bx0 + bx1) / 2, bx1 - 30):
            p.drawLine(QPointF(x, by0), QPointF(x, by0 - 14))
            p.drawEllipse(QRectF(x - 9, by0 - 40, 18, 26))
        p.setPen(QPen(QColor(30, 60, 160), 1))
        f.setPointSize(9)
        p.setFont(f)

        def dim(a, b, txt, at):
            p.drawLine(a, b)
            p.drawText(at, txt)
        dim(QPointF(bx0, by1 + 18), QPointF(bx1, by1 + 18), "A", QPointF((bx0 + bx1) / 2 - 4, by1 + 32))
        dim(QPointF(bx1 + 14, by0), QPointF(bx1 + 14, by1), "B", QPointF(bx1 + 20, (by0 + by1) / 2 + 4))
        p.drawText(QPointF(bx0 + 2, by1 - 8), "F")
        p.drawText(QPointF((bx0 + bx1) / 2 + 52, (by0 + by1) / 2 + 4), "H")
        p.drawText(QPointF(bx0 + 20, by0 - 44), "N, P")
        p.drawText(QPointF(bx0 + 40, by0 - 4), "Q")
        notes = ["C  thickness,  D  gap behind it,  E  how far up the wall",
                 "G, J, M  how far the border, letters and picture stand out",
                 "K  space round the words,  L  picture height",
                 "R  posts: board up from the ground,  S  post size"]
        p.setPen(QColor(50, 50, 50))
        f.setBold(False)
        p.setFont(f)
        for i, t in enumerate(notes):
            p.drawText(QPointF(12, H * 0.80 + i * 15), t)


class SignDialog(QDialog):
    def __init__(self, viewport, tool, cur):
        super().__init__(viewport)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self._pic = ""
        lay = QVBoxLayout(self)
        self.info_box = QLabel("Select a wall face (or a flat face, for a sign on posts), then Build. Sizes are "
                               "real-world mm: Scale Studio takes it down to your model scale. The letters by the "
                               "sizes are on the Key page.")
        self.info_box.setWordWrap(True)
        self.info_box.setVisible(False)
        lay.addWidget(self.info_box)
        self.lbl_report = QLabel()
        self.lbl_report.setWordWrap(True)
        lay.addWidget(self.lbl_report)
        top = QFormLayout()
        self.cb_kind = QComboBox()
        for k, t in MAKES:
            self.cb_kind.addItem(t, k)
        _narrow(self.cb_kind, 14)
        self.cb_kind.setToolTip("On a wall: the board on the wall face you pick, standing off it. On two posts: a "
                                "running-in board standing on the face you pick (the platform).")
        top.addRow("Make", self.cb_kind)
        lay.addLayout(top)

        self.preview = SignPreview()
        self.preview.setToolTip("A front view of what will be built. It changes as you change the settings.")
        self.views = QTabWidget()
        self.views.addTab(self.preview, "3D view")
        self.views.addTab(SignKey(), "Key (A, B, C...)")
        row = QHBoxLayout()
        lay.addLayout(row)
        row.addWidget(self.views, 1)
        self.tabs = QTabWidget()
        pages = {}
        for title in ("Board", "Words", "Picture", "Lamps", "Posts"):
            pg = QWidget()
            pages[title] = _form(pg)
            self.tabs.addTab(pg, title)
        for tw_ in (self.views, self.tabs):
            tw_.setUsesScrollButtons(False)
            tw_.setElideMode(Qt.TextElideMode.ElideNone)
            tw_.tabBar().setExpanding(False)
        row.addWidget(self.tabs, 1)
        # the words: typed or pasted, a line for each line
        pages["Words"].addRow(QLabel("The words (type or paste - Ctrl+V - a new line for each line):"))
        self.ed_text = QPlainTextEdit()
        self.ed_text.setFixedHeight(80)
        pages["Words"].addRow(self.ed_text)
        self.cb_letters = QComboBox()
        for k, t in LETTERING:
            self.cb_letters.addItem(t, k)
        pages["Words"].addRow("Lettering", self.cb_letters)
        self.cb_font = QComboBox()
        for k, t in FONTS:
            self.cb_font.addItem(t, k)
        pages["Words"].addRow("Font", self.cb_font)
        self.ck_bold = QCheckBox("Bold")
        pages["Words"].addRow(self.ck_bold)
        # the picture
        prow = QHBoxLayout()
        b_pic = QPushButton("Picture...")
        b_pic.setToolTip("A black and white picture on the board (any photo or drawing - it's made black and "
                         "white). Its dark parts stand out.")
        b_nopic = QPushButton("No picture")
        self.lbl_pic = QLabel("(none)")
        self.lbl_pic.setWordWrap(True)
        prow.addWidget(b_pic)
        prow.addWidget(b_nopic)
        pages["Picture"].addRow(prow)
        pages["Picture"].addRow(self.lbl_pic)
        self.cb_picpos = QComboBox()
        for k, t in PIC_POS:
            self.cb_picpos.addItem(t, k)
        pages["Picture"].addRow("Picture goes", self.cb_picpos)
        self.ck_dark = QCheckBox("Dark parts stand out (untick: light parts do)")
        pages["Picture"].addRow(self.ck_dark)
        b_pic.clicked.connect(self._pick_pic)
        b_nopic.clicked.connect(lambda: (self._set_pic(""), self.redraw()))
        self.w = {}
        for tab, key, label, lo, hi, dec, suf, tip in FIELDS:
            if dec is None:
                sp = QSpinBox()
                sp.setRange(int(lo), int(hi))
            else:
                sp = QDoubleSpinBox()
                sp.setDecimals(dec)
                sp.setRange(lo, hi)
                sp.setSuffix(suf)
            sp.setKeyboardTracking(False)
            sp.setToolTip(tip)
            lab = QLabel(label)
            lab.setToolTip(tip)
            pages[tab].addRow(lab, sp)
            self.w[key] = sp
        self.cb_shape = QComboBox()
        for k, t in SHAPES:
            self.cb_shape.addItem(t, k)
        self.cb_shape.setToolTip("A plain board; a railway totem - a bar with round ends and a hump top and "
                                 "bottom, small words on the humps; or a roundel - a bar right across a circle.")
        pages["Board"].insertRow(0, "Shape", self.cb_shape)
        self.ck_flip = QCheckBox("Turn it round (it faced into the wall)")
        pages["Board"].addRow(self.ck_flip)

        prow = QHBoxLayout()
        prow.addWidget(QLabel("Preset:"))
        self.cb_preset = QComboBox()
        _narrow(self.cb_preset, 14)
        self.cb_preset.setToolTip("Ready-made signs. Pick one and the window is filled in; your own presets are "
                                  "in the list too.")
        prow.addWidget(self.cb_preset, 1)
        b_up = QPushButton("▲")
        b_dn = QPushButton("▼")
        for b_ in (b_up, b_dn):
            b_.setFixedWidth(28)
            prow.addWidget(b_)
        b_up.clicked.connect(lambda: self.move_preset(-1))
        b_dn.clicked.connect(lambda: self.move_preset(1))
        b_save = QPushButton("Save")
        self.btn_preset_save = b_save
        b_saveas = QPushButton("Save as...")
        b_del = QPushButton("Delete")
        b_dir = QPushButton("Folder")
        for b_ in (b_save, b_saveas, b_del, b_dir):
            prow.addWidget(b_)
        lay.addLayout(prow)
        brow = QHBoxLayout()
        b_go = QPushButton("Add sign to selected face")
        b_go.setDefault(True)
        b_go.setToolTip("Builds the sign on the selected face (or at the origin if nothing is selected): one "
                        "group, with the board, border, letters, picture, each lamp and the posts as pieces "
                        "of their own.")
        b_close = QPushButton("Close")
        self.cb_lasttab = QCheckBox("Open at the last page used")
        brow.addWidget(b_go)
        brow.addStretch(1)
        self.b_info = QPushButton("Info")
        self.b_info.setCheckable(True)
        self.b_info.toggled.connect(self.toggle_info)
        brow.addWidget(self.b_info)
        brow.addWidget(self.cb_lasttab)
        brow.addWidget(b_close)
        lay.addLayout(brow)
        b_saveas.clicked.connect(self.save_as)
        b_del.clicked.connect(self.delete_preset)
        b_dir.clicked.connect(self.open_folder)
        b_save.clicked.connect(self.save_preset)
        b_go.clicked.connect(lambda: self.tool.build(self))
        b_close.clicked.connect(self.close)
        self.set_values(cur)
        self.fill_presets()
        for sp in self.w.values():
            sp.valueChanged.connect(self.redraw)
        for cb in (self.cb_kind, self.cb_letters, self.cb_font, self.cb_picpos, self.cb_shape):
            cb.currentIndexChanged.connect(self.changed)
        for ck in (self.ck_bold, self.ck_dark, self.ck_flip):
            ck.toggled.connect(self.changed)
        self._text_timer = QTimer(self)
        self._text_timer.setSingleShot(True)
        self._text_timer.timeout.connect(self.redraw)
        self.ed_text.textChanged.connect(lambda: self._text_timer.start(500))
        try:
            self.cb_preset.activated.connect(self.preset_picked)
        except Exception:
            self.cb_preset.currentIndexChanged.connect(self.preset_picked)
        self.changed()
        st = _ui_settings()
        self.cb_lasttab.setChecked(bool(st.get('remember_tab', True)))
        if self.cb_lasttab.isChecked():
            try:
                i_ = int(st.get('tab', -1))
                if i_ >= 0:
                    self.tabs.setCurrentIndex(i_)
            except Exception:
                pass
        self.tabs.currentChanged.connect(lambda i: _ui_settings_save(tab=int(i)))
        self.cb_lasttab.toggled.connect(lambda on: _ui_settings_save(remember_tab=bool(on)))

    def toggle_info(self, on):
        self.info_box.setVisible(bool(on))
        try:
            self.adjustSize()
        except Exception:
            pass

    def changed(self, *_):
        posts = self.cb_kind.currentData() == 'posts'
        self.tabs.setTabEnabled(4, posts)
        for k in ('stand_off', 'up'):
            self.w[k].setEnabled(not posts)
        self.w['totem_bar'].setEnabled(self.cb_shape.currentData() in ('totem', 'station'))
        raised = self.cb_letters.currentData() == 'raised'
        for wdg in (self.cb_font, self.ck_bold, self.w['letter_h'], self.w['letter_out']):
            wdg.setEnabled(raised)
        self.redraw()

    def redraw(self, *_):
        try:
            self.preview.set_values(self.values())
        except Exception:
            pass

    def _set_pic(self, path):
        self._pic = path or ""
        self.lbl_pic.setText(os.path.basename(self._pic) if self._pic else "(none)")

    def _pick_pic(self):
        from PySide6.QtWidgets import QFileDialog
        start = os.path.dirname(self._pic) if self._pic else os.path.expanduser("~")
        path, _f = QFileDialog.getOpenFileName(self, "A picture for the sign", start,
                                               "Pictures (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;All files (*)")
        if path:
            self._set_pic(path)
            self.redraw()

    def _own_file(self, name):
        """The file of one of your own presets, or None for a built-in one."""
        if not name or name in dict(PRESETS):
            return None
        fn = os.path.join(PRESETS_DIR, name + ".json")
        return fn if os.path.exists(fn) else None

    def save_preset(self, *_):
        """Save: updates the preset you have open, with no typing. A built-in one (or none
        picked) asks for a name instead."""
        name = self.cb_preset.currentData()
        if self._own_file(name):
            save_preset(name, self.values())
            self._presets = dict(load_presets())
            try:
                from PySide6.QtCore import QTimer
                self.btn_preset_save.setText("Saved")
                QTimer.singleShot(1500, lambda: self.btn_preset_save.setText("Save"))
            except Exception:
                pass
        else:
            self.save_as()

    def delete_preset(self, *_):
        name = self.cb_preset.currentData()
        fn = self._own_file(name)
        if not fn:
            QMessageBox.information(self, PLUGIN_NAME, "Pick one of your own presets to delete "
                                    "(built-in presets can't be deleted).")
            return
        if QMessageBox.question(self, PLUGIN_NAME, "Delete preset '%s'?" % name) != QMessageBox.Yes:
            return
        try:
            os.remove(fn)
        except Exception as e:
            QMessageBox.warning(self, PLUGIN_NAME, "Could not delete it:\n%s" % e)
            return
        self.fill_presets()

    def open_folder(self, *_):
        try:
            os.makedirs(PRESETS_DIR, exist_ok=True)
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(PRESETS_DIR))
        except Exception as e:
            QMessageBox.information(self, PLUGIN_NAME, "Presets folder:\n%s\n\n(%s)" % (PRESETS_DIR, e))

    def preset_order(self):
        """Every preset's name, in the order you've put them (new ones go at the bottom)."""
        names = []
        for name, _vals in load_presets():
            if name not in names:
                names.append(name)
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
        self.fill_presets()
        for k in range(self.cb_preset.count()):
            if self.cb_preset.itemData(k) == name:
                self.cb_preset.blockSignals(True)
                self.cb_preset.setCurrentIndex(k)
                self.cb_preset.blockSignals(False)

    def fill_presets(self):
        self.cb_preset.clear()
        self.cb_preset.addItem("(pick a preset)", None)
        for name in self.preset_order():
            self.cb_preset.addItem(name, name)
        self._presets = dict(load_presets())

    def preset_picked(self, *_):
        name = self.cb_preset.currentData()
        if not name:
            return
        vals = dict(self.values())
        vals.update(self._presets.get(name, {}))
        self.set_values(vals)
        self.changed()
        self.redraw()

    def save_as(self, *_):
        try:
            from PySide6.QtWidgets import QInputDialog
            name, ok = QInputDialog.getText(self, PLUGIN_NAME, "Name for this preset:")
        except Exception:
            return
        if not ok or not str(name).strip():
            return
        safe = save_preset(str(name), self.values())
        self.fill_presets()
        for i in range(self.cb_preset.count()):
            if self.cb_preset.itemData(i) == safe:
                self.cb_preset.setCurrentIndex(i)

    def set_values(self, cur):
        self.ed_text.blockSignals(True)
        self.ed_text.setPlainText(str(cur.get('text', "")))
        self.ed_text.blockSignals(False)
        for cb, key in ((self.cb_kind, 'mount'), (self.cb_letters, 'lettering'), (self.cb_font, 'font'),
                        (self.cb_shape, 'shape'),
                        (self.cb_picpos, 'pic_pos')):
            for i in range(cb.count()):
                if cb.itemData(i) == cur.get(key):
                    cb.setCurrentIndex(i)
        self.ck_bold.setChecked(bool(cur.get('bold', True)))
        self.ck_flip.setChecked(bool(cur.get('flip', False)))
        self.ck_dark.setChecked(bool(cur.get('pic_dark', True)))
        if 'picture' in cur:
            self._set_pic(cur.get('picture', ""))
        for k, sp in self.w.items():
            if k in cur:
                sp.blockSignals(True)
                sp.setValue(int(cur[k]) if isinstance(sp, QSpinBox) else float(cur[k]))
                sp.blockSignals(False)

    def values(self):
        v = dict(DEFAULTS)
        v.update({k: (int(sp.value()) if isinstance(sp, QSpinBox) else float(sp.value()))
                  for k, sp in self.w.items()})
        v.update(text=self.ed_text.toPlainText(), mount=self.cb_kind.currentData(),
                 lettering=self.cb_letters.currentData(), font=self.cb_font.currentData(),
                 bold=self.ck_bold.isChecked(), flip=self.ck_flip.isChecked(),
                 picture=self._pic, pic_pos=self.cb_picpos.currentData(), pic_dark=self.ck_dark.isChecked(),
                 shape=self.cb_shape.currentData())
        return v


class VertexWrapper(QVector3D):
    def __init__(self, x, y, z):
        super().__init__(float(x), float(y), float(z))


class SignsTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+Shift+N"
    description = ("Station name boards, running-in boards on posts, enamel signs and plain boards, with "
                   "raised lettering, a border and lamps.")
    _dialog = None

    def on_activate(self, viewport):
        dlg = SignsTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.raise_()
                    dlg.activateWindow()
                    return
            except Exception:
                pass
        dlg = SignDialog(viewport, self, dict(DEFAULTS, **last_used()))
        SignsTool._dialog = dlg

        def closed(*_):
            try:
                remember_last(dlg.values())
            except Exception:
                pass
            SignsTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)
        dlg.show()

    def on_deactivate(self, viewport):
        pass

    def build(self, dlg):
        v = dlg.values()
        remember_last(v)
        scene = getattr(dlg.viewport, 'scene', None)
        polys = selected_faces(scene) if scene is not None else []
        try:
            parts, rep = sign_parts(v)
        except Exception as e:
            QMessageBox.warning(dlg, PLUGIN_NAME, "Couldn't make the sign: %s" % e)
            return
        fr = frame_for(polys, v)
        if not polys:
            base = 0.0
            where = "at the origin (nothing was selected)"
        elif len(fr) == 5:                                # a flat face: on posts if asked, else lying on it
            base = fr[4] + (v['posts_h'] * SCALE if v['mount'] == 'posts' else 0.0)
            where = "on the face you picked"
        else:
            bot, top = fr[4], fr[5]
            if v['mount'] == 'posts':
                base = bot + v['posts_h'] * SCALE
            elif v['up'] > 0:
                base = bot + v['up'] * SCALE
            else:
                base = (bot + top) / 2 - rep['height'] * SCALE / 2
            where = "on the wall"
        parts = place(parts, fr, base)
        txt = " ".join(lines_of(v['text']))
        name = "Sign - %s" % (txt[:40] if txt else "plain board")
        nf = self.add_to_scene(dlg.viewport, name, parts)
        if nf is None:
            return
        msg = "Built a %.0f x %.0f mm board %s" % (rep['width'], rep['height'], where)
        if rep['lines']:
            msg += ", %d line%s of letters %.0f mm tall" % (rep['lines'], "" if rep['lines'] == 1 else "s",
                                                           rep['letter_h'])
        if rep['lamps']:
            msg += ", %d lamps" % rep['lamps']
        if rep.get('picture'):
            msg += ", a picture"
        dlg.lbl_report.setStyleSheet("color: #2e7d32;")
        dlg.lbl_report.setText(msg + ". %d faces." % nf)

    def add_to_scene(self, viewport, name, parts):
        stats = {'faces': 0, 'errors': 0, 'err': None}
        tol = 1e-4 * 0.001

        def mesh_of(solids):
            from core.mesh import Mesh
            mesh = Mesh()
            verts = {}

            def vx(p):
                k = (round(p[0] / tol), round(p[1] / tol), round(p[2] / tol))
                if k not in verts:
                    verts[k] = VertexWrapper(*p)
                return verts[k]
            for so in solids:
                for outer, holes in so:
                    try:
                        if holes:
                            hs = [[vx(p) for p in h] for h in holes]
                            try:
                                mesh.add_face([vx(p) for p in outer], hs)
                            except TypeError:
                                f_ = mesh.add_face([vx(p) for p in outer])
                                for h in hs:
                                    mesh.add_hole(f_, h)
                        else:
                            mesh.add_face([vx(p) for p in outer])
                        stats['faces'] += 1
                    except Exception as e:
                        stats['errors'] += 1
                        stats['err'] = e
            return mesh

        def make_group(Group, mesh, nm):
            try:
                g = Group(mesh, name=nm)
            except TypeError:
                g = Group(nm)
                g.mesh = mesh
            try:
                g.name = nm
            except Exception:
                pass
            g.component = False
            return g

        def mutate(scene):
            from core.group import Group
            kids = [make_group(Group, mesh_of(sol), nm) for nm, sol in parts.items() if sol]
            if stats['faces'] == 0:
                raise RuntimeError("No faces could be made (%s)." % stats['err'])
            top = None
            try:
                top = Group(name=name)
                if hasattr(top, 'adopt'):
                    top.adopt(kids)
                else:
                    top.children = kids
                top.component = False
            except Exception:
                top = None
            for g in ([top] if top is not None else kids):
                _ed3d_organise(scene, g)
                scene.groups.append(g)
        try:
            viewport.history.execute(SnapshotImport(mutate))
        except Exception as e:
            QMessageBox.warning(viewport, PLUGIN_NAME, "Could not add it:\n%s" % e)
            return None
        try:
            viewport.notify_scene_changed()
        except Exception:
            pass
        return stats['faces']


def run(viewport=None):
    SignsTool().on_activate(viewport)
