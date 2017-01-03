import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty, IntProperty, FloatVectorProperty
from math import radians, atan, tan, cos, sqrt, asin
from mathutils import Euler, Vector
import bmesh
from random import uniform
from . jarch_materials import image_material
from . jarch_utils import point_rotation, METRIC_INCH


def custom_tread_placement(context, custom_tread_pos, custom_tread):
    #custom treads
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


def create_stairs(self, context, style, overhang, steps, tw, rh, of,os, w, n_landing, is_close, tw0, rh0, ld0, l_rot0,
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
            
            #calculate variables to pass in
            if i == 0:
                pass_in = [tw, rh, of, os, overhang, steps]
            elif i == 1:
                pass_in = [tw0, rh0, of0, os0, overhang0, steps0, l_rot0, ld0]
            elif i == 2:
                pass_in = [tw1, rh1, of1, os1, overhang1, steps1, l_rot1, ld1]
        
            # get step data
            verts_t, faces_t, cx, cy, cz, verts2_t, faces2_t, tread_pos = normal_stairs(self, context, pass_in[0],
                                                                                        pass_in[1], pass_in[2],
                                                                                        pass_in[3], w, pass_in[4],
                                                                                        pass_in[5], is_close, set_in,
                                                                                        is_riser, is_light, i,
                                                                                        is_custom_tread)
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
                pos = list(o.matric_world * Vector(pre_pos))  # * matrix
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
                    verts2, faces2 = stair_landing(self, context, w, pass_in[7], pass_in[1], orient, set_in, rot)
                    mesh3 = bpy.data.meshes.new("landing_" + str(i))
                    mesh3.from_pydata(verts2, [], faces2)
                    ob2 = bpy.data.objects.new("landing_" + str(i), mesh3)
                    context.scene.objects.link(ob2)
                    names.append(ob2.name)
                    pre_pos2[2] -= pass_in[1]
                    pos2 = list(o.matric_world * pre_pos2)
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
        verts, faces = winding_stairs(self, context, tw, rh, of, w, steps, is_close, angle, stair_to_rot)
    elif style == "3":
        verts, faces, verts2, faces2 = spiral_stairs(self, context, w, num_steps2, tw, rh, rot, of, tread_res, pd,
                                                     pole_res)
        mesh = bpy.data.meshes.new("pole_temp")
        mesh.from_pydata(verts2, [], faces2)
        ob4 = bpy.data.objects.new("pole_temp", mesh)
        context.scene.objects.link(ob4)
        ob4.location = context.object.location
        ob4.rotation_euler = context.object.rotation_euler
        names.append(ob4.name)
        o = context.object
        ob4.scale = o.scale

        if context.scene.render.engine == "CYCLES":
            if len(mats) >= 2:
                ob4.data.materials.append(bpy.data.materials[mats[1]])
            else:
                mat = bpy.data.materials.new("pole_temp")
                mat.use_nodes = True
                ob4.data.materials.append(mat)
                                     
    return verts, faces, names


def spiral_stairs(self, context, w, steps, tw, rh, rot, of, tread_res, pd, pole_res):
    verts = []; faces = []
    #calculate rotation per step
    ang = rot / (steps - 1); t = 1 / METRIC_INCH
    #other needed variables
    cur_ang = 0.0; hof = of / 2; cz = rh - t 
    #half of the tread width out at the end
    hh = w * tan(ang / 2); ih = of / (tread_res + 1)
    for step in range(steps - 1):        
        v = (); p = len(verts)
        points = [(0.0, -hof), (w, 0.0)]
        for i in range(tread_res): points.append((w, 0.0))
        points += ((w, 0.0), (0.0, hof))
        for i in range(tread_res): points.append((0.0, hof - (i * ih) - ih))
        counter = 0
        for i in points:
            if step != 0: e_rot = asin(of / w)
            else: e_rot = 0.0
            #if positive rotation
            if counter == 1 and rot >= 0: angle = cur_ang - e_rot
            elif counter == 2 + tread_res and rot >= 0: angle = cur_ang + ang
            #if negative rotation
            elif counter == 1 and rot < 0: angle = cur_ang + ang
            elif counter == 2 + tread_res and rot < 0: angle =  cur_ang
            #middle vertices
            elif counter > 1 and counter < 2 + tread_res and rot >= 0: angle = cur_ang + (((ang + e_rot) / (tread_res + 1)) * (counter - 1)) - e_rot
            elif counter > 1 and counter < 2 + tread_res and rot < 0: angle = (cur_ang + ang) - (((ang + e_rot) / (tread_res + 1)) * (counter - 1)) - e_rot
            else: angle = step * ang; angle += radians(180); angle *= -1; angle -= ang / 2                    
            x, y = point_rotation(i, (0.0, 0.0), angle)                
            v += ((x, y, cz), (x, y, cz + t)); counter += 1
        cz += rh; cur_ang += ang; f = []
        for vert in v: verts.append(vert)
        #faces
        #edge faces
        lp = p #local version of the number of vertices
        for i in range(4 + (tread_res * 2)):
            if i != 3 + (tread_res * 2): f.append((lp, lp + 2, lp + 3, lp + 1)) #if not last face
            else: f.append((lp, p, p + 1, lp + 1)) #if last face
            lp += 2 #update local p
        #calculate top faces
        op = []; ip = [p + 1]
        for i in range(p + 3, p + 3 + (tread_res * 2) + 4, 2): op.append(i)    
        for i in range(p + 7 + (tread_res * 4), p + 7 + (tread_res * 4) - (tread_res * 2) - 2, -2): ip.append(i)
        for i in range(tread_res + 1): f.append((ip[i], op[i], op[i + 1], ip[i + 1]))
        #bottom faces
        op = []; ip = [p]
        for i in range(p + 2, p + 2 + (tread_res * 2) + 4, 2): op.append(i)    
        for i in range(p + 6 + (tread_res * 4), p + 6 + (tread_res * 4) - (tread_res * 2) - 2, -2): ip.append(i)
        for i in range(tread_res + 1): f.append((ip[i], ip[i + 1], op[i + 1], op[i]))
        for face in f: faces.append(face)
    #pole
    cz -= rh - t; verts2 = []; faces2 = []
    ang = radians(360 / pole_res); v = []; z = 0.0; p = len(verts2)
    for i in range(2):
        for vs in range(pole_res):
            cur_ang = vs * ang
            x, y = point_rotation((pd / 2, 0.0), (0.0, 0.0), cur_ang)
            v.append((x, y, z))
        z += cz
    for vert in v: verts2.append(vert)
    #faces
    pr = pole_res
    for i in range(pole_res):
        if i != pole_res - 1:
            f = (p + i, p + i + 1, p + i + pr + 1, p + i + pr)
        else:
            f = (p + i, p, p + pr, p + i + pr)
        faces2.append(f)
    f = []
    for i in range(pole_res, pole_res * 2):
        f.append(p + i)
    faces2.append(f)
    
    return (verts, faces, verts2, faces2)         
                   
def winding_stairs(self, context, tw, rh, of, w, steps, is_close, w_rot, stair_to_rot):
    #create radians measures and round to 4 decimal places
    w_rot = round(w_rot, 4); r45 = round(radians(45), 4); r180 = round(radians(180), 4); r90 = round(radians(90), 4)
    #winding stairs
    verts = []; faces = []; inch = 1 / METRIC_INCH; str = stair_to_rot; tw -= of
    #figure out the distance farther to go on left or right side based on rotation
    if -r45 < w_rot < r45:
        gy = abs(w * tan(w_rot)); ex = 0.0
    else: gy = w; ex = w * tan(abs(w_rot) - r45)
    t = 1 / METRIC_INCH; gy += t
    #calculate number of steps on corner 
    if w_rot != 0.0:
        ti = 10 / METRIC_INCH
        c_steps = int((ti * abs(w_rot)) / (tw - inch))
    else: c_steps = 0
    ###needed variables###
    cx = 0.0; cy = 0.0; cz = 0.0; dy = str * tw; dz = str * rh; hw = w / 2; rh -= t
    ay = (steps - str - c_steps) * tw; az = (steps - str) * rh #ay is the distance from the corner to the top of the stairs
    temp_dw = sqrt((gy ** 2 + w ** 2)); temp_x = 0.0
    if -r45 <= w_rot <= r45: dw = temp_dw        
    else:
        if w_rot < 0: angle = w_rot + r45
        else: angle = w_rot - r45
        dw = temp_dw * cos(w_rot)                   
    #steps
    for step in range(steps):
        p = len(verts); face_type = None; v = ()
        if step + 1 < str: #before rotation            
            v = ((cx - hw, cy, cz), (cx - hw, cy + t, cz), (cx - hw, cy + t, cz + rh), (cx - hw, cy, cz + rh))
            v += ((cx + hw, cy, cz), (cx + hw, cy + t, cz), (cx + hw, cy + t, cz + rh), (cx + hw, cy, cz + rh)); cz += rh
            v += ((cx - hw, cy - of, cz), (cx - hw, cy + tw, cz), (cx - hw, cy + tw, cz + t), (cx - hw, cy - of, cz + t))
            v += ((cx + hw, cy - of, cz), (cx + hw, cy + tw, cz), (cx + hw, cy + tw, cz + t), (cx + hw, cy - of, cz + t)); cy += tw; face_type = "normal"            
        elif str <= step + 1 <= str + c_steps: #in rotation
            if -r45 <= w_rot <= r45:
                yp = (gy / (c_steps + 1)); y = yp * (step + 2 - str); y2 = yp * (step + 1 - str)
                if 0 < w_rot <= r45: #positive rotation                    
                    cx = hw; v = ((cx, cy, cz), (cx, cy, cz + rh), (cx - w, cy + y2, cz), (cx - w, cy + y2, cz + rh), (cx - w, cy + y2 + t, cz), (cx - w, cy + y2 + t, cz + rh), (cx, cy + t, cz), (cx, cy + t, cz + rh)); cz += rh
                    v += ((cx, cy - of, cz), (cx, cy - of, cz + t), (cx - w, cy + y2 - of, cz), (cx - w, cy + y2 - of, cz + t), (cx - w, cy + y, cz), (cx - w, cy + y, cz + t), (cx, cy + t, cz), (cx, cy + t, cz + t)); face_type = "pos"
                elif -r45 <= w_rot < 0: #negative rotation
                    cx = -hw; v = ((cx, cy, cz), (cx, cy, cz + rh), (cx + w, cy + y2, cz), (cx + w, cy + y2, cz + rh), (cx + w, cy + y2 + t, cz), (cx + w, cy + y2 + t, cz + rh), (cx, cy + t, cz), (cx, cy + t, cz + rh)); cz += rh 
                    v += ((cx, cy - of, cz), (cx, cy - of, cz + t), (cx + w, cy + y2 - of, cz), (cx + w, cy + y2 - of, cz + t), (cx + w, cy + y, cz), (cx + w, cy + y, cz + t), (cx, cy + t, cz), (cx, cy + t, cz + t)); face_type = "neg"
            else: #more than abs(45)
                ang = w_rot / (c_steps + 1); cs = step + 1 - str; cur_ang = ang * (step + 2 - str)
                if w_rot > 0: #positive rotation
                    if abs(cur_ang) <= r45:
                        y = (gy / r45) * abs(cur_ang); y2 = (gy / r45) * (abs(cur_ang - ang))
                        cx = hw; v = ((cx, cy, cz), (cx, cy, cz + rh), (cx - w, cy + y2, cz), (cx - w, cy + y2, cz + rh), (cx - w, cy + y2 + t, cz), (cx - w, cy + y2 + t, cz + rh), (cx, cy + t, cz), (cx, cy + t, cz + rh)); cz += rh
                        v += ((cx, cy - of, cz), (cx, cy - of, cz + t), (cx - w, cy - of, cz), (cx - w, cy - of, cz + t), (cx - w, cy + y, cz),  (cx - w, cy + y, cz + t), (cx, cy + t, cz), (cx, cy + t, cz + t)); face_type = "pos"
                    elif abs(cur_ang) > r45 and abs(cur_ang - ang) < r45: #step on corner
                        x = (ex / (abs(w_rot) - r45)) * (abs(cur_ang) - r45); y2 = (gy / r45) * (abs(cur_ang - ang)); x -= t; temp_x = x
                        cx = hw; v = ((cx, cy, cz), (cx, cy, cz + rh), (cx - w, cy + y2, cz), (cx - w, cy + y2, cz + rh), (cx - w, cy + y2 + t, cz), (cx - w, cy + y2 + t, cz + rh), (cx, cy + t, cz), (cx, cy + t, cz + rh)); cz += rh
                        v += ((cx, cy - of, cz), (cx, cy - of, cz + t), (cx - w, cy - of + y2, cz), (cx - w, cy - of + y2, cz + t), (cx - w, cy + gy, cz), (cx - w, cy + gy, cz + t), (cx - w + x, cy + gy, cz), (cx - w + x, cy + gy, cz + t))
                        v += ((cx, cy, cz), (cx, cy, cz + t)); face_type = "pos_tri"
                    else: #last step
                        points = ((cx, cy), (cx - w + temp_x - t, cy + gy - t), (cx - w + temp_x - t, cy + gy), (cx - t, cy)); counter = 0
                        points += ((cx + of, cy), (cx - w + temp_x - t, cy + gy - of - t), (cx - w + temp_x - t, cy + gy + ex - temp_x - t), (cx - t, cy))
                        for i in points:
                            if counter in (1, 2, 5, 6): origin = (cx - w + temp_x, cy + gy - t)
                            else: origin = (cx, cy)
                            x, y = point_rotation(i, origin, w_rot + r180)
                            if counter <= 3:
                                v += ((x, y, cz), (x, y, cz + rh))
                            else:
                                v += ((x, y, cz + rh), (x, y, cz + rh + t))
                            counter += 1
                        cz += rh; face_type = "pos"
                if w_rot < 0: #negative rotation
                    if abs(cur_ang) <= r45:
                        y = (gy / r45) * abs(cur_ang); y2 = (gy / r45) * (abs(cur_ang - ang))
                        cx = -hw; v = ((cx, cy, cz), (cx, cy, cz + rh), (cx + w, cy + y2, cz), (cx + w, cy + y2, cz + rh), (cx + w, cy + y2 + t, cz), (cx + w, cy + y2 + t, cz + rh), (cx, cy + t, cz), (cx, cy + t, cz + rh)); cz += rh
                        v += ((cx, cy - of, cz), (cx, cy - of, cz + t), (cx + w, cy - of, cz), (cx + w, cy - of, cz + t), (cx + w, cy + y, cz),  (cx + w, cy + y, cz + t), (cx, cy + t, cz), (cx, cy + t, cz + t)); face_type = "neg"
                    elif abs(cur_ang) > r45 and abs(cur_ang - ang) < r45: #step on corner
                        x = (ex / (abs(w_rot) - r45)) * (abs(cur_ang) - r45); y2 = (gy / r45) * (abs(cur_ang - ang)); x += t; temp_x = x
                        cx = -hw; v = ((cx, cy, cz), (cx, cy, cz + rh), (cx + w, cy + y2, cz), (cx + w, cy + y2, cz + rh), (cx + w, cy + y2 + t, cz), (cx + w, cy + y2 + t, cz + rh), (cx, cy + t, cz), (cx, cy + t, cz + rh)); cz += rh
                        v += ((cx, cy - of, cz), (cx, cy - of, cz + t), (cx + w, cy - of + y2, cz), (cx + w, cy - of + y2, cz + t), (cx + w, cy + gy, cz), (cx + w, cy + gy, cz + t), (cx + w - x, cy + gy, cz), (cx + w - x, cy + gy, cz + t))
                        v += ((cx, cy, cz), (cx, cy, cz + t)); face_type = "neg_tri"
                    else: #last step
                        points = ((cx, cy), (cx + w - temp_x + t, cy + gy - t), (cx + w - temp_x + t, cy + gy), (cx + t, cy)); counter = 0
                        points += ((cx - of, cy), (cx + w - temp_x + t, cy + gy - of - t), (cx + w - temp_x + t, cy + gy + ex - temp_x - t), (cx + t, cy))
                        for i in points:
                            if counter in (1, 2, 5, 6): origin = (cx + w - temp_x, cy + gy - t)
                            else: origin = (cx, cy)
                            x, y = point_rotation(i, origin, w_rot + r180)
                            if counter <= 3:
                                v += ((x, y, cz), (x, y, cz + rh))
                            else:
                                v += ((x, y, cz + rh), (x, y, cz + rh + t))
                            counter += 1
                        cz += rh; face_type = "neg"
        else: #after rotation            
            if step == str + c_steps: cy += t; cz += rh + t
            else: cz += t           
            cs = step - c_steps - str
            z = cz + (rh * cs); counter = 0
            if w_rot > 0:
                o2 = (cx - w + ex, cy + gy - t); face_type = "pos"
                points = ((cx, cy + (cs * tw) - of), (cx - w + ex, cy + (cs * tw) + gy - t - of), (cx - w + ex, cy + (cs * tw) + tw + gy - t), (cx, cy + (cs * tw) + tw))
                points += ((cx, cy + (cs * tw)), (cx - w + ex, cy + (cs * tw) + gy - t), (cx - w + ex, cy + (cs * tw) + gy), (cx, cy + (cs * tw) + t))
            else:
                o2 = (cx + w - ex, cy + gy - t); face_type = "neg"            
                points = ((cx, cy + (cs * tw) - of), (cx + w - ex, cy + (cs * tw) + gy - t - of), (cx + w - ex, cy + (cs * tw) + tw + gy - t), (cx, cy + (cs * tw) + tw))
                points += ((cx, cy + (cs * tw)), (cx + w - ex, cy + (cs * tw) + gy - t), (cx + w - ex, cy + (cs * tw) + gy), (cx, cy + (cs * tw) + t))
            for i in points:                
                if counter in (1, 2, 5, 6): origin = o2
                else: origin = (cx, cy)
                x, y = point_rotation(i, origin, w_rot + r180)
                if counter <= 3:
                    v += ((x, y, z), (x, y, z + t))
                else:                    
                    v += ((x, y, z - rh - t), (x, y, z))
                counter += 1                               
        for vert in v: verts.append(vert)
        f = ()
        if face_type == "normal":
            f = ((p, p + 4, p + 7, p + 3), (p, p + 3, p + 2, p + 1), (p + 1, p + 2, p + 6, p + 5), (p + 2, p + 3, p + 7, p + 6), (p, p + 4, p + 5, p + 1), (p + 4, p + 5, p + 6, p + 7),
                    (p + 8, p + 11, p + 10, p + 9), (p + 8, p + 12, p + 15, p + 11), (p + 12, p + 13, p + 14, p + 15), (p + 14, p + 13, p + 9, p + 10), (p + 11, p + 15, p + 14, p + 10), (p + 8, p + 12, p + 13, p + 9))         
        elif face_type == "pos":
            for i in range(2):                
                f += ((p, p + 6, p + 7, p + 1), (p, p + 1, p + 3, p + 2), (p + 2, p + 3, p + 5, p + 4), (p + 4, p + 5, p + 7, p + 6), (p + 1, p + 7, p + 5, p + 3), (p, p + 2, p + 4, p + 6)); p += 8
        elif face_type == "neg":
            for i in range(2):                
                f += ((p, p + 1, p + 7, p + 6), (p, p + 2, p + 3, p + 1), (p + 2, p + 4, p + 5, p + 3), (p + 4, p + 6, p + 7, p + 5), (p + 1, p + 3, p + 5, p + 7), (p, p + 6, p + 4, p + 2)); p += 8
        elif face_type == "pos_tri":            
            f += ((p, p + 6, p + 7, p + 1), (p, p + 1, p + 3, p + 2), (p + 2, p + 3, p + 5, p + 4), (p + 4, p + 5, p + 7, p + 6), (p + 1, p + 7, p + 5, p + 3), (p, p + 2, p + 4, p + 6)); p += 8
            f += ((p, p + 8, p + 9, p + 1), (p + 1, p + 9, p + 7, p + 3), (p + 3, p + 7, p + 5), (p, p + 1, p + 3, p + 2), (p + 6, p + 7, p + 9, p + 8), (p + 4, p + 5, p + 7, p + 6), (p + 2, p + 3, p + 5, p + 4), (p, p + 2, p + 6, p + 8), (p + 2, p + 4, p + 6))            
        elif face_type == "neg_tri":
            f += ((p, p + 1, p + 7, p + 6), (p, p + 2, p + 3, p + 1), (p + 2, p + 4, p + 5, p + 3), (p + 4, p + 6, p + 7, p + 5), (p + 1, p + 3, p + 5, p + 7), (p, p + 6, p + 4, p + 2)); p += 8
            f += ((p, p + 1, p + 9, p + 8), (p + 1, p + 3, p + 7, p + 9), (p + 3, p + 5, p + 7), (p, p + 2, p + 3, p + 1), (p + 6, p + 8, p + 9, p + 7), (p + 4, p + 6, p + 7, p + 5), (p + 2, p + 4, p + 5, p + 3), (p, p + 8, p + 6, p + 2), (p + 2, p + 6, p + 4)) 
        for face in f: faces.append(face)
             
                
    return (verts, faces)
    

def stair_landing(self, context, w, depth, riser, type, set_in, rot):
    hw = w / 2; verts = []; faces = []; p = 0
    if type == "straight":
        #if set_in == False and rot in (0, 360):
         #   depth += 1 / METRIC_INCH
        v = ((-hw, 0.0, 0.0), (-hw, 0.0, riser), (-hw, depth, 0.0), (-hw, depth, riser), (hw, depth, 0.0), (hw, depth, riser), (hw, 0.0, 0.0), (hw, 0.0, riser))
    elif type == "left":
        v = ((-hw - w, 0.0, 0.0), (-hw - w, 0.0, riser), (-hw - w, depth, 0.0), (-hw - w, depth, riser), (hw, depth, 0.0), (hw, depth, riser), (hw, 0.0, 0.0), (hw, 0.0, riser))
    elif type == "right":
        v = ((-hw, 0.0, 0.0), (-hw, 0.0, riser), (-hw, depth, 0.0), (-hw, depth, riser), (hw + w, depth, 0.0), (hw + w, depth, riser), (hw + w, 0.0, 0.0), (hw + w, 0.0, riser))
    for vert in v: verts.append(vert)
    f = ((p, p + 1, p + 3, p + 2), (p + 1, p + 7, p + 5, p + 3), (p + 4, p + 5, p + 7, p + 6), (p, p + 2, p + 4, p + 6), (p + 2, p + 3, p + 5, p + 4), (p, p + 6, p + 7, p + 1))
    for face in f: faces.append(face)
    return (verts, faces) 

def normal_stairs(self, context, tw, rh, of, os, w, overhang, steps, is_close, set_in, is_riser, is_light, landing, is_custom_tread):
    tw -= of
    verts = []; faces = []; inch = 1 / METRIC_INCH
    #figure number of jacks
    if set_in == True: jack_type = "set_in"; jack_num = 2
    elif is_close == True: jack_num = int(w / 0.3048); jack_type = "normal"
    else: jack_type = "normal"; jack_num = int(w / 0.3048)
    #space if light
    if is_light == True and jack_type == "normal" and jack_num % 2 != 0:
        jack_num += 1
    tread = tw; riser = rh; over_front = of; over_sides = os; t_steps = steps; ov = overhang
    #create jacks
    cx = -(w / 2); thick = 0.0508; t = thick
    space = (w - thick) / (jack_num - 1) #current x, thickness, space between jacks
    
    ###set_in variables###
    if jack_type == "set_in":
        riser -= t
        ty = (t * tread) / (riser + t)
        ow = tread + tread + ty; width = tread + (2 * ty)           
    for jack in range(jack_num): #each jack
        extra = 6 / METRIC_INCH; t_height = t_steps * riser; t_depth = t_steps * tread - inch
        #amount gained on y and z axis because of jack slope
        angle = atan((t_height - extra) / (t_depth - extra))
        gz = riser - ((tread - extra) * tan(angle))
        if jack_type != "set_in":
            if is_riser == False: cy = 0.0
            else: cy = inch
        else:
            cy = 0.0
        #calculate line slope
        if is_close == False or (jack != 0 and jack != jack_num - 1):
            point = [extra + cy, 0.0]; point_1 = [tread * t_steps + cy - inch, (riser * t_steps) - extra]
            slope = (point[1] - point_1[1]) / (point[0] - point_1[0])
            b = point[1] - (slope * point[0])
        elif (jack == 0 or jack == jack_num - 1) and is_close == True:
            b = 0.0; slope = 0.0
        last = 0.0; out_faces = []
        if is_close == True and jack in (0, jack_num - 1): last = t_height - extra;
        #stairs
        cz = riser; sy = cy             
        for stair in range(t_steps):
            face_type = "normal"; p = len(verts)
            if jack_type == "normal":
                if stair == 0:
                    #first step
                    z = (slope * (cy + tread)) + b
                    v = ((cx, cy, cz - riser), (cx + t, cy, cz - riser), (cx, cy, cz), (cx + t, cy, cz), (cx, cy + tread, cz), (cx + t, cy + tread, cz))
                    v += ((cx, cy + tread, z), (cx + t, cy + tread, z), (cx, cy + extra, cz - riser), (cx + t, cy + extra, cz - riser))
                    face_type = "first"                    
                elif stair == t_steps - 1:
                    #last step                        
                    v = ((cx, cy, cz), (cx + t, cy, cz), (cx, cy + tread - inch, cz), (cx + t, cy + tread - inch, cz), (cx, cy + tread - inch, cz - extra - last), (cx + t, cy + tread - inch, cz - extra - last))
                else:
                    #other steps
                    z = (slope * (cy + tread)) + b
                    v = ((cx, cy, cz), (cx + t, cy, cz), (cx, cy + tread, cz), (cx + t, cy + tread, cz), (cx, cy + tread, z), (cx + t, cy + tread, z))                
                for vert in v:
                    verts.append(vert)
                if face_type == "first":
                    f = [(p, p + 1, p + 3, p + 2), (p + 2, p + 3, p + 5, p + 4), (p, p + 2, p + 4, p + 6), (p + 1, p + 7, p + 5, p + 3),
                            (p + 6, p + 7, p + 9, p + 8), (p, p + 8, p + 9, p + 1), (p, p + 6, p + 8), (p + 1, p + 9, p + 7)]
                else:
                    if stair == 1:
                        f = [(p, p + 1, p + 3, p + 2), (p, p + 2, p + 4, p - 6), (p - 6, p + 4, p - 4), (p, p - 6, p - 5, p + 1),
                                (p + 1, p - 5, p + 5, p + 3), (p - 5, p - 3, p + 5), (p - 3, p - 4, p + 4, p + 5)]
                    else:
                        f = [(p, p + 1, p + 3, p + 2), (p, p + 2, p + 4, p - 4), (p - 4, p + 4, p - 2), (p, p - 4, p - 3, p + 1),
                                (p + 1, p - 3, p + 5, p + 3), (p - 3, p - 1, p + 5), (p - 1, p - 2, p + 4, p + 5)]
                if stair == t_steps - 1:
                    if t_steps == 1:
                        f.append((p + 4, p + 5, p + 7, p + 6))
                    else:
                        f.append((p + 2, p + 3, p + 5, p + 4))
                for face in f:
                    faces.append(face)                   
                #update variables 
                cy += tread; cz += riser
            elif jack_type == "set_in":
                face_type = "normal"; p = len(verts)
                if stair == 0:
                    if landing != 0: cy = -tread
                    else: cy = 0.0
                    cz = 0.0
                    if landing != 0:
                        v = ((cx, cy + tread, cz), (cx + inch, cy + tread, cz), (cx + t, cy + tread, cz), (cx, cy + tread, cz + riser), (cx + inch, cy + tread, cz + riser), (cx + t, cy + tread, cz + riser))    
                    else:                                                         
                        v = ((cx, cy, cz), (cx + inch, cy, cz), (cx + t, cy, cz), (cx, cy + tread - ty, cz + riser), (cx + inch, cy + tread - ty, cz + riser), (cx + t, cy + tread - ty, cz + riser))
                    v += ((cx, cy + tread, cz + riser + t), (cx + inch, cy + tread, cz + riser + t), (cx + t, cy + tread, cz + riser + t), (cx, cy + ow, cz + riser + t))
                    v += ((cx + inch, cy + ow, cz + riser + t), (cx + t, cy + ow, cz + riser + t), (cx, cy + ow - ty, cz + riser), (cx + inch, cy + ow - ty, cz + riser), (cx + t, cy + ow - ty, cz + riser))
                    v += ((cx, cy + width - ty, cz), (cx + inch, cy + width - ty, cz), (cx + t, cy + width - ty, cz)); cy += tread + tread - ty; cz += riser + riser + t
                    if jack == 0: face_type = "first"
                    else: face_type = "first_right"
                elif stair == t_steps - 1: #last step
                    v = ((cx, cy, cz), (cx + inch, cy, cz), (cx + t, cy, cz), (cx, cy + ty, cz + t), (cx + inch, cy + ty, cz + t), (cx + t, cy + ty, cz + t))
                    v += ((cx, cy + width - ty, cz + t), (cx + inch, cy + width - ty, cz + t), (cx + t, cy + width - ty, cz + t))
                    v += ((cx, cy + tread + ty, cz), (cx + inch, cy + tread + ty, cz), (cx + t, cy + tread + ty, cz)); cz += riser + t + t; cy += tread + ty
                    v += ((cx, cy, cz), (cx + inch, cy, cz), (cx + t, cy, cz))
                    if jack == 0: face_type = "last"
                    else: face_type = "last_right"                    
                else: #normal steps                    
                    v = ((cx, cy, cz), (cx + inch, cy, cz), (cx + t, cy, cz), (cx, cy + ty, cz + t), (cx + inch, cy + ty, cz + t), (cx + t, cy + ty, cz + t))
                    v += ((cx, cy + width, cz + t), (cx + inch, cy + width, cz + t), (cx + t, cy + width, cz + t))
                    v += ((cx, cy + tread + ty, cz), (cx + inch, cy + tread + ty, cz), (cx + t, cy + tread + ty, cz))
                    cy += tread; cz += riser + t
                    if jack != 0: face_type = "normal_right"                      
                for vert in v: verts.append(vert)
                #faces
                f = ()
                if face_type == "first":
                    f = [(p, p + 3, p + 12, p + 15), (p, p + 1, p + 4, p + 3), (p + 1, p + 2, p + 5, p + 4), (p + 2, p + 17, p + 14, p + 5), (p + 16, p + 13, p + 14, p + 17),
                            (p + 15, p + 12, p + 13, p + 16), (p, p + 15, p + 16, p + 1), (p + 1, p + 16, p + 17, p + 2), (p + 3, p + 4, p + 7, p + 6), (p + 4, p + 5, p + 14, p + 13),
                            (p + 4, p + 13, p + 10, p + 7), (p + 12, p + 9, p + 10, p + 13), (p + 3, p + 6, p + 9, p + 12)]
                    if t_steps != 1: f.append((p + 7, p + 10, p + 11, p + 8))
                    else: f.append((p + 6, p + 7, p + 10, p + 9))
                elif face_type == "first_right":
                    f = [(p, p + 3, p + 12, p + 15), (p, p + 1, p + 4, p + 3), (p + 1, p + 2, p + 5, p + 4), (p + 2, p + 17, p + 14, p + 5), (p + 16, p + 13, p + 14, p + 17),
                            (p + 15, p + 12, p + 13, p + 16), (p + 4, p + 5, p + 8, p + 7), (p + 5, p + 14, p + 11, p + 8), (p + 14, p + 13, p + 10, p + 11),
                            (p + 12, p + 3, p + 4, p + 13), (p + 4, p + 7, p + 10, p + 13), (p, p + 15, p + 16, p + 1), (p + 1, p + 16, p + 17, p + 2)]
                    if t_steps != 1: f.append((p + 6, p + 9, p + 10, p + 7))
                    else: f.append((p + 7, p + 8, p + 11, p + 10))
                elif face_type == "normal":
                    if stair == 1:
                        f = ((p, p - 12, p - 11, p + 1), (p + 1, p - 11, p - 10, p + 2), (p + 2, p - 10, p - 7, p + 11), (p - 8, p + 10, p + 11, p - 7), (p - 9, p + 9, p + 10, p - 8),
                                (p, p + 9, p - 9, p - 12), (p, p + 1, p + 4, p + 3), (p + 1, p + 2, p + 11, p + 10), (p + 1, p + 10, p + 7, p + 4), (p + 4, p + 7, p + 8, p + 5),
                                (p + 6, p + 7, p + 10, p + 9), (p, p + 3, p + 6, p + 9))
                    else:
                        f = ((p, p - 9, p - 8, p + 1), (p + 1, p - 8, p - 7, p + 2), (p - 7, p - 4, p + 11, p + 2), (p - 4, p - 5, p + 10, p + 11), (p - 5, p - 6, p + 9, p + 10),
                                (p, p + 9, p - 6, p - 9), (p, p + 1, p + 4, p + 3), (p + 1, p + 2, p + 11, p + 10), (p + 1, p + 10, p + 7, p + 4), (p + 4, p + 7, p + 8, p + 5),
                                (p + 6, p + 7, p + 10, p + 9), (p, p + 3, p + 6, p + 9))
                elif face_type == "normal_right":
                    if stair == 1:
                        f = ((p, p - 12, p - 11, p + 1), (p + 1, p - 11, p - 10, p + 2), (p + 2, p - 10, p - 7, p + 11), (p - 8, p + 10, p + 11, p - 7), (p - 9, p + 9, p + 10, p - 8),
                                (p, p + 9, p - 9, p - 12), (p + 1, p + 2, p + 5, p + 4), (p + 2, p + 11, p + 8, p + 5), (p + 7, p + 8, p + 11, p + 10), (p, p + 1, p + 10, p + 9),
                                (p + 1, p + 4, p + 7, p + 10), (p + 3, p + 6, p + 7, p + 4))
                    else:
                        f = ((p, p - 9, p - 8, p + 1), (p + 1, p - 8, p - 7, p + 2), (p - 7, p - 4, p + 11, p + 2), (p - 4, p - 5, p + 10, p + 11), (p - 5, p - 6, p + 9, p + 10),
                                (p, p + 9, p - 6, p - 9), (p + 1, p + 2, p + 5, p + 4), (p + 2, p + 11, p + 8, p + 5), (p + 7, p + 8, p + 11, p + 10), (p, p + 1, p + 10, p + 9),
                                (p + 1, p + 4, p + 7, p + 10), (p + 3, p + 6, p + 7, p + 4))                        
                elif face_type == "last":                    
                    f = ((p, p - 9, p - 8, p + 1), (p + 1, p - 8, p - 7, p + 2), (p - 7, p - 4, p + 11, p + 2), (p - 4, p - 5, p + 10, p + 11), (p - 5, p - 6, p + 9, p + 10),
                            (p, p + 9, p - 6, p - 9), (p, p + 1, p + 4, p + 3), (p + 1, p + 2, p + 11, p + 10), (p + 1, p + 10, p + 7, p + 4), (p + 4, p + 7, p + 8, p + 5),
                            (p + 6, p + 7, p + 10, p + 9), (p, p + 3, p + 6, p + 9))
                elif face_type == "last_right":
                    f = ((p, p - 9, p - 8, p + 1), (p + 1, p - 8, p - 7, p + 2), (p - 7, p - 4, p + 11, p + 2), (p - 4, p - 5, p + 10, p + 11), (p - 5, p - 6, p + 9, p + 10),
                            (p, p + 9, p - 6, p - 9), (p + 1, p + 2, p + 5, p + 4), (p + 2, p + 11, p + 8, p + 5), (p + 7, p + 8, p + 11, p + 10), (p, p + 1, p + 10, p + 9),
                            (p + 1, p + 4, p + 7, p + 10), (p + 3, p + 6, p + 7, p + 4))
                if face_type in ("last_right", "last"):
                    f += ((p + 3, p + 4, p + 13, p + 12), (p + 4, p + 5, p + 14, p + 13), (p + 5, p + 8, p + 14), (p + 7, p + 13, p + 14, p + 8), (p + 6, p + 12, p + 13, p + 7), (p + 3, p + 12, p + 6))                                              
                for face in f: faces.append(face)
        #update variables
        cx += space
    verts1 = verts[:]; faces1 = faces[:]; verts = []; faces = []
    custom_tread_pos = []                 
    #treads and risers
    ry = cy   
    cx = 0.0; cy = sy; cz = 0.0; hw = w / 2
    if jack_type == "normal":
        if overhang == "4": left = hw + os; right = hw + os #both
        elif overhang == "2": left = hw; right = hw + os #right
        elif overhang == "3": left = hw + os; right = hw #left
        else: left = hw; right = hw #normal
        #front
        if is_riser == True:
            front = of + inch
        else:
            front = of
        #steps
        for step in range(t_steps):
            if is_riser == False: e = 0.0
            else: e = inch
            p = len(verts)
            
            #risers
            if is_riser == True:
                v = ((cx - hw, cy, cz), (cx - hw, cy - inch, cz), (cx - hw, cy, cz + riser), (cx - hw, cy - inch, cz + riser))
                v += ((cx + hw, cy, cz + riser), (cx + hw, cy - inch, cz + riser), (cx + hw, cy, cz), (cx + hw, cy - inch, cz))
                for vert in v: verts.append(vert)                
                f = ((p, p + 1, p + 3, p + 2), (p + 1, p + 7, p + 5, p + 3), (p + 4, p + 5, p + 7, p + 6), (p, p + 2, p + 4, p + 6), (p + 2, p + 3, p + 5, p + 4), (p, p + 6, p + 7, p + 1))
                for face in f: faces.append(face)
                p += 8
            cz += riser
            #treads
            if is_custom_tread == False:
                v = ((cx - left, cy - front, cz), (cx - left, cy - front, cz + inch), (cx - left, cy + tread - e, cz), (cx - left, cy + tread - e, cz + inch))
                v += ((cx + right, cy + tread - e, cz), (cx + right, cy + tread - e, cz + inch), (cx + right, cy - front, cz), (cx + right, cy - front, cz + inch))
                for vert in v: verts.append(vert)
                f = ((p, p + 1, p + 3, p + 2), (p + 1, p + 7, p + 5, p + 3), (p + 4, p + 5, p + 7, p + 6), (p, p + 2, p + 4, p + 6), (p + 2, p + 3, p + 5, p + 4), (p, p + 6, p + 7, p + 1))
                for face in f: faces.append(face)
                
            #custom tread
            else:
                custom_tread_pos.append([cx, cy + tread - e, cz]) 
            cy += tread
        ry -= inch
    elif jack_type == "set_in":
        hw -= inch; cz += riser
        if landing == 0: cy += tread
        else: cy = 0.0
        for step in range(t_steps):
            p = len(verts)
            v = ((cx - hw, cy, cz), (cx - hw, cy, cz + t), (cx - hw, cy + tread, cz), (cx - hw, cy + tread, cz + t))
            v += ((cx + hw, cy + tread, cz), (cx + hw, cy + tread, cz + t), (cx + hw, cy, cz), (cx + hw, cy, cz + t))
            for vert in v: verts.append(vert)
            f = ((p, p + 1, p + 3, p + 2), (p + 1, p + 7, p + 5, p + 3), (p + 4, p + 5, p + 7, p + 6), (p, p + 2, p + 4, p + 6), (p + 2, p + 3, p + 5, p + 4), (p, p + 6, p + 7, p + 1))
            for face in f: faces.append(face) 
            cz += t + riser; cy += tread        
        t_height += t * t_steps + t - inch

    return verts, faces, 0.0, ry, t_height + riser, verts1, faces1, custom_tread_pos

def UpdateStairs(self, context):
    o = context.object; mats = []
    
    #collect materials to reapply after mesh update
    for i in o.data.materials:
        mats.append(i.name)
    
    #create stairs    
    verts, faces, names = create_stairs(self, context, o.s_style, o.s_overhang, o.s_num_steps, o.s_tread_width, o.s_riser_height, o.s_over_front, o.s_over_sides, o.s_width,
            o.s_num_land, o.s_is_close, o.s_tread_width0, o.s_riser_height0, o.s_landing_depth0, o.s_landing_rot0, o.s_over_front0, o.s_over_sides0, o.s_overhang0, o.s_is_back0,
            o.s_landing_rot1, o.s_tread_width1, o.s_riser_height1, o.s_landing_depth1, o.s_over_front1, o.s_over_sides1, o.s_overhang1, o.s_is_back1, o.s_w_rot, o.s_num_rot, o.s_rot,
            o.s_num_steps0, o.s_num_steps1, o.s_is_set_in, o.s_is_riser, o.s_is_landing, o.s_is_light, o.s_num_steps2, o.s_tread_res, o.s_pole_dia, o.s_pole_res,
            o.s_is_custom_tread, o.s_custom_tread)
    
    #update mesh
    emesh = o.data
    mesh = bpy.data.meshes.new(name = "siding")
    mesh.from_pydata(verts, [], faces)
    mesh.update(calc_edges = True)
    
    for i in bpy.data.objects:
        if i.data == emesh:
            i.data = mesh
    
    emesh.user_clear()
    bpy.data.meshes.remove(emesh)
    
    if context.scene.render.engine == "CYCLES":
        if len(mats) >= 1:
            mat = bpy.data.materials[mats[0]]; o.data.materials.append(mat)
        else:
            mat = bpy.data.materials.new("stairs_temp"); mat.use_nodes = True; o.data.materials.append(mat)
              
    #join objects if needed
    if names != []:
        for name in names:
            ob = bpy.data.objects[name]; o.select = False; ob.select = True; o.select = True; context.scene.objects.active = o
            bpy.ops.object.join()
    if o.s_unwrap == True:
        UnwrapStairs(self, context)
        if o.s_random_uv == True:
            RandomUV(self, context)
    for i in mats:
        if i not in o.data.materials:
            mat = bpy.data.materials[i]; o.data.materials.append(mat)
    for i in bpy.data.materials: #remove unused materials
        if i.users == 0: bpy.data.materials.remove(i)
            
def StairsMaterials(self, context):
    o = context.object
    if context.scene.render.engine == "CYCLES":
        #run file checker
        error = False
        if o.s_col_image == "": error = True
        if o.s_norm_image == "" and o.s_is_bump == True: error = True
        #check if first image is empty
        if error == False and len(o.data.materials) >= 1:
            mat = image_material(bpy, context, o.s_im_scale, o.s_col_image, o.s_norm_image, o.s_bump_amo, o.s_is_bump, "stairs_temp_" + o.name, True, 0.1, 0.05, o.s_is_rotate, None)
            if mat != None:
                o.data.materials[0] = mat.copy(); o.data.materials[0].name = "stairs_" + o.name
            else: self.report({"ERROR"}, "Images Not Found, Make Sure Path Is Correct")
        else:
            self.report({"ERROR"}, "First Material Invalid, Try Updating Object")
        #second material
        if o.s_style in ("1", "3"):
            error2 = False
            if o.s_col_image2 == "": error2 = True
            if o.s_norm_image2 == "" and o.s_is_bump2 == True: error2 = True
            if error2 == False and len(o.data.materials) >= 2:
                mat = image_material(bpy, context, o.s_im_scale2, o.s_col_image2, o.s_norm_image2, o.s_bump_amo2, o.s_is_bump2, "second_temp_" + o.name, True, 0.1, 0.05, o.s_is_rotate2, None)
                if mat != None:
                    o.data.materials[1] = mat.copy()
                    if o.s_style == "1": o.data.materials[1].name = "jacks_" + o.name
                    else: o.data.materials[1].name = "pole_" + o.name
                else: self.report({"ERROR"}, "Images Not Found, Make Sure Path Is Correct")
            else:
                self.report({"ERROR"}, "Second Material Invalid, Try Updating Object")
        for i in bpy.data.materials: #remove unused materials
            if i.users == 0: bpy.data.materials.remove(i)
    else:
        self.report({"ERROR"}, "Render Engine Must Be Cycles")
       
def UnwrapStairs(self, context):
    o = context.object
    #uv unwrap
    for i in bpy.data.objects: i.select = False
    o.select = True; bpy.context.scene.objects.active = o    
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    bpy.ops.object.editmode_toggle()
                    override = bpy.context.copy(); override["area"] = area; override["region"] = region; override["active_object"] = (bpy.context.selected_objects)[0]
                    bpy.ops.mesh.select_all(action = "SELECT"); bpy.ops.uv.cube_project(override); bpy.ops.object.editmode_toggle()

def RandomUV(self, context):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    bpy.ops.object.editmode_toggle()
                    bpy.ops.mesh.select_all(action = "SELECT")
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
                        
def DeleteMaterials(self, context):
    o = context.object
    if o.s_is_material == False and o.s_mat != "2":
        for i in o.data.materials:
            bpy.ops.object.material_slot_remove()
        for i in bpy.data.materials:
            if i.users == 0:
                bpy.data.materials.remove(i)
                
def PreviewMaterials(self, context):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    if bpy.context.object.f_is_preview == True: space.viewport_shade = 'RENDERED'
                    else: space.viewport_shade = "SOLID"
                    
            
#properties
#setup
bpy.types.Object.s_object_add = StringProperty(default = "none", update = UpdateStairs)
#style
bpy.types.Object.s_style = EnumProperty(items = (("1", "Normal", ""), ("2", "Winding", ""), ("3", "Spiral", "")),
        default = "1", description = "Stair Style", update = UpdateStairs, name = "")
bpy.types.Object.s_overhang = EnumProperty(items = (("1", "Normal", ""), ("2", "Right", ""), ("3", "Left", ""), ("4", "Both", "")), 
        default = "1", description = "Overhang Style", update = UpdateStairs, name = "")
#common variables
bpy.types.Object.s_num_steps = IntProperty(name = "Number Of Steps", min = 1, max = 24, default = 13, update = UpdateStairs)
bpy.types.Object.s_num_steps2 = IntProperty(name = "Number Of Steps", min = 1, max = 48, default = 13, update = UpdateStairs)
bpy.types.Object.s_tread_width = FloatProperty(name = "Tread Width", min = 9.0 / METRIC_INCH, max = 16.0 / METRIC_INCH, default = 9.5 / METRIC_INCH, subtype = "DISTANCE", update = UpdateStairs)
bpy.types.Object.s_riser_height = FloatProperty(name = "Riser Height", min = 5.0 / METRIC_INCH, max = 8.0 / METRIC_INCH, default = 7.4 / METRIC_INCH, subtype = "DISTANCE", update = UpdateStairs)
bpy.types.Object.s_over_front = FloatProperty(name = "Front Overhang", min = 0.0, max = 1.25 / METRIC_INCH, default = 1.0 / METRIC_INCH, subtype = "DISTANCE", update = UpdateStairs)
bpy.types.Object.s_over_sides = FloatProperty(name = "Side Overhang", min = 0.0, max = 2.0 / METRIC_INCH, default = 1.0 / METRIC_INCH, subtype = "DISTANCE", update = UpdateStairs)
bpy.types.Object.s_width = FloatProperty(name = "Stair Width", min = 36.0 / METRIC_INCH, max = 60.0 / METRIC_INCH, default = 40.0 / METRIC_INCH, subtype = "DISTANCE", update = UpdateStairs)
bpy.types.Object.s_is_riser = BoolProperty(name = "Risers?", default = True, update = UpdateStairs)
bpy.types.Object.s_is_custom_tread = BoolProperty(name = "Custom Treads?", default = False, update = UpdateStairs)
bpy.types.Object.s_custom_tread = StringProperty(name = "Custom Tread", default = "", update = UpdateStairs)
#normal style
bpy.types.Object.s_num_land = IntProperty(name = "Number Of Landings", min = 0, max = 2, default = 0, update = UpdateStairs)
bpy.types.Object.s_is_close = BoolProperty(name = "Close Sides?", default = False, update = UpdateStairs)
bpy.types.Object.s_is_set_in = BoolProperty(name = "Set Steps In?", default = False, update = UpdateStairs)
bpy.types.Object.s_is_landing = BoolProperty(name = "Create Landings?", default = True, update = UpdateStairs)
bpy.types.Object.s_is_light = BoolProperty(name = "Allow Recessed Lights?", default = False, update = UpdateStairs, description = "Space Middle Step Jacks To Allow Recessed Lights")
#landing 0
bpy.types.Object.s_num_steps0 = IntProperty(name = "Number Of Steps", min = 1, max = 24, default = 13, update = UpdateStairs)
bpy.types.Object.s_tread_width0 = FloatProperty(name = "Tread Width", min = 9.0 / METRIC_INCH, max = 16.0 / METRIC_INCH, default = 9.5 / METRIC_INCH,  subtype = "DISTANCE", update = UpdateStairs)
bpy.types.Object.s_riser_height0 = FloatProperty(name = "Riser Height", min = 5.0 / METRIC_INCH, max = 8.0 / METRIC_INCH, default = 7.4 / METRIC_INCH, subtype = "DISTANCE", update = UpdateStairs)
bpy.types.Object.s_landing_depth0 = FloatProperty(name = "Landing 1 Depth", min = 36 / METRIC_INCH, max = 60 / METRIC_INCH, default = 40 / METRIC_INCH, subtype = "DISTANCE", update = UpdateStairs)
bpy.types.Object.s_landing_rot0 = EnumProperty(items = (("1", "Forwards", ""), ("2", "Left", ""), ("3", "Right", "")), update = UpdateStairs, name = "")
bpy.types.Object.s_over_front0 = FloatProperty(name = "Front Overhang", min = 0.0, max = 1.25 / METRIC_INCH, default = 1.0 / METRIC_INCH, subtype = "DISTANCE", update = UpdateStairs)
bpy.types.Object.s_over_sides0 = FloatProperty(name = "Side Overhang", min = 0.0, max = 2.0 / METRIC_INCH, default = 1.0 / METRIC_INCH, subtype = "DISTANCE", update = UpdateStairs)
bpy.types.Object.s_overhang0 = EnumProperty(items = (("1", "Normal", ""), ("2", "Right", ""), ("3", "Left", ""), ("4", "Both", "")), 
        default = "1", description = "Overhang Style", update = UpdateStairs, name = "")
bpy.types.Object.s_is_back0 = BoolProperty(name = "Turn Backwards?", default = False, update = UpdateStairs)
#landing 1
bpy.types.Object.s_num_steps1 = IntProperty(name = "Number Of Steps", min = 1, max = 24, default = 13, update = UpdateStairs)
bpy.types.Object.s_landing_rot1 = EnumProperty(items = (("1", "Forwards", ""), ("2", "Left", ""), ("3", "Right", "")), update = UpdateStairs, name = "")
bpy.types.Object.s_tread_width1 = FloatProperty(name = "Tread Width", min = 9.0 / METRIC_INCH, max = 16.0 / METRIC_INCH, default = 9.5 / METRIC_INCH, subtype = "DISTANCE", update = UpdateStairs)
bpy.types.Object.s_riser_height1 = FloatProperty(name = "Riser Height", min = 5.0 / METRIC_INCH, max = 8.0 / METRIC_INCH, default = 7.4 / METRIC_INCH, subtype = "DISTANCE", update = UpdateStairs)
bpy.types.Object.s_landing_depth1 = FloatProperty(name = "Landing 2 Depth", min = 36 / METRIC_INCH, max = 60 / METRIC_INCH, default = 40 / METRIC_INCH, subtype = "DISTANCE", update = UpdateStairs)
bpy.types.Object.s_over_front1 = FloatProperty(name = "Front Overhang", min = 0.0, max = 1.25 / METRIC_INCH, default = 1.0 / METRIC_INCH, subtype = "DISTANCE", update = UpdateStairs)
bpy.types.Object.s_over_sides1 = FloatProperty(name = "Side Overhang", min = 0.0, max = 2.0 / METRIC_INCH, default = 1.0 / METRIC_INCH, subtype = "DISTANCE", update = UpdateStairs)
bpy.types.Object.s_overhang1 = EnumProperty(items = (("1", "Normal", ""), ("2", "Right", ""), ("3", "Left", ""), ("4", "Both", "")), 
        default = "1", description = "Overhang Style", update = UpdateStairs, name = "")
bpy.types.Object.s_is_back1 = BoolProperty(name = "Turn Backwards?", default = False, update = UpdateStairs)
#winding
bpy.types.Object.s_w_rot = EnumProperty(name = "", items = (("1", "-90", ""), ("2", "-45", ""), ("3", "45", ""), ("4", "90", "")), default = "3", update = UpdateStairs)
bpy.types.Object.s_num_rot = IntProperty(name = "Stair To Begin Rotation On", update = UpdateStairs, min = 1, max = 13, default = 6)
#spiral
bpy.types.Object.s_rot = FloatProperty(name = "Total Rotation", unit = "ROTATION", min = radians(-720), max = radians(720), default = radians(90), update = UpdateStairs)
bpy.types.Object.s_pole_dia = FloatProperty(name = "Pole Diameter", min = 3.0 / METRIC_INCH, max = 10.0 / METRIC_INCH, default = 4.0 / METRIC_INCH, subtype = "DISTANCE", update = UpdateStairs)
bpy.types.Object.s_pole_res = IntProperty(name = "Pole Resolution", min = 8, max = 64, default = 16, update = UpdateStairs)
bpy.types.Object.s_tread_res = IntProperty(name = "Tread Resolution", min = 0, max = 8, default = 0, update = UpdateStairs)
#materials
bpy.types.Object.s_is_material = BoolProperty(name = "Cycles Materials?", default = False, description = "Adds Cycles Materials", update = DeleteMaterials)
bpy.types.Object.s_is_preview = BoolProperty(name = "Preview Material?", default = False, description = "Preview Material On Object", update = PreviewMaterials)
#stairs
bpy.types.Object.s_im_scale = FloatProperty(name = "Image Scale", max = 10.0, min = 0.1, default = 1.0, description = "Change Image Scaling")
bpy.types.Object.s_col_image = StringProperty(name = "", subtype = "FILE_PATH", description = "File Path For Color Image")
bpy.types.Object.s_is_bump = BoolProperty(name = "Normal Map?", default = False, description = "Add Normal To Material?")
bpy.types.Object.s_norm_image = StringProperty(name = "", subtype = "FILE_PATH", description = "File Path For Normal Map Image")
bpy.types.Object.s_bump_amo = FloatProperty(name = "Normal Stength", min = 0.001, max = 2.000, default = 0.250, description = "Normal Map Strength")
bpy.types.Object.s_is_rotate = BoolProperty(name = "Rotate Image?", default = False, description = "Rotate Image 90 Degrees")
#pole/jacks
bpy.types.Object.s_im_scale2 = FloatProperty(name = "Image Scale", max = 10.0, min = 0.1, default = 1.0, description = "Change Image Scaling")
bpy.types.Object.s_col_image2 = StringProperty(name = "", subtype = "FILE_PATH", description = "File Path For Color Image")
bpy.types.Object.s_is_bump2 = BoolProperty(name = "Normal Map?", default = False, description = "Add Normal To Material?")
bpy.types.Object.s_norm_image2 = StringProperty(name = "", subtype = "FILE_PATH", description = "File Path For Normal Map Image")
bpy.types.Object.s_bump_amo2 = FloatProperty(name = "Normal Stength", min = 0.001, max = 2.000, default = 0.250, description = "Normal Map Strength")
bpy.types.Object.s_is_rotate2 = BoolProperty(name = "Rotate Image?", default = False, description = "Rotate Image 90 Degrees")
#uv
bpy.types.Object.s_unwrap = BoolProperty(name = "UV Unwrap?", default = True, description = "UV Unwraps Siding", update = UnwrapStairs)
bpy.types.Object.s_random_uv = BoolProperty(name = "Random UV's?", default = True, description = "Random UV's", update = UpdateStairs)

#panel
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
            layout.label("JARCH Vis Doesn't Work In Edit Mode", icon = "ERROR")
        else:
            if o is not None:
                if o.s_object_add != "mesh":
                    if o.s_object_add == "add":
                        layout.label("Style:", icon = "OBJECT_DATA"); layout.prop(o, "s_style"); layout.separator(); layout.prop(o, "s_width"); layout.separator()

                        if o.s_style != "3": layout.prop(o, "s_num_steps")
                        else: layout.prop(o, "s_num_steps2")

                        #if not spiral stairs
                        if o.s_style != "3": layout.prop(o, "s_tread_width")

                        layout.prop(o, "s_riser_height");

                        #show height
                        h = round((o.s_num_steps * o.s_riser_height) + (1 / METRIC_INCH), 2)
                        if context.scene.unit_settings.system == "IMPERIAL": layout.label("Height: " + str(round(((h * METRIC_INCH) / 12), 2)) + " ft", icon = "INFO"); layout.separator()
                        else: layout.label("Height: " + str(round(h, 2)) + " m", icon = "INFO"); layout.separator()

                        if o.s_style == "1":
                            layout.prop(o, "s_is_set_in", icon = "OOPS")

                            #ask if you want custom treads
                            if o.s_is_set_in == False:
                                layout.separator()
                                layout.prop(o, "s_is_custom_tread", icon = "OBJECT_DATAMODE")
                                if o.s_is_custom_tread == True:
                                    layout.prop_search(o, "s_custom_tread", context.scene, "objects")
                                layout.separator()

                            if o.s_is_set_in == False: layout.prop(o, "s_is_close", icon = "AUTOMERGE_ON"); layout.prop(o, "s_is_light", icon = "OUTLINER_OB_LAMP")
                        if o.s_is_set_in == False and o.s_style != "3":
                            layout.separator()
                            if o.s_style == "1": layout.label("Overhang Style:", icon = "OUTLINER_OB_SURFACE"); layout.prop(o, "s_overhang")
                            layout.prop(o, "s_over_front")
                            if o.s_overhang != "1": layout.prop(o, "s_over_sides")
                            if o.s_style == "1":
                                layout.separator(); layout.prop(o, "s_is_riser", icon = "TRIA_UP")
                            layout.separator()
                        else: layout.prop(o, "s_over_front"); layout.separator()

                        #normal stairs
                        if o.s_style == "1": #normal stairs
                            layout.separator(); layout.prop(o, "s_num_land")
                            if o.s_num_land > 0: layout.prop(o, "s_is_landing", icon = "FULLSCREEN")

                            #for each landing
                            for i in range(int(o.s_num_land)):
                                layout.separator(); layout.separator(); box = layout.box()
                                box.label("Stair Set " + str(i + 2) + ":", icon = "MOD_ARRAY"); box.separator()
                                box.prop(o, "s_num_steps" + str(i))

                                if o.s_is_custom_tread == True:
                                    box.prop(o, "s_tread_width" + str(i)); box.prop(o, "s_riser_height" + str(i))

                                #display height
                                if i == 0:
                                    h2 = h + round((o.s_riser_height0 * o.s_num_steps0) + o.s_riser_height + (1 / METRIC_INCH), 2);
                                    if context.scene.unit_settings.system == "IMPERIAL": box.label("Height: " + str(round(((h2 * METRIC_INCH) / 12), 2)) + " ft", icon = "INFO")
                                    else: box.label("Height: " + str(round(h2, 2)) + " m", icon = "INFO")
                                else:
                                    h2 = h + round((o.s_riser_height0 * o.s_num_steps0) + (o.s_riser_height0 * o.s_num_steps0) + (2 / METRIC_INCH) + o.s_riser_height + o.s_riser_height0, 2)
                                    if context.scene.unit_settings.system == "IMPERIAL": box.label("Height: " + str(round(((h2 * METRIC_INCH) / 12), 2)) + " ft", icon = "INFO")
                                    else: box.label("Height: " + str(round(h2, 2)) + " m", icon = "INFO")

                                box.separator(); box.label("Landing " + str(i + 1) + " Rotation:")
                                box.prop(o, "s_landing_rot" + str(i))

                                if (i == 0 and o.s_landing_rot0 != "1") or (i == 1 and o.s_landing_rot1 != "1"):
                                    box.prop(o, "s_is_back" + str(i), icon = "LOOP_BACK")
                                box.prop(o, "s_landing_depth" + str(i))

                                #if steps are not set in then allow adjustment of overhang and stuff
                                if o.s_is_set_in == False:
                                    box.separator(); box.label("Overhang Style:", icon = "OUTLINER_OB_SURFACE"); box.prop(o, "s_overhang" + str(i))
                                    box.prop(o, "s_over_front" + str(i))
                                    if (i == 0 and o.s_overhang0 != "1") or (i == 1 and o.s_overhang1 != "1"): box.prop(o, "s_over_sides" + str(i))

                        elif o.s_style == "2": #winding stairs
                            layout.prop(o, "s_num_rot"); row = self.layout.row(); row.label("Rotation: "); row.prop(o, "s_w_rot")
                        elif o.s_style == "3": #spiral stairs
                            layout.prop(o, "s_rot", icon = "MAN_ROT"); layout.prop(o, "s_tread_res"); layout.separator(); layout.prop(o, "s_pole_dia"); layout.prop(o, "s_pole_res")
                        #materials
                        layout.separator(); layout.prop(o, "s_unwrap", icon = "GROUP_UVS")
                        if o.s_unwrap == True:
                            layout.prop(o, "s_random_uv", icon = "RNDCURVE")
                        layout.separator()
                        if context.scene.render.engine == "CYCLES": layout.prop(o, "s_is_material", icon = "MATERIAL")
                        else: layout.label("Materials Only Supported With Cycles", icon = "POTATO")
                        layout.separator()
                        if o.s_is_material == True and context.scene.render.engine == "CYCLES":
                            #steps
                            box = layout.box()
                            box.label("Stairs:"); box.prop(o, "s_col_image", icon = "COLOR"); box.prop(o, "s_is_bump", icon = "SMOOTHCURVE"); box.separator()
                            if o.s_is_bump == True: box.prop(o, "s_norm_image", icon = "TEXTURE"); box.prop(o, "s_bump_amo")
                            box.prop(o, "s_im_scale", icon = "MAN_SCALE"); box.prop(o, "s_is_rotate", icon = "MAN_ROT")
                            #pole/jacks
                            layout.separator()
                            if o.s_style in ("1", "3"):
                                box = layout.box()
                                if o.s_style == "1": box.label("Jacks:")
                                else: box.label("Pole:")
                                box.prop(o, "s_col_image2", icon = "COLOR"); box.prop(o, "s_is_bump2", icon = "SMOOTHCURVE"); box.separator()
                                if o.s_is_bump2 == True: box.prop(o, "s_norm_image2", icon = "TEXTURE"); box.prop(o, "s_bump_amo2")
                                box.prop(o, "s_im_scale2", icon = "MAN_SCALE"); box.prop(o, "s_is_rotate2", icon = "MAN_ROT")
                            layout.separator(); layout.operator("mesh.jarch_stairs_materials", icon = "MATERIAL")
                        #operators
                        layout.separator(); layout.separator()
                        layout.operator("mesh.jarch_stairs_update", icon = "FILE_REFRESH")
                        layout.operator("mesh.jarch_stairs_mesh", icon = "OUTLINER_OB_MESH")
                        layout.operator("mesh.jarch_stairs_delete", icon = "CANCEL")
                    else:
                        layout.operator("mesh.jarch_stairs_add", icon = "MOD_ARRAY")
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
    def poll(self, context):
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
        o = context.object
        bpy.ops.object.delete()
        for i in bpy.data.materials: #remove unused materials
            if i.users == 0: bpy.data.materials.remove(i)
        return {"FINISHED"}

class StairsUpdate(bpy.types.Operator):
    bl_idname = "mesh.jarch_stairs_update"
    bl_label = "Update Stairs"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        UpdateStairs(self, context)
        return {"FINISHED"}
    
class StairsMaterial(bpy.types.Operator):
    bl_idname = "mesh.jarch_stairs_materials"
    bl_label = "Generate\\Update Materials"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        StairsMaterials(self, context)
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
