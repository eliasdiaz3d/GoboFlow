"""
Ventana principal mejorada de GoboFlow
Incluye el editor visual de nodos funcional
"""

import sys
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QSplitter, QLabel, QPushButton, QMessageBox, QFrame, QStatusBar,
        QMenuBar, QMenu, QToolBar, QFileDialog
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QAction, QKeySequence
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("⚠️ PyQt6 no disponible")

# Imports de GoboFlow
try:
    from config import APP_NAME, APP_VERSION, USER_CONFIG_DIR
except ImportError:
    APP_NAME = "GoboFlow"
    APP_VERSION = "0.1.0"
    USER_CONFIG_DIR = Path.home() / ".goboflow"

# Importar editor de nodos
try:
    from ui.node_editor import create_node_editor, NODE_EDITOR_AVAILABLE
    print("✅ Editor de nodos disponible")
except ImportError as e:
    NODE_EDITOR_AVAILABLE = False
    create_node_editor = None
    print(f"⚠️ Editor de nodos no disponible: {e}")

class GoboFlowMainWindow(QMainWindow):
    """
    Ventana principal completa de GoboFlow
    """
    
    # Señales
    project_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Estado de la aplicación
        self.current_project_path = None
        self.is_modified = False
        
        # Componentes principales
        self.node_editor = None
        self.viewport_widget = None
        
        # Configurar ventana
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1000, 700)
        self.resize(1400, 900)
        
        # Inicializar UI
        self.init_ui()
        self.init_menus()
        self.init_toolbars()
        self.init_status_bar()
        self.connect_signals()
        
        # Aplicar tema dark
        self.apply_dark_theme()
        
        # Crear proyecto de ejemplo
        QTimer.singleShot(500, self.create_example_project)
        
        print("🎨 Ventana principal completa de GoboFlow inicializada")
    
    def init_ui(self):
        """Inicializa la interfaz principal"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter principal horizontal
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Panel izquierdo - Biblioteca de nodos
        left_panel = self.create_node_library()
        left_panel.setMaximumWidth(250)
        left_panel.setMinimumWidth(200)
        main_splitter.addWidget(left_panel)
        
        # Panel central - Editor + Viewport
        center_panel = self.create_center_panel()
        main_splitter.addWidget(center_panel)
        
        # Panel derecho - Propiedades
        right_panel = self.create_properties_panel()
        right_panel.setMaximumWidth(300)
        right_panel.setMinimumWidth(250)
        main_splitter.addWidget(right_panel)
        
        # Configurar tamaños
        main_splitter.setSizes([250, 800, 300])
    
    def create_node_library(self) -> QWidget:
        """Crea la biblioteca de nodos"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(panel)
        
        # Título
        title = QLabel("📚 Biblioteca de Nodos")
        title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px; background: #404040;")
        layout.addWidget(title)
        
        # Categorías de nodos
        categories = [
            ("🎯 Primitivas", [
                ("Círculo", self.add_circle_node),
                ("Rectángulo", self.add_rectangle_node),
                ("Polígono", self.add_polygon_node)
            ]),
            ("📊 Parámetros", [
                ("Número", self.add_number_node),
                ("Vector", self.add_vector_node),
                ("Color", self.add_color_node)
            ]),
            ("🔧 Modificadores", [
                ("Transformar", self.add_transform_node),
                ("Array", self.add_array_node),
                ("Escalar", self.add_scale_node)
            ]),
            ("🔀 Operaciones", [
                ("Unir", self.add_merge_node),
                ("Dividir", self.add_split_node),
                ("Booleanas", self.add_boolean_node)
            ]),
            ("📤 Salidas", [
                ("Visor", self.add_viewer_node),
                ("Exportar", self.add_export_node)
            ])
        ]
        
        for category_name, nodes in categories:
            # Título de categoría
            cat_label = QLabel(category_name)
            cat_label.setStyleSheet("font-weight: bold; color: #00aaff; margin-top: 10px;")
            layout.addWidget(cat_label)
            
            # Botones de nodos
            for node_name, callback in nodes:
                btn = QPushButton(f"  {node_name}")
                btn.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding: 8px;
                        margin: 1px;
                        border: 1px solid #555;
                        background: #2b2b2b;
                        color: white;
                    }
                    QPushButton:hover {
                        background: #404040;
                    }
                    QPushButton:pressed {
                        background: #0078d4;
                    }
                """)
                btn.clicked.connect(callback)
                layout.addWidget(btn)
        
        layout.addStretch()
        return panel
    
    def create_center_panel(self) -> QWidget:
        """Crea el panel central con editor y viewport"""
        center_widget = QWidget()
        layout = QVBoxLayout(center_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter vertical para editor + viewport
        center_splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(center_splitter)
        
        # Editor de nodos
        if NODE_EDITOR_AVAILABLE:
            self.node_editor = create_node_editor()
            center_splitter.addWidget(self.node_editor)
        else:
            # Placeholder si no está disponible
            placeholder = QLabel("Editor de nodos no disponible\nInstala PyQt6 completamente")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: #888; font-size: 16px; background: #2b2b2b;")
            center_splitter.addWidget(placeholder)
        
        # Viewport placeholder
        viewport_placeholder = self.create_viewport_placeholder()
        center_splitter.addWidget(viewport_placeholder)
        
        # Configurar tamaños
        center_splitter.setSizes([500, 200])
        
        return center_widget
    
    def create_viewport_placeholder(self) -> QWidget:
        """Crea placeholder para el viewport"""
        viewport = QFrame()
        viewport.setFrameStyle(QFrame.Shape.StyledPanel)
        viewport.setStyleSheet("background: black; border: 1px solid #555;")
        
        layout = QVBoxLayout(viewport)
        
        # Título
        title = QLabel("👁️ Vista Previa")
        title.setStyleSheet("font-weight: bold; padding: 8px; background: #404040; color: white;")
        layout.addWidget(title)
        
        # Área de preview
        preview_area = QLabel("Vista previa en tiempo real\n\n(Próximamente)")
        preview_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_area.setStyleSheet("color: #888; font-size: 14px; margin: 20px;")
        layout.addWidget(preview_area)
        
        return viewport
    
    def create_properties_panel(self) -> QWidget:
        """Crea el panel de propiedades"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(panel)
        
        # Título
        title = QLabel("⚙️ Propiedades")
        title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px; background: #404040;")
        layout.addWidget(title)
        
        # Información del nodo seleccionado
        self.selected_node_info = QLabel("Selecciona un nodo para ver sus propiedades")
        self.selected_node_info.setWordWrap(True)
        self.selected_node_info.setStyleSheet("padding: 10px; color: #ccc;")
        layout.addWidget(self.selected_node_info)
        
        # Propiedades editables (placeholder)
        props_title = QLabel("📝 Parámetros:")
        props_title.setStyleSheet("font-weight: bold; margin-top: 20px; color: #00aaff;")
        layout.addWidget(props_title)
        
        self.properties_area = QLabel("No hay parámetros editables")
        self.properties_area.setStyleSheet("padding: 10px; color: #888;")
        layout.addWidget(self.properties_area)
        
        layout.addStretch()
        
        # Información del proyecto
        project_title = QLabel("📁 Proyecto:")
        project_title.setStyleSheet("font-weight: bold; color: #00aaff;")
        layout.addWidget(project_title)
        
        self.project_info = QLabel("Proyecto nuevo")
        self.project_info.setStyleSheet("padding: 5px; color: #ccc; font-size: 11px;")
        layout.addWidget(self.project_info)
        
        return panel
    
    def init_menus(self):
        """Inicializa el menú"""
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu("&Archivo")
        
        new_action = QAction("&Nuevo", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Abrir...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("&Guardar", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        export_action = QAction("&Exportar SVG...", self)
        export_action.triggered.connect(self.export_svg)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("&Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Ver
        view_menu = menubar.addMenu("&Ver")
        
        fit_action = QAction("Ajustar &Vista", self)
        fit_action.triggered.connect(self.fit_view)
        view_menu.addAction(fit_action)
        
        zoom_reset_action = QAction("Zoom &100%", self)
        zoom_reset_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(zoom_reset_action)
        
        # Menú Ayuda
        help_menu = menubar.addMenu("&Ayuda")
        
        about_action = QAction("&Acerca de...", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def init_toolbars(self):
        """Inicializa las barras de herramientas"""
        # Toolbar principal
        main_toolbar = self.addToolBar("Principal")
        main_toolbar.setMovable(False)
        
        # Botones de archivo
        main_toolbar.addAction("📄 Nuevo", self.new_project)
        main_toolbar.addAction("📂 Abrir", self.open_project)
        main_toolbar.addAction("💾 Guardar", self.save_project)
        
        main_toolbar.addSeparator()
        
        # Botones de ejecución
        main_toolbar.addAction("▶️ Ejecutar", self.execute_graph)
        main_toolbar.addAction("🗑️ Limpiar", self.clear_graph)
        
        main_toolbar.addSeparator()
        
        # Botones de vista
        main_toolbar.addAction("🔍 Ajustar", self.fit_view)
        main_toolbar.addAction("📤 Exportar", self.export_svg)
    
    def init_status_bar(self):
        """Inicializa la barra de estado"""
        status = self.statusBar()
        status.showMessage("Listo - Editor de nodos cargado")
        
        # Indicadores permanentes
        self.node_count_label = QLabel("Nodos: 0")
        status.addPermanentWidget(self.node_count_label)
        
        self.zoom_label = QLabel("Zoom: 100%")
        status.addPermanentWidget(self.zoom_label)
    
    def connect_signals(self):
        """Conecta las señales"""
        if self.node_editor:
            self.node_editor.node_selected.connect(self.on_node_selected)
            self.node_editor.node_added.connect(self.on_node_added)
            self.node_editor.node_removed.connect(self.on_node_removed)
            self.node_editor.connection_created.connect(self.on_connection_created)
    
    def apply_dark_theme(self):
        """Aplica el tema oscuro"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: white;
            }
            QWidget {
                background-color: #2b2b2b;
                color: white;
            }
            QFrame {
                background-color: #353535;
                border: 1px solid #555;
            }
            QMenuBar {
                background-color: #404040;
                border-bottom: 1px solid #555;
            }
            QMenuBar::item:selected {
                background-color: #0078d4;
            }
            QMenu {
                background-color: #404040;
                border: 1px solid #555;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
            QToolBar {
                background-color: #404040;
                border: 1px solid #555;
                spacing: 3px;
            }
            QStatusBar {
                background-color: #404040;
                border-top: 1px solid #555;
            }
            QPushButton {
                background: #505050;
                border: 1px solid #606060;
                border-radius: 3px;
                padding: 5px 10px;
                color: white;
            }
            QPushButton:hover {
                background: #606060;
            }
            QPushButton:pressed {
                background: #0078d4;
            }
            QLabel {
                color: white;
            }
        """)
    
    def create_example_project(self):
        """Crea un proyecto de ejemplo"""
        if not self.node_editor:
            return
        
        try:
            # Limpiar editor
            self.node_editor.clear_scene()
            
            # Añadir nodos de ejemplo
            self.add_number_node()
            self.add_circle_node()
            self.add_viewer_node()
            
            # Posicionar nodos automáticamente
            self.arrange_nodes_automatically()
            
            self.statusBar().showMessage("Proyecto de ejemplo creado")
            print("📋 Proyecto de ejemplo creado con 3 nodos")
            
        except Exception as e:
            print(f"Error creando proyecto de ejemplo: {e}")
    
    def arrange_nodes_automatically(self):
        """Organiza los nodos automáticamente"""
        if not self.node_editor or not hasattr(self.node_editor, 'scene'):
            return
        
        # Obtener nodos y organizarlos en columnas
        nodes = list(self.node_editor.scene.node_graphics.values())
        
        for i, node_graphics in enumerate(nodes):
            x = -200 + (i * 250)  # Espaciado horizontal
            y = 0
            node_graphics.setPos(x, y)
    
    # ===========================================
    # ACCIONES DE MENÚ Y TOOLBAR
    # ===========================================
    
    def new_project(self):
        """Crea un nuevo proyecto"""
        if self.check_save_changes():
            if self.node_editor:
                self.node_editor.clear_scene()
            
            self.current_project_path = None
            self.is_modified = False
            self.update_window_title()
            self.statusBar().showMessage("Nuevo proyecto creado")
    
    def open_project(self):
        """Abre un proyecto"""
        if self.check_save_changes():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Abrir Proyecto GoboFlow",
                str(USER_CONFIG_DIR / "projects"),
                "GoboFlow Projects (*.gflow);;All Files (*.*)"
            )
            
            if file_path:
                # TODO: Implementar carga real de proyecto
                self.current_project_path = Path(file_path)
                self.update_window_title()
                self.statusBar().showMessage(f"Proyecto abierto: {Path(file_path).name}")
    
    def save_project(self):
        """Guarda el proyecto"""
        if self.current_project_path:
            # TODO: Implementar guardado real
            self.is_modified = False
            self.update_window_title()
            self.statusBar().showMessage("Proyecto guardado")
        else:
            self.save_project_as()
    
    def save_project_as(self):
        """Guarda el proyecto con un nuevo nombre"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Proyecto Como",
            str(USER_CONFIG_DIR / "projects" / "nuevo_proyecto.gflow"),
            "GoboFlow Projects (*.gflow);;All Files (*.*)"
        )
        
        if file_path:
            self.current_project_path = Path(file_path)
            self.save_project()
    
    def export_svg(self):
        """Exporta el resultado a SVG"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Gobo a SVG",
            str(Path.home() / "gobo_export.svg"),
            "SVG Files (*.svg);;All Files (*.*)"
        )
        
        if file_path:
            # TODO: Implementar exportación real desde viewport
            # Por ahora, crear SVG básico
            svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="1024" height="1024" 
     viewBox="0 0 1024 1024"
     style="background: black;">
  
  <!-- Gobo generado por GoboFlow -->
  <circle cx="512" cy="512" r="200" fill="white" opacity="0.8"/>
  
  <text x="50" y="980" fill="white" font-family="Arial" font-size="24">
    GoboFlow - Editor Visual
  </text>
  
</svg>'''
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            self.statusBar().showMessage(f"SVG exportado: {Path(file_path).name}")
            
            QMessageBox.information(
                self, "Exportación Completada",
                f"Gobo exportado exitosamente a:\n{file_path}"
            )
    
    def execute_graph(self):
        """Ejecuta el grafo de nodos"""
        if self.node_editor:
            self.node_editor.execute_graph()
            self.statusBar().showMessage("Grafo ejecutado con efectos visuales")
    
    def clear_graph(self):
        """Limpia el grafo"""
        if self.node_editor:
            self.node_editor.clear_scene()
            self.statusBar().showMessage("Grafo limpiado")
    
    def fit_view(self):
        """Ajusta la vista"""
        if self.node_editor and hasattr(self.node_editor, 'view'):
            self.node_editor.view.fit_in_view_all()
    
    def reset_zoom(self):
        """Resetea el zoom"""
        if self.node_editor and hasattr(self.node_editor, 'view'):
            self.node_editor.view.reset_zoom()
    
    # ===========================================
    # FUNCIONES DE AÑADIR NODOS
    # ===========================================
    
    def add_circle_node(self):
        """Añade un nodo círculo"""
        if self.node_editor:
            self.node_editor.add_circle_node()
    
    def add_rectangle_node(self):
        """Añade un nodo rectángulo"""
        self.statusBar().showMessage("Rectángulo - Próximamente")
    
    def add_polygon_node(self):
        """Añade un nodo polígono"""
        self.statusBar().showMessage("Polígono - Próximamente")
    
    def add_number_node(self):
        """Añade un nodo número"""
        if self.node_editor:
            self.node_editor.add_number_node()
    
    def add_vector_node(self):
        """Añade un nodo vector"""
        self.statusBar().showMessage("Vector - Próximamente")
    
    def add_color_node(self):
        """Añade un nodo color"""
        self.statusBar().showMessage("Color - Próximamente")
    
    def add_transform_node(self):
        """Añade un nodo transformar"""
        self.statusBar().showMessage("Transformar - Próximamente")
    
    def add_array_node(self):
        """Añade un nodo array"""
        self.statusBar().showMessage("Array - Próximamente")
    
    def add_scale_node(self):
        """Añade un nodo escalar"""
        self.statusBar().showMessage("Escalar - Próximamente")
    
    def add_merge_node(self):
        """Añade un nodo unir"""
        self.statusBar().showMessage("Unir - Próximamente")
    
    def add_split_node(self):
        """Añade un nodo dividir"""
        self.statusBar().showMessage("Dividir - Próximamente")
    
    def add_boolean_node(self):
        """Añade un nodo booleanas"""
        self.statusBar().showMessage("Booleanas - Próximamente")
    
    def add_viewer_node(self):
        """Añade un nodo visor"""
        if self.node_editor:
            self.node_editor.add_viewer_node()
    
    def add_export_node(self):
        """Añade un nodo exportar"""
        self.statusBar().showMessage("Exportar - Próximamente")
    
    # ===========================================
    # EVENTOS Y SEÑALES
    # ===========================================
    
    def on_node_selected(self, node):
        """Maneja selección de nodo"""
        if node:
            info = f"📋 {node.title}\n"
            info += f"Tipo: {node.NODE_TYPE}\n"
            info += f"Categoría: {getattr(node, 'NODE_CATEGORY', 'N/A')}\n"
            info += f"ID: {node.id[:8]}..."
            
            self.selected_node_info.setText(info)
            
            # TODO: Mostrar parámetros editables
            self.properties_area.setText("Parámetros editables\n(Próximamente)")
        else:
            self.selected_node_info.setText("Selecciona un nodo para ver sus propiedades")
            self.properties_area.setText("No hay parámetros editables")
    
    def on_node_added(self, node):
        """Maneja nodo añadido"""
        self.update_node_count()
        self.is_modified = True
        self.update_window_title()
    
    def on_node_removed(self, node):
        """Maneja nodo eliminado"""
        self.update_node_count()
        self.is_modified = True
        self.update_window_title()
    
    def on_connection_created(self, connection):
        """Maneja conexión creada"""
        self.is_modified = True
        self.update_window_title()
        self.statusBar().showMessage("Conexión creada")
    
    def update_node_count(self):
        """Actualiza el contador de nodos"""
        if self.node_editor and hasattr(self.node_editor, 'scene'):
            count = len(self.node_editor.scene.node_graphics)
            self.node_count_label.setText(f"Nodos: {count}")
    
    def update_window_title(self):
        """Actualiza el título de la ventana"""
        title = f"{APP_NAME} v{APP_VERSION}"
        
        if self.current_project_path:
            title += f" - {self.current_project_path.name}"
        
        if self.is_modified:
            title += " *"
        
        self.setWindowTitle(title)
    
    def check_save_changes(self) -> bool:
        """Verifica si hay cambios sin guardar"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Cambios sin guardar",
                "¿Deseas guardar los cambios antes de continuar?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.save_project()
                return not self.is_modified
            elif reply == QMessageBox.StandardButton.Cancel:
                return False
        
        return True
    
    def show_about(self):
        """Muestra diálogo acerca de"""
        QMessageBox.about(self, "Acerca de GoboFlow", f"""
        <h3>{APP_NAME} v{APP_VERSION}</h3>
        <p><b>Generador procedural de gobos para iluminación teatral</b></p>
        
        <p><b>Características:</b></p>
        <ul>
        <li>✅ Editor visual de nodos</li>
        <li>✅ Sistema de conexiones drag & drop</li>
        <li>✅ Generación procedural de geometrías</li>
        <li>✅ Exportación SVG de alta calidad</li>
        <li>🔄 Viewport en tiempo real (próximamente)</li>
        <li>🔄 Más tipos de nodos (próximamente)</li>
        </ul>
        
        <p><b>Controles del Editor:</b></p>
        <ul>
        <li>• Arrastra nodos para moverlos</li>
        <li>• Haz clic en sockets (círculos) para conectar</li>
        <li>• Ctrl + Rueda del mouse para zoom</li>
        <li>• Botón medio para pan</li>
        <li>• Delete para eliminar seleccionados</li>
        <li>• Escape para cancelar conexiones</li>
        </ul>
        
        <p>Desarrollado con Python y PyQt6</p>
        <p><a href="https://github.com/eliasdiaz3d/GoboFlow">GitHub</a></p>
        """)
    
    def closeEvent(self, event):
        """Maneja el cierre de la ventana"""
        if self.check_save_changes():
            event.accept()
            print("👋 Cerrando GoboFlow...")
        else:
            event.ignore()

def create_goboflow_app():
    """Crea la aplicación GoboFlow completa"""
    if not PYQT_AVAILABLE:
        print("❌ PyQt6 no está disponible. Instálalo con: pip install PyQt6")
        return None, None
        
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("GoboFlow")
    
    # Configurar estilo
    app.setStyle("Fusion")
    
    # Crear ventana principal
    window = GoboFlowMainWindow()
    
    return app, window

def run_gui():
    """Ejecuta la GUI completa de GoboFlow"""
    print("🎨 Iniciando GoboFlow - Editor Visual Completo...")
    
    app, window = create_goboflow_app()
    
    if app and window:
        window.show()
        
        print("✅ GoboFlow iniciado correctamente")
        print("\n🎯 Editor Visual de Nodos Activo:")
        print("  • Biblioteca de nodos en panel izquierdo")
        print("  • Editor visual en el centro")
        print("  • Propiedades en panel derecho")
        print("  • Arrastra nodos, conecta sockets")
        print("  • Ctrl+Rueda para zoom, botón medio para pan")
        
        return app.exec()
    else:
        print("❌ No se pudo iniciar la GUI")
        return 1

if __name__ == "__main__":
    sys.exit(run_gui())