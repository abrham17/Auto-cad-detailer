"""
Main application window
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import logging
import os
from typing import Optional, Dict, Any
from pathlib import Path

from column_detailer.autocad_manager import AutoCADManager
from column_detailer.excel_reader import ExcelColumnReader
from column_detailer.drawing_service import ColumnDrawingService
from utils.validation import DataValidator, UnitConverter

class ColumnDetailerApp:
    """Main application window for Column Detailer"""
    
    def __init__(self):
        self.root = None
        self.current_file = None
        self.column_data = None
        self.autocad_manager = AutoCADManager()
        self.drawing_service = None
        self.validator = DataValidator()
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self._initialize_services()
        
    def _initialize_services(self):
        """Initialize AutoCAD and drawing services"""
        try:
            # Try to connect to AutoCAD
            if self.autocad_manager.connect():
                self.drawing_service = ColumnDrawingService(self.autocad_manager)
                self.logger.info("AutoCAD services initialized successfully")
            else:
                self.logger.warning("AutoCAD not available - running in preview mode")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
    
    def run(self):
        """Start the main application"""
        self._create_main_window()
        self.root.mainloop()
    
    def _create_main_window(self):
        """Create the main application window"""
        self.root = tk.Tk()
        self.root.title("Column Detailer for AutoCAD")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Configure style
        self._configure_styles()
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Create UI sections
        self._create_header(main_frame)
        self._create_file_section(main_frame)
        self._create_preview_section(main_frame)
        self._create_control_section(main_frame)
        self._create_status_section(main_frame)
        
        # Update status
        self._update_status("Ready to load Excel file")
    
    def _configure_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        
        # Configure button styles
        style.configure('Action.TButton', font=('Arial', 10, 'bold'))
        style.configure('Success.TButton', background='#4CAF50', foreground='white')
        style.configure('Warning.TButton', background='#FF9800', foreground='white')
        
        # Configure label styles
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
    
    def _create_header(self, parent):
        """Create application header"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Title
        title_label = ttk.Label(header_frame, text="Column Detailer for AutoCAD", 
                               style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        # Version info
        version_label = ttk.Label(header_frame, text="v1.0.0", style='Heading.TLabel')
        version_label.pack(side=tk.RIGHT)
    
    def _create_file_section(self, parent):
        """Create file selection section"""
        file_frame = ttk.LabelFrame(parent, text="Excel File", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # File selection
        ttk.Label(file_frame, text="Select Excel File:").grid(row=0, column=0, sticky=tk.W)
        
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, state='readonly')
        file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        browse_button = ttk.Button(file_frame, text="Browse", command=self._browse_file)
        browse_button.grid(row=0, column=2, padx=(0, 5))
        
        load_button = ttk.Button(file_frame, text="Load Data", 
                                command=self._load_excel_data, style='Action.TButton')
        load_button.grid(row=0, column=3)
        
        # File info
        self.file_info_var = tk.StringVar(value="No file loaded")
        file_info_label = ttk.Label(file_frame, textvariable=self.file_info_var)
        file_info_label.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
    
    def _create_preview_section(self, parent):
        """Create data preview section"""
        preview_frame = ttk.LabelFrame(parent, text="Data Preview", padding="10")
        preview_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        # Create notebook for multiple columns
        self.notebook = ttk.Notebook(preview_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Default tab for instructions
        default_tab = ttk.Frame(self.notebook)
        self.notebook.add(default_tab, text="Instructions")
        
        instruction_text = """
        Column Detailer for AutoCAD
        
        Instructions:
        1. Click 'Browse' to select an Excel file with column data
        2. Click 'Load Data' to read and validate the data
        3. Review the data in the preview tabs
        4. Click 'Draw Elevations' to create column elevations in AutoCAD
        5. Click 'Draw Sections' to create column sections
        
        Excel File Requirements:
        - Must contain a 'Settings' worksheet with drawing parameters
        - Must contain one or more 'ColumnData' worksheets with floor data
        - See documentation for detailed format requirements
        """
        
        instruction_label = ttk.Label(default_tab, text=instruction_text, justify=tk.LEFT)
        instruction_label.pack(padx=10, pady=10, anchor=tk.W)
    
    def _create_control_section(self, parent):
        """Create control buttons section"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        # Drawing buttons
        draw_elevation_btn = ttk.Button(control_frame, text="Draw Elevations", 
                                       command=self._draw_elevations, style='Action.TButton')
        draw_elevation_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        draw_sections_btn = ttk.Button(control_frame, text="Draw Sections", 
                                      command=self._draw_sections, style='Action.TButton')
        draw_sections_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Utility buttons
        validate_btn = ttk.Button(control_frame, text="Validate Data", 
                                 command=self._validate_data)
        validate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = ttk.Button(control_frame, text="Clear Drawing", 
                              command=self._clear_drawing, style='Warning.TButton')
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        export_btn = ttk.Button(control_frame, text="Export Report", 
                               command=self._export_report)
        export_btn.pack(side=tk.LEFT)
    
    def _create_status_section(self, parent):
        """Create status section"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E))
        status_frame.columnconfigure(0, weight=1)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, mode='determinate')
        progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # AutoCAD status
        autocad_status = "Connected" if self.autocad_manager._connected else "Not Available"
        autocad_label = ttk.Label(status_frame, text=f"AutoCAD: {autocad_status}")
        autocad_label.grid(row=0, column=1, sticky=tk.E)
    
    def _browse_file(self):
        """Browse for Excel file"""
        file_path = filedialog.askopenfilename(
            title="Select Excel File with Column Data",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("Excel files", "*.xls"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.file_path_var.set(file_path)
            self.current_file = file_path
            self._update_file_info(f"Selected: {os.path.basename(file_path)}")
    
    def _load_excel_data(self):
        """Load and validate Excel data"""
        if not self.current_file or not os.path.exists(self.current_file):
            messagebox.showerror("Error", "Please select a valid Excel file")
            return
        
        try:
            self._update_status("Loading Excel file...")
            self.progress_var.set(10)
            
            # Read Excel file
            reader = ExcelColumnReader()
            self.column_data = reader.read_column_file(self.current_file)
            
            self.progress_var.set(50)
            
            # Validate data
            validation_results = {}
            for column_name, data in self.column_data.items():
                result = self.validator.validate_column_data({
                    'settings': data.settings,
                    'floors': data.floors
                })
                validation_results[column_name] = result
            
            self.progress_var.set(80)
            
            # Update UI with data
            self._update_preview_tabs(validation_results)
            
            self.progress_var.set(100)
            self._update_status("Data loaded successfully")
            self._update_file_info(f"Loaded {len(self.column_data)} columns")
            
            messagebox.showinfo("Success", f"Successfully loaded {len(self.column_data)} columns")
            
        except Exception as e:
            self._update_status("Error loading data")
            self.progress_var.set(0)
            messagebox.showerror("Error", f"Failed to load Excel file: {e}")
    
    def _update_preview_tabs(self, validation_results):
        """Update preview tabs with loaded data"""
        # Clear existing tabs (except instructions)
        for tab_id in self.notebook.tabs()[1:]:
            self.notebook.forget(tab_id)
        
        # Create tabs for each column
        for column_name, column_data in self.column_data.items():
            tab_frame = ttk.Frame(self.notebook)
            self.notebook.add(tab_frame, text=column_name)
            
            # Create treeview for floor data
            tree_frame = ttk.Frame(tab_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Create scrollable treeview
            tree_scroll = ttk.Scrollbar(tree_frame)
            tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            
            columns = ('Floor', 'Height', 'Length', 'Width', 'Rebars', 'Rebar Ø', 'Stirrup Ø')
            tree = ttk.Treeview(tree_frame, columns=columns, show='headings', 
                               yscrollcommand=tree_scroll.set)
            
            # Configure columns
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=80)
            
            # Add data
            for i, floor in enumerate(column_data.floors):
                tree.insert('', 'end', values=(
                    floor.floor_name,
                    f"{floor.total_height:.0f}",
                    f"{floor.column_length:.0f}",
                    f"{floor.column_width:.0f}" if floor.column_width > 0 else "Circular",
                    floor.rebar_amount,
                    f"{floor.rebar_diameter:.1f}",
                    f"{floor.stirrup_diameter:.1f}"
                ))
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            tree_scroll.config(command=tree.yview)
            
            # Add validation results
            validation = validation_results.get(column_name, {})
            if validation.get('errors'):
                error_text = "\n".join(validation['errors'])
                error_label = ttk.Label(tab_frame, text=f"Errors: {error_text}", 
                                      foreground='red')
                error_label.pack(anchor=tk.W, padx=5, pady=2)
            
            if validation.get('warnings'):
                warning_text = "\n".join(validation['warnings'])
                warning_label = ttk.Label(tab_frame, text=f"Warnings: {warning_text}", 
                                        foreground='orange')
                warning_label.pack(anchor=tk.W, padx=5, pady=2)
    
    def _draw_elevations(self):
        """Draw column elevations in AutoCAD"""
        if not self.column_data:
            messagebox.showwarning("Warning", "Please load column data first")
            return
        
        if not self.autocad_manager._connected:
            messagebox.showerror("Error", "AutoCAD is not available")
            return
        
        try:
            self._update_status("Drawing column elevations...")
            self.progress_var.set(0)
            
            insertion_point = (0, 0, 0)  # Starting point
            spacing = 5000  # mm between columns
            
            total_columns = len(self.column_data)
            current_column = 0
            
            for column_name, column_data in self.column_data.items():
                current_column += 1
                progress = (current_column / total_columns) * 100
                self.progress_var.set(progress)
                
                self._update_status(f"Drawing {column_name}...")
                
                # Draw column elevation
                success = self.drawing_service.draw_column_elevation(
                    column_data, insertion_point, current_column
                )
                
                if success:
                    # Move to next column position
                    max_length = max(floor.column_length for floor in column_data.floors)
                    insertion_point = (
                        insertion_point[0] + max_length + spacing,
                        insertion_point[1],
                        insertion_point[2]
                    )
                else:
                    self.logger.error(f"Failed to draw {column_name}")
            
            self.progress_var.set(100)
            self._update_status("Column elevations drawn successfully")
            messagebox.showinfo("Success", "Column elevations drawn successfully in AutoCAD")
            
        except Exception as e:
            self._update_status("Error drawing elevations")
            self.progress_var.set(0)
            messagebox.showerror("Error", f"Failed to draw column elevations: {e}")
    
    def _draw_sections(self):
        """Draw column sections in AutoCAD"""
        if not self.column_data:
            messagebox.showwarning("Warning", "Please load column data first")
            return
        
        if not self.autocad_manager._connected:
            messagebox.showerror("Error", "AutoCAD is not available")
            return
        
        try:
            self._update_status("Drawing column sections...")
            self.progress_var.set(0)
            
            insertion_point = (0, -10000, 0)  # Below elevations
            
            total_sections = sum(len(col_data.floors) for col_data in self.column_data.values())
            current_section = 0
            
            for column_name, column_data in self.column_data.items():
                for floor in column_data.floors:
                    current_section += 1
                    progress = (current_section / total_sections) * 100
                    self.progress_var.set(progress)
                    
                    # Draw section
                    success = self.drawing_service.draw_column_sections(
                        column_data, insertion_point
                    )
                    
                    if not success:
                        self.logger.warning(f"Failed to draw section for {column_name}")
            
            self.progress_var.set(100)
            self._update_status("Column sections drawn successfully")
            messagebox.showinfo("Success", "Column sections drawn successfully in AutoCAD")
            
        except Exception as e:
            self._update_status("Error drawing sections")
            self.progress_var.set(0)
            messagebox.showerror("Error", f"Failed to draw column sections: {e}")
    
    def _validate_data(self):
        """Validate loaded data"""
        if not self.column_data:
            messagebox.showwarning("Warning", "Please load column data first")
            return
        
        try:
            all_valid = True
            error_count = 0
            warning_count = 0
            
            for column_name, column_data in self.column_data.items():
                result = self.validator.validate_column_data({
                    'settings': column_data.settings,
                    'floors': column_data.floors
                })
                
                if not result['is_valid']:
                    all_valid = False
                    error_count += len(result['errors'])
                
                warning_count += len(result['warnings'])
            
            if all_valid and warning_count == 0:
                messagebox.showinfo("Validation", "All data is valid!")
            elif all_valid:
                messagebox.showwarning("Validation", 
                                    f"Data is valid with {warning_count} warning(s)")
            else:
                messagebox.showerror("Validation", 
                                   f"Data has {error_count} error(s) and {warning_count} warning(s)")
                
        except Exception as e:
            messagebox.showerror("Error", f"Validation failed: {e}")
    
    def _clear_drawing(self):
        """Clear current drawing"""
        if not self.autocad_manager._connected:
            messagebox.showerror("Error", "AutoCAD is not available")
            return
        
        try:
            # This would typically clear specific layers or objects
            # For now, just show a message
            messagebox.showinfo("Info", "Clear drawing functionality would be implemented here")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear drawing: {e}")
    
    def _export_report(self):
        """Export data report"""
        if not self.column_data:
            messagebox.showwarning("Warning", "Please load column data first")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export Report",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if file_path:
                self._generate_report(file_path)
                messagebox.showinfo("Success", f"Report exported to {file_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export report: {e}")
    
    def _generate_report(self, file_path: str):
        """Generate data report"""
        with open(file_path, 'w') as f:
            f.write("COLUMN DETAILER REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            for column_name, column_data in self.column_data.items():
                f.write(f"COLUMN: {column_name}\n")
                f.write("-" * 30 + "\n")
                
                # Column summary
                total_height = sum(floor.total_height for floor in column_data.floors)
                f.write(f"Total Height: {total_height:.0f} mm\n")
                f.write(f"Number of Floors: {len(column_data.floors)}\n\n")
                
                # Floor details
                f.write("FLOOR DETAILS:\n")
                f.write("Floor\tHeight\tLength\tWidth\tRebars\n")
                
                for floor in column_data.floors:
                    width_str = f"{floor.column_width:.0f}" if floor.column_width > 0 else "Circular"
                    f.write(f"{floor.floor_name}\t{floor.total_height:.0f}\t"
                           f"{floor.column_length:.0f}\t{width_str}\t{floor.rebar_amount}\n")
                
                f.write("\n")
    
    def _update_status(self, message: str):
        """Update status message"""
        self.status_var.set(message)
        self.logger.info(message)
        self.root.update_idletasks()
    
    def _update_file_info(self, message: str):
        """Update file information"""
        self.file_info_var.set(message)