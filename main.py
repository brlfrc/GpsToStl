from main_function.STL_text import generate_text_STL
from main_function.podium_STL import create_podium
from main_function.GPS_STL_generator import GPStoSTL

mesh = generate_text_STL (text= 'Selvino', font_size=80 )
mesh.show()

podium = create_podium ()
podium.show()

uphill= GPStoSTL(path_gps = 'example/selvino/selvino.gpx', selection=True)
uphill.show()


mesh.apply_translation([0, 0, 5])
uphill.apply_translation([0, 0, 10])

combined_mesh = mesh + podium + uphill
combined_mesh.show()