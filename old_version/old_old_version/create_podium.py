import trimesh
import numpy as np

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

# Creiamo il podio
podium_mesh = create_podium(shape='cylindrical')

# Visualizziamo il podio
# podium_mesh.show()

# Carica il modello STL della salita
track_mesh = trimesh.load("AAAA.stl")
track_mesh = create_podium()

# Visualizza il modello caricato (opzionale)
# track_mesh.show()

combined_mesh=merge_podium_and_track(track_mesh, podium_mesh)

combined_mesh.show()