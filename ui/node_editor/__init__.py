"""
Node editor module for GoboFlow - Editor Completo
"""

try:
    from .node_editor_widget import (
        NodeEditorWidget, NodeGraphics, SocketGraphics, 
        ConnectionGraphics, NodeState, create_node_editor
    )
    NODE_EDITOR_AVAILABLE = True
    print("✅ Editor completo cargado")
except ImportError as e:
    print(f"❌ Error cargando editor completo: {e}")
    NODE_EDITOR_AVAILABLE = False
    NodeEditorWidget = None
    NodeGraphics = None
    SocketGraphics = None
    ConnectionGraphics = None
    NodeState = None
    create_node_editor = None

__all__ = [
    'NodeEditorWidget', 'NodeGraphics', 'SocketGraphics', 
    'ConnectionGraphics', 'NodeState', 'create_node_editor',
    'NODE_EDITOR_AVAILABLE'
]