# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Centre Finder for IngeTrazo
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
3D Centre Finder - finds the centre of a face, an edge or an object in IngeTrazo
Select a face (or several), an edge, or an object (group), and the window shows its centre
and size. Then:
  * Mark the centre - a guide point there (like the Tape Measure leaves) to snap to.
  * Centre lines - guide lines through the centre: across the face both ways, or along
    X, Y and Z through an object.
  * Move to a centre - take one centre as the target, select another object, and move it so
    its centre lands there (a door central on a wall, a vent on a roof, a chimney on a stack).
Guides are not geometry: delete them with Edit > Delete Guides. Everything can be undone.
"""

import os
import json
import math
from tools.base import Tool
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton, QCheckBox, QGroupBox,
    QMessageBox, QApplication
)

PLUGIN_NAME = "3D Centre Finder"
VERSION = "1"
MM = 1000.0                       # IngeTrazo works in metres; the window shows mm


# ---------------------------------------------------------------------------
# Reading the selection
# ---------------------------------------------------------------------------
def vertex_to_vector3d(v):
    """The vertex position as a QVector3D, or None if it can't be read."""
    if isinstance(v, QVector3D):
        return QVector3D(v.x(), v.y(), v.z())
    for get in (lambda: (v.x(), v.y(), v.z()),
                lambda: (v.x, v.y, v.z),
                lambda: (v[0], v[1], v[2]),
                lambda: (v.pos.x(), v.pos.y(), v.pos.z()),
                lambda: (v.position.x(), v.position.y(), v.position.z())):
        try:
            x, y, z = get()
            return QVector3D(float(x), float(y), float(z))
        except Exception:
            pass
    return None


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


def _is_group(e):
    return (not _is_face(e)) and getattr(e, 'mesh', None) is not None


def _edge_ends(e):
    """An edge's two ends as QVector3D, or None if it isn't an edge."""
    for a, b in (('v1', 'v2'), ('a', 'b'), ('start', 'end')):
        p, q = getattr(e, a, None), getattr(e, b, None)
        if p is not None and q is not None:
            p, q = vertex_to_vector3d(p), vertex_to_vector3d(q)
            if p is not None and q is not None:
                return p, q
    vs = _items(getattr(e, 'vertices', None))
    if len(vs) == 2:
        p, q = vertex_to_vector3d(vs[0]), vertex_to_vector3d(vs[1])
        if p is not None and q is not None:
            return p, q
    return None


def _meshes_of(e, out, seen):
    m = getattr(e, 'mesh', None)
    if m is not None and id(m) not in seen:
        seen.add(id(m))
        out.append(m)
    for ch in _items(getattr(e, 'groups', None)) + _items(getattr(e, 'children', None)):
        if getattr(ch, 'mesh', None) is not None:
            _meshes_of(ch, out, seen)


def _face_loops(f):
    """A face's outline and holes as lists of (x, y, z), or None."""
    outer = [vertex_to_vector3d(v) for v in _items(getattr(f, 'vertices', None))]
    if len(outer) < 3 or any(q is None for q in outer):
        return None
    holes = []
    for h in _items(getattr(f, 'holes', None)):
        hl = [vertex_to_vector3d(v) for v in _items(h)]
        if len(hl) >= 3 and all(q is not None for q in hl):
            holes.append([(q.x(), q.y(), q.z()) for q in hl])
    return [(q.x(), q.y(), q.z()) for q in outer], holes


def group_points(g):
    """Every corner of a group (and the groups inside it) where it really is in the model -
    a moved or turned component through its placement."""
    m = None
    try:
        from core.group import world_mesh
        m = world_mesh(g)
    except Exception:
        m = None
    meshes = [m] if m is not None else []
    if not meshes:
        _meshes_of(g, meshes, set())
    pts = []
    for m_ in meshes:
        for v in _items(getattr(m_, 'vertices', None)):
            q = vertex_to_vector3d(v)
            if q is not None:
                pts.append((q.x(), q.y(), q.z()))
        if not _items(getattr(m_, 'vertices', None)):
            for f in _items(getattr(m_, 'faces', None)):
                lp = _face_loops(f)
                if lp:
                    pts += lp[0]
    return pts


# ---------------------------------------------------------------------------
# Sums (no Qt in them, so they can be checked on their own)
# ---------------------------------------------------------------------------
def _sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def _add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def _mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def _dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def _len(a): return math.sqrt(_dot(a, a))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(a):
    L = _len(a)
    return _mul(a, 1.0 / L) if L > 1e-15 else None


def newell(loop):
    nx = ny = nz = 0.0
    for i in range(len(loop)):
        a, b = loop[i], loop[(i + 1) % len(loop)]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    return (nx, ny, nz)


def loop_area_centre(loop, n):
    """(area, centre) of a flat loop, n its unit normal. Works for L shapes and other
    outlines that aren't convex: fan triangles count plus or minus."""
    p0 = loop[0]
    A, C = 0.0, (0.0, 0.0, 0.0)
    for i in range(1, len(loop) - 1):
        a, b = loop[i], loop[i + 1]
        s = _dot(_cross(_sub(a, p0), _sub(b, p0)), n) / 2.0
        A += s
        C = _add(C, _mul(_add(_add(p0, a), b), s / 3.0))
    if abs(A) < 1e-18:
        return 0.0, _mul(_add(_add(loop[0], loop[len(loop) // 3]), loop[2 * len(loop) // 3]), 1 / 3.0)
    return abs(A), _mul(C, 1.0 / A)


def face_area_centre(outer, holes):
    """(area, centre, unit normal) of a face with holes."""
    n = _unit(newell(outer)) or (0.0, 0.0, 1.0)
    A, c = loop_area_centre(outer, n)
    S = _mul(c, A)
    for h in holes:
        a, ch = loop_area_centre(h, n)
        A -= a
        S = _sub(S, _mul(ch, a))
    if A <= 1e-18:
        return 0.0, c, n
    return A, _mul(S, 1.0 / A), n


def bbox(pts):
    lo = tuple(min(p[k] for p in pts) for k in range(3))
    hi = tuple(max(p[k] for p in pts) for k in range(3))
    return lo, hi


def face_axes(outer, n):
    """Two directions across a face, square to each other: along its longest edge, and across."""
    best, u = -1.0, None
    for i in range(len(outer)):
        e = _sub(outer[(i + 1) % len(outer)], outer[i])
        e = _sub(e, _mul(n, _dot(e, n)))
        L = _len(e)
        if L > best:
            best, u = L, e
    u = _unit(u) if u else None
    if u is None:
        u = _unit(_cross(n, (0.0, 0.0, 1.0))) or (1.0, 0.0, 0.0)
    return u, _unit(_cross(n, u)) or (0.0, 1.0, 0.0)


def analyse(entities):
    """What's selected, and its centre: a dict with kind, label, centre, lo, hi, and for faces
    the normal, area and the two directions across it; for edges the length and direction."""
    faces, edges, groups = [], [], []
    for e in entities:
        if _is_group(e):
            groups.append(e)
        elif _is_face(e):
            faces.append(e)
        elif _edge_ends(e):
            edges.append(e)
    if groups:
        pts = []
        for g in groups:
            pts += group_points(g)
        for f in faces:
            lp = _face_loops(f)
            if lp:
                pts += lp[0]
        if not pts:
            return None
        lo, hi = bbox(pts)
        names = [str(getattr(g, 'name', '') or 'group') for g in groups]
        label = names[0] if len(names) == 1 else "%d objects" % len(names)
        return dict(kind='object', label=label, centre=_mul(_add(lo, hi), 0.5), lo=lo, hi=hi, groups=groups)
    if faces:
        A, S, N, pts, first = 0.0, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), [], None
        for f in faces:
            lp = _face_loops(f)
            if not lp:
                continue
            a, c, n = face_area_centre(*lp)
            A += a
            S = _add(S, _mul(c, a))
            N = _add(N, _mul(n, a))
            pts += lp[0]
            if first is None:
                first = lp[0]
        if not pts:
            return None
        lo, hi = bbox(pts)
        centre = _mul(S, 1.0 / A) if A > 1e-18 else _mul(_add(lo, hi), 0.5)
        n = _unit(N) or (0.0, 0.0, 1.0)
        u, v = face_axes(first, n)
        flat = all(abs(_dot(_sub(p, centre), n)) < 1e-6 for p in pts)
        label = "a face" if len(faces) == 1 else "%d faces" % len(faces)
        return dict(kind='face', label=label, centre=centre, lo=lo, hi=hi, normal=n if flat else None,
                    area=A, u=u, v=v)
    if edges:
        L, S, pts, d0 = 0.0, (0.0, 0.0, 0.0), [], None
        for e in edges:
            p, q = _edge_ends(e)
            p, q = (p.x(), p.y(), p.z()), (q.x(), q.y(), q.z())
            l = _len(_sub(q, p))
            L += l
            S = _add(S, _mul(_add(p, q), l / 2.0))
            pts += [p, q]
            if d0 is None:
                d0 = _unit(_sub(q, p))
        lo, hi = bbox(pts)
        centre = _mul(S, 1.0 / L) if L > 1e-15 else _mul(_add(lo, hi), 0.5)
        label = "an edge" if len(edges) == 1 else "%d edges" % len(edges)
        return dict(kind='edge', label=label, centre=centre, lo=lo, hi=hi, length=L, dir=d0 or (1.0, 0.0, 0.0))
    return None


def centre_lines(info):
    """The guide lines for a centre: [(point, direction)]."""
    c = info['centre']
    if info['kind'] == 'face':
        return [(c, info['u']), (c, info['v'])]
    if info['kind'] == 'edge':
        d = info['dir']
        across = _unit(_cross(d, (0.0, 0.0, 1.0))) or (1.0, 0.0, 0.0)
        up = _unit(_cross(across, d)) or (0.0, 0.0, 1.0)
        return [(c, across), (c, up)]
    return [(c, (1.0, 0.0, 0.0)), (c, (0.0, 1.0, 0.0)), (c, (0.0, 0.0, 1.0))]


def move_delta(target, moving_centre, axes=(True, True, True), along_face=None, sit=None):
    """How far to move so moving_centre lands on target: only along the ticked axes, or,
    sliding along a face (along_face = its normal), keeping the distance from it.
    sit = (target's top, moving thing's bottom): stand it on top instead, whatever Z says."""
    d = _sub(target, moving_centre)
    if along_face is not None:
        d = _sub(d, _mul(along_face, _dot(d, along_face)))
    d = tuple(d[k] if axes[k] else 0.0 for k in range(3))
    if sit is not None:
        d = (d[0], d[1], sit[0] - sit[1])
    return d


def fmt_mm(x):
    return ("%.1f" % (x * MM)).replace("-0.0", "0.0")


# ---------------------------------------------------------------------------
# The window
# ---------------------------------------------------------------------------


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
EDDY_TIPS_END = None


class CentreDialog(QDialog):
    def __init__(self, viewport, tool):
        super().__init__(viewport)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.info = None
        self.target = None
        self._sel_key = None
        lay = QVBoxLayout(self)

        intro = QLabel("Select a face, an edge or an object. Its centre shows here.")
        intro.setWordWrap(True)
        lay.addWidget(intro)
        form = QFormLayout()
        self.lbl_what = QLabel("-")
        self.lbl_what.setToolTip("What's selected now: faces, edges or objects (groups).")
        form.addRow("Selected:", self.lbl_what)
        self.lbl_centre = QLabel("-")
        self.lbl_centre.setToolTip("The centre in real mm. A face: the middle of its area (right for an L "
                                   "shape or a face with holes too). An edge: its middle. An object: the "
                                   "middle of the box it fits in.")
        try:
            from PySide6.QtCore import Qt
            self.lbl_centre.setTextInteractionFlags(Qt.TextSelectableByMouse)
        except Exception:
            pass
        crow = QHBoxLayout()
        crow.addWidget(self.lbl_centre, 1)
        b_copy = QPushButton("Copy")
        b_copy.setToolTip("Copies the centre and size to the clipboard, to paste anywhere.")
        b_copy.clicked.connect(self.copy)
        crow.addWidget(b_copy)
        form.addRow("Centre:", crow)
        self.lbl_size = QLabel("-")
        self.lbl_size.setToolTip("Its size along X, Y and Z (real mm), and a face's area or an edge's length.")
        self.lbl_size.setWordWrap(True)
        form.addRow("Size:", self.lbl_size)
        lay.addLayout(form)

        box1 = QGroupBox("Mark it")
        r1 = QHBoxLayout(box1)
        self.b_mark = QPushButton("Mark the centre")
        self.b_mark.setToolTip("Leaves a guide point at the centre, like the Tape Measure does - snap to it to "
                               "draw from the middle. Guides aren't geometry: Edit > Delete Guides clears them.")
        self.b_lines = QPushButton("Centre lines")
        self.b_lines.setToolTip("Guide lines through the centre: a face - across it both ways (along its "
                                "longest edge and square to it); an edge - square across it and upright; an "
                                "object - along X, Y and Z.")
        r1.addWidget(self.b_mark)
        r1.addWidget(self.b_lines)
        lay.addWidget(box1)
        self.b_mark.clicked.connect(self.mark)
        self.b_lines.clicked.connect(self.lines)

        box2 = QGroupBox("Move to a centre")
        f2 = QVBoxLayout(box2)
        self.b_target = QPushButton("Use this centre as the target")
        self.b_target.setToolTip("Remembers the centre of what's selected now (a wall face, a roof, a stack). "
                                 "Then select the object to move and press 'Move selected here'.")
        f2.addWidget(self.b_target)
        self.lbl_target = QLabel("No target yet.")
        self.lbl_target.setWordWrap(True)
        self.lbl_target.setToolTip("The centre things will be moved to.")
        f2.addWidget(self.lbl_target)
        arow = QHBoxLayout()
        self.cb_axes = []
        for k, t in enumerate(("X", "Y", "Z")):
            cb = QCheckBox("Line up " + t)
            cb.setChecked(k < 2)
            cb.setToolTip("Moves it along %s to line up with the target. Untick to leave it where it is "
                          "that way. Z is unticked by itself for a wall face, so a door or window keeps "
                          "its height and is only centred along the wall." % t)
            self.cb_axes.append(cb)
            arow.addWidget(cb)
        f2.addLayout(arow)
        self.cb_slide = QCheckBox("Slide along the face (keep its distance from it)")
        self.cb_slide.setChecked(True)
        self.cb_slide.setToolTip("When the target is a face: moves the object only across the face, so a door "
                                 "set into a wall or a vent on a roof stays as deep in or as far out as it was, "
                                 "just centred. Untick to use the X / Y / Z ticks instead.")
        f2.addWidget(self.cb_slide)
        self.cb_sit = QCheckBox("Sit it on top of the target")
        self.cb_sit.setToolTip("Stands the object with its bottom on the top of the target - a chimney pot on "
                               "a stack, a vent on a kiln roof, a lamp on a post - centred over it by the X / Y "
                               "ticks. On a face target, its bottom goes to the face's height at the centre.")
        f2.addWidget(self.cb_sit)
        self.b_move = QPushButton("Move selected here")
        self.b_move.setToolTip("Moves the selected object(s) so their centre lands on the target. Undo puts "
                               "them back.")
        f2.addWidget(self.b_move)
        lay.addWidget(box2)
        self.b_target.clicked.connect(self.set_target)
        self.b_move.clicked.connect(self.move_here)
        self.cb_slide.toggled.connect(self.update_buttons)

        self.lbl_report = QLabel()
        self.lbl_report.setWordWrap(True)
        lay.addWidget(self.lbl_report)
        brow = QHBoxLayout()
        brow.addStretch(1)
        b_close = QPushButton("Close")
        b_close.clicked.connect(self.close)
        brow.addWidget(b_close)
        lay.addLayout(brow)
        try:
            self.setMaximumWidth(420)
        except Exception:
            pass
        self.refresh()
        # follow the selection while the window is open
        try:
            from PySide6.QtCore import QTimer
            self._timer = QTimer(self)
            self._timer.timeout.connect(self.watch)
            self._timer.start(400)
        except Exception:
            pass

    # -------------------------------------------------------------- selection
    def selection(self):
        scene = getattr(self.viewport, 'scene', None)
        return list(getattr(scene, 'selection', None) or [])

    def watch(self):
        ents = self.selection()
        key = tuple(id(e) for e in ents)
        if key != self._sel_key:
            self.refresh()

    def refresh(self):
        ents = self.selection()
        self._sel_key = tuple(id(e) for e in ents)
        try:
            self.info = analyse(ents) if ents else None
        except Exception as e:
            self.info = None
            self.lbl_report.setText("Couldn't read the selection: %s" % e)
        i = self.info
        if not i:
            self.lbl_what.setText("nothing (select a face, an edge or an object)")
            self.lbl_centre.setText("-")
            self.lbl_size.setText("-")
        else:
            self.lbl_what.setText(i['label'])
            c = i['centre']
            self.lbl_centre.setText("X %s   Y %s   Z %s mm" % (fmt_mm(c[0]), fmt_mm(c[1]), fmt_mm(c[2])))
            lo, hi = i['lo'], i['hi']
            txt = "%s x %s x %s mm" % (fmt_mm(hi[0] - lo[0]), fmt_mm(hi[1] - lo[1]), fmt_mm(hi[2] - lo[2]))
            if i['kind'] == 'face':
                txt += ",  area %.4g m²" % i['area']
                if i['normal'] is None:
                    txt += "  (not all flat in one plane)"
            elif i['kind'] == 'edge':
                txt += ",  %s mm long" % fmt_mm(i['length'])
            self.lbl_size.setText(txt)
        self.update_buttons()

    def update_buttons(self, *_):
        has = self.info is not None
        for b in (self.b_mark, self.b_lines, self.b_target):
            b.setEnabled(has)
        face_t = bool(self.target and self.target.get('normal') is not None)
        self.cb_slide.setEnabled(face_t)
        self.b_move.setEnabled(bool(self.target) and has and self.info['kind'] == 'object')

    def report(self, text, bad=False):
        self.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if bad else "#2e7d32"))
        self.lbl_report.setText(text)

    # -------------------------------------------------------------- actions
    def copy(self, *_):
        if not self.info:
            return
        try:
            QApplication.clipboard().setText("Centre: %s\nSize: %s" % (self.lbl_centre.text(),
                                                                       self.lbl_size.text()))
            self.report("Copied.")
        except Exception as e:
            self.report("Couldn't copy: %s" % e, True)

    def _add_guides(self, guides, what):
        try:
            from core.guide import Guide
            from core.history import AddGuideCommand
        except Exception as e:
            self.report("This IngeTrazo has no guides (%s)." % e, True)
            return
        try:
            cmds = [AddGuideCommand(Guide(QVector3D(*p), QVector3D(*d) if d else None)) for p, d in guides]
            if len(cmds) == 1:
                self.viewport.history.execute(cmds[0])
            else:
                try:
                    from core.history import CompoundCommand
                    self.viewport.history.execute(CompoundCommand(cmds))
                except ImportError:
                    for c in cmds:
                        self.viewport.history.execute(c)
        except Exception as e:
            self.report("Couldn't add the guide: %s" % e, True)
            return
        self._changed()
        self.report(what)

    def mark(self, *_):
        if self.info:
            self._add_guides([(self.info['centre'], None)], "Marked the centre of %s with a guide point." %
                             self.info['label'])

    def lines(self, *_):
        if self.info:
            ls = centre_lines(self.info)
            self._add_guides(ls, "Added %d centre lines through %s." % (len(ls), self.info['label']))

    def set_target(self, *_):
        if not self.info:
            return
        i = self.info
        self.target = dict(centre=i['centre'], normal=i.get('normal') if i['kind'] == 'face' else None,
                           label=i['label'], groups=i.get('groups', []),
                           top=i['hi'][2] if i['kind'] == 'object' else i['centre'][2])
        n = self.target['normal']
        if n is not None:
            # a wall: keep things at their height; a roof or floor: follow the face
            self.cb_axes[2].setChecked(abs(n[2]) > 0.1)
        c = i['centre']
        self.lbl_target.setText("Target: the centre of %s, X %s  Y %s  Z %s mm. Now select what to move." % (
            i['label'], fmt_mm(c[0]), fmt_mm(c[1]), fmt_mm(c[2])))
        self.update_buttons()

    def move_here(self, *_):
        i, t = self.info, self.target
        if not (i and t) or i['kind'] != 'object':
            self.report("Select the object (group) to move.", True)
            return
        groups = i['groups']
        if any(g is tg for g in groups for tg in t['groups']):
            self.report("That's the target itself: select a different object to move.", True)
            return
        slide = t.get('normal') if (t.get('normal') is not None and self.cb_slide.isChecked()) else None
        sit = (t['top'], i['lo'][2]) if self.cb_sit.isChecked() else None
        d = move_delta(t['centre'], i['centre'], [cb.isChecked() for cb in self.cb_axes], slide, sit)
        if _len(d) < 1e-9:
            self.report("It's already centred there.")
            return
        try:
            from core.history import MoveGroupCommand
            cmds = [MoveGroupCommand(g, QVector3D(*d)) for g in groups]
            if len(cmds) == 1:
                self.viewport.history.execute(cmds[0])
            else:
                from core.history import CompoundCommand
                self.viewport.history.execute(CompoundCommand(cmds))
        except Exception as e:
            self.report("Couldn't move it: %s" % e, True)
            return
        self._changed()
        self._sel_key = None
        self.refresh()
        self.report("Moved %s by X %s  Y %s  Z %s mm, %s %s." % (
            i['label'], fmt_mm(d[0]), fmt_mm(d[1]), fmt_mm(d[2]),
            "sitting on top of" if sit else "centred on", t['label']))

    def _changed(self):
        for name in ('notify_scene_changed', 'update'):
            try:
                getattr(self.viewport, name)()
                return
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
class CentreFinderTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+M"
    description = ("Finds the centre of a face, an edge or an object: marks it with a guide point or "
                   "centre lines, shows its size, and moves another object onto it.")
    _dialog = None

    def on_activate(self, viewport):
        dlg = CentreFinderTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.raise_()
                    dlg.activateWindow()
                    dlg.refresh()
                    return
            except Exception:
                pass
        dlg = CentreDialog(viewport, self)
        CentreFinderTool._dialog = dlg

        def closed(*_):
            CentreFinderTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass


def run(viewport=None):
    CentreFinderTool().on_activate(viewport)
