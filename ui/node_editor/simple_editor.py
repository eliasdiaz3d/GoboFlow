"""
Editor simple para GoboFlow con navegación y zoom
"""

try:
    from PyQt6.QtWidgets import (
        QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, 
        QFrame, QTextEdit, QScrollArea, QSizePolicy
    )
    from PyQt6.QtCore import pyqtSignal, Qt, QPoint
    from PyQt6.QtGui import QFont, QWheelEvent, QMouseEvent
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    class QWidget: pass
    class pyqtSignal: 
        def connect(self, *args): pass

class NavigableArea(QScrollArea):
    """Área navegable con zoom y pan"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuración del scroll area
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Variables para pan
        self.last_pan_point = QPoint()
        self.is_panning = False
        
        # Zoom
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 3.0
        
        # Contenedor para nodos
        self.content_widget = QWidget()
        self.content_widget.setMinimumSize(1200, 800)
        self.content_widget.setStyleSheet("""
            background: qradialgradient(cx:0.5, cy:0.5, radius:1,
                stop:0 #2d2d2d, stop:1 #1a1a1a);
        """)
        
        # Layout absoluto para posicionar nodos libremente
        self.nodes_layout = None  # Usar posicionamiento manual
        
        self.setWidget(self.content_widget)
        
    def wheelEvent(self, event: QWheelEvent):
        """Zoom con rueda del mouse"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Zoom
            zoom_in = event.angleDelta().y() > 0
            zoom_factor = 1.25 if zoom_in else 1/1.25
            
            new_zoom = self.zoom_factor * zoom_factor
            new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
            
            if new_zoom != self.zoom_factor:
                self.zoom_factor = new_zoom
                self._apply_zoom()
        else:
            # Scroll normal
            super().wheelEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Iniciar pan con botón medio o ctrl+click izquierdo"""
        if (event.button() == Qt.MouseButton.MiddleButton or 
            (event.button() == Qt.MouseButton.LeftButton and 
             event.modifiers() == Qt.KeyboardModifier.ControlModifier)):
            self.is_panning = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Pan del viewport"""
        if self.is_panning:
            delta = event.pos() - self.last_pan_point
            self.last_pan_point = event.pos()
            
            # Mover scrollbars
            h_value = self.horizontalScrollBar().value() - delta.x()
            v_value = self.verticalScrollBar().value() - delta.y()
            
            self.horizontalScrollBar().setValue(h_value)
            self.verticalScrollBar().setValue(v_value)
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Terminar pan"""
        if event.button() in [Qt.MouseButton.MiddleButton, Qt.MouseButton.LeftButton]:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)
    
    def _apply_zoom(self):
        """Aplica el zoom al contenido"""
        transform = f"scale({self.zoom_factor})"
        self.content_widget.setStyleSheet(f"""
            background: qradialgradient(cx:0.5, cy:0.5, radius:1,
                stop:0 #2d2d2d, stop:1 #1a1a1a);
            transform: {transform};
        """)

class NodeWidget(QFrame):
    """Widget individual para un nodo"""
    
    node_selected = pyqtSignal(object)
    node_executed = pyqtSignal(object)
    
    def __init__(self, node, parent=None):
        super().__init__(parent)
        
        self.node = node
        self.is_selected = False
        
        # Configuración del widget
        self.setFixedSize(200, 120)
        self.setFrameStyle(QFrame.Shape.Box)
        
        self._setup_ui()
        self._update_style()
    
    def _setup_ui(self):
        """Configura la interfaz del nodo"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Título
        self.title_label = QLabel(self.node.title)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12px; color: white;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Botón ejecutar
        self.execute_btn = QPushButton("▶")
        self.execute_btn.setFixedSize(25, 20)
        self.execute_btn.setStyleSheet("""
            QPushButton { 
                background: #333; border: 1px solid #666; 
                border-radius: 3px; color: white; font-size: 10px;
            }
            QPushButton:hover { background: #555; }
        """)
        self.execute_btn.clicked.connect(self._execute_node)
        header_layout.addWidget(self.execute_btn)
        
        layout.addLayout(header_layout)
        
        # Información del nodo
        node_type = getattr(self.node, 'NODE_TYPE', 'unknown')
        category = getattr(self.node, 'NODE_CATEGORY', 'base')
        
        type_label = QLabel(f"{node_type}")
        type_label.setStyleSheet("font-size: 10px; color: #ccc;")
        layout.addWidget(type_label)
        
        # Sockets info
        inputs = len(self.node.input_sockets)
        outputs = len(self.node.output_sockets)
        io_label = QLabel(f"📥 {inputs} → 📤 {outputs}")
        io_label.setStyleSheet("font-size: 9px; color: #aaa;")
        layout.addWidget(io_label)
        
        # Parámetros (si los tiene)
        if hasattr(self.node, 'get_all_parameters'):
            params = self.node.get_all_parameters()
            if params:
                params_text = ", ".join([f"{k}:{v}" for k, v in list(params.items())[:2]])
                if len(params_text) > 30:
                    params_text = params_text[:27] + "..."
                params_label = QLabel(params_text)
                params_label.setStyleSheet("font-size: 8px; color: #888;")
                layout.addWidget(params_label)
        
        layout.addStretch()
    
    def _update_style(self):
        """Actualiza el estilo del nodo"""
        category = getattr(self.node, 'NODE_CATEGORY', 'base')
        
        color_map = {
            'generators': '#4CAF50',  # Verde
            'parameters': '#FFC107',  # Amarillo
            'outputs': '#F44336',     # Rojo
            'modifiers': '#2196F3',   # Azul
            'base': '#757575'         # Gris
        }
        
        base_color = color_map.get(category, '#757575')
        
        if self.is_selected:
            border_color = "#ffff00"
            border_width = "3px"
        else:
            border_color = "#fff"
            border_width = "2px"
        
        self.setStyleSheet(f"""
            NodeWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {base_color}E0, stop:1 {base_color}A0);
                border: {border_width} solid {border_color};
                border-radius: 8px;
            }}
            NodeWidget:hover {{
                border-color: #ffff00;
            }}
        """)
    
    def _execute_node(self):
        """Ejecuta el nodo"""
        try:
            self.node.mark_dirty()
            result = self.node.compute()
            self.node_executed.emit(self.node)
            print(f"✅ Ejecutado: {self.node.title}")
        except Exception as e:
            print(f"❌ Error ejecutando {self.node.title}: {e}")
    
    def mousePressEvent(self, event: QMouseEvent):
        """Seleccionar nodo"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_selected = True
            self._update_style()
            self.node_selected.emit(self.node)
        super().mousePressEvent(event)
    
    def set_selected(self, selected: bool):
        """Establece si el nodo está seleccionado"""
        self.is_selected = selected
        self._update_style()

class SimpleNodeEditor(QWidget):
    """Editor de nodos simple con navegación"""
    
    # Señales necesarias para compatibilidad
    node_selected = pyqtSignal(object)
    node_added = pyqtSignal(object)
    node_removed = pyqtSignal(object)
    connection_created = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.nodes = {}
        self.node_widgets = {}
        self.selected_node = None
        
        self._setup_ui()
        self._create_example_nodes()
        
        print("✅ SimpleNodeEditor con navegación inicializado")
    
    def _setup_ui(self):
        """Configura la interfaz"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(40)
        header.setStyleSheet("background: #3c3c3c; border-bottom: 1px solid #555;")
        
        header_layout = QHBoxLayout(header)
        
        title = QLabel("🎨 Editor de Nodos")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Indicador de zoom
        self.zoom_label = QLabel("Zoom: 100%")
        self.zoom_label.setStyleSheet("color: #ccc; font-size: 11px;")
        header_layout.addWidget(self.zoom_label)
        
        layout.addWidget(header)
        
        # Área navegable
        self.nav_area = NavigableArea()
        layout.addWidget(self.nav_area)
        
        # Footer con controles
        footer = QFrame()
        footer.setFixedHeight(100)
        footer.setStyleSheet("background: #2d2d2d; border-top: 1px solid #555;")
        
        footer_layout = QVBoxLayout(footer)
        
        # Controles
        controls_layout = QHBoxLayout()
        
        zoom_out_btn = QPushButton("🔍-")
        zoom_out_btn.setFixedSize(40, 25)
        zoom_out_btn.clicked.connect(self._zoom_out)
        controls_layout.addWidget(zoom_out_btn)
        
        zoom_reset_btn = QPushButton("⌂")
        zoom_reset_btn.setFixedSize(40, 25)
        zoom_reset_btn.clicked.connect(self._zoom_reset)
        controls_layout.addWidget(zoom_reset_btn)
        
        zoom_in_btn = QPushButton("🔍+")
        zoom_in_btn.setFixedSize(40, 25)
        zoom_in_btn.clicked.connect(self._zoom_in)
        controls_layout.addWidget(zoom_in_btn)
        
        controls_layout.addStretch()
        
        # Info de controles
        help_label = QLabel("💡 Ctrl+Rueda: Zoom | Ctrl+Click: Pan | Click: Seleccionar")
        help_label.setStyleSheet("color: #aaa; font-size: 10px;")
        controls_layout.addWidget(help_label)
        
        footer_layout.addLayout(controls_layout)
        
        # Info del nodo seleccionado
        self.info_label = QLabel("Selecciona un nodo para ver información")
        self.info_label.setStyleSheet("color: #ccc; font-size: 11px; padding: 5px;")
        self.info_label.setWordWrap(True)
        footer_layout.addWidget(self.info_label)
        
        layout.addWidget(footer)
    
    def _create_example_nodes(self):
        """Crea nodos de ejemplo en posiciones específicas"""
        try:
            from nodes.base.base_node import NumberParameterNode, ViewerNode
            from nodes.primitives.circle_node import CircleNode
            
            # Nodos con posiciones manuales
            nodes_data = [
                (NumberParameterNode("Radio"), 50, 50),
                (CircleNode("Círculo"), 300, 50),
                (ViewerNode("Vista Previa"), 550, 50),
                (NumberParameterNode("Segmentos"), 50, 200),
                (CircleNode("Círculo 2"), 300, 200),
            ]
            
            for node, x, y in nodes_data:
                if hasattr(node, 'set_parameter') and 'Radio' in node.title:
                    node.set_parameter("value", 75.0)
                elif hasattr(node, 'set_parameter') and 'Segmentos' in node.title:
                    node.set_parameter("value", 16)
                
                self.add_node(node, x, y)
            
        except Exception as e:
            print(f"⚠️ Error creando nodos de ejemplo: {e}")
    
    def add_node(self, node, x=100, y=100):
        """Añade un nodo en la posición especificada"""
        try:
            # Crear widget del nodo
            node_widget = NodeWidget(node, self.nav_area.content_widget)
            node_widget.move(x, y)
            node_widget.show()
            
            # Conectar señales
            node_widget.node_selected.connect(self._on_node_selected)
            node_widget.node_executed.connect(self._on_node_executed)
            
            # Registrar
            self.nodes[node.id] = node
            self.node_widgets[node.id] = node_widget
            
            # Emitir señal
            self.node_added.emit(node)
            
            print(f"➕ Nodo añadido: {node.title} en ({x}, {y})")
            
        except Exception as e:
            print(f"❌ Error añadiendo nodo: {e}")
    
    def _on_node_selected(self, node):
        """Maneja selección de nodo"""
        # Deseleccionar anterior
        if self.selected_node:
            old_widget = self.node_widgets.get(self.selected_node.id)
            if old_widget:
                old_widget.set_selected(False)
        
        # Seleccionar nuevo
        self.selected_node = node
        self.node_selected.emit(node)
        
        # Actualizar info
        self._update_info_display(node)
    
    def _on_node_executed(self, node):
        """Maneja ejecución de nodo"""
        try:
            info = ""
            if hasattr(node, 'get_preview_info'):
                preview = node.get_preview_info()
                info = f" | {preview}"
            
            self.info_label.setText(f"▶️ Ejecutado: {node.title}{info}")
        except Exception as e:
            self.info_label.setText(f"❌ Error ejecutando {node.title}: {e}")
    
    def _update_info_display(self, node):
        """Actualiza la información mostrada"""
        info_text = f"📋 {node.title} | {getattr(node, 'NODE_TYPE', 'unknown')}"
        
        # Sockets
        inputs = len(node.input_sockets)
        outputs = len(node.output_sockets)
        info_text += f" | 📥{inputs} → 📤{outputs}"
        
        # Parámetros
        if hasattr(node, 'get_all_parameters'):
            params = node.get_all_parameters()
            if params:
                key_params = list(params.items())[:3]
                params_str = ", ".join([f"{k}:{v}" for k, v in key_params])
                info_text += f" | {params_str}"
        
        self.info_label.setText(info_text)
    
    def _zoom_in(self):
        """Zoom in"""
        self.nav_area.zoom_factor = min(self.nav_area.max_zoom, self.nav_area.zoom_factor * 1.25)
        self.nav_area._apply_zoom()
        self._update_zoom_display()
    
    def _zoom_out(self):
        """Zoom out"""
        self.nav_area.zoom_factor = max(self.nav_area.min_zoom, self.nav_area.zoom_factor / 1.25)
        self.nav_area._apply_zoom()
        self._update_zoom_display()
    
    def _zoom_reset(self):
        """Reset zoom"""
        self.nav_area.zoom_factor = 1.0
        self.nav_area._apply_zoom()
        self._update_zoom_display()
    
    def _update_zoom_display(self):
        """Actualiza el display del zoom"""
        zoom_percent = int(self.nav_area.zoom_factor * 100)
        self.zoom_label.setText(f"Zoom: {zoom_percent}%")
    
    def clear_all(self):
        """Limpia todos los nodos"""
        for widget in self.node_widgets.values():
            widget.setParent(None)
        
        self.nodes.clear()
        self.node_widgets.clear()
        self.selected_node = None
        self.info_label.setText("Editor limpiado")

def create_simple_editor(parent=None):
    """Crea un editor simple con navegación"""
    if not PYQT_AVAILABLE:
        return None
    return SimpleNodeEditor(parent)

NODE_EDITOR_AVAILABLE = PYQT_AVAILABLE