import gpxpy
import matplotlib.pyplot as plt
import numpy as np
from stl import mesh

def thick_vertices(latitude, longitude, thick=0.5):
    delta_latitude = np.diff(latitude)
    delta_longitude = np.diff(longitude)
    zero_indices = np.where(delta_longitude == 0)[0]
    delta_longitude[zero_indices] = 0.001
    # Calculate slope (m) for each point
    m = delta_latitude / delta_longitude

    # Calculate q for each point
    q = np.where(delta_longitude > 0,
                 latitude[:-1] - m * longitude[:-1] + thick * np.sqrt(m**2 + 1),
                 latitude[:-1] - m * longitude[:-1] - thick * np.sqrt(m**2 + 1))

    # Calculate shifted longitude for each point
    longitude_thick = longitude[:-1]/ (m**2 + 1) + (latitude[:-1] - q )* (m / (m**2 + 1)) 
    longitude_thick[zero_indices] = longitude[zero_indices] + thick

    # Calculate shifted latitude for each point
    latitude_thick = m * longitude_thick + q
    latitude_thick[zero_indices] = latitude[zero_indices]

    # Handle the last point separately
    longitude_thick_last = longitude[-1] - thick
    latitude_thick_last = latitude[-1]

    shifted_latitude = np.concatenate([latitude_thick, [latitude_thick_last]])
    shifted_longitude = np.concatenate([longitude_thick, [longitude_thick_last]])

    return shifted_latitude, shifted_longitude

def is_point_behind_line(p, line_start, line_end):
    # Check if point p is behind the line defined by line_start and line_end
    cross_product = np.cross(line_end - line_start, p - line_start)
    return cross_product[2] < 0

def remove_overlapping_points(vertices_surface, vertices_thick_line):
    filtered_vertices_surface = [vertices_surface[0]]
    filtered_vertices_thick_line = [vertices_thick_line[0]]

    for i in range(1, len(vertices_surface)-1):
        # Check if the next two vertices are not behind the line
        if not (is_point_behind_line(vertices_surface[i], vertices_surface[i - 1], vertices_thick_line[i-1]) or
                is_point_behind_line(vertices_thick_line[i], vertices_surface[i - 1], vertices_thick_line[i-1])):
            filtered_vertices_surface.append(vertices_surface[i])
            filtered_vertices_thick_line.append(vertices_thick_line[i])

    # Add the last point
    filtered_vertices_surface.append(vertices_surface[-1])
    filtered_vertices_thick_line.append(vertices_thick_line[-1])

    return np.array(filtered_vertices_surface), np.array(filtered_vertices_thick_line)

# Define file paths
gpx_file_path = 'stelvio/stelvio.gpx'
output_file_path = 'stelvio/stelvio.stl'

# Read GPX File
gpx_file = open(gpx_file_path, 'r')
gpx = gpxpy.parse(gpx_file)
gpx_file.close()

# Extract GPS Data
latitudes = []
longitudes = []
elevations = []

for track in gpx.tracks:
    for segment in track.segments:
        for i, point in enumerate(segment.points):
            # Select every eigth point
            if i % 3== 0:
                latitudes.append(point.latitude)
                longitudes.append(point.longitude)
                elevations.append(point.elevation)

# Find Max Elevation Index
max_elevation_index = elevations.index(max(elevations))

# Filter Points Until Max Elevation
latitudes_filtered = latitudes[:max_elevation_index + 1]
longitudes_filtered = longitudes[:max_elevation_index + 1]
elevations_filtered = elevations[:max_elevation_index + 1]

# Scale Latitude and Longitude
latitudes_filtered = np.array(latitudes_filtered) * 700
longitudes_filtered = np.array(longitudes_filtered) * 800
elevations_filtered = np.array(elevations_filtered) / 30

# Create 3D Model
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot(latitudes_filtered, longitudes_filtered, elevations_filtered, 'b-')

# Print some information about the data
print(f"Number of points: {len(latitudes_filtered)}")
print(f"Latitude range: {min(latitudes_filtered)} to {max(latitudes_filtered)}")
print(f"Longitude range: {min(longitudes_filtered)} to {max(longitudes_filtered)}")
print(f"Elevation range: {min(elevations_filtered)} to {max(elevations_filtered)}")

# Normalize Data
latitudes = np.array(latitudes_filtered) - min(latitudes_filtered)
longitudes = np.array(longitudes_filtered) - min(longitudes_filtered)
elevations = np.array(elevations_filtered) - min(elevations_filtered)

# Create vertices for the thick line
vertices_surface = np.column_stack((latitudes, longitudes, elevations))

latitudes_thick, longitude_thick = thick_vertices(latitudes, longitudes, 0.2)
vertices_thick_line = np.column_stack((latitudes_thick, longitude_thick, elevations))

# Remove overlapping points
vertices_surface, vertices_thick_line = remove_overlapping_points(vertices_surface, vertices_thick_line)

# Create vertices for the projection with distinct elevation
vertices_projection = np.column_stack((vertices_surface[:, 0], vertices_surface[:, 1], np.full_like(vertices_surface[:, 2], min(elevations))))
vertices_projection_2 = np.column_stack((vertices_thick_line[:, 0], vertices_thick_line[:, 1], np.full_like(vertices_thick_line[:, 2], min(elevations))))

# Combine the two sets of vertices
vertices = np.vstack((vertices_surface, vertices_thick_line, vertices_projection, vertices_projection_2))

# Create faces for the flat surface
num_points = len(vertices_surface)
faces_surface_1 = np.array([[i, (i + 1) , i + num_points] for i in range(0, num_points-1)])
faces_surface_2 = np.array([[i + num_points, (i + 1) + num_points, i + 1] for i in range(0, num_points-1)])

# Create faces for the projection
faces_projection_1 =2*num_points + np.array([[i, (i + 1) , i + num_points] for i in range(0, num_points-1)])
faces_projection_2 =2*num_points + np.array([[i + num_points, (i + 1) + num_points, i + 1] for i in range(0, num_points-1)])

# Create faces between the flat surface and projection
faces_lateral_1 = np.array([[i, (i + 1), i + 2*num_points] for i in range(num_points-1)])
faces_lateral_2 = np.array([[(i + 1), i + 2*num_points, (i + 1) + 2*num_points] for i in range(num_points-1)])
faces_lateral_3 = num_points + np.array([[i, (i + 1), i + 2*num_points] for i in range(num_points-1)])
faces_lateral_4 = num_points + np.array([[(i + 1), i + 2*num_points, (i + 1) + 2*num_points] for i in range(num_points-1)])

faces_lateral_5 = num_points + np.array([[i, num_points+i, i + 2*num_points] for i in range(num_points-1)])
faces_lateral_6 = num_points + np.array([[num_points+i, i + 2*num_points, 3*num_points+i] for i in range(num_points-1)])

# Combine all sets of faces
faces = np.vstack((faces_surface_1, faces_surface_2, faces_projection_1, faces_projection_2,
                   faces_lateral_1,faces_lateral_2,faces_lateral_3,faces_lateral_4, faces_lateral_5, faces_lateral_6))

# Print information about the mesh
print(f"Number of vertices in the mesh: {len(vertices)}")
print(f"Number of faces in the mesh: {len(faces)}")

# Save STL file

mesh_data = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
for i, face in enumerate(faces):
    for j in range(3):
        mesh_data.vectors[i][j] = vertices[face[j] % len(vertices)]

mesh_data.save(output_file_path)
print(f"STL file saved to: {output_file_path}")
