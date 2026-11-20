# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Card Kit for IngeTrazo
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
3D Card Kit - turns a model into a printed card kit, for IngeTrazo
Select a building (or some walls), and each piece is drawn flat, at true scale, in its colours,
ready to print on an ordinary paper printer, stick on card, cut out and build:

  * Every piece is drawn as seen from the outside, with its bricks, windows and doors in
    the colours they have in the model (or a material you pick for it on the Parts page).
  * Glue tabs go along the edges where pieces meet, each one saying which piece it glues to
    ("glue to 3"). Solid lines are cut, dashed lines are folded.
  * Window glass can be left white to cut out (clear film goes behind), or printed.
  * The pieces are laid out on A4, A3, A5 or Letter sheets; a piece too big for the paper is
    split across sheets. The first sheet has the instructions and the list of parts.
  * Every sheet has a 50 mm check bar: print at 100 % ("Actual size"), never "Fit to page".

It makes a PDF, so anyone can print it. Pieces are worked out like Scale Studio's Pieces
page: one per group (or groups a few levels in), and groups joined in Show / Hide's Groups tab
print as one piece. Ctrl+Alt+Shift+K opens it.
"""

import os
import json
import math

PLUGIN_NAME = "3D Card Kit"
VERSION = "2.6"   # 2.6: the piece numbers go on a glue tab, not on the wall itself, so they don\'t show on the finished model; 2.5: a material picked for a brick wall goes on the bricks (it was going on the bare wall behind them); 2.4: a roof slope comes out as one clean shape (no slot or notch where the chimney goes through - the chimney sits on it); every piece has its main colour under its faces, so no gaps show through; 2.3: the choice of program comes up as a proper box in the middle of the Card Kit window, with big buttons; 2.2: Open PDF with... (and Ask me each time) shows a short list - Edge, Chrome, the usual program, or show it in its folder - as Windows' own Open with box did nothing; 2.1: "Open in" sits next to Make card kit; Open PDF with... works straight after making it (or makes it first); 2.0: bricks back (only parts set back behind the wall's own face are left out, like the frame behind a window); choose which program opens the PDF; 1.11: what's seen through a window with no glass (parts set back at the back of the wall) is left out, and the openings get the glass look you pick; 1.10: window glass is drawn whichever way its face points (some panes were missing, showing the frame behind as green); joint lines on dark colours (slates) are drawn lighter so they show; 1.9: the piece choices set by accident with the mouse wheel are cleared once; roof slates and tiles (and cladding) are printed on the roof piece under them, as one piece; 1.8: scrolling the Parts list with the mouse wheel no longer changes a drop-down it passes over; 1.7: click a piece in the preview to pick it in the Parts list (it's outlined in blue); narrower colour boxes, wider names; "&" shows in the page names; 1.6: glass never hidden behind the frame colour (faces only grouped when they can't cover each other); glass: cut out, plain white, the model's glass colour or pale blue; 1.5: switches to Sharp once, as 1.2 had saved "picture" as your setting; 1.4: leaves out Subframe's frame (studs, plates, trusses, glazing frames) but keeps the fascia, barge and soffit boards; 1.3: sharp shapes in the PDF, joined up by colour, so it prints crisp and still opens quickly; 1.2: piece names cut short to fit under small pieces; 1.1: the faces go into the PDF as a picture (opens fast in LibreOffice and the like); cut and fold lines stay sharp

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_card_kit.json")
PRESET_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Card Kit")
KIT_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Card Kits")

ONE_PIECE = "one piece"
PRINT_PIECE_KEY = "ed3d_print_piece"          # set by 3D Show / Hide: groups joined into one piece

SCALES = [("OO  1:76.2", 76.2), ("HO  1:87", 87.1), ("TT  1:120", 120.0), ("N (UK)  1:148", 148.0),
          ("N  1:160", 160.0), ("Z  1:220", 220.0), ("S  1:64", 64.0), ("O (UK)  1:43.5", 43.5),
          ("O (Europe)  1:45", 45.0), ("G  1:22.5", 22.5), ("1:24", 24.0), ("1:32", 32.0),
          ("1:100", 100.0), ("Already at print size (1:1)", 1.0)]
PAPERS = [("A4", (210.0, 297.0)), ("A3", (297.0, 420.0)), ("A5", (148.0, 210.0)),
          ("Letter", (215.9, 279.4))]
ORIENTS = [("Best fit", 'best'), ("Portrait (upright)", 'portrait'), ("Landscape (sideways)", 'landscape')]
PDF_MODES = [("Sharp - shapes joined up by colour (best)", 'sharp'),
             ("As a picture (if a PDF program still struggles)", 'picture')]
OPEN_WITH = [("Ask me each time", 'ask'), ("Microsoft Edge", 'edge'), ("Google Chrome", 'chrome'),
             ("The usual program for PDFs", 'default'), ("Don't open it", 'none')]
PICK_FROM = [("Microsoft Edge", 'edge'), ("Google Chrome", 'chrome'), ("The usual program for PDFs", 'default'),
             ("Show it in its folder", 'folder')]
DPIS = [("200 dpi (small file)", 200), ("300 dpi (sharp)", 300), ("600 dpi (very sharp, big file)", 600)]
WINDOW_MODES = [("Cut out - white with a cut line (clear film behind)", 'cut'),
                ("Plain - white, nothing to cut", 'plain'),
                ("Coloured - the glass colour from the model", 'model'),
                ("Coloured - pale blue", 'print')]
TAB_MODES = [("Where it joins", 'auto'), ("None", 'none'), ("All round", 'all')]
SIDE_MODES = [("Outside", 'front'), ("Other side", 'back')]
DEPTHS = [("Each group with faces is a piece", 0), ("Groups 1 level in", 1),
          ("Groups 2 levels in", 2), ("Groups 3 levels in", 3)]

DEFAULTS = dict(scale=76.2, paper="A4", orient='best', margin=10.0, gap=4.0, tab_w=6.0,
                bottom_tabs=True, windows='cut', lines=True, shading=True, numbers=True,
                instructions=True, depth=0, line_w=0.25, kit_name="", pdf_mode='sharp', dpi=300)

BUILTIN_PRESETS = {
    "OO card kit on A4": dict(scale=76.2, paper="A4", orient='best', margin=10.0, gap=4.0, tab_w=6.0,
                              bottom_tabs=True, windows='cut', lines=True, shading=True, line_w=0.25),
    "N card kit on A4": dict(scale=148.0, paper="A4", orient='best', margin=10.0, gap=3.0, tab_w=4.0,
                             bottom_tabs=True, windows='print', lines=True, shading=True, line_w=0.18),
    "O card kit on A3": dict(scale=43.5, paper="A3", orient='best', margin=10.0, gap=5.0, tab_w=8.0,
                             bottom_tabs=True, windows='cut', lines=True, shading=True, line_w=0.3),
}

DEFAULT_FACE = (0.86, 0.86, 0.84)          # a face with no colour of its own
GLASS_PRINT = (0.80, 0.88, 0.93)
TAB_FILL = (0.90, 0.90, 0.90)
HEADER_H = 13.0                            # mm at the top of each sheet for the title and check bar
LABEL_H = 5.0                              # mm under each piece for its number and name
TILE_OVERLAP = 0.0


# ---------------------------------------------------------------------------
# Small sums (no Qt in them, so they can be checked on their own)
# ---------------------------------------------------------------------------
def v_sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def v_add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def v_mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def v_dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def v_len(a): return math.sqrt(v_dot(a, a))


def v_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def v_unit(a):
    L = v_len(a)
    return v_mul(a, 1.0 / L) if L > 1e-15 else None


def newell(loop):
    nx = ny = nz = 0.0
    for i in range(len(loop)):
        a, b = loop[i], loop[(i + 1) % len(loop)]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    return (nx, ny, nz)


def area2(poly):
    """Signed area of a flat loop (x, y): plus when it goes round anticlockwise (y up)."""
    s = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def pip(p, poly):
    """Is point p inside the loop?"""
    x, y = p
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            xc = xi + (y - yi) * (xj - xi) / ((yj - yi) or 1e-30)
            if x < xc:
                inside = not inside
        j = i
    return inside


def inside_outline(p, loops):
    """Inside the piece: inside an odd number of its loops (outlines and holes)."""
    return sum(1 for lp in loops if pip(p, lp)) % 2 == 1


def bounds2(loops):
    xs = [p[0] for lp in loops for p in lp]
    ys = [p[1] for lp in loops for p in lp]
    if not xs:
        return (0.0, 0.0, 0.0, 0.0)
    return (min(xs), min(ys), max(xs), max(ys))


def clean_loop(loop, eps=1e-6):
    out = []
    for p in loop:
        if not out or abs(p[0] - out[-1][0]) > eps or abs(p[1] - out[-1][1]) > eps:
            out.append((float(p[0]), float(p[1])))
    while len(out) > 1 and abs(out[0][0] - out[-1][0]) <= eps and abs(out[0][1] - out[-1][1]) <= eps:
        out.pop()
    return out


def classify_loops(loops):
    """[(loop, is_hole)]: a loop inside an odd number of the others is a hole."""
    out = []
    for i, lp in enumerate(loops):
        # a point just inside this loop, to test against the others
        p = lp[0]
        depth = sum(1 for j, other in enumerate(loops) if j != i and pip(p, other))
        out.append((lp, depth % 2 == 1))
    return out


def merged_edges(loop, angle_deg=4.0, eps=1e-6):
    """The loop's straight runs: [(a, b)], consecutive segments in (nearly) the same direction joined.
    The loop must already go anticlockwise (y up)."""
    pts = clean_loop(loop, eps)
    n = len(pts)
    if n < 3:
        return []
    cos_lim = math.cos(math.radians(angle_deg))

    def d(i):
        a, b = pts[i % n], pts[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        return ((b[0] - a[0]) / L, (b[1] - a[1]) / L) if L > eps else None

    def corner(i):                      # does the direction change at point i?
        a, b = d(i - 1), d(i)
        if a is None or b is None:
            return False
        return a[0] * b[0] + a[1] * b[1] < cos_lim
    starts = [i for i in range(n) if corner(i)]
    if not starts:
        return []
    edges = []
    for k, s in enumerate(starts):
        e = starts[(k + 1) % len(starts)]
        a, b = pts[s], pts[e]
        if math.hypot(b[0] - a[0], b[1] - a[1]) > eps:
            edges.append((a, b))
    return edges


# ---------------------------------------------------------------------------
# Reading the model (the same rules as Scale Studio's Pieces page)
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


def _is_face(e):
    return hasattr(e, 'loop') or 'face' in type(e).__name__.lower()


def _pos(v):
    for get in (lambda: (v.x(), v.y(), v.z()),
                lambda: (v.x, v.y, v.z),
                lambda: (v[0], v[1], v[2]),
                lambda: (v.pos.x(), v.pos.y(), v.pos.z()),
                lambda: (v.position.x(), v.position.y(), v.position.z())):
        try:
            x, y, z = get()
            return (float(x), float(y), float(z))
        except Exception:
            pass
    return None


def _print_tag(g):
    ext = getattr(g, 'ext', None)
    if isinstance(ext, dict):
        t = ext.get(PRINT_PIECE_KEY)
        if isinstance(t, str) and t.strip():
            return t.strip()
    return ""


def _one_piece(g):
    nm = " ".join(str(getattr(g, 'name', '') or '').lower().replace("-", " ").replace("_", " ").split())
    return ONE_PIECE in nm


def _kids(g):
    return [c for c in _items(getattr(g, 'children', None)) + _items(getattr(g, 'groups', None))
            if not _is_face(c)]


def _placements(top):
    """(group, world matrix or None) for a group and every group inside it."""
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


def _hidden(g):
    for a in ('hidden', 'is_hidden', '_hidden'):
        v = getattr(g, a, None)
        if isinstance(v, bool) and v:
            return True
    return False


# 3D Subframe's groups: the frame inside the building, which a card kit doesn't need - all but the
# boards on the outside (fascia, barge boards, soffits and their finials), which it does
FRAME_GROUPS = ("subframe", "glazing frame", "roof truss", "roof trusses")
OUTSIDE_WORDS = ("fascia", "barge", "soffit", "finial")


def _low(g):
    return " ".join(str(getattr(g, 'name', '') or '').lower().split())


def _frame_group(g):
    return _low(g).startswith(FRAME_GROUPS)


def _outside_board(g):
    nm = _low(g)
    return any(w in nm for w in OUTSIDE_WORDS)


def _piece_groups(e, depth, skip_frame=False):
    """[(group, [(group, matrix)])]: the groups under e that each make one piece. With skip_frame,
    Subframe's frame is left out but its outside boards are kept."""
    place = {}
    for g, m in _placements(e):
        place.setdefault(id(g), m)
    out = []

    def faces_of(g):
        return _items(getattr(getattr(g, 'mesh', None), 'faces', None))

    def subtree(g, acc, lvl=0):
        if not _hidden(g):
            acc.append((g, place.get(id(g), getattr(g, 'xform', None))))
            if lvl < 12:
                for c in _kids(g):
                    subtree(c, acc, lvl + 1)
        return acc

    def walk(g, lvl, in_frame=False):
        if _hidden(g):
            return
        if skip_frame:
            if _outside_board(g):
                in_frame = False            # a board: kept, whatever it sits in
            elif in_frame or _frame_group(g):
                if lvl < 12:                # part of the frame: only look inside it for boards
                    for c in _kids(g):
                        walk(c, lvl + 1, True)
                return
        if (depth and lvl >= depth) or _one_piece(g) or _print_tag(g):
            out.append((g, subtree(g, [])))
            return
        if faces_of(g):
            out.append((g, [(g, place.get(id(g), getattr(g, 'xform', None)))]))
        if lvl < 12:
            for c in _kids(g):
                walk(c, lvl + 1)
    walk(e, 0)
    return out


def _mapper(m):
    if m is None:
        return lambda p: p
    try:
        from PySide6.QtGui import QVector3D

        def f(p):
            q = m.map(QVector3D(p[0], p[1], p[2]))
            return (q.x(), q.y(), q.z())
        return f
    except Exception:
        return lambda p: p


def _face_loops(f, mp):
    outer = [_pos(v) for v in _items(getattr(f, 'vertices', None))]
    if len(outer) < 3 or any(q is None for q in outer):
        return None
    holes = []
    for h in _items(getattr(f, 'holes', None)):
        hl = [_pos(v) for v in _items(h)]
        if len(hl) >= 3 and all(q is not None for q in hl):
            holes.append([mp(q) for q in hl])
    return [mp(q) for q in outer], holes


def _attrs_of(f, group):
    a = {}
    gm = getattr(group, 'material', None)
    if isinstance(gm, dict):
        a.update(gm)
    fa = getattr(f, 'attrs', None)
    if isinstance(fa, dict):
        a.update(fa)
    return a


def read_pieces(entities, depth=0, skip_frame=True):
    """The selection as pieces: [{'name', 'faces': [face record]}], a face record being
    {'outer', 'holes', 'attrs', 'face', 'mesh'} in world metres."""
    pieces, names, tags = [], {}, {}
    loose = []

    def recs(members):
        out = []
        for h, m in members:
            mesh = getattr(h, 'mesh', None)
            mp = _mapper(m)
            for f in _items(getattr(mesh, 'faces', None)):
                lp = _face_loops(f, mp)
                if lp:
                    out.append({'outer': lp[0], 'holes': lp[1], 'attrs': _attrs_of(f, h),
                                'face': f, 'mesh': mesh})
        return out
    for e in entities:
        if _is_face(e):
            loose.append(e)
            continue
        for g, members in _piece_groups(e, depth, skip_frame):
            fr = recs(members)
            if not fr:
                continue
            tag = _print_tag(g)
            if tag:
                if tag in tags:
                    tags[tag]['faces'] += fr
                else:
                    tags[tag] = {'name': tag, 'faces': fr}
                    pieces.append(tags[tag])
                continue
            nm = str(getattr(g, 'name', '') or "Part")
            names[nm] = names.get(nm, 0) + 1
            pieces.append({'name': nm if names[nm] == 1 else "%s (%d)" % (nm, names[nm]), 'faces': fr})
    if loose:
        fr = []
        for f in loose:
            lp = _face_loops(f, lambda p: p)
            if lp:
                fr.append({'outer': lp[0], 'holes': lp[1], 'attrs': dict(getattr(f, 'attrs', None) or {}),
                           'face': f, 'mesh': None})
        if fr:
            pieces.append({'name': "Selected faces", 'faces': fr})
    return pieces


COVER_WORDS = ("slate", "tile", "pantile", "shingle", "sheet", "corrugated", "plank", "cladding",
               "weatherboard", "board")


def join_coverings(pieces, gap=0.03):
    """Slates or tiles laid on a roof slope (and cladding on a wall) come from their own plugin as
    a piece of their own. On card they belong on the piece under them: each covering is joined
    onto the piece it lies flat on (same way round, touching or within gap metres, and over it)."""
    info = []
    for pc in pieces:
        n = main_direction(pc['faces'])
        u, v = view_axes(n)
        pts = [p for fr in pc['faces'] for p in fr['outer']]
        ds = [v_dot(p, n) for p in pts]
        xs = [v_dot(p, u) for p in pts]
        ys = [v_dot(p, v) for p in pts]
        info.append({'n': n, 'u': u, 'v': v, 'd': (min(ds), max(ds)),
                     'box': (min(xs), min(ys), max(xs), max(ys))})
    target = {}
    for i, pc in enumerate(pieces):
        nm = pc['name'].lower()
        if not any(w in nm for w in COVER_WORDS) or any(w in nm for w in OUTSIDE_WORDS):
            continue
        a = info[i]
        best = None
        for j, other in enumerate(pieces):
            if j == i:
                continue
            b = info[j]
            if abs(v_dot(a['n'], b['n'])) < 0.98:
                continue
            # depths along the shared direction: they must touch or nearly
            n = b['n']
            da = [v_dot(p, n) for fr in pc['faces'] for p in fr['outer']]
            if min(da) > b['d'][1] + gap or max(da) < b['d'][0] - gap:
                continue
            # the covering must lie over the other piece
            xs = [v_dot(p, b['u']) for fr in pc['faces'] for p in fr['outer']]
            ys = [v_dot(p, b['v']) for fr in pc['faces'] for p in fr['outer']]
            cx0, cy0, cx1, cy1 = min(xs), min(ys), max(xs), max(ys)
            bx0, by0, bx1, by1 = b['box']
            ox = max(0.0, min(cx1, bx1) - max(cx0, bx0))
            oy = max(0.0, min(cy1, by1) - max(cy0, by0))
            cover = (cx1 - cx0) * (cy1 - cy0)
            if cover <= 0 or ox * oy < 0.5 * cover:
                continue
            if any(w in other['name'].lower() for w in COVER_WORDS) and not any(
                    w in other['name'].lower() for w in OUTSIDE_WORDS):
                continue                       # not onto another covering
            score = ox * oy
            if best is None or score > best[0]:
                best = (score, j)
        if best is not None:
            target[i] = best[1]
    if not target:
        return pieces
    out = []
    for j, pc in enumerate(pieces):
        if j in target:
            continue
        joined = [pieces[i] for i, t in target.items() if t == j]
        if joined:
            pc = {'name': pc['name'] + " (with " + ", ".join(
                p['name'].split(" - ")[0].split("(")[0].strip() for p in joined) + ")",
                  'faces': pc['faces'] + [fr for p in joined for fr in p['faces']]}
        out.append(pc)
    return out


# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
def _mat_get(materials, name):
    if not name or materials is None:
        return None
    try:
        return materials.get(name)
    except Exception:
        try:
            return materials[name]
        except Exception:
            return None


def _rgb(c):
    try:
        c = tuple(float(x) for x in c)[:3]
        if len(c) == 3:
            if max(c) > 1.0:
                c = tuple(x / 255.0 for x in c)
            return tuple(min(1.0, max(0.0, x)) for x in c)
    except Exception:
        pass
    return None


def texture_info(t):
    """(image path, tile width m, tile height m) from a texture setting, or None."""
    if isinstance(t, dict):
        p = t.get('path')
        if p and os.path.isfile(str(p)):
            return (str(p), float(t.get('sw') or 1.0), float(t.get('sh') or 1.0))
        return None
    if isinstance(t, str) and os.path.isfile(t):
        return (t, 1.0, 1.0)
    p = getattr(t, 'path', None)
    if p and os.path.isfile(str(p)):
        return (str(p), float(getattr(t, 'sw', 1.0) or 1.0), float(getattr(t, 'sh', 1.0) or 1.0))
    return None


def material_look(mat):
    """(colour, opacity, texture) of one of the document's materials."""
    rgb = _rgb(getattr(mat, 'color', None)) or DEFAULT_FACE
    op = getattr(mat, 'opacity', 1.0)
    try:
        op = float(op)
    except Exception:
        op = 1.0
    return rgb, op, texture_info(getattr(mat, 'texture', None))


def face_look(attrs, materials):
    """(colour, is_glass, texture, material name) for a face."""
    name = attrs.get('mat') or ""
    mat = _mat_get(materials, name)
    rgb = _rgb(attrs.get('color')) if attrs.get('color') is not None else None
    tex = texture_info(attrs.get('texture'))
    op = attrs.get('opacity')
    if mat is not None:
        m_rgb, m_op, m_tex = material_look(mat)
        rgb = rgb or m_rgb
        if op is None:
            op = m_op
        tex = tex or m_tex
    if rgb is None:
        rgb = (0.78, 0.74, 0.68) if tex else DEFAULT_FACE
    try:
        op = 1.0 if op is None else float(op)
    except Exception:
        op = 1.0
    low = name.lower()
    glass = op < 0.9 or "glass" in low or "glaz" in low
    return rgb, glass, tex, name


def colour_key(rgb):
    return tuple(int(round(c * 255)) for c in rgb)


# ---------------------------------------------------------------------------
# A piece seen flat: which way it faces, its faces drawn in 2D, its outline and its edges
# ---------------------------------------------------------------------------
def main_direction(faces):
    """The direction most of a piece's area faces (either way), as a unit vector."""
    acc = {}
    for fr in faces:
        nv = newell(fr['outer'])
        A = v_len(nv) / 2.0
        n = v_unit(nv)
        if n is None or A <= 0:
            continue
        # one key for both ways
        s = 1.0
        for c in n:
            if abs(c) > 1e-3:
                s = 1.0 if c > 0 else -1.0
                break
        n = v_mul(n, s)
        k = tuple(int(round(c * 20)) for c in n)
        t = acc.setdefault(k, [0.0, (0.0, 0.0, 0.0)])
        t[0] += A
        t[1] = v_add(t[1], v_mul(n, A))
    if not acc:
        return (0.0, -1.0, 0.0)
    best = max(acc.values(), key=lambda t: t[0])
    return v_unit(best[1]) or (0.0, -1.0, 0.0)


def view_axes(n):
    """(u right, v up) on the paper, looking at the side n points out of."""
    up = (0.0, 0.0, 1.0)
    v = v_sub(up, v_mul(n, v_dot(up, n)))
    if v_len(v) < 0.15:                           # a flat piece (floor, flat roof): north is up
        y = (0.0, 1.0, 0.0)
        v = v_sub(y, v_mul(n, v_dot(y, n)))
    v = v_unit(v) or (0.0, 0.0, 1.0)
    u = v_unit(v_cross(v, n)) or (1.0, 0.0, 0.0)
    return u, v


def world_bounds(faces):
    pts = [p for fr in faces for p in fr['outer']]
    lo = tuple(min(p[k] for p in pts) for k in range(3))
    hi = tuple(max(p[k] for p in pts) for k in range(3))
    return lo, hi


def outward_sign(faces, n, centre):
    """+1 if n points out of the building (away from centre), -1 if in; by face count when
    the piece is in the middle (an inside wall)."""
    lo, hi = world_bounds(faces)
    mid = v_mul(v_add(lo, hi), 0.5)
    size = max(hi[k] - lo[k] for k in range(3)) or 1.0
    off = v_dot(v_sub(mid, centre), n) if centre is not None else 0.0
    if abs(off) > 0.05 * size:
        return 1.0 if off > 0 else -1.0
    front = back = 0
    for fr in faces:
        nf = v_unit(newell(fr['outer']))
        if nf is None:
            continue
        d = v_dot(nf, n)
        if d > 0.5:
            front += 1
        elif d < -0.5:
            back += 1
    return 1.0 if front >= back else -1.0


def flatten_piece(raw, centre, flip=False, materials=None, outline_fn=None):
    """Lays a piece out flat in real-size mm (y up), seen from the outside (or the other side
    with flip). Returns a dict with its faces in 2D, its outline loops, its edges and how to
    get from the paper back to the model (for finding where pieces meet)."""
    faces = raw['faces']
    n = main_direction(faces)
    if abs(n[2]) > 0.9:                            # lying flat (base, floor): seen from above
        s = 1.0 if n[2] > 0 else -1.0
    else:
        s = outward_sign(faces, n, centre)
    if flip:
        s = -s
    n = v_mul(n, s)
    u, v = view_axes(n)
    K = 1000.0                                     # model metres to real mm
    draw, front_side, back_side = [], [], []
    depths = []
    for fr in faces:
        nf = v_unit(newell(fr['outer']))
        if nf is None:
            continue
        d = v_dot(nf, n)
        o2 = [(v_dot(p, u) * K, v_dot(p, v) * K) for p in fr['outer']]
        h2 = [[(v_dot(p, u) * K, v_dot(p, v) * K) for p in h] for h in fr['holes']]
        if abs(area2(o2)) < 1e-6:
            continue
        dep = sum(v_dot(p, n) for p in fr['outer']) / len(fr['outer'])
        depths.append(dep)
        if d > 0.3:
            front_side.append((o2, h2))
        elif d < -0.3:
            back_side.append((o2, h2))
        if abs(d) > 0.05:
            rgb, glass, tex, mname = face_look(fr['attrs'], materials)
            # glass counts whichever way its face points: a pane built as a single face can point
            # into the building, and leaving it out showed the frame behind it instead
            if d > 0.05 or (glass and d < -0.3):
                at = fr['attrs'] or {}
                plain = at.get('color') is None and not at.get('mat') and not at.get('texture')
                draw.append({'outer': o2, 'holes': h2, 'depth': dep, 'shade': abs(d), 'rgb': rgb,
                             'glass': glass, 'tex': tex, 'mat': mname, 'rec': fr, 'plain': plain})
    if not draw:
        return None
    # a window built into a wall has no glass (glazing frames go in later), so through its panes
    # you'd see whatever sits at the back of the wall - on card that's no use: anything set back
    # past the middle of the piece is left out, and the openings get the glass look instead
    # The wall's own face is the depth with the most area facing out (bricks and windows stand
    # out in front of it); a part set back behind it - the back of a window frame - can only be
    # seen through an opening, so it's left out.
    if draw:
        by_depth = {}
        for f in draw:
            if f['shade'] > 0.9:
                k = int(round(f['depth'] * 1000.0))          # 1 mm (real) levels
                by_depth[k] = by_depth.get(k, 0.0) + abs(area2(f['outer']))
        if by_depth:
            base = max(by_depth, key=by_depth.get) / 1000.0
            kept = [f for f in draw if f['glass'] or f['depth'] >= base - 0.001]
            if kept and len(kept) < len(draw):
                draw = kept
    # the outline: from whichever side has fewer faces (the plain back of a brick wall)
    side = back_side if back_side and len(back_side) < len(front_side) else (front_side or back_side)
    loops = []
    if outline_fn is not None:
        try:
            loops = outline_fn(side)
        except Exception as e:
            print("%s: outline: %s" % (PLUGIN_NAME, e))
            loops = []
    if not loops:
        loops = simple_outline(side or [(f['outer'], f['holes']) for f in draw])
    loops = [clean_loop(lp) for lp in loops]
    loops = [lp for lp in loops if len(lp) >= 3 and abs(area2(lp)) > 1e-4]
    if not loops:
        return None
    if 0.2 < abs(n[2]) < 0.97:
        # a roof slope: one clean shape round it all. Where a chimney goes through, the roof was
        # cut round it (a slot, a notch) - on card the chimney is cut to fit and sits on top.
        hl = hull2([p for lp in loops for p in lp])
        if len(hl) >= 3:
            loops = [hl]
    x0, y0, x1, y1 = bounds2(loops)
    for f in draw:
        f['outer'] = [(x - x0, y - y0) for x, y in f['outer']]
        f['holes'] = [[(x - x0, y - y0) for x, y in h] for h in f['holes']]
    loops = [[(x - x0, y - y0) for x, y in lp] for lp in loops]
    draw.sort(key=lambda f: f['depth'])            # far ones first, near ones over them
    # the main colour: the one covering most of the piece (what a material picked on the Parts
    # page replaces - the windows and doors keep theirs)
    # faces with no colour of their own (the bare wall behind bricks) only count if nothing else
    # has a colour, or a brick wall's main colour came out as that grey and a picked material
    # went on the wall behind instead of the bricks
    area_by, plain_by = {}, {}
    for f in draw:
        if not f['glass']:
            k = colour_key(f['rgb'])
            tgt = plain_by if f.get('plain') else area_by
            tgt[k] = tgt.get(k, 0.0) + abs(area2(f['outer'])) * f['shade']
    if not area_by:
        area_by = plain_by
    main = max(area_by, key=area_by.get) if area_by else None
    cls = classify_loops(loops)
    outers = []
    for lp, hole in cls:
        if not hole:
            outers.append(lp if area2(lp) > 0 else lp[::-1])
    edges = []
    for lp in outers:
        for a, b in merged_edges(lp):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            o = ((b[1] - a[1]) / L, -(b[0] - a[0]) / L)      # right of the way round = outwards
            m = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
            if inside_outline((m[0] + o[0] * 0.3, m[1] + o[1] * 0.3), loops):
                o = (-o[0], -o[1])
            edges.append({'a': a, 'b': b, 'len': L, 'out': o})
    dmid = sum(depths) / len(depths) if depths else 0.0
    lo, hi = world_bounds(faces)
    ds = [v_dot(p, n) for fr in faces for p in fr['outer']]
    thick = max(max(ds) - min(ds), 1e-9)
    openings = [lp for lp, hole in cls if hole]
    return {'name': raw['name'], 'draw': draw, 'loops': loops, 'edges': edges, 'w': x1 - x0, 'h': y1 - y0,
            'openings': openings,
            'u': u, 'v': v, 'n': n, 'shift': (x0, y0), 'dmid': dmid, 'lo': lo, 'hi': hi,
            'thick': thick, 'main': main, 'raw': raw}


def hull2(pts):
    """The convex outline round some points (x, y), anticlockwise."""
    pts = sorted(set((round(p[0], 6), round(p[1], 6)) for p in pts))
    if len(pts) < 3:
        return pts

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
    return lo[:-1] + hi[:-1]


def simple_outline(side):
    """Without Qt to join the faces up: the biggest face's loops (good for a plain back)."""
    if not side:
        return []
    o, hs = max(side, key=lambda t: abs(area2(t[0])))
    return [o] + list(hs)


def to_world(piece, p):
    """A point on the flat piece (real mm) back in the model (metres), half way through it."""
    x = (p[0] + piece['shift'][0]) / 1000.0
    y = (p[1] + piece['shift'][1]) / 1000.0
    return v_add(v_add(v_mul(piece['u'], x), v_mul(piece['v'], y)), v_mul(piece['n'], piece['dmid']))


def find_joins(pieces):
    """For each edge of each piece: the number of the piece it meets (or None)."""
    for i, pc in enumerate(pieces):
        for e in pc['edges']:
            e['meets'] = None
            m = ((e['a'][0] + e['b'][0]) / 2.0, (e['a'][1] + e['b'][1]) / 2.0)
            # just outside the edge, so it lands in the next piece and not this one
            step = max(pc['thick'] * 1000.0 * 0.5, 0.5)
            q = to_world(pc, (m[0] + e['out'][0] * step, m[1] + e['out'][1] * step))
            tol = max(pc['thick'] * 0.6, 1e-6)
            best = None
            for j, other in enumerate(pieces):
                if j == i:
                    continue
                lo, hi = other['lo'], other['hi']
                if all(lo[k] - tol <= q[k] <= hi[k] + tol for k in range(3)):
                    size = v_len(v_sub(hi, lo))
                    if best is None or size < best[0]:
                        best = (size, j)
            if best is not None:
                e['meets'] = best[1]


def choose_tabs(pieces, modes, bottom_tabs, tab_w, f):
    """Which edges get glue tabs: [(piece index, edge, label)] per piece, as a dict.
    'Where it joins': one tab per join (the piece that finds the other first, or the lower
    number when both do); 'All round': every edge long enough; bottom tabs glue it down."""
    min_len = max(4.0, 1.4 * tab_w)
    out = {i: [] for i in range(len(pieces))}
    for i, pc in enumerate(pieces):
        mode = modes.get(i, 'auto')
        if mode == 'none':
            continue
        ymin = 0.0
        for e in pc['edges']:
            if e['len'] * f < min_len:
                continue
            j = e.get('meets')
            flat = abs(e['b'][1] - e['a'][1]) < 0.1 * e['len']
            bottom = flat and max(e['a'][1], e['b'][1]) <= ymin + 0.5 / max(f, 1e-9) and e['out'][1] < -0.5
            label = None
            if j is not None and modes.get(j, 'auto') != 'skip':
                if mode == 'all':
                    label = "glue to %d" % (j + 1)
                else:
                    other_finds = any(e2.get('meets') == i for e2 in pieces[j]['edges'])
                    if not other_finds or i < j or modes.get(j, 'auto') == 'none':
                        label = "glue to %d" % (j + 1)
            elif bottom and bottom_tabs and abs(pc['n'][2]) < 0.3:
                label = "glue to base"
            elif mode == 'all':
                label = "glue"
            if label:
                out[i].append((e, label))
    return out


def tab_polygon(e, w, f):
    """The tab on an edge (real mm in, real mm out): w is its width on the paper."""
    a, b, o = e['a'], e['b'], e['out']
    L = e['len']
    W = w / f
    ins = min(W, L * 0.25)
    d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    return [a, b, (b[0] + o[0] * W - d[0] * ins, b[1] + o[1] * W - d[1] * ins),
            (a[0] + o[0] * W + d[0] * ins, a[1] + o[1] * W + d[1] * ins)]


def tab_ok(poly, loops, tabs_so_far):
    """A tab may not lie over its own piece (a notch) or another tab."""
    a, b, c, d = poly
    tests = [((c[0] + d[0]) / 2, (c[1] + d[1]) / 2),
             ((a[0] + b[0] + c[0] + d[0]) / 4, (a[1] + b[1] + c[1] + d[1]) / 4), c, d]
    for p in tests:
        if inside_outline(p, loops):
            return False
        for t in tabs_so_far:
            if pip(p, t):
                return False
    return True


# ---------------------------------------------------------------------------
# Laying the kit out on sheets: everything as simple drawing steps in page mm (y down),
# so the same steps draw the PDF and the preview
# ---------------------------------------------------------------------------
def paper_size(paper, orient):
    w, h = dict(PAPERS).get(paper, (210.0, 297.0))
    if orient == 'landscape':
        w, h = h, w
    return w, h


def _shade(rgb, k):
    return tuple(max(0.0, min(1.0, c * k)) for c in rgb)


def kit_items(pieces, opts, choices):
    """Each piece ready to place: its tabs, its size on paper (with tabs and label)."""
    f = 1.0 / float(opts['scale'])
    modes = {i: choices.get(i, {}).get('tabs', 'auto') for i in range(len(pieces))}
    for i in range(len(pieces)):
        if not choices.get(i, {}).get('print', True):
            modes[i] = 'skip'
    picked = choose_tabs(pieces, modes, opts['bottom_tabs'], opts['tab_w'], f)
    items = []
    for i, pc in enumerate(pieces):
        if modes[i] == 'skip':
            continue
        tabs = []
        polys = []
        for e, label in picked[i]:
            poly = tab_polygon(e, opts['tab_w'], f)
            if tab_ok(poly, pc['loops'], polys):
                polys.append(poly)
                tabs.append((e, poly, label))
        allp = [p for lp in pc['loops'] for p in lp] + [p for t in polys for p in t]
        bx0 = min(p[0] for p in allp)
        by0 = min(p[1] for p in allp)
        bx1 = max(p[0] for p in allp)
        by1 = max(p[1] for p in allp)
        items.append({'i': i, 'piece': pc, 'tabs': tabs, 'box': (bx0, by0, bx1, by1),
                      'w': (bx1 - bx0) * f, 'h': (by1 - by0) * f})
    return items


def tile_items(items, aw, ah):
    """Pieces too big for the paper either way round are cut into tiles that fit."""
    out = []
    for it in items:
        w, h = it['w'], it['h'] + LABEL_H
        if (w <= aw and h <= ah) or (h <= aw and w <= ah):
            out.append(dict(it, clip=None, tile=""))
            continue
        # tile it upright: as few tiles as will do
        cols = max(1, int(math.ceil(it['w'] / aw)))
        rows = max(1, int(math.ceil(it['h'] / (ah - LABEL_H))))
        tw, th = it['w'] / cols, it['h'] / rows
        k = 0
        for r in range(rows):
            for c in range(cols):
                letter = chr(ord('a') + k) if k < 26 else str(k + 1)
                k += 1
                # clip box in paper mm from the piece's bottom-left (y up)
                out.append(dict(it, clip=(c * tw, (rows - 1 - r) * th, tw, th), tile=letter,
                                tiles=(rows, cols, r, c), w=tw, h=th))
    return out


def pack(items, aw, ah, gap, allow_turn=True):
    """Shelf packing onto sheets: [(sheet number, item, x, y, turned)] (page mm from the
    printable area's top-left)."""
    def size(it, turn):
        w, h = (it['h'], it['w']) if turn else (it['w'], it['h'])
        return w, h + LABEL_H
    order = sorted(items, key=lambda it: -max(it['w'], it['h']))
    placed = []
    sheets = []                        # each: list of shelves [y, height, x used]
    for it in order:
        opts_ = [False, True] if allow_turn and it.get('clip') is None else [False]
        done = False
        for si, shelves in enumerate(sheets + [None]):
            if shelves is None:
                sheets.append([])
                shelves = sheets[-1]
                si = len(sheets) - 1
            for turn in opts_:
                w, h = size(it, turn)
                if w > aw + 1e-6 or h > ah + 1e-6:
                    continue
                for sh in shelves:
                    if h <= sh[1] + 1e-6 and sh[2] + w <= aw + 1e-6:
                        placed.append((si, it, sh[2], sh[0], turn))
                        sh[2] += w + gap
                        done = True
                        break
                if done:
                    break
                top = (shelves[-1][0] + shelves[-1][1] + gap) if shelves else 0.0
                if top + h <= ah + 1e-6:
                    shelves.append([top, h, w + gap])
                    placed.append((si, it, 0.0, top, turn))
                    done = True
                    break
            if done:
                break
        if not done:                    # can't happen after tiling, but never lose a piece
            sheets.append([[0.0, size(it, False)[1], aw]])
            placed.append((len(sheets) - 1, it, 0.0, 0.0, False))
    return placed, len(sheets)


def best_orient(paper, orient, items, margin, gap):
    if orient != 'best':
        return orient
    best = None
    for o in ('portrait', 'landscape'):
        pw, ph = paper_size(paper, o)
        aw, ah = pw - 2 * margin, ph - 2 * margin - HEADER_H
        tiles = tile_items(items, aw, ah)
        _p, n = pack(tiles, aw, ah, gap)
        score = (n, len(tiles))
        if best is None or score < best[0]:
            best = (score, o)
    return best[1]


def layout_kit(pieces, opts, choices, materials=None):
    """The whole kit as sheets of drawing steps: (paper w, h, [sheet steps], summary)."""
    f = 1.0 / float(opts['scale'])
    items = kit_items(pieces, opts, choices)
    orient = best_orient(opts['paper'], opts['orient'], items, opts['margin'], opts['gap'])
    pw, ph = paper_size(opts['paper'], orient)
    m = opts['margin']
    aw, ah = pw - 2 * m, ph - 2 * m - HEADER_H
    tiles = tile_items(items, aw, ah)
    placed, n_sheets = pack(tiles, aw, ah, opts['gap'])
    first = 1 if opts.get('instructions', True) else 0
    total = n_sheets + first
    sheets = [[] for _ in range(n_sheets)]
    for si, it, x, y, turn in placed:
        sheets[si] += piece_steps(it, m + x, m + HEADER_H + y, turn, f, opts, choices, materials)
    name = opts.get('kit_name') or "Card kit"
    out = []
    for k, st in enumerate(sheets):
        out.append(header_steps(pw, ph, m, name, k + first + 1, total, opts) + st)
    if first:
        out.insert(0, instruction_steps(pw, ph, m, name, total, pieces, items, tiles, opts, choices))
    sheet_of = {}
    rects = {}                       # sheet: [(piece, x, y, w, h)] - where each piece is, to click on
    for si, it, x, y, turn in placed:
        sheet_of[it['i']] = min(sheet_of.get(it['i'], 10 ** 6), si + first)
        bw, bh = (it['h'], it['w']) if turn else (it['w'], it['h'])
        rects.setdefault(si + first, []).append((it['i'], m + x, m + HEADER_H + y, bw, bh + LABEL_H))
    summary = {'sheets': total, 'pieces': len(items), 'orient': orient, 'paper': opts['paper'],
               'tiled': sorted(set(t['i'] + 1 for t in tiles if t.get('clip'))), 'sheet_of': sheet_of,
               'rects': rects}
    return pw, ph, out, summary


def _mapper2(it, X, Y, turn, f):
    """From a piece's real mm (y up) to page mm (y down), for an item placed at X, Y."""
    bx0, by0, bx1, by1 = it['box']
    clip = it.get('clip')
    cx, cy = (clip[0], clip[1]) if clip else (0.0, 0.0)
    cw, ch = (it['w'], it['h'])

    def go(p):
        lx = (p[0] - bx0) * f - cx
        ly = (p[1] - by0) * f - cy
        if turn:
            lx, ly = ly, cw - lx
            return (X + lx, Y + (cw - ly))
        return (X + lx, Y + (ch - ly))
    return go


def piece_steps(it, X, Y, turn, f, opts, choices, materials):
    pc = it['piece']
    i = it['i']
    ch = choices.get(i, {})
    go = _mapper2(it, X, Y, turn, f)
    bw, bh = (it['h'], it['w']) if turn else (it['w'], it['h'])
    steps = []
    if it.get('clip'):
        steps.append(('clip', [[(X, Y), (X + bw, Y), (X + bw, Y + bh), (X, Y + bh)]]))
    lw = float(opts.get('line_w', 0.25))
    # tabs first (under the piece)
    for e, poly, label in it['tabs']:
        steps.append(('poly', [[go(p) for p in poly]], TAB_FILL, None, 0.0, False))
    # the faces, far ones first, kept inside the piece's outline (bricks standing proud at a
    # gable don't spill over the tabs)
    steps.append(('clip', [[go(p) for p in lp] for lp in pc['loops']]))
    face_steps = []
    # the piece's main colour all over first, so no gap between its faces shows the paper through
    if pc.get('main') is not None:
        base = tuple(c / 255.0 for c in pc['main'])
        if ch.get('mat') == '__white__':
            base = (1.0, 1.0, 1.0)
        elif ch.get('look'):
            base = ch['look'][0]
        face_steps.append((0, ('poly', [[go(p) for p in lp] for lp in pc['loops']], base, None, 0.0, False)))
    # the openings right through the piece (windows with no glass): the glass look goes in them
    wm = opts.get('windows', 'cut')
    if wm in ('model', 'print'):
        gl = GLASS_PRINT
        if wm == 'model':
            for fc in pc['draw']:
                if fc['glass']:
                    gl = fc['rgb']
                    break
        for lp in pc.get('openings', []):
            face_steps.append((0, ('poly', [[go(p) for p in lp]], gl, None, 0.0, False)))
    override = ch.get('look')                   # (rgb, texture) of the picked material, or None
    white = ch.get('mat') == '__white__'
    main = pc['main']
    for fc in pc['draw']:
        rgb, tex = fc['rgb'], fc['tex']
        band = 0
        if fc['glass']:
            wm = opts.get('windows', 'cut')
            if wm == 'cut':
                face_steps.append((band, ('poly', [[go(p) for p in fc['outer']]] + [[go(p) for p in h] for h in fc['holes']],
                                   (1.0, 1.0, 1.0), (0.0, 0.0, 0.0), lw * 0.8, False)))
                continue
            if wm == 'plain':
                face_steps.append((band, ('poly', [[go(p) for p in fc['outer']]] + [[go(p) for p in h] for h in fc['holes']],
                                   (1.0, 1.0, 1.0), None, 0.0, False)))
                continue
            rgb, tex = (fc['rgb'] if wm == 'model' else GLASS_PRINT), None
        elif white and colour_key(rgb) == main:
            rgb, tex = (1.0, 1.0, 1.0), None
        elif override and colour_key(fc['rgb']) == main:
            rgb, tex = override[0], override[1]
        k = (0.72 + 0.28 * fc['shade']) if opts.get('shading', True) else 1.0
        fill = _shade(rgb, k)
        if opts.get('lines', True):
            lum = 0.3 * fill[0] + 0.59 * fill[1] + 0.11 * fill[2]
            # joints show darker on light colours, lighter on dark ones (slates, dark paint)
            line = _shade(fill, 0.62) if lum > 0.42 else tuple(c + (1.0 - c) * 0.38 for c in fill)
        else:
            line = None
        fillspec = ('tex', tex[0], tex[1] * 1000.0 * f, tex[2] * 1000.0 * f, fill) if tex else fill
        face_steps.append((band, ('poly', [[go(p) for p in fc['outer']]] + [[go(p) for p in h] for h in fc['holes']],
                           fillspec, line, 0.06 if line else 0.0, False)))
    # far to near, with faces of the same colour gathered together where nothing between them
    # could cover them - so they draw as a few joined-up shapes (one per colour) instead of
    # thousands of little ones, and a pane of glass is never hidden under the frame's colour
    face_steps = group_faces([t[1] for t in face_steps])
    # all the faces as one step: drawn as one picture in the PDF (thousands of bricks as shapes
    # make a PDF that LibreOffice takes ages to open), or shape by shape
    ox0, oy0, ox1, oy1 = bounds2([q for st_ in face_steps for q in st_[1][0]] and
                                 [[q for st_ in face_steps for q in st_[1][0]]] or [[(X, Y)]])
    steps.append(('faces', ox0 - 0.5, oy0 - 0.5, ox1 - ox0 + 1.0, oy1 - oy0 + 1.0, face_steps))
    steps.append(('noclip',))
    # cut lines round the piece and its holes; fold lines where the tabs are
    tabbed = []
    for e, poly, label in it['tabs']:
        tabbed.append(e)
        steps.append(('line', [go(e['a']), go(e['b'])], (0.0, 0.0, 0.0), lw, True))
        a, b, c, d = poly
        steps.append(('line', [go(b), go(c), go(d), go(a)], (0.0, 0.0, 0.0), lw, False))
        mid = go(((c[0] + d[0] + a[0] + b[0]) / 4.0, (c[1] + d[1] + a[1] + b[1]) / 4.0))
        pa, pb = go(e['a']), go(e['b'])
        ang = math.degrees(math.atan2(pb[1] - pa[1], pb[0] - pa[0]))
        if ang > 90:
            ang -= 180
        elif ang < -90:
            ang += 180
        th = min(opts['tab_w'] * 0.42, 2.4)
        if e['len'] * f > len(label) * th * 0.6:
            steps.append(('text', mid[0], mid[1], label, th, (0.25, 0.25, 0.25), 'cc', False, ang))
    holes_ = set(id(lp) for lp in pc.get('openings', []))
    for lp in pc['loops']:
        if id(lp) in holes_ and opts.get('windows', 'cut') != 'cut':
            continue                    # window openings: nothing to cut unless they're cut out
        segs = segments_not_tabbed(lp, tabbed)
        for s in segs:
            steps.append(('line', [go(p) for p in s], (0.0, 0.0, 0.0), lw, False))
    if it.get('clip'):
        steps.append(('noclip',))
        # where the tiles join: a dashed line and a note
        rows, cols, r, c = it['tiles']
        steps.append(('poly', [[(X, Y), (X + bw, Y), (X + bw, Y + bh), (X, Y + bh)]], None,
                      (0.55, 0.55, 0.55), 0.15, True))
    # the piece's number on one of its glue tabs (hidden once it's glued, so it never shows on
    # the finished model), near one end of the longest tab, clear of the "glue to" words;
    # a piece with no tabs just has its number in the name underneath
    if opts.get('numbers', True) and it['tabs']:
        e, poly, _lab = max(it['tabs'], key=lambda tb: tb[0]['len'])
        a, b, c, d = poly
        s_ = go(((a[0] + d[0]) / 2.0, (a[1] + d[1]) / 2.0))     # the tab's two ends, half way out
        t_ = go(((b[0] + c[0]) / 2.0, (b[1] + c[1]) / 2.0))
        ln = math.hypot(t_[0] - s_[0], t_[1] - s_[1])
        if ln > 7.0:
            k_ = min(0.5, 3.8 / ln)
            q = (s_[0] + (t_[0] - s_[0]) * k_, s_[1] + (t_[1] - s_[1]) * k_)
            if (not it.get('clip')) or (X <= q[0] <= X + bw and Y <= q[1] <= Y + bh):
                steps.append(('badge', q[0], q[1], str(i + 1)))
    lab = "%d%s  %s" % (i + 1, it.get('tile') or "", pc['name'])
    if it.get('clip'):
        lab += "  (part %s of %d - join to the next part)" % (it['tile'], it['tiles'][0] * it['tiles'][1])
    # the name is cut short to fit under the piece, so it doesn't run into the next one
    lab = clip_text(lab, max(len(str(i + 1)) + 1, int(bw / 1.25)))
    steps.append(('text', X, Y + bh + 3.6, lab, 2.4, (0.1, 0.1, 0.1), 'l', False, 0.0))
    return steps


def group_faces(face_steps):
    """Faces (far to near) put in order so faces of the same look sit together, without ever
    moving one past a face it could overlap (so what's in front stays in front)."""
    runs = []                         # [look, [steps], bounding box of the run]

    def box(st):
        pts = st[1][0]
        return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))

    def hit(a, b):
        return not (a[2] <= b[0] + 1e-6 or b[2] <= a[0] + 1e-6 or a[3] <= b[1] + 1e-6 or b[3] <= a[1] + 1e-6)
    for st in face_steps:
        look = repr(st[2:])
        b = box(st)
        target = None
        for k in range(len(runs) - 1, max(-1, len(runs) - 60), -1):
            if runs[k][0] == look:
                target = k
                break
            if hit(runs[k][2], b):
                break                 # something in the way: it can't go further back
        if target is None:
            runs.append([look, [st], b])
        else:
            r = runs[target]
            r[1].append(st)
            r[2] = (min(r[2][0], b[0]), min(r[2][1], b[1]), max(r[2][2], b[2]), max(r[2][3], b[3]))
    return [st for r in runs for st in r[1]]


def segments_not_tabbed(loop, tabbed, eps=1e-4):
    """The loop as runs of lines, leaving out the parts under a tab (they're folds)."""
    n = len(loop)
    runs, cur = [], []

    def on_tab(a, b):
        for e in tabbed:
            ea, eb = e['a'], e['b']
            L = e['len']
            dx, dy = (eb[0] - ea[0]) / L, (eb[1] - ea[1]) / L
            ok = True
            for p in (a, b):
                t = (p[0] - ea[0]) * dx + (p[1] - ea[1]) * dy
                d = abs(-(p[0] - ea[0]) * dy + (p[1] - ea[1]) * dx)
                if d > eps * max(1.0, L) * 10 or t < -eps * L - 1e-6 or t > L * (1 + eps) + 1e-6:
                    ok = False
                    break
            if ok:
                return True
        return False
    for k in range(n):
        a, b = loop[k], loop[(k + 1) % n]
        if on_tab(a, b):
            if len(cur) > 1:
                runs.append(cur)
            cur = []
            continue
        if not cur:
            cur = [a, b]
        else:
            cur.append(b)
    if len(cur) > 1:
        runs.append(cur)
    # join the last run onto the first when the loop wraps round
    if len(runs) > 1 and runs[0][0] == runs[-1][-1]:
        runs[0] = runs[-1][:-1] + runs[0]
        runs.pop()
    return runs


def number_spot(pc, f):
    """Somewhere inside the piece near its bottom-left corner for its number."""
    r = 2.6 / f
    for fx, fy in ((0.0, 0.0), (0.0, 0.5), (0.5, 0.0), (0.5, 0.5)):
        p = (r * 1.4 + fx * pc['w'], r * 1.4 + fy * pc['h'])
        if all(inside_outline(q, pc['loops']) for q in
               (p, (p[0] - r, p[1]), (p[0] + r, p[1]), (p[0], p[1] - r), (p[0], p[1] + r))):
            return p
    return None


def header_steps(pw, ph, m, name, k, total, opts):
    st = [('text', m, m + 4.0, "%s  -  sheet %d of %d" % (name, k, total), 3.4, (0, 0, 0), 'l', True, 0.0),
          ('text', m, m + 9.0, "Print at 100%%  (\"Actual size\") - not \"Fit to page\". Scale %s."
           % scale_name(opts['scale']), 2.3, (0.2, 0.2, 0.2), 'l', False, 0.0)]
    st += check_bar(pw - m - 50.0, m + 3.0)
    return st


def check_bar(x, y):
    st = [('line', [(x, y + 3.0), (x + 50.0, y + 3.0)], (0, 0, 0), 0.35, False)]
    for t in range(0, 51, 10):
        st.append(('line', [(x + t, y + 1.6), (x + t, y + 3.0)], (0, 0, 0), 0.25, False))
    st.append(('text', x + 25.0, y + 7.0, "This bar should measure 50 mm", 2.2, (0.2, 0.2, 0.2), 'c', False, 0.0))
    return st


def scale_name(scale):
    for lab, s in SCALES:
        if abs(s - scale) < 1e-6:
            return " ".join(lab.split())
    return "1:%g" % scale


def instruction_steps(pw, ph, m, name, total, pieces, items, tiles, opts, choices):
    st = header_steps(pw, ph, m, name, 1, total, opts)
    y = m + HEADER_H + 6.0
    x = m
    st.append(('text', x, y, "How to build it", 4.2, (0, 0, 0), 'l', True, 0.0))
    y += 7.0
    steps = [
        "1. Print every sheet at 100% (\"Actual size\" in the print box). Measure the 50 mm bar to check.",
        "2. Stick each sheet onto thin card (about 1 mm, cereal-box card or greyboard) with spray glue or a glue stick.",
        "3. Cut along the solid lines with a sharp knife and a steel rule. Cut out the white window panes too.",
        "4. Score the dashed lines lightly on the printed side and fold the tabs back.",
        "5. Glue clear plastic (acetate) behind the window openings for glass.",
        "6. Glue each tab behind the piece it names (\"glue to 3\" goes behind piece 3). Work in number order.",
        "7. Paint the cut edges of the card to match, so the white doesn't show.",
    ]
    if opts['windows'] != 'cut':
        steps[2] = "3. Cut along the solid lines with a sharp knife and a steel rule."
        steps[4] = "5. The glass is printed: a coat of gloss varnish over it makes it shine."
    for s in steps:
        for line in wrap(s, int((pw - 2 * m) / 1.75)):
            st.append(('text', x, y, line, 2.9, (0.1, 0.1, 0.1), 'l', False, 0.0))
            y += 4.6
        y += 0.8
    # the key
    y += 3.0
    st.append(('text', x, y, "Key", 4.0, (0, 0, 0), 'l', True, 0.0))
    y += 4.0
    st.append(('line', [(x, y + 2), (x + 18, y + 2)], (0, 0, 0), 0.3, False))
    st.append(('text', x + 22, y + 3.2, "Cut", 2.9, (0, 0, 0), 'l', False, 0.0))
    st.append(('line', [(x + 45, y + 2), (x + 63, y + 2)], (0, 0, 0), 0.3, True))
    st.append(('text', x + 67, y + 3.2, "Fold (score first)", 2.9, (0, 0, 0), 'l', False, 0.0))
    st.append(('poly', [[(x + 108, y + 4), (x + 126, y + 4), (x + 122, y), (x + 112, y)]], TAB_FILL,
               (0, 0, 0), 0.25, False))
    st.append(('text', x + 130, y + 3.2, "Glue tab", 2.9, (0, 0, 0), 'l', False, 0.0))
    y += 14.0
    # the parts list
    st.append(('text', x, y, "Parts", 4.0, (0, 0, 0), 'l', True, 0.0))
    y += 6.0
    f = 1.0 / float(opts['scale'])
    shown = {it['i'] for it in items}
    tiled = {}
    for t in tiles:
        if t.get('clip'):
            tiled[t['i']] = tiled.get(t['i'], 0) + 1
    col_w = (pw - 2 * m) / 2.0
    rows = [i for i in range(len(pieces)) if i in shown]
    per_col = max(1, int((ph - m - y - 4) / 4.4))
    for k, i in enumerate(rows):
        if k >= per_col * 2:
            st.append(('text', x, ph - m, "... and %d more" % (len(rows) - k), 2.6, (0, 0, 0), 'l', False, 0.0))
            break
        cx = x + (k // per_col) * col_w
        cy = y + (k % per_col) * 4.4
        pc = pieces[i]
        txt = "%d   %s   %.0f x %.0f mm" % (i + 1, pc['name'], pc['w'] * f, pc['h'] * f)
        if tiled.get(i):
            txt += "  (in %d parts)" % tiled[i]
        st.append(('text', cx, cy, clip_text(txt, int(col_w / 1.45)), 2.7, (0.1, 0.1, 0.1), 'l', False, 0.0))
    st.append(('text', pw - m, ph - m + 4.0, "Made with %s %s - Eddy's Model Works" % (PLUGIN_NAME, VERSION),
               2.0, (0.45, 0.45, 0.45), 'r', False, 0.0))
    return st


def wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = "   " + w
        else:
            cur = (cur + " " + w) if cur else w
    if cur:
        lines.append(cur)
    return lines


def clip_text(t, n):
    return t if len(t) <= n else t[:max(1, n - 3)] + "..."


# ===========================================================================
# Drawing with Qt: the outline of a piece, and the drawing steps onto the PDF or the preview
# ===========================================================================
def qt_outline(side):
    """The outline of a piece: its faces on one side joined into one shape (with any holes
    right through it), as loops in mm."""
    from PySide6.QtGui import QPainterPath, QPolygonF
    from PySide6.QtCore import QPointF, Qt
    S = 100.0
    path = QPainterPath()
    path.setFillRule(Qt.FillRule.WindingFill)
    for outer, holes in side:
        o = outer if area2(outer) > 0 else outer[::-1]
        path.addPolygon(QPolygonF([QPointF(x * S, y * S) for x, y in o]))
        path.closeSubpath()
        for h in holes:
            hh = h if area2(h) < 0 else h[::-1]
            path.addPolygon(QPolygonF([QPointF(x * S, y * S) for x, y in hh]))
            path.closeSubpath()
    simp = path.simplified()
    out = []
    for poly in simp.toSubpathPolygons():
        lp = clean_loop([(p.x() / S, p.y() / S) for p in poly])
        if len(lp) >= 3:
            out.append(lp)
    return out


_TEX_CACHE = {}


def _qcolor(rgb):
    from PySide6.QtGui import QColor
    return QColor.fromRgbF(float(rgb[0]), float(rgb[1]), float(rgb[2]))


def _path(loops):
    from PySide6.QtGui import QPainterPath, QPolygonF
    from PySide6.QtCore import QPointF, Qt
    p = QPainterPath()
    p.setFillRule(Qt.FillRule.OddEvenFill)
    for lp in loops:
        if len(lp) >= 2:
            p.addPolygon(QPolygonF([QPointF(x, y) for x, y in lp]))
            p.closeSubpath()
    return p


def _pen(rgb, w, dash):
    from PySide6.QtGui import QPen
    from PySide6.QtCore import Qt
    pen = QPen(_qcolor(rgb))
    pen.setWidthF(max(w, 0.01))
    pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
    if dash:
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        ww = max(w, 0.01)
        pen.setDashPattern([2.0 / ww, 1.2 / ww])
    return pen


def _brush(fill):
    from PySide6.QtGui import QBrush, QImage, QTransform
    if isinstance(fill, tuple) and fill and fill[0] == 'tex':
        _t, path, tw, th, rgb = fill
        img = _TEX_CACHE.get(path)
        if img is None:
            img = QImage(path)
            _TEX_CACHE[path] = img
        if img is not None and not img.isNull() and tw > 0 and th > 0:
            b = QBrush(img)
            b.setTransform(QTransform.fromScale(tw / img.width(), th / img.height()))
            return b
        return QBrush(_qcolor(rgb))
    return QBrush(_qcolor(fill))


def _text(painter, x, y, text, h, rgb, align, bold, ang):
    from PySide6.QtGui import QFont, QFontMetricsF
    from PySide6.QtCore import QPointF
    font = QFont("Arial")
    font.setPixelSize(100)
    font.setBold(bool(bold))
    fm = QFontMetricsF(font)
    w = fm.horizontalAdvance(text)
    k = h * 1.35 / 100.0
    dx = 0.0 if align == 'l' else (-w if align == 'r' else -w / 2.0)
    dy = (fm.ascent() - fm.descent()) / 2.0 if align == 'cc' else 0.0
    painter.save()
    painter.translate(x, y)
    if ang:
        painter.rotate(ang)
    painter.scale(k, k)
    painter.setFont(font)
    painter.setPen(_qcolor(rgb))
    painter.drawText(QPointF(dx, dy), text)
    painter.restore()


def paint_joined(painter, sub):
    """Faces drawn as joined-up shapes: each run of faces with the same fill and line becomes one
    shape (many outlines in one path). Sharp at any size, and a PDF program reads one shape per
    colour instead of one per brick, so it opens quickly."""
    from PySide6.QtGui import QPainterPath, QPolygonF
    from PySide6.QtCore import Qt, QPointF
    run, key = [], None

    def flush():
        if not run:
            return
        fill, line, lw = run[0][2], run[0][3], run[0][4]
        path = QPainterPath()
        path.setFillRule(Qt.FillRule.WindingFill)
        for st in run:
            for j, lp in enumerate(st[1]):
                if len(lp) < 3:
                    continue
                a = area2(lp)
                # outlines one way round, holes the other, so overlaps fill and holes stay open
                lp2 = lp if ((a > 0) == (j == 0)) else lp[::-1]
                path.addPolygon(QPolygonF([QPointF(px, py) for px, py in lp2]))
                path.closeSubpath()
        if fill is not None:
            painter.fillPath(path, _brush(fill))
        if line is not None and lw > 0:
            painter.strokePath(path, _pen(line, lw, False))
        del run[:]
    for st in sub:
        k_ = repr(st[2:])
        if k_ != key:
            flush()
            key = k_
        run.append(st)
    flush()


def paint_steps(painter, steps, dpi=None):
    """Draws one sheet's steps. The painter must already be set to mm (y down). With dpi, each
    piece's faces are drawn as one picture at that many dots per inch (a much lighter PDF)."""
    from PySide6.QtCore import Qt, QPointF, QRectF
    from PySide6.QtGui import QPainter, QPolygonF, QImage, QColor
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    for s in steps:
        k = s[0]
        try:
            if k == 'faces':
                x, y, w, h, sub = s[1:]
                if not dpi:
                    paint_joined(painter, sub)
                    continue
                d = dpi / 25.4
                iw, ih = max(1, int(math.ceil(w * d))), max(1, int(math.ceil(h * d)))
                if iw * ih > 12000 * 12000:            # never a silly size: fall back to shapes
                    paint_steps(painter, sub)
                    continue
                img = QImage(iw, ih, QImage.Format.Format_ARGB32_Premultiplied)
                img.fill(QColor(0, 0, 0, 0))
                q = QPainter(img)
                q.scale(d, d)
                q.translate(-x, -y)
                paint_steps(q, sub)
                q.end()
                painter.drawImage(QRectF(x, y, iw / d, ih / d), img)
            elif k == 'poly':
                loops, fill, line, lw, dash = s[1:]
                path = _path(loops)
                if fill is not None:
                    painter.fillPath(path, _brush(fill))
                if line is not None and lw > 0:
                    painter.strokePath(path, _pen(line, lw, dash))
            elif k == 'line':
                pts, rgb, lw, dash = s[1:]
                painter.setPen(_pen(rgb, lw, dash))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPolyline(QPolygonF([QPointF(x, y) for x, y in pts]))
            elif k == 'text':
                _text(painter, *s[1:])
            elif k == 'badge':
                x, y, t = s[1:]
                painter.setPen(_pen((0, 0, 0), 0.25, False))
                painter.setBrush(_qcolor((1, 1, 1)))
                painter.drawEllipse(QPointF(x, y), 2.2, 2.2)
                _text(painter, x, y, t, 2.4, (0, 0, 0), 'cc', True, 0.0)
            elif k == 'clip':
                painter.save()
                op = Qt.ClipOperation.IntersectClip if painter.hasClipping() else Qt.ClipOperation.ReplaceClip
                painter.setClipPath(_path(s[1]), op)
            elif k == 'noclip':
                painter.restore()
        except Exception as e:
            print("%s: drawing %s: %s" % (PLUGIN_NAME, k, e))


def write_pdf(path, pw, ph, sheets, paper, title="", dpi=None):
    from PySide6.QtGui import QPdfWriter, QPainter, QPageSize, QPageLayout
    from PySide6.QtCore import QMarginsF
    ids = {"A4": QPageSize.PageSizeId.A4, "A3": QPageSize.PageSizeId.A3, "A5": QPageSize.PageSizeId.A5,
           "Letter": QPageSize.PageSizeId.Letter}
    w = QPdfWriter(path)
    w.setResolution(600)
    w.setPageSize(QPageSize(ids.get(paper, QPageSize.PageSizeId.A4)))
    w.setPageOrientation(QPageLayout.Orientation.Landscape if pw > ph else QPageLayout.Orientation.Portrait)
    w.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
    try:
        w.setTitle(title or "Card kit")
        w.setCreator("%s %s" % (PLUGIN_NAME, VERSION))
    except Exception:
        pass
    p = QPainter(w)
    if not p.isActive():
        raise IOError("Could not write %s (is it open in another program?)" % path)
    try:
        s = w.resolution() / 25.4
        for k, st in enumerate(sheets):
            if k:
                w.newPage()
            p.save()
            p.scale(s, s)
            paint_steps(p, st, dpi)
            p.restore()
    finally:
        p.end()


# ===========================================================================
# The window
# ===========================================================================
from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QColor, QIcon, QPainter, QImage
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox, QCheckBox,
    QPushButton, QLabel, QMessageBox, QWidget, QInputDialog, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QFileDialog, QApplication, QAbstractItemView
)

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


INFO_TEXT = ("<b>How to use it</b><br>"
             "1. Select the building (or some walls) in the model and click <b>Read the selection</b>. "
             "Each piece is drawn flat as seen from outside, at true scale, in its colours.<br>"
             "2. Pick the scale and paper on <b>Scale &amp; paper</b>.<br>"
             "3. On <b>Parts</b>, untick pieces you don't want, pick a material for any piece (its main "
             "colour changes - windows and doors keep theirs), turn a piece to show its other side, and "
             "choose where its glue tabs go.<br>"
             "4. Click <b>Make card kit (PDF)...</b> and print it at 100% (\"Actual size\").<br><br>"
             "Solid lines are cut, dashed lines are folds. Each tab says which piece it glues behind. "
             "Groups joined in Show / Hide's Groups tab come out as one piece, as in Scale Studio.")

EDDY_TIPS = {
    "read the selection": "Reads what's selected in the model: each group with faces becomes a piece "
                          "(or groups a few levels in - see 'Pieces are'), drawn flat from outside.",
    "make card kit (pdf)...": "Saves the kit as a PDF and opens it. Print it at 100% (Actual size).",
    "scale": "The model scale the kit is printed at. 'Already at print size' if you've scaled the model "
             "down yourself.",
    "paper": "The paper it's printed on.",
    "sheet": "Upright, sideways, or whichever uses fewer sheets.",
    "margin": "Blank border round each sheet. 10 mm suits most printers.",
    "gap between pieces": "Space left between pieces on the sheet, for cutting.",
    "tab width": "How far the glue tabs stand out from the edge, on the paper.",
    "tabs along the bottom": "Tabs along the foot of each wall, to glue it down onto the base (or "
                             "onto a piece of card). Roofs never get them.",
    "windows": "Cut out: the panes are white with a cut line, cut them out and put clear film behind. "
               "Plain: white, nothing to cut. Coloured: the glass colour from the model, or pale blue.",
    "lines between faces": "A thin darker line round every face, so bricks, tiles and planks show up.",
    "shading": "Faces that don't face straight out (reveals, sills, a roof seen from the gable) are "
               "drawn a little darker, for depth.",
    "number on each piece": "A small numbered circle on one of each piece's glue tabs, so you know "
                            "which is which once it's cut out - and it's hidden once it's glued.",
    "instructions sheet first": "A first sheet with how to build it, the key and the list of parts.",
    "cut line": "Thickness of the cut lines and fold lines.",
    "pieces in the pdf": "Sharp: the bricks and colours are drawn as shapes, joined up by colour, so "
                         "they print crisp at any size and the PDF still opens quickly (LibreOffice too). "
                         "As a picture: each piece goes in as a picture - only if a PDF program struggles.",
    "then open it in": "Which program opens the kit once it's saved. Edge or Chrome open it straight away "
                       "and print it well; LibreOffice is slow with it and draws the slate joints badly.",
    "open pdf with...": "Opens the last kit you saved, asking which program to use.",
    "picture quality": "How sharp the picture is. 300 dpi is as sharp as most home printers print.",
    "kit name": "Printed at the top of every sheet. Empty: the name of the first group.",
    "pieces are": "How the model is split into pieces - the same as Scale Studio's Pieces page.",
    "paint the picked colours onto the model": "Paints each piece's picked material onto the model "
                                               "too (its main colour only). Ctrl+Z undoes it.",
    "tick all": "Prints every piece.",
    "print slates, tiles and cladding on the piece under them": "Roof Tiles, Corrugated Iron and Wood "
        "Planking make their covering as a piece of its own. Ticked, each covering is printed on the roof "
        "slope or wall it lies on, as one piece - so the roof comes out slated, not plain.",
    "leave out the frame (keep the fascia, barge and soffit boards)": "Subframe's studs, plates, trusses "
        "and glazing frames aren't wanted in a card kit (the card is the strength), so they're left "
        "out. The boards on the outside - fascia, barge boards with their finials, soffits - stay in.",
    "untick all": "Prints none - then tick the ones you want.",
}


def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    return {}


def save_settings(**kw):
    d = load_settings()
    d.update(kw)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
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


def save_preset_file(name, values):
    os.makedirs(PRESET_DIR, exist_ok=True)
    d = {'name': name}
    d.update({k: values[k] for k in DEFAULTS if k in values and k != 'kit_name'})
    with open(os.path.join(PRESET_DIR, _safe_name(name) + ".json"), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)


def _swatch(rgb, size=14):
    pm = QPixmap(size, size)
    pm.fill(_qcolor(rgb))
    return QIcon(pm)


def _paint_command(mutate, meshes):
    """One undo step for repainting faces (as 3D Layers & Colours does it)."""
    try:
        from core.history import Command
    except Exception:
        Command = None
    if Command is None or not meshes or not all(hasattr(m, 'capture_state') for m in meshes):
        return SnapshotImport(mutate)

    class PaintCommand(Command):
        def __init__(self):
            self.before = self.after = None

        @staticmethod
        def _bump(scene):
            try:
                from core.history import _dirty_group_chunks
                _dirty_group_chunks(scene)
            except Exception:
                pass
            try:
                scene.version += 1
            except Exception:
                pass

        def do(self, scene):
            if self.after is None:
                self.before = [(m, m.capture_state()) for m in meshes]
                try:
                    mutate(scene)
                except BaseException:
                    for m, s in self.before:
                        m.restore_state(s)
                    raise
                self.after = [(m, m.capture_state()) for m in meshes]
            else:
                for m, s in self.after:
                    m.restore_state(s)
            self._bump(scene)

        def undo(self, scene):
            for m, s in self.before:
                m.restore_state(s)
            self._bump(scene)

    return PaintCommand()


def open_pdf(path, how):
    """Opens the saved PDF: in the usual program, in Edge or Chrome, or with Windows' 'Open with'
    box so you can pick (LibreOffice is slow with these and draws the slate joints badly)."""
    import sys
    import subprocess
    path = os.path.normpath(path)
    try:
        if how == 'none':
            return
        if sys.platform.startswith('win'):
            if how == 'edge':
                subprocess.Popen('start "" msedge "%s"' % path, shell=True)
                return
            if how == 'chrome':
                subprocess.Popen('start "" chrome "%s"' % path, shell=True)
                return
            if how == 'folder':
                subprocess.Popen('explorer /select,"%s"' % path, shell=True)
                return
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
    except Exception as e:
        print("%s: couldn't open the PDF: %s" % (PLUGIN_NAME, e))
        try:
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        except Exception:
            pass


class ListCombo(QComboBox):
    """A drop-down in the Parts list: the mouse wheel scrolls the list, it never changes the choice
    (rolling the wheel over a list full of these was quietly picking materials)."""

    def __init__(self, *a):
        super().__init__(*a)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, ev):
        ev.ignore()


class SheetPreview(QWidget):
    """The sheets as they'll print, one at a time."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 380)
        self.pw, self.ph, self.sheets = 210.0, 297.0, []
        self.index = 0
        self._img = None
        self._key = None
        self.message = "Select a building and click 'Read the selection'."
        self.rects = {}                  # sheet: [(piece, x, y, w, h)] in page mm
        self.lit = None                  # the piece picked, outlined in blue
        self.on_pick = None              # called with the piece clicked
        self._place = None               # (x, y, scale) of the page in the widget
        self.setMouseTracking(True)

    def set_sheets(self, pw, ph, sheets):
        self.pw, self.ph, self.sheets = pw, ph, sheets
        self.index = min(self.index, max(0, len(sheets) - 1))
        self._img = None
        self.update()

    def go(self, k):
        if self.sheets:
            self.index = max(0, min(len(self.sheets) - 1, k))
            self._img = None
            self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(120, 124, 130))
        if not self.sheets:
            p.setPen(QColor(255, 255, 255))
            p.drawText(self.rect().adjusted(20, 20, -20, -20),
                       int(Qt.AlignmentFlag.AlignCenter) | int(Qt.TextFlag.TextWordWrap), self.message)
            p.end()
            return
        W, H = self.width(), self.height()
        s = min((W - 16) / self.pw, (H - 16) / self.ph)
        iw, ih = int(self.pw * s), int(self.ph * s)
        key = (self.index, iw, ih, id(self.sheets))
        if self._img is None or self._key != key:
            dpr = self.devicePixelRatioF() if hasattr(self, 'devicePixelRatioF') else 1.0
            img = QImage(int(iw * dpr), int(ih * dpr), QImage.Format.Format_ARGB32_Premultiplied)
            img.fill(QColor(255, 255, 255))
            q = QPainter(img)
            q.scale(s * dpr, s * dpr)
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                paint_steps(q, self.sheets[self.index])
            finally:
                QApplication.restoreOverrideCursor()
                q.end()
            try:
                img.setDevicePixelRatio(dpr)
            except Exception:
                pass
            self._img, self._key = img, key
        x, y = (W - iw) // 2, (H - ih) // 2
        p.fillRect(x + 4, y + 4, iw, ih, QColor(60, 60, 60, 120))
        p.drawImage(x, y, self._img)
        self._place = (x, y, s)
        if self.lit is not None:
            from PySide6.QtGui import QPen
            from PySide6.QtCore import QRectF
            for i, rx, ry, rw, rh in self.rects.get(self.index, []):
                if i == self.lit:
                    pen = QPen(QColor(30, 110, 230), 3)
                    p.setPen(pen)
                    p.setBrush(QColor(30, 110, 230, 30))
                    p.drawRect(QRectF(x + rx * s - 3, y + ry * s - 3, rw * s + 6, rh * s + 6))
        p.end()

    def piece_at(self, pos):
        if not self._place:
            return None
        x, y, s = self._place
        mx, my = (pos.x() - x) / s, (pos.y() - y) / s
        for i, rx, ry, rw, rh in self.rects.get(self.index, []):
            if rx <= mx <= rx + rw and ry <= my <= ry + rh:
                return i
        return None

    def mouseMoveEvent(self, ev):
        try:
            pos = ev.position() if hasattr(ev, 'position') else ev.pos()
            over = self.piece_at(pos) is not None
            self.setCursor(Qt.CursorShape.PointingHandCursor if over else Qt.CursorShape.ArrowCursor)
        except Exception:
            pass

    def mousePressEvent(self, ev):
        try:
            pos = ev.position() if hasattr(ev, 'position') else ev.pos()
            i = self.piece_at(pos)
        except Exception:
            i = None
        if i is not None and self.on_pick is not None:
            self.on_pick(i)


class KeyDrawing(QWidget):
    """What the lines and marks on the sheets mean."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 300)

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(255, 255, 255))
        s = min(self.width() / 100.0, self.height() / 110.0)
        p.scale(s, s)
        st = [('text', 5, 9, "What the marks mean", 4.0, (0, 0, 0), 'l', True, 0.0),
              ('line', [(5, 20), (30, 20)], (0, 0, 0), 0.4, False),
              ('text', 36, 21.2, "Cut", 3.2, (0, 0, 0), 'l', False, 0.0),
              ('line', [(5, 32), (30, 32)], (0, 0, 0), 0.4, True),
              ('text', 36, 33.2, "Fold - score it first", 3.2, (0, 0, 0), 'l', False, 0.0),
              ('poly', [[(5, 47), (30, 47), (25, 41), (10, 41)]], TAB_FILL, (0, 0, 0), 0.3, False),
              ('text', 17.5, 44.2, "glue to 3", 2.2, (0.25, 0.25, 0.25), 'cc', False, 0.0),
              ('text', 36, 45.2, "Glue tab - goes behind piece 3", 3.2, (0, 0, 0), 'l', False, 0.0),
              ('poly', [[(5, 53), (30, 53), (30, 68), (5, 68)], [(10, 56), (25, 56), (25, 65), (10, 65)]],
               (0.66, 0.31, 0.22), (0, 0, 0), 0.3, False),
              ('poly', [[(10, 56), (25, 56), (25, 65), (10, 65)]], (1, 1, 1), (0, 0, 0), 0.3, False),
              ('text', 36, 59, "White window pane:", 3.2, (0, 0, 0), 'l', False, 0.0),
              ('text', 36, 64, "cut out, clear film behind", 3.2, (0, 0, 0), 'l', False, 0.0),
              ('badge', 17.5, 78, "3"),
              ('text', 36, 79.2, "The piece's number", 3.2, (0, 0, 0), 'l', False, 0.0)]
        st += check_bar(5, 88)
        st.append(('text', 60, 92, "Print at 100%", 3.0, (0, 0, 0), 'l', True, 0.0))
        paint_steps(p, st)
        p.end()


class CardKitDialog(QDialog):
    def __init__(self, viewport, tool):
        super().__init__(viewport)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.user_presets = load_presets()
        self.raw = []                    # the pieces as read from the model
        self.pieces = []                 # flattened
        self.flat_cache = {}
        self.entities = []
        self.sheets = []
        self.summary = None
        self._busy = False
        st = load_settings()
        lay = QVBoxLayout(self)

        self.info_box = QLabel(INFO_TEXT)
        self.info_box.setWordWrap(True)
        self.info_box.setVisible(False)
        lay.addWidget(self.info_box)

        row = QHBoxLayout()
        lay.addLayout(row)
        # left: the preview and the key
        self.left = QTabWidget()
        pv = QWidget()
        pvl = QVBoxLayout(pv)
        pvl.setContentsMargins(0, 0, 0, 0)
        self.preview = SheetPreview()
        pvl.addWidget(self.preview, 1)
        nav = QHBoxLayout()
        self.b_prev = QPushButton("◀")
        self.b_next = QPushButton("▶")
        for b in (self.b_prev, self.b_next):
            b.setFixedWidth(36)
        self.lbl_sheet = QLabel("No sheets yet")
        nav.addWidget(self.b_prev)
        nav.addWidget(self.lbl_sheet, 1)
        nav.addWidget(self.b_next)
        pvl.addLayout(nav)
        self.preview.on_pick = self.pick_in_list
        self.b_prev.clicked.connect(lambda: self.show_sheet(self.preview.index - 1))
        self.b_next.clicked.connect(lambda: self.show_sheet(self.preview.index + 1))
        self.left.addTab(pv, "Preview")
        self.left.addTab(KeyDrawing(), "Key")
        row.addWidget(self.left, 1)

        self.tabs = QTabWidget()
        row.addWidget(self.tabs, 1)

        # --- Start here
        ps = QWidget()
        fs = QVBoxLayout(ps)
        self.tabs.addTab(ps, "Start here")

        def step(text):
            l_ = QLabel(text)
            l_.setWordWrap(True)
            l_.setStyleSheet("font-weight: bold; margin-top: 8px;")
            fs.addWidget(l_)
        intro = QLabel("Make a card kit of your model: printed on paper, stuck on card, cut out and "
                       "glued up - no 3D printer needed.")
        intro.setWordWrap(True)
        fs.addWidget(intro)
        step("1  Select the building (or some walls) in the model, then:")
        self.b_read2 = QPushButton("Read the selection")
        fs.addWidget(self.b_read2)
        step("2  Pick the scale and the paper:")
        f2 = QFormLayout()
        self.cb_scale2 = QComboBox()
        self.cb_paper2 = QComboBox()
        f2.addRow("Scale", self.cb_scale2)
        f2.addRow("Paper", self.cb_paper2)
        fs.addLayout(f2)
        step("3  Colours and tabs (or leave them as they are):")
        b_parts = QPushButton("Go to the Parts page")
        fs.addWidget(b_parts)
        step("4  Make it:")
        self.b_make2 = QPushButton("Make card kit (PDF)...")
        fs.addWidget(self.b_make2)
        self.lbl_start = QLabel("")
        self.lbl_start.setWordWrap(True)
        self.lbl_start.setStyleSheet("color: gray;")
        fs.addWidget(self.lbl_start)
        fs.addStretch(1)

        # --- Parts
        pp = QWidget()
        fp = QVBoxLayout(pp)
        self.tabs.addTab(pp, "Parts")
        rp = QHBoxLayout()
        rp.addWidget(QLabel("Pieces are"))
        self.cb_depth = QComboBox()
        for lab, k in DEPTHS:
            self.cb_depth.addItem(lab, k)
        rp.addWidget(self.cb_depth, 1)
        fp.addLayout(rp)
        self.cb_noframe = QCheckBox("Leave out the frame (keep the fascia, barge and soffit boards)")
        self.cb_noframe.setChecked(bool(st.get('skip_frame', True)))
        fp.addWidget(self.cb_noframe)
        self.cb_covers = QCheckBox("Print slates, tiles and cladding on the piece under them")
        self.cb_covers.setChecked(bool(st.get('join_covers', True)))
        fp.addWidget(self.cb_covers)
        self.tbl = QTableWidget(0, 6)
        self.tbl.setHorizontalHeaderLabels(["Print", "No.", "Piece", "Material / colour", "Seen from", "Glue tabs"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        hh = self.tbl.horizontalHeader()
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for c in (0, 1, 4, 5):
            hh.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)   # the colour: narrow, drag to widen
        self.tbl.setColumnWidth(3, 150)
        fp.addWidget(self.tbl, 1)
        note = QLabel("Material: the piece's main colour changes to it (its windows and doors keep "
                      "theirs). Make your own on IngeTrazo's Materials tab and it's in the list. "
                      "Click a piece here to see it, or click a piece in the preview to find it here.")
        note.setWordWrap(True)
        note.setStyleSheet("color: gray;")
        fp.addWidget(note)
        rb = QHBoxLayout()
        b_all = QPushButton("Tick all")
        b_none = QPushButton("Untick all")
        self.b_paint = QPushButton("Paint the picked colours onto the model")
        rb.addWidget(b_all)
        rb.addWidget(b_none)
        rb.addStretch(1)
        rb.addWidget(self.b_paint)
        fp.addLayout(rb)
        b_all.clicked.connect(lambda: self.tick_all(True))
        b_none.clicked.connect(lambda: self.tick_all(False))
        self.b_paint.clicked.connect(self.paint_model)
        self.tbl.itemSelectionChanged.connect(self.piece_picked)

        # --- Scale & paper
        pa = QWidget()
        fa = QFormLayout(pa)
        self.tabs.addTab(pa, "Scale && paper")
        self.cb_scale = QComboBox()
        for lab, v in SCALES:
            self.cb_scale.addItem(lab, v)
            self.cb_scale2.addItem(lab, v)
        fa.addRow("Scale", self.cb_scale)
        self.cb_paper = QComboBox()
        for lab, _wh in PAPERS:
            self.cb_paper.addItem(lab, lab)
            self.cb_paper2.addItem(lab, lab)
        fa.addRow("Paper", self.cb_paper)
        self.cb_orient = QComboBox()
        for lab, k in ORIENTS:
            self.cb_orient.addItem(lab, k)
        fa.addRow("Sheet", self.cb_orient)
        self.sp_margin = self._spin(0, 30, 1, " mm")
        fa.addRow("Margin", self.sp_margin)
        self.sp_gap = self._spin(0, 30, 1, " mm")
        fa.addRow("Gap between pieces", self.sp_gap)
        self.ed_name = QLineEdit()
        self.ed_name.setPlaceholderText("(the name of the first group)")
        fa.addRow("Kit name", self.ed_name)
        self.cb_instr = QCheckBox("Instructions sheet first")
        fa.addRow(self.cb_instr)
        self.cb_pdf = QComboBox()
        for lab, k in PDF_MODES:
            self.cb_pdf.addItem(lab, k)
        fa.addRow("Pieces in the PDF", self.cb_pdf)
        self.cb_dpi = QComboBox()
        for lab, k in DPIS:
            self.cb_dpi.addItem(lab, k)
        fa.addRow("Picture quality", self.cb_dpi)

        self.lbl_summary = QLabel("")
        self.lbl_summary.setWordWrap(True)
        self.lbl_summary.setStyleSheet("color: gray;")
        fa.addRow(self.lbl_summary)

        # --- Tabs & look
        pt = QWidget()
        ft = QFormLayout(pt)
        self.tabs.addTab(pt, "Tabs && look")
        self.sp_tab = self._spin(2, 20, 1, " mm")
        ft.addRow("Tab width", self.sp_tab)
        self.cb_bottom = QCheckBox("Tabs along the bottom of the walls (to glue down)")
        ft.addRow(self.cb_bottom)
        self.cb_windows = QComboBox()
        for lab, k in WINDOW_MODES:
            self.cb_windows.addItem(lab, k)
        ft.addRow("Windows", self.cb_windows)
        self.cb_lines = QCheckBox("Lines between faces (bricks, tiles, planks show)")
        ft.addRow(self.cb_lines)
        self.cb_shading = QCheckBox("Shading")
        ft.addRow(self.cb_shading)
        self.cb_numbers = QCheckBox("Number on each piece")
        ft.addRow(self.cb_numbers)
        self.sp_line = self._spin(0.05, 1.0, 2, " mm")
        self.sp_line.setSingleStep(0.05)
        ft.addRow("Cut line", self.sp_line)
        tn = QLabel("Tabs are put where pieces meet, one per join, and say which piece they glue behind. "
                    "Change a piece's tabs on the Parts page (none, or all round).")
        tn.setWordWrap(True)
        tn.setStyleSheet("color: gray;")
        ft.addRow(tn)

        # --- presets
        prow = QHBoxLayout()
        prow.addWidget(QLabel("Preset:"))
        self.cb_preset = QComboBox()
        prow.addWidget(self.cb_preset, 1)
        b_up = QPushButton("▲")
        b_up.setToolTip("Moves the preset you have open up the list.")
        b_dn = QPushButton("▼")
        b_dn.setToolTip("Moves the preset you have open down the list.")
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
        for b in (b_save, b_saveas, b_del, b_dir):
            prow.addWidget(b)
        lay.addLayout(prow)
        b_save.clicked.connect(self.save_preset)
        b_saveas.clicked.connect(lambda: self.save_preset_as())
        b_del.clicked.connect(self.delete_preset)
        b_dir.clicked.connect(self.open_folder)

        # --- buttons
        brow = QHBoxLayout()
        self.b_read = QPushButton("Read the selection")
        self.b_make = QPushButton("Make card kit (PDF)...")
        self.b_make.setDefault(True)
        brow.addWidget(self.b_read)
        brow.addWidget(self.b_make)
        brow.addWidget(QLabel("then open it in"))
        self.cb_open = QComboBox()
        for lab, k in OPEN_WITH:
            self.cb_open.addItem(lab, k)
        self._set_combo(self.cb_open, st.get('open_with', 'ask'))
        self.cb_open.currentIndexChanged.connect(lambda *_: save_settings(open_with=self.cb_open.currentData()))
        brow.addWidget(self.cb_open)
        self.b_openwith = QPushButton("Open PDF with...")
        self.b_openwith.clicked.connect(self.open_last_with)
        brow.addWidget(self.b_openwith)
        self.last_pdf = st.get('last_pdf')
        brow.addStretch(1)
        self.b_info = QPushButton("Info")
        self.b_info.setCheckable(True)
        self.b_info.setToolTip("Shows how to use it.")
        self.b_info.toggled.connect(self.info_box.setVisible)
        brow.addWidget(self.b_info)
        self.cb_lasttab = QCheckBox("Open at the last page used")
        self.cb_lasttab.setChecked(bool(st.get('remember_tab', True)))
        brow.addWidget(self.cb_lasttab)
        b_close = QPushButton("Close")
        brow.addWidget(b_close)
        lay.addLayout(brow)
        self.lbl_report = QLabel("")
        self.lbl_report.setWordWrap(True)
        lay.addWidget(self.lbl_report)

        for b in (self.b_read, self.b_read2):
            b.clicked.connect(self.read_selection)
        for b in (self.b_make, self.b_make2):
            b.clicked.connect(self.make_pdf)
        b_parts.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        b_close.clicked.connect(self.close)

        # values in, then watch them
        self.choices = {}
        self.centre = None
        self.page = (210.0, 297.0)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.relayout)
        if not st.get('parts_reset_19'):
            # before 1.8 the mouse wheel could change a piece's drop-downs while scrolling the list
            # (a wall turned to 'Other side', a pot given a material): start those afresh, once
            st['parts'] = {}
            save_settings(parts={}, parts_reset_19=True)
        if not st.get('sharp_done'):
            # 1.2 saved 'As a picture' as everyone's setting: move to Sharp once (it can be set back)
            st['pdf_mode'] = 'sharp'
            save_settings(pdf_mode='sharp', sharp_done=True)
        self.set_values(dict(DEFAULTS, **{k: st[k] for k in DEFAULTS if k in st}))
        for w in (self.cb_scale, self.cb_paper, self.cb_orient, self.cb_windows, self.cb_dpi):
            w.currentIndexChanged.connect(self.changed)
        self.cb_pdf.currentIndexChanged.connect(
            lambda *_: (self.cb_dpi.setEnabled(self.cb_pdf.currentData() == 'picture'), self.changed()))
        for w in (self.sp_margin, self.sp_gap, self.sp_tab, self.sp_line):
            w.valueChanged.connect(self.changed)
        for w in (self.cb_bottom, self.cb_lines, self.cb_shading, self.cb_numbers, self.cb_instr):
            w.toggled.connect(self.changed)
        self.ed_name.textChanged.connect(self.changed)
        self.cb_depth.currentIndexChanged.connect(self.depth_changed)
        self.cb_noframe.toggled.connect(self.noframe_changed)
        self.cb_covers.toggled.connect(self.covers_changed)
        self._mirror(self.cb_scale, self.cb_scale2)
        self._mirror(self.cb_paper, self.cb_paper2)
        self.cb_preset.currentIndexChanged.connect(self.apply_preset)
        self.refresh_presets(select=st.get('last_preset'))
        if self.cb_lasttab.isChecked():
            try:
                self.tabs.setCurrentIndex(int(st.get('tab', 0)))
            except Exception:
                pass
        self.tabs.currentChanged.connect(lambda i: save_settings(tab=int(i)))
        self.cb_lasttab.toggled.connect(lambda on: save_settings(remember_tab=bool(on)))
        self.resize(1050, 680)

    # ---- small helpers
    def _spin(self, lo, hi, dec, suffix):
        s = QDoubleSpinBox()
        s.setRange(lo, hi)
        s.setDecimals(dec)
        s.setSuffix(suffix)
        return s

    def _mirror(self, a, b):
        def ab(i):
            b.blockSignals(True)
            b.setCurrentIndex(i)
            b.blockSignals(False)

        def ba(i):
            a.setCurrentIndex(i)
        a.currentIndexChanged.connect(ab)
        b.currentIndexChanged.connect(ba)
        ab(a.currentIndex())

    @staticmethod
    def _set_combo(cb, value):
        for i in range(cb.count()):
            d = cb.itemData(i)
            if d == value or (isinstance(d, float) and isinstance(value, (int, float)) and abs(d - value) < 1e-6):
                cb.setCurrentIndex(i)
                return

    def scene(self):
        return getattr(self.viewport, 'scene', None)

    def materials(self):
        return getattr(self.scene(), 'materials', None)

    def values(self):
        return dict(scale=float(self.cb_scale.currentData()), paper=self.cb_paper.currentData(),
                    orient=self.cb_orient.currentData(), margin=self.sp_margin.value(), gap=self.sp_gap.value(),
                    tab_w=self.sp_tab.value(), bottom_tabs=self.cb_bottom.isChecked(),
                    windows=self.cb_windows.currentData(), lines=self.cb_lines.isChecked(),
                    shading=self.cb_shading.isChecked(), numbers=self.cb_numbers.isChecked(),
                    instructions=self.cb_instr.isChecked(), depth=int(self.cb_depth.currentData() or 0),
                    line_w=self.sp_line.value(), kit_name=self.ed_name.text().strip(),
                    pdf_mode=self.cb_pdf.currentData(), dpi=int(self.cb_dpi.currentData() or 300))

    def set_values(self, d):
        self._busy = True
        try:
            self._set_combo(self.cb_scale, float(d.get('scale', 76.2)))
            self._set_combo(self.cb_paper, d.get('paper', "A4"))
            self._set_combo(self.cb_orient, d.get('orient', 'best'))
            self._set_combo(self.cb_windows, d.get('windows', 'cut'))
            self._set_combo(self.cb_depth, int(d.get('depth', 0)))
            self._set_combo(self.cb_pdf, 'picture' if d.get('pdf_mode') == 'picture' else 'sharp')
            self._set_combo(self.cb_dpi, int(d.get('dpi', 300)))
            self.cb_dpi.setEnabled(self.cb_pdf.currentData() == 'picture')
            self.sp_margin.setValue(float(d.get('margin', 10.0)))
            self.sp_gap.setValue(float(d.get('gap', 4.0)))
            self.sp_tab.setValue(float(d.get('tab_w', 6.0)))
            self.sp_line.setValue(float(d.get('line_w', 0.25)))
            self.cb_bottom.setChecked(bool(d.get('bottom_tabs', True)))
            self.cb_lines.setChecked(bool(d.get('lines', True)))
            self.cb_shading.setChecked(bool(d.get('shading', True)))
            self.cb_numbers.setChecked(bool(d.get('numbers', True)))
            self.cb_instr.setChecked(bool(d.get('instructions', True)))
            if 'kit_name' in d:
                self.ed_name.setText(d.get('kit_name') or "")
        finally:
            self._busy = False
        self.changed()

    def changed(self, *_):
        if self._busy:
            return
        save_settings(**self.values())
        self._timer.start(250)

    def report(self, text, bad=False):
        self.lbl_report.setStyleSheet("color: %s;" % ("#b71c1c" if bad else "#2e7d32"))
        self.lbl_report.setText(text)

    # ---- reading the model
    def read_selection(self):
        scene = self.scene()
        ents = list(getattr(scene, 'selection', None) or [])
        if not ents:
            QMessageBox.information(self, PLUGIN_NAME, "Select the building (or the walls and roof you want) "
                                    "in the model first, then click 'Read the selection'.")
            return
        self.entities = ents
        self._read()

    def depth_changed(self, *_):
        if self._busy:
            return
        save_settings(depth=int(self.cb_depth.currentData() or 0))
        if self.entities:
            self._read()

    def covers_changed(self, on):
        save_settings(join_covers=bool(on))
        if self.entities:
            self._read()

    def noframe_changed(self, on):
        save_settings(skip_frame=bool(on))
        if self.entities:
            self._read()

    def _read(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.raw = read_pieces(self.entities, int(self.cb_depth.currentData() or 0),
                                   skip_frame=self.cb_noframe.isChecked())
            if self.cb_covers.isChecked():
                self.raw = join_coverings(self.raw)
            self.flat_cache = {}
            pts = [p for r in self.raw for fr in r['faces'] for p in fr['outer']]
            if pts:
                lo = tuple(min(p[k] for p in pts) for k in range(3))
                hi = tuple(max(p[k] for p in pts) for k in range(3))
                self.centre = v_mul(v_add(lo, hi), 0.5)
            else:
                self.centre = None
            if not self.ed_name.text().strip():
                try:
                    self.ed_name.setPlaceholderText(str(getattr(self.entities[0], 'name', '') or "Card kit"))
                except Exception:
                    pass
            self.choices = {}
            remembered = load_settings().get('parts', {})
            for i, r in enumerate(self.raw):
                c = dict(print=True, mat=None, side='front', tabs='auto')
                c.update({k: v for k, v in (remembered.get(r['name']) or {}).items() if k in c})
                self.choices[i] = c
            self.flatten_all()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.report("Couldn't read the selection: %s" % e, bad=True)
            return
        finally:
            QApplication.restoreOverrideCursor()
        self.fill_table()
        self.relayout()
        bad = [r['name'] for r, p in zip(self.raw, self.pieces) if p is None]
        msg = "Read %d piece(s)." % len([p for p in self.pieces if p is not None])
        if bad:
            msg += " Left out (nothing to see from outside): %s" % ", ".join(bad[:6])
        self.report(msg)

    def flatten_all(self):
        mats = self.materials()
        out = []
        for i, r in enumerate(self.raw):
            side = self.choices.get(i, {}).get('side', 'front')
            key = (i, side)
            if key not in self.flat_cache:
                self.flat_cache[key] = flatten_piece(r, self.centre, flip=(side == 'back'),
                                                     materials=mats, outline_fn=qt_outline)
            out.append(self.flat_cache[key])
        self.pieces = out
        ok = [p for p in out if p is not None]
        find_joins(ok)

    def kit_parts(self):
        """The pieces that could be drawn, and the choices for them, numbered 1, 2, 3..."""
        idx = [i for i, p in enumerate(self.pieces) if p is not None]
        pieces = [self.pieces[i] for i in idx]
        mats = self.materials()
        ch = {}
        for k, i in enumerate(idx):
            c = dict(self.choices.get(i, {}))
            name = c.get('mat')
            if name and name != '__white__':
                mat = _mat_get(mats, name)
                if mat is not None:
                    rgb, _op, tex = material_look(mat)
                    c['look'] = (rgb, tex)
            ch[k] = c
        return pieces, ch, idx

    # ---- the parts table
    def fill_table(self):
        self.tbl.blockSignals(True)
        self.tbl.setRowCount(0)
        mats = self.materials()
        names = []
        try:
            names = sorted(str(n) for n in (mats.keys() if hasattr(mats, 'keys') else []))
        except Exception:
            names = []
        f = 1.0 / float(self.cb_scale.currentData())
        n = 0
        for i, pc in enumerate(self.pieces):
            if pc is None:
                continue
            n += 1
            r = self.tbl.rowCount()
            self.tbl.insertRow(r)
            c = self.choices[i]
            cb = QCheckBox()
            cb.setChecked(bool(c.get('print', True)))
            cb.toggled.connect(lambda on, i=i: self.set_choice(i, 'print', bool(on)))
            w = QWidget()
            hl = QHBoxLayout(w)
            hl.setContentsMargins(6, 0, 0, 0)
            hl.addWidget(cb)
            self.tbl.setCellWidget(r, 0, w)
            it = QTableWidgetItem(str(n))
            it.setData(Qt.ItemDataRole.UserRole, i)
            self.tbl.setItem(r, 1, it)
            self.tbl.setItem(r, 2, QTableWidgetItem("%s   (%.0f x %.0f mm)" % (pc['name'], pc['w'] * f, pc['h'] * f)))
            for col in (1, 2):
                self.tbl.item(r, col).setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            cm = ListCombo()
            try:
                cm.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
                cm.setMinimumContentsLength(8)
                cm.view().setMinimumWidth(260)        # the list itself opens wide enough to read
            except Exception:
                pass
            main = pc.get('main')
            cm.addItem(_swatch(tuple(x / 255.0 for x in main) if main else DEFAULT_FACE), "As modelled", None)
            cm.addItem(_swatch((1, 1, 1)), "Plain white (colour it yourself)", '__white__')
            for nm in names:
                mat = _mat_get(mats, nm)
                rgb = material_look(mat)[0] if mat is not None else DEFAULT_FACE
                cm.addItem(_swatch(rgb), nm, nm)
            self._set_combo(cm, c.get('mat'))
            cm.currentIndexChanged.connect(lambda _k, i=i, cm=cm: self.set_choice(i, 'mat', cm.currentData()))
            self.tbl.setCellWidget(r, 3, cm)
            cs = ListCombo()
            for lab, k in SIDE_MODES:
                cs.addItem(lab, k)
            self._set_combo(cs, c.get('side', 'front'))
            cs.currentIndexChanged.connect(lambda _k, i=i, cs=cs: self.set_choice(i, 'side', cs.currentData()))
            self.tbl.setCellWidget(r, 4, cs)
            ct = ListCombo()
            for lab, k in TAB_MODES:
                ct.addItem(lab, k)
            self._set_combo(ct, c.get('tabs', 'auto'))
            ct.currentIndexChanged.connect(lambda _k, i=i, ct=ct: self.set_choice(i, 'tabs', ct.currentData()))
            self.tbl.setCellWidget(r, 5, ct)
        self.tbl.blockSignals(False)

    def set_choice(self, i, key, value):
        self.choices.setdefault(i, {})[key] = value
        if key == 'side':
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                self.flatten_all()
            finally:
                QApplication.restoreOverrideCursor()
        # remember it by the piece's name for next time
        st = load_settings()
        parts = st.get('parts', {}) if isinstance(st.get('parts'), dict) else {}
        name = self.raw[i]['name']
        parts[name] = {k: self.choices[i].get(k) for k in ('print', 'mat', 'side', 'tabs')}
        if len(parts) > 400:
            parts = dict(list(parts.items())[-400:])
        save_settings(parts=parts)
        self._timer.start(200)

    def tick_all(self, on):
        for r in range(self.tbl.rowCount()):
            w = self.tbl.cellWidget(r, 0)
            cb = w.findChild(QCheckBox) if w is not None else None
            if cb is not None:
                cb.setChecked(on)

    def piece_picked(self):
        rows = sorted({ix.row() for ix in self.tbl.selectionModel().selectedRows()})
        if not rows or not self.summary:
            return
        it = self.tbl.item(rows[0], 1)
        i = it.data(Qt.ItemDataRole.UserRole) if it else None
        self.preview.lit = i
        sheet = self.summary.get('sheet_of', {}).get(i)
        if sheet is not None:
            self.left.setCurrentIndex(0)
            if sheet != self.preview.index:
                self.show_sheet(sheet)
        self.preview.update()

    def pick_in_list(self, i):
        """A piece clicked in the preview: picked in the Parts list, ready for its colour."""
        self.tabs.setCurrentIndex(1)
        for r in range(self.tbl.rowCount()):
            it = self.tbl.item(r, 1)
            if it is not None and it.data(Qt.ItemDataRole.UserRole) == i:
                self.tbl.selectRow(r)
                self.tbl.scrollToItem(it, QAbstractItemView.ScrollHint.PositionAtCenter)
                break
        self.preview.lit = i
        self.preview.update()

    # ---- laying out
    def relayout(self):
        if not self.pieces or not any(p is not None for p in self.pieces):
            self.preview.set_sheets(210, 297, [])
            self.lbl_sheet.setText("No sheets yet")
            return
        v = self.values()
        if not v['kit_name']:
            v['kit_name'] = self.ed_name.placeholderText().strip("()") or "Card kit"
        pieces, ch, idx = self.kit_parts()
        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            pw, ph, sheets, summ = layout_kit(pieces, v, ch, self.materials())
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.report("Couldn't lay the kit out: %s" % e, bad=True)
            return
        finally:
            QApplication.restoreOverrideCursor()
        # which sheet each piece is on (for clicking a piece in the list)
        summ['sheet_of'] = {idx[k]: s for k, s in summ.get('sheet_of', {}).items()}
        self.preview.rects = {sh: [(idx[k], *r) for k, *r in lst] for sh, lst in summ.get('rects', {}).items()}
        self.sheets, self.summary, self.page = sheets, summ, (pw, ph)
        self.preview.set_sheets(pw, ph, sheets)
        self.show_sheet(self.preview.index)
        txt = "%d sheet(s) of %s, %s, %d piece(s)." % (summ['sheets'], summ['paper'], summ['orient'], summ['pieces'])
        if summ['tiled']:
            txt += " Piece(s) %s are too big for the paper and are split across sheets." % \
                   ", ".join(str(t) for t in summ['tiled'])
        self.lbl_summary.setText(txt)
        self.lbl_start.setText(txt)

    def show_sheet(self, k):
        self.preview.go(k)
        n = len(self.preview.sheets)
        self.lbl_sheet.setText("Sheet %d of %d" % (self.preview.index + 1, n) if n else "No sheets yet")

    # ---- making the PDF
    def make_pdf(self):
        if not self.sheets:
            self.read_selection()
            if not self.sheets:
                return
        v = self.values()
        name = v['kit_name'] or self.ed_name.placeholderText().strip("()") or "Card kit"
        st = load_settings()
        folder = st.get('last_dir') or KIT_DIR
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception:
            pass
        path, _f = QFileDialog.getSaveFileName(self, "Save the card kit", os.path.join(folder, _safe_name(name) + ".pdf"),
                                               "PDF (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        save_settings(last_dir=os.path.dirname(path))
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            pw, ph = self.page
            dpi = v['dpi'] if v.get('pdf_mode', 'picture') == 'picture' else None
            write_pdf(path, pw, ph, self.sheets, self.summary['paper'], title=name, dpi=dpi)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, PLUGIN_NAME, "Could not save the PDF:\n%s" % e)
            return
        QApplication.restoreOverrideCursor()
        self.report("Saved %s - %d sheet(s). Print it at 100%% (Actual size)." % (path, len(self.sheets)))
        self.last_pdf = path
        save_settings(last_pdf=path)
        how = self.cb_open.currentData()
        if how == 'ask':
            self.pick_and_open(path)
        else:
            open_pdf(path, how)

    def pick_and_open(self, path):
        """A box in the middle of the Card Kit window: open the kit in Edge, Chrome, the usual
        program, or show it in its folder."""
        box = QMessageBox(self)
        box.setWindowTitle(PLUGIN_NAME)
        box.setIcon(QMessageBox.Icon.Question)
        box.setText("<b>Your card kit is saved.</b><br>Open it in:")
        box.setInformativeText(os.path.basename(path) + "\n\nPrint it at 100% (\"Actual size\").")
        role = QMessageBox.ButtonRole.ActionRole
        picks = {}
        for lab, k in PICK_FROM:
            b = box.addButton(lab, role)
            b.setMinimumHeight(34)
            b.setStyleSheet("QPushButton { font-weight: bold; padding: 4px 14px; }")
            picks[b] = k
        later = box.addButton("Not now", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(list(picks)[0])
        box.setEscapeButton(later)
        box.exec()
        k = picks.get(box.clickedButton())
        if k:
            open_pdf(path, k)

    def open_last_with(self):
        """Opens the last kit saved, asking which program to use."""
        path = getattr(self, 'last_pdf', None) or load_settings().get('last_pdf')
        if not path or not os.path.isfile(os.path.normpath(path)):
            # nothing made yet: make it now, then ask which program
            keep = self.cb_open.currentIndex()
            self._set_combo(self.cb_open, 'ask')
            try:
                self.make_pdf()
            finally:
                self.cb_open.setCurrentIndex(keep)
            return
        self.pick_and_open(os.path.normpath(path))

    # ---- painting the picked materials onto the model
    def paint_model(self):
        mats = self.materials()
        todo = []
        for i, pc in enumerate(self.pieces):
            if pc is None:
                continue
            name = self.choices.get(i, {}).get('mat')
            if not name or name == '__white__':
                continue
            mat = _mat_get(mats, name)
            if mat is None or pc.get('main') is None:
                continue
            faces = [fr for fr in self.raw[i]['faces']
                     if colour_key(face_look(fr['attrs'], mats)[0]) == pc['main']
                     and not face_look(fr['attrs'], mats)[1]]
            todo.append((mat, faces))
        if not todo:
            QMessageBox.information(self, PLUGIN_NAME, "Pick a material for a piece on the Parts page first "
                                    "(not 'As modelled' or 'Plain white').")
            return
        meshes = []
        for _m, faces in todo:
            for fr in faces:
                m = fr.get('mesh')
                if m is not None and all(m is not x for x in meshes):
                    meshes.append(m)

        def mutate(_scene):
            for mat, faces in todo:
                try:
                    paint = dict(mat.face_attrs())
                except Exception:
                    paint = {'color': material_look(mat)[0]}
                for fr in faces:
                    f = fr['face']
                    a = dict(getattr(f, 'attrs', None) or {})
                    for k in ('texture', 'color', 'mat', 'opacity'):
                        a.pop(k, None)
                    a.update(paint)
                    f.attrs = a
        try:
            self.viewport.history.execute(_paint_command(mutate, meshes))
        except Exception as e:
            QMessageBox.warning(self, PLUGIN_NAME, "Could not paint the model:\n%s" % e)
            return
        try:
            self.viewport.notify_scene_changed()
        except Exception:
            try:
                self.viewport.update()
            except Exception:
                pass
        n = sum(len(f) for _m, f in todo)
        self.report("Painted %d face(s) on %d piece(s). Ctrl+Z undoes it." % (n, len(todo)))
        # the picked materials are now the model's own: read it again so the list says so
        for i in self.choices:
            if self.choices[i].get('mat') not in (None, '__white__'):
                self.choices[i]['mat'] = None
        st = load_settings()
        parts = st.get('parts', {}) if isinstance(st.get('parts'), dict) else {}
        for r in self.raw:
            if r['name'] in parts:
                parts[r['name']]['mat'] = None
        save_settings(parts=parts)
        if self.entities:
            self._read()

    # ---- presets
    def preset_order(self):
        names = list(BUILTIN_PRESETS) + sorted(n for n in self.user_presets if n not in BUILTIN_PRESETS)
        order = [n for n in load_settings().get('preset_order', []) if n in names]
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
            save_settings(preset_order=order)
            self.refresh_presets(select=name)

    def apply_preset(self, *_):
        name = self.cb_preset.currentData()
        save_settings(last_preset=name or None)
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
        d.pop('kit_name', None)
        self.set_values(d)

    def save_preset(self):
        name = self.cb_preset.currentData()
        if name and name in self.user_presets and name not in BUILTIN_PRESETS:
            if self.save_preset_as(quiet_name=name):
                self.btn_preset_save.setText("Saved")
                QTimer.singleShot(1500, lambda: self.btn_preset_save.setText("Save"))
        else:
            self.save_preset_as(prefill=(name + " (my copy)") if name else "")

    def save_preset_as(self, prefill="", quiet_name=None):
        if quiet_name:
            name, ok = quiet_name, True
        else:
            name, ok = QInputDialog.getText(self, "Save preset", "Preset name:", QLineEdit.EchoMode.Normal, prefill)
        name = (name or "").strip()
        if not ok or not name:
            return False
        if name in BUILTIN_PRESETS:
            QMessageBox.warning(self, PLUGIN_NAME, "That name is used by a built-in preset.")
            return False
        if not quiet_name and name in self.user_presets and QMessageBox.question(
                self, PLUGIN_NAME, "Preset '%s' already exists. Overwrite it?" % name) != QMessageBox.StandardButton.Yes:
            return False
        try:
            save_preset_file(name, self.values())
        except Exception as e:
            QMessageBox.warning(self, PLUGIN_NAME, "Could not save the preset:\n%s" % e)
            return False
        self.user_presets = load_presets()
        self.refresh_presets(select=name)
        save_settings(last_preset=name)
        return True

    def delete_preset(self):
        name = self.cb_preset.currentData()
        if not name or name not in self.user_presets or name in BUILTIN_PRESETS:
            QMessageBox.information(self, PLUGIN_NAME, "Pick one of your own presets to delete "
                                    "(built-in presets can't be deleted).")
            return
        if QMessageBox.question(self, PLUGIN_NAME, "Delete preset '%s'?" % name) != QMessageBox.StandardButton.Yes:
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


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
class CardKitTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+Shift+K"
    description = ("Makes a printable card kit of the selected model: each piece drawn flat at true scale "
                   "in its colours, with glue tabs, laid out on A4 or A3 sheets as a PDF.")
    _dialog = None

    def on_activate(self, viewport):
        dlg = CardKitTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.raise_()
                    dlg.activateWindow()
                    return
            except Exception:
                pass
        dlg = CardKitDialog(viewport, self)
        CardKitTool._dialog = dlg

        def closed(*_):
            CardKitTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()
        # read what's already selected, so the preview is there straight away
        try:
            if list(getattr(getattr(viewport, 'scene', None), 'selection', None) or []):
                QTimer.singleShot(50, dlg.read_selection)
        except Exception:
            pass

    def on_deactivate(self, viewport):
        pass


def run(viewport=None):
    CardKitTool().on_activate(viewport)
