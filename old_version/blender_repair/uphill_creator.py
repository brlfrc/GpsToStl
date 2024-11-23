import bpy  # type: ignore
import bmesh # type: ignore
import sys

# Clear all existing objects in the scene
bpy.ops.object.select_all(action='SELECT')  # Select all objects
bpy.ops.object.delete()  # Delete selected objects

# Retrieve the input file path and output file path from command-line arguments
file_path = sys.argv[-2]  # Argument after "--" is the input file path
output_stl_path = sys.argv[-1]  # Argument after the input path is the output STL file path

# Read and parse points from the file
points = []
with open(file_path, 'r') as file:
    lines = file.readlines()
    
    for line in lines:
        # Skip commented lines
        if line.startswith("#"):
            continue
        
        # Process the line containing points
        line = line.strip()  # Remove any leading/trailing whitespace
        if line:  # Check if the line is not empty
            # Split the line by semicolons and parse the x, y, z values
            for point in line.split(';'):
                if point.strip():  # Check if the point is not empty
                    x, y, z = map(float, point.split(','))
                    points.append([x, y, z])

if points:
    max_x = max(point[0] for point in points)
    min_x = min(point[0] for point in points)
    max_y = max(point[1] for point in points)
    min_y = min(point[1] for point in points)
    
    center_x = (max_x + min_x) / 2
    center_y = (max_y + min_y) / 2
    
    for point in points:
        point[0] -= center_x
        point[1] -= center_y
        
# Create a new mesh and an object for the mesh
mesh = bpy.data.meshes.new("ExtrudedMesh")
obj = bpy.data.objects.new("uphill_blender", mesh)

# Add the object to the current scene
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

# Create the mesh using bmesh
bm = bmesh.new()

# Add vertices at Z = 0 and vertices at the original Z position
base_vertices = []
top_vertices = []

for x, y, z in points:
    # Vertices at the base (Z = 0)
    base_vertex = bm.verts.new((x, y, 0))
    base_vertices.append(base_vertex)
    
    # Vertices at the top (original Z position)
    top_vertex = bm.verts.new((x, y, z))
    top_vertices.append(top_vertex)

bm.verts.ensure_lookup_table()

# Create faces between the base and top vertices (excluding the connection between the first and last)
for i in range(len(points) - 1):  # Use len(points) - 1 to avoid the last connection
    v1 = base_vertices[i]
    v2 = top_vertices[i]
    v3 = top_vertices[i + 1]
    v4 = base_vertices[i + 1]

    # Create a quadrilateral face between the vertices
    bm.faces.new([v1, v2, v3, v4])

for face in bm.faces:
    face.normal_flip() if face.normal.z < 0 else None
    
# Update the mesh with the new geometry
bm.to_mesh(mesh)
bm.free()

# Add a Solidify modifier to give thickness to the mesh
solidify_modifier = obj.modifiers.new(name="ThicknessModifier", type='SOLIDIFY')
solidify_modifier.thickness = 1  # Adjust the thickness as needed
solidify_modifier.offset = 0



decimate_modifier = obj.modifiers.new(name="Decimate", type='DECIMATE')
decimate_modifier.decimate_type = 'COLLAPSE'

decimate_modifier.ratio = 0.05

# Applicare il modificatore
bpy.ops.object.modifier_apply(modifier=decimate_modifier.name)


# Update the 3D view
bpy.context.view_layer.update()

# Save the mesh to an STL file
bpy.ops.export_mesh.stl(filepath=output_stl_path)

print(f"Mesh has been saved to {output_stl_path}")