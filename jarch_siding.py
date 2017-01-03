from itertools import permutations
import bpy
from bpy.props import FloatVectorProperty, BoolProperty, FloatProperty, StringProperty, IntProperty, EnumProperty
from math import sqrt, atan, asin, sin, cos, tan
from random import uniform, choice
from mathutils import Euler, Vector
from . jarch_materials import *
import bmesh
from . jarch_utils import rot_from_normal, object_dimensions, point_rotation, METRIC_INCH, METRIC_FOOT, I, HI
from ast import literal_eval


# manages sorting out which type of siding needs to be create, gets corner data for cutout objects
def create_siding(context, mat, tin_types, wood_types, vinyl_types, sloped, ow, oh, bw, slope, is_width_vary,
                  width_vary, is_cutout, num_cutouts, nc1, nc2, nc3, nc4, nc5, baw, spacing, is_length_vary,
                  length_vary, max_boards, b_w, b_h, b_offset, b_gap, m_d, b_ran_offset, b_vary, is_corner, is_invert,
                  is_soldier, is_left, is_right, avw, avh, s_random, b_random, x_off):

    # percentages
    width_vary = 1 / (100 / width_vary)
    length_vary = 1 / (100 / length_vary)   
    
    # evaluate cutouts
    cutouts = []
    if is_cutout:
        if nc1 != "" and num_cutouts >= 1:
            add = nc1.split(",")
            cutouts.append(add)
        if nc2 != "" and num_cutouts >= 2:
            add = nc2.split(",")
            cutouts.append(add)
        if nc3 != "" and num_cutouts >= 3:
            add = nc3.split(",")
            cutouts.append(add)
        if nc4 != "" and num_cutouts >= 4:
            add = nc4.split(",")
            cutouts.append(add)
        if nc5 != "" and num_cutouts >= 5:
            add = nc5.split(",")
            cutouts.append(add)

    cuts = []  # create list of data if cutout has correct info and is numbers
    for i in cutouts:
        pre = []
        skip = False
        if len(i) == 4:
            for i2 in i:
                try:
                    if context.scene.unit_settings.system == "IMPERIAL":
                        i2 = round(float(i2) / METRIC_FOOT, 5)
                    else:
                        i2 = float(i2)
                    pre.append(i2)
                except ValueError:
                    skip = True
        if not skip and pre != []:
            cuts.append(pre)

    # determine corner points
    corner_data, corner_data_l = [], []
    for i in cuts:
        corner_data.append([i[0], i[1], i[0] + i[3], i[1] + i[2]])
        if is_soldier:
            corner_data_l.append([i[0], i[1], i[0] + i[3], i[1] + i[2] + b_w + b_gap])

    # verts and faces
    verts, faces = [], []
    v, f = [], []

    # Wood
    if mat == "1" and wood_types == "1":  # Wood > Vertical
        verts, faces, temp = wood_vertical(verts, faces, oh, ow, sloped, slope, is_width_vary, width_vary, bw,
                                           spacing, is_length_vary, length_vary, max_boards)
    elif mat == "1" and wood_types == "2":  # Wood > Vertical: Tongue & Groove
        verts, faces = wood_ton_gro(verts, faces, oh, ow, sloped, slope, bw, is_length_vary, length_vary, spacing,
                                    max_boards)
    elif mat == "1" and wood_types == "3":  # Wood > Vertical: Board & Batten
        verts, faces, batten_pos = wood_vertical(verts, faces, oh, ow, sloped, slope, False, width_vary, bw, 0.00635,
                                                 is_length_vary, length_vary, max_boards)
        for x in batten_pos:
            hw = ow - x if x + baw / 2 > ow else baw / 2  # half width of batten
            p = len(v)

            z_dif = 0
            if sloped:
                z_dif = slope * 2 * hw / 12
                if sloped and x > ow / 2:
                    z_dif *= -1

            ht = -(slope / 12) * abs(x - hw - ow / 2) + oh if sloped else oh  # height at left edge of board
            ht2 = -(slope / 12) * abs(x + hw - ow / 2) + oh  # height at right edge of board

            if sloped and x - hw < ow / 2 < x + hw:  # middle board
                v += [(x - hw, -I, 0), (x - hw, -2 * I, 0), (ow / 2, -I, 0), (ow / 2, -2 * I, 0),
                      (x + hw, -I, 0), (x + hw, -2 * I, 0), (x - hw, -I, ht), (x - hw, -2 * I, ht),
                      (ow / 2, -I, oh), (ow / 2, -2 * I, oh), (x + hw, -I, ht2), (x + hw, -2 * I, ht2)]
                f += [(p, p + 2, p + 3, p + 1), (p + 2, p + 4, p + 5, p + 3), (p, p + 1, p + 7, p + 6),
                      (p + 1, p + 3, p + 9, p + 7), (p + 3, p + 5, p + 11, p + 9), (p + 5, p + 4, p + 10, p + 11),
                      (p + 2, p + 8, p + 10, p + 4), (p, p + 6, p + 8, p + 2), (p + 6, p + 7, p + 9, p + 8),
                      (p + 9, p + 11, p + 10, p + 8)]
            else:
                v += [(x - hw, -I, 0), (x - hw, -2 * I, 0), (x + hw, -I, 0), (x + hw, -2 * I, 0),
                      (x - hw, -I, ht), (x - hw, -2 * I, ht), (x + hw, -I, ht + z_dif), (x + hw, -2 * I, ht + z_dif)]
                f += [(p, p + 2, p + 3, p + 1), (p, p + 1, p + 5, p + 4), (p + 1, p + 3, p + 7, p + 5),
                      (p + 3, p + 2, p + 6, p + 7), (p, p + 4, p + 6, p + 2), (p + 5, p + 7, p + 6, p + 4)]
    elif mat == "1" and wood_types == "4":
        verts, faces = wood_lap(oh, ow, sloped, slope, bw, verts, faces, is_length_vary, length_vary, max_boards,
                                0.02540, spacing)
    elif mat == "1" and wood_types == "5":
        verts, faces = wood_lap_bevel(oh, ow, sloped, slope, bw, is_length_vary, length_vary, faces, verts,
                                      max_boards, spacing)
    # Vinyl
    elif mat == "2" and vinyl_types == "1":
        verts, faces = vinyl_vertical(oh, ow, sloped, slope, is_length_vary, length_vary, bw, baw, faces, verts,
                                      max_boards, spacing)
    elif mat == "2" and vinyl_types == "2":
        verts, faces = vinyl_lap(oh, ow, sloped, slope, is_length_vary, length_vary, bw, faces, verts, max_boards,
                                 spacing)
    elif mat == "2" and vinyl_types == "3":
        verts, faces = vinyl_dutch_lap(oh, ow, sloped, slope, is_length_vary, length_vary, bw, faces, verts,
                                       max_boards, spacing)
    # Tin
    elif mat == "3" and tin_types == "1":
        verts, faces = tin_normal(oh, ow, sloped, slope, faces, verts)
    elif mat == "3" and tin_types == "2":
        verts, faces = tin_angular(oh, ow, sloped, slope, faces, verts)
    # Fiber Cement
    elif mat == "4":
        verts, faces = wood_lap(oh, ow, sloped, slope, bw, verts, faces, is_length_vary, length_vary, max_boards,
                                0.009525, spacing)
    # Bricks
    elif mat == "5":
        verts, faces = bricks(oh, ow, b_w, b_h, b_offset, b_gap, b_ran_offset, b_vary, faces, verts,
                              is_corner, is_invert, is_left, is_right)
    # Stone
    elif mat == "6":
        verts, faces = stone_faces(oh, ow, avw, avh, s_random, b_random, b_gap)
    
    # adjust for x_offset
    out_verts, out_v = [], []

    for i in verts:
        l = list(i)
        l[0] += x_off
        out_verts.append(l)
    for i in v:
        l = list(i)
        l[0] += x_off
        out_v.append(l)

    return out_verts, faces, corner_data, corner_data_l, out_v, f


def boolean_object(corner_data):  # creates list of vertices and faces for all the cutout objects
    verts, faces = [], []
    for ob in corner_data:
        p = len(verts)
        verts += [(ob[0], 0.5, ob[1]), (ob[0], -0.5, ob[1]), (ob[2], -0.5, ob[1]), (ob[2], 0.5, ob[1]),
                  (ob[0], 0.5, ob[3]), (ob[0], -0.5, ob[3]), (ob[2], -0.5, ob[3]), (ob[2], 0.5, ob[3])]
        faces += [(p, p + 3, p + 2, p + 1), (p + 4, p + 5, p + 6, p + 7), (p, p + 1, p + 5, p + 4),
                  (p + 2, p + 3, p + 7, p + 6), (p, p + 4, p + 7, p + 3), (p + 1, p + 2, p + 6, p + 5)]
    return verts, faces


def slope_height(x, slope, ow, oh):
    return -(slope / 12) * abs(x - ow / 2) + oh


def recalculate_slope(slope, oh, ow):
    square = oh - ((slope * (ow / 2)) / 12)  # height - what that slope and width would give for height
    if square <= 0:  # check is it is a negative number
        slope = ((24 * oh) / ow) - 0.01

    return slope


def wood_vertical(verts, faces, oh, ow, sloped, slope, is_width_vary, width_vary, width, spacing, is_length_vary,
                  length_vary, max_boards):
    cur_x = 0.0
    batten_pos = []
    if sloped:
        slope = recalculate_slope(slope, oh, ow)

    while cur_x < ow:
        if is_length_vary:
            v = oh * length_vary * 0.45
            bl = uniform(oh / 2 - v, oh / 2 + v)
        else:
            bl = oh
            max_boards = 1

        if is_width_vary:
            v = width * width_vary * 0.75
            bw = uniform(width - v, width + v)
        else:
            bw = width

        if cur_x + bw > ow:  # trim if wider
            bw = ow - cur_x

        z_dif = 0
        if sloped:
            z_dif = slope * bw / 12
            if sloped and cur_x > ow / 2:
                z_dif *= -1

        ct = 1
        cur_z = 0
        while cur_z < oh:
            center = True
            p = len(verts)
            ht = -(slope / 12) * abs(cur_x - ow / 2) + oh if sloped else oh  # height at left edge of board
            ht2 = -(slope / 12) * abs(cur_x + bw - ow / 2) + oh  # height at right edge of board

            if sloped and ((cur_x < ow / 2 < cur_x + bw and cur_z + bl >= oh) or
                           (cur_x < ow / 2 < cur_x + bw and ct >= max_boards)):  # middle board
                verts += [(cur_x, 0, cur_z), (cur_x, -I, cur_z), (ow / 2, 0, cur_z), (ow / 2, -I, cur_z),
                          (cur_x + bw, 0, cur_z), (cur_x + bw, -I, cur_z), (cur_x, 0, ht), (cur_x, -I, ht),
                          (ow / 2, 0, oh), (ow / 2, -I, oh), (cur_x + bw, 0, ht2), (cur_x + bw, -I, ht2)]
                cur_z = oh
                center = False
            elif cur_z + bl >= ht or ct >= max_boards or (cur_x > ow / 2 and cur_z + bl > ht2):
                verts += [(cur_x, 0, cur_z), (cur_x, -I, cur_z), (cur_x + bw, 0, cur_z), (cur_x + bw, -I, cur_z),
                          (cur_x, 0, ht), (cur_x, -I, ht), (cur_x + bw, 0, ht + z_dif), (cur_x + bw, -I, ht + z_dif)]
                cur_z = oh
            else:
                verts += [(cur_x, 0, cur_z), (cur_x, -I, cur_z), (cur_x + bw, 0, cur_z), (cur_x + bw, -I, cur_z),
                          (cur_x, 0, cur_z + bl), (cur_x, -I, cur_z + bl), (cur_x + bw, 0, cur_z + bl),
                          (cur_x + bw, -I, cur_z + bl)]
                cur_z += bl + spacing

            if center:
                faces += [(p, p + 2, p + 3, p + 1), (p, p + 1, p + 5, p + 4), (p + 1, p + 3, p + 7, p + 5),
                          (p + 3, p + 2, p + 6, p + 7), (p, p + 4, p + 6, p + 2), (p + 5, p + 7, p + 6, p + 4)]
            else:
                faces += [(p, p + 2, p + 3, p + 1), (p + 2, p + 4, p + 5, p + 3), (p, p + 1, p + 7, p + 6),
                          (p + 1, p + 3, p + 9, p + 7), (p + 3, p + 5, p + 11, p + 9), (p + 5, p + 4, p + 10, p + 11),
                          (p + 2, p + 8, p + 10, p + 4), (p, p + 6, p + 8, p + 2), (p + 6, p + 7, p + 9, p + 8),
                          (p + 9, p + 11, p + 10, p + 8)]

            ct += 1

        batten_pos.append(cur_x + bw + spacing / 2)  # middle of joint
        cur_x += bw + spacing

    return verts, faces, batten_pos


def wood_ton_gro(verts, faces, oh, ow, sloped, slope, bw, is_length_vary, length_vary, spacing, max_boards):
    x = 0.0
    tei = 0.375 / METRIC_INCH
    ei = 0.125 / METRIC_INCH
    ssi = 0.4375 / METRIC_INCH
    qi = 0.25 / METRIC_INCH

    # adjust slope if needed
    if sloped:
        slope = recalculate_slope(slope, oh, ow)

    while x < ow:
        z = 0.0

        if x + bw > ow:
            bw = ow - x

        ct = 1
        while z < oh:  # while not full height
            p = len(verts)

            if is_length_vary:  # if varied length calculate length
                v = oh * (length_vary * 0.45)
                bl = uniform((oh / 2) - v, (oh / 2) + v)
            else:
                bl = oh

            if z + bl + spacing > oh or (is_length_vary and ct >= max_boards):
                bl = oh - z

            if sloped and ((z + bl + spacing > slope_height(x, slope, ow, oh) and x < ow / 2) or
                           (z + bl + spacing > slope_height(x + bw + HI, slope, ow, oh) and x > ow / 2)):
                h1, h2, h3, h4, h5, h6, h7 = [slope_height(i, slope, ow, oh) for i in
                                              [x, x + qi, x + HI, x + bw / 2, x + bw, x + bw + qi, x + bw + HI]]
                bl = oh  # force z to be greater then oh on update
            else:
                h1, h2, h3, h4, h5, h6, h7 = [z + bl] * 7

            verts += [[x, 0, z], [x, 0, h1], [x, -tei, z], [x, -tei, h1], [x + qi, -tei, z], [x + qi, -tei, h2],
                      [x + HI, -tei, z], [x + HI, -tei, h3], [x + HI, -tei - qi, z], [x + HI, -tei - qi, h3],
                      [x + qi, -tei - qi, z], [x + qi, -tei - qi, h2], [x, -tei - qi, z], [x, -tei - qi, h1],
                      [x, -I, z], [x, -I, h1], [x + qi, -I, z], [x + qi, -I, h2], [x + HI, -I, z], [x + HI, -I, h3],
                      [x + bw / 2, -I, z], [x + bw / 2, -I, h4], [x + bw, -I, z], [x + bw, -I, h5],
                      [x + bw, -ssi - ei, z], [x + bw, -ssi - ei, h5], [x + bw + qi, -ssi - ei, z],
                      [x + bw + qi, -ssi - ei, h6], [x + bw + HI, -ssi - ei, z], [x + bw + HI, -ssi - ei, h7],
                      [x + bw + HI, -ssi, z], [x + bw + HI, -ssi, h7], [x + bw + qi, -ssi, z], [x + bw + qi, -ssi, h6],
                      [x + bw, -ssi, z], [x + bw, -ssi, h5], [x + bw, 0, z], [x + bw, 0, h5], [x + bw / 2, 0, z],
                      [x + bw / 2, 0, h4], [x + HI, 0, z], [x + HI, 0, h3], [x + qi, 0, z], [x + qi, 0, h2],
                      [x + bw / 2, -tei, z], [x + bw / 2, -tei, h4], [x + bw / 2, -tei - qi, z],
                      [x + bw / 2, -tei - qi, h4]]

            if sloped and ((x < ow / 2 < x + bw + HI and z + bl >= oh) or
                           (x < ow / 2 < x + bw + HI and ct >= max_boards)):
                if x + HI > ow / 2:  # in groove
                    adj = [4, 5, 10, 11, 16, 17, 42, 43]
                elif x + bw > ow / 2:  # in main board
                    adj = [20, 21, 38, 39, 44, 45, 46, 47]
                else:  # in tongue
                    adj = [26, 27, 32, 33]

                for i in adj:  # adjust to make points at proper x and z values
                    verts[p + i][0] = ow / 2
                    if i % 2 != 0:
                        verts[p + i][2] = oh

            p2 = p
            for i in range(20):
                faces += [(p2, p2 + 2, p2 + 3, p2 + 1)]
                p2 += 2
            faces += [(p, p + 1, p2 + 1, p2)]  # last face

            faces += [(p, p + 42, p + 4, p + 2), (p + 4, p + 42, p + 40, p + 6), (p + 6, p + 40, p + 38, p + 44),
                      (p + 34, p + 44, p + 38, p + 36), (p + 6, p + 44, p + 46, p + 8), (p + 24, p + 46, p + 44, p+34),
                      (p + 24, p + 34, p + 32, p + 26), (p + 26, p + 32, p + 30, p + 28), (p + 10, p + 16, p+14, p+12),
                      (p + 8, p + 18, p + 16, p + 10), (p + 8, p + 46, p + 20, p + 18), (p + 20, p + 46, p + 24, p+22),
                      (p + 1, p + 3, p + 5, p + 43), (p + 5, p + 7, p + 41, p + 43), (p + 7, p + 45, p + 39, p + 41),
                      (p + 39, p + 45, p + 35, p + 37), (p + 7, p + 9, p + 47, p + 45), (p + 45, p + 47, p + 25, p+35),
                      (p + 35, p + 25, p + 27, p + 33), (p + 33, p + 27, p + 29, p + 31), (p + 11, p + 13, p+15, p+17),
                      (p + 9, p + 11, p + 17, p + 19), (p + 9, p + 19, p + 21, p + 47), (p + 47, p + 21, p + 23, p+25)]

            ct += 1
            z += bl + spacing
        x += bw + spacing

    return verts, faces

                
def wood_lap(oh, ow, sloped, slope, bw, verts, faces, is_length_vary, length_vary, max_boards, thickness, spacing):
    z = 0.0
    th = thickness

    if sloped:  # if slope check and see if slope is possible, if not recalculate
        slope = recalculate_slope(slope, oh, ow)

    start_x = 0.0  # used to jump start cur_x if sloped
    last_x = ow
    square = oh - (ow / 2) * (slope / 12)
    theta = asin(th / (bw - I))
    inch_offset = I * cos(theta) * (12 / slope)

    while z < oh:
        ct = 1
        y_dif = 0
        x = start_x

        if z + bw * cos(theta) > oh and not sloped:
            temp = bw
            bw = sqrt(th**2 + (oh - z)**2) + I
            y_dif = (temp - bw) * sin(theta)  # help keep board oriented well

        while x < last_x:
            p = len(verts)
            normal_face = True

            if is_length_vary:
                v = ow * (length_vary * 0.49)
                bl = uniform((ow / 2) - v, (ow / 2) + v)
                if sloped and bl < bw * cos(theta) * (12 / slope):  # make board longer then sloped part of board
                    bl = bw * cos(theta) * (12 / slope) * 1.1
            else:
                bl = 2 * ow

            l1, l2, l3, r1, r2, r3 = x, x, x, x + bl, x + bl, x + bl
            y1, y2, y3 = y_dif + bw * sin(theta), y_dif + bw / 2 * sin(theta), y_dif
            z1, z2, z3 = z, z + bw / 2 * cos(theta), z + bw * cos(theta)

            if sloped and z3 > square:
                if z1 < square < z3:
                    z2 = square
                    y2 = (z3 - z2) * tan(theta)

                if x == start_x:  # first
                    if z1 < square < z3:
                        l1, l2, l3 = 0, 0, (z3 - z2) * (12 / slope)
                    else:
                        l1, l2, l3 = x, x + (z2 - z) * (12 / slope), x + (z3 - z) * (12 / slope)

                    start_x = l3 - inch_offset

                if x + bl >= last_x - bw * cos(theta) * (12 / slope) or (is_length_vary and ct >= max_boards):  # last
                    if z1 < square < z3:
                        r1, r2, r3 = ow, ow, ow - (z3 - z2) * (12 / slope)
                    else:
                        r1, r2, r3 = last_x, last_x - (z2 - z) * (12 / slope), last_x - bw * cos(theta) * (12 / slope)

                    last_x = r3 + inch_offset
                    bl = 2 * ow

            elif x + bl > ow or (is_length_vary and ct >= max_boards):
                r1, r2, r3 = [ow] * 3
                bl = ow  # make sure this is last board for row

            if z3 <= oh or (not sloped and z3 > oh):
                verts += [(l1, -y1, z1), (l2, -y2, z2), (l3, -y3, z3), (l1, -y1 - th, z1), (l2, -y2 - th, z2),
                          (l3, -y3 - th, z3), (r1, -y1 - th, z1), (r2, -y2 - th, z2), (r3, -y3 - th, z3),
                          (r1, -y1, z1), (r2, -y2, z2), (r3, -y3, z3)]
            else:  # triangle
                y2 = y1 - (oh - z) * tan(theta)
                verts += [(l1, -y1, z1), (l1, -y1 - th, z1), (r1, -y1, z1), (r1, -y1 - th, z1),
                          (ow / 2, -y2, oh), (ow / 2, -y2 - th, oh)]
                normal_face = False

            if normal_face:
                p2 = p
                for i in range(3):
                    faces += [(p2, p2 + 3, p2 + 4, p2 + 1), (p2 + 1, p2 + 4, p2 + 5, p2 + 2)]
                    p2 += 3
                faces += [(p + 2, p + 5, p + 8, p + 11), (p, p + 9, p + 6, p + 3), (p, p + 1, p + 10, p + 9),
                          (p + 1, p + 2, p + 11, p + 10)]
            else:
                faces += [(p, p + 2, p + 3, p + 1), (p, p + 1, p + 5, p + 4), (p + 2, p + 4, p + 5, p + 3),
                          (p + 1, p + 3, p + 5), (p, p + 4, p + 2)]

            ct += 1
            x += bl + spacing

        if z + bw * cos(theta) > oh:
            z = oh
        else:
            z += (bw - I) * cos(theta)

    return verts, faces


def wood_lap_bevel(oh, ow, sloped, slope, bw, is_length_vary, length_vary, faces, verts, max_boards, spacing):
    z = 0.0
    last_x = ow
    start_x = 0.0

    if sloped:
        slope = recalculate_slope(slope, oh, ow)

    square = oh - ((slope * (ow / 2)) / 12)

    while z < oh:
        x = start_x
        ct = 1

        if z + bw > oh:
            bw = oh - z

        while x < last_x:
            p = len(verts)

            if is_length_vary:
                v = ow * (length_vary * 0.45)
                bl = uniform((ow / 2) - v, (ow / 2) + v)
                if x + bl > ow or ct >= max_boards:
                    bl = ow - x
                if sloped and x < ow / 2 and bl < bw * (12 / slope):  # make sure longer than slope's run
                    bl = bw * (12 / slope) * 1.1
            else:
                bl = ow

            sp = bw / 3
            theta = atan(I / (bw / 2))
            z1, z2, z3, z4, z5, z6, z7 = [z + i for i in [0, sp / 2, sp, 1.5 * sp, 2 * sp, 2.5 * sp, bw]]
            y1, y2 = (bw / 3) * tan(theta), (bw / 6) * tan(theta)
            y3, y4 = I - y2, I - y1

            if sloped and z7 > square:
                l1, l2, l3, l4, l5, l6, l7 = [x] * 7
                r1, r2, r3, r4, r5, r6, r7 = [x + bl] * 7

                if z1 < square < z7:  # adjust z positions to get row at square, adjust y positions for new z positions
                    if z1 < square < z3:
                        z2 = square
                        y2 = (z3 - z2) * tan(theta)
                    elif z3 < square < z5:
                        z4 = square
                    else:
                        z6 = square
                        y3 = I - (z6 - z5) * tan(theta)

                if x == start_x:  # first
                    if z1 < square < z7:
                        temp = [z1, z2, z3, z4, z5, z6, z7]
                        for i in range(len(temp)):
                            temp[i] = (temp[i] - square) * (12 / slope) if temp[i] > square else 0
                        l1, l2, l3, l4, l5, l6, l7 = temp
                    else:
                        l1, l2, l3, l4, l5, l6, l7 = [start_x + (i - z) * (12 / slope) for i in
                                                      [z1, z2, z3, z4, z5, z6, z7]]
                    start_x = l7 - (bw / 6) * (12 / slope)

                if x + bl >= last_x - bw * (12 / slope) or (is_length_vary and ct >= max_boards):  # last
                    if z1 < square < z7:
                        temp = [z1, z2, z3, z4, z5, z6, z7]
                        for i in range(len(temp)):
                            temp[i] = ow - (temp[i] - square) * (12 / slope) if temp[i] > square else ow
                        r1, r2, r3, r4, r5, r6, r7 = temp
                    else:
                        r1, r2, r3, r4, r5, r6, r7 = [last_x - (i - z) * (12 / slope) for i in
                                                      [z1, z2, z3, z4, z5, z6, z7]]

                    last_x = r7 + (bw / 6) * (12 / slope)
                    bl = 2 * ow
            else:
                l1, l2, l3, l4, l5, l6, l7 = [x] * 7
                r1, r2, r3, r4, r5, r6, r7 = [x + bl] * 7

            verts += [(l1, -y1, z1), (l2, -y2, z2), (l3, 0, z3), (l4, 0, z4), (l5, 0, z5), (l6, 0, z6), (l7, 0, z7),
                      (l1, -I, z1), (l2, -I, z2), (l3, -I, z3), (l4, -I, z4), (l5, -I, z5),
                      (l6, -y3, z6), (l7, -y4, z7), (r1, -I, z1), (r2, -I, z2), (r3, -I, z3),
                      (r4, -I, z4), (r5, -I, z5), (r6, -y3, z6), (r7, -y4, z7), (r1, -y1, z1), (r2, -y2, z2),
                      (r3, 0, z3), (r4, 0, z4), (r5, 0, z5), (r6, 0, z6), (r7, 0, z7)]

            p2 = p
            for i in range(3):  # first three sides
                for j in range(6):
                    faces += [(p2 + j, p2 + j + 7, p2 + j + 8, p2 + j + 1)]
                p2 += 7
            for j in range(6):  # back faces
                faces += [(p + j, p + j + 1, p + 22 + j, p + 21 + j)]
            faces += [(p + 6, p + 13, p + 20, p + 27), (p, p + 21, p + 14, p + 7)]  # top and bottom

            ct += 1
            x += bl + spacing

        if z + bw >= oh:
            z = oh
        else:
            z += bw - (bw / 6)

    return verts, faces


def vinyl_vertical(oh, ow, sloped, slope, is_length_vary, length_vary, bw, baw, faces, verts, max_boards, spacing):
    # creates a plane, which then has a bevel and solidify added
    x = 0
    pan = (bw - 2 * baw) / 2
    tei = 0.375 / METRIC_INCH
    qi = 0.25 / METRIC_INCH

    if sloped:
        slope = recalculate_slope(slope, oh, ow)

    while x < ow:
        z = 0
        ct = 1

        while z < oh:
            p = len(verts)

            if is_length_vary:
                v = oh * length_vary * 0.45
                bl = uniform((oh / 2) - v, (oh / 2) + v)
                if z + bl + spacing > oh or ct >= max_boards:
                    bl = oh - z
            else:
                bl = oh

            if sloped and ((z + bl + spacing > slope_height(x, slope, ow, oh) and x < ow / 2) or
                           (z + bl + spacing > slope_height(x + bw, slope, ow, oh) and x > ow / 2)):
                z1, z2, z3, z4, z5 = [slope_height(i, slope, ow, oh) for i in
                                      [x, x + pan, x + pan + baw, x + bw - baw, x + bw]]
                bl = oh
            else:
                z1, z2, z3, z4, z5 = [z + bl] * 5

            v = [[x, -tei, z1], [x, 0, z1], [x + pan, 0, z2], [x + pan, -HI, z2], [x + pan + baw, -HI, z3],
                 [x + pan + baw, 0, z3], [x + bw - baw, 0, z4], [x + bw - baw, -HI, z4], [x + bw, -HI, z5],
                 [x + bw, -qi, z5]]

            fa = 0
            cut = False
            for i in range(len(v)):  # trim to correct position
                # determine if middle board, make sure top is sloped, and not lower board
                if sloped and 0 < i < len(v) - 1 and v[i - 1][0] < ow / 2 < v[i][0] and \
                                v[i][2] == slope_height(v[i][0], slope, ow, oh):
                    verts += [(ow / 2, v[i - 1][1], z), (ow / 2, v[i - 1][1], oh)]
                    fa += 1

                # cut for length
                if v[i][0] >= ow and not cut:
                    if sloped and v[i][2] != v[0][2]:  # sloped
                        v[i][2] = slope_height(ow, slope, ow, oh)
                    verts += [(ow, v[i][1], z), (ow, v[i][1], v[i][2])]
                    cut = True
                    fa += 1
                elif v[i][0] < ow and not cut:
                    verts += [(v[i][0], v[i][1], z), v[i]]
                    fa += 1

            for i in range(fa - 1):
                faces += [(p, p + 2, p + 3, p + 1)]
                p += 2

            ct += 1
            z += bl + spacing
        x += bw - 0.125 / METRIC_INCH

    return verts, faces


def vinyl_lap(oh, ow, sloped, slope, is_length_vary, length_vary, bw, faces, verts, max_boards, spacing):
    z = 0.0
    start_x = 0.0
    tqi = 0.01905
    last_x = ow
    theta = atan(tqi / bw)

    if sloped:
        slope = recalculate_slope(slope, oh, ow)
        square = oh - ((slope * (ow / 2)) / 12)
    else:
        square = oh

    while z < oh:
        x = start_x
        ct = 1

        if z + bw > oh:
            bw = oh - z

        while x < last_x:
            p = len(verts)

            if is_length_vary:
                v = ow * length_vary * 0.49
                bl = uniform((ow / 2) - v, (ow / 2) + v)
                if x + bl + spacing > ow or ct >= max_boards:
                    bl = ow - x
                if sloped and x < ow / 2 and bl < bw * (12 / slope):  # make sure longer than slope's run
                    bl = bw * (12 / slope) * 1.1
            else:
                bl = ow

            l1, l2, l3 = [x] * 3
            r1, r2, r3 = [x + bl] * 3
            z1, z2, z3 = z, z + bw / 2, z + bw
            y2, y3 = tqi / 2, 0

            if sloped and z3 > square:
                if z1 < square < z3:
                    z2 = square
                    y2 = (z3 - z2) * tan(theta)

                if x == start_x:
                    if z1 < square < z3:
                        l1, l2, l3 = x, x, x + (z3 - z2) * (12 / slope)
                    else:
                        l1, l2, l3 = x, x + (bw / 2) * (12 / slope), x + bw * (12 / slope)
                    start_x = l3
                if x + bl + spacing > last_x or (x + bl > ow / 2 and x + bl + spacing > last_x - bw * (12 / slope)) or \
                        ct >= max_boards:
                    if z1 < square < z3:
                        r1, r2, r3 = last_x, last_x, last_x - (z3 - z2) * (12 / slope)
                    else:
                        r1, r2, r3 = last_x, last_x - (bw / 2) * (12 / slope), last_x - bw * (12 / slope)
                    last_x = r3
                    bl = ow

            verts += [(l1, 0, z1), (l1, -tqi, z1), (l2, -y2, z2), (l3, -y3, z3), (r1, 0, z1), (r1, -tqi, z1),
                      (r2, -y2, z2), (r3, -y3, z3)]

            faces += [(p, p + 4, p + 5, p + 1), (p + 1, p + 5, p + 6, p + 2), (p + 2, p + 6, p + 7, p + 3)]

            ct += 1
            x += bl + spacing
        z += bw

    return verts, faces


def vinyl_dutch_lap(oh, ow, sloped, slope, is_length_vary, length_vary, bw, faces, verts, max_boards, spacing):
    z = 0
    last_x = ow
    start_x = 0
    theta = atan(HI / (bw / 3))

    if sloped:
        slope = recalculate_slope(slope, oh, ow)
        square = oh - ((slope * (ow / 2)) / 12)  # z height where slope starts
    else:
        square = oh

    while z < oh:
        x = start_x
        ct = 1

        if z + bw > oh:
            bw = oh - z
            theta = atan(HI / (bw / 3))

        tb, ttb = bw / 3, 2 * bw / 3

        while x < last_x:
            p = len(verts)

            if is_length_vary:
                v = ow * length_vary * 0.49
                bl = uniform((ow / 2) - v, (ow / 2) + v)
                if x + bl + spacing > ow or ct >= max_boards:
                    bl = ow - x
                if sloped and x < ow / 2 and bl < bw * (12 / slope):  # make sure longer than slope's run
                    bl = bw * (12 / slope) * 1.1
            else:
                bl = ow

            l1, l2, l3, l4, l5 = [x] * 5
            r1, r2, r3, r4, r5 = [x + bl] * 5
            z1, z2, z3, z4, z5 = z, z + ttb / 2, z + ttb, z + ttb + tb / 2, z + bw
            y4 = (bw / 6) * tan(theta)

            if sloped and z5 > square:
                if z1 < square < z3:
                    z2 = square
                elif z3 < square < z5:
                    z4 = square
                    y4 = (z5 - z4) * tan(theta)

                if x == start_x:
                    if z1 < square < z3:
                        l1, l2, l3, l4, l5 = [x + (i - z2) * (12 / slope) for i in [z2, z2, z3, z4, z5]]
                    elif z3 < square < z5:
                        l1, l2, l3, l4, l5 = [x + (i - z4) * (12 / slope) for i in [z4, z4, z4, z4, z5]]
                    else:
                        l1, l2, l3, l4, l5 = [x + i * (12 / slope) for i in [0, ttb / 2, ttb, ttb + tb / 2, bw]]
                    start_x = l5
                if x + bl + spacing > last_x or (x + bl > ow / 2 and x + bl + spacing > last_x - bw * (12 / slope)) or \
                        ct >= max_boards:
                    if z1 < square < z3:
                        r1, r2, r3, r4, r5 = [last_x - (i - z2) * (12 / slope) for i in [z2, z2, z3, z4, z5]]
                    elif z3 < square < z5:
                        r1, r2, r3, r4, r5 = [last_x - (i - z4) * (12 / slope) for i in [z4, z4, z4, z4, z5]]
                    else:
                        r1, r2, r3, r4, r5 = [last_x - i * (12 / slope) for i in [0, ttb / 2, ttb, ttb + tb / 2, bw]]
                    last_x = r5
                    bl = ow

            verts += [(l1, 0, z1), (l1, -HI, z1), (l2, -HI, z2), (l3, -HI, z3), (l4, -y4, z4), (l5, 0, z5),
                      (r1, 0, z1), (r1, -HI, z1), (r2, -HI, z2), (r3, -HI, z3), (r4, -y4, z4), (r5, 0, z5)]

            for i in range(5):
                faces += [(p, p + 1, p + 7, p + 6)]
                p += 1

            ct += 1
            x += bl + spacing
        z += bw

    return verts, faces


def tin_base(oh, ow, sloped, slope, faces, verts, steps, x_off):  # uses profile from steps to create sheets
    x = 0
    ct = 0

    while x + steps[ct][0] < ow:
        if sloped:
            z = slope_height(x + steps[ct][0], slope, ow, oh)
        else:
            z = oh

        verts += [(x + steps[ct][0], -steps[ct][1], 0), (x + steps[ct][0], -steps[ct][1], z)]

        ct_pre = ct
        ct = (ct + 1) % len(steps)  # wrap around

        if sloped and x + steps[ct_pre][0] < ow / 2 < x + steps[ct][0]:  # place middle row
            slp = (steps[ct][1] - steps[ct_pre][1]) / (steps[ct][0] - steps[ct_pre][0])  # slope: (y2 - y1) / (x2 - x1)
            y = -steps[ct_pre][1] - (((ow / 2) - x - steps[ct_pre][0]) * slp)
            verts += [(ow / 2, y, 0), (ow / 2, y, oh)]
        if ct == 0:
            x += x_off

    if sloped:
        z = slope_height(ow, slope, ow, oh)
    else:
        z = oh

    ct_pre = (ct - 1) % len(steps)
    slp = (steps[ct][1] - steps[ct_pre][1]) / (steps[ct][0] - steps[ct_pre][0])  # slope: (y2 - y1) / (x2 - x1)
    y = -steps[ct_pre][1] - ((ow - verts[len(verts) - 1][0]) * slp)
    verts += [(ow, y, 0), (ow, y, z)]

    p = 0
    for i in range(int(len(verts) / 2) - 1):
        faces += [(p, p + 1, p + 3, p + 2)]
        p += 2


def tin_normal(oh, ow, sloped, slope, faces, verts):
    qi, ei, si = HI / 2, HI / 4, HI / 8
    tqi, fei = 0.75 / METRIC_INCH, 0.625 / METRIC_INCH
    itqi, ifei = I + tqi, I + fei

    steps = [[0, 0], [HI, tqi], [fei, tqi + ei], [fei + si, I], [I + si, I], [I + ei, tqi + ei], [I + qi, tqi]]
    for i in [itqi, itqi + ifei + I + qi]:
        steps += [[i, 0], [i + ifei, 0], [i + ifei + qi, ei], [i + ifei + I, ei]]
    steps += [[9 / METRIC_INCH - ifei, 0]]

    tin_base(oh, ow, sloped, slope, faces, verts, steps, 9 / METRIC_INCH)

    return verts, faces


def tin_angular(oh, ow, sloped, slope, faces, verts):
    qi, ei = HI / 2, HI / 4
    iqi = I + qi
    pan = 6.5 / 3 / METRIC_INCH

    steps = [[0, 0], [HI, iqi], [I + HI, iqi]]
    for i in [2 * I, 2 * I + pan + HI + iqi]:
        steps += [[i, 0], [i + pan, 0], [i + pan + qi, ei], [i + pan + qi + iqi, ei]]
    steps += [[1 / METRIC_FOOT - pan, 0]]

    tin_base(oh, ow, sloped, slope, faces, verts, steps, 1 / METRIC_FOOT)

    return verts, faces


def tin_screws(oh, ow, is_slope, slope):
    verts, faces = [], []
    m_i = METRIC_INCH  # metric_inch
    rows = int((oh - 4 / m_i) / (16 / m_i))
    
    row_offset = (oh - 4 / m_i) / rows
    column_offset = 9 / m_i
    dia_w = 0.25 / m_i
    dia_s = 0.15 / m_i
    
    x_off = 0.05715
    cur_z = 2 / m_i
    
    while cur_z < oh:
        cur_x = x_off
        
        while cur_x < ow:
            exists = True
            
            if is_slope:
                # calculate height at current x value
                if (cur_x < (ow / 2) and cur_z > ((slope / 12) * (cur_x - (ow / 2))) + oh) or \
                                cur_z > ((-slope / 12) * (cur_x - (ow / 2))) + oh:
                    exists = False
            
            if exists:
                p = len(verts)
                # step by a sixteenth of an inch each time
                for i in range(2):
                    for j in range(-30, 330, 60):
                        x, z = point_rotation((cur_x + dia_w, cur_z), (cur_x, cur_z), radians(j))
                        verts += [(x, i * -((1 / 16) / m_i), z)]
                for i in range(2):
                    for j in range(-30, 330, 60):
                        x, z = point_rotation((cur_x + dia_s, cur_z), (cur_x, cur_z), radians(j))
                        verts += [(x, -((1 / 16) / m_i) + (i * -(0.2 / m_i)), z)]
                        
                # faces
                for i in range(3):
                    tp = p
                    for j in range(5):
                        faces += [(tp, tp + 1, tp + 7, tp + 6)]
                        tp += 1
                    faces += [(tp, tp - 5, tp + 1, tp + 6)]
                    p += 6
                faces += [(p, p + 1, p + 2, p + 5), (p + 5, p + 2, p + 3, p + 4)]
            
            cur_x += column_offset
        cur_z += row_offset            
    
    return verts, faces


def bricks(oh, ow, b_w, b_h, b_offset, gap, ran_offset, b_vary, faces, verts, corners, inverted,
           left, right):
    z, th = 0, 3.5 / METRIC_INCH
    b_offset, b_vary = b_offset / 100, b_vary / 100
    stepped = inverted
    cur_off = inverted

    while z < oh:
        x = -th - gap if corners and stepped and left else 0
        end_x = ow + th + gap if corners and not stepped and right else ow

        if z + b_h > oh:
            b_h = oh - z

        while x < end_x:
            w = b_w
            p = len(verts)

            if x == -th - gap:
                w = th + gap + b_w / 2 - gap / 2
            elif cur_off and x == 0 and (not ran_offset or (corners and not left)):
                w = b_w * b_offset - gap / 2
            elif cur_off and x == 0 and ran_offset:
                v = (b_w / 2) * b_vary
                w = uniform((b_w / 2) - v, (b_w / 2) + v) - gap / 2

            if x + b_w > end_x:
                w = end_x - x

            verts += [(x, 0, z), (x, 0, z + b_h), (x, -th, z), (x, -th, z + b_h), (x + w, -th, z),
                      (x + w, -th, z + b_h), (x + w, 0, z), (x + w, 0, z + b_h)]
            faces += [(p, p + 2, p + 3, p + 1), (p + 2, p + 4, p + 5, p + 3), (p + 4, p + 6, p + 7, p + 5),
                      (p, p + 1, p + 7, p + 6), (p + 1, p + 3, p + 5, p + 7), (p, p + 6, p + 4, p + 2)]

            x += w + gap
        stepped = not stepped
        cur_off = not cur_off
        z += b_h + gap

    return verts, faces


def slope_cutter(oh, ow, slope, corners, b_w):  # creates object to cut slope
    verts, faces = [], []
    if not corners:
        slope = recalculate_slope(slope, oh, ow)
        edge = slope_height(-0.1, slope, ow, oh)

        verts += [(-0.1, 0.5, edge), (-0.1, -0.5, edge), (ow / 2, 0.5, oh), (ow / 2, -0.5, oh), (ow + 0.1, 0.5, edge),
                  (ow + 0.1, -0.5, edge), (-0.1, 0.5, oh + 0.5), (-0.1, -0.5, oh + 0.5), (ow / 2, 0.5, oh + 0.5),
                  (ow / 2, -0.5, oh + 0.5), (ow + 0.1, 0.5, oh + 0.5), (ow + 0.1, -0.5, oh + 0.5)]
    else:
        square = oh - ((slope * ((ow + (2 * b_w)) / 2)) / 12)
        if square <= 0:
            slope = ((24 * oh) / (ow + (2 * b_w))) - 0.01
        edge = slope_height(-b_w - 0.1, slope, ow, oh)

        verts += [(-b_w - 0.1, 0.5, edge), (-b_w - 0.1, -0.5, edge), (ow / 2, 0.5, oh), (ow / 2, -0.5, oh),
                  (ow + b_w + 0.1, 0.5, edge), (ow + b_w + 0.1, -0.5, edge), (-b_w - 0.1, 0.5, oh + 1),
                  (-b_w - 0.1, -0.5, oh + 1), (ow / 2, 0.5, oh + 1), (ow / 2, -0.5, oh + 1),
                  (ow + b_w + 0.1, 0.5, oh + 1), (ow + b_w + 0.1, -0.5, oh + 1)]

    faces += [(0, 2, 3, 1), (2, 4, 5, 3), (0, 1, 7, 6), (1, 3, 9, 7), (3, 5, 11, 9), (5, 4, 10, 11), (4, 2, 8, 10),
              (2, 0, 6, 8), (6, 7, 9, 8), (8, 9, 11, 10)]

    return verts, faces


def mortar(oh, ow, m_d, sloped, slope, corners, left, right, convert, bw, gap, brick, x_off):
    verts, faces = [], []
    depth = 3.5 / METRIC_INCH
    y = depth - m_d if brick else m_d

    # expand mortar if brick has usable corners or if it is a converted object
    x, fx, th = 0, ow, 3.5 / METRIC_INCH

    if convert == "convert":
        fx = ow + (bw / 2)
    if corners and left:
        x = -th - gap + m_d
    if corners and right:
        fx = ow + gap + th - m_d

    if sloped:
        slope = recalculate_slope(slope, oh, ow)
        square = oh - ((slope * (ow / 2)) / 12)  # z height where slope starts
        ls, rs = square, square

        # get correct square height if usable corners is enabled
        if corners and left:
            ls = oh - ((slope * ((ow / 2) + ((bw / 2) - gap))) / 12)
        elif corners and right:
            rs = oh - ((slope * ((ow / 2) + ((bw / 2) - gap))) / 12)

    x += x_off
    if sloped:
        verts += [(x, 0.0, 0.0), (x, -y, 0.0), (fx, -y, 0.0), (fx, 0.0, 0.0), (x, 0.0, ls), (x, -y, ls), (fx, -y, rs),
                  (fx, 0.0, rs), (ow / 2, 0.0, oh), (ow / 2, -y, oh)]
        faces += [(0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (0, 4, 7, 3), (4, 5, 9, 8), (5, 6, 9),
                  (6, 7, 8, 9), (7, 4, 8)]
    else:
        verts += [(x, 0.0, 0.0), (x, -y, 0.0), (fx, -y, 0.0), (fx, 0.0, 0.0), (x, 0.0, oh), (x, -y, oh), (fx, -y, oh),
                  (fx, 0.0, oh)]
        faces += [(0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (0, 4, 7, 3), (4, 5, 6, 7)]

    return verts, faces


def solider_bricks(corner_data, b_h, gap, b_w, oh):
    verts, faces = [], []
    d = 3.75 / METRIC_INCH
    # corner data: x, z, far x, far z
    for i in corner_data:
        x, z = i[0] + gap, i[3]
        bw2 = oh - z if z + b_w > oh else b_w

        if z < oh:
            while x < i[2]:
                bh2 = b_h
                p = len(verts)
               
                if x + b_h + gap > i[2]:
                    bh2 = i[2] - x - gap
                
                verts += [(x, 0.0, z), (x, -d, z), (x + bh2, -d, z), (x + bh2, 0.0, z), (x, 0.0, z + bw2),
                          (x, -d, z + bw2), (x + bh2, -d, z + bw2), (x + bh2, 0.0, z + bw2)]
                x += gap + bh2
                faces += [(p, p + 3, p + 2, p + 1), (p, p + 1, p + 5, p + 4), (p + 1, p + 2, p + 6, p + 5),
                          (p + 2, p + 3, p + 7, p + 6), (p, p + 4, p + 7, p + 3), (p + 4, p + 5, p + 6, p + 7)]
    
    return verts, faces


# TODO: Try and speed up stone generation
def stone_sizes(num, rows, columns, grid):
    block, out = [], []
    row, col = int(num / columns), num % columns

    for r in range(row - 3, row + 4, 1):
        block_row = []
        for c in range(col - 3, col + 4, 1):
            pos = r * columns + c
            if 0 <= r < rows and 0 <= c < columns and type(grid[pos]) == type(1):
                block_row.append(True)
            else:
                block_row.append(False)
        block.append(block_row)

    perms = list(permutations([1, 2, 3, 4], 2))
    perms += [(2, 2), (3, 3), (4, 4)]

    for per in perms:
        # check if all positions are valid
        for start_r in range(4 - per[0], 4, 1):
            for start_c in range(4 - per[1], 4, 1):
                safe = True
                pos = []
                for r in range(0, per[0], 1):
                    for c in range(0, per[1], 1):
                        pos.append((row - 3 + start_r + r) * columns + (col - 3 + start_c + c))
                        if not block[start_r + r][start_c + c]:
                            safe = False

                if safe:
                    out.append({"indices": pos, "height": per[0], "width": per[1]})

    return out


def stone_grid(oh, ow, avw, avh, sr):  # generate grid and figure stone sizes
    hh, hw = avh / 2, avw / 2
    rows, columns = int(oh / hh), int(ow / hw)
    hh2, hw2 = oh / rows, ow / columns
    grid = [i for i in range(rows * columns)]
    out = []
    clist = grid[:]  # list to have numbers chosen from

    while clist:
        # pick number choice
        num = choice(clist) if sr else clist[0]

        # calculate possible sizes for this number
        possible = stone_sizes(num, rows, columns, grid)
        sizes = {i: [] for i in ["2", "3", "4", "6", "8", "9", "12", "16"]}
        for i in possible:
            if str(len(i["indices"])) in sizes:
                sizes[str(len(i["indices"]))].append(i)

        # probability
        if not sr:
            rock = {"indices": [num, num + 1, num + columns, num + columns + 1], "width": 2, "height": 2}
        else:
            lines = {"2": 2, "3": 2, "4": 10, "6": 4, "8": 5, "9": 6, "12": 7, "16": 8}
            pick = []
            for i in sizes.keys():
                if sizes[i]:
                    c = [pick.append(i) for i2 in range(int(lines[i] / 100 * sr + (10 - lines[i])))]
            c = [pick.append("1") for i2 in range(int(0.02 * sr + 8))]

            size = choice(pick)
            if size != "1":
                rock = choice(sizes[size])
            else:
                rock = {"indices": [num], "width": 1, "height": 1}

        out.append(rock)
        for i in rock["indices"]:
            clist.remove(i)
            grid[i] = False
            
    return out, columns, hh2, hw2


def stone_faces(oh, ow, avw, avh, sr, br, b_gap):  # convert grid data to faces
    verts, faces = [], []
    g, depth = b_gap / 2, 0.0508
    stones, columns, hh, hw = stone_grid(oh, ow, avw, avh, sr)
    h, w = hh - (2 * g),  hw - (2 * g)

    for rock in stones:
        if br:
            vary = depth * br * 0.0045
            y = uniform(depth - vary, depth + vary)
        else:
            y = depth

        p = len(verts)
        r, c = int(rock["indices"][0] / columns), rock["indices"][0] % columns
        x, z = (c * hw) + g, (hh * r) + g
        x2 = x + w * rock["width"] + b_gap * (rock["width"] - 1)
        z2 = z + h * rock["height"] + b_gap * (rock["height"] - 1)

        verts += [(x, 0, z), (x, -y, z), (x2, 0, z), (x2, -y, z), (x2, 0, z2), (x2, -y, z2), (x, 0, z2), (x, -y, z2)]
        faces += [(p, p + 1, p + 7, p + 6), (p + 1, p + 3, p + 5, p + 7), (p + 3, p + 2, p + 4, p + 5),
                  (p, p + 6, p + 4, p + 2), (p + 6, p + 7, p + 5, p + 4), (p, p + 2, p + 3, p + 1)]

    return verts, faces


def update_siding(self, context):
    o = context.object

    mats = []
    for i in o.data.materials:
        mats.append(i.name)

    pre_scale = tuple(o.scale.copy())
    if tuple(o.scale) != (1.0, 1.0, 1.0) and o.from_dims != "none":  # apply scale
        bpy.ops.object.transform_apply(scale=True)
    
    # update from_dims
    if o.dims == "none":
        dim = object_dimensions(o)
        o.dims = str(dim[0]) + ", " + str(dim[1])
    else:
        dim_temp = o.dims.split(",")
        dim = [float(dim_temp[0]), float(dim_temp[1])]

    # create object
    if o.object_add == "add":
        verts, faces, corner_data, corner_data_l, v, f = create_siding(context, o.mat, o.tin_types, o.wood_types,
                                                                       o.vinyl_types, o.is_slope, o.over_width,
                                                                       o.over_height, o.board_width, o.slope,
                                                                       o.is_width_vary, o.width_vary, o.is_cutout,
                                                                       o.num_cutouts, o.nc1, o.nc2, o.nc3, o.nc4, o.nc5,
                                                                       o.batten_width, o.board_space, o.is_length_vary,
                                                                       o.length_vary, o.max_boards, o.b_width,
                                                                       o.b_height, o.b_offset, o.b_gap, o.m_depth,
                                                                       o.b_ran_offset, o.b_vary, o.is_corner,
                                                                       o.is_invert, o.is_soldier, o.is_left, o.is_right,
                                                                       o.av_width, o.av_height, o.s_random, o.b_random,
                                                                       o.x_offset)
    elif o.object_add == "convert":
        ow, oh = dim[0], dim[1]
        o.from_dims = "something"

        verts, faces, corner_data, corner_data_l, v, f = create_siding(context, o.mat, o.tin_types, o.wood_types,
                                                                       o.vinyl_types, o.is_slope, ow, oh, o.board_width,
                                                                       o.slope, o.is_width_vary, o.width_vary,
                                                                       o.is_cutout, o.num_cutouts, o.nc1, o.nc2, o.nc3,
                                                                       o.nc4, o.nc5, o.batten_width, o.board_space,
                                                                       o.is_length_vary, o.length_vary, o.max_boards,
                                                                       o.b_width, o.b_height, o.b_offset, o.b_gap,
                                                                       o.m_depth, o.b_ran_offset, o.b_vary, o.is_corner,
                                                                       o.is_invert, o.is_soldier, o.is_left, o.is_right,
                                                                       o.av_width, o.av_height, o.s_random, o.b_random,
                                                                       o.x_offset)
    else:
        return
    old_mesh = o.data
       
    if o.object_add == "add":
        mesh = bpy.data.meshes.new(name="siding")
        mesh.from_pydata(verts, [], faces)
        mesh.update(calc_edges=True)
    elif o.object_add == "convert":
        mesh = bpy.data.meshes.new(name="siding")
        mesh.from_pydata(verts, [], faces)
        mesh.update(calc_edges=True)

        if o.cut_name == "none":  # if cutter object hasn't been created yet
            for ob in context.selected_objects:
                ob.select = False

            cutter = bpy.data.objects.new(o.name + "_cutter", o.data.copy())
            context.scene.objects.link(cutter)
            cutter.location = o.location
            cutter.rotation_euler = o.rotation_euler
            cutter.scale = o.scale
            o.cut_name = cutter.name

            cutter.select = True
            bpy.context.scene.objects.active = cutter
            bpy.ops.object.modifier_add(type="SOLIDIFY")
            pos = len(cutter.modifiers) - 1
            bpy.context.object.modifiers[pos].offset = 0
            bpy.context.object.modifiers[pos].thickness = 1

            o.select = True
            bpy.context.scene.objects.active = o
            x, y, z = None, None, None
            for i in [vert.co for vert in o.data.vertices]:  # find smallest x, y, and z positions
                if x is None:
                    x = i[0]
                    y = i[1]
                elif i[0] < x or (i[0] == x and i[1] < y):
                    x = i[0]
                    y = i[1]
                if z is None:
                    z = i[2]
                elif i[2] < z:
                    z = i[2]

            # find object rotation
            rot = list(rot_from_normal(o.data.polygons[0].normal))
            rot[2] -= radians(270)
            rot[1] -= radians(90)
            position = o.matrix_world * Vector((x, y, z))  # get world space
            coords = [tuple(position), (rot[1], 0, rot[2])]  # rearrange order of rot
            o.previous_rotation = str(rot)
        elif o.cut_name in bpy.data.objects:
            bpy.data.objects[o.cut_name].name = o.name + "_cutter"
            o.cut_name = o.name + "_cutter"
            coords = [o.location, o.rotation_euler]
        else: 
            self.report({"ERROR"}, "Can't Find Cutter Object")

    for i in bpy.data.objects:
        if i.data == old_mesh:
            i.data = mesh
    old_mesh.user_clear()
    bpy.data.meshes.remove(old_mesh)
    
    # create battens if needed
    if v:
        batten_mesh = bpy.data.meshes.new(o.name + "_battens")
        batten_mesh.from_pydata(v, [], f)
        battens = bpy.data.objects.new(batten_mesh.name, batten_mesh)
        context.scene.objects.link(battens)
        battens.location = o.location
        battens.rotation_euler = o.rotation_euler
        battens.scale = o.scale

    bpy.context.scene.objects.active = o
    # create soldiers if needed
    if o.is_soldier and o.is_cutout and o.mat == "5":
        verts2, faces2 = solider_bricks(corner_data, o.b_height, o.b_gap, o.b_width, o.over_height)
        p_mesh = bpy.data.meshes.new("soldier")
        p_mesh.from_pydata(verts2, [], faces2)
        soldier = bpy.data.objects.new("soldier", p_mesh)
        context.scene.objects.link(soldier)
        soldier.location = o.location
        soldier.rotation_euler = o.rotation_euler
        soldier.scale = o.scale

        if o.is_bevel:
            context.scene.objects.active = soldier
            bpy.ops.object.modifier_add(type="BEVEL")
            soldier.modifiers["Bevel"].width = 0.0024384
            soldier.modifiers["Bevel"].use_clamp_overlap = False
            soldier.modifiers["Bevel"].segments = o.res
            bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Bevel")
            context.scene.objects.active = o

    # solidify and bevel as needed
    if o.mat == "2":  # vinyl
        bpy.ops.object.modifier_add(type="BEVEL")
        pos = len(o.modifiers) - 1
        bpy.context.object.modifiers[pos].width = 0.003048
        bpy.context.object.modifiers[pos].use_clamp_overlap = o.vinyl_types != "3"
        bpy.context.object.modifiers[pos].segments = o.res
        bpy.context.object.modifiers[pos].limit_method = "ANGLE"
        bpy.context.object.modifiers[pos].angle_limit = 1.4
        bpy.ops.object.modifier_apply(apply_as="DATA", modifier=o.modifiers[pos].name)
        bpy.ops.object.modifier_add(type="SOLIDIFY")
        bpy.context.object.modifiers[pos].thickness = 0.002
        bpy.ops.object.modifier_apply(apply_as="DATA", modifier=o.modifiers[pos].name)
    elif o.mat == "3":  # tin
        bpy.ops.object.modifier_add(type="SOLIDIFY")
        pos = len(o.modifiers) - 1
        bpy.context.object.modifiers[pos].thickness = 0.0003429
        bpy.ops.object.modifier_apply(apply_as="DATA", modifier=o.modifiers[pos].name)
    elif (o.mat in ("5", "6") or (o.mat == "1" and o.wood_types == "1")) and o.is_bevel:  # brick or stone
        bpy.ops.object.modifier_add(type="BEVEL")
        pos = len(o.modifiers) - 1
        width = o.bevel_width if o.mat == "1" else 0.0024384
        bpy.context.object.modifiers[pos].width = width
        bpy.context.object.modifiers[pos].use_clamp_overlap = False 
        bpy.context.object.modifiers[pos].segments = o.res
        bpy.ops.object.modifier_apply(apply_as="DATA", modifier=o.modifiers[pos].name)

    # cut slope on brick and stone
    if o.mat in ("5", "6") and o.object_add == "add" and o.is_slope:
        verts2, faces2 = slope_cutter(o.over_height, o.over_width, o.slope, o.is_corner, o.b_width)
        bc_s = bpy.data.meshes.new(o.name + "_slope_cut")
        bc_s.from_pydata(verts2, [], faces2)
        cut = bpy.data.objects.new(o.name + "_slope_cut", bc_s)
        context.scene.objects.link(cut)
        cut.location = o.location
        cut.rotation_euler = o.rotation_euler
        cut.scale = o.scale

        ob_to_cut = [o]
        if o.is_soldier and o.is_cutout and o.mat == "5":  # cut soldiers
            ob_to_cut.append(soldier)

        for ob in ob_to_cut:
            bpy.context.scene.objects.active = ob
            bpy.ops.object.modifier_add(type="BOOLEAN")
            pos = len(o.modifiers) - 1
            ob.modifiers[pos].object = cut
            ob.modifiers[pos].solver = "CARVE"
            ob.modifiers[pos].operation = "DIFFERENCE"
            bpy.ops.object.modifier_apply(apply_as="DATA", modifier=ob.modifiers[pos].name)

        o.select, cut.select = False, True
        bpy.ops.object.delete()
        o.select = True

    if o.mat in ("5", "6"):  # mortar
        brick_stone = o.mat == "5"
        depth = round(o.m_depth if o.mat == "5" else o.s_mortar, 5)

        if o.object_add == "convert":
            verts3, faces3 = mortar(dim[1], dim[0], depth, o.is_slope, o.slope, o.is_corner, o.is_left, o.is_right,
                                    o.object_add, o.b_width, o.b_gap, brick_stone, o.x_offset)
        else:
            verts3, faces3 = mortar(o.over_height, o.over_width, depth, o.is_slope, o.slope, o.is_corner, o.is_left,
                                    o.is_right, o.object_add, o.b_width, o.b_gap, brick_stone, o.x_offset)

        bc_m = bpy.data.meshes.new(o.name + "_mortar")
        bc_m.from_pydata(verts3, [], faces3)
        mortar_ob = bpy.data.objects.new(o.name + "_mortar", bc_m)
        context.scene.objects.link(mortar_ob)
        mortar_ob.location = o.location
        mortar_ob.rotation_euler = o.rotation_euler
        mortar_ob.scale = o.scale

        if len(mats) < 2:
            mat = bpy.data.materials.new("mortar_temp")
            mat.use_nodes = True
            mortar_ob.data.materials.append(mat)
        else:
            mat = bpy.data.materials.get(mats[1])
            mortar_ob.data.materials.append(mat)

        # bevel edges slightly so that a subdivision modifier won't mess it up
        o.select = False
        mortar_ob.select = True
        context.scene.objects.active = mortar_ob
        bpy.ops.object.modifier_add(type="BEVEL")
        mortar_ob.modifiers["Bevel"].width = 0.001524
        bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Bevel")
        o.select = True
        mortar_ob.select = False
        context.scene.objects.active = o

    if o.mat == "3" and o.is_screws:  # tin screws
        if o.object_add == "convert":
            verts2, faces2 = tin_screws(dim[1], dim[0], o.is_slope, o.slope)
        else:
            verts2, faces2 = tin_screws(o.over_height, o.over_width, o.is_slope, o.slope)

        screws = bpy.data.meshes.new(o.name + "_screws")
        screws.from_pydata(verts2, [], faces2)
        screw_ob = bpy.data.objects.new(o.name + "_screws", screws)
        context.scene.objects.link(screw_ob)
        screw_ob.location = o.location
        screw_ob.rotation_euler = o.rotation_euler
        o.select = True
        bpy.context.scene.objects.active = o
        bpy.ops.object.join()

    if o.is_cutout and o.object_add == "add":  # cutouts
        bool_stuff = boolean_object(corner_data)

        if o.mat == "5" and o.is_soldier:
            verts3, faces3 = boolean_object(corner_data_l)
            bool_me_l = bpy.data.meshes.new(o.name + "_bool2")
            bool_me_l.from_pydata(verts3, [], faces3)
            bool_ob_l = bpy.data.objects.new(o.name + "_bool2", bool_me_l)
            context.scene.objects.link(bool_ob_l)
            bool_ob_l.location = o.location
            bool_ob_l.rotation_euler = o.rotation_euler
            bool_ob_l.scale = o.scale

        if bool_stuff[0]:
            verts2, faces2 = bool_stuff[0], bool_stuff[1]
            bool_me = bpy.data.meshes.new(o.name + "_bool")
            bool_me.from_pydata(verts2, [], faces2)
            bool_ob = bpy.data.objects.new(o.name + "_bool", bool_me)
            context.scene.objects.link(bool_ob)
            bool_ob.location = o.location
            bool_ob.rotation_euler = o.rotation_euler
            bool_ob.scale = o.scale
            bpy.context.scene.objects.active = o

            bpy.ops.object.modifier_add(type="BOOLEAN")
            pos = len(o.modifiers) - 1
            if o.mat == "5" and o.is_soldier:
                bpy.context.object.modifiers[pos].object = bool_ob_l
            else:
                bpy.context.object.modifiers[pos].object = bool_ob  
            bpy.context.object.modifiers[pos].operation = "DIFFERENCE"
            bpy.ops.object.modifier_apply(apply_as="DATA", modifier=o.modifiers[pos].name)

            for ob in context.selected_objects:
                ob.select = False

            if v:  # battens
                battens.select = True
                context.scene.objects.active = battens
                bpy.ops.object.modifier_add(type="BOOLEAN")
                bpy.context.object.modifiers["Boolean"].object = bool_ob                 
                bpy.context.object.modifiers["Boolean"].operation = "DIFFERENCE"
                bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Boolean")
                battens.select = False
            if o.mat in ("5", "6"):
                bpy.context.scene.objects.active = mortar_ob
                bpy.ops.object.modifier_add(type="BOOLEAN")
                pos = len(mortar_ob.modifiers) - 1
                bpy.context.object.modifiers[pos].object = bool_ob
                bpy.context.object.modifiers[pos].operation = "DIFFERENCE"
                bpy.ops.object.modifier_apply(apply_as="DATA", modifier=mortar_ob.modifiers[pos].name)

            if o.name + "_bool2" in bpy.data.objects:
                bool_ob_l.select = True

            bool_ob.select = True
            bpy.ops.object.delete()
            o.select = True
            bpy.context.scene.objects.active = o
    
    if o.object_add == "convert":  # set position
        o.location = coords[0]
        o.rotation_euler = coords[1]
        cutter = bpy.data.objects[o.cut_name]  # update cutter object scale, rotation, location, origin point

        for ob in context.selected_objects:
            ob.select = False

        cursor = context.scene.cursor_location.copy()
        o.select = True
        bpy.context.scene.objects.active = o
        bpy.ops.view3d.snap_cursor_to_selected()
        o.select = False

        if o.is_cut == "none":
            cutter.select = True
            bpy.context.scene.objects.active = cutter
            bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
            bpy.ops.object.move_to_layer(layers=[i >= 19 for i in range(20)])
            cutter.select = False
            o.is_cut = "cut"

        pre_rot = literal_eval(o.previous_rotation)
        o.select = True
        bpy.context.scene.objects.active = o
        cutter.location = o.location
        cutter.rotation_euler = (coords[1][0] - pre_rot[1], 0, coords[1][2] - pre_rot[2])
        bpy.context.scene.cursor_location = cursor  # change cursor location back to original

        if pre_scale != (1.0, 1.0, 1.0):
            pre_layers = [i for i in bpy.context.scene.layers]
            layers = [i >= 19 for i in range(20)]
            context.scene.layers = layers
            cutter.select, o.select = True, False
            bpy.context.scene.objects.active = cutter
            cutter.scale = (pre_scale[0], pre_scale[2], pre_scale[1])
            bpy.ops.object.transform_apply(scale=True)
            cutter.select = False
            context.scene.layers = pre_layers
            bpy.context.scene.objects.active = o
            o.select = True

        # cut objects
        bpy.ops.object.modifier_add(type="BOOLEAN")
        pos = len(o.modifiers) - 1
        context.object.modifiers[pos].object = bpy.data.objects[o.cut_name]
        context.object.modifiers[pos].solver = "CARVE"
        bpy.ops.object.modifier_apply(apply_as="DATA", modifier=o.modifiers[0].name)

        if o.mat in ("5", "6"):
            o.select, mortar_ob.select = False, True
            bpy.context.scene.objects.active = mortar_ob
            bpy.ops.object.modifier_add(type="BOOLEAN")
            pos = len(mortar_ob.modifiers) - 1
            context.object.modifiers[pos].solver = "CARVE"
            bpy.context.object.modifiers[pos].object = bpy.data.objects[o.cut_name]
            bpy.ops.object.modifier_apply(apply_as="DATA", modifier=mortar_ob.modifiers[pos].name)
            o.select, mortar_ob.select = True, False
            bpy.context.scene.objects.active = o
        elif v:
            o.select, battens.select = False,  True
            bpy.context.scene.objects.active = battens
            bpy.ops.object.modifier_add(type="BOOLEAN")
            context.object.modifiers[pos].solver = "CARVE"
            bpy.context.object.modifiers["Boolean"].object = bpy.data.objects[o.cut_name]
            bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Boolean")
            o.select, battens.select = True, False
            bpy.context.scene.objects.active = o

    if o.mat in ("5", "6"):  # join mortar and brick
        vertex_group(self, context)
        for ob in context.selected_objects:
            ob.select = False
        o.select = True

        if o.is_soldier and o.mat == "5" and o.is_cutout:
            soldier.select = True

        if len(mats) < 2:
            mat = bpy.data.materials.new("siding_" + o.name)
            mat.use_nodes = True
            o.data.materials.append(mat)
        else:
            mat = bpy.data.materials.get(mats[0])
            o.data.materials.append(mat)

        mortar_ob.select = True
        bpy.context.scene.objects.active = o
        bpy.ops.object.join()

    # join battens if needed
    elif v:
        for ob in context.selected_objects:
            ob.select = False

        battens.select, o.select = True, True
        bpy.context.scene.objects.active = o
        bpy.ops.object.join()

    for i in mats:
        if i not in o.data.materials:
            mat = bpy.data.materials.get(i)
            o.data.materials.append(mat)

    unwrap_siding(self, context)
    if o.random_uv and o.unwrap:
        randomize_uv(self, context)


def siding_materials(self, context):
    o = bpy.context.object
    mat, mat2 = None, None

    if o.mat in ("2", "3", "4"):  # vinyl, tin, fiber cement
        rough = 0.3 if o.mat == "2" else 0.18 if o.mat == "3" else 0.35
        mat = glossy_diffuse_material(bpy, o.mat_color, (1.0, 1.0, 1.0), rough, 0.05, "siding_use")
    elif o.mat == "1" or (o.mat == "6" and o.s_mat == "1"):  # wood or stone with image
        if o.col_image == "":
            self.report({"ERROR"}, "JARCH Vis: No Color Image Entered")
            return
        elif o.is_bump and o.norm_image == "":
            self.report({"ERROR"}, "JARCH Vis: No Normal Map Image Entered")
            return

        mat = image_material(bpy, o.im_scale, o.col_image, o.norm_image, o.bump_amo, o.is_bump, "siding_use", False,
                             1.0, 1.0, o.is_rotate, None)
        if mat is not None:
            if o.mat == "6" and len(o.data.materials) >= 2:
                o.data.materials[0] = mat
                o.data.materials[0].name = "siding_" + o.name
            elif len(o.data.materials) < 2 and o.mat == "6":
                self.report({"ERROR"}, "JARCH Vis: Material Needed For Stone Not Found")
                return
        else:
            self.report({"ERROR"}, "JARCH Vis: Images Not Found, Make Sure Path Is Correct")
            return
    elif o.mat == "5" or (o.mat == "6" and o.s_mat == "2"):  # bricks or stone with built-in materials
        if len(o.data.materials) >= 2:  
            mat = brick_material(bpy, o.color_style, o.mat_color, o.mat_color2, o.mat_color3, o.color_sharp,
                                 o.color_scale, o.bump_type, o.brick_bump, o.bump_scale, "siding_use")
            o.data.materials[0] = mat
            o.data.materials[0].name = "siding_" + o.name
        else:
            self.report({"ERROR"}, "JARCH Vis: Material Needed For Bricks//Stones Not Found, Please Update Siding")
            return

    if o.mat in ("5", "6"):  # mortar
        if len(o.data.materials) >= 2:
            mname = "mortar_temp" if "mortar_temp" in o.data.materials else o.data.materials[1].name
            mat2 = mortar_material(bpy, o.mortar_color, o.mortar_bump, mname)
            o.data.materials[1] = mat2
            o.data.materials[1].name = "mortar_" + o.name
        else:
            self.report({"ERROR"}, "JARCH Vis: Material Needed For Mortar Not Found, Please Update Siding")
            return

    # set material
    if len(o.data.materials) >= 1 and mat is not None:
        mat.name = o.name + "_siding"
        o.data.materials[0] = mat
    elif mat is not None:
        mat.name = o.name + "_siding"
        o.data.materials.append(mat)
    elif mat is None:
        self.report({"ERROR"}, "JARCH Vis: Material Could Not Be Created, Possibly Missing Images")

    if len(o.data.materials) >= 2 and o.mat in ("5", "6") and mat2 is not None:
        mat2.name = o.name + "_mortar"
        o.data.materials[1] = mat2
    elif mat2 is not None:
        mat2.name = o.name + "_mortar"
        o.data.append(mat2)
    elif mat is None and o.mat in ("5", "6"):
        self.report({"ERROR"}, "JARCH Vis: Mortar Material Could Not Be Created, Possibly Missing Images")

    for i in bpy.data.materials:
        if not i.users:
            bpy.data.materials.remove(i)


def delete_materials(self, context):
    o = context.object
    if not o.is_material and o.mat not in ("5", "6"):
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
                    space.viewport_shade = "RENDERED" if bpy.context.object.is_preview else "SOLID"


def unwrap_siding(self, context):
    o = context.object

    if o.mat in ("1", "5", "6") and o.unwrap:
        for i in context.selected_objects:
            i.select = False
        o.select = True
        bpy.context.scene.objects.active = o

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        bpy.ops.object.editmode_toggle()
                        override = bpy.context.copy()
                        override["area"] = area
                        override["region"] = region
                        override["active_object"] = bpy.context.selected_objects[0]
                        bpy.ops.mesh.select_all(action="SELECT")
                        bpy.ops.uv.cube_project(override)
                        bpy.ops.object.editmode_toggle()


def vertex_group(self, context):
    o = context.object
    for i in context.selected_objects:
        i.select = False
    o.select = True
    bpy.context.scene.objects.active = o

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    bpy.ops.object.editmode_toggle()
                    if "JARCH" in o.vertex_groups:
                        group = o.vertex_groups.get("JARCH")
                        o.vertex_groups.remove(group)
                    bpy.ops.object.vertex_group_add()
                    bpy.ops.object.vertex_group_assign()
                    active = o.vertex_groups.active
                    active.name = "JARCH"
                    bpy.ops.object.editmode_toggle()


def randomize_uv(self, context):
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
                    
# Properties
bpy.types.Object.mat = EnumProperty(items=(("1", "Wood", ""), ("2", "Vinyl", ""), ("3", "Tin", ""),
                                           ("4", "Fiber Cement", ""), ("5", "Bricks", ""), ("6", "Stone", "")),
                                    default="1", name="", update=update_siding)
bpy.types.Object.tin_types = EnumProperty(items=(("1", "Normal", ""), ("2", "Angular", "")), default="1",
                                          name="", update=update_siding)
bpy.types.Object.wood_types = EnumProperty(items=(("1", "Vertical", ""), ("2", "Vertical: Tongue & Groove", ""),
                                                  ("3", "Vertical: Board & Batten", ""), ("4", "Horizontal: Lap", ""),
                                                  ("5", "Horizontal: Lap Bevel", "")), default="1", name="",
                                           update=update_siding)
bpy.types.Object.vinyl_types = EnumProperty(items=(("1", "Vertical", ""), ("2", "Horizontal: Lap", ""),
                                                   ("3", "Horizontal: Dutch Lap", "")), default="1", name="",
                                            update=update_siding)
# measurements
bpy.types.Object.is_cut = StringProperty(default="none")
bpy.types.Object.cut_name = StringProperty(default="none")
bpy.types.Object.object_add = StringProperty(default="none", update=update_siding)
bpy.types.Object.from_dims = StringProperty(default="none")
bpy.types.Object.previous_rotation = StringProperty(default="none")
bpy.types.Object.dims = StringProperty(default="none")
bpy.types.Object.is_slope = BoolProperty(name="Slope Top?", default=False, update=update_siding)
bpy.types.Object.over_height = FloatProperty(name="Overall Height", min=0.30486, max=15.2399, default=2.4384,
                                             subtype="DISTANCE", description="Height", update=update_siding)
bpy.types.Object.over_width = FloatProperty(name="Overall Width", min=0.609, max=30.4799, default=6.0959,
                                            subtype="DISTANCE", description="Width From Left To Right",
                                            update=update_siding)
bpy.types.Object.board_width = FloatProperty(name="Board Width", min=0.1016, max=24 / METRIC_INCH, default=0.1524,
                                             subtype="DISTANCE", description="Board Width)", update=update_siding)
bpy.types.Object.batten_width = FloatProperty(name="Batten Width", min=0.5 / METRIC_INCH, max=4 / METRIC_INCH,
                                              default=2 / METRIC_INCH, subtype="DISTANCE",
                                              description="Width Of Batten", update=update_siding)
bpy.types.Object.board_space = FloatProperty(name="Board Gap", min=0.05 / METRIC_INCH, max=2 / METRIC_INCH,
                                             default=0.25 / METRIC_INCH, subtype="DISTANCE",
                                             description="Gap Between Boards", update=update_siding)
bpy.types.Object.slope = FloatProperty(name="Slope (X/12)", min=1.0, max=12.0, default=4.0,
                                       description="Slope In RISE/RUN Format In Inches", update=update_siding)
bpy.types.Object.is_width_vary = BoolProperty(name="Vary Width?", default=False, update=update_siding)
bpy.types.Object.width_vary = FloatProperty(name="Width Varience", min=0.001, max=100.0, default=50.0,
                                            subtype="PERCENTAGE", update=update_siding)
bpy.types.Object.is_cutout = BoolProperty(name="Cutouts?", default=False, description="Cut Rectangles Out (Slower)",
                                          update=update_siding)
bpy.types.Object.num_cutouts = IntProperty(name="# Cutouts", min=1, max=6, default=1, update=update_siding)
bpy.types.Object.is_length_vary = BoolProperty(name="Vary Length?", default=False, update=update_siding)
bpy.types.Object.length_vary = FloatProperty(name="Length Varience", min=0.001, max=100.0, default=50.0,
                                             subtype="PERCENTAGE", update=update_siding)
bpy.types.Object.max_boards = IntProperty(name="Max # Of Boards", min=2, max=6, default=2,
                                          description="Max Number Of Boards In Row", update=update_siding)
bpy.types.Object.res = IntProperty(name="Bevel Resolution", min=1, max=6, default=1,
                                   description="Bevel Modifier  # Of Segments", update=update_siding)
bpy.types.Object.is_screws = BoolProperty(name="Screw Heads?", default=False, description="Add Screw Heads?",
                                          update=update_siding)
bpy.types.Object.bevel_width = FloatProperty(name="Bevel Width", min=0.05 / METRIC_INCH, max=0.5 / METRIC_INCH,
                                             default=0.2 / METRIC_INCH, subtype="DISTANCE", update=update_siding)
bpy.types.Object.x_offset = FloatProperty(name="X-Offset", min=-2.0 / METRIC_INCH, max=2.0 / METRIC_INCH, default=0.0,
                                          subtype="DISTANCE", update=update_siding)
# brick
bpy.types.Object.b_width = FloatProperty(name="Brick Width", min=4.0 / METRIC_INCH, max=10.0 / METRIC_INCH,
                                         default=7.625 / METRIC_INCH, subtype="DISTANCE", description="Brick Width",
                                         update=update_siding)
bpy.types.Object.b_height = FloatProperty(name="Brick Height", min=2.0 / METRIC_INCH, max=5.0 / METRIC_INCH,
                                          default=2.375 / METRIC_INCH, subtype="DISTANCE", description="Brick Height",
                                          update=update_siding)
bpy.types.Object.b_ran_offset = BoolProperty(name="Random Offset?", default=False,
                                             description="Random Offset Between Rows", update=update_siding)
bpy.types.Object.b_offset = FloatProperty(name="Brick Offset", subtype="PERCENTAGE", min=0, max=100.0, default=50.0,
                                          description="Brick Offset Between Rows", update=update_siding)
bpy.types.Object.b_gap = FloatProperty(name="Gap", min=0.1 / METRIC_INCH, max=1 / METRIC_INCH,
                                       default=0.5 / METRIC_INCH, subtype="DISTANCE", description="Gap Between Bricks",
                                       update=update_siding)
bpy.types.Object.m_depth = FloatProperty(name="Mortar Depth", min=0.1 / METRIC_INCH, max=1.0 / METRIC_INCH,
                                         default=0.25 / METRIC_INCH, subtype="DISTANCE", description="Mortar Depth",
                                         update=update_siding)
bpy.types.Object.b_vary = FloatProperty(name="Offset Varience", subtype="PERCENTAGE", min=0, max=100, default=50,
                                        description="Offset Varience", update=update_siding)
bpy.types.Object.is_bevel = BoolProperty(name="Bevel?", default=False,
                                         description="Bevel Brick (Slower)", update=update_siding)
bpy.types.Object.bump_type = EnumProperty(items=(("1", "Dimpled", ""), ("2", "Ridges", ""), ("3", "Flaky", ""),
                                                 ("4", "Smooth", "")), name="Bump Type")
bpy.types.Object.color_style = EnumProperty(items=(("constant", "Constant", "Single Color"),
                                                   ("speckled", "Speckled", "Speckled Pattern"),
                                                   ("multiple", "Multiple", "Two Mixed Colors"),
                                                   ("extreme", "Extreme", "Three Mixed Colors")), name="Color Style")
bpy.types.Object.mat_color2 = FloatVectorProperty(name="Color 2", subtype="COLOR", default=(1.0, 1.0, 1.0), min=0.0,
                                                  max=1.0, description="Color 2 For Siding")
bpy.types.Object.mat_color3 = FloatVectorProperty(name="Color 3", subtype="COLOR", default=(1.0, 1.0, 1.0), min=0.0,
                                                  max=1.0, description="Color 3 For Siding")
bpy.types.Object.color_sharp = FloatProperty(name="Color Sharpness", min=0.0, max=10.0, default=1.0,
                                             description="Sharpness Of Color Edges")
bpy.types.Object.mortar_color = FloatVectorProperty(name="Mortar Color", subtype="COLOR", default=(1.0, 1.0, 1.0),
                                                    min=0.0, max=1.0, description="Color For Mortar")
bpy.types.Object.mortar_bump = FloatProperty(name="Mortar Bump", min=0.0, max=1.0, default=0.25,
                                             description="Mortar Bump Amount")
bpy.types.Object.brick_bump = FloatProperty(name="Brick Bump", min=0.0, max=1.0, default=0.25,
                                            description="Brick Bump Amount")
bpy.types.Object.color_scale = FloatProperty(name="Color Scale", min=0.01, max=20.0, default=1.0,
                                             description="Color Scale")
bpy.types.Object.bump_scale = FloatProperty(name="Bump Scale", min=0.01, max=20.0, default=1.0,
                                            description="Bump Scale")
bpy.types.Object.is_corner = BoolProperty(name="Usable Corners?", default=False,
                                          description="Alternate Ends To Allow Corners", update=update_siding)
bpy.types.Object.is_invert = BoolProperty(name="Flip Rows?", default=False, description="Flip Offset Staggering",
                                          update=update_siding)
bpy.types.Object.is_soldier = BoolProperty(name="Soldier Bricks?", default=False, description="Bricks Above Cutouts",
                                           update=update_siding)
bpy.types.Object.is_left = BoolProperty(name="Corners Left?", default=True, description="Usable Corners On Left",
                                        update=update_siding)
bpy.types.Object.is_right = BoolProperty(name="Corners Right?", default=True, description="Usable Corners On Right",
                                         update=update_siding)
# stone
bpy.types.Object.av_width = FloatProperty(name="Average Width", default=10.00 / METRIC_INCH, min=4.00 / METRIC_INCH,
                                          max=36.00 / METRIC_INCH, subtype="DISTANCE",
                                          description="Average Width Of Stones", update=update_siding)
bpy.types.Object.av_height = FloatProperty(name="Average Height", default=6.00 / METRIC_INCH, min=2.00 / METRIC_INCH,
                                           max=36.00 / METRIC_INCH, subtype="DISTANCE",
                                           description="Average Height Of Stones", update=update_siding)
bpy.types.Object.s_random = FloatProperty(name="Size Randomness", default=25.00, max=100.00, min=0.00,
                                          subtype="PERCENTAGE", description="Size Randomness", update=update_siding)
bpy.types.Object.b_random = FloatProperty(name="Bump Randomness", default=25.00, max=100.00, min=0.00,
                                          subtype="PERCENTAGE", description="Bump Randomness", update=update_siding)
bpy.types.Object.s_mortar = FloatProperty(name="Mortar Depth", default=1.5 / METRIC_INCH, min=0.5 / METRIC_INCH,
                                          max=3.0 / METRIC_INCH, subtype="DISTANCE", description="Depth Of Mortar",
                                          update=update_siding)
bpy.types.Object.s_mat = EnumProperty(name="", items=(("1", "Image", ""), ("2", "Procedural", "")), default="1",
                                      description="Stone Material Type")
# materials
bpy.types.Object.is_material = BoolProperty(name="Cycles Materials?", default=False,
                                            description="Adds Cycles Materials", update=delete_materials)
bpy.types.Object.mat_color = FloatVectorProperty(name="Color", subtype="COLOR", default=(1.0, 1.0, 1.0), min=0.0,
                                                 max=1.0, description="Color For Siding")
bpy.types.Object.is_preview = BoolProperty(name="Preview Material?", default=False,
                                           description="Preview Material On Object", update=preview_materials)
bpy.types.Object.im_scale = FloatProperty(name="Image Scale", max=10.0, min=0.1, default=1.0,
                                          description="Change Image Scaling")
bpy.types.Object.col_image = StringProperty(name="", subtype="FILE_PATH", description="File Path For Color Image")
bpy.types.Object.is_bump = BoolProperty(name="Normal Map?", default=False, description="Add Normal To Material?")
bpy.types.Object.norm_image = StringProperty(name="", subtype="FILE_PATH", description="File Path For Normal Map Image")
bpy.types.Object.bump_amo = FloatProperty(name="Normal Stength", min=0.001, max=2.000, default=0.250,
                                          description="Normal Map Strength")
bpy.types.Object.unwrap = BoolProperty(name="UV Unwrap?", default=True, description="UV Unwraps Siding",
                                       update=unwrap_siding)
bpy.types.Object.is_rotate = BoolProperty(name="Rotate Image?", default=False, description="Rotate Image 90 Degrees")
bpy.types.Object.random_uv = BoolProperty(name="Random UV's?", default=True, description="Random UV's",
                                          update=update_siding)
# cutout variables
desc = "X, Y, Height, Width In (ft/m)"
bpy.types.Object.nc1 = StringProperty(name="", default="", description=desc, update=update_siding)
bpy.types.Object.nc2 = StringProperty(name="", default="", description=desc, update=update_siding)
bpy.types.Object.nc3 = StringProperty(name="", default="", description=desc, update=update_siding)
bpy.types.Object.nc4 = StringProperty(name="", default="", description=desc, update=update_siding)
bpy.types.Object.nc5 = StringProperty(name="", default="", description=desc, update=update_siding)
bpy.types.Object.nc6 = StringProperty(name="", default="", description=desc, update=update_siding)


class SidingUpdate(bpy.types.Operator):
    bl_idname = "mesh.jarch_siding_update"
    bl_label = "Update Siding"
    bl_description = "Update Siding, Specifically For Updating Stone"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        update_siding(self, context)
        return {"FINISHED"}


class SidingMesh(bpy.types.Operator):
    bl_idname = "mesh.jarch_siding_mesh" 
    bl_label = "Convert To Mesh"
    bl_description = "Converts Siding Object To Normal Object (No Longer Editable)"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        o = context.object
        o.object_add = "mesh"
        return {"FINISHED"}


class SidingDelete(bpy.types.Operator):
    bl_idname = "mesh.jarch_siding_delete"
    bl_label = "Delete Siding"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        o = context.object
        cutter = None

        if o.object_add == "convert" and o.cut_name in bpy.data.objects:
            cutter = bpy.data.objects[o.cut_name]
            o.select, cutter.select = False, True
            context.scene.objects.active = cutter

            pre_layers = [i for i in bpy.context.scene.layers]
            al = context.scene.active_layer
            context.scene.layers = [i >= 19 for i in range(20)]
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            bpy.ops.object.modifier_remove(modifier="Solidify")
            bpy.ops.object.move_to_layer(layers=[i == al for i in range(20)])
            cutter.name = o.name

            cutter.select = False
            context.scene.layers = pre_layers

        o.select = True
        bpy.context.scene.objects.active = o
        bpy.ops.object.delete()

        if cutter is not None:  # select cutter object if it exists
            cutter.select = True
            context.scene.objects.active = cutter

        for i in bpy.data.materials:
            if i.users == 0:
                bpy.data.materials.remove(i)

        return {"FINISHED"}


class SidingMaterials(bpy.types.Operator):
    bl_idname = "mesh.jarch_siding_materials"
    bl_label = "Generate\\Update Materials"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        siding_materials(self, context)
        return {"FINISHED"}


class SidingPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_jarch_siding"
    bl_label = "JARCH Vis: Siding"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "JARCH Vis"
    
    def draw(self, context):
        layout = self.layout
        if bpy.context.mode == "EDIT_MESH":
            layout.label("JARCH Vis Doesn't Work In Edit Mode", icon="ERROR")
        else:
            o = context.object
            if o is not None:
                if o.type == "MESH":
                    if o.object_add in ("convert", "add"):
                        layout.label("Material:")
                        layout.prop(o, "mat", icon="MATERIAL")
                        layout.label("Type(s):")

                        if o.mat == "1":
                            layout.prop(o, "wood_types", icon="OBJECT_DATA")
                        elif o.mat == "2":
                            layout.prop(o, "vinyl_types", icon="OBJECT_DATA")
                        elif o.mat == "3":
                            layout.prop(o, "tin_types", icon="OBJECT_DATA")
                        elif o.mat == "4":
                            layout.label("Horizontal: Lap", icon="OBJECT_DATA")
                        elif o.mat == "5":
                            layout.label("Bricks", icon="OBJECT_DATA")
                        elif o.mat == "6":
                            layout.label("Stone", icon="OBJECT_DATA")
                        layout.separator()

                        if o.object_add == "add":
                            layout.prop(o, "over_width")
                            layout.prop(o, "over_height")
                            layout.separator()

                        if o.mat not in ("3", "5", "6"):
                            layout.prop(o, "board_width")
                        elif o.mat == "3":
                            layout.label("Sheet Lays: 36 (in)", icon="ARROW_LEFTRIGHT")
                            layout.prop(o, "is_screws", icon="PLUS")

                        if o.mat not in ("5", "6"):  # if not bricks or stone
                            if o.mat == "1" and o.wood_types in ("1", "2"):
                                layout.prop(o, "board_space")
                                layout.separator()
                            if o.mat in ("1", "2") and ((o.vinyl_types == "1" and o.mat == "2") or
                                                        (o.wood_types == "3" and o.mat == "1")):
                                layout.prop(o, "batten_width")
                                if o.batten_width / 2 > (o.board_width / 2) - (0.125 / METRIC_INCH):
                                    layout.label("Max Width: " + str(round(2 * ((o.board_width / 2) -
                                                                                (0.125 / METRIC_INCH)), 3)) +
                                                 " in", icon="ERROR")
                        elif o.mat == "5":  # bricks
                            layout.prop(o, "b_width")
                            layout.prop(o, "b_height")
                            layout.separator()
                            if o.object_add == "add":
                                layout.prop(o, "is_corner", icon="VIEW3D")
                            if not o.is_corner:
                                layout.separator()
                                layout.prop(o, "b_ran_offset", icon="NLA")
                                if not o.b_ran_offset:
                                    layout.prop(o, "b_offset")
                                else:
                                    layout.prop(o, "b_vary")
                            else:
                                layout.separator()
                                layout.prop(o, "is_left", icon="TRIA_LEFT")
                                layout.prop(o, "is_right", icon="TRIA_RIGHT")
                                layout.prop(o, "is_invert", icon="FILE_REFRESH")
                                layout.separator()
                            layout.prop(o, "b_gap")
                            layout.separator()
                            layout.prop(o, "m_depth")
                            layout.separator()

                        if o.object_add == "convert":
                            layout.prop(o, "x_offset")
                            layout.separator()

                        if o.mat in ("5", "6") or (o.mat == "1" and o.wood_types == "1"):
                            layout.prop(o, "is_bevel", icon="MOD_BEVEL")
                            if o.is_bevel and o.mat != "1":
                                layout.prop(o, "res", icon="OUTLINER_DATA_CURVE")
                                layout.separator()
                            elif o.mat == "1" and o.is_bevel:
                                layout.prop(o, "bevel_width")

                        if o.mat == "6":  # stone
                            layout.prop(o, "av_width")
                            layout.prop(o, "av_height")
                            layout.separator()
                            layout.prop(o, "s_random")
                            layout.prop(o, "b_random")
                            layout.separator()
                            layout.prop(o, "b_gap")
                            layout.prop(o, "s_mortar")
                        layout.separator()

                        if o.object_add == "add":
                            layout.prop(o, "is_slope", icon="TRIA_UP")
                            if o.is_slope:
                                layout.label("Pitch x/12", icon="LINCURVE")
                                layout.prop(o, "slope")
                                units = " m"
                                if o.is_corner:
                                    ht = round(o.over_height - ((o.slope * (o.over_width / 2)) / 12), 2)
                                    if ht <= 0:
                                        slope = round(((24 * o.over_height) / o.over_width) - 0.01, 2)
                                        ht = round(o.over_height - ((slope * (o.over_width / 2)) / 12), 2)
                                        layout.label("Max Slope: " + str(slope), icon="ERROR")
                                else:
                                    ht = round(o.over_height - ((o.slope * ((o.over_width + (2 * o.b_width)) / 2))
                                                                / 12), 2)
                                    if ht <= 0:
                                        slope = round(((24 * o.over_height) / o.over_width + (2 * o.b_width)) - 0.01, 2)
                                        ht = round(o.over_height - ((slope * ((o.over_width + (2 * o.b_width)) / 2))
                                                                    / 12), 2)
                                        layout.label("Max Slope: " + str(slope), icon="ERROR")
                                if context.scene.unit_settings.system == "IMPERIAL":
                                    ht = round(METRIC_FOOT * ht, 2)
                                units = " ft"
                                layout.label("Height At Edges: " + str(ht) + units, icon="TEXT")

                        if o.mat not in ("5", "6"):
                            if o.mat == "1" and o.wood_types == "1":
                                layout.prop(o, "is_width_vary", icon="UV_ISLANDSEL")
                                if o.is_width_vary:
                                    layout.prop(o, "width_vary")
                            if o.mat != "3":
                                layout.prop(o, "is_length_vary", icon="NLA")
                            if o.is_length_vary:
                                layout.prop(o, "length_vary")
                                layout.prop(o, "max_boards")
                            if o.mat == "2":
                                layout.separator()
                                layout.prop(o, "res", icon="OUTLINER_DATA_CURVE")
                                layout.separator()

                        if o.object_add == "add":
                            layout.prop(o, "is_cutout", icon="MOD_BOOLEAN")
                            units = " ft" if context.scene.unit_settings.system == "IMPERIAL" else " m"
                            if o.is_cutout:
                                if o.mat == "5":
                                    layout.separator()
                                    layout.prop(o, "is_soldier", icon="DOTSUP")
                                    layout.separator()
                                layout.prop(o, "num_cutouts")
                                layout.separator()
                                layout.label("X, Z, Height, Width in" + units)
                                for i in range(1, o.num_cutouts + 1):
                                    layout.label("Cutout " + str(i) + ":", icon="MOD_BOOLEAN")
                                    layout.prop(o, "nc" + str(i))

                        layout.separator()
                        layout.prop(o, "unwrap", icon="GROUP_UVS")
                        if o.unwrap:
                            layout.prop(o, "random_uv", icon="RNDCURVE")
                        layout.separator()

                        # materials
                        if context.scene.render.engine == "CYCLES":
                            layout.prop(o, "is_material", icon="MATERIAL")
                        else:
                            layout.label("Materials Only Supported With Cycles", icon="POTATO")
                        layout.separator()

                        if o.is_material and context.scene.render.engine == "CYCLES":
                            if o.mat == "6":
                                layout.prop(o, "s_mat")
                                layout.separator()
                            if o.mat in ("2", "3", "4"):
                                layout.prop(o, "mat_color", icon="COLOR")  # vinyl and tin
                            elif o.mat == "1" or (o.mat == "6" and o.s_mat == "1"):  # wood and fiber cement
                                layout.prop(o, "col_image", icon="COLOR")
                                layout.prop(o, "is_bump", icon="SMOOTHCURVE")

                                if o.is_bump:
                                    layout.prop(o, "norm_image", icon="TEXTURE")
                                    layout.prop(o, "bump_amo")

                                layout.prop(o, "im_scale", icon="MAN_SCALE")
                                layout.prop(o, "is_rotate", icon="MAN_ROT")
                            elif o.mat == "5" or (o.mat == "6" and o.s_mat == "2"):  # bricks or stone
                                layout.prop(o, "color_style", icon="COLOR")
                                layout.prop(o, "mat_color", icon="COLOR")

                                if o.color_style != "constant":
                                    layout.prop(o, "mat_color2", icon="COLOR")
                                if o.color_style == "extreme":
                                    layout.prop(o, "mat_color3", icon="COLOR")

                                layout.prop(o, "color_sharp")
                                layout.prop(o, "color_scale")
                                layout.separator()
                                layout.prop(o, "mortar_color", icon="COLOR")
                                layout.prop(o, "mortar_bump")
                                layout.prop(o, "bump_type", icon="SMOOTHCURVE")

                                if o.bump_type != "4":
                                    layout.prop(o, "brick_bump")
                                    layout.prop(o, "bump_scale")

                            if o.mat == "6":
                                layout.separator()
                                layout.prop(o, "mortar_color", icon="COLOR")
                                layout.prop(o, "mortar_bump")
                                layout.prop(o, "bump_scale")

                            layout.separator()
                            layout.operator("mesh.jarch_siding_materials", icon="MATERIAL")
                            layout.separator()
                            layout.prop(o, "is_preview", icon="SCENE")

                        layout.separator()
                        layout.separator()
                        layout.operator("mesh.jarch_siding_update", icon="FILE_REFRESH")
                        layout.operator("mesh.jarch_siding_mesh", icon="OUTLINER_OB_MESH")
                        layout.operator("mesh.jarch_siding_delete", icon="CANCEL")
                        layout.operator("mesh.jarch_siding_add", icon="UV_ISLANDSEL")
                    else:
                        if o.object_add != "mesh":
                            layout.operator("mesh.jarch_siding_convert", icon="FILE_REFRESH")
                            layout.operator("mesh.jarch_siding_add", icon="UV_ISLANDSEL")
                        else:
                            layout.label("This Is A JARCH Vis Mesh Object", icon="INFO")
                else:
                    layout.label("Only Mesh Objects Can Be Used", icon="ERROR")
            else:
                layout.operator("mesh.jarch_siding_add", icon="UV_ISLANDSEL")


class SidingAdd(bpy.types.Operator):
    bl_idname = "mesh.jarch_siding_add"
    bl_label = "Add Siding"
    bl_description = "JARCH Vis: Siding Generator"

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        o = bpy.context.scene.objects.active
        o.object_add = "add"
        return {"FINISHED"}


class SidingConvert(bpy.types.Operator):
    bl_idname = "mesh.jarch_siding_convert"
    bl_label = "Convert To Siding"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        o = context.object
        o.object_add = "convert"
        return {"FINISHED"}


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
