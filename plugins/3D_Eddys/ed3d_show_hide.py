# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Show / Hide for IngeTrazo
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
3D Show / Hide - one small window, with a tab for each kind of thing you want out of the way
while you work: the floors and plates of a Floor Plan building, and the roof, boards and loose
trusses over a Subframe. Ticked = shown, untick to hide. Each click is one Ctrl+Z step, using
IngeTrazo's own Hide, so Edit > Unhide brings things back too.

It's the window that Floor Plan's 'Show floors...' and Subframe's 'Show / hide...' buttons open
(on their own tab), or Ctrl+Alt+Shift+H. It floats over the model and stays open until you close
it, and opens where you left it, on the tab you last used.

Adding a tab later: write a page class like FloorsPage below (a title, refresh() and show_all())
and add it to PAGES at the bottom of the pages section.
"""

import os
import sys
import json

from tools.base import Tool
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
                               QCheckBox, QPushButton, QTabWidget, QMessageBox)

PLUGIN_NAME = "3D Show / Hide"
VERSION = "1"             # shown in the window title, so you can tell which file is loaded
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_eddy_show_hide.json")


def _items(x):
    if x is None:
        return []
    if isinstance(x, dict):
        return list(x.values())
    try:
        return list(x)
    except Exception:
        return []


def _load():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save(**kw):
    d = _load()
    d.update(kw)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)
    except Exception:
        pass


def plugin_module(stem):
    """Another of the 3D plugins, as it's loaded (by the 3D_Eddys folder or on its own), or None."""
    for name, mod in list(sys.modules.items()):
        if mod is None:
            continue
        if name == stem or name.endswith("_" + stem) or name.endswith("." + stem):
            return mod
    return None


def hide_things(viewport, ents, hidden, is_hidden=None):
    """Hides (or shows) groups the way IngeTrazo's own Edit > Hide does, so it can be undone."""
    is_hidden = is_hidden or (lambda e: bool(getattr(e, 'hidden', False)))
    ents = [e for e in ents if is_hidden(e) != bool(hidden)]
    if not ents:
        return
    try:
        from core.history import HideCommand
        viewport.history.execute(HideCommand(ents, bool(hidden)))
    except Exception as e:
        QMessageBox.warning(None, PLUGIN_NAME, "Couldn't %s them:\n%s" % ("hide" if hidden else "show", e))
        return
    try:
        viewport.notify_scene_changed()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# The pages (one tab each)
# ---------------------------------------------------------------------------
class FloorsPage(QWidget):
    """Floor Plan: a tick for each storey's walls and one for its floor; the plates on their own."""
    key = 'floors'
    title = "Floors"
    plugin = "ed3d_floor_plan"

    def __init__(self, win):
        super().__init__()
        self.win = win
        self.checks = {}
        self._shape = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(3)
        self.lbl = QLabel()
        self.lbl.setWordWrap(True)
        lay.addWidget(self.lbl)
        self.grid_w = QWidget()
        self.grid = QGridLayout(self.grid_w)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setVerticalSpacing(1)
        lay.addWidget(self.grid_w)
        b_fl = QPushButton("Hide floors && plates")
        b_fl.setToolTip("Hides every floor slab, floor panel and plate but keeps all the walls - the "
                        "inside walls too - so you can see every room from above.")
        b_fl.clicked.connect(self.hide_floors)
        lay.addWidget(b_fl)
        lay.addStretch(1)

    def mod(self):
        m = plugin_module(self.plugin)
        return m if m is not None and hasattr(m, 'floor_groups') else None

    def _rows(self):
        m, sc = self.mod(), self.win.scene()
        if m is None or sc is None:
            return {}, []
        return m.floor_groups(sc)

    def refresh(self):
        m = self.mod()
        if m is None:
            self._clear()
            self._shape = None
            self.lbl.setText("3D Floor Plan isn't loaded, so there are no floors to show here.")
            return
        rows, _h = self._rows()
        labels = sorted(rows, key=m._floor_order)
        shape = [(l_, bool(rows[l_]['walls']), bool(rows[l_]['floor'])) for l_ in labels]
        if shape != self._shape:
            self._shape = shape
            self._clear()
            mid = Qt.AlignHCenter | Qt.AlignVCenter
            if labels:
                for c_, txt in ((1, "Walls"), (2, "Floor")):
                    h = QLabel("<b>%s</b>" % txt)
                    h.setAlignment(mid)
                    self.grid.addWidget(h, 0, c_, mid)
            for r, (lab, has_w, has_f) in enumerate(shape, start=1):
                self.grid.addWidget(QLabel(lab), r, 0, Qt.AlignLeft | Qt.AlignVCenter)
                for c_, part, has in ((1, 'walls', has_w), (2, 'floor', has_f)):
                    if not has:
                        continue
                    cb = QCheckBox()
                    cb.setToolTip("Untick to hide the %s %s." % (lab.lower(), "walls" if part == 'walls' else
                                  ("floor" if lab not in ("Top plate", "Base plate") else "")))
                    cb.toggled.connect(lambda on, l_=lab, p_=part: self.toggle(l_, p_, on))
                    self.grid.addWidget(cb, r, c_, mid)
                    self.checks[(lab, part)] = cb
        for (lab, part), cb in self.checks.items():
            ents = rows.get(lab, {}).get(part, [])
            cb.blockSignals(True)
            cb.setChecked(not (ents and all(m._is_hidden(e) for e in ents)))
            cb.blockSignals(False)
        self.lbl.setText("Untick to hide. Hide the floors and plates to see into the rooms." if labels else
                         "No floor plan in the model yet - build one and its floors show up here.")

    def _clear(self):
        while self.grid.count():
            it = self.grid.takeAt(0)
            w = it.widget()
            if w is not None:
                w.deleteLater()
        self.checks = {}

    def toggle(self, lab, part, on):
        m = self.mod()
        if m is None:
            return
        rows, _h = self._rows()
        m.set_hidden(self.win.viewport, rows.get(lab, {}).get(part, []), not on)
        self.win.changed()

    def show_all(self):
        m = self.mod()
        if m is None:
            return
        rows, holders = self._rows()
        m.set_hidden(self.win.viewport, holders + [e for r in rows.values() for e in r['walls'] + r['floor']],
                     False)

    def hide_floors(self):
        m = self.mod()
        if m is None:
            return
        rows, holders = self._rows()
        m.set_hidden(self.win.viewport, [e for r in rows.values() for e in r['floor']], True)
        m.set_hidden(self.win.viewport, holders + [e for r in rows.values() for e in r['walls']], False)
        self.win.changed()


class RoofPage(QWidget):
    """Subframe: the roof, the fascia / barge / soffit boards and the loose trusses, so you can see
    the frame inside. The wall frames themselves are never touched."""
    key = 'roof'
    title = "Roof && frame"
    plugin = "ed3d_subframe"

    def __init__(self, win):
        super().__init__()
        self.win = win
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(3)
        self.lbl = QLabel()
        self.lbl.setWordWrap(True)
        lay.addWidget(self.lbl)
        self.ticks = {}
        self.box = QVBoxLayout()
        self.box.setSpacing(1)
        lay.addLayout(self.box)
        lay.addStretch(1)
        self._built = False

    def mod(self):
        m = plugin_module(self.plugin)
        return m if m is not None and hasattr(m, 'show_hide_groups') else None

    def _build(self, m):
        if self._built:
            return
        self._built = True
        tips = getattr(m, 'SHOW_HIDE_TIPS', {})
        for k, lab, _s in m.SHOW_HIDE:
            cb = QCheckBox(lab)
            cb.setToolTip(tips.get(k, ""))
            cb.clicked.connect(lambda _on=False, k=k: self.flip(k))
            self.box.addWidget(cb)
            self.ticks[k] = (cb, lab)

    def refresh(self):
        m, sc = self.mod(), self.win.scene()
        if m is None:
            self.lbl.setText("3D Subframe isn't loaded, so there's nothing to show here.")
            return
        self._build(m)
        self.lbl.setText("Untick to hide it - the wall frames stay put.")
        found = m.show_hide_groups(sc) if sc is not None else {}
        for k, (cb, lab) in self.ticks.items():
            gs = found.get(k, [])
            cb.blockSignals(True)
            if not gs:
                cb.setText("%s - none" % lab)
                cb.setChecked(True)
                cb.setEnabled(False)
            else:
                hid = sum(1 for g in gs if getattr(g, 'hidden', False))
                cb.setEnabled(True)
                cb.setText("%s (%d)" % (lab, len(gs)) if hid in (0, len(gs)) else
                           "%s (%d, %d hidden)" % (lab, len(gs), hid))
                cb.setChecked(hid == 0)
            cb.blockSignals(False)

    def flip(self, key):
        m, sc = self.mod(), self.win.scene()
        if m is None or sc is None:
            return
        gs = m.show_hide_groups(sc).get(key, [])
        # shown (or partly shown) -> hide them all; all hidden -> show them all
        hide_things(self.win.viewport, gs, any(not getattr(g, 'hidden', False) for g in gs))
        self.win.changed()

    def show_all(self):
        m, sc = self.mod(), self.win.scene()
        if m is None or sc is None:
            return
        hide_things(self.win.viewport, [g for gs in m.show_hide_groups(sc).values() for g in gs], False)


# the tabs, in order - add new pages here
PAGES = [FloorsPage, RoofPage]


# ---------------------------------------------------------------------------
# The window
# ---------------------------------------------------------------------------
class ShowHideWindow(QDialog):
    _open = None            # the one that's open, kept here so it isn't thrown away

    def __init__(self, viewport, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Show / hide  (%s)" % VERSION)
        self.setModal(False)
        try:
            # a small floating tool window: it stays over the model while you click and work there
            self.setWindowFlags(Qt.Tool | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        except Exception:
            pass
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.viewport = viewport
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.pages = []
        for cls in PAGES:
            pg = cls(self)
            self.pages.append(pg)
            self.tabs.addTab(pg, cls.title)
        lay.addWidget(self.tabs)
        row = QHBoxLayout()
        b_all = QPushButton("Show everything")
        b_all.setToolTip("Shows everything on every tab again.")
        b_all.clicked.connect(self.show_all)
        b_close = QPushButton("Close")
        b_close.setToolTip("Closes this window (so does its X). Anything hidden stays hidden.")
        b_close.clicked.connect(self.close)
        row.addWidget(b_all)
        row.addStretch(1)
        row.addWidget(b_close)
        lay.addLayout(row)
        self.go_to(_load().get('tab'))
        self.tabs.currentChanged.connect(self._tab_changed)
        self._ver = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(800)              # keeps up with undo, new builds, Edit > Unhide...
        self.refresh()

    def scene(self):
        return getattr(self.viewport, 'scene', None)

    def go_to(self, key):
        for i, pg in enumerate(self.pages):
            if pg.key == key:
                self.tabs.setCurrentIndex(i)
                return

    def _tab_changed(self, i):
        if 0 <= i < len(self.pages):
            _save(tab=self.pages[i].key)
        self.refresh()

    def _poll(self):
        if getattr(self.scene(), 'version', None) != self._ver:
            self.refresh()

    def changed(self):
        self._ver = None
        self.refresh()

    def refresh(self):
        self._ver = getattr(self.scene(), 'version', None)
        pg = self.tabs.currentWidget()
        if pg is not None:
            try:
                pg.refresh()
            except Exception as e:
                print("%s: %s" % (PLUGIN_NAME, e))

    def show_all(self):
        for pg in self.pages:
            try:
                pg.refresh()
                pg.show_all()
            except Exception as e:
                print("%s: %s" % (PLUGIN_NAME, e))
        self.changed()

    def keyPressEvent(self, ev):
        # Esc and Enter don't shut it - only its X or Close
        if ev.key() in (Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter):
            ev.ignore()
            return
        super().keyPressEvent(ev)

    def closeEvent(self, ev):
        try:
            self._timer.stop()
        except Exception:
            pass
        if ShowHideWindow._open is self:
            ShowHideWindow._open = None
        super().closeEvent(ev)


def open_show_hide(viewport, tab=None):
    """Opens the Show / hide window (or brings it to the front), on the tab asked for. The other
    plugins' 'Show floors...' and 'Show / hide...' buttons call this."""
    w = ShowHideWindow._open
    try:
        if w is not None and w.isVisible():
            w.viewport = viewport
            if tab:
                w.go_to(tab)
            w.changed()
            w.raise_()
            w.activateWindow()
            return w
    except Exception:
        pass
    # it belongs to IngeTrazo's main window, so it stays on top of the model when you click there,
    # and stays open when the plugin that opened it is closed
    main = None
    try:
        main = viewport.window()
    except Exception:
        main = None
    w = ShowHideWindow(viewport, main)
    ShowHideWindow._open = w
    if tab:
        w.go_to(tab)
    eddy_window(w, PLUGIN_NAME, None, place=True)      # opens where you left it
    w.show()
    return w


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


class ShowHideTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+Shift+H"
    description = ("One small window, with a tab each, to hide and show the floors of a Floor Plan "
                   "building and the roof, boards and trusses over a Subframe.")

    def on_activate(self, viewport):
        open_show_hide(viewport)

    def on_deactivate(self, viewport):
        pass


def run(viewport=None):
    ShowHideTool().on_activate(viewport)
