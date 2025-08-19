"""
Configuración de GoboFlow
Define constantes y configuraciones globales
"""

import logging
from pathlib import Path
import json

# Información de la aplicación
APP_NAME = "GoboFlow"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Generador procedural de gobos para iluminación teatral"

# Configuración de ventana
WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION}"
WINDOW_DEFAULT_SIZE = (1200, 800)
WINDOW_MIN_SIZE = (800, 600)

# Directorios
ROOT_DIR = Path(__file__).parent.absolute()
USER_HOME = Path.home()
USER_CONFIG_DIR = USER_HOME / ".goboflow"
USER_LOGS_DIR = USER_CONFIG_DIR / "logs"
USER_PROJECTS_DIR = USER_CONFIG_DIR / "projects"

# Archivos
CONFIG_FILE = USER_CONFIG_DIR / "config.json"
LOG_FILE = USER_LOGS_DIR / "goboflow.log"

# Configuración de logging
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Modo debug
DEBUG_MODE = True

# Tema dark por defecto
DARK_THEME = {
    'background': '#2b2b2b',
    'background_light': '#3c3c3c',
    'foreground': '#ffffff',
    'selection': '#0078d4',
    'border': '#555555',
    'accent': '#0078d4'
}

# Configuración por defecto
DEFAULT_CONFIG = {
    'app': {
        'theme': 'dark',
        'language': 'es',
        'auto_save': True,
        'recent_projects': []
    },
    'render': {
        'quality': 'preview',  # preview, high, ultra
        'anti_aliasing': True,
        'cache_enabled': True
    },
    'nodes': {
        'auto_connect': True,
        'show_grid': True,
        'snap_to_grid': False
    },
    'export': {
        'default_format': 'svg',
        'default_resolution': [1024, 1024],
        'default_dpi': 300
    }
}

# Variable global de configuración
config = DEFAULT_CONFIG.copy()

def ensure_directories():
    """Asegura que los directorios necesarios existan"""
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    USER_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    USER_PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

def load_user_config():
    """Carga la configuración del usuario"""
    global config
    
    ensure_directories()
    
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                
            # Merge con configuración por defecto
            config = merge_configs(DEFAULT_CONFIG, user_config)
            print(f"✅ Configuración cargada desde {CONFIG_FILE}")
        else:
            print(f"📁 Usando configuración por defecto")
            
    except Exception as e:
        print(f"⚠️ Error cargando configuración: {e}")
        config = DEFAULT_CONFIG.copy()

def save_user_config():
    """Guarda la configuración del usuario"""
    ensure_directories()
    
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"💾 Configuración guardada en {CONFIG_FILE}")
        
    except Exception as e:
        print(f"❌ Error guardando configuración: {e}")

def merge_configs(default: dict, user: dict) -> dict:
    """Combina configuración por defecto con configuración de usuario"""
    result = default.copy()
    
    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result

def get_config_value(key_path: str, default_value=None):
    """Obtiene un valor de configuración usando notación de punto"""
    keys = key_path.split('.')
    value = config
    
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default_value

def set_config_value(key_path: str, value):
    """Establece un valor de configuración usando notación de punto"""
    keys = key_path.split('.')
    target = config
    
    for key in keys[:-1]:
        if key not in target:
            target[key] = {}
        target = target[key]
    
    target[keys[-1]] = value

def initialize_config():
    """Inicializa el sistema de configuración"""
    load_user_config()
    
    # Configurar logging
    ensure_directories()
    
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Iniciando {APP_NAME} v{APP_VERSION}")
    logger.info(f"Directorio de configuración: {USER_CONFIG_DIR}")
    
    return logger

def reset_config_to_defaults():
    """Restaura la configuración a valores por defecto"""
    global config
    config = DEFAULT_CONFIG.copy()
    save_user_config()
    print("🔄 Configuración restaurada a valores por defecto")

def get_recent_projects():
    """Obtiene la lista de proyectos recientes"""
    return get_config_value('app.recent_projects', [])

def add_recent_project(project_path: str):
    """Añade un proyecto a la lista de recientes"""
    recent = get_recent_projects()
    
    # Remover si ya existe
    if project_path in recent:
        recent.remove(project_path)
    
    # Añadir al principio
    recent.insert(0, project_path)
    
    # Limitar a 10 proyectos
    recent = recent[:10]
    
    set_config_value('app.recent_projects', recent)
    save_user_config()

def get_theme_colors():
    """Obtiene los colores del tema actual"""
    theme_name = get_config_value('app.theme', 'dark')
    
    if theme_name == 'dark':
        return DARK_THEME
    else:
        # Tema claro (por implementar)
        return {
            'background': '#ffffff',
            'background_light': '#f5f5f5',
            'foreground': '#000000',
            'selection': '#0078d4',
            'border': '#cccccc',
            'accent': '#0078d4'
        }

# Inicializar configuración al importar
if __name__ != "__main__":
    try:
        initialize_config()
    except Exception as e:
        print(f"⚠️ Error inicializando configuración: {e}")

# Para testing
if __name__ == "__main__":
    print("🧪 Probando sistema de configuración...")
    
    # Inicializar
    logger = initialize_config()
    
    # Mostrar configuración actual
    print("\n📋 Configuración actual:")
    for section, values in config.items():
        print(f"  {section}:")
        for key, value in values.items():
            print(f"    {key}: {value}")
    
    # Probar get/set
    print(f"\n🔍 Tema actual: {get_config_value('app.theme')}")
    print(f"🔍 Calidad de render: {get_config_value('render.quality')}")
    
    # Probar proyectos recientes
    add_recent_project("/path/to/project1.gflow")
    add_recent_project("/path/to/project2.gflow")
    print(f"📁 Proyectos recientes: {get_recent_projects()}")
    
    print("\n✅ Tests de configuración completados")