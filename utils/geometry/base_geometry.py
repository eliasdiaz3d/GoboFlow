"""
Sistema de geometría base para GoboFlow
Define las clases fundamentales para manejar geometrías 2D
"""

import math
from typing import List, Tuple, Optional, Any, Dict
from abc import ABC, abstractmethod

class Geometry(ABC):
    """
    Clase base abstracta para todas las geometrías
    """
    
    def __init__(self):
        self.vertices: List[Tuple[float, float]] = []
        self.edges: List[Tuple[int, int]] = []
        self.properties: Dict[str, Any] = {}
        self._bbox: Optional[Tuple[float, float, float, float]] = None
        self._area: Optional[float] = None
        self._perimeter: Optional[float] = None
        self._center: Optional[Tuple[float, float]] = None
    
    @abstractmethod
    def get_svg_path(self) -> str:
        """Retorna el path SVG para esta geometría"""
        pass
    
    @abstractmethod
    def calculate_bounds(self) -> Tuple[float, float, float, float]:
        """Calcula los límites de la geometría (min_x, min_y, max_x, max_y)"""
        pass
    
    @abstractmethod
    def calculate_area(self) -> float:
        """Calcula el área de la geometría"""
        pass
    
    @abstractmethod
    def calculate_perimeter(self) -> float:
        """Calcula el perímetro de la geometría"""
        pass
    
    @property
    def bbox(self) -> Tuple[float, float, float, float]:
        """Bounding box de la geometría"""
        if self._bbox is None:
            self._bbox = self.calculate_bounds()
        return self._bbox
    
    @property
    def area(self) -> float:
        """Área de la geometría"""
        if self._area is None:
            self._area = self.calculate_area()
        return self._area
    
    @property
    def perimeter(self) -> float:
        """Perímetro de la geometría"""
        if self._perimeter is None:
            self._perimeter = self.calculate_perimeter()
        return self._perimeter
    
    @property
    def center(self) -> Tuple[float, float]:
        """Centro de la geometría"""
        if self._center is None:
            bbox = self.bbox
            self._center = (
                (bbox[0] + bbox[2]) / 2,
                (bbox[1] + bbox[3]) / 2
            )
        return self._center
    
    def invalidate_cache(self):
        """Invalida el cache de propiedades calculadas"""
        self._bbox = None
        self._area = None
        self._perimeter = None
        self._center = None
    
    def transform(self, translation: Tuple[float, float] = (0, 0), 
                  rotation: float = 0, scale: Tuple[float, float] = (1, 1),
                  origin: Optional[Tuple[float, float]] = None) -> 'Geometry':
        """
        Aplica transformaciones a la geometría
        
        Args:
            translation: Traslación (dx, dy)
            rotation: Rotación en radianes
            scale: Escala (sx, sy)
            origin: Punto de origen para rotación y escala
        """
        if origin is None:
            origin = self.center
        
        # Crear copia de la geometría
        transformed = self.copy()
        
        # Aplicar transformaciones a los vértices
        new_vertices = []
        for x, y in transformed.vertices:
            # Trasladar al origen
            x -= origin[0]
            y -= origin[1]
            
            # Escalar
            x *= scale[0]
            y *= scale[1]
            
            # Rotar
            if rotation != 0:
                cos_r = math.cos(rotation)
                sin_r = math.sin(rotation)
                new_x = x * cos_r - y * sin_r
                new_y = x * sin_r + y * cos_r
                x, y = new_x, new_y
            
            # Trasladar de vuelta y aplicar traslación
            x += origin[0] + translation[0]
            y += origin[1] + translation[1]
            
            new_vertices.append((x, y))
        
        transformed.vertices = new_vertices
        transformed.invalidate_cache()
        
        return transformed
    
    @abstractmethod
    def copy(self) -> 'Geometry':
        """Crea una copia de la geometría"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa la geometría a diccionario"""
        return {
            'type': self.__class__.__name__,
            'vertices': self.vertices,
            'edges': self.edges,
            'properties': self.properties
        }
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(vertices={len(self.vertices)})"

class Circle(Geometry):
    """
    Geometría de círculo
    """
    
    def __init__(self, center: Tuple[float, float] = (0, 0), radius: float = 100, segments: int = 32):
        super().__init__()
        self.circle_center = center
        self.radius = radius
        self.segments = max(3, segments)  # Mínimo 3 segmentos
        self.properties = {
            'type': 'circle',
            'center': center,
            'radius': radius,
            'segments': segments
        }
        self._generate_vertices()
    
    def _generate_vertices(self):
        """Genera los vértices del círculo"""
        self.vertices = []
        self.edges = []
        
        cx, cy = self.circle_center
        
        # Generar vértices
        for i in range(self.segments):
            angle = 2 * math.pi * i / self.segments
            x = cx + self.radius * math.cos(angle)
            y = cy + self.radius * math.sin(angle)
            self.vertices.append((x, y))
        
        # Generar edges (conexiones entre vértices)
        for i in range(self.segments):
            next_i = (i + 1) % self.segments
            self.edges.append((i, next_i))
        
        self.invalidate_cache()
    
    def get_svg_path(self) -> str:
        """Retorna el path SVG del círculo"""
        cx, cy = self.circle_center
        r = self.radius
        
        # Usar circle element para SVG más limpio
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="white" opacity="0.8"/>'
    
    def calculate_bounds(self) -> Tuple[float, float, float, float]:
        """Calcula los límites del círculo"""
        cx, cy = self.circle_center
        r = self.radius
        return (cx - r, cy - r, cx + r, cy + r)
    
    def calculate_area(self) -> float:
        """Calcula el área del círculo"""
        return math.pi * self.radius * self.radius
    
    def calculate_perimeter(self) -> float:
        """Calcula el perímetro del círculo"""
        return 2 * math.pi * self.radius
    
    def copy(self) -> 'Circle':
        """Crea una copia del círculo"""
        return Circle(self.circle_center, self.radius, self.segments)
    
    def set_radius(self, radius: float):
        """Cambia el radio del círculo"""
        self.radius = max(0, radius)
        self.properties['radius'] = self.radius
        self._generate_vertices()
    
    def set_center(self, center: Tuple[float, float]):
        """Cambia el centro del círculo"""
        self.circle_center = center
        self.properties['center'] = center
        self._generate_vertices()
    
    def set_segments(self, segments: int):
        """Cambia el número de segmentos"""
        self.segments = max(3, segments)
        self.properties['segments'] = self.segments
        self._generate_vertices()

class Rectangle(Geometry):
    """
    Geometría de rectángulo
    """
    
    def __init__(self, center: Tuple[float, float] = (0, 0), 
                 width: float = 200, height: float = 100):
        super().__init__()
        self.rect_center = center
        self.width = width
        self.height = height
        self.properties = {
            'type': 'rectangle',
            'center': center,
            'width': width,
            'height': height
        }
        self._generate_vertices()
    
    def _generate_vertices(self):
        """Genera los vértices del rectángulo"""
        cx, cy = self.rect_center
        w2, h2 = self.width / 2, self.height / 2
        
        self.vertices = [
            (cx - w2, cy - h2),  # Esquina inferior izquierda
            (cx + w2, cy - h2),  # Esquina inferior derecha
            (cx + w2, cy + h2),  # Esquina superior derecha
            (cx - w2, cy + h2)   # Esquina superior izquierda
        ]
        
        self.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0)
        ]
        
        self.invalidate_cache()
    
    def get_svg_path(self) -> str:
        """Retorna el path SVG del rectángulo"""
        cx, cy = self.rect_center
        w, h = self.width, self.height
        x = cx - w / 2
        y = cy - h / 2
        
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white" opacity="0.8"/>'
    
    def calculate_bounds(self) -> Tuple[float, float, float, float]:
        """Calcula los límites del rectángulo"""
        cx, cy = self.rect_center
        w2, h2 = self.width / 2, self.height / 2
        return (cx - w2, cy - h2, cx + w2, cy + h2)
    
    def calculate_area(self) -> float:
        """Calcula el área del rectángulo"""
        return self.width * self.height
    
    def calculate_perimeter(self) -> float:
        """Calcula el perímetro del rectángulo"""
        return 2 * (self.width + self.height)
    
    def copy(self) -> 'Rectangle':
        """Crea una copia del rectángulo"""
        return Rectangle(self.rect_center, self.width, self.height)
    
    def set_size(self, width: float, height: float):
        """Cambia el tamaño del rectángulo"""
        self.width = max(0, width)
        self.height = max(0, height)
        self.properties['width'] = self.width
        self.properties['height'] = self.height
        self._generate_vertices()
    
    def set_center(self, center: Tuple[float, float]):
        """Cambia el centro del rectángulo"""
        self.rect_center = center
        self.properties['center'] = center
        self._generate_vertices()

class Polygon(Geometry):
    """
    Geometría de polígono general
    """
    
    def __init__(self, vertices: List[Tuple[float, float]]):
        super().__init__()
        self.vertices = vertices.copy()
        self.properties = {
            'type': 'polygon',
            'vertex_count': len(vertices)
        }
        self._generate_edges()
    
    def _generate_edges(self):
        """Genera las aristas del polígono"""
        self.edges = []
        vertex_count = len(self.vertices)
        
        for i in range(vertex_count):
            next_i = (i + 1) % vertex_count
            self.edges.append((i, next_i))
        
        self.invalidate_cache()
    
    def get_svg_path(self) -> str:
        """Retorna el path SVG del polígono"""
        if not self.vertices:
            return ""
        
        path_data = f"M {self.vertices[0][0]} {self.vertices[0][1]}"
        
        for x, y in self.vertices[1:]:
            path_data += f" L {x} {y}"
        
        path_data += " Z"  # Cerrar el path
        
        return f'<path d="{path_data}" fill="white" opacity="0.8"/>'
    
    def calculate_bounds(self) -> Tuple[float, float, float, float]:
        """Calcula los límites del polígono"""
        if not self.vertices:
            return (0, 0, 0, 0)
        
        xs = [x for x, y in self.vertices]
        ys = [y for x, y in self.vertices]
        
        return (min(xs), min(ys), max(xs), max(ys))
    
    def calculate_area(self) -> float:
        """Calcula el área del polígono usando la fórmula del shoelace"""
        if len(self.vertices) < 3:
            return 0.0
        
        area = 0.0
        n = len(self.vertices)
        
        for i in range(n):
            j = (i + 1) % n
            area += self.vertices[i][0] * self.vertices[j][1]
            area -= self.vertices[j][0] * self.vertices[i][1]
        
        return abs(area) / 2.0
    
    def calculate_perimeter(self) -> float:
        """Calcula el perímetro del polígono"""
        if len(self.vertices) < 2:
            return 0.0
        
        perimeter = 0.0
        n = len(self.vertices)
        
        for i in range(n):
            j = (i + 1) % n
            dx = self.vertices[j][0] - self.vertices[i][0]
            dy = self.vertices[j][1] - self.vertices[i][1]
            perimeter += math.sqrt(dx * dx + dy * dy)
        
        return perimeter
    
    def copy(self) -> 'Polygon':
        """Crea una copia del polígono"""
        return Polygon(self.vertices)

class CompositeGeometry(Geometry):
    """
    Geometría compuesta por múltiples geometrías
    """
    
    def __init__(self, geometries: List[Geometry] = None):
        super().__init__()
        self.geometries = geometries or []
        self.properties = {
            'type': 'composite',
            'geometry_count': len(self.geometries)
        }
        self._update_vertices()
    
    def _update_vertices(self):
        """Actualiza vértices y aristas basado en las geometrías componentes"""
        self.vertices = []
        self.edges = []
        
        vertex_offset = 0
        
        for geometry in self.geometries:
            # Añadir vértices
            self.vertices.extend(geometry.vertices)
            
            # Añadir aristas con offset
            for edge in geometry.edges:
                new_edge = (edge[0] + vertex_offset, edge[1] + vertex_offset)
                self.edges.append(new_edge)
            
            vertex_offset += len(geometry.vertices)
        
        self.invalidate_cache()
    
    def add_geometry(self, geometry: Geometry):
        """Añade una geometría al compuesto"""
        self.geometries.append(geometry)
        self.properties['geometry_count'] = len(self.geometries)
        self._update_vertices()
    
    def remove_geometry(self, index: int):
        """Remueve una geometría por índice"""
        if 0 <= index < len(self.geometries):
            del self.geometries[index]
            self.properties['geometry_count'] = len(self.geometries)
            self._update_vertices()
    
    def get_svg_path(self) -> str:
        """Retorna el path SVG del compuesto"""
        svg_elements = []
        
        for geometry in self.geometries:
            svg_elements.append(geometry.get_svg_path())
        
        return '\n  '.join(svg_elements)
    
    def calculate_bounds(self) -> Tuple[float, float, float, float]:
        """Calcula los límites del compuesto"""
        if not self.geometries:
            return (0, 0, 0, 0)
        
        bounds = [geom.bbox for geom in self.geometries]
        
        min_x = min(bound[0] for bound in bounds)
        min_y = min(bound[1] for bound in bounds)
        max_x = max(bound[2] for bound in bounds)
        max_y = max(bound[3] for bound in bounds)
        
        return (min_x, min_y, max_x, max_y)
    
    def calculate_area(self) -> float:
        """Calcula el área total del compuesto"""
        return sum(geom.area for geom in self.geometries)
    
    def calculate_perimeter(self) -> float:
        """Calcula el perímetro total del compuesto"""
        return sum(geom.perimeter for geom in self.geometries)
    
    def copy(self) -> 'CompositeGeometry':
        """Crea una copia del compuesto"""
        copied_geometries = [geom.copy() for geom in self.geometries]
        return CompositeGeometry(copied_geometries)

# ===========================================
# UTILIDADES DE GEOMETRÍA
# ===========================================

def distance_between_points(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calcula la distancia entre dos puntos"""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.sqrt(dx * dx + dy * dy)

def angle_between_points(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calcula el ángulo entre dos puntos en radianes"""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.atan2(dy, dx)

def rotate_point(point: Tuple[float, float], angle: float, 
                origin: Tuple[float, float] = (0, 0)) -> Tuple[float, float]:
    """Rota un punto alrededor de un origen"""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    
    # Trasladar al origen
    x = point[0] - origin[0]
    y = point[1] - origin[1]
    
    # Rotar
    new_x = x * cos_a - y * sin_a
    new_y = x * sin_a + y * cos_a
    
    # Trasladar de vuelta
    return (new_x + origin[0], new_y + origin[1])

def scale_point(point: Tuple[float, float], scale: Tuple[float, float],
               origin: Tuple[float, float] = (0, 0)) -> Tuple[float, float]:
    """Escala un punto desde un origen"""
    # Trasladar al origen
    x = point[0] - origin[0]
    y = point[1] - origin[1]
    
    # Escalar
    x *= scale[0]
    y *= scale[1]
    
    # Trasladar de vuelta
    return (x + origin[0], y + origin[1])

def create_regular_polygon(center: Tuple[float, float], radius: float, 
                          sides: int) -> Polygon:
    """Crea un polígono regular"""
    vertices = []
    
    for i in range(sides):
        angle = 2 * math.pi * i / sides
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        vertices.append((x, y))
    
    return Polygon(vertices)

def create_star(center: Tuple[float, float], outer_radius: float, 
               inner_radius: float, points: int) -> Polygon:
    """Crea una estrella"""
    vertices = []
    
    for i in range(points * 2):
        angle = math.pi * i / points
        radius = outer_radius if i % 2 == 0 else inner_radius
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        vertices.append((x, y))
    
    return Polygon(vertices)

def geometry_from_svg_path(svg_path: str) -> Optional[Geometry]:
    """
    Convierte un path SVG básico a geometría
    Implementación simplificada para paths básicos
    """
    # TODO: Implementar parser completo de SVG paths
    # Por ahora, retorna None
    return None

def export_geometries_to_svg(geometries: List[Geometry], 
                           width: int = 1024, height: int = 1024,
                           background: str = "black") -> str:
    """
    Exporta una lista de geometrías a SVG completo
    """
    # Calcular bounding box total
    if geometries:
        all_bounds = [geom.bbox for geom in geometries]
        min_x = min(bound[0] for bound in all_bounds)
        min_y = min(bound[1] for bound in all_bounds)
        max_x = max(bound[2] for bound in all_bounds)
        max_y = max(bound[3] for bound in all_bounds)
        
        # Añadir margen
        margin = 50
        viewbox_x = min_x - margin
        viewbox_y = min_y - margin
        viewbox_w = (max_x - min_x) + 2 * margin
        viewbox_h = (max_y - min_y) + 2 * margin
    else:
        viewbox_x, viewbox_y = 0, 0
        viewbox_w, viewbox_h = width, height
    
    # Crear SVG
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{width}" height="{height}" 
     viewBox="{viewbox_x} {viewbox_y} {viewbox_w} {viewbox_h}"
     style="background: {background};">
  
  <!-- Gobos generados por GoboFlow -->
'''
    
    # Añadir geometrías
    for i, geometry in enumerate(geometries):
        svg_content += f"  <!-- Geometría {i+1}: {geometry.__class__.__name__} -->\n"
        svg_content += f"  {geometry.get_svg_path()}\n"
    
    # Añadir información del archivo
    svg_content += f'''  
  <!-- Información del archivo -->
  <text x="{viewbox_x + 20}" y="{viewbox_y + viewbox_h - 20}" 
        fill="white" font-family="Arial" font-size="16" opacity="0.7">
    GoboFlow - {len(geometries)} geometría(s)
  </text>
  
</svg>'''
    
    return svg_content

# ===========================================
# PRUEBAS DE GEOMETRÍA
# ===========================================

def test_geometries():
    """Pruebas básicas de las geometrías"""
    print("🧪 Probando geometrías...")
    
    # Probar Circle
    circle = Circle((100, 100), 50)
    assert abs(circle.area - math.pi * 50 * 50) < 0.01
    assert abs(circle.perimeter - 2 * math.pi * 50) < 0.01
    assert circle.center == (100, 100)
    print("✅ Circle OK")
    
    # Probar Rectangle
    rect = Rectangle((0, 0), 100, 50)
    assert rect.area == 5000
    assert rect.perimeter == 300
    assert rect.center == (0, 0)
    print("✅ Rectangle OK")
    
    # Probar Polygon (triángulo)
    triangle = Polygon([(0, 0), (100, 0), (50, 87)])
    assert triangle.calculate_area() > 0
    assert len(triangle.vertices) == 3
    print("✅ Polygon OK")
    
    # Probar CompositeGeometry
    composite = CompositeGeometry([circle, rect])
    assert len(composite.geometries) == 2
    assert composite.area > 0
    print("✅ CompositeGeometry OK")
    
    # Probar transformaciones
    transformed_circle = circle.transform(translation=(50, 50))
    assert transformed_circle.center == (150, 150)
    print("✅ Transformaciones OK")
    
    # Probar exportación SVG
    svg = export_geometries_to_svg([circle, rect])
    assert "<svg" in svg
    assert "circle" in svg
    assert "rect" in svg
    print("✅ Exportación SVG OK")
    
    print("🎉 Todos los tests de geometría pasaron!")

if __name__ == "__main__":
    test_geometries()