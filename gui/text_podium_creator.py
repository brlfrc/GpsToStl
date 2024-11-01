import tkinter as tk
from tkinter import colorchooser, messagebox

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from main_function.UphillSTL import UphillSTL
from main_function.Text3D import Text3D
from main_function.Podium import Podium

from gui.model_3D_creator import Model3DGeneratorGUI


class TextAndPodiumGeneratorGUI(tk.Toplevel):
    def __init__(self, uphill_STL = None):
        self.uphill_STL = uphill_STL if uphill_STL is not None else UphillSTL()
        self.text_3d = None
        self.podium_STL = None
        super().__init__()

        self.title("Text and Podium Generator")
        self.geometry("1200x700")

        # Left frame for text generator
        self.text_frame = tk.Frame(self)
        self.text_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

        # Text Generator Title
        tk.Label(self.text_frame, text="Text Generator", font=("Helvetica", 16)).pack(pady=5)

        # Text Input
        tk.Label(self.text_frame, text="Text:").pack(pady=5)
        self.text_entry = tk.Entry(self.text_frame)
        self.text_entry.pack(pady=5)

        # Font Selection
        tk.Label(self.text_frame, text="Font:").pack(pady=5)
        self.font_entry = tk.Entry(self.text_frame)
        self.font_entry.pack(pady=5)
        self.font_entry.insert(0, "arial.ttf")  # Default font

        # Color Selection
        color_frame = tk.Frame(self.text_frame)
        color_frame.pack(pady=5)
        tk.Label(color_frame, text="Color:").pack(side=tk.LEFT)
        self.color_button = tk.Button(color_frame, text="Select Color", command=self.choose_color)
        self.color_button.pack(side=tk.LEFT)
        self.color = [0, 250, 0, 250]  # Default color
        self.color_preview = tk.Label(color_frame, width=2, height=1, bg=self.rgb_to_hex(self.color[:3]))  # Preview square
        self.color_preview.pack(side=tk.LEFT, padx=5)

        # Update Button for Text
        tk.Button(self.text_frame, text="Update Text", command=self.update_text).pack(pady=20)

        # Placeholder for text preview
        self.text_preview_frame = tk.Frame(self.text_frame)
        self.text_preview_frame.pack(pady=20)

        # Right frame for podium generator
        self.podium_frame = tk.Frame(self)
        self.podium_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.Y)

        # Podium Title
        tk.Label(self.podium_frame, text="Podium Generator", font=("Helvetica", 16)).pack(pady=5)

        # Shape Selection
        self.shape_var = tk.StringVar(value="rectangular")
        tk.Label(self.podium_frame, text="Shape:").pack(pady=5)
        self.shape_option = tk.OptionMenu(self.podium_frame, self.shape_var, "rectangular", "cylindrical", command=self.update_shape_options)
        self.shape_option.pack(pady=5)

        # Width/Radius and Height Inputs
        input_frame = tk.Frame(self.podium_frame)
        input_frame.pack(pady=5)

        # Width/Radius
        self.width_label = tk.Label(input_frame, text="Width:")
        self.width_label.grid(row=0, column=0, padx=5)
        self.width_entry = tk.Entry(input_frame, width=10)
        self.width_entry.grid(row=0, column=1, padx=5)
        self.width_entry.insert(0, "50")  # Default value

        # Depth for Rectangular / Radius for Cylindrical
        self.depth_label = tk.Label(input_frame, text="Depth:")
        self.depth_label.grid(row=0, column=2, padx=5)
        self.depth_entry = tk.Entry(input_frame, width=10)
        self.depth_entry.grid(row=0, column=3, padx=5)
        self.depth_entry.insert(0, "50")  # Default value

        # Height
        tk.Label(input_frame, text="Height:").grid(row=0, column=4, padx=5)
        self.height_entry = tk.Entry(input_frame, width=10)
        self.height_entry.grid(row=0, column=5, padx=5)
        self.height_entry.insert(0, "10")  # Default value

        # Color Selection for Podium
        color_frame_podium = tk.Frame(self.podium_frame)
        color_frame_podium.pack(pady=5)
        tk.Label(color_frame_podium, text="Color:").pack(side=tk.LEFT)
        self.color_button_podium = tk.Button(color_frame_podium, text="Select Color", command=self.choose_color_podium)
        self.color_button_podium.pack(side=tk.LEFT)
        self.color_podium = [0, 0, 250, 250]  # Default color
        self.color_preview_podium = tk.Label(color_frame_podium, width=2, height=1, bg=self.rgb_to_hex(self.color_podium[:3]))  # Preview square
        self.color_preview_podium.pack(side=tk.LEFT, padx=5)

        # Update Button for Podium
        tk.Button(self.podium_frame, text="Update Podium", command=self.update_podium).pack(pady=20)

        # Placeholder for podium preview
        self.podium_preview_frame = tk.Frame(self.podium_frame)
        self.podium_preview_frame.pack(pady=20)

        # Continue button (initially hidden)
        self.continue_button = tk.Button(self, text="Continue", command=self.on_continue)
        self.continue_button.pack(pady=20)
        self.continue_button.pack_forget()  # Hide the button initially
        self.text_updated = False
        self.podium_updated = False

        # Initially set to rectangular, update the shape options
        self.update_shape_options()

    def choose_color(self):
        """Open color chooser and get RGB value for text."""
        color_code = colorchooser.askcolor(title="Choose color")
        if color_code:
            self.color = [int(c) for c in color_code[0]] + [250]  # RGBA, keeping alpha at 250
            self.color_preview.config(bg=self.rgb_to_hex(self.color[:3]))  # Update preview square color

    def choose_color_podium(self):
        """Open color chooser and get RGB value for podium."""
        color_code = colorchooser.askcolor(title="Choose color")
        if color_code:
            self.color_podium = [int(c) for c in color_code[0]] + [250]  # RGBA, keeping alpha at 250
            self.color_preview_podium.config(bg=self.rgb_to_hex(self.color_podium[:3]))  # Update preview square color

    def rgb_to_hex(self, rgb):
        """Convert RGB values to hex color format."""
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

    def update_shape_options(self, *args):
        """Updates the input fields based on selected podium shape."""
        if self.shape_var.get() == "rectangular":
            self.width_label.config(text="Width")  # Change the text here
            self.depth_entry.config(state='normal')  # Enable the entry
        else:  # cylindrical
            self.width_label.config(text="Radius")  # Change the text here
            self.depth_entry.config(state='disabled')  # Disable the entry

    def update_text(self):
        """Handles updating the text 3D model."""
        try:
            text_value = self.text_entry.get()
            font_value = self.font_entry.get()
            font_size = 50  # You can add an input for font size if needed
            scale = 5  # Adjust this as needed

            # Create an instance of Text3D
            self.text_3d = Text3D(text=text_value, font=font_value, font_size=font_size, scale=scale, color=self.color, mask_val=0.01)

            # Display in matplotlib
            self.show_text_in_matplotlib(self.text_3d)

            # Set flag to indicate text has been updated
            self.text_updated = True
            self.check_continue_button()  # Check if we can show the continue button

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate text: {e}")

    def update_podium(self):
        """Handles updating the podium model."""
        try:
            width = float(self.width_entry.get())
            height = float(self.height_entry.get())
            depth = float(self.depth_entry.get()) if self.shape_var.get() == "rectangular" else float(self.width_entry.get())

            # Create an instance of Podium
            self.podium_STL = Podium(width=width, depth=depth, height=height, shape=self.shape_var.get(), color=self.color_podium)

            # Display in matplotlib
            self.show_podium_in_matplotlib(self.podium_STL)

            # Set flag to indicate podium has been updated
            self.podium_updated = True
            self.check_continue_button()  # Check if we can show the continue button

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values for width, height, and depth/radius.")

    def check_continue_button(self):
        """Checks if both updates have been made to show the continue button."""
        if self.text_updated and self.podium_updated:
            self.continue_button.pack(pady=20)  # Show the continue button

    def on_continue(self):

        self.destroy()
        fourth_window = Model3DGeneratorGUI(uphill_STL=self.uphill_STL, podium_stl=self.podium_STL, text3d=self.text_3d)
    

    def show_text_in_matplotlib(self, text_3d):
        """Displays the generated text model using Matplotlib in the Tkinter window."""
        if hasattr(self, 'text_canvas'):
            self.text_canvas.get_tk_widget().destroy()  # Destroy the existing canvas to refresh

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111, projection='3d')

        # Extract vertices and faces from the text mesh
        vertices = text_3d.mesh.vertices
        faces = text_3d.mesh.faces

        # Prepare a Poly3DCollection to hold the triangles
        polygons = []
        for face in faces:
            triangle = vertices[face]
            color_normalized = np.array(text_3d.color[:3]) / 255.0  # Normalize color
            polygons.append((triangle, color_normalized))

        # Create the Poly3DCollection
        poly_collection = Poly3DCollection(
            [poly[0] for poly in polygons],
            facecolors=[poly[1] for poly in polygons],
            linewidths=1,
            edgecolors=[poly[1] for poly in polygons],  # Set edge colors to match face colors
            alpha=0.5
        )

        # Add the collection to the axes
        ax.add_collection3d(poly_collection)

        z_positive_vertices = vertices[vertices[:, 2] > np.max(vertices[:, 2])-0.01]  # Filter vertices where z > 0

        ax.scatter(z_positive_vertices[:, 0], z_positive_vertices[:, 1], z_positive_vertices[:, 2], color='black', s=10)

        ax.set_title('3D Text Model')
        ax.axis('off')  # Hide axes
        ax.grid(False)  # Hide grid

        # Create the canvas and display
        self.text_canvas = FigureCanvasTkAgg(fig, master=self.text_preview_frame)
        self.text_canvas.draw()
        self.text_canvas.get_tk_widget().pack()

    def show_podium_in_matplotlib(self, podium):
        """Displays the generated podium model using Matplotlib in the Tkinter window."""
        if hasattr(self, 'podium_canvas'):
            self.podium_canvas.get_tk_widget().destroy()  # Destroy the existing canvas to refresh

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111, projection='3d')

        # Extract vertices and faces from the podium mesh
        vertices = podium.mesh.vertices
        faces = podium.mesh.faces

        # Prepare a Poly3DCollection to hold the triangles
        polygons = []
        for face in faces:
            triangle = vertices[face]
            color_normalized = np.array(podium.color[:3]) / 255.0  # Normalize color
            polygons.append((triangle, color_normalized))

        # Create the Poly3DCollection
        poly_collection = Poly3DCollection(
            [poly[0] for poly in polygons],
            facecolors=[poly[1] for poly in polygons],
            linewidths=1,
            edgecolors=[poly[1] for poly in polygons],  # Set edge colors to match face colors
            alpha=0.5
        )

        # Add the collection to the axes
        ax.add_collection3d(poly_collection)

        # Filter vertices to only those with z > 0
        z_positive_vertices = vertices[vertices[:, 2] > -0.1]  # Filter vertices where z > 0
        ax.scatter(z_positive_vertices[:, 0], z_positive_vertices[:, 1], z_positive_vertices[:, 2], color='black', s=10)

        ax.set_title('3D Podium Model')
        ax.axis('off')  # Hide axes
        ax.grid(False)  # Hide grid

        # Create the canvas and display
        self.podium_canvas = FigureCanvasTkAgg(fig, master=self.podium_preview_frame)
        self.podium_canvas.draw()
        self.podium_canvas.get_tk_widget().pack()

# Example of how to create and run the GUI
# if __name__ == "__main__":
# root = tk.Tk()
# root.withdraw()  # Hide the root window
# app = TextAndPodiumGeneratorGUI()
# app.mainloop()
