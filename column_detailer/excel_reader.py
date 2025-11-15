"""
Excel data reader for column details
"""

import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ColumnSettings:
    """Column drawing settings"""
    beam_depth: float
    beam_extension: float
    concrete_cover: float
    scale: float
    spacing_between_columns: float
    foundation_depth: float
    foundation_cover: float
    section_scale: float
    is_foundation_string: bool = False

@dataclass
class FloorData:
    """Data for each floor"""
    total_height: float
    column_length: float
    column_width: float
    floor_name: str
    rebar_amount: int
    rebar_amount_x: int
    rebar_amount_y: int
    rebar_diameter: float
    edge_stirrup_spacing: float
    mid_stirrup_spacing: float
    stirrup_diameter: float
    section_number: int = 0

@dataclass
class ColumnData:
    """Complete column data"""
    settings: ColumnSettings
    floors: List[FloorData]
    column_name: str

class ExcelColumnReader:
    """Reads column data from Excel files"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.required_columns = [
            'Total Floor Height', 'Column Length', 'Column Width', 'Floor Name',
            'Rebar Amount', 'Rebar Amount X', 'Rebar Amount Y', 'Rebar Diameter',
            'Edge Stirrup Spacing', 'Mid Stirrup Spacing', 'Stirrup Diameter'
        ]
    
    def read_column_file(self, file_path: str) -> Dict[str, ColumnData]:
        """Read all column data from Excel file"""
        try:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Excel file not found: {file_path}")
            
            # Read settings
            settings = self._read_settings(file_path)
            
            # Read all column data sheets
            column_data = {}
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                if sheet_name.lower().startswith('columndata'):
                    column_name = sheet_name.replace('ColumnData', '').strip() or f"Column_{len(column_data) + 1}"
                    column_data[column_name] = self._read_column_sheet(file_path, sheet_name, settings)
            
            if not column_data:
                raise ValueError("No valid column data sheets found in the Excel file")
            
            return column_data
            
        except Exception as e:
            self.logger.error(f"Error reading column file: {e}")
            raise
    
    def _read_settings(self, file_path: str) -> ColumnSettings:
        """Read settings from Settings worksheet"""
        try:
            df = pd.read_excel(file_path, sheet_name='Settings', header=None)
            
            # Get values with error handling
            beam_depth = self._get_numeric_value(df, 0, 1, "Beam Depth")
            beam_extension = self._get_numeric_value(df, 1, 1, "Beam Extension")
            concrete_cover = self._get_numeric_value(df, 2, 1, "Concrete Cover")
            scale = self._get_numeric_value(df, 3, 1, "Scale")
            spacing = self._get_numeric_value(df, 4, 1, "Spacing Between Columns")
            
            # Foundation depth might be string or number
            foundation_depth_val = self._get_cell_value(df, 5, 1)
            is_string = False
            foundation_depth = 1000.0
            
            if isinstance(foundation_depth_val, str):
                is_string = True
            else:
                try:
                    foundation_depth = float(foundation_depth_val)
                except (ValueError, TypeError):
                    is_string = True
            
            foundation_cover = self._get_numeric_value(df, 6, 1, "Foundation Cover")
            section_scale = self._get_numeric_value(df, 7, 1, "Section Scale")
            
            return ColumnSettings(
                beam_depth=beam_depth,
                beam_extension=beam_extension,
                concrete_cover=concrete_cover,
                scale=scale,
                spacing_between_columns=spacing,
                foundation_depth=foundation_depth,
                foundation_cover=foundation_cover,
                section_scale=section_scale,
                is_foundation_string=is_string
            )
            
        except Exception as e:
            self.logger.error(f"Error reading settings: {e}")
            raise
    
    def _read_column_sheet(self, file_path: str, sheet_name: str, settings: ColumnSettings) -> ColumnData:
        """Read data from a specific column sheet"""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=0)
            
            # Validate required columns
            missing_columns = [col for col in self.required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns in {sheet_name}: {missing_columns}")
            
            floors = []
            for _, row in df.iterrows():
                if pd.notna(row['Total Floor Height']):
                    floor_data = FloorData(
                        total_height=float(row['Total Floor Height']),
                        column_length=float(row['Column Length']),
                        column_width=float(row['Column Width']),
                        floor_name=str(row['Floor Name']),
                        rebar_amount=int(row['Rebar Amount']),
                        rebar_amount_x=int(row['Rebar Amount X']),
                        rebar_amount_y=int(row['Rebar Amount Y']),
                        rebar_diameter=float(row['Rebar Diameter']),
                        edge_stirrup_spacing=float(row['Edge Stirrup Spacing']),
                        mid_stirrup_spacing=float(row['Mid Stirrup Spacing']),
                        stirrup_diameter=float(row['Stirrup Diameter'])
                    )
                    floors.append(floor_data)
            
            if not floors:
                raise ValueError(f"No valid floor data found in {sheet_name}")
            
            return ColumnData(settings=settings, floors=floors, column_name=sheet_name)
            
        except Exception as e:
            self.logger.error(f"Error reading column sheet {sheet_name}: {e}")
            raise
    
    def _get_numeric_value(self, df: pd.DataFrame, row: int, col: int, field_name: str) -> float:
        """Get numeric value from DataFrame with validation"""
        try:
            value = df.iloc[row, col]
            if pd.isna(value):
                raise ValueError(f"{field_name} is missing")
            return float(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid value for {field_name}: {df.iloc[row, col]}")
    
    def _get_cell_value(self, df: pd.DataFrame, row: int, col: int) -> Any:
        """Get raw cell value"""
        try:
            return df.iloc[row, col]
        except IndexError:
            return None