"""
Stirrup entity classes
"""

from dataclasses import dataclass
from typing import List, Tuple
from .column import Point3D
import math

@dataclass
class Stirrup:
    """Single stirrup representation"""
    diameter: float
    positions: List[Point3D]  # Corner points
    elevation: float  # Y-coordinate
    
    @property
    def perimeter(self) -> float:
        """Calculate stirrup perimeter"""
        if len(self.positions) < 2:
            return 0.0
        
        perimeter = 0.0
        for i in range(len(self.positions)):
            p1 = self.positions[i]
            p2 = self.positions[(i + 1) % len(self.positions)]
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            perimeter += math.sqrt(dx*dx + dy*dy)
        
        return perimeter
    
    @property
    def corners(self) -> List[Tuple[float, float]]:
        """Get 2D corner coordinates"""
        return [(p.x, p.y) for p in self.positions]

class RectangularStirrup(Stirrup):
    """Rectangular stirrup"""
    
    def __init__(self, diameter: float, elevation: float, 
                 width: float, height: float, center_x: float = 0):
        self.diameter = diameter
        self.elevation = elevation
        self.width = width
        self.height = height
        self.center_x = center_x
        
        # Calculate corner positions
        left = center_x - width / 2
        right = center_x + width / 2
        bottom = elevation - height / 2
        top = elevation + height / 2
        
        positions = [
            Point3D(left, bottom, 0),
            Point3D(right, bottom, 0),
            Point3D(right, top, 0),
            Point3D(left, top, 0)
        ]
        
        super().__init__(diameter, positions, elevation)

class CircularStirrup(Stirrup):
    """Circular stirrup/helix"""
    
    def __init__(self, diameter: float, elevation: float, 
                 column_diameter: float, center_x: float = 0,
                 segments: int = 16):
        self.diameter = diameter
        self.elevation = elevation
        self.column_diameter = column_diameter
        self.center_x = center_x
        self.segments = segments
        
        # Calculate circular positions
        radius = column_diameter / 2 - diameter / 2
        positions = []
        
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = center_x + radius * math.cos(angle)
            y = elevation + radius * math.sin(angle)
            positions.append(Point3D(x, y, 0))
        
        super().__init__(diameter, positions, elevation)

class StirrupPattern:
    """Complete stirrup pattern for a column"""
    
    def __init__(self):
        self.stirrups: List[Stirrup] = []
        self.diameter: float = 8.0
        self.edge_spacing: float = 100.0
        self.mid_spacing: float = 150.0
    
    def add_stirrup(self, stirrup: Stirrup):
        """Add a stirrup to the pattern"""
        self.stirrups.append(stirrup)
    
    def get_stirrups_in_range(self, start_y: float, end_y: float) -> List[Stirrup]:
        """Get stirrups within elevation range"""
        return [s for s in self.stirrups if start_y <= s.elevation <= end_y]
    
    def get_total_length(self) -> float:
        """Get total length of all stirrups"""
        return sum(stirrup.perimeter for stirrup in self.stirrups)
    
    def get_total_weight(self, density: float = 7850) -> float:
        """Get total weight of stirrups in kg"""
        total_length = self.get_total_length()
        area = math.pi * (self.diameter / 2) ** 2
        volume = area * total_length / 1000  # Convert to m³
        return volume * density  # kg
    
    def generate_rectangular_pattern(self, start_y: float, height: float, 
                                   beam_depth: float, width: float, 
                                   column_width: float, center_x: float = 0):
        """Generate rectangular stirrup pattern"""
        self.stirrups.clear()
        net_height = height - beam_depth
        
        # Calculate positions using the same logic as calculator
        third_height = net_height / 3
        
        # Bottom third
        current_y = start_y + self.edge_spacing
        while current_y < start_y + third_height:
            stirrup = RectangularStirrup(
                self.diameter, current_y, width, column_width, center_x
            )
            self.stirrups.append(stirrup)
            current_y += self.edge_spacing
        
        # Middle third
        current_y = start_y + third_height + self.mid_spacing
        while current_y < start_y + 2 * third_height:
            stirrup = RectangularStirrup(
                self.diameter, current_y, width, column_width, center_x
            )
            self.stirrups.append(stirrup)
            current_y += self.mid_spacing
        
        # Top third
        current_y = start_y + 2 * third_height + self.edge_spacing
        while current_y < start_y + height:
            stirrup = RectangularStirrup(
                self.diameter, current_y, width, column_width, center_x
            )
            self.stirrups.append(stirrup)
            current_y += self.edge_spacing