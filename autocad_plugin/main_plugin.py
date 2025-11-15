"""
Main plugin module with tkinter UI and Ribbon
Standalone version for development and testing
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add the plugin directory to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.logger import Logger, logger
from utils.config import Config, config
from services.cache_manager import CacheManager
from services.sync_service import SyncService
from services.license_service import LicenseService
from ui.palette_manager import PaletteManager
from ui.ribbon_ui import RibbonUI

class StructuralPlugin:
    """
    Main plugin class with tkinter UI and ribbon
    """
    
    def __init__(self):
        self.name = "AutoCAD Structural Plugin"
        self.version = "1.0.0"
        self.is_initialized = False
        
        # Core components
        self.cache_manager = None
        self.sync_service = None
        self.license_service = None
        
        # UI Components
        self.root = None
        self.palette_manager = None
        self.ribbon_ui = None
        
        # Content area
        self.content_frame = None
        self.status_bar = None
        
    def initialize(self):
        """Initialize the plugin"""
        try:
            logger.info("Initializing Structural Plugin...")
            
            # Initialize core utilities
            self._initialize_core_utilities()
            
            # Initialize services
            self._initialize_services()
            
            # Initialize UI
            self._initialize_ui()
            
            self.is_initialized = True
            logger.info("Plugin initialized successfully!")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize plugin: {e}")
            return False
    
    def _initialize_core_utilities(self):
        """Initialize core utilities"""
        log_level = config.get('logging.level', 'INFO')
        logger.set_level(log_level)
        
    def _initialize_services(self):
        """Initialize services"""
        self.cache_manager = CacheManager()
        self.sync_service = SyncService()
        self.license_service = LicenseService()
        
    def _initialize_ui(self):
        """Initialize tkinter UI with ribbon"""
        self.root = tk.Tk()
        self.root.title(f"{self.name} v{self.version}")
        self.root.geometry("1000x700")
        
        # Create main layout
        self._create_main_layout()
        
    def _create_main_layout(self):
        """Create the main application layout"""
        # Ribbon at the top
        self.ribbon_ui = RibbonUI(self.root)
        self.ribbon_ui.ribbon_frame.pack(fill='x', padx=2, pady=2)
        
        # Tab selector below ribbon
        tab_selector = self.ribbon_ui.create_tab_selector(self.root)
        tab_selector.pack(fill='x', padx=5, pady=2)
        
        # Content area
        self.content_frame = ttk.Frame(self.root)
        self.content_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create content
        self._create_content()
        
        # Status bar at the bottom
        self._create_status_bar()
        
    def _create_content(self):
        """Create main content area"""
        # Left panel - Properties
        left_panel = ttk.LabelFrame(self.content_frame, text="Properties")
        left_panel.pack(side='left', fill='y', padx=(0, 5))
        
        # Sample properties tree
        props_tree = ttk.Treeview(left_panel, columns=('Value',), show='tree headings')
        props_tree.heading('#0', text='Property')
        props_tree.heading('Value', text='Value')
        
        sample_data = [
            ('General', '', [
                ('Type', 'Column'),
                ('Material', 'Concrete C30'),
                ('Status', 'Designed')
            ]),
            ('Dimensions', '', [
                ('Width', '400 mm'),
                ('Depth', '400 mm'), 
                ('Height', '3000 mm')
            ]),
            ('Reinforcement', '', [
                ('Main Bars', '4T20'),
                ('Ties', 'T10@200'),
                ('Cover', '40 mm')
            ])
        ]
        
        for category, _, items in sample_data:
            cat_id = props_tree.insert('', 'end', text=category, values=('',))
            for prop, value in items:
                props_tree.insert(cat_id, 'end', text=prop, values=(value,))
                
        props_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Right panel - Canvas/Viewport simulation
        right_panel = ttk.LabelFrame(self.content_frame, text="Model View")
        right_panel.pack(side='left', fill='both', expand=True)
        
        # Simulate CAD viewport
        viewport = tk.Canvas(right_panel, bg='white', relief='sunken')
        viewport.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Draw some sample structural elements
        self._draw_sample_elements(viewport)
        
    def _draw_sample_elements(self, canvas):
        """Draw sample structural elements on canvas"""
        # Draw a column
        canvas.create_rectangle(100, 100, 150, 300, fill='lightblue', outline='blue', width=2)
        canvas.create_text(125, 320, text="COLUMN", font=('Arial', 8, 'bold'))
        
        # Draw a beam
        canvas.create_rectangle(50, 100, 350, 120, fill='lightgreen', outline='green', width=2)
        canvas.create_text(200, 130, text="BEAM", font=('Arial', 8, 'bold'))
        
        # Draw a wall
        canvas.create_rectangle(400, 100, 450, 300, fill='lightyellow', outline='orange', width=2)
        canvas.create_text(425, 320, text="WALL", font=('Arial', 8, 'bold'))
        
        # Draw grid lines
        for i in range(0, 600, 50):
            canvas.create_line(i, 0, i, 400, fill='gray90', dash=(2, 2))
            canvas.create_line(0, i, 600, i, fill='gray90', dash=(2, 2))
        
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = ttk.Frame(self.root, relief='sunken')
        self.status_bar.pack(fill='x', side='bottom')
        
        # Left status
        left_status = ttk.Label(self.status_bar, text="Ready")
        left_status.pack(side='left', padx=5)
        
        # Right status
        right_status = ttk.Label(self.status_bar, text="Structural Plugin v1.0.0")
        right_status.pack(side='right', padx=5)
        
    def run(self):
        """Run the plugin"""
        if not self.is_initialized:
            if not self.initialize():
                messagebox.showerror("Error", "Failed to initialize plugin")
                return
        
        logger.info("Starting plugin...")
        print(f"🚀 {self.name} v{self.version} is running!")
        print("💡 Use the ribbon tabs to access different tools")
        
        self.root.mainloop()
        
    def shutdown(self):
        """Shutdown the plugin"""
        try:
            if self.root:
                self.root.quit()
                self.root.destroy()
                
            if self.sync_service:
                self.sync_service.stop()
                
            logger.info("Plugin shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

def main():
    """Main entry point for standalone execution"""
    plugin = StructuralPlugin()
    
    try:
        plugin.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        plugin.shutdown()

if __name__ == "__main__":
    print("AutoCAD Structural Plugin - Standalone Mode with Ribbon UI")
    print("=" * 60)
    main()