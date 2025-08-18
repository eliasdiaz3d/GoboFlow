"""
UI module for GoboFlow
Contains the graphical user interface components
"""

try:
    from .main_window import GoboFlowMainWindow, create_goboflow_app, run_gui
    UI_AVAILABLE = True
except ImportError:
    UI_AVAILABLE = False
    GoboFlowMainWindow = None
    create_goboflow_app = None
    run_gui = None

__all__ = [
    'GoboFlowMainWindow', 'create_goboflow_app', 'run_gui', 'UI_AVAILABLE'
]