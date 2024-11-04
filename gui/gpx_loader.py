import tkinter as tk
from tkinter import filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

from main_function.GPS_function import AltimetryPlotter
from gui.uphill_creator import UphillCreatorGUI


def get_gpx_examples(folder_path='example/'):
    # Check if the folder exists
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"The folder '{folder_path}' does not exist.")

    # Find all files in the specified folder that end with .gpx
    gpx_files = [f for f in os.listdir(folder_path) if f.endswith(".gpx")]

    # Raise an error if no GPX files are found
    if not gpx_files:
        raise FileNotFoundError(f"No GPX files found in the folder '{folder_path}'.")

    return gpx_files

class GPXLoaderGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Load GPS Data and View Altimetry")
        self.geometry("800x600")

        # Label and button for uploading GPX file
        self.upload_label = tk.Label(self, text="Upload GPX File:")
        self.upload_label.pack(pady=5)

        self.upload_button = tk.Button(self, text="Upload GPX file", command=self.upload_gpx_file)
        self.upload_button.pack(pady=5)

        # Dropdown menu for selecting an example GPX file
        self.example_label = tk.Label(self, text="Use GPX example:")
        self.example_label.pack(pady=5)

        self.example_var = tk.StringVar(self)
        self.example_var.set("Select an example")  # Default option

        # Loading examples from the "data" folder
        self.gpx_examples = get_gpx_examples("example")
        self.example_menu = tk.OptionMenu(self, self.example_var, *self.gpx_examples, command=self.enable_load_selection)
        self.example_menu.pack(pady=5)

        # Button to confirm selection
        self.load_button = tk.Button(self, text="Load Selection", command=self.load_selection, state=tk.DISABLED)
        self.load_button.pack(pady=10)

        # Placeholder for the plot canvas
        self.canvas = None  # Matplotlib canvas for the plot
        self.plotter = None  # Instance of AltimetryPlotter

    def upload_gpx_file(self):
        # Open file dialog
        file_path = filedialog.askopenfilename(filetypes=[("GPX files", "*.gpx")])
        if file_path:
            self.display_altimetry(file_path)
            self.load_button.config(state=tk.DISABLED)  # Disable the load button after upload

    def load_selection(self):
        # Load selected example file
        selected_example = self.example_var.get()
        if selected_example != "Select an example":
            file_path = os.path.join("example", selected_example)
            self.display_altimetry(file_path)
            self.load_button.config(state=tk.DISABLED)  # Disable the load button after loading selection
        else:
            messagebox.showwarning("Warning", "Select an example or upload a file.")

    def enable_load_selection(self, *args):
        # Enable the Load Selection button when a different example is selected
        self.load_button.config(state=tk.NORMAL)

    def display_altimetry(self, file_path):
        # Initialize AltimetryPlotter to display the profile
        if self.canvas:
            self.canvas.get_tk_widget().pack_forget()  # Remove existing plot if any

        # Use AltimetryPlotter to parse the data and create the plot
        self.plotter = AltimetryPlotter.from_file(file_path, close_callback=self.open_second_window)  # Pass the close callback
        fig, ax = self.plotter.get_figure()

        # Embedding the plot in the tkinter GUI
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(pady=10)

    def open_second_window(self):
        self.destroy()  # Close the first window
        second_window = UphillCreatorGUI()  # Create and open the second window
   