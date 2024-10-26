import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from haversine import haversine, Unit
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from stl import mesh
import trimesh

def load_gps_data(file_path):
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            lat, lon, ele = map(float, line.strip().split(','))
            data.append((lat, lon, ele))
    
    return np.array(data)

def subsample_gps_data(latitudes, longitudes, elevations,  min_distance=50, max_distance=300):
    subsampled_data = []
    last_point = (latitudes[0], longitudes[0], elevations[0])
    subsampled_data.append(last_point)
    print(f"Number of original points: {len(latitudes)}")

    for i in range(1, len(latitudes)):
        current_point = (latitudes[i], longitudes[i], elevations[i])
        distance = haversine((last_point[0], last_point[1]), (current_point[0], current_point[1]), unit=Unit.METERS)
        
        if min_distance <= distance <= max_distance:
            subsampled_data.append(current_point)
            last_point = current_point  # Update last point
    
    
    print(f"Number of subsampled points: {len(subsampled_data)}")    
    return np.array(subsampled_data)

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

def generate_faces(num_points):
    faces = []
    for i in range(num_points - 1):
        # Upper surface face
        faces.append([i, i + 1, i + num_points])
        faces.append([i + 1, i + num_points + 1, i + num_points])

        # Lower surface
        faces.append([i + 2* num_points, i + 2* num_points + 1, i + 3*num_points])
        faces.append([i + 1 + 2* num_points,  i + 3* num_points + 1, i + 3 * num_points])
        
        # Side faces connecting to the projection plane
        faces.append([i, i + 1, i + 2 * num_points])
        faces.append([i + 1, i + 1 + 2 * num_points, i + 2 * num_points])

        faces.append([i + num_points, i + 1 + num_points, i + 3 * num_points])
        faces.append([i + 1 + num_points, i + 1 + 3 * num_points, i + 3 * num_points])
    
    # The last faces
    faces.append([num_points-1, 2*num_points-1, 3*num_points-1])
    faces.append([2*num_points-1, 4*num_points-1, 3*num_points-1])
    
    return np.array(faces)

def generate_surface_mesh(subsampled_data, scale_factor):
    latitudes = subsampled_data[:, 0] * scale_factor
    longitudes = subsampled_data[:, 1] * scale_factor 
    elevations = subsampled_data[:, 2]
    min_elevation = np.ones(len(elevations)) * np.min(elevations)

    latitudes_thick, longitude_thick = thick_vertices(latitudes, longitudes, 1/5000*scale_factor) # Check this last value

    vertices_1 = np.column_stack((latitudes, longitudes, elevations))
    vertices_2 = np.column_stack((latitudes_thick, longitude_thick, elevations))
    vertices_3 = np.column_stack((latitudes, longitudes, min_elevation))
    vertices_4 = np.column_stack((latitudes_thick, longitude_thick, min_elevation))
    
    vertices= np.vstack((vertices_1, vertices_2, vertices_3, vertices_4))
    num_points = len(latitudes)

    faces = generate_faces(num_points)

    # print(f"Number of vertices in the mesh: {len(vertices)}")
    # print(f"Number of faces in the mesh: {len(faces)}")

    # mesh_data = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    # for i, face in enumerate(faces):
    #     for j in range(3):
    #         mesh_data.vectors[i][j] = vertices[face[j] % len(vertices)]

    # mesh_data.save('extruded_uphill_model.stl')
    # print(f"STL file saved to: {'extruded_uphill_model.stl'}")

    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

    trimesh.repair.fix_normals(mesh)  # Assicura che tutte le normali siano consistenti
    trimesh.repair.fill_holes(mesh)   # Chiude eventuali buchi nella mesh
    # trimesh.repair.remove_duplicate_faces(mesh)  # Rimuove facce degeneri
    trimesh.repair.fix_inversion(mesh)
    # Esporta la mesh come file STL
    mesh.export('extruded_uphill_model.stl')
    print(f"STL file saved to: {'extruded_uphill_model.stl'}")

    fig = plt.figure(figsize=(18, 6))

    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(vertices_1[:,0], vertices_1[:,1], vertices_1[:,2], c='blue', marker='o', label='original point')
    ax.scatter(vertices_2[:,0], vertices_2[:,1], vertices_2[:,2], c='red', marker='x', label='thick point')
    ax.scatter(vertices_3[:,0], vertices_3[:,1], vertices_3[:,2], c='green', marker='x', label='thick point')
    ax.scatter(vertices_4[:,0], vertices_4[:,1], vertices_4[:,2], c='yellow', marker='x', label='thick point')
    ax.set_xlabel('Latitude')
    ax.set_ylabel('Longitude')
    ax.set_zlabel('Elevation') 
    ax.set_title('GPS Points')
    ax.legend()

    plt.tight_layout()
    plt.show()
    

    fig = plt.figure(figsize=(12, 12))
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(vertices_1[:,0], vertices_1[:,1], vertices_1[:,2], c='blue', marker='o', label='original point')

    # Create a Poly3DCollection object
    poly3d = Poly3DCollection(vertices[faces], alpha=.25, linewidths=1, edgecolors='k')

    # Add the collection to the plot
    ax.add_collection3d(poly3d)

    # Set plot limits
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    
    plt.show()
    return mesh

ASCII_FACET = """  facet normal  {face[0]:e}  {face[1]:e}  {face[2]:e}
    outer loop
      vertex    {face[3]:e}  {face[4]:e}  {face[5]:e}
      vertex    {face[6]:e}  {face[7]:e}  {face[8]:e}
      vertex    {face[9]:e}  {face[10]:e}  {face[11]:e}
    endloop
  endfacet"""


def _build_ascii_stl(facets):
    """returns a list of ascii lines for the stl file """

    lines = ['solid ffd_geom', ]
    for facet in facets:
        lines.append(ASCII_FACET.format(face=facet))
    lines.append('endsolid ffd_geom')
    return lines


def writeSTL(facets, file_name):
    """writes an ASCII or binary STL file"""

    f = open(file_name, 'wb')
    
    lines = _build_ascii_stl(facets)
    lines_ = "\n".join(lines).encode("UTF-8")
    f.write(lines_)

    f.close()

def generate_surface_mesh_2_method(subsampled_data, scale_factor):
    latitudes = subsampled_data[:, 0] * scale_factor
    longitudes = subsampled_data[:, 1] * scale_factor 
    elevations = subsampled_data[:, 2]
    min_elevation = np.ones(len(elevations)) * np.min(elevations)

    latitudes_thick, longitude_thick = thick_vertices(latitudes, longitudes, 1/5000*scale_factor) # Check this last value

    vertices_1 = np.column_stack((latitudes, longitudes, elevations))
    vertices_2 = np.column_stack((latitudes_thick, longitude_thick, elevations))
    vertices_3 = np.column_stack((latitudes, longitudes, min_elevation))
    vertices_4 = np.column_stack((latitudes_thick, longitude_thick, min_elevation))
    
    vertices= np.vstack((vertices_1, vertices_2, vertices_3, vertices_4))
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

    fn = 'mesh.stl'
    writeSTL(facets, fn)

    mesh = trimesh.load("mesh.stl")

    # Riorienta le facce in modo coerente
    # trimesh.repair.orient_faces(mesh)
    print(len(trimesh.repair.broken_faces(mesh, color=None)))

    trimesh.repair.fill_holes(mesh)
    trimesh.repair.fix_normals(mesh)
    trimesh.repair.fix_inversion(mesh)
    trimesh.repair.fix_winding(mesh)

    print(len(trimesh.repair.broken_faces(mesh, color=None)))
    mesh.export('repair_mesh.stl')

    # Verifica e corregge le normali
    return mesh

def debug_visualization(gps_data_original, subsampled_gps_data):
    latitudes = gps_data_original[:, 0]
    longitudes = gps_data_original[:, 1]
    elevations = gps_data_original[:, 2]

    latitudes_sub = subsampled_gps_data[:, 0]
    longitudes_sub = subsampled_gps_data[:, 1]
    elevations_sub = subsampled_gps_data[:, 2]

    print ('Original GPS data: '+str(len(latitudes))+'.\n Selected GPS data: '+str(len(latitudes_sub)))
    fig = plt.figure(figsize=(18, 6))

    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(latitudes, longitudes, elevations, c='blue', marker='o', label='original point')
    ax.scatter(latitudes_sub, longitudes_sub, elevations_sub, c='red', marker='x', label='subsample point')
    ax.set_xlabel('Latitude')
    ax.set_ylabel('Longitude')
    ax.set_zlabel('Elevation') 
    ax.set_title('GPS Points')
    ax.legend()

    plt.tight_layout()
    plt.show()


# Example usage
file_path = 'selected_gps_data.txt'
gps_data = load_gps_data(file_path)
latitudes = gps_data[:, 0]
longitudes = gps_data[:, 1]
elevations = gps_data[:, 2]

# Subsample the data
subsampled_gps_data = subsample_gps_data(latitudes, longitudes, elevations, min_distance=2, max_distance=350)

# debug_visualization(gps_data, subsampled_gps_data)

surface_mesh = generate_surface_mesh_2_method(subsampled_gps_data, scale_factor=10000)
surface_mesh.show()


