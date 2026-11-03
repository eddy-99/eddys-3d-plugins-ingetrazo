# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Notepad for IngeTrazo
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
3D Notepad - a jotting pad that stays on screen in IngeTrazo
A small note window that floats over IngeTrazo and saves itself as you type.
Keep several notes (one text file each), and use the converter along the bottom
to turn real sizes into model sizes (or model sizes back into real ones) at any
scale and add them to the note where your cursor is. Highlight text in colours to
pick out groups of notes.
Ctrl+Alt+J shows or hides it.
"""

import os
import json
from tools.base import Tool

PLUGIN_NAME = "3D Notepad"
NOTES_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Notes")
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_notepad.json")
FIRST_NOTE = "Scale notes"

MY_SCALE = 80.0          # the scale the notepad starts on (and the starter note uses)
SCALES = [("1:80", 80.0), ("OO 1:76.2", 76.2), ("HO 1:87", 87.1), ("N (UK) 1:148", 148.0), ("N 1:160", 160.0),
          ("TT 1:120", 120.0), ("O (UK) 1:43.5", 43.5), ("O (US) 1:48", 48.0), ("S 1:64", 64.0),
          ("G 1:22.5", 22.5), ("1:24", 24.0), ("1:12", 12.0), ("Z 1:220", 220.0),
          ("Custom", None)]

# real-world sizes (mm) for the first note
STARTER = [
    ("Brick length", 215.0), ("Brick width", 102.5), ("Brick height", 65.0),
    ("Brick + joint (one course)", 75.0),
    ("Half-brick wall", 102.5), ("One-brick wall (9 in)", 215.0), ("Cavity wall (11 in)", 275.0),
    ("Brick-and-a-half wall (13.5 in)", 327.5),
    ("Storey height", 2700.0), ("Door height (6 ft 8 in)", 2032.0), ("Door width (2 ft 8 in)", 813.0),
    ("Window sill height", 900.0), ("Sash window 3 ft wide", 914.0), ("Sash window 5 ft high", 1524.0),
    ("Platform height (3 ft)", 914.0), ("Standard gauge (4 ft 8.5 in)", 1435.0),
    ("Person (5 ft 9 in)", 1753.0), ("Soil pipe", 110.0), ("Downpipe", 68.0),
]


def note_line(label, real_mm, scale_name, scale):
    """One line of the table: label, real size, model size."""
    return "%-32s %9.1f mm  ->  %7.2f mm   (%s)" % (label[:32], real_mm, real_mm / scale, scale_name)


def starter_text(scale=MY_SCALE, label="1:80"):
    lines = ["SCALE NOTES - real size -> model size (%s)" % label, "=" * 70]
    lines += [note_line(n, v, label, scale) for n, v in STARTER]
    lines += ["", "Add your own below (or use the converter at the bottom of this window):", ""]
    return "\n".join(lines)


def _old_starter():
    """The starter note exactly as the first version wrote it (OO), so it can be updated."""
    lines = ["SCALE NOTES - real size -> model size (OO 1:76.2)", "=" * 70]
    lines += [note_line(n, v, "OO", 76.2) for n, v in STARTER]
    lines += ["", "Add your own below (or use the converter at the bottom of this window):", ""]
    return "\n".join(lines)


HIGHLIGHT_DIR = os.path.join(NOTES_DIR, "Highlights")
HIGHLIGHTS = [("Yellow", "#fff176"), ("Green", "#a5d6a7"), ("Blue", "#90caf9"),
              ("Pink", "#f48fb1"), ("Orange", "#ffcc80"), ("Purple", "#ce93d8")]


def load_settings():
    s = {'note': FIRST_NOTE, 'geometry': None, 'scale_name': "1:80", 'custom': MY_SCALE,
         'font': 10, 'visible': False, 'highlight': HIGHLIGHTS[0][1]}
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


def _safe(name):
    return "".join(c if c.isalnum() or c in " -_()." else "_" for c in name).strip() or "Note"


def note_path(name):
    return os.path.join(NOTES_DIR, _safe(name) + ".txt")


def list_notes():
    try:
        return sorted(fn[:-4] for fn in os.listdir(NOTES_DIR) if fn.lower().endswith(".txt"))
    except Exception:
        return []


def read_note(name):
    try:
        with open(note_path(name), "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def write_note(name, text):
    os.makedirs(NOTES_DIR, exist_ok=True)
    with open(note_path(name), "w", encoding="utf-8") as f:
        f.write(text)


# Highlights are kept beside the notes (in a Highlights folder), so the notes themselves
# stay plain text files you can open anywhere.
def highlight_path(name):
    return os.path.join(HIGHLIGHT_DIR, _safe(name) + ".json")


def read_highlights(name):
    try:
        with open(highlight_path(name), "r", encoding="utf-8") as f:
            d = json.load(f)
        return [(int(a), int(b), str(c)) for a, b, c in d.get('marks', [])]
    except Exception:
        return []


def write_highlights(name, marks):
    p = highlight_path(name)
    try:
        if not marks:
            if os.path.exists(p):
                os.remove(p)
            return
        os.makedirs(HIGHLIGHT_DIR, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump({'marks': [list(m) for m in marks]}, f)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# The notepad window
# ---------------------------------------------------------------------------
def make_window(parent):
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QComboBox,
                                   QPushButton, QLabel, QLineEdit, QDoubleSpinBox, QSpinBox,
                                   QInputDialog, QMessageBox, QToolButton, QMenu)
    from PySide6.QtGui import (QFontDatabase, QTextCursor, QTextCharFormat, QColor, QPixmap,
                               QIcon, QAction)
    from PySide6.QtCore import Qt, QTimer

    class NotepadWindow(QDialog):
        def __init__(self, parent):
            super().__init__(parent)
            self.setWindowTitle(PLUGIN_NAME)
            self.setModal(False)
            # floats over IngeTrazo and never gets lost behind it
            self.setWindowFlags(Qt.Tool | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
            self.st = load_settings()
            self.current = None
            self._loading = False
            lay = QVBoxLayout(self)

            top = QHBoxLayout()
            top.addWidget(QLabel("Note:"))
            self.cb_note = QComboBox()
            self.cb_note.setMinimumWidth(160)
            top.addWidget(self.cb_note, 1)
            b_new = QPushButton("New")
            b_ren = QPushButton("Rename")
            b_del = QPushButton("Delete")
            b_dir = QPushButton("Folder")
            for b in (b_new, b_ren, b_del, b_dir):
                top.addWidget(b)
            # highlighter: pick some text, then click to colour it
            self.b_hl = QToolButton()
            self.b_hl.setText("Highlight")
            self.b_hl.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            self.b_hl.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
            menu = QMenu(self.b_hl)
            for text, col in HIGHLIGHTS:
                act = QAction(self.swatch(col), text, menu)
                act.triggered.connect(lambda _=False, c=col: self.pick_highlight(c))
                menu.addAction(act)
            menu.addSeparator()
            act = QAction("Clear highlight", menu)
            act.triggered.connect(self.clear_highlight)
            menu.addAction(act)
            self.b_hl.setMenu(menu)
            self.hl_colour = self.st.get('highlight') or HIGHLIGHTS[0][1]
            self.b_hl.setIcon(self.swatch(self.hl_colour))
            top.addWidget(self.b_hl)
            top.addWidget(QLabel("Text size:"))
            self.sp_font = QSpinBox()
            self.sp_font.setRange(7, 24)
            self.sp_font.setValue(int(self.st.get('font', 10)))
            top.addWidget(self.sp_font)
            lay.addLayout(top)

            self.ed = QPlainTextEdit()
            self.ed.setLineWrapMode(QPlainTextEdit.NoWrap)
            self.ed.setPlaceholderText("Jot your notes here - they save themselves as you type.")
            lay.addWidget(self.ed, 1)

            # converter: real size -> model size, added to the note
            conv = QHBoxLayout()
            self.le_label = QLineEdit()
            self.le_label.setPlaceholderText("What is it? e.g. Real wall thickness")
            conv.addWidget(self.le_label, 2)
            # type in either box: the real size or the model size; the other one follows
            self.sp_real = QDoubleSpinBox()
            self.sp_real.setDecimals(1)
            self.sp_real.setRange(0.0, 1000000.0)
            self.sp_real.setSuffix(" mm real")
            self.sp_real.setValue(215.0)
            conv.addWidget(self.sp_real)
            self.cb_scale = QComboBox()
            for text, n in SCALES:
                self.cb_scale.addItem(text, n)
            names = [t for t, _ in SCALES]
            want = self.st.get('scale_name', "1:80")
            self.cb_scale.setCurrentIndex(names.index(want) if want in names else 0)
            conv.addWidget(self.cb_scale)
            self.sp_custom = QDoubleSpinBox()
            self.sp_custom.setDecimals(2)
            self.sp_custom.setRange(1.0, 10000.0)
            self.sp_custom.setPrefix("1:")
            self.sp_custom.setValue(float(self.st.get('custom', MY_SCALE) or MY_SCALE))
            self.sp_custom.setToolTip("Your own scale: pick 'Custom' in the list, then type it here.")
            conv.addWidget(self.sp_custom)
            self.sp_model = QDoubleSpinBox()
            self.sp_model.setDecimals(2)
            self.sp_model.setRange(0.0, 1000000.0)
            self.sp_model.setSuffix(" mm model")
            conv.addWidget(self.sp_model)
            self._typed_model = False          # which box was typed in last
            b_add = QPushButton("Add to note")
            conv.addWidget(b_add)
            lay.addLayout(conv)

            self.lbl_status = QLabel()
            self.lbl_status.setStyleSheet("color: #777;")
            lay.addWidget(self.lbl_status)

            # saving: a moment after you stop typing, and when the window closes
            self.timer = QTimer(self)
            self.timer.setSingleShot(True)
            self.timer.setInterval(800)
            self.timer.timeout.connect(self.save_now)
            self.ed.textChanged.connect(self.typed)
            self.cb_note.currentIndexChanged.connect(self.pick_note)
            b_new.clicked.connect(self.new_note)
            b_ren.clicked.connect(self.rename_note)
            b_del.clicked.connect(self.delete_note)
            b_dir.clicked.connect(self.open_folder)
            b_add.clicked.connect(self.add_line)
            self.b_hl.clicked.connect(self.highlight)
            self.ed.cursorPositionChanged.connect(self.tidy_typing_format)
            self.sp_real.valueChanged.connect(self.real_typed)
            self.sp_model.valueChanged.connect(self.model_typed)
            self.cb_scale.currentIndexChanged.connect(self.update_model)
            self.sp_custom.valueChanged.connect(self.update_model)
            self.sp_font.valueChanged.connect(self.set_font)

            self.set_font(self.sp_font.value())
            try:
                old = read_note(FIRST_NOTE)
                # first time, or still the untouched OO starter from the first version: make it 1:80
                if not list_notes() or old == _old_starter():
                    write_note(FIRST_NOTE, starter_text())
            except Exception:
                pass
            self.refresh_notes(self.st.get('note') or FIRST_NOTE)
            self.update_model()
            geo = self.st.get('geometry')
            if geo and len(geo) == 4:
                self.setGeometry(*geo)
            else:
                self.resize(640, 460)

        # ---- notes ----
        def refresh_notes(self, select=None):
            names = list_notes() or [FIRST_NOTE]
            self.cb_note.blockSignals(True)
            self.cb_note.clear()
            for n in names:
                self.cb_note.addItem(n)
            i = names.index(select) if select in names else 0
            self.cb_note.setCurrentIndex(i)
            self.cb_note.blockSignals(False)
            self.pick_note()

        def pick_note(self, *_):
            name = self.cb_note.currentText()
            if not name or name == self.current:
                return
            self.save_now()
            self.current = name
            self._loading = True
            self.ed.setPlainText(read_note(name) or "")
            self.apply_highlights(read_highlights(name))
            self._loading = False
            self.ed.moveCursor(QTextCursor.End)
            self.st['note'] = name
            save_settings(self.st)
            self.lbl_status.setText("Saved in: %s" % note_path(name))

        def typed(self):
            if not self._loading:
                self.lbl_status.setText("Typing ...")
                self.timer.start()

        def save_now(self):
            self.timer.stop()
            if self.current is None or self._loading:
                return
            try:
                write_note(self.current, self.ed.toPlainText())
                write_highlights(self.current, self.get_highlights())
                self.lbl_status.setText("Saved in: %s" % note_path(self.current))
            except Exception as e:
                self.lbl_status.setText("Could not save: %s" % e)

        def new_note(self):
            name, ok = QInputDialog.getText(self, PLUGIN_NAME, "Name for the new note:")
            name = _safe(name or "")
            if not ok or not name:
                return
            if name in list_notes():
                QMessageBox.information(self, PLUGIN_NAME, "There's already a note called '%s'." % name)
                return
            self.save_now()
            write_note(name, "")
            self.current = None
            self.refresh_notes(name)

        def rename_note(self):
            old = self.current
            if not old:
                return
            name, ok = QInputDialog.getText(self, PLUGIN_NAME, "New name for '%s':" % old, text=old)
            name = _safe(name or "")
            if not ok or not name or name == old:
                return
            if name in list_notes():
                QMessageBox.information(self, PLUGIN_NAME, "There's already a note called '%s'." % name)
                return
            self.save_now()
            try:
                os.replace(note_path(old), note_path(name))
                if os.path.exists(highlight_path(old)):
                    try:
                        os.replace(highlight_path(old), highlight_path(name))
                    except Exception:
                        pass
            except Exception as e:
                QMessageBox.warning(self, PLUGIN_NAME, "Could not rename it:\n%s" % e)
                return
            self.current = None
            self.refresh_notes(name)

        def delete_note(self):
            name = self.current
            if not name:
                return
            if QMessageBox.question(self, PLUGIN_NAME, "Delete the note '%s'?" % name) != QMessageBox.Yes:
                return
            self.timer.stop()
            try:
                os.remove(note_path(name))
            except Exception:
                pass
            write_highlights(name, [])
            self.current = None
            self.refresh_notes()

        def open_folder(self):
            try:
                os.makedirs(NOTES_DIR, exist_ok=True)
                from PySide6.QtGui import QDesktopServices
                from PySide6.QtCore import QUrl
                QDesktopServices.openUrl(QUrl.fromLocalFile(NOTES_DIR))
            except Exception as e:
                QMessageBox.information(self, PLUGIN_NAME, "Notes folder:\n%s\n\n(%s)" % (NOTES_DIR, e))

        # ---- converter ----
        def scale(self):
            """(the scale number, its short name) chosen at the bottom of the window."""
            n = self.cb_scale.currentData()
            if n is None:                      # Custom
                n = self.sp_custom.value()
                return n, "1:%g" % n
            text = self.cb_scale.currentText()
            return n, (text if text.startswith("1:") else text.split(" ")[0])

        def real_mm(self):
            """The real size in mm (worked out from the model size if that was typed in)."""
            if self._typed_model:
                return self.sp_model.value() * self.scale()[0]
            return self.sp_real.value()

        def real_typed(self, *_):
            self._typed_model = False
            self.update_model()

        def model_typed(self, *_):
            self._typed_model = True
            self.update_model()

        def update_model(self, *_):
            """Fills in the other box: the model size from the real one, or the other way."""
            custom = self.cb_scale.currentData() is None
            self.sp_custom.setVisible(custom)
            n, _ = self.scale()
            if self._typed_model:
                self.sp_real.blockSignals(True)
                self.sp_real.setValue(self.sp_model.value() * n)
                self.sp_real.blockSignals(False)
            else:
                self.sp_model.blockSignals(True)
                self.sp_model.setValue(self.sp_real.value() / n)
                self.sp_model.blockSignals(False)
            self.st['scale_name'] = self.cb_scale.currentText()
            self.st['custom'] = self.sp_custom.value()
            save_settings(self.st)

        def add_line(self):
            """Puts the line in the note where the cursor is (on a line of its own)."""
            label = self.le_label.text().strip() or "Size"
            n, name = self.scale()
            line = note_line(label, self.real_mm(), name, n)
            cur = self.ed.textCursor()
            cur.clearSelection()
            if cur.positionInBlock() > 0:
                # part way along a line: the new line goes after that line
                cur.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                line = "\n" + line
            elif cur.block().length() > 1:
                # at the start of a line with writing on it: the new line goes above it
                line = line + "\n"
            cur.insertText(line, QTextCharFormat())     # not highlighted
            self.ed.setTextCursor(cur)
            self.ed.setFocus()
            self.le_label.clear()
            self.save_now()

        # ---- highlighter ----
        @staticmethod
        def swatch(col):
            pm = QPixmap(14, 14)
            pm.fill(QColor(col))
            return QIcon(pm)

        def pick_highlight(self, col):
            self.hl_colour = col
            self.b_hl.setIcon(self.swatch(col))
            self.st['highlight'] = col
            save_settings(self.st)
            self.highlight()

        def highlight(self):
            cur = self.ed.textCursor()
            if not cur.hasSelection():
                self.lbl_status.setText("Select some text first, then click Highlight.")
                return
            f = QTextCharFormat()
            f.setBackground(QColor(self.hl_colour))
            f.setForeground(QColor("#000000"))           # readable on a dark theme too
            cur.mergeCharFormat(f)
            self.typed()

        def clear_highlight(self):
            cur = self.ed.textCursor()
            if not cur.hasSelection():
                self.lbl_status.setText("Select the highlighted text first, then Clear highlight.")
                return
            cur.setCharFormat(QTextCharFormat())
            self.typed()

        def tidy_typing_format(self):
            """Typing straight after a highlight isn't highlighted (only typing inside one)."""
            cur = self.ed.textCursor()
            if cur.hasSelection() or not self._has_bg(cur.charFormat()):
                return
            nxt = QTextCursor(cur)
            if cur.atBlockEnd() or not nxt.movePosition(QTextCursor.MoveOperation.NextCharacter) \
                    or not self._has_bg(nxt.charFormat()):
                self.ed.setCurrentCharFormat(QTextCharFormat())

        @staticmethod
        def _has_bg(fmt):
            return fmt.background().style() != Qt.BrushStyle.NoBrush

        def get_highlights(self):
            """[(start, length, colour)] for every highlighted run in the note."""
            marks = []
            b = self.ed.document().begin()
            while b.isValid():
                for r in b.textFormats():
                    br = r.format.background()
                    if br.style() != Qt.BrushStyle.NoBrush and r.length > 0:
                        col = br.color().name()
                        start = b.position() + r.start
                        if marks and marks[-1][2] == col and marks[-1][0] + marks[-1][1] == start:
                            marks[-1] = (marks[-1][0], marks[-1][1] + r.length, col)
                        else:
                            marks.append((start, r.length, col))
                b = b.next()
            return marks

        def apply_highlights(self, marks):
            end = max(0, self.ed.document().characterCount() - 1)
            for start, length, col in marks:
                a, z = min(start, end), min(start + length, end)
                if z <= a:
                    continue
                cur = QTextCursor(self.ed.document())
                cur.setPosition(a)
                cur.setPosition(z, QTextCursor.MoveMode.KeepAnchor)
                f = QTextCharFormat()
                f.setBackground(QColor(col))
                f.setForeground(QColor("#000000"))
                cur.mergeCharFormat(f)
            # undoing shouldn't take the saved highlights off
            self.ed.document().clearUndoRedoStacks()

        def set_font(self, size):
            f = QFontDatabase.systemFont(QFontDatabase.FixedFont)   # columns line up
            f.setPointSize(int(size))
            self.ed.setFont(f)
            self.st['font'] = int(size)
            save_settings(self.st)

        # ---- remember where it was ----
        def remember(self):
            g = self.geometry()
            self.st['geometry'] = [g.x(), g.y(), g.width(), g.height()]
            save_settings(self.st)

        def hideEvent(self, e):
            self.save_now()
            self.remember()
            self.st['visible'] = False
            save_settings(self.st)
            super().hideEvent(e)

        def showEvent(self, e):
            self.st['visible'] = True
            save_settings(self.st)
            super().showEvent(e)

        def closeEvent(self, e):
            self.save_now()
            self.remember()
            super().closeEvent(e)

    return NotepadWindow(parent)


def _main_window():
    from PySide6.QtWidgets import QApplication, QMainWindow
    app = QApplication.instance()
    if app is None:
        return None
    wins = [w for w in app.topLevelWidgets() if isinstance(w, QMainWindow)]
    shown = [w for w in wins if w.isVisible()]
    return (shown or wins or [None])[0]


# ---------------------------------------------------------------------------
# Tool: Ctrl+Alt+J shows or hides the notepad
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

EDDY_TIPS = {'@cb_note': "The note you're looking at. Pick another note to open it.",
 'New': 'Starts a new, empty note.',
 'Rename': 'Renames this note.',
 'Delete': 'Deletes this note.',
 'Folder': 'Opens the folder your notes are saved in (one text file each).',
 'Text size': 'How big the writing is.',
 '@ed': 'Jot your notes here - they save themselves as you type.',
 '@le_label': "What the size is, e.g. 'Real wall thickness'. It goes in the note with the "
              'size.',
 '@sp_real': 'A real, full-size measurement in mm. Type it here and the model size '
             'is worked out, or type the model size and this fills in.',
 '@cb_scale': 'The scale to turn it into.',
 '@sp_model': 'The model size in mm at that scale. Type it here and the real size '
              'is worked out, or type the real size and this fills in.',
 '@b_hl': 'Select some text, then click to highlight it, to show groups of notes. '
          'The arrow picks the colour, or clears a highlight.',
 'Add to note': 'Puts the real size and the model size in the note where your cursor is.'}
EDDY_TIPS_END = None


class NotepadTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+J"
    description = "A note pad that stays on screen and saves itself, with a real/model size converter and a highlighter."

    _window = None

    def on_activate(self, viewport):
        w = NotepadTool._window
        if w is not None:
            try:
                if w.isVisible():
                    w.hide()
                else:
                    eddy_window(w, PLUGIN_NAME, EDDY_TIPS, place=False)  # eddy-window
                    w.show()
                    w.raise_()
                    w.activateWindow()
                return
            except Exception:
                NotepadTool._window = None
        parent = None
        try:
            parent = viewport.window()
        except Exception:
            parent = _main_window()
        w = make_window(parent)
        NotepadTool._window = w
        eddy_window(w, PLUGIN_NAME, EDDY_TIPS, place=False)  # eddy-window
        w.show()
        w.raise_()

    def on_deactivate(self, viewport):
        pass


def run(viewport=None):
    """Console entry point: run() opens the notepad."""
    NotepadTool().on_activate(viewport)
