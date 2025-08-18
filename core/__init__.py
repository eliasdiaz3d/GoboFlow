"""
Core module of GoboFlow
Contains the fundamental node system and execution engine
"""

from .node_system import Node, Socket, Connection, NodeGraph, NodeState, SocketDirection

__all__ = [
    'Node', 'Socket', 'Connection', 'NodeGraph', 
    'NodeState', 'SocketDirection'
]