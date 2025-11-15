"""
Cache management service for structural data and API responses
"""
import json
import pickle
import sqlite3
import os
from datetime import datetime, timedelta
from threading import Lock, RLock

from utils.logger import logger
from utils.config import Config

class CacheManager:
    """Cache management with persistence and expiration"""
    
    def __init__(self):
        self.cache_dir = Config.get('cache_dir', 'cache')
        self.max_cache_size = Config.get('max_cache_size', 100 * 1024 * 1024)  # 100MB
        self.default_ttl = Config.get('default_ttl', 3600)  # 1 hour
        
        self._memory_cache = {}
        self._db_connection = None
        self._lock = RLock()
        self._initialized = False
        
        self._initialize_cache()
        
    def _initialize_cache(self):
        """Initialize cache system"""
        try:
            # Create cache directory
            os.makedirs(self.cache_dir, exist_ok=True)
            
            # Initialize SQLite database for persistent cache
            db_path = os.path.join(self.cache_dir, 'cache.db')
            self._db_connection = sqlite3.connect(db_path, check_same_thread=False)
            self._create_cache_tables()
            
            # Clean up expired entries on startup
            self._cleanup_expired()
            
            self._initialized = True
            logger.info("Cache manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing cache manager: {str(e)}")
            
    def _create_cache_tables(self):
        """Create cache database tables"""
        try:
            cursor = self._db_connection.cursor()
            
            # Main cache table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Cache metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    name TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache(last_accessed)')
            
            self._db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error creating cache tables: {str(e)}")
            
    def set(self, key, value, ttl=None, persistent=True):
        """Set cache value with optional TTL"""
        try:
            with self._lock:
                if ttl is None:
                    ttl = self.default_ttl
                    
                expires_at = datetime.now() + timedelta(seconds=ttl)
                
                # Store in memory cache
                self._memory_cache[key] = {
                    'value': value,
                    'expires_at': expires_at,
                    'created_at': datetime.now(),
                    'access_count': 0
                }
                
                # Store in persistent cache if requested
                if persistent:
                    self._set_persistent(key, value, expires_at)
                    
                logger.debug(f"Cache set for key: {key}")
                return True
                
        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {str(e)}")
            return False
            
    def _set_persistent(self, key, value, expires_at):
        """Set value in persistent cache"""
        try:
            cursor = self._db_connection.cursor()
            
            # Serialize value
            serialized_value = pickle.dumps(value)
            
            cursor.execute('''
                INSERT OR REPLACE INTO cache (key, value, expires_at, access_count, last_accessed)
                VALUES (?, ?, ?, 0, CURRENT_TIMESTAMP)
            ''', (key, serialized_value, expires_at))
            
            self._db_connection.commit()
            
            # Check cache size and cleanup if needed
            self._enforce_cache_limits()
            
        except Exception as e:
            logger.error(f"Error setting persistent cache for key {key}: {str(e)}")
            
    def get(self, key, default=None):
        """Get cached value"""
        try:
            with self._lock:
                # First check memory cache
                if key in self._memory_cache:
                    cache_item = self._memory_cache[key]
                    if cache_item['expires_at'] > datetime.now():
                        # Update access statistics
                        cache_item['access_count'] += 1
                        logger.debug(f"Cache hit (memory) for key: {key}")
                        return cache_item['value']
                    else:
                        # Remove expired item
                        del self._memory_cache[key]
                        
                # Check persistent cache
                persistent_value = self._get_persistent(key)
                if persistent_value is not None:
                    # Also store in memory cache for faster access
                    ttl = (persistent_value['expires_at'] - datetime.now()).total_seconds()
                    if ttl > 0:
                        self.set(key, persistent_value['value'], ttl=ttl, persistent=False)
                    logger.debug(f"Cache hit (persistent) for key: {key}")
                    return persistent_value['value']
                    
                logger.debug(f"Cache miss for key: {key}")
                return default
                
        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {str(e)}")
            return default
            
    def _get_persistent(self, key):
        """Get value from persistent cache"""
        try:
            cursor = self._db_connection.cursor()
            
            cursor.execute('''
                SELECT value, expires_at FROM cache 
                WHERE key = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ''', (key,))
            
            result = cursor.fetchone()
            if result:
                value_data, expires_at = result
                
                # Update access statistics
                cursor.execute('''
                    UPDATE cache 
                    SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP
                    WHERE key = ?
                ''', (key,))
                self._db_connection.commit()
                
                # Deserialize value
                value = pickle.loads(value_data)
                return {
                    'value': value,
                    'expires_at': datetime.fromisoformat(expires_at) if expires_at else None
                }
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting persistent cache for key {key}: {str(e)}")
            return None
            
    def delete(self, key):
        """Delete cached value"""
        try:
            with self._lock:
                # Remove from memory cache
                if key in self._memory_cache:
                    del self._memory_cache[key]
                    
                # Remove from persistent cache
                cursor = self._db_connection.cursor()
                cursor.execute('DELETE FROM cache WHERE key = ?', (key,))
                self._db_connection.commit()
                
                logger.debug(f"Cache deleted for key: {key}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {str(e)}")
            return False
            
    def exists(self, key):
        """Check if key exists in cache and is not expired"""
        try:
            with self._lock:
                # Check memory cache
                if key in self._memory_cache:
                    if self._memory_cache[key]['expires_at'] > datetime.now():
                        return True
                    else:
                        del self._memory_cache[key]
                        return False
                        
                # Check persistent cache
                cursor = self._db_connection.cursor()
                cursor.execute('''
                    SELECT 1 FROM cache 
                    WHERE key = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                ''', (key,))
                
                return cursor.fetchone() is not None
                
        except Exception as e:
            logger.error(f"Error checking cache existence for key {key}: {str(e)}")
            return False
            
    def clear(self, pattern=None):
        """Clear cache entries, optionally matching pattern"""
        try:
            with self._lock:
                cleared_count = 0
                
                # Clear memory cache
                if pattern:
                    keys_to_delete = [k for k in self._memory_cache.keys() if pattern in k]
                    for key in keys_to_delete:
                        del self._memory_cache[key]
                        cleared_count += 1
                else:
                    cleared_count = len(self._memory_cache)
                    self._memory_cache.clear()
                    
                # Clear persistent cache
                cursor = self._db_connection.cursor()
                if pattern:
                    cursor.execute('DELETE FROM cache WHERE key LIKE ?', (f'%{pattern}%',))
                else:
                    cursor.execute('DELETE FROM cache')
                    
                cleared_count += cursor.rowcount
                self._db_connection.commit()
                
                logger.info(f"Cleared {cleared_count} cache entries")
                return cleared_count
                
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return 0
            
    def _cleanup_expired(self):
        """Remove expired cache entries"""
        try:
            with self._lock:
                # Clean memory cache
                current_time = datetime.now()
                expired_keys = [
                    key for key, item in self._memory_cache.items() 
                    if item['expires_at'] <= current_time
                ]
                for key in expired_keys:
                    del self._memory_cache[key]
                    
                # Clean persistent cache
                cursor = self._db_connection.cursor()
                cursor.execute('DELETE FROM cache WHERE expires_at <= CURRENT_TIMESTAMP')
                deleted_count = cursor.rowcount
                self._db_connection.commit()
                
                if deleted_count > 0:
                    logger.debug(f"Cleaned up {deleted_count} expired cache entries")
                    
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {str(e)}")
            
    def _enforce_cache_limits(self):
        """Enforce cache size limits"""
        try:
            cursor = self._db_connection.cursor()
            
            # Get current cache size
            cursor.execute('SELECT SUM(LENGTH(value)) FROM cache')
            result = cursor.fetchone()
            current_size = result[0] or 0
            
            if current_size > self.max_cache_size:
                # Remove least recently used items
                cursor.execute('''
                    DELETE FROM cache 
                    WHERE key IN (
                        SELECT key FROM cache 
                        ORDER BY last_accessed ASC 
                        LIMIT (SELECT COUNT(*) * 0.1 FROM cache)
                    )
                ''')
                self._db_connection.commit()
                
                logger.info(f"Cache size limit enforced, removed old entries")
                
        except Exception as e:
            logger.error(f"Error enforcing cache limits: {str(e)}")
            
    def get_stats(self):
        """Get cache statistics"""
        try:
            with self._lock:
                cursor = self._db_connection.cursor()
                
                # Memory cache stats
                memory_stats = {
                    'entries': len(self._memory_cache),
                    'expired_entries': len([
                        k for k, v in self._memory_cache.items() 
                        if v['expires_at'] <= datetime.now()
                    ])
                }
                
                # Persistent cache stats
                cursor.execute('SELECT COUNT(*) FROM cache')
                persistent_entries = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM cache WHERE expires_at <= CURRENT_TIMESTAMP')
                expired_persistent = cursor.fetchone()[0]
                
                cursor.execute('SELECT SUM(LENGTH(value)) FROM cache')
                total_size = cursor.fetchone()[0] or 0
                
                cursor.execute('SELECT AVG(access_count) FROM cache')
                avg_access = cursor.fetchone()[0] or 0
                
                return {
                    'memory_cache': memory_stats,
                    'persistent_cache': {
                        'entries': persistent_entries,
                        'expired_entries': expired_persistent,
                        'total_size_bytes': total_size,
                        'average_access_count': round(avg_access, 2)
                    },
                    'total_entries': memory_stats['entries'] + persistent_entries
                }
                
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {}
            
    def prefetch(self, keys_with_ttl):
        """Prefetch multiple keys into cache"""
        try:
            with self._lock:
                success_count = 0
                for key, (value, ttl) in keys_with_ttl.items():
                    if self.set(key, value, ttl=ttl):
                        success_count += 1
                        
                logger.debug(f"Prefetched {success_count} items into cache")
                return success_count
                
        except Exception as e:
            logger.error(f"Error prefetching cache items: {str(e)}")
            return 0
            
    def close(self):
        """Close cache and clean up resources"""
        try:
            with self._lock:
                if self._db_connection:
                    self._db_connection.close()
                self._memory_cache.clear()
                logger.info("Cache manager closed")
                
        except Exception as e:
            logger.error(f"Error closing cache manager: {str(e)}")