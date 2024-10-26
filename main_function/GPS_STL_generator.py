import numpy as np

import trimesh
from main_function.STL_function import writeSTL
from main_function.GPS_function import parse_gps, AltimetryPlotter, load_gps_data, subsample_gps_data


def thick_vertices(latitude, longitude, thick=0.5):
    delta_latitude = np.diff(latitude)
    delta_longitude = np.diff(longitude)
    zero_indices = np.where(delta_longitude == 0)[0]

    if zero_indices.size > 0:
        delta_longitude[zero_indices] = 0.001
    
    # Calculate slope (m) for each point
    m = delta_latitude / delta_longitude

    # Calculate q for each point
    q = np.where(delta_longitude > 0,
                 latitude[:-1] - m * longitude[:-1] + thick * np.sqrt(m**2 + 1),
                 latitude[:-1] - m * longitude[:-1] - thick * np.sqrt(m**2 + 1))

    # Calculate shifted longitude for each point
    longitude_thick = longitude[:-1]/ (m**2 + 1) + (latitude[:-1] - q )* (m / (m**2 + 1)) 

    # Calculate shifted latitude for each point
    latitude_thick = m * longitude_thick + q

    if zero_indices.size > 0:
        longitude_thick[zero_indices] = longitude[zero_indices] + thick
        latitude_thick[zero_indices] = latitude[zero_indices]

    # Handle the last point separately
    longitude_thick_last = longitude[-1]/ (m[-1]**2 + 1) + (latitude[-1] - q[-1] )* (m[-1] / (m[-1]**2 + 1)) 
    latitude_thick_last = m[-1] * longitude_thick_last + q[-1]

    shifted_latitude = np.concatenate([latitude_thick, [latitude_thick_last]])
    shifted_longitude = np.concatenate([longitude_thick, [longitude_thick_last]])

    return shifted_latitude, shifted_longitude


def generate_surface_mesh(subsampled_data, scale_factor, fn = 'tmp_STL/road_STL.stl'):
    latitudes = subsampled_data[:, 0] * scale_factor
    longitudes = subsampled_data[:, 1] * scale_factor 
    elevations = subsampled_data[:, 2]
    min_elevation = np.ones(len(elevations)) * np.min(elevations)

    latitudes_thick, longitude_thick = thick_vertices(latitudes, longitudes, 1/5000*scale_factor) # Check this last value

    vertices_1 = np.column_stack((latitudes, longitudes, elevations))
    vertices_2 = np.column_stack((latitudes_thick, longitude_thick, elevations))
    vertices_3 = np.column_stack((latitudes, longitudes, min_elevation))
    vertices_4 = np.column_stack((latitudes_thick, longitude_thick, min_elevation))
    
    num_points = len(latitudes)
    facets = []

    n1 = np.zeros(3)

    for i in range(num_points - 1):
        # Upper surface face
        facet1 =  np.concatenate([n1, vertices_1[i], vertices_2[i], vertices_1[i+1]])
        facets.append(facet1)
        facet2 =  np.concatenate([n1, vertices_1[i+1], vertices_2[i+1], vertices_2[i]])
        facets.append(facet2)

        # Lower surface face
        facet3 =  np.concatenate([n1, vertices_3[i], vertices_4[i], vertices_3[i+1]])
        facets.append(facet3)
        facet4 =  np.concatenate([n1, vertices_3[i+1], vertices_4[i+1], vertices_4[i]])
        facets.append(facet4)

        # Side surface face
        facet5 =  np.concatenate([n1, vertices_1[i], vertices_3[i], vertices_1[i+1]])
        facets.append(facet5)
        facet6 =  np.concatenate([n1, vertices_1[i+1], vertices_3[i+1], vertices_3[i]])
        facets.append(facet6)
        
        facet7 =  np.concatenate([n1, vertices_2[i], vertices_4[i], vertices_2[i+1]])
        facets.append(facet7)
        facet8 =  np.concatenate([n1, vertices_2[i+1], vertices_4[i+1], vertices_4[i]])
        facets.append(facet8)

    # The last faces
    facet =  np.concatenate([n1, vertices_1[-1], vertices_2[-1], vertices_3[-1]])
    facets.append(facet)
    facet =  np.concatenate([n1, vertices_2[-1], vertices_4[-1], vertices_3[-1]])
    facets.append(facet)

    writeSTL(facets, fn)

    mesh = trimesh.load(fn)

    trimesh.repair.fill_holes(mesh)
    trimesh.repair.fix_normals(mesh)
    trimesh.repair.fix_inversion(mesh)
    trimesh.repair.fix_winding(mesh)

    mesh.export(fn)

    return mesh



def GPStoSTL (path_gps = 'example/selvino/selvino.gpx', selection = True, output_path = 'tmp_STL/selected_data.txt'):
    if selection == True:
        file_path = path_gps
        distances, elevation_data = parse_gps(file_path)
        AltimetryPlotter(distances, elevation_data, output_path)

    gps_data = load_gps_data(output_path)
    latitudes = gps_data[:, 0]
    longitudes = gps_data[:, 1]
    elevations = gps_data[:, 2]

    # Subsample the data
    subsampled_gps_data = subsample_gps_data(latitudes, longitudes, elevations, min_distance=2, max_distance=350)

    # debug_visualization(gps_data, subsampled_gps_data)

    return generate_surface_mesh(subsampled_gps_data, scale_factor=10000)