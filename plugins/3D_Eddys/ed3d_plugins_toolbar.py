# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Plugins Toolbar for IngeTrazo
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
3D Plugins Toolbar - one-click icons for your IngeTrazo plugins
A toolbar along the top of the IngeTrazo window with a button for each of the
3D plugins (Print Scaler, Brick & Block Studio, Loft, Gutters & Downpipes,
Soil & Waste Pipes, Scale Converter, Period Windows, Roof Tiles, Notepad). Click a button to start
that plugin. Right-click the toolbar to pick which buttons it shows, and whether
they have labels. Ctrl+Alt+B shows or hides the toolbar.
"""

import os
import json
import math
from tools.base import Tool

PLUGIN_NAME = "3D Plugins Toolbar"
TOOLBAR_NAME = "ThreeDPluginsToolbar"
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_plugins_toolbar.json")

# (name the plugin registers with, its shortcut, short label, icon)
PLUGINS = [
    ("3D Period Windows", "Ctrl+Alt+N", "Windows", "window"),
    ("3D Brick & Block Studio", "Ctrl+Shift+T", "Bricks", "brick"),
    ("3D Gutters & Downpipes", "Ctrl+Alt+G", "Gutters", "gutter"),
    ("3D Soil & Waste Pipes", "Ctrl+Alt+W", "Soil pipes", "soil"),
    ("3D Loft", "Ctrl+Alt+L", "Loft", "loft"),
    ("3D Print Scaler", "Ctrl+Alt+P", "Scaler", "scaler"),
    ("3D Scale Converter", "Ctrl+Alt+K", "Scale bar", "ruler"),
    ("3D Roof Tiles", "Ctrl+Alt+R", "Roof", "roof"),
    ("3D Notepad", "Ctrl+Alt+J", "Notes", "note"),
    ("3D Wood Planking", "Ctrl+Alt+O", "Planks", "planks"),
    ("3D Period Doors", "Ctrl+Alt+D", "Doors", "door"),
    ("3D Fences & Gates", "Ctrl+Alt+F", "Fences", "fence"),
    ("3D Wrap", "Ctrl+Alt+U", "Wrap", "wrap"),
    ("3D Chimneys", "Ctrl+Alt+H", "Chimneys", "chimney"),
    ("3D Corrugated Iron", "Ctrl+Alt+I", "Tin sheet", "corrugated"),
    ("3D Station Canopies", "Ctrl+Alt+C", "Canopy", "canopy"),
]


def load_settings():
    s = {'visible': True, 'hidden': [], 'labels': True}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            s.update(json.load(f))
    except Exception:
        pass
    return s


def save_settings(s):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Icons, drawn here so nothing extra has to be installed
# ---------------------------------------------------------------------------
def make_icon(kind):
    from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QIcon, QPainterPath, QPolygonF
    from PySide6.QtCore import Qt, QRectF, QPointF
    S = 32
    pm = QPixmap(S, S)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    dark = QPen(QColor(50, 50, 50), 1.4)

    if kind == "window":
        p.setPen(dark)
        p.setBrush(QColor(245, 245, 240))
        path = QPainterPath()
        path.moveTo(7, 29)
        path.lineTo(7, 12)
        path.arcTo(QRectF(7, 3, 18, 18), 180, -180)
        path.lineTo(25, 29)
        path.closeSubpath()
        p.drawPath(path)
        p.setBrush(QColor(170, 210, 235))
        inner = QPainterPath()
        inner.moveTo(10, 26)
        inner.lineTo(10, 12)
        inner.arcTo(QRectF(10, 6, 12, 12), 180, -180)
        inner.lineTo(22, 26)
        inner.closeSubpath()
        p.drawPath(inner)
        p.drawLine(QPointF(16, 6), QPointF(16, 26))
        p.drawLine(QPointF(10, 17), QPointF(22, 17))
        p.setBrush(QColor(200, 195, 180))
        p.drawRect(QRectF(5, 27, 22, 3))
    elif kind == "brick":
        p.setPen(QPen(QColor(235, 225, 210), 1.2))
        p.setBrush(QColor(170, 80, 55))
        for r in range(4):
            y = 4 + r * 6.5
            off = 0 if r % 2 == 0 else -6
            for c in range(4):
                p.drawRect(QRectF(2 + off + c * 12, y, 11, 5.5))
    elif kind == "gutter":
        p.setPen(dark)
        p.setBrush(QColor(90, 95, 100))
        g = QPainterPath()
        g.moveTo(2, 6)
        g.lineTo(30, 6)
        g.arcTo(QRectF(2, 0, 28, 14), 0, -180)
        g.closeSubpath()
        p.drawPath(g)
        p.drawRect(QRectF(20, 12, 5, 14))
        p.drawRect(QRectF(16, 25, 10, 4))
    elif kind == "soil":
        p.setPen(dark)
        p.setBrush(QColor(80, 85, 90))
        p.drawRect(QRectF(12, 2, 8, 20))
        p.drawRect(QRectF(10, 2, 12, 4))
        b = QPainterPath()
        b.moveTo(12, 21)
        b.lineTo(20, 21)
        b.quadTo(20, 26, 26, 26)
        b.lineTo(30, 26)
        b.lineTo(30, 30)
        b.lineTo(26, 30)
        b.quadTo(12, 30, 12, 21)
        p.drawPath(b)
        p.setBrush(QColor(140, 145, 150))
        p.drawRect(QRectF(4, 12, 8, 5))
    elif kind == "loft":
        p.setPen(dark)
        p.setBrush(QColor(120, 160, 200))
        l = QPainterPath()
        l.moveTo(4, 28)
        l.lineTo(28, 28)
        l.lineTo(21, 6)
        l.lineTo(11, 6)
        l.closeSubpath()
        p.drawPath(l)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(30, 60, 120), 1.6))
        p.drawEllipse(QRectF(10, 3, 12, 6))
        p.drawRect(QRectF(4, 25, 24, 5))
    elif kind == "scaler":
        p.setPen(dark)
        p.setBrush(QColor(225, 120, 40))
        p.drawRect(QRectF(5, 14, 14, 14))
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(225, 120, 40), 1.4, Qt.DashLine))
        p.drawRect(QRectF(5, 4, 24, 24))
        p.setPen(QPen(QColor(50, 50, 50), 2.0))
        p.drawLine(QPointF(17, 16), QPointF(26, 7))
        p.drawLine(QPointF(26, 7), QPointF(21, 7))
        p.drawLine(QPointF(26, 7), QPointF(26, 12))
    elif kind == "ruler":
        p.setPen(dark)
        p.setBrush(QColor(240, 205, 90))
        p.drawRect(QRectF(2, 10, 28, 12))
        for i in range(1, 9):
            x = 2 + i * 3.1
            h = 6 if i % 2 == 0 else 3.5
            p.drawLine(QPointF(x, 10), QPointF(x, 10 + h))
    elif kind == "roof":
        p.setPen(QPen(QColor(90, 40, 25), 1.0))
        p.setBrush(QColor(176, 84, 56))
        for r in range(4):
            y = 22 - r * 5.5
            inset = r * 3.0
            off = 0 if r % 2 == 0 else 3.0
            x = 3 + inset + off
            while x < 29 - inset - 0.5:
                w = min(6.0, 29 - inset - x)
                p.drawRect(QRectF(x, y, w, 5.0))
                x += 6.0
        p.setPen(QPen(QColor(60, 60, 60), 1.6))
        p.drawLine(QPointF(2, 28), QPointF(30, 28))
    elif kind == "wrap":
        p.setPen(QPen(QColor(90, 40, 25), 1.0))
        p.setBrush(QColor(176, 84, 56))
        for r in range(5):
            y = 26 - r * 5.0
            w0 = 10.0 - r * 1.0
            for k in range(-2, 2):
                x = 16 + k * w0 + (w0 / 2 if r % 2 else 0)
                if 16 - 2 * w0 <= x <= 16 + w0:
                    p.drawRect(QRectF(x, y, w0 - 0.8, 4.2))
    elif kind == "corrugated":
        path = QPainterPath()
        for row, y0 in enumerate((6.0, 18.0)):
            p.setPen(QPen(QColor(70, 76, 82), 1.0))
            p.setBrush(QColor(150, 158, 164) if row == 0 else QColor(168, 112, 74))
            pts = [QPointF(3 + i * 0.5, y0 + 1.6 * math.sin(i * 0.5 * 2 * math.pi / 5.0)) for i in range(53)]
            pts += [QPointF(29, y0 + 10), QPointF(3, y0 + 10)]
            p.drawPolygon(QPolygonF(pts))
            p.setPen(QPen(QColor(90, 96, 100), 0.7))
            for k in range(6):
                x = 5.5 + k * 5.0
                p.drawLine(QPointF(x, y0 + 2), QPointF(x, y0 + 10))
    elif kind == "canopy":
        p.setPen(QPen(QColor(50, 50, 60), 1.0))
        p.setBrush(QColor(110, 112, 124))
        p.drawPolygon(QPolygonF([QPointF(2, 5), QPointF(30, 10), QPointF(30, 13), QPointF(2, 8)]))   # the roof
        p.setBrush(QColor(214, 200, 160))
        p.setPen(QPen(QColor(130, 110, 70), 0.8))
        pts = [QPointF(4, 13), QPointF(30, 13)]
        x = 30.0
        while x > 4.5:
            pts.append(QPointF(x, 16.5))
            pts.append(QPointF(x - 1.6, 19.5))
            pts.append(QPointF(x - 3.2, 16.5))
            x -= 3.2
        p.drawPolygon(QPolygonF(pts))                                                         # the valance
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(50, 80, 65))
        for cx in (9.0, 23.0):
            p.drawRect(QRectF(cx - 1.2, 16, 2.4, 13))
            p.drawRect(QRectF(cx - 2.2, 27, 4.4, 3))
            p.drawPolygon(QPolygonF([QPointF(cx - 4, 16), QPointF(cx + 4, 16), QPointF(cx + 1.2, 19),
                                     QPointF(cx - 1.2, 19)]))
    elif kind == "chimney":
        p.setPen(QPen(QColor(60, 60, 60), 1.4))
        p.drawLine(QPointF(1, 30), QPointF(31, 18))          # the roof slope
        p.setPen(QPen(QColor(90, 40, 25), 1.0))
        p.setBrush(QColor(176, 84, 56))
        p.drawPolygon(QPolygonF([QPointF(9, 27), QPointF(9, 11), QPointF(23, 11), QPointF(23, 21.7)]))
        p.drawRect(QRectF(7.5, 8.5, 17, 3))                     # oversailing course
        p.setBrush(QColor(200, 110, 60))
        p.drawRect(QRectF(10.5, 2.5, 4, 6))                     # the pots
        p.drawRect(QRectF(17.5, 2.5, 4, 6))
        p.setPen(QPen(QColor(120, 50, 30), 0.8))
        for y in (14, 17, 20, 23):
            p.drawLine(QPointF(9, y), QPointF(23, y))
    elif kind == "fence":
        p.setPen(QPen(QColor(80, 50, 25), 1.0))
        p.setBrush(QColor(150, 104, 64))
        p.drawRect(QRectF(2, 13, 28, 3.5))
        p.drawRect(QRectF(2, 22, 28, 3.5))
        for i in range(5):
            x = 3.5 + i * 5.6
            p.drawPolygon(QPolygonF([QPointF(x, 29), QPointF(x + 3.6, 29), QPointF(x + 3.6, 9),
                                     QPointF(x + 1.8, 5.5), QPointF(x, 9)]))
    elif kind == "door":
        p.setPen(QPen(QColor(220, 218, 210), 1.0))
        p.setBrush(QColor(236, 234, 226))
        p.drawRect(QRectF(7, 2, 18, 28))
        p.setPen(QPen(QColor(25, 55, 40), 1.0))
        p.setBrush(QColor(52, 96, 72))
        p.drawRect(QRectF(9.5, 4.5, 13, 25.5))
        p.setBrush(QColor(40, 78, 58))
        for y in (7, 17):
            p.drawRect(QRectF(11.5, y, 3.8, 8))
            p.drawRect(QRectF(16.7, y, 3.8, 8))
        p.setPen(QPen(QColor(30, 30, 30), 2.0))
        p.drawPoint(QPointF(20.5, 16.5))
    elif kind == "planks":
        p.setPen(QPen(QColor(80, 50, 25), 1.0))
        for i, w in enumerate((5.5, 6.5, 5.0, 6.0)):
            x = 3 + sum((5.5, 6.5, 5.0, 6.0)[:i]) + i * 0.8
            p.setBrush(QColor(150 + 12 * (i % 2), 104 + 8 * (i % 2), 64))
            p.drawRect(QRectF(x, 4, w, 24))
        p.setPen(QPen(QColor(60, 40, 20), 1.6))
        p.drawPoint(QPointF(7, 10))
        p.drawPoint(QPointF(19, 22))
    elif kind == "note":
        p.setPen(dark)
        p.setBrush(QColor(255, 244, 160))
        p.drawRect(QRectF(6, 4, 20, 25))
        p.setPen(QPen(QColor(120, 150, 200), 1.0))
        for i in range(5):
            y = 10 + i * 4
            p.drawLine(QPointF(9, y), QPointF(23, y))
        p.setPen(QPen(QColor(200, 60, 50), 2.2))
        p.drawLine(QPointF(19, 22), QPointF(29, 12))
        p.setPen(QPen(QColor(50, 50, 50), 1.0))
        p.drawLine(QPointF(17, 25), QPointF(19, 22))
    p.end()
    return QIcon(pm)


# ---------------------------------------------------------------------------
# Starting a plugin: find the menu entry IngeTrazo made for it and trigger it
# ---------------------------------------------------------------------------
def _clean(text):
    return (text or "").split("\t")[0].replace("&", "").strip().lower()


def _ours(obj):
    """True for anything belonging to this toolbar (its buttons, its right-click menu)."""
    depth = 0
    while obj is not None and depth < 20:
        try:
            if (obj.objectName() or "").startswith(TOOLBAR_NAME):
                return True
            obj = obj.parent()
        except Exception:
            return False
        depth += 1
    return False


def find_plugin_action(win, name, shortcut):
    """The QAction IngeTrazo created for a plugin tool (matched by name, then shortcut)."""
    from PySide6.QtGui import QAction, QKeySequence
    want = QKeySequence(shortcut).toString()
    by_key = None
    acts = list(win.findChildren(QAction))
    # menu entries made without a parent aren't children of the window: walk the menus too

    def walk(actions, depth=0):
        for a in actions:
            acts.append(a)
            m = a.menu() if depth < 6 else None
            if m is not None:
                walk(m.actions(), depth + 1)
    try:
        walk(win.menuBar().actions())
    except Exception:
        pass
    for a in acts:
        if _ours(a):
            continue
        if _clean(a.text()) == name.lower():
            return a
        try:
            if by_key is None and want and a.shortcut().toString() == want:
                by_key = a
        except Exception:
            pass
    return by_key


_TOOLS = {}


def find_tool_class(name):
    """The plugin's Tool class, among every Tool IngeTrazo has loaded (matched by its name)."""
    found = None
    seen = set()
    todo = list(Tool.__subclasses__())
    while todo:
        c = todo.pop()
        if c in seen:
            continue
        seen.add(c)
        todo.extend(c.__subclasses__())
        if str(getattr(c, 'name', '')).strip().lower() == name.lower():
            found = c                    # the newest one wins if a plugin was loaded twice
    return found


def find_viewport(win):
    """IngeTrazo's 3D view: what a plugin tool is started with."""
    for attr in ('viewport', '_viewport', 'view'):
        vp = getattr(win, attr, None)
        if vp is not None and getattr(vp, 'scene', None) is not None:
            return vp
    from PySide6.QtWidgets import QWidget
    for w in win.findChildren(QWidget):
        if getattr(w, 'scene', None) is not None and getattr(w, 'history', None) is not None:
            return w
    return None


def run_plugin(win, name, shortcut):
    """Starts a plugin the way IngeTrazo's Extensions menu does: its tool's on_activate
    with the 3D view. Falls back to the plugin's menu entry."""
    from PySide6.QtWidgets import QMessageBox
    cls = find_tool_class(name)
    vp = find_viewport(win) if cls is not None else None
    if cls is not None and vp is not None:
        tool = _TOOLS.get(cls)           # one copy of each tool, kept between clicks
        for args in ((), (vp,)):
            if tool is not None:
                break
            try:
                tool = cls(*args)
                _TOOLS[cls] = tool
            except TypeError:
                continue
        if tool is not None:
            try:
                tool.on_activate(vp)
                return
            except Exception as e:
                QMessageBox.warning(win, PLUGIN_NAME, "%s could not start:\n%s" % (name, e))
                return
    a = find_plugin_action(win, name, shortcut)
    if a is None or a.menu() is not None:
        QMessageBox.information(win, PLUGIN_NAME,
                                "%s isn't loaded.\n\nCheck that its .py file is in your IngeTrazo "
                                "plugins folder, then restart IngeTrazo." % name)
        return
    a.trigger()


def refresh_buttons(tb):
    """Greys out the buttons of plugins that aren't installed."""
    win = tb.parent()
    for act in tb.actions():
        info = getattr(act, '_plugin', None)
        if not info:
            continue
        name, shortcut = info
        found = find_tool_class(name) is not None or find_plugin_action(win, name, shortcut) is not None
        act.setEnabled(True)            # stays clickable, so it can say what's missing
        act.setToolTip("%s  (%s)%s" % (name, shortcut, "" if found else "\nNot installed"))


# ---------------------------------------------------------------------------
# The toolbar
# ---------------------------------------------------------------------------
def _main_window():
    from PySide6.QtWidgets import QApplication, QMainWindow
    app = QApplication.instance()
    if app is None:
        return None
    wins = [w for w in app.topLevelWidgets() if isinstance(w, QMainWindow)]
    shown = [w for w in wins if w.isVisible()]
    return (shown or wins or [None])[0]


def find_toolbar(win=None):
    from PySide6.QtWidgets import QToolBar
    win = win or _main_window()
    return win.findChild(QToolBar, TOOLBAR_NAME) if win is not None else None


DIVIDER = "|"          # in the saved layout: a divider between groups of buttons


def current_layout():
    """The saved order of the buttons (plugin names, with DIVIDER between groups).
    Plugins that aren't in it yet (newly added ones) go on the end."""
    st = load_settings()
    known = [p[0] for p in PLUGINS]
    lay = [x for x in (st.get('layout') or []) if x == DIVIDER or x in known]
    for name in known:
        if name not in lay:
            lay.append(name)
    return lay


def build_buttons(tb, win):
    """(Re)makes the toolbar's buttons in the saved order, with dividers."""
    from PySide6.QtGui import QAction
    for a in list(tb.actions()):
        tb.removeAction(a)
        if getattr(a, '_plugin', None) or a.isSeparator():
            a.deleteLater()
    hidden = set(load_settings().get('hidden') or [])
    info = {p[0]: p for p in PLUGINS}
    for entry in current_layout():
        if entry == DIVIDER:
            sep = tb.addSeparator()
            sep.setObjectName(TOOLBAR_NAME + "_divider")
            continue
        name, shortcut, label, icon = info[entry]
        act = QAction(make_icon(icon), label, tb)
        act.setObjectName("%s_%s" % (TOOLBAR_NAME, icon))
        act.setToolTip("%s  (%s)" % (name, shortcut))
        act._plugin = (name, shortcut)
        act.triggered.connect(lambda checked=False, n=name, s=shortcut: run_plugin(win, n, s))
        tb.addAction(act)
        act.setVisible(name not in hidden)


def arrange_buttons(tb):
    """A window to tick which buttons show, put them in order and group them with dividers."""
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                                   QPushButton, QLabel, QDialogButtonBox)
    from PySide6.QtCore import Qt
    win = tb.parent()
    dlg = QDialog(tb)
    dlg.setObjectName(TOOLBAR_NAME + "_arrange")
    dlg.setWindowTitle("Arrange the 3D Plugins toolbar")
    lay = QVBoxLayout(dlg)
    lay.addWidget(QLabel("Tick the buttons you want. Use Move up / Move down to put them in order, "
                         "and Add divider to split them into groups."))
    row = QHBoxLayout()
    lst = QListWidget()
    lst.setMinimumSize(300, 300)
    row.addWidget(lst, 1)
    col = QVBoxLayout()
    b_up, b_down = QPushButton("Move up"), QPushButton("Move down")
    b_div, b_rem, b_reset = QPushButton("Add divider"), QPushButton("Remove divider"), QPushButton("Reset")
    for b in (b_up, b_down, b_div, b_rem, b_reset):
        col.addWidget(b)
    col.addStretch(1)
    row.addLayout(col)
    lay.addLayout(row)
    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    lay.addWidget(bb)
    info = {p[0]: p for p in PLUGINS}

    def add_item(entry, shown=True, at=None):
        if entry == DIVIDER:
            it = QListWidgetItem("-------------  divider  -------------")
            it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        else:
            it = QListWidgetItem(make_icon(info[entry][3]), entry)
            it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if shown else Qt.Unchecked)
        it.setData(Qt.UserRole, entry)
        if at is None:
            lst.addItem(it)
        else:
            lst.insertItem(at, it)
        return it

    def fill(layout, hidden):
        lst.clear()
        for e in layout:
            add_item(e, e not in hidden)

    fill(current_layout(), set(load_settings().get('hidden') or []))

    def move(d):
        r = lst.currentRow()
        if r < 0 or not (0 <= r + d < lst.count()):
            return
        it = lst.takeItem(r)
        lst.insertItem(r + d, it)
        lst.setCurrentRow(r + d)

    def add_div():
        r = lst.currentRow()
        lst.setCurrentItem(add_item(DIVIDER, at=(r + 1) if r >= 0 else lst.count()))

    def rem_div():
        r = lst.currentRow()
        if r >= 0 and lst.item(r).data(Qt.UserRole) == DIVIDER:
            lst.takeItem(r)

    b_up.clicked.connect(lambda: move(-1))
    b_down.clicked.connect(lambda: move(1))
    b_div.clicked.connect(add_div)
    b_rem.clicked.connect(rem_div)
    b_reset.clicked.connect(lambda: fill([p[0] for p in PLUGINS], set()))
    bb.accepted.connect(dlg.accept)
    bb.rejected.connect(dlg.reject)
    eddy_window(dlg, PLUGIN_NAME + ' - arrange', EDDY_TIPS, place=True)  # eddy-window
    if dlg.exec() != QDialog.Accepted:
        return
    layout, hidden = [], []
    for i in range(lst.count()):
        it = lst.item(i)
        e = it.data(Qt.UserRole)
        if layout and layout[-1] == DIVIDER and e == DIVIDER:
            continue                         # two dividers together count as one
        layout.append(e)
        if e != DIVIDER and it.checkState() != Qt.Checked:
            hidden.append(e)
    s = load_settings()
    s['layout'] = layout
    s['hidden'] = hidden
    save_settings(s)
    build_buttons(tb, win)
    refresh_buttons(tb)


def install_toolbar(win=None):
    from PySide6.QtWidgets import QToolBar
    from PySide6.QtGui import QAction
    from PySide6.QtCore import Qt, QSize, QTimer
    win = win or _main_window()
    if win is None:
        return None
    tb = find_toolbar(win)
    if tb is not None:
        return tb
    tb = QToolBar("3D Plugins", win)
    tb.setObjectName(TOOLBAR_NAME)
    tb.setIconSize(QSize(28, 28))
    st = load_settings()
    if st.get('version') != 2:
        # buttons hidden by the old bug (a click unticked them) all come back once
        st['hidden'] = []
        st['version'] = 2
        save_settings(st)
    tb.setToolButtonStyle(Qt.ToolButtonTextUnderIcon if st.get('labels', True) else Qt.ToolButtonIconOnly)
    build_buttons(tb, win)
    win.addToolBar(Qt.TopToolBarArea, tb)
    # right-click the toolbar to choose its buttons
    tb.setContextMenuPolicy(Qt.CustomContextMenu)
    tb.customContextMenuRequested.connect(lambda pos: choose_buttons(tb, tb.mapToGlobal(pos)))

    def vis_changed(on):
        s = load_settings()
        s['visible'] = bool(on)
        save_settings(s)
    tb.visibilityChanged.connect(vis_changed)
    tb.setVisible(bool(load_settings().get('visible', True)))
    # the other plugins may still be loading: check which ones are there a little later
    QTimer.singleShot(3000, lambda: refresh_buttons(tb))
    return tb


def choose_buttons(tb, where=None):
    """A menu of all the plugins with a tick for each button shown, plus labels on/off."""
    from PySide6.QtWidgets import QMenu
    from PySide6.QtGui import QCursor
    from PySide6.QtCore import Qt
    menu = QMenu(tb)
    menu.setObjectName(TOOLBAR_NAME + "_menu")
    menu.addSection("Buttons on this toolbar")
    for act in tb.actions():
        info = getattr(act, '_plugin', None)
        if not info:
            continue
        item = menu.addAction(act.icon(), info[0])
        item.setCheckable(True)
        item.setChecked(act.isVisible())

        def toggled(on, act=act, name=info[0]):
            act.setVisible(on)
            s = load_settings()
            hid = set(s.get('hidden') or [])
            if on:
                hid.discard(name)
            else:
                hid.add(name)
            s['hidden'] = sorted(hid)
            save_settings(s)
        item.toggled.connect(toggled)
    menu.addSeparator()
    show_all = menu.addAction("Show all buttons")
    labels = menu.addAction("Show labels under the icons")
    labels.setCheckable(True)
    labels.setChecked(tb.toolButtonStyle() != Qt.ToolButtonIconOnly)

    def all_on():
        for act in tb.actions():
            if getattr(act, '_plugin', None):
                act.setVisible(True)
        s = load_settings()
        s['hidden'] = []
        save_settings(s)

    def set_labels(on):
        tb.setToolButtonStyle(Qt.ToolButtonTextUnderIcon if on else Qt.ToolButtonIconOnly)
        s = load_settings()
        s['labels'] = bool(on)
        save_settings(s)
    show_all.triggered.connect(all_on)
    labels.toggled.connect(set_labels)
    menu.addSeparator()
    arrange = menu.addAction("Arrange buttons...")
    from PySide6.QtCore import QTimer
    # opened once the menu has closed
    arrange.triggered.connect(lambda: QTimer.singleShot(0, lambda: arrange_buttons(tb)))
    menu.addSeparator()
    hide = menu.addAction("Hide this toolbar (Ctrl+Alt+B brings it back)")
    hide.triggered.connect(lambda: tb.setVisible(False))
    menu.exec(where or QCursor.pos())
    menu.deleteLater()            # don't leave it lying about once it's closed


def _install_when_ready(tries=0):
    """IngeTrazo loads plugins before its window is up, so wait for the window."""
    try:
        from PySide6.QtCore import QTimer
        win = _main_window()
        if win is None or not win.isVisible():
            if tries < 240:
                QTimer.singleShot(500, lambda: _install_when_ready(tries + 1))
            return
        install_toolbar(win)
    except Exception as e:
        print("%s: could not add the toolbar (%s). Press Ctrl+Alt+B to try again." % (PLUGIN_NAME, e))


# --- Extensions menu (begin) ---
# ---------------------------------------------------------------------------
# Extensions menu: all of Eddy's plugins together under "3D Plugins by Eddy"
# ---------------------------------------------------------------------------
EDDY_MENU_TITLE = "3D Plugins by Eddy"
EDDY_STEMS = ("period_windows", "brick_block_studio", "gutters_downpipes", "soil_waste_pipes",
              "loft", "print_scaler", "scale_converter", "roof_tiles", "notepad", "wood_planking",
              "period_doors", "fences_gates", "wrap", "chimneys", "corrugated_iron",
              "station_canopies", "plugins_toolbar")
EDDY_EXTRA_NAMES = ()


def _eddy_menu_key(a):
    return _clean(a.text()).replace("3d ", "", 1)


def group_eddy_menu(win=None):
    """Moves every one of the 3D plugins' entries in the Extensions menu into one
    submenu, '3D Plugins by Eddy'. Safe to run again: it only moves new entries."""
    from PySide6.QtWidgets import QMenu
    win = win or _main_window()
    if win is None:
        return 0
    menu = getattr(win, "_ext_menu", None)
    if menu is None:
        try:
            for a in win.menuBar().actions():
                if a.menu() is not None and _clean(a.text()) == "extensions":
                    menu = a.menu()
                    break
        except Exception:
            menu = None
    if menu is None:
        return 0
    names = {_clean(n) for n in [p[0] for p in PLUGINS] + [PLUGIN_NAME] + list(EDDY_EXTRA_NAMES)}
    owners = win.__dict__.get("_ext_action_owner", {}) or {}
    sub = None
    for a in menu.actions():
        if a.menu() is not None and _clean(a.text()) == _clean(EDDY_MENU_TITLE):
            sub = a.menu()
            break
    found = []

    def scan(m, depth):
        for a in list(m.actions()):
            if a.menu() is not None:
                if a.menu() is not sub and depth < 3:
                    scan(a.menu(), depth + 1)
                continue
            if a.isSeparator():
                continue
            stem = owners.get(a)
            if _clean(a.text()) in names or (stem is not None and (
                    stem in EDDY_STEMS or str(stem).lower().startswith("ed3d_") or str(stem) == "3D_Eddys")):
                found.append((m, a))
    scan(menu, 0)
    if not found:
        return 0
    if sub is None:
        sub = QMenu(EDDY_MENU_TITLE, menu)
        sub.setObjectName("EddyPluginsMenu")
        sub.setToolTipsVisible(True)
        first = None
        for m, a in found:
            if m is menu:
                first = a
                break
        if first is None:
            first = getattr(win, "_ext_anchor", None)
        if first is not None:
            menu.insertMenu(first, sub)
        else:
            menu.addMenu(sub)
    left = set()
    for m, a in found:
        m.removeAction(a)
        if m is not menu:
            left.add(m)
    # tidy: one alphabetical list, the toolbar's own entry last
    acts = [a for a in sub.actions() if not a.isSeparator()] + [a for _, a in found]
    seen, uniq = set(), []
    for a in acts:
        if id(a) not in seen:
            seen.add(id(a))
            uniq.append(a)
    for a in sub.actions():
        sub.removeAction(a)
    tool = [a for a in uniq if _clean(a.text()) == _clean(PLUGIN_NAME)]
    rest = sorted([a for a in uniq if a not in tool], key=_eddy_menu_key)
    for a in rest:
        sub.addAction(a)
        try:
            if a.statusTip():
                a.setToolTip(a.statusTip())     # the pop-up note says what the plugin does
        except Exception:
            pass
    if tool:
        sub.addSeparator()
        for a in tool:
            sub.addAction(a)
    # a category submenu that's now empty is hidden
    for m in left:
        try:
            if not [a for a in m.actions() if not a.isSeparator()]:
                m.menuAction().setVisible(False)
        except Exception:
            pass
    if not getattr(menu, "_eddy_hooked", False):
        try:
            menu.aboutToShow.connect(lambda: group_eddy_menu(win))
            menu._eddy_hooked = True
        except Exception:
            pass
    return len(found)


def _group_menu_when_ready(tries=0):
    """The plugins' menu entries are added a moment after the window opens: keep
    looking for a while, then the menu tidies itself each time it's opened."""
    try:
        from PySide6.QtCore import QTimer
        win = _main_window()
        if win is not None and win.isVisible():
            group_eddy_menu(win)
        if tries < 40:
            QTimer.singleShot(1500, lambda: _group_menu_when_ready(tries + 1))
    except Exception as e:
        print("%s: could not tidy the Extensions menu (%s)." % (PLUGIN_NAME, e))
# --- Extensions menu (end) ---


try:
    _install_when_ready()
except Exception:
    pass
try:  # eddy-window
    _group_menu_when_ready()  # eddy-window
except Exception:  # eddy-window
    pass  # eddy-window


# ---------------------------------------------------------------------------
# Tool: Ctrl+Alt+B shows or hides the toolbar
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

EDDY_TIPS = {'OK': 'Keeps the new order of the buttons.',
 'Move up': 'Moves the picked button up the list (left along the toolbar).',
 'Move down': 'Moves the picked button down the list (right along the toolbar).',
 'Add divider': 'Puts a divider line on the toolbar after the picked button.',
 'Remove divider': 'Takes away the picked divider.',
 'Reset': 'Puts the buttons back in their first order, with no dividers.',
 'Cancel': 'Leaves the buttons as they were.'}
EDDY_TIPS_END = None


class PluginsToolbarTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+B"
    description = "Shows or hides the toolbar with a button for each 3D plugin."

    def on_activate(self, viewport):
        win = None
        try:
            win = viewport.window()
        except Exception:
            pass
        tb = find_toolbar(win) or find_toolbar()
        if tb is None:
            tb = install_toolbar(win)
            if tb is not None:
                tb.setVisible(True)
            return
        tb.setVisible(not tb.isVisible())
        if tb.isVisible():
            refresh_buttons(tb)

    def on_deactivate(self, viewport):
        pass


def run(viewport=None):
    """Console entry point: run() adds the toolbar, or shows it."""
    tb = find_toolbar() or install_toolbar()
    if tb is not None:
        tb.setVisible(True)
