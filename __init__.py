# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Original Author = Jacob Morris

bl_info = {
    "name": "JARCH Vis",
    "author": "Jacob Morris",
    "version": (2, 0, 0),
    "blender": (2, 80, 0),
    "location": "View 3D > Toolbar > JARCH Vis",
    "description": "Allows The Creation Of Architectural Objects Like Flooring, Siding, Stairs, Roofing, and Windows",
    "category": "Add Mesh"
}

if "bpy" in locals():
    import importlib

    modules = [
        jv_utils,
        jv_types,
        jv_properties,

        jv_builder_base,
        jv_flooring,
        jv_siding,
        jv_roofing,
        jv_windows,

        jv_operators,
        jv_panel
    ]

    for module in modules:
        importlib.reload(module)
else:
    from . import jv_utils
    from . import jv_types
    from . import jv_properties

    from . import jv_builder_base
    from . import jv_flooring
    from . import jv_siding
    from . import jv_roofing
    from . import jv_windows

    from . import jv_operators
    from . import jv_panel


import bpy


def register():
    jv_properties.register()
    jv_operators.register()
    jv_panel.register()


def unregister():
    jv_panel.unregister()
    jv_operators.unregister()
    jv_properties.unregister()


if __name__ == "__main__":
    register()
