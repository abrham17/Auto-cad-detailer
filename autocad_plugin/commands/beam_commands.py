"""
Beam-related commands for AutoCAD Structural Plugin
"""
from autocad import Ap, Document, Point3d
from utils.logger import logger

class CreateBeam:
    """Command to create structural beams"""
    
    def execute(self):
        """Execute beam creation command"""
        try:
            start_point, end_point = self._get_beam_points()
            if not start_point or not end_point:
                logger.info("Beam creation cancelled")
                return
                
            beam_data = self._get_beam_parameters()
            if not beam_data:
                return
                
            beam_entity = self._create_beam_entity(start_point, end_point, beam_data)
            
            if beam_entity:
                logger.info("Beam created successfully")
                self._sync_beam_data(beam_entity, beam_data)
                
        except Exception as e:
            logger.error(f"Error creating beam: {str(e)}")
            
    def _get_beam_points(self):
        """Get beam start and end points"""
        try:
            Ap.Prompt("Specify beam start point: ")
            start = Ap.GetPoint(None, "")
            if not start:
                return None, None
                
            Ap.Prompt("Specify beam end point: ")
            end = Ap.GetPoint(Point3d(start[0], start[1], start[2]), "")
            
            return (Point3d(start[0], start[1], start[2]), 
                    Point3d(end[0], end[1], end[2]) if end else None)
                    
        except:
            return None, None
            
    def _get_beam_parameters(self):
        """Get beam parameters"""
        return {
            'width': 300,      # mm
            'depth': 500,      # mm
            'material': 'Concrete',
            'type': 'Rectangular',
            'reinforcement': 'Standard',
            'name': f"BEAM_{int(Ap.GetTickCount())}"
        }
        
    def _create_beam_entity(self, start_point, end_point, beam_data):
        """Create beam entity in AutoCAD"""
        try:
            doc = Document()
            
            # Create beam as a 3D solid or line with width
            # For simplicity, creating a line on beam layer
            line = doc.ModelSpace.AddLine(start_point, end_point)
            line.Layer = "STRUCTURAL_BEAMS"
            
            # Add beam data as extended data
            self._add_beam_data(line, beam_data, start_point, end_point)
            
            return line
            
        except Exception as e:
            logger.error(f"Error creating beam entity: {str(e)}")
            return None
            
    def _add_beam_data(self, entity, beam_data, start_point, end_point):
        """Add beam data to entity"""
        # Implementation for adding beam structural data
        pass


class ModifyBeam:
    """Command to modify existing beams"""
    
    def execute(self):
        """Execute beam modification command"""
        try:
            beam = self._select_beam()
            if beam:
                self._show_modification_dialog(beam)
        except Exception as e:
            logger.error(f"Error modifying beam: {str(e)}")
            
    def _select_beam(self):
        """Select beam entity"""
        try:
            selection = Ap.GetEntity("Select beam to modify: ")
            return selection[0] if selection else None
        except:
            return None


class DeleteBeam:
    """Command to delete beams"""
    
    def execute(self):
        """Execute beam deletion command"""
        try:
            beam = ModifyBeam()._select_beam()
            if beam:
                if self._confirm_deletion():
                    beam.Delete()
                    logger.info("Beam deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting beam: {str(e)}")
            
    def _confirm_deletion(self):
        """Confirm deletion with user"""
        try:
            result = Ap.GetString(False, "Delete selected beam? [Yes/No]: ")
            return result.upper() in ['Y', 'YES']
        except:
            return False