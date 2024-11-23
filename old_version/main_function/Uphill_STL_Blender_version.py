import numpy as np
import matplotlib.pyplot as plt
import trimesh
import subprocess
import os

from main_function.GPS_function import parse_gps, AltimetryPlotter, load_gps_data
from main_function.STL_function import repair_with_blender

from scipy.interpolate import splprep, splev, interp1d
from haversine import haversine, Unit

class UphillSTL_blender:
    def __init__(self, path_gps='example/selvino.gpx', selection=True, selected_point_path='tmp_STL/selected_data.txt', 
                output_path='tmp_STL/uphill_blender_v.stl', point_output_path = 'tmp_STL/uphill_points.txt', 
                repair= False, min_thickness_percent=0.5):
        """
        Initializes an instance of UphillSTL to generate a 3D STL model from GPS data.
        
        Parameters:
        - path_gps: Path to the GPS file (.gpx).
        - selection: Whether to perform selection on the GPS data.
        - output_path: Path to save the selected GPS data.
        - scale: Scale factor to adjust the STL dimensions.
        - image_resolution: Resolution for the elevation matrix image.
        """
        self.path_gps = path_gps
        self.selection = selection
        self.selected_point_path = selected_point_path
        self.output_path = output_path
        self.point_output_path = point_output_path
        self.mesh = None
        self.min_thickness_percent= min_thickness_percent

        self.track_points = self._track_points_gen()
        self.file_point_generated = False
        self._create_mesh()  # Create the mesh from the elevation matrix

        self.mesh_is_watertight = self.mesh.is_watertight
        self.repair = repair
        if self.repair:
            self._repair_mesh()
        

    def show(self):
        """Displays the generated STL mesh."""
        self.mesh.show()

    def _track_points_gen(self):
        """Generates the elevation matrix from the GPS data."""
        if self.selection:
            distances, elevation_data = parse_gps(self.path_gps)
            selection = AltimetryPlotter(distances, elevation_data, self.selected_point_path)
            selected_distance = selection.get_selected_distance()
            gps_data = load_gps_data(self.selected_point_path)
            latitudes = gps_data[:, 0]
            longitudes = gps_data[:, 1]
            elevations = gps_data[:, 2]
        else:
            gps_data = load_gps_data(self.selected_point_path)
            latitudes = gps_data[:, 0]
            longitudes = gps_data[:, 1]
            elevations = gps_data[:, 2]
            total_distance = 0
            
            previous_point = None
            for lat, lon in zip(latitudes, longitudes):
                if previous_point is not None:
                    dist = haversine((previous_point.latitude, previous_point.longitude), (lat, lon), unit=Unit.METERS)
                    total_distance += dist / 1000  
                else:
                    dist = 0  
            
            selected_distance = total_distance


        x = latitudes
        y = longitudes

        # Generate the smooth spline curve and inner boundaries
        x_smooth, y_smooth, elevations_smooth = self._spline_curve(x, y, elevations, selected_distance)

        self.points = np.column_stack((x_smooth, y_smooth, elevations_smooth))
        self.points = self._rescale_points(self.points)

        self._generate_file()


    def _spline_curve(self, x, y, elevations, selection_len):
        """Generates inner curves and corresponding elevation data."""        
        points = np.column_stack((x, y))
        _, indices = np.unique(points, axis=0, return_index=True)
        indices = np.sort(indices)

        x, y = x[indices], y[indices]
        elevations = elevations[indices]
        tck, u = splprep([x, y], s=0)

        u_fine = np.linspace(0, 1, 1000 * int(selection_len + 1))

        x_smooth, y_smooth = splev(u_fine, tck)

        elevation_spline = interp1d(u, elevations, kind='linear', fill_value='extrapolate')
        elevations_smooth = elevation_spline(u_fine)

        return x_smooth, y_smooth, elevations_smooth

    def _rescale_points (self, points):
        """Scales the uphill mesh to fit the podium dimensions in x and y axes and sets a height for z axis."""

        min_coords = points.min(axis=0)
        max_coords = points.max(axis=0)
        scale_width = 80/(max_coords[0] - min_coords[0])
        scale_depth = 30/(max_coords[1] - min_coords[1])
        
        points[:,2] = points[:,2] - min_coords[2]
        scale_height = 40/(1+self.min_thickness_percent)/(max_coords[2] - min_coords[2])
        points[:,2]= points[:,2]*scale_height + 40/(1+self.min_thickness_percent) * self.min_thickness_percent

        points = np.column_stack((points[:,0]*scale_width, points[:,1]*scale_depth, points[:,2]))

        return points

    def _generate_file (self):
        self.file_point_generated = True

        with open(self.point_output_path, 'w') as file:
            # Write the comment header
            file.write("# Final point for uphill Mesh\n")
            
            # Format the points as "x,y,z;" for each point in the 'points' array
            points_str = ';'.join([f"{x:.6f},{y:.6f},{z:.6f}" for x, y, z in self.points])
            
            # Write the formatted points to the file
            file.write(f"{points_str}\n")

    def _create_mesh(self):

        point_path = os.path.join(r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl", self.point_output_path)
        mesh_path = os.path.join(r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl", self.output_path)

        blender_path = r"C:\Program Files\Blender Foundation\Blender 2.91\blender.exe"
        script_path = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\blender_repair\uphill_creator.py"
        
        command = [
            blender_path, "--background", "--python", script_path,
            "--", point_path, mesh_path
        ]
        subprocess.run(command)

        self.mesh = trimesh.load(self.output_path)

    def _repair_mesh(self):
        path = os.path.join(r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl", self.output_path)

        if not self.mesh_is_watertight:
            repair_with_blender(path, path)
            self.mesh = trimesh.load(path)
            self.mesh_is_watertight = self.mesh.is_watertight
        
        print('Mesh is watertight: ', self.mesh_is_watertight)

