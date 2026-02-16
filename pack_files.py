import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import re
import json
import threading

CONFIG_FILE = "exporter_config_v4.json"
PRESETS_FOLDER = "exporter_presets"

DEFAULT_IGNORES = [
    ".git", "node_modules", "dist", "build", "target", 
    ".vscode", ".idea", "coverage", "__pycache__", 
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", 
    ".DS_Store", ".env", ".env.local", "bin", "obj", 
    ".next", ".nuxt"
]

DEFAULT_EXT_CONFIG = {
    ".css": False, ".js": False, ".ts": False, ".jsx": False, ".tsx": False, 
    ".html": False, ".json": False, ".py": False, ".md": False,
    ".go": True, ".rs": True, ".vue": True, ".cpp": True, ".c": True, 
    ".cs": True, ".yml": True, ".yaml": True, ".bat": True, ".sh": True, 
    ".java": True, ".proto": True, ".gitignore": True, ".gitmodules": True,
    "Dockerfile": True, "Makefile": True
}

class UltimateExporter:
    def __init__(self, root):
        self.root = root
        self.root.title("ULTIMATE CONTEXT EXPORTER v4")
        self.root.geometry("1100x850")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        self.root.configure(bg="#1e1e1e")

        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.export_path = os.path.join(self.base_path, "ai_context_export")
        self.presets_path = os.path.join(self.base_path, PRESETS_FOLDER)
        
        if not os.path.exists(self.presets_path):
            os.makedirs(self.presets_path)
        
        self.tree_nodes = {}
        self.node_states = {} 
        
        # Load Config First
        self.config = self.load_config()
        
        # Restore Data
        self.apply_config_data(self.config)
        
        self.setup_ui()
        self.refresh_full_tree()
        self.refresh_presets_list() # Init presets dropdown
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def on_close(self):
        self.save_config()
        self.root.destroy()

    def configure_styles(self):
        bg_dark = "#1e1e1e"
        fg_light = "#e0e0e0"
        accent = "#06b6d4"
        accent_hover = "#0891b2"
        panel_bg = "#2d2d2d"

        self.style.configure("TFrame", background=bg_dark)
        self.style.configure("TLabel", background=bg_dark, foreground=fg_light, font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground=accent)
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 11, "bold"), foreground="#a5f3fc")
        
        self.style.configure("TButton", font=("Segoe UI", 9, "bold"), background=panel_bg, foreground="white", borderwidth=1)
        self.style.map("TButton", background=[("active", accent), ("pressed", accent_hover)])
        
        self.style.configure("Accent.TButton", background=accent, foreground="white")
        self.style.map("Accent.TButton", background=[("active", accent_hover)])
        
        self.style.configure("TCheckbutton", background=bg_dark, foreground=fg_light, font=("Segoe UI", 10))
        self.style.map("TCheckbutton", background=[("active", bg_dark)])
        
        self.style.configure("TNotebook", background=bg_dark, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=panel_bg, foreground="lightgray", padding=[12, 8])
        self.style.map("TNotebook.Tab", background=[("selected", accent)], foreground=[("selected", "white")])

        self.style.configure("Treeview", background="#252526", foreground="white", fieldbackground="#252526", rowheight=25)
        self.style.map("Treeview", background=[("selected", accent)])

    def apply_config_data(self, d):
        """Helper to apply a config dictionary to internal state"""
        self.custom_roots = d.get("custom_roots", [])
        self.blocked_paths = set(d.get("blocked_paths", []))
        self.forced_includes = d.get("forced_includes", [])
        self.forced_excludes = d.get("forced_excludes", [])
        self.global_ext_config = d.get("global_ext_config", DEFAULT_EXT_CONFIG.copy())
        self.folder_configs = d.get("folder_configs", {})
        self.saved_node_states = d.get("tree_selection_state", {})
        
        # Settings Variables (create if not exist, else update)
        if not hasattr(self, 'conf_merge'): self.conf_merge = tk.BooleanVar()
        self.conf_merge.set(d.get("merge_mode", False))
        
        if not hasattr(self, 'conf_flatten'): self.conf_flatten = tk.BooleanVar()
        self.conf_flatten.set(d.get("flatten_paths", True))
        
        if not hasattr(self, 'proc_comments'): self.proc_comments = tk.BooleanVar()
        self.proc_comments.set(d.get("remove_comments", False))
        
        if not hasattr(self, 'proc_empty'): self.proc_empty = tk.BooleanVar()
        self.proc_empty.set(d.get("remove_empty_lines", False))
        
        if not hasattr(self, 'proc_indent'): self.proc_indent = tk.BooleanVar()
        self.proc_indent.set(d.get("fix_indent", False))

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(header_frame, text="ULTIMATE CONTEXT EXPORTER v4", style="Header.TLabel").pack(side="left")
        
        btn_add_root = ttk.Button(header_frame, text="+ Add Custom Folder", command=self.add_custom_root)
        btn_add_root.pack(side="left", padx=20)

        # --- PRESETS UI ---
        preset_frame = ttk.Frame(header_frame)
        preset_frame.pack(side="right")
        
        ttk.Label(preset_frame, text="Preset:").pack(side="left", padx=(0, 5))
        self.preset_var = tk.StringVar()
        self.preset_cb = ttk.Combobox(preset_frame, textvariable=self.preset_var, state="readonly", width=20)
        self.preset_cb.pack(side="left")
        self.preset_cb.bind("<<ComboboxSelected>>", self.on_preset_select)
        
        ttk.Button(preset_frame, text="💾 Save", width=6, command=self.save_preset_dialog).pack(side="left", padx=(5, 0))
        # ------------------

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)

        self.tab_explorer = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_explorer, text="📂 Structure & Rules")
        self.setup_explorer_tab()

        self.tab_settings = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_settings, text="⚙️ Settings")
        self.setup_settings_tab()

        self.tab_processing = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_processing, text="🧠 AI Optimization")
        self.setup_processing_tab()

        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill="x", pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(action_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=(0, 10))

        btn_grid = ttk.Frame(action_frame)
        btn_grid.pack(fill="x")
        
        ttk.Button(btn_grid, text="Rescan All", command=self.refresh_full_tree).pack(side="left", padx=(0, 5))
        self.export_btn = ttk.Button(btn_grid, text="🚀 EXPORT CONTEXT", style="Accent.TButton", command=self.start_export_thread)
        self.export_btn.pack(side="right", fill="x", expand=True)

    def setup_explorer_tab(self):
        container = ttk.Frame(self.tab_explorer)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        left_panel = ttk.Frame(container)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        lbl_frame = ttk.Frame(left_panel)
        lbl_frame.pack(fill="x")
        ttk.Label(lbl_frame, text="Project Structure (Check to Include)", style="SubHeader.TLabel").pack(side="left")
        
        self.tree = ttk.Treeview(left_panel, selectmode="browse", show="tree headings", columns=("path",))
        self.tree.heading("#0", text="Name")
        self.tree.column("#0", width=400)
        self.tree.column("path", width=0, stretch=False) 
        
        vsb = ttk.Scrollbar(left_panel, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(left_panel, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        btn_tree_ctrl = ttk.Frame(left_panel)
        btn_tree_ctrl.pack(fill="x", pady=5)
        ttk.Button(btn_tree_ctrl, text="Exclude/Block Selected Folder", command=self.block_selected_folder).pack(side="left")
        ttk.Button(btn_tree_ctrl, text="Remove Custom Root", command=self.remove_custom_root).pack(side="right")

        right_panel = ttk.Frame(container, width=380)
        right_panel.pack(side="right", fill="y", padx=10)
        
        ttk.Label(right_panel, text="Extension Whitelist", style="SubHeader.TLabel").pack(anchor="w", pady=(0, 10))
        
        self.lbl_editing_scope = ttk.Label(right_panel, text="Scope: GLOBAL", foreground="#06b6d4")
        self.lbl_editing_scope.pack(anchor="w", pady=(0, 5))
        
        cols = ("Ext", "Allowed?", "Add .txt?")
        self.ext_tree = ttk.Treeview(right_panel, columns=cols, show="headings", height=20)
        self.ext_tree.heading("Ext", text="Ext / File")
        self.ext_tree.heading("Allowed?", text="Allowed?")
        self.ext_tree.heading("Add .txt?", text="Add .txt?")
        self.ext_tree.column("Ext", width=120)
        self.ext_tree.column("Allowed?", width=70)
        self.ext_tree.column("Add .txt?", width=70)
        self.ext_tree.pack(fill="x", expand=True, pady=5)
        self.ext_tree.bind("<Double-1>", self.on_ext_tree_double_click)

        btn_ext = ttk.Frame(right_panel)
        btn_ext.pack(fill="x", pady=5)
        ttk.Button(btn_ext, text="Add New Extension", command=self.add_extension_dialog).pack(fill="x", pady=2)
        ttk.Button(btn_ext, text="Remove Extension", command=self.remove_extension).pack(fill="x", pady=2)
        
        ttk.Separator(right_panel, orient="horizontal").pack(fill="x", pady=10)
        
        ttk.Button(right_panel, text="Save to Selected Folder", command=self.save_folder_specific_config).pack(fill="x", pady=2)
        ttk.Button(right_panel, text="Revert to Global", command=self.revert_folder_to_global).pack(fill="x", pady=2)
        
        self.load_ext_table(self.global_ext_config)

    def setup_settings_tab(self):
        f = ttk.Frame(self.tab_settings)
        f.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.conf_merge = tk.BooleanVar(value=self.config.get("merge_mode", False))
        self.conf_flatten = tk.BooleanVar(value=self.config.get("flatten_paths", True))
        
        # --- LEFT COLUMN: EXPORT MODES ---
        left_col = ttk.Frame(f)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ttk.Label(left_col, text="Export Mode", style="SubHeader.TLabel").pack(anchor="w", pady=(0, 10))
        ttk.Checkbutton(left_col, text="Merge ALL code into one file (code.txt)", variable=self.conf_merge).pack(anchor="w", pady=5)
        ttk.Checkbutton(left_col, text="Flatten Paths (apps/web/main.ts -> apps_web_main.ts)", variable=self.conf_flatten).pack(anchor="w", pady=5)
        
        # --- RIGHT COLUMN: FORCED EXCLUDES & INCLUDES ---
        right_col = ttk.Frame(f)
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # 1. Excludes
        ttk.Label(right_col, text="⛔ Permanent Excludes (Files/Folders)", style="SubHeader.TLabel").pack(anchor="w")
        btn_ex = ttk.Frame(right_col)
        btn_ex.pack(fill="x", pady=5)
        ttk.Button(btn_ex, text="Add File/Folder...", command=self.add_exclude_dialog).pack(side="left")
        ttk.Button(btn_ex, text="Remove", command=self.remove_exclude_item).pack(side="left", padx=5)
        
        self.list_excludes = tk.Listbox(right_col, bg="#252526", fg="#ff6b6b", height=6)
        self.list_excludes.pack(fill="x", expand=True, pady=5)
        for i in self.forced_excludes: self.list_excludes.insert(tk.END, i)
        
        ttk.Separator(right_col, orient="horizontal").pack(fill="x", pady=15)

        # 2. Includes
        ttk.Label(right_col, text="✅ Forced File Includes", style="SubHeader.TLabel").pack(anchor="w")
        btn_inc = ttk.Frame(right_col)
        btn_inc.pack(fill="x", pady=5)
        ttk.Button(btn_inc, text="Add File...", command=self.add_force_include).pack(side="left")
        ttk.Button(btn_inc, text="Remove", command=self.remove_force_include).pack(side="left", padx=5)
        
        self.list_includes = tk.Listbox(right_col, bg="#252526", fg="#a5f3fc", height=6)
        self.list_includes.pack(fill="x", expand=True, pady=5)
        for i in self.forced_includes: self.list_includes.insert(tk.END, i)

    def setup_processing_tab(self):
        f = ttk.Frame(self.tab_processing)
        f.pack(fill="both", expand=True, padx=20, pady=20)
        self.proc_comments = tk.BooleanVar(value=self.config.get("remove_comments", False))
        self.proc_empty = tk.BooleanVar(value=self.config.get("remove_empty_lines", False))
        self.proc_indent = tk.BooleanVar(value=self.config.get("fix_indent", False))
        
        ttk.Label(f, text="Code Cleaning", style="SubHeader.TLabel").pack(anchor="w", pady=(0, 10))
        ttk.Checkbutton(f, text="Remove Comments (Safe Mode)", variable=self.proc_comments).pack(anchor="w", pady=5)
        ttk.Checkbutton(f, text="Remove Empty Lines", variable=self.proc_empty).pack(anchor="w", pady=5)
        ttk.Checkbutton(f, text="Normalize Indentation", variable=self.proc_indent).pack(anchor="w", pady=5)

    def refresh_presets_list(self):
        if not os.path.exists(self.presets_path): return
        files = [f.replace(".json", "") for f in os.listdir(self.presets_path) if f.endswith(".json")]
        self.preset_cb['values'] = files

    def save_preset_dialog(self):
        name = simpledialog.askstring("Save Preset", "Enter preset name:")
        if name:
            # Build the config dict same as save_config
            current_tree_state = {self.tree_nodes[i]: s for i, s in self.node_states.items() if self.tree_nodes.get(i)}
            
            d = {
                "custom_roots": self.custom_roots,
                "blocked_paths": list(self.blocked_paths),
                "forced_includes": self.forced_includes,
                "forced_excludes": self.forced_excludes,
                "global_ext_config": self.global_ext_config,
                "folder_configs": self.folder_configs,
                "tree_selection_state": current_tree_state,
                "merge_mode": self.conf_merge.get(),
                "flatten_paths": self.conf_flatten.get(),
                "remove_comments": self.proc_comments.get(),
                "remove_empty_lines": self.proc_empty.get(),
                "fix_indent": self.proc_indent.get()
            }
            
            p_file = os.path.join(self.presets_path, f"{name}.json")
            with open(p_file, 'w') as f: json.dump(d, f, indent=2)
            
            self.refresh_presets_list()
            self.preset_var.set(name)
            messagebox.showinfo("Saved", f"Preset '{name}' saved!")

    def on_preset_select(self, event):
        name = self.preset_var.get()
        if not name: return
        
        p_file = os.path.join(self.presets_path, f"{name}.json")
        if os.path.exists(p_file):
            try:
                with open(p_file, 'r') as f:
                    d = json.load(f)
                    d["blocked_paths"] = set(d.get("blocked_paths", []))
                    
                    # 1. Apply Logic
                    self.apply_config_data(d)
                    
                    # 2. Refresh Tree (State & Checkboxes)
                    self.refresh_full_tree()
                    
                    # 3. Refresh Lists (Excludes/Includes)
                    self.list_excludes.delete(0, tk.END)
                    for i in self.forced_excludes: self.list_excludes.insert(tk.END, i)
                    
                    self.list_includes.delete(0, tk.END)
                    for i in self.forced_includes: self.list_includes.insert(tk.END, i)
                    
                    # 4. Refresh Extension Table
                    self.load_ext_table(self.global_ext_config)
                    self.lbl_editing_scope.config(text="Scope: GLOBAL", foreground="#06b6d4")
                    
                    messagebox.showinfo("Loaded", f"Preset '{name}' loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load preset: {e}")

    def add_custom_root(self):
        path = filedialog.askdirectory()
        if path:
            if path not in self.custom_roots:
                self.custom_roots.append(path)
                self.refresh_full_tree()
    
    def remove_custom_root(self):
        sel = self.tree.selection()
        if not sel: return
        path = self.tree_nodes.get(sel[0])
        if path in self.custom_roots:
            self.custom_roots.remove(path)
            self.refresh_full_tree()

    def block_selected_folder(self):
        sel = self.tree.selection()
        if not sel: return
        path = self.tree_nodes.get(sel[0])
        if path:
            if messagebox.askyesno("Block Path", f"Permanently exclude {path}?\nIt will disappear from the tree."):
                self.blocked_paths.add(path)
                self.refresh_full_tree()

    def refresh_full_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.tree_nodes.clear()
        self.node_states.clear()
        
        roots_to_scan = []
        
        cats = ['apps', 'package', 'crate', 'libs', 'tools', 'services', 'src', 'src-tauri', 'scripts', 'docker']
        for c in cats:
            p = os.path.join(self.base_path, c)
            if os.path.exists(p) and os.path.isdir(p):
                roots_to_scan.append(p)
        
        for cr in self.custom_roots:
            if os.path.exists(cr):
                roots_to_scan.append(cr)
        
        for r in roots_to_scan:
            if r in self.blocked_paths: continue
            self.populate_tree_recursive("", r)

    def populate_tree_recursive(self, parent_id, path):
        if path in self.blocked_paths: return
        
        name = os.path.basename(path)
        if name in DEFAULT_IGNORES or name.startswith('.'): return 

        # Restore state if path exists in saved config, else False
        is_checked = self.saved_node_states.get(path, False)

        icon = "✅" if is_checked else "⬜"
        oid = self.tree.insert(parent_id, "end", text=f"{icon} {name}", open=False, values=(path,))
        self.tree_nodes[oid] = path
        self.node_states[oid] = is_checked
        
        try:
            items = os.listdir(path)
            items.sort()
            
            sub_dirs = []
            sub_files = []
            
            for i in items:
                full = os.path.join(path, i)
                if i in DEFAULT_IGNORES or i.startswith('.'): continue
                if full in self.blocked_paths: continue
                
                if os.path.isdir(full):
                    sub_dirs.append(full)
                else:
                    sub_files.append(full)
            
            for d in sub_dirs:
                self.populate_tree_recursive(oid, d)
            
            for f in sub_files:
                fname = os.path.basename(f)
                _, ext = os.path.splitext(fname)
                if fname == "Dockerfile" or fname == "Makefile": ext = fname 
                
                if ext == ".txt": continue 

                # Restore file state
                f_checked = self.saved_node_states.get(f, False)
                f_icon = "✅" if f_checked else "⬜"
                
                fid = self.tree.insert(oid, "end", text=f"{f_icon} {fname}", values=(f,))
                self.tree_nodes[fid] = f
                self.node_states[fid] = f_checked
                
        except PermissionError: pass

    def on_tree_click(self, event):
        element = self.tree.identify_element(event.x, event.y)
        if "indicator" in element:
            return

        region = self.tree.identify("region", event.x, event.y)
        if region == "tree":
            item_id = self.tree.identify_row(event.y)
            if item_id:
                self.toggle_check(item_id)

    def toggle_check(self, item_id):
        current = self.node_states.get(item_id, False)
        new_state = not current
        self.set_node_state(item_id, new_state)
        
        for child in self.tree.get_children(item_id):
            self.set_node_recursive(child, new_state)

    def set_node_recursive(self, item_id, state):
        self.set_node_state(item_id, state)
        for child in self.tree.get_children(item_id):
            self.set_node_recursive(child, state)

    def set_node_state(self, item_id, state):
        self.node_states[item_id] = state
        txt = self.tree.item(item_id, "text")
        clean_txt = txt[2:] 
        icon = "✅" if state else "⬜"
        self.tree.item(item_id, text=f"{icon} {clean_txt}")

    def on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel: 
            self.load_ext_table(self.global_ext_config)
            self.lbl_editing_scope.config(text="Scope: GLOBAL", foreground="#06b6d4")
            return
            
        path = self.tree_nodes.get(sel[0])
        if os.path.isdir(path):
            self.current_folder_editing = path
            cfg = self.folder_configs.get(path, self.global_ext_config)
            self.load_ext_table(cfg)
            self.lbl_editing_scope.config(text=f"Scope: {os.path.basename(path)}", foreground="#f472b6")

    def load_ext_table(self, config_map):
        for i in self.ext_tree.get_children(): self.ext_tree.delete(i)
        
        sorted_keys = sorted(config_map.keys())
        for k in sorted_keys:
            val = config_map[k]
            allowed = "Yes" if (k in config_map) else "No" 
            add_txt = "Yes" if val else "No"
            self.ext_tree.insert("", "end", values=(k, "Yes", add_txt))

    def on_ext_tree_double_click(self, event):
        item = self.ext_tree.identify_row(event.y)
        col = self.ext_tree.identify_column(event.x)
        if not item: return
        
        vals = list(self.ext_tree.item(item, "values"))
        key = vals[0]
        
        if col == "#2": 
            pass 
        elif col == "#3": 
            vals[2] = "No" if vals[2] == "Yes" else "Yes"
            self.ext_tree.item(item, values=vals)

    def add_extension_dialog(self):
        ans = simpledialog.askstring("Add Extension", "Enter extension (e.g. .rb) or exact filename (e.g. Gemfile):")
        if ans:
            if not ans.startswith(".") and "." in ans: pass 
            elif not ans.startswith(".") and ans not in ["Dockerfile", "Makefile", "Gemfile", "LICENSE"]: ans = "." + ans
            
            self.ext_tree.insert("", "end", values=(ans, "Yes", "No"))

    def remove_extension(self):
        s = self.ext_tree.selection()
        if s: self.ext_tree.delete(s[0])

    def get_current_ui_ext_map(self):
        m = {}
        for item in self.ext_tree.get_children():
            v = self.ext_tree.item(item, "values")
            key = v[0]
            add_txt = (v[2] == "Yes")
            m[key] = add_txt
        return m

    def save_folder_specific_config(self):
        if not hasattr(self, 'current_folder_editing') or not self.current_folder_editing:
            self.global_ext_config = self.get_current_ui_ext_map()
            messagebox.showinfo("Saved", "Global extension configuration updated.")
            return
            
        m = self.get_current_ui_ext_map()
        self.folder_configs[self.current_folder_editing] = m
        messagebox.showinfo("Saved", f"Configuration saved for {os.path.basename(self.current_folder_editing)}")

    def revert_folder_to_global(self):
        if hasattr(self, 'current_folder_editing') and self.current_folder_editing in self.folder_configs:
            del self.folder_configs[self.current_folder_editing]
            self.load_ext_table(self.global_ext_config)

    def add_force_include(self):
        f = filedialog.askopenfilename()
        if f and f not in self.forced_includes:
            self.forced_includes.append(f)
            self.list_includes.insert(tk.END, f)

    def remove_force_include(self):
        s = self.list_includes.curselection()
        if s:
            val = self.list_includes.get(s[0])
            self.forced_includes.remove(val)
            self.list_includes.delete(s[0])

    def add_exclude_dialog(self):
        path = filedialog.askopenfilename(title="Select file to ignore")
        if not path:
            path = filedialog.askdirectory(title="Select folder to ignore")
        
        if path:
            try: rel = os.path.relpath(path, self.base_path)
            except: rel = path
            
            if rel not in self.forced_excludes:
                self.forced_excludes.append(rel)
                self.list_excludes.insert(tk.END, rel)

    def remove_exclude_item(self):
        s = self.list_excludes.curselection()
        if s:
            val = self.list_excludes.get(s[0])
            self.forced_excludes.remove(val)
            self.list_excludes.delete(s[0])

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    d = json.load(f)
                    d["blocked_paths"] = set(d.get("blocked_paths", []))
                    if "global_ext_config" not in d: d["global_ext_config"] = DEFAULT_EXT_CONFIG.copy()
                    return d
            except: pass
        return {}

    def save_config(self):
        current_tree_state = {}
        for item_id, state in self.node_states.items():
            path = self.tree_nodes.get(item_id)
            if path:
                current_tree_state[path] = state

        d = {
            "custom_roots": self.custom_roots,
            "blocked_paths": list(self.blocked_paths),
            "forced_includes": self.forced_includes,
            "forced_excludes": self.forced_excludes,
            "global_ext_config": self.global_ext_config,
            "folder_configs": self.folder_configs,
            "tree_selection_state": current_tree_state,
            "merge_mode": self.conf_merge.get(),
            "flatten_paths": self.conf_flatten.get(),
            "remove_comments": self.proc_comments.get(),
            "remove_empty_lines": self.proc_empty.get(),
            "fix_indent": self.proc_indent.get()
        }
        try:
            with open(CONFIG_FILE, 'w') as f: json.dump(d, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def clean_code(self, content, ext):
        if self.proc_comments.get() and ext in ['.ts', '.js', '.rs', '.py', '.java', '.c', '.cpp', '.vue', '.cs', '.go']:
            pattern = re.compile(r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"', re.DOTALL | re.MULTILINE)
            content = re.sub(pattern, lambda m: " " if m.group(0).startswith('/') else m.group(0), content)
        
        if self.proc_empty.get():
            content = "\n".join([line for line in content.splitlines() if line.strip()])
            
        if self.proc_indent.get():
            content = "\n".join([line.rstrip() for line in content.splitlines()])
            
        return content

    def start_export_thread(self):
        self.save_config()
        self.export_btn.config(state="disabled", text="Processing...")
        self.progress_var.set(0)
        threading.Thread(target=self.run_export).start()

    def run_export(self):
        try:
            if os.path.exists(self.export_path): shutil.rmtree(self.export_path)
            os.makedirs(self.export_path)
            
            merge_mode = self.conf_merge.get()
            merge_handle = open(os.path.join(self.export_path, "code.txt"), "w", encoding="utf-8") if merge_mode else None
            
            files_to_process = []
            
            # Gather checked files from tree
            for item_id, state in self.node_states.items():
                if state:
                    path = self.tree_nodes[item_id]
                    if os.path.isfile(path):
                        files_to_process.append(path)

            # Gather forced includes
            for fi in self.forced_includes:
                if os.path.exists(fi): files_to_process.append(fi)

            unique_files = sorted(list(set(files_to_process)))
            total = len(unique_files)
            processed_count = 0

            # Pre-calculate exclude paths (normalized)
            excludes_norm = [os.path.abspath(os.path.join(self.base_path, e)) for e in self.forced_excludes]

            for i, fpath in enumerate(unique_files):
                self.progress_var.set((i / total) * 100)
                
                # CHECK EXCLUDES
                abs_path = os.path.abspath(fpath)
                is_excluded = False
                for ex in excludes_norm:
                    # Check if file IS the exclude or INSIDE an excluded folder
                    if abs_path == ex or abs_path.startswith(ex + os.sep):
                        is_excluded = True
                        break
                if is_excluded: continue

                fname = os.path.basename(fpath)
                _, ext = os.path.splitext(fname)
                if fname in DEFAULT_EXT_CONFIG: key = fname
                else: key = ext

                folder_rule = None
                curr = os.path.dirname(fpath)
                while len(curr) >= len(self.base_path):
                    if curr in self.folder_configs:
                        folder_rule = self.folder_configs[curr]
                        break
                    p_curr = os.path.dirname(curr)
                    if p_curr == curr: break
                    curr = p_curr
                
                active_map = folder_rule if folder_rule else self.global_ext_config
                
                is_forced = (fpath in self.forced_includes)
                
                if not is_forced:
                    if ext == ".txt": continue 
                    if key not in active_map: continue 
                
                add_txt = False
                if is_forced: add_txt = True 
                elif key in active_map: add_txt = active_map[key]

                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    content = self.clean_code(content, ext)
                    rel_path = os.path.relpath(fpath, self.base_path)
                    
                    if merge_mode:
                        sep = "-" * 60
                        merge_handle.write(f"{sep}\nFILE: {rel_path}\n{sep}\n{content}\n{sep}\n\n")
                    else:
                        if self.conf_flatten.get():
                            safe_name = rel_path.replace(os.sep, "_").replace(":", "")
                        else:
                            safe_name = rel_path
                            os.makedirs(os.path.join(self.export_path, os.path.dirname(safe_name)), exist_ok=True)
                            
                        if add_txt and not safe_name.endswith(".txt"): safe_name += ".txt"
                        
                        out_p = os.path.join(self.export_path, safe_name)
                        with open(out_p, 'w', encoding='utf-8') as out:
                            out.write(f"// FILE: {rel_path}\n" + content)
                            
                    processed_count += 1
                except Exception as e:
                    print(f"Skipped {fpath}: {e}")

            if merge_handle: merge_handle.close()
            
            self.root.after(0, lambda: self.finish_export(processed_count))

        except Exception as e:
            print(e)
            self.root.after(0, lambda: self.export_btn.config(state="normal", text="🚀 EXPORT CONTEXT"))

    def finish_export(self, count):
        self.progress_var.set(100)
        self.export_btn.config(state="normal", text="🚀 EXPORT CONTEXT")
        messagebox.showinfo("Done", f"Exported {count} files to:\n{self.export_path}")
        try: os.startfile(self.export_path)
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = UltimateExporter(root)
    root.mainloop()