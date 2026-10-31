# SPDX-License-Identifier: GPL-3.0-or-later
# Eddy's 3D plugins for IngeTrazo - all in one folder
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
Eddy's 3D plugins, kept together in their own folder (3D_Eddys) in IngeTrazo's plugins
folder, so they don't get mixed up with other people's plugins.

IngeTrazo loads a plugin folder by running this file. It loads every ed3d_*.py beside it and
hands IngeTrazo their tools, exactly as if each file sat in the plugins folder on its own. If
one of them fails to load, the others still load, and the reason is printed in IngeTrazo's log.

To leave a plugin out, rename its file so it no longer ends in .py (for example add .off).
"""

import importlib.util
import os
import sys
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))
LOADED, FAILED = [], []


def _load_all():
    try:
        from tools.base import Tool
    except Exception:
        Tool = None
    names = sorted(fn for fn in os.listdir(_HERE)
                   if fn.lower().startswith("ed3d_") and fn.lower().endswith(".py"))
    # the toolbar last, so every plugin it puts a button up for is there first
    names.sort(key=lambda fn: fn.lower() == "ed3d_plugins_toolbar.py")
    g = globals()
    for fn in names:
        stem = fn[:-3]
        modname = "%s_%s" % (__name__, stem)
        try:
            spec = importlib.util.spec_from_file_location(modname, os.path.join(_HERE, fn))
            mod = importlib.util.module_from_spec(spec)
            sys.modules[modname] = mod
            spec.loader.exec_module(mod)
        except Exception:
            sys.modules.pop(modname, None)
            FAILED.append((fn, traceback.format_exc()))
            print("3D_Eddys: could not load %s:\n%s" % (fn, FAILED[-1][1]))
            continue
        LOADED.append(stem)
        if Tool is None:
            continue
        for attr, obj in list(vars(mod).items()):
            if isinstance(obj, type) and obj is not Tool and getattr(obj, '__module__', None) == modname:
                try:
                    if issubclass(obj, Tool):
                        # IngeTrazo picks up the tools defined in this file: make each one count as ours
                        obj.__module__ = __name__
                        g[attr] = obj
                except Exception:
                    pass


_load_all()
