import trimesh
import numpy as np
import matplotlib.pyplot as plt
from main_function.Podium import Podium
from main_function.UphillSTL import UphillSTL

# Quando trasformo queso in una classe modifico a priori fixed_height = 0, margin = 0.8, senza doverle passare alla funzione di volta in volta

def _scale_uphill(uphill_mesh, podium, fixed_height = 0, margin = 0.8):
    """Scales the uphill mesh to fit the podium dimensions in x and y axes and sets a fixed height for z axis."""
    # Extract vertices
    vertices = uphill_mesh.vertices
    # Calculate min and max coordinates
    min_coords = vertices.min(axis=0)  # Minimum coordinates along each axis
    max_coords = vertices.max(axis=0)  # Maximum coordinates along each axis
    
    # Calculate width and height of the uphill based on vertices
    uphill_width = max_coords[0] - min_coords[0]  # Width of the uphill
    uphill_depth = max_coords[1] - min_coords[1]  # Depth of the uphill

    # Determine target dimensions based on podium shape
    if podium.shape == "rectangular":
        target_width = podium.width * margin  # Width of the podium
        target_depth = podium.depth * margin  # Depth of the podium

    elif podium.shape == "cylindrical":
        target_width = podium.width * margin  # Circumference of the podium
        target_depth = target_width
        uphill_width = np.sqrt(uphill_width*uphill_width+uphill_depth*uphill_depth)
        uphill_depth = uphill_width

    else:
        raise ValueError("Unsupported podium shape: choose 'rectangular' or 'cylindrical'.")

    # Compute scale factors for x and y
    scale_x = target_width / uphill_width if uphill_width > 0 else 1
    scale_y = target_depth / uphill_depth if uphill_depth > 0 else 1
    
    min_z = vertices[:, 2].min()  # Minimum z coordinate
    max_z = vertices[:, 2].max()  # Maximum z coordinate

    # Calculate current height of the uphill mesh
    current_height = max_z - min_z

    # Compute scale factor for z-axis
    if fixed_height == 0:
        scale_z = podium.height*3 / current_height
    else:
        scale_z = fixed_height / current_height
    
    uphill_mesh.apply_scale([scale_x, scale_y, scale_z])  # Scale x and y, keep z the same

    return uphill_mesh

def _combine_uphill_with_rectangular_podium(uphill_mesh, podium):
    """Combines uphill mesh with a rectangular podium."""
    # Scale the uphill mesh to match the fixed height
    uphill_mesh = _scale_uphill(uphill_mesh, podium)

    # Align uphill mesh with podium
    angle = np.pi/2
    uphill_mesh.apply_transform(trimesh.transformations.rotation_matrix(angle, [0, 0, 1]))

    # Position uphill centered on the top face of the podium
    podium_top_center_x = 0  # Centered along the x-axis
    podium_top_center_y = 0  # Centered along the y-axis
    podium_top_center_z = podium.height/2   # Positioned at the top face

    # Translate the uphill mesh to position it on the podium
    translation_vector = [
        podium_top_center_x,  # x-coordinate (centered on top)
        podium_top_center_y,   # y-coordinate (on top)
        podium_top_center_z     # z-coordinate (at the height of the podium)
    ]
    
    uphill_mesh.apply_translation(translation_vector)

    # Combine podium and uphill meshes
    combined_mesh = podium.mesh + uphill_mesh
    return combined_mesh

def _combine_uphill_with_cylindrical_podium(uphill_mesh, podium):
    """Combines uphill mesh with a cylindrical podium."""
    # Scale the uphill mesh to match the fixed height
    uphill_mesh = _scale_uphill(uphill_mesh, podium, 0)

    # Align uphill mesh with podium
    angle = np.pi/2
    uphill_mesh.apply_transform(trimesh.transformations.rotation_matrix(angle, [0, 0, 1]))

    # Position uphill centered on the top face of the podium
    podium_top_center_x = 0  # Centered along the x-axis
    podium_top_center_y = 0  # Centered along the y-axis
    podium_top_center_z = podium.height/2   # Positioned at the top face

    # Translate the uphill mesh to position it on the podium
    translation_vector = [
        podium_top_center_x,  # x-coordinate (centered on top)
        podium_top_center_y,   # y-coordinate (on top)
        podium_top_center_z     # z-coordinate (at the height of the podium)
    ]
    
    uphill_mesh.apply_translation(translation_vector)

    # Combine podium and uphill meshes into the final result
    combined_mesh = podium.mesh + uphill_mesh
    return combined_mesh

def combine_uphill_and_podium(uphill_stl, podium):
    """
    Combines an uphill STL mesh with a podium STL mesh, adjusting dimensions and positioning based on podium shape.
    
    Parameters:
    - uphill_stl: Instance of UphillSTL containing the STL uphill mesh.
    - podium: Instance of Podium containing the podium mesh.
    
    Returns:
    - A combined trimesh object with both the podium and scaled uphill mesh.
    """
    uphill_mesh = uphill_stl.mesh.copy()  # Copy to avoid modifying the original

    if podium.shape == "rectangular":
        combined_mesh = _combine_uphill_with_rectangular_podium(uphill_mesh, podium)
    elif podium.shape == "cylindrical":
        combined_mesh = _combine_uphill_with_cylindrical_podium(uphill_mesh, podium)
    else:
        raise ValueError("Unsupported podium shape: choose 'rectangular' or 'cylindrical'.")
    
    return combined_mesh

# Example Usage
uphill = UphillSTL(path_gps='example/selvino/selvino.gpx', selection=True)
podium = Podium(width=80, height=20, shape="cylindrical")  # Example podium shape

# Combine the uphill mesh with the podium
combined_mesh = combine_uphill_and_podium(uphill, podium)

# Visualize the combined mesh
combined_mesh.show()
