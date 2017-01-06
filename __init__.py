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
    "version": (0, 8, 3),
    "blender": (2, 76, 0),
    "location": "View 3D > Toolbar > JARCH Vis",
    "description": "Allows The Creation Of Architectural Objects Like Flooring, Siding, Stairs, and Roofing",
    "category": "Add Mesh"
    }

if "bpy" in locals():
    import importlib
    import jarch_siding
    import jarch_flooring
    import jarch_stairs
    import jarch_roofing

    importlib.reload(jarch_siding)
    importlib.reload(jarch_flooring)
    importlib.reload(jarch_stairs)
    importlib.reload(jarch_roofing)
else: 
    from . import jarch_siding
    from . import jarch_flooring
    from . import jarch_stairs
    from . import jarch_roofing

import bpy
from bpy.props import StringProperty, CollectionProperty, IntProperty, FloatProperty


class FaceGroup(bpy.types.PropertyGroup):
    data = StringProperty()
    num_faces = IntProperty()
    face_slope = FloatProperty()
    rot = FloatProperty(unit="ROTATION")


class INFO_MT_mesh_jarch_menu_add(bpy.types.Menu):
    bl_idname = "INFO_MT_mesh_jarch_menu_add"
    bl_label = "JARCH Vis"

    def draw(self, context):
        layout = self.layout       
        layout.operator("mesh.jarch_flooring_add", text="Add Flooring", icon="MESH_GRID")
        layout.operator("mesh.jarch_roofing_add", text="Add Roofing", icon="LINCURVE")
        layout.operator("mesh.jarch_siding_add", text="Add Siding", icon="UV_ISLANDSEL")
        layout.operator("mesh.jarch_stairs_add", text="Add Stairs", icon="MOD_ARRAY")


def menu_add(self, context):
    self.layout.menu("INFO_MT_mesh_jarch_menu_add", icon="PLUGIN")


def register():
    bpy.utils.register_module(__name__)   
    bpy.types.INFO_MT_mesh_add.append(menu_add)
    bpy.types.Object.face_groups = CollectionProperty(type=FaceGroup)


def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Object.face_groups
    
if __name__ == "__main__":
    register()
