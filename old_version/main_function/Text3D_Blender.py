import trimesh
import os

from main_function.STL_function import repair_with_blender
import subprocess

class Text3D_blender:
    def __init__(self, text='Example', font="arial.ttf", input_text_path = r'tmp_STL\text_blender.txt',
                output_path = r'tmp_STL\text_blender.stl', repair= False, min_thickness_percent = 0.5):
        """
        Initializes an instance of Text3DGenerator to generate a 3D STL model from text.
        
        Parameters:
        - text: The text to display.
        - font: Path to the TrueType font file.
        - font_size: Size of the font.
        - padding: Padding around the text in the image.
        - scale: Scale factor to adjust the STL dimensions.
        """
        self.text = text
        self.font = font
        self.input_text_path = input_text_path
        self.output_path = output_path



        self.min_thickness_percent = min_thickness_percent
        
        self.repair = repair
        self.mesh = None

        self._generate_file()
        self._create_mesh()  # Automatically generates the STL mesh
        self.mesh_is_watertight = self.mesh.is_watertight
        if self.repair:
            self._repair_text()

    def show(self):
        """Displays the generated STL mesh."""
        self.mesh.show()


    def _generate_file(self):
        """Generates a text file with the given content if it does not already exist."""
        try:
            # Open the file in write mode, which overwrites the file if it already exists
            with open(self.input_text_path, 'w') as file:
                file.write(self.text)

        except Exception as e:
            print(f"An error occurred while generating the file: {e}")

    def _create_mesh(self):

        input_text_path = os.path.join(r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl", self.input_text_path)
        mesh_path = os.path.join(r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl", self.output_path)

        blender_path = r"C:\Program Files\Blender Foundation\Blender 2.91\blender.exe"
        script_path = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\blender_repair\text_creator.py"
        
        command = [
            blender_path, "--background", "--python", script_path,
            "--", input_text_path, mesh_path
        ]
        subprocess.run(command)

        self.mesh = trimesh.load(self.output_path)

    def _repair_text(self):
        path = os.path.join(r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl", self.text_path)

        if not self.mesh_is_watertight:
            repair_with_blender(path, path)
            self.mesh = trimesh.load(path)
            self.mesh_is_watertight = self.mesh.is_watertight
        
        print('Mesh is watertight: ', self.mesh_is_watertight)