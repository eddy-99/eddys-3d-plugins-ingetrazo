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
* Colours / Roofs: each part is painted with a material named after what it is - "Eddy - Brick",
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
VERSION = "5.12"   # 5.12: glass is solid dark blue-grey (like real windows from outside) - see-through glass showed patchy shading where you look through one window and another behind it; 5.11: colours for the new shop front styles - black glass (Vitrolite), chrome & aluminium, bronze, gilt, bow window glass; 5.10: the layers are kept in A to Z order (IngeTrazo\'s own first layer stays at the top); 5.9: shop fronts fawn, their sign lettering dark maroon; 5.8: colours and a layer for 3D Shop Fronts (shop front paint, gilt sign lettering, stallriser tiles, polished granite); 5.7: new builds always take the colour set here; 5.6: Save also changes the colour of that material in the open model, so the next build comes out in the new colour (it stayed the old one, e.g. black pipework); 5.5: the view re-reads the colours, as the Paint tool makes it; 5.4: the new colours show straight away, and Ctrl+Z takes them off again; 5.3: Repaint also recolours parts already wearing one of these colours (windows built into a wall); 5.2: Repaint really repaints; 5.1: parts in a whole house go by their own group   # 5.2: Repaint really repaints (the old colour was left on and still showed); 5.1: Apply to selected colours each part by the plugin its own group came from (windows, doors... inside a whole house)
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
    "3D Shop Fronts": "Shop fronts",
}

# (material, colour 0-255, opacity, words in a part's name that pick it, only for these plugins)
# The first one whose word is in the part's name wins, so the narrow ones come first.
DEFAULT_PALETTE = [
    ("Fascia & barge boards", (240, 230, 200), 1.0, "fascia, barge, soffit", ""),
    ("Glass", (82, 100, 112), 1.0, "glass, pane, light", ""),   # solid: see-through glass shows patches
    ("Ironmongery", (40, 40, 42), 1.0, "handle, hinge, knob, latch, letter, knocker, vane, finial", ""),
    ("Black glass (Vitrolite)", (32, 32, 36), 1.0, "vitrolite, black", ""),
    ("Chrome & aluminium", (198, 202, 206), 1.0, "chrome, aluminium", ""),
    ("Bronze", (140, 100, 52), 1.0, "bronze", ""),
    ("Gilt", (214, 178, 84), 1.0, "gilt", ""),
    ("Bow window glass", (70, 86, 98), 1.0, "bowfront", ""),
    ("Sign lettering", (96, 30, 40), 1.0, "lettering", ""),
    ("Stallriser tiles", (40, 86, 70), 1.0, "tiling", ""),
    ("Polished granite", (150, 146, 148), 1.0, "granite", ""),
    ("Shop front paint", (222, 196, 150), 1.0, "shop, stallriser, pilaster, console", ""),
    ("Chimney pot", (184, 108, 72), 1.0, "pot", "3D Chimneys"),
    ("Lead", (115, 120, 128), 1.0, "flashing, lead, roll", ""),
    ("Mortar", (200, 194, 178), 1.0, "mortar, flaunching, render, pointing", ""),
    ("Pipework", (38, 38, 40), 1.0, "gutter, downpipe, pipe, hopper, shoe, swan, bend, branch, stack, clip", "3D Gutters & Downpipes, 3D Soil & Waste Pipes"),
    ("Canopy ironwork", (46, 92, 68), 1.0, "column, bracket, beam, spandrel, girder, truss, post", "3D Station Canopies"),
    ("Valance", (234, 222, 184), 1.0, "valance", ""),
    ("Window paint", (238, 236, 226), 1.0, "frame, sash, bar, cill, sill, casement, window, mullion, transom", "3D Period Windows"),
    ("Door paint", (60, 82, 70), 1.0, "door, leaf, panel, frame, rail, stile, muntin, fanlight", "3D Period Doors"),
    ("Galvanised iron", (158, 166, 170), 1.0, "corrugated, sheet, tin, iron", ""),
    ("Roof tiles", (186, 96, 62), 1.0, "tile, pantile", ""),
    ("Slate", (84, 90, 102), 1.0, "slate, roof, ridge, hip, verge", ""),
    ("Brick", (168, 80, 56), 1.0, "brick, brickwork, chimney, pier, oversailing, arch", ""),
    ("Stone", (204, 196, 178), 1.0, "block, stone, coping, cill, sill, lintel, plinth, cap, quoin, kerb, string, band, base", ""),
    ("Timber", (140, 102, 66), 1.0, "plank, board, timber, fence, gate, picket, post, rail, weather, cladding, batten", ""),
]

# rows added since version 1: put into a palette you saved before they were there
NEW_ROWS = ("Fascia & barge boards", "Roof tiles", "Sign lettering", "Stallriser tiles", "Polished granite", "Shop front paint",
            "Black glass (Vitrolite)", "Chrome & aluminium", "Bronze", "Gilt", "Bow window glass")

# The colours shown on the Roofs tab (the rest are on the Colours tab). A colour you add on
# the Roofs tab is kept there.
ROOF_ROWS = ("Fascia & barge boards", "Lead", "Galvanised iron", "Roof tiles", "Slate")


def _is_roof(row):
    if len(row) > 5:
        return row[5] == "roof"
    return row[0] in ROOF_ROWS


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
    "3D Shop Fronts": "Shop front paint",
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
                    row = [str(r[0]), tuple(int(c) for c in r[1][:3]), float(r[2]), str(r[3]),
                                str(r[4]) if len(r) > 4 else ""]
                    if len(r) > 5:
                        row.append(str(r[5]))
                    if row[0] == "Glass" and row[1] == (176, 196, 206) and abs(row[2] - 0.35) < 1e-6:
                        row[1], row[2] = (82, 100, 112), 1.0     # the old see-through glass: the new solid one
                    pal.append(row)
                except Exception:
                    pass
            if pal:
                # rows added in a newer version go in too (at the place they have in the list)
                have = {r[0] for r in pal}
                for i, r in enumerate(DEFAULT_PALETTE):
                    if r[0] not in have and r[0] in NEW_ROWS:
                        pal.insert(min(i, len(pal)), list(r))
                s['palette'] = pal
    except Exception:
        pass
    return s


def save_settings(s):
    try:
        out = dict(s)
        out['palette'] = [[r[0], list(r[1]), r[2], r[3], r[4], "roof" if _is_roof(r) else ""]
                          for r in s['palette']]
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
    if name not in {getattr(ly, 'name', None) for ly in layers}:
        from core.layers import Layer
        layers.append(Layer(name))
    sort_layers(scene)


def sort_layers(scene):
    """Puts the layers in A to Z order, so they're easy to find. IngeTrazo's own first layer stays at
    the top, and the layer you're working on stays the one you're working on."""
    layers = getattr(scene, 'layers', None)
    if not isinstance(layers, list) or len(layers) < 3:
        return
    rest = layers[1:]
    want = sorted(rest, key=lambda ly: (getattr(ly, 'name', '') or '').lower())
    if all(a is b for a, b in zip(rest, want)):
        return
    keep = {}
    for attr in ('current_layer', 'active_layer', 'layer_index', 'current'):
        val = getattr(scene, attr, None)
        if isinstance(val, int) and not isinstance(val, bool) and 0 <= val < len(layers):
            keep[attr] = layers[val]          # remembered by its place in the list: find it again after
    try:
        layers[1:] = want
    except Exception as e:
        print("%s: couldn't sort the layers: %s" % (PLUGIN_NAME, e))
        return
    for attr, ly in keep.items():
        try:
            setattr(scene, attr, next(i for i, x in enumerate(layers) if x is ly))
        except Exception:
            pass


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
            if only and plugin and plugin.lower() not in only:
                continue                # (when it isn't known which plugin made it, any row will do)
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
    by_mat = {MAT_PREFIX + r[0]: r for r in palette} if repaint else {}
    if repaint:
        mats = getattr(scene, 'materials', None) or {}
        for r in palette:                    # the document's own materials take the new colours too
            if MAT_PREFIX + r[0] in mats:
                _paint_attrs(scene, r, True)

    def walk(g, names, pl):
        nonlocal count
        names = [getattr(g, 'name', '') or ''] + names
        # a house built by several plugins: each part goes by the plugin its own group came
        # from (a window's group, a door's group...), not just the group that was selected
        if not plugin:                     # (a plugin building its own work says which it is)
            pl = pl or _plugin_of(g)
        faces = _faces(g)
        if faces and repaint and by_mat:
            # faces already wearing one of our colours (a window built into a wall, say) take
            # the new colour of that material, whatever their group is called
            for f in faces:
                a = getattr(f, 'attrs', None) or {}
                r = by_mat.get(a.get('mat'))
                if r is not None:
                    a = dict(a)
                    a['color'] = tuple(c / 255.0 for c in r[1])
                    a['opacity'] = float(r[2])
                    f.attrs = a
                    count += 1
        if faces:
            row = _pick_row(palette, names, pl)
            if row is not None:
                if row[0] not in cache:
                    pa = dict(_paint_attrs(scene, row, repaint))
                    # the colour set here wins, even if the model's material of that name is an
                    # older colour (new pipework kept coming out black)
                    pa['color'] = tuple(c / 255.0 for c in row[1])
                    pa['opacity'] = float(row[2])
                    cache[row[0]] = pa
                paint = cache[row[0]]
                for f in faces:
                    a = dict(getattr(f, 'attrs', None) or {})
                    if not repaint and ('color' in a or 'mat' in a or 'texture' in a):
                        continue
                    if repaint:
                        # the old colour has to go, or it still shows over the new material
                        for k in ('texture', 'color', 'mat', 'opacity'):
                            a.pop(k, None)
                    a.update(paint)
                    f.attrs = a
                    count += 1
        for c in _children(g):
            walk(c, names, pl)

    walk(group, [], plugin)
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
    guesses = [("shop front", "3D Shop Fronts"), ("chimney", "3D Chimneys"), ("pot", "3D Chimneys"), ("vent", "3D Chimneys"),
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


def _paint_command(mutate, meshes):
    """One undo step for recolouring faces already in the model. It keeps the meshes as they
    were and as they end up (like IngeTrazo's own tools do), and tells the view the model has
    changed so the new colours show straight away."""
    try:
        from core.history import Command
    except Exception:
        Command = None
    if Command is None or not all(hasattr(m, 'capture_state') for m in meshes):
        return SnapshotImport(mutate)

    class PaintCommand(Command):
        def __init__(self):
            self.before = self.after = None

        @staticmethod
        def _bump(scene):
            # colours changed outside IngeTrazo's own mesh edits: tell the view to re-read them
            # (what IngeTrazo's Paint tool does too), or the old colours stay on screen
            try:
                from core.history import _dirty_group_chunks
                _dirty_group_chunks(scene)
            except Exception:
                for g in getattr(scene, 'groups', None) or []:
                    m = getattr(g, 'mesh', None)
                    for flag in ('_chunk_dirty', '_attrs_dirty'):
                        try:
                            setattr(m, flag, True)
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


# ---------------------------------------------------------------------------
# The dialog
# ---------------------------------------------------------------------------
class LayersColoursDialog(QDialog):
    KEEP = "(keep each group's layer, or the plugin's)"

    def __init__(self, viewport):
        super().__init__(viewport)
        self.viewport = viewport
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
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

        # colours, and the roof colours on a tab of their own
        note_text = ("Click a colour to change it. A part takes the first colour with one of its words in "
                     "its name (whole words; plurals count). Each is a material named \"%s...\": it is only "
                     "made if the document hasn't got one, so a colour you change in IngeTrazo stays yours."
                     % MAT_PREFIX)
        self.tbl = self._colour_tab(tabs, "Colours", note_text)
        self.tbl_roof = self._colour_tab(tabs, "Roofs", "The colours for roofs: clay tiles, slates, ridges, "
                                         "tin sheets, lead and the fascia and barge boards. " + note_text)
        self._tabs = tabs
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

    # palette tables ----------------------------------------------------
    def _colour_tab(self, tabs, title, text):
        w = QWidget()
        v = QVBoxLayout(w)
        note = QLabel(text)
        note.setWordWrap(True)
        v.addWidget(note)
        tbl = QTableWidget(0, 4)
        tbl.setHorizontalHeaderLabels(["Material", "Colour", "Words in the part's name", "Only for"])
        tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.cellClicked.connect(lambda r, c, t=tbl: self._cell_clicked(t, r, c))
        v.addWidget(tbl, 1)
        row_btns = QHBoxLayout()
        b_add = QPushButton("Add colour")
        b_add.clicked.connect(lambda _=False, t=tbl: self._add_row(t))
        b_del = QPushButton("Remove")
        b_del.clicked.connect(lambda _=False, t=tbl: self._del_row(t))
        b_reset = QPushButton("Back to the standard colours")
        b_reset.setToolTip("Puts the standard colours back on both the Colours and Roofs tabs")
        b_reset.clicked.connect(self._reset_palette)
        row_btns.addWidget(b_add)
        row_btns.addWidget(b_del)
        row_btns.addStretch(1)
        row_btns.addWidget(b_reset)
        v.addLayout(row_btns)
        tabs.addTab(w, title)
        return tbl

    def _fill_palette(self, palette):
        self.tbl.setRowCount(0)
        self.tbl_roof.setRowCount(0)
        self._next = 0
        for row in palette:
            self._insert(self.tbl_roof if _is_roof(row) else self.tbl, row)

    def _insert(self, tbl, row):
        # each row remembers its place in the whole list, as the first colour that fits wins
        r = tbl.rowCount()
        tbl.insertRow(r)
        name = QTableWidgetItem(row[0])
        name.setData(Qt.UserRole, self._next)
        self._next += 1
        tbl.setItem(r, 0, name)
        sw = QTableWidgetItem("  %d%%" % round(row[2] * 100) if row[2] < 1 else "")
        sw.setBackground(QColor(*row[1]))
        sw.setData(Qt.UserRole, [list(row[1]), row[2]])        # Qt.UserRole
        sw.setFlags(sw.flags() & ~Qt.ItemIsEditable)
        sw.setToolTip("Click to change")
        tbl.setItem(r, 1, sw)
        tbl.setItem(r, 2, QTableWidgetItem(row[3]))
        tbl.setItem(r, 3, QTableWidgetItem(row[4] if len(row) > 4 else ""))

    def _cell_clicked(self, tbl, r, c):
        if c != 1:
            return
        it = tbl.item(r, 1)
        rgb, op = it.data(Qt.UserRole)
        col = QColorDialog.getColor(QColor(*rgb), self, "Colour for %s" % tbl.item(r, 0).text())
        if col.isValid():
            it.setBackground(col)
            it.setData(Qt.UserRole, [[col.red(), col.green(), col.blue()], op])

    def _add_row(self, tbl):
        self._insert(tbl, ["New colour", (180, 180, 180), 1.0, "", ""])
        tbl.scrollToBottom()

    def _del_row(self, tbl):
        r = tbl.currentRow()
        if r >= 0:
            tbl.removeRow(r)

    def _reset_palette(self):
        self._fill_palette([list(r) for r in DEFAULT_PALETTE])

    def _read(self):
        s = dict(self.s)
        s['layers_on'] = self.cb_layers.isChecked()
        s['colours_on'] = self.cb_colours.isChecked()
        s['repaint'] = self.cb_repaint.isChecked()
        found = []
        for tbl, tab in ((self.tbl, ""), (self.tbl_roof, "roof")):
            for r in range(tbl.rowCount()):
                it = tbl.item(r, 0)
                name = (it.text() if it else "").strip()
                if not name:
                    continue
                place = it.data(Qt.UserRole)
                rgb, op = tbl.item(r, 1).data(Qt.UserRole)
                found.append((place if place is not None else 1e9, tab == "roof", r,
                              [name, tuple(int(c) for c in rgb), float(op),
                               tbl.item(r, 2).text() if tbl.item(r, 2) else "",
                               tbl.item(r, 3).text() if tbl.item(r, 3) else "", tab]))
        found.sort(key=lambda x: (x[0], x[1], x[2]))         # back in the order they had
        s['palette'] = [x[3] for x in found]
        layers = {}
        for r in range(self.tbl_layers.rowCount()):
            layers[self.tbl_layers.item(r, 0).text()] = self.tbl_layers.item(r, 1).text().strip()
        s['layers'] = layers
        return s

    def _save_close(self):
        old = {r[0]: (tuple(r[1]), float(r[2])) for r in self.s.get('palette', [])}
        self.s = self._read()
        save_settings(self.s)
        # a colour changed here: the open model's own material of that name takes it too,
        # or the next build would still come out in the model's old colour
        try:
            scene = getattr(self.viewport, 'scene', None)
            mats = getattr(scene, 'materials', None) or {}
            changed = 0
            for r in self.s['palette']:
                if old.get(r[0]) != (tuple(r[1]), float(r[2])) and (MAT_PREFIX + r[0]) in mats:
                    _paint_attrs(scene, r, True)
                    changed += 1
            if changed:
                try:
                    scene.version += 1
                except Exception:
                    pass
        except Exception as e:
            print("%s: updating the model's colours: %s" % (PLUGIN_NAME, e))
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
                    done['faces'] += colour_group(sc, g, "", s['palette'], repaint=repaint)
                done['groups'] += 1

        meshes = []

        def gather(g):
            m = getattr(g, 'mesh', None)
            if m is not None and all(m is not x for x in meshes):
                meshes.append(m)
            for c in _children(g):
                gather(c)

        for g in sel:
            gather(g)
        try:
            vp.history.execute(_paint_command(mutate, meshes))
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
