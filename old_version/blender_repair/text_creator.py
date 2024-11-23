import bpy # type: ignore
import sys

# Paths for input and output
input_text_path  = sys.argv[-2]  # Replace with the actual text or load it from a file
output_stl_path = sys.argv[-1]  # Path to save the STL


with open(input_text_path, 'r') as file:
    text_input = file.read().strip()
font_path = r"C:\Windows\Fonts\Stencilia-A.ttf"  # Path to the Stencilia-A font


# Clear existing objects in the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create a new text object
bpy.ops.object.text_add(location=(0, 0, 0))
text_obj = bpy.context.active_object
text_obj.data.body = text_input

# Load and set the Stencilia-A font
font = bpy.data.fonts.load(font_path)
text_obj.data.font = font

# Extrude the text in the Geometry section
text_obj.data.extrude = 0.2  # Adjust the extrusion thickness as needed
text_obj.data.offset = 0  # Ensure offset is set to 0

# Rotate the text 90 degrees around the X-axis
text_obj.rotation_euler[0] = 1.5708  # 90 degrees in radians

# Convert the text object to a mesh
bpy.ops.object.convert(target='MESH')

# Apply the transformation to make sure rotation takes effect
bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

# Scaling to the desired dimensions (replace with your dimensions)
desired_x = 5.0  # Replace with your desired X dimension
desired_y = 3.0  # Replace with your desired Y dimension
desired_z = 1.0  # Replace with your desired Z dimension

# Calculate the current bounding box size of the mesh
mesh = text_obj.data
min_coords = [min(v.co[i] for v in mesh.vertices) for i in range(3)]
max_coords = [max(v.co[i] for v in mesh.vertices) for i in range(3)]
current_x = max_coords[0] - min_coords[0]
current_y = max_coords[1] - min_coords[1]
current_z = max_coords[2] - min_coords[2]

# Calculate the scale factors for each dimension
scale_x = desired_x / current_x
scale_y = desired_y / current_y
scale_z = desired_z / current_z

# Apply the scaling
text_obj.scale = (scale_x, scale_y, scale_z)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# Recalculate the bounding box after scaling
min_coords = [min(v.co[i] for v in mesh.vertices) for i in range(3)]
max_coords = [max(v.co[i] for v in mesh.vertices) for i in range(3)]

# Center the object in X and Y
center_x = (min_coords[0] + max_coords[0]) / 2
center_y = (min_coords[1] + max_coords[1]) / 2
text_obj.location.x -= center_x
text_obj.location.y -= center_y

# Save the mesh as an STL file
bpy.ops.export_mesh.stl(filepath=output_stl_path)

print(f"Mesh has been saved to {output_stl_path}")
