import bpy
from bpy.props import EnumProperty, FloatProperty, StringProperty, BoolProperty, IntProperty
from math import radians, sqrt, acos, cos, sin
from . jarch_utils import METRIC_INCH, METRIC_FOOT, I, HI, point_rotation

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


# bay windows
def bay(width, height, depth, segments, split_center, double_hung, jamb_w):
    verts, faces = [], []
    ang = radians(180) / segments
    hw = width / 2

    return verts, faces


# circular
def circular(radius, angle, res, jamb_w, full):
    verts, faces = [], []
        
    if full:
        verts, faces = polygon(radius, res, jamb_w)
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
        faces.append(inner_face)
        faces.append(outer_face)
        
        p2 = p
        for i in range(res+3):
            faces += [(p, p+2, p+8, p+6), (p+2, p+3, p+9, p+8), (p+4, p+5, p+11, p+10), (p+1, p+7, p+11, p+5), (p, p+1, p+7, p+6)]
            p += 6
        faces += [(p, p+2, p2+2, p2), (p+2, p+3, p2+3, p2+2), (p2+1, p2+5, p+5, p+1), (p2+5, p2+4, p+4, p+5)]

    return verts, faces


# roundness refers to what percentage of height that arch is
def arch(width, height, roundness, res, is_slider, jamb_w):
    verts, faces = [], []
    
    arch_h = height * (1 / (100/roundness))
    arch_h2 = arch_h + I
    h = height - arch_h  # height to bottom of arch
    hw = width/2
    hw2 = width/2 + I
    w = jamb_w/2      
    y = -t/2   
    
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
        faces += [(p, p+1, p+3, p+2), (p, p+2, p+off+2, p+off),
                  (p+off, p+off+2, p+off+3, p+off+1), (p+1, p+off+1, p+off+3, p+3)]
        p += 2
    
    # connecting faces
    faces += [(p2-8, p2-7, p2, p2+off), (p2-7, p2-6, p2+1, p2), (p2-6, p2-5, p2+off+1, p2+1),
              (p2-8, p2+off, p2+off+1, p2-5), (p2-4, p2-3, p+off, p), (p2-3, p2-2, p+off+1, p+off),
              (p2-2, p2-1, p+1, p+off+1), (p2-1, p2-4, p, p+1)]  # right side
    
    # if slide add extra pane
    sz, ph = I, h
    if is_slider:
        create_rectangle_pane(verts, faces, width, (h + I) / 2, 0.0, 0.0, I + (h + I) / 4, [0.0, 0.0, 0.0, 0.0])
        sz = (h + I) / 2
        ph = h - (h - I) / 2
        y = 0.0
     
    p = len(verts)
    # border bottom
    verts += [(-hw, y, sz), (hw, y, sz), (hw, y+t, sz), (-hw, y+t, sz), (-hw + I, y, sz + I), (hw - I, y, sz + I),
              (hw - I, y + t, sz + I), (-hw + I, y + t, sz + I), (-hw + I + bevelXZ, y + bevelY, sz + I + bevelXZ),
              (hw - I - bevelXZ, y + bevelY, sz + I + bevelXZ), (hw - I, y + t - ei, sz + I),
              (-hw + I, y + t - ei, sz + I)]
            
    # border middle
    sz += ph    
    p3 = len(verts)
    verts += [(-hw, y, sz), (hw, y, sz), (hw, y+t, sz), (-hw, y+t, sz), (-hw + I, y, sz), (hw - I, y, sz),
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
    faces += [(p, p+1, p+5, p+4), (p+4, p+5, p+9, p+8), (p, p+3, p+2, p+1), (p+2, p+3, p+7, p+6),
              (p+6, p+7, p+11, p+10), (p, p+4, p+16, p+12), (p+4, p+8, p+20, p+16), (p+1, p+13, p+17, p+5),
              (p+5, p+17, p+21, p+9), (p+2, p+6, p+18, p+14), (p+6, p+10, p+22, p+18), (p+11, p+7, p+19, p+23),
              (p+7, p+3, p+15, p+19), (p+8, p+9, p+21, p+20), (p+10, p+11, p+23, p+22)]
    
    # combine vert lists with correct indexs for easier indexing
    inner_face, outer_face = sort_window_verts(temp1, temp2, temp3, verts)
    p4 = len(verts) 
    
    # faces for arch
    p = p2   
    for i in range(res - 2):
        faces += [(p, p+2, p+8, p+6), (p+2, p+3, p+9, p+8), (p+4, p+5, p+11, p+10), (p+1, p+7, p+11, p+5),
                  (p, p+1, p+7, p+6)]
        p += 6
    faces.append(inner_face)
    faces.append(outer_face)
        
    # extra faces
    faces += [(p3, p3+4, p3+14, p3+12), (p3+4, p3+8, p3+15, p3+14), (p3+7, p3+3, p3+13, p3+17),
              (p3+11, p3+7, p3+17, p3+16), (p3, p3+3, p3+13, p3+12), (p3+1, p4-6, p4-4, p3+5), (p3+5, p4-4, p4-3, p3+9),
              (p3+6, p3+10, p4-2, p4-1), (p3+2, p3+6, p4-1, p4-5), (p3+1, p4-6, p4-5, p3+2), (p3+8, p3+9, p4-3, p3+15),
              (p3+10, p3+11, p3+16, p4-2)]
    
    return verts, faces


# creates a single window with two panes in it, startX, startY define the bottom center of the window
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
def create_rectangle_pane(verts, faces, width, height, sx, sy, sz, wide_frame):
    p = len(verts)    
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


def double_hung(width, height, jamb, num):
    verts, faces = [], []             
    sx = -(num - 1) / 2 * width - (num - 1) * HI
    full_jamb = True
    
    for i in range(num):
        create_rectangle_jamb(verts, faces, width, height, jamb, full_jamb, sx)
        
        # panes
        create_rectangle_pane(verts, faces, width, (height + I) / 2, sx, 0.0, I + (height + I) / 4, [HI, 0.0, 0.0, 0.0])
        create_rectangle_pane(verts, faces, width, (height + I) / 2, sx, (1.5 / METRIC_INCH), I + (height + I) / 4 +
                              (height - I) / 2, [0.0, 0.0, 0.0, 0.0])
        
        sx += width + I
        full_jamb = False
                                        
    return verts, faces 


def gliding(width, height, slide_right, jamb_w):
    verts, faces = [], []
    
    create_rectangle_jamb(verts, faces, width, height, jamb_w, True, 0.0)
    
    if slide_right:
        create_rectangle_pane(verts, faces, (width + I) / 2, height, -(width - I) / 4, 0.0, (height + 2 * I) / 2,
                              [0.0, HI, 0.0, I])
        create_rectangle_pane(verts, faces, (width + 2 * I) / 2, height, (width - 2 * I) / 4, I + HI,
                              (height + 2 * I) / 2, [0.0, 0.0, 0.0, HI])
    else:
        create_rectangle_pane(verts, faces, (width + I) / 2, height, -(width - I) / 4, I + HI, (height + 2 * I) / 2,
                              [0.0, 0.0, 0.0, HI])
        create_rectangle_pane(verts, faces, (width + I) / 2, height, (width - I) / 4, 0.0, (height + 2 * I) / 2,
                              [0.0, HI, 0.0, I])
    
    return verts, faces 


def gothic(width, height, res, is_slider, jamb_w):
    # make res even because IntProperty step isn't not currently supported
    if res % 2 != 0:
        res += 1
        
    verts, faces = [], []    
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
        create_rectangle_pane(verts, faces, width, h_off + t, 0.0, y, h_off / 2 + I + t / 2, [t - I for i in range(4)])
          
    return verts, faces


def oval(width, height, res, jamb_w):
    # make res even because IntProperty step isn't not currently supported
    if res % 2 != 0:
        res += 1
        
    verts, faces = [], []
    
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
    faces += [inner_face, outer_face]
    for i in range(res - 1):
        faces += [(p, p+2, p+8, p+6), (p+2, p+3, p+9, p+8), (p+4, p+5, p+11, p+10), (p+1, p+7, p+11, p+5),
                  (p, p+1, p+7, p+6)]
        p += 6
    faces += [(e+1, p, p+2, e+3), (p+2, p+3, e+4, e+3), (p+4, p+5, e+5, e+6), (p+5, p+1, e+2, e+6), (e+1, p, p+1, e+2)]
        
    return verts, faces         


def polygon(radius, sides, jamb_w):
    verts, faces = [], []   
    
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
    
    return verts, faces


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


def stationary(width, height, jamb_w):
    verts, faces = [], []
    
    create_rectangle_jamb(verts, faces, width, height, jamb_w, True, 0.0)
    create_rectangle_pane(verts, faces, width, height, 0.0, 0.75 / METRIC_INCH, (height + 2 * I) / 2,
                          [0.0, 0.0, 0.0, 0.0])
    
    return verts, faces   


# create window based off of parameters
def create_window(context, types, sub_type, jamb_w, dh_width, dh_height, dh_num, gl_width, gl_height, gl_slide_right,
                  so_width, so_height, so_height_tall, sides, radius, is_full_circle, angle, roundness, res, is_slider,
                  ba_width, ba_height, depth, segments, is_split_center, is_double_hung):
     
    verts, faces, ob_to_join = [], [], []     

    if types == "1":
        verts, faces = double_hung(dh_width, dh_height, jamb_w, dh_num)
    elif types == "2":
        verts, faces = gliding(gl_width, gl_height, gl_slide_right, jamb_w)
    elif types == "3":
        verts, faces = stationary(so_width, so_height, jamb_w)
    # odd-shaped
    elif types == "4":
        if sub_type == "1": 
            verts, faces = polygon(radius, sides, jamb_w)
        elif sub_type == "2":
            verts, faces = circular(radius, angle, res, jamb_w, is_full_circle)
        elif sub_type == "3":
            verts, faces = arch(so_width, so_height, roundness, res, is_slider, jamb_w)
        elif sub_type == "4":
            verts, faces = gothic(so_width, so_height_tall, res, is_slider, jamb_w)
        elif sub_type == "5":
            verts, faces = oval(so_width, so_height, res, jamb_w)
    elif types == "5":
        verts, faces = bay(ba_width, ba_height, depth, segments, is_split_center, is_double_hung, jamb_w)
    
    return verts, faces, ob_to_join


# update window
def update_window(self, context):
    ob = context.object
    
    verts, faces, ob_to_join = create_window(context, ob.w_types, ob.w_odd_types, ob.w_jamb_width, ob.w_dh_width,
                                             ob.w_dh_height, ob.w_dh_num, ob.w_gl_width, ob.w_gl_height,
                                             ob.w_gl_slide_right, ob.w_so_width, ob.w_so_height, ob.w_so_height_tall,
                                             ob.w_sides, ob.w_o_radius, ob.w_full_circle, ob.w_angle, ob.w_roundness,
                                             ob.w_resolution, ob.w_is_slider, ob.w_ba_width, ob.w_ba_height, ob.w_depth,
                                             ob.w_segments, ob.w_is_split_center, ob.w_is_double_hung)
            
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
    

# general variables
bpy.types.Object.w_types = EnumProperty(items=(("1", "Double-Hung", ""), ("2", "Gliding", ""), ("3", "Stationary", ""),
                                               ("4", "Odd-Shaped", ""), ("5", "Bay", "")), name="",
                                        update=update_window)
bpy.types.Object.w_odd_types = EnumProperty(items=(("1", "Polygon", ""), ("2", "Circular", ""), ("3", "Arch", ""),
                                                   ("4", "Gothic", ""), ("5", "Oval", "")), name="",
                                            update=update_window)
bpy.types.Object.w_object_add = StringProperty(default="none", update=update_window)
bpy.types.Object.w_jamb_width = FloatProperty(name="Jamb Width", subtype="DISTANCE", min=2 / METRIC_INCH,
                                              max=8 / METRIC_INCH, default=4 / METRIC_INCH, update=update_window)

# double hung
bpy.types.Object.w_dh_width = FloatProperty(name="Width", subtype="DISTANCE", min=1 / METRIC_FOOT, max=3 / METRIC_FOOT,
                                            default=32 / METRIC_INCH, update=update_window)
bpy.types.Object.w_dh_height = FloatProperty(name="Height", subtype="DISTANCE", min=1 / METRIC_FOOT,
                                             max=6 / METRIC_FOOT, default=48 / METRIC_INCH, update=update_window)
bpy.types.Object.w_dh_num = IntProperty(name="Number Ganged Together", min=1, max=4, default=1, update=update_window)
# gliding
bpy.types.Object.w_gl_width = FloatProperty(name="Width", subtype="DISTANCE", min=1 / METRIC_FOOT, max=6 / METRIC_FOOT,
                                            default=60 / METRIC_INCH, update=update_window)
bpy.types.Object.w_gl_height = FloatProperty(name="Height", subtype="DISTANCE", min=1 / METRIC_FOOT,
                                             max=4 / METRIC_FOOT, default=36 / METRIC_INCH, update=update_window)
bpy.types.Object.w_gl_slide_right = BoolProperty(name="Slide Right?", default=True, update=update_window)
# stationary & odd-shaped
bpy.types.Object.w_so_width = FloatProperty(name="Width", subtype="DISTANCE", min=1 / METRIC_FOOT, max=6 / METRIC_FOOT,
                                            default=24 / METRIC_INCH, update=update_window)
bpy.types.Object.w_so_height = FloatProperty(name="Height", subtype="DISTANCE", min=1 / METRIC_FOOT,
                                             max=10 / METRIC_FOOT, default=36 / METRIC_INCH, update=update_window)
bpy.types.Object.w_so_height_tall = FloatProperty(name="Height", subtype="DISTANCE", min=3 / METRIC_FOOT,
                                                  max=20 / METRIC_FOOT, default=5 / METRIC_FOOT, update=update_window)
bpy.types.Object.w_o_radius = FloatProperty(name="Radius", subtype="DISTANCE", min=1 / METRIC_FOOT, max=3 / METRIC_FOOT,
                                            default=1.5 / METRIC_FOOT, update=update_window)
# polygon
bpy.types.Object.w_sides = IntProperty(name="Sides", min=3, max=12, default=3, update=update_window)
# circular
bpy.types.Object.w_full_circle = BoolProperty(name="Full Circle?", default=True, update=update_window)
bpy.types.Object.w_angle = FloatProperty(name="Angle", unit="ROTATION", min=radians(45), max=radians(270),
                                         default=radians(90), update=update_window)
# arch
bpy.types.Object.w_roundness = FloatProperty(name="Roundness", subtype="PERCENTAGE", max=100.0, min=1.0, default=25.0,
                                             update=update_window)
bpy.types.Object.w_resolution = IntProperty(name="Resolution", min=32, max=512, default=64, step=2,
                                            update=update_window)
bpy.types.Object.w_is_slider = BoolProperty(name="Slider?", update=update_window)
# bay
bpy.types.Object.w_ba_width = FloatProperty(name="Width", subtype="DISTANCE", min=1 / METRIC_FOOT, max=10 / METRIC_FOOT,
                                            default=72 / METRIC_INCH, update=update_window)
bpy.types.Object.w_ba_height = FloatProperty(name="Height", subtype="DISTANCE", min=1 / METRIC_FOOT,
                                             max=6 / METRIC_FOOT, default=48 / METRIC_INCH, update=update_window)
bpy.types.Object.w_depth = FloatProperty(name="Window Depth", subtype="DISTANCE", min=0.5 / METRIC_FOOT,
                                         max=2 / METRIC_FOOT, default=16 / METRIC_INCH, update=update_window)
bpy.types.Object.w_segments = IntProperty(name="Segments", min=3, max=8, default=3, update=update_window)
bpy.types.Object.w_is_split_center = BoolProperty(name="Split Center Pane?", default=False, update=update_window)
bpy.types.Object.w_is_double_hung = BoolProperty(name="Double Hung?", default=True, update=update_window)


class WindowMaterials(bpy.types.Operator):
    bl_idname = "mesh.jarch_window_materials"
    bl_label = "Generate\\Update Materials"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):      
        return {"FINISHED", "INTERNAL"}


class WindowPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_jarch_window"
    bl_label = "JARCH Vis: Window"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "JARCH Vis"

    def draw(self, context):
        layout = self.layout
        if bpy.context.mode == "EDIT_MESH":
            layout.label("JARCH Vis Doesn't Work In Edit Mode", icon="ERROR")
        else:
            o = context.object
            if o is not None and o.w_object_add == "add":
                layout.label("Window Type:")
                layout.prop(o, "w_types", icon="OBJECT_DATAMODE")
                
                if o.w_types == "4":
                    layout.label("Shape:")
                    layout.prop(o, "w_odd_types", icon="SPACE2")
                    
                # parameters
                if o.w_types != "5":
                    layout.separator()
                    layout.prop(o, "w_jamb_width")
                    
                # double hung
                layout.separator()
                if o.w_types == "1":
                    layout.prop(o, "w_dh_width")
                    layout.prop(o, "w_dh_height")
                    layout.prop(o, "w_dh_num")
                # gliding
                elif o.w_types == "2":
                    layout.prop(o, "w_gl_width")
                    layout.prop(o, "w_gl_height")
                    layout.prop(o, "w_gl_slide_right", icon="FORWARD")
                # stationary 
                elif o.w_types == "3":
                    layout.prop(o, "w_so_width")
                    layout.prop(o, "w_so_height")
                # odd-shaped
                elif o.w_types == "4":
                    # polygon
                    if o.w_odd_types == "1":
                        layout.prop(o, "w_o_radius")
                        layout.prop(o, "w_sides")
                    # circular
                    elif o.w_odd_types == "2":
                        layout.prop(o, "w_o_radius")
                        layout.prop(o, "w_resolution")
                        layout.prop(o, "w_full_circle", icon="MESH_CIRCLE")
                        if not o.w_full_circle:
                            layout.prop(o, "w_angle")
                    
                    else:
                        layout.prop(o, "w_so_width")
                        
                        if o.w_odd_types == "4":  # gothic
                            layout.prop(o, "w_so_height_tall")                                
                            layout.prop(o, "w_is_slider", icon="SETTINGS")
                        else:
                            layout.prop(o, "w_so_height")
                            
                        layout.separator()                    
                        layout.prop(o, "w_resolution")
                        
                        # arch
                        if o.w_odd_types == "3":
                            layout.prop(o, "w_roundness")                            
                            layout.prop(o, "w_is_slider", icon="SETTINGS")
                            
                # bay
                elif o.w_types == "5":
                    layout.prop(o, "w_ba_width")
                    layout.prop(o, "w_ba_height")
                    layout.prop(o, "w_segments")                    
                    layout.separator()
                    
                    if o.w_segments % 2 != 0:
                        layout.prop(o, "w_depth")  
                        layout.prop(o, "w_is_split_center", icon="PAUSE")
                        layout.separator()
                    
                    layout.prop(o, "w_is_double_hung", icon="SPLITSCREEN")
                                              
                # operators
                layout.separator()
                layout.separator()
                layout.operator("mesh.jarch_window_update", icon="FILE_REFRESH")
                layout.operator("mesh.jarch_window_delete", icon="CANCEL")
            
            else:
                layout.operator("mesh.jarch_window_add", icon="OUTLINER_OB_LATTICE")


class WindowAdd(bpy.types.Operator):
    bl_idname = "mesh.jarch_window_add"
    bl_label = "JARCH Vis: Add Window"
    bl_description = "JARCH Vis: Window Generator"
    
    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        o = context.object
        o.w_object_add = "add"            
        return {"FINISHED"}


class WindowUpdate(bpy.types.Operator):
    bl_idname = "mesh.jarch_window_update"
    bl_label = "Update Window"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        update_window(self, context)
        return {"FINISHED"}


# TODO: not completed
class WindowMesh(bpy.types.Operator):
    bl_idname = "mesh.jarch_window_mesh"
    bl_label = "Convert To Mesh"
    bl_description = "Converts Window Object To Normal Object (No Longer Editable)"
    bl_options = {"UNDO", "INTERNAL"}
    
    def execute(self, context):
        return {"FINISHED"}


class WindowDelete(bpy.types.Operator):
    bl_idname = "mesh.jarch_window_delete"
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
