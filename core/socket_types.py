"""
Tipos de datos para sockets en GoboFlow
Define los diferentes tipos de datos que pueden fluir entre nodos
"""

from abc import ABC, abstractmethod
from typing import Any, List, Union, Optional
from enum import Enum
import math

class SocketType(ABC):
    """
    Clase base abstracta para tipos de socket
    """
    
    def __init__(self, name: str, color: str = "#888888"):
        self.name = name
        self.color = color  # Color para representación visual
    
    @abstractmethod
    def is_compatible_with(self, other: 'SocketType') -> bool:
        """Verifica si este tipo es compatible con otro"""
        pass
    
    @abstractmethod
    def validate_value(self, value: Any) -> bool:
        """Valida si un valor es válido para este tipo"""
        pass
    
    @abstractmethod
    def convert_value(self, value: Any) -> Any:
        """Convierte un valor al tipo apropiado"""
        pass
    
    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}('{self.name}')>"

class NumberType(SocketType):
    """
    Tipo para valores numéricos (int, float)
    """
    
    def __init__(self, min_value: Optional[float] = None, max_value: Optional[float] = None):
        super().__init__("Number", "#4CAF50")  # Verde
        self.min_value = min_value
        self.max_value = max_value
    
    def is_compatible_with(self, other: 'SocketType') -> bool:
        # Los números son compatibles con otros números y vectores
        return isinstance(other, (NumberType, VectorType))
    
    def validate_value(self, value: Any) -> bool:
        try:
            num_value = float(value)
            
            if self.min_value is not None and num_value < self.min_value:
                return False
            if self.max_value is not None and num_value > self.max_value:
                return False
                
            return True
        except (ValueError, TypeError):
            return False
    
    def convert_value(self, value: Any) -> float:
        if value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

class VectorType(SocketType):
    """
    Tipo para vectores 2D/3D
    """
    
    def __init__(self, dimensions: int = 2):
        super().__init__(f"Vector{dimensions}D", "#2196F3")  # Azul
        self.dimensions = dimensions
    
    def is_compatible_with(self, other: 'SocketType') -> bool:
        # Los vectores son compatibles con otros vectores y números
        if isinstance(other, NumberType):
            return True
        if isinstance(other, VectorType):
            return True  # Permitir conversión entre diferentes dimensiones
        return False
    
    def validate_value(self, value: Any) -> bool:
        try:
            if isinstance(value, (list, tuple)):
                return len(value) >= 2 and all(isinstance(x, (int, float)) for x in value)
            elif isinstance(value, (int, float)):
                return True  # Número escalará a vector
            return False
        except (ValueError, TypeError):
            return False
    
    def convert_value(self, value: Any) -> List[float]:
        if value is None:
            return [0.0] * self.dimensions
        
        if isinstance(value, (int, float)):
            # Escalar número a vector
            return [float(value)] * self.dimensions
        
        if isinstance(value, (list, tuple)):
            # Convertir lista/tupla a vector
            vec = [float(x) for x in value[:self.dimensions]]
            # Rellenar con ceros si es necesario
            while len(vec) < self.dimensions:
                vec.append(0.0)
            return vec
        
        return [0.0] * self.dimensions

class GeometryType(SocketType):
    """
    Tipo para datos de geometría
    """
    
    def __init__(self):
        super().__init__("Geometry", "#FF9800")  # Naranja
    
    def is_compatible_with(self, other: 'SocketType') -> bool:
        # La geometría solo es compatible con otras geometrías
        return isinstance(other, GeometryType)
    
    def validate_value(self, value: Any) -> bool:
        # Verificar si es una instancia de alguna clase de geometría
        return hasattr(value, 'vertices') or hasattr(value, 'get_svg_path') or value is None
    
    def convert_value(self, value: Any) -> Any:
        # La geometría se pasa tal como está
        return value

class ColorType(SocketType):
    """
    Tipo para colores (RGB, RGBA, HSV)
    """
    
    def __init__(self):
        super().__init__("Color", "#E91E63")  # Rosa
    
    def is_compatible_with(self, other: 'SocketType') -> bool:
        # Los colores son compatibles con vectores y otros colores
        return isinstance(other, (ColorType, VectorType))
    
    def validate_value(self, value: Any) -> bool:
        try:
            if isinstance(value, str):
                # Verificar formato hex
                return value.startswith('#') and len(value) in [4, 7, 9]
            elif isinstance(value, (list, tuple)):
                # Verificar RGB/RGBA
                return len(value) in [3, 4] and all(0 <= x <= 1 for x in value)
            elif isinstance(value, dict):
                # Verificar formato de diccionario
                return 'r' in value and 'g' in value and 'b' in value
            return False
        except (ValueError, TypeError):
            return False
    
    def convert_value(self, value: Any) -> dict:
        if value is None:
            return {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0}
        
        if isinstance(value, str):
            # Convertir hex a RGB
            if value.startswith('#'):
                hex_color = value[1:]
                if len(hex_color) == 3:
                    # Formato #RGB
                    r = int(hex_color[0] * 2, 16) / 255.0
                    g = int(hex_color[1] * 2, 16) / 255.0
                    b = int(hex_color[2] * 2, 16) / 255.0
                    return {'r': r, 'g': g, 'b': b, 'a': 1.0}
                elif len(hex_color) == 6:
                    # Formato #RRGGBB
                    r = int(hex_color[0:2], 16) / 255.0
                    g = int(hex_color[2:4], 16) / 255.0
                    b = int(hex_color[4:6], 16) / 255.0
                    return {'r': r, 'g': g, 'b': b, 'a': 1.0}
        
        elif isinstance(value, (list, tuple)):
            if len(value) >= 3:
                color = {'r': float(value[0]), 'g': float(value[1]), 'b': float(value[2])}
                color['a'] = float(value[3]) if len(value) > 3 else 1.0
                return color
        
        elif isinstance(value, dict):
            # Ya está en formato de diccionario
            return {
                'r': float(value.get('r', 1.0)),
                'g': float(value.get('g', 1.0)),
                'b': float(value.get('b', 1.0)),
                'a': float(value.get('a', 1.0))
            }
        
        # Valor por defecto (blanco)
        return {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0}

class StringType(SocketType):
    """
    Tipo para cadenas de texto
    """
    
    def __init__(self):
        super().__init__("String", "#9C27B0")  # Púrpura
    
    def is_compatible_with(self, other: 'SocketType') -> bool:
        # Los strings son compatibles con otros strings
        return isinstance(other, StringType)
    
    def validate_value(self, value: Any) -> bool:
        return isinstance(value, str) or value is None
    
    def convert_value(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value)

class BooleanType(SocketType):
    """
    Tipo para valores booleanos
    """
    
    def __init__(self):
        super().__init__("Boolean", "#607D8B")  # Gris azulado
    
    def is_compatible_with(self, other: 'SocketType') -> bool:
        # Los booleanos son compatibles con números y otros booleanos
        return isinstance(other, (BooleanType, NumberType))
    
    def validate_value(self, value: Any) -> bool:
        return isinstance(value, bool) or value is None
    
    def convert_value(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'on']
        return bool(value)

class ArrayType(SocketType):
    """
    Tipo para arrays/listas de elementos
    """
    
    def __init__(self, element_type: SocketType):
        super().__init__(f"Array[{element_type.name}]", "#795548")  # Marrón
        self.element_type = element_type
    
    def is_compatible_with(self, other: 'SocketType') -> bool:
        if isinstance(other, ArrayType):
            return self.element_type.is_compatible_with(other.element_type)
        # Un array puede ser compatible con su tipo de elemento (para arrays de un elemento)
        return self.element_type.is_compatible_with(other)
    
    def validate_value(self, value: Any) -> bool:
        if value is None:
            return True
        if not isinstance(value, (list, tuple)):
            # Verificar si es compatible con el tipo de elemento (array de un elemento)
            return self.element_type.validate_value(value)
        # Validar todos los elementos
        return all(self.element_type.validate_value(item) for item in value)
    
    def convert_value(self, value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, (list, tuple)):
            return [self.element_type.convert_value(item) for item in value]
        # Convertir elemento único a array de un elemento
        return [self.element_type.convert_value(value)]

class AnyType(SocketType):
    """
    Tipo que acepta cualquier valor (wildcard)
    """
    
    def __init__(self):
        super().__init__("Any", "#424242")  # Gris oscuro
    
    def is_compatible_with(self, other: 'SocketType') -> bool:
        # Any es compatible con cualquier tipo
        return True
    
    def validate_value(self, value: Any) -> bool:
        # Any acepta cualquier valor
        return True
    
    def convert_value(self, value: Any) -> Any:
        # Any pasa el valor sin conversión
        return value

# ===========================================
# INSTANCIAS GLOBALES DE TIPOS COMUNES
# ===========================================

# Tipos básicos
NUMBER = NumberType()
VECTOR2D = VectorType(2)
VECTOR3D = VectorType(3)
GEOMETRY = GeometryType()
COLOR = ColorType()
STRING = StringType()
BOOLEAN = BooleanType()
ANY = AnyType()

# Tipos con restricciones comunes
POSITIVE_NUMBER = NumberType(min_value=0.0)
NORMALIZED_NUMBER = NumberType(min_value=0.0, max_value=1.0)
ANGLE_DEGREES = NumberType(min_value=0.0, max_value=360.0)
ANGLE_RADIANS = NumberType(min_value=0.0, max_value=2 * math.pi)

# Arrays comunes
NUMBER_ARRAY = ArrayType(NUMBER)
VECTOR_ARRAY = ArrayType(VECTOR2D)
GEOMETRY_ARRAY = ArrayType(GEOMETRY)
COLOR_ARRAY = ArrayType(COLOR)

# ===========================================
# UTILIDADES DE TIPOS
# ===========================================

def get_type_by_name(name: str) -> Optional[SocketType]:
    """Obtiene un tipo de socket por su nombre"""
    type_map = {
        'Number': NUMBER,
        'Vector2D': VECTOR2D,
        'Vector3D': VECTOR3D,
        'Geometry': GEOMETRY,
        'Color': COLOR,
        'String': STRING,
        'Boolean': BOOLEAN,
        'Any': ANY,
        'PositiveNumber': POSITIVE_NUMBER,
        'NormalizedNumber': NORMALIZED_NUMBER,
        'AngleDegrees': ANGLE_DEGREES,
        'AngleRadians': ANGLE_RADIANS
    }
    return type_map.get(name)

def create_compatible_types(type1: SocketType, type2: SocketType) -> bool:
    """Verifica si dos tipos son compatibles en cualquier dirección"""
    return type1.is_compatible_with(type2) or type2.is_compatible_with(type1)

def auto_convert_value(value: Any, target_type: SocketType) -> Any:
    """Convierte automáticamente un valor al tipo objetivo"""
    try:
        return target_type.convert_value(value)
    except Exception:
        # Si la conversión falla, usar valor por defecto
        if isinstance(target_type, NumberType):
            return 0.0
        elif isinstance(target_type, VectorType):
            return [0.0] * target_type.dimensions
        elif isinstance(target_type, ColorType):
            return {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0}
        elif isinstance(target_type, StringType):
            return ""
        elif isinstance(target_type, BooleanType):
            return False
        elif isinstance(target_type, ArrayType):
            return []
        else:
            return None

def get_socket_color(socket_type: SocketType) -> str:
    """Obtiene el color para representar visualmente un tipo de socket"""
    return socket_type.color

# ===========================================
# VALIDACIONES Y PRUEBAS
# ===========================================

def test_socket_types():
    """Pruebas básicas de los tipos de socket"""
    print("🧪 Probando tipos de socket...")
    
    # Probar conversiones de números
    assert NUMBER.convert_value("3.14") == 3.14
    assert NUMBER.convert_value(None) == 0.0
    print("✅ NumberType conversiones OK")
    
    # Probar conversiones de vectores
    assert VECTOR2D.convert_value([1, 2]) == [1.0, 2.0]
    assert VECTOR2D.convert_value(5) == [5.0, 5.0]
    print("✅ VectorType conversiones OK")
    
    # Probar conversiones de color
    color = COLOR.convert_value("#FF0000")
    assert abs(color['r'] - 1.0) < 0.01
    assert abs(color['g'] - 0.0) < 0.01
    print("✅ ColorType conversiones OK")
    
    # Probar compatibilidades
    assert NUMBER.is_compatible_with(VECTOR2D)
    assert GEOMETRY.is_compatible_with(GEOMETRY)
    assert not GEOMETRY.is_compatible_with(NUMBER)
    print("✅ Compatibilidades OK")
    
    print("🎉 Todos los tests de tipos de socket pasaron!")

if __name__ == "__main__":
    test_socket_types()