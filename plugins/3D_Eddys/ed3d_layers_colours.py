# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Layers & Colours for IngeTrazo
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
3D Layers & Colours - every part the 3D plugins build comes out on its own layer and
coloured by what it is, so a model is easy to read and easy to manage.

* Layers: each plugin puts what it builds on a layer of its own (Chimneys, Windows,
  Station canopies...), so a whole kind of structure can be hidden, shown or selected at
  once. The names can be changed here.
* Colours: each part is painted with a material named after what it is - "Eddy - Brick",
  "Eddy - Slate", "Eddy - Glass", "Eddy - Canopy ironwork"... A material is only made if
  the document hasn't got it yet, so if you recolour one in IngeTrazo, the next thing you
  build uses your colour.
* Apply to selected: does the same to groups already in the model - older builds, or
  anything else - in one undo step.

The other plugins hand their new groups to organise() below. If this file is left out,
they simply build as before. Ctrl+Alt+V.
"""

import json
import os
import re

from tools.base import Tool
from core.history import SnapshotImport
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QLabel,
                               QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
                               QWidget, QColorDialog, QComboBox, QFormLayout, QAbstractItemView)

PLUGIN_NAME = "3D Layers & Colours"
VERSION = "1"
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_eddy_layers_colours.json")
MAT_PREFIX = "Eddy - "

# The layer each plugin puts its work on
DEFAULT_LAYERS = {
    "3D Brick & Block Studio": "Walls - brick & block",
    "3D Wood Planking": "Walls - timber cladding",
    "3D Roof Tiles": "Roofs - tiles & slates",
    "3D Corrugated Iron": "Roofs - corrugated iron",
    "3D Chimneys": "Chimneys",
    "3D Period Doors": "Doors",
    "3D Period Windows": "Windows",
    "3D Gutters & Downpipes": "Gutters & downpipes",
    "3D Soil & Waste Pipes": "Soil & waste pipes",
    "3D Station Canopies": "Station canopies",
    "3D Fences & Gates": "Fences & gates",
}

# (material, colour 0-255, opacity, words in a part's name that pick it, only for these plugins)
# The first one whose word is in the part's name wins, so the narrow ones come first.
DEFAULT_PALETTE = [
    ("Glass", (176, 196, 206), 0.35, "glass, pane, light", ""),
    ("Ironmongery", (40, 40, 42), 1.0, "handle, hinge, knob, latch, letter, knocker, vane, finial", ""),
    ("Chimney pot", (184, 108, 72), 1.0, "pot", "3D Chimneys"),
    ("Lead", (115, 120, 128), 1.0, "flashing, lead, roll", ""),
    ("Mortar", (200, 194, 178), 1.0, "mortar, flaunching, render, pointing", ""),
    ("Pipework", (38, 38, 40), 1.0, "gutter, downpipe, pipe, hopper, shoe, swan, bend, branch, stack, clip", "3D Gutters & Downpipes, 3D Soil & Waste Pipes"),
    ("Canopy ironwork", (46, 92, 68), 1.0, "column, bracket, beam, spandrel, girder, truss, post", "3D Station Canopies"),
    ("Valance", (234, 222, 184), 1.0, "valance", ""),
    ("Window paint", (238, 236, 226), 1.0, "frame, sash, bar, cill, sill, casement, window, mullion, transom", "3D Period Windows"),
    ("Door paint", (60, 82, 70), 1.0, "door, leaf, panel, frame, rail, stile, muntin, fanlight", "3D Period Doors"),
    ("Galvanised iron", (158, 166, 170), 1.0, "corrugated, sheet, tin, iron", ""),
    ("Slate", (84, 90, 102), 1.0, "slate, tile, roof, ridge, hip, verge", ""),
    ("Brick", (168, 80, 56), 1.0, "brick, brickwork, chimney, pier, oversailing, arch", ""),
    ("Stone", (204, 196, 178), 1.0, "block, stone, coping, cill, sill, lintel, plinth, cap, quoin, kerb, string, band, base", ""),
    ("Timber", (140, 102, 66), 1.0, "plank, board, timber, fence, gate, picket, post, rail, weather, cladding, batten", ""),
]

# What a part is painted with when none of the words fit, by plugin
PLUGIN_FALLBACK = {
    "3D Brick & Block Studio": "Brick",
    "3D Wood Planking": "Timber",
    "3D Roof Tiles": "Slate",
    "3D Corrugated Iron": "Galvanised iron",
    "3D Chimneys": "Brick",
    "3D Period Doors": "Door paint",
    "3D Period Windows": "Window paint",
    "3D Gutters & Downpipes": "Pipework",
    "3D Soil & Waste Pipes": "Pipework",
    "3D Station Canopies": "Canopy ironwork",
    "3D Fences & Gates": "Timber",
}


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
def _default_settings():
    return {
        'layers_on': True,
        'colours_on': True,
        'repaint': False,
        'layers': dict(DEFAULT_LAYERS),
        'palette': [list(r) for r in DEFAULT_PALETTE],
    }


def load_settings():
    s = _default_settings()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        for k in ('layers_on', 'colours_on', 'repaint'):
            if k in saved:
                s[k] = bool(saved[k])
        if isinstance(saved.get('layers'), dict):
            s['layers'].update({str(k): str(v) for k, v in saved['layers'].items()})
        if isinstance(saved.get('palette'), list) and saved['palette']:
            pal = []
            for r in saved['palette']:
                try:
                    pal.append([str(r[0]), tuple(int(c) for c in r[1][:3]), float(r[2]), str(r[3]),
                                str(r[4]) if len(r) > 4 else ""])
                except Exception:
                    pass
            if pal:
                s['palette'] = pal
    except Exception:
        pass
    return s


def save_settings(s):
    try:
        out = dict(s)
        out['palette'] = [[r[0], list(r[1]), r[2], r[3], r[4]] for r in s['palette']]
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1)
    except Exception as e:
        print("%s: could not save settings: %s" % (PLUGIN_NAME, e))


def _words(text):
    return [w.strip().lower() for w in (text or "").split(",") if w.strip()]


# ---------------------------------------------------------------------------
# Doing it
# ---------------------------------------------------------------------------
def _children(g):
    return list(getattr(g, 'children', None) or ())


def _faces(g):
    mesh = getattr(g, 'mesh', None)
    return list(getattr(mesh, 'faces', None) or ()) if mesh is not None else []


def ensure_layer(scene, name):
    if not name:
        return
    layers = getattr(scene, 'layers', None)
    if layers is None:
        return
    if name in {getattr(ly, 'name', None) for ly in layers}:
        return
    from core.layers import Layer
    layers.append(Layer(name))


def _paint_attrs(scene, row, update):
    """The face attributes for palette row `row`, making (or with `update`, recolouring) its
    material in the document."""
    name, rgb, opacity = MAT_PREFIX + row[0], row[1], row[2]
    colour = (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
    mats = getattr(scene, 'materials', None)
    if mats is not None:
        try:
            mat = mats.get(name)
            if mat is None:
                from core.materials import Material
                mat = mats[name] = Material(name, color=colour, opacity=opacity)
            elif update:
                for attr, val in (('color', colour), ('opacity', opacity)):
                    if hasattr(mat, attr):
                        setattr(mat, attr, val)
            return dict(mat.face_attrs())
        except Exception as e:
            print("%s: material %r: %s" % (PLUGIN_NAME, name, e))
    return {"color": colour}


def _pick_row(palette, names, plugin):
    """The palette row for a part, from its own name first and then its parents' names."""
    for nm in names:
        low = (nm or "").lower()
        for row in palette:
            only = _words(row[4])
            if only and (plugin or "").lower() not in only:
                continue
            if any(re.search(r"\b%s(s|es)?\b" % re.escape(w), low) for w in _words(row[3])):
                return row
    fb = PLUGIN_FALLBACK.get(plugin or "")
    for row in palette:
        if row[0] == fb:
            return row
    return None


def colour_group(scene, group, plugin, palette, repaint=False):
    """Paint every face under `group` by what its part is called. Faces that already have
    a colour or material are left alone unless `repaint`. Returns the number of faces painted."""
    cache = {}
    count = 0

    def walk(g, names):
        nonlocal count
        names = [getattr(g, 'name', '') or ''] + names
        faces = _faces(g)
        if faces:
            row = _pick_row(palette, names, plugin)
            if row is not None:
                if row[0] not in cache:
                    cache[row[0]] = _paint_attrs(scene, row, repaint)
                paint = cache[row[0]]
                for f in faces:
                    a = dict(getattr(f, 'attrs', None) or {})
                    if not repaint and ('color' in a or 'mat' in a or 'texture' in a):
                        continue
                    if repaint:
                        a.pop('texture', None)
                    a.update(paint)
                    f.attrs = a
                    count += 1
        for c in _children(g):
            walk(c, names)

    walk(group, [])
    return count


def organise(scene, group, plugin):
    """Called by the other 3D plugins for each top-level group they build, inside their own
    undo step: put it on the plugin's layer and colour its parts, as set in this plugin."""
    s = load_settings()
    if s['layers_on']:
        layer = s['layers'].get(plugin) or DEFAULT_LAYERS.get(plugin)
        if layer:
            ensure_layer(scene, layer)
            group.layer = layer
    if s['colours_on']:
        colour_group(scene, group, plugin, s['palette'], repaint=False)


def _plugin_of(group):
    """Which plugin made a group, guessed from its name - for Apply to selected."""
    low = (getattr(group, 'name', '') or '').lower()
    guesses = [("chimney", "3D Chimneys"), ("pot", "3D Chimneys"), ("vent", "3D Chimneys"),
               ("canopy", "3D Station Canopies"), ("window", "3D Period Windows"),
               ("door", "3D Period Doors"), ("gutter", "3D Gutters & Downpipes"),
               ("downpipe", "3D Gutters & Downpipes"), ("soil", "3D Soil & Waste Pipes"),
               ("waste", "3D Soil & Waste Pipes"), ("fence", "3D Fences & Gates"),
               ("gate", "3D Fences & Gates"), ("corrugated", "3D Corrugated Iron"),
               ("plank", "3D Wood Planking"), ("board", "3D Wood Planking"),
               ("tile", "3D Roof Tiles"), ("slate", "3D Roof Tiles"), ("roof", "3D Roof Tiles"),
               ("brick", "3D Brick & Block Studio"), ("block", "3D Brick & Block Studio")]
    for word, plugin in guesses:
        if word in low:
            return plugin
    return ""


# ---------------------------------------------------------------------------
# The dialog
# ---------------------------------------------------------------------------
class LayersColoursDialog(QDialog):
    KEEP = "(keep each group's layer, or the plugin's)"

    def __init__(self, viewport):
        super().__init__(viewport)
        self.viewport = viewport
        self.setWindowTitle(PLUGIN_NAME)
        self.resize(640, 560)
        self.s = load_settings()
        lay = QVBoxLayout(self)

        intro = QLabel("Everything the 3D plugins build goes on a layer for its kind of work and is "
                       "coloured by what each part is, so structures are easy to pick out and to "
                       "show, hide or select together.")
        intro.setWordWrap(True)
        lay.addWidget(intro)
        self.cb_layers = QCheckBox("Put new builds on a layer for each plugin")
        self.cb_layers.setChecked(self.s['layers_on'])
        self.cb_colours = QCheckBox("Colour new builds by what each part is (brick, slate, glass...)")
        self.cb_colours.setChecked(self.s['colours_on'])
        lay.addWidget(self.cb_layers)
        lay.addWidget(self.cb_colours)

        tabs = QTabWidget()
        lay.addWidget(tabs, 1)

        # colours
        w = QWidget()
        v = QVBoxLayout(w)
        note = QLabel("Click a colour to change it. A part takes the first colour with one of its words in "
                      "its name (whole words; plurals count). Each is a material named \"%s...\": it is only made if the document "
                      "hasn't got one, so a colour you change in IngeTrazo stays yours." % MAT_PREFIX)
        note.setWordWrap(True)
        v.addWidget(note)
        self.tbl = QTableWidget(0, 4)
        self.tbl.setHorizontalHeaderLabels(["Material", "Colour", "Words in the part's name", "Only for"])
        self.tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.cellClicked.connect(self._cell_clicked)
        v.addWidget(self.tbl, 1)
        row_btns = QHBoxLayout()
        b_add = QPushButton("Add colour")
        b_add.clicked.connect(self._add_row)
        b_del = QPushButton("Remove")
        b_del.clicked.connect(self._del_row)
        b_reset = QPushButton("Back to the standard colours")
        b_reset.clicked.connect(self._reset_palette)
        row_btns.addWidget(b_add)
        row_btns.addWidget(b_del)
        row_btns.addStretch(1)
        row_btns.addWidget(b_reset)
        v.addLayout(row_btns)
        tabs.addTab(w, "Colours")
        self._fill_palette(self.s['palette'])

        # layers
        w = QWidget()
        v = QVBoxLayout(w)
        self.tbl_layers = QTableWidget(0, 2)
        self.tbl_layers.setHorizontalHeaderLabels(["Plugin", "Layer it builds on"])
        self.tbl_layers.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_layers.verticalHeader().setVisible(False)
        for plugin in sorted(DEFAULT_LAYERS):
            r = self.tbl_layers.rowCount()
            self.tbl_layers.insertRow(r)
            it = QTableWidgetItem(plugin)
            it.setFlags(it.flags() & ~Qt.ItemIsEditable)          # not editable
            self.tbl_layers.setItem(r, 0, it)
            self.tbl_layers.setItem(r, 1, QTableWidgetItem(self.s['layers'].get(plugin, "")))
        v.addWidget(self.tbl_layers, 1)
        tabs.addTab(w, "Layers")

        # apply to selected
        w = QWidget()
        f = QFormLayout(w)
        expl = QLabel("Organise groups that are already in the model - things built before, or "
                      "anything else. Select the groups first.")
        expl.setWordWrap(True)
        f.addRow(expl)
        self.cmb_layer = QComboBox()
        self.cmb_layer.setEditable(True)
        self.cmb_layer.addItem(self.KEEP)
        scene = getattr(viewport, 'scene', None)
        for ly in (getattr(scene, 'layers', None) or []):
            nm = getattr(ly, 'name', '')
            if nm:
                self.cmb_layer.addItem(nm)
        f.addRow("Put them on layer:", self.cmb_layer)
        self.cb_sel_colour = QCheckBox("Colour them by part name")
        self.cb_sel_colour.setChecked(True)
        f.addRow(self.cb_sel_colour)
        self.cb_repaint = QCheckBox("Repaint faces that already have a colour (and update the "
                                    "\"%s\" materials to the colours here)" % MAT_PREFIX)
        self.cb_repaint.setChecked(self.s['repaint'])
        f.addRow(self.cb_repaint)
        b_apply = QPushButton("Apply to selected")
        b_apply.clicked.connect(self._apply_selected)
        f.addRow(b_apply)
        self.lbl = QLabel("")
        self.lbl.setWordWrap(True)
        f.addRow(self.lbl)
        tabs.addTab(w, "Apply to selected")

        btns = QHBoxLayout()
        btns.addStretch(1)
        b_save = QPushButton("Save")
        b_save.setDefault(True)
        b_save.clicked.connect(self._save_close)
        b_close = QPushButton("Close")
        b_close.clicked.connect(self.reject)
        btns.addWidget(b_save)
        btns.addWidget(b_close)
        lay.addLayout(btns)

    # palette table -----------------------------------------------------
    def _fill_palette(self, palette):
        self.tbl.setRowCount(0)
        for row in palette:
            self._insert(row)

    def _insert(self, row):
        r = self.tbl.rowCount()
        self.tbl.insertRow(r)
        self.tbl.setItem(r, 0, QTableWidgetItem(row[0]))
        sw = QTableWidgetItem("  %d%%" % round(row[2] * 100) if row[2] < 1 else "")
        sw.setBackground(QColor(*row[1]))
        sw.setData(Qt.UserRole, [list(row[1]), row[2]])        # Qt.UserRole
        sw.setFlags(sw.flags() & ~Qt.ItemIsEditable)
        sw.setToolTip("Click to change")
        self.tbl.setItem(r, 1, sw)
        self.tbl.setItem(r, 2, QTableWidgetItem(row[3]))
        self.tbl.setItem(r, 3, QTableWidgetItem(row[4] if len(row) > 4 else ""))

    def _cell_clicked(self, r, c):
        if c != 1:
            return
        it = self.tbl.item(r, 1)
        rgb, op = it.data(Qt.UserRole)
        col = QColorDialog.getColor(QColor(*rgb), self, "Colour for %s" % self.tbl.item(r, 0).text())
        if col.isValid():
            it.setBackground(col)
            it.setData(Qt.UserRole, [[col.red(), col.green(), col.blue()], op])

    def _add_row(self):
        self._insert(["New colour", (180, 180, 180), 1.0, "", ""])
        self.tbl.scrollToBottom()

    def _del_row(self):
        r = self.tbl.currentRow()
        if r >= 0:
            self.tbl.removeRow(r)

    def _reset_palette(self):
        self._fill_palette([list(r) for r in DEFAULT_PALETTE])

    def _read(self):
        s = dict(self.s)
        s['layers_on'] = self.cb_layers.isChecked()
        s['colours_on'] = self.cb_colours.isChecked()
        s['repaint'] = self.cb_repaint.isChecked()
        pal = []
        for r in range(self.tbl.rowCount()):
            name = (self.tbl.item(r, 0).text() if self.tbl.item(r, 0) else "").strip()
            if not name:
                continue
            rgb, op = self.tbl.item(r, 1).data(Qt.UserRole)
            pal.append([name, tuple(int(c) for c in rgb), float(op),
                        self.tbl.item(r, 2).text() if self.tbl.item(r, 2) else "",
                        self.tbl.item(r, 3).text() if self.tbl.item(r, 3) else ""])
        s['palette'] = pal
        layers = {}
        for r in range(self.tbl_layers.rowCount()):
            layers[self.tbl_layers.item(r, 0).text()] = self.tbl_layers.item(r, 1).text().strip()
        s['layers'] = layers
        return s

    def _save_close(self):
        self.s = self._read()
        save_settings(self.s)
        self.accept()

    # apply to selected ---------------------------------------------------
    def _apply_selected(self):
        vp = self.viewport
        scene = getattr(vp, 'scene', None)
        sel = [g for g in (getattr(scene, 'selection', None) or ())
               if hasattr(g, 'children') or hasattr(g, 'mesh')]
        top = set(id(g) for g in (getattr(scene, 'groups', None) or []))
        sel = [g for g in sel if id(g) in top or hasattr(g, 'children')]
        if not sel:
            QMessageBox.information(self, PLUGIN_NAME, "Select one or more groups first.")
            return
        s = self._read()
        save_settings(s)
        self.s = s
        layer_choice = self.cmb_layer.currentText().strip()
        if layer_choice == self.KEEP:
            layer_choice = ""
        colour = self.cb_sel_colour.isChecked()
        repaint = self.cb_repaint.isChecked()
        done = {'groups': 0, 'faces': 0}

        def mutate(sc):
            for g in sel:
                plugin = _plugin_of(g)
                layer = layer_choice or getattr(g, 'layer', '') or s['layers'].get(plugin, "")
                if layer and id(g) in top:          # only a top-level group's layer counts
                    ensure_layer(sc, layer)
                    g.layer = layer
                if colour:
                    done['faces'] += colour_group(sc, g, plugin, s['palette'], repaint=repaint)
                done['groups'] += 1

        try:
            vp.history.execute(SnapshotImport(mutate))
        except Exception as e:
            QMessageBox.warning(self, PLUGIN_NAME, "Could not do it:\n%s" % e)
            return
        try:
            vp.notify_scene_changed()
        except Exception:
            pass
        self.lbl.setStyleSheet("color: #2e7d32;")
        self.lbl.setText("Done: %d group(s), %d face(s) coloured. Ctrl+Z undoes it in one go."
                         % (done['groups'], done['faces']))


class LayersColoursTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+V"
    description = ("Puts what the 3D plugins build on a layer for each kind of work and colours each "
                   "part by what it is (brick, slate, glass, ironwork...); can also organise groups "
                   "already in the model.")
    _dialog = None

    def on_activate(self, viewport):
        dlg = LayersColoursTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.raise_()
                    dlg.activateWindow()
                    return
            except Exception:
                pass
        dlg = LayersColoursTool._dialog = LayersColoursDialog(viewport)

        def closed(*_):
            LayersColoursTool._dialog = None
        dlg.finished.connect(closed)
        dlg.show()

    def on_deactivate(self, viewport):
        pass


def run(viewport=None):
    LayersColoursTool().on_activate(viewport)
