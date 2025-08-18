"""
Configuración global para GoboFlow
Define constantes, paths, configuraciones por defecto y ajustes del sistema
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from enum import Enum

# =============================================================================
# INFORMACIÓN DE LA APLICACIÓN
# =============================================================================

APP_NAME = "GoboFlow"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Generador procedural de gobos para iluminación teatral"
APP_AUTHOR = "GoboFlow Team"
APP_URL = "https://github.com/goboflow/goboflow"

# =============================================================================
# PATHS Y DIRECTORIOS
# =============================================================================

# Directorio raíz del proyecto
ROOT_DIR = Path(__file__).parent.absolute()

# Directorios principales
CORE_DIR = ROOT_DIR / "core"
NODES_DIR = ROOT_DIR / "nodes"
UI_DIR = ROOT_DIR / "ui"
UTILS_DIR = ROOT_DIR / "utils"
DATA_DIR = ROOT_DIR / "data"
TESTS_DIR = ROOT_DIR / "tests"
DOCS_DIR = ROOT_DIR / "docs"
EXAMPLES_DIR = ROOT_DIR / "examples"

# Subdirectorios de data
ICONS_DIR = DATA_DIR / "icons"
PRESETS_DIR = DATA_DIR / "presets"
SHADERS_DIR = DATA_DIR / "shaders"
FONTS_DIR = DATA_DIR / "fonts"

# Subdirectorios de iconos
NODES_ICONS_DIR = ICONS_DIR / "nodes"
UI_ICONS_DIR = ICONS_DIR / "ui"

# Directorio de usuario (home)
USER_HOME = Path.home()
USER_CONFIG_DIR = USER_HOME / ".goboflow"
USER_PROJECTS_DIR = USER_CONFIG_DIR / "projects"
USER_PRESETS_DIR = USER_CONFIG_DIR / "presets"
USER_CACHE_DIR = USER_CONFIG_DIR / "cache"
USER_LOGS_DIR = USER_CONFIG_DIR / "logs"

# Crear directorios de usuario si no existen
def ensure_user_directories():
    """Crea los directorios de usuario necesarios"""
    for directory in [USER_CONFIG_DIR, USER_PROJECTS_DIR, USER_PRESETS_DIR, USER_CACHE_DIR, USER_LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

# =============================================================================
# CONFIGURACIÓN DE ARCHIVOS
# =============================================================================

# Extensiones de archivo
PROJECT_EXTENSION = ".gflow"
PRESET_EXTENSION = ".gpreset"
EXPORT_EXTENSIONS = [".svg", ".png", ".jpg", ".pdf", ".eps"]

# Filtros de archivos para diálogos
FILE_FILTERS = {
    "project": f"GoboFlow Projects (*{PROJECT_EXTENSION})",
    "preset": f"GoboFlow Presets (*{PRESET_EXTENSION})",
    "svg": "SVG Files (*.svg)",
    "image": "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff)",
    "all": "All Files (*.*)"
}

# Configuración de auto-guardado
AUTO_SAVE_ENABLED = True
AUTO_SAVE_INTERVAL = 300  # segundos (5 minutos)
MAX_AUTO_SAVE_FILES = 10

# =============================================================================
# CONFIGURACIÓN DE RENDERIZADO
# =============================================================================

class RenderQuality(Enum):
    """Calidades de renderizado disponibles"""
    DRAFT = "draft"
    PREVIEW = "preview"
    FINAL = "final"
    ULTRA = "ultra"

# Configuraciones de renderizado por calidad
RENDER_SETTINGS = {
    RenderQuality.DRAFT: {
        "resolution": (512, 512),
        "dpi": 72,
        "antialiasing": False,
        "max_segments": 16,
        "simplify_curves": True
    },
    RenderQuality.PREVIEW: {
        "resolution": (1024, 1024),
        "dpi": 150,
        "antialiasing": True,
        "max_segments": 32,
        "simplify_curves": False
    },
    RenderQuality.FINAL: {
        "resolution": (2048, 2048),
        "dpi": 300,
        "antialiasing": True,
        "max_segments": 64,
        "simplify_curves": False
    },
    RenderQuality.ULTRA: {
        "resolution": (4096, 4096),
        "dpi": 600,
        "antialiasing": True,
        "max_segments": 128,
        "simplify_curves": False
    }
}

# Configuración por defecto
DEFAULT_RENDER_QUALITY = RenderQuality.PREVIEW
DEFAULT_RESOLUTION = RENDER_SETTINGS[DEFAULT_RENDER_QUALITY]["resolution"]
DEFAULT_DPI = RENDER_SETTINGS[DEFAULT_RENDER_QUALITY]["dpi"]

# Formatos de exportación
EXPORT_FORMATS = {
    "svg": {
        "name": "SVG Vector",
        "extension": ".svg",
        "supports_vector": True,
        "supports_raster": False,
        "default_dpi": 96
    },
    "png": {
        "name": "PNG Image",
        "extension": ".png",
        "supports_vector": False,
        "supports_raster": True,
        "default_dpi": 300
    },
    "jpg": {
        "name": "JPEG Image", 
        "extension": ".jpg",
        "supports_vector": False,
        "supports_raster": True,
        "default_dpi": 300
    },
    "pdf": {
        "name": "PDF Document",
        "extension": ".pdf",
        "supports_vector": True,
        "supports_raster": True,
        "default_dpi": 300
    }
}

# =============================================================================
# CONFIGURACIÓN DE LA INTERFAZ
# =============================================================================

# Colores del tema (modo oscuro por defecto)
DARK_THEME = {
    "background": "#2b2b2b",
    "background_light": "#3c3c3c",
    "background_dark": "#1e1e1e",
    "foreground": "#ffffff",
    "foreground_dim": "#cccccc",
    "accent": "#0078d4",
    "accent_hover": "#106ebe",
    "success": "#4caf50",
    "warning": "#ff9800",
    "error": "#f44336",
    "border": "#555555",
    "border_light": "#777777",
    "selection": "#0078d4",
    "selection_inactive": "#404040"
}

LIGHT_THEME = {
    "background": "#ffffff",
    "background_light": "#f5f5f5",
    "background_dark": "#e0e0e0",
    "foreground": "#000000",
    "foreground_dim": "#666666",
    "accent": "#0078d4",
    "accent_hover": "#106ebe",
    "success": "#4caf50",
    "warning": "#ff9800",
    "error": "#f44336",
    "border": "#cccccc",
    "border_light": "#e0e0e0",
    "selection": "#0078d4",
    "selection_inactive": "#cccccc"
}

# Tema por defecto
DEFAULT_THEME = "dark"
CURRENT_THEME = DARK_THEME

# Configuración de ventana
WINDOW_DEFAULT_SIZE = (1200, 800)
WINDOW_MIN_SIZE = (800, 600)
WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION}"

# Configuración de paneles
PANEL_SIZES = {
    "node_library": 250,
    "properties": 300,
    "outliner": 200,
    "console": 150,
    "viewport": 400
}

# =============================================================================
# CONFIGURACIÓN DE NODOS
# =============================================================================

# Colores de nodos por categoría
NODE_COLORS = {
    "generators": "#4CAF50",      # Verde
    "modifiers": "#2196F3",       # Azul
    "operations": "#FF9800",      # Naranja
    "materials": "#9C27B0",       # Púrpura
    "inputs": "#607D8B",          # Gris azulado
    "outputs": "#F44336",         # Rojo
    "parameters": "#FFC107",      # Amarillo
    "math": "#795548",            # Marrón
    "utility": "#9E9E9E",         # Gris
    "base": "#757575"             # Gris oscuro
}

# Configuración visual de nodos
NODE_VISUAL = {
    "width": 160,
    "height": 80,
    "title_height": 24,
    "socket_size": 12,
    "socket_spacing": 20,
    "corner_radius": 6,
    "border_width": 2,
    "shadow_offset": (2, 2),
    "shadow_blur": 4
}

# Configuración de conexiones
CONNECTION_VISUAL = {
    "width": 2,
    "width_selected": 3,
    "curve_strength": 100,
    "hover_tolerance": 5,
    "color_default": "#888888",
    "color_selected": "#ffffff",
    "color_invalid": "#ff4444"
}

# =============================================================================
# CONFIGURACIÓN DE PERFORMANCE
# =============================================================================

# Cache del sistema
CACHE_ENABLED = True
CACHE_MAX_SIZE = 1000  # Número máximo de resultados cacheados
CACHE_CLEANUP_THRESHOLD = 0.8  # Limpiar cuando se alcance 80% de capacidad

# Ejecución
MAX_EXECUTION_TIME = 30.0  # segundos
MAX_RECURSION_DEPTH = 100
ENABLE_PARALLEL_EXECUTION = True
MAX_WORKER_THREADS = 4

# Viewport
VIEWPORT_MAX_FPS = 60
VIEWPORT_UPDATE_THRESHOLD = 0.016  # ~60 FPS
ENABLE_VIEWPORT_CULLING = True
VIEWPORT_CULLING_MARGIN = 100  # pixels

# =============================================================================
# CONFIGURACIÓN DE LOGGING
# =============================================================================

import logging

# Configuración de logging
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

LOG_FILE = USER_LOGS_DIR / "goboflow.log"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# =============================================================================
# CONFIGURACIÓN DE GEOMETRÍA
# =============================================================================

# Límites de geometría
GEOMETRY_LIMITS = {
    "max_points": 100000,
    "max_segments": 1000,
    "min_radius": 0.1,
    "max_radius": 10000,
    "min_size": 0.1,
    "max_size": 10000,
    "precision": 6  # decimales para coordenadas
}

# Tolerancias para operaciones geométricas
GEOMETRY_TOLERANCE = {
    "epsilon": 1e-6,
    "curve_tolerance": 0.1,
    "boolean_tolerance": 1e-4,
    "snap_distance": 5.0  # pixels
}

# =============================================================================
# CONFIGURACIÓN DE DESARROLLO
# =============================================================================

# Flags de desarrollo
DEBUG_MODE = __debug__
ENABLE_PROFILING = False
ENABLE_MEMORY_TRACKING = False
SHOW_DEBUG_INFO = DEBUG_MODE

# Testing
RUN_TESTS_ON_STARTUP = False
TEST_DATA_DIR = TESTS_DIR / "data"

# =============================================================================
# CONFIGURACIÓN DINÁMICA
# =============================================================================

class Config:
    """
    Clase para manejo dinámico de configuración
    Permite cambiar configuraciones en tiempo de ejecución
    """
    
    def __init__(self):
        self._settings = {}
        self._load_defaults()
        
    def _load_defaults(self):
        """Carga configuraciones por defecto"""
        self._settings = {
            "app": {
                "name": APP_NAME,
                "version": APP_VERSION,
                "theme": DEFAULT_THEME
            },
            "render": {
                "quality": DEFAULT_RENDER_QUALITY.value,
                "resolution": DEFAULT_RESOLUTION,
                "dpi": DEFAULT_DPI
            },
            "window": {
                "size": WINDOW_DEFAULT_SIZE,
                "min_size": WINDOW_MIN_SIZE
            },
            "performance": {
                "cache_enabled": CACHE_ENABLED,
                "max_execution_time": MAX_EXECUTION_TIME,
                "max_threads": MAX_WORKER_THREADS
            },
            "auto_save": {
                "enabled": AUTO_SAVE_ENABLED,
                "interval": AUTO_SAVE_INTERVAL
            }
        }
    
    def get(self, key: str, default=None):
        """Obtiene un valor de configuración usando notación de punto"""
        keys = key.split('.')
        value = self._settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Establece un valor de configuración usando notación de punto"""
        keys = key.split('.')
        settings = self._settings
        
        # Navegar hasta el último nivel
        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]
        
        # Establecer el valor
        settings[keys[-1]] = value
    
    def load_from_file(self, filepath: Path):
        """Carga configuración desde archivo JSON"""
        try:
            import json
            with open(filepath, 'r', encoding='utf-8') as f:
                file_settings = json.load(f)
                self._merge_settings(file_settings)
        except Exception as e:
            print(f"Error loading config from {filepath}: {e}")
    
    def save_to_file(self, filepath: Path):
        """Guarda configuración a archivo JSON"""
        try:
            import json
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config to {filepath}: {e}")
    
    def _merge_settings(self, new_settings: Dict[str, Any]):
        """Fusiona nuevas configuraciones con las existentes"""
        def merge_dict(base: Dict, new: Dict):
            for key, value in new.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value
        
        merge_dict(self._settings, new_settings)
    
    def reset_to_defaults(self):
        """Resetea toda la configuración a valores por defecto"""
        self._load_defaults()
    
    def get_all(self) -> Dict[str, Any]:
        """Obtiene toda la configuración"""
        return self._settings.copy()

# Instancia global de configuración
config = Config()

# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def get_resource_path(relative_path: str) -> Path:
    """Obtiene la ruta absoluta de un recurso"""
    if hasattr(sys, '_MEIPASS'):
        # Ejecutándose como ejecutable empaquetado
        return Path(sys._MEIPASS) / relative_path
    else:
        # Ejecutándose como script
        return ROOT_DIR / relative_path

def get_user_config_path() -> Path:
    """Obtiene la ruta del archivo de configuración del usuario"""
    return USER_CONFIG_DIR / "config.json"

def load_user_config():
    """Carga la configuración del usuario"""
    user_config_path = get_user_config_path()
    if user_config_path.exists():
        config.load_from_file(user_config_path)

def save_user_config():
    """Guarda la configuración del usuario"""
    user_config_path = get_user_config_path()
    config.save_to_file(user_config_path)

def initialize_config():
    """Inicializa el sistema de configuración"""
    ensure_user_directories()
    load_user_config()

# Inicializar automáticamente al importar
initialize_config()

# =============================================================================
# EXPORTAR CONFIGURACIONES PRINCIPALES
# =============================================================================

__all__ = [
    'APP_NAME', 'APP_VERSION', 'APP_DESCRIPTION',
    'ROOT_DIR', 'DATA_DIR', 'USER_CONFIG_DIR',
    'RENDER_SETTINGS', 'RenderQuality', 'DEFAULT_RENDER_QUALITY',
    'DARK_THEME', 'LIGHT_THEME', 'CURRENT_THEME',
    'NODE_COLORS', 'NODE_VISUAL', 'CONNECTION_VISUAL',
    'GEOMETRY_LIMITS', 'GEOMETRY_TOLERANCE',
    'config', 'initialize_config', 'save_user_config'
]