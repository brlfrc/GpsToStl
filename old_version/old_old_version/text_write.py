from PIL import Image, ImageDraw, ImageFont
import numpy as np
import matplotlib.pyplot as plt
import trimesh
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import numpy as np
from itertools import product
import struct

ASCII_FACET = """  facet normal  {face[0]:e}  {face[1]:e}  {face[2]:e}
    outer loop
      vertex    {face[3]:e}  {face[4]:e}  {face[5]:e}
      vertex    {face[6]:e}  {face[7]:e}  {face[8]:e}
      vertex    {face[9]:e}  {face[10]:e}  {face[11]:e}
    endloop
  endfacet"""

BINARY_HEADER = "80sI"
BINARY_FACET = "12fH"


def generate_text_image(text, font_size=50, padding=20):
    """
    Genera un'immagine in scala di grigi del testo fornito.
    :param text: Il testo da visualizzare.
    :param font_size: La dimensione del font.
    :return: Immagine del testo in scala di grigi.
    """
    # Usa un font standard di sistema
    font = ImageFont.truetype("arial.ttf", font_size)

    # Crea un'immagine dummy per ottenere le dimensioni del testo
    dummy_image = Image.new('L', (1, 1), color=0)
    draw = ImageDraw.Draw(dummy_image)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

     # Aggiungi il padding
    image_width = text_width + padding * 2
    image_height = text_height + padding * 2

    # Crea un'immagine reale per il testo
    image = Image.new('L', (image_width, image_height), color=0)
    draw = ImageDraw.Draw(image)
    
    # Disegna il testo centrato
    draw.text((padding, padding), text, font=font, fill=255)

    return image

def crop_array(A):
    # Trova le righe e colonne che contengono almeno un valore non zero
    non_zero_rows = np.any(A != 0, axis=1)
    non_zero_cols = np.any(A != 0, axis=0)

    # Ottieni gli indici della prima e ultima riga non zero
    first_row = np.argmax(non_zero_rows)
    last_row = len(non_zero_rows) - np.argmax(non_zero_rows[::-1]) - 1

    # Ottieni gli indici della prima e ultima colonna non zero
    first_col = np.argmax(non_zero_cols)
    last_col = len(non_zero_cols) - np.argmax(non_zero_cols[::-1]) - 1

    # Ritaglia l'array
    cropped_A = A[first_row:last_row + 1, first_col:last_col + 1]

    # Aggiungi una riga e una colonna di zeri attorno
    cropped_A_with_zeros = np.pad(cropped_A, ((1, 1), (1, 1)), mode='constant', constant_values=0)

    return cropped_A_with_zeros


def _build_binary_stl(facets):
    """returns a string of binary binary data for the stl file"""

    lines = [struct.pack(BINARY_HEADER, b'Binary STL Writer', len(facets)), ]
    for facet in facets:
        facet = list(facet)
        facet.append(0)  # need to pad the end with a unsigned short byte
        lines.append(struct.pack(BINARY_FACET, *facet))
    return lines

def _build_ascii_stl(facets):
    """returns a list of ascii lines for the stl file """

    lines = ['solid ffd_geom', ]
    for facet in facets:
        lines.append(ASCII_FACET.format(face=facet))
    lines.append('endsolid ffd_geom')
    return lines


def writeSTL(facets, file_name, ascii=False):
    """writes an ASCII or binary STL file"""

    f = open(file_name, 'wb')
    if ascii:
        lines = _build_ascii_stl(facets)
        lines_ = "\n".join(lines).encode("UTF-8")
        f.write(lines_)
    else:
        data = _build_binary_stl(facets)
        data = b"".join(data)
        f.write(data)

    f.close()

def roll2d(image, shifts):
    return np.roll(np.roll(image, shifts[0], axis=0), shifts[1], axis=1)

def numpy2stl_GPT(image, fn = 'scritta_STL.stl',scale=0.1, mask_val=None,
                  solid=True,  min_thickness_percent=0.1):
    
    A = np.array(image) / 255.0  # Normalizza tra 0 e 1
    A = crop_array(A)
    
    m, n = A.shape
    A = scale * (A - A.min())

    if not mask_val:
        mask_val = A.min() - 1.

    # show_array_as_image(A)
    vertices = []
    facets = []
    mask = np.zeros((m, n))
    
    print("Creating top mesh...")

    for i, k in product(range(m - 1), range(n - 1)):

        this_pt = np.array([i - m / 2., k - n / 2., A[i, k]])
        top_right = np.array([i - m / 2., k + 1 - n / 2., A[i, k + 1]])
        bottom_left = np.array([i + 1. - m / 2., k - n / 2., A[i + 1, k]])
        bottom_right = np.array([i + 1. - m / 2., k + 1 - n / 2., A[i + 1, k + 1]])

        n1, n2 = np.zeros(3), np.zeros(3)

        if (this_pt[-1] > mask_val and top_right[-1] > mask_val and bottom_left[-1] > mask_val):

            facet = np.concatenate([n1, top_right, this_pt, bottom_right])
            mask[i, k] = 1
            mask[i, k + 1] = 1
            mask[i + 1, k] = 1
            facets.append(facet)

        if (this_pt[-1] > mask_val and bottom_right[-1] > mask_val and
                bottom_left[-1] > mask_val):

            facet = np.concatenate([n2, bottom_right, this_pt, bottom_left])
            facets.append(facet)
            mask[i, k] = 1
            mask[i + 1, k + 1] = 1
            mask[i + 1, k] = 1

    facets = np.array(facets)

    if solid:
        print("Computed edges...")
        edge_mask = np.sum([roll2d(mask, (i, k))
                            for i, k in product([-1, 0, 1], repeat=2)],
                            axis=0)
        edge_mask[np.where(edge_mask == 9.)] = 0.
        edge_mask[np.where(edge_mask != 0.)] = 1.
        edge_mask[0::m - 1, :] = 1.
        edge_mask[:, 0::n - 1] = 1.
        X, Y = np.where(edge_mask == 1.)
        locs = zip(X - m / 2., Y - n / 2.)

        zvals = facets[:, 5::3]
        zmin, zthickness = zvals.min(), np.ptp(zvals)
    
        minval = zmin - min_thickness_percent * zthickness

        bottom = []
        print("Extending edges, creating bottom...")
        for i, facet in enumerate(facets):
            if (facet[3], facet[4]) in locs:
                facets[i][5] = minval
            if (facet[6], facet[7]) in locs:
                facets[i][8] = minval
            if (facet[9], facet[10]) in locs:
                facets[i][11] = minval
            this_bottom = np.concatenate(
                [facet[:3], facet[6:8], [minval], facet[3:5], [minval],
                    facet[9:11], [minval]])
            bottom.append(this_bottom)

        facets = np.concatenate([facets, bottom])

    writeSTL(facets, fn, ascii=ascii)


def create_podium(width=50, depth=50, height=10, shape="rectangular"):
    """Crea una mesh podio su cui posizionare la traccia GPS."""
    if shape == "rectangular":
        podium = trimesh.creation.box(extents=(width, depth, height))
    elif shape == "cylindrical":
        podium = trimesh.creation.cylinder(radius=width / 2, height=height)
    
    return podium


def merge_podium_and_track(track_mesh, podium_mesh, track_offset=10):
    """Unisce il podio e la mesh della traccia in una mesh combinata."""
    # Sposta la traccia in modo che sia sopra il podio
    track_mesh.apply_translation([0, 0, track_offset])
    # Unisci le mesh
    combined_mesh = podium_mesh + track_mesh
    return combined_mesh

# Genera l'immagine del testo
text_image = generate_text_image("Presolana", font_size=50)


# Visualizza l'immagine per il debug
text_image.show()


text_mesh = numpy2stl_GPT(text_image, scale=5, solid=True)
mesh = trimesh.load('scritta_STL.stl')

mesh.show()
podium_mesh = create_podium(width=200, depth=200,shape='cylindrical')
combined_mesh=merge_podium_and_track(mesh, podium_mesh)
combined_mesh.show()
# Crea la mesh a partire dall'immagine
#text_mesh = create_text_mesh_from_image(text_image, scale=0.1, depth=1)
#text_mesh.show()


# Posiziona la mesh del testo sopra il podio (assicurati di avere `combined_mesh`)
#text_mesh.apply_translation([0, 0, 10])  # Aggiusta Z per posizionarlo sopra il podio

