"""
Clases base para diferentes tipos de nodos en GoboFlow
Extiende la clase Node del core con funcionalidades específicas
"""

from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
import math

from core.node_system import Node
from core.socket_types import (
    GeometryType, NumberType, VectorType, ColorType, 
    BooleanType, StringType, ImageType
)

class BaseNode(Node):
    """
    Extensión de Node con funcionalidades comunes para GoboFlow
    """
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
        self._parameters = {}  # Parámetros internos del nodo
        
    def set_parameter(self, name: str, value: Any):
        """Establece un parámetro interno del nodo"""
        if self._parameters.get(name) != value:
            self._parameters[name] = value
            self.mark_dirty()
    
    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Obtiene un parámetro interno del nodo"""
        return self._parameters.get(name, default)
    
    def get_all_parameters(self) -> Dict[str, Any]:
        """Obtiene todos los parámetros del nodo"""
        return self._parameters.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el nodo incluyendo parámetros"""
        data = super().to_dict()
        data['parameters'] = self._parameters.copy()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseNode':
        """Deserializa un nodo incluyendo parámetros"""
        node = super().from_dict(data)
        node._parameters = data.get('parameters', {})
        return node

class GeneratorNode(BaseNode):
    """
    Clase base para nodos generadores (crean geometría desde cero)
    """
    
    NODE_CATEGORY = "generators"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
        
    def _init_sockets(self):
        """Los generadores típicamente solo tienen outputs de geometría"""
        self.add_output("geometry", GeometryType())
        
    def generate_geometry(self) -> Any:
        """
        Método abstracto para generar geometría.
        Debe ser implementado por subclases.
        """
        raise NotImplementedError("Subclasses must implement generate_geometry")
    
    def compute(self) -> Dict[str, Any]:
        """Implementación base del compute para generadores"""
        geometry = self.generate_geometry()
        return {"geometry": geometry}

class ModifierNode(BaseNode):
    """
    Clase base para nodos modificadores (transforman geometría existente)
    """
    
    NODE_CATEGORY = "modifiers"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
        
    def _init_sockets(self):
        """Los modificadores típicamente tienen input y output de geometría"""
        self.add_input("geometry", GeometryType())
        self.add_output("geometry", GeometryType())
        
    def modify_geometry(self, geometry: Any) -> Any:
        """
        Método abstracto para modificar geometría.
        Debe ser implementado por subclases.
        """
        raise NotImplementedError("Subclasses must implement modify_geometry")
    
    def compute(self) -> Dict[str, Any]:
        """Implementación base del compute para modificadores"""
        input_geometry = self.get_input_value("geometry")
        if input_geometry is None:
            return {"geometry": None}
            
        modified_geometry = self.modify_geometry(input_geometry)
        return {"geometry": modified_geometry}

class OperationNode(BaseNode):
    """
    Clase base para nodos de operaciones (combinan múltiples geometrías)
    """
    
    NODE_CATEGORY = "operations"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
        
    def _init_sockets(self):
        """Las operaciones típicamente tienen múltiples inputs y un output"""
        self.add_input("geometry_a", GeometryType())
        self.add_input("geometry_b", GeometryType())
        self.add_output("geometry", GeometryType())
        
    def perform_operation(self, geometry_a: Any, geometry_b: Any) -> Any:
        """
        Método abstracto para realizar operación entre geometrías.
        Debe ser implementado por subclases.
        """
        raise NotImplementedError("Subclasses must implement perform_operation")
    
    def compute(self) -> Dict[str, Any]:
        """Implementación base del compute para operaciones"""
        geometry_a = self.get_input_value("geometry_a")
        geometry_b = self.get_input_value("geometry_b")
        
        if geometry_a is None or geometry_b is None:
            return {"geometry": None}
            
        result_geometry = self.perform_operation(geometry_a, geometry_b)
        return {"geometry": result_geometry}

class InputNode(BaseNode):
    """
    Clase base para nodos de entrada (importan datos externos)
    """
    
    NODE_CATEGORY = "inputs"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
        
    def _init_sockets(self):
        """Los nodos de entrada solo tienen outputs"""
        # Se definirán en subclases según el tipo de entrada
        pass
        
    def load_data(self) -> Any:
        """
        Método abstracto para cargar datos externos.
        Debe ser implementado por subclases.
        """
        raise NotImplementedError("Subclasses must implement load_data")

class OutputNode(BaseNode):
    """
    Clase base para nodos de salida (exportan o muestran datos)
    """
    
    NODE_CATEGORY = "outputs"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
        
    def _init_sockets(self):
        """Los nodos de salida típicamente solo tienen inputs"""
        self.add_input("geometry", GeometryType())
        
    def export_data(self, data: Any) -> None:
        """
        Método abstracto para exportar o mostrar datos.
        Debe ser implementado por subclases.
        """
        raise NotImplementedError("Subclasses must implement export_data")
    
    def compute(self) -> Dict[str, Any]:
        """Los nodos de salida procesan pero no retornan datos"""
        input_data = self.get_input_value("geometry")
        if input_data is not None:
            self.export_data(input_data)
        return {}

class MaterialNode(BaseNode):
    """
    Clase base para nodos de material y color
    """
    
    NODE_CATEGORY = "materials"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
        
    def _init_sockets(self):
        """Los nodos de material típicamente outputean color"""
        self.add_output("color", ColorType())
        
    def compute_color(self, u: float = 0.0, v: float = 0.0) -> Tuple[float, float, float, float]:
        """
        Método abstracto para computar color en coordenadas UV.
        Retorna RGBA (0-1 range).
        """
        raise NotImplementedError("Subclases must implement compute_color")
    
    def compute(self) -> Dict[str, Any]:
        """Implementación base para nodos de material"""
        # Para nodos de material simple, computar en UV (0,0)
        color = self.compute_color(0.0, 0.0)
        return {"color": color}

class ParameterNode(BaseNode):
    """
    Clase base para nodos de parámetros (exponen valores ajustables)
    """
    
    NODE_CATEGORY = "parameters"
    
    def __init__(self, title: Optional[str] = None, value_type: Any = None):
        self.value_type = value_type or NumberType()  # Asignar antes del super().__init__
        super().__init__(title)
        
    def _init_sockets(self):
        """Los nodos de parámetro solo tienen output del tipo especificado"""
        self.add_output("value", self.value_type)
        
    def get_parameter_value(self) -> Any:
        """Obtiene el valor del parámetro"""
        raise NotImplementedError("Subclases must implement get_parameter_value")
    
    def compute(self) -> Dict[str, Any]:
        """Retorna el valor del parámetro"""
        value = self.get_parameter_value()
        return {"value": value}

class MathNode(BaseNode):
    """
    Clase base para nodos matemáticos
    """
    
    NODE_CATEGORY = "math"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
        
    def _init_sockets(self):
        """Nodos matemáticos típicamente tienen inputs numéricos y output numérico"""
        self.add_input("a", NumberType(), default_value=0.0)
        self.add_input("b", NumberType(), default_value=0.0)
        self.add_output("result", NumberType())
        
    def perform_math_operation(self, a: float, b: float) -> float:
        """
        Método abstracto para realizar operación matemática.
        """
        raise NotImplementedError("Subclases must implement perform_math_operation")
    
    def compute(self) -> Dict[str, Any]:
        """Implementación base para nodos matemáticos"""
        a = self.get_input_value("a")
        b = self.get_input_value("b")
        
        # Convertir a float si es necesario
        try:
            a = float(a) if a is not None else 0.0
            b = float(b) if b is not None else 0.0
        except (ValueError, TypeError):
            a, b = 0.0, 0.0
            
        result = self.perform_math_operation(a, b)
        return {"result": result}

class UtilityNode(BaseNode):
    """
    Clase base para nodos de utilidad
    """
    
    NODE_CATEGORY = "utility"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)

# Clases específicas comunes que pueden ser útiles

class NumberParameterNode(ParameterNode):
    """Nodo de parámetro numérico"""
    
    NODE_TYPE = "number_parameter"
    NODE_TITLE = "Number"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title, NumberType())
        self.set_parameter("value", 0.0)
        self.set_parameter("min_value", -1000.0)
        self.set_parameter("max_value", 1000.0)
        self.set_parameter("step", 0.1)
        
    def get_parameter_value(self) -> float:
        return self.get_parameter("value", 0.0)

class VectorParameterNode(ParameterNode):
    """Nodo de parámetro vectorial"""
    
    NODE_TYPE = "vector_parameter"
    NODE_TITLE = "Vector"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title, VectorType())
        self.set_parameter("x", 0.0)
        self.set_parameter("y", 0.0)
        self.set_parameter("z", 0.0)
        
    def get_parameter_value(self) -> Tuple[float, float, float]:
        x = self.get_parameter("x", 0.0)
        y = self.get_parameter("y", 0.0)
        z = self.get_parameter("z", 0.0)
        return (x, y, z)

class ColorParameterNode(ParameterNode):
    """Nodo de parámetro de color"""
    
    NODE_TYPE = "color_parameter"
    NODE_TITLE = "Color"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title, ColorType())
        self.set_parameter("r", 1.0)
        self.set_parameter("g", 1.0)
        self.set_parameter("b", 1.0)
        self.set_parameter("a", 1.0)
        
    def get_parameter_value(self) -> Tuple[float, float, float, float]:
        r = self.get_parameter("r", 1.0)
        g = self.get_parameter("g", 1.0)
        b = self.get_parameter("b", 1.0)
        a = self.get_parameter("a", 1.0)
        return (r, g, b, a)

class AddNode(MathNode):
    """Nodo de suma"""
    
    NODE_TYPE = "add"
    NODE_TITLE = "Add"
    
    def perform_math_operation(self, a: float, b: float) -> float:
        return a + b

class SubtractNode(MathNode):
    """Nodo de resta"""
    
    NODE_TYPE = "subtract"
    NODE_TITLE = "Subtract"
    
    def perform_math_operation(self, a: float, b: float) -> float:
        return a - b

class MultiplyNode(MathNode):
    """Nodo de multiplicación"""
    
    NODE_TYPE = "multiply"
    NODE_TITLE = "Multiply"
    
    def perform_math_operation(self, a: float, b: float) -> float:
        return a * b

class DivideNode(MathNode):
    """Nodo de división"""
    
    NODE_TYPE = "divide"
    NODE_TITLE = "Divide"
    
    def perform_math_operation(self, a: float, b: float) -> float:
        return a / b if b != 0 else 0.0

class ViewerNode(OutputNode):
    """Nodo visor básico"""
    
    NODE_TYPE = "viewer"
    NODE_TITLE = "Viewer"
    
    def __init__(self, title: Optional[str] = None):
        super().__init__(title)
        self._last_data = None
        
    def export_data(self, data: Any) -> None:
        """Almacena los datos para visualización"""
        self._last_data = data
        # TODO: Notificar a la UI para actualizar la vista
        
    def get_last_data(self) -> Any:
        """Obtiene los últimos datos visualizados"""
        return self._last_data

# Diccionario de registro de nodos base
BASE_NODE_REGISTRY = {
    "number_parameter": NumberParameterNode,
    "vector_parameter": VectorParameterNode, 
    "color_parameter": ColorParameterNode,
    "add": AddNode,
    "subtract": SubtractNode,
    "multiply": MultiplyNode,
    "divide": DivideNode,
    "viewer": ViewerNode,
}