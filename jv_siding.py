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

from itertools import permutations
import bpy
from bpy.props import FloatVectorProperty, BoolProperty, FloatProperty, StringProperty, IntProperty, EnumProperty
from math import sqrt, atan, asin, sin, cos, tan
from random import uniform, choice
from mathutils import Euler, Vector
from . jv_materials import *
import jv_properties
import bmesh
from . jv_utils import rot_from_normal, object_dimensions, point_rotation, METRIC_INCH, METRIC_FOOT, I, HI
from ast import literal_eval


# manages sorting out which type of siding needs to be create, gets corner data for cutout objects
def create_siding(context, mat, tin_types, wood_types, vinyl_types, sloped, ow, oh, bw, slope, is_width_vary,
                  width_vary, is_cutout, num_cutouts, nc1, nc2, nc3, nc4, nc5, baw, spacing, is_length_vary,
                  length_vary, max_boards, b_w, b_h, b_offset, b_gap, b_ran_offset, b_vary, is_corner, is_invert,
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


def tin_screws(oh, ow, sloped, slope):
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

            if sloped:
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
            if 0 <= r < rows and 0 <= c < columns and not isinstance(grid[pos], bool):
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
    if tuple(o.scale) != (1.0, 1.0, 1.0) and o.jv_pre_jv_dims != "none":  # apply scale
        bpy.ops.object.transform_apply(scale=True)

    # update jv_pre_jv_dims
    if o.jv_dims == "none":
        dim = object_dimensions(o)
        o.jv_dims = str(dim[0]) + ", " + str(dim[1])
    else:
        dim_temp = o.jv_dims.split(",")
        dim = [float(dim_temp[0]), float(dim_temp[1])]

    # create object
    if o.jv_object_add == "add":
        verts, faces, corner_data, corner_data_l, v, f = create_siding(context, o.jv_siding_types, o.tin_types,
                                                                       o.wood_types, o.vinyl_types, o.jv_is_slope,
                                                                       o.jv_over_width, o.jv_over_height, o.jv_b_width,
                                                                       o.jv_slope, o.jv_is_width_vary, o.jv_width_vary,
                                                                       o.jv_is_cutout, o.jv_num_cutouts, o.jv_nc1,
                                                                       o.jv_nc2, o.jv_nc3, o.jv_nc4, o.jv_nc5,
                                                                       o.jv_batten_width, o.jv_spacing,
                                                                       o.jv_is_length_vary, o.jv_length_vary,
                                                                       o.jv_max_boards, o.jv_br_width, o.jv_br_height,
                                                                       o.jv_br_offset, o.jv_br_gap, o.jv_br_ran_offset,
                                                                       o.jv_br_vary, o.jv_is_corner, o.jv_is_invert,
                                                                       o.jv_is_soldier, o.jv_is_left, o.jv_is_right,
                                                                       o.jv_av_width, o.jv_av_height,  o.jv_random_size,
                                                                       o.jv_random_bump, o.jv_x_offset)
    elif o.jv_object_add == "convert":
        ow, oh = dim[0], dim[1]
        o.jv_pre_jv_dims = "something"

        verts, faces, corner_data, corner_data_l, v, f = create_siding(context, o.jv_siding_types, o.tin_types,
                                                                       o.wood_types, o.vinyl_types, o.jv_is_slope, ow,
                                                                       oh, o.jv_b_width, o.jv_slope, o.jv_is_width_vary,
                                                                       o.jv_width_vary, o.jv_is_cutout,
                                                                       o.jv_num_cutouts, o.jv_nc1, o.jv_nc2, o.jv_nc3,
                                                                       o.jv_nc4, o.jv_nc5, o.jv_batten_width,
                                                                       o.jv_spacing,  o.jv_is_length_vary,
                                                                       o.jv_length_vary, o.jv_max_boards, o.jv_br_width,
                                                                       o.jv_br_height, o.jv_br_offset, o.jv_br_gap,
                                                                       o.jv_br_ran_offset, o.jv_br_vary, o.jv_is_corner,
                                                                       o.jv_is_invert, o.jv_is_soldier, o.jv_is_left,
                                                                       o.jv_is_right, o.jv_av_width, o.jv_av_height,
                                                                       o.jv_random_size, o.jv_random_bump,
                                                                       o.jv_x_offset)
    else:
        return
    old_mesh = o.data

    if o.jv_object_add == "add":
        mesh = bpy.data.meshes.new(name="siding")
        mesh.from_pydata(verts, [], faces)
        mesh.update(calc_edges=True)
    elif o.jv_object_add == "convert":
        mesh = bpy.data.meshes.new(name="siding")
        mesh.from_pydata(verts, [], faces)
        mesh.update(calc_edges=True)

        if o.jv_cut_name == "none":  # if cutter object hasn't been created yet
            for ob in context.selected_objects:
                ob.select = False

            cutter = bpy.data.objects.new(o.name + "_cutter", o.data.copy())
            context.scene.objects.link(cutter)
            cutter.location = o.location
            cutter.rotation_euler = o.rotation_euler
            cutter.scale = o.scale
            o.jv_cut_name = cutter.name

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
            o.jv_previous_rotation = str(rot)
        elif o.jv_cut_name in bpy.data.objects:
            bpy.data.objects[o.jv_cut_name].name = o.name + "_cutter"
            o.jv_cut_name = o.name + "_cutter"
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
    if o.jv_is_soldier and o.jv_is_cutout and o.jv_siding_types == "5":
        verts2, faces2 = solider_bricks(corner_data, o.jv_br_height, o.jv_br_gap, o.jv_br_width, o.jv_over_height)
        p_mesh = bpy.data.meshes.new("soldier")
        p_mesh.from_pydata(verts2, [], faces2)
        soldier = bpy.data.objects.new("soldier", p_mesh)
        context.scene.objects.link(soldier)
        soldier.location = o.location
        soldier.rotation_euler = o.rotation_euler
        soldier.scale = o.scale

        if o.jv_is_bevel:
            context.scene.objects.active = soldier
            bpy.ops.object.modifier_add(type="BEVEL")
            soldier.modifiers["Bevel"].width = 0.0024384
            soldier.modifiers["Bevel"].use_clamp_overlap = False
            soldier.modifiers["Bevel"].segments = o.jv_res
            bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Bevel")
            context.scene.objects.active = o

    # solidify and bevel as needed
    if o.jv_siding_types == "2":  # vinyl
        bpy.ops.object.modifier_add(type="BEVEL")
        pos = len(o.modifiers) - 1
        bpy.context.object.modifiers[pos].width = 0.003048
        bpy.context.object.modifiers[pos].use_clamp_overlap = o.vinyl_types != "3"
        bpy.context.object.modifiers[pos].segments = o.jv_res
        bpy.context.object.modifiers[pos].limit_method = "ANGLE"
        bpy.context.object.modifiers[pos].angle_limit = 1.4
        bpy.ops.object.modifier_apply(apply_as="DATA", modifier=o.modifiers[pos].name)
        bpy.ops.object.modifier_add(type="SOLIDIFY")
        bpy.context.object.modifiers[pos].thickness = 0.002
        bpy.ops.object.modifier_apply(apply_as="DATA", modifier=o.modifiers[pos].name)
    elif o.jv_siding_types == "3":  # tin
        bpy.ops.object.modifier_add(type="SOLIDIFY")
        pos = len(o.modifiers) - 1
        bpy.context.object.modifiers[pos].thickness = 0.0003429
        bpy.ops.object.modifier_apply(apply_as="DATA", modifier=o.modifiers[pos].name)
    # brick or stone
    elif (o.jv_siding_types in ("5", "6") or (o.jv_siding_types == "1" and o.wood_types == "1")) and o.jv_is_bevel:
        bpy.ops.object.modifier_add(type="BEVEL")
        pos = len(o.modifiers) - 1
        width = o.jv_bevel_width if o.jv_siding_types == "1" else 0.0024384
        bpy.context.object.modifiers[pos].width = width
        bpy.context.object.modifiers[pos].use_clamp_overlap = False
        bpy.context.object.modifiers[pos].segments = o.jv_res
        bpy.ops.object.modifier_apply(apply_as="DATA", modifier=o.modifiers[pos].name)

    # cut slope on brick and stone
    if o.jv_siding_types in ("5", "6") and o.jv_object_add == "add" and o.jv_is_slope:
        verts2, faces2 = slope_cutter(o.jv_over_height, o.jv_over_width, o.jv_slope, o.is_corner, o.jv_br_width)
        bc_s = bpy.data.meshes.new(o.name + "_slope_cut")
        bc_s.from_pydata(verts2, [], faces2)
        cut = bpy.data.objects.new(o.name + "_slope_cut", bc_s)
        context.scene.objects.link(cut)
        cut.location = o.location
        cut.rotation_euler = o.rotation_euler
        cut.scale = o.scale

        ob_to_cut = [o]
        if o.jv_is_soldier and o.jv_is_cutout and o.jv_siding_types == "5":  # cut soldiers
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

    if o.jv_siding_types in ("5", "6"):  # mortar
        brick_stone = o.jv_siding_types == "5"
        depth = o.jv_br_m_depth if o.jv_siding_types == "5" else o.jv_st_m_depth

        if o.jv_object_add == "convert":
            verts3, faces3 = mortar(dim[1], dim[0], depth, o.jv_is_slope, o.jv_slope, o.jv_is_corner, o.jv_is_left,
                                    o.jv_is_right, o.jv_object_add, o.jv_br_width, o.jv_br_gap, brick_stone,
                                    o.jv_x_offset)
        else:
            verts3, faces3 = mortar(o.jv_over_height, o.jv_over_width, depth, o.jv_is_slope, o.jv_slope, o.jv_is_corner,
                                    o.jv_is_left, o.jv_is_right, o.jv_object_add, o.jv_br_width, o.jv_br_gap,
                                    brick_stone, o.jv_x_offset)

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

    if o.jv_siding_types == "3" and o.jv_is_screws:  # tin screws
        if o.jv_object_add == "convert":
            verts2, faces2 = tin_screws(dim[1], dim[0], o.jv_is_slope, o.jv_slope)
        else:
            verts2, faces2 = tin_screws(o.jv_over_height, o.jv_over_width, o.jv_is_slope, o.jv_slope)

        screws = bpy.data.meshes.new(o.name + "_screws")
        screws.from_pydata(verts2, [], faces2)
        screw_ob = bpy.data.objects.new(o.name + "_screws", screws)
        context.scene.objects.link(screw_ob)
        screw_ob.location = o.location
        screw_ob.rotation_euler = o.rotation_euler
        o.select = True
        bpy.context.scene.objects.active = o
        bpy.ops.object.join()

    if o.jv_is_cutout and o.jv_object_add == "add":  # cutouts
        bool_stuff = boolean_object(corner_data)

        if o.jv_siding_types == "5" and o.jv_is_soldier:
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
            if o.jv_siding_types == "5" and o.jv_is_soldier:
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
            if o.jv_siding_types in ("5", "6"):
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

    if o.jv_object_add == "convert":  # set position
        o.location = coords[0]
        o.rotation_euler = coords[1]
        cutter = bpy.data.objects[o.jv_cut_name]  # update cutter object scale, rotation, location, origin point

        for ob in context.selected_objects:
            ob.select = False

        cursor = context.scene.cursor_location.copy()
        o.select = True
        bpy.context.scene.objects.active = o
        bpy.ops.view3d.snap_cursor_to_selected()
        o.select = False

        if o.jv_is_cut == "none":
            cutter.select = True
            bpy.context.scene.objects.active = cutter
            bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
            bpy.ops.object.move_to_layer(layers=[i >= 19 for i in range(20)])
            cutter.select = False
            o.jv_is_cut = "cut"

        pre_rot = literal_eval(o.jv_previous_rotation)
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
        context.object.modifiers[pos].object = bpy.data.objects[o.jv_cut_name]
        context.object.modifiers[pos].solver = "CARVE"
        bpy.ops.object.modifier_apply(apply_as="DATA", modifier=o.modifiers[0].name)

        if o.jv_siding_types in ("5", "6"):
            o.select, mortar_ob.select = False, True
            bpy.context.scene.objects.active = mortar_ob
            bpy.ops.object.modifier_add(type="BOOLEAN")
            pos = len(mortar_ob.modifiers) - 1
            context.object.modifiers[pos].solver = "CARVE"
            bpy.context.object.modifiers[pos].object = bpy.data.objects[o.jv_cut_name]
            bpy.ops.object.modifier_apply(apply_as="DATA", modifier=mortar_ob.modifiers[pos].name)
            o.select, mortar_ob.select = True, False
            bpy.context.scene.objects.active = o
        elif v:
            o.select, battens.select = False,  True
            bpy.context.scene.objects.active = battens
            bpy.ops.object.modifier_add(type="BOOLEAN")
            context.object.modifiers[pos].solver = "CARVE"
            bpy.context.object.modifiers["Boolean"].object = bpy.data.objects[o.jv_cut_name]
            bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Boolean")
            o.select, battens.select = True, False
            bpy.context.scene.objects.active = o

    if o.jv_siding_types in ("5", "6"):  # join mortar and brick
        vertex_group(self, context)
        for ob in context.selected_objects:
            ob.select = False
        o.select = True

        if o.jv_is_soldier and o.jv_siding_types == "5" and o.jv_is_cutout:
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
    if o.jv_is_random_uv and o.jv_is_unwrap:
        randomize_uv(self, context)


def siding_materials(self, context):
    o = bpy.context.object
    mat, mat2 = None, None

    if o.mat in ("2", "3", "4"):  # vinyl, tin, fiber cement
        rough = 0.3 if o.jv_siding_types == "2" else 0.18 if o.jv_siding_types == "3" else 0.35
        mat = glossy_diffuse_material(bpy, o.jv_rgba_color, (1.0, 1.0, 1.0), rough, 0.05, "siding_use")
    elif o.jv_siding_types == "1" or (o.jv_siding_types == "6" and o.jv_sb_mat_type == "1"):  # wood or stone with image
        if o.jv_col_image == "":
            self.report({"ERROR"}, "JARCH Vis: No Color Image Entered")
            return
        elif o.jv_is_bump and o.jv_norm_image == "":
            self.report({"ERROR"}, "JARCH Vis: No Normal Map Image Entered")
            return

        mat = image_material(bpy, o.jv_im_scale, o.jv_col_image, o.jv_norm_image, o.jv_bump_amo, o.jv_is_bump,
                             "siding_use", False, 1.0, 1.0, o.jv_is_rotate, None)
        if mat is not None:
            if o.jv_siding_types == "6" and len(o.data.materials) >= 2:
                o.data.materials[0] = mat
                o.data.materials[0].name = "siding_" + o.name
            elif len(o.data.materials) < 2 and o.jv_siding_types == "6":
                self.report({"ERROR"}, "JARCH Vis: Material Needed For Stone Not Found")
                return
        else:
            self.report({"ERROR"}, "JARCH Vis: Images Not Found, Make Sure Path Is Correct")
            return
    # bricks or stone with built-in materials
    elif o.jv_siding_types == "5" or (o.jv_siding_types == "6" and o.jv_sb_mat_type == "2"):
        if len(o.data.materials) >= 2:
            mat = brick_material(bpy, o.jv_color_style, o.jv_rgba_color, o.jv_color2, o.jv_color3, o.jv_color_sharp,
                                 o.jv_color_scale, o.jv_bump_type, o.jv_brick_bump, o.jv_bump_scale, "siding_use")
            o.data.materials[0] = mat
            o.data.materials[0].name = "siding_" + o.name
        else:
            self.report({"ERROR"}, "JARCH Vis: Material Needed For Bricks//Stones Not Found, Please Update Siding")
            return

    if o.jv_siding_types in ("5", "6"):  # mortar
        if len(o.data.materials) >= 2:
            mname = "mortar_temp" if "mortar_temp" in o.data.materials else o.data.materials[1].name
            mat2 = mortar_material(bpy, o.jv_mortar_color, o.jv_mortar_bump, mname)
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

    if len(o.data.materials) >= 2 and o.jv_siding_types in ("5", "6") and mat2 is not None:
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


def unwrap_siding(self, context):
    o = context.object

    if o.jv_siding_types in ("1", "5", "6") and o.jv_is_unwrap:
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


class SidingUpdate(bpy.types.Operator):
    bl_idname = "mesh.jv_siding_update"
    bl_label = "Update Siding"
    bl_description = "Update Siding, Specifically For Updating Stone"
    bl_options = {"UNDO", "INTERNAL"}

    def execute(self, context):
        update_siding(self, context)
        return {"FINISHED"}


class SidingDelete(bpy.types.Operator):
    bl_idname = "mesh.jv_siding_delete"
    bl_label = "Delete Siding"
    bl_options = {"UNDO", "INTERNAL"}

    def execute(self, context):
        o = context.object
        cutter = None

        if o.jv_object_add == "convert" and o.jv_cut_name in bpy.data.objects:
            cutter = bpy.data.objects[o.jv_cut_name]
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
    bl_idname = "mesh.jv_siding_materials"
    bl_label = "Generate\\Update Materials"
    bl_options = {"UNDO", "INTERNAL"}

    def execute(self, context):
        siding_materials(self, context)
        return {"FINISHED"}


class SidingPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_jv_siding"
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
                    if o.jv_object_add in ("convert", "add"):
                        layout.label("Material:")
                        layout.prop(o, "jv_siding_types", icon="MATERIAL")
                        layout.label("Type(s):")

                        if o.jv_siding_types == "1":
                            layout.prop(o, "wood_types", icon="OBJECT_DATA")
                        elif o.jv_siding_types == "2":
                            layout.prop(o, "vinyl_types", icon="OBJECT_DATA")
                        elif o.jv_siding_types == "3":
                            layout.prop(o, "tin_types", icon="OBJECT_DATA")
                        elif o.jv_siding_types == "4":
                            layout.label("Horizontal: Lap", icon="OBJECT_DATA")
                        elif o.jv_siding_types == "5":
                            layout.label("Bricks", icon="OBJECT_DATA")
                        elif o.jv_siding_types == "6":
                            layout.label("Stone", icon="OBJECT_DATA")
                        layout.separator()

                        if o.jv_object_add == "add":
                            layout.prop(o, "jv_over_width")
                            layout.prop(o, "jv_over_height")
                            layout.separator()

                        if o.jv_siding_types not in ("3", "5", "6"):
                            layout.prop(o, "jv_b_width")
                        elif o.jv_siding_types == "3":
                            layout.label("Sheet Lays: 36 (in)", icon="ARROW_LEFTRIGHT")
                            layout.prop(o, "jv_is_screws", icon="PLUS")

                        if o.jv_siding_types not in ("5", "6"):  # if not bricks or stone
                            if o.jv_siding_types == "1" and o.wood_types in ("1", "2"):
                                layout.prop(o, "jv_spacing")
                                layout.separator()
                            if o.jv_siding_types in ("1", "2") and ((o.vinyl_types == "1" and o.jv_siding_types == "2")
                                                                    or (o.wood_types == "3"
                                                                        and o.jv_siding_types == "1")):
                                layout.prop(o, "jv_batten_width")
                                if o.jv_batten_width / 2 > (o.jv_b_width / 2) - (0.125 / METRIC_INCH):
                                    layout.label("Max Width: " + str(round(2 * ((o.jv_b_width / 2) -
                                                                                (0.125 / METRIC_INCH)), 3)) +
                                                 " in", icon="ERROR")
                        elif o.jv_siding_types == "5":  # bricks
                            layout.prop(o, "jv_br_width")
                            layout.prop(o, "jv_br_height")
                            layout.separator()
                            if o.jv_object_add == "add":
                                layout.prop(o, "jv_is_corner", icon="VIEW3D")
                            if not o.jv_is_corner:
                                layout.separator()
                                layout.prop(o, "jv_br_ran_offset", icon="NLA")
                                if not o.jv_br_ran_offset:
                                    layout.prop(o, "jv_br_offset")
                                else:
                                    layout.prop(o, "jv_br_vary")
                            else:
                                layout.separator()
                                layout.prop(o, "jv_is_left", icon="TRIA_LEFT")
                                layout.prop(o, "jv_is_right", icon="TRIA_RIGHT")
                                layout.prop(o, "jv_is_invert", icon="FILE_REFRESH")
                                layout.separator()
                            layout.prop(o, "jv_br_gap")
                            layout.separator()
                            layout.prop(o, "jv_br_m_depth")
                            layout.separator()

                        if o.jv_object_add == "convert":
                            layout.prop(o, "jv_x_offset")
                            layout.separator()

                        if o.jv_siding_types in ("5", "6") or (o.jv_siding_types == "1" and o.wood_types == "1"):
                            layout.prop(o, "jv_is_bevel", icon="MOD_BEVEL")
                            if o.jv_is_bevel and o.jv_siding_types != "1":
                                layout.prop(o, "jv_res", icon="OUTLINER_DATA_CURVE")
                                layout.separator()
                            elif o.jv_siding_types == "1" and o.jv_is_bevel:
                                layout.prop(o, "jv_bevel_width")

                        if o.jv_siding_types == "6":  # stone
                            layout.prop(o, "jv_av_width")
                            layout.prop(o, "jv_av_height")
                            layout.separator()
                            layout.prop(o, "jv_random_size")
                            layout.prop(o, "jv_random_bump")
                            layout.separator()
                            layout.prop(o, "jv_br_gap")
                            layout.prop(o, "jv_st_m_depth")
                        layout.separator()

                        if o.jv_object_add == "add":
                            layout.prop(o, "jv_is_slope", icon="TRIA_UP")
                            if o.jv_is_slope:
                                layout.label("Pitch x/12", icon="LINCURVE")
                                layout.prop(o, "jv_slope")
                                units = " m"
                                if o.jv_is_corner:
                                    ht = round(o.jv_over_height - ((o.jv_slope * (o.jv_over_width / 2)) / 12), 2)
                                    if ht <= 0:
                                        slope = round(((24 * o.jv_over_height) / o.jv_over_width) - 0.01, 2)
                                        ht = round(o.jv_over_height - ((slope * (o.jv_over_width / 2)) / 12), 2)
                                        layout.label("Max Slope: " + str(slope), icon="ERROR")
                                else:
                                    ht = round(o.jv_over_height - ((o.jv_slope * ((o.jv_over_width +
                                                                                   (2 * o.jv_br_width)) / 2)) / 12), 2)
                                    if ht <= 0:
                                        slope = round(((24 * o.jv_over_height) / o.jv_over_width + (2 * o.jv_br_width))
                                                      - 0.01, 2)
                                        ht = round(o.jv_over_height - ((slope * ((o.jv_over_width + (2 * o.jv_br_width))
                                                                                 / 2)) / 12), 2)
                                        layout.label("Max Slope: " + str(slope), icon="ERROR")
                                if context.scene.unit_settings.system == "IMPERIAL":
                                    ht = round(METRIC_FOOT * ht, 2)
                                    units = " ft"
                                layout.label("Height At Edges: " + str(ht) + units, icon="TEXT")

                        if o.jv_siding_types not in ("5", "6"):
                            if o.jv_siding_types == "1" and o.wood_types == "1":
                                layout.prop(o, "jv_is_width_vary", icon="UV_ISLANDSEL")
                                if o.jv_is_width_vary:
                                    layout.prop(o, "jv_width_vary")
                            if o.jv_siding_types != "3":
                                layout.prop(o, "jv_is_length_vary", icon="NLA")
                            if o.jv_is_length_vary:
                                layout.prop(o, "jv_length_vary")
                                layout.prop(o, "jv_max_boards")
                            if o.jv_siding_types == "2":
                                layout.separator()
                                layout.prop(o, "jv_res", icon="OUTLINER_DATA_CURVE")
                                layout.separator()

                        if o.jv_object_add == "add":
                            layout.prop(o, "jv_is_cutout", icon="MOD_BOOLEAN")
                            units = " ft" if context.scene.unit_settings.system == "IMPERIAL" else " m"
                            if o.jv_is_cutout:
                                if o.jv_siding_types == "5":
                                    layout.separator()
                                    layout.prop(o, "jv_is_soldier", icon="DOTSUP")
                                    layout.separator()
                                layout.prop(o, "jv_num_cutouts")
                                layout.separator()
                                layout.label("X, Z, Height, Width in" + units)
                                for i in range(1, o.jv_num_cutouts + 1):
                                    layout.label("Cutout " + str(i) + ":", icon="MOD_BOOLEAN")
                                    layout.prop(o, "jv_nc" + str(i))

                        layout.separator()
                        layout.prop(o, "jv_is_unwrap", icon="GROUP_UVS")
                        if o.jv_is_unwrap:
                            layout.prop(o, "jv_is_random_uv", icon="RNDCURVE")
                        layout.separator()

                        # materials
                        if context.scene.render.engine == "CYCLES":
                            layout.prop(o, "jv_is_material", icon="MATERIAL")
                        else:
                            layout.label("Materials Only Supported With Cycles", icon="POTATO")
                        layout.separator()

                        if o.jv_is_material and context.scene.render.engine == "CYCLES":
                            if o.jv_siding_types == "6":
                                layout.prop(o, "jv_sb_mat_type")
                                layout.separator()
                            if o.jv_siding_types in ("2", "3", "4"):
                                layout.prop(o, "jv_rgba_color", icon="COLOR")  # vinyl and tin
                            # wood and fiber cement
                            elif o.jv_siding_types == "1" or (o.jv_siding_types == "6" and o.jv_sb_mat_type == "1"):
                                layout.prop(o, "jv_col_image", icon="COLOR")
                                layout.prop(o, "jv_is_bump", icon="SMOOTHCURVE")

                                if o.jv_is_bump:
                                    layout.prop(o, "jv_norm_image", icon="TEXTURE")
                                    layout.prop(o, "jv_bump_amo")

                                layout.prop(o, "jv_im_scale", icon="MAN_SCALE")
                                layout.prop(o, "jv_is_rotate", icon="MAN_ROT")
                            # bricks or stone
                            elif o.jv_siding_types == "5" or (o.jv_siding_types == "6" and o.jv_sb_mat_type == "2"):
                                layout.prop(o, "jv_color_style", icon="COLOR")
                                layout.prop(o, "jv_rgba_color", icon="COLOR")

                                if o.jv_color_style != "constant":
                                    layout.prop(o, "jv_color2", icon="COLOR")
                                if o.jv_color_style == "extreme":
                                    layout.prop(o, "jv_color3", icon="COLOR")

                                layout.prop(o, "jv_color_sharp")
                                layout.prop(o, "jv_color_scale")
                                layout.separator()
                                layout.prop(o, "jv_mortar_color", icon="COLOR")
                                layout.prop(o, "jv_mortar_bump")
                                layout.prop(o, "jv_bump_type", icon="SMOOTHCURVE")

                                if o.jv_bump_type != "4":
                                    layout.prop(o, "jv_brick_bump")
                                    layout.prop(o, "jv_bump_scale")

                            if o.jv_siding_types == "6":
                                layout.separator()
                                layout.prop(o, "jv_mortar_color", icon="COLOR")
                                layout.prop(o, "jv_mortar_bump")
                                layout.prop(o, "jv_bump_scale")

                            layout.separator()
                            layout.operator("mesh.jv_siding_materials", icon="MATERIAL")
                            layout.separator()
                            layout.prop(o, "jv_is_preview", icon="SCENE")

                        layout.separator()
                        layout.separator()
                        layout.operator("mesh.jv_siding_update", icon="FILE_REFRESH")
                        layout.operator("mesh.jv_siding_delete", icon="CANCEL")
                        layout.operator("mesh.jv_siding_add", icon="UV_ISLANDSEL")
                    else:
                        if o.jv_object_add != "mesh":
                            layout.operator("mesh.jv_siding_convert", icon="FILE_REFRESH")
                            layout.operator("mesh.jv_siding_add", icon="UV_ISLANDSEL")
                        else:
                            layout.label("This Is A JARCH Vis Mesh Object", icon="INFO")
                else:
                    layout.label("Only Mesh Objects Can Be Used", icon="ERROR")
            else:
                layout.operator("mesh.jv_siding_add", icon="UV_ISLANDSEL")


class SidingAdd(bpy.types.Operator):
    bl_idname = "mesh.jv_siding_add"
    bl_label = "Add Siding"
    bl_description = "JARCH Vis: Siding Generator"

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        o = bpy.context.scene.objects.active
        o.jv_internal_type = "siding"
        o.jv_object_add = "add"
        return {"FINISHED"}


class SidingConvert(bpy.types.Operator):
    bl_idname = "mesh.jv_siding_convert"
    bl_label = "Convert To Siding"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        o = context.object
        o.jv_internal_type = "siding"
        o.jv_object_add = "convert"
        return {"FINISHED"}


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
