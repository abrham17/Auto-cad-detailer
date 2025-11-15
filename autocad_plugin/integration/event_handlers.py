"""
AutoCAD event handlers for the structural plugin
"""
import threading
from datetime import datetime

from utils.logger import logger
from integration.autocad_api import AutoCADAPI

class EventHandlers:
    """Handle AutoCAD events for the structural plugin"""
    
    def __init__(self):
        self.api = AutoCADAPI()
        self.registered_events = {}
        self.is_initialized = False
        
    def initialize_events(self):
        """Initialize all event handlers"""
        if self.is_initialized:
            return
            
        try:
            self._register_document_events()
            self._register_entity_events()
            self._register_application_events()
            
            self.is_initialized = True
            logger.info("AutoCAD event handlers initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing event handlers: {str(e)}")
            
    def _register_document_events(self):
        """Register document-related events"""
        try:
            doc_mgr = self.api.application.DocumentManager
            
            # Document activated event
            self.registered_events['DocumentActivated'] = doc_mgr.DocumentActivated
            self.registered_events['DocumentActivated'] += self._on_document_activated
            
            # Document to be destroyed event
            self.registered_events['DocumentToBeDestroyed'] = doc_mgr.DocumentToBeDestroyed
            self.registered_events['DocumentToBeDestroyed'] += self._on_document_to_be_destroyed
            
            logger.debug("Document events registered")
            
        except Exception as e:
            logger.error(f"Error registering document events: {str(e)}")
            
    def _register_entity_events(self):
        """Register entity-related events"""
        try:
            doc = self.api.get_active_document()
            if not doc:
                return
                
            # Database event for object modification
            self.registered_events['ObjectModified'] = doc.Database.ObjectModified
            self.registered_events['ObjectModified'] += self._on_object_modified
            
            # Object erased event
            self.registered_events['ObjectErased'] = doc.Database.ObjectErased
            self.registered_events['ObjectErased'] += self._on_object_erased
            
            logger.debug("Entity events registered")
            
        except Exception as e:
            logger.error(f"Error registering entity events: {str(e)}")
            
    def _register_application_events(self):
        """Register application-level events"""
        try:
            app = self.api.application.Application
            
            # System variable changed
            self.registered_events['SysVarChanged'] = app.SysVarChanged
            self.registered_events['SysVarChanged'] += self._on_sysvar_changed
            
            # Begin command event
            self.registered_events['BeginCommand'] = app.BeginCommand
            self.registered_events['BeginCommand'] += self._on_begin_command
            
            # End command event  
            self.registered_events['EndCommand'] = app.EndCommand
            self.registered_events['EndCommand'] += self._on_end_command
            
            logger.debug("Application events registered")
            
        except Exception as e:
            logger.error(f"Error registering application events: {str(e)}")
            
    def _on_document_activated(self, sender, e):
        """Handle document activated event"""
        try:
            logger.info(f"Document activated: {e.Document.Name}")
            
            # Re-initialize API for new document
            self.api._initialize_application()
            
            # Re-register entity events for new document
            self._register_entity_events()
            
            # Notify other components about document change
            self._notify_document_change(e.Document.Name)
            
        except Exception as ex:
            logger.error(f"Error in document activated handler: {str(ex)}")
            
    def _on_document_to_be_destroyed(self, sender, e):
        """Handle document to be destroyed event"""
        try:
            logger.info(f"Document to be destroyed: {e.Document.Name}")
            
            # Clean up document-specific resources
            self._cleanup_document_resources(e.Document.Name)
            
        except Exception as ex:
            logger.error(f"Error in document destruction handler: {str(ex)}")
            
    def _on_object_modified(self, sender, e):
        """Handle object modified event"""
        try:
            # Check if this is a structural entity
            if self._is_structural_entity(e.DBObject):
                entity_data = self._get_entity_data(e.DBObject)
                if entity_data:
                    self._handle_structural_modification(entity_data)
                    
        except Exception as ex:
            logger.error(f"Error in object modified handler: {str(ex)}")
            
    def _on_object_erased(self, sender, e):
        """Handle object erased event"""
        try:
            # Check if this is a structural entity being erased
            if self._is_structural_entity(e.DBObject) and e.Erased:
                entity_data = self._get_entity_data(e.DBObject)
                if entity_data:
                    self._handle_structural_deletion(entity_data)
                    
        except Exception as ex:
            logger.error(f"Error in object erased handler: {str(ex)}")
            
    def _on_sysvar_changed(self, sender, e):
        """Handle system variable changed event"""
        try:
            # Monitor specific system variables that affect structural elements
            important_vars = ['INSUNITS', 'DIMSTYLE', 'LUNITS', 'LUPREC']
            
            if e.Name in important_vars:
                logger.info(f"System variable changed: {e.Name} = {e.Value}")
                self._handle_system_variable_change(e.Name, e.Value)
                
        except Exception as ex:
            logger.error(f"Error in system variable handler: {str(ex)}")
            
    def _on_begin_command(self, sender, e):
        """Handle begin command event"""
        try:
            # Track commands that might affect structural elements
            structural_commands = ['MOVE', 'ROTATE', 'SCALE', 'COPY', 'MIRROR']
            
            if e.GlobalCommandName.upper() in structural_commands:
                logger.debug(f"Structural command started: {e.GlobalCommandName}")
                self._pre_command_cleanup(e.GlobalCommandName)
                
        except Exception as ex:
            logger.error(f"Error in begin command handler: {str(ex)}")
            
    def _on_end_command(self, sender, e):
        """Handle end command event"""
        try:
            structural_commands = ['MOVE', 'ROTATE', 'SCALE', 'COPY', 'MIRROR']
            
            if e.GlobalCommandName.upper() in structural_commands:
                logger.debug(f"Structural command ended: {e.GlobalCommandName}")
                self._post_command_processing(e.GlobalCommandName)
                
        except Exception as ex:
            logger.error(f"Error in end command handler: {str(ex)}")
            
    def _is_structural_entity(self, db_object):
        """Check if entity is a structural element"""
        try:
            if not db_object:
                return False
                
            # Check layer
            layer = db_object.Layer
            structural_layers = [
                'STRUCTURAL_COLUMNS',
                'STRUCTURAL_WALLS', 
                'STRUCTURAL_BEAMS',
                'STRUCTURAL_SLABS',
                'STRUCTURAL_FOUNDATIONS'
            ]
            
            if layer.upper() in structural_layers:
                return True
                
            # Check for structural XData
            xdata = self.api.get_entity_xdata(db_object, 'STRUCTURAL_DATA')
            return len(xdata) > 0
            
        except Exception as e:
            logger.error(f"Error checking structural entity: {str(e)}")
            return False
            
    def _get_entity_data(self, db_object):
        """Extract structural data from entity"""
        try:
            entity_data = {
                'handle': str(db_object.Handle),
                'layer': db_object.Layer,
                'type': self._get_entity_type(db_object),
                'timestamp': datetime.now().isoformat()
            }
            
            # Add XData if available
            xdata = self.api.get_entity_xdata(db_object, 'STRUCTURAL_DATA')
            if xdata:
                entity_data['xdata'] = xdata
                
            # Add geometric data based on entity type
            geometry_data = self._extract_geometry_data(db_object)
            if geometry_data:
                entity_data['geometry'] = geometry_data
                
            return entity_data
            
        except Exception as e:
            logger.error(f"Error getting entity data: {str(e)}")
            return None
            
    def _get_entity_type(self, db_object):
        """Determine entity type from layer or properties"""
        layer = db_object.Layer.upper()
        
        if 'COLUMN' in layer:
            return 'column'
        elif 'WALL' in layer:
            return 'wall'
        elif 'BEAM' in layer:
            return 'beam'
        elif 'SLAB' in layer:
            return 'slab'
        elif 'FOUNDATION' in layer:
            return 'foundation'
        else:
            return 'unknown'
            
    def _extract_geometry_data(self, db_object):
        """Extract relevant geometry data from entity"""
        try:
            geometry_data = {}
            
            # This would be implemented based on specific entity types
            # For example, for a line: start point, end point
            # For a polyline: vertices, etc.
            
            return geometry_data
            
        except Exception as e:
            logger.error(f"Error extracting geometry data: {str(e)}")
            return {}
            
    def _handle_structural_modification(self, entity_data):
        """Handle modification of structural elements"""
        try:
            from .realtime_sync import RealTimeSync
            sync_service = RealTimeSync()
            
            sync_data = {
                'type': 'modification',
                'entity_type': entity_data['type'],
                'entity_id': entity_data['handle'],
                'data': entity_data,
                'change_type': 'modify'
            }
            
            sync_service.queue_for_sync(sync_data)
            logger.debug(f"Queued modification sync for entity {entity_data['handle']}")
            
        except Exception as e:
            logger.error(f"Error handling structural modification: {str(e)}")
            
    def _handle_structural_deletion(self, entity_data):
        """Handle deletion of structural elements"""
        try:
            from .realtime_sync import RealTimeSync
            sync_service = RealTimeSync()
            
            sync_data = {
                'type': 'deletion',
                'entity_type': entity_data['type'],
                'entity_id': entity_data['handle'],
                'data': entity_data,
                'change_type': 'delete'
            }
            
            sync_service.queue_for_sync(sync_data)
            logger.debug(f"Queued deletion sync for entity {entity_data['handle']}")
            
        except Exception as e:
            logger.error(f"Error handling structural deletion: {str(e)}")
            
    def _notify_document_change(self, document_name):
        """Notify other components about document change"""
        try:
            # This would integrate with other parts of the plugin
            # to handle document switching
            pass
            
        except Exception as e:
            logger.error(f"Error notifying document change: {str(e)}")
            
    def _cleanup_document_resources(self, document_name):
        """Clean up resources when document is closed"""
        try:
            # Clean up any document-specific caches or resources
            logger.info(f"Cleaned up resources for document: {document_name}")
            
        except Exception as e:
            logger.error(f"Error cleaning up document resources: {str(e)}")
            
    def _handle_system_variable_change(self, var_name, var_value):
        """Handle system variable changes that affect structural elements"""
        try:
            # Handle unit changes
            if var_name == 'INSUNITS':
                self._handle_unit_change(var_value)
                
        except Exception as e:
            logger.error(f"Error handling system variable change: {str(e)}")
            
    def _handle_unit_change(self, new_units):
        """Handle drawing unit changes"""
        try:
            logger.info(f"Drawing units changed to: {new_units}")
            # Notify components that need to handle unit conversions
            
        except Exception as e:
            logger.error(f"Error handling unit change: {str(e)}")
            
    def _pre_command_cleanup(self, command_name):
        """Perform cleanup before structural command execution"""
        try:
            # Prepare for command execution
            pass
            
        except Exception as e:
            logger.error(f"Error in pre-command cleanup: {str(e)}")
            
    def _post_command_processing(self, command_name):
        """Process changes after structural command execution"""
        try:
            # Handle post-command processing
            pass
            
        except Exception as e:
            logger.error(f"Error in post-command processing: {str(e)}")
            
    def dispose(self):
        """Clean up event handlers"""
        try:
            # Unregister all events
            for event_name, event in self.registered_events.items():
                try:
                    # This would properly unregister the events
                    # Implementation depends on specific event types
                    pass
                except Exception as e:
                    logger.error(f"Error unregistering event {event_name}: {str(e)}")
                    
            self.registered_events.clear()
            self.is_initialized = False
            logger.info("Event handlers disposed successfully")
            
        except Exception as e:
            logger.error(f"Error disposing event handlers: {str(e)}")