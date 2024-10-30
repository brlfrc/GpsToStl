import trimesh

class Podium:
    def __init__(self, width=50, depth=50, height=10, shape="rectangular"):
        """
        Inizializza un'istanza della classe Podium, creando una mesh per il podio.
        
        Parametri:
        - width: Larghezza del podio (o diametro se cilindrico).
        - depth: Profondità del podio (solo per forma rettangolare).
        - height: Altezza del podio.
        - shape: Forma del podio ("rectangular" o "cylindrical").
        """
        self.width = width
        self.depth = depth
        self.height = height
        self.shape = shape
        self.mesh = self._create_mesh()
        
    def _create_mesh(self):
        """Crea la mesh in base ai parametri dell'istanza."""
        if self.shape == "rectangular":
            # Crea una mesh di tipo box per il podio rettangolare
            podium = trimesh.creation.box(extents=(self.depth, self.width, self.height))
        elif self.shape == "cylindrical":
            # Crea una mesh di tipo cilindro per il podio circolare
            podium = trimesh.creation.cylinder(radius=self.width / 2, height=self.height)
            self.depth = self.width
        else:
            raise ValueError("Forma non supportata: scegli 'rectangular' o 'cylindrical'.")
        return podium

    def show(self):
        """Visualizza la mesh del podio."""
        self.mesh.show()

    def translate(self, translation_vector):
        """Applica una traslazione alla mesh del podio."""
        self.mesh.apply_translation(translation_vector)

    def rotate(self, angle, axis=(0, 0, 1)):
        """Applica una rotazione alla mesh del podio."""
        self.mesh.apply_rotation(trimesh.transformations.rotation_matrix(angle, axis))
