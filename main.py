from main_function.Text3D import Text3D
from main_function.Podium import Podium
from main_function.UphillSTL import UphillSTL
from main_function.Model_3D import Model_3D
from gui.gpx_loader import GPXLoaderGUI
import trimesh

# Approccio con Gui

# app = GPXLoaderGUI()
# app.mainloop()

# # Approccio da codice
# photo_holder = trimesh.load('tmp_STL/photo_holder.stl')
# photo_holder.show()

# uphill = UphillSTL(path_gps='example/presolana.gpx', selection=True, thickness_multiplier=1)

# trimesh.interfaces.scad.SCAD_PATH = "C:\\Program Files\\OpenSCAD\\openscad.exe"  # Cambia il percorso se necessario

# podium1 = Podium(width=80, depth=35, height=25, shape="rectangular")  
# podium2 = Podium(width=20, depth=50, height=30, shape="rectangular")

# mesh_difference = podium1.mesh.difference(podium2.mesh)

# if mesh_difference.is_watertight:
#     print("La mesh risultante è watertight.")

# mesh_difference.show()

uphill = UphillSTL(path_gps='example/presolana.gpx', selection=True, thickness_multiplier=1, image_resolution=40)

podium = Podium(width=80, depth=35, height=25, radius= 40, shape="cylindrical")  
text = Text3D(text= 'caso', font_size=80, mask_val= 0.01 )


# total_model = Model_3D(podium= podium, uphill= uphill, text3d= text)
total_model = Model_3D(podium= podium, uphill= uphill, text3d= text)

total_model.magnets_support()
total_model.update_mesh()

# total_model.update_mesh()
total_model.show()