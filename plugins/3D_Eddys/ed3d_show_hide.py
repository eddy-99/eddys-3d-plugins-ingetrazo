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
while you work, in build order: the floors, plates and roof of a Floor Plan building (step 1),
and the boards, roof panels and loose trusses of a Subframe (step 3). The last tab, 'All groups',
lists every main group in the model (and the groups one level inside them): tick to show, and
tick 'Print' and click 'Select to print' to select them in the model, so 3D Scale Studio
(with 'Follow selection' ticked) takes just those groups. Ticked = shown, untick to hide. Each click is one Ctrl+Z step, using
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
                               QCheckBox, QPushButton, QTabWidget, QMessageBox, QTreeWidget,
                               QTreeWidgetItem, QHeaderView)

PLUGIN_NAME = "3D Show / Hide"
VERSION = "2.15"             # shown in the window title, so you can tell which file is loaded
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


PRINT_PIECE_KEY = "ed3d_print_piece"     # read by 3D Scale Studio: groups with the same name print as one


def _print_tag(g):
    ext = getattr(g, 'ext', None)
    if isinstance(ext, dict):
        t = ext.get(PRINT_PIECE_KEY)
        if isinstance(t, str):
            return t.strip()
    return ""


def _set_print_tag(g, name):
    ext = getattr(g, 'ext', None)
    if not isinstance(ext, dict):
        try:
            g.ext = {}
            ext = g.ext
        except Exception:
            return
    if name:
        ext[PRINT_PIECE_KEY] = name
    else:
        ext.pop(PRINT_PIECE_KEY, None)


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
        print("%s: Hide didn't take (%s) - doing it by hand" % (PLUGIN_NAME, e))
    # anything the Hide didn't reach (a group inside another, say): done by hand
    for e in ents:
        if is_hidden(e) != bool(hidden):
            try:
                e.hidden = bool(hidden)
            except Exception:
                pass
    try:
        sc = viewport.scene
        sc.version += 1
    except Exception:
        pass
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
    title = "1 Floors"
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
        b_fl = QPushButton("Hide floors")
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
    title = "3 Frame"
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
            try:
                from PySide6.QtWidgets import QSizePolicy
                cb.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)    # lets the window go narrow
            except Exception:
                pass
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


class GroupsPage(QWidget):
    """Every main group in the model, and the groups one level inside each: tick to show or
    hide it; tick 'Print' and click 'Select to print' to select those groups in the model,
    so Scale Studio (with 'Follow selection' ticked) takes just them - a whole storey, the
    Subframe, the boards, the gutters... - without hunting through IngeTrazo's small group list."""
    key = 'groups'
    title = "Groups"
    plugin = None

    def __init__(self, win):
        super().__init__()
        self.win = win
        self._sig = None
        self._picked = set()          # ids of the groups ticked to print
        self._items = {}              # id -> (group, tree item)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(3)
        self.lbl = QLabel("Left tick: shown or hidden.  'Pick' tick: what the buttons work on.")
        self.lbl.setToolTip("Tick 'Pick' on what you want to print, then 'Select to print': those groups are "
                            "selected in the model, so Scale Studio (with 'Follow selection' ticked) has just them. "
                            "Double-click a group to select just that one.")
        self.lbl.setWordWrap(True)
        lay.addWidget(self.lbl)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Shown  (untick to hide)", "Pick", "Prints as"])
        try:
            hi = self.tree.headerItem()
            hi.setToolTip(0, "The tick by each name shows or hides that group in the model - it's not for picking. "
                             "Untick to hide it; tick to show it again.")
            hi.setToolTip(1, "Tick 'Pick' on the groups you want a button below to work on (join, separate, "
                             "select to print...).")
        except Exception:
            pass
        self.tree.setIndentation(14)
        try:
            from PySide6.QtWidgets import QAbstractItemView
            try:
                self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            except Exception:
                self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        except Exception:
            pass
        try:
            # drag the lines between the column headings to make any column wider or narrower
            hd = self.tree.header()
            for c_ in range(3):
                hd.setSectionResizeMode(c_, QHeaderView.Interactive)
            hd.setMinimumSectionSize(30)
            hd.setStretchLastSection(True)
            w_ = (_load().get('group_cols') or [170, 40])
            self.tree.setColumnWidth(0, int(w_[0]))
            self.tree.setColumnWidth(1, int(w_[1]))
            hd.sectionResized.connect(lambda *_a: _save(group_cols=[self.tree.columnWidth(0),
                                                                     self.tree.columnWidth(1)]))
        except Exception:
            pass
        self.tree.setMinimumHeight(60)
        self.tree.setMinimumWidth(80)
        self.tree.itemChanged.connect(self._item_changed)
        self.tree.itemDoubleClicked.connect(self._double)
        self.tree.itemClicked.connect(self._clicked)
        lay.addWidget(self.tree, 1)
        row = QGridLayout()
        row.setSpacing(2)
        b_sel = QPushButton("Select to print")
        b_sel.setToolTip("Selects every group ticked 'Pick' in the model (and nothing else), so Scale "
                         "Studio - with 'Follow selection' ticked - sizes and prints just those.")
        b_sel.clicked.connect(self.select_picked)
        b_clr = QPushButton("Clear all Pick ticks")
        b_clr.setToolTip("Unticks every 'Pick' box.")
        b_clr.clicked.connect(self.clear_picks)
        b_only = QPushButton("Show only these")
        b_only.setToolTip("Hides every main group that has nothing ticked 'Pick' in it, so you see just "
                          "what you're going to print. 'Show everything' brings the rest back.")
        b_only.clicked.connect(self.show_only_picked)
        row.addWidget(b_sel, 0, 0, 1, 2)
        row.addWidget(b_clr, 1, 0)
        row.addWidget(b_only, 1, 1)
        b_join = QPushButton("Join as one print piece...")
        b_join.setToolTip("Click the groups that print together (Ctrl+click for more - say a wall's ground "
                          "and first floor), then this: give the piece a name, and Scale Studio prints them as "
                          "one piece - no joining in 'Plan the pieces'. Saved with your model.")
        b_join.clicked.connect(lambda *_a: self.join_piece(hide=False))
        b_sep = QPushButton("Separate")
        b_sep.setToolTip("The groups you've clicked print on their own again (their 'Prints as' is cleared).")
        b_sep.clicked.connect(self.separate_piece)
        b_jh = QPushButton("Join && hide...")
        b_jh.setToolTip("Joins the clicked groups into one print piece (as 'Join as one print piece') and hides "
                        "them, so what's left is easier to see and pick. Tick them to show them again.")
        b_jh.clicked.connect(lambda *_a: self.join_piece(hide=True))
        row.addWidget(b_join, 2, 0)
        row.addWidget(b_jh, 2, 1)
        row.addWidget(b_sep, 3, 0, 1, 2)
        lay.addLayout(row)
        self.lbl_n = QLabel()                 # how many are ticked 'Pick' (kept up to date)
        lay.addWidget(self.lbl_n)
        self.lbl2 = QLabel()                  # what you just did (stays until you do something else)
        self.lbl2.setWordWrap(True)
        lay.addWidget(self.lbl2)

    # ---- the model's groups
    def _tops(self):
        sc = self.win.scene()
        return [g for g in _items(getattr(sc, 'groups', None)) if g is not None] if sc is not None else []

    @staticmethod
    def _kids(g):
        return [c for c in _items(getattr(g, 'children', None))
                if c is not None and (getattr(c, 'children', None) is not None or getattr(c, 'mesh', None) is not None)]

    @staticmethod
    def _name(g):
        return str(getattr(g, 'name', '') or 'Group')

    def refresh(self):
        tops = self._tops()
        rows = self._rows(tops)
        sig = tuple(path for path, _g, _par in rows)
        if sig != self._sig:
            self._sig = sig
            self._rebuild(rows)
        else:
            # the same groups: keep the list (and what's clicked and opened), just catch up with them
            for path, g, _par in rows:
                if path in self._items:
                    self._items[path] = (g, self._items[path][1])
        self._sync()

    def _rows(self, tops):
        """[(path, group, parent path)] - each named by its place in the model (by names, which stay the
        same while you work, so the list isn't rebuilt - and what you've clicked isn't lost - all the time)."""
        out, seen = [], {}

        def key(base):
            seen[base] = seen.get(base, 0) + 1
            return base if seen[base] == 1 else "%s#%d" % (base, seen[base])
        for t in tops:
            tp = key(self._name(t))
            out.append((tp, t, None))
            for c in self._kids(t):
                out.append((key(tp + "/" + self._name(c)), c, tp))
        return out

    def _rebuild(self, rows):
        open_, sel_ = set(), set()
        for path, (_g, it) in self._items.items():
            try:
                if it.isExpanded():
                    open_.add(path)
                if it.isSelected():
                    sel_.add(path)
            except Exception:
                pass
        self.tree.blockSignals(True)
        self.tree.clear()
        self._items = {}
        live = set()
        for path, g, par in rows:
            it = QTreeWidgetItem([self._name(g), "", ""])
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(0, Qt.Checked)
            it.setCheckState(1, Qt.Unchecked)
            it.setData(0, Qt.UserRole, path)
            if par is None or par not in self._items:
                self.tree.addTopLevelItem(it)
            else:
                self._items[par][1].addChild(it)
            self._items[path] = (g, it)
            live.add(path)
        for path, (_g, it) in self._items.items():
            if it.childCount():
                it.setExpanded(path in open_)     # just the main groups, until you open one (its arrow)
            if path in sel_:
                it.setSelected(True)
        self._picked &= live
        self.tree.blockSignals(False)
        if not rows:
            self.lbl2.setText("No groups in the model yet.")

    def _sync(self):
        self.tree.blockSignals(True)
        for gid, (g, it) in self._items.items():
            it.setCheckState(0, Qt.Unchecked if getattr(g, 'hidden', False) else Qt.Checked)
            it.setCheckState(1, Qt.Checked if gid in self._picked else Qt.Unchecked)
            it.setText(2, _print_tag(g))
        self.tree.blockSignals(False)
        n = len(self._picked)
        self.lbl_n.setText("%d group%s ticked 'Pick'." % (n, "" if n == 1 else "s") if n else
                          "Nothing ticked 'Pick'.")

    def _item_changed(self, it, col):
        gid = it.data(0, Qt.UserRole)
        g = self._items.get(gid, (None, None))[0]
        if g is None:
            return
        if col == 0:
            hide_things(self.win.viewport, [g], it.checkState(0) != Qt.Checked)
            self.win.changed()
        elif col == 1:
            if it.checkState(1) == Qt.Checked:
                self._picked.add(gid)
            else:
                self._picked.discard(gid)
            self._sync()

    def _select(self, gs):
        """Selects the groups in the model (so they light up), whichever way this IngeTrazo does it.
        Returns how it was done, or None."""
        sc, vp = self.win.scene(), self.win.viewport
        if sc is None:
            return None
        how = None
        # IngeTrazo's own 'select these' first, if it has one
        for owner in (sc, vp):
            for fn in ('set_selection', 'select_only', 'select_entities', 'select'):
                m = getattr(owner, fn, None)
                if callable(m) and how is None:
                    try:
                        m(list(gs))
                        how = fn
                    except Exception:
                        pass
        if how is None:
            sel = getattr(sc, 'selection', None)
            try:
                if hasattr(sel, 'clear') and hasattr(sel, 'add'):
                    sel.clear()
                    for g in gs:
                        sel.add(g)
                    how = 'selection.add'
                elif hasattr(sel, 'clear') and hasattr(sel, 'append'):
                    sel.clear()
                    sel.extend(gs)
                    how = 'selection list'
                else:
                    sc.selection = type(sel)(gs) if sel is not None else list(gs)
                    how = 'selection set'
            except Exception as e:
                self.lbl2.setText("Couldn't select it: %s" % e)
                return None
        for owner in (sc, vp):
            for fn in ('notify_selection_changed', 'selection_changed', 'notify_scene_changed'):
                m = getattr(owner, fn, None)
                if callable(m):
                    try:
                        m()
                    except Exception:
                        pass
        for fn in ('update', 'repaint'):
            m = getattr(vp, fn, None)
            if callable(m):
                try:
                    m()
                except Exception:
                    pass
        try:
            sc.version += 1
        except Exception:
            pass
        n_ = len(_items(getattr(sc, 'selection', None)))
        print("%s: selected %d group(s) by %s; the selection now holds %d" % (PLUGIN_NAME, len(gs), how, n_))
        return how

    def _clicked(self, it, col):
        # one click on a group lights it up in the model (it's selected there)
        gid = it.data(0, Qt.UserRole)
        g = self._items.get(gid, (None, None))[0]
        if g is None:
            return
        if getattr(g, 'hidden', False):
            self.lbl2.setText("'%s' is hidden - tick it to show it, then click it to light it up." % self._name(g))
            return
        gs = [x for x in self._clicked_groups() if not getattr(x, 'hidden', False)] or [g]
        how = self._select(gs)
        if how:
            self.lbl2.setText("Lit up in the model: %s" % ", ".join(self._name(x) for x in gs[:4]) +
                              (" and %d more" % (len(gs) - 4) if len(gs) > 4 else ""))

    def _targets(self):
        """What the join buttons work on: the groups ticked 'Pick' - or, with none ticked, what's selected
        in the model (groups, or the groups the selected faces are in) - or the ones clicked in the list."""
        return self._picked_groups() or self._model_groups() or self._clicked_groups()

    def _model_groups(self):
        """The groups selected in the model: a selected face counts as the group it's in."""
        sc = self.win.scene()
        sel = _items(getattr(sc, 'selection', None)) if sc is not None else []
        if not sel:
            return []
        out, seen = [], set()

        def add(g):
            if g is not None and id(g) not in seen:
                seen.add(id(g))
                out.append(g)
        faces = []
        for e in sel:
            if getattr(e, 'children', None) is not None or getattr(e, 'mesh', None) is not None:
                add(e)                                  # a group
            else:
                faces.append(e)                         # a face (or an edge)
        if faces:
            # which group's mesh each face is in
            owner = {}

            def walk(g, depth=0):
                m = getattr(g, 'mesh', None)
                for f in _items(getattr(m, 'faces', None)):
                    owner[id(f)] = g
                for ed in _items(getattr(m, 'edges', None)):
                    owner[id(ed)] = g
                if depth < 20:
                    for c in _items(getattr(g, 'children', None)):
                        walk(c, depth + 1)
            for t in _items(getattr(sc, 'groups', None)):
                walk(t)
            for f in faces:
                add(owner.get(id(f)))
        return out

    def _clicked_groups(self):
        out = []
        for it in self.tree.selectedItems():
            g = self._items.get(it.data(0, Qt.UserRole), (None, None))[0]
            if g is not None:
                out.append(g)
        return out

    def join_piece(self, hide=False):
        try:
            self._join_piece(bool(hide))
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.lbl2.setText("Couldn't join them: %s" % e)

    def _join_piece(self, hide=False):
        """The clicked groups print as one piece (a name kept on each, saved with the model)."""
        from PySide6.QtWidgets import QInputDialog
        gs = self._targets()
        if len(gs) < 1:
            self.lbl2.setText("Tick 'Pick' on the groups that print together first - or select them in the model "
                              "(Ctrl+click), then the button.")
            return
        have = sorted(set(t for t in (_print_tag(g) for g in self._all_groups()) if t))
        first = _print_tag(gs[0]) or self._name(gs[0]).split(" - ")[-1]
        name, ok = QInputDialog.getItem(self, PLUGIN_NAME, "A name for this print piece (pick one you've made "
                                        "to add these to it):", [first] + [h for h in have if h != first], 0, True)
        name = str(name or "").strip() if ok else ""
        if not name:
            return
        for g in gs:
            _set_print_tag(g, name)
        self._picked = set()                   # done with those: the ticks clear for the next lot
        self._touched()
        n_ = sum(1 for g in self._all_groups() if _print_tag(g) == name)
        msg = ("\u2714 '%s' prints as one piece (%d group%s). Scale Studio does the rest - no joining "
               "needed in 'Plan the pieces'." % (name, n_, "" if n_ == 1 else "s"))
        if hide:
            try:
                sc = self.win.scene()
                sc.selection.clear()               # nothing selected, so hidden things aren't lit up
            except Exception:
                pass
            hide_things(self.win.viewport, gs, True)
            still = [g for g in gs if not getattr(g, 'hidden', False)]
            self.tree.clearSelection()
            self.win.changed()
            msg += (" Hidden - tick them to show them again." if not still else
                    " (%d couldn't be hidden.)" % len(still))
        self.lbl2.setText(msg)

    def separate_piece(self):
        gs = [g for g in self._targets() if _print_tag(g)]
        if not gs:
            self.lbl2.setText("Tick 'Pick' on the joined groups to separate (their 'Prints as' shows a name).")
            return
        for g in gs:
            _set_print_tag(g, "")
        self._picked = set()
        self._touched()
        self.lbl2.setText("%d group%s will print on %s own again." % (len(gs), "" if len(gs) == 1 else "s",
                                                                     "its" if len(gs) == 1 else "their"))

    def _all_groups(self):
        return [g for g, _it in self._items.values()]

    def _touched(self):
        # the model has changed (so it's saved), and the list shows the new names
        sc = self.win.scene()
        for fn in ('mark_modified', 'set_modified', 'mark_dirty'):
            m = getattr(sc, fn, None)
            if callable(m):
                try:
                    m()
                    break
                except Exception:
                    pass
        try:
            sc.modified = True
        except Exception:
            pass
        try:
            sc.version += 1
        except Exception:
            pass
        try:
            self.win.viewport.notify_scene_changed()
        except Exception:
            pass
        self._sync()

    def _double(self, it, col):
        # double-click a group: it's the only one ticked to print, and it's selected at once
        gid = it.data(0, Qt.UserRole)
        if gid in self._items:
            self._picked = {gid}
            self._sync()
            self.select_picked()

    def _picked_groups(self):
        return [self._items[i][0] for i in self._picked if i in self._items]

    def select_picked(self):
        sc = self.win.scene()
        gs = self._picked_groups()
        if sc is None:
            return
        if not gs:
            self.lbl2.setText("Tick 'Pick' on the groups you want first (or double-click one).")
            return
        hid = [g for g in gs if getattr(g, 'hidden', False)]
        if hid:
            hide_things(self.win.viewport, hid, False)       # can't print what you can't see
        if not self._select(gs):
            return
        names = ", ".join(self._name(g) for g in gs[:4]) + (" and %d more" % (len(gs) - 4) if len(gs) > 4 else "")
        self.lbl2.setText("\u2714 Selected: %s. Scale Studio (with 'Follow selection' ticked) now has just "
                          "these." % names)

    def clear_picks(self):
        self._picked = set()
        self._sync()

    def show_only_picked(self):
        gs = self._picked_groups()
        if not gs:
            self.lbl2.setText("Tick 'Pick' on the groups you want first.")
            return
        keep = set(self._picked)
        rows = self._rows(self._tops())
        kids_of = {}
        for path, g, par in rows:
            if par is not None:
                kids_of.setdefault(par, []).append((path, g))
        hide, show = [], []
        for path, t, par in rows:
            if par is not None:
                continue
            kids = kids_of.get(path, [])
            if path in keep:
                show.append(t)
                continue
            if any(cp in keep for cp, _c in kids):
                show.append(t)                     # its picked groups stay; the rest of it goes
                for cp, c in kids:
                    (show if cp in keep else hide).append(c)
            else:
                hide.append(t)
        hide_things(self.win.viewport, show, False)
        hide_things(self.win.viewport, hide, True)
        self.win.changed()

    def show_all(self):
        every = [g for g, _it in self._items.values()]
        hide_things(self.win.viewport, every, False)


TAB_TIPS = {'floors': "Step 1, Floor Plan: each storey's walls and floor, the plates and the roof.",
            'roof': "Step 3, Subframe: the roof panels, the fascia, barge and soffit boards, and loose trusses.",
            'groups': "Every main group in the model: show or hide it, and pick what to print."}

# the tabs, in order (the build order) - add new pages here
PAGES = [FloorsPage, RoofPage, GroupsPage]


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
        self.setMinimumSize(100, 100)          # drag it as small as you like
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
            # each page scrolls, so the window can be dragged as small as you like
            from PySide6.QtWidgets import QScrollArea, QFrame
            sa = QScrollArea()
            sa.setWidgetResizable(True)
            try:
                sa.setFrameShape(getattr(QFrame, 'NoFrame', None) or QFrame.Shape.NoFrame)
            except Exception:
                pass
            sa.setWidget(pg)
            self.tabs.addTab(sa, cls.title)
            self.tabs.setTabToolTip(self.tabs.count() - 1, TAB_TIPS.get(cls.key, ""))
        try:
            self.tabs.setUsesScrollButtons(True)
        except Exception:
            pass
        lay.setContentsMargins(4, 4, 4, 4)
        lay.addWidget(self.tabs)
        row = QHBoxLayout()
        b_all = QPushButton("Show all")
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
        i_ = self.tabs.currentIndex()
        pg = self.pages[i_] if 0 <= i_ < len(self.pages) else None
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
        try:
            main_up = _main_window() is not None and _main_window().isVisible()
        except Exception:
            main_up = False
        if main_up and not _WATCH.get('quitting'):
            _remember_open(False)             # you closed it: this model opens without it next time
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
    mk = _model_key()
    if mk and (PLUGIN_NAME + " | " + mk) not in _eddy_places() and PLUGIN_NAME in _eddy_places():
        # first time with this model: start where it was last time with any model
        try:
            d = _eddy_places()
            d[PLUGIN_NAME + " | " + mk] = d[PLUGIN_NAME]
            with open(EDDY_PLACES_FILE, "w", encoding="utf-8") as f:
                json.dump(d, f, indent=1)
        except Exception:
            pass
    # opens where you left it with this model (each model remembers its own place)
    eddy_window(w, PLUGIN_NAME + (" | " + mk if mk else ""), None, place=True)
    w.show()
    _remember_open(True)
    return w


# ---------------------------------------------------------------------------
# Each model remembers whether Show / hide was open (and where): open that model again and the
# window comes back by itself, in the same place.
# ---------------------------------------------------------------------------
def _main_window():
    from PySide6.QtWidgets import QApplication, QMainWindow
    app = QApplication.instance()
    if app is None:
        return None
    wins = [w for w in app.topLevelWidgets() if isinstance(w, QMainWindow)]
    shown = [w for w in wins if w.isVisible()]
    return (shown or wins or [None])[0]


def _find_viewport(win):
    for attr in ('viewport', '_viewport', 'view'):
        vp = getattr(win, attr, None)
        if vp is not None and getattr(vp, 'scene', None) is not None:
            return vp
    from PySide6.QtWidgets import QWidget
    for w in win.findChildren(QWidget):
        if getattr(w, 'scene', None) is not None and getattr(w, 'history', None) is not None:
            return w
    return None


def _model_key():
    """The model that's open, from IngeTrazo's window title (its file name), or None."""
    win = _main_window()
    if win is None:
        return None
    t = str(win.windowTitle() or "").replace("[*]", "").strip().lstrip("*").rstrip("*").strip()
    for sep in (" \u2014 ", " - ", " | "):
        parts = [x.strip() for x in t.split(sep) if x.strip()]
        if len(parts) > 1:
            named = [x for x in parts if "." in x or "/" in x or "\\" in x]
            t = named[0] if named else parts[0] if "ingetrazo" not in parts[0].lower() else parts[-1]
            break
    t = t.strip().lstrip("*").rstrip("*").strip()
    if not t or t.lower() in ("ingetrazo", "untitled", "new model", "untitled model"):
        return None
    return t


def _remember_open(is_open):
    mk = _model_key()
    if not mk:
        return
    d = _load().get('models') or {}
    d[mk] = bool(is_open)
    _save(models=d)


_WATCH = {'key': None, 'timer': None}


def _watch():
    try:
        mk = _model_key()
        if mk == _WATCH['key']:
            return
        _WATCH['key'] = mk
        if not mk or not (_load().get('models') or {}).get(mk):
            return
        w = ShowHideWindow._open
        if w is not None and w.isVisible():
            return
        win = _main_window()
        vp = _find_viewport(win) if win is not None else None
        if vp is not None:
            open_show_hide(vp)
    except Exception as e:
        print("%s: %s" % (PLUGIN_NAME, e))


def _start_watch(tries=0):
    try:
        from PySide6.QtCore import QTimer
        win = _main_window()
        if win is None or not win.isVisible():
            if tries < 240:
                QTimer.singleShot(500, lambda: _start_watch(tries + 1))
            return
        try:
            from PySide6.QtWidgets import QApplication
            QApplication.instance().aboutToQuit.connect(lambda: _WATCH.__setitem__('quitting', True))
        except Exception:
            pass
        if _WATCH['timer'] is None:
            t = QTimer(win)
            t.timeout.connect(_watch)
            t.start(1500)
            _WATCH['timer'] = t
    except Exception as e:
        print("%s: couldn't watch for models opening (%s)" % (PLUGIN_NAME, e))


try:
    from PySide6.QtCore import QTimer as _QT
    _QT.singleShot(1000, _start_watch)
except Exception:
    pass


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
