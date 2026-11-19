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
Looks at Eddy's plugins page on GitHub and compares it with the plugins on this computer:
  - Updates ready: a plugin you have, with a newer version on GitHub
  - New plugins: ones you haven't got yet
Tick the ones you want and click 'Update ticked': they're downloaded and put in your plugins
folder (your old copy is kept in Documents\\IngeTrazo Presets\\Plugin backups). Restart
IngeTrazo to use them.
It can also check by itself when IngeTrazo starts (at most once a day) and tell you when
something new is ready. Ctrl+Alt+Shift+U opens it.

It only ever talks to GitHub (api.github.com and raw.githubusercontent.com), only to read
Eddy's plugins page, and only changes Eddy's own ed3d_ plugin files.
"""

import os
import re
import json
import time
import hashlib
import threading
from tools.base import Tool

PLUGIN_NAME = "3D Check for Updates"
VERSION = "1.1"           # 1.1: old whole-number versions (15) count as renumbered (1.5); shown in the window title, so you can tell which file is loaded

GITHUB_OWNER = "eddy-99"
GITHUB_REPO = "eddys-3d-plugins-ingetrazo"
GITHUB_BRANCH = "main"
GITHUB_FOLDER = "plugins/3D_Eddys"
PAGE_URL = "https://github.com/%s/%s" % (GITHUB_OWNER, GITHUB_REPO)
LIST_URL = "https://api.github.com/repos/%s/%s/contents/%s?ref=%s" % (
    GITHUB_OWNER, GITHUB_REPO, GITHUB_FOLDER, GITHUB_BRANCH)
RAW_URL = "https://raw.githubusercontent.com/%s/%s/%s/%s/" % (
    GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH, GITHUB_FOLDER)

PRESETS_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets")
SETTINGS_FILE = os.path.join(PRESETS_DIR, "Check for Updates.json")
BACKUP_DIR = os.path.join(PRESETS_DIR, "Plugin backups")
PLUGIN_FOLDER = os.path.dirname(os.path.abspath(__file__))
CHECK_EVERY = 20 * 3600       # 'once a day' (a bit less, so the same time each day still counts)
TIMEOUT = 20


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def save_settings(d):
    try:
        os.makedirs(PRESETS_DIR, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)
    except Exception:
        pass


def auto_check_on():
    return bool(load_settings().get('auto', True))


# ---------------------------------------------------------------------------
# Versions and files (no Qt, so this can be checked on its own)
# ---------------------------------------------------------------------------
_VER_RE = re.compile(r'^\s*VERSION\s*=\s*["\']([^"\']+)["\']', re.M)
_NAME_RE = re.compile(r'^\s*PLUGIN_NAME\s*=\s*["\']([^"\']+)["\']', re.M)


def version_of(text):
    """The plugin's VERSION = "x.y" line, or '' if it hasn't got one."""
    m = _VER_RE.search(text or "")
    return m.group(1).strip() if m else ""


def name_of(text, stem=""):
    m = _NAME_RE.search(text or "")
    if m:
        return m.group(1).strip()
    nice = stem[5:] if stem.startswith("ed3d_") else stem
    return "3D " + nice.replace("_", " ").title()


def about_of(text):
    """The first line of what the plugin says about itself, after its name."""
    m = re.search(r'"""\s*\n?(.*?)\n', text or "", re.S)
    line = m.group(1).strip() if m else ""
    if " - " in line:
        line = line.split(" - ", 1)[1].strip()
    return line[:160]


def version_key(v):
    """'1.12' is newer than '1.9' (each part is a number: 1.9, 1.10, 1.11, 1.12...).
    Old-style whole numbers of 10 or more count the way they were renumbered: 15 = 1.5, 16 = 1.6."""
    t = str(v or "").strip()
    if re.fullmatch(r"\d{2,}", t):
        t = "%s.%s" % (t[:-1], t[-1])
    v = t
    parts = []
    for p in re.split(r"[.\s]+", str(v or "").strip()):
        m = re.match(r"\d+", p)
        parts.append(int(m.group(0)) if m else 0)
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


def blob_sha(data):
    """The fingerprint GitHub gives every file (so we can tell if two copies are the same)."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def local_sha(path):
    with open(path, "rb") as f:
        data = f.read()
    return blob_sha(data.replace(b"\r\n", b"\n"))      # Windows line endings count as the same


def stem_of(filename):
    """'ed3d_part_splitter .py.off' -> ('ed3d_part_splitter', switched_off=True)."""
    low = filename.lower()
    if not low.startswith("ed3d_"):
        return None, False
    i = low.find(".py")
    if i < 0:
        return None, False
    stem = filename[:i].strip()
    rest = low[i + 3:]
    return stem, rest != ""


def plugin_folders():
    """Where Eddy's plugins can be: this file's folder, IngeTrazo's plugins folder, and its 3D_Eddys folder."""
    here = PLUGIN_FOLDER
    root = os.path.dirname(here) if os.path.basename(os.path.dirname(here)).lower() == "plugins" else here
    out = []
    for d in (here, root, os.path.join(root, "3D_Eddys")):
        d = os.path.normpath(d)
        if os.path.isdir(d) and d not in out:
            out.append(d)
    return out


def local_plugins():
    """{stem: {'paths': [working .py files], 'off': [switched-off files]}}"""
    found = {}
    for d in plugin_folders():
        try:
            names = os.listdir(d)
        except Exception:
            continue
        for fn in names:
            p = os.path.join(d, fn)
            if not os.path.isfile(p):
                continue
            stem, off = stem_of(fn)
            if not stem:
                continue
            e = found.setdefault(stem, {'paths': [], 'off': []})
            if off:
                e['off'].append(p)
            elif fn.lower().endswith(".py"):
                e['paths'].append(p)
    return found


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------
def fetch(url, accept=None):
    import urllib.request
    req = urllib.request.Request(url, headers={
        'User-Agent': "%s/%s (IngeTrazo plugin)" % (PLUGIN_NAME.replace(" ", "-"), VERSION),
        'Accept': accept or "*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def github_list():
    """[{'name', 'sha', 'url'}] for every ed3d_*.py on Eddy's plugins page."""
    data = json.loads(fetch(LIST_URL, "application/vnd.github+json").decode("utf-8"))
    if not isinstance(data, list):
        raise RuntimeError("GitHub sent something unexpected")
    out = []
    for f in data:
        nm = str(f.get('name') or "")
        if f.get('type') == "file" and nm.lower().startswith("ed3d_") and nm.lower().endswith(".py"):
            out.append({'name': nm, 'sha': str(f.get('sha') or ""),
                        'url': str(f.get('download_url') or (RAW_URL + nm))})
    return out


def friendly_error(e):
    t = str(e)
    if "403" in t or "rate limit" in t.lower():
        return "GitHub is busy (too many checks from this internet connection). Try again in an hour."
    if "404" in t:
        return "The plugins page wasn't found on GitHub."
    if "CERTIFICATE" in t.upper() or "SSL" in t.upper():
        return "Couldn't make a safe connection to GitHub (%s)." % t
    return "Couldn't reach GitHub - are you online? (%s)" % t


def check(progress=None):
    """Compares the plugins here with GitHub. Returns a list of rows:
    {'stem', 'name', 'about', 'state', 'mine', 'theirs', 'paths', 'sha', 'url', 'data'}
    state: 'update' (newer on GitHub), 'new' (not got it), 'changed' (different, same version),
           'newer_here' (yours is newer), 'same' (up to date), 'off' (switched off here)."""
    remote = github_list()
    here = local_plugins()
    rows = []
    for i, f in enumerate(sorted(remote, key=lambda f: f['name'].lower())):
        if progress:
            progress(i, len(remote), f['name'])
        stem = f['name'][:-3]
        loc = here.get(stem) or {'paths': [], 'off': []}
        row = {'stem': stem, 'name': name_of("", stem), 'about': "", 'mine': "", 'theirs': "",
               'paths': list(loc['paths']), 'sha': f['sha'], 'url': f['url'], 'data': None}
        if not loc['paths'] and loc['off']:
            row['state'] = 'off'
            row['name'] = name_of(read_text(loc['off'][0]), stem)
            rows.append(row)
            continue
        if loc['paths']:
            mine_text = read_text(loc['paths'][0])
            row['name'] = name_of(mine_text, stem)
            row['mine'] = version_of(mine_text)
            try:
                same = all(local_sha(p) == f['sha'] for p in loc['paths'])
            except Exception:
                same = False
            if same:
                row['state'] = 'same'
                row['theirs'] = row['mine']
                rows.append(row)
                continue
        # different (or not here): fetch GitHub's copy to see its version
        data = fetch(f['url'])
        row['data'] = data
        text = data.decode("utf-8", errors="replace")
        row['theirs'] = version_of(text)
        row['name'] = name_of(text, stem)
        row['about'] = about_of(text)
        if not loc['paths']:
            row['state'] = 'new'
        else:
            a, b = version_key(row['theirs']), version_key(row['mine'])
            if row['theirs'] and row['mine'] and a > b:
                row['state'] = 'update'
            elif row['theirs'] and row['mine'] and a < b:
                row['state'] = 'newer_here'
            elif row['theirs'] and not row['mine']:
                row['state'] = 'update'          # GitHub's copy has a version number, yours hasn't
            else:
                row['state'] = 'changed'
        rows.append(row)
    return rows


def worth_telling(rows):
    """The rows the 'something new is ready' notice is about."""
    return [r for r in rows if r['state'] in ('update', 'new')]


def install(row):
    """Puts GitHub's copy in place. Keeps the old copy in the backups folder. Returns where it went."""
    data = row.get('data')
    if data is None:
        data = fetch(row['url'])
    if row.get('sha') and blob_sha(data) != row['sha']:
        raise RuntimeError("GitHub is still catching up with a change. Try again in a few minutes.")
    compile(data.decode("utf-8"), row['stem'] + ".py", "exec")      # not a broken download
    targets = list(row.get('paths') or []) or [os.path.join(PLUGIN_FOLDER, row['stem'] + ".py")]
    stamp = time.strftime("%Y-%m-%d %H%M")
    for t in targets:
        if os.path.isfile(t):
            os.makedirs(BACKUP_DIR, exist_ok=True)
            old_v = version_of(read_text(t)) or "old"
            with open(t, "rb") as f_old:
                old = f_old.read()
            bk = os.path.join(BACKUP_DIR, "%s %s (%s).py" % (row['stem'], old_v, stamp))
            with open(bk, "wb") as f_bk:
                f_bk.write(old)
        tmp = t + ".downloading"
        with open(tmp, "wb") as f_new:
            f_new.write(data)
        os.replace(tmp, t)
    return targets


STATE_TEXT = {
    'update': "Update ready",
    'new': "New plugin",
    'changed': "Different from GitHub (same version number)",
    'newer_here': "Yours is newer",
    'same': "Up to date",
    'off': "Switched off here",
}


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
    "Looks at Eddy's plugins page on GitHub and compares it with the plugins on this computer.<br><br>"
    "<b>Update ready</b> - there's a newer version of a plugin you have.<br>"
    "<b>New plugin</b> - one you haven't got yet.<br>"
    "<b>Different from GitHub</b> - your copy isn't the same as GitHub's but has the same version "
    "number (you may have changed it yourself). Left unticked.<br>"
    "<b>Yours is newer</b> - nothing to do.<br><br>"
    "Tick the ones you want and click <b>Update ticked</b>. Your old copy is kept in "
    "Documents\\IngeTrazo Presets\\Plugin backups, so you can always go back. "
    "<b>Restart IngeTrazo</b> to use the new versions.<br><br>"
    "With <b>Check when IngeTrazo starts</b> ticked it checks by itself (at most once a day) and "
    "only tells you when something new is ready.<br><br>"
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
            self.tree.setHeaderLabels(["Plugin", "Yours", "On GitHub", "What it is"])
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
            os.makedirs(BACKUP_DIR, exist_ok=True)
            open_url(BACKUP_DIR)

        # -- checking
        def busy(self, on, text=""):
            self.b_check.setEnabled(not on)
            self.b_update.setEnabled(not on and bool(self.ticked()))
            if text:
                self.status.setText(text)

        def start_check(self):
            if self.job is not None and not self.job.finished:
                return
            self.busy(True, "Looking at Eddy's plugins page on GitHub...")
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
                      ("Different from GitHub (same version number)", ('changed',), True, False),
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
                    if r['state'] in ('update', 'new', 'changed'):
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
                    "  %s: %s" % (r['name'], e if "catching up" in str(e) else friendly_error(e)) for r, e in failed)
            QMessageBox.information(self, PLUGIN_NAME, msg)
            for r in done:
                r['state'] = 'same'
                r['mine'] = r['theirs']
                r['data'] = None
            self.show_rows(self.rows)
            if done:
                self.status.setText("Restart IngeTrazo to use the new versions.")

    return UpdatesWindow(parent)


# ---------------------------------------------------------------------------
# Checking by itself when IngeTrazo starts
# ---------------------------------------------------------------------------
_STARTUP = {'job': None}


def _startup_check(tries=0):
    try:
        from PySide6.QtCore import QTimer
        win = _main_window()
        if win is None or not win.isVisible():
            if tries < 240:
                QTimer.singleShot(500, lambda: _startup_check(tries + 1))
            return
        s = load_settings()
        if not s.get('auto', True) or time.time() - float(s.get('last_check') or 0) < CHECK_EVERY:
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
    'Check now': "Looks at Eddy's plugins page on GitHub again.",
    'Update ticked': "Downloads the ticked plugins and puts them in your plugins folder. Your old "
                     "copies are kept in the Plugin backups folder. Restart IngeTrazo afterwards.",
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
