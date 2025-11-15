"""
API client for communicating with external structural analysis services
"""
import requests
import json
import time
from threading import Lock
from datetime import datetime, timedelta

from utils.logger import logger
from utils.config import Config

class APIClient:
    """HTTP client for external API communication"""
    
    def __init__(self):
        self.base_url = Config.get('api_base_url', 'https://api.structural.example.com')
        self.api_key = Config.get('api_key', '')
        self.timeout = Config.get('api_timeout', 30)
        self.max_retries = Config.get('api_max_retries', 3)
        self.retry_delay = Config.get('api_retry_delay', 1)
        
        self.session = None
        self._auth_token = None
        self._token_expiry = None
        self._lock = Lock()
        self._initialize_session()
        
    def _initialize_session(self):
        """Initialize HTTP session with proper headers"""
        try:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': f'AutoCAD-Structural-Plugin/{Config.get("plugin_version", "1.0.0")}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
            
            # Set up retry strategy
            from requests.adapters import HTTPAdapter
            from requests.packages.urllib3.util.retry import Retry
            
            retry_strategy = Retry(
                total=self.max_retries,
                backoff_factor=self.retry_delay,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
            )
            
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
            
            logger.debug("API client session initialized")
            
        except Exception as e:
            logger.error(f"Error initializing API session: {str(e)}")
            self.session = requests.Session()  # Fallback
            
    def _ensure_authentication(self):
        """Ensure we have a valid authentication token"""
        try:
            with self._lock:
                if self._auth_token and self._token_expiry and self._token_expiry > datetime.now():
                    return True
                    
                # Need to authenticate
                return self._authenticate()
                
        except Exception as e:
            logger.error(f"Error ensuring authentication: {str(e)}")
            return False
            
    def _authenticate(self):
        """Authenticate with the API server"""
        try:
            auth_endpoint = f"{self.base_url}/api/auth/token"
            
            payload = {
                'api_key': self.api_key,
                'client_info': {
                    'client_type': 'autocad_plugin',
                    'version': Config.get('plugin_version', '1.0.0')
                }
            }
            
            response = self.session.post(
                auth_endpoint,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                self._auth_token = auth_data.get('access_token')
                
                # Calculate token expiry (with 5-minute buffer)
                expires_in = auth_data.get('expires_in', 3600)
                self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)
                
                # Update session headers
                self.session.headers['Authorization'] = f'Bearer {self._auth_token}'
                
                logger.info("Successfully authenticated with API")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            return False
            
    def get(self, endpoint, params=None):
        """Perform GET request to API"""
        try:
            if not self._ensure_authentication():
                return None
                
            url = f"{self.base_url}{endpoint}"
            
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            
            return self._handle_response(response, 'GET', endpoint)
            
        except Exception as e:
            logger.error(f"GET request failed for {endpoint}: {str(e)}")
            return None
            
    def post(self, endpoint, data):
        """Perform POST request to API"""
        try:
            if not self._ensure_authentication():
                return None
                
            url = f"{self.base_url}{endpoint}"
            
            response = self.session.post(
                url,
                json=data,
                timeout=self.timeout
            )
            
            return self._handle_response(response, 'POST', endpoint)
            
        except Exception as e:
            logger.error(f"POST request failed for {endpoint}: {str(e)}")
            return None
            
    def put(self, endpoint, data):
        """Perform PUT request to API"""
        try:
            if not self._ensure_authentication():
                return None
                
            url = f"{self.base_url}{endpoint}"
            
            response = self.session.put(
                url,
                json=data,
                timeout=self.timeout
            )
            
            return self._handle_response(response, 'PUT', endpoint)
            
        except Exception as e:
            logger.error(f"PUT request failed for {endpoint}: {str(e)}")
            return None
            
    def delete(self, endpoint):
        """Perform DELETE request to API"""
        try:
            if not self._ensure_authentication():
                return None
                
            url = f"{self.base_url}{endpoint}"
            
            response = self.session.delete(
                url,
                timeout=self.timeout
            )
            
            return self._handle_response(response, 'DELETE', endpoint)
            
        except Exception as e:
            logger.error(f"DELETE request failed for {endpoint}: {str(e)}")
            return None
            
    def _handle_response(self, response, method, endpoint):
        """Handle API response with proper error handling"""
        try:
            log_message = f"{method} {endpoint} - Status: {response.status_code}"
            
            if response.status_code in [200, 201]:
                logger.debug(f"{log_message} - Success")
                try:
                    return response.json()
                except ValueError:
                    return {'success': True, 'message': 'Operation completed'}
                    
            elif response.status_code == 401:
                logger.warning(f"{log_message} - Authentication expired")
                # Clear auth token to force re-authentication
                self._auth_token = None
                return None
                
            elif response.status_code == 403:
                logger.error(f"{log_message} - Access forbidden")
                return {'success': False, 'error': 'Access forbidden'}
                
            elif response.status_code == 404:
                logger.warning(f"{log_message} - Endpoint not found")
                return {'success': False, 'error': 'Endpoint not found'}
                
            elif response.status_code == 429:
                logger.warning(f"{log_message} - Rate limit exceeded")
                # Implement rate limit backoff
                time.sleep(2)
                return {'success': False, 'error': 'Rate limit exceeded'}
                
            elif response.status_code >= 500:
                logger.error(f"{log_message} - Server error: {response.text}")
                return {'success': False, 'error': 'Server error'}
                
            else:
                logger.warning(f"{log_message} - Unexpected response: {response.text}")
                return {'success': False, 'error': f'Unexpected response: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"Error handling response: {str(e)}")
            return None
            
    def upload_file(self, endpoint, file_path, extra_data=None):
        """Upload file to API"""
        try:
            if not self._ensure_authentication():
                return None
                
            url = f"{self.base_url}{endpoint}"
            
            with open(file_path, 'rb') as file:
                files = {'file': (os.path.basename(file_path), file)}
                data = extra_data or {}
                
                response = self.session.post(
                    url,
                    files=files,
                    data=data,
                    timeout=60  # Longer timeout for file uploads
                )
                
            return self._handle_response(response, 'UPLOAD', endpoint)
            
        except Exception as e:
            logger.error(f"File upload failed for {endpoint}: {str(e)}")
            return None
            
    def download_file(self, endpoint, local_path):
        """Download file from API"""
        try:
            if not self._ensure_authentication():
                return False
                
            url = f"{self.base_url}{endpoint}"
            
            response = self.session.get(
                url,
                stream=True,
                timeout=60
            )
            
            if response.status_code == 200:
                with open(local_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                logger.info(f"File downloaded successfully: {local_path}")
                return True
            else:
                logger.error(f"File download failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"File download failed for {endpoint}: {str(e)}")
            return False
            
    def health_check(self):
        """Check API health status"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/health",
                timeout=10
            )
            
            if response.status_code == 200:
                health_data = response.json()
                return {
                    'status': 'healthy',
                    'version': health_data.get('version', 'unknown'),
                    'timestamp': health_data.get('timestamp')
                }
            else:
                return {'status': 'unhealthy', 'error': f'Status code: {response.status_code}'}
                
        except Exception as e:
            return {'status': 'unreachable', 'error': str(e)}
            
    def batch_operation(self, operations):
        """Perform batch operations"""
        try:
            endpoint = '/api/batch'
            payload = {
                'operations': operations,
                'batch_id': f"batch_{int(time.time())}",
                'timestamp': datetime.now().isoformat()
            }
            
            return self.post(endpoint, payload)
            
        except Exception as e:
            logger.error(f"Batch operation failed: {str(e)}")
            return None
            
    def get_service_status(self):
        """Get comprehensive service status"""
        try:
            # Check API health
            api_health = self.health_check()
            
            # Check authentication
            auth_status = self._ensure_authentication()
            
            status = {
                'api_health': api_health,
                'authentication': 'valid' if auth_status else 'invalid',
                'base_url': self.base_url,
                'timeout': self.timeout,
                'last_checked': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting service status: {str(e)}")
            return {'status': 'error', 'error': str(e)}
            
    def disconnect(self):
        """Clean up resources"""
        try:
            if self.session:
                self.session.close()
            logger.info("API client disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting API client: {str(e)}")