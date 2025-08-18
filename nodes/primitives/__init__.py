"""
Primitive shape nodes for GoboFlow
Contains nodes that generate basic geometric shapes
"""

from .circle_node import CircleNode, CircleGeometry, CIRCLE_NODE_REGISTRY
from .rectangle_node import RectangleNode, RectangleGeometry, RECTANGLE_NODE_REGISTRY

# Combinar registros
PRIMITIVES_REGISTRY = {
    **CIRCLE_NODE_REGISTRY,
    **RECTANGLE_NODE_REGISTRY
}

__all__ = [
    'CircleNode', 'CircleGeometry', 'CIRCLE_NODE_REGISTRY',
    'RectangleNode', 'RectangleGeometry', 'RECTANGLE_NODE_REGISTRY',
    'PRIMITIVES_REGISTRY'
]