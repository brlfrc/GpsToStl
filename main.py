from main_function.STL_text import generate_text_STL
from main_function.podium_STL import create_podium
from main_function.GPS_STL_generator import GPStoSTL

#mesh = generate_text_STL (text= 'Presolana', font_size=80 )
#mesh.show()

podium = create_podium ()
# podium.show()

uphill= GPStoSTL (path_gps = 'example/selvino/selvino.gpx', selection=True)
uphill.show()


# Sposta la traccia in modo che sia sopra il podio
uphill.apply_translation([0, 0, 10])
uphill.show()

# Unisci le mesh
combined_mesh = podium + uphill
combined_mesh.show()