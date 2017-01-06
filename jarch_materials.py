# This file is part of JARCH Vis
#
# JARCH Vis is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# JARCH Vis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with JARCH Vis.  If not, see <http://www.gnu.org/licenses/>.

from math import radians


# glossy / diffuse mix
def glossy_diffuse_material(bpy, dif_col, glos_col, rough, mix, name):
    mat = bpy.data.materials.new(name)

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    rgba = list(dif_col)
    rgba.append(1.0)
    mat.diffuse_color = dif_col
    g_rgba = list(glos_col)
    g_rgba.append(1.0)

    # shaders
    node = nodes["Diffuse BSDF"]
    node.location = -100, 400
    node.inputs[0].default_value = rgba
    node = nodes.new("ShaderNodeBsdfGlossy")
    node.name = "Glossy"
    node.inputs[1].default_value = rough
    node.inputs[0].default_value = g_rgba
    node.location = -100, 200
    node = nodes.new("ShaderNodeMixShader")
    node.name = "Mix"
    node.location = 100, 300
    node.inputs[0].default_value = mix

    links = [["Diffuse BSDF", 0, "Mix", 1], ["Glossy", 0, "Mix", 2], ["Mix", 0, "Material Output", 0]]

    for link in links:
        o = nodes[link[0]].outputs[link[1]]
        i = nodes[link[2]].inputs[link[3]]
        mat.node_tree.links.new(o, i)

    return mat


# wood
def image_material(bpy, im_scale, c_image, n_image, bump_amo, is_bump, name, is_gloss, glossy, mix, rotate, extra_rot):
    color_loaded, normal_loaded = False, False
    
    for i in bpy.data.images:
        if i.filepath == c_image and not color_loaded:
            col_im = i
            color_loaded = True  # check if color image already loaded
        elif i.filepath == n_image and not normal_loaded and is_bump:
            norm_im = i
            normal_loaded = True  # check if normal image already loaded
    
    if not color_loaded:  # load the images otherwise
        try:
            col_im = bpy.data.images.load(c_image)
        except RuntimeError:
            return None
    if not normal_loaded and is_bump:
        try:
            norm_im = bpy.data.images.load(n_image)
        except RuntimeError:
            return None

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    node = nodes.new("ShaderNodeTexCoord")
    node.location = -700, 0
    node.name = "uv_coords"
    node = nodes.new("ShaderNodeMapping")
    node.location = -500, 0
    node.name = "scale"
    node.scale = (im_scale, im_scale, im_scale)

    if rotate:
        node.rotation = (0.0, 0.0, radians(90))
    if extra_rot is not None:
        node.rotation = (0.0, 0.0, node.rotation[2] + radians(extra_rot))

    node = nodes.new("ShaderNodeTexImage")
    node.location = -100, 150
    node.name = "color_image"
    node.image = col_im
    node = nodes.new("ShaderNodeTexImage")
    node.location = -100, -150
    node.name = "normal_image"
    if is_bump:
        node.image = norm_im

    node = nodes["Diffuse BSDF"]
    node.location = 100, 100
    node.name = "diffuse"

    if is_gloss:
        node = nodes.new("ShaderNodeBsdfGlossy")
        node.location = 100, -50
        node.name = "glossy"
        node.inputs[1].default_value = glossy
        node = nodes.new("ShaderNodeMixShader")
        node.location = 300, 50
        node.name = "mix"
        node.inputs[0].default_value = mix

    node = nodes.new("ShaderNodeNormalMap")
    node.location = 100, -200
    node.name = "normal_map"
    node.inputs[0].default_value = bump_amo
    node = nodes.new("ShaderNodeMath")
    node.location = 300, -200
    node.name = "math"
    node.operation = "MULTIPLY"

    if is_bump:
        node.inputs[1].default_value = 1.0
    else:
        node.inputs[1].default_value = 0.0

    node = nodes["Material Output"]
    node.location = 500, 0
    links = [["uv_coords", 2, "scale", 0], ["scale", 0, "color_image", 0], ["scale", 0, "normal_image", 0],
             ["color_image", 0, "diffuse", 0], ["normal_image", 0, "normal_map", 1], ["normal_map", 0, "math", 0],
             ["math", 0, "Material Output", 2]]

    if is_gloss:
        links += [["diffuse", 0, "mix", 1], ["glossy", 0, "mix", 2], ["mix", 0, "Material Output", 0]]

    for link in links:
        o = nodes[link[0]].outputs[link[1]]
        i = nodes[link[2]].inputs[link[3]]
        mat.node_tree.links.new(o, i)

    return mat


def brick_material(bpy, color_style, color1, color2, color3, color_sharp, color_scale, bump_type, brick_bump,
                   bump_scale, name):

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes

    # color rgba
    c1l, c2l, c3l = list(color1), list(color2), list(color3)
    c1l.append(1.0)
    c2l.append(1.0)
    c3l.append(1.0)  # create rgba lists for the three colors
    mat.diffuse_color = color1

    # colors
    if color_style == "constant":  # add uv_coords if single color since it wouldn't get it otherwise
        nodes["Diffuse BSDF"].inputs[0].default_value = c1l
        if bump_type != "4": 
            node = nodes.new("ShaderNodeTexCoord")
            node.name = "uv_coords"
            node.location = -1700, 400

    elif color_style == "speckled":
        node = nodes.new("ShaderNodeTexCoord")
        node.name = "uv_coords"
        node.location = -1500, 200
        node = nodes.new("ShaderNodeMapping")
        node.name = "scale"
        node.location = -1300, 200
        node.scale = (color_scale * 2.0, color_scale * 2.0, color_scale * 2.0)
        node.label = "Color Scale"

        node = nodes.new("ShaderNodeTexNoise")
        node.name = "c_noise1"
        node.location = -1200, 400
        node.inputs[1].default_value = 2.0
        node = nodes.new("ShaderNodeTexNoise")
        node.name = "c_noise2"
        node.location = -1200, 600
        node = nodes.new("ShaderNodeMixRGB")
        node.name = "cn1|cn2"
        node.location = -1000, 475
        node = nodes.new("ShaderNodeBrightContrast")
        node.name = "color_vary"
        node.location = -850, 400
        node.inputs[2].default_value = color_sharp * 2.0
        node.label = "Color Sharpness"

        node = nodes.new("ShaderNodeRGB")
        node.name = "color1"
        node.location = -900, 50
        node.outputs[0].default_value = c1l
        node.label = "Color 1"
        node = nodes.new("ShaderNodeRGB")
        node.name = "color2"
        node.location = -900, 250
        node.outputs[0].default_value = c2l
        node.label = "Color 2"
        node = nodes.new("ShaderNodeMixRGB")
        node.name = "c1|c2"
        node.location = -700, 300
        node = nodes.new("ShaderNodeMixRGB")
        node.name = "c1Xc2"
        node.location = -700, 100
        node.blend_type = "MULTIPLY"

        node = nodes.new("ShaderNodeTexNoise")
        node.name = "c_noise3"
        node.location = -1000, 700
        node.inputs[1].default_value = 600.0
        node = nodes.new("ShaderNodeBrightContrast")
        node.name = "contrast"
        node.location = -800, 700
        node.inputs[2].default_value = 6.0
        node = nodes.new("ShaderNodeTexNoise")
        node.name = "c_noise4"
        node.location = -800, 575
        node.inputs[1].default_value = 1000.0
        node = nodes.new("ShaderNodeMixRGB")
        node.name = "con|cn4"
        node.location = -600, 600
        node.inputs[1].default_value = (0.0, 0.0, 0.0, 1.0)

        node = nodes.new("ShaderNodeBrightContrast")
        node.name = "contrast2"
        node.location = -400, 400
        node.inputs[2].default_value = 4.0
        node = nodes.new("ShaderNodeMixRGB")
        node.name = "final|"
        node.location = -200, 300

        links = [["uv_coords", 2, "scale", 0], ["uv_coords", 2, "c_noise3", 0], ["uv_coords", 2, "c_noise4", 0],
                 ["scale", 0, "c_noise1", 0], ["scale", 0, "c_noise2", 0], ["c_noise1", 1, "cn1|cn2", 2],
                 ["c_noise2", 1, "cn1|cn2", 1], ["cn1|cn2", 0, "color_vary", 0], ["color_vary", 0, "c1|c2", 0],
                 ["color1", 0, "c1|c2", 1], ["color2", 0, "c1|c2", 2], ["color1", 0, "c1Xc2", 1],
                 ["color2", 0, "c1Xc2", 2], ["c1|c2", 0, "final|", 1], ["c1Xc2", 0, "final|", 2],
                 ["c_noise3", 1, "contrast", 0], ["contrast", 0, "con|cn4", 0], ["c_noise4", 1, "con|cn4", 2],
                 ["con|cn4", 0, "contrast2", 0], ["contrast2", 0, "final|", 0], ["final|", 0, "Diffuse BSDF", 0]]
        for i in links:
            o = nodes[i[0]].outputs[i[1]]
            i = nodes[i[2]].inputs[i[3]]
            mat.node_tree.links.new(o, i)

    elif color_style == "multiple":
        node = nodes.new("ShaderNodeTexCoord")
        node.name = "uv_coords"
        node.location = -1100, 300
        node = nodes.new("ShaderNodeMapping")
        node.name = "scale"
        node.location = -925, 35
        node.scale = [color_scale for i in range(3)]
        node.label = "Color Scale"

        node = nodes.new("ShaderNodeTexNoise")
        node.name = "c_noise"
        node.location = -600, 600
        node.inputs[1].default_value = 4.0
        node = nodes.new("ShaderNodeBrightContrast")
        node.name = "color_vary"
        node.location = -400, 500
        node.inputs[2].default_value = color_sharp
        node.label = "Color Sharpness"
        node = nodes.new("ShaderNodeMixRGB")
        node.name = "c1|c2"
        node.location = -200, 450

        node = nodes.new("ShaderNodeRGB")
        node.name = "color1"
        node.location = -500, 175
        node.outputs[0].default_value = c1l
        node.label = "Color 1"
        node = nodes.new("ShaderNodeRGB")
        node.name = "color2"
        node.location = -500, 375
        node.outputs[0].default_value = c2l
        node.label = "Color 2"

        links = [["uv_coords", 2, "scale", 0], ["scale", 0, "c_noise", 0], ["c_noise", 1, "color_vary", 0],
                 ["color_vary", 0, "c1|c2", 0], ["color1", 0, "c1|c2", 2], ["color2", 0, "c1|c2", 1],
                 ["c1|c2", 0, "Diffuse BSDF", 0]]
        for i in links:
            o = nodes[i[0]].outputs[i[1]]
            i = nodes[i[2]].inputs[i[3]]
            mat.node_tree.links.new(o, i)

    elif color_style == "extreme":
        node = nodes.new("ShaderNodeTexCoord")
        node.name = "uv_coords"
        node.location = -1700, 400
        node = nodes.new("ShaderNodeMapping")
        node.name = "scale"
        node.location = -1500, 400
        node.scale = (color_scale, color_scale, color_scale)
        node.label = "Color Scale"

        node = nodes.new("ShaderNodeTexNoise")
        node.name = "c_noise"
        node.location = -1100, 600
        node.inputs[1].default_value = 10.0
        node = nodes.new("ShaderNodeRGB")
        node.name = "color3"
        node.location = -1150, 800
        node.outputs[0].default_value = c3l
        node.label = "Color 3"
        node = nodes.new("ShaderNodeRGB")
        node.name = "color2"
        node.location = -1050, 400
        node.outputs[0].default_value = c2l
        node.label = "Color 2"
        node = nodes.new("ShaderNodeRGB")
        node.name = "color1"
        node.location = -1050, 200
        node.outputs[0].default_value = c1l
        node.label = "Color 1"

        node = nodes.new("ShaderNodeBrightContrast")
        node.name = "c_v1"
        node.location = -900, 525
        node.inputs[2].default_value = color_sharp
        node.label = "Color Sharpness 1"
        node = nodes.new("ShaderNodeMixRGB")
        node.name = "c1|c2"
        node.location = -700, 400

        node = nodes.new("ShaderNodeTexNoise")
        node.name = "c_noise2"
        node.location = -900, 800
        node = nodes.new("ShaderNodeBrightContrast")
        node.name = "c_v2"
        node.location = -700, 700
        node.inputs[2].default_value = color_sharp * 1.25
        node.label = "Color Sharpness 2"
        node = nodes.new("ShaderNodeMixRGB")
        node.name = "c3|c2c1"
        node.location = -500, 600
        node = nodes.new("ShaderNodeTexNoise")
        node.name = "c_noise3"
        node.location = -600, 900
        node.inputs[1].default_value = 50.0

        node = nodes.new("ShaderNodeBrightContrast")
        node.name = "c_v3"
        node.location = -400, 800
        node.inputs[2].default_value = color_sharp * 1.25
        node.label = "Color Sharpness 3"
        node = nodes.new("ShaderNodeMixRGB")
        node.name = "c1|c2.2"
        node.location = -400, 400
        node = nodes.new("ShaderNodeMixRGB")
        node.name = "final|"
        node.location = -250, 600

        links = [["uv_coords", 2, "scale", 0], ["scale", 0, "c_noise", 0], ["scale", 0, "c_noise2", 0],
                 ["scale", 0, "c_noise3", 0], ["c_noise", 1, "c_v1", 0], ["c_v1", 0, "c1|c2", 0],
                 ["color1", 0, "c1|c2", 2], ["color2", 0, "c1|c2", 1], ["color1", 0, "c1|c2.2", 2],
                 ["color2", 0, "c1|c2.2", 1], ["color3", 0, "c3|c2c1", 1], ["c_noise2", 1, "c_v2", 0],
                 ["c_v2", 0, "c3|c2c1", 0], ["c1|c2", 0, "c3|c2c1", 2], ["c_noise3", 1, "c_v3", 0],
                 ["c_v3", 0, "final|", 0], ["c3|c2c1", 0, "final|", 2], ["c1|c2.2", 0, "final|", 1],
                 ["final|", 0, "Diffuse BSDF", 0]]
        for i in links:
            o = nodes[i[0]].outputs[i[1]]
            i = nodes[i[2]].inputs[i[3]]
            mat.node_tree.links.new(o, i)

    # BUMP ------------------------------------------------->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    if bump_type == "1":  # dimpled
        node = nodes.new("ShaderNodeMapping")
        node.name = "b_scale"
        node.location = -700, -100
        node.scale = (bump_scale, bump_scale, bump_scale)
        node.label = "Scale Amount"
        node.label = "Bump Scale"
        node = nodes.new("ShaderNodeTexNoise")
        node.name = "b_noise"
        node.location = -300, 0
        node.inputs[1].default_value = 400.0

        node = nodes.new("ShaderNodeTexNoise")
        node.name = "b_noise2"
        node.location = -300, -200
        node.inputs[1].default_value = 200.0
        node = nodes.new("ShaderNodeMixRGB")
        node.name = "bn|bn2"
        node.location = -100, -100
        node = nodes.new("ShaderNodeMath")
        node.name = "b_amount"
        node.location = 100, 0
        node.operation = "MULTIPLY"
        node.inputs[1].default_value = brick_bump
        node.label = "Bump Amount"

        links = [["uv_coords", 3, "b_scale", 0], ["b_scale", 0, "b_noise", 0], ["b_scale", 0, "b_noise2", 0],
                 ["b_noise", 1, "bn|bn2", 1], ["b_noise2", 1, "bn|bn2", 2], ["bn|bn2", 0, "b_amount", 0],
                 ["b_amount", 0, "Material Output", 2]]
        for i in links:
            o = nodes[i[0]].outputs[i[1]]
            i = nodes[i[2]].inputs[i[3]]
            mat.node_tree.links.new(o, i)

    elif bump_type == "2":  # ridges
        nodes = mat.node_tree.nodes
        node = nodes.new("ShaderNodeMapping")
        node.name = "b_scale"
        node.location = -800, -100
        node.rotation = (radians(-45.0), 0.0, 0.0)
        node.scale = (bump_scale, bump_scale, bump_scale)
        node.label = "Bump Scale"
        node = nodes.new("ShaderNodeTexWave")
        node.name = "b_wave"
        node.location = -400, 0
        node.inputs[1].default_value = 100.0
        node = nodes.new("ShaderNodeTexNoise")
        node.name = "b_noise"
        node.location = -400, -200
        node.inputs[1].default_value = 400.0
        node.inputs[3].default_value = 1.0

        node = nodes.new("ShaderNodeMixRGB")
        node.name = "bw|bn"
        node.location = -200, -100
        node.blend_type = "ADD"
        node.inputs[0].default_value = 1.0
        node = nodes.new("ShaderNodeMath")
        node.name = "b_amount"
        node.location = 100, 0
        node.operation = "MULTIPLY"
        node.inputs[1].default_value = brick_bump
        node.label = "Bump Amount"

        links = [["uv_coords", 2, "b_scale", 0], ["b_scale", 0, "b_noise", 0], ["b_scale", 0, "b_wave", 0],
                 ["b_noise", 1, "bw|bn", 2], ["b_wave", 1, "bw|bn", 1], ["bw|bn", 0, "b_amount", 0],
                 ["b_amount", 0, "Material Output", 2]]
        for i in links:
            o = nodes[i[0]].outputs[i[1]]
            i = nodes[i[2]].inputs[i[3]]
            mat.node_tree.links.new(o, i)

    elif bump_type == "3":  # flaky
        node = nodes.new("ShaderNodeMapping")
        node.name = "b_scale"
        node.location = -1500, -700
        node.scale = (bump_scale, bump_scale, bump_scale)
        node.label = "Bump Scale"
        node = nodes.new("ShaderNodeMapping")
        node.name = "b_scale2"
        node.location = -1500, -400
        node.rotation = (radians(-45.0), 0.0, 0.0)
        node.scale = (bump_scale, bump_scale, bump_scale)
        node.label = "Bump Scale 2"

        node = nodes.new("ShaderNodeTexNoise")
        node.name = "b_noise"
        node.location = -1400, -200
        node.inputs[1].default_value = 40.0
        node = nodes.new("ShaderNodeBrightContrast")
        node.name = "bc"
        node.location = -1200, -25
        node.inputs[2].default_value = 15.0
        node = nodes.new("ShaderNodeTexNoise")
        node.name = "b_noise2"
        node.location = -1200, -50
        node.inputs[1].default_value = 12.0
        node.inputs[3].default_value = 1.0

        node = nodes.new("ShaderNodeTexWave")
        node.name = "wave"
        node.location = -1150, -500
        node.inputs[1].default_value = 30.0
        node.inputs[2].default_value = 4.0
        node = nodes.new("ShaderNodeBrightContrast")
        node.name = "bc2"
        node.location = -1000, -200
        node.inputs[2].default_value = 15.0
        node = nodes.new("ShaderNodeMixRGB")
        node.name = "w|bc"
        node.location = -950, -425
        node.inputs[1].default_value = (0.2, 0.2, 0.2, 1.0)

        node = nodes.new("ShaderNodeTexMusgrave")
        node.name = "musgrave"
        node.location = -900, -600
        node.inputs[1].default_value = 300.0
        node = nodes.new("ShaderNodeTexNoise")
        node.name = "b_noise3"
        node.location = -800, -900
        node.inputs[1].default_value = 1500.0
        node.inputs[3].default_value = 0.25
        node = nodes.new("ShaderNodeMixRGB")
        node.name = "bc2|m1"
        node.location = -750, -300
        node.inputs[1].default_value = (0.2, 0.2, 0.2, 1.0)
        node = nodes.new("ShaderNodeMixRGB")
        node.name = "m2|mus"
        node.location = -700, -500
        node = nodes.new("ShaderNodeMixRGB")
        node.name = "m2|m3"
        node.location = -500, -400
        node.inputs[1].default_value = (0.2, 0.2, 0.2, 1.0)

        node = nodes.new("ShaderNodeMath")
        node.name = "math"
        node.location = -500, -800
        node.operation = "MULTIPLY"
        node.inputs[1].default_value = 0.1
        node = nodes.new("ShaderNodeInvert")
        node.name = "invert"
        node.location = -350, -600
        node = nodes.new("ShaderNodeMixRGB")
        node.name = "m3|math"
        node.location = -150, -550
        node = nodes.new("ShaderNodeMath")
        node.name = "b_amount"
        node.location = 100, -200
        node.operation = "MULTIPLY"
        node.inputs[1].default_value = brick_bump
        node.label = "Bump Amount"

        links = [["uv_coords", 2, "b_scale", 0], ["uv_coords", 2, "b_scale2", 0], ["b_scale", 0, "b_noise", 0],
                 ["b_scale", 0, "b_noise2", 0], ["b_scale", 0, "musgrave", 0], ["b_scale2", 0, "wave", 0],
                 ["b_noise", 1, "bc", 0], ["b_noise2", 1, "bc2", 0], ["bc", 0, "w|bc", 0], ["wave", 1, "w|bc", 2],
                 ["bc2", 0, "bc2|m1", 0], ["w|bc", 0, "bc2|m1", 2], ["musgrave", 1, "m2|mus", 2],
                 ["b_noise3", 1, "math", 1], ["bc2|m1", 0, "m2|mus", 0], ["m2|mus", 0, "m2|m3", 2],
                 ["bc2|m1", 0, "m2|m3", 0], ["m2|m3", 0, "invert", 1], ["m2|m3", 0, "m3|math", 1],
                 ["invert", 0, "m3|math", 0], ["math", 0, "m3|math", 2], ["m3|math", 0, "b_amount", 0],
                 ["b_amount", 0, "Material Output", 2]]
        for i in links:
            o = nodes[i[0]].outputs[i[1]]
            i = nodes[i[2]].inputs[i[3]]
            mat.node_tree.links.new(o, i)

    return mat


def mortar_material(bpy, mortar_color, mortar_bump, name):
    mat = bpy.data.materials.get(name)
    nodes = mat.node_tree.nodes
    mat.diffuse_color = mortar_color

    if len(nodes) > 2:  # update
        node = nodes["Diffuse BSDF"]
        node.inputs[0].default_value = (mortar_color[0], mortar_color[1], mortar_color[2], 1.0)
        node = nodes["b_amount"]
        node.inputs[1].default_value = mortar_bump
    else:  # create
        node = nodes["Diffuse BSDF"]
        node.inputs[0].default_value = (mortar_color[0], mortar_color[1], mortar_color[2], 1.0)
        node = nodes.new("ShaderNodeTexCoord")
        node.name = "uv_coords"
        node.location = -700, 200
        node = nodes.new("ShaderNodeMapping")
        node.name = "scale"
        node.location = -500, 200
        node.scale = (15.0, 15.0, 15.0)

        node = nodes.new("ShaderNodeTexNoise")
        node.name = "b_noise"
        node.location = -150, 200
        node.inputs[1].default_value = 100.0
        node = nodes.new("ShaderNodeMath")
        node.name = "b_amount"
        node.location = 50, 100
        node.operation = "MULTIPLY"
        node.inputs[1].default_value = mortar_bump

        links = [["uv_coords", 2, "scale", 0], ["scale", 0, "b_noise", 0], ["b_noise", 1, "b_amount", 0],
                 ["b_amount", 0, "Material Output", 2]]
        for link in links:
            o = nodes[link[0]].outputs[link[1]]
            i = nodes[link[2]].inputs[link[3]]
            mat.node_tree.links.new(o, i)

    return mat
