from main_function.Text3D import Text3D
from main_function.Podium import Podium
from main_function.UphillSTL import UphillSTL
from main_function.Model_3D import Model_3D


uphill = UphillSTL(path_gps='example/selvino/selvino.gpx', selection=True) # In questo momento stelvio non va, non so perché 
podium = Podium(width=50, height=15, shape="cylindrical")  # shape cylindrical or rectangular
text = Text3D(text= 'SELVINO', font_size=80 )

total_model = Model_3D(podium= podium, uphill= uphill, text3d= text)
total_model.update_mesh()
total_model.show()