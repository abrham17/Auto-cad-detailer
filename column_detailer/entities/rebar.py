"""
Rebar entity classes
"""

from dataclasses import dataclass
from typing import List, Tuple
from .column import Point3D

@dataclass
class Rebar:
    """Single rebar representation"""
    diameter: float
    start_point: Point3D
    end_point: Point3D
    grade: str = "500"  # MPa
    
    @property
    def length(self) -> float:
        """Calculate rebar length"""
        dx = self.end_point.x - self.start_point.x
        dy = self.end_point.y - self.start_point.y
        dz = self.end_point.z - self.start_point.z
        return (dx**2 + dy**2 + dz**2) ** 0.5
    
    @property
    def is_vertical(self) -> bool:
        """Check if rebar is vertical"""
        return (abs(self.start_point.x - self.end_point.x) < 0.001 and 
                abs(self.start_point.z - self.end_point.z) < 0.001)
    
    @property
    def is_horizontal(self) -> bool:
        """Check if rebar is horizontal"""
        return abs(self.start_point.y - self.end_point.y) < 0.001

class RebarLayout:
    """Complete rebar layout for a column"""
    
    def __init__(self):
        self.main_bars: List[Rebar] = []
        self.links: List[Rebar] = []
        self.main_bars_x: int = 0
        self.main_bars_y: int = 0
        
    @property
    def main_bars_count(self) -> int:
        """Total number of main bars"""
        return len(self.main_bars)
    
    def add_main_bar(self, rebar: Rebar):
        """Add a main bar"""
        self.main_bars.append(rebar)
    
    def add_link(self, rebar: Rebar):
        """Add a link/stirrup"""
        self.links.append(rebar)
    
    def get_total_length(self) -> float:
        """Get total length of all rebars"""
        total = sum(bar.length for bar in self.main_bars)
        total += sum(link.length for link in self.links)
        return total
    
    def get_total_weight(self, density: float = 7850) -> float:
        """Get total weight of rebars in kg"""
        total_volume = 0.0
        
        for bar in self.main_bars + self.links:
            area = math.pi * (bar.diameter / 2) ** 2
            volume = area * bar.length / 1000  # Convert to m³
            total_volume += volume
        
        return total_volume * density  # kg

class StirrupLayout:
    """Stirrup/link layout configuration"""
    
    def __init__(self):
        self.diameter: float = 8.0
        self.edge_spacing: float = 100.0
        self.mid_spacing: float = 150.0
        self.positions: List[float] = []  # Y-coordinates
    
    def calculate_positions(self, start_y: float, height: float, beam_depth: float):
        """Calculate stirrup positions"""
        self.positions = []
        net_height = height - beam_depth
        
        # Divide into thirds
        third_height = net_height / 3
        
        # Bottom third - edge spacing
        current_y = start_y + self.edge_spacing
        while current_y < start_y + third_height:
            self.positions.append(current_y)
            current_y += self.edge_spacing
        
        # Middle third - mid spacing
        current_y = start_y + third_height + self.mid_spacing
        while current_y < start_y + 2 * third_height:
            self.positions.append(current_y)
            current_y += self.mid_spacing
        
        # Top third - edge spacing
        current_y = start_y + 2 * third_height + self.edge_spacing
        while current_y < start_y + height:
            self.positions.append(current_y)
            current_y += self.edge_spacing
    
    def get_spacing_at_height(self, y: float, start_y: float, height: float) -> float:
        """Get stirrup spacing at specific height"""
        net_height = height - (y - start_y)
        third_height = height / 3
        
        if net_height <= third_height:
            return self.edge_spacing
        elif net_height <= 2 * third_height:
            return self.mid_spacing
        else:
            return self.edge_spacing