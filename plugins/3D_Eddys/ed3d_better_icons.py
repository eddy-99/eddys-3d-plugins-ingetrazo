# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Better Icons for IngeTrazo
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
3D Better Icons - clearer, colour icons for IngeTrazo's own toolbar buttons
When IngeTrazo opens, this finds its tool buttons (Line, Arc, Tape Measure, Walk...)
by name and gives each a clearer icon, drawn here as SVG so they stay sharp at
any size, including with 'Large toolbar icons' on. Nothing extra to install.
Ctrl+Alt+Y opens its settings: the new icons on or off, the icon size, and names
under the icons (on the new ones, or on every toolbar button) and their text size.
Ctrl+Alt+Q turns the names on or off. The menus keep IngeTrazo's full names.
Removing this file puts IngeTrazo's icons back too.

A list of every toolbar button it found, and which icon each got, is written beside
this file (ed3d_better_icons_buttons.txt), to help match any button it missed.
"""

import os
import re
import json
from tools.base import Tool

PLUGIN_NAME = "3D Better Icons"
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_better_icons.json")
LIST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ed3d_better_icons_buttons.txt")
# Eddy's own toolbars keep their icons
SKIP_TOOLBARS = ("ThreeDPluginsToolbar", "ScaleConverterToolbar")

# ---------------------------------------------------------------------------
# The icons, as SVG on a 32 x 32 grid
# ---------------------------------------------------------------------------
INK = "#2f3640"       # outlines
BLUE = "#2b7bd6"      # points and guide lines
PALE = "#d6e8fb"      # filled shapes
ORANGE = "#ef7d22"    # the point you start from / the thing that moves
YELLOW = "#f4c542"
RED = "#d9443a"
GREEN = "#2f9e55"
GREY = "#8a929b"


def _dot(x, y, c=BLUE, r=2.5):
    return '<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="#ffffff" stroke-width="1"/>' % (x, y, r, c)


def _cube(cx, cy, s, top, left, right):
    a = s * 0.866
    pts = lambda ps: " ".join("%.1f,%.1f" % p for p in ps)
    return ('<g stroke="%s" stroke-width="0.9" stroke-linejoin="round">'
            '<polygon points="%s" fill="%s"/><polygon points="%s" fill="%s"/>'
            '<polygon points="%s" fill="%s"/></g>') % (
        INK,
        pts([(cx, cy - s), (cx + a, cy - s / 2), (cx, cy), (cx - a, cy - s / 2)]), top,
        pts([(cx - a, cy - s / 2), (cx, cy), (cx, cy + s), (cx - a, cy + s / 2)]), left,
        pts([(cx, cy), (cx + a, cy - s / 2), (cx + a, cy + s / 2), (cx, cy + s)]), right)


_A = "M16 3 L27.5 29 L21.5 29 L19.3 23.5 L12.7 23.5 L10.5 29 L4.5 29 Z M14.3 19 L17.7 19 L16 14.2 Z"

ICONS = {
    # --- drawing ---
    "line": '<line x1="6" y1="26" x2="26" y2="6" stroke="%s" stroke-width="2.4" stroke-linecap="round"/>%s%s'
            % (INK, _dot(6, 26, ORANGE), _dot(26, 6)),
    "freehand": '<path d="M4 25 C7 10 12 6 13.5 13 S16 28 20.5 19 S25 6 28.5 6" fill="none" stroke="%s" '
                'stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>%s'
                '<path d="M25.5 3.5 L31 3 L29.5 8.5 Z" fill="%s"/>' % (INK, _dot(4, 25, ORANGE), INK),
    "rect": '<rect x="5" y="8" width="22" height="16" fill="%s" stroke="%s" stroke-width="2" '
            'stroke-linejoin="round"/><line x1="5" y1="24" x2="27" y2="8" stroke="%s" stroke-width="1.2" '
            'stroke-dasharray="2 2"/>%s%s' % (PALE, INK, BLUE, _dot(5, 24, ORANGE), _dot(27, 8)),
    "rot_rect": '<polygon points="3,19 15,9 22,17.5 10,27.5" fill="%s" stroke="%s" stroke-width="2" '
                'stroke-linejoin="round"/><path d="M17 4 A12 12 0 0 1 28 12" fill="none" stroke="%s" '
                'stroke-width="2.2" stroke-linecap="round"/><polygon points="25,11.5 31,11 28.5,16.5" '
                'fill="%s"/>%s' % (PALE, INK, ORANGE, ORANGE, _dot(3, 19, BLUE)),
    "circle": '<circle cx="16" cy="16" r="11.5" fill="%s" stroke="%s" stroke-width="2"/>'
              '<line x1="16" y1="16" x2="27.5" y2="16" stroke="%s" stroke-width="1.6"/>%s%s'
              % (PALE, INK, BLUE, _dot(16, 16, ORANGE), _dot(27.5, 16)),
    "polygon": '<polygon points="28,16 22,5.6 10,5.6 4,16 10,26.4 22,26.4" fill="%s" stroke="%s" '
               'stroke-width="2" stroke-linejoin="round"/><line x1="16" y1="16" x2="28" y2="16" stroke="%s" '
               'stroke-width="1.6"/>%s%s' % (PALE, INK, BLUE, _dot(16, 16, ORANGE), _dot(28, 16)),
    "arc_centre": '<line x1="16" y1="25" x2="4.7" y2="20.9" stroke="%s" stroke-width="1.3" stroke-dasharray="2 1.6"/>'
                  '<line x1="16" y1="25" x2="27.3" y2="20.9" stroke="%s" stroke-width="1.3" '
                  'stroke-dasharray="2 1.6"/><path d="M4.7 20.9 A12 12 0 0 1 27.3 20.9" fill="none" stroke="%s" '
                  'stroke-width="2.4" stroke-linecap="round"/>%s%s%s'
                  % (BLUE, BLUE, INK, _dot(16, 25, ORANGE), _dot(4.7, 20.9), _dot(27.3, 20.9)),
    "arc2": '<line x1="4" y1="25" x2="28" y2="25" stroke="%s" stroke-width="1.2" stroke-dasharray="2 1.6"/>'
            '<path d="M4 25 A12 12 0 0 1 28 25" fill="none" stroke="%s" stroke-width="2.4" '
            'stroke-linecap="round"/><line x1="16" y1="24" x2="16" y2="17" stroke="%s" stroke-width="1.8"/>'
            '<polygon points="16,13 12.8,18 19.2,18" fill="%s"/>%s%s'
            % (GREY, INK, ORANGE, ORANGE, _dot(4, 25, ORANGE), _dot(28, 25)),
    "arc3": '<path d="M4 25 A12 12 0 0 1 28 25" fill="none" stroke="%s" stroke-width="2.4" '
            'stroke-linecap="round"/>%s%s%s' % (INK, _dot(4, 25, ORANGE), _dot(7.5, 16.5), _dot(28, 25)),
    "pie": '<path d="M16 25 L4.7 18.5 A13 13 0 0 1 27.3 18.5 Z" fill="#fbd3a8" stroke="%s" stroke-width="2" '
           'stroke-linejoin="round"/>%s' % (INK, _dot(16, 25, ORANGE)),
    "path": '<polyline points="4,26 11,11 19,21 28,6" fill="none" stroke="%s" stroke-width="2.2" '
            'stroke-linejoin="round" stroke-linecap="round"/>%s%s%s%s'
            % (INK, _dot(4, 26, ORANGE), _dot(11, 11), _dot(19, 21), _dot(28, 6)),
    # --- measuring and notes ---
    "tape": '<rect x="2.5" y="8.5" width="18" height="18" rx="4.5" fill="%s" stroke="%s" stroke-width="1.8"/>'
            '<circle cx="11.5" cy="17.5" r="4.2" fill="#ffffff" stroke="%s" stroke-width="1.5"/>'
            '<rect x="20.5" y="21" width="9.5" height="5" fill="#fff3c4" stroke="%s" stroke-width="1.2"/>'
            '<line x1="23.5" y1="21" x2="23.5" y2="23.5" stroke="%s" stroke-width="1"/>'
            '<line x1="26.5" y1="21" x2="26.5" y2="23.5" stroke="%s" stroke-width="1"/>'
            '<line x1="30" y1="19.5" x2="30" y2="27.5" stroke="%s" stroke-width="1.8"/>'
            % (YELLOW, INK, INK, INK, INK, INK, INK),
    "protractor": '<path d="M2.5 26 A13.5 13.5 0 0 1 29.5 26 Z" fill="%s" stroke="%s" stroke-width="1.8" '
                  'stroke-linejoin="round"/><path d="M11 26 A5 5 0 0 1 21 26 Z" fill="#ffffff" stroke="%s" '
                  'stroke-width="1.2"/><g stroke="%s" stroke-width="1.1"><line x1="5.5" y1="18.8" x2="7.6" '
                  'y2="20"/><line x1="9.2" y1="14.5" x2="10.6" y2="16.4"/><line x1="16" y1="12.5" x2="16" '
                  'y2="15"/><line x1="22.8" y1="14.5" x2="21.4" y2="16.4"/><line x1="26.5" y1="18.8" x2="24.4" '
                  'y2="20"/></g><line x1="16" y1="26" x2="26" y2="7" stroke="%s" stroke-width="2.2" '
                  'stroke-linecap="round"/>%s' % (YELLOW, INK, INK, INK, RED, _dot(16, 26, ORANGE, 2.2)),
    "dimension": '<g stroke="%s" stroke-width="1.4"><line x1="4" y1="9" x2="4" y2="28"/><line x1="28" y1="9" '
                 'x2="28" y2="28"/></g><line x1="8" y1="21" x2="24" y2="21" stroke="%s" stroke-width="1.6"/>'
                 '<polygon points="4.5,21 10,17.8 10,24.2" fill="%s"/><polygon points="27.5,21 22,17.8 22,24.2" '
                 'fill="%s"/><text x="16" y="16" font-family="Arial" font-weight="bold" font-size="10" '
                 'text-anchor="middle" fill="%s">25</text>' % (GREY, INK, INK, INK, BLUE),
    "text": '<rect x="3" y="3.5" width="19" height="15.5" rx="2.5" fill="#ffffff" stroke="%s" stroke-width="1.8"/>'
            '<text x="12.5" y="16" font-family="Arial" font-weight="bold" font-size="13" text-anchor="middle" '
            'fill="%s">T</text><line x1="16" y1="19" x2="26" y2="27" stroke="%s" stroke-width="1.6"/>%s'
            % (INK, BLUE, INK, _dot(27, 28, ORANGE)),
    "text3d": '<path d="%s" fill="#5a6370" transform="translate(2.4,1.8)"/>'
              '<path d="%s" fill="#5a6370" transform="translate(1.6,1.2)"/>'
              '<path d="%s" fill="#5a6370" transform="translate(0.8,0.6)"/>'
              '<path d="%s" fill="%s" fill-rule="evenodd" stroke="%s" stroke-width="0.9" '
              'stroke-linejoin="round" transform="translate(-1,-1)"/>' % (_A, _A, _A, _A, ORANGE, INK),
    # --- camera and views ---
    "camera": '<rect x="10" y="6" width="10" height="6" rx="1.5" fill="#4a5462"/>'
              '<rect x="3" y="10" width="26" height="17" rx="3" fill="#4a5462" stroke="%s" stroke-width="1.2"/>'
              '<circle cx="16" cy="18.5" r="6" fill="#cfe3f7" stroke="#ffffff" stroke-width="1.8"/>'
              '<circle cx="16" cy="18.5" r="2.6" fill="%s"/><rect x="23" y="12.5" width="4" height="2.6" '
              'rx="0.8" fill="%s"/>' % (INK, BLUE, ORANGE),
    "walk": '<g fill="#4a5462"><ellipse cx="9.5" cy="19.5" rx="3.6" ry="5" transform="rotate(-12 9.5 19.5)"/>'
            '<ellipse cx="11" cy="28" rx="2.8" ry="2.5"/><circle cx="6.6" cy="13.2" r="1.25"/>'
            '<circle cx="9" cy="12.2" r="1.25"/><circle cx="11.5" cy="12.6" r="1.15"/></g>'
            '<g fill="%s"><ellipse cx="21.5" cy="10.5" rx="3.6" ry="5" transform="rotate(12 21.5 10.5)"/>'
            '<ellipse cx="20" cy="19" rx="2.8" ry="2.5"/><circle cx="19.6" cy="3.6" r="1.15"/>'
            '<circle cx="22.2" cy="3.2" r="1.25"/><circle cx="24.6" cy="4.4" r="1.25"/></g>' % BLUE,
    "look": '<path d="M2 16 Q16 3 30 16 Q16 29 2 16 Z" fill="#ffffff" stroke="%s" stroke-width="2" '
            'stroke-linejoin="round"/><circle cx="16" cy="16" r="6" fill="%s"/><circle cx="16" cy="16" '
            'r="2.6" fill="%s"/><circle cx="18.2" cy="13.6" r="1.3" fill="#ffffff"/>' % (INK, BLUE, INK),
    "components": _cube(9.5, 21, 6.5, "#9cc6f2", "#4f8fd6", "#2d64a8")
                  + _cube(22.5, 21, 6.5, "#9fdcb3", "#45a868", "#2c7a49")
                  + _cube(16, 9.5, 6.5, "#fbc995", "#ef7d22", "#b85a12"),
    # --- other tools IngeTrazo has, for any toolbar that shows them ---
    "select": '<path d="M8 3 L8 26 L13.5 20.5 L17.5 29 L21 27.4 L17 19 L24.5 19 Z" fill="#ffffff" stroke="%s" '
              'stroke-width="1.8" stroke-linejoin="round"/>' % INK,
    "eraser": '<g transform="rotate(-35 16 16)"><rect x="5" y="11" width="22" height="10" rx="2.5" fill="#f39aa7" '
              'stroke="%s" stroke-width="1.6"/><rect x="5" y="11" width="8" height="10" rx="2.5" fill="#8fb8e8" '
              'stroke="%s" stroke-width="1.6"/></g><line x1="4" y1="29" x2="28" y2="29" stroke="%s" '
              'stroke-width="1.4"/>' % (INK, INK, GREY),
    "paint": '<path d="M5 13 L18 5.5 L26.5 18.5 L13.5 26 Z" fill="#cfd6de" stroke="%s" stroke-width="1.8" '
             'stroke-linejoin="round"/><path d="M26.5 18.5 Q30.5 23 28.5 27 Q26.5 30 25.3 26.5 Q24.7 23 26.5 18.5 Z" '
             'fill="%s"/><path d="M8 11.5 Q11 3 18 5.5" fill="none" stroke="%s" stroke-width="1.5"/>'
             % (INK, BLUE, INK),
    "move": '<g stroke="%s" stroke-width="2.2"><line x1="16" y1="7" x2="16" y2="25"/><line x1="7" y1="16" '
            'x2="25" y2="16"/></g><g fill="%s"><polygon points="16,2 11.5,8 20.5,8"/><polygon points="16,30 '
            '11.5,24 20.5,24"/><polygon points="2,16 8,11.5 8,20.5"/><polygon points="30,16 24,11.5 24,20.5"/>'
            '</g>' % (RED, RED),
    "rotate": '<path d="M16 5 A11 11 0 1 1 5 16" fill="none" stroke="%s" stroke-width="2.6" '
              'stroke-linecap="round"/><polygon points="14.5,0.5 21.5,5 14.5,9.5" fill="%s"/>%s'
              % (GREEN, GREEN, _dot(16, 16, ORANGE)),
    "scale": '<rect x="4" y="4" width="24" height="24" fill="none" stroke="%s" stroke-width="1.4" '
             'stroke-dasharray="2.5 2"/><rect x="4" y="14" width="14" height="14" fill="%s" stroke="%s" '
             'stroke-width="1.8"/><line x1="13" y1="19" x2="24" y2="8" stroke="%s" stroke-width="2"/>'
             '<polygon points="27,5 19.5,6.5 25.5,12.5" fill="%s"/>' % (BLUE, PALE, INK, ORANGE, ORANGE),
    "pushpull": '<polygon points="3,23 17,23 29,17 15,17" fill="%s" stroke="%s" stroke-width="1.6" '
                'stroke-linejoin="round"/><line x1="16" y1="20" x2="16" y2="8" stroke="%s" stroke-width="2.6"/>'
                '<polygon points="16,2 10.5,9 21.5,9" fill="%s"/>' % (PALE, INK, RED, RED),
    "offset": '<rect x="3.5" y="3.5" width="25" height="25" rx="3" fill="%s" stroke="%s" stroke-width="1.8"/>'
              '<rect x="10" y="10" width="12" height="12" rx="1.5" fill="none" stroke="%s" stroke-width="1.8" '
              'stroke-dasharray="2.5 2"/>' % (PALE, INK, ORANGE),
    "followme": '<path d="M5 27 Q5 9 23 9 L29 9" fill="none" stroke="%s" stroke-width="1.6" '
                'stroke-dasharray="2.5 2"/><path d="M5 27 Q5 9 23 9" fill="none" stroke="%s" stroke-width="4" '
                'stroke-opacity="0.35"/><rect x="2" y="23" width="6.5" height="6.5" fill="%s" stroke="%s" '
                'stroke-width="1.2"/>' % (BLUE, ORANGE, ORANGE, INK),
    "orbit": '<circle cx="16" cy="16" r="6" fill="%s" stroke="%s" stroke-width="1.6"/>'
             '<ellipse cx="16" cy="16" rx="13.5" ry="5.5" fill="none" stroke="%s" stroke-width="2" '
             'transform="rotate(-20 16 16)"/><polygon points="25.5,6.5 30.5,7.5 26.5,11.5" fill="%s"/>'
             % (PALE, INK, BLUE, BLUE),
    "pan": '<g fill="#f2d2b0" stroke="%s" stroke-width="1.3"><rect x="8.5" y="7" width="3.6" height="13" rx="1.8"/>'
           '<rect x="12.4" y="4" width="3.6" height="15" rx="1.8"/><rect x="16.3" y="5" width="3.6" height="14" '
           'rx="1.8"/><rect x="20.2" y="8" width="3.6" height="12" rx="1.8"/><rect x="3" y="15" width="4" '
           'height="10" rx="2" transform="rotate(-35 5 20)"/><rect x="7.5" y="14" width="16.3" height="15" '
           'rx="5.5"/></g>' % INK,
    "zoom": '<line x1="19.5" y1="19.5" x2="28" y2="28" stroke="%s" stroke-width="4.2" stroke-linecap="round"/>'
            '<circle cx="13" cy="13" r="9" fill="#e6f1fc" stroke="%s" stroke-width="2.2"/>'
            '<g stroke="%s" stroke-width="2"><line x1="9" y1="13" x2="17" y2="13"/><line x1="13" y1="9" x2="13" '
            'y2="17"/></g>' % (INK, INK, BLUE),
    "zoom_window": '<rect x="2" y="2" width="17" height="17" fill="none" stroke="%s" stroke-width="1.6" '
                   'stroke-dasharray="2.5 2"/><line x1="21" y1="21" x2="28.5" y2="28.5" stroke="%s" '
                   'stroke-width="4" stroke-linecap="round"/><circle cx="16" cy="16" r="7" fill="#e6f1fc" '
                   'stroke="%s" stroke-width="2.2"/>' % (RED, INK, INK),
    "zoom_ext": '<g fill="none" stroke="%s" stroke-width="2"><path d="M2 8 V2 H8"/><path d="M24 2 H30 V8"/>'
                '<path d="M2 24 V30 H8"/></g><line x1="20" y1="20" x2="28.5" y2="28.5" stroke="%s" '
                'stroke-width="4" stroke-linecap="round"/><circle cx="15" cy="15" r="7.5" fill="#e6f1fc" '
                'stroke="%s" stroke-width="2.2"/>' % (RED, INK, INK),
    "section": '<polygon points="4,11 20,4 28,21 12,28" fill="%s" fill-opacity="0.35" stroke="%s" '
               'stroke-width="1.8" stroke-linejoin="round"/><line x1="16" y1="16" x2="25" y2="12" stroke="%s" '
               'stroke-width="2"/><polygon points="29,10 22,9.5 24.5,15" fill="%s"/>'
               % (ORANGE, ORANGE, INK, INK),
    "axes": '<g stroke-width="2.4" stroke-linecap="round"><line x1="10" y1="22" x2="29" y2="22" stroke="%s"/>'
            '<line x1="10" y1="22" x2="10" y2="3" stroke="%s"/><line x1="10" y1="22" x2="3" y2="29" stroke="%s"/>'
            '</g>%s' % (RED, BLUE, GREEN, _dot(10, 22, ORANGE)),
}



# --- more of IngeTrazo's buttons ---
def _badge_pencil():
    return ('<g transform="rotate(45 24 23)"><rect x="21.8" y="14" width="4.4" height="12" fill="%s" stroke="%s" '
            'stroke-width="1"/><polygon points="21.8,26 26.2,26 24,30.5" fill="%s"/></g>' % (YELLOW, INK, INK))


def _sheets(top=PALE, mid=PALE, low=PALE):
    s = ""
    for y, c in ((15, low), (9, mid), (3, top)):
        s += ('<polygon points="16,%s 29,%s 16,%s 3,%s" fill="%s" stroke="%s" stroke-width="1.3" '
              'stroke-linejoin="round"/>' % (y, y + 5.5, y + 11, y + 5.5, c, INK))
    return s


def _badge(inner):
    return '<circle cx="24.5" cy="24.5" r="7" fill="#ffffff" stroke="%s" stroke-width="1.3"/>%s' % (INK, inner)


_EYE = ('<path d="M18.5 24.5 Q24.5 19 30.5 24.5 Q24.5 30 18.5 24.5 Z" fill="#ffffff" stroke="%s" stroke-width="1.2"/>'
        '<circle cx="24.5" cy="24.5" r="2" fill="%s"/>' % (INK, BLUE))
_VIEW_CUBE = (16, 17, 12)


def _view(face, hidden=False):
    cx, cy, s = _VIEW_CUBE
    a = s * 0.866
    faces = {"top": [(cx, cy - s), (cx + a, cy - s / 2), (cx, cy), (cx - a, cy - s / 2)],
             "left": [(cx - a, cy - s / 2), (cx, cy), (cx, cy + s), (cx - a, cy + s / 2)],
             "right": [(cx, cy), (cx + a, cy - s / 2), (cx + a, cy + s / 2), (cx, cy + s)]}
    out = _cube(cx, cy, s, "#eef2f6", "#d5dce4", "#b9c3ce")
    pts = " ".join("%.1f,%.1f" % p for p in faces[face])
    if hidden:
        out += ('<polygon points="%s" fill="%s" fill-opacity="0.25" stroke="%s" stroke-width="1.8" '
                'stroke-dasharray="2.5 1.8" stroke-linejoin="round"/>' % (pts, ORANGE, ORANGE))
    else:
        out += '<polygon points="%s" fill="%s" stroke="%s" stroke-width="0.9" stroke-linejoin="round"/>' % (
            pts, ORANGE, INK)
    return out


def _stairs(points, fill="#e9d3b4"):
    return '<polygon points="%s" fill="%s" stroke="%s" stroke-width="1.6" stroke-linejoin="round"/>' % (
        points, fill, INK)


_HOUSE = ('<rect x="6" y="16" width="20" height="12" fill="%s" stroke="%s" stroke-width="1.6"/>'
          '<rect x="13.5" y="20" width="5" height="8" fill="#ffffff" stroke="%s" stroke-width="1.2"/>'
          % (PALE, INK, INK))
_TILED_ROOF = ('<polygon points="2,17 16,4 30,17" fill="#c45a3b" stroke="%s" stroke-width="1.6" '
               'stroke-linejoin="round"/><g stroke="#8a3a24" stroke-width="1"><line x1="7.5" y1="12" x2="24.5" '
               'y2="12"/><line x1="11" y1="8.5" x2="21" y2="8.5"/><line x1="12" y1="12" x2="10" y2="17"/>'
               '<line x1="16" y1="12" x2="16" y2="17"/><line x1="20" y1="12" x2="22" y2="17"/></g>' % INK)
_LENS = "M16 9.07 A8 8 0 0 1 16 22.93 A8 8 0 0 1 16 9.07 Z"

ICONS.update({
    "undo": '<path d="M9 12 H19.5 A7.5 7.5 0 0 1 19.5 27 H10" fill="none" stroke="%s" stroke-width="2.8" '
            'stroke-linecap="round"/><polygon points="2.5,12 10,5.5 10,18.5" fill="%s"/>' % (BLUE, BLUE),
    "redo": '<g transform="translate(32,0) scale(-1,1)"><path d="M9 12 H19.5 A7.5 7.5 0 0 1 19.5 27 H10" '
            'fill="none" stroke="%s" stroke-width="2.8" stroke-linecap="round"/><polygon points="2.5,12 10,5.5 '
            '10,18.5" fill="%s"/></g>' % (BLUE, BLUE),
    "save": '<path d="M4 4 H23 L28 9 V28 H4 Z" fill="%s" stroke="%s" stroke-width="1.4" stroke-linejoin="round"/>'
            '<rect x="8.5" y="4" width="12.5" height="8" fill="#ffffff"/><rect x="16.5" y="5.5" width="2.8" '
            'height="5" fill="%s"/><rect x="8" y="17" width="16" height="11" fill="#ffffff" stroke="%s" '
            'stroke-width="1"/>' % (BLUE, INK, INK, INK),
    "sample": '<g transform="rotate(45 16 16)"><rect x="13" y="0.5" width="6" height="8" rx="2.5" fill="%s"/>'
              '<rect x="11" y="8" width="10" height="3" rx="1" fill="%s"/><path d="M13.5 11 H18.5 V24 L16 30 '
              'L13.5 24 Z" fill="#ffffff" stroke="%s" stroke-width="1.5" stroke-linejoin="round"/>'
              '<path d="M13.5 18 H18.5 V24 L16 30 L13.5 24 Z" fill="%s"/></g>' % (INK, INK, INK, ORANGE),
    "flip": '<line x1="16" y1="2" x2="16" y2="30" stroke="%s" stroke-width="1.4" stroke-dasharray="2.5 2"/>'
            '<polygon points="13,9 13,27 3,27" fill="%s" stroke="%s" stroke-width="1.6" stroke-linejoin="round"/>'
            '<polygon points="19,9 19,27 29,27" fill="%s" stroke="%s" stroke-width="1.6" stroke-linejoin="round"/>'
            '<path d="M8 6 Q16 0.5 23 5" fill="none" stroke="%s" stroke-width="1.8"/>'
            '<polygon points="26,7 20.5,7.5 23.5,2.5" fill="%s"/>' % (GREY, PALE, INK, ORANGE, INK, ORANGE, ORANGE),
    "fillet": '<path d="M4 28 V13 A9 9 0 0 1 13 4 H28 V28 Z" fill="%s" stroke="%s" stroke-width="1.8" '
              'stroke-linejoin="round"/><path d="M4 13 A9 9 0 0 1 13 4" fill="none" stroke="%s" stroke-width="3.2" '
              'stroke-linecap="round"/>' % (PALE, INK, ORANGE),
    "bevel": '<path d="M4 28 V13 L13 4 H28 V28 Z" fill="%s" stroke="%s" stroke-width="1.8" stroke-linejoin="round"/>'
             '<line x1="4" y1="13" x2="13" y2="4" stroke="%s" stroke-width="3.2" stroke-linecap="round"/>'
             % (PALE, INK, ORANGE),
    "bridge": '<polygon points="10,7 22,7 22,25 10,25" fill="%s" fill-opacity="0.45"/>'
              '<polygon points="2,9 10,7 10,25 2,29" fill="%s" stroke="%s" stroke-width="1.5" stroke-linejoin="round"/>'
              '<polygon points="22,7 30,3 30,23 22,25" fill="%s" stroke="%s" stroke-width="1.5" stroke-linejoin="round"/>'
              '<g stroke="%s" stroke-width="1.6"><line x1="10" y1="7" x2="22" y2="7"/><line x1="10" y1="25" '
              'x2="22" y2="25"/></g>' % (ORANGE, PALE, INK, PALE, INK, ORANGE),
    "make_component": _cube(13, 17, 10.5, "#9cc6f2", "#4f8fd6", "#2d64a8")
                      + '<circle cx="25" cy="7.5" r="6" fill="%s" stroke="#ffffff" stroke-width="1.2"/>'
                        '<g stroke="#ffffff" stroke-width="2.2"><line x1="21.5" y1="7.5" x2="28.5" y2="7.5"/>'
                        '<line x1="25" y1="4" x2="25" y2="11"/></g>' % ORANGE,
    "make_group": '<rect x="2.5" y="2.5" width="27" height="27" rx="2" fill="none" stroke="%s" stroke-width="1.6" '
                  'stroke-dasharray="3 2"/>' % BLUE + _cube(16, 16, 9, "#eef2f6", "#d5dce4", "#b9c3ce"),
    "zoom_sel": '<rect x="2" y="2" width="14" height="14" rx="1" fill="%s" fill-opacity="0.55" stroke="%s" '
                'stroke-width="1.6"/><line x1="21" y1="21" x2="28.5" y2="28.5" stroke="%s" stroke-width="4" '
                'stroke-linecap="round"/><circle cx="16" cy="16" r="7" fill="none" stroke="%s" stroke-width="2.2"/>'
                % (ORANGE, ORANGE, INK, INK),
    "first_person": '<circle cx="16" cy="10" r="6" fill="#4a5462"/><path d="M4.5 30 Q4.5 18.5 16 18.5 Q27.5 18.5 '
                    '27.5 30 Z" fill="#4a5462"/><path d="M12 9.5 Q16 6.5 20 9.5 Q16 12.5 12 9.5 Z" '
                    'fill="#ffffff"/><circle cx="16" cy="9.5" r="1.3" fill="%s"/>' % BLUE,
    "view_top": _view("top"), "view_front": _view("left"), "view_right": _view("right"),
    "view_bottom": _view("top", True), "view_back": _view("left", True), "view_left": _view("right", True),
    "view_iso": _cube(16, 17, 12, "#9cc6f2", "#4f8fd6", "#2d64a8"),
    "persp": '<polygon points="3,9 15,5 15,28 3,24" fill="%s" stroke="%s" stroke-width="1.5" stroke-linejoin="round"/>'
             '<polygon points="15,5 29,10 29,23 15,28" fill="#9cc6f2" stroke="%s" stroke-width="1.5" '
             'stroke-linejoin="round"/><g stroke="%s" stroke-width="1" stroke-dasharray="2 2"><line x1="29" y1="10" '
             'x2="31" y2="15.5"/><line x1="29" y1="23" x2="31" y2="17.5"/></g>' % (PALE, INK, INK, ORANGE),
    "parallel": _cube(16, 17, 12, "#eef2f6", "#d5dce4", "#b9c3ce")
                + '<g stroke="%s" stroke-width="2" stroke-linecap="round"><line x1="3" y1="27" x2="10.5" y2="31"/>'
                  '<line x1="21.5" y1="31" x2="29" y2="27"/></g>' % ORANGE,
    "two_point": '<polygon points="3,10 15,6 15,28 3,25" fill="%s" stroke="%s" stroke-width="1.5" '
                 'stroke-linejoin="round"/><polygon points="15,6 29,10 29,25 15,28" fill="#9cc6f2" stroke="%s" '
                 'stroke-width="1.5" stroke-linejoin="round"/><g stroke="%s" stroke-width="2.4" '
                 'stroke-linecap="round"><line x1="3" y1="10" x2="3" y2="25"/><line x1="15" y1="6" x2="15" '
                 'y2="28"/><line x1="29" y1="10" x2="29" y2="25"/></g>' % (PALE, INK, INK, ORANGE),
    "section_cuts": _cube(16, 17, 12, "#eef2f6", "#d5dce4", "#b9c3ce")
                    + '<polygon points="16,5 26.4,11 26.4,23 16,17" fill="%s" stroke="%s" stroke-width="1" '
                      'stroke-linejoin="round"/>' % (ORANGE, INK),
    "section_fill": '<rect x="4" y="4" width="24" height="24" fill="%s" stroke="%s" stroke-width="1.8"/>'
                    '<g stroke="#ffffff" stroke-width="1.4"><line x1="4" y1="12" x2="12" y2="4"/><line x1="4" '
                    'y1="20" x2="20" y2="4"/><line x1="4" y1="28" x2="28" y2="4"/><line x1="12" y1="28" x2="28" '
                    'y2="12"/><line x1="20" y1="28" x2="28" y2="20"/></g>' % (ORANGE, INK),
    "section_planes": '<polygon points="4,11 20,4 28,21 12,28" fill="none" stroke="%s" stroke-width="2.2" '
                      'stroke-linejoin="round"/><g fill="%s"><polygon points="2,9 8,6.5 6,13"/><polygon '
                      'points="30,23 24,25.5 26,19"/></g>' % (ORANGE, ORANGE),
    "union": '<circle cx="12" cy="16" r="8.5" fill="none" stroke="%s" stroke-width="2.4"/><circle cx="20" cy="16" '
             'r="8.5" fill="none" stroke="%s" stroke-width="2.4"/><circle cx="12" cy="16" r="8.5" fill="%s"/>'
             '<circle cx="20" cy="16" r="8.5" fill="%s"/>' % (INK, INK, BLUE, BLUE),
    "subtract": '<circle cx="12" cy="16" r="8" fill="%s" stroke="%s" stroke-width="1.6"/><circle cx="20" cy="16" '
                'r="8" fill="#ffffff" stroke="%s" stroke-width="1.6" stroke-dasharray="2.5 2"/>' % (BLUE, INK, GREY),
    "intersect": '<circle cx="12" cy="16" r="8" fill="none" stroke="%s" stroke-width="1.4" stroke-dasharray="2.5 2"/>'
                 '<circle cx="20" cy="16" r="8" fill="none" stroke="%s" stroke-width="1.4" stroke-dasharray="2.5 2"/>'
                 '<path d="%s" fill="%s" stroke="%s" stroke-width="1.6"/>' % (GREY, GREY, _LENS, ORANGE, INK),
    "trim": '<circle cx="20" cy="16" r="8" fill="%s" stroke="%s" stroke-width="1.6"/><path d="%s" fill="#ffffff"/>'
            '<circle cx="12" cy="16" r="8" fill="none" stroke="%s" stroke-width="2"/>' % (BLUE, INK, _LENS, ORANGE),
    "split": '<circle cx="11" cy="16" r="8" fill="%s"/><circle cx="21" cy="16" r="8" fill="%s"/>'
             '<path d="M16 9.76 A8 8 0 0 1 16 22.24 A8 8 0 0 1 16 9.76 Z" fill="%s" stroke="#ffffff" '
             'stroke-width="1.8"/>' % (BLUE, GREEN, ORANGE),
    "outer_shell": '<circle cx="12" cy="16" r="8.5" fill="none" stroke="%s" stroke-width="3.2"/><circle cx="20" '
                   'cy="16" r="8.5" fill="none" stroke="%s" stroke-width="3.2"/><circle cx="12" cy="16" r="8.5" '
                   'fill="%s"/><circle cx="20" cy="16" r="8.5" fill="%s"/>' % (ORANGE, ORANGE, PALE, PALE),
    "layers_panel": _sheets("#9cc6f2", PALE, PALE),
    "layers_hide": _sheets() + _badge(_EYE + '<line x1="19.5" y1="29" x2="29.5" y2="20" stroke="%s" '
                                             'stroke-width="2"/>' % RED),
    "layers_isolate": _sheets(PALE, ORANGE, PALE),
    "layers_lock": _sheets() + _badge('<rect x="20.5" y="23.5" width="8" height="6" rx="1" fill="%s"/>'
                                      '<path d="M22.3 23.5 V21.5 A2.2 2.2 0 0 1 26.7 21.5 V23.5" fill="none" '
                                      'stroke="%s" stroke-width="1.6"/>' % (INK, INK)),
    "layers_active": _sheets(PALE, ORANGE, PALE) + _badge('<path d="M20.5 24.5 L23.3 27.3 L28.5 21.5" fill="none" '
                                                          'stroke="%s" stroke-width="2.2" stroke-linecap="round" '
                                                          'stroke-linejoin="round"/>' % GREEN),
    "layers_show_all": _sheets("#9cc6f2", "#9cc6f2", "#9cc6f2") + _badge(_EYE),
    "layers_to_active": _sheets(PALE, ORANGE, PALE) + _badge('<line x1="24.5" y1="19.5" x2="24.5" y2="26" '
                                                             'stroke="%s" stroke-width="2"/><polygon points="24.5,'
                                                             '29.5 21,25 28,25" fill="%s"/>' % (ORANGE, ORANGE)),
    "layers_previous": _sheets() + _badge('<path d="M21.5 22.5 H26 A2.6 2.6 0 0 1 26 27.7 H22" fill="none" '
                                          'stroke="%s" stroke-width="1.8"/><polygon points="19,22.5 22.5,19.5 '
                                          '22.5,25.5" fill="%s"/>' % (BLUE, BLUE)),
    "roof_create": _HOUSE + '<polygon points="2,17 16,4 30,17" fill="%s" stroke="%s" stroke-width="1.6" '
                            'stroke-linejoin="round"/>' % (ORANGE, INK),
    "roof_cover": _HOUSE + _TILED_ROOF,
    "roof_edit": _HOUSE + '<polygon points="2,17 16,4 30,17" fill="%s" stroke="%s" stroke-width="1.6" '
                          'stroke-linejoin="round"/>' % (ORANGE, INK) + _badge_pencil(),
    "roof_tiles_edit": _HOUSE + _TILED_ROOF + _badge_pencil(),
    "stair": _stairs("3,28 3,23 9,23 9,18 15,18 15,13 21,13 21,8 27,8 27,3 29,3 29,28"),
    "stair_landing": _stairs("2,28 2,23 7,23 7,18 12,18 12,13 19,13 19,8 24,8 24,3 30,3 30,28")
                     + '<line x1="12" y1="13" x2="19" y2="13" stroke="%s" stroke-width="2.6"/>' % ORANGE,
    "stair_l": '<rect x="3" y="3" width="9" height="26" fill="#e9d3b4" stroke="%s" stroke-width="1.5"/>'
               '<rect x="12" y="20" width="17" height="9" fill="#e9d3b4" stroke="%s" stroke-width="1.5"/>'
               '<g stroke="%s" stroke-width="1"><line x1="3" y1="8" x2="12" y2="8"/><line x1="3" y1="13" x2="12" '
               'y2="13"/><line x1="17" y1="20" x2="17" y2="29"/><line x1="22" y1="20" x2="22" y2="29"/></g>'
               '<rect x="3" y="20" width="9" height="9" fill="%s"/>' % (INK, INK, INK, ORANGE),
    "stair_u": '<rect x="3" y="3" width="10" height="26" fill="#e9d3b4" stroke="%s" stroke-width="1.5"/>'
               '<rect x="19" y="3" width="10" height="26" fill="#e9d3b4" stroke="%s" stroke-width="1.5"/>'
               '<g stroke="%s" stroke-width="1"><line x1="3" y1="9" x2="13" y2="9"/><line x1="3" y1="15" x2="13" '
               'y2="15"/><line x1="19" y1="9" x2="29" y2="9"/><line x1="19" y1="15" x2="29" y2="15"/></g>'
               '<rect x="3" y="21" width="26" height="8" fill="%s" stroke="%s" stroke-width="1.5"/>'
               % (INK, INK, INK, ORANGE, INK),
    "stair_edit": _stairs("3,28 3,23 9,23 9,18 15,18 15,13 21,13 21,8 27,8 27,3 29,3 29,28") + _badge_pencil(),
    "isolate_groups": '<rect x="5" y="5" width="22" height="22" fill="none" stroke="%s" stroke-width="1.4" '
                      'stroke-dasharray="2.5 2" transform="rotate(20 16 16)"/><rect x="11" y="11" width="10" '
                      'height="10" fill="%s" stroke="%s" stroke-width="1.4"/>' % (GREY, ORANGE, INK),
    "sidebar_left": '<rect x="3" y="5" width="26" height="22" rx="2" fill="#ffffff" stroke="%s" stroke-width="1.6"/>'
                    '<rect x="4" y="6" width="8" height="20" fill="%s"/>' % (INK, ORANGE),
    "sidebar_right": '<rect x="3" y="5" width="26" height="22" rx="2" fill="#ffffff" stroke="%s" stroke-width="1.6"/>'
                     '<rect x="20" y="6" width="8" height="20" fill="%s"/>' % (INK, ORANGE),
})

# IngeTrazo's button names (as it shows them in English) -> (icon, short name under it)
BUTTONS = {
    "line": ("line", "Line"), "freehand": ("freehand", "Freehand"), "rectangle": ("rect", "Rect"),
    "rotated rect": ("rot_rect", "Rotated"), "rotated rectangle": ("rot_rect", "Rotated"),
    "circle": ("circle", "Circle"), "polygon": ("polygon", "Polygon"),
    "center arc": ("arc_centre", "Centre arc"), "centre arc": ("arc_centre", "Centre arc"),
    "arc": ("arc2", "Arc"), "2-point arc": ("arc2", "Arc"), "3-point arc": ("arc3", "3-pt arc"),
    "pie": ("pie", "Pie"), "path": ("path", "Path"), "tape measure": ("tape", "Tape"),
    "protractor": ("protractor", "Angle"), "dimension": ("dimension", "Dim"), "text": ("text", "Text"),
    "3d text": ("text3d", "3D text"), "position camera": ("camera", "Camera"), "walk": ("walk", "Walk"),
    "look around": ("look", "Look"), "components": ("components", "Comps"),
    "select": ("select", "Select"), "eraser": ("eraser", "Erase"), "paint": ("paint", "Paint"),
    "move": ("move", "Move"), "rotate": ("rotate", "Rotate"), "scale": ("scale", "Scale"),
    "push / pull": ("pushpull", "Push"), "push/pull": ("pushpull", "Push"), "offset": ("offset", "Offset"),
    "follow me": ("followme", "Follow"), "orbit": ("orbit", "Orbit"), "pan": ("pan", "Pan"),
    "zoom": ("zoom", "Zoom"), "zoom window": ("zoom_window", "Window"),
    "zoom extents": ("zoom_ext", "Extents"), "zoom selection": ("zoom_sel", "Selected"),
    "section plane": ("section", "Section"), "axes": ("axes", "Axes"),
    "sample material": ("sample", "Sample"), "flip": ("flip", "Flip"), "fillet 3d": ("fillet", "Fillet"),
    "bevel selected edges / solid": ("bevel", "Bevel"), "bevel": ("bevel", "Bevel"),
    "bridge": ("bridge", "Bridge"), "make component": ("make_component", "Component"),
    "make group": ("make_group", "Group"), "first person": ("first_person", "1st person"),
    "undo": ("undo", "Undo"), "redo": ("redo", "Redo"), "save": ("save", "Save"),
    "top": ("view_top", "Top"), "front": ("view_front", "Front"), "right": ("view_right", "Right"),
    "back": ("view_back", "Back"), "left": ("view_left", "Left"), "bottom": ("view_bottom", "Bottom"),
    "isometric": ("view_iso", "Iso"), "parallel projection": ("parallel", "Parallel"),
    "perspective": ("persp", "Persp"), "two-point perspective": ("two_point", "2-point"),
    "section cuts": ("section_cuts", "Cuts"), "section fill": ("section_fill", "Fill"),
    "section planes": ("section_planes", "Planes"),
    "union": ("union", "Union"), "subtract": ("subtract", "Subtract"), "intersect": ("intersect", "Intersect"),
    "trim": ("trim", "Trim"), "split": ("split", "Split"), "outer shell": ("outer_shell", "Shell"),
    "layers panel": ("layers_panel", "Layers"), "hide layer": ("layers_hide", "Hide"),
    "isolate layer": ("layers_isolate", "Isolate"), "lock layer": ("layers_lock", "Lock"),
    "make layer active": ("layers_active", "Active"), "show all layers": ("layers_show_all", "Show all"),
    "move to active layer": ("layers_to_active", "To active"), "previous state": ("layers_previous", "Previous"),
    "create roof": ("roof_create", "Roof"), "cover roof": ("roof_cover", "Tiles"),
    "edit roof shape": ("roof_edit", "Edit roof"), "edit roof tiles": ("roof_tiles_edit", "Edit tiles"),
    "create straight stair": ("stair", "Stair"), "create straight with landing stair": ("stair_landing", "Landing"),
    "create l-shaped stair": ("stair_l", "L stair"), "create u-shaped stair": ("stair_u", "U stair"),
    "edit selected stair": ("stair_edit", "Edit stair"),
}
# buttons with no name of their own, known by their pop-up note or internal name
BY_OBJECT_NAME = {"left_sidebar_handle": ("sidebar_left", "Left bar"),
                  "sidebar_handle": ("sidebar_right", "Right bar")}
BY_TIP_START = {"isolate: hide everything": ("isolate_groups", "Isolate")}
# Qt's own little buttons that never get a name
NEVER = ("qt_toolbar_ext_button", "qt_menubar_ext_button", "float_close_button", "ScrollLeftButton",
         "ScrollRightButton", "_q_")

DEFAULTS = {'on': True, 'labels': 'off', 'text_pt': 8.5, 'icon_px': 0, 'tight': True}
LABEL_MODES = [("off", "Off"), ("new", "On the buttons with new icons"), ("all", "On every toolbar button")]


def svg_for(kind):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">%s</svg>'
            % ICONS[kind])


def load_settings():
    s = dict(DEFAULTS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            s.update(json.load(f))
    except Exception:
        pass
    if s.get('labels') is True:          # the first version kept this as on / off
        s['labels'] = 'new'
    elif s.get('labels') in (False, None):
        s['labels'] = 'off'
    return s


def save_settings(s):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f)
    except Exception:
        pass


def update_settings(**changes):
    s = load_settings()
    s.update(changes)
    save_settings(s)
    return s


# ---------------------------------------------------------------------------
# Making the icons (sharp at every size the toolbars use)
# ---------------------------------------------------------------------------
_CACHE = {}


def make_icon(kind):
    if kind in _CACHE:
        return _CACHE[kind]
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtGui import QIcon, QPixmap, QPainter
    from PySide6.QtCore import QByteArray, Qt
    r = QSvgRenderer(QByteArray(svg_for(kind).encode("utf-8")))
    icon = QIcon()
    for size in (16, 20, 24, 28, 32, 40, 48, 56, 64):
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        r.render(p)
        p.end()
        icon.addPixmap(pm)
    _CACHE[kind] = icon
    return icon


# ---------------------------------------------------------------------------
# Finding IngeTrazo's toolbar buttons
# ---------------------------------------------------------------------------
def _clean(text):
    t = (text or "").split("\n")[0].split("\t")[0].replace("&", "")
    t = re.sub(r"\s*\([^)]*\)\s*$", "", t)        # "Line (L)" -> "Line"
    t = t.rstrip(".… ").strip()
    return " ".join(t.split()).lower()


def match(texts, obj_name="", tip=""):
    """(icon, short name) for a button, or None."""
    for t in texts:
        hit = BUTTONS.get(_clean(t))
        if hit:
            return hit
    if obj_name in BY_OBJECT_NAME:
        return BY_OBJECT_NAME[obj_name]
    low = (tip or "").strip().lower()
    for start, hit in BY_TIP_START.items():
        if low.startswith(start):
            return hit
    return None


def kind_for(*texts):
    hit = match(texts)
    return hit[0] if hit else None


def short_name(text):
    """A short name for a button this plugin doesn't know: its own, cut down if long."""
    t = (text or "").split("\n")[0].split("\t")[0].replace("&", "")
    t = re.sub(r"\s*\([^)]*\)\s*$", "", t).rstrip(".… ").strip()
    if len(t) > 11:
        t = t.split(" ")[0]
    return t[:11]


def _main_window():
    from PySide6.QtWidgets import QApplication, QMainWindow
    app = QApplication.instance()
    if app is None:
        return None
    wins = [w for w in app.topLevelWidgets() if isinstance(w, QMainWindow)]
    shown = [w for w in wins if w.isVisible()]
    return (shown or wins or [None])[0]


def _toolbar_of(w):
    """The IngeTrazo toolbar a button sits on (None if not on one, or on one of Eddy's)."""
    from PySide6.QtWidgets import QToolBar
    depth = 0
    while w is not None and depth < 25:
        try:
            if (w.objectName() or "").startswith(SKIP_TOOLBARS):
                return None
            if isinstance(w, QToolBar):
                return w
            w = w.parent()
        except Exception:
            return None
        depth += 1
    return None


class Btn:
    """One toolbar button: the QToolButton, its action (if any), what it is."""
    def __init__(self, button, action, toolbar):
        self.button, self.action, self.toolbar = button, action, toolbar
        a, b = action, button
        self.name = (getattr(a, "_eddy_orig_icontext", None) or a.text()) if a is not None \
            else (getattr(b, "_eddy_orig_text", None) or b.text())
        self.tip = a.toolTip() if a is not None else b.toolTip()
        self.obj = (a.objectName() if a is not None else "") or b.objectName() or ""
        texts = (a.text(), self.tip, self.name, a.objectName()) if a is not None else (self.name, self.tip,
                                                                                       b.objectName())
        self.hit = match(texts, b.objectName() or self.obj, self.tip)
        self.qt_own = any((b.objectName() or "").startswith(n) for n in NEVER)

    @property
    def target(self):
        return self.action if self.action is not None else self.button


def toolbar_buttons(win):
    from PySide6.QtWidgets import QToolButton
    out = []
    for b in win.findChildren(QToolButton):
        try:
            if b.window() is not win:
                continue
            tb = _toolbar_of(b)
            if tb is None:
                continue
            out.append(Btn(b, b.defaultAction(), tb))
        except Exception:
            pass
    return out


# ---------------------------------------------------------------------------
# Putting it all on (or back as it was)
# ---------------------------------------------------------------------------
def _set_icon(t, kind, on):
    if on and kind:
        if getattr(t, "_eddy_icon_kind", None) == kind:
            return
        if not hasattr(t, "_eddy_orig_icon"):
            t._eddy_orig_icon = t.icon()
        t._eddy_busy = True
        try:
            t.setIcon(make_icon(kind))
        finally:
            t._eddy_busy = False
        t._eddy_icon_kind = kind
    elif hasattr(t, "_eddy_orig_icon") and getattr(t, "_eddy_icon_kind", None):
        t._eddy_busy = True
        try:
            t.setIcon(t._eddy_orig_icon)
        finally:
            t._eddy_busy = False
        t._eddy_icon_kind = None


def _guard(t):
    """If IngeTrazo puts its own icon back on a button (it can, when it redraws its
    toolbars), the new one goes straight back on."""
    if getattr(t, "_eddy_guarded", False) or not hasattr(t, "changed"):
        return
    t._eddy_guarded = True

    def changed(t=t):
        try:
            if getattr(t, "_eddy_busy", False):
                return
            kind = getattr(t, "_eddy_icon_kind", None)
            if kind and t.icon().cacheKey() != make_icon(kind).cacheKey():
                t._eddy_icon_kind = None
                t._eddy_orig_icon = t.icon()
                _set_icon(t, kind, True)
        except Exception:
            pass
    t.changed.connect(changed)


def _set_label(btn, text):
    t = btn.target
    if text is None:                                  # back to its own
        if hasattr(t, "_eddy_orig_icontext"):
            (t.setIconText if hasattr(t, "setIconText") else t.setText)(t._eddy_orig_icontext)
            del t._eddy_orig_icontext
        return
    if not hasattr(t, "_eddy_orig_icontext"):
        t._eddy_orig_icontext = t.iconText() if hasattr(t, "iconText") else t.text()
    t._eddy_busy = True
    try:
        (t.setIconText if hasattr(t, "setIconText") else t.setText)(text)   # the button only
    finally:
        t._eddy_busy = False


TIGHT_STYLE = "QToolButton { padding: 1px 2px 1px 2px; }"


def _style_button(b, labelled, s):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
    if labelled:
        if not hasattr(b, "_eddy_orig_style"):
            b._eddy_orig_style = b.toolButtonStyle()
            b._eddy_orig_sheet = b.styleSheet()
        f = QFont(b.font())
        f.setPointSizeF(float(s.get('text_pt', 8.5)))
        b.setFont(f)
        b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        b.setStyleSheet((b._eddy_orig_sheet + "\n" + TIGHT_STYLE) if s.get('tight', True) else b._eddy_orig_sheet)
    elif hasattr(b, "_eddy_orig_style"):
        b.setToolButtonStyle(b._eddy_orig_style)
        b.setStyleSheet(b._eddy_orig_sheet)
        b.setFont(QFont())
        b.setAttribute(Qt.WA_SetFont, False)
        del b._eddy_orig_style


def _size_toolbars(win, px):
    from PySide6.QtWidgets import QToolBar
    from PySide6.QtCore import QSize
    for tb in win.findChildren(QToolBar):
        try:
            if (tb.objectName() or "").startswith(SKIP_TOOLBARS):
                continue
            if px:
                if not hasattr(tb, "_eddy_orig_iconsize"):
                    tb._eddy_orig_iconsize = tb.iconSize()
                if tb.iconSize() != QSize(px, px):
                    tb.setIconSize(QSize(px, px))
            elif hasattr(tb, "_eddy_orig_iconsize"):
                tb.setIconSize(tb._eddy_orig_iconsize)
                del tb._eddy_orig_iconsize
        except Exception:
            pass


def refresh(win=None, write_list=False):
    """Puts every setting on IngeTrazo's toolbars. Returns how many buttons got new icons."""
    win = win or _main_window()
    if win is None:
        return 0
    s = load_settings()
    on, mode = bool(s.get('on', True)), s.get('labels', 'off')
    _size_toolbars(win, int(s.get('icon_px', 0) or 0))
    n = 0
    lines = []
    for btn in toolbar_buttons(win):
        try:
            kind, short = btn.hit if btn.hit else (None, None)
            lines.append("%-16s %s" % (kind or "-", " | ".join(x for x in (btn.name, btn.tip.split("\n")[0],
                                                                         btn.obj) if x)))
            if btn.qt_own:
                continue
            _set_icon(btn.target, kind, on)
            if kind:
                _guard(btn.target)
                n += 1 if on else 0
            if mode == 'all' and not short:
                short = short_name(btn.name) or None
            labelled = bool(short) and (mode == 'all' or (mode == 'new' and kind))
            _set_label(btn, short if labelled else None)
            _style_button(btn.button, labelled, s)
        except Exception:
            pass
    if write_list:
        try:
            with open(LIST_FILE, "w", encoding="utf-8") as f:
                f.write("3D Better Icons: IngeTrazo's toolbar buttons (icon given | name | pop-up note | "
                        "internal name)\nA '-' means no new icon matched that button.\n\n")
                f.write("\n".join(sorted(lines)) + "\n")
        except Exception:
            pass
    return n


def apply_icons(win=None, on=None, write_list=False):
    if on is not None:
        update_settings(on=bool(on))
    return refresh(win, write_list)


def _apply_when_ready(tries=0):
    """IngeTrazo loads plugins before its window is up, and some buttons come a little
    later: keep checking for a while."""
    try:
        from PySide6.QtCore import QTimer
        win = _main_window()
        if win is None or not win.isVisible():
            if tries < 240:
                QTimer.singleShot(500, lambda: _apply_when_ready(tries + 1))
            return
        _again(win, 0)
    except Exception as e:
        print("%s: could not change the icons (%s)." % (PLUGIN_NAME, e))


def _again(win, n):
    from PySide6.QtCore import QTimer
    try:
        refresh(win, write_list=(n == 7))
    except Exception as e:
        print("%s: could not change the icons (%s)." % (PLUGIN_NAME, e))
    if n < 7:
        QTimer.singleShot(2000, lambda: _again(win, n + 1))


try:
    _apply_when_ready()
except Exception:
    pass


# ---------------------------------------------------------------------------
# The settings window
# ---------------------------------------------------------------------------
EDDY_TIPS = {
    "Use the new icons": "Ticked: the clearer icons. Unticked: IngeTrazo's own icons.",
    "Names under the icons": "Off, only on the buttons that have new icons, or on every toolbar button.",
    "Text size": "How big the names under the icons are.",
    "Icon size": "How big the icons on IngeTrazo's toolbars are. 'IngeTrazo's own' keeps its setting.",
    "Names close to the icons": "Trims the space inside each button so the name sits just under its icon.",
    "Button list": "Opens the list of every toolbar button found, and which icon it got.",
}


def open_settings(win=None):
    from PySide6.QtWidgets import (QDialog, QFormLayout, QCheckBox, QComboBox, QDoubleSpinBox, QSpinBox,
                                   QDialogButtonBox, QPushButton, QVBoxLayout, QLabel)
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtCore import QUrl
    win = win or _main_window()
    old = getattr(win, "_eddy_icons_dlg", None)
    if old is not None:
        try:
            old.show()
            old.raise_()
            old.activateWindow()
            return old
        except Exception:
            pass
    s = load_settings()
    dlg = QDialog(win)
    dlg.setWindowTitle(PLUGIN_NAME)
    dlg.setObjectName("EddyBetterIcons_dialog")
    top = QVBoxLayout(dlg)
    top.addWidget(QLabel("Changes show straight away and are remembered."))
    form = QFormLayout()
    top.addLayout(form)
    cb_on = QCheckBox("Use the new icons")
    cb_on.setChecked(bool(s.get('on', True)))
    form.addRow(cb_on)
    cb_labels = QComboBox()
    for key, text in LABEL_MODES:
        cb_labels.addItem(text, key)
    cb_labels.setCurrentIndex(max(0, cb_labels.findData(s.get('labels', 'off'))))
    form.addRow("Names under the icons:", cb_labels)
    sp_text = QDoubleSpinBox()
    sp_text.setRange(6.0, 14.0)
    sp_text.setSingleStep(0.5)
    sp_text.setDecimals(1)
    sp_text.setSuffix(" pt")
    sp_text.setValue(float(s.get('text_pt', 8.5)))
    form.addRow("Text size:", sp_text)
    sp_icon = QSpinBox()
    sp_icon.setRange(15, 64)              # 15 = "IngeTrazo's own"
    sp_icon.setSpecialValueText("IngeTrazo's own")
    sp_icon.setSuffix(" px")
    sp_icon.setValue(int(s.get('icon_px', 0) or 15))
    form.addRow("Icon size:", sp_icon)
    cb_tight = QCheckBox("Names close to the icons")
    cb_tight.setChecked(bool(s.get('tight', True)))
    form.addRow(cb_tight)
    bb = QDialogButtonBox(QDialogButtonBox.Close)
    b_list = QPushButton("Button list")
    bb.addButton(b_list, QDialogButtonBox.ActionRole)
    top.addWidget(bb)

    def changed(*_):
        px = sp_icon.value()
        update_settings(on=cb_on.isChecked(), labels=cb_labels.currentData(), text_pt=sp_text.value(),
                        icon_px=0 if px <= 15 else px, tight=cb_tight.isChecked())
        sp_text.setEnabled(cb_labels.currentData() != 'off')
        cb_tight.setEnabled(cb_labels.currentData() != 'off')
        refresh(win)

    def show_list():
        refresh(win, write_list=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(LIST_FILE))
    cb_on.toggled.connect(changed)
    cb_labels.currentIndexChanged.connect(changed)
    sp_text.valueChanged.connect(changed)
    sp_icon.valueChanged.connect(changed)
    cb_tight.toggled.connect(changed)
    b_list.clicked.connect(show_list)
    bb.rejected.connect(dlg.close)
    sp_text.setEnabled(cb_labels.currentData() != 'off')
    cb_tight.setEnabled(cb_labels.currentData() != 'off')
    try:
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)
    except Exception:
        pass
    win._eddy_icons_dlg = dlg
    dlg.show()
    return dlg

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
# Tools: Ctrl+Alt+Y opens the settings, Ctrl+Alt+Q turns the names on / off
# ---------------------------------------------------------------------------
def _window_of(viewport):
    try:
        return viewport.window()
    except Exception:
        return _main_window()


class BetterIconsTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+Y"
    description = "Clearer icons for IngeTrazo's toolbars: icon size, names under the icons and their size."

    def on_activate(self, viewport):
        open_settings(_window_of(viewport) or _main_window())

    def on_deactivate(self, viewport):
        pass


class ToolbarLabelsTool(Tool):
    name = "3D Toolbar Labels"
    shortcut = "Ctrl+Alt+Q"
    description = "Shows or hides the names under the toolbar icons."

    def on_activate(self, viewport):
        win = _window_of(viewport) or _main_window()
        s = load_settings()
        if s.get('labels', 'off') == 'off':
            s = update_settings(labels=s.get('labels_last', 'all'))
        else:
            s = update_settings(labels='off', labels_last=s.get('labels'))
        refresh(win)
        try:
            win.statusBar().showMessage("%s: %s" % (self.name, dict(LABEL_MODES)[s['labels']]), 4000)
        except Exception:
            pass

    def on_deactivate(self, viewport):
        pass


def run(viewport=None):
    """Console entry point: run() opens the settings window."""
    return open_settings()
