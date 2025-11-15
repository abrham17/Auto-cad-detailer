"""
Additional dialog windows
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from typing import Optional, Dict, Any

class SettingsDialog(simpledialog.Dialog):
    """Dialog for editing column settings"""
    
    def __init__(self, parent, settings: Dict[str, Any]):
        self.settings = settings.copy()
        super().__init__(parent, title="Column Settings")
    
    def body(self, master):
        """Create dialog body"""
        ttk.Label(master, text="Column Drawing Settings").grid(row=0, column=0, columnspan=2, pady=10)
        
        # Beam settings
        ttk.Label(master, text="Beam Depth (mm):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.beam_depth_var = tk.DoubleVar(value=self.settings.get('beam_depth', 500))
        ttk.Entry(master, textvariable=self.beam_depth_var).grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(master, text="Beam Extension (mm):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.beam_extension_var = tk.DoubleVar(value=self.settings.get('beam_extension', 200))
        ttk.Entry(master, textvariable=self.beam_extension_var).grid(row=2, column=1, padx=5, pady=2)
        
        # Concrete cover
        ttk.Label(master, text="Concrete Cover (mm):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.cover_var = tk.DoubleVar(value=self.settings.get('concrete_cover', 25))
        ttk.Entry(master, textvariable=self.cover_var).grid(row=3, column=1, padx=5, pady=2)
        
        # Scale
        ttk.Label(master, text="Drawing Scale:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        self.scale_var = tk.DoubleVar(value=self.settings.get('scale', 50))
        ttk.Entry(master, textvariable=self.scale_var).grid(row=4, column=1, padx=5, pady=2)
        
        return ttk.Entry(master)  # initial focus
    
    def apply(self):
        """Apply settings"""
        try:
            self.settings.update({
                'beam_depth': self.beam_depth_var.get(),
                'beam_extension': self.beam_extension_var.get(),
                'concrete_cover': self.cover_var.get(),
                'scale': self.scale_var.get()
            })
        except tk.TclError:
            messagebox.showerror("Error", "Please enter valid numeric values")

class InsertionPointDialog(simpledialog.Dialog):
    """Dialog for specifying insertion point"""
    
    def __init__(self, parent):
        self.point = (0, 0, 0)
        super().__init__(parent, title="Insertion Point")
    
    def body(self, master):
        """Create dialog body"""
        ttk.Label(master, text="Specify Insertion Point (mm)").grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Label(master, text="X:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.x_var = tk.DoubleVar(value=0)
        ttk.Entry(master, textvariable=self.x_var).grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(master, text="Y:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.y_var = tk.DoubleVar(value=0)
        ttk.Entry(master, textvariable=self.y_var).grid(row=2, column=1, padx=5, pady=2)
        
        ttk.Label(master, text="Z:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.z_var = tk.DoubleVar(value=0)
        ttk.Entry(master, textvariable=self.z_var).grid(row=3, column=1, padx=5, pady=2)
        
        return ttk.Entry(master)  # initial focus
    
    def apply(self):
        """Apply insertion point"""
        try:
            self.point = (
                self.x_var.get(),
                self.y_var.get(),
                self.z_var.get()
            )
        except tk.TclError:
            messagebox.showerror("Error", "Please enter valid numeric values")

class ProgressDialog:
    """Progress dialog for long operations"""
    
    def __init__(self, parent, title="Processing", message="Please wait..."):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("300x100")
        x = parent.winfo_rootx() + (parent.winfo_width() - 300) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 100) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Create content
        ttk.Label(self.dialog, text=message).pack(pady=10)
        self.progress_var = tk.DoubleVar()
        ttk.Progressbar(self.dialog, variable=self.progress_var, mode='indeterminate').pack(fill=tk.X, padx=20, pady=5)
        self.progress_var.set(50)  # Start indeterminate
        
    def update_progress(self, value: int):
        """Update progress value (0-100)"""
        self.progress_var.set(value)
    
    def set_message(self, message: str):
        """Update progress message"""
        for widget in self.dialog.winfo_children():
            if isinstance(widget, ttk.Label):
                widget.config(text=message)
                break
    
    def close(self):
        """Close the dialog"""
        self.dialog.destroy()