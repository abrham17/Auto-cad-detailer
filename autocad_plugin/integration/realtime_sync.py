"""
Real-time synchronization with external services and databases
"""
import threading
import time
import json
from queue import Queue, Empty
from datetime import datetime

from utils.logger import logger
from utils.config import Config
from services.api_client import APIClient
from services.cache_manager import CacheManager

class RealTimeSync:
    """Real-time synchronization service for structural data"""
    
    def __init__(self):
        self.sync_queue = Queue()
        self.is_running = False
        self.sync_thread = None
        self.sync_interval = 5  # seconds
        self.max_retries = 3
        self.api_client = APIClient()
        self.cache_manager = CacheManager()
        self.pending_changes = {}
        
    def start_sync(self):
        """Start the synchronization service"""
        if self.is_running:
            logger.warning("Sync service already running")
            return
            
        self.is_running = True
        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()
        logger.info("Real-time sync service started")
        
    def stop_sync(self):
        """Stop the synchronization service"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        logger.info("Real-time sync service stopped")
        
    def queue_for_sync(self, sync_data):
        """Queue data for synchronization"""
        try:
            sync_item = {
                'data': sync_data,
                'timestamp': datetime.now().isoformat(),
                'retry_count': 0,
                'id': f"{sync_data.get('entity_id', 'unknown')}_{int(time.time())}"
            }
            
            self.sync_queue.put(sync_item)
            self.pending_changes[sync_item['id']] = sync_item
            
            logger.debug(f"Queued sync item: {sync_item['id']}")
            return sync_item['id']
            
        except Exception as e:
            logger.error(f"Error queueing sync data: {str(e)}")
            return None
            
    def _sync_worker(self):
        """Background worker for processing sync queue"""
        while self.is_running:
            try:
                # Process all items in queue
                while not self.sync_queue.empty():
                    sync_item = self.sync_queue.get_nowait()
                    self._process_sync_item(sync_item)
                    
                # Wait for next cycle
                time.sleep(self.sync_interval)
                
            except Exception as e:
                logger.error(f"Error in sync worker: {str(e)}")
                time.sleep(self.sync_interval)  # Prevent tight loop on errors
                
    def _process_sync_item(self, sync_item):
        """Process a single sync item"""
        try:
            success = self._send_to_external_service(sync_item['data'])
            
            if success:
                # Remove from pending changes on success
                if sync_item['id'] in self.pending_changes:
                    del self.pending_changes[sync_item['id']]
                logger.debug(f"Successfully synced item: {sync_item['id']}")
                
            else:
                # Handle retry logic
                sync_item['retry_count'] += 1
                if sync_item['retry_count'] < self.max_retries:
                    # Re-queue for retry
                    self.sync_queue.put(sync_item)
                    logger.warning(f"Sync failed, requeuing item {sync_item['id']} "
                                 f"(attempt {sync_item['retry_count']})")
                else:
                    # Max retries exceeded
                    logger.error(f"Max retries exceeded for sync item: {sync_item['id']}")
                    # Cache for manual sync later
                    self._cache_failed_sync(sync_item)
                    
        except Exception as e:
            logger.error(f"Error processing sync item {sync_item['id']}: {str(e)}")
            
    def _send_to_external_service(self, data):
        """Send data to external service"""
        try:
            # Determine endpoint based on data type
            endpoint = self._get_endpoint_for_data(data)
            if not endpoint:
                logger.error(f"No endpoint found for data type: {data.get('type')}")
                return False
                
            # Prepare payload
            payload = self._prepare_payload(data)
            
            # Send to API
            response = self.api_client.post(endpoint, payload)
            
            if response and response.get('success'):
                return True
            else:
                logger.warning(f"API response indicates failure: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending to external service: {str(e)}")
            return False
            
    def _get_endpoint_for_data(self, data):
        """Get appropriate API endpoint for data type"""
        endpoints = {
            'column': '/api/structural/columns',
            'wall': '/api/structural/walls', 
            'beam': '/api/structural/beams',
            'slab': '/api/structural/slabs',
            'foundation': '/api/structural/foundations',
            'modification': '/api/structural/modifications',
            'deletion': '/api/structural/deletions'
        }
        
        data_type = data.get('type')
        return endpoints.get(data_type)
        
    def _prepare_payload(self, data):
        """Prepare payload for external service"""
        payload = {
            'entity_data': data,
            'drawing_info': self._get_drawing_info(),
            'sync_timestamp': datetime.now().isoformat(),
            'plugin_version': Config.get('plugin_version', '1.0.0')
        }
        
        return payload
        
    def _get_drawing_info(self):
        """Get current drawing information"""
        try:
            from .autocad_api import AutoCADAPI
            api = AutoCADAPI()
            
            doc = api.get_active_document()
            if doc:
                return {
                    'drawing_name': doc.Name,
                    'drawing_path': doc.Database.Filename,
                    'units': api.get_drawing_units(),
                    'last_saved': str(doc.Database.TduUpdate)
                }
            return {}
            
        except Exception as e:
            logger.error(f"Error getting drawing info: {str(e)}")
            return {}
            
    def _cache_failed_sync(self, sync_item):
        """Cache failed sync items for manual recovery"""
        try:
            cache_key = f"failed_sync_{sync_item['id']}"
            self.cache_manager.set(cache_key, sync_item, expire=86400)  # 24 hours
            
            # Also add to failed syncs list
            failed_syncs = self.cache_manager.get('failed_syncs', [])
            failed_syncs.append(sync_item['id'])
            self.cache_manager.set('failed_syncs', failed_syncs)
            
        except Exception as e:
            logger.error(f"Error caching failed sync: {str(e)}")
            
    def get_sync_status(self):
        """Get current synchronization status"""
        return {
            'is_running': self.is_running,
            'queue_size': self.sync_queue.qsize(),
            'pending_changes': len(self.pending_changes),
            'last_sync': getattr(self, 'last_sync_time', None)
        }
        
    def force_sync(self):
        """Force immediate synchronization of all pending changes"""
        try:
            processed_count = 0
            temp_queue = Queue()
            
            # Move all items to temporary queue
            while not self.sync_queue.empty():
                try:
                    item = self.sync_queue.get_nowait()
                    temp_queue.put(item)
                except Empty:
                    break
                    
            # Process all items
            while not temp_queue.empty():
                item = temp_queue.get()
                self._process_sync_item(item)
                processed_count += 1
                
            logger.info(f"Force sync completed. Processed {processed_count} items.")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error during force sync: {str(e)}")
            return 0
            
    def sync_entity_batch(self, entities_data):
        """Sync a batch of entities at once"""
        try:
            batch_payload = {
                'batch_data': entities_data,
                'batch_timestamp': datetime.now().isoformat(),
                'drawing_info': self._get_drawing_info()
            }
            
            response = self.api_client.post('/api/structural/batch', batch_payload)
            return response is not None
            
        except Exception as e:
            logger.error(f"Error syncing entity batch: {str(e)}")
            return False