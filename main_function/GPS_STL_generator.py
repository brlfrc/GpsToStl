import numpy as np

from main_function.GPS_function import parse_gps, AltimetryPlotter, load_gps_data
from main_function.STL_function import numpy2stl

from skimage.draw import polygon
from scipy.interpolate import splprep, splev, interp1d


def GPStoSTL (path_gps = 'example/selvino/selvino.gpx', selection = True, output_path = 'tmp_STL/selected_data.txt'):
    if selection == True:
        file_path = path_gps
        distances, elevation_data = parse_gps(file_path)
        selection = AltimetryPlotter(distances, elevation_data, output_path)
        selected_distance = selection.get_selected_distance()

    gps_data = load_gps_data(output_path)
    latitudes = gps_data[:, 0]
    longitudes = gps_data[:, 1]
    elevations = gps_data[:, 2]

    x = latitudes
    y = longitudes
    thickness = np.min(np.diff(latitudes))
    
    x_smooth, y_smooth, x_inner, y_inner, elevations_smooth = spline_inner_curve(x, y, elevations, selected_distance, thickness)
    uphill_matrix = generate_elevation_matrix(x_smooth, y_smooth, x_inner, y_inner, elevations_smooth,image_resolution= 800)


    return numpy2stl(uphill_matrix, fn = 'tmp_STL/uphill_tmp_STL.stl',scale=100, mask_val=1, solid=True,  min_thickness_percent=0)




def spline_inner_curve(x, y, elevations, selection_len, thickness=None):
    thickness = np.min(np.diff(x)) if thickness is None else thickness
    
    tck, u = splprep([x, y], s=0)
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

def generate_elevation_matrix(x_inner, y_inner, x_outer, y_outer, elevations, image_resolution=3000):
    x_min, x_max = min(np.min(x_inner), np.min(x_outer)), max(np.max(x_inner), np.max(x_outer))
    y_min, y_max = min(np.min(y_inner), np.min(y_outer)), max(np.max(y_inner), np.max(y_outer))

    range_x, range_y = x_max - x_min, y_max - y_min
    scale_factor = image_resolution / max(range_x, range_y)  # Fattore di scala unico per mantenere le proporzioni
    
    image_width = int(range_x * scale_factor)
    image_height = int(range_y * scale_factor)
    elevation_matrix = np.zeros((image_width,image_height), dtype=np.float32) 

    x_inner_scaled = ((x_inner - x_min) * scale_factor).astype(int)
    y_inner_scaled = ((y_inner - y_min) * scale_factor).astype(int)
    x_outer_scaled = ((x_outer - x_min) * scale_factor).astype(int)
    y_outer_scaled = ((y_outer - y_min) * scale_factor).astype(int)
    elevations_scaled = elevations-np.min(elevations)

    for i in range(len(x_inner_scaled) - 1):
        inner_start = (x_inner_scaled[i], y_inner_scaled[i])
        inner_end = (x_inner_scaled[i + 1], y_inner_scaled[i + 1])
        outer_start = (x_outer_scaled[i], y_outer_scaled[i])
        outer_end = (x_outer_scaled[i + 1], y_outer_scaled[i + 1])

        polygon_points = [inner_start, outer_start, outer_end, inner_end]
        rr, cc = polygon(np.array(polygon_points)[:, 0], np.array(polygon_points)[:, 1], elevation_matrix.shape)

        # Assicurati che rr e cc siano nei limiti della matrice
        valid_indices = (rr >= 0) & (rr < elevation_matrix.shape[0]) & (cc >= 0) & (cc < elevation_matrix.shape[1])
        elevation_matrix[rr[valid_indices], cc[valid_indices]] = elevations_scaled[i]+0.1 
  

    return elevation_matrix