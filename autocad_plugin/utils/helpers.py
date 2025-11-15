"""
Helper functions and utilities for AutoCAD Structural Plugin
"""
import math
import random
import string
import os
import re
from datetime import datetime
from typing import Union, Tuple, List, Optional
from pathlib import Path

from .logger import logger

# Type aliases
Point2D = Tuple[float, float]
Point3D = Tuple[float, float, float]

def validate_point(point: Union[Point2D, Point3D], 
                  min_x: float = -1e6, max_x: float = 1e6,
                  min_y: float = -1e6, max_y: float = 1e6,
                  min_z: float = -1e6, max_z: float = 1e6) -> bool:
    """
    Validate point coordinates are within reasonable bounds
    
    Args:
        point: 2D or 3D point coordinates
        min_x, max_x: X coordinate bounds
        min_y, max_y: Y coordinate bounds  
        min_z, max_z: Z coordinate bounds
        
    Returns:
        bool: True if point is valid
    """
    try:
        if len(point) < 2 or len(point) > 3:
            return False
        
        x, y = point[0], point[1]
        if not (min_x <= x <= max_x and min_y <= y <= max_y):
            return False
        
        if len(point) == 3:
            z = point[2]
            if not (min_z <= z <= max_z):
                return False
        
        # Check for NaN or infinity
        for coord in point:
            if math.isnan(coord) or math.isinf(coord):
                return False
        
        return True
        
    except (TypeError, ValueError, IndexError):
        return False

def calculate_distance(point1: Union[Point2D, Point3D], 
                      point2: Union[Point2D, Point3D]) -> float:
    """
    Calculate distance between two points
    
    Args:
        point1: First point
        point2: Second point
        
    Returns:
        float: Distance between points
    """
    try:
        if len(point1) != len(point2):
            raise ValueError("Points must have same dimensions")
        
        if len(point1) == 2:
            dx = point2[0] - point1[0]
            dy = point2[1] - point1[1]
            return math.sqrt(dx*dx + dy*dy)
        elif len(point1) == 3:
            dx = point2[0] - point1[0]
            dy = point2[1] - point1[1]
            dz = point2[2] - point1[2]
            return math.sqrt(dx*dx + dy*dy + dz*dz)
        else:
            raise ValueError("Points must be 2D or 3D")
            
    except Exception as e:
        logger.error(f"Error calculating distance: {e}")
        return 0.0

def convert_units(value: float, 
                  from_unit: str, 
                  to_unit: str, 
                  unit_type: str = 'length') -> float:
    """
    Convert between different units
    
    Args:
        value: Value to convert
        from_unit: Source unit
        to_unit: Target unit  
        unit_type: Type of unit (length, force, stress, etc.)
        
    Returns:
        float: Converted value
    """
    try:
        if from_unit == to_unit:
            return value
        
        # Length conversions
        if unit_type == 'length':
            conversion_factors = {
                'mm': 1.0,
                'cm': 10.0,
                'm': 1000.0,
                'in': 25.4,
                'ft': 304.8
            }
        # Force conversions
        elif unit_type == 'force':
            conversion_factors = {
                'N': 1.0,
                'kN': 1000.0,
                'lbf': 4.44822,
                'kip': 4448.22
            }
        # Stress conversions
        elif unit_type == 'stress':
            conversion_factors = {
                'Pa': 1.0,
                'kPa': 1000.0,
                'MPa': 1e6,
                'GPa': 1e9,
                'psi': 6894.76,
                'ksi': 6894760.0
            }
        # Moment conversions
        elif unit_type == 'moment':
            conversion_factors = {
                'Nm': 1.0,
                'kNm': 1000.0,
                'lb-ft': 1.35582,
                'kip-ft': 1355.82
            }
        else:
            logger.warning(f"Unknown unit type: {unit_type}")
            return value
        
        if from_unit not in conversion_factors or to_unit not in conversion_factors:
            logger.warning(f"Unknown units: {from_unit} -> {to_unit}")
            return value
        
        # Convert to base unit first, then to target unit
        value_in_base = value * conversion_factors[from_unit]
        value_in_target = value_in_base / conversion_factors[to_unit]
        
        return value_in_target
        
    except Exception as e:
        logger.error(f"Error converting units: {e}")
        return value

def generate_id(prefix: str = "elem", length: int = 8) -> str:
    """
    Generate a unique ID for structural elements
    
    Args:
        prefix: ID prefix
        length: Length of random part
        
    Returns:
        str: Generated ID
    """
    try:
        timestamp = datetime.now().strftime("%H%M%S")
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        return f"{prefix}_{timestamp}_{random_part}"
        
    except Exception as e:
        logger.error(f"Error generating ID: {e}")
        return f"{prefix}_{int(datetime.now().timestamp())}"

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    try:
        # Remove invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255 - len(ext)] + ext
        
        return sanitized
        
    except Exception as e:
        logger.error(f"Error sanitizing filename: {e}")
        return "unnamed_file"

def format_timestamp(timestamp: Optional[datetime] = None, 
                     format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format timestamp as string
    
    Args:
        timestamp: Datetime object (uses current time if None)
        format_str: Format string
        
    Returns:
        str: Formatted timestamp
    """
    try:
        if timestamp is None:
            timestamp = datetime.now()
        return timestamp.strftime(format_str)
    except Exception as e:
        logger.error(f"Error formatting timestamp: {e}")
        return "unknown_time"

def calculate_area(points: List[Point2D]) -> float:
    """
    Calculate area of a polygon using shoelace formula
    
    Args:
        points: List of 2D points forming a closed polygon
        
    Returns:
        float: Area of the polygon
    """
    try:
        if len(points) < 3:
            return 0.0
        
        # Ensure polygon is closed
        if points[0] != points[-1]:
            points = points + [points[0]]
        
        area = 0.0
        n = len(points)
        
        for i in range(n - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            area += (x1 * y2) - (x2 * y1)
        
        return abs(area) / 2.0
        
    except Exception as e:
        logger.error(f"Error calculating area: {e}")
        return 0.0

def normalize_vector(vector: Union[Point2D, Point3D]) -> Union[Point2D, Point3D]:
    """
    Normalize a vector to unit length
    
    Args:
        vector: Input vector
        
    Returns:
        Normalized vector
    """
    try:
        if len(vector) == 2:
            x, y = vector
            length = math.sqrt(x*x + y*y)
            if length == 0:
                return (0.0, 0.0)
            return (x/length, y/length)
        elif len(vector) == 3:
            x, y, z = vector
            length = math.sqrt(x*x + y*y + z*z)
            if length == 0:
                return (0.0, 0.0, 0.0)
            return (x/length, y/length, z/length)
        else:
            raise ValueError("Vector must be 2D or 3D")
            
    except Exception as e:
        logger.error(f"Error normalizing vector: {e}")
        return vector

def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp value between min and max
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        float: Clamped value
    """
    return max(min_val, min(value, max_val))

def lerp(start: float, end: float, t: float) -> float:
    """
    Linear interpolation between start and end
    
    Args:
        start: Start value
        end: End value
        t: Interpolation factor (0-1)
        
    Returns:
        float: Interpolated value
    """
    return start + (end - start) * clamp(t, 0.0, 1.0)

def is_point_in_polygon(point: Point2D, polygon: List[Point2D]) -> bool:
    """
    Check if point is inside polygon using ray casting algorithm
    
    Args:
        point: Point to check
        polygon: List of polygon vertices
        
    Returns:
        bool: True if point is inside polygon
    """
    try:
        if len(polygon) < 3:
            return False
        
        x, y = point
        inside = False
        
        # Ensure polygon is closed
        if polygon[0] != polygon[-1]:
            polygon = polygon + [polygon[0]]
        
        j = len(polygon) - 1
        for i in range(len(polygon)):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        
        return inside
        
    except Exception as e:
        logger.error(f"Error checking point in polygon: {e}")
        return False

def format_number(value: float, decimals: int = 2, unit: str = "") -> str:
    """
    Format number with specified decimals and unit
    
    Args:
        value: Number to format
        decimals: Number of decimal places
        unit: Unit suffix
        
    Returns:
        str: Formatted number string
    """
    try:
        if value == 0:
            return f"0{unit}"
        
        if abs(value) < 0.001:
            return f"{value:.2e}{unit}"
        elif abs(value) >= 1000000:
            return f"{value/1000000:.{decimals}f}M{unit}"
        elif abs(value) >= 1000:
            return f"{value/1000:.{decimals}f}k{unit}"
        else:
            return f"{value:.{decimals}f}{unit}"
            
    except Exception as e:
        logger.error(f"Error formatting number: {e}")
        return str(value)

def get_file_size(file_path: str) -> str:
    """
    Get human-readable file size
    
    Args:
        file_path: Path to file
        
    Returns:
        str: Human-readable file size
    """
    try:
        size_bytes = os.path.getsize(file_path)
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.2f} TB"
        
    except Exception as e:
        logger.error(f"Error getting file size: {e}")
        return "Unknown"

def create_backup(file_path: str, backup_dir: Optional[str] = None) -> bool:
    """
    Create backup of file
    
    Args:
        file_path: Path to file to backup
        backup_dir: Backup directory (uses file directory if None)
        
    Returns:
        bool: True if backup created successfully
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File not found for backup: {file_path}")
            return False
        
        if backup_dir is None:
            backup_dir = os.path.dirname(file_path)
        
        os.makedirs(backup_dir, exist_ok=True)
        
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{os.path.splitext(filename)[0]}_backup_{timestamp}{os.path.splitext(filename)[1]}"
        backup_path = os.path.join(backup_dir, backup_name)
        
        import shutil
        shutil.copy2(file_path, backup_path)
        
        logger.info(f"Backup created: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return False

def parse_version(version_string: str) -> Tuple[int, int, int]:
    """
    Parse version string into major, minor, patch tuple
    
    Args:
        version_string: Version string (e.g., "1.2.3")
        
    Returns:
        Tuple of (major, minor, patch)
    """
    try:
        parts = version_string.split('.')
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return (major, minor, patch)
    except Exception as e:
        logger.error(f"Error parsing version: {e}")
        return (0, 0, 0)

def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two version strings
    
    Args:
        version1: First version string
        version2: Second version string
        
    Returns:
        int: -1 if version1 < version2, 0 if equal, 1 if version1 > version2
    """
    try:
        v1 = parse_version(version1)
        v2 = parse_version(version2)
        
        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
        else:
            return 0
            
    except Exception as e:
        logger.error(f"Error comparing versions: {e}")
        return 0

def get_plugin_directory() -> Path:
    """
    Get the plugin installation directory
    
    Returns:
        Path: Plugin directory path
    """
    try:
        return Path(__file__).parent.parent
    except Exception as e:
        logger.error(f"Error getting plugin directory: {e}")
        return Path.home() / "AutoCAD_Structural_Plugin"

def is_autocad_running() -> bool:
    """
    Check if AutoCAD is running and available
    
    Returns:
        bool: True if AutoCAD is running
    """
    try:
        import clr
        from Autodesk.AutoCAD.ApplicationServices import Application
        return Application.DocumentManager.MdiActiveDocument is not None
    except Exception:
        return False

def measure_execution_time(func):
    """
    Decorator to measure function execution time
    
    Usage:
        @measure_execution_time
        def my_function():
            ...
    """
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        logger.log_performance(func.__name__, duration_ms, {
            'args_count': len(args),
            'kwargs_count': len(kwargs)
        })
        
        return result
    return wrapper