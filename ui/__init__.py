"""
Módulo UI de GoboFlow
Inicialización del sistema de interfaz de usuario
"""

# Verificar disponibilidad de PyQt6
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    UI_AVAILABLE = True
    
    # Importar componentes UI si están disponibles
    try:
        from .main_window import run_gui
        print("✅ GUI completa disponible")
    except ImportError as e:
        print(f"⚠️ GUI completa no disponible: {e}")
        print("🔄 Usando GUI simplificada")
        
        def run_gui():
            print("❌ GUI completa no implementada")
            return 1
    
except ImportError:
    UI_AVAILABLE = False
    print("⚠️ PyQt6 no disponible - modo GUI deshabilitado")
    
    def run_gui():
        print("❌ GUI no disponible. Instala PyQt6 con: pip install PyQt6")
        return 1

__all__ = ['UI_AVAILABLE', 'run_gui']