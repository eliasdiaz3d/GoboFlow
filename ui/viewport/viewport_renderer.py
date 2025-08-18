"""
Renderizador de viewport para GoboFlow
Renderiza geometrías de nodos en tiempo real
"""

import math
from typing import List, Optional, Tuple, Any, Dict
from pathlib import Path

try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QMutex, QRectF, QPointF
    from PyQt6.QtGui import (
        QPainter, QPen, QBrush, QColor, QPixmap, QPainterPath, 
        QLinearGradient, QRadialGradient, QFont, QFontMetrics
    )
    PYQT_AVAILABLE = True
    
    # SVG opcional
    try:
        from PyQt6.QtSvg import QSvgGenerator
        SVG_AVAILABLE = True
    except ImportError:
        SVG_AVAILABLE = False
        QSvgGenerator = None
        
except ImportError:
    PYQT_AVAILABLE = False
    SVG_AVAILABLE = False
    class QWidget: pass
    class pyqtSignal: pass

from config import RENDER_SETTINGS, RenderQuality, DARK_THEME
from core.node_system import NodeGraph, Node
from nodes.primitives.circle_node import CircleGeometry
from nodes.primitives.rectangle_node import RectangleGeometry

class GeometryRenderer:
    """Renderizador de geometrías individuales"""
    
    @staticmethod
    def render_circle(painter: QPainter, circle: CircleGeometry, render_mode: str = "preview"):
        """Renderiza un círculo"""
        cx, cy = circle.center
        radius = circle.radius
        
        # Configurar pen y brush
        if circle.filled:
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(QPen(QColor(255, 255, 255), 1))
        else:
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            painter.setPen(QPen(QColor(255, 255, 255), 2))
        
        # Dibujar círculo usando QRectF para compatibilidad con PyQt6
        if render_mode == "high_quality":
            # Usar path para mejor calidad
            path = QPainterPath()
            path.addEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))
            painter.drawPath(path)
        else:
            # Dibujo directo para preview usando QRectF
            rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
            painter.drawEllipse(rect)
    
    @staticmethod
    def render_rectangle(painter: QPainter, rectangle: RectangleGeometry, render_mode: str = "preview"):
        """Renderiza un rectángulo"""
        cx, cy = rectangle.center
        width = rectangle.width
        height = rectangle.height
        corner_radius = rectangle.corner_radius
        
        # Configurar pen y brush
        if rectangle.filled:
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(QPen(QColor(255, 255, 255), 1))
        else:
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            painter.setPen(QPen(QColor(255, 255, 255), 2))
        
        # Calcular rectángulo
        x = cx - width / 2
        y = cy - height / 2
        rect = QRectF(x, y, width, height)
        
        # Dibujar rectángulo
        if corner_radius > 0:
            painter.drawRoundedRect(rect, corner_radius, corner_radius)
        else:
            painter.drawRect(rect)
    
    @staticmethod
    def render_geometry(painter: QPainter, geometry: Any, render_mode: str = "preview"):
        """Renderiza cualquier tipo de geometría"""
        if isinstance(geometry, CircleGeometry):
            GeometryRenderer.render_circle(painter, geometry, render_mode)
        elif isinstance(geometry, RectangleGeometry):
            GeometryRenderer.render_rectangle(painter, geometry, render_mode)
        else:
            # Geometría genérica - intentar renderizar usando puntos
            if hasattr(geometry, 'get_polygon_points'):
                points = geometry.get_polygon_points()
                if points:
                    GeometryRenderer.render_polygon(painter, points, getattr(geometry, 'filled', True))
    
    @staticmethod
    def render_polygon(painter: QPainter, points: List[Tuple[float, float]], filled: bool = True):
        """Renderiza un polígono genérico"""
        if len(points) < 2:
            return
        
        # Configurar pen y brush
        if filled:
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(QPen(QColor(255, 255, 255), 1))
        else:
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            painter.setPen(QPen(QColor(255, 255, 255), 2))
        
        # Crear path
        path = QPainterPath()
        path.moveTo(points[0][0], points[0][1])
        
        for x, y in points[1:]:
            path.lineTo(x, y)
        
        if filled:
            path.closeSubpath()
        
        painter.drawPath(path)

class ViewportRenderer(QThread):
    """Renderizador en hilo separado para no bloquear UI"""
    
    render_complete = pyqtSignal(QPixmap)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.render_queue = []
        self.mutex = QMutex()
        self.should_stop = False
        
        # Configuración de renderizado
        self.render_quality = RenderQuality.PREVIEW
        self.canvas_size = (400, 400)
        self.background_color = QColor(0, 0, 0)  # Negro para gobos
        self.zoom_factor = 1.0
        self.center_offset = (0, 0)
        
    def set_render_params(self, quality: RenderQuality, size: Tuple[int, int]):
        """Establece parámetros de renderizado"""
        self.render_quality = quality
        self.canvas_size = size
        
    def add_render_request(self, geometries: List[Any], viewport_bounds: QRectF):
        """Añade una solicitud de renderizado a la cola"""
        self.mutex.lock()
        # Solo mantener la solicitud más reciente
        self.render_queue = [(geometries, viewport_bounds)]
        self.mutex.unlock()
        
        if not self.isRunning():
            self.start()
    
    def run(self):
        """Hilo principal de renderizado"""
        while not self.should_stop:
            self.mutex.lock()
            if not self.render_queue:
                self.mutex.unlock()
                self.msleep(16)  # ~60 FPS
                continue
            
            geometries, viewport_bounds = self.render_queue.pop(0)
            self.mutex.unlock()
            
            # Renderizar
            pixmap = self._render_geometries(geometries, viewport_bounds)
            self.render_complete.emit(pixmap)
            
            self.msleep(16)  # Limite de FPS
    
    def _render_geometries(self, geometries: List[Any], viewport_bounds: QRectF) -> QPixmap:
        """Renderiza las geometrías en un pixmap"""
        width, height = self.canvas_size
        pixmap = QPixmap(width, height)
        pixmap.fill(self.background_color)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        print(f"🎨 Renderizando {len(geometries)} geometrías en {width}x{height}")
        
        # Configurar transformación de viewport
        self._setup_viewport_transform(painter, viewport_bounds, width, height)
        
        # Renderizar cada geometría
        for i, geometry in enumerate(geometries):
            if geometry is not None:
                print(f"   Renderizando geometría {i}: {type(geometry).__name__}")
                try:
                    GeometryRenderer.render_geometry(painter, geometry, "preview")
                    print(f"   ✅ Geometría {i} renderizada")
                except Exception as e:
                    print(f"   ❌ Error renderizando geometría {i}: {e}")
        
        painter.end()
        print(f"🎨 Render completado: pixmap {pixmap.size()}")
        return pixmap
    
    def _setup_viewport_transform(self, painter: QPainter, bounds: QRectF, width: int, height: int):
        """Configura la transformación para ajustar el contenido al viewport"""
        if bounds.width() == 0 or bounds.height() == 0:
            # Bounds por defecto si están vacíos
            bounds = QRectF(-200, -200, 400, 400)
        
        # Calcular escala para ajustar al viewport con margen
        margin = 20
        scale_x = (width - 2 * margin) / bounds.width()
        scale_y = (height - 2 * margin) / bounds.height()
        scale = min(scale_x, scale_y) * self.zoom_factor
        
        # Centrar en el viewport
        center_x = width / 2
        center_y = height / 2
        bounds_center_x = bounds.center().x()
        bounds_center_y = bounds.center().y()
        
        # Aplicar transformaciones
        painter.translate(center_x + self.center_offset[0], center_y + self.center_offset[1])
        painter.scale(scale, scale)
        painter.translate(-bounds_center_x, -bounds_center_y)
    
    def stop_rendering(self):
        """Detiene el hilo de renderizado"""
        self.should_stop = True
        self.wait()

class ViewportWidget(QWidget):
    """Widget de vista previa del gobo"""
    
    # Señales
    zoom_changed = pyqtSignal(float)
    export_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Estado
        self.current_geometries = []
        self.current_pixmap = None
        self.zoom_factor = 1.0
        self.auto_update = True
        
        # Renderizador
        self.renderer = ViewportRenderer()
        self.renderer.render_complete.connect(self._on_render_complete)
        
        # Timer para updates con delay
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._perform_update)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura la interfaz del viewport"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header con controles
        header = self._create_header()
        layout.addWidget(header)
        
        # Área de renderizado
        self.render_area = QFrame()
        self.render_area.setMinimumSize(400, 400)
        self.render_area.setStyleSheet("""
            QFrame {
                background: black;
                border: 2px solid #555;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.render_area)
        
        # Footer con info
        footer = self._create_footer()
        layout.addWidget(footer)
    
    def _create_header(self) -> QWidget:
        """Crea el header con controles"""
        header = QFrame()
        header.setFixedHeight(40)
        header.setStyleSheet("background: #3c3c3c; border-bottom: 1px solid #555;")
        
        layout = QHBoxLayout(header)
        
        # Título
        title = QLabel("👁️ Vista Previa")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Controles de zoom
        zoom_out_btn = QPushButton("🔍-")
        zoom_out_btn.setFixedSize(30, 25)
        zoom_out_btn.clicked.connect(self._zoom_out)
        layout.addWidget(zoom_out_btn)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("color: #ccc; font-size: 11px; margin: 0 5px;")
        self.zoom_label.setMinimumWidth(40)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.zoom_label)
        
        zoom_in_btn = QPushButton("🔍+")
        zoom_in_btn.setFixedSize(30, 25)
        zoom_in_btn.clicked.connect(self._zoom_in)
        layout.addWidget(zoom_in_btn)
        
        # Botón de ajustar
        fit_btn = QPushButton("⌂")
        fit_btn.setFixedSize(30, 25)
        fit_btn.setToolTip("Ajustar a ventana")
        fit_btn.clicked.connect(self._fit_to_window)
        layout.addWidget(fit_btn)
        
        # Botón exportar
        export_btn = QPushButton("📤")
        export_btn.setFixedSize(30, 25)
        export_btn.setToolTip("Exportar gobo")
        export_btn.clicked.connect(self.export_requested.emit)
        layout.addWidget(export_btn)
        
        return header
    
    def _create_footer(self) -> QWidget:
        """Crea el footer con información"""
        footer = QFrame()
        footer.setFixedHeight(30)
        footer.setStyleSheet("background: #2d2d2d; border-top: 1px solid #555;")
        
        layout = QHBoxLayout(footer)
        
        self.info_label = QLabel("Listo para renderizar")
        self.info_label.setStyleSheet("color: #aaa; font-size: 11px;")
        layout.addWidget(self.info_label)
        
        layout.addStretch()
        
        # Toggle auto-update
        self.auto_update_btn = QPushButton("🔄 Auto")
        self.auto_update_btn.setFixedSize(50, 20)
        self.auto_update_btn.setCheckable(True)
        self.auto_update_btn.setChecked(True)
        self.auto_update_btn.toggled.connect(self._toggle_auto_update)
        layout.addWidget(self.auto_update_btn)
        
        return footer
    
    def update_geometries(self, geometries: List[Any]):
        """Actualiza las geometrías a renderizar"""
        self.current_geometries = geometries
        
        if self.auto_update:
            # Delay para evitar updates muy frecuentes
            self.update_timer.start(100)  # 100ms delay
    
    def _perform_update(self):
        """Realiza el update del renderizado"""
        if not self.current_geometries:
            self._show_empty_state()
            return
        
        # Calcular bounds de todas las geometrías
        bounds = self._calculate_bounds(self.current_geometries)
        
        # Solicitar renderizado
        self.renderer.add_render_request(self.current_geometries, bounds)
        
        # Actualizar info
        count = len(self.current_geometries)
        self.info_label.setText(f"Renderizando {count} geometría(s)...")
    
    def _calculate_bounds(self, geometries: List[Any]) -> QRectF:
        """Calcula el bounding box de todas las geometrías"""
        if not geometries:
            return QRectF(-200, -200, 400, 400)
        
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for geom in geometries:
            if hasattr(geom, 'bbox'):
                bbox = geom.bbox  # (min_x, min_y, max_x, max_y)
                min_x = min(min_x, bbox[0])
                min_y = min(min_y, bbox[1])
                max_x = max(max_x, bbox[2])
                max_y = max(max_y, bbox[3])
        
        # Añadir margen
        margin = 50
        return QRectF(min_x - margin, min_y - margin, 
                     max_x - min_x + 2 * margin, max_y - min_y + 2 * margin)
    
    def _on_render_complete(self, pixmap: QPixmap):
        """Se ejecuta cuando se completa el renderizado"""
        self.current_pixmap = pixmap
        self.update()  # Forzar repaint del widget completo
        
        # Actualizar info
        count = len(self.current_geometries)
        self.info_label.setText(f"✅ {count} geometría(s) renderizada(s)")
        print(f"🎨 Render completado: {pixmap.size()}")
    
    def _show_empty_state(self):
        """Muestra estado vacío"""
        self.current_pixmap = None
        self.update()  # Forzar repaint
        self.info_label.setText("Sin geometrías para mostrar")
    
    def paintEvent(self, event):
        """Dibuja el viewport"""
        super().paintEvent(event)
        
        if not self.current_pixmap:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Obtener el rect del render_area relativo a este widget
        area_rect = self.render_area.geometry()
        pixmap_rect = self.current_pixmap.rect()
        
        # Centrar pixmap en el área
        x = area_rect.x() + (area_rect.width() - pixmap_rect.width()) // 2
        y = area_rect.y() + (area_rect.height() - pixmap_rect.height()) // 2
        
        # Asegurar que esté dentro del área
        x = max(area_rect.x(), x)
        y = max(area_rect.y(), y)
        
        painter.drawPixmap(x, y, self.current_pixmap)
        painter.end()
        
        print(f"🖼️ Pixmap dibujado en ({x}, {y}) tamaño {pixmap_rect.size()}")
    
    def _zoom_in(self):
        """Aumenta zoom"""
        self.zoom_factor = min(5.0, self.zoom_factor * 1.25)
        self._update_zoom_display()
        self.renderer.zoom_factor = self.zoom_factor
        self._perform_update()
    
    def _zoom_out(self):
        """Disminuye zoom"""
        self.zoom_factor = max(0.1, self.zoom_factor / 1.25)
        self._update_zoom_display()
        self.renderer.zoom_factor = self.zoom_factor
        self._perform_update()
    
    def _fit_to_window(self):
        """Ajusta zoom para mostrar todo el contenido"""
        self.zoom_factor = 1.0
        self._update_zoom_display()
        self.renderer.zoom_factor = self.zoom_factor
        self._perform_update()
    
    def _update_zoom_display(self):
        """Actualiza el display del zoom"""
        zoom_percent = int(self.zoom_factor * 100)
        self.zoom_label.setText(f"{zoom_percent}%")
        self.zoom_changed.emit(self.zoom_factor)
    
    def _toggle_auto_update(self, enabled: bool):
        """Activa/desactiva auto-update"""
        self.auto_update = enabled
        style = "background: #4CAF50;" if enabled else "background: #666;"
        self.auto_update_btn.setStyleSheet(style)
        
        if enabled:
            self._perform_update()
    
    def export_svg(self, filepath: str, size: Tuple[int, int] = (1024, 1024)):
        """Exporta el gobo como SVG"""
        if not SVG_AVAILABLE:
            print("SVG export no disponible - instala PyQt6 completo")
            return False
            
        if not self.current_geometries:
            return False
        
        try:
            generator = QSvgGenerator()
            generator.setFileName(filepath)
            generator.setSize(size)
            generator.setViewBox(QRectF(0, 0, size[0], size[1]))
            
            painter = QPainter(generator)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Configurar viewport
            bounds = self._calculate_bounds(self.current_geometries)
            self.renderer._setup_viewport_transform(painter, bounds, size[0], size[1])
            
            # Renderizar geometrías
            for geometry in self.current_geometries:
                if geometry is not None:
                    GeometryRenderer.render_geometry(painter, geometry, "high_quality")
            
            painter.end()
            return True
            
        except Exception as e:
            print(f"Error exportando SVG: {e}")
            return False
    
    def closeEvent(self, event):
        """Limpieza al cerrar"""
        self.renderer.stop_rendering()
        super().closeEvent(event)

def create_viewport_widget(parent=None) -> ViewportWidget:
    """Crea un widget de viewport configurado"""
    if not PYQT_AVAILABLE:
        return None
    
    return ViewportWidget(parent)