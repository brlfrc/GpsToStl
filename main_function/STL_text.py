from PIL import Image, ImageDraw, ImageFont
import numpy as np
from itertools import product

import trimesh
from main_function.STL_function import writeSTL


def generate_text_image(text, font = "arial.ttf",  font_size=50, padding=20):
    """
    Genera un'immagine in scala di grigi del testo fornito.
    :param text: Il testo da visualizzare.
    :param font_size: La dimensione del font.
    :return: Immagine del testo in scala di grigi.
    """
    font = ImageFont.truetype(font, font_size)

    dummy_image = Image.new('L', (1, 1), color=0)
    draw = ImageDraw.Draw(dummy_image)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

    image_width = text_width + padding * 2
    image_height = text_height + padding * 2

    image = Image.new('L', (image_width, image_height), color=0)
    draw = ImageDraw.Draw(image)
    
    draw.text((padding, padding), text, font=font, fill=255)

    return image

def crop_array(A):
    non_zero_rows = np.any(A != 0, axis=1)
    non_zero_cols = np.any(A != 0, axis=0)

    first_row = np.argmax(non_zero_rows)
    last_row = len(non_zero_rows) - np.argmax(non_zero_rows[::-1]) - 1

    first_col = np.argmax(non_zero_cols)
    last_col = len(non_zero_cols) - np.argmax(non_zero_cols[::-1]) - 1

    cropped_A = A[first_row:last_row + 1, first_col:last_col + 1]

    cropped_A_with_zeros = np.pad(cropped_A, ((1, 1), (1, 1)), mode='constant', constant_values=0)

    return cropped_A_with_zeros



def roll2d(image, shifts):
    return np.roll(np.roll(image, shifts[0], axis=0), shifts[1], axis=1)

def numpy2stl(image, fn = 'tmp_STL/title_STL.stl',scale=0.1, mask_val=None,
                  solid=True,  min_thickness_percent=0.1):
    
    A = np.array(image) / 255.0  
    A = crop_array(A)
    
    m, n = A.shape
    A = scale * (A - A.min())

    if not mask_val:
        mask_val = A.min() - 1.

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
    
    mesh = trimesh.load(fn)
    trimesh.repair.fill_holes(mesh)
    trimesh.repair.fix_normals(mesh)
    trimesh.repair.fix_inversion(mesh)
    trimesh.repair.fix_winding(mesh)
    mesh.export(fn)

    return mesh


def generate_text_STL (text= 'Example 1', font = "arial.ttf",  font_size=50 ):
    text_image = generate_text_image(text, font,  font_size)

    return numpy2stl(text_image, scale=5, solid=True)