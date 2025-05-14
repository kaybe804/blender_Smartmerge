bl_info = {
    "name": "Smart Merge",
    "author": "kaybe & OpenAI",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "description": "Merges vertices by distance, providing an option to revert the merge to get the original topology back.",
    "category": "Object",
}

import bpy
import bmesh
import json
from mathutils.kdtree import KDTree

MERGE_TAG = "_smart_merge_topo_data"

def store_merge_data(obj, mapping, original_coords, original_faces):
    obj[MERGE_TAG] = json.dumps({
        "mapping": mapping,
        "original_coords": original_coords,
        "original_faces": original_faces
    })

def load_merge_data(obj):
    if MERGE_TAG not in obj:
        return None
    return json.loads(obj[MERGE_TAG])

def smart_merge_topo(obj, threshold=0.0001):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    original_coords = [list(v.co) for v in bm.verts]
    original_faces = [[v.index for v in f.verts] for f in bm.faces]

    total = len(bm.verts)
    tree = KDTree(total)
    for i, v in enumerate(bm.verts):
        tree.insert(v.co, i)
    tree.balance()

    visited = set()
    groups = []
    for i, v in enumerate(bm.verts):
        if i in visited:
            continue
        close = tree.find_range(v.co, threshold)
        indices = list(set(idx for (_, idx, _) in close))
        for idx in indices:
            visited.add(idx)
        groups.append(indices)

    merge_map = {}
    for group in groups:
        keeper = group[0]
        for idx in group:
            merge_map[str(idx)] = keeper

    # Rebuild mesh with merged verts
    new_verts = []
    idx_map = {}
    keeper_set = set(int(v) for v in merge_map.values())
    for i in range(len(original_coords)):
        if i in keeper_set:
            idx_map[i] = len(new_verts)
            new_verts.append(original_coords[i])

    for i in range(len(original_coords)):
        merge_to = int(merge_map[str(i)])
        if merge_to not in idx_map:
            print(f"Warning: Missing keeper for vertex {i} -> {merge_to}")
            continue
        idx_map[i] = idx_map[merge_to]


    # Reconstruct new face indices
    new_faces = []
    for face in original_faces:
        new_face = [idx_map[i] for i in face]
        if len(set(new_face)) == len(new_face):  # skip degenerate
            new_faces.append(new_face)

    # Replace original mesh data
    bm.free()
    new_mesh = bpy.data.meshes.new(obj.name + "_merged")
    new_mesh.from_pydata(new_verts, [], new_faces)
    new_mesh.update()
    obj.data = new_mesh

    store_merge_data(obj, idx_map, original_coords, original_faces)
    print("Smart merge successful.")

def smart_restore_topo(obj):
    data = load_merge_data(obj)
    if not data:
        print("No smart merge data found.")
        return

    mapping = data["mapping"]
    original_coords = data["original_coords"]
    original_faces = data["original_faces"]

    current_positions = [v.co.copy() for v in obj.data.vertices]
    restored_coords = []

    for i in range(len(original_coords)):
        mapped = mapping[str(i)]
        restored_coords.append(current_positions[mapped])

    mesh = bpy.data.meshes.new(obj.name + "_restored")
    mesh.from_pydata(restored_coords, [], original_faces)
    mesh.update()

    new_obj = bpy.data.objects.new(obj.name + "_restored", mesh)
    bpy.context.collection.objects.link(new_obj)

    print("Smart restore complete.")

class OBJECT_OT_SmartMergeTopo(bpy.types.Operator):
    bl_idname = "object.smart_merge_topo"
    bl_label = "Smart Merge"
    bl_options = {'REGISTER', 'UNDO'}

    threshold: bpy.props.FloatProperty(name="Distance", default=0.0001, min=0.000001)

    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            smart_merge_topo(obj, self.threshold)
            return {'FINISHED'}
        return {'CANCELLED'}

class OBJECT_OT_SmartRestoreTopo(bpy.types.Operator):
    bl_idname = "object.smart_restore_topo"
    bl_label = "Smart Restore"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            smart_restore_topo(obj)
            return {'FINISHED'}
        return {'CANCELLED'}

class VIEW3D_PT_SmartMergeTopoPanel(bpy.types.Panel):
    bl_label = "Smart Merge (Topological)"
    bl_idname = "VIEW3D_PT_smart_merge_topo_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Smart Merge'

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        if obj and obj.type == 'MESH':
            layout.operator("object.smart_merge_topo")
            layout.operator("object.smart_restore_topo")
        else:
            layout.label(text="Select a mesh object.")

def register():
    bpy.utils.register_class(OBJECT_OT_SmartMergeTopo)
    bpy.utils.register_class(OBJECT_OT_SmartRestoreTopo)
    bpy.utils.register_class(VIEW3D_PT_SmartMergeTopoPanel)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_SmartMergeTopo)
    bpy.utils.unregister_class(OBJECT_OT_SmartRestoreTopo)
    bpy.utils.unregister_class(VIEW3D_PT_SmartMergeTopoPanel)

if __name__ == "__main__":
    register()
