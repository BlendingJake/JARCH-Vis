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
from math import radians, sqrt, acos, cos, sin, asin
from . jv_utils import METRIC_INCH, I, HI, point_rotation, random_uvs, unwrap_object
from . jv_materials import glossy_diffuse_material, image_material, architectural_glass_material
from mathutils import Vector, Matrix
# import jv_properties

# variables for pane size
t = 1.5 / METRIC_INCH
bevelY = HI
bevelXZ = 0.25 / METRIC_INCH
ei = 0.125 / METRIC_INCH
y = -t / 2


# an iterator that returns x,y coordinates for ellipse based on resolution
def arch_function(half_width, half_height, res):
    step = (2*half_width) / res
    for i in range(res - 1):
        x = step * i - half_width + step
        y = (half_height/half_width) * sqrt((half_width**2) - (x**2))
        
        yield (x, y)


# roundness refers to what percentage of height that arch is
def arch(width, height, roundness, res, is_slider, jamb_w):
    verts, faces, glass_indices = [], [], []

    arch_h = height * (1 / (100 / roundness))
    arch_h2 = arch_h + I
    h = height - arch_h  # height to bottom of arch
    hw = width / 2
    hw2 = width / 2 + I
    w = jamb_w / 2
    y = -t / 2

    # jamb base
    verts += [(-hw - I, -w, 0.0), (hw + I, -w, 0.0), (hw + I, w, 0.0), (-hw - I, w, 0.0), (-hw, -w, I), (hw, -w, I),
              (hw, w, I), (-hw, w, I), (-hw - I, -w, h + I), (-hw, -w, h + I), (-hw, w, h + I), (-hw - I, w, h + I),
              (hw, -w, h + I), (hw + I, -w, h + I), (hw + I, w, h + I), (hw, w, h + I)]

    faces += [(0, 3, 2, 1), (0, 1, 5, 4), (2, 3, 7, 6), (4, 5, 6, 7), (0, 4, 9, 8), (0, 8, 11, 3), (3, 11, 10, 7),
              (4, 7, 10, 9), (1, 2, 14, 13), (1, 13, 12, 5), (5, 12, 15, 6), (2, 6, 15, 14)]

    p = len(verts)
    p2 = len(verts)

    # jamb arch
    for i in arch_function(hw, arch_h, res):
        verts += [(i[0], -w, i[1] + h + I), (i[0], w, i[1] + h + I)]

    off = len(verts) - p
    for i in arch_function(hw2, arch_h2, res):
        verts += [(i[0], -w, i[1] + h + I), (i[0], w, i[1] + h + I)]

    # jamb faces
    for i in range(res - 2):  # arch faces
        faces += [(p, p + 1, p + 3, p + 2), (p, p + 2, p + off + 2, p + off),
                  (p + off, p + off + 2, p + off + 3, p + off + 1), (p + 1, p + off + 1, p + off + 3, p + 3)]
        p += 2

    # connecting faces
    faces += [(p2 - 8, p2 - 7, p2, p2 + off), (p2 - 7, p2 - 6, p2 + 1, p2), (p2 - 6, p2 - 5, p2 + off + 1, p2 + 1),
              (p2 - 8, p2 + off, p2 + off + 1, p2 - 5), (p2 - 4, p2 - 3, p + off, p),
              (p2 - 3, p2 - 2, p + off + 1, p + off),
              (p2 - 2, p2 - 1, p + 1, p + off + 1), (p2 - 1, p2 - 4, p, p + 1)]  # right side

    # if slide add extra pane
    sz, ph = I, h
    if is_slider:
        create_rectangle_pane(verts, faces, glass_indices, width, (h + I) / 2, 0.0, 0.0, I + (h + I) / 4,
                              [0.0, 0.0, 0.0, 0.0])
        sz = (h + I) / 2
        ph = h - (h - I) / 2
        y = 0.0

    p = len(verts)
    # border bottom
    verts += [(-hw, y, sz), (hw, y, sz), (hw, y + t, sz), (-hw, y + t, sz), (-hw + I, y, sz + I),
              (hw - I, y, sz + I),
              (hw - I, y + t, sz + I), (-hw + I, y + t, sz + I), (-hw + I + bevelXZ, y + bevelY, sz + I + bevelXZ),
              (hw - I - bevelXZ, y + bevelY, sz + I + bevelXZ), (hw - I, y + t - ei, sz + I),
              (-hw + I, y + t - ei, sz + I)]

    # border middle
    sz += ph
    p3 = len(verts)
    verts += [(-hw, y, sz), (hw, y, sz), (hw, y + t, sz), (-hw, y + t, sz), (-hw + I, y, sz), (hw - I, y, sz),
              (hw - I, y + t, sz), (-hw + I, y + t, sz), (-hw + I + bevelXZ, y + bevelY, sz),
              (hw - I - bevelXZ, y + bevelY, sz), (hw - I, y + t - ei, sz), (-hw + I, y + t - ei, sz)]

    # border arch
    temp1 = []
    p2 = len(verts)
    for i in arch_function(hw, arch_h, res):
        temp1 += [(i[0], y, i[1] + h + I), (i[0], y + t, i[1] + h + I)]
    temp2 = []
    for i in arch_function(hw - I, arch_h - I, res):
        temp2 += [(i[0], y, i[1] + h + I), (i[0], y + t - ei, i[1] + h + I), (i[0], y + t, i[1] + h + I)]
    temp3 = []
    for i in arch_function(hw - I - bevelXZ, arch_h - I - bevelXZ, res):
        temp3 += [(i[0], y + bevelY, i[1] + h + I)]

    # bottom and side faces for border
    faces += [(p, p + 1, p + 5, p + 4), (p + 4, p + 5, p + 9, p + 8), (p, p + 3, p + 2, p + 1),
              (p + 2, p + 3, p + 7, p + 6),
              (p + 6, p + 7, p + 11, p + 10), (p, p + 4, p + 16, p + 12), (p + 4, p + 8, p + 20, p + 16),
              (p + 1, p + 13, p + 17, p + 5),
              (p + 5, p + 17, p + 21, p + 9), (p + 2, p + 6, p + 18, p + 14), (p + 6, p + 10, p + 22, p + 18),
              (p + 11, p + 7, p + 19, p + 23),
              (p + 7, p + 3, p + 15, p + 19), (p + 8, p + 9, p + 21, p + 20), (p + 10, p + 11, p + 23, p + 22)]

    # combine vert lists with correct indexs for easier indexing
    inner_face, outer_face = sort_window_verts(temp1, temp2, temp3, verts)
    p4 = len(verts)

    # faces for arch
    p = p2
    for i in range(res - 2):
        faces += [(p, p + 2, p + 8, p + 6), (p + 2, p + 3, p + 9, p + 8), (p + 4, p + 5, p + 11, p + 10),
                  (p + 1, p + 7, p + 11, p + 5),
                  (p, p + 1, p + 7, p + 6)]
        p += 6
    glass_indices += [len(faces), len(faces) + 1]
    faces.append(inner_face)
    faces.append(outer_face)

    # extra faces
    faces += [(p3, p3 + 4, p3 + 14, p3 + 12), (p3 + 4, p3 + 8, p3 + 15, p3 + 14),
              (p3 + 7, p3 + 3, p3 + 13, p3 + 17),
              (p3 + 11, p3 + 7, p3 + 17, p3 + 16), (p3, p3 + 3, p3 + 13, p3 + 12), (p3 + 1, p4 - 6, p4 - 4, p3 + 5),
              (p3 + 5, p4 - 4, p4 - 3, p3 + 9),
              (p3 + 6, p3 + 10, p4 - 2, p4 - 1), (p3 + 2, p3 + 6, p4 - 1, p4 - 5), (p3 + 1, p4 - 6, p4 - 5, p3 + 2),
              (p3 + 8, p3 + 9, p4 - 3, p3 + 15),
              (p3 + 10, p3 + 11, p3 + 16, p4 - 2)]

    return verts, faces, glass_indices


# bay windows
def bay(width, h, is_bay, bay_angle, segments, split_center, db_hung, jamb_w, depth):
    verts, faces, glass_indices = [], [], []
    segments = int(segments)
    hw, jw, h2 = width / 2, jamb_w / 2, h
    h -= 2 * I  # adjust for height of jamb

    if is_bay:  # bay
        side_pw, th2 = (depth - jamb_w) / sin(bay_angle), radians(90) - bay_angle
        x = hw - 0.5 * jamb_w * cos(th2) - side_pw * 0.5 * cos(bay_angle)
        y = 0.5 * jamb_w * sin(th2) + side_pw * sin(bay_angle) * 0.5

        for r in [bay_angle, -bay_angle]:
            p = len(verts)

            matrix = Matrix.Translation((x, y, 0)) * Matrix.Rotation(radians(180) - r, 4, "Z")
            create_rectangle_jamb(verts, faces, side_pw - 2 * I, h, jamb_w, True, 0)

            if db_hung:
                create_rectangle_pane(verts, faces, glass_indices, side_pw, (h + I) / 2, 0, 0.0, I + (h + I) / 4,
                                      [HI, 0.0, 0.0, 0.0])
                create_rectangle_pane(verts, faces, glass_indices, side_pw, (h + I) / 2, 0, (1.5 / METRIC_INCH),
                                      I + (h + I) / 4 + (h - I) / 2, [0.0, 0.0, 0.0, 0.0])
            else:
                create_rectangle_pane(verts, faces, glass_indices, side_pw, h, 0, 0.0, h / 2 + I, [HI, 0.0, 0.0, 0.0])

            # rotation and translation
            for v in range(p, len(verts), 1):
                verts[v] = (matrix * Vector(verts[v])).to_tuple()

            x *= -1  # flip for other side

        # center jambs and panes
        hpw = hw - jamb_w * cos(th2) - side_pw * cos(bay_angle)
        width_between_sides = 2 * hpw - 2 * I
        pw = width_between_sides / 2 - I if split_center else width_between_sides
        cx = -pw / 2 - I if split_center else 0

        for i in range(2 if split_center else 1):
            p = len(verts)
            create_rectangle_jamb(verts, faces, pw, h, jamb_w, True, 0)

            if db_hung:
                create_rectangle_pane(verts, faces, glass_indices, pw, (h + I) / 2, 0, 0.0, I + (h + I) / 4,
                                      [HI, 0.0, 0.0, 0.0])
                create_rectangle_pane(verts, faces, glass_indices, pw, (h + I) / 2, 0, (1.5 / METRIC_INCH),
                                      I + (h + I) / 4 + (h - I) / 2, [0.0, 0.0, 0.0, 0.0])
            else:
                create_rectangle_pane(verts, faces, glass_indices, pw, h, 0, 0.0, h / 2 + I, [HI, 0.0, 0.0, 0.0])

            matrix = Matrix.Translation((cx, depth - jw, 0)) * Matrix.Rotation(radians(180), 4, "Z")
            # rotation and translation
            for v in range(p, len(verts), 1):
                verts[v] = (matrix * Vector(verts[v])).to_tuple()

            cx += pw + 2 * I

        # filler strips
        points = [((hw - jamb_w * cos(th2), 0), (hw, 0), (hw, jamb_w * sin(th2))),
                  ((-hw + jamb_w * cos(th2), 0), (-hw, jamb_w * sin(th2)), (-hw, 0)),
                  ((hpw, depth - jamb_w), (hpw + jamb_w * cos(th2), depth - jamb_w + jamb_w * sin(th2)),
                   (hpw, depth)), ((-hpw, depth - jamb_w), (-hpw, depth),
                                   (-hpw - jamb_w * cos(th2), depth - jamb_w + jamb_w * sin(th2)),)]

        for pts in points:
            p = len(verts)
            for pt in pts:
                verts += [(pt[0], pt[1], 0), (pt[0], pt[1], h2)]
            faces += [(p, p + 2, p + 3, p + 1), (p + 2, p + 4, p + 5, p + 3), (p, p + 1, p + 5, p + 4),
                      (p + 1, p + 3, p + 5), (p, p + 4, p + 2)]
    else:  # bow
        ang = radians(180) / segments
        th2 = asin(jamb_w * sin(ang / 2) / hw)
        pw = 2 * hw * sin(ang / 2 - th2) - 2 * I
        r = hw * cos(ang / 2 - th2) - jamb_w / 2
        sx = jamb_w * cos(ang / 2)

        # first filler strip on far right
        pt = point_rotation((hw, 0), (0, 0), th2)
        adj_x = pt[0] - sx
        verts += [(pt[0] - sx, 0, 0), (pt[0] - sx, 0, h2), (pt[0], 0, 0), (pt[0], 0, h2), (pt[0], pt[1], 0),
                  (pt[0], pt[1], h2)]
        faces += [(0, 2, 3, 1), (2, 4, 5, 3), (0, 1, 5, 4), (1, 3, 5), (0, 4, 2)]

        for i in range(segments):
            p = len(verts)
            x, y = point_rotation((r, 0), (0, 0), ang * (i + 1) - ang / 2)
            matrix = Matrix.Translation((x, y, 0)) * Matrix.Rotation(radians(90) + ang * i + ang / 2, 4, "Z")
            create_rectangle_jamb(verts, faces, pw, h, jamb_w, True, 0)

            if db_hung:
                create_rectangle_pane(verts, faces, glass_indices, pw, (h + I) / 2, 0, 0.0, I + (h + I) / 4,
                                      [HI, 0.0, 0.0, 0.0])
                create_rectangle_pane(verts, faces, glass_indices, pw, (h + I) / 2, 0, (1.5 / METRIC_INCH),
                                      I + (h + I) / 4 + (h - I) / 2, [0.0, 0.0, 0.0, 0.0])
            else:
                create_rectangle_pane(verts, faces, glass_indices, pw, h, 0, 0.0, h / 2 + I, [HI, 0.0, 0.0, 0.0])

            # rotation and translation
            for v in range(p, len(verts), 1):
                verts[v] = (matrix * Vector(verts[v])).to_tuple()

            # filler strips between panes/jambs on outside
            p2 = len(verts)
            if i == segments - 1:  # last strip, adjust final point rotation
                pts = point_rotation(((adj_x, 0), (hw, 0), (adj_x + sx, 0)), (0, 0),
                                     (ang * (i + 1), ang * (i + 1) - th2, ang * (i + 1)))
            else:
                pts = point_rotation(((adj_x, 0), (hw, 0), (hw, 0)), (0, 0),
                                     (ang * (i + 1), ang * (i + 1) - th2, ang * (i + 1) + th2))
            for pt in pts:
                verts += [(pt[0], pt[1], 0), (pt[0], pt[1], h2)]
            faces += [(p2, p2 + 2, p2 + 3, p2 + 1), (p2 + 2, p2 + 4, p2 + 5, p2 + 3), (p2, p2 + 1, p2 + 5, p2 + 4),
                      (p2 + 1, p2 + 3, p2 + 5), (p2, p2 + 4, p2 + 2)]

    return verts, faces, glass_indices


# circulars
def circular(radius, angle, res, jamb_w, full):
    verts, faces, glass_indices = [], [], []
        
    if full:
        verts, faces, glass_indices = polygon(radius, res, jamb_w)
    else:        
        w = jamb_w / 2
        edge_ang = radians(90) - acos(I / radius)
        ang = (angle - 2*edge_ang) / res        
        
        # jamb
        verts += [(0, -w, 0), (0, w, 0)]
        x, z = point_rotation((radius, 0), (0, 0), angle)
        verts += [(x, -w, z), (x, w, z)]
            
        for i in range(res, -1, -1):
            x, z = point_rotation((radius, 0), (0, 0), i*ang + edge_ang)
            verts += [(x, -w, z), (x, w, z)]
            
        verts += [(radius, -w, 0), (radius, w, 0)]
        off = len(verts)
        edge_ang = radians(90) - acos(I / (radius - I))  # adjust angle for inch because of smaller radius
        ang = (angle - 2*edge_ang) / res

        rot_x, rot_z = point_rotation((I / sin(angle / 2), 0), (0, 0), angle / 2)
        verts += [(rot_x, -w, rot_z), (rot_x, w, rot_z)]
        x, z = point_rotation((radius - I, 0), (0, 0), angle - edge_ang)
        verts += [(x, -w, z), (x, w, z)]
        
        for i in range(res, -1, -1):
            x, z = point_rotation((radius - I, 0), (0, 0), i * ang + edge_ang)
            verts += [(x, -w, z), (x, w, z)]
        verts += [(x, -w, z), (x, w, z)]
            
        p = 0
        for i in range(res + 3):
            faces += [(p, p+off, p+off+2, p+2), (p, p+2, p+3, p+1), (p+off, p+off+1, p+off+3, p+off+2),
                      (p+1, p+3, p+off+3, p+off+1)]
            p += 2
            
        faces += [(p, p+off, off, 0), (p, p+1, 1, 0), (p+1, 1, off+1, p+off+1), (off, p+off, p+off+1, off+1)]
        p = len(verts)
        
        # window - code is complicated mainly due to having to properly place corners to make sure no faces overlap
        # that is why edge_ang is always being recalculated, to allow room for next tier of vertices                
        temp1 = [(rot_x, y, rot_z), (rot_x, y+t, rot_z)]  # intital vertices at pivot
        x, z = point_rotation((radius - I, 0), (0, 0), angle - edge_ang)
        temp1 += [(x, y, z), (x, y+t, z)]  # top corner
        
        edge_ang = radians(90) - acos(2 * I / (radius - 2 * I))  # adjust angle to make room for next tier of vertices
        ang = (angle - 2*edge_ang) / res  # get angle offset for new edge_ang
        for i in range(res, -1, -1):
            x, z = point_rotation((radius - I, 0), (0, 0), i * ang + edge_ang)
            temp1 += [(x, y, z), (x, y+t, z)]
        temp1 += [(radius - I, y, I), (radius - I, y + t, I)]
        
        rot_x, rot_z = point_rotation((2 * I / sin(angle / 2), 0), (0, 0), angle / 2)
        temp2 = [(rot_x, y, rot_z), (rot_x, y+t-ei, rot_z), (rot_x, y+t, rot_z)]
        x, z = point_rotation((radius - 2 * I, 0), (0, 0), angle - edge_ang)
        temp2 += [(x, y, z), (x, y+t-ei, z), (x, y+t, z)]
        
        temp_ang = edge_ang  # make copy to use later for placing last vertex
        edge_ang = radians(90) - acos((2 * I + bevelXZ) / (radius - 2 * I - bevelXZ))  # adjust angle for smaller radius
        ang = (angle - 2*edge_ang) / res
        for i in range(res, -1, -1):
            x, z = point_rotation((radius - 2 * I, 0), (0, 0), i * ang + edge_ang)
            temp2 += [(x, y, z), (x, y+t-ei, z), (x, y+t, z)]
        x, z = point_rotation((radius - 2 * I, 0), (0, 0), temp_ang)
        temp2 += [(x, y, z), (x, y+t-ei, z), (x, y+t, z)]
                
        rot_x, rot_z = point_rotation(((2 * I + bevelXZ) / sin(angle / 2), 0), (0, 0), angle / 2)
        temp3 = [(rot_x, y+bevelY, rot_z)]
        x, z = point_rotation((radius - 2 * I - bevelXZ, 0), (0, 0), angle - edge_ang)
        temp3 += [(x, y+bevelY, z)]
        
        x = 0.0  # retain x for use below
        for i in range(res, -1, -1):
            x, z = point_rotation((radius - 2 * I - bevelXZ, 0), (0, 0), i * ang + edge_ang)
            temp3 += [(x, y+bevelY, z)]
        temp3 += [(x, y + bevelY, 2 * I + bevelXZ)]
        
        inner_face, outer_face = sort_window_verts(temp1, temp2, temp3, verts)  # sort vertices lists
        glass_indices += [len(faces), len(faces) + 1]
        faces.append(inner_face)
        faces.append(outer_face)
        
        p2 = p
        for i in range(res+3):
            faces += [(p, p+2, p+8, p+6), (p+2, p+3, p+9, p+8), (p+4, p+5, p+11, p+10), (p+1, p+7, p+11, p+5),
                      (p, p+1, p+7, p+6)]
            p += 6
        faces += [(p, p+2, p2+2, p2), (p+2, p+3, p2+3, p2+2), (p2+1, p2+5, p+5, p+1), (p2+5, p2+4, p+4, p+5)]

    return verts, faces, glass_indices


# creates jamb, startX define the bottom center of the window
def create_rectangle_jamb(verts, faces, width, height, jamb, full_jamb, start_x):
    p = len(verts) 
    
    # jambs - inch border around outside
    cur_x = start_x - (width / 2) - I
    cur_y = -(jamb / 2)
    cur_z = 0.0    
    
    # counteract extra inch for jamb thickness on left side if not full_jamb
    ex = I if not full_jamb else 0
    
    verts += [(cur_x + ex, cur_y, cur_z), (cur_x + width + (2 * I), cur_y, cur_z),
              (cur_x + width + (2 * I), cur_y + jamb, cur_z), (cur_x + ex, cur_y + jamb, cur_z),
              (cur_x + I, cur_y, cur_z + I), (cur_x + width + I, cur_y, cur_z + I),
              (cur_x + width + I, cur_y + jamb, cur_z + I), (cur_x + I, cur_y + jamb, cur_z + I)]
    
    cur_z += height + I
    verts += [(cur_x + I, cur_y, cur_z), (cur_x + width + I, cur_y, cur_z),
              (cur_x + width + I, cur_y + jamb, cur_z), (cur_x + I, cur_y + jamb, cur_z),
              (cur_x + ex, cur_y, cur_z + I), (cur_x + width + (2 * I), cur_y, cur_z + I),
              (cur_x + width + (2 * I), cur_y + jamb, cur_z + I), (cur_x + ex, cur_y + jamb, cur_z + I)]

    # top and bottom  
    for i in range(2):
        faces += [(p + 0, p + 1, p + 5, p + 4), (p + 4, p + 5, p + 6, p + 7), (p + 0, p + 3, p + 2, p + 1),
                  (p + 2, p + 3, p + 7, p + 6)]
        p += 8   
        
    p -= 16
    if full_jamb:  # don't do left side
        faces += [(p + 0, p + 4, p + 8, p + 12), (p + 0, p + 12, p + 15, p + 3), (p + 3, p + 15, p + 11, p + 7),
                  (p + 4, p + 7, p + 11, p + 8)]
                
    faces += [(p + 1, p + 2, p + 14, p + 13), (p + 1, p + 13, p + 9, p + 5), (p + 5, p + 9, p + 10, p + 6),
              (p + 2, p + 6, p + 10, p + 14)]


# add faces and verts to (verts and faces)
# start_y and start_z need to be center of window pane at inside on y
# wide_frame is extra [bottom, right, top, left]
def create_rectangle_pane(verts, faces, glass_indices, width, height, sx, sy, sz, wide_frame):
    p, f = len(verts), len(faces)
    w, h = width / 2, height / 2

    # loops allow just one corner to be done, and then all the rest is done by just inverting values    
    for i2 in range(1, -2, -2):  # invert for top and bottom
        ex = wide_frame[0] if i2 == 1 else -wide_frame[2]
        
        for i in range(-1, 2, 2):  # invert for sides
            ex2 = wide_frame[3] if i == -1 else -wide_frame[1]
                
            verts += [(sx + i * w, sy - t, sz - i2 * h), (sx + i * (w - I) + ex2, sy - t, sz - i2 * (h - I) + ex),
                      (sx + i * (w - I - bevelXZ) + ex2, sy - t + bevelY, sz - i2 * (h - I - bevelXZ) + ex),
                      (sx + i * (w - I) + ex2, sy - t + bevelY, sz - i2 * (h - I) + ex),
                      (sx + i * (w - I) + ex2, sy - ei, sz - i2 * (h - I) + ex),
                      (sx + i * (w - I) + ex2, sy, sz - i2 * (h - I) + ex), (sx + i * w, sy, sz - i2 * h)]
                    
    # faces
    faces += [(p+0, p+7, p+8, p+1), (p+1, p+8, p+9, p+2), (p+6, p+5, p+12, p+13)]
    p += 14
    faces += [(p+0, p+1, p+8, p+7), (p+1, p+2, p+9, p+8), (p+6, p+13, p+12, p+5)]
    p -= 14
    faces += [(p, p+1, p+15, p+14), (p+1, p+2, p+16, p+15), (p, p+14, p+20, p+6),
              (p+6, p+20, p+19, p+5), (p+4, p+5, p+19, p+18)]
    p += 7
    faces += [(p, p+14, p+15, p+1), (p+1, p+15, p+16, p+2), (p, p+6, p+20, p+14),
              (p+6, p+5, p+19, p+20), (p+4, p+18, p+19, p+5)]
    p -= 7

    faces += [(p+2, p+9, p+23, p+16), (p+4, p+18, p+25, p+11), (p, p+6, p+13, p+7), (p+14, p+21, p+27, p+20), 
              (p+2, p+3, p+17, p+16), (p+3, p+4, p+17, p+18), (p+11, p+10, p+24, p+25), (p+10, p+9, p+23, p+24),
              (p+4, p+5, p+12, p+11), (p+18, p+19, p+26, p+25)]

    glass_indices += [f + 16, f + 17]


def double_hung(width, height, jamb, num):
    verts, faces, glass_indices = [], [], []
    sx = -(num - 1) / 2 * width - (num - 1) * HI
    full_jamb = True
    
    for i in range(num):
        create_rectangle_jamb(verts, faces, width, height, jamb, full_jamb, sx)
        
        # panes
        create_rectangle_pane(verts, faces, glass_indices, width, (height + I) / 2, sx, 0.0, I + (height + I) / 4,
                              [HI, 0.0, 0.0, 0.0])
        create_rectangle_pane(verts, faces, glass_indices, width, (height + I) / 2, sx, (1.5 / METRIC_INCH),
                              I + (height + I) / 4 + (height - I) / 2, [0.0, 0.0, 0.0, 0.0])
        
        sx += width + I
        full_jamb = False
                                        
    return verts, faces, glass_indices


def gliding(width, height, slide_right, jamb_w):
    verts, faces, glass_indices = [], [], []
    
    create_rectangle_jamb(verts, faces, width, height, jamb_w, True, 0.0)
    
    if slide_right:
        create_rectangle_pane(verts, faces, glass_indices, (width + I) / 2, height, -(width - I) / 4, 0.0,
                              (height + 2 * I) / 2, [0.0, HI, 0.0, I])
        create_rectangle_pane(verts, faces, glass_indices, (width + 2 * I) / 2, height, (width - 2 * I) / 4, I + HI,
                              (height + 2 * I) / 2, [0.0, 0.0, 0.0, HI])
    else:
        create_rectangle_pane(verts, faces, glass_indices, (width + I) / 2, height, -(width - I) / 4, I + HI,
                              (height + 2 * I) / 2, [0.0, 0.0, 0.0, HI])
        create_rectangle_pane(verts, faces, glass_indices, (width + I) / 2, height, (width - I) / 4, 0.0,
                              (height + 2 * I) / 2, [0.0, HI, 0.0, I])
    
    return verts, faces, glass_indices


def gothic(width, height, res, is_slider, jamb_w):
    # make res even because IntProperty step isn't not currently supported
    if res % 2 != 0:
        res += 1
        
    verts, faces, glass_indices = [], [], []
    hw, w = width / 2, jamb_w / 2
    hres = int(res / 2)

    edge_height = height - sqrt(3)*hw
    end_angles = [acos((hw + I) / (width + 2 * I)), acos((hw + I) / (width + I)), acos((hw + I) / width),
                  acos((hw + I) / (width - bevelXZ))]

    y = 0 if is_slider else -t / 2
    h_off = edge_height / 2 if is_slider else 0

    # lists keep from having multiple sections of codes with only slight differences
    outer_inner = [[I, end_angles[0], 0.0], [0.0, end_angles[1], I]]  # width offset, end_angle, leg height offset
    offsets = [[0, int(res/2) + 1, -1, 1], [int(res/2) - 1, -1, 1, -1]]  # start, stop, mod1/angle side, mod2/step
    
    for oi in outer_inner:
        verts += [(-hw-oi[0], -w, oi[2]), (-hw-oi[0], w, oi[2])]
        ang_off = oi[1] / hres
              
        for g in offsets:
            for i in range(g[0], g[1], g[3]):
                x, z = point_rotation((g[2] * (hw+oi[0]), edge_height),
                                      (g[3] * (hw + I), edge_height), g[2] * ang_off * i)
                verts += [(x, -w, z), (x, w, z)]
            
        verts += [(hw+oi[0], -w, oi[2]), (hw+oi[0], w, oi[2])]
    off = int(len(verts)/2)   
    p = 0
    
    for i in range(res+2):
        faces += [(p, p+off, p+off+2, p+2), (p+off, p+off+1, p+off+3, p+off+2), (p, p+2, p+3, p+1),
                  (p+1, p+3, p+off+3, p+off+1)]
        p += 2
    faces += [(p, p+off, off, 0), (p, p+1, 1, 0), (1, off+1, p+off+1, p+1), (off, p+off, p+off+1, off+1)]
    
    # window
    temp1 = [(-hw, y, I + h_off), (-hw, y + t, I + h_off)]
    ang_off = end_angles[1] / hres
    for g in offsets:
        for i in range(g[0], g[1], g[3]):
            x, z = point_rotation((g[2] * hw, edge_height), (g[3] * (hw + I), edge_height), g[2] * ang_off * i)
            temp1 += [(x, y, z), (x, y+t, z)]  
    temp1 += [(hw, y, I + h_off), (hw, y + t, I + h_off)]
    
    temp2 = [(-hw + I, y, 2 * I + h_off), (-hw + I, y + t - ei, 2 * I + h_off), (-hw + I, y + t, 2 * I + h_off)]
    ang_off = end_angles[2] / hres
    for g in offsets:
        for i in range(g[0], g[1], g[3]):
            x, z = point_rotation((g[2] * (hw - I), edge_height), (g[3] * (hw + I), edge_height), g[2] * ang_off * i)
            temp2 += [(x, y, z), (x, y+t-ei, z), (x, y+t, z)]  
    temp2 += [(hw - I, y, 2 * I + h_off), (hw - I, y + t - ei, 2 * I + h_off), (hw - I, y + t, 2 * I + h_off)]
    
    temp3 = [(-hw + I + bevelXZ, y + bevelY, 2 * I + bevelXZ + h_off)]
    ang_off = end_angles[3] / hres
    for g in offsets:
        for i in range(g[0], g[1], g[3]):
            x, z = point_rotation((g[2] * (hw - I - bevelXZ), edge_height),
                                  (g[3] * (hw + I), edge_height), g[2] * ang_off * i)
            temp3 += [(x, y+bevelY, z)]  
    temp3 += [(hw - I - bevelXZ, y + bevelY, 2 * I + bevelXZ + h_off)]

    inner_face, outer_face = sort_window_verts(temp1, temp2, temp3, verts)
    p2 = p+off+2  
    faces.append(inner_face)
    faces.append(outer_face)
    
    p += off+2
    for i in range(res+2):
        faces += [(p, p+2, p+8, p+6), (p+2, p+3, p+9, p+8), (p+4, p+5, p+11, p+10), (p+1, p+7, p+11, p+5),
                  (p, p+1, p+7, p+6)]
        p += 6
    faces += [(p2, p, p+2, p2+2), (p2, p2+1, p+1, p), (p+1, p2+1, p2+5, p+5), (p2+5, p2+4, p+4, p+5),
              (p2+2, p+2, p+3, p2+3)]

    if is_slider:
        create_rectangle_pane(verts, faces, glass_indices, width, h_off + t, 0.0, y, h_off / 2 + I + t / 2,
                              [t - I for i in range(4)])
          
    return verts, faces, glass_indices


def oval(width, height, res, jamb_w):
    # make res even because IntProperty step isn't not currently supported
    if res % 2 != 0:
        res += 1
        
    verts, faces, glass_indices = [], [], []
    
    hw = width / 2
    hh = height / 2
    w = jamb_w / 2
    hres = int(res / 2)  
    
    # jamb
    for offset in [I, 0.0]:  # top
        verts += [(-hw - offset, -w, 0.0), (-hw - offset, w, 0.0)]
        for i in arch_function(hw + offset, hh + offset, hres):
            verts += [(i[0], -w, i[1]), (i[0], w, i[1])]
        verts += [(hw + offset, -w, 0.0), (hw + offset, w, 0.0)]   
    
    # insert vertices at key positions to make the inner and outer loop vertices consecutively numbered
    p = int(len(verts) / 2)               
    for i in arch_function(hw + I, hh + I, hres):
        verts.insert(p, (i[0], w, -i[1]))
        verts.insert(p, (i[0], -w, -i[1]))
        
    e = len(verts)        
    for i in arch_function(hw, hh, hres):
        verts.insert(e, (i[0], w, -i[1]))  
        verts.insert(e, (i[0], -w, -i[1]))        
    
    p = int(len(verts) / 2)
    # top faces
    for i in range(0, 2*res - 2, 2):
        faces += [(i, i+2, i+3, i+1), (i, i+p, i+p+2, i+2), (i+p, i+p+1, i+p+3, i+p+2), (i+p+1, i+1, i+3, i+p+3)]      

    # left side connecting faces
    e = len(verts) - 1
    faces += [(p-2, e-1, p, 0), (p-2, 0, 1, p-1), (e, p-1, 1, p+1), (e-1, e, p+1, p)]
                
    # window - TOP
    temp1 = [(-hw, y, 0.0), (-hw, y+t, 0.0)]
    for i in arch_function(hw, hh, hres):  # outer two vertices
        temp1 += [(i[0], y, i[1]), (i[0], y+t, i[1])]
    temp1 += [(hw, y, 0.0), (hw, y+t, 0.0)]
    insert1 = len(temp1)        
    
    temp2 = [(-hw + I, y, 0.0), (-hw + I, y + t - ei, 0.0), (-hw + I, y + t, 0.0)]
    for i in arch_function(hw - I, hh - I, hres):  # center three vertices
        temp2 += [(i[0], y, i[1]), (i[0], y + t - ei, i[1]), (i[0], y + t, i[1])]
    temp2 += [(hw - I, y, 0.0), (hw - I, y + t - ei, 0.0), (hw - I, y + t, 0.0)]
    insert2 = len(temp2)        
    
    temp3 = [(-hw + I + bevelXZ, y + bevelY, 0.0)]
    for i in arch_function(hw - I - bevelXZ, hh - I - bevelXZ, hres):  # inner vertex
        temp3 += [(i[0], y + bevelY, i[1])] 
    temp3 += [(hw - I - bevelXZ, y + bevelY, 0.0)]
    insert3 = len(temp3)
    
    # window - BOTTOM
    for i in arch_function(hw, hh, hres):  # outer two vertices
        temp1.insert(insert1, (i[0], y+t, -i[1]))
        temp1.insert(insert1, (i[0], y, -i[1]))
        
    for i in arch_function(hw - I, hh - I, hres):  # center three vertices
        temp2.insert(insert2, (i[0], y + t, -i[1]))
        temp2.insert(insert2, (i[0], y + t - ei, -i[1]))
        temp2.insert(insert2, (i[0], y, -i[1]))
        
    for i in arch_function(hw - I - bevelXZ, hh - I - bevelXZ, hres):  # inner vertex
        temp3.insert(insert3, (i[0], y + bevelY, -i[1]))
    
    # put all vertices in correct order into main list 
    inner_face, outer_face = sort_window_verts(temp1, temp2, temp3, verts)
    p = e + 1
    glass_indices += [len(faces), len(faces) + 1]
    faces += [inner_face, outer_face]
    for i in range(res - 1):
        faces += [(p, p+2, p+8, p+6), (p+2, p+3, p+9, p+8), (p+4, p+5, p+11, p+10), (p+1, p+7, p+11, p+5),
                  (p, p+1, p+7, p+6)]
        p += 6
    faces += [(e+1, p, p+2, e+3), (p+2, p+3, e+4, e+3), (p+4, p+5, e+5, e+6), (p+5, p+1, e+2, e+6), (e+1, p, p+1, e+2)]
        
    return verts, faces, glass_indices


def polygon(radius, sides, jamb_w):
    verts, faces, glass_indices = [], [], []
    
    ang = 360 / sides  
    w = jamb_w / 2    
    th = I / cos(radians(ang) / 2)  # adjust inch because of angle
        
    # jamb verts
    for i in range(sides): 
        x, z = point_rotation((radius, 0.0), (0.0, 0.0), radians(i*ang + 90))      
        verts += [(x, -w, z), (x, w, z)]
    off = len(verts)
    
    for i in range(sides):
        x, z = point_rotation((radius-th, 0.0), (0.0, 0.0), radians(i*ang + 90))  
        verts += [(x, -w, z), (x, w, z)]   
    
    # jamb faces
    p = 0
    for i in range(sides-1):
        faces += [(p, p+1, p+3, p+2), (p, p+2, p+2+off, p+off), (p+1, p+1+off, p+3+off, p+3),
                  (p+off, p+2+off, p+3+off, p+1+off)]
        p += 2  
    faces += [(p, p+1, 1, 0), (p, 0, off, p+off), (p+1, p+1+off, 1+off, 1), (p+off, off, 1+off, p+1+off)]
    
    temp1 = []
    for i in range(sides):
        x, z = point_rotation((radius - th, 0.0), (0.0, 0.0), radians(i*ang + 90))
        temp1 += [(x, y, z), (x, y+t, z)]
        
    temp2 = []
    for i in range(sides):
        x, z = point_rotation((radius - 2*th, 0.0), (0.0, 0.0), radians(i*ang + 90))
        temp2 += [(x, y, z), (x, y+t-ei, z), (x, y+t, z)]
        
    temp3 = []
    for i in range(sides):
        x, z = point_rotation((radius - 2*th - bevelXZ, 0.0), (0.0, 0.0), radians(i*ang + 90))
        temp3 += [(x, y+bevelY, z)]
        
    inner_face, outer_face = sort_window_verts(temp1, temp2, temp3, verts)
    inner_face.reverse()  # reverse faces because verts were done counterclockwise, not clockwise
    outer_face.reverse()
    
    # pane faces
    glass_indices += [len(faces), len(faces) + 1]
    faces.append(inner_face)
    faces.append(outer_face)
    p += off+2
    p2 = p
    for i in range(sides - 1):
        faces += [(p, p+6, p+8, p+2), (p+2, p+8, p+9, p+3), (p+4, p+10, p+11, p+5), (p+1, p+5, p+11, p+7),
                  (p, p+6, p+7, p+1)]
        p += 6
    faces += [(p2, p2+2, p+2, p), (p2, p, p+1, p2+1), (p+1, p+5, p2+5, p2+1), (p2+5, p+5, p+4, p2+4),
              (p2+2, p2+3, p+3, p+2)]
    
    return verts, faces, glass_indices


# takes separate groups of vertices that compose the window pane and adds them into verts in a manner that makes it easy
# to create faces
def sort_window_verts(temp1, temp2, temp3, verts):
    inner_face = []
    outer_face = []
    p_final = len(verts)
    for i in range(int(len(temp1) / 2)):
        verts += temp1[0:2]
        del temp1[0:2]
        verts += [temp2[0]]
        verts += [temp3[0]]
        verts += temp2[1:3]        
        del temp2[0:3]
        del temp3[0]
        inner_face.insert(0, p_final+3)
        outer_face.append(p_final+4)
        p_final += 6
        
    return inner_face, outer_face   


def stationary(width, height, jamb_w, num):
    verts, faces, glass_indices = [], [], []
    sx = -(num - 1) / 2 * width - (num - 1) * HI
    full_jamb = True

    for i in range(num):
        create_rectangle_jamb(verts, faces, width, height, jamb_w, full_jamb, sx)
        create_rectangle_pane(verts, faces, glass_indices, width, height, sx, 0.75 / METRIC_INCH, (height + 2 * I) / 2,
                              [0.0, 0.0, 0.0, 0.0])

        sx += width + I
        full_jamb = False
    
    return verts, faces, glass_indices


# create window based off of parameters
def create_window(context, types, sub_type, jamb_w, dh_width, dh_height, gang_num, gl_width, gl_height, gl_slide_right,
                  so_width, so_height, so_height_tall, sides, radius, is_full_circle, angle, roundness, res, is_slider,
                  ba_width, ba_height, is_bay, bay_angle, segments, is_split_center, is_double_hung, depth):
     
    verts, faces, ob_to_join, glass_indices = [], [], [], []

    if types == "1":
        verts, faces, glass_indices = double_hung(dh_width, dh_height, jamb_w, gang_num)
    elif types == "2":
        verts, faces, glass_indices = gliding(gl_width, gl_height, gl_slide_right, jamb_w)
    elif types == "3":
        verts, faces, glass_indices = stationary(so_width, so_height, jamb_w, gang_num)
    # odd-shaped
    elif types == "4":
        if sub_type == "1": 
            verts, faces, glass_indices = polygon(radius, sides, jamb_w)
        elif sub_type == "2":
            verts, faces, glass_indices = circular(radius, angle, res, jamb_w, is_full_circle)
        elif sub_type == "3":
            verts, faces, glass_indices = arch(so_width, so_height, roundness, res, is_slider, jamb_w)
        elif sub_type == "4":
            verts, faces, glass_indices = gothic(so_width, so_height_tall, res, is_slider, jamb_w)
        elif sub_type == "5":
            verts, faces, glass_indices = oval(so_width, so_height, res, jamb_w)
    elif types == "5":
        verts, faces, glass_indices = bay(ba_width, ba_height, is_bay, bay_angle, segments, is_split_center,
                                          is_double_hung, jamb_w, depth)
    
    return verts, faces, ob_to_join, glass_indices


# update window
def update_window(self, context):
    ob = context.object

    mats = []
    for mat in ob.data.materials:
        mats.append(mat.name)
    
    verts, faces, ob_to_join, gl_is = create_window(context, ob.jv_w_types, ob.jv_odd_types, ob.jv_jamb_width,
                                                    ob.jv_dh_width, ob.jv_dh_height, ob.jv_gang_num, ob.jv_gl_width,
                                                    ob.jv_gl_height, ob.jv_gl_slide_right, ob.jv_so_width,
                                                    ob.jv_so_height, ob.jv_so_height_tall, ob.jv_sides, ob.jv_o_radius,
                                                    ob.jv_full_circle, ob.jv_w_angle, ob.jv_roundness, ob.jv_resolution,
                                                    ob.jv_is_slider, ob.jv_ba_width, ob.jv_ba_height, ob.jv_is_bay,
                                                    ob.jv_bay_angle, ob.jv_bow_segments, ob.jv_is_split_center,
                                                    ob.jv_is_double_hung, ob.jv_depth)
            
    old_mesh = ob.data
    mesh = bpy.data.meshes.new(name="window")
    mesh.from_pydata(verts, [], faces)
    mesh.update(calc_edges=True)
    ob.data = mesh
    
    # remove old mesh
    for i in bpy.data.objects:
        if i.data == old_mesh:
            i.data = mesh
    
    old_mesh.user_clear()
    bpy.data.meshes.remove(old_mesh)

    # assign materials to correct faces, first material is frame, second is glass
    if len(mats) >= 1:
        ob.data.materials.append(bpy.data.materials[mats[0]])
    else:
        mat = bpy.data.materials.new(ob.name + "_frame")
        mat.use_nodes = True
        ob.data.materials.append(mat)

    if len(mats) >= 2:
        ob.data.materials.append(bpy.data.materials[mats[1]])
    else:
        mat = bpy.data.materials.new(ob.name + "_glass")
        mat.use_nodes = True
        ob.data.materials.append(mat)

    assign_glass_faces(context, gl_is)

    if ob.jv_is_unwrap:
        unwrap_object(self, context)
        if ob.jv_is_random_uv:
            random_uvs(self, context)


def assign_glass_faces(context, indices):
    o = context.object

    for i in indices:
        o.data.polygons[i].material_index = 1


def window_materials(self, context):
    o, mat = context.object, None

    if o.jv_color_image == "rgba":
        mat = glossy_diffuse_material(bpy, o.jv_rgba_color, (1, 1, 1), 0.05, 0.1, o.name + "_frame")
    else:
        if o.jv_col_image == "":
            self.report({"ERROR"}, "JARCH Vis: No Color Image Filepath")
            return
        if o.jv_is_bump and o.jv_norm_image == "":
            self.report({"ERROR"}, "JARCH VIs: No Normal Image Filepath")
            return

        mat = image_material(bpy, o.jv_im_scale, o.jv_col_image, o.jv_norm_image, o.jv_bump_amo, o.jv_is_bump,
                             o.name + "_frame", True, 0.1, 0.05, o.jv_is_rotate, None)

    if mat is None:
        self.report({"ERROR"}, "JARCH Vis: Invalid Filepath Found When Creating Material")
        return
    elif len(o.data.materials) >= 1:
        o.data.materials[0] = mat
    elif len(o.data.materials) == 0:
        o.data.materials.append(mat)

    mat2 = architectural_glass_material(bpy, (1, 1, 1, 1), o.name + "_glass")
    if len(o.data.materials) >= 2:
        o.data.materials[1] = mat2
    else:
        o.data.materials.append(mat2)

    for i in bpy.data.materials:
        if i.users == 0:
            bpy.data.materials.remove(i)


class WindowMaterials(bpy.types.Operator):
    bl_idname = "mesh.jv_window_materials"
    bl_label = "Generate\\Update Materials"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        window_materials(self, context)
        return {"FINISHED"}


class WindowPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_jv_window"
    bl_label = "JARCH Vis: Window"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "JARCH Vis"

    def draw(self, context):
        layout = self.layout
        if bpy.context.mode == "EDIT_MESH":
            layout.label("JARCH Vis: Windows Doesn't Work In Edit Mode", icon="ERROR")
        elif context.object is None:
            layout.operator("mesh.jv_window_add", icon="OUTLINER_OB_LATTICE")
        elif context.object.jv_internal_type == "window":
            o = context.object
            layout.label("Window Type:")
            layout.prop(o, "jv_w_types", icon="OBJECT_DATAMODE")

            if o.jv_w_types == "4":
                layout.label("Shape:")
                layout.prop(o, "jv_odd_types", icon="SPACE2")

            # parameters
            layout.separator()
            layout.prop(o, "jv_jamb_width")

            # double hung
            layout.separator()
            if o.jv_w_types == "1":
                layout.prop(o, "jv_dh_width")
                layout.prop(o, "jv_dh_height")
                layout.prop(o, "jv_gang_num")
            # gliding
            elif o.jv_w_types == "2":
                layout.prop(o, "jv_gl_width")
                layout.prop(o, "jv_gl_height")
                layout.prop(o, "jv_gl_slide_right", icon="FORWARD")
            # stationary
            elif o.jv_w_types == "3":
                layout.prop(o, "jv_so_width")
                layout.prop(o, "jv_so_height")
                layout.prop(o, "jv_gang_num")
            # odd-shaped
            elif o.jv_w_types == "4":
                # polygon
                if o.jv_odd_types == "1":
                    layout.prop(o, "jv_o_radius")
                    layout.prop(o, "jv_sides")
                # circular
                elif o.jv_odd_types == "2":
                    layout.prop(o, "jv_o_radius")
                    layout.prop(o, "jv_resolution")
                    layout.prop(o, "jv_full_circle", icon="MESH_CIRCLE")
                    if not o.jv_full_circle:
                        layout.prop(o, "jv_w_angle")

                else:
                    layout.prop(o, "jv_so_width")

                    if o.jv_odd_types == "4":  # gothic
                        layout.prop(o, "jv_so_height_tall")
                        layout.prop(o, "jv_is_slider", icon="SETTINGS")
                    else:
                        layout.prop(o, "jv_so_height")

                    layout.separator()
                    layout.prop(o, "jv_resolution")

                    # arch
                    if o.jv_odd_types == "3":
                        layout.prop(o, "jv_roundness")
                        layout.prop(o, "jv_is_slider", icon="SETTINGS")

            # bay
            elif o.jv_w_types == "5":
                layout.prop(o, "jv_ba_width")
                layout.prop(o, "jv_ba_height")
                layout.separator()

                layout.prop(o, "jv_is_bay", icon="NOCURVE")
                if o.jv_is_bay:
                    layout.prop(o, "jv_bay_angle", icon="MAN_ROT")
                    layout.prop(o, "jv_depth")
                    layout.separator()
                    layout.prop(o, "jv_is_split_center", icon="PAUSE")
                else:
                    layout.prop(o, "jv_bow_segments")
                layout.prop(o, "jv_is_double_hung", icon="SPLITSCREEN")

            layout.separator()
            layout.prop(o, "jv_is_unwrap", icon="GROUP_UVS")
            if o.jv_is_unwrap:
                layout.prop(o, "jv_is_random_uv", icon="RNDCURVE")

            # materials
            layout.separator()
            if context.scene.render.engine == "CYCLES":
                layout.prop(o, "jv_is_material", icon="MATERIAL")
            else:
                layout.label("Materials Only Supported With Cycles", icon="POTATO")

            if o.jv_is_material and context.scene.render.engine == "CYCLES":
                layout.separator()
                layout.label("Frame Material:")
                layout.prop(o, "jv_color_image")

                if o.jv_color_image == "rgba":
                    layout.prop(o, "jv_rgba_color")
                else:
                    layout.prop(o, "jv_col_image", icon="COLOR")
                    layout.prop(o, "jv_is_bump", icon="SMOOTHCURVE")

                    if o.jv_is_bump:
                        layout.prop(o, "jv_norm_image", icon="TEXTURE")
                        layout.prop(o, "jv_bump_amo")

                    layout.prop(o, "jv_im_scale")
                    layout.prop(o, "jv_is_rotate", icon="MAN_ROT")

                layout.separator()
                layout.operator("mesh.jv_window_materials", icon="MATERIAL")
                layout.prop(o, "jv_is_preview", icon="SCENE")

            # operators
            layout.separator()
            layout.separator()
            layout.operator("mesh.jv_window_update", icon="FILE_REFRESH")
            layout.operator("mesh.jv_window_delete", icon="CANCEL")
            layout.operator("mesh.jv_window_add", icon="OUTLINER_OB_LATTICE")

        else:
            if context.object.jv_internal_type != "":
                layout.label("This Is Already A JARCH Vis Object", icon="INFO")
            layout.operator("mesh.jv_window_add", icon="OUTLINER_OB_LATTICE")


class WindowAdd(bpy.types.Operator):
    bl_idname = "mesh.jv_window_add"
    bl_label = "Add Window"
    bl_description = "JARCH Vis: Window Generator"
    
    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        o = context.object
        o.jv_internal_type = "window"
        o.jv_object_add = "add"
        return {"FINISHED"}


class WindowUpdate(bpy.types.Operator):
    bl_idname = "mesh.jv_window_update"
    bl_label = "Update Window"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        update_window(self, context)
        return {"FINISHED"}


class WindowDelete(bpy.types.Operator):
    bl_idname = "mesh.jv_window_delete"
    bl_label = "Delete Window"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        bpy.ops.object.delete()          
        return {"FINISHED"}


def register():
    bpy.utils.register_module(__name__)   


def unregister():
    bpy.utils.unregister_module(__name__)
    
if __name__ == "__main__":
    register()
