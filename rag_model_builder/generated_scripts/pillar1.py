import bpy
import math
profile = [
    ("rectangle", 0.125),
    ("taper", 0.1),
    ("arc", 0.0625), ("arc", 0.0625),
    ("rectangle", 0.3),
    ("arc", 0.0375), ("arc", 0.0375),
    ("extrusion", 0.075),
    ("rectangle", 0.1),
    ("rectangle", 0.05),
    ("circle_segment", 0.025), ("circle_segment", 0.025)
]
pillar_height = 10
base_radius = 1
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
curve_data = bpy.data.curves.new(name='ProfileCurve', type='CURVE')
curve_data.dimensions = '3D'
spline = curve_data.splines.new('BEZIER')
points = []
z = 0
r = base_radius
for seg_type, size in profile:
    h = size * pillar_height
    if seg_type == "rectangle":
        points.append((r, 0, z))
        z += h
        points.append((r, 0, z))
    elif seg_type == "taper":
        points.append((r, 0, z))
        r *= 0.8
        z += h
        points.append((r, 0, z))
    elif seg_type == "arc":
        mid_z = z + h / 2
        points.append((r, 0, z))
        points.append((r + 0.3, 0, mid_z))  # control bulge
        z += h
        points.append((r, 0, z))
    elif seg_type == "circle_segment":
        mid_z = z + h / 2
        points.append((r, 0, z))
        points.append((r + 0.2, 0, mid_z))
        z += h
        points.append((r, 0, z))
    elif seg_type == "extrusion":
        points.append((r, 0, z))
        r *= 1.2
        z += h
        points.append((r, 0, z))
spline.bezier_points.add(len(points) - 1)
for i, (x, y, z) in enumerate(points):
    bp = spline.bezier_points[i]
    bp.co = (x, y, z)
    bp.handle_left_type = 'AUTO'
    bp.handle_right_type = 'AUTO'
curve_obj = bpy.data.objects.new("Profile", curve_data)
bpy.context.collection.objects.link(curve_obj)
bpy.context.view_layer.objects.active = curve_obj
curve_obj.select_set(True)
bpy.ops.object.convert(target='MESH')
obj = bpy.context.active_object
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.spin(
    steps=128,
    angle=2 * math.pi,
    axis=(0, 0, 1),
    center=(0, 0, 0)
)
bpy.ops.object.mode_set(mode='OBJECT')
print(" High-quality pillar generated with Bezier profile")