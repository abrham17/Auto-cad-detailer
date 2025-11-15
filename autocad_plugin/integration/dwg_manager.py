"""
Drawing management utilities for structural plugin
"""
import os
import json
from datetime import datetime

from utils.logger import logger
from utils.config import Config
from integration.autocad_api import AutoCADAPI

class DrawingManager:
    """Manage drawing operations and structural data"""
    
    def __init__(self):
        self.api = AutoCADAPI()
        self.structural_data = {}
        self.drawing_properties = {}
        
    def get_drawing_info(self):
        """Get comprehensive drawing information"""
        try:
            doc = self.api.get_active_document()
            if not doc:
                return None
                
            db = doc.Database
            info = {
                'name': doc.Name,
                'path': db.Filename,
                'units': self.api.get_drawing_units(),
                'created': str(db.TduCreate),
                'modified': str(db.TduUpdate),
                'size': self._get_drawing_size(),
                'layers': self._get_layer_info(),
                'structural_elements': self._count_structural_elements()
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting drawing info: {str(e)}")
            return None
            
    def _get_drawing_size(self):
        """Get drawing extents and size"""
        try:
            doc = self.api.get_active_document()
            if not doc:
                return {}
                
            # This would calculate actual drawing extents
            # Simplified implementation
            return {
                'extents_min': {'x': 0, 'y': 0, 'z': 0},
                'extents_max': {'x': 100, 'y': 100, 'z': 10},
                'area': 10000  # m²
            }
            
        except Exception as e:
            logger.error(f"Error getting drawing size: {str(e)}")
            return {}
            
    def _get_layer_info(self):
        """Get information about structural layers"""
        try:
            structural_layers = [
                'STRUCTURAL_COLUMNS',
                'STRUCTURAL_WALLS',
                'STRUCTURAL_BEAMS', 
                'STRUCTURAL_SLABS',
                'STRUCTURAL_FOUNDATIONS'
            ]
            
            layer_info = {}
            for layer_name in structural_layers:
                layer_info[layer_name] = self._count_entities_on_layer(layer_name)
                
            return layer_info
            
        except Exception as e:
            logger.error(f"Error getting layer info: {str(e)}")
            return {}
            
    def _count_entities_on_layer(self, layer_name):
        """Count entities on specific layer"""
        try:
            # This would actually count entities on the layer
            # Simplified implementation
            return 0
            
        except Exception as e:
            logger.error(f"Error counting entities on layer {layer_name}: {str(e)}")
            return 0
            
    def _count_structural_elements(self):
        """Count all structural elements in drawing"""
        try:
            counts = {
                'columns': self._count_entities_on_layer('STRUCTURAL_COLUMNS'),
                'walls': self._count_entities_on_layer('STRUCTURAL_WALLS'),
                'beams': self._count_entities_on_layer('STRUCTURAL_BEAMS'),
                'slabs': self._count_entities_on_layer('STRUCTURAL_SLABS'),
                'foundations': self._count_entities_on_layer('STRUCTURAL_FOUNDATIONS'),
                'total': 0
            }
            
            counts['total'] = sum(counts.values())
            return counts
            
        except Exception as e:
            logger.error(f"Error counting structural elements: {str(e)}")
            return {}
            
    def export_structural_data(self, export_path=None):
        """Export structural data to external file"""
        try:
            if not export_path:
                export_path = self._generate_export_filename()
                
            structural_data = self._collect_all_structural_data()
            
            if not structural_data:
                logger.warning("No structural data found to export")
                return False
                
            # Prepare export data
            export_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'drawing_name': self.api.document.Name if self.api.document else 'Unknown',
                    'plugin_version': Config.get('plugin_version', '1.0.0')
                },
                'structural_data': structural_data
            }
            
            # Write to file
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            logger.info(f"Structural data exported to: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting structural data: {str(e)}")
            return False
            
    def _generate_export_filename(self):
        """Generate export filename based on drawing name"""
        try:
            drawing_name = "unknown"
            if self.api.document and self.api.document.Name:
                drawing_name = os.path.splitext(self.api.document.Name)[0]
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{drawing_name}_structural_export_{timestamp}.json"
            
            # Use desktop or current directory
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if os.path.exists(desktop):
                return os.path.join(desktop, filename)
            else:
                return filename
                
        except Exception as e:
            logger.error(f"Error generating export filename: {str(e)}")
            return f"structural_export_{int(datetime.now().timestamp())}.json"
            
    def _collect_all_structural_data(self):
        """Collect all structural data from drawing"""
        try:
            structural_data = {
                'columns': [],
                'walls': [],
                'beams': [],
                'slabs': [],
                'foundations': []
            }
            
            # This would iterate through all entities and extract structural data
            # Simplified implementation
            logger.info("Structural data collection would be implemented here")
            
            return structural_data
            
        except Exception as e:
            logger.error(f"Error collecting structural data: {str(e)}")
            return {}
            
    def import_structural_data(self, import_path):
        """Import structural data from external file"""
        try:
            if not os.path.exists(import_path):
                logger.error(f"Import file not found: {import_path}")
                return False
                
            # Read import file
            with open(import_path, 'r') as f:
                import_data = json.load(f)
                
            # Validate import data
            if not self._validate_import_data(import_data):
                logger.error("Invalid import data format")
                return False
                
            # Import structural elements
            success_count = self._import_structural_elements(import_data)
            
            logger.info(f"Successfully imported {success_count} structural elements")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error importing structural data: {str(e)}")
            return False
            
    def _validate_import_data(self, import_data):
        """Validate imported structural data"""
        try:
            required_keys = ['export_info', 'structural_data']
            if not all(key in import_data for key in required_keys):
                return False
                
            # Check structural data structure
            structural_data = import_data.get('structural_data', {})
            expected_types = ['columns', 'walls', 'beams', 'slabs', 'foundations']
            
            return all(key in structural_data for key in expected_types)
            
        except Exception as e:
            logger.error(f"Error validating import data: {str(e)}")
            return False
            
    def _import_structural_elements(self, import_data):
        """Import structural elements from data"""
        try:
            success_count = 0
            structural_data = import_data.get('structural_data', {})
            
            # Import each type of structural element
            for element_type, elements in structural_data.items():
                for element_data in elements:
                    if self._create_element_from_import(element_type, element_data):
                        success_count += 1
                        
            return success_count
            
        except Exception as e:
            logger.error(f"Error importing structural elements: {str(e)}")
            return 0
            
    def _create_element_from_import(self, element_type, element_data):
        """Create structural element from imported data"""
        try:
            # This would create the appropriate element based on type and data
            # Simplified implementation
            logger.info(f"Would create {element_type} from imported data")
            return True
            
        except Exception as e:
            logger.error(f"Error creating element from import: {str(e)}")
            return False
            
    def create_structural_layers(self):
        """Create standard structural layers if they don't exist"""
        try:
            layers = [
                ('STRUCTURAL_COLUMNS', 1),      # Red
                ('STRUCTURAL_WALLS', 2),        # Yellow
                ('STRUCTURAL_BEAMS', 3),        # Green
                ('STRUCTURAL_SLABS', 4),        # Cyan
                ('STRUCTURAL_FOUNDATIONS', 5),  # Blue
                ('STRUCTURAL_DIMENSIONS', 6),   # Magenta
                ('STRUCTURAL_NOTES', 7)         # White
            ]
            
            created_count = 0
            for layer_name, color in layers:
                if self.api.create_layer(layer_name, color=color):
                    created_count += 1
                    
            logger.info(f"Created {created_count} structural layers")
            return created_count
            
        except Exception as e:
            logger.error(f"Error creating structural layers: {str(e)}")
            return 0
            
    def purge_structural_data(self):
        """Remove all structural data from drawing"""
        try:
            # This would remove all structural elements and data
            # Implementation would depend on specific requirements
            logger.warning("Purge structural data functionality would be implemented here")
            return True
            
        except Exception as e:
            logger.error(f"Error purging structural data: {str(e)}")
            return False
            
    def get_drawing_statistics(self):
        """Get detailed statistics about the drawing"""
        try:
            info = self.get_drawing_info()
            if not info:
                return {}
                
            stats = {
                'general': {
                    'drawing_name': info.get('name', 'Unknown'),
                    'file_size': self._get_file_size(info.get('path')),
                    'units': info.get('units', 'Unknown'),
                    'last_modified': info.get('modified', 'Unknown')
                },
                'structural_elements': info.get('structural_elements', {}),
                'layers': info.get('layers', {})
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting drawing statistics: {str(e)}")
            return {}
            
    def _get_file_size(self, file_path):
        """Get file size in human-readable format"""
        try:
            if not file_path or not os.path.exists(file_path):
                return "Unknown"
                
            size_bytes = os.path.getsize(file_path)
            
            # Convert to appropriate unit
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.2f} {unit}"
                size_bytes /= 1024.0
                
            return f"{size_bytes:.2f} TB"
            
        except Exception as e:
            logger.error(f"Error getting file size: {str(e)}")
            return "Unknown"
            
    def backup_drawing(self, backup_dir=None):
        """Create a backup of the current drawing"""
        try:
            doc = self.api.get_active_document()
            if not doc or not doc.Database.Filename:
                logger.error("No drawing file to backup")
                return False
                
            original_path = doc.Database.Filename
            if not original_path:
                logger.error("Drawing has not been saved")
                return False
                
            # Determine backup directory
            if not backup_dir:
                backup_dir = os.path.join(os.path.dirname(original_path), "backups")
                
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create backup filename
            basename = os.path.splitext(os.path.basename(original_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"{basename}_backup_{timestamp}.dwg")
            
            # Save copy (this would use proper AutoCAD save methods)
            logger.info(f"Backup would be created at: {backup_path}")
            # Implementation would use proper AutoCAD API for saving copies
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating drawing backup: {str(e)}")
            return False