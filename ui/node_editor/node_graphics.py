"""
Representación gráfica de nodos para el editor visual
"""

import math
from typing import Dict, List, Optional, Tuple

from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem, 
    QGraphicsTextItem, QGraphicsProxyWidget, QWidget, QVBoxLayout,
    QLabel, QPushButton, QSlider, QSpinBox, QDoubleSpinBox, QComboBox
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QObject
from PyQt6.QtGui import (
    QPen, QBrush, QColor, QPainter, QFont, QPainterPath, 
    QLinearGradient, QRadialGradient
)

class NodeGraphicsItem(QGraphicsRectItem):
    """
    Representación gráfica de un nodo en el editor
    """
    
    # Constantes de diseño
    NODE_WIDTH = 180
    NODE_HEIGHT = 120
    NODE_CORNER_RADIUS = 8
    SOCKET_RADIUS = 8
    SOCKET_SPACING = 20
    TITLE_HEIGHT = 30
    CONTENT_MARGIN = 10
    
    # Colores del tema
    COLORS = {
        'background': QColor(60, 60, 60),
        'background_selected': QColor(80, 120, 200),
        'border': QColor(40, 40, 40),
        'border_selected': QColor(100, 150, 255),
        'title_bg': QColor(40, 40, 40),
        'title_text': QColor(255, 255, 255),
        'content_bg': QColor(70, 70, 70),
        'socket_border': QColor(20, 20, 20),
        'socket_fill': QColor(150, 150, 150)
    }
    
    def __init__(self, node, parent=None):
        super().__init__(parent)
        
        self.node = node
        self.sockets_graphics = {}  # ID socket -> SocketGraphicsItem
        self.content_widget = None
        self.title_item = None
        
        # Configurar item gráfico
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges, True)
        
        # Configurar geometría
        self.setRect(0, 0, self.NODE_WIDTH, self.NODE_HEIGHT)
        
        # Inicializar componentes gráficos
        self.init_ui()
        self.init_sockets()
        
    def init_ui(self):
        """Inicializa los elementos de la interfaz del nodo"""
        # Título del nodo
        self.title_item = QGraphicsTextItem(self.node.title, self)
        self.title_item.setPos(self.CONTENT_MARGIN, 5)
        self.title_item.setDefaultTextColor(self.COLORS['title_text'])
        
        # Configurar fuente del título
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        self.title_item.setFont(font)
        
        # Widget de contenido personalizable
        self.content_widget = self.create_content_widget()
        if self.content_widget:
            proxy = QGraphicsProxyWidget(self)
            proxy.setWidget(self.content_widget)
            proxy.setPos(self.CONTENT_MARGIN, self.TITLE_HEIGHT + 5)
    
    def create_content_widget(self) -> Optional[QWidget]:
        """
        Crea el widget de contenido específico para el tipo de nodo
        Puede ser overrideado por subclases
        """
        # Widget básico con información del nodo
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget { 
                background: transparent; 
                color: white; 
                font-size: 9px;
            }
            QLabel { 
                color: #cccccc; 
                margin: 2px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Información básica del nodo
        type_label = QLabel(f"Tipo: {self.node.NODE_TYPE}")
        layout.addWidget(type_label)
        
        # Estado del nodo
        state_label = QLabel(f"Estado: {self.node.state.value}")
        layout.addWidget(state_label)
        
        widget.setMaximumWidth(self.NODE_WIDTH - 2 * self.CONTENT_MARGIN)
        return widget
    
    def init_sockets(self):
        """Inicializa los sockets gráficos"""
        input_y_start = self.TITLE_HEIGHT + 15
        output_y_start = self.TITLE_HEIGHT + 15
        
        input_count = 0
        output_count = 0
        
        # Sockets de entrada (lado izquierdo)
        for name, socket in self.node.input_sockets.items():
            y_pos = input_y_start + input_count * self.SOCKET_SPACING
            socket_graphics = SocketGraphicsItem(
                socket, 
                QPointF(0, y_pos),  # Posición donde queremos el centro del socket
                self
            )
            self.sockets_graphics[socket.id] = socket_graphics
            input_count += 1
        
        # Sockets de salida (lado derecho)
        for name, socket in self.node.output_sockets.items():
            y_pos = output_y_start + output_count * self.SOCKET_SPACING
            socket_graphics = SocketGraphicsItem(
                socket,
                QPointF(self.NODE_WIDTH, y_pos),  # Posición donde queremos el centro del socket
                self
            )
            self.sockets_graphics[socket.id] = socket_graphics
            output_count += 1
        
        # Ajustar altura del nodo según el número de sockets
        max_sockets = max(input_count, output_count, 1)
        content_height = max_sockets * self.SOCKET_SPACING + 30
        min_height = self.TITLE_HEIGHT + content_height
        new_height = max(self.NODE_HEIGHT, min_height)
        
        self.setRect(0, 0, self.NODE_WIDTH, new_height)
    
    def paint(self, painter: QPainter, option, widget):
        """Dibuja el nodo"""
        rect = self.rect()
        
        # Configurar antialiasing
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Determinar colores según selección
        if self.isSelected():
            bg_color = self.COLORS['background_selected']
            border_color = self.COLORS['border_selected']
            border_width = 2
        else:
            bg_color = self.COLORS['background']
            border_color = self.COLORS['border']
            border_width = 1
        
        # Crear path del nodo con esquinas redondeadas
        path = QPainterPath()
        path.addRoundedRect(rect, self.NODE_CORNER_RADIUS, self.NODE_CORNER_RADIUS)
        
        # Fondo del nodo con gradiente
        gradient = QLinearGradient(0, 0, 0, rect.height())
        gradient.setColorAt(0, bg_color.lighter(110))
        gradient.setColorAt(1, bg_color.darker(110))
        
        brush = QBrush(gradient)
        painter.fillPath(path, brush)
        
        # Borde del nodo
        pen = QPen(border_color, border_width)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Área del título
        title_rect = QRectF(0, 0, rect.width(), float(self.TITLE_HEIGHT))
        title_path = QPainterPath()
        title_path.addRoundedRect(title_rect, self.NODE_CORNER_RADIUS, self.NODE_CORNER_RADIUS)
        
        # Clip para que solo se vea la parte superior redondeada
        painter.setClipPath(title_path)
        
        title_gradient = QLinearGradient(0, 0, 0, int(self.TITLE_HEIGHT))
        title_gradient.setColorAt(0, self.COLORS['title_bg'].lighter(120))
        title_gradient.setColorAt(1, self.COLORS['title_bg'])
        
        painter.fillRect(title_rect, QBrush(title_gradient))
        
        # Restaurar clipping
        painter.setClipping(False)
        
        # Línea separadora entre título y contenido
        painter.setPen(QPen(border_color, 1))
        painter.drawLine(0, int(self.TITLE_HEIGHT), int(rect.width()), int(self.TITLE_HEIGHT))
    
    def get_socket_position(self, socket_id: str) -> QPointF:
        """Obtiene la posición mundial del centro exacto de un socket"""
        if socket_id in self.sockets_graphics:
            socket_graphics = self.sockets_graphics[socket_id]
            # Como el socket está centrado en su posición, la posición ES el centro
            return self.mapToScene(socket_graphics.pos())
        return QPointF()
    
    def itemChange(self, change, value):
        """Maneja cambios en el item (movimiento, selección, etc.)"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Actualizar posición del nodo en el modelo
            if hasattr(self.node, 'pos_x') and hasattr(self.node, 'pos_y'):
                self.node.pos_x = value.x()
                self.node.pos_y = value.y()
        
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Actualizar conexiones después del movimiento
            self.update_connections()
        
        return super().itemChange(change, value)
    
    def update_connections(self):
        """Actualiza las conexiones visuales conectadas a este nodo"""
        scene = self.scene()
        if scene and hasattr(scene, 'update_connections_for_node'):
            scene.update_connections_for_node(self.node.id)

class SocketGraphicsItem(QGraphicsEllipseItem):
    """
    Representación gráfica de un socket
    """
    
    def __init__(self, socket, center_position: QPointF, parent_node: NodeGraphicsItem):
        radius = parent_node.SOCKET_RADIUS
        # Crear el socket centrado en (0,0) con el radio dado
        super().__init__(-radius, -radius, radius * 2, radius * 2, parent_node)
        
        self.socket = socket
        self.parent_node = parent_node
        
        # La posición pasada es donde queremos el CENTRO del socket
        # Como el socket está definido centrado en (0,0), simplemente usar esa posición
        self.setPos(center_position)
        
        # Configurar interactividad
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setAcceptHoverEvents(True)
        
        # Color según tipo de socket
        self.update_socket_color()
        
        print(f"🔌 Socket '{socket.name}' posicionado en centro: ({center_position.x()}, {center_position.y()})")
    
    def update_socket_color(self):
        """Actualiza el color del socket según su tipo"""
        # Obtener color del tipo de socket
        if hasattr(self.socket.socket_type, 'color'):
            color = QColor(self.socket.socket_type.color)
        else:
            color = QColor(150, 150, 150)  # Gris por defecto
        
        # Configurar brush y pen
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor(20, 20, 20), 2))
    
    def paint(self, painter: QPainter, option, widget):
        """Dibuja el socket"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dibujar círculo base
        super().paint(painter, option, widget)
        
        # Dibujar indicador de conexión si está conectado
        if self.socket.connections:
            inner_radius = self.rect().width() / 4
            inner_rect = QRectF(-inner_radius, -inner_radius, inner_radius * 2, inner_radius * 2)
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(inner_rect)
    
    def hoverEnterEvent(self, event):
        """Maneja el evento de hover enter"""
        # Resaltar socket al hacer hover
        self.setBrush(QBrush(self.brush().color().lighter(130)))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Maneja el evento de hover leave"""
        # Restaurar color original
        self.update_socket_color()
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """Maneja clicks en el socket para crear conexiones"""
        if event.button() == Qt.MouseButton.LeftButton:
            scene = self.scene()
            if scene and hasattr(scene, 'start_connection'):
                scene.start_connection(self)
                event.accept()
                print(f"🔌 Click en socket: {self.socket.name} ({self.socket.direction.value})")
            return
        super().mousePressEvent(event)

class ParameterNodeGraphics(NodeGraphicsItem):
    """
    Nodo gráfico especializado para nodos de parámetros
    """
    
    def create_content_widget(self) -> Optional[QWidget]:
        """Crea widget con control del parámetro"""
        if not hasattr(self.node, 'parameter_type'):
            return super().create_content_widget()
        
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget { 
                background: transparent; 
                color: white; 
            }
            QSlider { 
                background: transparent;
            }
            QSpinBox, QDoubleSpinBox {
                background: #404040;
                border: 1px solid #606060;
                border-radius: 3px;
                padding: 2px;
                color: white;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Crear control según el tipo de parámetro
        from core.socket_types import NumberType, VectorType, ColorType
        
        if isinstance(self.node.parameter_type, NumberType):
            # Control numérico
            value_label = QLabel(f"Valor: {self.node.parameter_value:.2f}")
            layout.addWidget(value_label)
            
            # Slider para valores numéricos
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(1000)
            slider.setValue(int(self.node.parameter_value * 10))
            
            def on_slider_change(value):
                new_value = value / 10.0
                self.node.set_parameter("value", new_value)
                value_label.setText(f"Valor: {new_value:.2f}")
                self.node.mark_dirty()
            
            slider.valueChanged.connect(on_slider_change)
            layout.addWidget(slider)
            
        elif isinstance(self.node.parameter_type, VectorType):
            # Control de vector
            layout.addWidget(QLabel("Vector:"))
            
            x_spin = QDoubleSpinBox()
            x_spin.setRange(-9999, 9999)
            x_spin.setValue(self.node.parameter_value[0] if self.node.parameter_value else 0)
            layout.addWidget(x_spin)
            
            y_spin = QDoubleSpinBox()
            y_spin.setRange(-9999, 9999)  
            y_spin.setValue(self.node.parameter_value[1] if self.node.parameter_value else 0)
            layout.addWidget(y_spin)
            
            def update_vector():
                new_value = [x_spin.value(), y_spin.value()]
                self.node.set_parameter("value", new_value)
                self.node.mark_dirty()
            
            x_spin.valueChanged.connect(update_vector)
            y_spin.valueChanged.connect(update_vector)
        
        widget.setMaximumWidth(self.NODE_WIDTH - 2 * self.CONTENT_MARGIN)
        return widget

class ViewerNodeGraphics(NodeGraphicsItem):
    """
    Nodo gráfico especializado para nodos visor
    """
    
    def create_content_widget(self) -> Optional[QWidget]:
        """Crea widget con preview del contenido"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget { 
                background: transparent; 
                color: white; 
            }
            QLabel { 
                color: #cccccc; 
                margin: 2px;
                font-size: 9px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Información del contenido visualizado
        info_label = QLabel("👁️ Viewer")
        layout.addWidget(info_label)
        
        # Estado del viewer
        if hasattr(self.node, 'get_data_info'):
            data_info = self.node.get_data_info()
            type_label = QLabel(f"Tipo: {data_info.get('data_type', 'None')}")
            layout.addWidget(type_label)
            
            if data_info.get('has_data'):
                status_label = QLabel("✅ Con datos")
            else:
                status_label = QLabel("⚪ Sin datos")
            layout.addWidget(status_label)
        
        widget.setMaximumWidth(self.NODE_WIDTH - 2 * self.CONTENT_MARGIN)
        return widget

# Factory function para crear nodos gráficos
def create_node_graphics(node) -> NodeGraphicsItem:
    """
    Factory function para crear la representación gráfica apropiada según el tipo de nodo
    """
    # Importar aquí para evitar importaciones circulares
    from nodes.base.base_node import ParameterNode, ViewerNode
    
    if isinstance(node, ParameterNode):
        return ParameterNodeGraphics(node)
    elif isinstance(node, ViewerNode):
        return ViewerNodeGraphics(node)
    else:
        return NodeGraphicsItem(node)

# Utilidades de diseño
class NodeTheme:
    """
    Tema visual para los nodos
    """
    
    @staticmethod
    def get_node_color(node_category: str) -> QColor:
        """Obtiene el color base para una categoría de nodo"""
        colors = {
            'primitives': QColor(100, 150, 100),    # Verde
            'generators': QColor(150, 100, 150),    # Púrpura
            'modifiers': QColor(150, 150, 100),     # Amarillo
            'operations': QColor(150, 100, 100),    # Rojo
            'parameters': QColor(100, 100, 150),    # Azul
            'outputs': QColor(100, 150, 150),       # Cian
            'utilities': QColor(120, 120, 120),     # Gris
        }
        
        return colors.get(node_category, QColor(80, 80, 80))
    
    @staticmethod
    def apply_category_colors(node_graphics: NodeGraphicsItem):
        """Aplica colores según la categoría del nodo"""
        if hasattr(node_graphics.node, 'NODE_CATEGORY'):
            base_color = NodeTheme.get_node_color(node_graphics.node.NODE_CATEGORY)
            
            # Modificar colores del nodo
            node_graphics.COLORS['background'] = base_color
            node_graphics.COLORS['background_selected'] = base_color.lighter(140)
            node_graphics.COLORS['title_bg'] = base_color.darker(120)