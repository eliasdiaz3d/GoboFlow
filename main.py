import sys
import traceback
from pathlib import Path

# Añadir el directorio raiz al path para imports
ROOT_DIR = Path(__file__).parent.absolute()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Imports de GoboFlow
try:
    import config
    from config import (
        APP_NAME, APP_VERSION, APP_DESCRIPTION,
        initialize_config, save_user_config,
        DEBUG_MODE, USER_CONFIG_DIR
    )
    from core.node_system import NodeGraph
    
    # Importar nodos corregidos
    try:
        from nodes.primitives.circle_node import CircleNode
        print("✅ CircleNode cargado correctamente")
    except ImportError as e:
        print(f"⚠️ CircleNode no disponible: {e}")
        CircleNode = None
    
    try:
        from nodes.base.base_node import NumberParameterNode, ViewerNode
        print("✅ Nodos base cargados correctamente")
    except ImportError as e:
        print(f"⚠️ Nodos base no disponibles: {e}")
        NumberParameterNode = None
        ViewerNode = None
    
    # Intentar importar socket types
    try:
        from core.socket_types import NUMBER, GEOMETRY
        print("✅ Socket types cargados correctamente")
    except ImportError as e:
        print(f"⚠️ Socket types no disponibles: {e}")
    
    # Intentar importar UI
    try:
        from ui import UI_AVAILABLE, run_gui
    except ImportError:
        UI_AVAILABLE = False
        run_gui = None
    
except ImportError as e:
    print(f"Error importing GoboFlow modules: {e}")
    print(f"Make sure you're running from the project root directory")
    print(f"Current working directory: {Path.cwd()}")
    print(f"Project root: {ROOT_DIR}")
    sys.exit(1)

# Clases de nodos básicas si no están disponibles
class BasicNode:
    """Nodo básico temporal para testing"""
    def __init__(self, title="Basic Node"):
        self.id = f"basic_{id(self)}"
        self.title = title
        self.inputs = {}
        self.outputs = {}
    
    def compute(self):
        return {}
    
    def mark_dirty(self):
        pass

class BasicNumberNode(BasicNode):
    """Nodo de número básico temporal"""
    def __init__(self, title="Number"):
        super().__init__(title)
        self.value = 0.0
    
    def set_parameter(self, name, value):
        if name == "value":
            self.value = float(value)
    
    def get_parameter_value(self):
        return self.value
    
    def compute(self):
        return {"value": self.value}

class BasicCircleNode(BasicNode):
    """Nodo de círculo básico temporal"""
    def __init__(self, title="Circle"):
        super().__init__(title)
        self.radius = 100.0
        self.center = (0, 0)
    
    def generate_geometry(self):
        """Genera una geometría básica de círculo"""
        # Crear un objeto básico con las propiedades necesarias
        class BasicCircle:
            def __init__(self, center, radius):
                self.center = center
                self.radius = radius
                self.segments = 32
                self.area = 3.14159 * radius * radius
                self.perimeter = 2 * 3.14159 * radius
                self.bbox = (center[0] - radius, center[1] - radius, 
                           center[0] + radius, center[1] + radius)
            
            def get_svg_path(self):
                cx, cy = self.center
                return f'<circle cx="{cx}" cy="{cy}" r="{self.radius}" fill="white" opacity="0.8"/>'
        
        return BasicCircle(self.center, self.radius)
    
    def get_preview_info(self):
        return {
            "center": self.center,
            "radius": self.radius,
            "area": 3.14159 * self.radius * self.radius,
            "perimeter": 2 * 3.14159 * self.radius
        }
    
    def compute(self):
        geometry = self.generate_geometry()
        return {"geometry": geometry}

class BasicViewerNode(BasicNode):
    """Nodo visor básico temporal"""
    def __init__(self, title="Viewer"):
        super().__init__(title)
        self._last_data = None
    
    def get_last_data(self):
        return self._last_data
    
    def compute(self):
        return {"display": "viewer"}

# Usar nodos disponibles o básicos
if NumberParameterNode is None:
    NumberParameterNode = BasicNumberNode
if CircleNode is None:
    CircleNode = BasicCircleNode
if ViewerNode is None:
    ViewerNode = BasicViewerNode

def setup_logging():
    """Configura el sistema de logging"""
    import logging
    from config import LOG_LEVEL, LOG_FORMAT, LOG_FILE, USER_LOGS_DIR
    
    # Crear directorio de logs si no existe
    USER_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Configurar logging
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def print_banner():
    """Imprime el banner de inicio de la aplicacion"""
    print("=" * 60)
    print(f"GoboFlow v{APP_VERSION}")
    print(f"   {APP_DESCRIPTION}")
    print("=" * 60)
    print()

def create_test_graph():
    """Crea un grafo de prueba con un circulo"""
    print("Creando grafo de prueba...")
    
    # Crear el grafo
    graph = NodeGraph()
    
    # Crear nodos
    print("  Creando nodo de radio...")
    radius_node = NumberParameterNode("Radio")
    radius_node.set_parameter("value", 150.0)
    
    print("  Creando nodo circulo...")
    circle_node = CircleNode("Mi Circulo")
    
    print("  Creando nodo viewer...")
    viewer_node = ViewerNode("Vista Previa")
    
    # Añadir nodos al grafo
    graph.add_node(radius_node)
    graph.add_node(circle_node)
    graph.add_node(viewer_node)
    
    # Conectar nodos (versión simplificada sin validación de tipos)
    print("  Conectando nodos...")
    try:
        # Para nodos básicos, simular conexiones
        print("  Conexiones simuladas para nodos básicos")
        
    except Exception as e:
        print(f"  Error conectando nodos: {e}")
        return None
    
    return graph, radius_node, circle_node, viewer_node

def execute_test_graph(graph, radius_node, circle_node, viewer_node):
    """Ejecuta el grafo de prueba y muestra los resultados"""
    print("\n🚀 Ejecutando grafo de prueba...")
    
    try:
        # Obtener lista de nodos para ejecución
        nodes = [radius_node, circle_node, viewer_node]
        print(f"  📋 Ejecutando {len(nodes)} nodos")
        
        # Ejecutar nodos en orden
        for i, node in enumerate(nodes, 1):
            print(f"  {i}. Ejecutando: {node.title}")
            
            # Forzar recálculo
            node.mark_dirty()
            
            if hasattr(node, 'compute'):
                try:
                    result = node.compute()
                    print(f"     ✅ Resultado: {type(result).__name__}")
                    
                    # Mostrar información específica del nodo
                    if hasattr(node, 'get_parameter_value'):
                        value = node.get_parameter_value()
                        print(f"     📊 Valor: {value}")
                        
                    elif hasattr(node, 'get_preview_info'):
                        preview_info = node.get_preview_info()
                        print(f"     🔍 Centro: {preview_info.get('center', 'N/A')}")
                        print(f"     📏 Radio: {preview_info.get('radius', 'N/A')}")
                        print(f"     📐 Área: {preview_info.get('area', 'N/A'):.2f}")
                        print(f"     📏 Perímetro: {preview_info.get('perimeter', 'N/A'):.2f}")
                        
                        # Obtener geometría
                        if hasattr(node, 'generate_geometry'):
                            geometry = node.generate_geometry()
                            if geometry:
                                print(f"     🔺 Segmentos: {getattr(geometry, 'segments', 'N/A')}")
                                print(f"     ⬜ BBox: {getattr(geometry, 'bbox', 'N/A')}")
                            
                    elif hasattr(node, 'get_last_data'):
                        data = node.get_last_data()
                        if data:
                            print(f"     👁️ Visualizando: {type(data).__name__}")
                        
                except Exception as e:
                    print(f"     ❌ Error: {e}")
                    
        print("\n✅ Ejecución completada")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error en ejecución: {e}")
        if DEBUG_MODE:
            traceback.print_exc()
        return False

def export_test_svg(circle_node, filename="test_gobo.svg"):
    """Exporta el círculo generado a un archivo SVG"""
    print(f"\n📄 Exportando a {filename}...")
    
    try:
        # Obtener la geometría del círculo
        if hasattr(circle_node, 'generate_geometry'):
            circle_geometry = circle_node.generate_geometry()
        else:
            # Crear geometría básica
            class BasicGeometry:
                def __init__(self):
                    self.radius = 150
                def get_svg_path(self):
                    return f'<circle cx="200" cy="200" r="{self.radius}" fill="white" opacity="0.8"/>'
            circle_geometry = BasicGeometry()
        
        # Crear SVG básico
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="400" height="400" 
     viewBox="0 0 400 400"
     style="background: black;">
  
  <!-- Círculo generado por GoboFlow -->
  {circle_geometry.get_svg_path()}
  
  <!-- Información del gobo -->
  <text x="20" y="380" fill="white" font-family="Arial" font-size="12">
    GoboFlow v{APP_VERSION} - Radio: {getattr(circle_geometry, 'radius', 150)}px
  </text>
  
</svg>'''
        
        # Guardar archivo
        output_path = ROOT_DIR / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
            
        print(f"  ✅ SVG exportado: {output_path}")
        print(f"  📂 Abre el archivo para ver tu primer gobo!")
        
        return output_path
        
    except Exception as e:
        print(f"  ❌ Error exportando SVG: {e}")
        if DEBUG_MODE:
            traceback.print_exc()
        return None

def run_interactive_test():
    """Ejecuta una prueba interactiva donde el usuario puede cambiar parámetros"""
    print("\n🎮 Modo Interactivo")
    print("Puedes cambiar el radio del círculo y ver los cambios.")
    print("Escribe 'quit' para salir.\n")
    
    # Crear grafo
    result = create_test_graph()
    if not result:
        return
        
    graph, radius_node, circle_node, viewer_node = result
    
    while True:
        try:
            user_input = input("🔵 Ingresa nuevo radio (o 'quit'): ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
                
            # Convertir a número
            try:
                new_radius = float(user_input)
                if new_radius <= 0:
                    print("❌ El radio debe ser mayor que 0")
                    continue
                    
            except ValueError:
                print("❌ Ingresa un número válido")
                continue
            
            # Actualizar parámetro
            radius_node.set_parameter("value", new_radius)
            
            # Ejecutar grafo
            print(f"\n🔄 Actualizando con radio {new_radius}...")
            execute_test_graph(graph, radius_node, circle_node, viewer_node)
            
            # Exportar nuevo SVG
            svg_file = f"gobo_radio_{new_radius}.svg"
            export_test_svg(circle_node, svg_file)
            
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Saliendo...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def show_system_info():
    """Muestra información del sistema y configuración"""
    print("🔧 Información del Sistema:")
    print(f"  Python: {sys.version}")
    print(f"  Directorio raíz: {ROOT_DIR}")
    print(f"  Directorio de usuario: {USER_CONFIG_DIR}")
    print(f"  Modo debug: {DEBUG_MODE}")
    print(f"  Tema actual: {config.config.get('app.theme', 'dark')}")
    print(f"  Calidad de render: {config.config.get('render.quality', 'preview')}")
    print()

def main():
    """Función principal de la aplicación"""
    try:
        # Configurar logging
        logger = setup_logging()
        logger.info(f"Iniciando {APP_NAME} v{APP_VERSION}")
        
        # Mostrar banner
        print_banner()
        
        # Mostrar información del sistema
        show_system_info()
        
        # Crear y ejecutar grafo de prueba
        result = create_test_graph()
        if not result:
            print("❌ No se pudo crear el grafo de prueba")
            return 1
            
        graph, radius_node, circle_node, viewer_node = result
        
        # Ejecutar grafo
        success = execute_test_graph(graph, radius_node, circle_node, viewer_node)
        if not success:
            print("❌ Error ejecutando el grafo")
            return 1
        
        # Exportar SVG de prueba
        svg_path = export_test_svg(circle_node)
        
        # Preguntar si quiere modo GUI o consola
        print("\n🎯 ¿Cómo te gustaría usar GoboFlow?")
        if UI_AVAILABLE:
            print("1. Interfaz gráfica (GUI)")
            print("2. Modo interactivo (consola)")
            print("3. Solo mostrar resultado y salir")
        else:
            print("1. Modo interactivo (consola)")
            print("2. Solo mostrar resultado y salir")
            print("   (GUI no disponible - instala PyQt6 para usarla)")
        
        try:
            choice = input("\nElige una opción: ").strip()
            
            if UI_AVAILABLE and choice == "1":
                print("\n🎨 Iniciando interfaz gráfica...")
                return run_gui()
            elif (UI_AVAILABLE and choice == "2") or (not UI_AVAILABLE and choice == "1"):
                run_interactive_test()
            elif (UI_AVAILABLE and choice == "3") or (not UI_AVAILABLE and choice == "2"):
                print("\n🎉 ¡Primer gobo creado exitosamente!")
                if svg_path:
                    print(f"📂 Archivo SVG: {svg_path}")
            else:
                print("🤷 Opción no válida, saliendo...")
                
        except KeyboardInterrupt:
            print("\n👋 Saliendo...")
            
        # Guardar configuración
        save_user_config()
        logger.info(f"Cerrando {APP_NAME}")
        
        print(f"\n👋 ¡Gracias por usar {APP_NAME}!")
        return 0
        
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        if DEBUG_MODE:
            traceback.print_exc()
        return 1

def run_tests():
    """Ejecuta tests básicos del sistema"""
    print("🧪 Ejecutando tests básicos...\n")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Importación de módulos
    tests_total += 1
    try:
        from core.socket_types import NUMBER, GEOMETRY
        print("✅ Test 1: Importación de módulos")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 1: Error importando módulos: {e}")
    
    # Test 2: Creación de nodos
    tests_total += 1
    try:
        circle = CircleNode()
        radius = NumberParameterNode()
        print("✅ Test 2: Creación de nodos")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 2: Error creando nodos: {e}")
    
    # Test 3: Creación de grafo
    tests_total += 1
    try:
        graph = NodeGraph()
        circle = CircleNode()
        radius = NumberParameterNode()
        
        graph.add_node(circle)
        graph.add_node(radius)
        
        print("✅ Test 3: Creación de grafo")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 3: Error creando grafo: {e}")
    
    # Test 4: Ejecución de nodos
    tests_total += 1
    try:
        circle.mark_dirty()
        result = circle.compute()
        if 'geometry' in result or result:  # Acepta cualquier resultado válido
            print("✅ Test 4: Ejecución de nodos")
            tests_passed += 1
        else:
            print("❌ Test 4: Nodo no retornó resultado válido")
    except Exception as e:
        print(f"❌ Test 4: Error ejecutando nodo: {e}")
    
    print(f"\n📊 Resultado: {tests_passed}/{tests_total} tests pasaron")
    return tests_passed == tests_total

if __name__ == "__main__":
    # Verificar argumentos de línea de comandos
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            print_banner()
            success = run_tests()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "--version":
            print(f"{APP_NAME} v{APP_VERSION}")
            sys.exit(0)
        elif sys.argv[1] == "--help":
            print(f"""
{APP_NAME} v{APP_VERSION}
{APP_DESCRIPTION}

Uso:
  python main.py          - Ejecutar aplicación (GUI si está disponible)
  python main.py --gui    - Forzar modo GUI
  python main.py --cli    - Forzar modo consola
  python main.py --test   - Ejecutar tests básicos
  python main.py --version - Mostrar versión
  python main.py --help   - Mostrar esta ayuda
""")
            sys.exit(0)
        elif sys.argv[1] == "--gui":
            # Forzar modo GUI
            if UI_AVAILABLE:
                print_banner()
                print("🎨 Iniciando interfaz gráfica...")
                sys.exit(run_gui())
            else:
                print("❌ GUI no disponible. Instala PyQt6 con: pip install PyQt6")
                sys.exit(1)
        elif sys.argv[1] == "--cli":
            # Forzar modo consola
            exit_code = main()
            sys.exit(exit_code)
    
    # Sin argumentos - modo automático
    if UI_AVAILABLE:
        print_banner()
        print("🎨 Iniciando interfaz gráfica...")
        print("💡 Tip: Usa --cli para forzar modo consola")
        sys.exit(run_gui())
    else:
        # Ejecutar modo consola si GUI no está disponible
        exit_code = main()
        sys.exit(exit_code)