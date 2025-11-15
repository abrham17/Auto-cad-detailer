"""
Column-related commands for AutoCAD Structural Plugin
"""
import math
from autocad import Ap, Application, Document, Point3d
from utils.logger import logger
from utils.helpers import validate_point, calculate_distance

class CreateColumn:
    """Command to create structural columns"""
    
    def __init__(self):
        self.name = "CREATE_COLUMN"
        self.description = "Create structural column at specified location"
        
    def execute(self):
        """Execute column creation command"""
        try:
            doc = Document()
            if not doc:
                logger.error("No active document found")
                return
                
            # Get insertion point from user
            insertion_point = self._get_insertion_point()
            if not insertion_point:
                logger.info("Column creation cancelled by user")
                return
                
            # Get column parameters
            column_data = self._get_column_parameters()
            if not column_data:
                return
                
            # Create column in AutoCAD
            column_entity = self._create_column_entity(insertion_point, column_data)
            
            if column_entity:
                logger.info(f"Column created successfully at {insertion_point}")
                # Sync with external service if needed
                self._sync_column_data(column_entity, column_data)
                
        except Exception as e:
            logger.error(f"Error creating column: {str(e)}")
            
    def _get_insertion_point(self):
        """Get column insertion point from user input"""
        try:
            point = Ap.GetPoint(None, "Specify column insertion point: ")
            return Point3d(point[0], point[1], point[2]) if point else None
        except:
            return None
            
    def _get_column_parameters(self):
        """Get column parameters from user or palette"""
        try:
            # Default values
            column_data = {
                'width': 400,  # mm
                'depth': 400,  # mm
                'height': 3000,  # mm
                'material': 'Concrete',
                'grade': 'C30',
                'reinforcement_ratio': 0.02,
                'name': f"COL_{int(Ap.GetTickCount())}"
            }
            
            # In practice, this would show a dialog or use property palette
            logger.info("Using default column parameters. Implement UI for custom parameters.")
            
            return column_data
            
        except Exception as e:
            logger.error(f"Error getting column parameters: {str(e)}")
            return None
            
    def _create_column_entity(self, insertion_point, column_data):
        """Create actual column entity in AutoCAD"""
        try:
            # Create column as a 3D solid or block
            width = column_data['width'] / 1000  # Convert to meters
            depth = column_data['depth'] / 1000
            height = column_data['height'] / 1000
            
            # Calculate corner points
            half_width = width / 2
            half_depth = depth / 2
            
            points = [
                Point3d(insertion_point.X - half_width, insertion_point.Y - half_depth, insertion_point.Z),
                Point3d(insertion_point.X + half_width, insertion_point.Y - half_depth, insertion_point.Z),
                Point3d(insertion_point.X + half_width, insertion_point.Y + half_depth, insertion_point.Z),
                Point3d(insertion_point.X - half_width, insertion_point.Y + half_depth, insertion_point.Z)
            ]
            
            # Create column solid (simplified - actual implementation would use proper 3D solid creation)
            # This is a conceptual implementation
            column = doc.ModelSpace.AddBox(
                insertion_point, 
                width, 
                depth, 
                height
            )
            
            # Add extended data for structural information
            self._add_structural_data(column, column_data)
            
            return column
            
        except Exception as e:
            logger.error(f"Error creating column entity: {str(e)}")
            return None
            
    def _add_structural_data(self, entity, column_data):
        """Add structural data as extended entity data"""
        try:
            # Add custom data to entity for structural properties
            xdata = entity.GetXData("STRUCTURAL_COLUMN")
            if not xdata:
                # Create new xdata
                pass
                
            # Set properties like material, reinforcement, etc.
            entity.Layer = "STRUCTURAL_COLUMNS"
            
        except Exception as e:
            logger.error(f"Error adding structural data: {str(e)}")
            
    def _sync_column_data(self, entity, column_data):
        """Sync column data with external services"""
        try:
            from services.sync_service import SyncService
            sync_service = SyncService()
            
            # Prepare data for sync
            sync_data = {
                'type': 'column',
                'entity_id': str(entity.Handle),
                'parameters': column_data,
                'timestamp': Ap.GetVar("CDATE")
            }
            
            sync_service.queue_for_sync(sync_data)
            
        except Exception as e:
            logger.warning(f"Could not sync column data: {str(e)}")


class ModifyColumn:
    """Command to modify existing columns"""
    
    def execute(self):
        """Execute column modification command"""
        try:
            column = self._select_column()
            if not column:
                logger.info("No column selected")
                return
                
            # Get new parameters
            new_parameters = self._get_modification_parameters()
            if new_parameters:
                self._apply_modifications(column, new_parameters)
                
        except Exception as e:
            logger.error(f"Error modifying column: {str(e)}")
            
    def _select_column(self):
        """Select column entity"""
        try:
            selection = Ap.GetEntity("Select column to modify: ")
            return selection[0] if selection else None
        except:
            return None
            
    def _get_modification_parameters(self):
        """Get modification parameters from user"""
        # Implementation for parameter dialog
        logger.info("Column modification parameters dialog would appear here")
        return {}


class DeleteColumn:
    """Command to delete columns"""
    
    def execute(self):
        """Execute column deletion command"""
        try:
            column = self._select_column()
            if column:
                # Confirm deletion
                if self._confirm_deletion():
                    column.Delete()
                    logger.info("Column deleted successfully")
                    
        except Exception as e:
            logger.error(f"Error deleting column: {str(e)}")
            
    def _select_column(self):
        """Select column entity"""
        return ModifyColumn()._select_column()
        
    def _confirm_deletion(self):
        """Confirm deletion with user"""
        try:
            result = Ap.GetString(False, "Delete selected column? [Yes/No]: ")
            return result.upper() in ['Y', 'YES']
        except:
            return False