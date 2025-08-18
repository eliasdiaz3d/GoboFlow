"""
Viewport module for GoboFlow
Contains real-time preview and rendering components
"""

try:
    from .viewport_renderer import (
        ViewportWidget, ViewportRenderer, GeometryRenderer, 
        create_viewport_widget
    )
    VIEWPORT_AVAILABLE = True
except ImportError:
    VIEWPORT_AVAILABLE = False
    ViewportWidget = None
    ViewportRenderer = None
    GeometryRenderer = None
    create_viewport_widget = None

__all__ = [
    'ViewportWidget', 'ViewportRenderer', 'GeometryRenderer',
    'create_viewport_widget', 'VIEWPORT_AVAILABLE'
]