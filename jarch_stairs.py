import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty, IntProperty, FloatVectorProperty
from math import radians, atan, tan, cos, sqrt, asin
from mathutils import Euler, Vector
import bmesh
from random import uniform
from . jarch_materials import image_material
from . jarch_utils import point_rotation, METRIC_INCH, I


def custom_tread_placement(context, custom_tread_pos, custom_tread):
    # custom treads
    if custom_tread_pos:
        if custom_tread in bpy.data.objects:
            tread_ob = bpy.data.objects[custom_tread]
            ob = context.object

            for i in context.selected_objects:
                i.select = False
                
            tread_names = []
            for i in custom_tread_pos:
                tread_ob.select = True
                context.scene.objects.active = tread_ob
                
                bpy.ops.object.duplicate()
                context.object.location = i
                context.object.hide = False
                tread_names.append(context.object.name)
                context.object.select = False
            tread_ob.select = False
            
            for i in tread_names:
                bpy.data.objects[i].select = True
                
            ob.select = True
            context.scene.objects.active = ob
            bpy.ops.object.join() 


def create_stairs(self, context, style, overhang, steps, tw, rh, of, os, w, n_landing, is_close, tw0, rh0, ld0, l_rot0,
                  of0, os0, overhang0, is_back0, l_rot1, tw1, rh1, ld1, of1, os1, overhang1, is_back1, w_rot,
                  stair_to_rot, rot, steps0, steps1, set_in, is_riser, is_landing, is_light, num_steps2, tread_res,
                  pd, pole_res, is_custom_tread, custom_tread):
    
    verts, faces, names = [], [], []
    
    # figure out what angle to use for winding stairs if them
    angles = [None, radians(-90), radians(-45), radians(45), radians(90)]    
    angle = angles[int(w_rot)]

    mats = []
    for i in context.object.data.materials:
        mats.append(i.name)

    if style == "1":
        pre_pos = [0.0, 0.0, 0.0]
        pre_rot = tuple(context.object.rotation_euler)
        
        # for each set of stairs and landings
        for i in range(n_landing + 1):
            
            # calculate variables to pass in
            if i == 0:
                pass_in = [tw, rh, of, os, overhang, steps]
            elif i == 1:
                pass_in = [tw0, rh0, of0, os0, overhang0, steps0, l_rot0, ld0]
            elif i == 2:
                pass_in = [tw1, rh1, of1, os1, overhang1, steps1, l_rot1, ld1]
        
            # get step data
            verts_t, faces_t, cx, cy, cz, verts2_t, faces2_t, tread_pos = normal_stairs(pass_in[0], pass_in[1],
                                                                                        pass_in[2], pass_in[3], w,
                                                                                        pass_in[4], pass_in[5],
                                                                                        is_close, set_in, is_riser,
                                                                                        is_light, i, is_custom_tread)
            rot = 0
            # create jacks or wait till rotation and location is figured out depending on which level you are on
            if i == 0:
                m_ob = context.object
                verts, faces = verts_t, faces_t
                mesh4 = bpy.data.meshes.new("jacks_" + str(i))
                mesh4.from_pydata(verts2_t, [], faces2_t)
                ob3 = bpy.data.objects.new("jacks_" + str(i), mesh4)
                context.scene.objects.link(ob3)
                
                m_ob.select, ob3.select = False, True
                context.scene.objects.active = ob3
                custom_tread_placement(context, tread_pos, custom_tread)
                
                ob3.select, m_ob.select = False, True
                context.scene.objects.active = m_ob
                
                ob3.rotation_euler = context.object.rotation_euler
                ob3.location = context.object.location
                names.append(ob3.name)
                ob3.scale = context.object.scale

                if context.scene.render.engine == "CYCLES":
                    if len(mats) >= 2:
                        ob3.data.materials.append(bpy.data.materials[mats[1]])
                    else:
                        mat = bpy.data.materials.new("jack_temp")
                        mat.use_nodes = True
                        ob3.data.materials.append(mat)
            else:
                pre_pos2 = pre_pos[:]

                if l_rot0 == "2":
                    rot += 180 if is_back0 else 90
                elif l_rot0 == "3":
                    rot -= 180 if is_back0 else 90
                if n_landing == 2 and i == 2:
                    if l_rot1 == "2":
                        rot += 180 if is_back1 else 90
                    elif l_rot1 == "3":
                        rot -= 180 if is_back1 else 90

                # calculate position, adjust offset causes by rotating to the side
                if pass_in[6] == "1":  # forwards
                    orient = "straight"
                    if i == 1:
                        pre_pos[1] += pass_in[7]
                    elif i == 2 and l_rot0 == "1":
                        pre_pos[1] += pass_in[7]
                    elif i == 2 and l_rot0 == "2" and not is_back0:
                        pre_pos[0] -= pass_in[7]
                    elif i == 2 and l_rot0 == "2" and is_back0:
                        pre_pos[1] -= pass_in[7]
                    elif i == 2 and l_rot0 == "3" and not is_back0:
                        pre_pos[0] += pass_in[7]
                    elif i == 2 and l_rot0 == "3" and is_back0:
                        pre_pos[1] -= pass_in[7]
                elif pass_in[6] == "2":  # left
                    if i == 1 and not is_back0:
                        pre_pos[0] -= w / 2
                        pre_pos[1] += pass_in[7] / 2
                        orient = "straight"
                    elif i == 1 and is_back0:
                        pre_pos[0] -= w
                        orient = "left"
                    elif i == 2 and l_rot0 == "1" and not is_back1:
                        pre_pos[1] += pass_in[7] / 2
                        pre_pos[0] -= w / 2
                        orient = "straight"
                    elif i == 2 and l_rot0 == "1" and is_back1:
                        pre_pos[0] -= w
                        orient = "left"
                    elif i == 2 and l_rot0 == "2" and not is_back0 and not is_back1:
                        pre_pos[0] -= pass_in[7] / 2
                        pre_pos[1] -= w / 2
                        orient = "straight"
                    elif i == 2 and l_rot0 == "2" and not is_back0 and is_back1:
                        pre_pos[1] -= w
                        orient = "left"
                    elif i == 2 and l_rot0 == "2" and is_back0 and not is_back1:
                        pre_pos[0] += w / 2
                        pre_pos[1] -= pass_in[7] / 2
                        orient = "straight"
                    elif i == 2 and l_rot0 == "2" and is_back0 and is_back1:
                        pre_pos[0] += w
                        orient = "left"
                    elif i == 2 and l_rot0 == "3" and not is_back0 and not is_back1:
                        pre_pos[0] += pass_in[7] / 2
                        pre_pos[1] += w / 2
                        orient = "straight"
                    elif i == 2 and l_rot0 == "3" and not is_back0 and is_back1:
                        pre_pos[1] += w
                        orient = "left"
                    elif i == 2 and l_rot0 == "3" and is_back0 and not is_back1:
                        pre_pos[0] += w / 2
                        pre_pos[1] -= pass_in[7] / 2
                        orient = "straight"
                    elif i == 2 and l_rot0 == "3" and is_back0 and is_back1:
                        pre_pos[0] += w
                        orient = "left"
                elif pass_in[6] == "3":
                    if i == 1 and not is_back0:
                        pre_pos[1] += pass_in[7] / 2
                        pre_pos[0] += w / 2
                        orient = "straight"
                    elif i == 1 and is_back0:
                        pre_pos[0] += w
                        orient = "right"
                    elif i == 2 and l_rot0 == "1" and not is_back1:
                        pre_pos[1] += pass_in[7] / 2
                        pre_pos[0] += w / 2
                        orient = "straight"
                    elif i == 2 and l_rot0 == "1" and is_back1:
                        pre_pos[0] += w
                        orient = "right"
                    elif i == 2 and l_rot0 == "2" and not is_back0 and not is_back1:
                        pre_pos[0] -= pass_in[7] / 2
                        pre_pos[1] += w / 2
                        orient = "straight"
                    elif i == 2 and l_rot0 == "2" and not is_back0 and is_back1:
                        pre_pos[1] += w
                        orient = "right"
                    elif i == 2 and l_rot0 == "2" and is_back0 and not is_back1:
                        pre_pos[0] -= w / 2
                        pre_pos[1] -= pass_in[7] / 2
                        orient = "straight"
                    elif i == 2 and l_rot0 == "2" and is_back0 and is_back1:
                        pre_pos[0] -= w
                        orient = "right"
                    elif i == 2 and l_rot0 == "3" and not is_back0 and not is_back1:
                        pre_pos[0] += pass_in[7] / 2
                        pre_pos[1] -= w / 2
                        orient = "straight"
                    elif i == 2 and l_rot0 == "3" and not is_back0 and is_back1:
                        pre_pos[1] -= w
                        orient = "right"
                    elif i == 2 and l_rot0 == "3" and is_back0 and not is_back1:
                        pre_pos[0] -= w / 2
                        pre_pos[1] -= pass_in[7] / 2
                        orient = "straight"
                    elif i == 2 and l_rot0 == "3" and is_back0 and is_back1:
                        pre_pos[0] -= w
                        orient = "right"
                    
                # create stairs
                pre_pos[2] += 1 / METRIC_INCH                
                mesh2 = bpy.data.meshes.new("stair_" + str(i))
                mesh2.from_pydata(verts_t, [], faces_t)
                ob = bpy.data.objects.new("stair_" + str(i), mesh2)
                context.scene.objects.link(ob) 
                
                m_ob = context.object
                
                m_ob.select, ob.select = False, True
                context.scene.objects.active = ob
                custom_tread_placement(context, tread_pos, custom_tread)
                
                ob.select, m_ob.select = False, True
                context.scene.objects.active = m_ob                                  
                
                o = context.object
                eur = o.rotation_euler.copy()
                eur2 = Euler((0.0, 0.0, radians(rot)))
                eur.rotate(eur2)
                # matrix = o.matrix_world.inverted()
                pos = list(o.matrix_world * Vector(pre_pos))  # * matrix
                pos[0] += o.location[0]
                pos[1] += o.location[1]
                pos[2] += o.location[2]
                names.append(ob.name)
                ob.rotation_euler, ob.location, ob.scale = eur, pos, o.scale
                
                # jacks
                mesh4 = bpy.data.meshes.new("jacks_" + str(i))
                mesh4.from_pydata(verts2_t, [], faces2_t)
                ob3 = bpy.data.objects.new("jacks_" + str(i), mesh4)
                context.scene.objects.link(ob3)
                ob3.rotation_euler, ob3.location, ob3.scale = eur, pos, o.scale
                names.append(ob3.name)

                if context.scene.render.engine == "CYCLES":
                    if len(mats) >= 2:
                        ob3.data.materials.append(bpy.data.materials[mats[1]])
                    else:
                        mat = bpy.data.materials.new("jack_temp")
                        mat.use_nodes = True
                        ob3.data.materials.append(mat)
                        
                # landings
                if is_landing:
                    pre_pos2[2] += 1 / METRIC_INCH        
                    verts2, faces2 = stair_landing(w, pass_in[7], pass_in[1], orient)
                    mesh3 = bpy.data.meshes.new("landing_" + str(i))
                    mesh3.from_pydata(verts2, [], faces2)
                    ob2 = bpy.data.objects.new("landing_" + str(i), mesh3)
                    context.scene.objects.link(ob2)
                    names.append(ob2.name)
                    pre_pos2[2] -= pass_in[1]
                    pos2 = list(o.matrix_world * Vector(pre_pos2))
                    pos2[0] += o.location[0]
                    pos2[1] += o.location[1]
                    pos2[2] += o.location[2]
                    ob2.rotation_euler, ob2.location, ob2.scale = pre_rot, pos2, o.scale
                    pre_rot = eur    
                    
            # Apply translations correctly in relation to the rotation of the stairs
            if rot == 0 or rot == 360:
                pre_pos = [cx + pre_pos[0], cy + pre_pos[1], cz + pre_pos[2]]
            elif rot == 90 or rot == -270:
                pre_pos = [pre_pos[0] - cy, pre_pos[1], pre_pos[2] + cz]
            elif rot == -90 or rot == 270:
                pre_pos = [pre_pos[0] + cy, pre_pos[1], pre_pos[2] + cz]
            elif rot == 180 or rot == -180:
                pre_pos = [pre_pos[0], pre_pos[1] - cy, pre_pos[2] + cz]
    elif style == "2":
        verts, faces = winding_stairs(tw, rh, of, w, steps, angle, stair_to_rot)
    elif style == "3":
        verts, faces, verts2, faces2 = spiral_stairs(w, num_steps2, rh, rot, of, tread_res, pd, pole_res)
        mesh = bpy.data.meshes.new("pole_temp")
        mesh.from_pydata(verts2, [], faces2)
        ob4 = bpy.data.objects.new("pole_temp", mesh)
        context.scene.objects.link(ob4)
        o = context.object
        ob4.location, ob4.rotation_euler, ob4.scale = o.location, o.rotation_euler, o.scale
        names.append(ob4.name)

        if context.scene.render.engine == "CYCLES":
            if len(mats) >= 2:
                ob4.data.materials.append(bpy.data.materials[mats[1]])
            else:
                mat = bpy.data.materials.new("pole_temp")
                mat.use_nodes = True
                ob4.data.materials.append(mat)
                                     
    return verts, faces, names


def spiral_stairs(w, steps, rh, rot, of, tread_res, pd, pole_res):
    verts, faces = [], []
    ang = rot / (steps - 1)
    cur_ang, hof, cz = 0.0, of / 2, rh - I

    # half of the tread width out at the end
    ih = of / (tread_res + 1)
    for step in range(steps - 1):        
        p = len(verts)

        points = [(0.0, -hof), (w, 0.0)]
        for i in range(tread_res):
            points.append((w, 0.0))
        points += ((w, 0.0), (0.0, hof))
        for i in range(tread_res):
            points.append((0.0, hof - (i * ih) - ih))

        ct = 0
        for i in points:
            e_rot = asin(of / w) if step != 0 else 0

            if ct == 1 and rot >= 0:
                angle = cur_ang - e_rot
            elif ct == 2 + tread_res and rot >= 0:
                angle = cur_ang + ang
            elif ct == 1 and rot < 0:
                angle = cur_ang + ang
            elif ct == 2 + tread_res and rot < 0:
                angle = cur_ang
            elif 1 < ct < 2 + tread_res and rot >= 0:
                angle = cur_ang + (((ang + e_rot) / (tread_res + 1)) * (ct - 1)) - e_rot
            elif 1 < ct < 2 + tread_res and rot < 0:
                angle = (cur_ang + ang) - (((ang + e_rot) / (tread_res + 1)) * (ct - 1)) - e_rot
            else:
                angle = -(step * ang + radians(180)) - ang / 2

            x, y = point_rotation(i, (0.0, 0.0), angle)                
            verts += [(x, y, cz), (x, y, cz + I)]
            ct += 1

        cz += rh
        cur_ang += ang

        lp = p
        for i in range(3 + 2 * tread_res):  # edge faces
            faces.append((lp, lp + 2, lp + 3, lp + 1))
            lp += 2
        faces.append((p, p + 1, lp + 1, lp + 1, lp))  # last side face

        p1, p2 = 1, 3
        for i in range(1 + tread_res):
            p3 = (p1 - 2) % (8 + tread_res * 4)
            faces.append((p + p1, p + p2, p + p2 + 2, p + p3))
            p1, p2 = p3, p2 + 2

        p1, p2 = 0, 2
        for i in range(1 + tread_res):
            p3 = (p1 - 2) % (8 + tread_res * 4)
            faces.append((p + p1, p + p3, p + p2 + 2, p + p2))
            p1, p2 = p3, p2 + 2

    # pole
    cz -= rh - I
    verts2, faces2 = [], []
    ang = radians(360 / pole_res)
    z = 0.0

    for i in range(2):
        for vs in range(pole_res):
            cur_ang = vs * ang
            x, y = point_rotation((pd / 2, 0.0), (0.0, 0.0), cur_ang)
            verts2.append((x, y, z))
        z += cz

    for i in range(pole_res - 1):
        faces2.append((i, i + 1, i + pole_res + 1, i + pole_res))
    faces2.append((pole_res - 1, 0, pole_res, 2 * pole_res - 1))  # last side face
    faces2.append([i for i in range(0, pole_res)])  # bottom
    faces2.append([i for i in range(pole_res, pole_res * 2)])  # top
    
    return verts, faces, verts2, faces2


def winding_stairs(tw, rh, of, w, steps, w_rot, st_t_rot):
    verts, faces = [], []
    # create radians measures and round to 4 decimal places
    r45, r90, r180 = radians(45), radians(90), radians(180)
    tw -= of

    # figure out the distance farther to go on left or right side based on rotation
    if -r45 < w_rot < r45:
        gy, ex = abs(w * tan(w_rot)), 0
    else:
        gy, ex = w, w * tan(abs(w_rot) - r45)
    gy += I

    # calculate number of steps on corner
    if w_rot != 0.0:
        ti = 10 / METRIC_INCH
        c_steps = int((ti * abs(w_rot)) / (tw - I))
    else:
        c_steps = 0

    cx, cy, cz, hw = 0, 0, 0, w / 2
    rh -= I
    temp_dw, temp_x = sqrt((gy ** 2 + w ** 2)), 0.0

    for step in range(steps):
        p = len(verts)
        face_type = None

        if step + 1 < st_t_rot:  # before rotation
            verts += [(cx - hw, cy, cz), (cx - hw, cy + I, cz), (cx - hw, cy + I, cz + rh), (cx - hw, cy, cz + rh),
                      (cx + hw, cy, cz), (cx + hw, cy + I, cz), (cx + hw, cy + I, cz + rh), (cx + hw, cy, cz + rh),
                      (cx - hw, cy - of, cz + rh), (cx - hw, cy + tw, cz + rh), (cx - hw, cy + tw, cz + rh + I),
                      (cx - hw, cy - of, cz + rh + I), (cx + hw, cy - of, cz + rh), (cx + hw, cy + tw, cz + rh),
                      (cx + hw, cy + tw, cz + rh + I), (cx + hw, cy - of, cz + rh + I)]
            cy += tw
            cz += rh
            face_type = "normal"
        elif st_t_rot <= step + 1 <= st_t_rot + c_steps:  # in rotation
            if -r45 <= w_rot <= r45:
                yp = (gy / (c_steps + 1))
                y, y2 = yp * (step + 2 - st_t_rot),  yp * (step + 1 - st_t_rot)
                if 0 < w_rot <= r45:  # positive rotation
                    cx = hw
                    verts += [(cx, cy, cz), (cx, cy, cz + rh), (cx - w, cy + y2, cz), (cx - w, cy + y2, cz + rh),
                              (cx - w, cy + y2 + I, cz), (cx - w, cy + y2 + I, cz + rh), (cx, cy + I, cz),
                              (cx, cy + I, cz + rh), (cx, cy - of, cz + rh), (cx, cy - of, cz + rh + I),
                              (cx - w, cy + y2 - of, cz + rh), (cx - w, cy + y2 - of, cz + rh + I),
                              (cx - w, cy + y, cz + rh), (cx - w, cy + y, cz + rh + I), (cx, cy + I, cz + rh),
                              (cx, cy + I, cz + rh + I)]
                    face_type = "pos"
                elif -r45 <= w_rot < 0:  # negative rotation
                    cx = -hw
                    verts += [(cx, cy, cz), (cx, cy, cz + rh), (cx + w, cy + y2, cz), (cx + w, cy + y2, cz + rh),
                              (cx + w, cy + y2 + I, cz), (cx + w, cy + y2 + I, cz + rh), (cx, cy + I, cz),
                              (cx, cy + I, cz + rh), (cx, cy - of, cz + rh), (cx, cy - of, cz + rh + I),
                              (cx + w, cy + y2 - of, cz + rh), (cx + w, cy + y2 - of, cz + rh + I),
                              (cx + w, cy + y, cz + rh), (cx + w, cy + y, cz + rh + I), (cx, cy + I, cz + rh),
                              (cx, cy + I, cz + rh + I)]
                    face_type = "neg"
            else:  # |w_rot| > 45
                ang = w_rot / (c_steps + 1)
                cur_ang = ang * (step + 2 - st_t_rot)
                if w_rot > 0:  # positive rotation
                    if abs(cur_ang) <= r45:
                        y, y2 = (gy / r45) * abs(cur_ang), (gy / r45) * (abs(cur_ang - ang))
                        cx = hw
                        verts += [(cx, cy, cz), (cx, cy, cz + rh), (cx - w, cy + y2, cz), (cx - w, cy + y2, cz + rh),
                                  (cx - w, cy + y2 + I, cz), (cx - w, cy + y2 + I, cz + rh), (cx, cy + I, cz),
                                  (cx, cy + I, cz + rh), (cx, cy - of, cz + rh), (cx, cy - of, cz + rh + I),
                                  (cx - w, cy - of, cz + rh), (cx - w, cy - of, cz + rh + I), (cx - w, cy + y, cz + rh),
                                  (cx - w, cy + y, cz + rh + I), (cx, cy + I, cz + rh), (cx, cy + I, cz + rh + I)]
                        face_type = "pos"
                    elif abs(cur_ang - ang) < r45 < abs(cur_ang):  # step on corner
                        x = (ex / (abs(w_rot) - r45)) * (abs(cur_ang) - r45) - I
                        y2, temp_x, cx = (gy / r45) * (abs(cur_ang - ang)), x, hw
                        verts += [(cx, cy, cz), (cx, cy, cz + rh), (cx - w, cy + y2, cz), (cx - w, cy + y2, cz + rh),
                                  (cx - w, cy + y2 + I, cz), (cx - w, cy + y2 + I, cz + rh), (cx, cy + I, cz),
                                  (cx, cy + I, cz + rh), (cx, cy - of, cz + rh), (cx, cy - of, cz + rh + I),
                                  (cx - w, cy - of + y2, cz + rh), (cx - w, cy - of + y2, cz + rh + I),
                                  (cx - w, cy + gy, cz + rh), (cx - w, cy + gy, cz + rh + I),
                                  (cx - w + x, cy + gy, cz + rh), (cx - w + x, cy + gy, cz + rh + I), (cx, cy, cz + rh),
                                  (cx, cy, cz + rh + I)]
                        face_type = "pos_tri"
                    else:  # last step
                        ct = 0
                        points = ((cx, cy), (cx - w + temp_x - I, cy + gy - I), (cx - w + temp_x - I, cy + gy),
                                  (cx - I, cy), (cx + of, cy), (cx - w + temp_x - I, cy + gy - of - I),
                                  (cx - w + temp_x - I, cy + gy + ex - temp_x - I), (cx - I, cy))

                        for i in points:
                            origin = (cx - w + temp_x, cy + gy - I) if ct in (1, 2, 5, 6) else (cx, cy)
                            x, y = point_rotation(i, origin, w_rot + r180)

                            if ct <= 3:
                                verts += [(x, y, cz), (x, y, cz + rh)]
                            else:
                                verts += [(x, y, cz + rh), (x, y, cz + rh + I)]
                            ct += 1
                        face_type = "pos"
                else:  # negative rotation
                    if abs(cur_ang) <= r45:
                        y, y2, cx = (gy / r45) * abs(cur_ang), (gy / r45) * (abs(cur_ang - ang)), -hw
                        verts += [(cx, cy, cz), (cx, cy, cz + rh), (cx + w, cy + y2, cz), (cx + w, cy + y2, cz + rh),
                                  (cx + w, cy + y2 + I, cz), (cx + w, cy + y2 + I, cz + rh), (cx, cy + I, cz),
                                  (cx, cy + I, cz + rh), (cx, cy - of, cz + rh), (cx, cy - of, cz + rh + I),
                                  (cx + w, cy - of, cz + rh), (cx + w, cy - of, cz + rh + I), (cx + w, cy + y, cz + rh),
                                  (cx + w, cy + y, cz + rh + I), (cx, cy + I, cz + rh), (cx, cy + I, cz + rh + I)]
                        face_type = "neg"
                    elif abs(cur_ang - ang) < r45 < abs(cur_ang):  # step on corner
                        x = (ex / (abs(w_rot) - r45)) * (abs(cur_ang) - r45) + I
                        y2, temp_x, cx = (gy / r45) * (abs(cur_ang - ang)), x, -hw
                        verts += [(cx, cy, cz), (cx, cy, cz + rh), (cx + w, cy + y2, cz), (cx + w, cy + y2, cz + rh),
                                  (cx + w, cy + y2 + I, cz), (cx + w, cy + y2 + I, cz + rh), (cx, cy + I, cz),
                                  (cx, cy + I, cz + rh), (cx, cy - of, cz + rh), (cx, cy - of, cz + rh + I),
                                  (cx + w, cy - of + y2, cz + rh), (cx + w, cy - of + y2, cz + rh + I),
                                  (cx + w, cy + gy, cz + rh), (cx + w, cy + gy, cz + rh + I),
                                  (cx + w - x, cy + gy, cz + rh), (cx + w - x, cy + gy, cz + rh + I), (cx, cy, cz + rh),
                                  (cx, cy, cz + rh + I)]
                        face_type = "neg_tri"
                    else:  # last step
                        ct = 0
                        points = ((cx, cy), (cx + w - temp_x + I, cy + gy - I), (cx + w - temp_x + I, cy + gy),
                                  (cx + I, cy), (cx - of, cy), (cx + w - temp_x + I, cy + gy - of - I),
                                  (cx + w - temp_x + I, cy + gy + ex - temp_x - I), (cx + I, cy))

                        for i in points:
                            origin = (cx + w - temp_x, cy + gy - I) if ct in (1, 2, 5, 6) else (cx, cy)
                            x, y = point_rotation(i, origin, w_rot + r180)

                            if ct <= 3:
                                verts += [(x, y, cz), (x, y, cz + rh)]
                            else:
                                verts += [(x, y, cz + rh), (x, y, cz + rh + I)]
                            ct += 1
                        face_type = "neg"
            cz += rh
        else:  # after rotation
            if step == st_t_rot + c_steps:
                cy += I
                cz += rh + I
            else:
                cz += I
            cs, ct = step - c_steps - st_t_rot, 0
            z = cz + (rh * cs)

            if w_rot > 0:
                o2, face_type = (cx - w + ex, cy + gy - I), "pos"
                points = ((cx, cy + (cs * tw) - of), (cx - w + ex, cy + (cs * tw) + gy - I - of),
                          (cx - w + ex, cy + (cs * tw) + tw + gy - I), (cx, cy + (cs * tw) + tw), (cx, cy + (cs * tw)),
                          (cx - w + ex, cy + (cs * tw) + gy - I), (cx - w + ex, cy + (cs * tw) + gy),
                          (cx, cy + (cs * tw) + I))
            else:
                o2, face_type = (cx + w - ex, cy + gy - I), "neg"
                points = ((cx, cy + (cs * tw) - of), (cx + w - ex, cy + (cs * tw) + gy - I - of),
                          (cx + w - ex, cy + (cs * tw) + tw + gy - I), (cx, cy + (cs * tw) + tw), (cx, cy + (cs * tw)),
                          (cx + w - ex, cy + (cs * tw) + gy - I), (cx + w - ex, cy + (cs * tw) + gy),
                          (cx, cy + (cs * tw) + I))
            for i in points:
                origin = o2 if ct in (1, 2, 5, 6) else (cx, cy)
                x, y = point_rotation(i, origin, w_rot + r180)

                if ct <= 3:
                    verts += [(x, y, z), (x, y, z + I)]
                else:                    
                    verts += [(x, y, z - rh - I), (x, y, z)]
                ct += 1

        if face_type == "normal":
            faces += [(p, p + 4, p + 7, p + 3), (p, p + 3, p + 2, p + 1), (p + 1, p + 2, p + 6, p + 5),
                      (p + 2, p + 3, p + 7, p + 6), (p, p + 4, p + 5, p + 1), (p + 4, p + 5, p + 6, p + 7),
                      (p + 8, p + 11, p + 10, p + 9), (p + 8, p + 12, p + 15, p + 11), (p + 12, p + 13, p + 14, p + 15),
                      (p + 14, p + 13, p + 9, p + 10), (p + 11, p + 15, p + 14, p + 10), (p + 8, p + 12, p + 13, p + 9)]
        elif face_type == "pos":
            for i in range(2):                
                faces += [(p, p + 6, p + 7, p + 1), (p, p + 1, p + 3, p + 2), (p + 2, p + 3, p + 5, p + 4),
                          (p + 4, p + 5, p + 7, p + 6), (p + 1, p + 7, p + 5, p + 3), (p, p + 2, p + 4, p + 6)]
                p += 8
        elif face_type == "neg":
            for i in range(2):                
                faces += [(p, p + 1, p + 7, p + 6), (p, p + 2, p + 3, p + 1), (p + 2, p + 4, p + 5, p + 3),
                          (p + 4, p + 6, p + 7, p + 5), (p + 1, p + 3, p + 5, p + 7), (p, p + 6, p + 4, p + 2)]
                p += 8
        elif face_type == "pos_tri":            
            faces += [(p, p + 6, p + 7, p + 1), (p, p + 1, p + 3, p + 2), (p + 2, p + 3, p + 5, p + 4),
                      (p + 4, p + 5, p + 7, p + 6), (p + 1, p + 7, p + 5, p + 3), (p, p + 2, p + 4, p + 6)]
            p += 8
            faces += [(p, p + 8, p + 9, p + 1), (p + 1, p + 9, p + 7, p + 3), (p + 3, p + 7, p + 5),
                      (p, p + 1, p + 3, p + 2), (p + 6, p + 7, p + 9, p + 8), (p + 4, p + 5, p + 7, p + 6),
                      (p + 2, p + 3, p + 5, p + 4), (p, p + 2, p + 6, p + 8), (p + 2, p + 4, p + 6)]
        elif face_type == "neg_tri":
            faces += [(p, p + 1, p + 7, p + 6), (p, p + 2, p + 3, p + 1), (p + 2, p + 4, p + 5, p + 3),
                      (p + 4, p + 6, p + 7, p + 5), (p + 1, p + 3, p + 5, p + 7), (p, p + 6, p + 4, p + 2)]
            p += 8
            faces += [(p, p + 1, p + 9, p + 8), (p + 1, p + 3, p + 7, p + 9), (p + 3, p + 5, p + 7),
                      (p, p + 2, p + 3, p + 1), (p + 6, p + 8, p + 9, p + 7), (p + 4, p + 6, p + 7, p + 5),
                      (p + 2, p + 4, p + 5, p + 3), (p, p + 8, p + 6, p + 2), (p + 2, p + 6, p + 4)]

    return verts, faces
    

def stair_landing(w, depth, riser, orient):
    hw, p = w / 2, 0
    if orient == "straight":
        verts = [(-hw, 0.0, 0.0), (-hw, 0.0, riser), (-hw, depth, 0.0), (-hw, depth, riser), (hw, depth, 0.0),
                 (hw, depth, riser), (hw, 0.0, 0.0), (hw, 0.0, riser)]
    elif orient == "left":
        verts = [(-hw - w, 0.0, 0.0), (-hw - w, 0.0, riser), (-hw - w, depth, 0.0), (-hw - w, depth, riser),
                 (hw, depth, 0.0), (hw, depth, riser), (hw, 0.0, 0.0), (hw, 0.0, riser)]
    else:
        verts = [(-hw, 0.0, 0.0), (-hw, 0.0, riser), (-hw, depth, 0.0), (-hw, depth, riser), (hw + w, depth, 0.0),
                 (hw + w, depth, riser), (hw + w, 0.0, 0.0), (hw + w, 0.0, riser)]

    faces = [(p, p + 1, p + 3, p + 2), (p + 1, p + 7, p + 5, p + 3), (p + 4, p + 5, p + 7, p + 6),
             (p, p + 2, p + 4, p + 6), (p + 2, p + 3, p + 5, p + 4), (p, p + 6, p + 7, p + 1)]

    return verts, faces


def normal_stairs(tread, riser, over_front, over_sides, w, ov, t_steps, is_close, set_in, is_riser, is_light, landing,
                  is_custom_tread):
    verts, faces = [], []
    tread -= over_front
    # figure number of jacks
    if set_in:
        jack_type = "set_in"
        jack_num = 2
    elif is_close:
        jack_num = int(w / 0.3048)
        jack_type = "normal"
    else:
        jack_type = "normal"
        jack_num = int(w / 0.3048)

    if is_light and jack_type == "normal" and jack_num % 2 != 0:
        jack_num += 1

    cx, t, cz, sy, cy = -(w / 2), 0.0508, 0, 0, 0
    space = (w - t) / (jack_num - 1)  # current x, thickness, space between jacks
    extra = 6 / METRIC_INCH
    t_height, t_depth = t_steps * riser, t_steps * tread - I

    if jack_type == "set_in":
        riser -= t
        ty = (t * tread) / (riser + t)
        ow, width = tread + tread + ty, tread + (2 * ty)

    for jack in range(jack_num):  # each jack
        if jack_type != "set_in":
            cy = 0 if not is_riser else I
        else:
            cy = 0.0

        # calculate line slope
        if not is_close or (jack != 0 and jack != jack_num - 1):
            point = [extra + cy, 0.0]
            point_1 = [tread * t_steps + cy - I, (riser * t_steps) - extra]
            slope = (point[1] - point_1[1]) / (point[0] - point_1[0])
            b = point[1] - (slope * point[0])
        elif (jack == 0 or jack == jack_num - 1) and is_close:
            b, slope = 0.0, 0.0

        last = 0.0
        if is_close and jack in (0, jack_num - 1):
            last = t_height - extra

        cz, sy = riser, cy
        for stair in range(t_steps):
            face_type = "normal"
            p = len(verts)

            if jack_type == "normal":
                if stair == 0:
                    z = (slope * (cy + tread)) + b
                    verts += [(cx, cy, cz - riser), (cx + t, cy, cz - riser), (cx, cy, cz), (cx + t, cy, cz),
                              (cx, cy + tread, cz), (cx + t, cy + tread, cz), (cx, cy + tread, z),
                              (cx + t, cy + tread, z), (cx, cy + extra, cz - riser), (cx + t, cy + extra, cz - riser)]
                    face_type = "first"
                elif stair == t_steps - 1:
                    verts += [(cx, cy, cz), (cx + t, cy, cz), (cx, cy + tread - I, cz), (cx + t, cy + tread - I, cz),
                              (cx, cy + tread - I, cz - extra - last), (cx + t, cy + tread - I, cz - extra - last)]
                else:
                    z = (slope * (cy + tread)) + b
                    verts += [(cx, cy, cz), (cx + t, cy, cz), (cx, cy + tread, cz), (cx + t, cy + tread, cz),
                              (cx, cy + tread, z), (cx + t, cy + tread, z)]

                if face_type == "first":
                    faces += [(p, p + 1, p + 3, p + 2), (p + 2, p + 3, p + 5, p + 4), (p, p + 2, p + 4, p + 6),
                              (p + 1, p + 7, p + 5, p + 3), (p + 6, p + 7, p + 9, p + 8), (p, p + 8, p + 9, p + 1),
                              (p, p + 6, p + 8), (p + 1, p + 9, p + 7)]
                else:
                    if stair == 1:
                        faces += [(p, p + 1, p + 3, p + 2), (p, p + 2, p + 4, p - 6), (p - 6, p + 4, p - 4),
                                  (p, p - 6, p - 5, p + 1), (p + 1, p - 5, p + 5, p + 3), (p - 5, p - 3, p + 5),
                                  (p - 3, p - 4, p + 4, p + 5)]
                    else:
                        faces += [(p, p + 1, p + 3, p + 2), (p, p + 2, p + 4, p - 4), (p - 4, p + 4, p - 2),
                                  (p, p - 4, p - 3, p + 1), (p + 1, p - 3, p + 5, p + 3), (p - 3, p - 1, p + 5),
                                  (p - 1, p - 2, p + 4, p + 5)]
                if stair == t_steps - 1:
                    if t_steps == 1:
                        faces.append((p + 4, p + 5, p + 7, p + 6))
                    else:
                        faces.append((p + 2, p + 3, p + 5, p + 4))

                cy += tread
                cz += riser
            elif jack_type == "set_in":
                if stair == 0:
                    cy = -tread if landing != 0 else 0
                    cz = 0.0

                    if landing != 0:
                        verts += [(cx, cy + tread, cz), (cx + I, cy + tread, cz), (cx + t, cy + tread, cz),
                                  (cx, cy + tread, cz + riser), (cx + I, cy + tread, cz + riser),
                                  (cx + t, cy + tread, cz + riser)]
                    else:                                                         
                        verts += [(cx, cy, cz), (cx + I, cy, cz), (cx + t, cy, cz), (cx, cy + tread - ty, cz + riser),
                                  (cx + I, cy + tread - ty, cz + riser), (cx + t, cy + tread - ty, cz + riser)]

                    verts += [(cx, cy + tread, cz + riser + t), (cx + I, cy + tread, cz + riser + t),
                              (cx + t, cy + tread, cz + riser + t), (cx, cy + ow, cz + riser + t),
                              (cx + I, cy + ow, cz + riser + t), (cx + t, cy + ow, cz + riser + t),
                              (cx, cy + ow - ty, cz + riser), (cx + I, cy + ow - ty, cz + riser),
                              (cx + t, cy + ow - ty, cz + riser), (cx, cy + width - ty, cz),
                              (cx + I, cy + width - ty, cz), (cx + t, cy + width - ty, cz)]
                    cy += tread + tread - ty
                    cz += riser + riser + t
                    face_type = "first" if jack == 0 else "first_right"
                elif stair == t_steps - 1:
                    verts += [(cx, cy, cz), (cx + I, cy, cz), (cx + t, cy, cz), (cx, cy + ty, cz + t),
                              (cx + I, cy + ty, cz + t), (cx + t, cy + ty, cz + t), (cx, cy + width - ty, cz + t),
                              (cx + I, cy + width - ty, cz + t), (cx + t, cy + width - ty, cz + t),
                              (cx, cy + tread + ty, cz), (cx + I, cy + tread + ty, cz), (cx + t, cy + tread + ty, cz)]

                    cz += riser + t + t
                    cy += tread + ty
                    face_type = "last" if jack == 0 else "last_right"
                    verts += [(cx, cy, cz), (cx + I, cy, cz), (cx + t, cy, cz)]
                else:
                    verts += [(cx, cy, cz), (cx + I, cy, cz), (cx + t, cy, cz), (cx, cy + ty, cz + t),
                              (cx + I, cy + ty, cz + t), (cx + t, cy + ty, cz + t),
                              (cx, cy + width, cz + t), (cx + I, cy + width, cz + t), (cx + t, cy + width, cz + t),
                              (cx, cy + tread + ty, cz), (cx + I, cy + tread + ty, cz), (cx + t, cy + tread + ty, cz)]

                    cy += tread
                    cz += riser + t
                    if jack != 0:
                        face_type = "normal_right"

                if face_type == "first":
                    faces += [(p, p + 3, p + 12, p + 15), (p, p + 1, p + 4, p + 3), (p + 1, p + 2, p + 5, p + 4),
                              (p + 2, p + 17, p + 14, p + 5), (p + 16, p + 13, p + 14, p + 17),
                              (p + 15, p + 12, p + 13, p + 16), (p, p + 15, p + 16, p + 1),
                              (p + 1, p + 16, p + 17, p + 2), (p + 3, p + 4, p + 7, p + 6),
                              (p + 4, p + 5, p + 14, p + 13), (p + 4, p + 13, p + 10, p + 7),
                              (p + 12, p + 9, p + 10, p + 13), (p + 3, p + 6, p + 9, p + 12)]

                    if t_steps != 1:
                        faces.append((p + 7, p + 10, p + 11, p + 8))
                    else:
                        faces.append((p + 6, p + 7, p + 10, p + 9))
                elif face_type == "first_right":
                    faces += [(p, p + 3, p + 12, p + 15), (p, p + 1, p + 4, p + 3), (p + 1, p + 2, p + 5, p + 4),
                              (p + 2, p + 17, p + 14, p + 5), (p + 16, p + 13, p + 14, p + 17),
                              (p + 15, p + 12, p + 13, p + 16), (p + 4, p + 5, p + 8, p + 7),
                              (p + 5, p + 14, p + 11, p + 8), (p + 14, p + 13, p + 10, p + 11),
                              (p + 12, p + 3, p + 4, p + 13), (p + 4, p + 7, p + 10, p + 13),
                              (p, p + 15, p + 16, p + 1), (p + 1, p + 16, p + 17, p + 2)]

                    if t_steps != 1:
                        faces.append((p + 6, p + 9, p + 10, p + 7))
                    else:
                        faces.append((p + 7, p + 8, p + 11, p + 10))
                elif face_type == "normal":
                    if stair == 1:
                        faces += [(p, p - 12, p - 11, p + 1), (p + 1, p - 11, p - 10, p + 2),
                                  (p + 2, p - 10, p - 7, p + 11), (p - 8, p + 10, p + 11, p - 7),
                                  (p - 9, p + 9, p + 10, p - 8), (p, p + 9, p - 9, p - 12), (p, p + 1, p + 4, p + 3),
                                  (p + 1, p + 2, p + 11, p + 10), (p + 1, p + 10, p + 7, p + 4),
                                  (p + 4, p + 7, p + 8, p + 5), (p + 6, p + 7, p + 10, p + 9), (p, p + 3, p + 6, p + 9)]
                    else:
                        faces += [(p, p - 9, p - 8, p + 1), (p + 1, p - 8, p - 7, p + 2), (p - 7, p - 4, p + 11, p + 2),
                                  (p - 4, p - 5, p + 10, p + 11), (p - 5, p - 6, p + 9, p + 10),
                                  (p, p + 9, p - 6, p - 9), (p, p + 1, p + 4, p + 3), (p + 1, p + 2, p + 11, p + 10),
                                  (p + 1, p + 10, p + 7, p + 4), (p + 4, p + 7, p + 8, p + 5),
                                  (p + 6, p + 7, p + 10, p + 9), (p, p + 3, p + 6, p + 9)]
                elif face_type == "normal_right":
                    if stair == 1:
                        faces += [(p, p - 12, p - 11, p + 1), (p + 1, p - 11, p - 10, p + 2),
                                  (p + 2, p - 10, p - 7, p + 11), (p - 8, p + 10, p + 11, p - 7),
                                  (p - 9, p + 9, p + 10, p - 8), (p, p + 9, p - 9, p - 12),
                                  (p + 1, p + 2, p + 5, p + 4), (p + 2, p + 11, p + 8, p + 5),
                                  (p + 7, p + 8, p + 11, p + 10), (p, p + 1, p + 10, p + 9),
                                  (p + 1, p + 4, p + 7, p + 10), (p + 3, p + 6, p + 7, p + 4)]
                    else:
                        faces += [(p, p - 9, p - 8, p + 1), (p + 1, p - 8, p - 7, p + 2), (p - 7, p - 4, p + 11, p + 2),
                                  (p - 4, p - 5, p + 10, p + 11), (p - 5, p - 6, p + 9, p + 10),
                                  (p, p + 9, p - 6, p - 9), (p + 1, p + 2, p + 5, p + 4), (p + 2, p + 11, p + 8, p + 5),
                                  (p + 7, p + 8, p + 11, p + 10), (p, p + 1, p + 10, p + 9),
                                  (p + 1, p + 4, p + 7, p + 10), (p + 3, p + 6, p + 7, p + 4)]
                elif face_type == "last":                    
                    faces += [(p, p - 9, p - 8, p + 1), (p + 1, p - 8, p - 7, p + 2), (p - 7, p - 4, p + 11, p + 2),
                              (p - 4, p - 5, p + 10, p + 11), (p - 5, p - 6, p + 9, p + 10), (p, p + 9, p - 6, p - 9),
                              (p, p + 1, p + 4, p + 3), (p + 1, p + 2, p + 11, p + 10), (p + 1, p + 10, p + 7, p + 4),
                              (p + 4, p + 7, p + 8, p + 5), (p + 6, p + 7, p + 10, p + 9), (p, p + 3, p + 6, p + 9)]
                elif face_type == "last_right":
                    faces += [(p, p - 9, p - 8, p + 1), (p + 1, p - 8, p - 7, p + 2), (p - 7, p - 4, p + 11, p + 2),
                              (p - 4, p - 5, p + 10, p + 11), (p - 5, p - 6, p + 9, p + 10), (p, p + 9, p - 6, p - 9),
                              (p + 1, p + 2, p + 5, p + 4), (p + 2, p + 11, p + 8, p + 5),
                              (p + 7, p + 8, p + 11, p + 10), (p, p + 1, p + 10, p + 9), (p + 1, p + 4, p + 7, p + 10),
                              (p + 3, p + 6, p + 7, p + 4)]

                if face_type in ("last_right", "last"):
                    faces += [(p + 3, p + 4, p + 13, p + 12), (p + 4, p + 5, p + 14, p + 13), (p + 5, p + 8, p + 14),
                              (p + 7, p + 13, p + 14, p + 8), (p + 6, p + 12, p + 13, p + 7), (p + 3, p + 12, p + 6)]

        cx += space

    verts_jacks, faces_jacks = verts, faces
    verts, faces, custom_tread_pos = [], [], []
    ry = cy   
    cx, cy, cz, hw = 0.0,  sy, 0.0,  w / 2

    if jack_type == "normal":
        if ov == "4":
            left = hw + over_sides
            right = hw + over_sides
        elif ov == "2":
            left = hw
            right = hw + over_sides
        elif ov == "3":
            left = hw + over_sides
            right = hw
        else:
            left = hw
            right = hw

        front = over_front + I if is_riser else over_front

        for step in range(t_steps):
            e = 0 if not is_riser else I
            p = len(verts)

            if is_riser:
                verts += [(cx - hw, cy, cz), (cx - hw, cy - I, cz), (cx - hw, cy, cz + riser),
                          (cx - hw, cy - I, cz + riser), (cx + hw, cy, cz + riser), (cx + hw, cy - I, cz + riser),
                          (cx + hw, cy, cz), (cx + hw, cy - I, cz)]

                faces += [(p, p + 1, p + 3, p + 2), (p + 1, p + 7, p + 5, p + 3), (p + 4, p + 5, p + 7, p + 6),
                          (p, p + 2, p + 4, p + 6), (p + 2, p + 3, p + 5, p + 4), (p, p + 6, p + 7, p + 1)]
                p += 8

            cz += riser

            if not is_custom_tread:
                verts += [(cx - left, cy - front, cz), (cx - left, cy - front, cz + I), (cx - left, cy + tread - e, cz),
                          (cx - left, cy + tread - e, cz + I), (cx + right, cy + tread - e, cz),
                          (cx + right, cy + tread - e, cz + I), (cx + right, cy - front, cz),
                          (cx + right, cy - front, cz + I)]

                faces += [(p, p + 1, p + 3, p + 2), (p + 1, p + 7, p + 5, p + 3), (p + 4, p + 5, p + 7, p + 6),
                          (p, p + 2, p + 4, p + 6), (p + 2, p + 3, p + 5, p + 4), (p, p + 6, p + 7, p + 1)]
            else:
                custom_tread_pos.append([cx, cy + tread - e, cz]) 
            cy += tread
        ry -= I
    elif jack_type == "set_in":
        hw -= I
        cz += riser
        cy += tread if landing == 0 else 0

        for step in range(t_steps):
            p = len(verts)
            verts += [(cx - hw, cy, cz), (cx - hw, cy, cz + t), (cx - hw, cy + tread, cz),
                      (cx - hw, cy + tread, cz + t), (cx + hw, cy + tread, cz), (cx + hw, cy + tread, cz + t),
                      (cx + hw, cy, cz), (cx + hw, cy, cz + t)]

            faces += [(p, p + 1, p + 3, p + 2), (p + 1, p + 7, p + 5, p + 3), (p + 4, p + 5, p + 7, p + 6),
                      (p, p + 2, p + 4, p + 6), (p + 2, p + 3, p + 5, p + 4), (p, p + 6, p + 7, p + 1)]

            cz += t + riser
            cy += tread
        t_height += t * t_steps + t - I

    return verts, faces, 0.0, ry, t_height + riser, verts_jacks, faces_jacks, custom_tread_pos


def update_stairs(self, context):
    o = context.object

    mats = []
    for i in o.data.materials:
        mats.append(i.name)

    verts, faces, names = create_stairs(self, context, o.s_style, o.s_overhang, o.s_num_steps, o.s_tread_width,
                                        o.s_riser_height, o.s_over_front, o.s_over_sides, o.s_width, o.s_num_land,
                                        o.s_is_close, o.s_tread_width0, o.s_riser_height0, o.s_landing_depth0,
                                        o.s_landing_rot0, o.s_over_front0, o.s_over_sides0, o.s_overhang0, o.s_is_back0,
                                        o.s_landing_rot1, o.s_tread_width1, o.s_riser_height1, o.s_landing_depth1,
                                        o.s_over_front1, o.s_over_sides1, o.s_overhang1, o.s_is_back1, o.s_w_rot,
                                        o.s_num_rot, o.s_rot, o.s_num_steps0, o.s_num_steps1, o.s_is_set_in,
                                        o.s_is_riser, o.s_is_landing, o.s_is_light, o.s_num_steps2, o.s_tread_res,
                                        o.s_pole_dia, o.s_pole_res, o.s_is_custom_tread, o.s_custom_tread)

    emesh = o.data
    mesh = bpy.data.meshes.new(name="siding")
    mesh.from_pydata(verts, [], faces)
    mesh.update(calc_edges=True)
    
    for i in bpy.data.objects:
        if i.data == emesh:
            i.data = mesh
    
    emesh.user_clear()
    bpy.data.meshes.remove(emesh)
    
    if context.scene.render.engine == "CYCLES":
        if len(mats) >= 1:
            o.data.materials.append(bpy.data.materials[mats[0]])
        else:
            mat = bpy.data.materials.new("stairs_temp")
            mat.use_nodes = True
            o.data.materials.append(mat)

    if names:
        for name in names:
            ob = bpy.data.objects[name].select = True
        o.select = True
        context.scene.objects.active = o
        bpy.ops.object.join()

    if o.s_unwrap:
        unwrap_stairs(self, context)
        if o.s_random_uve:
            random_uvs(self, context)

    for i in mats:
        if i not in o.data.materials:
            mat = bpy.data.materials[i]
            o.data.materials.append(mat)

    for i in bpy.data.materials:
        if i.users == 0:
            bpy.data.materials.remove(i)


def stair_materials(self, context):
    o = context.object
    if context.scene.render.engine == "CYCLES":
        if o.s_col_image == "" or (o.s_norm_image == "" and o.s_is_bump):
            self.report({"ERROR"}, "JARCH Vis: Image Filepaths Are Invalid")
            return

        mat = image_material(bpy, o.s_im_scale, o.s_col_image, o.s_norm_image, o.s_bump_amo, o.s_is_bump,
                             "stairs_temp_" + o.name, True, 0.1, 0.05, o.s_is_rotate, None)
        if mat is not None:
            mat.name = "stairs_" + o.name
            if len(o.data.materials) >= 1:
                o.data.materials[0] = mat
            else:
                o.data.materials.append(mat)
        else:
            self.report({"ERROR"}, "Images Not Found, Make Sure Path Is Correct")

        if o.s_style in ("1", "3"):
            if o.s_col_image2 == "" or (o.s_norm_image2 == "" and o.s_is_bump2):
                self.report({"ERROR"}, "JARCH Vis: Image Filepaths Are Invalid")
                return

            mat = image_material(bpy, o.s_im_scale2, o.s_col_image2, o.s_norm_image2, o.s_bump_amo2, o.s_is_bump2,
                                 "second_temp_" + o.name, True, 0.1, 0.05, o.s_is_rotate2, None)
            if mat is not None:
                mat.name = "jacks_" + o.name if o.s_style == "1" else "pole_" + o.name
                if len(o.data.materials) >= 2:
                    o.data.materials[1] = mat
                else:
                    o.data.materials.append(mat)
            else:
                self.report({"ERROR"}, "Images Not Found, Make Sure Path Is Correct")

        for i in bpy.data.materials:
            if i.users == 0:
                bpy.data.materials.remove(i)
    else:
        self.report({"ERROR"}, "JARCH VIS: Render Engine Must Be Cycles To Create Materials")


def unwrap_stairs(self, context):
    o = context.object
    for i in context.selected_objects:
        i.select = False

    o.select = True
    context.scene.objects.active = o
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    bpy.ops.object.editmode_toggle()
                    override = bpy.context.copy()
                    override["area"] = area
                    override["region"] = region
                    override["active_object"] = context.selected_objects[0]
                    bpy.ops.mesh.select_all(action="SELECT")
                    bpy.ops.uv.cube_project(override)
                    bpy.ops.object.editmode_toggle()


def random_uvs(self, context):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    bpy.ops.object.editmode_toggle()
                    bpy.ops.mesh.select_all(action="SELECT")
                    obj = bpy.context.object
                    me = obj.data
                    bm = bmesh.from_edit_mesh(me)      

                    uv_layer = bm.loops.layers.uv.verify()
                    bm.faces.layers.tex.verify()
                    # adjust UVs                        
                    for f in bm.faces:
                        offset = Vector((uniform(-1.0, 1.0), uniform(-1.0, 1.0)))
                        for v in f.loops:
                            luv = v[uv_layer]   
                            luv.uv = (luv.uv + offset).xy

                    bmesh.update_edit_mesh(me)
                    bpy.ops.object.editmode_toggle()


def delete_materials(self, context):
    o = context.object
    if not o.s_is_material and o.s_mat != "2":
        for i in o.data.materials:
            bpy.ops.object.material_slot_remove()
        for i in bpy.data.materials:
            if i.users == 0:
                bpy.data.materials.remove(i)


def preview_materials(self, context):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.viewport_shade = "RENDERED" if context.object.f_is_preview else "SOLID"
            

bpy.types.Object.s_object_add = StringProperty(default="none", update=update_stairs)
bpy.types.Object.s_style = EnumProperty(items=(("1", "Normal", ""), ("2", "Winding", ""), ("3", "Spiral", "")),
                                        default="1", description="Stair Style", update=update_stairs, name="")
bpy.types.Object.s_overhang = EnumProperty(items=(("1", "Normal", ""), ("2", "Right", ""), ("3", "Left", ""),
                                                  ("4", "Both", "")), default="1", description="Overhang Style",
                                           update=update_stairs, name="")
# common variables
bpy.types.Object.s_num_steps = IntProperty(name="Number Of Steps", min=1, max=24, default=13, update=update_stairs)
bpy.types.Object.s_num_steps2 = IntProperty(name="Number Of Steps", min=1, max=48, default=13, update=update_stairs)
bpy.types.Object.s_tread_width = FloatProperty(name="Tread Width", min=9.0 / METRIC_INCH, max=16.0 / METRIC_INCH,
                                               default=9.5 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
bpy.types.Object.s_riser_height = FloatProperty(name="Riser Height", min=5.0 / METRIC_INCH, max=8.0 / METRIC_INCH,
                                                default=7.4 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
bpy.types.Object.s_over_front = FloatProperty(name="Front Overhang", min=0.0, max=1.25 / METRIC_INCH,
                                              default=1.0 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
bpy.types.Object.s_over_sides = FloatProperty(name="Side Overhang", min=0.0, max=2.0 / METRIC_INCH,
                                              default=1.0 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
bpy.types.Object.s_width = FloatProperty(name="Stair Width", min=36.0 / METRIC_INCH, max=60.0 / METRIC_INCH,
                                         default=40.0 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
bpy.types.Object.s_is_riser = BoolProperty(name="Risers?", default=True, update=update_stairs)
bpy.types.Object.s_is_custom_tread = BoolProperty(name="Custom Treads?", default=False, update=update_stairs)
bpy.types.Object.s_custom_tread = StringProperty(name="Custom Tread", default="", update=update_stairs)
# normal style
bpy.types.Object.s_num_land = IntProperty(name="Number Of Landings", min=0, max=2, default=0, update=update_stairs)
bpy.types.Object.s_is_close = BoolProperty(name="Close Sides?", default=False, update=update_stairs)
bpy.types.Object.s_is_set_in = BoolProperty(name="Set Steps In?", default=False, update=update_stairs)
bpy.types.Object.s_is_landing = BoolProperty(name="Create Landings?", default=True, update=update_stairs)
bpy.types.Object.s_is_light = BoolProperty(name="Allow Recessed Lights?", default=False, update=update_stairs,
                                           description="Space Middle Step Jacks To Allow Recessed Lights")
# landing 0
bpy.types.Object.s_num_steps0 = IntProperty(name="Number Of Steps", min=1, max=24, default=13, update=update_stairs)
bpy.types.Object.s_tread_width0 = FloatProperty(name="Tread Width", min=9.0 / METRIC_INCH, max=16.0 / METRIC_INCH,
                                                default=9.5 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
bpy.types.Object.s_riser_height0 = FloatProperty(name="Riser Height", min=5.0 / METRIC_INCH, max=8.0 / METRIC_INCH,
                                                 default=7.4 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
bpy.types.Object.s_landing_depth0 = FloatProperty(name="Landing 1 Depth", min=36 / METRIC_INCH, max=60 / METRIC_INCH,
                                                  default=40 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
bpy.types.Object.s_landing_rot0 = EnumProperty(items=(("1", "Forwards", ""), ("2", "Left", ""), ("3", "Right", "")),
                                               update=update_stairs, name="")
bpy.types.Object.s_over_front0 = FloatProperty(name="Front Overhang", min=0.0, max=1.25 / METRIC_INCH,
                                               default=1.0 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
bpy.types.Object.s_over_sides0 = FloatProperty(name="Side Overhang", min=0.0, max=2.0 / METRIC_INCH,
                                               default=1.0 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
bpy.types.Object.s_overhang0 = EnumProperty(items=(("1", "Normal", ""), ("2", "Right", ""), ("3", "Left", ""),
                                                   ("4", "Both", "")), default="1", description="Overhang Style",
                                            update=update_stairs, name="")
bpy.types.Object.s_is_back0 = BoolProperty(name="Turn Backwards?", default=False, update=update_stairs)
# landing 1
bpy.types.Object.s_num_steps1 = IntProperty(name="Number Of Steps", min=1, max=24, default=13, update=update_stairs)
bpy.types.Object.s_landing_rot1 = EnumProperty(items=(("1", "Forwards", ""), ("2", "Left", ""), ("3", "Right", "")),
                                               update=update_stairs, name="")
bpy.types.Object.s_tread_width1 = FloatProperty(name="Tread Width", min=9.0 / METRIC_INCH, max=16.0 / METRIC_INCH,
                                                default=9.5 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
bpy.types.Object.s_riser_height1 = FloatProperty(name="Riser Height", min=5.0 / METRIC_INCH, max=8.0 / METRIC_INCH,
                                                 default=7.4 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
bpy.types.Object.s_landing_depth1 = FloatProperty(name="Landing 2 Depth", min=36 / METRIC_INCH, max=60 / METRIC_INCH,
                                                  default=40 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
bpy.types.Object.s_over_front1 = FloatProperty(name="Front Overhang", min=0.0, max=1.25 / METRIC_INCH,
                                               default=1.0 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
bpy.types.Object.s_over_sides1 = FloatProperty(name="Side Overhang", min=0.0, max=2.0 / METRIC_INCH,
                                               default=1.0 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
bpy.types.Object.s_overhang1 = EnumProperty(items=(("1", "Normal", ""), ("2", "Right", ""), ("3", "Left", ""),
                                                   ("4", "Both", "")), default="1", description="Overhang Style",
                                            update=update_stairs, name="")
bpy.types.Object.s_is_back1 = BoolProperty(name="Turn Backwards?", default=False, update=update_stairs)
# winding
bpy.types.Object.s_w_rot = EnumProperty(name="", items=(("1", "-90", ""), ("2", "-45", ""), ("3", "45", ""),
                                                        ("4", "90", "")), default="3", update=update_stairs)
bpy.types.Object.s_num_rot = IntProperty(name="Stair To Begin Rotation On", update=update_stairs, min=1, max=13,
                                         default=6)
# spiral
bpy.types.Object.s_rot = FloatProperty(name="Total Rotation", unit="ROTATION", min=radians(-720), max=radians(720),
                                       default=radians(90), update=update_stairs)
bpy.types.Object.s_pole_dia = FloatProperty(name="Pole Diameter", min=3.0 / METRIC_INCH, max=10.0 / METRIC_INCH,
                                            default=4.0 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
bpy.types.Object.s_pole_res = IntProperty(name="Pole Resolution", min=8, max=64, default=16, update=update_stairs)
bpy.types.Object.s_tread_res = IntProperty(name="Tread Resolution", min=0, max=8, default=0, update=update_stairs)
# materials
bpy.types.Object.s_is_material = BoolProperty(name="Cycles Materials?", default=False,
                                              description="Adds Cycles Materials", update=delete_materials)
bpy.types.Object.s_is_preview = BoolProperty(name="Preview Material?", default=False,
                                             description="Preview Material On Object", update=preview_materials)
# stairs
bpy.types.Object.s_im_scale = FloatProperty(name="Image Scale", max=10.0, min=0.1, default=1.0,
                                            description="Change Image Scaling")
bpy.types.Object.s_col_image = StringProperty(name="", subtype="FILE_PATH", description="File Path For Color Image")
bpy.types.Object.s_is_bump = BoolProperty(name="Normal Map?", default=False, description="Add Normal To Material?")
bpy.types.Object.s_norm_image = StringProperty(name="", subtype="FILE_PATH",
                                               description="Filepath For Normal Map Image")
bpy.types.Object.s_bump_amo = FloatProperty(name="Normal Stength", min=0.001, max=2.000, default=0.250,
                                            description="Normal Map Strength")
bpy.types.Object.s_is_rotate = BoolProperty(name="Rotate Image?", default=False, description="Rotate Image 90 Degrees")
# pole/jacks
bpy.types.Object.s_im_scale2 = FloatProperty(name="Image Scale", max=10.0, min=0.1, default=1.0,
                                             description="Change Image Scaling")
bpy.types.Object.s_col_image2 = StringProperty(name="", subtype="FILE_PATH", description="File Path For Color Image")
bpy.types.Object.s_is_bump2 = BoolProperty(name="Normal Map?", default=False, description="Add Normal To Material?")
bpy.types.Object.s_norm_image2 = StringProperty(name="", subtype="FILE_PATH",
                                                description="Filepath For Normal Map Image")
bpy.types.Object.s_bump_amo2 = FloatProperty(name="Normal Stength", min=0.001, max=2.000, default=0.250,
                                             description="Normal Map Strength")
bpy.types.Object.s_is_rotate2 = BoolProperty(name="Rotate Image?", default=False, description="Rotate Image 90 Degrees")
# uv
bpy.types.Object.s_unwrap = BoolProperty(name="UV Unwrap?", default=True, description="UV Unwraps Siding",
                                         update=unwrap_stairs)
bpy.types.Object.s_random_uv = BoolProperty(name="Random UV's?", default=True, description="Random UV's",
                                            update=update_stairs)


class StairsPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_jarch_stairs"
    bl_label = "JARCH Vis: Stairs"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "JARCH Vis"
    
    def draw(self, context):
        layout = self.layout
        o = context.object
        if bpy.context.mode == "EDIT_MESH":
            layout.label("JARCH Vis Doesn't Work In Edit Mode", icon="ERROR")
        else:
            if o is not None:
                if o.s_object_add != "mesh":
                    if o.s_object_add == "add":
                        layout.label("Style:", icon="OBJECT_DATA")
                        layout.prop(o, "s_style")
                        layout.separator()
                        layout.prop(o, "s_width")
                        layout.separator()

                        if o.s_style != "3":
                            layout.prop(o, "s_num_steps")
                        else:
                            layout.prop(o, "s_num_steps2")

                        if o.s_style != "3":
                            layout.prop(o, "s_tread_width")

                        layout.prop(o, "s_riser_height")
                        h = round((o.s_num_steps * o.s_riser_height) + (1 / METRIC_INCH), 2)
                        if context.scene.unit_settings.system == "IMPERIAL":
                            layout.label("Height: " + str(round(((h * METRIC_INCH) / 12), 2)) + " ft", icon="INFO")
                            layout.separator()
                        else:
                            layout.label("Height: " + str(round(h, 2)) + " m", icon="INFO")
                            layout.separator()

                        if o.s_style == "1":
                            layout.prop(o, "s_is_set_in", icon="OOPS")

                            if not o.s_is_set_in:
                                layout.separator()
                                layout.prop(o, "s_is_custom_tread", icon="OBJECT_DATAMODE")
                                if o.s_is_custom_tread:
                                    layout.prop_search(o, "s_custom_tread", context.scene, "objects")
                                layout.separator()

                            if not o.s_is_set_in:
                                layout.prop(o, "s_is_close", icon="AUTOMERGE_ON")
                                layout.prop(o, "s_is_light", icon="OUTLINER_OB_LAMP")
                        if not o.s_is_set_in and o.s_style != "3":
                            layout.separator()
                            if o.s_style == "1":
                                layout.label("Overhang Style:", icon="OUTLINER_OB_SURFACE")
                                layout.prop(o, "s_overhang")
                            layout.prop(o, "s_over_front")

                            if o.s_overhang != "1":
                                layout.prop(o, "s_over_sides")
                            if o.s_style == "1":
                                layout.separator()
                                layout.prop(o, "s_is_riser", icon="TRIA_UP")
                            layout.separator()
                        else:
                            layout.prop(o, "s_over_front")
                            layout.separator()

                        if o.s_style == "1":  # normal stairs
                            layout.separator()
                            layout.prop(o, "s_num_land")
                            if o.s_num_land > 0:
                                layout.prop(o, "s_is_landing", icon="FULLSCREEN")

                            for i in range(int(o.s_num_land)):
                                layout.separator()
                                layout.separator()
                                box = layout.box()
                                box.label("Stair Set " + str(i + 2) + ":", icon="MOD_ARRAY")
                                box.separator()
                                box.prop(o, "s_num_steps" + str(i))

                                if o.s_is_custom_tread:
                                    box.prop(o, "s_tread_width" + str(i))
                                    box.prop(o, "s_riser_height" + str(i))

                                if i == 0:
                                    h2 = h + round((o.s_riser_height0 * o.s_num_steps0) + o.s_riser_height +
                                                   (1 / METRIC_INCH), 2)
                                    if context.scene.unit_settings.system == "IMPERIAL":
                                        box.label("Height: " + str(round(((h2 * METRIC_INCH) / 12), 2)) + " ft",
                                                  icon="INFO")
                                    else:
                                        box.label("Height: " + str(round(h2, 2)) + " m", icon="INFO")
                                else:
                                    h2 = h + round((o.s_riser_height0 * o.s_num_steps0) +
                                                   (o.s_riser_height0 * o.s_num_steps0) + (2 / METRIC_INCH) +
                                                   o.s_riser_height + o.s_riser_height0, 2)
                                    if context.scene.unit_settings.system == "IMPERIAL":
                                        box.label("Height: " + str(round(((h2 * METRIC_INCH) / 12), 2)) + " ft",
                                                  icon="INFO")
                                    else:
                                        box.label("Height: " + str(round(h2, 2)) + " m", icon="INFO")
                                box.separator()
                                box.label("Landing " + str(i + 1) + " Rotation:")
                                box.prop(o, "s_landing_rot" + str(i))

                                if (i == 0 and o.s_landing_rot0 != "1") or (i == 1 and o.s_landing_rot1 != "1"):
                                    box.prop(o, "s_is_back" + str(i), icon="LOOP_BACK")
                                box.prop(o, "s_landing_depth" + str(i))

                                if not o.s_is_set_in:
                                    box.separator()
                                    box.label("Overhang Style:", icon="OUTLINER_OB_SURFACE")
                                    box.prop(o, "s_overhang" + str(i))
                                    box.prop(o, "s_over_front" + str(i))
                                    if (i == 0 and o.s_overhang0 != "1") or (i == 1 and o.s_overhang1 != "1"):
                                        box.prop(o, "s_over_sides" + str(i))
                        elif o.s_style == "2":
                            layout.prop(o, "s_num_rot")
                            row = self.layout.row()
                            row.label("Rotation: ")
                            row.prop(o, "s_w_rot")
                        elif o.s_style == "3":
                            layout.prop(o, "s_rot", icon="MAN_ROT")
                            layout.prop(o, "s_tread_res")
                            layout.separator()
                            layout.prop(o, "s_pole_dia")
                            layout.prop(o, "s_pole_res")

                        layout.separator()
                        layout.prop(o, "s_unwrap", icon="GROUP_UVS")
                        if o.s_unwrap:
                            layout.prop(o, "s_random_uv", icon="RNDCURVE")
                        layout.separator()

                        if context.scene.render.engine == "CYCLES":
                            layout.prop(o, "s_is_material", icon="MATERIAL")
                        else:
                            layout.label("Materials Only Supported With Cycles", icon="POTATO")
                        layout.separator()

                        if o.s_is_material and context.scene.render.engine == "CYCLES":
                            box = layout.box()
                            box.label("Stairs:")
                            box.prop(o, "s_col_image", icon="COLOR")
                            box.prop(o, "s_is_bump", icon="SMOOTHCURVE")
                            box.separator()

                            if o.s_is_bump:
                                box.prop(o, "s_norm_image", icon="TEXTURE")
                                box.prop(o, "s_bump_amo")
                            box.prop(o, "s_im_scale", icon="MAN_SCALE")
                            box.prop(o, "s_is_rotate", icon="MAN_ROT")

                            layout.separator()
                            if o.s_style in ("1", "3"):
                                box = layout.box()
                                if o.s_style == "1":
                                    box.label("Jacks:")
                                else:
                                    box.label("Pole:")
                                box.prop(o, "s_col_image2", icon="COLOR")
                                box.prop(o, "s_is_bump2", icon="SMOOTHCURVE")
                                box.separator()

                                if o.s_is_bump2:
                                    box.prop(o, "s_norm_image2", icon="TEXTURE")
                                    box.prop(o, "s_bump_amo2")
                                box.prop(o, "s_im_scale2", icon="MAN_SCALE")
                                box.prop(o, "s_is_rotate2", icon="MAN_ROT")
                            layout.separator()
                            layout.operator("mesh.jarch_stairs_materials", icon="MATERIAL")

                        layout.separator()
                        layout.separator()
                        layout.operator("mesh.jarch_stairs_update", icon="FILE_REFRESH")
                        layout.operator("mesh.jarch_stairs_mesh", icon="OUTLINER_OB_MESH")
                        layout.operator("mesh.jarch_stairs_delete", icon="CANCEL")
                    else:
                        layout.operator("mesh.jarch_stairs_add", icon="MOD_ARRAY")
                else:
                    layout.label("This Is A Mesh JARCH Vis Object", icon="INFO")
            else:
                layout.operator("mesh.jarch_stairs_add", icon="MOD_ARRAY")


class StairsAdd(bpy.types.Operator):
    bl_idname = "mesh.jarch_stairs_add"
    bl_label = "Add Stairs"
    bl_description = "JARCH Vis: Stair Generator"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        o = context.object
        o.s_object_add = "add"
        return {"FINISHED"}


class StairsDelete(bpy.types.Operator):
    bl_idname = "mesh.jarch_stairs_delete"
    bl_label = "Delete Stairs"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        bpy.ops.object.delete()
        for i in bpy.data.materials:
            if i.users == 0:
                bpy.data.materials.remove(i)
        return {"FINISHED"}


class StairsUpdate(bpy.types.Operator):
    bl_idname = "mesh.jarch_stairs_update"
    bl_label = "Update Stairs"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        update_stairs(self, context)
        return {"FINISHED"}


class StairsMaterial(bpy.types.Operator):
    bl_idname = "mesh.jarch_stairs_materials"
    bl_label = "Generate\\Update Materials"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        stair_materials(self, context)
        return {"FINISHED"}


class StairsMesh(bpy.types.Operator):
    bl_idname = "mesh.jarch_stairs_mesh" 
    bl_label = "Convert To Mesh"
    bl_description = "Converts Stair Object To Normal Object (No Longer Editable)"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        o = context.object
        o.s_object_add = "mesh"
        return {"FINISHED"}


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
