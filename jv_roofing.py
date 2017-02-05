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

import bpy
from mathutils import Vector, Euler
from math import atan, degrees, cos, tan, sin, radians
from . jv_utils import point_rotation, object_dimensions, round_tuple, METRIC_INCH, HI, I, rot_from_normal, \
    unwrap_object, random_uvs
from . jv_materials import glossy_diffuse_material, image_material
from random import uniform
import bmesh
# import jv_properties
# from bpy.props import *

con = METRIC_INCH


def tin_normal(wh, ow, slope):
    cur_x = 0.0
    cur_y = -(wh / 2)
    faces, verts = [], []
    
    # calculate overall depth/oh
    oh = (wh / 2) / cos(atan((((wh / 2) * slope) / 12) / (wh / 2)))
    
    # set up small variables
    eti, nti = 0.8 / con,  0.9 / con
    fei = (5 / 8) / con
    nfei = 0.6875 / con
    otqi = 1.75 / con
    ofei = I+fei
    ohi = I+HI
    qi, ei, osi = HI / 2, HI / 4, HI / 8
    
    while cur_x < ow:
        p = len(verts)
        v2 = []
        a_e = False  # verts holder 2, at_edge for putting in last set of verts

        for i in range(4):
            z = 0.0 if i else osi
            
            v2 += [(cur_x, cur_y, z), (cur_x, cur_y+oh, z), (cur_x+HI, cur_y, eti+z), (cur_x+HI, cur_y+oh, eti+z),
                   (cur_x+fei, cur_y, nti+z), (cur_x+fei, cur_y+oh, nti+z), (cur_x+nfei, cur_y, I+z),
                   (cur_x+nfei, cur_y+oh, I+z)]
            cur_x += otqi
            v2 += [(cur_x-nfei, cur_y, I+z), (cur_x-nfei, cur_y+oh, I+z), (cur_x-fei, cur_y, nti+z),
                   (cur_x-fei, cur_y+oh, nti+z)]  # Right Mid Rib
            v2 += [(cur_x-HI, cur_y, eti+z), (cur_x-HI, cur_y+oh, eti+z), (cur_x, cur_y, z), (cur_x, cur_y+oh, z)]
            cur_x += ofei
            
            for i2 in range(2):
                v2 += [(cur_x, cur_y, 0.0), (cur_x, cur_y+oh, 0.0), (cur_x+qi, cur_y, ei), (cur_x+qi, cur_y+oh, ei)]
                cur_x += I
                v2 += [(cur_x, cur_y, ei), (cur_x, cur_y+oh, ei), (cur_x+qi, cur_y, 0.0), (cur_x+qi, cur_y+oh, 0.0)]
                cur_x += ohi+qi

            cur_x += ei
            
        v2 += [(cur_x, cur_y, 0.0), (cur_x, cur_y+oh, 0.0), (cur_x+HI, cur_y, eti), (cur_x+HI, cur_y+oh, eti),
               (cur_x+fei, cur_y, nti), (cur_x+fei, cur_y+oh, nti)]  # Left Top Of Rib
        v2 += [(cur_x+nfei, cur_y, I), (cur_x+nfei, cur_y+oh, I)]
        cur_x += otqi
        v2 += [(cur_x-nfei, cur_y, I), (cur_x-nfei, cur_y+oh, I), (cur_x-fei, cur_y, nti), (cur_x-fei, cur_y+oh, nti)]
        v2 += [(cur_x-HI, cur_y, eti), (cur_x-HI, cur_y+oh, eti), (cur_x, cur_y, 0.0), (cur_x, cur_y+oh, 0.0)]
        cur_x -= otqi

        vts = []
        if cur_x+otqi > ow:  # chop off extra
            for i in range(len(v2)):
                if v2[i][0] <= ow:
                    vts.append(v2[i])
                elif v2[i][0] > ow and not a_e:
                    a_e = True
                    b_o = v2[i-1]
                    f_o = v2[i]
                    dif_x = f_o[0]-b_o[0]
                    dif_z = f_o[2]-b_o[2]
                    r_r = dif_z / dif_x
                    b = b_o[2]-(r_r * b_o[0])
                    z2 = (ow * r_r)+b
                    vts += [(ow, cur_y, z2), (ow, cur_y, z2)]

            f_t = int((len(vts) / 2)-1)
        else: 
            vts = v2
            f_t = 71
                               
        for i in vts:
            verts.append(i)
        for i in range(f_t):
            faces.append((p, p+2, p+3, p+1))
            p += 2
    
    # apply rotation
    rot = atan(slope / 12)
    
    for num in range(1, len(verts), 2):
        point = point_rotation((verts[num][1], verts[num][2]), (cur_y, verts[num][2]), rot)
        verts[num] = [verts[num][0], point[0], point[1]]
                     
    return verts, faces


def tin_angular(wh, ow, slope):
    cur_x, cur_y, cur_z = 0.0, -(wh / 2), 0.0
    verts, faces = [], []

    # variables
    osi = (1 / 16) / con
    oqi = (5 / 4) / con
    ohi = (3 / 2) / con
    ti = ohi+HI
    qi = (1 / 4) / con
    ei = (1 / 8) / con

    # calculate overall depth/oh
    oh = (wh / 2) / cos(atan((((wh / 2) * slope) / 12) / (wh / 2)))
    
    # main loop
    while cur_x < ow:
        p = len(verts)

        v2 = []
        a_e = False
        for i in range(3):
            z = 0.0 if i else -osi

            v2 += [(cur_x, cur_y, z), (cur_x, cur_y+oh, z), (cur_x+HI, cur_y, oqi+z), (cur_x+HI, cur_y+oh, oqi+z),
                   (cur_x+ohi, cur_y, oqi+z), (cur_x+ohi, cur_y+oh, oqi+z), (cur_x+ti, cur_y, z),
                   (cur_x+ti, cur_y+oh, z)]
            cur_x += 2 * ti

            for i2 in range(2):
                v2 += [(cur_x, cur_y, 0.0), (cur_x, cur_y+oh, z), (cur_x+qi, cur_y, ei), (cur_x+qi, cur_y+oh, ei),
                       (cur_x+ohi, cur_y, ei), (cur_x+ohi, cur_y+oh, ei)]
                cur_x += ohi
                v2 += [(cur_x+qi, cur_y, 0.0), (cur_x+qi, cur_y+oh, 0.0)]
                cur_x += qi+ti+HI

            cur_x -= HI

        v2 += [(cur_x, cur_y, 0.0), (cur_x, cur_y+oh, 0.0), (cur_x+HI, cur_y, oqi), (cur_x+HI, cur_y+oh, oqi),
               (cur_x+ohi, cur_y, oqi), (cur_x+ohi, cur_y+oh, oqi), (cur_x+ti, cur_y, 0.0), (cur_x+ti, cur_y+oh, 0.0)]

        vts = []
        if cur_x+ti > ow:  # cut off extra
            for i in range(len(v2)):
                if v2[i][0] <= ow:
                    vts.append(v2[i])
                elif v2[i][0] > ow and not a_e:
                    a_e = True
                    b_o = v2[i-1]
                    f_o = v2[i]
                    dif_x = f_o[0]-b_o[0]
                    dif_z = f_o[2]-b_o[2]
                    r_r = dif_z / dif_x
                    b = b_o[2]-(r_r * b_o[0])
                    z2 = (ow * r_r)+b

                    vts += [(ow, cur_y, z2), (ow, cur_y+oh, z2)]

            f_t = int((len(vts) / 2)-1)
        else:
            vts = v2
            f_t = 38
                            
        for i in vts:
            verts.append(i)
        # faces
        for i in range(f_t):
            faces.append((p, p+2, p+3, p+1))
            p += 2
            
    # adjust points for slope
    rot = atan(slope / 12)
    
    for num in range(1, len(verts), 2):
        point = point_rotation((verts[num][1], verts[num][2]), (cur_y, verts[num][2]), rot)
        verts[num] = [verts[num][0], point[0], point[1]]
        
    return verts, faces


def tin_standing_seam(wh, ow, slope):
    verts, faces = [], []
    cur_x, cur_y, cur_z = 0.0, -(wh / 2), 0.0
    
    # variables
    qi = 0.25 / con
    fei = 0.625 / con
    otei = 1.375 / con
    osi = 0.0625 / con
    ei = 0.125 / con
    si = 16 / con
    
    # calculate overall height
    oh = (wh / 2) / cos(atan((((wh / 2) * slope) / 12) / (wh / 2)))
    
    while cur_x < ow:
        p = len(verts)
        v2 = []
        a_e = False
        # left side
        v2 += [(cur_x+qi, cur_y, cur_z+otei), (cur_x+qi, cur_y+oh, cur_z+otei), (cur_x+qi, cur_y, cur_z+qi),
               (cur_x+qi, cur_y+oh, cur_z+qi), (cur_x+ei, cur_y, cur_z+qi), (cur_x+ei, cur_y+oh, cur_z+qi),
               (cur_x+ei, cur_y, cur_z+HI), (cur_x+ei, cur_y+oh, cur_z+HI), (cur_x, cur_y, cur_z+HI),
               (cur_x, cur_y+oh, cur_z+HI), (cur_x, cur_y, cur_z), (cur_x, cur_y+oh, cur_z)]
        # right side
        cur_x += si
        v2 += [(cur_x, cur_y, cur_z), (cur_x, cur_y+oh, cur_z), (cur_x+qi, cur_y, cur_z+otei),
               (cur_x+qi, cur_y+oh, cur_z+otei), (cur_x+qi+ei, cur_y, cur_z+otei), (cur_x+qi+ei, cur_y+oh, cur_z+otei),
               (cur_x+fei, cur_y, cur_z+osi), (cur_x+fei, cur_y+oh, cur_z+osi)]
        cur_x += ei

        # cut-off extra
        if cur_x+HI > ow:
            for i in range(len(v2)):
                if v2[i][0] <= ow:
                    vts.append(v2[i])
                elif v2[i][0] > ow and not a_e:
                    a_e = True
                    b_o = v2[i-1]
                    f_o = v2[i]
                    dif_x = f_o[0]-b_o[0]
                    dif_z = f_o[2]-b_o[2]
                    r_r = dif_z / dif_x
                    b = b_o[2]-(r_r * b_o[0])
                    z2 = (ow * r_r)+b

                    vts += [(ow, cur_y, z2), (ow, cur_y+oh, z2)]
            f_t = int((len(vts) / 2)-1)
        else:
            vts = v2
            f_t = 9
                            
        for i in vts:
            verts.append(i)
        # faces
        for i in range(f_t):
            faces.append((p, p+2, p+3, p+1))
            p += 2
            
    # adjust points for slope
    rot = atan(slope / 12)
    
    for num in range(1, len(verts), 2):
        point = point_rotation((verts[num][1], verts[num][2]), (cur_y, verts[num][2]), rot)
        verts[num] = (verts[num][0], point[0], point[1])
        
    return verts, faces


def shingles_3tab(wh, ow, slope):
    verts, faces = [], []
    cur_y, cur_z = -(wh / 2), 0.0
    
    # constants
    of = 12 / con
    fi = 5 / con
    tsi = 0.125 / con
    qi = 0.25 / con
    etqi = 11.75 / con
    
    # calculate overall height
    oh = (wh / 2) / cos(atan((((wh / 2) * slope) / 12) / (wh / 2)))
    end_y = cur_y+oh    
    
    offset = False
    row = 1

    # row to go under tabs at bottom
    verts += [(0, cur_y, -tsi), (0, cur_y, 0), (0, cur_y + fi, -tsi), (0, cur_y + fi, 0), (ow, cur_y, -tsi),
              (ow, cur_y, 0), (ow, cur_y + fi, -tsi), (ow, cur_y + fi, 0)]
    faces += [(0, 1, 3, 2), (0, 4, 5, 1), (1, 5, 7, 3), (2, 3, 7, 6), (4, 6, 7, 5)]

    # main loop for growing on width
    while cur_y < end_y:        
        last_row_stay = True
        cur_x = 0.0
        bj = of  # big jump
        sj = fi  # small jump
        p = len(verts)
        
        # determine if shingle needs to be cut down on y axis
        if cur_y+fi < end_y < cur_y+of:
            bj = end_y-cur_y
        # if last row doesn't stay figure out how much to cut down second row
        elif cur_y+of > end_y and cur_y+fi > end_y:
            sj = end_y-cur_y
            last_row_stay = False

        # determine shingle height at front, middle, and back based on which row it is
        if row == 1:
            h1, h2, h3 = 0, 0, 0  # height 1, 2, and 3
        elif row == 2:
            h1, h2, h3 = tsi, tsi, 0
        else:
            h1, h2, h3 = 2 * tsi, tsi, 0

        # first vertices
        verts += [[cur_x, cur_y, h1], [cur_x, cur_y, h1 + tsi], [cur_x, cur_y + sj, h2],
                  [cur_x, cur_y + sj, h2 + tsi]]
        if last_row_stay:
            verts += [[cur_x, cur_y + bj, h3], [cur_x, cur_y + bj, h3 + tsi]]

        # loop for growing length
        width = qi
        sections_placed = 0
        cur_x += etqi / 2 if offset else etqi

        while cur_x < ow:
            last_p = len(verts)

            verts += [[cur_x, cur_y, h1], [cur_x, cur_y, h1 + tsi], [cur_x, cur_y + sj, h2],
                      [cur_x, cur_y + sj, h2 + tsi]]
            if last_row_stay:
                verts += [[cur_x, cur_y + bj, h3], [cur_x, cur_y + bj, h3 + tsi]]

            cur_x += width
            width = etqi if width == qi else qi
            sections_placed += 1

            for i in range(last_p, len(verts), 1):
                if verts[i][0] > ow:
                    verts[i][0] = ow

        verts += [[ow, cur_y, h1], [ow, cur_y, h1 + tsi], [ow, cur_y + sj, h2], [ow, cur_y + sj, h2 + tsi]]
        if last_row_stay:
            verts += [[ow, cur_y + bj, h3], [ow, cur_y + bj, h3 + tsi]]
        sections_placed += 1

        if last_row_stay:
            faces += [(p, p + 1, p + 3, p + 2), (p + 2, p + 3, p + 5, p + 4)]  # close in end

            for i in range(int(sections_placed / 2)):
                faces += [(p, p + 6, p + 7, p + 1), (p + 1, p + 7, p + 9, p + 3), (p + 3, p + 9, p + 11, p + 5),
                          (p + 4, p + 5, p + 11, p + 10), (p, p + 2, p + 8, p + 6), (p + 2, p + 4, p + 10, p + 8)]
                p += 6

                if i < sections_placed / 2 - 1 or sections_placed % 2 == 0:
                    faces += [(p, p + 2, p + 3, p + 1), (p + 2, p + 8, p + 9, p + 3), (p + 6, p + 7, p + 9, p + 8),
                              (p + 3, p + 9, p + 11, p + 5), (p + 4, p + 5, p + 11, p + 10),
                              (p + 2, p + 4, p + 10, p + 8)]
                    p += 6

            if sections_placed % 2 != 0:
                faces += [(p, p + 6, p + 7, p + 1), (p + 1, p + 7, p + 9, p + 3), (p + 3, p + 9, p + 11, p + 5),
                          (p + 4, p + 5, p + 11, p + 10), (p, p + 2, p + 8, p + 6), (p + 2, p + 4, p + 10, p + 8)]
                p += 6
                faces += [(p, p + 2, p + 3, p + 1), (p + 2, p + 4, p + 5, p + 3)]  # close end
            else:
                faces += [(p + 2, p + 4, p + 5, p + 3)]  # close end
        else:
            for i in range(int(sections_placed / 2)):
                faces += [(p, p + 1, p + 3, p + 2), (p, p + 4, p + 5, p + 1), (p + 1, p + 5, p + 7, p + 3),
                          (p + 2, p + 3, p + 7, p + 6), (p + 4, p + 6, p + 7, p + 5)]
                p += 8

            if sections_placed % 2 != 0:
                faces += [(p, p + 1, p + 3, p + 2), (p, p + 4, p + 5, p + 1), (p + 1, p + 5, p + 7, p + 3),
                          (p + 2, p + 3, p + 7, p + 6), (p + 4, p + 6, p + 7, p + 5)]
            
        cur_y += fi
        row += 1
        offset = not offset               
        
    # adjust vertex position to adjust for slope
    rot = atan(slope / 12)
    
    for num in range(len(verts)):
        point = point_rotation((verts[num][1], verts[num][2]), (-(wh / 2), verts[num][2]), rot)
        verts[num] = (verts[num][0], point[0], point[1])
        
    return verts, faces


def shingles_arch(wh, ow, slope):
    def raised_faces(f, j):
        f += [(j, j + 9, j + 10, j + 1), (j + 1, j + 10, j + 11, j + 2), (j + 1, j + 2, j + 5, j + 4),
              (j + 2, j + 11, j + 14, j + 5), (j + 5, j + 14, j + 17, j + 8), (j + 7, j + 8, j + 17, j + 16),
              (j + 6, j + 7, j + 16, j + 15), (j + 3, j + 6, j + 15, j + 12), (j, j + 3, j + 12, j + 9),
              (j + 10, j + 13, j + 14, j + 11)]

    def lower_faces(f, j, subtract):
        a = 1 if subtract else 0
        j -= 1 if subtract else 0

        f += [(j + a, j + 9, j + 10, j + 1 + a), (j + 1 + a, j + 10, j + 13, j + 4), (j + 4, j + 13, j + 14, j + 5),
              (j + 5, j + 14, j + 17, j + 8), (j + 7, j + 8, j + 17, j + 16), (j + 6, j + 7, j + 16, j + 15),
              (j + a, j + 3, j + 12, j + 9), (j + 3, j + 6, j + 15, j + 12)]

    def lower_faces_vert_removed(f, j):
        f += [(j, j + 9, j + 10, j + 1), (j + 1, j + 10, j + 12, j + 4), (j + 4, j + 12, j + 13, j + 5),
              (j + 5, j + 13, j + 16, j + 8), (j + 15, j + 7, j + 8, j + 16), (j + 14, j + 6, j + 7, j + 15),
              (j + 6, j + 14, j + 11, j + 3), (j + 3, j + 11, j + 9, j), (j + 9, j + 11, j + 12, j + 10),
              (j + 11, j + 14, j + 15, j + 12), (j + 12, j + 15, j + 16, j + 13)]

    verts, faces = [], []
    rot = atan(slope / 12)
    
    cur_y = -(wh / 2)
    
    # variables
    sfei = 6.625 / con
    lth = 0.1875 / con
    sw = 39.375 / con
    third_single = sw / 3
    ffei = 5.625 / con
    tth = lth / 2
    two = 2 / con
    
    oh = (wh / 2) / cos(atan((((wh / 2) * slope) / 12) / (wh / 2)))
    end_y = cur_y+oh

    last_row_stay = True
    row = 1
            
    while cur_y < end_y:
        cur_x = 0.0
        sj = ffei
        bj = sfei+ffei
        v = []
        p = len(verts)  # size before anything is added
        tabs_placed = 0

        if cur_y+ffei >= end_y:
            last_row_stay = False
            sj = end_y-cur_y  # small jump replaces ffei and is adjusted for if shingle is not full width

        if cur_y+ffei < end_y <= cur_y+ffei+sfei:
            bj = end_y-cur_y  # big jump replaces sfei if shingle is not full width, but row can still be placed

        if row == 1:
            h1, h2, h3 = 0, 0, 0  # height 1, 2, and 3
        elif row == 2:
            h1, h2, h3 = lth, lth, 0
        elif row >= 3:
            h1, h2, h3 = 2 * lth, lth, 0

        v += [(cur_x, cur_y, h1), (cur_x, cur_y, h1 + tth), (cur_x, cur_y + sj, h2),
              (cur_x, cur_y + sj, h2 + tth)]
        if last_row_stay:
            v += [(cur_x, cur_y + sj, h2 + lth), (cur_x, cur_y + bj, h3), (cur_x, cur_y + bj, h3 + tth),
                  (cur_x, cur_y + bj, h3 + lth)]

        clipped = False
        placed_right = True
        while cur_x < ow:
            cur_x += two
            tabs_placed += 1
            width = uniform(3 / con, 7 / con)  # width of tab
            start_p = len(v)

            # left side of tab
            v += [[cur_x, cur_y, h1], [cur_x, cur_y, h1+tth], [cur_x, cur_y, h1+lth],
                  [cur_x + HI, cur_y + sj, h2], [cur_x + HI, cur_y + sj, h2 + tth], [cur_x + HI, cur_y+sj, h2+lth]]
            if last_row_stay:
                v += [[cur_x + HI, cur_y + bj, h3], [cur_x + HI, cur_y + bj, h3 + tth], [cur_x + HI, cur_y+bj, h3+lth]]

            if cur_x + HI < ow:
                start_p = len(v)  # verts so far don't need to be clipped, so update start position for clipping
                # right side of tab, only do if previous set didn't go to far
                v += [[cur_x + width + I, cur_y, h1], [cur_x + width + I, cur_y, h1+tth],
                      [cur_x + width + I, cur_y, h1+lth], [cur_x + width + HI, cur_y + sj, h2],
                      [cur_x + width + HI, cur_y + sj, h2 + tth], [cur_x + width + HI, cur_y + sj, h2 + lth]]

                if last_row_stay:
                    v += [[cur_x + width + HI, cur_y + bj, h3], [cur_x + width + HI, cur_y + bj, h3 + tth],
                          [cur_x + width + HI, cur_y + bj, h3 + lth]]
            else:
                placed_right = False

            # shorten if needed
            if cur_x + width + I > ow or not placed_right:
                clipped = True
                for i in range(start_p, len(v), 1):
                    v[i][0] = ow

            if clipped and not placed_right and last_row_stay:  # remove vertex at corner because no face will use it
                del v[len(v) - 7]
            elif clipped and not placed_right and not last_row_stay:  # remove vertex when no last row
                del v[len(v) - 4]
                del v[len(v) - 1]

            cur_x += uniform(width, third_single)  # space between tabs

        if not clipped:  # manually put in end vertices
            v += [(ow, cur_y, h1), (ow, cur_y, h1 + tth), (ow, cur_y + sj, h2), (ow, cur_y + sj, h2 + tth)]
            if last_row_stay:
                v += [(ow, cur_y + sj, h2 + lth), (ow, cur_y + bj, h3), (ow, cur_y + bj, h3 + tth),
                      (ow, cur_y + bj, h3 + lth)]

        for i in v:
            verts.append(i)

        if last_row_stay:
            lower_faces(faces, p, True)
            faces += [(p, p + 1, p + 3, p + 2), (p + 2, p + 3, p + 6, p + 5), (p + 3, p + 4, p + 7, p + 6)]  # close end
            p += 8
            for tab in range(tabs_placed - 1):
                raised_faces(faces, p)
                p += 9
                if clipped and not placed_right and tab == tabs_placed - 2:  # bottom, right, top vertex removed
                    lower_faces_vert_removed(faces, p)
                else:
                    lower_faces(faces, p, False)
                p += 9

            if placed_right:  # go one step further if placed right
                raised_faces(faces, p)
                p += 9

            if clipped and placed_right:  # close end in
                faces += [(p, p + 3, p + 4, p + 1), (p + 3, p + 6, p + 7, p + 4), (p + 4, p + 7, p + 8, p + 5)]
            elif clipped and not placed_right:  # bottom, right, top vertex was removed
                faces += [(p, p + 2, p + 3, p + 1), (p + 2, p + 5, p + 6, p + 3), (p + 3, p + 6, p + 7, p + 4)]

            if not clipped:  # build faces for end that was manually put in
                lower_faces_vert_removed(faces, p)
        else:
            faces += [(p, p + 1, p + 3, p + 2), (p, p + 4, p + 5, p + 1), (p + 1, p + 5, p + 8, p + 3),
                      (p, p + 2, p + 7, p + 4), (p + 2, p + 3, p + 8, p + 7)]  # first lower and close end
            p += 4
            for tab in range(tabs_placed - 1):
                # raised
                faces += [(p, p + 6, p + 7, p + 1), (p + 1, p + 7, p + 8, p + 2), (p + 2, p + 8, p + 11, p + 5),
                          (p + 1, p + 2, p + 5, p + 4), (p + 7, p + 10, p + 11, p + 8),
                          (p + 3, p + 4, p + 10, p + 9), (p + 4, p + 5, p + 11, p + 10), (p, p + 3, p + 9, p + 6)]
                p += 6
                if clipped and not placed_right and tab == tabs_placed - 2:  # vertex removed
                    faces += [(p, p + 6, p + 7, p + 1), (p + 1, p + 7, p + 9, p + 4), (p + 3, p + 4, p + 9, p + 8),
                              (p, p + 3, p + 8, p + 6)]
                else:
                    faces += [(p, p + 6, p + 7, p + 1), (p + 1, p + 7, p + 10, p + 4), (p + 3, p + 4, p + 10, p + 9),
                              (p, p + 3, p + 9, p + 6)]  # lower
                p += 6

            if placed_right:
                faces += [(p, p + 6, p + 7, p + 1), (p + 1, p + 7, p + 8, p + 2), (p + 2, p + 8, p + 11, p + 5),
                          (p + 1, p + 2, p + 5, p + 4), (p + 7, p + 10, p + 11, p + 8),
                          (p + 3, p + 4, p + 10, p + 9), (p + 4, p + 5, p + 11, p + 10), (p, p + 3, p + 9, p + 6)]
                p += 6

            if clipped and placed_right:  # close end in
                faces += [(p, p + 3, p + 4, p + 1)]
            elif clipped and not placed_right:  # close end in
                faces += [(p, p + 2, p + 3, p + 1)]

            if not clipped:
                faces += [(p, p + 6, p + 7, p + 1), (p + 1, p + 7, p + 9, p + 4), (p + 3, p + 4, p + 9, p + 8),
                          (p, p + 3, p + 8, p + 6), (p + 6, p + 8, p + 9, p + 7)]

        row += 1
        cur_y += ffei

    for num in range(len(verts)):
        point = point_rotation((verts[num][1], verts[num][2]), (-(wh / 2), verts[num][2]), rot)
        verts[num] = (verts[num][0], point[0], point[1])

    return verts, faces


def terra_cotta(wh, ow, slope, res, rad):
    verts, faces = [], []
    rot = atan(slope / 12)
    
    cur_y = -(wh / 2)
    
    # variables
    th = 0.5 / con
    st_h = 2 / con
    tile_l1 = 18 / con
    tail_h = 0.5 / con
    rot_dif = radians(180 / (res+1))
    
    oh = (wh / 2) / cos(atan((((wh / 2) * slope) / 12) / (wh / 2)))
    end_y = cur_y+oh
        
    # main loop for width
    while cur_y < end_y:
        cur_x = rad  # reset the distances moved length wise each time
        
        # check to see if tile is to long
        tile_l = end_y-cur_y if cur_y+tile_l1 > end_y else tile_l1
            
        while cur_x < ow:
            p = len(verts)
            cur_z = st_h
            next_x, next_z, cut_point = 0, 0, 0
                    
            # left circle
            for i in range(res+2, 0, -1):
                cur_rot = rot_dif * i  # calculate current rotation
                # first set for position
                x, z = point_rotation((cur_x-rad, cur_z), (cur_x, cur_z), cur_rot+radians(180))               
                
                if x <= ow:
                    xz = point_rotation([(cur_x-rad+th, cur_z), (cur_x-rad-th, cur_z), (cur_x-rad, cur_z)],
                                        (cur_x, cur_z), cur_rot+radians(180))

                    verts += [(x, cur_y, z + tail_h), (xz[0][0], cur_y + tile_l, xz[0][1]),
                              (xz[1][0], cur_y, xz[1][1] + tail_h), (xz[2][0], cur_y + tile_l, xz[2][1])]

                    next_x = x
                    next_z = z
                    cut_point += 1
                
            cur_x = next_x+rad
            cur_z = next_z
            
            # right circle
            for i in range(0, res+1, 1):
                cur_rot = rot_dif * (i+1)
                # first set for position
                x, z = point_rotation((cur_x-rad, cur_z), (cur_x, cur_z), cur_rot)
                
                if x <= ow:
                    xz = point_rotation([(cur_x-rad-th, cur_z), (cur_x-rad+th, cur_z), (cur_x-rad, cur_z)],
                                        (cur_x, cur_z), cur_rot)

                    verts += [(x, cur_y, z+tail_h), (xz[0][0], cur_y+tile_l, xz[0][1]),
                              (xz[1][0], cur_y, xz[1][1]+tail_h), (xz[2][0], cur_y+tile_l, xz[2][1])]
                    cut_point += 1

            faces += [(p, p+2, p+3, p+1)]
            for i in range(cut_point-1):
                faces += [(p+2, p+6, p+7, p+3), (p, p+1, p+5, p+4), (p, p+4, p+6, p+2), (p+1, p+3, p+7, p+5)]
                p += 4

            faces += [(p, p+1, p+3, p+2)]

            cur_x += rad * 1.25

        cur_y += tile_l1 * 0.75

    for num in range(len(verts)):
        point = point_rotation((verts[num][1], verts[num][2]), (-(wh / 2), verts[num][2]), rot)
        verts[num] = (verts[num][0], point[0], point[1])
        
    return verts, faces


def create_roofing(context, mode, mat, shingles, tin, length, width, slope, res, radius):
    verts, faces = [], []
    return_ob = ""

    # tin
    if mat == "1":
        if tin == "1":
            verts, faces = tin_normal(width, length, slope)
        elif tin == "2":
            verts, faces = tin_angular(width, length, slope)
        else:
            verts, faces = tin_standing_seam(width, length, slope)  

    # shingles
    elif mat == "2":
        if shingles == "1":
            verts, faces = shingles_arch(width, length, slope)
        elif shingles == "2":
            verts, faces = shingles_3tab(width, length, slope)
   
    # terra cotta
    else:
        verts, faces = terra_cotta(width, length, slope, res, radius)

    # decide whether to replace current objects mesh or create a new object
    if mode == "add":
        mesh = bpy.data.meshes.new("roofing")
        mesh.from_pydata(verts, [], faces)
        context.object.data = mesh
    
    elif mode == "convert":
        mesh = bpy.data.meshes.new("roofing")
        mesh.from_pydata(verts, [], faces)
        return_ob = bpy.data.objects.new("roofing", mesh)
        context.scene.objects.link(return_ob)
        
    return return_ob 


def update_roofing(self, context):
    m_ob = context.object
    dup_ob = None
    obs = []
    ft = True

    # get materials on object
    materials = []
    for i in m_ob.data.materials:
        materials.append(i.name)

    # deselect all objects
    sel = []
    for i in context.selected_objects:
        sel.append(i.name)
        i.select = False

    # create backup object for cutting to use subsequent times
    if m_ob.jv_main_name == "none" and m_ob.jv_object_add == "convert" and len(m_ob.jv_face_groups) >= 1:
        m_ob.select = True
            
        bpy.ops.object.duplicate()
        n_ob = context.object
        n_ob.name = m_ob.name + "_cutter"
        m_ob.jv_main_name = n_ob.name
        
        bpy.ops.object.move_to_layer(layers=[False if i < 19 else True for i in range(20)])
        context.scene.objects.active = m_ob
        m_ob.select = True
            
        use_ob = context.object
        roof_data = [use_ob.jv_object_add, use_ob.jv_roofing_types, use_ob.jv_shingle_types,
                     use_ob.jv_tin_roofing_types, use_ob.jv_terra_cotta_res, use_ob.jv_tile_radius]
        
    # if the object to use for cutting is already on the other layer
    elif m_ob.jv_main_name != "none":
        ft = False
        use_ob = bpy.data.objects[m_ob.jv_main_name]

        # move to last layer
        pre_layers = list(context.scene.layers)
        context.scene.layers = [False if i < 19 else True for i in range(20)]

        use_ob.select = True
        context.scene.objects.active = use_ob
        bpy.ops.object.duplicate()  # leave duplicate on last layer, move back original
        dup_ob = context.object
        context.scene.objects.active = use_ob
        use_ob.select = True
        dup_ob.select = False

        context.scene.layers = pre_layers
        
        # move cutter object to active layer
        al = context.scene.active_layer
        context.scene.layers = [False if i < 19 else True for i in range(20)]  # just last layer
        
        layer_list = [False] * 19
        layer_list.insert(al, True)
                                
        bpy.ops.object.move_to_layer(layers=layer_list)
        context.scene.layers = pre_layers
        
        roof_data = [m_ob.jv_object_add, m_ob.jv_roofing_types, m_ob.jv_shingle_types, m_ob.jv_tin_roofing_types,
                     m_ob.jv_terra_cotta_res, m_ob.jv_tile_radius]
    else:
        use_ob = context.object      
    
    if use_ob.jv_object_add == "convert" and len(use_ob.jv_face_groups) >= 1:                
        # deselect any object that is not the active object
        for ob in context.selected_objects:
            if ob.name != context.object.name:
                ob.select = False

        fg = []        
        # create groups of face centers for cutting use the data in ob.jv_face_groups
        for f_g in use_ob.jv_face_groups:
            temp_l = []
            for i in f_g.data.split(","):
                if int(i) < len(use_ob.data.polygons):
                    temp_l.append(round_tuple(tuple(use_ob.data.polygons[int(i)].center), 4))
                else:
                    self.report({"ERROR"}, "JARCH Vis: Cannot Find Face, Please Update Roof Face Groups")

            temp_m = [temp_l, f_g.face_slope, f_g.rot]
            fg.append(temp_m)           
            
        # split object
        # deselect all faces and edges to make sure no extra geometry gets separated
        for f in use_ob.data.polygons:
            f.select = False
        for e in use_ob.data.edges:
            e.select = False
        for v in use_ob.data.vertices:
            v.select = False
             
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        
        # select faces and separate by selection
        # remove first object from list and apply it to the main object
        main_data = fg[0]
        del fg[0]                  
        
        for i in fg:            
            for i2 in i[0]:
                for face_in_obj in use_ob.data.polygons:
                    if round_tuple(tuple(face_in_obj.center), 4) == i2:                     
                        face_in_obj.select = True
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.separate(type="SELECTED")
            bpy.ops.object.editmode_toggle()            
            
            # set newly created plane objects jv_pl_z_rot and jv_pl_pitch for use when creating roofing for it
            temp_ob = bpy.context.selected_objects[0]
            temp_ob.jv_pl_pitch = i[1]
            temp_ob.jv_pl_z_rot = i[2]
            
        use_ob.jv_pl_pitch = main_data[1]
        use_ob.jv_pl_z_rot = main_data[2]
        
        # create list of objects and solidify current ones
        for ob in context.selected_objects:
            obs.append(ob.name)
            context.scene.objects.active = ob
            bpy.ops.object.modifier_add(type="SOLIDIFY")
            context.object.modifiers["Solidify"].thickness = 1
            context.object.modifiers["Solidify"].offset = 0.0
     
    roofing_names = []
    main_name = ""  
    # for each cutter object
    if use_ob.jv_object_add == "convert" and obs != []:
        for i in context.selected_objects:
            i.select = False
            
        # get rid of extra vertices in main object
        index_list = []
        for fa in use_ob.data.polygons:
            for vt in fa.vertices:
                if vt not in index_list:
                    index_list.append(vt)
        for vt in use_ob.data.polygons:
            if vt.index not in index_list:
                vt.select = True
        
        use_ob.select = True
        context.scene.objects.active = use_ob
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.delete(type="VERT")
        bpy.ops.object.editmode_toggle() 
        use_ob.select = False

        for o_name in obs:
            o = bpy.data.objects[o_name]
            
            # calculate size and then create siding and cut it
            # TODO: Figure out better way to determine plane dimensions
            xy_dim, z = object_dimensions(o)
            ang = atan(o.jv_pl_pitch / 12)
            z_dim = 2 * z / sin(ang)  # multiplied by two to correct for normally using half width
            
            # create roofing object
            new_ob = create_roofing(context, roof_data[0], roof_data[1], roof_data[2], roof_data[3], xy_dim * 1.1,
                                    z_dim * 1.1, o.jv_pl_pitch, roof_data[4], roof_data[5])
            
            # center o's origin point
            o.select = True
            context.scene.objects.active = o
            bpy.ops.object.origin_set(type="ORIGIN_CENTER_OF_MASS")
            
            o.select = False
            # set new object's location and rotation
            new_ob.select = True
            context.scene.objects.active = new_ob
            bpy.ops.object.origin_set(type="ORIGIN_CENTER_OF_MASS")
             
            new_ob.location = o.location
            eur = Euler((0.0, 0.0, o.jv_pl_z_rot), "XYZ")
            new_ob.rotation_euler = eur
            
            # solidify new object
            if roof_data[1] == "1":
                bpy.ops.object.modifier_add(type="SOLIDIFY")
                new_ob.modifiers["Solidify"].thickness = 0.001
                bpy.ops.object.modifier_apply(modifier="Solidify", apply_as="DATA")
            
            # boolean new object
            # fix normals
            bpy.ops.object.modifier_add(type="BOOLEAN")
            new_ob.modifiers["Boolean"].object = o
            bpy.ops.object.modifier_apply(modifier="Boolean", apply_as="DATA")
            
            # if current object is the main object set roofing objects name to main_name
            if o.name == use_ob.name:
                main_name = new_ob.name
            else:
                roofing_names.append(new_ob.name)          

        # deselect all objects
        for i in context.selected_objects:
            i.select = False
        # get rid of extra objects and join roofing objects
        for na in obs:
            if na != use_ob.name:
                temp_ob = bpy.data.objects[na]
                temp_ob.select = True
                context.scene.objects.active = temp_ob
                bpy.ops.object.delete()
                
        last_ob = bpy.data.objects[main_name]        
        use_ob.data = last_ob.data
        eur = Euler((0.0, 0.0, use_ob.jv_pl_z_rot), "XYZ")
        use_ob.rotation_euler = eur
        last_ob.select = True
        context.scene.objects.active = last_ob
        bpy.ops.object.delete()
        
        # join remaining roof objects to use_ob
        for na in roofing_names:
            bpy.data.objects[na].select = True
            
        use_ob.select = True
        context.scene.objects.active = use_ob
        bpy.ops.object.join()
        bpy.ops.object.modifier_remove(modifier="Solidify")
        
        # if this is not the first time creating object transfer mesh to main object
        if not ft:
            m_ob.data = use_ob.data       
            bpy.ops.object.delete()
            m_ob.select = True
            context.scene.objects.active = m_ob
            dup_ob.name = m_ob.name + "_cutter"
            
        # uvs and materials
        if m_ob.jv_is_unwrap:
            unwrap_object(self, context)
            if m_ob.jv_is_random_uv:
                random_uvs(self, context)
                
        for i in materials:
            mat = bpy.data.materials[i]
            m_ob.data.materials.append(mat)

        # remove random vertices that aren't apart of any faces, seem to come from boolean process
        bpy.ops.object.editmode_toggle()
        bm = bmesh.from_edit_mesh(context.object.data)
        to_remove = []
        for v in bm.verts:
            if len(v.link_faces) == 0:
                to_remove.append(v)
        for v in to_remove:
            bm.verts.remove(v)
        bmesh.update_edit_mesh(context.object.data)
        bpy.ops.object.editmode_toggle()
            
    # if object is added, create mesh
    if m_ob.jv_object_add == "add":
        for i in m_ob.data.materials:
            materials.append(i.name)
            
        # create new object
        create_roofing(context, m_ob.jv_object_add, m_ob.jv_roofing_types, m_ob.jv_shingle_types,
                       m_ob.jv_tin_roofing_types, m_ob.jv_over_length, m_ob.jv_over_width, m_ob.jv_slope,
                       m_ob.jv_terra_cotta_res, m_ob.jv_tile_radius)

        for i in materials:
            mat = bpy.data.materials[i]
            m_ob.data.materials.append(mat)

        if m_ob.jv_is_unwrap:
            unwrap_object(self, context)
            if m_ob.jv_is_random_uv:
                random_uvs(self, context)
        
        # create mirrored object
        if m_ob.jv_is_mirrored:
            bpy.ops.object.modifier_add(type="MIRROR")
            context.object.modifiers["Mirror"].use_x = False
            context.object.modifiers["Mirror"].use_y = True
            bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Mirror")

    # reselect objects
    for i in sel:
        bpy.data.objects[i].select = True


def roofing_materials(self):
    # create material
    o = bpy.context.object

    # check to make sure pictures have been picked
    if o.jv_col_image == "" and o.jv_roofing_types in ("2", "3"): 
        self.report({"ERROR"}, "JARCH Vis: No Color Image Filepath")
        return
    if o.jv_is_bump and o.jv_norm_image == "" and o.jv_roofing_types in ("2", "3"):
        self.report({"ERROR"}, "JARCH Vis: No Normal Image Filepath")
        return

    if o.jv_roofing_types == "1":
        mat = glossy_diffuse_material(bpy, o.jv_tin_color, (1.0, 1.0, 1.0), 0.18, 0.05, "roofing_use")
    else:
        mat = image_material(bpy, o.jv_im_scale, o.jv_col_image, o.jv_norm_image, o.jv_bump_amo, o.jv_is_bump,
                             "roofing_use", True, 0.1, 0.05, o.jv_is_rotate, None)

    if mat is not None:
        if len(o.data.materials) == 0:
            o.data.materials.append(mat.copy())
        else:
            o.data.materials[0] = mat.copy()
        o.data.materials[0].name = "roofing_"+o.name
    else:
        self.report({"ERROR"}, "JARCH Vis: Image(s) Not Found, Make Sure Path Is Correct")

    # remove extra materials
    for i in bpy.data.materials:
        if i.users == 0:
            bpy.data.materials.remove(i)


def collect_item_data(self, context, ignore):
    face_indices = []
    ob = context.object

    # toggle edit-mode to update which edges are selected
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()

    selected_faces = []
    # create list of selected edges
    for fa in ob.data.polygons:
        if fa.select:
            # make sure there are not duplicate faces, if there are, report error and exit
            for fg in ob.jv_face_groups:
                if str(fa.index) not in ignore and str(fa.index) in fg.data.split(","):
                    self.report({"ERROR"}, "JARCH Vis: Face Is Already In Another Group")
                    return None, None

            selected_faces.append(fa)
            face_indices.append(str(fa.index))

    return selected_faces, face_indices


def add_item(self, context):
    ob = context.object
    selected_faces, face_indices = collect_item_data(self, context, [])
                                
    if face_indices is not None and len(face_indices) > 0:  # make sure a face is selected
        item = ob.jv_face_groups.add()
        
        # set collection object item data
        item.data = ",".join(face_indices)
        item.num_faces = len(face_indices)
        
        # calculate slope and rotation
        rot = rot_from_normal(selected_faces[0].normal)
        item.face_slope = 12 * tan(rot[1])
        item.rot = rot[2] - radians(270)
        
        item.name = "Group " + str(ob.jv_face_group_ct + 1)
        
        ob.jv_face_group_index = len(ob.jv_face_groups) - 1
        ob.jv_face_group_ct = len(ob.jv_face_groups)
    elif face_indices is not None and len(face_indices) == 0:
        self.report({"ERROR"}, "JARCH Vis: At Least One Face Must Be Selected")


def update_item(self, context):
    ob = context.object

    if len(ob.jv_face_groups) > 0:
        fg = ob.jv_face_groups[ob.jv_face_group_index]
        selected_faces, face_indices = collect_item_data(self, context, fg.data.split(","))

        if len(face_indices) > 0:
            # set collection object item data
            fg.data = ",".join(face_indices)
            fg.num_faces = len(face_indices)

            # get slope and rot
            rot = rot_from_normal(selected_faces[0].normal)
            fg.face_slope = 12 * tan(rot[1])
            fg.rot = rot[2] - radians(270)
        else:
            self.report({"ERROR"}, "JARCH Vis: At Least One Face Must Be Selected")


def update_all_items(self, context):
    ob = context.object
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()

    for fg in ob.jv_face_groups:
        fa = ob.data.polygons[int(fg.data.split(",")[0])]
        rot = rot_from_normal(fa.normal)
        fg.face_slope = 12 * tan(rot[1])
        fg.rot = rot[2] - radians(270)


class RoofingPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_jv_roofing"
    bl_label = "JARCH Vis: Roofing"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "JARCH Vis"
    
    def draw(self, context):
        layout = self.layout
        ob = context.object
        
        # if in edit mode layout UIlist
        if ob is not None:
            if ob.jv_internal_type in ("roofing", "") and ob.type == "MESH":
                if context.mode == "EDIT_MESH" and ob.jv_object_add == "none":                
                    layout.template_list("OBJECT_UL_jv_face_groups", "", ob, "jv_face_groups", ob,
                                         "jv_face_group_index")
                    layout.separator()
                    row = layout.row()
                    row.operator("mesh.jv_add_face_group_item", icon="ZOOMIN")
                    row.operator("mesh.jv_remove_face_group_item", icon="ZOOMOUT")
                    row = layout.row()
                    row.operator("mesh.jv_update_face_group_item", icon="FILE_REFRESH")
                    row.operator("mesh.jv_update_face_group_items", icon="FILE_REFRESH")

                    # let user know if all faces are in a group
                    ct = 0
                    for fg in ob.jv_face_groups:
                        ct += fg.num_faces
                    if ct == len(ob.data.polygons):
                        layout.label("Every Face Is In A Group", icon="INFO")

                elif context.mode == "EDIT_MESH" and ob.jv_object_add != "none":
                    layout.label("This Object Is Already A JARCH Vis: Roofing Object", icon="INFO")
                    
                # if in object mode and there are face groups
                if (context.mode == "OBJECT" and len(ob.jv_face_groups) >= 1 and ob.jv_object_add == "convert") or \
                        ob.jv_object_add == "add":

                    if True:  # ob.jv_object_add != "convert":
                        layout.prop(ob, "jv_roofing_types", icon="MATERIAL")
                    else:
                        layout.label("Material: Tin", icon="MATERIAL")
                    
                    if ob.jv_roofing_types == "1":
                        layout.prop(ob, "jv_tin_roofing_types")
                    elif ob.jv_roofing_types == "2":
                        layout.prop(ob, "jv_shingle_types")               
                        
                    layout.separator()
                    if ob.jv_object_add != "convert":
                        layout.prop(ob, "jv_over_length")
                        layout.prop(ob, "jv_over_width")
                        layout.prop(ob, "jv_slope")
                        layout.separator()
                        layout.prop(ob, "jv_is_mirrored", icon="MOD_MIRROR")
                        
                    layout.separator()
                    if ob.jv_roofing_types == "3":
                        layout.prop(ob, "jv_tile_radius")
                        layout.prop(ob, "jv_terra_cotta_res")
                        layout.separator()
                    
                    # uv stuff
                    layout.prop(ob, "jv_is_unwrap", icon="GROUP_UVS")
                    layout.prop(ob, "jv_is_random_uv", icon="RNDCURVE")
                                        
                    # materials
                    layout.separator()               
                    if context.scene.render.engine == "CYCLES": 
                        layout.prop(ob, "jv_is_material", icon="MATERIAL")
                    else: 
                        layout.label("Materials Only Supported With Cycles", icon="POTATO")
                        
                    if ob.jv_is_material and context.scene.render.engine == "CYCLES":
                        layout.separator()
                        if ob.jv_roofing_types == "1":  # tin
                            layout.prop(ob, "jv_tin_color")
                        elif ob.jv_roofing_types in ("2", "3"):  # shingles and terra cotta
                            layout.prop(ob, "jv_col_image", icon="COLOR")
                            layout.prop(ob, "jv_is_bump", icon="SMOOTHCURVE")
                            
                            if ob.jv_is_bump:
                                layout.prop(ob, "jv_norm_image", icon="TEXTURE")
                                layout.prop(ob, "jv_bump_amo")
                            
                            layout.prop(ob, "jv_im_scale")
                            layout.prop(ob, "jv_is_rotate", icon="MAN_ROT")
                            
                        layout.separator()
                        layout.operator("mesh.jv_roofing_materials", icon="MATERIAL")
                        layout.prop(ob, "jv_is_preview", icon="SCENE")
                                                
                    # operators
                    layout.separator()
                    layout.operator("mesh.jv_roofing_update", icon="FILE_REFRESH")
                    layout.operator("mesh.jv_roofing_delete", icon="CANCEL")
                    layout.operator("mesh.jv_roofing_add", icon="LINCURVE")
                elif ob.jv_object_add == "none" and context.mode == "OBJECT" and len(ob.jv_face_groups) == 0:
                    layout.label("Enter Edit Mode And Create Face Groups", icon="ERROR")
                    layout.operator("mesh.jv_roofing_add", icon="LINCURVE")
                elif ob.jv_object_add == "none" and context.mode == "OBJECT" and len(ob.jv_face_groups) >= 1:                
                    layout.operator("mesh.jv_roofing_convert", icon="FILE_REFRESH")
                    layout.operator("mesh.jv_roofing_add", icon="LINCURVE")
            else:
                if ob.type != "MESH":
                    layout.label("Only Mesh Objects Can Be Used", icon="ERROR")
                else:
                    layout.label("This Is Already A JARCH Vis Object", icon="INFO")
                layout.operator("mesh.jv_roofing_add", icon="LINCURVE")
        else:
            layout.operator("mesh.jv_roofing_add", icon="LINCURVE")


class OBJECT_UL_jv_face_groups(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):         
        row = layout.row(align=True)
        row.prop(item, "name", text="", emboss=False, translate=False, icon="FACESEL")
        row.label("Faces: "+str(item.num_faces))
        row.label("Pitch: "+str(round(item.face_slope, 3)))
        row.label("Rot: "+str(round(degrees(item.rot), 1)))               


class RoofingUpdate(bpy.types.Operator):
    bl_idname = "mesh.jv_roofing_update"
    bl_label = "Update Roofing"
    bl_description = "Update Roofing"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        update_roofing(self, context)
        return {"FINISHED"}


class RoofingDelete(bpy.types.Operator):
    bl_idname = "mesh.jv_roofing_delete"
    bl_label = "Delete Roofing"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        o = context.object
        # deselect any selected objects
        for i in context.selected_objects:
            i.select = False
        
        if o.jv_object_add == "add":
            o.select = True
            bpy.ops.object.delete()
        
        elif o.jv_object_add == "convert":
            second_obj = bpy.data.objects[o.jv_main_name]
            
            if second_obj is not None:
                o.select = False
                second_obj.select = True
                context.scene.objects.active = second_obj

                # move to last layer, move that object back, then move back
                first_layers = [i for i in bpy.context.scene.layers]
                move_layers = [False] * 19
                move_layers.append(True)
                
                bpy.context.scene.layers = move_layers                        
                bpy.ops.object.move_to_layer(layers=first_layers)
                bpy.context.scene.layers = first_layers
                
                second_obj.jv_object_add = "none"
                second_obj.jv_internal_type = ""
                # remove "_cutter" from name
                if second_obj.name[len(second_obj.name)-7:len(second_obj.name)] == "_cutter":
                    second_obj.name = second_obj.name[0:len(second_obj.name)-7]
                second_obj.select = False                
                
                o.select = True
                context.scene.objects.active = o
                bpy.ops.object.delete()                                
            
        return {"FINISHED"}


class RoofingMaterials(bpy.types.Operator):
    bl_idname = "mesh.jv_roofing_materials"
    bl_label = "Generate\\Update Materials"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        roofing_materials(self)
        return {"FINISHED"}


class RoofingAdd(bpy.types.Operator):
    bl_idname = "mesh.jv_roofing_add"
    bl_label = "Add Roofing"
    bl_description = "JARCH Vis: Roofing Generator"
    
    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        o = bpy.context.scene.objects.active
        o.jv_internal_type = "roofing"
        o.jv_object_add = "add"
        return {"FINISHED"}


class RoofingConvert(bpy.types.Operator):
    bl_idname = "mesh.jv_roofing_convert"
    bl_label = "Convert To Roofing"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        o = context.object
        o.jv_internal_type = "roofing"
        o.jv_object_add = "convert"
        return {"FINISHED"}    


class FGAddItem(bpy.types.Operator):
    bl_idname = "mesh.jv_add_face_group_item"
    bl_label = "Add"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        add_item(self, context)
        return {"FINISHED"}


class FGRemoveItem(bpy.types.Operator):
    bl_idname = "mesh.jv_remove_face_group_item"
    bl_label = "Remove"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        ob = context.object
        if len(ob.jv_face_groups) > 0:
            ob.jv_face_groups.remove(ob.jv_face_group_index)
            ob.jv_face_group_ct = len(ob.jv_face_groups)

            # update names
            for i in range(ob.jv_face_group_index, len(ob.jv_face_groups), 1):
                ob.jv_face_groups[i].name = "Group " + str(i + 1)
           
            if len(ob.jv_face_groups) == 0 or ob.jv_face_group_index <= 0:
                ob.jv_face_group_index = 0
            else:
                ob.jv_face_group_index -= 1
        return {"FINISHED"}


class FGUpdateItem(bpy.types.Operator):
    bl_idname = "mesh.jv_update_face_group_item"
    bl_label = "Update"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        update_item(self, context)
        return {"FINISHED"}


class FGUpdateAllItems(bpy.types.Operator):
    bl_idname = "mesh.jv_update_face_group_items"
    bl_label = "Update All"
    bl_options = {"UNDO", "INTERNAL"}

    def execute(self, context):
        update_all_items(self, context)
        return {"FINISHED"}


# class FaceGroup(bpy.types.PropertyGroup):
#     data = StringProperty()
#     num_faces = IntProperty()
#     face_slope = FloatProperty()
#     rot = FloatProperty(unit="ROTATION")
#
#
# def register():
#     wm = bpy.context.window_manager
#     km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type="VIEW_3D")
#     km.keymap_items.new("mesh.jv_add_face_group_item", "A", "PRESS", ctrl=True)
#     bpy.utils.register_module(__name__)
#     bpy.types.Object.jv_face_groups = CollectionProperty(type=FaceGroup)
#
#
# def unregister():
#     bpy.utils.unregister_module(__name__)
#     del bpy.types.Object.jv_face_groups
#     wm = bpy.context.window_manager
#     if wm.keyconfigs.addon:
#         for kmi in wm.keyconfigs.addon.keymaps['3D View'].keymap_items:
#             if kmi.idname == "mesh.jv_add_face_group_item":
#                 wm.keyconfig.addon.keymaps['3D View'].keymap_items.remove(kmi)
#
# if __name__ == "__main__":
#     register()
