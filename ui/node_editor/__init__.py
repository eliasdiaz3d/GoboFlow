"""
Módulo del editor visual de nodos
Implementa el editor gráfico completo con drag & drop
"""

try:
    from .node_editor_widget import (
        NodeEditorWidget, 
        create_node_editor, 
        NODE_EDITOR_AVAILABLE
    )
    
    from .node_graphics import (
        NodeGraphicsItem,
        SocketGraphicsItem, 
        create_node_graphics,
        NodeTheme
    )
    
    from .connection_graphics import (
        ConnectionGraphicsItem,
        ConnectionManager,
        ConnectionValidator
    )
    
    print("✅ Editor visual completo cargado correctamente")
    
except ImportError as e:
    print(f"⚠️ Error cargando editor completo: {e}")
    print("🔄 Intentando cargar editor simplificado como fallback")
    
    try:
        from .node_editor_simple import (
            SimpleNodeEditorWidget as NodeEditorWidget,
            create_simple_node_editor as create_node_editor
        )
        NODE_EDITOR_AVAILABLE = True
        print("✅ Editor simplificado cargado como fallback")
        
    except ImportError as e2:
        print(f"❌ Error cargando editor simplificado: {e2}")
        
        # Fallback final
        NODE_EDITOR_AVAILABLE = False
        NodeEditorWidget = None
        
        def create_node_editor(parent=None):
            print("❌ Editor no disponible")
            return None

__all__ = [
    'NodeEditorWidget',
    'create_node_editor', 
    'NODE_EDITOR_AVAILABLE'
]