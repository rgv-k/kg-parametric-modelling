```python
import bpy
import math
def create_component(name, segments, order):
    bpy.ops.mesh.primitive_cube_add()
    component = bpy.context.active_object
    component.name = name
    base_size = 2.0
    total_height = sum([seg["size"] for seg in segments])
    component.scale.x = base_size
    component.scale.y = base_size
    component.scale.z = total_height
    component.location.z = order * total_height
    if "roof" in name.lower() or "prastara" in name.lower():
        component.scale.x = base_size * 1.2
        component.scale.y = base_size * 1.2
        component.scale.z = total_height * 0.3  # Low height
    return component
def main():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    PROFILE = [
        {
            "name": "chada",
            "order": 1,
            "segments": [
                {"type": "taper", "size": 1.0}
            ]
        },
        {
            "name": "kapota",
            "order": 2,
            "segments": [
                {"type": "extrusion", "size": 0.5},
                {"type": "sigmoid", "size": 0.5}
            ]
        },
        {
            "name": "puṣkara",
            "order": 3,
            "segments": [
                {"type": "arc", "size": 1.0}
            ]
        },
        {
            "name": "lupākārya",
            "order": 4,
            "segments": [
                {"type": "line", "size": 0.5},
                {"type": "arc", "size": 0.5}
            ]
        },
        {
            "name": "shikhara",
            "order": 5,
            "segments": [
                {"type": "taper", "size": 1.0}
            ]
        },
        {
            "name": "munda",
            "order": 6,
            "segments": [
                {"type": "circle_segment", "size": 1.0}
            ]
        },
        {
            "name": "anuvamsa",
            "order": 7,
            "segments": [
                {"type": "line", "size": 0.5},
                {"type": "sigmoid", "size": 0.5}
            ]
        },
        {
            "name": "urdhvavamsa",
            "order": 8,
            "segments": [
                {"type": "extrusion", "size": 1.0}
            ]
        }
    ]
    for component_data in PROFILE:
        name = component_data["name"]
        order = component_data["order"]
        segments = component_data["segments"]
        segment_total = 0
        for seg in segments:
            segment_total += seg["size"]
        create_component(name, segments, order)
if __name__ == "__main__":
    main()
```