"""
Nodos base para GoboFlow
Implementaciones básicas de nodos comunes
"""

from typing import Dict, Any, Optional, List
import uuid
from abc import abstractmethod

from core.node_system import Node
from core.socket_types import (
    NUMBER, GEOMETRY, COLOR, STRING, BOOLEAN, VECTOR2D,
    auto_convert_value
)

class ParameterNode(Node):
    """
    Clase base para nodos de parámetros de entrada
    """
    
    NODE_CATEGORY = "parameters"
    
    def __init__(self, title: Optional[str] = None, parameter_type=NUMBER, default_value=None):
        # Establecer el tipo antes de llamar a super().__init__
        self.parameter_type = parameter_type
        self.parameter_value = default_value or self._get_default_value()
        
        # Ahora llamar a super().__init__ que llamará a _init_sockets()
        super().__init__(title)
        
    def _get_default_value(self):
        """Obtiene el valor por defecto según el tipo"""
        return auto_convert_value(None, self.parameter_type)
    
    def _init_sockets(self):
        """Inicializa los sockets del nodo parámetro"""
        # Solo output
        self.add_output("value", self.parameter_type)
    
    def compute(self) -> Dict[str, Any]:
        """Retorna el valor del parámetro"""
        return {"value": self.parameter_value}
    
    def set_parameter(self, name: str, value: Any):
        """Establece el valor del parámetro"""
        if name == "value":
            self.parameter_value = auto_convert_value(value, self.parameter_type)
            self.mark_dirty()
    
    def get_parameter_value(self):
        """Obtiene el valor actual del parámetro"""
        return self.parameter_value

class NumberParameterNode(ParameterNode):
    """
    Nodo de parámetro numérico
    """
    
    NODE_TYPE = "number_parameter"
    NODE_TITLE = "Number"
    NODE_DESCRIPTION = "Parámetro numérico de entrada"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title, NUMBER, 0.0)

class VectorParameterNode(ParameterNode):
    """
    Nodo de parámetro de vector 2D
    """
    
    NODE_TYPE = "vector_parameter"
    NODE_TITLE = "Vector"
    NODE_DESCRIPTION = "Parámetro de vector 2D"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title, VECTOR2D, [0.0, 0.0])

class ColorParameterNode(ParameterNode):
    """
    Nodo de parámetro de color
    """
    
    NODE_TYPE = "color_parameter"
    NODE_TITLE = "Color"
    NODE_DESCRIPTION = "Parámetro de color"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title, COLOR, {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0})

class ViewerNode(Node):
    """
    Nodo visor para mostrar resultados
    """
    
    NODE_TYPE = "viewer"
    NODE_TITLE = "Viewer"
    NODE_CATEGORY = "outputs"
    NODE_DESCRIPTION = "Visualiza datos de entrada"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
        self._last_data = None
        self._data_type = None
    
    def _init_sockets(self):
        """Inicializa los sockets del visor"""
        # Acepta geometría como entrada principal
        self.add_input("geometry", GEOMETRY, None)
        # Opcionalmente acepta otros tipos
        self.add_input("color", COLOR, None)
        self.add_input("opacity", NUMBER, 1.0)
    
    def compute(self) -> Dict[str, Any]:
        """Procesa los datos de entrada para visualización"""
        geometry = self.get_input_value("geometry")
        color = self.get_input_value("color")
        opacity = self.get_input_value("opacity")
        
        # Almacenar datos para visualización
        self._last_data = geometry
        self._data_type = type(geometry).__name__ if geometry else "None"
        
        # El visor no produce output, solo visualiza
        return {
            "display_geometry": geometry,
            "display_color": color,
            "display_opacity": opacity
        }
    
    def get_last_data(self):
        """Obtiene los últimos datos procesados"""
        return self._last_data
    
    def get_data_info(self) -> Dict[str, Any]:
        """Obtiene información sobre los datos visualizados"""
        return {
            "data_type": self._data_type,
            "has_data": self._last_data is not None,
            "data": self._last_data
        }

class TransformNode(Node):
    """
    Nodo base para transformaciones geométricas
    """
    
    NODE_CATEGORY = "modifiers"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
    
    def _init_sockets(self):
        """Inicializa sockets de transformación"""
        self.add_input("geometry", GEOMETRY, None)
        self.add_input("translation", VECTOR2D, [0.0, 0.0])
        self.add_input("rotation", NUMBER, 0.0)
        self.add_input("scale", VECTOR2D, [1.0, 1.0])
        
        self.add_output("geometry", GEOMETRY)
    
    def compute(self) -> Dict[str, Any]:
        """Aplica transformaciones a la geometría"""
        geometry = self.get_input_value("geometry")
        
        if geometry is None:
            return {"geometry": None}
        
        translation = self.get_input_value("translation")
        rotation = self.get_input_value("rotation")
        scale = self.get_input_value("scale")
        
        # Aplicar transformaciones
        transformed_geometry = self.apply_transform(geometry, translation, rotation, scale)
        
        return {"geometry": transformed_geometry}
    
    @abstractmethod
    def apply_transform(self, geometry, translation, rotation, scale):
        """Aplica las transformaciones a la geometría. Debe ser implementado por subclases."""
        pass

class MergeNode(Node):
    """
    Nodo para combinar múltiples geometrías
    """
    
    NODE_TYPE = "merge"
    NODE_TITLE = "Merge"
    NODE_CATEGORY = "operations"
    NODE_DESCRIPTION = "Combina múltiples geometrías"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
    
    def _init_sockets(self):
        """Inicializa sockets para merge"""
        # Múltiples entradas de geometría
        self.add_input("geometry1", GEOMETRY, None)
        self.add_input("geometry2", GEOMETRY, None)
        self.add_input("geometry3", GEOMETRY, None, is_multi=False)
        
        self.add_output("geometry", GEOMETRY)
    
    def compute(self) -> Dict[str, Any]:
        """Combina las geometrías de entrada"""
        geometries = []
        
        # Recopilar todas las geometrías no nulas
        for i in range(1, 4):
            geom = self.get_input_value(f"geometry{i}")
            if geom is not None:
                geometries.append(geom)
        
        if not geometries:
            return {"geometry": None}
        
        # Combinar geometrías (implementación básica)
        merged_geometry = self.merge_geometries(geometries)
        
        return {"geometry": merged_geometry}
    
    def merge_geometries(self, geometries: List[Any]) -> Any:
        """
        Combina una lista de geometrías.
        Implementación básica - debe ser extendida según el tipo de geometría.
        """
        if len(geometries) == 1:
            return geometries[0]
        
        # Para ahora, retornar la primera geometría
        # TODO: Implementar merge real según el tipo de geometría
        return geometries[0]

class SplitNode(Node):
    """
    Nodo para separar componentes de una geometría
    """
    
    NODE_TYPE = "split"
    NODE_TITLE = "Split"
    NODE_CATEGORY = "operations"
    NODE_DESCRIPTION = "Separa componentes de una geometría"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
    
    def _init_sockets(self):
        """Inicializa sockets para split"""
        self.add_input("geometry", GEOMETRY, None)
        self.add_input("method", STRING, "components")  # components, paths, etc.
        
        # Múltiples outputs
        self.add_output("output1", GEOMETRY)
        self.add_output("output2", GEOMETRY)
        self.add_output("output3", GEOMETRY)
        self.add_output("count", NUMBER)
    
    def compute(self) -> Dict[str, Any]:
        """Separa la geometría de entrada"""
        geometry = self.get_input_value("geometry")
        method = self.get_input_value("method")
        
        if geometry is None:
            return {
                "output1": None,
                "output2": None,
                "output3": None,
                "count": 0
            }
        
        # Separar según el método
        components = self.split_geometry(geometry, method)
        
        # Asignar a outputs
        result = {}
        for i in range(1, 4):
            if i <= len(components):
                result[f"output{i}"] = components[i-1]
            else:
                result[f"output{i}"] = None
        
        result["count"] = len(components)
        
        return result
    
    def split_geometry(self, geometry: Any, method: str) -> List[Any]:
        """
        Separa una geometría según el método especificado.
        Implementación básica - debe ser extendida.
        """
        # Por ahora, retornar la geometría original como único componente
        return [geometry] if geometry else []

class InfoNode(Node):
    """
    Nodo para obtener información sobre geometrías
    """
    
    NODE_TYPE = "info"
    NODE_TITLE = "Info"
    NODE_CATEGORY = "utilities"
    NODE_DESCRIPTION = "Obtiene información sobre geometrías"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
    
    def _init_sockets(self):
        """Inicializa sockets para info"""
        self.add_input("geometry", GEOMETRY, None)
        
        # Outputs de información
        self.add_output("area", NUMBER)
        self.add_output("perimeter", NUMBER)
        self.add_output("center", VECTOR2D)
        self.add_output("bounds", VECTOR2D)  # width, height
        self.add_output("vertex_count", NUMBER)
    
    def compute(self) -> Dict[str, Any]:
        """Calcula información sobre la geometría"""
        geometry = self.get_input_value("geometry")
        
        if geometry is None:
            return {
                "area": 0.0,
                "perimeter": 0.0,
                "center": [0.0, 0.0],
                "bounds": [0.0, 0.0],
                "vertex_count": 0
            }
        
        # Calcular información
        info = self.calculate_geometry_info(geometry)
        
        return info
    
    def calculate_geometry_info(self, geometry: Any) -> Dict[str, Any]:
        """
        Calcula información detallada sobre una geometría.
        Implementación básica - debe ser extendida según el tipo de geometría.
        """
        info = {
            "area": 0.0,
            "perimeter": 0.0,
            "center": [0.0, 0.0],
            "bounds": [0.0, 0.0],
            "vertex_count": 0
        }
        
        # Si la geometría tiene métodos específicos, usarlos
        if hasattr(geometry, 'area'):
            info["area"] = float(geometry.area)
        
        if hasattr(geometry, 'perimeter'):
            info["perimeter"] = float(geometry.perimeter)
        
        if hasattr(geometry, 'center'):
            center = geometry.center
            if isinstance(center, (list, tuple)):
                info["center"] = [float(center[0]), float(center[1])]
        
        if hasattr(geometry, 'bbox'):
            bbox = geometry.bbox
            if bbox and len(bbox) >= 4:
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                info["bounds"] = [float(width), float(height)]
        
        if hasattr(geometry, 'vertices'):
            info["vertex_count"] = len(geometry.vertices)
        
        return info

class ConditionalNode(Node):
    """
    Nodo condicional que selecciona entre dos entradas
    """
    
    NODE_TYPE = "conditional"
    NODE_TITLE = "Switch"
    NODE_CATEGORY = "logic"
    NODE_DESCRIPTION = "Selecciona entre dos entradas basado en una condición"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
    
    def _init_sockets(self):
        """Inicializa sockets para condicional"""
        self.add_input("condition", BOOLEAN, False)
        self.add_input("true_input", GEOMETRY, None)
        self.add_input("false_input", GEOMETRY, None)
        
        self.add_output("output", GEOMETRY)
    
    def compute(self) -> Dict[str, Any]:
        """Selecciona la entrada según la condición"""
        condition = self.get_input_value("condition")
        
        if condition:
            selected = self.get_input_value("true_input")
        else:
            selected = self.get_input_value("false_input")
        
        return {"output": selected}

class RandomNode(Node):
    """
    Nodo generador de números aleatorios
    """
    
    NODE_TYPE = "random"
    NODE_TITLE = "Random"
    NODE_CATEGORY = "generators"
    NODE_DESCRIPTION = "Genera números aleatorios"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
        self._last_seed = None
    
    def _init_sockets(self):
        """Inicializa sockets para random"""
        self.add_input("seed", NUMBER, 42)
        self.add_input("min_value", NUMBER, 0.0)
        self.add_input("max_value", NUMBER, 1.0)
        
        self.add_output("value", NUMBER)
        self.add_output("vector", VECTOR2D)
    
    def compute(self) -> Dict[str, Any]:
        """Genera valores aleatorios"""
        import random
        
        seed = int(self.get_input_value("seed"))
        min_val = self.get_input_value("min_value")
        max_val = self.get_input_value("max_value")
        
        # Usar seed para resultados reproducibles
        if seed != self._last_seed:
            random.seed(seed)
            self._last_seed = seed
        
        # Generar valores
        random_value = random.uniform(min_val, max_val)
        random_vector = [
            random.uniform(min_val, max_val),
            random.uniform(min_val, max_val)
        ]
        
        return {
            "value": random_value,
            "vector": random_vector
        }

class MathNode(Node):
    """
    Nodo para operaciones matemáticas básicas
    """
    
    NODE_TYPE = "math"
    NODE_TITLE = "Math"
    NODE_CATEGORY = "math"
    NODE_DESCRIPTION = "Operaciones matemáticas básicas"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
        self.operation = "add"  # add, subtract, multiply, divide, power, etc.
    
    def _init_sockets(self):
        """Inicializa sockets para math"""
        self.add_input("a", NUMBER, 0.0)
        self.add_input("b", NUMBER, 0.0)
        self.add_input("operation", STRING, "add")
        
        self.add_output("result", NUMBER)
    
    def compute(self) -> Dict[str, Any]:
        """Realiza operación matemática"""
        import math
        
        a = self.get_input_value("a")
        b = self.get_input_value("b")
        operation = self.get_input_value("operation").lower()
        
        result = 0.0
        
        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                result = a / b if b != 0 else 0.0
            elif operation == "power":
                result = pow(a, b)
            elif operation == "modulo":
                result = a % b if b != 0 else 0.0
            elif operation == "min":
                result = min(a, b)
            elif operation == "max":
                result = max(a, b)
            elif operation == "sin":
                result = math.sin(a)
            elif operation == "cos":
                result = math.cos(a)
            elif operation == "tan":
                result = math.tan(a)
            elif operation == "sqrt":
                result = math.sqrt(abs(a))
            elif operation == "abs":
                result = abs(a)
            elif operation == "floor":
                result = math.floor(a)
            elif operation == "ceil":
                result = math.ceil(a)
            else:
                result = a  # Operación no reconocida, devolver primer valor
                
        except (ValueError, ZeroDivisionError, OverflowError):
            result = 0.0
        
        return {"result": result}
    
    def set_operation(self, operation: str):
        """Establece la operación matemática"""
        self.operation = operation
        self.mark_dirty()

# ===========================================
# UTILIDADES PARA NODOS BASE
# ===========================================

def create_parameter_node(param_type: str, value: Any = None, title: str = None):
    """Factory function para crear nodos de parámetros"""
    if param_type.lower() == "number":
        node = NumberParameterNode(title)
        if value is not None:
            node.set_parameter("value", value)
        return node
    elif param_type.lower() == "vector":
        node = VectorParameterNode(title)
        if value is not None:
            node.set_parameter("value", value)
        return node
    elif param_type.lower() == "color":
        node = ColorParameterNode(title)
        if value is not None:
            node.set_parameter("value", value)
        return node
    else:
        raise ValueError(f"Tipo de parámetro no soportado: {param_type}")

def get_base_node_types():
    """Retorna lista de todos los tipos de nodos base disponibles"""
    return [
        NumberParameterNode,
        VectorParameterNode,
        ColorParameterNode,
        ViewerNode,
        MergeNode,
        SplitNode,
        InfoNode,
        ConditionalNode,
        RandomNode,
        MathNode
    ]

def create_node_by_type(node_type: str, title: str = None):
    """Factory function para crear nodos por tipo"""
    node_map = {
        "number_parameter": NumberParameterNode,
        "vector_parameter": VectorParameterNode,
        "color_parameter": ColorParameterNode,
        "viewer": ViewerNode,
        "merge": MergeNode,
        "split": SplitNode,
        "info": InfoNode,
        "conditional": ConditionalNode,
        "random": RandomNode,
        "math": MathNode
    }
    
    if node_type in node_map:
        return node_map[node_type](title)
    else:
        raise ValueError(f"Tipo de nodo no encontrado: {node_type}")

# ===========================================
# PRUEBAS DE NODOS BASE
# ===========================================

def test_base_nodes():
    """Pruebas básicas de los nodos base"""
    print("🧪 Probando nodos base...")
    
    # Probar NumberParameterNode
    num_node = NumberParameterNode("Test Number")
    num_node.set_parameter("value", 42.5)
    result = num_node.compute()
    assert result["value"] == 42.5
    print("✅ NumberParameterNode OK")
    
    # Probar ViewerNode
    viewer = ViewerNode("Test Viewer")
    viewer_result = viewer.compute()
    assert "display_geometry" in viewer_result
    print("✅ ViewerNode OK")
    
    # Probar MathNode
    math_node = MathNode("Test Math")
    # Simular entrada
    math_node.add_input("a", NUMBER, 5.0)
    math_node.add_input("b", NUMBER, 3.0)
    math_result = math_node.compute()
    assert math_result["result"] == 8.0  # 5 + 3
    print("✅ MathNode OK")
    
    print("🎉 Todos los tests de nodos base pasaron!")

if __name__ == "__main__":
    test_base_nodes()