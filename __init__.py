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
    "version": (1, 0, 1),
    "blender": (2, 78, 0),
    "location": "View 3D > Toolbar > JARCH Vis",
    "description": "Allows The Creation Of Architectural Objects Like Flooring, Siding, Stairs, Roofing, and Windows",
    "category": "Add Mesh"
    }

if "bpy" in locals():
    import importlib

    importlib.reload(jv_properties)
    importlib.reload(jv_siding)
    importlib.reload(jv_flooring)
    importlib.reload(jv_stairs)
    importlib.reload(jv_roofing)
    importlib.reload(jv_windows)
else:
    from . import jv_properties
    from . import jv_siding
    from . import jv_flooring
    from . import jv_stairs
    from . import jv_roofing
    from . import jv_windows

import bpy
from bpy.props import StringProperty, CollectionProperty, IntProperty, FloatProperty


class FaceGroup(bpy.types.PropertyGroup):
    data = StringProperty()
    num_faces = IntProperty()
    face_slope = FloatProperty()
    rot = FloatProperty(unit="ROTATION")


class CutoutGroup(bpy.types.PropertyGroup):
    x_dist = FloatProperty(subtype="DISTANCE")
    z_dist = FloatProperty(subtype="DISTANCE")
    width = FloatProperty(subtype="DISTANCE")
    height = FloatProperty(subtype="DISTANCE")


class INFO_MT_mesh_jv_menu_add(bpy.types.Menu):
    bl_idname = "INFO_MT_mesh_jv_menu_add"
    bl_label = "JARCH Vis"

    def draw(self, context):
        layout = self.layout       
        layout.operator("mesh.jv_flooring_add", text="Add Flooring", icon="MESH_GRID")
        layout.operator("mesh.jv_roofing_add", text="Add Roofing", icon="LINCURVE")
        layout.operator("mesh.jv_siding_add", text="Add Siding", icon="UV_ISLANDSEL")
        layout.operator("mesh.jv_stairs_add", text="Add Stairs", icon="MOD_ARRAY")
        layout.operator("mesh.jv_window_add", text="Add Window", icon="OUTLINER_OB_LATTICE")


def menu_add(self, context):
    self.layout.menu("INFO_MT_mesh_jv_menu_add", icon="PLUGIN")


def register():
    bpy.utils.register_module(__name__)   
    bpy.types.INFO_MT_mesh_add.append(menu_add)
    bpy.types.Object.jv_face_groups = CollectionProperty(type=FaceGroup)
    bpy.types.Object.jv_cutout_groups = CollectionProperty(type=CutoutGroup)

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type="VIEW_3D")
    km.keymap_items.new("mesh.jv_add_face_group_item", "A", "PRESS", ctrl=True)


def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Object.jv_face_groups
    del bpy.types.Object.jv_cutout_groups

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        for kmi in wm.keyconfigs.addon.keymaps['3D View'].keymap_items:
            if kmi.bl_idname == "mesh.jv_add_face_group_item":
                wm.keyconfig.addon.keymaps['3D View'].keymap_items.remove(kmi)

if __name__ == "__main__":
    register()
