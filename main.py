from main_function.Uphill_Point_bl import Uphill_Point_blender

import json
import subprocess

def create_configuration(
    thickness: int = 2,
    points_file_path: str= r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\uphill_points.txt",
    uphill_stl_path: str=  r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\uphill_blender.stl",
    text_input: str= 'Selvino',
    font_path: str= r"C:\Windows\Fonts\Stencilia-A.ttf",
    text_stl_path: str= r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\text_blender.stl",
    diff_stl_path: str= r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\diff_blender.stl",
    cube_path: str= r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\cube_magnet_holder_v2.stl",
    magnet_holder_path: str=  r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\magnet_holder_v2.stl",
    output_file: str = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\config.json"
):
    config = {
        "thickness": thickness,
        "points_file_path": points_file_path,
        "uphill_stl_path": uphill_stl_path,
        "text_input": text_input,
        "font_path": font_path,
        "text_stl_path": text_stl_path,
        "diff_stl_path": diff_stl_path,
        "cube_path": cube_path,
        "magnet_holder_path": magnet_holder_path
    }

    # Write the configuration file
    with open(output_file, "w") as file:
        json.dump(config, file, indent=4)

    print(f"Configuration file created: {output_file}")

Uphill_Point_blender(path_gps='example/Zoncolan.gpx', selection=True, selected_point_path='tmp_STL/selected_data.txt', 
                point_output_path = 'tmp_STL/uphill_points.txt', rotation = 160, base_percent= 0.6, height= 45)

output_file = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\config.json"

# diff_stl_path = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\diff_blender.stl"

diff_stl_path = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\STL_da_Stampare\Zoncolan.stl"

create_configuration(output_file=output_file, text_input='ZONCOLAN', thickness=1.6, diff_stl_path=diff_stl_path)

blender_path = r"C:\Program Files\Blender Foundation\Blender 2.91\blender.exe"
script_path = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\blender_function\blender_total.py"

command = [
    blender_path, "--background", "--python", script_path,
    "--", output_file
]
subprocess.run(command)

# for thick in [0.5,1,1.5,2]:
#     diff_stl_path = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\tmp_STL\prototipi\diff_blender_"+str(thick)+".stl"
#     create_configuration(output_file=output_file, thickness=thick, diff_stl_path=diff_stl_path)

#     blender_path = r"C:\Program Files\Blender Foundation\Blender 2.91\blender.exe"
#     script_path = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\blender_repair\blender_total.py"

#     command = [
#         blender_path, "--background", "--python", script_path,
#         "--", output_file
#     ]
#     subprocess.run(command)













# # uphill = UphillSTL(path_gps='example/presolana.gpx', selection=True, thickness_multiplier=2, image_resolution=800, min_thickness_percent=0.5)
# uphill = UphillSTL_blender(path_gps='example/selvino.gpx', selection=True, 
#                            selected_point_path='tmp_STL/selected_data.txt', output_path='tmp_STL/uphill_blender_v.stl', point_output_path = 'tmp_STL/uphill_points.txt', 
#                             repair= False, min_thickness_percent=0.5)


# # text1 = Text3D(text='Stelvio', font_size=70, mask_val=0.1, smoothing= False, repair=True)
# text= Text3D_blender ( text='SELVINO')
# # text.show()

# model = Model_2v(uphill=uphill, text3d=text)
# model.update_mesh()
# model.save_all_mesh()
# model.make_difference_mesh()
# # # # model.solidify_uphill_mesh()
# # model.make_magnet_union()
# model.mesh.show()

# model.make_difference_mesh()

# text1 = Text3D(text='Cavolfiore', font_size=80, mask_val=0.01, smoothing= False)
# text2 = Text3D(text= 'AAA', font_size=80, mask_val=0.00)

# mesh_difference = text1.mesh.difference(text2.mesh)
# mesh_difference.show()

# # Approccio con Gui

# app = GPXLoaderGUI()
# app.mainloop()

# # # Approccio da codice

# # uphill = UphillSTL(path_gps='example/presolana.gpx', selection=True, thickness_multiplier=1)

# mesh_difference = text1.mesh.difference(text2.mesh)

# if mesh_difference.is_watertight:
#     print("La mesh risultante è watertight.")

# mesh_difference.show()

# uphill = UphillSTL(path_gps='example/selvino.gpx', selection=True, thickness_multiplier=1, image_resolution=800)
# # text = Text3D(text= 'Selvino', font_size=80, mask_val= 0.01 )
# mesh = uphill.mesh
# print(mesh.is_watertight)  # Returns True if the mesh is watertight
# print(mesh.is_winding_consistent)  # Check if face normals are consistently defined

# mesh.fill_holes()
# mesh.show()
# trimesh.repair.broken_faces(mesh, color=[255, 0, 0, 255]) 
# mesh.show()
# print(mesh.is_watertight)  # Returns True if the mesh is watertight
# print(mesh.is_winding_consistent)


# print(mesh.non_manifold_edges)  # Returns a list of edges that are problematic
# if len(mesh.non_manifold_edges) > 0:
#     print("Mesh has non-manifold edges!")

# print(mesh.boundary_edges)  # List of edges that form the boundaries
# if len(mesh.boundary_edges) > 0:
#     print("Mesh has open boundaries, indicating holes.")


# podium = Podium(width=80, depth=35, height=25, radius= 40, shape="cylindrical")  
# text = Text3D(text= 'Selvino', font_size=80, mask_val= 0.01 )


# total_model = Model_3D(podium= podium, uphill= uphill, text3d= text)
# total_model = Model_3D(podium= podium, uphill= uphill, text3d= text)
# total_model.photo_holder()
# total_model.magnets_support()
# total_model.update_mesh()

# total_model.update_mesh()
# total_model.show()