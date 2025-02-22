import numpy as np

from main_function.GPS_function import parse_gps, AltimetryPlotter, load_gps_data

from scipy.interpolate import splprep, splev, interp1d
from haversine import haversine, Unit

class Uphill_Point_blender:
    def __init__(self, path_gps='example/selvino.gpx', selection=True, selected_point_path='tmp_STL/selected_data.txt', 
                point_output_path = 'tmp_STL/uphill_points.txt', height = 40, width = 80, depth = 30, base_percent = 0.5,rotation = 0):
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
        self.point_output_path = point_output_path

        self.height = height
        self.depth = depth
        self.width = width
        self.base_percent = base_percent
        self.rotation = rotation

        self.track_points = self._track_points_gen()

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

        x_smooth, y_smooth, elevations_smooth = self._spline_curve(x, y, elevations, selected_distance)

        self.points = np.column_stack((x_smooth, y_smooth, elevations_smooth))
        self.points = self._rotation(self.points)
        self.points = self._rescale_points(self.points)

        self._generate_file()


    def _spline_curve(self, x, y, elevations, selection_len):
        """Generates inner curves and corresponding elevation data."""        
        points = np.column_stack((x, y))
        _, indices = np.unique(points, axis=0, return_index=True)
        indices = np.sort(indices)

        x, y = x[indices], -y[indices]
        elevations = elevations[indices]
        tck, u = splprep([x, y], s=0)

        u_fine = np.linspace(0, 1, 1000 * int(selection_len + 1))

        x_smooth, y_smooth = splev(u_fine, tck)

        elevation_spline = interp1d(u, elevations, kind='linear', fill_value='extrapolate')
        elevations_smooth = elevation_spline(u_fine)

        return x_smooth, y_smooth, elevations_smooth

    def _rotation (self, points):
        # rotation to allign first and last points
        p1 = points[0]
        p2 = points[-1]
        direction_vector = p2[:2] - p1[:2]
        angle = np.arctan2(direction_vector[1], direction_vector[0]) 
        rotation_matrix = np.array([
            [np.cos(-angle), -np.sin(-angle), 0],
            [np.sin(-angle),  np.cos(-angle), 0],
            [0,               0,              1]
        ])
        points_centered = points - p1 
        points_rotated = np.dot(points_centered, rotation_matrix.T)
        points = points_rotated + p1


        # An other custom rotation (standard is 0)
        theta = self.rotation * np.pi/180
        rotation_matrix = np.array([
            [np.cos(theta), -np.sin(theta), 0],
            [np.sin(theta),  np.cos(theta), 0],
            [0,              0,             1]
        ])

        return np.dot(points, rotation_matrix.T)

    def _rescale_points (self, points):
        """Scales the uphill mesh to fit the podium dimensions in x and y axes and sets a height for z axis."""

        min_coords = points.min(axis=0)
        max_coords = points.max(axis=0)
        scale_width = self.width/(max_coords[0] - min_coords[0])
        scale_depth = self.depth/(max_coords[1] - min_coords[1])
        
        points[:,2] = points[:,2] - min_coords[2]
        scale_height = self.height/(1+self.base_percent)/(max_coords[2] - min_coords[2])
        points[:,2]= points[:,2]*scale_height + 40/(1+self.base_percent) * self.base_percent

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
