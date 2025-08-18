"""
Editor visual de nodos para GoboFlow - Version Completa
Permite crear, conectar y editar nodos de forma visual
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

try:
    from PyQt6.QtWidgets import (
        QWidget, QGraphicsView, QGraphicsScene, QGraphicsItem,
        QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem,
        QGraphicsLineItem, QVBoxLayout, QHBoxLayout, QLabel, QMenu
    )
    from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QPropertyAnimation
    from PyQt6.QtGui import (
        QPen, QBrush, QColor, QPainter, QPainterPath, QFont,
        QLinearGradient, QCursor
    )
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    class QWidget: pass
    class QGraphicsView: pass
    class QGraphicsItem: pass
    class pyqtSignal: pass

if PYQT_AVAILABLE:
    from config import NODE_COLORS, NODE_VISUAL, CONNECTION_VISUAL, DARK_THEME
    from core.node_system import Node, Socket, Connection, SocketDirection

class NodeState(Enum):
    """Estados visuales de los nodos"""
    NORMAL = "normal"
    SELECTED = "selected"
    HOVERED = "hovered"
    PROCESSING = "processing"
    ERROR = "error"

class SocketGraphics(QGraphicsEllipseItem):
    """Representación visual de un socket"""
    
    def __init__(self, socket: Socket, parent_node: 'NodeGraphics'):
        super().__init__(parent_node)
        
        self.socket = socket
        self.parent_node = parent_node
        self.connections: List['ConnectionGraphics'] = []
        
        # Configuración visual
        size = 16  # NODE_VISUAL["socket_size"]
        self.setRect(-size/2, -size/2, size, size)
        
        # Interactividad
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.setZValue(100)
        
        self._update_appearance()
        
    def _update_appearance(self):
        """Actualiza la apariencia del socket"""
        base_color = self._get_socket_color()
        
        pen = QPen(QColor(255, 255, 255), 3)
        self.setPen(pen)
        
        if self.socket.direction == SocketDirection.INPUT:
            if self.socket.connections:
                brush = QBrush(base_color)
            else:
                brush = QBrush(Qt.BrushStyle.NoBrush)
        else:
            brush = QBrush(base_color)
            
        self.setBrush(brush)
    
    def _get_socket_color(self) -> QColor:
        """Obtiene el color del socket según su tipo"""
        socket_type = self.socket.socket_type.__class__.__name__
        
        color_map = {
            "GeometryType": QColor(76, 175, 80),
            "NumberType": QColor(33, 150, 243),
            "VectorType": QColor(156, 39, 176),
            "ColorType": QColor(255, 193, 7),
            "BooleanType": QColor(244, 67, 54),
            "StringType": QColor(96, 125, 139),
        }
        
        return color_map.get(socket_type, QColor(158, 158, 158))
    
    def add_connection(self, connection: 'ConnectionGraphics'):
        if connection not in self.connections:
            self.connections.append(connection)
            self._update_appearance()
    
    def remove_connection(self, connection: 'ConnectionGraphics'):
        if connection in self.connections:
            self.connections.remove(connection)
            self._update_appearance()
    
    def hoverEnterEvent(self, event):
        self.setScale(1.3)
        pen = QPen(QColor(255, 255, 0), 4)
        self.setPen(pen)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.setScale(1.0)
        pen = QPen(QColor(255, 255, 255), 3)
        self.setPen(pen)
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"Socket clickeado: {self.socket.node.title}.{self.socket.name}")
            editor = self.parent_node.editor
            editor.start_connection(self)
            event.accept()
        else:
            event.ignore()

class ConnectionGraphics(QGraphicsItem):
    """Representación visual de una conexión"""
    
    def __init__(self, output_socket: SocketGraphics, input_socket: SocketGraphics, connection: Connection):
        super().__init__()
        
        self.output_socket = output_socket
        self.input_socket = input_socket
        self.connection = connection
        
        self.setZValue(-1)
        self.setAcceptHoverEvents(True)
        
        self._selected = False
        self._hovered = False
        
        output_socket.add_connection(self)
        input_socket.add_connection(self)
    
    def boundingRect(self) -> QRectF:
        start = self.output_socket.scenePos()
        end = self.input_socket.scenePos()
        
        margin = 100  # CONNECTION_VISUAL["curve_strength"]
        
        return QRectF(
            min(start.x(), end.x()) - margin,
            min(start.y(), end.y()) - margin,
            abs(end.x() - start.x()) + 2 * margin,
            abs(end.y() - start.y()) + 2 * margin
        )
    
    def paint(self, painter: QPainter, option, widget):
        start = self.mapFromScene(self.output_socket.scenePos())
        end = self.mapFromScene(self.input_socket.scenePos())
        
        if self._selected:
            pen = QPen(QColor(255, 255, 255), 3)
        elif self._hovered:
            pen = QPen(QColor(255, 255, 255), 3)
        else:
            color = self.output_socket._get_socket_color()
            pen = QPen(color, 2)
        
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        path = self._create_bezier_path(start, end)
        painter.drawPath(path)
    
    def _create_bezier_path(self, start: QPointF, end: QPointF) -> QPainterPath:
        path = QPainterPath()
        path.moveTo(start)
        
        curve_strength = 100
        control1 = QPointF(start.x() + curve_strength, start.y())
        control2 = QPointF(end.x() - curve_strength, end.y())
        
        path.cubicTo(control1, control2, end)
        return path
    
    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)

class NodeGraphics(QGraphicsRectItem):
    """Representación visual de un nodo"""
    
    def __init__(self, node: Node, editor: 'NodeEditorWidget'):
        super().__init__()
        
        self.node = node
        self.editor = editor
        self.state = NodeState.NORMAL
        
        self.input_sockets: Dict[str, SocketGraphics] = {}
        self.output_sockets: Dict[str, SocketGraphics] = {}
        
        self._init_appearance()
        self._create_sockets()
        self._create_title()
        
        # Interactividad
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(1)
        
        self.setPos(node.pos_x, node.pos_y)
    
    def _init_appearance(self):
        width = 180  # NODE_VISUAL["width"]
        height = 100  # NODE_VISUAL["height"]
        
        self.setRect(0, 0, width, height)
        self._update_appearance()
    
    def _update_appearance(self):
        category = getattr(self.node, 'NODE_CATEGORY', 'base')
        
        color_map = {
            'generators': '#4CAF50',
            'parameters': '#FFC107',
            'outputs': '#F44336',
            'modifiers': '#2196F3',
            'operations': '#FF9800',
            'materials': '#9C27B0',
            'base': '#757575'
        }
        
        base_color = QColor(color_map.get(category, '#757575'))
        
        if self.state == NodeState.SELECTED:
            base_color = base_color.lighter(150)
            pen_width = 3
        elif self.state == NodeState.HOVERED:
            base_color = base_color.lighter(120)
            pen_width = 2
        else:
            pen_width = 2
        
        gradient = QLinearGradient(0, 0, 0, 100)
        gradient.setColorAt(0, base_color.lighter(130))
        gradient.setColorAt(1, base_color.darker(130))
        
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(QColor(255, 255, 255, 180), pen_width))
    
    def _create_sockets(self):
        input_count = len(self.node.input_sockets)
        for i, (name, socket) in enumerate(self.node.input_sockets.items()):
            socket_graphics = SocketGraphics(socket, self)
            y = self._calculate_socket_y(i, input_count)
            socket_graphics.setPos(0, y)
            self.input_sockets[name] = socket_graphics
        
        output_count = len(self.node.output_sockets)
        for i, (name, socket) in enumerate(self.node.output_sockets.items()):
            socket_graphics = SocketGraphics(socket, self)
            y = self._calculate_socket_y(i, output_count)
            socket_graphics.setPos(180, y)
            self.output_sockets[name] = socket_graphics
    
    def _calculate_socket_y(self, index: int, total: int) -> float:
        title_height = 30
        available_height = 100 - title_height
        
        if total == 1:
            return title_height + available_height / 2
        else:
            spacing = available_height / (total + 1)
            return title_height + spacing * (index + 1)
    
    def _create_title(self):
        self.title_item = QGraphicsTextItem(self.node.title, self)
        self.title_item.setPos(8, 4)
        
        font = QFont("Arial", 10, QFont.Weight.Bold)
        self.title_item.setFont(font)
        self.title_item.setDefaultTextColor(QColor(255, 255, 255))
    
    def set_state(self, state: NodeState):
        if self.state != state:
            self.state = state
            self._update_appearance()
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self.node.pos_x = value.x()
            self.node.pos_y = value.y()
            
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            if value:
                self.set_state(NodeState.SELECTED)
                self.editor.node_selected.emit(self.node)
            else:
                self.set_state(NodeState.NORMAL)
        
        return super().itemChange(change, value)
    
    def hoverEnterEvent(self, event):
        if not self.isSelected():
            self.set_state(NodeState.HOVERED)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        if not self.isSelected():
            self.set_state(NodeState.NORMAL)
        super().hoverLeaveEvent(event)

class NodeEditorWidget(QGraphicsView):
    """Widget principal del editor de nodos"""
    
    node_selected = pyqtSignal(object)
    node_added = pyqtSignal(object)
    node_removed = pyqtSignal(object)
    connection_created = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        self.node_graphics: Dict[str, NodeGraphics] = {}
        self.connection_graphics: List[ConnectionGraphics] = []
        
        # Estado de conexión
        self.connecting_socket = None
        self.temp_connection_line = None
        self.is_connecting = False
        
        self._setup_view()
        
        print("✅ NodeEditorWidget completo inicializado")
    
    def _setup_view(self):
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        bg_color = QColor("#1e1e1e")  # DARK_THEME['background_dark']
        self.setBackgroundBrush(QBrush(bg_color))
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            items = self.scene.items(self.mapToScene(event.pos()))
            
            for item in items:
                if isinstance(item, SocketGraphics):
                    self.start_connection(item)
                    event.accept()
                    return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.is_connecting and self.temp_connection_line:
            scene_pos = self.mapToScene(event.pos())
            start_pos = self.connecting_socket.scenePos()
            
            self.temp_connection_line.setLine(
                start_pos.x(), start_pos.y(),
                scene_pos.x(), scene_pos.y()
            )
            event.accept()
            return
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_connecting:
            items = self.scene.items(self.mapToScene(event.pos()))
            
            target_socket = None
            for item in items:
                if isinstance(item, SocketGraphics) and item != self.connecting_socket:
                    target_socket = item
                    break
            
            if target_socket:
                self.finish_connection(target_socket)
            else:
                self.cancel_connection()
            event.accept()
            return
        
        super().mouseReleaseEvent(event)
    
    def add_node(self, node: Node, pos: QPointF = None) -> NodeGraphics:
        if pos:
            node.pos_x = pos.x()
            node.pos_y = pos.y()
        
        node_graphics = NodeGraphics(node, self)
        self.scene.addItem(node_graphics)
        
        self.node_graphics[node.id] = node_graphics
        self.node_added.emit(node)
        
        return node_graphics
    
    def create_connection(self, output_socket: SocketGraphics, input_socket: SocketGraphics):
        try:
            if not output_socket.socket.can_connect_to(input_socket.socket):
                print(f"No se puede conectar: tipos incompatibles")
                return None
            
            connection = Connection(output_socket.socket, input_socket.socket)
            connection_graphics = ConnectionGraphics(output_socket, input_socket, connection)
            self.scene.addItem(connection_graphics)
            self.connection_graphics.append(connection_graphics)
            
            self.connection_created.emit(connection)
            print(f"✅ Conexión creada: {output_socket.socket.node.title} → {input_socket.socket.node.title}")
            
            return connection_graphics
            
        except Exception as e:
            print(f"❌ Error creando conexión: {e}")
            return None
    
    def start_connection(self, socket: SocketGraphics):
        self.connecting_socket = socket
        self.is_connecting = True
        
        start_pos = socket.scenePos()
        self.temp_connection_line = QGraphicsLineItem(
            start_pos.x(), start_pos.y(), 
            start_pos.x(), start_pos.y()
        )
        
        pen = QPen(QColor(255, 255, 255, 128), 2)
        pen.setStyle(Qt.PenStyle.DashLine)
        self.temp_connection_line.setPen(pen)
        
        self.scene.addItem(self.temp_connection_line)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        
        print(f"🔗 Iniciando conexión desde: {socket.socket.node.title}")
    
    def finish_connection(self, target_socket: SocketGraphics):
        if self.connecting_socket and target_socket:
            if (self.connecting_socket.socket.direction == SocketDirection.OUTPUT and 
                target_socket.socket.direction == SocketDirection.INPUT):
                self.create_connection(self.connecting_socket, target_socket)
            elif (self.connecting_socket.socket.direction == SocketDirection.INPUT and 
                  target_socket.socket.direction == SocketDirection.OUTPUT):
                self.create_connection(target_socket, self.connecting_socket)
            else:
                print("❌ Direcciones incompatibles")
        
        self.cancel_connection()
    
    def cancel_connection(self):
        if self.temp_connection_line:
            self.scene.removeItem(self.temp_connection_line)
            self.temp_connection_line = None
        
        self.connecting_socket = None
        self.is_connecting = False
        
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
    
    def wheelEvent(self, event):
        zoom_factor = 1.25
        
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1/zoom_factor, 1/zoom_factor)
    
    def clear_all(self):
        self.cancel_connection()
        self.scene.clear()
        self.node_graphics.clear()
        self.connection_graphics.clear()

def create_node_editor(parent=None) -> NodeEditorWidget:
    if not PYQT_AVAILABLE:
        return None
        
    editor = NodeEditorWidget(parent)
    
    # Crear nodos de ejemplo
    try:
        from nodes.primitives.circle_node import CircleNode
        from nodes.base.base_node import NumberParameterNode, ViewerNode
        
        number_node = NumberParameterNode("Radio")
        circle_node = CircleNode("Círculo")
        viewer_node = ViewerNode("Vista Previa")
        
        editor.add_node(number_node, QPointF(50, 100))
        editor.add_node(circle_node, QPointF(300, 100))
        editor.add_node(viewer_node, QPointF(550, 100))
        
        print("✅ Nodos de ejemplo creados")
        
    except Exception as e:
        print(f"⚠️ Error creando nodos de ejemplo: {e}")
    
    return editor