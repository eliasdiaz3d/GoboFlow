"""
Panel de propiedades interactivo para editar parámetros de nodos
"""

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
        QFrame, QSlider, QSpinBox, QDoubleSpinBox, QCheckBox,
        QLineEdit, QComboBox, QColorDialog, QGroupBox, QScrollArea
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QColor, QFont, QPalette
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    class QWidget: pass
    class pyqtSignal: 
        def connect(self, *args): pass

class ParameterWidget(QWidget):
    """Widget base para parámetros editables"""
    
    value_changed = pyqtSignal(str, object)  # (parameter_name, new_value)
    
    def __init__(self, param_name: str, param_type: str, default_value, parent=None):
        super().__init__(parent)
        self.param_name = param_name
        self.param_type = param_type
        self.current_value = default_value
        
        self.setStyleSheet("""
            QWidget {
                background: transparent;
            }
            QLabel {
                color: #ccc;
                font-size: 11px;
                margin: 2px 0;
            }
            QSlider::groove:horizontal {
                background: #555;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #0078d4;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSpinBox, QDoubleSpinBox, QLineEdit {
                background: #404040;
                border: 1px solid #606060;
                border-radius: 3px;
                padding: 4px;
                color: white;
                font-size: 11px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {
                border-color: #0078d4;
            }
            QPushButton {
                background: #505050;
                border: 1px solid #606060;
                border-radius: 3px;
                padding: 4px 8px;
                color: white;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #606060;
            }
        """)

class NumberParameterWidget(ParameterWidget):
    """Widget para parámetros numéricos"""
    
    def __init__(self, param_name: str, default_value: float = 0.0, 
                 min_val: float = -999, max_val: float = 999, parent=None):
        super().__init__(param_name, "number", default_value, parent)
        
        self.min_val = min_val
        self.max_val = max_val
        
        self.init_ui()
        self.set_value(default_value)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(4)
        
        # Etiqueta
        self.label = QLabel(self.param_name.replace('_', ' ').title())
        layout.addWidget(self.label)
        
        # Layout horizontal para controles
        controls_layout = QHBoxLayout()
        
        # Spin box para valor exacto
        self.spin_box = QDoubleSpinBox()
        self.spin_box.setRange(self.min_val, self.max_val)
        self.spin_box.setDecimals(2)
        self.spin_box.setSingleStep(0.1)
        self.spin_box.setMaximumWidth(80)
        self.spin_box.valueChanged.connect(self.on_spin_changed)
        controls_layout.addWidget(self.spin_box)
        
        # Slider para ajuste rápido (si el rango es razonable)
        if self.max_val - self.min_val <= 1000:
            self.slider = QSlider(Qt.Orientation.Horizontal)
            self.slider.setRange(int(self.min_val * 10), int(self.max_val * 10))
            self.slider.valueChanged.connect(self.on_slider_changed)
            controls_layout.addWidget(self.slider)
        else:
            self.slider = None
        
        layout.addLayout(controls_layout)
    
    def set_value(self, value: float):
        """Establece el valor sin emitir señal"""
        self.current_value = value
        
        # Actualizar controles sin emitir señales
        self.spin_box.blockSignals(True)
        self.spin_box.setValue(value)
        self.spin_box.blockSignals(False)
        
        if self.slider:
            self.slider.blockSignals(True)
            self.slider.setValue(int(value * 10))
            self.slider.blockSignals(False)
    
    def on_spin_changed(self, value: float):
        """Maneja cambios en el spin box"""
        self.current_value = value
        
        # Actualizar slider
        if self.slider:
            self.slider.blockSignals(True)
            self.slider.setValue(int(value * 10))
            self.slider.blockSignals(False)
        
        self.value_changed.emit(self.param_name, value)
    
    def on_slider_changed(self, value: int):
        """Maneja cambios en el slider"""
        float_value = value / 10.0
        self.current_value = float_value
        
        # Actualizar spin box
        self.spin_box.blockSignals(True)
        self.spin_box.setValue(float_value)
        self.spin_box.blockSignals(False)
        
        self.value_changed.emit(self.param_name, float_value)

class VectorParameterWidget(ParameterWidget):
    """Widget para parámetros de vector"""
    
    def __init__(self, param_name: str, default_value: list = [0.0, 0.0], parent=None):
        super().__init__(param_name, "vector", default_value, parent)
        self.init_ui()
        self.set_value(default_value)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(4)
        
        # Etiqueta
        self.label = QLabel(self.param_name.replace('_', ' ').title())
        layout.addWidget(self.label)
        
        # Controles X e Y
        xy_layout = QHBoxLayout()
        
        # X
        x_layout = QVBoxLayout()
        x_label = QLabel("X:")
        x_layout.addWidget(x_label)
        
        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(-9999, 9999)
        self.x_spin.setDecimals(1)
        self.x_spin.valueChanged.connect(self.on_value_changed)
        x_layout.addWidget(self.x_spin)
        
        xy_layout.addLayout(x_layout)
        
        # Y
        y_layout = QVBoxLayout()
        y_label = QLabel("Y:")
        y_layout.addWidget(y_label)
        
        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(-9999, 9999)
        self.y_spin.setDecimals(1)
        self.y_spin.valueChanged.connect(self.on_value_changed)
        y_layout.addWidget(self.y_spin)
        
        xy_layout.addLayout(y_layout)
        
        layout.addLayout(xy_layout)
    
    def set_value(self, value: list):
        """Establece el valor del vector"""
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            self.current_value = [float(value[0]), float(value[1])]
        else:
            self.current_value = [0.0, 0.0]
        
        self.x_spin.blockSignals(True)
        self.y_spin.blockSignals(True)
        
        self.x_spin.setValue(self.current_value[0])
        self.y_spin.setValue(self.current_value[1])
        
        self.x_spin.blockSignals(False)
        self.y_spin.blockSignals(False)
    
    def on_value_changed(self):
        """Maneja cambios en cualquier componente"""
        self.current_value = [self.x_spin.value(), self.y_spin.value()]
        self.value_changed.emit(self.param_name, self.current_value)

class BooleanParameterWidget(ParameterWidget):
    """Widget para parámetros booleanos"""
    
    def __init__(self, param_name: str, default_value: bool = False, parent=None):
        super().__init__(param_name, "boolean", default_value, parent)
        self.init_ui()
        self.set_value(default_value)
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(8)
        
        # Checkbox
        self.checkbox = QCheckBox(self.param_name.replace('_', ' ').title())
        self.checkbox.setStyleSheet("""
            QCheckBox {
                color: #ccc;
                font-size: 11px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #606060;
                border-radius: 3px;
                background: #404040;
            }
            QCheckBox::indicator:checked {
                background: #0078d4;
                border-color: #0078d4;
            }
        """)
        self.checkbox.stateChanged.connect(self.on_state_changed)
        layout.addWidget(self.checkbox)
        
        layout.addStretch()
    
    def set_value(self, value: bool):
        """Establece el valor del checkbox"""
        self.current_value = bool(value)
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(self.current_value)
        self.checkbox.blockSignals(False)
    
    def on_state_changed(self, state):
        """Maneja cambios en el checkbox"""
        self.current_value = state == Qt.CheckState.Checked.value
        self.value_changed.emit(self.param_name, self.current_value)

class ColorParameterWidget(ParameterWidget):
    """Widget para parámetros de color"""
    
    def __init__(self, param_name: str, default_value: dict = None, parent=None):
        if default_value is None:
            default_value = {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0}
        super().__init__(param_name, "color", default_value, parent)
        self.init_ui()
        self.set_value(default_value)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(4)
        
        # Etiqueta
        self.label = QLabel(self.param_name.replace('_', ' ').title())
        layout.addWidget(self.label)
        
        # Layout horizontal para controles
        controls_layout = QHBoxLayout()
        
        # Botón de color
        self.color_button = QPushButton()
        self.color_button.setFixedSize(40, 25)
        self.color_button.clicked.connect(self.open_color_dialog)
        controls_layout.addWidget(self.color_button)
        
        # Etiqueta con valor hex
        self.hex_label = QLabel("#FFFFFF")
        self.hex_label.setStyleSheet("font-family: monospace; font-size: 10px;")
        controls_layout.addWidget(self.hex_label)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
    
    def set_value(self, value: dict):
        """Establece el valor del color"""
        if isinstance(value, dict) and 'r' in value:
            self.current_value = value
        else:
            self.current_value = {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0}
        
        self.update_color_display()
    
    def update_color_display(self):
        """Actualiza la visualización del color"""
        r = int(self.current_value['r'] * 255)
        g = int(self.current_value['g'] * 255)
        b = int(self.current_value['b'] * 255)
        
        # Actualizar botón de color
        self.color_button.setStyleSheet(f"""
            QPushButton {{
                background: rgb({r}, {g}, {b});
                border: 1px solid #606060;
                border-radius: 3px;
            }}
        """)
        
        # Actualizar etiqueta hex
        hex_color = f"#{r:02X}{g:02X}{b:02X}"
        self.hex_label.setText(hex_color)
    
    def open_color_dialog(self):
        """Abre el diálogo de selección de color"""
        r = int(self.current_value['r'] * 255)
        g = int(self.current_value['g'] * 255)
        b = int(self.current_value['b'] * 255)
        
        initial_color = QColor(r, g, b)
        color = QColorDialog.getColor(initial_color, self, f"Seleccionar {self.param_name}")
        
        if color.isValid():
            self.current_value = {
                'r': color.red() / 255.0,
                'g': color.green() / 255.0,
                'b': color.blue() / 255.0,
                'a': self.current_value.get('a', 1.0)
            }
            
            self.update_color_display()
            self.value_changed.emit(self.param_name, self.current_value)

class StringParameterWidget(ParameterWidget):
    """Widget para parámetros de texto"""
    
    def __init__(self, param_name: str, default_value: str = "", parent=None):
        super().__init__(param_name, "string", default_value, parent)
        self.init_ui()
        self.set_value(default_value)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(4)
        
        # Etiqueta
        self.label = QLabel(self.param_name.replace('_', ' ').title())
        layout.addWidget(self.label)
        
        # Campo de texto
        self.line_edit = QLineEdit()
        self.line_edit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.line_edit)
    
    def set_value(self, value: str):
        """Establece el valor del texto"""
        self.current_value = str(value)
        self.line_edit.blockSignals(True)
        self.line_edit.setText(self.current_value)
        self.line_edit.blockSignals(False)
    
    def on_text_changed(self, text: str):
        """Maneja cambios en el texto"""
        self.current_value = text
        self.value_changed.emit(self.param_name, text)

class ChoiceParameterWidget(ParameterWidget):
    """Widget para parámetros de selección (dropdown)"""
    
    def __init__(self, param_name: str, choices: list, default_value: str = "", parent=None):
        self.choices = choices
        super().__init__(param_name, "choice", default_value, parent)
        self.init_ui()
        self.set_value(default_value)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(4)
        
        # Etiqueta
        self.label = QLabel(self.param_name.replace('_', ' ').title())
        layout.addWidget(self.label)
        
        # ComboBox
        self.combo_box = QComboBox()
        self.combo_box.addItems(self.choices)
        self.combo_box.setStyleSheet("""
            QComboBox {
                background: #404040;
                border: 1px solid #606060;
                border-radius: 3px;
                padding: 4px;
                color: white;
                font-size: 11px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
            }
            QComboBox QAbstractItemView {
                background: #404040;
                border: 1px solid #606060;
                color: white;
                selection-background-color: #0078d4;
            }
        """)
        self.combo_box.currentTextChanged.connect(self.on_selection_changed)
        layout.addWidget(self.combo_box)
    
    def set_value(self, value: str):
        """Establece el valor seleccionado"""
        self.current_value = str(value)
        self.combo_box.blockSignals(True)
        
        index = self.combo_box.findText(self.current_value)
        if index >= 0:
            self.combo_box.setCurrentIndex(index)
        
        self.combo_box.blockSignals(False)
    
    def on_selection_changed(self, text: str):
        """Maneja cambios en la selección"""
        self.current_value = text
        self.value_changed.emit(self.param_name, text)

class PropertiesPanel(QWidget):
    """
    Panel principal de propiedades que combina todos los widgets de parámetros
    """
    
    # Señales
    parameter_changed = pyqtSignal(object, str, object)  # (node, param_name, new_value)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_node = None
        self.parameter_widgets = {}
        
        self.init_ui()
        
        print("🎛️ Panel de propiedades interactivo inicializado")
    
    def init_ui(self):
        """Inicializa la interfaz del panel"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(35)
        header.setStyleSheet("""
            QFrame {
                background: #404040;
                border-bottom: 1px solid #555;
            }
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 8px;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("⚙️ Propiedades")
        header_layout.addWidget(title)
        
        layout.addWidget(header)
        
        # Área de scroll para parámetros
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: #353535;
                border: none;
            }
            QScrollBar:vertical {
                background: #2b2b2b;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666;
            }
        """)
        
        # Widget contenedor para parámetros
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(8)
        
        # Mensaje por defecto
        self.default_message = QLabel("Selecciona un nodo para ver sus propiedades")
        self.default_message.setWordWrap(True)
        self.default_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.default_message.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 12px;
                padding: 20px;
                background: transparent;
            }
        """)
        self.content_layout.addWidget(self.default_message)
        
        self.content_layout.addStretch()
        
        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)
    
    def set_node(self, node):
        """Establece el nodo actual y genera sus controles de propiedades"""
        if self.current_node == node:
            return
        
        self.current_node = node
        self.clear_parameters()
        
        if node is None:
            self.show_default_message()
            return
        
        self.generate_node_parameters(node)
    
    def clear_parameters(self):
        """Limpia todos los widgets de parámetros"""
        for widget in self.parameter_widgets.values():
            widget.setParent(None)
        
        self.parameter_widgets.clear()
        
        # Limpiar layout
        while self.content_layout.count() > 0:
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
    
    def show_default_message(self):
        """Muestra el mensaje por defecto"""
        self.content_layout.addWidget(self.default_message)
        self.content_layout.addStretch()
    
    def generate_node_parameters(self, node):
        """Genera los controles de parámetros para un nodo"""
        try:
            # Información del nodo
            self.add_node_info_section(node)
            
            # Separador
            self.add_separator()
            
            # Parámetros editables
            self.add_editable_parameters_section(node)
            
            # Información de sockets
            self.add_separator()
            self.add_sockets_info_section(node)
            
            # Stretch al final
            self.content_layout.addStretch()
            
        except Exception as e:
            error_label = QLabel(f"Error generando propiedades: {e}")
            error_label.setStyleSheet("color: #ff6666; font-size: 11px;")
            self.content_layout.addWidget(error_label)
            print(f"❌ Error en generate_node_parameters: {e}")
    
    def add_node_info_section(self, node):
        """Añade sección de información del nodo"""
        # Grupo de información
        info_group = QGroupBox("📋 Información del Nodo")
        info_group.setStyleSheet("""
            QGroupBox {
                color: #ccc;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(4)
        
        # Título del nodo (editable)
        title_widget = StringParameterWidget("title", node.title)
        title_widget.value_changed.connect(lambda name, value: self.on_title_changed(value))
        info_layout.addWidget(title_widget)
        
        # Tipo de nodo
        type_label = QLabel(f"Tipo: {getattr(node, 'NODE_TYPE', 'unknown')}")
        type_label.setStyleSheet("color: #aaa; font-size: 10px; margin: 2px;")
        info_layout.addWidget(type_label)
        
        # Categoría
        category_label = QLabel(f"Categoría: {getattr(node, 'NODE_CATEGORY', 'base')}")
        category_label.setStyleSheet("color: #aaa; font-size: 10px; margin: 2px;")
        info_layout.addWidget(category_label)
        
        self.content_layout.addWidget(info_group)
    
    def add_editable_parameters_section(self, node):
        """Añade sección de parámetros editables"""
        # Detectar parámetros editables
        editable_params = self.get_editable_parameters(node)
        
        if not editable_params:
            no_params_label = QLabel("No hay parámetros editables")
            no_params_label.setStyleSheet("color: #888; font-size: 11px; font-style: italic; padding: 10px;")
            self.content_layout.addWidget(no_params_label)
            return
        
        # Grupo de parámetros
        params_group = QGroupBox("🎛️ Parámetros")
        params_group.setStyleSheet("""
            QGroupBox {
                color: #ccc;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        params_layout = QVBoxLayout(params_group)
        params_layout.setSpacing(8)
        
        # Crear widgets para cada parámetro
        for param_name, param_info in editable_params.items():
            widget = self.create_parameter_widget(param_name, param_info, node)
            if widget:
                widget.value_changed.connect(
                    lambda name, value, n=node: self.on_parameter_changed(n, name, value)
                )
                self.parameter_widgets[param_name] = widget
                params_layout.addWidget(widget)
        
        self.content_layout.addWidget(params_group)
    
    def add_sockets_info_section(self, node):
        """Añade información de sockets"""
        sockets_group = QGroupBox("🔌 Conectores")
        sockets_group.setStyleSheet("""
            QGroupBox {
                color: #ccc;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        sockets_layout = QVBoxLayout(sockets_group)
        sockets_layout.setSpacing(2)
        
        # Inputs
        if node.input_sockets:
            input_label = QLabel("🔥 Entradas:")
            input_label.setStyleSheet("color: #4CAF50; font-size: 11px; font-weight: bold; margin: 4px 0 2px 0;")
            sockets_layout.addWidget(input_label)
            
            for name, socket in node.input_sockets.items():
                socket_info = QLabel(f"  • {name} ({socket.socket_type.name})")
                socket_info.setStyleSheet("color: #aaa; font-size: 10px; margin: 1px 0;")
                sockets_layout.addWidget(socket_info)
        
        # Outputs
        if node.output_sockets:
            output_label = QLabel("🔤 Salidas:")
            output_label.setStyleSheet("color: #FF9800; font-size: 11px; font-weight: bold; margin: 4px 0 2px 0;")
            sockets_layout.addWidget(output_label)
            
            for name, socket in node.output_sockets.items():
                socket_info = QLabel(f"  • {name} ({socket.socket_type.name})")
                socket_info.setStyleSheet("color: #aaa; font-size: 10px; margin: 1px 0;")
                sockets_layout.addWidget(socket_info)
        
        self.content_layout.addWidget(sockets_group)
    
    def add_separator(self):
        """Añade un separador visual"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #555; margin: 5px 0;")
        self.content_layout.addWidget(separator)
    
    def get_editable_parameters(self, node) -> dict:
        """Detecta parámetros editables del nodo"""
        params = {}
        
        # Parámetros específicos según el tipo de nodo
        if hasattr(node, 'NODE_TYPE'):
            node_type = node.NODE_TYPE
            
            if node_type == "number_parameter":
                if hasattr(node, 'parameter_value'):
                    params["value"] = {
                        'type': 'number',
                        'current_value': node.parameter_value,
                        'min': 0,
                        'max': 1000
                    }
            
            elif node_type == "circle":
                # Parámetros del nodo círculo
                if hasattr(node, 'input_sockets'):
                    if "radius" in node.input_sockets:
                        socket = node.input_sockets["radius"]
                        params["radius"] = {
                            'type': 'number',
                            'current_value': socket.default_value or 100,
                            'min': 1,
                            'max': 500
                        }
                    
                    if "center" in node.input_sockets:
                        socket = node.input_sockets["center"]
                        params["center"] = {
                            'type': 'vector',
                            'current_value': socket.default_value or [0, 0]
                        }
                    
                    if "segments" in node.input_sockets:
                        socket = node.input_sockets["segments"]
                        params["segments"] = {
                            'type': 'choice',
                            'current_value': str(int(socket.default_value or 32)),
                            'choices': ['8', '16', '32', '64', '128']
                        }
            
            elif node_type == "viewer":
                if hasattr(node, 'input_sockets'):
                    if "opacity" in node.input_sockets:
                        socket = node.input_sockets["opacity"]
                        params["opacity"] = {
                            'type': 'number',
                            'current_value': socket.default_value or 1.0,
                            'min': 0.0,
                            'max': 1.0
                        }
        
        return params
    
    def create_parameter_widget(self, param_name: str, param_info: dict, node) -> ParameterWidget:
        """Crea el widget apropiado para un parámetro"""
        param_type = param_info.get('type', 'string')
        current_value = param_info.get('current_value')
        
        if param_type == 'number':
            min_val = param_info.get('min', -999)
            max_val = param_info.get('max', 999)
            return NumberParameterWidget(param_name, current_value, min_val, max_val)
        
        elif param_type == 'vector':
            return VectorParameterWidget(param_name, current_value)
        
        elif param_type == 'boolean':
            return BooleanParameterWidget(param_name, current_value)
        
        elif param_type == 'color':
            return ColorParameterWidget(param_name, current_value)
        
        elif param_type == 'choice':
            choices = param_info.get('choices', [])
            return ChoiceParameterWidget(param_name, choices, current_value)
        
        else:  # string
            return StringParameterWidget(param_name, str(current_value))
    
    def on_parameter_changed(self, node, param_name: str, new_value):
        """Maneja cambios en parámetros"""
        try:
            # Aplicar el cambio al nodo
            if hasattr(node, 'set_parameter'):
                node.set_parameter(param_name, new_value)
            elif param_name in node.input_sockets:
                # Actualizar valor por defecto del socket
                node.input_sockets[param_name].default_value = new_value
            
            # Marcar el nodo como dirty para recálculo
            node.mark_dirty()
            
            # Emitir señal
            self.parameter_changed.emit(node, param_name, new_value)
            
            print(f"🎛️ Parámetro actualizado: {node.title}.{param_name} = {new_value}")
            
        except Exception as e:
            print(f"❌ Error actualizando parámetro {param_name}: {e}")
    
    def on_title_changed(self, new_title: str):
        """Maneja cambios en el título del nodo"""
        if self.current_node:
            self.current_node.title = new_title
            # La UI del nodo debería actualizarse automáticamente

# Factory function
def create_properties_panel(parent=None) -> PropertiesPanel:
    """Crea un panel de propiedades"""
    if not PYQT_AVAILABLE:
        # Fallback si PyQt6 no está disponible
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
        from PyQt6.QtCore import Qt
        
        fallback = QWidget(parent)
        layout = QVBoxLayout(fallback)
        label = QLabel("Panel de propiedades no disponible\nInstala PyQt6 completamente")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        return fallback
    
    return PropertiesPanel(parent)