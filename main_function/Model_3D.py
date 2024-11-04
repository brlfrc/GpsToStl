import trimesh
import numpy as np
from main_function.Text3D import Text3D
from main_function.Podium import Podium
from main_function.UphillSTL import UphillSTL

class Model_3D:
    def __init__(self, podium=None, text3d=None, uphill=None, podium_specs=None, text_specs=None, uphill_specs=None, margin = 0.8, height_multiplier = 3, rotation_uphill_angle = 0):
        """
        Initialize the Model_3D class. Allows initializing by passing podium, text3d, and uphill objects
        directly or by passing specifications for each.
        """
        if podium and text3d and uphill:
            self.podium = podium
            self.text3d = text3d
            self.uphill = uphill
        else:
            self.podium = Podium(**podium_specs) if podium_specs else None
            self.text3d = Text3D(**text_specs) if text_specs else None
            self.uphill = UphillSTL(**uphill_specs) if uphill_specs else None

        self.podium_mesh = self.podium.mesh
        self.text_mesh = self.text3d.mesh
        self.uphill_mesh = self.uphill.mesh

        # Initialize combined mesh
        self.mesh = None

        # Fixed parameters
        self.height_multiplier = height_multiplier
        self.margin = margin
        self.rotation_uphill_angle= rotation_uphill_angle

    # Main function
    def update_mesh(self, combine_uphill=True, combine_text=True):
        """
        Update the mesh with specified combinations.
        - combine_uphill: if True, combines uphill and podium.
        - combine_text: if True, combines text and podium.
        """

        if combine_text and self.text3d:
            self.text_mesh = self._remodel_text_stl()
        if combine_uphill and self.uphill:
            self.rotation_uphill(self.rotation_uphill_angle)
            self.uphill_mesh = self._remodel_uphill_stl()
        
        self.text_mesh.visual.face_colors= self.text3d.color
        self.uphill_mesh.visual.face_colors= self.uphill.color
        self.podium_mesh.visual.face_colors= self.podium.color

        self.mesh = self.podium_mesh + self.text_mesh + self.uphill_mesh
        

    def save_mesh(self, filename='final_model.stl'):
        """Exports the current mesh to an STL file."""
        if self.mesh:
            self.mesh.export(filename)
        else:
            raise ValueError("Mesh is not defined. Call update_mesh() to create it first.")
    
    def save_two_mesh(self, filepath='tmp_STL/'):
        """Exports the current mesh to an STL file."""
        podium_text_mesh = self.podium_mesh + self.text_mesh
        
        podium_text_mesh.export(filepath+ 'PODIUM_TEXT.STL')
        self.uphill_mesh.export(filepath+ 'uphill.STL')

    def save_all_mesh(self, filepath='tmp_STL/'):
        """Exports the current mesh to an STL file."""
        self.text_mesh.export(filepath+ 'text.STL')
        self.podium_mesh.export(filepath+ 'podium.STL')
        self.uphill_mesh.export(filepath+ 'uphill.STL')
        
    def show(self):
        """Displays the generated STL mesh."""
        self.mesh.show()

    def rotation_uphill(self, rotation_uphill_angle):
        angle = rotation_uphill_angle/360*2*np.pi
        self.uphill_mesh.apply_transform(trimesh.transformations.rotation_matrix(angle, [0, 0, 1]))

##########################################
    # COMBINE UPHILL AND PODIUM
##########################################

    def _remodel_uphill_stl(self):

        if self.podium.shape == "rectangular":
            uphill_mesh = self._combine_uphill_with_rectangular_podium(self.uphill_mesh.copy(), self.podium)
        elif self.podium.shape == "cylindrical":
            uphill_mesh = self._combine_uphill_with_cylindrical_podium(self.uphill_mesh.copy(), self.podium)
        else:
            raise ValueError("Unsupported podium shape: choose 'rectangular' or 'cylindrical'.")

        return uphill_mesh


    def _combine_uphill_with_rectangular_podium(self, uphill_mesh, podium):
        """Combines uphill mesh with a rectangular podium."""
        uphill_mesh = self._scale_uphill(uphill_mesh)

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

        return uphill_mesh

    def _combine_uphill_with_cylindrical_podium(self, uphill_mesh, podium):
        """Combines uphill mesh with a cylindrical podium."""
        uphill_mesh = self._scale_uphill(uphill_mesh)

        # # Align uphill mesh with podium
        # angle = np.pi/2
        # uphill_mesh.apply_transform(trimesh.transformations.rotation_matrix(angle, [0, 0, 1]))

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

        return uphill_mesh
    
    def _scale_uphill(self, uphill_mesh):
        """Scales the uphill mesh to fit the podium dimensions in x and y axes and sets a height for z axis."""
        vertices = uphill_mesh.vertices
        min_coords = vertices.min(axis=0)
        max_coords = vertices.max(axis=0)
        uphill_width = max_coords[0] - min_coords[0]
        uphill_depth = max_coords[1] - min_coords[1]

        if self.podium.shape == "rectangular":
            target_width = self.podium.width * self.margin
            target_depth = self.podium.depth * self.margin
        elif self.podium.shape == "cylindrical":
            target_width = self.podium.width * self.margin
            target_depth = target_width
            uphill_width = np.sqrt(uphill_width**2 + uphill_depth**2)
            uphill_depth = uphill_width
        else:
            raise ValueError("Unsupported podium shape: choose 'rectangular' or 'cylindrical'.")

        scale_x = target_width / uphill_width if uphill_width > 0 else 1
        scale_y = target_depth / uphill_depth if uphill_depth > 0 else 1
        min_z, max_z = vertices[:, 2].min(), vertices[:, 2].max()
        current_height = max_z - min_z
        scale_z = (self.height_multiplier*self.podium.height) / current_height

        uphill_mesh.apply_scale([scale_x, scale_y, scale_z])
        return uphill_mesh


################################################
    # COMBINE TEXT AND PODIUM
################################################

    def _remodel_text_stl(self):
        """Combines the scaled text mesh with the podium."""
        text_mesh = self.text3d.mesh.copy()

        rotation_matrix = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])
        text_mesh.apply_transform(rotation_matrix)

        if self.podium.shape == "rectangular":
            text_mesh_modified = self._combine_text_with_rectangular_podium(text_mesh, self.podium)
        elif self.podium.shape == "cylindrical":
            text_mesh_modified = self._combine_text_with_cylindrical_podium(text_mesh, self.podium)
        else:
            raise ValueError("Unsupported podium shape: choose 'rectangular' or 'cylindrical'.")

        return text_mesh_modified

    def _scale_text_to_podium(self, text_mesh, podium):
        """Scales the text mesh dimensions to fit the podium's dimensions."""
        vertices = text_mesh.vertices
        min_coords, max_coords = vertices.min(axis=0), vertices.max(axis=0)
        text_width, text_height = max_coords[1] - min_coords[1], max_coords[2] - min_coords[2]

        # Define target width and height based on podium shape
        if podium.shape == "rectangular":
            target_width, target_height = podium.width * 0.9, podium.height * 0.9
        elif podium.shape == "cylindrical":
            target_width = 2 * np.pi * (podium.width / 2) * 0.8
            target_height = podium.height * 0.8
        else:
            raise ValueError("Unsupported podium shape.")

        # Calculate scale factor and apply scaling
        scale_factor = min(target_width / text_width if text_width else 1,
                           target_height / text_height if text_height else 1)
        text_mesh.apply_scale(scale_factor)
        return text_mesh

    def _combine_text_with_rectangular_podium(self, text_mesh, podium):
        """Combines scaled text with a rectangular podium."""
        text_mesh = self._scale_text_to_podium(text_mesh, podium)
        translation_vector = [podium.depth / 2, 0, 0]
        text_mesh.apply_translation(translation_vector)
        return text_mesh

    def _slice_mesh_by_width(self, mesh, slice_width, axis='x'):
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

    def _combine_text_with_cylindrical_podium(self,text_mesh, podium):
        # Scale the text to match the podium's dimensions
        text_mesh = self._scale_text_to_podium(text_mesh, podium)


        # Generate the cylindrical podium mesh
        num_segments = (len(podium.mesh.vertices)-2)/2  # Get number of faces
        
        # Calculate the angle per segment
        angle_per_segment = 2 * np.pi / num_segments
        len_segment = 2 * np.pi * (podium.width/2) / num_segments

        submeshes = self._slice_mesh_by_width(text_mesh, len_segment, axis='y')

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
        
        return final_text_mesh


