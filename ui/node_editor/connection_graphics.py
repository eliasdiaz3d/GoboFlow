"""
Sistema de conexiones visuales para el editor de nodos
"""

import math
from typing import Optional, Tuple

from PyQt6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import (
    QPen, QBrush, QColor, QPainter, QPainterPath, 
    QLinearGradient, QPainterPathStroker
)

from core.node_system import Connection
from .node_graphics import SocketGraphicsItem

class ConnectionGraphicsItem(QGraphicsPathItem):
    """
    Representación visual de una conexión entre dos sockets
    """
    
    # Constantes de diseño
    CONNECTION_WIDTH = 3
    CONNECTION_WIDTH_SELECTED = 4
    CONNECTION_CURVE_FACTOR = 80  # Curvatura de las conexiones Bézier
    ARROW_SIZE = 8
    
    # Colores
    COLORS = {
        'default': QColor(150, 150, 150),
        'selected': QColor(255, 255, 100),
        'hover': QColor(200, 200, 200),
        'active': QColor(100, 255, 100),    # Cuando datos fluyen
        'error': QColor(255, 100, 100),     # Cuando hay error
        'shadow': QColor(0, 0, 0, 50)
    }
    
    def __init__(self, connection: Connection = None):
        super().__init__()
        
        self.connection = connection
        self.source_socket = None
        self.dest_socket = None
        
        # Estado visual
        self.is_active = False  # Si hay datos fluyendo
        self.has_error = False  # Si hay error en la conexión
        
        # Configurar item
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(-1)  # Detrás de los nodos
        
        # Configurar estilo inicial
        self.update_style()
        
        if connection:
            self.set_connection(connection)
    
    def set_connection(self, connection: Connection):
        """Establece la conexión del modelo asociada"""
        self.connection = connection
        self.update_path()
    
    def set_sockets(self, source_socket: SocketGraphicsItem, dest_socket: SocketGraphicsItem):
        """Establece los sockets gráficos de origen y destino"""
        self.source_socket = source_socket
        self.dest_socket = dest_socket
        self.update_path()
    
    def update_path(self):
        """Actualiza el path de la conexión"""
        if not self.source_socket or not self.dest_socket:
            return
        
        # Obtener posiciones exactas del centro de los sockets
        start_pos = self.get_socket_center_position(self.source_socket)
        end_pos = self.get_socket_center_position(self.dest_socket)
        
        # Crear path de conexión con curva Bézier
        path = self.create_bezier_path(start_pos, end_pos)
        self.setPath(path)
    
    def get_socket_center_position(self, socket_graphics):
        """Obtiene la posición exacta del centro de un socket"""
        # El socket está definido como un círculo centrado en (0,0) con radio
        # Entonces su centro real está en su posición + (0, 0)
        socket_pos = socket_graphics.pos()
        socket_scene_pos = socket_graphics.parent_node.mapToScene(socket_pos)
        return socket_scene_pos
    
    def create_bezier_path(self, start: QPointF, end: QPointF) -> QPainterPath:
        """Crea un path curvo entre dos puntos"""
        path = QPainterPath()
        path.moveTo(start)
        
        # Calcular puntos de control para la curva Bézier
        distance = abs(end.x() - start.x())
        curve_factor = min(self.CONNECTION_CURVE_FACTOR, distance / 2)
        
        # Los puntos de control salen horizontalmente de los sockets
        control1 = QPointF(start.x() + curve_factor, start.y())
        control2 = QPointF(end.x() - curve_factor, end.y())
        
        # Crear curva Bézier suave
        path.cubicTo(control1, control2, end)
        
        return path
    
    def update_style(self):
        """Actualiza el estilo visual de la conexión"""
        # Determinar color según estado
        if self.has_error:
            color = self.COLORS['error']
        elif self.is_active:
            color = self.COLORS['active']
        elif self.isSelected():
            color = self.COLORS['selected']
        else:
            # Color basado en el tipo de socket si está disponible
            if (self.source_socket and 
                hasattr(self.source_socket, 'socket') and
                hasattr(self.source_socket.socket, 'socket_type') and
                hasattr(self.source_socket.socket.socket_type, 'color')):
                color = QColor(self.source_socket.socket.socket_type.color)
            else:
                color = self.COLORS['default']
        
        # Determinar grosor
        width = self.CONNECTION_WIDTH_SELECTED if self.isSelected() else self.CONNECTION_WIDTH
        
        # Configurar pen
        pen = QPen(color, width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        self.setPen(pen)
    
    def paint(self, painter: QPainter, option, widget):
        """Dibuja la conexión con efectos visuales"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dibujar sombra sutil
        if not self.isSelected():
            shadow_pen = QPen(self.COLORS['shadow'], self.CONNECTION_WIDTH + 2)
            shadow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            shadow_path = self.path()
            shadow_path.translate(1, 1)
            painter.setPen(shadow_pen)
            painter.drawPath(shadow_path)
        
        # Dibujar conexión principal
        super().paint(painter, option, widget)
        
        # Dibujar flecha direccional si la conexión está activa
        if self.is_active:
            self.draw_flow_arrow(painter)
        
        # Dibujar indicador de datos si hay información fluyendo
        if self.is_active:
            self.draw_data_flow_effect(painter)
    
    def draw_flow_arrow(self, painter: QPainter):
        """Dibuja una flecha indicando la dirección del flujo de datos"""
        path = self.path()
        if path.isEmpty():
            return
        
        # Calcular posición en el medio del path
        percent = 0.5
        point = path.pointAtPercent(percent)
        angle = path.angleAtPercent(percent)
        
        # Crear flecha
        arrow_path = QPainterPath()
        arrow_size = self.ARROW_SIZE
        
        # Puntas de la flecha
        arrow_path.moveTo(0, -arrow_size/2)
        arrow_path.lineTo(arrow_size, 0)
        arrow_path.lineTo(0, arrow_size/2)
        arrow_path.lineTo(-arrow_size/4, 0)
        arrow_path.closeSubpath()
        
        # Transformar y dibujar
        painter.save()
        painter.translate(point)
        painter.rotate(-angle)  # Rotar según la dirección del path
        
        painter.fillPath(arrow_path, QBrush(self.pen().color()))
        painter.restore()
    
    def draw_data_flow_effect(self, painter: QPainter):
        """Dibuja efecto de partículas fluyendo por la conexión"""
        import time
        
        path = self.path()
        if path.isEmpty():
            return
        
        # Efecto de "pulso" basado en tiempo
        time_factor = time.time() * 2  # Velocidad del efecto
        
        # Dibujar múltiples puntos que se mueven a lo largo del path
        for i in range(3):
            # Calcular posición del punto en el path
            offset = (time_factor + i * 0.3) % 1.0
            point = path.pointAtPercent(offset)
            
            # Dibujar punto brillante
            painter.save()
            painter.setBrush(QBrush(QColor(255, 255, 255, 150)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(point, 3, 3)
            painter.restore()
    
    def hoverEnterEvent(self, event):
        """Maneja hover enter"""
        if not self.isSelected():
            # Resaltar conexión
            pen = self.pen()
            pen.setColor(self.COLORS['hover'])
            pen.setWidth(self.CONNECTION_WIDTH + 1)
            self.setPen(pen)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Maneja hover leave"""
        self.update_style()
        super().hoverLeaveEvent(event)
    
    def itemChange(self, change, value):
        """Maneja cambios en el item"""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self.update_style()
        return super().itemChange(change, value)
    
    def set_active(self, active: bool):
        """Establece si la conexión está activa (con datos fluyendo)"""
        self.is_active = active
        self.update_style()
        if active:
            # Forzar repintado para animación
            self.update()
    
    def set_error(self, has_error: bool):
        """Establece si la conexión tiene error"""
        self.has_error = has_error
        self.update_style()

class TempConnectionItem(QGraphicsPathItem):
    """
    Conexión temporal mostrada mientras se arrastra para crear una nueva conexión
    """
    
    def __init__(self, start_socket: SocketGraphicsItem):
        super().__init__()
        
        self.start_socket = start_socket
        self.end_point = QPointF()
        
        # Configurar estilo
        pen = QPen(QColor(255, 255, 255, 180), 2)
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)
        
        self.setZValue(-0.5)  # Entre nodos y conexiones normales
        
        # Posición inicial
        self.update_path()
    
    def set_end_point(self, point: QPointF):
        """Actualiza el punto final de la conexión temporal"""
        self.end_point = point
        self.update_path()
    
    def update_path(self):
        """Actualiza el path de la conexión temporal"""
        if not self.start_socket:
            return
        
        # Obtener posición exacta del centro del socket de inicio
        start_pos = self.start_socket.parent_node.mapToScene(self.start_socket.pos())
        
        # Crear path simple hacia el punto final
        path = QPainterPath()
        path.moveTo(start_pos)
        
        # Línea recta o curva simple según la distancia
        distance = (self.end_point - start_pos).manhattanLength()
        if distance > 50:
            # Curva simple para distancias largas
            control_offset = min(50, distance / 4)
            
            if self.start_socket.socket.direction.value == "output":
                control1 = QPointF(start_pos.x() + control_offset, start_pos.y())
                control2 = QPointF(self.end_point.x() - control_offset, self.end_point.y())
            else:
                control1 = QPointF(start_pos.x() - control_offset, start_pos.y())
                control2 = QPointF(self.end_point.x() + control_offset, self.end_point.y())
            
            path.cubicTo(control1, control2, self.end_point)
        else:
            # Línea recta para distancias cortas
            path.lineTo(self.end_point)
        
        self.setPath(path)

class ConnectionManager:
    """
    Gestor de conexiones visuales en el editor
    """
    
    def __init__(self, scene):
        self.scene = scene
        self.connections = {}  # connection_id -> ConnectionGraphicsItem
        self.temp_connection = None
        self.connection_start_socket = None
    
    def create_connection_graphics(self, connection: Connection) -> ConnectionGraphicsItem:
        """Crea la representación gráfica de una conexión"""
        connection_graphics = ConnectionGraphicsItem(connection)
        
        # Buscar los sockets gráficos correspondientes
        source_socket_graphics = self.find_socket_graphics(connection.output_socket.id)
        dest_socket_graphics = self.find_socket_graphics(connection.input_socket.id)
        
        if source_socket_graphics and dest_socket_graphics:
            connection_graphics.set_sockets(source_socket_graphics, dest_socket_graphics)
            
            # Añadir a la escena
            self.scene.addItem(connection_graphics)
            self.connections[connection.id] = connection_graphics
            
            print(f"🔗 Conexión gráfica creada: {connection.output_socket.node.title} -> {connection.input_socket.node.title}")
            return connection_graphics
        else:
            print(f"❌ Error: No se encontraron sockets gráficos para la conexión")
        
        return None
    
    def remove_connection_graphics(self, connection_id: str):
        """Elimina la representación gráfica de una conexión"""
        if connection_id in self.connections:
            connection_graphics = self.connections[connection_id]
            self.scene.removeItem(connection_graphics)
            del self.connections[connection_id]
    
    def find_socket_graphics(self, socket_id: str):
        """Busca el socket gráfico por ID"""
        for item in self.scene.items():
            if hasattr(item, 'sockets_graphics'):
                if socket_id in item.sockets_graphics:
                    return item.sockets_graphics[socket_id]
        return None
    
    def start_connection(self, socket_graphics: SocketGraphicsItem):
        """Inicia la creación de una nueva conexión"""
        self.connection_start_socket = socket_graphics
        
        # Crear conexión temporal
        self.temp_connection = TempConnectionItem(socket_graphics)
        self.scene.addItem(self.temp_connection)
        
        # Aplicar color del tipo de socket a la conexión temporal
        if hasattr(socket_graphics.socket.socket_type, 'color'):
            color = QColor(socket_graphics.socket.socket_type.color)
            pen = self.temp_connection.pen()
            pen.setColor(color)
            self.temp_connection.setPen(pen)
    
    def update_temp_connection(self, pos: QPointF):
        """Actualiza la posición de la conexión temporal"""
        if self.temp_connection:
            self.temp_connection.set_end_point(pos)
    
    def finish_connection(self, end_socket_graphics: SocketGraphicsItem = None):
        """Finaliza la creación de una conexión"""
        if not self.connection_start_socket:
            return False
        
        success = False
        
        if end_socket_graphics and end_socket_graphics != self.connection_start_socket:
            # Intentar crear conexión en el modelo
            try:
                start_socket = self.connection_start_socket.socket
                end_socket = end_socket_graphics.socket
                
                print(f"🔄 Intentando conectar: {start_socket.node.title}.{start_socket.name} -> {end_socket.node.title}.{end_socket.name}")
                
                # Verificar que la conexión es válida
                if start_socket.can_connect_to(end_socket):
                    # Determinar dirección de la conexión
                    if start_socket.direction.value == "output":
                        output_socket = start_socket
                        input_socket = end_socket
                    else:
                        output_socket = end_socket
                        input_socket = start_socket
                    
                    # Crear conexión en el modelo
                    from core.node_system import Connection
                    connection = Connection(output_socket, input_socket)
                    
                    # Crear representación gráfica
                    connection_graphics = self.create_connection_graphics(connection)
                    
                    if connection_graphics:
                        # Notificar a la escena sobre la nueva conexión
                        if hasattr(self.scene, 'connection_created'):
                            self.scene.connection_created.emit(connection)
                        
                        success = True
                        print(f"✅ Conexión creada exitosamente")
                    else:
                        print(f"❌ Error creando gráficos de conexión")
                else:
                    print(f"❌ Conexión no válida entre {start_socket.name} y {end_socket.name}")
                    
            except Exception as e:
                print(f"❌ Error creando conexión: {e}")
                import traceback
                traceback.print_exc()
        
        # Limpiar conexión temporal
        if self.temp_connection:
            self.scene.removeItem(self.temp_connection)
            self.temp_connection = None
        
        self.connection_start_socket = None
        return success
    
    def cancel_connection(self):
        """Cancela la creación de una conexión"""
        if self.temp_connection:
            self.scene.removeItem(self.temp_connection)
            self.temp_connection = None
        
        self.connection_start_socket = None
    
    def update_all_connections(self):
        """Actualiza todas las conexiones visuales"""
        for connection_graphics in self.connections.values():
            connection_graphics.update_path()
    
    def update_connections_for_node(self, node_id: str):
        """Actualiza las conexiones relacionadas con un nodo específico"""
        for connection_graphics in self.connections.values():
            if (connection_graphics.connection and 
                (connection_graphics.connection.output_socket.node.id == node_id or
                 connection_graphics.connection.input_socket.node.id == node_id)):
                connection_graphics.update_path()
    
    def set_connection_active(self, connection_id: str, active: bool):
        """Establece el estado activo de una conexión"""
        if connection_id in self.connections:
            self.connections[connection_id].set_active(active)
    
    def set_connection_error(self, connection_id: str, has_error: bool):
        """Establece el estado de error de una conexión"""
        if connection_id in self.connections:
            self.connections[connection_id].set_error(has_error)
    
    def highlight_data_flow(self, execution_order: list):
        """Resalta el flujo de datos durante la ejecución"""
        # Resetear todas las conexiones
        for connection_graphics in self.connections.values():
            connection_graphics.set_active(False)
        
        # Activar conexiones en orden de ejecución
        import time
        for i, node in enumerate(execution_order):
            # Simular delay de ejecución
            time.sleep(0.1)
            
            # Activar conexiones de salida del nodo
            for connection_graphics in self.connections.values():
                if (connection_graphics.connection and
                    connection_graphics.connection.output_socket.node == node):
                    connection_graphics.set_active(True)
    
    def get_connection_at_point(self, point: QPointF) -> Optional[ConnectionGraphicsItem]:
        """Obtiene la conexión en un punto específico"""
        for connection_graphics in self.connections.values():
            if connection_graphics.contains(connection_graphics.mapFromScene(point)):
                return connection_graphics
        return None

# Utilidades para conexiones
class ConnectionValidator:
    """
    Validador de conexiones entre sockets
    """
    
    @staticmethod
    def can_connect(source_socket, dest_socket) -> Tuple[bool, str]:
        """
        Verifica si dos sockets pueden conectarse
        Retorna (puede_conectar, mensaje_error)
        """
        if source_socket == dest_socket:
            return False, "No se puede conectar un socket consigo mismo"
        
        if source_socket.node == dest_socket.node:
            return False, "No se puede conectar sockets del mismo nodo"
        
        if source_socket.direction == dest_socket.direction:
            return False, "No se puede conectar sockets de la misma dirección"
        
        if not source_socket.socket_type.is_compatible_with(dest_socket.socket_type):
            return False, f"Tipos incompatibles: {source_socket.socket_type.name} -> {dest_socket.socket_type.name}"
        
        # Verificar conexiones múltiples
        if not source_socket.is_multi and len(source_socket.connections) > 0:
            return False, f"Socket {source_socket.name} ya tiene una conexión"
        
        if not dest_socket.is_multi and len(dest_socket.connections) > 0:
            return False, f"Socket {dest_socket.name} ya tiene una conexión"
        
        # Verificar ciclos
        if source_socket.node in dest_socket.node.get_dependencies():
            return False, "La conexión crearía un ciclo"
        
        return True, "Conexión válida"
    
    @staticmethod
    def get_connection_color(source_socket) -> QColor:
        """Obtiene el color apropiado para una conexión basado en el socket de origen"""
        if hasattr(source_socket.socket_type, 'color'):
            return QColor(source_socket.socket_type.color)
        return QColor(150, 150, 150)

class ConnectionAnimator:
    """
    Animador de efectos visuales para conexiones
    """
    
    def __init__(self):
        self.animated_connections = set()
    
    def start_flow_animation(self, connection_graphics: ConnectionGraphicsItem):
        """Inicia animación de flujo de datos"""
        connection_graphics.set_active(True)
        self.animated_connections.add(connection_graphics)
    
    def stop_flow_animation(self, connection_graphics: ConnectionGraphicsItem):
        """Detiene animación de flujo de datos"""
        connection_graphics.set_active(False)
        self.animated_connections.discard(connection_graphics)
    
    def update_animations(self):
        """Actualiza todas las animaciones activas"""
        for connection in self.animated_connections:
            connection.update()  # Forzar repintado para animación