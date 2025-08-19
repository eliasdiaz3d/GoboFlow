"""
Widget de viewport para vista previa en tiempo real SIN dependencia SVG
Usa QPainter para renderizado directo - más rápido y sin dependencias
"""

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
        QFrame, QSlider, QScrollArea
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
    from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    class QWidget: pass
    class pyqtSignal: 
        def connect(self, *args): pass

class ViewportWidget(QWidget):
    """
    Widget de viewport con vista previa en tiempo real usando QPainter
    """
    
    # Señales
    export_requested = pyqtSignal(str)  # Formato de exportación
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Estado del viewport
        self.current_geometry = None
        self.viewport_size = (1024, 1024)  # Resolución del gobo
        self.show_grid = False
        self.show_info = True
        self.zoom_factor = 1.0
        
        # Configurar UI
        self.init_ui()
        
        # Timer para updates automáticos
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.auto_refresh)
        self.update_timer.start(100)  # Refresh cada 100ms
        
        print("🖼️ Viewport (QPainter) en tiempo real inicializado")
    
    def init_ui(self):
        """Inicializa la interfaz del viewport"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header con controles
        header = self.create_header()
        layout.addWidget(header)
        
        # Área principal con canvas
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
            QPushButton:checked {
                background: #0078d4;
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
        """Crea el área principal con el canvas"""
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
        
        # Widget contenedor para el canvas
        container = QWidget()
        container.setMinimumSize(600, 600)
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Canvas widget
        self.canvas = CanvasWidget()
        self.canvas.setFixedSize(400, 400)  # Tamaño inicial
        container_layout.addWidget(self.canvas)
        
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
            
            # Actualizar canvas
            self.canvas.set_geometry(geometry_data)
            self.canvas.set_grid(self.show_grid)
            self.canvas.set_info(self.show_info)
            self.canvas.set_zoom(self.zoom_factor)
            self.canvas.update()
            
            # Actualizar información
            if geometry_data:
                self.update_geometry_info(geometry_data)
                self.status_label.setText("Estado: Actualizado")
                print(f"🔄 Viewport actualizado con nueva geometría")
            else:
                self.geometry_info_label.setText("Geometría: Ninguna")
                self.status_label.setText("Estado: Sin geometría")
                
        except Exception as e:
            print(f"❌ Error actualizando preview: {e}")
            self.status_label.setText(f"Estado: Error - {e}")
    
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
        if hasattr(self, 'canvas'):
            self.canvas.set_grid(show)
            self.canvas.update()
        print(f"🔳 Grid {'activado' if show else 'desactivado'}")
    
    def toggle_info(self, show: bool):
        """Activa/desactiva la información"""
        self.show_info = show
        if hasattr(self, 'canvas'):
            self.canvas.set_info(show)
            self.canvas.update()
        print(f"ℹ️ Info {'activada' if show else 'desactivada'}")
    
    def on_zoom_changed(self, value):
        """Maneja cambios en el zoom"""
        zoom_percent = value
        self.zoom_factor = value / 100.0
        self.zoom_value_label.setText(f"{zoom_percent}%")
        
        # Calcular nuevo tamaño del canvas
        base_size = 400
        new_size = int(base_size * self.zoom_factor)
        
        self.canvas.setFixedSize(new_size, new_size)
        self.canvas.set_zoom(self.zoom_factor)
        self.canvas.update()
        
        print(f"🔍 Zoom: {zoom_percent}%")
    
    def auto_refresh(self):
        """Refresh automático (placeholder por ahora)"""
        pass
    
    def get_current_svg(self) -> str:
        """Obtiene el SVG actual para exportación"""
        return self.generate_svg_from_current_geometry()
    
    def generate_svg_from_current_geometry(self) -> str:
        """Genera SVG desde la geometría actual"""
        try:
            if not self.current_geometry:
                return self.get_default_svg()
            
            # Grid
            grid_svg = self.generate_grid_svg() if self.show_grid else ""
            
            # Geometría principal
            geometry_svg = self.generate_geometry_svg(self.current_geometry)
            
            # Información
            info_svg = self.generate_info_svg() if self.show_info else ""
            
            # SVG completo
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{self.viewport_size[0]}" height="{self.viewport_size[1]}" 
     viewBox="0 0 {self.viewport_size[0]} {self.viewport_size[1]}"
     style="background: black;">
  
  {grid_svg}
  {geometry_svg}
  {info_svg}
  
</svg>'''
            
            return svg_content
            
        except Exception as e:
            print(f"❌ Error generando SVG: {e}")
            return self.get_error_svg(str(e))
    
    def generate_geometry_svg(self, geometry_data) -> str:
        """Genera SVG de la geometría"""
        if hasattr(geometry_data, 'radius'):
            # Círculo
            center = getattr(geometry_data, 'center', (0, 0))
            if isinstance(center, (list, tuple)) and len(center) >= 2:
                cx = 512 + center[0]  # Centrar en el viewport
                cy = 512 + center[1]
            else:
                cx, cy = 512, 512
            
            radius = geometry_data.radius
            return f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="white" opacity="0.8"/>'
        
        return '<circle cx="512" cy="512" r="100" fill="white" opacity="0.5"/>'
    
    def generate_grid_svg(self) -> str:
        """Genera grid SVG"""
        lines = []
        grid_size = 64
        width, height = self.viewport_size
        
        for x in range(0, width + 1, grid_size):
            opacity = "0.3" if x % (grid_size * 4) == 0 else "0.1"
            lines.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="white" stroke-width="1" opacity="{opacity}"/>')
        
        for y in range(0, height + 1, grid_size):
            opacity = "0.3" if y % (grid_size * 4) == 0 else "0.1"
            lines.append(f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="white" stroke-width="1" opacity="{opacity}"/>')
        
        return "\n  ".join(lines)
    
    def generate_info_svg(self) -> str:
        """Genera información SVG"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        info_text = "GoboFlow"
        if self.current_geometry and hasattr(self.current_geometry, 'radius'):
            info_text = f"Radio: {self.current_geometry.radius:.1f}px"
        
        return f'''
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
    
    def get_default_svg(self) -> str:
        """SVG por defecto"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{self.viewport_size[0]}" height="{self.viewport_size[1]}" 
     viewBox="0 0 {self.viewport_size[0]} {self.viewport_size[1]}"
     style="background: black;">
  
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
  
</svg>'''
    
    def get_error_svg(self, error: str) -> str:
        """SVG de error"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{self.viewport_size[0]}" height="{self.viewport_size[1]}" 
     viewBox="0 0 {self.viewport_size[0]} {self.viewport_size[1]}"
     style="background: black;">
  
  <g opacity="0.8">
    <circle cx="512" cy="512" r="100" fill="none" stroke="red" stroke-width="3"/>
    <text x="512" y="480" fill="red" font-family="Arial" font-size="20" text-anchor="middle" font-weight="bold">
      Error
    </text>
    <text x="512" y="510" fill="#ff6666" font-family="Arial" font-size="12" text-anchor="middle">
      {error[:50]}
    </text>
  </g>
  
</svg>'''

class CanvasWidget(QWidget):
    """Widget canvas que dibuja usando QPainter"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.geometry_data = None
        self.show_grid = False
        self.show_info = True
        self.zoom_factor = 1.0
        
        self.setStyleSheet("background: black; border: 2px solid #666; border-radius: 4px;")
    
    def set_geometry(self, geometry_data):
        self.geometry_data = geometry_data
    
    def set_grid(self, show):
        self.show_grid = show
    
    def set_info(self, show):
        self.show_info = show
    
    def set_zoom(self, zoom):
        self.zoom_factor = zoom
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fondo negro
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        
        # Calcular centro
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Dibujar grid si está activado
        if self.show_grid:
            self.draw_grid(painter)
        
        # Dibujar geometría
        if self.geometry_data:
            self.draw_geometry(painter, center_x, center_y)
        else:
            self.draw_placeholder(painter, center_x, center_y)
        
        # Dibujar información
        if self.show_info:
            self.draw_info(painter)
    
    def draw_grid(self, painter):
        """Dibuja la grilla"""
        pen = QPen(QColor(60, 60, 60), 1)
        painter.setPen(pen)
        
        grid_size = int(20 * self.zoom_factor)
        if grid_size < 5:
            grid_size = 5
        
        # Líneas verticales
        x = 0
        while x < self.width():
            painter.drawLine(x, 0, x, self.height())
            x += grid_size
        
        # Líneas horizontales
        y = 0
        while y < self.height():
            painter.drawLine(0, y, self.width(), y)
            y += grid_size
    
    def draw_geometry(self, painter, center_x, center_y):
        """Dibuja la geometría"""
        if hasattr(self.geometry_data, 'radius'):
            # Dibujar círculo
            radius = self.geometry_data.radius * self.zoom_factor
            
            # Centro del círculo
            offset_x = offset_y = 0
            if hasattr(self.geometry_data, 'center'):
                center = self.geometry_data.center
                if isinstance(center, (list, tuple)) and len(center) >= 2:
                    offset_x = center[0] * self.zoom_factor
                    offset_y = center[1] * self.zoom_factor
            elif hasattr(self.geometry_data, 'circle_center'):
                center = self.geometry_data.circle_center
                if isinstance(center, (list, tuple)) and len(center) >= 2:
                    # Para circle_center, usar coordenadas directamente sin offset
                    center_x = center[0] * self.zoom_factor * self.width() / 1024
                    center_y = center[1] * self.zoom_factor * self.height() / 1024
                    offset_x = offset_y = 0
            
            # Configurar estilo
            pen = QPen(QColor(255, 255, 255), 2)
            brush = QBrush(QColor(255, 255, 255, 200))
            painter.setPen(pen)
            painter.setBrush(brush)
            
            # Dibujar círculo
            circle_x = center_x + offset_x - radius
            circle_y = center_y + offset_y - radius
            painter.drawEllipse(int(circle_x), int(circle_y), int(radius * 2), int(radius * 2))
            
        else:
            # Geometría desconocida - dibujar placeholder
            self.draw_placeholder(painter, center_x, center_y)
    
    def draw_placeholder(self, painter, center_x, center_y):
        """Dibuja placeholder cuando no hay geometría"""
        pen = QPen(QColor(100, 100, 100), 2)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        # Círculo punteado
        radius = int(100 * self.zoom_factor)
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # Texto
        if self.zoom_factor >= 0.5:  # Solo mostrar texto si hay suficiente zoom
            painter.setPen(QPen(QColor(150, 150, 150), 1))
            font = QFont("Arial", max(8, int(16 * self.zoom_factor)), QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(center_x - 50, center_y, "GoboFlow")
    
    def draw_info(self, painter):
        """Dibuja información superpuesta"""
        if not self.geometry_data:
            return
        
        # Fondo para el texto
        info_rect = QRectF(10, 10, 200, 60)
        painter.fillRect(info_rect, QColor(0, 0, 0, 180))
        
        # Texto de información
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)
        
        y_pos = 25
        painter.drawText(15, y_pos, "GoboFlow")
        
        if hasattr(self.geometry_data, 'radius'):
            y_pos += 15
            painter.drawText(15, y_pos, f"Radio: {self.geometry_data.radius:.1f}px")
            
            if hasattr(self.geometry_data, 'center'):
                center = self.geometry_data.center
                if isinstance(center, (list, tuple)) and len(center) >= 2:
                    y_pos += 15
                    painter.drawText(15, y_pos, f"Centro: ({center[0]:.1f}, {center[1]:.1f})")

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