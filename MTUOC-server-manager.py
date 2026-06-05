import os
import sys
import subprocess
import shutil
import yaml
import threading
import requests
import json
import random
import xmlrpc.client
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

# Suppress the specific FutureWarning from huggingface_hub modules
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="huggingface_hub")
from huggingface_hub import HfApi

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the download logic directly from MTUOC-downloader.py
try:
    from MTUOC_downloader import RecipeDownloader
except ImportError:
    import importlib.util
    try:
        spec = importlib.util.spec_from_file_location("MTUOC_downloader", "MTUOC-downloader.py")
        MTUOC_downloader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(MTUOC_downloader)
        RecipeDownloader = MTUOC_downloader.RecipeDownloader
    except Exception as e:
        # Failsafe if the downloader script is missing during startup
        pass

class MTUOCManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MTUOC-server Manager")
        
        # Enhanced window dimensions for multi-editor layout
        self.root.geometry("1800x1200")
        self.root.resizable(True, True)
        
        # Absolute base directory determination to solve relative path issues
        self.base_dir = os.path.dirname(os.path.abspath(__file__)) if __file__ in locals() else os.getcwd()
        
        self.process = None
        self.config_files = []
        self.filtered_configs = []
        self.stop_reader = threading.Event()
        
        # Server control variables
        self.current_port = "8000"
        self.current_type = "MTUOC"
        self.current_ip = "127.0.0.1"
        self.associated_model_yaml = None
        self.current_aux_file = None  # Tracks the currently opened file in the auxiliary editor

        # Recipe variables
        self.all_recipes = []
        self.filtered_recipes = []

        style = ttk.Style()
        style.theme_use('clam')

        # Primary Tabbed Interface Deployment (Notebook)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: CONTROL
        self.tab_control = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_control, text=" Control ")
        self.setup_control_tab()

        # Tab 2: TEST
        self.tab_test = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_test, text=" Test ")
        self.setup_test_tab()

        # Tab 3: EDITOR (With internal sub-tabs)
        self.tab_editor = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_editor, text=" Configuration Editor ")
        self.setup_editor_tab()

        # Tab 4: AUXILIARY EDITOR
        self.tab_aux = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_aux, text=" Aux. editor ")
        self.setup_aux_editor_tab()

        # Tab 5: RECIPES (New Integrated Tab!)
        self.tab_recipes = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.tab_recipes, text=" Recipes ")
        self.setup_recipes_tab()

        # Initial loading routines
        self.refresh_configs()
        self.load_recipes_from_repo()

    # --- CONTROL TAB CONFIGURATION (DISTRIBUCIÓ IDÈNTICA A RECIPES) ---
    def setup_control_tab(self):
        frame = ttk.Frame(self.tab_control, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # 1. Capçalera superior amb títol i botó de refresh local (com el de connect de recipes)
        top_frame = ttk.LabelFrame(frame, text=" Local Server Manager ", padding="10")
        top_frame.pack(fill=tk.X, pady=(0, 10))

        lbl_title = ttk.Label(top_frame, text="MTUOC-server manager", font=("Arial", 14, "bold"))
        lbl_title.pack(side=tk.LEFT, padx=(0, 10))

        btn_refresh_local = ttk.Button(top_frame, text="REFRESH LOCAL CONFIGS", command=self.refresh_configs)
        btn_refresh_local.pack(side=tk.RIGHT)

        # 2. Quadre de cerca / filtre (Igual que a Recipes)
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        lbl_search = ttk.Label(search_frame, text="Filter configurations: ", font=("Arial", 10, "bold"))
        lbl_search.pack(side=tk.LEFT, padx=(0, 5))
        
        self.config_search_var = tk.StringVar()
        self.config_search_var.trace_add("write", self.filter_configs)
        self.entry_config_search = ttk.Entry(search_frame, textvariable=self.config_search_var, font=("Arial", 10))
        self.entry_config_search.pack(fill=tk.X, expand=True)

        # 3. Llista de fitxers YAML local (Igual que Available Recipes)
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        lbl_list = ttk.Label(list_frame, text="Available server configurations (YAML):", font=("Arial", 10))
        lbl_list.pack(anchor=tk.W, pady=(0, 5))
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.listbox_configs = tk.Listbox(
            list_frame, 
            font=("Arial", 10), 
            yscrollcommand=scrollbar.set, 
            selectmode=tk.SINGLE,
            bg="#ffffff",
            fg="#000000",
            highlightbackground="#cccccc"
        )
        scrollbar.config(command=self.listbox_configs.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox_configs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 4. Botons d'acció de control (START / STOP) i etiqueta d'estat
        actions_frame = ttk.Frame(frame)
        actions_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.btn_start = ttk.Button(actions_frame, text="START SERVER", command=self.start_server)
        self.btn_start.pack(side=tk.LEFT, padx=(0, 5), expand=True, fill=tk.X)

        self.btn_stop = ttk.Button(actions_frame, text="STOP SERVER", command=self.stop_server, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.RIGHT, padx=(5, 0), expand=True, fill=tk.X)

        self.lbl_status = ttk.Label(frame, text="Status: Terminated / Stopped", foreground="red", font=("Arial", 11, "bold"))
        self.lbl_status.pack(pady=(5, 10), anchor=tk.W)

        # 5. Consola del servidor en temps real
        lbl_log = ttk.Label(frame, text="Live Server Console Output (Select text to copy):", font=("Arial", 9))
        lbl_log.pack(anchor=tk.W, pady=(5, 2))
        
        self.txt_log = scrolledtext.ScrolledText(frame, height=14, bg="#1e1e1e", fg="#ffffff", font=("Courier", 10), selectbackground="#444444")
        self.txt_log.pack(fill=tk.BOTH, expand=True)

    # --- TEST TAB CONFIGURATION ---
    def setup_test_tab(self):
        frame = ttk.Frame(self.tab_test, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        lbl_test_title = ttk.Label(frame, text="Test model", font=("Arial", 14, "bold"))
        lbl_test_title.pack(pady=(0, 10))

        lbl_src = ttk.Label(frame, text="Source Text Segment:", font=("Arial", 10))
        lbl_src.pack(anchor=tk.W)
        self.test_text_source = scrolledtext.ScrolledText(frame, height=8, font=("Arial", 11))
        self.test_text_source.pack(fill=tk.BOTH, expand=True, pady=(5, 15))

        lbl_tgt = ttk.Label(frame, text="Target Output Translation:", font=("Arial", 10))
        lbl_tgt.pack(anchor=tk.W)
        self.test_text_target = scrolledtext.ScrolledText(frame, height=8, font=("Arial", 11), bg="#f9f9f9")
        self.test_text_target.pack(fill=tk.BOTH, expand=True, pady=(5, 15))

        test_btn_frame = ttk.Frame(frame)
        test_btn_frame.pack(fill=tk.X)

        self.btn_translate = ttk.Button(test_btn_frame, text="TRANSLATE", command=self.translate_test)
        self.btn_translate.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.btn_clear_test = ttk.Button(test_btn_frame, text="CLEAR", command=self.clear_test)
        self.btn_clear_test.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    # --- DUAL-EDITOR TAB CONFIGURATION ---
    def setup_editor_tab(self):
        main_editor_frame = ttk.Frame(self.tab_editor, padding="15")
        main_editor_frame.pack(fill=tk.BOTH, expand=True)

        self.btn_load_yaml = ttk.Button(main_editor_frame, text="LOAD SELECTED SERVER CONFIGURATION & LINKED MODEL CONFIG", command=self.load_yaml_to_editor)
        self.btn_load_yaml.pack(fill=tk.X, pady=(0, 10))

        self.editor_notebook = ttk.Notebook(main_editor_frame)
        self.editor_notebook.pack(fill=tk.BOTH, expand=True)

        # SUB-TAB A: Server Configuration
        self.subtab_server = ttk.Frame(self.editor_notebook)
        self.editor_notebook.add(self.subtab_server, text=" 1. Server Configuration (Main) ")
        
        frame_srv = ttk.Frame(self.subtab_server, padding="10")
        frame_srv.pack(fill=tk.BOTH, expand=True)
        self.lbl_editing_file_server = ttk.Label(frame_srv, text="No Server file loaded.", font=("Arial", 10, "italic"), foreground="gray")
        self.lbl_editing_file_server.pack(anchor=tk.W, pady=(0, 5))
        self.txt_editor_server = scrolledtext.ScrolledText(frame_srv, wrap=tk.WORD, font=("Courier", 11), bg="#ffffff", fg="#000000")
        self.txt_editor_server.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.btn_save_server = ttk.Button(frame_srv, text="SAVE SERVER CONFIGURATION", command=self.save_server_yaml)
        self.btn_save_server.pack(fill=tk.X)

        # SUB-TAB B: Model Configuration
        self.subtab_model = ttk.Frame(self.editor_notebook)
        self.editor_notebook.add(self.subtab_model, text=" 2. Model Configuration (Linked) ")
        
        frame_mdl = ttk.Frame(self.subtab_model, padding="10")
        frame_mdl.pack(fill=tk.BOTH, expand=True)
        self.lbl_editing_file_model = ttk.Label(frame_mdl, text="No nested model configuration detected.", font=("Arial", 10, "italic"), foreground="gray")
        self.lbl_editing_file_model.pack(anchor=tk.W, pady=(0, 5))
        self.txt_editor_model = scrolledtext.ScrolledText(frame_mdl, wrap=tk.WORD, font=("Courier", 11), bg="#ffffff", fg="#000000")
        self.txt_editor_model.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.btn_save_model = ttk.Button(frame_mdl, text="SAVE MODEL CONFIGURATION", command=self.save_model_yaml, state=tk.DISABLED)
        self.btn_save_model.pack(fill=tk.X)

    # --- AUXILIARY EDITOR TAB CONFIGURATION ---
    def setup_aux_editor_tab(self):
        frame = ttk.Frame(self.tab_aux, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        lbl_aux_title = ttk.Label(frame, text="Auxiliary Configuration Editor", font=("Arial", 14, "bold"))
        lbl_aux_title.pack(pady=(0, 5))

        self.lbl_aux_file_status = ttk.Label(frame, text="No active auxiliary file loaded. Use 'OPEN FILE' to begin.", font=("Arial", 10, "italic"), foreground="gray")
        self.lbl_aux_file_status.pack(anchor=tk.W, pady=(0, 10))

        self.txt_editor_aux = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=("Courier", 11), bg="#ffffff", fg="#000000")
        self.txt_editor_aux.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        aux_btn_frame = ttk.Frame(frame)
        aux_btn_frame.pack(fill=tk.X)

        self.btn_open_aux = ttk.Button(aux_btn_frame, text="OPEN FILE", command=self.open_aux_file)
        self.btn_open_aux.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.btn_save_as_aux = ttk.Button(aux_btn_frame, text="SAVE AS...", command=self.save_as_aux_file)
        self.btn_save_as_aux.pack(side=tk.RIGHT, padx=5, expand=True, fill=tk.X)

    # --- RECIPES TAB CONFIGURATION (INTEGRATED) ---
    def setup_recipes_tab(self):
        # 1. Repository Connection Interface
        repo_frame = ttk.LabelFrame(self.tab_recipes, text=" Recipe Repository (Hugging Face Dataset ID) ", padding="10")
        repo_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.entry_repo = ttk.Entry(repo_frame, font=("Arial", 10))
        self.entry_repo.insert(0, "aoliverg/MTUOC-recipes")
        self.entry_repo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        btn_connect = ttk.Button(repo_frame, text="CONNECT / REFRESH", command=self.load_recipes_from_repo)
        btn_connect.pack(side=tk.RIGHT)

        # 2. Search Box Filter mechanics
        search_frame = ttk.Frame(self.tab_recipes)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        lbl_search = ttk.Label(search_frame, text="Filter recipes: ", font=("Arial", 10, "bold"))
        lbl_search.pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_recipes)
        self.entry_search = ttk.Entry(search_frame, textvariable=self.search_var, font=("Arial", 10))
        self.entry_search.pack(fill=tk.X, expand=True)

        # 3. Available Files List view
        list_frame = ttk.Frame(self.tab_recipes)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        lbl_list = ttk.Label(list_frame, text="Available recipes (YAML):", font=("Arial", 10))
        lbl_list.pack(anchor=tk.W, pady=(0, 5))
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.listbox_recipes = tk.Listbox(
            list_frame, 
            font=("Arial", 10), 
            yscrollcommand=scrollbar.set, 
            selectmode=tk.SINGLE,
            bg="#ffffff",
            fg="#000000",
            highlightbackground="#cccccc"
        )
        scrollbar.config(command=self.listbox_recipes.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox_recipes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 4. Interactive Execution Control and logging area
        actions_frame = ttk.Frame(self.tab_recipes)
        actions_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_download_recipe = ttk.Button(actions_frame, text="DOWNLOAD SELECTED RECIPE", command=self.start_download_thread)
        self.btn_download_recipe.pack(fill=tk.X)
        
        lbl_console = ttk.Label(self.tab_recipes, text="Download Console Output:", font=("Arial", 9))
        lbl_console.pack(anchor=tk.W, pady=(5, 2))
        
        self.txt_recipe_console = scrolledtext.ScrolledText(self.tab_recipes, height=12, bg="#1e1e1e", fg="#ffffff", font=("Courier", 10))
        self.txt_recipe_console.pack(fill=tk.BOTH, expand=True)

    # --- SERVER MANAGEMENT OPERATIONS ---
    def refresh_configs(self):
        self.config_files = []
        for file in os.listdir(self.base_dir):
            if file.endswith((".yaml", ".yml")):
                if file in ["config-server.yaml", "config-preprocess.yaml", "config-tokenization.yaml", "config-postprocess.yaml"]:
                    continue
                try:
                    with open(os.path.join(self.base_dir, file), 'r', encoding='utf-8') as f:
                        content = yaml.safe_load(f)
                        if isinstance(content, dict) and "MTengine" in content:
                            self.config_files.append(file)
                except Exception as e:
                    print(f"Framework Alert: Core engine skipped file '{file}': {e}")
                    
        self.filter_configs()

    def filter_configs(self, *args):
        search_text = self.config_search_var.get().lower()
        self.listbox_configs.delete(0, tk.END)
        self.filtered_configs = [c for c in self.config_files if search_text in c.lower()]
        
        if self.filtered_configs:
            for config in self.filtered_configs:
                self.listbox_configs.insert(tk.END, config)
            self.listbox_configs.selection_set(0) # Selecciona el primer element per defecte
            self.btn_start.config(state=tk.NORMAL)
        else:
            self.listbox_configs.insert(tk.END, "No matching configuration files found")
            self.btn_start.config(state=tk.DISABLED)

    def get_selected_config(self):
        selection = self.listbox_configs.curselection()
        if not selection:
            return None
        selected_text = self.filtered_configs[selection[0]]
        if selected_text.startswith("No matching"):
            return None
        return selected_text

    def log_message(self, message):
        self.txt_log.insert(tk.END, message)
        self.txt_log.see(tk.END)

    def read_output(self):
        while not self.stop_reader.is_set():
            if self.process is None:
                break
            try:
                line = self.process.stdout.readline()
                if not line and (self.process is None or self.process.poll() is not None): 
                    break
                if line: 
                    self.lbl_status.after(0, lambda l=line: self.log_message(l))
            except:
                break
            
        while not self.stop_reader.is_set():
            if self.process is None:
                break
            try:
                line = self.process.stderr.readline()
                if not line and (self.process is None or self.process.poll() is not None): 
                    break
                if line: 
                    self.lbl_status.after(0, lambda l=line: self.log_message(f"ERROR: {l}"))
            except:
                break

    def start_server(self):
        selected_config = self.get_selected_config()
        if not selected_config:
            messagebox.showwarning("Warning", "Please select a valid configuration file from the list.")
            return

        config_full_path = os.path.join(self.base_dir, selected_config)
        try:
            with open(config_full_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                self.current_port = content["MTUOCServer"].get("port", "8000")
                self.current_type = content["MTUOCServer"].get("type", "MTUOC")
        except Exception as e:
            messagebox.showerror("Parsing Error", f"Could not map initialization metadata: {e}")
            return

        try:
            self.txt_log.delete("1.0", tk.END)
            self.log_message(f"--- Initializing {self.current_type} server on port {self.current_port} ---\n")
            
            self.stop_reader.clear()
            self.process = subprocess.Popen(
                [sys.executable, "-u", "MTUOC-server.py", config_full_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1,
                cwd=self.base_dir
            )
            
            self.lbl_status.config(
                text=f"Status: ACTIVE | Engine Type: {self.current_type} | Port Allocation: {self.current_port}\nListening environment: http://localhost:{self.current_port}", 
                foreground="green"
            )
            self.btn_start.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
            
            threading.Thread(target=self.read_output, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to instantiate server subprocess:\n{e}")

    def stop_server(self):
        self.log_message("\n--- Dispatching termination signal to server... ---\n")
        try:
            self.stop_reader.set()
            
            selected_config = self.get_selected_config()
            if selected_config:
                config_full_path = os.path.join(self.base_dir, selected_config)
                shutil.copy(config_full_path, os.path.join(self.base_dir, "config-server.yaml"))
                
                # --- AVIS D'OLLAMA SENSE COMPLICACIONS ---
                try:
                    with open(config_full_path, 'r', encoding='utf-8') as f:
                        content = yaml.safe_load(f)
                        
                    server_type = content.get("MTUOCServer", {}).get("type", "")
                    engine_name = content.get("MTengine", "")
                    
                    if "ollama" in server_type.lower() or "ollama" in str(engine_name).lower():
                        self.log_message("ℹ Note: Ollama engine detected. VRAM will be automatically freed by Ollama in 5 minutes if inactive.\n")
                        self.root.update_idletasks()
                except Exception as e_yaml:
                    print(f"Ollama log check skip: {e_yaml}")
            
            # Procedim a tancar el servidor de MTUOC i alliberar els ports de l'aplicació
            subprocess.run([sys.executable, "MTUOC-stop-server.py", selected_config if selected_config else ""], capture_output=True, text=True, cwd=self.base_dir)
            
            if self.process: 
                try:
                    self.process.terminate()
                    self.process.wait(timeout=2)
                except: pass
                self.process = None
                
            self.lbl_status.config(text="Status: Terminated / Stopped", foreground="red")
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Termination Error", f"An anomaly occurred while shutting down the server:\n{e}")
            
            # Executem el script de MTUOC per alliberar ports i tancar el servidor de traducció
            subprocess.run([sys.executable, "MTUOC-stop-server.py", selected_config if selected_config else ""], capture_output=True, text=True, cwd=self.base_dir)
            
            if self.process: 
                try:
                    self.process.terminate()
                    self.process.wait(timeout=2)
                except: pass
                self.process = None
                
            self.lbl_status.config(text="Status: Terminated / Stopped", foreground="red")
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Termination Error", f"An anomaly occurred while shutting down the server:\n{e}")
            if self.process: 
                try:
                    self.process.terminate()
                    self.process.wait(timeout=2)
                except: pass
                self.process = None
                
            self.lbl_status.config(text="Status: Terminated / Stopped", foreground="red")
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Termination Error", f"An anomaly occurred while shutting down the server:\n{e}")
            if self.process: 
                try:
                    self.process.terminate()
                    self.process.wait(timeout=2)
                except: pass
                self.process = None
                
            self.lbl_status.config(text="Status: Terminated / Stopped", foreground="red")
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Termination Error", f"An anomaly occurred while shutting down the server:\n{e}")
            if self.process: 
                try:
                    self.process.terminate()
                    self.process.wait(timeout=2)
                except: pass
                self.process = None
                
            self.lbl_status.config(text="Status: Terminated / Stopped", foreground="red")
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Termination Error", f"An anomaly occurred while shutting down the server:\n{e}")
    def clear_test(self):
        self.test_text_source.delete(1.0, tk.END)
        self.test_text_target.delete(1.0, tk.END)

    def translate_test(self):
        segment = self.test_text_source.get("1.0", tk.END).strip()
        if not segment: return

        self.test_text_target.delete(1.0, tk.END)
        self.test_text_target.insert(tk.END, "Processing translation request...")
        self.root.update_idletasks()
        threading.Thread(target=self.perform_translation, args=(segment,), daemon=True).start()

    def perform_translation(self, segment):
        translation = ""
        try:
            if self.current_type == "MTUOC":
                url = f"http://{self.current_ip}:{self.current_port}/translate"
                params = {"id": random.randint(0, 10000), "src": segment, "srcLang": "any", "tgtLang": "any"}
                response = requests.post(url, json=params, timeout=10)
                translation = response.json().get("tgt", "Error: Missing target translation field.")
            elif self.current_type == "Moses":
                proxy = xmlrpc.client.ServerProxy(f"http://{self.current_ip}:{self.current_port}/RPC2")
                result = proxy.translate({"text": segment})
                translation = result.get('text', '')
            elif self.current_type == "OpenNMT":
                url = f"http://{self.current_ip}:{self.current_port}/translator/translate"
                response = requests.post(url, json=[{"src": segment}], timeout=10)
                translation = response.json()[0][0].get("tgt", "")
            elif self.current_type == "NMTWizard":
                url = f"http://{self.current_ip}:{self.current_port}/translate"
                response = requests.post(url, json={"src": [{"text": segment}]}, timeout=10)
                translation = response.json()["tgt"][0][0].get("text", "")
            elif self.current_type == "ModernMT":
                url = f"http://{self.current_ip}:{self.current_port}/translate"
                response = requests.get(url, params={'q': segment}, timeout=10)
                translation = response.json().get('data', {}).get("translation", "")
        except Exception as e:
            translation = f"Network Connection Error: {str(e)}"

        self.root.after(0, lambda t=translation: self.update_target_text(t))

    def update_target_text(self, text):
        self.test_text_target.delete(1.0, tk.END)
        self.test_text_target.insert(tk.END, text)

    # --- DUAL-EDITOR OPERATIONS ---
    def load_yaml_to_editor(self):
        selected_config = self.get_selected_config()
        if not selected_config:
            messagebox.showwarning("Editor Warning", "No valid configuration schema selected from the Control tab list.")
            return

        config_full_path = os.path.join(self.base_dir, selected_config)
        try:
            with open(config_full_path, "r", encoding="utf-8") as f:
                server_raw = f.read()
            
            self.txt_editor_server.delete("1.0", tk.END)
            self.txt_editor_server.insert(tk.END, server_raw)
            self.lbl_editing_file_server.config(text=f"Server Configuration File: {config_full_path}", foreground="blue")
            
            self.associated_model_yaml = None
            self.txt_editor_model.delete("1.0", tk.END)
            self.lbl_editing_file_model.config(text="No nested model configuration detected.", foreground="gray")
            self.btn_save_model.config(state=tk.DISABLED)

            try:
                parsed_srv = yaml.safe_load(server_raw)
                if isinstance(parsed_srv, dict) and "model_config" in parsed_srv:
                    raw_path = parsed_srv["model_config"]
                    if raw_path.startswith("./") or raw_path.startswith(".\\"):
                        raw_path = raw_path[2:]
                    self.associated_model_yaml = os.path.normpath(os.path.join(self.base_dir, raw_path))
            except Exception as e_yaml:
                print(f"YAML Parsing Alert: {e_yaml}")

            if self.associated_model_yaml:
                if os.path.exists(self.associated_model_yaml):
                    with open(self.associated_model_yaml, "r", encoding="utf-8") as f:
                        model_raw = f.read()
                    self.txt_editor_model.insert(tk.END, model_raw)
                    self.lbl_editing_file_model.config(text=f"Model Configuration File: {self.associated_model_yaml}", foreground="blue")
                    self.btn_save_model.config(state=tk.NORMAL)
                else:
                    self.lbl_editing_file_model.config(text=f"File referenced in model_config not found: {self.associated_model_yaml}", foreground="orange")
            else:
                self.lbl_editing_file_model.config(text="Active engine does not reference an external model_config YAML at root level.", foreground="gray")

        except Exception as e:
            messagebox.showerror("File I/O Error", f"Unable to read files:\n{str(e)}")

    def save_server_yaml(self):
        selected_config = self.get_selected_config()
        if not selected_config: return
        
        config_full_path = os.path.join(self.base_dir, selected_config)
        raw_text = self.txt_editor_server.get("1.0", tk.END)
        try:
            yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            messagebox.showerror("YAML Syntax Error (Server File)", f"Invalid structure rules detected:\n\n{str(exc)}")
            return

        try:
            with open(config_full_path, "w", encoding="utf-8") as f:
                f.write(raw_text)
            messagebox.showinfo("Persistence Status", f"Server parameters committed to '{selected_config}'.")
        except Exception as e:
            messagebox.showerror("Persistence Error", f"Failed to save:\n{e}")

    def save_model_yaml(self):
        if not self.associated_model_yaml or not os.path.exists(self.associated_model_yaml): return
        
        raw_text = self.txt_editor_model.get("1.0", tk.END)
        try:
            yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            messagebox.showerror("YAML Syntax Error (Model File)", f"Invalid structure rules detected:\n\n{str(exc)}")
            return

        try:
            with open(self.associated_model_yaml, "w", encoding="utf-8") as f:
                f.write(raw_text)
            messagebox.showinfo("Persistence Status", f"Model parameters committed successfully.")
        except Exception as e:
            messagebox.showerror("Persistence Error", f"Failed to save:\n{e}")

    # --- AUXILIARY EDITOR FILE OPERATIONS ---
    def open_aux_file(self):
        file_types = [('YAML Configurations', '*.yaml *.yml'), ('All Files', '*.*')]
        chosen_file = filedialog.askopenfilename(initialdir=self.base_dir, title="Open Custom/Secondary Configuration", filetypes=file_types)
        if not chosen_file: return

        try:
            with open(chosen_file, "r", encoding="utf-8") as f:
                file_content = f.read()
            self.txt_editor_aux.delete("1.0", tk.END)
            self.txt_editor_aux.insert(tk.END, file_content)
            self.current_aux_file = chosen_file
            self.lbl_aux_file_status.config(text=f"Currently inspecting auxiliary source: {chosen_file}", foreground="blue")
        except Exception as e:
            messagebox.showerror("File I/O Error", f"Could not open target file:\n{e}")

    def save_as_aux_file(self):
        raw_text = self.txt_editor_aux.get("1.0", tk.END)
        try:
            yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            messagebox.showerror("YAML Syntax Violation", f"Structural anomalies detected. Aborting save sequence:\n\n{str(exc)}")
            return

        file_types = [('YAML Configurations', '*.yaml *.yml'), ('All Files', '*.*')]
        initial_file = os.path.basename(self.current_aux_file) if self.current_aux_file else "custom-config.yaml"
        
        target_save_path = filedialog.asksaveasfilename(
            initialdir=self.base_dir, initialfile=initial_file,
            title="Save Auxiliary Document As", filetypes=file_types, defaultextension=".yaml"
        )
        if not target_save_path: return

        try:
            with open(target_save_path, "w", encoding="utf-8") as f:
                f.write(raw_text)
            self.current_aux_file = target_save_path
            self.lbl_aux_file_status.config(text=f"Currently inspecting auxiliary source: {target_save_path}", foreground="blue")
            messagebox.showinfo("Persistence Status", "Auxiliary data successfully saved.")
            self.refresh_configs()
        except Exception as e:
            messagebox.showerror("Persistence Error", f"An anomaly prevented saving the document:\n{e}")

    # --- RECIPE MANAGEMENT LOGIC ---
    def recipe_log(self, message):
        self.txt_recipe_console.insert(tk.END, message)
        self.txt_recipe_console.see(tk.END)

    def load_recipes_from_repo(self):
        repo_id = self.entry_repo.get().strip()
        if "huggingface.co/datasets/" in repo_id:
            repo_id = repo_id.split("huggingface.co/datasets/")[-1].split("/tree")[0]
            self.entry_repo.delete(0, tk.END)
            self.entry_repo.insert(0, repo_id)

        self.txt_recipe_console.delete("1.0", tk.END)
        self.recipe_log(f"Connecting to Hugging Face Dataset repository: '{repo_id}'...\n")
        
        def fetch():
            try:
                api = HfApi()
                files = api.list_repo_files(repo_id=repo_id, repo_type="dataset")
                self.all_recipes = [f for f in files if f.endswith(('.yaml', '.yml'))]
                self.root.after(0, self.update_recipe_listbox)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Connection Error", f"Could not access the recipe repository:\n{e}"))
                self.root.after(0, lambda: self.recipe_log(f"❌ Connection error: {e}\n"))

        threading.Thread(target=fetch, daemon=True).start()

    def update_recipe_listbox(self):
        self.filter_recipes()
        self.recipe_log(f"✔ Found {len(self.all_recipes)} available recipes.\n")

    def filter_recipes(self, *args):
        search_text = self.search_var.get().lower()
        self.listbox_recipes.delete(0, tk.END)
        self.filtered_recipes = [r for r in self.all_recipes if search_text in r.lower()]
        for recipe in self.filtered_recipes:
            self.listbox_recipes.insert(tk.END, recipe)

    def start_download_thread(self):
        selection = self.listbox_recipes.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a recipe from the list.")
            return
        
        if 'RecipeDownloader' not in globals():
            messagebox.showerror("Dependency Error", "MTUOC-downloader.py was not found or could not be loaded properly.")
            return
        
        selected_recipe = self.filtered_recipes[selection[0]]
        repo_id = self.entry_repo.get().strip()
        remote_yaml_url = f"https://huggingface.co/datasets/{repo_id}/raw/main/{selected_recipe}"
        
        self.btn_download_recipe.config(state=tk.DISABLED)
        self.txt_recipe_console.delete("1.0", tk.END)
        self.recipe_log(f"Initializing download from: {remote_yaml_url}\n\n")
        
        threading.Thread(target=self.execute_recipe_download, args=(remote_yaml_url,), daemon=True).start()

    def execute_recipe_download(self, url):
        try:
            class CustomStdout:
                def __init__(self, log_func):
                    self.log_func = log_func
                def write(self, string):
                    if string.strip():
                        self.log_func(string + "\n")
                def flush(self):
                    pass
            
            old_stdout = sys.stdout
            sys.stdout = CustomStdout(self.recipe_log)
            
            downloader = RecipeDownloader(url)
            downloader.run()
            
            sys.stdout = old_stdout
            self.root.after(0, lambda: messagebox.showinfo("Success", "The recipe model and configurations have been successfully downloaded."))
            self.root.after(0, self.refresh_configs) # Auto-refresh local YAML file selector drop-down list
            
        except Exception as e:
            sys.stdout = old_stdout
            self.root.after(0, lambda: messagebox.showerror("Download Error", f"The download process failed:\n{e}"))
        finally:
            self.root.after(0, lambda: self.btn_download_recipe.config(state=tk.NORMAL))

if __name__ == "__main__":
    root = tk.Tk()
    app = MTUOCManagerApp(root)
    root.mainloop()
