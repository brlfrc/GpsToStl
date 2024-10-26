import numpy as np
import matplotlib.pyplot as plt



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