# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Photo to Building for IngeTrazo
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
3D Photo to Building - a building started from a photo of a real one

  Photo       Pick a photo of the building - taken from a corner, so two walls show.
  Sizes       Type one size you know (the height of the door, the length of the front...).
              Everything else is measured from the photo and sized from that.
  Match it    Your 3D program opens with the photo as a camera match. Line up two edges along each
              wall, then click round the building: the corners on the ground, the top of a corner,
              the top of the roof, two corners of each window and door. Send it back.
  Build       The building comes back here: 3D Floor Plan is filled in (outline, height, floors,
              roof) and built, the windows and doors are cut through the walls the way 3D Openings
              cuts them - each one where it is in the photo, at its own size - and on you go with the
              next step in the build order (3 Frame).

Sizes are real-world mm, like the other plugins - Scale Studio takes it down to your model scale.
Ctrl+Alt+Shift+P.
Version 1.0: first version.
Version 1.1: the 3D program's panel now opens (its lists weren't set up the way it wants, so it stopped
before the photo came up); if the 3D program has a problem starting, it's shown here; the depth box says
what 0 means.
Version 1.2: the photo view can't be turned away from the photo (dragging the wheel slides it); the
keyboard and the zoom/hand buttons work while clicking; Backspace works wherever the mouse is; clicks on
the panel no longer land on the photo.
Version 1.3: with two corners and a typed depth, the whole outline shows straight away (a rough depth
until the size you know is clicked, then the real one) - before, it waited for a door it couldn't click.
Version 1.4: parts - a wing, a bay or a porch can be clicked on the same photo as the main building ('Against
the main building' runs a bay back to its wall by itself); each part is built with Floor Plan and gets its own
windows and doors. The 3D program's panel opens in a window of its own, to move out of the way; windows and
doors are numbered separately (W1... and D1...).
Version 1.5: windows and doors can be traced (half the shape, mirrored - for pointed tops and the like) or
copied from one already done; the 3D program's panel shows one step at a time (Back / Next, the less-used
buttons under More...); a Clean view button hides the 3D program's menus and toolbars.
Version 1.6: windows and doors can be clicked all the way round; dragging slides the photo (a click is still a
click); the panel is a walk-through - numbered step tabs with plain instructions - in a window of its own with
nothing else in it.
Version 1.7: a first step listing the building's parts (how many wings and bays); a bay or wing can be copied
(click where the copy goes); steps 3 to 5 work through each part in turn from the main building; parts can be
taken off and any step started again; a plan of the building shows under the panel.
Version 1.8: dragging no longer slides the photo (Shift + wheel-drag does) - a click is just a click again.
Version 1.9: pointed gables on the front of a roof (click their corners at the eaves and their peak - each is
built as a little gable-ended roof into the main one); 'Measure on a map' on the Sizes page, for the length and
depth; the 3D program keeps its view and panel window where they were left, warns when a part has only two
corners and no depth, saves the clicks as a readable file, and explains the steps more clearly.
Version 2.0: more than one photo of the building - from other corners (lined up, and tied to photo 1 by two of
the main building's corners) or straight on to a wall (its 4 corners clicked) - so every side can be done,
back and ends too; map sizes (front and depth) for every part.
Version 2.1: the extra photos are picked here, on the Photo page (with the thumbnails), and open in the 3D
program with the main one.
Version 2.2: Change the plan - a window of its own showing the plan, where the parts are moved and resized
with the mouse (like resizing a window), lining up with the walls; a part can be copied to the other end of
the building (mirrored, windows and doors too), sizes typed, parts taken off, and it all undone.
Version 3.0: the clicking round the building can be done here in IngeTrazo - no 3D program needed. The photo
opens big in a window of its own, with the same 7 steps beside it (and the plan under them), a magnifier for
the corners, and Send to Build. The 3D program's way is still there (Match it page); either can carry on
where the other left off.
Version 3.1: the clicking window can go full screen (Full screen button, or F11; Esc or the button again to come
back) and has a maximise button; the steps panel fits without sliding sideways.
Version 3.2: a wing or bay hidden on the photos can be put on the plan and dragged into place there (moved, and
resized by its edges and corners, lining up with the other walls) - it shows on the photo as it moves; Copy to
the other end makes a mirror copy the same height; heights can be typed for a part that can't be clicked; the
magnifier stays in the bottom left corner.
Version 3.3: corners can be clicked part way up the walls, where it's clearer (the top of a plinth, the window
sills - a level line all the way round), then the ground straight below one of them; a wing or bay can use the
same height as the main building's.
Version 3.4: with corners clicked up the wall, a dashed line runs straight down from each one (truly upright in
the photo), to show where the ground below it is.
Version 3.5: the height of the line can be taken anywhere the bottom of the wall is clear - click a point on
the line, then the foot of the wall straight below it (the corners' own feet are often hidden).
Version 3.6: Backspace / Delete / Ctrl+Z on the photo work even where IngeTrazo has those keys for itself; a
Take the last click off button; Set the height starts again from its first click each time it's pressed.
Version 3.7: the photo's keys are caught before IngeTrazo's own (Backspace now takes a click off); Take the last
click off undoes the very last click, whatever step it was on; the two Set the height clicks can be either way
round (the lower one is taken as the foot of the wall).
Version 3.8: on step 3, with corners clicked up the wall, the camera's eye-level line is shown dashed (a level
line there runs flat across the photo and can't be measured), with a warning if the corners are on it.
Version 3.9: Ctrl+Z undoes anything in the clicking window - clicks, Start this step again, parts or photos taken
off, plan drags and settings - and Ctrl+Y (or Ctrl+Shift+Z, or the Bring it back button) brings it back.
Version 4.0: Set the height is one click - the foot of the front wall anywhere it's clear between corners 1 and 2;
the point on the line above it is found from the corners (shown on the photo).
Version 4.1: once a part's corners are all clicked, a click on the photo no longer starts them again - with
corners up the wall it goes straight on to the height (the foot of the front wall); to click the corners again,
use Undo or Clear this part's corners.
Version 4.2: Start from the front - a face-on photo of the front does the length, height, roof top, gables,
windows, doors, bays and wings in one go (straightened from the wall's 4 corners and its length); the depth
comes from the corner photo (as clicked the other way), a straight-on photo of a side wall, or a map.
Version 4.3: Start from the front - the scale can come from anything on the front you know the size of (a door's
height, a bench): click its two ends and type its size, instead of typing the front's length.
Version 4.4: Start from the front - hold Shift while clicking to line the click up exactly level with, or
straight above / below, the one before it.
Version 4.5: a How to click drawing for every step of both windows, the dot to click next lit up; the steps'
words cut to one short line (the full wording when the mouse is over it).
Version 4.6: Start from the front - windows and doors of any shape (pointed, arched...): All round - click 6 or
more points round it, then Finish (or Enter / right-click); it goes to Openings as its own outline.
Version 4.7: Start from the front - windows, doors, bays and wings snap to line up with the ones already done
(sills, tops, sides, the same width and height), a dashed guide showing it (hold Ctrl not to); boxes are drawn
with their real tops (round, segmental).
Version 4.8: Start from the front - bays and wings come before the windows and doors (step 3, then 4), so the
bays are there for their windows to go on.
Version 4.9: Start from the front - snapping only reaches a few pixels on screen, so zoomed in it hardly pulls
at all and clicks go where they're put.
Version 5.0: Ctrl (not Alt) stops the snapping and lining up, everywhere; Alt on its own no longer opens a
Windows menu while the clicking windows are in front.
Version 5.1: Undo / Bring it back (Ctrl+Z / Ctrl+Y) keep the zoom - the photo's only fitted again when it
changes.
Version 5.2: Start from the front - a bay's shape: Square, Splayed (angled sides - click or type its flat front)
or Round (a bow); its windows go on whichever face they're on.
Version 5.3: Start from the front - a window on a bay stops at the corners of the face it's on (it can't hang
over); the plan says when a splayed bay's flat front still needs clicking.
Version 5.4: Start from the front - Make the other bays the same as this one: its shape, flat front, how far it
comes out and its roof, copied to the other bays (each keeps its own place and size along the front).
Version 5.5: Start from the front - the depth from the corner photo is found in another job too (the one with
the same building's photos, the newest that's done), or picked with Use another job's corner photo.
Version 5.6: Use another job's corner photo shows a list of the jobs - a picture of each one's photo, when it was
clicked, and whether its corners are done (with the depth it gives) - instead of a folder to find.
Version 5.7: Start from the front - the main roof's height can come from the front gables' pitch (the ridge is
set back, so a face-on photo makes it look low), the clicked top, or a pitch typed; a bay side that can't be seen
gets the same windows as the side that can (mirrored), and bays the same shape share their side windows.
Version 5.8: Start from the front - the roof's pitch from a side photo: draw a triangle over the gable end (left
eave, ridge, right eave - drag its corners to fine-tune), for a roof that doesn't stand out on the front photo.
Version 5.9: Start from the front - tabs above the photo, one for each photo, to flick between them. The tab with
a dot is the photo this step clicks on; the others are for a look (or, for a side photo not clicked yet, use it).
Version 6.0: Start from the front - picking a different front photo no longer loses the front's 4 corners: each
photo keeps its own, and they come back when you pick it again. The same photo isn't listed twice (/ and \\).
Version 6.1: Start from the front - a gable's 3 clicks can be in any order (the highest is its peak), so gables
clicked eave, peak, eave come out right; doors and windows clicked all round go the right way round.
Version 6.2: a door clicked all round sits flat on the floor - every point near its bottom goes down to the
floor, not just the lowest one (a bottom a hair off level made the wall come out in a tangle).
Version 6.3: a hip roof on a bay (or any part against the main building) is a lean-to with hipped ends - level
along the main wall, sloping down at the front and both sides. Roof gables on the front stand at the main eaves,
and the main roof's overhang is cut away in front of each one, so the gable goes straight up from the wall.
Version 6.4: roof gables have no overhang down their sides (their barge boards stop at the main eaves); a bay's
roof overhangs 150 mm, not the main roof's overhang; a splayed bay's two sides get the same windows - the side
with the bigger ones (the one seen best) mirrored onto the other.
Version 6.5: Start from the front - the roof step has the eaves and verge overhangs (no need to go into Floor
Plan), and a tick for fascia, barge boards and soffits: made by 3D Subframe (its board sizes) when it's built -
fascia and soffits along the eaves (not across the gables), barge boards and finials up every gable.
Version 9.1: Start from the front - after Undo takes a bay off, clicking the flat front's 2 corners is switched
off again, so the next clicks start a new bay (they went nowhere before).
Version 9.2: the bay settings on the right follow the bay picked in the list again (9.1 stopped them updating).
Version 9.3: Start from the front - bays and wings are a guided job, one thing at a time: Add a bay, pick its
shape, click it (a splayed bay: bottom left, left post, right post, top right - its flat front comes from the
posts), then how far it comes out and its roof, Done. Add another the same: just click where it is.
Version 9.4: clearer words when adding another bay the same (which bay it copies, and that you're showing where
the new one is).
Version 10.0: Start from the front, made simpler for beginners (step 1 first): a yellow box says the one thing
to do next in a few words, the front's corners are asked for one at a time, the length is one box (or measure
from something you know), the rest is tucked under More settings, and Next goes green when the step's done.
Version 10.1: Start from the front starts a fresh one (a new job); Carry on from the front opens the last one.
Version 10.2: step 1's words for measuring from something you know match its box (How long is it?).
Version 10.3: step 2 (the roof) made simple the same way: pick the roof's shape from big buttons, say if there
are pointed gables on the front and click them one point at a time, then (only if needed) click the top of the
roof. The rest is under More settings.
Version 10.4: windows and doors made simple: big buttons for Window / Door and the shape of its top, and the
yellow box says which corner to click next (top left, then bottom right), with a count of what's marked.
Version 10.5: an odd-shaped window or door clicked all round finishes by itself when you click back on its
first point (or right-click, or Enter).
Version 10.6: windows and doors page packed together at the top (not spread down the panel), the count shown
once, and the yellow box says bay windows are marked too.
Version 10.7: the depth made simple: pick how from big buttons - the corner photo (new: click 6 corners on it
right here, no other job needed), a straight-on side photo, or typed from a map - then the yellow box takes you
through the clicks. Photos can be mixed: the front for the face, any photo for the depth.
Version 10.8: after a restart, the Carry on button for your last job is coloured green so it stands out.
Version 10.9: the corner photo depth measures from the roof-edge corners, so the lower 3 clicks needn't be on
the ground - any height will do (the window sills, where an extension's roof meets the wall) as long as
they're all at the same height, each straight below its top click.
Version 11.0: a new way to get the roof's height (step 2, More settings): as high as the tallest front gable's
peak - on a face-on photo the gables are in the front wall, so their peaks measure true.
Version 11.1: no gables on the front? The roof's height can come from the corner photo: its 6 corners (the same
ones as the depth) and one click on the peak of the end wall. With no gables it's offered first.
Version 11.2: the How to click picture shows the corner photo's 6 corners (and the end wall's peak) with the
next one to click lit up.
Version 11.3: step 6 packed together, with a big plan right in it: click a bay on the plan to pick it, then change
its shape, how far it comes out, swap it with the other bay or take it off - no scrolling down.
Version 11.4: the Build it button is green when there's a building ready to build.
Version 11.5: bays and wings are numbered left to right along the front (Bay 1 is the left one), whatever order
they're clicked in.
Version 11.6: step 6 - Even up the angled sides: centres a bay's flat front (same width) so both angled sides
are the same length. Also Make the others like this one, right there on the plan.
Version 11.7: line up windows (step 4): Line windows up, click the good one, Shift + click the others, then a
box asks how - tops level, bottoms level, the same size, evenly spaced.
Version 11.8: Move windows (after building, the model changing as you go): size the first window, Shift + click
the others (they light up), then Make these like the first one - a pop-up asks size, tops, bottoms, spacing.
Version 11.9: a door with a window (fanlight) marked right on top of it becomes one doorway with that window's
top - before, the door was left out for overlapping it.
Version 12.0: moving on the model - the picked window's width and height in the little window to resize it,
Shift + click windows to gather them (they light up) then Line these up in one go, and shorter words there.
Version 12.1: the windows editing window made small and simple: the picked window's width and height (also
while carrying it), Match (a drop-down), Match these, Match all on this wall, Undo, Finished.
Version 12.2: stretch a window by eye on the model - click near its edge or corner, move, click to let go (its
middle still moves it). The size boxes are gone again: just Match, Match these, Undo, Finished.
Version 12.3: moving on the model - clicking in the middle of a window (through the hole, onto what's behind)
finds that window, so it can be picked up and moved from its middle.
Version 12.4: the little Windows box opens at the top right of the 3D view (not over the building), and Move
windows opens smaller at the right, so the building shows beside it as you drag.
Version 12.5: moving on the model uses the line from your eye through the mouse: clicking anywhere on a window
(its middle too) picks that one, and a carried window slides exactly along its wall; stretching an edge
follows the mouse on the wall and goes in 25 mm steps (or snaps to another window's edge).
Version 12.6: Let go is back in the Windows box (and Esc does it), so you can start on another window.
Version 12.7: Match - Same size and place: each one goes to the same spot on its own wall as the first (centred
if it's centred - good for a bay's sides), the same size and height. It's the first choice now.
Version 12.8: moving on the model doesn't use the 3D program's snapping (it pulled clicks onto the wrong
window) - it goes by exactly where you click.
Version 12.9: Carry on and Build it always showing at the bottom of the main window, whichever page is open.
Version 13.0: matching and lining up leave doors alone (unless the first one picked is a door) - a door had
been made window-sized and lifted off the floor.
Version 13.1: works both ways - windows and doors moved or resized on the model (or in Move windows) move
their boxes on the photo too, so Carry on shows them where they are now and Send to Build keeps them.
Version 13.2: the steps panel packed together - each step only as tall as it needs (no big gaps), the small
plan only on the bays and depth steps, so the bottom fits on the screen.
Version 13.3: the step's part of the panel is exactly as tall as what's in it, so the buttons sit right under it.
Version 13.4: a live 3D preview of the building at the bottom of the steps panel - it builds up as you click
(walls, roof, gables, bays, windows and doors); drag to turn it, wheel to zoom, double-click to straighten.
Version 13.5: the 3D preview shows the whole building before the depth is set, with a guessed depth (it says so);
bays drawn in front of the main building whenever you can see their wall, and the right way out.
Version 13.6: the preview finds the main wall each bay stands against (not the overall size), so the far bay
doesn't vanish behind the building at an angle; it also logs the shapes once, to help if it ever goes wrong.
Version 13.7: the preview trims windows to fit their wall (like the real build), so bay windows don't poke round
the corners.
Version 13.8: the preview slides a window back onto its wall keeping its size (as the real build does), and only
trims what's still too wide - so a bay's windows sit where they do on the model.
Version 13.9: the preview keeps an even strip of wall each side of a window (a frame), so a bay's windows don't
run into each other round the corners, and a cream frame drawn round each window and door.
Version 14.0: Build it writes the bays and their windows to the log (to track down a bay window left out).
Version 14.1: a bay window moved or lined up on the model keeps that place when you Send to Build again from
Carry on (remembered with its box) - unless you change its box on the photo.
Version 14.2: Keep the model's window places - one button in the main window that takes the windows' places from
the last time they were moved on the model (saved with the job) into the photo, without building again.
Also 'Clear out old jobs' - deletes every old job folder in the work folder, keeping only the one you're on.
Version 14.3: Keep the model's window places works with places saved by older versions too - it opens the front
and matches each window on the model to its box on the photo by where it is.
Version 14.4: a traced window (pointed top and so on) is squared up - its sides upright, its bottom level and
its top even both sides - so the glazing bars put in it stand straight.
"""

import os
import sys
import copy
import json
import math
import re
import time
from tools.base import Tool
from PySide6.QtCore import Qt, QPointF, QRectF, QSize, QTimer
from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QDoubleSpinBox, QSpinBox, QCheckBox, QComboBox,
    QMessageBox, QPushButton, QInputDialog, QListWidget, QListWidgetItem, QLineEdit, QLabel, QWidget,
    QTabWidget, QFileDialog
)

PLUGIN_NAME = "3D Photo to Building"
VERSION = "14.4"             # shown in the window title, so you can tell which file is loaded

SCALE = 0.001               # IngeTrazo stores metres; the building is worked out in real-world mm
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".ingetrazo_photo_to_building.json")
PRESET_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Presets", "Photo to Building")
WORK_DIR = os.path.join(os.path.expanduser("~"), "Documents", "IngeTrazo Photo Buildings")
DEFAULT_PICTURES = os.path.join(os.path.expanduser("~"), "Pictures")
PICTURE_TYPES = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp")
RESULT_NAME = "building from photo.json"

# the size you know - the letters are the ones on the Key drawing
KNOWN = [('wall1', "A   Front wall (corner 1 to corner 2)"), ('wall2', "B   Side wall (to corner 3)"),
         ('eaves', "C   Height to the eaves"), ('ridge', "D   Height to the top of the roof"),
         ('door_h', "E   Height of the first door"), ('win_w', "F   Width of the first window"),
         ('win_h', "G   Height of the first window")]
ROOFS = [("Gable - ridge along the front (1-2)", 'gable_len'), ("Gable - gable end at the front (1-2)", 'gable_across'),
         ("Hip - slopes on every side", 'hip'), ("Lean-to - one slope", 'mono'), ("Flat roof", 'flat'),
         ("No roof", 'none')]
ROOF_LOW = [("The low side at the front", 'front'), ("The low side at the back", 'back')]
SHAPES = [("Rectangle - click 3 corners", 'rect'), ("My own corners - click every one", 'own')]

DEFAULTS = dict(known_what='door_h', known_mm=2000.0, storeys=2, roof='gable_len', roof_low='front',
                shape='rect', depth_mm=0.0, wall_t=230.0, snap_doors=True,
                one_group=True)
SIZE_KEYS = ('known_mm', 'depth_mm', 'wall_t')
BUILTIN_PRESETS = {
    "House - door 2000 mm high": dict(DEFAULTS),
    "Victorian terrace - door 2100 mm": dict(DEFAULTS, known_mm=2100.0, wall_t=230.0),
    "Bungalow - door 1980 mm": dict(DEFAULTS, known_mm=1980.0, storeys=1, roof='hip'),
    "Station building - door 2400 mm": dict(DEFAULTS, known_mm=2400.0, storeys=1, wall_t=350.0),
    "Goods shed - eaves 5000 mm": dict(DEFAULTS, known_what='eaves', known_mm=5000.0, storeys=1, wall_t=350.0),
    "Lean-to - door 2000 mm": dict(DEFAULTS, storeys=1, roof='mono', wall_t=230.0),
}
# what the window remembers between times (besides the values)
KEEP = {'where': 'here', 'match_full': False, 'folder': DEFAULT_PICTURES, 'photo': '', 'blender': '', 'work_dir': WORK_DIR, 'tab': 0,
        'remember_tab': True, 'last_preset': None, 'preset_order': [], 'last_job': '', 'last_built': '', 'place': '',
        'extra_photos': []}


def load_settings():
    d = dict(DEFAULTS)
    d.update(KEEP)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            got = json.load(f)
        if isinstance(got, dict):
            d.update({k: v for k, v in got.items() if k in d})
    except Exception:
        pass
    return d


def save_settings(**kw):
    d = load_settings()
    d.update(kw)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)
    except Exception:
        pass


def _safe_name(name):
    return "".join(c if c.isalnum() or c in " -_()" else "_" for c in name).strip() or "preset"


def load_presets():
    out = {}
    try:
        for fn in sorted(os.listdir(PRESET_DIR)):
            if fn.lower().endswith(".json"):
                try:
                    with open(os.path.join(PRESET_DIR, fn), "r", encoding="utf-8") as f:
                        d = json.load(f)
                    if isinstance(d, dict):
                        out[d.get('name') or fn[:-5]] = d
                except Exception:
                    pass
    except Exception:
        pass
    return out


def save_preset_file(name, values):
    os.makedirs(PRESET_DIR, exist_ok=True)
    d = {'name': name}
    d.update({k: values[k] for k in DEFAULTS if k in values})
    with open(os.path.join(PRESET_DIR, _safe_name(name) + ".json"), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)


def delete_preset_file(name):
    path = os.path.join(PRESET_DIR, _safe_name(name) + ".json")
    if os.path.exists(path):
        os.remove(path)


# ---------------------------------------------------------------------------
# The other plugins this one works with (found among the ones IngeTrazo has loaded)
# ---------------------------------------------------------------------------
def plugin_module(stem, needs=None):
    for name, mod in list(sys.modules.items()):
        if mod is not None and (name == stem or name.endswith("_" + stem)) and (needs is None or hasattr(mod, needs)):
            return mod
    return None


def floor_plan():
    return plugin_module("ed3d_floor_plan", "build_plan")


def openings():
    return plugin_module("ed3d_openings", "cut_wall")


def toolbar():
    return plugin_module("ed3d_plugins_toolbar", "project_next")


# ---------------------------------------------------------------------------
# Finding the 3D program (the same way 3D Realistic Wall does)
# ---------------------------------------------------------------------------
def _version_key(path):
    import re
    nums = re.findall(r"\d+", os.path.basename(os.path.dirname(path)))
    return tuple(int(n) for n in nums[:3]) or (0,)


def _main_exe(prog):
    """The launcher hands over to the main program: start that one."""
    if prog and os.path.basename(prog).lower().startswith("blender"):
        main = os.path.join(os.path.dirname(prog), "blender.exe" if os.name == 'nt' else "blender")
        if os.path.isfile(main):
            return main
    return prog


def find_blender(saved=""):
    """The 3D program to open: the one set here, else the one 3D Realistic Wall uses, else the newest one
    installed in the usual places. '' if none is found."""
    if saved and os.path.isfile(saved):
        return _main_exe(saved)
    for other in (".ingetrazo_realistic_wall.json", ".ingetrazo_pieces_in.json"):
        try:
            with open(os.path.join(os.path.expanduser("~"), other), "r", encoding="utf-8") as f:
                d = json.load(f)
            p = d.get('blender') or d.get('open_prog') or ''
            if p and os.path.isfile(p) and "blender" in os.path.basename(p).lower():
                return _main_exe(p)
        except Exception:
            pass
    found = []
    bases = [os.environ.get(k, "") for k in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432")]
    bases.append(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"))
    for base in [b for b in bases if b]:
        bf = os.path.join(base, "Blender Foundation")
        try:
            for d in os.listdir(bf):
                exe = os.path.join(bf, d, "blender.exe")
                if os.path.isfile(exe):
                    found.append(exe)
        except Exception:
            pass
    found.sort(key=_version_key, reverse=True)
    steam = os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Steam", "steamapps", "common", "Blender",
                         "blender.exe")
    if os.path.isfile(steam):
        found.append(steam)
    if not found:
        try:
            import shutil
            w = shutil.which("blender")
            if w:
                found.append(w)
        except Exception:
            pass
    return found[0] if found else ""


def make_job(photo, values, work_dir, extras=None):
    """A new folder with everything the 3D program needs. Returns (job file, script file, folder)."""
    stamp = time.strftime("%Y-%m-%d %H%M%S")
    name = os.path.splitext(os.path.basename(photo))[0][:40]
    folder = os.path.join(work_dir, "%s %s" % (_safe_name(name), stamp))
    os.makedirs(folder, exist_ok=True)
    job = {'photo': photo, 'fresh': True, 'extra_photos': list(extras or []),
           'out_json': os.path.join(folder, RESULT_NAME),
           'out_blend': os.path.join(folder, "photo to building.blend")}
    for k in ('known_what', 'known_mm', 'storeys', 'roof', 'roof_low', 'shape', 'depth_mm'):
        job[k] = values[k]
    jp = os.path.join(folder, "job.json")
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(job, f, indent=1)
    sp = os.path.join(folder, "photo_to_building_blender.py")
    with open(sp, "w", encoding="utf-8") as f:
        f.write(BLENDER_SCRIPT)
    return jp, sp, folder


def reopen_job(folder, extras=None):
    """Opens a job again where it was left (its saved file, with the clicks). Returns (job, script, blend)."""
    jp = os.path.join(folder, "job.json")
    with open(jp, "r", encoding="utf-8") as f:
        job = json.load(f)
    job['fresh'] = False
    if extras is not None:                                # photos added here since: the 3D program adds them
        job['extra_photos'] = list(extras)
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(job, f, indent=1)
    sp = os.path.join(folder, "photo_to_building_blender.py")
    with open(sp, "w", encoding="utf-8") as f:
        f.write(BLENDER_SCRIPT)                       # the newest version of the clicking
    return jp, sp, job.get('out_blend', '')


def open_blender(prog, script, job, blend=""):
    import subprocess
    prog = _main_exe(prog)
    if not prog or not os.path.isfile(prog):
        return "The 3D program wasn't found - set where it is on the Program page.", True
    args = [prog]
    if blend and os.path.isfile(blend):
        args.append(blend)
    args += ["--python", script, "--", job]
    try:
        subprocess.Popen(args, cwd=os.path.dirname(job))
    except Exception as e:
        return "Couldn't open the 3D program: %s" % e, True
    return ("Opening the 3D program with the photo... Its Photo to Building panel (press N) takes you through "
            "it, step by step. Click Send to IngeTrazo there when you've finished."), False


# ---------------------------------------------------------------------------
# What comes back: filling in Floor Plan, and cutting the openings
# ---------------------------------------------------------------------------
def save_json(path, data):
    """Saved whole or not at all: written to a spare file first, then swapped in (a half-written file can't be
    left behind to stop the building loading next time)."""
    txt = json.dumps(data, indent=1, default=lambda o: list(o) if isinstance(o, (tuple, set)) else str(o))
    tmp = path + ".saving"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(txt)
    os.replace(tmp, path)


def read_result(path):
    with open(path, "r", encoding="utf-8") as f:
        r = json.load(f)
    if not isinstance(r, dict) or len(r.get('corners') or []) < 3:
        raise ValueError("That file doesn't have a building in it.")
    if not isinstance(r.get('parts'), list) or not r['parts']:     # sent by version 1.3 or before: one part
        r['parts'] = [dict((k, r[k]) for k in ('corners', 'eaves', 'ridge', 'roof', 'roof_low', 'storeys', 'pitch',
                                                'length', 'width') if k in r)]
        r['parts'][0]['name'] = "Main building"
    for o in r.get('openings') or []:
        o.setdefault('part', 0)
    return r


def corners_text(r):
    return "; ".join("%g, %g" % (round(x, 1), round(y, 1)) for x, y in r['corners'])


OPPOSITE = {'front': 'back', 'back': 'front', 'left': 'right', 'right': 'left'}


def part_roof(part, fp):
    """The part's roof in Floor Plan's terms. A part's 'front' is its own wall 1-2: a wing on the end of the
    building faces left or right, so its ridge 'along the front' runs across, and so on."""
    roof = part.get('roof', 'gable_len')
    low = part.get('roof_low', 'front')
    cs = part['corners']
    dx, dy = cs[1][0] - cs[0][0], cs[1][1] - cs[0][1]
    L = math.hypot(dx, dy) or 1.0
    try:
        side = fp.side_name((dx / L, dy / L))
    except Exception:
        side = 'front'
    lengthwise = side in ('front', 'back')
    if roof == 'gable_len':
        roof = 'gable_len' if lengthwise else 'gable_across'
    elif roof == 'gable_across':
        roof = 'gable_across' if lengthwise else 'gable_len'
    return roof, (side if low == 'front' else OPPOSITE.get(side, 'back'))


BAY_EAVES = 150.0      # mm a bay's (or porch's) roof overhangs


def back_wall(cs):
    """The wall of a part that stands against the main building: the one furthest back from its front (wall 1-2)."""
    a, b = cs[0], cs[1]
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L          # into the part (its corners go anticlockwise)
    n = len(cs)
    return max(range(n), key=lambda i: ((cs[i][0] + cs[(i + 1) % n][0]) / 2.0 - a[0]) * nx +
               ((cs[i][1] + cs[(i + 1) % n][1]) / 2.0 - a[1]) * ny)


def cut_eaves_for_gables(fp, pieces, part, gables):
    """The roof's overhang taken away in front of each roof gable on this part's walls, so the gable's face
    goes straight up from the wall (as on the real thing, the eaves stop either side of it)."""
    cs = part['corners']
    n = len(cs)
    cuts = []
    for g in gables:
        i = int(g.get('wall', 0)) % n
        a, b = cs[i], cs[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        nn = (-u[1], u[0])
        a = (a[0] + nn[0] * 2.0, a[1] + nn[1] * 2.0)     # 2 mm behind the wall's face: no flicker with the gable
        cuts.append((a, u, nn, float(g['s0']), float(g['s1'])))
    if not cuts:
        return pieces, 0
    out, done = [], 0
    for pc in pieces:
        sol = getattr(pc, 'custom', None)
        if pc.kind != 'roof' or sol is None or len(getattr(sol, 'faces', [])) < 2:
            out.append(pc)
            continue
        top = sol.faces[0]
        pl = _plane3(top)
        bot = sol.faces[1]
        if pl is None or not bot:
            out.append(pc)
            continue
        depth = (pl[0] * bot[0][0] + pl[1] * bot[0][1] + pl[2]) - bot[0][2]
        regs = [[(q[0], q[1]) for q in pc.poly]]
        for a, u, nn, s0, s1 in cuts:
            nxt = []
            for reg in regs:
                keep = fp.clip_half(reg, a, nn)                        # behind the wall's face
                front = fp.clip_half(reg, a, (-nn[0], -nn[1]))         # the overhang in front of it
                if keep and len(keep) >= 3:
                    nxt.append(keep)
                if not front or len(front) < 3:
                    continue
                q0 = (a[0] + u[0] * s0, a[1] + u[1] * s0)
                q1 = (a[0] + u[0] * s1, a[1] + u[1] * s1)
                for side in (fp.clip_half(front, q0, (-u[0], -u[1])), fp.clip_half(front, q1, u)):
                    if side and len(side) >= 3:
                        nxt.append(side)
            regs = nxt
        regs = [r_ for r_ in (fp.clean(r_) for r_ in regs) if r_ and abs(fp.area2(r_)) > 100.0]
        if len(regs) == 1 and abs(abs(fp.area2(regs[0])) - abs(fp.area2(pc.poly))) < 1.0:
            out.append(pc)                                             # nothing in front of a gable here
            continue
        done += 1
        for k, reg in enumerate(regs):
            zs = [pl[0] * x + pl[1] * y + pl[2] for x, y in reg]
            np_ = fp.Piece(pc.name if k == 0 else "%s (%d)" % (pc.name, k + 1), 'roof', pc.storey, reg,
                           min(zs) - depth, max(zs))
            np_.custom = fp.slab_on_plane(reg, pl, depth)
            out.append(np_)
    return out, done


def _plane3(face):
    """z = gx*x + gy*y + c through a flat face's corners (not upright), or None."""
    for i in range(len(face)):
        for j in range(i + 1, len(face)):
            for k in range(j + 1, len(face)):
                (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = face[i], face[j], face[k]
                d = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
                if abs(d) < 1e-3:
                    continue
                gx = ((z2 - z1) * (y3 - y1) - (z3 - z1) * (y2 - y1)) / d
                gy = ((x2 - x1) * (z3 - z1) - (x3 - x1) * (z2 - z1)) / d
                return gx, gy, z1 - gx * x1 - gy * y1
    return None


def floor_plan_values(r, values, fp, extra=None):
    """Floor Plan's settings for one part of the building in the photo: your usual ones (the last used in
    Floor Plan), with the outline, height, floors and roof from the photo."""
    v = dict(fp.DEFAULTS)
    last = None
    try:
        last = fp._ui_settings().get('last_values')
    except Exception:
        last = None
    if isinstance(last, dict):
        v.update({k: last[k] for k in fp.DEFAULTS if k in last})
    else:
        try:
            v.update(fp.BUILTIN_PRESETS["Two-storey house 7.5 x 6 m"])
        except Exception:
            pass
    storeys = max(1, int(r.get('storeys') or values.get('storeys') or 1))
    for key in ('eave_over', 'verge_over'):              # set on the photo's roof step
        if values.get(key) is not None:
            v[key] = float(values[key])
    v.update(shape='custom', corners_text=corners_text(r), length=float(r.get('length') or 0.0),
             width=float(r.get('width') or 0.0), wall_t=float(values.get('wall_t') or 230.0),
             height_mode='divide', total_h=float(r['eaves']), storeys=storeys,
             storey_heights=", ".join("%g" % round(r['eaves'] / storeys, 1) for _ in range(storeys)),
             cross_x='', cross_y='', gables=False, split_len=float(v.get('split_len') or 0.0))
    if extra:
        v.update(extra)
    roof = r.get('roof', 'gable_len')
    if roof == 'none':
        v['roof'] = False
    else:
        v['roof'] = True
        v['roof_type'], v['roof_low'] = part_roof(r, fp)
        hipped_lean = roof == 'hip' and r.get('against') and len(r.get('corners') or []) >= 3
        if hipped_lean:
            v['roof_type'], v['roof_gables'] = 'pick', str(back_wall(r['corners']) + 1)
            v['verge_over'] = 0.0                         # its top edge stops at the main wall
        if r.get('against') and roof in ('hip', 'mono'):
            v['eave_over'] = min(float(v.get('eave_over') or 0.0), BAY_EAVES)       # a bay's roof: a small overhang
        if roof != 'flat':
            v['roof_pitch'] = float(r.get('pitch') or v.get('roof_pitch') or 40.0)
            if r.get('ridge') and r['ridge'] > r['eaves'] and not hipped_lean:
                try:
                    ang, _why = fp.solve_roof_angle(v, float(r['ridge']))
                    if ang:
                        v['roof_pitch'] = ang
                except Exception as e:
                    print("%s: roof pitch from the photo's ridge: %s" % (PLUGIN_NAME, e))
        elif not (0 < float(v.get('roof_fall') or 0) < 30):
            v['roof_fall'] = 3.0
    if v.get('floor_style') == 'stacked' and float(v.get('floor_t') or 0) <= 0:
        v['floor_t'] = 200.0
    if extra:
        v.update(extra)
    return v


def _scene_tops(scene, op):
    return [t for t in op._items(getattr(scene, 'groups', None))]


def building_middle(r):
    """The middle of a part as Floor Plan builds it (at the origin), in the model (metres): each wall's
    outside is the side away from it."""
    xs = [c[0] for c in r['corners']]
    ys = [c[1] for c in r['corners']]
    return ((min(xs) + max(xs)) / 2.0 * SCALE, (min(ys) + max(ys)) / 2.0 * SCALE, float(r['eaves']) / 2.0 * SCALE)


def outside_walls(scene, tops, op, centre_w):
    """Every plain wall in these groups: [dict(group, mesh, m, inv, wall)], each wall's front the side away
    from centre_w (the middle of the building)."""
    out = []
    for t in tops:
        for g, m in op._placements(t):
            mesh = getattr(g, 'mesh', None)
            if mesh is None or not op._items(getattr(mesh, 'faces', None)):
                continue
            name = str(getattr(g, 'name', '') or '').lower().split(" - ")[-1]
            if any(w_ in name for w_ in op._NOT_WALLS):
                continue
            try:
                centre, up, inv = op._local(m, centre_w)
                w = op.read_wall(op._faces_of(mesh), centre, up, False)
            except Exception:
                continue
            o0 = op._wmap(m, op.to3(w, 0.0, w.y0, 0.0))
            o1 = op._wmap(m, op.to3(w, 0.0, w.y0, 1000.0))
            nx, ny = o1[0] - o0[0], o1[1] - o0[1]
            nl = math.hypot(nx, ny) or 1.0
            out.append(dict(group=g, mesh=mesh, m=m, inv=inv, wall=w, bottom=o0[2], n=(nx / nl, ny / nl),
                            record=op._has_record(g), name=str(getattr(g, 'name', '') or 'A wall')))
    return out


def plan_openings(r, ops_in, walls, op, snap_doors=True, names=None):
    """Where each window and door of one part goes: {id(wall): (wall dict, [(name, poly)])}, problems.
    names: the numbers already given (windows and doors are numbered across the whole building)."""
    corners = r['corners']
    n = len(corners)
    zref = min((w['bottom'] for w in walls), default=0.0)
    per, problems = {}, []
    for o, name in zip(ops_in, names or ["Opening %d" % (k + 1) for k in range(len(ops_in))]):
        kind = 'door' if o.get('kind') == 'door' else 'window'
        i = int(o.get('wall', 0))
        if not 0 <= i < n:
            problems.append("%s: no wall %d" % (name, i + 1))
            continue
        a, b = corners[i], corners[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        outward = (uy, -ux)                               # the outline runs round anticlockwise

        def world(s, z):
            return ((a[0] + ux * s) * SCALE, (a[1] + uy * s) * SCALE, zref + z * SCALE)
        s0, s1, z0, z1 = float(o['s0']), float(o['s1']), float(o['z0']), float(o['z1'])
        mid = world((s0 + s1) / 2.0, (z0 + z1) / 2.0)
        best = None
        for wd in walls:
            if wd['n'][0] * outward[0] + wd['n'][1] * outward[1] < 0.5:
                continue                                  # a wall facing the other way (a bay's back wall)
            w = wd['wall']
            lp = op._wmap(wd['inv'], mid) if wd['inv'] is not None else mid
            x, y, z = op.to2(w, lp)
            if abs(z) > 60.0:
                continue
            if not (-1.0 <= x <= w.length + 1.0 and w.y0 - 1.0 <= y <= w.y0 + w.height + 1.0):
                continue
            if best is None or abs(z) < best[0]:
                best = (abs(z), wd)
        if best is None:
            problems.append("%s: no plain wall where it goes (%.0f mm along wall %d)" % (name, (s0 + s1) / 2.0, i + 1))
            continue
        wd = best[1]
        if wd['record']:
            problems.append("%s: %s already has windows or doors built in - left out" % (name, wd['name']))
            continue
        w = wd['wall']
        if o.get('shape'):                                # traced (or a copy of a traced one): its own outline
            poly, trimmed = traced_poly(o['shape'], w, wd, world, op, kind, snap_doors)
            if poly is None:
                problems.append("%s is too small once it's fitted to %s - left out" % (name, wd['name']))
                continue
            if trimmed:
                problems.append("%s trimmed to fit inside %s" % (name, wd['name']))
            per.setdefault(id(wd['group']), (wd, []))[1].append((name, poly))
            continue
        pts = []
        for s, z in ((s0, z0), (s1, z1)):
            q = op._wmap(wd['inv'], world(s, z)) if wd['inv'] is not None else world(s, z)
            pts.append(op.to2(w, q)[:2])
        x0, x1 = sorted((pts[0][0], pts[1][0]))
        y0, y1 = sorted((pts[0][1], pts[1][1]))
        lo, hi = w.x_lo + 5.0, w.x_hi - 5.0
        top_room = w.y0 + w.height - 5.0
        trimmed = x0 < lo - 1.0 or x1 > hi + 1.0 or y1 > top_room + 1.0
        x0, x1 = max(x0, lo), min(x1, hi)
        y1 = min(y1, top_room)
        if kind == 'door' and snap_doors and y0 - w.y0 < 300.0:
            y0 = w.y0                                   # on the floor: a doorway cut up from the bottom
        elif kind == 'window' and y0 < w.y0 + 5.0:
            y0 = w.y0 + 5.0
            trimmed = True
        if x1 - x0 < 20.0 or y1 - y0 < 20.0:
            problems.append("%s is too small once it's fitted to %s - left out" % (name, wd['name']))
            continue
        top = o.get('top', 'square')
        wid, hgt = x1 - x0, y1 - y0
        rise = min(0.2 * wid, 0.4 * hgt)
        if top == 'round' and hgt < wid / 2.0 + 1.0:
            top = 'segment'
        try:
            poly = op.opening_poly(x0, y0, wid, hgt, top, rise)
        except Exception:
            poly = op.opening_poly(x0, y0, wid, hgt, 'square', 0.0)
        if trimmed:
            problems.append("%s trimmed to fit inside %s" % (name, wd['name']))
        per.setdefault(id(wd['group']), (wd, []))[1].append((name, poly))
    return per, problems


def traced_poly(shape, w, wd, world, op, kind, snap_doors):
    """A traced outline (along the wall, up it - mm) in the wall's own terms, fitted inside the wall.
    Returns (poly anticlockwise, trimmed) or (None, False) if there's nothing left of it."""
    pts = []
    for s, z in shape:
        q = op._wmap(wd['inv'], world(s, z)) if wd['inv'] is not None else world(s, z)
        x, y, _z = op.to2(w, q)
        pts.append([x, y])
    lo, hi = w.x_lo + 5.0, w.x_hi - 5.0
    top_room = w.y0 + w.height - 5.0
    ymin = min(p[1] for p in pts)
    door = kind == 'door' and snap_doors and ymin - w.y0 < 300.0
    trimmed = False
    for p in pts:
        if door and p[1] <= ymin + 150.0:
            p[1] = w.y0                                   # on the floor: a doorway cut up from the bottom
        nx, ny = min(max(p[0], lo), hi), min(p[1], top_room)
        if not door:
            ny = max(ny, w.y0 + 5.0)
        if abs(nx - p[0]) > 1.0 or abs(ny - p[1]) > 1.0:
            trimmed = True
        p[0], p[1] = nx, ny
    clean = []
    for p in pts:
        if not clean or abs(p[0] - clean[-1][0]) + abs(p[1] - clean[-1][1]) > 0.5:
            clean.append((p[0], p[1]))
    if len(clean) > 2 and abs(clean[0][0] - clean[-1][0]) + abs(clean[0][1] - clean[-1][1]) <= 0.5:
        clean.pop()
    if len(clean) < 3:
        return None, False
    a = 0.5 * sum(clean[i][0] * clean[(i + 1) % len(clean)][1] - clean[(i + 1) % len(clean)][0] * clean[i][1]
                  for i in range(len(clean)))
    if abs(a) < 400.0:                                    # under 20 x 20 mm
        return None, False
    if a < 0:
        clean.reverse()
    return clean, trimmed


def opening_names(r):
    """W1, W2... and D1, D2... as numbered in the 3D program (windows and doors each from 1)."""
    out, nw, nd = [], 0, 0
    for o in r.get('openings') or []:
        if o.get('name'):
            out.append(o['name'])
            continue
        if o.get('kind') == 'door':
            nd += 1
            out.append("Door %d" % nd)
        else:
            nw += 1
            out.append("Window %d" % nw)
    return out


def cut_openings(viewport, r, tops_by_part=None, snap_doors=True, recut=False):
    """Cuts the photo's windows and doors through the walls of each part, in one go (one Undo).
    tops_by_part: the groups each part was just built as (else the walls in the model are searched).
    Returns (message, bad)."""
    op = openings()
    if op is None:
        return "3D Openings isn't loaded - it's needed to cut the windows and doors.", True
    scene = getattr(viewport, 'scene', None)
    if scene is None:
        return "No model open.", True
    bays = bay_openings(r, float(load_settings().get('wall_t') or 230.0))
    if bays:
        r = dict(r)
        r['openings'] = list(r.get('openings') or []) + bays
    if not r.get('openings'):
        return "No windows or doors were clicked on the photo.", False
    saved = {}                                            # moving them: the walls as they were before cutting
    if recut:
        for key_, (g_, orig_) in list(WALL_ORIG.items()):
            saved[key_] = (g_, getattr(g_, 'mesh', None))
            try:
                g_.mesh = orig_
            except Exception:
                saved.pop(key_, None)

    def restore():
        for g_, cur_ in saved.values():
            try:
                g_.mesh = cur_
            except Exception:
                pass
        saved_done.append(True)
    saved_done, origs = [], []
    try:
        names = opening_names(r)
        per, problems = {}, []
        any_walls = False
        for pi, part in enumerate(r['parts']):
            mine = [(o, nm) for o, nm in zip(r['openings'], names) if int(o.get('part', 0)) == pi]
            if not mine:
                continue
            tops = (tops_by_part[pi] if tops_by_part and pi < len(tops_by_part) else None) or _scene_tops(scene, op)
            walls = outside_walls(scene, tops, op, building_middle(part))
            xs = [c[0] * SCALE for c in part['corners']]
            ys = [c[1] * SCALE for c in part['corners']]
            pad = 0.1 * max(float(part.get('length') or 0), float(part.get('width') or 0), 1000.0) * SCALE

            def near(wd):                                   # only this part's walls (others may be about)
                try:
                    q = op._wmap(wd['m'], op.to3(wd['wall'], wd['wall'].length / 2.0, wd['wall'].y0, 0.0))
                except Exception:
                    return True
                return min(xs) - pad <= q[0] <= max(xs) + pad and min(ys) - pad <= q[1] <= max(ys) + pad
            walls = [wd for wd in walls if near(wd)]
            if walls:
                ZREF[pi] = min(wd['bottom'] for wd in walls)
            if not walls:
                problems.append("%s: no plain walls found for its windows and doors" % part.get('name', 'A part'))
                continue
            any_walls = True
            got, probs = plan_openings(part, [o for o, _n in mine], walls, op, snap_doors, [nm for _o, nm in mine])
            problems += probs
            for key, (wd, ops) in got.items():
                per.setdefault(key, (wd, []))[1].extend(ops)
        if not any_walls:
            restore()
            return "No plain walls found to cut the windows and doors into.\n" + "\n".join(problems[:6]), True
        swaps, cut = [], 0
        for _k, (wd, ops) in per.items():
            try:
                faces = op._faces_of(wd['mesh'])
                holes, notches, probs = op.check_openings(wd['wall'], ops, {'top_keep': 0.0})
                problems += ["%s - %s" % (wd['name'], x) for x in probs]
                if not (holes or notches):
                    continue
                nm_, bad = op.make_mesh(op.cut_wall(faces, wd['wall'], holes, notches))
                if bad:
                    problems.append("%s: %d face%s couldn't be made - left as it was" % (wd['name'], bad,
                                                                                       "s" if bad > 1 else ""))
                    continue
                g_ = wd['group']
                swaps.append((g_, saved[id(g_)][1] if id(g_) in saved else wd['mesh'], nm_))
                origs.append((g_, wd['mesh']))
                cut += len(holes) + len(notches)
            except Exception as e:
                problems.append("%s: %s" % (wd['name'], e))
        restore()
        done_ = set(id(g_) for g_, _o, _n in swaps)
        for key_, (g_, cur_) in saved.items():                 # moved off a wall altogether: back to no hole there
            if key_ not in done_ and cur_ is not None and cur_ is not WALL_ORIG[key_][1]:
                swaps.append((g_, cur_, WALL_ORIG[key_][1]))
        if not swaps:
            return "No windows or doors were cut.\n" + "\n".join(problems[:12]), True
    except Exception:
        if not saved_done:
            restore()
        raise
    cmd, _ok = op.openings_command(swaps, [])
    try:
        viewport.history.execute(cmd)
    except Exception as e:
        return "Could not change the walls:\n%s" % e, True
    for g_, m_ in origs:
        WALL_ORIG[id(g_)] = (g_, WALL_ORIG[id(g_)][1] if id(g_) in WALL_ORIG else m_)
    try:
        viewport.notify_scene_changed()
    except Exception:
        pass
    msg = "Cut %d window%s and door%s through %d wall%s." % (cut, "" if cut == 1 else "s", "" if cut == 1 else "s",
                                                            len(swaps), "" if len(swaps) == 1 else "s")
    if problems:
        msg += "\n" + "\n".join(problems)
    return msg, False


def build_part(viewport, part, values, fp, scene, gables=None):
    """Builds one part with 3D Floor Plan. Returns (new top groups, message, bad)."""
    v = floor_plan_values(part, values, fp)
    try:
        p = fp.plan_params(v)
        outline = fp.make_outline(p)
        pieces, notes = fp.build_plan(p, outline)
    except ValueError as e:
        return [], "%s - Floor Plan: %s" % (part.get('name', 'A part'), e), True
    if part.get('against'):
        pieces = no_back_wall(pieces, part, float(v.get('wall_t') or 230.0))
        try:
            pieces = base_to_main(fp, pieces, part, values)
        except Exception as e:
            print("%s: %s's base not trimmed: %s" % (PLUGIN_NAME, part.get('name'), e))
    planes = roof_planes(pieces)
    tops = [pc.z1 for pc in pieces if pc.kind == 'wall' and getattr(pc, 'custom', None) is None
            and getattr(pc, 'prof', None) is None]
    WALL_TOP[id(part)] = max(tops) if tops else float(part.get('eaves') or 0.0)
    if gables and v.get('roof'):
        done = False
        try:                                              # an opening in the roof under each roof gable
            holes = []
            for g in gables:
                hs = gable_hole(gable_pieces(part, g, values, fp, planes), 0.0)
                if not hs:
                    raise ValueError("no footprint for a roof gable")
                holes += hs
            pieces = cut_roof_for_gables(fp, pieces, holes)
            done = True
        except Exception as e:
            print("%s: roof not opened under the roof gables: %s" % (PLUGIN_NAME, e))
        if not done:
            try:
                pieces, _n = cut_eaves_for_gables(fp, pieces, part, gables)
            except Exception as e:
                print("%s: eaves not cut for the gables: %s" % (PLUGIN_NAME, e))
    ROOF_PLANES[id(part)] = planes
    before = set(id(t) for t in fp._items(getattr(scene, 'groups', None)))
    n = fp.FloorPlanTool().add_to_scene(viewport, pieces, v.get('grouping', 'storeys'), 0.0)
    if n is None:
        return [], "Floor Plan couldn't add %s." % part.get('name', 'a part'), True
    new = [t for t in fp._items(getattr(scene, 'groups', None)) if id(t) not in before]
    nw = sum(1 for pc in pieces if pc.kind == 'wall')
    msg = "%s: %.0f x %.0f mm, %d floor%s, %.0f mm to the eaves, %d wall sections" % (
        part.get('name', 'Main building'), part.get('length', 0), part.get('width', 0), int(v['storeys']),
        "" if int(v['storeys']) == 1 else "s", float(part['eaves']), nw)
    if v.get('roof'):
        rt = dict((b, a) for a, b in ROOFS).get(part.get('roof'), part.get('roof') or '')
        msg += ", %s roof" % rt.split(" - ")[0].lower()
        if v.get('roof_type') != 'flat':
            msg += " at %.1f°" % float(v.get('roof_pitch') or 0)
    return new, msg + ".", False, v


BOARD_TOPS = []         # the boards just made: [(('part', i) or ('gable', i), their groups)]


def front_board(sol, r, g):
    """Is this board on the front of a roof gable (not along where it runs into the main roof)?"""
    try:
        cs = r['parts'][int(g.get('part', 0))]['corners']
        i = int(g['wall']) % len(cs)
        a, b = cs[i], cs[(i + 1) % len(cs)]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        ix, iy = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
        ts = [(q[0] / SCALE - a[0]) * ix + (q[1] / SCALE - a[1]) * iy for f_ in sol.faces for q in f_]
        return min(ts) < 300.0 and max(ts) - min(ts) < 600.0
    except Exception:
        return True


def nearest_wall(sol, cs):
    """Which wall of an outline (mm) a board (metres) is nearest to, by its middle seen from above."""
    pts = [q for f_ in sol.faces for q in f_]
    x = sum(q[0] for q in pts) / len(pts) / SCALE
    y = sum(q[1] for q in pts) / len(pts) / SCALE
    best, bi = None, 0
    n = len(cs)
    for i in range(n):
        a, b = cs[i], cs[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy or 1.0
        t = min(max(((x - a[0]) * dx + (y - a[1]) * dy) / L2, 0.0), 1.0)
        d = math.hypot(x - a[0] - dx * t, y - a[1] - dy * t)
        if best is None or d < best:
            best, bi = d, i
    return bi


def at_back(sol, part):
    """Is a board up against a bay's back (where it meets the main building)?"""
    cs = part.get('corners') or []
    if len(cs) < 3:
        return False
    i = back_wall(cs)
    a, b = cs[i], cs[(i + 1) % len(cs)]
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
    ds = [(q[0] / SCALE - a[0]) * nx + (q[1] / SCALE - a[1]) * ny for f_ in sol.faces for q in f_]
    return bool(ds) and max(ds) < 400.0


def reach_wall(bd, part):
    """A bay's side fascia and soffit carried on back to the main building's wall (they stopped short of it)."""
    cs = part.get('corners') or []
    n = len(cs)
    if n < 3:
        return
    i = back_wall(cs)
    a, b = cs[i], cs[(i + 1) % n]
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    nn = (-u[1], u[0])                                    # into the part, away from the main wall

    def d(q):
        return (q[0] / SCALE - a[0]) * nn[0] + (q[1] / SCALE - a[1]) * nn[1]
    for x in bd:
        if x[1] not in ('fascia', 'soffit'):
            continue
        sol = x[2]
        ds = [d(q) for f_ in sol.faces for q in f_]
        if not ds:
            continue
        lo, hi = min(ds), max(ds)
        if not (0.5 < lo < 600.0) or hi - lo < 150.0:
            continue                                      # already there, or not running back to the wall
        sh = (-nn[0] * lo * SCALE, -nn[1] * lo * SCALE)
        sol.faces = [[(q[0] + sh[0], q[1] + sh[1], q[2]) if d(q) <= lo + 1.0 else q for q in f_]
                     for f_ in sol.faces]


def add_boards(viewport, r, tops_by_part, gable_tops):
    """Fascia, barge boards (with finials) and soffits on the roofs just built - made by 3D Subframe from
    Floor Plan's roof slopes, at Subframe's own board sizes. Fascia and soffits along the eaves, but not across
    a roof gable on the front; on a roof gable only its barge boards. Returns (message, bad)."""
    sf = plugin_module("ed3d_subframe", "fp_roof_boards")
    if sf is None:
        return "Boards: 3D Subframe isn't loaded - put ed3d_subframe.py in the plugins folder.", True
    try:
        v = dict(sf.DEFAULTS)
        last = sf._ui_settings().get('last_values')
        if isinstance(last, dict):
            v.update({k: last[k] for k in sf.DEFAULTS if k in last})
        if float(v.get('width') or 0) <= 0 or float(v.get('depth') or 0) <= 0:
            v.update(width=230.0, depth=230.0)
        v.update(boards=True, soffits=True)
        p = sf.frame_params(v)
        p['_fp_roof'] = True
    except Exception as e:
        return "Boards: Subframe's sizes - %s" % e, True
    main = r['parts'][0]['corners']
    a, b = main[0], main[1]
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    nn = (-u[1], u[0])
    cuts = [(float(g['s0']), float(g['s1'])) for g in r.get('gables') or [] if int(g.get('part', 0)) == 0]

    deep = 0.6 * max(float(r['parts'][0].get('width') or 0.0), 1000.0)

    def across_gable(sol):
        """A board where a roof gable is: along the front wall in front of it, or round the opening in the roof
        under it (mm, the building's own terms)."""
        pts = [q for f_ in getattr(sol, 'faces', []) for q in f_]
        if not pts or not cuts:
            return False
        cx = sum(((q[0] / SCALE - a[0]) * u[0] + (q[1] / SCALE - a[1]) * u[1]) for q in pts) / len(pts)
        cy = sum(((q[0] / SCALE - a[0]) * nn[0] + (q[1] / SCALE - a[1]) * nn[1]) for q in pts) / len(pts)
        if any(s0 - 50.0 <= cx <= s1 + 50.0 for s0, s1 in cuts) and -1500.0 <= cy <= deep:
            return True
        xs = [((q[0] / SCALE - a[0]) * u[0] + (q[1] / SCALE - a[1]) * u[1]) for q in pts]
        ys = [((q[0] / SCALE - a[0]) * nn[0] + (q[1] / SCALE - a[1]) * nn[1]) for q in pts]
        if max(ys) > 600.0 or min(ys) < -1500.0:
            return False
        mid = (min(xs) + max(xs)) / 2.0
        return any(s0 - 1.0 <= mid <= s1 + 1.0 and max(xs) - min(xs) <= (s1 - s0) + 2.0 * over + 100.0
                   for s0, s1 in cuts)
    over = max(float(r.get('verge_over') or 0), float(r.get('eave_over') or 0), 300.0)
    out, probs = [], []
    jobs = [(tops, 'main' if i == 0 else None, ('part', i)) for i, tops in enumerate(tops_by_part)] + \
        [(gt, 'gable', ('gable', gi)) for gi, (_g, gt) in enumerate(gable_tops)]
    per_job = []
    for tops, kind, key in jobs:
        rg = sf._fp_roof_groups(tops or [])
        if not rg:
            continue
        try:
            bd, pr = sf.fp_roof_boards(rg, p, want_fascia=True, want_soffit=(kind != 'gable'))
        except Exception as e:
            probs.append("Boards: %s" % e)
            continue
        if kind == 'gable':
            bd = [x for x in bd if x[1] in ('barge', 'finial') and front_board(x[2], r, gable_tops[key[1]][0])]
        else:
            bd = [x for x in bd if not (kind == 'main' and across_gable(x[2]))]
        if key[0] == 'part' and key[1] > 0 and r['parts'][key[1]].get('against'):
            reach_wall(bd, r['parts'][key[1]])
            bd = [x for x in bd if not (x[1] in ('barge', 'finial') and at_back(x[2], r['parts'][key[1]]))]
        out += bd
        if bd:
            per_job.append((key, bd))
        probs += pr
    if not out:
        return "Boards: none made%s" % ((" - " + "; ".join(probs[:3])) if probs else ""), bool(probs)
    scene = getattr(viewport, 'scene', None)
    del BOARD_TOPS[:]
    split = []
    for key, bd in per_job:                               # the main building's boards: a group for each wall
        if key != ('part', 0):
            split.append((key, bd))
            continue
        cs = r['parts'][0]['corners']
        byw = {}
        for x in bd:
            byw.setdefault(nearest_wall(x[2], cs), []).append(x)
        split += [(('part', 0, w), byw[w]) for w in sorted(byw)]
    for key, bd in split:
        nm = ("Boards - wall %d" % (key[2] + 1) if len(key) == 3 else
              "Boards - %s" % (r['parts'][key[1]].get('name') or "Part %d" % (key[1] + 1)) if key[0] == 'part'
              else "Boards - roof gable %d" % (key[1] + 1))
        before = set(id(g) for g in _top_groups(scene))
        try:
            sf.SubframeTool().add_to_scene(viewport, [("Boards", bd)], nm)
        except Exception as e:
            return "Boards: couldn't add them - %s" % e, True
        BOARD_TOPS.append((key, [g for g in _top_groups(scene) if id(g) not in before]))
    nf = sum(1 for x in out if x[1] == 'fascia')
    nb = sum(1 for x in out if x[1] == 'barge')
    ns = sum(1 for x in out if x[1] == 'soffit')
    return "Boards (Subframe's sizes): %d fascia, %d barge, %d soffit%s." % (
        nf, nb, ns, (" - " + "; ".join(probs[:3])) if probs else ""), False


def remove_groups(viewport, gs):
    """Takes these top groups out of the model (one Undo)."""
    try:
        from core.history import SnapshotImport
    except Exception:
        return

    def mutate(sc):
        for g in gs:
            try:
                if hasattr(sc, 'remove_group'):
                    sc.remove_group(g)
                else:
                    sc.groups.remove(g)
            except Exception as e:
                print("%s: taking the old building out: %s" % (PLUGIN_NAME, e))
    try:
        viewport.history.execute(SnapshotImport(mutate))
        viewport.notify_scene_changed()
    except Exception as e:
        print("%s: taking the old building out: %s" % (PLUGIN_NAME, e))


def _top_groups(scene):
    try:
        return list(getattr(scene, 'groups', None) or [])
    except TypeError:
        return []


def _group_pts(g):
    """Every corner of a group's mesh (model metres), or []."""
    op = openings()
    if op is None:
        return []
    try:
        return [q for fd in op._faces_of(getattr(g, 'mesh', None)) for q in fd['pts']]
    except Exception:
        return []


def wall_under(kids, gd, front, r):
    """The main building's wall piece a roof gable's pointed front stands on: on the same wall line, its top
    where the front's bottom is, and running under it."""
    fp_ = _group_pts(front)
    if not fp_:
        return None
    cs = r['parts'][int(gd.get('part', 0))]['corners']
    i = int(gd.get('wall', 0)) % len(cs)
    a, b = cs[i], cs[(i + 1) % len(cs)]
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    nn = (-u[1], u[0])

    def st(q):
        x, y = q[0] / SCALE - a[0], q[1] / SCALE - a[1]
        return x * u[0] + y * u[1], x * nn[0] + y * nn[1], q[2] / SCALE
    f_ = [st(q) for q in fp_]
    fz = min(q[2] for q in f_)
    fs = (min(q[0] for q in f_) + max(q[0] for q in f_)) / 2.0
    best = None
    for g in kids:
        if getattr(g, 'mesh', None) is None:
            continue
        pts = [st(q) for q in _group_pts(g)]
        if not pts:
            continue
        ts = [q[1] for q in pts]
        if min(ts) < -5.0 or max(ts) > 600.0:
            continue                                      # not on that wall's line
        if not min(q[0] for q in pts) - 1.0 <= fs <= max(q[0] for q in pts) + 1.0:
            continue
        gap = abs(max(q[2] for q in pts) - fz)
        if gap < 5.0 and (best is None or gap < best[0]):
            best = (gap, g)
    return best[1] if best else None


def group_building(viewport, before, tops_by_part, gable_tops, r, name=''):
    """Everything just built put in one group for the building. Each bay or wing (with its boards) and each roof
    gable (with its barge boards) is a group named '... (one piece)', so Scale Studio prints it as one piece.
    Returns a line for the message ('' if nothing was done)."""
    scene = getattr(viewport, 'scene', None)
    new = [g for g in _top_groups(scene) if id(g) not in before]
    if len(new) < 2:
        return ""
    newids = set(id(g) for g in new)
    boards = {}
    for key, gs in BOARD_TOPS:
        boards.setdefault(key, []).extend(g for g in gs if id(g) in newids)
    try:
        from core.group import Group
        from core.history import SnapshotImport
    except Exception as e:
        return "Not put in one group: %s" % e

    def holder(nm, kids):
        h = Group(name=nm)
        if hasattr(h, 'adopt'):
            h.adopt(kids)
        else:
            h.children = kids
        try:
            h.name = nm
        except Exception:
            pass
        h.component = False
        return h
    names = []

    def kids_of(g):
        out = []
        for attr in ('children', 'groups'):
            try:
                out += list(getattr(g, attr, None) or [])
            except TypeError:
                pass
        return out

    def flat(g):
        """Floor Plan's holders ('Floor plan', 'Walls (8 pieces)'...) opened up: their pieces, one level down."""
        nm = str(getattr(g, 'name', '') or '')
        try:
            has_faces = len(list(getattr(getattr(g, 'mesh', None), 'faces', None) or [])) > 0
        except TypeError:
            has_faces = False
        if not has_faces and kids_of(g) and (
                nm.startswith("Floor plan") or re.search(r"\(\d+ pieces?\)$", nm)):
            return [x for k in kids_of(g) for x in flat(k)]
        return [g]

    def mutate(sc):
        used = set()
        kids = []
        for pi, tops in enumerate(tops_by_part):
            bds = [g for key, gs in boards.items() if key[0] == 'part' and key[1] == pi for g in gs]
            mine = [g for g in (tops or []) if id(g) in newids]
            used.update(id(g) for g in mine + bds)
            if not mine and not bds:
                continue
            if pi == 0:
                kids += [x for g in mine for x in flat(g)] + bds
            else:
                nm = "%s (one piece)" % (r['parts'][pi].get('name') or "Part %d" % (pi + 1))
                kids.append(holder(nm, mine + bds))
                names.append(nm)
        ng = 0
        onto = {}                                         # id(main wall piece): (wall piece, [gable fronts on it])
        for gi, (gd, gt) in enumerate(gable_tops):
            mine = [g for g in (gt or []) if id(g) in newids]
            fronts = []
            rest = []
            for g in mine:                                # its pointed front goes with the wall it stands on
                for x in flat(g):
                    if "gable on wall" in str(getattr(x, 'name', '') or '').lower():
                        w_ = wall_under(kids, gd, x, r)
                        if w_ is not None:
                            onto.setdefault(id(w_), (w_, []))[1].append(x)
                            fronts.append(x)
                            continue
                    rest.append(x)
            if not fronts:
                rest = mine
            rest += boards.get(('gable', gi), [])
            used.update(id(g) for g in mine + boards.get(('gable', gi), []))
            if rest:
                kids.append(holder("Roof gable %d (one piece)" % (gi + 1), rest))
                ng += 1
        for wid, (w_, fronts) in onto.items():            # the wall and the gable fronts on it: one flat piece
            k_ = next((i for i, x in enumerate(kids) if x is w_), None)
            if k_ is None:
                continue
            nm = "%s with %d roof gable front%s (one piece)" % (str(getattr(w_, 'name', '') or "Wall"), len(fronts),
                                                               "" if len(fronts) == 1 else "s")
            kids[k_] = holder(nm, [w_] + fronts)
        if ng:
            names.append("%d roof gable%s" % (ng, "" if ng == 1 else "s"))
        kids += [x for g in new if id(g) not in used for x in flat(g)]
        for g in new:
            if hasattr(sc, 'remove_group'):
                sc.remove_group(g)
            else:
                sc.groups.remove(g)
        top = holder("Building" + (" - " + name if name else ""), kids)
        if hasattr(sc, 'add_group'):
            sc.add_group(top)
        else:
            sc.groups.append(top)
    try:
        viewport.history.execute(SnapshotImport(mutate))
    except Exception as e:
        return "Not put in one group: %s" % e
    try:
        viewport.notify_scene_changed()
    except Exception:
        pass
    return "All in one group: 'Building%s'%s." % (" - " + name if name else "",
                                                  (" - one piece each to print: " + ", ".join(names)) if names else "")


def build_floor_plan(viewport, r, values):
    """Builds each part of the building with 3D Floor Plan, from the photo. Returns (the new top groups of
    each part, message, bad)."""
    fp = floor_plan()
    if fp is None:
        return [], "3D Floor Plan isn't loaded - it's needed to build the walls.", True
    scene = getattr(viewport, 'scene', None)
    if scene is None:
        return [], "No model open.", True
    tops_by_part, msgs, bad_any, main_v = [], [], False, None
    values = dict(values)
    for key in ('eave_over', 'verge_over'):
        if r.get(key) is not None:
            values[key] = float(r[key])
    del GABLE_TOPS[:]
    for pi, part in enumerate(r['parts']):
        got = build_part(viewport, part, values, fp, scene,
                         [g for g in r.get('gables') or [] if int(g.get('part', 0)) == pi])
        new, msg, bad = got[0], got[1], got[2]
        msgs.append(msg)
        tops_by_part.append(new)
        if bad:
            bad_any = True
            if pi == 0:
                return [], msg, True
            continue
        if pi == 0:
            main_v = got[3]
        if len(new) == 1:
            try:                                          # 'Floor plan - Bay 1', so you can tell them apart
                new[0].name = "%s - %s" % (getattr(new[0], 'name', '') or "Floor plan", part.get('name', 'Part'))
            except Exception:
                pass
        if part.get('against'):
            msgs[-1] = msgs[-1][:-1] + " (its back wall stands against the main building - handy to glue to)."
    for gi, g in enumerate(r.get('gables') or []):
        try:                                              # the wall it stands on, as actually built
            pi_ = int(g.get('part', 0))
            wt_ = measured_wall_top(tops_by_part[pi_] if pi_ < len(tops_by_part) else [], r, g,
                                    float(values.get('wall_t') or 230.0))
            if wt_ is not None:
                WALL_TOP[id(r['parts'][pi_])] = wt_
        except Exception as e:
            print("%s: wall top: %s" % (PLUGIN_NAME, e))
        got = build_gable(viewport, r, g, gi, values, fp, scene)
        GABLE_TOPS.append((g, got[0]))
        msgs.append(got[1])
        bad_any = bad_any or got[2]
    if main_v is not None:
        try:
            fp._ui_settings_save(last_values={k: main_v[k] for k in fp.DEFAULTS if k in main_v})   # Floor Plan shows it
        except Exception:
            pass
    return tops_by_part, "Built with Floor Plan:\n" + "\n".join(msgs), bad_any


GABLE_TOPS = []         # the roof gables just built: [(gable, its groups)] - for the barge boards
GABLE_WALL = 50.0      # mm of wall under a roof gable (it stands on the building's own wall)


def no_back_wall(pieces, part, wall_t):
    """A bay or wing against the main building: its back wall (and gable) left out - it opens into the building."""
    cs = part['corners']
    n = len(cs)
    i = back_wall(cs)
    a, b = cs[i], cs[(i + 1) % n]
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L        # into the part

    def t(q):
        return (q[0] - a[0]) * nx + (q[1] - a[1]) * ny
    out = []
    for pc in pieces:
        if pc.kind in ('wall', 'gable') and pc.poly and max(t(q) for q in pc.poly) <= wall_t + 5.0 \
                and min(t(q) for q in pc.poly) >= -wall_t - 5.0:
            continue
        out.append(pc)
    return out


def base_to_main(fp, pieces, part, values):
    """A bay's base plate (plinth) cut back to where the main building's base plate ends, so the two meet
    instead of overlapping."""
    try:
        mv = dict(fp.DEFAULTS)
        last = fp._ui_settings().get('last_values')
        if isinstance(last, dict):
            mv.update({k: last[k] for k in fp.DEFAULTS if k in last})
        over = float(mv.get('base_over') or 0.0) if mv.get('base') else 0.0
    except Exception:
        over = 0.0
    cs = part['corners']
    i = back_wall(cs)
    a, b = cs[i], cs[(i + 1) % len(cs)]
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    nn = (-(b[1] - a[1]) / L, (b[0] - a[0]) / L)          # out from the main wall, into the bay
    q = (a[0] + nn[0] * over, a[1] + nn[1] * over)
    out = []
    for pc in pieces:
        if pc.kind == 'base' and pc.poly and getattr(pc, 'custom', None) is None and not getattr(pc, 'parts', None):
            reg = fp.clip_half([(c[0], c[1]) for c in pc.poly], q, nn)
            reg = fp.clean(reg) if reg else None
            if reg and len(reg) >= 3 and abs(fp.area2(reg)) > 100.0:
                pc.poly = reg
            else:
                continue
        out.append(pc)
    return out


def bay_openings(r, wall_t):
    """A hole in the main building's wall behind each bay or wing, between its side walls, from the floor to
    just under its eaves - so it's part of the building."""
    out = []
    parts = r.get('parts') or []
    if len(parts) < 2:
        return out
    main = parts[0]['corners']
    nm_ = len(main)
    for pi, part in enumerate(parts[1:], 1):
        if not part.get('against') or len(part.get('corners') or []) < 3:
            continue
        cs = part['corners']
        k = back_wall(cs)
        p, q = cs[k], cs[(k + 1) % len(cs)]
        for i in range(nm_):
            a, b = main[i], main[(i + 1) % nm_]
            L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
            u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
            off = lambda c: abs((c[0] - a[0]) * -u[1] + (c[1] - a[1]) * u[0])
            if off(p) > 60.0 or off(q) > 60.0:
                continue
            sp = (p[0] - a[0]) * u[0] + (p[1] - a[1]) * u[1]
            sq = (q[0] - a[0]) * u[0] + (q[1] - a[1]) * u[1]
            s0, s1 = sorted((sp, sq))
            s0, s1 = max(s0, 0.0) + wall_t, min(s1, L) - wall_t
            z1 = float(part.get('eaves') or 0) - 100.0
            if s1 - s0 > 50.0 and z1 > 200.0:
                out.append({'part': 0, 'wall': i, 'kind': 'door', 'top': 'square', 's0': round(s0, 1),
                            's1': round(s1, 1), 'z0': 0.0, 'z1': round(z1, 1),
                            'name': "Opening to %s" % (part.get('name') or "part %d" % (pi + 1))})
            break
    return out


WALL_TOP = {}           # id(part): the top of its walls as Floor Plan built them (mm)
ROOF_PLANES = {}        # id(part): [(plan outline, (gx, gy, c) of its top)] - its roof slopes as just built


def roof_planes(pieces):
    out = []
    for pc in pieces:
        sol = getattr(pc, 'custom', None)
        if pc.kind == 'roof' and sol is not None and getattr(sol, 'faces', None):
            pl = _plane3(sol.faces[0])
            if pl is not None:
                out.append(([(q[0], q[1]) for q in pc.poly], pl))
    return out


def _in_poly(poly, x, y):
    c = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def trim_gable(fp, pieces, planes, a, inn, mid, zb, wall_t):
    """A roof gable keeps only what shows: its front wall and gable, and its roof slopes down to where they
    meet the main roof. Its back gable, side walls and the slopes inside the main roof are left out."""
    def t_of(q):
        return (q[0] - a[0]) * inn[0] + (q[1] - a[1]) * inn[1]
    main = next((pl for poly, pl in planes if _in_poly(poly, mid[0], mid[1])), None)
    out = []
    for pc in pieces:
        if pc.kind != 'roof':
            if pc.poly and max(t_of(q) for q in pc.poly) <= wall_t + 5.0:
                out.append(pc)                             # the front wall and its gable
            continue
        sol = getattr(pc, 'custom', None)
        if main is None or sol is None or len(getattr(sol, 'faces', [])) < 2:
            out.append(pc)
            continue
        pl = _plane3(sol.faces[0])
        bot = sol.faces[1]
        if pl is None or not bot:
            out.append(pc)
            continue
        depth = (pl[0] * bot[0][0] + pl[1] * bot[0][1] + pl[2]) - bot[0][2]
        A, B = pl[0] - main[0], pl[1] - main[1]
        C = pl[2] + zb - main[2]                         # above the main roof where A x + B y + C >= 0
        nn = A * A + B * B
        if nn < 1e-12:
            out.append(pc)
            continue
        q0 = (-C * A / nn, -C * B / nn)
        reg = fp.clip_half([(q[0], q[1]) for q in pc.poly], q0, (A, B))
        reg = fp.clean(reg) if reg else None
        if not reg or len(reg) < 3 or abs(fp.area2(reg)) < 100.0:
            continue
        zs = [pl[0] * x + pl[1] * y + pl[2] for x, y in reg]
        np_ = fp.Piece(pc.name, 'roof', pc.storey, reg, min(zs) - depth, max(zs))
        np_.custom = fp.slab_on_plane(reg, pl, depth)
        out.append(np_)
    return out


def gable_pieces(part, g, values, fp, planes, gi=0):
    """A roof gable's pieces from Floor Plan, trimmed to what shows (needs its part's roof planes).
    Returns dict(pieces, v, gp, zb, a, u, inn, back, rise, s0, s1); raises ValueError."""
    cs = part['corners']
    i = int(g['wall'])
    a, b = cs[i % len(cs)], cs[(i + 1) % len(cs)]
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    ix, iy = -uy, ux                                   # into the building
    rise = float(g['peak']) - float(g['z0'])
    try:
        pitch = float(floor_plan_values(part, values, fp).get('roof_pitch') or 40.0)
    except Exception:
        pitch = 40.0
    pitch = min(max(pitch, 10.0), 75.0)
    back = rise / math.tan(math.radians(pitch)) + 300.0          # far enough back to meet the main roof
    back = min(back, 0.9 * max(float(part.get('width') or 0.0), 1000.0))
    s0, s1 = float(g['s0']), float(g['s1'])
    P = lambda s, t: [round(a[0] + ux * s + ix * t, 1), round(a[1] + uy * s + iy * t, 1)]
    gp = {'name': "Roof gable %d" % (gi + 1), 'corners': [P(s0, 0), P(s1, 0), P(s1, back), P(s0, back)],
          'eaves': GABLE_WALL, 'ridge': GABLE_WALL + rise, 'roof': 'gable_across', 'roof_low': 'front',
          'storeys': 1, 'length': round(s1 - s0, 1), 'width': round(back, 1)}
    v = floor_plan_values(gp, values, fp, extra=dict(floor_style='none', base=False, top=False, gables=False,
                                                     ledges=False, split_len=0.0, cross_x='', cross_y=''))
    v['eave_over'] = 0.0                               # its sides sit on the main roof: the barge boards stop there
    p = fp.plan_params(v)
    pieces, _notes = fp.build_plan(p, fp.make_outline(p))
    zb = float(g['z0']) - GABLE_WALL
    try:                                              # stand it so its eaves meet the main roof's top at the wall
        q = P(s0 + 20.0, 20.0)
        zm = next((pl[0] * q[0] + pl[1] * q[1] + pl[2] for poly, pl in (planes or []) if _in_poly(poly, q[0], q[1])),
                  None)
        zl = None
        for pc in pieces:
            sol = getattr(pc, 'custom', None)
            if pc.kind == 'roof' and sol is not None and getattr(sol, 'faces', None) and pc.poly \
                    and _in_poly([(c[0], c[1]) for c in pc.poly], q[0], q[1]):
                pl_ = _plane3(sol.faces[0])
                if pl_ is not None:
                    zl = pl_[0] * q[0] + pl_[1] * q[1] + pl_[2]
                    break
        if zm is not None and zl is not None:
            zb = zm - zl + 2.0
    except Exception as e:
        print("%s: roof gable height: %s" % (PLUGIN_NAME, e))
    lo = float(WALL_TOP.get(id(part), part.get('eaves')) or 0.0) - zb    # the main wall's top, in its own heights
    keep = []
    for pc in pieces:                                   # its wall and gable: only above the main wall, not into it
        if pc.kind in ('wall', 'gable') and not getattr(pc, 'parts', None):
            if lo >= pc.z1 - 0.5:
                continue
            try:
                sol = pc.solid()
                if min(q[2] for f_ in sol.faces for q in f_) < lo - 0.01:
                    s2 = copy.copy(sol)                 # its bottom lifted to the wall top (its sides are upright)
                    s2.faces = [[(q[0], q[1], max(q[2], lo)) for q in f_] for f_ in sol.faces]
                    pc.custom = s2
                    pc.z0 = max(pc.z0, lo)
            except Exception as e:
                print("%s: roof gable's bottom: %s" % (PLUGIN_NAME, e))
        keep.append(pc)
    pieces = keep
    try:
        pieces = trim_gable(fp, pieces, planes or [], (a[0], a[1]), (ix, iy), P((s0 + s1) / 2.0, back / 2.0), zb,
                            float(v.get('wall_t') or 230.0))
    except Exception as e:
        print("%s: roof gable %d not trimmed: %s" % (PLUGIN_NAME, gi + 1, e))
    return dict(pieces=pieces, v=v, gp=gp, zb=zb, a=(a[0], a[1]), u=(ux, uy), inn=(ix, iy), back=back, rise=rise,
                s0=s0, s1=s1)


def gable_hole(info, margin):
    """The hole in the main roof under a roof gable: its footprint on the roof (from the front, where the eaves
    are already cut away, back to where its slopes meet the roof), kept in from its sides so it sits on the roof."""
    a, u, inn = info['a'], info['u'], info['inn']
    st = []
    for pc in info['pieces']:
        if pc.kind == 'roof':
            for q in pc.poly:
                st.append(((q[0] - a[0]) * u[0] + (q[1] - a[1]) * u[1], (q[0] - a[0]) * inn[0] + (q[1] - a[1]) * inn[1]))
    if len(st) < 3:
        return None
    st = st + [(x, -3000.0) for x, y in st if y < 5.0]            # straight out past the eaves at the front
    wt_ = float(info['v'].get('wall_t') or 230.0) + 2.0
    if margin <= 0.0:                                     # one opening: the eaves in front of it too
        st += [(info['s0'], -3000.0), (info['s1'], -3000.0)]
    hull = _hull(st)
    if len(hull) < 3:
        return None
    reg = list(hull)
    n = len(hull)
    for i in range(n):
        p_, q_ = hull[i], hull[(i + 1) % n]
        if p_[1] <= -2999.0 and q_[1] <= -2999.0:
            continue                                      # the front: no need to keep in from it
        dx, dy = q_[0] - p_[0], q_[1] - p_[1]
        L = math.hypot(dx, dy) or 1.0
        nn = (-dy / L, dx / L)                            # into the hull (it goes anticlockwise)
        reg = _clip_half2(reg, (p_[0] + nn[0] * margin, p_[1] + nn[1] * margin), nn)
        if len(reg) < 3:
            return None
    P = lambda x, y: (a[0] + u[0] * x + inn[0] * y, a[1] + u[1] * x + inn[1] * y)
    s0, s1 = info['s0'], info['s1']
    wt = float(info['v'].get('wall_t') or 230.0) + 2.0
    front = [P(s0, -3000.0), P(s1, -3000.0), P(s1, wt), P(s0, wt)]      # the eaves in front of it, back past its wall
    tidy = []
    for q in reg:                                       # no corner twice (a zero-length edge)
        if not tidy or abs(q[0] - tidy[-1][0]) + abs(q[1] - tidy[-1][1]) > 0.01:
            tidy.append(q)
    if len(tidy) > 2 and abs(tidy[0][0] - tidy[-1][0]) + abs(tidy[0][1] - tidy[-1][1]) <= 0.01:
        tidy.pop()
    if margin <= 0.0:
        return [[P(x, y) for x, y in tidy]]
    return [front, [P(x, y) for x, y in tidy]]


def _hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p_ in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p_) <= 0:
            lo.pop()
        lo.append(p_)
    for p_ in reversed(pts):
        while len(hi) >= 2 and cr(hi[-2], hi[-1], p_) <= 0:
            hi.pop()
        hi.append(p_)
    return lo[:-1] + hi[:-1]


def _clip_half2(poly, q, d):
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        fa = (a[0] - q[0]) * d[0] + (a[1] - q[1]) * d[1]
        fb = (b[0] - q[0]) * d[0] + (b[1] - q[1]) * d[1]
        if fa >= 0:
            out.append(a)
        if (fa >= 0) != (fb >= 0):
            t = fa / (fa - fb)
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    return out


def _seg_hit(p, q, a, b):
    """Where segments p-q and a-b cross: (t along p-q, s along a-b) or None."""
    rx, ry = q[0] - p[0], q[1] - p[1]
    sx, sy = b[0] - a[0], b[1] - a[1]
    d = rx * sy - ry * sx
    if abs(d) < 1e-12:
        return None
    t = ((a[0] - p[0]) * sy - (a[1] - p[1]) * sx) / d
    u_ = ((a[0] - p[0]) * ry - (a[1] - p[1]) * rx) / d
    if 0.0 <= t <= 1.0 and 0.0 <= u_ <= 1.0:
        return t, u_
    return None


def subtract_convex(reg, hole):
    """reg (anticlockwise) with a convex hole taken out of it, where the hole cuts in from one edge (a notch):
    [one outline]. Anything else: the pieces that are left (several). None if the hole misses it."""
    def inh(p_):                                          # well inside the hole (over 0.5 mm in from its edges)
        n = len(hole)
        for i in range(n):
            a_, b_ = hole[i], hole[(i + 1) % n]
            L = math.hypot(b_[0] - a_[0], b_[1] - a_[1]) or 1.0
            if ((b_[0] - a_[0]) * (p_[1] - a_[1]) - (b_[1] - a_[1]) * (p_[0] - a_[0])) / L <= 0.5:
                return False
        return True
    hits = []
    n, m = len(reg), len(hole)
    for i in range(n):
        p_, q_ = reg[i], reg[(i + 1) % n]
        for j in range(m):
            h = _seg_hit(p_, q_, hole[j], hole[(j + 1) % m])
            if h:
                hits.append((i, h[0], j, (p_[0] + h[0] * (q_[0] - p_[0]), p_[1] + h[0] * (q_[1] - p_[1]))))
    if not hits and not any(inh(p_) for p_ in reg) and not any(_in_poly(reg, h_[0], h_[1]) for h_ in hole):
        return None
    if len(hits) == 2:
        def going_in(h):
            p_, q_ = reg[h[0]], reg[(h[0] + 1) % n]
            t = min(h[1] + 1e-4, 1.0)
            return inh((p_[0] + t * (q_[0] - p_[0]), p_[1] + t * (q_[1] - p_[1])))
        if not going_in(hits[0]):
            hits.reverse()                                # X: the way in
        (i1, _t1, j1, X), (i2, _t2, j2, Y) = hits
        out = []
        k = (i2 + 1) % n
        while True:                                       # round the outline from Y's edge to X's edge
            out.append(reg[k])
            if k == i1:
                break
            k = (k + 1) % n
        out.append(X)
        k = j1                                            # back round the hole, X to Y
        guard = 0
        while k != j2 and guard < m + 1:
            out.append(hole[k])
            k = (k - 1) % m
            guard += 1
        out.append(Y)
        if not any(inh(p_) for p_ in out):
            return [out]
    pieces = []                                           # otherwise: the bits left, in convex pieces
    rest = list(reg)
    for j in range(m):
        a_, b_ = hole[j], hole[(j + 1) % m]
        d_ = (b_[1] - a_[1], -(b_[0] - a_[0]))            # outside this edge of the hole
        outp = _clip_half2(rest, a_, d_)
        if len(outp) >= 3:
            pieces.append(outp)
        rest = _clip_half2(rest, a_, (-d_[0], -d_[1]))
        if len(rest) < 3:
            break
    return pieces


def cut_roof_for_gables(fp, pieces, holes):
    """Holes cut in the main roof's slopes under the roof gables, so they sit on top of the roof and open into it."""
    out = []
    for pc in pieces:
        sol = getattr(pc, 'custom', None)
        if pc.kind != 'roof' or sol is None or len(getattr(sol, 'faces', [])) < 2:
            out.append(pc)
            continue
        pl = _plane3(sol.faces[0])
        bot = sol.faces[1]
        if pl is None or not bot:
            out.append(pc)
            continue
        depth = (pl[0] * bot[0][0] + pl[1] * bot[0][1] + pl[2]) - bot[0][2]
        regs = [[(q[0], q[1]) for q in pc.poly]]
        if fp.area2(regs[0]) < 0:
            regs[0].reverse()
        hit = False
        for hole in holes:
            nxt = []
            for reg in regs:
                got = subtract_convex(reg, hole)
                if got is None:
                    nxt.append(reg)
                else:
                    hit = True
                    nxt += got
            regs = nxt
        if not hit:
            out.append(pc)
            continue
        for k, reg in enumerate(r_ for r_ in regs if len(r_) >= 3 and abs(fp.area2(r_)) > 100.0):
            zs = [pl[0] * x + pl[1] * y + pl[2] for x, y in reg]
            np_ = fp.Piece(pc.name if k == 0 else "%s (%d)" % (pc.name, k + 1), 'roof', pc.storey, list(reg),
                           min(zs) - depth, max(zs))
            np_.custom = fp.slab_on_plane(list(reg), pl, depth)
            out.append(np_)
    return out


def measured_wall_top(tops, r, g, wall_t):
    """The top of the main wall under a roof gable, read from the wall pieces as they were put in the model (mm),
    or None."""
    cs = r['parts'][int(g.get('part', 0))]['corners']
    i = int(g.get('wall', 0)) % len(cs)
    a, b = cs[i], cs[(i + 1) % len(cs)]
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    nn = (-u[1], u[0])
    s0, s1 = float(g['s0']), float(g['s1'])
    best = None

    def walk(x):
        kids = []
        for attr in ('children', 'groups'):
            try:
                kids += list(getattr(x, attr, None) or [])
            except TypeError:
                pass
        return [x] + [y for k in kids for y in walk(k)]
    for top in tops or []:
        for x in walk(top):
            nm = str(getattr(x, 'name', '') or '').lower()
            if 'wall' not in nm or 'gable' in nm:
                continue
            zs = []
            for q in _group_pts(x):
                X, Y = q[0] / SCALE - a[0], q[1] / SCALE - a[1]
                s_, t_ = X * u[0] + Y * u[1], X * nn[0] + Y * nn[1]
                if -1.0 <= t_ <= wall_t + 1.0 and s0 - 1.0 <= s_ <= s1 + 1.0:
                    zs.append(q[2] / SCALE)
            if zs and (best is None or max(zs) > best):
                best = max(zs)
    return best


def build_gable(viewport, r, g, gi, values, fp, scene):
    """A pointed gable on the front of a roof: a little gable-ended roof, with its front flush with the wall,
    sitting on the main roof (built with Floor Plan, standing at the eaves). Returns (tops, msg, bad)."""
    pi = int(g.get('part', 0))
    if not 0 <= pi < len(r['parts']):
        return [], "Roof gable %d: no part %d" % (gi + 1, pi + 1), True
    part = r['parts'][pi]
    try:
        info = gable_pieces(part, g, values, fp, ROOF_PLANES.get(id(part)), gi)
    except ValueError as e:
        return [], "Roof gable %d - Floor Plan: %s" % (gi + 1, e), True
    pieces, v, gp, back, rise, s0, s1 = (info[k] for k in ('pieces', 'v', 'gp', 'back', 'rise', 's0', 's1'))
    try:
        lines = ["%s roof gable %d: wall top %s, stands at %.1f" % (time.strftime("%H:%M:%S"), gi + 1,
                                                                    WALL_TOP.get(id(part)), info['zb'])]
        for pc in pieces:
            sol = pc.solid() if getattr(pc, 'custom', None) is None else pc.custom
            zs = [q[2] for f_ in sol.faces for q in f_]
            lines.append("  %s (%s): bottom %.1f top %.1f" % (pc.name, pc.kind, info['zb'] + min(zs),
                                                              info['zb'] + max(zs)))
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "photo_to_building_gables.txt"), "a",
                  encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception as e:
        print("%s: gable note: %s" % (PLUGIN_NAME, e))
    before = set(id(t) for t in fp._items(getattr(scene, 'groups', None)))
    n = fp.FloorPlanTool().add_to_scene(viewport, pieces, v.get('grouping', 'storeys'), info['zb'])
    if n is None:
        return [], "Floor Plan couldn't add roof gable %d." % (gi + 1), True
    new = [t for t in fp._items(getattr(scene, 'groups', None)) if id(t) not in before]
    if len(new) == 1:
        try:
            new[0].name = "%s - %s" % (getattr(new[0], 'name', '') or "Floor plan", gp['name'])
        except Exception:
            pass
    return new, "%s: %.0f mm wide, %.0f mm from the eaves to its peak, %.0f mm back into the roof at %.1f°." % (
        gp['name'], s1 - s0, rise, back, float(v.get('roof_pitch') or 0)), False


# ---------------------------------------------------------------------------
# Carrying on with the build order
# ---------------------------------------------------------------------------
def carry_on(dlg):
    """On to the next step: the toolbar's next step if you're working through a job (Make...), else 3D
    Subframe at its 'Start here' page (3 Frame - Floor Plan and Openings are done)."""
    tb = toolbar()
    if tb is not None:
        try:
            pj = tb._project()
            cur = tb._project_cur()
            if pj and cur is not None and 0 <= cur < len(pj[1]) and pj[1][cur][0] == PLUGIN_NAME:
                tb.project_next(tb._main_window())
                return
        except Exception as e:
            print("%s: toolbar's next step: %s" % (PLUGIN_NAME, e))
    sf = plugin_module("ed3d_subframe", "SubframeTool")
    if sf is None:
        QMessageBox.information(dlg, PLUGIN_NAME, "Subframe isn't loaded - put ed3d_subframe.py in the plugins "
                                "folder with this one.")
        return
    try:
        vp = dlg.viewport
        dlg.close()                                    # one window at a time
        sf.SubframeTool().on_activate(vp)
        d2 = getattr(sf.SubframeTool, '_dialog', None)
        if d2 is not None and hasattr(d2, 'show_start'):
            d2.show_start()
    except Exception as e:
        QMessageBox.warning(dlg, PLUGIN_NAME, "Couldn't open Subframe:\n%s" % e)


def open_floor_plan_filled(dlg, r, values):
    """Opens 3D Floor Plan with one part of the photo's building filled in, to check or change before
    building (r is the part)."""
    fp = floor_plan()
    if fp is None:
        QMessageBox.information(dlg, PLUGIN_NAME, "Floor Plan isn't loaded - put ed3d_floor_plan.py in the "
                                "plugins folder with this one.")
        return False
    v = floor_plan_values(r, values, fp)
    try:
        fp._ui_settings_save(last_values={k: v[k] for k in fp.DEFAULTS if k in v})
    except Exception:
        pass
    try:
        fp.FloorPlanTool().on_activate(dlg.viewport)
        d2 = getattr(fp.FloorPlanTool, '_dialog', None)
        if d2 is not None:
            d2.set_values(v)
            try:
                for i in range(d2.tabs.count()):
                    if "shape" in d2.tabs.tabText(i).lower():
                        d2.tabs.setCurrentIndex(i)
                        break
            except Exception:
                pass
    except Exception as e:
        QMessageBox.warning(dlg, PLUGIN_NAME, "Couldn't open Floor Plan:\n%s" % e)
        return False
    return True


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


class TwoRowTabs(QWidget):
    """Pages with their tabs on two rows, so they all show without scrolling across.
    Works like a QTabWidget: addTab, setTabToolTip, currentIndex, setCurrentIndex, currentChanged."""
    try:
        from PySide6.QtCore import Signal as _Signal
        currentChanged = _Signal(int)
    except Exception:
        currentChanged = None

    def __init__(self, rows=2, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QGridLayout, QStackedWidget, QButtonGroup
        self._rows = rows
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self._grid = QGridLayout()
        self._grid.setSpacing(2)
        lay.addLayout(self._grid)
        self._stack = QStackedWidget()
        try:
            from PySide6.QtWidgets import QFrame
            self._stack.setFrameShape(QFrame.StyledPanel)
        except Exception:
            pass
        lay.addWidget(self._stack, 1)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons = []
        self._group.idClicked.connect(self.setCurrentIndex)

    def _relayout(self):
        n = len(self._buttons)
        per = max(1, -(-n // self._rows))         # tabs on each row
        for b in self._buttons:
            self._grid.removeWidget(b)
        for i, b in enumerate(self._buttons):
            self._grid.addWidget(b, i // per, i % per)

    def addTab(self, widget, title):
        b = QPushButton(title.replace("&&", "&"))
        b.setCheckable(True)
        b.setStyleSheet("QPushButton { padding: 3px 8px; }"
                        "QPushButton:checked { font-weight: bold; background-color: palette(base); "
                        "border: 1px solid palette(mid); border-bottom: 2px solid palette(highlight); }")
        i = len(self._buttons)
        self._group.addButton(b, i)
        self._buttons.append(b)
        self._stack.addWidget(widget)
        self._relayout()
        if i == 0:
            b.setChecked(True)
        return i

    def setTabToolTip(self, i, tip):
        if 0 <= i < len(self._buttons):
            self._buttons[i].setToolTip(tip)

    def tabText(self, i):
        return self._buttons[i].text() if 0 <= i < len(self._buttons) else ""

    def count(self):
        return len(self._buttons)

    def currentIndex(self):
        return self._stack.currentIndex()

    def setCurrentIndex(self, i):
        try:
            i = int(i)
        except Exception:
            return
        if not 0 <= i < len(self._buttons) or i == self._stack.currentIndex() and self._buttons[i].isChecked():
            return
        self._buttons[i].setChecked(True)
        self._stack.setCurrentIndex(i)
        try:
            self.currentChanged.emit(i)
        except Exception:
            pass

EDDY_TIPS = {
    "choose folder...": "Pick the folder your photos are in.",
    "open folder": "Opens the folder in Windows.",
    "choose a photo...": "Pick a photo from anywhere on your PC.",
    "known size": "One size you know on the building - everything else is measured from the photo and sized "
                  "from this. The letters are on the Key drawing.",
    "it is": "How big that size is on the real building, in mm.",
    "floors (storeys)": "How many floors the building has - Floor Plan divides the height between them.",
    "roof": "The kind of roof. 'Along the front' means the ridge runs the same way as the wall from corner 1 to "
            "corner 2.",
    "low side": "Which side a lean-to roof comes down to.",
    "shape": "Rectangle: click 3 corners (the 4th is worked out). My own corners: click every corner, going round.",
    "depth if you can't see a side": "Only if the far end of a side wall can't be seen in the photo: how deep "
                                     "the building is (0 = click corner 3 instead).",
    "wall thickness": "How thick Floor Plan makes the walls (the photo can't show it). 230 mm is a brick "
                         "wall (9 inches).",
    "door bottoms on the floor": "Doors clicked near the bottom of a wall are cut right down to the floor, "
                                 "as doorways.",
    "start clicking round the building": "Opens the photo big, with the steps beside it, ready to click round "
                                         "the building (or in your 3D program, if picked on the Match it page).",
    "here in ingetrazo - no 3d program needed": "The photo opens in a window here, with the steps beside it.",
    "in the 3d program (blender), as before": "Your 3D program opens with the photo as a camera match, and its "
                                              "panel takes you through the steps.",
    "start from the front (a face-on photo)": "A photo straight on to the front does the widths, heights, windows, "
                                              "doors, bays and wings in one go; the depth comes after.",
    "carry on with the last one": "Opens the last photo again, with everything you'd clicked, to change it or "
                                  "carry on (here or in the 3D program - either picks up the other's clicks).",
    "get the building back": "Takes in what the 3D program sent (it's taken in by itself when it arrives).",
    "build it": "Builds the walls, floors and roof with Floor Plan, cuts the windows and doors through the walls, "
                "and gets you ready for the next step (3 Frame).",
    "fill in floor plan to check first": "Opens Floor Plan with the building (or the part picked next to it) "
                                         "filled in, so you can check or change it (add inside walls...) before "
                                         "building. Then come back and click Cut the windows and doors.",
    "cut the windows and doors": "Cuts the photo's windows and doors through the walls Floor Plan built.",
    "next: 3 frame \u25b6": "Closes this and opens the next step in your build order - Subframe.",
    "find it": "Looks for the 3D program in the usual places (the newest version first).",
    "info": "Shows how to use it.",
    "open at the last page used": "Ticked, the window opens at the page you had open last time.",
}

INFO_TEXT = ("<b>How to use it</b><br>"
             "1. <b>Photo</b>: pick a photo of the building, taken from a corner so two walls show. The longer "
             "the straight edges in it (eaves, ground, rows of windows), the better it measures.<br>"
             "2. <b>Sizes</b>: pick one size you know (the Key drawing shows them) and type it in mm. A door is "
             "usually about 2000 mm high. Set the floors and the roof.<br>"
             "3. <b>Match it</b>: click <b>Start clicking round the building</b>. The photo opens big, with the "
             "steps beside it (or, if you pick it on the Match it page, in the 3D program): line up the red lines with two edges of one wall and the green "
             "ones with the wall round the corner (the blue grid then lies flat on the ground); click the "
             "corners on the ground (1 and 2 at the ends of the front, then the far end of the side wall); "
             "the top of a corner; the top of the roof; two corners of each window and door. "
             "Then click <b>Send to Build</b>.<br>"
             "A wing, a bay or a porch: add it on step 1 and do "
             "steps 2 to 4 for it - a bay runs back to the main building's wall by itself. Each part is built "
             "on its own, with its own windows and doors.<br>"
             "4. <b>Build</b>: the building comes back by itself. Click <b>Build it</b>: Floor Plan builds the walls, "
             "floors and roof, and the windows and doors are cut through the walls where they are in the photo. "
             "Then <b>Next: 3 Frame</b> carries on with your build order.<br><br>"
             "Walls hidden in the photo can't be measured - add their windows afterwards with Openings. "
             "Sizes are real-world mm - Scale Studio takes it down to your model scale.")


# ---------------------------------------------------------------------------
# Drawings: the key, and what came back from the photo
# ---------------------------------------------------------------------------
class KeyDrawing(QWidget):
    """The sizes you might know (A to G), and the corners to click (1, 2, 3)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 420)

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 248))
        dark = QPen(QColor(40, 40, 40), 1.2)
        red = QPen(QColor(200, 40, 40), 1.4)
        f = QFont(p.font())
        f.setBold(True)

        def letter(x, y, t, col=QColor(200, 40, 40)):
            p.setFont(f)
            p.setPen(col)
            p.drawText(QRectF(x - 10, y - 10, 20, 20), Qt.AlignCenter, t)
            p.setFont(QFont())

        p.setPen(dark)
        p.drawText(QRectF(10, 6, 300, 18), Qt.AlignLeft, "The building, from a corner")
        # a house seen from its front-left corner: front wall, side wall, gable roof
        c1, c2, c3 = QPointF(40, 300), QPointF(200, 318), QPointF(290, 268)
        up = 120.0
        t1, t2, t3 = QPointF(c1.x(), c1.y() - up), QPointF(c2.x(), c2.y() - up * 1.05), QPointF(c3.x(), c3.y() - up * 0.9)
        rid2 = QPointF((t2.x() + t3.x()) / 2.0, (t2.y() + t3.y()) / 2.0 - 70)
        rid1 = QPointF(rid2.x() - (c2.x() - c1.x()) - 8, rid2.y() - (c2.y() - c1.y()) * 0.6)
        p.setBrush(QColor(196, 120, 90))
        p.drawPolygon(QPolygonF([c1, c2, t2, t1]))
        p.setBrush(QColor(170, 100, 75))
        p.drawPolygon(QPolygonF([c2, c3, t3, rid2, t2]))
        p.setBrush(QColor(110, 110, 120))
        p.drawPolygon(QPolygonF([t1, t2, rid2, rid1]))
        # a door and a window on the front
        p.setBrush(QColor(90, 60, 40))
        door = QPolygonF([QPointF(80, 305), QPointF(104, 308), QPointF(104, 262), QPointF(80, 259)])
        p.drawPolygon(door)
        p.setBrush(QColor(200, 225, 240))
        win = QPolygonF([QPointF(135, 270), QPointF(170, 274), QPointF(170, 244), QPointF(135, 240)])
        p.drawPolygon(win)
        # the corners to click
        for k, c in enumerate((c1, c2, c3)):
            p.setPen(QPen(QColor(230, 170, 0), 2))
            p.setBrush(QColor(255, 210, 40))
            p.drawEllipse(c, 4, 4)
            letter(c.x() + (-12 if k == 0 else 12), c.y() + 12, str(k + 1), QColor(160, 110, 0))
        p.setPen(red)
        letter((c1.x() + c2.x()) / 2.0, (c1.y() + c2.y()) / 2.0 + 22, "A")
        letter((c2.x() + c3.x()) / 2.0 + 6, (c2.y() + c3.y()) / 2.0 + 20, "B")
        p.drawLine(QPointF(c1.x() - 14, c1.y()), QPointF(t1.x() - 14, t1.y()))
        letter(c1.x() - 26, (c1.y() + t1.y()) / 2.0, "C")
        p.drawLine(QPointF(rid1.x() - 14, c1.y() - 2), QPointF(rid1.x() - 14, rid1.y()))
        letter(rid1.x() - 26, rid1.y() + 30, "D")
        p.drawLine(QPointF(110, 308), QPointF(110, 262))
        letter(120, 285, "E")
        p.drawLine(QPointF(135, 232), QPointF(170, 236))
        letter(152, 224, "F")
        p.drawLine(QPointF(176, 274), QPointF(176, 244))
        letter(187, 258, "G")
        p.setPen(dark)
        p.drawText(QRectF(10, 340, 310, 80), Qt.AlignLeft | Qt.TextWordWrap,
                   "1, 2, 3  the corners to click, where the walls meet the ground.\n"
                   "A front wall   B side wall   C eaves   D top of the roof\n"
                   "E first door's height   F, G first window's width and height\n"
                   "Pick one of A to G you know - the rest is measured.")
        p.end()


class ResultDrawing(QWidget):
    """What came back from the photo: the plan (looking down) and the front wall."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.r = None
        self.setMinimumSize(320, 420)

    def set_result(self, r):
        self.r = r
        self.update()

    def mouseDoubleClickEvent(self, _ev):
        if self.r is not None and callable(getattr(self, 'on_double', None)):
            self.on_double()

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QPolygonF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(250, 250, 248))
        dark = QPen(QColor(40, 40, 40), 1.2)
        p.setPen(dark)
        r = self.r
        if not r:
            p.drawText(QRectF(10, 10, self.width() - 20, 80), Qt.AlignLeft | Qt.TextWordWrap,
                       "Nothing clicked and sent yet.\n\nWhen you click Send after clicking round the building, "
                       "the building's plan and front are drawn here.")
            p.end()
            return
        cs = r['corners']
        n = len(cs)
        parts = r.get('parts') or [r]
        xs = [c[0] for pt in parts for c in pt['corners']]
        ys = [c[1] for pt in parts for c in pt['corners']]
        W_, H_ = max(xs) - min(xs) or 1.0, max(ys) - min(ys) or 1.0
        Wd = self.width() - 40
        half = (self.height() - 60) / 2.0
        # plan, looking down: the front (wall 1) at the bottom
        k = min(Wd / W_, (half - 30) / H_)
        ox, oy = 20 + (Wd - W_ * k) / 2.0, 30 + (half - 30 + H_ * k) / 2.0

        def P(x, y):
            return QPointF(ox + (x - min(xs)) * k, oy - (y - min(ys)) * k)
        p.drawText(QRectF(10, 6, 300, 18), Qt.AlignLeft, "Looking down (the front at the bottom)")
        for k, pt in enumerate(parts):
            p.setBrush(QColor(235, 220, 200) if k == 0 else QColor(215, 205, 225))
            p.drawPolygon(QPolygonF([P(x, y) for x, y in pt['corners']]))
            if k:
                c0 = pt['corners']
                mx = sum(c[0] for c in c0) / len(c0)
                my = sum(c[1] for c in c0) / len(c0)
                q = P(mx, my)
                p.drawText(QRectF(q.x() - 40, q.y() - 9, 80, 18), Qt.AlignCenter, pt.get('name', ''))
        for o in r.get('openings') or []:
            pcs = parts[int(o.get('part', 0))]['corners'] if int(o.get('part', 0)) < len(parts) else cs
            i = int(o['wall'])
            if not 0 <= i < len(pcs):
                continue
            a, b = pcs[i], pcs[(i + 1) % len(pcs)]
            L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
            u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
            q0 = P(a[0] + u[0] * o['s0'], a[1] + u[1] * o['s0'])
            q1 = P(a[0] + u[0] * o['s1'], a[1] + u[1] * o['s1'])
            p.setPen(QPen(QColor(220, 120, 30) if o['kind'] == 'door' else QColor(40, 130, 210), 4))
            p.drawLine(q0, q1)
        p.setPen(dark)
        for i in range(n):
            a, b = cs[i], cs[(i + 1) % n]
            m = P((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
            p.drawText(QRectF(m.x() - 30, m.y() - 9, 60, 18), Qt.AlignCenter,
                       "%d: %.0f" % (i + 1, math.hypot(b[0] - a[0], b[1] - a[1])))
        # the front wall (wall 1), with its windows and doors
        top0 = 40 + half
        p.drawText(QRectF(10, top0 - 18, 300, 18), Qt.AlignLeft, "The front (wall 1)")
        a, b = cs[0], cs[1 % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        Hh = max(float(r.get('ridge') or 0.0), float(r['eaves']))
        k2 = min(Wd / L, (half - 20) / Hh)
        ex, ey = 20 + (Wd - L * k2) / 2.0, top0 + (half - 20 + Hh * k2) / 2.0

        def F(s, z):
            return QPointF(ex + s * k2, ey - z * k2)
        p.setBrush(QColor(196, 120, 90))
        p.drawPolygon(QPolygonF([F(0, 0), F(L, 0), F(L, r['eaves']), F(0, r['eaves'])]))
        roof = r.get('roof')
        if r.get('ridge') and roof in ('gable_across',):
            p.setBrush(QColor(170, 100, 75))
            p.drawPolygon(QPolygonF([F(0, r['eaves']), F(L, r['eaves']), F(L / 2.0, r['ridge'])]))
        elif r.get('ridge') and roof in ('gable_len', 'hip', 'mono'):
            p.setBrush(QColor(110, 110, 120))
            inset = 0.0 if roof != 'hip' else min(L / 2.0, float(r.get('width') or 0) / 2.0)
            p.drawPolygon(QPolygonF([F(0, r['eaves']), F(L, r['eaves']), F(L - inset, r['ridge']),
                                     F(inset, r['ridge'])]))
        for o in r.get('openings') or []:
            if int(o['wall']) != 0 or int(o.get('part', 0)) != 0:
                continue
            p.setBrush(QColor(90, 60, 40) if o['kind'] == 'door' else QColor(200, 225, 240))
            if o.get('shape'):
                p.drawPolygon(QPolygonF([F(a_, b_) for a_, b_ in o['shape']]))
            else:
                p.drawRect(QRectF(F(o['s0'], o['z1']), F(o['s1'], o['z0'])))
        p.setPen(dark)
        p.drawText(QRectF(10, self.height() - 22, self.width() - 20, 18), Qt.AlignLeft,
                   "%.0f x %.0f mm, eaves %.0f mm%s" % (r.get('length', 0), r.get('width', 0), r['eaves'],
                                                        (", top of roof %.0f mm" % r['ridge']) if r.get('ridge') else ""))
        p.end()


# ---------------------------------------------------------------------------
# Changing the plan: move and resize the parts with the mouse, copy one to the other end
# ---------------------------------------------------------------------------
ADJUSTED_NAME = "building from photo - plan changed.json"
MIN_SIDE = 200.0            # mm - the smallest a part can be made
ROUND_TO = 10.0             # mm - sizes and moves go in steps of this (when nothing's snapped to)


def _frame(corners):
    """A part's own directions: (corner 1, along wall 1, into the part)."""
    a, b = corners[0], corners[1 % len(corners)]
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    return (a[0], a[1]), u, (-u[1], u[0])


def _to_fr(fr, p):
    o, u, v = fr
    dx, dy = p[0] - o[0], p[1] - o[1]
    return dx * u[0] + dy * u[1], dx * v[0] + dy * v[1]


def _from_fr(fr, a, b):
    o, u, v = fr
    return [o[0] + u[0] * a + v[0] * b, o[1] + u[1] * a + v[1] * b]


def _box(fr, corners):
    pts = [_to_fr(fr, c) for c in corners]
    return (min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts))


def _wall_len(cs, i):
    a, b = cs[i % len(cs)], cs[(i + 1) % len(cs)]
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _inside(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1:
            inside = not inside
    return inside


def tidy_part(r, pi):
    """A part's sizes after its corners have changed (as the 3D program gives them: across and back)."""
    pt = r['parts'][pi]
    pt['corners'] = [[round(c[0], 1), round(c[1], 1)] for c in pt['corners']]
    xs = [c[0] for c in pt['corners']]
    ys = [c[1] for c in pt['corners']]
    pt['length'] = round(max(xs) - min(xs), 1)
    pt['width'] = round(max(ys) - min(ys), 1)
    if pi == 0:                                        # the main building's are on the top level too
        for k in ('corners', 'length', 'width'):
            r[k] = copy.deepcopy(pt[k])


def refit_on_walls(r, start, pi):
    """Keeps a part's windows, doors and roof gables on its walls after it's been resized: each stays the
    same size, its middle the same share of the way along the wall."""
    old = start['parts'][pi]['corners']
    new = r['parts'][pi]['corners']
    for key in ('openings', 'gables'):
        items = []
        for o0 in start.get(key) or []:
            o = copy.deepcopy(o0)
            if int(o.get('part', 0)) == pi:
                i = int(o.get('wall', 0))
                L0, L1 = _wall_len(old, i), _wall_len(new, i)
                if L0 > 1.0 and abs(L1 - L0) > 0.05:
                    s0, s1 = float(o['s0']), float(o['s1'])
                    mid = (s0 + s1) / 2.0
                    d = mid * L1 / L0 - mid
                    if s1 + d > L1:                          # keep it on the wall if it'll fit
                        d = L1 - s1
                    if s0 + d < 0.0:
                        d = -s0
                    o['s0'], o['s1'] = round(s0 + d, 1), round(s1 + d, 1)
                    if o.get('shape'):
                        o['shape'] = [[round(s + d, 1), z] for s, z in o['shape']]
            items.append(o)
        if key in start or items:
            r[key] = items


def _next_name(r, name):
    import re
    names = set(pt.get('name', '') for pt in r['parts'])
    m = re.match(r"^(.*?)\s*(\d+)$", name or "")
    base, n = (m.group(1), int(m.group(2))) if m else ((name or "Part"), 1)
    n = 0                                              # the lowest number not in use
    while True:
        n += 1
        cand = "%s %d" % (base, n)
        if cand not in names:
            return cand


def mirror_part(r, pi):
    """A copy of a part on the other end of the main building (mirrored about its middle, as you look at the
    front), with its windows, doors and roof gables. Returns the new part's number."""
    parts = r['parts']
    xs = [c[0] for c in parts[0]['corners']]
    mid = (min(xs) + max(xs)) / 2.0
    src = parts[pi]
    cs = src['corners']
    n = len(cs)
    m = lambda c: [round(2.0 * mid - c[0], 1), c[1]]
    new = copy.deepcopy(src)
    new['corners'] = [m(cs[(1 - k) % n]) for k in range(n)]    # anticlockwise again; wall 1 still wall 1
    # a part already standing there (the other bay) is replaced by the copy
    nx_ = [c[0] for c in new['corners']]
    ny_ = [c[1] for c in new['corners']]
    for k in range(len(parts) - 1, 0, -1):
        if k == pi:
            continue
        c_ = parts[k]['corners']
        cx = sum(c[0] for c in c_) / len(c_)
        cy = sum(c[1] for c in c_) / len(c_)
        if min(nx_) <= cx <= max(nx_) and min(ny_) - 1.0 <= cy <= max(ny_) + 1.0:
            new['_was'] = parts[k].get('name')
            remove_part(r, k)
            if k < pi:
                pi -= 1
    src = parts[pi]
    new['name'] = new.pop('_was', None) or _next_name(r, src.get('name', 'Part'))
    parts.append(new)
    ni = len(parts) - 1
    tidy_part(r, ni)
    for key in ('openings', 'gables'):
        for o in list(r.get(key) or []):
            if int(o.get('part', 0)) != pi:
                continue
            i = int(o.get('wall', 0))
            L = _wall_len(cs, i)
            o2 = copy.deepcopy(o)
            o2['part'], o2['wall'] = ni, (-i) % n
            o2['s0'], o2['s1'] = round(L - float(o['s1']), 1), round(L - float(o['s0']), 1)
            if o.get('shape'):
                o2['shape'] = [[round(L - s, 1), z] for s, z in reversed(o['shape'])]
            r[key].append(o2)
    keep_on_walls(r)
    return ni


def keep_on_walls(r):
    """Windows, doors and roof gables that have ended up past the end of their wall slid back onto it."""
    for key in ('openings', 'gables'):
        for o in r.get(key) or []:
            pi = int(o.get('part', 0))
            if not 0 <= pi < len(r['parts']):
                continue
            L = _wall_len(r['parts'][pi]['corners'], int(o.get('wall', 0)))
            s0, s1 = float(o['s0']), float(o['s1'])
            d = 0.0
            if s1 > L:
                d = L - s1
            if s0 + d < 0.0:
                d = -s0
            if abs(d) > 0.05:
                o['s0'], o['s1'] = round(s0 + d, 1), round(s1 + d, 1)
                if o.get('shape'):
                    o['shape'] = [[round(a_ + d, 1), b_] for a_, b_ in o['shape']]


def remove_part(r, pi):
    """Takes a part off (not the main building), with its windows, doors and roof gables."""
    if pi <= 0 or pi >= len(r['parts']):
        return
    del r['parts'][pi]
    for key in ('openings', 'gables'):
        keep = []
        for o in r.get(key) or []:
            k = int(o.get('part', 0))
            if k == pi:
                continue
            if k > pi:
                o['part'] = k - 1
            keep.append(o)
        if key in r:
            r[key] = keep


class PlanCanvas(QWidget):
    """The plan, looking down, to change with the mouse - like resizing a window: drag a part to move it,
    drag its edges or corners to make it bigger or smaller."""
    HANDLES = [('l', 'b'), ('', 'b'), ('r', 'b'), ('r', ''), ('r', 't'), ('', 't'), ('l', 't'), ('l', '')]

    def __init__(self, editor):
        super().__init__(editor)
        self.ed = editor
        self.k = 0.05                     # pixels per mm
        self.ox, self.oy = 0.0, 0.0
        self.drag = None
        self.pan = None
        self.snap_line = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(560, 460)
        self._fitted = False

    # ---- mm <-> screen ----
    def S(self, x, y):
        return QPointF(self.ox + x * self.k, self.oy - y * self.k)

    def W(self, pos):
        return ((pos.x() - self.ox) / self.k, (self.oy - pos.y()) / self.k)

    def fit(self):
        parts = self.ed.r['parts']
        xs = [c[0] for pt in parts for c in pt['corners']]
        ys = [c[1] for pt in parts for c in pt['corners']]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        W_, H_ = (x1 - x0) or 1000.0, (y1 - y0) or 1000.0
        x0, x1 = x0 - 0.35 * W_, x1 + 0.35 * W_        # room either side to drag and copy into
        y0, y1 = y0 - 0.25 * H_, y1 + 0.25 * H_
        self.k = max(1e-4, min((self.width() - 40) / (x1 - x0), (self.height() - 60) / (y1 - y0)))
        self.ox = (self.width() - (x1 - x0) * self.k) / 2.0 - x0 * self.k
        self.oy = (self.height() + (y1 - y0) * self.k) / 2.0 + y0 * self.k + 10
        self._fitted = True
        self.update()

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if not self._fitted or not self.drag:
            self.fit()

    # ---- what's under the mouse ----
    def handle_at(self, pos):
        """(edges, part) of a handle or edge of the selected part under the mouse; ('move', part) inside it."""
        pi = self.ed.sel
        if pi is None or pi >= len(self.ed.r['parts']):
            return None
        cs = self.ed.r['parts'][pi]['corners']
        fr = _frame(cs)
        u0, u1, v0, v1 = _box(fr, cs)
        a, b = _to_fr(fr, self.W(pos))
        tol = 7.0 / self.k
        if u0 - tol <= a <= u1 + tol and v0 - tol <= b <= v1 + tol:
            h = ('l' if abs(a - u0) <= tol else 'r' if abs(a - u1) <= tol else '',
                 'b' if abs(b - v0) <= tol else 't' if abs(b - v1) <= tol else '')
            if h != ('', ''):
                return h, pi
        if _inside(self.W(pos), cs):
            return 'move', pi
        return None

    def part_at(self, pos):
        w = self.W(pos)
        parts = self.ed.r['parts']
        for pi in range(len(parts) - 1, -1, -1):           # the extensions sit on top of the main building
            if _inside(w, parts[pi]['corners']):
                return pi
        return None

    def _cursor_for(self, h, pi):
        if h is None:
            return Qt.ArrowCursor
        if h == 'move':
            return Qt.ArrowCursor if pi == 0 else Qt.SizeAllCursor
        cs = self.ed.r['parts'][pi]['corners']
        _o, u, v = _frame(cs)
        dx = dy = 0.0
        if h[0]:
            dx, dy = dx + u[0], dy + u[1]
        if h[1]:
            s = 1.0 if (h[0] == 'r') == (h[1] == 't') else -1.0
            dx, dy = dx + s * v[0], dy + s * v[1]
        ang = math.degrees(math.atan2(dy, dx)) % 180.0      # up the screen is +y here, as on the plan
        if ang < 22.5 or ang >= 157.5:
            return Qt.SizeHorCursor
        if ang < 67.5:
            return Qt.SizeBDiagCursor
        if ang < 112.5:
            return Qt.SizeVerCursor
        return Qt.SizeFDiagCursor

    # ---- the mouse ----
    def mousePressEvent(self, ev):
        self.setFocus()
        if ev.button() in (Qt.RightButton, Qt.MiddleButton):
            self.pan = (ev.position(), self.ox, self.oy)
            self.setCursor(Qt.ClosedHandCursor)
            return
        if ev.button() != Qt.LeftButton:
            return
        hit = self.handle_at(ev.position())
        if hit is None:
            pi = self.part_at(ev.position())
            self.ed.select(pi)
            if pi is None:
                return
            hit = ('move', pi)
        h, pi = hit
        if h == 'move' and pi == 0:
            self.ed.select(0)
            self.ed.say("The main building stays put - drag its edges or corners to change its size, or move "
                        "the parts to it.")
            return
        cs = self.ed.r['parts'][pi]['corners']
        fr = _frame(cs)
        self.drag = dict(h=h, pi=pi, start=copy.deepcopy(self.ed.r), fr=fr, box=_box(fr, cs),
                         at=_to_fr(fr, self.W(ev.position())), w0=self.W(ev.position()), moved=False)

    def mouseMoveEvent(self, ev):
        pos = ev.position()
        if self.pan:
            p0, ox, oy = self.pan
            self.ox, self.oy = ox + pos.x() - p0.x(), oy + pos.y() - p0.y()
            self.update()
            return
        if not self.drag:
            hit = self.handle_at(pos)
            self.setCursor(self._cursor_for(hit[0], hit[1]) if hit else Qt.ArrowCursor)
            return
        d = self.drag
        free = bool(ev.modifiers() & Qt.ControlModifier)    # Ctrl: no snapping
        a, b = _to_fr(d['fr'], self.W(pos))
        if d['h'] == 'move':
            self._do_move(d, a - d['at'][0], b - d['at'][1], free)
        else:
            self._do_resize(d, a - d['at'][0], b - d['at'][1], free)
        d['moved'] = True
        self.ed.changed_live()
        self.update()

    def mouseReleaseEvent(self, ev):
        if self.pan:
            self.pan = None
            self.setCursor(Qt.ArrowCursor)
            return
        d, self.drag = self.drag, None
        self.snap_line = None
        if d and d['moved']:
            self.ed.push_undo(d['start'])
            self.ed.changed_done()
        self.update()

    def wheelEvent(self, ev):
        pos = ev.position()
        wx, wy = self.W(pos)
        f = 1.15 if ev.angleDelta().y() > 0 else 1 / 1.15
        self.k = min(max(self.k * f, 0.002), 5.0)
        self.ox = pos.x() - wx * self.k
        self.oy = pos.y() + wy * self.k
        self.update()

    def keyPressEvent(self, ev):
        key = ev.key()
        step = 100.0 if ev.modifiers() & Qt.ShiftModifier else ROUND_TO
        moves = {Qt.Key_Left: (-step, 0), Qt.Key_Right: (step, 0), Qt.Key_Up: (0, step), Qt.Key_Down: (0, -step)}
        if key in moves and self.ed.sel:
            self.ed.nudge(*moves[key])
        elif key in (Qt.Key_Delete, Qt.Key_Backspace):
            self.ed.take_off()
        elif key == Qt.Key_Z and ev.modifiers() & Qt.ControlModifier:
            self.ed.undo()
        else:
            super().keyPressEvent(ev)

    # ---- snapping ----
    def _targets(self, fr, pi, start):
        """Where the edges of a part can snap to: the corners of every other part, in this part's directions."""
        us, vs = [], []
        for k, pt in enumerate(start['parts']):
            if k == pi:
                continue
            for c in pt['corners']:
                a, b = _to_fr(fr, c)
                us.append(a)
                vs.append(b)
        return us, vs

    @staticmethod
    def _nearest(val, cands, tol):
        best = None
        for c in cands:
            if abs(c - val) <= tol and (best is None or abs(c - val) < abs(best - val)):
                best = c
        return best

    def _do_move(self, d, du, dv, free):
        fr, (u0, u1, v0, v1) = d['fr'], d['box']
        snapped = []
        if not free:
            us, vs = self._targets(fr, d['pi'], d['start'])
            tol = 9.0 / self.k
            best_u = None
            for edge in (u0, u1):
                c = self._nearest(edge + du, us, tol)
                if c is not None and (best_u is None or abs(c - edge - du) < abs(best_u)):
                    best_u = c - edge - du
            best_v = None
            for edge in (v0, v1):
                c = self._nearest(edge + dv, vs, tol)
                if c is not None and (best_v is None or abs(c - edge - dv) < abs(best_v)):
                    best_v = c - edge - dv
            du = du + best_u if best_u is not None else round(du / ROUND_TO) * ROUND_TO
            dv = dv + best_v if best_v is not None else round(dv / ROUND_TO) * ROUND_TO
            snapped = [x for x in (best_u, best_v) if x is not None]
        r = copy.deepcopy(d['start'])
        pt = r['parts'][d['pi']]
        pt['corners'] = [_from_fr(fr, a + du, b + dv) for a, b in (_to_fr(fr, c) for c in pt['corners'])]
        tidy_part(r, d['pi'])
        self.ed.r = r
        self.snap_line = bool(snapped)

    def _do_resize(self, d, du, dv, free):
        fr, (u0, u1, v0, v1) = d['fr'], d['box']
        hu, hv = d['h']
        nu0, nu1, nv0, nv1 = u0, u1, v0, v1
        us, vs = self._targets(fr, d['pi'], d['start']) if not free else ([], [])
        tol = 9.0 / self.k
        snapped = False

        def place(val, fixed, cands, grow):
            nonlocal snapped
            c = self._nearest(val, cands, tol)
            if c is not None:
                snapped = True
                val = c
            elif not free:
                val = fixed + grow * round(abs(val - fixed) / ROUND_TO) * ROUND_TO
            if grow * (val - fixed) < MIN_SIDE:
                val = fixed + grow * MIN_SIDE
            return val
        if hu == 'l':
            nu0 = place(u0 + du, u1, us, -1.0)
        elif hu == 'r':
            nu1 = place(u1 + du, u0, us, 1.0)
        if hv == 'b':
            nv0 = place(v0 + dv, v1, vs, -1.0)
        elif hv == 't':
            nv1 = place(v1 + dv, v0, vs, 1.0)
        self.ed.r = resized(d['start'], d['pi'], fr, (u0, u1, v0, v1), (nu0, nu1, nv0, nv1))
        self.snap_line = snapped

    # ---- drawing ----
    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QPolygonF, QFont
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(252, 252, 250))
        r = self.ed.r
        # the grid: 1 m squares (and 100 mm ones when zoomed in)
        x0, y1 = self.W(QPointF(0, 0))
        x1, y0 = self.W(QPointF(self.width(), self.height()))
        for step, col in ((100.0, QColor(240, 240, 238)), (1000.0, QColor(222, 222, 218))):
            if step * self.k < 8:
                continue
            p.setPen(QPen(col, 1))
            x = math.floor(x0 / step) * step
            while x <= x1:
                p.drawLine(self.S(x, y0), self.S(x, y1))
                x += step
            y = math.floor(y0 / step) * step
            while y <= y1:
                p.drawLine(self.S(x0, y), self.S(x1, y))
                y += step
        parts = r['parts']
        # the middle of the main building (copies go the other side of it)
        xs = [c[0] for c in parts[0]['corners']]
        mid = (min(xs) + max(xs)) / 2.0
        pen = QPen(QColor(150, 150, 150), 1, Qt.DashLine)
        p.setPen(pen)
        p.drawLine(self.S(mid, y0), self.S(mid, y1))
        p.drawText(QRectF(self.S(mid, y1).x() + 4, 4, 140, 16), Qt.AlignLeft, "middle of the main building")
        bold = QFont(p.font())
        bold.setBold(True)
        for k, pt in enumerate(parts):
            sel = k == self.ed.sel
            p.setPen(QPen(QColor(30, 90, 200) if sel else QColor(60, 60, 60), 2.2 if sel else 1.2))
            p.setBrush(QColor(235, 220, 200) if k == 0 else QColor(215, 205, 225))
            p.drawPolygon(QPolygonF([self.S(x, y) for x, y in pt['corners']]))
        # windows and doors along the walls
        for o in r.get('openings') or []:
            pi = int(o.get('part', 0))
            if not 0 <= pi < len(parts):
                continue
            cs = parts[pi]['corners']
            i = int(o.get('wall', 0))
            if not 0 <= i < len(cs):
                continue
            a, b = cs[i], cs[(i + 1) % len(cs)]
            L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
            u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
            p.setPen(QPen(QColor(220, 120, 30) if o.get('kind') == 'door' else QColor(40, 130, 210), 4))
            p.drawLine(self.S(a[0] + u[0] * o['s0'], a[1] + u[1] * o['s0']),
                       self.S(a[0] + u[0] * o['s1'], a[1] + u[1] * o['s1']))
        # names, and the wall lengths of the one picked
        for k, pt in enumerate(parts):
            cs = pt['corners']
            mx = sum(c[0] for c in cs) / len(cs)
            my = sum(c[1] for c in cs) / len(cs)
            q = self.S(mx, my)
            p.setPen(QColor(40, 40, 40))
            p.setFont(bold)
            p.drawText(QRectF(q.x() - 80, q.y() - 18, 160, 18), Qt.AlignCenter, pt.get('name', '') or "Part")
            p.setFont(QFont())
            fr = _frame(cs)
            u0, u1, v0, v1 = _box(fr, cs)
            p.drawText(QRectF(q.x() - 80, q.y(), 160, 18), Qt.AlignCenter, "%.0f x %.0f mm" % (u1 - u0, v1 - v0))
        sel = self.ed.sel
        if sel is not None and sel < len(parts):
            cs = parts[sel]['corners']
            n = len(cs)
            p.setPen(QColor(30, 90, 200))
            for i in range(n):
                a, b = cs[i], cs[(i + 1) % n]
                m = self.S((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
                p.drawText(QRectF(m.x() - 40, m.y() - 9, 80, 18), Qt.AlignCenter, "%.0f" % _wall_len(cs, i))
            # the handles, like the corners and sides of a window
            fr = _frame(cs)
            u0, u1, v0, v1 = _box(fr, cs)
            um, vm = (u0 + u1) / 2.0, (v0 + v1) / 2.0
            p.setPen(QPen(QColor(30, 90, 200), 1.2))
            p.setBrush(QColor(255, 255, 255))
            for hu, hv in self.HANDLES:
                a = u0 if hu == 'l' else u1 if hu == 'r' else um
                b = v0 if hv == 'b' else v1 if hv == 't' else vm
                q = self.S(*_from_fr(fr, a, b))
                p.drawRect(QRectF(q.x() - 4, q.y() - 4, 8, 8))
        if self.snap_line:
            p.setPen(QColor(0, 140, 60))
            p.drawText(QRectF(8, self.height() - 20, 300, 18), Qt.AlignLeft, "Lined up")
        p.end()


def resized(start, pi, fr, old_box, new_box):
    """The building with part pi stretched from one box (in its own directions) to another, its windows,
    doors and gables kept on its walls."""
    u0, u1, v0, v1 = old_box
    nu0, nu1, nv0, nv1 = new_box
    su = (nu1 - nu0) / ((u1 - u0) or 1.0)
    sv = (nv1 - nv0) / ((v1 - v0) or 1.0)
    r = copy.deepcopy(start)
    pt = r['parts'][pi]
    pt['corners'] = [_from_fr(fr, nu0 + (a - u0) * su, nv0 + (b - v0) * sv)
                     for a, b in (_to_fr(fr, c) for c in pt['corners'])]
    tidy_part(r, pi)
    refit_on_walls(r, start, pi)
    return r


# ---------------------------------------------------------------------------
# Moving the windows and doors after it's built
# ---------------------------------------------------------------------------
WALL_ORIG = {}          # id(wall group): (group, its mesh before any windows or doors were cut) - this session


def wall_list(r):
    """Every wall of every part: [(part, wall, name, length mm, height mm)]."""
    out = []
    for pi, part in enumerate(r.get('parts') or []):
        cs = part.get('corners') or []
        n = len(cs)
        for i in range(n):
            a, b = cs[i], cs[(i + 1) % n]
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L < 1.0:
                continue
            k = sum(1 for o in r.get('openings') or [] if int(o.get('part', 0)) == pi and int(o.get('wall', 0)) == i)
            out.append((pi, i, "%s - wall %d%s" % (part.get('name') or "Part %d" % (pi + 1), i + 1,
                                                    "  (%d)" % k if k else ""), L, float(part.get('eaves') or 3000.0)))
    return out


# ---------------------------------------------------------------------------
# Moving the windows and doors on the model itself
# ---------------------------------------------------------------------------
ZREF = {}               # part index: the bottom of its walls in the model (metres), from the last cut
SNAP_MM = 80.0          # how near (mm) an edge must come to another's to snap to it


def op_set_box(o, s0, s1, z0, z1):
    """New box for an opening (mm along and up its wall): a traced outline is stretched to fit."""
    s0, s1 = sorted((s0, s1))
    z0, z1 = sorted((z0, z1))
    if s1 - s0 < 50.0 or z1 - z0 < 50.0:
        return
    if o.get('shape'):
        os0, os1, oz0, oz1 = o['s0'], o['s1'], o['z0'], o['z1']
        fx = (s1 - s0) / max(os1 - os0, 1e-6)
        fz = (z1 - z0) / max(oz1 - oz0, 1e-6)
        o['shape'] = [[round(s0 + (a - os0) * fx, 1), round(z0 + (b - oz0) * fz, 1)] for a, b in o['shape']]
    o['s0'], o['s1'], o['z0'], o['z1'] = round(s0, 1), round(s1, 1), round(z0, 1), round(z1, 1)


def box_round_shapes(r):
    for o in r.get('openings') or []:
        if o.get('shape'):
            o['s0'], o['s1'] = min(q[0] for q in o['shape']), max(q[0] for q in o['shape'])
            o['z0'], o['z1'] = min(q[1] for q in o['shape']), max(q[1] for q in o['shape'])


class ModelMover:
    """What the 'move on the model' tool is doing: picking a window or door up, carrying it along its wall
    (its edges snapping to the others'), and lining others up to it."""

    LINE = {'P': "same size and place", 'T': "tops", 'B': "bottoms", 'H': "tops and bottoms", 'C': "centred over/under it",
            'S': "same size, tops in line"}

    def __init__(self, dlg):
        self.dlg = dlg
        self.reset()

    def reset(self):
        self.carry = None        # (index, box before, grab offset along, grab offset up)
        self.ref = None          # the one the others line up to
        self.how = 'P'
        self.hover = None        # the opening under the mouse
        self.multi = []          # Shift + clicked: lined up together with Line these up
        self.edge = None         # stretching: which edges ('l', 'r', 't', 'b') follow the mouse
        self.vp = getattr(self.dlg, 'viewport', None)
        self.undos = []
        self.lock = None         # arrow keys: 'along' (left/right only) or 'up' (up/down only)

    @property
    def r(self):
        return self.dlg.result

    # where things are
    def wall_frame(self, pi, wi):
        cs = self.r['parts'][pi]['corners']
        a, b = cs[wi % len(cs)], cs[(wi + 1) % len(cs)]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        return a, u, (u[1], -u[0]), L

    def on_wall(self, p, pi, wi):
        """(along, up, out) of a model point (metres) against a wall, mm."""
        a, u, n, _L = self.wall_frame(pi, wi)
        x, y = p[0] / SCALE - a[0], p[1] / SCALE - a[1]
        return x * u[0] + y * u[1], (p[2] - ZREF.get(pi, 0.0)) / SCALE, x * n[0] + y * n[1]

    def eye(self):
        """Where you're looking from (model metres), or None."""
        try:
            cam = self.vp.camera
            e = cam.eye() if callable(getattr(cam, 'eye', None)) else cam.eye
            return (float(e.x()), float(e.y()), float(e.z())) if hasattr(e, 'x') else tuple(float(c) for c in e[:3])
        except Exception:
            return None

    def through_wall(self, p, pi, wi):
        """Where the line from your eye to p crosses the wall's outside face: (along, up, how far along the line),
        or None."""
        e = self.eye()
        if e is None:
            return None
        se, ze, de = self.on_wall(e, pi, wi)
        sp, zp, dp = self.on_wall(p, pi, wi)
        if abs(de - dp) < 1e-6:
            return None
        t = de / (de - dp)
        if t < -0.05:
            return None
        return se + t * (sp - se), ze + t * (zp - ze), t, de

    def opening_at(self, p):
        e = self.eye()
        if e is not None:                                 # the first window the line from your eye goes through
            best = None
            for k, o in enumerate(self.r.get('openings') or []):
                pi, wi = int(o.get('part', 0)), int(o.get('wall', 0))
                if pi not in ZREF:
                    continue
                h = self.through_wall(p, pi, wi)
                if h is None:
                    continue
                s, z, t, de = h
                if de <= 0 or t > 1.05:
                    continue                              # looking at the wall from inside, or it's past the click
                if o['s0'] - 30.0 <= s <= o['s1'] + 30.0 and o['z0'] - 30.0 <= z <= o['z1'] + 30.0:
                    if best is None or t < best[0]:
                        best = (t, k)
            if best is not None:
                return best[1]
        best = None
        wt = float(load_settings().get('wall_t') or 230.0)
        for k, o in enumerate(self.r.get('openings') or []):
            pi, wi = int(o.get('part', 0)), int(o.get('wall', 0))
            if pi not in ZREF:
                continue
            s, z, d = self.on_wall(p, pi, wi)
            if not (-wt - 80.0 <= d <= 80.0):
                continue
            if o['s0'] - 40.0 <= s <= o['s1'] + 40.0 and o['z0'] - 40.0 <= z <= o['z1'] + 40.0:
                area = (o['s1'] - o['s0']) * (o['z1'] - o['z0'])
                if best is None or area < best[0]:
                    best = (area, k)
        return best[1] if best else None

    def still_over(self, k, p):
        """Is the mouse still looking through opening k (the point it lands on is behind its wall, in line with it)?"""
        o = self.r['openings'][k]
        s, z, d = self.on_wall(p, int(o.get('part', 0)), int(o.get('wall', 0)))
        return d < 80.0 and o['s0'] - 40.0 <= s <= o['s1'] + 40.0 and o['z0'] - 40.0 <= z <= o['z1'] + 40.0

    def log_miss(self, p, what="missed"):
        """A click that found no window: where it was against every opening's wall, written to a file next to the
        plugin (for working out why)."""
        try:
            names = opening_names(self.r)
            lines = ["%s  %s at %.4f, %.4f, %.4f (m)   ZREF %s" % (time.strftime("%H:%M:%S"), what, p[0], p[1], p[2],
                                                                     {k: round(v, 4) for k, v in ZREF.items()})]
            for k, o in enumerate(self.r.get('openings') or []):
                pi, wi = int(o.get('part', 0)), int(o.get('wall', 0))
                s_, z_, d_ = self.on_wall(p, pi, wi)
                lines.append("  %-10s part %d wall %d kind %s  box s %.0f-%.0f z %.0f-%.0f  | click s %.0f z %.0f out %.0f%s"
                             % (names[k], pi, wi, o.get('kind'), o['s0'], o['s1'], o['z0'], o['z1'], s_, z_, d_,
                                "  shape" if o.get('shape') else ""))
            for pi, pt in enumerate(self.r.get('parts') or []):
                lines.append("  part %d %s corners %s" % (pi, pt.get('name'), pt.get('corners')))
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "photo_to_building_clicks.txt"), "a",
                      encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n\n")
        except Exception as e:
            print("%s: click log: %s" % (PLUGIN_NAME, e))

    def look(self, p):
        """The opening under the mouse: one whose edge or reveal it's on, or (looking through the hole, where it
        lands on something further in) the one it was last on, while it's still in line with it."""
        k = self.opening_at(p)
        if k is None and self.hover is not None and self.still_over(self.hover, p):
            k = self.hover
        if k is None:
            k = self.through(p)
        self.hover = k
        return k

    def through(self, p):
        """Looking through a hole: the point landed on something behind a wall - the opening it's behind (in line
        with it, allowing for looking at it a bit from the side the further in it lands)."""
        best = None
        for k, o in enumerate(self.r.get('openings') or []):
            pi, wi = int(o.get('part', 0)), int(o.get('wall', 0))
            if pi not in ZREF:
                continue
            s, z, d = self.on_wall(p, pi, wi)
            if not (-15000.0 < d < -20.0):
                continue                                  # not behind this wall
            slack = 40.0 + 0.6 * abs(d)
            if o['s0'] - slack <= s <= o['s1'] + slack and o['z0'] - slack <= z <= o['z1'] + slack:
                cs, cz = (o['s0'] + o['s1']) / 2.0, (o['z0'] + o['z1']) / 2.0
                score = math.hypot(s - cs, z - cz) + 0.2 * abs(d)
                if best is None or score < best[0]:
                    best = (score, k)
        return best[1] if best else None

    def others(self, k):
        o = self.r['openings'][k]
        return [x for i, x in enumerate(self.r['openings']) if i != k and int(x.get('part', 0)) == int(o.get('part', 0))
                and int(x.get('wall', 0)) == int(o.get('wall', 0))]

    # doing things
    def save_undo(self):
        self.undos.append(copy.deepcopy(self.r['openings']))
        del self.undos[:-30]

    def pick(self, k, p):
        o = self.r['openings'][k]
        s, z, _d = self.on_wall(p, int(o.get('part', 0)), int(o.get('wall', 0)))
        h_ = self.through_wall(p, int(o.get('part', 0)), int(o.get('wall', 0)))
        if h_ is not None and h_[3] > 0:
            s, z = h_[0], h_[1]
        self.carry = (k, copy.deepcopy(o), s - o['s0'], z - o['z0'])
        # near an edge or corner: stretch it there; in the middle: move it
        w, h = o['s1'] - o['s0'], o['z1'] - o['z0']
        ts, tz = min(150.0, 0.25 * w), min(150.0, 0.2 * h)
        e = ""
        if abs(s - o['s0']) < ts:
            e += "l"
        elif abs(s - o['s1']) < ts:
            e += "r"
        if abs(z - o['z1']) < tz:
            e += "t"
        elif abs(z - o['z0']) < tz:
            e += "b"
        self.edge = e or None

    def follow(self, p):
        if self.carry is None or (abs(p[0]) + abs(p[1]) + abs(p[2]) < 1e-9):
            return                                        # nothing under the mouse: stay where it is
        k, o0, ds, dz = self.carry
        o = self.r['openings'][k]
        s, z, _d = self.on_wall(p, int(o.get('part', 0)), int(o.get('wall', 0)))
        h_ = self.through_wall(p, int(o.get('part', 0)), int(o.get('wall', 0)))
        if h_ is not None and h_[3] > 0:                  # slides along its wall, under the mouse
            s, z = h_[0], h_[1]
        if getattr(self, 'edge', None):                   # stretching: the grabbed edges follow the mouse
            s0, s1, z0, z1 = o0['s0'], o0['s1'], o0['z0'], o0['z1']
            s, z = round(s / 25.0) * 25.0, round(z / 25.0) * 25.0      # steady 25 mm steps
            for x in self.others(k):                      # snapping to the others' edges
                for e_ in (x['s0'], x['s1']):
                    if abs(e_ - s) < SNAP_MM:
                        s = e_
                for e_ in (x['z0'], x['z1']):
                    if abs(e_ - z) < SNAP_MM:
                        z = e_
            if 'l' in self.edge:
                s0 = min(s, s1 - 50.0)
            if 'r' in self.edge:
                s1 = max(s, s0 + 50.0)
            if 't' in self.edge:
                z1 = max(z, z0 + 50.0)
            if 'b' in self.edge:
                z0 = min(max(z, 0.0), z1 - 50.0)
            o.clear()
            o.update(copy.deepcopy(o0))
            op_set_box(o, s0, s1, z0, z1)
            return
        w, h = o0['s1'] - o0['s0'], o0['z1'] - o0['z0']
        s0, z0 = s - ds, z - dz
        if self.lock == 'up':
            s0 = o0['s0']
        elif self.lock == 'along':
            z0 = o0['z0']
        bs, bz = None, None
        for x in self.others(k):
            for mine, theirs in ((s0, x['s0']), (s0 + w, x['s1']), (s0 + w / 2.0, (x['s0'] + x['s1']) / 2.0),
                                 (s0, x['s1']), (s0 + w, x['s0'])):
                d_ = theirs - mine
                if abs(d_) < SNAP_MM and (bs is None or abs(d_) < abs(bs)):
                    bs = d_
            for mine, theirs in ((z0, x['z0']), (z0 + h, x['z1'])):
                d_ = theirs - mine
                if abs(d_) < SNAP_MM and (bz is None or abs(d_) < abs(bz)):
                    bz = d_
        if o.get('kind') == 'door' and abs(z0) < SNAP_MM:
            bz = -z0
        if self.lock == 'up':
            bs = None
        elif self.lock == 'along':
            bz = None
        s0 += bs or 0.0
        z0 += bz or 0.0
        o.clear()
        o.update(copy.deepcopy(o0))
        op_set_box(o, s0, s0 + w, z0, z0 + h)

    def drop(self):
        if self.carry is None:
            return
        k = self.carry[0]
        self.carry = None
        self.edge = None
        self.lock = None
        self.ref = k
        self.dlg.model_moved()

    def cancel_carry(self):
        if self.carry is None:
            return False
        k, o0 = self.carry[0], self.carry[1]
        o = self.r['openings'][k]
        o.clear()
        o.update(o0)
        self.carry = None
        self.edge = None
        self.lock = None
        if self.undos:
            self.undos.pop()
        return True

    def line_up(self, k):
        if self._line(k, True):
            self.dlg.model_moved()

    def line_up_all(self, every_wall):
        """Every other window (or door, if it's a door) on the picked one's floor - on its wall, or on every
        wall - lined up the chosen way, in one go."""
        if self.ref is None:
            return 0
        ref = self.r['openings'][self.ref]
        lo, hi = ref['z0'], ref['z1']
        self.save_undo()
        n = 0
        for k, o in enumerate(self.r['openings']):
            if k == self.ref or o.get('kind', 'window') != ref.get('kind', 'window'):
                continue
            if not every_wall and (int(o.get('part', 0)) != int(ref.get('part', 0)) or
                                   int(o.get('wall', 0)) != int(ref.get('wall', 0))):
                continue
            if min(hi, o['z1']) - max(lo, o['z0']) <= 0.3 * min(hi - lo, o['z1'] - o['z0']):
                continue                                  # another floor
            if self._line(k, False):
                n += 1
        if n:
            self.dlg.model_moved()
        else:
            self.undos.pop()
        return n

    def _line(self, k, undo):
        ref = self.r['openings'][self.ref]
        o = self.r['openings'][k]
        w, h = o['s1'] - o['s0'], o['z1'] - o['z0']
        s0, z0, z1 = o['s0'], o['z0'], o['z1']
        door = o.get('kind') == 'door' and ref.get('kind') != 'door'
        if self.how == 'P' and not door:                 # the same place on its own wall, the same size
            _a, _u, _n, Lr = self.wall_frame(int(ref.get('part', 0)), int(ref.get('wall', 0)))
            _a, _u, _n, Lo = self.wall_frame(int(o.get('part', 0)), int(o.get('wall', 0)))
            w = ref['s1'] - ref['s0']
            frac = ((ref['s0'] + ref['s1']) / 2.0) / max(Lr, 1e-6)
            m_ = frac * Lo
            s0, z0, z1 = m_ - w / 2.0, ref['z0'], ref['z1']
            if ref.get('shape'):                         # an odd shape: the same shape there
                if undo:
                    self.save_undo()
                o['shape'] = [[round(s0 + (q[0] - ref['s0']), 1), round(z0 + (q[1] - ref['z0']), 1)]
                              for q in ref['shape']]
                o['top'] = ref.get('top', o.get('top'))
                o['s0'], o['s1'], o['z0'], o['z1'] = round(s0, 1), round(s0 + w, 1), round(z0, 1), round(z1, 1)
                return True
        elif self.how == 'S' and not door:
            m_ = (o['s0'] + o['s1']) / 2.0
            w = ref['s1'] - ref['s0']
            s0, z0, z1 = m_ - w / 2.0, ref['z0'], ref['z1']
        elif self.how == 'T' and not door:
            z0, z1 = ref['z1'] - h, ref['z1']
        elif self.how == 'B' and not door:
            z0, z1 = ref['z0'], ref['z0'] + h
        elif self.how == 'H' and not door:
            z0, z1 = ref['z0'], ref['z1']
        elif self.how == 'C':
            s0 = (ref['s0'] + ref['s1']) / 2.0 - w / 2.0
        if abs(s0 - o['s0']) < 0.05 and abs(s0 + w - o['s1']) < 0.05 and abs(z0 - o['z0']) < 0.05 \
                and abs(z1 - o['z1']) < 0.05:
            return False                                  # nothing to change (a door, or already in line)
        if undo:
            self.save_undo()
        op_set_box(o, s0, s0 + w, z0, z1)
        return True

    def line_multi(self):
        """The Shift + clicked ones lined up to the picked one, in one go."""
        if self.ref is None or not self.multi:
            return 0
        self.save_undo()
        rk = self.r['openings'][self.ref].get('kind')
        n = sum(1 for k in list(self.multi) if 0 <= k < len(self.r['openings']) and
                (self.r['openings'][k].get('kind') != 'door' or rk == 'door') and self._line(k, False))
        self.multi = []
        if n:
            self.dlg.model_moved()
        else:
            self.undos.pop()
        return n

    def resize_ref(self, w=None, h=None):
        """The picked one's width / height (mm), kept centred, its top where it was (the one being carried,
        if there is one)."""
        k = self.carry[0] if self.carry is not None else self.ref
        if k is None:
            return
        o = self.r['openings'][k]
        if self.carry is not None:                       # carried: its size goes with it
            o0 = self.carry[1]
            m0 = (o0['s0'] + o0['s1']) / 2.0
            w_ = w if w else o0['s1'] - o0['s0']
            h_ = h if h else o0['z1'] - o0['z0']
            op_set_box(o0, m0 - w_ / 2.0, m0 + w_ / 2.0, o0['z1'] - h_, o0['z1'])
            mo = (o['s0'] + o['s1']) / 2.0
            op_set_box(o, mo - w_ / 2.0, mo + w_ / 2.0, o['z1'] - h_, o['z1'])
            return
        m_ = (o['s0'] + o['s1']) / 2.0
        w = w if w else o['s1'] - o['s0']
        h = h if h else o['z1'] - o['z0']
        if abs(w - (o['s1'] - o['s0'])) < 0.5 and abs(h - (o['z1'] - o['z0'])) < 0.5:
            return
        self.save_undo()
        op_set_box(o, m_ - w / 2.0, m_ + w / 2.0, o['z1'] - h, o['z1'])
        self.dlg.model_moved()

    def undo(self):
        if not self.undos:
            return False
        self.r['openings'][:] = self.undos.pop()
        self.carry = None
        self.dlg.model_moved()
        return True

    def click(self, p):
        if self.carry is not None:
            self.follow(p)
            self.drop()
            return
        k = self.look(p)
        if k is None:
            self.log_miss(p)
            return
        self.log_miss(p, "picked %s" % opening_names(self.r)[k])
        from PySide6.QtWidgets import QApplication as _QA
        if self.ref is not None and k != self.ref and _QA.keyboardModifiers() & Qt.ShiftModifier:
            if k in self.multi:                           # gathered: lined up together later
                self.multi.remove(k)
            else:
                self.multi.append(k)
            return
        if self.ref is not None and k != self.ref:
            self.line_up(k)
            return
        self.save_undo()
        self.pick(k, p)

    # what's drawn and said
    def outline(self, k):
        o = self.r['openings'][k]
        pi, wi = int(o.get('part', 0)), int(o.get('wall', 0))
        a, u, n, _L = self.wall_frame(pi, wi)
        zr = ZREF.get(pi, 0.0)
        V = QVector3D

        def W(s, z):
            return V((a[0] + u[0] * s + n[0] * 3.0) * SCALE, (a[1] + u[1] * s + n[1] * 3.0) * SCALE, zr + z * SCALE)
        pts = [W(s, z) for s, z in o['shape']] if o.get('shape') else \
            [W(o['s0'], o['z0']), W(o['s1'], o['z0']), W(o['s1'], o['z1']), W(o['s0'], o['z1'])]
        return [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]

    def lines(self):
        out = []
        for k in {x for x in [self.hover, self.ref, self.carry[0] if self.carry else None] + list(self.multi)
                  if x is not None}:
            try:
                out += self.outline(k)
            except Exception:
                pass
        return out

    def status(self):
        names = opening_names(self.r)
        if self.carry is not None:
            lk = {'along': " Locked: along the wall only (arrow again to free it).",
                  'up': " Locked: up and down only (arrow again to free it)."}.get(self.lock, "")
            return ("Moving %s - click to put it down (it snaps to the others' edges). Arrow keys: Left/Right lock it "
                    "along the wall, Up locks it up and down, Down frees it.%s" % (names[self.carry[0]], lk))
        if self.ref is not None:
            if self.multi:
                return "<b>%d</b> picked. Shift + click more, then <b>Line these up</b>." % len(self.multi)
            return ("<b>%s</b> picked.<br>Click one to make it match, or <b>Shift + click</b> several." %
                    names[self.ref])
        return "Click a window (on its edge, so it goes red)."


class MovePanel(QDialog):
    """The one small window for editing windows and doors on the model: the picked one's size, lining others
    up to it, Undo, Finished."""

    def __init__(self, dlg):
        super().__init__(dlg.viewport if dlg.viewport is not None else None)
        self.dlg = dlg
        self.setWindowTitle("Windows")
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        lay = QVBoxLayout(self)
        lay.setSpacing(4)
        self.lbl = QLabel()
        self.lbl.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl)
        fsz = QFormLayout()
        self.sp_w = QDoubleSpinBox()
        self.sp_h = QDoubleSpinBox()
        for s_ in (self.sp_w, self.sp_h):
            s_.setRange(50.0, 20000.0)
            s_.setDecimals(0)
            s_.setSingleStep(10.0)
            s_.setSuffix(" mm")
            s_.setKeyboardTracking(False)
        fsz.addRow("Width", self.sp_w)
        fsz.addRow("Height", self.sp_h)
        lay.addLayout(fsz)
        for w_ in (self.sp_w, self.sp_h, fsz.labelForField(self.sp_w), fsz.labelForField(self.sp_h)):
            w_.setVisible(False)                          # stretched by eye on the model instead
        self._busy_sz = False
        self.sp_w.valueChanged.connect(lambda v: self._size(w=v))
        self.sp_h.valueChanged.connect(lambda v: self._size(h=v))
        self.cb_how = QComboBox()
        for key, txt in (('P', "Same size and place"), ('S', "Same size, tops level"), ('T', "Tops level"),
                         ('B', "Bottoms level"),
                         ('H', "Tops and bottoms level"), ('C', "Centred over / under")):
            self.cb_how.addItem(txt, key)
        self.cb_how.setCurrentIndex(max(0, self.cb_how.findData(dlg.mover.how)))
        self.cb_how.currentIndexChanged.connect(self.how)
        fl2 = QFormLayout()
        fl2.addRow("Match", self.cb_how)
        lay.addLayout(fl2)
        self.b_multi = QPushButton("Match these")
        self.b_multi.setStyleSheet("QPushButton { min-height: 28px; font-weight: bold; background: #7ad67a; }")
        lay.addWidget(self.b_multi)
        self.b_multi.clicked.connect(self.do_multi)
        self.b_wall = QPushButton("Match all on this wall")
        lay.addWidget(self.b_wall)
        self.b_wall.clicked.connect(lambda: self.all(False))
        self.b_let = QPushButton("Let go - pick another")
        lay.addWidget(self.b_let)
        self.b_let.clicked.connect(self.new)
        row = QHBoxLayout()
        self.b_undo = QPushButton("Undo")
        self.b_done = QPushButton("Finished")
        row.addWidget(self.b_undo)
        row.addWidget(self.b_done)
        lay.addLayout(row)
        self.b_undo.clicked.connect(self.undo)
        self.b_done.clicked.connect(dlg.stop_model_move)
        self.lbl_tip = QLabel("Edge: stretch it.  Middle: move it.\nShift + click others, then Match these.\n"
                              "Esc or Let go: pick another.")
        self.lbl_tip.setStyleSheet("color: #666;")
        lay.addWidget(self.lbl_tip)
        self.refresh()

    def _back(self):
        try:
            self.dlg.viewport.update()
            self.dlg.viewport.setFocus()
        except Exception:
            pass
        self.refresh()

    def _size(self, w=None, h=None):
        if self._busy_sz:
            return
        self.dlg.mover.resize_ref(w=w, h=h)
        self._back()

    def how(self, _i):
        self.dlg.mover.how = self.cb_how.currentData()
        self._back()

    def all(self, every):
        self.dlg.mover.line_up_all(every)
        self._back()

    def do_multi(self):
        self.dlg.mover.line_multi()
        self._back()

    def put_back(self):
        self.dlg.mover.cancel_carry()
        self.dlg.mover.hover = None
        self._back()

    def new(self):
        self.dlg.mover.cancel_carry()
        self.dlg.mover.ref = None
        self.dlg.mover.multi = []
        self.dlg.mover.hover = None
        self._back()

    def undo(self):
        self.dlg.mover.undo()
        self._back()

    def refresh(self):
        mv = self.dlg.mover
        cur = mv.carry[0] if mv.carry is not None else mv.ref
        names = opening_names(mv.r)
        if cur is None:
            self.lbl.setText("Click a window")
        elif mv.carry is not None:
            self.lbl.setText("%s - %s, click to let go" % (names[cur], "stretching" if mv.edge else "moving"))
        else:
            self.lbl.setText(names[cur])
        for w_ in (self.sp_w, self.sp_h):
            w_.setEnabled(cur is not None)
        if cur is not None:
            o = mv.r['openings'][cur]
            self._busy_sz = True
            self.sp_w.setValue(o['s1'] - o['s0'])
            self.sp_h.setValue(o['z1'] - o['z0'])
            self._busy_sz = False
        has = mv.ref is not None and mv.carry is None
        self.b_multi.setVisible(has and bool(mv.multi))
        self.b_multi.setText("Match these %d" % len(mv.multi))
        self.b_wall.setEnabled(has)
        self.b_let.setEnabled(cur is not None)
        self.b_undo.setEnabled(bool(mv.undos))
        self.adjustSize()


def make_move_tool(dlg):
    """The 'move on the model' tool (made here, so it gets no menu entry of its own)."""
    from PySide6.QtCore import Qt
    st = dlg.mover

    class _MoveTool(Tool):
        name = "Photo to Building - move windows"
        shortcut = None
        uses_snap = False                                 # snapping pulled clicks onto other windows
        wireframe_color = (0.85, 0.20, 0.15, 1.0)

        def on_activate(self, viewport):
            pass

        def on_deactivate(self, viewport):
            st.cancel_carry()
            st.ref = None
            st.hover = None
            dlg.model_move_gone(self)

        def on_hover(self, ctx):
            try:
                st.vp = ctx.viewport
                q = ctx.world
                p = (float(q.x()), float(q.y()), float(q.z()))
                if st.carry is not None:
                    st.follow(p)
                else:
                    st.look(p)
                ctx.viewport.update()
            except Exception:
                pass

        def on_click(self, ctx):
            try:
                if not getattr(st, '_probed', False):
                    st._probed = True
                    try:
                        vp_ = ctx.viewport
                        info = ["ctx: %s" % [a for a in dir(ctx) if not a.startswith('__')],
                                "viewport: %s" % [a for a in dir(vp_) if 'cam' in a.lower() or 'eye' in a.lower()
                                                  or 'ray' in a.lower() or 'view' in a.lower() or 'proj' in a.lower()]]
                        cam_ = getattr(vp_, 'camera', None)
                        if cam_ is not None:
                            info.append("camera: %s" % [a for a in dir(cam_) if not a.startswith('_')])
                        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               "photo_to_building_clicks.txt"), "a", encoding="utf-8") as fh:
                            fh.write("PROBE\n" + "\n".join(info) + "\n\n")
                    except Exception as e_:
                        print("%s: probe: %s" % (PLUGIN_NAME, e_))
                st.vp = ctx.viewport
                q = ctx.world
                st.click((float(q.x()), float(q.y()), float(q.z())))
                ctx.viewport.update()
                pnl = getattr(dlg, 'move_panel', None)
                if pnl is not None:
                    pnl.refresh()
            except Exception as e:
                dlg.say("Moving on the model: %s" % e, True)

        def on_key(self, viewport, key, modifiers):
            k = _key_int(key)
            if st.carry is not None:
                lk = {_key_int(Qt.Key_Left): 'along', _key_int(Qt.Key_Right): 'along', _key_int(Qt.Key_Up): 'up',
                      _key_int(Qt.Key_Down): 'free'}.get(k)
                if lk:
                    st.lock = None if lk == 'free' or st.lock == lk else lk
                    pnl = getattr(dlg, 'move_panel', None)
                    if pnl is not None:
                        pnl.refresh()
                    viewport.update()
                    return True
            if k == _key_int(Qt.Key_Escape):
                if not st.cancel_carry():
                    if st.ref is not None:
                        st.ref = None                     # let go of the picked one: pick another
                        st.multi = []
                        st.hover = None
                    else:
                        dlg.stop_model_move()
                if getattr(dlg, 'move_panel', None) is not None:
                    dlg.move_panel.refresh()
                viewport.update()
                return True
            return False

        def status_clause(self):
            return st.status()

        def rubber_band_lines(self):
            try:
                return st.lines()
            except Exception:
                return []
    return _MoveTool()


def _key_int(k):
    for get in (lambda: int(k), lambda: int(k.value)):
        try:
            return get()
        except Exception:
            pass
    return -1


class WallCanvas(QWidget):
    """One wall seen face-on from outside, with its windows and doors: drag one to move it, drag its edges or
    corners to resize it. Everything snaps to the grid."""

    EDGE = 7            # pixels from an edge that count as grabbing it

    def __init__(self, dlg):
        super().__init__(dlg)
        self.dlg = dlg
        self.setMinimumSize(640, 380)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.drag = None

    # wall mm <-> screen
    def _fit(self):
        L, H = self.dlg.cur_L, self.dlg.cur_H
        m = 30.0
        k = min((self.width() - 2 * m) / max(L, 1.0), (self.height() - 2 * m) / max(H, 1.0))
        ox = (self.width() - L * k) / 2.0
        oy = (self.height() + H * k) / 2.0
        return k, ox, oy

    def S(self, s, z):
        k, ox, oy = self._fit()
        return QPointF(ox + s * k, oy - z * k)

    def W(self, x, y):
        k, ox, oy = self._fit()
        return (x - ox) / k, (oy - y) / k

    def paintEvent(self, ev):
        from PySide6.QtGui import QPainter, QPen, QColor, QPolygonF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(246, 246, 244))
        L, H = self.dlg.cur_L, self.dlg.cur_H
        g = self.dlg.grid()
        p.setPen(QPen(QColor(120, 90, 80), 1.2))
        p.setBrush(QColor(214, 190, 170))
        p.drawRect(QRectF(self.S(0, H), self.S(L, 0)))
        if g > 0 and L / g < 400 and H / g < 400:
            p.setPen(QPen(QColor(190, 165, 148), 0.6))
            s = g
            while s < L:
                p.drawLine(self.S(s, 0), self.S(s, H))
                s += g
            z = g
            while z < H:
                p.drawLine(self.S(0, z), self.S(L, z))
                z += g
        for idx in self.dlg.on_wall():
            o = self.dlg.ops[idx]
            sel = idx == self.dlg.sel
            mul = idx in self.dlg.multi
            p.setPen(QPen(QColor(200, 30, 30) if sel else QColor(0, 150, 220) if mul else QColor(40, 40, 50),
                          3.5 if mul else 2.2 if sel else 1.2))
            p.setBrush(QColor(60, 70, 90) if o.get('kind') == 'door' else QColor(170, 205, 235))
            if o.get('shape'):
                p.drawPolygon(QPolygonF([self.S(s_, z_) for s_, z_ in o['shape']]))
            else:
                p.drawRect(QRectF(self.S(o['s0'], o['z1']), self.S(o['s1'], o['z0'])))
            p.setPen(QColor(200, 30, 30) if sel else QColor(30, 30, 30))
            c = self.S((o['s0'] + o['s1']) / 2.0, o['z1'])
            p.drawText(QRectF(c.x() - 60, c.y() - 18, 120, 16), Qt.AlignCenter, self.dlg.names[idx])
        p.setPen(QColor(90, 90, 90))
        p.drawText(QRectF(4, self.height() - 20, self.width() - 8, 18), Qt.AlignLeft,
                   "Seen from outside.  Wall %.0f mm long, %.0f mm to the eaves." % (L, H))
        p.end()

    def _grab(self, pos):
        """(index, what) under the mouse: what is 'move' or a mix of l, r, t, b (edges)."""
        best = None
        for idx in reversed(self.dlg.on_wall()):
            o = self.dlg.ops[idx]
            a, b = self.S(o['s0'], o['z1']), self.S(o['s1'], o['z0'])
            x, y, e = pos.x(), pos.y(), self.EDGE
            if not (a.x() - e <= x <= b.x() + e and a.y() - e <= y <= b.y() + e):
                continue
            w = ""
            if abs(x - a.x()) <= e:
                w += "l"
            elif abs(x - b.x()) <= e:
                w += "r"
            if abs(y - a.y()) <= e:
                w += "t"
            elif abs(y - b.y()) <= e:
                w += "b"
            best = (idx, w or "move")
            break
        return best

    def mousePressEvent(self, ev):
        pos = ev.position() if hasattr(ev, 'position') else ev.pos()
        if ev.button() != Qt.LeftButton:
            return
        hit = self._grab(pos)
        if hit is None:
            if not ev.modifiers() & Qt.ShiftModifier:
                self.dlg.multi = []
                self.dlg.select(None)
            return
        idx, what = hit
        if ev.modifiers() & Qt.ShiftModifier and self.dlg.sel is not None:
            if idx != self.dlg.sel:                       # one more to make like the first
                if idx in self.dlg.multi:
                    self.dlg.multi.remove(idx)
                else:
                    self.dlg.multi.append(idx)
                self.dlg.show_multi()
                self.update()
            return
        if idx != self.dlg.sel:
            self.dlg.multi = []
        self.dlg.select(idx)
        self.dlg.show_multi()
        self.dlg.push_undo()
        self.drag = (idx, what, self.W(pos.x(), pos.y()), copy.deepcopy(self.dlg.ops[idx]))

    def mouseMoveEvent(self, ev):
        pos = ev.position() if hasattr(ev, 'position') else ev.pos()
        if self.drag is None:
            hit = self._grab(pos)
            cur = Qt.ArrowCursor
            if hit:
                w = hit[1]
                cur = (Qt.SizeAllCursor if w == "move" else Qt.SizeFDiagCursor if w in ("lt", "rb")
                       else Qt.SizeBDiagCursor if w in ("rt", "lb") else Qt.SizeHorCursor if w in ("l", "r")
                       else Qt.SizeVerCursor)
            self.setCursor(cur)
            return
        idx, what, start, o0 = self.drag
        s, z = self.W(pos.x(), pos.y())
        ds, dz = s - start[0], z - start[1]
        self.dlg.apply_drag(idx, what, o0, ds, dz, bool(ev.modifiers() & Qt.ControlModifier))
        self.update()

    def mouseReleaseEvent(self, ev):
        if self.drag is not None:
            self.drag = None
            self.dlg.changed_one()

    def keyPressEvent(self, ev):
        k = ev.key()
        step = self.dlg.grid() or 10.0
        d = {Qt.Key_Left: (-step, 0), Qt.Key_Right: (step, 0), Qt.Key_Up: (0, step), Qt.Key_Down: (0, -step)}.get(k)
        if d and self.dlg.sel is not None:
            self.dlg.push_undo()
            self.dlg.shift(self.dlg.sel, d[0], d[1])
            self.dlg.changed_one()
            return
        super().keyPressEvent(ev)


class MoveOpeningsDialog(QDialog):
    """Put the windows and doors right after the building's built: pick a wall, drag them about, Apply."""

    def __init__(self, r, parent=None, live=None):
        super().__init__(parent)
        self.live = live
        self.moved_live = False
        self.setWindowTitle("Move windows and doors - %s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(True)
        self.r = copy.deepcopy(r)
        self.ops = self.r.setdefault('openings', [])
        self.names = opening_names(self.r)
        for o in self.ops:                                # a traced one: its box is round its outline
            if o.get('shape'):
                o['s0'], o['s1'] = min(q[0] for q in o['shape']), max(q[0] for q in o['shape'])
                o['z0'], o['z1'] = min(q[1] for q in o['shape']), max(q[1] for q in o['shape'])
        self.sel = None
        self.multi = []                                   # Shift + clicked: made like the picked one
        self.undos = []
        self.walls = wall_list(self.r)
        self.cur = (0, 0)
        self.cur_L, self.cur_H = 1000.0, 1000.0
        self.resize(760, 470)
        try:                                              # at the right of the screen, the building beside it
            from PySide6.QtGui import QGuiApplication as _QGA
            sg_ = _QGA.primaryScreen().availableGeometry()
            self.move(sg_.right() - 780, sg_.top() + 60)
        except Exception:
            pass
        lay = QHBoxLayout(self)
        left = QVBoxLayout()
        left.addWidget(_note("<b>Drag</b> a window or door to move it, drag its <b>edges or corners</b> to resize it. "
                             "It snaps to the grid (hold Ctrl not to). Arrow keys nudge the picked one."))
        self.canvas = WallCanvas(self)
        left.addWidget(self.canvas, 1)
        lay.addLayout(left, 3)

        side = QVBoxLayout()
        side.addWidget(QLabel("<b>1  Pick the wall</b>"))
        self.cb_wall = QComboBox()
        for pi, wi, nm, L, H in self.walls:
            self.cb_wall.addItem(nm, (pi, wi))
        side.addWidget(self.cb_wall)
        b_prev, b_next = QPushButton("◀ Wall"), QPushButton("Wall ▶")
        row = QHBoxLayout()
        row.addWidget(b_prev)
        row.addWidget(b_next)
        side.addLayout(row)
        side.addWidget(QLabel("<b>2  Move them</b>"))
        self.cb_live = QCheckBox("Show it on the model as I go")
        self.cb_live.setToolTip("Each time you let go, the walls in the model are cut again so you can see it there "
                                "(Cancel puts them back).")
        self.cb_live.setChecked(live is not None and bool(load_settings().get('move_live', True)))
        self.cb_live.setEnabled(live is not None)
        self.cb_live.toggled.connect(lambda on: (save_settings(move_live=bool(on)), self.changed_one()))
        side.addWidget(self.cb_live)
        fl = QFormLayout()
        self.sp_grid = QDoubleSpinBox()
        self.sp_grid.setRange(0.0, 1000.0)
        self.sp_grid.setDecimals(0)
        self.sp_grid.setSingleStep(10.0)
        self.sp_grid.setSuffix(" mm")
        self.sp_grid.setValue(float(load_settings().get('move_grid', 50.0)))
        fl.addRow("Grid", self.sp_grid)
        self.lbl_sel = QLabel("Nothing picked")
        fl.addRow(self.lbl_sel)
        self.sp = {}
        for key, label in (('s0', "From the left"), ('z0', "Bottom up"), ('w', "Width"), ('h', "Height")):
            s = QDoubleSpinBox()
            s.setRange(-100000.0, 100000.0)
            s.setDecimals(0)
            s.setSingleStep(10.0)
            s.setSuffix(" mm")
            s.setKeyboardTracking(False)
            fl.addRow(label, s)
            self.sp[key] = s
            s.valueChanged.connect(lambda v, k=key: self.typed(k, v))
        side.addLayout(fl)
        self.lbl_multi = QLabel()
        self.lbl_multi.setWordWrap(True)
        side.addWidget(self.lbl_multi)
        self.b_like = QPushButton("Make these like the first one...")
        self.b_like.setStyleSheet("QPushButton { min-height: 32px; font-weight: bold; background: #7ad67a; }")
        side.addWidget(self.b_like)
        self.b_like.clicked.connect(self.make_like)
        self.b_tops = QPushButton("Line up the tops on its floor")
        self.b_tops.setToolTip("The other windows on the same floor of this wall get their tops at the same height "
                               "as the picked one (doors stay on the floor).")
        self.b_bots = QPushButton("Line up the bottoms on its floor")
        self.b_size = QPushButton("Make the others on its floor its size")
        self.b_space = QPushButton("Space its floor's evenly along the wall")
        self.b_undo = QPushButton("Undo")
        for b_ in (self.b_tops, self.b_bots, self.b_size, self.b_space, self.b_undo):
            side.addWidget(b_)
        side.addStretch(1)
        side.addWidget(QLabel("<b>3  Apply</b>"))
        side.addWidget(_note("Cuts the walls again with the holes in their new places (the new places are saved "
                             "with the job, so building again keeps them).", True))
        b_ok, b_no = QPushButton("Apply"), QPushButton("Cancel")
        b_ok.setMinimumHeight(32)
        row = QHBoxLayout()
        row.addWidget(b_ok)
        row.addWidget(b_no)
        side.addLayout(row)
        lay.addLayout(side, 1)

        self._busy = False
        self.cb_wall.currentIndexChanged.connect(self.pick_wall)
        b_prev.clicked.connect(lambda: self.cb_wall.setCurrentIndex(max(0, self.cb_wall.currentIndex() - 1)))
        b_next.clicked.connect(lambda: self.cb_wall.setCurrentIndex(min(self.cb_wall.count() - 1,
                                                                       self.cb_wall.currentIndex() + 1)))
        self.sp_grid.valueChanged.connect(lambda v: (save_settings(move_grid=float(v)), self.canvas.update()))
        self.b_tops.clicked.connect(lambda: self.line_up('top'))
        self.b_bots.clicked.connect(lambda: self.line_up('bottom'))
        self.b_size.clicked.connect(lambda: self.line_up('size'))
        self.b_space.clicked.connect(self.space_out)
        self.b_undo.clicked.connect(self.undo)
        b_ok.clicked.connect(self.accept)
        b_no.clicked.connect(self.reject)
        first = next((k for k, w in enumerate(self.walls) if any(int(o.get('part', 0)) == w[0] and
                                                                 int(o.get('wall', 0)) == w[1] for o in self.ops)), 0)
        self.cb_wall.setCurrentIndex(first)
        self.pick_wall(first)
        self.show_multi()

    # ------------------------------------------------------------------ the wall and what's on it
    def grid(self):
        return float(self.sp_grid.value())

    def on_wall(self):
        return [i for i, o in enumerate(self.ops)
                if int(o.get('part', 0)) == self.cur[0] and int(o.get('wall', 0)) == self.cur[1]]

    def pick_wall(self, k):
        if not 0 <= k < len(self.walls):
            return
        pi, wi, _nm, L, H = self.walls[k]
        self.cur, self.cur_L, self.cur_H = (pi, wi), L, H
        self.multi = []
        on = self.on_wall()
        self.select(on[0] if on else None)
        if hasattr(self, 'lbl_multi'):
            self.show_multi()
        self.canvas.update()

    def select(self, idx):
        self.sel = idx
        self._busy = True
        try:
            on = idx is not None
            for s in self.sp.values():
                s.setEnabled(on)
            for b_ in (self.b_tops, self.b_bots, self.b_size, self.b_space):
                b_.setEnabled(on)
            if on:
                o = self.ops[idx]
                self.lbl_sel.setText("<b>%s</b>" % self.names[idx])
                self.sp['s0'].setValue(o['s0'])
                self.sp['z0'].setValue(o['z0'])
                self.sp['w'].setValue(o['s1'] - o['s0'])
                self.sp['h'].setValue(o['z1'] - o['z0'])
            else:
                self.lbl_sel.setText("Nothing picked - click a window or door")
        finally:
            self._busy = False
        self.canvas.update()

    def changed_one(self):
        self.select(self.sel)
        if self.live is not None and self.cb_live.isChecked():
            try:
                self.live(self.r)
                self.moved_live = True
            except Exception as e:
                print("%s: showing it on the model: %s" % (PLUGIN_NAME, e))

    def push_undo(self):
        self.undos.append(copy.deepcopy(self.ops))
        del self.undos[:-50]

    def undo(self):
        if not self.undos:
            return
        self.ops[:] = self.undos.pop()
        if self.sel is not None and self.sel >= len(self.ops):
            self.sel = None
        self.changed_one()

    # ------------------------------------------------------------------ changing them
    def _snap(self, v, free=False):
        g = self.grid()
        return v if free or g <= 0 else round(v / g) * g

    def _set_box(self, o, s0, s1, z0, z1):
        """New box for an opening: a traced outline is stretched to fit it."""
        op_set_box(o, s0, s1, z0, z1)
        return
        s0, s1 = sorted((s0, s1))
        z0, z1 = sorted((z0, z1))
        if s1 - s0 < 50.0 or z1 - z0 < 50.0:
            return
        if o.get('shape'):
            os0, os1, oz0, oz1 = o['s0'], o['s1'], o['z0'], o['z1']
            fx = (s1 - s0) / max(os1 - os0, 1e-6)
            fz = (z1 - z0) / max(oz1 - oz0, 1e-6)
            o['shape'] = [[round(s0 + (a - os0) * fx, 1), round(z0 + (b - oz0) * fz, 1)] for a, b in o['shape']]
        o['s0'], o['s1'], o['z0'], o['z1'] = round(s0, 1), round(s1, 1), round(z0, 1), round(z1, 1)

    def apply_drag(self, idx, what, o0, ds, dz, free):
        o = self.ops[idx]
        o.clear()
        o.update(copy.deepcopy(o0))
        s0, s1, z0, z1 = o0['s0'], o0['s1'], o0['z0'], o0['z1']
        if what == "move":
            ns0 = self._snap(s0 + ds, free)
            nz0 = self._snap(z0 + dz, free)
            self._set_box(o, ns0, ns0 + (s1 - s0), nz0, nz0 + (z1 - z0))
            return
        if "l" in what:
            s0 = self._snap(s0 + ds, free)
        if "r" in what:
            s1 = self._snap(s1 + ds, free)
        if "t" in what:
            z1 = self._snap(z1 + dz, free)
        if "b" in what:
            z0 = self._snap(z0 + dz, free)
        self._set_box(o, s0, s1, z0, z1)

    def shift(self, idx, ds, dz):
        o = self.ops[idx]
        self._set_box(o, o['s0'] + ds, o['s1'] + ds, o['z0'] + dz, o['z1'] + dz)

    def typed(self, key, v):
        if self._busy or self.sel is None:
            return
        self.push_undo()
        o = self.ops[self.sel]
        w, h = o['s1'] - o['s0'], o['z1'] - o['z0']
        s0, z0 = o['s0'], o['z0']
        if key == 's0':
            s0 = v
        elif key == 'z0':
            z0 = v
        elif key == 'w':
            w = v
        else:
            h = v
        self._set_box(o, s0, s0 + w, z0, z0 + h)
        self.changed_one()

    def line_up(self, how):
        if self.sel is None:
            return
        self.push_undo()
        ref = self.ops[self.sel]
        for i in self.same_floor():
            if i == self.sel:
                continue
            o = self.ops[i]
            if o.get('kind') == 'door' and how != 'size':
                continue
            if how == 'top':
                self._set_box(o, o['s0'], o['s1'], ref['z1'] - (o['z1'] - o['z0']), ref['z1'])
            elif how == 'bottom':
                self._set_box(o, o['s0'], o['s1'], ref['z0'], ref['z0'] + (o['z1'] - o['z0']))
            elif o.get('kind') == ref.get('kind'):
                m = (o['s0'] + o['s1']) / 2.0
                w = ref['s1'] - ref['s0']
                self._set_box(o, m - w / 2.0, m + w / 2.0, ref['z0'], ref['z1'])
        self.changed_one()

    def show_multi(self):
        n = len(self.multi)
        if self.sel is None:
            txt = "<b>To make windows the same:</b> click the good one (size it to fit), then <b>Shift + click</b> " \
                  "the others."
        elif n == 0:
            txt = "<b>%s</b> picked. <b>Shift + click</b> the windows to make like it." % self.names[self.sel]
        else:
            txt = "<b>%d</b> to make like <b>%s</b> (blue). Shift + click more, or press the green button." % (
                n, self.names[self.sel])
        self.lbl_multi.setText(txt)
        self.b_like.setVisible(self.sel is not None and n > 0)

    def make_like(self):
        """The pop-up: make the Shift + clicked ones like the first one picked."""
        from PySide6.QtWidgets import QDialogButtonBox
        if self.sel is None or not self.multi:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Make these like %s" % self.names[self.sel])
        vl = QVBoxLayout(dlg)
        vl.addWidget(QLabel("<b>Make %d window%s like %s:</b>" % (len(self.multi), "" if len(self.multi) == 1 else "s",
                                                                  self.names[self.sel])))
        ck_size = QCheckBox("The same size")
        ck_top = QCheckBox("Tops level with it")
        ck_bot = QCheckBox("Bottoms level with it")
        ck_even = QCheckBox("Evenly spaced (the two end ones stay put)")
        ck_size.setChecked(True)
        ck_top.setChecked(True)
        for c_ in (ck_size, ck_top, ck_bot, ck_even):
            c_.setStyleSheet("font-size: 10.5pt; padding: 3px;")
            vl.addWidget(c_)
        ck_top.toggled.connect(lambda on: on and ck_bot.setChecked(False))
        ck_bot.toggled.connect(lambda on: on and ck_top.setChecked(False))
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("Make them like it")
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        vl.addWidget(bb)
        if dlg.exec() != QDialog.Accepted:
            return
        self.push_undo()
        ref = self.ops[self.sel]
        rw, rh = ref['s1'] - ref['s0'], ref['z1'] - ref['z0']
        group = [self.sel] + [i for i in self.multi if i != self.sel and
                              (self.ops[i].get('kind') != 'door' or ref.get('kind') == 'door')]
        for i in group[1:]:
            o = self.ops[i]
            m = (o['s0'] + o['s1']) / 2.0
            w, h = (rw, rh) if ck_size.isChecked() else (o['s1'] - o['s0'], o['z1'] - o['z0'])
            if ck_top.isChecked():
                z1 = ref['z1']
                z0 = z1 - h
            elif ck_bot.isChecked():
                z0 = ref['z0']
                z1 = z0 + h
            else:
                z1 = o['z1']
                z0 = z1 - h
            if ck_size.isChecked() and ref.get('shape') and o.get('kind') == ref.get('kind'):
                # an odd shape: the same shape, put where this one is
                o['shape'] = [[round(m - rw / 2.0 + (q[0] - ref['s0']), 1), round(z0 + (q[1] - ref['z0']), 1)]
                              for q in ref['shape']]
                o['top'] = ref.get('top', o.get('top'))
                o['s0'], o['s1'] = round(m - rw / 2.0, 1), round(m + rw / 2.0, 1)
                o['z0'], o['z1'] = round(z0, 1), round(z1, 1)
            else:
                self._set_box(o, m - w / 2.0, m + w / 2.0, z0, z1)
        if ck_even.isChecked() and len(group) >= 3:
            order = sorted(group, key=lambda i: self.ops[i]['s0'] + self.ops[i]['s1'])
            c0 = (self.ops[order[0]]['s0'] + self.ops[order[0]]['s1']) / 2.0
            c1 = (self.ops[order[-1]]['s0'] + self.ops[order[-1]]['s1']) / 2.0
            for k, i in enumerate(order):
                o = self.ops[i]
                cx = c0 + (c1 - c0) * k / float(len(order) - 1)
                d = cx - (o['s0'] + o['s1']) / 2.0
                if abs(d) > 1e-6:
                    self.shift(i, d, 0.0)
        self.changed_one()
        self.canvas.update()

    def same_floor(self):
        """The windows and doors on this wall at the same level as the picked one (overlapping it in height)."""
        if self.sel is None:
            return self.on_wall()
        ref = self.ops[self.sel]
        lo, hi = ref['z0'], ref['z1']
        return [i for i in self.on_wall()
                if min(hi, self.ops[i]['z1']) - max(lo, self.ops[i]['z0']) > 0.3 * min(hi - lo, self.ops[i]['z1'] -
                                                                                     self.ops[i]['z0'])]

    def space_out(self):
        on = sorted(self.same_floor(), key=lambda i: self.ops[i]['s0'])
        if not on:
            return
        self.push_undo()
        total = sum(self.ops[i]['s1'] - self.ops[i]['s0'] for i in on)
        gap = (self.cur_L - total) / (len(on) + 1)
        if gap <= 0:
            return
        s = gap
        for i in on:
            o = self.ops[i]
            w = o['s1'] - o['s0']
            self._set_box(o, s, s + w, o['z0'], o['z1'])
            s += w + gap
        self.changed_one()


class PlanEditor(QDialog):
    """A window of its own to put the plan right: move and resize the parts with the mouse, and copy a
    part to the other end of the building."""

    def __init__(self, r, photo_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change the plan - %s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(True)
        self.r = copy.deepcopy(r)
        self.photo_path = photo_path
        self.sel = 1 if len(self.r['parts']) > 1 else 0
        self.undos = []
        self._quiet = False
        self.resize(1100, 720)

        lay = QHBoxLayout(self)
        left = QVBoxLayout()
        left.addWidget(_note("<b>Like resizing a window:</b> drag a part to move it, drag its edges or corners to "
                             "make it bigger or smaller. It lines up with the other walls as you get near them "
                             "(hold Ctrl not to). Wheel: zoom. Right-drag: slide the view."))
        self.canvas = PlanCanvas(self)
        left.addWidget(self.canvas, 1)
        lay.addLayout(left, 3)

        side = QVBoxLayout()
        side.addWidget(QLabel("<b>Parts</b>"))
        self.lst = QListWidget()
        self.lst.setMaximumHeight(170)
        side.addWidget(self.lst)
        fl = QFormLayout()
        self.sp_len = QDoubleSpinBox()
        self.sp_dep = QDoubleSpinBox()
        for s in (self.sp_len, self.sp_dep):
            s.setRange(MIN_SIDE, 200000.0)
            s.setDecimals(0)
            s.setSingleStep(ROUND_TO)
            s.setSuffix(" mm")
            s.setKeyboardTracking(False)
        fl.addRow("Along wall 1", self.sp_len)
        fl.addRow("Back from it", self.sp_dep)
        side.addLayout(fl)
        side.addWidget(_note("Typed sizes keep the side nearest the main building where it is.", True))
        self.b_mirror = QPushButton("Copy to the other end (replaces what's there)")
        self.b_mirror.setMinimumHeight(32)
        self.b_mirror.setToolTip("A mirror copy of the part picked, the same distance the other side of the "
                                 "middle of the main building - windows and doors too. Then drag it to fit.")
        self.b_off = QPushButton("Take this part off")
        self.b_undo = QPushButton("Undo")
        self.b_fit = QPushButton("Fit in the window")
        self.b_reset = QPushButton("Back to the photo's plan")
        self.b_reset.setToolTip("Throws away the changes made here - the plan as it came from the 3D program.")
        for b_ in (self.b_mirror, self.b_off, self.b_undo, self.b_fit, self.b_reset):
            side.addWidget(b_)
        self.lbl = _note("", True)
        side.addWidget(self.lbl)
        side.addStretch(1)
        row = QHBoxLayout()
        b_ok = QPushButton("Use this plan")
        b_ok.setDefault(True)
        b_ok.setMinimumHeight(32)
        b_cancel = QPushButton("Cancel")
        row.addWidget(b_ok)
        row.addWidget(b_cancel)
        side.addLayout(row)
        lay.addLayout(side, 1)

        self.lst.currentRowChanged.connect(lambda i: self.select(i if i >= 0 else None, from_list=True))
        self.sp_len.valueChanged.connect(lambda _v: self.typed())
        self.sp_dep.valueChanged.connect(lambda _v: self.typed())
        self.b_mirror.clicked.connect(self.mirror)
        self.b_off.clicked.connect(self.take_off)
        self.b_undo.clicked.connect(self.undo)
        self.b_fit.clicked.connect(self.canvas.fit)
        self.b_reset.clicked.connect(self.reset)
        b_ok.clicked.connect(self.accept)
        b_cancel.clicked.connect(self.reject)
        self.fill_list()
        self.select(self.sel)
        try:
            eddy_place(self, PLUGIN_NAME + " - plan")
        except Exception:
            pass

    # ---- keeping the side panel up to date ----
    def fill_list(self):
        self._quiet = True
        self.lst.clear()
        for k, pt in enumerate(self.r['parts']):
            self.lst.addItem(pt.get('name') or ("Main building" if k == 0 else "Part %d" % (k + 1)))
        if self.sel is not None:
            self.lst.setCurrentRow(self.sel)
        self._quiet = False

    def select(self, pi, from_list=False):
        if self._quiet and from_list:
            return
        if pi is not None and not 0 <= pi < len(self.r['parts']):
            pi = None
        self.sel = pi
        if not from_list:
            self._quiet = True
            self.lst.setCurrentRow(-1 if pi is None else pi)
            self._quiet = False
        self.show_sizes()
        self.b_mirror.setEnabled(bool(pi))
        self.b_off.setEnabled(bool(pi))
        self.b_undo.setEnabled(bool(self.undos))
        self.canvas.update()

    def show_sizes(self):
        self._quiet = True
        pi = self.sel
        on = pi is not None
        for s in (self.sp_len, self.sp_dep):
            s.setEnabled(on)
        if on:
            cs = self.r['parts'][pi]['corners']
            u0, u1, v0, v1 = _box(_frame(cs), cs)
            self.sp_len.setValue(u1 - u0)
            self.sp_dep.setValue(v1 - v0)
        self._quiet = False

    def changed_live(self):
        self.show_sizes()

    def changed_done(self):
        self.show_sizes()
        self.b_undo.setEnabled(True)
        self.say("")

    def say(self, text):
        self.lbl.setText(text)

    def push_undo(self, state):
        self.undos.append(state)
        del self.undos[:-50]
        self.b_undo.setEnabled(True)

    # ---- the buttons ----
    def typed(self):
        if self._quiet or self.sel is None:
            return
        pi = self.sel
        cs = self.r['parts'][pi]['corners']
        fr = _frame(cs)
        u0, u1, v0, v1 = _box(fr, cs)
        L, D = self.sp_len.value(), self.sp_dep.value()
        if abs(L - (u1 - u0)) < 0.5 and abs(D - (v1 - v0)) < 0.5:
            return
        # keep the side nearest the main building where it is
        if pi:
            mc = self.r['parts'][0]['corners']
            cu, cv = _to_fr(fr, (sum(c[0] for c in mc) / len(mc), sum(c[1] for c in mc) / len(mc)))
        else:
            cu, cv = u0, v0
        nu0, nu1 = (u1 - L, u1) if cu > (u0 + u1) / 2.0 else (u0, u0 + L)
        nv0, nv1 = (v1 - D, v1) if cv > (v0 + v1) / 2.0 else (v0, v0 + D)
        start = copy.deepcopy(self.r)
        self.r = resized(start, pi, fr, (u0, u1, v0, v1), (nu0, nu1, nv0, nv1))
        self.push_undo(start)
        self.canvas.update()

    def nudge(self, dx, dy):
        pi = self.sel
        if not pi:
            return
        self.push_undo(copy.deepcopy(self.r))
        pt = self.r['parts'][pi]
        pt['corners'] = [[c[0] + dx, c[1] + dy] for c in pt['corners']]
        tidy_part(self.r, pi)
        self.changed_done()
        self.canvas.update()

    def mirror(self):
        pi = self.sel
        if not pi:
            return
        self.push_undo(copy.deepcopy(self.r))
        ni = mirror_part(self.r, pi)
        self.fill_list()
        self.select(ni)
        self.say("%s made on the other end (in place of what was there) - drag it to fit if the building isn't "
                 "the same both ends." % self.r['parts'][ni]['name'])

    def take_off(self):
        pi = self.sel
        if not pi:
            return
        name = self.r['parts'][pi].get('name', 'this part')
        if QMessageBox.question(self, PLUGIN_NAME, "Take %s off (with its windows and doors)?" % name) != \
                QMessageBox.StandardButton.Yes:
            return
        self.push_undo(copy.deepcopy(self.r))
        remove_part(self.r, pi)
        self.sel = None
        self.fill_list()
        self.select(None)
        self.say("%s taken off (Undo puts it back)." % name)

    def undo(self):
        if not self.undos:
            return
        self.r = self.undos.pop()
        n = len(self.r['parts'])
        if self.sel is not None and self.sel >= n:
            self.sel = n - 1
        self.fill_list()
        self.select(self.sel)

    def reset(self):
        if not self.photo_path or not os.path.isfile(self.photo_path):
            self.say("The plan from the 3D program isn't there any more.")
            return
        try:
            r = read_result(self.photo_path)
        except Exception as e:
            self.say("Couldn't read it: %s" % e)
            return
        self.push_undo(copy.deepcopy(self.r))
        self.r = r
        self.sel = 1 if len(r['parts']) > 1 else 0
        self.fill_list()
        self.select(self.sel)
        self.canvas.fit()
        self.say("Back to the plan as it came from the photo (Undo to get your changes back).")


# ---------------------------------------------------------------------------
# How to click: a little drawing for each step, the dot to click next lit up (version 4.5)
# ---------------------------------------------------------------------------
DG_COL = {'wall': (215, 215, 215), 'faint': (120, 120, 120), 'cyan': (77, 230, 255), 'green': (80, 230, 120),
          'pink': (255, 115, 230), 'red': (255, 70, 60), 'lime': (80, 255, 90), 'yellow': (255, 217, 26),
          'blue': (77, 170, 255), 'orange': (255, 140, 38), 'white': (255, 255, 255)}


class StepDiagram(QWidget):
    """Draws the window's diagram(): ('line', [(x, y)...], colour, width[, dashed]) / ('dot', (x, y), label,
    colour, next) / ('text', (x, y), words, colour) - in a 100 x 70 box, up from the bottom."""

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setMinimumHeight(170)
        self.setMaximumHeight(210)

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QFont
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(24, 26, 32))
        p.setPen(QColor(150, 200, 255))
        p.drawText(QRectF(8, 3, self.width() - 16, 16), Qt.AlignLeft, "How to click")
        try:
            items = self.win.diagram() or []
        except Exception as e:
            items = [('text', (5, 35), "(%s)" % e, 'faint')]
        x0, y0, x1, y1 = 10.0, 22.0, self.width() - 10.0, self.height() - 8.0
        sc = min((x1 - x0) / 100.0, (y1 - y0) / 70.0)
        ox = (x0 + x1) / 2.0 - 50.0 * sc
        oy = (y0 + y1) / 2.0 + 35.0 * sc

        def P(q):
            return QPointF(ox + q[0] * sc, oy - q[1] * sc)

        def col(c, a=255):
            r, g, b = DG_COL.get(c, DG_COL['wall'])
            return QColor(r, g, b, a)
        f = QFont(p.font())
        f.setBold(True)
        for it in items:
            if it[0] == 'line':
                pts, c, w = it[1], it[2], it[3]
                pen = QPen(col(c), w)
                if len(it) > 4 and it[4]:
                    pen.setStyle(Qt.DashLine)
                p.setPen(pen)
                for a, b in zip(pts, pts[1:]):
                    p.drawLine(P(a), P(b))
        for it in items:
            if it[0] == 'text':
                p.setFont(f)
                p.setPen(col(it[3]))
                q = P(it[1])
                p.drawText(QRectF(q.x(), q.y() - 9, self.width(), 18), Qt.AlignLeft | Qt.AlignVCenter, it[2])
        for it in items:
            if it[0] == 'dot':
                q, lab, c, nxt = P(it[1]), it[2], it[3], it[4]
                if nxt:                                    # the one to click next
                    p.setPen(QPen(col('white'), 2))
                    p.setBrush(Qt.NoBrush)
                    p.drawEllipse(q, 10, 10)
                p.setPen(Qt.NoPen)
                p.setBrush(col(c, 255 if nxt else 170))
                p.drawEllipse(q, 6 if nxt else 4.5, 6 if nxt else 4.5)
                p.setBrush(Qt.NoBrush)
                if lab:
                    p.setFont(f)
                    p.setPen(col('white') if nxt else col(c))
                    p.drawText(QPointF(q.x() + 9, q.y() - 6), lab)
        p.end()


def _house_front(roof=True, door=True, faint=False):
    """A plain house front for the diagrams: wall 15..85 x 5..40."""
    c = 'faint' if faint else 'wall'
    out = [('line', [(15, 5), (85, 5), (85, 40), (15, 40), (15, 5)], c, 2)]
    if roof:
        out.append(('line', [(10, 40), (22, 56), (78, 56), (90, 40)], 'faint', 1.5))
    if door:
        out.append(('line', [(45, 5), (45, 22), (55, 22), (55, 5)], 'faint', 1.5))
    out.append(('line', [(22, 18), (22, 30), (32, 30), (32, 18), (22, 18)], 'faint', 1.2))
    out.append(('line', [(68, 18), (68, 30), (78, 30), (78, 18), (68, 18)], 'faint', 1.2))
    return out


# the corner view: front wall A..B (left), side wall B..C (right); ' is the top (eaves)
_A, _B, _C = (8, 14), (55, 4), (92, 16)
_At, _Bt, _Ct = (8, 42), (55, 48), (92, 40)


def _corner_clicks(n, peak=False):
    """The corner photo's 6 corners as a picture: 3 corners, each low then at the roof edge (next one lit)."""
    out = _corner_house()
    lo = [(_A[0], _A[1] + 8), (_B[0], _B[1] + 8), (_C[0], _C[1] + 8)]
    out.append(('line', [lo[0], lo[1]], 'pink', 2))
    out.append(('line', [_At, _Bt], 'pink', 2))
    out.append(('line', [lo[1], lo[2]], 'green', 2))
    out.append(('line', [_Bt, _Ct], 'green', 2))
    pts = [(lo[0], "1"), (_At, "2"), (lo[1], "3"), (_Bt, "4"), (lo[2], "5"), (_Ct, "6")]
    for i, (pt, lab) in enumerate(pts):
        out.append(('dot', pt, lab, 'yellow', i == n))
    if peak:
        apex = ((_Bt[0] + _Ct[0]) / 2.0, 64)
        out.append(('line', [_Bt, apex, _Ct], 'pink', 2.5))
        out.append(('dot', apex, "7 peak", 'pink', n >= 6))
        out.append(('text', (2, 66), "front left, the corner, the back - low, then top", 'yellow'))
    else:
        out.append(('text', (2, 66), "front left, the corner, the back - low, then top", 'yellow'))
    return out


def _corner_house():
    return [('line', [_A, _B, _C], 'wall', 2), ('line', [_At, _Bt, _Ct], 'wall', 2),
            ('line', [_A, _At], 'wall', 2), ('line', [_B, _Bt], 'wall', 2), ('line', [_C, _Ct], 'wall', 2),
            ('line', [_At, (24, 60), (72, 63), _Ct], 'faint', 1.5),
            ('line', [(24, 60), _Bt], 'faint', 1)]


def _mid(a, b, t=0.5):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# ---------------------------------------------------------------------------
# Clicking round the building here in IngeTrazo - no 3D program needed (version 3.0)
# The measuring is the same as the 3D program's side: it's run here from the same script.
# ---------------------------------------------------------------------------
CLICKS_NAME = "clicks.json"
_MATHS = None


def maths():
    """The photo measuring (lining up, corners, heights, windows...) - the 3D program's side of this plugin,
    loaded here without the 3D program (it only does the maths when it isn't in one)."""
    global _MATHS
    if _MATHS is None:
        import types
        mod = types.ModuleType("ptb_maths")
        mod.__dict__['__file__'] = "photo_to_building_maths"
        exec(compile(BLENDER_SCRIPT, "photo_to_building_maths", "exec"), mod.__dict__)
        _MATHS = mod
    return _MATHS


def photo_size(path):
    """(width, height) of a photo in pixels as it's stored (not turned round), or None."""
    from PySide6.QtGui import QImageReader
    try:
        rd = QImageReader(path)
        rd.setAutoTransform(False)
        s = rd.size()
        if s.width() > 0 and s.height() > 0:
            return s.width(), s.height()
    except Exception:
        pass
    return None


def load_photo(path):
    from PySide6.QtGui import QImageReader, QPixmap
    rd = QImageReader(path)
    rd.setAutoTransform(False)                    # as the 3D program shows it, so old clicks still fit
    img = rd.read()
    return QPixmap.fromImage(img) if not img.isNull() else None


PART_STEPS = (3, 4, 5)
MSHORT = {1: "The main building, and any wings, bays or porches.",
          2: "Drag the red lines along one wall, the green along the other.",
          3: "Click corners 1, 2, 3.", 'up': "Corners 1, 2, 3 on your line - then the foot of the front wall.",
          'up_main': "Corners 1, 2, 3 on the main building's line.", 'own': "Click every corner, going round.",
          'bay': "Click its 2 front corners.", 'copy': "Click its left front corner.",
          'tie': "Line up its edges, then click the 2 corners picked.", 'wall': "Click the wall's 4 corners.",
          4: "Click the top of a corner (under the fascia).", 5: "Pick the roof, click its very top.",
          'same': "The same as the one it's copied from - Next.", 6: "Window or door: bottom left, top right.",
          7: "Check the size you know - Send."}
MSTEPS = [(1, "The building's parts"), (2, "Line up the edges"), (3, "Corners on the ground"), (4, "Height"),
          (5, "Roof"), (6, "Windows and doors"), (7, "Size you know - send")]
MHOWTO = {
    1: "What the building's made of: the main building, plus any wings (a separate block) and bays or "
       "porches (built against the main building). Set how many - you can add more later.",
    2: "Drag the dots of the RED lines onto two long, level edges of one wall (the gutter, the bottom of the "
       "wall). Drag the GREEN lines onto edges of the wall round the corner. When it's right, the blue grid looks "
       "like floor tiles lying on the ground, and upright things (corners, lamp posts) stand straight up from it.",
    3: "Click where the front wall meets the ground: corner 1 at one end, corner 2 at the other. Then corner 3 - "
       "the far end of the side wall, on the ground. Can't see it? Type the depth under More (from a map).",
    'up': "Pick a level line that runs all round, clear of clutter, well above or below the dashed eye-level line "
          "(the gutters, the bottom of the plinth). Click "
          "the corners on that line: corner 1 and 2 at the ends of the front, then the far end of the side wall. "
          "Then click Set the height and click the bottom of the front wall (the bottom of the plinth) anywhere it's "
          "clear between corners 1 and 2 - a flat bit of wall, not a bay.",
    'up_main': "Click its corners on the same level line as the main building's (the top of the plinth, the window "
               "sills) - corners 1 and 2 at the ends of its front, then the far end of a side wall.",
    'own': "Click every corner where the walls meet the ground, going round the building. Then click Next.",
    'bay': "Click the bay's two front corners, where it meets the ground. Its back runs to the main building by "
           "itself.",
    'tie': "Another corner photo: 1 - line up its edges like photo 1 (red along one wall, green the other). "
           "2 - pick two of the main building's corners you can see on it (numbered on the plan below), and click "
           "them where the walls meet the ground.",
    'wall': "A photo straight on to one wall: pick which part and wall it is (numbered on the plan below), then "
            "click the wall's 4 corners - bottom left, bottom right, top right, top left (the top ones just under "
            "the gutter). Then click its windows, doors and gables in steps 5 and 6.",
    'copy': "A copy: click its left front corner, where it meets the ground. It's the same size and shape as the "
            "one it's copied from.",
    4: "Click the top of the wall at a corner, just under the gutter - where the roof starts, not the top of a "
       "gable.",
    5: "Pick the roof's shape, then click once on the very top of the roof (the ridge). Pointed gables on the "
       "front of the roof: tick Click gables, then click each one's left and right corners at the eaves and its "
       "peak.",
    'same': "A copy - its height and roof are the same as the one it's copied from. Click Next.",
    6: "Pick Window or Door, and how:  Box - bottom left, then top right.  Half - bottom corner, up the side, "
       "round to the peak, then Enter (or right-click).  All round - every point, then Enter.  Copy - click inside "
       "one you've done, then the bottom left of each one the same.",
    7: "Check the size you know is right, then click Send to Build. The building goes to the Build page.",
}
PHOTO_HELP = {
    'lines': "LINE UP THE EDGES - drag the dots of the red and green lines onto the walls' edges",
    'link': "TIE THIS PHOTO IN - click the main building's two corners picked in the panel",
    'wall4': "THE WALL'S 4 CORNERS - bottom left, bottom right, top right, top left",
    'corners': "CORNERS ON THE GROUND",
    'base': "THE HEIGHT - click the bottom of the front wall anywhere it's clear between corners 1 and 2 (not a bay)",
    'eaves': "HEIGHT - click the top of a corner (the eaves)",
    'ridge': "ROOF - click the very top of the roof",
    'gable': "ROOF GABLES - left corner at the eaves, right corner, then the peak",
    'openings': "WINDOWS AND DOORS",
}
MCOLS = {'r': (255, 51, 38), 'g': (51, 255, 77), 'ground': (255, 217, 26), 'wall': (255, 217, 26),
         'roof': (255, 115, 230), 'window': (77, 204, 255), 'door': (255, 140, 38), 'grid': (90, 153, 255)}
MKEYS = ("W window   D door   B box   H half   A all round   C copy   T top   Backspace takes the last off   "
         "Enter finishes a half / all round")


class PhotoView(QWidget):
    """The photo, to click on: wheel zooms, right-drag (or middle-drag) slides it, F fits it."""

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.pix = None
        self.k = 1.0
        self.ox = self.oy = 0.0
        self.pan = None
        self.mouse = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(600, 450)

    def set_pixmap(self, pix):
        if pix is self.pix and pix is not None:            # the same photo: keep the zoom
            self.update()
            return
        self.pix = pix
        self.fit()

    def fit(self):
        if self.pix is None:
            return
        W, H = self.pix.width(), self.pix.height()
        self.k = max(1e-3, min((self.width() - 10) / W, (self.height() - 10) / H))
        self.ox = (self.width() - W * self.k) / 2.0
        self.oy = (self.height() - H * self.k) / 2.0
        self.update()

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self.fit()

    # photo across/up (0..1, up from the bottom) <-> screen
    def n2s(self, nu, nv):
        W, H = (self.pix.width(), self.pix.height()) if self.pix else (1, 1)
        return QPointF(self.ox + nu * W * self.k, self.oy + (1.0 - nv) * H * self.k)

    def s2n(self, pos):
        W, H = (self.pix.width(), self.pix.height()) if self.pix else (1, 1)
        return (pos.x() - self.ox) / (W * self.k), 1.0 - (pos.y() - self.oy) / (H * self.k)

    def enterEvent(self, ev):
        self.setFocus()
        super().enterEvent(ev)

    def leaveEvent(self, ev):
        self.mouse = None
        self.update()
        super().leaveEvent(ev)

    def mousePressEvent(self, ev):
        pos = ev.position()
        if ev.button() in (Qt.RightButton, Qt.MiddleButton):
            self.pan = dict(start=pos, ox=self.ox, oy=self.oy, moved=ev.button() == Qt.MiddleButton,
                            right=ev.button() == Qt.RightButton)
            return
        if ev.button() == Qt.LeftButton and self.pix is not None:
            self.win.photo_press(self.s2n(pos), pos)

    def mouseMoveEvent(self, ev):
        pos = ev.position()
        self.mouse = pos
        if self.pan:
            dx, dy = pos.x() - self.pan['start'].x(), pos.y() - self.pan['start'].y()
            if not self.pan['moved'] and math.hypot(dx, dy) > 5:
                self.pan['moved'] = True
                self.setCursor(Qt.ClosedHandCursor)
            if self.pan['moved']:
                self.ox, self.oy = self.pan['ox'] + dx, self.pan['oy'] + dy
            self.update()
            return
        if self.pix is not None:
            self.win.photo_move(self.s2n(pos), pos, bool(ev.buttons() & Qt.LeftButton))
        self.update()

    def mouseReleaseEvent(self, ev):
        if self.pan and ev.button() in (Qt.RightButton, Qt.MiddleButton):
            was = self.pan
            self.pan = None
            self.setCursor(Qt.CrossCursor if self.win.mode() else Qt.ArrowCursor)
            if was['right'] and not was['moved']:
                self.win.right_click()
            return
        if ev.button() == Qt.LeftButton:
            self.win.photo_release()

    def wheelEvent(self, ev):
        if self.pix is None:
            return
        pos = ev.position()
        f = 1.2 if ev.angleDelta().y() > 0 else 1 / 1.2
        nk = min(max(self.k * f, 0.02), 20.0)
        self.ox = pos.x() - (pos.x() - self.ox) * nk / self.k
        self.oy = pos.y() - (pos.y() - self.oy) * nk / self.k
        self.k = nk
        self.update()

    def event(self, ev):
        """The photo's own keys come here first, not to IngeTrazo's shortcuts (Delete, Backspace, Ctrl+Z...)."""
        try:
            from PySide6.QtCore import QEvent
            if ev.type() == QEvent.Type.ShortcutOverride and ev.key() in (
                    Qt.Key_Backspace, Qt.Key_Delete, Qt.Key_Z, Qt.Key_Y, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape, Qt.Key_F,
                    Qt.Key_Home, Qt.Key_F11, Qt.Key_W, Qt.Key_D, Qt.Key_B, Qt.Key_H, Qt.Key_A, Qt.Key_C, Qt.Key_T):
                ev.accept()
                return True
        except Exception:
            pass
        return super().event(ev)

    def keyPressEvent(self, ev):
        if ev.key() in (Qt.Key_F, Qt.Key_Home):
            self.fit()
            return
        if not self.win.key(ev):
            super().keyPressEvent(ev)

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(45, 45, 48))
        if self.pix is None:
            p.setPen(QColor(220, 220, 220))
            p.drawText(self.rect(), Qt.AlignCenter, "The photo couldn't be opened.")
            p.end()
            return
        p.setRenderHint(QPainter.SmoothPixmapTransform, self.k < 1.0)
        p.drawPixmap(QRectF(self.ox, self.oy, self.pix.width() * self.k, self.pix.height() * self.k),
                     self.pix, QRectF(0, 0, self.pix.width(), self.pix.height()))
        try:
            self.win.draw_overlay(p, self)
        except Exception as e:
            print("%s: drawing: %s" % (PLUGIN_NAME, e))
        if self.mouse is not None and self.win.mode() and not self.pan:
            self.draw_loupe(p)
        p.end()

    def draw_loupe(self, p):
        """A magnifier in the top corner: what's under the mouse, 4 times bigger, to click corners exactly."""
        from PySide6.QtGui import QColor, QPen, QPainterPath
        R, mag = 75.0, 4.0
        m = self.mouse
        cx = R + 12                                        # always in the bottom left corner
        cy = self.height() - R - 12
        px_ = (m.x() - self.ox) / self.k
        py_ = (m.y() - self.oy) / self.k
        half = R / (self.k * mag)
        p.save()
        path = QPainterPath()
        path.addEllipse(QPointF(cx, cy), R, R)
        p.setClipPath(path)
        p.fillRect(QRectF(cx - R, cy - R, 2 * R, 2 * R), QColor(30, 30, 30))
        p.drawPixmap(QRectF(cx - R, cy - R, 2 * R, 2 * R), self.pix,
                     QRectF(px_ - half, py_ - half, 2 * half, 2 * half))
        p.setClipping(False)
        p.setPen(QPen(QColor(255, 255, 255), 2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(cx, cy), R, R)
        p.setPen(QPen(QColor(255, 60, 60), 1))
        p.drawLine(QPointF(cx - 10, cy), QPointF(cx + 10, cy))
        p.drawLine(QPointF(cx, cy - 10), QPointF(cx, cy + 10))
        p.restore()


class PlanPreview(QWidget):
    """The plan, looking down, under the panel: the parts, wall numbers, corner numbers, windows and doors.
    On step 3 a wing, bay or porch can be dragged into place here and resized by its edges and corners -
    for one that's hidden on the photos (it shows on the photo as it's moved)."""

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setMinimumHeight(260)
        self.setMouseTracking(True)
        self.map = None                   # (cx, cy, sc): plan -> screen, kept still while dragging
        self.drag = None
        self.snapped = False

    # ---- plan <-> screen ----
    def _plans(self):
        M = maths()
        m = self.win.m or {}
        pms = m.get('parts') or []
        main = pms[0].get('outline') if pms else None
        if not main:
            return None, []
        fr = M.plan_frame(main)
        return fr, [[M.to_plan(fr, q) for q in pm_['outline']] if pm_.get('outline') else None for pm_ in pms]

    def _fit(self, plans):
        pts = [q for pl in plans if pl for q in pl]
        mnx, mxx = min(q[0] for q in pts), max(q[0] for q in pts)
        mny, mxy = min(q[1] for q in pts), max(q[1] for q in pts)
        wx, wy = max(mxx - mnx, 1e-6), max(mxy - mny, 1e-6)
        mnx, mxx = mnx - 0.15 * wx, mxx + 0.15 * wx          # room round it to drag into
        mny, mxy = mny - 0.15 * wy, mxy + 0.15 * wy
        x0, y0, x1, y1 = 10.0, 26.0, self.width() - 10.0, self.height() - 24.0
        sc = min((x1 - x0) / (mxx - mnx), (y1 - y0) / (mxy - mny))
        return ((x0 + x1) / 2.0 - (mnx + mxx) / 2.0 * sc, (y0 + y1) / 2.0 + (mny + mxy) / 2.0 * sc, sc)

    def P(self, q):
        cx, cy, sc = self.map
        return QPointF(cx + q[0] * sc, cy - q[1] * sc)

    def Q(self, pos):
        cx, cy, sc = self.map
        return ((pos.x() - cx) / sc, (cy - pos.y()) / sc)

    def editable(self):
        return int(self.win.d.get('step') or 1) == 3

    # ---- the mouse: on step 3, drag a part (not the main building) ----
    def _hit(self, pos):
        """('move' | (edge-x, edge-y), part) under the mouse, or None."""
        if self.map is None or not self.editable():
            return None
        _fr, plans = self._plans()
        d = self.win.d
        q = self.Q(pos)
        tol = 7.0 / self.map[2]
        cur = d['cur']
        if cur > 0 and cur < len(plans) and plans[cur]:
            pl = plans[cur]
            x0, x1 = min(p[0] for p in pl), max(p[0] for p in pl)
            y0, y1 = min(p[1] for p in pl), max(p[1] for p in pl)
            if x0 - tol <= q[0] <= x1 + tol and y0 - tol <= q[1] <= y1 + tol:
                h = ('l' if abs(q[0] - x0) <= tol else 'r' if abs(q[0] - x1) <= tol else '',
                     'b' if abs(q[1] - y0) <= tol else 't' if abs(q[1] - y1) <= tol else '')
                if h != ('', ''):
                    return h, cur
        for pi in range(len(plans) - 1, 0, -1):
            if plans[pi] and _inside(q, plans[pi]):
                return 'move', pi
        return None

    def mousePressEvent(self, ev):
        if ev.button() != Qt.LeftButton:
            return
        pos = ev.position()
        hit = self._hit(pos)
        if hit is None:
            if self.editable() and self.map is not None:
                _fr, plans = self._plans()
                if plans and plans[0] and _inside(self.Q(pos), plans[0]):
                    self.win.say("The main building comes from its clicked corners - drag the wings and bays.")
            return
        h, pi = hit
        d = self.win.d
        self.win.remember()
        if d['cur'] != pi:
            d['cur'] = pi
            self.win.refresh()
        _fr, plans = self._plans()
        pl = [list(q) for q in plans[pi]]
        part = d['parts'][pi]
        part['plan'] = [[round(q[0], 4), round(q[1], 4)] for q in pl]     # from now on, it's where it's put here
        part['copy_of'] = None
        xs, ys = [q[0] for q in pl], [q[1] for q in pl]
        self.drag = dict(h=h, pi=pi, start=pl, box=(min(xs), max(xs), min(ys), max(ys)), at=self.Q(pos),
                         moved=False)

    def mouseMoveEvent(self, ev):
        pos = ev.position()
        if not self.drag:
            hit = self._hit(pos)
            if hit is None:
                self.setCursor(Qt.ArrowCursor)
            elif hit[0] == 'move':
                self.setCursor(Qt.SizeAllCursor)
            else:
                hx, hy = hit[0]
                self.setCursor(Qt.SizeHorCursor if not hy else Qt.SizeVerCursor if not hx else
                               Qt.SizeBDiagCursor if (hx == 'r') == (hy == 't') else Qt.SizeFDiagCursor)
            return
        dr = self.drag
        q = self.Q(pos)
        dx, dy = q[0] - dr['at'][0], q[1] - dr['at'][1]
        x0, x1, y0, y1 = dr['box']
        tol = 9.0 / self.map[2]
        _fr, plans = self._plans()
        xs = [p[0] for k, pl in enumerate(plans) if pl and k != dr['pi'] for p in pl]
        ys = [p[1] for k, pl in enumerate(plans) if pl and k != dr['pi'] for p in pl]
        free = bool(ev.modifiers() & Qt.ControlModifier)
        self.snapped = False

        def near(v, cands):
            best = None
            if not free:
                for c in cands:
                    if abs(c - v) <= tol and (best is None or abs(c - v) < abs(best - v)):
                        best = c
            if best is not None:
                self.snapped = True
            return best
        if dr['h'] == 'move':
            sx = [c - e - dx for e in (x0, x1) for c in [near(e + dx, xs)] if c is not None]
            sy = [c - e - dy for e in (y0, y1) for c in [near(e + dy, ys)] if c is not None]
            dx += min(sx, key=abs) if sx else 0.0
            dy += min(sy, key=abs) if sy else 0.0
            new = [[p[0] + dx, p[1] + dy] for p in dr['start']]
        else:
            hx, hy = dr['h']
            nx0, nx1, ny0, ny1 = x0, x1, y0, y1
            least = 0.05 * max(x1 - x0, y1 - y0, 1e-6)
            if hx == 'l':
                nx0 = min(near(x0 + dx, xs) or (x0 + dx), x1 - least)
            elif hx == 'r':
                nx1 = max(near(x1 + dx, xs) or (x1 + dx), x0 + least)
            if hy == 'b':
                ny0 = min(near(y0 + dy, ys) or (y0 + dy), y1 - least)
            elif hy == 't':
                ny1 = max(near(y1 + dy, ys) or (y1 + dy), y0 + least)
            su = (nx1 - nx0) / ((x1 - x0) or 1.0)
            sv = (ny1 - ny0) / ((y1 - y0) or 1.0)
            new = [[nx0 + (p[0] - x0) * su, ny0 + (p[1] - y0) * sv] for p in dr['start']]
        self.win.d['parts'][dr['pi']]['plan'] = [[round(a, 4), round(b, 4)] for a, b in new]
        dr['moved'] = True
        self.win.recompute(save=False)                    # the photo shows it where it's put

    def mouseReleaseEvent(self, ev):
        if self.drag:
            self.drag = None
            self.snapped = False
            self.win.recompute()

    # ---- drawing ----
    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QPolygonF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(32, 32, 36))
        M = maths()
        d, m = self.win.d, self.win.m or {}
        p.setPen(QColor(215, 215, 215))
        p.drawText(QRectF(8, 4, self.width() - 16, 18), Qt.AlignLeft, "Looking down - the front at the bottom")
        _fr, plans = self._plans()
        if not plans or not plans[0]:
            p.setPen(QColor(170, 170, 170))
            p.drawText(QRectF(8, 26, self.width() - 16, 40), Qt.AlignLeft | Qt.TextWordWrap,
                       "The plan shows here once the main building's corners are clicked.")
            p.end()
            return
        if not self.drag or self.map is None:
            self.map = self._fit(plans)
        P = self.P
        if self.editable() and len(d['parts']) > 1:
            p.setPen(QColor(150, 200, 255))
            p.drawText(QRectF(8, 4, self.width() - 16, 18), Qt.AlignRight, "drag the wings and bays here")
            # the middle of the main building: a copy goes the other side of it
            xs0 = [q[0] for q in plans[0]]
            mid = (min(xs0) + max(xs0)) / 2.0
            p.setPen(QPen(QColor(120, 120, 120), 1, Qt.DashLine))
            p.drawLine(QPointF(P((mid, 0)).x(), 24), QPointF(P((mid, 0)).x(), self.height() - 22))
        for i, pl in enumerate(plans):
            if not pl:
                continue
            here = i == d['cur']
            col = QColor(255, 217, 26) if here else QColor(215, 215, 215, 200)
            p.setPen(QPen(col, 2.5 if here else 1.5))
            p.setBrush(QColor(255, 217, 26, 40) if (here and i > 0 and self.editable()) else Qt.NoBrush)
            p.drawPolygon(QPolygonF([P(q) for q in pl]))
            p.setBrush(Qt.NoBrush)
            mx = sum(q[0] for q in pl) / len(pl)
            my = sum(q[1] for q in pl) / len(pl)
            c = P((mx, my))
            label = M.part_label(i, d['parts'][i])
            if i < len(d['parts']) and d['parts'][i].get('plan'):
                label += " (placed)"
            p.drawText(QRectF(c.x() - 70, c.y() - 9, 140, 18), Qt.AlignCenter, label)
        p.setPen(QColor(100, 255, 255))
        for ci, q in enumerate(plans[0]):                  # the main building's corners, to tie photos in by
            c = P(q)
            p.drawText(QRectF(c.x() + 2, c.y() - 16, 20, 16), Qt.AlignLeft, str(ci + 1))
        pc = plans[d['cur']] if d['cur'] < len(plans) else None
        if pc:                                             # the walls of the part picked: w1, w2...
            p.setPen(QColor(255, 217, 26))
            for wi in range(len(pc)):
                a_, b_ = pc[wi], pc[(wi + 1) % len(pc)]
                c = P(((a_[0] + b_[0]) / 2.0, (a_[1] + b_[1]) / 2.0))
                p.drawText(QRectF(c.x() - 15, c.y() + 1, 30, 14), Qt.AlignCenter, "w%d" % (wi + 1))
            if d['cur'] > 0 and self.editable():           # handles, like a window's corners and sides
                x0, x1 = min(q[0] for q in pc), max(q[0] for q in pc)
                y0, y1 = min(q[1] for q in pc), max(q[1] for q in pc)
                p.setPen(QPen(QColor(255, 217, 26), 1.2))
                p.setBrush(QColor(40, 40, 40))
                for hx in (x0, (x0 + x1) / 2.0, x1):
                    for hy in (y0, (y0 + y1) / 2.0, y1):
                        if hx == (x0 + x1) / 2.0 and hy == (y0 + y1) / 2.0:
                            continue
                        c = P((hx, hy))
                        p.drawRect(QRectF(c.x() - 4, c.y() - 4, 8, 8))
                p.setBrush(Qt.NoBrush)
        for o in m.get('openings') or []:
            pl = plans[o['part']] if o['part'] < len(plans) else None
            if not pl:
                continue
            a, b = pl[o['wall']], pl[(o['wall'] + 1) % len(pl)]
            L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
            u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
            p.setPen(QPen(QColor(*MCOLS['door' if o['kind'] == 'door' else 'window']), 4))
            p.drawLine(P((a[0] + u[0] * o['s0'], a[1] + u[1] * o['s0'])),
                       P((a[0] + u[0] * o['s1'], a[1] + u[1] * o['s1'])))
        k = m.get('k')
        p.setPen(QColor(215, 215, 215))
        if k:
            pc_ = pc if (pc and d['cur'] > 0) else plans[0]
            p.drawText(QRectF(8, self.height() - 20, self.width() - 16, 18), Qt.AlignLeft,
                       "%s: %.2f x %.2f m" % (M.part_label(d['cur'] if pc_ is pc else 0, d['parts'][d['cur']
                                              if pc_ is pc else 0]),
                                            (max(q[0] for q in pc_) - min(q[0] for q in pc_)) * k / 1000.0,
                                            (max(q[1] for q in pc_) - min(q[1] for q in pc_)) * k / 1000.0))
        if self.snapped:
            p.setPen(QColor(80, 220, 120))
            p.drawText(QRectF(8, self.height() - 20, self.width() - 16, 18), Qt.AlignRight, "Lined up")
        p.end()


class MatchWindow(QDialog):
    """Clicking round the building on its photos, here in IngeTrazo: the same 7 steps as the 3D program's
    panel, the photo big on the left, the steps on the right with the plan under them."""

    def __init__(self, main, folder, photo, extras, values, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QStackedWidget, QRadioButton, QButtonGroup, QScrollArea, QFrame
        self.setWindowTitle("Click round the building - %s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.main = main
        self.folder = folder
        self.M = maths()
        self.pixes = {}
        self.busy = False
        self.pending = None                   # the first corner of a box
        self.trace = []                       # the points of a half / all round
        self.copy_src = None
        self.hover = None
        self.drag = None                      # (line, end) being dragged
        self.note = ""
        self.kind, self.how, self.top = 'window', 'box', 'square'
        self.gable_mode = False
        self.base_mode = False                # clicking the ground below a corner clicked up the wall
        self.tie_mode = 'lines'               # another corner photo: lining up, or clicking the two corners
        self.history = []                     # before each change, for Ctrl+Z
        self.future = []                      # what Ctrl+Z took off, for Ctrl+Y
        self.d = self._load_or_new(photo, values)
        for ex in extras or []:
            self.add_photo(ex.get('path'), 'wall' if ex.get('kind') == 'wall' else 'corner', quiet=True)
        self.m = None
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self.save_clicks)

        lay = QHBoxLayout(self)
        left = QVBoxLayout()
        self.lbl_top = QLabel()
        self.lbl_top.setWordWrap(True)
        left.addWidget(self.lbl_top)
        self.view = PhotoView(self)
        left.addWidget(self.view, 1)
        hrow = QHBoxLayout()
        hrow.addWidget(_note("Wheel: zoom.  Right-drag: slide the photo.  F: fit it in.  The circle shows what's "
                             "under the mouse close up.", True), 1)
        self.b_full = QPushButton("Full screen  (F11)")
        self.b_full.setCheckable(True)
        self.b_full.setToolTip("Fills the whole screen with this window - click again (or press F11 or Esc) to "
                               "come back.")
        hrow.addWidget(self.b_full)
        left.addLayout(hrow)
        lay.addLayout(left, 3)

        side_w = QWidget()
        side = QVBoxLayout(side_w)
        side.setContentsMargins(0, 0, 0, 0)
        srow = QHBoxLayout()
        self.step_btns = []
        for n, title in MSTEPS:
            b = QPushButton(str(n))
            b.setCheckable(True)
            b.setMinimumHeight(30)
            b.setMinimumWidth(30)
            b.setMaximumWidth(60)
            b.setToolTip(title)
            b.clicked.connect(lambda _c=False, n=n: self.goto(n))
            srow.addWidget(b)
            self.step_btns.append(b)
        side.addLayout(srow)
        prow = QHBoxLayout()
        b_prev = QPushButton("◀")
        b_next = QPushButton("▶")
        for b_ in (b_prev, b_next):
            b_.setFixedWidth(30)
        self.lbl_photo = QLabel()
        prow.addWidget(b_prev)
        prow.addWidget(self.lbl_photo, 1)
        prow.addWidget(b_next)
        side.addLayout(prow)
        arow = QHBoxLayout()
        b_addc = QPushButton("+ Corner photo")
        b_addc.setToolTip("Another photo of the building from a different corner (the back, the other end...).")
        b_addw = QPushButton("+ Straight-on photo")
        b_addw.setToolTip("A photo looking straight at one wall - good for its windows and doors.")
        self.b_rmph = QPushButton("Take this photo off")
        arow.addWidget(b_addc)
        arow.addWidget(b_addw)
        side.addLayout(arow)
        arow2 = QHBoxLayout()
        arow2.addStretch(1)
        arow2.addWidget(self.b_rmph)
        side.addLayout(arow2)

        self.lbl_step = QLabel()
        f = self.lbl_step.font()
        f.setBold(True)
        if f.pointSizeF() > 0:
            f.setPointSizeF(f.pointSizeF() * 1.15)
        self.lbl_step.setFont(f)
        side.addWidget(self.lbl_step)
        # which part (steps 3 to 5 work through each in turn)
        self.part_row = QWidget()
        pr = QHBoxLayout(self.part_row)
        pr.setContentsMargins(0, 0, 0, 0)
        self.lbl_part = QLabel()
        self.b_pclone = QPushButton("Copy")
        self.b_pclone.setToolTip("Another one the same (click where it goes).")
        self.b_premove = QPushButton("Take off")
        pr.addWidget(self.lbl_part, 1)
        pr.addWidget(self.b_pclone)
        pr.addWidget(self.b_premove)
        side.addWidget(self.part_row)
        self.lbl_how = _note("")
        side.addWidget(self.lbl_how)

        self.stack = QStackedWidget()
        side.addWidget(self.stack)
        # 1 the parts
        pg = QWidget()
        v1 = QVBoxLayout(pg)
        v1.setContentsMargins(0, 0, 0, 0)
        self.lbl_wings = QLabel()
        self.lbl_bays = QLabel()
        for lab, less, more in ((self.lbl_wings, 'less', 'add'), (self.lbl_bays, 'less_against', 'add_against')):
            r_ = QHBoxLayout()
            r_.addWidget(lab, 1)
            bm, bp = QPushButton("−"), QPushButton("+")
            for b_ in (bm, bp):
                b_.setFixedWidth(30)
                r_.addWidget(b_)
            bm.clicked.connect(lambda _c=False, a=less: self.part_action(a))
            bp.clicked.connect(lambda _c=False, a=more: self.part_action(a))
            v1.addLayout(r_)
        self.lst_parts = QListWidget()
        self.lst_parts.setMaximumHeight(130)
        v1.addWidget(self.lst_parts)
        r_ = QHBoxLayout()
        b_c = QPushButton("Copy this part")
        b_r = QPushButton("Take this part off")
        r_.addWidget(b_c)
        r_.addWidget(b_r)
        v1.addLayout(r_)
        b_c.clicked.connect(lambda: self.part_action('clone', self.lst_parts.currentRow()))
        b_r.clicked.connect(lambda: self.part_action('remove', self.lst_parts.currentRow()))
        self.stack.addWidget(pg)
        # 2 line up / set up another photo
        pg = QWidget()
        v2 = QVBoxLayout(pg)
        v2.setContentsMargins(0, 0, 0, 0)
        self.tie_box = QWidget()
        tb = QVBoxLayout(self.tie_box)
        tb.setContentsMargins(0, 0, 0, 0)
        self.rb_tie_lines = QRadioButton("1  Line up its edges")
        self.rb_tie_link = QRadioButton("2  Click the two corners")
        self.grp_tie = QButtonGroup(self)
        for i_, rb in enumerate((self.rb_tie_lines, self.rb_tie_link)):
            self.grp_tie.addButton(rb, i_)
            tb.addWidget(rb)
        fl2 = QFormLayout()
        self.cb_link_a = QComboBox()
        self.cb_link_b = QComboBox()
        fl2.addRow("First corner", self.cb_link_a)
        fl2.addRow("Second corner", self.cb_link_b)
        tb.addLayout(fl2)
        v2.addWidget(self.tie_box)
        self.wall_box = QWidget()
        fl3 = QFormLayout(self.wall_box)
        fl3.setContentsMargins(0, 0, 0, 0)
        self.cb_wpart = QComboBox()
        self.cb_wwall = QComboBox()
        fl3.addRow("Part", self.cb_wpart)
        fl3.addRow("Wall", self.cb_wwall)
        v2.addWidget(self.wall_box)
        self.lbl_photo_state = _note("", True)
        v2.addWidget(self.lbl_photo_state)
        v2.addStretch(1)
        self.stack.addWidget(pg)
        # 3 corners
        pg = QWidget()
        fl = QFormLayout(pg)
        fl.setContentsMargins(0, 0, 0, 0)
        self.cb_shape = QComboBox()
        self.cb_shape.addItem("Rectangle - click 3 corners", 'rect')
        self.cb_shape.addItem("My own corners - click every one", 'own')
        fl.addRow("Shape", self.cb_shape)
        self.cb_clickat = QComboBox()
        self.cb_clickat.addItem("On the ground", 'ground')
        self.cb_clickat.addItem("Up the wall - all at one height", 'up')
        self.cb_clickat.addItem("Up the wall - the main building's height", 'up_main')
        self.cb_clickat.setToolTip("Cluttered at the bottom? Click the corners part way up instead, on a level line "
                                   "that runs all round (the top of the plinth, the window sills).")
        fl.addRow("Click corners", self.cb_clickat)
        self.b_base = QPushButton("Set the height: click the foot of the front wall")
        self.b_base.setCheckable(True)
        self.b_base.setToolTip("One click: the bottom of the front wall (the bottom of the plinth), anywhere it's "
                               "clear between corners 1 and 2 - not on a bay. It works out how high up your corners "
                               "are from that.")
        fl.addRow(self.b_base)
        fl.addRow(_note("<b>Hidden on the photo?</b> Drag it into place on the plan below - by the middle to move "
                        "it, by its edges or corners to size it.", True))
        r3 = QHBoxLayout()
        self.b_plan_put = QPushButton("Put it on the plan")
        self.b_plan_put.setToolTip("For a part you can't click on the photos: a box next to the main building "
                                   "on the plan, to drag into place.")
        self.b_plan_mirror = QPushButton("Copy to the other end")
        self.b_plan_mirror.setToolTip("A mirror copy of this part on the other end of the main building, the "
                                      "same height and roof. Drag it to fit if the ends aren't the same.")
        r3.addWidget(self.b_plan_put)
        r3.addWidget(self.b_plan_mirror)
        fl.addRow(r3)
        self.b_plan_reset = QPushButton("Back to its clicked corners")
        fl.addRow(self.b_plan_reset)
        self.b_more3 = QPushButton("More...")
        self.b_more3.setCheckable(True)
        fl.addRow(self.b_more3)
        self.more3 = QWidget()
        fm = QFormLayout(self.more3)
        fm.setContentsMargins(0, 0, 0, 0)
        self.ed_pname = QLineEdit()
        self.ck_against = QCheckBox("Against the main building (a bay, porch or lean-to)")
        self.sp_maplen = QDoubleSpinBox()
        self.sp_depth = QDoubleSpinBox()
        for s in (self.sp_maplen, self.sp_depth):
            s.setRange(0.0, 200000.0)
            s.setDecimals(0)
            s.setSingleStep(100.0)
            s.setSuffix(" mm")
            s.setSpecialValueText("from the photo")
        fm.addRow("Name", self.ed_pname)
        fm.addRow(self.ck_against)
        fm.addRow("Front, from a map", self.sp_maplen)
        fm.addRow("Depth, from a map", self.sp_depth)
        self.b_clear_corners = QPushButton("Clear this part's corners")
        fm.addRow(self.b_clear_corners)
        fl.addRow(self.more3)
        self.stack.addWidget(pg)
        # 4 height
        pg = QWidget()
        fl = QFormLayout(pg)
        fl.setContentsMargins(0, 0, 0, 0)
        self.sp_storeys = QSpinBox()
        self.sp_storeys.setRange(1, 20)
        fl.addRow("Floors (storeys)", self.sp_storeys)
        self.sp_eaves_mm = QDoubleSpinBox()
        self.sp_ridge_mm = QDoubleSpinBox()
        for s_ in (self.sp_eaves_mm, self.sp_ridge_mm):
            s_.setRange(0.0, 100000.0)
            s_.setDecimals(0)
            s_.setSingleStep(100.0)
            s_.setSuffix(" mm")
            s_.setSpecialValueText("clicked on the photo")
        self.lbl_typed4 = _note("Can't see its top corner? Type its height to the eaves instead:", True)
        fl.addRow(self.lbl_typed4)
        fl.addRow("Eaves height", self.sp_eaves_mm)
        self.stack.addWidget(pg)
        # 5 roof
        pg = QWidget()
        fl = QFormLayout(pg)
        fl.setContentsMargins(0, 0, 0, 0)
        self.cb_roof = QComboBox()
        for key, label, _desc in self.M.ROOFS:
            self.cb_roof.addItem(label, key)
        self.cb_low = QComboBox()
        self.cb_low.addItem("The low side at the front", 'front')
        self.cb_low.addItem("The low side at the back", 'back')
        fl.addRow("Roof", self.cb_roof)
        fl.addRow("Lean-to", self.cb_low)
        self.lbl_typed5 = _note("Can't see its roof top? Type its height instead:", True)
        fl.addRow(self.lbl_typed5)
        fl.addRow("Roof top height", self.sp_ridge_mm)
        self.lbl_gables = QLabel()
        fl.addRow(self.lbl_gables)
        self.ck_gables = QCheckBox("Click gables (pointed ones on the front of the roof)")
        fl.addRow(self.ck_gables)
        self.b_gable_off = QPushButton("Take the last gable off")
        fl.addRow(self.b_gable_off)
        self.stack.addWidget(pg)
        # 6 windows and doors
        pg = QWidget()
        v6 = QVBoxLayout(pg)
        v6.setContentsMargins(0, 0, 0, 0)
        r6 = QHBoxLayout()
        self.rb_win = QRadioButton("Windows (W)")
        self.rb_door = QRadioButton("Doors (D)")
        self.grp_kind = QButtonGroup(self)
        self.grp_kind.addButton(self.rb_win, 0)
        self.grp_kind.addButton(self.rb_door, 1)
        r6.addWidget(self.rb_win)
        r6.addWidget(self.rb_door)
        v6.addLayout(r6)
        r6b = QHBoxLayout()
        self.grp_how = QButtonGroup(self)
        self.how_btns = {}
        for i_, (key, lab) in enumerate((('box', "Box (B)"), ('trace', "Half (H)"), ('outline', "All round (A)"),
                                         ('copy', "Copy (C)"))):
            rb = QRadioButton(lab)
            self.grp_how.addButton(rb, i_)
            self.how_btns[key] = rb
            r6b.addWidget(rb)
        v6.addLayout(r6b)
        f6 = QFormLayout()
        self.cb_top = QComboBox()
        for key, label, _desc in self.M.TOPS:
            self.cb_top.addItem(label, key)
        f6.addRow("Top (T)", self.cb_top)
        v6.addLayout(f6)
        r6c = QHBoxLayout()
        self.b_op_off = QPushButton("Take the last off")
        self.lbl_ops = QLabel()
        r6c.addWidget(self.b_op_off)
        r6c.addWidget(self.lbl_ops, 1)
        v6.addLayout(r6c)
        self.stack.addWidget(pg)
        # 7 the size you know, send
        pg = QWidget()
        v7 = QVBoxLayout(pg)
        v7.setContentsMargins(0, 0, 0, 0)
        f7 = QFormLayout()
        self.cb_known = QComboBox()
        for key, label in self.M.KNOWN:
            self.cb_known.addItem(label, key)
        self.sp_known = QDoubleSpinBox()
        self.sp_known.setRange(1.0, 200000.0)
        self.sp_known.setDecimals(0)
        self.sp_known.setSingleStep(10.0)
        self.sp_known.setSuffix(" mm")
        f7.addRow("Known size", self.cb_known)
        f7.addRow("It is", self.sp_known)
        v7.addLayout(f7)
        self.lbl_sizes = _note("", True)
        v7.addWidget(self.lbl_sizes)
        self.b_send = QPushButton("Send to Build  ▶")
        self.b_send.setMinimumHeight(38)
        v7.addWidget(self.b_send)
        self.stack.addWidget(pg)

        self.lbl_problem = _note("")
        self.lbl_problem.setStyleSheet("color: #b00;")
        side.addWidget(self.lbl_problem)
        urow = QHBoxLayout()
        self.b_undo_click = QPushButton("Undo  (Ctrl+Z)")
        self.b_undo_click.setToolTip("Takes off the last click or change (Backspace does too).")
        self.b_redo = QPushButton("Bring it back  (Ctrl+Y)")
        self.b_redo.setToolTip("Puts back what Undo just took off.")
        self.b_restart = QPushButton("Start this step again")
        urow.addWidget(self.b_undo_click)
        urow.addWidget(self.b_redo)
        urow.addWidget(self.b_restart)
        side.addLayout(urow)
        nrow = QHBoxLayout()
        self.b_back = QPushButton("Back")
        self.b_fwd = QPushButton("Next")
        for b_ in (self.b_back, self.b_fwd):
            b_.setMinimumHeight(34)
        nrow.addWidget(self.b_back)
        nrow.addWidget(self.b_fwd, 2)
        side.addLayout(nrow)
        self.diag = StepDiagram(self)
        side.addWidget(self.diag)
        self.plan = PlanPreview(self)
        side.addWidget(self.plan, 1)
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setFrameShape(QFrame.NoFrame)
        sa.setWidget(side_w)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)      # it fits across: no sliding sideways
        sa.setMinimumWidth(430)
        lay.addWidget(sa, 1)
        try:
            self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        except Exception:
            pass

        # ---- connections ----
        b_prev.clicked.connect(lambda: self.photo_action('prev'))
        b_next.clicked.connect(lambda: self.photo_action('next'))
        self.b_rmph.clicked.connect(lambda: self.photo_action('remove'))
        b_addc.clicked.connect(lambda: self.pick_photo('corner'))
        b_addw.clicked.connect(lambda: self.pick_photo('wall'))
        self.b_pclone.clicked.connect(lambda: self.part_action('clone'))
        self.b_premove.clicked.connect(lambda: self.part_action('remove'))
        self.lst_parts.currentRowChanged.connect(self._list_pick)
        self.grp_tie.idClicked.connect(self._tie_mode)
        self.cb_link_a.currentIndexChanged.connect(lambda i: self._link_corner(0, i))
        self.cb_link_b.currentIndexChanged.connect(lambda i: self._link_corner(1, i))
        self.cb_wpart.currentIndexChanged.connect(self._wall_part)
        self.cb_wwall.currentIndexChanged.connect(self._wall_wall)
        self.cb_shape.currentIndexChanged.connect(lambda _i: self._part_set('shape', self.cb_shape.currentData()))
        self.b_more3.toggled.connect(self.more3.setVisible)
        self.ed_pname.editingFinished.connect(lambda: self._part_set('name', self.ed_pname.text().strip()))
        self.ck_against.toggled.connect(lambda on: self._part_set('against', bool(on)))
        self.sp_maplen.valueChanged.connect(lambda v: self._part_set('map_len', float(v)))
        self.sp_depth.valueChanged.connect(lambda v: self._part_set('depth_mm', float(v)))
        self.b_clear_corners.clicked.connect(lambda: self._part_set('corners', []))
        self.sp_storeys.valueChanged.connect(lambda v: self._part_set('storeys', int(v)))
        self.sp_eaves_mm.valueChanged.connect(lambda v: self._part_set('eaves_mm', float(v)))
        self.sp_ridge_mm.valueChanged.connect(lambda v: self._part_set('ridge_mm', float(v)))
        self.b_plan_put.clicked.connect(self.plan_put)
        self.cb_clickat.currentIndexChanged.connect(lambda _i: self._part_set('click_at', self.cb_clickat.currentData()))
        self.b_base.toggled.connect(self._base_mode)
        self.b_plan_mirror.clicked.connect(self.plan_mirror)
        self.b_plan_reset.clicked.connect(self.plan_reset)
        self.cb_roof.currentIndexChanged.connect(lambda _i: self._part_set('roof', self.cb_roof.currentData()))
        self.cb_low.currentIndexChanged.connect(lambda _i: self._part_set('roof_low', self.cb_low.currentData()))
        self.ck_gables.toggled.connect(self._gable_mode)
        self.b_gable_off.clicked.connect(self.gable_off)
        self.grp_kind.idClicked.connect(lambda i: self._set_kind('door' if i == 1 else 'window'))
        self.grp_how.idClicked.connect(lambda i: self._set_how(('box', 'trace', 'outline', 'copy')[i]))
        self.cb_top.currentIndexChanged.connect(lambda _i: self._set_top(self.cb_top.currentData()))
        self.b_op_off.clicked.connect(self.opening_off)
        self.cb_known.currentIndexChanged.connect(lambda _i: self._known())
        self.sp_known.valueChanged.connect(lambda _v: self._known())
        self.b_send.clicked.connect(self.send)
        self.b_full.toggled.connect(self.full_screen)
        self.b_restart.clicked.connect(self.restart_step)
        self.b_undo_click.clicked.connect(self.undo_click)
        self.b_redo.clicked.connect(self.redo)
        self.b_back.clicked.connect(lambda: self.walk(True))
        self.b_fwd.clicked.connect(lambda: self.walk(False))

        self.more3.setVisible(False)
        self.resize(1450, 900)
        try:
            eddy_place(self, PLUGIN_NAME + " - clicking")
        except Exception:
            pass
        self.show_current_photo()
        self.recompute()
        self._install_keys()
        if load_settings().get('match_full'):
            QTimer.singleShot(0, lambda: self.b_full.setChecked(True))

    def full_screen(self, on):
        if on:
            self._was_max = self.isMaximized()
            self.showFullScreen()
        elif getattr(self, '_was_max', False):
            self.showMaximized()
        else:
            self.showNormal()
        save_settings(match_full=bool(on))
        QTimer.singleShot(100, self.view.fit)

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_F11 or (ev.key() == Qt.Key_Escape and self.isFullScreen()):
            self.b_full.setChecked(not self.b_full.isChecked())
            return
        if ev.key() == Qt.Key_Escape:
            return                                         # Esc doesn't close the window by mistake
        super().keyPressEvent(ev)

    # ---- the clicks: kept in the job's folder ----
    def _load_or_new(self, photo, values):
        M = self.M
        cp = os.path.join(self.folder, CLICKS_NAME)
        if os.path.isfile(cp):
            try:
                with open(cp, "r", encoding="utf-8") as f:
                    d = json.load(f).get('clicks')
                if isinstance(d, dict) and d.get('W') and d.get('lines'):
                    M.migrate(d)
                    d['photos'][0]['path'] = d['photos'][0].get('path') or photo
                    return d
            except Exception as e:
                print("%s: the clicks couldn't be read (%s) - starting again" % (PLUGIN_NAME, e))
        size = photo_size(photo) or (1000, 750)
        d = M.data_default(size[0], size[1])
        M.migrate(d)
        d['photos'][0].update(path=photo, kind='corner')
        for key in ('known_what', 'known_mm'):
            if values.get(key) is not None:
                d[key] = values[key]
        for key in ('storeys', 'roof', 'roof_low', 'shape', 'depth_mm'):
            if values.get(key) is not None:
                d['parts'][0][key] = values[key]
        return d

    def save_clicks(self):
        try:
            m = self.m or {}
            info = {'saved': time.strftime("%Y-%m-%d %H:%M:%S"), 'clicks': self.d,
                    'problems': m.get('problems') or [],
                    'sizes': self.M.sizes_text(m, self.d) if m.get('parts') else []}
            tmp = os.path.join(self.folder, CLICKS_NAME + ".part")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(info, f, indent=1)
            os.replace(tmp, os.path.join(self.folder, CLICKS_NAME))
        except Exception as e:
            print("%s: clicks not saved: %s" % (PLUGIN_NAME, e))

    def closeEvent(self, ev):
        self.save_clicks()
        self._remove_keys()
        super().closeEvent(ev)

    # ---- the keys: caught before IngeTrazo's own shortcuts while this window's in front ----
    KEYS = None

    def _install_keys(self):
        from PySide6.QtCore import QObject, QEvent
        from PySide6.QtWidgets import QApplication, QLineEdit, QAbstractSpinBox
        win = self
        keys = {Qt.Key_Backspace, Qt.Key_Delete, Qt.Key_Z, Qt.Key_Y, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape, Qt.Key_F,
                Qt.Key_Home, Qt.Key_F11, Qt.Key_W, Qt.Key_D, Qt.Key_B, Qt.Key_H, Qt.Key_A, Qt.Key_C, Qt.Key_T}

        class _Keys(QObject):
            def eventFilter(self, obj, ev):
                try:
                    t = ev.type()
                    if t in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease) and win.isVisible() and \
                            win.isActiveWindow() and ev.key() == Qt.Key_Alt:
                        return True                        # Alt on its own: no Windows menu
                    if t not in (QEvent.Type.KeyPress, QEvent.Type.ShortcutOverride):
                        return False
                    if not win.isVisible() or not win.isActiveWindow() or ev.key() not in keys:
                        return False
                    fw = QApplication.focusWidget()
                    if isinstance(fw, (QLineEdit, QAbstractSpinBox)):
                        return False                       # typing in a box: the box has the keys
                    if t == QEvent.Type.ShortcutOverride:
                        ev.accept()                        # not IngeTrazo's shortcut
                        return True
                    return bool(win.handle_key(ev))
                except Exception:
                    return False
        try:
            self._keys = _Keys(self)
            QApplication.instance().installEventFilter(self._keys)
        except Exception as e:
            print("%s: keys: %s" % (PLUGIN_NAME, e))

    def _remove_keys(self):
        try:
            from PySide6.QtWidgets import QApplication
            if getattr(self, '_keys', None) is not None:
                QApplication.instance().removeEventFilter(self._keys)
                self._keys = None
        except Exception:
            pass

    def handle_key(self, ev):
        k = ev.key()
        mod = ev.modifiers()
        if k in (Qt.Key_F, Qt.Key_Home) and not mod & (Qt.ControlModifier | Qt.AltModifier):
            self.view.fit()
            return True
        if k == Qt.Key_F11:
            self.b_full.setChecked(not self.b_full.isChecked())
            return True
        return self.key(ev) or k == Qt.Key_Escape

    def recompute(self, save=True):
        M = self.M
        M.migrate(self.d)
        try:
            self.m = M.compute(self.d)
        except Exception as e:
            self.m = {'problems': ["Couldn't measure it: %s" % e], 'parts': [], 'openings': [], 'views': []}
        self.refresh()
        if save:
            self._save_timer.start(400)

    # ---- photos ----
    def add_photo(self, path, kind, quiet=False):
        d = self.d
        if not path or not os.path.isfile(path):
            return None
        for k, ph in enumerate(d['photos']):
            if os.path.normcase(ph.get('path') or '') == os.path.normcase(path):
                return k
        size = photo_size(path)
        if not size:
            if not quiet:
                self.say("Couldn't open that photo.")
            return None
        ph = {'path': path, 'kind': kind, 'W': size[0], 'H': size[1]}
        if kind == 'corner':
            ph.update(lines=self.M.start_lines(), link=[], link_corners=[0, 1])
        else:
            ph.update(part=0, wall=0, quad=[])
        d['photos'].append(ph)
        return len(d['photos']) - 1

    def pick_photo(self, kind):
        folder = os.path.dirname(self.d['photos'][0].get('path') or '') or DEFAULT_PICTURES
        path, _f = QFileDialog.getOpenFileName(self, "Another photo of the building", folder,
                                               "Photos (%s)" % " ".join("*" + e for e in PICTURE_TYPES))
        if not path:
            return
        k = self.add_photo(path, kind)
        if k is None:
            return
        self.d['photo'] = k
        self.d['step'] = 2                                   # set it up
        self.tie_mode = 'lines'
        self.show_current_photo()
        self.recompute()

    def photo_action(self, action):
        d, M = self.d, self.M
        k, n = M.cur_photo(d), len(d['photos'])
        if action == 'next':
            d['photo'] = (k + 1) % n
        elif action == 'prev':
            d['photo'] = (k - 1) % n
        elif action == 'remove' and k > 0:
            if QMessageBox.question(self, PLUGIN_NAME, "Take this photo off, with everything clicked on it?") != \
                    QMessageBox.StandardButton.Yes:
                return
            self.remember()
            ck = M.ck
            d['photos'].pop(k)
            drop = lambda cl: [c for c in cl if ck(c) != k]
            shift = lambda cl: [(list(c[:2]) + [ck(c) - 1]) if ck(c) > k else c for c in cl]
            for p_ in d['parts']:                          # its clicks go with it
                p_['corners'] = shift(drop(p_.get('corners') or []))
                for key in ('eaves', 'ridge'):
                    c = p_.get(key)
                    if c and ck(c) == k:
                        p_[key] = None
                    elif c and ck(c) > k:
                        p_[key] = list(c[:2]) + [ck(c) - 1]
            d['openings'] = [dict(o, clicks=shift(o['clicks'])) for o in d['openings']
                             if not any(ck(c) == k for c in o.get('clicks') or [])]
            d['gables'] = [dict(g, clicks=shift(g['clicks'])) for g in d.get('gables') or []
                           if not any(ck(c) == k for c in g.get('clicks') or [])]
            self.copy_src = None
            d['photo'] = 0
        else:
            return
        self.pending, self.trace = None, []
        self.tie_mode = 'lines' if not self.M.lines_done(d, self.M.cur_photo(d)) else 'link'
        self.show_current_photo()
        self.recompute()

    def show_current_photo(self):
        k = self.M.cur_photo(self.d)
        path = self.d['photos'][k].get('path') or ''
        if path not in self.pixes:
            self.pixes[path] = load_photo(path) if path and os.path.isfile(path) else None
        self.view.set_pixmap(self.pixes[path])

    # ---- what clicking does now ----
    def mode(self):
        d = self.d
        step = int(d.get('step') or 1)
        kph = self.M.cur_photo(d)
        kind = self.M.photo_info(d, kph).get('kind')
        if step == 2:
            if kind == 'wall':
                return 'wall4'
            return self.tie_mode if kph > 0 else 'lines'
        if step == 5 and self.gable_mode:
            return 'gable'
        if step == 3 and self.base_mode:
            return 'base'
        if step == 3:
            part = d['parts'][d['cur']]
            if part.get('click_at') == 'up' and part.get('copy_of') is None and self._corners_full(part):
                return 'base'                              # corners done: on to the height
        return {3: 'corners', 4: 'eaves', 5: 'ridge', 6: 'openings'}.get(step)

    def _corners_full(self, part):
        """Has this part got all the corners it takes (3 for a rectangle, 2 against the building, 1 for a copy)?"""
        d = self.d
        most = 1 if part.get('copy_of') is not None else (2 if (d['parts'].index(part) > 0 and part.get('against'))
                                                           else 3)
        return (part.get('shape', 'rect') == 'rect' or most < 3) and len(part.get('corners') or []) >= most

    def can_click(self, what):
        """None if clicking for this step can go ahead, else why not."""
        M, d, m = self.M, self.d, self.m or {}
        kph = M.cur_photo(d)
        ph = M.photo_info(d, kph)
        views = m.get('views') or []
        view = views[kph] if kph < len(views) else None
        if what in ('corners', 'eaves', 'ridge', 'openings', 'link', 'gable') and m.get('cam') is None:
            return "Line up the edges on photo 1 first (step 2)."
        if what == 'base':
            what = 'corners'
        if what in ('corners', 'eaves', 'ridge') and ph.get('kind') == 'wall':
            return ("This photo's straight on to one wall - do corners, heights and roofs on a corner photo "
                    "(windows, doors and gables are fine here).")
        if what == 'corners' and kph > 0 and d['cur'] == 0:
            return "The main building's corners go on photo 1 - the other photos are tied to them."
        if what in ('corners', 'eaves', 'ridge', 'openings', 'gable') and kph > 0 and view is None:
            return "Set this photo up first (step 2): %s" % ((m.get('photo_problems') or {}).get(kph) or
                                                             "line it up and tie it in")
        if what == 'link' and not m.get('outline'):
            return "The main building's corners on photo 1 come first (step 3)."
        pms = m.get('parts') or []
        pm = pms[d['cur']] if d['cur'] < len(pms) else {}
        if what in ('eaves', 'ridge') and not (pm.get('outline') or len(pm.get('raw') or []) >= 2):
            return "Click the corners on the ground first (step 3)."
        if what == 'ridge' and not pm.get('outline'):
            return "The outline isn't finished - click corner 3, or type the depth under More (step 3)."
        if what in ('openings', 'gable') and not m.get('outline'):
            return "The main building's outline isn't finished - click corner 3, or type the depth (step 3)."
        if what == 'corners' and d['cur'] > 0 and d['parts'][d['cur']].get('against') and not m.get('outline'):
            return "Finish the main building's corners first - this part runs back to it."
        part = d['parts'][d['cur']]
        if what in ('eaves', 'ridge') and (part.get('copy_of') is not None or part.get('same_as') is not None):
            return "A copy - its height and roof are the same as the one it's copied from. Click Next."
        if what == 'ridge' and part.get('roof') in ('flat', 'none'):
            return "No roof top to click for a flat roof (or no roof) - click Next."
        return None

    # ---- the mouse on the photo ----
    def photo_press(self, n, pos):
        M, d = self.M, self.d
        what = self.mode()
        if not what:
            self.say("Nothing to click on this step - %s" % ("set the parts up, then click Next."
                                                            if int(d.get('step') or 1) == 1 else
                                                            "check the size, then Send."))
            return
        nu, nv = n
        kph = M.cur_photo(d)
        if what == 'lines':
            best = None
            for key in M.LINE_KEYS:
                for end in (0, 1):
                    q = self.view.n2s(*M.cur_lines(d)[key][end][:2])
                    dist = math.hypot(q.x() - pos.x(), q.y() - pos.y())
                    if dist < 22 and (best is None or dist < best[0]):
                        best = (dist, key, end)
            self.drag = (best[1], best[2]) if best else None
            if best:
                self.remember()
            if not best:
                self.say("Drag the dots at the ends of the red and green lines.")
            return
        why = self.can_click(what)
        if why:
            self.say(why, True)
            return
        self.note = ""
        self.remember()
        if what == 'link':
            ph = d['photos'][kph]
            lk = ph.setdefault('link', [])
            pick = ph.get('link_corners') or [0, 1]
            if len(lk) >= 2:
                lk.clear()
            lk.append({'c': [nu, nv], 'corner': int(pick[len(lk)])})
        elif what == 'wall4':
            q = d['photos'][kph].setdefault('quad', [])
            if len(q) >= 4:
                q.clear()
            q.append([nu, nv])
        elif what == 'corners':
            part = d['parts'][d['cur']]
            if self._corners_full(part):                   # done: a stray click mustn't wipe them
                self.history.pop()
                self.say("This part's corners are all clicked. To click them again: Undo (Ctrl+Z), or More... > "
                         "Clear this part's corners.", True)
                return
            part['corners'].append([nu, nv, kph])
        elif what in ('eaves', 'ridge'):
            d['parts'][d['cur']][what] = [nu, nv, kph]
        elif what == 'base':
            part = d['parts'][d['cur']]
            part['base'] = [nu, nv, kph]                   # the foot of the front wall: the line above is found
            part['base_top'] = None
            self.base_mode = False
        elif what == 'gable':
            gl = d.setdefault('gables', [])
            if not gl or len(gl[-1].get('clicks') or []) >= 3:
                gl.append({'clicks': []})
            gl[-1]['clicks'].append([nu, nv, kph])
        elif what == 'openings':
            if self.how in ('trace', 'outline'):
                self.trace.append([nu, nv, kph])
            elif self.how == 'copy':
                hit = self.opening_at(nu, nv, kph)
                if hit is not None:
                    self.copy_src = hit                    # the one to copy
                elif self.copy_src is None:
                    self.note = "Click inside the window you want to copy first."
                else:
                    d['openings'].append({'how': 'copy', 'src': self.copy_src, 'clicks': [[nu, nv, kph]]})
            elif self.pending is None:
                self.pending = {'click': [nu, nv, kph], 'kind': self.kind}
            else:
                d['openings'].append({'kind': self.pending['kind'], 'top': self.top, 'how': 'box',
                                      'clicks': [self.pending['click'], [nu, nv, kph]]})
                self.pending = None
        self.recompute()

    def photo_move(self, n, pos, held):
        if self.drag and held:
            key, end = self.drag
            self.M.cur_lines(self.d)[key][end] = [n[0], n[1]]
            self.recompute(save=False)
            return
        what = self.mode()
        self.view.setCursor(Qt.CrossCursor if what else Qt.ArrowCursor)
        if what == 'openings':
            self.hover = [n[0], n[1], self.M.cur_photo(self.d)]

    def photo_release(self):
        if self.drag:
            self.drag = None
            self.recompute()

    def right_click(self):
        if self.mode() == 'openings':
            self.finish_trace()

    def finish_trace(self):
        if len(self.trace) >= (3 if self.how == 'outline' else 2):
            self.d['openings'].append({'kind': self.kind, 'how': self.how, 'clicks': self.trace})
            self.trace = []
            self.recompute()
            return True
        return False

    def key(self, ev):
        """Keys on the photo. True if used."""
        k = ev.key()
        mod = ev.modifiers()
        what = self.mode()
        if k in (Qt.Key_Return, Qt.Key_Enter):
            if what == 'openings' and self.finish_trace():
                return True
            return True
        if k == Qt.Key_F11 or (k == Qt.Key_Escape and self.isFullScreen() and not (self.pending or self.trace)):
            self.b_full.setChecked(not self.b_full.isChecked())
            return True
        if k == Qt.Key_Escape:
            self.pending, self.trace = None, []
            self.view.update()
            return True
        if (k == Qt.Key_Y and mod & Qt.ControlModifier) or \
                (k == Qt.Key_Z and mod & Qt.ControlModifier and mod & Qt.ShiftModifier):
            self.redo()
            return True
        if k in (Qt.Key_Backspace, Qt.Key_Delete) or (k == Qt.Key_Z and mod & Qt.ControlModifier):
            self.undo_click()
            return True
        if what == 'openings' and not mod & (Qt.ControlModifier | Qt.AltModifier):
            if k == Qt.Key_W:
                self._set_kind('window')
            elif k == Qt.Key_D:
                self._set_kind('door')
            elif k in (Qt.Key_B, Qt.Key_H, Qt.Key_A, Qt.Key_C):
                self._set_how({Qt.Key_B: 'box', Qt.Key_H: 'trace', Qt.Key_A: 'outline', Qt.Key_C: 'copy'}[k])
            elif k == Qt.Key_T:
                ks = [t[0] for t in self.M.TOPS]
                self._set_top(ks[(ks.index(self.top) + 1) % len(ks)] if self.top in ks else ks[0])
            else:
                return False
            self.refresh()
            return True
        return False

    def _state(self):
        return (copy.deepcopy(self.d), copy.deepcopy(self.pending), list(self.trace), self.base_mode)

    def remember(self):
        """Keeps how things are before a change, so Ctrl+Z can go back to it."""
        self.history.append(self._state())
        del self.history[:-80]
        self.future = []

    def _put_back(self, st):
        self.d, self.pending, self.trace, self.base_mode = copy.deepcopy(st[0]), st[1], list(st[2]), st[3]
        if self.copy_src is not None and self.copy_src >= len(self.d.get('openings') or []):
            self.copy_src = None
        self.d['cur'] = min(int(self.d.get('cur') or 0), len(self.d['parts']) - 1)
        self.show_current_photo()
        self.recompute()

    def redo(self):
        if not getattr(self, 'future', None):
            self.say("Nothing to bring back.")
            return
        self.history.append(self._state())
        self._put_back(self.future.pop())

    def undo_click(self):
        if self.history:                                   # the very last change, whatever step it was on
            if not hasattr(self, 'future'):
                self.future = []
            self.future.append(self._state())
            self._put_back(self.history.pop())
            return
        d, what = self.d, self.mode()
        part = d['parts'][d['cur']]
        if what == 'corners' and part['corners']:
            part['corners'].pop()
        elif what == 'openings':
            if self.trace:
                self.trace.pop()
            elif self.pending:
                self.pending = None
            elif d['openings']:
                d['openings'].pop()
                if self.copy_src is not None and self.copy_src >= len(d['openings']):
                    self.copy_src = None
        elif what in ('eaves', 'ridge'):
            part[what] = None
        elif what == 'base':
            part['base'] = part['base_top'] = None
        elif what in ('link', 'wall4'):
            lst = d['photos'][self.M.cur_photo(d)].get('link' if what == 'link' else 'quad') or []
            if lst:
                lst.pop()
        elif what == 'gable':
            self.gable_off(one_click=True)
            return
        self.recompute()

    def opening_at(self, nu, nv, kph):
        """The window or door clicked inside (its number in the list), if any."""
        M, m, d = self.M, self.m or {}, self.d
        views = m.get('views') or []
        view = views[kph] if kph < len(views) else None
        if view is None:
            return None
        ph = M.photo_info(d, kph)
        u, v = nu * ph['W'], nv * ph['H']
        for o in m.get('openings') or []:
            pts = [M.view_project(view, P) for P in M.opening_outline(m, o)]
            if any(p_ is None for p_ in pts):
                continue
            inside = False
            for i in range(len(pts)):
                (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % len(pts)]
                if (y1 > v) != (y2 > v) and u < x1 + (v - y1) * (x2 - x1) / (y2 - y1):
                    inside = not inside
            if inside:
                return o.get('idx')
        return None

    def preview_opening(self):
        """The window or door being clicked, to where the mouse is now (drawn white)."""
        hv = self.hover
        if not hv:
            return None
        if self.how == 'box' and self.pending:
            return {'kind': self.kind, 'top': self.top, 'how': 'box', 'clicks': [self.pending['click'], hv]}
        if self.how in ('trace', 'outline') and self.trace:
            return {'kind': self.kind, 'how': self.how, 'clicks': self.trace + [hv]}
        if self.how == 'copy' and self.copy_src is not None:
            return {'how': 'copy', 'src': self.copy_src, 'clicks': [hv]}
        return None

    # ---- drawing over the photo ----
    def draw_overlay(self, p, view_w):
        from PySide6.QtGui import QColor, QPen, QFont
        M, d, m = self.M, self.d, self.m or {}
        kph = M.cur_photo(d)
        ph = M.photo_info(d, kph)
        W, H = ph.get('W') or d['W'], ph.get('H') or d['H']
        views = m.get('views') or []
        view = views[kph] if kph < len(views) else None
        cam = view.get('cam') if view else None
        n2s = view_w.n2s

        def px(u, v):
            return n2s(u / W, v / H)

        def w2s(P):
            q = M.view_project(view, P) if view is not None else None
            return px(*q) if q else None

        def seg(a, b):
            pa, pb = w2s(a), w2s(b)
            return (pa, pb) if pa is not None and pb is not None else None

        def col(name, alpha=255):
            c = MCOLS.get(name, MCOLS['wall'])
            return QColor(c[0], c[1], c[2], alpha)

        def lines(segs, c, width):
            p.setPen(QPen(c, width))
            for a, b in segs:
                p.drawLine(a, b)

        def dot(q, c, r=5.0):
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawEllipse(q, r, r)
            p.setBrush(Qt.NoBrush)

        def text(q, s, c, size=11, bold=True):
            f = QFont(p.font())
            f.setPointSizeF(size)
            f.setBold(bold)
            p.setFont(f)
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(QPointF(q.x() + 1.5, q.y() + 1.5), s)
            p.setPen(c)
            p.drawText(q, s)

        def mine(c):
            return M.ck(c) == kph
        mode = self.mode()
        # the ground grid: flat on the ground if the lines are right
        if cam and mode in ('lines', 'corners', None):
            g, span = [], 12.0
            ol = m.get('outline') or m.get('raw')
            ox, oy = (ol[0][0], ol[0][1]) if ol else (0.0, 0.0)
            if not ol:
                c = M.hit_ground(cam, W / 2.0, H * 0.25)
                if c:
                    ox, oy = c[0], c[1]
            k = -span
            while k <= span + 1e-9:
                for a, b in (((ox + k, oy - span, 0.0), (ox + k, oy + span, 0.0)),
                             ((ox - span, oy + k, 0.0), (ox + span, oy + k, 0.0))):
                    s = seg(a, b)
                    if s:
                        g.append(s)
                k += 1.0
            lines(g, col('grid', 115), 1.0)
        # the building so far
        if view is not None:
            by = {}
            for a, b, kind, pi in M.building_lines(m, d):
                s = seg(a, b)
                if s:
                    by.setdefault((kind, pi == d['cur'] or kind in ('window', 'door')), []).append(s)
            for (kind, here), segs in by.items():
                lines(segs, col(kind, 255 if here else 115), (2.0 if kind != 'ground' else 2.5) if here else 1.5)
            pv = self.preview_opening() if mode == 'openings' and m.get('outline') else None
            if pv:
                dd = dict(d)
                dd['openings'] = list(d['openings']) + [pv]
                try:
                    mm = M.compute(dd)
                    last = [o for o in mm['openings'] if o.get('idx') == len(d['openings'])]
                    if last:
                        lines([s for s in (seg(a, b) for a, b in M.opening_lines(mm, last[0])) if s],
                              QColor(255, 255, 255, 230), 1.5)
                except Exception:
                    pass
            if mode == 'openings' and self.copy_src is not None:
                got = [o for o in m.get('openings') or [] if o.get('idx') == self.copy_src]
                if got:
                    lines([s for s in (seg(a, b) for a, b in M.opening_lines(m, got[0])) if s],
                          QColor(255, 255, 255), 3.0)
            part = d['parts'][d['cur']]
            for i, c in enumerate(part.get('corners') or []):
                if mine(c):
                    q = n2s(c[0], c[1])
                    dot(q, QColor(255, 217, 26))
                    text(QPointF(q.x() + 8, q.y() - 6), str(i + 1), QColor(255, 230, 50), 13)
            if len(d['parts']) > 1:
                for pi, pm in enumerate(m.get('parts') or []):
                    ol = pm.get('outline')
                    if ol:
                        q = w2s(M.v_mul(M.v_add(ol[0], ol[1]), 0.5))
                        if q is not None:
                            text(QPointF(q.x() - 20, q.y() + 20), M.part_label(pi, d['parts'][pi]),
                                 QColor(255, 230, 50, 255 if pi == d['cur'] else 150), 11)
            if cam and part.get('click_at') in ('up', 'up_main') and mode in ('corners', 'base') and \
                    len(cam.get('vp') or []) == 2:            # the camera's eye level: no use for level lines
                (a1, b1), (a2, b2) = cam['vp']
                if abs(a2 - a1) > 1e-6:
                    sl = (b2 - b1) / (a2 - a1)
                    pa, pb = px(-W, b1 + sl * (-W - a1)), px(2 * W, b1 + sl * (2 * W - a1))
                    p.setPen(QPen(QColor(255, 255, 255, 200), 1.5, Qt.DashDotLine))
                    p.drawLine(pa, pb)
                    q_ = px(W * 0.02, b1 + sl * (W * 0.02 - a1))
                    text(QPointF(q_.x(), q_.y() - 6), "eye level - don't use a line here", QColor(255, 255, 255), 11)
            if cam and part.get('click_at') == 'up' and mode in ('corners', 'base'):
                q = M.to_cam(cam, (0.0, 0.0, 1.0))         # straight up, as the photo sees it
                for c in ([part['base_top']] if part.get('base_top') else []) + list(part.get('corners') or []):
                    if not mine(c):
                        continue
                    u0, v0 = c[0] * W, c[1] * H
                    if abs(q[2]) < 1e-9:
                        du, dv = -q[0], -q[1]
                    else:
                        vu, vv = W / 2.0 + cam['f'] * q[0] / -q[2], H / 2.0 + cam['f'] * q[1] / -q[2]
                        du, dv = (vu - u0, vv - v0) if vv < v0 else (u0 - vu, v0 - vv)
                    L = math.hypot(du, dv) or 1.0
                    end = px(u0 + du / L * 3.0 * (W + H), v0 + dv / L * 3.0 * (W + H))
                    p.setPen(QPen(QColor(255, 115, 230, 230), 1.5, Qt.DashLine))
                    p.drawLine(px(u0, v0), end)
            pms_ = m.get('parts') or []
            la = pms_[d['cur']].get('level_at') if d['cur'] < len(pms_) else None
            if la and mine(la) and part.get('base') and mine(part['base']):
                qa, qb = n2s(la[0], la[1]), n2s(part['base'][0], part['base'][1])
                p.setPen(QPen(QColor(255, 115, 230, 230), 1.5, Qt.DashLine))
                p.drawLine(qa, qb)
                dot(qa, QColor(255, 115, 230))
                text(QPointF(qa.x() + 8, qa.y() - 6), "your line here", QColor(255, 150, 240), 11)
            for key, lab in (('base_top', "on the line"), ('base', "foot of the wall"), ('eaves', "eaves"),
                             ('ridge', "roof top")):
                if part.get(key) and mine(part[key]):
                    q = n2s(part[key][0], part[key][1])
                    dot(q, QColor(255, 115, 230))
                    text(QPointF(q.x() + 8, q.y() - 6), lab, QColor(255, 150, 240), 11)
            count = {'window': 0, 'door': 0}
            for o in m.get('openings') or []:
                kind = 'door' if o['kind'] == 'door' else 'window'
                count[kind] += 1                           # windows and doors each numbered from 1
                ol = m['parts'][o['part']]['outline']
                a, b = ol[o['wall']], ol[(o['wall'] + 1) % len(ol)]
                u = M.v_norm(M.v_sub(b, a))
                q = w2s(M.v_add(a, M.v_add(M.v_mul(u, (o['s0'] + o['s1']) / 2.0), (0.0, 0.0, o['z1']))))
                if q is not None:
                    text(QPointF(q.x() - 6, q.y() - 6), ("D" if kind == 'door' else "W") + str(count[kind]),
                         col(kind), 10)
        if mode == 'openings' and self.pending:
            c = self.pending['click']
            dot(n2s(c[0], c[1]), QColor(255, 255, 255), 4)
        if mode == 'gable' and d.get('gables') and len(d['gables'][-1].get('clicks') or []) < 3:
            for c in d['gables'][-1]['clicks']:
                if mine(c):
                    dot(n2s(c[0], c[1]), QColor(255, 150, 240))
        if mode == 'openings' and self.trace:
            for c in self.trace:
                dot(n2s(c[0], c[1]), QColor(255, 255, 255), 4)
        if kph > 0:                                        # tying a photo in, and a wall's 4 corners
            for l_ in ph.get('link') or []:
                if l_.get('c'):
                    q = n2s(*l_['c'][:2])
                    dot(q, QColor(77, 255, 255), 6)
                    text(QPointF(q.x() + 8, q.y() - 6), "corner %d" % (int(l_['corner']) + 1), QColor(100, 255, 255), 12)
            quad = ph.get('quad') or []
            for i, q_ in enumerate(quad):
                q = n2s(q_[0], q_[1])
                dot(q, QColor(77, 255, 255), 6)
                text(QPointF(q.x() + 8, q.y() - 6), ("bottom left", "bottom right", "top right", "top left")[i % 4],
                     QColor(100, 255, 255), 11)
            if len(quad) >= 2:
                pts = [n2s(q_[0], q_[1]) for q_ in quad[:4]]
                lines([(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))], QColor(77, 255, 255, 200), 2.0)
        # the four lines, long and faint, with dots to drag
        if ph.get('kind') == 'corner':
            ls = M.cur_lines(d)
            show = mode == 'lines' or (kph == 0 and not cam) or (kph > 0 and not M.lines_done(d, kph))
            for key in (M.LINE_KEYS if show else ()):
                c = col(key[0])
                a, b = n2s(*ls[key][0][:2]), n2s(*ls[key][1][:2])
                dx, dy = b.x() - a.x(), b.y() - a.y()
                L = math.hypot(dx, dy) or 1.0
                ext = 6000.0 / L
                lines([(QPointF(a.x() - dx * ext, a.y() - dy * ext), QPointF(b.x() + dx * ext, b.y() + dy * ext))],
                      QColor(c.red(), c.green(), c.blue(), 90), 1.0)
                lines([(a, b)], c, 3.0)
                for q in (a, b):
                    dot(q, c, 7)
                    dot(q, QColor(0, 0, 0), 2)
                if self.drag and self.drag[0] == key:
                    dot(a if self.drag[1] == 0 else b, QColor(255, 255, 255), 3)

    # ---- the panel ----
    def refresh(self):
        M, d, m = self.M, self.d, self.m or {}
        self.busy = True
        try:
            cur = int(d.get('step') or 1)
            kph = M.cur_photo(d)
            ph = M.photo_info(d, kph)
            part = d['parts'][d['cur']]
            pms = m.get('parts') or []
            pm = pms[d['cur']] if d['cur'] < len(pms) else {}
            copy_ = part.get('copy_of') is not None
            against = d['cur'] > 0 and bool(part.get('against'))
            for n_, b in zip(range(1, 8), self.step_btns):
                b.setChecked(n_ == cur)
                done = n_ > 1 and self.step_done(n_)
                b.setText(("%d ✓" % n_) if done else str(n_))
            nm = os.path.basename(ph.get('path') or '') or "photo"
            self.lbl_photo.setText("Photo %d of %d: %s%s" % (kph + 1, len(d['photos']), nm[:34],
                                                            "  (straight on)" if ph.get('kind') == 'wall' else ""))
            self.b_rmph.setEnabled(kph > 0)
            self.lbl_step.setText("Step %d of 7:  %s" % (cur, dict(MSTEPS)[cur]))
            self.part_row.setVisible(cur in PART_STEPS)
            self.lbl_part.setText("Part %d of %d:  <b>%s</b>%s" % (
                d['cur'] + 1, len(d['parts']), M.part_label(d['cur'], part),
                "  ✓" if self.part_done(cur, part, pm) else ""))
            self.b_pclone.setVisible(d['cur'] > 0)
            self.b_premove.setVisible(d['cur'] > 0)
            if cur == 3 and copy_:
                how = MHOWTO['copy']
            elif cur in (4, 5) and (copy_ or part.get('same_as') is not None):
                how = MHOWTO['same']
            elif cur == 2 and kph > 0:
                how = MHOWTO['wall' if ph.get('kind') == 'wall' else 'tie']
            elif cur == 3 and against:
                how = MHOWTO['bay']
            elif cur == 3 and part.get('click_at') in ('up', 'up_main'):
                how = MHOWTO['up' if part.get('click_at') == 'up' else 'up_main']
            elif cur == 3 and part.get('shape') == 'own':
                how = MHOWTO['own']
            else:
                how = MHOWTO[cur]
            short = how
            for key, txt in MHOWTO.items():
                if txt == how:
                    short = MSHORT.get(key, how)
                    break
            self.lbl_how.setText(short)
            self.lbl_how.setToolTip(how)
            self.stack.setCurrentIndex(cur - 1)
            # 1
            nw = sum(1 for p_ in d['parts'][1:] if not p_.get('against'))
            nb = sum(1 for p_ in d['parts'][1:] if p_.get('against'))
            self.lbl_wings.setText("Wings:  %d" % nw)
            self.lbl_bays.setText("Bays / porches:  %d" % nb)
            row = self.lst_parts.currentRow()
            self.lst_parts.clear()
            for i, p_ in enumerate(d['parts']):
                pmi = pms[i] if i < len(pms) else {}
                ok = pmi.get('outline') is not None and bool(pmi.get('eaves'))
                kind = "main" if i == 0 else ("bay" if p_.get('against') else "wing")
                self.lst_parts.addItem("%s %s  (%s)%s" % ("✓" if ok else "○", M.part_label(i, p_), kind,
                                                           "  - copy" if p_.get('copy_of') is not None else ""))
            self.lst_parts.setCurrentRow(min(max(row, 0), len(d['parts']) - 1))
            # 2
            self.tie_box.setVisible(kph > 0 and ph.get('kind') == 'corner')
            self.wall_box.setVisible(kph > 0 and ph.get('kind') == 'wall')
            if kph > 0 and ph.get('kind') == 'corner':
                (self.rb_tie_lines if self.tie_mode == 'lines' else self.rb_tie_link).setChecked(True)
                ol = m.get('outline')
                n = len(ol) if ol else 4
                lc = ph.get('link_corners') or [0, 1]
                for cb, i in ((self.cb_link_a, 0), (self.cb_link_b, 1)):
                    cb.clear()
                    for c_ in range(n):
                        cb.addItem("Main building corner %d" % (c_ + 1))
                    cb.setCurrentIndex(min(int(lc[i]), n - 1))
            if kph > 0 and ph.get('kind') == 'wall':
                self.cb_wpart.clear()
                for i, p_ in enumerate(d['parts']):
                    self.cb_wpart.addItem(M.part_label(i, p_))
                pi_ = min(int(ph.get('part') or 0), len(d['parts']) - 1)
                self.cb_wpart.setCurrentIndex(pi_)
                ol = pms[pi_].get('outline') if pi_ < len(pms) else None
                self.cb_wwall.clear()
                for w_ in range(len(ol) if ol else 4):
                    self.cb_wwall.addItem("Wall %d (w%d on the plan)" % (w_ + 1, w_ + 1))
                self.cb_wwall.setCurrentIndex(min(int(ph.get('wall') or 0), self.cb_wwall.count() - 1))
            if cur == 2:
                if kph == 0:
                    st_ = ("Lined up: a %.0f mm lens." % m['cam']['lens35']) if (
                        m.get('cam') and d.get('lines') != M.start_lines()) else "Not lined up yet."
                else:
                    pp_ = (m.get('photo_problems') or {}).get(kph)
                    st_ = ("Still to do: " + pp_) if pp_ else "This photo's set up ✓"
                self.lbl_photo_state.setText(st_)
            # 3
            self.cb_shape.setCurrentIndex(0 if part.get('shape', 'rect') == 'rect' else 1)
            self.cb_shape.setEnabled(not against and not copy_)
            self.ed_pname.setText(part.get('name') or "")
            self.ed_pname.setEnabled(d['cur'] > 0)
            self.ck_against.setChecked(bool(part.get('against')))
            self.ck_against.setEnabled(d['cur'] > 0 and not copy_)
            self.sp_maplen.setValue(float(part.get('map_len') or 0.0))
            self.sp_maplen.setEnabled(d['cur'] > 0 and part.get('shape', 'rect') == 'rect' and not against)
            self.sp_depth.setValue(float(part.get('depth_mm') or 0.0))
            self.sp_depth.setEnabled(part.get('shape', 'rect') == 'rect' and not against and not copy_)
            sub = d['cur'] > 0
            self.cb_clickat.clear()
            for lab, key in (("On the ground", 'ground'), ("Up the wall - all at one height", 'up'),
                             ("Up the wall - the main building's height", 'up_main')):
                if key != 'up_main' or sub:
                    self.cb_clickat.addItem(lab, key)
            self.cb_clickat.setCurrentIndex(max(self.cb_clickat.findData(part.get('click_at', 'ground')), 0))
            self.cb_clickat.setEnabled(not copy_)
            up = part.get('click_at') == 'up'
            self.b_base.setVisible(up and not copy_)
            self.b_base.setChecked(self.base_mode)
            self.b_base.setText("Set the height: click the foot of the front wall%s" % (
                "  ✓" if part.get('base') else ""))
            self.b_plan_put.setVisible(sub)
            self.b_plan_put.setEnabled(sub and not pm.get('outline') and bool(m.get('outline')))
            self.b_plan_mirror.setVisible(sub)
            self.b_plan_mirror.setEnabled(sub and bool(pm.get('outline')))
            self.b_plan_reset.setVisible(sub and bool(part.get('plan')))
            # 4, 5
            same = part.get('same_as') is not None
            for w_ in (self.lbl_typed4, self.sp_eaves_mm, self.lbl_typed5, self.sp_ridge_mm):
                w_.setVisible(sub and not copy_ and not same)
            self.sp_eaves_mm.setValue(float(part.get('eaves_mm') or 0.0))
            self.sp_ridge_mm.setValue(float(part.get('ridge_mm') or 0.0))
            self.sp_storeys.setValue(int(part.get('storeys') or 1))
            self.sp_storeys.setEnabled(not copy_)
            i_ = self.cb_roof.findData(part.get('roof', 'gable_len'))
            self.cb_roof.setCurrentIndex(max(i_, 0))
            self.cb_roof.setEnabled(not copy_)
            self.cb_low.setCurrentIndex(0 if part.get('roof_low', 'front') == 'front' else 1)
            self.cb_low.setEnabled(part.get('roof') == 'mono' and not copy_)
            self.lbl_gables.setText("Pointed gables on the roof: %d" % len(m.get('gables') or []))
            self.ck_gables.setChecked(self.gable_mode)
            # 6
            (self.rb_door if self.kind == 'door' else self.rb_win).setChecked(True)
            self.how_btns[self.how].setChecked(True)
            self.cb_top.setCurrentIndex(max(self.cb_top.findData(self.top), 0))
            self.cb_top.setEnabled(self.how == 'box')
            ops = m.get('openings') or []
            nwin = sum(1 for o in ops if o['kind'] != 'door')
            self.lbl_ops.setText("%d window%s, %d door%s" % (nwin, "" if nwin == 1 else "s", len(ops) - nwin,
                                                            "" if len(ops) - nwin == 1 else "s"))
            # 7
            self.cb_known.setCurrentIndex(max(self.cb_known.findData(d.get('known_what', 'door_h')), 0))
            self.sp_known.setValue(float(d.get('known_mm') or 2000.0))
            sizes = M.sizes_text(m, d) if m.get('parts') else []
            if not m.get('k'):
                sizes = ["The known size isn't clicked yet - click it, or pick another size you know."] + sizes
            self.lbl_sizes.setText("<br>".join(sizes))
            # problems, back / next
            probs = list((m.get('problems') or [])[:1])
            if self.note:
                probs.insert(0, self.note)
            if cur == 3 and pm.get('rough'):
                probs.append("The depth is rough until the size you know (step 7) can be measured.")
            self.lbl_problem.setText("<br>".join(probs))
            self.b_restart.setVisible(cur > 1)
            self.b_undo_click.setEnabled(bool(self.history))
            self.b_redo.setEnabled(bool(getattr(self, 'future', None)))
            self.b_back.setEnabled(cur > 1 or d['cur'] > 0)
            if cur < 7:
                nxt = "Next  ▶"
                if cur in PART_STEPS and d['cur'] < len(d['parts']) - 1:
                    nxt = "Next: %s  ▶" % M.part_label(d['cur'] + 1, d['parts'][d['cur'] + 1])
                self.b_fwd.setText(nxt)
                self.b_fwd.setVisible(True)
            else:
                self.b_fwd.setVisible(False)
            # over the photo: what clicking does now
            what = self.mode()
            top = PHOTO_HELP.get(what, "")
            if what == 'corners' and part.get('click_at') in ('up', 'up_main'):
                top = "CORNERS ON THE LEVEL LINE UP THE WALL"
            if what in ('corners', 'eaves', 'ridge') and len(d['parts']) > 1:
                top += "   -   " + M.part_label(d['cur'], part).upper()
            if what == 'openings':
                w_ = "DOORS" if self.kind == 'door' else "WINDOWS"
                if self.how == 'box':
                    w_ += " - " + {t[0]: t[1] for t in M.TOPS}[self.top].lower()
                top += "   -   %s, %s<br><span style='font-weight:normal'>%s<br>%s</span>" % (
                    w_, {'box': "box", 'trace': "half", 'outline': "all round", 'copy': "copy"}[self.how],
                    " ".join(M.HOW_HELP[self.how]), MKEYS)
            pp = (m.get('photo_problems') or {}).get(kph)
            if pp and kph > 0:
                top += "<br><span style='color:#b00'>This photo: %s</span>" % pp
            self.lbl_top.setText("<b>%s</b>" % top if top else "")
        finally:
            self.busy = False
        self.view.update()
        self.plan.update()
        self.diag.update()

    def diagram(self):
        """How to click this step, as a drawing: the dot to click next lit up."""
        d = self.d
        cur = int(d.get('step') or 1)
        part = d['parts'][d['cur']]
        kph = self.M.cur_photo(d)
        out = []
        if cur == 1:
            out.append(('line', [(25, 15), (65, 15), (65, 45), (25, 45), (25, 15)], 'yellow', 2))
            out.append(('text', (30, 30), "main", 'yellow'))
            out.append(('line', [(65, 20), (88, 20), (88, 40), (65, 40)], 'pink', 2))
            out.append(('text', (68, 30), "wing", 'pink'))
            out.append(('line', [(32, 15), (32, 6), (48, 6), (48, 15)], 'cyan', 2))
            out.append(('text', (50, 6), "bay", 'cyan'))
            out.append(('text', (2, 64), "looking down", 'faint'))
            return out
        if cur == 2 and kph > 0 and self.M.photo_info(d, kph).get('kind') == 'wall':
            out += _house_front(roof=False)
            q = len(d['photos'][kph].get('quad') or [])
            for i, (pt, lab) in enumerate((((15, 5), "1"), ((85, 5), "2"), ((85, 40), "3"), ((15, 40), "4"))):
                out.append(('dot', pt, lab, 'cyan', i == q))
            return out
        out += _corner_house()
        if cur == 2:
            out += [('line', [_At, _Bt], 'red', 3), ('line', [_A, _B], 'red', 3),
                    ('line', [_Bt, _Ct], 'lime', 3), ('line', [_B, _C], 'lime', 3)]
            for pt in (_A, _B, _At, _Bt):
                out.append(('dot', pt, "", 'red', False))
            for pt in (_B, _C, _Bt, _Ct):
                out.append(('dot', pt, "", 'lime', False))
            out.append(('text', (2, 66), "drag the line ends onto the edges", 'faint'))
        elif cur == 3:
            n_ = len(part.get('corners') or [])
            up = part.get('click_at') in ('up', 'up_main')
            pts = (_At, _Bt, _Ct) if up else (_A, _B, _C)
            for i, pt in enumerate(pts):
                out.append(('dot', pt, str(i + 1), 'yellow', i == n_))
            if part.get('click_at') == 'up':
                foot = _mid(_A, _B, 0.45)
                out.append(('line', [foot, _mid(_At, _Bt, 0.45)], 'pink', 1.5, True))
                out.append(('dot', foot, "foot", 'pink', n_ >= 3 and not part.get('base')))
                out.append(('text', (2, 66), "corners on a level line up the wall", 'faint'))
            else:
                out.append(('text', (2, 66), "corners where the walls meet the ground", 'faint'))
        elif cur == 4:
            out.append(('dot', _Bt, "top of a corner", 'pink', not part.get('eaves')))
        elif cur == 5:
            if self.gable_mode:
                g = [_mid(_At, _Bt, 0.3), _mid(_At, _Bt, 0.7)]
                pk = _mid(g[0], g[1])
                pk = (pk[0], pk[1] + 12)
                out.append(('line', [g[0], pk, g[1]], 'red', 2))
                gl = d.get('gables') or []
                n_ = len(gl[-1]['clicks']) if gl and len(gl[-1].get('clicks') or []) < 3 else 0
                for i, (pt, lab) in enumerate(((g[0], "1"), (g[1], "2"), (pk, "3 peak"))):
                    out.append(('dot', pt, lab, 'red', i == n_))
            else:
                out.append(('dot', (50, 61.5), "roof top", 'pink', not part.get('ridge')))
        elif cur == 6:
            a = _mid(_A, _B, 0.25)
            a = (a[0], a[1] + 10)
            b = (a[0] + 10, a[1] + 12)
            c = 'orange' if self.kind == 'door' else 'blue'
            out.append(('line', [a, (b[0], a[1] - 2), b, (a[0], b[1] + 2), a], c, 2.5))
            out.append(('dot', a, "1", c, self.pending is None))
            out.append(('dot', b, "2", c, self.pending is not None))
        else:
            out.append(('line', [(30, 4), (30, 26)], 'green', 2.5))
            out.append(('text', (32, 15), "a size you know", 'green'))
        return out

    def step_done(self, n):
        M, d, m = self.M, self.d, self.m or {}
        pms = m.get('parts') or []
        if n == 2:
            return bool(m.get('cam')) and d.get('lines') != M.start_lines()
        if n == 3:
            return bool(pms) and all(p_.get('outline') for p_ in pms)
        if n == 4:
            return bool(pms) and all(p_.get('eaves') for p_ in pms)
        if n == 5:
            return bool(pms) and all(p_.get('ridge') or d['parts'][i].get('roof') in ('flat', 'none')
                                     for i, p_ in enumerate(pms))
        if n == 6:
            return bool(m.get('openings'))
        if n == 7:
            return bool(m.get('k'))
        return False

    @staticmethod
    def part_done(n, part, pm):
        if n == 3:
            return pm.get('outline') is not None
        if n == 4:
            return bool(pm.get('eaves'))
        if n == 5:
            return bool(pm.get('ridge')) or part.get('roof') in ('flat', 'none')
        return False

    def say(self, text, bad=False):
        self.note = text if bad else ""
        self.lbl_problem.setText(text)
        self.lbl_problem.setStyleSheet("color: #b00;" if bad else "color: #050;")

    # ---- panel changes ----
    def _part_set(self, key, value):
        if self.busy:
            return
        d = self.d
        part = d['parts'][d['cur']]
        if key == 'name' and not value:
            return
        if key == 'against' and d['cur'] == 0:
            return
        if part.get(key) == value:
            return
        self.remember()
        part[key] = value
        self.recompute()

    def _known(self):
        if self.busy:
            return
        self.remember()
        self.d['known_what'] = self.cb_known.currentData()
        self.d['known_mm'] = float(self.sp_known.value())
        self.recompute()

    def _set_kind(self, kind):
        self.kind = kind
        if self.pending:
            self.pending['kind'] = kind
        if not self.busy:
            self.refresh()

    def _set_how(self, how):
        self.how = how
        self.pending, self.trace = None, []
        if not self.busy:
            self.refresh()

    def _set_top(self, top):
        if top:
            self.top = top
        if not self.busy:
            self.refresh()

    def _base_mode(self, on):
        if self.busy:
            return
        self.base_mode = bool(on)
        if on:                                             # each time: from the first click (on the line)
            part = self.d['parts'][self.d['cur']]
            part['base_top'] = part['base'] = None
            self.recompute()
            return
        self.refresh()

    def _gable_mode(self, on):
        if self.busy:
            return
        self.gable_mode = bool(on)
        self.refresh()

    def gable_off(self, one_click=False):
        gl = self.d.get('gables') or []
        if gl:
            self.remember()
        if gl:
            if one_click:
                cl = gl[-1].get('clicks') or []
                if cl:
                    cl.pop()
                if not cl:
                    gl.pop()
            else:
                gl.pop()
        self.recompute()

    def opening_off(self):
        self.remember()
        self.trace, self.pending = [], None
        if self.d['openings']:
            self.d['openings'].pop()
            if self.copy_src is not None and self.copy_src >= len(self.d['openings']):
                self.copy_src = None
        self.recompute()

    def _tie_mode(self, i):
        if self.busy:
            return
        self.tie_mode = 'link' if i == 1 else 'lines'
        self.refresh()

    def _link_corner(self, which, i):
        if self.busy or i < 0:
            return
        ph = self.d['photos'][self.M.cur_photo(self.d)]
        lc = ph.setdefault('link_corners', [0, 1])
        lc[which] = int(i)
        ph['link'] = []
        self.tie_mode = 'link'
        self.recompute()

    def _wall_part(self, i):
        if self.busy or i < 0:
            return
        ph = self.d['photos'][self.M.cur_photo(self.d)]
        ph['part'], ph['wall'], ph['quad'] = int(i), 0, []
        self.d['cur'] = int(i)                              # its walls are numbered on the plan
        self.recompute()

    def _wall_wall(self, i):
        if self.busy or i < 0:
            return
        ph = self.d['photos'][self.M.cur_photo(self.d)]
        ph['wall'], ph['quad'] = int(i), []
        self.recompute()

    def _list_pick(self, i):
        if self.busy or i < 0:
            return
        self.d['cur'] = min(i, len(self.d['parts']) - 1)
        self.refresh()

    def _clear_transient(self):
        self.pending, self.trace, self.drag = None, [], None
        self.gable_mode = False
        self.base_mode = False
        self.note = ""

    def goto(self, n):
        self.d['step'] = min(max(1, int(n)), 7)
        self.d['cur'] = 0                                   # each step starts at the main building
        self._clear_transient()
        self.recompute()

    def walk(self, back):
        d = self.d
        n = int(d.get('step') or 1)
        self._clear_transient()
        if n in PART_STEPS:
            k = d['cur'] + (-1 if back else 1)
            if 0 <= k < len(d['parts']):
                d['cur'] = k
                self.recompute()
                return
        n = min(max(1, n + (-1 if back else 1)), 7)
        d['step'] = n
        d['cur'] = (len(d['parts']) - 1) if (back and n in PART_STEPS) else 0
        self.recompute()

    def restart_step(self):
        d = self.d
        n = int(d.get('step') or 1)
        if QMessageBox.question(self, PLUGIN_NAME, "Take off everything clicked in step %d (for every part), to "
                                                   "start it again? (Ctrl+Z brings it back.)" % n) != \
                QMessageBox.StandardButton.Yes:
            return
        self.remember()
        if n == 2:
            k_ = self.M.cur_photo(d)
            if k_ == 0:
                d['lines'] = self.M.start_lines()
            else:
                d['photos'][k_].update(lines=self.M.start_lines(), link=[], quad=[])
                self.tie_mode = 'lines'
        elif n in (3, 4, 5):
            key = {3: 'corners', 4: 'eaves', 5: 'ridge'}[n]
            for p_ in d['parts']:
                p_[key] = [] if key == 'corners' else None
            if n == 5:
                d['gables'] = []
        elif n == 6:
            d['openings'] = []
            self.copy_src = None
        d['cur'] = 0
        self._clear_transient()
        self.recompute()

    def part_action(self, action, index=-1):
        M, d = self.M, self.d
        i = d['cur'] if index is None or index < 0 else index
        self.remember()

        def fresh_name(kind):
            used = set(p_.get('name') for p_ in d['parts'])
            n = 1
            while "%s %d" % (kind, n) in used:
                n += 1
            return "%s %d" % (kind, n)
        if action in ('add', 'add_against'):
            against = action == 'add_against'
            d['parts'].append(M.new_part(fresh_name("Bay" if against else "Wing"), against))
            if int(d.get('step') or 1) in PART_STEPS:
                d['cur'] = len(d['parts']) - 1
        elif action in ('less', 'less_against'):           # one fewer wing / bay: the last one goes
            against = action == 'less_against'
            ks = [k for k, p_ in enumerate(d['parts']) if k and bool(p_.get('against')) == against]
            if ks:
                self._remove_part(ks[-1])
        elif action == 'clone' and i > 0:
            src = d['parts'][i]
            against = bool(src.get('against'))
            c = M.new_part(fresh_name("Bay" if against else "Wing"), against)
            for key in M.PART_KEYS:
                c[key] = src.get(key, c.get(key))
            c['copy_of'] = i if src.get('copy_of') is None else src['copy_of']
            d['parts'].append(c)
            d['cur'] = len(d['parts']) - 1
            d['step'] = 3                                  # click where the copy goes (the steps say how)
        elif action == 'remove' and i > 0:
            if QMessageBox.question(self, PLUGIN_NAME, "Take %s off?" % M.part_label(i, d['parts'][i])) != \
                    QMessageBox.StandardButton.Yes:
                return
            self._remove_part(i)
        else:
            return
        self.recompute()

    def _remove_part(self, i):
        d = self.d
        if i <= 0 or i >= len(d['parts']):
            return
        d['parts'].pop(i)
        for p_ in d['parts']:                              # copies of it become parts of their own
            c = p_.get('copy_of')
            if c is not None:
                if c == i:
                    p_['copy_of'] = None
                    p_['corners'] = []
                elif c > i:
                    p_['copy_of'] = c - 1
            c = p_.get('same_as')
            if c is not None:
                if c == i:
                    p_['same_as'] = None
                elif c > i:
                    p_['same_as'] = c - 1
        d['cur'] = min(d['cur'], len(d['parts']) - 1)

    # ---- parts put on the plan by hand ----
    def _main_plan(self):
        M, m = self.M, self.m or {}
        if not m.get('outline'):
            return None, None
        fr = M.plan_frame(m['outline'])
        return fr, [M.to_plan(fr, q) for q in m['outline']]

    def plan_put(self):
        """A box beside the main building on the plan, for a part that can't be clicked on the photos."""
        fr, main = self._main_plan()
        d = self.d
        if main is None or d['cur'] == 0:
            self.say("The main building's corners come first.", True)
            return
        x0, x1 = min(q[0] for q in main), max(q[0] for q in main)
        y0, y1 = min(q[1] for q in main), max(q[1] for q in main)
        L, D = x1 - x0, y1 - y0
        part = d['parts'][d['cur']]
        self.remember()
        if part.get('against'):                            # a bay: on the front, against the wall
            xa, xb, ya, yb = x0 + 0.35 * L, x0 + 0.65 * L, y0 - 0.25 * D, y0
        else:                                              # a wing: off the right-hand end
            xa, xb, ya, yb = x1, x1 + 0.35 * L, y0 + 0.15 * D, y0 + 0.75 * D
        part['plan'] = [[xa, ya], [xb, ya], [xb, yb], [xa, yb]]
        part['copy_of'] = None
        self.recompute()
        self.say("It's on the plan - drag it into place (the photo shows where it is as you go).")

    def plan_mirror(self):
        """A mirror copy of this part on the other end of the main building, the same height and roof."""
        M, d, m = self.M, self.d, self.m or {}
        i = d['cur']
        pms = m.get('parts') or []
        fr, main = self._main_plan()
        if i == 0 or main is None or i >= len(pms) or not pms[i].get('outline'):
            return
        xs = [q[0] for q in main]
        mid = (min(xs) + max(xs)) / 2.0
        cs = [M.to_plan(fr, q) for q in pms[i]['outline']]
        n = len(cs)
        src = d['parts'][i]
        used = set(p_.get('name') for p_ in d['parts'])
        kind = "Bay" if src.get('against') else "Wing"
        k_ = 1
        while "%s %d" % (kind, k_) in used:
            k_ += 1
        c = M.new_part("%s %d" % (kind, k_), bool(src.get('against')))
        for key in M.PART_KEYS:
            c[key] = src.get(key, c.get(key))
        self.remember()
        c['plan'] = [[round(2.0 * mid - cs[(1 - j) % n][0], 4), round(cs[(1 - j) % n][1], 4)] for j in range(n)]
        c['same_as'] = src['same_as'] if src.get('same_as') is not None else i
        c['copy_of'] = None
        d['parts'].append(c)
        d['cur'] = len(d['parts']) - 1
        self.recompute()
        self.say("%s made on the other end, the same height and roof - drag it to fit if the ends aren't the "
                 "same." % c['name'])

    def plan_reset(self):
        self.remember()
        part = self.d['parts'][self.d['cur']]
        part.pop('plan', None)
        self.recompute()

    # ---- sending it to the Build page ----
    def send(self):
        M = self.M
        self.recompute(save=False)
        try:
            res = M.result(self.m, self.d)
        except ValueError as e:
            self.say(str(e), True)
            return
        res['photo'] = self.d['photos'][0].get('path', '')
        res['clicks'] = self.d
        res['clicked_in'] = "IngeTrazo"
        path = os.path.join(self.folder, RESULT_NAME)
        try:
            tmp = path + ".part"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=1)
            os.replace(tmp, path)
        except Exception as e:
            self.say("Couldn't save it: %s" % e, True)
            return
        self.save_clicks()
        try:
            self.main.job_folder = self.folder
            save_settings(last_job=self.folder)
            self.main.take_result(path)
            self.main._seen = os.path.getmtime(path)
            self.main.refresh_buttons()
            self.main.raise_()
            self.main.activateWindow()
        except Exception as e:
            print("%s: back to the window: %s" % (PLUGIN_NAME, e))
        self.close()


# ---------------------------------------------------------------------------
# Start from the front: a face-on photo of the front does the widths, heights, windows, doors, bays and wings in
# one go; the depth comes from the corner photo (as clicked the other way), a side face-on photo or a map.
# (version 4.2)
# ---------------------------------------------------------------------------
FRONT_NAME = "front.json"
FSTEPS = [(1, "The front"), (2, "The roof"), (3, "Bays and wings"), (4, "Windows and doors"), (5, "Depth"),
          (6, "Check and send")]
FORDER = (1, 2, 4, 3, 5, 6)          # step n shows page FORDER[n - 1] (pages: 3 windows and doors, 4 bays and wings)
FHOWTO = {
    1: "Pick the photo straight on to the front. Click the main building's front wall: bottom left, bottom right "
       "(where it meets the ground), top right, top left (just under the fascia). Then type its length (a map is "
       "best), or click the two ends of something you know the size of - a door's height - and type its size.",
    2: "Pick the roof's shape. Click the very top of the roof. Pointed gables on the front: tick Click gables, then "
       "each one's left and right corners at the eaves, then its peak. Roof hard to see on the front? Roof height "
       "from: A triangle on a side photo - pick the side photo, click the left eave, the ridge, the right eave, "
       "then drag the corners to fine-tune.",
    3: "Pick Window or Door and its top, then click each one's bottom left and top right corners. Ones on a bay "
       "or a wing go on it by themselves.",
    4: "Pick Bay (sticks out in front) or Wing (a lower block on an end), then click its bottom left corner (on "
       "the ground) and top right corner (just under its fascia). Set how far each comes out or goes back below. "
       "Their windows come next (step 4) and go on them by themselves.",
    5: "How deep the main building is, front to back: from the corner photo (if you've clicked its corners the "
       "other way), a straight-on photo of a side wall, or typed from a map.",
    6: "Check the sizes, then Send to Build.",
}
FSHORT = {1: "Follow the yellow box.",
          2: "Follow the yellow box.",
          3: "Follow the yellow box.",
          4: "Follow the yellow box - one thing at a time.",
          5: "How deep it is - pick one.",
          6: "Check the sizes, then Send."}
FCOLS = {'window': (77, 204, 255), 'door': (255, 140, 38), 'bay': (255, 217, 26), 'wing': (255, 115, 230)}


def front_blank(photo, extras):
    """A new front-first job: the face-on photo is the first straight-on one there is, else the main photo."""
    face = next((e['path'] for e in extras or [] if e.get('kind') == 'wall' and e.get('path')), None)
    return {'v': 1, 'photo': face or photo, 'quad': [], 'length_mm': 0.0, 'eaves_mm': 0.0, 'storeys': 2,
            'roof': 'gable_len', 'roof_low': 'front', 'ridge': None, 'gables': [], 'boxes': [], 'parts': [],
            'depth_how': 'type', 'depth_mm': 0.0, 'side': {'photo': None, 'quad': []}, 'step': 1}


def _square_up(pts):
    """A traced outline squared up: points near its sides put on them (upright sides), near its bottom put on
    it (level), the two sides' tops made the same height and a point near the middle put on it (an even peak)."""
    try:
        if not pts or len(pts) < 3:
            return pts
        xs, zs = [p[0] for p in pts], [p[1] for p in pts]
        x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
        w, h = x1 - x0, z1 - z0
        if w <= 1.0 or h <= 1.0:
            return pts
        tx, tz = 0.15 * w, 0.1 * h
        out = []
        for x, z in pts:
            if abs(z - z0) < tz:
                z = z0
            if abs(x - x0) < tx:
                x = x0
            elif abs(x - x1) < tx:
                x = x1
            elif abs(x - (x0 + x1) / 2.0) < tx:
                x = (x0 + x1) / 2.0
            out.append([round(x, 1), round(z, 1)])
        lt = [i for i, p in enumerate(out) if p[0] == x0 and p[1] > z0]
        rt = [i for i, p in enumerate(out) if p[0] == x1 and p[1] > z0]
        if len(lt) == 1 and len(rt) == 1:
            zz = round((out[lt[0]][1] + out[rt[0]][1]) / 2.0, 1)   # the sides' tops (shoulders) even
            out[lt[0]][1] = out[rt[0]][1] = zz
        clean = []
        for p in out:                                     # no doubled points
            if not clean or abs(p[0] - clean[-1][0]) > 0.5 or abs(p[1] - clean[-1][1]) > 0.5:
                clean.append(p)
        if len(clean) > 1 and abs(clean[0][0] - clean[-1][0]) <= 0.5 and abs(clean[0][1] - clean[-1][1]) <= 0.5:
            clean.pop()
        return clean if len(clean) >= 3 else pts
    except Exception:
        return pts


def _ccw(pts):
    """An outline the right way round (anticlockwise, seen from outside)."""
    a = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    return list(reversed(pts)) if a < 0 else pts


class FrontWindow(QDialog):
    """Start from the front: a face-on photo of the front, then the depth."""

    def __init__(self, main, folder, photo, extras, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QStackedWidget, QRadioButton, QButtonGroup, QScrollArea, QFrame, QGridLayout
        self.setWindowTitle("Start from the front - %s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.main, self.folder, self.M = main, folder, maths()
        self.photo0, self.extras = photo, list(extras or [])
        self.pixes, self.busy = {}, False
        self.history, self.future = [], []
        self.kind, self.top, self.box_kind = 'window', 'square', 'bay'
        self.pending = None
        self.hover = None
        self._sizes = {}
        self.gable_mode = False
        self.drag_tri = None                          # the roof triangle's corner being dragged
        self.peek = None                              # a photo looked at from the tabs (not this step's)
        self._tab_paths = []
        self.side_mode = False                        # clicking the side photo's 4 corners
        self.known_mode = False                       # clicking the two ends of something you know the size of
        self._auto_job = 0                            # the other job with the corner photo (0: not looked yet)
        self._ratios = {}
        self.how_f = 'box'                            # a window: 'box' (2 clicks) or 'outline' (all round)
        self.guides = []                              # what the mouse has snapped to
        self.front_mode = False                       # clicking a splayed bay's flat front
        self.trace = []                               # the points of one being clicked all round
        self.f = self._load()
        self.line_mode, self.line_sel = False, []
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self.save)

        lay = QHBoxLayout(self)
        left = QVBoxLayout()
        self.lbl_top = QLabel()
        self.lbl_top.setWordWrap(True)
        left.addWidget(self.lbl_top)
        from PySide6.QtWidgets import QTabBar
        self.tabs = QTabBar()
        self.tabs.setExpanding(False)
        self.tabs.setDocumentMode(True)
        self.tabs.setToolTip("Flick between the photos. The one with a dot is the photo this step clicks on.")
        left.addWidget(self.tabs)
        self.view = PhotoView(self)
        left.addWidget(self.view, 1)
        hrow = QHBoxLayout()
        hrow.addWidget(_note("Wheel: zoom in.   Right-drag: move the photo.   Ctrl+Z: undo a click.", True), 1)
        self.b_full = QPushButton("Full screen  (F11)")
        self.b_full.setCheckable(True)
        hrow.addWidget(self.b_full)
        left.addLayout(hrow)
        lay.addLayout(left, 3)

        side_w = QWidget()
        side = QVBoxLayout(side_w)
        side.setContentsMargins(0, 0, 0, 0)
        srow = QHBoxLayout()
        self.step_btns = []
        for n, title in FSTEPS:
            b = QPushButton(str(n))
            b.setCheckable(True)
            b.setMinimumHeight(30)
            b.setMaximumWidth(64)
            b.setToolTip(title)
            b.clicked.connect(lambda _c=False, n=n: self.goto(n))
            srow.addWidget(b)
            self.step_btns.append(b)
        side.addLayout(srow)
        self.lbl_step = QLabel()
        fnt = self.lbl_step.font()
        fnt.setBold(True)
        if fnt.pointSizeF() > 0:
            fnt.setPointSizeF(fnt.pointSizeF() * 1.15)
        self.lbl_step.setFont(fnt)
        side.addWidget(self.lbl_step)
        self.lbl_how = _note("")
        side.addWidget(self.lbl_how)
        self.lbl_guide = QLabel()
        self.lbl_guide.setWordWrap(True)
        self.lbl_guide.setStyleSheet("background: #fff4c2; border: 1px solid #e0c060; padding: 8px; "
                                     "font-size: 12pt;")
        side.addWidget(self.lbl_guide)
        self.stack = QStackedWidget()
        side.addWidget(self.stack)

        def mm_box(top=200000.0, special=None):
            s = QDoubleSpinBox()
            s.setRange(0.0, top)
            s.setDecimals(0)
            s.setSingleStep(10.0)
            s.setSuffix(" mm")
            if special:
                s.setSpecialValueText(special)
            s.setKeyboardTracking(False)
            return s
        # 1 the front - one thing at a time
        pg = QWidget()
        v1 = QVBoxLayout(pg)
        v1.setContentsMargins(0, 0, 0, 0)
        fl = QFormLayout()
        self.cb_photo = QComboBox()
        b_addp = QPushButton("Another photo...")
        r_ = QHBoxLayout()
        r_.addWidget(self.cb_photo, 1)
        r_.addWidget(b_addp)
        fl.addRow("Photo of the front", r_)
        v1.addLayout(fl)
        # the size: once the corners are in
        self.w_size1 = QWidget()
        fs1 = QFormLayout(self.w_size1)
        fs1.setContentsMargins(0, 6, 0, 0)
        self.sp_len = mm_box(special="type it here")
        self.sp_len.setMinimumHeight(30)
        fs1.addRow("<b>How long is the front?</b>", self.sp_len)
        self.b_known_show = QPushButton("Don't know?  Measure from something on it instead ▸")
        self.b_known_show.setCheckable(True)
        fs1.addRow(self.b_known_show)
        self.w_known = QWidget()
        fk = QFormLayout(self.w_known)
        fk.setContentsMargins(12, 0, 0, 0)
        fk.addRow(_note("Something on the front you know the size of - a door's height, a bench:", True))
        self.b_known = QPushButton("1.  Click its two ends")
        self.b_known.setCheckable(True)
        self.sp_known = mm_box(special="type its size")
        fk.addRow(self.b_known)
        fk.addRow("2.  How long is it?", self.sp_known)
        fs1.addRow(self.w_known)
        self.sp_storeys = QSpinBox()
        self.sp_storeys.setRange(1, 20)
        fs1.addRow("<b>How many floors?</b>", self.sp_storeys)
        v1.addWidget(self.w_size1)
        # tucked away
        self.b_more1 = QPushButton("More settings ▸")
        self.b_more1.setCheckable(True)
        self.b_more1.setFlat(True)
        self.b_more1.setStyleSheet("text-align: left; color: #555;")
        v1.addWidget(self.b_more1)
        self.w_more1 = QWidget()
        fm1 = QFormLayout(self.w_more1)
        fm1.setContentsMargins(12, 0, 0, 0)
        self.sp_eaves = mm_box(special="from the photo")
        fm1.addRow("Height to the roof edge", self.sp_eaves)
        self.b_quad_again = QPushButton("Click the 4 corners again")
        fm1.addRow(self.b_quad_again)
        v1.addWidget(self.w_more1)
        v1.addStretch(1)
        self.stack.addWidget(pg)
        # 2 roof - one thing at a time
        pg = QWidget()
        v2 = QVBoxLayout(pg)
        v2.setContentsMargins(0, 0, 0, 0)
        big2 = "QPushButton { min-height: 34px; font-size: 10.5pt; font-weight: bold; text-align: left; " \
               "padding-left: 10px; }"
        self.w_rshape = QWidget()
        vr = QVBoxLayout(self.w_rshape)
        vr.setContentsMargins(0, 0, 0, 0)
        self.rshape_btns = []
        for key, low, label in (('gable_len', None, "Ridge along the front  (slopes down to the front)"),
                                ('gable_across', None, "Pointed end facing you  (the front is a gable)"),
                                ('hip', None, "Slopes on every side  (hipped)"),
                                ('mono', 'front', "One slope - low at the front  (lean-to)"),
                                ('mono', 'back', "One slope - low at the back  (lean-to)"),
                                ('flat', None, "Flat roof")):
            b_ = QPushButton(label)
            b_.setStyleSheet(big2)
            b_.clicked.connect(lambda _c=False, k=key, lo=low: self.roof_pick(k, lo))
            vr.addWidget(b_)
        v2.addWidget(self.w_rshape)
        self.w_gq = QWidget()
        hg = QVBoxLayout(self.w_gq)
        hg.setContentsMargins(0, 0, 0, 0)
        self.b_gyes = QPushButton("Yes - I'll click them")
        self.b_gno = QPushButton("No pointed gables")
        for b_ in (self.b_gyes, self.b_gno):
            b_.setStyleSheet(big2)
            hg.addWidget(b_)
        v2.addWidget(self.w_gq)
        self.b_gdone = QPushButton("That's all the gables  ✓")
        self.b_gdone.setStyleSheet("QPushButton { min-height: 34px; font-size: 10.5pt; font-weight: bold; "
                                   "background: #c8f0c8; }")
        v2.addWidget(self.b_gdone)
        self.w_rhow2 = QWidget()
        vh2 = QVBoxLayout(self.w_rhow2)
        vh2.setContentsMargins(0, 0, 0, 0)
        b_cp = QPushButton("Use the corner photo  (best)")
        b_ck = QPushButton("Click the top of the roof on this photo")
        for b_ in (b_cp, b_ck):
            b_.setStyleSheet(big2)
            vh2.addWidget(b_)
        b_cp.clicked.connect(lambda: self._rhow_pick('cpeak'))
        b_ck.clicked.connect(lambda: self._rhow_pick('click'))
        v2.addWidget(self.w_rhow2)
        self.b_rshape_again = QPushButton("Change the roof's shape")
        v2.addWidget(self.b_rshape_again)
        self.b_more2 = QPushButton("More settings ▸")
        self.b_more2.setCheckable(True)
        self.b_more2.setFlat(True)
        self.b_more2.setStyleSheet("text-align: left; color: #555;")
        v2.addWidget(self.b_more2)
        self.w_more2 = QWidget()
        fl = QFormLayout(self.w_more2)
        fl.setContentsMargins(12, 0, 0, 0)
        self.cb_roof = QComboBox()
        for key, label, _d in self.M.ROOFS:
            self.cb_roof.addItem(label, key)
        self.cb_low = QComboBox()
        self.cb_low.addItem("The low side at the front", 'front')
        self.cb_low.addItem("The low side at the back", 'back')
        fl.addRow("Roof", self.cb_roof)
        fl.addRow("Lean-to", self.cb_low)
        self.ck_gables = QCheckBox("Click gables (pointed ones on the front of the roof)")
        fl.addRow(self.ck_gables)
        self.cb_rhow = QComboBox()
        self.cb_rhow.addItem("The front gables' pitch (best)", 'gables')
        self.cb_rhow.addItem("The roof top I clicked", 'click')
        self.cb_rhow.addItem("A pitch I type", 'pitch')
        self.cb_rhow.addItem("A triangle on a side photo", 'side')
        self.cb_rhow.addItem("As high as the tallest gable's peak", 'peak')
        self.cb_rhow.addItem("The end wall's peak on the corner photo", 'cpeak')
        self.cb_rhow.setToolTip("The ridge is set back from the front, so a face-on photo makes it look lower than "
                                "it is - the gables are in the wall, so their pitch measures true.")
        fl.addRow("Roof height from", self.cb_rhow)
        self.sp_rpitch = QDoubleSpinBox()
        self.sp_rpitch.setRange(5.0, 70.0)
        self.sp_rpitch.setDecimals(0)
        self.sp_rpitch.setSuffix(" °")
        fl.addRow("Roof pitch", self.sp_rpitch)
        self.w_rside = QWidget()
        fs = QFormLayout(self.w_rside)
        fs.setContentsMargins(0, 0, 0, 0)
        self.cb_rside = QComboBox()
        self.cb_rside.setToolTip("A photo of the gable end, as straight on as you can (Another photo... adds one).")
        fs.addRow("Side photo", self.cb_rside)
        self.lbl_rside = _note("", True)
        fs.addRow(self.lbl_rside)
        self.b_rside_new = QPushButton("Start the triangle again")
        fs.addRow(self.b_rside_new)
        fl.addRow(self.w_rside)
        self.sp_eover = mm_box(top=2000.0)
        self.sp_eover.setToolTip("How far the roof hangs out past the front and back walls (bays: 150 mm).")
        fl.addRow("Roof sticks out (front, back)", self.sp_eover)
        self.sp_vover = mm_box(top=2000.0)
        self.sp_vover.setToolTip("How far the roof hangs out past the gable ends (and the front gables' barge boards).")
        fl.addRow("Roof sticks out (ends)", self.sp_vover)
        self.ck_boards = QCheckBox("Fascia, barge boards and soffits (made by Subframe, its board sizes)")
        fl.addRow(self.ck_boards)
        self.lbl_gables = QLabel()
        fl.addRow(self.lbl_gables)
        v2.addWidget(self.w_more2)
        v2.addStretch(1)
        self.stack.addWidget(pg)
        # 3 windows and doors
        pg = QWidget()
        v3 = QVBoxLayout(pg)
        v3.setContentsMargins(0, 0, 0, 0)
        r3 = QHBoxLayout()
        self.rb_win = QRadioButton("Windows (W)")
        self.rb_door = QRadioButton("Doors (D)")
        self.grp_kind = QButtonGroup(self)
        self.grp_kind.addButton(self.rb_win, 0)
        self.grp_kind.addButton(self.rb_door, 1)
        r3.addWidget(self.rb_win)
        r3.addWidget(self.rb_door)
        v3.addLayout(r3)
        r3b = QHBoxLayout()
        self.rb_fbox = QRadioButton("Box - 2 corners")
        self.rb_fall = QRadioButton("All round - 6+ points")
        self.rb_fall.setToolTip("Any shape - pointed, arched: click 6 or more points round it, then Finish.")
        self.grp_fhow = QButtonGroup(self)
        self.grp_fhow.addButton(self.rb_fbox, 0)
        self.grp_fhow.addButton(self.rb_fall, 1)
        r3b.addWidget(self.rb_fbox)
        r3b.addWidget(self.rb_fall)
        v3.addLayout(r3b)
        self.b_finish = QPushButton("Finish this one  (Enter)")
        self.b_finish.setMinimumHeight(30)
        v3.addWidget(self.b_finish)
        f3 = QFormLayout()
        self.cb_top = QComboBox()
        for key, label, _d in self.M.TOPS:
            self.cb_top.addItem(label, key)
        f3.addRow("Top (T)", self.cb_top)
        v3.addLayout(f3)
        self.lbl_ops = QLabel()
        v3.addWidget(self.lbl_ops)
        self.ck_sides = QCheckBox("Bay sides you can't see: the same windows as the side you can")
        v3.addWidget(self.ck_sides)
        # the simple way: big buttons (the ones above are kept for the keys, but hidden)
        for w_ in (self.rb_win, self.rb_door, self.rb_fbox, self.rb_fall, self.cb_top):
            w_.setVisible(False)
        f3.labelForField(self.cb_top).setVisible(False)
        bigt = "QPushButton { min-height: 32px; font-size: 10.5pt; font-weight: bold; } " \
               "QPushButton:checked { background: #ffd84a; border: 2px solid #b08a00; }"
        v3.insertWidget(0, QLabel("<b>What are you marking?</b>"))
        rk_ = QHBoxLayout()
        self.b_k_win = QPushButton("Windows")
        self.b_k_door = QPushButton("Doors")
        for b_ in (self.b_k_win, self.b_k_door):
            b_.setCheckable(True)
            b_.setStyleSheet(bigt)
            rk_.addWidget(b_)
        v3.insertLayout(1, rk_)
        v3.insertWidget(2, QLabel("<b>The shape of its top</b>"))
        gt_ = QGridLayout()
        self.b_t = {}
        for i_, (key, label) in enumerate((('square', "Square"), ('segment', "Shallow arch"),
                                           ('round', "Round arch"), ('outline', "Odd shape (click all round)"))):
            b_ = QPushButton(label)
            b_.setCheckable(True)
            b_.setStyleSheet(bigt)
            gt_.addWidget(b_, i_ // 2, i_ % 2)
            self.b_t[key] = b_
        v3.insertLayout(3, gt_)
        self.lbl_ops.setVisible(False)                 # the count is in the yellow box
        rl_ = QHBoxLayout()
        self.b_line = QPushButton("Line windows up...")
        self.b_line.setCheckable(True)
        self.b_line.setStyleSheet("QPushButton { min-height: 30px; font-weight: bold; } "
                                  "QPushButton:checked { background: #9fe0ff; border: 2px solid #2a7fa8; }")
        self.b_line_go = QPushButton("Line them up...")
        self.b_line_go.setStyleSheet("QPushButton { min-height: 30px; font-weight: bold; background: #7ad67a; }")
        rl_.addWidget(self.b_line)
        rl_.addWidget(self.b_line_go)
        v3.insertLayout(4, rl_)
        self.b_line.toggled.connect(self._line_mode)
        self.b_line_go.clicked.connect(self.line_up)
        self.ck_sides.setText("Bay sides hidden from view: the same windows as the side you can see")
        v3.addStretch(1)
        self.ck_sides.toggled.connect(lambda on: self._set('bay_sides', bool(on)))
        self.stack.addWidget(pg)
        # 4 bays and wings - a guided job, one thing at a time
        pg = QWidget()
        v4 = QVBoxLayout(pg)
        v4.setContentsMargins(0, 0, 0, 0)
        self.lbl_job = QLabel()
        self.lbl_job.setWordWrap(True)
        self.lbl_job.setStyleSheet("background: #fff4c2; border: 1px solid #e0c060; padding: 8px; font-size: 11pt;")
        v4.addWidget(self.lbl_job)
        big = "QPushButton { min-height: 34px; font-size: 10.5pt; font-weight: bold; }"
        # what next: add one
        self.w_jstart = QWidget()
        vj = QVBoxLayout(self.w_jstart)
        vj.setContentsMargins(0, 0, 0, 0)
        self.b_add_bay = QPushButton("+  Add a bay")
        self.b_add_same = QPushButton("+  Add another bay the same")
        self.b_add_wing = QPushButton("+  Add a wing (a block on an end)")
        for b_ in (self.b_add_bay, self.b_add_same, self.b_add_wing):
            b_.setStyleSheet(big)
            vj.addWidget(b_)
        v4.addWidget(self.w_jstart)
        # its shape
        self.w_jshape = QWidget()
        vj = QVBoxLayout(self.w_jshape)
        vj.setContentsMargins(0, 0, 0, 0)
        self.b_sh_sq = QPushButton("Square  (straight out, square corners)")
        self.b_sh_sp = QPushButton("Splayed  (angled sides - most bay windows)")
        self.b_sh_rd = QPushButton("Round  (a curved bow)")
        for b_ in (self.b_sh_sq, self.b_sh_sp, self.b_sh_rd):
            b_.setStyleSheet(big)
            vj.addWidget(b_)
        v4.addWidget(self.w_jshape)
        # its sizes and roof (the bay being set up, or one picked from the list)
        self.w_form = QWidget()
        f4 = QFormLayout(self.w_form)
        f4.setContentsMargins(0, 0, 0, 0)
        self.sp_out = mm_box()
        self.sp_back = mm_box(special="level with the front")
        self.cb_proof = QComboBox()
        for key, label, _d in self.M.ROOFS:
            self.cb_proof.addItem(label, key)
        self.sp_pitch = QDoubleSpinBox()
        self.sp_pitch.setRange(5.0, 70.0)
        self.sp_pitch.setDecimals(0)
        self.sp_pitch.setSuffix(" °")
        self.lbl_out = QLabel("Comes out")
        self.cb_bshape = QComboBox()
        self.cb_bshape.addItem("Square", 'square')
        self.cb_bshape.addItem("Splayed (angled sides)", 'splayed')
        self.cb_bshape.addItem("Round (a bow)", 'round')
        f4.addRow("Bay shape", self.cb_bshape)
        self.sp_front = mm_box(special="from its posts, or 60%")
        self.b_front = QPushButton("Click its 2 posts again")
        self.b_front.setCheckable(True)
        f4.addRow("Flat front", self.sp_front)
        f4.addRow(self.b_front)
        f4.addRow(self.lbl_out, self.sp_out)
        f4.addRow("Set back from the front", self.sp_back)
        f4.addRow("Its roof", self.cb_proof)
        f4.addRow("Roof pitch", self.sp_pitch)
        v4.addWidget(self.w_form)
        self.b_job_done = QPushButton("Done  ✓")
        self.b_job_done.setStyleSheet("QPushButton { min-height: 34px; font-size: 10.5pt; font-weight: bold; "
                                      "background: #c8f0c8; }")
        v4.addWidget(self.b_job_done)
        self.b_job_stop = QPushButton("Stop - don't add this one")
        v4.addWidget(self.b_job_stop)
        # the ones done
        self.lbl_done = QLabel("<b>Done so far</b> - pick one to change it:")
        v4.addWidget(self.lbl_done)
        self.lst_parts = QListWidget()
        self.lst_parts.setMaximumHeight(90)
        v4.addWidget(self.lst_parts)
        self.w_pick = QWidget()
        hp = QHBoxLayout(self.w_pick)
        hp.setContentsMargins(0, 0, 0, 0)
        self.b_same = QPushButton("Make the others the same")
        self.b_same.setToolTip("Copies this bay's shape, flat front, how far it comes out and its roof to the other "
                               "bays - each keeps its own place along the front.")
        self.b_part_off = QPushButton("Take this one off")
        hp.addWidget(self.b_same)
        hp.addWidget(self.b_part_off)
        v4.addWidget(self.w_pick)
        # kept (not shown): bay or wing for the old way
        self.rb_bay = QRadioButton("Bay")
        self.rb_wing = QRadioButton("Wing")
        self.grp_box = QButtonGroup(self)
        self.grp_box.addButton(self.rb_bay, 0)
        self.grp_box.addButton(self.rb_wing, 1)
        self.rb_bay.setVisible(False)
        self.rb_wing.setVisible(False)
        v4.addStretch(1)
        self.stack.addWidget(pg)
        # 5 depth
        pg = QWidget()
        v5 = QVBoxLayout(pg)
        v5.setContentsMargins(0, 0, 0, 0)
        self.grp_depth = QButtonGroup(self)
        self.rb_d_corner = QRadioButton("From the corner photo")
        self.rb_d_side = QRadioButton("From a straight-on photo of a side wall")
        self.rb_d_type = QRadioButton("Typed (from a map)")
        bigd = "QPushButton { min-height: 34px; font-size: 10.5pt; font-weight: bold; text-align: left; " \
               "padding-left: 10px; } QPushButton:checked { background: #ffd84a; border: 2px solid #b08a00; }"
        v5.addWidget(QLabel("<b>How shall we find how deep it is?</b>"))
        self.b_dh = {}
        for key_, label in (('cphoto', "From the corner photo  (click 6 corners)"),
                            ('side', "From a photo straight on to the side"),
                            ('type', "Type it in  (measured on a map)")):
            b_ = QPushButton(label)
            b_.setCheckable(True)
            b_.setStyleSheet(bigd)
            b_.clicked.connect(lambda _c=False, k=key_: self.depth_pick(k))
            v5.addWidget(b_)
            self.b_dh[key_] = b_
        f5 = QFormLayout()
        self.cb_side = QComboBox()
        self.lbl_side5 = QLabel("Side photo")
        f5.addRow(self.lbl_side5, self.cb_side)
        self.sp_depth = mm_box(special="type it")
        self.sp_depth.setMinimumHeight(30)
        self.lbl_depth5 = QLabel("<b>How deep is it?</b>")
        f5.addRow(self.lbl_depth5, self.sp_depth)
        v5.addLayout(f5)
        self.b_cd_again = QPushButton("Click the 6 corners again")
        v5.addWidget(self.b_cd_again)
        self.b_cd_again.clicked.connect(self.cdepth_again)
        self.b_more5 = QPushButton("More settings ▸")
        self.b_more5.setCheckable(True)
        self.b_more5.setFlat(True)
        self.b_more5.setStyleSheet("text-align: left; color: #555;")
        v5.addWidget(self.b_more5)
        self.w_more5 = QWidget()
        vm5 = QVBoxLayout(self.w_more5)
        vm5.setContentsMargins(12, 0, 0, 0)
        for i_, rb in enumerate((self.rb_d_corner, self.rb_d_side, self.rb_d_type)):
            self.grp_depth.addButton(rb, i_)
        self.rb_d_corner.setText("From a corner photo done the other way (Start clicking round the building)")
        vm5.addWidget(self.rb_d_corner)
        self.lbl_corner = _note("", True)
        vm5.addWidget(self.lbl_corner)
        self.b_cjob = QPushButton("Pick which corner photo job to use...")
        self.b_cjob.setToolTip("Pick the job folder where you clicked round the building on the corner photo.")
        vm5.addWidget(self.b_cjob)
        self.b_cjob.clicked.connect(self.pick_corner_job)
        self.rb_d_side.setVisible(False)
        self.rb_d_type.setVisible(False)
        v5.addWidget(self.w_more5)
        self.b_more5.toggled.connect(lambda _on: None if self.busy else self.update_all())
        v5.addStretch(1)
        self.stack.addWidget(pg)
        # 6 send: the plan, big, to check - and change a bay if it isn't right
        pg = QWidget()
        v6 = QVBoxLayout(pg)
        v6.setContentsMargins(0, 0, 0, 0)
        self.lbl_sizes = _note("", True)
        v6.addWidget(self.lbl_sizes)
        self.plan6 = FrontPlan(self, pickable=True)
        self.plan6.setMinimumHeight(300)
        v6.addWidget(self.plan6)
        self.lbl_pick6 = QLabel()
        self.lbl_pick6.setWordWrap(True)
        v6.addWidget(self.lbl_pick6)
        self.w_ed6 = QWidget()
        e6 = QVBoxLayout(self.w_ed6)
        e6.setContentsMargins(0, 0, 0, 0)
        r6 = QHBoxLayout()
        self.b6_shape = {}
        for key_, label in (('square', "Square"), ('splayed', "Angled sides"), ('round', "Round")):
            b_ = QPushButton(label)
            b_.setCheckable(True)
            b_.setStyleSheet("QPushButton:checked { background: #ffd84a; border: 2px solid #b08a00; }")
            b_.clicked.connect(lambda _c=False, k=key_: self._part_set('shape', k))
            r6.addWidget(b_)
            self.b6_shape[key_] = b_
        e6.addLayout(r6)
        f6 = QFormLayout()
        self.sp6_out = mm_box()
        f6.addRow("Comes out", self.sp6_out)
        e6.addLayout(f6)
        r6c = QHBoxLayout()
        self.b6_even = QPushButton("Even up the angled sides")
        self.b6_same = QPushButton("Make the others like this one")
        r6c.addWidget(self.b6_even)
        r6c.addWidget(self.b6_same)
        e6.addLayout(r6c)
        self.b6_even.clicked.connect(self.even_splays)
        self.b6_same.clicked.connect(lambda: self.bays_same())
        r6b = QHBoxLayout()
        self.b6_swap = QPushButton("Swap it with the next bay")
        self.b6_off = QPushButton("Take it off")
        r6b.addWidget(self.b6_swap)
        r6b.addWidget(self.b6_off)
        e6.addLayout(r6b)
        v6.addWidget(self.w_ed6)
        self.sp6_out.valueChanged.connect(lambda v: self._part_set('out', float(v)))
        self.b6_swap.clicked.connect(self.swap_bay)
        self.b6_off.clicked.connect(lambda: self.b_part_off.click())
        self.b_send = QPushButton("Send to Build  ▶")
        self.b_send.setMinimumHeight(38)
        self.b_send.setStyleSheet("QPushButton { background: #7ad67a; font-weight: bold; }")
        v6.addWidget(self.b_send)
        v6.addStretch(1)
        self.stack.addWidget(pg)

        self.lbl_problem = _note("")
        self.lbl_problem.setStyleSheet("color: #b00;")
        side.addWidget(self.lbl_problem)
        urow = QHBoxLayout()
        self.b_undo = QPushButton("Undo  (Ctrl+Z)")
        self.b_redo = QPushButton("Bring it back  (Ctrl+Y)")
        urow.addWidget(self.b_undo)
        urow.addWidget(self.b_redo)
        side.addLayout(urow)
        nrow = QHBoxLayout()
        self.b_back = QPushButton("Back")
        self.b_fwd = QPushButton("Next  ▶")
        for b_ in (self.b_back, self.b_fwd):
            b_.setMinimumHeight(34)
        nrow.addWidget(self.b_back)
        nrow.addWidget(self.b_fwd, 2)
        side.addLayout(nrow)
        self.diag = StepDiagram(self)
        side.addWidget(self.diag)
        self.plan = FrontPlan(self)
        self.plan.setMinimumHeight(150)
        side.addWidget(self.plan, 1)
        self.preview3d = Preview3D(self)
        side.addWidget(self.preview3d, 2)                 # the spare room: the building in 3D
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setFrameShape(QFrame.NoFrame)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sa.setWidget(side_w)
        sa.setMinimumWidth(430)
        lay.addWidget(sa, 1)
        try:
            self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        except Exception:
            pass

        b_addp.clicked.connect(self.add_photo)
        self.tabs.currentChanged.connect(self._tab)
        self.cb_photo.currentIndexChanged.connect(self._front_photo)
        self.sp_len.valueChanged.connect(lambda v: self._set('length_mm', float(v)))
        self.sp_eaves.valueChanged.connect(lambda v: self._set('eaves_mm', float(v)))
        self.sp_storeys.valueChanged.connect(lambda v: self._set('storeys', int(v)))
        self.b_known.toggled.connect(self._known_mode)
        self.b_known_show.toggled.connect(lambda _on: None if self.busy else self.update_all())
        self.b_more1.toggled.connect(lambda _on: None if self.busy else self.update_all())
        self.b_quad_again.clicked.connect(self._quad_again)
        self.sp_known.valueChanged.connect(self._known_mm)
        self.cb_roof.currentIndexChanged.connect(lambda _i: self._set('roof', self.cb_roof.currentData()))
        self.cb_low.currentIndexChanged.connect(lambda _i: self._set('roof_low', self.cb_low.currentData()))
        self.ck_gables.toggled.connect(self._gables)
        self.cb_rhow.currentIndexChanged.connect(lambda _i: self._set('ridge_how', self.cb_rhow.currentData()))
        self.sp_rpitch.valueChanged.connect(lambda v: self._set('roof_pitch', float(v)))
        self.cb_rside.currentIndexChanged.connect(self._roof_side_photo)
        self.sp_eover.valueChanged.connect(lambda v: self._set('eave_over', float(v)))
        self.sp_vover.valueChanged.connect(lambda v: self._set('verge_over', float(v)))
        self.ck_boards.toggled.connect(lambda on: self._set('boards', bool(on)))
        self.b_rside_new.clicked.connect(self._roof_tri_clear)
        self.b_gyes.clicked.connect(lambda: self.gables_answer(True))
        self.b_gno.clicked.connect(lambda: self.gables_answer(False))
        self.b_gdone.clicked.connect(self.gables_finished)
        self.b_rshape_again.clicked.connect(self.roof_again)
        self.b_more2.toggled.connect(lambda _on: None if self.busy else self.update_all())
        self.grp_kind.idClicked.connect(lambda i: self._kind('door' if i == 1 else 'window'))
        self.cb_top.currentIndexChanged.connect(lambda _i: self._top(self.cb_top.currentData()))
        self.grp_fhow.idClicked.connect(lambda i: self._how_f('outline' if i == 1 else 'box'))
        self.b_finish.clicked.connect(self.finish_trace)
        self.b_k_win.clicked.connect(lambda: self._kind('window'))
        self.b_k_door.clicked.connect(lambda: self._kind('door'))
        for key_, b_ in self.b_t.items():
            b_.clicked.connect(lambda _c=False, k=key_: self.top_pick(k))
        self.grp_box.idClicked.connect(lambda i: self._box_kind('wing' if i == 1 else 'bay'))
        self.lst_parts.currentRowChanged.connect(self._pick_part)
        self.sp_out.valueChanged.connect(lambda v: self._part_set('out', float(v)))
        self.sp_back.valueChanged.connect(lambda v: self._part_set('back', float(v)))
        self.cb_proof.currentIndexChanged.connect(lambda _i: self._part_set('roof', self.cb_proof.currentData()))
        self.sp_pitch.valueChanged.connect(lambda v: self._part_set('pitch', float(v)))
        self.cb_bshape.currentIndexChanged.connect(lambda _i: self._part_set('shape', self.cb_bshape.currentData()))
        self.sp_front.valueChanged.connect(lambda v: self._part_set('front', float(v)))
        self.b_front.toggled.connect(self._front_mode)
        self.b_part_off.clicked.connect(self.part_off)
        self.b_same.clicked.connect(self.bays_same)
        self.b_add_bay.clicked.connect(lambda: self.job_start('bay'))
        self.b_add_same.clicked.connect(lambda: self.job_start('same'))
        self.b_add_wing.clicked.connect(lambda: self.job_start('wing'))
        self.b_sh_sq.clicked.connect(lambda: self.job_shape('square'))
        self.b_sh_sp.clicked.connect(lambda: self.job_shape('splayed'))
        self.b_sh_rd.clicked.connect(lambda: self.job_shape('round'))
        self.b_job_done.clicked.connect(self.job_done)
        self.b_job_stop.clicked.connect(self.job_stop)
        self.grp_depth.idClicked.connect(lambda i: self._set('depth_how', ('corner', 'side', 'type')[i]))
        self.cb_side.currentIndexChanged.connect(self._side_photo)
        self.sp_depth.valueChanged.connect(lambda v: self._set('depth_mm', float(v)))
        self.b_send.clicked.connect(self.send)
        self.b_undo.clicked.connect(self.undo)
        self.b_redo.clicked.connect(self.redo)
        self.b_back.clicked.connect(lambda: self.goto(int(self.f.get('step') or 1) - 1))
        self.b_fwd.clicked.connect(lambda: self.goto(int(self.f.get('step') or 1) + 1))
        self.b_full.toggled.connect(self.full_screen)
        self.resize(1450, 900)
        try:
            eddy_place(self, PLUGIN_NAME + " - front")
        except Exception:
            pass
        self.sel_part = 0
        self.line_mode = False                         # lining windows up: picking them
        self.line_sel = []                             # the windows picked (the first is the one to copy)
        self.sort_parts()                               # older jobs: numbered left to right too
        self.show_photo()
        self.update_all()
        self._install_keys()

    # ---- keeping it ----
    def _load(self):
        fp = os.path.join(self.folder, FRONT_NAME)
        if os.path.isfile(fp):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    got = json.load(f)
                if isinstance(got, dict) and got.get('v'):
                    base = front_blank(self.photo0, self.extras)
                    base.update(got)
                    return base
            except Exception as e:
                print("%s: front.json not read: %s" % (PLUGIN_NAME, e))
        return front_blank(self.photo0, self.extras)

    def save(self):
        try:
            tmp = os.path.join(self.folder, FRONT_NAME + ".part")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.f, f, indent=1)
            os.replace(tmp, os.path.join(self.folder, FRONT_NAME))
        except Exception as e:
            print("%s: front not saved: %s" % (PLUGIN_NAME, e))

    def closeEvent(self, ev):
        self.save()
        self._remove_keys()
        super().closeEvent(ev)

    def remember(self):
        self.history.append(copy.deepcopy((self.f, self.pending)))
        del self.history[:-80]
        self.future = []

    def undo(self):
        if not self.history:
            return
        self.peek = None
        self.future.append(copy.deepcopy((self.f, self.pending)))
        self.f, self.pending = self.history.pop()
        self.show_photo()
        self.update_all()

    def redo(self):
        if not self.future:
            return
        self.history.append(copy.deepcopy((self.f, self.pending)))
        self.f, self.pending = self.future.pop()
        self.show_photo()
        self.update_all()

    def full_screen(self, on):
        if on:
            self._was_max = self.isMaximized()
            self.showFullScreen()
        elif getattr(self, '_was_max', False):
            self.showMaximized()
        else:
            self.showNormal()
        QTimer.singleShot(100, self.view.fit)

    # keys: the same catcher as the corner-photo window
    _install_keys = MatchWindow._install_keys
    _remove_keys = MatchWindow._remove_keys

    def handle_key(self, ev):
        k, mod = ev.key(), ev.modifiers()
        if k in (Qt.Key_F, Qt.Key_Home) and not mod & (Qt.ControlModifier | Qt.AltModifier):
            self.view.fit()
            return True
        if k == Qt.Key_F11:
            self.b_full.setChecked(not self.b_full.isChecked())
            return True
        return self.key(ev) or k == Qt.Key_Escape

    def key(self, ev):
        k, mod = ev.key(), ev.modifiers()
        if (k == Qt.Key_Y and mod & Qt.ControlModifier) or \
                (k == Qt.Key_Z and mod & Qt.ControlModifier and mod & Qt.ShiftModifier):
            self.redo()
            return True
        if k in (Qt.Key_Return, Qt.Key_Enter):
            if self.trace:
                self.finish_trace()
            return True
        if k in (Qt.Key_Backspace, Qt.Key_Delete) or (k == Qt.Key_Z and mod & Qt.ControlModifier):
            if self.trace:
                self.trace.pop()
                self.update_all()
            else:
                self.undo()
            return True
        if k == Qt.Key_Escape:
            if self.isFullScreen():
                self.b_full.setChecked(False)
            self.pending, self.trace = None, []
            self.view.update()
            return True
        if self.page() == 3 and not mod & (Qt.ControlModifier | Qt.AltModifier):
            if k == Qt.Key_W:
                self._kind('window')
                return True
            if k == Qt.Key_D:
                self._kind('door')
                return True
            if k == Qt.Key_T:
                ks = [t[0] for t in self.M.TOPS]
                self._top(ks[(ks.index(self.top) + 1) % len(ks)] if self.top in ks else ks[0])
                return True
        return False

    # ---- photos ----
    def photos(self):
        out = [self.photo0] + [e.get('path') for e in self.extras if e.get('path')]
        for p_ in (self.f.get('photo'), (self.f.get('side') or {}).get('photo')):
            if p_ and p_ not in out:
                out.append(p_)
        seen, keys = [], []
        for p_ in out:
            k_ = os.path.normcase(os.path.normpath(p_)) if p_ else None
            if p_ and k_ not in keys:
                seen.append(p_)
                keys.append(k_)
        return seen

    def add_photo(self):
        folder = os.path.dirname(self.photo0 or '') or DEFAULT_PICTURES
        path, _f = QFileDialog.getOpenFileName(self, "A straight-on photo", folder,
                                               "Photos (%s)" % " ".join("*" + e for e in PICTURE_TYPES))
        if not path:
            return
        self.extras.append({'path': path, 'kind': 'wall'})
        self.remember()
        if self.page() == 5:
            self.f['side'] = {'photo': path, 'quad': []}
            self.f['depth_how'] = 'side'
        elif self.page() == 2 and self.ridge_how() == 'side':
            self.f['roof_side'] = {'photo': path, 'clicks': []}
        else:
            self._switch_front(path)
        self.show_photo()
        self.update_all()

    def _switch_front(self, path):
        """A different front photo: the old one's corners are kept with it, the new one's come back."""
        f = self.f
        qs = f.setdefault('quads', {})
        if f.get('photo') and f.get('quad'):
            qs[os.path.normcase(os.path.normpath(f['photo']))] = f['quad']
        f['photo'] = path
        f['quad'] = list(qs.get(os.path.normcase(os.path.normpath(path)), []))

    def cur_photo(self):
        if self.peek and self.peek in self.photos():
            return self.peek
        return self.step_photo()

    def step_photo(self):
        """The photo this step clicks on."""
        if self.page() == 2 and self.ridge_how() == 'side' and not self.gable_mode:
            return (self.f.get('roof_side') or {}).get('photo') or self.f.get('photo')
        if self.page() == 2 and self.ridge_how() == 'cpeak' and not self.gable_mode:
            return self.cdepth_photo() or self.f.get('photo')
        if self.page() == 5 and self.f.get('depth_how') == 'side':
            return (self.f.get('side') or {}).get('photo') or self.f.get('photo')
        if self.page() == 5 and self.f.get('depth_how') == 'cphoto':
            return self.cdepth_photo() or self.f.get('photo')
        return self.f.get('photo')

    def cdepth_photo(self):
        """The corner photo the depth is clicked on: picked, else the first photo that isn't the front."""
        cd = self.f.get('cdepth') or {}
        ps = self.photos()
        if cd.get('photo') in ps:
            return cd['photo']
        for p_ in ps:
            if p_ != self.f.get('photo'):
                return p_
        return None

    def cdepth_cam(self):
        """The corner photo's camera from its 6 corners: (camera, W, H, clicks) or (None, why)."""
        cd = self.f.get('cdepth') or {}
        cl = cd.get('clicks') or []
        path = self.cdepth_photo()
        if len(cl) < 6 or not path:
            return None, "click the 6 corners on the corner photo"
        if path not in self._sizes:
            self._sizes[path] = photo_size(path)
        W, H = self._sizes[path] or (1000, 750)
        lines = {'r1': [cl[0][:2], cl[2][:2]], 'r2': [cl[1][:2], cl[3][:2]],
                 'g1': [cl[2][:2], cl[4][:2]], 'g2': [cl[3][:2], cl[5][:2]]}
        try:
            cam = self.M.solve_camera(lines, W, H)
        except Exception as e:
            return None, "those corners don't fit together (%s) - Ctrl+Z and click them again" % e
        return (cam, W, H, cl), ""

    def cpeak_pitch(self):
        """The roof's pitch (degrees) from the peak of the end wall clicked on the corner photo, or None."""
        pk = self.f.get('cpeak')
        got, _why = self.cdepth_cam()
        if not pk or not got:
            return None
        cam, W, H, cl = got
        M = self.M
        o4, d4 = M.ray(cam, cl[3][0] * W, cl[3][1] * H)
        o6, d6 = M.ray(cam, cl[5][0] * W, cl[5][1] * H)
        if abs(d4[2]) < 1e-9 or abs(d6[2]) < 1e-9:
            return None
        h = cam['C'][2] + (1.0 if d4[2] > 0 else -1.0)    # the roof edge on a level plane (any height will do)
        p4 = M.hit_level(cam, cl[3][0] * W, cl[3][1] * H, h)
        p6 = M.hit_level(cam, cl[5][0] * W, cl[5][1] * H, h)
        if p4 is None or p6 is None:
            return None
        mid = M.v_mul(M.v_add(p4, p6), 0.5)
        o, d = M.ray(cam, pk[0] * W, pk[1] * H)
        r = M.up_line(o, d, mid)
        if r is None:
            return None
        rise, half = r[0] - h, M.v_len(M.v_sub(p6, p4)) / 2.0
        if rise <= 1e-9 or half <= 1e-9:
            return None
        return math.degrees(math.atan2(rise, half))

    def cdepth_ratio(self):
        """Depth / length from the 6 corners clicked on the corner photo: (ratio or None, what's wrong)."""
        cd = self.f.get('cdepth') or {}
        cl = cd.get('clicks') or []
        path = self.cdepth_photo()
        if len(cl) < 6 or not path:
            return None, "click the 6 corners on the corner photo"
        if path not in self._sizes:
            self._sizes[path] = photo_size(path)
        W, H = self._sizes[path] or (1000, 750)
        M = self.M
        lines = {'r1': [cl[0][:2], cl[2][:2]], 'r2': [cl[1][:2], cl[3][:2]],
                 'g1': [cl[2][:2], cl[4][:2]], 'g2': [cl[3][:2], cl[5][:2]]}
        try:
            cam = M.solve_camera(lines, W, H)
        except Exception as e:
            return None, "those corners don't fit together (%s) - Ctrl+Z and click them again" % e
        def level_ratio(pts):
            """side / front from three points at one height (any height: the ratio is the same)."""
            rays = [M.ray(cam, c[0] * W, c[1] * H) for c in pts]
            dz = [d[2] for _o, d in rays]
            if all(z_ > 1e-9 for z_ in dz):
                h = cam['C'][2] + 1.0                     # above the eye: a level plane over it
            elif all(z_ < -1e-9 for z_ in dz):
                h = cam['C'][2] - 1.0
            else:
                return None                               # the skyline runs between them
            g = [M.hit_level(cam, c[0] * W, c[1] * H, h) for c in pts]
            if any(q is None for q in g):
                return None
            front = M.v_len(M.v_sub(g[1], g[0]))
            side = M.v_len(M.v_sub(g[2], g[1]))
            return side / front if front > 1e-9 and side > 1e-9 else None
        r = level_ratio((cl[1], cl[3], cl[5]))           # the roof-edge corners
        if r is None:
            r = level_ratio((cl[0], cl[2], cl[4]))       # else the lower ones
        if r is None:
            return None, "the corners don't measure - Ctrl+Z and click them again"
        return r, ""

    def photo_role(self, path):
        f = self.f
        if path == f.get('photo'):
            return "Front"
        if path == (f.get('roof_side') or {}).get('photo') and self.ridge_how() == 'side':
            return "Roof side"
        if path == (f.get('side') or {}).get('photo') and f.get('depth_how') == 'side':
            return "Side"
        if f.get('depth_how') == 'cphoto' and path == self.cdepth_photo():
            return "Corner"
        if path == self.photo0:
            return "Corner"
        return ""

    def _tab(self, i):
        if self.busy or not 0 <= i < len(self._tab_paths):
            return
        path = self._tab_paths[i]
        f, pg = self.f, self.page()
        if path != self.step_photo():
            # a side photo not clicked on yet: this one's it
            if pg == 2 and self.ridge_how() == 'side' and not self.gable_mode and \
                    not (f.get('roof_side') or {}).get('clicks') and path != f.get('photo'):
                self.remember()
                f['roof_side'] = {'photo': path, 'clicks': []}
                path = None
            elif pg == 5 and f.get('depth_how') == 'side' and not (f.get('side') or {}).get('quad') and \
                    path != f.get('photo'):
                self.remember()
                f['side'] = {'photo': path, 'quad': []}
                path = None
            elif pg == 5 and f.get('depth_how') == 'cphoto' and not (f.get('cdepth') or {}).get('clicks') and \
                    path != f.get('photo'):
                self.remember()
                f['cdepth'] = {'photo': path, 'clicks': []}
                path = None
        self.peek = path if path and path != self.step_photo() else None
        self.pending, self.trace = None, []
        self.show_photo()
        self.update_all()

    def _fill_tabs(self):
        ps = self.photos()
        here, shown = self.step_photo(), self.cur_photo()
        self._tab_paths = list(ps)
        while self.tabs.count():
            self.tabs.removeTab(0)
        for p_ in ps:
            role = self.photo_role(p_)
            self.tabs.addTab(("● " if p_ == here else "") + (role + ": " if role else "") + os.path.basename(p_))
        if shown in ps:
            self.tabs.setCurrentIndex(ps.index(shown))

    def show_photo(self):
        path = self.cur_photo() or ''
        if path not in self.pixes:
            self.pixes[path] = load_photo(path) if path and os.path.isfile(path) else None
        self.view.set_pixmap(self.pixes[path])

    def _front_photo(self, i):
        if self.busy or i < 0:
            return
        ps = self.photos()
        if i < len(ps) and ps[i] != self.f.get('photo'):
            self.remember()
            self._switch_front(ps[i])
            self.peek = None
            self.show_photo()
            self.update_all()

    def _side_photo(self, i):
        if self.busy or i < 0:
            return
        ps = self.photos()
        if i < len(ps):
            self.remember()
            self.f['side'] = {'photo': ps[i], 'quad': []}
            self.f['depth_how'] = 'side'
            self.peek = None
            self.show_photo()
            self.update_all()

    # ---- the front, straightened: photo (0..1, up from the bottom) <-> mm along / up the wall ----
    def _size_px(self, quad, path):
        if path not in self._sizes:
            self._sizes[path] = photo_size(path) if path else None
        sz = self._sizes[path]
        W, H = sz if sz else (1000, 750)
        P = [(q[0] * W, q[1] * H) for q in quad]
        wpx = (math.hypot(P[1][0] - P[0][0], P[1][1] - P[0][1]) + math.hypot(P[2][0] - P[3][0], P[2][1] - P[3][1])) / 2
        hpx = (math.hypot(P[3][0] - P[0][0], P[3][1] - P[0][1]) + math.hypot(P[2][0] - P[1][0], P[2][1] - P[1][1])) / 2
        return W, H, P, wpx, hpx

    def wall(self):
        """(L, E, to_mm, to_photo) for the front, or None: L its length, E its height to the eaves (mm)."""
        f = self.f
        q = f.get('quad') or []
        if len(q) < 4:
            return None
        W, H, P, wpx, hpx = self._size_px(q, f.get('photo'))
        L, E = float(f.get('length_mm') or 0.0), float(f.get('eaves_mm') or 0.0)
        kn = f.get('known') or {}
        if L <= 0 and E <= 0 and len(kn.get('clicks') or []) == 2 and float(kn.get('mm') or 0) > 0:
            # something on the front you know the size of: scale the whole front from it
            r1 = [(0.0, 0.0), (1.0, 0.0), (1.0, hpx / max(wpx, 1e-6)), (0.0, hpx / max(wpx, 1e-6))]
            H1 = self.M.homography(P, r1)
            if H1 is not None:
                a_ = self.M.hmap(H1, kn['clicks'][0][0] * W, kn['clicks'][0][1] * H)
                b_ = self.M.hmap(H1, kn['clicks'][1][0] * W, kn['clicks'][1][1] * H)
                if a_ and b_ and math.hypot(b_[0] - a_[0], b_[1] - a_[1]) > 1e-9:
                    L = float(kn['mm']) / math.hypot(b_[0] - a_[0], b_[1] - a_[1])
        if L <= 0 and E <= 0:
            return None
        if L <= 0:
            L = E * wpx / max(hpx, 1e-6)
        if E <= 0:
            E = L * hpx / max(wpx, 1e-6)
        rect = [(0.0, 0.0), (L, 0.0), (L, E), (0.0, E)]
        Hm = self.M.homography(P, rect)
        Hi = self.M.homography(rect, P)
        if Hm is None or Hi is None:
            return None

        def to_mm(c):
            return self.M.hmap(Hm, c[0] * W, c[1] * H) or (0.0, 0.0)

        def to_photo(s, z):
            u, v = self.M.hmap(Hi, s, z) or (0.0, 0.0)
            return u / W, v / H
        return L, E, to_mm, to_photo

    def depth(self):
        """The main building's depth (mm), and where it came from - or (0, why not)."""
        f = self.f
        how = f.get('depth_how', 'type')
        if how == 'type':
            d_ = float(f.get('depth_mm') or 0.0)
            return (d_, "typed") if d_ > 0 else (0.0, "type the depth (step 5)")
        w = self.wall()
        if w is None:
            return 0.0, "the front comes first (step 1)"
        L, E = w[0], w[1]
        if how == 'side':
            sd = f.get('side') or {}
            q = sd.get('quad') or []
            if len(q) < 4:
                return 0.0, "click the side wall's 4 corners on its photo (step 5)"
            _W, _H, _P, wpx, hpx = self._size_px(q, sd.get('photo'))
            return E * wpx / max(hpx, 1e-6), "from the side photo"
        if how == 'cphoto':
            r, why = self.cdepth_ratio()
            return (L * r, "from the corner photo") if r else (0.0, why)
        r = self.corner_ratio()
        if r is None:
            return 0.0, ("the corner photo's main building corners aren't done - click them the other way (Start "
                         "clicking round the building), or pick another way")
        return L * r, "from the corner photo"

    def _ratio_from(self, folder):
        """Depth / length of the main building in a job's corner-photo clicks, if they're done (cached)."""
        cp = os.path.join(folder or '', CLICKS_NAME)
        try:
            mt = os.path.getmtime(cp)
        except Exception:
            return None
        cache = self._ratios
        if cache.get(cp, (None,))[0] == mt:
            return cache[cp][1]
        r = self._ratio_file(cp)
        cache[cp] = (mt, r)
        return r

    def corner_job(self):
        """The job whose corner photo gives the depth: picked, this one, or the newest done one with the same
        building's photos. Returns (folder, ratio) or (None, None)."""
        picked = self.f.get('corner_job')
        for fo in ([picked] if picked else []) + [self.folder]:
            r = self._ratio_from(fo)
            if r:
                return fo, r
        if self._auto_job == 0:                            # look round the other jobs once
            self._auto_job = None
            names = set(os.path.basename(p_ or '').lower() for p_ in self.photos())
            parent = os.path.dirname(self.folder)
            cands = []
            try:
                for nm in os.listdir(parent):
                    fo = os.path.join(parent, nm)
                    cp = os.path.join(fo, CLICKS_NAME)
                    if fo == self.folder or not os.path.isfile(cp):
                        continue
                    try:
                        with open(cp, "r", encoding="utf-8") as fh:
                            d = json.load(fh).get('clicks') or {}
                        used = set(os.path.basename(ph.get('path') or '').lower() for ph in d.get('photos') or [])
                    except Exception:
                        continue
                    if used & names:
                        cands.append((os.path.getmtime(cp), fo))
            except Exception:
                pass
            for _mt, fo in sorted(cands, reverse=True):
                if self._ratio_from(fo):
                    self._auto_job = fo
                    break
        fo = self._auto_job
        r = self._ratio_from(fo) if fo else None
        return (fo, r) if r else (None, None)

    def pick_corner_job(self):
        """A list of the jobs with a corner photo clicked: a picture of each, when, and the depth it gives."""
        from PySide6.QtWidgets import QDialogButtonBox
        from PySide6.QtGui import QIcon
        from PySide6.QtCore import QSize as _QSize
        parent = os.path.dirname(self.folder)
        w = self.wall()
        rows = []
        try:
            names = os.listdir(parent)
        except Exception:
            names = []
        for nm in names:
            fo = os.path.join(parent, nm)
            cp = os.path.join(fo, CLICKS_NAME)
            if not os.path.isfile(cp):
                continue
            try:
                with open(cp, "r", encoding="utf-8") as fh:
                    d = json.load(fh).get('clicks') or {}
                ph = ((d.get('photos') or [{}])[0] or {}).get('path') or ''
            except Exception:
                continue
            r = self._ratio_from(fo)
            rows.append((bool(r), os.path.getmtime(cp), fo, ph, r))
        if not rows:
            self.say("There aren't any jobs with a corner photo clicked yet - click one the other way first "
                     "(Start clicking round the building).", True)
            return
        rows.sort(key=lambda t: (not t[0], -t[1]))         # the done ones first, newest first
        dlg = QDialog(self)
        dlg.setWindowTitle("Which corner photo? - %s" % PLUGIN_NAME)
        lay = QVBoxLayout(dlg)
        lay.addWidget(_note("Pick the job where you clicked round this building on a corner photo. The ones with "
                            "their corners done are at the top.", True))
        lst = QListWidget()
        lst.setIconSize(_QSize(120, 90))
        lst.setMinimumSize(620, 420)
        for done, mt, fo, ph, r in rows:
            when = time.strftime("%a %d %b, %H:%M", time.localtime(mt))
            txt = "%s   -   %s\n%s" % (when, os.path.basename(ph) or "(no photo)",
                                       ("Corners done ✓   depth %.0f mm" % (w[0] * r)) if (done and w) else
                                       ("Corners done ✓" if done else "Corners not finished"))
            it = QListWidgetItem(txt)
            pix = self._thumb(ph)
            if pix is not None:
                it.setIcon(QIcon(pix))
            it.setData(Qt.UserRole, fo)
            if not done:
                it.setForeground(Qt.gray)
            lst.addItem(it)
        lst.setCurrentRow(0)
        lay.addWidget(lst)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lst.itemDoubleClicked.connect(lambda _it: dlg.accept())
        lay.addWidget(bb)
        if not dlg.exec() or lst.currentItem() is None:
            return
        fo = lst.currentItem().data(Qt.UserRole)
        if not fo:
            return
        if not self._ratio_from(fo):
            self.say("That job's corner photo isn't done (its main building's corners) - pick another.", True)
            return
        self.remember()
        self.f['corner_job'] = fo
        self.f['depth_how'] = 'corner'
        self.update_all()

    def _thumb(self, path):
        cache = self.__dict__.setdefault('_thumbs', {})
        if path not in cache:
            pm = None
            try:
                if path and os.path.isfile(path):
                    big = load_photo(path)
                    if big is not None:
                        pm = big.scaled(120, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            except Exception:
                pm = None
            cache[path] = pm
        return cache[path]

    @staticmethod
    def _fill_bay_sides(parts, ops):
        """Splayed bays: a side with no windows gets the other side's, mirrored; and a bay with no side windows
        gets another splayed bay's. (A splayed bay's walls: 0 the front, 1 the right side, 3 the left side.)"""
        def wlen(cs, wi):
            a, b = cs[wi % len(cs)], cs[(wi + 1) % len(cs)]
            return math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0

        def moved(o, pi, wall, mirror, scale):
            o2 = dict(o, part=pi, wall=wall)
            o2.pop('box', None)                            # a copy: not a box on the photo
            o2.pop('box2', None)
            L2 = wlen(parts[pi]['corners'], wall)
            if mirror:
                o2['s0'], o2['s1'] = round(L2 - o['s1'] * scale, 1), round(L2 - o['s0'] * scale, 1)
                if o.get('shape'):
                    o2['shape'] = [[round(L2 - s_ * scale, 1), z] for s_, z in reversed(o['shape'])]
            else:
                o2['s0'], o2['s1'] = round(o['s0'] * scale, 1), round(o['s1'] * scale, 1)
                if o.get('shape'):
                    o2['shape'] = [[round(s_ * scale, 1), z] for s_, z in o['shape']]
            return o2
        bays = [i for i, pr in enumerate(parts) if i > 0 and pr.get('against') and len(pr['corners']) == 4 and
                pr.get('shape') == 'own']
        side = {(i, w): [o for o in ops if o['part'] == i and o['wall'] == w] for i in bays for w in (1, 3)}

        def area(lst):
            return sum((o['s1'] - o['s0']) * (o['z1'] - o['z0']) for o in lst)
        for i in bays:                                     # both sides clicked: the one seen best, both sides
            a1, a3 = area(side[(i, 1)]), area(side[(i, 3)])
            if a1 > 0 and a3 > 0 and abs(a1 - a3) > 0.1 * max(a1, a3):
                big, small = (1, 3) if a1 > a3 else (3, 1)
                scale = wlen(parts[i]['corners'], small) / wlen(parts[i]['corners'], big)
                drop = set(id(o) for o in side[(i, small)])
                ops = [o for o in ops if id(o) not in drop]
                side[(i, small)] = [moved(o, i, small, True, scale) for o in side[(i, big)]]
                ops = ops + side[(i, small)]
        extra = []
        for i in bays:
            for w, other in ((1, 3), (3, 1)):
                if side[(i, w)]:
                    continue
                src = None
                if side[(i, other)]:                       # the other side of this bay, mirrored
                    src = (i, other, True)
                else:
                    for j in bays:
                        if j == i:
                            continue
                        if side[(j, w)]:
                            src = (j, w, False)
                            break
                        if side[(j, other)]:
                            src = (j, other, True)
                            break
                if src is None:
                    continue
                j, wj, mir = src
                scale = wlen(parts[i]['corners'], w) / wlen(parts[j]['corners'], wj)
                extra += [moved(o, i, w, mir, scale) for o in side[(j, wj)]]
        return ops + extra

    def gable_pitch(self):
        """The front gables' pitch (degrees, their average), or None."""
        w = self.wall()
        if w is None:
            return None
        to_mm = w[2]
        ps = []
        for g in self.f.get('gables') or []:
            cl = g.get('clicks') or []
            if len(cl) < 3:
                continue
            p0, p1, pk = sorted((to_mm(c) for c in cl[:3]), key=lambda q_: q_[1])
            half = abs(p1[0] - p0[0]) / 2.0
            rise = pk[1] - (p0[1] + p1[1]) / 2.0
            if half > 1.0 and rise > 1.0:
                ps.append(math.degrees(math.atan2(rise, half)))
        return sum(ps) / len(ps) if ps else None

    def side_pitch(self):
        """The roof's pitch (degrees) from the triangle drawn on the side photo, or None. Each slope is measured
        on its own and the two averaged, so a photo a little off square still comes out close."""
        rs = self.f.get('roof_side') or {}
        cl = rs.get('clicks') or []
        if len(cl) < 3 or not rs.get('photo'):
            return None
        path = rs['photo']
        if path not in self._sizes:
            self._sizes[path] = photo_size(path) if path else None
        W, H = self._sizes[path] or (1000, 750)
        pts = sorted(((c[0] * W, c[1] * H) for c in cl[:3]), key=lambda q: q[1])
        e1, e2, pk = pts
        ps = []
        for e in (e1, e2):
            run, rise = abs(pk[0] - e[0]), pk[1] - e[1]
            if run > 1.0 and rise > 1.0:
                ps.append(math.degrees(math.atan2(rise, run)))
        if len(ps) < 2 or (e1[0] - pk[0]) * (e2[0] - pk[0]) >= 0:
            return None                                   # the ridge isn't between the two eaves
        return sum(ps) / len(ps)

    def _roof_side_photo(self, i):
        if self.busy or i < 0:
            return
        ps = self.photos()
        if i < len(ps) and ps[i] != (self.f.get('roof_side') or {}).get('photo'):
            self.remember()
            self.f['roof_side'] = {'photo': ps[i], 'clicks': []}
            self.peek = None
            self.show_photo()
            self.update_all()

    def _roof_tri_clear(self):
        rs = self.f.get('roof_side') or {}
        if rs.get('clicks'):
            self.remember()
            rs['clicks'] = []
            self.update_all()

    def ridge_how(self):
        """Where the main roof's height comes from: 'gables' (their pitch), 'click' or 'pitch' (typed)."""
        h = self.f.get('ridge_how')
        if h in ('click', 'pitch', 'side'):
            return h
        if h == 'peak':
            return 'peak' if self.gable_pitch() else 'click'
        if h == 'cpeak':
            return 'cpeak'
        if h == 'gables' or h is None:
            return 'gables' if self.gable_pitch() else 'click'
        return 'click'

    def corner_ratio(self):
        """Depth / length of the main building as clicked on the corner photo (the other way), if it's done."""
        return self.corner_job()[1]

    def _ratio_file(self, cp):
        try:
            with open(cp, "r", encoding="utf-8") as fh:
                d = json.load(fh).get('clicks')
            if not isinstance(d, dict):
                return None
            self.M.migrate(d)
            m = self.M.compute(d)
            ol = m.get('outline')
            if not ol:
                return None
            fr = self.M.plan_frame(ol)
            pl = [self.M.to_plan(fr, p_) for p_ in ol]
            ln = max(p_[0] for p_ in pl) - min(p_[0] for p_ in pl)
            dp = max(p_[1] for p_ in pl) - min(p_[1] for p_ in pl)
            return dp / ln if ln > 1e-9 else None
        except Exception:
            return None

    # ---- the building from it all (mm) ----
    def build(self, guess_depth=False):
        """The building, as the Build page takes it. Raises ValueError saying what's missing."""
        M, f = self.M, self.f
        w = self.wall()
        if w is None:
            raise ValueError("Click the front wall's 4 corners and type its length (step 1).")
        L, E, to_mm, _tp = w
        D, why = self.depth()
        if D <= 0 and guess_depth:
            D = max(3000.0, min(0.5 * L, 9000.0))          # the preview only: a likely depth till it's set
        if D <= 0:
            raise ValueError("The depth: " + why + ".")
        main = {'name': "Main building", 'corners': [[0.0, 0.0], [L, 0.0], [L, D], [0.0, D]], 'shape': 'rect',
                'storeys': int(f.get('storeys') or 1), 'against': False, 'length': round(L, 1), 'width': round(D, 1)}
        ridge = 0.0
        roof_ = f.get('roof')
        run = {'gable_len': D / 2.0, 'gable_across': L / 2.0, 'hip': min(L, D) / 2.0, 'mono': D}.get(roof_, D / 2.0)
        how_r = self.ridge_how()
        if roof_ not in ('flat', 'none'):
            if how_r == 'gables':
                ridge = E + math.tan(math.radians(self.gable_pitch() or 40.0)) * run
            elif how_r == 'pitch':
                ridge = E + math.tan(math.radians(float(f.get('roof_pitch') or 40.0))) * run
            elif how_r == 'cpeak':
                cp_ = self.cpeak_pitch()
                if not cp_:
                    raise ValueError("Click the 6 corners and the peak of the end wall on the corner photo (step 2).")
                ridge = E + math.tan(math.radians(cp_)) * run
            elif how_r == 'peak':
                pk = [max((to_mm(c)[1] for c in (g.get('clicks') or [])[:3]), default=0.0)
                      for g in f.get('gables') or [] if len(g.get('clicks') or []) >= 3]
                ridge = max(pk) if pk else 0.0
            elif how_r == 'side':
                sp_ = self.side_pitch()
                if not sp_:
                    raise ValueError("Draw the roof's triangle on the side photo (step 2): the left eave, the "
                                     "ridge, the right eave.")
                ridge = E + math.tan(math.radians(sp_)) * run
            elif f.get('ridge'):
                ridge = to_mm(f['ridge'])[1]
        if roof_ not in ('flat', 'none') and ridge <= E:
            raise ValueError("Click the very top of the roof (step 2).")
        main.update(M._roof_info({'roof': f.get('roof'), 'roof_low': f.get('roof_low')}, main['corners'], E, ridge))
        parts, spans = [main], [(0.0, L, 0.0, E, 0.0, None)]    # each part's front: s from, s to, z.., x0, outline
        nb = nw = 0
        for bx in f.get('parts') or []:
            cl = bx.get('clicks') or []
            if len(cl) < 2:
                continue
            (s0, z0), (s1, z1) = to_mm(cl[0]), to_mm(cl[1])
            a, b = min(s0, s1), max(s0, s1)
            top = max(z0, z1)
            out = float(bx.get('out') or (900.0 if bx['kind'] == 'bay' else 3000.0))
            if bx['kind'] == 'bay':
                nb += 1
                shape = bx.get('shape', 'square')
                if shape == 'splayed':
                    fw = float(bx.get('front') or 0.0)
                    fc = bx.get('front_clicks') or []
                    if len(fc) == 2:                       # its flat front, clicked
                        fw = abs(to_mm(fc[1])[0] - to_mm(fc[0])[0])
                    if fw <= 0 or fw >= b - a:
                        fw = 0.6 * (b - a)
                    fl = (a + b) / 2.0 - fw / 2.0
                    if len(fc) == 2:
                        fl = min(to_mm(fc[0])[0], to_mm(fc[1])[0])
                    cs = [[fl, -out], [fl + fw, -out], [b, 0.0], [a, 0.0]]
                elif shape == 'round':                     # a bow: round from wall to wall
                    nseg = 8
                    arc = [((a + b) / 2.0 - (b - a) / 2.0 * math.cos(math.pi * t / nseg),
                            -out * math.sin(math.pi * t / nseg)) for t in range(nseg + 1)]
                    cs = [list(q_) for q_ in arc]
                else:
                    cs = [[a, -out], [b, -out], [b, 0.0], [a, 0.0]]
                name, against = "Bay %d" % nb, True
            else:
                nw += 1
                y0 = float(bx.get('back') or 0.0)
                cs = [[a, y0], [b, y0], [b, y0 + out], [a, y0 + out]]
                name, against = "Wing %d" % nw, False
            roof = bx.get('roof') or ('mono' if bx['kind'] == 'bay' else 'gable_len')
            pitch = math.radians(float(bx.get('pitch') or 30.0))
            run = {'gable_len': out / 2.0, 'gable_across': (b - a) / 2.0, 'hip': min(b - a, out) / 2.0,
                   'mono': out}.get(roof, out / 2.0)
            rd = top + math.tan(pitch) * run if roof not in ('flat', 'none') else 0.0
            pr = {'name': name, 'corners': [[round(x, 1), round(y, 1)] for x, y in cs],
                  'shape': 'rect' if len(cs) == 4 and (bx['kind'] != 'bay' or bx.get('shape', 'square') == 'square')
                  else 'own', 'storeys': 1, 'against': against, 'length': round(b - a, 1), 'width': round(out, 1)}
            pr.update(M._roof_info({'roof': roof, 'roof_low': 'front'}, pr['corners'], top, rd))
            parts.append(pr)
            spans.append((a, b, 0.0, top, a, cs))
        ops = []
        for bi_, o in enumerate(f.get('boxes') or []):
            cl = o.get('clicks') or []
            if len(cl) < 2:
                continue
            pts = [to_mm(c) for c in cl]
            a, b = min(q_[0] for q_ in pts), max(q_[0] for q_ in pts)
            lo, hi = min(q_[1] for q_ in pts), max(q_[1] for q_ in pts)
            mid = (a + b) / 2.0
            pi = 0
            for k in range(len(spans) - 1, 0, -1):              # on a bay or wing if it's within its front
                sa, sb, _za, zb, _x0, _cs = spans[k]
                if sa <= mid <= sb and hi <= zb + 50.0:
                    pi = k
                    break
            x0, pcs = spans[pi][4], spans[pi][5]
            wall, along = 0, (lambda x: x - x0)
            if pcs is not None and pi > 0:                 # which face of the bay or wing it's on
                bestw = None
                for wi in range(len(pcs)):
                    pa_, pb_ = pcs[wi], pcs[(wi + 1) % len(pcs)]
                    if abs(pb_[0] - pa_[0]) < 1.0 or max(pa_[1], pb_[1]) >= -1.0 and min(pa_[1], pb_[1]) >= -1.0 \
                            and pcs is not None and parts[pi]['against']:
                        continue                           # upright in the photo, or the back (against the wall)
                    if min(pa_[0], pb_[0]) - 1.0 <= mid <= max(pa_[0], pb_[0]) + 1.0:
                        yy = (pa_[1] + pb_[1]) / 2.0
                        if bestw is None or yy < bestw[0]:
                            bestw = (yy, wi, pa_, pb_)
                if bestw is not None:
                    _yy, wall, pa_, pb_ = bestw
                    seg = math.hypot(pb_[0] - pa_[0], pb_[1] - pa_[1])
                    dx = pb_[0] - pa_[0]
                    along = (lambda x, pa_=pa_, dx=dx, seg=seg: min(max((x - pa_[0]) / dx * seg, 0.0), seg))
            traced = o.get('top') == 'traced' and len(pts) >= 3
            sa_, sb_ = sorted((along(a), along(b)))
            ops.append({'kind': o.get('kind', 'window'), 'top': o.get('top', 'square'), 'part': pi, 'wall': wall,
                        's0': round(sa_, 1), 's1': round(sb_, 1), 'z0': round(max(lo, 0.0), 1),
                        'z1': round(hi, 1),
                        'shape': _square_up(_ccw([[round(along(q_[0]), 1), round(max(q_[1], 0.0), 1)] for q_ in pts]))
                        if traced
                        else None, 'box': bi_})
            md = o.get('model')
            if md and pi > 0 and len(md.get('clicks') or []) == len(cl) and all(
                    abs(p_[0] - q_[0]) < 1e-6 and abs(p_[1] - q_[1]) < 1e-6 for p_, q_ in zip(md['clicks'], cl)):
                # moved on the model since, and its box not changed on the photo: where it was put on the bay
                ops[-1].update({'part': int(md['part']), 'wall': int(md['wall']), 's0': md['s0'], 's1': md['s1'],
                                'z0': md['z0'], 'z1': md['z1'], 'shape': md.get('shape'),
                                'top': md.get('top') or ops[-1]['top']})
        ops = join_fanlights(ops)
        if f.get('bay_sides', True):
            ops = self._fill_bay_sides(parts, ops)
        gables = []
        for g in f.get('gables') or []:
            cl = g.get('clicks') or []
            if len(cl) < 3:
                continue
            p0, p1, pk = sorted((to_mm(c) for c in cl[:3]), key=lambda q_: q_[1])
            if pk[1] <= E + 50.0:
                continue                                  # its peak isn't above the eaves
            gables.append({'part': 0, 'wall': 0, 's0': round(min(p0[0], p1[0]), 1), 's1': round(max(p0[0], p1[0]), 1),
                           'z0': round(E, 1), 'peak': round(pk[1], 1)})     # they stand at the main eaves
        out = dict(parts[0])
        try:
            Wf, Hf, Pf, _wp, _hp = self._size_px(f.get('quad') or [], f.get('photo'))
            front_map = {'P': [list(q_) for q_ in Pf], 'W': Wf, 'H': Hf, 'L': L, 'E': E}
        except Exception:
            front_map = None
        out.update({'front_map': front_map})
        out.update({'version': 2, 'made': time.strftime("%Y-%m-%d %H:%M:%S"), 'parts': parts, 'openings': ops,
                    'gables': gables, 'eave_over': float(f.get('eave_over', 300.0)),
                    'verge_over': float(f.get('verge_over', 300.0)), 'boards': bool(f.get('boards', True)),
                    'known_what': 'front_length', 'known_mm': round(L, 1), 'lens35': 0.0,
                    'from': "front photo", 'depth_from': why})
        return out

    # ---- clicking ----
    def _known_mode(self, on):
        if self.busy:
            return
        self.known_mode = bool(on)
        if on:
            self.remember()
            self.f['known'] = {'clicks': [], 'mm': float((self.f.get('known') or {}).get('mm') or 0.0)}
        self.update_all()

    def _quad_again(self):
        if self.busy:
            return
        self.remember()
        self.f['quad'] = []
        self.update_all()

    def step1_next(self):
        """What step 1 still needs: (number of corners clicked, the text for the yellow box, done)."""
        f = self.f
        q = f.get('quad') or []
        corners = ["the <b>BOTTOM LEFT</b> corner of the front wall<br><small>where it meets the ground</small>",
                   "the <b>BOTTOM RIGHT</b> corner<br><small>where it meets the ground</small>",
                   "the <b>TOP RIGHT</b> corner<br><small>just under the edge of the roof</small>",
                   "the <b>TOP LEFT</b> corner<br><small>just under the edge of the roof</small>"]
        if not self.photos():
            return 0, "Add the photo taken <b>straight on to the front</b> (Another photo...).", False
        if self.known_mode:
            n = len((f.get('known') or {}).get('clicks') or [])
            return len(q), "On the photo, click %s." % (
                "<b>one end</b> of the thing you know the size of" if n == 0 else "its <b>other end</b>"), False
        if len(q) < 4:
            return len(q), "Click %s<br><small>(%d of 4)</small>" % (corners[len(q)], len(q) + 1), False
        kn = f.get('known') or {}
        sized = float(f.get('length_mm') or 0) > 0 or (len(kn.get('clicks') or []) == 2 and
                                                        float(kn.get('mm') or 0) > 0)
        if not sized:
            if len(kn.get('clicks') or []) == 2:
                return 4, ("Now type its size in the box <b>2. How long is it?</b> below<br>"
                           "<small>e.g. a door 2000 mm high, a bench 1800 mm long</small>"), False
            return 4, "Corners done ✓<br>Now type <b>how long the front is</b> (a map is good for this).", False
        return 4, "<b>Step 1 done ✓</b><br>Check the floors, then press <b>Next ▸</b>", True

    def _known_mm(self, v):
        if self.busy:
            return
        self.remember()
        self.f.setdefault('known', {'clicks': []})['mm'] = float(v)
        self.update_all()

    def page(self):
        """Which page this step is (the steps are in a different order from the pages)."""
        return FORDER[min(max(1, int(self.f.get('step') or 1)), 6) - 1]

    def mode(self):
        st = self.page()
        if st == 1 and self.known_mode:
            return 'known'
        if st == 1:
            return 'quad'
        if st == 2:
            if self.gable_mode:
                return 'gable'
            if self.step2_next()[0] in ('shape', 'gq', 'rhow'):
                return 'nojob'
            if self.ridge_how() == 'cpeak':
                return 'cdepth' if len((self.f.get('cdepth') or {}).get('clicks') or []) < 6 else 'cpeak'
            return 'rtri' if self.ridge_how() == 'side' else 'ridge'
        if st == 3:
            return 'linepick' if self.line_mode else 'box'
        if st == 4:
            jb = self.f.get('_job') or {}
            if jb.get('stage') == 'click':
                return 'job'
            return 'front' if self.front_mode else 'nojob'
        if st == 5 and self.f.get('depth_how') == 'side':
            return 'side'
        if st == 5 and self.f.get('depth_how') == 'cphoto':
            return 'cdepth'
        return None

    def photo_press(self, n, pos):
        if self.peek:
            self.say("Just looking at this photo - click the tab with the dot (●) to carry on clicking.", True)
            return
        f, what = self.f, self.mode()
        if not what:
            return
        if what == 'linepick':
            from PySide6.QtWidgets import QApplication as _QA
            k = self.box_at(c)
            if k is None:
                self.say("Click on a window (inside its box).", True)
                return
            if _QA.keyboardModifiers() & Qt.ShiftModifier and self.line_sel:
                if k in self.line_sel[1:]:
                    self.line_sel.remove(k)
                elif k != self.line_sel[0]:
                    self.line_sel.append(k)
            else:
                self.line_sel = [k]
            self.update_all()
            return
        if what == 'nojob' and self.page() == 2:
            self.say("Answer the question on the right first.", True)
            return
        if what == 'nojob':
            jb = f.get('_job') or {}
            self.say("Pick its shape on the right first." if jb.get('stage') == 'shape' else
                     "Set how far it comes out and its roof on the right, then Done." if jb.get('stage') == 'size'
                     else "Press  + Add a bay  (or a wing) on the right first.", True)
            return
        if what == 'rtri':
            self.roof_tri_press(n, pos)
            return
        if what not in ('quad', 'side', 'known') and self.wall() is None:
            self.say("Do the front first (step 1): its 4 corners and its length.", True)
            return
        self.remember()
        c = [n[0], n[1]]
        prev = self._prev_click(what)
        if prev is not None and self._shift():          # Shift: level with / straight above the last click
            path = self.cur_photo()
            if path not in self._sizes:
                self._sizes[path] = photo_size(path) if path else None
            W_, H_ = self._sizes[path] or (1000, 750)
            if abs((c[0] - prev[0]) * W_) >= abs((c[1] - prev[1]) * H_):
                c[1] = prev[1]
            else:
                c[0] = prev[0]
        if what in ('box', 'part'):
            c = list(self.snap(c, what)[0])
        jb_ = f.get('_job') or {}
        if what == 'job':
            n_ = len(jb_.get('clicks') or [])
            if n_ == 0 or n_ == self.job_need() - 1:      # its corners line up with the others
                c = list(self.snap(c, 'part')[0])
        if what == 'known':
            kn = f.setdefault('known', {'clicks': [], 'mm': 0.0})
            kn.setdefault('clicks', []).append(c)
            if len(kn['clicks']) >= 2:
                kn['clicks'] = kn['clicks'][-2:]
                self.known_mode = False
        elif what == 'quad':
            if len(f['quad']) >= 4:
                self.history.pop()
                self.say("The front's 4 corners are clicked - Undo (Ctrl+Z) to move them.", True)
                return
            f['quad'].append(c)
        elif what == 'cpeak':
            f['cpeak'] = c
        elif what == 'cdepth':
            cd = f.setdefault('cdepth', {'photo': None, 'clicks': []})
            if not cd.get('photo'):
                cd['photo'] = self.cdepth_photo()
            q = cd.setdefault('clicks', [])
            if len(q) >= 6:
                self.history.pop()
                self.say("The 6 corners are clicked - Ctrl+Z to move them.", True)
                return
            q.append(c)
        elif what == 'side':
            q = f.setdefault('side', {'photo': None, 'quad': []}).setdefault('quad', [])
            if len(q) >= 4:
                self.history.pop()
                self.say("The side's 4 corners are clicked - Undo (Ctrl+Z) to move them.", True)
                return
            q.append(c)
        elif what == 'ridge':
            f['ridge'] = c
        elif what == 'gable':
            gl = f.setdefault('gables', [])
            if not gl or len(gl[-1]['clicks']) >= 3:
                gl.append({'clicks': []})
            gl[-1]['clicks'].append(c)
        elif what == 'box' and self.how_f == 'outline':
            self.history.pop()                             # each point: Backspace takes the last one off
            t0 = self.trace[0] if self.trace else None
            if t0 is not None and len(self.trace) >= 3 and abs(c[0] - t0[0]) < 0.015 and abs(c[1] - t0[1]) < 0.015:
                self.finish_trace()                        # back on its first point: that one's done
                self.save()
                self.say("Done ✓ - click round the next one.")
                return
            self.trace.append(c)
        elif what == 'box':
            if self.pending is None:
                self.pending = c
            else:
                f['boxes'].append({'kind': self.kind, 'top': self.top, 'clicks': [self.pending, c]})
                self.pending = None
        elif what == 'job':
            jb = f['_job']
            jb.setdefault('clicks', []).append(c)
            if len(jb['clicks']) >= self.job_need():
                cl = jb['clicks']
                src = jb.get('copy') or {}
                part = {'kind': jb['kind'], 'clicks': [cl[0], cl[-1]], 'shape': jb.get('shape', 'square'),
                        'out': src.get('out', 900.0 if jb['kind'] == 'bay' else 3000.0), 'back': 0.0,
                        'roof': src.get('roof', 'hip' if jb['kind'] == 'bay' else 'gable_len'),
                        'pitch': src.get('pitch', 30.0)}
                if part['shape'] == 'splayed' and len(cl) == 4:
                    part['front_clicks'] = [cl[1], cl[2]]
                f.setdefault('parts', []).append(part)
                self.sort_parts()
                self.sel_part = next(k_ for k_, q_ in enumerate(f['parts']) if q_ is part)
                if src:
                    part['shape'] = src.get('shape') or part['shape']
                    if part['shape'] == 'splayed' and src.get('front'):
                        part['front'] = float(src['front'])        # centred in its own box
                    f.pop('_job', None)
                    self.say("Done - the same as the one before. Add another, or Next.")
                else:
                    jb['stage'] = 'size'
                    jb['clicks'] = []
        elif what == 'front' and not (0 <= self.sel_part < len(f.get('parts') or [])):
            self.front_mode = False                     # no bay to give a flat front to: start a new bay
            self.pending = c
        elif what == 'front':
            ps = f.get('parts') or []
            if 0 <= self.sel_part < len(ps):
                fc = ps[self.sel_part].setdefault('front_clicks', [])
                fc.append(c)
                if len(fc) >= 2:
                    ps[self.sel_part]['front_clicks'] = fc[-2:]
                    self.front_mode = False
        elif what == 'part':
            if self.pending is None:
                self.pending = c
            else:
                f['parts'].append({'kind': self.box_kind, 'clicks': [self.pending, c], 'shape': 'square',
                                   'out': 900.0 if self.box_kind == 'bay' else 3000.0, 'back': 0.0,
                                   'roof': 'mono' if self.box_kind == 'bay' else 'gable_len', 'pitch': 30.0})
                self.pending = None
                self.sel_part = len(f['parts']) - 1
        self.update_all()

    def roof_tri_press(self, n, pos):
        """The triangle on the side photo: click its 3 corners, or grab one to drag it."""
        rs = self.f.get('roof_side') or {}
        if not rs.get('photo'):
            self.say("Pick the side photo first (or Another photo... to add one).", True)
            return
        cl = rs.setdefault('clicks', [])
        best = None
        for i, c in enumerate(cl):
            q = self.view.n2s(c[0], c[1])
            d = math.hypot(q.x() - pos.x(), q.y() - pos.y())
            if d < 14 and (best is None or d < best[0]):
                best = (d, i)
        self.remember()
        if best is not None:
            self.drag_tri = best[1]
            return
        if len(cl) >= 3:
            self.history.pop()
            self.say("The triangle's done - drag a corner to move it, or Start the triangle again.", True)
            return
        c = [n[0], n[1]]
        if cl and self._shift():                        # Shift: level with / straight above the last click
            path = rs['photo']
            if path not in self._sizes:
                self._sizes[path] = photo_size(path) if path else None
            W_, H_ = self._sizes[path] or (1000, 750)
            if abs((c[0] - cl[-1][0]) * W_) >= abs((c[1] - cl[-1][1]) * H_):
                c[1] = cl[-1][1]
            else:
                c[0] = cl[-1][0]
        cl.append(c)
        self.update_all()

    @staticmethod
    def _shift():
        try:
            from PySide6.QtGui import QGuiApplication
            return bool(QGuiApplication.keyboardModifiers() & Qt.ShiftModifier)
        except Exception:
            return False

    def _prev_click(self, what):
        """The click before, to line up with (Shift)."""
        f = self.f
        if what == 'known':
            cl = (f.get('known') or {}).get('clicks') or []
            return cl[-1] if len(cl) == 1 else None
        if what == 'quad':
            q = f.get('quad') or []
            return q[-1] if 0 < len(q) < 4 else None
        if what == 'side':
            q = (f.get('side') or {}).get('quad') or []
            return q[-1] if 0 < len(q) < 4 else None
        if what == 'box' and self.how_f == 'outline':
            return self.trace[-1] if self.trace else None
        if what == 'front':
            ps = f.get('parts') or []
            fc = ps[self.sel_part].get('front_clicks') or [] if 0 <= self.sel_part < len(ps) else []
            return fc[-1] if len(fc) == 1 else None
        if what in ('box', 'part'):
            return self.pending
        if what == 'rtri':
            cl = (f.get('roof_side') or {}).get('clicks') or []
            return cl[-1] if 0 < len(cl) < 3 else None
        if what == 'gable':
            gl = f.get('gables') or []
            return gl[-1]['clicks'][-1] if gl and 0 < len(gl[-1].get('clicks') or []) < 3 else None
        return None

    def snap(self, c, what):
        """Lines a window / door / bay corner up with the ones already done: their sills, tops and sides, and the
        same width and height as one of them. Returns (the click, guide lines [('s' | 'z', mm)])."""
        w = self.wall()
        if w is None or what not in ('box', 'part'):
            return c, []
        try:
            from PySide6.QtGui import QGuiApplication
            if QGuiApplication.keyboardModifiers() & Qt.ControlModifier:
                return c, []
        except Exception:
            pass
        L, E, to_mm, to_photo = w
        s_, z_ = to_mm(c)
        # how far it reaches: 7 pixels on the screen, in mm on the wall (so zoomed in, it hardly pulls)
        try:
            pa, pb = self.view.n2s(*to_photo(0.0, 0.0)), self.view.n2s(*to_photo(L, 0.0))
            screen_w = math.hypot(pb.x() - pa.x(), pb.y() - pa.y())
            tol = 7.0 * L / max(screen_w, 1.0)
        except Exception:
            tol = max(L, E) * 0.004
        ss, zs, ws, hs = [], [], [], []
        for key in ('boxes', 'parts'):
            for o in self.f.get(key) or []:
                cl = o.get('clicks') or []
                if len(cl) < 2:
                    continue
                pts = [to_mm(q) for q in cl]
                a, b = min(q[0] for q in pts), max(q[0] for q in pts)
                lo, hi = min(q[1] for q in pts), max(q[1] for q in pts)
                ss += [a, b]
                zs += [lo, hi]
                ws.append(b - a)
                hs.append(hi - lo)
        guides = []
        pend = to_mm(self.pending) if self.pending is not None else None

        def best(v, cands):
            got = None
            for x in cands:
                if abs(x - v) <= tol and (got is None or abs(x - v) < abs(got - v)):
                    got = x
            return got
        # a side or the same width (from the first corner)
        cs = list(ss)
        if pend is not None:
            cs += [pend[0] + wv for wv in ws] + [pend[0] - wv for wv in ws]
        g = best(s_, cs)
        if g is not None:
            s_ = g
            guides.append(('s', g))
        cz = list(zs)
        if pend is not None:
            cz += [pend[1] + hv for hv in hs] + [pend[1] - hv for hv in hs]
        g = best(z_, cz)
        if g is not None:
            z_ = g
            guides.append(('z', g))
        if not guides:
            return c, []
        return list(to_photo(s_, z_)), guides

    def photo_move(self, n, pos, held):
        if self.drag_tri is not None and held:
            cl = (self.f.get('roof_side') or {}).get('clicks') or []
            if self.drag_tri < len(cl):
                cl[self.drag_tri] = [n[0], n[1]]
                self.view.update()
            return
        self.hover = [n[0], n[1]]
        self.guides = []
        if self.mode() in ('box', 'part') and not (self.mode() == 'box' and self.how_f == 'outline'):
            c, self.guides = self.snap([n[0], n[1]], self.mode())
            self.hover = c
        self.view.setCursor(Qt.CrossCursor if self.mode() else Qt.ArrowCursor)

    def photo_release(self):
        if self.drag_tri is not None:
            self.drag_tri = None
            self.update_all()

    # ---- drawing over the photo ----
    def draw_overlay(self, p, vw):
        from PySide6.QtGui import QColor, QPen, QFont
        f, n2s = self.f, vw.n2s
        st = self.page()
        if self.peek:                                     # only a look: nothing's clicked on this one here
            return

        def text(q, s, c, size=11):
            fo = QFont(p.font())
            fo.setPointSizeF(size)
            fo.setBold(True)
            p.setFont(fo)
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(QPointF(q.x() + 1.5, q.y() + 1.5), s)
            p.setPen(c)
            p.drawText(q, s)

        def dot(q, c, r=5.0):
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawEllipse(q, r, r)
            p.setBrush(Qt.NoBrush)
        if st == 2 and self.ridge_how() == 'side' and not self.gable_mode:
            cl = (f.get('roof_side') or {}).get('clicks') or []
            pts = [n2s(c[0], c[1]) for c in cl]
            pink = QColor(255, 115, 230)
            p.setPen(QPen(pink, 2.5))
            for i in range(len(pts) - 1):
                p.drawLine(pts[i], pts[i + 1])
            if len(pts) == 3:
                lo = sorted(range(3), key=lambda i: cl[i][1])
                p.setPen(QPen(QColor(255, 150, 240, 160), 1.2, Qt.DashLine))
                p.drawLine(pts[lo[0]], pts[lo[1]])
            elif pts and self.hover:
                p.setPen(QPen(pink, 1.5, Qt.DashLine))
                p.drawLine(pts[-1], n2s(*self.hover))
            labs = ("left eave", "ridge", "right eave")
            for i, q_ in enumerate(pts):
                dot(q_, QColor(255, 255, 255) if i == self.drag_tri else pink, 6)
                text(QPointF(q_.x() + 9, q_.y() - 7), labs[i], QColor(255, 150, 240))
            sp_ = self.side_pitch()
            if sp_ and len(pts) == 3:
                top = min(pts, key=lambda q_: q_.y())
                text(QPointF(top.x() - 30, top.y() - 22), "%.1f°" % sp_, QColor(255, 255, 255), 14)
            return
        if (st == 5 and f.get('depth_how') == 'cphoto') or (st == 2 and self.ridge_how() == 'cpeak' and
                                                            not self.gable_mode):
            if st == 2 and f.get('cpeak'):
                q_ = n2s(*f['cpeak'][:2])
                dot(q_, QColor(255, 120, 230), 7)
                cpp = self.cpeak_pitch()
                text(QPointF(q_.x() + 9, q_.y() - 8), "the peak" + (" %.0f°" % cpp if cpp else ""),
                     QColor(255, 150, 240), 13)
            q = (f.get('cdepth') or {}).get('clicks') or []
            pts = [n2s(c[0], c[1]) for c in q]
            p.setPen(QPen(QColor(255, 90, 90), 2))
            for a_, b_ in ((0, 2), (1, 3)):
                if b_ < len(pts):
                    p.drawLine(pts[a_], pts[b_])
            p.setPen(QPen(QColor(90, 255, 120), 2))
            for a_, b_ in ((2, 4), (3, 5)):
                if b_ < len(pts):
                    p.drawLine(pts[a_], pts[b_])
            p.setPen(QPen(QColor(255, 255, 255), 1))
            for a_, b_ in ((0, 1), (2, 3), (4, 5)):
                if b_ < len(pts):
                    p.drawLine(pts[a_], pts[b_])
            labs = ("1 front end, low", "2 front end, top", "3 the corner, low", "4 the corner, top",
                    "5 back of side, low", "6 back of side, top")
            for i, q_ in enumerate(pts):
                dot(q_, QColor(255, 217, 26), 6)
                text(QPointF(q_.x() + 8, q_.y() - 6), labs[i], QColor(255, 230, 120))
            return
        if st == 5 and f.get('depth_how') == 'side':
            q = (f.get('side') or {}).get('quad') or []
            pts = [n2s(c[0], c[1]) for c in q]
            p.setPen(QPen(QColor(77, 255, 255), 2))
            for i in range(len(pts) - 1 + (1 if len(pts) == 4 else 0)):
                p.drawLine(pts[i], pts[(i + 1) % len(pts)])
            for i, q_ in enumerate(pts):
                dot(q_, QColor(77, 255, 255), 6)
                text(QPointF(q_.x() + 8, q_.y() - 6), ("front, bottom", "back, bottom", "back, top", "front, top")[i],
                     QColor(100, 255, 255))
            return
        q = f.get('quad') or []
        pts = [n2s(c[0], c[1]) for c in q]
        p.setPen(QPen(QColor(77, 255, 255), 2))
        for i in range(len(pts) - 1 + (1 if len(pts) == 4 else 0)):
            p.drawLine(pts[i], pts[(i + 1) % len(pts)])
        for i, q_ in enumerate(pts):
            dot(q_, QColor(77, 255, 255), 6)
            text(QPointF(q_.x() + 8, q_.y() - 6), ("bottom left", "bottom right", "top right", "top left")[i],
                 QColor(100, 255, 255))
        kc = (f.get('known') or {}).get('clicks') or []
        kp = [n2s(c[0], c[1]) for c in kc]
        if kp:
            p.setPen(QPen(QColor(80, 230, 120), 2.5))
            if len(kp) == 2:
                p.drawLine(kp[0], kp[1])
            for q_ in kp:
                dot(q_, QColor(80, 230, 120), 5)
            if len(kp) == 2 and float((f.get('known') or {}).get('mm') or 0) > 0:
                text(QPointF(kp[1].x() + 8, kp[1].y() - 6), "%.0f mm (I know this)" % f['known']['mm'],
                     QColor(120, 255, 150))
        w = self.wall()
        if w is None:
            return
        L, E, to_mm, to_photo = w

        def P(s, z):
            return n2s(*to_photo(s, z))
        # a 1 m grid on the wall, so you can see it's square on
        p.setPen(QPen(QColor(90, 153, 255, 90), 1))
        s_ = 0.0
        while s_ <= L + 1e-6:
            p.drawLine(P(s_, 0.0), P(s_, E))
            s_ += 1000.0
        z_ = 0.0
        while z_ <= E + 1e-6:
            p.drawLine(P(0.0, z_), P(L, z_))
            z_ += 1000.0
        text(QPointF(P(L / 2.0, 0.0).x() - 40, P(L / 2.0, 0.0).y() + 18), "%.0f mm" % L, QColor(100, 255, 255))
        if f.get('ridge'):
            r_ = n2s(*f['ridge'])
            dot(r_, QColor(255, 115, 230))
            text(QPointF(r_.x() + 8, r_.y() - 6), "roof top %.0f" % to_mm(f['ridge'])[1], QColor(255, 150, 240))
        for g in f.get('gables') or []:
            gp = [n2s(*c) for c in g.get('clicks') or []]
            p.setPen(QPen(QColor(255, 115, 230), 2))
            for i in range(len(gp) - 1):
                p.drawLine(gp[i], gp[i + 1])
            if len(gp) == 3:
                p.drawLine(gp[2], gp[0])
            for q_ in gp:
                dot(q_, QColor(255, 150, 240), 4)

        def box(cl, col, label, top='square'):
            (s0, z0), (s1, z1) = to_mm(cl[0]), to_mm(cl[1])
            a, b, lo, hi = min(s0, s1), max(s0, s1), min(z0, z1), max(z0, z1)
            p.setPen(QPen(col, 2))
            wd = b - a
            if top in ('round', 'segment') and wd > 1.0:   # its real top
                rise = wd / 2.0 if top == 'round' else wd * 0.15
                spring = max(lo, hi - rise)
                rise = hi - spring
                if top == 'round':
                    arc = [((a + b) / 2.0 - wd / 2.0 * math.cos(math.pi * t / 16.0),
                            spring + rise * math.sin(math.pi * t / 16.0)) for t in range(17)]
                else:
                    arc = [(a + wd * t / 16.0, spring + rise * (1.0 - (2.0 * t / 16.0 - 1.0) ** 2)) for t in range(17)]
                pts_ = [(a, spring), (a, lo), (b, lo), (b, spring)] + list(reversed(arc))
                for i in range(len(pts_) - 1):
                    p.drawLine(P(*pts_[i]), P(*pts_[i + 1]))
            else:
                for (x1, y1), (x2, y2) in (((a, lo), (b, lo)), ((b, lo), (b, hi)), ((b, hi), (a, hi)), ((a, hi), (a, lo))):
                    p.drawLine(P(x1, y1), P(x2, y2))
            t = P(a, hi)
            text(QPointF(t.x() + 3, t.y() - 4), label, col, 10)
        if st == 3 and self.line_mode:                    # windows picked to line up
            for i_, k_ in enumerate(self.line_sel):
                bl_ = (f.get('boxes') or [])
                if not 0 <= k_ < len(bl_):
                    continue
                cl_ = bl_[k_].get('clicks') or []
                us_ = [n2s(*c) for c in cl_]
                if not us_:
                    continue
                x0_, x1_ = min(q.x() for q in us_), max(q.x() for q in us_)
                y0_, y1_ = min(q.y() for q in us_), max(q.y() for q in us_)
                p.setPen(QPen(QColor(255, 255, 255) if i_ == 0 else QColor(77, 255, 255), 4))
                p.drawRect(QRectF(x0_ - 4, y0_ - 4, x1_ - x0_ + 8, y1_ - y0_ + 8))
                if i_ == 0:
                    text(QPointF(x0_, y0_ - 10), "copy this one", QColor(255, 255, 255), 11)
        cnt = {'window': 0, 'door': 0}
        for o in f.get('boxes') or []:
            if o.get('top') == 'traced' and len(o.get('clicks') or []) >= 3:
                cnt[o['kind']] += 1
                col = QColor(*FCOLS[o['kind']])
                tp = [n2s(*c) for c in o['clicks']]
                p.setPen(QPen(col, 2))
                for i in range(len(tp)):
                    p.drawLine(tp[i], tp[(i + 1) % len(tp)])
                mm_ = [to_mm(c) for c in o['clicks']]
                text(QPointF(min(q_.x() for q_ in tp) + 3, min(q_.y() for q_ in tp) - 4), "%s%d  %.0f x %.0f" % (
                    "D" if o['kind'] == 'door' else "W", cnt[o['kind']], max(m_[0] for m_ in mm_) -
                    min(m_[0] for m_ in mm_), max(m_[1] for m_ in mm_) - min(m_[1] for m_ in mm_)), col, 10)
                continue
            if len(o.get('clicks') or []) == 2:
                cnt[o['kind']] += 1
                (s0, z0), (s1, z1) = to_mm(o['clicks'][0]), to_mm(o['clicks'][1])
                box(o['clicks'], QColor(*FCOLS[o['kind']]), "%s%d  %.0f x %.0f" % (
                    "D" if o['kind'] == 'door' else "W", cnt[o['kind']], abs(s1 - s0), abs(z1 - z0)),
                    o.get('top', 'square'))
        nb = nw = 0
        for i, bx in enumerate(f.get('parts') or []):
            if len(bx.get('clicks') or []) == 2:
                if bx['kind'] == 'bay':
                    nb += 1
                    lab = "Bay %d" % nb
                else:
                    nw += 1
                    lab = "Wing %d" % nw
                col = QColor(*FCOLS[bx['kind']])
                if st == 4 and i == self.sel_part:
                    col = QColor(255, 255, 255)
                box(bx['clicks'], col, lab + {'splayed': " (splayed)", 'round': " (round)"}.get(bx.get('shape'), ""))
                for fcl in bx.get('front_clicks') or []:
                    q_ = n2s(*fcl)
                    p.setPen(QPen(QColor(255, 217, 26), 1.5, Qt.DashLine))
                    lo_ = P(to_mm(fcl)[0], 0.0)
                    p.drawLine(QPointF(q_.x(), q_.y() - 40), QPointF(lo_.x(), lo_.y()))
                    dot(q_, QColor(255, 217, 26), 5)
        jb_ = f.get('_job') or {}
        for k_, jc in enumerate(jb_.get('clicks') or []):      # a bay being clicked: its clicks so far
            q_ = n2s(*jc)
            dot(q_, QColor(255, 217, 26), 6)
            text(QPointF(q_.x() + 8, q_.y() - 6), str(k_ + 1), QColor(255, 217, 26), 12)
        for kind_, v_ in getattr(self, 'guides', None) or []:      # lined up: the guide it snapped to
            p.setPen(QPen(QColor(80, 255, 120), 1.2, Qt.DashLine))
            if kind_ == 'z':
                p.drawLine(P(-0.1 * L, v_), P(1.1 * L, v_))
            else:
                p.drawLine(P(v_, -0.05 * E), P(v_, 1.3 * E))
        if self.trace:
            tp = [n2s(*c) for c in self.trace]
            p.setPen(QPen(QColor(255, 255, 255), 2))
            for i in range(len(tp) - 1):
                p.drawLine(tp[i], tp[i + 1])
            if self.hover:
                p.setPen(QPen(QColor(255, 255, 255), 1.5, Qt.DashLine))
                p.drawLine(tp[-1], n2s(*self.hover))
                p.drawLine(n2s(*self.hover), tp[0])
            for i, q_ in enumerate(tp):
                dot(q_, QColor(255, 255, 255), 4)
                text(QPointF(q_.x() + 6, q_.y() - 5), str(i + 1), QColor(255, 255, 255), 9)
        if self.pending is not None and getattr(self, 'hover', None) and self.page() == 3 and \
                self.top in ('round', 'segment'):
            box([self.pending, self.hover], QColor(255, 255, 255), "", self.top)
        if self.pending is not None and getattr(self, 'hover', None):
            a, b = n2s(*self.pending), n2s(*self.hover)
            p.setPen(QPen(QColor(255, 255, 255), 1.5, Qt.DashLine))
            p.drawRect(QRectF(QPointF(min(a.x(), b.x()), min(a.y(), b.y())),
                              QPointF(max(a.x(), b.x()), max(a.y(), b.y()))))
        if self.pending is not None:
            dot(n2s(*self.pending), QColor(255, 255, 255), 4)

    # ---- the panel ----
    def goto(self, n):
        self.f['step'] = min(max(1, int(n)), 6)
        self.pending, self.trace = None, []
        self.gable_mode = False
        self.drag_tri = None
        self.peek = None
        self.show_photo()
        self.update_all()

    def _set(self, key, value):
        if self.busy or self.f.get(key) == value:
            return
        self.remember()
        self.f[key] = value
        if key == 'ridge_how' and value == 'side' and not (self.f.get('roof_side') or {}).get('photo'):
            ps = [p_ for p_ in self.photos() if p_ != self.f.get('photo')]     # a guess: the side photo, if any
            sp_ = (self.f.get('side') or {}).get('photo')
            pick = sp_ if sp_ and sp_ != self.f.get('photo') else (ps[0] if ps else None)
            if pick:
                self.f['roof_side'] = {'photo': pick, 'clicks': []}
        if key in ('depth_how', 'ridge_how'):
            self.peek = None
            self.show_photo()
        self.update_all()

    def _part_set(self, key, value):
        if self.busy:
            return
        ps = self.f.get('parts') or []
        if 0 <= self.sel_part < len(ps) and ps[self.sel_part].get(key) != value:
            self.remember()
            ps[self.sel_part][key] = value
            self.update_all()

    def _pick_part(self, i):
        if self.busy or i < 0:
            return
        self.sel_part = i
        self.update_all()

    def _line_mode(self, on):
        if self.busy:
            return
        self.line_mode = bool(on)
        self.line_sel = []
        self.pending, self.trace = None, []
        self.update_all()

    def box_at(self, c):
        """The window or door clicked on (its index), or None - the smallest one round the click."""
        best = None
        for k, o in enumerate(self.f.get('boxes') or []):
            cl = o.get('clicks') or []
            if len(cl) < 2:
                continue
            us, vs = [q[0] for q in cl], [q[1] for q in cl]
            pad = 0.006
            if min(us) - pad <= c[0] <= max(us) + pad and min(vs) - pad <= c[1] <= max(vs) + pad:
                area = (max(us) - min(us)) * (max(vs) - min(vs))
                if best is None or area < best[0]:
                    best = (area, k)
        return best[1] if best else None

    def line_up(self):
        """The pop-up: how to line the picked windows up with the first one."""
        from PySide6.QtWidgets import QDialogButtonBox
        boxes = self.f.get('boxes') or []
        sel = [k for k in self.line_sel if 0 <= k < len(boxes)]
        w = self.wall()
        if len(sel) < 2 or w is None:
            self.say("Click the good window first, then Shift + click the others.", True)
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Line them up")
        vl = QVBoxLayout(dlg)
        vl.addWidget(QLabel("<b>Line up %d windows with the first one you clicked:</b>" % (len(sel) - 1)))
        ck_top = QCheckBox("Tops level with it")
        ck_bot = QCheckBox("Bottoms level with it")
        ck_size = QCheckBox("The same size as it")
        ck_even = QCheckBox("Evenly spaced across (the two end ones stay put)")
        ck_top.setChecked(True)
        ck_size.setChecked(True)
        for c_ in (ck_top, ck_bot, ck_size, ck_even):
            c_.setStyleSheet("font-size: 10.5pt; padding: 3px;")
            vl.addWidget(c_)
        ck_top.toggled.connect(lambda on: on and ck_bot.setChecked(False))
        ck_bot.toggled.connect(lambda on: on and ck_top.setChecked(False))
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("Line them up")
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        vl.addWidget(bb)
        if dlg.exec() != QDialog.Accepted:
            return
        _L, _E, to_mm, to_photo = w
        self.remember()

        def rect(o):
            pts = [to_mm(c) for c in o['clicks']]
            return (min(q[0] for q in pts), max(q[0] for q in pts), min(q[1] for q in pts), max(q[1] for q in pts))
        ref = rect(boxes[sel[0]])
        rw, rh = ref[1] - ref[0], ref[3] - ref[2]
        if boxes[sel[0]].get('kind') != 'door':
            sel = [sel[0]] + [k for k in sel[1:] if boxes[k].get('kind') != 'door']     # doors left alone
        new = {}
        for k in sel:
            s0, s1, z0, z1 = rect(boxes[k])
            cx = (s0 + s1) / 2.0
            wdt, hgt = (rw, rh) if ck_size.isChecked() else (s1 - s0, z1 - z0)
            if ck_top.isChecked():
                z1n = ref[3]
                z0n = z1n - hgt
            elif ck_bot.isChecked():
                z0n = ref[2]
                z1n = z0n + hgt
            else:
                z1n = z1
                z0n = z1n - hgt
            new[k] = [cx - wdt / 2.0, cx + wdt / 2.0, z0n, z1n]
        if ck_even.isChecked() and len(sel) >= 3:
            order = sorted(sel, key=lambda k_: new[k_][0] + new[k_][1])
            c_first = (new[order[0]][0] + new[order[0]][1]) / 2.0
            c_last = (new[order[-1]][0] + new[order[-1]][1]) / 2.0
            for i, k in enumerate(order):
                cx = c_first + (c_last - c_first) * i / float(len(order) - 1)
                half = (new[k][1] - new[k][0]) / 2.0
                new[k][0], new[k][1] = cx - half, cx + half
        for k, (s0, s1, z0, z1) in new.items():
            o = boxes[k]
            if o.get('top') == 'traced' and len(o.get('clicks') or []) >= 3:
                os0, os1, oz0, oz1 = rect(o)                # an odd shape: moved and stretched to fit
                sx = (s1 - s0) / max(os1 - os0, 1e-6)
                sz = (z1 - z0) / max(oz1 - oz0, 1e-6)
                o['clicks'] = [list(to_photo(s0 + (m[0] - os0) * sx, z0 + (m[1] - oz0) * sz))
                               for m in (to_mm(c) for c in o['clicks'])]
            else:
                o['clicks'] = [list(to_photo(s0, z0)), list(to_photo(s1, z1))]
        self.save()
        self.update_all()
        self.say("Lined up ✓  (Ctrl+Z to put them back)")

    def even_splays(self):
        """The picked bay's flat front put in the middle (same width), so both angled sides are the same."""
        if self.busy:
            return
        ps = self.f.get('parts') or []
        if not 0 <= self.sel_part < len(ps):
            return
        bx = ps[self.sel_part]
        if bx.get('kind') != 'bay' or bx.get('shape') != 'splayed':
            self.say("That one hasn't got angled sides - pick Angled sides first.", True)
            return
        fw = float(bx.get('front') or 0.0)
        fc = bx.get('front_clicks') or []
        w = self.wall()
        if len(fc) == 2 and w is not None:
            fw = abs(w[2](fc[1])[0] - w[2](fc[0])[0])
        self.remember()
        if fw > 0:
            bx['front'] = fw
        bx.pop('front_clicks', None)
        self.update_all()
        self.say("Both angled sides the same now ✓")

    def _fit_stack(self):
        """The step's part exactly as tall as what's showing in it (no gap under it)."""
        try:
            cur = self.stack.currentWidget()
            if cur is None:
                return
            lay_ = cur.layout()
            if lay_ is not None:
                lay_.activate()
            h = max(cur.sizeHint().height(), cur.minimumSizeHint().height())
            self.stack.setFixedHeight(h)
        except Exception as e:
            print("%s: fitting the step: %s" % (PLUGIN_NAME, e))

    def sort_parts(self):
        """Bays first, then wings, each left to right along the front - so Bay 1 is the left one."""
        ps = self.f.get('parts') or []
        if len(ps) < 2:
            return
        sel = ps[self.sel_part] if 0 <= self.sel_part < len(ps) else None
        ps.sort(key=lambda q: (q.get('kind') != 'bay',
                               min((c[0] for c in (q.get('clicks') or [])), default=9.9)))
        if sel is not None:
            self.sel_part = next(k for k, q in enumerate(ps) if q is sel)

    def swap_bay(self):
        """Swaps the picked bay's shape, how far it comes out and its roof with the next bay along (each keeps
        its own place on the front)."""
        if self.busy:
            return
        ps = self.f.get('parts') or []
        bays = [k for k, q in enumerate(ps) if q.get('kind') == 'bay']
        if self.sel_part not in bays or len(bays) < 2:
            self.say("Pick a bay on the plan first (there need to be 2).", True)
            return
        other = bays[(bays.index(self.sel_part) + 1) % len(bays)]
        self.remember()
        a, b = ps[self.sel_part], ps[other]
        for key in ('shape', 'out', 'roof', 'pitch', 'front', 'front_clicks'):
            a_has, b_has = key in a, key in b
            av, bv = a.get(key), b.get(key)
            if key == 'front_clicks':
                continue                            # the posts stay where they were clicked
            a.pop(key, None)
            b.pop(key, None)
            if b_has:
                a[key] = bv
            if a_has:
                b[key] = av
        self.sel_part = other
        self.update_all()
        self.say("Swapped over.")

    def job_hint(self, jb, n):
        """What the next click of a bay or wing is."""
        if jb.get('shape') == 'splayed':
            return ["its <b>BOTTOM LEFT</b> corner - where it meets the ground, on the far left",
                    "its <b>LEFT POST</b> - where the left side window meets the big front window",
                    "its <b>RIGHT POST</b> - where the big front window meets the right side window",
                    "its <b>TOP RIGHT</b> corner - just under its roof (fascia), on the far right"][min(n, 3)]
        return ["its <b>BOTTOM LEFT</b> corner - where it meets the ground",
                "its <b>TOP RIGHT</b> corner - just under its roof (fascia)"][min(n, 1)]

    def job_top(self):
        jb = self.f.get('_job') or {}
        stage = jb.get('stage') or 'start'
        if stage == 'click':
            n_ = len(jb.get('clicks') or [])
            return "CLICK %d OF %d: %s" % (n_ + 1, self.job_need(),
                                          re.sub(r"<[^>]+>", "", self.job_hint(jb, n_)).upper())
        if stage == 'shape':
            return "WHAT SHAPE IS THE BAY? - pick on the right"
        if stage == 'size':
            return "HOW FAR IT COMES OUT AND ITS ROOF - on the right, then Done"
        return "BAYS AND WINGS - press + Add a bay on the right (or Next if there aren't any)"

    def job_need(self):
        jb = self.f.get('_job') or {}
        return 4 if jb.get('shape') == 'splayed' else 2

    def job_start(self, what):
        if self.busy:
            return
        f = self.f
        self.front_mode = False
        self.remember()
        if what == 'wing':
            f['_job'] = {'stage': 'click', 'kind': 'wing', 'shape': 'square', 'clicks': []}
        elif what == 'same':
            bays = [q for q in f.get('parts') or [] if q.get('kind') == 'bay']
            if not bays:
                self.history.pop()
                self.say("There isn't a bay to copy yet - Add a bay first.", True)
                return
            src = bays[-1]
            fw = float(src.get('front') or 0.0)
            w = self.wall()
            fc = src.get('front_clicks') or []
            if w is not None and len(fc) == 2:
                fw = abs(w[2](fc[1])[0] - w[2](fc[0])[0])
            f['_job'] = {'stage': 'click', 'kind': 'bay', 'shape': 'square' if src.get('shape') == 'splayed'
                         else src.get('shape', 'square'), 'clicks': [],
                         'copy': {'out': src.get('out'), 'roof': src.get('roof'), 'pitch': src.get('pitch'),
                                  'shape': src.get('shape'), 'front': fw}}
        else:
            f['_job'] = {'stage': 'shape', 'kind': 'bay', 'clicks': []}
        self.update_all()

    def job_shape(self, shape):
        if self.busy:
            return
        jb = self.f.get('_job')
        if not jb:
            return
        self.remember()
        jb['shape'] = shape
        jb['stage'] = 'click'
        jb['clicks'] = []
        self.update_all()

    def job_done(self):
        if self.busy:
            return
        self.remember()
        self.f.pop('_job', None)
        self.front_mode = False
        self.update_all()
        n = len(self.f.get('parts') or [])
        self.say("That's %d done. Add another, or Next ▸ when they're all in." % n)

    def job_stop(self):
        if self.busy:
            return
        jb = self.f.get('_job')
        if not jb:
            return
        self.remember()
        if jb.get('stage') == 'size':                 # it was made: take it off again
            ps = self.f.get('parts') or []
            if 0 <= self.sel_part < len(ps):
                ps.pop(self.sel_part)
                self.sel_part = max(0, self.sel_part - 1)
        self.f.pop('_job', None)
        self.front_mode = False
        self.update_all()

    def bays_same(self):
        """The other bays the same as the one picked: shape, flat front (its width), out, roof, pitch."""
        ps = self.f.get('parts') or []
        if not 0 <= self.sel_part < len(ps) or ps[self.sel_part].get('kind') != 'bay':
            return
        src = ps[self.sel_part]
        fw = float(src.get('front') or 0.0)
        w = self.wall()
        fc = src.get('front_clicks') or []
        if w is not None and len(fc) == 2:                 # its flat front, as clicked: the width of it
            fw = abs(w[2](fc[1])[0] - w[2](fc[0])[0])
        others = [q for i, q in enumerate(ps) if i != self.sel_part and q.get('kind') == 'bay']
        if not others:
            self.say("There's only one bay.", True)
            return
        self.remember()
        for q in others:
            for key in ('shape', 'out', 'roof', 'pitch'):
                q[key] = src.get(key)
            q['front'] = fw
            q['front_clicks'] = []                         # centred in its own box
        self.update_all()
        self.say("%d other bay%s made the same." % (len(others), "" if len(others) == 1 else "s"))

    def part_off(self):
        ps = self.f.get('parts') or []
        if 0 <= self.sel_part < len(ps):
            self.remember()
            ps.pop(self.sel_part)
            self.sel_part = max(0, self.sel_part - 1)
            self.update_all()

    def depth_pick(self, key):
        if self.busy:
            return
        self.remember()
        f = self.f
        f['depth_how'] = key
        f['depth_set'] = True
        if key == 'cphoto':
            cd = f.setdefault('cdepth', {'photo': None, 'clicks': []})
            if not cd.get('photo'):
                cd['photo'] = self.cdepth_photo()
        self.peek = None
        self.pending, self.trace = None, []
        self.show_photo()
        self.update_all()

    def cdepth_again(self):
        if self.busy:
            return
        self.remember()
        self.f.setdefault('cdepth', {'photo': None})['clicks'] = []
        self.update_all()

    def step5_next(self):
        """The depth: (text for the yellow box, done)."""
        f = self.f
        how = f.get('depth_how', 'type')
        d_, why = self.depth()
        if not f.get('depth_set') and not d_:
            return ("<b>How deep is the building?</b><br><small>How far it goes back, front to back. Pick how "
                    "below - a corner photo is easiest.</small>"), False
        if d_ > 0:
            return ("<b>Depth: %.0f mm ✓</b> (%s)<br>Step 5 done - press <b>Next ▸</b>" % (d_, why)), True
        if how == 'cphoto':
            if not self.cdepth_photo():
                return ("Add a photo taken from a <b>corner</b> of the building (Another photo... on step 1)."), False
            n = len((f.get('cdepth') or {}).get('clicks') or [])
            hints = ["the <b>FAR END of the front wall</b>, low down<br><small>at the ground - or if that's "
                     "hidden, any height you can see on all 3 (e.g. the window sills)</small>",
                     "the same corner at the <b>TOP</b><br><small>just under the roof edge</small>",
                     "the <b>CORNER</b> nearest you (where the front meets the side), <b>at the same height</b> "
                     "as click 1",
                     "that corner at the <b>TOP</b><br><small>just under the roof edge</small>",
                     "the <b>BACK END of the side wall</b>, <b>at the same height</b> as click 1",
                     "that end at the <b>TOP</b><br><small>just under the roof edge</small>"]
            if n < 6:
                return ("On the corner photo, click %s<br><small>(%d of 6)</small>" % (hints[n], n + 1)), False
            return ("<b>Those corners don't work:</b> %s" % why), False
        if how == 'side':
            q = (f.get('side') or {}).get('quad') or []
            if not (f.get('side') or {}).get('photo'):
                return "Pick the <b>side photo</b> below (or its tab above the photo).", False
            names = ["the <b>FRONT end, bottom</b>", "the <b>BACK end, bottom</b>", "the <b>BACK end, top</b>",
                     "the <b>FRONT end, top</b>"]
            if len(q) < 4:
                return ("On the side photo, click the side wall's %s<br><small>(%d of 4)</small>"
                        % (names[len(q)], len(q) + 1)), False
            return why, False
        return ("Type <b>how deep</b> the building is, front to back<br><small>On Google Maps: right-click a "
                "corner, Measure distance, click the back corner.</small>"), False

    def top_pick(self, key):
        if self.busy:
            return
        if key == 'outline':
            self._how_f('outline')
        else:
            if self.how_f != 'box':
                self._how_f('box')
            self._top(key)
        self.update_all()

    def step_wd_next(self):
        """Windows and doors: (text for the yellow box, done)."""
        f = self.f
        if self.line_mode:
            n = len(self.line_sel)
            if n == 0:
                return ("<b>Lining up:</b> click the <b>good window</b> - the one to copy", False)
            if n == 1:
                return ("Now <b>Shift + click</b> the windows to line up with it", False)
            return ("%d picked. Shift + click more, or press <b>Line them up...</b>" % (n - 1), False)
        bx = f.get('boxes') or []
        nw = sum(1 for b in bx if b.get('kind') == 'window')
        nd = len(bx) - nw
        thing = "door" if self.kind == 'door' else "window"
        so_far = ""
        if bx:
            so_far = ("<br><small>Marked so far: %d window%s, %d door%s. All done? Press <b>Next ▸</b></small>"
                      % (nw, "" if nw == 1 else "s", nd, "" if nd == 1 else "s"))
        if self.how_f == 'outline':
            n = len(self.trace)
            if n < 3:
                return ("Click <b>all round the edge</b> of a %s<br><small>6 or more points, going round it</small>"
                        % thing + so_far, bool(bx))
            return ("Keep clicking round it (%d points)<br><small>Finish by clicking its <b>first point</b> again"
                    "</small>" % n, False)
        if self.pending is None:
            bays_ = any(q.get('kind') == 'bay' for q in f.get('parts') or [])
            return ("Click a %s's <b>TOP LEFT</b> corner" % thing +
                    ("<br><small>Do the bay windows too - they go on the bay by themselves.</small>"
                     if bays_ and thing == "window" else "") + so_far, bool(bx))
        return ("Now click its <b>BOTTOM RIGHT</b> corner", False)

    def roof_pick(self, key, low=None):
        if self.busy:
            return
        self.remember()
        f = self.f
        f['roof'] = key
        if low:
            f['roof_low'] = low
        f['roof_set'] = True
        self.update_all()

    def _rhow_pick(self, how):
        if self.busy:
            return
        self.remember()
        self.f['ridge_how'] = how
        if how == 'cpeak':
            cd = self.f.setdefault('cdepth', {'photo': None, 'clicks': []})
            if not cd.get('photo'):
                cd['photo'] = self.cdepth_photo()
        self.peek = None
        self.show_photo()
        self.update_all()

    def roof_again(self):
        if self.busy:
            return
        self.remember()
        self.f['roof_set'] = False
        self.gable_mode = False
        self.update_all()

    def gables_answer(self, yes):
        if self.busy:
            return
        self.remember()
        self.f['gables_q'] = 'yes' if yes else 'no'
        self.gable_mode = bool(yes)
        self.peek = None
        self.show_photo()
        self.update_all()

    def gables_finished(self):
        if self.busy:
            return
        f = self.f
        gl = f.get('gables') or []
        if gl and len(gl[-1].get('clicks') or []) < 3:
            self.say("Finish the gable you're on first (its 3 points), or Ctrl+Z to take its clicks off.", True)
            return
        self.remember()
        self.gable_mode = False
        if not gl:
            f['gables_q'] = 'no'
        self.update_all()

    def step2_next(self):
        """Step 2 (the roof): (stage, the text for the yellow box, done)."""
        f = self.f
        roof_set = f.get('roof_set')
        if roof_set is None:                            # a job from before: done if it was clicked
            roof_set = bool(f.get('gables')) or f.get('ridge') is not None
        if not roof_set:
            return 'shape', "<b>What shape is the main roof?</b><br>Pick the one that looks most like it.", False
        roof = f.get('roof', 'gable_len')
        if roof in ('flat', 'none'):
            return 'done', "<b>Step 2 done ✓</b><br>Press <b>Next ▸</b>", True
        gq = f.get('gables_q') or ('yes' if f.get('gables') else None)
        gl = [g for g in f.get('gables') or [] if g.get('clicks')]
        if gq is None:
            return 'gq', ("<b>Are there pointed gables on the front of the roof?</b><br>"
                          "<small>Triangles sticking up from the roof edge, like on a station.</small>"), False
        if self.gable_mode:
            done_g = [g for g in gl if len(g['clicks']) >= 3]
            k = len(gl[-1]['clicks']) % 3 if gl and len(gl[-1]['clicks']) < 3 else 0
            n = len(done_g) + (1 if k else 1)
            what = ["its <b>LEFT</b> corner<br><small>where it sits on the roof edge</small>",
                    "its <b>RIGHT</b> corner<br><small>where it sits on the roof edge</small>",
                    "its <b>PEAK</b><br><small>the very top point</small>"][k]
            more = "" if k else ("<br><small>No more? Press <b>That's all the gables</b>.</small>"
                                 if done_g else "")
            return 'gables', "Gable %d: click %s%s" % (n, what, more), False
        rh = self.ridge_how()
        if gq == 'no' and not f.get('ridge_how') and len(self.photos()) > 1:
            return 'rhow', ("<b>How high is the roof?</b><br><small>Best: the corner photo - click the peak of the "
                            "end wall.</small>"), False
        if rh == 'cpeak':
            n6 = len((f.get('cdepth') or {}).get('clicks') or [])
            if n6 < 6:
                hints = ["the <b>LEFT END of the front</b>, low down<br><small>(the ground, or any height you can "
                         "see on all 3 corners)</small>",
                         "straight up from there, at the <b>ROOF EDGE</b>",
                         "the <b>CORNER</b> where the front meets the end wall, at the <b>same height</b> as click 1",
                         "straight up from there, at the <b>ROOF EDGE</b>",
                         "the <b>BACK END of the end wall</b>, at the <b>same height</b> as click 1",
                         "straight up from there, at the <b>ROOF EDGE</b>"]
                return 'cpeak', ("On the corner photo, click %s<br><small>(%d of 7)</small>" % (hints[n6], n6 + 1)), \
                    False
            if not f.get('cpeak'):
                return 'cpeak', ("Now click the <b>PEAK of the end wall</b><br><small>the top point of its "
                                 "triangle (7 of 7)</small>"), False
            if not self.cpeak_pitch():
                return 'cpeak', ("That peak doesn't measure - Ctrl+Z and click the very top of the end wall's "
                                 "triangle."), False
        if rh == 'click' and f.get('ridge') is None:
            return 'ridge', ("Click the <b>very TOP of the roof</b><br><small>the ridge, the highest line of the "
                             "main roof</small>"), False
        if rh == 'side' and not self.side_pitch():
            return 'side', "Draw the triangle on the side photo (under More settings).", False
        return 'done', "<b>Step 2 done ✓</b><br>Press <b>Next ▸</b>", True

    def _gables(self, on):
        if self.busy:
            return
        self.gable_mode = bool(on)
        self.peek = None
        self.show_photo()
        self.update_all()

    def _kind(self, k):
        self.kind = k
        if not self.busy:
            self.update_all()

    def _top(self, t):
        if t:
            self.top = t
        if not self.busy:
            self.update_all()

    def _how_f(self, how):
        self.how_f = how
        self.pending, self.trace = None, []
        if not self.busy:
            self.update_all()

    def finish_trace(self):
        """Ends a window or door clicked all round."""
        if len(self.trace) < 3:
            self.say("Click at least 3 points round it (6 or more for a good shape) first.", True)
            return False
        self.remember()
        self.f['boxes'].append({'kind': self.kind, 'top': 'traced', 'clicks': list(self.trace)})
        self.trace = []
        self.update_all()
        return True

    def right_click(self):
        if self.mode() == 'box' and self.how_f == 'outline':
            self.finish_trace()

    def _front_mode(self, on):
        if self.busy:
            return
        self.front_mode = bool(on)
        ps = self.f.get('parts') or []
        if on and 0 <= self.sel_part < len(ps):
            self.remember()
            ps[self.sel_part]['front_clicks'] = []
        self.update_all()

    def _box_kind(self, k):
        self.box_kind = k
        self.pending = None
        if not self.busy:
            self.update_all()

    def say(self, text, bad=False):
        self.lbl_problem.setText(text)
        self.lbl_problem.setStyleSheet("color: #b00;" if bad else "color: #050;")

    def update_all(self):
        f = self.f
        self.busy = True
        try:
            st = int(f.get('step') or 1)
            pg = self.page()
            for n_, b in zip(range(1, 7), self.step_btns):
                b.setChecked(n_ == st)
            self.lbl_step.setText("Step %d of 6:  %s" % (st, dict(FSTEPS)[st]))
            self.lbl_how.setText(FSHORT[pg])
            self.lbl_how.setToolTip(FHOWTO[pg])
            self.lbl_how.setVisible(pg not in (1, 2, 3, 4, 5))
            done_ = False
            if pg == 1:
                nq_, gtxt, done_ = self.step1_next()
                self.lbl_guide.setText(gtxt)
                self.w_size1.setVisible(nq_ >= 4)
                kn_ = f.get('known') or {}
                show_k = self.b_known_show.isChecked() or bool(kn_.get('clicks')) or self.known_mode
                self.b_known_show.setChecked(show_k)
                self.w_known.setVisible(show_k)
                self.w_more1.setVisible(self.b_more1.isChecked())
                self.b_more1.setText("More settings ▾" if self.b_more1.isChecked() else "More settings ▸")
            if pg == 5:
                gtxt, done_ = self.step5_next()
                self.lbl_guide.setText(gtxt)
                how5 = f.get('depth_how', 'type')
                set5 = bool(f.get('depth_set')) or how5 != 'type' or float(f.get('depth_mm') or 0) > 0
                for key_, b_ in self.b_dh.items():
                    b_.setChecked(set5 and key_ == how5)
                self.cb_side.setVisible(how5 == 'side')
                self.lbl_side5.setVisible(how5 == 'side')
                self.sp_depth.setVisible(set5 and how5 == 'type')
                self.lbl_depth5.setVisible(set5 and how5 == 'type')
                self.b_cd_again.setVisible(how5 == 'cphoto' and bool((f.get('cdepth') or {}).get('clicks')))
                self.w_more5.setVisible(self.b_more5.isChecked())
                self.b_more5.setText("More settings ▾" if self.b_more5.isChecked() else "More settings ▸")
            if pg == 3:
                gtxt, done_ = self.step_wd_next()
                self.lbl_guide.setText(gtxt)
                self.b_k_win.setChecked(self.kind != 'door')
                self.b_k_door.setChecked(self.kind == 'door')
                for key_, b_ in self.b_t.items():
                    b_.setChecked(key_ == 'outline' if self.how_f == 'outline' else
                                  (self.how_f == 'box' and key_ == self.top))
                self.ck_sides.setVisible(any(q.get('kind') == 'bay' for q in f.get('parts') or []))
                self.b_line.setChecked(self.line_mode)
                self.b_line.setText("Stop lining up" if self.line_mode else "Line windows up...")
                self.b_line_go.setVisible(self.line_mode and len(self.line_sel) >= 2)
                self.b_line.setVisible(len(f.get('boxes') or []) >= 2)
            if pg == 2:
                stg2, gtxt, done_ = self.step2_next()
                self.lbl_guide.setText(gtxt)
                self.w_rshape.setVisible(stg2 == 'shape')
                self.w_gq.setVisible(stg2 == 'gq')
                self.w_rhow2.setVisible(stg2 == 'rhow')
                self.b_gdone.setVisible(stg2 == 'gables')
                self.b_rshape_again.setVisible(stg2 != 'shape')
                self.w_more2.setVisible(self.b_more2.isChecked())
                self.b_more2.setText("More settings ▾" if self.b_more2.isChecked() else "More settings ▸")
            if pg != 3 and self.line_mode:
                self.line_mode, self.line_sel = False, []
            self.lbl_guide.setVisible(pg in (1, 2, 3, 5))
            self.diag.setVisible(pg != 6)
            self.plan.setVisible(pg in (4, 5))             # the plan: only for the bays and the depth
            self.preview3d.update()
            if pg == 6:
                ps6 = f.get('parts') or []
                sel6 = self.sel_part if 0 <= self.sel_part < len(ps6) else -1
                bx6 = ps6[sel6] if sel6 >= 0 else None
                if not ps6:
                    self.lbl_pick6.setText("")
                elif bx6 is None:
                    self.lbl_pick6.setText("<b>Something not right?</b> Click a bay on the plan to change it.")
                else:
                    nb6 = sum(1 for q in ps6[:sel6 + 1] if q.get('kind') == bx6.get('kind'))
                    self.lbl_pick6.setText("<b>%s %d</b> (picked - blue on the plan):" % (
                        "Bay" if bx6.get('kind') == 'bay' else "Wing", nb6))
                self.w_ed6.setVisible(bx6 is not None)
                if bx6 is not None:
                    for key_, b_ in self.b6_shape.items():
                        b_.setChecked(bx6.get('shape', 'square') == key_)
                        b_.setVisible(bx6.get('kind') == 'bay')
                    self.sp6_out.setValue(float(bx6.get('out') or 0.0))
                    self.b6_even.setVisible(bx6.get('kind') == 'bay' and bx6.get('shape') == 'splayed')
                    self.b6_same.setVisible(bx6.get('kind') == 'bay' and
                                            sum(1 for q in ps6 if q.get('kind') == 'bay') > 1)
                    self.b6_swap.setVisible(bx6.get('kind') == 'bay' and
                                            sum(1 for q in ps6 if q.get('kind') == 'bay') > 1)
                self.plan6.update()
            self.b_fwd.setStyleSheet("QPushButton { background: #7ad67a; font-weight: bold; }" if done_ else "")
            self.stack.setCurrentIndex(pg - 1)
            from PySide6.QtWidgets import QSizePolicy as _QSP
            for i_ in range(self.stack.count()):           # only the step showing takes up room
                w_ = self.stack.widget(i_)
                if i_ == pg - 1:
                    w_.setSizePolicy(_QSP.Preferred, _QSP.Maximum)
                else:
                    w_.setSizePolicy(_QSP.Ignored, _QSP.Ignored)
            self.stack.setSizePolicy(_QSP.Preferred, _QSP.Maximum)
            QTimer.singleShot(0, self._fit_stack)
            ps = self.photos()
            self._fill_tabs()
            self.cb_photo.clear()
            self.cb_side.clear()
            for p_ in ps:
                self.cb_photo.addItem(os.path.basename(p_))
                self.cb_side.addItem(os.path.basename(p_))
            if f.get('photo') in ps:
                self.cb_photo.setCurrentIndex(ps.index(f['photo']))
            sp = (f.get('side') or {}).get('photo')
            self.cb_side.setCurrentIndex(ps.index(sp) if sp in ps else -1)
            self.sp_len.setValue(float(f.get('length_mm') or 0.0))
            self.sp_eaves.setValue(float(f.get('eaves_mm') or 0.0))
            self.sp_storeys.setValue(int(f.get('storeys') or 2))
            kn = f.get('known') or {}
            self.sp_known.setValue(float(kn.get('mm') or 0.0))
            self.b_known.setChecked(bool(self.known_mode))
            self.b_known.setText("1.  Click its two ends%s" % ("  ✓" if len(kn.get('clicks') or []) == 2 else ""))
            self.cb_roof.setCurrentIndex(max(self.cb_roof.findData(f.get('roof', 'gable_len')), 0))
            self.cb_low.setCurrentIndex(0 if f.get('roof_low', 'front') == 'front' else 1)
            self.cb_low.setEnabled(f.get('roof') == 'mono')
            self.ck_gables.setChecked(self.gable_mode)
            self.lbl_gables.setText("Gables clicked: %d" % len([g for g in f.get('gables') or []
                                                                if len(g.get('clicks') or []) == 3]))
            rh = self.ridge_how()
            self.cb_rhow.setCurrentIndex(max(self.cb_rhow.findData(rh), 0))
            gp = self.gable_pitch()
            sdp = self.side_pitch()
            if rh == 'side':
                self.sp_rpitch.setValue(round(sdp) if sdp else float(f.get('roof_pitch') or 40.0))
            else:
                self.sp_rpitch.setValue(float(f.get('roof_pitch') or (round(gp) if gp else 40.0)))
            self.sp_rpitch.setEnabled(rh == 'pitch')
            self.w_rside.setVisible(rh == 'side')
            self.sp_eover.setValue(float(f.get('eave_over', 300.0)))
            self.sp_vover.setValue(float(f.get('verge_over', 300.0)))
            self.ck_boards.setChecked(bool(f.get('boards', True)))
            self.cb_rside.clear()
            for p_ in ps:
                self.cb_rside.addItem(os.path.basename(p_))
            rsp = (f.get('roof_side') or {}).get('photo')
            self.cb_rside.setCurrentIndex(ps.index(rsp) if rsp in ps else -1)
            ntri = len((f.get('roof_side') or {}).get('clicks') or [])
            if not rsp:
                self.lbl_rside.setText("Pick the side photo (the gable end, straight on).")
            elif ntri < 3:
                self.lbl_rside.setText("Click the %s." % ("left eave", "ridge (the top)", "right eave")[ntri])
            elif sdp:
                self.lbl_rside.setText("<b>Roof pitch %.1f°</b> - drag a corner to fine-tune it." % sdp)
            else:
                self.lbl_rside.setText("That triangle doesn't point up - drag its corners: eave, ridge, eave.")
            self.b_rside_new.setEnabled(ntri > 0)
            (self.rb_door if self.kind == 'door' else self.rb_win).setChecked(True)
            self.cb_top.setCurrentIndex(max(self.cb_top.findData(self.top), 0))
            (self.rb_fall if self.how_f == 'outline' else self.rb_fbox).setChecked(True)
            self.ck_sides.setChecked(bool(f.get('bay_sides', True)))
            self.b_finish.setVisible(self.how_f == 'outline')
            self.b_finish.setEnabled(len(self.trace) >= 3)
            self.b_finish.setText("Finish this one  (Enter)  - %d points" % len(self.trace))
            self.cb_top.setEnabled(self.how_f == 'box')
            nw_ = sum(1 for o in f.get('boxes') or [] if o.get('kind') != 'door')
            self.lbl_ops.setText("%d windows, %d doors" % (nw_, len(f.get('boxes') or []) - nw_))
            (self.rb_wing if self.box_kind == 'wing' else self.rb_bay).setChecked(True)
            parts = f.get('parts') or []
            self.lst_parts.clear()
            nb = nw = 0
            for bx in parts:
                if bx['kind'] == 'bay':
                    nb += 1
                    self.lst_parts.addItem("✓ Bay %d  (%s)" % (nb, {'splayed': "splayed", 'round': "round"}.get(
                        bx.get('shape'), "square")))
                else:
                    nw += 1
                    self.lst_parts.addItem("✓ Wing %d" % nw)
            if parts:
                self.sel_part = min(self.sel_part, len(parts) - 1)
            if self.front_mode and not (parts and parts[self.sel_part].get('kind') == 'bay' and
                                        parts[self.sel_part].get('shape') == 'splayed'):
                self.front_mode = False                 # Undo took its bay away
            if parts:
                self.lst_parts.setCurrentRow(self.sel_part)
                bx = parts[self.sel_part]
                self.lbl_out.setText("Comes out (front of it to the wall)" if bx['kind'] == 'bay'
                                     else "Goes back (its depth)")
                self.sp_out.setValue(float(bx.get('out') or 0.0))
                self.sp_back.setValue(float(bx.get('back') or 0.0))
                self.sp_back.setEnabled(bx['kind'] == 'wing')
                self.cb_proof.setCurrentIndex(max(self.cb_proof.findData(bx.get('roof')), 0))
                self.sp_pitch.setValue(float(bx.get('pitch') or 30.0))
                self.cb_bshape.setCurrentIndex(max(self.cb_bshape.findData(bx.get('shape', 'square')), 0))
                spl = bx['kind'] == 'bay' and bx.get('shape') == 'splayed'
                self.sp_front.setValue(float(bx.get('front') or 0.0))
                for w_ in (self.sp_front, self.b_front):
                    w_.setEnabled(spl)
                self.b_front.setChecked(self.front_mode)
                self.b_front.setText("Click its 2 posts again%s" % (
                    "  ✓" if len(bx.get('front_clicks') or []) == 2 else ""))
                self.cb_bshape.setEnabled(bx['kind'] == 'bay')
                self.b_same.setEnabled(bx['kind'] == 'bay' and sum(1 for q in parts if q.get('kind') == 'bay') > 1)
            for w_ in (self.sp_out, self.sp_back, self.cb_proof, self.sp_pitch, self.b_part_off):
                w_.setEnabled(bool(parts) and (w_ is not self.sp_back or
                                               parts[self.sel_part]['kind'] == 'wing'))
            # the guided job: one thing at a time
            jb = f.get('_job') or {}
            stage = jb.get('stage') or 'start'
            kname = "wing" if jb.get('kind') == 'wing' else "bay"
            nparts = len(parts)
            if stage == 'start':
                if not parts:
                    txt = ("<b>Bays and wings</b><br>Does the front have bays (or a porch) sticking out, or a wing "
                           "on an end? Press <b>+ Add a bay</b> to do the first one.<br>None? Just press "
                           "<b>Next ▸</b>.")
                else:
                    txt = ("<b>%d done.</b> Another one? <b>+ Add a bay</b> (or <b>+ Add another bay the same</b> "
                           "- then you only click where it is).<br>All done? Press <b>Next ▸</b>." % nparts)
            elif stage == 'shape':
                txt = "<b>New bay - 1 of 3: what shape is it?</b><br>Look at it in the photo and pick one below."
            elif stage == 'click':
                n_ = len(jb.get('clicks') or [])
                need = self.job_need()
                if jb.get('copy'):
                    nb_ = sum(1 for q in parts if q.get('kind') == 'bay')
                    txt = ("<b>Copying Bay %d</b> - same shape, size and roof.<br>Now show where the new bay is "
                           "on the photo (click %d of 2):<br>%s" % (nb_, n_ + 1, self.job_hint(jb, n_)))
                else:
                    txt = ("<b>New %s - %sclick %d of %d on the photo:</b><br>%s" % (
                        kname, "2 of 3: " if kname == 'bay' else "", n_ + 1, need, self.job_hint(jb, n_)))
            else:
                txt = ("<b>New %s - 3 of 3: how far it comes out and its roof</b><br>Check the numbers below, "
                       "then press <b>Done ✓</b>." % kname)
            self.lbl_job.setText(txt)
            self.w_jstart.setVisible(stage == 'start')
            self.b_add_same.setVisible(any(q.get('kind') == 'bay' for q in parts))
            self.w_jshape.setVisible(stage == 'shape')
            self.w_form.setVisible(stage == 'size' or (stage == 'start' and nparts > 0))
            self.b_job_done.setVisible(stage == 'size')
            self.b_job_stop.setVisible(stage != 'start')
            for w_ in (self.lbl_done, self.lst_parts, self.w_pick):
                w_.setVisible(stage == 'start' and nparts > 0)
            how = f.get('depth_how', 'type')
            {'corner': self.rb_d_corner, 'side': self.rb_d_side}.get(how, self.rb_d_type).setChecked(True)
            cfo, r = self.corner_job()
            w = self.wall()
            self.lbl_corner.setText(("The corner photo makes it %.0f mm deep (from the job '%s')." % (
                w[0] * r, os.path.basename(cfo or ''))) if (r and w) else
                "No corner photo found with its corners done - Pick which corner photo to use, or click one the "
                "other way (Start clicking round the building).")
            self.rb_d_corner.setEnabled(bool(r))
            self.cb_side.setEnabled(how == 'side')
            self.sp_depth.setEnabled(how == 'type')
            self.sp_depth.setValue(float(f.get('depth_mm') or 0.0))
            try:
                b_ = self.build()
                rh_ = self.ridge_how()
                lines = ["<b>Main building</b>: %.0f x %.0f mm, eaves %.0f, ridge %.0f%s (depth %s)" % (
                    b_['length'], b_['width'], b_['eaves'], b_['ridge'],
                    {'gables': " from the gables' %.0f° pitch" % (self.gable_pitch() or 0),
                     'pitch': " from a %.0f° pitch" % float(f.get('roof_pitch') or 40.0),
                     'side': " from the side photo's %.0f° pitch" % (self.side_pitch() or 0),
                     'peak': " as high as the tallest gable's peak"}.get(rh_, ""),
                    b_['depth_from'])]
                nb_ = 0
                for pr, bx_ in zip(b_['parts'][1:], [q for q in f.get('parts') or [] if len(q.get('clicks') or []) == 2]):
                    lines.append("<b>%s</b>: %.0f x %.0f mm, eaves %.0f" % (pr['name'], pr['length'], pr['width'],
                                                                         pr['eaves']))
                    if bx_.get('kind') == 'bay' and bx_.get('shape') == 'splayed' and \
                            len(bx_.get('front_clicks') or []) < 2 and not float(bx_.get('front') or 0):
                        lines.append("<span style='color:#b00'>%s: its flat front is a guess - click its 2 corners "
                                     "(step 3)</span>" % pr['name'])
                lines.append("%d windows and doors, %d gables" % (len(b_['openings']), len(b_['gables'])))
                self.lbl_sizes.setText("<br>".join(lines))
                prob = ""
            except ValueError as e:
                self.lbl_sizes.setText(str(e))
                prob = str(e) if st == 6 else ""
            self.lbl_problem.setText(prob)
            self.lbl_problem.setStyleSheet("color: #b00;")
            self.b_back.setEnabled(st > 1)
            self.b_fwd.setVisible(st < 6)
            self.b_undo.setEnabled(bool(self.history))
            self.b_redo.setEnabled(bool(self.future))
            tops = {1: re.sub(r"<[^>]+>", " ", self.step1_next()[1]).replace("  ", " ").upper(),
                    2: re.sub(r"<[^>]+>", " ", self.step2_next()[1]).replace("  ", " ").upper(),
                    3: re.sub(r"<[^>]+>", " ", self.step_wd_next()[0].split("<br>")[0]).replace("  ", " ").upper(),
                    4: "THE BAY'S 2 POSTS - click the left post, then the right post" if self.front_mode else
                    self.job_top(),
                    5: re.sub(r"<[^>]+>", " ", self.step5_next()[0].split("<br>")[0]).replace("  ", " ").upper(),
                    6: ""}
            self.lbl_top.setText("<b>%s</b>" % tops[pg] if tops[pg] else "")
        finally:
            self.busy = False
        self.view.update()
        self.plan.update()
        self.diag.update()
        self._save_timer.start(400)

    def diagram(self):
        """How to click this step, as a drawing: the dot to click next lit up."""
        f = self.f
        st = self.page()
        out = []
        if st == 1:
            out += _house_front()
            q = len(f.get('quad') or [])
            kc = len((f.get('known') or {}).get('clicks') or [])
            for i, (pt, lab) in enumerate((((15, 5), "1"), ((85, 5), "2"), ((85, 40), "3"), ((15, 40), "4"))):
                out.append(('dot', pt, lab, 'cyan', not self.known_mode and i == q))
            out.append(('line', [(58, 5), (58, 22)], 'green', 2))
            out.append(('dot', (58, 5), "", 'green', self.known_mode and kc in (0, 2)))
            out.append(('dot', (58, 22), "", 'green', self.known_mode and kc == 1))
            out.append(('text', (60, 13), "or a size you know", 'green'))
        elif st == 2 and self.ridge_how() == 'cpeak' and not self.gable_mode:
            n6 = len((f.get('cdepth') or {}).get('clicks') or [])
            out += _corner_clicks(n6 if n6 < 6 else (6 if not f.get('cpeak') else 7), peak=True)
        elif st == 2 and self.ridge_how() == 'side' and not self.gable_mode:
            out.append(('line', [(25, 5), (75, 5), (75, 38), (25, 38), (25, 5)], 'wall', 2))
            out.append(('line', [(25, 38), (50, 60), (75, 38)], 'pink', 2.5))
            n_ = len((f.get('roof_side') or {}).get('clicks') or [])
            for i, (pt, lab) in enumerate((((25, 38), "1 eave"), ((50, 60), "2 ridge"), ((75, 38), "3 eave"))):
                out.append(('dot', pt, lab, 'pink', i == n_))
            out.append(('text', (2, 66), "the gable end, straight on", 'pink'))
        elif st == 2:
            out += _house_front(roof=False)
            out.append(('line', [(10, 40), (22, 56), (78, 56), (90, 40)], 'pink', 2))
            out.append(('dot', (50, 56), "top", 'pink', not self.gable_mode and not f.get('ridge')))
            out.append(('line', [(60, 40), (70, 52), (80, 40)], 'red', 2))
            gl = f.get('gables') or []
            n_ = len(gl[-1]['clicks']) if gl and len(gl[-1].get('clicks') or []) < 3 else 0
            for i, (pt, lab) in enumerate((((60, 40), "1"), ((80, 40), "2"), ((70, 52), "3 peak"))):
                out.append(('dot', pt, lab, 'red', self.gable_mode and i == n_))
        elif st == 3 and self.how_f == 'outline':
            out += _house_front()
            c = 'orange' if self.kind == 'door' else 'blue'
            pw = [(40, 12), (60, 12), (60, 26), (55, 33), (50, 37), (45, 33), (40, 26)]
            out.append(('line', pw + [pw[0]], c, 2.5))
            n_ = len(self.trace)
            for i, pt in enumerate(pw):
                out.append(('dot', pt, str(i + 1), c, i == min(n_, len(pw) - 1) and n_ < len(pw)))
            out.append(('text', (64, 30), "then Finish", 'green'))
        elif st == 3:
            out += _house_front()
            win = self.kind != 'door'
            r = [(22, 18), (32, 30)] if win else [(45, 5), (55, 22)]
            c = 'blue' if win else 'orange'
            out.append(('line', [r[0], (r[1][0], r[0][1]), r[1], (r[0][0], r[1][1]), r[0]], c, 2.5))
            out.append(('dot', r[0], "1", c, self.pending is None))
            out.append(('dot', r[1], "2", c, self.pending is not None))
        elif st == 4:
            out += _house_front()
            jb = f.get('_job') or {}
            bay = jb.get('kind', 'bay') != 'wing'
            n_ = len(jb.get('clicks') or [])
            live = jb.get('stage') == 'click'
            if bay and jb.get('shape') == 'splayed' and not jb.get('copy'):
                c = 'yellow'                                # a splayed bay: corners and its 2 posts
                a, b = (18, 5), (40, 26)
                out.append(('line', [a, (b[0], a[1]), b, (a[0], b[1]), a], c, 2.5))
                out.append(('line', [(23, 5), (23, 26)], c, 1.5))
                out.append(('line', [(35, 5), (35, 26)], c, 1.5))
                for i, (pt, lab) in enumerate(((a, "1"), ((23, 12), "2"), ((35, 12), "3"), (b, "4"))):
                    out.append(('dot', pt, lab, c, live and i == n_))
                out.append(('text', (8, 63), "corner, post, post, corner", 'yellow'))
            else:
                for kind, (a, b), c in (('bay', ((20, 5), (38, 26)), 'yellow'),
                                        ('wing', ((85, 5), (99, 28)), 'pink')):
                    on = (kind == 'bay') == bay
                    out.append(('line', [a, (b[0], a[1]), b, (a[0], b[1]), a], c if on else 'faint',
                                2.5 if on else 1))
                    if on:
                        out.append(('dot', a, "1", c, live and n_ == 0))
                        out.append(('dot', b, "2", c, live and n_ == 1))
                out.append(('text', (19, 63), "a bay" if bay else "a wing", 'yellow' if bay else 'pink'))
        elif st == 5:
            how = f.get('depth_how', 'type')
            if how == 'side':
                out.append(('line', [(25, 5), (75, 5), (75, 40), (25, 40), (25, 5)], 'wall', 2))
                out.append(('line', [(25, 40), (50, 60), (75, 40)], 'faint', 1.5))
                q = len((f.get('side') or {}).get('quad') or [])
                for i, (pt, lab) in enumerate((((25, 5), "1 front"), ((75, 5), "2 back"), ((75, 40), "3"),
                                               ((25, 40), "4"))):
                    out.append(('dot', pt, lab, 'cyan', i == q))
                out.append(('text', (2, 66), "the side wall, straight on", 'cyan'))
            elif how == 'cphoto':
                out += _corner_clicks(len((f.get('cdepth') or {}).get('clicks') or []))
            elif how == 'corner':
                out += _corner_house()
                out.append(('line', [_B, _C], 'yellow', 3))
                out.append(('text', (2, 66), "uses the corner photo's corners", 'yellow'))
            else:
                out.append(('line', [(20, 15), (80, 15), (80, 50), (20, 50), (20, 15)], 'wall', 2))
                out.append(('line', [(86, 15), (86, 50)], 'yellow', 2.5))
                out.append(('text', (60, 32), "depth", 'yellow'))
                out.append(('text', (2, 66), "type it from a map", 'yellow'))
        else:
            out += _house_front(faint=True)
            out.append(('text', (30, 62), "check - then Send", 'green'))
        return out

    # ---- send ----
    def send(self):
        try:
            res = self.build()
        except ValueError as e:
            self.say(str(e), True)
            return
        res['photo'] = self.f.get('photo') or self.photo0
        path = os.path.join(self.folder, RESULT_NAME)
        try:
            tmp = path + ".part"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(res, fh, indent=1)
            os.replace(tmp, path)
        except Exception as e:
            self.say("Couldn't save it: %s" % e, True)
            return
        self.save()
        try:
            self.main.job_folder = self.folder
            save_settings(last_job=self.folder)
            self.main.take_result(path)
            self.main._seen = os.path.getmtime(path)
            self.main.refresh_buttons()
            self.main.raise_()
            self.main.activateWindow()
        except Exception as e:
            print("%s: back to the window: %s" % (PLUGIN_NAME, e))
        self.close()


def join_fanlights(ops):
    """A door with a window marked right on top of it (a fanlight): one doorway, as tall as both, with the
    window's top - two holes touching would leave the door out."""
    out = list(ops)
    used = set()
    for i, d in enumerate(ops):
        if d.get('kind') != 'door':
            continue
        for j, w in enumerate(ops):
            if j == i or j in used or w.get('kind') == 'door' or w.get('part') != d.get('part') or \
                    w.get('wall') != d.get('wall'):
                continue
            ov = min(d['s1'], w['s1']) - max(d['s0'], w['s0'])
            narrow = min(d['s1'] - d['s0'], w['s1'] - w['s0'])
            if narrow <= 0 or ov < 0.5 * narrow:
                continue                                    # not over the door
            if not (w['z1'] > d['z1'] and w['z0'] <= d['z1'] + 150.0):
                continue                                    # not sitting on top of it
            nd = dict(d)
            nd['z1'] = w['z1']
            nd['box2'] = w.get('box')                       # the fanlight's own box on the photo
            nd['fan_h'] = round(w['z1'] - d['z1'], 1)
            if w.get('shape'):
                # the window's arched top, fitted to the door's width, on top of the door
                ws0, ws1 = w['s0'], w['s1']
                fx = (d['s1'] - d['s0']) / max(ws1 - ws0, 1e-6)
                midz = (w['z0'] + w['z1']) / 2.0
                top = sorted(([d['s0'] + (q[0] - ws0) * fx, max(q[1], d['z1'])] for q in w['shape'] if q[1] >= midz),
                             key=lambda q: -q[0])
                nd['shape'] = [[d['s0'], d['z0']], [d['s1'], d['z0']], [d['s1'], d['z1']]] + top + \
                    [[d['s0'], d['z1']]]
                nd['top'] = 'traced'
            else:
                nd['top'] = w.get('top', 'square')
                nd['shape'] = None
            out[i] = nd
            used.add(j)
            break
    return [o for k, o in enumerate(out) if k not in used]


class Preview3D(QWidget):
    """The building as it comes together, in 3D: drag to turn it, wheel to zoom, double-click to set it straight."""

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.yaw, self.pitch, self.zoom = -35.0, 22.0, 1.0
        self._drag = None
        self.setMinimumHeight(220)
        self.setToolTip("Drag to turn it, wheel to zoom, double-click to put it straight")

    # ---- mouse
    def mousePressEvent(self, ev):
        pos = ev.position() if hasattr(ev, 'position') else ev.pos()
        self._drag = (pos.x(), pos.y(), self.yaw, self.pitch)

    def mouseMoveEvent(self, ev):
        if self._drag is None:
            return
        pos = ev.position() if hasattr(ev, 'position') else ev.pos()
        x0, y0, yw, pt = self._drag
        self.yaw = yw + (pos.x() - x0) * 0.5
        self.pitch = max(-5.0, min(85.0, pt + (pos.y() - y0) * 0.4))
        self.update()

    def mouseReleaseEvent(self, _ev):
        self._drag = None

    def mouseDoubleClickEvent(self, _ev):
        self.yaw, self.pitch, self.zoom = -35.0, 22.0, 1.0
        self.update()

    def wheelEvent(self, ev):
        d = ev.angleDelta().y()
        self.zoom = max(0.4, min(4.0, self.zoom * (1.15 if d > 0 else 1.0 / 1.15)))
        self.update()

    # ---- the building as flat faces: [(points 3D mm, colour, kind)]
    def faces(self):
        self.guessed = False
        self._main_cs, self._gcent = None, {}
        try:
            b = self.win.build()
        except Exception:
            try:
                b = self.win.build(guess_depth=True)
                self.guessed = True
            except Exception:
                b = None
        out = []
        if b is None:
            w = self.win.wall()
            if w is None:
                return out, False
            L, E = w[0], w[1]
            out.append(([(0, 0, 0), (L, 0, 0), (L, 0, E), (0, 0, E)], (215, 212, 205), 'wall', 0, None))
            return out, False
        WALL, ROOF, BAY = (218, 214, 205), (78, 84, 98), (205, 200, 190)
        def area(cs_):
            return sum(cs_[i][0] * cs_[(i + 1) % len(cs_)][1] - cs_[(i + 1) % len(cs_)][0] * cs_[i][1]
                       for i in range(len(cs_)))
        for pi, pr in enumerate(b['parts']):
            cs = [(float(c[0]), float(c[1])) for c in pr['corners']]
            n = len(cs)
            if n < 3:
                continue
            if area(cs) < 0:
                cs.reverse()                               # always anticlockwise: faces turned outwards
            if pi == 0:
                self._main_cs = list(cs)
            else:
                self._gcent[pi + 1] = (sum(c[0] for c in cs) / n, sum(c[1] for c in cs) / n)
            e = float(pr.get('eaves') or b.get('eaves') or 0.0)
            r = float(pr.get('ridge') or 0.0)
            col = WALL if pi == 0 else BAY
            g_ = 0 if pi == 0 else pi + 1                  # group: each part on its own (the gables are 1)
            for i in range(n):
                a, c = cs[i], cs[(i + 1) % n]
                out.append(([(a[0], a[1], 0), (c[0], c[1], 0), (c[0], c[1], e), (a[0], a[1], e)], col, 'wall', g_,
                            None))
            out += [f_ + (g_, None) for f_ in self.roof(cs, e, r, pr.get('roof', 'gable_len'),
                                                        pr.get('roof_low', 'front'), ROOF, col)]
        # the front gables
        for g in b.get('gables') or []:
            s0, s1, z0, pk = float(g['s0']), float(g['s1']), float(g['z0']), float(g['peak'])
            m = (s0 + s1) / 2.0
            dd = (s1 - s0) / 2.0
            out.append(([(s0, -1, z0), (s1, -1, z0), (m, -1, pk)], WALL, 'wall', 1, None))
            out.append(([(s0, 0, z0), (m, 0, pk), (m, dd, pk), (s0, dd, z0)], ROOF, 'roof', 1, None))
            out.append(([(m, 0, pk), (s1, 0, z0), (s1, dd, z0), (m, dd, pk)], ROOF, 'roof', 1, None))
        # windows and doors, just in front of their walls
        for o in b.get('openings') or []:
            pi = int(o.get('part', 0))
            if not 0 <= pi < len(b['parts']):
                continue
            cs = b['parts'][pi]['corners']
            wi = int(o.get('wall', 0)) % len(cs)
            a, c = cs[wi], cs[(wi + 1) % len(cs)]
            ln = math.hypot(c[0] - a[0], c[1] - a[1]) or 1.0
            ux, uy = (c[0] - a[0]) / ln, (c[1] - a[1]) / ln
            nx, ny = uy, -ux                                # outside (the outline runs anticlockwise)
            if area([(float(c_[0]), float(c_[1])) for c_ in cs]) < 0:
                nx, ny = -nx, -ny                           # it runs the other way: outside is the other side
            pts2 = o['shape'] if o.get('shape') else [(o['s0'], o['z0']), (o['s1'], o['z0']), (o['s1'], o['z1']),
                                                      (o['s0'], o['z1'])]
            # slid back onto its wall keeping its size, as the real build does, then trimmed if still too wide
            fr = min(90.0, ln * 0.08)                       # the wall left each side: a frame round it
            lo_, hi_ = fr, ln - fr
            smin, smax = min(q_[0] for q_ in pts2), max(q_[0] for q_ in pts2)
            if smax - smin > hi_ - lo_ > 0:                 # too wide: narrowed evenly to fit between the frames
                k_ = (hi_ - lo_) / (smax - smin)
                pts2 = [(lo_ + (q_[0] - smin) * k_, q_[1]) for q_ in pts2]
            else:                                           # slid back inside the frames, keeping its size
                d_ = 0.0
                if smax > hi_:
                    d_ = hi_ - smax
                if smin + d_ < lo_:
                    d_ = lo_ - smin
                pts2 = [(q_[0] + d_, q_[1]) for q_ in pts2]
            ew = float(b['parts'][pi].get('eaves') or b.get('eaves') or 1e9)
            mg = 1.0
            for k_, lim, keep_lo in ((0, mg, True), (0, ln - mg, False), (1, 0.0, True), (1, ew - 20.0, False)):
                cl_ = []
                for i_ in range(len(pts2)):
                    p_, q_ = pts2[i_], pts2[(i_ + 1) % len(pts2)]
                    pin = p_[k_] >= lim if keep_lo else p_[k_] <= lim
                    qin = q_[k_] >= lim if keep_lo else q_[k_] <= lim
                    if pin:
                        cl_.append(tuple(p_))
                    if pin != qin:
                        t_ = (lim - p_[k_]) / ((q_[k_] - p_[k_]) or 1e-9)
                        cl_.append((p_[0] + t_ * (q_[0] - p_[0]), p_[1] + t_ * (q_[1] - p_[1])))
                pts2 = cl_
                if len(pts2) < 3:
                    break
            if len(pts2) < 3:
                continue
            pts = [(a[0] + ux * s + nx * 8.0, a[1] + uy * s + ny * 8.0, z) for s, z in pts2]
            out.append((pts, (110, 75, 50) if o.get('kind') == 'door' else (150, 190, 220), 'hole',
                        0 if pi == 0 else pi + 1, (nx, ny, 0.0)))
        return out, True

    def roof(self, cs, e, r, roof, low, ROOF, col):
        out = []
        if roof in ('flat', 'none') or r <= e:
            out.append(([(x, y, e) for x, y in cs], ROOF, 'roof'))
            return out
        xs, ys = [c[0] for c in cs], [c[1] for c in cs]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        rect = len(cs) == 4 and all(any(abs(c[0] - v) < 1.0 for v in (x0, x1)) and
                                    any(abs(c[1] - v) < 1.0 for v in (y0, y1)) for c in cs)
        if not rect:                                        # a bay or odd shape: a pyramid
            cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
            for i in range(len(cs)):
                a, c = cs[i], cs[(i + 1) % len(cs)]
                out.append(([(a[0], a[1], e), (c[0], c[1], e), (cx, cy, r)], ROOF, 'roof'))
            return out
        ym, xm = (y0 + y1) / 2.0, (x0 + x1) / 2.0
        if roof == 'gable_len':
            out.append(([(x0, y0, e), (x1, y0, e), (x1, ym, r), (x0, ym, r)], ROOF, 'roof'))
            out.append(([(x1, y1, e), (x0, y1, e), (x0, ym, r), (x1, ym, r)], ROOF, 'roof'))
            out.append(([(x0, y1, e), (x0, y0, e), (x0, ym, r)], col, 'wall'))
            out.append(([(x1, y0, e), (x1, y1, e), (x1, ym, r)], col, 'wall'))
        elif roof == 'gable_across':
            out.append(([(x0, y1, e), (x0, y0, e), (xm, y0, r), (xm, y1, r)], ROOF, 'roof'))
            out.append(([(x1, y0, e), (x1, y1, e), (xm, y1, r), (xm, y0, r)], ROOF, 'roof'))
            out.append(([(x0, y0, e), (x1, y0, e), (xm, y0, r)], col, 'wall'))
            out.append(([(x1, y1, e), (x0, y1, e), (xm, y1, r)], col, 'wall'))
        elif roof == 'mono':
            if low == 'front':
                out.append(([(x0, y0, e), (x1, y0, e), (x1, y1, r), (x0, y1, r)], ROOF, 'roof'))
                out.append(([(x0, y1, e), (x0, y0, e), (x0, y1, r)], col, 'wall'))
                out.append(([(x1, y0, e), (x1, y1, e), (x1, y1, r)], col, 'wall'))
                out.append(([(x1, y1, e), (x0, y1, e), (x0, y1, r), (x1, y1, r)], col, 'wall'))
            else:
                out.append(([(x0, y0, r), (x1, y0, r), (x1, y1, e), (x0, y1, e)], ROOF, 'roof'))
                out.append(([(x0, y1, e), (x0, y0, e), (x0, y0, r)], col, 'wall'))
                out.append(([(x1, y0, e), (x1, y1, e), (x1, y0, r)], col, 'wall'))
                out.append(([(x0, y0, e), (x1, y0, e), (x1, y0, r), (x0, y0, r)], col, 'wall'))
        else:                                               # hip
            h = min(x1 - x0, y1 - y0) / 2.0
            if x1 - x0 >= y1 - y0:
                pa, pb = (x0 + h, ym, r), (x1 - h, ym, r)
                out.append(([(x0, y0, e), (x1, y0, e), pb, pa], ROOF, 'roof'))
                out.append(([(x1, y1, e), (x0, y1, e), pa, pb], ROOF, 'roof'))
                out.append(([(x0, y1, e), (x0, y0, e), pa], ROOF, 'roof'))
                out.append(([(x1, y0, e), (x1, y1, e), pb], ROOF, 'roof'))
            else:
                pa, pb = (xm, y0 + h, r), (xm, y1 - h, r)
                out.append(([(x1, y0, e), (x1, y1, e), pb, pa], ROOF, 'roof'))
                out.append(([(x0, y1, e), (x0, y0, e), pa, pb], ROOF, 'roof'))
                out.append(([(x0, y0, e), (x1, y0, e), pa], ROOF, 'roof'))
                out.append(([(x1, y1, e), (x0, y1, e), pb], ROOF, 'roof'))
        return out

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QPolygonF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(236, 238, 241))
        fs, whole = self.faces()
        if fs and whole and not getattr(Preview3D, '_logged', False):
            Preview3D._logged = True
            try:
                b_ = self.win.build(guess_depth=True)
                with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "photo_to_building_clicks.txt"),
                          "a", encoding="utf-8") as fh:
                    fh.write("PREVIEW parts: %s\n\n" % json.dumps([pr.get('corners') for pr in b_.get('parts')]))
            except Exception:
                pass
        p.setPen(QColor(110, 110, 110))
        p.drawText(QRectF(8, 4, self.width() - 16, 18), Qt.AlignLeft,
                   "Your building so far - drag to turn it" if fs else
                   "Your building shows here in 3D as you go")
        if not fs:
            p.end()
            return
        allp = [q for f in fs for q in f[0]]
        cx = (min(q[0] for q in allp) + max(q[0] for q in allp)) / 2.0
        cy = (min(q[1] for q in allp) + max(q[1] for q in allp)) / 2.0
        cz = (min(q[2] for q in allp) + max(q[2] for q in allp)) / 2.0
        span = max(max(q[0] for q in allp) - min(q[0] for q in allp),
                   max(q[1] for q in allp) - min(q[1] for q in allp),
                   max(q[2] for q in allp) - min(q[2] for q in allp), 1.0)
        yw, pt = math.radians(self.yaw), math.radians(self.pitch)
        cyw, syw, cpt, spt = math.cos(yw), math.sin(yw), math.cos(pt), math.sin(pt)

        def view(q):
            x, y, z = q[0] - cx, q[1] - cy, q[2] - cz
            xr = x * cyw - y * syw                          # turn round the upright
            yr = x * syw + y * cyw
            yv = yr * cpt - z * spt                         # tip to look down a bit
            zv = yr * spt + z * cpt
            return xr, yv, zv                               # across, into the screen, up
        dist = span * 2.6
        sc = min(self.width(), self.height() - 24) * 0.95 * self.zoom
        ox, oy = self.width() / 2.0, (self.height() + 18) / 2.0

        def scr(v):
            f = dist / max(dist + v[1], 1.0)
            return QPointF(ox + v[0] / span * sc * f, oy - v[2] / span * sc * f)
        light = (0.45, -0.75, 0.5)

        def facing(nv):
            """Is a face with this facing (model) turned towards you?"""
            return ((nv[0] * syw + nv[1] * cyw) * cpt - nv[2] * spt) < 0.0

        def normal(pts):
            nx = ny = nz = 0.0                               # Newell: the facing of a flat polygon
            for i in range(len(pts)):
                a_, b_ = pts[i], pts[(i + 1) % len(pts)]
                nx += (a_[1] - b_[1]) * (a_[2] + b_[2])
                ny += (a_[2] - b_[2]) * (a_[0] + b_[0])
                nz += (a_[0] - b_[0]) * (a_[1] + b_[1])
            return nx, ny, nz
        groups = {}
        for pts, col, kind, g_, hn in fs:
            groups.setdefault(g_, []).append((pts, col, kind, hn))
        front_seen = facing((0.0, -1.0, 0.0))
        order = []
        for g_, lst in groups.items():
            if g_ == 1 and not front_seen:
                continue                                     # the front gables: only when the front shows
            allq = [view(q) for f_ in lst for q in f_[0]]
            d_ = sum(v[1] for v in allq) / len(allq)
            if g_ == 1:
                d_ = None                                    # straight after the main building
            order.append((d_, g_, lst))
        main_d = next((d_ for d_, g_, _l in order if g_ == 0), 0.0)
        mq = [q for f_ in groups.get(0, []) for q in f_[0]]
        mcs = getattr(self, '_main_cs', None)
        if mq:
            mx0, mx1 = min(q[0] for q in mq), max(q[0] for q in mq)
            my0, my1 = min(q[1] for q in mq), max(q[1] for q in mq)
        new_order = []
        for d_, g_, lst in order:
            if d_ is None:
                d_ = main_d - 1e-3
            elif g_ >= 2 and mq:
                # a bay or wing: in front of the main building if the wall it stands on faces you
                pts_ = [q for f_ in lst for q in f_[0]]
                bx_ = sum(q[0] for q in pts_) / len(pts_)
                by_ = sum(q[1] for q in pts_) / len(pts_)
                bx_, by_ = getattr(self, '_gcent', {}).get(g_, (bx_, by_))
                best_ = None
                if mcs:
                    for i_ in range(len(mcs)):               # the main wall it stands against: the nearest
                        a_, c_ = mcs[i_], mcs[(i_ + 1) % len(mcs)]
                        ex, ey = c_[0] - a_[0], c_[1] - a_[1]
                        ll = ex * ex + ey * ey or 1.0
                        t_ = max(0.0, min(1.0, ((bx_ - a_[0]) * ex + (by_ - a_[1]) * ey) / ll))
                        dd_ = math.hypot(bx_ - a_[0] - t_ * ex, by_ - a_[1] - t_ * ey)
                        if best_ is None or dd_ < best_[0]:
                            lw = math.sqrt(ll)
                            best_ = (dd_, (ey / lw, -ex / lw, 0.0))
                if best_ is not None:
                    nv_ = best_[1]
                elif by_ < my0:
                    nv_ = (0.0, -1.0, 0.0)
                elif by_ > my1:
                    nv_ = (0.0, 1.0, 0.0)
                elif bx_ < mx0:
                    nv_ = (-1.0, 0.0, 0.0)
                elif bx_ > mx1:
                    nv_ = (1.0, 0.0, 0.0)
                else:
                    nv_ = (0.0, -1.0, 0.0)
                d_ = (main_d - 2e-3 - 1e-9 * (span * 10 - d_)) if facing(nv_) else (main_d + 1.0 + d_ * 1e-9)
            new_order.append((d_, g_, lst))
        order = new_order
        order.sort(key=lambda t: -t[0])                      # the far parts first
        for _d, _g, lst in order:
            solids, holes = [], []
            for pts, col, kind, hn in lst:
                nv = hn if kind == 'hole' else normal(pts)
                if not facing(nv):
                    continue                                 # turned away from you
                nl = math.sqrt(nv[0] ** 2 + nv[1] ** 2 + nv[2] ** 2) or 1.0
                lit = abs(nv[0] * light[0] + nv[1] * light[1] + nv[2] * light[2]) / nl
                k = 0.62 + 0.38 * lit
                vs = [view(q) for q in pts]
                item = (sum(v[1] for v in vs) / len(vs), [scr(v) for v in vs],
                        QColor(int(col[0] * k), int(col[1] * k), int(col[2] * k)), kind)
                (holes if kind == 'hole' else solids).append(item)
            solids.sort(key=lambda t: -t[0])
            for _dd, poly, qc, kind in solids + holes:
                p.setBrush(qc)
                if kind == 'hole':
                    p.setPen(QPen(QColor(240, 230, 195), 2.2))  # a cream frame round each window and door
                else:
                    p.setPen(QPen(QColor(70, 70, 75), 0.8))
                p.drawPolygon(QPolygonF(poly))
        if not whole or getattr(self, 'guessed', False):
            p.setPen(QColor(120, 120, 120))
            p.drawText(QRectF(8, self.height() - 20, self.width() - 16, 18), Qt.AlignLeft,
                       "Depth guessed till you set it (step 5)" if whole else "The rest comes as you do the steps")
        p.end()


class FrontPlan(QWidget):
    """The plan as it stands, looking down, front at the bottom."""

    def __init__(self, win, pickable=False):
        super().__init__(win)
        self.win = win
        self.pickable = pickable
        self._hit = []                       # [(part index in the job, polygon on screen)]
        self.setMinimumHeight(220)

    def mousePressEvent(self, ev):
        if not self.pickable:
            return
        pos = ev.position() if hasattr(ev, 'position') else ev.pos()
        from PySide6.QtGui import QPolygonF
        for k, poly in reversed(self._hit):
            if QPolygonF(poly).containsPoint(pos, Qt.OddEvenFill):
                self.win.sel_part = k
                self.win.update_all()
                return

    def paintEvent(self, _ev):
        from PySide6.QtGui import QPainter, QColor, QPen, QPolygonF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(32, 32, 36))
        p.setPen(QColor(215, 215, 215))
        p.drawText(QRectF(8, 4, self.width() - 16, 18), Qt.AlignLeft, "Looking down - the front at the bottom")
        try:
            b = self.win.build()
        except ValueError as e:
            p.setPen(QColor(170, 170, 170))
            p.drawText(QRectF(8, 26, self.width() - 16, 60), Qt.AlignLeft | Qt.TextWordWrap,
                       "The plan shows here as it comes together.\n" + str(e))
            p.end()
            return
        pts = [c for pr in b['parts'] for c in pr['corners']]
        mnx, mxx = min(c[0] for c in pts), max(c[0] for c in pts)
        mny, mxy = min(c[1] for c in pts), max(c[1] for c in pts)
        x0, y0, x1, y1 = 14.0, 30.0, self.width() - 14.0, self.height() - 26.0
        sc = min((x1 - x0) / max(mxx - mnx, 1.0), (y1 - y0) / max(mxy - mny, 1.0))
        cx = (x0 + x1) / 2.0 - (mnx + mxx) / 2.0 * sc
        cy = (y0 + y1) / 2.0 + (mny + mxy) / 2.0 * sc

        def P(c):
            return QPointF(cx + c[0] * sc, cy - c[1] * sc)
        jp = [k for k, bx in enumerate(self.win.f.get('parts') or []) if len(bx.get('clicks') or []) >= 2]
        self._hit = []
        for i, pr in enumerate(b['parts']):
            k = jp[i - 1] if 0 < i <= len(jp) else None
            picked = self.pickable and k is not None and k == self.win.sel_part
            col = QColor(255, 217, 26) if i == 0 else (QColor(77, 255, 255) if picked else QColor(215, 205, 225))
            p.setPen(QPen(col, 2 if i == 0 else (3 if picked else 1.5)))
            poly = [P(c) for c in pr['corners']]
            p.drawPolygon(QPolygonF(poly))
            if k is not None:
                self._hit.append((k, poly))
            mx = sum(c[0] for c in pr['corners']) / float(len(pr['corners']))
            my = sum(c[1] for c in pr['corners']) / float(len(pr['corners']))
            q = P((mx, my))
            p.drawText(QRectF(q.x() - 60, q.y() - 9, 120, 18), Qt.AlignCenter, pr['name'])
        for o in b['openings']:
            cs = b['parts'][o['part']]['corners']
            a, b2 = cs[o['wall'] % len(cs)], cs[(o['wall'] + 1) % len(cs)]
            ln = math.hypot(b2[0] - a[0], b2[1] - a[1]) or 1.0
            ux, uy = (b2[0] - a[0]) / ln, (b2[1] - a[1]) / ln
            p.setPen(QPen(QColor(*FCOLS['door' if o['kind'] == 'door' else 'window']), 4))
            p.drawLine(P((a[0] + ux * o['s0'], a[1] + uy * o['s0'])), P((a[0] + ux * o['s1'], a[1] + uy * o['s1'])))
        p.setPen(QColor(215, 215, 215))
        p.drawText(QRectF(8, self.height() - 20, self.width() - 16, 18), Qt.AlignLeft,
                   "%.2f x %.2f m (main building)" % (b['length'] / 1000.0, b['width'] / 1000.0))
        p.end()


# ---------------------------------------------------------------------------
# The window
# ---------------------------------------------------------------------------
def _form(page):
    fl = QFormLayout(page)
    fl.setHorizontalSpacing(6)
    fl.setVerticalSpacing(4)
    return fl


def _note(text, grey=False):
    lab = QLabel(text)
    lab.setWordWrap(True)
    if grey:
        lab.setStyleSheet("color: #555;")
    return lab


class PhotoDialog(QDialog):
    CUSTOM = "-- Custom --"

    def __init__(self, viewport, tool=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.user_presets = load_presets()
        self._busy = False
        self.result = None
        self.result_path = ''
        self._seen = 0.0
        self.built_tops = []
        st = load_settings()
        self.photo = st.get('photo', '')
        self.job_folder = st.get('last_job', '')

        lay = QVBoxLayout(self)
        self.info_box = QLabel(INFO_TEXT)
        self.info_box.setWordWrap(True)
        self.info_box.setVisible(False)
        lay.addWidget(self.info_box)

        side = QHBoxLayout()
        lay.addLayout(side, 1)
        self.views = QTabWidget()
        self.lbl_big = QLabel("No photo chosen yet.")
        self.lbl_big.setAlignment(Qt.AlignCenter)
        self.lbl_big.setMinimumSize(320, 300)
        self.views.addTab(self.lbl_big, "Photo")
        self.drawing = ResultDrawing()
        self.drawing.on_double = self.edit_plan
        self.views.addTab(self.drawing, "From the photo")
        from PySide6.QtWidgets import QScrollArea
        ks = QScrollArea()
        ks.setWidgetResizable(True)
        ks.setWidget(KeyDrawing())
        self.views.addTab(ks, "Key")
        self.views.setTabToolTip(0, "The photo you've picked.")
        self.views.setTabToolTip(1, "What came back from the 3D program: the plan and the front wall. "
                                     "Double-click it to change the plan.")
        self.views.setTabToolTip(2, "The sizes you might know (A to G) and the corners to click.")
        side.addWidget(self.views, 1)

        self.tabs = TwoRowTabs(1)
        side.addWidget(self.tabs, 1)
        self._photo_page(st)
        self._sizes_page()
        self._match_page()
        self._build_page()
        self._program_page(st)
        tips = ["Pick the photo of the building.",
                "One size you know, the floors and the roof.",
                "Click round the building on the photo (here, or in your 3D program).",
                "Build it with Floor Plan, cut the windows and doors, and carry on.",
                "Where your 3D program is, and where the work is saved."]
        for i, t in enumerate(tips):
            self.tabs.setTabToolTip(i, t)

        # ---- presets ----
        prow = QHBoxLayout()
        prow.addWidget(QLabel("Preset:"))
        self.cb_preset = QComboBox()
        try:
            self.cb_preset.setMinimumContentsLength(16)
            self.cb_preset.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        except Exception:
            pass
        prow.addWidget(self.cb_preset, 1)
        b_up = QPushButton("▲")
        b_up.setToolTip("Moves the preset you have open up the list.")
        b_dn = QPushButton("▼")
        b_dn.setToolTip("Moves the preset you have open down the list.")
        for b_ in (b_up, b_dn):
            b_.setFixedWidth(28)
            prow.addWidget(b_)
        self.btn_save = QPushButton("Save")
        b_saveas = QPushButton("Save as...")
        b_del = QPushButton("Delete")
        b_fold = QPushButton("Folder")
        for b_ in (self.btn_save, b_saveas, b_del, b_fold):
            prow.addWidget(b_)
        lay.addLayout(prow)

        brow = QHBoxLayout()
        self.btn_main = QPushButton("Start clicking round the building")
        self.btn_main.setDefault(True)
        self.b_info = QPushButton("Info")
        self.b_info.setCheckable(True)
        self.b_info.toggled.connect(self.info_box.setVisible)
        self.cb_lasttab = QCheckBox("Open at the last page used")
        self.cb_lasttab.setChecked(bool(st.get('remember_tab', True)))
        b_close = QPushButton("Close")
        brow.addWidget(self.btn_main)
        # the two most used, always there
        self.qb_carry = QPushButton("Carry on")
        self.qb_carry.setToolTip("Carry on with the last one (from the front)")
        self.qb_build = QPushButton("Build it")
        for b_ in (self.qb_carry, self.qb_build):
            b_.setMinimumHeight(30)
            b_.setMinimumWidth(110)
            brow.addWidget(b_)
        self.qb_carry.clicked.connect(lambda: self.front_it(carry_on=True))
        self.qb_keep = QPushButton("Keep the model's window places")
        self.qb_keep.setToolTip("Takes where the windows were last put on the model into the photo, so Carry on and "
                                "Send to Build keep them there - nothing is built or changed on the model")
        self.qb_keep.setMinimumHeight(30)
        brow.addWidget(self.qb_keep)
        self.qb_keep.clicked.connect(self.keep_model_places)
        self.qb_clear = QPushButton("Clear out old jobs")
        self.qb_clear.setToolTip("Deletes all the old jobs in the work folder - keeps the one you're on")
        self.qb_clear.setMinimumHeight(30)
        brow.addWidget(self.qb_clear)
        self.qb_clear.clicked.connect(self.clear_old_jobs)
        self.qb_build.clicked.connect(self.build_it)
        brow.addStretch(1)
        brow.addWidget(self.b_info)
        brow.addWidget(self.cb_lasttab)
        brow.addWidget(b_close)
        lay.addLayout(brow)
        self.lbl_status = QLabel()
        self.lbl_status.setWordWrap(True)
        lay.addWidget(self.lbl_status)
        self.cb_details = QCheckBox("Show details")
        self.cb_details.setChecked(bool(load_settings().get('show_details', False)))
        self.cb_details.setVisible(False)
        self.cb_details.toggled.connect(self._details)
        lay.addWidget(self.cb_details)
        lay.setSpacing(4)
        lay.setContentsMargins(8, 8, 8, 8)

        self.refresh_presets()
        self.set_values(st)
        self.cb_preset.currentIndexChanged.connect(self.apply_preset)
        b_up.clicked.connect(lambda: self.move_preset(-1))
        b_dn.clicked.connect(lambda: self.move_preset(1))
        self.btn_save.clicked.connect(self.save_preset)
        b_saveas.clicked.connect(lambda: self.save_preset_as())
        b_del.clicked.connect(self.delete_preset)
        b_fold.clicked.connect(lambda: self._open_in_windows(PRESET_DIR))
        self.btn_main.clicked.connect(self.match_it)
        b_close.clicked.connect(self.close)
        if self.cb_lasttab.isChecked():
            try:
                self.tabs.setCurrentIndex(int(st.get('tab', 0)))
            except Exception:
                pass
        self.tabs.currentChanged.connect(lambda i: save_settings(tab=int(i)))
        self.cb_lasttab.toggled.connect(lambda on: save_settings(remember_tab=bool(on)))
        last = st.get('last_preset')
        if last and last in self.preset_order():
            self.refresh_presets(select=last)
        # the last building that came back (if it's still there)
        if self.job_folder:
            rp = os.path.join(self.job_folder, RESULT_NAME)
            ap = os.path.join(self.job_folder, ADJUSTED_NAME)
            if os.path.isfile(rp):
                use = ap if os.path.isfile(ap) and os.path.getmtime(ap) > os.path.getmtime(rp) else rp
                try:
                    self.take_result(use, quiet=True)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    if use == ap:                         # the changed plan won't load: the one from the photo
                        try:
                            self.take_result(rp, quiet=True)
                            self.say("The changed plan (moved windows, resized parts) couldn't be read back (%s), so "
                                     "this is the building as it came from the photo." % e, True)
                        except Exception as e2:
                            self.say("The last building couldn't be read back: %s" % e2, True)
                    else:
                        self.say("The last building couldn't be read back: %s" % e, True)
                try:
                    self._seen = os.path.getmtime(rp)
                except Exception:
                    pass
        if self.result is None:
            self.find_last_building()
        self.refresh_buttons()
        # when the 3D program sends the building, take it in
        self._watch = QTimer(self)
        self._watch.timeout.connect(self.watch_job)
        self._watch.start(1500)

    # ---- pages ----
    def _page(self, title):
        from PySide6.QtWidgets import QScrollArea, QFrame
        pg = QWidget()
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setFrameShape(QFrame.NoFrame)
        sa.setWidget(pg)
        self.tabs.addTab(sa, title)
        return pg

    def _photo_page(self, st):
        from PySide6.QtWidgets import QListView
        lay = QVBoxLayout(self._page("Photo"))
        lay.addWidget(_note("Pick the main photo of the building, taken from a corner so two walls show. Long "
                            "straight edges (the eaves, the ground, rows of windows) make it measure better. Once "
                            "it's picked, double-click another to change it."))
        self.ed_folder = QLineEdit()
        self.ed_folder.setReadOnly(True)
        lay.addWidget(self.ed_folder)
        row = QHBoxLayout()
        b_choose = QPushButton("Choose folder...")
        b_open = QPushButton("Open folder")
        b_file = QPushButton("Choose a photo...")
        for b_ in (b_choose, b_open, b_file):
            row.addWidget(b_)
        row.addStretch(1)
        lay.addLayout(row)
        self.lst_pics = QListWidget()
        self.lst_pics.setViewMode(QListView.IconMode)
        self.lst_pics.setIconSize(QSize(96, 96))
        self.lst_pics.setGridSize(QSize(116, 128))
        self.lst_pics.setResizeMode(QListView.Adjust)
        self.lst_pics.setMovement(QListView.Static)
        self.lst_pics.setWordWrap(True)
        self.lst_pics.setToolTip("Click the photo of the building.")
        lay.addWidget(self.lst_pics, 1)
        self.lbl_pic = QLabel("No photo chosen.")
        self.lbl_pic.setWordWrap(True)
        self.lbl_pic.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl_pic)
        # more photos of the same building: other corners, the back, straight on to a wall
        lay.addWidget(_note("<b>More photos of this building</b> (the back, the ends, straight on to a wall): "
                            "click one above, then add it here."))
        self.lst_set = QListWidget()
        self.lst_set.setMaximumHeight(96)
        self.lst_set.setToolTip("The photos the 3D program opens. The first is the main one (taken from a corner).")
        lay.addWidget(self.lst_set)
        srow = QHBoxLayout()
        b_addc = QPushButton("Add as a corner photo")
        b_addw = QPushButton("Add as a straight-on photo")
        b_rem = QPushButton("Take it off")
        for b_ in (b_addc, b_addw, b_rem):
            srow.addWidget(b_)
        lay.addLayout(srow)
        b_addc.clicked.connect(lambda: self.add_extra('corner'))
        b_addw.clicked.connect(lambda: self.add_extra('wall'))
        b_rem.clicked.connect(self.remove_extra)
        self.extras = [e for e in (st.get('extra_photos') or []) if isinstance(e, dict) and e.get('path')]
        self.show_set()
        b_choose.clicked.connect(self.choose_folder)
        b_open.clicked.connect(lambda: self._open_in_windows(self.ed_folder.text()))
        b_file.clicked.connect(self.choose_file)
        self.lst_pics.itemClicked.connect(self.picture_clicked)
        self.lst_pics.itemDoubleClicked.connect(self.picture_double_clicked)
        self.set_folder(st.get('folder') or DEFAULT_PICTURES)

    def _sizes_page(self):
        pg = self._page("Sizes")
        fl = _form(pg)
        fl.addRow(_note("One size you know on the real building - the Key drawing shows which is which. "
                        "Everything else is measured from the photo and sized from it."))
        self.cb_known = QComboBox()
        for key, label in KNOWN:
            self.cb_known.addItem(label, key)
        fl.addRow(QLabel("Known size"), self.cb_known)
        self.sp = {}
        s = QDoubleSpinBox()
        s.setRange(1.0, 200000.0)
        s.setDecimals(0)
        s.setSingleStep(10.0)
        s.setSuffix(" mm")
        fl.addRow(QLabel("It is"), s)
        self.sp['known_mm'] = s
        fl.addRow(_note("A door is usually about 2000 mm high (Victorian ones 2100 mm or more). A course of "
                        "bricks is 75 mm - count them for a height.", True))
        self.sp_storeys = QSpinBox()
        self.sp_storeys.setRange(1, 20)
        fl.addRow(QLabel("Floors (storeys)"), self.sp_storeys)
        self.cb_roof = QComboBox()
        for label, key in ROOFS:
            self.cb_roof.addItem(label, key)
        fl.addRow(QLabel("Roof"), self.cb_roof)
        self.cb_low = QComboBox()
        for label, key in ROOF_LOW:
            self.cb_low.addItem(label, key)
        self.lab_low = QLabel("Low side")
        fl.addRow(self.lab_low, self.cb_low)
        self.cb_shape = QComboBox()
        for label, key in SHAPES:
            self.cb_shape.addItem(label, key)
        fl.addRow(QLabel("Shape"), self.cb_shape)
        s = QDoubleSpinBox()
        s.setRange(0.0, 100000.0)
        s.setDecimals(0)
        s.setSingleStep(100.0)
        s.setSuffix(" mm")
        s.setSpecialValueText("0 = I'll click corner 3")
        fl.addRow(QLabel("Depth if you can't see a side"), s)
        self.sp['depth_mm'] = s
        fl.addRow(_note("How deep the building is, front to back. Leave it at 0 if you can see the far end of "
                        "the side wall in the photo (you click it as corner 3). If it's hidden, type the depth "
                        "here and just click corners 1 and 2.", True))
        fl.addRow(_note("These are where the 3D program starts - you can change them in its panel too.", True))
        # measuring the outline from above, on a map: the most accurate start
        fl.addRow(_note("<b>Measure on a map</b> - the most accurate way to start: find the building from above, "
                        "measure its front and its depth (right-click, Measure distance), and type them here. "
                        "Measured roofs stick out past the walls, so take about 250 mm off each."))
        mrow = QHBoxLayout()
        self.ed_place = QLineEdit()
        self.ed_place.setPlaceholderText("Where it is, e.g. Llanfairpwll station")
        b_map = QPushButton("Open a map")
        mrow.addWidget(self.ed_place, 1)
        mrow.addWidget(b_map)
        fl.addRow(mrow)
        self.sp_map_len = QDoubleSpinBox()
        self.sp_map_dep = QDoubleSpinBox()
        for s_ in (self.sp_map_len, self.sp_map_dep):
            s_.setRange(0.0, 200000.0)
            s_.setDecimals(0)
            s_.setSingleStep(100.0)
            s_.setSuffix(" mm")
        fl.addRow(QLabel("Front (from the map)"), self.sp_map_len)
        fl.addRow(QLabel("Depth (from the map)"), self.sp_map_dep)
        b_use = QPushButton("Use these sizes")
        fl.addRow(b_use)
        b_map.clicked.connect(self.open_map)
        b_use.clicked.connect(self.use_map_sizes)
        self.ed_place.editingFinished.connect(lambda: save_settings(place=self.ed_place.text().strip()))
        self.ed_place.setText(load_settings().get('place', ''))
        for w_ in (self.cb_known, self.cb_roof, self.cb_low, self.cb_shape):
            w_.currentIndexChanged.connect(self.changed)
        self.sp_storeys.valueChanged.connect(self.changed)
        for s_ in self.sp.values():
            s_.valueChanged.connect(self.changed)

    def _match_page(self):
        from PySide6.QtWidgets import QRadioButton, QButtonGroup
        lay = QVBoxLayout(self._page("Match it"))
        lay.addWidget(_note("<b>Where to click round the building:</b>"))
        self.rb_here = QRadioButton("Here in IngeTrazo - no 3D program needed")
        self.rb_blender = QRadioButton("In the 3D program (Blender), as before")
        self.grp_where = QButtonGroup(self)
        self.grp_where.addButton(self.rb_here, 0)
        self.grp_where.addButton(self.rb_blender, 1)
        lay.addWidget(self.rb_here)
        lay.addWidget(self.rb_blender)
        (self.rb_blender if load_settings().get('where') == 'blender' else self.rb_here).setChecked(True)
        lay.addWidget(_note("The photo opens big, with the steps beside it:"))
        lay.addWidget(_note("1  <b>Parts</b> - the main building, and any wings, bays or porches.<br>"
                            "2  <b>Line up the edges</b> - drag the red lines onto two edges of one wall, the green "
                            "ones onto two edges of the wall round the corner. The blue grid then lies flat on "
                            "the ground.<br>"
                            "3  <b>Corners</b> - click where the walls meet the ground: 1 and 2 at the ends of the "
                            "front, 3 at the far end of the side wall.<br>"
                            "4  <b>Height</b> - click the top of a corner (the eaves).<br>"
                            "5  <b>Roof</b> - click the very top of the roof.<br>"
                            "6  <b>Windows and doors</b> - a box (two corners), half the shape (mirrored), all the way "
                            "round, or a copy of one you've done.<br>"
                            "7  <b>The size you know</b> - check it, then <b>Send</b>.<br><br>"
                            "More photos (the back, the ends, straight-on views of a wall) can be added at the top of "
                            "the steps, then set up on step 2. Either way can carry on where the other left off."))
        b_go = QPushButton("Start clicking round the building")
        b_go.setMinimumHeight(34)
        b_front = QPushButton("Start from the front - a new one (a face-on photo)")
        b_front.setMinimumHeight(34)
        b_front_on = QPushButton("Carry on from the front (the last one)")
        b_front_on.setMinimumHeight(30)
        self.b_front_on = b_front_on
        b_front.setToolTip("A photo straight on to the front does the widths, heights, windows, doors, bays and "
                           "wings in one go; the depth then comes from the corner photo, a side photo or a map.")
        self.b_again = QPushButton("Carry on with the last one")
        self.b_back = QPushButton("Get the building back")
        self.b_back.setToolTip("If the 3D program's Send didn't come through by itself: fetch it.")
        lay.addWidget(b_go)
        lay.addWidget(b_front)
        lay.addWidget(b_front_on)
        b_front.clicked.connect(lambda: self.front_it(fresh=True))
        b_front_on.clicked.connect(lambda: self.front_it(carry_on=True))
        row = QHBoxLayout()
        row.addWidget(self.b_again)
        row.addWidget(self.b_back)
        row.addStretch(1)
        lay.addLayout(row)
        self.lbl_job = _note("", True)
        lay.addWidget(self.lbl_job)
        lay.addStretch(1)
        b_go.clicked.connect(self.match_it)
        self.b_again.clicked.connect(self.carry_on_match)
        self.b_back.clicked.connect(self.get_back_clicked)
        self.grp_where.idClicked.connect(lambda i: save_settings(where='blender' if i == 1 else 'here'))

    def front_it(self, carry_on=False, fresh=False):
        """Start from the front: the face-on window, in this job's folder (a new job if there isn't one, or
        fresh: always a new one)."""
        folder = self.job_folder if (carry_on or self.job_folder) and self.job_folder and \
            os.path.isdir(self.job_folder) else None
        if fresh:
            folder = None
        if folder is None or not carry_on and not os.path.isfile(os.path.join(folder, "job.json")):
            vals = self.get_values()
            save_settings(**vals)
            try:
                _job, _script, folder = make_job(self.photo, vals, self.ed_work.text() or WORK_DIR, self.extras)
            except Exception as e:
                self.say("Couldn't get it ready: %s" % e, True)
                return
            self.job_folder = folder
            self._seen = time.time()
            save_settings(last_job=folder)
            self.refresh_buttons()
        w = getattr(self, 'front_win', None)
        try:
            if w is not None and w.isVisible():
                w.close()
        except Exception:
            pass
        try:
            w = FrontWindow(self, folder, self.photo, self.extras, self)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.say("Couldn't open the front window: %s" % e, True)
            return
        self.front_win = w
        w.show()
        self.say("Work through the front in its own window - Send there brings it back here.")

    def here(self):
        """Clicking round the building here in IngeTrazo (not in the 3D program)?"""
        return not self.rb_blender.isChecked()

    def open_clicking(self, folder, vals):
        """The clicking window for this job (the one open, if it's this job's)."""
        w = getattr(self, 'match_win', None)
        try:
            if w is not None and w.isVisible():
                if os.path.normcase(w.folder) == os.path.normcase(folder):
                    w.raise_()
                    w.activateWindow()
                    return
                w.close()
        except Exception:
            pass
        try:
            w = MatchWindow(self, folder, self.photo, self.extras, vals, self)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.say("Couldn't open the clicking window: %s" % e, True)
            return
        self.match_win = w
        w.show()
        self.say("Click round the building in its own window - Send there brings it back here.")

    def _build_page(self):
        pg = self._page("Build")
        fl = _form(pg)
        self.lbl_result = _note("Nothing clicked yet - Match it, then Send.")
        fl.addRow(self.lbl_result)
        self.b_plan = QPushButton("Change the plan (move, resize, copy parts)...")
        self.b_plan.setToolTip("Opens the plan in a window of its own: drag the parts to move them, drag their "
                               "edges or corners to resize them, and copy one to the other end.")
        fl.addRow(self.b_plan)
        s = QDoubleSpinBox()
        s.setRange(20.0, 1000.0)
        s.setDecimals(0)
        s.setSingleStep(10.0)
        s.setSuffix(" mm")
        fl.addRow(QLabel("H   Wall thickness"), s)
        self.sp['wall_t'] = s
        s.valueChanged.connect(self.changed)
        self.cb_snap = QCheckBox("Door bottoms on the floor")
        fl.addRow(self.cb_snap)
        self.cb_group = QCheckBox("Put it all in one group (bays and roof gables one piece each)")
        self.cb_group.setToolTip("The built building comes out as one group, with a group inside it for each part "
                                 "(Main building, Bay 1, Wing 1...), one for the roof gables and one for the "
                                 "fascia and barge boards.")
        self.cb_group.setChecked(True)
        fl.addRow(self.cb_group)
        self.cb_group.toggled.connect(self.changed)
        self.cb_snap.toggled.connect(self.changed)
        fl.addRow(_note("Floor Plan's other settings (floors, base, joints...) are the ones you used last in "
                        "Floor Plan.", True))
        self.b_build = QPushButton("Build it")
        self.b_build.setMinimumHeight(34)
        fl.addRow(self.b_build)
        self.b_fill = QPushButton("Fill in Floor Plan to check first")
        self.b_cut = QPushButton("Cut the windows and doors")
        self.cb_part = QComboBox()
        self.cb_part.setToolTip("Which part of the building to fill Floor Plan in with (the main building, a "
                                "wing, a bay...).")
        row = QHBoxLayout()
        row.addWidget(self.b_fill)
        row.addWidget(self.cb_part)
        fl.addRow(row)
        fl.addRow(self.b_cut)
        self.b_move = QPushButton("Move windows and doors...")
        self.b_move.setToolTip("After it's built: pick a wall, drag its windows and doors where they should be, "
                               "and the walls are cut again with the holes in their new places.")
        self.b_model = QPushButton("Move them on the model...")
        self.b_model.setToolTip("Click a window or door on the model, slide it along its wall (it snaps to the "
                                "others' edges), click to put it down - then click others to line them up to it.")
        row_m = QHBoxLayout()
        row_m.addWidget(self.b_move)
        row_m.addWidget(self.b_model)
        fl.addRow(row_m)
        self.b_move.clicked.connect(self.move_openings)
        self.b_model.clicked.connect(self.start_model_move)
        self.b_next = QPushButton("Next: 3 Frame  ▶")
        self.b_next.setMinimumHeight(30)
        fl.addRow(self.b_next)
        self.b_build.clicked.connect(self.build_it)
        self.b_plan.clicked.connect(self.edit_plan)
        self.b_fill.clicked.connect(self.fill_floor_plan)
        self.b_cut.clicked.connect(self.cut_clicked)
        self.b_next.clicked.connect(lambda: carry_on(self))

    def _program_page(self, st):
        lay = QVBoxLayout(self._page("Program"))
        lay.addWidget(_note("The 3D program the photo is matched in:"))
        self.ed_blender = QLineEdit()
        self.ed_blender.setPlaceholderText("Not found yet - click Find it or Choose...")
        lay.addWidget(self.ed_blender)
        row = QHBoxLayout()
        b_find = QPushButton("Find it")
        b_pick = QPushButton("Choose...")
        b_pick.setToolTip("Pick the program yourself.")
        row.addWidget(b_find)
        row.addWidget(b_pick)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addWidget(_note("The work (the 3D program's file, with your clicks) is saved in:"))
        self.ed_work = QLineEdit()
        self.ed_work.setReadOnly(True)
        lay.addWidget(self.ed_work)
        row2 = QHBoxLayout()
        b_work = QPushButton("Choose...")
        b_work.setToolTip("Pick the folder the work is saved in.")
        b_wopen = QPushButton("Open folder")
        row2.addWidget(b_work)
        row2.addWidget(b_wopen)
        row2.addStretch(1)
        lay.addLayout(row2)
        lay.addStretch(1)
        self.ed_blender.setText(find_blender(st.get('blender', '')))
        self.ed_work.setText(st.get('work_dir') or WORK_DIR)
        b_find.clicked.connect(self.find_blender_clicked)
        b_pick.clicked.connect(self.pick_blender)
        b_work.clicked.connect(self.pick_work)
        b_wopen.clicked.connect(lambda: self._open_in_windows(self.ed_work.text()))
        self.ed_blender.editingFinished.connect(lambda: save_settings(blender=self.ed_blender.text().strip()))

    # ---- measuring on a map ----
    def open_map(self):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        from urllib.parse import quote
        place = self.ed_place.text().strip()
        save_settings(place=place)
        if place:
            url = "https://www.google.com/maps/search/?api=1&query=%s" % quote(place)
        else:
            url = "https://www.google.com/maps/@?api=1&map_action=map&basemap=satellite"
        QDesktopServices.openUrl(QUrl(url))
        self.say("The map's opening in your web browser. Switch to the satellite view (Layers), zoom in on the "
                 "roof, right-click a corner > Measure distance and click the next corner. Type the front and the "
                 "depth here, then click Use these sizes.")

    def use_map_sizes(self):
        L, D = self.sp_map_len.value(), self.sp_map_dep.value()
        if L <= 0:
            QMessageBox.information(self, PLUGIN_NAME, "Type the front's length from the map first.")
            return
        self.cb_known.setCurrentIndex(max(0, self.cb_known.findData('wall1')))
        self.sp['known_mm'].setValue(L)
        if D > 0:
            self.cb_shape.setCurrentIndex(max(0, self.cb_shape.findData('rect')))
            self.sp['depth_mm'].setValue(D)
        self.say("Known size: the front wall, %.0f mm%s. In the 3D program, click the front's two corners (1 and 2)%s."
                 % (L, (", depth %.0f mm" % D) if D > 0 else "",
                    " and press Enter - the depth's done" if D > 0 else " and corner 3"))

    # ---- the photo ----
    def choose_folder(self):
        start = self.ed_folder.text() or DEFAULT_PICTURES
        try:
            opts = QFileDialog.Option.DontUseNativeDialog | QFileDialog.Option.ShowDirsOnly
        except Exception:
            opts = QFileDialog.DontUseNativeDialog | QFileDialog.ShowDirsOnly
        d = QFileDialog.getExistingDirectory(self, "The folder your photos are in", start, opts)
        if d:
            self.set_folder(os.path.normpath(d))
            save_settings(folder=os.path.normpath(d))

    def choose_file(self):
        start = os.path.dirname(self.photo) if self.photo else (self.ed_folder.text() or DEFAULT_PICTURES)
        try:
            opt = QFileDialog.Option.DontUseNativeDialog
        except Exception:
            opt = QFileDialog.DontUseNativeDialog
        p, _f = QFileDialog.getOpenFileName(self, "The photo of the building", start,
                                            "Photos (*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.webp);;All files (*)",
                                            options=opt)
        if p:
            p = os.path.normpath(p)
            self.set_folder(os.path.dirname(p))
            save_settings(folder=os.path.dirname(p))
            self.pick_photo(p)

    def set_folder(self, folder):
        from PySide6.QtGui import QIcon, QPixmap
        self.ed_folder.setText(folder or "")
        self.lst_pics.clear()
        if folder and os.path.isdir(folder):
            try:
                names = sorted(fn for fn in os.listdir(folder) if fn.lower().endswith(PICTURE_TYPES))
            except Exception:
                names = []
            for fn in names[:400]:
                path = os.path.join(folder, fn)
                it = QListWidgetItem(os.path.splitext(fn)[0])
                it.setData(Qt.UserRole, path)
                it.setToolTip(path)
                pm = QPixmap(path)
                if not pm.isNull():
                    it.setIcon(QIcon(pm.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
                self.lst_pics.addItem(it)
                if os.path.normcase(path) == os.path.normcase(self.photo or ""):
                    it.setSelected(True)
            if not names:
                self.lst_pics.addItem(QListWidgetItem("(no photos in this folder)"))
        self._show_photo()

    def picture_clicked(self, it):
        path = it.data(Qt.UserRole)
        if path:
            self._clicked = path
            if not self.photo or not os.path.isfile(self.photo) or not self.extras_mode():
                self.pick_photo(path)
            else:
                self.say("Picked %s - click Add as a corner photo or Add as a straight-on photo to add it, or "
                         "double-click it to make it the main photo." % os.path.basename(path))

    def extras_mode(self):
        """Once there's a main photo, a click picks a photo to add (a double-click changes the main one)."""
        return bool(self.photo)

    def picture_double_clicked(self, it):
        path = it.data(Qt.UserRole)
        if path:
            self.pick_photo(path)

    def show_set(self):
        self.lst_set.clear()
        if self.photo:
            self.lst_set.addItem("1   main (from a corner):   %s" % os.path.basename(self.photo))
        for k, e in enumerate(self.extras):
            self.lst_set.addItem("%d   %s:   %s" % (k + 2, "straight on to a wall" if e['kind'] == 'wall'
                                                   else "from another corner", os.path.basename(e['path'])))

    def add_extra(self, kind):
        path = getattr(self, '_clicked', '') or ''
        it = self.lst_pics.currentItem()
        if it is not None and it.data(Qt.UserRole):
            path = it.data(Qt.UserRole)
        if not path or not os.path.isfile(path):
            QMessageBox.information(self, PLUGIN_NAME, "Click the photo to add first (in the pictures above).")
            return
        if not self.photo:
            self.pick_photo(path)
            return
        if os.path.normcase(path) == os.path.normcase(self.photo) or \
                any(os.path.normcase(e['path']) == os.path.normcase(path) for e in self.extras):
            self.say("That photo's already in the set.", True)
            return
        self.extras.append({'path': path, 'kind': kind})
        save_settings(extra_photos=self.extras)
        self.show_set()
        self.say("Added. The 3D program opens it with the others - set it up on its step 2.")

    def remove_extra(self):
        r = self.lst_set.currentRow()
        if r <= 0:
            QMessageBox.information(self, PLUGIN_NAME, "Click one of the added photos (2 onwards) to take it off. "
                                                       "To change the main photo, double-click another picture.")
            return
        self.extras.pop(r - 1)
        save_settings(extra_photos=self.extras)
        self.show_set()

    def pick_photo(self, path):
        if self.photo and os.path.normcase(path) != os.path.normcase(self.photo) and getattr(self, 'extras', None):
            self.extras = []                               # a different building: its own set of photos
            save_settings(extra_photos=[])
        self.photo = path
        save_settings(photo=path)
        if hasattr(self, 'lst_set'):
            self.show_set()
        self._show_photo()
        self.views.setCurrentIndex(0)
        self.refresh_buttons()

    def _show_photo(self):
        from PySide6.QtGui import QPixmap
        if self.photo and os.path.isfile(self.photo):
            self.lbl_pic.setText("Photo: %s" % os.path.basename(self.photo))
            pm = QPixmap(self.photo)
            if pm.isNull():
                self.lbl_big.setPixmap(QPixmap())
                self.lbl_big.setText("%s\n\n(IngeTrazo can't show this kind of picture, but the 3D program can "
                                     "use it.)" % os.path.basename(self.photo))
            else:
                self.lbl_big.setPixmap(pm.scaled(420, 420, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.lbl_pic.setText("No photo chosen.")
            self.lbl_big.setPixmap(QPixmap())
            self.lbl_big.setText("No photo chosen yet.")

    # ---- the 3D program ----
    def find_blender_clicked(self):
        p = find_blender("")
        if p:
            self.ed_blender.setText(p)
            save_settings(blender=p)
            self.say("Found it: %s" % p)
        else:
            self.say("It wasn't found in the usual places - click Choose... and pick the program.", True)

    def pick_blender(self):
        start = self.ed_blender.text() or os.environ.get("ProgramFiles", "")
        try:
            opt = QFileDialog.Option.DontUseNativeDialog
        except Exception:
            opt = QFileDialog.DontUseNativeDialog
        p, _f = QFileDialog.getOpenFileName(self, "The 3D program", start, "Programs (*.exe);;All files (*)",
                                            options=opt)
        if p:
            p = _main_exe(os.path.normpath(p))
            self.ed_blender.setText(p)
            save_settings(blender=p)

    def pick_work(self):
        try:
            opts = QFileDialog.Option.DontUseNativeDialog | QFileDialog.Option.ShowDirsOnly
        except Exception:
            opts = QFileDialog.DontUseNativeDialog | QFileDialog.ShowDirsOnly
        d = QFileDialog.getExistingDirectory(self, "Save the work in", self.ed_work.text(), opts)
        if d:
            self.ed_work.setText(os.path.normpath(d))
            save_settings(work_dir=os.path.normpath(d))

    def _prog(self):
        prog = self.ed_blender.text().strip() or find_blender("")
        if not prog or not os.path.isfile(prog):
            self.tabs.setCurrentIndex(4)
            QMessageBox.information(self, PLUGIN_NAME, "The 3D program wasn't found. Click Find it, or Choose... "
                                                       "and pick it (Program page).")
            return None
        return prog

    def match_it(self):
        if not self.photo or not os.path.isfile(self.photo):
            self.tabs.setCurrentIndex(0)
            QMessageBox.information(self, PLUGIN_NAME, "Pick the photo of the building first (Photo page).")
            return
        if self.result is not None and QMessageBox.question(
                self, PLUGIN_NAME, "Start clicking round the building again, as a new job?\n\nThe building you have "
                "now stays saved in its folder.") != QMessageBox.Yes:
            return
        here = self.here()
        prog = None if here else self._prog()
        if not here and not prog:
            return
        vals = self.get_values()
        save_settings(**vals)
        try:
            job, script, folder = make_job(self.photo, vals, self.ed_work.text() or WORK_DIR, self.extras)
        except Exception as e:
            self.say("Couldn't get it ready: %s" % e, True)
            return
        if here:
            self.job_folder = folder
            self._seen = time.time()
            save_settings(last_job=folder)
            self.refresh_buttons()
            self.open_clicking(folder, vals)
            return
        msg, warn = open_blender(prog, script, job)
        self.say(msg, warn)
        if not warn:
            self.job_folder = folder
            self._seen = time.time()
            self._err_seen = time.time() - 1
            save_settings(last_job=folder)
            self.tabs.setCurrentIndex(2)
            self.refresh_buttons()

    def carry_on_match(self):
        if not self.job_folder or not os.path.isfile(os.path.join(self.job_folder, "job.json")):
            QMessageBox.information(self, PLUGIN_NAME, "There's no last one to carry on with - click Start clicking "
                                                       "round the building.")
            return
        fj, cj = os.path.join(self.job_folder, FRONT_NAME), os.path.join(self.job_folder, CLICKS_NAME)
        if os.path.isfile(fj) and (not os.path.isfile(cj) or os.path.getmtime(fj) >= os.path.getmtime(cj)):
            rp = os.path.join(self.job_folder, RESULT_NAME)
            self._seen = os.path.getmtime(rp) if os.path.isfile(rp) else time.time()
            self.front_it(carry_on=True)
            return
        if self.here():
            rp = os.path.join(self.job_folder, RESULT_NAME)
            self._seen = os.path.getmtime(rp) if os.path.isfile(rp) else time.time()
            try:
                with open(os.path.join(self.job_folder, "job.json"), "r", encoding="utf-8") as f:
                    jb = json.load(f)
            except Exception:
                jb = {}
            if jb.get('photo') and os.path.isfile(jb['photo']):
                self.photo = jb['photo']
            self.open_clicking(self.job_folder, self.get_values())
            return
        prog = self._prog()
        if not prog:
            return
        try:
            job, script, blend = reopen_job(self.job_folder, self.extras)
        except Exception as e:
            self.say("Couldn't open the last one: %s" % e, True)
            return
        rp = os.path.join(self.job_folder, RESULT_NAME)
        self._seen = os.path.getmtime(rp) if os.path.isfile(rp) else time.time()
        msg, warn = open_blender(prog, script, job, blend)
        self.say(msg, warn)

    def watch_job(self):
        if not self.job_folder:
            return
        ep = os.path.join(self.job_folder, "3D program problem.txt")
        try:
            if os.path.isfile(ep) and os.path.getmtime(ep) > getattr(self, '_err_seen', 0.0):
                self._err_seen = os.path.getmtime(ep)
                with open(ep, "r", encoding="utf-8", errors="replace") as f:
                    lines = [x for x in f.read().strip().splitlines() if x.strip()]
                self.say("The 3D program couldn't start Photo to Building: %s\n(the whole message is in %s - "
                         "send it to Claude)" % (lines[-1] if lines else "?", ep), True)
        except Exception:
            pass
        rp = os.path.join(self.job_folder, RESULT_NAME)
        try:
            if not os.path.isfile(rp):
                return
            t = os.path.getmtime(rp)
        except Exception:
            return
        if t <= self._seen + 0.01:
            return
        self._seen = t
        try:
            self.take_result(rp)
        except Exception as e:
            self.say("What the 3D program sent couldn't be read: %s" % e, True)
            return
        try:
            self.raise_()
            self.activateWindow()
        except Exception:
            pass

    def find_last_building(self):
        """The newest job (in the work folder) that has a building sent back - loaded, if there is one."""
        work = self.ed_work.text() or WORK_DIR
        best = None
        try:
            for nm in os.listdir(work):
                f = os.path.join(work, nm)
                for fn in (ADJUSTED_NAME, RESULT_NAME):
                    pth = os.path.join(f, fn)
                    if os.path.isfile(pth):
                        t = os.path.getmtime(pth)
                        if best is None or t > best[0]:
                            best = (t, f)
        except Exception:
            return False
        if best is None:
            return False
        f = best[1]
        rp, ap = os.path.join(f, RESULT_NAME), os.path.join(f, ADJUSTED_NAME)
        for use in ([ap] if os.path.isfile(ap) else []) + ([rp] if os.path.isfile(rp) else []):
            try:
                self.take_result(use, quiet=True)
                self.job_folder = f
                save_settings(last_job=f)
                self._seen = os.path.getmtime(use)
                self.say("Your last building is back (%s)." % os.path.basename(f))
                return True
            except Exception as e:
                print("%s: %s: %s" % (PLUGIN_NAME, use, e))
        return False

    def get_back_clicked(self):
        rp = os.path.join(self.job_folder, RESULT_NAME) if self.job_folder else ''
        if not rp or not os.path.isfile(rp):
            try:
                opt = QFileDialog.Option.DontUseNativeDialog
            except Exception:
                opt = QFileDialog.DontUseNativeDialog
            rp, _f = QFileDialog.getOpenFileName(self, "A building sent from the 3D program",
                                                 self.ed_work.text() or WORK_DIR,
                                                 "Building from a photo (*.json)", options=opt)
            if not rp:
                self.say("Nothing sent yet: click Send to IngeTrazo in the 3D program's Photo to Building panel.",
                         True)
                return
            self.job_folder = os.path.dirname(rp)
            save_settings(last_job=self.job_folder)
        try:
            self.take_result(rp)
            self._seen = os.path.getmtime(rp)
        except Exception as e:
            self.say("That couldn't be read: %s" % e, True)

    def take_result(self, path, quiet=False):
        r = read_result(path)
        self.result = r
        self.result_path = path
        self.drawing.set_result(r)
        nw = sum(1 for o in r.get('openings') or [] if o.get('kind') != 'door')
        nd = sum(1 for o in r.get('openings') or [] if o.get('kind') == 'door')
        rt = dict((b, a) for a, b in ROOFS).get(r.get('roof'), r.get('roof'))
        txt = ("<b>From the photo</b> (%s):<br>%d walls, %.0f x %.0f mm; %d floor%s, %.0f mm to the eaves%s.<br>"
               "Roof: %s%s.<br>%d window%s and %d door%s." % (
                   r.get('made', ''), len(r['corners']), r.get('length', 0), r.get('width', 0),
                   int(r.get('storeys') or 1), "" if int(r.get('storeys') or 1) == 1 else "s", r['eaves'],
                   (", %.0f mm to the top of the roof" % r['ridge']) if r.get('ridge') else "",
                   rt, (" at about %.1f°" % r['pitch']) if r.get('pitch') else "",
                   nw, "" if nw == 1 else "s", nd, "" if nd == 1 else "s"))
        parts = r.get('parts') or []
        if len(parts) > 1:
            txt += "<br>Parts: " + "; ".join("%s %.0f x %.0f mm, %.0f mm to the eaves" % (
                pt.get('name', ''), pt.get('length', 0), pt.get('width', 0), pt.get('eaves', 0)) for pt in parts[1:])
        if r.get('plan_changed'):
            txt += "<br><i>Plan changed here (%s).</i>" % r['plan_changed']
        self.lbl_result.setText(txt)
        self.cb_part.clear()
        for k, pt in enumerate(parts or [r]):
            self.cb_part.addItem(pt.get('name') or ("Main building" if k == 0 else "Part %d" % (k + 1)))
        self.cb_part.setVisible(len(parts) > 1)
        if not quiet:
            self.views.setCurrentIndex(1)
            self.tabs.setCurrentIndex(3)
            self.say("The building came back from the 3D program - check it on the left, then click Build it.")
        self.refresh_buttons()

    # ---- building ----
    def build_it(self):
        if not self.result:
            QMessageBox.information(self, PLUGIN_NAME, "Nothing clicked and sent yet (Match it page).")
            return
        vals = self.get_values()
        save_settings(**vals)
        try:
            keep_on_walls(self.result)
        except Exception as e:
            print("%s: keeping windows on their walls: %s" % (PLUGIN_NAME, e))
        scene = getattr(self.viewport, 'scene', None)
        old = [g for g in _top_groups(scene) if str(getattr(g, 'name', '') or '').startswith("Building - ")
               or str(getattr(g, 'name', '') or '') == "Building"]
        if old:
            a_ = QMessageBox.question(self, PLUGIN_NAME, "There's already a building from a photo in the model (%s).\n\n"
                                      "Replace it with the new one?\n(No: keep both.)" % ", ".join(
                                          str(g.name) for g in old), QMessageBox.Yes | QMessageBox.No |
                                      QMessageBox.Cancel)
            if a_ == QMessageBox.Cancel:
                return
            if a_ == QMessageBox.Yes:
                remove_groups(self.viewport, old)
        before = set(id(g) for g in _top_groups(scene))
        WALL_ORIG.clear()
        del BOARD_TOPS[:]
        try:                                              # what's being built, for tracking down problems
            r_ = self.result or {}
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "photo_to_building_clicks.txt"),
                      "a", encoding="utf-8") as fh:
                fh.write("BUILD %s\nparts: %s\nopenings: %s\nfrom: %s\n\n" % (
                    time.strftime("%H:%M:%S"), json.dumps([pr.get('corners') for pr in r_.get('parts') or []]),
                    json.dumps([{k: o.get(k) for k in ('kind', 'part', 'wall', 's0', 's1', 'z0', 'z1', 'box')}
                                for o in r_.get('openings') or []]), self.result_path))
        except Exception:
            pass
        tops, msg, bad = build_floor_plan(self.viewport, self.result, vals)
        if bad and not tops:
            self.say(msg, True)
            QMessageBox.warning(self, PLUGIN_NAME, msg)
            return
        self.built_tops = tops
        msg2, bad2 = cut_openings(self.viewport, self.result, tops, vals.get('snap_doors', True))
        bad2 = bad2 or bad
        if self.result.get('boards'):
            mb, bb = add_boards(self.viewport, self.result, tops, list(GABLE_TOPS))
            msg2 += "\n" + mb
            bad2 = bad2 or bb
        if vals.get('one_group', True):
            mg = group_building(self.viewport, before, tops, list(GABLE_TOPS), self.result,
                                self.result.get('name') or os.path.splitext(os.path.basename(self.photo or ''))[0])
            if mg:
                msg2 += "\n" + mg
        save_settings(last_built=self.result_path)
        parts = [p_.get('name') or "Part" for p_ in self.result.get('parts') or []]
        ng = len(self.result.get('gables') or [])
        mc = re.search(r"Cut (\d+) window", msg2)
        short = "Built: %s%s.%s%s Next: 3 Frame." % (
            ", ".join(parts), (", %d roof gable%s" % (ng, "" if ng == 1 else "s")) if ng else "",
            (" %s windows and doors cut." % mc.group(1)) if mc else "",
            " All in one group 'Building'." if vals.get('one_group', True) else "")
        self.say(msg + "\n" + msg2 + "\nInside walls: add them in Floor Plan if you want them (before Frame). "
                 "Next: 3 Frame.", bad2, short)
        self.refresh_buttons()

    def fill_floor_plan(self):
        if not self.result:
            QMessageBox.information(self, PLUGIN_NAME, "Nothing clicked and sent yet (Match it page).")
            return
        vals = self.get_values()
        save_settings(**vals)
        parts = self.result.get('parts') or [self.result]
        i = max(0, min(self.cb_part.currentIndex(), len(parts) - 1))
        if open_floor_plan_filled(self, parts[i], vals):
            more = (" Do the same for each part (pick it in the list next to the button)." if len(parts) > 1 else "")
            self.say("Floor Plan is filled in with %s from the photo. Check it, add any inside walls, click its "
                     "Build button.%s Then come back here and click Cut the windows and doors."
                     % (parts[i].get('name', 'the building').lower() if i == 0 else parts[i].get('name', 'the part'),
                        more))

    def cut_clicked(self):
        if not self.result:
            QMessageBox.information(self, PLUGIN_NAME, "Nothing clicked and sent yet (Match it page).")
            return
        vals = self.get_values()
        msg, bad = cut_openings(self.viewport, self.result, None, vals.get('snap_doors', True))
        self.say(msg, bad)

    def start_model_move(self):
        if not self.result or not self.result.get('openings'):
            QMessageBox.information(self, PLUGIN_NAME, "There are no windows or doors to move.")
            return
        if not WALL_ORIG or not ZREF:
            QMessageBox.information(self, PLUGIN_NAME, "Build it first (in this session) - then the windows and "
                                    "doors can be moved on the model.")
            return
        box_round_shapes(self.result)
        if getattr(self, 'mover', None) is None:
            self.mover = ModelMover(self)
        self.mover.reset()
        self.mover.log_miss((0.0, 0.0, 0.0))              # what it's working from, for checking
        try:
            self.move_tool = make_move_tool(self)
            self.viewport.set_active_tool(self.move_tool)
            self.viewport.setFocus()
        except Exception as e:
            self.say("Couldn't start moving on the model: %s" % e, True)
            return
        self._hidden_for_move = True
        self.hide()
        try:
            self.move_panel = MovePanel(self)
            self.move_panel.show()
            try:                                          # top right of the 3D view, out of the way
                from PySide6.QtCore import QPoint as _QP
                vp_ = self.viewport
                pnl_ = self.move_panel
                pnl_.adjustSize()
                g_ = vp_.mapToGlobal(_QP(max(0, vp_.width() - pnl_.width() - 24), 24))
                pnl_.move(g_)
            except Exception:
                pass
        except Exception as e:
            print("%s: the moving window: %s" % (PLUGIN_NAME, e))

    def stop_model_move(self):
        try:
            act = getattr(self.viewport.window(), "_activate_tool", None)
            if callable(act):
                act("select")
            else:
                self.viewport.set_active_tool(None)
        except Exception:
            pass
        self.model_move_gone(getattr(self, 'move_tool', None))

    def model_move_gone(self, tool):
        pnl = getattr(self, 'move_panel', None)
        if pnl is not None:
            try:
                pnl.close()
            except Exception:
                pass
            self.move_panel = None
        if getattr(self, '_hidden_for_move', False):
            self._hidden_for_move = False
            try:
                self.show()
                self.raise_()
            except Exception:
                pass
            self.say("Finished moving on the model - the new places are saved.", False)

    def write_back(self):
        """Windows and doors moved on the model (or in Move windows): their boxes on the front photo moved to
        match, so Carry on shows them there and Send to Build keeps them."""
        r = self.result or {}
        fm = r.get('front_map')
        folder = self.job_folder or os.path.dirname(self.result_path or '')
        if not fm or not folder:
            return 0
        M = maths()
        L, E, W, H = float(fm['L']), float(fm['E']), float(fm['W']), float(fm['H'])
        P = [tuple(q) for q in fm['P']]
        rect = [(0.0, 0.0), (L, 0.0), (L, E), (0.0, E)]
        Hm, Hi = M.homography(P, rect), M.homography(rect, P)
        if Hm is None or Hi is None:
            return 0
        to_mm = lambda c: M.hmap(Hm, c[0] * W, c[1] * H) or (0.0, 0.0)

        def to_ph(sv, zv):
            u, v = M.hmap(Hi, sv, zv) or (0.0, 0.0)
            return [u / W, v / H]
        fw = getattr(self, 'front_win', None)
        live = fw is not None and fw.isVisible() if fw is not None else False
        fdata = None
        if live:
            fdata = fw.f
        else:
            fp = os.path.join(folder, FRONT_NAME)
            try:
                with open(fp, "r", encoding="utf-8") as fh:
                    fdata = json.load(fh)
            except Exception:
                return 0
        boxes = fdata.get('boxes') or []

        def refit(bi, s0, s1, z0, z1, keep_across):
            """Box bi's clicks stretched from where they are to the new box (along the wall and up)."""
            if bi is None or not 0 <= bi < len(boxes):
                return False
            cl = boxes[bi].get('clicks') or []
            if len(cl) < 2:
                return False
            mm = [to_mm(c) for c in cl]
            os0, os1 = min(q[0] for q in mm), max(q[0] for q in mm)
            oz0, oz1 = min(q[1] for q in mm), max(q[1] for q in mm)
            if keep_across:
                s0, s1 = os0, os1
            fx = (s1 - s0) / max(os1 - os0, 1e-6)
            fz = (z1 - z0) / max(oz1 - oz0, 1e-6)
            boxes[bi]['clicks'] = [to_ph(s0 + (q[0] - os0) * fx, z0 + (q[1] - oz0) * fz) for q in mm]
            return True
        n = 0
        for o in r.get('openings') or []:
            bi = o.get('box')
            if bi is None:
                continue
            front = int(o.get('part', 0)) == 0 and int(o.get('wall', 0)) == 0
            if not front and int(o.get('part', 0)) == 0:
                continue                                  # on another wall of the main building: not on the photo
            z0, z1 = float(o['z0']), float(o['z1'])
            if o.get('box2') is not None and o.get('fan_h'):
                fh_ = float(o['fan_h'])                   # a door with its fanlight: two boxes on the photo
                n += refit(bi, o['s0'], o['s1'], z0, z1 - fh_, not front)
                n += refit(o['box2'], o['s0'], o['s1'], z1 - fh_, z1, not front)
            else:
                n += refit(bi, o['s0'], o['s1'], z0, z1, not front)   # on a bay: just its heights
                if not front and 0 <= bi < len(boxes):
                    # and where it is on the bay, remembered with its box (kept while its box isn't changed)
                    boxes[bi]['model'] = {'part': int(o.get('part', 0)), 'wall': int(o.get('wall', 0)),
                                          's0': o['s0'], 's1': o['s1'], 'z0': z0, 'z1': z1,
                                          'shape': o.get('shape'), 'top': o.get('top'),
                                          'clicks': [list(c) for c in boxes[bi].get('clicks') or []]}
        if not n:
            return 0
        if live:
            try:
                fw.save()
                fw.show_photo()
                fw.update_all()
            except Exception as e:
                print("%s: writing back: %s" % (PLUGIN_NAME, e))
        else:
            try:
                save_json(os.path.join(folder, FRONT_NAME), fdata)
            except Exception as e:
                print("%s: writing back: %s" % (PLUGIN_NAME, e))
                return 0
        return n

    def clear_old_jobs(self):
        """Every job folder in the work folder deleted, except the one being worked on."""
        import shutil
        work = self.ed_work.text() or WORK_DIR
        keep = os.path.normcase(os.path.abspath(self.job_folder)) if self.job_folder else ''
        old = []
        try:
            for nm in os.listdir(work):
                f = os.path.join(work, nm)
                if os.path.isfile(os.path.join(f, "job.json")) and os.path.normcase(os.path.abspath(f)) != keep:
                    old.append(f)
        except Exception:
            pass
        if not old:
            QMessageBox.information(self, PLUGIN_NAME, "No old jobs to clear.")
            return
        if QMessageBox.question(self, PLUGIN_NAME, "Delete %d old job%s?\nThe one you're on is kept.\n"
                                "This can't be undone." % (len(old), "" if len(old) == 1 else "s"),
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        gone = 0
        for f in old:
            try:
                shutil.rmtree(f)
                gone += 1
            except Exception as e:
                print("%s: %s: %s" % (PLUGIN_NAME, f, e))
        QMessageBox.information(self, PLUGIN_NAME, "Cleared %d old job%s." % (gone, "" if gone == 1 else "s") +
                                ("" if gone == len(old) else "\n%d couldn't be deleted (open somewhere?)." %
                                 (len(old) - gone)))

    def match_old_places(self, r):
        """Places saved by an older version (no box numbers): the front opened, and each window on the model
        matched to the window built from the photo nearest it on the same wall."""
        fw = getattr(self, 'front_win', None)
        if fw is None or not fw.isVisible():
            self.front_it(carry_on=True)
            fw = getattr(self, 'front_win', None)
        if fw is None:
            return False
        try:
            b = fw.build(guess_depth=True)
        except Exception as e:
            QMessageBox.information(self, PLUGIN_NAME, "Couldn't match them to the photo: %s" % e)
            return False
        pairs = []
        bo = [o for o in b.get('openings') or [] if o.get('box') is not None]
        ro = r.get('openings') or []
        for i, o in enumerate(ro):
            for j, q in enumerate(bo):
                if int(o.get('part', 0)) != int(q.get('part', 0)):
                    continue
                d = abs((o['s0'] + o['s1']) - (q['s0'] + q['s1'])) * 0.5 + \
                    abs((o['z0'] + o['z1']) - (q['z0'] + q['z1'])) * 0.5
                if int(o.get('wall', 0)) != int(q.get('wall', 0)):
                    d += 100000.0                          # another wall of the bay: only if nothing else fits
                pairs.append((d, i, j))
        pairs.sort()
        used_i, used_j = set(), set()
        for d, i, j in pairs:
            if i in used_i or j in used_j:
                continue
            used_i.add(i)
            used_j.add(j)
            for k in ('box', 'box2', 'fan_h'):
                if bo[j].get(k) is not None:
                    ro[i][k] = bo[j][k]
        r['front_map'] = b.get('front_map')
        if not used_i or not r['front_map']:
            QMessageBox.information(self, PLUGIN_NAME, "Couldn't match the windows on the model to the photo.")
            return False
        return True

    def keep_model_places(self):
        """The windows' places from the last time they were moved on the model (the job's plan changed file)
        put into the photo, without building."""
        folder = self.job_folder or os.path.dirname(self.result_path or '')
        ap = os.path.join(folder, ADJUSTED_NAME) if folder else ''
        if not ap or not os.path.isfile(ap):
            QMessageBox.information(self, PLUGIN_NAME, "There aren't any window places saved from the model for this "
                                    "job yet.")
            return
        try:
            with open(ap, "r", encoding="utf-8") as fh:
                r = json.load(fh)
        except Exception as e:
            QMessageBox.warning(self, PLUGIN_NAME, "Couldn't read the saved places: %s" % e)
            return
        if not any(o.get('box') is not None for o in r.get('openings') or []) or not r.get('front_map'):
            if not self.match_old_places(r):
                return
        old = self.result
        self.result = r
        try:
            n = self.write_back()
        finally:
            self.result = old
        QMessageBox.information(self, PLUGIN_NAME, ("Done - %d window places kept from the model (saved %s).\n"
                                                    "Carry on and Send to Build will keep them there." %
                                                    (n, r.get('plan_changed', "earlier"))) if n else
                                "Nothing to keep - no windows had been moved on the model.")

    def model_moved(self):
        """A window or door moved on the model: the walls cut again, and the new places saved."""
        msg, bad = cut_openings(self.viewport, self.result, None, self.get_values().get('snap_doors', True),
                                recut=True)
        try:
            self.write_back()
        except Exception as e:
            print("%s: writing back to the photo: %s" % (PLUGIN_NAME, e))
        if bad:
            print("%s: %s" % (PLUGIN_NAME, msg))
        folder = self.job_folder or os.path.dirname(self.result_path or '')
        if folder:
            try:
                self.result['plan_changed'] = time.strftime("%Y-%m-%d %H:%M:%S")
                ap = os.path.join(folder, ADJUSTED_NAME)
                save_json(ap, self.result)
                self.result_path = ap
            except Exception as e:
                print("%s: saving the moved windows: %s" % (PLUGIN_NAME, e))

    def move_openings(self):
        if not self.result:
            QMessageBox.information(self, PLUGIN_NAME, "Nothing clicked and sent yet (Match it page).")
            return
        if not self.result.get('openings'):
            QMessageBox.information(self, PLUGIN_NAME, "There are no windows or doors to move.")
            return
        snap = self.get_values().get('snap_doors', True)
        start = copy.deepcopy(self.result)

        def live(r_):
            if WALL_ORIG:
                cut_openings(self.viewport, r_, None, snap, recut=True)
        dlg = MoveOpeningsDialog(self.result, self, live if WALL_ORIG else None)
        if not dlg.exec():
            if dlg.moved_live:
                live(start)                               # cancelled: back as they were
            return
        folder = self.job_folder or os.path.dirname(self.result_path or '')
        ap = os.path.join(folder, ADJUSTED_NAME) if folder else ''
        try:
            dlg.r['plan_changed'] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_json(ap, dlg.r)
            self.take_result(ap, quiet=True)
        except Exception as e:
            self.result = dlg.r
            self.drawing.set_result(dlg.r)
            print("%s: saving the moved windows: %s" % (PLUGIN_NAME, e))
        if not WALL_ORIG:
            try:
                self.write_back()
            except Exception as e:
                print("%s: writing back to the photo: %s" % (PLUGIN_NAME, e))
            self.say("The new places are saved. The building wasn't built in this session, so the walls can't be "
                     "cut again here: delete the old building and click Build it.", True)
            return
        vals = self.get_values()
        msg, bad = cut_openings(self.viewport, self.result, None, vals.get('snap_doors', True), recut=True)
        try:
            self.write_back()
        except Exception as e:
            print("%s: writing back to the photo: %s" % (PLUGIN_NAME, e))
        self.say("Windows and doors moved.\n" + msg, bad, "Windows and doors moved.")

    def edit_plan(self):
        if not self.result:
            QMessageBox.information(self, PLUGIN_NAME, "Nothing clicked and sent yet (Match it page).")
            return
        folder = self.job_folder or os.path.dirname(self.result_path or '')
        dlg = PlanEditor(self.result, os.path.join(folder, RESULT_NAME) if folder else '', self)
        if not dlg.exec():
            return
        ap = os.path.join(folder, ADJUSTED_NAME) if folder else ''
        try:
            dlg.r['plan_changed'] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_json(ap, dlg.r)
            self.take_result(ap, quiet=True)
        except Exception as e:                            # couldn't save it: use it anyway, this time
            self.result = dlg.r
            self.drawing.set_result(dlg.r)
            print("%s: saving the changed plan: %s" % (PLUGIN_NAME, e))
        self.views.setCurrentIndex(1)
        self.tabs.setCurrentIndex(3)
        self.say("The plan's changed - click Build it. (If you send it again from the 3D program, it comes back "
                 "as clicked there: change the plan again.)")

    def refresh_buttons(self):
        has = self.result is not None
        for b_ in (self.b_build, self.b_fill, self.b_cut, self.b_plan, self.b_move, self.b_model):
            b_.setEnabled(has)
        self.b_build.setStyleSheet("QPushButton { background: #7ad67a; font-weight: bold; }" if has else "")
        qb = getattr(self, 'qb_build', None)
        if qb is not None:
            qb.setEnabled(has)
            qb.setStyleSheet("QPushButton { background: #7ad67a; font-weight: bold; }" if has else "")
        self.b_again.setEnabled(bool(self.job_folder and os.path.isfile(os.path.join(self.job_folder, "job.json"))))
        # the last job, ready to carry on: coloured so it stands out
        green = "QPushButton { background: #7ad67a; font-weight: bold; }"
        fo_ = self.job_folder if self.job_folder and os.path.isdir(self.job_folder) else None
        front_ok = bool(fo_ and os.path.isfile(os.path.join(fo_, FRONT_NAME)))
        b_fo = getattr(self, 'b_front_on', None)
        if b_fo is not None:
            b_fo.setEnabled(bool(fo_))
            b_fo.setStyleSheet(green if front_ok else "")
        qc = getattr(self, 'qb_carry', None)
        if qc is not None:
            qc.setEnabled(bool(fo_))
            qc.setStyleSheet(green if front_ok else "")
        clicks_ok = bool(fo_ and os.path.isfile(os.path.join(fo_, CLICKS_NAME)))
        self.b_again.setStyleSheet(green if clicks_ok and not front_ok else "")
        if self.job_folder:
            self.lbl_job.setText("Working on: %s" % os.path.basename(self.job_folder))

    # ---- odds and ends ----
    def say(self, text, bad=False, short=None):
        """The message under the buttons. With a short version, the full one only shows with Show details."""
        self._said = (text, bad, short)
        show = short is None or self.cb_details.isChecked()
        self.lbl_status.setText(text if show else short + "  (tick Show details for the rest)")
        self.lbl_status.setStyleSheet("color: #b00;" if bad else "color: #050;")
        self.cb_details.setVisible(short is not None)

    def _details(self, on):
        save_settings(show_details=bool(on))
        if getattr(self, '_said', None):
            self.say(*self._said)

    def _open_in_windows(self, folder):
        try:
            if folder:
                os.makedirs(folder, exist_ok=True)
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        except Exception as e:
            QMessageBox.information(self, PLUGIN_NAME, "Folder:\n%s\n\n(%s)" % (folder, e))

    # ---- values ----
    def get_values(self):
        v = {k: float(s.value()) for k, s in self.sp.items()}
        v.update(known_what=self.cb_known.currentData() or 'door_h', storeys=int(self.sp_storeys.value()),
                 roof=self.cb_roof.currentData() or 'gable_len', roof_low=self.cb_low.currentData() or 'front',
                 shape=self.cb_shape.currentData() or 'rect', snap_doors=self.cb_snap.isChecked(),
                 one_group=self.cb_group.isChecked())
        return v

    def set_values(self, d):
        self._busy = True
        try:
            for k, s in self.sp.items():
                if k in d and d[k] is not None:
                    try:
                        s.setValue(float(d[k]))
                    except (TypeError, ValueError):
                        pass
            for cb, key in ((self.cb_known, 'known_what'), (self.cb_roof, 'roof'), (self.cb_low, 'roof_low'),
                            (self.cb_shape, 'shape')):
                if key in d:
                    cb.setCurrentIndex(max(0, cb.findData(d[key])))
            if 'storeys' in d:
                self.sp_storeys.setValue(int(d['storeys'] or 1))
            if 'snap_doors' in d:
                self.cb_snap.setChecked(bool(d['snap_doors']))
            if 'one_group' in d:
                self.cb_group.setChecked(bool(d['one_group']))
        finally:
            self._busy = False
        self.changed()

    def changed(self, *_):
        mono = self.cb_roof.currentData() == 'mono'
        self.cb_low.setVisible(mono)
        self.lab_low.setVisible(mono)
        self.sp['depth_mm'].setEnabled(self.cb_shape.currentData() == 'rect')
        if self._busy:
            return
        save_settings(**self.get_values())

    # ---- presets ----
    def all_presets(self):
        d = dict(BUILTIN_PRESETS)
        d.update(self.user_presets)
        return d

    def preset_order(self):
        names = list(BUILTIN_PRESETS) + sorted(n for n in self.user_presets if n not in BUILTIN_PRESETS)
        order = [n for n in load_settings().get('preset_order', []) if n in names]
        return order + [n for n in names if n not in order]

    def move_preset(self, step):
        name = self.cb_preset.currentData()
        if not name:
            return
        order = self.preset_order()
        i = order.index(name)
        j = i + step
        if 0 <= j < len(order):
            order[i], order[j] = order[j], order[i]
            save_settings(preset_order=order)
            self.refresh_presets(select=name)

    def refresh_presets(self, select=None):
        self.cb_preset.blockSignals(True)
        self.cb_preset.clear()
        self.cb_preset.addItem(self.CUSTOM, None)
        for name in self.preset_order():
            self.cb_preset.addItem(name + ("  (built-in)" if name in BUILTIN_PRESETS else ""), name)
        if select:
            for i in range(self.cb_preset.count()):
                if self.cb_preset.itemData(i) == select:
                    self.cb_preset.setCurrentIndex(i)
                    break
        self.cb_preset.blockSignals(False)

    def apply_preset(self, _idx=None):
        name = self.cb_preset.currentData()
        save_settings(last_preset=name or None)
        p = self.all_presets().get(name) if name else None
        if p:
            self.set_values({k: v for k, v in p.items() if k in DEFAULTS})

    def save_preset(self):
        name = self.cb_preset.currentData()
        if name and name in self.user_presets and name not in BUILTIN_PRESETS:
            if self.save_preset_as(quiet_name=name):
                self.btn_save.setText("Saved")
                QTimer.singleShot(1500, lambda: self.btn_save.setText("Save"))
        else:
            self.save_preset_as(prefill=(name + " (my copy)") if name else "")

    def save_preset_as(self, prefill="", quiet_name=None):
        if quiet_name:
            name, ok = quiet_name, True
        else:
            name, ok = QInputDialog.getText(self, "Save preset", "Preset name:", QLineEdit.Normal, prefill)
        name = (name or "").strip()
        if not ok or not name:
            return False
        if name in BUILTIN_PRESETS:
            QMessageBox.warning(self, "Name in use", "That name belongs to a built-in preset. Choose another name.")
            return False
        if name in self.user_presets and not quiet_name:
            if QMessageBox.question(self, "Overwrite preset",
                                    "Preset '%s' already exists. Overwrite it?" % name) != QMessageBox.Yes:
                return False
        try:
            save_preset_file(name, self.get_values())
        except Exception as e:
            QMessageBox.warning(self, "Save failed", "Could not save the preset:\n%s" % e)
            return False
        self.user_presets = load_presets()
        self.refresh_presets(select=name)
        save_settings(last_preset=name)
        return True

    def delete_preset(self):
        name = self.cb_preset.currentData()
        if not name or name in BUILTIN_PRESETS or name not in self.user_presets:
            QMessageBox.information(self, PLUGIN_NAME, "Pick one of your own presets to delete "
                                                       "(built-in presets can't be deleted).")
            return
        if QMessageBox.question(self, "Delete preset", "Delete preset '%s'?" % name) != QMessageBox.Yes:
            return
        try:
            delete_preset_file(name)
        except Exception as e:
            QMessageBox.warning(self, PLUGIN_NAME, "Could not delete it:\n%s" % e)
        self.user_presets = load_presets()
        self.refresh_presets()


class PhotoToBuildingTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+Shift+P"
    description = ("A building started from a photo of a real one: match the photo in your 3D program, click "
                   "round the walls, windows, doors and roof, and it comes back filled into Floor Plan and "
                   "Openings, ready for the next step.")

    _dialog = None

    def on_activate(self, viewport):
        dlg = PhotoToBuildingTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.viewport = viewport
                    dlg.raise_()
                    dlg.activateWindow()
                    return
            except Exception:
                pass
        dialog = PhotoDialog(viewport, tool=self, parent=viewport)
        PhotoToBuildingTool._dialog = dialog

        def closed(*_):
            PhotoToBuildingTool._dialog = None
        dialog.finished.connect(closed)
        eddy_window(dialog, PLUGIN_NAME, EDDY_TIPS, place=True)
        dialog.show()

    def on_deactivate(self, viewport):
        pass


def run(viewport=None):
    PhotoToBuildingTool().on_activate(viewport)


# The 3D program's side: written into each job's folder and run there (it also keeps itself in the
# saved file, so the panel comes back when the file's opened again).
BLENDER_SCRIPT = '# Eddy\'s Model Works - Photo to Building, 3D program side.\n# Run by the Photo to Building plugin:  blender [saved.blend] --python photo_to_building_blender.py -- job.json\n# The photo is set up as a camera match: line up two edges along each wall of the building, and the\n# camera is worked out from where they meet (their vanishing points). Then click round the building -\n# the corners on the ground, the top of a corner, the top of the roof, two corners of each window and\n# door - and it\'s all measured off the photo, sized from the one size you know, and sent back.\n# Works with Blender 3.x to 5.x (nothing extra to install).\n\nimport json, math, os, sys, time\n\ntry:\n    import bpy\n    IN_BLENDER = True\nexcept ImportError:          # lets the maths be tested without the 3D program\n    IN_BLENDER = False\n\nEYE = 1.6                    # the camera\'s height above the ground, before the known size sizes it all\n\nKNOWN = [(\'wall1\', "A  Front wall (corner 1 to 2)"), (\'wall2\', "B  Side wall (to corner 3)"),\n         (\'eaves\', "C  Height to the eaves"), (\'ridge\', "D  Height to the top of the roof"),\n         (\'door_h\', "E  Height of the first door"), (\'win_w\', "F  Width of the first window"),\n         (\'win_h\', "G  Height of the first window")]\nROOFS = [(\'gable_len\', "Gable - ridge along the front (1-2)", "The ridge runs the same way as the front wall"),\n         (\'gable_across\', "Gable - gable end at the front (1-2)", "The front wall is a gable end"),\n         (\'hip\', "Hip - slopes on every side", ""), (\'mono\', "Lean-to - one slope", ""),\n         (\'flat\', "Flat roof", ""), (\'none\', "No roof", "")]\nTOPS = [(\'square\', "Square top", ""), (\'segment\', "Segmental arch", ""), (\'round\', "Round top", "")]\nLINE_KEYS = (\'r1\', \'r2\', \'g1\', \'g2\')\n\n\n# ---------------------------------------------------------------- maths (no 3D program needed)\ndef v_add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])\ndef v_sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])\ndef v_mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)\ndef v_dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]\ndef v_len(a): return math.sqrt(v_dot(a, a))\n\n\ndef v_cross(a, b):\n    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])\n\n\ndef v_norm(a):\n    n = v_len(a)\n    return v_mul(a, 1.0 / n) if n > 1e-12 else a\n\n\ndef start_lines():\n    """Where the four lines start (0..1 across and up the photo): red pair on the left, green pair on\n    the right, each pair closing in towards its own side - roughly how a building from a corner looks."""\n    return {\'r1\': [[0.12, 0.66], [0.44, 0.62]], \'r2\': [[0.12, 0.30], [0.44, 0.36]],\n            \'g1\': [[0.56, 0.62], [0.88, 0.66]], \'g2\': [[0.56, 0.36], [0.88, 0.30]]}\n\n\ndef meet2(l1, l2):\n    """Where two lines (each two points) cross, or None if they\'re (nearly) parallel."""\n    (x1, y1), (x2, y2) = l1\n    (x3, y3), (x4, y4) = l2\n    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)\n    s1 = math.hypot(x2 - x1, y2 - y1) * math.hypot(x4 - x3, y4 - y3)\n    if s1 < 1e-9 or abs(d) < 1e-4 * s1:\n        return None\n    a = x1 * y2 - y1 * x2\n    b = x3 * y4 - y3 * x4\n    return ((a * (x3 - x4) - (x1 - x2) * b) / d, (a * (y3 - y4) - (y1 - y2) * b) / d)\n\n\ndef solve_camera(lines, W, H):\n    """The camera from the lines (photo pixels, y up). Returns dict(f, M, C, vp) or raises ValueError.\n    M turns a world direction into the camera\'s (rows are the world axes as the camera sees them... its\n    columns are the world X, Y, Z axes in the camera\'s terms). World X runs along the red lines, Y along\n    the green ones, Z up; the camera stands EYE above the ground at x = y = 0."""\n    px = {k: [(p[0] * W, p[1] * H) for p in lines[k]] for k in LINE_KEYS}\n    vp1 = meet2(px[\'r1\'], px[\'r2\'])\n    vp2 = meet2(px[\'g1\'], px[\'g2\'])\n    if vp1 is None:\n        raise ValueError("The two red lines are side by side (parallel) - tilt them to follow the edges "\n                         "of one wall, which close in towards each other in the photo.")\n    if vp2 is None:\n        raise ValueError("The two green lines are side by side (parallel) - tilt them to follow the edges "\n                         "of the other wall.")\n    cx, cy = W / 2.0, H / 2.0\n    a = (vp1[0] - cx, vp1[1] - cy)\n    b = (vp2[0] - cx, vp2[1] - cy)\n    f2 = -(a[0] * b[0] + a[1] * b[1])\n    if f2 <= 1.0:\n        raise ValueError("The red and green lines don\'t fit together - the red ones should follow one wall "\n                         "and the green ones the wall round the corner (a photo taken from a corner works "\n                         "best).")\n    f = math.sqrt(f2)\n    d1 = v_norm((a[0], a[1], -f))\n    d2 = v_norm((b[0], b[1], -f))\n    d3 = v_cross(d1, d2)\n    if d3[1] < 0:                         # Z must point up the photo\n        d2 = v_mul(d2, -1.0)\n        d3 = v_mul(d3, -1.0)\n    d2 = v_norm(v_cross(d3, d1))          # tidy: exactly square to each other\n    M = [[d1[i], d2[i], d3[i]] for i in range(3)]     # camera = M * world\n    lens35 = f * 36.0 / max(W, H)\n    if lens35 < 4.0 or lens35 > 1500.0:\n        raise ValueError("The lines give an odd camera (a %.0f mm lens) - line them up again along "\n                         "straight edges, as long as you can make them." % lens35)\n    return {\'f\': f, \'M\': M, \'C\': (0.0, 0.0, EYE), \'vp\': [vp1, vp2], \'W\': W, \'H\': H, \'lens35\': lens35}\n\n\ndef to_cam(cam, d):\n    M = cam[\'M\']\n    return tuple(M[i][0] * d[0] + M[i][1] * d[1] + M[i][2] * d[2] for i in range(3))\n\n\ndef to_world(cam, d):\n    M = cam[\'M\']\n    return tuple(M[0][i] * d[0] + M[1][i] * d[1] + M[2][i] * d[2] for i in range(3))\n\n\ndef ray(cam, u, v):\n    """The ray through photo pixel (u, v): (start, direction) in the world."""\n    d = (u - cam[\'W\'] / 2.0, v - cam[\'H\'] / 2.0, -cam[\'f\'])\n    return cam[\'C\'], v_norm(to_world(cam, d))\n\n\ndef project(cam, P):\n    """The photo pixel a world point lands on, or None if it\'s behind the camera."""\n    q = to_cam(cam, v_sub(P, cam[\'C\']))\n    if q[2] > -1e-9:\n        return None\n    return (cam[\'W\'] / 2.0 + cam[\'f\'] * q[0] / -q[2], cam[\'H\'] / 2.0 + cam[\'f\'] * q[1] / -q[2])\n\n\ndef hit_plane(o, d, p0, n):\n    dn = v_dot(d, n)\n    if abs(dn) < 1e-12:\n        return None, None\n    t = v_dot(v_sub(p0, o), n) / dn\n    return t, v_add(o, v_mul(d, t))\n\n\ndef hit_ground(cam, u, v):\n    o, d = ray(cam, u, v)\n    if d[2] > -1e-9:\n        return None                       # above the horizon\n    t, h = hit_plane(o, d, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0))\n    return (h[0], h[1], 0.0) if t and t > 0 else None\n\n\ndef hit_level(cam, u, v, h):\n    """Where the ray through (u, v) meets a level plane h up - dropped to the ground below it (corners clicked\n    part way up the walls, where it\'s clearer than at the bottom)."""\n    o, d = ray(cam, u, v)\n    if abs(d[2]) < 1e-12:\n        return None\n    t = (h - o[2]) / d[2]\n    if t <= 0:\n        return None\n    p = v_add(o, v_mul(d, t))\n    return (p[0], p[1], 0.0)\n\n\ndef up_line(o, d, q):\n    """Where a ray passes closest to the upright line through ground point q: that point\'s height."""\n    w0 = v_sub(o, (q[0], q[1], 0.0))\n    e = (0.0, 0.0, 1.0)\n    a, b, c = v_dot(d, d), v_dot(d, e), 1.0\n    dd, ee = v_dot(d, w0), v_dot(e, w0)\n    den = a * c - b * b\n    if abs(den) < 1e-12:\n        return None\n    s = (a * ee - b * dd) / den\n    t = (b * ee - c * dd) / den\n    gap = v_len(v_sub(v_add(o, v_mul(d, t)), (q[0], q[1], s)))\n    return s, gap\n\n\nAXES = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, -1.0, 0.0)]\n\n\ndef snap_axis(d):\n    """The world axis (along the red or green lines) nearest to direction d (on the ground)."""\n    return max(AXES, key=lambda e: v_dot(d, e))\n\n\ndef area_xy(pts):\n    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]\n                     for i in range(len(pts)))\n\n\ndef ck(c):\n    """Which photo a click was made on (clicks are [across, up] or [across, up, photo])."""\n    return int(c[2]) if len(c) > 2 else 0\n\n\ndef view_of(views, c):\n    """(camera, u, v) for a click on a photo that\'s lined up (a corner photo), else None."""\n    k = ck(c)\n    if not 0 <= k < len(views) or views[k] is None or views[k].get(\'cam\') is None:\n        return None\n    cam = views[k][\'cam\']\n    return cam, c[0] * cam[\'W\'], c[1] * cam[\'H\']\n\n\ndef footprint(views, data, problems, depth_fn=None):\n    """The building\'s outline on the ground (world points, counter-clockwise from above), with the wall\n    from corner 1 to corner 2 first. Also the corners as clicked (snapped), for measuring.\n    depth_fn(A, B, y): the depth of a rectangle that runs back to something (the main building).\n    data[\'_len_units\']: the front\'s length (measured on a map), instead of where corner 2 was clicked."""\n    raw = []\n    cam = None\n    lvl = data.get(\'_level\')\n    for k, c in enumerate(data.get(\'corners\') or []):\n        vc = view_of(views, c)\n        g = (hit_level(vc[0], vc[1], vc[2], lvl) if lvl else hit_ground(*vc)) if vc else None\n        if g is None:\n            problems.append(("Corner %d is above the skyline - click where the wall meets the ground." % (k + 1))\n                            if vc else ("Corner %d was clicked on a photo that isn\'t lined up yet." % (k + 1)))\n            return None, []\n        cam = cam or vc[0]\n        raw.append(g)\n    if len(raw) < 2:\n        return None, raw\n    if data.get(\'shape\', \'rect\') == \'rect\' or depth_fn is not None:\n        A = raw[0]\n        e = snap_axis(v_sub(raw[1], A))                   # the first wall runs along the lines you lined up\n        B = v_add(A, v_mul(e, v_dot(v_sub(raw[1], A), e)))\n        if data.get(\'_len_units\'):                        # the front\'s length from the map\n            B = v_add(A, v_mul(v_norm(v_sub(B, A)), data[\'_len_units\']))\n        x = v_norm(v_sub(B, A))\n        y = (-x[1], x[0], 0.0)\n        cam_g = (cam[\'C\'][0], cam[\'C\'][1], 0.0)\n        if v_dot(v_sub(A, cam_g), y) < 0:                 # the building is on the far side of the first wall\n            y = v_mul(y, -1.0)\n        if depth_fn is not None:\n            D = depth_fn(A, B, y)\n            pts = [A, B]\n            if not D or D <= 1e-6:\n                problems.append("It doesn\'t reach back to the main building - click its two front corners, "\n                                "in front of the main building\'s wall.")\n                return None, pts\n        elif len(raw) >= 3:\n            D = v_dot(v_sub(raw[2], A), y)\n            if D <= 1e-6:\n                problems.append("Corner 3 should be the far end of a side wall (behind corner 2 or "\n                                "corner 1).")\n                return None, [A, B]\n            # which end of the first wall the side wall is at: the nearer one\n            near = B if abs(v_dot(v_sub(raw[2], B), x)) <= abs(v_dot(v_sub(raw[2], A), x)) else A\n            pts = [A, B, v_add(near, v_mul(y, D))]\n        else:\n            D = data.get(\'_depth_units\') or 0.0\n            pts = [A, B]\n            if D <= 0:\n                return None, pts\n        out = [A, B, v_add(B, v_mul(y, D)), v_add(A, v_mul(y, D))]\n    else:\n        pts = [raw[0]]\n        for g in raw[1:]:\n            e = snap_axis(v_sub(g, pts[-1]))              # walls run along the lines you lined up\n            pts.append(v_add(pts[-1], v_mul(e, v_dot(v_sub(g, pts[-1]), e))))\n        if len(pts) < 3:\n            return None, pts\n        out = list(pts)\n        ea = snap_axis(v_sub(out[-1], out[-2]))           # the last wall closes back to corner 1 squarely\n        out[-1] = v_add(out[-2], v_mul(ea, v_dot(v_sub(out[0], out[-2]), ea)))\n        clean = []\n        for p in out:\n            if not clean or v_len(v_sub(p, clean[-1])) > 1e-6:\n                clean.append(p)\n        if len(clean) > 2 and v_len(v_sub(clean[0], clean[-1])) < 1e-6:\n            clean.pop()\n        out = clean\n        if len(out) < 3:\n            problems.append("The corners don\'t make a shape - click round the building.")\n            return None, pts\n    if area_xy(out) < 0:\n        out.reverse()\n    # first: the wall from corner 1 to corner 2 (the front), running left to right\n    A, B = pts[0], pts[1]\n    bi = 0\n    for i in range(len(out)):\n        a, b = out[i], out[(i + 1) % len(out)]\n        if (v_len(v_sub(a, A)) < 1e-6 and v_len(v_sub(b, B)) < 1e-6) or \\\n                (v_len(v_sub(a, B)) < 1e-6 and v_len(v_sub(b, A)) < 1e-6):\n            bi = i\n            break\n    out = out[bi:] + out[:bi]\n    return out, pts\n\n\ndef back_to(main):\n    """For a part against the main building: how far back from its front it is to the main building\'s wall."""\n    def depth(A, B, y):\n        best = None\n        n = len(main)\n        for P in (A, B, v_mul(v_add(A, B), 0.5)):\n            for i in range(n):\n                a, b = main[i], main[(i + 1) % n]\n                uu = v_norm(v_sub(b, a))\n                nn = (uu[1], -uu[0], 0.0)                 # the main wall\'s outside\n                if v_dot(nn, y) > -0.5:\n                    continue                              # not facing the part\n                t, h = hit_plane(P, y, a, nn)\n                if t is None or t <= 1e-6:\n                    continue\n                s = v_dot(v_sub(h, a), uu)\n                L = v_len(v_sub(b, a))\n                if -0.02 * L <= s <= 1.02 * L and (best is None or t < best):\n                    best = t\n        return best\n    return depth\n\n\ndef plan_frame(outline):\n    """(origin, x, y): plan terms with the first wall along x from 0, the building behind it (+y)."""\n    O = outline[0]\n    x = v_norm(v_sub(outline[1], O))\n    y = (-x[1], x[0], 0.0)\n    return O, x, y\n\n\ndef to_plan(fr, P):\n    O, x, y = fr\n    d = v_sub(P, O)\n    return (v_dot(d, x), v_dot(d, y))\n\n\ndef from_plan(fr, px, py, z=0.0):\n    O, x, y = fr\n    return (O[0] + x[0] * px + y[0] * py, O[1] + x[1] * px + y[1] * py, z)\n\n\ndef nearest_corner(cam, outline, u, v):\n    o, d = ray(cam, u, v)\n    best = None\n    for q in outline:\n        r = up_line(o, d, q)\n        if r is None:\n            continue\n        if best is None or r[1] < best[1]:\n            best = (r[0], r[1], q)\n    return best\n\n\ndef wall_hit(cam, outline, u, v, top, wall=None, caps=None):\n    """Where the ray through (u, v) meets a wall: (wall index, along it, height) - the nearest outside\n    face it hits, or the face of the given wall. caps: how high each wall goes (else 1.6 x top)."""\n    o, d = ray(cam, u, v)\n    best = None\n    n_ = len(outline)\n    for i in range(n_):\n        if wall is not None and i != wall:\n            continue\n        a, b = outline[i], outline[(i + 1) % n_]\n        L = v_len(v_sub(b, a))\n        uu = v_norm(v_sub(b, a))\n        n = (uu[1], -uu[0], 0.0)\n        if wall is None and v_dot(d, n) >= 0:\n            continue                                      # looking at its back\n        t, h = hit_plane(o, d, a, n)\n        if t is None or t <= 0:\n            continue\n        s = v_dot(v_sub(h, a), uu)\n        z = h[2]\n        cap = caps[i] if caps else 1.6 * top\n        if wall is None and not (-0.02 * L <= s <= 1.02 * L and -0.1 * top <= z <= cap):\n            continue\n        if best is None or t < best[0]:\n            best = (t, i, s, z, L)\n    if best is None:\n        return None\n    t, i, s, z, L = best\n    if wall is not None:\n        s = min(max(s, 0.0), L)\n        z = max(z, 0.0)\n    return i, s, z, t\n\n\ndef roof_top(cam, outline, roof, low, u, v, eaves):\n    """The height of the top of the roof from the click: on the ridge (gables), above the middle (hip) or\n    along the high edge (lean-to)."""\n    if roof in (\'flat\', \'none\'):\n        return None\n    fr = plan_frame(outline)\n    pl = [to_plan(fr, p) for p in outline]\n    x0, x1 = min(p[0] for p in pl), max(p[0] for p in pl)\n    y0, y1 = min(p[1] for p in pl), max(p[1] for p in pl)\n    o, d = ray(cam, u, v)\n    _O, xa, ya = fr\n    if roof == \'hip\':\n        r = up_line(o, d, from_plan(fr, (x0 + x1) / 2.0, (y0 + y1) / 2.0))\n        return r[0] if r else None\n    if roof == \'gable_len\':\n        p0, n = from_plan(fr, 0.0, (y0 + y1) / 2.0), ya\n    elif roof == \'gable_across\':\n        p0, n = from_plan(fr, (x0 + x1) / 2.0, 0.0), xa\n    else:                                                 # lean-to: the high edge\n        p0, n = from_plan(fr, 0.0, y1 if low == \'front\' else y0), ya\n    t, h = hit_plane(o, d, p0, n)\n    return h[2] if t and t > 0 else None\n\n\nPART_KEYS = (\'shape\', \'depth_mm\', \'storeys\', \'roof\', \'roof_low\', \'against\', \'map_len\')\n\n\ndef new_part(name, against=False):\n    return {\'name\': name, \'corners\': [], \'eaves\': None, \'ridge\': None, \'shape\': \'rect\', \'depth_mm\': 0.0,\n            \'storeys\': 1, \'roof\': \'mono\' if against else \'gable_len\', \'roof_low\': \'front\', \'against\': against,\n            \'map_len\': 0.0}\n\n\ndef migrate(d):\n    """Clicks saved before there were parts: they\'re the main building."""\n    if not isinstance(d.get(\'parts\'), list) or not d[\'parts\']:\n        d[\'parts\'] = [new_part("Main building")]\n    p = d[\'parts\'][0]\n    for key in (\'corners\', \'eaves\', \'ridge\') + PART_KEYS:\n        if key in d and key != \'against\':\n            p[key] = d.pop(key)\n    p[\'corners\'] = p.get(\'corners\') or []\n    d[\'parts\'][0][\'against\'] = False\n    d.setdefault(\'cur\', 0)\n    d[\'cur\'] = min(max(0, int(d.get(\'cur\') or 0)), len(d[\'parts\']) - 1)\n    if d.get(\'steps_v\') != 2:                            # a new first step (the parts) was put in at 1.7\n        if d.get(\'step\'):\n            d[\'step\'] = int(d[\'step\']) + 1\n        d[\'steps_v\'] = 2\n    d.setdefault(\'openings\', [])\n    d.setdefault(\'gables\', [])\n    if not isinstance(d.get(\'photos\'), list) or not d[\'photos\']:\n        d[\'photos\'] = [{\'path\': \'\', \'kind\': \'corner\'}]\n    d[\'photos\'][0][\'kind\'] = \'corner\'\n    d[\'photo\'] = min(max(0, int(d.get(\'photo\') or 0)), len(d[\'photos\']) - 1) if isinstance(d.get(\'photo\'), int) \\\n        else 0\n    return d\n\n\ndef part_label(i, part):\n    return part.get(\'name\') or ("Main building" if i == 0 else "Part %d" % (i + 1))\n\n\ndef _solve(A, b):\n    """Solves A x = b (small, by elimination). None if it can\'t."""\n    n = len(b)\n    M = [list(A[i]) + [b[i]] for i in range(n)]\n    for c in range(n):\n        piv = max(range(c, n), key=lambda r: abs(M[r][c]))\n        if abs(M[piv][c]) < 1e-12:\n            return None\n        M[c], M[piv] = M[piv], M[c]\n        for r in range(n):\n            if r != c:\n                f = M[r][c] / M[c][c]\n                for k in range(c, n + 1):\n                    M[r][k] -= f * M[c][k]\n    return [M[i][n] / M[i][i] for i in range(n)]\n\n\ndef homography(src, dst):\n    """The 3x3 that takes 4 points src to 4 points dst (in a flat picture), or None."""\n    A, b = [], []\n    for (x, y), (X, Y) in zip(src, dst):\n        A.append([x, y, 1, 0, 0, 0, -X * x, -X * y])\n        b.append(X)\n        A.append([0, 0, 0, x, y, 1, -Y * x, -Y * y])\n        b.append(Y)\n    h = _solve(A, b)\n    if h is None:\n        return None\n    return [h[0:3], h[3:6], h[6:8] + [1.0]]\n\n\ndef hmap(Hm, x, y):\n    w = Hm[2][0] * x + Hm[2][1] * y + Hm[2][2]\n    if abs(w) < 1e-12:\n        return None\n    return ((Hm[0][0] * x + Hm[0][1] * y + Hm[0][2]) / w, (Hm[1][0] * x + Hm[1][1] * y + Hm[1][2]) / w)\n\n\ndef tie_in(cam_k, links, main_ol, W, H):\n    """Ties a second corner photo to the first: two corners of the main building clicked on it (which\n    corner each is) turn its camera into the first photo\'s world. Returns (camera, problem)."""\n    if main_ol is None:\n        return None, "the main building\'s corners (on photo 1) aren\'t finished yet"\n    ok = [l_ for l_ in links if l_.get(\'c\') and l_.get(\'corner\') is not None]\n    if len(ok) < 2:\n        return None, "click two of the main building\'s corners on it (step 2, Tie it in)"\n    g, w = [], []\n    for l_ in ok[:2]:\n        gp = hit_ground(cam_k, l_[\'c\'][0] * W, l_[\'c\'][1] * H)\n        if gp is None:\n            return None, "a tie-in corner is above the skyline - click where the wall meets the ground"\n        i = int(l_[\'corner\'])\n        if not 0 <= i < len(main_ol):\n            return None, "the main building has no corner %d" % (i + 1)\n        g.append(gp)\n        w.append(main_ol[i])\n    vk, vw = v_sub(g[1], g[0]), v_sub(w[1], w[0])\n    if v_len(vk) < 1e-9 or v_len(vw) < 1e-9:\n        return None, "pick two different corners to tie it in"\n    th = math.atan2(vw[1], vw[0]) - math.atan2(vk[1], vk[0])\n    sn = round(th / (math.pi / 2.0)) * (math.pi / 2.0)    # its walls run the same ways as photo 1\'s\n    if abs(math.atan2(math.sin(th - sn), math.cos(th - sn))) < math.radians(12):\n        th = sn\n    c, s_ = math.cos(th), math.sin(th)\n    rot = lambda p_: (c * p_[0] - s_ * p_[1], s_ * p_[0] + c * p_[1], p_[2])\n    rk = rot(vk)\n    sc = v_dot(vw, rk) / v_dot(rk, rk)\n    if sc <= 0:\n        return None, "the two tie-in corners are the wrong way round - swap them"\n    mk = v_mul(v_add(g[0], g[1]), 0.5)\n    mw = v_mul(v_add(w[0], w[1]), 0.5)\n    rm = rot(mk)\n    t = (mw[0] - sc * rm[0], mw[1] - sc * rm[1])\n    Ck = cam_k[\'C\']\n    rc = rot(Ck)\n    C = (sc * rc[0] + t[0], sc * rc[1] + t[1], sc * Ck[2])\n    R = [[c, s_, 0.0], [-s_, c, 0.0], [0.0, 0.0, 1.0]]       # world (photo 1) direction -> its own\n    Mk = cam_k[\'M\']\n    M = [[sum(Mk[i][j] * R[j][q] for j in range(3)) for q in range(3)] for i in range(3)]\n    cam = dict(cam_k)\n    cam.update(M=M, C=C)\n    return cam, None\n\n\ndef wall_view(part_ol, eaves, wall, quad, W, H):\n    """A straight-on photo of one wall: its 4 corners clicked (bottom left, bottom right, top right, top\n    left, seen from outside - the top ones under the gutter) give where everything on it is."""\n    if not part_ol or not eaves:\n        return None, "that part isn\'t finished yet (its corners and height)"\n    if len(quad) < 4:\n        return None, "click the wall\'s 4 corners (step 2)"\n    a, b = part_ol[wall % len(part_ol)], part_ol[(wall + 1) % len(part_ol)]\n    L = v_len(v_sub(b, a))\n    px = [(q[0] * W, q[1] * H) for q in quad[:4]]\n    wl = [(0.0, 0.0), (L, 0.0), (L, eaves), (0.0, eaves)]\n    Hm, Hi = homography(px, wl), homography(wl, px)\n    if Hm is None or Hi is None:\n        return None, "the wall\'s 4 corners don\'t make a shape - click them again"\n    u = v_norm(v_sub(b, a))\n    return {\'kind\': \'wall\', \'W\': W, \'H\': H, \'cam\': None, \'Hm\': Hm, \'Hi\': Hi, \'wall\': wall, \'a\': a, \'u\': u,\n            \'n\': (u[1], -u[0], 0.0), \'L\': L}, None\n\n\ndef _first_hit(cam, parts, u, v):\n    """The nearest outside wall of any part the ray through (u, v) meets: (part, (wall, along, up, t))."""\n    best = None\n    for pi, pm in enumerate(parts):\n        if not pm[\'outline\']:\n            continue\n        top = pm[\'eaves\'] or (parts[0][\'eaves\'] or 3.0 * EYE)\n        h = wall_hit(cam, pm[\'outline\'], u, v, top, caps=pm.get(\'caps\'))\n        if h is not None and (best is None or h[3] < best[1][3]):\n            best = (pi, h)\n    return best\n\n\ndef half_shape(pts):\n    """A whole outline from half of one (bottom corner, up the side, round the top to the peak in the\n    middle), mirrored about the peak: [(along, up)], anticlockwise seen from outside."""\n    sc = pts[-1][0]\n    half = list(pts)\n    other = [(2.0 * sc - p[0], p[1]) for p in reversed(half[:-1])]\n    poly = half + other\n    a = 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]\n                  for i in range(len(poly)))\n    if a < 0:\n        poly.reverse()\n    clean = []\n    for p in poly:\n        if not clean or abs(p[0] - clean[-1][0]) + abs(p[1] - clean[-1][1]) > 1e-9:\n            clean.append(p)\n    return clean\n\n\ndef all_round(pts):\n    """An outline clicked all the way round: anticlockwise seen from outside (None if under 3 points)."""\n    clean = []\n    for p in pts:\n        if not clean or abs(p[0] - clean[-1][0]) + abs(p[1] - clean[-1][1]) > 1e-9:\n            clean.append((p[0], p[1]))\n    if len(clean) < 3:\n        return None\n    a = 0.5 * sum(clean[i][0] * clean[(i + 1) % len(clean)][1] - clean[(i + 1) % len(clean)][0] * clean[i][1]\n                  for i in range(len(clean)))\n    if a < 0:\n        clean.reverse()\n    return clean\n\n\ndef wall_point(views, c):\n    """A click on a straight-on wall photo: (part, wall, along, up), else None."""\n    k = ck(c)\n    if not 0 <= k < len(views) or views[k] is None or views[k].get(\'kind\') != \'wall\':\n        return None\n    v = views[k]\n    q = hmap(v[\'Hm\'], c[0] * v[\'W\'], c[1] * v[\'H\'])\n    return (v[\'part\'], v[\'wall\'], q[0], q[1]) if q else None\n\n\ndef hit_any(views, parts, c):\n    """Where a click lands on a wall: (part, (wall, along, up, distance)) - from a lined-up photo (the\n    nearest wall it sees) or a straight-on one (its wall)."""\n    wp = wall_point(views, c)\n    if wp is not None:\n        return wp[0], (wp[1], wp[2], wp[3], 0.0)\n    vc = view_of(views, c)\n    return _first_hit(vc[0], parts, vc[1], vc[2]) if vc else None\n\n\ndef hit_same(views, parts, c, pi, wall):\n    """A further click of the same window, door or gable: on the same wall."""\n    wp = wall_point(views, c)\n    if wp is not None:\n        if wp[0] != pi or wp[1] != wall:\n            return None\n        return (wall, wp[2], max(0.0, wp[3]), 0.0)\n    vc = view_of(views, c)\n    if vc is None or not parts[pi][\'outline\']:\n        return None\n    return wall_hit(vc[0], parts[pi][\'outline\'], vc[1], vc[2], 1.0, wall=wall)\n\n\ndef opening_from(views, parts, op, done):\n    """One window or door from its clicks: a box (two corners), half traced (mirrored), all round, or a\n    copy of another one put where it\'s clicked. A dict, None (not finished), or a string saying what\'s wrong."""\n    cl = op.get(\'clicks\') or []\n    how = op.get(\'how\', \'box\')\n    kind = op.get(\'kind\', \'window\')\n    if how == \'copy\':\n        src = done.get(op.get(\'src\'))\n        if src is None or not cl:\n            return "the window it\'s copied from isn\'t there any more"\n        hit = hit_any(views, parts, cl[0])\n        if hit is None:\n            return "isn\'t on a wall you can see - click its bottom left corner on the wall"\n        pi, (wall, s, z, _t) = hit\n        ds, dz = s - src[\'s0\'], z - src[\'z0\']\n        shape = [(p[0] + ds, p[1] + dz) for p in src[\'shape\']] if src.get(\'shape\') else None\n        return {\'kind\': src[\'kind\'], \'top\': src[\'top\'], \'part\': pi, \'wall\': wall, \'s0\': s,\n                \'s1\': s + src[\'s1\'] - src[\'s0\'], \'z0\': max(0.0, z), \'z1\': z + src[\'z1\'] - src[\'z0\'], \'shape\': shape}\n    if len(cl) < 2:\n        return None\n    hit = hit_any(views, parts, cl[0])\n    if hit is None:\n        return "isn\'t on a wall you can see - click its corners on the wall"\n    pi, h1 = hit\n    pts = [(h1[1], h1[2])]\n    for c in cl[1:]:\n        h = hit_same(views, parts, c, pi, h1[0])\n        if h is None:\n            return "its clicks are on different photos or walls - do it again on one photo"\n        pts.append((h[1], h[2]))\n    if how in (\'trace\', \'outline\'):\n        shape = half_shape(pts) if how == \'trace\' else all_round(pts)\n        if not shape:\n            return None\n        ss, zz = [p[0] for p in shape], [p[1] for p in shape]\n        if max(ss) - min(ss) < 1e-6 or max(zz) - min(zz) < 1e-6:\n            return None\n        return {\'kind\': kind, \'top\': \'traced\', \'part\': pi, \'wall\': h1[0], \'s0\': min(ss), \'s1\': max(ss),\n                \'z0\': max(0.0, min(zz)), \'z1\': max(zz), \'shape\': [(p[0], max(0.0, p[1])) for p in shape]}\n    s0, s1 = sorted((pts[0][0], pts[1][0]))\n    z0, z1 = sorted((pts[0][1], pts[1][1]))\n    if s1 - s0 < 1e-6 or z1 - z0 < 1e-6:\n        return None\n    return {\'kind\': kind, \'top\': op.get(\'top\', \'square\'), \'part\': pi, \'wall\': h1[0],\n            \'s0\': s0, \'s1\': s1, \'z0\': max(0.0, z0), \'z1\': z1, \'shape\': None}\n\n\ndef photo_info(d, k):\n    """Photo k\'s size, lines and set-up (photo 1 - k = 0 - keeps its lines in the clicks themselves)."""\n    ph = (d.get(\'photos\') or [{}])[k] if k < len(d.get(\'photos\') or [{}]) else {}\n    if k == 0:\n        return dict(ph, W=d[\'W\'], H=d[\'H\'], lines=d[\'lines\'], kind=\'corner\')\n    return ph\n\n\ndef _part(i, part, views, out, k, main_ol, probs):\n    """One part\'s outline, height and roof (from whichever photos its clicks are on)."""\n    rough = False\n    depth_fn = None\n    if part.get(\'copy_of\') is not None:                   # a copy of another part, put where it\'s clicked\n        src = int(part[\'copy_of\'])\n        sp = out[\'parts\'][src] if 0 <= src < len(out[\'parts\']) else None\n        ol = None\n        if sp is None or not sp.get(\'outline\'):\n            if part.get(\'corners\'):\n                probs.append("the part it\'s a copy of isn\'t finished")\n        elif part.get(\'corners\'):\n            vc = view_of(views, part[\'corners\'][0])\n            g = hit_ground(*vc) if vc else None\n            if g is None:\n                probs.append("click its left front corner on the ground")\n            else:\n                so = sp[\'outline\']\n                x = v_norm(v_sub(so[1], so[0]))\n                sh = v_mul(x, v_dot(v_sub(g, so[0]), x))       # slid along the same line as the one copied\n                ol = [v_add(p_, sh) for p_ in so]\n        return {\'outline\': ol, \'raw\': ol[:2] if ol else [], \'eaves\': sp[\'eaves\'] if (ol and sp) else None,\n                \'ridge\': sp[\'ridge\'] if (ol and sp) else None, \'rough\': False,\n                \'caps\': sp.get(\'caps\') if (ol and sp) else None}\n    planned = None                                        # put on the plan by hand (hidden on the photos)\n    if i > 0 and part.get(\'plan\') and main_ol is not None and len(part[\'plan\']) >= 3:\n        frm = plan_frame(main_ol)\n        planned = [from_plan(frm, float(q[0]), float(q[1])) for q in part[\'plan\']]\n        if area_xy(planned) < 0:\n            planned.reverse()\n    if i > 0 and part.get(\'against\') and planned is None:\n        if main_ol is None:\n            if part.get(\'corners\'):\n                probs.append("Finish the main building first - this part runs back to it.")\n            return {\'outline\': None, \'raw\': [], \'eaves\': None, \'ridge\': None, \'rough\': False}\n        depth_fn = back_to(main_ol)\n    pd = dict(part)\n    level = None                                           # corners clicked part way up the walls\n    how_up = part.get(\'click_at\', \'ground\')\n    if how_up == \'up_main\' and i > 0:\n        level = (out[\'parts\'][0].get(\'level\') if out[\'parts\'] else None) or None\n        if level is None and part.get(\'corners\'):\n            probs.append("the main building\'s corners weren\'t clicked up the wall - pick another way")\n    elif how_up == \'up\' and part.get(\'corners\'):\n        vb = view_of(views, part[\'base\']) if part.get(\'base\') else None\n        g = hit_ground(*vb) if vb else None\n        cs_ = part[\'corners\']\n        found = None\n        if g is not None and not part.get(\'base_top\') and len(cs_) >= 2 and ck(cs_[0]) == ck(cs_[1]) == \\\n                ck(part[\'base\']):\n            # the point on the line straight above the foot: where the line from corner 1 to corner 2 (the front,\n            # at the clicked height) crosses the upright through the foot, in the photo\n            cam_, fu, fv = vb\n            W_, H_ = cam_[\'W\'], cam_[\'H\']\n            q_ = to_cam(cam_, (0.0, 0.0, 1.0))\n            if abs(q_[2]) < 1e-9:\n                up2 = (fu + q_[0] * 1000.0, fv + q_[1] * 1000.0)\n            else:\n                up2 = (W_ / 2.0 + cam_[\'f\'] * q_[0] / -q_[2], H_ / 2.0 + cam_[\'f\'] * q_[1] / -q_[2])\n            hit_ = meet2(((cs_[0][0] * W_, cs_[0][1] * H_), (cs_[1][0] * W_, cs_[1][1] * H_)), ((fu, fv), up2))\n            if hit_ is not None and hit_[1] > fv:\n                found = [hit_[0] / W_, hit_[1] / H_, ck(part[\'base\'])]\n        if g is None:\n            probs.append("set the height of the line: click the foot of the front wall, where it\'s clear")\n        else:\n            best = None\n            for c_ in ([part[\'base_top\']] if part.get(\'base_top\') else [found] if found else part[\'corners\']):\n                vc = view_of(views, c_)\n                if not vc:\n                    continue\n                o_, d_ = ray(vc[0], vc[1], vc[2])\n                r_ = up_line(o_, d_, g)\n                if r_ is not None and (best is None or r_[1] < best[1]):\n                    best = r_\n            if best is None or best[0] <= 0:\n                probs.append("the foot of the wall should be straight below the point on the line (on the pink line)")\n            else:\n                level = best[0]\n    if level and how_up in (\'up\', \'up_main\'):            # a line at the camera\'s own height can\'t be measured\n        flat = 0\n        for c_ in part.get(\'corners\') or []:\n            vc = view_of(views, c_)\n            if vc:\n                o_, d_ = ray(vc[0], vc[1], vc[2])\n                if abs(d_[2]) < 0.035:\n                    flat += 1\n        if flat:\n            probs.append("its corners are on a line at the camera\'s own height (the dashed eye-level line) - "\n                         "they can\'t be measured there: click them on a line well above it (the gutters) or "\n                         "below it (the bottom of the plinth)")\n    if level:\n        pd[\'_level\'] = level\n    if depth_fn is None and part.get(\'shape\', \'rect\') == \'rect\' and len(part.get(\'corners\') or []) == 2 \\\n            and float(part.get(\'depth_mm\') or 0.0) > 0:\n        pd[\'_depth_units\'] = float(part[\'depth_mm\']) / (k or 1000.0)\n        rough = not k\n    if i > 0 and float(part.get(\'map_len\') or 0.0) > 0 and part.get(\'shape\', \'rect\') == \'rect\':\n        pd[\'_len_units\'] = float(part[\'map_len\']) / (k or 1000.0)      # the front from the map\n        rough = rough or not k\n    if planned is not None:\n        ol, raw = planned, planned[:2]\n    else:\n        ol, raw = footprint(views, pd, probs, depth_fn)\n    if ol is None and depth_fn is None and part.get(\'shape\', \'rect\') == \'rect\' and len(raw) == 2 and \\\n            not float(part.get(\'depth_mm\') or 0.0) and not probs:\n        probs.append("only 2 corners - click corner 3 on the ground, or type its depth under More")\n    eaves = ridge = None\n    pts = ol or (raw if len(raw) >= 2 else None)\n    if pts and part.get(\'eaves\'):\n        vc = view_of(views, part[\'eaves\'])\n        r = nearest_corner(vc[0], pts, vc[1], vc[2]) if vc else None\n        if r is not None and r[0] > 0:\n            eaves = r[0]\n        elif vc:\n            probs.append("The top of the corner (eaves) is below the ground - click the top of a corner.")\n    same = part.get(\'same_as\')\n    same = out[\'parts\'][int(same)] if same is not None and 0 <= int(same) < len(out[\'parts\']) else None\n    if pts and eaves is None and not part.get(\'eaves\'):     # not clicked: the same as another, or typed\n        if same is not None and same.get(\'eaves\'):\n            eaves = same[\'eaves\']\n        elif float(part.get(\'eaves_mm\') or 0.0) > 0:\n            eaves = float(part[\'eaves_mm\']) / (k or 1000.0)\n            rough = rough or not k\n    if ol and eaves and part.get(\'ridge\'):\n        vc = view_of(views, part[\'ridge\'])\n        z = roof_top(vc[0], ol, part.get(\'roof\', \'gable_len\'), part.get(\'roof_low\', \'front\'), vc[1], vc[2],\n                     eaves) if vc else None\n        if z is not None:\n            if z <= eaves:\n                probs.append("The top of the roof comes out lower than the eaves - click the very top of "\n                             "the roof (the ridge).")\n            else:\n                ridge = z\n    if ol and eaves and ridge is None and not part.get(\'ridge\'):\n        if same is not None and same.get(\'ridge\'):\n            ridge = same[\'ridge\']\n        elif float(part.get(\'ridge_mm\') or 0.0) > 0 and float(part[\'ridge_mm\']) / (k or 1000.0) > eaves:\n            ridge = float(part[\'ridge_mm\']) / (k or 1000.0)\n            rough = rough or not k\n    caps = None\n    if ol and eaves:                                      # walls stop at the eaves, gable ends at the ridge\n        roof = part.get(\'roof\', \'gable_len\')\n        caps = []\n        e0 = v_norm(v_sub(ol[1], ol[0]))\n        for i_ in range(len(ol)):\n            e = v_norm(v_sub(ol[(i_ + 1) % len(ol)], ol[i_]))\n            along = abs(v_dot(e, e0)) > 0.7\n            gable = (roof == \'gable_len\' and not along) or (roof == \'gable_across\' and along) or \\\n                (roof == \'mono\' and not along)\n            caps.append((ridge or eaves * 1.6) * 1.05 if gable else eaves * 1.05)\n    return {\'outline\': ol, \'raw\': raw, \'eaves\': eaves, \'ridge\': ridge, \'rough\': rough, \'caps\': caps,\n            \'level\': level, \'level_at\': found if how_up == \'up\' and part.get(\'corners\') and part.get(\'base\') else None}\n\n\ndef _build(cams, data, k):\n    """The parts\' outlines, heights and roofs, and the windows and doors - from every photo - with the scale\n    k (mm a unit) if it\'s known yet (for depths and lengths typed in). cams: each corner photo\'s own camera."""\n    n_ph = len(data[\'photos\'])\n    views = [None] * n_ph\n    out = {\'parts\': [], \'openings\': [], \'problems\': [], \'sizes\': {}, \'views\': views, \'photo_problems\': {}}\n    pr = out[\'problems\']\n    php = out[\'photo_problems\']\n    views[0] = {\'kind\': \'corner\', \'cam\': cams[0], \'W\': data[\'W\'], \'H\': data[\'H\']}\n    # the main building\'s corners: on photo 1, which everything else is tied to\n    main = data[\'parts\'][0]\n    if any(ck(c_) != 0 for c_ in main.get(\'corners\') or []):\n        pr.append("Click the main building\'s corners on photo 1 - the other photos are tied to them.")\n    main_geo = _part(0, dict(main, corners=[c_ for c_ in main.get(\'corners\') or [] if ck(c_) == 0]),\n                     views, {\'parts\': []}, k, None, [])\n    main_ol = main_geo[\'outline\']\n    # the other photos: corner ones tied in by two corners, straight-on ones by a wall\'s 4 corners (later)\n    for j in range(1, n_ph):\n        ph = photo_info(data, j)\n        if ph.get(\'kind\') != \'corner\':\n            continue\n        if cams.get(j) is None:\n            php[j] = cams.get((\'why\', j)) or "line up its edges (step 2)"\n            continue\n        cam, why = tie_in(cams[j], ph.get(\'link\') or [], main_ol, ph[\'W\'], ph[\'H\'])\n        if cam is None:\n            php[j] = why\n            continue\n        views[j] = {\'kind\': \'corner\', \'cam\': cam, \'W\': ph[\'W\'], \'H\': ph[\'H\']}\n    main_ol = None\n    for i, part in enumerate(data[\'parts\']):\n        probs = []\n        geo = _part(i, part, views, out, k, main_ol, probs)\n        out[\'parts\'].append(geo)\n        pr += [("%s: %s" % (part_label(i, part), x)) if i else x for x in probs]\n        if i == 0:\n            main_ol = geo[\'outline\']\n    for j in range(1, n_ph):\n        ph = photo_info(data, j)\n        if ph.get(\'kind\') != \'wall\':\n            continue\n        pi = int(ph.get(\'part\') or 0)\n        pm = out[\'parts\'][pi] if pi < len(out[\'parts\']) else {}\n        v, why = wall_view(pm.get(\'outline\'), pm.get(\'eaves\'), int(ph.get(\'wall\') or 0), ph.get(\'quad\') or [],\n                           ph[\'W\'], ph[\'H\'])\n        if v is None:\n            php[j] = why\n            continue\n        v[\'part\'] = pi\n        views[j] = v\n    # windows and doors: on whichever part\'s wall each one is clicked on (the nearest one seen)\n    ops = []\n    by_index = {}\n    for n_, op in enumerate(data.get(\'openings\') or []):\n        o = opening_from(views, out[\'parts\'], op, by_index)\n        if isinstance(o, str):\n            pr.append("%s %d: %s" % (op.get(\'kind\', \'window\').capitalize(), n_ + 1, o))\n            continue\n        if o is None:\n            continue\n        o[\'idx\'] = n_\n        by_index[n_] = o\n        ops.append(o)\n    out[\'openings\'] = ops\n    # gables on the front of a roof: their two corners at the eaves and the peak, on a wall\n    gs = []\n    for n_, gb in enumerate(data.get(\'gables\') or []):\n        cl = gb.get(\'clicks\') or []\n        if len(cl) < 3:\n            continue\n        hit = hit_any(views, out[\'parts\'], cl[0])\n        if hit is None:\n            pr.append("Roof gable %d isn\'t on a wall you can see - click its corners where it meets the eaves."\n                      % (n_ + 1))\n            continue\n        pi, h1 = hit\n        h2 = hit_same(views, out[\'parts\'], cl[1], pi, h1[0])\n        h3 = hit_same(views, out[\'parts\'], cl[2], pi, h1[0])\n        if h2 is None or h3 is None:\n            continue\n        s0, s1 = sorted((h1[1], h2[1]))\n        z0 = out[\'parts\'][pi][\'eaves\'] or (h1[2] + h2[2]) / 2.0\n        if s1 - s0 < 1e-6 or h3[2] <= z0:\n            pr.append("Roof gable %d: click its two corners at the eaves, then its peak." % (n_ + 1))\n            continue\n        gs.append({\'part\': pi, \'wall\': h1[0], \'s0\': s0, \'s1\': s1, \'z0\': z0, \'peak\': h3[2], \'sp\': h3[1]})\n    out[\'gables\'] = gs\n    # the sizes you might know (the main building, and the first door and window)\n    meas = out[\'sizes\']\n    mn = out[\'parts\'][0] if out[\'parts\'] else {\'raw\': [], \'eaves\': None, \'ridge\': None}\n    raw = mn[\'raw\']\n    if len(raw) >= 2:\n        meas[\'wall1\'] = v_len(v_sub(raw[1], raw[0]))\n    if len(raw) >= 3:\n        meas[\'wall2\'] = v_len(v_sub(raw[2], raw[1])) if data[\'parts\'][0].get(\'shape\', \'rect\') != \'rect\' else \\\n            min(v_len(v_sub(raw[2], raw[1])), v_len(v_sub(raw[2], raw[0])))\n    if mn[\'eaves\']:\n        meas[\'eaves\'] = mn[\'eaves\']\n    if mn[\'ridge\']:\n        meas[\'ridge\'] = mn[\'ridge\']\n    doors = [o for o in ops if o[\'kind\'] == \'door\']\n    wins = [o for o in ops if o[\'kind\'] == \'window\']\n    if doors:\n        meas[\'door_h\'] = doors[0][\'z1\'] - (0.0 if doors[0][\'z0\'] < 0.15 * EYE else doors[0][\'z0\'])\n    if wins:\n        meas[\'win_h\'] = wins[0][\'z1\'] - wins[0][\'z0\']\n        meas[\'win_w\'] = wins[0][\'s1\'] - wins[0][\'s0\']\n    what, mm = data.get(\'known_what\', \'door_h\'), float(data.get(\'known_mm\') or 0.0)\n    m_ = meas.get(what)\n    out[\'k\'] = mm / m_ if (m_ and mm > 0) else None          # mm for each unit\n    return out\n\n\ndef compute(data):\n    """Everything measured from the clicks on every photo: the cameras, each part, the windows and doors,\n    the scale - with \'problems\'. (Sizes typed in need the scale: worked out roughly first, then again.)"""\n    migrate(data)\n    cams = {}\n    try:\n        cams[0] = solve_camera(data[\'lines\'], data[\'W\'], data[\'H\'])\n    except ValueError as e:\n        return {\'problems\': [str(e)], \'cam\': None, \'outline\': None, \'raw\': [], \'eaves\': None, \'ridge\': None,\n                \'openings\': [], \'k\': None, \'sizes\': {}, \'parts\': [], \'gables\': [], \'views\': [None] * len(data[\'photos\']),\n                \'photo_problems\': {}}\n    for j in range(1, len(data[\'photos\'])):\n        ph = photo_info(data, j)\n        if ph.get(\'kind\') == \'corner\' and ph.get(\'lines\') and ph.get(\'W\'):\n            try:\n                cams[j] = solve_camera(ph[\'lines\'], ph[\'W\'], ph[\'H\'])\n            except ValueError as e:\n                cams[j] = None\n                cams[(\'why\', j)] = str(e)\n    m = _build(cams, data, None)\n    if m[\'k\'] and any(p[\'rough\'] for p in m[\'parts\']):\n        m2 = _build(cams, data, m[\'k\'])\n        if m2[\'k\']:\n            m = m2\n    m[\'cam\'] = cams[0]\n    mn = m[\'parts\'][0]\n    m.update(outline=mn[\'outline\'], raw=mn[\'raw\'], eaves=mn[\'eaves\'], ridge=mn[\'ridge\'])\n    m[\'rough_depth\'] = any(p[\'rough\'] for p in m[\'parts\'])\n    return m\n\n\ndef sizes_text(m, data):\n    """The measured sizes in real mm, for the panel."""\n    k = m.get(\'k\')\n    lines = []\n    if not k:\n        return lines\n    s = m[\'sizes\']\n    for key, label in ((\'wall1\', "Wall 1-2"), (\'wall2\', "Wall 2-3"), (\'eaves\', "Eaves"), (\'ridge\', "Roof top"),\n                       (\'door_h\', "First door"), (\'win_w\', "First window wide"), (\'win_h\', "First window high")):\n        if s.get(key):\n            lines.append("%s: %.0f mm" % (label, s[key] * k))\n    for i, pm in enumerate(m.get(\'parts\') or []):\n        ol = pm.get(\'outline\')\n        if not ol:\n            continue\n        fr = plan_frame(ol)\n        pl = [to_plan(fr, p) for p in ol]\n        L, D = (max(p[0] for p in pl) - min(p[0] for p in pl)) * k, (max(p[1] for p in pl) - min(p[1] for p in pl)) * k\n        if i == 0:\n            lines.append("Main: %.0f x %.0f mm" % (L, D))\n        else:\n            lines.append("%s: %.0f x %.0f mm%s" % (part_label(i, data[\'parts\'][i]), L, D,\n                                                   (", eaves %.0f" % (pm[\'eaves\'] * k)) if pm[\'eaves\'] else ""))\n    nw = sum(1 for o in m[\'openings\'] if o[\'kind\'] != \'door\')\n    nd = len(m[\'openings\']) - nw\n    if nw or nd:\n        lines.append("%d window%s, %d door%s" % (nw, "" if nw == 1 else "s", nd, "" if nd == 1 else "s"))\n    return lines\n\n\ndef _roof_info(part, corners, eaves, ridge):\n    roof = part.get(\'roof\', \'gable_len\')\n    out = {\'roof\': roof, \'roof_low\': part.get(\'roof_low\', \'front\'), \'eaves\': round(eaves, 1),\n           \'ridge\': round(ridge, 1) if ridge else 0.0}\n    a, b = corners[0], corners[1]\n    L = math.hypot(b[0] - a[0], b[1] - a[1])\n    D = 0.0\n    if len(corners) >= 3:\n        ux, uy = (b[0] - a[0]) / (L or 1.0), (b[1] - a[1]) / (L or 1.0)\n        D = max(abs(-uy * (c[0] - a[0]) + ux * (c[1] - a[1])) for c in corners)\n    if roof not in (\'flat\', \'none\') and out[\'ridge\'] > out[\'eaves\']:\n        rise = out[\'ridge\'] - out[\'eaves\']\n        run = {\'gable_len\': D / 2.0, \'gable_across\': L / 2.0, \'hip\': min(L, D) / 2.0, \'mono\': D}.get(roof, D / 2.0)\n        out[\'pitch\'] = round(math.degrees(math.atan2(rise, max(run, 1.0))), 2)\n    return out\n\n\ndef result(m, data):\n    """What goes back to IngeTrazo (real mm): each part\'s outline (in the main building\'s plan: its front\n    along x from 0), heights and roof, and the windows and doors. Raises ValueError saying what\'s missing."""\n    if m[\'cam\'] is None:\n        raise ValueError(m[\'problems\'][0] if m[\'problems\'] else "Line up the edges first (step 1).")\n    main = data[\'parts\'][0]\n    if m[\'outline\'] is None:\n        if main.get(\'shape\', \'rect\') == \'rect\' and len(m[\'raw\']) == 2:\n            raise ValueError("Only two corners clicked - click the far end of a side wall too, or type the "\n                             "depth (step 2) and the known size (step 6).")\n        raise ValueError("Click the corners of the main building on the ground first (step 2).")\n    if not m[\'eaves\']:\n        raise ValueError("Click the top of a corner (the eaves) of the main building first (step 3).")\n    k = m[\'k\']\n    if not k:\n        name = dict(KNOWN).get(data.get(\'known_what\'), "the known size")\n        raise ValueError("The known size (step 6) can\'t be measured yet: \'%s\' - click it, or pick another "\n                         "size you know." % name)\n    fr = plan_frame(m[\'outline\'])\n    parts = []\n    for i, (part, pm) in enumerate(zip(data[\'parts\'], m[\'parts\'])):\n        if i and not pm[\'outline\']:\n            raise ValueError("%s isn\'t finished - click its corners, or take it off (Remove this part)."\n                             % part_label(i, part))\n        if i and not pm[\'eaves\']:\n            raise ValueError("%s: click the top of one of its corners (step 3)." % part_label(i, part))\n        corners = [[round(x * k, 1), round(y * k, 1)] for x, y in (to_plan(fr, p) for p in pm[\'outline\'])]\n        xs, ys = [c[0] for c in corners], [c[1] for c in corners]\n        pr = {\'name\': part_label(i, part), \'corners\': corners, \'shape\': part.get(\'shape\', \'rect\'),\n              \'storeys\': int(part.get(\'storeys\') or 1), \'against\': bool(part.get(\'against\')) and i > 0,\n              \'length\': round(max(xs) - min(xs), 1), \'width\': round(max(ys) - min(ys), 1)}\n        pr.update(_roof_info(part, corners, pm[\'eaves\'] * k, pm[\'ridge\'] * k if pm[\'ridge\'] else 0.0))\n        parts.append(pr)\n    out = dict(parts[0])\n    out.update({\'version\': 2, \'made\': time.strftime("%Y-%m-%d %H:%M:%S"), \'parts\': parts,\n                \'known_what\': data.get(\'known_what\'), \'known_mm\': float(data.get(\'known_mm\') or 0.0),\n                \'lens35\': round(m[\'cam\'][\'lens35\'], 1), \'openings\': []})\n    out[\'gables\'] = [{\'part\': g[\'part\'], \'wall\': g[\'wall\'], \'s0\': round(g[\'s0\'] * k, 1), \'s1\': round(g[\'s1\'] * k, 1),\n                      \'z0\': round(g[\'z0\'] * k, 1), \'peak\': round(g[\'peak\'] * k, 1)} for g in m.get(\'gables\') or []]\n    for o in m[\'openings\']:\n        out[\'openings\'].append({\'kind\': o[\'kind\'], \'top\': o[\'top\'], \'part\': o[\'part\'], \'wall\': o[\'wall\'],\n                                \'s0\': round(o[\'s0\'] * k, 1), \'s1\': round(o[\'s1\'] * k, 1),\n                                \'z0\': round(o[\'z0\'] * k, 1), \'z1\': round(o[\'z1\'] * k, 1),\n                                \'shape\': [[round(p[0] * k, 1), round(p[1] * k, 1)] for p in o[\'shape\']]\n                                if o.get(\'shape\') else None})\n    return out\n\n\ndef _part_lines(ol, top, ridge, roof, low, pi):\n    segs = []\n    n = len(ol)\n    for i in range(n):\n        a, b = ol[i], ol[(i + 1) % n]\n        segs.append((a, b, \'ground\', pi))\n        if top:\n            segs.append(((a[0], a[1], top), (b[0], b[1], top), \'wall\', pi))\n            segs.append((a, (a[0], a[1], top), \'wall\', pi))\n    if top and ridge and n == 4:\n        fr = plan_frame(ol)\n        pl = [to_plan(fr, p) for p in ol]\n        x0, x1 = min(p[0] for p in pl), max(p[0] for p in pl)\n        y0, y1 = min(p[1] for p in pl), max(p[1] for p in pl)\n        P = lambda x, y, z: from_plan(fr, x, y, z)\n        ym, xm = (y0 + y1) / 2.0, (x0 + x1) / 2.0\n        rs = []\n        if roof == \'gable_len\':\n            r0, r1 = P(x0, ym, ridge), P(x1, ym, ridge)\n            rs = [(r0, r1), (P(x0, y0, top), r0), (P(x0, y1, top), r0), (P(x1, y0, top), r1), (P(x1, y1, top), r1)]\n        elif roof == \'gable_across\':\n            r0, r1 = P(xm, y0, ridge), P(xm, y1, ridge)\n            rs = [(r0, r1), (P(x0, y0, top), r0), (P(x1, y0, top), r0), (P(x0, y1, top), r1), (P(x1, y1, top), r1)]\n        elif roof == \'hip\':\n            h = min(x1 - x0, y1 - y0) / 2.0\n            if x1 - x0 >= y1 - y0:\n                r0, r1 = P(x0 + h, ym, ridge), P(x1 - h, ym, ridge)\n                rs = [(r0, r1), (P(x0, y0, top), r0), (P(x0, y1, top), r0), (P(x1, y0, top), r1),\n                      (P(x1, y1, top), r1)]\n            else:\n                r0, r1 = P(xm, y0 + h, ridge), P(xm, y1 - h, ridge)\n                rs = [(r0, r1), (P(x0, y0, top), r0), (P(x1, y0, top), r0), (P(x0, y1, top), r1),\n                      (P(x1, y1, top), r1)]\n        elif roof == \'mono\':\n            hy = y1 if low == \'front\' else y0\n            ly = y0 if hy == y1 else y1\n            rs = [(P(x0, hy, ridge), P(x1, hy, ridge)), (P(x0, ly, top), P(x0, hy, ridge)),\n                  (P(x1, ly, top), P(x1, hy, ridge)), (P(x0, hy, top), P(x0, hy, ridge)),\n                  (P(x1, hy, top), P(x1, hy, ridge))]\n        segs += [(a, b, \'roof\', pi) for a, b in rs]\n    return segs\n\n\ndef building_lines(m, data):\n    """The building as lines in the world, to draw over the photo: [(a, b, kind, part)]."""\n    segs = []\n    if not m.get(\'cam\'):\n        return segs\n    for pi, (part, pm) in enumerate(zip(data.get(\'parts\') or [], m.get(\'parts\') or [])):\n        ol = pm.get(\'outline\')\n        if not ol:\n            raw = pm.get(\'raw\') or []\n            segs += [(a, b, \'wall\', pi) for a, b in zip(raw, raw[1:])]\n            continue\n        segs += _part_lines(ol, pm.get(\'eaves\'), pm.get(\'ridge\'), part.get(\'roof\', \'gable_len\'),\n                            part.get(\'roof_low\', \'front\'), pi)\n    for o in m.get(\'openings\') or []:\n        kind = \'door\' if o[\'kind\'] == \'door\' else \'window\'\n        segs += [(a, b, kind, o[\'part\']) for a, b in opening_lines(m, o)]\n    for g in m.get(\'gables\') or []:\n        ol = m[\'parts\'][g[\'part\']][\'outline\']\n        a, b = ol[g[\'wall\']], ol[(g[\'wall\'] + 1) % len(ol)]\n        u = v_norm(v_sub(b, a))\n        mid = (g[\'s0\'] + g[\'s1\']) / 2.0\n        c = [v_add(a, v_add(v_mul(u, s_), (0.0, 0.0, z_))) for s_, z_ in\n             ((g[\'s0\'], g[\'z0\']), (mid, g[\'peak\']), (g[\'s1\'], g[\'z0\']))]\n        segs += [(c[0], c[1], \'roof\', g[\'part\']), (c[1], c[2], \'roof\', g[\'part\']), (c[0], c[2], \'roof\', g[\'part\'])]\n    return segs\n\n\ndef opening_outline(m, o):\n    """An opening\'s outline in the world (its traced shape, else its box)."""\n    ol = m[\'parts\'][o[\'part\']][\'outline\']\n    a, b = ol[o[\'wall\']], ol[(o[\'wall\'] + 1) % len(ol)]\n    u = v_norm(v_sub(b, a))\n    pts = o.get(\'shape\') or ((o[\'s0\'], o[\'z0\']), (o[\'s1\'], o[\'z0\']), (o[\'s1\'], o[\'z1\']), (o[\'s0\'], o[\'z1\']))\n    return [v_add(a, v_add(v_mul(u, s), (0.0, 0.0, z))) for s, z in pts]\n\n\ndef opening_lines(m, o):\n    c = opening_outline(m, o)\n    return [(c[i], c[(i + 1) % len(c)]) for i in range(len(c))]\n\n\n# ---------------------------------------------------------------- inside the 3D program\nHOW_HELP = {\n    \'box\': ["BOX: click two opposite corners of each one - bottom left, then top right (level with the top).",\n            "T changes the top (square, segmental, round)."],\n    \'trace\': ["TRACE HALF: click the bottom corner on the side you can see best, up that side and round the top",\n              "to the PEAK in the middle.  Enter (or right-click) finishes it - it\'s mirrored to make the other half."],\n    \'outline\': ["ALL ROUND: click every point of its outline, all the way round (where the sides meet the top,",\n                "the peak...).  Enter (or right-click) finishes it."],\n    \'copy\': ["COPY: click inside the window to copy (it goes white), then click the bottom left corner of each",\n             "window the same shape.  Click inside another one to copy that instead."],\n}\nKEYS_HELP = ("W window   D door   B box   H half   A all round   C copy   Backspace takes the last off   "\n             "Esc when done   (Shift + wheel-drag slides the photo)")\n\nSTATE = {\'data\': None, \'model\': None, \'mode\': None, \'hover\': None, \'drag\': None, \'pending\': None,\n         \'job\': {}}\n\nMODE_HELP = {\n    \'lines\': ["1  LINE UP THE EDGES",\n              "Drag the ends of the two RED lines onto two edges of one wall (the eaves, the ground, a row of",\n              "windows - long straight edges). Drag the two GREEN lines onto edges of the wall round the corner.",\n              "The blue grid on the ground should then look flat.   Enter or right-click when done."],\n    \'corners\': ["2  CORNERS ON THE GROUND",\n                "Click where each corner meets the ground. Rectangle: corner 1, corner 2 along the front, then",\n                "the far end of the side wall. Against the main building (a bay, a porch): just its two front",\n                "corners.  Backspace takes the last one off.  Enter when done."],\n    \'eaves\': ["3  HEIGHT",\n              "Click the top of a corner of the walls (where the roof starts - the eaves). Backspace takes it off.",\n              "Enter when done."],\n    \'ridge\': ["4  ROOF", "Click the very top of the roof (the ridge, or the high edge of a lean-to).  Enter when done."],\n    \'link\': ["TIE THIS PHOTO IN", "Click the main building\'s two corners you picked in the panel, where the walls meet",\n             "the ground (the first, then the second).  Backspace takes the last off.  Enter when done."],\n    \'wall4\': ["THE WALL\'S 4 CORNERS", "Click its corners: bottom left, bottom right, top right, top left (as you look at",\n              "it - the top ones just under the gutter).  Backspace takes the last off.  Enter when done."],\n    \'gable\': ["ROOF GABLES", "For each pointed gable on the front of the roof: click its left corner where it meets the",\n              "eaves, its right corner, then its peak.  Backspace takes the last click off.  Enter when done."],\n    \'openings\': ["5  WINDOWS AND DOORS"],\n}\n\n\ndef add_photo_data(d, path, kind):\n    """Puts another photo in the set (a corner one, or straight on to a wall). Returns its number, or None."""\n    if not IN_BLENDER or not path or not os.path.isfile(path):\n        return None\n    for k, ph in enumerate(d[\'photos\']):\n        if os.path.normcase(ph.get(\'path\') or \'\') == os.path.normcase(path):\n            return k                                      # already there\n    try:\n        img = bpy.data.images.load(path, check_existing=True)\n        W, H = int(img.size[0]), int(img.size[1])\n    except Exception as e:\n        print("Photo to Building: couldn\'t open %s: %s" % (path, e))\n        return None\n    if W <= 0 or H <= 0:\n        return None\n    ph = {\'path\': path, \'img\': str(img.name), \'kind\': kind, \'W\': W, \'H\': H}\n    if kind == \'corner\':\n        ph.update(lines=start_lines(), link=[], link_corners=[0, 1])\n    else:\n        ph.update(part=0, wall=0, quad=[])\n    d[\'photos\'].append(ph)\n    return len(d[\'photos\']) - 1\n\n\ndef cur_photo(d):\n    return min(max(0, int(d.get(\'photo\') or 0)), len(d.get(\'photos\') or [0]) - 1)\n\n\ndef cur_lines(d):\n    """The lines being lined up on the photo shown."""\n    k = cur_photo(d)\n    if k == 0:\n        return d[\'lines\']\n    ph = d[\'photos\'][k]\n    if not ph.get(\'lines\'):\n        ph[\'lines\'] = start_lines()\n    return ph[\'lines\']\n\n\ndef lines_done(d, k):\n    ph = photo_info(d, k)\n    return bool(ph.get(\'lines\')) and ph[\'lines\'] != start_lines()\n\n\ndef view_project(view, P):\n    """Where a world point is on a photo (a lined-up one, or on the wall of a straight-on one)."""\n    if view is None:\n        return None\n    if view.get(\'kind\') == \'wall\':\n        dlt = v_sub(P, view[\'a\'])\n        if abs(v_dot(dlt, view[\'n\'])) > 0.02 * max(view[\'L\'], 1e-6):\n            return None                                   # not on that wall\n        return hmap(view[\'Hi\'], v_dot(dlt, view[\'u\']), P[2])\n    return project(view[\'cam\'], P) if view.get(\'cam\') else None\n\n\ndef data_default(W, H):\n    return {\'W\': W, \'H\': H, \'lines\': start_lines(), \'parts\': [new_part("Main building")], \'cur\': 0,\n            \'openings\': [], \'known_what\': \'door_h\', \'known_mm\': 2000.0, \'step\': 1, \'steps_v\': 2}\n\n\ndef cur_part(d=None):\n    d = d or STATE[\'data\']\n    return d[\'parts\'][d[\'cur\']]\n\n\ndef props_from_part(st, part):\n    """Shows a part\'s settings in the panel (without measuring again on each one)."""\n    st.busy = True\n    try:\n        for key in PART_KEYS:\n            if key in part and part[key] is not None:\n                try:\n                    setattr(st, key, part[key])\n                except Exception:\n                    pass\n        st.part_name = part.get(\'name\') or ""\n    finally:\n        st.busy = False\n\n\ndef recompute(save=True):\n    d = STATE[\'data\']\n    if d is None:\n        return\n    migrate(d)\n    if IN_BLENDER:\n        st = bpy.context.scene.ptb\n        part = cur_part(d)\n        for key in PART_KEYS:\n            part[key] = getattr(st, key)\n        if d[\'cur\'] == 0:\n            part[\'against\'] = False\n        if st.part_name.strip():\n            part[\'name\'] = st.part_name.strip()\n        d[\'known_what\'], d[\'known_mm\'] = st.known_what, st.known_mm\n    STATE[\'model\'] = compute(d)\n    if IN_BLENDER:\n        show_photo(d)\n        if save:\n            bpy.context.scene[\'ptb_json\'] = json.dumps(d)\n        for win in bpy.context.window_manager.windows:\n            for area in win.screen.areas:\n                if area.type in (\'VIEW_3D\', \'PROPERTIES\'):\n                    area.tag_redraw()\n\n\ndef save_soon():\n    """Saves the file a moment later (the clicks are kept in it), once the step has finished."""\n    if not IN_BLENDER:\n        return\n\n    def later():\n        save_now()\n        return None\n    bpy.app.timers.register(later, first_interval=0.3)\n\n\ndef save_now():\n    """Saves the file (the clicks, the view, the panel\'s window) and the clicks as a file that can be read\n    without the 3D program (\'clicks.json\' in the job\'s folder)."""\n    try:\n        if bpy.data.filepath:\n            bpy.ops.wm.save_mainfile()\n    except Exception as e:\n        print("Photo to Building: not saved:", e)\n    try:\n        out = STATE[\'job\'].get(\'out_json\') or bpy.context.scene.ptb.out_json\n        if out and STATE[\'data\']:\n            m = STATE[\'model\'] or {}\n            info = {\'saved\': time.strftime("%Y-%m-%d %H:%M:%S"), \'clicks\': STATE[\'data\'],\n                    \'problems\': m.get(\'problems\') or [], \'sizes\': sizes_text(m, STATE[\'data\']) if m else []}\n            with open(os.path.join(os.path.dirname(out), "clicks.json"), "w", encoding="utf-8") as f:\n                json.dump(info, f, indent=1)\n    except Exception as e:\n        print("Photo to Building: clicks not written:", e)\n\n\ndef keep_saving():\n    """Every minute, while nothing\'s being clicked: so the view\'s kept where it was left."""\n    if STATE.get(\'mode\') is None and STATE.get(\'data\') is not None:\n        save_now()\n    return 60.0\n\n\ndef show_photo(d):\n    """Shows the photo being worked on, through the camera worked out for it."""\n    if not IN_BLENDER:\n        return\n    k = cur_photo(d)\n    ph = photo_info(d, k)\n    m = STATE[\'model\'] or {}\n    views = m.get(\'views\') or []\n    view = views[k] if k < len(views) else None\n    sc = bpy.context.scene\n    ob = bpy.data.objects.get("Photo camera")\n    if ob is None:\n        return\n    try:\n        if ph.get(\'W\') and (sc.render.resolution_x != ph[\'W\'] or sc.render.resolution_y != ph[\'H\']):\n            sc.render.resolution_x, sc.render.resolution_y = int(ph[\'W\']), int(ph[\'H\'])\n        name = ph.get(\'img\') or (d[\'photos\'][0].get(\'img\') if k == 0 else None)\n        img = bpy.data.images.get(name) if name else None\n        if img is None and ph.get(\'path\') and os.path.isfile(ph[\'path\']):\n            img = bpy.data.images.load(ph[\'path\'], check_existing=True)\n            d[\'photos\'][k][\'img\'] = img.name\n        if img is not None:\n            bgs = ob.data.background_images\n            bg = bgs[0] if len(bgs) else bgs.new()\n            if bg.image != img:\n                bg.image = img\n    except Exception as e:\n        print("Photo to Building: showing the photo:", e)\n    if view is not None and view.get(\'cam\'):\n        set_camera(view[\'cam\'])\n    elif k == 0 and m.get(\'cam\'):\n        set_camera(m[\'cam\'])\n\n\ndef set_camera(cam):\n    if not IN_BLENDER or cam is None:\n        return\n    from mathutils import Matrix\n    ob = bpy.data.objects.get("Photo camera")\n    if ob is None:\n        return\n    M = cam[\'M\']\n    R = Matrix(((M[0][0], M[1][0], M[2][0]), (M[0][1], M[1][1], M[2][1]), (M[0][2], M[1][2], M[2][2])))\n    mw = R.to_4x4()\n    mw.translation = cam[\'C\']\n    ob.matrix_world = mw\n    ob.data.sensor_fit = \'AUTO\'\n    ob.data.sensor_width = 36.0\n    ob.data.lens = cam[\'lens35\']\n    ob.data.shift_x = ob.data.shift_y = 0.0\n\n\nif IN_BLENDER:\n    import gpu, blf\n    from gpu_extras.batch import batch_for_shader\n    from bpy_extras.view3d_utils import location_3d_to_region_2d\n    from bpy.props import FloatProperty, IntProperty, EnumProperty, StringProperty, BoolProperty\n\n    def frame_rect(region, rv3d):\n        """The photo\'s frame on screen: (x0, y0, x1, y1), or None if not looking through the camera."""\n        sc = bpy.context.scene\n        ob = bpy.data.objects.get("Photo camera")\n        if ob is None or rv3d is None or rv3d.view_perspective != \'CAMERA\':\n            return None\n        pts = []\n        for c in ob.data.view_frame(scene=sc):\n            p = location_3d_to_region_2d(region, rv3d, ob.matrix_world @ c)\n            if p is None:\n                return None\n            pts.append(p)\n        xs, ys = [p.x for p in pts], [p.y for p in pts]\n        return min(xs), min(ys), max(xs), max(ys)\n\n    def n2r(fr, nu, nv):\n        return (fr[0] + nu * (fr[2] - fr[0]), fr[1] + nv * (fr[3] - fr[1]))\n\n    def r2n(fr, x, y):\n        return ((x - fr[0]) / max(fr[2] - fr[0], 1e-6), (y - fr[1]) / max(fr[3] - fr[1], 1e-6))\n\n    _SH = {}\n\n    def _shaders():\n        if not _SH:\n            try:\n                _SH[\'poly\'] = gpu.shader.from_builtin(\'POLYLINE_UNIFORM_COLOR\')\n            except Exception:\n                _SH[\'poly\'] = None\n            for nm in (\'UNIFORM_COLOR\', \'2D_UNIFORM_COLOR\'):\n                try:\n                    _SH[\'flat\'] = gpu.shader.from_builtin(nm)\n                    break\n                except Exception:\n                    continue\n        return _SH\n\n    def draw_lines(region, segs, col, width=2.0):\n        if not segs:\n            return\n        sh = _shaders()\n        coords = [c for s in segs for c in s]\n        if sh.get(\'poly\') is not None:\n            try:\n                b = batch_for_shader(sh[\'poly\'], \'LINES\', {"pos": [(x, y, 0.0) for x, y in coords]})\n                sh[\'poly\'].bind()\n                sh[\'poly\'].uniform_float("viewportSize", (region.width, region.height))\n                sh[\'poly\'].uniform_float("lineWidth", width)\n                sh[\'poly\'].uniform_float("color", col)\n                b.draw(sh[\'poly\'])\n                return\n            except Exception:\n                _SH[\'poly\'] = None\n        try:\n            gpu.state.line_width_set(width)\n        except Exception:\n            pass\n        b = batch_for_shader(sh[\'flat\'], \'LINES\', {"pos": coords})\n        sh[\'flat\'].bind()\n        sh[\'flat\'].uniform_float("color", col)\n        b.draw(sh[\'flat\'])\n\n    def draw_dots(pts, col, r=5.0):\n        if not pts:\n            return\n        sh = _shaders()[\'flat\']\n        tris = []\n        for x, y in pts:\n            a, b, c, d = (x - r, y - r), (x + r, y - r), (x + r, y + r), (x - r, y + r)\n            tris += [a, b, c, a, c, d]\n        bt = batch_for_shader(sh, \'TRIS\', {"pos": tris})\n        sh.bind()\n        sh.uniform_float("color", col)\n        bt.draw(sh)\n\n    def text(x, y, s, size=14, col=(1, 1, 1, 1)):\n        try:\n            blf.size(0, size)\n        except TypeError:\n            blf.size(0, size, 72)\n        blf.color(0, *col)\n        try:\n            blf.enable(0, blf.SHADOW)\n            blf.shadow(0, 3, 0.0, 0.0, 0.0, 0.9)\n        except Exception:\n            pass\n        blf.position(0, x, y, 0)\n        blf.draw(0, s)\n\n    COLS = {\'r\': (1.0, 0.2, 0.15, 1.0), \'g\': (0.2, 1.0, 0.3, 1.0), \'ground\': (1.0, 0.85, 0.1, 1.0),\n            \'wall\': (1.0, 0.85, 0.1, 1.0), \'roof\': (1.0, 0.45, 0.9, 1.0), \'window\': (0.3, 0.8, 1.0, 1.0),\n            \'door\': (1.0, 0.55, 0.15, 1.0), \'grid\': (0.35, 0.6, 1.0, 0.45)}\n\n    def slide(rv3d, region, dx, dy):\n        """Slides the photo with the mouse (the photo view\'s own way of panning)."""\n        try:\n            zf = ((math.sqrt(2.0) + rv3d.view_camera_zoom / 50.0) ** 2) / 4.0 * 2.0\n            ox, oy = rv3d.view_camera_offset\n            rv3d.view_camera_offset = (ox - dx / (region.width * zf), oy - dy / (region.height * zf))\n        except Exception as e:\n            print("Photo to Building: sliding:", e)\n\n    def preview_opening(d, st):\n        """The window or door being clicked, where the mouse is now (drawn white)."""\n        hv = STATE[\'hover\']\n        if st.how == \'box\' and STATE[\'pending\']:\n            return {\'kind\': st.kind, \'top\': st.top, \'how\': \'box\', \'clicks\': [STATE[\'pending\'][\'click\'], hv]}\n        if st.how in (\'trace\', \'outline\') and STATE.get(\'trace\'):\n            return {\'kind\': st.kind, \'how\': st.how, \'clicks\': STATE[\'trace\'] + [hv]}\n        if st.how == \'copy\' and STATE.get(\'copy_src\') is not None:\n            return {\'how\': \'copy\', \'src\': STATE[\'copy_src\'], \'clicks\': [hv]}\n        return None\n\n    def opening_at(m, d, nu, nv, kph=0):\n        """The window or door clicked inside (its index in the list), if any."""\n        views = m.get(\'views\') or []\n        view = views[kph] if kph < len(views) else None\n        if view is None:\n            return None\n        ph = photo_info(d, kph)\n        u, v = nu * ph[\'W\'], nv * ph[\'H\']\n        for o in m.get(\'openings\') or []:\n            pts = [view_project(view, P) for P in opening_outline(m, o)]\n            if any(p_ is None for p_ in pts):\n                continue\n            inside = False\n            for i in range(len(pts)):\n                (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % len(pts)]\n                if (y1 > v) != (y2 > v) and u < x1 + (v - y1) * (x2 - x1) / (y2 - y1):\n                    inside = not inside\n            if inside:\n                return o.get(\'idx\')\n        return None\n\n    def draw_preview():\n        """The plan, looking down, in the space under the panel in its own window."""\n        try:\n            _draw_preview()\n        except Exception as e:\n            print("Photo to Building: preview:", e)\n\n    def _draw_preview():\n        ctx = bpy.context\n        area, region = ctx.area, ctx.region\n        if area is None or region is None or len(ctx.screen.areas) != 1:\n            return                                         # only in the panel\'s own window\n        d, m = STATE[\'data\'], STATE[\'model\']\n        if not d or not m or region.height < 420:\n            return\n        pms = m.get(\'parts\') or []\n        main = pms[0].get(\'outline\') if pms else None\n        x0, y0, x1, y1 = 12, 12, region.width - 12, min(300, int(region.height * 0.4))\n        gpu.state.blend_set(\'ALPHA\')\n        sh = _shaders()[\'flat\']\n        bt = batch_for_shader(sh, \'TRIS\', {"pos": [(x0, y0), (x1, y0), (x1, y1), (x0, y0), (x1, y1), (x0, y1)]})\n        sh.bind()\n        sh.uniform_float("color", (0.12, 0.12, 0.14, 0.9))\n        bt.draw(sh)\n        text(x0 + 8, y1 - 20, "Looking down - the front at the bottom", 13, (0.85, 0.85, 0.85, 1))\n        if not main:\n            text(x0 + 8, y1 - 44, "The plan shows here once the corners are clicked", 12, (0.7, 0.7, 0.7, 1))\n            gpu.state.blend_set(\'NONE\')\n            return\n        fr = plan_frame(main)\n        plans = [[to_plan(fr, p_) for p_ in pm_[\'outline\']] if pm_.get(\'outline\') else None for pm_ in pms]\n        pts = [q for pl in plans if pl for q in pl]\n        mnx, mxx = min(q[0] for q in pts), max(q[0] for q in pts)\n        mny, mxy = min(q[1] for q in pts), max(q[1] for q in pts)\n        sc = min((x1 - x0 - 40) / max(mxx - mnx, 1e-6), (y1 - y0 - 60) / max(mxy - mny, 1e-6))\n        cx = (x0 + x1) / 2.0 - (mnx + mxx) / 2.0 * sc\n        cy = (y0 + y1 - 24) / 2.0 - (mny + mxy) / 2.0 * sc\n\n        def P(q):\n            return (cx + q[0] * sc, cy + q[1] * sc)\n        for i, pl in enumerate(plans):\n            if not pl:\n                continue\n            here = i == d[\'cur\']\n            col = (1.0, 0.85, 0.1, 1.0) if here else (0.85, 0.85, 0.85, 0.8)\n            draw_lines(region, [(P(pl[k]), P(pl[(k + 1) % len(pl)])) for k in range(len(pl))], col, 2.5 if here else 1.5)\n            mx = sum(q[0] for q in pl) / len(pl)\n            my = sum(q[1] for q in pl) / len(pl)\n            c = P((mx, my))\n            text(c[0] - 24, c[1] - 5, part_label(i, d[\'parts\'][i]), 12, col)\n        if plans[0]:                                       # the main building\'s corners, to tie photos in by\n            for ci, q in enumerate(plans[0]):\n                c = P(q)\n                text(c[0] + 3, c[1] + 3, str(ci + 1), 13, (0.4, 1, 1, 1))\n        pc = plans[d[\'cur\']] if d[\'cur\'] < len(plans) else None\n        if pc:                                             # the walls of the part picked: W1, W2...\n            for wi in range(len(pc)):\n                a_, b_ = pc[wi], pc[(wi + 1) % len(pc)]\n                c = P(((a_[0] + b_[0]) / 2.0, (a_[1] + b_[1]) / 2.0))\n                text(c[0] - 8, c[1] - 14, "w%d" % (wi + 1), 11, (1.0, 0.85, 0.1, 0.9))\n        for o in m.get(\'openings\') or []:                  # windows blue, doors orange, on their walls\n            pl = plans[o[\'part\']] if o[\'part\'] < len(plans) else None\n            if not pl:\n                continue\n            a, b = pl[o[\'wall\']], pl[(o[\'wall\'] + 1) % len(pl)]\n            L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0\n            u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)\n            q0 = (a[0] + u[0] * o[\'s0\'], a[1] + u[1] * o[\'s0\'])\n            q1 = (a[0] + u[0] * o[\'s1\'], a[1] + u[1] * o[\'s1\'])\n            draw_lines(region, [(P(q0), P(q1))], COLS[\'door\'] if o[\'kind\'] == \'door\' else COLS[\'window\'], 4.0)\n        k = m.get(\'k\')\n        if k:\n            text(x0 + 8, y0 + 8, "%.1f x %.1f m (main building)" % (\n                (max(q[0] for q in plans[0]) - min(q[0] for q in plans[0])) * k / 1000.0,\n                (max(q[1] for q in plans[0]) - min(q[1] for q in plans[0])) * k / 1000.0), 12, (0.85, 0.85, 0.85, 1))\n        gpu.state.blend_set(\'NONE\')\n\n    def draw_overlay():\n        try:\n            _draw_overlay()\n        except Exception as e:\n            print("Photo to Building: drawing:", e)\n\n    def _draw_overlay():\n        ctx = bpy.context\n        region, rv3d = ctx.region, getattr(ctx.space_data, \'region_3d\', None)\n        d, m = STATE[\'data\'], STATE[\'model\']\n        if d is None or m is None:\n            return\n        fr = frame_rect(region, rv3d)\n        if fr is None:\n            text(20, region.height - 40, "Photo to Building: press Numpad 0 to look through the photo camera",\n                 15, (1, 0.9, 0.3, 1))\n            return\n        kph = cur_photo(d)\n        ph = photo_info(d, kph)\n        W, H = ph.get(\'W\') or d[\'W\'], ph.get(\'H\') or d[\'H\']\n        gpu.state.blend_set(\'ALPHA\')\n        views = m.get(\'views\') or []\n        view = views[kph] if kph < len(views) else None\n        cam = view.get(\'cam\') if view else None\n\n        def px2r(u, v):\n            return n2r(fr, u / W, v / H)\n\n        def w2r(P):\n            p = view_project(view, P)\n            return px2r(*p) if p else None\n\n        def mine(c):                                       # clicks made on this photo\n            return ck(c) == kph\n\n        def seg3(a, b):\n            pa, pb = w2r(a), w2r(b)\n            return (pa, pb) if pa and pb else None\n        mode = STATE[\'mode\']\n        # the ground grid: flat on the ground if the camera\'s right\n        if cam and mode in (\'lines\', \'corners\', None):\n            g = []\n            span = 12.0\n            step = 1.0\n            ol = m.get(\'outline\') or m.get(\'raw\')\n            ox, oy = (ol[0][0], ol[0][1]) if ol else (0.0, 0.0)\n            if not ol:\n                # centre the grid on the ground under the middle of the photo, if it\'s below the skyline\n                c = hit_ground(cam, W / 2.0, H * 0.25)\n                if c:\n                    ox, oy = c[0], c[1]\n            k = -span\n            while k <= span + 1e-9:\n                for a, b in (((ox + k, oy - span, 0.0), (ox + k, oy + span, 0.0)),\n                             ((ox - span, oy + k, 0.0), (ox + span, oy + k, 0.0))):\n                    s = seg3(a, b)\n                    if s:\n                        g.append(s)\n                k += step\n            draw_lines(region, g, COLS[\'grid\'], 1.0)\n        # the building so far\n        if view is not None:\n            by = {}\n            preview = None\n            if mode == \'openings\' and STATE[\'hover\'] and m.get(\'outline\'):\n                preview = preview_opening(d, ctx.scene.ptb)\n            for a, b, kind, pi in building_lines(m, d):\n                s = seg3(a, b)\n                if s:\n                    by.setdefault((kind, pi == d[\'cur\'] or kind in (\'window\', \'door\')), []).append(s)\n            for (kind, here), segs in by.items():\n                c = COLS.get(kind, COLS[\'wall\'])\n                if not here:                               # the other parts: fainter\n                    c = (c[0], c[1], c[2], 0.45)\n                draw_lines(region, segs, c, (2.0 if kind != \'ground\' else 2.5) if here else 1.5)\n            if preview:\n                dd = dict(d)\n                dd[\'openings\'] = list(d[\'openings\']) + [preview]\n                mm = compute(dd)\n                last = [o for o in mm[\'openings\'] if o.get(\'idx\') == len(d[\'openings\'])]\n                if last:\n                    segs = [s for s in (seg3(a, b) for a, b in opening_lines(mm, last[0])) if s]\n                    draw_lines(region, segs, (1, 1, 1, 0.9), 1.5)\n            src = STATE.get(\'copy_src\')\n            if mode == \'openings\' and src is not None:\n                got = [o for o in m[\'openings\'] if o.get(\'idx\') == src]\n                if got:\n                    segs = [s for s in (seg3(a, b) for a, b in opening_lines(m, got[0])) if s]\n                    draw_lines(region, segs, (1, 1, 1, 1), 3.0)\n            # numbers on the corners\n            part = cur_part(d)\n            for i, c in enumerate(part.get(\'corners\') or []):\n                if not mine(c):\n                    continue\n                x, y = px2r(c[0] * W, c[1] * H)\n                draw_dots([(x, y)], (1.0, 0.85, 0.1, 1.0), 5)\n                text(x + 8, y + 6, str(i + 1), 16, (1, 0.9, 0.2, 1))\n            if len(d[\'parts\']) > 1:\n                for pi, pm in enumerate(m.get(\'parts\') or []):\n                    ol = pm.get(\'outline\')\n                    if ol:\n                        c = w2r(v_mul(v_add(ol[0], ol[1]), 0.5))\n                        if c:\n                            text(c[0] - 20, c[1] - 22, part_label(pi, d[\'parts\'][pi]), 13,\n                                 (1, 0.9, 0.2, 1) if pi == d[\'cur\'] else (1, 0.9, 0.2, 0.6))\n            for key, lab in ((\'eaves\', "eaves"), (\'ridge\', "roof top")):\n                if part.get(key) and mine(part[key]):\n                    x, y = px2r(part[key][0] * W, part[key][1] * H)\n                    draw_dots([(x, y)], (1.0, 0.45, 0.9, 1.0), 5)\n                    text(x + 8, y + 6, lab, 14, (1, 0.6, 0.95, 1))\n        if True:\n            if mode == \'openings\' and STATE[\'pending\']:\n                c = STATE[\'pending\'][\'click\']\n                draw_dots([px2r(c[0] * W, c[1] * H)], (1, 1, 1, 1), 4)\n            if mode == \'gable\' and d.get(\'gables\') and len(d[\'gables\'][-1].get(\'clicks\') or []) < 3:\n                draw_dots([px2r(c[0] * W, c[1] * H) for c in d[\'gables\'][-1][\'clicks\'] if mine(c)],\n                          (1, 0.6, 0.95, 1), 5)\n            if mode == \'openings\' and STATE.get(\'trace\'):\n                draw_dots([px2r(c[0] * W, c[1] * H) for c in STATE[\'trace\']], (1, 1, 1, 1), 4)\n            # tying a photo in: the main building\'s corners clicked on it, and a wall\'s 4 corners\n            if kph > 0:\n                for l_ in ph.get(\'link\') or []:\n                    if l_.get(\'c\'):\n                        x, y = px2r(l_[\'c\'][0] * W, l_[\'c\'][1] * H)\n                        draw_dots([(x, y)], (0.3, 1, 1, 1), 6)\n                        text(x + 8, y + 6, "corner %d" % (int(l_[\'corner\']) + 1), 16, (0.4, 1, 1, 1))\n                for i, q in enumerate(ph.get(\'quad\') or []):\n                    x, y = px2r(q[0] * W, q[1] * H)\n                    draw_dots([(x, y)], (0.3, 1, 1, 1), 6)\n                    text(x + 8, y + 6, ("bottom left", "bottom right", "top right", "top left")[i % 4], 15,\n                         (0.4, 1, 1, 1))\n                quad = ph.get(\'quad\') or []\n                if len(quad) >= 2:\n                    pts = [px2r(q[0] * W, q[1] * H) for q in quad[:4]]\n                    draw_lines(region, [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))],\n                               (0.3, 1, 1, 0.8), 2.0)\n        if view is not None:\n            count = {\'window\': 0, \'door\': 0}\n            for o in m.get(\'openings\') or []:\n                kind = \'door\' if o[\'kind\'] == \'door\' else \'window\'\n                count[kind] += 1                           # windows and doors each numbered from 1\n                ol = m[\'parts\'][o[\'part\']][\'outline\']\n                a, b = ol[o[\'wall\']], ol[(o[\'wall\'] + 1) % len(ol)]\n                u = v_norm(v_sub(b, a))\n                p = w2r(v_add(a, v_add(v_mul(u, (o[\'s0\'] + o[\'s1\']) / 2.0), (0.0, 0.0, o[\'z1\']))))\n                if p:\n                    text(p[0] - 4, p[1] + 6, ("D" if kind == \'door\' else "W") + str(count[kind]), 13, COLS[kind])\n        # the four lines, long and faint, and the handles\n        lines_here = cur_lines(d) if ph.get(\'kind\') == \'corner\' else None\n        for key in (LINE_KEYS if lines_here else ()):\n            col = COLS[key[0]]\n            (u0, v0), (u1, v1) = lines_here[key][:2]\n            a, b = n2r(fr, u0, v0), n2r(fr, u1, v1)\n            if mode == \'lines\' or (kph == 0 and not cam) or (kph > 0 and not lines_done(d, kph)):\n                dx, dy = b[0] - a[0], b[1] - a[1]\n                L = math.hypot(dx, dy) or 1.0\n                ext = 4000.0 / L\n                draw_lines(region, [((a[0] - dx * ext, a[1] - dy * ext), (b[0] + dx * ext, b[1] + dy * ext))],\n                           (col[0], col[1], col[2], 0.35), 1.0)\n                draw_lines(region, [(a, b)], col, 3.0)\n                draw_dots([a, b], col, 6)\n                drag = STATE.get(\'drag\')\n                if drag and drag[0] == key:\n                    draw_dots([a if drag[1] == 0 else b], (1, 1, 1, 1), 3)\n        # what to do now, and any problem\n        y = region.height - 30\n        if len(d[\'photos\']) > 1:\n            text(24, y, "PHOTO %d of %d%s" % (kph + 1, len(d[\'photos\']),\n                                               "  (straight on to a wall)" if ph.get(\'kind\') == \'wall\' else ""),\n                 16, (0.4, 1, 1, 1))\n            y -= 26\n        lines = list(MODE_HELP.get(mode) or [])\n        if mode in (\'corners\', \'eaves\', \'ridge\') and len(d[\'parts\']) > 1:\n            lines[0] += "   -   " + part_label(d[\'cur\'], cur_part(d)).upper()\n        if mode == \'openings\':\n            st = ctx.scene.ptb\n            what = "DOORS" if st.kind == \'door\' else "WINDOWS"\n            if st.how == \'box\':\n                what += " - " + {t[0]: t[1] for t in TOPS}[st.top].lower()\n            lines = [lines[0] + "   -   " + what] + HOW_HELP[st.how] + [KEYS_HELP]\n            if STATE.get(\'note\'):\n                lines.append(STATE[\'note\'])\n        step_col = {\'lines\': (1, 0.45, 0.4, 1), \'corners\': (1, 0.9, 0.3, 1), \'eaves\': (1, 0.6, 0.95, 1),\n                    \'ridge\': (1, 0.6, 0.95, 1), \'openings\': (0.45, 0.85, 1, 1)}.get(mode, (1, 0.9, 0.3, 1))\n        for i, s in enumerate(lines):\n            text(24, y, s, 20 if i == 0 else 16, step_col if i == 0 else (1, 1, 1, 1))\n            y -= 30 if i == 0 else 24\n        pp = (m.get(\'photo_problems\') or {}).get(kph)\n        if pp:\n            text(20, y - 6, "This photo: " + pp, 14, (1, 0.45, 0.4, 1))\n            y -= 22\n        if m[\'problems\'] and mode:\n            text(20, y - 6, m[\'problems\'][0], 14, (1, 0.45, 0.4, 1))\n        gpu.state.blend_set(\'NONE\')\n\n    class PTB_OT_click(bpy.types.Operator):\n        """Click on the photo (or drag the lines) for this step"""\n        bl_idname = "eddy_ptb.click"\n        bl_label = "Click on the photo"\n        what: StringProperty(default=\'lines\')\n\n        def invoke(self, context, event):\n            area = context.area\n            if area is None or area.type != \'VIEW_3D\':\n                area = next((a for a in context.screen.areas if a.type == \'VIEW_3D\'), None)\n            if area is None or STATE[\'data\'] is None:\n                self.report({\'WARNING\'}, "No photo set up")\n                return {\'CANCELLED\'}\n            self.area = area\n            self.region = next(r for r in area.regions if r.type == \'WINDOW\')\n            self.rv3d = area.spaces.active.region_3d\n            if self.rv3d.view_perspective != \'CAMERA\':\n                self.rv3d.view_perspective = \'CAMERA\'\n            try:\n                self.rv3d.lock_rotation = True             # the view can\'t be turned off the photo\n            except Exception:\n                pass\n            if self.what in (\'corners\', \'eaves\', \'ridge\', \'openings\', \'link\') and STATE[\'model\'].get(\'cam\') is None:\n                self.report({\'WARNING\'}, "Line up the edges on photo 1 first (step 2)")\n                return {\'CANCELLED\'}\n            d0 = STATE[\'data\']\n            kph = cur_photo(d0)\n            ph0 = photo_info(d0, kph)\n            view0 = (STATE[\'model\'].get(\'views\') or [None] * (kph + 1))[kph] if kph < len(\n                STATE[\'model\'].get(\'views\') or []) else None\n            if self.what in (\'corners\', \'eaves\', \'ridge\') and ph0.get(\'kind\') == \'wall\':\n                self.report({\'WARNING\'}, "This photo\'s straight on to one wall - do corners, heights and roofs on a "\n                                         "corner photo (windows, doors and gables are fine here)")\n                return {\'CANCELLED\'}\n            if self.what == \'corners\' and kph > 0 and d0[\'cur\'] == 0:\n                self.report({\'WARNING\'}, "The main building\'s corners go on photo 1 - the other photos are tied to them")\n                return {\'CANCELLED\'}\n            if self.what in (\'corners\', \'eaves\', \'ridge\', \'openings\', \'gable\') and kph > 0 and view0 is None:\n                self.report({\'WARNING\'}, "Set this photo up first (step 2): %s" % (\n                    (STATE[\'model\'].get(\'photo_problems\') or {}).get(kph) or "line it up and tie it in"))\n                return {\'CANCELLED\'}\n            if self.what == \'link\' and not STATE[\'model\'].get(\'outline\'):\n                self.report({\'WARNING\'}, "The main building\'s corners on photo 1 come first (step 3)")\n                return {\'CANCELLED\'}\n            if self.what in (\'lines\', \'link\') and ph0.get(\'kind\') == \'wall\':\n                return {\'CANCELLED\'}\n            d_ = STATE[\'data\']\n            pm = (STATE[\'model\'].get(\'parts\') or [{}] * (d_[\'cur\'] + 1))[d_[\'cur\']] if STATE[\'model\'] else {}\n            if self.what in (\'eaves\', \'ridge\') and not (pm.get(\'outline\') or len(pm.get(\'raw\') or []) >= 2):\n                self.report({\'WARNING\'}, "Click the corners on the ground first (step 2)")\n                return {\'CANCELLED\'}\n            if self.what == \'ridge\' and not pm.get(\'outline\'):\n                self.report({\'WARNING\'}, "The outline isn\'t finished - click corner 3, or type the depth")\n                return {\'CANCELLED\'}\n            if self.what in (\'openings\', \'gable\') and not STATE[\'model\'].get(\'outline\'):\n                self.report({\'WARNING\'}, "The main building\'s outline isn\'t finished - click corner 3, or type "\n                                         "the depth")\n                return {\'CANCELLED\'}\n            if self.what == \'corners\' and d_[\'cur\'] > 0 and cur_part(d_).get(\'against\') and \\\n                    not STATE[\'model\'].get(\'outline\'):\n                self.report({\'WARNING\'}, "Finish the main building\'s corners first - this part runs back to it")\n                return {\'CANCELLED\'}\n            STATE[\'mode\'] = self.what\n            STATE[\'token\'] = STATE.get(\'token\', 0) + 1\n            self.token = STATE[\'token\']\n            STATE[\'pending\'] = None\n            STATE[\'drag\'] = None\n            context.window_manager.modal_handler_add(self)\n            recompute(False)\n            return {\'RUNNING_MODAL\'}\n\n        def _right(self):\n            """Where the photo\'s part of the view ends: the sidebar (N) can sit over its right-hand side."""\n            right = self.region.width\n            try:\n                for r in self.area.regions:\n                    if r.type == \'UI\' and r.width > 1 and r.x > self.region.x:\n                        right = min(right, r.x - self.region.x)\n            except Exception:\n                pass\n            return right\n\n        def _here(self, event):\n            x, y = event.mouse_x - self.region.x, event.mouse_y - self.region.y\n            inside = 0 <= x < self._right() and 0 <= y < self.region.height\n            return x, y, inside\n\n        def _on_buttons(self, x, y):\n            """Is the mouse on the view\'s own buttons (zoom, hand, camera) down its right-hand side?"""\n            right = self._right()\n            return right - 80 <= x <= right and self.region.height - 340 <= y <= self.region.height\n\n        def finish(self):\n            STATE[\'press\'] = None\n            d = STATE[\'data\']\n            m = STATE[\'model\'] or {}\n            pms = m.get(\'parts\') or []\n            pm = pms[d[\'cur\']] if d[\'cur\'] < len(pms) else {}\n            done = {\'gable\': False, \'link\': False, \'wall4\': False,\n                    \'lines\': m.get(\'cam\') is not None and cur_photo(d) == 0, \'corners\': pm.get(\'outline\') is not None,\n                    \'eaves\': bool(pm.get(\'eaves\')), \'ridge\': bool(pm.get(\'ridge\')), \'openings\': True}\n            if done.get(self.what):\n                d[\'step\'] = {\'lines\': 2, \'corners\': 3, \'eaves\': 4, \'ridge\': 5, \'openings\': 6}[self.what]\n                step_on(d)                                 # the next part, or the next step\n            STATE[\'mode\'] = None\n            STATE[\'pending\'] = None\n            STATE[\'trace\'] = []\n            STATE[\'note\'] = ""\n            STATE[\'drag\'] = None\n            STATE[\'hover\'] = None\n            recompute()\n            save_soon()\n            return {\'FINISHED\'}\n\n        def modal(self, context, event):\n            d = STATE[\'data\']\n            et, ev = event.type, event.value\n            if STATE[\'mode\'] != self.what or STATE.get(\'token\') != self.token:   # another step was started\n                return {\'CANCELLED\'}\n            x, y, inside = self._here(event)\n            fr = frame_rect(self.region, self.rv3d)\n            st_ = context.scene.ptb\n            if self.what == \'openings\' and ev == \'PRESS\' and et in {\'RET\', \'NUMPAD_ENTER\', \'RIGHTMOUSE\'} and \\\n                    len(STATE.get(\'trace\') or []) >= (3 if st_.how == \'outline\' else 2):\n                d[\'openings\'].append({\'kind\': st_.kind, \'how\': st_.how, \'clicks\': STATE[\'trace\']})\n                STATE[\'trace\'] = []                        # that traced one\'s done: on to the next\n                recompute()\n                return {\'RUNNING_MODAL\'}\n            if et in {\'ESC\', \'RET\', \'NUMPAD_ENTER\'} and ev == \'PRESS\':\n                return self.finish()\n            if et in {\'MIDDLEMOUSE\', \'WHEELUPMOUSE\', \'WHEELDOWNMOUSE\', \'TRACKPADPAN\', \'TRACKPADZOOM\', \'HOME\',\n                      \'LEFT_ARROW\', \'RIGHT_ARROW\', \'UP_ARROW\', \'DOWN_ARROW\'} or et.startswith(\'NUMPAD_\'):\n                return {\'PASS_THROUGH\'}                    # sliding and zooming the photo still work\n            undo = (et in {\'BACK_SPACE\', \'DEL\'} or (et == \'Z\' and event.ctrl)) and ev == \'PRESS\'\n            if undo:                                       # wherever the mouse is\n                if self.what == \'corners\' and cur_part(d)[\'corners\']:\n                    cur_part(d)[\'corners\'].pop()\n                elif self.what == \'openings\':\n                    if STATE.get(\'trace\'):\n                        STATE[\'trace\'].pop()\n                    elif STATE[\'pending\']:\n                        STATE[\'pending\'] = None\n                    elif d[\'openings\']:\n                        d[\'openings\'].pop()\n                        if STATE.get(\'copy_src\') is not None and STATE[\'copy_src\'] >= len(d[\'openings\']):\n                            STATE[\'copy_src\'] = None\n                elif self.what in (\'eaves\', \'ridge\'):\n                    cur_part(d)[self.what] = None\n                elif self.what in (\'link\', \'wall4\'):\n                    lst = d[\'photos\'][cur_photo(d)].get(\'link\' if self.what == \'link\' else \'quad\') or []\n                    if lst:\n                        lst.pop()\n                elif self.what == \'gable\' and d.get(\'gables\'):\n                    cl = d[\'gables\'][-1].get(\'clicks\') or []\n                    if cl:\n                        cl.pop()\n                    if not cl:\n                        d[\'gables\'].pop()\n                recompute()\n                return {\'RUNNING_MODAL\'}\n            if et == \'RIGHTMOUSE\' and ev == \'PRESS\' and inside:\n                return self.finish()\n            if not inside or fr is None:\n                return {\'PASS_THROUGH\'}\n            if self._on_buttons(x, y):\n                return {\'PASS_THROUGH\'}                    # the zoom / hand buttons at the side of the view\n            nu, nv = r2n(fr, x, y)\n            kph = cur_photo(d)\n            if et == \'MOUSEMOVE\' and STATE.get(\'press\'):     # the mouse button\'s held down: slide the photo?\n                px_, py_ = STATE[\'press\'][\'last\']\n                if not STATE[\'press\'][\'moved\'] and math.hypot(x - STATE[\'press\'][\'x\'], y - STATE[\'press\'][\'y\']) > 6:\n                    STATE[\'press\'][\'moved\'] = True\n                if STATE[\'press\'][\'moved\']:\n                    slide(self.rv3d, self.region, x - px_, y - py_)\n                    self.area.tag_redraw()\n                STATE[\'press\'][\'last\'] = (x, y)\n                return {\'RUNNING_MODAL\'}\n            if et == \'MOUSEMOVE\':\n                if self.what == \'lines\' and STATE[\'drag\']:\n                    key, end = STATE[\'drag\']\n                    cur_lines(d)[key][end] = [nu, nv]\n                    recompute(False)\n                elif self.what == \'openings\':\n                    STATE[\'hover\'] = [nu, nv, kph]\n                    self.area.tag_redraw()\n                return {\'RUNNING_MODAL\'}\n            if self.what == \'openings\' and ev == \'PRESS\' and et in {\'W\', \'D\', \'T\', \'B\', \'H\', \'A\', \'C\'}:\n                st = context.scene.ptb\n                if et == \'W\':\n                    st.kind = \'window\'\n                elif et == \'D\':\n                    st.kind = \'door\'\n                elif et in (\'B\', \'H\', \'A\', \'C\'):\n                    st.how = {\'B\': \'box\', \'H\': \'trace\', \'A\': \'outline\', \'C\': \'copy\'}[et]\n                    STATE[\'pending\'] = None\n                    STATE[\'trace\'] = []\n                else:\n                    ks = [t[0] for t in TOPS]\n                    st.top = ks[(ks.index(st.top) + 1) % len(ks)]\n                self.area.tag_redraw()\n                return {\'RUNNING_MODAL\'}\n            if et == \'LEFTMOUSE\':\n                if self.what == \'lines\' and ev == \'PRESS\':\n                    best = None\n                    for key in LINE_KEYS:\n                        for end in (0, 1):\n                            hx, hy = n2r(fr, *cur_lines(d)[key][end][:2])\n                            dist = math.hypot(hx - x, hy - y)\n                            if dist < 20 and (best is None or dist < best[0]):\n                                best = (dist, key, end)\n                    STATE[\'drag\'] = (best[1], best[2]) if best else None\n                    return {\'RUNNING_MODAL\'}\n                if self.what == \'lines\':\n                    if ev == \'RELEASE\':\n                        STATE[\'drag\'] = None\n                        recompute()\n                    return {\'RUNNING_MODAL\'}\n                if ev != \'PRESS\':                          # a click counts as soon as it\'s pressed\n                    return {\'RUNNING_MODAL\'}\n                if self.what == \'link\':                    # tying this photo in: two of the main building\'s corners\n                    ph = d[\'photos\'][kph]\n                    lk = ph.setdefault(\'link\', [])\n                    pick = ph.get(\'link_corners\') or [0, 1]\n                    if len(lk) >= 2:\n                        lk.clear()\n                    lk.append({\'c\': [nu, nv], \'corner\': int(pick[len(lk)])})\n                elif self.what == \'wall4\':                 # a straight-on photo: the wall\'s 4 corners\n                    q = d[\'photos\'][kph].setdefault(\'quad\', [])\n                    if len(q) >= 4:\n                        q.clear()\n                    q.append([nu, nv])\n                elif self.what == \'corners\':\n                    part = cur_part(d)\n                    most = 1 if part.get(\'copy_of\') is not None else \\\n                        (2 if (d[\'cur\'] > 0 and part.get(\'against\')) else 3)\n                    if (context.scene.ptb.shape == \'rect\' or most < 3) and len(part[\'corners\']) >= most:\n                        part[\'corners\'] = []\n                    part[\'corners\'].append([nu, nv, kph])\n                elif self.what in (\'eaves\', \'ridge\'):\n                    cur_part(d)[self.what] = [nu, nv, kph]\n                elif self.what == \'gable\':\n                    gl = d.setdefault(\'gables\', [])\n                    if not gl or len(gl[-1].get(\'clicks\') or []) >= 3:\n                        gl.append({\'clicks\': []})\n                    gl[-1][\'clicks\'].append([nu, nv, kph])\n                elif self.what == \'openings\':\n                    st = context.scene.ptb\n                    STATE[\'note\'] = ""\n                    if st.how in (\'trace\', \'outline\'):\n                        STATE.setdefault(\'trace\', []).append([nu, nv, kph])\n                    elif st.how == \'copy\':\n                        hit = opening_at(STATE[\'model\'], d, nu, nv, kph)\n                        if hit is not None:\n                            STATE[\'copy_src\'] = hit        # the one to copy\n                        elif STATE.get(\'copy_src\') is None:\n                            STATE[\'note\'] = "Click inside the window you want to copy first."\n                        else:\n                            d[\'openings\'].append({\'how\': \'copy\', \'src\': STATE[\'copy_src\'], \'clicks\': [[nu, nv, kph]]})\n                    elif STATE[\'pending\'] is None:\n                        STATE[\'pending\'] = {\'click\': [nu, nv, kph], \'kind\': st.kind}\n                    else:\n                        d[\'openings\'].append({\'kind\': STATE[\'pending\'][\'kind\'], \'top\': st.top, \'how\': \'box\',\n                                              \'clicks\': [STATE[\'pending\'][\'click\'], [nu, nv, kph]]})\n                        STATE[\'pending\'] = None\n                recompute()\n                return {\'RUNNING_MODAL\'}\n            if et in {\'LEFT_CTRL\', \'RIGHT_CTRL\', \'LEFT_SHIFT\', \'RIGHT_SHIFT\', \'LEFT_ALT\', \'RIGHT_ALT\'}:\n                return {\'PASS_THROUGH\'}\n            return {\'RUNNING_MODAL\'}\n\n    class PTB_OT_clear(bpy.types.Operator):\n        """Takes these clicks off, to do them again"""\n        bl_idname = "eddy_ptb.clear"\n        bl_label = "Clear"\n        what: StringProperty(default=\'corners\')\n\n        def execute(self, context):\n            d = STATE[\'data\']\n            if d is None:\n                return {\'CANCELLED\'}\n            if self.what == \'lines\':\n                if cur_photo(d) == 0:\n                    d[\'lines\'] = start_lines()\n                else:\n                    d[\'photos\'][cur_photo(d)][\'lines\'] = start_lines()\n            elif self.what == \'gable_last\':\n                if d.get(\'gables\'):\n                    d[\'gables\'].pop()\n            elif self.what == \'openings_last\':\n                if d[\'openings\']:\n                    d[\'openings\'].pop()\n            elif self.what == \'openings\':\n                d[\'openings\'] = []\n            elif self.what == \'corners\':\n                cur_part(d)[\'corners\'] = []\n            else:\n                cur_part(d)[self.what] = None\n            recompute()\n            return {\'FINISHED\'}\n\n    PART_STEPS = (3, 4, 5)                                 # the steps done for each part in turn\n\n    def step_on(d, back=False):\n        """Next (or back): through each part in turn on the corners, height and roof steps, then the next\n        step - starting at the main building."""\n        n = int(d.get(\'step\') or 1)\n        if n in PART_STEPS:\n            k = d[\'cur\'] + (-1 if back else 1)\n            if 0 <= k < len(d[\'parts\']):\n                d[\'cur\'] = k\n                props_from_part(bpy.context.scene.ptb, cur_part(d))\n                return\n        n = min(max(1, n + (-1 if back else 1)), 7)\n        d[\'step\'] = n\n        d[\'cur\'] = (len(d[\'parts\']) - 1) if (back and n in PART_STEPS) else 0\n        props_from_part(bpy.context.scene.ptb, cur_part(d))\n\n    def fresh_name(d, kind):\n        """\'Bay 3\', \'Wing 2\'... - the first number not used yet."""\n        used = set(p_.get(\'name\') for p_ in d[\'parts\'])\n        n = 1\n        while "%s %d" % (kind, n) in used:\n            n += 1\n        return "%s %d" % (kind, n)\n\n    def remove_part(d, i):\n        if i <= 0 or i >= len(d[\'parts\']):\n            return\n        d[\'parts\'].pop(i)\n        for p_ in d[\'parts\']:                              # copies of it become parts of their own\n            c = p_.get(\'copy_of\')\n            if c is None:\n                continue\n            if c == i:\n                p_[\'copy_of\'] = None\n                p_[\'corners\'] = []\n            elif c > i:\n                p_[\'copy_of\'] = c - 1\n        d[\'cur\'] = min(d[\'cur\'], len(d[\'parts\']) - 1)\n\n    class PTB_OT_part(bpy.types.Operator):\n        """Picks, adds, copies or takes off a part of the building (the main building, a wing, a bay...)"""\n        bl_idname = "eddy_ptb.part"\n        bl_label = "Part"\n        action: StringProperty(default=\'select\')\n        index: IntProperty(default=-1)\n\n        def execute(self, context):\n            d = STATE[\'data\']\n            if d is None:\n                return {\'CANCELLED\'}\n            migrate(d)\n            recompute(False)                               # keeps the panel\'s settings in the part we\'re leaving\n            i = d[\'cur\'] if self.index < 0 else self.index\n            if self.action == \'select\':\n                d[\'cur\'] = min(max(0, i), len(d[\'parts\']) - 1)\n            elif self.action in (\'prev\', \'next\'):\n                d[\'cur\'] = (d[\'cur\'] + (1 if self.action == \'next\' else -1)) % len(d[\'parts\'])\n            elif self.action in (\'add\', \'add_against\'):\n                against = self.action == \'add_against\'\n                d[\'parts\'].append(new_part(fresh_name(d, "Bay" if against else "Wing"), against))\n                if int(d.get(\'step\') or 1) in PART_STEPS:\n                    d[\'cur\'] = len(d[\'parts\']) - 1\n            elif self.action in (\'less\', \'less_against\'):  # one fewer wing / bay: the last one goes\n                against = self.action == \'less_against\'\n                ks = [k for k, p_ in enumerate(d[\'parts\']) if k and bool(p_.get(\'against\')) == against]\n                if ks:\n                    remove_part(d, ks[-1])\n            elif self.action == \'clone\' and i > 0:\n                src = d[\'parts\'][i]\n                against = bool(src.get(\'against\'))\n                c = new_part(fresh_name(d, "Bay" if against else "Wing"), against)\n                for key in PART_KEYS:\n                    c[key] = src.get(key, c.get(key))\n                c[\'copy_of\'] = i if src.get(\'copy_of\') is None else src[\'copy_of\']\n                d[\'parts\'].append(c)\n                d[\'cur\'] = len(d[\'parts\']) - 1\n                d[\'step\'] = 3                              # click where the copy goes\n            elif self.action == \'remove\':\n                remove_part(d, i)\n            props_from_part(context.scene.ptb, cur_part(d))\n            recompute()\n            return {\'FINISHED\'}\n\n    def main_view():\n        """The window, area and region showing the photo (the panel can be in a window of its own)."""\n        best = None\n        for win in bpy.context.window_manager.windows:\n            for area in win.screen.areas:\n                if area.type != \'VIEW_3D\':\n                    continue\n                reg = next((r for r in area.regions if r.type == \'WINDOW\'), None)\n                if reg is None:\n                    continue\n                cam = area.spaces.active.region_3d.view_perspective == \'CAMERA\'\n                if best is None or (cam and not best[3]):\n                    best = (win, area, reg, cam)\n        return best\n\n    class PTB_OT_start(bpy.types.Operator):\n        """Starts clicking on the photo for this step"""\n        bl_idname = "eddy_ptb.start"\n        bl_label = "Click on the photo"\n        what: StringProperty(default=\'lines\')\n\n        def execute(self, context):\n            mv = main_view()\n            if mv is None:\n                self.report({\'WARNING\'}, "The photo\'s view wasn\'t found")\n                return {\'CANCELLED\'}\n            win, area, reg, _cam = mv\n            try:\n                with context.temp_override(window=win, area=area, region=reg):\n                    bpy.ops.eddy_ptb.click(\'INVOKE_DEFAULT\', what=self.what)\n            except AttributeError:                          # older Blender: no temp_override\n                bpy.ops.eddy_ptb.click(\'INVOKE_DEFAULT\', what=self.what)\n            return {\'FINISHED\'}\n\n    class PTB_OT_float(bpy.types.Operator):\n        """Puts this panel in a window of its own, to move wherever it\'s out of the way"""\n        bl_idname = "eddy_ptb.float"\n        bl_label = "Panel in its own window"\n\n        def execute(self, context):\n            if not open_float(force=True):\n                self.report({\'WARNING\'}, "Couldn\'t open its own window - the panel stays at the side (N)")\n                return {\'CANCELLED\'}\n            return {\'FINISHED\'}\n\n    class PTB_OT_send(bpy.types.Operator):\n        """Sends the building to IngeTrazo: the outline, heights, roof, windows and doors, in real mm"""\n        bl_idname = "eddy_ptb.send"\n        bl_label = "Send to IngeTrazo"\n\n        def execute(self, context):\n            recompute()\n            d, m = STATE[\'data\'], STATE[\'model\']\n            try:\n                res = result(m, d)\n            except ValueError as e:\n                context.scene.ptb.note = str(e)\n                self.report({\'WARNING\'}, str(e))\n                return {\'CANCELLED\'}\n            res[\'photo\'] = STATE[\'job\'].get(\'photo\', \'\')\n            res[\'clicks\'] = d\n            path = STATE[\'job\'].get(\'out_json\') or context.scene.ptb.out_json\n            if not path:\n                self.report({\'WARNING\'}, "Nowhere to send it (open it from IngeTrazo)")\n                return {\'CANCELLED\'}\n            try:\n                tmp = path + ".part"\n                with open(tmp, "w", encoding="utf-8") as f:\n                    json.dump(res, f, indent=1)\n                os.replace(tmp, path)\n            except Exception as e:\n                self.report({\'ERROR\'}, "Couldn\'t save it: %s" % e)\n                return {\'CANCELLED\'}\n            save_soon()\n            np_ = len(res[\'parts\'])\n            context.scene.ptb.note = ("Sent: %.0f x %.0f mm%s, %d window%s and door%s - go back to IngeTrazo."\n                                      % (res[\'length\'], res[\'width\'],\n                                         (" and %d more part%s" % (np_ - 1, "" if np_ == 2 else "s")) if np_ > 1 else "",\n                                         len(res[\'openings\']), "" if len(res[\'openings\']) == 1 else "s",\n                                         "" if len(res[\'openings\']) == 1 else "s"))\n            self.report({\'INFO\'}, context.scene.ptb.note)\n            return {\'FINISHED\'}\n\n    def _changed(self, context):\n        if not self.busy:\n            recompute()\n\n    class PTB_Settings(bpy.types.PropertyGroup):\n        shape: EnumProperty(name="Shape", items=[(\'rect\', "Rectangle", "4 walls - click 3 corners"),\n                                                 (\'own\', "My own corners", "Click every corner, going round")],\n                            default=\'rect\', update=_changed)\n        depth_mm: FloatProperty(name="Depth if you can\'t see a side (mm)", default=0.0, min=0.0, max=100000.0,\n                                update=_changed,\n                                description="Only if the far end of the side wall can\'t be seen: how deep the "\n                                "building is, in real mm (0 = click corner 3)")\n        storeys: IntProperty(name="Floors (storeys)", default=1, min=1, max=20, update=_changed,\n                             description="How many floors the building has")\n        roof: EnumProperty(name="Roof", items=ROOFS, default=\'gable_len\', update=_changed)\n        roof_low: EnumProperty(name="Low side", items=[(\'front\', "At the front", ""), (\'back\', "At the back", "")],\n                               default=\'front\', update=_changed)\n        kind: EnumProperty(name="Clicking", items=[(\'window\', "Windows", ""), (\'door\', "Doors", "")],\n                           default=\'window\')\n        top: EnumProperty(name="Top", items=TOPS, default=\'square\')\n        how: EnumProperty(name="How", items=[(\'box\', "Box", "Two opposite corners (B)"),\n                                             (\'trace\', "Half", "Half its shape, mirrored (H)"),\n                                             (\'outline\', "All round", "Click all the way round it (A)"),\n                                             (\'copy\', "Copy", "The same as one already done (C)")], default=\'box\')\n        more: BoolProperty(name="More...", default=False, description="The less-used buttons for this step")\n        clean: BoolProperty(default=False)\n        known_what: EnumProperty(name="Known size", items=[(k, l, "") for k, l in KNOWN], default=\'door_h\',\n                                 update=_changed)\n        known_mm: FloatProperty(name="It is (mm)", default=2000.0, min=1.0, max=200000.0, update=_changed)\n        against: BoolProperty(name="Against the main building", default=False, update=_changed,\n                              description="A bay, porch or lean-to on the main building: click its two front "\n                              "corners and it runs back to the main building\'s wall by itself")\n        map_len: FloatProperty(name="Front (from a map), mm", default=0.0, min=0.0, max=200000.0, update=_changed,\n                               description="Its front\'s length, measured from above on a map (0 = from the photo)")\n        part_name: StringProperty(name="Name", default="", update=_changed,\n                                  description="What this part\'s called (it\'s the name of its group in IngeTrazo)")\n        note: StringProperty(default="")\n        out_json: StringProperty(default="")\n        busy: BoolProperty(default=False)\n\n    STEPS = [(1, "The building\'s parts"), (2, "Line up the edges"), (3, "Corners on the ground"), (4, "Height"),\n             (5, "Roof"), (6, "Windows and doors"), (7, "Size you know - send")]\n\n    HOWTO = {\n        1: "What the building\'s made of: the main building, plus any wings (a separate block) and bays or "\n           "porches (built against the main building). Set how many - you can add more later.",\n        2: "Drag the dots of the RED lines onto two long, level edges of one wall (the gutter, the bottom of "\n           "the wall). Drag the GREEN lines onto edges of the wall round the corner. Shift + wheel-drag slides "\n           "the photo. When it\'s right, the blue grid looks like floor tiles lying on the ground: one set of "\n           "lines runs along the front wall, the other along the end wall, and upright things (corners, lamp "\n           "posts) stand straight up from it.",\n        3: "Either 3 corners, or 2 corners and the depth. Click where the front wall meets the ground: "\n           "corner 1 at one end, corner 2 at the other. Then EITHER corner 3 - the far end of the side wall, on "\n           "the ground - OR press Enter and type the depth under More (measured on a map, say).",\n        \'bay\': "Click the bay\'s two front corners, where it meets the ground. Its back runs to the main "\n               "building by itself.",\n        \'tie\': "Another corner photo: 1 - line up its edges like photo 1 (red along one wall, green the other). "\n               "2 - pick two of the main building\'s corners you can see on it (their numbers are on the plan "\n               "below) and click them, where the walls meet the ground. Then click on it in the other steps.",\n        \'wall\': "A photo straight on to one wall: pick which part and wall it is (wall numbers are on the plan "\n                "below), then click the wall\'s 4 corners - bottom left, bottom right, top right, top left, the top "\n                "ones just under the gutter. Then click its windows, doors and gables in steps 5 and 6.",\n        \'copy\': "A copy: click its left front corner, where it meets the ground. It\'s the same size and shape "\n                "as the one it\'s copied from.",\n        4: "Click the top of the wall at a corner, just under the gutter - where the roof starts, not the top "\n           "of a gable.",\n        5: "Pick the roof\'s shape, then click once on the very top of the roof (the ridge). Pointed gables on "\n           "the front of the roof: Click a gable - its left and right corners at the eaves, then its peak.",\n        \'same\': "A copy - its height and roof are the same as the one it\'s copied from. Click Next.",\n        6: "Pick Window or Door, and how: Box - bottom left, then top right. Half - bottom corner, up the side, "\n           "round to the peak, Enter. All round - every point, Enter. Copy - click inside one you\'ve done, then "\n           "the bottom left of each one the same.",\n        7: "Check the size you know is right, then click Send. The building goes back to IngeTrazo.",\n    }\n\n    def part_kind(i, part):\n        return "Main" if i == 0 else ("Bay" if part.get(\'against\') else "Wing")\n\n    def step_summary(n, d, m, pm, st):\n        """The one line a finished step shrinks to (None if it isn\'t done)."""\n        k = m.get(\'k\')\n        pms = m.get(\'parts\') or []\n        if n == 1:\n            return "%d part%s" % (len(d[\'parts\']), "" if len(d[\'parts\']) == 1 else "s")\n        if n == 2:\n            kph = cur_photo(d)\n            if kph > 0:\n                vs = m.get(\'views\') or []\n                return "set up" if (kph < len(vs) and vs[kph] is not None) else None\n            return ("%.0f mm lens" % m[\'cam\'][\'lens35\']) if (m.get(\'cam\') and d.get(\'lines\') != start_lines()) else None\n        if n == 3 and pms and all(p_.get(\'outline\') for p_ in pms):\n            return "all parts"\n        if n == 4 and pms and all(p_.get(\'eaves\') for p_ in pms):\n            return "all parts"\n        if n == 5 and pms and all(p_.get(\'ridge\') or d[\'parts\'][i].get(\'roof\') in (\'flat\', \'none\')\n                                  for i, p_ in enumerate(pms)):\n            return "all parts"\n        if n == 6 and m.get(\'openings\'):\n            nw = sum(1 for o in m[\'openings\'] if o[\'kind\'] != \'door\')\n            nd = len(m[\'openings\']) - nw\n            return "%d window%s, %d door%s" % (nw, "" if nw == 1 else "s", nd, "" if nd == 1 else "s")\n        if n == 7 and k:\n            return "ready to send"\n        return None\n\n    def part_done(n, part, pm):\n        if n == 3:\n            return pm.get(\'outline\') is not None\n        if n == 4:\n            return bool(pm.get(\'eaves\'))\n        if n == 5:\n            return bool(pm.get(\'ridge\')) or part.get(\'roof\') in (\'flat\', \'none\')\n        return False\n\n    def wrapped(box, txt, width=40):\n        """Text over several lines (the panel doesn\'t wrap it)."""\n        col = box.column(align=True)\n        col.scale_y = 0.8\n        line = ""\n        for word in txt.split():\n            if line and len(line) + 1 + len(word) > width:\n                col.label(text=line)\n                line = word\n            else:\n                line = (line + " " + word).strip()\n        if line:\n            col.label(text=line)\n\n    def draw_parts_list(b, d, m):\n        """Step 1: how many wings and bays, and each part (copy, take off)."""\n        pms = m.get(\'parts\') or []\n        nw = sum(1 for p_ in d[\'parts\'][1:] if not p_.get(\'against\'))\n        nb = sum(1 for p_ in d[\'parts\'][1:] if p_.get(\'against\'))\n        for label, n, less, more in (("Wings", nw, \'less\', \'add\'), ("Bays / porches", nb, \'less_against\', \'add_against\')):\n            r = b.row(align=True)\n            r.label(text="%s:  %d" % (label, n))\n            r.operator("eddy_ptb.part", text="", icon=\'REMOVE\').action = less\n            r.operator("eddy_ptb.part", text="", icon=\'ADD\').action = more\n        b.separator()\n        for i, part in enumerate(d[\'parts\']):\n            pm = pms[i] if i < len(pms) else {}\n            r = b.row(align=True)\n            ok = pm.get(\'outline\') is not None and bool(pm.get(\'eaves\'))\n            r.label(text="%s  (%s)%s" % (part_label(i, part), part_kind(i, part).lower(),\n                                         "  - copy" if part.get(\'copy_of\') is not None else ""),\n                    icon=\'CHECKMARK\' if ok else \'RADIOBUT_OFF\')\n            if i > 0:\n                op = r.operator("eddy_ptb.part", text="", icon=\'DUPLICATE\')\n                op.action, op.index = \'clone\', i\n                op = r.operator("eddy_ptb.part", text="", icon=\'X\')\n                op.action, op.index = \'remove\', i\n\n    def draw_panel(layout, context):\n        st = context.scene.ptb\n        m = STATE[\'model\'] or {}\n        d = STATE[\'data\'] or {}\n        col = layout.column()\n        if not d:\n            col.label(text="Open this from IngeTrazo\'s Photo to Building")\n            return\n        migrate(d)\n        pms = m.get(\'parts\') or []\n        pm = pms[d[\'cur\']] if d[\'cur\'] < len(pms) else {}\n        part = cur_part(d)\n        cur = int(d.get(\'step\') or 1)\n        # the steps, as numbered tabs\n        r = col.row(align=True)\n        r.scale_y = 1.4\n        for n, _title in STEPS:\n            op = r.operator("eddy_ptb.goto", text=str(n), depress=(n == cur),\n                            icon=\'CHECKMARK\' if (n > 1 and step_summary(n, d, m, pm, st)) else \'NONE\')\n            op.step = n\n        # the photos: switch, add\n        kph = cur_photo(d)\n        ph = photo_info(d, kph)\n        pb_ = col.row(align=True)\n        pb_.operator("eddy_ptb.photo", text="", icon=\'TRIA_LEFT\').action = \'prev\'\n        nm = os.path.basename(ph.get(\'path\') or \'\') or "photo"\n        pb_.label(text="Photo %d of %d: %s%s" % (kph + 1, len(d[\'photos\']), nm[:22],\n                                                 " (wall)" if ph.get(\'kind\') == \'wall\' else ""), icon=\'IMAGE_DATA\')\n        pb_.operator("eddy_ptb.photo", text="", icon=\'TRIA_RIGHT\').action = \'next\'\n        ar = col.row(align=True)\n        op = ar.operator("eddy_ptb.add_photo", text="Add a corner photo", icon=\'ADD\')\n        op.kind = \'corner\'\n        op = ar.operator("eddy_ptb.add_photo", text="Add a straight-on photo", icon=\'ADD\')\n        op.kind = \'wall\'\n        b = col.box()\n        b.label(text="Step %d of 7:  %s" % (cur, dict(STEPS)[cur]))\n        against = d[\'cur\'] > 0 and st.against\n        copy = part.get(\'copy_of\') is not None\n        if cur in PART_STEPS:                              # which part: worked through in turn\n            r = b.row(align=True)\n            r.scale_y = 1.2\n            r.label(text="Part %d of %d:  %s" % (d[\'cur\'] + 1, len(d[\'parts\']), part_label(d[\'cur\'], part)),\n                    icon=\'CHECKMARK\' if part_done(cur, part, pm) else \'RADIOBUT_OFF\')\n            if d[\'cur\'] > 0:\n                op = r.operator("eddy_ptb.part", text="", icon=\'DUPLICATE\')\n                op.action, op.index = \'clone\', d[\'cur\']\n                r.operator("eddy_ptb.part", text="", icon=\'X\').action = \'remove\'\n        if cur == 1:\n            wrapped(b, HOWTO[1])\n            draw_parts_list(b, d, m)\n        elif cur == 3 and copy:\n            wrapped(b, HOWTO[\'copy\'])\n        elif cur in (4, 5) and copy:\n            wrapped(b, HOWTO[\'same\'])\n        elif cur == 2 and kph > 0 and ph.get(\'kind\') == \'wall\':\n            wrapped(b, HOWTO[\'wall\'])\n        elif cur == 2 and kph > 0:\n            wrapped(b, HOWTO[\'tie\'])\n        else:\n            wrapped(b, HOWTO[\'bay\'] if (cur == 3 and against) else HOWTO[cur])\n        b.separator()\n        if cur == 3 and not against and not copy:\n            b.prop(st, "shape", text="")\n        elif cur == 4 and not copy:\n            b.prop(st, "storeys")\n        elif cur == 5 and not copy:\n            b.prop(st, "roof", text="")\n            if st.roof == \'mono\':\n                b.prop(st, "roof_low")\n        elif cur == 6:\n            r = b.row()\n            r.prop(st, "kind", expand=True)\n            r = b.row()\n            r.prop(st, "how", expand=True)\n            if st.how == \'box\':\n                b.prop(st, "top", text="")\n        elif cur == 7:\n            b.prop(st, "known_what", text="")\n            b.prop(st, "known_mm")\n            if not m.get(\'k\'):\n                b.label(text="Not clicked yet - click it, or pick another", icon=\'ERROR\')\n            for s_ in sizes_text(m, d) if m else []:\n                b.label(text=s_)\n        big = b.row()\n        big.scale_y = 2.0\n        what = {2: (\'lines\', "Line up the edges"), 3: (\'corners\', "Click the corners"),\n                4: (\'eaves\', "Click the top of a corner"), 5: (\'ridge\', "Click the top of the roof"),\n                6: (\'openings\', "Click windows and doors")}.get(cur)\n        if cur == 3 and copy:\n            what = (\'corners\', "Click where the copy goes")\n        if cur == 2 and kph > 0:                           # setting up another photo\n            pms_ = m.get(\'parts\') or []\n            if ph.get(\'kind\') == \'wall\':\n                pi_ = int(ph.get(\'part\') or 0)\n                r = b.row(align=True)\n                op = r.operator("eddy_ptb.pick", text="", icon=\'TRIA_LEFT\')\n                op.what, op.step = \'part\', -1\n                r.label(text="Part: " + part_label(pi_, d[\'parts\'][pi_]) if pi_ < len(d[\'parts\']) else "Part")\n                op = r.operator("eddy_ptb.pick", text="", icon=\'TRIA_RIGHT\')\n                op.what, op.step = \'part\', 1\n                r = b.row(align=True)\n                op = r.operator("eddy_ptb.pick", text="", icon=\'TRIA_LEFT\')\n                op.what, op.step = \'wall\', -1\n                r.label(text="Wall %d (numbered on the plan below)" % (int(ph.get(\'wall\') or 0) + 1))\n                op = r.operator("eddy_ptb.pick", text="", icon=\'TRIA_RIGHT\')\n                op.what, op.step = \'wall\', 1\n                big.operator("eddy_ptb.start", text="Click the wall\'s 4 corners", icon=\'MOUSE_LMB\').what = \'wall4\'\n            else:\n                r2 = b.row()\n                r2.scale_y = 1.4\n                r2.operator("eddy_ptb.start", text="1  Line up its edges", icon=\'DRIVER_DISTANCE\').what = \'lines\'\n                lc = ph.get(\'link_corners\') or [0, 1]\n                for i_, (wh, lab) in enumerate(((\'corner_a\', "First corner"), (\'corner_b\', "Second corner"))):\n                    r = b.row(align=True)\n                    op = r.operator("eddy_ptb.pick", text="", icon=\'TRIA_LEFT\')\n                    op.what, op.step = wh, -1\n                    r.label(text="%s: main building corner %d" % (lab, int(lc[i_]) + 1))\n                    op = r.operator("eddy_ptb.pick", text="", icon=\'TRIA_RIGHT\')\n                    op.what, op.step = wh, 1\n                big.operator("eddy_ptb.start", text="2  Click those two corners", icon=\'MOUSE_LMB\').what = \'link\'\n            pp_ = (m.get(\'photo_problems\') or {}).get(kph)\n            if pp_:\n                b.label(text="Still to do:", icon=\'INFO\')\n                wrapped(b, pp_)\n            else:\n                b.label(text="This photo\'s set up", icon=\'CHECKMARK\')\n        elif what and not (cur == 5 and st.roof in (\'flat\', \'none\')) and not (cur in (4, 5) and copy):\n            big.operator("eddy_ptb.start", text=what[1], icon=\'MOUSE_LMB\').what = what[0]\n        elif cur == 7:\n            big.operator("eddy_ptb.send", icon=\'EXPORT\')\n        if cur == 5:                                       # pointed gables on the front of the roof\n            g = b.box()\n            ng = len([x for x in (m.get(\'gables\') or [])])\n            g.label(text="Pointed gables on the roof: %d" % ng, icon=\'MOD_TRIANGULATE\')\n            r = g.row(align=True)\n            r.operator("eddy_ptb.start", text="Click a gable", icon=\'MOUSE_LMB\').what = \'gable\'\n            r.operator("eddy_ptb.clear", text="Take the last off").what = \'gable_last\'\n        if cur == 3 and pm.get(\'rough\'):\n            b.label(text="Depth is rough until step 7\'s size is clicked", icon=\'INFO\')\n        if cur == 7 and st.note:\n            wrapped(b, st.note)\n        for p_ in (m.get(\'problems\') or [])[:1]:\n            b.label(text="Problem:", icon=\'ERROR\')\n            wrapped(b, p_)\n        # the less-used buttons, tucked away\n        if cur in (2, 3, 6):\n            b.prop(st, "more", icon=\'TRIA_DOWN\' if st.more else \'TRIA_RIGHT\', emboss=False)\n            if st.more:\n                if cur == 3:\n                    if st.shape == \'rect\' and not against and not copy:\n                        b.label(text="Sizes from a map (0 = from the photo):")\n                        if d[\'cur\'] > 0:\n                            b.prop(st, "map_len", text="Front, mm")\n                        b.prop(st, "depth_mm", text="Depth, mm")\n                    b.operator("eddy_ptb.clear", text="Clear this part\'s corners").what = \'corners\'\n                    if d[\'cur\'] > 0:\n                        b.prop(st, "part_name")\n                        if not copy:\n                            b.prop(st, "against")\n                elif cur == 6:\n                    b.operator("eddy_ptb.clear", text="Take the last off").what = \'openings_last\'\n        if cur > 1:\n            b.operator("eddy_ptb.restart", text="Start this step again", icon=\'LOOP_BACK\').step = cur\n        # back and next - through each part in turn on steps 3 to 5\n        r = col.row()\n        r.scale_y = 1.4\n        if cur > 1:\n            r.operator("eddy_ptb.walk", text="Back", icon=\'BACK\').back = True\n        if cur < 7:\n            nxt = "Next"\n            if cur in PART_STEPS and d[\'cur\'] < len(d[\'parts\']) - 1:\n                nxt = "Next: " + part_label(d[\'cur\'] + 1, d[\'parts\'][d[\'cur\'] + 1])\n            r.operator("eddy_ptb.walk", text=nxt, icon=\'FORWARD\').back = False\n        col.separator()\n        col.operator("eddy_ptb.clean", text="Show the 3D program\'s menus" if st.clean else "Clean view (hide menus)",\n                     icon=\'FULLSCREEN_EXIT\' if st.clean else \'FULLSCREEN_ENTER\')\n\n    class PTB_OT_add_photo(bpy.types.Operator):\n        """Adds another photo of the building - from another corner, or straight on to one wall"""\n        bl_idname = "eddy_ptb.add_photo"\n        bl_label = "Add this photo"\n        filepath: StringProperty(subtype=\'FILE_PATH\')\n        filter_image: BoolProperty(default=True, options={\'HIDDEN\'})\n        filter_folder: BoolProperty(default=True, options={\'HIDDEN\'})\n        kind: StringProperty(default=\'corner\')\n\n        def invoke(self, context, event):\n            d = STATE[\'data\']\n            if d and d[\'photos\'][0].get(\'path\'):\n                self.filepath = os.path.dirname(d[\'photos\'][0][\'path\']) + os.sep\n            context.window_manager.fileselect_add(self)\n            return {\'RUNNING_MODAL\'}\n\n        def execute(self, context):\n            d = STATE[\'data\']\n            if d is None or not os.path.isfile(self.filepath):\n                return {\'CANCELLED\'}\n            recompute(False)\n            k = add_photo_data(d, self.filepath, self.kind)\n            if k is None:\n                self.report({\'WARNING\'}, "Couldn\'t open that photo")\n                return {\'CANCELLED\'}\n            d[\'photo\'] = k\n            d[\'step\'] = 2                                  # set it up\n            recompute()\n            return {\'FINISHED\'}\n\n    class PTB_OT_photo(bpy.types.Operator):\n        """Shows another photo (or takes this one off)"""\n        bl_idname = "eddy_ptb.photo"\n        bl_label = "Photo"\n        action: StringProperty(default=\'next\')\n\n        def execute(self, context):\n            d = STATE[\'data\']\n            if d is None:\n                return {\'CANCELLED\'}\n            recompute(False)\n            k, n = cur_photo(d), len(d[\'photos\'])\n            if self.action == \'next\':\n                d[\'photo\'] = (k + 1) % n\n            elif self.action == \'prev\':\n                d[\'photo\'] = (k - 1) % n\n            elif self.action == \'remove\' and k > 0:\n                d[\'photos\'].pop(k)\n                drop = lambda cl: [c for c in cl if ck(c) != k]\n                shift = lambda cl: [(c[:2] + [ck(c) - 1]) if ck(c) > k else c for c in cl]\n                for p_ in d[\'parts\']:                      # its clicks go with it\n                    p_[\'corners\'] = shift(drop(p_.get(\'corners\') or []))\n                    for key in (\'eaves\', \'ridge\'):\n                        c = p_.get(key)\n                        if c and ck(c) == k:\n                            p_[key] = None\n                        elif c and ck(c) > k:\n                            p_[key] = c[:2] + [ck(c) - 1]\n                d[\'openings\'] = [dict(o, clicks=shift(o[\'clicks\'])) for o in d[\'openings\']\n                                 if not any(ck(c) == k for c in o.get(\'clicks\') or [])]\n                d[\'gables\'] = [dict(g, clicks=shift(g[\'clicks\'])) for g in d.get(\'gables\') or []\n                               if not any(ck(c) == k for c in g.get(\'clicks\') or [])]\n                STATE[\'copy_src\'] = None\n                d[\'photo\'] = 0\n            recompute()\n            return {\'FINISHED\'}\n\n    class PTB_OT_pick(bpy.types.Operator):\n        """Picks which part and wall a straight-on photo shows, or which corners tie a photo in"""\n        bl_idname = "eddy_ptb.pick"\n        bl_label = "Pick"\n        what: StringProperty(default=\'wall\')\n        step: IntProperty(default=1)\n\n        def execute(self, context):\n            d = STATE[\'data\']\n            m = STATE[\'model\'] or {}\n            if d is None:\n                return {\'CANCELLED\'}\n            ph = d[\'photos\'][cur_photo(d)]\n            if self.what == \'part\':\n                ph[\'part\'] = (int(ph.get(\'part\') or 0) + self.step) % len(d[\'parts\'])\n                ph[\'wall\'] = 0\n                ph[\'quad\'] = []\n                d[\'cur\'] = ph[\'part\']                      # its walls are numbered on the plan\n                props_from_part(context.scene.ptb, cur_part(d))\n            elif self.what == \'wall\':\n                pms = m.get(\'parts\') or []\n                ol = pms[int(ph.get(\'part\') or 0)].get(\'outline\') if int(ph.get(\'part\') or 0) < len(pms) else None\n                n = len(ol) if ol else 4\n                ph[\'wall\'] = (int(ph.get(\'wall\') or 0) + self.step) % n\n                ph[\'quad\'] = []\n            elif self.what in (\'corner_a\', \'corner_b\'):\n                ol = m.get(\'outline\')\n                n = len(ol) if ol else 4\n                lc = ph.setdefault(\'link_corners\', [0, 1])\n                i = 0 if self.what == \'corner_a\' else 1\n                lc[i] = (int(lc[i]) + self.step) % n\n                ph[\'link\'] = []\n            recompute()\n            return {\'FINISHED\'}\n\n    class PTB_OT_goto(bpy.types.Operator):\n        """Opens this step (at the main building)"""\n        bl_idname = "eddy_ptb.goto"\n        bl_label = "Step"\n        step: IntProperty(default=1)\n\n        def execute(self, context):\n            d = STATE[\'data\']\n            if d is not None:\n                recompute(False)\n                d[\'step\'] = min(max(1, self.step), 7)\n                d[\'cur\'] = 0                                # each step starts at the main building\n                props_from_part(context.scene.ptb, cur_part(d))\n                context.scene.ptb.more = False\n                recompute()\n            return {\'FINISHED\'}\n\n    class PTB_OT_walk(bpy.types.Operator):\n        """The next part, or the next step (Back: the one before)"""\n        bl_idname = "eddy_ptb.walk"\n        bl_label = "Next"\n        back: BoolProperty(default=False)\n\n        def execute(self, context):\n            d = STATE[\'data\']\n            if d is not None:\n                recompute(False)\n                step_on(d, self.back)\n                context.scene.ptb.more = False\n                recompute()\n            return {\'FINISHED\'}\n\n    class PTB_OT_restart(bpy.types.Operator):\n        """Takes off everything clicked in this step (for every part), to start it again"""\n        bl_idname = "eddy_ptb.restart"\n        bl_label = "Start this step again?"\n        step: IntProperty(default=1)\n\n        def invoke(self, context, event):\n            return context.window_manager.invoke_confirm(self, event)\n\n        def execute(self, context):\n            d = STATE[\'data\']\n            if d is None:\n                return {\'CANCELLED\'}\n            if self.step == 2:\n                k_ = cur_photo(d)\n                if k_ == 0:\n                    d[\'lines\'] = start_lines()\n                else:\n                    d[\'photos\'][k_].update(lines=start_lines(), link=[], quad=[])\n            elif self.step in (3, 4, 5):\n                key = {3: \'corners\', 4: \'eaves\', 5: \'ridge\'}[self.step]\n                for p_ in d[\'parts\']:\n                    p_[key] = [] if key == \'corners\' else None\n                if self.step == 5:\n                    d[\'gables\'] = []\n            elif self.step == 6:\n                d[\'openings\'] = []\n                STATE[\'copy_src\'] = None\n            d[\'cur\'] = 0\n            props_from_part(context.scene.ptb, cur_part(d))\n            recompute()\n            return {\'FINISHED\'}\n\n    class PTB_OT_clean(bpy.types.Operator):\n        """Hides the 3D program\'s menus, toolbars and other panels - just the photo (click again to bring\n        them back)"""\n        bl_idname = "eddy_ptb.clean"\n        bl_label = "Clean view"\n\n        def execute(self, context):\n            st = context.scene.ptb\n            mv = main_view()\n            if mv is None:\n                return {\'CANCELLED\'}\n            win, area, reg, _c = mv\n            sp = area.spaces.active\n            try:\n                if not st.clean:\n                    own = open_float()                     # the panel must be somewhere once the sides go\n                    with context.temp_override(window=win, area=area, region=reg):\n                        bpy.ops.screen.screen_full_area(use_hide_panels=bool(own))\n                    st.clean = True\n                else:\n                    with context.temp_override(window=win, area=area, region=reg):\n                        bpy.ops.screen.back_to_previous()\n                    st.clean = False\n            except Exception as e:\n                self.report({\'WARNING\'}, "Couldn\'t change the view: %s" % e)\n            mv = main_view()\n            if mv is not None:\n                sp = mv[1].spaces.active\n                for attr in (\'show_gizmo_navigate\', \'show_gizmo_tool\', \'show_gizmo_context\'):\n                    try:\n                        setattr(sp, attr, not st.clean)\n                    except Exception:\n                        pass\n                try:\n                    sp.overlay.show_text = not st.clean     # the \'Camera Perspective\' writing\n                    sp.overlay.show_stats = False\n                except Exception:\n                    pass\n                if not st.clean and _float_window() is not None:\n                    sp.show_region_ui = False\n                mv[1].tag_redraw()\n            return {\'FINISHED\'}\n\n    class PTB_PT_panel(bpy.types.Panel):\n        bl_label = "Photo to Building"\n        bl_space_type = \'VIEW_3D\'\n        bl_region_type = \'UI\'\n        bl_category = "Photo to Building"\n\n        def draw(self, context):\n            self.layout.operator("eddy_ptb.float", icon=\'WINDOW\')\n            draw_panel(self.layout, context)\n\n    class PTB_PT_float(bpy.types.Panel):\n        """The same panel, in its own window (the World tab of a Properties window - empty in this file)."""\n        bl_label = "Photo to Building"\n        bl_space_type = \'PROPERTIES\'\n        bl_region_type = \'WINDOW\'\n        bl_context = "world"                    # the photo has no world, so nothing else shows on this tab\n        bl_order = -1\n\n        def draw(self, context):\n            draw_panel(self.layout, context)\n\n    CLASSES = (PTB_Settings, PTB_OT_click, PTB_OT_clear, PTB_OT_part, PTB_OT_start, PTB_OT_float, PTB_OT_send,\n               PTB_OT_goto, PTB_OT_walk, PTB_OT_restart, PTB_OT_clean, PTB_OT_add_photo, PTB_OT_photo,\n               PTB_OT_pick,\n               PTB_PT_panel, PTB_PT_float)\n\n\ndef register():\n    for c in CLASSES:\n        try:\n            bpy.utils.unregister_class(c)\n        except Exception:\n            pass\n        try:\n            bpy.utils.register_class(c)\n        except Exception:\n            if \'bl_order\' in c.__dict__:                    # an older Blender that doesn\'t take it\n                delattr(c, \'bl_order\')\n                bpy.utils.register_class(c)\n            else:\n                raise\n    bpy.types.Scene.ptb = bpy.props.PointerProperty(type=PTB_Settings)\n    ns = bpy.app.driver_namespace\n    old = ns.get("ptb_draw")\n    if old is not None:\n        try:\n            bpy.types.SpaceView3D.draw_handler_remove(old, \'WINDOW\')\n        except Exception:\n            pass\n    ns["ptb_draw"] = bpy.types.SpaceView3D.draw_handler_add(draw_overlay, (), \'WINDOW\', \'POST_PIXEL\')\n    old = ns.get("ptb_draw2")\n    if old is not None:\n        try:\n            bpy.types.SpaceProperties.draw_handler_remove(old, \'WINDOW\')\n        except Exception:\n            pass\n    try:\n        ns["ptb_draw2"] = bpy.types.SpaceProperties.draw_handler_add(draw_preview, (), \'WINDOW\', \'POST_PIXEL\')\n    except Exception as e:\n        print("Photo to Building: no preview:", e)\n\n\ndef load_from_scene():\n    """Takes the clicks kept in the saved file (opened again)."""\n    sc = bpy.context.scene\n    try:\n        d = json.loads(sc.get(\'ptb_json\') or "")\n    except Exception:\n        d = None\n    if isinstance(d, dict) and d.get(\'W\'):\n        migrate(d)\n        STATE[\'data\'] = d\n        st = sc.ptb\n        props_from_part(st, cur_part(d))\n        st.busy = True\n        for key in (\'known_what\', \'known_mm\'):\n            if d.get(key) is not None:\n                try:\n                    setattr(st, key, d[key])\n                except Exception:\n                    pass\n        st.busy = False\n        recompute(False)\n        return True\n    return False\n\n\ndef _float_window():\n    """The panel\'s own window, if it\'s open: a window with just a Properties editor in it."""\n    for win in bpy.context.window_manager.windows:\n        areas = list(win.screen.areas)\n        if len(areas) == 1 and areas[0].type == \'PROPERTIES\':\n            return win\n    return None\n\n\ndef open_float(force=False):\n    """Opens the panel in a window of its own (a copy of a small editor, turned into the Scene properties),\n    and puts the side panel in the photo\'s view away. True if it\'s open."""\n    try:\n        win = _float_window()\n        if win is None:\n            mv = main_view()\n            if mv is None:\n                return False\n            mwin = mv[0]\n            src = None\n            for kind in (\'PROPERTIES\', \'OUTLINER\'):\n                src = next((a for a in mwin.screen.areas if a.type == kind), None)\n                if src is not None:\n                    break\n            if src is None:\n                return False\n            before = set(w.as_pointer() for w in bpy.context.window_manager.windows)\n            reg = next((r for r in src.regions if r.type == \'WINDOW\'), None)\n            with bpy.context.temp_override(window=mwin, area=src, region=reg):\n                bpy.ops.screen.area_dupli(\'INVOKE_DEFAULT\')\n            win = next((w for w in bpy.context.window_manager.windows if w.as_pointer() not in before), None)\n            if win is None:\n                return False\n        area = win.screen.areas[0]\n        if area.type != \'PROPERTIES\':\n            area.type = \'PROPERTIES\'\n        sp = area.spaces.active\n        try:\n            bpy.context.scene.world = None             # nothing of its own on the World tab, then\n        except Exception:\n            pass\n        try:\n            sp.context = \'WORLD\'\n        except Exception:\n            pass\n        for attr in (\'show_region_navigation_bar\', \'show_region_header\'):\n            try:\n                setattr(sp, attr, False)                # just the panel: no tabs down the side, no header\n            except Exception:\n                pass\n        area.tag_redraw()\n        mv = main_view()\n        if mv is not None:\n            try:\n                mv[1].spaces.active.show_region_ui = False     # the photo gets the whole view\n            except Exception:\n                pass\n        return True\n    except Exception as e:\n        print("Photo to Building: its own window:", e)\n        return False\n\n\ndef view_through_camera():\n    try:\n        for win in bpy.context.window_manager.windows:\n            for area in win.screen.areas:\n                if area.type != \'VIEW_3D\':\n                    continue\n                sp = area.spaces[0]\n                try:\n                    sp.show_region_ui = True\n                except Exception:\n                    pass\n                try:\n                    sp.overlay.show_floor = False\n                    sp.overlay.show_axis_x = sp.overlay.show_axis_y = False\n                except Exception:\n                    pass\n                rv = sp.region_3d\n                rv.view_perspective = \'CAMERA\'\n                try:\n                    rv.lock_rotation = True                # dragging the wheel slides it, never turns it\n                except Exception:\n                    pass\n                reg = [r for r in area.regions if r.type == \'WINDOW\'][0]\n                if STATE[\'job\'].get(\'fresh\', True):       # opened again: the view stays as it was left\n                    with bpy.context.temp_override(window=win, area=area, region=reg):\n                        try:\n                            bpy.ops.view3d.view_center_camera()\n                        except Exception:\n                            pass\n                area.tag_redraw()\n    except Exception as e:\n        print("Photo to Building: view:", e)\n    bpy.app.timers.register(lambda: (open_float(), None)[1], first_interval=0.6)\n    try:\n        if not bpy.app.timers.is_registered(keep_saving):\n            bpy.app.timers.register(keep_saving, first_interval=60.0, persistent=True)\n    except Exception:\n        pass\n    return None\n\n\ndef setup_photo(job):\n    """A new start: the photo on a camera, the lines where they start."""\n    sc = bpy.context.scene\n    for ob in list(bpy.data.objects):\n        bpy.data.objects.remove(ob, do_unlink=True)\n    try:\n        sc.world = None                                 # keeps the panel\'s own window clear\n    except Exception:\n        pass\n    img = bpy.data.images.load(job[\'photo\'], check_existing=True)\n    W, H = int(img.size[0]), int(img.size[1])\n    if W <= 0 or H <= 0:\n        raise ValueError("The photo couldn\'t be read")\n    cd = bpy.data.cameras.new("Photo camera")\n    ob = bpy.data.objects.new("Photo camera", cd)\n    sc.collection.objects.link(ob)\n    sc.camera = ob\n    sc.render.resolution_x, sc.render.resolution_y = W, H\n    sc.render.resolution_percentage = 100\n    sc.render.pixel_aspect_x = sc.render.pixel_aspect_y = 1.0\n    cd.clip_start, cd.clip_end = 0.01, 10000.0\n    cd.show_background_images = True\n    bg = cd.background_images.new()\n    bg.image = img\n    try:\n        bg.frame_method = \'STRETCH\'\n        bg.alpha = 1.0\n        bg.display_depth = \'BACK\'\n    except Exception:\n        pass\n    try:\n        cd.passepartout_alpha = 0.9\n    except Exception:\n        pass\n    d = data_default(W, H)\n    migrate(d)\n    d[\'photos\'][0].update(path=job[\'photo\'], img=str(img.name))\n    for key in (\'known_what\', \'known_mm\'):\n        if job.get(key) is not None:\n            d[key] = job[key]\n    for key in (\'storeys\', \'roof\', \'roof_low\', \'shape\', \'depth_mm\'):\n        if job.get(key) is not None:\n            d[\'parts\'][0][key] = job[key]\n    STATE[\'data\'] = d\n    st = sc.ptb\n    props_from_part(st, cur_part(d))\n    st.busy = True\n    for key in (\'known_what\', \'known_mm\'):\n        try:\n            setattr(st, key, d[key])\n        except Exception:\n            pass\n    st.busy = False\n    from math import radians\n    ob.location = (0.0, 0.0, EYE)\n    ob.rotation_euler = (radians(90), 0.0, 0.0)\n    recompute()\n\n\ndef run(job_path):\n    job = json.load(open(job_path, encoding="utf-8"))\n    STATE[\'job\'] = job\n    register()\n    sc = bpy.context.scene\n    sc.ptb.out_json = job.get(\'out_json\', \'\')\n    fresh = job.get(\'fresh\', True) or not load_from_scene()\n    if fresh:\n        setup_photo(job)\n    cp = os.path.join(os.path.dirname(job_path), "clicks.json")\n    newer = False\n    try:\n        newer = os.path.isfile(cp) and (fresh or not bpy.data.filepath or\n                                        os.path.getmtime(cp) > os.path.getmtime(bpy.data.filepath) + 5.0)\n    except Exception:\n        pass\n    if not job.get(\'fresh\', True) and newer:       # clicked in IngeTrazo since: carry on from those clicks\n        try:\n            cl = json.load(open(cp, encoding="utf-8")).get(\'clicks\')\n            d0 = STATE[\'data\']\n            if isinstance(cl, dict) and cl.get(\'W\') == d0[\'W\'] and cl.get(\'H\') == d0[\'H\']:\n                migrate(cl)\n                cl[\'photos\'][0].update(path=d0[\'photos\'][0].get(\'path\'), img=d0[\'photos\'][0].get(\'img\'))\n                STATE[\'data\'] = cl\n                props_from_part(sc.ptb, cur_part(cl))\n                sc.ptb.busy = True\n                for key in (\'known_what\', \'known_mm\'):\n                    try:\n                        setattr(sc.ptb, key, cl[key])\n                    except Exception:\n                        pass\n                sc.ptb.busy = False\n                recompute()\n        except Exception as e:\n            print("Photo to Building: the clicks from IngeTrazo couldn\'t be read:", e)\n    d = STATE[\'data\']\n    if d is not None:                                     # the other photos picked in IngeTrazo\n        for ex in job.get(\'extra_photos\') or []:\n            add_photo_data(d, ex.get(\'path\'), \'wall\' if ex.get(\'kind\') == \'wall\' else \'corner\')\n        recompute()\n    # keep this script in the file, so the panel is there when it\'s opened again\n    try:\n        src = open(__file__, encoding="utf-8").read()\n        t = bpy.data.texts.get("photo_to_building.py") or bpy.data.texts.new("photo_to_building.py")\n        t.clear()\n        t.write(src)\n        t.use_module = True\n    except Exception as e:\n        print("Photo to Building: script not kept in the file:", e)\n    bpy.app.timers.register(view_through_camera, first_interval=0.5)\n    blend = job.get(\'out_blend\')\n    if blend:\n        def save_later():\n            try:\n                bpy.ops.wm.save_as_mainfile(filepath=blend)\n            except Exception as e:\n                print("Photo to Building: file not saved:", e)\n            return None\n        bpy.app.timers.register(save_later, first_interval=2.0)\n    print("Photo to Building: ready")\n\n\nif IN_BLENDER:\n    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []\n    if __name__ == "__main__" and argv:\n        try:\n            run(argv[0])\n        except Exception:\n            import traceback\n            msg = traceback.format_exc()\n            print("Photo to Building couldn\'t start:\\n" + msg)\n            try:                                       # IngeTrazo shows this, so it doesn\'t just sit there\n                with open(os.path.join(os.path.dirname(argv[0]), "3D program problem.txt"), "w",\n                          encoding="utf-8") as f:\n                    f.write(msg)\n            except Exception:\n                pass\n    else:\n        register()             # opened again from a saved file: put the panel back\n        try:\n            load_from_scene()\n        except Exception as e:\n            print("Photo to Building:", e)\n'
