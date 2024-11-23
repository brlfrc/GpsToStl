import bpy  # type: ignore
import sys

# Clear all existing objects in the scene
bpy.ops.object.select_all(action='SELECT')  # Select all objects
bpy.ops.object.delete()

input_stl_path_1 = sys.argv[-5]  # Text mesh path
input_stl_path_2 = sys.argv[-4]  # Uphill mesh path
cube_path = sys.argv[-3]  # Cube mesh path
magnet_holder_path = sys.argv[-2]  # Magnet holder mesh path
output_stl_path = sys.argv[-1]  # Output STL file path

# Import the STL files into the scene
bpy.ops.import_mesh.stl(filepath=input_stl_path_1)
text_mesh = bpy.context.view_layer.objects.active

bpy.ops.import_mesh.stl(filepath=input_stl_path_2)
uphill_mesh = bpy.context.view_layer.objects.active

# Import the Cube and Magnet Holder meshes
bpy.ops.import_mesh.stl(filepath=cube_path)
cube_mesh = bpy.context.view_layer.objects.active

bpy.ops.import_mesh.stl(filepath=magnet_holder_path)
magnet_holder_mesh = bpy.context.view_layer.objects.active



# Ensure both meshes are correctly imported
if text_mesh and uphill_mesh:
    
    # ---- Align Cube and Magnet Holder Meshes ----
    # Calculate Z-minimums
    cube_min_z = min((cube_mesh.matrix_world @ v.co).z for v in cube_mesh.data.vertices)
    uphill_min_z = min((uphill_mesh.matrix_world @ v.co).z for v in uphill_mesh.data.vertices)
    magnet_holder_min_z = min((magnet_holder_mesh.matrix_world @ v.co).z for v in magnet_holder_mesh.data.vertices)

    # Translate cube and magnet holder meshes to align Z-minimums
    cube_mesh.location[2] += uphill_min_z - cube_min_z
    magnet_holder_mesh.location[2] += uphill_min_z - magnet_holder_min_z
    bpy.context.view_layer.update()

    # Calculate Y-max for cube and Y-min for uphill
    cube_max_y = max((cube_mesh.matrix_world @ v.co).y for v in cube_mesh.data.vertices)
    uphill_min_y = min((uphill_mesh.matrix_world @ v.co).y for v in uphill_mesh.data.vertices)

    # Translate cube along Y-axis
    cube_mesh.location[1] += uphill_min_y - cube_max_y + 0.1
    bpy.context.view_layer.update()

    # Calculate Y-max for magnet holder and Y-min for cube
    magnet_holder_max_y = max((magnet_holder_mesh.matrix_world @ v.co).y for v in magnet_holder_mesh.data.vertices)
    cube_min_y = min((cube_mesh.matrix_world @ v.co).y for v in cube_mesh.data.vertices)

    # Translate magnet holder along Y-axis
    magnet_holder_mesh.location[1] += cube_min_y - magnet_holder_max_y
    bpy.context.view_layer.update()
    
     
    shrinkwrap = cube_mesh.modifiers.new(name="Shrinkwrap", type='SHRINKWRAP')
    shrinkwrap.target = uphill_mesh
    shrinkwrap.wrap_method = 'PROJECT'
    shrinkwrap.use_negative_direction = False
    shrinkwrap.use_positive_direction = True

    # ---- Translate Original Mesh and Duplicate with Adjustments ----
    x_translation = 0.4 * (max((uphill_mesh.matrix_world @ v.co).x for v in uphill_mesh.data.vertices) -
                       min((uphill_mesh.matrix_world @ v.co).x for v in uphill_mesh.data.vertices))

    
    # Move the original cube mesh by x_translation
    bpy.ops.object.select_all(action='DESELECT')  # Deselect all objects
    cube_mesh.select_set(True)  # Select the original cube mesh
    cube_mesh.location[0] += x_translation  # Translate the original cube mesh by x_translation
    cube_mesh.modifiers["Shrinkwrap"].subsurf_levels = 6
    
    # Duplicate the original cube mesh
    bpy.ops.object.duplicate()  

    # Get the newly duplicated object (it will be the active object after the duplication)
    cube_copy = bpy.context.view_layer.objects.selected[-1]

    # Explicitly select and set the duplicated object as active
    cube_copy.select_set(True)  # Select the duplicated object
    bpy.context.view_layer.objects.active = cube_copy  # Set the duplicated object as the active object

    # Now you can apply transformations to the duplicated object
    cube_copy.location[0] -= 2 * x_translation  # Translate the duplicate by -2 * x_translation
    cube_copy.modifiers["Shrinkwrap"].subsurf_levels = 6

    
    bpy.context.view_layer.update()  # Update the scene
    
       
    # Repeat the same process for the magnet holder mesh
    bpy.ops.object.select_all(action='DESELECT')  # Deselect all objects
    magnet_holder_mesh.select_set(True)  # Select the original magnet holder mesh
    magnet_holder_mesh.location[0] += x_translation  # Translate the original magnet holder mesh by x_translation
    
    # Duplicate the magnet holder mesh and translate the duplicate by -2 * x_translation
    bpy.ops.object.duplicate()  # Duplicate the selected (now translated) magnet holder mesh
    magnet_copy = bpy.context.view_layer.objects.selected[-1]  # Get the duplicated magnet holder mesh
    magnet_copy.location[0] -= 2*x_translation  # Translate the duplicate by -2 * x_translation
    bpy.context.view_layer.update()  # Update the scene
    
    
    
    # ---- Text Mesh Operations ----
    # Calculate min and max Y-coordinates
    text_mesh_min_z = min((text_mesh.matrix_world @ v.co).z for v in text_mesh.data.vertices)
    uphill_min_z = min((uphill_mesh.matrix_world @ v.co).z for v in uphill_mesh.data.vertices)

    # Translate text mesh along Y-Z-axis
    text_mesh.location[2] += uphill_min_z - text_mesh_min_z

    bpy.context.view_layer.update()

    # Scale the text mesh along the Y-axis
    target_x_text = 2*x_translation - 15
    
    text_mesh.scale[0] = target_x_text / text_mesh.dimensions.x

    # Force scene update after scaling
    bpy.context.view_layer.update()

    # 2. Apply a Boolean modifier to subtract the text_mesh from uphill_mesh
    # First, create a new Boolean modifier for the uphill_mesh object
    boolean_modifier = uphill_mesh.modifiers.new(name="Boolean", type='BOOLEAN')
    boolean_modifier.operation = 'DIFFERENCE'  # Set the operation type to "Difference"
    boolean_modifier.use_self = True  # Allow the modifier to interact with the object itself
    boolean_modifier.object = text_mesh  # Set the text_mesh as the target object for the operation

    # 3. Apply the Boolean modifier
    bpy.context.view_layer.objects.active = uphill_mesh
    bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
    
    bpy.ops.object.duplicate(linked=False) 

    # 5. Remove the text_mesh object after the operation is applied
    # The text_mesh is no longer needed, so we can safely delete it
    bpy.data.objects.remove(text_mesh, do_unlink=True)


    # 5. Force a final scene update
    # This step ensures the scene updates properly after the changes
    bpy.context.view_layer.update()

    
    # ---- Export the Final Mesh ----
    bpy.context.view_layer.objects.active = uphill_mesh
    bpy.ops.export_mesh.stl(filepath=output_stl_path)
    print(f"STL file saved to: {output_stl_path}")