"""
Widget de viewport para vista previa SVG en tiempo real
Reemplaza el placeholder actual con funcionalidad real
"""

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
        QFrame, QSizePolicy, QScrollArea, QSlider, QSpinBox
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
    from PyQt6.QtGui import QPainter, QPixmap, QPen, QBrush, QColor, QFont
    from PyQt6.QtSvgWidgets import QSvgWidget
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    class QWidget: pass
    class pyqtSignal: 
        def connect(self, *args): pass

class ViewportWidget(QWidget):
    """
    Widget de viewport con vista previa SVG en tiempo real
    """
    
    # Señales
    export_requested = pyqtSignal(str)  # Formato de exportación
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Estado del viewport
        self.current_svg_content = ""
        self.current_geometry = None
        self.viewport_size = (1024, 1024)  # Resolución del gobo
        self.background_color = "black"
        self.show_grid = False
        self.show_info = True
        
        # Configurar UI
        self.init_ui()
        
        # Timer para updates automáticos
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.auto_refresh)
        self.update_timer.start(100)  # Refresh cada 100ms
        
        # Generar SVG inicial
        self.generate_default_svg()
        
        print("🖼️ Viewport con SVG en tiempo real inicializado")
    
    def init_ui(self):
        """Inicializa la interfaz del viewport"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header con controles
        header = self.create_header()
        layout.addWidget(header)
        
        # Área principal con SVG
        main_area = self.create_main_area()
        layout.addWidget(main_area)
        
        # Footer con información
        footer = self.create_footer()
        layout.addWidget(footer)
    
    def create_header(self) -> QWidget:
        """Crea el header con controles"""
        header = QFrame()
        header.setFixedHeight(40)
        header.setStyleSheet("""
            QFrame {
                background: #404040;
                border-bottom: 1px solid #555;
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
            QLabel {
                color: white;
                font-weight: bold;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Título
        title = QLabel("👁️ Vista Previa")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Controles de vista
        self.grid_btn = QPushButton("🔳")
        self.grid_btn.setCheckable(True)
        self.grid_btn.setToolTip("Mostrar/ocultar grid")
        self.grid_btn.clicked.connect(self.toggle_grid)
        layout.addWidget(self.grid_btn)
        
        self.info_btn = QPushButton("ℹ️")
        self.info_btn.setCheckable(True)
        self.info_btn.setChecked(True)
        self.info_btn.setToolTip("Mostrar/ocultar información")
        self.info_btn.clicked.connect(self.toggle_info)
        layout.addWidget(self.info_btn)
        
        # Botones de exportación
        export_svg_btn = QPushButton("📤 SVG")
        export_svg_btn.clicked.connect(lambda: self.export_requested.emit("svg"))
        layout.addWidget(export_svg_btn)
        
        export_png_btn = QPushButton("📤 PNG")
        export_png_btn.clicked.connect(lambda: self.export_requested.emit("png"))
        layout.addWidget(export_png_btn)
        
        return header
    
    def create_main_area(self) -> QWidget:
        """Crea el área principal con el SVG"""
        # Contenedor con scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: #2a2a2a;
                border: none;
            }
        """)
        
        # Widget contenedor para el SVG
        container = QWidget()
        container.setMinimumSize(600, 600)
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Widget SVG
        self.svg_widget = QSvgWidget()
        self.svg_widget.setFixedSize(400, 400)  # Tamaño inicial
        self.svg_widget.setStyleSheet("""
            QSvgWidget {
                background: black;
                border: 2px solid #666;
                border-radius: 4px;
            }
        """)
        
        container_layout.addWidget(self.svg_widget)
        
        scroll_area.setWidget(container)
        return scroll_area
    
    def create_footer(self) -> QWidget:
        """Crea el footer con información"""
        footer = QFrame()
        footer.setFixedHeight(60)
        footer.setStyleSheet("""
            QFrame {
                background: #353535;
                border-top: 1px solid #555;
            }
            QLabel {
                color: #ccc;
                font-size: 11px;
                padding: 2px;
            }
        """)
        
        layout = QVBoxLayout(footer)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Información del gobo
        info_layout = QHBoxLayout()
        
        self.resolution_label = QLabel("Resolución: 1024×1024")
        info_layout.addWidget(self.resolution_label)
        
        self.geometry_info_label = QLabel("Geometría: Ninguna")
        info_layout.addWidget(self.geometry_info_label)
        
        info_layout.addStretch()
        
        self.status_label = QLabel("Estado: Listo")
        info_layout.addWidget(self.status_label)
        
        layout.addLayout(info_layout)
        
        # Controles de zoom
        zoom_layout = QHBoxLayout()
        
        zoom_label = QLabel("Zoom:")
        zoom_layout.addWidget(zoom_label)
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(25, 200)  # 25% a 200%
        self.zoom_slider.setValue(100)
        self.zoom_slider.setMaximumWidth(150)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        zoom_layout.addWidget(self.zoom_slider)
        
        self.zoom_value_label = QLabel("100%")
        zoom_layout.addWidget(self.zoom_value_label)
        
        zoom_layout.addStretch()
        
        layout.addLayout(zoom_layout)
        
        return footer
    
    def update_preview(self, geometry_data):
        """Actualiza la vista previa con nueva geometría"""
        try:
            self.current_geometry = geometry_data
            
            if geometry_data is None:
                self.generate_default_svg()
                self.geometry_info_label.setText("Geometría: Ninguna")
                return
            
            # Generar SVG desde la geometría
            svg_content = self.generate_svg_from_geometry(geometry_data)
            
            if svg_content:
                self.current_svg_content = svg_content
                
                # Cargar en el widget SVG
                self.svg_widget.load(svg_content.encode('utf-8'))
                
                # Actualizar información
                self.update_geometry_info(geometry_data)
                self.status_label.setText("Estado: Actualizado")
            else:
                self.generate_default_svg()
                
        except Exception as e:
            print(f"❌ Error actualizando preview: {e}")
            self.status_label.setText(f"Estado: Error - {e}")
            self.generate_default_svg()
    
    def generate_svg_from_geometry(self, geometry_data) -> str:
        """Genera contenido SVG desde datos de geometría"""
        try:
            # Determinar tipo de geometría
            if hasattr(geometry_data, 'get_svg_path'):
                # Geometría con método SVG
                svg_path = geometry_data.get_svg_path()
                geometry_type = getattr(geometry_data, 'geometry_type', 'unknown')
                
                # Información adicional
                info_text = ""
                if hasattr(geometry_data, 'radius'):
                    info_text = f"Radio: {geometry_data.radius:.1f}px"
                elif hasattr(geometry_data, 'width'):
                    info_text = f"Tamaño: {geometry_data.width:.1f}×{geometry_data.height:.1f}px"
                
            elif isinstance(geometry_data, dict) and 'type' in geometry_data:
                # Geometría como diccionario
                if geometry_data['type'] == 'circle':
                    center = geometry_data.get('center', (512, 512))
                    radius = geometry_data.get('radius', 100)
                    svg_path = f'<circle cx="{center[0]}" cy="{center[1]}" r="{radius}" fill="white" opacity="0.8"/>'
                    info_text = f"Radio: {radius:.1f}px"
                    geometry_type = "circle"
                else:
                    svg_path = '<circle cx="512" cy="512" r="50" fill="white" opacity="0.5"/>'
                    info_text = "Geometría desconocida"
                    geometry_type = "unknown"
            else:
                # Fallback: círculo simple
                svg_path = '<circle cx="512" cy="512" r="100" fill="white" opacity="0.8"/>'
                info_text = "Geometría básica"
                geometry_type = "basic"
            
            # Construir SVG completo
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{self.viewport_size[0]}" height="{self.viewport_size[1]}" 
     viewBox="0 0 {self.viewport_size[0]} {self.viewport_size[1]}"
     style="background: {self.background_color};">
  
  <!-- Grid de referencia -->
  {self.generate_grid_svg() if self.show_grid else ""}
  
  <!-- Geometría principal -->
  {svg_path}
  
  <!-- Información del gobo -->
  {self.generate_info_svg(info_text) if self.show_info else ""}
  
</svg>'''
            
            return svg_content
            
        except Exception as e:
            print(f"❌ Error generando SVG: {e}")
            return self.get_error_svg(str(e))
    
    def generate_grid_svg(self) -> str:
        """Genera grid de referencia en SVG"""
        grid_size = 64  # Tamaño de la grilla
        width, height = self.viewport_size
        
        lines = []
        
        # Líneas verticales
        for x in range(0, width + 1, grid_size):
            opacity = "0.3" if x % (grid_size * 4) == 0 else "0.1"
            lines.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="white" stroke-width="1" opacity="{opacity}"/>')
        
        # Líneas horizontales
        for y in range(0, height + 1, grid_size):
            opacity = "0.3" if y % (grid_size * 4) == 0 else "0.1"
            lines.append(f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="white" stroke-width="1" opacity="{opacity}"/>')
        
        return "\n  ".join(lines)
    
    def generate_info_svg(self, info_text: str) -> str:
        """Genera información superpuesta en el SVG"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        return f'''
  <!-- Información del gobo -->
  <g opacity="0.8">
    <rect x="10" y="10" width="300" height="80" fill="black" opacity="0.7" rx="5"/>
    <text x="20" y="30" fill="white" font-family="Arial" font-size="14" font-weight="bold">
      GoboFlow v0.1.0
    </text>
    <text x="20" y="50" fill="#ccc" font-family="Arial" font-size="12">
      {info_text}
    </text>
    <text x="20" y="70" fill="#aaa" font-family="Arial" font-size="10">
      Generado: {timestamp}
    </text>
  </g>'''
    
    def generate_default_svg(self):
        """Genera SVG por defecto cuando no hay geometría"""
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{self.viewport_size[0]}" height="{self.viewport_size[1]}" 
     viewBox="0 0 {self.viewport_size[0]} {self.viewport_size[1]}"
     style="background: {self.background_color};">
  
  <!-- Mensaje por defecto -->
  <g opacity="0.6">
    <circle cx="512" cy="512" r="200" fill="none" stroke="white" stroke-width="2" stroke-dasharray="10,5"/>
    <text x="512" y="480" fill="white" font-family="Arial" font-size="24" text-anchor="middle" font-weight="bold">
      GoboFlow
    </text>
    <text x="512" y="510" fill="#ccc" font-family="Arial" font-size="16" text-anchor="middle">
      Editor de Gobos
    </text>
    <text x="512" y="540" fill="#aaa" font-family="Arial" font-size="12" text-anchor="middle">
      Conecta nodos para generar geometría
    </text>
  </g>
  
  {self.generate_grid_svg() if self.show_grid else ""}
  
</svg>'''
        
        self.current_svg_content = svg_content
        self.svg_widget.load(svg_content.encode('utf-8'))
    
    def get_error_svg(self, error_message: str) -> str:
        """Genera SVG de error"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{self.viewport_size[0]}" height="{self.viewport_size[1]}" 
     viewBox="0 0 {self.viewport_size[0]} {self.viewport_size[1]}"
     style="background: {self.background_color};">
  
  <g opacity="0.8">
    <circle cx="512" cy="512" r="100" fill="none" stroke="red" stroke-width="3"/>
    <text x="512" y="400" fill="red" font-family="Arial" font-size="20" text-anchor="middle" font-weight="bold">
      Error
    </text>
    <text x="512" y="430" fill="#ff6666" font-family="Arial" font-size="12" text-anchor="middle">
      {error_message[:50]}
    </text>
  </g>
  
</svg>'''
    
    def update_geometry_info(self, geometry_data):
        """Actualiza la información de geometría en el footer"""
        try:
            if hasattr(geometry_data, 'geometry_type'):
                geo_type = geometry_data.geometry_type
            elif isinstance(geometry_data, dict):
                geo_type = geometry_data.get('type', 'unknown')
            else:
                geo_type = type(geometry_data).__name__
            
            # Información específica según el tipo
            if hasattr(geometry_data, 'radius'):
                info = f"Tipo: {geo_type} | Radio: {geometry_data.radius:.1f}"
            elif hasattr(geometry_data, 'width'):
                info = f"Tipo: {geo_type} | {geometry_data.width:.1f}×{geometry_data.height:.1f}"
            else:
                info = f"Tipo: {geo_type}"
            
            self.geometry_info_label.setText(f"Geometría: {info}")
            
        except Exception as e:
            self.geometry_info_label.setText(f"Geometría: Error - {e}")
    
    def toggle_grid(self, show: bool):
        """Activa/desactiva la grilla"""
        self.show_grid = show
        if self.current_geometry:
            self.update_preview(self.current_geometry)
        else:
            self.generate_default_svg()
    
    def toggle_info(self, show: bool):
        """Activa/desactiva la información"""
        self.show_info = show
        if self.current_geometry:
            self.update_preview(self.current_geometry)
        else:
            self.generate_default_svg()
    
    def on_zoom_changed(self, value):
        """Maneja cambios en el zoom"""
        zoom_percent = value
        self.zoom_value_label.setText(f"{zoom_percent}%")
        
        # Calcular nuevo tamaño
        base_size = 400
        new_size = int(base_size * zoom_percent / 100)
        
        self.svg_widget.setFixedSize(new_size, new_size)
    
    def auto_refresh(self):
        """Refresh automático (placeholder por ahora)"""
        # En el futuro aquí podríamos detectar cambios automáticamente
        pass
    
    def get_current_svg(self) -> str:
        """Obtiene el SVG actual para exportación"""
        return self.current_svg_content
    
    def export_current_view(self, format_type: str = "svg") -> str:
        """Exporta la vista actual"""
        try:
            if format_type.lower() == "svg":
                return self.current_svg_content
            elif format_type.lower() == "png":
                # TODO: Implementar conversión SVG -> PNG
                return "PNG export not implemented yet"
            else:
                return f"Format {format_type} not supported"
        except Exception as e:
            return f"Export error: {e}"

# Factory function
def create_viewport_widget(parent=None) -> ViewportWidget:
    """Crea un widget de viewport"""
    if not PYQT_AVAILABLE:
        # Fallback si PyQt6 no está disponible
        fallback = QWidget(parent)
        layout = QVBoxLayout(fallback)
        label = QLabel("Viewport no disponible\nInstala PyQt6 completamente")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        return fallback
    
    return ViewportWidget(parent)