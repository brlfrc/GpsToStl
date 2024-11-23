import trimesh
import numpy as np
import subprocess

from main_function.Text3D import Text3D
from main_function.Podium import Podium
from main_function.UphillSTL import UphillSTL
from main_function.STL_function import difference_with_blender, union_with_blender


class Model_2v:
    def __init__(self, text3d=None, uphill=None, text_specs=None, uphill_specs=None,
                pic_size= 100, depth = 30, height = 40):
        """
        Initialize the Model_3D class. Allows initializing by passing podium, text3d, and uphill objects
        directly or by passing specifications for each.
        """
        if text3d and uphill:
            self.text3d = text3d
            self.uphill = uphill
        else:
            self.text3d = Text3D(**text_specs) if text_specs else None
            self.uphill = UphillSTL(**uphill_specs) if uphill_specs else None

        self.text_mesh = self.text3d.mesh
        self.uphill_mesh = self.uphill.mesh

        # Initialize combined mesh
        self.mesh = None
        self.difference_mesh = None

        # Fixed parameters
        self.width = pic_size*0.8
        self.depth = depth
        self.height = height

        self.saved_mesh = False
        
        
    def update_mesh(self):
        self._remodel_text()
        self._remodel_uphill()
        self._allign_models()

        self.mesh = self.text_mesh+self.uphill_mesh


    def make_magnet_union(self, filepath='tmp_STL/'):
        """Exports the current mesh to an STL file."""
        if not self.saved_mesh:
            self.save_all_mesh()

        path_text = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\text_2v.stl"
        path_uphill = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\uphill_2v.stl"
        path_magnet = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\magnet_holder.stl"
        path_cube = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\cube_magnet_holder.stl"
        path_uphill_diff = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\final_mesh.stl"

        union_with_blender(path_text, path_uphill, path_cube, path_magnet, path_uphill_diff)

        self.mesh = trimesh.load(path_uphill_diff)

    def solidify_uphill_mesh(self):
        """Exports the current mesh to an STL file."""
        if not self.saved_mesh:
            self.save_all_mesh()

        path_uphill = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\uphill_2v.stl"
        
        blender_path = r"C:\Program Files\Blender Foundation\Blender 2.91\blender.exe"
        script_path = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\blender_repair\solidify_uphill.py"
        
        command = [
            blender_path, "--background", "--python", script_path,
            "--", path_uphill
        ]
        subprocess.run(command)


        self.uphill_mesh = trimesh.load(path_uphill)
        self.save_all_mesh()

    def make_difference_mesh(self):
        """Exports the current mesh to an STL file."""
        if not self.saved_mesh:
            self.save_all_mesh()

        path_text = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\text_2v.stl"
        path_uphill = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\uphill_2v.stl"
        path_uphill_diff = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\mesh_difference.stl"
        path_cube = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\cube_magnet_holder.stl"
        path_magnet = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\magnet_holder.stl"
        
        
        difference_with_blender(path_text, path_uphill, path_cube, path_magnet, path_uphill_diff)

        self.difference_mesh = trimesh.load(path_uphill_diff)


    def save_all_mesh(self, filepath='tmp_STL/'):
        """Exports the current mesh to an STL file."""
        self.text_mesh.export(filepath+ 'text_2v.stl')
        self.uphill_mesh.export(filepath+ 'uphill_2v.stl')

        self.saved_mesh = True


    def _remodel_uphill (self):
        """Scales the uphill mesh to fit the podium dimensions in x and y axes and sets a height for z axis."""
        vertices = self.uphill_mesh.vertices
        min_coords = vertices.min(axis=0)
        max_coords = vertices.max(axis=0)
        scale_width = self.width/(max_coords[0] - min_coords[0])
        scale_depth = self.depth/(max_coords[1] - min_coords[1])
        scale_height = self.height/(max_coords[2] - min_coords[2])

        self.uphill_mesh.apply_scale([scale_width, scale_depth, scale_height])
        # self.uphill_mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1]))


    def _remodel_text (self):
        """Scales the uphill mesh to fit the podium dimensions in x and y axes and sets a height for z axis."""
        vertices = self.text_mesh.vertices
        min_coords = vertices.min(axis=0)
        max_coords = vertices.max(axis=0)
        scale_height = self.height/(max_coords[2] - min_coords[2])*self.uphill.min_thickness_percent/(1+self.uphill.min_thickness_percent)
        scale_width = self.width/(max_coords[0] - min_coords[0])
        scale_depth = self.depth/(max_coords[1] - min_coords[1])*1.1
        self.text_mesh.apply_scale([scale_width, scale_depth, scale_height])
        
        # vertices = self.text_mesh.vertices
        # min_coords = vertices.min(axis=0)
        # max_coords = vertices.max(axis=0)
        # scale_width = self.height/(max_coords[0] - min_coords[0])*self.uphill.min_thickness_percent/(1+self.uphill.min_thickness_percent)
        # scale_depth = self.width/(max_coords[1] - min_coords[1])
        # scale_height = self.depth/(max_coords[2] - min_coords[2])*1.1
        # self.text_mesh.apply_scale([scale_width, scale_depth, scale_height])
        # self.text_mesh.show()

        # self.text_mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
        self.text_mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1]))

    def _allign_models (self):
        """Scales the uphill mesh to fit the podium dimensions in x and y axes and sets a height for z axis."""
        vertices_text = self.text_mesh.vertices
        vertices_uphill = self.uphill_mesh.vertices

        min_coords_text = vertices_text.min(axis=0)
        min_coords_uphill = vertices_uphill.min(axis=0)

        translation_vector = [
            -min_coords_text[0]+min_coords_uphill[0],  # x-coordinate (centered on top)
            -min_coords_text[1]+min_coords_uphill[1]-0.05,   # y-coordinate (on top)
            -min_coords_text[2]+min_coords_uphill[2]     # z-coordinate (at the height of the podium)
        ]
        
        self.text_mesh.apply_translation(translation_vector)
        







