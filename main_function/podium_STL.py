import trimesh

def create_podium(width=50, depth=50, height=10, shape="rectangular"):
    """Crea una mesh podio su cui posizionare la traccia GPS."""
    if shape == "rectangular":
        podium = trimesh.creation.box(extents=(width, depth, height))
    elif shape == "cylindrical":
        podium = trimesh.creation.cylinder(radius=width / 2, height=height)
    
    return podium