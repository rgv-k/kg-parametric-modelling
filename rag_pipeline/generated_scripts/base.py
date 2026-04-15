```python
import bpy
import math
import json
from mathutils import Vector

PROFILE = {
  "component": "base",
  "profile": [
    {
      "name": "upana",
      "order": 1,
      "segments": [
        {
          "type": "rectangle",
          "size": 0.1389
        }
      ]
    },
    {
      "name": "kumuda",
      "order": 2,
      "segments": [
        {
          "type": "taper",
          "size": 0.1667
        }
      ]
    },
    {
      "name": "kantha",
      "order": 3,
      "segments": [
        {
          "type": "rectangle",
          "size": 0.125
        }
      ]
    },
    {
      "name": "kampa",
      "order": 4,
      "segments": [
        {
          "type": "sigmoid",
          "size": 0.0417
        }
      ]
    },
    {
      "name": "pattika",
      "order": 5,
      "segments": [
        {
          "type": "taper",
          "size": 0.125
        }
      ]
    },
    {
      "name": "ksepana",
      "order": 6,
      "segments": [
        {
          "type": "rectangle",
          "size": 0.2308
        }
      ]
    }
  ]
}

def smooth_interp(t, r1, r2):
    return r1 + (r2 - r1) * (3 * t * t - 2 * t * t * t)

def create_base_profile():
    vertices = []
    faces = []
    z = 0.0
    prev_radius = 1.0
    current_radius = 1.0
    
    base_radius = 2.0
    resolution = 32
    
    for section in PROFILE["profile"]:
        for seg in section["segments"]:
            seg_type = seg["type"]
            h = seg["size"]
            
            if seg_type == "rectangle":
                vertices.append((base_radius * prev_radius, 0, z))
                vertices.append((base_radius * prev_radius, 0, z + h))
                current_radius = prev_radius
                z += h
                
            elif seg_type == "taper":
                steps = 8
                for i in range(steps + 1):
                    t = i / steps
                    current_z = z + t * h
                    r = smooth_interp(t, prev_radius, prev_radius * 0.8)
                    vertices.append((base_radius * r, 0, current_z))
                current_radius = prev_radius * 0.8
                z += h
                
            elif seg_type == "sigmoid":
                steps = 8
                for i in range(steps + 1):
                    t = i / steps
                    current_z = z + t * h
                    r = smooth_interp(t, prev_radius, prev_radius * 1.1)
                    vertices.append((base_radius * r, 0, current_z))
                current_radius = prev_radius * 1.1
                z += h
                
            prev_radius = current_radius
    
    profile_curve = bpy.data.curves.new('BaseProfile', type='CURVE')
    profile_curve.dimensions = '3D'
    profile_curve.resolution_u = 2
    
    polyline = profile_curve.splines.new('POLY')
    polyline.points.add(len(vertices) - 1)
    
    for i, coord in enumerate(vertices):
        x, y, z = coord
        polyline.points[i].co = (x, y, z, 1)
    
    profile_obj = bpy.data.objects.new('BaseProfile', profile_curve)
    bpy.context.collection.objects.link(profile_obj)
    
    return profile_obj, vertices

def revolve_profile(vertices):
    mesh = bpy.data.meshes.new('BaseMesh')
    obj = bpy.data.objects.new('Base', mesh)
    bpy.context.collection.objects.link(obj)
    
    rev_vertices = []
    rev_faces = []
    
    steps = 32
    angle_step = 2 * math.pi / steps
    
    for i, vert in enumerate(vertices):
        x, y, z = vert
        for j in range(steps):
            angle = j * angle_step
            nx = x * math.cos(angle)
            ny = x * math.sin(angle)
            rev_vertices.append((nx, ny, z))
    
    for i in range(len(vertices) - 1):
        for j in range(steps):
            next_j = (j + 1) % steps
            v1 = i * steps + j
            v2 = i * steps + next_j
            v3 = (i + 1) * steps + next_j
            v4 = (i + 1) * steps + j
            rev_faces.append([v1, v2, v3, v4])
    
    mesh.from_pydata(rev_vertices, [], rev_faces)
    mesh.update()
    
    return obj

def main():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    profile_obj, vertices = create_base_profile()
    base_obj = revolve_profile(vertices)
    
    bpy.data.objects.remove(profile_obj, do_unlink=True)
    
    bpy.context.view_layer.objects.active = base_obj
    base_obj.select_set(True)
    
    bpy.ops.object.shade_smooth()
    
    bpy.ops.object.modifier_add(type='SOLIDIFY')
    base_obj.modifiers["Solidify"].thickness = 0.1
    
    bpy.ops.object.modifier_add(type='BEVEL')
    base_obj.modifiers["Bevel"].width = 0.02
    base_obj.modifiers["Bevel"].segments = 2
    
    base_obj.location = (0, 0, 0)
    base_obj.scale = (1, 1, 1)

if __name__ == "__main__":
    main()
```