"""
Advanced logging utility for AutoCAD Structural Plugin
"""
import logging
import logging.handlers
import os
import sys
import inspect
from datetime import datetime
from pathlib import Path

class Logger:
    """Advanced logger with AutoCAD integration and multiple handlers"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.logger = None
            self.log_level = logging.INFO
            self.log_file = None
            self._initialize_logger()
            self._initialized = True
    
    def _initialize_logger(self):
        """Initialize the logger with multiple handlers"""
        try:
            # Create logger
            self.logger = logging.getLogger('AutoCAD_Structural_Plugin')
            self.logger.setLevel(self.log_level)
            self.logger.propagate = False
            
            # Clear any existing handlers
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
            
            # Create logs directory
            log_dir = self._get_log_directory()
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Set log file path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = log_dir / f"structural_plugin_{timestamp}.log"
            
            # Create formatters
            detailed_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            simple_formatter = logging.Formatter(
                '%(levelname)-8s | %(message)s'
            )
            
            # File handler (detailed)
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(file_handler)
            
            # Console handler (simple)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(simple_formatter)
            self.logger.addHandler(console_handler)
            
            # AutoCAD command line handler (minimal)
            autocad_handler = AutoCADHandler()
            autocad_handler.setLevel(logging.WARNING)
            autocad_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            self.logger.addHandler(autocad_handler)
            
            self.info("Logger initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize logger: {e}")
    
    def _get_log_directory(self):
        """Get the log directory path"""
        try:
            # Try to use AutoCAD plugin directory first
            plugin_dir = Path(__file__).parent.parent
            log_dir = plugin_dir / "logs"
            return log_dir
        except:
            # Fallback to user documents
            documents_dir = Path.home() / "Documents" / "AutoCAD_Structural_Plugin" / "logs"
            return documents_dir
    
    def set_level(self, level):
        """Set logging level"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if level.upper() in level_map:
            self.log_level = level_map[level.upper()]
            self.logger.setLevel(self.log_level)
            for handler in self.logger.handlers:
                handler.setLevel(self.log_level)
    
    def debug(self, message, extra_data=None):
        """Log debug message"""
        self._log(logging.DEBUG, message, extra_data)
    
    def info(self, message, extra_data=None):
        """Log info message"""
        self._log(logging.INFO, message, extra_data)
    
    def warning(self, message, extra_data=None):
        """Log warning message"""
        self._log(logging.WARNING, message, extra_data)
    
    def error(self, message, extra_data=None):
        """Log error message"""
        self._log(logging.ERROR, message, extra_data)
    
    def critical(self, message, extra_data=None):
        """Log critical message"""
        self._log(logging.CRITICAL, message, extra_data)
    
    def _log(self, level, message, extra_data=None):
        """Internal logging method with caller information"""
        try:
            # Get caller information
            frame = inspect.currentframe().f_back.f_back
            caller_info = inspect.getframeinfo(frame)
            
            # Prepare log record
            log_record = {
                'filename': os.path.basename(caller_info.filename),
                'lineno': caller_info.lineno,
                'function': caller_info.function
            }
            
            # Add extra data if provided
            if extra_data:
                if isinstance(extra_data, dict):
                    log_record.update(extra_data)
                else:
                    log_record['extra_data'] = str(extra_data)
            
            # Format message with extra data
            formatted_message = str(message)
            if extra_data:
                formatted_message += f" | {extra_data}"
            
            self.logger.log(level, formatted_message, extra=log_record)
            
        except Exception as e:
            # Fallback logging if main logger fails
            print(f"LOG[{level}]: {message} | Error: {e}")
    
    def log_command(self, command_name, parameters=None, success=True):
        """Log command execution"""
        command_data = {
            'command': command_name,
            'parameters': parameters or {},
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        level = logging.INFO if success else logging.ERROR
        self._log(level, f"Command executed: {command_name}", command_data)
    
    def log_entity_operation(self, operation, entity_type, entity_id, details=None):
        """Log entity operations"""
        operation_data = {
            'operation': operation,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.info(f"Entity {operation}: {entity_type} ({entity_id})", operation_data)
    
    def log_performance(self, operation, duration_ms, details=None):
        """Log performance metrics"""
        performance_data = {
            'operation': operation,
            'duration_ms': duration_ms,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        
        if duration_ms > 1000:
            self.warning(f"Slow operation: {operation} took {duration_ms}ms", performance_data)
        else:
            self.debug(f"Performance: {operation} took {duration_ms}ms", performance_data)
    
    def get_log_file_path(self):
        """Get current log file path"""
        return str(self.log_file) if self.log_file else None
    
    def export_logs(self, target_path=None):
        """Export logs to specified location"""
        try:
            if not self.log_file or not self.log_file.exists():
                return False
            
            if not target_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                target_path = Path.home() / "Desktop" / f"plugin_logs_export_{timestamp}.log"
            
            # Copy current log file
            import shutil
            shutil.copy2(self.log_file, target_path)
            
            self.info(f"Logs exported to: {target_path}")
            return True
            
        except Exception as e:
            self.error(f"Failed to export logs: {e}")
            return False
    
    def clear_old_logs(self, days_to_keep=30):
        """Clear log files older than specified days"""
        try:
            log_dir = self._get_log_directory()
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            
            deleted_count = 0
            for log_file in log_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                self.info(f"Cleared {deleted_count} old log files")
            
            return deleted_count
            
        except Exception as e:
            self.error(f"Failed to clear old logs: {e}")
            return 0
    
    def get_log_stats(self):
        """Get logging statistics"""
        try:
            log_dir = self._get_log_directory()
            log_files = list(log_dir.glob("*.log"))
            
            total_size = sum(f.stat().st_size for f in log_files)
            oldest_log = min((f.stat().st_mtime for f in log_files), default=0)
            
            return {
                'total_log_files': len(log_files),
                'total_size_bytes': total_size,
                'current_log_file': self.get_log_file_path(),
                'oldest_log_timestamp': datetime.fromtimestamp(oldest_log).isoformat() if oldest_log > 0 else None,
                'log_level': logging.getLevelName(self.log_level)
            }
            
        except Exception as e:
            self.error(f"Failed to get log stats: {e}")
            return {}


class AutoCADHandler(logging.Handler):
    """Custom handler for AutoCAD command line output"""
    
    def emit(self, record):
        try:
            # Try to import AutoCAD .NET API
            import clr
            from Autodesk.AutoCAD.ApplicationServices import Application
            
            message = self.format(record)
            
            # Send to AutoCAD command line
            doc = Application.DocumentManager.MdiActiveDocument
            if doc:
                editor = doc.Editor
                if record.levelno >= logging.ERROR:
                    editor.WriteMessage(f"\n{message}\n")
                elif record.levelno >= logging.WARNING:
                    editor.WriteMessage(f"\n{message}\n")
                    
        except Exception:
            # Fallback to console if AutoCAD not available
            print(f"AUTOCAD: {record.levelname}: {record.getMessage()}")


# Global logger instance
logger = Logger()

# Convenience functions
def debug(message, extra_data=None):
    logger.debug(message, extra_data)

def info(message, extra_data=None):
    logger.info(message, extra_data)

def warning(message, extra_data=None):
    logger.warning(message, extra_data)

def error(message, extra_data=None):
    logger.error(message, extra_data)

def critical(message, extra_data=None):
    logger.critical(message, extra_data)