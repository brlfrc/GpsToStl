import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import splprep, splev, interp1d
from shapely.geometry import LineString, Point, MultiPoint, GeometryCollection
from main_function.STL_function import writeSTL
import trimesh
from main_function.GPS_function import parse_gps, AltimetryPlotter, load_gps_data


# Questo è un metodo alternativo che però non funziona, riesco a generare i punti correttamente ma poi non mi genera un STL valido
# Credo che quindi l'errore sia nel generatore del STL
def spline_fitter (x, y, elevations, selection_len):
    tck, u = splprep([x, y], s=0)
    u_fine = np.linspace(0, 1, 1000*int(selection_len+1))
    x_smooth, y_smooth = splev(u_fine, tck)
    elevation_spline = interp1d(u, elevations, kind='linear', fill_value='extrapolate')
    elevations_smooth = elevation_spline(u_fine)

    dx, dy = splev(u_fine, tck, der=1)
    d2x, d2y = splev(u_fine, tck, der=2)
    
    norm = np.sqrt(dx**2 + dy**2)
    kappa = (dx * d2y - dy * d2x) / (norm**3)
    return x_smooth, y_smooth, elevations_smooth, kappa, dx, dy, u_fine

def segment_curve(kappa, threshold_std_dev, num_point_default=50):
    kappa_mean = np.mean(kappa)
    kappa_std = np.std(kappa)
    threshold = kappa_mean + threshold_std_dev * kappa_std
    
    sections = ['straight'] * len(kappa)
    last_turn_end = -num_point_default  # Initialize for the first turn without limitations

    for i, curv in enumerate(kappa):
        if abs(curv) > threshold:
            # Calculate the distance from the previous turn
            distance_from_prev_turn = i - last_turn_end
            
            # Check for the next turn
            if i + 1 < len(kappa):
                # Find the next turn's position
                next_turn_start = i + 1
                while next_turn_start < len(kappa) and abs(kappa[next_turn_start]) <= threshold:
                    next_turn_start += 1
                
                distance_to_next_turn = next_turn_start - i

            else:
                distance_to_next_turn = float('inf')  # No next turn

            # Determine the number of points to include before and after the turn
            num_point_before = distance_from_prev_turn // 2 if distance_from_prev_turn < 2*num_point_default else num_point_default
            num_point_after = distance_to_next_turn // 2 if distance_to_next_turn < 2*num_point_default else num_point_default
            
            # Assign the interval as "turn"
            start = max(0, i - num_point_before)
            end = min(len(kappa), i + num_point_after + 1)
            for j in range(start, end):
                sections[j] = 'turn'

            # Update the last turn end for calculating distance
            last_turn_end = end

    # Convert sections into intervals (type, start, end)
    intervals = []
    start = 0
    for i in range(1, len(sections)):
        if sections[i] != sections[i - 1]:
            intervals.append((sections[start], start, i))
            start = i
    intervals.append((sections[start], start, len(sections)))  # Add last interval
    
    return intervals

def create_inner_outer_curves(x_smooth, y_smooth, kappa, dx, dy, segments, thickness):
    # Calculate the norm and normal vectors
    norm = np.sqrt(dx**2 + dy**2)
    nx = -dy / norm
    ny = dx / norm
    
    # Initialize inner and outer curves as copies of the smoothed curve
    x_inner, y_inner = np.copy(x_smooth), np.copy(y_smooth)
    x_outer, y_outer = np.copy(x_smooth), np.copy(y_smooth)

    for _, start, end in segments:
        # Calculate the mean curvature of the segment to determine offset direction
        mean_kappa = np.mean(kappa[start:end])
        direction = 1 if mean_kappa >= 0 else -1

        for i in range(start, end):
            # For positive curvature, offset outer curve while inner curve remains on the smoothed curve
            if direction == 1:
                x_outer[i] = x_smooth[i] + thickness * nx[i]
                y_outer[i] = y_smooth[i] + thickness * ny[i]
                # Inner curve remains the smoothed curve itself
                x_inner[i], y_inner[i] = x_smooth[i], y_smooth[i]
            # For negative curvature, offset inner curve while outer curve remains on the smoothed curve
            else:
                x_inner[i] = x_smooth[i] - thickness * nx[i]
                y_inner[i] = y_smooth[i] - thickness * ny[i]
                # Outer curve remains the smoothed curve itself
                x_outer[i], y_outer[i] = x_smooth[i], y_smooth[i]
                
    return x_inner, y_inner, x_outer, y_outer
   

def downsample_curve(x_inner, y_inner, x_outer, y_outer, elevations_smooth, segments, straight_factor=10, turn_factor=2):
    x_inner_downsampled, y_inner_downsampled = [], []
    x_outer_downsampled, y_outer_downsampled = [], []
    elevations_downsampled = [] 

    for interval_type, start, end in segments:
        # Choose the downsampling factor based on the interval type
        factor = straight_factor if interval_type == 'straight' else turn_factor

        # Downsample the points in the current segment
        x_inner_downsampled.extend(x_inner[start:end:factor])
        y_inner_downsampled.extend(y_inner[start:end:factor])
        x_outer_downsampled.extend(x_outer[start:end:factor])
        y_outer_downsampled.extend(y_outer[start:end:factor])
        
        # Downsample the elevations in the same manner
        elevations_downsampled.extend(elevations_smooth[start:end:factor])


    x_inner_downsampled = np.array(x_inner_downsampled, dtype=float)
    y_inner_downsampled = np.array(y_inner_downsampled, dtype=float)
    x_outer_downsampled = np.array(x_outer_downsampled, dtype=float)
    y_outer_downsampled = np.array(y_outer_downsampled, dtype=float)
    elevations_downsampled = np.array(elevations_downsampled, dtype=float)

    return x_inner_downsampled, y_inner_downsampled, x_outer_downsampled, y_outer_downsampled, elevations_downsampled


def check_intersections(x_inner, y_inner, x_outer, y_outer):
    # Convert points to line segments
    inner_line = LineString([(x_inner[i], y_inner[i]) for i in range(len(x_inner))])
    outer_line = LineString([(x_outer[i], y_outer[i]) for i in range(len(x_outer))])

    # Check for intersections
    if inner_line.intersects(outer_line):
        intersection_points = inner_line.intersection(outer_line)

        if intersection_points.is_empty:
            return False, []  # No intersection points found
        elif isinstance(intersection_points, Point):
            # Single intersection point
            return True, [(intersection_points.x, intersection_points.y)]
        elif isinstance(intersection_points, MultiPoint):
            # Multiple intersection points
            return True, [(pt.x, pt.y) for pt in intersection_points.geoms]
        elif isinstance(intersection_points, GeometryCollection):
            # Mixed geometries; filter out Points
            points = [(geom.x, geom.y) for geom in intersection_points.geoms if isinstance(geom, Point)]
            return bool(points), points
        else:
            return False, []  # Unexpected case: No valid intersection points
    else:
        return False, []


def generate_surface_mesh(x_inner, y_inner, x_outer, y_outer, elevations, scale_factor, fn = 'tmp_STL/road_STL.stl'):
    latitudes_inner = x_inner*scale_factor
    latitudes_outer = x_outer*scale_factor
    longitudes_inner = y_inner*scale_factor
    longitudes_outer = y_outer*scale_factor
    
    min_elevation = np.ones(len(elevations)) * np.min(elevations)

    vertices_1 = np.column_stack((latitudes_inner, longitudes_inner, elevations))
    vertices_2 = np.column_stack((latitudes_outer, longitudes_outer, elevations))
    vertices_3 = np.column_stack((latitudes_inner, longitudes_inner, min_elevation))
    vertices_4 = np.column_stack((latitudes_outer, longitudes_outer, min_elevation))
    
    num_points = len(latitudes_inner)
    facets = []

    n1 = np.zeros(3)

    for i in range(num_points - 1):
        # Upper surface faces
        facets.append(np.concatenate([n1, vertices_1[i], vertices_1[i + 1], vertices_2[i]]))
        facets.append(np.concatenate([n1, vertices_2[i], vertices_1[i + 1], vertices_2[i + 1]]))

        # Lower surface faces
        facets.append(np.concatenate([n1, vertices_3[i], vertices_4[i], vertices_3[i + 1]]))
        facets.append(np.concatenate([n1, vertices_4[i], vertices_4[i + 1], vertices_3[i + 1]]))

        # Side surface faces
        facets.append(np.concatenate([n1, vertices_1[i], vertices_3[i], vertices_1[i + 1]]))
        facets.append(np.concatenate([n1, vertices_1[i + 1], vertices_3[i], vertices_3[i + 1]]))
        
        facets.append(np.concatenate([n1, vertices_2[i], vertices_2[i + 1], vertices_4[i]]))
        facets.append(np.concatenate([n1, vertices_2[i + 1], vertices_4[i + 1], vertices_4[i]]))

        # facets.append(np.concatenate([n1, vertices_1[i], vertices_2[i], vertices_3[i]]))
        # facets.append(np.concatenate([n1, vertices_2[i], vertices_4[i], vertices_3[i]]))

        # facets.append(np.concatenate([n1, vertices_1[i + 1], vertices_2[i + 1], vertices_3[i + 1]]))
        # facets.append(np.concatenate([n1, vertices_2[i + 1], vertices_4[i + 1], vertices_3[i + 1]]))

    # The last faces
    facet =  np.concatenate([n1, vertices_1[-1], vertices_2[-1], vertices_3[-1]])
    facets.append(facet)
    facet =  np.concatenate([n1, vertices_2[-1], vertices_4[-1], vertices_3[-1]])
    facets.append(facet)

    writeSTL(facets, fn)

    mesh = trimesh.load(fn)

    # trimesh.repair.fill_holes(mesh)
    # # trimesh.repair.fix_normals(mesh)
    # # trimesh.repair.fix_inversion(mesh)
    # trimesh.repair.fix_winding(mesh)
    # # trimesh.repair.fill_holes(mesh)


    # mesh.export(fn)

    return mesh

path_gps = 'example/selvino/selvino.gpx'
output_path = 'tmp_STL/selected_data.txt'
file_path = path_gps
distances, elevation_data = parse_gps(file_path)
selection = AltimetryPlotter(distances, elevation_data, output_path)
selected_distance = selection.get_selected_distance()
 
gps_data = load_gps_data(output_path)
latitudes = gps_data[:, 0]
longitudes = gps_data[:, 1]
elevations = gps_data[:, 2]


# Parametri e input
x = latitudes
y = longitudes
threshold_std_dev = 3
thickness = np.min(np.diff(latitudes))

# Calcoli
x_smooth, y_smooth, elevations_smooth, kappa, dx, dy, u_fine = spline_fitter(x, y, elevations,selected_distance)

sezioni = segment_curve(kappa, threshold_std_dev, num_point_default=50)
# Calculate inner and outer curves
x_inner, y_inner, x_outer, y_outer = create_inner_outer_curves(x_smooth, y_smooth, kappa, dx, dy, sezioni, thickness)
x_inner_downsampled, y_inner_downsampled, x_outer_downsampled, y_outer_downsampled, elevations_downsampled  = downsample_curve(x_inner, y_inner, x_outer, y_outer, elevations_smooth, sezioni, straight_factor=10, turn_factor=2)


mesh = generate_surface_mesh(x_inner, y_inner, x_outer, y_outer, elevations, scale_factor=1000, fn = 'tmp_STL/road_STL.stl')