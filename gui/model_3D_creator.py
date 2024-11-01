import tkinter as tk
from tkinter import messagebox, ttk

from main_function.Model_3D import Model_3D  # Adjust this import based on your project structure
from main_function.Text3D import Text3D
from main_function.Podium import Podium
from main_function.UphillSTL import UphillSTL


class Model3DGeneratorGUI(tk.Tk):
    def __init__(self, uphill_STL=None, podium_stl=None, text3d=Text3D()):
        super().__init__() 

        self.uphill_STL = uphill_STL if uphill_STL is not None else UphillSTL()
        self.text_3d = text3d if text3d is not None else Text3D() 
        self.podium_stl = podium_stl if podium_stl is not None else Podium()  
        

        self.title("3D Model Generator")
        self.geometry("800x400")

        # Initialize variables for inputs
        self.rotation_angle = tk.DoubleVar(value=0)  # Default rotation angle in degrees
        self.uphill_multiplier = tk.DoubleVar(value=1.0)  # Default multiplier
        self.margin = tk.DoubleVar(value=0.8)  # Default margin

        ttk.Label(self, text="Rotation Angle (degrees):").grid(row=0, column=0, padx=10, pady=5)
        self.rotation_angle_entry = ttk.Entry(self, width=10)
        self.rotation_angle_entry.grid(row=0, column=1, padx=10, pady=5)
        self.rotation_angle_entry.insert(0, "0") 

        ttk.Label(self, text="Uphill Dimension Multiplier:").grid(row=1, column=0, padx=10, pady=5)
        self.uphill_multiplier_entry = ttk.Entry(self, width=10)
        self.uphill_multiplier_entry.grid(row=1, column=1, padx=10, pady=5)
        self.uphill_multiplier_entry.insert(0, "1.0")

        ttk.Label(self, text="Margin (distance from border):").grid(row=2, column=0, padx=10, pady=5)
        self.margin_entry = ttk.Entry(self, width=10)
        self.margin_entry.grid(row=2, column=1, padx=10, pady=5)
        self.margin_entry.insert(0, "0.8")  
        # Generate button
        generate_button = ttk.Button(self, text="Generate 3D Model", command=self.generate_model)
        generate_button.grid(row=3, columnspan=2, pady=10)

        # Return button
        return_button = ttk.Button(self, text="Return Model_3D", command=self.return_model)
        return_button.grid(row=4, columnspan=2, pady=10)

    def generate_model(self):
        """Generate the 3D model based on user inputs."""
        try:
            rotation = float(self.rotation_angle_entry.get())
            height_multiplier = float(self.uphill_multiplier_entry.get())
            margin = float(self.margin_entry.get())

            # Create the Model_3D instance
            self.model_3D = Model_3D(podium=self.podium_stl, text3d=self.text_3d, uphill=self.uphill_STL, margin=margin, height_multiplier=height_multiplier, rotation_uphill_angle=rotation)

            # Update the mesh based on user inputs
            self.model_3D.update_mesh()

            # Show the model
            self.model_3D.show()  # This will open a window displaying the 3D model
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def return_model(self):
        """Return the Model_3D instance and close the application."""
        # You can now use the Model_3D instance as needed
        if hasattr(self, 'model_3D'):
            # Here, you might want to process the model_3D before closing
            print("Returning Model_3D instance:", self.model_3D)
        
        # Close all windows
        self.quit()  # This will close the main window and exit the application


# Start the GUI application
# if __name__ == "__main__":
#     app = Model3DGeneratorGUI()
#     app.mainloop()
