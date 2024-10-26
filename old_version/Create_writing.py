from PIL import Image, ImageDraw, ImageFont
import numpy as np
from stl import mesh
import matplotlib.pyplot as plt

def create_text_image(text, font_path, font_size):
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print(f"Cannot open font resource: {font_path}. Using default font.")
        font = ImageFont.load_default()
    
    # Create an image with a white background
    image = Image.new('L', (1000, 500), 255)
    draw = ImageDraw.Draw(image)
    
    # Use textbbox instead of textsize
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    print(f"Text bounding box: {bbox}")  # Debug print
    
    # Calculate text position to center it in the image
    text_position = ((image.width - text_width) // 2 - bbox[0], (image.height - text_height) // 2 - bbox[1])
    print(f"Text position: {text_position}")  # Debug print
    
    draw.text(text_position, text, font=font, fill=0)
    
    cropped_image = image.crop(bbox)
    
    return cropped_image

def plot_image(image):
    plt.imshow(image, cmap='gray')
    plt.title('Generated Text Image')
    plt.axis('off')  # Hide axes for better visualization
    plt.show()

def image_to_3d_mesh(image, extrusion_height):
    data = np.array(image)
    height, width = data.shape
    vertices = []
    faces = []

    for y in range(height - 1):
        for x in range(width - 1):
            if data[y, x] == 0:  # If the pixel is black, create vertices and faces
                # Bottom vertices
                v0 = [x, y, 0]
                v1 = [x + 1, y, 0]
                v2 = [x + 1, y + 1, 0]
                v3 = [x, y + 1, 0]
                # Top vertices
                v4 = [x, y, extrusion_height]
                v5 = [x + 1, y, extrusion_height]
                v6 = [x + 1, y + 1, extrusion_height]
                v7 = [x, y + 1, extrusion_height]

                start_index = len(vertices)
                vertices.extend([v0, v1, v2, v3, v4, v5, v6, v7])
                
                # Add faces for the bottom, top, and sides
                faces.extend([
                    [start_index, start_index+1, start_index+2],
                    [start_index, start_index+2, start_index+3],
                    [start_index+4, start_index+5, start_index+6],
                    [start_index+4, start_index+6, start_index+7],
                    [start_index, start_index+1, start_index+5],
                    [start_index, start_index+5, start_index+4],
                    [start_index+1, start_index+2, start_index+6],
                    [start_index+1, start_index+6, start_index+5],
                    [start_index+2, start_index+3, start_index+7],
                    [start_index+2, start_index+7, start_index+6],
                    [start_index+3, start_index+0, start_index+4],
                    [start_index+3, start_index+4, start_index+7]
                ])
    
    vertices = np.array(vertices)
    faces = np.array(faces)
    return vertices, faces

def save_stl(vertices, faces, filename):
    text_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            text_mesh.vectors[i][j] = vertices[f[j], :]
    text_mesh.save(filename)

# Input text, font path, font size, and extrusion height
# text = input("Enter the text: ")
# font_path = input("Enter the path to the font file (e.g., Arial.ttf): ")
# font_size = int(input("Enter the font size: "))
# extrusion_height = float(input("Enter the extrusion height: "))

# Create the text image
# text_image = create_text_image(text, font_path, font_size)
text_image = create_text_image("casa", "caso", 25)

# Plot the text image for debugging
plot_image(text_image)

# Convert the image to a 3D mesh
# vertices, faces = image_to_3d_mesh(text_image, extrusion_height)
vertices, faces = image_to_3d_mesh(text_image, 20)

# Save the mesh to an STL file
output_filename = "text_output.stl"
save_stl(vertices, faces, output_filename)

print(f"STL file saved as {output_filename}")