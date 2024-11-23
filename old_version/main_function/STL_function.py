import struct
import numpy as np
from itertools import product
import trimesh
import subprocess

ASCII_FACET = """  facet normal  {face[0]:e}  {face[1]:e}  {face[2]:e}
    outer loop
      vertex    {face[3]:e}  {face[4]:e}  {face[5]:e}
      vertex    {face[6]:e}  {face[7]:e}  {face[8]:e}
      vertex    {face[9]:e}  {face[10]:e}  {face[11]:e}
    endloop
  endfacet"""

BINARY_HEADER = "80sI"
BINARY_FACET = "12fH"


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

def crop_array(A, margin=2):
    non_zero_rows = np.any(A != 0, axis=1)
    non_zero_cols = np.any(A != 0, axis=0)

    first_row = np.argmax(non_zero_rows)
    last_row = len(non_zero_rows) - np.argmax(non_zero_rows[::-1]) - 1

    first_col = np.argmax(non_zero_cols)
    last_col = len(non_zero_cols) - np.argmax(non_zero_cols[::-1]) - 1

    # Calcola i margini reali per rimanere all'interno dei limiti di A
    top_margin = min(margin, first_row)  # Non va oltre il limite superiore
    bottom_margin = min(margin, len(A) - last_row - 1)  # Non va oltre il limite inferiore
    left_margin = min(margin, first_col)  # Non va oltre il limite sinistro
    right_margin = min(margin, len(A[0]) - last_col - 1)  # Non va oltre il limite destro

    # Esegui il ritaglio tenendo conto dei margini
    cropped_A = A[
        first_row - top_margin : last_row + 1 + bottom_margin,
        first_col - left_margin : last_col + 1 + right_margin
    ]

    # Aggiungi il padding di 1 unità di zeri tutto intorno
    cropped_A_with_zeros = np.pad(cropped_A, ((1, 1), (1, 1)), mode='constant', constant_values=0)

    return cropped_A_with_zeros

def roll2d(image, shifts):
    return np.roll(np.roll(image, shifts[0], axis=0), shifts[1], axis=1)

def numpy2stl(image, fn = 'tmp_STL/null.stl', scale=0.1, mask_val=None, rotation = True,
                  solid=True,  min_thickness_percent=0.1):
    
    A = np.array(image) / 255.0  
    A = crop_array(A)
    
    m, n = A.shape
    if n >= m and rotation:
        A = np.rot90(A, k=3)
        m, n = n, m
    
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

        if (this_pt[-1] > mask_val or top_right[-1] > mask_val or bottom_left[-1] > mask_val):

            facet = np.concatenate([n1, top_right, this_pt, bottom_right])
            mask[i, k] = 1
            mask[i, k + 1] = 1
            mask[i + 1, k] = 1
            facets.append(facet)

        if (this_pt[-1] > mask_val or bottom_right[-1] > mask_val or bottom_left[-1] > mask_val):

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
        locs = list(zip(X - m / 2., Y - n / 2.))

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

    mesh.export(fn)

    return mesh


def repair_with_blender (input_stl_path, output_stl_path):
    blender_path = r"C:\Program Files\Blender Foundation\Blender 2.91\blender.exe"
    script_path = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\blender_repair\repair_mesh.py"
    
    command = [
        blender_path, "--background", "--python", script_path,
        "--", input_stl_path, output_stl_path
    ]
    subprocess.run(command)

    # print("Repair completed. Model exported to:", output_stl_path)

def difference_with_blender (path_text, path_uphill, path_cube, path_magnet, path_final):
    blender_path = r"C:\Program Files\Blender Foundation\Blender 2.91\blender.exe"
    script_path = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\blender_repair\difference_mesh.py"
    
    command = [
        blender_path, "--background", "--python", script_path,
        "--", path_text, path_uphill, path_cube, path_magnet, path_final
    ]
    subprocess.run(command)



def union_with_blender (path_text, path_uphill, path_cube, path_magnet, path_uphill_diff):
    blender_path = r"C:\Program Files\Blender Foundation\Blender 2.91\blender.exe"
    script_path = r"C:\Users\utente\OneDrive - Universita degli Studi di Milano-Bicocca\Desktop\GpxToStl\blender_repair\union_mesh.py"
    
    command = [
        blender_path, "--background", "--python", script_path,
        "--", path_text, path_uphill, path_cube, path_magnet, path_uphill_diff
    ]
    subprocess.run(command)