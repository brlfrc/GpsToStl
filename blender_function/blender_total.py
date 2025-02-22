import bpy  # type: ignore
import bmesh # type: ignore
import json
import sys

################################################
#           Reading the input file
################################################
config_file_path = sys.argv[-1]
with open(config_file_path, "r") as file:
    config = json.load(file)

# Uphill mesh
thickness = config["thickness"]
points_file_path = config["points_file_path"]
uphill_stl_path = config["uphill_stl_path"]

# Text mesh
text_input = config["text_input"]
font_path = config["font_path"]
text_stl_path = config["text_stl_path"]

# diff mesh
diff_stl_path = config["diff_stl_path"]

cube_path = config["cube_path"]
magnet_holder_path = config["magnet_holder_path"]


################################################
#           Creation of the Uphill mesh
################################################
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

points = []
with open(points_file_path, 'r') as file:
    lines = file.readlines()
    
    for line in lines:
        if line.startswith("#"):
            continue
        
        line = line.strip()
        if line: 
            for point in line.split(';'):
                if point.strip():
                    x, y, z = map(float, point.split(','))
                    points.append([x, y, z])

if points:
    max_x = max(point[0] for point in points)
    min_x = min(point[0] for point in points)
    max_y = max(point[1] for point in points)
    min_y = min(point[1] for point in points)
    min_z = min(point[2] for point in points)
    
    center_x = (max_x + min_x) / 2
    center_y = (max_y + min_y) / 2
    
    for point in points:
        point[0] -= center_x
        point[1] -= center_y
        
mesh = bpy.data.meshes.new("Uphill_Mesh")
obj = bpy.data.objects.new("Uphill", mesh)

bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bm = bmesh.new()
base_vertices = []
top_vertices = []

for x, y, z in points:
    base_vertex = bm.verts.new((x, y, 0))
    base_vertices.append(base_vertex)
    
    top_vertex = bm.verts.new((x, y, z))
    top_vertices.append(top_vertex)

bm.verts.ensure_lookup_table()

for i in range(len(points) - 1): 
    v1 = base_vertices[i]
    v2 = top_vertices[i]
    v3 = top_vertices[i + 1]
    v4 = base_vertices[i + 1]

    bm.faces.new([v1, v2, v3, v4])

for face in bm.faces:
    face.normal_flip() if face.normal.z < 0 else None
    
bm.to_mesh(mesh)
bm.free()

solidify_modifier = obj.modifiers.new(name="ThicknessModifier", type='SOLIDIFY')
solidify_modifier.thickness = thickness
solidify_modifier.offset = 0

decimate_modifier = obj.modifiers.new(name="Decimate", type='DECIMATE')
decimate_modifier.decimate_type = 'COLLAPSE'

decimate_modifier.ratio = 0.05

bpy.ops.object.modifier_apply(modifier=decimate_modifier.name)


bpy.context.view_layer.update()

bpy.ops.export_mesh.stl(filepath=uphill_stl_path)

print(f"Uphill mesh has been saved to {uphill_stl_path}")


################################################
#           Creation of the Text mesh
################################################
if text_input.strip():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    bpy.ops.object.text_add(location=(0, 0, 0))
    text_obj = bpy.context.active_object
    text_obj.data.body = text_input

    font = bpy.data.fonts.load(font_path)
    text_obj.data.font = font

    text_obj.data.extrude = 0.2
    text_obj.data.offset = 0

    text_obj.rotation_euler[0] = 1.5708  # 90 degrees in radians
    text_obj.rotation_euler[2] += 3.14159 

    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    # Scaling to the desired dimensions using the dimension of the uphill
    desired_x = max_x-min_x
    desired_y = 3.0
    desired_z = min_z

    # Calculate the current bounding box size of the mesh
    mesh = text_obj.data
    min_coords = [min(v.co[i] for v in mesh.vertices) for i in range(3)]
    max_coords = [max(v.co[i] for v in mesh.vertices) for i in range(3)]
    current_x = max_coords[0] - min_coords[0]
    current_y = max_coords[1] - min_coords[1]
    current_z = max_coords[2] - min_coords[2]
    scale_x = desired_x / current_x
    scale_y = desired_y / current_y
    scale_z = desired_z / current_z
    text_obj.scale = (scale_x, scale_y, scale_z)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    min_coords = [min(v.co[i] for v in mesh.vertices) for i in range(3)]
    max_coords = [max(v.co[i] for v in mesh.vertices) for i in range(3)]
    center_x = (min_coords[0] + max_coords[0]) / 2
    center_y = (min_coords[1] + max_coords[1]) / 2
    text_obj.location.x -= center_x
    text_obj.location.y -= center_y

    bpy.ops.export_mesh.stl(filepath=text_stl_path)
    print(f"Text mesh has been saved to {text_stl_path}")

################################################
#           Difference Mesh
################################################
bpy.ops.object.select_all(action='SELECT')  # Select all objects
bpy.ops.object.delete()

if text_input.strip():
    bpy.ops.import_mesh.stl(filepath=text_stl_path)
    text_mesh = bpy.context.view_layer.objects.active
    
bpy.ops.import_mesh.stl(filepath=uphill_stl_path)
uphill_mesh = bpy.context.view_layer.objects.active
bpy.ops.import_mesh.stl(filepath=cube_path)
cube_mesh = bpy.context.view_layer.objects.active
bpy.ops.import_mesh.stl(filepath=magnet_holder_path)
magnet_holder_mesh = bpy.context.view_layer.objects.active



# Ensure both meshes are correctly imported
if uphill_mesh:
    
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

    
    bpy.ops.object.select_all(action='DESELECT')  # Deselect all objects
    cube_mesh.select_set(True)  # Select the original cube mesh
    cube_mesh.location[0] += x_translation  # Translate the original cube mesh by x_translation
    cube_mesh.modifiers["Shrinkwrap"].subsurf_levels = 6
    
    bpy.ops.object.duplicate()  

    cube_copy = bpy.context.view_layer.objects.selected[-1]

    cube_copy.select_set(True)  # Select the duplicated object
    bpy.context.view_layer.objects.active = cube_copy  # Set the duplicated object as the active object

    cube_copy.location[0] -= 2 * x_translation  # Translate the duplicate by -2 * x_translation
    cube_copy.modifiers["Shrinkwrap"].subsurf_levels = 6

    
    bpy.context.view_layer.update()  # Update the scene
    
       
    bpy.ops.object.select_all(action='DESELECT')  # Deselect all objects
    magnet_holder_mesh.select_set(True)  # Select the original magnet holder mesh
    magnet_holder_mesh.location[0] += x_translation  # Translate the original magnet holder mesh by x_translation
    
    bpy.ops.object.duplicate()  # Duplicate the selected (now translated) magnet holder mesh
    magnet_copy = bpy.context.view_layer.objects.selected[-1]  # Get the duplicated magnet holder mesh
    magnet_copy.location[0] -= 2*x_translation  # Translate the duplicate by -2 * x_translation
    bpy.context.view_layer.update()  # Update the scene
    
    
    
    # ---- Text Mesh Operations ----
    if text_input.strip():
        text_mesh_min_z = min((text_mesh.matrix_world @ v.co).z for v in text_mesh.data.vertices)
        uphill_min_z = min((uphill_mesh.matrix_world @ v.co).z for v in uphill_mesh.data.vertices)

        text_mesh.location[2] += uphill_min_z - text_mesh_min_z

        bpy.context.view_layer.update()

        target_x_text = 2*x_translation - 20
        
        text_mesh.scale[0] = target_x_text / text_mesh.dimensions.x
        
        text_mesh.scale[1] = (max_y-min_y+50) / text_mesh.dimensions.y

        bpy.context.view_layer.update()

        
        boolean_modifier = uphill_mesh.modifiers.new(name="Boolean", type='BOOLEAN')
        boolean_modifier.operation = 'DIFFERENCE'  # Set the operation type to "Difference"
        boolean_modifier.use_self = True  # Allow the modifier to interact with the object itself
        boolean_modifier.object = text_mesh  # Set the text_mesh as the target object for the operation

        bpy.context.view_layer.objects.active = uphill_mesh
        bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)
        
        bpy.ops.object.duplicate(linked=False) 

        bpy.data.objects.remove(text_mesh, do_unlink=True)
        bpy.context.view_layer.update()

    
    # ---- Export the Final Mesh ----
    bpy.context.view_layer.objects.active = uphill_mesh
    bpy.ops.export_mesh.stl(filepath=diff_stl_path)
    print(f"STL file saved to: {diff_stl_path}")