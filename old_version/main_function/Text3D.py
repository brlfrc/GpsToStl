from PIL import Image, ImageDraw, ImageFont
import trimesh
import os

from main_function.STL_function import numpy2stl, repair_with_blender
from scipy.ndimage import gaussian_filter

class Text3D:
    def __init__(self, text='Example', font="arial.ttf", font_size=50, scale=5, mask_val= None, color = [0,250,0,250], smoothing = True, 
                 text_path = r'tmp_STL\text.stl', repair= True, min_thickness_percent = 0):
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
        self.font_size = font_size
        self.padding = 20
        self.scale = scale
        self.min_thickness_percent = min_thickness_percent
        self.solid = True
        self.mask = mask_val
        self.image = None
        self.color = color
        self.smoothing = smoothing
        self.repair = repair
        self.text_path = text_path
        self.mesh = self._generate_text_stl()  # Automatically generates the STL mesh
        self.mesh_is_watertight = self.mesh.is_watertight
        if self.repair:
            self._repair_text()

    def _generate_text_image(self):
        """
        Generates a grayscale image of the specified text.
        
        :return: A grayscale PIL image of the text.
        """
        font = ImageFont.truetype(self.font, self.font_size)

        # Create a dummy image to calculate text dimensions
        dummy_image = Image.new('L', (1, 1), color=0)
        draw = ImageDraw.Draw(dummy_image)
        text_bbox = draw.textbbox((0, 0), self.text, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

        # Calculate image dimensions with padding
        image_width = text_width + self.padding * 2
        image_height = text_height + self.padding * 2

        # Create the final image with black background
        image = Image.new('L', (image_width, image_height), color=0)
        draw = ImageDraw.Draw(image)

        # Draw the text in white
        draw.text((self.padding, self.padding), self.text, font=font, fill=255)

        self.image = image

    def _generate_text_stl(self):
        """
        Converts the generated text image into an STL mesh.
        
        :return: STL mesh generated from the text.
        """
        # Generate the text image
        self._generate_text_image()
        if self.smoothing:
            text_image = gaussian_filter(self.image, 1)  # smoothing
        else:
            text_image = self.image

        
        # Convert the image into an STL mesh
        stl_mesh = numpy2stl(text_image, scale=self.scale, fn = self.text_path, mask_val=self.mask, rotation = False, min_thickness_percent= self.min_thickness_percent)
        stl_mesh.visual.face_colors= self.color

        return stl_mesh


    def _repair_text(self):
        path = os.path.join(r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl", self.text_path)

        if not self.mesh_is_watertight:
            repair_with_blender(path, path)
            self.mesh = trimesh.load(path)
            self.mesh_is_watertight = self.mesh.is_watertight
        
        print('Mesh is watertight: ', self.mesh_is_watertight)



    def show(self):
        """Displays the generated STL mesh."""
        self.mesh.show()

    def show_image_text(self):
        """Displays the generated STL mesh."""
        if self.image is None:
            self._generate_text_image()
        self.image.show()