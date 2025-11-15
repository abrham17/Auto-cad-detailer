"""
Core AutoCAD API integration and wrapper functions
"""
import clr
import sys
import os

# Add AutoCAD .NET references
try:
    # Add common AutoCAD .NET assembly paths
    acad_paths = [
        r"C:\Program Files\Autodesk\AutoCAD 2023\AccoreMgd.dll",
        r"C:\Program Files\Autodesk\AutoCAD 2023\AcDbMgd.dll",
        r"C:\Program Files\Autodesk\AutoCAD 2023\AcMgd.dll",
        r"C:\Program Files\Autodesk\AutoCAD 2023\acdbmgdbrep.dll"
    ]
    
    for path in acad_paths:
        if os.path.exists(path):
            clr.AddReference(path)
    
    # Import AutoCAD .NET namespaces
    from Autodesk.AutoCAD.ApplicationServices import *
    from Autodesk.AutoCAD.DatabaseServices import *
    from Autodesk.AutoCAD.Runtime import *
    from Autodesk.AutoCAD.Geometry import *
    from Autodesk.AutoCAD.EditorInput import *
    from Autodesk.AutoCAD.Colors import *
    
    AUTOCAD_AVAILABLE = True
    
except Exception as e:
    AUTOCAD_AVAILABLE = False
    print(f"AutoCAD API not available: {e}")

from utils.logger import logger

class AutoCADAPI:
    """Main AutoCAD API wrapper class"""
    
    def __init__(self):
        self.application = None
        self.document = None
        self.database = None
        self.editor = None
        self._initialize_application()
        
    def _initialize_application(self):
        """Initialize connection to AutoCAD application"""
        try:
            if not AUTOCAD_AVAILABLE:
                logger.warning("AutoCAD .NET API not available - running in test mode")
                return
                
            self.application = Application.DocumentManager.MdiActiveDocument
            if self.application:
                self.document = self.application
                self.database = self.document.Database
                self.editor = self.document.Editor
                logger.info("AutoCAD application initialized successfully")
            else:
                logger.warning("No active AutoCAD document found")
                
        except Exception as e:
            logger.error(f"Failed to initialize AutoCAD application: {str(e)}")
            
    def get_active_document(self):
        """Get active document with error handling"""
        try:
            if self.document and self.document.IsActive:
                return self.document
            else:
                # Try to refresh the connection
                self._initialize_application()
                return self.document
        except Exception as e:
            logger.error(f"Error getting active document: {str(e)}")
            return None
            
    def create_transaction(self):
        """Create a database transaction"""
        try:
            doc = self.get_active_document()
            if doc:
                transaction = doc.TransactionManager.StartTransaction()
                return transaction
            return None
        except Exception as e:
            logger.error(f"Error creating transaction: {str(e)}")
            return None
            
    def commit_transaction(self, transaction):
        """Commit a transaction with error handling"""
        try:
            if transaction:
                transaction.Commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error committing transaction: {str(e)}")
            return False
            
    def abort_transaction(self, transaction):
        """Abort a transaction with error handling"""
        try:
            if transaction:
                transaction.Abort()
                return True
            return False
        except Exception as e:
            logger.error(f"Error aborting transaction: {str(e)}")
            return False
            
    def create_layer(self, layer_name, color=None, lineweight=None):
        """Create a new layer in the current drawing"""
        transaction = self.create_transaction()
        if not transaction:
            return False
            
        try:
            layer_table = transaction.GetObject(
                self.database.LayerTableId, 
                OpenMode.ForRead
            )
            
            if layer_table.Has(layer_name):
                logger.info(f"Layer '{layer_name}' already exists")
                return True
                
            layer_table_record = LayerTableRecord()
            layer_table_record.Name = layer_name
            
            # Set layer color if provided
            if color:
                if isinstance(color, int):
                    layer_table_record.Color = Color.FromColorIndex(ColorMethod.ByAci, color)
                elif isinstance(color, str):
                    # Handle named colors
                    pass
                    
            # Set lineweight if provided
            if lineweight:
                layer_table_record.LineWeight = lineweight
                
            layer_table.UpgradeOpen()
            layer_table_id = layer_table.Add(layer_table_record)
            transaction.AddNewlyCreatedDBObject(layer_table_record, True)
            
            self.commit_transaction(transaction)
            logger.info(f"Layer '{layer_name}' created successfully")
            return True
            
        except Exception as e:
            self.abort_transaction(transaction)
            logger.error(f"Error creating layer '{layer_name}': {str(e)}")
            return False
            
    def create_block_reference(self, block_name, insertion_point, layer_name=None):
        """Create a block reference in model space"""
        transaction = self.create_transaction()
        if not transaction:
            return None
            
        try:
            # Get block table
            block_table = transaction.GetObject(
                self.database.BlockTableId, 
                OpenMode.ForRead
            )
            
            if not block_table.Has(block_name):
                logger.error(f"Block '{block_name}' not found")
                self.abort_transaction(transaction)
                return None
                
            # Get model space
            model_space = transaction.GetObject(
                block_table[BlockTableRecord.ModelSpace],
                OpenMode.ForWrite
            )
            
            # Create block reference
            block_ref = BlockReference(insertion_point, block_table[block_name])
            
            # Set layer if provided
            if layer_name:
                block_ref.Layer = layer_name
                
            # Add to model space
            model_space.AppendEntity(block_ref)
            transaction.AddNewlyCreatedDBObject(block_ref, True)
            
            self.commit_transaction(transaction)
            return block_ref
            
        except Exception as e:
            self.abort_transaction(transaction)
            logger.error(f"Error creating block reference: {str(e)}")
            return None
            
    def get_entity_by_handle(self, handle):
        """Get entity by handle string"""
        transaction = self.create_transaction()
        if not transaction:
            return None
            
        try:
            entity_id = self.database.GetObjectId(False, ObjectId(handle), 0)
            if entity_id.IsNull:
                return None
                
            entity = transaction.GetObject(entity_id, OpenMode.ForRead)
            return entity
            
        except Exception as e:
            logger.error(f"Error getting entity by handle {handle}: {str(e)}")
            return None
        finally:
            if transaction:
                transaction.Dispose()
                
    def set_entity_xdata(self, entity, app_name, xdata_dict):
        """Set extended data on entity"""
        try:
            # Register application name if not exists
            self._register_application(app_name)
            
            # Create result buffer for XData
            from Autodesk.AutoCAD.DatabaseServices import ResultBuffer
            from Autodesk.AutoCAD.DatabaseServices import TypedValue
            from System import Int16
            
            rb = ResultBuffer()
            
            # Add application name
            rb.Add(TypedValue(Int16(1001), app_name))
            
            # Add data pairs
            for key, value in xdata_dict.items():
                rb.Add(TypedValue(Int16(1000), str(key)))  # Key as string
                rb.Add(TypedValue(Int16(1000), str(value)))  # Value as string
                
            # Set XData
            entity.XData = rb
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting XData: {str(e)}")
            return False
            
    def get_entity_xdata(self, entity, app_name):
        """Get extended data from entity"""
        try:
            xdata = entity.GetXData(app_name)
            if not xdata:
                return {}
                
            xdata_dict = {}
            for i in range(1, xdata.Length - 1, 2):  # Skip app name and process pairs
                if xdata[i].TypeCode == 1000 and i + 1 < xdata.Length:
                    key = xdata[i].Value
                    value = xdata[i + 1].Value
                    xdata_dict[key] = value
                    
            return xdata_dict
            
        except Exception as e:
            logger.error(f"Error getting XData: {str(e)}")
            return {}
            
    def _register_application(self, app_name):
        """Register application name for XData"""
        try:
            # Check if application is already registered
            registered_apps = self.database.RegAppTableId
            with self.create_transaction() as transaction:
                reg_app_table = transaction.GetObject(
                    self.database.RegAppTableId, 
                    OpenMode.ForRead
                )
                
                if not reg_app_table.Has(app_name):
                    reg_app_table.UpgradeOpen()
                    reg_app_record = RegAppTableRecord()
                    reg_app_record.Name = app_name
                    reg_app_table.Add(reg_app_record)
                    transaction.AddNewlyCreatedDBObject(reg_app_record, True)
                    
        except Exception as e:
            logger.error(f"Error registering application '{app_name}': {str(e)}")
            
    def zoom_extents(self):
        """Zoom to drawing extents"""
        try:
            if self.editor:
                self.editor.ZoomExtents()
                return True
            return False
        except Exception as e:
            logger.error(f"Error zooming to extents: {str(e)}")
            return False
            
    def refresh_view(self):
        """Refresh the AutoCAD view"""
        try:
            if self.application:
                self.application.UpdateScreen()
                return True
            return False
        except Exception as e:
            logger.error(f"Error refreshing view: {str(e)}")
            return False
            
    def get_drawing_units(self):
        """Get current drawing units"""
        try:
            if self.database:
                units = self.database.Insunits
                return self._decode_units(units)
            return "Unknown"
        except Exception as e:
            logger.error(f"Error getting drawing units: {str(e)}")
            return "Unknown"
            
    def _decode_units(self, unit_code):
        """Decode AutoCAD unit codes to human-readable format"""
        unit_map = {
            0: "Unitless",
            1: "Inches",
            2: "Feet",
            3: "Miles",
            4: "Millimeters",
            5: "Centimeters", 
            6: "Meters",
            7: "Kilometers",
            8: "Microinches",
            9: "Mils",
            10: "Yards",
            11: "Angstroms",
            12: "Nanometers",
            13: "Microns",
            14: "Decimeters",
            15: "Decameters",
            16: "Hectometers",
            17: "Gigameters",
            18: "Astronomical Units",
            19: "Light Years",
            20: "Parsecs"
        }
        return unit_map.get(unit_code, "Unknown")