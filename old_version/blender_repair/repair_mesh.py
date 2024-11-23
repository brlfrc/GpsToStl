import bpy # type: ignore
import sys

# Clear all existing objects in the scene
bpy.ops.object.select_all(action='SELECT')  # Select all objects
bpy.ops.object.delete()  # Delete selected objects

# Retrieve input and output paths from command-line arguments
input_stl_path = sys.argv[-2]
output_stl_path = sys.argv[-1]

bpy.ops.import_mesh.stl(filepath=input_stl_path)
obj = bpy.context.active_object

bpy.ops.object.mode_set(mode='EDIT')

bpy.ops.mesh.select_all(action='DESELECT')

bpy.ops.mesh.select_non_manifold()

bpy.ops.mesh.edge_collapse()

bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.mesh.select_non_manifold()

bpy.ops.mesh.edge_face_add() 

# Step 3: Recalculate normals to ensure correct orientation
bpy.ops.mesh.select_all(action='SELECT')  # Select all elements
bpy.ops.mesh.normals_make_consistent(inside=False)  # Recalculate normals

# Step 4: Remove duplicate vertices to clean up the mesh
bpy.ops.mesh.remove_doubles(threshold=0.0001)  # Merge nearby vertices

# Step 5: Check for and remove any isolated vertices
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.mesh.select_loose()  # Select any loose geometry
bpy.ops.mesh.delete(type='VERT')  # Delete isolated vertices



bpy.ops.object.mode_set(mode='OBJECT')

bpy.ops.export_mesh.stl(filepath=output_stl_path)
print(f"Modello riparato e salvato in: {output_stl_path}")

