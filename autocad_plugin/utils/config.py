"""
Configuration management for AutoCAD Structural Plugin
"""
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

from .logger import logger

class Config:
    """Configuration management with persistence and validation"""
    
    _instance = None
    _config_data = {}
    _config_file = None
    _default_config = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._load_defaults()
            self._initialize_config()
    
    def _load_defaults(self):
        """Load default configuration values"""
        self._default_config = {
            'plugin': {
                'version': '1.0.0',
                'auto_update_check': True,
                'check_interval_hours': 24,
                'backup_enabled': True,
                'backup_count': 5
            },
            'logging': {
                'level': 'INFO',
                'max_file_size_mb': 10,
                'backup_count': 5,
                'auto_cleanup_days': 30
            },
            'ui': {
                'palette_visible': True,
                'palette_dock_side': 'left',
                'palette_width': 300,
                'palette_opacity': 100,
                'ribbon_visible': True,
                'toolbar_visible': False,
                'theme': 'system'
            },
            'sync': {
                'enabled': True,
                'interval_seconds': 30,
                'max_retries': 3,
                'batch_size': 50,
                'auto_sync': True
            },
            'api': {
                'base_url': 'https://api.structural.example.com',
                'timeout_seconds': 30,
                'retry_count': 3,
                'cache_enabled': True,
                'cache_ttl_minutes': 60
            },
            'units': {
                'system': 'metric',
                'length_unit': 'mm',
                'force_unit': 'kN',
                'moment_unit': 'kNm',
                'stress_unit': 'MPa'
            },
            'structural': {
                'default_material': 'Concrete C30',
                'default_reinforcement_grade': '500 MPa',
                'safety_factors': {
                    'concrete': 1.5,
                    'steel': 1.15,
                    'load': 1.35
                },
                'auto_calculate': True,
                'validate_geometry': True
            },
            'license': {
                'key': '',
                'type': 'trial',
                'expires_at': None,
                'features': []
            }
        }
    
    def _initialize_config(self):
        """Initialize configuration system"""
        try:
            # Determine config file location
            self._config_file = self._get_config_file_path()
            
            # Load existing config or create default
            if self._config_file.exists():
                self._load_config()
            else:
                self._config_data = self._default_config.copy()
                self._save_config()
                
            logger.info("Configuration system initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize configuration: {e}")
            self._config_data = self._default_config.copy()
    
    def _get_config_file_path(self) -> Path:
        """Get configuration file path"""
        try:
            # Try plugin directory first
            plugin_dir = Path(__file__).parent.parent
            config_dir = plugin_dir / "config"
            config_dir.mkdir(exist_ok=True)
            return config_dir / "plugin_config.json"
        except:
            # Fallback to user directory
            user_dir = Path.home() / "AppData" / "Roaming" / "AutoCAD_Structural_Plugin"
            user_dir.mkdir(parents=True, exist_ok=True)
            return user_dir / "config.json"
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            with open(self._config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Merge with defaults (deep merge)
            self._config_data = self._deep_merge(self._default_config, loaded_config)
            
            logger.debug("Configuration loaded from file")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._config_data = self._default_config.copy()
    
    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in update.items():
            if (key in result and 
                isinstance(result[key], dict) and 
                isinstance(value, dict)):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            # Create backup if file exists
            if self._config_file.exists():
                backup_file = self._config_file.with_suffix('.json.backup')
                shutil.copy2(self._config_file, backup_file)
            
            # Save config
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, indent=2, ensure_ascii=False)
            
            logger.debug("Configuration saved to file")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (dot notation supported)"""
        try:
            keys = key.split('.')
            value = self._config_data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            logger.debug(f"Error getting config key '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """Set configuration value (dot notation supported)"""
        try:
            keys = key.split('.')
            config_ref = self._config_data
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config_ref or not isinstance(config_ref[k], dict):
                    config_ref[k] = {}
                config_ref = config_ref[k]
            
            # Set the value
            config_ref[keys[-1]] = value
            
            # Save if requested
            if save:
                return self._save_config()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to set config key '{key}': {e}")
            return False
    
    def save(self) -> bool:
        """Save current configuration to file"""
        return self._save_config()
    
    def reset(self, section: Optional[str] = None) -> bool:
        """Reset configuration to defaults"""
        try:
            if section:
                if section in self._default_config:
                    self._config_data[section] = self._default_config[section].copy()
                else:
                    logger.warning(f"Section '{section}' not found in defaults")
                    return False
            else:
                self._config_data = self._default_config.copy()
            
            return self._save_config()
            
        except Exception as e:
            logger.error(f"Failed to reset configuration: {e}")
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration data"""
        return self._config_data.copy()
    
    def export_config(self, file_path: str) -> bool:
        """Export configuration to specified file"""
        try:
            export_data = {
                'config': self._config_data,
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'version': self.get('plugin.version'),
                    'exported_from': 'AutoCAD Structural Plugin'
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration exported to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """Import configuration from file"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"Import file not found: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate import data
            if 'config' not in import_data:
                logger.error("Invalid configuration file format")
                return False
            
            # Merge imported config
            self._config_data = self._deep_merge(self._config_data, import_data['config'])
            
            # Save merged config
            success = self._save_config()
            
            if success:
                logger.info(f"Configuration imported from: {file_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration and return issues"""
        issues = {}
        
        # Check required sections
        required_sections = ['plugin', 'api', 'units']
        for section in required_sections:
            if section not in self._config_data:
                issues[section] = f"Missing required section: {section}"
        
        # Validate API configuration
        api_url = self.get('api.base_url')
        if not api_url or not api_url.startswith(('http://', 'https://')):
            issues['api.base_url'] = "Invalid API base URL"
        
        # Validate units
        valid_units = {
            'system': ['metric', 'imperial'],
            'length_unit': ['mm', 'cm', 'm', 'in', 'ft'],
            'force_unit': ['N', 'kN', 'lbf', 'kip'],
            'stress_unit': ['Pa', 'kPa', 'MPa', 'GPa', 'psi', 'ksi']
        }
        
        for unit_type, valid_values in valid_units.items():
            current_value = self.get(f'units.{unit_type}')
            if current_value not in valid_values:
                issues[f'units.{unit_type}'] = f"Invalid {unit_type}: {current_value}"
        
        # Validate sync settings
        sync_interval = self.get('sync.interval_seconds')
        if sync_interval and (sync_interval < 5 or sync_interval > 3600):
            issues['sync.interval_seconds'] = "Sync interval must be between 5 and 3600 seconds"
        
        return issues
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration metadata and statistics"""
        return {
            'config_file': str(self._config_file) if self._config_file else None,
            'file_exists': self._config_file.exists() if self._config_file else False,
            'file_size': self._config_file.stat().st_size if self._config_file and self._config_file.exists() else 0,
            'last_modified': datetime.fromtimestamp(self._config_file.stat().st_mtime).isoformat() if self._config_file and self._config_file.exists() else None,
            'validation_issues': self.validate_config(),
            'sections_count': len(self._config_data),
            'plugin_version': self.get('plugin.version')
        }


# Global config instance
config = Config()

# Convenience functions
def get_config(key: str, default: Any = None) -> Any:
    return config.get(key, default)

def set_config(key: str, value: Any, save: bool = True) -> bool:
    return config.set(key, value, save)

def save_config() -> bool:
    return config.save()