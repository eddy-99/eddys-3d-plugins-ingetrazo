# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Plugins Toolbar for IngeTrazo
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
3D Plugins Toolbar (version 3.5) - one-click icons for your IngeTrazo plugins
A toolbar along the top of the IngeTrazo window with a button for each of the
3D plugins (Print Scaler, Part Splitter, Brick & Block Studio, Loft, Gutters & Downpipes,
Soil & Waste Pipes, Scale Studio, Period Windows, Roof Tiles, Notepad). Click a button to start
that plugin. Right-click the toolbar to pick which buttons it shows, and whether
they have labels. Ctrl+Alt+B shows or hides the toolbar.

Workflow toolbars: a toolbar of steps to work through in order - say, making a building: floor
plan, bricks, windows, doors, frame, roof... Copy any buttons onto it (the same plugin can be on
it more than once, and on your other toolbars too), each step numbered with a note of your own.
The next step is lit up; each one gets a tick when you've done it; 'Start again' clears them.
'Open last' (at the end of each workflow toolbar) opens the model you last had open, in one click -
the top one in IngeTrazo's own File > Open Recent list.
Make one with Arrange toolbars (right-click any of the toolbars).

Simple view (the first button on the main toolbar): hides all of IngeTrazo's other toolbars so only
yours are left - fewer buttons to frighten a beginner. Click it again and they all come back. It
stays on next time you start IngeTrazo, and puts them back for a moment as IngeTrazo closes, so
IngeTrazo never saves them hidden.

What do you want to make? (the big button after Simple view): pick Make a building, Make a bridge
and so on, and a maroon-and-gold toolbar comes up with that job's steps across your plugins -
1 Floor plan, 2 Openings, 3 Frame... Click a step to open that plugin; 'Next' closes the plugin
you're in and opens the next one. Done steps get a tick and the next one is lit up. It remembers
where you'd got to when you restart IngeTrazo. 'Close' puts it away.

Step toolbar: open any plugin and a toolbar of its pages comes up - 1 Start here, 2 Shape, 3 Walls...
Click a step to go to that page, or 'Next' for the next one. The page you're on is lit up and the
ones you've been to get a tick. It goes away when you close the plugin. Turn it off or on by
right-clicking any of the 3D Plugins toolbars.
"""

import os
import json
import math

VERSION = "3.27"  # 3.27: Make... sorted into groups (Buildings, Railway & outside, Locos, wagons & parts, Printing), with new jobs - station building, goods/engine shed, timber building, tin shed, factory chimney, riveted part, boiler with a dome; 3.26: closing the empty Untitled tab no longer asks you to save it (answers Don't Save for you); 3.25: Realistic Wall video link; 3.24: the Start window closes the empty Untitled tab IngeTrazo starts with, once your model is open; 3.23: the Start window shows each model's own name (not its folder), and uses IngeTrazo's list of recent models (not a list of folders); 3.22: a Start window when IngeTrazo opens - open the last model, open another, or start a new one; 3.21: Make a building / bridge: walling is a choice - Bricks or Realistic wall; 3.20: Realistic Wall button; 3.19: Card Kit video link; 3.18: version number taken off the main toolbar; 3.17: Card Kit button (Scale & print), and Make a card kit in Make...; 3.16: How to install video in the Make... menu; 3.15: Scale Studio video link; 3.14: Layers & Colours video link; 3.13: Soil & Waste Pipes video link; 3.12: Gutters video link; 3.11: Bricks video link; 3.10: Check for Updates button; 3.9: Roof Tiles video link; 3.8: Chimneys video link; 3.7: Doors video link; 3.6: Windows video link; 2.1: 'Open last' button on the workflow toolbars; 2.2: Bridges & Arches button;
                  # 2.3: Simple view button - hides all the toolbars except yours;
                  # 2.4: Step toolbar - a numbered toolbar of a plugin's pages when you open it;
                  # 2.5: Simple view first on the toolbar; step toolbar also checks every half second
                  #      (it didn't come up on Floor Plan);
                  # 2.6: step toolbar made bigger and bolder in maroon and gold, Simple view at its
                  #      start, '&' in page names shows properly (Base & top);
                  # 2.7: step buttons made bigger for sure (size and font set on each button, not just
                  #      the style); version number shown on the toolbars;
                  # 2.8: 'What do you want to make?' - pick a building, a bridge... and a maroon-and-gold
                  #      toolbar takes you through the plugins for it, one step at a time;
                  # 2.9: step toolbars and buttons a size smaller (2.8 was a bit too big);
                  # 3.0: the job toolbar (Make a building...) is your normal plugin buttons in a row,
                  #      numbered; 'What do you want to make?' is a normal button ('Make...');
                  # 3.1: picking a job lights up step 1 (the one you're on), not step 2; a step gets
                  #      its tick when you move on from it;
                  # 3.2: roof step with a choice of covering - roof tiles or roof sheets - on the
                  #      building and the canopy (it remembers which you picked);
                  # 3.3: Simple view and Make... are in Arrange toolbars like the other buttons, so
                  #      they can be moved, put on another toolbar, or unticked;
                  # 3.4: video links - 'Watch: Getting started' in Make..., and a 'Watch the video'
                  #      button on the page bar of any plugin that has a video;
                  # 3.5: video links for Openings and Subframe
from tools.base import Tool

PLUGIN_NAME = "3D Plugins Toolbar"
TOOLBAR_NAME = "ThreeDPluginsToolbar"
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_plugins_toolbar.json")

# (name the plugin registers with, its shortcut, short label, icon)
PLUGINS = [
    ("3D Period Windows", "Ctrl+Alt+N", "Windows", "window"),
    ("3D Brick & Block Studio", "Ctrl+Shift+T", "Bricks", "brick"),
    ("3D Gutters & Downpipes", "Ctrl+Alt+G", "Gutters", "gutter"),
    ("3D Soil & Waste Pipes", "Ctrl+Alt+W", "Soil pipes", "soil"),
    ("3D Loft", "Ctrl+Alt+L", "Loft", "loft"),
    ("3D Print Scaler", "Ctrl+Alt+P", "Scaler", "scaler"),
    ("3D Part Splitter", "Ctrl+Alt+Z", "Splitter", "splitter"),
    ("3D Scale Studio", "Ctrl+Alt+K", "Scale studio", "ruler"),
    ("3D Roof Tiles", "Ctrl+Alt+R", "Roof", "roof"),
    ("3D Notepad", "Ctrl+Alt+J", "Notes", "note"),
    ("3D Quick Links", "Ctrl+Alt+A", "Links", "links"),
    ("3D Wood Planking", "Ctrl+Alt+O", "Planks", "planks"),
    ("3D Period Doors", "Ctrl+Alt+D", "Doors", "door"),
    ("3D Fences & Gates", "Ctrl+Alt+F", "Fences", "fence"),
    ("3D Wrap", "Ctrl+Alt+U", "Wrap", "wrap"),
    ("3D Chimneys", "Ctrl+Alt+H", "Chimneys", "chimney"),
    ("3D Corrugated Iron", "Ctrl+Alt+I", "Tin sheet", "corrugated"),
    ("3D Station Canopies", "Ctrl+Alt+C", "Canopy", "canopy"),
    ("3D Centre Finder", "Ctrl+Alt+M", "Centre", "centre"),
    ("3D Timeline", "Ctrl+Alt+T", "Timeline", "timeline"),
    ("3D Find & Replace", "Ctrl+Alt+X", "Swap parts", "swap"),
    ("3D Place Along Line", "Ctrl+Alt+S", "Along line", "along"),
    ("3D Layers & Colours", "Ctrl+Alt+V", "Layers", "layers"),
    ("3D Pieces In", "Ctrl+Alt+E", "Pieces in", "piecesin"),
    ("3D Blend", "Ctrl+Shift+B", "Blend", "blend"),
    ("3D Subframe", "Ctrl+Alt+Y", "Subframe", "subframe"),
    ("3D Floor Plan", "Ctrl+Alt+Shift+F", "Floor plan", "floorplan"),
    ("3D Openings", "Ctrl+Shift+O", "Openings", "openings"),
    ("3D Show / Hide", "Ctrl+Alt+Shift+H", "Show/hide", "eye"),
    ("3D Bridges & Arches", "Ctrl+Alt+Shift+B", "Bridges", "bridge"),
    ("3D Check for Updates", "Ctrl+Alt+Shift+U", "Updates", "update"),
    ("3D Card Kit", "Ctrl+Alt+Shift+K", "Card kit", "cardkit"),
    ("3D Realistic Wall", "Ctrl+Shift+W", "Stone face", "realwall"),
]


# buttons that aren't plugins, but can be moved about in Arrange toolbars like the rest
SIMPLE_ITEM = "Simple view (hide IngeTrazo's other toolbars)"
MAKE_ITEM = "Make... (what do you want to make?)"
SPECIAL = {SIMPLE_ITEM: "simple", MAKE_ITEM: "make"}


def item_icon(entry):
    if entry in SPECIAL:
        return make_icon(SPECIAL[entry])
    p = next((p for p in PLUGINS if p[0] == entry), None)
    return make_icon(p[3]) if p else make_icon("note")


# plugins that have been renamed: (old name, new name), so saved button layouts still fit
RENAMED = {"3D Scale Converter": "3D Scale Studio"}


def load_settings():
    s = {'visible': True, 'hidden': [], 'labels': True}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            s.update(json.load(f))
    except Exception:
        pass
    for k in ('layout', 'hidden'):
        if isinstance(s.get(k), list):
            s[k] = [RENAMED.get(x, x) for x in s[k]]
    return s


def save_settings(s):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Icons, drawn here so nothing extra has to be installed
# ---------------------------------------------------------------------------
def make_icon(kind):
    from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QIcon, QPainterPath, QPolygonF
    from PySide6.QtCore import Qt, QRectF, QPointF
    S = 32
    pm = QPixmap(S, S)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    dark = QPen(QColor(50, 50, 50), 1.4)

    if kind == "window":
        p.setPen(dark)
        p.setBrush(QColor(245, 245, 240))
        path = QPainterPath()
        path.moveTo(7, 29)
        path.lineTo(7, 12)
        path.arcTo(QRectF(7, 3, 18, 18), 180, -180)
        path.lineTo(25, 29)
        path.closeSubpath()
        p.drawPath(path)
        p.setBrush(QColor(170, 210, 235))
        inner = QPainterPath()
        inner.moveTo(10, 26)
        inner.lineTo(10, 12)
        inner.arcTo(QRectF(10, 6, 12, 12), 180, -180)
        inner.lineTo(22, 26)
        inner.closeSubpath()
        p.drawPath(inner)
        p.drawLine(QPointF(16, 6), QPointF(16, 26))
        p.drawLine(QPointF(10, 17), QPointF(22, 17))
        p.setBrush(QColor(200, 195, 180))
        p.drawRect(QRectF(5, 27, 22, 3))
    elif kind == "brick":
        p.setPen(QPen(QColor(235, 225, 210), 1.2))
        p.setBrush(QColor(170, 80, 55))
        for r in range(4):
            y = 4 + r * 6.5
            off = 0 if r % 2 == 0 else -6
            for c in range(4):
                p.drawRect(QRectF(2 + off + c * 12, y, 11, 5.5))
    elif kind == "gutter":
        p.setPen(dark)
        p.setBrush(QColor(90, 95, 100))
        g = QPainterPath()
        g.moveTo(2, 6)
        g.lineTo(30, 6)
        g.arcTo(QRectF(2, 0, 28, 14), 0, -180)
        g.closeSubpath()
        p.drawPath(g)
        p.drawRect(QRectF(20, 12, 5, 14))
        p.drawRect(QRectF(16, 25, 10, 4))
    elif kind == "soil":
        p.setPen(dark)
        p.setBrush(QColor(80, 85, 90))
        p.drawRect(QRectF(12, 2, 8, 20))
        p.drawRect(QRectF(10, 2, 12, 4))
        b = QPainterPath()
        b.moveTo(12, 21)
        b.lineTo(20, 21)
        b.quadTo(20, 26, 26, 26)
        b.lineTo(30, 26)
        b.lineTo(30, 30)
        b.lineTo(26, 30)
        b.quadTo(12, 30, 12, 21)
        p.drawPath(b)
        p.setBrush(QColor(140, 145, 150))
        p.drawRect(QRectF(4, 12, 8, 5))
    elif kind == "loft":
        p.setPen(dark)
        p.setBrush(QColor(120, 160, 200))
        l = QPainterPath()
        l.moveTo(4, 28)
        l.lineTo(28, 28)
        l.lineTo(21, 6)
        l.lineTo(11, 6)
        l.closeSubpath()
        p.drawPath(l)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(30, 60, 120), 1.6))
        p.drawEllipse(QRectF(10, 3, 12, 6))
        p.drawRect(QRectF(4, 25, 24, 5))
    elif kind == "subframe":
        # a wall frame: plates, posts, a stud and a brace, round a window
        p.setPen(QPen(QColor(80, 50, 25), 1.0))
        p.setBrush(QColor(150, 104, 64))
        p.drawRect(QRectF(3, 26, 26, 3))                            # bottom plate
        p.drawRect(QRectF(3, 4, 26, 3))                             # top plate
        p.setBrush(QColor(120, 82, 50))
        p.drawRect(QRectF(3, 7, 3, 19))                             # end posts
        p.drawRect(QRectF(26, 7, 3, 19))
        p.setBrush(QColor(215, 150, 50))
        p.drawRect(QRectF(15, 11, 9, 2.5))                          # lintel and sill
        p.drawRect(QRectF(15, 20, 9, 2.5))
        p.setBrush(QColor(200, 120, 40))
        p.drawRect(QRectF(13, 7, 2.5, 19))                          # post by the window
        p.setPen(QPen(QColor(90, 120, 70), 2.4))
        p.drawLine(QPointF(7, 25), QPointF(12, 8))                  # brace
    elif kind == "floorplan":
        # a plan from above: an L of walls, an inside wall, the floor showing through
        p.setPen(QPen(QColor(110, 60, 40), 1.0))
        p.setBrush(QColor(196, 120, 90))
        o = QPainterPath()
        for x, y in ((3, 29), (29, 29), (29, 15), (17, 15), (17, 3), (3, 3)):
            (o.moveTo if o.elementCount() == 0 else o.lineTo)(x, y)
        o.closeSubpath()
        i = QPainterPath()
        for x, y in ((7, 25), (25, 25), (25, 19), (13, 19), (13, 7), (7, 7)):
            (i.moveTo if i.elementCount() == 0 else i.lineTo)(x, y)
        i.closeSubpath()
        p.drawPath(o.subtracted(i))
        p.setBrush(QColor(240, 225, 195))
        p.drawPath(i)
        p.setBrush(QColor(225, 170, 120))
        p.drawRect(QRectF(7, 13, 6, 2))                            # an inside wall
    elif kind == "openings":
        # a wall with a window hole and a doorway cut up from the bottom
        p.setPen(QPen(QColor(110, 60, 40), 1.0))
        p.setBrush(QColor(196, 120, 90))
        w_ = QPainterPath()
        for x, y in ((3, 29), (17, 29), (17, 15), (25, 15), (25, 29), (29, 29), (29, 5), (3, 5)):
            (w_.moveTo if w_.elementCount() == 0 else w_.lineTo)(x, y)
        w_.closeSubpath()
        h_ = QPainterPath()
        h_.addRect(QRectF(6, 10, 7, 9))
        p.drawPath(w_.subtracted(h_))
        p.setBrush(QColor(190, 215, 235))                           # sky through the window
        p.drawRect(QRectF(6, 10, 7, 9))
    elif kind == "blend":
        # a post standing on a block, a curved fillet blending one into the other
        p.setPen(dark)
        p.setBrush(QColor(200, 205, 212))
        p.drawRect(QRectF(3, 22, 26, 7))                            # the base
        p.setBrush(QColor(235, 120, 30))
        f = QPainterPath()
        f.moveTo(6, 22)
        f.quadTo(12, 22, 12, 15)
        f.lineTo(20, 15)
        f.quadTo(20, 22, 26, 22)
        f.closeSubpath()
        p.drawPath(f)                                               # the blend
        p.setBrush(QColor(60, 140, 220))
        p.drawRect(QRectF(12, 3, 8, 19))                            # the post
    elif kind == "scaler":
        p.setPen(dark)
        p.setBrush(QColor(225, 120, 40))
        p.drawRect(QRectF(5, 14, 14, 14))
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(225, 120, 40), 1.4, Qt.DashLine))
        p.drawRect(QRectF(5, 4, 24, 24))
        p.setPen(QPen(QColor(50, 50, 50), 2.0))
        p.drawLine(QPointF(17, 16), QPointF(26, 7))
        p.drawLine(QPointF(26, 7), QPointF(21, 7))
        p.drawLine(QPointF(26, 7), QPointF(26, 12))
    elif kind == "ruler":
        p.setPen(dark)
        p.setBrush(QColor(240, 205, 90))
        p.drawRect(QRectF(2, 10, 28, 12))
        for i in range(1, 9):
            x = 2 + i * 3.1
            h = 6 if i % 2 == 0 else 3.5
            p.drawLine(QPointF(x, 10), QPointF(x, 10 + h))
    elif kind == "roof":
        p.setPen(QPen(QColor(90, 40, 25), 1.0))
        p.setBrush(QColor(176, 84, 56))
        for r in range(4):
            y = 22 - r * 5.5
            inset = r * 3.0
            off = 0 if r % 2 == 0 else 3.0
            x = 3 + inset + off
            while x < 29 - inset - 0.5:
                w = min(6.0, 29 - inset - x)
                p.drawRect(QRectF(x, y, w, 5.0))
                x += 6.0
        p.setPen(QPen(QColor(60, 60, 60), 1.6))
        p.drawLine(QPointF(2, 28), QPointF(30, 28))
    elif kind == "wrap":
        p.setPen(QPen(QColor(90, 40, 25), 1.0))
        p.setBrush(QColor(176, 84, 56))
        for r in range(5):
            y = 26 - r * 5.0
            w0 = 10.0 - r * 1.0
            for k in range(-2, 2):
                x = 16 + k * w0 + (w0 / 2 if r % 2 else 0)
                if 16 - 2 * w0 <= x <= 16 + w0:
                    p.drawRect(QRectF(x, y, w0 - 0.8, 4.2))
    elif kind == "corrugated":
        path = QPainterPath()
        for row, y0 in enumerate((6.0, 18.0)):
            p.setPen(QPen(QColor(70, 76, 82), 1.0))
            p.setBrush(QColor(150, 158, 164) if row == 0 else QColor(168, 112, 74))
            pts = [QPointF(3 + i * 0.5, y0 + 1.6 * math.sin(i * 0.5 * 2 * math.pi / 5.0)) for i in range(53)]
            pts += [QPointF(29, y0 + 10), QPointF(3, y0 + 10)]
            p.drawPolygon(QPolygonF(pts))
            p.setPen(QPen(QColor(90, 96, 100), 0.7))
            for k in range(6):
                x = 5.5 + k * 5.0
                p.drawLine(QPointF(x, y0 + 2), QPointF(x, y0 + 10))
    elif kind == "canopy":
        p.setPen(QPen(QColor(50, 50, 60), 1.0))
        p.setBrush(QColor(110, 112, 124))
        p.drawPolygon(QPolygonF([QPointF(2, 5), QPointF(30, 10), QPointF(30, 13), QPointF(2, 8)]))   # the roof
        p.setBrush(QColor(214, 200, 160))
        p.setPen(QPen(QColor(130, 110, 70), 0.8))
        pts = [QPointF(4, 13), QPointF(30, 13)]
        x = 30.0
        while x > 4.5:
            pts.append(QPointF(x, 16.5))
            pts.append(QPointF(x - 1.6, 19.5))
            pts.append(QPointF(x - 3.2, 16.5))
            x -= 3.2
        p.drawPolygon(QPolygonF(pts))                                                         # the valance
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(50, 80, 65))
        for cx in (9.0, 23.0):
            p.drawRect(QRectF(cx - 1.2, 16, 2.4, 13))
            p.drawRect(QRectF(cx - 2.2, 27, 4.4, 3))
            p.drawPolygon(QPolygonF([QPointF(cx - 4, 16), QPointF(cx + 4, 16), QPointF(cx + 1.2, 19),
                                     QPointF(cx - 1.2, 19)]))
    elif kind == "chimney":
        p.setPen(QPen(QColor(60, 60, 60), 1.4))
        p.drawLine(QPointF(1, 30), QPointF(31, 18))          # the roof slope
        p.setPen(QPen(QColor(90, 40, 25), 1.0))
        p.setBrush(QColor(176, 84, 56))
        p.drawPolygon(QPolygonF([QPointF(9, 27), QPointF(9, 11), QPointF(23, 11), QPointF(23, 21.7)]))
        p.drawRect(QRectF(7.5, 8.5, 17, 3))                     # oversailing course
        p.setBrush(QColor(200, 110, 60))
        p.drawRect(QRectF(10.5, 2.5, 4, 6))                     # the pots
        p.drawRect(QRectF(17.5, 2.5, 4, 6))
        p.setPen(QPen(QColor(120, 50, 30), 0.8))
        for y in (14, 17, 20, 23):
            p.drawLine(QPointF(9, y), QPointF(23, y))
    elif kind == "fence":
        p.setPen(QPen(QColor(80, 50, 25), 1.0))
        p.setBrush(QColor(150, 104, 64))
        p.drawRect(QRectF(2, 13, 28, 3.5))
        p.drawRect(QRectF(2, 22, 28, 3.5))
        for i in range(5):
            x = 3.5 + i * 5.6
            p.drawPolygon(QPolygonF([QPointF(x, 29), QPointF(x + 3.6, 29), QPointF(x + 3.6, 9),
                                     QPointF(x + 1.8, 5.5), QPointF(x, 9)]))
    elif kind == "door":
        p.setPen(QPen(QColor(220, 218, 210), 1.0))
        p.setBrush(QColor(236, 234, 226))
        p.drawRect(QRectF(7, 2, 18, 28))
        p.setPen(QPen(QColor(25, 55, 40), 1.0))
        p.setBrush(QColor(52, 96, 72))
        p.drawRect(QRectF(9.5, 4.5, 13, 25.5))
        p.setBrush(QColor(40, 78, 58))
        for y in (7, 17):
            p.drawRect(QRectF(11.5, y, 3.8, 8))
            p.drawRect(QRectF(16.7, y, 3.8, 8))
        p.setPen(QPen(QColor(30, 30, 30), 2.0))
        p.drawPoint(QPointF(20.5, 16.5))
    elif kind == "planks":
        p.setPen(QPen(QColor(80, 50, 25), 1.0))
        for i, w in enumerate((5.5, 6.5, 5.0, 6.0)):
            x = 3 + sum((5.5, 6.5, 5.0, 6.0)[:i]) + i * 0.8
            p.setBrush(QColor(150 + 12 * (i % 2), 104 + 8 * (i % 2), 64))
            p.drawRect(QRectF(x, 4, w, 24))
        p.setPen(QPen(QColor(60, 40, 20), 1.6))
        p.drawPoint(QPointF(7, 10))
        p.drawPoint(QPointF(19, 22))
    elif kind == "centre":
        p.setPen(dark)
        p.setBrush(QColor(225, 232, 240))
        p.drawRect(QRectF(4, 6, 24, 20))                       # a face
        p.setPen(QPen(QColor(70, 120, 200), 1.0, Qt.DashLine))
        p.drawLine(QPointF(4, 16), QPointF(28, 16))           # centre lines
        p.drawLine(QPointF(16, 6), QPointF(16, 26))
        p.setPen(QPen(QColor(200, 50, 40), 1.6))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(16, 16), 4.5, 4.5)              # the centre mark
        p.drawLine(QPointF(16, 9.5), QPointF(16, 22.5))
        p.drawLine(QPointF(9.5, 16), QPointF(22.5, 16))
    elif kind == "timeline":
        p.setPen(dark)
        p.setBrush(QColor(235, 238, 242))
        p.drawRoundedRect(QRectF(2, 9, 28, 14), 3, 3)          # the strip
        for i, col in enumerate(((60, 120, 210), (230, 140, 30), (50, 150, 80), (190, 190, 190))):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(*col))
            p.drawRoundedRect(QRectF(4 + i * 6.5, 12, 5, 8), 1.5, 1.5)  # the steps
        p.setPen(QPen(QColor(210, 40, 40), 2.0))
        p.drawLine(QPointF(23.5, 6), QPointF(23.5, 26))          # where the model is now
    elif kind == "note":
        p.setPen(dark)
        p.setBrush(QColor(255, 244, 160))
        p.drawRect(QRectF(6, 4, 20, 25))
        p.setPen(QPen(QColor(120, 150, 200), 1.0))
        for i in range(5):
            y = 10 + i * 4
            p.drawLine(QPointF(9, y), QPointF(23, y))
        p.setPen(QPen(QColor(200, 60, 50), 2.2))
        p.drawLine(QPointF(19, 22), QPointF(29, 12))
        p.setPen(QPen(QColor(50, 50, 50), 1.0))
        p.drawLine(QPointF(17, 25), QPointF(19, 22))
    elif kind == "links":
        p.setPen(dark)
        p.setBrush(QColor(240, 200, 90))
        tab = QPainterPath()                                   # a folder
        tab.moveTo(3, 9)
        tab.lineTo(3, 6)
        tab.lineTo(12, 6)
        tab.lineTo(14, 9)
        tab.closeSubpath()
        p.drawPath(tab)
        p.drawRect(QRectF(3, 9, 26, 18))
        p.setPen(QPen(QColor(40, 90, 160), 2.2))               # a chain link on it
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(8, 15, 10, 6), 3, 3)
        p.drawRoundedRect(QRectF(14, 15, 10, 6), 3, 3)
    elif kind == "swap":
        import math as _m
        p.setPen(dark)
        p.setBrush(QColor(200, 205, 212))                      # a flat hex marker
        hexp = QPolygonF([QPointF(9 + 6 * _m.cos(_m.radians(a)), 10 + 6 * _m.sin(_m.radians(a)))
                          for a in range(0, 360, 60)])
        p.drawPolygon(hexp)
        grad_c = QColor(150, 110, 70)                          # becomes a domed rivet
        p.setBrush(grad_c)
        p.drawEllipse(QRectF(17, 16, 12, 12))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(235, 215, 185))
        p.drawEllipse(QRectF(20, 18.5, 4, 3))                  # its shine
        p.setPen(QPen(QColor(40, 120, 70), 2.0))               # the swap arrows
        p.setBrush(Qt.NoBrush)
        p.drawLine(QPointF(14, 6), QPointF(24, 6))
        p.drawLine(QPointF(24, 6), QPointF(24, 12))
        p.drawLine(QPointF(21, 9.5), QPointF(24, 12.5))
        p.drawLine(QPointF(27, 9.5), QPointF(24, 12.5))
        p.drawLine(QPointF(15, 26), QPointF(6, 26))
        p.drawLine(QPointF(6, 26), QPointF(6, 19))
        p.drawLine(QPointF(3, 22), QPointF(6, 18.5))
        p.drawLine(QPointF(9, 22), QPointF(6, 18.5))
    elif kind == "along":
        p.setPen(dark)
        p.setBrush(QColor(200, 205, 212))
        p.drawChord(QRectF(3, 9, 26, 40), 0, 180 * 16)            # a boiler's curve
        p.setPen(QPen(QColor(235, 120, 30), 1.4, Qt.DashLine))
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(5.5, 11.5, 21, 35), 15 * 16, 150 * 16)     # the line over it
        p.setPen(QPen(QColor(90, 60, 30), 0.8))
        p.setBrush(QColor(150, 110, 70))
        import math as _m
        for a in (25, 57, 90, 123, 155):                            # rivets along it
            r = _m.radians(a)
            p.drawEllipse(QPointF(16 + 10.5 * _m.cos(r), 29 - 17.5 * _m.sin(r)), 2.2, 2.2)
    elif kind == "splitter":
        # a block cut in two, the halves pulled apart, the cut line between them
        p.setPen(dark)
        p.setBrush(QColor(225, 120, 40))
        p.drawRect(QRectF(3, 9, 10, 18))
        p.setBrush(QColor(60, 140, 220))
        p.drawRect(QRectF(19, 5, 10, 18))
        p.setPen(QPen(QColor(200, 30, 30), 1.6, Qt.DashLine))
        p.drawLine(QPointF(16, 2), QPointF(16, 30))
    elif kind == "piecesin":
        # coloured pieces dropping into a tray, an arrow bringing them in
        p.setPen(dark)
        p.setBrush(QColor(200, 205, 212))
        p.drawRect(QRectF(3, 22, 26, 7))                            # the tray
        p.setBrush(QColor(230, 90, 70))
        p.drawRect(QRectF(5, 15, 8, 7))
        p.setBrush(QColor(60, 140, 220))
        p.drawRect(QRectF(13, 15, 7, 7))
        p.setBrush(QColor(90, 180, 80))
        p.drawRect(QRectF(20, 12, 7, 10))
        p.setPen(QPen(QColor(235, 120, 30), 2.2))
        p.drawLine(QPointF(16, 2), QPointF(16, 10))                 # the arrow coming in
        p.setBrush(QColor(235, 120, 30))
        p.drawPolygon(QPolygonF([QPointF(11.5, 8), QPointF(20.5, 8), QPointF(16, 13)]))
    elif kind == "again":
        # a round arrow: start the workflow again
        p.setPen(QPen(QColor(46, 125, 50), 3.0))
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(6, 6, 20, 20), 60 * 16, 290 * 16)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(46, 125, 50))
        p.drawPolygon(QPolygonF([QPointF(17, 1), QPointF(26, 6), QPointF(17, 12)]))
    elif kind == "openlast":
        # an open folder with a green arrow: open the model you had last
        p.setPen(dark)
        p.setBrush(QColor(222, 178, 82))
        p.drawPolygon(QPolygonF([QPointF(3, 8), QPointF(12, 8), QPointF(14, 11), QPointF(25, 11),
                                 QPointF(25, 27), QPointF(3, 27)]))
        p.setBrush(QColor(245, 205, 110))
        p.drawPolygon(QPolygonF([QPointF(3, 27), QPointF(8, 15), QPointF(30, 15), QPointF(25, 27)]))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(46, 125, 50))
        p.drawPolygon(QPolygonF([QPointF(19, 1), QPointF(28, 6), QPointF(19, 11)]))
        p.setPen(QPen(QColor(46, 125, 50), 3.0))
        p.drawLine(QPointF(12, 6), QPointF(20, 6))
    elif kind == "layers":
        p.setPen(dark)
        for i, col in enumerate(((168, 80, 56), (84, 90, 102), (46, 92, 68))):   # brick, slate, ironwork
            y = 18 - i * 6
            p.setBrush(QColor(*col))
            p.drawPolygon(QPolygonF([QPointF(4, y + 4), QPointF(16, y - 2), QPointF(28, y + 4),
                                     QPointF(16, y + 10)]))
    elif kind == "simple":
        # Simple view: a toolbar with one bright button and the rest faded away
        p.setPen(QPen(QColor(90, 90, 90), 1.4))
        p.setBrush(QColor(240, 240, 235))
        p.drawRoundedRect(QRectF(2, 9, 28, 14), 3, 3)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(200, 200, 200, 150))
        for x in (5.0, 10.5, 21.5):
            p.drawRect(QRectF(x, 13, 4, 6))
        p.setBrush(QColor(128, 24, 40))                      # maroon, like the works plate
        p.drawRoundedRect(QRectF(15, 11, 6.5, 10), 1.5, 1.5)
        p.setBrush(QColor(212, 168, 60))                     # gold dot
        p.drawEllipse(QRectF(16.6, 14.4, 3.4, 3.4))
    elif kind == "make":
        # what do you want to make: a little house with a gold star
        p.setPen(dark)
        p.setBrush(QColor(196, 98, 70))
        p.drawRect(QRectF(6, 15, 16, 13))
        p.setBrush(QColor(128, 24, 40))
        p.drawPolygon(QPolygonF([QPointF(3, 16), QPointF(14, 6), QPointF(25, 16)]))
        p.setBrush(QColor(170, 210, 235))
        p.drawRect(QRectF(9, 18, 4, 4))
        p.setBrush(QColor(90, 60, 40))
        p.drawRect(QRectF(15, 20, 4, 8))
        p.setBrush(QColor(240, 200, 90))
        star = QPolygonF()
        for i in range(10):
            r = 6.5 if i % 2 == 0 else 2.8
            a = math.pi / 2 + i * math.pi / 5
            star.append(QPointF(25 + r * math.cos(a), 8 - r * math.sin(a)))
        p.drawPolygon(star)
    elif kind == "close":
        p.setPen(QPen(QColor(150, 40, 40), 3.0))
        p.drawLine(QPointF(9, 9), QPointF(23, 23))
        p.drawLine(QPointF(23, 9), QPointF(9, 23))
    elif kind == "next":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(46, 125, 50))
        p.drawPolygon(QPolygonF([QPointF(6, 12), QPointF(17, 12), QPointF(17, 5), QPointF(28, 16),
                                 QPointF(17, 27), QPointF(17, 20), QPointF(6, 20)]))
    elif kind == "eye":
        # an eye: show / hide
        p.setPen(QPen(QColor(50, 50, 50), 1.6))
        p.setBrush(QColor(250, 250, 245))
        eye = QPainterPath()
        eye.moveTo(3, 16)
        eye.quadTo(16, 3, 29, 16)
        eye.quadTo(16, 29, 3, 16)
        eye.closeSubpath()
        p.drawPath(eye)
        p.setBrush(QColor(70, 120, 170))
        p.drawEllipse(QRectF(10.5, 10.5, 11, 11))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(30, 30, 30))
        p.drawEllipse(QRectF(13.5, 13.5, 5, 5))
    elif kind == "bridge":
        # a little viaduct: deck, two arches and their piers
        p.setPen(QPen(QColor(110, 70, 50), 1.0))
        p.setBrush(QColor(196, 120, 86))
        path = QPainterPath()
        path.moveTo(2, 28)
        path.lineTo(2, 10)
        path.lineTo(30, 10)
        path.lineTo(30, 28)
        path.lineTo(26, 28)
        path.lineTo(26, 21)
        path.arcTo(QRectF(18, 15, 8, 12), 0, 180)
        path.lineTo(18, 28)
        path.lineTo(14, 28)
        path.lineTo(14, 21)
        path.arcTo(QRectF(6, 15, 8, 12), 0, 180)
        path.lineTo(6, 28)
        path.closeSubpath()
        p.drawPath(path)
        p.setBrush(QColor(225, 214, 192))
        p.drawRect(QRectF(1, 6, 30, 4))                       # the parapet and coping
        p.setPen(QPen(QColor(240, 225, 200), 1.0))
        for x0 in (6.0, 18.0):
            ring = QPainterPath()
            ring.arcMoveTo(QRectF(x0 - 1.5, 13.5, 11, 15), 180)
            ring.arcTo(QRectF(x0 - 1.5, 13.5, 11, 15), 180, -180)
            p.drawPath(ring)
    elif kind == "cardkit":
        # a sheet of paper with a little printed house on it: its glue tab and a dashed fold
        p.setPen(dark)
        p.setBrush(QColor(250, 250, 246))
        sheet = QPainterPath()
        sheet.moveTo(5, 2)
        sheet.lineTo(22, 2)
        sheet.lineTo(28, 8)
        sheet.lineTo(28, 30)
        sheet.lineTo(5, 30)
        sheet.closeSubpath()
        p.drawPath(sheet)
        p.setBrush(QColor(225, 225, 225))
        p.drawPolygon(QPolygonF([QPointF(22, 2), QPointF(22, 8), QPointF(28, 8)]))   # turned-up corner
        p.setBrush(QColor(215, 215, 215))
        p.drawPolygon(QPolygonF([QPointF(9, 25), QPointF(24, 25), QPointF(22, 28), QPointF(11, 28)]))  # tab
        p.setPen(QPen(QColor(110, 50, 35), 1.0))
        p.setBrush(QColor(176, 84, 56))
        p.drawPolygon(QPolygonF([QPointF(9, 25), QPointF(9, 15), QPointF(16.5, 8.5), QPointF(24, 15),
                                 QPointF(24, 25)]))                                   # the house
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255))
        p.drawRect(QRectF(12, 17, 4, 4))                                              # window to cut out
        p.setPen(QPen(QColor(30, 30, 30), 1.0, Qt.DashLine))
        p.drawLine(QPointF(9, 25), QPointF(24, 25))                                   # the fold
    elif kind == "update":
        # a green arrow coming down into a tray, under a blue circling arrow
        p.setPen(QPen(QColor(40, 110, 180), 2.4))
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(5, 3, 22, 22), 30 * 16, 300 * 16)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(40, 110, 180))
        p.drawPolygon(QPolygonF([QPointF(25.5, 4), QPointF(27.5, 11.5), QPointF(20.5, 10)]))
        p.setBrush(QColor(60, 160, 70))
        p.drawRect(QRectF(13.5, 7, 5, 9))
        p.drawPolygon(QPolygonF([QPointF(9.5, 15), QPointF(22.5, 15), QPointF(16, 22)]))
        p.setPen(dark)
        p.setBrush(QColor(225, 225, 220))
        p.drawRect(QRectF(5, 25, 22, 4))
    elif kind == "realwall":
        # a wall of rough stones, carved in
        p.setPen(QPen(QColor(70, 60, 50), 1.0))
        p.setBrush(QColor(95, 85, 72))
        p.drawRect(QRectF(2, 3, 28, 26))
        stones = [(3, 4, 9, 6), (13, 4, 7, 6), (21, 4, 8, 6), (3, 11, 6, 6), (10, 11, 10, 6), (21, 11, 8, 6),
                  (3, 18, 10, 5), (14, 18, 6, 5), (21, 18, 8, 5), (3, 24, 7, 4), (11, 24, 9, 4), (21, 24, 8, 4)]
        shades = [(196, 186, 165), (175, 165, 145), (210, 200, 180), (185, 175, 152)]
        for i, (x, y, w, h) in enumerate(stones):
            p.setBrush(QColor(*shades[i % 4]))
            p.drawRoundedRect(QRectF(x, y, w, h), 1.6, 1.6)
    p.end()
    return QIcon(pm)


# ---------------------------------------------------------------------------
# Starting a plugin: find the menu entry IngeTrazo made for it and trigger it
# ---------------------------------------------------------------------------
def _clean(text):
    return (text or "").split("\t")[0].replace("&", "").strip().lower()


def _ours(obj):
    """True for anything belonging to this toolbar (its buttons, its right-click menu)."""
    depth = 0
    while obj is not None and depth < 20:
        try:
            if (obj.objectName() or "").startswith(TOOLBAR_NAME):
                return True
            obj = obj.parent()
        except Exception:
            return False
        depth += 1
    return False


def find_plugin_action(win, name, shortcut):
    """The QAction IngeTrazo created for a plugin tool (matched by name, then shortcut)."""
    from PySide6.QtGui import QAction, QKeySequence
    want = QKeySequence(shortcut).toString()
    by_key = None
    acts = list(win.findChildren(QAction))
    # menu entries made without a parent aren't children of the window: walk the menus too

    def walk(actions, depth=0):
        for a in actions:
            acts.append(a)
            m = a.menu() if depth < 6 else None
            if m is not None:
                walk(m.actions(), depth + 1)
    try:
        walk(win.menuBar().actions())
    except Exception:
        pass
    for a in acts:
        if _ours(a):
            continue
        if _clean(a.text()) == name.lower():
            return a
        try:
            if by_key is None and want and a.shortcut().toString() == want:
                by_key = a
        except Exception:
            pass
    return by_key


_TOOLS = {}


def find_tool_class(name):
    """The plugin's Tool class, among every Tool IngeTrazo has loaded (matched by its name)."""
    found = None
    seen = set()
    todo = list(Tool.__subclasses__())
    while todo:
        c = todo.pop()
        if c in seen:
            continue
        seen.add(c)
        todo.extend(c.__subclasses__())
        if str(getattr(c, 'name', '')).strip().lower() == name.lower():
            found = c                    # the newest one wins if a plugin was loaded twice
    return found


def find_viewport(win):
    """IngeTrazo's 3D view: what a plugin tool is started with."""
    for attr in ('viewport', '_viewport', 'view'):
        vp = getattr(win, attr, None)
        if vp is not None and getattr(vp, 'scene', None) is not None:
            return vp
    from PySide6.QtWidgets import QWidget
    for w in win.findChildren(QWidget):
        if getattr(w, 'scene', None) is not None and getattr(w, 'history', None) is not None:
            return w
    return None


def run_plugin(win, name, shortcut):
    """Starts a plugin the way IngeTrazo's Extensions menu does: its tool's on_activate
    with the 3D view. Falls back to the plugin's menu entry."""
    from PySide6.QtWidgets import QMessageBox
    cls = find_tool_class(name)
    vp = find_viewport(win) if cls is not None else None
    if cls is not None and vp is not None:
        tool = _TOOLS.get(cls)           # one copy of each tool, kept between clicks
        for args in ((), (vp,)):
            if tool is not None:
                break
            try:
                tool = cls(*args)
                _TOOLS[cls] = tool
            except TypeError:
                continue
        if tool is not None:
            try:
                tool.on_activate(vp)
                return
            except Exception as e:
                QMessageBox.warning(win, PLUGIN_NAME, "%s could not start:\n%s" % (name, e))
                return
    a = find_plugin_action(win, name, shortcut)
    if a is None or a.menu() is not None:
        QMessageBox.information(win, PLUGIN_NAME,
                                "%s isn't loaded.\n\nCheck that its .py file is in your IngeTrazo "
                                "plugins folder, then restart IngeTrazo." % name)
        return
    a.trigger()


def refresh_buttons(tb):
    """Hides the buttons of plugins that aren't installed or are switched off (.off), so
    only working buttons show. They come back by themselves when the plugin is switched on."""
    win = tb.parent()
    hidden = set(load_settings().get('hidden') or [])
    for act in tb.actions():
        info = getattr(act, '_plugin', None)
        if not info:
            continue
        name, shortcut = info
        found = find_tool_class(name) is not None or find_plugin_action(win, name, shortcut) is not None
        act._missing = not found
        act.setEnabled(True)
        if hasattr(act, '_step'):
            act.setVisible(found)                # a workflow step: always shown if the plugin's there
            continue
        act.setToolTip("%s  (%s)" % (name, shortcut))
        act.setVisible(found and name not in hidden)


# ---------------------------------------------------------------------------
# The toolbar
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


DIVIDER = "|"          # in the saved layout: a divider between groups of buttons

# The plugins sorted by what they're for: the Extensions menu's sub-menus, and the
# ready-made 'one small toolbar for each kind' layout.
GROUPS = [
    ("Walls", ["3D Brick & Block Studio", "3D Realistic Wall", "3D Wrap", "3D Wood Planking", "3D Subframe", "3D Floor Plan"]),
    ("Roofs", ["3D Roof Tiles", "3D Corrugated Iron", "3D Chimneys"]),
    ("Doors & windows", ["3D Openings", "3D Period Doors", "3D Period Windows"]),
    ("Pipes & gutters", ["3D Gutters & Downpipes", "3D Soil & Waste Pipes"]),
    ("Railway & outside", ["3D Station Canopies", "3D Fences & Gates", "3D Bridges & Arches"]),
    ("Shaping tools", ["3D Loft", "3D Blend", "3D Centre Finder", "3D Find & Replace", "3D Place Along Line"]),
    ("Scale & print", ["3D Scale Studio", "3D Print Scaler", "3D Part Splitter", "3D Pieces In", "3D Card Kit"]),
    ("Notes & set-up", ["3D Show / Hide", "3D Layers & Colours", "3D Timeline", "3D Notepad", "3D Quick Links", "3D Better Icons", "3D Plugins Toolbar", "3D Check for Updates"]),
]
MAIN_ID = "main"

# ready-made workflow toolbars: (plugin, the step's note)
WORKFLOWS = {
    "Make a building": [
        ("3D Floor Plan", "Floor plan"), ("3D Openings", "Openings"), ("3D Brick & Block Studio", "Bricks"),
        ("3D Period Windows", "Windows"), ("3D Period Doors", "Doors"), ("3D Subframe", "Frame"),
        ("3D Roof Tiles", "Roof tiles"), ("3D Chimneys", "Chimneys"), ("3D Gutters & Downpipes", "Gutters"),
        ("3D Layers & Colours", "Colours"), ("3D Scale Studio", "Scale & print")],
    "Get it ready to print": [
        ("3D Layers & Colours", "Check parts"), ("3D Scale Studio", "Scale & pieces"),
        ("3D Print Scaler", "Fit the bed")],
}
STEP_SEP = "::"          # a workflow step is saved as 'plugin name::your note'


def split_step(entry):
    name, _sep, note = str(entry).partition(STEP_SEP)
    return RENAMED.get(name, name), note.strip()


def join_step(name, note=""):
    note = (note or "").replace(STEP_SEP, ":").strip()
    return name + (STEP_SEP + note if note else "")


def _new_id(bars):
    used = {b.get('id') for b in bars}
    n = 1
    while "bar%d" % n in used:
        n += 1
    return "bar%d" % n


def current_bars():
    """The saved toolbars: [{'id', 'name', 'items': [plugin names and DIVIDER], 'visible', 'workflow'}].
    The first is always the main one. Every plugin is on exactly one ordinary toolbar; new plugins go
    on the end of the main one. Workflow toolbars are extra: their steps can be any plugin, as often
    as you like ('name::note'). An old single-toolbar layout becomes the main toolbar."""
    st = load_settings()
    known = [p[0] for p in PLUGINS]
    bars = st.get('bars')
    if not isinstance(bars, list) or not bars:
        bars = [{'id': MAIN_ID, 'name': "3D Plugins", 'items': list(st.get('layout') or []),
                 'visible': bool(st.get('visible', True))}]
    out, seen = [], set()
    for b in bars:
        if not isinstance(b, dict):
            continue
        items = []
        wf = bool(b.get('workflow')) and b.get('id') != MAIN_ID
        for x in b.get('items') or []:
            if x == DIVIDER:
                if items and items[-1] != DIVIDER:
                    items.append(x)
                continue
            nm, note = split_step(x)
            if nm in SPECIAL and not wf and nm not in seen:
                seen.add(nm)
                items.append(nm)
                continue
            if nm not in known:
                continue
            if wf:
                items.append(join_step(nm, note))
            elif nm not in seen:
                seen.add(nm)
                items.append(nm)
        while items and items[-1] == DIVIDER:
            items.pop()
        out.append({'id': str(b.get('id') or _new_id(out)), 'name': str(b.get('name') or "Toolbar"),
                    'items': items, 'visible': bool(b.get('visible', True)), 'workflow': wf})
    if not out or out[0]['id'] != MAIN_ID:
        out.insert(0, {'id': MAIN_ID, 'name': "3D Plugins", 'items': [], 'visible': True})
    for name in known:
        if name not in seen:
            out[0]['items'].append(name)
    front = [n for n in (SIMPLE_ITEM, MAKE_ITEM) if n not in seen]
    if front:                                   # first time: at the front of the main toolbar
        main = out[0]['items']
        out[0]['items'] = front + ([DIVIDER] if main and main[0] != DIVIDER else []) + main
    return out


def current_layout():
    """The main toolbar's buttons (kept for anything that still asks for the old single list)."""
    return current_bars()[0]['items']


def save_bars(bars):
    s = load_settings()
    s['bars'] = bars
    s['layout'] = bars[0]['items']           # older copies of this plugin still find their buttons
    save_settings(s)


def grouped_bars():
    """The ready-made layout: a small toolbar for each kind of plugin."""
    known = [p[0] for p in PLUGINS]
    bars, used = [], set()
    for i, (title, names) in enumerate(GROUPS):
        items = [n for n in names if n in known]
        used.update(items)
        if items:
            bars.append({'id': MAIN_ID if not bars else "bar%d" % (i + 1), 'name': title, 'items': items,
                         'visible': True})
    rest = [n for n in known if n not in used]
    if rest:
        bars[0]['items'] += [DIVIDER] + rest
    bars[0]['items'] = [SIMPLE_ITEM, MAKE_ITEM, DIVIDER] + bars[0]['items']
    return bars


def bar_object_name(bar_id):
    return TOOLBAR_NAME if bar_id == MAIN_ID else "%s_%s" % (TOOLBAR_NAME, bar_id)


def all_toolbars(win=None):
    """Every one of these toolbars on the window: [(bar id, QToolBar)]."""
    from PySide6.QtWidgets import QToolBar
    win = win or _main_window()
    if win is None:
        return []
    out = []
    for tb in win.findChildren(QToolBar):
        nm = tb.objectName() or ""
        if nm == TOOLBAR_NAME:
            out.append((MAIN_ID, tb))
        elif nm.startswith(TOOLBAR_NAME + "_bar"):
            out.append((nm[len(TOOLBAR_NAME) + 1:], tb))
    return out


def build_buttons(tb, win, items=None):
    """(Re)makes a toolbar's buttons in the saved order, with dividers."""
    from PySide6.QtGui import QAction
    if items is None:
        bid = getattr(tb, '_bar_id', MAIN_ID)
        items = next((b['items'] for b in current_bars() if b['id'] == bid), [])
    for a in list(tb.actions()):
        tb.removeAction(a)
        if getattr(a, '_plugin', None) or a.isSeparator() or getattr(a, '_wf', False):
            a.deleteLater()
    if getattr(tb, '_workflow', False):
        build_workflow(tb, win, items)
        return
    hidden = set(load_settings().get('hidden') or [])
    info = {p[0]: p for p in PLUGINS}
    for entry in items:
        if entry == DIVIDER:
            sep = tb.addSeparator()
            sep.setObjectName(TOOLBAR_NAME + "_divider")
            continue
        if entry in SPECIAL:                    # Simple view, Make... - wherever you've put them
            if entry not in hidden:
                (add_simple_button if entry == SIMPLE_ITEM else add_make_button)(tb, win)
            continue
        if entry not in info:
            continue
        name, shortcut, label, icon = info[entry]
        act = QAction(make_icon(icon), label, tb)
        act.setObjectName("%s_%s" % (TOOLBAR_NAME, icon))
        act.setToolTip("%s  (%s)" % (name, shortcut))
        act._plugin = (name, shortcut)
        act.triggered.connect(lambda checked=False, n=name, s=shortcut: run_plugin(win, n, s))
        tb.addAction(act)
        act.setVisible(name not in hidden)
    # (the version number used to sit at the end of the main toolbar; taken off in 3.18 - it's in
    # the title of the Arrange toolbars window instead)


# ---------------------------------------------------------------------------
# Simple view: hide all IngeTrazo's other toolbars, leaving only Eddy's
# ---------------------------------------------------------------------------
# toolbars that count as ours (they stay up in Simple view)
OUR_TOOLBARS = (TOOLBAR_NAME, "ScaleConverterToolbar", "ed3d", "Eddy")
SIMPLE_TIP = ("Simple view: hides all of IngeTrazo's other toolbars, so only your 3D Plugins "
              "toolbars are left. Click again to bring them all back.")


def is_our_toolbar(tb):
    nm = tb.objectName() or ""
    return any(nm.startswith(k) for k in OUR_TOOLBARS) or _ours(tb)


def _bar_key(tb, i):
    return tb.objectName() or tb.windowTitle() or "toolbar%d" % i


def other_toolbars(win):
    """IngeTrazo's own toolbars on the main window (not ours, not inside a plugin window)."""
    from PySide6.QtWidgets import QToolBar
    from PySide6.QtCore import Qt
    out = []
    if win is None:
        return out
    for i, tb in enumerate(win.findChildren(QToolBar)):
        try:
            if is_our_toolbar(tb) or win.toolBarArea(tb) == Qt.NoToolBarArea:
                continue
        except Exception:
            continue
        out.append((_bar_key(tb, i), tb))
    return out


def simple_view_on():
    return bool(load_settings().get('simple_view', False))


def set_simple_view(on, win=None, save=True):
    """On: hides IngeTrazo's other toolbars (noting which were showing). Off: shows them again."""
    win = win or _main_window()
    if win is None:
        return
    s = load_settings()
    if on:
        was = set(s.get('simple_hidden') or [])
        for key, tb in other_toolbars(win):
            if tb.isVisible():
                was.add(key)
                tb.setVisible(False)
        s['simple_hidden'] = sorted(was)
    else:
        keys = set(s.get('simple_hidden') or [])
        for key, tb in other_toolbars(win):
            if key in keys or not keys:
                tb.setVisible(True)
        s['simple_hidden'] = []
    if save:
        s['simple_view'] = bool(on)
    save_settings(s)
    bars = [t for _bid, t in all_toolbars(win)]
    st = _steps_bar(win, make=False)
    if st is not None:
        bars.append(st)
    for t in bars:                              # keep the button's tick in step on every toolbar
        for a in t.actions():
            if getattr(a, '_simple', False):
                a.blockSignals(True)
                a.setChecked(bool(on))
                a.blockSignals(False)


def _show_for_close(win):
    """As IngeTrazo closes: put its toolbars back for a moment, so it doesn't save them hidden.
    If the close is cancelled (say, you pressed Cancel on 'save changes?'), Simple view goes back on."""
    from PySide6.QtCore import QTimer
    keys = set(load_settings().get('simple_hidden') or [])
    for key, tb in other_toolbars(win):
        if key in keys:
            tb.setVisible(True)

    def again():
        try:
            if win.isVisible() and simple_view_on():
                set_simple_view(True, win)
        except Exception:
            pass
    QTimer.singleShot(300, again)


def _hook_close(win):
    from PySide6.QtCore import QObject, QEvent
    if getattr(win, '_eddy_simple_hooked', False):
        return

    class _CloseWatch(QObject):
        def eventFilter(self, obj, ev):
            try:
                if obj is win and ev.type() == QEvent.Close and simple_view_on():
                    _show_for_close(win)
            except Exception:
                pass
            return False
    win._eddy_simple_watch = _CloseWatch(win)
    win.installEventFilter(win._eddy_simple_watch)
    win._eddy_simple_hooked = True


def add_simple_button(tb, win):
    from PySide6.QtGui import QAction
    act = QAction(make_icon("simple"), "Simple view", tb)
    act._wf = True                              # made fresh each time the buttons are rebuilt
    act._simple = True
    act.setObjectName(TOOLBAR_NAME + "_simple")
    act.setCheckable(True)
    act.setChecked(simple_view_on())
    act.setToolTip(SIMPLE_TIP)
    act.toggled.connect(lambda on: set_simple_view(on, win))
    tb.addAction(act)


# ---------------------------------------------------------------------------
# Step toolbar: open a plugin and its pages come up as numbered steps to click through
# ---------------------------------------------------------------------------
STEPS_NAME = TOOLBAR_NAME + "_steps"
# maroon and gold, like the works plate: big round buttons that are easy to see and click
STEPS_BAR_CSS = ("QToolBar#%s { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8e1d33, "
                 "stop:1 #650e20); border: none; border-top: 2px solid #d4a83c; "
                 "border-bottom: 2px solid #d4a83c; padding: 3px 6px; spacing: 5px; }" % STEPS_NAME)
_PILL = "border-radius: 13px; padding: 3px 10px; font-size: 10pt; "
STEP_CSS = ("QToolButton { color: #fff6e0; background: rgba(255,255,255,0.12); "
            "border: 1px solid rgba(255,255,255,0.35); " + _PILL + "} "
            "QToolButton:hover { background: rgba(255,255,255,0.28); border-color: #f0c85a; }")
HERE_CSS = ("QToolButton { color: #4a0a16; background: #f0c85a; border: 2px solid #fff3c0; "
            + _PILL + "font-weight: bold; }")
SEEN_CSS = ("QToolButton { color: #ffffff; background: #2e7d32; border: 1px solid #a5d6a7; " + _PILL + "} "
            "QToolButton:hover { background: #3d9a42; }")
NEXT_STEP_CSS = ("QToolButton { color: #4a0a16; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
                 "stop:0 #ffe08a, stop:1 #e0b040); border: 2px solid #fff3c0; " + _PILL +
                 "font-weight: bold; font-size: 10pt; padding: 3px 14px; } "
                 "QToolButton:hover { background: #fff0b0; } "
                 "QToolButton:disabled { color: #b89aa0; background: rgba(255,255,255,0.08); "
                 "border: 1px solid rgba(255,255,255,0.2); }")
SIMPLE_STEP_CSS = ("QToolButton { color: #fff6e0; background: rgba(0,0,0,0.25); "
                   "border: 1px solid #d4a83c; " + _PILL + "} "
                   "QToolButton:hover { background: rgba(0,0,0,0.4); } "
                   "QToolButton:checked { color: #4a0a16; background: #f0c85a; font-weight: bold; }")
TITLE_CSS = "color: #f0c85a; font-weight: bold; font-size: 11pt; padding: 0 8px 0 4px; background: transparent;"
_STEPS = {'dlg': None}


def steps_on():
    return bool(load_settings().get('steps_bar', True))


def plugin_window_name(w):
    """The plugin's name if w is the main window of one of these plugins (with pages), else None."""
    try:
        title = w.windowTitle() or ""
        tabs = getattr(w, 'tabs', None)
        if tabs is None or not hasattr(tabs, 'setCurrentIndex') or tabs.count() < 2:
            return None
    except Exception:
        return None
    for name, _sc, _lab, _ic in PLUGINS:
        if title == name or title.startswith(name + "  (version"):
            return name
    return None


def _steps_bar(win, make=True):
    from PySide6.QtWidgets import QToolBar
    from PySide6.QtCore import Qt, QSize
    tb = win.findChild(QToolBar, STEPS_NAME)
    if tb is None and make:
        win.addToolBarBreak(Qt.TopToolBarArea)
        tb = QToolBar("3D Plugins - Steps", win)
        tb.setObjectName(STEPS_NAME)
        tb.setIconSize(QSize(20, 20))
        tb.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        tb.setStyleSheet(STEPS_BAR_CSS)
        tb.setMinimumHeight(42)
        win.addToolBar(Qt.TopToolBarArea, tb)
        tb.setContextMenuPolicy(Qt.CustomContextMenu)
        tb.customContextMenuRequested.connect(lambda pos, tb=tb: choose_buttons(tb, tb.mapToGlobal(pos)))
    return tb


def _big(w, size=10, bold=False, height=30):
    """Makes a toolbar button big: its own height and font, whatever IngeTrazo's style says."""
    if w is None:
        return
    from PySide6.QtGui import QFont
    f = QFont(w.font())
    f.setPointSize(size)
    f.setBold(bold)
    w.setFont(f)
    w.setMinimumHeight(height)
    w.setMinimumWidth(height)


def _version_label(dark=False):
    from PySide6.QtWidgets import QLabel
    lab = QLabel("v" + VERSION)
    lab.setToolTip("%s, version %s" % (PLUGIN_NAME, VERSION))
    lab.setStyleSheet("color: %s; font-size: 9pt; padding: 0 6px; background: transparent;"
                      % ("#f0c85a" if dark else "#777777"))
    return lab


def _style_steps(tb, dlg):
    try:
        cur = dlg.tabs.currentIndex()
    except Exception:
        return
    seen = getattr(dlg, '_eddy_seen', set())
    seen.add(cur)
    dlg._eddy_seen = seen
    for a in tb.actions():
        k = getattr(a, '_page', None)
        if k is None:
            continue
        a.setText(("\u2713 " if (k in seen and k != cur) else "") + a._label)
        w = tb.widgetForAction(a)
        if w is not None:
            w.setStyleSheet(HERE_CSS if k == cur else (SEEN_CSS if k in seen else STEP_CSS))
            _big(w, 10, k == cur)
    for a in tb.actions():
        if getattr(a, '_next', False):
            last = cur >= dlg.tabs.count() - 1
            a.setEnabled(not last)
            a.setText("All done \u2713" if last else "Next step \u25b6")
            _big(tb.widgetForAction(a), 10, True, 32)


def _go_page(dlg, k):
    try:
        if k == 'next':
            k = min(dlg.tabs.currentIndex() + 1, dlg.tabs.count() - 1)
        dlg.tabs.setCurrentIndex(k)
        dlg.raise_()
        dlg.activateWindow()
    except Exception:
        pass


def show_steps(dlg, win=None):
    """Puts up the step toolbar for this plugin window (any problem goes in IngeTrazo's log)."""
    try:
        _show_steps(dlg, win)
    except Exception:
        import traceback
        print("%s: step toolbar problem:\n%s" % (PLUGIN_NAME, traceback.format_exc()))


def _alive(w):
    try:
        return w is not None and w.isVisible()
    except Exception:                  # the window has been deleted
        return False


def _poll_steps(win):
    """Every half second: is a plugin open? Put its steps up (or take them away)."""
    try:
        if not steps_on():
            return
        from PySide6.QtWidgets import QApplication
        cur = _STEPS['dlg']
        act = QApplication.activeWindow()
        pick = None
        if _alive(act) and plugin_window_name(act):
            pick = act
        elif _alive(cur):
            pick = cur
        else:
            for w in QApplication.topLevelWidgets():
                if _alive(w) and plugin_window_name(w):
                    pick = w
                    break
        tb = _steps_bar(win, make=False)
        if pick is None:
            if cur is not None or (tb is not None and tb.isVisible()):
                _STEPS['dlg'] = None
                if tb is not None:
                    tb.setVisible(False)
            return
        if pick is not cur or tb is None or not tb.isVisible():
            show_steps(pick, win)
    except Exception:
        import traceback
        print("%s: step toolbar check:\n%s" % (PLUGIN_NAME, traceback.format_exc()))


def _show_steps(dlg, win=None):
    from PySide6.QtGui import QAction
    from PySide6.QtWidgets import QLabel
    win = win or _main_window()
    name = plugin_window_name(dlg)
    if win is None or name is None or not steps_on():
        return
    tb = _steps_bar(win)
    if _STEPS['dlg'] is dlg and tb.isVisible() and tb.actions():
        _style_steps(tb, dlg)
        return
    _STEPS['dlg'] = dlg
    for a in list(tb.actions()):
        tb.removeAction(a)
        a.deleteLater()
    tb.setStyleSheet(STEPS_BAR_CSS)
    # Simple view first: hide IngeTrazo's other toolbars from right here
    sv = QAction(make_icon("simple"), "Simple view", tb)
    sv._simple = True
    sv.setCheckable(True)
    sv.setChecked(simple_view_on())
    sv.setToolTip(SIMPLE_TIP)
    sv.toggled.connect(lambda on: set_simple_view(on, win))
    tb.addAction(sv)
    w = tb.widgetForAction(sv)
    if w is not None:
        w.setStyleSheet(SIMPLE_STEP_CSS)
        _big(w, 9)
    title = QLabel(name.replace("3D ", "", 1) + ":")
    title.setStyleSheet(TITLE_CSS)
    _big(title, 11, True, 30)
    tb.addWidget(title)
    tabs = dlg.tabs
    for k in range(tabs.count()):
        text = (tabs.tabText(k) or "").replace("&&", "&")      # 'Base & top' as written on the page
        a = QAction("", tb)
        a._page = k
        a._label = "%d  %s" % (k + 1, text.replace("&", "&&"))  # && shows one & on a button
        a.setToolTip("Step %d: go to the '%s' page" % (k + 1, text))
        a.triggered.connect(lambda checked=False, d=dlg, k=k: _go_page(d, k))
        tb.addAction(a)
    nxt = QAction("Next step \u25b6", tb)
    nxt._next = True
    nxt.setToolTip("Go on to the next page")
    nxt.triggered.connect(lambda checked=False, d=dlg: _go_page(d, 'next'))
    tb.addAction(nxt)
    w = tb.widgetForAction(nxt)
    if w is not None:
        w.setStyleSheet(NEXT_STEP_CSS)
    if VIDEOS.get(name):                        # this plugin has a video: a button to watch it
        va = QAction("\u25b6  Watch the video", tb)
        va.setToolTip("Opens the %s video on YouTube" % name.replace("3D ", "", 1))
        va.triggered.connect(lambda checked=False, n=name: open_video(n))
        tb.addAction(va)
        w = tb.widgetForAction(va)
        if w is not None:
            w.setStyleSheet(SIMPLE_STEP_CSS)
            _big(w, 9)
    ver = tb.addWidget(_version_label(dark=True))
    ver._wf = True
    if not getattr(dlg, '_eddy_steps_hooked', False):
        try:
            tabs.currentChanged.connect(lambda _i, d=dlg: _STEPS['dlg'] is d and _style_steps(_steps_bar(win), d))
        except Exception:
            pass
        dlg._eddy_steps_hooked = True
    tb.setVisible(True)
    _style_steps(tb, dlg)


def hide_steps(dlg=None, win=None):
    """Takes the step toolbar away (when its plugin closes), or moves it to another open plugin."""
    from PySide6.QtWidgets import QApplication
    win = win or _main_window()
    if win is None:
        return
    if dlg is not None and _STEPS['dlg'] is not dlg:
        return
    _STEPS['dlg'] = None
    tb = _steps_bar(win, make=False)
    if tb is None:
        return
    for w in QApplication.instance().topLevelWidgets():       # another plugin still open: show its steps
        try:
            if w is not dlg and w.isVisible() and plugin_window_name(w):
                show_steps(w, win)
                return
        except Exception:
            continue
    tb.setVisible(False)


def _hook_steps(win):
    from PySide6.QtCore import QObject, QEvent, QTimer
    from PySide6.QtWidgets import QApplication
    if getattr(win, '_eddy_steps_watch', None) is not None:
        return
    wanted = (QEvent.Show, QEvent.Hide, QEvent.Close, QEvent.WindowActivate)

    class _StepWatch(QObject):
        def eventFilter(self, obj, ev):
            try:
                t = ev.type()
                if t in wanted and obj.isWidgetType() and obj.isWindow() and plugin_window_name(obj):
                    if t in (QEvent.Show, QEvent.WindowActivate):
                        QTimer.singleShot(0, lambda o=obj: o.isVisible() and show_steps(o, win))
                    else:
                        QTimer.singleShot(0, lambda o=obj: (not o.isVisible()) and hide_steps(o, win))
            except Exception:
                pass
            return False
    win._eddy_steps_watch = _StepWatch(win)
    QApplication.instance().installEventFilter(win._eddy_steps_watch)
    # and a check every half second, in case IngeTrazo opens a plugin without the window noticing
    t = QTimer(win)
    t.setObjectName(STEPS_NAME + "_timer")
    t.setInterval(500)
    t.timeout.connect(lambda: _poll_steps(win))
    t.start()
    win._eddy_steps_timer = t
    print("%s %s: step toolbar ready" % (PLUGIN_NAME, VERSION))


def set_steps_on(on, win=None):
    s = load_settings()
    s['steps_bar'] = bool(on)
    save_settings(s)
    win = win or _main_window()
    if win is None:
        return
    if not on:
        _STEPS['dlg'] = None
        tb = _steps_bar(win, make=False)
        if tb is not None:
            tb.setVisible(False)
        return
    from PySide6.QtWidgets import QApplication
    for w in QApplication.instance().topLevelWidgets():
        try:
            if w.isVisible() and plugin_window_name(w):
                show_steps(w, win)
                break
        except Exception:
            continue


# ---------------------------------------------------------------------------
# What do you want to make? - a job's steps across the plugins, one at a time
# ---------------------------------------------------------------------------
PROJECT_NAME = TOOLBAR_NAME + "_project"

# EssexBrick Model Works videos on YouTube: add each plugin's link here as its video comes out
VIDEOS = {
    "Getting started": "https://youtu.be/ho2iT4jlClQ",
    "How to install": "https://youtu.be/Qernr_VfzYQ",
    "3D Floor Plan": "https://youtu.be/PPgYvw2RL8I",
    "3D Openings": "https://youtu.be/2Y94tA5ecPQ",
    "3D Subframe": "https://youtu.be/HjO3KEXHdlY",
    "3D Period Windows": "https://youtu.be/dLsRhKhNmY8",
    "3D Period Doors": "https://youtu.be/FU5quEtEPTQ",
    "3D Chimneys": "https://youtu.be/ltoIpYbRxhQ",
    "3D Roof Tiles": "https://youtu.be/atuQ2b-Nx6k",
    "3D Brick & Block Studio": "https://youtu.be/acH3uugEmXI",
    "3D Gutters & Downpipes": "https://youtu.be/s0yIkavaSiA",
    "3D Soil & Waste Pipes": "https://youtu.be/eiuQK9xQjDA",
    "3D Layers & Colours": "https://youtu.be/27Vfeo2Jmj4",
    "3D Scale Studio": "https://youtu.be/IrMON6o8TE8",
    "3D Card Kit": "https://youtu.be/1Z8iHbJ2nJU",
    "3D Realistic Wall": "https://youtu.be/0Sd6ZMrLLf4",
}


def open_video(key):
    url = VIDEOS.get(key) or ""
    if not url:
        return
    try:
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl(url))
    except Exception as e:
        print("%s: couldn't open the video (%s): %s" % (PLUGIN_NAME, e, url))
# a step can be a choice: [(plugin, what it's called)] - you pick one when you get to it
ROOF_CHOICE = [("3D Roof Tiles", "Roof tiles"), ("3D Corrugated Iron", "Roof sheets")]
WALL_CHOICE = [("3D Brick & Block Studio", "Bricks"), ("3D Realistic Wall", "Realistic wall")]
# (what it's called, [(plugin or a choice, the step's name)]) - the building follows Eddy's build order
PROJECTS = [
    ("Make a building", [
        ("3D Floor Plan", "Floor plan"), ("3D Openings", "Openings"), ("3D Subframe", "Frame"),
        ("3D Period Windows", "Windows"), ("3D Period Doors", "Doors"), ("3D Chimneys", "Chimneys"),
        (ROOF_CHOICE, "Roof"), (WALL_CHOICE, "Walling"),
        ("3D Gutters & Downpipes", "Gutters"), ("3D Soil & Waste Pipes", "Soil pipes"),
        ("3D Layers & Colours", "Colours"), ("3D Scale Studio", "Scale & print")]),
    ("Make a station building", [
        ("3D Floor Plan", "Floor plan"), ("3D Openings", "Openings"), ("3D Subframe", "Frame"),
        ("3D Period Windows", "Windows"), ("3D Period Doors", "Doors"), ("3D Chimneys", "Chimneys"),
        (ROOF_CHOICE, "Roof"), (WALL_CHOICE, "Walling"), ("3D Station Canopies", "Canopy"),
        ("3D Gutters & Downpipes", "Gutters"), ("3D Soil & Waste Pipes", "Soil pipes"),
        ("3D Layers & Colours", "Colours"), ("3D Scale Studio", "Scale & print")]),
    ("Make a goods shed or engine shed", [
        ("3D Floor Plan", "Floor plan"), ("3D Openings", "Openings"), ("3D Subframe", "Frame"),
        ("3D Period Windows", "Windows"), ("3D Period Doors", "Goods doors"),
        (ROOF_CHOICE, "Roof"), (WALL_CHOICE, "Walling"), ("3D Gutters & Downpipes", "Gutters"),
        ("3D Layers & Colours", "Colours"), ("3D Scale Studio", "Scale & print")]),
    ("Make a timber building", [
        ("3D Floor Plan", "Floor plan"), ("3D Openings", "Openings"), ("3D Subframe", "Frame"),
        ("3D Period Windows", "Windows"), ("3D Period Doors", "Doors"), ("3D Wood Planking", "Cladding"),
        (ROOF_CHOICE, "Roof"), ("3D Gutters & Downpipes", "Gutters"),
        ("3D Layers & Colours", "Colours"), ("3D Scale Studio", "Scale & print")]),
    ("Make a tin shed", [
        ("3D Floor Plan", "Floor plan"), ("3D Openings", "Openings"), ("3D Subframe", "Frame"),
        ("3D Period Windows", "Windows"), ("3D Period Doors", "Doors"), ("3D Corrugated Iron", "Tin walls"),
        (ROOF_CHOICE, "Roof"), ("3D Gutters & Downpipes", "Gutters"),
        ("3D Layers & Colours", "Colours"), ("3D Scale Studio", "Scale & print")]),
    ("Make a factory chimney", [
        ("3D Chimneys", "Chimney"), ("3D Wrap", "Bricks round it"),
        ("3D Layers & Colours", "Colours"), ("3D Scale Studio", "Scale & print")]),
    ("Make a bridge or arches", [
        ("3D Bridges & Arches", "Bridge"), (WALL_CHOICE, "Walling"),
        ("3D Layers & Colours", "Colours"), ("3D Scale Studio", "Scale & print")]),
    ("Make a station canopy", [
        ("3D Station Canopies", "Canopy"), (ROOF_CHOICE, "Roof"),
        ("3D Gutters & Downpipes", "Gutters"), ("3D Layers & Colours", "Colours"),
        ("3D Scale Studio", "Scale & print")]),
    ("Make fences and gates", [
        ("3D Fences & Gates", "Fences"), ("3D Layers & Colours", "Colours"),
        ("3D Scale Studio", "Scale & print")]),
    ("Make a riveted part (loco or wagon)", [
        ("3D Loft", "Shape"), ("3D Blend", "Blend the joins"), ("3D Place Along Line", "Rivets"),
        ("3D Find & Replace", "Full rivets"), ("3D Layers & Colours", "Colours"),
        ("3D Scale Studio", "Scale & print")]),
    ("Make a boiler with a dome", [
        ("3D Loft", "Boiler"), ("3D Blend", "Dome & collar"), ("3D Place Along Line", "Rivets & bands"),
        ("3D Layers & Colours", "Colours"), ("3D Scale Studio", "Scale & print")]),
    ("Get a model ready to print", [
        ("3D Layers & Colours", "Check parts"), ("3D Scale Studio", "Scale & pieces"),
        ("3D Print Scaler", "Fit the bed")]),
    ("Make a card kit (print on paper)", [
        ("3D Layers & Colours", "Colours"), ("3D Card Kit", "Card kit")]),
]
# the Make... menu, sorted into groups (any job not listed here goes under 'More')
PROJECT_GROUPS = [
    ("Buildings", ["Make a building", "Make a station building", "Make a goods shed or engine shed",
                   "Make a timber building", "Make a tin shed", "Make a factory chimney"]),
    ("Railway & outside", ["Make a bridge or arches", "Make a station canopy", "Make fences and gates"]),
    ("Locos, wagons & parts", ["Make a riveted part (loco or wagon)", "Make a boiler with a dome"]),
    ("Printing", ["Get a model ready to print", "Make a card kit (print on paper)"]),
]
MAKE_CSS = ("QToolButton { color: #4a0a16; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #ffe08a, stop:1 #e0b040); border: 2px solid #8e1d33; border-radius: 13px; "
            "padding: 3px 12px; font-weight: bold; } QToolButton:hover { background: #fff0b0; } "
            "QToolButton::menu-indicator { subcontrol-position: right center; right: 6px; }")
SMALL_CSS = ("QToolButton { color: #fff6e0; background: rgba(0,0,0,0.25); border: 1px solid #d4a83c; "
             "border-radius: 12px; padding: 2px 9px; } QToolButton:hover { background: rgba(0,0,0,0.4); }")


def _project():
    """The job you're on: (its name, its steps, the steps done) - or None."""
    st = load_settings()
    pj = st.get('project')
    for name, steps in PROJECTS:
        if name == pj:
            try:
                done = set(int(i) for i in st.get('project_done') or [])
            except Exception:
                done = set()
            known = {p[0] for p in PLUGINS}
            out = []
            for plug, label in steps:
                if isinstance(plug, list):
                    opts = [o for o in plug if o[0] in known]
                    if opts:
                        out.append((opts, label))
                elif plug in known:
                    out.append((plug, label))
            return name, out, done
    return None


def _save_project(name, done=(), cur=None):
    s = load_settings()
    s['project'] = name
    s['project_done'] = sorted(int(i) for i in done)
    s['project_cur'] = cur
    save_settings(s)


def _project_cur():
    """The step you're on (lit up), or None before you've started."""
    try:
        c = load_settings().get('project_cur')
        return None if c is None else int(c)
    except Exception:
        return None


def add_make_button(tb, win):
    """The big 'What do you want to make?' button, with the list of jobs."""
    from PySide6.QtWidgets import QToolButton, QMenu
    from PySide6.QtCore import Qt, QSize
    btn = QToolButton(tb)
    btn.setText("Make...")
    btn.setIcon(make_icon("make"))
    btn.setIconSize(tb.iconSize() if tb.iconSize().width() > 0 else QSize(28, 28))
    btn.setToolButtonStyle(tb.toolButtonStyle())
    btn.setAutoRaise(True)
    btn.setToolTip("What do you want to make? Pick a building, a bridge... and a toolbar takes you "
                   "through the plugins for it, one step at a time.")
    btn.setStatusTip("Pick what you want to make - a building, a bridge... - and a toolbar takes you "
                   "through the plugins for it, one step at a time.")
    btn.setPopupMode(QToolButton.InstantPopup)
    menu = QMenu(btn)
    menu.setObjectName(TOOLBAR_NAME + "_makemenu")
    steps_of = dict(PROJECTS)
    listed = set()
    groups = [(g, [n for n in names if n in steps_of]) for g, names in PROJECT_GROUPS]
    for g, names in PROJECT_GROUPS:
        listed.update(names)
    rest = [n for n, _ in PROJECTS if n not in listed]
    if rest:
        groups.append(("More", rest))
    for g, names in groups:
        if not names:
            continue
        sub = menu.addMenu(g)
        for name in names:
            a = sub.addAction("%s   (%d steps)" % (name, len(steps_of[name])))
            a.triggered.connect(lambda checked=False, n=name: start_project(n, win))
    menu.addSeparator()
    if VIDEOS.get("Getting started"):
        menu.addSeparator()
        vid = menu.addAction("\u25b6  Watch: Getting started (video)")
        vid.triggered.connect(lambda checked=False: open_video("Getting started"))
    if VIDEOS.get("How to install"):
        ins = menu.addAction("\u25b6  Watch: How to install (video)")
        ins.triggered.connect(lambda checked=False: open_video("How to install"))
    menu.addSeparator()
    off = menu.addAction("Put the steps away")
    off.triggered.connect(lambda checked=False: close_project(win))
    btn.setMenu(menu)
    tb.toolButtonStyleChanged.connect(btn.setToolButtonStyle)     # labels on/off like the others
    act = tb.addWidget(btn)
    act._wf = True
    act.setObjectName(TOOLBAR_NAME + "_make")


def _project_bar(win, make=True):
    from PySide6.QtWidgets import QToolBar
    from PySide6.QtCore import Qt, QSize
    tb = win.findChild(QToolBar, PROJECT_NAME)
    if tb is None and make:
        win.addToolBarBreak(Qt.TopToolBarArea)
        tb = QToolBar("3D Plugins - What you're making", win)
        tb.setObjectName(PROJECT_NAME)
        tb.setIconSize(QSize(28, 28))
        tb.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        win.addToolBar(Qt.TopToolBarArea, tb)
        tb.setContextMenuPolicy(Qt.CustomContextMenu)
        tb.customContextMenuRequested.connect(lambda pos, tb=tb: choose_buttons(tb, tb.mapToGlobal(pos)))
    return tb


def start_project(name, win=None):
    win = win or _main_window()
    _save_project(name, (), None)
    show_project(win)
    pj = _project()
    if pj and pj[1]:
        project_step(win, 0)                    # straight on to step 1


def close_project(win=None):
    win = win or _main_window()
    _save_project(None, ())
    tb = _project_bar(win, make=False) if win is not None else None
    if tb is not None:
        tb.setVisible(False)


def _close_plugin_windows(except_name=None):
    """Closes the plugin you're in (as you move on to the next step)."""
    from PySide6.QtWidgets import QApplication
    for w in QApplication.instance().topLevelWidgets():
        try:
            nm = plugin_window_name(w) or (w.windowTitle() if w.isVisible() and
                                           any(w.windowTitle() == p[0] for p in PLUGINS) else None)
            if w.isVisible() and nm and nm != except_name:
                w.close()
        except Exception:
            continue


def _choices():
    c = load_settings().get('project_choice')
    return c if isinstance(c, dict) else {}


def _chosen(name, k, opts):
    """The covering you picked for this step before (or None)."""
    pick = _choices().get("%s|%d" % (name, k))
    return pick if pick in [o[0] for o in opts] else None


def _choose(name, k, plugin):
    s = load_settings()
    c = s.get('project_choice') if isinstance(s.get('project_choice'), dict) else {}
    c["%s|%d" % (name, k)] = plugin
    s['project_choice'] = c
    save_settings(s)


def _choice_menu(win, tb, k, opts):
    from PySide6.QtWidgets import QMenu
    menu = QMenu(tb)
    menu.setObjectName(TOOLBAR_NAME + "_choice")
    info = {p[0]: p for p in PLUGINS}
    for plug, label in opts:
        a = menu.addAction(make_icon(info[plug][3]), label)
        a.triggered.connect(lambda checked=False, plug=plug: project_step(win, k, True, plug))
    return menu


def _pop_choice(win, k):
    """Next step lands on a choice you haven't made yet: show the list under its button."""
    tb = _project_bar(win, make=False)
    if tb is None:
        return False
    for a in tb.actions():
        if getattr(a, '_pstep', None) == k and a.menu() is not None:
            w = tb.widgetForAction(a)
            if w is not None:
                a.menu().popup(w.mapToGlobal(w.rect().bottomLeft()))
                return True
    return False


def project_step(win, k, close_others=False, plugin=None):
    """Opens step k: it's lit up as the one you're on; the step you were on gets its tick."""
    pj = _project()
    if not pj or not (0 <= k < len(pj[1])):
        return
    name, steps, done = pj
    opts = steps[k][0] if isinstance(steps[k][0], list) else None
    if opts is not None:
        if plugin is None:
            plugin = _chosen(name, k, opts)
        if plugin is None:                      # not picked yet: ask which covering
            if not _pop_choice(win, k):
                plugin = opts[0][0]
            else:
                return
        _choose(name, k, plugin)
        pj = _project()
        name, steps, done = pj
    cur = _project_cur()
    if cur is not None and cur != k:
        done.add(cur)
    done.discard(k)
    if opts is None:
        plugin = steps[k][0]
    if close_others:
        _close_plugin_windows(plugin)
    _save_project(name, done, k)
    if opts is not None:
        show_project(win)                       # the button now shows the covering you picked
    else:
        _style_project(win)
    sc = next((p[1] for p in PLUGINS if p[0] == plugin), "")
    run_plugin(win, plugin, sc)


def project_next(win):
    """Ticks the step you're on and opens the next one."""
    pj = _project()
    if not pj:
        return
    name, steps, done = pj
    cur = _project_cur()
    after = [k for k in range(len(steps)) if (cur is None or k > cur) and k not in done]
    nxt = after[0] if after else next((k for k in range(len(steps)) if k not in done and k != cur), None)
    if nxt is None:                             # that was the last one
        if cur is not None:
            done.add(cur)
        _save_project(name, done, None)
        _style_project(win)
        return
    project_step(win, nxt, close_others=True)


def show_project(win=None):
    """Puts up the toolbar for the job you're on (or takes it away if there isn't one)."""
    from PySide6.QtGui import QAction
    from PySide6.QtWidgets import QLabel
    win = win or _main_window()
    if win is None:
        return
    pj = _project()
    if not pj:
        tb = _project_bar(win, make=False)
        if tb is not None:
            tb.setVisible(False)
        return
    name, steps, done = pj
    tb = _project_bar(win)
    for a in list(tb.actions()):
        tb.removeAction(a)
        a.deleteLater()
    title = QLabel("  %s:  " % name.replace("Make ", "Making ", 1).replace("Get ", "Getting ", 1))
    title.setStyleSheet("font-weight: bold;")
    tb.addWidget(title)
    info = {p[0]: p for p in PLUGINS}
    for k, (plugin, label) in enumerate(steps):
        if isinstance(plugin, list):            # a choice: roof tiles or roof sheets...
            pick = _chosen(name, k, plugin)
            plabel = next((l for p_, l in plugin if p_ == pick), None)
            a = QAction(make_icon(info[pick or plugin[0][0]][3]), "", tb)
            a._pstep = k
            a._label = "%d  %s \u25be" % (k + 1, (plabel or label).replace("&", "&&"))
            a.setToolTip("Step %d: %s - pick %s" % (k + 1, label, " or ".join(l for _p, l in plugin)))
            a.setMenu(_choice_menu(win, tb, k, plugin))
            tb.addAction(a)
            try:
                from PySide6.QtWidgets import QToolButton
                w = tb.widgetForAction(a)
                if w is not None:
                    w.setPopupMode(QToolButton.InstantPopup)
            except Exception:
                pass
            continue
        icon = info[plugin][3]
        a = QAction(make_icon(icon), "", tb)
        a._pstep = k
        a._label = "%d  %s" % (k + 1, label.replace("&", "&&"))
        a.setToolTip("Step %d: %s - opens %s" % (k + 1, label, plugin))
        a.triggered.connect(lambda checked=False, k=k: project_step(win, k, close_others=True))
        tb.addAction(a)
    tb.addSeparator()
    nxt = QAction(make_icon("next"), "Next step", tb)
    nxt._pnext = True
    nxt.setToolTip("Closes the plugin you're in and opens the next step")
    nxt.triggered.connect(lambda checked=False: project_next(win))
    tb.addAction(nxt)
    for icon, text, tip, fn in (
            ("again", "Start again", "Clears the ticks, back to step 1", lambda: start_again(win)),
            ("openlast", "Open last", "Opens the model you last had open", lambda: open_last(win)),
            ("close", "Close", "Puts these steps away (pick again from Make...)", lambda: close_project(win))):
        a = QAction(make_icon(icon), text, tb)
        a.setToolTip(tip)
        a.triggered.connect(lambda checked=False, fn=fn: fn())
        tb.addAction(a)
    tb.setVisible(True)
    _style_project(win)


def start_again(win):
    pj = _project()
    if pj:
        _save_project(pj[0], (), None)
        _style_project(win)


def _style_project(win):
    tb = _project_bar(win, make=False)
    pj = _project()
    if tb is None or not pj:
        return
    _name, steps, done = pj
    cur = _project_cur()
    if cur is None:                             # not started yet: the first one not done is lit
        cur = next((k for k in range(len(steps)) if k not in done), None)
    left = [k for k in range(len(steps)) if k not in done and k != cur]
    for a in tb.actions():
        k = getattr(a, '_pstep', None)
        w = tb.widgetForAction(a)
        if k is not None:
            a.setText(("\u2713 " if k in done else "") + a._label)
            if w is not None:                   # the step you're on lit up, done ones in green
                w.setStyleSheet(NEXT_CSS if k == cur else (DONE_CSS if k in done else ""))
        elif getattr(a, '_pnext', False):
            a.setEnabled(cur is not None)
            a.setText("Finish" if cur is not None and not left else
                      ("All done" if cur is None else "Next step"))


# ---------------------------------------------------------------------------
# Workflow toolbars: numbered steps, the next one lit up, ticks as you go
# ---------------------------------------------------------------------------
NEXT_CSS = ("QToolButton { background-color: #fff3a0; border: 1px solid #c9a227; border-radius: 4px; "
            "font-weight: bold; }")
DONE_CSS = "QToolButton { color: #2e7d32; }"


def wf_done(bid):
    try:
        return set(int(i) for i in (load_settings().get('progress') or {}).get(bid, []))
    except Exception:
        return set()


def wf_set_done(bid, done):
    s = load_settings()
    pr = s.get('progress') if isinstance(s.get('progress'), dict) else {}
    pr[bid] = sorted(int(i) for i in done)
    s['progress'] = pr
    save_settings(s)


def build_workflow(tb, win, items):
    from PySide6.QtGui import QAction
    from PySide6.QtWidgets import QLabel
    info = {p[0]: p for p in PLUGINS}
    title = QLabel("  %s:  " % tb._bar_name)
    title.setStyleSheet("font-weight: bold;")
    ta = tb.addWidget(title)
    ta._wf = True
    n = 0
    for entry in items:
        if entry == DIVIDER:
            sep = tb.addSeparator()
            sep.setObjectName(TOOLBAR_NAME + "_divider")
            continue
        nm, note = split_step(entry)
        if nm not in info:
            continue
        name, shortcut, label, icon = info[nm]
        n += 1
        act = QAction(make_icon(icon), "", tb)
        act.setObjectName("%s_step%d" % (TOOLBAR_NAME, n))
        act._plugin = (name, shortcut)
        act._step = n - 1
        short = note or label
        act._label = "%d %s" % (n, short if len(short) <= 16 else short[:15] + "\u2026")
        act._tip = "Step %d: %s%s  (%s)" % (n, name, (" - " + note) if note else "", shortcut)
        act.triggered.connect(lambda checked=False, n_=name, s_=shortcut, k=n - 1:
                              step_clicked(tb, win, n_, s_, k))
        tb.addAction(act)
    again = QAction(make_icon("again"), "Start again", tb)
    again._wf = True
    again.setObjectName(TOOLBAR_NAME + "_again")
    again.setToolTip("Clears the ticks, back to step 1.")
    again.triggered.connect(lambda checked=False: reset_workflow(tb))
    tb.addAction(again)
    last = QAction(make_icon("openlast"), "Open last", tb)
    last._wf = True
    last.setObjectName(TOOLBAR_NAME + "_openlast")
    last.setToolTip("Opens the model you last had open (the top one in File > Open Recent).")
    last.triggered.connect(lambda checked=False: open_last(win))
    tb.addAction(last)
    style_workflow(tb)


# ---------------------------------------------------------------------------
# Open last: one click for the model you last had open. It uses IngeTrazo's own
# File > Open Recent list (so IngeTrazo still asks about saving the model you're in).
# ---------------------------------------------------------------------------
NOT_A_FILE = ("clear", "empty", "no recent", "none")


MODEL_TYPES = (".igz", ".ige", ".igt")


def _action_path(a):
    """The file an Open Recent entry opens, if it says (its data, else its text)."""
    try:
        d = a.data()
        if isinstance(d, str) and d.strip():
            return d.strip()
    except Exception:
        pass
    return (a.text() or "").split("\t")[0].replace("&", "").strip()


def _recent_menu(win):
    """IngeTrazo's list of recent models. If there's more than one 'recent' list (recent folders, say),
    the one with model files in it."""
    from PySide6.QtWidgets import QMenu
    best, best_n = None, -1
    for m in win.findChildren(QMenu):
        try:
            if "recent" not in _clean(m.title()) or _ours(m):
                continue
            try:
                m.aboutToShow.emit()
            except Exception:
                pass
            n = sum(1 for a in m.actions() if _action_path(a).lower().endswith(MODEL_TYPES)
                    or any(t in _action_path(a).lower() for t in MODEL_TYPES))
            if "folder" in _clean(m.title()) or "dir" in _clean(m.title()):
                n -= 1000
            if n > best_n:
                best, best_n = m, n
        except Exception:
            continue
    return best


def _recent_files(menu):
    """The entries in the Open Recent menu that are files, newest first."""
    try:
        menu.aboutToShow.emit()          # some programs fill the list just before it shows
    except Exception:
        pass
    out = []
    for a in menu.actions():
        try:
            if a.isSeparator() or a.menu() is not None or not a.isEnabled():
                continue
            t = _clean(a.text())
            if not t or any(w in t for w in NOT_A_FILE):
                continue
            out.append(a)
        except Exception:
            continue
    return out


def _open_action(win):
    from PySide6.QtGui import QAction
    for a in win.findChildren(QAction):
        try:
            if _clean(a.text()) in ("open", "open...", "open…", "open file", "open file...") and not _ours(a):
                return a
        except Exception:
            continue
    return None


def open_last(win=None):
    from PySide6.QtWidgets import QMessageBox
    win = win or _main_window()
    if win is None:
        return
    menu = _recent_menu(win)
    files = _recent_files(menu) if menu is not None else []
    if files:
        a = files[0]
        print("%s: Open last - %s" % (PLUGIN_NAME, (a.text() or "").replace("&", "")))
        a.trigger()
        return
    op = _open_action(win)
    if menu is None:
        why = "Couldn't find IngeTrazo's Open Recent list."
    else:
        why = "There's nothing in IngeTrazo's Open Recent list yet - open a model once and this button will work."
    if op is not None:
        QMessageBox.information(win, PLUGIN_NAME, why + "\n\nThe ordinary Open window will come up instead.")
        op.trigger()
    else:
        QMessageBox.information(win, PLUGIN_NAME, why)


# ---------------------------------------------------------------------------
# Start window: when IngeTrazo opens, open the last model, another one, or start new
# ---------------------------------------------------------------------------
def start_popup_on():
    return bool(load_settings().get('start_popup', True))


def set_start_popup(on):
    s = load_settings()
    s['start_popup'] = bool(on)
    save_settings(s)


def _recent_name(a):
    """The model's own name for an Open Recent entry (not its folder)."""
    import re
    for t in (_action_path(a), (a.text() or "").split("\t")[0].replace("&", "").strip()):
        m = re.search(r"([^\\/:]+?)(%s)\b" % "|".join(re.escape(x) for x in MODEL_TYPES), t, re.I)
        if m:
            got = m.group(1).strip()
            if t.lstrip("&")[:1].isdigit() and not ("\\" in t or "/" in t):
                got = re.sub(r"^\d+[.)]?\s+", "", got)      # '1 name' -> 'name'
            return got
    t = (a.text() or "").split("\t")[0].replace("&", "").strip()
    t = re.sub(r"^\d+[.)]?\s+", "", t)                    # '1 name' -> 'name'
    for sep in ("  ", " \u2014 ", " \u2013 ", " - ", " ("):
        if sep in t:
            t = t.split(sep)[0]
            break
    return os.path.splitext(os.path.basename(t.rstrip("\\/")))[0] or t


def start_popup(win=None):
    """A small window when IngeTrazo starts: Open last model, Open another, or Start a new one (the
    empty model IngeTrazo has open already)."""
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QCheckBox
    from PySide6.QtCore import Qt
    win = win or _main_window()
    if win is None or getattr(win, '_eddy_start_shown', False):
        return
    win._eddy_start_shown = True
    menu = _recent_menu(win)
    files = _recent_files(menu) if menu is not None else []
    op = _open_action(win)
    dlg = QDialog(win)
    dlg.setWindowTitle("Start")
    lay = QVBoxLayout(dlg)
    lab = QLabel("What would you like to do?")
    f = lab.font()
    f.setPointSize(f.pointSize() + 2)
    f.setBold(True)
    lab.setFont(f)
    lay.addWidget(lab)
    choice = [None]

    def pick(what):
        choice[0] = what
        dlg.accept()
    big = "QPushButton { padding: 8px 14px; text-align: left; font-size: 11pt; }"
    if files:
        b = QPushButton(make_icon("openlast"), "Open last:  %s" % _recent_name(files[0]))
        b.setToolTip((files[0].text() or "").replace("&", ""))
        b.setStyleSheet(big)
        b.setDefault(True)
        b.clicked.connect(lambda: pick('last'))
        lay.addWidget(b)
        for a in files[1:4]:                       # the next few from the recent list
            bb = QPushButton("      %s" % _recent_name(a))
            bb.setToolTip((a.text() or "").replace("&", ""))
            bb.setFlat(True)
            bb.setStyleSheet("QPushButton { text-align: left; padding: 3px 14px; }")
            bb.clicked.connect(lambda _=False, a=a: pick(a))
            lay.addWidget(bb)
    if op is not None:
        b = QPushButton("Open another model...")
        b.setStyleSheet(big)
        b.clicked.connect(lambda: pick('open'))
        lay.addWidget(b)
    b = QPushButton("Start a new model")
    b.setToolTip("Carries on with the empty model IngeTrazo has open.")
    b.setStyleSheet(big)
    b.clicked.connect(lambda: pick('new'))
    lay.addWidget(b)
    cb = QCheckBox("Show this when IngeTrazo starts")
    cb.setToolTip("Untick it to stop this window coming up. It can be put back from the right-click menu on "
                  "the 3D Plugins toolbar.")
    cb.setChecked(True)
    cb.toggled.connect(set_start_popup)
    lay.addWidget(cb)
    dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
    dlg.exec()
    what = choice[0]
    if what not in (None, 'new'):
        _close_untitled_later(win)
    try:
        if what == 'last' and files:
            print("%s: Start - open last %s" % (PLUGIN_NAME, _recent_name(files[0])))
            files[0].trigger()
        elif what == 'open' and op is not None:
            op.trigger()
        elif what not in (None, 'new', 'last', 'open'):
            what.trigger()
    except Exception as e:
        print("%s: Start - couldn't open it (%s)" % (PLUGIN_NAME, e))


def _tab_name(t):
    return (t or "").replace("&", "").replace("\u2022", "").replace("*", "").strip().lower()


def _untitled_tab(win):
    """(tab bar, index, holder) of the empty 'Untitled' tab IngeTrazo starts with, when another model is
    open beside it - else None."""
    from PySide6.QtWidgets import QTabBar, QTabWidget
    for bar in win.findChildren(QTabBar):
        try:
            if _ours(bar) or bar.count() < 2:
                continue
            names = [_tab_name(bar.tabText(i)) for i in range(bar.count())]
            hits = [i for i, n in enumerate(names) if n.startswith("untitled")]
            if len(hits) != 1:
                continue
            i = hits[0]
            if bar.currentIndex() == i:                # the model hasn't opened beside it yet
                continue
            holder = bar.parent() if isinstance(bar.parent(), QTabWidget) else None
            if holder is not None and not _tab_is_empty(holder.widget(i)):
                return None                            # something's been drawn in it: leave it
            return bar, i, holder
        except Exception:
            continue
    return None


def _tab_is_empty(page):
    """True unless the tab's model clearly has something in it (when it can't tell, it's the fresh
    one IngeTrazo started with, so it counts as empty)."""
    if page is None:
        return True
    try:
        from PySide6.QtWidgets import QWidget
        for w in [page] + page.findChildren(QWidget):
            sc = getattr(w, 'scene', None)
            if sc is not None and not callable(sc):
                return not list(getattr(sc, 'groups', []) or [])
    except Exception:
        pass
    return True


def _close_untitled_later(win, tries=0):
    """After the Start window opens your model, closes the empty Untitled tab beside it (checks for up to
    15 seconds while the model loads)."""
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QTabBar, QApplication
    if QApplication.activeModalWidget() is not None and tries < 60:      # an Open window is still up
        QTimer.singleShot(500, lambda: _close_untitled_later(win, tries + 1))
        return
    found = _untitled_tab(win)
    if found is None:
        if tries < 30:
            QTimer.singleShot(500, lambda: _close_untitled_later(win, tries + 1))
        return
    bar, i, holder = found
    print("%s: Start - closing the empty Untitled tab" % PLUGIN_NAME)
    QTimer.singleShot(150, lambda: _answer_dont_save(0))   # IngeTrazo asks 'Save changes?': answer Don't Save
    try:
        btn = bar.tabButton(i, QTabBar.RightSide) or bar.tabButton(i, QTabBar.LeftSide)
        if btn is not None:
            btn.click()                                  # just as if you'd clicked its little x
        elif holder is not None:
            holder.tabCloseRequested.emit(i)
        else:
            bar.tabCloseRequested.emit(i)
    except Exception as e:
        print("%s: Start - couldn't close the Untitled tab (%s)" % (PLUGIN_NAME, e))


def _answer_dont_save(tries):
    """Just after the empty Untitled tab is closed: if IngeTrazo asks whether to save it, clicks Don't Save
    (only that one question, and only for about 3 seconds after the tab is closed)."""
    import re
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QMessageBox, QAbstractButton, QLabel
    dlg = QApplication.activeModalWidget()
    if dlg is None:
        if tries < 20:
            QTimer.singleShot(150, lambda: _answer_dont_save(tries + 1))
        return
    try:
        words = [dlg.windowTitle()] + [lb.text() for lb in dlg.findChildren(QLabel)]
        if isinstance(dlg, QMessageBox):
            words.append(dlg.text())
        if not re.search(r"save|unsaved|changes", " ".join(words), re.I):
            return                                     # some other question: leave it alone
        pick = None
        if isinstance(dlg, QMessageBox):
            for sb in (QMessageBox.Discard, QMessageBox.No):
                pick = dlg.button(sb)
                if pick is not None:
                    break
        if pick is None:
            for b in dlg.findChildren(QAbstractButton):
                if re.search(r"don.?t\s*save|discard|close without|^\s*no\s*$", b.text().replace("&", ""), re.I):
                    pick = b
                    break
        if pick is not None:
            print("%s: Start - answered Don't Save for the empty Untitled tab" % PLUGIN_NAME)
            pick.click()
    except Exception as e:
        print("%s: Start - couldn't answer the Save question (%s)" % (PLUGIN_NAME, e))


def _start_popup_when_ready(win, tries=0):
    """Waits until IngeTrazo's window is up (and nothing else is asking something) before the Start window."""
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    if not start_popup_on() or getattr(win, '_eddy_start_shown', False):
        return
    busy = QApplication.activeModalWidget() is not None
    if (not win.isVisible() or busy) and tries < 40:
        QTimer.singleShot(500, lambda: _start_popup_when_ready(win, tries + 1))
        return
    if win.isVisible():
        start_popup(win)


def style_workflow(tb):
    """Ticks on the steps you've done, and the next step lit up."""
    done = wf_done(tb._bar_id)
    steps = [a for a in tb.actions() if hasattr(a, '_step')]
    nxt = next((a._step for a in steps if a._step not in done), None)
    for a in steps:
        is_done = a._step in done
        a.setText(("\u2713 " if is_done else "") + a._label)
        a.setToolTip(a._tip + ("   - done" if is_done else ("   - next" if a._step == nxt else "")))
        w = tb.widgetForAction(a)
        if w is not None:
            w.setStyleSheet(NEXT_CSS if a._step == nxt else (DONE_CSS if is_done else ""))


def step_clicked(tb, win, name, shortcut, k):
    run_plugin(win, name, shortcut)
    done = wf_done(tb._bar_id)
    done.add(k)
    wf_set_done(tb._bar_id, done)
    style_workflow(tb)


def reset_workflow(tb):
    wf_set_done(tb._bar_id, set())
    style_workflow(tb)


def skip_step(tb):
    done = wf_done(tb._bar_id)
    steps = [a._step for a in tb.actions() if hasattr(a, '_step')]
    nxt = next((k for k in steps if k not in done), None)
    if nxt is not None:
        done.add(nxt)
        wf_set_done(tb._bar_id, done)
        style_workflow(tb)


def _make_bar(win, bar):
    from PySide6.QtWidgets import QToolBar
    from PySide6.QtCore import Qt, QSize
    tb = QToolBar(bar['name'] if bar['id'] == MAIN_ID else "3D Plugins - " + bar['name'], win)
    tb.setObjectName(bar_object_name(bar['id']))
    tb._bar_id = bar['id']
    tb._workflow = bool(bar.get('workflow'))
    tb._bar_name = bar['name']
    tb.setIconSize(QSize(28, 28))
    tb.setToolButtonStyle(Qt.ToolButtonTextUnderIcon if (tb._workflow or load_settings().get('labels', True))
                          else Qt.ToolButtonIconOnly)
    win.addToolBar(Qt.TopToolBarArea, tb)
    tb.setContextMenuPolicy(Qt.CustomContextMenu)
    tb.customContextMenuRequested.connect(lambda pos, tb=tb: choose_buttons(tb, tb.mapToGlobal(pos)))

    def vis_changed(on, bid=bar['id']):
        if getattr(tb, '_quiet', False):
            return
        bars = current_bars()
        for b in bars:
            if b['id'] == bid:
                b['visible'] = bool(on)
        save_bars(bars)
        if bid == MAIN_ID:
            s = load_settings()
            s['visible'] = bool(on)
            save_settings(s)
    tb.visibilityChanged.connect(vis_changed)
    return tb


def sync_toolbars(win=None):
    """Makes the window's toolbars match the saved layout: new ones made, gone ones taken away,
    every one's buttons and name brought up to date."""
    win = win or _main_window()
    if win is None:
        return None
    bars = current_bars()
    have = dict(all_toolbars(win))
    want = {b['id'] for b in bars}
    for bid, tb in have.items():
        if bid not in want:
            tb._quiet = True
            win.removeToolBar(tb)
            tb.deleteLater()
    main = None
    broke = False
    for b in bars:
        tb = have.get(b['id'])
        if tb is None:
            if b['id'] != MAIN_ID and not broke:
                # new small toolbars start on a row of their own (not squeezed beside the others);
                # drag them by their handles to wherever you like
                try:
                    from PySide6.QtCore import Qt
                    win.addToolBarBreak(Qt.TopToolBarArea)
                except Exception:
                    pass
                broke = True
            tb = _make_bar(win, b)
        tb.setWindowTitle(b['name'] if b['id'] == MAIN_ID else "3D Plugins - " + b['name'])
        tb._workflow = bool(b.get('workflow'))
        tb._bar_name = b['name']
        build_buttons(tb, win, b['items'])
        tb._quiet = True
        tb.setVisible(bool(b.get('visible', True)) and bool(b['items']))
        tb._quiet = False
        if b['id'] == MAIN_ID:
            main = tb
    for _bid, tb in all_toolbars(win):
        refresh_buttons(tb)
    return main


def arrange_buttons(tb=None):
    """Arrange toolbars: every toolbar with its buttons in one list. Move buttons up and down
    (and from one toolbar to the next), tick the ones to show, add dividers, make new small
    toolbars, rename or delete them - or pick the ready-made layout."""
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
                                   QPushButton, QLabel, QDialogButtonBox, QComboBox, QInputDialog,
                                   QLineEdit, QMessageBox)
    from PySide6.QtCore import Qt
    win = (tb.parent() if tb is not None else None) or _main_window()
    dlg = QDialog(win)
    dlg.setObjectName(TOOLBAR_NAME + "_arrange")
    dlg.setWindowTitle("Arrange the 3D Plugins toolbars  (version %s)" % VERSION)
    lay = QVBoxLayout(dlg)
    note = QLabel("Every toolbar and its buttons. Pick a button and move it up or down - past the top or "
                  "bottom of a toolbar it goes onto the next one - or send it straight to another toolbar. "
                  "Tick the buttons you want to see. Each toolbar can be dragged anywhere on the window by "
                  "its handle.\n\nWorkflow toolbars are steps to work through in order: copy any buttons "
                  "onto one (the same plugin as often as you like), put them in order and give each step a "
                  "note. On the toolbar the next step is lit up and each gets a tick when it's done.")
    note.setWordWrap(True)
    lay.addWidget(note)
    row = QHBoxLayout()
    tree = QTreeWidget()
    tree.setHeaderHidden(True)
    tree.setMinimumSize(340, 420)
    try:
        from PySide6.QtCore import QSize
        tree.setIconSize(QSize(22, 22))
    except Exception:
        pass
    row.addWidget(tree, 1)
    col = QVBoxLayout()
    b_up, b_down = QPushButton("Move up"), QPushButton("Move down")
    cb_to = QComboBox()
    b_to = QPushButton("Move to toolbar")
    b_div, b_rem = QPushButton("Add divider"), QPushButton("Remove divider")
    b_new, b_ren, b_del = QPushButton("New toolbar..."), QPushButton("Rename toolbar..."), QPushButton("Delete toolbar")
    b_bar_up, b_bar_down = QPushButton("Toolbar up"), QPushButton("Toolbar down")
    b_one, b_grp = QPushButton("All on one toolbar"), QPushButton("A toolbar for each kind")
    b_copy = QPushButton("Copy to toolbar")
    b_note = QPushButton("Step note...")
    b_wf = QPushButton("New workflow toolbar...")
    b_rem.setText("Remove divider / step")
    b_ready = [QPushButton("Workflow: " + nm) for nm in WORKFLOWS]
    for w in [b_up, b_down, QLabel(""), cb_to, b_to, b_copy, QLabel(""), b_div, b_rem, b_note, QLabel(""), b_new,
              b_wf, b_ren, b_del, b_bar_up, b_bar_down, QLabel("Ready-made:"), b_one, b_grp] + b_ready:
        col.addWidget(w)
    col.addStretch(1)
    row.addLayout(col)
    lay.addLayout(row)
    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    lay.addWidget(bb)
    info = {p[0]: p for p in PLUGINS}
    ROLE = Qt.UserRole

    def bar_title(bid, name, wf):
        return name + ("   (main toolbar)" if bid == MAIN_ID else ("   (workflow - steps in order)" if wf else ""))

    def bar_item(bar):
        wf = bool(bar.get('workflow'))
        top = QTreeWidgetItem([bar_title(bar['id'], bar['name'], wf)])
        top.setData(0, ROLE, ('bar', bar['id'], bar['name'], wf))
        f = top.font(0)
        f.setBold(True)
        top.setFont(0, f)
        top.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return top

    def is_wf(top):
        return top is not None and bool(top.data(0, ROLE)[3])

    def button_item(entry, shown=True, wf=False):
        if entry == DIVIDER:
            it = QTreeWidgetItem(["-----------  divider  -----------"])
            it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        elif wf:
            nm, _note = split_step(entry)
            it = QTreeWidgetItem([nm])
            it.setIcon(0, make_icon(info[nm][3]))
            it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)      # steps always show: no tick
        else:
            it = QTreeWidgetItem([entry])
            it.setIcon(0, item_icon(entry))
            it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            it.setCheckState(0, Qt.Checked if shown else Qt.Unchecked)
        it.setData(0, ROLE, ('item', entry))
        return it

    def renumber():
        """Workflow steps: '1. 3D Floor Plan - note'."""
        for i in range(tree.topLevelItemCount()):
            top = tree.topLevelItem(i)
            if not is_wf(top):
                continue
            n = 0
            for j in range(top.childCount()):
                it = top.child(j)
                e = it.data(0, ROLE)[1]
                if e == DIVIDER:
                    continue
                n += 1
                nm, note = split_step(e)
                it.setText(0, "%d.  %s%s" % (n, nm, ("   - " + note) if note else ""))

    def as_item(it, wf):
        """The same button for a toolbar of the other sort (a step keeps its note on a workflow)."""
        e = it.data(0, ROLE)[1]
        if e == DIVIDER:
            return button_item(DIVIDER)
        nm, note = split_step(e)
        return button_item(join_step(nm, note) if wf else nm, True, wf)

    def fill(bars, hidden, keep_workflows=False):
        keep = []
        if keep_workflows:
            keep = [b for b in read_tree()[0] if b.get('workflow')]
        tree.clear()
        for b in list(bars) + keep:
            top = bar_item(b)
            tree.addTopLevelItem(top)
            wf = bool(b.get('workflow'))
            for e in b['items']:
                top.addChild(button_item(e, split_step(e)[0] not in hidden, wf))
            top.setExpanded(True)
        renumber()
        fill_targets()

    def read_tree():
        bars_, hidden_ = [], []
        for i in range(tree.topLevelItemCount()):
            top = tree.topLevelItem(i)
            _k, bid, name, wf = top.data(0, ROLE)
            items = []
            for j in range(top.childCount()):
                it = top.child(j)
                e = it.data(0, ROLE)[1]
                if e == DIVIDER and (not items or items[-1] == DIVIDER):
                    continue                     # two dividers together count as one
                items.append(e)
                if not wf and e != DIVIDER and it.checkState(0) != Qt.Checked:
                    hidden_.append(e)
            while items and items[-1] == DIVIDER:
                items.pop()
            bars_.append({'id': bid, 'name': name, 'items': items, 'workflow': bool(wf)})
        return bars_, hidden_

    def fill_targets():
        cb_to.clear()
        for i in range(tree.topLevelItemCount()):
            d = tree.topLevelItem(i).data(0, ROLE)
            cb_to.addItem(d[2], i)

    def picked():
        it = tree.currentItem()
        if it is None:
            return None, None, None
        par = it.parent()
        if par is None:
            return it, None, None
        return it, par, par.indexOfChild(it)

    def move(d):
        it, par, i = picked()
        if par is None:
            return
        n = tree.indexOfTopLevelItem(par)
        if 0 <= i + d < par.childCount():
            par.takeChild(i)
            par.insertChild(i + d, it)
        elif d < 0 and n > 0 and is_wf(tree.topLevelItem(n - 1)) == is_wf(par):
            par.takeChild(i)                       # off the top: onto the end of the toolbar before
            tree.topLevelItem(n - 1).addChild(it)
        elif d > 0 and n < tree.topLevelItemCount() - 1 and is_wf(tree.topLevelItem(n + 1)) == is_wf(par):
            par.takeChild(i)                       # off the bottom: onto the start of the next
            tree.topLevelItem(n + 1).insertChild(0, it)
        else:
            return                                 # (onto or off a workflow: use Copy to toolbar)
        tree.setCurrentItem(it)
        renumber()

    def move_to():
        it, par, i = picked()
        n = cb_to.currentData()
        if par is None or n is None:
            return
        dest = tree.topLevelItem(int(n))
        if dest is par:
            return
        if is_wf(dest) and not is_wf(par):
            return copy_to()                       # onto a workflow, a button is copied, not moved
        if is_wf(par) and not is_wf(dest):
            QMessageBox.information(dlg, PLUGIN_NAME, "That plugin is on your ordinary toolbars already. To "
                                    "take a step off the workflow, use 'Remove divider / step'.")
            return
        new = as_item(it, is_wf(dest))
        par.takeChild(i)
        dest.addChild(new)
        dest.setExpanded(True)
        tree.setCurrentItem(new)
        renumber()

    def copy_to():
        it, par, i = picked()
        n = cb_to.currentData()
        if par is None or n is None:
            return
        dest = tree.topLevelItem(int(n))
        if not is_wf(dest):
            QMessageBox.information(dlg, PLUGIN_NAME, "Copies go on workflow toolbars - pick one in the list "
                                    "above (or make one with 'New workflow toolbar...'). On your ordinary "
                                    "toolbars each button is only once: use 'Move to toolbar'.")
            return
        if it.data(0, ROLE)[1] == DIVIDER:
            return
        if it.data(0, ROLE)[1] in SPECIAL:
            QMessageBox.information(dlg, PLUGIN_NAME, "Simple view and Make... can be moved to any ordinary "
                                    "toolbar, but they aren't steps, so they don't go on workflows.")
            return
        new = as_item(it, True)
        if dest is par:
            par.insertChild(i + 1, new)            # the same step again, just after it
        else:
            dest.addChild(new)
        dest.setExpanded(True)
        tree.setCurrentItem(new)
        renumber()

    def step_note():
        it, par, i = picked()
        if par is None or not is_wf(par) or it.data(0, ROLE)[1] == DIVIDER:
            QMessageBox.information(dlg, PLUGIN_NAME, "Pick a step on a workflow toolbar first.")
            return
        nm, note = split_step(it.data(0, ROLE)[1])
        normal = QLineEdit.EchoMode.Normal if hasattr(QLineEdit, 'EchoMode') else QLineEdit.Normal
        res = QInputDialog.getText(dlg, "Step note", "What this step is for (shown on its button, e.g. "
                                   "'Front windows'). Empty = the plugin's own name:", normal, note)
        new, ok = (res[0], res[1]) if isinstance(res, (tuple, list)) else (res, bool(res))
        if ok:
            it.setData(0, ROLE, ('item', join_step(nm, new)))
            renumber()

    def ready_workflow(name):
        ids = [tree.topLevelItem(i).data(0, ROLE)[1] for i in range(tree.topLevelItemCount())]
        bar = {'id': _new_id([{'id': x} for x in ids]), 'name': name, 'workflow': True,
               'items': [join_step(p, nt) for p, nt in WORKFLOWS[name] if p in info]}
        top = bar_item(bar)
        tree.addTopLevelItem(top)
        for e in bar['items']:
            top.addChild(button_item(e, True, True))
        top.setExpanded(True)
        tree.setCurrentItem(top)
        renumber()
        fill_targets()

    def add_div():
        it, par, i = picked()
        if par is None and it is not None:          # a toolbar picked: divider at its end
            it.addChild(button_item(DIVIDER))
            return
        if par is not None:
            d = button_item(DIVIDER)
            par.insertChild(i + 1, d)
            tree.setCurrentItem(d)

    def rem_div():
        it, par, i = picked()
        if par is not None and (it.data(0, ROLE)[1] == DIVIDER or is_wf(par)):
            par.takeChild(i)
            renumber()

    def new_bar(workflow=False):
        normal = QLineEdit.EchoMode.Normal if hasattr(QLineEdit, 'EchoMode') else QLineEdit.Normal
        if workflow:
            res = QInputDialog.getText(dlg, "New workflow toolbar", "A name for the workflow (e.g. Make a "
                                       "signal box). Then copy buttons onto it in the order you'll use "
                                       "them:", normal, "")
        else:
            res = QInputDialog.getText(dlg, "New toolbar", "A name for the new toolbar (e.g. Walls):", normal, "")
        name, ok = (res[0], res[1]) if isinstance(res, (tuple, list)) else (res, bool(res))
        name = (name or "").strip()
        if not ok or not name:
            return
        ids = [tree.topLevelItem(i).data(0, ROLE)[1] for i in range(tree.topLevelItemCount())]
        top = bar_item({'id': _new_id([{'id': x} for x in ids]), 'name': name, 'workflow': workflow})
        tree.addTopLevelItem(top)
        top.setExpanded(True)
        tree.setCurrentItem(top)
        fill_targets()
        cb_to.setCurrentIndex(cb_to.count() - 1)

    def ren_bar():
        it, par, _i = picked()
        top = par or it
        if top is None:
            return
        kind, bid, name, wf = top.data(0, ROLE)
        normal = QLineEdit.EchoMode.Normal if hasattr(QLineEdit, 'EchoMode') else QLineEdit.Normal
        res = QInputDialog.getText(dlg, "Rename toolbar", "New name:", normal, name)
        new, ok = (res[0], res[1]) if isinstance(res, (tuple, list)) else (res, bool(res))
        new = (new or "").strip()
        if ok and new:
            top.setData(0, ROLE, (kind, bid, new, wf))
            top.setText(0, bar_title(bid, new, wf))
            fill_targets()

    def del_bar():
        it, par, _i = picked()
        top = par or it
        if top is None:
            return
        if top.data(0, ROLE)[1] == MAIN_ID:
            QMessageBox.information(dlg, PLUGIN_NAME, "The main toolbar stays - its buttons can be moved to "
                                                      "other toolbars, or hidden.")
            return
        main = tree.topLevelItem(0)
        while top.childCount():
            ch = top.takeChild(0)
            if not is_wf(top):
                main.addChild(ch)                 # its buttons go back to the main toolbar
            # (a workflow's steps are copies: they just go)
        tree.takeTopLevelItem(tree.indexOfTopLevelItem(top))
        fill_targets()

    def move_bar(d):
        it, par, _i = picked()
        top = par or it
        if top is None:
            return
        n = tree.indexOfTopLevelItem(top)
        if n == 0 or not (1 <= n + d < tree.topLevelItemCount()):
            return                                  # the main toolbar stays first
        exp = top.isExpanded()
        tree.takeTopLevelItem(n)
        tree.insertTopLevelItem(n + d, top)
        top.setExpanded(exp)
        tree.setCurrentItem(top)
        fill_targets()

    fill(current_bars(), set(load_settings().get('hidden') or []))
    b_up.clicked.connect(lambda: move(-1))
    b_down.clicked.connect(lambda: move(1))
    b_to.clicked.connect(move_to)
    b_copy.clicked.connect(copy_to)
    b_note.clicked.connect(step_note)
    b_wf.clicked.connect(lambda: new_bar(True))
    for b_, nm_ in zip(b_ready, WORKFLOWS):
        b_.clicked.connect(lambda checked=False, nm_=nm_: ready_workflow(nm_))
    b_div.clicked.connect(add_div)
    b_rem.clicked.connect(rem_div)
    b_new.clicked.connect(lambda: new_bar(False))
    b_ren.clicked.connect(ren_bar)
    b_del.clicked.connect(del_bar)
    b_bar_up.clicked.connect(lambda: move_bar(-1))
    b_bar_down.clicked.connect(lambda: move_bar(1))
    b_one.clicked.connect(lambda: fill([{'id': MAIN_ID, 'name': "3D Plugins", 'visible': True,
                                         'items': [SIMPLE_ITEM, MAKE_ITEM, DIVIDER] + [p[0] for p in PLUGINS]}],
                                       set(), keep_workflows=True))
    b_grp.clicked.connect(lambda: fill(grouped_bars(), set(), keep_workflows=True))
    bb.accepted.connect(dlg.accept)
    bb.rejected.connect(dlg.reject)
    eddy_window(dlg, PLUGIN_NAME + ' - arrange', EDDY_TIPS, place=True)  # eddy-window
    if dlg.exec() != QDialog.Accepted:
        return
    old = {b['id']: b for b in current_bars()}
    bars, hidden = read_tree()
    for b in bars:
        b['visible'] = old.get(b['id'], {}).get('visible', True)
        if b['workflow'] and old.get(b['id'], {}).get('items') != b['items']:
            wf_set_done(b['id'], set())          # the steps changed: start the workflow again
    if bars[0]['id'] != MAIN_ID:                 # (the main one can't be moved, but be sure)
        bars.sort(key=lambda b: b['id'] != MAIN_ID)
    save_bars(bars)
    s = load_settings()
    s['hidden'] = hidden
    save_settings(s)
    sync_toolbars(win)


def install_toolbar(win=None):
    """Puts up the main toolbar and any small ones you've made (once). Returns the main one."""
    win = win or _main_window()
    if win is None:
        return None
    tb = find_toolbar(win)
    if tb is not None:
        return tb
    st = load_settings()
    if st.get('version') != 2:
        # buttons hidden by the old bug (a click unticked them) all come back once
        st['hidden'] = []
        st['version'] = 2
        save_settings(st)
    tb = sync_toolbars(win)
    # where you left the toolbars: put back, and kept when IngeTrazo closes
    from PySide6.QtCore import QTimer
    QTimer.singleShot(0, lambda: restore_places(win))
    try:
        from PySide6.QtWidgets import QApplication
        if not getattr(win, '_eddy_bars_hooked', False):
            QApplication.instance().aboutToQuit.connect(lambda: keep_places(win))
            win._eddy_bars_hooked = True
    except Exception:
        pass
    # the other plugins may still be loading: check which ones are there a little later
    QTimer.singleShot(3000, lambda: [refresh_buttons(t) for _b, t in all_toolbars(win)])
    # Simple view left on last time: hide IngeTrazo's toolbars again once it has put them up
    try:
        _hook_close(win)
    except Exception:
        pass
    try:
        _hook_steps(win)                    # step toolbar when a plugin opens
        QTimer.singleShot(200, lambda: show_project(win))   # the job you were on, where you'd got to
        QTimer.singleShot(0, lambda: (_steps_bar(win, make=False) is not None
                                      and _STEPS['dlg'] is None and _steps_bar(win, make=False).setVisible(False)))
    except Exception as e:
        print("%s: step toolbar not set up (%s)" % (PLUGIN_NAME, e))
    if simple_view_on():
        for ms in (1500, 4000):
            QTimer.singleShot(ms, lambda: simple_view_on() and set_simple_view(True, win))
    if start_popup_on():
        QTimer.singleShot(2500, lambda: _start_popup_when_ready(win))   # after the plugins have loaded
    return tb


def keep_places(win):
    """Notes where every toolbar is (IngeTrazo puts its own back; these come after it)."""
    try:
        s = load_settings()
        s['places'] = bytes(win.saveState(7).toHex()).decode('ascii')
        save_settings(s)
    except Exception:
        pass


def restore_places(win):
    """Puts the toolbars back where they were left - only when there are small toolbars of
    your own (one toolbar needs nothing: IngeTrazo looks after it)."""
    try:
        if len(current_bars()) < 2:
            return
        hx = load_settings().get('places')
        if hx:
            from PySide6.QtCore import QByteArray
            win.restoreState(QByteArray.fromHex(hx.encode('ascii')), 7)
            for b in current_bars():          # restoring must not show a toolbar you've hidden
                for bid, t in all_toolbars(win):
                    if bid == b['id']:
                        t._quiet = True
                        t.setVisible(bool(b.get('visible', True)) and bool(b['items']))
                        t._quiet = False
    except Exception:
        pass


def set_all_visible(on, win=None):
    bars = current_bars()
    for b in bars:
        b['visible'] = bool(on)
    save_bars(bars)
    for _bid, t in all_toolbars(win):
        t._quiet = True
        t.setVisible(bool(on) and bool(t.actions()))
        t._quiet = False


def choose_buttons(tb, where=None):
    """Right-click on a toolbar: tick its buttons, labels on/off, arrange all the toolbars."""
    from PySide6.QtWidgets import QMenu
    from PySide6.QtGui import QCursor
    from PySide6.QtCore import Qt, QTimer
    menu = QMenu(tb)
    menu.setObjectName(TOOLBAR_NAME + "_menu")
    wf = getattr(tb, '_workflow', False)
    if wf:
        menu.addSection("Workflow: " + getattr(tb, '_bar_name', ''))
        again = menu.addAction("Start again (clear the ticks)")
        again.triggered.connect(lambda: reset_workflow(tb))
        skip = menu.addAction("Skip the next step (tick it)")
        skip.triggered.connect(lambda: skip_step(tb))
    else:
        menu.addSection("Buttons on this toolbar")
    for act in ([] if wf else tb.actions()):
        info = getattr(act, '_plugin', None)
        if not info or getattr(act, '_missing', False):
            continue
        item = menu.addAction(act.icon(), info[0])
        item.setCheckable(True)
        item.setChecked(act.isVisible())

        def toggled(on, act=act, name=info[0]):
            act.setVisible(on)
            s = load_settings()
            hid = set(s.get('hidden') or [])
            if on:
                hid.discard(name)
            else:
                hid.add(name)
            s['hidden'] = sorted(hid)
            save_settings(s)
        item.toggled.connect(toggled)
    menu.addSeparator()
    show_all = menu.addAction("Show all buttons")
    labels = menu.addAction("Show labels under the icons")
    labels.setCheckable(True)
    labels.setChecked(tb.toolButtonStyle() != Qt.ToolButtonIconOnly)

    def all_on():
        s = load_settings()
        s['hidden'] = []
        save_settings(s)
        for _b, t in all_toolbars(tb.parent()):
            for act in t.actions():
                if getattr(act, '_plugin', None):
                    act.setVisible(not getattr(act, '_missing', False))

    def set_labels(on):
        for _b, t in all_toolbars(tb.parent()):
            if not getattr(t, '_workflow', False):     # workflow steps always show their numbers
                t.setToolButtonStyle(Qt.ToolButtonTextUnderIcon if on else Qt.ToolButtonIconOnly)
        s = load_settings()
        s['labels'] = bool(on)
        save_settings(s)
    show_all.triggered.connect(all_on)
    labels.toggled.connect(set_labels)
    menu.addSeparator()
    arrange = menu.addAction("Arrange toolbars... (move buttons, small toolbars, workflows)")
    arrange.triggered.connect(lambda: QTimer.singleShot(0, lambda: arrange_buttons(tb)))
    menu.addSeparator()
    simple = menu.addAction("Simple view (hide IngeTrazo's other toolbars)")
    simple.setCheckable(True)
    simple.setChecked(simple_view_on())
    simple.toggled.connect(lambda on: set_simple_view(on, tb.parent()))
    steps = menu.addAction("Step toolbar when a plugin opens (its pages, 1, 2, 3...)")
    steps.setCheckable(True)
    steps.setChecked(steps_on())
    steps.toggled.connect(lambda on: set_steps_on(on, tb.parent()))
    startw = menu.addAction("Start window when IngeTrazo opens (open last, open, new)")
    startw.setCheckable(True)
    startw.setChecked(start_popup_on())
    startw.toggled.connect(set_start_popup)
    menu.addSeparator()
    hide = menu.addAction("Hide this toolbar")
    hide.triggered.connect(lambda: tb.setVisible(False))
    hide_all = menu.addAction("Hide all the 3D Plugins toolbars (Ctrl+Alt+B brings them back)")
    hide_all.triggered.connect(lambda: set_all_visible(False, tb.parent()))
    menu.exec(where or QCursor.pos())
    menu.deleteLater()            # don't leave it lying about once it's closed


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
        _hook_steps(win)                    # (does nothing if it's already set up)
    except Exception as e:
        print("%s: could not add the toolbar (%s). Press Ctrl+Alt+B to try again." % (PLUGIN_NAME, e))


# --- Extensions menu (begin) ---
# ---------------------------------------------------------------------------
# Extensions menu: all of Eddy's plugins together under "3D Plugins by Eddy"
# ---------------------------------------------------------------------------
EDDY_MENU_TITLE = "3D Plugins by Eddy"
EDDY_STEMS = ("period_windows", "brick_block_studio", "gutters_downpipes", "soil_waste_pipes",
              "loft", "print_scaler", "part_splitter", "scale_converter", "roof_tiles", "notepad", "quick_links", "wood_planking",
              "period_doors", "fences_gates", "wrap", "chimneys", "corrugated_iron",
              "station_canopies", "centre_finder", "timeline", "find_replace", "place_along",
              "pieces_in", "blend", "subframe", "floor_plan", "openings", "plugins_toolbar",
              "update_checker", "realistic_wall")
EDDY_EXTRA_NAMES = ()


def _eddy_menu_key(a):
    return _clean(a.text()).replace("3d ", "", 1)


def _eddy_leaf_actions(sub):
    """Every plugin entry in the submenu, including those already in its kind sub-menus."""
    out = []
    kinds = set(id(m) for m in (getattr(sub, '_eddy_kinds', None) or {}).values())
    for a in sub.actions():
        if a.isSeparator():
            continue
        m = a.menu()
        if m is not None and id(m) in kinds:
            out += [x for x in m.actions() if not x.isSeparator()]
        elif m is None:
            out.append(a)
    return out


def _fill_eddy_groups(sub, acts):
    """'3D Plugins by Eddy' > Walls, Roofs, Doors & windows ... each with its plugins in A-Z order;
    a plugin not in any kind goes under 'More'."""
    from PySide6.QtWidgets import QMenu
    kinds = getattr(sub, '_eddy_kinds', None)
    if kinds is None:
        kinds = sub._eddy_kinds = {}
    for a in list(sub.actions()):
        sub.removeAction(a)
    by = {}
    for title, names in GROUPS:
        for n in names:
            by[_clean(n)] = title
    sorted_in = {}
    for a in acts:
        sorted_in.setdefault(by.get(_clean(a.text()), "More"), []).append(a)
    for title in [g[0] for g in GROUPS] + ["More"]:
        lst = sorted_in.get(title)
        if not lst:
            continue
        m = kinds.get(title)
        if m is None:
            m = kinds[title] = QMenu(title, sub)
            m.setObjectName("EddyPluginsMenu_" + title)
            m.setToolTipsVisible(True)
        for x in list(m.actions()):
            m.removeAction(x)
        for a in sorted(lst, key=_eddy_menu_key):
            m.addAction(a)
            try:
                if a.statusTip():
                    a.setToolTip(a.statusTip())     # the pop-up note says what the plugin does
            except Exception:
                pass
        sub.addMenu(m)


def group_eddy_menu(win=None):
    """Moves every one of the 3D plugins' entries in the Extensions menu into one
    submenu, '3D Plugins by Eddy'. Safe to run again: it only moves new entries."""
    from PySide6.QtWidgets import QMenu
    win = win or _main_window()
    if win is None:
        return 0
    menu = getattr(win, "_ext_menu", None)
    if menu is None:
        try:
            for a in win.menuBar().actions():
                if a.menu() is not None and _clean(a.text()) == "extensions":
                    menu = a.menu()
                    break
        except Exception:
            menu = None
    if menu is None:
        return 0
    names = {_clean(n) for n in [p[0] for p in PLUGINS] + [PLUGIN_NAME] + list(EDDY_EXTRA_NAMES)}
    owners = win.__dict__.get("_ext_action_owner", {}) or {}
    sub = None
    for a in menu.actions():
        if a.menu() is not None and _clean(a.text()) == _clean(EDDY_MENU_TITLE):
            sub = a.menu()
            break
    found = []

    def scan(m, depth):
        for a in list(m.actions()):
            if a.menu() is not None:
                if a.menu() is not sub and depth < 3:
                    scan(a.menu(), depth + 1)
                continue
            if a.isSeparator():
                continue
            stem = owners.get(a)
            if _clean(a.text()) in names or (stem is not None and (
                    stem in EDDY_STEMS or str(stem).lower().startswith("ed3d_") or str(stem) == "3D_Eddys")):
                found.append((m, a))
    scan(menu, 0)
    if not found:
        return 0
    if sub is None:
        sub = QMenu(EDDY_MENU_TITLE, menu)
        sub.setObjectName("EddyPluginsMenu")
        sub.setToolTipsVisible(True)
        first = None
        for m, a in found:
            if m is menu:
                first = a
                break
        if first is None:
            first = getattr(win, "_ext_anchor", None)
        if first is not None:
            menu.insertMenu(first, sub)
        else:
            menu.addMenu(sub)
    left = set()
    for m, a in found:
        m.removeAction(a)
        if m is not menu:
            left.add(m)
    # tidy: the plugins sorted into sub-menus by kind (Walls, Roofs, Doors & windows ...)
    acts = _eddy_leaf_actions(sub) + [a for _, a in found]
    seen, uniq = set(), []
    for a in acts:
        if id(a) not in seen:
            seen.add(id(a))
            uniq.append(a)
    _fill_eddy_groups(sub, uniq)
    # a category submenu that's now empty is hidden
    for m in left:
        try:
            if not [a for a in m.actions() if not a.isSeparator()]:
                m.menuAction().setVisible(False)
        except Exception:
            pass
    if not getattr(menu, "_eddy_hooked", False):
        try:
            menu.aboutToShow.connect(lambda: group_eddy_menu(win))
            menu._eddy_hooked = True
        except Exception:
            pass
    return len(found)


def _group_menu_when_ready(tries=0):
    """The plugins' menu entries are added a moment after the window opens: keep
    looking for a while, then the menu tidies itself each time it's opened."""
    try:
        from PySide6.QtCore import QTimer
        win = _main_window()
        if win is not None and win.isVisible():
            group_eddy_menu(win)
        if tries < 40:
            QTimer.singleShot(1500, lambda: _group_menu_when_ready(tries + 1))
    except Exception as e:
        print("%s: could not tidy the Extensions menu (%s)." % (PLUGIN_NAME, e))
# --- Extensions menu (end) ---


try:
    _install_when_ready()
except Exception:
    pass
try:  # eddy-window
    _group_menu_when_ready()  # eddy-window
except Exception:  # eddy-window
    pass  # eddy-window


# ---------------------------------------------------------------------------
# Tool: Ctrl+Alt+B shows or hides the toolbar
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

EDDY_TIPS = {'OK': 'Keeps the new layout of the toolbars.',
 'Move to toolbar': 'Sends the picked button to the toolbar chosen above.',
 'New toolbar...': 'Makes a new small toolbar (Walls, Roofs ...). Then move buttons onto it.',
 'Rename toolbar...': 'Gives the picked toolbar a new name.',
 'Delete toolbar': 'Takes the picked toolbar away; its buttons go back onto the main toolbar.',
 'Toolbar up': 'Moves the picked toolbar up the list.',
 'Toolbar down': 'Moves the picked toolbar down the list.',
 'All on one toolbar': 'Every button on the main toolbar again, in the first order.',
 'A toolbar for each kind': 'Ready-made: a small toolbar each for walls, roofs, doors and windows, pipes, '
                            'railway and outside, shaping tools, scale and print, notes.',
 'Move up': 'Moves the picked button up the list (left along the toolbar).',
 'Move down': 'Moves the picked button down the list (right along the toolbar).',
 'Add divider': 'Puts a divider line on the toolbar after the picked button.',
 'Remove divider': 'Takes away the picked divider.',
 'Copy to toolbar': 'Copies the picked button onto the workflow toolbar chosen above, as a new step. '
                    'The same plugin can be a step as often as you like.',
 'Step note...': 'A note for the picked workflow step, shown on its button (e.g. Front windows).',
 'New workflow toolbar...': 'Makes a workflow toolbar: steps to work through in order. Copy buttons onto it.',
 'Remove divider / step': 'Takes away the picked divider, or the picked step of a workflow.',
 'Workflow: Make a building': 'Ready-made workflow: floor plan, bricks, windows, doors, frame, roof tiles, '
                              'chimneys, gutters, colours, scale and print. Change it as you like.',
 'Workflow: Get it ready to print': 'Ready-made workflow: check the parts, scale and pieces, fit the bed.',
 'Cancel': 'Leaves the buttons as they were.'}
EDDY_TIPS_END = None


class PluginsToolbarTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+B"
    description = ("Shows or hides the 3D Plugins toolbars: a button for each plugin, on one toolbar or on "
                   "small toolbars of your own (right-click a toolbar to arrange them).")

    def on_activate(self, viewport):
        win = None
        try:
            win = viewport.window()
        except Exception:
            pass
        tb = find_toolbar(win) or find_toolbar()
        if tb is None:
            install_toolbar(win)
            set_all_visible(True, win)
            return
        bars = all_toolbars(win)
        on = not any(t.isVisible() for _b, t in bars)
        set_all_visible(on, win)
        if on:
            for _b, t in bars:
                refresh_buttons(t)

    def on_deactivate(self, viewport):
        pass


def run(viewport=None):
    """Console entry point: run() adds the toolbar, or shows it."""
    tb = find_toolbar() or install_toolbar()
    if tb is not None:
        tb.setVisible(True)

