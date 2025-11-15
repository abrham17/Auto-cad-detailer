"""
Property palette with tkinter
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

class PropertyPalette(ttk.Frame):
    """Property palette for structural element properties"""
    
    def __init__(self, master=None):
        super().__init__(master)
        self.current_entity = None
        self.properties: Dict[str, Any] = {}
        self._create_widgets()
        
    def _create_widgets(self):
        """Create property palette widgets"""
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        title_label = ttk.Label(
            header_frame, 
            text="Structural Properties",
            font=('Arial', 12, 'bold')
        )
        title_label.pack()
        
        self.selection_label = ttk.Label(
            header_frame,
            text="No selection",
            font=('Arial', 9, 'italic')
        )
        self.selection_label.pack()
        
        # Properties frame
        props_frame = ttk.LabelFrame(self, text="Properties")
        props_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create scrollable frame for properties
        canvas = tk.Canvas(props_frame)
        scrollbar = ttk.Scrollbar(props_frame, orient='vertical', command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons frame
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill='x', padx=10, pady=5)
        
        refresh_btn = ttk.Button(
            buttons_frame, 
            text="Refresh",
            command=self.refresh_properties
        )
        refresh_btn.pack(side='left', padx=5)
        
        save_btn = ttk.Button(
            buttons_frame,
            text="Save", 
            command=self.save_properties
        )
        save_btn.pack(side='left', padx=5)
        
        # Initialize with sample properties
        self._show_sample_properties()
        
    def _show_sample_properties(self):
        """Show sample properties for demonstration"""
        sample_properties = {
            'Handle': '4F2',
            'Layer': 'STRUCTURAL_COLUMNS',
            'Type': 'Column',
            'Width': '400 mm',
            'Depth': '400 mm', 
            'Height': '3000 mm',
            'Material': 'Concrete C30',
            'Reinforcement': '4T20'
        }
        
        self.update_for_entity(sample_properties, "Column [4F2]")
        
    def update_for_entity(self, properties: Dict[str, Any], entity_info: str = ""):
        """Update property grid for specific entity"""
        self.properties = properties
        self.selection_label.config(text=entity_info or "Custom element")
        
        # Clear existing properties
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        # Add properties to grid
        row = 0
        for prop_name, prop_value in properties.items():
            # Property name label
            name_label = ttk.Label(
                self.scrollable_frame,
                text=f"{prop_name}:",
                font=('Arial', 9, 'bold')
            )
            name_label.grid(row=row, column=0, sticky='w', padx=5, pady=2)
            
            # Property value - use entry for editable fields
            value_var = tk.StringVar(value=str(prop_value))
            value_entry = ttk.Entry(
                self.scrollable_frame,
                textvariable=value_var,
                width=20
            )
            value_entry.grid(row=row, column=1, sticky='ew', padx=5, pady=2)
            value_entry.var = value_var
            value_entry.prop_name = prop_name
            
            row += 1
            
        # Configure grid weights
        self.scrollable_frame.columnconfigure(1, weight=1)
        
    def refresh_properties(self):
        """Refresh properties from entity"""
        # In real implementation, this would reload from the entity
        print("Refreshing properties...")
        
    def save_properties(self):
        """Save modified properties"""
        print("Saving properties...")
        
        # Collect modified values
        for child in self.scrollable_frame.winfo_children():
            if isinstance(child, ttk.Entry) and hasattr(child, 'var'):
                prop_name = getattr(child, 'prop_name', '')
                new_value = child.var.get()
                print(f"Property '{prop_name}' changed to: {new_value}")
                
        print("Properties saved successfully!")
        
    def clear_selection(self):
        """Clear current selection"""
        self.properties = {}
        self.selection_label.config(text="No selection")
        
        # Clear property fields
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()