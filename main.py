from main_function.Text3D import Text3D
from main_function.Podium import Podium
from main_function.UphillSTL import UphillSTL
from main_function.Model_3D import Model_3D
from gui.gpx_loader import GPXLoaderGUI
import trimesh

# Approccio con Gui

app = GPXLoaderGUI()
app.mainloop()

# # Approccio da codice
# uphill = UphillSTL(path_gps='example/presolana.gpx', selection=True, thickness_multiplier=1)

# podium = Podium(width=50, height=15, shape="rectangular")  # shape cylindrical or rectangular

# text = Text3D(text= 'Stelvio', font_size=80, mask_val= 0.01 )


# total_model = Model_3D(podium= podium, uphill= uphill, text3d= text)
# total_model.update_mesh()
# total_model.show()