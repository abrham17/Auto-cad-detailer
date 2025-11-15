"""
Slab-related commands for AutoCAD Structural Plugin
"""
from autocad import Ap, Document, Point3d
from utils.logger import logger

class CreateSlab:
    """Command to create structural slabs"""
    
    def execute(self):
        """Execute slab creation command"""
        try:
            boundary = self._get_slab_boundary()
            if not boundary or len(boundary) < 3:
                logger.info("Slab creation cancelled or invalid boundary")
                return
                
            slab_data = self._get_slab_parameters()
            if not slab_data:
                return
                
            slab_entity = self._create_slab_entity(boundary, slab_data)
            
            if slab_entity:
                logger.info("Slab created successfully")
                self._sync_slab_data(slab_entity, slab_data)
                
        except Exception as e:
            logger.error(f"Error creating slab: {str(e)}")
            
    def _get_slab_boundary(self):
        """Get slab boundary points from user"""
        points = []
        try:
            Ap.Prompt("Specify slab boundary points (closed polygon): ")
            
            first_point = Ap.GetPoint(None, "First point: ")
            if not first_point:
                return None
                
            points.append(Point3d(first_point[0], first_point[1], first_point[2]))
            current_point = points[0]
            
            point_index = 2
            while True:
                Ap.Prompt(f"Point {point_index} or [Close]: ")
                next_point = Ap.GetPoint(current_point, "")
                
                if not next_point:
                    # Close the boundary
                    if len(points) >= 3:
                        points.append(points[0])  # Close the polygon
                    break
                    
                points.append(Point3d(next_point[0], next_point[1], next_point[2]))
                current_point = points[-1]
                point_index += 1
                
        except:
            pass
            
        return points if len(points) >= 4 else None  # At least triangle + closure
        
    def _get_slab_parameters(self):
        """Get slab parameters"""
        return {
            'thickness': 150,      # mm
            'material': 'Concrete',
            'type': 'Floor Slab',
            'reinforcement': 'Mesh A142',
            'name': f"SLAB_{int(Ap.GetTickCount())}"
        }
        
    def _create_slab_entity(self, boundary, slab_data):
        """Create slab entity in AutoCAD"""
        try:
            doc = Document()
            
            # Create closed polyline for slab boundary
            points_2d = [Ap.Array[Ap.Double]([p.X, p.Y]) for p in boundary]
            flat_points = [coord for point in points_2d for coord in point]
            
            pline = doc.ModelSpace.AddLightWeightPolyline(
                Ap.Array[Ap.Double](flat_points)
            )
            
            pline.Closed = True
            pline.Layer = "STRUCTURAL_SLABS"
            
            # Add thickness data
            self._add_slab_thickness_data(pline, slab_data)
            
            return pline
            
        except Exception as e:
            logger.error(f"Error creating slab entity: {str(e)}")
            return None
            
    def _add_slab_thickness_data(self, entity, slab_data):
        """Add slab thickness and other data"""
        # Implementation for adding slab structural data
        pass


class ModifySlab:
    """Command to modify existing slabs"""
    
    def execute(self):
        """Execute slab modification command"""
        try:
            slab = self._select_slab()
            if slab:
                self._show_modification_dialog(slab)
        except Exception as e:
            logger.error(f"Error modifying slab: {str(e)}")
            
    def _select_slab(self):
        """Select slab entity"""
        try:
            selection = Ap.GetEntity("Select slab to modify: ")
            return selection[0] if selection else None
        except:
            return None


class DeleteSlab:
    """Command to delete slabs"""
    
    def execute(self):
        """Execute slab deletion command"""
        try:
            slab = ModifySlab()._select_slab()
            if slab:
                if self._confirm_deletion():
                    slab.Delete()
                    logger.info("Slab deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting slab: {str(e)}")
            
    def _confirm_deletion(self):
        """Confirm deletion with user"""
        try:
            result = Ap.GetString(False, "Delete selected slab? [Yes/No]: ")
            return result.upper() in ['Y', 'YES']
        except:
            return False