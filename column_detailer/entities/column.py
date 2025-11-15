"""
Column entity classes
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
import math

@dataclass
class Point3D:
    """3D point representation"""
    x: float
    y: float
    z: float
    
    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)
    
    def offset(self, dx: float = 0, dy: float = 0, dz: float = 0) -> 'Point3D':
        return Point3D(self.x + dx, self.y + dy, self.z + dz)

@dataclass
class Rectangle:
    """Rectangle representation"""
    lower_left: Point3D
    upper_right: Point3D
    
    @property
    def width(self) -> float:
        return self.upper_right.x - self.lower_left.x
    
    @property
    def height(self) -> float:
        return self.upper_right.y - self.lower_left.y
    
    @property
    def center(self) -> Point3D:
        return Point3D(
            (self.lower_left.x + self.upper_right.x) / 2,
            (self.lower_left.y + self.upper_right.y) / 2,
            self.lower_left.z
        )
    
    def get_corners(self) -> List[Point3D]:
        return [
            self.lower_left,
            Point3D(self.upper_right.x, self.lower_left.y, self.lower_left.z),
            self.upper_right,
            Point3D(self.lower_left.x, self.upper_right.y, self.lower_left.z)
        ]

class Column:
    """Column entity representing a structural column"""
    
    def __init__(self, name: str = "Column"):
        self.name = name
        self.floors: List[ColumnFloor] = []
        self.base_point = Point3D(0, 0, 0)
        self.settings = None
    
    def add_floor(self, floor: 'ColumnFloor'):
        """Add a floor to the column"""
        self.floors.append(floor)
    
    def get_total_height(self) -> float:
        """Get total height of column"""
        return sum(floor.height for floor in self.floors)
    
    def get_floor_levels(self) -> List[float]:
        """Get Y-coordinates of each floor level"""
        levels = [self.base_point.y]
        current_y = self.base_point.y
        
        for floor in self.floors:
            current_y += floor.height
            levels.append(current_y)
        
        return levels
    
    def get_floor_boundaries(self) -> List[Tuple[float, float]]:
        """Get left and right boundaries for each floor"""
        boundaries = []
        for floor in self.floors:
            left = self.base_point.x - floor.length / 2
            right = self.base_point.x + floor.length / 2
            boundaries.append((left, right))
        return boundaries

class ColumnFloor:
    """Represents a single floor in a column"""
    
    def __init__(self, name: str = "Floor"):
        self.name = name
        self.height: float = 0.0
        self.length: float = 0.0
        self.width: float = 0.0
        self.reinforcement: Optional['RebarLayout'] = None
        self.stirrups: Optional['StirrupLayout'] = None
        
    @property
    def is_circular(self) -> bool:
        """Check if column is circular"""
        return self.width == 0
    
    @property
    def cross_section_area(self) -> float:
        """Calculate cross-sectional area"""
        if self.is_circular:
            return math.pi * (self.length / 2) ** 2
        else:
            return self.length * self.width

class ColumnSection:
    """Column cross-section representation"""
    
    def __init__(self, floor: ColumnFloor, scale: float = 1.0):
        self.floor = floor
        self.scale = scale
        self.rebar_positions: List[Point3D] = []
        
    def calculate_rebar_positions(self, cover: float = 25.0):
        """Calculate rebar positions in section"""
        self.rebar_positions = []
        
        if self.floor.is_circular:
            self._calculate_circular_positions(cover)
        else:
            self._calculate_rectangular_positions(cover)
    
    def _calculate_circular_positions(self, cover: float):
        """Calculate rebar positions for circular section"""
        radius = (self.floor.length / 2) - cover
        center_x = self.floor.length / 2
        center_y = self.floor.width / 2 if self.floor.width > 0 else center_x
        
        if self.floor.reinforcement:
            angle_step = 2 * math.pi / self.floor.reinforcement.main_bars_count
            
            for i in range(self.floor.reinforcement.main_bars_count):
                angle = i * angle_step
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                self.rebar_positions.append(Point3D(x, y, 0))
    
    def _calculate_rectangular_positions(self, cover: float):
        """Calculate rebar positions for rectangular section"""
        if not self.floor.reinforcement:
            return
            
        x_count = self.floor.reinforcement.main_bars_x
        y_count = self.floor.reinforcement.main_bars_y
        
        if x_count > 0 and y_count > 0:
            x_spacing = (self.floor.length - 2 * cover) / (x_count - 1)
            y_spacing = (self.floor.width - 2 * cover) / (y_count - 1)
            
            for i in range(x_count):
                for j in range(y_count):
                    # Skip corners if they're handled separately
                    if (i == 0 or i == x_count - 1) and (j == 0 or j == y_count - 1):
                        continue
                        
                    x = cover + i * x_spacing
                    y = cover + j * y_spacing
                    self.rebar_positions.append(Point3D(x, y, 0))