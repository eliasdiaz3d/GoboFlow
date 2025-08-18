"""
Sistema base de nodos para GoboFlow
Define las clases fundamentales: Node, Socket, Connection
"""

from typing import Dict, List, Any, Optional, Tuple, Set, Callable, TYPE_CHECKING
from enum import Enum
import uuid
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from .socket_types import SocketType

class SocketDirection(Enum):
    """Dirección de un socket"""
    INPUT = "input"
    OUTPUT = "output"

class NodeState(Enum):
    """Estados posibles de un nodo"""
    CLEAN = "clean"          # Nodo calculado y actualizado
    DIRTY = "dirty"          # Nodo necesita recálculo
    PROCESSING = "processing" # Nodo siendo procesado
    ERROR = "error"          # Error en el nodo

class Socket:
    """
    Representa un punto de conexión en un nodo (entrada o salida)
    """
    
    def __init__(self, 
                 node: 'Node',
                 socket_type: 'SocketType', 
                 direction: SocketDirection,
                 name: str,
                 default_value: Any = None,
                 is_multi: bool = False):
        self.id = str(uuid.uuid4())
        self.node = node
        self.socket_type = socket_type
        self.direction = direction
        self.name = name
        self.default_value = default_value
        self.is_multi = is_multi  # Permite múltiples conexiones
        
        # Conexiones
        self.connections: List['Connection'] = []
        
        # Cache del valor actual
        self._cached_value: Any = None
        self._is_cached: bool = False
        
    def can_connect_to(self, other: 'Socket') -> bool:
        """Verifica si este socket puede conectarse a otro"""
        # No conectar sockets del mismo nodo
        if self.node == other.node:
            return False
            
        # Direcciones opuestas
        if self.direction == other.direction:
            return False
            
        # Verificar compatibilidad de tipos
        if not self.socket_type.is_compatible_with(other.socket_type):
            return False
            
        # Verificar si ya está conectado (para sockets no-multi)
        if not self.is_multi and len(self.connections) > 0:
            return False
        if not other.is_multi and len(other.connections) > 0:
            return False
            
        return True
    
    def get_value(self) -> Any:
        """Obtiene el valor del socket"""
        if self.direction == SocketDirection.OUTPUT:
            # Los outputs obtienen su valor del nodo
            return self.node.get_output_value(self.name)
        else:
            # Los inputs obtienen valor de conexiones o valor por defecto
            if self.connections:
                if self.is_multi:
                    # Multi-input: lista de valores
                    return [conn.get_value() for conn in self.connections]
                else:
                    # Single input: primer valor
                    return self.connections[0].get_value()
            else:
                return self.default_value
    
    def clear_cache(self):
        """Limpia el cache del valor"""
        self._is_cached = False
        self._cached_value = None
        
    def add_connection(self, connection: 'Connection'):
        """Añade una conexión al socket"""
        if connection not in self.connections:
            self.connections.append(connection)
            self.clear_cache()
            
    def remove_connection(self, connection: 'Connection'):
        """Remueve una conexión del socket"""
        if connection in self.connections:
            self.connections.remove(connection)
            self.clear_cache()

class Connection:
    """
    Representa una conexión entre dos sockets
    """
    
    def __init__(self, output_socket: Socket, input_socket: Socket):
        self.id = str(uuid.uuid4())
        self.output_socket = output_socket
        self.input_socket = input_socket
        
        # Verificar que la conexión es válida
        if not output_socket.can_connect_to(input_socket):
            raise ValueError(f"Cannot connect {output_socket.name} to {input_socket.name}")
        
        # Añadir la conexión a ambos sockets
        output_socket.add_connection(self)
        input_socket.add_connection(self)
        
    def get_value(self) -> Any:
        """Obtiene el valor de la conexión (desde el output)"""
        return self.output_socket.get_value()
    
    def disconnect(self):
        """Desconecta esta conexión"""
        self.output_socket.remove_connection(self)
        self.input_socket.remove_connection(self)

class Node(ABC):
    """
    Clase base abstracta para todos los nodos en GoboFlow
    """
    
    # Información del tipo de nodo
    NODE_TYPE = "base"
    NODE_TITLE = "Base Node"
    NODE_CATEGORY = "base"
    NODE_DESCRIPTION = "Base node class"
    
    def __init__(self, title: Optional[str] = None):
        self.id = str(uuid.uuid4())
        self.title = title or self.NODE_TITLE
        self.state = NodeState.CLEAN
        
        # Posición en el editor (será manejada por la UI)
        self.pos_x = 0.0
        self.pos_y = 0.0
        
        # Sockets
        self.input_sockets: Dict[str, Socket] = {}
        self.output_sockets: Dict[str, Socket] = {}
        
        # Cache de resultados
        self._output_cache: Dict[str, Any] = {}
        self._cache_valid = False
        
        # Callbacks
        self.on_state_changed: Optional[Callable[['Node'], None]] = None
        self.on_value_changed: Optional[Callable[['Node'], None]] = None
        
        # Inicializar sockets del nodo
        self._init_sockets()
        
    @abstractmethod
    def _init_sockets(self):
        """Inicializa los sockets del nodo. Debe ser implementado por subclases."""
        pass
    
    @abstractmethod  
    def compute(self) -> Dict[str, Any]:
        """
        Lógica de computación del nodo.
        Debe retornar un diccionario con los valores de output.
        """
        pass
    
    def add_input(self, name: str, socket_type: 'SocketType', default_value: Any = None, is_multi: bool = False) -> Socket:
        """Añade un socket de entrada"""
        socket = Socket(self, socket_type, SocketDirection.INPUT, name, default_value, is_multi)
        self.input_sockets[name] = socket
        return socket
    
    def add_output(self, name: str, socket_type: 'SocketType') -> Socket:
        """Añade un socket de salida"""
        socket = Socket(self, socket_type, SocketDirection.OUTPUT, name)
        self.output_sockets[name] = socket
        return socket
    
    def get_input_value(self, name: str) -> Any:
        """Obtiene el valor de un input socket"""
        if name not in self.input_sockets:
            raise KeyError(f"Input socket '{name}' not found in node {self.title}")
        return self.input_sockets[name].get_value()
    
    def get_output_value(self, name: str) -> Any:
        """Obtiene el valor de un output socket"""
        if name not in self.output_sockets:
            raise KeyError(f"Output socket '{name}' not found in node {self.title}")
            
        # Si el cache es válido, retornar valor cacheado
        if self._cache_valid and name in self._output_cache:
            return self._output_cache[name]
        
        # Recalcular si es necesario
        if self.state == NodeState.DIRTY or not self._cache_valid:
            self._recalculate()
            
        return self._output_cache.get(name)
    
    def _recalculate(self):
        """Recalcula los valores del nodo"""
        try:
            self._set_state(NodeState.PROCESSING)
            
            # Ejecutar lógica de computación
            results = self.compute()
            
            # Actualizar cache
            self._output_cache = results
            self._cache_valid = True
            
            self._set_state(NodeState.CLEAN)
            
            # Notificar cambio de valor
            if self.on_value_changed:
                self.on_value_changed(self)
                
        except Exception as e:
            self._set_state(NodeState.ERROR)
            # TODO: Sistema de logging de errores
            raise e
    
    def mark_dirty(self, propagate: bool = True):
        """Marca el nodo como dirty (necesita recálculo)"""
        if self.state != NodeState.DIRTY:
            self._set_state(NodeState.DIRTY)
            self._cache_valid = False
            
            # Propagar a nodos dependientes
            if propagate:
                self._propagate_dirty()
    
    def _propagate_dirty(self):
        """Propaga el estado dirty a nodos conectados"""
        for output_socket in self.output_sockets.values():
            for connection in output_socket.connections:
                connected_node = connection.input_socket.node
                connected_node.mark_dirty(propagate=True)
    
    def _set_state(self, new_state: NodeState):
        """Cambia el estado del nodo"""
        if self.state != new_state:
            self.state = new_state
            if self.on_state_changed:
                self.on_state_changed(self)
    
    def get_dependencies(self) -> Set['Node']:
        """Obtiene todos los nodos de los que depende este nodo"""
        dependencies = set()
        
        for input_socket in self.input_sockets.values():
            for connection in input_socket.connections:
                dep_node = connection.output_socket.node
                dependencies.add(dep_node)
                # Recursivamente obtener dependencias de dependencias
                dependencies.update(dep_node.get_dependencies())
                
        return dependencies
    
    def get_dependents(self) -> Set['Node']:
        """Obtiene todos los nodos que dependen de este nodo"""
        dependents = set()
        
        for output_socket in self.output_sockets.values():
            for connection in output_socket.connections:
                dep_node = connection.input_socket.node
                dependents.add(dep_node)
                # Recursivamente obtener dependientes de dependientes
                dependents.update(dep_node.get_dependents())
                
        return dependents
    
    def can_connect_to(self, other: 'Node') -> bool:
        """Verifica si este nodo puede conectarse a otro sin crear ciclos"""
        # Verificar que no se cree un ciclo
        if other in self.get_dependencies():
            return False
        if self in other.get_dependencies():
            return False
        return True
    
    def disconnect_all(self):
        """Desconecta todas las conexiones del nodo"""
        # Desconectar inputs
        for socket in self.input_sockets.values():
            connections_copy = socket.connections.copy()
            for connection in connections_copy:
                connection.disconnect()
        
        # Desconectar outputs
        for socket in self.output_sockets.values():
            connections_copy = socket.connections.copy()
            for connection in connections_copy:
                connection.disconnect()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el nodo a diccionario"""
        return {
            'id': self.id,
            'type': self.NODE_TYPE,
            'title': self.title,
            'pos_x': self.pos_x,
            'pos_y': self.pos_y,
            'state': self.state.value,
            # Los sockets y conexiones serán serializados por el graph_manager
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """Deserializa un nodo desde diccionario"""
        # Esta implementación será específica para cada tipo de nodo
        # La implementación base solo restaura propiedades comunes
        node = cls()
        node.id = data.get('id', node.id)
        node.title = data.get('title', node.title)
        node.pos_x = data.get('pos_x', 0.0)
        node.pos_y = data.get('pos_y', 0.0)
        return node
    
    def __str__(self) -> str:
        return f"{self.NODE_TYPE}({self.title})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id[:8]} title='{self.title}'>"

class NodeGraph:
    """
    Contenedor que mantiene una colección de nodos y sus conexiones
    """
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.connections: Dict[str, Connection] = {}
        
    def add_node(self, node: Node) -> str:
        """Añade un nodo al grafo"""
        self.nodes[node.id] = node
        return node.id
    
    def remove_node(self, node_id: str):
        """Remueve un nodo del grafo"""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            # Desconectar todas las conexiones
            node.disconnect_all()
            del self.nodes[node_id]
    
    def connect_nodes(self, output_node_id: str, output_socket_name: str,
                     input_node_id: str, input_socket_name: str) -> Connection:
        """Conecta dos nodos"""
        output_node = self.nodes[output_node_id]
        input_node = self.nodes[input_node_id]
        
        output_socket = output_node.output_sockets[output_socket_name]
        input_socket = input_node.input_sockets[input_socket_name]
        
        connection = Connection(output_socket, input_socket)
        self.connections[connection.id] = connection
        
        # Marcar el nodo de entrada como dirty
        input_node.mark_dirty()
        
        return connection
    
    def disconnect(self, connection_id: str):
        """Desconecta una conexión"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.disconnect()
            del self.connections[connection_id]
            
            # Marcar el nodo de entrada como dirty
            connection.input_socket.node.mark_dirty()
    
    def get_execution_order(self) -> List[Node]:
        """
        Obtiene el orden de ejecución de los nodos usando ordenamiento topológico
        """
        # Algoritmo de Kahn para ordenamiento topológico
        in_degree = {node_id: 0 for node_id in self.nodes}
        
        # Calcular grados de entrada
        for node in self.nodes.values():
            for input_socket in node.input_sockets.values():
                if input_socket.connections:
                    in_degree[node.id] += len(input_socket.connections)
        
        # Cola con nodos sin dependencias
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current_id = queue.pop(0)
            current_node = self.nodes[current_id]
            result.append(current_node)
            
            # Reducir grado de entrada de nodos dependientes
            for output_socket in current_node.output_sockets.values():
                for connection in output_socket.connections:
                    dependent_id = connection.input_socket.node.id
                    in_degree[dependent_id] -= 1
                    if in_degree[dependent_id] == 0:
                        queue.append(dependent_id)
        
        # Verificar ciclos
        if len(result) != len(self.nodes):
            raise ValueError("Cycle detected in node graph")
            
        return result
    
    def clear(self):
        """Limpia el grafo de todos los nodos y conexiones"""
        # Desconectar todo primero
        for node in self.nodes.values():
            node.disconnect_all()
            
        self.nodes.clear()
        self.connections.clear()