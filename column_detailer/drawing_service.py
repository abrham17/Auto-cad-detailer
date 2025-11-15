"""
Main drawing service for column details
"""

import logging
from typing import List, Dict, Any, Tuple
from .autocad_manager import AutoCADManager, DrawingContext
from .excel_reader import ColumnData, FloorData
from .column_calculator import ColumnCalculator, ColumnGeometry, RebarLayout

class ColumnDrawingService:
    """Main service for drawing column elevations and sections"""
    
    def __init__(self, autocad_manager: AutoCADManager):
        self.autocad = autocad_manager
        self.calculator = ColumnCalculator()
        self.logger = logging.getLogger(__name__)
        
        # Layer definitions
        self.layers = {
            'concrete': 'CONCRETE',
            'rebar': 'REBAR',
            'stirrups': 'STIRRUPS',
            'dimensions': 'DIMENSIONS',
            'text': 'TEXT',
            'sections': 'SECTIONS',
            'hidden': 'HIDDEN'
        }
    
    def draw_column_elevation(self, column_data: ColumnData, 
                            insertion_point: Tuple[float, float, float],
                            column_number: int = 1) -> bool:
        """Draw complete column elevation"""
        try:
            self.logger.info(f"Drawing column elevation for {column_data.column_name}")
            
            # Calculate geometry
            geometry = self.calculator.calculate_column_geometry(
                column_data.floors, column_data.settings, insertion_point
            )
            
            # Calculate rebar layout
            rebar_layout = self.calculator.calculate_rebar_layout(
                column_data.floors, geometry, column_data.settings
            )
            
            # Setup layers
            self._setup_layers()
            
            # Draw components
            with DrawingContext(self.autocad, self.layers['concrete']):
                self._draw_concrete_outline(column_data, geometry)
            
            with DrawingContext(self.autocad, self.layers['rebar']):
                self._draw_main_rebars(rebar_layout.main_bars)
            
            with DrawingContext(self.autocad, self.layers['stirrups']):
                self._draw_stirrups(rebar_layout.stirrup_positions, geometry.column_boundaries)
            
            with DrawingContext(self.autocad, self.layers['dimensions']):
                self._draw_dimensions(column_data, geometry)
            
            with DrawingContext(self.autocad, self.layers['text']):
                self._draw_annotations(column_data, geometry, column_number)
            
            self.autocad.refresh_view()
            return True
            
        except Exception as e:
            self.logger.error(f"Error drawing column elevation: {e}")
            return False
    
    def draw_column_sections(self, column_data: ColumnData,
                           insertion_point: Tuple[float, float, float]) -> bool:
        """Draw column sections for each floor"""
        try:
            current_y = insertion_point[1]
            
            for i, floor in enumerate(column_data.floors):
                section_point = (insertion_point[0], current_y, insertion_point[2])
                
                with DrawingContext(self.autocad, self.layers['sections']):
                    self._draw_single_section(floor, section_point, column_data.settings.section_scale)
                
                current_y -= (floor.column_length * 1.5)  # Space between sections
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error drawing column sections: {e}")
            return False
    
    def _setup_layers(self):
        """Setup required layers"""
        for layer_name in self.layers.values():
            self.autocad.create_layer(layer_name)
        
        # Setup hidden line type
        self.autocad.get_linetype('HIDDEN')
    
    def _draw_concrete_outline(self, column_data: ColumnData, geometry: ColumnGeometry):
        """Draw concrete outline of column"""
        base_x, base_y, base_z = geometry.base_point
        
        # Draw foundation if first floor
        first_floor = column_data.floors[0]
        settings = column_data.settings
        
        if settings.foundation_depth > 0 and not settings.is_foundation_string:
            self._draw_foundation(geometry, settings)
        
        # Draw each floor
        for i, (floor, (left_x, right_x)) in enumerate(zip(column_data.floors, geometry.column_boundaries)):
            floor_base_y = geometry.floor_levels[i]
            floor_height = floor.total_height - settings.beam_depth
            
            # Draw column
            self.autocad.model_space.AddLine(
                (left_x, floor_base_y, base_z), 
                (left_x, floor_base_y + floor_height, base_z)
            )
            self.autocad.model_space.AddLine(
                (right_x, floor_base_y, base_z), 
                (right_x, floor_base_y + floor_height, base_z)
            )
            
            # Draw beams
            beam_y = floor_base_y + floor_height
            beam_left = left_x - settings.beam_extension
            beam_right = right_x + settings.beam_extension
            
            self.autocad.model_space.AddLine(
                (beam_left, beam_y, base_z), 
                (beam_right, beam_y, base_z)
            )
            self.autocad.model_space.AddLine(
                (beam_left, beam_y + settings.beam_depth, base_z), 
                (beam_right, beam_y + settings.beam_depth, base_z)
            )
    
    def _draw_foundation(self, geometry: ColumnGeometry, settings: ColumnSettings):
        """Draw foundation"""
        base_x, base_y, base_z = geometry.base_point
        first_left, first_right = geometry.column_boundaries[0]
        
        foundation_top = base_y
        foundation_bottom = base_y - settings.foundation_depth
        
        # Foundation outline
        foundation_left = first_left - settings.beam_extension
        foundation_right = first_right + settings.beam_extension
        
        points = [
            (foundation_left, foundation_top),
            (foundation_right, foundation_top),
            (foundation_right, foundation_bottom),
            (foundation_left, foundation_bottom),
            (foundation_left, foundation_top)
        ]
        
        # Convert to 3D points
        points_3d = []
        for x, y in points:
            points_3d.extend([x, y, base_z])
        
        polyline = self.autocad.model_space.AddLightWeightPolyline(points_3d[:6])  # First 4 points for polyline
        polyline.Closed = True
    
    def _draw_main_rebars(self, main_bars: List[Tuple]):
        """Draw main reinforcement bars"""
        for x, start_y, end_y, diameter in main_bars:
            # Draw bar as a line
            self.autocad.model_space.AddLine(
                (x, start_y, 0), 
                (x, end_y, 0)
            )
            
            # Add diameter indicator (simplified)
            text_point = (x + 50, (start_y + end_y) / 2, 0)
            self.autocad.model_space.AddText(
                f"Ø{diameter}", 
                text_point, 
                2.5
            )
    
    def _draw_stirrups(self, stirrups: List[Tuple], boundaries: List[Tuple]):
        """Draw stirrups"""
        for y, spacing_type, diameter in stirrups:
            if boundaries:
                left_x, right_x = boundaries[0]  # Use first floor boundaries for simplicity
                
                # Draw stirrup as horizontal line
                self.autocad.model_space.AddLine(
                    (left_x, y, 0), 
                    (right_x, y, 0)
                )
    
    def _draw_dimensions(self, column_data: ColumnData, geometry: ColumnGeometry):
        """Draw dimensions"""
        base_x, base_y, base_z = geometry.base_point
        settings = column_data.settings
        
        # Draw height dimensions
        for i, level in enumerate(geometry.floor_levels):
            if i < len(column_data.floors):
                floor_name = column_data.floors[i].floor_name
                
                # Add height dimension
                dim_x = base_x + max([b[1] for b in geometry.column_boundaries]) + 100
                
                if i > 0:
                    prev_level = geometry.floor_levels[i-1]
                    height = level - prev_level
                    
                    # Draw dimension line
                    self.autocad.model_space.AddLine(
                        (dim_x, prev_level, base_z), 
                        (dim_x, level, base_z)
                    )
                    
                    # Add dimension text
                    text_point = (dim_x + 20, (prev_level + level) / 2, base_z)
                    self.autocad.model_space.AddText(
                        f"{height:.0f}", 
                        text_point, 
                        2.5
                    )
    
    def _draw_annotations(self, column_data: ColumnData, geometry: ColumnGeometry, column_number: int):
        """Draw text annotations"""
        base_x, base_y, base_z = geometry.base_point
        
        # Column title
        title_point = (base_x, geometry.floor_levels[-1] + 100, base_z)
        self.autocad.model_space.AddText(
            f"COLUMN-{column_number}", 
            title_point, 
            5.0
        )
        
        # Floor labels
        for i, level in enumerate(geometry.floor_levels[:-1]):  # Exclude top level
            if i < len(column_data.floors):
                floor = column_data.floors[i]
                label_point = (base_x - 150, level + floor.total_height / 2, base_z)
                self.autocad.model_space.AddText(
                    floor.floor_name, 
                    label_point, 
                    3.0
                )
    
    def _draw_single_section(self, floor: FloorData, insertion_point: Tuple[float, float, float], scale: float):
        """Draw single column section"""
        section_data = self.calculator.calculate_section_dimensions(floor, scale)
        
        ip_x, ip_y, ip_z = insertion_point
        length = section_data['length'] * scale
        width = section_data['width'] * scale if not section_data['is_circular'] else length
        
        if section_data['is_circular']:
            # Draw circular section
            radius = length / 2
            self.autocad.model_space.AddCircle(
                (ip_x, ip_y, ip_z), 
                radius
            )
        else:
            # Draw rectangular section
            left = ip_x - length / 2
            bottom = ip_y - width / 2
            right = ip_x + length / 2
            top = ip_y + width / 2
            
            points = [left, bottom, right, bottom, right, top, left, top, left, bottom]
            polyline = self.autocad.model_space.AddLightWeightPolyline(points)
            polyline.Closed = True
        
        # Draw rebars in section
        for rebar_x, rebar_y in section_data['rebar_positions']:
            scaled_x = ip_x - length / 2 + rebar_x * scale
            scaled_y = ip_y - width / 2 + rebar_y * scale
            
            self.autocad.model_space.AddCircle(
                (scaled_x, scaled_y, ip_z), 
                floor.rebar_diameter * scale / 2
            )