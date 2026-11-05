# SPDX-License-Identifier: GPL-3.0-or-later
# 3D Find & Replace for IngeTrazo
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
3D Find & Replace - swaps every copy of one part for another, in one go, in IngeTrazo.

Model with light stand-ins and swap in the full detail when you're ready: a steam loco can
carry hundreds of rivets, and every one is dozens of faces. Put a flat hex marker (a few
faces) on each rivet spot while you work, so the model stays quick to turn and edit; when
it's done, swap every marker for the full rivet or bolt. Swap them back any time.

  * Light part / Detail part - pick the marker and the full part (from the lists, or from
    what's selected). Every copy is found, inside other groups too.
  * Show detail / Go light - one button each way. The part going out is kept in the file,
    so the other button can always bring it back.
  * Fit options - the new part lands where each old one sat: base centre on base centre (the rivet
    sits on the plate where the marker sat), centre on centre, or component origin on
    origin. It takes each marker's turn, so rivets on a curved boiler face out with it.
  * Make a part - a flat hex marker, a round-head rivet, a hex bolt head or a nut on a
    bolt end, at real size, on the centre of the selected face.
Everything is one Undo.
"""

import math
from tools.base import Tool
from PySide6.QtGui import QVector3D, QMatrix4x4
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton, QCheckBox, QGroupBox,
    QComboBox, QDoubleSpinBox, QSpinBox, QLineEdit, QTabWidget, QWidget, QMessageBox
)

PLUGIN_NAME = "3D Find & Replace"
VERSION = "6"
MM = 1000.0                       # IngeTrazo works in metres; the window shows mm


# ---------------------------------------------------------------------------
# 4 x 4 matrices as plain lists (row by row), so the sums can be checked on their own
# ---------------------------------------------------------------------------
def m_ident():
    return [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def m_mul(a, b):
    return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)] for r in range(4)]


def m_trans(x, y, z):
    m = m_ident()
    m[0][3], m[1][3], m[2][3] = float(x), float(y), float(z)
    return m


def m_rot_z(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [[c, -s, 0.0, 0.0], [s, c, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def m_flip_x():
    """Upside down: half a turn about its own X."""
    return [[1.0, 0.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def m_apply(m, p):
    return tuple(m[r][0] * p[0] + m[r][1] * p[1] + m[r][2] * p[2] + m[r][3] for r in range(3))


def m_vec(m, v):
    return tuple(m[r][0] * v[0] + m[r][1] * v[1] + m[r][2] * v[2] for r in range(3))


def m_inv(m):
    """Inverse of an affine 4 x 4 (any 3 x 3 part that isn't flat)."""
    a = [row[:3] for row in m[:3]]
    det = (a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
           - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
           + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]))
    if abs(det) < 1e-30:
        raise ValueError("a placement squashed flat")
    inv = [[0.0] * 3 for _ in range(3)]
    for r in range(3):
        for c in range(3):
            r1, r2 = [i for i in range(3) if i != c]
            c1, c2 = [i for i in range(3) if i != r]
            minor = a[r1][c1] * a[r2][c2] - a[r1][c2] * a[r2][c1]
            inv[r][c] = ((-1) ** (r + c)) * minor / det
    t = [m[0][3], m[1][3], m[2][3]]
    it = [-(inv[r][0] * t[0] + inv[r][1] * t[1] + inv[r][2] * t[2]) for r in range(3)]
    return [inv[0] + [it[0]], inv[1] + [it[1]], inv[2] + [it[2]], [0.0, 0.0, 0.0, 1.0]]


def _unit(v):
    L = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    return (v[0] / L, v[1] / L, v[2] / L) if L > 1e-15 else None


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def m_frame(o, x, y, z):
    """The matrix whose columns are x, y, z and whose move is o."""
    return [[x[0], y[0], z[0], o[0]], [x[1], y[1], z[1], o[1]], [x[2], y[2], z[2], o[2]],
            [0.0, 0.0, 0.0, 1.0]]


def m_rigid(m):
    """m with any stretch or squash taken out: the same place and turn, at full size.
    Red first, green squared to it, blue from both (a mirrored one stays mirrored)."""
    x = _unit(m_vec(m, (1.0, 0.0, 0.0))) or (1.0, 0.0, 0.0)
    y0 = m_vec(m, (0.0, 1.0, 0.0))
    z0 = m_vec(m, (0.0, 0.0, 1.0))
    d = _dot(y0, x)
    y = _unit((y0[0] - x[0] * d, y0[1] - x[1] * d, y0[2] - x[2] * d)) or _unit(_cross(z0, x)) or (0.0, 1.0, 0.0)
    z = _unit(_cross(x, y)) or (0.0, 0.0, 1.0)
    if _dot(z, z0) < 0:
        z = (-z[0], -z[1], -z[2])
    return m_frame((m[0][3], m[1][3], m[2][3]), x, y, z)


def m_from_q(q):
    """A QMatrix4x4 as rows (None = no turn or move)."""
    if q is None:
        return m_ident()
    d = list(q.data())                                 # column by column
    return [[float(d[c * 4 + r]) for c in range(4)] for r in range(4)]


def m_to_q(m):
    return QMatrix4x4(*[float(m[r][c]) for r in range(4) for c in range(4)])


# ---------------------------------------------------------------------------
# Where a part sits: its own axes and the box it fits in, in those axes
# ---------------------------------------------------------------------------
LINE_UP = [
    ("base", "Base centre on base centre",
     "The middle of the bottom of the new part goes where the middle of the bottom of the old one was, "
     "square to it - a rivet sits on the plate where its marker sat. Bottom means its own blue (Z) axis, "
     "so turned markers on a boiler or a smokebox front give rivets that face out the same way."),
    ("centre", "Centre on centre",
     "The middle of the new part goes where the middle of the old one was."),
    ("origin", "Component origin on origin",
     "The new part's own origin goes where the old one's was, as IngeTrazo's own Replace Component does. "
     "Best when both parts were drawn round the same point."),
]


def _mesh_points(mesh):
    """Every corner of a mesh as (x, y, z) in its own space."""
    try:
        from core.group import _local_points
        arr = _local_points(mesh)
        if arr is None:
            return []
        return [(float(p[0]), float(p[1]), float(p[2])) for p in arr]
    except Exception:
        pass
    out = []
    for v in list(getattr(mesh, 'vertices', None) or []):
        p = getattr(v, 'position', v)
        try:
            out.append((float(p.x()), float(p.y()), float(p.z())))
        except Exception:
            pass
    return out


def _iter_placements(group, base=None):
    try:
        from core.group import iter_placements
        yield from iter_placements(group, base)
        return
    except ImportError:
        pass
    m = getattr(group, 'xform', None)
    if base is not None:
        m = base if m is None else base * m
    yield group, m
    for ch in getattr(group, 'children', None) or ():
        yield from _iter_placements(ch, m)


def own_points(g):
    """g's corners - its own mesh and every group inside it - in g's own mesh space (what its
    xform carries into the model)."""
    pts = list(_mesh_points(g.mesh))
    for ch in getattr(g, 'children', None) or ():
        for pg, q in _iter_placements(ch):
            m = m_from_q(q) if q is not None else None
            for p in _mesh_points(pg.mesh):
                pts.append(m_apply(m, p) if m else p)
    return pts


def axes_of(g):
    a = getattr(g, 'axes', None)
    return m_from_q(a) if a is not None else m_ident()


def frame_of(g):
    """Where g's own axes sit, in the space g lives in (the model, or the group it's in)."""
    x = getattr(g, 'xform', None)
    return m_mul(m_from_q(x) if x is not None else m_ident(), axes_of(g))


_BOUNDS = {}


def local_box(g):
    """(lo, hi): the box g fits in, measured along its own axes."""
    a = getattr(g, 'axes', None)
    akey = tuple(round(v, 9) for v in a.data()) if a is not None else None
    key = (id(g.mesh), akey) if getattr(g, 'xform', None) is not None else None
    if key is not None and key in _BOUNDS:
        return _BOUNDS[key]
    inv = m_inv(axes_of(g))
    pts = [m_apply(inv, p) for p in own_points(g)]
    if not pts:
        box = ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    else:
        box = (tuple(min(p[k] for p in pts) for k in range(3)),
               tuple(max(p[k] for p in pts) for k in range(3)))
    if key is not None:
        _BOUNDS[key] = box
    return box


def anchor(box, how):
    lo, hi = box
    if how == "origin":
        return (0.0, 0.0, 0.0)
    cx, cy = (lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0
    if how == "centre":
        return (cx, cy, (lo[2] + hi[2]) / 2.0)
    return (cx, cy, lo[2])


def placement_for(target_frame, target_box, source_axes, source_box, how="base", turn=0.0,
                  flip=False, scale=False, reverse=False):
    """The xform that puts the source part where the target sat (both as row lists).
    reverse: putting a light part back where its detail part sits - turn and flip undone, so
    going to detail and back again leaves every marker where it started.

    target_frame: the target's own axes in the space it lives in.  source_axes: the source's
    axes in its mesh space.  Boxes are measured along each one's own axes."""
    at = anchor(target_box, how)
    asrc = anchor(source_box, how)
    if scale:
        place = m_mul(target_frame, m_trans(*at))
    else:
        rig = m_rigid(target_frame)
        o = m_apply(target_frame, at)
        place = [row[:] for row in rig]
        place[0][3], place[1][3], place[2][3] = o
    m = place
    if reverse:
        if flip:
            if how == "base":
                lo, hi = target_box
                m = m_mul(m, m_trans(0.0, 0.0, hi[2] - lo[2]))
            m = m_mul(m, m_flip_x())
        if turn:
            m = m_mul(m, m_rot_z(-turn))
    else:
        if turn:
            m = m_mul(m, m_rot_z(turn))
        if flip:
            m = m_mul(m, m_flip_x())
            # turned over, it hangs from the anchor: set it back so it still sits on its base
            if how == "base":
                lo, hi = source_box
                m = m_mul(m, m_trans(0.0, 0.0, -(hi[2] - lo[2])))
    m = m_mul(m, m_trans(-asrc[0], -asrc[1], -asrc[2]))
    return m_mul(m, m_inv(source_axes))


# ---------------------------------------------------------------------------
# Finding the parts in the model
# ---------------------------------------------------------------------------
def part_key(g):
    """What makes two groups 'the same part': copies sharing one definition (a component, or a
    copied group), or groups with the same name."""
    if getattr(g, 'xform', None) is not None:
        return "def:%d" % id(g.mesh)
    return "name:" + str(getattr(g, 'name', '') or '')


def scene_roots(scene):
    """The groups at the level you're working in: the model, or the group you've opened."""
    ctx = getattr(scene, 'edit_group', None)
    if ctx is not None and getattr(ctx, 'children', None) is not None:
        return list(ctx.children or [])
    return list(getattr(scene, 'groups', None) or [])


def all_groups(roots):
    seen = set()
    for r in roots:
        for g, _m in _iter_placements(r):
            if id(g) in seen:
                continue
            seen.add(id(g))
            yield g


def face_count(g):
    """Faces in one copy (its groups inside too), or None for a big part not read in yet."""
    n = 0
    for pg, _m in _iter_placements(g):
        mesh = pg.mesh
        if 'deferred' in type(mesh).__name__.lower():
            return None
        try:
            n += len(mesh.faces)
        except Exception:
            return None
    return n


def scan(scene):
    """{key: {'name', 'copies': [groups], 'kind', 'rep'}} for every part in the model (nested
    ones too), plus the definitions kept in the file with no copy placed ('copies' empty)."""
    parts = {}
    for g in all_groups(scene_roots(scene)):
        if getattr(g, 'billboard', False) or getattr(g, 'owner', None) is not None:
            continue
        k = part_key(g)
        p = parts.get(k)
        if p is None:
            if getattr(g, 'xform', None) is None:
                kind = "group"
            elif getattr(g, 'component', True):
                kind = "component"
            else:
                kind = "copied group"
            p = parts[k] = dict(name=str(getattr(g, 'name', '') or 'Unnamed'), copies=[], kind=kind, rep=g)
        p['copies'].append(g)
    for t in list(getattr(scene, 'kept_components', None) or []):
        k = part_key(t)
        if k not in parts:
            parts[k] = dict(name=str(getattr(t, 'name', '') or 'Unnamed'), copies=[], kind="kept in file", rep=t)
        else:
            parts[k]['kept'] = t
    return parts


def is_inside(inner, outer):
    """Whether inner is outer, or anywhere inside it."""
    return any(g is inner for g, _m in _iter_placements(outer))


# ---------------------------------------------------------------------------
# The swap, as one undoable step
# ---------------------------------------------------------------------------
def _command_base():
    try:
        from core.history import Command
        return Command
    except Exception:
        return object


_SHARED = ("mesh", "children", "name", "axes", "component", "text3d", "ifc", "ext", "billboard",
           "exploded", "xform")


def _owner_list(scene, g):
    try:
        from core.history import group_owner_list
        return group_owner_list(scene, g)
    except ImportError:
        pass
    if g in scene.groups:
        return scene.groups
    for top in scene.groups:
        for pg, _m in _iter_placements(top):
            kids = getattr(pg, 'children', None)
            if kids and g in kids:
                return kids
    return None


def _copy_group(g):
    from core.group import copy_group
    return copy_group(g)


def _make_template(g):
    try:
        from core.kept_components import make_template
        return make_template(g)
    except ImportError:
        t = _copy_group(g)
        t.xform = QMatrix4x4()
        t.layer, t.material, t.hidden, t.component = None, None, False, True
        return t


class SwapPartsCommand(_command_base()):
    """Every target takes the source's definition at its own place (xforms worked out
    beforehand). A target that's a copy (it has a placement) changes in place, keeping its
    layer, paint, visibility and identity; a plain group is swapped for a new copy in the same
    spot in its list. keep: groups whose definition goes into the file as a kept component
    first, so it can be swapped back."""
    keeps_paint = False
    keeps_groups = False

    def __init__(self, targets, xforms, source, keep=(), tag=None):
        self.targets = list(targets)
        self.xforms = list(xforms)
        self.source = source
        self.keep = list(keep)
        self.tag = tag
        self._templates = None
        self._new = {}
        self._before = []
        self._src_before = None

    def do(self, scene):
        self._before = []
        self._src_before = (self.source.xform, getattr(self.source, 'component', True))
        try:
            self._do(scene)
        except Exception:
            self.undo(scene)            # put back what was done before it went wrong
            raise

    def _do(self, scene):
        import copy as _copy
        src = self.source
        # the definitions that would otherwise be lost, kept in the file
        if self._templates is None:
            self._templates = [_make_template(g) for g in self.keep]
        kept = getattr(scene, 'kept_components', None)
        if kept is not None:
            for t in self._templates:
                if t not in kept:
                    kept.append(t)
        # a plain group used as the source becomes a component, so all the copies share it
        if src.xform is None:
            src.xform = QMatrix4x4()
        src.component = True
        for i, (g, x) in enumerate(zip(self.targets, self.xforms)):
            if getattr(g, 'xform', None) is not None:
                self._before.append(('copy', g, {k: getattr(g, k, None) for k in _SHARED}))
                g.mesh = src.mesh
                g.children = [_shared_child(c) for c in (src.children or ())]
                g.name = src.name
                g.axes = QMatrix4x4(src.axes) if src.axes is not None else None
                g.component = True
                g.text3d = dict(src.text3d) if getattr(src, 'text3d', None) else None
                g.ifc = dict(src.ifc) if getattr(src, 'ifc', None) else None
                g.ext = _tagged_ext(src, self.tag)
                g.billboard = getattr(src, 'billboard', False)
                g.exploded = None
                g.xform = m_to_q(x)
            else:
                owner = _owner_list(scene, g)
                if owner is None:
                    self._before.append(('skip', g, None))
                    continue
                new = self._new.get(i)
                if new is None:
                    new = _copy_group(src)
                    new.xform = m_to_q(x)
                    new.axes = QMatrix4x4(src.axes) if src.axes is not None else None
                    new.component = True
                    new.layer = getattr(g, 'layer', None)
                    new.material = dict(g.material) if getattr(g, 'material', None) else None
                    new.hidden = getattr(g, 'hidden', False)
                    new.locked = False
                    new.exploded, new.explode_offset = None, None
                    new.ext = _tagged_ext(src, self.tag)
                    self._new[i] = new
                idx = owner.index(g)
                owner[idx] = new
                try:
                    scene.selection.discard(g)
                except Exception:
                    pass
                self._before.append(('swap', g, (owner, idx, new)))
        scene.version += 1

    def undo(self, scene):
        for kind, g, data in reversed(self._before):
            if kind == 'copy':
                for k, v in data.items():
                    setattr(g, k, v)
            elif kind == 'swap':
                owner, idx, new = data
                if idx < len(owner) and owner[idx] is new:
                    owner[idx] = g
                elif new in owner:
                    owner[owner.index(new)] = g
                try:
                    scene.selection.discard(new)
                except Exception:
                    pass
        self.source.xform, self.source.component = self._src_before
        kept = getattr(scene, 'kept_components', None)
        if kept is not None:
            for t in self._templates or []:
                if t in kept:
                    kept.remove(t)
        scene.version += 1


SWAP_TAG = "eddy_swap"


def _tagged_ext(src, tag):
    """The source's extension data for a new copy: without any old swap mark, and with this
    swap's mark when it has one (it says the copy was a marker, and which)."""
    import copy as _copy
    ext = getattr(src, 'ext', None)
    ext = _copy.deepcopy(ext) if isinstance(ext, dict) else {}
    ext.pop(SWAP_TAG, None)
    if tag:
        ext[SWAP_TAG] = dict(tag)
    return ext or None


def swapped_from(g):
    """The light part's name a detail copy was swapped in for, or None if it was placed by hand."""
    ext = getattr(g, 'ext', None)
    if isinstance(ext, dict) and isinstance(ext.get(SWAP_TAG), dict):
        return ext[SWAP_TAG].get("light")
    return None


def back_to_light(detail_copies, light_name):
    """The detail copies Go light changes: the ones that were markers of this light part. Any
    you placed yourself stay - unless none were swapped in at all (then every copy goes)."""
    marked = [g for g in detail_copies if swapped_from(g) == light_name]
    if marked:
        return marked
    if any(swapped_from(g) for g in detail_copies):
        return []
    return list(detail_copies)


def _shared_child(c):
    """A group inside the source, shared by every copy (an edit inside one reaches them all)."""
    from core.group import copy_group
    try:
        return copy_group(c, _in_definition=True)
    except TypeError:
        return copy_group(c)


# ---------------------------------------------------------------------------
# Making a marker, rivet or bolt (real size, standing on its base at the origin, Z up)
# ---------------------------------------------------------------------------
SHAPES = [
    ("marker", "Flat hex marker",
     "A thin flat hexagon - 8 faces - to mark where a rivet or bolt goes. Copy it to every spot "
     "while you model, then swap the lot for the real thing."),
    ("rivet", "Round-head rivet",
     "A domed (snap) rivet head, with a short shank under it if you want one to set into the plate."),
    ("bolt", "Hex bolt head",
     "A hexagon bolt head, on a round washer if you give the washer a thickness."),
    ("nut", "Nut on a bolt end",
     "A hexagon nut with the end of the bolt standing out of it, on a washer if you give it a thickness."),
]


def _ring(n, r, z, rot=0.0):
    """n corners round a circle of radius r (to the corners) at height z, anticlockwise from above."""
    return [(r * math.cos(rot + 2 * math.pi * i / n), r * math.sin(rot + 2 * math.pi * i / n), z)
            for i in range(n)]


def hex_r(across_flats):
    return across_flats / (2.0 * math.cos(math.pi / 6.0))


def inradius(n, r):
    return r * math.cos(math.pi / n)


def solid_faces(tiers, dome=None):
    """The faces of a closed solid made of upright prisms stacked one on another, each
    (sides, radius to the corners, turn, bottom, top), with an optional dome on top
    (sides, radius, bottom, height, rings). Each tier sits fully on or under the next, so the
    step between them is a flat ring with the smaller outline as its hole.
    Returns [(outline, [holes])], each wound anticlockwise seen from outside."""
    faces = []

    def up(loop):
        return loop

    def down(loop):
        return list(reversed(loop))

    t0 = tiers[0] if tiers else None
    first = (t0[0], t0[1], t0[2], t0[3]) if t0 else (dome[0], dome[1], 0.0, dome[2])
    faces.append((down(_ring(first[0], first[1], first[3], first[2])), []))       # bottom
    for i, (n, r, rot, z0, z1) in enumerate(tiers):
        b, t = _ring(n, r, z0, rot), _ring(n, r, z1, rot)
        for k in range(n):
            faces.append(([b[k], b[(k + 1) % n], t[(k + 1) % n], t[k]], []))       # sides
        if i + 1 < len(tiers):
            nn, rr, rrot, _a, _b = tiers[i + 1]
            nxt = (nn, rr, rrot)
        elif dome is not None:
            nxt = (dome[0], dome[1], 0.0)
        else:
            faces.append((up(t), []))                                             # flat top
            continue
        lower, upper = (n, r, rot), nxt
        lo_ring = _ring(lower[0], lower[1], z1, lower[2])
        hi_ring = _ring(upper[0], upper[1], z1, upper[2])
        if inradius(upper[0], upper[1]) <= inradius(lower[0], lower[1]):
            faces.append((up(lo_ring), [down(hi_ring)]))        # a ledge facing up, the next tier on it
        else:
            faces.append((down(hi_ring), [up(lo_ring)]))        # an overhang facing down
    if dome is not None:
        n, r, z0, h, rings = dome
        rings = max(1, int(rings))
        prev = _ring(n, r, z0)
        for j in range(1, rings):
            a = (math.pi / 2.0) * j / rings
            cur = _ring(n, r * math.cos(a), z0 + h * math.sin(a))
            for k in range(n):
                faces.append(([prev[k], prev[(k + 1) % n], cur[(k + 1) % n], cur[k]], []))
            prev = cur
        apex = (0.0, 0.0, z0 + h)
        for k in range(n):
            faces.append(([prev[k], prev[(k + 1) % n], apex], []))
    return faces


def part_faces(shape, v):
    """The faces for one of the SHAPES, from the sizes in v (metres)."""
    n = max(6, int(v.get('sides', 16)))
    if shape == "marker":
        return solid_faces([(6, hex_r(v['af']), 0.0, 0.0, v['h'])])
    if shape == "rivet":
        tiers = []
        z = 0.0
        if v.get('shank', 0) > 1e-9:
            tiers.append((n, v['shank_d'] / 2.0 / math.cos(math.pi / n), 0.0, -v['shank'], 0.0))
        if tiers:
            return solid_faces(tiers, dome=(n, v['d'] / 2.0, z, v['h'], max(2, n // 4)))
        return solid_faces([], dome=(n, v['d'] / 2.0, z, v['h'], max(2, n // 4)))
    tiers = []
    z = 0.0
    if v.get('washer_t', 0) > 1e-9:
        tiers.append((n, v['washer_d'] / 2.0, 0.0, z, z + v['washer_t']))
        z += v['washer_t']
    tiers.append((6, hex_r(v['af']), 0.0, z, z + v['h']))
    z += v['h']
    if shape == "nut" and v.get('end', 0) > 1e-9:
        tiers.append((n, v['bolt_d'] / 2.0, 0.0, z, z + v['end']))
    return solid_faces(tiers)


def check_part(shape, v):
    """None if the sizes make a sound part, or what's wrong with them."""
    if shape in ("marker", "bolt", "nut") and v['af'] <= 0:
        return "Give it a width across the flats."
    if shape == "rivet" and v['d'] <= 0:
        return "Give the rivet head a diameter."
    if v['h'] <= 0:
        return "Give it a height."
    if shape in ("bolt", "nut") and v.get('washer_t', 0) > 1e-9:
        if v['washer_d'] / 2.0 * math.cos(math.pi / max(6, int(v.get('sides', 16)))) <= hex_r(v['af']) * 1.0001:
            return ("The washer has to be wider than the hexagon's corners (%.1f mm across)."
                    % (2 * hex_r(v['af']) * MM))
    if shape == "nut" and v.get('end', 0) > 1e-9 and v['bolt_d'] >= v['af'] * 0.999:
        return "The bolt has to be thinner than the nut is across the flats."
    if shape == "rivet" and v.get('shank', 0) > 1e-9 and v['shank_d'] >= v['d'] * 0.95:
        return "The shank has to be thinner than the rivet head."
    return None


# ---------------------------------------------------------------------------
# The parts library: tabs of parts (Markers, Rivets, Bolts & nuts, and your own), kept between
# sessions. A part is either a shape made here (its sizes) or a component you added from a
# model (its faces, standing on its base centre at the origin).
# ---------------------------------------------------------------------------
import os as _os
import json as _json

LIBRARY_FILE = _os.path.join(_os.path.expanduser("~"), ".ingetrazo_eddy_parts.json")
EXT_KEY = "eddy_parts"                 # tags a definition in the model with the library part it came from


def _new_id():
    import uuid
    return uuid.uuid4().hex[:12]


def _shape_part(name, shape, sides=12, **mm):
    return dict(id=_new_id(), kind="shape", name=name, shape=shape, sides=sides, sizes=mm)


def _metric_bolts():
    """ISO sizes: hexagon across flats, head / nut height, and washer (ISO 7089) - all mm."""
    out = []
    for m, af, head, nut, washer in ((12, 18.0, 7.5, 10.0, 24.0), (16, 24.0, 10.0, 13.0, 30.0),
                                     (20, 30.0, 12.5, 16.0, 37.0), (24, 36.0, 15.0, 19.0, 44.0)):
        out.append(_shape_part("Bolt head M%d" % m, "bolt", 12, af=af, h=head, washer_d=washer, washer_t=0.0))
    for m, af, head, nut, washer in ((16, 24.0, 10.0, 13.0, 30.0), (20, 30.0, 12.5, 16.0, 37.0),
                                     (24, 36.0, 15.0, 19.0, 44.0)):
        out.append(_shape_part("Nut on bolt M%d" % m, "nut", 12, af=af, h=nut, washer_d=washer,
                               washer_t=3.0 if m < 20 else 4.0, bolt_d=float(m), end=round(m * 0.4, 1)))
    return out


def _metric_rivets():
    """Snap-head rivets by shank size: head about 1.75 x the shank across, 0.7 x high."""
    return [_shape_part("Snap rivet %d mm" % d, "rivet", 12 if d < 25 else 14,
                        d=round(d * 1.75), h=round(d * 0.7), shank=0.0, shank_d=float(d))
            for d in (16, 19, 22, 25)]


def default_library():
    """Real-size starting points, all in mm: adjust them or add your own."""
    return {"units": "mm", "tabs": [
        {"name": "Markers", "parts": [
            _shape_part("Marker - rivet", "marker", af=30.0, h=2.0),
            _shape_part("Marker - bolt", "marker", af=40.0, h=2.0),
        ]},
        {"name": "Rivets", "parts": _metric_rivets()},
        {"name": "Bolts & nuts", "parts": _metric_bolts()},
    ]}


_OLD_INCH = {"Snap rivet 3/4in", "Snap rivet 7/8in", "Snap rivet 1in", "Bolt head 3/4in",
             "Nut on bolt 3/4in", "Bolt head M20"}


def _to_metric(lib):
    """The first library had inch rivets and bolts: swap those for the mm ones (your own parts stay)."""
    if lib.get("units") == "mm":
        return lib
    for t in lib["tabs"]:
        if t.get("name") == "Rivets":
            t["parts"] = [p for p in t["parts"] if p.get("name") not in _OLD_INCH]
            have = {p.get("name") for p in t["parts"]}
            t["parts"] = [p for p in _metric_rivets() if p["name"] not in have] + t["parts"]
        elif t.get("name") == "Bolts & nuts":
            t["parts"] = [p for p in t["parts"] if p.get("name") not in _OLD_INCH]
            have = {p.get("name") for p in t["parts"]}
            t["parts"] = [p for p in _metric_bolts() if p["name"] not in have] + t["parts"]
        else:
            t["parts"] = [p for p in t["parts"] if p.get("name") not in _OLD_INCH]
    lib["units"] = "mm"
    save_library(lib)
    return lib


def load_library():
    try:
        with open(LIBRARY_FILE, "r", encoding="utf-8") as f:
            lib = _json.load(f)
        if isinstance(lib, dict) and isinstance(lib.get("tabs"), list) and lib["tabs"]:
            return _to_metric(lib)
    except Exception:
        pass
    return default_library()


def save_library(lib):
    try:
        tmp = LIBRARY_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            _json.dump(lib, f, indent=1)
        _os.replace(tmp, LIBRARY_FILE)
        return None
    except Exception as e:
        return str(e)


def entry_polys(entry):
    """[(outline, [holes])] for a library part, in metres, standing on its base at the origin."""
    if entry.get("kind") == "shape":
        v = {k: float(x) / MM for k, x in (entry.get("sizes") or {}).items()}
        for k in ('af', 'd', 'h', 'shank', 'shank_d', 'washer_d', 'washer_t', 'bolt_d', 'end'):
            v.setdefault(k, 0.0)
        v['sides'] = int(entry.get("sides", 12))
        return part_faces(entry["shape"], v)
    out = []
    for f in entry.get("faces") or []:
        out.append(([tuple(p) for p in f[0]], [[tuple(p) for p in h] for h in (f[1] if len(f) > 1 else [])]))
    return out


def entry_check(entry):
    if entry.get("kind") != "shape":
        return None if entry.get("faces") else "This part has no faces saved."
    v = {k: float(x) / MM for k, x in (entry.get("sizes") or {}).items()}
    for k in ('af', 'd', 'h', 'shank', 'shank_d', 'washer_d', 'washer_t', 'bolt_d', 'end'):
        v.setdefault(k, 0.0)
    v['sides'] = int(entry.get("sides", 12))
    return check_part(entry["shape"], v)


def build_definition(entry):
    """A new component (no turn, at the origin) holding the library part, tagged with its id."""
    from core.mesh import Mesh
    from core.group import Group
    mesh = Mesh()
    colours = entry.get("colours") or {}
    for i, (outline, holes) in enumerate(entry_polys(entry)):
        f = mesh.add_face([QVector3D(*p) for p in outline],
                          [[QVector3D(*p) for p in h] for h in holes] or None)
        c = colours.get(str(i))
        if c is not None:
            try:
                f.attrs["color"] = tuple(c) if isinstance(c, list) else c
            except Exception:
                pass
    g = Group(mesh, name=entry.get("name") or "Part")
    g.xform = QMatrix4x4()
    g.component = True
    try:
        g.ext = {EXT_KEY: {"id": entry["id"]}}
    except Exception:
        pass
    return g


def capture_definition(g):
    """Faces of a model part in its own axes, moved so it stands on its base centre at the
    origin - ready to save as a library part. Returns (faces, colours)."""
    tpl = _make_template(g)                       # no placement: the definition as it is
    try:
        from core.group import world_mesh
        mesh = world_mesh(tpl)
    except Exception:
        mesh = tpl.mesh
    inv = m_inv(axes_of(g))
    lo, hi = local_box(g)
    shift = m_trans(-(lo[0] + hi[0]) / 2.0, -(lo[1] + hi[1]) / 2.0, -lo[2])
    m = m_mul(shift, inv)

    def P(v):
        q = getattr(v, 'position', v)
        p = m_apply(m, (float(q.x()), float(q.y()), float(q.z())))
        return [round(p[0], 8), round(p[1], 8), round(p[2], 8)]
    faces, colours = [], {}
    for f in list(getattr(mesh, 'faces', None) or []):
        outline = [P(v) for v in list(getattr(f, 'vertices', None) or [])]
        if len(outline) < 3:
            continue
        holes = []
        for h in list(getattr(f, 'holes', None) or []):
            hl = [P(v) for v in list(h)]
            if len(hl) >= 3:
                holes.append(hl)
        c = (getattr(f, 'attrs', None) or {}).get("color")
        if isinstance(c, (list, tuple, str)):
            colours[str(len(faces))] = list(c) if not isinstance(c, str) else c
        faces.append([outline, holes])
    return faces, colours


def entry_in_model(entry, parts):
    """The key of this library part's definition if it's already in the model (placed or kept)."""
    for k, p in parts.items():
        for g in [p['rep']] + ([p['kept']] if p.get('kept') is not None else []):
            ext = getattr(g, 'ext', None) or {}
            if isinstance(ext, dict) and (ext.get(EXT_KEY) or {}).get("id") == entry.get("id"):
                return k
    if entry.get("kind") != "shape":
        n = len(entry.get("faces") or [])
        for k, p in parts.items():
            if p['name'] == entry.get("name") and face_count(p['rep']) == n:
                return k
    return None


class AddKeptCommand(_command_base()):
    """Puts definitions in the file with no copy placed (Undo takes them out)."""
    keeps_paint = False
    keeps_groups = True

    def __init__(self, templates):
        self.templates = list(templates)

    def do(self, scene):
        for t in self.templates:
            if t not in scene.kept_components:
                scene.kept_components.append(t)
        scene.version += 1

    def undo(self, scene):
        for t in self.templates:
            if t in scene.kept_components:
                scene.kept_components.remove(t)
        scene.version += 1



# What was last clicked in IngeTrazo's Components tray ('In model' list), so a component
# clicked there - even one kept in the file with no copy placed - can be used.
_TRAY = {'def': None}


def _tray_clicked(item):
    try:
        from PySide6.QtCore import Qt
        if item is None:
            return
        gs = item.data(Qt.UserRole) or []
        kept = item.data(Qt.UserRole + 1)
        d = gs[0] if gs else kept
        if d is not None:
            _TRAY['def'] = d
    except Exception:
        pass


def part_icon(definition):
    """The same picture the Components tray shows for a part, or None."""
    if definition is None:
        return None
    try:
        from views.component_thumbs import thumbnail
        from PySide6.QtGui import QIcon
        return QIcon(thumbnail(definition))
    except Exception:
        return None


def _icon_grid(lst):
    """A list shown as pictures with their names under them, like the Components tray."""
    try:
        from PySide6.QtWidgets import QListView
        from PySide6.QtCore import QSize
        lst.setViewMode(QListView.ViewMode.IconMode)
        lst.setIconSize(QSize(56, 56))
        lst.setGridSize(QSize(112, 112))
        lst.setResizeMode(QListView.ResizeMode.Adjust)
        lst.setMovement(QListView.Movement.Static)
        lst.setWordWrap(True)
        lst.setUniformItemSizes(True)
    except Exception:
        pass


def patch_tray_menu():
    """Adds 'Set as light part' and 'Set as detail part' to the right-click menu of the
    'In model' list in IngeTrazo's Components tray - the pictures you can already see."""
    try:
        from PySide6.QtWidgets import QApplication
        cls = None
        for w in QApplication.allWidgets():
            if type(w).__name__ == "ComponentsPanel":
                cls = type(w)
                break
        if cls is None or getattr(cls, "_eddy_fr_patched", False) or not hasattr(cls, "_in_model_actions"):
            return
        orig = cls._in_model_actions

        def actions(self, groups, kept=None):
            out = list(orig(self, groups, kept))
            d = kept if kept is not None else (groups[0] if groups else None)
            if d is not None:
                win = getattr(self, "_window", None)
                out.append(("Set as light part (%s)" % PLUGIN_NAME,
                            lambda: _set_from_tray(win, d, True), None,
                            "Makes this the light part (the marker) in %s." % PLUGIN_NAME))
                out.append(("Set as detail part (%s)" % PLUGIN_NAME,
                            lambda: _set_from_tray(win, d, False), None,
                            "Makes this the detail part (the rivet or bolt) in %s." % PLUGIN_NAME))
            return out
        cls._in_model_actions = actions
        cls._eddy_fr_patched = True
    except Exception:
        pass


def _set_from_tray(win, definition, light):
    try:
        dlg = FindReplaceTool._dialog
        if dlg is None or not dlg.isVisible():
            FindReplaceTool().on_activate(getattr(win, "viewport", None))
            dlg = FindReplaceTool._dialog
        if dlg is not None:
            dlg.tabs.setCurrentIndex(0)
            dlg.set_part(light=light, key=part_key(definition))
            dlg.raise_()
    except Exception as e:
        print("%s: %s" % (PLUGIN_NAME, e))


def hook_tray():
    try:
        from PySide6.QtWidgets import QApplication
        for w in QApplication.allWidgets():
            if type(w).__name__ == "ComponentsPanel":
                lst = getattr(w, "_in_model", None)
                if lst is not None and not getattr(lst, "_eddy_fr_hooked", False):
                    lst.itemClicked.connect(_tray_clicked)
                    lst.itemPressed.connect(_tray_clicked)
                    lst._eddy_fr_hooked = True
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


EDDY_TIPS = {
    "components in this model": "Every component in the model, with how many copies are placed - "
                                "including ones kept in the file with none placed (a marker you've "
                                "swapped away). Click one, then Set as light part or Set as detail part "
                                "(or right-click it). You can also right-click a component in IngeTrazo's "
                                "Components tray.",
    "light part": "The quick, light stand-in you place while modelling - a flat hex marker on each rivet "
                  "spot. A part with no copies placed is kept in the file, ready to come back.",
    "detail part": "The full part each marker turns into - your rivet or bolt.",
    "show detail": "Changes every light part into the detail part, each one sitting where its marker "
                   "sat and facing the same way. One Undo puts them back.",
    "go light": "Changes the detail parts that were markers back into the light part, so the model is "
                "quick to work on again. Any you placed yourself stay as they are. One Undo puts them back.",
    "look in": "Where to change them: the whole model (or the group you have open), only inside the "
               "objects you've selected (say, just the tender), or only the copies you've selected.",
    "line up": "How the detail part sits on each marker.",
    "turn": "Turns every detail part this much about its own up (blue) axis - to set the flats of a "
            "bolt head square, say. Going light turns them back.",
    "flip it over": "Puts every detail part upside down on its spot - for a part drawn the other way up "
                    "to its marker.",
    "scale with the marker": "Ticked, a marker you made bigger or smaller makes its detail part bigger "
                             "or smaller too. Unticked, every detail part comes in at its own size.",
    "refresh": "Reads the model again - after you've added, copied or deleted parts.",
    "use selected": "Takes the part that's selected in the model.",
    "shape": "What kind of part.",
    "place it": "Puts a copy of the part on the centre of the selected face, standing on it and facing "
                "out (or at the origin with nothing selected). Copy it to each spot with Move + Ctrl.",
    "use as light": "Makes this the light part on the Light / detail tab (it's put in the file if it "
                    "isn't there yet - no copy is placed).",
    "use as detail": "Makes this the detail part on the Light / detail tab (it's put in the file if it "
                     "isn't there yet - no copy is placed).",
    "add selected component to this tab": "Saves the component selected in the model - or the one picked in "
                                          "the list on the Light / detail tab - into this tab, so it's there in every model.",
    "add as new part": "Saves the shape and sizes above as a new part in this tab.",
    "save changes": "Saves the shape, sizes and name above over the part picked in the list.",
    "across flats": "Width of the hexagon from one flat side to the opposite one, in real mm.",
    "diameter": "Width of the rivet head, in real mm.",
    "height": "How tall the head, nut or marker is, in real mm.",
    "shank length": "Length of the shank under the rivet head, to set into the plate (0 = no shank, "
                    "the head sits on the surface).",
    "shank diameter": "Width of the rivet's shank, in real mm.",
    "washer diameter": "Width of the round washer under the bolt head or nut, in real mm.",
    "washer thickness": "Thickness of the washer (0 = no washer).",
    "bolt diameter": "Width of the bolt standing out of the nut, in real mm.",
    "bolt end": "How far the end of the bolt stands out of the nut (0 = flush).",
    "sides": "How many sides round curves. Fewer is lighter (a model with 1000 rivets has 1000 times "
             "this); 12 to 16 looks round once printed small.",
    "name": "The name the part goes by in the model and in the lists.",
}
EDDY_TIPS_END = None


try:
    from PySide6.QtCore import Qt as _Qt
    _TIP_ROLE = _Qt.ItemDataRole.ToolTipRole
except Exception:
    _TIP_ROLE = 3


def _fmt_faces(n):
    return "{:,}".format(n)


class FindReplaceDialog(QDialog):
    # remembered while IngeTrazo is open
    state = dict(how=0, turn=0.0, flip=False, scale=False, scope=0, shape=0,
                 sizes={}, tab=0, fit_open=False)

    def __init__(self, viewport, tool):
        super().__init__(viewport)
        self.setWindowTitle("%s  (version %s)" % (PLUGIN_NAME, VERSION))
        self.setModal(False)
        self.viewport = viewport
        self.tool = tool
        self.parts = {}
        lay = QVBoxLayout(self)
        self.tabs = QTabWidget()
        lay.addWidget(self.tabs)
        self.tabs.addTab(self._find_page(), "Light \u21c4 detail")
        self.tabs.addTab(self._make_page(), "Parts")
        self.tabs.setTabToolTip(0, "Change every marker into the detail part, and back.")
        self.tabs.setTabToolTip(1, "Your parts library: markers, rivets, bolts and your own components, "
                                   "in tabs of your own.")
        self.lbl_report = QLabel()
        self.lbl_report.setWordWrap(True)
        lay.addWidget(self.lbl_report)
        brow = QHBoxLayout()
        brow.addStretch(1)
        b_close = QPushButton("Close")
        b_close.clicked.connect(self.close)
        brow.addWidget(b_close)
        lay.addLayout(brow)
        try:
            self.setMinimumWidth(430)
        except Exception:
            pass
        hook_tray()
        patch_tray_menu()
        self.tabs.setCurrentIndex(self.state.get('tab', 0))
        self.tabs.currentChanged.connect(lambda i: self.state.__setitem__('tab', i))
        self.refresh()

    # -------------------------------------------------------------- pages
    def _find_page(self):
        page = QWidget()
        v = QVBoxLayout(page)
        intro = QLabel("Pick a light part (a marker) and a detail part (the full rivet or bolt). One "
                       "button changes every marker into the detail part, the other changes them all "
                       "back to markers.")
        intro.setWordWrap(True)
        v.addWidget(intro)

        from PySide6.QtWidgets import QListWidget
        lab = QLabel("<b>Components in this model</b> - click one, then set it as the light or detail part:")
        lab.setWordWrap(True)
        v.addWidget(lab)
        self.comp_list = QListWidget()
        self.comp_list.setToolTip(EDDY_TIPS["components in this model"])
        _icon_grid(self.comp_list)
        self.comp_list.setMinimumHeight(140)
        from PySide6.QtCore import Qt as _Q
        self.comp_list.setContextMenuPolicy(_Q.CustomContextMenu)
        self.comp_list.customContextMenuRequested.connect(self._comp_menu)
        self.comp_list.itemDoubleClicked.connect(lambda *_: self.set_part(light=True))
        self.comp_list.currentRowChanged.connect(self._comp_row)
        v.addWidget(self.comp_list)
        r = QHBoxLayout()
        self.b_set_light = QPushButton("Set as light part")
        self.b_set_light.setToolTip(EDDY_TIPS["light part"])
        self.b_set_light.clicked.connect(lambda: self.set_part(light=True))
        self.b_set_detail = QPushButton("Set as detail part")
        self.b_set_detail.setToolTip(EDDY_TIPS["detail part"])
        self.b_set_detail.clicked.connect(lambda: self.set_part(light=False))
        r.addWidget(self.b_set_light)
        r.addWidget(self.b_set_detail)
        b_ref = QPushButton("Refresh")
        b_ref.setToolTip(EDDY_TIPS["refresh"])
        b_ref.clicked.connect(self.refresh)
        r.addStretch(1)
        r.addWidget(b_ref)
        v.addLayout(r)
        form = QFormLayout()
        self.lbl_light = QLabel("-")
        self.lbl_detail = QLabel("-")
        form.addRow("Light part:", self.lbl_light)
        form.addRow("Detail part:", self.lbl_detail)
        v.addLayout(form)
        self.light_key = None
        self.detail_key = None
        self._sig = self.state.setdefault('sig', {})        # remembered while IngeTrazo is open

        big = ("QPushButton { font-size: 11pt; font-weight: bold; padding: 9px; text-align: left; }")
        self.b_detail = QPushButton("Show detail")
        self.b_detail.setStyleSheet(big)
        self.b_detail.setToolTip(EDDY_TIPS["show detail"])
        self.b_detail.clicked.connect(lambda: self.swap(to_detail=True))
        v.addWidget(self.b_detail)
        self.b_light = QPushButton("Go light")
        self.b_light.setStyleSheet(big)
        self.b_light.setToolTip(EDDY_TIPS["go light"])
        self.b_light.clicked.connect(lambda: self.swap(to_detail=False))
        v.addWidget(self.b_light)

        self.lbl_faces = QLabel("-")
        self.lbl_faces.setWordWrap(True)
        self.lbl_faces.setToolTip("How many faces the copies come to, light and with detail.")
        v.addWidget(self.lbl_faces)

        r = QHBoxLayout()
        r.addWidget(QLabel("Look in:"))
        self.cb_scope = QComboBox()
        self.cb_scope.addItems(["The whole model", "Inside the selected objects", "Only the selected copies"])
        self.cb_scope.setToolTip(EDDY_TIPS["look in"])
        r.addWidget(self.cb_scope, 1)
        v.addLayout(r)

        # fit options, folded away until wanted
        self.b_fit = QPushButton()
        self.b_fit.setCheckable(True)
        self.b_fit.setFlat(True)
        self.b_fit.setStyleSheet("QPushButton { text-align: left; }")
        self.b_fit.setToolTip("How the detail part sits on each marker. Usually nothing to change here.")
        v.addWidget(self.b_fit)
        self.fit_box = QWidget()
        f3 = QFormLayout(self.fit_box)
        f3.setContentsMargins(16, 0, 0, 0)
        self.cb_how = QComboBox()
        for _k, label, tip in LINE_UP:
            self.cb_how.addItem(label)
            self.cb_how.setItemData(self.cb_how.count() - 1, tip, _TIP_ROLE)
        self.cb_how.setCurrentIndex(self.state['how'])
        f3.addRow("Line up:", self.cb_how)
        self.sp_turn = QDoubleSpinBox()
        self.sp_turn.setRange(-360.0, 360.0)
        self.sp_turn.setDecimals(1)
        self.sp_turn.setSuffix(" °")
        self.sp_turn.setValue(self.state['turn'])
        f3.addRow("Turn:", self.sp_turn)
        self.ck_flip = QCheckBox("Flip it over")
        self.ck_flip.setChecked(self.state['flip'])
        f3.addRow(self.ck_flip)
        self.ck_scale = QCheckBox("Scale with the marker")
        self.ck_scale.setChecked(self.state['scale'])
        f3.addRow(self.ck_scale)
        v.addWidget(self.fit_box)

        def fold(on):
            self.fit_box.setVisible(on)
            self.b_fit.setText(("▾" if on else "▸") + "  Fit options")
            self.state['fit_open'] = on
        self.b_fit.toggled.connect(fold)
        self.b_fit.setChecked(self.state.get('fit_open', False))
        fold(self.state.get('fit_open', False))
        v.addStretch(1)

        self.cb_scope.currentIndexChanged.connect(self.update_counts)
        return page

    def _make_page(self):
        from PySide6.QtWidgets import QListWidget, QInputDialog
        self._QInputDialog = QInputDialog
        self.lib = load_library()
        page = QWidget()
        v = QVBoxLayout(page)

        # the tabs of parts, with buttons to add, rename and delete tabs
        top = QHBoxLayout()
        self.part_tabs = QTabWidget()
        self.part_tabs.setDocumentMode(True)
        self.part_tabs.setMovable(True)
        top.addWidget(self.part_tabs, 1)
        v.addLayout(top)
        trow = QHBoxLayout()
        for text, fn, tip in (("+ New tab", self.tab_new, "Adds a tab of your own - Smokebox, Tender, "
                                                          "Wagon strapping..."),
                              ("Rename tab", self.tab_rename, "Renames the tab you're on."),
                              ("Delete tab", self.tab_delete, "Deletes the tab you're on and the parts in "
                                                              "it (not the copies in your model).")):
            b = QPushButton(text)
            b.setToolTip(tip)
            b.clicked.connect(fn)
            trow.addWidget(b)
        trow.addStretch(1)
        v.addLayout(trow)
        self.part_lists = []
        for t in self.lib["tabs"]:
            self._add_tab_page(t)
        self.part_tabs.tabBar().tabMoved.connect(self._tab_moved)
        self.part_tabs.currentChanged.connect(lambda *_: self._part_picked())

        # what to do with the part picked
        act = QHBoxLayout()
        self.b_place = QPushButton("Place it")
        self.b_place.setToolTip(EDDY_TIPS["place it"])
        self.b_place.clicked.connect(self.part_place)
        self.b_as_light = QPushButton("Use as light")
        self.b_as_light.setToolTip(EDDY_TIPS["use as light"])
        self.b_as_light.clicked.connect(lambda: self.part_use(light=True))
        self.b_as_detail = QPushButton("Use as detail")
        self.b_as_detail.setToolTip(EDDY_TIPS["use as detail"])
        self.b_as_detail.clicked.connect(lambda: self.part_use(light=False))
        for b in (self.b_place, self.b_as_light, self.b_as_detail):
            act.addWidget(b)
        v.addLayout(act)
        act2 = QHBoxLayout()
        self.b_add_sel = QPushButton("Add selected component to this tab")
        self.b_add_sel.setToolTip(EDDY_TIPS["add selected component to this tab"])
        self.b_add_sel.clicked.connect(self.part_add_selected)
        self.b_remove = QPushButton("Remove from tab")
        self.b_remove.setToolTip("Takes the part out of this tab (copies already in your model stay).")
        self.b_remove.clicked.connect(self.part_remove)
        act2.addWidget(self.b_add_sel)
        act2.addStretch(1)
        act2.addWidget(self.b_remove)
        v.addLayout(act2)

        # making or changing a part from a shape
        box = QGroupBox("Shape and sizes")
        form = QFormLayout(box)
        self.cb_shape = QComboBox()
        for _k, label, tip in SHAPES:
            self.cb_shape.addItem(label)
            self.cb_shape.setItemData(self.cb_shape.count() - 1, tip, _TIP_ROLE)
        form.addRow("Shape:", self.cb_shape)
        self.size_boxes = {}
        self.size_rows = {}
        for key, label in (('af', "Across flats:"), ('d', "Diameter:"), ('h', "Height:"),
                           ('shank', "Shank length:"), ('shank_d', "Shank diameter:"),
                           ('washer_d', "Washer diameter:"), ('washer_t', "Washer thickness:"),
                           ('bolt_d', "Bolt diameter:"), ('end', "Bolt end:")):
            sp = QDoubleSpinBox()
            sp.setRange(0.0, 10000.0)
            sp.setDecimals(1)
            sp.setSuffix(" mm")
            lab = QLabel(label)
            form.addRow(lab, sp)
            self.size_boxes[key] = sp
            self.size_rows[key] = (lab, sp)
        self.sp_sides = QSpinBox()
        self.sp_sides.setRange(6, 64)
        self.sp_sides.setValue(12)
        lab = QLabel("Sides:")
        form.addRow(lab, self.sp_sides)
        self.size_rows['sides'] = (lab, self.sp_sides)
        self.ed_name = QLineEdit()
        form.addRow("Name:", self.ed_name)
        self.lbl_comp = QLabel("")
        self.lbl_comp.setWordWrap(True)
        form.addRow(self.lbl_comp)
        brow = QHBoxLayout()
        self.b_save_new = QPushButton("Add as new part")
        self.b_save_new.setToolTip(EDDY_TIPS["add as new part"])
        self.b_save_new.clicked.connect(lambda: self.part_save(new=True))
        self.b_save_over = QPushButton("Save changes")
        self.b_save_over.setToolTip(EDDY_TIPS["save changes"])
        self.b_save_over.clicked.connect(lambda: self.part_save(new=False))
        brow.addStretch(1)
        brow.addWidget(self.b_save_new)
        brow.addWidget(self.b_save_over)
        form.addRow(brow)
        v.addWidget(box)
        self._shape_box = box
        self._shape_defaults = {
            'marker': dict(af=30.0, h=2.0),
            'rivet': dict(d=33.0, h=13.0, shank=0.0, shank_d=19.0),
            'bolt': dict(af=32.0, h=13.0, washer_d=45.0, washer_t=0.0),
            'nut': dict(af=32.0, h=16.0, washer_d=45.0, washer_t=3.0, bolt_d=19.0, end=8.0),
        }
        self.cb_shape.currentIndexChanged.connect(self.shape_changed)
        self.shape_changed(0)
        i = min(self.state.get('part_tab', 0), self.part_tabs.count() - 1)
        self.part_tabs.setCurrentIndex(max(0, i))
        self._part_picked()
        return page

    # -------------------------------------------------------------- the parts library
    def _add_tab_page(self, t):
        from PySide6.QtWidgets import QListWidget
        lst = QListWidget()
        lst.setToolTip("The parts in this tab. Double-click one to place it.")
        _icon_grid(lst)
        for e in t["parts"]:
            self._add_part_item(lst, e)
        lst.currentRowChanged.connect(lambda *_: self._part_picked())
        lst.itemDoubleClicked.connect(lambda *_: self.part_place())
        self.part_tabs.addTab(lst, t["name"])
        self.part_lists.append(lst)

    def _add_part_item(self, lst, e):
        from PySide6.QtWidgets import QListWidgetItem
        it = QListWidgetItem(self._entry_label(e))
        try:
            icon = part_icon(build_definition(e))
            if icon is not None:
                it.setIcon(icon)
        except Exception:
            pass
        lst.addItem(it)

    def _entry_label(self, e):
        if e.get("kind") == "shape":
            what = dict((k, lab) for k, lab, _t in SHAPES).get(e.get("shape"), "")
            sz = e.get("sizes") or {}
            main = sz.get('af') if e.get("shape") != "rivet" else sz.get('d')
            return "%s\n%s mm" % (e["name"], ("%g" % main) if main else "?")
        return "%s\n%d faces" % (e["name"], len(e.get("faces") or []))

    def _tab_moved(self, a, b):
        tabs = self.lib["tabs"]
        tabs.insert(b, tabs.pop(a))
        self.part_lists.insert(b, self.part_lists.pop(a))
        self._save_lib()

    def _save_lib(self):
        err = save_library(self.lib)
        if err:
            self.report("Couldn't save the parts library: %s" % err, True)

    def _cur(self):
        """(tab index, part index, part) for the part picked, or (tab, -1, None)."""
        ti = self.part_tabs.currentIndex()
        if ti < 0:
            return -1, -1, None
        pi = self.part_lists[ti].currentRow()
        parts = self.lib["tabs"][ti]["parts"]
        return ti, pi, (parts[pi] if 0 <= pi < len(parts) else None)

    def _part_picked(self):
        if not hasattr(self, 'b_save_over'):
            return
        ti, _pi, e = self._cur()
        self.state['part_tab'] = max(0, ti)
        for b in (self.b_place, self.b_as_light, self.b_as_detail, self.b_remove):
            b.setEnabled(e is not None)
        self.b_save_over.setEnabled(e is not None)
        if e is None:
            return
        self.ed_name.setText(e.get("name", ""))
        if e.get("kind") == "shape":
            keys = [k for k, _l, _t in SHAPES]
            self.cb_shape.setEnabled(True)
            self.cb_shape.blockSignals(True)
            self.cb_shape.setCurrentIndex(keys.index(e["shape"]) if e.get("shape") in keys else 0)
            self.cb_shape.blockSignals(False)
            self._show_sizes(e.get("shape"), e.get("sizes") or {}, e.get("sides", 12))
            self.lbl_comp.setText("")
        else:
            self.lbl_comp.setText("Picked: your own component, %d faces - only its name can be changed "
                                  "(Save changes). The shape above is for making new parts."
                                  % len(e.get("faces") or []))

    def _show_sizes(self, shape, sizes, sides):
        uses = {
            'marker': ('af', 'h'),
            'rivet': ('d', 'h', 'shank', 'shank_d', 'sides'),
            'bolt': ('af', 'h', 'washer_d', 'washer_t', 'sides'),
            'nut': ('af', 'h', 'washer_d', 'washer_t', 'bolt_d', 'end', 'sides'),
        }.get(shape, ())
        for key, (lab, w) in self.size_rows.items():
            lab.setVisible(key in uses)
            w.setVisible(key in uses)
        for key, val in sizes.items():
            if key in self.size_boxes:
                self.size_boxes[key].setValue(float(val))
        self.sp_sides.setValue(int(sides))

    def shape_changed(self, i, first=False):
        shape = SHAPES[i][0]
        self._show_sizes(shape, self._shape_defaults[shape], self.sp_sides.value())
        self.lbl_comp.setText("")

    def tab_new(self, *_):
        name, ok = self._QInputDialog.getText(self, PLUGIN_NAME, "Name for the new tab:")
        name = (name or "").strip()
        if not ok or not name:
            return
        t = {"name": name, "parts": []}
        self.lib["tabs"].append(t)
        self._add_tab_page(t)
        self.part_tabs.setCurrentIndex(self.part_tabs.count() - 1)
        self._save_lib()
        self.report("Added the tab %s. Make a part below, or select a component in the model and press "
                    "Add selected component to this tab." % name)

    def tab_rename(self, *_):
        ti = self.part_tabs.currentIndex()
        if ti < 0:
            return
        name, ok = self._QInputDialog.getText(self, PLUGIN_NAME, "New name for the tab:",
                                              text=self.lib["tabs"][ti]["name"])
        name = (name or "").strip()
        if not ok or not name:
            return
        self.lib["tabs"][ti]["name"] = name
        self.part_tabs.setTabText(ti, name)
        self._save_lib()

    def tab_delete(self, *_):
        ti = self.part_tabs.currentIndex()
        if ti < 0:
            return
        t = self.lib["tabs"][ti]
        if self.part_tabs.count() == 1:
            self.report("That's the last tab - add another before deleting this one.", True)
            return
        if t["parts"] and QMessageBox.question(
                self, PLUGIN_NAME, "Delete the tab %s and the %d parts in it?\n(Copies already in your "
                "model stay.)" % (t["name"], len(t["parts"]))) != QMessageBox.StandardButton.Yes:
            return
        self.lib["tabs"].pop(ti)
        self.part_lists.pop(ti)
        self.part_tabs.removeTab(ti)
        self._save_lib()

    def _sizes_from_boxes(self):
        return {k: round(sp.value(), 3) for k, sp in self.size_boxes.items()}

    def part_save(self, new=True):
        ti, pi, e = self._cur()
        if ti < 0:
            return
        name = self.ed_name.text().strip()
        if not new and e is not None and e.get("kind") != "shape":
            if name:
                e["name"] = name
        else:
            shape = SHAPES[self.cb_shape.currentIndex()][0]
            data = _shape_part(name or dict((k, l) for k, l, _t in SHAPES)[shape], shape,
                               self.sp_sides.value(), **self._sizes_from_boxes())
            bad = entry_check(data)
            if bad:
                self.report(bad, True)
                return
            if new or e is None:
                self.lib["tabs"][ti]["parts"].append(data)
                self._add_part_item(self.part_lists[ti], data)
                self.part_lists[ti].setCurrentRow(self.part_lists[ti].count() - 1)
                self._save_lib()
                self.report("Added %s to %s." % (data["name"], self.lib["tabs"][ti]["name"]))
                return
            changed = (e.get("shape") != data["shape"] or e.get("sizes") != data["sizes"]
                       or int(e.get("sides", 12)) != data["sides"])
            e.update(name=data["name"], shape=data["shape"], sizes=data["sizes"], sides=data["sides"])
            if changed:
                e["id"] = _new_id()        # new sizes: a new part, so copies already placed aren't mixed up with it
        it = self.part_lists[ti].item(pi)
        it.setText(self._entry_label(e))
        try:
            icon = part_icon(build_definition(e))
            if icon is not None:
                it.setIcon(icon)
        except Exception:
            pass
        self._save_lib()
        self.report("Saved %s." % e["name"])

    def part_remove(self, *_):
        ti, pi, e = self._cur()
        if e is None:
            return
        self.lib["tabs"][ti]["parts"].pop(pi)
        self.part_lists[ti].takeItem(pi)
        self._save_lib()
        self.report("Took %s out of the tab." % e["name"])

    def _picked_model_part(self):
        """The part picked in the model (selected) or, failing that, clicked in the Components tray."""
        gs = self.selected_groups()
        if gs:
            return gs[0]
        return self._picked_row_part() or self._tray_pick()

    def part_add_selected(self, *_):
        ti = self.part_tabs.currentIndex()
        g = self._picked_model_part()
        if ti < 0 or g is None:
            self.report("Select a component in the model, or click one in the list on the Light / detail "
                        "tab, first.", True)
            return
        try:
            faces, colours = capture_definition(g)
        except Exception as e:
            self.report("Couldn't read that part: %s" % e, True)
            return
        if not faces:
            self.report("That part has no faces to save.", True)
            return
        if len(faces) > 20000:
            self.report("That part has %s faces - too big for the parts library." % _fmt_faces(len(faces)), True)
            return
        e = dict(id=_new_id(), kind="mesh", name=str(getattr(g, 'name', '') or "Part"), faces=faces)
        if colours:
            e["colours"] = colours
        self.lib["tabs"][ti]["parts"].append(e)
        self._add_part_item(self.part_lists[ti], e)
        self.part_lists[ti].setCurrentRow(self.part_lists[ti].count() - 1)
        self._save_lib()
        self.report("Added %s (%d faces) to %s. It's there in every model from now on." % (
            e["name"], len(faces), self.lib["tabs"][ti]["name"]))

    def _definition_for(self, e, place_matrix=None):
        """The model's definition of library part e - found, or put in the file as a kept
        component (one Undo). Returns its key in self.parts, or None."""
        self.refresh()
        k = entry_in_model(e, self.parts)
        if k is not None:
            return k
        bad = entry_check(e)
        if bad:
            self.report(bad, True)
            return None
        try:
            tpl = build_definition(e)
        except Exception as ex:
            self.report("Couldn't make %s: %s" % (e.get("name"), ex), True)
            return None
        h = self.viewport.history
        h.execute(AddKeptCommand([tpl]))
        if getattr(h, 'last_error', None):
            self.report("Couldn't add it: %s" % h.last_error, True)
            return None
        self._changed()
        self.refresh()
        return part_key(tpl)

    def part_use(self, light=True):
        _ti, _pi, e = self._cur()
        if e is None:
            return
        k = self._definition_for(e)
        if k is None:
            return
        self.tabs.setCurrentIndex(0)
        self.set_part(light=light, key=k)

    def part_place(self, *_):
        _ti, _pi, e = self._cur()
        if e is None:
            return
        k = self._definition_for(e)
        p = self.parts.get(k) if k is not None else None
        if p is None:
            return
        rep = p['copies'][0] if p['copies'] else (p.get('kept') or p['rep'])
        try:
            g = _copy_group(rep)
            box = local_box(rep)
            a = anchor(box, "base")
            x = m_mul(m_mul(self.place_on_selected_face(), m_trans(-a[0], -a[1], -a[2])), m_inv(axes_of(rep)))
            g.xform = m_to_q(x)
            g.component = True
            g.layer, g.hidden, g.locked, g.material = None, False, False, None
            try:
                from core.history import InsertGroupCommand
                cmd = InsertGroupCommand(g)
            except ImportError:
                from core.history import SnapshotImport
                cmd = SnapshotImport(lambda s: s.groups.append(g))
            h = self.viewport.history
            h.execute(cmd)
            if getattr(h, 'last_error', None):
                raise RuntimeError(h.last_error)
        except Exception as ex:
            self.report("Couldn't place it: %s" % ex, True)
            return
        self._changed()
        self.refresh()
        self.report("Placed %s, selected. Copy it to each spot - Move with Ctrl - and every copy shares it."
                    % e["name"])
    # -------------------------------------------------------------- reading the model
    def scene(self):
        return getattr(self.viewport, 'scene', None)

    def selection(self):
        sc = self.scene()
        return list(getattr(sc, 'selection', None) or [])

    def selected_groups(self):
        return [e for e in self.selection() if getattr(e, 'mesh', None) is not None
                and not hasattr(e, 'loop') and 'face' not in type(e).__name__.lower()]

    def refresh(self, *_):
        sc = self.scene()
        _BOUNDS.clear()
        if sc is None:
            self.parts = {}
        else:
            try:
                self.parts = scan(sc)
            except Exception as e:
                self.parts = {}
                self.report("Couldn't read the model: %s" % e, True)
        order = sorted(self.parts.items(), key=lambda kv: (-len(kv[1]['copies']), kv[1]['name'].lower()))
        # the parts library too, so a marker is never lost: one not in the model is put back from it
        lib_rows = []
        for t in getattr(self, 'lib', {}).get("tabs", []):
            for e in t["parts"]:
                if entry_in_model(e, self.parts) is None:
                    k = "lib:" + e["id"]
                    lib_rows.append((k, dict(name=e["name"], copies=[], kind="library", rep=None,
                                             entry=e, tab=t["name"])))
        for k, p in lib_rows:
            self.parts[k] = p
        keep_l = self._refind(self.light_key, 'light')
        keep_d = self._refind(self.detail_key, 'detail')
        if keep_d == keep_l:
            keep_d = None
        self.light_key, self.detail_key = keep_l, keep_d
        for k, which in ((keep_l, 'light'), (keep_d, 'detail')):
            if k in self.parts:
                self._sig[which] = (self.parts[k]['name'], self._faces_of(self.parts[k]))
        cur = self.comp_list.currentRow()
        cur_key = self._row_keys[cur] if 0 <= cur < len(getattr(self, '_row_keys', [])) else None
        self.comp_list.blockSignals(True)
        self.comp_list.clear()
        self._row_keys = []
        from PySide6.QtWidgets import QListWidgetItem
        from PySide6.QtGui import QColor, QBrush
        for k, p in order:
            n = len(p['copies'])
            label = "%s\n%s" % (p['name'], ("%d placed" % n) if n else "none placed")
            if k == keep_l:
                label += "\nLIGHT"
            elif k == keep_d:
                label += "\nDETAIL"
            it = QListWidgetItem(label)
            icon = part_icon(p['copies'][0] if p['copies'] else (p.get('kept') or p['rep']))
            if icon is not None:
                it.setIcon(icon)
            if k == keep_l:
                it.setBackground(QBrush(QColor(210, 232, 255)))
            elif k == keep_d:
                it.setBackground(QBrush(QColor(255, 226, 200)))
            it.setToolTip("%s - %s. Right-click to set it as the light or detail part." % (
                p['name'], ("%d placed" % n) if n else "kept in the file, none placed"))
            self.comp_list.addItem(it)
            self._row_keys.append(k)
        if cur_key in self._row_keys:
            self.comp_list.setCurrentRow(self._row_keys.index(cur_key))
        self.comp_list.blockSignals(False)
        if not order:
            self.comp_list.addItem("No components yet -\nplace a marker and a\nrivet from the Parts tab.")
        self._comp_row()
        self.update_counts()

    def _comp_menu(self, pos):
        from PySide6.QtWidgets import QMenu
        it = self.comp_list.itemAt(pos)
        if it is None:
            return
        self.comp_list.setCurrentItem(it)
        m = QMenu(self.comp_list)
        m.addAction("Set as light part", lambda: self.set_part(light=True))
        m.addAction("Set as detail part", lambda: self.set_part(light=False))
        m.exec(self.comp_list.viewport().mapToGlobal(pos))

    def _faces_of(self, p):
        if p.get('entry') is not None:
            return len(entry_polys(p['entry']))
        return face_count(p['rep'])

    def _refind(self, key, which):
        """The light or detail part again after the model changed: by its key, else the same name
        and face count in the model, else the same name in the parts library."""
        if key in self.parts:
            return key
        sig = self._sig.get(which)
        if not sig:
            return None
        name, faces = sig
        for k, p in self.parts.items():
            if p['name'] == name and p['kind'] != "library" and self._faces_of(p) == faces:
                return k
        for k, p in self.parts.items():
            if p['name'] == name and p['kind'] == "library":
                return k
        return None

    def _comp_row(self, *_):
        r = self.comp_list.currentRow()
        ok = 0 <= r < len(getattr(self, '_row_keys', []))
        self.b_set_light.setEnabled(ok)
        self.b_set_detail.setEnabled(ok)

    def _picked_row_part(self):
        r = self.comp_list.currentRow()
        keys = getattr(self, '_row_keys', [])
        if 0 <= r < len(keys) and keys[r] in self.parts and self.parts[keys[r]]['kind'] != "library":
            p = self.parts[keys[r]]
            return p['copies'][0] if p['copies'] else (p.get('kept') or p['rep'])
        return None

    def set_part(self, light=True, key=None):
        if key is None:
            r = self.comp_list.currentRow()
            keys = getattr(self, '_row_keys', [])
            if not 0 <= r < len(keys):
                self.report("Click a component in the list first.", True)
                return
            key = keys[r]
        if light:
            self.light_key = key
            if self.detail_key == key:
                self.detail_key = None
        else:
            self.detail_key = key
            if self.light_key == key:
                self.light_key = None
        self.refresh()
        p = self.parts.get(key)
        if p:
            self.report("%s is now the %s part." % (p['name'], "light" if light else "detail"))

    def _in_scope(self, copies):
        scope = self.cb_scope.currentIndex()
        if scope == 1:
            outer = self.selected_groups()
            return [g for g in copies if any(g is not o and is_inside(g, o) for o in outer)]
        if scope == 2:
            sel = {id(e) for e in self.selection()}
            return [g for g in copies if id(g) in sel]
        return list(copies)

    def update_counts(self, *_):
        L = self.parts.get(self.light_key)
        D = self.parts.get(self.detail_key)
        def show(p):
            if not p:
                return "<i>not set</i>"
            return "<b>%s</b>%s" % (p['name'], "  (from the parts library)" if p['kind'] == "library" else "")
        self.lbl_light.setText(show(L))
        self.lbl_detail.setText(show(D))
        same = L is not None and L is D
        nl = len(self._in_scope(L['copies'])) if L else 0
        nd = len(self._in_scope(back_to_light(D['copies'], L['name']))) if (D and L) else 0
        stay = (len(self._in_scope(D['copies'])) - nd) if (D and L) else 0
        ln, dn = (L['name'] if L else "?"), (D['name'] if D else "?")
        arrow = "  →  "
        self.b_detail.setText("Show detail:   %d %s%s%s" % (nl, ln, arrow, dn))
        self.b_light.setText("Go light:   %d %s%s%s" % (nd, dn, arrow, ln))
        self.b_light.setToolTip(EDDY_TIPS["go light"] + (
            "\n\n%d %s placed by hand (not swapped in) will stay as they are." % (stay, dn) if stay > 0 else ""))
        self.b_detail.setEnabled(bool(L and D) and not same and nl > 0)
        self.b_light.setEnabled(bool(L and D) and not same and nd > 0)
        if not L or not D:
            self.lbl_faces.setText("Click a component in the list and Set as light part, then another "
                                   "and Set as detail part.")
            return
        if same:
            self.lbl_faces.setText("The light and detail parts are the same - choose a different one.")
            return
        fl, fd = self._faces_of(L), self._faces_of(D)
        n = nl + nd
        if nl == 0 and nd == 0:
            self.lbl_faces.setText("Neither part has copies placed%s." % (
                "" if self.cb_scope.currentIndex() == 0 else " where 'Look in' is looking"))
            return
        if fl is not None and fd is not None and n:
            self.lbl_faces.setText("All %d light: %s faces.   All %d with detail: %s faces." % (
                n, _fmt_faces(fl * n), n, _fmt_faces(fd * n)))
        else:
            self.lbl_faces.setText("")

    # -------------------------------------------------------------- the swap
    def _remember(self):
        self.state.update(how=self.cb_how.currentIndex(), turn=self.sp_turn.value(),
                          flip=self.ck_flip.isChecked(), scale=self.ck_scale.isChecked(),
                          )

    def swap(self, to_detail=True):
        try:
            self._swap(to_detail)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.report("Couldn't change them: %s" % e, True)
            QMessageBox.warning(self, PLUGIN_NAME, "Couldn't change them:\n%s" % e)

    def _swap(self, to_detail):
        self._remember()
        sc = self.scene()
        L = self.parts.get(self.light_key)
        D = self.parts.get(self.detail_key)
        if sc is None or not L or not D or L is D:
            self.report("Choose a light part and a different detail part.", True)
            return
        for which in ('light', 'detail'):
            p = L if which == 'light' else D
            if p['kind'] == "library":
                k = self._definition_for(p['entry'])          # puts it in the file, kept
                if k is None:
                    return
                setattr(self, which + '_key', k)
        L = self.parts.get(self.light_key)
        D = self.parts.get(self.detail_key)
        if not L or not D or L is D:
            self.report("Couldn't find the light and detail parts in the model.", True)
            return
        old, new = (L, D) if to_detail else (D, L)
        source = new['copies'][0] if new['copies'] else new.get('kept') or new['rep']
        pool = old['copies'] if to_detail else back_to_light(old['copies'], L['name'])
        targets = [g for g in self._in_scope(pool) if not getattr(g, 'locked', False)]
        targets = [g for g in targets if g is not source and not is_inside(source, g)]
        if not targets:
            self.report("Nothing to change.", True)
            return
        how = LINE_UP[self.cb_how.currentIndex()][0]
        src_box, src_axes = local_box(source), axes_of(source)
        xforms = [placement_for(frame_of(g), local_box(g), src_axes, src_box, how,
                                self.sp_turn.value(), self.ck_flip.isChecked(),
                                self.ck_scale.isChecked(), reverse=not to_detail)
                  for g in targets]
        # the part going out stays in the file, so the other button can bring it back
        keep = []
        if len(targets) == len(old['copies']) and not old.get('kept'):
            try:
                from core.kept_components import kept_template
                if not (getattr(old['rep'], 'xform', None) is not None
                        and kept_template(sc, old['rep'].mesh) is not None):
                    keep = [old['rep']]
            except Exception:
                keep = [old['rep']]
        busy = len(targets) > 300
        if busy:
            try:
                from PySide6.QtWidgets import QApplication
                from PySide6.QtCore import Qt
                QApplication.setOverrideCursor(Qt.WaitCursor)
            except Exception:
                busy = False
        cmd = SwapPartsCommand(targets, xforms, source, keep,
                               tag={"light": L['name']} if to_detail else None)
        try:
            h = self.viewport.history
            h.execute(cmd)
            err = getattr(h, 'last_error', None) or getattr(h, 'last_rejected', None)
        finally:
            if busy:
                from PySide6.QtWidgets import QApplication
                QApplication.restoreOverrideCursor()
        if err:
            self.report("Couldn't change them: %s" % err, True)
            return
        self._changed()
        new_k = part_key(source)
        old_k = part_key(cmd._templates[0]) if cmd._templates else part_key(old['rep'])
        self.light_key, self.detail_key = (old_k, new_k) if to_detail else (new_k, old_k)
        self.refresh()
        msg = "Changed %d %s into %s. One Undo puts them back." % (len(targets), old['name'], new['name'])
        self.report(msg)
        try:
            self.viewport.window().statusBar().showMessage(msg, 6000)
        except Exception:
            pass

    # -------------------------------------------------------------- the Components tray
    def _tray_pick(self):
        d = _TRAY.get('def')
        return d if d is not None and getattr(d, 'mesh', None) is not None else None
    def place_on_selected_face(self):
        """Standing on the centre of the selected face(s), its up (Z) out of the face; else the origin."""
        faces = [e for e in self.selection() if hasattr(e, 'loop') or 'face' in type(e).__name__.lower()]
        best = None
        for f in faces:
            pts = []
            for vx in list(getattr(f, 'vertices', None) or []):
                q = getattr(vx, 'position', vx)
                try:
                    pts.append((float(q.x()), float(q.y()), float(q.z())))
                except Exception:
                    pass
            if len(pts) < 3:
                continue
            nx = ny = nz = 0.0
            for i in range(len(pts)):
                a, b = pts[i], pts[(i + 1) % len(pts)]
                nx += (a[1] - b[1]) * (a[2] + b[2])
                ny += (a[2] - b[2]) * (a[0] + b[0])
                nz += (a[0] - b[0]) * (a[1] + b[1])
            area = math.sqrt(nx * nx + ny * ny + nz * nz)
            if best is None or area > best[0]:
                c = tuple(sum(p[k] for p in pts) / len(pts) for k in range(3))
                best = (area, c, (nx, ny, nz))
        if best is None or best[0] < 1e-18:
            return m_ident()
        _a, c, n = best
        z = _unit(n)
        # keep the part's red axis level where it can be: along the face, square to straight up
        x = _unit(_cross((0.0, 0.0, 1.0), z)) or (1.0, 0.0, 0.0)
        y = _cross(z, x)
        return m_frame(c, x, y, z)

    # -------------------------------------------------------------- odds and ends
    def report(self, text, bad=False):
        self.lbl_report.setStyleSheet("color: %s;" % ("#b35900" if bad else "#2e7d32"))
        self.lbl_report.setText(text)

    def _changed(self):
        for name in ('notify_scene_changed', 'update'):
            try:
                getattr(self.viewport, name)()
            except Exception:
                pass

    def closeEvent(self, ev):
        try:
            self._remember()
        except Exception:
            pass
        super().closeEvent(ev)


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
class FindReplaceTool(Tool):
    name = PLUGIN_NAME
    shortcut = "Ctrl+Alt+X"
    description = ("Swaps every copy of one part for another in one go - light hex markers for full "
                   "rivets or bolts and back - and makes markers, rivets and bolts to place.")
    _dialog = None

    def on_activate(self, viewport):
        dlg = FindReplaceTool._dialog
        if dlg is not None:
            try:
                if dlg.isVisible():
                    dlg.raise_()
                    dlg.activateWindow()
                    dlg.refresh()
                    return
            except Exception:
                pass
        dlg = FindReplaceDialog(viewport, self)
        FindReplaceTool._dialog = dlg

        def closed(*_):
            FindReplaceTool._dialog = None
        dlg.finished.connect(closed)
        eddy_window(dlg, PLUGIN_NAME, EDDY_TIPS, place=True)  # eddy-window
        dlg.show()

    def on_deactivate(self, viewport):
        pass


def run(viewport=None):
    FindReplaceTool().on_activate(viewport)
