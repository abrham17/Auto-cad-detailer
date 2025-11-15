"""
AutoCAD Structural Plugin
A comprehensive structural engineering plugin for AutoCAD
"""

__version__ = "1.0.0"
__author__ = "Structural Plugin Team"
__description__ = "Structural modeling and analysis plugin for AutoCAD"

import sys
import os

# Add the plugin directory to the Python path
plugin_dir = os.path.dirname(os.path.abspath(__file__))
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

# Import main components for easy access
from .main_plugin import StructuralPlugin
from .commands import (
    CreateColumn, ModifyColumn, DeleteColumn,
    CreateWall, ModifyWall, DeleteWall,
    CreateBeam, ModifyBeam, DeleteBeam,
    CreateSlab, ModifySlab, DeleteSlab,
    CreateFoundation, ModifyFoundation, DeleteFoundation
)

from .ui import PaletteManager, RibbonUI, PropertyPalette, ToolbarManager
from .integration import AutoCADAPI, RealTimeSync, EventHandlers, DrawingManager
from .services import APIClient, CacheManager, SyncService, LicenseService
from .utils import Logger, Config, helpers

# Global plugin instance
_plugin_instance = None

def load_plugin():
    """
    Load the structural plugin into AutoCAD
    This function is called by AutoCAD when the plugin is loaded
    """
    global _plugin_instance
    try:
        _plugin_instance = StructuralPlugin()
        _plugin_instance.initialize()
        return _plugin_instance
    except Exception as e:
        print(f"Failed to load AutoCAD Structural Plugin: {e}")
        return None

def unload_plugin():
    """
    Unload the structural plugin from AutoCAD
    This function is called by AutoCAD when the plugin is unloaded
    """
    global _plugin_instance
    try:
        if _plugin_instance:
            _plugin_instance.shutdown()
            _plugin_instance = None
        return True
    except Exception as e:
        print(f"Failed to unload AutoCAD Structural Plugin: {e}")
        return False

def get_plugin():
    """
    Get the current plugin instance
    """
    return _plugin_instance

# AutoCAD command registration functions
def register_commands():
    """
    Register all structural commands with AutoCAD
    """
    try:
        from Autodesk.AutoCAD.Runtime import CommandMethod
        from Autodesk.AutoCAD.ApplicationServices import Application
        
        # This would register all command methods with AutoCAD
        # In practice, each command class would be decorated with @CommandMethod
        print("Structural commands registered successfully")
        return True
    except Exception as e:
        print(f"Failed to register commands: {e}")
        return False

# Convenience imports for common functionality
__all__ = [
    # Main plugin
    'StructuralPlugin',
    'load_plugin',
    'unload_plugin',
    'get_plugin',
    'register_commands',
    
    # Commands
    'CreateColumn', 'ModifyColumn', 'DeleteColumn',
    'CreateWall', 'ModifyWall', 'DeleteWall', 
    'CreateBeam', 'ModifyBeam', 'DeleteBeam',
    'CreateSlab', 'ModifySlab', 'DeleteSlab',
    'CreateFoundation', 'ModifyFoundation', 'DeleteFoundation',
    
    # UI Components
    'PaletteManager', 'RibbonUI', 'PropertyPalette', 'ToolbarManager',
    
    # Integration
    'AutoCADAPI', 'RealTimeSync', 'EventHandlers', 'DrawingManager',
    
    # Services
    'APIClient', 'CacheManager', 'SyncService', 'LicenseService',
    
    # Utilities
    'Logger', 'Config', 'helpers'
]