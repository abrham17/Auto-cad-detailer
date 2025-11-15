"""
Ribbon UI with tkinter that mimics AutoCAD's ribbon interface
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Callable, Optional

class RibbonUI:
    """Ribbon interface for structural plugin"""
    
    def __init__(self, master=None):
        self.master = master
        self.ribbon_frame = None
        self.tabs: Dict[str, ttk.Frame] = {}
        self.current_tab = None
        
        self._create_ribbon()
        
    def _create_ribbon(self):
        """Create the main ribbon interface"""
        # Main ribbon container
        self.ribbon_frame = ttk.Frame(self.master, relief='raised', borderwidth=1)
        self.ribbon_frame.pack(fill='x', padx=2, pady=2)
        
        # Create tabs
        self._create_home_tab()
        self._create_analyze_tab()
        self._create_modify_tab()
        self._create_tools_tab()
        
        # Show home tab by default
        self.show_tab('home')
        
    def _create_home_tab(self):
        """Create Home tab with structural modeling tools"""
        home_tab = ttk.Frame(self.ribbon_frame)
        self.tabs['home'] = home_tab
        
        # Structural Panel
        structural_panel = self._create_panel(home_tab, "Structural", 0)
        
        # Column tools
        col_frame = ttk.LabelFrame(structural_panel, text="Columns")
        col_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Button(col_frame, text="Create Column", 
                  command=lambda: self._execute_command('CREATE_COLUMN'),
                  width=12).pack(padx=2, pady=2)
        
        ttk.Button(col_frame, text="Column Grid", 
                  command=lambda: self._execute_command('COLUMN_GRID'),
                  width=12).pack(padx=2, pady=2)
        
        # Wall tools
        wall_frame = ttk.LabelFrame(structural_panel, text="Walls")
        wall_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Button(wall_frame, text="Create Wall", 
                  command=lambda: self._execute_command('CREATE_WALL'),
                  width=12).pack(padx=2, pady=2)
        
        ttk.Button(wall_frame, text="Wall Opening", 
                  command=lambda: self._execute_command('WALL_OPENING'),
                  width=12).pack(padx=2, pady=2)
        
        # Beam tools
        beam_frame = ttk.LabelFrame(structural_panel, text="Beams")
        beam_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Button(beam_frame, text="Create Beam", 
                  command=lambda: self._execute_command('CREATE_BEAM'),
                  width=12).pack(padx=2, pady=2)
        
        ttk.Button(beam_frame, text="Beam System", 
                  command=lambda: self._execute_command('BEAM_SYSTEM'),
                  width=12).pack(padx=2, pady=2)
        
        # Slab & Foundation tools
        slab_frame = ttk.LabelFrame(structural_panel, text="Slabs & Foundations")
        slab_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Button(slab_frame, text="Create Slab", 
                  command=lambda: self._execute_command('CREATE_SLAB'),
                  width=12).pack(side='left', padx=2, pady=2)
        
        ttk.Button(slab_frame, text="Foundation", 
                  command=lambda: self._execute_command('CREATE_FOUNDATION'),
                  width=12).pack(side='left', padx=2, pady=2)
        
        # Properties Panel
        props_panel = self._create_panel(home_tab, "Properties", 1)
        
        ttk.Button(props_panel, text="Properties", 
                  command=lambda: self._execute_command('PROPERTIES'),
                  width=15).pack(padx=5, pady=5)
        
        ttk.Button(props_panel, text="Quick Properties", 
                  command=lambda: self._execute_command('QUICK_PROPERTIES'),
                  width=15).pack(padx=5, pady=5)
        
        # Layers Panel
        layers_panel = self._create_panel(home_tab, "Layers", 2)
        
        ttk.Button(layers_panel, text="Layer Manager", 
                  command=lambda: self._execute_command('LAYER_MANAGER'),
                  width=15).pack(padx=5, pady=5)
        
        ttk.Button(layers_panel, text="Create Layers", 
                  command=lambda: self._execute_command('CREATE_LAYERS'),
                  width=15).pack(padx=5, pady=5)
        
    def _create_analyze_tab(self):
        """Create Analyze tab with analysis tools"""
        analyze_tab = ttk.Frame(self.ribbon_frame)
        self.tabs['analyze'] = analyze_tab
        
        # Analysis Panel
        analysis_panel = self._create_panel(analyze_tab, "Analysis", 0)
        
        ttk.Button(analysis_panel, text="Run Analysis", 
                  command=lambda: self._execute_command('RUN_ANALYSIS'),
                  width=15).pack(padx=5, pady=5)
        
        ttk.Button(analysis_panel, text="Load Cases", 
                  command=lambda: self._execute_command('LOAD_CASES'),
                  width=15).pack(padx=5, pady=5)
        
        ttk.Button(analysis_panel, text="Results", 
                  command=lambda: self._execute_command('SHOW_RESULTS'),
                  width=15).pack(padx=5, pady=5)
        
        # Report Panel
        report_panel = self._create_panel(analyze_tab, "Reports", 1)
        
        ttk.Button(report_panel, text="Generate Report", 
                  command=lambda: self._execute_command('GENERATE_REPORT'),
                  width=15).pack(padx=5, pady=5)
        
        ttk.Button(report_panel, text="Export Data", 
                  command=lambda: self._execute_command('EXPORT_DATA'),
                  width=15).pack(padx=5, pady=5)
        
    def _create_modify_tab(self):
        """Create Modify tab with editing tools"""
        modify_tab = ttk.Frame(self.ribbon_frame)
        self.tabs['modify'] = modify_tab
        
        # Modify Panel
        modify_panel = self._create_panel(modify_tab, "Modify", 0)
        
        ttk.Button(modify_panel, text="Move", 
                  command=lambda: self._execute_command('MOVE'),
                  width=12).pack(padx=2, pady=2)
        
        ttk.Button(modify_panel, text="Rotate", 
                  command=lambda: self._execute_command('ROTATE'),
                  width=12).pack(padx=2, pady=2)
        
        ttk.Button(modify_panel, text="Copy", 
                  command=lambda: self._execute_command('COPY'),
                  width=12).pack(padx=2, pady=2)
        
        ttk.Button(modify_panel, text="Mirror", 
                  command=lambda: self._execute_command('MIRROR'),
                  width=12).pack(padx=2, pady=2)
        
        ttk.Button(modify_panel, text="Array", 
                  command=lambda: self._execute_command('ARRAY'),
                  width=12).pack(padx=2, pady=2)
        
        # Edit Panel
        edit_panel = self._create_panel(modify_tab, "Edit", 1)
        
        ttk.Button(edit_panel, text="Properties", 
                  command=lambda: self._execute_command('PROPERTIES'),
                  width=15).pack(padx=5, pady=5)
        
        ttk.Button(edit_panel, text="Match Properties", 
                  command=lambda: self._execute_command('MATCH_PROPERTIES'),
                  width=15).pack(padx=5, pady=5)
        
        ttk.Button(edit_panel, text="Delete", 
                  command=lambda: self._execute_command('DELETE'),
                  width=15).pack(padx=5, pady=5)
        
    def _create_tools_tab(self):
        """Create Tools tab with utilities"""
        tools_tab = ttk.Frame(self.ribbon_frame)
        self.tabs['tools'] = tools_tab
        
        # Utilities Panel
        utils_panel = self._create_panel(tools_tab, "Utilities", 0)
        
        ttk.Button(utils_panel, text="Settings", 
                  command=lambda: self._execute_command('SETTINGS'),
                  width=15).pack(padx=5, pady=5)
        
        ttk.Button(utils_panel, text="Sync Now", 
                  command=lambda: self._execute_command('SYNC_NOW'),
                  width=15).pack(padx=5, pady=5)
        
        ttk.Button(utils_panel, text="Backup", 
                  command=lambda: self._execute_command('BACKUP'),
                  width=15).pack(padx=5, pady=5)
        
        # Help Panel
        help_panel = self._create_panel(tools_tab, "Help", 1)
        
        ttk.Button(help_panel, text="Help", 
                  command=lambda: self._execute_command('HELP'),
                  width=15).pack(padx=5, pady=5)
        
        ttk.Button(help_panel, text="About", 
                  command=lambda: self._execute_command('ABOUT'),
                  width=15).pack(padx=5, pady=5)
        
    def _create_panel(self, parent, title, column):
        """Create a ribbon panel"""
        panel = ttk.LabelFrame(parent, text=title)
        panel.grid(row=0, column=column, padx=5, pady=5, sticky='nsew')
        return panel
        
    def show_tab(self, tab_name):
        """Show a specific ribbon tab"""
        # Hide all tabs first
        for tab in self.tabs.values():
            tab.pack_forget()
            
        # Show requested tab
        if tab_name in self.tabs:
            self.tabs[tab_name].pack(fill='x', padx=2, pady=2)
            self.current_tab = tab_name
            return True
        return False
        
    def _execute_command(self, command):
        """Execute a ribbon command"""
        from utils.logger import logger
        
        command_actions = {
            'CREATE_COLUMN': "Creating structural column...",
            'CREATE_WALL': "Creating structural wall...",
            'CREATE_BEAM': "Creating structural beam...",
            'CREATE_SLAB': "Creating structural slab...",
            'CREATE_FOUNDATION': "Creating foundation...",
            'PROPERTIES': "Opening properties palette...",
            'LAYER_MANAGER': "Opening layer manager...",
            'CREATE_LAYERS': "Creating structural layers...",
            'RUN_ANALYSIS': "Running structural analysis...",
            'EXPORT_DATA': "Exporting structural data...",
            'MOVE': "Move tool activated",
            'ROTATE': "Rotate tool activated", 
            'COPY': "Copy tool activated",
            'DELETE': "Delete tool activated",
            'SETTINGS': "Opening settings...",
            'SYNC_NOW': "Syncing data...",
            'HELP': "Opening help...",
        }
        
        action = command_actions.get(command, f"Command: {command}")
        logger.info(f"Ribbon command: {command}")
        print(f"🔧 {action}")
        
        # You can add specific command handlers here
        self._handle_ribbon_command(command)
        
    def _handle_ribbon_command(self, command):
        """Handle specific ribbon commands"""
        # Add specific command handling logic here
        # For now, just print the command
        pass
        
    def create_tab_selector(self, parent):
        """Create tab selector buttons"""
        tab_frame = ttk.Frame(parent)
        tab_frame.pack(fill='x', padx=5, pady=2)
        
        tabs = [
            ("🏠 Home", 'home'),
            ("📊 Analyze", 'analyze'), 
            ("✏️ Modify", 'modify'),
            ("🛠️ Tools", 'tools')
        ]
        
        for text, tab_id in tabs:
            btn = ttk.Button(
                tab_frame, 
                text=text,
                command=lambda tid=tab_id: self.show_tab(tid)
            )
            btn.pack(side='left', padx=2)
            
        return tab_frame