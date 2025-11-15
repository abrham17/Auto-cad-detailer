"""
Column Detailer for AutoCAD - Main Entry Point
"""

import sys
import os
import logging
from tkinter import messagebox

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import ColumnDetailerApp
from utils.validation import LicenseManager

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('column_detailer.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main application entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Column Detailer for AutoCAD")
        
        # Check license
        license_manager = LicenseManager()
        if not license_manager.is_licensed():
            messagebox.showerror(
                "License Error", 
                "This machine is not authorized to run Column Detailer.\nPlease contact the administrator."
            )
            sys.exit(1)
        
        # Start the application
        app = ColumnDetailerApp()
        app.run()
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        messagebox.showerror("Startup Error", f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()