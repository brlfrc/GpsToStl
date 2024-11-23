import bpy # type: ignore
import sys
import os

# Get the input STL file path (passed as command-line argument)
input_stl_path = sys.argv[-1]

# Clear all existing objects in the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Import the STL file into the scene
bpy.ops.import_mesh.stl(filepath=input_stl_path)
imported_mesh = bpy.context.view_layer.objects.active  # The last imported object is active

# Make sure the mesh exists
if imported_mesh:
    # Add the Solidify modifier
    solidify_modifier = imported_mesh.modifiers.new(name="Solidify", type='SOLIDIFY')
    solidify_modifier.thickness = 2.5  # Set the thickness to 2.5
    solidify_modifier.offset = 0  # Set the offset to 0
    solidify_modifier.use_rim = True  # Enable rim fill (rim will be filled)
    
    # Apply the Solidify modifier
    bpy.ops.object.modifier_apply(modifier=solidify_modifier.name)

    # Export the modified mesh to the same path
    bpy.ops.export_mesh.stl(filepath=input_stl_path)
    print(f"Modified mesh saved to: {input_stl_path}")

else:
    print("The mesh could not be imported.")
