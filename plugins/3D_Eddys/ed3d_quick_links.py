# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Quick Links for IngeTrazo
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
3D Quick Links - your folders, files and web pages, one click away in IngeTrazo
A small window that floats over IngeTrazo with a list of links: click one and it opens.
Keep a set of links for each job (one for each video, say) and switch between them.
Add links with the buttons, or drag folders, files and web addresses onto the list.
Right-click a link to rename it, change where it goes, move it up or down, or remove it.
Ctrl+Alt+A shows or hides it.
"""

import os
import json
from tools.base import Tool

PLUGIN_NAME = "3D Quick Links"
LINKS_FILE = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Quick Links.json")
FIRST_SET = "My links"
PLUGIN_FOLDER = os.path.dirname(os.path.abspath(__file__))


def starter_links():
    home = os.path.expanduser("~")
    return [
        {'name': "My plugins folder", 'target': PLUGIN_FOLDER},
        {'name': "Presets and notes", 'target': os.path.join(home, "Documents", "IngeTrazo Presets")},
        {'name': "Downloads", 'target': os.path.join(home, "Downloads")},
        {'name': "Eddy's 3D plugins page", 'target': "https://github.com/eddy-99/eddys-3d-plugins-ingetrazo"},
    ]


# ---------------------------------------------------------------------------
# The links (no Qt, so they can be checked on their own)
# ---------------------------------------------------------------------------
def is_web(target):
    t = (target or "").strip().lower()
    return t.startswith(("http://", "https://", "www.", "mailto:"))


def web_url(target):
    t = (target or "").strip()
    return "https://" + t if t.lower().startswith("www.") else t


def kind_of(target):
    """'web', 'folder', 'file' or 'missing'."""
    if is_web(target):
        return 'web'
    t = os.path.expandvars(os.path.expanduser((target or "").strip().strip('"')))
    if os.path.isdir(t):
        return 'folder'
    if os.path.isfile(t):
        return 'file'
    return 'missing'


def local_path(target):
    return os.path.expandvars(os.path.expanduser((target or "").strip().strip('"')))


def name_for(target):
    """A sensible name for a new link."""
    t = (target or "").strip().rstrip("/\\")
    if is_web(t):
        u = web_url(t).split("://", 1)[-1]
        host = u.split("/", 1)[0]
        rest = [p for p in u.split("/")[1:] if p]
        return (host[4:] if host.startswith("www.") else host) + ((" - " + rest[-1]) if rest else "")
    base = os.path.basename(local_path(t))
    return base or t


def load_links():
    d = {'sets': {}, 'order': [], 'current': FIRST_SET}
    try:
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            got = json.load(f)
        if isinstance(got, dict) and isinstance(got.get('sets'), dict):
            d.update(got)
    except Exception:
        pass
    sets = {}
    for k, v in d['sets'].items():
        if isinstance(v, list):
            sets[str(k)] = [{'name': str(x.get('name') or name_for(x.get('target', ''))),
                             'target': str(x.get('target', ''))}
                            for x in v if isinstance(x, dict) and str(x.get('target', '')).strip()]
    if not sets:
        sets = {FIRST_SET: starter_links()}
    order = [n for n in d.get('order', []) if n in sets] + sorted(n for n in sets if n not in d.get('order', []))
    cur = d.get('current') if d.get('current') in sets else order[0]
    return {'sets': sets, 'order': order, 'current': cur}


def save_links(d):
    try:
        os.makedirs(os.path.dirname(LINKS_FILE), exist_ok=True)
        tmp = LINKS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)
        os.replace(tmp, LINKS_FILE)
        return True
    except Exception:
        return False


def open_target(target):
    """Opens the link the way the computer usually opens that kind of thing. Returns '' or a reason."""
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtCore import QUrl
    if is_web(target):
        ok = QDesktopServices.openUrl(QUrl(web_url(target)))
        return "" if ok else "Couldn't open %s" % target
    p = local_path(target)
    if not os.path.exists(p):
        return "Can't find it any more:\n%s\n\n(Right-click the link > Change where it goes.)" % p
    ok = QDesktopServices.openUrl(QUrl.fromLocalFile(p))
    return "" if ok else "Couldn't open %s" % p


# ---------------------------------------------------------------------------
# The window
# ---------------------------------------------------------------------------
def make_window(parent):
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel,
                                   QListWidget, QListWidgetItem, QInputDialog, QMessageBox, QMenu,
                                   QFileDialog, QFileIconProvider, QAbstractItemView, QLineEdit)
    from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush
    from PySide6.QtCore import Qt, QFileInfo, QSize, QPointF, QRectF

    def web_icon():
        pm = QPixmap(32, 32)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor(40, 90, 160), 1.6))
        p.setBrush(QColor(190, 220, 245))
        p.drawEllipse(QPointF(16, 16), 12, 12)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(16, 16), 5, 12)
        p.drawLine(QPointF(4, 16), QPointF(28, 16))
        p.drawLine(QPointF(16, 4), QPointF(16, 28))
        p.drawLine(QPointF(6, 10), QPointF(26, 10))
        p.drawLine(QPointF(6, 22), QPointF(26, 22))
        p.end()
        return QIcon(pm)

    def missing_icon():
        pm = QPixmap(32, 32)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor(190, 50, 40), 2.4))
        p.drawEllipse(QPointF(16, 16), 11, 11)
        p.drawLine(QPointF(9, 23), QPointF(23, 9))
        p.end()
        return QIcon(pm)

    class LinkList(QListWidget):
        """The list: click to open, drop folders, files or web addresses on it to add them."""

        def __init__(self, owner):
            super().__init__(owner)
            self.owner = owner
            self.setAcceptDrops(True)
            self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
            self.setDefaultDropAction(Qt.DropAction.MoveAction)
            self.setIconSize(QSize(22, 22))
            self.setSpacing(2)
            self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        def _outside(self, ev):
            return ev.source() is not self and (ev.mimeData().hasUrls() or ev.mimeData().hasText())

        def dragEnterEvent(self, ev):
            if self._outside(ev):
                ev.acceptProposedAction()
            else:
                super().dragEnterEvent(ev)

        def dragMoveEvent(self, ev):
            if self._outside(ev):
                ev.acceptProposedAction()
            else:
                super().dragMoveEvent(ev)

        def dropEvent(self, ev):
            if not self._outside(ev):
                super().dropEvent(ev)
                self.owner.order_changed()
                return
            md = ev.mimeData()
            targets = []
            if md.hasUrls():
                for u in md.urls():
                    targets.append(u.toLocalFile() if u.isLocalFile() else u.toString())
            elif md.hasText():
                targets = [t.strip() for t in md.text().splitlines() if t.strip()]
            ev.acceptProposedAction()
            self.owner.add_links([t for t in targets if t])

    class QuickLinksWindow(QDialog):
        def __init__(self, parent):
            super().__init__(parent)
            self.setWindowTitle(PLUGIN_NAME)
            self.setModal(False)
            # floats over IngeTrazo and never gets lost behind it
            self.setWindowFlags(Qt.Tool | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
            self.data = load_links()
            self.icons = QFileIconProvider()
            self._web, self._missing = web_icon(), missing_icon()
            self.resize(300, 380)
            lay = QVBoxLayout(self)
            lay.setContentsMargins(6, 6, 6, 6)
            lay.setSpacing(4)

            top = QHBoxLayout()
            top.addWidget(QLabel("Set:"))
            self.cb_set = QComboBox()
            top.addWidget(self.cb_set, 1)
            b_set = QPushButton("...")
            b_set.setFixedWidth(30)
            self.b_set = b_set
            m = QMenu(b_set)
            m.addAction("New set...", self.new_set)
            m.addAction("Copy this set...", lambda: self.new_set(copy=True))
            m.addAction("Rename this set...", self.rename_set)
            m.addAction("Delete this set", self.delete_set)
            m.addSeparator()
            m.addAction("Open the file the links are kept in", self.show_store)
            b_set.setMenu(m)
            top.addWidget(b_set)
            lay.addLayout(top)

            self.list = LinkList(self)
            self.list.itemClicked.connect(self.clicked)
            self.list.customContextMenuRequested.connect(self.menu_for)
            lay.addWidget(self.list, 1)

            self.lbl = QLabel("Click a link to open it. Drag folders, files or web addresses here to add them.")
            self.lbl.setWordWrap(True)
            self.lbl.setStyleSheet("color: gray; font-size: 9pt;")
            lay.addWidget(self.lbl)

            row = QHBoxLayout()
            self.b_folder = QPushButton("+ Folder")
            self.b_file = QPushButton("+ File")
            self.b_web = QPushButton("+ Web")
            for b in (self.b_folder, self.b_file, self.b_web):
                row.addWidget(b)
            lay.addLayout(row)
            self.b_folder.clicked.connect(self.add_folder)
            self.b_file.clicked.connect(self.add_file)
            self.b_web.clicked.connect(self.add_web)

            self.fill_sets()
            self.cb_set.currentIndexChanged.connect(self.set_picked)
            self.fill_links()

        # ---- the sets ----
        def links(self):
            return self.data['sets'].setdefault(self.data['current'], [])

        def save(self):
            if not save_links(self.data):
                self.note("Couldn't save the links to %s" % LINKS_FILE, bad=True)

        def fill_sets(self):
            self.cb_set.blockSignals(True)
            self.cb_set.clear()
            for n in self.data['order']:
                self.cb_set.addItem(n)
            self.cb_set.setCurrentIndex(max(0, self.cb_set.findText(self.data['current'])))
            self.cb_set.blockSignals(False)

        def set_picked(self, *_):
            name = self.cb_set.currentText()
            if name and name in self.data['sets']:
                self.data['current'] = name
                self.save()
                self.fill_links()

        def ask_name(self, title, text, start=""):
            normal = QLineEdit.EchoMode.Normal if hasattr(QLineEdit, 'EchoMode') else QLineEdit.Normal
            res = QInputDialog.getText(self, title, text, normal, start)
            name, ok = (res[0], res[1]) if isinstance(res, (tuple, list)) else (res, bool(res))
            return (name or "").strip() if ok else ""

        def new_set(self, copy=False):
            start = (self.data['current'] + " copy") if copy else "Video - "
            name = self.ask_name("New set", "A name for the set (e.g. the video it's for):", start)
            if not name:
                return
            if name in self.data['sets']:
                QMessageBox.information(self, PLUGIN_NAME, "You already have a set called '%s'." % name)
                return
            self.data['sets'][name] = [dict(x) for x in self.links()] if copy else []
            self.data['order'].insert(0, name)
            self.data['current'] = name
            self.save()
            self.fill_sets()
            self.fill_links()

        def rename_set(self):
            old = self.data['current']
            name = self.ask_name("Rename set", "New name for '%s':" % old, old)
            if not name or name == old:
                return
            if name in self.data['sets']:
                QMessageBox.information(self, PLUGIN_NAME, "You already have a set called '%s'." % name)
                return
            self.data['sets'][name] = self.data['sets'].pop(old)
            self.data['order'] = [name if n == old else n for n in self.data['order']]
            self.data['current'] = name
            self.save()
            self.fill_sets()

        def delete_set(self):
            old = self.data['current']
            if QMessageBox.question(self, PLUGIN_NAME, "Delete the set '%s' and its %d links?\n"
                                    "(Only the links - your folders, files and pages aren't touched.)"
                                    % (old, len(self.links()))) != QMessageBox.StandardButton.Yes:
                return
            del self.data['sets'][old]
            self.data['order'] = [n for n in self.data['order'] if n != old]
            if not self.data['order']:
                self.data['sets'][FIRST_SET] = []
                self.data['order'] = [FIRST_SET]
            self.data['current'] = self.data['order'][0]
            self.save()
            self.fill_sets()
            self.fill_links()

        def show_store(self):
            self.save()
            err = open_target(os.path.dirname(LINKS_FILE))
            if err:
                QMessageBox.information(self, PLUGIN_NAME, err)

        # ---- the links ----
        def icon_for(self, target):
            k = kind_of(target)
            if k == 'web':
                return self._web
            if k == 'missing':
                return self._missing
            try:
                return self.icons.icon(QFileInfo(local_path(target)))
            except Exception:
                return QIcon()

        def fill_links(self):
            self.list.clear()
            for i, ln in enumerate(self.links()):
                it = QListWidgetItem(self.icon_for(ln['target']), ln['name'])
                it.setData(Qt.ItemDataRole.UserRole, i)
                tip = ln['target']
                if kind_of(ln['target']) == 'missing':
                    tip += "\n(can't find it - right-click to change where it goes)"
                    it.setForeground(QColor(150, 150, 150))
                it.setToolTip(tip)
                self.list.addItem(it)
            n = len(self.links())
            self.note("Click a link to open it. Drag folders, files or web addresses here to add them." if n
                      else "No links in this set yet: use the buttons below, or drag folders, files or "
                           "web addresses here.")

        def note(self, text, bad=False):
            self.lbl.setText(text)
            self.lbl.setStyleSheet("color: %s; font-size: 9pt;" % ("#b03020" if bad else "gray"))

        def clicked(self, it):
            i = it.data(Qt.ItemDataRole.UserRole)
            if i is None or not (0 <= i < len(self.links())):
                return
            ln = self.links()[i]
            err = open_target(ln['target'])
            if err:
                self.note(err.split("\n")[0], bad=True)
                QMessageBox.information(self, PLUGIN_NAME, err)
            else:
                self.note("Opened '%s'." % ln['name'])
            self.list.clearSelection()

        def add_links(self, targets):
            added = 0
            have = {os.path.normcase(x['target']) for x in self.links()}
            for t in targets:
                t = t.strip().strip('"')
                if not t or os.path.normcase(t) in have:
                    continue
                if not is_web(t):
                    t = os.path.normpath(t)
                self.links().append({'name': name_for(t), 'target': t})
                have.add(os.path.normcase(t))
                added += 1
            if added:
                self.save()
                self.fill_links()
                self.note("Added %d link%s. Right-click one to rename it." % (added, "" if added == 1 else "s"))
            elif targets:
                self.note("Already in this set.")

        def add_folder(self):
            d = QFileDialog.getExistingDirectory(self, "Pick a folder to add", os.path.expanduser("~"))
            if d:
                self.add_links([d])

        def add_file(self):
            res = QFileDialog.getOpenFileNames(self, "Pick files to add", os.path.expanduser("~"))
            files = res[0] if isinstance(res, (tuple, list)) else res
            if files:
                self.add_links(list(files))

        def add_web(self):
            url = self.ask_name("Add a web page", "The web address (copy it from the address bar):", "https://")
            if not url or url in ("https://", "http://"):
                return
            if not is_web(url):
                url = "https://" + url
            self.add_links([url])

        def order_changed(self):
            old = self.links()
            new = []
            for r in range(self.list.count()):
                i = self.list.item(r).data(Qt.ItemDataRole.UserRole)
                if i is not None and 0 <= i < len(old):
                    new.append(old[i])
            if len(new) == len(old):
                self.data['sets'][self.data['current']] = new
                self.save()
            self.fill_links()

        def menu_for(self, pos):
            it = self.list.itemAt(pos)
            if it is None:
                return
            i = it.data(Qt.ItemDataRole.UserRole)
            ln = self.links()[i]
            m = QMenu(self)
            m.addAction("Open", lambda: self.clicked(it))
            m.addAction("Rename...", lambda: self.rename_link(i))
            m.addAction("Change where it goes...", lambda: self.retarget_link(i))
            if not is_web(ln['target']) and kind_of(ln['target']) == 'file':
                m.addAction("Open the folder it's in", lambda: self.open_parent(i))
            m.addSeparator()
            up = m.addAction("Move up", lambda: self.move_link(i, -1))
            up.setEnabled(i > 0)
            dn = m.addAction("Move down", lambda: self.move_link(i, 1))
            dn.setEnabled(i < len(self.links()) - 1)
            if len(self.data['order']) > 1:
                sub = m.addMenu("Copy to set")
                for n in self.data['order']:
                    if n != self.data['current']:
                        sub.addAction(n, lambda n=n: self.copy_to(i, n))
            m.addSeparator()
            m.addAction("Remove from this set", lambda: self.remove_link(i))
            m.exec(self.list.viewport().mapToGlobal(pos))

        def rename_link(self, i):
            ln = self.links()[i]
            name = self.ask_name("Rename link", "Name to show:", ln['name'])
            if name:
                ln['name'] = name
                self.save()
                self.fill_links()

        def retarget_link(self, i):
            ln = self.links()[i]
            t = self.ask_name("Change where it goes", "Folder, file or web address:", ln['target'])
            if t:
                ln['target'] = t if is_web(t) else os.path.normpath(t.strip('"'))
                self.save()
                self.fill_links()

        def open_parent(self, i):
            err = open_target(os.path.dirname(local_path(self.links()[i]['target'])))
            if err:
                QMessageBox.information(self, PLUGIN_NAME, err)

        def move_link(self, i, d):
            L = self.links()
            j = i + d
            if 0 <= j < len(L):
                L[i], L[j] = L[j], L[i]
                self.save()
                self.fill_links()

        def copy_to(self, i, name):
            ln = dict(self.links()[i])
            dest = self.data['sets'].setdefault(name, [])
            if all(os.path.normcase(x['target']) != os.path.normcase(ln['target']) for x in dest):
                dest.append(ln)
                self.save()
            self.note("Copied '%s' to '%s'." % (ln['name'], name))

        def remove_link(self, i):
            ln = self.links().pop(i)
            self.save()
            self.fill_links()
            self.note("Removed '%s' (only the link - nothing on your computer was touched)." % ln['name'])

        def closeEvent(self, e):
            self.save()
            super().closeEvent(e)

    return QuickLinksWindow(parent)


def _main_window():
    from PySide6.QtWidgets import QApplication, QMainWindow
    app = QApplication.instance()
    if app is None:
        return None
    wins = [w for w in app.topLevelWidgets() if isinstance(w, QMainWindow)]
    shown = [w for w in wins if w.isVisible()]
    return (shown or wins or [None])[0]


# ---------------------------------------------------------------------------
# Tool: Ctrl+Alt+A shows or hides the links
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


EDDY_TIPS = {'Set': "Your sets of links - keep one for each video or job, and pick it here.",
 '@cb_set': "Your sets of links - keep one for each video or job, and pick it here.",
 '@b_set': "New set, copy, rename or delete this set.",
 '@list': "Click a link to open it. Right-click for rename, change, move or remove. Drag links up "
          "and down to put them in order, or drag folders, files and web addresses here to add them.",
 '+ Folder': "Adds a folder to this set.",
 '+ File': "Adds one or more files to this set (they open in their usual program).",
 '+ Web': "Adds a web page to this set (paste its address)."}
EDDY_TIPS_END = None


class QuickLinksTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+A"
    description = "Your folders, files and web pages in a small window over the work area: one click opens them."

    _window = None

    def on_activate(self, viewport):
        w = QuickLinksTool._window
        if w is not None:
            try:
                if w.isVisible():
                    w.hide()
                else:
                    w.fill_links()
                    w.show()
                    w.raise_()
                    w.activateWindow()
                return
            except Exception:
                QuickLinksTool._window = None
        parent = None
        try:
            parent = viewport.window()
        except Exception:
            parent = _main_window()
        w = make_window(parent)
        QuickLinksTool._window = w
        eddy_window(w, PLUGIN_NAME, EDDY_TIPS)  # eddy-window
        w.show()
        w.raise_()

    def on_deactivate(self, viewport):
        pass


def run(viewport=None):
    """Console entry point: run() opens the quick links."""
    QuickLinksTool().on_activate(viewport)
