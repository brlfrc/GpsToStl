import tkinter as tk
from tkinter import colorchooser
from tkinter import messagebox
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from main_function.UphillSTL import UphillSTL  
from gui.text_podium_creator import TextAndPodiumGeneratorGUI

class UphillCreatorGUI(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title("Road Model Generator")
        self.geometry("800x400")

        # Initialize a flag to track if the model has been generated
        self.model_generated = False

        # Left frame for parameters
        self.param_frame = tk.Frame(self)
        self.param_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

        # Color Selection
        self.color_label = tk.Label(self.param_frame, text="Color:")
        self.color_label.pack(pady=5)

        # Color selection button
        color_frame = tk.Frame(self.param_frame)
        color_frame.pack(pady=5)
        self.color_button = tk.Button(color_frame, text="Select Color", command=self.choose_color)
        self.color_button.pack(side=tk.LEFT)

        self.color = [250, 0, 0, 250]  # Default color
        self.color_preview = tk.Label(color_frame, width=2, height=1, bg=self.rgb_to_hex(self.color[:3]))  # Preview square
        self.color_preview.pack(side=tk.LEFT, padx=5)

        # Thickness Multiplier
        self.thickness_label = tk.Label(self.param_frame, text="Thickness Multiplier (~1):")
        self.thickness_label.pack(pady=5)

        self.thickness_entry = tk.Entry(self.param_frame)
        self.thickness_entry.pack(pady=5)
        self.thickness_entry.insert(0, "1")  # Set default value to 1

        # Resolution
        self.resolution_label = tk.Label(self.param_frame, text="Resolution (~800):")
        self.resolution_label.pack(pady=5)

        self.resolution_entry = tk.Entry(self.param_frame)
        self.resolution_entry.pack(pady=5)
        self.resolution_entry.insert(0, "800")  # Set default value to 800

        # Update Button
        self.update_button = tk.Button(self.param_frame, text="Update", command=self.update_stl)
        self.update_button.pack(pady=20)

        # Confirm Button (initially hidden)
        self.confirm_button = tk.Button(self.param_frame, text="Confirm", command=self.confirm)
        self.confirm_button.pack(pady=20)
        self.confirm_button.pack_forget()  # Hide the button initially

        # Right frame for preview and plot
        self.plot_frame = tk.Frame(self)
        self.plot_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Placeholder for STL preview
        self.preview_label = tk.Label(self.plot_frame, text="STL Preview Will Appear Here")
        self.preview_label.pack(pady=20)

        self.uphill_STL = None  # Placeholder for the UphillSTL model
        self.canvas = None  # Placeholder for the canvas

    def rgb_to_hex(self, rgb):
        """Convert RGB values to hex color format."""
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

    def choose_color(self):
        # Open color chooser and get RGB value
        color_code = colorchooser.askcolor(title="Choose color")
        if color_code:
            self.color = [int(c) for c in color_code[0]] + [250]  # RGBA, keeping alpha at 250
            self.color_preview.config(bg=self.rgb_to_hex(self.color[:3]))  # Update preview square color

    def update_stl(self):
        # Get values from entries and create the UphillSTL model
        try:
            thickness_multiplier = float(self.thickness_entry.get())
            resolution = int(self.resolution_entry.get())

            # Create an instance of UphillSTL
            self.uphill_STL = UphillSTL(selection=False, thickness_multiplier=thickness_multiplier, image_resolution=resolution, color=self.color)
            
            # Remove the preview label after the model is created
            self.preview_label.pack_forget()  # Hide the label

            # Show the model or update the visualization
            self.show_in_matplotlib()  # Call the method to display the model

            # Mark that the model has been generated and show the Confirm button
            self.model_generated = True
            self.confirm_button.pack(pady=20)  # Show the Confirm button

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values for thickness and resolution.")

    def show_in_matplotlib(self):
        """Displays the generated STL mesh using Matplotlib in the Tkinter window."""
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()  # Destroy the existing canvas to refresh

        fig = Figure(figsize=(10, 8), dpi=100)
        ax = fig.add_subplot(111, projection='3d')

        # Extract vertices and faces from the mesh
        vertices = self.uphill_STL.mesh.vertices
        faces = self.uphill_STL.mesh.faces

        # Prepare a Poly3DCollection to hold the triangles
        polygons = []
        for face in faces:
            triangle = vertices[face]
            color_normalized = np.array(self.uphill_STL.color[:3]) / 255.0  # Normalize color
            polygons.append((triangle, color_normalized))

        # Create the Poly3DCollection with edge colors matching face colors
        poly_collection = Poly3DCollection(
            [poly[0] for poly in polygons], 
            facecolors=[poly[1] for poly in polygons], 
            linewidths=1, 
            edgecolors=[poly[1] for poly in polygons],  # Set edge colors to match face colors
            alpha=0.5
        )

        # Add the collection to the axes
        ax.add_collection3d(poly_collection)

        z_positive_vertices = vertices[vertices[:, 2] > 0]  # Filter vertices where z > 0
        ax.scatter(z_positive_vertices[:, 0], z_positive_vertices[:, 1], z_positive_vertices[:, 2], color='black', s=5)

        # Set limits based on vertices
        ax.set_xlim([vertices[:, 0].min(), vertices[:, 0].max()])
        ax.set_ylim([vertices[:, 1].min(), vertices[:, 1].max()])
        ax.set_zlim([vertices[:, 2].min(), vertices[:, 2].max()])

        # Hide axes and grid
        ax.set_xticks([])  # Hide x ticks
        ax.set_yticks([])  # Hide y ticks
        ax.set_zticks([])  # Hide z ticks       
        ax.grid(True)

        # Create a canvas and add it to the Tkinter frame
        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def confirm(self):
        """Handles confirmation of the model generation."""
        if self.model_generated:
            # Proceed to generate podium and text here
            self.destroy()  # Close the current window after confirmation
            third_window = TextAndPodiumGeneratorGUI(self.uphill_STL)

# Usage Example:
# If you want to run this as a standalone application, you can add:
# if __name__ == "__main__":
# app = tk.Tk()
# app.withdraw()  # Hide the root window
# uphill_creator = UphillCreatorGUI()
# uphill_creator.mainloop()
