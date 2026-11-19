# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Check for Updates for IngeTrazo
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
3D Check for Updates - new versions of Eddy's 3D plugins, and new plugins, in one click
Reads IngeTrazo's extension catalog (the same list the Extensions window shows) and
compares Eddy's entries in it with the ones installed on this computer:
  - Updates ready: a plugin you have, with a newer version in the catalog
  - New plugins: ones you haven't got yet
Tick the ones you want and click 'Update ticked': each one is downloaded from the address
the catalog gives, checked against the catalog's SHA-256 fingerprint (a different file is
refused and nothing is changed), and installed by IngeTrazo's own extension installer.
Your old copy is kept in the backups folder. Restart IngeTrazo to use them.
It can also check by itself when IngeTrazo starts (at most once a day), but only if you
tick that box: it is off until you do. Ctrl+Alt+Shift+U opens it.

It only ever reads the catalog
(raw.githubusercontent.com/ingelibre/ingetrazo-extensions/main/catalog.json) and the
download addresses listed in it, and only installs Eddy's own entries.
"""

import os
import re
import json
import time
import shutil
import hashlib
import threading
from tools.base import Tool

PLUGIN_NAME = "3D Check for Updates"
VERSION = "1.2"           # 1.2: reads IngeTrazo's catalog, checks each download's SHA-256, startup check off by default

GITHUB_OWNER = "eddy-99"
GITHUB_REPO = "eddys-3d-plugins-ingetrazo"
PAGE_URL = "https://github.com/%s/%s" % (GITHUB_OWNER, GITHUB_REPO)
CATALOG_URL = "https://raw.githubusercontent.com/ingelibre/ingetrazo-extensions/main/catalog.json"
PLUGIN_FOLDER = os.path.dirname(os.path.abspath(__file__))
CHECK_EVERY = 20 * 3600       # 'once a day' (a bit less, so the same time each day still counts)
TIMEOUT = 20
MAX_CATALOG = 2 * 1024 * 1024
MAX_DOWNLOAD = 64 * 1024 * 1024


def data_dir():
    """This plugin's own folder inside IngeTrazo's data folder (next to 'plugins')."""
    try:
        from core.extensions import user_plugins_dir
        base = str(user_plugins_dir().parent)
    except Exception:
        from PySide6.QtCore import QStandardPaths
        base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    return os.path.join(base, "ed3d_update_checker")


def settings_file():
    return os.path.join(data_dir(), "settings.json")


def backup_dir():
    return os.path.join(data_dir(), "backups")


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
def load_settings():
    try:
        with open(settings_file(), "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def save_settings(d):
    try:
        os.makedirs(data_dir(), exist_ok=True)
        with open(settings_file(), "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)
    except Exception:
        pass


def auto_check_on():
    return bool(load_settings().get('auto', False))      # off until the user ticks it


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------
def version_key(v):
    """'1.12' is newer than '1.9' (each part is a number: 1.9, 1.10, 1.11, 1.12...).
    Old-style whole numbers of 10 or more count the way they were renumbered: 15 = 1.5, 16 = 1.6."""
    t = str(v or "").strip()
    if re.fullmatch(r"\d{2,}", t):
        t = "%s.%s" % (t[:-1], t[-1])
    parts = []
    for p in re.split(r"[.\s]+", t):
        m = re.match(r"\d+", p)
        parts.append(int(m.group(0)) if m else 0)
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


# ---------------------------------------------------------------------------
# The catalog
# ---------------------------------------------------------------------------
def fetch(url, limit):
    import urllib.request
    if not url.startswith("https://"):
        raise RuntimeError("Not a safe (https) address: %s" % url)
    req = urllib.request.Request(url, headers={
        'User-Agent': "%s/%s (IngeTrazo plugin)" % (PLUGIN_NAME.replace(" ", "-"), VERSION)})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        data = r.read(limit + 1)
    if len(data) > limit:
        raise RuntimeError("The file is too large.")
    return data


def catalog_entries():
    """Eddy's entries in IngeTrazo's catalog: [{id, version, download, sha256, name, ...}]."""
    data = json.loads(fetch(CATALOG_URL, MAX_CATALOG).decode("utf-8"))
    items = data.get("extensions") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise RuntimeError("The catalog sent something unexpected")
    out = []
    for e in items:
        if not isinstance(e, dict) or e.get("repository") != PAGE_URL:
            continue
        if not all(isinstance(e.get(k), str) and e.get(k) for k in ("id", "version", "download", "sha256")):
            continue
        if not re.fullmatch(r"[0-9a-fA-F]{64}", e["sha256"]):
            continue
        out.append(e)
    return out


def installed_version(ident):
    """The version IngeTrazo's installer recorded for ``ident``, or None."""
    try:
        from core.extension_manager import installed_info
        info = installed_info(ident) or {}
    except Exception:
        info = {}
    v = info.get("version")
    return str(v) if v else None


def by_hand(entry):
    """True when the same plugin file was put in by hand (not by the catalog)."""
    name = entry["download"].rsplit("/", 1)[-1]
    folders = list(plugin_folders())
    try:
        from core.extensions import user_plugins_dir
        root = str(user_plugins_dir())
        folders += [root, os.path.join(root, "3D_Eddys")]
    except Exception:
        pass
    return any(os.path.isfile(os.path.join(d, name)) for d in folders)


def plugin_folders():
    here = PLUGIN_FOLDER
    root = os.path.dirname(here)
    return [d for d in (here, root, os.path.join(root, "3D_Eddys")) if os.path.isdir(d)]


def friendly_error(e):
    t = str(e)
    if "403" in t or "rate limit" in t.lower():
        return "GitHub is busy (too many checks from this internet connection). Try again in an hour."
    if "404" in t:
        return "The catalog wasn't found."
    if "CERTIFICATE" in t.upper() or "SSL" in t.upper():
        return "Couldn't make a safe connection (%s)." % t
    return "Couldn't read the catalog - are you online? (%s)" % t


def check(progress=None):
    """Compares Eddy's catalog entries with what is installed. Returns a list of rows:
    {'stem', 'name', 'about', 'state', 'mine', 'theirs', 'sha', 'url', 'entry'}
    state: 'update' (newer in the catalog), 'new' (not got it), 'newer_here' (yours is newer),
           'same' (up to date), 'off' (put in by hand: use IngeTrazo's Extensions window)."""
    rows = []
    entries = sorted(catalog_entries(), key=lambda e: e["id"])
    for i, e in enumerate(entries):
        if progress:
            progress(i, len(entries), e["id"])
        names = e.get("name") if isinstance(e.get("name"), dict) else {}
        about = e.get("summary") if isinstance(e.get("summary"), dict) else {}
        mine = installed_version(e["id"])
        row = {'stem': e["id"], 'name': names.get("en") or e["id"], 'about': (about.get("en") or "")[:160],
               'mine': mine or "", 'theirs': e["version"], 'sha': e["sha256"].lower(),
               'url': e["download"], 'entry': e}
        if mine is None:
            row['state'] = 'off' if by_hand(e) else 'new'
        else:
            a, b = version_key(e["version"]), version_key(mine)
            row['state'] = 'update' if a > b else ('newer_here' if a < b else 'same')
        rows.append(row)
    return rows


def worth_telling(rows):
    """The rows the 'something new is ready' notice is about."""
    return [r for r in rows if r['state'] in ('update', 'new')]


def install(row):
    """Downloads the catalog's file, refuses it unless its SHA-256 is the catalog's, and has
    IngeTrazo's installer put it in place. The old copy goes to the backups folder."""
    from core.extension_manager import _parse_extension, install_extension
    from core.extensions import user_plugins_dir
    e = row['entry']
    data = fetch(e["download"], MAX_DOWNLOAD)
    if hashlib.sha256(data).hexdigest() != e["sha256"].lower():
        raise RuntimeError("The download is not the file the catalog lists (SHA-256 differs); nothing was changed.")
    target = os.path.join(str(user_plugins_dir()), e["id"])
    if (os.path.lexists(target) and installed_version(e["id"]) is None) or by_hand(e):
        raise RuntimeError("Put in by hand: use IngeTrazo's Extensions window to switch to the catalog copy.")
    keep = None
    if os.path.isdir(target):
        stamp = time.strftime("%Y-%m-%d %H%M%S")
        keep = os.path.join(backup_dir(), "%s %s (%s)" % (e["id"], row.get('mine') or "old", stamp))
        os.makedirs(backup_dir(), exist_ok=True)
        shutil.copytree(target, keep + ".part", ignore=shutil.ignore_patterns("__pycache__"))
    try:
        # Downloads again and checks the SHA-256 again: what is installed is what was checked.
        install_extension(_parse_extension(e))
    except Exception:
        if keep:
            shutil.rmtree(keep + ".part", ignore_errors=True)
        raise
    if keep:
        os.replace(keep + ".part", keep)
    return [target]


STATE_TEXT = {
    'update': "Update ready",
    'new': "New plugin",
    'newer_here': "Yours is newer",
    'same': "Up to date",
    'off': "Put in by hand - use IngeTrazo's Extensions window",
}

# --- Eddy's 3D plugins: hover help and remembered window places (begin) ---
import os
# The same in each of the plugins. Every box, tick and button gets a pop-up note when
# you hover over it, and each window opens where (and at the size) you last left it.
EDDY_PLACES_FILE = os.path.join(data_dir(), "windows.json")
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


# ---------------------------------------------------------------------------
# Doing the slow bits without freezing IngeTrazo
# ---------------------------------------------------------------------------
class _Job:
    """Runs fn in the background; done(result, error) is called back on IngeTrazo's side."""
    def __init__(self, fn, done, owner=None):
        from PySide6.QtCore import QTimer
        self.result, self.error, self.finished = None, None, False
        self.done = done
        self.timer = QTimer(owner)
        self.timer.setInterval(150)
        self.timer.timeout.connect(self._poll)

        def work():
            try:
                self.result = fn()
            except Exception as e:
                self.error = e
            self.finished = True
        threading.Thread(target=work, daemon=True).start()
        self.timer.start()

    def _poll(self):
        if not self.finished:
            return
        self.timer.stop()
        try:
            self.done(self.result, self.error)
        except Exception as e:
            print("%s: %s" % (PLUGIN_NAME, e))


def _main_window():
    from PySide6.QtWidgets import QApplication, QMainWindow
    app = QApplication.instance()
    if app is None:
        return None
    wins = [w for w in app.topLevelWidgets() if isinstance(w, QMainWindow)]
    shown = [w for w in wins if w.isVisible()]
    return (shown or wins or [None])[0]


def open_url(target):
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtCore import QUrl
    if target.startswith("http"):
        QDesktopServices.openUrl(QUrl(target))
    else:
        QDesktopServices.openUrl(QUrl.fromLocalFile(target))


INFO_TEXT = (
    "<b>%s</b> (version %s)<br><br>"
    "Reads IngeTrazo's extension catalog and compares Eddy's plugins in it with the ones on this computer.<br><br>"
    "<b>Update ready</b> - there's a newer version of a plugin you have.<br>"
    "<b>New plugin</b> - one you haven't got yet.<br>"
    "<b>Put in by hand</b> - not installed from the catalog; IngeTrazo's Extensions window can switch it.<br>"
    "<b>Yours is newer</b> - nothing to do.<br><br>"
    "Tick the ones you want and click <b>Update ticked</b>. Each download is checked against the "
    "catalog's SHA-256 fingerprint; a different file is refused. Your old copy is kept in the "
    "Backups folder, so you can always go back. "
    "<b>Restart IngeTrazo</b> to use the new versions.<br><br>"
    "With <b>Check when IngeTrazo starts</b> ticked (it is off until you tick it) it checks by itself "
    "(at most once a day) and only tells you when something new is ready.<br><br>"
    "Ctrl+Alt+Shift+U opens this window." % (PLUGIN_NAME, VERSION))


# ---------------------------------------------------------------------------
# The window
# ---------------------------------------------------------------------------
def make_window(parent=None):
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                   QTreeWidget, QTreeWidgetItem, QCheckBox, QMessageBox,
                                   QHeaderView, QAbstractItemView)
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont, QColor, QBrush

    class UpdatesWindow(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
            self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
            self.resize(760, 520)
            self.rows = []
            self.job = None
            lay = QVBoxLayout(self)

            head = QLabel("Eddy's 3D plugins - new versions and new plugins")
            f = QFont(head.font())
            f.setPointSize(f.pointSize() + 3)
            f.setBold(True)
            head.setFont(f)
            lay.addWidget(head)
            self.status = QLabel("")
            self.status.setWordWrap(True)
            lay.addWidget(self.status)

            self.tree = QTreeWidget()
            self.tree.setColumnCount(4)
            self.tree.setHeaderLabels(["Plugin", "Yours", "In catalog", "What it is"])
            self.tree.setRootIsDecorated(True)
            self.tree.setSelectionMode(QAbstractItemView.NoSelection)
            hd = self.tree.header()
            hd.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            hd.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            hd.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            hd.setStretchLastSection(True)
            self.tree.itemChanged.connect(lambda *_a: self.count_ticked())
            lay.addWidget(self.tree, 1)

            self.auto = QCheckBox("Check when IngeTrazo starts (at most once a day)")
            self.auto.setChecked(auto_check_on())
            self.auto.toggled.connect(self.set_auto)
            lay.addWidget(self.auto)

            row = QHBoxLayout()
            self.b_check = QPushButton("Check now")
            self.b_update = QPushButton("Update ticked")
            self.b_update.setDefault(True)
            self.b_page = QPushButton("Plugins page")
            self.b_backups = QPushButton("Backups")
            self.b_info = QPushButton("Info")
            self.b_close = QPushButton("Close")
            for b in (self.b_check, self.b_update, self.b_page, self.b_backups):
                row.addWidget(b)
            row.addStretch(1)
            row.addWidget(self.b_info)
            row.addWidget(self.b_close)
            lay.addLayout(row)
            self.b_check.clicked.connect(self.start_check)
            self.b_update.clicked.connect(self.update_ticked)
            self.b_page.clicked.connect(lambda: open_url(PAGE_URL))
            self.b_backups.clicked.connect(self.open_backups)
            self.b_info.clicked.connect(lambda: QMessageBox.information(self, PLUGIN_NAME, INFO_TEXT))
            self.b_close.clicked.connect(self.close)
            self.b_update.setEnabled(False)

        # -- settings
        def set_auto(self, on):
            s = load_settings()
            s['auto'] = bool(on)
            save_settings(s)

        def open_backups(self):
            os.makedirs(backup_dir(), exist_ok=True)
            open_url(backup_dir())

        # -- checking
        def busy(self, on, text=""):
            self.b_check.setEnabled(not on)
            self.b_update.setEnabled(not on and bool(self.ticked()))
            if text:
                self.status.setText(text)

        def start_check(self):
            if self.job is not None and not self.job.finished:
                return
            self.busy(True, "Reading IngeTrazo's extension catalog...")
            self.job = _Job(check, self.checked, self)

        def checked(self, rows, error):
            self.job = None
            if error is not None:
                self.busy(False, friendly_error(error))
                return
            s = load_settings()
            s['last_check'] = time.time()
            s['told'] = sorted(set(s.get('told') or []) | {r['stem'] + ":" + r['sha'] for r in worth_telling(rows)})
            save_settings(s)
            self.show_rows(rows)

        def show_rows(self, rows):
            self.rows = rows
            self.tree.blockSignals(True)
            self.tree.clear()
            groups = [("Updates ready", ('update',), True, True),
                      ("New plugins", ('new',), True, True),
                      ("Up to date", ('same', 'newer_here', 'off'), False, False)]
            for title, states, open_, tick in groups:
                mine = [r for r in rows if r['state'] in states]
                if not mine:
                    continue
                top = QTreeWidgetItem(["%s (%d)" % (title, len(mine))])
                f = QFont(top.font(0))
                f.setBold(True)
                top.setFont(0, f)
                top.setFirstColumnSpanned(True)
                self.tree.addTopLevelItem(top)
                top.setFirstColumnSpanned(True)
                for r in sorted(mine, key=lambda r: r['name'].lower()):
                    what = r['about'] or STATE_TEXT.get(r['state'], "")
                    if r['state'] in ('newer_here', 'off'):
                        what = STATE_TEXT[r['state']]
                    it = QTreeWidgetItem([r['name'], r['mine'] or ("-" if r['state'] != 'new' else ""),
                                          r['theirs'] or "-", what])
                    it.setToolTip(3, what)
                    if r['state'] in ('update', 'new'):
                        it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
                        it.setCheckState(0, Qt.Checked if tick else Qt.Unchecked)
                    else:
                        it.setForeground(0, QBrush(QColor(110, 110, 110)))
                    it.setData(0, Qt.UserRole, r['stem'])
                    top.addChild(it)
                top.setExpanded(open_)
            self.tree.blockSignals(False)
            n_up = len([r for r in rows if r['state'] == 'update'])
            n_new = len([r for r in rows if r['state'] == 'new'])
            if n_up or n_new:
                bits = []
                if n_up:
                    bits.append("%d update%s" % (n_up, "" if n_up == 1 else "s"))
                if n_new:
                    bits.append("%d new plugin%s" % (n_new, "" if n_new == 1 else "s"))
                text = " and ".join(bits) + " ready. Tick the ones you want and click Update ticked."
            else:
                text = "All your plugins are up to date (checked %s)." % time.strftime("%H:%M")
            self.busy(False, text)
            self.count_ticked()

        def ticked(self):
            from PySide6.QtCore import Qt
            out = []
            for i in range(self.tree.topLevelItemCount()):
                top = self.tree.topLevelItem(i)
                for j in range(top.childCount()):
                    it = top.child(j)
                    if it.flags() & Qt.ItemIsUserCheckable and it.checkState(0) == Qt.Checked:
                        out.append(it.data(0, Qt.UserRole))
            return out

        def count_ticked(self):
            n = len(self.ticked())
            self.b_update.setText("Update ticked (%d)" % n if n else "Update ticked")
            self.b_update.setEnabled(n > 0 and (self.job is None or self.job.finished))

        # -- updating
        def update_ticked(self):
            stems = set(self.ticked())
            todo = [r for r in self.rows if r['stem'] in stems]
            if not todo:
                return
            names = "\n".join("  %s  %s" % (r['name'], r['theirs']) for r in todo)
            if QMessageBox.question(self, PLUGIN_NAME,
                                    "Download and put in place:\n\n%s\n\nYour old copies are kept in the "
                                    "Plugin backups folder." % names) != QMessageBox.Yes:
                return
            self.busy(True, "Downloading...")

            def work():
                done, failed = [], []
                for r in todo:
                    try:
                        install(r)
                        done.append(r)
                    except Exception as e:
                        failed.append((r, e))
                return done, failed
            self.job = _Job(work, self.updated, self)

        def updated(self, result, error):
            self.job = None
            if error is not None:
                self.busy(False, friendly_error(error))
                return
            done, failed = result
            msg = ""
            if done:
                msg += "Done:\n" + "\n".join("  %s  %s" % (r['name'], r['theirs']) for r in done)
                msg += "\n\nRestart IngeTrazo to use the new versions."
            if failed:
                msg += ("\n\n" if msg else "") + "Not done:\n" + "\n".join(
                    "  %s: %s" % (r['name'], e if isinstance(e, RuntimeError) else friendly_error(e)) for r, e in failed)
            QMessageBox.information(self, PLUGIN_NAME, msg)
            for r in done:
                r['state'] = 'same'
                r['mine'] = r['theirs']
            self.show_rows(self.rows)
            if done:
                self.status.setText("Restart IngeTrazo to use the new versions.")

    return UpdatesWindow(parent)


# ---------------------------------------------------------------------------
# Checking by itself when IngeTrazo starts
# ---------------------------------------------------------------------------
_STARTUP = {'job': None}


def _startup_check(tries=0):
    if not auto_check_on():              # off by default: nothing is read until the user ticks the box
        return
    try:
        from PySide6.QtCore import QTimer
        win = _main_window()
        if win is None or not win.isVisible():
            if tries < 240:
                QTimer.singleShot(500, lambda: _startup_check(tries + 1))
            return
        s = load_settings()
        if not s.get('auto', False) or time.time() - float(s.get('last_check') or 0) < CHECK_EVERY:
            return
        _STARTUP['job'] = _Job(check, lambda rows, err: _startup_done(win, rows, err), win)
    except Exception as e:
        print("%s: could not check (%s)" % (PLUGIN_NAME, e))


def _startup_done(win, rows, error):
    _STARTUP['job'] = None
    if error is not None:
        print("%s: %s" % (PLUGIN_NAME, friendly_error(error)))     # quietly: try again next time
        return
    s = load_settings()
    s['last_check'] = time.time()
    told = set(s.get('told') or [])
    news = worth_telling(rows)
    fresh = [r for r in news if r['stem'] + ":" + r['sha'] not in told]
    s['told'] = sorted(told | {r['stem'] + ":" + r['sha'] for r in news})
    save_settings(s)
    if fresh:
        _tell(win, rows)


def _tell(win, rows):
    """A small note: something new is ready. 'Show me' opens the window with the list."""
    from PySide6.QtWidgets import QMessageBox
    n_up = len([r for r in rows if r['state'] == 'update'])
    n_new = len([r for r in rows if r['state'] == 'new'])
    bits = []
    if n_up:
        bits.append("%d update%s" % (n_up, "" if n_up == 1 else "s"))
    if n_new:
        bits.append("%d new plugin%s" % (n_new, "" if n_new == 1 else "s"))
    lines = "\n".join("  %s  %s" % (r['name'], r['theirs']) for r in worth_telling(rows)[:8])
    box = QMessageBox(win)
    box.setWindowTitle(PLUGIN_NAME)
    box.setIcon(QMessageBox.Information)
    box.setText("Eddy's 3D plugins: %s ready." % " and ".join(bits))
    box.setInformativeText(lines)
    show = box.addButton("Show me", QMessageBox.AcceptRole)
    box.addButton("Later", QMessageBox.RejectRole)
    box.setModal(False)

    def show_me():
        w = UpdatesTool.open_window(win)
        w.show_rows(rows)
    show.clicked.connect(show_me)
    box.show()
    UpdatesTool._note = box


# ---------------------------------------------------------------------------
# Tool: Ctrl+Alt+Shift+U opens the window and checks
# ---------------------------------------------------------------------------
class UpdatesTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+Shift+U"
    description = "Checks Eddy's plugins page for new versions of your 3D plugins, and new plugins, and puts them in."

    _window = None
    _note = None

    @staticmethod
    def open_window(parent=None):
        w = UpdatesTool._window
        if w is not None:
            try:
                w.isVisible()
            except Exception:
                w = None
        if w is None:
            w = make_window(parent or _main_window())
            UpdatesTool._window = w
            eddy_window(w, PLUGIN_NAME, EDDY_TIPS)  # eddy-window
        w.show()
        w.raise_()
        w.activateWindow()
        return w

    def on_activate(self, viewport):
        parent = None
        try:
            parent = viewport.window()
        except Exception:
            parent = None
        w = UpdatesTool.open_window(parent)
        w.start_check()

    def on_deactivate(self, viewport):
        pass


def run(viewport=None):
    """Console entry point: run() opens the window and checks."""
    UpdatesTool().on_activate(viewport)


EDDY_TIPS = {
    'Check now': "Reads IngeTrazo's extension catalog again.",
    'Update ticked': "Downloads the ticked plugins from the catalog, checks each one's SHA-256 and "
                     "installs it. Your old copies are kept in the Backups folder. Restart IngeTrazo afterwards.",
    'Plugins page': "Opens Eddy's plugins page on GitHub in your browser.",
    'Backups': "Opens the folder your old copies are kept in, in case you want one back.",
    'Info': "What this window does.",
    'Check when IngeTrazo starts (at most once a day)':
        "Checks by itself a little after IngeTrazo opens, and only tells you when something new is ready.",
    '@tree': "Tick the updates and new plugins you want, then click Update ticked.",
}
EDDY_TIPS_END = None


try:
    _startup_check()
except Exception:
    pass
