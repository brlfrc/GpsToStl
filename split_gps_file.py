import gpxpy

def filter_and_save_gps_data(input_gpx_path, output_gpx_path, altitude_threshold):
    # Read GPX File
    with open(input_gpx_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    # Find the index of the first point with altitude above the threshold
    index_threshold = next((i for i, point in enumerate(gpx.tracks[0].segments[0].points) if point.elevation < altitude_threshold), None)

    if index_threshold is not None:
        # Create a new GPX object
        selected_gpx = gpxpy.gpx.GPX()

        # Create a new track and segment
        track = gpxpy.gpx.GPXTrack()
        segment = gpxpy.gpx.GPXTrackSegment()

        # Add points after the threshold to the new segment
        segment.points = gpx.tracks[0].segments[0].points[index_threshold:]

        # Add the segment to the track
        track.segments.append(segment)

        # Add the track to the GPX object
        selected_gpx.tracks.append(track)

        # Save the selected GPX data to a new file
        with open(output_gpx_path, 'w') as output_gpx_file:
            output_gpx_file.write(selected_gpx.to_xml())
    else:
        print(f"No points found above altitude threshold {altitude_threshold}")

# Example Usage
input_gpx_file_path = 'stelvio/stelvio.gpx'
output_gpx_file_path = 'gavia/gavia.gpx'
altitude_threshold = 1200

filter_and_save_gps_data(input_gpx_file_path, output_gpx_file_path, altitude_threshold)
