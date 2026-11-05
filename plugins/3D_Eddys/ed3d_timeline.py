# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Timeline for IngeTrazo
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
3D Timeline - every step you've made, in a strip along the bottom of the window
Each thing you do in IngeTrazo (a line, a push/pull, a move, a paint, a plugin's part)
gets an icon in the strip, oldest on the left. Click a step to roll the model back to
just after it; click a later (greyed) step to bring the work back again. The red marker
shows where the model is now.

Rolling back and then drawing something new throws the greyed steps away, exactly as
Undo does. The timeline is IngeTrazo's own undo history, so it starts empty in each new
session and keeps as many steps as Undo does.

Two things outlast a session:
- The list of steps is kept inside the .igz file when you save, so when you open the file
  again you can still see what was done before (shown faded: you can read them, but not
  roll back to them).
- Checkpoints: full copies of the model saved in a folder beside your file (for
  station.igz, a folder called "station checkpoints"). Made by hand with the flag button,
  and automatically every so many steps. Click one to open it as its own model.
  Your named checkpoints are never deleted; only the oldest automatic ones are, once
  there are more than you've chosen to keep.
- Click a faded step from an earlier session to bring back the checkpoint saved at (or
  just before) it, into the model on screen. One Undo puts back what you had.

Ctrl+Alt+T shows or hides the timeline.
"""

import os
import re
import json
import time
from tools.base import Tool

PLUGIN_NAME = "3D Timeline"
DOCK_NAME = "EddyTimelineDock"
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_timeline.json")
POLL_MS = 300                 # how often the strip checks for new steps
DATA_KEY = "eddy_timeline"    # the steps kept inside the .igz file
MAX_PAST = 1000               # steps from earlier sessions kept in the file
SHOW_PAST = 150               # of those, how many the strip shows when opened out
INDEX_FILE = "checkpoints.json"

EDDY_TIPS = {
    "Start": "Roll back to before the first step still in the history.",
    "Back": "One step back (the same as Undo).",
    "Forward": "One step forward (the same as Redo).",
    "Latest": "Bring every greyed step back.",
}


# ---------------------------------------------------------------------------
# Settings


def load_settings():
    s = {'visible': True, 'labels': True, 'names': {}, 'auto_every': 25, 'keep_auto': 20,
         'keep_list': True}
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
# Naming the steps

# Eddy's plugins, by the end of their file name
EDDY_PLUGINS = {
    "period_windows": "Period Windows", "brick_block_studio": "Brick & Block",
    "gutters_downpipes": "Gutters", "soil_waste_pipes": "Soil pipes", "loft": "Loft",
    "print_scaler": "Print Scaler", "scale_converter": "Scale Studio", "roof_tiles": "Roof Tiles",
    "wood_planking": "Wood Planking", "period_doors": "Period Doors",
    "fences_gates": "Fences & Gates", "wrap": "Wrap", "chimneys": "Chimneys",
    "corrugated_iron": "Tin sheet", "station_canopies": "Canopy", "centre_finder": "Centre Finder",
}

# IngeTrazo's own steps whose plain name reads badly
NICE = {
    "AddEdge": "Line", "AddFace": "Face", "EraseSelection": "Erase", "DeleteEdges": "Delete lines",
    "DeleteFace": "Delete face", "MoveVertices": "Move", "RotateVertices": "Rotate",
    "ScaleVertices": "Scale", "MoveGroup": "Move", "RotateGroup": "Rotate", "ScaleGroup": "Scale",
    "MeshSnapshot": "Push/Pull", "SolidOperation": "Solid tool", "SetFaceColor": "Paint",
    "SetFaceMaterialTag": "Material", "SetFaceTexture": "Texture", "SetGroupMaterial": "Paint group",
    "MakeGroup": "Make group", "GroupToComponent": "Make component", "ExplodeGroup": "Explode",
    "FlipFaces": "Reverse faces", "AddGuide": "Guide", "AddDimension": "Dimension",
    "AddTextLabel": "Text", "Hide": "Hide", "Lock": "Lock", "AssignLayer": "Layer",
    "CoplanarMerge": "Merge faces", "StitchSolid": "Stitch", "HealOverlaps": "Heal",
    "PurgeUnused": "Purge", "SetPluginData": "Plugin data", "Compound": "Edit",
    "Windowizer": "Window opening", "RepairSolids": "Repair solids",
    "RestoreCheckpoint": "Restore checkpoint",
}

# what kind of step it is: picks the icon
KINDS = [
    ("plugin", ("RestoreCheckpoint",)),
    ("delete", ("Delete", "Erase", "Purge", "Prune")),
    ("move", ("Move", "Rotate", "Scale", "Flip", "Straighten", "ChangeAxes")),
    ("paint", ("Color", "Colour", "Material", "Texture", "Paint", "Restamp", "Opacity", "Finish", "FaceBack")),
    ("group", ("Group", "Component", "Explode", "Unique", "Insert", "Reshare", "Kept", "Pieces")),
    ("hide", ("Hide", "Lock", "Layer")),
    ("measure", ("Guide", "Dimension", "TextLabel", "Text3D", "Section", "Sheet", "View", "Plan")),
    ("shape", ("Snapshot", "Solid", "Stitch", "Heal", "Coplanar", "Simplify", "Rebuild", "Repair", "Bevel")),
    ("draw", ("Add", "Edge", "Face", "Curve", "Geo", "Image")),
]


def _words(camel):
    """'SetFaceColor' -> 'Set face color'"""
    w = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", camel).strip()
    return w[:1].upper() + w[1:].lower() if w else "Step"


def _class_stem(cmd):
    n = type(cmd).__name__
    for tail in ("Command", "Cmd"):
        if n.endswith(tail) and len(n) > len(tail):
            n = n[:-len(tail)]
    return n


def describe(cmd, tool_name=None):
    """(short label, kind, longer description) for one history step."""
    stem = _class_stem(cmd)
    # a step run through a snapshot: name it by who made it
    mutate = getattr(cmd, 'mutate', None)
    if mutate is not None:
        mod = str(getattr(mutate, '__module__', '') or '')
        qual = str(getattr(mutate, '__qualname__', '') or '')
        m = re.search(r"ed3d_([a-z_]+)", mod)
        if m:
            nm = EDDY_PLUGINS.get(m.group(1), _words(m.group(1).replace("_", " ").title().replace(" ", "")))
            return nm, "plugin", "%s (one of Eddy's 3D plugins)" % nm
        if "python_console" in mod or "<console>" in qual:
            return "Script", "plugin", "Python console script"
        if mod.startswith("core.ai") or "ai_" in mod:
            return "AI step", "plugin", "A step made by the AI assistant"
        if "import" in qual.lower() or "main_window" in mod:
            return "Import", "draw", "Imported geometry"
        if mod and not mod.startswith(("core", "views", "tools")):
            nm = _words(mod.split(".")[-1].replace("_", " ").title().replace(" ", ""))
            return nm, "plugin", "%s (extension)" % nm
    # several steps made as one: name it after what's inside
    inner = getattr(cmd, 'commands', None) or getattr(cmd, 'inner', None)
    if stem in ("Compound", "MeshSnapshot") and inner:
        try:
            stems = [_class_stem(c) for c in inner]
        except TypeError:
            stems = []
        if stem == "Compound" and stems and len(set(stems)) == 1:
            label, kind, _d = describe(inner[0])
            return label, kind, "%s (%s)" % (label, _parts(len(stems)))
        if tool_name and tool_name.lower() not in ("select", "selection"):
            return tool_name, _tool_kind(tool_name, _kind_of(stem)), "%s (%s)" % (tool_name, _parts(len(stems)))
    label = NICE.get(stem) or _words(stem)
    kind = _kind_of(stem)
    if stem in ("Compound",) and tool_name and tool_name.lower() not in ("select", "selection"):
        label, kind = tool_name, _tool_kind(tool_name, kind)
    if tool_name and tool_name.lower() != label.lower():
        longer = "%s  -  with the %s tool" % (label, tool_name)
    else:
        longer = label
    return label, kind, longer


TOOL_KINDS = [("shape", ("push", "pull", "follow", "offset", "solid", "fillet", "bevel")),
              ("move", ("move", "rotate", "scale", "flip")),
              ("paint", ("paint", "texture")), ("delete", ("erase",)),
              ("measure", ("tape", "dimension", "protractor", "text", "section")),
              ("draw", ("line", "rect", "circle", "arc", "freehand", "polygon"))]


def _tool_kind(tool_name, fallback):
    t = (tool_name or "").lower()
    for kind, keys in TOOL_KINDS:
        if any(k in t for k in keys):
            return kind
    return fallback


def _parts(n):
    return "1 part" if n == 1 else "%d parts" % n


def _kind_of(stem):
    for kind, keys in KINDS:
        if any(k in stem for k in keys):
            return kind
    return "other"


# ---------------------------------------------------------------------------
# Icons, drawn here so nothing extra has to be installed

_ICONS = {}


def step_icon(kind, future=False):
    key = (kind, future)
    if key in _ICONS:
        return _ICONS[key]
    from PySide6.QtCore import Qt, QRectF, QPointF
    from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QIcon, QPolygonF, QFont
    colours = {
        "draw": QColor(60, 120, 210), "move": QColor(230, 140, 30), "delete": QColor(200, 55, 45),
        "paint": QColor(150, 80, 190), "group": QColor(50, 150, 80), "hide": QColor(120, 120, 120),
        "measure": QColor(30, 150, 150), "shape": QColor(150, 100, 50), "plugin": QColor(40, 70, 60),
        "other": QColor(110, 110, 140),
    }
    c = colours.get(kind, colours["other"])
    if future:
        g = int(0.3 * c.red() + 0.59 * c.green() + 0.11 * c.blue())
        c = QColor(int(g * 0.4 + 150), int(g * 0.4 + 150), int(g * 0.4 + 150))
    pm = QPixmap(64, 64)                      # drawn at double size: stays sharp when big
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(2, 2)
    p.setPen(Qt.NoPen)
    p.setBrush(c)
    p.drawRoundedRect(QRectF(2, 2, 28, 28), 6, 6)
    w = QColor(255, 255, 255) if not future else QColor(245, 245, 245)
    pen = QPen(w, 2.2)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    if kind == "draw":                       # a pencil line
        p.drawLine(QPointF(8, 24), QPointF(22, 10))
        p.drawLine(QPointF(22, 10), QPointF(25, 13))
        p.drawLine(QPointF(25, 13), QPointF(11, 27))
        p.drawLine(QPointF(8, 24), QPointF(7, 26))
    elif kind == "move":                     # four arrows
        p.drawLine(QPointF(16, 6), QPointF(16, 26))
        p.drawLine(QPointF(6, 16), QPointF(26, 16))
        for a, b, d in (((16, 6), (12, 10), (20, 10)), ((16, 26), (12, 22), (20, 22)),
                        ((6, 16), (10, 12), (10, 20)), ((26, 16), (22, 12), (22, 20))):
            p.drawLine(QPointF(*a), QPointF(*b))
            p.drawLine(QPointF(*a), QPointF(*d))
    elif kind == "delete":                   # a cross
        p.drawLine(QPointF(10, 10), QPointF(22, 22))
        p.drawLine(QPointF(22, 10), QPointF(10, 22))
    elif kind == "paint":                    # a pot of paint
        p.drawRect(QRectF(9, 13, 14, 12))
        p.drawArc(QRectF(9, 6, 14, 14), 0, 180 * 16)
        p.setBrush(w)
        p.drawEllipse(QPointF(25, 22), 2, 3)
    elif kind == "group":                    # a box
        p.drawPolygon(QPolygonF([QPointF(16, 6), QPointF(26, 11), QPointF(16, 16), QPointF(6, 11)]))
        p.drawLine(QPointF(6, 11), QPointF(6, 21))
        p.drawLine(QPointF(26, 11), QPointF(26, 21))
        p.drawLine(QPointF(16, 16), QPointF(16, 26))
        p.drawLine(QPointF(6, 21), QPointF(16, 26))
        p.drawLine(QPointF(26, 21), QPointF(16, 26))
    elif kind == "hide":                     # an eye
        p.drawArc(QRectF(6, 9, 20, 16), 20 * 16, 140 * 16)
        p.drawArc(QRectF(6, 7, 20, 16), 200 * 16, 140 * 16)
        p.setBrush(w)
        p.drawEllipse(QPointF(16, 16), 3, 3)
    elif kind == "measure":                  # a tape line with ticks
        p.drawLine(QPointF(6, 20), QPointF(26, 20))
        for x in (7, 12, 17, 22, 26):
            p.drawLine(QPointF(x, 20), QPointF(x, 14 if x in (7, 17, 26) else 17))
    elif kind == "shape":                    # a block being pushed up
        p.drawRect(QRectF(8, 16, 16, 10))
        p.drawLine(QPointF(16, 13), QPointF(16, 5))
        p.drawLine(QPointF(16, 5), QPointF(12, 9))
        p.drawLine(QPointF(16, 5), QPointF(20, 9))
    elif kind == "plugin":                   # the printed E of Eddy's Model Works
        f = QFont("Arial", 15)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(240, 200, 90) if not future else w)
        p.drawText(QRectF(2, 1, 28, 28), Qt.AlignCenter, "E")
    else:                                    # a dot
        p.setBrush(w)
        p.drawEllipse(QPointF(16, 16), 4, 4)
    p.end()
    icon = QIcon(pm)
    _ICONS[key] = icon
    return icon


SIZES = [("Small", 1.0), ("Medium", 1.5), ("Large", 2.0), ("Extra large", 2.5)]


def nav_icon(kind):
    """|< < > >| drawn, so they show whatever fonts the PC has."""
    from PySide6.QtCore import Qt, QPointF
    from PySide6.QtGui import QPixmap, QPainter, QColor, QPolygonF, QIcon
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(60, 70, 85))
    left = kind in ("start", "back")
    tri = [QPointF(44, 14), QPointF(44, 50), QPointF(16, 32)] if left else \
          [QPointF(20, 14), QPointF(20, 50), QPointF(48, 32)]
    if kind in ("start", "end"):
        tri = [QPointF(x.x() + (4 if left else -4), x.y()) for x in tri]
        p.drawRect(*((10, 14, 6, 36) if left else (48, 14, 6, 36)))
    p.drawPolygon(QPolygonF(tri))
    p.end()
    return QIcon(pm)


def menu_icon():
    """Three lines: the settings menu."""
    from PySide6.QtCore import Qt, QRectF
    from PySide6.QtGui import QPixmap, QPainter, QColor, QIcon
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(60, 70, 85))
    for y in (16, 29, 42):
        p.drawRoundedRect(QRectF(14, y, 36, 6), 3, 3)
    p.end()
    return QIcon(pm)


def flag_pixmap(size=22, colour=(215, 160, 20)):
    from PySide6.QtCore import Qt, QPointF
    from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QPolygonF
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    k = size / 22.0
    p.setPen(QPen(QColor(70, 70, 70), 1.8 * k))
    p.drawLine(QPointF(5 * k, 2 * k), QPointF(5 * k, 21 * k))              # the pole
    p.setPen(QPen(QColor(120, 80, 0), 1.0 * k))
    p.setBrush(QColor(*colour))
    p.drawPolygon(QPolygonF([QPointF(6 * k, 3 * k), QPointF(19 * k, 6.5 * k),
                             QPointF(6 * k, 11 * k)]))                    # the flag
    p.end()
    return pm


# ---------------------------------------------------------------------------
# Finding IngeTrazo's window, 3D view and history


def _main_window():
    from PySide6.QtWidgets import QApplication, QMainWindow
    app = QApplication.instance()
    if app is None:
        return None
    wins = [w for w in app.topLevelWidgets() if isinstance(w, QMainWindow)]
    shown = [w for w in wins if w.isVisible()]
    return (shown or wins or [None])[0]


def find_viewport(win):
    """The 3D view in front (with tabs open, the one showing)."""
    if win is None:
        return None
    for attr in ('viewport', '_viewport', 'view'):
        vp = getattr(win, attr, None)
        if vp is not None and getattr(vp, 'history', None) is not None:
            return vp
    from PySide6.QtWidgets import QWidget
    for w in win.findChildren(QWidget):
        if getattr(w, 'scene', None) is not None and getattr(w, 'history', None) is not None:
            if w.isVisible():
                return w
    return None


def _refresh_view(vp):
    """What IngeTrazo's own Undo does once the history has moved."""
    for name in ('clear_references',):
        inf = getattr(vp, 'inference', None)
        fn = getattr(inf, name, None)
        if callable(fn):
            try:
                fn()
            except Exception:
                pass
    for name in ('notify_scene_changed', 'update'):
        fn = getattr(vp, name, None)
        if callable(fn):
            try:
                fn()
            except Exception:
                pass


def go_to(vp, target):
    """Move the model to just after step number ``target`` (0 = before every step).
    Returns how many steps it moved."""
    h = getattr(vp, 'history', None)
    if h is None:
        return 0
    tool = getattr(vp, 'active_tool', None)
    cancel = getattr(tool, 'on_undo', None)
    moved = 0
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    QApplication.setOverrideCursor(Qt.WaitCursor)
    try:
        if callable(cancel):
            # a tool half-way through (a line being drawn) lets go first, as Undo does
            try:
                cancel()
            except Exception:
                pass
        while len(h.undo_stack) > target:
            if not h.undo():
                break
            moved += 1
        while len(h.undo_stack) < target and h.redo_stack:
            if not h.redo():
                break
            moved += 1
    finally:
        QApplication.restoreOverrideCursor()
        _refresh_view(vp)
    if moved and getattr(h, 'last_error', None):
        _flash(vp, "Timeline: a step could not be undone (%s)" % h.last_error)
    return moved


def _flash(vp, text, ms=4000):
    fn = getattr(vp, 'flash_status', None)
    if callable(fn):
        try:
            fn(text, ms)
            return
        except TypeError:
            try:
                fn(text)
                return
            except Exception:
                pass
        except Exception:
            pass
    print(text)


# ---------------------------------------------------------------------------
# Keeping the steps in the file, and checkpoints beside it


def doc_path(win):
    """The .igz the model in front was opened from or saved to (None if never saved)."""
    for owner in (win, getattr(win, '_doc', None)):
        if owner is None:
            continue
        for attr in ('current_path', '_current_path', 'path'):
            p = getattr(owner, attr, None)
            if callable(p):
                try:
                    p = p()
                except Exception:
                    p = None
            if p:
                p = str(p)
                if p.lower().endswith(".igz"):
                    return p
    return None


def checkpoint_dir(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    return os.path.join(os.path.dirname(path), stem + " checkpoints")


def read_index(folder):
    try:
        with open(os.path.join(folder, INDEX_FILE), "r", encoding="utf-8") as f:
            idx = json.load(f)
        idx = [e for e in idx if isinstance(e, dict) and e.get('file')]
    except Exception:
        idx = []
    # checkpoints copied in by hand, or an index that went missing: still listed
    try:
        known = {e['file'] for e in idx}
        for fn in sorted(os.listdir(folder)):
            if fn.lower().endswith(".igz") and fn not in known:
                full = os.path.join(folder, fn)
                idx.append({'file': fn, 'time': os.path.getmtime(full), 'label': "", 'auto': False})
    except Exception:
        pass
    return [e for e in idx if os.path.isfile(os.path.join(folder, e['file']))]


def write_index(folder, idx):
    try:
        tmp = os.path.join(folder, INDEX_FILE + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(idx, f, indent=1)
        os.replace(tmp, os.path.join(folder, INDEX_FILE))
    except Exception:
        pass


def list_checkpoints(win):
    path = doc_path(win)
    if not path:
        return None, []
    folder = checkpoint_dir(path)
    if not os.path.isdir(folder):
        return folder, []
    return folder, sorted(read_index(folder), key=lambda e: e.get('time') or 0)


def save_checkpoint(win, vp, label="", step=None, auto=False, keep_auto=20, after=None):
    """A full copy of the model as it is now, into the checkpoints folder.
    Returns (file name, None) or (None, why not)."""
    path = doc_path(win)
    if not path:
        return None, "Save the model first, so its checkpoints have a folder to go in."
    scene = getattr(vp, 'scene', None)
    if scene is None:
        return None, "There's no model open."
    if getattr(scene, 'edit_group', None) is not None:
        return None, "Close the group you're editing first (Esc), then make the checkpoint."
    try:
        from formats.igz import save_scene
    except Exception as e:
        return None, "IngeTrazo's file saver couldn't be found (%s)." % e
    folder = checkpoint_dir(path)
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    QApplication.setOverrideCursor(Qt.WaitCursor)
    try:
        os.makedirs(folder, exist_ok=True)
        idx = read_index(folder)
        n = 1 + max([int(e.get('n') or 0) for e in idx] + [len(idx)])
        fn = "checkpoint %03d%s.igz" % (n, " (auto)" if auto else "")
        from pathlib import Path
        save_scene(scene, Path(folder) / fn)        # IngeTrazo's saver wants a Path, not text
        idx.append({'file': fn, 'n': n, 'time': time.time(), 'label': label or "",
                    'step': step, 'auto': bool(auto), 'after': after})
        # only the oldest AUTOMATIC ones go: the ones you made yourself always stay
        autos = [e for e in idx if e.get('auto')]
        if keep_auto and len(autos) > keep_auto:
            for e in autos[:len(autos) - keep_auto]:
                try:
                    os.remove(os.path.join(folder, e['file']))
                except Exception:
                    pass
                idx.remove(e)
        write_index(folder, idx)
        return fn, None
    except Exception as e:
        return None, "The checkpoint couldn't be saved: %s" % e
    finally:
        QApplication.restoreOverrideCursor()


def _command_base():
    try:
        from core.history import Command
        return Command
    except Exception:
        return object


def _after_load(win, vp):
    """The tidying IngeTrazo's own File > Open does once a file is read in."""
    for owner, name in ((vp, 'reset_texture_cache'), (vp, 'prepare_drawing'),
                        (getattr(vp, 'inference', None), 'reset'),
                        (win, '_sync_style_menu'), (win, '_sync_section_menu'),
                        (vp, 'notify_scene_changed'), (vp, 'update'), (win, '_update_title')):
        fn = getattr(owner, name, None)
        if callable(fn):
            try:
                fn()
            except Exception:
                pass


def restore_checkpoint(win, vp, full, on_change=None):
    """Loads a checkpoint into the model on screen as ONE undoable step.

    The model as it was goes into a 'before restoring' file first (beside the checkpoints,
    or in the temp folder for a model never saved): that's what Undo loads back, so
    nothing can be lost. Every earlier undo step is let go of, the way opening a file
    does - they point at geometry that has just been replaced.
    Returns None if all went well, or the reason it didn't."""
    scene = getattr(vp, 'scene', None)
    h = getattr(vp, 'history', None)
    if scene is None or h is None:
        return "There's no model open."
    if getattr(scene, 'edit_group', None) is not None:
        return "Close the group you're editing first (Esc), then restore."
    try:
        from formats.igz import save_scene, load_into
    except Exception as e:
        return "IngeTrazo's file reader couldn't be found (%s)." % e
    from pathlib import Path
    import tempfile
    path = doc_path(win)
    folder = checkpoint_dir(path) if path else os.path.join(tempfile.gettempdir(), "IngeTrazo timeline")
    os.makedirs(folder, exist_ok=True)
    before = os.path.join(folder, "before restoring %s.igz" % time.strftime("%Y-%m-%d %H-%M-%S"))

    Base = _command_base()

    class RestoreCheckpointCommand(Base):
        keeps_paint = False
        keeps_groups = False

        def __init__(self):
            self.target, self.before = full, before
            self.name = os.path.basename(full)

        def _load(self, sc, src):
            load_into(sc, Path(src))
            _after_load(win, vp)
            if on_change:
                on_change()

        def do(self, sc):
            try:
                self._load(sc, self.target)
            except BaseException:
                try:
                    self._load(sc, self.before)       # never leave a half-loaded model
                except Exception:
                    pass
                raise

        def undo(self, sc):
            self._load(sc, self.before)

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    QApplication.setOverrideCursor(Qt.WaitCursor)
    try:
        save_scene(scene, Path(before))
        cmd = RestoreCheckpointCommand()
        cmd.do(scene)
        h.undo_stack[:] = [cmd]
        h.redo_stack.clear()
    except Exception as e:
        return "The checkpoint couldn't be restored: %s" % e
    finally:
        QApplication.restoreOverrideCursor()
        _refresh_view(vp)
    return None


def open_model(win, full):
    """Opens a checkpoint as a model of its own (IngeTrazo's File > Open)."""
    fn = getattr(win, 'open_path', None)
    if callable(fn):
        try:
            from pathlib import Path
            fn(Path(full))                   # IngeTrazo wants a Path, not text
            return True
        except Exception as e:
            print("%s: could not open %s (%s)" % (PLUGIN_NAME, full, e))
    return False


def open_folder(folder):
    try:
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# The strip


def make_dock(win):
    from PySide6.QtCore import Qt, QTimer, QSize
    from PySide6.QtWidgets import (QDockWidget, QWidget, QHBoxLayout, QVBoxLayout, QToolButton,
                                   QScrollArea, QLabel, QFrame, QMenu, QInputDialog, QSizePolicy)

    dock = QDockWidget(PLUGIN_NAME, win)
    dock.setObjectName(DOCK_NAME)
    dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
    dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)

    body = QWidget()
    row = QHBoxLayout(body)
    row.setContentsMargins(4, 2, 4, 2)
    row.setSpacing(4)

    def nav(kind, tip, slot):
        b = QToolButton()
        b.setIcon(nav_icon(kind))
        b.setToolTip(tip)
        b.setAutoRaise(True)
        b.clicked.connect(slot)
        return b

    st0 = load_settings()
    state = {'vp': None, 'sig': None, 'seen': {}, 'tools': {}, 'labels': st0.get('labels', True),
             'tokens': {}, 'past': {}, 'written': {}, 'show_past': False, 'since_cp': 0,
             'marks': {}, 'settings': st0,
             'zoom': float(st0.get('zoom') or 2.0), 'sids': {}, 'sid_n': 0,
             'prefix': "%x" % int(time.time() * 1000)}
    names = {}                                # id(cmd) -> your own name for a step (this session)

    btn_start = nav("start", EDDY_TIPS["Start"], lambda: jump(0))
    btn_back = nav("back", EDDY_TIPS["Back"], lambda: jump(cur() - 1))
    btn_fwd = nav("fwd", EDDY_TIPS["Forward"], lambda: jump(cur() + 1))
    btn_end = nav("end", EDDY_TIPS["Latest"], lambda: jump(total()))
    for b in (btn_start, btn_back, btn_fwd, btn_end):
        row.addWidget(b)

    btn_cp = QToolButton()
    from PySide6.QtGui import QIcon
    btn_cp.setIcon(QIcon(flag_pixmap(64)))
    btn_cp.setToolTip("Checkpoints: save a full copy of the model now, open an earlier one, "
                      "and set how often they're made automatically.")
    btn_cp.setAutoRaise(True)
    btn_cp.setPopupMode(QToolButton.InstantPopup)
    cp_menu = QMenu(btn_cp)
    btn_cp.setMenu(cp_menu)
    row.addWidget(btn_cp)

    def Z(n):
        return int(round(n * float(state.get('zoom') or 2.0)))

    def apply_size():
        for b in (btn_start, btn_back, btn_fwd, btn_end):
            b.setFixedSize(QSize(Z(28), Z(28)))
            b.setIconSize(QSize(Z(20), Z(20)))
        btn_cp.setFixedSize(QSize(Z(40), Z(28)))
        btn_menu.setFixedSize(QSize(Z(28), Z(28)))
        btn_menu.setIconSize(QSize(Z(18), Z(18)))
        btn_cp.setIconSize(QSize(Z(22), Z(22)))
        f = dock.font()
        f.setPointSizeF(max(8.0, 8.0 * (1 + (float(state.get('zoom') or 2.0) - 1) * 0.5)))
        strip.setFont(f)
        btn_past.setFont(f)
        count.setFont(f)
        warn_text.setFont(f)
        dock.setMinimumHeight(Z(40) + 30)

    btn_past = QToolButton()
    btn_past.setAutoRaise(True)
    btn_past.setCheckable(True)
    btn_past.setVisible(False)
    btn_past.toggled.connect(lambda on: (state.__setitem__('show_past', bool(on)), rebuild(force=True)))
    row.addWidget(btn_past)

    sep = QFrame()
    sep.setFrameShape(QFrame.VLine)
    row.addWidget(sep)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setFrameShape(QFrame.NoFrame)
    strip = QWidget()
    strip_row = QHBoxLayout(strip)
    strip_row.setContentsMargins(0, 0, 0, 0)
    strip_row.setSpacing(2)
    scroll.setWidget(strip)
    row.addWidget(scroll, 1)

    count = QLabel("")
    count.setMinimumWidth(70)
    count.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    count.setStyleSheet("color: gray;")
    row.addWidget(count)
    btn_menu = QToolButton()
    btn_menu.setIcon(menu_icon())
    btn_menu.setAutoRaise(True)
    btn_menu.setToolTip("Timeline settings: button size, names under the icons, hide")
    row.addWidget(btn_menu)
    outer = QWidget()
    col = QVBoxLayout(outer)
    col.setContentsMargins(0, 0, 0, 0)
    col.setSpacing(0)
    warn = QWidget()
    warn.setStyleSheet("background: rgb(255, 236, 190);")
    wrow = QHBoxLayout(warn)
    wrow.setContentsMargins(8, 2, 6, 2)
    warn_text = QLabel("")
    warn_text.setStyleSheet("color: rgb(110, 60, 0);")
    wrow.addWidget(warn_text, 1)
    warn_cp = QToolButton()
    warn_cp.setText("Save a checkpoint")
    warn_back = QToolButton()
    warn_back.setText("Back to latest")
    wrow.addWidget(warn_cp)
    wrow.addWidget(warn_back)
    warn.setVisible(False)
    col.addWidget(warn)
    col.addWidget(body)
    dock.setWidget(outer)

    def steps():
        """(cmd, done) oldest first: the done ones, then the greyed ones still to redo."""
        vp = state['vp']
        h = getattr(vp, 'history', None)
        if h is None:
            return []
        out = [(c, True) for c in list(h.undo_stack)]
        out += [(c, False) for c in reversed(list(h.redo_stack))]
        return out

    def cur():
        h = getattr(state['vp'], 'history', None)
        return len(h.undo_stack) if h is not None else 0

    def total():
        h = getattr(state['vp'], 'history', None)
        return len(h.undo_stack) + len(h.redo_stack) if h is not None else 0

    def jump(target):
        vp = state['vp']
        if vp is None:
            return
        target = max(0, min(total(), target))
        if target < cur() and cur() == total() and not ask_before_rollback(vp, cur() - target):
            return
        if target != cur():
            go_to(vp, target)
        rebuild(force=True)

    def ask_before_rollback(vp, n):
        """Going back from the latest model: say what happens, and offer a checkpoint first."""
        s = state['settings']
        if not s.get('warn_rollback', True):
            return True
        from PySide6.QtWidgets import QMessageBox, QCheckBox
        box = QMessageBox(dock)
        box.setWindowTitle(PLUGIN_NAME)
        box.setIcon(QMessageBox.Warning)
        box.setText("Roll back %d step%s?" % (n, "" if n == 1 else "s"))
        saved = doc_path(win) is not None
        box.setInformativeText(
            "You can look around and come forward again with no harm done.\n\n"
            "But if you change anything while rolled back (even opening a group), the greyed "
            "steps after it are thrown away, just as with Undo.\n\n"
            + ("A checkpoint saves the model as it is now, so you can always get back to it."
               if saved else "Save the model once to be able to make a checkpoint first."))
        choice = []
        b_cp = box.addButton("Checkpoint, then roll back", QMessageBox.AcceptRole) if saved else None
        b_go = box.addButton("Roll back", QMessageBox.DestructiveRole)
        box.addButton(QMessageBox.Cancel)
        if b_cp is not None:
            b_cp.clicked.connect(lambda: choice.append('cp'))
        b_go.clicked.connect(lambda: choice.append('go'))
        box.setDefaultButton(b_cp or b_go)
        never = QCheckBox("Don't ask me again")
        box.setCheckBox(never)
        box.exec()
        pressed = choice[-1] if choice else None
        if pressed is None:
            return False
        if never.isChecked():
            setting('warn_rollback', False)
        if pressed == 'cp':
            text, ok = QInputDialog.getText(dock, PLUGIN_NAME, "Name for this checkpoint:",
                                            text="before going back")
            if not ok:
                return False
            fn, why = save_checkpoint(win, vp, text.strip(), step=cur(), auto=False, after=current_after(),
                                      keep_auto=int(s.get('keep_auto') or 0))
            if not fn:
                from PySide6.QtWidgets import QMessageBox as MB
                if MB.question(dock, PLUGIN_NAME, why + "\n\nRoll back anyway?") != MB.Yes:
                    return False
            else:
                state['since_cp'] = 0
                h = getattr(vp, 'history', None)
                if h is not None and h.undo_stack:
                    state['marks'][id(h.undo_stack[-1])] = text.strip() or fn[:-4]
                state['cp_at_latest'] = True
        return True

    def playhead():
        m = QFrame()
        m.setFixedWidth(max(4, Z(3)))
        m.setMinimumHeight(Z(40))
        m.setStyleSheet("background: rgb(210, 40, 40); border-radius: 2px;")
        m.setToolTip("The model is here now")
        return m

    def chip(i, cmd, done):
        tool_name = state['tools'].get(id(cmd))
        label, kind, longer = describe(cmd, tool_name)
        label = names.get(id(cmd), label)
        b = QToolButton()
        b.setIcon(step_icon(kind, future=not done))
        b.setIconSize(QSize(Z(26), Z(26)))
        b.setAutoRaise(True)
        if state['labels']:
            b.setText("%d %s" % (i + 1, label) if len(label) <= 14 else "%d %s.." % (i + 1, label[:13]))
            b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        else:
            b.setToolButtonStyle(Qt.ToolButtonIconOnly)
        if not done:
            b.setStyleSheet("color: gray;")
        when = state['seen'].get(id(cmd))
        tip = "Step %d: %s" % (i + 1, names.get(id(cmd), longer))
        if when:
            tip += "\nMade at %s" % time.strftime("%H:%M:%S", time.localtime(when))
        tip += ("\nClick to roll back to just after this step." if done
                else "\nGreyed: undone. Click to bring the work back up to here.")
        b.setToolTip(tip)
        b.clicked.connect(lambda _=False, t=i + 1: jump(t))
        b.setContextMenuPolicy(Qt.CustomContextMenu)
        b.customContextMenuRequested.connect(lambda pos, b=b, c=cmd, t=i + 1, lb=label: step_menu(b, pos, c, t, lb))
        return b

    def step_menu(b, pos, cmd, t, label):
        menu = QMenu(b)
        menu.addAction("Go to just after this step", lambda: jump(t))
        menu.addAction("Go to just before this step", lambda: jump(t - 1))
        menu.addSeparator()

        def rename():
            text, ok = QInputDialog.getText(dock, PLUGIN_NAME, "Name for this step:", text=label)
            if ok:
                if text.strip():
                    names[id(cmd)] = text.strip()
                else:
                    names.pop(id(cmd), None)
                rebuild(force=True)
        menu.addAction("Rename step...", rename)
        menu.exec(b.mapToGlobal(pos))
        menu.deleteLater()

    def setting(key, value):
        s = load_settings()
        s[key] = value
        save_settings(s)
        state['settings'] = s

    def current_after():
        """The id of the last done step (this session, or the last earlier one)."""
        h = getattr(state['vp'], 'history', None)
        if h is not None and h.undo_stack:
            return state['sids'].get(id(h.undo_stack[-1]))
        scene = getattr(state['vp'], 'scene', None)
        past = state['past'].get(id(scene)) or []
        return past[-1].get('id') if past else None

    def make_checkpoint(auto=False):
        vp = state['vp']
        label = ""
        if not auto:
            text, ok = QInputDialog.getText(dock, PLUGIN_NAME,
                                            "Name for this checkpoint (you can leave it blank):")
            if not ok:
                return
            label = text.strip()
        s = state['settings']
        fn, why = save_checkpoint(win, vp, label, step=cur(), auto=auto,
                                  keep_auto=int(s.get('keep_auto') or 0), after=current_after())
        if fn:
            state['since_cp'] = 0
            h = getattr(vp, 'history', None)
            if h is not None and h.undo_stack:
                state['marks'][id(h.undo_stack[-1])] = label or ("automatic" if auto else fn[:-4])
            _flash(vp, "Checkpoint saved: %s%s" % (fn, (" - " + label) if label else ""))
            rebuild(force=True)
        elif not auto:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(dock, PLUGIN_NAME, why)

    def reload_past():
        scene = getattr(state['vp'], 'scene', None)
        if scene is not None:
            state['tokens'].pop(id(scene), None)     # read the restored file's step list again
            state['written'].pop(id(scene), None)

    def offer_checkpoint(full, e, note=""):
        """Restore a checkpoint into this model, or open it on its own."""
        from PySide6.QtWidgets import QMessageBox
        box = QMessageBox(dock)
        box.setWindowTitle(PLUGIN_NAME)
        box.setIcon(QMessageBox.Question)
        when = time.strftime("%d %b %Y %H:%M", time.localtime(e.get('time') or 0))
        name = e.get('label') or ("automatic" if e.get('auto') else e['file'][:-4])
        box.setText("Checkpoint: %s  (%s)" % (name, when))
        box.setInformativeText(
            (note + "\n\n" if note else "") +
            "Restore it here: the model on screen becomes that version. The model as it is now "
            "is saved first, and one Undo brings it back.\n\n"
            "Open on its own: it opens as a separate model and this one is left alone.")
        choice = []
        b_here = box.addButton("Restore it here", QMessageBox.AcceptRole)
        b_open = box.addButton("Open on its own", QMessageBox.ActionRole)
        box.addButton(QMessageBox.Cancel)
        b_here.clicked.connect(lambda: choice.append('here'))
        b_open.clicked.connect(lambda: choice.append('open'))
        box.setDefaultButton(b_here)
        box.exec()
        pressed = choice[-1] if choice else None
        if pressed == 'open':
            # once the menu and this box have closed, as File > Open would be
            QTimer.singleShot(50, lambda: _try(dock, lambda: open_or_say(full)))
        elif pressed == 'here':
            why = restore_checkpoint(win, state['vp'], full, on_change=reload_past)
            if why:
                QMessageBox.information(dock, PLUGIN_NAME, why)
            else:
                reload_past()
                _flash(state['vp'], "Restored %s - Undo (Ctrl+Z) puts back what you had." % name, 6000)
            state['since_cp'] = 0
            rebuild(force=True)

    def open_or_say(full):
        from PySide6.QtWidgets import QMessageBox
        if not open_model(win, full):
            QMessageBox.information(dock, PLUGIN_NAME, "The checkpoint couldn't be opened. You can open it "
                                    "with File > Open from this folder:\n\n%s" % os.path.dirname(full))

    def checkpoint_for(past, i):
        """The checkpoint saved at past step i, or the nearest one before it: (entry, full, steps short)."""
        folder, cps = list_checkpoints(win)
        if not cps:
            return None
        by_after = {}
        for e in cps:                       # newest wins
            if e.get('after'):
                by_after[e['after']] = e
        for j in range(i, -1, -1):
            sid = past[j].get('id')
            if sid and sid in by_after:
                e = by_after[sid]
                return e, os.path.join(folder, e['file']), i - j
        return None

    def past_clicked(past, i):
        found = checkpoint_for(past, i)
        if not found:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(dock, PLUGIN_NAME,
                                    "There's no checkpoint at or before this step, so it can't be brought back.\n\n"
                                    "Checkpoints made from now on are linked to their steps; set Automatic "
                                    "checkpoints (flag button) to 'Every step' to be able to go back to any step.")
            return
        e, full, short = found
        note = "" if short == 0 else "The nearest checkpoint is %d step%s before the one you clicked." % (
            short, "" if short == 1 else "s")
        offer_checkpoint(full, e, note)

    def fill_cp_menu():
        cp_menu.clear()
        cp_menu.addAction("Save a checkpoint now...", lambda: make_checkpoint(False))
        folder, cps = list_checkpoints(win)
        if folder is None:
            a = cp_menu.addAction("(save the model first: checkpoints go in a folder beside it)")
            a.setEnabled(False)
        else:
            cp_menu.addSection("Open a checkpoint (opens as its own model)")
            if not cps:
                a = cp_menu.addAction("(none yet)")
                a.setEnabled(False)
            for e in list(reversed(cps))[:40]:
                when = time.strftime("%d %b %H:%M", time.localtime(e.get('time') or 0))
                text = "%s   %s" % (when, e.get('label') or ("automatic" if e.get('auto') else e['file'][:-4]))
                if e.get('step') is not None:
                    text += "   (step %s)" % e['step']
                full = os.path.join(folder, e['file'])
                cp_menu.addAction(text, lambda f=full, e=e: _try(dock, lambda: offer_checkpoint(f, e)))
            cp_menu.addSeparator()
            cp_menu.addAction("Open the checkpoints folder", lambda: (os.makedirs(folder, exist_ok=True), open_folder(folder)))
        s = state['settings']
        sub = cp_menu.addMenu("Automatic checkpoints")
        for n in (0, 1, 5, 10, 25, 50, 100):
            a = sub.addAction("Off" if n == 0 else "Every step (uses the most disk space)" if n == 1
                              else "Every %d steps" % n)
            a.setCheckable(True)
            a.setChecked(int(s.get('auto_every') or 0) == n)
            a.triggered.connect(lambda _=False, n=n: setting('auto_every', n))
        sub2 = cp_menu.addMenu("Automatic ones to keep")
        for n in (5, 10, 20, 50, 0):
            a = sub2.addAction("All of them" if n == 0 else "The last %d" % n)
            a.setCheckable(True)
            a.setChecked(int(s.get('keep_auto') or 0) == n)
            a.triggered.connect(lambda _=False, n=n: setting('keep_auto', n))
        cp_menu.addSeparator()
        w = cp_menu.addAction("Ask before rolling back")
        w.setCheckable(True)
        w.setChecked(bool(s.get('warn_rollback', True)))
        w.toggled.connect(lambda on: setting('warn_rollback', bool(on)))
        a = cp_menu.addAction("Keep the list of steps in the file when saving")
        a.setCheckable(True)
        a.setChecked(bool(s.get('keep_list', True)))
        a.toggled.connect(lambda on: setting('keep_list', bool(on)))

    cp_menu.aboutToShow.connect(lambda: _safe(fill_cp_menu))

    def checkpoint_latest():
        """From the yellow bar: go to the latest, save it, come back to where you were."""
        vp = state['vp']
        here = cur()
        go_to(vp, total())
        text, ok = QInputDialog.getText(dock, PLUGIN_NAME, "Name for this checkpoint (the latest model):",
                                        text="latest")
        fn = why = None
        if ok:
            fn, why = save_checkpoint(win, vp, text.strip(), step=cur(), auto=False, after=current_after(),
                                      keep_auto=int(state['settings'].get('keep_auto') or 0))
        go_to(vp, here)
        if fn:
            state['cp_at_latest'] = True
            _flash(vp, "Checkpoint saved: %s" % fn)
        elif why:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(dock, PLUGIN_NAME, why)
        rebuild(force=True)

    warn_cp.clicked.connect(lambda: _safe(checkpoint_latest))
    warn_back.clicked.connect(lambda: jump(total()))

    def sync_file(vp, all_steps, n_done, fresh):
        """The steps from earlier sessions (read from the file), and the done steps of this
        one written back into it, so saving keeps them."""
        scene = getattr(vp, 'scene', None)
        pd = getattr(scene, 'plugin_data', None)
        if scene is None or not isinstance(pd, dict):
            return []
        key = id(scene)
        data = pd.get(DATA_KEY)
        data = data if isinstance(data, dict) else {}
        tok = state['tokens'].get(key)
        if tok is None or (data.get('session') and data.get('session') != tok):
            # first sight of this model, or another file opened into it
            past = [e for e in (data.get('past') or []) + (data.get('now') or []) if isinstance(e, dict)]
            state['past'][key] = past[-MAX_PAST:]
            tok = "%x-%x" % (int(time.time() * 1000), id(scene) & 0xffffff)
            state['tokens'][key] = tok
        elif not data and not all_steps and state['past'].get(key):
            state['past'][key] = []         # File > New on the same window: a clean start
        past = state['past'].get(key, [])
        if not state['settings'].get('keep_list', True):
            if DATA_KEY in pd:
                pd.pop(DATA_KEY, None)
            return past
        now_list = []
        for c, done in all_steps[:n_done]:
            label, kind, _l = describe(c, state['tools'].get(id(c)))
            now_list.append({'l': names.get(id(c), label), 'k': kind, 't': state['seen'].get(id(c)),
                             'id': state['sids'].get(id(c))})
        new = {'session': tok, 'past': past[-MAX_PAST:], 'now': now_list}
        blob = json.dumps(new, sort_keys=True)
        if state['written'].get(key) != blob or data.get('session') != tok:
            pd[DATA_KEY] = new
            state['written'][key] = blob
        return past

    def past_chip(i, e, past=None):
        b = QToolButton()
        b.setIcon(step_icon(e.get('k') or "other", future=True))
        b.setIconSize(QSize(Z(20), Z(20)))
        b.setAutoRaise(True)
        label = str(e.get('l') or "Step")
        if state['labels']:
            b.setText(label if len(label) <= 12 else label[:11] + "..")
            b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        b.setStyleSheet("color: rgb(150, 150, 150); font-style: italic;")
        tip = "Earlier session: %s" % label
        if e.get('t'):
            tip += "\nMade %s" % time.strftime("%d %b %Y %H:%M", time.localtime(e['t']))
        tip += "\nClick to bring back the checkpoint saved at (or just before) this step."
        b.setToolTip(tip)
        if past is not None:
            b.clicked.connect(lambda _=False: _try(dock, lambda: past_clicked(past, i)))
        return b

    def strip_menu(pos=None):
        from PySide6.QtGui import QCursor
        menu = QMenu(dock)
        act = menu.addAction("Show names under the icons")
        act.setCheckable(True)
        act.setChecked(state['labels'])

        def set_labels(on):
            state['labels'] = bool(on)
            s = load_settings()
            s['labels'] = bool(on)
            save_settings(s)
            rebuild(force=True)
        act.toggled.connect(set_labels)
        sub = menu.addMenu("Button size")
        for name, z in SIZES:
            a = sub.addAction(name)
            a.setCheckable(True)
            a.setChecked(abs(state['zoom'] - z) < 0.01)

            def pick(_=False, z=z):
                state['zoom'] = z
                setting('zoom', z)
                apply_size()
                rebuild(force=True)
            a.triggered.connect(pick)
        menu.addSeparator()
        menu.addAction("Hide the timeline (Ctrl+Alt+T brings it back)", lambda: dock.setVisible(False))
        menu.exec(QCursor.pos())
        menu.deleteLater()

    # right-click anywhere on the timeline that isn't a step
    for w in (outer, body, scroll, scroll.viewport(), strip, count, warn):
        w.setContextMenuPolicy(Qt.CustomContextMenu)
        w.customContextMenuRequested.connect(lambda pos: _safe(strip_menu))
    btn_menu.clicked.connect(lambda: _safe(strip_menu))

    def rebuild(force=False):
        vp = find_viewport(win)
        fresh = vp is not state['vp']          # a new tab or file: its steps aren't new
        if fresh:
            state['vp'] = vp
            force = True
        h = getattr(vp, 'history', None)
        if h is None:
            sig = None
        else:
            u, r = h.undo_stack, h.redo_stack
            sig = (id(vp), len(u), len(r), id(u[-1]) if u else 0, id(r[-1]) if r else 0,
                   id(u[0]) if u else 0)
        if sig == state['sig'] and not force:
            return
        old = state['sig']
        state['sig'] = sig
        # greyed steps thrown away by a new change: say so once
        if (old and sig and not fresh and old[0] == sig[0] and old[2] > 0 and sig[2] == 0
                and sig[1] == old[1] + 1 and sig[3] != old[4]):
            lost = old[2]
            _flash(vp, "Timeline: %d greyed step%s dropped by the new change%s." % (
                lost, "" if lost == 1 else "s",
                " - the checkpoint you saved still has them" if state.get('cp_at_latest') else ""), 8000)
            state['cp_at_latest'] = False
        all_steps = steps()
        # note when each step first turned up, and the tool in use then
        now = time.time()
        alive = set()
        tool = getattr(getattr(vp, 'active_tool', None), 'name', None)
        h_undo = list(getattr(h, 'undo_stack', None) or [])
        newest = h_undo[-1] if h_undo else None
        new_steps = 0
        for c, _done in all_steps:
            alive.add(id(c))
            if id(c) not in state['sids']:
                state['sid_n'] += 1
                state['sids'][id(c)] = "%s:%d" % (state['prefix'], state['sid_n'])
            if id(c) not in state['seen']:
                state['seen'][id(c)] = None if (fresh or not state.get('primed')) else now
                if not fresh and state.get('primed'):
                    new_steps += 1
                # the tool in use as a step appears is the one that made it
                if tool and c is newest and not fresh and state.get('primed'):
                    state['tools'][id(c)] = str(tool)
        state['primed'] = True
        for d in (state['seen'], state['tools'], names, state['marks'], state['sids']):
            for k in [k for k in d if k not in alive]:
                del d[k]
        n_done = cur()
        past = sync_file(vp, all_steps, n_done, fresh) if vp is not None else []
        # automatic checkpoint every so many new steps
        if fresh:
            state['since_cp'] = 0
        state['since_cp'] += new_steps
        every = int(state['settings'].get('auto_every') or 0)
        if every and state['since_cp'] >= every and doc_path(win):
            state['since_cp'] = 0
            QTimer.singleShot(0, lambda: _safe(lambda: make_checkpoint(True)))
        # rebuild the row of icons
        if not dock.isVisible() and not force:
            return
        while strip_row.count():
            it = strip_row.takeAt(0)
            w = it.widget()
            if w is not None:
                w.deleteLater()
        head = None
        btn_past.setVisible(bool(past))
        if past:
            btn_past.setText(("\u25B8 %d earlier" if not state['show_past'] else "\u25C2 %d earlier") % len(past))
            btn_past.setToolTip("Steps from earlier sessions, kept with the file. Click to show or hide them.")
            if state['show_past']:
                linked = set()
                try:
                    _f, cps = list_checkpoints(win)
                    linked = {c.get('after') for c in cps if c.get('after')}
                except Exception:
                    pass
                start = max(0, len(past) - SHOW_PAST)
                for i in range(start, len(past)):
                    e = past[i]
                    strip_row.addWidget(past_chip(i, e, past))
                    if e.get('id') and e['id'] in linked:
                        flag = QLabel()
                        flag.setPixmap(flag_pixmap(Z(14)))
                        flag.setToolTip("A checkpoint was saved here")
                        strip_row.addWidget(flag)
                opened = QLabel(" opened ")
                opened.setStyleSheet("color: gray; border-left: 2px dotted gray; padding-left: 3px;")
                opened.setToolTip("This session starts here.")
                strip_row.addWidget(opened)
        if n_done == 0:
            head = playhead()
            strip_row.addWidget(head)
        for i, (c, done) in enumerate(all_steps):
            strip_row.addWidget(chip(i, c, done))
            if id(c) in state['marks']:
                flag = QLabel()
                flag.setPixmap(flag_pixmap(Z(18)))
                flag.setToolTip("Checkpoint saved here: %s" % state['marks'][id(c)])
                strip_row.addWidget(flag)
            if i + 1 == n_done:
                head = playhead()
                strip_row.addWidget(head)
        strip_row.addStretch(1)
        if not all_steps:
            empty = QLabel("Nothing yet: each thing you draw or change appears here.")
            empty.setStyleSheet("color: gray;")
            strip_row.insertWidget(strip_row.count() - 1, empty)
        count.setText("%d of %d" % (n_done, len(all_steps)) if all_steps else "")
        btn_start.setEnabled(n_done > 0)
        btn_back.setEnabled(n_done > 0)
        btn_fwd.setEnabled(n_done < len(all_steps))
        btn_end.setEnabled(n_done < len(all_steps))
        ahead = len(all_steps) - n_done
        if ahead == 0 and new_steps:
            state['cp_at_latest'] = False       # new work since: the checkpoint doesn't have it
        warn.setVisible(ahead > 0)
        if ahead:
            warn_text.setText("Rolled back: %d greyed step%s. Changing anything here throws them away%s." % (
                ahead, "" if ahead == 1 else "s",
                " (your checkpoint still has them)" if state.get('cp_at_latest') else
                " - save a checkpoint first to keep them"))
            warn_cp.setVisible(not state.get('cp_at_latest') and doc_path(win) is not None)
        if head is not None:
            QTimer.singleShot(0, lambda: _safe(lambda: scroll.ensureWidgetVisible(head, 80, 0)))

    timer = QTimer(dock)
    timer.setInterval(POLL_MS)
    timer.timeout.connect(lambda: _safe(rebuild))
    timer.start()
    dock._eddy_rebuild = rebuild
    dock._eddy_timer = timer
    dock.visibilityChanged.connect(lambda on: on and _safe(lambda: rebuild(True)))
    dock.visibilityChanged.connect(lambda on: _remember_visible(win, on))
    apply_size()
    body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    win.addDockWidget(Qt.BottomDockWidgetArea, dock)
    _safe(lambda: rebuild(True))
    return dock


def _remember_visible(win, on):
    """Only when you show or hide it: not when IngeTrazo itself is closing."""
    try:
        if not win.isVisible():
            return
    except Exception:
        return
    s = load_settings()
    if s.get('visible') != bool(on):
        s['visible'] = bool(on)
        save_settings(s)


LOG_FILE = os.path.join(os.path.expanduser("~"), "ingetrazo_timeline_log.txt")


def _try(parent, fn):
    """For things you click: if it goes wrong, say so (and keep the details in a log)."""
    try:
        fn()
    except Exception as e:
        import traceback
        detail = traceback.format_exc()
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write("%s\n%s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), detail))
        except Exception:
            pass
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(parent, PLUGIN_NAME, "That didn't work: %s\n\nThe details are in %s"
                                % (e, LOG_FILE))
        except Exception:
            print(detail)


def _safe(fn):
    try:
        fn()
    except Exception as e:                 # never let the strip break IngeTrazo
        if not getattr(_safe, '_told', False):
            _safe._told = True
            print("%s: %s" % (PLUGIN_NAME, e))


def find_dock(win=None):
    from PySide6.QtWidgets import QDockWidget
    win = win or _main_window()
    return win.findChild(QDockWidget, DOCK_NAME) if win is not None else None


def show_timeline(win, show=None):
    dock = find_dock(win) or make_dock(win)
    if show is None:
        show = not dock.isVisible()
    dock.setVisible(bool(show))
    if show:
        dock.raise_()
    return dock


def add_to_view_menu(win, dock):
    """A tick-box 'Timeline' in IngeTrazo's View menu, to show or hide the strip."""
    try:
        act = dock.toggleViewAction()
        act.setText("3D Timeline")
        act.setShortcut("")                 # Ctrl+Alt+T belongs to the tool already
        act.setToolTip("Show or hide the timeline strip (Ctrl+Alt+T)")
        for a in win.menuBar().actions():
            m = a.menu()
            t = (a.text() or "").replace("&", "").strip().lower()
            if m is not None and t in ("view", "window", "ver", "vista", "ventana", "affichage", "ansicht", "visualizza"):
                if act not in m.actions():
                    m.addSeparator()
                    m.addAction(act)
                return True
    except Exception as e:
        print("%s: could not add to the View menu (%s)" % (PLUGIN_NAME, e))
    return False


def _install_when_ready(tries=0):
    """IngeTrazo loads plugins before its window is up, so wait for the window."""
    try:
        from PySide6.QtCore import QTimer
        win = _main_window()
        if win is None or not win.isVisible():
            if tries < 240:
                QTimer.singleShot(500, lambda: _install_when_ready(tries + 1))
            return
        if find_dock(win) is None:
            dock = make_dock(win)
            dock.setVisible(bool(load_settings().get('visible', True)))
            add_to_view_menu(win, dock)
    except Exception as e:
        print("%s: could not add the timeline (%s). Press Ctrl+Alt+T to try again." % (PLUGIN_NAME, e))


class TimelineTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+T"
    description = ("A strip of every step you've made: click a step to roll the model back to it, "
                   "or forward again.")

    def on_activate(self, viewport):
        win = None
        try:
            win = viewport.window()
        except Exception:
            pass
        win = win or _main_window()
        if win is None:
            return
        show_timeline(win)

    def on_deactivate(self, viewport):
        # IngeTrazo needs every tool to have this, or it leaves the tool out of its menus
        pass


try:
    from PySide6.QtCore import QTimer as _QT
    _QT.singleShot(0, _install_when_ready)
except Exception:
    pass
