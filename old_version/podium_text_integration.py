import trimesh
import numpy as np

def _scale_text_to_podium(text_mesh, podium):
    """Scales the text mesh dimensions to fit the podium's dimensions."""
    # Extract vertices
    vertices = text_mesh.vertices
    # Calculate min and max coordinates
    min_coords = vertices.min(axis=0)  # Minimum coordinates along each axis
    max_coords = vertices.max(axis=0)  # Maximum coordinates along each axis
    
    # Calculate width and height of the text based on vertices
    text_width = max_coords[1] - min_coords[1]  # Width of the text
    text_height = max_coords[2] - min_coords[2]  # Height of the text

    # Determine target dimensions based on podium shape
    if podium.shape == "rectangular":
        target_width = podium.width * 0.9  # Width of the podium
        target_height = podium.height * 0.9  # Height of the podium (scaled for aesthetics)

    elif podium.shape == "cylindrical":
        target_width = 2 * np.pi * (podium.width / 2) * 0.8  # Circumference of the podium
        target_height = podium.height * 0.8

    else:
        raise ValueError("Unsupported podium shape: choose 'rectangular' or 'cylindrical'.")

    # Compute scale factors
    scale_x = target_width / text_width if text_width > 0 else 1
    scale_z = target_height / text_height if text_height > 0 else 1
    scale_factor = min(scale_x, scale_z)

    # Apply uniform scaling
    text_mesh.apply_scale(scale_factor)

    return text_mesh

def _combine_text_with_rectangular_podium(text_mesh, podium):
    """Combines text mesh with a rectangular podium."""
    # Scale the text to match the podium's dimensions
    text_mesh = _scale_text_to_podium(text_mesh, podium)

    # Position text centered on the front face of the podium
    podium_front_center_x = podium.depth / 2  # Centered along the x-axis
    podium_front_center_y = 0  # Centered along the y-axis
    podium_front_center_z = 0

    # Translate the text to center it on the front face
    translation_vector = [
        podium_front_center_x,  # x-coordinate (centered)
        podium_front_center_y,   # y-coordinate (at the front face)
        podium_front_center_z     # z-coordinate (above podium)
    ]
    
    text_mesh.apply_translation(translation_vector)

    # Combine podium and text meshes
    combined_mesh = podium.mesh + text_mesh
    return combined_mesh


def _slice_mesh_by_width(mesh, slice_width, axis='x'):
    """
    Slices a mesh into smaller sub-meshes based on a specified width along a given axis.
    It also scales the mesh to ensure the total range along the specified axis is divisible by slice_width.

    Parameters:
    - mesh: The input trimesh object to be sliced.
    - slice_width: The width for each slice along the specified axis.
    - axis: The axis along which to slice ('x', 'y', or 'z').

    Returns:
    - List of trimesh objects representing the sliced sub-meshes.
    """
    # Map axis to the corresponding index (0 for 'x', 1 for 'y', 2 for 'z')
    axis_index = 'xyz'.index(axis)
    
    vertices = mesh.vertices
    # Calculate min and max coordinates
    min_val = vertices[:, axis_index].min()
    max_val = vertices[:, axis_index].max()
    
    # Calculate the total range
    total_range = max_val - min_val

    # Determine the scaling factor to make the total range divisible by slice_width
    num_slices = total_range / slice_width
    if num_slices % 1 != 0:  # If it's not an integer
        scale_factor = np.ceil(num_slices)  # Round up to the nearest whole number
        new_total_range = scale_factor * slice_width  # Calculate new total range
        scaling_factor = new_total_range / total_range  # Calculate scaling factor
        # Scale the mesh along the specified axis
        scaling_matrix = np.eye(4)
        scaling_matrix[axis_index, axis_index] = scaling_factor
        mesh.apply_transform(scaling_matrix)  # Scale the mesh

    # Recalculate min and max coordinates after scaling
    vertices = mesh.vertices
    min_val = vertices[:, axis_index].min()
    max_val = vertices[:, axis_index].max()
    
    # List to store the resulting sub-meshes
    sub_meshes = []

    # Iterate through each slice range from min to max along the specified axis
    start = min_val
    while start < max_val:
        end = min(start + slice_width, max_val)  # Ensure the last slice reaches max_val
        
        # Create a mask for vertices within the current slice range along the axis
        mask = (vertices[:, axis_index] >= start) & (vertices[:, axis_index] < end)

        # If there are any vertices in this range, create a sub-mesh
        if np.any(mask):
            # Get original vertex indices that fall within the current slice range
            selected_vertex_indices = np.where(mask)[0]
            # Select the faces where all vertices fall within the current slice range
            face_mask = np.isin(mesh.faces, selected_vertex_indices).all(axis=1)
            selected_faces = mesh.faces[face_mask]

            # Reindex the faces to match the selected vertices
            index_map = {old_idx: new_idx for new_idx, old_idx in enumerate(selected_vertex_indices)}
            reindexed_faces = np.array([[index_map.get(v) for v in face] for face in selected_faces])

            # Create a sub-mesh if there are valid faces selected
            if len(reindexed_faces) > 0:
                selected_vertices = vertices[selected_vertex_indices]
                new_mesh = trimesh.Trimesh(vertices=selected_vertices, faces=reindexed_faces)
                sub_meshes.append(new_mesh)

        start += slice_width  # Move to the next slice range

    return sub_meshes

def _combine_text_with_cylindrical_podium(text_mesh, podium):
    """Combines text mesh with a cylindrical podium."""
    # Scale the text to match the podium's dimensions
    text_mesh = _scale_text_to_podium(text_mesh, podium)


    # Generate the cylindrical podium mesh
    num_segments = (len(podium.mesh.vertices)-2)/2  # Get number of faces
    
    # Calculate the angle per segment
    angle_per_segment = 2 * np.pi / num_segments
    len_segment = 2 * np.pi * (podium.width/2) / num_segments

    submeshes = _slice_mesh_by_width(text_mesh, len_segment, axis='y')
    
    # # Calculate vertical offset for centering text on the podium height
    # text_height = np.max(text_mesh.vertices[:, 2]) - np.min(text_mesh.vertices[:, 2])
    # text_offset_z = (podium.height / 2) - (text_height / 2)

    # List to hold the transformed sub-meshes
    combined_meshes = []

    for i, submesh in enumerate(submeshes):
        # Calcola l'angolo di rotazione per questo segmento
        angle = i * angle_per_segment

        # Calcola il centro originario di submesh lungo X e Y
        center_x = (np.max(submesh.vertices[:, 0]) + np.min(submesh.vertices[:, 0])) / 2
        center_y = (np.max(submesh.vertices[:, 1]) + np.min(submesh.vertices[:, 1])) / 2

        # Calcola il vettore di traslazione per centrare il submesh all'origine
        origin_translation_vector = [-center_x, -center_y, 0]
        submesh.apply_translation(origin_translation_vector)

        # Matrice di rotazione per orientare il submesh verso l'esterno
        rotation_matrix = trimesh.transformations.rotation_matrix(angle, [0, 0, 1])  # Rotazione attorno all'asse Z
        submesh.apply_transform(rotation_matrix)  # Applica la rotazione

        # Calcola la posizione finale lungo la circonferenza
        x_pos = (podium.width / 2) * np.cos(angle)
        y_pos = (podium.width / 2) * np.sin(angle)

        # Applica la traslazione finale per posizionare il submesh sulla circonferenza del podio
        submesh.apply_translation([x_pos, y_pos, 0])

        # Aggiungi il submesh trasformato alla lista dei combined_meshes
        combined_meshes.append(submesh)

    # Combine all transformed submeshes into a single mesh for the text
    final_text_mesh = trimesh.util.concatenate(combined_meshes)
    
    # Combine podium and text meshes into the final result
    combined_mesh = podium.mesh + final_text_mesh
    return combined_mesh

def combine_text_and_podium(text3d, podium, fn= 'tmp_STL/podium_title.stl'):
    """
    Combines a text STL mesh with a podium STL mesh, adjusting dimensions and positioning based on podium shape.
    
    Parameters:
    - text3d: Instance of Text3D containing the STL text mesh.
    - podium: Instance of Podium containing the podium mesh.
    
    Returns:
    - A combined trimesh object with both the podium and scaled text.
    """
    text_mesh = text3d.mesh.copy()  # Copy to avoid modifying the original
    # Rotate the text mesh by 90 degrees around the Y-axis
    rotation_matrix = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])  # 90 degrees in radians
    text_mesh.apply_transform(rotation_matrix)

    if podium.shape == "rectangular":
        mesh_combined = _combine_text_with_rectangular_podium(text_mesh, podium)
    elif podium.shape == "cylindrical":
        mesh_combined = _combine_text_with_cylindrical_podium(text_mesh, podium)
    else:
        raise ValueError("Unsupported podium shape: choose 'rectangular' or 'cylindrical'.")
    
    mesh_combined.export(fn)

    return mesh_combined

