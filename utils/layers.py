"""
Layer management utilities
"""

from typing import Dict, List, Optional
import logging

class LayerManager:
    """Manages AutoCAD layers for column detailing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Standard layer definitions
        self.standard_layers = {
            # Concrete elements
            'concrete': {
                'name': 'CONCRETE',
                'color': 7,  # White
                'linetype': 'Continuous',
                'lineweight': 0.30
            },
            # Reinforcement
            'rebar_main': {
                'name': 'REBAR-MAIN',
                'color': 1,  # Red
                'linetype': 'Continuous',
                'lineweight': 0.25
            },
            'rebar_links': {
                'name': 'REBAR-LINKS',
                'color': 3,  # Green
                'linetype': 'Continuous',
                'lineweight': 0.18
            },
            # Dimensions
            'dimensions': {
                'name': 'DIMENSIONS',
                'color': 4,  # Cyan
                'linetype': 'Continuous',
                'lineweight': 0.18
            },
            # Text
            'text': {
                'name': 'TEXT',
                'color': 7,  # White
                'linetype': 'Continuous',
                'lineweight': 0.18
            },
            # Sections
            'sections': {
                'name': 'SECTIONS',
                'color': 6,  # Magenta
                'linetype': 'Continuous',
                'lineweight': 0.25
            },
            # Hidden lines
            'hidden': {
                'name': 'HIDDEN',
                'color': 9,  # Grey
                'linetype': 'HIDDEN',
                'lineweight': 0.18
            },
            # Center lines
            'center': {
                'name': 'CENTER',
                'color': 1,  # Red
                'linetype': 'CENTER',
                'lineweight': 0.18
            },
            # Construction lines
            'construction': {
                'name': 'CONSTRUCTION',
                'color': 8,  # Dark Grey
                'linetype': 'DASHED',
                'lineweight': 0.13
            }
        }
        
        self.created_layers = set()
    
    def setup_standard_layers(self, autocad_manager) -> bool:
        """Setup all standard layers"""
        try:
            for layer_key, layer_config in self.standard_layers.items():
                self.create_layer(autocad_manager, layer_config)
            
            self.logger.info("All standard layers created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup standard layers: {e}")
            return False
    
    def create_layer(self, autocad_manager, layer_config: Dict) -> bool:
        """Create a single layer"""
        try:
            layer_name = layer_config['name']
            
            # Check if layer already exists
            layers = autocad_manager.doc.Layers
            for layer in layers:
                if layer.Name == layer_name:
                    self.created_layers.add(layer_name)
                    return True
            
            # Create new layer
            new_layer = layers.Add(layer_name)
            new_layer.Color = layer_config.get('color', 7)
            
            # Set linetype if specified
            linetype = layer_config.get('linetype')
            if linetype and linetype != 'Continuous':
                autocad_manager.get_linetype(linetype)
                new_layer.Linetype = linetype
            
            # Set lineweight if specified
            lineweight = layer_config.get('lineweight')
            if lineweight:
                # Convert mm to AutoCAD lineweight (1/100 mm)
                new_layer.Lineweight = int(lineweight * 100)
            
            self.created_layers.add(layer_name)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create layer {layer_config.get('name')}: {e}")
            return False
    
    def set_layer_current(self, autocad_manager, layer_name: str) -> bool:
        """Set a layer as current"""
        try:
            layers = autocad_manager.doc.Layers
            for layer in layers:
                if layer.Name == layer_name:
                    autocad_manager.doc.ActiveLayer = layer
                    return True
            
            self.logger.warning(f"Layer {layer_name} not found")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to set current layer to {layer_name}: {e}")
            return False
    
    def get_layer_names(self) -> List[str]:
        """Get list of all created layer names"""
        return list(self.created_layers)
    
    def get_layer_config(self, layer_key: str) -> Optional[Dict]:
        """Get configuration for a layer by key"""
        return self.standard_layers.get(layer_key)
    
    def create_custom_layer(self, autocad_manager, name: str, color: int = 7, 
                          linetype: str = 'Continuous', lineweight: float = 0.18) -> bool:
        """Create a custom layer"""
        config = {
            'name': name,
            'color': color,
            'linetype': linetype,
            'lineweight': lineweight
        }
        
        return self.create_layer(autocad_manager, config)

class LayerContext:
    """Context manager for layer operations"""
    
    def __init__(self, layer_manager: LayerManager, autocad_manager, layer_key: str):
        self.layer_manager = layer_manager
        self.autocad_manager = autocad_manager
        self.layer_key = layer_key
        self.previous_layer = None
    
    def __enter__(self):
        # Get layer configuration
        layer_config = self.layer_manager.get_layer_config(self.layer_key)
        if layer_config:
            # Ensure layer exists
            self.layer_manager.create_layer(self.autocad_manager, layer_config)
            
            # Store current layer and set new one
            self.previous_layer = self.autocad_manager.doc.ActiveLayer.Name
            self.layer_manager.set_layer_current(self.autocad_manager, layer_config['name'])
        
        return self.autocad_manager
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous layer
        if self.previous_layer:
            self.layer_manager.set_layer_current(self.autocad_manager, self.previous_layer)
        
        return False  # Don't suppress exceptions