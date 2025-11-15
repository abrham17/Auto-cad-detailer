"""
Column geometry and reinforcement calculations
"""

import math
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from .excel_reader import FloorData, ColumnSettings

@dataclass
class ColumnGeometry:
    """Calculated column geometry"""
    base_point: Tuple[float, float, float]
    total_height: float
    floor_heights: List[float]
    floor_levels: List[float]
    column_boundaries: List[Tuple[float, float]]  # (left_x, right_x) for each floor

@dataclass
class RebarLayout:
    """Rebar layout calculations"""
    main_bars: List[Tuple[float, float, float, float]]  # (x, start_y, end_y, diameter)
    stirrup_positions: List[Tuple[float, float, float]]  # (y, spacing_type, diameter)
    lap_lengths: List[Tuple[float, float, float]]  # (y_position, length, diameter)

class ColumnCalculator:
    """Performs calculations for column detailing"""
    
    def __init__(self):
        self.rebar_clearance = 25.0  # mm clearance for rebars
    
    def calculate_column_geometry(self, floors: List[FloorData], settings: ColumnSettings,
                                base_point: Tuple[float, float, float]) -> ColumnGeometry:
        """Calculate complete column geometry"""
        base_x, base_y, base_z = base_point
        
        floor_heights = [floor.total_height for floor in floors]
        total_height = sum(floor_heights)
        
        # Calculate floor levels
        floor_levels = [base_y]
        current_height = base_y
        for height in floor_heights:
            current_height += height
            floor_levels.append(current_height)
        
        # Calculate column boundaries for each floor
        column_boundaries = []
        for i, floor in enumerate(floors):
            left_x = base_x - floor.column_length / 2
            right_x = base_x + floor.column_length / 2
            column_boundaries.append((left_x, right_x))
        
        return ColumnGeometry(
            base_point=base_point,
            total_height=total_height,
            floor_heights=floor_heights,
            floor_levels=floor_levels,
            column_boundaries=column_boundaries
        )
    
    def calculate_rebar_layout(self, floors: List[FloorData], geometry: ColumnGeometry,
                             settings: ColumnSettings) -> RebarLayout:
        """Calculate rebar and stirrup layout"""
        main_bars = []
        stirrup_positions = []
        lap_lengths = []
        
        current_y = geometry.base_point[1]
        
        for i, floor in enumerate(floors):
            floor_height = floor.total_height
            column_length = floor.column_length
            concrete_cover = settings.concrete_cover
            
            # Calculate main bar positions
            bars = self._calculate_main_bars(floor, geometry.column_boundaries[i], 
                                           current_y, floor_height, concrete_cover)
            main_bars.extend(bars)
            
            # Calculate stirrup positions
            stirrups = self._calculate_stirrups(floor, current_y, floor_height, 
                                              settings.beam_depth)
            stirrup_positions.extend(stirrups)
            
            # Calculate lap lengths
            if i < len(floors) - 1:  # Not the top floor
                lap_length = self._calculate_lap_length(floor.rebar_diameter)
                lap_y = current_y + floor_height - settings.beam_depth / 2
                lap_lengths.append((lap_y, lap_length, floor.rebar_diameter))
            
            current_y += floor_height
        
        return RebarLayout(
            main_bars=main_bars,
            stirrup_positions=stirrup_positions,
            lap_lengths=lap_lengths
        )
    
    def _calculate_main_bars(self, floor: FloorData, boundaries: Tuple[float, float],
                           base_y: float, height: float, cover: float) -> List[Tuple]:
        """Calculate positions for main reinforcement bars"""
        bars = []
        left_x, right_x = boundaries
        column_length = right_x - left_x
        
        # Edge bars
        edge_x_left = left_x + cover
        edge_x_right = right_x - cover
        
        bars.append((edge_x_left, base_y, base_y + height, floor.rebar_diameter))
        bars.append((edge_x_right, base_y, base_y + height, floor.rebar_diameter))
        
        # Intermediate bars (if any)
        if floor.rebar_amount_x > 2:
            spacing = (column_length - 2 * cover) / (floor.rebar_amount_x - 1)
            for i in range(1, floor.rebar_amount_x - 1):
                x_pos = left_x + cover + i * spacing
                bars.append((x_pos, base_y, base_y + height, floor.rebar_diameter))
        
        return bars
    
    def _calculate_stirrups(self, floor: FloorData, base_y: float, 
                          height: float, beam_depth: float) -> List[Tuple]:
        """Calculate stirrup positions"""
        stirrups = []
        net_height = height - beam_depth
        
        # Divide column into thirds
        third_height = net_height / 3
        
        # Bottom third - edge spacing
        current_y = base_y + floor.edge_stirrup_spacing
        while current_y < base_y + third_height:
            stirrups.append((current_y, 'edge', floor.stirrup_diameter))
            current_y += floor.edge_stirrup_spacing
        
        # Middle third - mid spacing
        current_y = base_y + third_height + floor.mid_stirrup_spacing
        while current_y < base_y + 2 * third_height:
            stirrups.append((current_y, 'mid', floor.stirrup_diameter))
            current_y += floor.mid_stirrup_spacing
        
        # Top third - edge spacing (including beam zone)
        current_y = base_y + 2 * third_height + floor.edge_stirrup_spacing
        while current_y < base_y + height:
            stirrups.append((current_y, 'edge', floor.stirrup_diameter))
            current_y += floor.edge_stirrup_spacing
        
        return stirrups
    
    def _calculate_lap_length(self, bar_diameter: float) -> float:
        """Calculate lap length for rebars (simplified)"""
        # Simplified calculation - in practice, this would follow code requirements
        return max(40 * bar_diameter, 300)  # 40d or 300mm, whichever is greater
    
    def calculate_section_dimensions(self, floor: FloorData, scale: float = 1.0) -> Dict[str, Any]:
        """Calculate dimensions for column section view"""
        length = floor.column_length
        width = floor.column_width if floor.column_width > 0 else length  # Circular if width = 0
        
        return {
            'length': length,
            'width': width,
            'scale': scale,
            'rebar_positions': self._calculate_section_rebar_positions(floor),
            'is_circular': floor.column_width == 0
        }
    
    def _calculate_section_rebar_positions(self, floor: FloorData) -> List[Tuple[float, float]]:
        """Calculate rebar positions in section view"""
        positions = []
        length = floor.column_length
        width = floor.column_width if floor.column_width > 0 else length
        cover = 25.0  # Default cover
        
        if floor.column_width > 0:  # Rectangular section
            # Calculate positions for rectangular arrangement
            x_spacing = (length - 2 * cover) / (floor.rebar_amount_x - 1)
            y_spacing = (width - 2 * cover) / (floor.rebar_amount_y - 1)
            
            for i in range(floor.rebar_amount_x):
                for j in range(floor.rebar_amount_y):
                    x = cover + i * x_spacing
                    y = cover + j * y_spacing
                    positions.append((x, y))
        else:  # Circular section
            # Circular arrangement
            radius = (length / 2) - cover
            angle_step = 2 * math.pi / floor.rebar_amount_x
            
            for i in range(floor.rebar_amount_x):
                angle = i * angle_step
                x = length / 2 + radius * math.cos(angle)
                y = length / 2 + radius * math.sin(angle)
                positions.append((x, y))
        
        return positions