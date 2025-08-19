"""
Widget principal del editor de nodos
Combina la vista, escena y funcionalidad del editor
"""

import math
from typing import Optional, Dict, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene,
    QToolBar, QPushButton, QLabel, QSlider, QComboBox, QFrame,
    QMenu, QMenuBar, QStatusBar, QSplitter, QScrollArea, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QTimer
from PyQt6.QtGui import (
    QAction, QPainter, QBrush, QColor, QPen, QWheelEvent, 
    QMouseEvent, QKeyEvent, QPixmap, QIcon
)

from core.node_system import NodeGraph, Node
from .node_graphics import NodeGraphicsItem, create_node_graphics, NodeTheme
from .connection_graphics import ConnectionManager, ConnectionGraphicsItem

class NodeEditorScene(QGraphicsScene):
    """
    Escena especializada para el editor de nodos
    """
    
    # Señales
    node_selected = pyqtSignal(object)  # Node
    node_added = pyqtSignal(object)     # Node
    node_removed = pyqtSignal(object)   # Node
    connection_created = pyqtSignal(object)  # Connection
    connection_removed = pyqtSignal(object) # Connection
    
    # Constantes de la grilla
    GRID_SIZE = 20
    GRID_SQUARES = 5
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configurar escena
        self.setSceneRect(-5000, -5000, 10000, 10000)
        
        # Estado del editor
        self.node_graph = NodeGraph()
        self.node_graphics = {}  # node_id -> NodeGraphicsItem
        
        # Sistema de conexiones completo
        self.connection_manager = ConnectionManager(self)
        
        # Configuración visual
        self.grid_enabled = True
        self.snap_to_grid = False
        
        # Configurar colores
        self.setBackgroundBrush(QBrush(QColor(35, 35, 35)))
        
        # Timer para animaciones
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animations)
        self.animation_timer.start(50)  # 20 FPS para animaciones suaves
        
        print("🎬 Escena de editor inicializada con sistema completo de conexiones")
    
    def drawBackground(self, painter: QPainter, rect: QRectF):
        """Dibuja el fondo con grilla"""
        super().drawBackground(painter, rect)
        
        if not self.grid_enabled:
            return
        
        # Configurar painter
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        # Colores de la grilla
        grid_pen_fine = QPen(QColor(60, 60, 60), 1)
        grid_pen_thick = QPen(QColor(80, 80, 80), 2)
        
        # Calcular líneas visibles
        left = int(rect.left()) - (int(rect.left()) % self.GRID_SIZE)
        top = int(rect.top()) - (int(rect.top()) % self.GRID_SIZE)
        
        # Líneas verticales
        x = left
        while x < rect.right():
            if x % (self.GRID_SIZE * self.GRID_SQUARES) == 0:
                painter.setPen(grid_pen_thick)
            else:
                painter.setPen(grid_pen_fine)
            
            # Convertir a enteros para drawLine
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += self.GRID_SIZE
        
        # Líneas horizontales
        y = top
        while y < rect.bottom():
            if y % (self.GRID_SIZE * self.GRID_SQUARES) == 0:
                painter.setPen(grid_pen_thick)
            else:
                painter.setPen(grid_pen_fine)
            
            # Convertir a enteros para drawLine
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += self.GRID_SIZE
    
    def add_node(self, node: Node, position: QPointF = None) -> NodeGraphicsItem:
        """Añade un nodo a la escena"""
        # Añadir al modelo
        self.node_graph.add_node(node)
        
        # Crear representación gráfica
        node_graphics = create_node_graphics(node)
        
        # Aplicar tema
        NodeTheme.apply_category_colors(node_graphics)
        
        # Posicionar nodo
        if position:
            if self.snap_to_grid:
                position = self.snap_to_grid_point(position)
            node_graphics.setPos(position)
            node.pos_x = position.x()
            node.pos_y = position.y()
        
        # Añadir a la escena
        self.addItem(node_graphics)
        self.node_graphics[node.id] = node_graphics
        
        # Conectar señales
        self.node_added.emit(node)
        
        print(f"🎯 Nodo añadido: {node.title} con {len(node.input_sockets)} inputs y {len(node.output_sockets)} outputs")
        return node_graphics
    
    def remove_node(self, node_id: str):
        """Elimina un nodo de la escena"""
        if node_id not in self.node_graphics:
            return
        
        node_graphics = self.node_graphics[node_id]
        node = node_graphics.node
        
        # Eliminar conexiones relacionadas
        connections_to_remove = []
        for connection_id, connection_graphics in self.connection_manager.connections.items():
            if (connection_graphics.connection.output_socket.node.id == node_id or
                connection_graphics.connection.input_socket.node.id == node_id):
                connections_to_remove.append(connection_id)
        
        for connection_id in connections_to_remove:
            self.connection_manager.remove_connection_graphics(connection_id)
        
        # Eliminar del modelo
        self.node_graph.remove_node(node_id)
        
        # Eliminar gráficos
        self.removeItem(node_graphics)
        del self.node_graphics[node_id]
        
        # Emitir señal
        self.node_removed.emit(node)
    
    def snap_to_grid_point(self, point: QPointF) -> QPointF:
        """Ajusta un punto a la grilla"""
        x = round(point.x() / self.GRID_SIZE) * self.GRID_SIZE
        y = round(point.y() / self.GRID_SIZE) * self.GRID_SIZE
        return QPointF(x, y)
    
    def mouseMoveEvent(self, event):
        """Maneja movimiento del mouse"""
        # Actualizar conexión temporal si existe
        if self.connection_manager.temp_connection:
            self.connection_manager.update_temp_connection(event.scenePos())
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Maneja liberación del mouse"""
        # Finalizar conexión si hay una temporal
        if self.connection_manager.temp_connection:
            # Buscar socket en la posición
            item = self.itemAt(event.scenePos(), self.views()[0].transform())
            
            from .node_graphics import SocketGraphicsItem
            if isinstance(item, SocketGraphicsItem):
                self.connection_manager.finish_connection(item)
            else:
                self.connection_manager.cancel_connection()
        
        super().mouseReleaseEvent(event)
    
    def start_connection(self, socket_graphics):
        """Inicia la creación de una conexión"""
        self.connection_manager.start_connection(socket_graphics)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Maneja teclas presionadas"""
        if event.key() == Qt.Key.Key_Delete:
            # Eliminar items seleccionados
            self.delete_selected_items()
        elif event.key() == Qt.Key.Key_Escape:
            # Cancelar conexión temporal
            self.connection_manager.cancel_connection()
        
        super().keyPressEvent(event)
    
    def delete_selected_items(self):
        """Elimina los items seleccionados"""
        selected_items = self.selectedItems()
        
        for item in selected_items:
            if isinstance(item, NodeGraphicsItem):
                self.remove_node(item.node.id)
            elif isinstance(item, ConnectionGraphicsItem):
                if item.connection:
                    # Eliminar conexión del modelo
                    item.connection.disconnect()
                    # Eliminar gráficos
                    self.connection_manager.remove_connection_graphics(item.connection.id)
                    # Emitir señal
                    self.connection_removed.emit(item.connection)
    
    def update_connections_for_node(self, node_id: str):
        """Actualiza conexiones para un nodo específico"""
        self.connection_manager.update_connections_for_node(node_id)
    
    def update_animations(self):
        """Actualiza animaciones activas"""
        # Actualizar animaciones de conexiones activas
        for connection_graphics in self.connection_manager.connections.values():
            if connection_graphics.is_active:
                connection_graphics.update()
    
    def clear_all(self):
        """Limpia toda la escena"""
        self.clear()
        self.node_graph.clear()
        self.node_graphics.clear()
        self.connection_manager.connections.clear()
        print("🗑️ Escena limpiada completamente")
    
    def get_node_at_position(self, pos: QPointF) -> Optional[Node]:
        """Obtiene el nodo en una posición"""
        item = self.itemAt(pos, self.views()[0].transform())
        if isinstance(item, NodeGraphicsItem):
            return item.node
        return None
    
    def execute_graph(self):
        """Ejecuta el grafo de nodos con efectos visuales"""
        try:
            # Obtener orden de ejecución
            execution_order = self.node_graph.get_execution_order()
            
            # Resetear estados visuales
            for node_graphics in self.node_graphics.values():
                # Cambiar color temporalmente para mostrar ejecución
                pass
            
            # Ejecutar nodos con visualización
            for node in execution_order:
                node.mark_dirty()
                if hasattr(node, 'compute'):
                    result = node.compute()
                    
                    # Activar conexiones de salida
                    for output_socket in node.output_sockets.values():
                        for connection in output_socket.connections:
                            connection_graphics = self.connection_manager.connections.get(connection.id)
                            if connection_graphics:
                                connection_graphics.set_active(True)
                                
                                # Programar desactivación
                                QTimer.singleShot(1000, lambda cg=connection_graphics: cg.set_active(False))
            
            print(f"✅ Grafo ejecutado: {len(execution_order)} nodos")
            
        except Exception as e:
            print(f"❌ Error ejecutando grafo: {e}")

class NodeEditorView(QGraphicsView):
    """
    Vista especializada para el editor de nodos
    """
    
    def __init__(self, scene: NodeEditorScene, parent=None):
        super().__init__(scene, parent)
        
        # Configurar vista
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        # Configurar interacción
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setInteractive(True)
        
        # Configurar zoom
        self.zoom_factor = 1.0
        self.zoom_step = 1.15
        self.zoom_range = (0.1, 3.0)
        
        # Estado del editor
        self.middle_mouse_pressed = False
        self.last_pan_point = QPointF()
    
    def wheelEvent(self, event: QWheelEvent):
        """Maneja zoom con rueda del mouse"""
        # Zoom con Ctrl + rueda
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            zoom_in = event.angleDelta().y() > 0
            zoom_factor = self.zoom_step if zoom_in else 1.0 / self.zoom_step
            
            # Aplicar zoom
            self.scale_view(zoom_factor)
            event.accept()
        else:
            # Scroll normal
            super().wheelEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Maneja clicks del mouse"""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Pan con botón medio
            self.middle_mouse_pressed = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Maneja movimiento del mouse"""
        if self.middle_mouse_pressed:
            # Pan de la vista
            delta = event.pos() - self.last_pan_point
            self.last_pan_point = event.pos()
            
            # Mover vista
            h_bar = self.horizontalScrollBar()
            v_bar = self.verticalScrollBar()
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())
            
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Maneja liberación del mouse"""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.middle_mouse_pressed = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def scale_view(self, factor: float):
        """Escala la vista con límites"""
        new_zoom = self.zoom_factor * factor
        
        if self.zoom_range[0] <= new_zoom <= self.zoom_range[1]:
            self.scale(factor, factor)
            self.zoom_factor = new_zoom
    
    def fit_in_view_all(self):
        """Ajusta la vista para mostrar todos los items"""
        if self.scene().items():
            self.fitInView(self.scene().itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.zoom_factor = self.transform().m11()
    
    def reset_zoom(self):
        """Resetea el zoom a 100%"""
        self.resetTransform()
        self.zoom_factor = 1.0

class NodeEditorWidget(QWidget):
    """
    Widget principal del editor de nodos
    Combina la vista, herramientas y funcionalidad
    """
    
    # Señales
    node_selected = pyqtSignal(object)
    node_added = pyqtSignal(object)
    node_removed = pyqtSignal(object)
    connection_created = pyqtSignal(object)
    connection_removed = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Crear componentes
        self.scene = NodeEditorScene(self)
        self.view = NodeEditorView(self.scene, self)
        
        # Configurar layout
        self.init_ui()
        
        # Conectar señales
        self.connect_signals()
        
        print("🔗 Editor de nodos inicializado")
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar superior
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # Área principal con splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Vista del editor (área principal)
        self.view.setMinimumSize(400, 300)
        splitter.addWidget(self.view)
        
        # Panel lateral derecho (mini propiedades)
        side_panel = self.create_side_panel()
        side_panel.setMaximumWidth(200)
        splitter.addWidget(side_panel)
        
        # Configurar tamaños del splitter
        splitter.setSizes([600, 200])
        
        # Barra de estado
        self.status_bar = self.create_status_bar()
        layout.addWidget(self.status_bar)
    
    def create_toolbar(self) -> QToolBar:
        """Crea la barra de herramientas"""
        toolbar = QToolBar()
        toolbar.setStyleSheet("""
            QToolBar {
                background: #404040;
                border: none;
                spacing: 5px;
                padding: 5px;
            }
            QPushButton {
                background: #505050;
                border: 1px solid #606060;
                border-radius: 3px;
                padding: 5px 10px;
                color: white;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #606060;
            }
            QPushButton:pressed {
                background: #0078d4;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
        """)
        
        # Botones de control
        execute_btn = QPushButton("▶️ Ejecutar")
        execute_btn.clicked.connect(self.execute_graph)
        toolbar.addWidget(execute_btn)
        
        toolbar.addSeparator()
        
        clear_btn = QPushButton("🗑️ Limpiar")
        clear_btn.clicked.connect(self.clear_scene)
        toolbar.addWidget(clear_btn)
        
        toolbar.addSeparator()
        
        # Controles de vista
        fit_btn = QPushButton("🔍 Ajustar Vista")
        fit_btn.clicked.connect(self.view.fit_in_view_all)
        toolbar.addWidget(fit_btn)
        
        zoom_reset_btn = QPushButton("100%")
        zoom_reset_btn.clicked.connect(self.view.reset_zoom)
        toolbar.addWidget(zoom_reset_btn)
        
        toolbar.addSeparator()
        
        # Controles de grilla
        grid_btn = QPushButton("📐 Grilla")
        grid_btn.setCheckable(True)
        grid_btn.setChecked(True)
        grid_btn.clicked.connect(self.toggle_grid)
        toolbar.addWidget(grid_btn)
        
        snap_btn = QPushButton("🧲 Snap")
        snap_btn.setCheckable(True)
        snap_btn.clicked.connect(self.toggle_snap)
        toolbar.addWidget(snap_btn)
        
        toolbar.addSeparator()
        
        # Información de zoom
        self.zoom_label = QLabel("Zoom: 100%")
        toolbar.addWidget(self.zoom_label)
        
        return toolbar
    
    def create_side_panel(self) -> QWidget:
        """Crea el panel lateral con información rápida"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background: #353535;
                border: 1px solid #555;
            }
            QLabel {
                color: white;
                padding: 5px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        
        # Título
        title = QLabel("📊 Editor Info")
        title.setStyleSheet("font-weight: bold; font-size: 14px; background: #404040; padding: 8px;")
        layout.addWidget(title)
        
        # Contadores
        self.node_count_label = QLabel("Nodos: 0")
        layout.addWidget(self.node_count_label)
        
        self.connection_count_label = QLabel("Conexiones: 0")
        layout.addWidget(self.connection_count_label)
        
        # Separador visual
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #555;")
        layout.addWidget(separator)
        
        # Nodo seleccionado
        selected_title = QLabel("🎯 Seleccionado:")
        selected_title.setStyleSheet("font-weight: bold;")
        layout.addWidget(selected_title)
        
        self.selected_node_label = QLabel("Ninguno")
        self.selected_node_label.setWordWrap(True)
        layout.addWidget(self.selected_node_label)
        
        layout.addStretch()
        
        # Botones rápidos
        quick_title = QLabel("⚡ Acciones Rápidas:")
        quick_title.setStyleSheet("font-weight: bold;")
        layout.addWidget(quick_title)
        
        add_circle_btn = QPushButton("➕ Círculo")
        add_circle_btn.clicked.connect(self.add_circle_node)
        layout.addWidget(add_circle_btn)
        
        add_number_btn = QPushButton("➕ Número")
        add_number_btn.clicked.connect(self.add_number_node)
        layout.addWidget(add_number_btn)
        
        add_viewer_btn = QPushButton("➕ Visor")
        add_viewer_btn.clicked.connect(self.add_viewer_node)
        layout.addWidget(add_viewer_btn)
        
        return panel
    
    def create_status_bar(self) -> QFrame:
        """Crea la barra de estado"""
        status_bar = QFrame()
        status_bar.setFixedHeight(25)
        status_bar.setStyleSheet("""
            QFrame {
                background: #404040;
                border-top: 1px solid #555;
            }
            QLabel {
                color: white;
                padding: 0 10px;
                font-size: 11px;
            }
        """)
        
        layout = QHBoxLayout(status_bar)
        layout.setContentsMargins(5, 0, 5, 0)
        
        self.status_label = QLabel("Listo")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        self.coordinates_label = QLabel("X: 0, Y: 0")
        layout.addWidget(self.coordinates_label)
        
        return status_bar
    
    def connect_signals(self):
        """Conecta las señales internas"""
        # Señales de la escena
        self.scene.node_selected.connect(self.on_node_selected)
        self.scene.node_added.connect(self.on_node_added)
        self.scene.node_removed.connect(self.on_node_removed)
        self.scene.connection_created.connect(self.on_connection_created)
        self.scene.connection_removed.connect(self.on_connection_removed)
        
        # Reenviar señales al exterior
        self.scene.node_selected.connect(self.node_selected.emit)
        self.scene.node_added.connect(self.node_added.emit)
        self.scene.node_removed.connect(self.node_removed.emit)
        self.scene.connection_created.connect(self.connection_created.emit)
        self.scene.connection_removed.connect(self.connection_removed.emit)
        
        # Actualización de zoom
        self.view.scene().changed.connect(self.update_zoom_label)
    
    def execute_graph(self):
        """Ejecuta el grafo con efectos visuales"""
        self.scene.execute_graph()
        self.status_label.setText("Grafo ejecutado")
    
    def clear_scene(self):
        """Limpia la escena"""
        self.scene.clear_all()
        self.update_info_labels()
        self.status_label.setText("Escena limpiada")
    
    def toggle_grid(self, enabled: bool):
        """Activa/desactiva la grilla"""
        self.scene.grid_enabled = enabled
        self.scene.update()
        self.status_label.setText(f"Grilla {'activada' if enabled else 'desactivada'}")
    
    def toggle_snap(self, enabled: bool):
        """Activa/desactiva snap to grid"""
        self.scene.snap_to_grid = enabled
        self.status_label.setText(f"Snap {'activado' if enabled else 'desactivado'}")
    
    def add_circle_node(self):
        """Añade un nodo círculo"""
        try:
            from nodes.primitives.circle_node import CircleNode
            node = CircleNode("Círculo")
            
            # Posicionar en el centro de la vista
            center = self.view.mapToScene(self.view.rect().center())
            self.scene.add_node(node, center)
            
            self.status_label.setText("Nodo círculo añadido")
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
    
    def add_number_node(self):
        """Añade un nodo número"""
        try:
            from nodes.base.base_node import NumberParameterNode
            node = NumberParameterNode("Número")
            
            center = self.view.mapToScene(self.view.rect().center())
            self.scene.add_node(node, center)
            
            self.status_label.setText("Nodo número añadido")
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
    
    def add_viewer_node(self):
        """Añade un nodo visor"""
        try:
            from nodes.base.base_node import ViewerNode
            node = ViewerNode("Visor")
            
            center = self.view.mapToScene(self.view.rect().center())
            self.scene.add_node(node, center)
            
            self.status_label.setText("Nodo visor añadido")
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
    
    def on_node_selected(self, node):
        """Maneja selección de nodo"""
        if node:
            self.selected_node_label.setText(f"{node.title}\nTipo: {node.NODE_TYPE}")
        else:
            self.selected_node_label.setText("Ninguno")
    
    def on_node_added(self, node):
        """Maneja nodo añadido"""
        self.update_info_labels()
    
    def on_node_removed(self, node):
        """Maneja nodo eliminado"""
        self.update_info_labels()
    
    def on_connection_created(self, connection):
        """Maneja conexión creada"""
        self.update_info_labels()
    
    def on_connection_removed(self, connection):
        """Maneja conexión eliminada"""
        self.update_info_labels()
    
    def update_info_labels(self):
        """Actualiza las etiquetas de información"""
        node_count = len(self.scene.node_graphics)
        connection_count = len(self.scene.connection_manager.connections)
        
        self.node_count_label.setText(f"Nodos: {node_count}")
        self.connection_count_label.setText(f"Conexiones: {connection_count}")
    
    def update_zoom_label(self):
        """Actualiza la etiqueta de zoom"""
        zoom_percent = int(self.view.zoom_factor * 100)
        self.zoom_label.setText(f"Zoom: {zoom_percent}%")
    
    def get_scene_data(self) -> dict:
        """Obtiene los datos de la escena para serialización"""
        return {
            'nodes': [node.to_dict() for node in self.scene.node_graph.nodes.values()],
            'connections': [
                {
                    'id': conn.id,
                    'output_node': conn.output_socket.node.id,
                    'output_socket': conn.output_socket.name,
                    'input_node': conn.input_socket.node.id,
                    'input_socket': conn.input_socket.name
                }
                for conn in self.scene.connection_manager.connections.values()
                if conn.connection
            ]
        }
    
    def load_scene_data(self, data: dict):
        """Carga datos de escena desde serialización"""
        # Limpiar escena actual
        self.clear_scene()
        
        # TODO: Implementar carga completa de nodos y conexiones
        # Por ahora, solo mostrar que los datos fueron recibidos
        node_count = len(data.get('nodes', []))
        connection_count = len(data.get('connections', []))
        
        self.status_label.setText(f"Cargando: {node_count} nodos, {connection_count} conexiones")
        print(f"📁 Datos de escena recibidos: {node_count} nodos, {connection_count} conexiones")

# Función de conveniencia para crear el editor
def create_node_editor(parent=None) -> NodeEditorWidget:
    """Crea una instancia del editor de nodos"""
    return NodeEditorWidget(parent)

# Constantes de disponibilidad
NODE_EDITOR_AVAILABLE = True

# Funciones de utilidad para testing
def test_node_editor():
    """Prueba básica del editor de nodos"""
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    editor = create_node_editor()
    editor.show()
    
    # Añadir algunos nodos de prueba
    editor.add_circle_node()
    editor.add_number_node()
    editor.add_viewer_node()
    
    print("🧪 Editor de nodos en modo de prueba")
    print("💡 Consejos:")
    print("  - Arrastra los nodos para moverlos")
    print("  - Haz clic en los círculos (sockets) para crear conexiones")
    print("  - Usa Ctrl+Rueda para hacer zoom")
    print("  - Botón medio del mouse para hacer pan")
    print("  - Delete para eliminar elementos seleccionados")
    print("  - Escape para cancelar conexiones temporales")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_node_editor()