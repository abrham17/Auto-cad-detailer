"""
Wall-related commands for AutoCAD Structural Plugin
"""
from autocad import Ap, Document, Point3d
from utils.logger import logger

class CreateWall:
    """Command to create structural walls"""
    
    def execute(self):
        """Execute wall creation command"""
        try:
            points = self._get_wall_points()
            if not points or len(points) < 2:
                logger.info("Wall creation cancelled or insufficient points")
                return
                
            wall_data = self._get_wall_parameters()
            if not wall_data:
                return
                
            wall_entity = self._create_wall_entity(points, wall_data)
            
            if wall_entity:
                logger.info("Wall created successfully")
                self._sync_wall_data(wall_entity, wall_data, points)
                
        except Exception as e:
            logger.error(f"Error creating wall: {str(e)}")
            
    def _get_wall_points(self):
        """Get wall points from user input"""
        points = []
        try:
            Ap.Prompt("Specify wall start point: ")
            start_point = Ap.GetPoint(None, "")
            if not start_point:
                return None
                
            points.append(Point3d(start_point[0], start_point[1], start_point[2]))
            
            while True:
                Ap.Prompt("Specify next point or [Close/Undo]: ")
                next_point = Ap.GetPoint(points[-1], "")
                
                if not next_point:
                    break
                    
                points.append(Point3d(next_point[0], next_point[1], next_point[2]))
                
        except:
            pass
            
        return points if len(points) >= 2 else None
        
    def _get_wall_parameters(self):
        """Get wall parameters"""
        return {
            'thickness': 200,  # mm
            'height': 3000,    # mm
            'material': 'Concrete',
            'type': 'Shear Wall',
            'name': f"WALL_{int(Ap.GetTickCount())}"
        }
        
    def _create_wall_entity(self, points, wall_data):
        """Create wall entity in AutoCAD"""
        try:
            # Create wall as polyline or 3D solid
            doc = Document()
            
            # Convert points to 2D for polyline (simplified)
            points_2d = [Ap.Array[Ap.Double]([p.X, p.Y]) for p in points]
            
            # Create polyline for wall centerline
            pline = doc.ModelSpace.AddLightWeightPolyline(
                Ap.Array[Ap.Double]([coord for point in points_2d for coord in point])
            )
            
            pline.Layer = "STRUCTURAL_WALLS"
            pline.ConstantWidth = wall_data['thickness'] / 1000  # Convert to meters
            
            # Add elevation data
            self._add_wall_elevation_data(pline, wall_data)
            
            return pline
            
        except Exception as e:
            logger.error(f"Error creating wall entity: {str(e)}")
            return None
            
    def _add_wall_elevation_data(self, entity, wall_data):
        """Add elevation data to wall entity"""
        # Implementation for adding elevation information
        pass


class ModifyWall:
    """Command to modify existing walls"""
    
    def execute(self):
        """Execute wall modification command"""
        try:
            wall = self._select_wall()
            if wall:
                self._show_modification_dialog(wall)
        except Exception as e:
            logger.error(f"Error modifying wall: {str(e)}")
            
    def _select_wall(self):
        """Select wall entity"""
        try:
            selection = Ap.GetEntity("Select wall to modify: ")
            return selection[0] if selection else None
        except:
            return None
            
    def _show_modification_dialog(self, wall):
        """Show modification dialog"""
        logger.info("Wall modification dialog would appear here")


class DeleteWall:
    """Command to delete walls"""
    
    def execute(self):
        """Execute wall deletion command"""
        try:
            wall = ModifyWall()._select_wall()
            if wall:
                if self._confirm_deletion():
                    wall.Delete()
                    logger.info("Wall deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting wall: {str(e)}")
            
    def _confirm_deletion(self):
        """Confirm deletion with user"""
        try:
            result = Ap.GetString(False, "Delete selected wall? [Yes/No]: ")
            return result.upper() in ['Y', 'YES']
        except:
            return False