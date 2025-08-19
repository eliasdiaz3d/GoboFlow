"""
Nodo de círculo para GoboFlow
Genera geometrías circulares procedurales
"""

import math
from typing import Dict, Any, Optional

from core.node_system import Node
from core.socket_types import NUMBER, GEOMETRY, VECTOR2D, POSITIVE_NUMBER
from utils.geometry.base_geometry import Circle

class CircleNode(Node):
    """
    Nodo que genera geometrías de círculo
    """
    
    NODE_TYPE = "circle"
    NODE_TITLE = "Circle"
    NODE_CATEGORY = "primitives"
    NODE_DESCRIPTION = "Genera un círculo procedural"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
        
        # Parámetros internos
        self._last_geometry = None
        self._last_params = {}
    
    def _init_sockets(self):
        """Inicializa los sockets del nodo círculo"""
        # Inputs
        self.add_input("center", VECTOR2D, [0.0, 0.0])
        self.add_input("radius", POSITIVE_NUMBER, 100.0)
        self.add_input("segments", NUMBER, 32)
        
        # Outputs
        self.add_output("geometry", GEOMETRY)
        self.add_output("area", NUMBER)
        self.add_output("perimeter", NUMBER)
        self.add_output("center_out", VECTOR2D)
    
    def compute(self) -> Dict[str, Any]:
        """Genera la geometría del círculo"""
        # Obtener parámetros de entrada
        center = self.get_input_value("center")
        radius = self.get_input_value("radius")
        segments = int(self.get_input_value("segments"))
        
        # Validar parámetros
        radius = max(0.1, radius)  # Radio mínimo
        segments = max(3, min(256, segments))  # Límites de segmentos
        
        # Convertir center a tupla si es lista
        if isinstance(center, list):
            center = (center[0], center[1])
        
        # Verificar si necesitamos regenerar la geometría
        current_params = {
            'center': center,
            'radius': radius,
            'segments': segments
        }
        
        if (self._last_geometry is None or 
            current_params != self._last_params):
            
            # Generar nueva geometría
            self._last_geometry = Circle(center, radius, segments)
            self._last_params = current_params
        
        # Calcular propiedades
        area = self._last_geometry.area
        perimeter = self._last_geometry.perimeter
        
        return {
            "geometry": self._last_geometry,
            "area": area,
            "perimeter": perimeter,
            "center_out": list(center)
        }
    
    def generate_geometry(self) -> Optional[Circle]:
        """
        Método de conveniencia para generar la geometría directamente
        Usado por el sistema de preview y exportación
        """
        try:
            result = self.compute()
            return result.get("geometry")
        except Exception as e:
            print(f"Error generando geometría en {self.title}: {e}")
            return None
    
    def get_preview_info(self) -> Dict[str, Any]:
        """Obtiene información para preview del nodo"""
        try:
            result = self.compute()
            geometry = result.get("geometry")
            
            if geometry:
                return {
                    "type": "circle",
                    "center": geometry.circle_center,
                    "radius": geometry.radius,
                    "segments": geometry.segments,
                    "area": geometry.area,
                    "perimeter": geometry.perimeter,
                    "bbox": geometry.bbox
                }
            else:
                return {"type": "none"}
                
        except Exception as e:
            return {"type": "error", "error": str(e)}
    
    def set_radius(self, radius: float):
        """Establece el radio del círculo"""
        if "radius" in self.input_sockets:
            # Si hay conexión, no cambiar el valor por defecto
            if not self.input_sockets["radius"].connections:
                self.input_sockets["radius"].default_value = max(0.1, radius)
                self.mark_dirty()
    
    def set_center(self, center: tuple):
        """Establece el centro del círculo"""
        if "center" in self.input_sockets:
            if not self.input_sockets["center"].connections:
                self.input_sockets["center"].default_value = list(center)
                self.mark_dirty()
    
    def set_segments(self, segments: int):
        """Establece el número de segmentos"""
        if "segments" in self.input_sockets:
            if not self.input_sockets["segments"].connections:
                segments = max(3, min(256, segments))
                self.input_sockets["segments"].default_value = segments
                self.mark_dirty()
    
    def get_svg_export(self, style_override: Optional[Dict[str, str]] = None) -> str:
        """
        Exporta el círculo como elemento SVG
        
        Args:
            style_override: Diccionario con estilos CSS para override
        """
        geometry = self.generate_geometry()
        
        if not geometry:
            return ""
        
        # Estilo por defecto
        style = {
            "fill": "white",
            "opacity": "0.8",
            "stroke": "none"
        }
        
        # Aplicar overrides
        if style_override:
            style.update(style_override)
        
        # Construir string de estilo
        style_str = "; ".join([f"{k}: {v}" for k, v in style.items()])
        
        cx, cy = geometry.circle_center
        r = geometry.radius
        
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" style="{style_str}"/>'
    
    def animate_radius(self, start_radius: float, end_radius: float, 
                      frame: int, total_frames: int) -> float:
        """
        Calcula el radio para un frame de animación
        
        Args:
            start_radius: Radio inicial
            end_radius: Radio final
            frame: Frame actual (0-based)
            total_frames: Total de frames
        """
        if total_frames <= 1:
            return end_radius
        
        # Interpolación lineal
        t = frame / (total_frames - 1)
        return start_radius + (end_radius - start_radius) * t
    
    def create_concentric_circles(self, count: int, spacing: float) -> list:
        """
        Crea múltiples círculos concéntricos
        
        Args:
            count: Número de círculos
            spacing: Espaciado entre círculos
            
        Returns:
            Lista de geometrías Circle
        """
        center = self.get_input_value("center")
        base_radius = self.get_input_value("radius")
        segments = int(self.get_input_value("segments"))
        
        if isinstance(center, list):
            center = (center[0], center[1])
        
        circles = []
        
        for i in range(count):
            radius = base_radius + (i * spacing)
            if radius > 0:
                circle = Circle(center, radius, segments)
                circles.append(circle)
        
        return circles
    
    def create_circle_grid(self, rows: int, cols: int, 
                          spacing_x: float, spacing_y: float) -> list:
        """
        Crea una grilla de círculos
        
        Args:
            rows: Número de filas
            cols: Número de columnas
            spacing_x: Espaciado horizontal
            spacing_y: Espaciado vertical
            
        Returns:
            Lista de geometrías Circle
        """
        base_center = self.get_input_value("center")
        radius = self.get_input_value("radius")
        segments = int(self.get_input_value("segments"))
        
        if isinstance(base_center, list):
            base_center = (base_center[0], base_center[1])
        
        circles = []
        
        # Calcular offset para centrar la grilla
        total_width = (cols - 1) * spacing_x
        total_height = (rows - 1) * spacing_y
        start_x = base_center[0] - total_width / 2
        start_y = base_center[1] - total_height / 2
        
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * spacing_x
                y = start_y + row * spacing_y
                
                circle = Circle((x, y), radius, segments)
                circles.append(circle)
        
        return circles
    
    def create_spiral_circles(self, count: int, turns: float, 
                             radius_growth: float) -> list:
        """
        Crea círculos en espiral
        
        Args:
            count: Número de círculos
            turns: Número de vueltas de la espiral
            radius_growth: Crecimiento del radio de la espiral
            
        Returns:
            Lista de geometrías Circle
        """
        base_center = self.get_input_value("center")
        circle_radius = self.get_input_value("radius")
        segments = int(self.get_input_value("segments"))
        
        if isinstance(base_center, list):
            base_center = (base_center[0], base_center[1])
        
        circles = []
        
        for i in range(count):
            # Calcular ángulo y radio de la espiral
            t = i / count  # Parámetro normalizado (0-1)
            angle = 2 * math.pi * turns * t
            spiral_radius = radius_growth * t
            
            # Posición en la espiral
            x = base_center[0] + spiral_radius * math.cos(angle)
            y = base_center[1] + spiral_radius * math.sin(angle)
            
            # Crear círculo
            circle = Circle((x, y), circle_radius, segments)
            circles.append(circle)
        
        return circles
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el nodo a diccionario"""
        data = super().to_dict()
        
        # Añadir parámetros específicos del círculo
        data['circle_params'] = {
            'center': self.get_input_value("center"),
            'radius': self.get_input_value("radius"),
            'segments': self.get_input_value("segments")
        }
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CircleNode':
        """Deserializa un nodo desde diccionario"""
        node = super().from_dict(data)
        
        # Restaurar parámetros específicos
        if 'circle_params' in data:
            params = data['circle_params']
            node.set_center(tuple(params.get('center', [0, 0])))
            node.set_radius(params.get('radius', 100))
            node.set_segments(params.get('segments', 32))
        
        return node

# ===========================================
# VARIACIONES DE CÍRCULO
# ===========================================

class RingNode(CircleNode):
    """
    Nodo que genera anillos (círculos con hueco)
    """
    
    NODE_TYPE = "ring"
    NODE_TITLE = "Ring"
    NODE_DESCRIPTION = "Genera un anillo (círculo con hueco central)"
    
    def _init_sockets(self):
        """Inicializa sockets específicos del anillo"""
        super()._init_sockets()
        
        # Añadir input para radio interno
        self.add_input("inner_radius", POSITIVE_NUMBER, 50.0)
    
    def compute(self) -> Dict[str, Any]:
        """Genera la geometría del anillo"""
        # Obtener parámetros
        center = self.get_input_value("center")
        outer_radius = self.get_input_value("radius")
        inner_radius = self.get_input_value("inner_radius")
        segments = int(self.get_input_value("segments"))
        
        # Validar que el radio interno sea menor que el externo
        inner_radius = min(inner_radius, outer_radius * 0.95)
        
        if isinstance(center, list):
            center = (center[0], center[1])
        
        # Crear círculo externo e interno
        outer_circle = Circle(center, outer_radius, segments)
        inner_circle = Circle(center, inner_radius, segments)
        
        # Para un anillo, necesitaríamos una geometría más compleja
        # Por simplicidad, retornamos el círculo externo
        # TODO: Implementar geometría de anillo real
        
        area = math.pi * (outer_radius ** 2 - inner_radius ** 2)
        perimeter = 2 * math.pi * (outer_radius + inner_radius)
        
        return {
            "geometry": outer_circle,  # Temporal
            "area": area,
            "perimeter": perimeter,
            "center_out": list(center),
            "outer_radius": outer_radius,
            "inner_radius": inner_radius
        }

class EllipseNode(CircleNode):
    """
    Nodo que genera elipses
    """
    
    NODE_TYPE = "ellipse"
    NODE_TITLE = "Ellipse"
    NODE_DESCRIPTION = "Genera una elipse"
    
    def _init_sockets(self):
        """Inicializa sockets específicos de la elipse"""
        # Modificar sockets del círculo
        self.add_input("center", VECTOR2D, [0.0, 0.0])
        self.add_input("radius_x", POSITIVE_NUMBER, 100.0)
        self.add_input("radius_y", POSITIVE_NUMBER, 50.0)
        self.add_input("segments", NUMBER, 32)
        
        self.add_output("geometry", GEOMETRY)
        self.add_output("area", NUMBER)
        self.add_output("perimeter", NUMBER)
        self.add_output("center_out", VECTOR2D)
    
    def compute(self) -> Dict[str, Any]:
        """Genera la geometría de la elipse"""
        center = self.get_input_value("center")
        radius_x = self.get_input_value("radius_x")
        radius_y = self.get_input_value("radius_y")
        segments = int(self.get_input_value("segments"))
        
        if isinstance(center, list):
            center = (center[0], center[1])
        
        # Crear elipse usando polígono
        from utils.geometry.base_geometry import Polygon
        
        vertices = []
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = center[0] + radius_x * math.cos(angle)
            y = center[1] + radius_y * math.sin(angle)
            vertices.append((x, y))
        
        ellipse = Polygon(vertices)
        
        # Calcular área y perímetro aproximados
        area = math.pi * radius_x * radius_y
        # Aproximación de Ramanujan para el perímetro de elipse
        h = ((radius_x - radius_y) / (radius_x + radius_y)) ** 2
        perimeter = math.pi * (radius_x + radius_y) * (1 + (3 * h) / (10 + math.sqrt(4 - 3 * h)))
        
        return {
            "geometry": ellipse,
            "area": area,
            "perimeter": perimeter,
            "center_out": list(center)
        }

# ===========================================
# PRUEBAS DE NODOS DE CÍRCULO
# ===========================================

def test_circle_nodes():
    """Pruebas de los nodos de círculo"""
    print("🧪 Probando nodos de círculo...")
    
    # Probar CircleNode
    circle_node = CircleNode("Test Circle")
    circle_node.set_radius(50)
    circle_node.set_center((100, 100))
    
    result = circle_node.compute()
    assert result["geometry"] is not None
    assert abs(result["area"] - math.pi * 50 * 50) < 0.01
    print("✅ CircleNode OK")
    
    # Probar generación de geometría
    geometry = circle_node.generate_geometry()
    assert isinstance(geometry, Circle)
    assert geometry.radius == 50
    print("✅ Generación de geometría OK")
    
    # Probar círculos concéntricos
    concentric = circle_node.create_concentric_circles(3, 25)
    assert len(concentric) == 3
    print("✅ Círculos concéntricos OK")
    
    # Probar RingNode
    ring_node = RingNode("Test Ring")
    ring_result = ring_node.compute()
    assert ring_result["geometry"] is not None
    print("✅ RingNode OK")
    
    # Probar EllipseNode
    ellipse_node = EllipseNode("Test Ellipse")
    ellipse_result = ellipse_node.compute()
    assert ellipse_result["geometry"] is not None
    print("✅ EllipseNode OK")
    
    print("🎉 Todos los tests de nodos de círculo pasaron!")

if __name__ == "__main__":
    test_circle_nodes()