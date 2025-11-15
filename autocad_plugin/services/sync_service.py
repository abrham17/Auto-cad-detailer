"""
Synchronization service for structural data between AutoCAD and external systems
"""
import threading
import time
import json
from queue import Queue, PriorityQueue, Empty
from datetime import datetime, timedelta
from enum import Enum

from utils.logger import logger
from utils.config import Config
from .api_client import APIClient
from .cache_manager import CacheManager

class SyncPriority(Enum):
    HIGH = 1
    NORMAL = 2
    LOW = 3

class SyncService:
    """Main synchronization service for structural data"""
    
    def __init__(self):
        self.api_client = APIClient()
        self.cache_manager = CacheManager()
        
        self.sync_queue = PriorityQueue()
        self.failed_syncs = []
        self.sync_history = []
        
        self.is_running = False
        self.sync_thread = None
        self.sync_interval = Config.get('sync_interval', 10)  # seconds
        self.max_history_size = Config.get('max_sync_history', 1000)
        self.max_retries = Config.get('sync_max_retries', 3)
        
        self._stats = {
            'successful_syncs': 0,
            'failed_syncs': 0,
            'last_sync_time': None,
            'total_items_processed': 0
        }
        
        self._lock = threading.RLock()
        
    def start(self):
        """Start the synchronization service"""
        if self.is_running:
            logger.warning("Sync service already running")
            return
            
        self.is_running = True
        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()
        logger.info("Synchronization service started")
        
    def stop(self):
        """Stop the synchronization service"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        logger.info("Synchronization service stopped")
        
    def queue_sync(self, data, priority=SyncPriority.NORMAL, entity_type=None, operation='create'):
        """Queue data for synchronization"""
        try:
            sync_item = {
                'id': self._generate_sync_id(),
                'data': data,
                'entity_type': entity_type or data.get('type', 'unknown'),
                'operation': operation,
                'priority': priority,
                'timestamp': datetime.now(),
                'retry_count': 0,
                'status': 'queued'
            }
            
            # Calculate priority score (lower = higher priority)
            priority_score = priority.value
            
            self.sync_queue.put((priority_score, sync_item))
            
            with self._lock:
                self._stats['total_items_processed'] += 1
                
            logger.debug(f"Queued sync item: {sync_item['id']} (priority: {priority.name})")
            return sync_item['id']
            
        except Exception as e:
            logger.error(f"Error queueing sync data: {str(e)}")
            return None
            
    def _generate_sync_id(self):
        """Generate unique sync ID"""
        return f"sync_{int(time.time())}_{threading.get_ident()}"
        
    def _sync_worker(self):
        """Background worker for processing sync queue"""
        while self.is_running:
            try:
                # Process items from queue
                processed_count = 0
                while not self.sync_queue.empty() and processed_count < 10:  # Process up to 10 items per cycle
                    try:
                        priority, sync_item = self.sync_queue.get_nowait()
                        self._process_sync_item(sync_item)
                        processed_count += 1
                    except Empty:
                        break
                        
                # Wait for next cycle
                time.sleep(self.sync_interval)
                
            except Exception as e:
                logger.error(f"Error in sync worker: {str(e)}")
                time.sleep(self.sync_interval)  # Prevent tight loop on errors
                
    def _process_sync_item(self, sync_item):
        """Process a single sync item"""
        try:
            sync_item['status'] = 'processing'
            sync_item['processing_start'] = datetime.now()
            
            success = self._sync_to_external_service(sync_item)
            
            sync_item['processing_end'] = datetime.now()
            sync_item['status'] = 'completed' if success else 'failed'
            
            if success:
                with self._lock:
                    self._stats['successful_syncs'] += 1
                    self._stats['last_sync_time'] = datetime.now()
                logger.debug(f"Successfully synced item: {sync_item['id']}")
            else:
                with self._lock:
                    self._stats['failed_syncs'] += 1
                    
                # Handle retry logic
                sync_item['retry_count'] += 1
                if sync_item['retry_count'] < self.max_retries:
                    # Re-queue with higher priority
                    sync_item['priority'] = SyncPriority.HIGH
                    self.sync_queue.put((SyncPriority.HIGH.value, sync_item))
                    logger.warning(f"Sync failed, requeuing item {sync_item['id']} "
                                 f"(attempt {sync_item['retry_count']})")
                else:
                    # Max retries exceeded
                    logger.error(f"Max retries exceeded for sync item: {sync_item['id']}")
                    self._handle_failed_sync(sync_item)
                    
            # Add to history
            self._add_to_history(sync_item)
            
        except Exception as e:
            logger.error(f"Error processing sync item {sync_item['id']}: {str(e)}")
            sync_item['status'] = 'error'
            sync_item['error'] = str(e)
            self._add_to_history(sync_item)
            
    def _sync_to_external_service(self, sync_item):
        """Sync data to external service"""
        try:
            operation = sync_item['operation']
            entity_type = sync_item['entity_type']
            data = sync_item['data']
            
            endpoint_map = {
                'create': f'/api/structural/{entity_type}s',
                'update': f'/api/structural/{entity_type}s/{data.get("entity_id")}',
                'delete': f'/api/structural/{entity_type}s/{data.get("entity_id")}',
                'batch': '/api/structural/batch'
            }
            
            endpoint = endpoint_map.get(operation)
            if not endpoint:
                logger.error(f"Unknown operation: {operation}")
                return False
                
            # Prepare payload
            payload = {
                'entity_data': data,
                'operation': operation,
                'sync_timestamp': datetime.now().isoformat(),
                'sync_id': sync_item['id']
            }
            
            # Make API call based on operation
            if operation == 'create':
                response = self.api_client.post(endpoint, payload)
            elif operation == 'update':
                response = self.api_client.put(endpoint, payload)
            elif operation == 'delete':
                response = self.api_client.delete(endpoint)
            elif operation == 'batch':
                response = self.api_client.post(endpoint, payload)
                
            return response is not None and response.get('success', False)
            
        except Exception as e:
            logger.error(f"Error syncing to external service: {str(e)}")
            return False
            
    def _handle_failed_sync(self, sync_item):
        """Handle permanently failed sync items"""
        try:
            # Store in failed syncs list
            self.failed_syncs.append(sync_item)
            
            # Cache for manual recovery
            cache_key = f"failed_sync_{sync_item['id']}"
            self.cache_manager.set(cache_key, sync_item, ttl=86400)  # 24 hours
            
            # Log failure
            logger.error(f"Sync permanently failed for item: {sync_item['id']}")
            
        except Exception as e:
            logger.error(f"Error handling failed sync: {str(e)}")
            
    def _add_to_history(self, sync_item):
        """Add sync item to history"""
        try:
            with self._lock:
                self.sync_history.append(sync_item.copy())
                
                # Limit history size
                if len(self.sync_history) > self.max_history_size:
                    self.sync_history = self.sync_history[-self.max_history_size:]
                    
        except Exception as e:
            logger.error(f"Error adding to sync history: {str(e)}")
            
    def get_sync_status(self):
        """Get current synchronization status"""
        with self._lock:
            status = {
                'is_running': self.is_running,
                'queue_size': self.sync_queue.qsize(),
                'failed_syncs_count': len(self.failed_syncs),
                'history_size': len(self.sync_history),
                'stats': self._stats.copy()
            }
            
            return status
            
    def retry_failed_syncs(self):
        """Retry all failed syncs"""
        try:
            retry_count = 0
            failed_syncs_copy = self.failed_syncs.copy()
            self.failed_syncs.clear()
            
            for sync_item in failed_syncs_copy:
                sync_item['retry_count'] = 0
                sync_item['status'] = 'queued'
                self.sync_queue.put((SyncPriority.HIGH.value, sync_item))
                retry_count += 1
                
            logger.info(f"Retrying {retry_count} failed syncs")
            return retry_count
            
        except Exception as e:
            logger.error(f"Error retrying failed syncs: {str(e)}")
            return 0
            
    def clear_history(self):
        """Clear sync history"""
        with self._lock:
            cleared_count = len(self.sync_history)
            self.sync_history.clear()
            logger.info(f"Cleared {cleared_count} items from sync history")
            return cleared_count
            
    def export_sync_report(self, file_path=None):
        """Export sync report to file"""
        try:
            if not file_path:
                file_path = f"sync_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
            report = {
                'generated_at': datetime.now().isoformat(),
                'status': self.get_sync_status(),
                'recent_history': self.sync_history[-100:],  # Last 100 items
                'failed_syncs': self.failed_syncs
            }
            
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
                
            logger.info(f"Sync report exported to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting sync report: {str(e)}")
            return False
            
    def sync_entity_batch(self, entities_data, operation='create'):
        """Sync a batch of entities at once"""
        try:
            batch_id = f"batch_{int(time.time())}"
            
            batch_payload = {
                'batch_id': batch_id,
                'operation': operation,
                'entities': entities_data,
                'timestamp': datetime.now().isoformat()
            }
            
            return self.queue_sync(
                batch_payload, 
                priority=SyncPriority.HIGH,
                entity_type='batch',
                operation='batch'
            )
            
        except Exception as e:
            logger.error(f"Error queueing entity batch: {str(e)}")
            return None
            
    def wait_for_sync_completion(self, timeout=30):
        """Wait for all queued syncs to complete (for testing or critical operations)"""
        try:
            start_time = time.time()
            while not self.sync_queue.empty() and (time.time() - start_time) < timeout:
                time.sleep(0.1)
                
            return self.sync_queue.empty()
            
        except Exception as e:
            logger.error(f"Error waiting for sync completion: {str(e)}")
            return False