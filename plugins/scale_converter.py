# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Scale Converter for IngeTrazo
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
3D Scale Converter - model scale calculator toolbar for IngeTrazo
A toolbar along the top of the window that converts between real-world sizes
(feet and inches, or mm) and model sizes (mm or inches) at a chosen model scale.
Type in any box and the others follow. Ctrl+Alt+K shows or hides the toolbar.
"""

import os
import json
from tools.base import Tool
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QDoubleSpinBox, QSpinBox, QComboBox, QLabel, QFrame
)

PLUGIN_NAME = "3D Scale Converter"
TOOLBAR_NAME = "ScaleConverterToolbar"
MM_PER_INCH = 25.4
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_scale_converter.json")

SCALES = [("OO 1:76.2", 76.2), ("N (UK) 1:148", 148.0), ("N 1:160", 160.0),
          ("Z 1:220", 220.0), ("TT 1:120", 120.0), ("HO 1:87", 87.1), ("S 1:64", 64.0),
          ("O (UK) 1:43.5", 43.5), ("O (US) 1:48", 48.0),
          ("G 1:22.5", 22.5), ("1:24", 24.0), ("1:12", 12.0),
          ("1:50", 50.0), ("1:100", 100.0), ("Custom", None)]

DEFAULTS = {'scale': 76.2, 'real_mm': 112.0, 'visible': True}


# ---------------------------------------------------------------------------
# Sums (no Qt, so they can be checked on their own)
# ---------------------------------------------------------------------------
def ft_in_to_mm(ft, inch):
    return (ft * 12.0 + inch) * MM_PER_INCH


def mm_to_ft_in(mm):
    """(feet, inches) with inches under 12, rounded to 1/1000 in."""
    total = round(abs(mm) / MM_PER_INCH, 3)
    ft = int(total // 12)
    inch = round(total - ft * 12, 3)
    if inch >= 12.0:
        ft, inch = ft + 1, 0.0
    return ft, inch


def load_settings():
    s = dict(DEFAULTS)
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
# The converter strip that sits in the toolbar
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

EDDY_TIPS = {'@cb_scale': "The model scale to convert to. Pick 'Custom' to type your own."}
EDDY_TIPS_END = None


class ConverterStrip(QWidget):
    def __init__(self, cur, parent=None):
        super().__init__(parent)
        self._busy = False
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 0, 4, 0)
        row.setSpacing(4)

        def label(text):
            lab = QLabel(text)
            row.addWidget(lab)
            return lab

        def sep():
            line = QFrame()
            line.setFrameShape(QFrame.VLine)
            line.setFrameShadow(QFrame.Sunken)
            row.addWidget(line)

        def dspin(val, dec, hi, suffix, width):
            s = QDoubleSpinBox()
            s.setDecimals(dec)
            s.setRange(0.0, hi)
            s.setSuffix(suffix)
            s.setValue(val)
            s.setKeyboardTracking(False)
            s.setMinimumWidth(width)
            s.setButtonSymbols(QDoubleSpinBox.NoButtons)
            row.addWidget(s)
            return s

        label("Scale:")
        self.cb_scale = QComboBox()
        for text, n in SCALES:
            self.cb_scale.addItem(text, n)
        idx = len(SCALES) - 1
        for i, (_, n) in enumerate(SCALES):
            if n is not None and abs(n - cur['scale']) < 1e-9:
                idx = i
        self.cb_scale.setCurrentIndex(idx)
        row.addWidget(self.cb_scale)
        self.sp_custom = dspin(cur['scale'], 2, 10000.0, "", 60)
        self.sp_custom.setRange(1.0, 10000.0)
        self.sp_custom.setPrefix("1:")
        self.sp_custom.setToolTip("Custom scale (pick 'Custom' in the list to type your own)")
        sep()

        label("Real:")
        self.sp_ft = QSpinBox()
        self.sp_ft.setRange(0, 100000)
        self.sp_ft.setSuffix(" ft")
        self.sp_ft.setKeyboardTracking(False)
        self.sp_ft.setButtonSymbols(QSpinBox.NoButtons)
        self.sp_ft.setMinimumWidth(55)
        row.addWidget(self.sp_ft)
        self.sp_in = dspin(0.0, 3, 11.999, " in", 70)
        self.sp_real = dspin(cur['real_mm'], 1, 10000000.0, " mm", 90)
        self.sp_ft.setToolTip("Real-world size: feet")
        self.sp_in.setToolTip("Real-world size: inches")
        self.sp_real.setToolTip("Real-world size in millimetres")
        sep()

        label("Model:")
        self.sp_model = dspin(0.0, 3, 100000.0, " mm", 85)
        self.sp_model_in = dspin(0.0, 4, 10000.0, " in", 80)
        self.sp_model.setToolTip("Size on the model in millimetres")
        self.sp_model_in.setToolTip("Size on the model in inches")

        self.cb_scale.currentIndexChanged.connect(self.scale_changed)
        self.sp_custom.valueChanged.connect(lambda *_: self.edited('real'))
        self.sp_ft.valueChanged.connect(lambda *_: self.edited('ftin'))
        self.sp_in.valueChanged.connect(lambda *_: self.edited('ftin'))
        self.sp_real.valueChanged.connect(lambda *_: self.edited('real'))
        self.sp_model.valueChanged.connect(lambda *_: self.edited('model'))
        self.sp_model_in.valueChanged.connect(lambda *_: self.edited('model_in'))
        self.scale_changed()

    def scale(self):
        n = self.cb_scale.currentData()
        return n if n else self.sp_custom.value()

    def scale_changed(self, *_):
        n = self.cb_scale.currentData()
        self.sp_custom.setEnabled(n is None)
        if n:
            self.sp_custom.blockSignals(True)
            self.sp_custom.setValue(n)
            self.sp_custom.blockSignals(False)
        self.edited('real')          # keep the real size, work out the new model size

    def edited(self, which):
        if self._busy:
            return
        self._busy = True
        try:
            n = self.scale()
            if which == 'ftin':
                real = ft_in_to_mm(self.sp_ft.value(), self.sp_in.value())
            elif which == 'real':
                real = self.sp_real.value()
            elif which == 'model':
                real = self.sp_model.value() * n
            else:
                real = self.sp_model_in.value() * MM_PER_INCH * n
            ft, inch = mm_to_ft_in(real)
            if which != 'ftin':
                self.sp_ft.setValue(ft)
                self.sp_in.setValue(inch)
            if which != 'real':
                self.sp_real.setValue(real)
            if which != 'model':
                self.sp_model.setValue(real / n)
            if which != 'model_in':
                self.sp_model_in.setValue(real / n / MM_PER_INCH)
        finally:
            self._busy = False
        save_settings({'scale': self.scale(), 'real_mm': self.sp_real.value(),
                       'visible': load_settings().get('visible', True)})


# ---------------------------------------------------------------------------
# Putting the toolbar on IngeTrazo's main window
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


def install_toolbar(win=None):
    """Adds the converter toolbar along the top of the main window (once)."""
    from PySide6.QtWidgets import QToolBar
    from PySide6.QtCore import Qt
    win = win or _main_window()
    if win is None:
        return None
    tb = find_toolbar(win)
    if tb is not None:
        return tb
    cur = load_settings()
    tb = QToolBar("Scale Converter", win)
    tb.setObjectName(TOOLBAR_NAME)
    tb.setToolTip(PLUGIN_NAME)
    strip = ConverterStrip(cur, tb)  # eddy-window
    eddy_window(strip, PLUGIN_NAME, EDDY_TIPS, place=False)  # eddy-window
    tb.addWidget(strip)  # eddy-window
#tb.addWidget(ConverterStrip(cur, tb))  # eddy-window
    win.addToolBar(Qt.TopToolBarArea, tb)

    def vis_changed(on):
        s = load_settings()
        s['visible'] = bool(on)
        save_settings(s)
    tb.visibilityChanged.connect(vis_changed)
    tb.setVisible(bool(cur.get('visible', True)))
    return tb


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
        print("%s: could not add the toolbar (%s). Press Ctrl+Alt+K to try again." % (PLUGIN_NAME, e))


try:
    _install_when_ready()
except Exception:
    pass


# ---------------------------------------------------------------------------
# Tool: Ctrl+Alt+K shows or hides the toolbar
# ---------------------------------------------------------------------------
class ScaleConverterTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+K"
    description = "Shows or hides the scale converter toolbar: real sizes (ft / in / mm) to model sizes."

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

    def on_deactivate(self, viewport):
        pass


def run(viewport=None):
    """Console entry point: run() adds the toolbar, or shows / hides it."""
    tb = find_toolbar() or install_toolbar()
    if tb is not None:
        tb.setVisible(True)
