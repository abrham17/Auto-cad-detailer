"""
Validation and license management utilities
"""

import subprocess
import platform
import hashlib
import logging
from typing import Set, Optional, Dict, Any
from pathlib import Path

class LicenseManager:
    """Manages software licensing and machine authorization"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Authorized machine IDs (hashed)
        self.authorized_machines: Set[str] = {
            self._hash_machine_id("4CE351D6T9-BFEBFBFF00090672-BE8A4584"),
            self._hash_machine_id("1CSPLG3-BFEBFBFF000A0653-6427AA17"),
            self._hash_machine_id("1XHTWV3-BFEBFBFF00090675-980127AE"),
            self._hash_machine_id("GZ5TPM3-BFEBFBFF000A0653-C8CD709F"),
            self._hash_machine_id("9kff314-BFEBFBFF00090675-BE00C22D"),
            self._hash_machine_id("GNN6LL3-BFEBFBFF000A0653-0EE96299"),
            self._hash_machine_id("H5SX014-BFEBFBFF00090675-D2A62B0E")
        }
    
    def is_licensed(self) -> bool:
        """Check if current machine is licensed"""
        try:
            machine_id = self._get_machine_id()
            hashed_id = self._hash_machine_id(machine_id)
            
            licensed = hashed_id in self.authorized_machines
            
            if licensed:
                self.logger.info("Machine license verified successfully")
            else:
                self.logger.warning(f"Machine not authorized: {machine_id}")
            
            return licensed
            
        except Exception as e:
            self.logger.error(f"License check failed: {e}")
            return False
    
    def _get_machine_id(self) -> str:
        """Generate unique machine ID"""
        bios_serial = self._get_bios_serial()
        processor_id = self._get_processor_id()
        volume_serial = self._get_volume_serial()
        
        machine_id = f"{bios_serial}-{processor_id}-{volume_serial}"
        return machine_id.strip()
    
    def _get_bios_serial(self) -> str:
        """Get BIOS serial number"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ['wmic', 'bios', 'get', 'serialnumber'], 
                    capture_output=True, text=True, check=True
                )
                lines = result.stdout.strip().split('\n')
                return lines[2].strip() if len(lines) > 2 else "UNKNOWN"
            else:
                return "UNKNOWN"
        except Exception as e:
            self.logger.warning(f"Failed to get BIOS serial: {e}")
            return "UNKNOWN"
    
    def _get_processor_id(self) -> str:
        """Get processor ID"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ['wmic', 'cpu', 'get', 'processorid'], 
                    capture_output=True, text=True, check=True
                )
                lines = result.stdout.strip().split('\n')
                return lines[2].strip() if len(lines) > 2 else "UNKNOWN"
            else:
                return "UNKNOWN"
        except Exception as e:
            self.logger.warning(f"Failed to get processor ID: {e}")
            return "UNKNOWN"
    
    def _get_volume_serial(self) -> str:
        """Get volume serial number for C: drive"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ['wmic', 'logicaldisk', 'where', "deviceid='C:'", 'get', 'volumeserialnumber'], 
                    capture_output=True, text=True, check=True
                )
                lines = result.stdout.strip().split('\n')
                return lines[2].strip() if len(lines) > 2 else "UNKNOWN"
            else:
                return "UNKNOWN"
        except Exception as e:
            self.logger.warning(f"Failed to get volume serial: {e}")
            return "UNKNOWN"
    
    def _hash_machine_id(self, machine_id: str) -> str:
        """Hash machine ID for security"""
        return hashlib.sha256(machine_id.encode()).hexdigest()

class DataValidator:
    """Validates input data for column detailing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Minimum and maximum allowed values
        self.limits = {
            'column_length': {'min': 100, 'max': 5000},  # mm
            'column_width': {'min': 0, 'max': 5000},     # mm (0 for circular)
            'floor_height': {'min': 2000, 'max': 50000}, # mm
            'rebar_diameter': {'min': 6, 'max': 50},     # mm
            'stirrup_diameter': {'min': 6, 'max': 16},   # mm
            'concrete_cover': {'min': 20, 'max': 100},   # mm
            'spacing': {'min': 50, 'max': 500}           # mm
        }
    
    def validate_column_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete column data"""
        errors = []
        warnings = []
        
        # Validate settings
        settings_errors = self._validate_settings(data.get('settings', {}))
        errors.extend(settings_errors)
        
        # Validate floors
        for i, floor in enumerate(data.get('floors', [])):
            floor_errors = self._validate_floor(floor, i)
            errors.extend(floor_errors)
            
            floor_warnings = self._check_floor_warnings(floor, i)
            warnings.extend(floor_warnings)
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_settings(self, settings: Dict[str, Any]) -> List[str]:
        """Validate column settings"""
        errors = []
        
        required_fields = [
            'beam_depth', 'beam_extension', 'concrete_cover', 
            'scale', 'spacing_between_columns'
        ]
        
        for field in required_fields:
            if field not in settings or settings[field] is None:
                errors.append(f"Missing required setting: {field}")
        
        # Validate numeric values
        if 'beam_depth' in settings:
            if not self._is_in_range(settings['beam_depth'], 'floor_height'):
                errors.append(f"Beam depth {settings['beam_depth']} is out of range")
        
        if 'concrete_cover' in settings:
            if not self._is_in_range(settings['concrete_cover'], 'concrete_cover'):
                errors.append(f"Concrete cover {settings['concrete_cover']} is out of range")
        
        return errors
    
    def _validate_floor(self, floor: Dict[str, Any], floor_index: int) -> List[str]:
        """Validate individual floor data"""
        errors = []
        
        required_fields = [
            'total_height', 'column_length', 'floor_name',
            'rebar_amount', 'rebar_diameter'
        ]
        
        for field in required_fields:
            if field not in floor or floor[field] is None:
                errors.append(f"Floor {floor_index + 1}: Missing {field}")
        
        # Validate dimensions
        if 'total_height' in floor:
            if not self._is_in_range(floor['total_height'], 'floor_height'):
                errors.append(f"Floor {floor_index + 1}: Height {floor['total_height']} is out of range")
        
        if 'column_length' in floor:
            if not self._is_in_range(floor['column_length'], 'column_length'):
                errors.append(f"Floor {floor_index + 1}: Length {floor['column_length']} is out of range")
        
        if 'column_width' in floor and floor['column_width'] > 0:
            if not self._is_in_range(floor['column_width'], 'column_width'):
                errors.append(f"Floor {floor_index + 1}: Width {floor['column_width']} is out of range")
        
        # Validate reinforcement
        if 'rebar_diameter' in floor:
            if not self._is_in_range(floor['rebar_diameter'], 'rebar_diameter'):
                errors.append(f"Floor {floor_index + 1}: Rebar diameter {floor['rebar_diameter']} is out of range")
        
        if 'stirrup_diameter' in floor:
            if not self._is_in_range(floor['stirrup_diameter'], 'stirrup_diameter'):
                errors.append(f"Floor {floor_index + 1}: Stirrup diameter {floor['stirrup_diameter']} is out of range")
        
        # Validate rebar amounts
        if all(field in floor for field in ['rebar_amount', 'rebar_amount_x', 'rebar_amount_y']):
            expected = self._calculate_expected_rebars(floor['rebar_amount_x'], floor['rebar_amount_y'])
            if floor['rebar_amount'] != expected:
                errors.append(f"Floor {floor_index + 1}: Rebar amount mismatch. Expected {expected}, got {floor['rebar_amount']}")
        
        return errors
    
    def _check_floor_warnings(self, floor: Dict[str, Any], floor_index: int) -> List[str]:
        """Check for potential issues (warnings)"""
        warnings = []
        
        # Check concrete cover vs column size
        if all(field in floor for field in ['column_length', 'column_width']):
            cover = floor.get('concrete_cover', 25)
            if cover * 2 >= floor['column_length']:
                warnings.append(f"Floor {floor_index + 1}: Concrete cover may be too large for column length")
        
        # Check stirrup spacing
        if 'edge_stirrup_spacing' in floor and 'mid_stirrup_spacing' in floor:
            if floor['edge_stirrup_spacing'] < 75:
                warnings.append(f"Floor {floor_index + 1}: Edge stirrup spacing is very small")
            if floor['mid_stirrup_spacing'] > 300:
                warnings.append(f"Floor {floor_index + 1}: Mid stirrup spacing is large")
        
        return warnings
    
    def _is_in_range(self, value: float, value_type: str) -> bool:
        """Check if value is within allowed range"""
        if value_type in self.limits:
            limits = self.limits[value_type]
            return limits['min'] <= value <= limits['max']
        return True
    
    def _calculate_expected_rebars(self, amount_x: int, amount_y: int) -> int:
        """Calculate expected total rebar amount"""
        if amount_x > 0 and amount_y > 0:
            return 2 * amount_x + 2 * max(0, amount_y - 2)
        elif amount_x > 0 and amount_y == 0:
            return amount_x
        else:
            return 0

class UnitConverter:
    """Handles unit conversions"""
    
    @staticmethod
    def mm_to_m(value: float) -> float:
        """Convert millimeters to meters"""
        return value / 1000.0
    
    @staticmethod
    def m_to_mm(value: float) -> float:
        """Convert meters to millimeters"""
        return value * 1000.0
    
    @staticmethod
    def mm_to_cm(value: float) -> float:
        """Convert millimeters to centimeters"""
        return value / 10.0
    
    @staticmethod
    def cm_to_mm(value: float) -> float:
        """Convert centimeters to millimeters"""
        return value * 10.0
    
    @staticmethod
    def kg_to_ton(value: float) -> float:
        """Convert kilograms to metric tons"""
        return value / 1000.0
    
    @staticmethod
    def ton_to_kg(value: float) -> float:
        """Convert metric tons to kilograms"""
        return value * 1000.0