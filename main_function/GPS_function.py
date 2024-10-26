import gpxpy
import gpxpy.gpx
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector, Button
from haversine import haversine, Unit


def parse_gps(file_path):
    with open(file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
    
    elevation_data = []
    distances = []
    total_distance = 0
    previous_point = None
    
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if previous_point:
                    dist = haversine((previous_point.latitude, previous_point.longitude), (point.latitude, point.longitude), unit=Unit.METERS)
                    total_distance += dist/1000
                else:
                    dist = 0
                distances.append(total_distance)
                elevation_data.append((point.latitude, point.longitude, point.elevation))
                previous_point = point
    
    return distances, elevation_data

class AltimetryPlotter:
    def __init__(self, distances, elevation_data, output_path = 'tmp_STL/selected_data.txt'):
        self.distances = distances
        self.elevation_data = elevation_data
        self.elevations = [point[2] for point in elevation_data]
        self.fig, self.ax = plt.subplots(figsize=(10, 5))
        self.span = None
        self.selection = (None, None)
        self.output_path = output_path
        self._create_plot()
    
    def _create_plot(self):
        self.ax.plot(self.distances, self.elevations, label='Elevation Profile')
        self.ax.set_xlabel('Distance (meters)')
        self.ax.set_ylabel('Elevation (meters)')
        self.ax.set_title('Elevation Profile with Interactive Selection')
        self.ax.grid(True)
        
        self.span = SpanSelector(self.ax, self.onselect, 'horizontal', useblit=True,
                                 props=dict(alpha=0.5, facecolor='red'))

        ax_button = plt.axes([0.8, 0.01, 0.1, 0.075])
        self.button = Button(ax_button, 'Finalize')
        self.button.on_clicked(self.finalize_selection)
        
        plt.show()

    def onselect(self, xmin, xmax):
        self.selection = (xmin, xmax)
        self.update_span()

    def update_span(self):
        self.span.extents = self.selection
        print(f"Updated range: {self.selection[0]} to {self.selection[1]} meters")

    def finalize_selection(self, event):
        xmin, xmax = self.selection
        if xmin is not None and xmax is not None:
            print(f"Finalized selection: {xmin} to {xmax} meters")
            indices = [i for i, d in enumerate(self.distances) if xmin <= d <= xmax]
            selected_data = [self.elevation_data[i] for i in indices]
            
            with open(self.output_path, 'w') as f:
                for point in selected_data:
                    f.write(f"{point[0]},{point[1]},{point[2]}\n")
            
            print(f"Selected data saved with {len(selected_data)} points.")
            plt.close(self.fig)  # Close the plot when finalized
        else:
            print("No selection made")


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