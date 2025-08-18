"""
Nodo generador de rectángulos para GoboFlow
Genera geometría rectangular con parámetros configurables
"""

import math
from typing import Dict, List, Tuple, Any, Optional

from nodes.base.base_node import GeneratorNode
from core.socket_types import NumberType, VectorType, BooleanType, GeometryType

class RectangleGeometry:
    """
    Representación de geometría rectangular para GoboFlow
    Soporta esquinas redondeadas y diferentes modos de dimensionado
    """
    
    def __init__(self, center: Tuple[float, float] = (0, 0),
                 width: float = 200.0,
                 height: float = 100.0,
                 corner_radius: float = 0.0,
                 filled: bool = True):
        self.center = center
        self.width = max(1.0, width)  # Mínimo 1px
        self.height = max(1.0, height)  # Mínimo 1px
        self.corner_radius = max(0.0, min(corner_radius, min(width, height) / 2))
        self.filled = filled
        
        # Generar puntos del rectángulo
        self.points = self._generate_rectangle_points()
        
        # Metadatos de geometría
        self.geometry_type = "rectangle"
        self.bbox = self._calculate_bbox()
        
    def _generate_rectangle_points(self) -> List[Tuple[float, float]]:
        """Genera los puntos del contorno del rectángulo"""
        cx, cy = self.center
        half_w = self.width / 2
        half_h = self.height / 2
        
        if self.corner_radius == 0:
            # Rectángulo simple (4 puntos)
            return [
                (cx - half_w, cy - half_h),  # Top-left
                (cx + half_w, cy - half_h),  # Top-right
                (cx + half_w, cy + half_h),  # Bottom-right
                (cx - half_w, cy + half_h),  # Bottom-left
            ]
        else:
            # Rectángulo con esquinas redondeadas
            points = []
            r = self.corner_radius
            
            # Calcular puntos de las esquinas redondeadas
            # Se generan aproximadamente como polígonos
            segments_per_corner = max(4, int(r / 5))  # Más segmentos para radios grandes
            
            # Centros de los arcos de las esquinas
            corners = [
                (cx + half_w - r, cy - half_h + r),  # Top-right
                (cx + half_w - r, cy + half_h - r),  # Bottom-right
                (cx - half_w + r, cy + half_h - r),  # Bottom-left
                (cx - half_w + r, cy - half_h + r),  # Top-left
            ]
            
            # Ángulos iniciales para cada esquina
            start_angles = [3 * math.pi / 2, 0, math.pi / 2, math.pi]
            
            for i, (corner_x, corner_y) in enumerate(corners):
                start_angle = start_angles[i]
                
                for j in range(segments_per_corner + 1):
                    angle = start_angle + (math.pi / 2) * j / segments_per_corner
                    x = corner_x + r * math.cos(angle)
                    y = corner_y + r * math.sin(angle)
                    points.append((x, y))
            
            return points
    
    def _calculate_bbox(self) -> Tuple[float, float, float, float]:
        """Calcula el bounding box (min_x, min_y, max_x, max_y)"""
        cx, cy = self.center
        half_w = self.width / 2
        half_h = self.height / 2
        
        return (
            cx - half_w,  # min_x
            cy - half_h,  # min_y
            cx + half_w,  # max_x
            cy + half_h   # max_y
        )
    
    def get_svg_path(self) -> str:
        """Genera un path SVG del rectángulo"""
        cx, cy = self.center
        half_w = self.width / 2
        half_h = self.height / 2
        
        x = cx - half_w
        y = cy - half_h
        
        if self.corner_radius == 0:
            # Rectángulo simple
            if self.filled:
                return f'<rect x="{x}" y="{y}" width="{self.width}" height="{self.height}" fill="white" stroke="none"/>'
            else:
                return f'<rect x="{x}" y="{y}" width="{self.width}" height="{self.height}" fill="none" stroke="white" stroke-width="1"/>'
        else:
            # Rectángulo con esquinas redondeadas
            r = self.corner_radius
            fill_attr = 'fill="white" stroke="none"' if self.filled else 'fill="none" stroke="white" stroke-width="1"'
            return f'<rect x="{x}" y="{y}" width="{self.width}" height="{self.height}" rx="{r}" ry="{r}" {fill_attr}/>'
    
    def get_polygon_points(self) -> List[Tuple[float, float]]:
        """Retorna los puntos como polígono"""
        return self.points.copy()
    
    def contains_point(self, x: float, y: float) -> bool:
        """Verifica si un punto está dentro del rectángulo"""
        cx, cy = self.center
        half_w = self.width / 2
        half_h = self.height / 2
        
        # Verificación básica del rectángulo
        if not (cx - half_w <= x <= cx + half_w and cy - half_h <= y <= cy + half_h):
            return False
        
        # Si no hay esquinas redondeadas, ya está dentro
        if self.corner_radius == 0:
            return True
        
        # Verificar esquinas redondeadas
        r = self.corner_radius
        
        # Posiciones relativas al centro
        rel_x = abs(x - cx)
        rel_y = abs(y - cy)
        
        # Si está en la zona central (no en las esquinas), está dentro
        if rel_x <= half_w - r or rel_y <= half_h - r:
            return True
        
        # Verificar si está dentro del radio de la esquina
        corner_x = half_w - r
        corner_y = half_h - r
        
        if rel_x > corner_x and rel_y > corner_y:
            # Está en una de las esquinas, verificar distancia al centro del arco
            distance_sq = (rel_x - corner_x) ** 2 + (rel_y - corner_y) ** 2
            return distance_sq <= r ** 2
        
        return True
    
    def get_area(self) -> float:
        """Calcula el área del rectángulo"""
        if self.corner_radius == 0:
            return self.width * self.height
        else:
            # Área del rectángulo menos las esquinas + área de los cuartos de círculo
            r = self.corner_radius
            rect_area = self.width * self.height
            corner_area_removed = 4 * (r * r - math.pi * r * r / 4)
            return rect_area - corner_area_removed
    
    def get_perimeter(self) -> float:
        """Calcula el perímetro del rectángulo"""
        if self.corner_radius == 0:
            return 2 * (self.width + self.height)
        else:
            # Perímetro de los lados rectos + arcos de las esquinas
            r = self.corner_radius
            straight_length = 2 * (self.width - 2 * r) + 2 * (self.height - 2 * r)
            arc_length = 2 * math.pi * r  # 4 cuartos de círculo = círculo completo
            return straight_length + arc_length
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa la geometría a diccionario"""
        return {
            "type": "rectangle",
            "center": self.center,
            "width": self.width,
            "height": self.height,
            "corner_radius": self.corner_radius,
            "filled": self.filled,
            "points": self.points,
            "bbox": self.bbox
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RectangleGeometry':
        """Deserializa geometría desde diccionario"""
        return cls(
            center=data.get("center", (0, 0)),
            width=data.get("width", 200.0),
            height=data.get("height", 100.0),
            corner_radius=data.get("corner_radius", 0.0),
            filled=data.get("filled", True)
        )

class RectangleNode(GeneratorNode):
    """
    Nodo generador de rectángulos
    Crea geometría rectangular con esquinas redondeadas opcionales
    """
    
    NODE_TYPE = "rectangle"
    NODE_TITLE = "Rectangle"
    NODE_DESCRIPTION = "Generates a rectangular shape with optional rounded corners"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
        
        # Parámetros por defecto
        self.set_parameter("width", 200.0)
        self.set_parameter("height", 100.0)
        self.set_parameter("center_x", 0.0)
        self.set_parameter("center_y", 0.0)
        self.set_parameter("corner_radius", 0.0)
        self.set_parameter("filled", True)
        
    def _init_sockets(self):
        """Inicializa los sockets del nodo rectángulo"""
        # Inputs para parámetros del rectángulo
        self.add_input("width", NumberType(), default_value=200.0)
        self.add_input("height", NumberType(), default_value=100.0)
        self.add_input("center", VectorType(), default_value=(0.0, 0.0, 0.0))
        self.add_input("corner_radius", NumberType(), default_value=0.0)
        self.add_input("filled", BooleanType(), default_value=True)
        
        # Output de geometría
        self.add_output("geometry", GeometryType())
        
        # Outputs adicionales para información
        self.add_output("area", NumberType())
        self.add_output("perimeter", NumberType())
        self.add_output("bbox", VectorType())  # Como vector 4D
        self.add_output("aspect_ratio", NumberType())
    
    def generate_geometry(self) -> RectangleGeometry:
        """Genera la geometría del rectángulo"""
        # Obtener valores de inputs o parámetros internos
        width = self._get_width()
        height = self._get_height()
        center = self._get_center()
        corner_radius = self._get_corner_radius()
        filled = self._get_filled()
        
        # Crear geometría del rectángulo
        rectangle = RectangleGeometry(
            center=center,
            width=width,
            height=height,
            corner_radius=corner_radius,
            filled=filled
        )
        
        return rectangle
    
    def _get_width(self) -> float:
        """Obtiene el ancho desde input o parámetro"""
        input_width = self.get_input_value("width")
        if input_width is not None:
            try:
                width = float(input_width)
                return max(1.0, width)  # Mínimo 1px
            except (ValueError, TypeError):
                pass
        return self.get_parameter("width", 200.0)
    
    def _get_height(self) -> float:
        """Obtiene la altura desde input o parámetro"""
        input_height = self.get_input_value("height")
        if input_height is not None:
            try:
                height = float(input_height)
                return max(1.0, height)  # Mínimo 1px
            except (ValueError, TypeError):
                pass
        return self.get_parameter("height", 100.0)
    
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
    
    def _get_corner_radius(self) -> float:
        """Obtiene el radio de esquina desde input o parámetro"""
        input_radius = self.get_input_value("corner_radius")
        if input_radius is not None:
            try:
                radius = float(input_radius)
                return max(0.0, radius)  # No negativo
            except (ValueError, TypeError):
                pass
        return self.get_parameter("corner_radius", 0.0)
    
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
        rectangle = self.generate_geometry()
        
        # Calcular outputs adicionales
        area = rectangle.get_area()
        perimeter = rectangle.get_perimeter()
        bbox = rectangle.bbox  # (min_x, min_y, max_x, max_y)
        aspect_ratio = rectangle.width / rectangle.height if rectangle.height > 0 else 1.0
        
        return {
            "geometry": rectangle,
            "area": area,
            "perimeter": perimeter,
            "bbox": bbox,
            "aspect_ratio": aspect_ratio
        }
    
    def get_preview_info(self) -> Dict[str, Any]:
        """Información para preview en la UI"""
        try:
            rectangle = self.generate_geometry()
            return {
                "type": "rectangle",
                "center": rectangle.center,
                "width": rectangle.width,
                "height": rectangle.height,
                "corner_radius": rectangle.corner_radius,
                "area": rectangle.get_area(),
                "perimeter": rectangle.get_perimeter(),
                "aspect_ratio": rectangle.width / rectangle.height,
                "filled": rectangle.filled
            }
        except Exception:
            return {"type": "rectangle", "error": True}
    
    # Métodos de conveniencia
    def set_size(self, width: float, height: float):
        """Método de conveniencia para establecer el tamaño"""
        self.set_parameter("width", max(1.0, float(width)))
        self.set_parameter("height", max(1.0, float(height)))
    
    def set_center(self, x: float, y: float):
        """Método de conveniencia para establecer el centro"""
        self.set_parameter("center_x", float(x))
        self.set_parameter("center_y", float(y))
    
    def set_corner_radius(self, radius: float):
        """Método de conveniencia para establecer el radio de esquina"""
        self.set_parameter("corner_radius", max(0.0, float(radius)))
    
    def set_filled(self, filled: bool):
        """Método de conveniencia para establecer si está relleno"""
        self.set_parameter("filled", bool(filled))
    
    def make_square(self, size: float):
        """Convierte en cuadrado del tamaño especificado"""
        self.set_size(size, size)
    
    def set_aspect_ratio(self, ratio: float, maintain_width: bool = True):
        """Establece la relación de aspecto manteniendo el ancho o alto"""
        if maintain_width:
            width = self.get_parameter("width", 200.0)
            height = width / ratio if ratio > 0 else width
            self.set_size(width, height)
        else:
            height = self.get_parameter("height", 100.0)
            width = height * ratio if ratio > 0 else height
            self.set_size(width, height)

# Utilidades adicionales para trabajar con rectángulos

def create_rectangle_grid(rows: int, cols: int, spacing_x: float, spacing_y: float, 
                         width: float, height: float) -> List[RectangleGeometry]:
    """Crea una grilla de rectángulos"""
    rectangles = []
    
    start_x = -(cols - 1) * spacing_x / 2
    start_y = -(rows - 1) * spacing_y / 2
    
    for row in range(rows):
        for col in range(cols):
            x = start_x + col * spacing_x
            y = start_y + row * spacing_y
            rectangle = RectangleGeometry(center=(x, y), width=width, height=height)
            rectangles.append(rectangle)
    
    return rectangles

def create_concentric_rectangles(center: Tuple[float, float], 
                               min_size: Tuple[float, float],
                               max_size: Tuple[float, float], 
                               count: int) -> List[RectangleGeometry]:
    """Crea rectángulos concéntricos"""
    rectangles = []
    min_w, min_h = min_size
    max_w, max_h = max_size
    
    for i in range(count):
        t = i / (count - 1) if count > 1 else 0
        width = min_w + (max_w - min_w) * t
        height = min_h + (max_h - min_h) * t
        
        rectangle = RectangleGeometry(center=center, width=width, height=height, filled=False)
        rectangles.append(rectangle)
    
    return rectangles

def rectangle_intersects_rectangle(rect1: RectangleGeometry, rect2: RectangleGeometry) -> bool:
    """Verifica si dos rectángulos se intersectan"""
    bbox1 = rect1.bbox
    bbox2 = rect2.bbox
    
    # Verificar si los bounding boxes se intersectan
    return not (bbox1[2] < bbox2[0] or  # rect1.max_x < rect2.min_x
                bbox1[0] > bbox2[2] or  # rect1.min_x > rect2.max_x
                bbox1[3] < bbox2[1] or  # rect1.max_y < rect2.min_y
                bbox1[1] > bbox2[3])    # rect1.min_y > rect2.max_y

# Registro del nodo
RECTANGLE_NODE_REGISTRY = {
    "rectangle": RectangleNode
}