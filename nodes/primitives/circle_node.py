"""
Nodo generador de círculos para GoboFlow
Genera geometría circular con parámetros configurables
"""

import math
from typing import Dict, List, Tuple, Any, Optional

from nodes.base.base_node import GeneratorNode
from core.socket_types import NumberType, VectorType, BooleanType, GeometryType

class CircleGeometry:
    """
    Representación de geometría circular para GoboFlow
    Contiene tanto la representación vectorial como datos para rasterización
    """
    
    def __init__(self, center: Tuple[float, float] = (0, 0), 
                 radius: float = 100.0, 
                 segments: int = 32,
                 filled: bool = True):
        self.center = center
        self.radius = radius
        self.segments = max(3, segments)  # Mínimo 3 segmentos
        self.filled = filled
        
        # Generar puntos del círculo
        self.points = self._generate_circle_points()
        
        # Metadatos de geometría
        self.geometry_type = "circle"
        self.bbox = self._calculate_bbox()
        
    def _generate_circle_points(self) -> List[Tuple[float, float]]:
        """Genera los puntos del perímetro del círculo"""
        points = []
        cx, cy = self.center
        
        for i in range(self.segments):
            angle = (2 * math.pi * i) / self.segments
            x = cx + self.radius * math.cos(angle)
            y = cy + self.radius * math.sin(angle)
            points.append((x, y))
            
        return points
    
    def _calculate_bbox(self) -> Tuple[float, float, float, float]:
        """Calcula el bounding box (min_x, min_y, max_x, max_y)"""
        cx, cy = self.center
        return (
            cx - self.radius,  # min_x
            cy - self.radius,  # min_y
            cx + self.radius,  # max_x
            cy + self.radius   # max_y
        )
    
    def get_svg_path(self) -> str:
        """Genera un path SVG del círculo"""
        cx, cy = self.center
        
        if self.filled:
            # Círculo relleno usando comando circle de SVG
            return f'<circle cx="{cx}" cy="{cy}" r="{self.radius}" fill="white" stroke="none"/>'
        else:
            # Círculo solo contorno
            return f'<circle cx="{cx}" cy="{cy}" r="{self.radius}" fill="none" stroke="white" stroke-width="1"/>'
    
    def get_polygon_points(self) -> List[Tuple[float, float]]:
        """Retorna los puntos como polígono aproximado"""
        return self.points.copy()
    
    def contains_point(self, x: float, y: float) -> bool:
        """Verifica si un punto está dentro del círculo"""
        cx, cy = self.center
        distance_sq = (x - cx) ** 2 + (y - cy) ** 2
        return distance_sq <= self.radius ** 2
    
    def get_area(self) -> float:
        """Calcula el área del círculo"""
        return math.pi * self.radius ** 2
    
    def get_perimeter(self) -> float:
        """Calcula el perímetro del círculo"""
        return 2 * math.pi * self.radius
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa la geometría a diccionario"""
        return {
            "type": "circle",
            "center": self.center,
            "radius": self.radius,
            "segments": self.segments,
            "filled": self.filled,
            "points": self.points,
            "bbox": self.bbox
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CircleGeometry':
        """Deserializa geometría desde diccionario"""
        return cls(
            center=data.get("center", (0, 0)),
            radius=data.get("radius", 100.0),
            segments=data.get("segments", 32),
            filled=data.get("filled", True)
        )

class CircleNode(GeneratorNode):
    """
    Nodo generador de círculos
    Crea geometría circular con parámetros configurables
    """
    
    NODE_TYPE = "circle"
    NODE_TITLE = "Circle"
    NODE_DESCRIPTION = "Generates a circular shape"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
        
        # Parámetros por defecto
        self.set_parameter("radius", 100.0)
        self.set_parameter("center_x", 0.0)
        self.set_parameter("center_y", 0.0)
        self.set_parameter("segments", 32)
        self.set_parameter("filled", True)
        
    def _init_sockets(self):
        """Inicializa los sockets del nodo círculo"""
        # Inputs para parámetros del círculo
        self.add_input("radius", NumberType(), default_value=100.0)
        self.add_input("center", VectorType(), default_value=(0.0, 0.0, 0.0))
        self.add_input("segments", NumberType(), default_value=32)
        self.add_input("filled", BooleanType(), default_value=True)
        
        # Output de geometría
        self.add_output("geometry", GeometryType())
        
        # Outputs adicionales para información
        self.add_output("area", NumberType())
        self.add_output("perimeter", NumberType())
        self.add_output("bbox", VectorType())  # Como vector 4D (min_x, min_y, max_x, max_y)
    
    def generate_geometry(self) -> CircleGeometry:
        """Genera la geometría del círculo"""
        # Obtener valores de inputs o parámetros internos
        radius = self._get_radius()
        center = self._get_center()
        segments = self._get_segments()
        filled = self._get_filled()
        
        # Crear geometría del círculo
        circle = CircleGeometry(
            center=center,
            radius=radius,
            segments=segments,
            filled=filled
        )
        
        return circle
    
    def _get_radius(self) -> float:
        """Obtiene el radio desde input o parámetro"""
        input_radius = self.get_input_value("radius")
        if input_radius is not None:
            try:
                radius = float(input_radius)
                return max(0.1, radius)  # Mínimo 0.1 para evitar círculos invisibles
            except (ValueError, TypeError):
                pass
        return self.get_parameter("radius", 100.0)
    
    def _get_center(self) -> Tuple[float, float]:
        """Obtiene el centro desde input o parámetros"""
        input_center = self.get_input_value("center")
        if input_center is not None:
            try:
                if isinstance(input_center, (list, tuple)) and len(input_center) >= 2:
                    return (float(input_center[0]), float(input_center[1]))
            except (ValueError, TypeError):
                pass
        
        # Usar parámetros internos
        x = self.get_parameter("center_x", 0.0)
        y = self.get_parameter("center_y", 0.0)
        return (x, y)
    
    def _get_segments(self) -> int:
        """Obtiene el número de segmentos desde input o parámetro"""
        input_segments = self.get_input_value("segments")
        if input_segments is not None:
            try:
                segments = int(float(input_segments))
                return max(3, min(256, segments))  # Entre 3 y 256 segmentos
            except (ValueError, TypeError):
                pass
        return int(self.get_parameter("segments", 32))
    
    def _get_filled(self) -> bool:
        """Obtiene si está relleno desde input o parámetro"""
        input_filled = self.get_input_value("filled")
        if input_filled is not None:
            if isinstance(input_filled, bool):
                return input_filled
            try:
                return bool(input_filled)
            except (ValueError, TypeError):
                pass
        return self.get_parameter("filled", True)
    
    def compute(self) -> Dict[str, Any]:
        """Computa todos los outputs del nodo"""
        # Generar geometría
        circle = self.generate_geometry()
        
        # Calcular outputs adicionales
        area = circle.get_area()
        perimeter = circle.get_perimeter()
        bbox = circle.bbox  # (min_x, min_y, max_x, max_y)
        
        return {
            "geometry": circle,
            "area": area,
            "perimeter": perimeter,
            "bbox": bbox
        }
    
    def get_preview_info(self) -> Dict[str, Any]:
        """Información para preview en la UI"""
        try:
            circle = self.generate_geometry()
            return {
                "type": "circle",
                "center": circle.center,
                "radius": circle.radius,
                "area": circle.get_area(),
                "perimeter": circle.get_perimeter(),
                "segments": circle.segments,
                "filled": circle.filled
            }
        except Exception:
            return {"type": "circle", "error": True}
    
    def set_radius(self, radius: float):
        """Método de conveniencia para establecer el radio"""
        self.set_parameter("radius", max(0.1, float(radius)))
    
    def set_center(self, x: float, y: float):
        """Método de conveniencia para establecer el centro"""
        self.set_parameter("center_x", float(x))
        self.set_parameter("center_y", float(y))
    
    def set_segments(self, segments: int):
        """Método de conveniencia para establecer segmentos"""
        self.set_parameter("segments", max(3, min(256, int(segments))))
    
    def set_filled(self, filled: bool):
        """Método de conveniencia para establecer si está relleno"""
        self.set_parameter("filled", bool(filled))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialización del nodo incluyendo geometría"""
        data = super().to_dict()
        
        # Añadir información específica del círculo para serialización
        try:
            circle = self.generate_geometry()
            data["geometry_data"] = circle.to_dict()
        except Exception:
            data["geometry_data"] = None
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CircleNode':
        """Deserialización del nodo"""
        node = super().from_dict(data)
        
        # Restaurar geometría si existe
        geometry_data = data.get("geometry_data")
        if geometry_data:
            try:
                # Los parámetros ya están restaurados por BaseNode
                pass
            except Exception:
                pass
                
        return node

# Utilidades adicionales para trabajar con círculos

def create_circle_grid(rows: int, cols: int, spacing: float, radius: float) -> List[CircleGeometry]:
    """Crea una grilla de círculos"""
    circles = []
    
    start_x = -(cols - 1) * spacing / 2
    start_y = -(rows - 1) * spacing / 2
    
    for row in range(rows):
        for col in range(cols):
            x = start_x + col * spacing
            y = start_y + row * spacing
            circle = CircleGeometry(center=(x, y), radius=radius)
            circles.append(circle)
    
    return circles

def create_concentric_circles(center: Tuple[float, float], 
                            min_radius: float, 
                            max_radius: float, 
                            count: int) -> List[CircleGeometry]:
    """Crea círculos concéntricos"""
    circles = []
    
    for i in range(count):
        t = i / (count - 1) if count > 1 else 0
        radius = min_radius + (max_radius - min_radius) * t
        circle = CircleGeometry(center=center, radius=radius, filled=False)
        circles.append(circle)
    
    return circles

def circle_intersects_circle(circle1: CircleGeometry, circle2: CircleGeometry) -> bool:
    """Verifica si dos círculos se intersectan"""
    dx = circle1.center[0] - circle2.center[0]
    dy = circle1.center[1] - circle2.center[1]
    distance = math.sqrt(dx * dx + dy * dy)
    
    return distance < (circle1.radius + circle2.radius)

# Registro del nodo
CIRCLE_NODE_REGISTRY = {
    "circle": CircleNode
}