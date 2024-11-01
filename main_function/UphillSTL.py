import numpy as np
import matplotlib.pyplot as plt

from main_function.GPS_function import parse_gps, AltimetryPlotter, load_gps_data
from main_function.STL_function import numpy2stl
from skimage.draw import polygon
from scipy.interpolate import splprep, splev, interp1d
from haversine import haversine, Unit

class UphillSTL:
    def __init__(self, path_gps='example/selvino.gpx', selection=True, output_path='tmp_STL/selected_data.txt', fn = 'tmp_STL/uphill_tmp_STL.stl', scale=100, thickness_multiplier=1,  image_resolution=800, color = [250,0,0,250]):
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
        self.output_path = output_path
        self.fn = fn
        self.scale = scale
        self.thickness_multiplier = thickness_multiplier
        self.image_resolution = image_resolution
        self.color = color
        self.elevation_matrix = self._generate_elevation_matrix()
        self.mesh = self._create_mesh()  # Create the mesh from the elevation matrix

    def show_matrix(self):
        """Displays the elevation matrix using matplotlib."""
        plt.imshow(self.elevation_matrix, cmap='terrain')
        plt.colorbar(label='Elevation')
        plt.title('Elevation Matrix')
        plt.xlabel('X coordinate')
        plt.ylabel('Y coordinate')
        plt.show()

    def show(self):
        """Displays the generated STL mesh."""
        self.mesh.show()

    def show_all(self):
        """Displays both the elevation matrix and the STL mesh."""
        self.show_matrix()  # Show the elevation matrix
        self.show_mesh()    # Show the mesh

    def _generate_elevation_matrix(self):
        """Generates the elevation matrix from the GPS data."""
        if self.selection:
            distances, elevation_data = parse_gps(self.path_gps)
            selection = AltimetryPlotter(distances, elevation_data, self.output_path)
            selected_distance = selection.get_selected_distance()
            gps_data = load_gps_data(self.output_path)
            latitudes = gps_data[:, 0]
            longitudes = gps_data[:, 1]
            elevations = gps_data[:, 2]
        else:
            gps_data = load_gps_data(self.output_path)
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
        x_smooth, y_smooth, x_inner, y_inner, elevations_smooth = self._spline_inner_curve(x, y, elevations, selected_distance, self.thickness_multiplier)
        elevation_matrix = self._create_elevation_matrix(x_smooth, y_smooth, x_inner, y_inner, elevations_smooth)

        return elevation_matrix

    def _spline_inner_curve(self, x, y, elevations, selection_len, thickness=None):
        """Generates inner curves and corresponding elevation data."""
        thickness = np.min(np.diff(x))*self.thickness_multiplier
        
        # Initialize parameters for fitting the spline
        attempts = 0
        max_attempts = 3  # Maximum number of attempts to fit the spline

        while attempts < max_attempts:
            try:
                # Attempt spline fitting
                tck, u = splprep([x, y], s=0)
                break  # Exit the loop if successful
            except ValueError:
                # If it fails, downsample to use half the points
                x, y = x[::2], y[::2]
                elevations = elevations[::2]  # Also downsample elevations to match
                attempts += 1  # Increment the attempt counter
                
                # If downsampling results in too few points, break the loop
                if len(x) < 2:  # Ensure there are at least 2 points to fit a spline
                    raise ValueError("Not enough unique points to fit a spline.")

        u_fine = np.linspace(0, 1, 1000 * int(selection_len + 1))

        x_smooth, y_smooth = splev(u_fine, tck)

        elevation_spline = interp1d(u, elevations, kind='linear', fill_value='extrapolate')
        elevations_smooth = elevation_spline(u_fine)

        x_inner = np.copy(x_smooth)
        y_inner = np.copy(y_smooth)

        nx = - (y_smooth[1:] - y_smooth[:-1]) / np.sqrt((x_smooth[1:] - x_smooth[:-1])**2 + (y_smooth[1:] - y_smooth[:-1])**2)
        ny = (x_smooth[1:] - x_smooth[:-1]) / np.sqrt((x_smooth[1:] - x_smooth[:-1])**2 + (y_smooth[1:] - y_smooth[:-1])**2)

        for i in range(len(x_inner) - 1):
            x_inner[i] -= thickness * nx[i]
            y_inner[i] -= thickness * ny[i]

        return x_smooth, y_smooth, x_inner, y_inner, elevations_smooth

    def _create_elevation_matrix(self, x_inner, y_inner, x_outer, y_outer, elevations):
        """Creates a matrix representation of the elevation data."""
        x_min, x_max = min(np.min(x_inner), np.min(x_outer)), max(np.max(x_inner), np.max(x_outer))
        y_min, y_max = min(np.min(y_inner), np.min(y_outer)), max(np.max(y_inner), np.max(y_outer))

        range_x, range_y = x_max - x_min, y_max - y_min
        scale_factor = self.image_resolution / max(range_x, range_y)
        
        image_width = int(range_x * scale_factor)
        image_height = int(range_y * scale_factor)
        elevation_matrix = np.zeros((image_width, image_height), dtype=np.float32)

        x_inner_scaled = ((x_inner - x_min) * scale_factor).astype(int)
        y_inner_scaled = ((y_inner - y_min) * scale_factor).astype(int)
        x_outer_scaled = ((x_outer - x_min) * scale_factor).astype(int)
        y_outer_scaled = ((y_outer - y_min) * scale_factor).astype(int)
        elevations_scaled = elevations - np.min(elevations)

        for i in range(len(x_inner_scaled) - 1):
            inner_start = (x_inner_scaled[i], y_inner_scaled[i])
            inner_end = (x_inner_scaled[i + 1], y_inner_scaled[i + 1])
            outer_start = (x_outer_scaled[i], y_outer_scaled[i])
            outer_end = (x_outer_scaled[i + 1], y_outer_scaled[i + 1])

            polygon_points = [inner_start, outer_start, outer_end, inner_end]
            rr, cc = polygon(np.array(polygon_points)[:, 0], np.array(polygon_points)[:, 1], elevation_matrix.shape)

            # Ensure valid indices
            valid_indices = (rr >= 0) & (rr < elevation_matrix.shape[0]) & (cc >= 0) & (cc < elevation_matrix.shape[1])
            elevation_matrix[rr[valid_indices], cc[valid_indices]] = elevations_scaled[i] + 0.1

        return elevation_matrix

    def _create_mesh(self):
        """Creates a trimesh object from the elevation matrix."""
        mesh = numpy2stl(self.elevation_matrix, fn=self.fn, scale=self.scale, mask_val=0.05, solid=True, min_thickness_percent=0)
        mesh.visual.face_colors= self.color
        return mesh
