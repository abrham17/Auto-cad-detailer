"""
Foundation-related commands for AutoCAD Structural Plugin
"""
from autocad import Ap, Document, Point3d
from utils.logger import logger

class CreateFoundation:
    """Command to create structural foundations"""
    
    def execute(self):
        """Execute foundation creation command"""
        try:
            foundation_type = self._select_foundation_type()
            if not foundation_type:
                logger.info("Foundation creation cancelled")
                return
                
            if foundation_type == "PAD":
                self._create_pad_foundation()
            elif foundation_type == "STRIP":
                self._create_strip_foundation()
            elif foundation_type == "RAFT":
                self._create_raft_foundation()
            elif foundation_type == "PILE":
                self._create_pile_foundation()
                
        except Exception as e:
            logger.error(f"Error creating foundation: {str(e)}")
            
    def _select_foundation_type(self):
        """Select foundation type from user"""
        try:
            Ap.Prompt("Select foundation type [Pad/Strip/Raft/Pile]: ")
            result = Ap.GetString(False, "")
            if not result:
                return None
                
            foundation_types = {
                'P': 'PAD', 'PAD': 'PAD',
                'S': 'STRIP', 'STRIP': 'STRIP', 
                'R': 'RAFT', 'RAFT': 'RAFT',
                'PI': 'PILE', 'PILE': 'PILE'
            }
            
            return foundation_types.get(result.upper(), 'PAD')
            
        except:
            return 'PAD'
            
    def _create_pad_foundation(self):
        """Create pad foundation"""
        try:
            insertion_point = self._get_insertion_point()
            if not insertion_point:
                return
                
            foundation_data = self._get_pad_parameters()
            foundation_entity = self._create_pad_entity(insertion_point, foundation_data)
            
            if foundation_entity:
                logger.info("Pad foundation created successfully")
                self._sync_foundation_data(foundation_entity, foundation_data)
                
        except Exception as e:
            logger.error(f"Error creating pad foundation: {str(e)}")
            
    def _create_strip_foundation(self):
        """Create strip foundation"""
        try:
            points = self._get_strip_points()
            if not points or len(points) < 2:
                return
                
            foundation_data = self._get_strip_parameters()
            foundation_entity = self._create_strip_entity(points, foundation_data)
            
            if foundation_entity:
                logger.info("Strip foundation created successfully")
                
        except Exception as e:
            logger.error(f"Error creating strip foundation: {str(e)}")
            
    def _create_raft_foundation(self):
        """Create raft foundation"""
        logger.info("Raft foundation creation - similar to slab creation")
        # Implementation similar to slab creation
        
    def _create_pile_foundation(self):
        """Create pile foundation"""
        try:
            location = self._get_insertion_point()
            if not location:
                return
                
            pile_data = self._get_pile_parameters()
            pile_entity = self._create_pile_entity(location, pile_data)
            
            if pile_entity:
                logger.info("Pile foundation created successfully")
                
        except Exception as e:
            logger.error(f"Error creating pile foundation: {str(e)}")
            
    def _get_insertion_point(self):
        """Get foundation insertion point"""
        try:
            point = Ap.GetPoint(None, "Specify foundation location: ")
            return Point3d(point[0], point[1], point[2]) if point else None
        except:
            return None
            
    def _get_pad_parameters(self):
        """Get pad foundation parameters"""
        return {
            'type': 'Pad Foundation',
            'width': 1500,     # mm
            'length': 1500,    # mm
            'depth': 500,      # mm
            'material': 'Concrete',
            'name': f"PAD_{int(Ap.GetTickCount())}"
        }
        
    def _get_strip_parameters(self):
        """Get strip foundation parameters"""
        return {
            'type': 'Strip Foundation',
            'width': 600,      # mm
            'depth': 750,      # mm
            'material': 'Concrete',
            'name': f"STRIP_{int(Ap.GetTickCount())}"
        }
        
    def _get_pile_parameters(self):
        """Get pile foundation parameters"""
        return {
            'type': 'Pile Foundation',
            'diameter': 300,   # mm
            'length': 8000,    # mm
            'material': 'Concrete',
            'name': f"PILE_{int(Ap.GetTickCount())}"
        }
        
    def _get_strip_points(self):
        """Get strip foundation alignment points"""
        points = []
        try:
            Ap.Prompt("Specify strip foundation alignment: ")
            
            start_point = Ap.GetPoint(None, "Start point: ")
            if not start_point:
                return None
                
            points.append(Point3d(start_point[0], start_point[1], start_point[2]))
            current_point = points[0]
            
            while True:
                next_point = Ap.GetPoint(current_point, "Next point: ")
                if not next_point:
                    break
                    
                points.append(Point3d(next_point[0], next_point[1], next_point[2]))
                current_point = points[-1]
                
        except:
            pass
            
        return points if len(points) >= 2 else None
        
    def _create_pad_entity(self, location, foundation_data):
        """Create pad foundation entity"""
        try:
            doc = Document()
            
            # Create pad as 3D solid or block
            # Simplified implementation
            width = foundation_data['width'] / 1000
            length = foundation_data['length'] / 1000
            depth = foundation_data['depth'] / 1000
            
            # Create rectangle for pad footprint
            half_width = width / 2
            half_length = length / 2
            
            points = [
                Point3d(location.X - half_width, location.Y - half_length, location.Z),
                Point3d(location.X + half_width, location.Y - half_length, location.Z),
                Point3d(location.X + half_width, location.Y + half_length, location.Z),
                Point3d(location.X - half_width, location.Y + half_length, location.Z)
            ]
            
            # Create closed polyline
            pline = doc.ModelSpace.AddLightWeightPolyline(
                Ap.Array[Ap.Double]([
                    points[0].X, points[0].Y,
                    points[1].X, points[1].Y,
                    points[2].X, points[2].Y,
                    points[3].X, points[3].Y
                ])
            )
            pline.Closed = True
            pline.Layer = "STRUCTURAL_FOUNDATIONS"
            
            return pline
            
        except Exception as e:
            logger.error(f"Error creating pad entity: {str(e)}")
            return None
            
    def _create_strip_entity(self, points, foundation_data):
        """Create strip foundation entity"""
        # Implementation for strip foundation
        pass
        
    def _create_pile_entity(self, location, pile_data):
        """Create pile foundation entity"""
        # Implementation for pile foundation
        pass
        
    def _sync_foundation_data(self, entity, foundation_data):
        """Sync foundation data with external services"""
        try:
            from services.sync_service import SyncService
            sync_service = SyncService()
            
            sync_data = {
                'type': 'foundation',
                'subtype': foundation_data.get('type', 'Pad'),
                'entity_id': str(entity.Handle),
                'parameters': foundation_data,
                'timestamp': Ap.GetVar("CDATE")
            }
            
            sync_service.queue_for_sync(sync_data)
            
        except Exception as e:
            logger.warning(f"Could not sync foundation data: {str(e)}")


class ModifyFoundation:
    """Command to modify existing foundations"""
    
    def execute(self):
        """Execute foundation modification command"""
        try:
            foundation = self._select_foundation()
            if foundation:
                self._show_modification_dialog(foundation)
        except Exception as e:
            logger.error(f"Error modifying foundation: {str(e)}")
            
    def _select_foundation(self):
        """Select foundation entity"""
        try:
            selection = Ap.GetEntity("Select foundation to modify: ")
            return selection[0] if selection else None
        except:
            return None


class DeleteFoundation:
    """Command to delete foundations"""
    
    def execute(self):
        """Execute foundation deletion command"""
        try:
            foundation = ModifyFoundation()._select_foundation()
            if foundation:
                if self._confirm_deletion():
                    foundation.Delete()
                    logger.info("Foundation deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting foundation: {str(e)}")
            
    def _confirm_deletion(self):
        """Confirm deletion with user"""
        try:
            result = Ap.GetString(False, "Delete selected foundation? [Yes/No]: ")
            return result.upper() in ['Y', 'YES']
        except:
            return False