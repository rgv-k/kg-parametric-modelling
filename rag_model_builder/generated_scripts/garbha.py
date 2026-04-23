```python
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
profile_data = {
    "component": "garbha",
    "profile": [
        {"name": "adhiṣṭhāna", "order": 1, "segments": [{"type": "rectangle", "size": 1.0}]},
        {"name": "pīṭha", "order": 2, "segments": [{"type": "taper", "size": 0.5}, {"type": "rectangle", "size": 0.5}]},
        {"name": "bhitti", "order": 3, "segments": [{"type": "line", "size": 0.333}, {"type": "line", "size": 0.667}]},
        {"name": "prastara", "order": 4, "segments": [{"type": "rectangle", "size": 1.0}]},
        {"name": "śikhara", "order": 5, "segments": [{"type": "arc", "size": 0.5}, {"type": "line", "size": 0.5}]},
        {"name": "liṅga", "order": 6, "segments": [{"type": "circle_segment", "size": 0.5}, {"type": "line", "size": 0.5}]},
        {"name": "ajasūtra", "order": 7, "segments": [{"type": "line", "size": 1.0}]},
        {"name": "mekhalā", "order": 8, "segments": [{"type": "rectangle", "size": 1.0}]}
    ]
}
total_height = 0.0
for component in profile_data["profile"]:
    for segment in component["segments"]:
        total_height += segment["size"]
component_proportions = {}
for component in profile_data["profile"]:
    component_height = sum(segment["size"] for segment in component["segments"])
    component_proportions[component["name"]] = component_height / total_height
current_height = 0.0
base_scale = 2.0  # Wider base scale factor
mid_scale = 1.5   # Intermediate scale
top_scale = 0.8   # Smaller top scale
for component in profile_data["profile"]:
    name = component["name"]
    proportion = component_proportions[name]
    height = proportion * total_height
    if name == "adhiṣṭhāna" or name == "pīṭha" or name == "base":
        bpy.ops.mesh.primitive_cube_add(size=1)
        obj = bpy.context.object
        obj.scale = (base_scale, base_scale, height)
        obj.location.z = current_height + height/2
        obj.name = name
    elif name == "bhitti":
        bpy.ops.mesh.primitive_cube_add(size=1)
        obj = bpy.context.object
        obj.scale = (mid_scale, mid_scale, height)
        obj.location.z = current_height + height/2
        obj.name = name
    elif name == "śikhara":
        bpy.ops.mesh.primitive_cube_add(size=1)
        obj = bpy.context.object
        taper_factor = 0.85
        obj.scale = (top_scale * taper_factor, top_scale * taper_factor, height)
        obj.location.z = current_height + height/2
        obj.name = name
    elif name == "liṅga":
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.5, depth=height)
        obj = bpy.context.object
        obj.scale = (top_scale, top_scale, 1)
        obj.location.z = current_height + height/2
        obj.name = name
    else:
        bpy.ops.mesh.primitive_cube_add(size=1)
        obj = bpy.context.object
        varied_scale = 1.2 + (component["order"] * 0.1)
        obj.scale = (varied_scale, varied_scale, height)
        obj.location.z = current_height + height/2
        obj.name = name
    current_height += height
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        import random
        obj.scale.x *= (1 + random.uniform(-0.05, 0.05))
        obj.scale.y *= (1 + random.uniform(-0.05, 0.05))
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'SOLID'
```