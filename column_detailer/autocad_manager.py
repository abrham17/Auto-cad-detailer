"""
AutoCAD connection and document management
"""

import win32com.client
import pythoncom
from typing import Optional, List, Dict, Any
import logging

class AutoCADManager:
    """Manages AutoCAD connection and operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.acad_app = None
        self.doc = None
        self.model_space = None
        self.paper_space = None
        self._connected = False
        
    def connect(self) -> bool:
        """Connect to running AutoCAD instance"""
        try:
            self.acad_app = win32com.client.Dispatch("AutoCAD.Application")
            self.doc = self.acad_app.ActiveDocument
            self.model_space = self.doc.ModelSpace
            self.paper_space = self.doc.PaperSpace
            self._connected = True
            
            self.logger.info("Successfully connected to AutoCAD")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to AutoCAD: {e}")
            self._connected = False
            return False
    
    def ensure_connection(self) -> bool:
        """Ensure we have a valid AutoCAD connection"""
        if not self._connected:
            return self.connect()
        return True
    
    def create_layer(self, layer_name: str, color: int = 256) -> bool:
        """Create a layer if it doesn't exist"""
        try:
            layers = self.doc.Layers
            for layer in layers:
                if layer.Name == layer_name:
                    return True
            
            new_layer = layers.Add(layer_name)
            new_layer.Color = color
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create layer {layer_name}: {e}")
            return False
    
    def set_current_layer(self, layer_name: str) -> bool:
        """Set current layer"""
        try:
            self.doc.ActiveLayer = self.doc.Layers.Item(layer_name)
            return True
        except Exception as e:
            self.logger.error(f"Failed to set current layer to {layer_name}: {e}")
            return False
    
    def get_linetype(self, linetype_name: str) -> bool:
        """Load linetype if not present"""
        try:
            linetypes = self.doc.Linetypes
            for lt in linetypes:
                if lt.Name == linetype_name:
                    return True
            
            # Load from ACAD.lin
            linetypes.Load(linetype_name, "acad.lin")
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to load linetype {linetype_name}: {e}")
            return False
    
    def zoom_extents(self):
        """Zoom to extents"""
        try:
            self.acad_app.ZoomExtents()
        except Exception as e:
            self.logger.warning(f"Failed to zoom extents: {e}")
    
    def refresh_view(self):
        """Refresh AutoCAD view"""
        try:
            self.doc.Regen(1)  # 1 = acActiveViewport
        except Exception as e:
            self.logger.warning(f"Failed to refresh view: {e}")

class DrawingContext:
    """Context manager for AutoCAD drawing operations"""
    
    def __init__(self, autocad_manager: AutoCADManager, layer: str = "0"):
        self.autocad = autocad_manager
        self.layer = layer
        self.original_layer = None
        
    def __enter__(self):
        if self.autocad.ensure_connection():
            self.autocad.create_layer(self.layer)
            self.original_layer = self.autocad.doc.ActiveLayer.Name
            self.autocad.set_current_layer(self.layer)
        return self.autocad
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_layer and self.autocad._connected:
            self.autocad.set_current_layer(self.original_layer)
        return False  # Don't suppress exceptions