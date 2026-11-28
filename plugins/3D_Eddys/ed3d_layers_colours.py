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
                               QWidget, QColorDialog, QComboBox, QFormLayout, QAbstractItemView,
                               QLineEdit, QListWidget, QListWidgetItem)
from PySide6.QtGui import QPixmap, QIcon

PLUGIN_NAME = "3D Layers & Colours"
VERSION = "5.26"   # 5.26: colours and a layer for 3D Signs & Boards (maroon board, cream letters and border, brass lamps); 5.25: a part painted all in one colour by its name before (gables that came out slate) takes its new colour on Apply to selected - it kept the old one; 5.24: a Gables colour of its own (walls with a gable on - gable ends and the fronts of the roof gables), before Walls; 5.23: a Floors colour (floor panels); 5.22: a colour marked Only for one plugin is only used on that plugin work (floor panels came out door green), and Apply to selected puts a part wrongly wearing one back to plain; 5.21: a Walls colour (plain walls and gables - they had no colour of their own, so they could not be changed); Apply to selected leaves windows, doors and sills in a wall their own colours while it colours the wall; 5.20: Save no longer closes the window (only Close does) - it says Saved instead; 5.19: Pick from screen - an eyedropper in the colour list: click anywhere on the screen (the model, a photo of the real building) to take that colour; 5.18: a Find box at the top - type window, door, brick, glass... and only those colours show (on whichever tab they are); 5.17: clicking a colour opens a list of the 213 RAL Classic colours with a search box (type cream, green, slate or a RAL number), and My own colour... for the usual chooser; 5.16: the view really redraws the new colours (each recoloured part is put back the way Undo does it, which the view always redraws); 5.15: recoloured parts deep inside a building (boards in a Boards group) show their new colour straight away - they changed but the view kept the old one; 5.14: Save recolours what is already built even when the model own material list doesn\'t show the colour, and says so if it can\'t; 5.13: Save recolours everything already in the model that wears one of these colours in an older shade (barge boards stayed their old colour - each face keeps its own copy); Ctrl+Z puts it back; 5.12: glass is solid dark blue-grey (like real windows from outside) - see-through glass showed patchy shading where you look through one window and another behind it; 5.11: colours for the new shop front styles - black glass (Vitrolite), chrome & aluminium, bronze, gilt, bow window glass; 5.10: the layers are kept in A to Z order (IngeTrazo\'s own first layer stays at the top); 5.9: shop fronts fawn, their sign lettering dark maroon; 5.8: colours and a layer for 3D Shop Fronts (shop front paint, gilt sign lettering, stallriser tiles, polished granite); 5.7: new builds always take the colour set here; 5.6: Save also changes the colour of that material in the open model, so the next build comes out in the new colour (it stayed the old one, e.g. black pipework); 5.5: the view re-reads the colours, as the Paint tool makes it; 5.4: the new colours show straight away, and Ctrl+Z takes them off again; 5.3: Repaint also recolours parts already wearing one of these colours (windows built into a wall); 5.2: Repaint really repaints; 5.1: parts in a whole house go by their own group   # 5.2: Repaint really repaints (the old colour was left on and still showed); 5.1: Apply to selected colours each part by the plugin its own group came from (windows, doors... inside a whole house)
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
    "3D Signs & Boards": "Signs",
}

# (material, colour 0-255, opacity, words in a part's name that pick it, only for these plugins)
# The first one whose word is in the part's name wins, so the narrow ones come first.
DEFAULT_PALETTE = [
    ("Sign board lettering", (240, 236, 224), 1.0, "lettering", "3D Signs & Boards"),
    ("Sign boards", (110, 36, 52), 1.0, "sign", "3D Signs & Boards"),
    ("Brass lamps", (196, 156, 64), 1.0, "lamp", "3D Signs & Boards"),
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
    ("Gables", (200, 198, 190), 1.0, "gable", ""),
    ("Walls", (200, 198, 190), 1.0, "wall", ""),
    ("Floors", (176, 168, 150), 1.0, "floor, ceiling", ""),
]

# rows added since version 1: put into a palette you saved before they were there
NEW_ROWS = ("Fascia & barge boards", "Roof tiles", "Sign lettering", "Stallriser tiles", "Polished granite", "Shop front paint",
            "Black glass (Vitrolite)", "Chrome & aluminium", "Bronze", "Gilt", "Bow window glass", "Gables", "Walls", "Floors",
            "Sign board lettering", "Sign boards", "Brass lamps")

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
                    if row[0] == "Walls" and row[3].replace(" ", "") == "wall,gable":
                        row[3] = "wall"                          # gables have a colour of their own now
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
            if only and (not plugin or plugin.lower() not in only):
                continue                # a row only for one plugin: only for that plugin's work (a
                                        # building's floor panels were taking the door colour)
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
        mats_here = {(getattr(f, 'attrs', None) or {}).get('mat') for f in faces}
        all_one = len(mats_here) == 1 and None not in mats_here    # the whole part in one colour (painted
        #                                       by its name), not a door built into a wall among others
        if faces and repaint and by_mat:
            # faces already wearing one of our colours (a window built into a wall, say) take
            # the new colour of that material, whatever their group is called
            for f in faces:
                a = getattr(f, 'attrs', None) or {}
                r = by_mat.get(a.get('mat'))
                only = _words(r[4]) if r is not None and len(r) > 4 else []
                if r is not None and only and (pl.lower() not in only if pl else all_one):
                    # wearing a colour that's only for another plugin's work (a floor panel that
                    # took the door colour): back to plain
                    a = dict(a)
                    for k in ('texture', 'color', 'mat', 'opacity'):
                        a.pop(k, None)
                    f.attrs = a
                    count += 1
                    continue
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
                    if repaint and a.get('mat') in by_mat and not all_one:
                        continue     # a window, door or sill set into a wall: its own colour, done above
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
                scene._dirty_group_chunks = True
            except Exception:
                pass
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
            # and every mesh recoloured, however deep its group (boards inside a building's
            # "Boards - wall 1" group kept their old colour on screen)
            for m in meshes:
                for flag in ('_chunk_dirty', '_attrs_dirty', '_dirty', 'dirty'):
                    try:
                        setattr(m, flag, True)
                    except Exception:
                        pass
                for meth in ('mark_dirty', 'invalidate', 'touch', 'changed'):
                    fn = getattr(m, meth, None)
                    if callable(fn):
                        try:
                            fn()
                        except Exception:
                            pass
                try:
                    m.version += 1
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
                for m, s_ in self.after:
                    try:
                        m.restore_state(s_)          # the way Undo / Redo put colours back - and the
                    except Exception:                # view redraws after those, so it does now too
                        pass
            else:
                for m, s in self.after:
                    m.restore_state(s)
            self._bump(scene)

        def undo(self, scene):
            for m, s in self.before:
                m.restore_state(s)
            self._bump(scene)

    return PaintCommand()


RAL_COLOURS = (   # RAL Classic: number, on-screen colour (approximate), name
    ("1000", "#CCC58F", "Green beige"),
    ("1001", "#D1BC8A", "Beige"),
    ("1002", "#D2B773", "Sand yellow"),
    ("1003", "#F7BA0B", "Signal yellow"),
    ("1004", "#E2B007", "Golden yellow"),
    ("1005", "#C89F04", "Honey yellow"),
    ("1006", "#E1A100", "Maize yellow"),
    ("1007", "#E79C00", "Daffodil yellow"),
    ("1011", "#AF8A54", "Brown beige"),
    ("1012", "#D9C022", "Lemon yellow"),
    ("1013", "#E9E5CE", "Oyster white"),
    ("1014", "#DFCEA1", "Ivory"),
    ("1015", "#EADEBD", "Light ivory"),
    ("1016", "#EAF044", "Sulfur yellow"),
    ("1017", "#F4B752", "Saffron yellow"),
    ("1018", "#F3E03B", "Zinc yellow"),
    ("1019", "#A4957D", "Grey beige"),
    ("1020", "#9A9464", "Olive yellow"),
    ("1021", "#EEC900", "Rape yellow"),
    ("1023", "#F0CA00", "Traffic yellow"),
    ("1024", "#B89C50", "Ochre yellow"),
    ("1026", "#F5FF00", "Luminous yellow"),
    ("1027", "#A38C15", "Curry"),
    ("1028", "#FFAB00", "Melon yellow"),
    ("1032", "#DDB20F", "Broom yellow"),
    ("1033", "#FAAB21", "Dahlia yellow"),
    ("1034", "#EDAB56", "Pastel yellow"),
    ("1035", "#A29985", "Pearl beige"),
    ("1036", "#927549", "Pearl gold"),
    ("1037", "#EEA205", "Sun yellow"),
    ("2000", "#DD7907", "Yellow orange"),
    ("2001", "#BE4E20", "Red orange"),
    ("2002", "#C63927", "Vermillion"),
    ("2003", "#FA842B", "Pastel orange"),
    ("2004", "#E75B12", "Pure orange"),
    ("2005", "#FF2300", "Luminous orange"),
    ("2007", "#FFA421", "Luminous bright orange"),
    ("2008", "#F3752C", "Bright red orange"),
    ("2009", "#E15501", "Traffic orange"),
    ("2010", "#D4652F", "Signal orange"),
    ("2011", "#EC7C25", "Deep orange"),
    ("2012", "#DB6A50", "Salmon orange"),
    ("2013", "#954527", "Pearl orange"),
    ("3000", "#AB2524", "Flame red"),
    ("3001", "#A02128", "Signal red"),
    ("3002", "#A1232B", "Carmine red"),
    ("3003", "#8D1D2C", "Ruby red"),
    ("3004", "#701F29", "Purple red"),
    ("3005", "#5E2028", "Wine red"),
    ("3007", "#402225", "Black red"),
    ("3009", "#703731", "Oxide red"),
    ("3011", "#7E292C", "Brown red"),
    ("3012", "#CB8D73", "Beige red"),
    ("3013", "#9C322E", "Tomato red"),
    ("3014", "#D47479", "Antique pink"),
    ("3015", "#E1A6AD", "Light pink"),
    ("3016", "#AC4034", "Coral red"),
    ("3017", "#D3545F", "Rose"),
    ("3018", "#D14152", "Strawberry red"),
    ("3020", "#C1121C", "Traffic red"),
    ("3022", "#D56D56", "Salmon pink"),
    ("3024", "#F70000", "Luminous red"),
    ("3026", "#FF0000", "Luminous bright red"),
    ("3027", "#B42041", "Raspberry red"),
    ("3028", "#E72512", "Pure red"),
    ("3031", "#AC323B", "Orient red"),
    ("3032", "#711521", "Pearl ruby red"),
    ("3033", "#B24C43", "Pearl pink"),
    ("4001", "#8A5A83", "Red lilac"),
    ("4002", "#933D50", "Red violet"),
    ("4003", "#D15B8F", "Heather violet"),
    ("4004", "#691639", "Claret violet"),
    ("4005", "#83639D", "Blue lilac"),
    ("4006", "#992572", "Traffic purple"),
    ("4007", "#4A203B", "Purple violet"),
    ("4008", "#904684", "Signal violet"),
    ("4009", "#A38995", "Pastel violet"),
    ("4010", "#C63678", "Telemagenta"),
    ("4011", "#8773A1", "Pearl violet"),
    ("4012", "#6B6880", "Pearl blackberry"),
    ("5000", "#384C70", "Violet blue"),
    ("5001", "#1F4764", "Green blue"),
    ("5002", "#2B2C7C", "Ultramarine blue"),
    ("5003", "#2A3756", "Sapphire blue"),
    ("5004", "#1D1F2A", "Black blue"),
    ("5005", "#154889", "Signal blue"),
    ("5007", "#41678D", "Brilliant blue"),
    ("5008", "#313C48", "Grey blue"),
    ("5009", "#2E5978", "Azure blue"),
    ("5010", "#13447C", "Gentian blue"),
    ("5011", "#232C3F", "Steel blue"),
    ("5012", "#3481B8", "Light blue"),
    ("5013", "#232D53", "Cobalt blue"),
    ("5014", "#6C7C98", "Pigeon blue"),
    ("5015", "#2874B2", "Sky blue"),
    ("5017", "#0E518D", "Traffic blue"),
    ("5018", "#21888F", "Turquoise blue"),
    ("5019", "#1A5784", "Capri blue"),
    ("5020", "#0B4151", "Ocean blue"),
    ("5021", "#07737A", "Water blue"),
    ("5022", "#2F2A5A", "Night blue"),
    ("5023", "#4D668E", "Distant blue"),
    ("5024", "#6A93B0", "Pastel blue"),
    ("5025", "#296478", "Pearl gentian blue"),
    ("5026", "#102C54", "Pearl night blue"),
    ("6000", "#327662", "Patina green"),
    ("6001", "#28713E", "Emerald green"),
    ("6002", "#276235", "Leaf green"),
    ("6003", "#4B573E", "Olive green"),
    ("6004", "#0E4243", "Blue green"),
    ("6005", "#0F4336", "Moss green"),
    ("6006", "#40433B", "Grey olive"),
    ("6007", "#283424", "Bottle green"),
    ("6008", "#35382E", "Brown green"),
    ("6009", "#26392F", "Fir green"),
    ("6010", "#3E753B", "Grass green"),
    ("6011", "#68825B", "Reseda green"),
    ("6012", "#31403D", "Black green"),
    ("6013", "#797C5A", "Reed green"),
    ("6014", "#444337", "Yellow olive"),
    ("6015", "#3D403A", "Black olive"),
    ("6016", "#026A52", "Turquoise green"),
    ("6017", "#468641", "May green"),
    ("6018", "#48A43F", "Yellow green"),
    ("6019", "#B7D9B1", "Pastel green"),
    ("6020", "#354733", "Chrome green"),
    ("6021", "#86A47C", "Pale green"),
    ("6022", "#3E3C32", "Brown olive"),
    ("6024", "#008754", "Traffic green"),
    ("6025", "#53753C", "Fern green"),
    ("6026", "#005D52", "Opal green"),
    ("6027", "#81C0BB", "Light green"),
    ("6028", "#2D5546", "Pine green"),
    ("6029", "#007243", "Mint green"),
    ("6032", "#0F8558", "Signal green"),
    ("6033", "#478A84", "Mint turquoise"),
    ("6034", "#7FB0B2", "Pastel turquoise"),
    ("6035", "#1B542C", "Pearl green"),
    ("6036", "#005D4C", "Pearl opal green"),
    ("6037", "#25E712", "Pure green"),
    ("6038", "#00F700", "Luminous green"),
    ("7000", "#7E8B92", "Squirrel grey"),
    ("7001", "#8F999F", "Silver grey"),
    ("7002", "#817F68", "Olive grey"),
    ("7003", "#7A7B6D", "Moss grey"),
    ("7004", "#9EA0A1", "Signal grey"),
    ("7005", "#6B716F", "Mouse grey"),
    ("7006", "#756F61", "Beige grey"),
    ("7008", "#746643", "Khaki grey"),
    ("7009", "#5B6259", "Green grey"),
    ("7010", "#575D57", "Tarpaulin grey"),
    ("7011", "#555D61", "Iron grey"),
    ("7012", "#596163", "Basalt grey"),
    ("7013", "#555548", "Brown grey"),
    ("7015", "#51565C", "Slate grey"),
    ("7016", "#373F43", "Anthracite grey"),
    ("7021", "#2E3234", "Black grey"),
    ("7022", "#4B4D46", "Umbra grey"),
    ("7023", "#818479", "Concrete grey"),
    ("7024", "#474A50", "Graphite grey"),
    ("7026", "#374447", "Granite grey"),
    ("7030", "#939388", "Stone grey"),
    ("7031", "#5D6970", "Blue grey"),
    ("7032", "#B9B9A8", "Pebble grey"),
    ("7033", "#818979", "Cement grey"),
    ("7034", "#939176", "Yellow grey"),
    ("7035", "#CBD0CC", "Light grey"),
    ("7036", "#9A9697", "Platinum grey"),
    ("7037", "#7C7F7E", "Dusty grey"),
    ("7038", "#B4B8B0", "Agate grey"),
    ("7039", "#6B695F", "Quartz grey"),
    ("7040", "#9DA3A6", "Window grey"),
    ("7042", "#8F9695", "Traffic grey A"),
    ("7043", "#4E5451", "Traffic grey B"),
    ("7044", "#BDBDB2", "Silk grey"),
    ("7045", "#91969A", "Telegrey 1"),
    ("7046", "#82898E", "Telegrey 2"),
    ("7047", "#CFD0CF", "Telegrey 4"),
    ("7048", "#888175", "Pearl mouse grey"),
    ("8000", "#887142", "Green brown"),
    ("8001", "#9C6B30", "Ochre brown"),
    ("8002", "#7B5141", "Signal brown"),
    ("8003", "#80542F", "Clay brown"),
    ("8004", "#8F4E35", "Copper brown"),
    ("8007", "#6F4A2F", "Fawn brown"),
    ("8008", "#6F4F28", "Olive brown"),
    ("8011", "#5A3A29", "Nut brown"),
    ("8012", "#673831", "Red brown"),
    ("8014", "#49392D", "Sepia brown"),
    ("8015", "#633A34", "Chestnut brown"),
    ("8016", "#4C2F26", "Mahogany brown"),
    ("8017", "#44322D", "Chocolate brown"),
    ("8019", "#3F3A3A", "Grey brown"),
    ("8022", "#211F20", "Black brown"),
    ("8023", "#A65E2F", "Orange brown"),
    ("8024", "#79553C", "Beige brown"),
    ("8025", "#755C49", "Pale brown"),
    ("8028", "#4E3B31", "Terra brown"),
    ("8029", "#763C28", "Pearl copper"),
    ("9001", "#FDF4E3", "Cream"),
    ("9002", "#E7EBDA", "Grey white"),
    ("9003", "#F4F4F4", "Signal white"),
    ("9004", "#282828", "Signal black"),
    ("9005", "#0A0A0A", "Jet black"),
    ("9006", "#A5A5A5", "White aluminium"),
    ("9007", "#8F8F8F", "Grey aluminium"),
    ("9010", "#FFFFFF", "Pure white"),
    ("9011", "#1C1C1C", "Graphite black"),
    ("9016", "#F6F6F6", "Traffic white"),
    ("9017", "#1E1E1E", "Traffic black"),
    ("9018", "#D7D7D7", "Papyrus white"),
    ("9022", "#9C9C9C", "Pearl light grey"),
    ("9023", "#828282", "Pearl dark grey"),
)


class ColourPicker(QDialog):
    """Pick a colour: the RAL Classic colours with a search box (type a name like 'cream' or 'green',
    or a number like 6005), or 'My own colour...' for the usual colour chooser."""

    def __init__(self, parent, rgb, title):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(380, 520)
        self.rgb = tuple(rgb)
        v = QVBoxLayout(self)
        self.ed = QLineEdit()
        self.ed.setPlaceholderText("Search - a name (cream, green, slate...) or a RAL number")
        self.ed.setClearButtonEnabled(True)
        v.addWidget(self.ed)
        self.lst = QListWidget()
        v.addWidget(self.lst, 1)
        for num, hx, name in RAL_COLOURS:
            c = QColor(hx)
            pm = QPixmap(28, 18)
            pm.fill(c)
            it = QListWidgetItem(QIcon(pm), "RAL %s  %s" % (num, name))
            it.setData(Qt.UserRole, (c.red(), c.green(), c.blue()))
            self.lst.addItem(it)
        row = QHBoxLayout()
        b_pick = QPushButton("Pick from screen")
        b_pick.setToolTip("Then click anywhere on the screen - the model, a photo, anything - to take its colour "
                          "(Esc to stop)")
        row.addWidget(b_pick)
        b_pick.clicked.connect(self._pick_screen)
        b_own = QPushButton("My own colour...")
        b_ok = QPushButton("OK")
        b_ok.setDefault(True)
        b_cancel = QPushButton("Cancel")
        row.addWidget(b_own)
        row.addStretch(1)
        row.addWidget(b_ok)
        row.addWidget(b_cancel)
        v.addLayout(row)
        self.ed.textChanged.connect(self._filter)
        self.lst.itemDoubleClicked.connect(lambda *_: self._ok())
        b_ok.clicked.connect(self._ok)
        b_cancel.clicked.connect(self.reject)
        b_own.clicked.connect(self._own)
        self.ed.setFocus()

    def _filter(self, text):
        words = text.lower().split()
        first = None
        for i in range(self.lst.count()):
            it = self.lst.item(i)
            show = all(w in it.text().lower() for w in words)
            it.setHidden(not show)
            if show and first is None:
                first = it
        if first is not None:
            self.lst.setCurrentItem(first)

    def _ok(self):
        it = self.lst.currentItem()
        if it is None or it.isHidden():
            return
        self.rgb = tuple(it.data(Qt.UserRole))
        self.accept()

    def _pick_screen(self):
        """An eyedropper: the screen as it is now, shown full size; the colour under the click is taken."""
        from PySide6.QtGui import QGuiApplication, QCursor
        from PySide6.QtWidgets import QApplication
        main = self.parent()
        self.hide()
        if main is not None:
            main.hide()                                  # the Layers & Colours window out of the way too
        QApplication.processEvents()
        import time
        time.sleep(0.25)                                 # this window gone from the picture
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        shot = screen.grabWindow(0)
        img = shot.toImage()
        picker = self

        class Dropper(QDialog):
            def __init__(self):
                super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
                self.got = None
                self.setCursor(Qt.CrossCursor)
                self.setGeometry(screen.geometry())
                self.setMouseTracking(True)
                self.lbl = QLabel(self)
                self.lbl.setStyleSheet("background: #ffffffee; border: 1px solid #555; padding: 4px;")
                self.lbl.setText("Click a colour  (Esc to stop)")
                self.lbl.adjustSize()
                self.lbl.move(20, 20)

            def _at(self, pos):
                dpr = shot.devicePixelRatio() or 1.0
                x = max(0, min(img.width() - 1, int(pos.x() * dpr)))
                y = max(0, min(img.height() - 1, int(pos.y() * dpr)))
                return img.pixelColor(x, y)

            def paintEvent(self, _e):
                from PySide6.QtGui import QPainter
                QPainter(self).drawPixmap(self.rect(), shot)

            def mouseMoveEvent(self, e):
                c = self._at(e.position().toPoint())
                self.lbl.setText("Click a colour  (Esc to stop)   R%d G%d B%d" % (c.red(), c.green(), c.blue()))
                self.lbl.setStyleSheet("background: %s; color: %s; border: 1px solid #555; padding: 4px;"
                                       % (c.name(), "#000" if c.lightness() > 128 else "#fff"))
                self.lbl.adjustSize()
                p = e.position().toPoint()
                self.lbl.move(p.x() + 18, p.y() + 18)

            def mousePressEvent(self, e):
                c = self._at(e.position().toPoint())
                self.got = (c.red(), c.green(), c.blue())
                self.accept()

            def keyPressEvent(self, e):
                if e.key() == Qt.Key_Escape:
                    self.reject()
        d = Dropper()
        d.showFullScreen()
        d.exec()
        if main is not None:
            main.show()
        self.show()
        if d.got:
            picker.rgb = d.got
            picker.accept()

    def _own(self):
        col = QColorDialog.getColor(QColor(*self.rgb), self, self.windowTitle())
        if col.isValid():
            self.rgb = (col.red(), col.green(), col.blue())
            self.accept()


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

        self.ed_find = QLineEdit()
        self.ed_find.setPlaceholderText("Find a colour - type window, door, brick, glass, slate...")
        self.ed_find.setClearButtonEnabled(True)
        lay.addWidget(self.ed_find)
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
        self.ed_find.textChanged.connect(self._find)

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
        self.lbl_saved = QLabel("")
        self.lbl_saved.setStyleSheet("color: #2e7d32;")
        btns.addWidget(self.lbl_saved)
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
        dlg = ColourPicker(self, rgb, "Colour for %s" % tbl.item(r, 0).text())
        col = QColor(*dlg.rgb) if dlg.exec() == QDialog.Accepted else QColor()
        if col.isValid():
            it.setBackground(col)
            it.setData(Qt.UserRole, [[col.red(), col.green(), col.blue()], op])

    def _find(self, text):
        """Only the colours whose name (or words) has what's typed; the tab with them comes up."""
        words = text.lower().split()
        hits = {}
        for tbl in (self.tbl, self.tbl_roof):
            n = 0
            for r in range(tbl.rowCount()):
                txt = " ".join((tbl.item(r, c).text() if tbl.item(r, c) else "") for c in (0, 2)).lower()
                show = all(w in txt for w in words)
                tbl.setRowHidden(r, not show)
                n += show
            hits[id(tbl)] = n
        if words:
            if hits[id(self.tbl)] == 0 and hits[id(self.tbl_roof)] > 0:
                self._tabs.setCurrentIndex(1)
            elif hits[id(self.tbl)] > 0 and self._tabs.currentIndex() not in (0, 1):
                self._tabs.setCurrentIndex(0)
            elif hits[id(self.tbl)] > 0 and hits[id(self.tbl_roof)] == 0:
                self._tabs.setCurrentIndex(0)

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
            changed = {}
            for r in self.s['palette']:
                if old.get(r[0]) != (tuple(r[1]), float(r[2])) and (MAT_PREFIX + r[0]) in mats:
                    _paint_attrs(scene, r, True)
                    changed[MAT_PREFIX + r[0]] = r
            if changed:
                try:
                    scene.version += 1
                except Exception:
                    pass
            # every face wearing one of these colours, but still in an older shade of it, takes the
            # colour set here (each face keeps its own copy, so changing the material alone left
            # them as they were - barge boards stayed their old colour)
            changed = {MAT_PREFIX + r[0]: r for r in self.s['palette']}

            def stale(f):
                a = getattr(f, 'attrs', None) or {}
                r = changed.get(a.get('mat'))
                if r is None:
                    return None
                want = tuple(c / 255.0 for c in r[1])
                got = tuple(a.get('color') or ())
                if len(got) >= 3 and all(abs(x - y) < 1e-3 for x, y in zip(got, want)) \
                        and abs(float(a.get('opacity', 1.0)) - float(r[2])) < 1e-3:
                    return None
                return r
            if changed:
                meshes, seen = [], set()

                def gather(g):
                    m = getattr(g, 'mesh', None)
                    if m is not None and id(m) not in seen:
                        seen.add(id(m))
                        if any(stale(f) is not None for f in (getattr(m, 'faces', None) or ())):
                            meshes.append(m)
                    for c in _children(g):
                        gather(c)
                for g in getattr(scene, 'groups', None) or []:
                    gather(g)

                def mutate(_sc):
                    for m in meshes:
                        for f in getattr(m, 'faces', None) or ():
                            r = stale(f)
                            if r is not None:
                                a = dict(getattr(f, 'attrs', None) or {})
                                a['color'] = tuple(c / 255.0 for c in r[1])
                                a['opacity'] = float(r[2])
                                f.attrs = a
                if meshes:
                    try:
                        self.viewport.history.execute(_paint_command(mutate, meshes))
                        self.viewport.notify_scene_changed()
                    except Exception as e:
                        print("%s: recolouring the model: %s" % (PLUGIN_NAME, e))
        except Exception as e:
            import traceback
            print("%s: updating the model's colours: %s" % (PLUGIN_NAME, traceback.format_exc()))
            QMessageBox.warning(self, PLUGIN_NAME, "Saved, but couldn't recolour what's already built:\n%s" % e)
        import time as _t
        self.lbl_saved.setText("Saved %s - the model shows the new colours." % _t.strftime("%H:%M"))
        # the window stays open: only Close shuts it

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
