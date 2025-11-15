"""
Palette management with tkinter
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
from typing import Dict, Optional

from utils.logger import logger
from utils.config import Config

class PaletteManager:
    """Manages tkinter windows for the structural plugin"""
    
    def __init__(self, master=None):
        self.master = master or tk.Tk()
        self.palettes: Dict[str, tk.Toplevel] = {}
        self._setup_main_window()
        
    def _setup_main_window(self):
        """Setup the main application window"""
        self.master.title("AutoCAD Structural Plugin")
        self.master.geometry("400x600")
        self.master.configure(bg='white')
        
        # Create menu bar
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.master.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Properties", command=lambda: self.show_palette('properties'))
        view_menu.add_command(label="Tools", command=lambda: self.show_palette('tools'))
        view_menu.add_command(label="Layers", command=lambda: self.show_palette('layers'))
        
        # Create main content
        self._create_main_content()
        
    def _create_main_content(self):
        """Create main window content"""
        # Header
        header_frame = ttk.Frame(self.master)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        title_label = ttk.Label(
            header_frame, 
            text="Structural Plugin", 
            font=('Arial', 16, 'bold')
        )
        title_label.pack()
        
        # Quick actions frame
        actions_frame = ttk.LabelFrame(self.master, text="Quick Actions")
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        # Action buttons
        actions = [
            ("📐 Create Column", self._create_column),
            ("🧱 Create Wall", self._create_wall),
            ("🏗️ Create Beam", self._create_beam),
            ("🔲 Create Slab", self._create_slab),
            ("🏠 Create Foundation", self._create_foundation)
        ]
        
        for text, command in actions:
            btn = ttk.Button(actions_frame, text=text, command=command)
            btn.pack(fill='x', padx=5, pady=2)
        
        # Status frame
        status_frame = ttk.LabelFrame(self.master, text="Status")
        status_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.status_text = tk.Text(status_frame, height=10, width=50)
        scrollbar = ttk.Scrollbar(status_frame, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self._log_status("Plugin initialized successfully")
        
    def _log_status(self, message: str):
        """Add message to status window"""
        self.status_text.insert('end', f"{message}\n")
        self.status_text.see('end')
        
    def create_properties_palette(self):
        """Create properties palette"""
        palette = tk.Toplevel(self.master)
        palette.title("Structural Properties")
        palette.geometry("300x400")
        palette.transient(self.master)
        
        # Create property palette content
        from .property_palette import PropertyPalette
        property_ui = PropertyPalette(palette)
        property_ui.pack(fill='both', expand=True)
        
        self.palettes['properties'] = palette
        return True
        
    def create_tool_palette(self):
        """Create tool palette"""
        palette = tk.Toplevel(self.master)
        palette.title("Structural Tools")
        palette.geometry("250x300")
        palette.transient(self.master)
        
        # Tools content
        tools_frame = ttk.Frame(palette)
        tools_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        tools = [
            ("Column Tool", "column"),
            ("Wall Tool", "wall"),
            ("Beam Tool", "beam"), 
            ("Slab Tool", "slab"),
            ("Foundation Tool", "foundation"),
            ("Modify Tool", "modify"),
            ("Delete Tool", "delete")
        ]
        
        for tool_name, tool_id in tools:
            btn = ttk.Button(
                tools_frame, 
                text=tool_name,
                command=lambda tid=tool_id: self._execute_tool(tid)
            )
            btn.pack(fill='x', pady=2)
            
        self.palettes['tools'] = palette
        return True
        
    def create_layer_manager_palette(self):
        """Create layer management palette"""
        palette = tk.Toplevel(self.master)
        palette.title("Structural Layers")
        palette.geometry("350x200")
        palette.transient(self.master)
        
        # Layers content
        layers_frame = ttk.Frame(palette)
        layers_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Layer list
        layer_tree = ttk.Treeview(layers_frame, columns=('Count', 'Color'), show='headings')
        layer_tree.heading('#0', text='Layer')
        layer_tree.heading('Count', text='Count')
        layer_tree.heading('Color', text='Color')
        
        # Sample layers
        layers = [
            ('STRUCTURAL_COLUMNS', '0', 'Red'),
            ('STRUCTURAL_WALLS', '0', 'Yellow'),
            ('STRUCTURAL_BEAMS', '0', 'Green'),
            ('STRUCTURAL_SLABS', '0', 'Cyan'),
            ('STRUCTURAL_FOUNDATIONS', '0', 'Blue')
        ]
        
        for layer, count, color in layers:
            layer_tree.insert('', 'end', text=layer, values=(count, color))
            
        layer_tree.pack(fill='both', expand=True)
        
        # Create layers button
        create_btn = ttk.Button(
            layers_frame, 
            text="Create All Layers",
            command=self._create_structural_layers
        )
        create_btn.pack(fill='x', pady=5)
        
        self.palettes['layers'] = palette
        return True
        
    def show_palette(self, name: str):
        """Show a specific palette"""
        if name in self.palettes:
            palette = self.palettes[name]
            palette.deiconify()  # Show window
            palette.lift()       # Bring to front
            palette.focus_force() # Focus
            return True
        
        # Create palette if it doesn't exist
        create_methods = {
            'properties': self.create_properties_palette,
            'tools': self.create_tool_palette,
            'layers': self.create_layer_manager_palette
        }
        
        if name in create_methods:
            if create_methods[name]():
                return self.show_palette(name)
                
        return False
        
    def hide_palette(self, name: str):
        """Hide a specific palette"""
        if name in self.palettes:
            self.palettes[name].withdraw()
            return True
        return False
        
    def toggle_palette_visibility(self):
        """Toggle visibility of all palettes"""
        any_visible = any(palette.winfo_viewable() for palette in self.palettes.values())
        
        for palette in self.palettes.values():
            if any_visible:
                palette.withdraw()
            else:
                palette.deiconify()
                
        return not any_visible
        
    def _execute_tool(self, tool_id: str):
        """Execute a tool command"""
        self._log_status(f"Executing tool: {tool_id}")
        
        # Simulate tool execution
        tool_actions = {
            'column': "Creating structural column...",
            'wall': "Creating structural wall...", 
            'beam': "Creating structural beam...",
            'slab': "Creating structural slab...",
            'foundation': "Creating foundation...",
            'modify': "Modify tool activated - select an element",
            'delete': "Delete tool activated - select an element to delete"
        }
        
        if tool_id in tool_actions:
            messagebox.showinfo("Tool Activated", tool_actions[tool_id])
            self._log_status(tool_actions[tool_id])
            
    def _create_structural_layers(self):
        """Create structural layers"""
        self._log_status("Creating structural layers...")
        messagebox.showinfo("Layers Created", "Structural layers created successfully!")
        self._log_status("✓ Structural layers created")
        
    def _create_column(self):
        self._log_status("Creating column...")
        messagebox.showinfo("Column", "Column creation tool activated")
        
    def _create_wall(self):
        self._log_status("Creating wall...")
        messagebox.showinfo("Wall", "Wall creation tool activated")
        
    def _create_beam(self):
        self._log_status("Creating beam...") 
        messagebox.showinfo("Beam", "Beam creation tool activated")
        
    def _create_slab(self):
        self._log_status("Creating slab...")
        messagebox.showinfo("Slab", "Slab creation tool activated")
        
    def _create_foundation(self):
        self._log_status("Creating foundation...")
        messagebox.showinfo("Foundation", "Foundation creation tool activated")
        
    def run(self):
        """Start the tkinter main loop"""
        self.master.mainloop()
        
    def destroy(self):
        """Clean up all windows"""
        for palette in self.palettes.values():
            palette.destroy()
        self.master.destroy()