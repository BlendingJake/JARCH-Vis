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
    "blender": (2, 78, 0),
    "location": "View 3D > Toolbar > JARCH Vis",
    "description": "Allows The Creation Of Architectural Objects Like Flooring, Siding, Stairs, Roofing, and Windows",
    "category": "Add Mesh"
}

if "bpy" in locals():
    import importlib

    importlib.reload(jv_operators)
    importlib.reload(jv_base)
    importlib.reload(jv_panel)

    importlib.reload(jv_flooring)
# else:
#     from . import jv_operators
#     from . import jv_base
#     from . import jv_panel
#
#     from . import jv_flooring

import jv_base
import jv_panel
import jv_operators
import jv_flooring


from bpy.types import Object, Menu, PropertyGroup
from bpy.props import StringProperty, IntProperty, FloatProperty, CollectionProperty
from bpy.utils import register_module
import bpy.types


class FaceGroup(PropertyGroup):
    data = StringProperty()
    num_faces = IntProperty()
    face_slope = FloatProperty()
    rot = FloatProperty(unit="ROTATION")


class CutoutGroup(PropertyGroup):
    x_dist = FloatProperty(subtype="DISTANCE")
    z_dist = FloatProperty(subtype="DISTANCE")
    width = FloatProperty(subtype="DISTANCE")
    height = FloatProperty(subtype="DISTANCE")


class INFO_MT_mesh_jv_menu_add(Menu):
    bl_idname = "INFO_MT_mesh_jv_menu_add"
    bl_label = "JARCH Vis"

    def draw(self, context):
        layout = self.layout       
        layout.operator("object.jv_flooring_add", text="Add Flooring", icon="MESH_GRID")


def menu_add(self, context):
    self.layout.menu("INFO_MT_mesh_jv_menu_add", icon="PLUGIN")


def register():
    register_module(__name__)
    register_module(jv_base)
    register_module(jv_panel)
    register_module(jv_operators)

    register_module(jv_flooring)

    bpy.types.INFO_MT_mesh_add.append(menu_add)
    # Object.jv_face_groups = CollectionProperty(type=FaceGroup)
    # Object.jv_cutout_groups = CollectionProperty(type=CutoutGroup)
    #
    # wm = bpy.context.window_manager
    # km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type="VIEW_3D")
    # km.keymap_items.new("mesh.jv_add_face_group_item", "A", "PRESS", ctrl=True)


def unregister():
    bpy.utils.unregister_module(__name__)
    # del Object.jv_face_groups
    # del Object.jv_cutout_groups
    #
    # wm = bpy.context.window_manager
    # if wm.keyconfigs.addon:
    #     for kmi in wm.keyconfigs.addon.keymaps['3D View'].keymap_items:
    #         if kmi.idname == "mesh.jv_add_face_group_item":
    #             wm.keyconfigs.addon.keymaps['3D View'].keymap_items.remove(kmi)


if __name__ == "__main__":
    register()
