"""
License management service for the AutoCAD structural plugin
"""
import hashlib
import uuid
import json
import socket
from datetime import datetime, timedelta
from threading import Lock

from utils.logger import logger
from utils.config import Config
from .api_client import APIClient
from .cache_manager import CacheManager

class LicenseService:
    """License management and validation service"""
    
    def __init__(self):
        self.api_client = APIClient()
        self.cache_manager = CacheManager()
        
        self.license_data = None
        self.license_key = None
        self.machine_id = self._get_machine_id()
        
        self._validation_lock = Lock()
        self._last_validation = None
        self._validation_interval = timedelta(hours=1)  # Revalidate every hour
        
        self._load_license_data()
        
    def _get_machine_id(self):
        """Generate unique machine identifier"""
        try:
            # Use combination of hostname and MAC address
            hostname = socket.gethostname()
            
            # Get MAC address (platform-specific)
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                           for elements in range(0, 8*6, 8)][::-1])
            
            machine_string = f"{hostname}_{mac}"
            return hashlib.sha256(machine_string.encode()).hexdigest()[:32]
            
        except Exception as e:
            logger.error(f"Error generating machine ID: {str(e)}")
            return str(uuid.uuid4())
            
    def _load_license_data(self):
        """Load license data from cache or configuration"""
        try:
            # Try to load from cache first
            cached_license = self.cache_manager.get('license_data')
            if cached_license:
                self.license_data = cached_license
                self.license_key = Config.get('license_key')
                logger.debug("License data loaded from cache")
                
        except Exception as e:
            logger.error(f"Error loading license data: {str(e)}")
            
    def validate_license(self, license_key=None):
        """Validate license key"""
        with self._validation_lock:
            try:
                if license_key:
                    self.license_key = license_key
                    
                if not self.license_key:
                    logger.error("No license key provided")
                    return False
                    
                # Check if we recently validated
                if (self._last_validation and 
                    self.license_data and 
                    datetime.now() - self._last_validation < self._validation_interval):
                    return self._is_license_valid(self.license_data)
                    
                # Validate with license server
                validation_result = self._validate_with_server()
                
                if validation_result:
                    self.license_data = validation_result
                    self._last_validation = datetime.now()
                    
                    # Cache license data
                    self.cache_manager.set('license_data', validation_result, ttl=3600)
                    
                    # Save license key to config
                    Config.set('license_key', self.license_key)
                    Config.save()
                    
                    logger.info("License validation successful")
                    return True
                else:
                    logger.error("License validation failed")
                    return False
                    
            except Exception as e:
                logger.error(f"Error validating license: {str(e)}")
                return False
                
    def _validate_with_server(self):
        """Validate license with license server"""
        try:
            payload = {
                'license_key': self.license_key,
                'machine_id': self.machine_id,
                'plugin_version': Config.get('plugin_version', '1.0.0'),
                'validation_timestamp': datetime.now().isoformat()
            }
            
            response = self.api_client.post('/api/license/validate', payload)
            
            if response and response.get('valid'):
                return response.get('license_data')
            else:
                logger.warning(f"License server response: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error validating with license server: {str(e)}")
            return None
            
    def _is_license_valid(self, license_data):
        """Check if license data is valid"""
        try:
            if not license_data:
                return False
                
            # Check expiration
            expiry_str = license_data.get('expires_at')
            if expiry_str:
                expiry_date = datetime.fromisoformat(expiry_str)
                if expiry_date < datetime.now():
                    logger.warning("License has expired")
                    return False
                    
            # Check features
            if not license_data.get('features'):
                logger.warning("No features in license")
                return False
                
            # Check machine binding
            if license_data.get('machine_bound') and license_data.get('machine_id') != self.machine_id:
                logger.warning("License not valid for this machine")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking license validity: {str(e)}")
            return False
            
    def get_license_info(self):
        """Get comprehensive license information"""
        try:
            if not self.license_data:
                return {
                    'status': 'no_license',
                    'message': 'No license data available'
                }
                
            is_valid = self._is_license_valid(self.license_data)
            
            info = {
                'status': 'valid' if is_valid else 'invalid',
                'license_type': self.license_data.get('type', 'unknown'),
                'expires_at': self.license_data.get('expires_at'),
                'features': self.license_data.get('features', []),
                'machine_bound': self.license_data.get('machine_bound', False),
                'last_validation': self._last_validation.isoformat() if self._last_validation else None,
                'days_remaining': self._get_days_remaining()
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting license info: {str(e)}")
            return {'status': 'error', 'error': str(e)}
            
    def _get_days_remaining(self):
        """Calculate days remaining until license expiry"""
        try:
            expiry_str = self.license_data.get('expires_at')
            if not expiry_str:
                return None
                
            expiry_date = datetime.fromisoformat(expiry_str)
            now = datetime.now()
            
            if expiry_date < now:
                return 0
                
            return (expiry_date - now).days
            
        except Exception as e:
            logger.error(f"Error calculating days remaining: {str(e)}")
            return None
            
    def has_feature(self, feature_name):
        """Check if license includes specific feature"""
        try:
            if not self.license_data:
                return False
                
            features = self.license_data.get('features', [])
            return feature_name in features
            
        except Exception as e:
            logger.error(f"Error checking feature {feature_name}: {str(e)}")
            return False
            
    def get_available_features(self):
        """Get list of available features"""
        try:
            if not self.license_data:
                return []
                
            return self.license_data.get('features', [])
            
        except Exception as e:
            logger.error(f"Error getting available features: {str(e)}")
            return []
            
    def activate_trial(self, email=None):
        """Activate trial license"""
        try:
            payload = {
                'email': email,
                'machine_id': self.machine_id,
                'plugin_version': Config.get('plugin_version', '1.0.0')
            }
            
            response = self.api_client.post('/api/license/trial', payload)
            
            if response and response.get('success'):
                trial_license = response.get('license_data')
                if trial_license:
                    self.license_data = trial_license
                    self.license_key = trial_license.get('license_key')
                    
                    # Save to config
                    Config.set('license_key', self.license_key)
                    Config.save()
                    
                    # Cache license data
                    self.cache_manager.set('license_data', trial_license, ttl=3600)
                    
                    logger.info("Trial license activated successfully")
                    return True
                    
            logger.error("Failed to activate trial license")
            return False
            
        except Exception as e:
            logger.error(f"Error activating trial license: {str(e)}")
            return False
            
    def deactivate_license(self):
        """Deactivate current license"""
        try:
            if self.license_key:
                # Notify server about deactivation
                payload = {
                    'license_key': self.license_key,
                    'machine_id': self.machine_id
                }
                
                self.api_client.post('/api/license/deactivate', payload)
                
            # Clear local license data
            self.license_data = None
            self.license_key = None
            
            # Clear from config and cache
            Config.set('license_key', '')
            Config.save()
            self.cache_manager.delete('license_data')
            
            logger.info("License deactivated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating license: {str(e)}")
            return False
            
    def check_for_updates(self):
        """Check for license updates or upgrades"""
        try:
            if not self.license_key:
                return {'available': False, 'message': 'No active license'}
                
            payload = {
                'license_key': self.license_key,
                'current_version': Config.get('plugin_version', '1.0.0')
            }
            
            response = self.api_client.post('/api/license/updates', payload)
            
            if response and response.get('available'):
                return {
                    'available': True,
                    'new_version': response.get('new_version'),
                    'release_notes': response.get('release_notes'),
                    'download_url': response.get('download_url')
                }
            else:
                return {'available': False, 'message': 'No updates available'}
                
        except Exception as e:
            logger.error(f"Error checking for updates: {str(e)}")
            return {'available': False, 'error': str(e)}
            
    def get_usage_statistics(self):
        """Get license usage statistics"""
        try:
            if not self.license_key:
                return {}
                
            payload = {
                'license_key': self.license_key,
                'machine_id': self.machine_id
            }
            
            response = self.api_client.post('/api/license/usage', payload)
            
            if response:
                return response.get('usage_data', {})
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error getting usage statistics: {str(e)}")
            return {}
            
    def is_license_active(self):
        """Check if license is currently active and valid"""
        try:
            if not self.license_data:
                return False
                
            return self._is_license_valid(self.license_data)
            
        except Exception as e:
            logger.error(f"Error checking license activity: {str(e)}")
            return False
            
    def refresh_license(self):
        """Force refresh of license data from server"""
        try:
            self._last_validation = None  # Force revalidation
            return self.validate_license()
            
        except Exception as e:
            logger.error(f"Error refreshing license: {str(e)}")
            return False
            
    def get_license_summary(self):
        """Get user-friendly license summary"""
        try:
            info = self.get_license_info()
            
            if info['status'] == 'no_license':
                return "No license active - Please activate your license"
                
            elif info['status'] == 'valid':
                license_type = info.get('license_type', 'Unknown').title()
                days_remaining = info.get('days_remaining')
                
                if days_remaining is not None:
                    if days_remaining > 30:
                        return f"{license_type} License (Valid)"
                    elif days_remaining > 0:
                        return f"{license_type} License (Expires in {days_remaining} days)"
                    else:
                        return f"{license_type} License (Expired)"
                else:
                    return f"{license_type} License (Valid)"
                    
            else:
                return "License Invalid - Please contact support"
                
        except Exception as e:
            logger.error(f"Error generating license summary: {str(e)}")
            return "License Status Unknown"