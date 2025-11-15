"""
Geometry utility functions
"""

import math
from typing import List, Tuple, Optional
from column_detailer.entities.column import Point3D

class GeometryUtils:
    """Geometry calculation utilities"""
    
    @staticmethod
    def distance(point1: Point3D, point2: Point3D) -> float:
        """Calculate distance between two points"""
        dx = point2.x - point1.x
        dy = point2.y - point1.y
        dz = point2.z - point1.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    @staticmethod
    def midpoint(point1: Point3D, point2: Point3D) -> Point3D:
        """Calculate midpoint between two points"""
        return Point3D(
            (point1.x + point2.x) / 2,
            (point1.y + point2.y) / 2,
            (point1.z + point2.z) / 2
        )
    
    @staticmethod
    def angle_between_points(point1: Point3D, point2: Point3D) -> float:
        """Calculate angle between two points in radians"""
        dx = point2.x - point1.x
        dy = point2.y - point1.y
        return math.atan2(dy, dx)
    
    @staticmethod
    def point_on_circle(center: Point3D, radius: float, angle: float) -> Point3D:
        """Calculate point on circle given center, radius and angle"""
        return Point3D(
            center.x + radius * math.cos(angle),
            center.y + radius * math.sin(angle),
            center.z
        )
    
    @staticmethod
    def rotate_point(point: Point3D, center: Point3D, angle: float) -> Point3D:
        """Rotate point around center by angle (radians)"""
        # Translate to origin
        translated_x = point.x - center.x
        translated_y = point.y - center.y
        
        # Rotate
        rotated_x = translated_x * math.cos(angle) - translated_y * math.sin(angle)
        rotated_y = translated_x * math.sin(angle) + translated_y * math.cos(angle)
        
        # Translate back
        return Point3D(
            rotated_x + center.x,
            rotated_y + center.y,
            point.z
        )
    
    @staticmethod
    def line_intersection(line1: Tuple[Point3D, Point3D], 
                         line2: Tuple[Point3D, Point3D]) -> Optional[Point3D]:
        """Find intersection point of two lines (2D)"""
        p1, p2 = line1
        p3, p4 = line2
        
        # Line1 represented as a1x + b1y = c1
        a1 = p2.y - p1.y
        b1 = p1.x - p2.x
        c1 = a1 * p1.x + b1 * p1.y
        
        # Line2 represented as a2x + b2y = c2
        a2 = p4.y - p3.y
        b2 = p3.x - p4.x
        c2 = a2 * p3.x + b2 * p3.y
        
        determinant = a1 * b2 - a2 * b1
        
        if abs(determinant) < 1e-10:
            return None  # Lines are parallel
        
        x = (b2 * c1 - b1 * c2) / determinant
        y = (a1 * c2 - a2 * c1) / determinant
        
        return Point3D(x, y, p1.z)
    
    @staticmethod
    def point_in_polygon(point: Point3D, polygon: List[Point3D]) -> bool:
        """Check if point is inside polygon (2D)"""
        if len(polygon) < 3:
            return False
        
        x, y = point.x, point.y
        inside = False
        
        j = len(polygon) - 1
        for i in range(len(polygon)):
            xi, yi = polygon[i].x, polygon[i].y
            xj, yj = polygon[j].x, polygon[j].y
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        
        return inside
    
    @staticmethod
    def calculate_polygon_area(polygon: List[Point3D]) -> float:
        """Calculate area of polygon (2D)"""
        if len(polygon) < 3:
            return 0.0
        
        area = 0.0
        j = len(polygon) - 1
        
        for i in range(len(polygon)):
            area += (polygon[j].x + polygon[i].x) * (polygon[j].y - polygon[i].y)
            j = i
        
        return abs(area) / 2.0

class Transform:
    """Coordinate transformation utilities"""
    
    def __init__(self, scale: float = 1.0, rotation: float = 0.0, 
                 translation: Point3D = Point3D(0, 0, 0)):
        self.scale = scale
        self.rotation = rotation
        self.translation = translation
    
    def apply(self, point: Point3D) -> Point3D:
        """Apply transformation to point"""
        # Scale
        scaled_x = point.x * self.scale
        scaled_y = point.y * self.scale
        
        # Rotate
        rotated_x = scaled_x * math.cos(self.rotation) - scaled_y * math.sin(self.rotation)
        rotated_y = scaled_x * math.sin(self.rotation) + scaled_y * math.cos(self.rotation)
        
        # Translate
        return Point3D(
            rotated_x + self.translation.x,
            rotated_y + self.translation.y,
            point.z * self.scale + self.translation.z
        )
    
    def apply_to_points(self, points: List[Point3D]) -> List[Point3D]:
        """Apply transformation to multiple points"""
        return [self.apply(point) for point in points]