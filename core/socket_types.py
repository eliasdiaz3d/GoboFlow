"""
Tipos de datos para sockets en GoboFlow - Versión Simplificada
Define los tipos de datos que pueden fluir entre nodos
"""

from abc import ABC, abstractmethod
from typing import Any

class SocketType(ABC):
    """Clase base para tipos de socket"""
    
    def __init__(self, name: str):
        self.name = name
        
    def is_compatible_with(self, other: 'SocketType') -> bool:
        """Verifica si este tipo es compatible con otro"""
        # Por defecto, solo es compatible con el mismo tipo
        return type(self) == type(other)
        
    def validate_value(self, value: Any) -> bool:
        """Valida si un valor es del tipo correcto"""
        # Por defecto, acepta cualquier valor
        return True
        
    def __str__(self) -> str:
        return self.name

class GeometryType(SocketType):
    """Tipo para datos de geometría"""
    
    def __init__(self):
        super().__init__("Geometry")

class NumberType(SocketType):
    """Tipo para números (int/float)"""
    
    def __init__(self):
        super().__init__("Number")
        
    def validate_value(self, value: Any) -> bool:
        return isinstance(value, (int, float)) or value is None

class VectorType(SocketType):
    """Tipo para vectores (tuple/list de números)"""
    
    def __init__(self, dimensions: int = 3):
        super().__init__(f"Vector{dimensions}D")
        self.dimensions = dimensions
        
    def validate_value(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, (list, tuple)):
            return len(value) >= 2  # Al menos 2 dimensiones
        return False

class ColorType(SocketType):
    """Tipo para colores RGBA"""
    
    def __init__(self):
        super().__init__("Color")
        
    def validate_value(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, (list, tuple)):
            return len(value) in [3, 4]  # RGB o RGBA
        return False

class BooleanType(SocketType):
    """Tipo para valores booleanos"""
    
    def __init__(self):
        super().__init__("Boolean")
        
    def validate_value(self, value: Any) -> bool:
        return isinstance(value, bool) or value is None

class StringType(SocketType):
    """Tipo para cadenas de texto"""
    
    def __init__(self):
        super().__init__("String")
        
    def validate_value(self, value: Any) -> bool:
        return isinstance(value, str) or value is None

class ImageType(SocketType):
    """Tipo para imágenes"""
    
    def __init__(self):
        super().__init__("Image")