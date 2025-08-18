def _on_node_added(self, node):"""
Ventana principal de GoboFlow
Interfaz gráfica principal con editor de nodos y paneles
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QSplitter, QMenuBar, QMenu, QStatusBar, QToolBar, QDockWidget,
        QMessageBox, QFileDialog, QLabel, QPushButton, QFrame
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSettings
    from PyQt6.QtGui import QAction, QIcon, QKeySequence, QPixmap
    PYQT_AVAILABLE = True
except ImportError:
    print("PyQt6 no está instalado. Instálalo con: pip install PyQt6")
    PYQT_AVAILABLE = False
    # Clases dummy para que el código no falle
    class QMainWindow: pass
    class QWidget: pass
    class pyqtSignal: pass

# Imports de GoboFlow
from config import (
    APP_NAME, APP_VERSION, WINDOW_DEFAULT_SIZE, WINDOW_MIN_SIZE,
    WINDOW_TITLE, DARK_THEME, USER_CONFIG_DIR, config
)
from core.node_system import NodeGraph
from nodes.primitives.circle_node import CircleNode
from nodes.primitives.rectangle_node import RectangleNode
from nodes.base.base_node import NumberParameterNode, ViewerNode

# Importar editor de nodos
try:
    from .node_editor import NodeEditorWidget, create_node_editor, NODE_EDITOR_AVAILABLE
except ImportError:
    NODE_EDITOR_AVAILABLE = False
    NodeEditorWidget = None
    create_node_editor = None

# Importar viewport
try:
    from .viewport import ViewportWidget, create_viewport_widget, VIEWPORT_AVAILABLE
except ImportError:
    VIEWPORT_AVAILABLE = False
    ViewportWidget = None
    create_viewport_widget = None

class GoboFlowMainWindow(QMainWindow):
    """
    Ventana principal de GoboFlow
    Contiene el editor de nodos, paneles laterales y menús
    """
    
    # Señales
    project_changed = pyqtSignal()
    node_selected = pyqtSignal(object)
    graph_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Estado de la aplicación
        self.current_project_path: Optional[Path] = None
        self.node_graph = NodeGraph()
        self.is_modified = False
        
        # Referencias a componentes
        self.node_editor = None
        self.viewport_widget = None
        
        # Configuración de Qt
        self.settings = QSettings('GoboFlow', 'GoboFlow')
        
        # Inicializar UI
        self._init_ui()
        self._init_menus()
        self._init_toolbars()
        self._init_status_bar()
        self._init_docks()
        self._connect_signals()
        
        # Aplicar tema
        self._apply_theme()
        
        # Restaurar configuración de ventana
        self._restore_window_state()
        
        # Crear proyecto nuevo por defecto
        self._new_project()
        
        # Actualizar viewport inicial después de un breve delay
        QTimer.singleShot(500, self._update_viewport)
        
        print("🎨 Ventana principal de GoboFlow inicializada")
    
    def _init_ui(self):
        """Inicializa la interfaz básica"""
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(*WINDOW_MIN_SIZE)
        self.resize(*WINDOW_DEFAULT_SIZE)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter principal (horizontal)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Panel izquierdo (biblioteca de nodos)
        self.left_panel = self._create_left_panel()
        self.main_splitter.addWidget(self.left_panel)
        
        # Panel central (editor de nodos + viewport)
        self.center_panel = self._create_center_panel()
        self.main_splitter.addWidget(self.center_panel)
        
        # Panel derecho (propiedades)
        self.right_panel = self._create_right_panel()
        self.main_splitter.addWidget(self.right_panel)
        
        # Configurar tamaños del splitter
        self.main_splitter.setSizes([250, 700, 250])
        self.main_splitter.setCollapsible(0, True)
        self.main_splitter.setCollapsible(2, True)
    
    def _create_left_panel(self) -> QWidget:
        """Crea el panel izquierdo con la biblioteca de nodos"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumWidth(300)
        panel.setMinimumWidth(200)
        
        layout = QVBoxLayout(panel)
        
        # Título del panel
        title = QLabel("📚 Biblioteca de Nodos")
        title.setStyleSheet("font-weight: bold; padding: 8px; background: #3c3c3c;")
        layout.addWidget(title)
        
        # Lista de categorías de nodos (placeholder)
        categories = [
            "🎯 Primitives",
            "⚙️ Generators", 
            "🔧 Modifiers",
            "🔀 Operations",
            "🎨 Materials",
            "📊 Parameters",
            "🔢 Math",
            "📥 Inputs",
            "📤 Outputs"
        ]
        
        for category in categories:
            btn = QPushButton(category)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px;
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
            layout.addWidget(btn)
        
        layout.addStretch()
        return panel
    
    def _create_center_panel(self) -> QWidget:
        """Crea el panel central con el editor de nodos"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter vertical para editor + viewport
        center_splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(center_splitter)
        
        # Editor de nodos (placeholder)
        node_editor = self._create_node_editor()
        center_splitter.addWidget(node_editor)
        
        # Viewport/Preview (placeholder)  
        viewport = self._create_viewport()
        center_splitter.addWidget(viewport)
        
        # Configurar tamaños
        center_splitter.setSizes([400, 200])
        
        return panel
    
    def _create_node_editor(self) -> QWidget:
        """Crea el editor de nodos"""
        if NODE_EDITOR_AVAILABLE:
            # Crear editor visual real
            self.node_editor = create_node_editor()
            
            # Conectar señales
            self.node_editor.node_selected.connect(self.node_selected.emit)
            self.node_editor.node_added.connect(self._on_node_added)
            self.node_editor.node_removed.connect(self._on_node_removed)
            self.node_editor.connection_created.connect(self._on_connection_created)
            
            return self.node_editor
        else:
            # Fallback placeholder
            editor = QFrame()
            editor.setFrameStyle(QFrame.Shape.StyledPanel)
            editor.setStyleSheet("background: #1e1e1e; border: 1px solid #555;")
            
            layout = QVBoxLayout(editor)
            
            # Título
            title = QLabel("Editor de Nodos")
            title.setStyleSheet("font-weight: bold; padding: 8px; background: #3c3c3c; color: white;")
            layout.addWidget(title)
            
            # Mensaje
            message = QLabel("Editor visual no disponible\nInstala PyQt6 para usar el editor visual")
            message.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message.setStyleSheet("color: #888; font-size: 14px; background: #2b2b2b; margin: 10px;")
            message.setMinimumHeight(300)
            layout.addWidget(message)
            
            self.node_editor = None
            return editor
        editor.setStyleSheet("background: #1e1e1e; border: 1px solid #555;")
        
        layout = QVBoxLayout(editor)
        
        # Título
        title = QLabel("🔗 Editor de Nodos")
        title.setStyleSheet("font-weight: bold; padding: 8px; background: #3c3c3c; color: white;")
        layout.addWidget(title)
        
        # Área de trabajo del editor (placeholder)
        work_area = QLabel("Área de trabajo del editor de nodos\n\n(Próximamente: Editor visual de nodos)")
        work_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        work_area.setStyleSheet("color: #888; font-size: 14px; background: #2b2b2b; margin: 10px;")
        work_area.setMinimumHeight(300)
        layout.addWidget(work_area)
        
        return editor
    
    def _create_viewport(self) -> QWidget:
        """Crea el viewport de preview"""
        if VIEWPORT_AVAILABLE:
            # Crear viewport real
            self.viewport_widget = create_viewport_widget()
            
            # Conectar señales
            if self.viewport_widget:
                self.viewport_widget.export_requested.connect(self._export_svg)
                return self.viewport_widget
        
        # Fallback placeholder
        viewport = QFrame()
        viewport.setFrameStyle(QFrame.Shape.StyledPanel)
        viewport.setStyleSheet("background: black; border: 1px solid #555;")
        
        layout = QVBoxLayout(viewport)
        
        # Título
        title = QLabel("👁️ Vista Previa")
        title.setStyleSheet("font-weight: bold; padding: 8px; background: #3c3c3c; color: white;")
        layout.addWidget(title)
        
        # Área de preview
        preview_area = QLabel("Vista previa del gobo\n\n(Los gobos se mostrarán aquí)")
        preview_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_area.setStyleSheet("color: #888; font-size: 14px; background: black; margin: 10px;")
        preview_area.setMinimumHeight(150)
        layout.addWidget(preview_area)
        
        self.viewport_widget = None
        return viewport
    
    def _create_right_panel(self) -> QWidget:
        """Crea el panel derecho con propiedades"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumWidth(300)
        panel.setMinimumWidth(200)
        
        layout = QVBoxLayout(panel)
        
        # Título
        title = QLabel("⚙️ Propiedades")
        title.setStyleSheet("font-weight: bold; padding: 8px; background: #3c3c3c;")
        layout.addWidget(title)
        
        # Área de propiedades (placeholder)
        props_area = QLabel("Propiedades del nodo seleccionado\n\n(Selecciona un nodo para ver sus propiedades)")
        props_area.setAlignment(Qt.AlignmentFlag.AlignTop)
        props_area.setStyleSheet("color: #888; padding: 10px; background: #2b2b2b;")
        props_area.setWordWrap(True)
        layout.addWidget(props_area)
        
        layout.addStretch()
        return panel
    
    def _init_menus(self):
        """Inicializa la barra de menús"""
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu("&Archivo")
        
        # Nuevo proyecto
        new_action = QAction("&Nuevo", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)
        
        # Abrir proyecto
        open_action = QAction("&Abrir...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Guardar proyecto
        save_action = QAction("&Guardar", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)
        
        # Guardar como
        save_as_action = QAction("Guardar &como...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Exportar
        export_action = QAction("&Exportar SVG...", self)
        export_action.triggered.connect(self._export_svg)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Salir
        exit_action = QAction("&Salir", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Editar
        edit_menu = menubar.addMenu("&Editar")
        
        undo_action = QAction("&Deshacer", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Rehacer", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addAction(redo_action)
        
        # Menú Nodos
        nodes_menu = menubar.addMenu("&Nodos")
        
        add_circle_action = QAction("Añadir &Círculo", self)
        add_circle_action.triggered.connect(self._add_circle_node)
        nodes_menu.addAction(add_circle_action)
        
        add_rectangle_action = QAction("Añadir &Rectángulo", self)
        add_rectangle_action.triggered.connect(self._add_rectangle_node)
        nodes_menu.addAction(add_rectangle_action)
        
        add_number_action = QAction("Añadir &Número", self)
        add_number_action.triggered.connect(self._add_number_node)
        nodes_menu.addAction(add_number_action)
        
        add_viewer_action = QAction("Añadir &Visor", self)
        add_viewer_action.triggered.connect(self._add_viewer_node)
        nodes_menu.addAction(add_viewer_action)
        
        # Menú Ayuda
        help_menu = menubar.addMenu("A&yuda")
        
        about_action = QAction("&Acerca de...", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _init_toolbars(self):
        """Inicializa las barras de herramientas"""
        # Toolbar principal
        main_toolbar = self.addToolBar("Principal")
        main_toolbar.setObjectName("MainToolBar")  # Importante para saveState
        main_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        
        # Botones de archivo
        new_btn = main_toolbar.addAction("📄 Nuevo")
        new_btn.triggered.connect(self._new_project)
        
        open_btn = main_toolbar.addAction("📂 Abrir")
        open_btn.triggered.connect(self._open_project)
        
        save_btn = main_toolbar.addAction("💾 Guardar")
        save_btn.triggered.connect(self._save_project)
        
        main_toolbar.addSeparator()
        
        # Botones de nodos
        circle_btn = main_toolbar.addAction("🔵 Círculo")
        circle_btn.triggered.connect(self._add_circle_node)
        
        rectangle_btn = main_toolbar.addAction("⬜ Rectángulo")
        rectangle_btn.triggered.connect(self._add_rectangle_node)
        
        number_btn = main_toolbar.addAction("🔢 Número")
        number_btn.triggered.connect(self._add_number_node)
        
        viewer_btn = main_toolbar.addAction("👁️ Visor")
        viewer_btn.triggered.connect(self._add_viewer_node)
        
        main_toolbar.addSeparator()
        
        # Botón de ejecutar
        execute_btn = main_toolbar.addAction("▶️ Ejecutar")
        execute_btn.triggered.connect(self._execute_graph)
    
    def _init_status_bar(self):
        """Inicializa la barra de estado"""
        status = self.statusBar()
        
        # Mensaje por defecto
        status.showMessage("Listo")
        
        # Indicadores permanentes
        self.node_count_label = QLabel("Nodos: 0")
        status.addPermanentWidget(self.node_count_label)
        
        self.modified_label = QLabel("")
        status.addPermanentWidget(self.modified_label)
    
    def _init_docks(self):
        """Inicializa los paneles acoplables"""
        # Por ahora, los paneles están integrados en el layout principal
        # En el futuro, se pueden convertir en QDockWidget para mayor flexibilidad
        
        # Configurar objectNames para los widgets principales
        if hasattr(self, 'left_panel'):
            self.left_panel.setObjectName("LeftPanel")
        if hasattr(self, 'center_panel'):
            self.center_panel.setObjectName("CenterPanel")
        if hasattr(self, 'right_panel'):
            self.right_panel.setObjectName("RightPanel")
        if hasattr(self, 'main_splitter'):
            self.main_splitter.setObjectName("MainSplitter")
    
    def _connect_signals(self):
        """Conecta las señales de la aplicación"""
        self.project_changed.connect(self._on_project_changed)
        self.node_selected.connect(self._on_node_selected)
        self.graph_updated.connect(self._on_graph_updated)
    
    def _apply_theme(self):
        """Aplica el tema visual a la aplicación"""
        # Usar tema oscuro por defecto
        dark_style = f"""
        QMainWindow {{
            background-color: {DARK_THEME['background']};
            color: {DARK_THEME['foreground']};
        }}
        QMenuBar {{
            background-color: {DARK_THEME['background_light']};
            color: {DARK_THEME['foreground']};
            border-bottom: 1px solid {DARK_THEME['border']};
        }}
        QMenuBar::item:selected {{
            background-color: {DARK_THEME['selection']};
        }}
        QMenu {{
            background-color: {DARK_THEME['background_light']};
            color: {DARK_THEME['foreground']};
            border: 1px solid {DARK_THEME['border']};
        }}
        QMenu::item:selected {{
            background-color: {DARK_THEME['selection']};
        }}
        QToolBar {{
            background-color: {DARK_THEME['background_light']};
            border: 1px solid {DARK_THEME['border']};
            spacing: 2px;
        }}
        QStatusBar {{
            background-color: {DARK_THEME['background_light']};
            color: {DARK_THEME['foreground']};
            border-top: 1px solid {DARK_THEME['border']};
        }}
        QSplitter::handle {{
            background-color: {DARK_THEME['border']};
        }}
        QLabel {{
            color: {DARK_THEME['foreground']};
        }}
        """
        
        self.setStyleSheet(dark_style)
    
    def _restore_window_state(self):
        """Restaura el estado de la ventana desde configuración"""
        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
                
            window_state = self.settings.value("windowState")
            if window_state:
                self.restoreState(window_state)
                
            splitter_state = self.settings.value("splitterState")
            if splitter_state:
                self.main_splitter.restoreState(splitter_state)
        except Exception:
            pass  # Usar configuración por defecto si hay error
    
    def _save_window_state(self):
        """Guarda el estado de la ventana"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("splitterState", self.main_splitter.saveState())
    
    # ===========================================
    # ACCIONES DE MENÚ Y TOOLBAR
    # ===========================================
    
    def _new_project(self):
        """Crea un nuevo proyecto"""
        if self._check_save_changes():
            self.node_graph.clear()
            
            # Limpiar editor visual si está disponible
            if self.node_editor and NODE_EDITOR_AVAILABLE:
                self.node_editor.clear_all()
            
            self.current_project_path = None
            self.is_modified = False
            self.project_changed.emit()
            self.statusBar().showMessage("Nuevo proyecto creado")
            print("📄 Nuevo proyecto creado")
    
    def _open_project(self):
        """Abre un proyecto existente"""
        if self._check_save_changes():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Abrir Proyecto", 
                str(USER_CONFIG_DIR / "projects"),
                "GoboFlow Projects (*.gflow);;All Files (*.*)"
            )
            
            if file_path:
                # TODO: Implementar carga de proyecto
                self.statusBar().showMessage(f"Proyecto abierto: {Path(file_path).name}")
                print(f"📂 Abriendo proyecto: {file_path}")
    
    def _save_project(self):
        """Guarda el proyecto actual"""
        if self.current_project_path:
            # TODO: Implementar guardado
            self.is_modified = False
            self.project_changed.emit()
            self.statusBar().showMessage("Proyecto guardado")
            print("💾 Proyecto guardado")
        else:
            self._save_project_as()
    
    def _save_project_as(self):
        """Guarda el proyecto con un nuevo nombre"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Proyecto Como",
            str(USER_CONFIG_DIR / "projects" / "nuevo_proyecto.gflow"),
            "GoboFlow Projects (*.gflow);;All Files (*.*)"
        )
        
        if file_path:
            self.current_project_path = Path(file_path)
            self._save_project()
    
    def _export_svg(self):
        """Exporta el gobo a SVG usando el viewport"""
        if not self.viewport_widget:
            # Fallback al método anterior
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exportar SVG",
                str(Path.home() / "gobo_export.svg"),
                "SVG Files (*.svg);;All Files (*.*)"
            )
            
            if file_path:
                # TODO: Implementar exportación básica
                self.statusBar().showMessage(f"Exportado: {Path(file_path).name}")
                print(f"📤 Exportando a: {file_path}")
            return
        
        # Usar viewport para exportación de alta calidad
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Gobo a SVG",
            str(Path.home() / "gobo_export.svg"),
            "SVG Files (*.svg);;All Files (*.*)"
        )
        
        if file_path:
            try:
                # Exportar usando el viewport
                success = self.viewport_widget.export_svg(file_path, (1024, 1024))
                
                if success:
                    self.statusBar().showMessage(f"✅ Exportado exitosamente: {Path(file_path).name}")
                    print(f"📤 SVG exportado exitosamente: {file_path}")
                    
                    # Mostrar mensaje de éxito
                    QMessageBox.information(
                        self, "Exportación Exitosa",
                        f"Gobo exportado exitosamente a:\n{file_path}\n\nResolución: 1024x1024 px"
                    )
                else:
                    self.statusBar().showMessage("❌ Error en la exportación")
                    QMessageBox.warning(
                        self, "Error de Exportación",
                        "No se pudo exportar el gobo.\nVerifica que haya geometrías para exportar."
                    )
                    
            except Exception as e:
                self.statusBar().showMessage("❌ Error en la exportación")
                QMessageBox.critical(
                    self, "Error de Exportación",
                    f"Error inesperado durante la exportación:\n{e}"
                )
                print(f"❌ Error exportando SVG: {e}")
    
    def _add_circle_node(self):
        """Añade un nodo círculo al grafo"""
        circle_node = CircleNode(f"Círculo {len(self.node_graph.nodes) + 1}")
        
        # Añadir al modelo
        self.node_graph.add_node(circle_node)
        
        # Añadir al editor visual si está disponible
        if self.node_editor and NODE_EDITOR_AVAILABLE:
            self.node_editor.add_node(circle_node)
        
        self.is_modified = True
        self.graph_updated.emit()
        self.statusBar().showMessage("Nodo círculo añadido")
        print("🔵 Nodo círculo añadido")
    
    def _add_number_node(self):
        """Añade un nodo número al grafo"""
        number_node = NumberParameterNode(f"Número {len(self.node_graph.nodes) + 1}")
        
        # Añadir al modelo
        self.node_graph.add_node(number_node)
        
        # Añadir al editor visual si está disponible
        if self.node_editor and NODE_EDITOR_AVAILABLE:
            self.node_editor.add_node(number_node)
        
        self.is_modified = True
        self.graph_updated.emit()
        self.statusBar().showMessage("Nodo número añadido")
        print("🔢 Nodo número añadido")
    
    def _add_rectangle_node(self):
        """Añade un nodo rectángulo al grafo"""
        rectangle_node = RectangleNode(f"Rectángulo {len(self.node_graph.nodes) + 1}")
        
        # Añadir al modelo
        self.node_graph.add_node(rectangle_node)
        
        # Añadir al editor visual si está disponible
        if self.node_editor and NODE_EDITOR_AVAILABLE:
            self.node_editor.add_node(rectangle_node)
        
        self.is_modified = True
        self.graph_updated.emit()
        self.statusBar().showMessage("Nodo rectángulo añadido")
        print("⬜ Nodo rectángulo añadido")
    
    def _add_viewer_node(self):
        """Añade un nodo visor al grafo"""
        viewer_node = ViewerNode(f"Visor {len(self.node_graph.nodes) + 1}")
        
        # Añadir al modelo
        self.node_graph.add_node(viewer_node)
        
        # Añadir al editor visual si está disponible
        if self.node_editor and NODE_EDITOR_AVAILABLE:
            self.node_editor.add_node(viewer_node)
        
        self.is_modified = True
        self.graph_updated.emit()
        self.statusBar().showMessage("Nodo visor añadido")
        print("👁️ Nodo visor añadido")
    
    def _execute_graph(self):
        """Ejecuta el grafo de nodos"""
        try:
            execution_order = self.node_graph.get_execution_order()
            
            for node in execution_order:
                node.mark_dirty()
                if hasattr(node, 'compute'):
                    node.compute()
            
            # Actualizar viewport después de ejecutar
            self._update_viewport()
            
            self.statusBar().showMessage("Grafo ejecutado exitosamente")
            print("▶️ Grafo ejecutado exitosamente")
            
        except Exception as e:
            QMessageBox.warning(self, "Error de Ejecución", f"Error ejecutando el grafo:\n{e}")
            print(f"❌ Error ejecutando grafo: {e}")
    
    def _update_viewport(self):
        """Actualiza el viewport con las geometrías actuales"""
        if not self.viewport_widget:
            return
        
        try:
            # Recopilar todas las geometrías del grafo
            geometries = []
            
            for node in self.node_graph.nodes.values():
                # Buscar nodos con output de geometría
                if hasattr(node, 'output_sockets') and 'geometry' in node.output_sockets:
                    try:
                        # Obtener la geometría del nodo
                        if hasattr(node, 'generate_geometry'):
                            geometry = node.generate_geometry()
                            if geometry is not None:
                                geometries.append(geometry)
                    except Exception as e:
                        print(f"Error obteniendo geometría de {node.title}: {e}")
            
            # Actualizar viewport
            self.viewport_widget.update_geometries(geometries)
            print(f"🎨 Viewport actualizado con {len(geometries)} geometría(s)")
            
        except Exception as e:
            print(f"❌ Error actualizando viewport: {e}")
    
    def _show_about(self):
        """Muestra el diálogo Acerca de"""
        QMessageBox.about(self, "Acerca de GoboFlow", 
                         f"""
                         <h3>{APP_NAME} v{APP_VERSION}</h3>
                         <p>Generador procedural de gobos para iluminación teatral</p>
                         <p>Desarrollado con Python y PyQt6</p>
                         <p><a href="https://github.com/goboflow/goboflow">GitHub</a></p>
                         """)
    
    # ===========================================
    # EVENTOS Y SEÑALES
    # ===========================================
    
    def _check_save_changes(self) -> bool:
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
                self._save_project()
                return not self.is_modified  # Solo continuar si se guardó exitosamente
            elif reply == QMessageBox.StandardButton.Cancel:
                return False
                
        return True
    
    def _on_project_changed(self):
        """Se ejecuta cuando el proyecto cambia"""
        # Actualizar título de ventana
        title = WINDOW_TITLE
        if self.current_project_path:
            title += f" - {self.current_project_path.name}"
        if self.is_modified:
            title += " *"
        self.setWindowTitle(title)
        
        # Actualizar indicador de modificado
        self.modified_label.setText("●" if self.is_modified else "")
    
    def _on_node_selected(self, node):
        """Se ejecuta cuando se selecciona un nodo"""
        # TODO: Actualizar panel de propiedades
        if node:
            self.statusBar().showMessage(f"Nodo seleccionado: {node.title}")
        else:
            self.statusBar().showMessage("Ningún nodo seleccionado")
    
    def _on_graph_updated(self):
        """Se ejecuta cuando el grafo se actualiza"""
        node_count = len(self.node_graph.nodes)
        self.node_count_label.setText(f"Nodos: {node_count}")
        self.is_modified = True
        self.project_changed.emit()
    
    def _on_node_added(self, node):
        """Se ejecuta cuando se añade un nodo en el editor"""
        # Sincronizar con el modelo si no está ya
        if node.id not in self.node_graph.nodes:
            self.node_graph.add_node(node)
        self.graph_updated.emit()
        
        # Actualizar viewport automáticamente
        self._update_viewport()
    
    def _on_node_removed(self, node):
        """Se ejecuta cuando se remueve un nodo del editor"""
        # Sincronizar con el modelo
        if node.id in self.node_graph.nodes:
            self.node_graph.remove_node(node.id)
        self.graph_updated.emit()
        
        # Actualizar viewport automáticamente
        self._update_viewport()
    
    def _on_connection_created(self, connection):
        """Se ejecuta cuando se crea una conexión en el editor"""
        # Las conexiones ya están sincronizadas en el modelo
        self.is_modified = True
        self.project_changed.emit()
        
        # Actualizar viewport automáticamente
        self._update_viewport()
        
        print(f"Conexión creada: {connection.output_socket.node.title} -> {connection.input_socket.node.title}")
    
    def closeEvent(self, event):
        """Se ejecuta al cerrar la ventana"""
        if self._check_save_changes():
            self._save_window_state()
            event.accept()
            print("👋 Cerrando GoboFlow...")
        else:
            event.ignore()

# ===========================================
# FUNCIONES DE UTILIDAD
# ===========================================

def create_goboflow_app():
    """Crea y configura la aplicación GoboFlow"""
    if not PYQT_AVAILABLE:
        print("❌ PyQt6 no está disponible. Instálalo con: pip install PyQt6")
        return None, None
        
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("GoboFlow")
    
    # Configurar iconos y estilo
    app.setStyle("Fusion")  # Estilo moderno multiplataforma
    
    # Crear ventana principal
    window = GoboFlowMainWindow()
    
    return app, window

def run_gui():
    """Ejecuta la interfaz gráfica de GoboFlow"""
    app, window = create_goboflow_app()
    
    if app and window:
        window.show()
        print(f"🎨 {APP_NAME} iniciado en modo GUI")
        return app.exec()
    else:
        return 1

if __name__ == "__main__":
    sys.exit(run_gui())