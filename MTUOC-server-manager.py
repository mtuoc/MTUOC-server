#    MTUOC-server-manager (PyQt6 version)
#    Copyright (C) 2026 Antoni Oliver
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

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
import time
import warnings

# Suppress the specific FutureWarning from huggingface_hub modules
warnings.filterwarnings("ignore", category=FutureWarning, module="huggingface_hub")
from huggingface_hub import HfApi

# IMPORTS DE PYQT6
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QListWidget, QGroupBox, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

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
    except Exception:
        pass


class TranslationThread(QThread):
    """Fil secundari de seguretat per a la petició de traducció."""
    translation_done = pyqtSignal(str)

    def __init__(self, parent_app, segment):
        super().__init__()
        self.parent_app = parent_app
        self.segment = segment

    def run(self):
        translation = self.parent_app.perform_translation(self.segment)
        self.translation_done.emit(translation)


class LogReaderThread(QThread):
    """Fil secundari de seguretat per llegir el fitxer de logs del servidor."""
    new_log_line = pyqtSignal(str)
    process_finished = pyqtSignal()

    def __init__(self, log_file_path, process, stop_event):
        super().__init__()
        self.log_file_path = log_file_path
        self.process = process
        self.stop_event = stop_event

    def run(self):
        time.sleep(0.2)
        try:
            with open(self.log_file_path, "r", encoding="utf-8") as f_read:
                f_read.seek(0)
                while not self.stop_event.is_set():
                    if self.process is None:
                        break
                    line = f_read.readline()
                    if line:
                        self.new_log_line.emit(line)
                    else:
                        if self.process.poll() is not None:
                            self.new_log_line.emit("\n--- Server process terminated unexpectedly. ---")
                            self.process_finished.emit()
                            break
                        time.sleep(0.1)
        except Exception as e_file:
            print(f"Error reading log file tracker: {e_file}")


class RecipeFetchThread(QThread):
    """Fil secundari per consultar les receptes del repositori Hugging Face."""
    recipes_fetched = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, repo_id):
        super().__init__()
        self.repo_id = repo_id

    def run(self):
        try:
            api = HfApi()
            files = api.list_repo_files(repo_id=self.repo_id, repo_type="dataset")
            all_recipes = [f for f in files if f.endswith(('.yaml', '.yml'))]
            self.recipes_fetched.emit(all_recipes)
        except Exception as e:
            self.error_occurred.emit(str(e))


class RecipeDownloadThread(QThread):
    """Fil secundari per gestionar la descàrrega de receptes."""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)

    def __init__(self, cmd, base_dir):
        super().__init__()
        self.cmd = cmd
        self.base_dir = base_dir

    def run(self):
        try:
            env_unbuffered = os.environ.copy()
            env_unbuffered["PYTHONUNBUFFERED"] = "1"

            process_dl = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=self.base_dir,
                env=env_unbuffered
            )

            while True:
                line = process_dl.stdout.readline()
                if not line and process_dl.poll() is not None:
                    break
                if line:
                    clean_line = line.replace('\r', '\n')
                    self.log_signal.emit(clean_line)

            process_dl.poll()
            self.finished_signal.emit(process_dl.returncode)
        except Exception as e:
            self.log_signal.emit(f"\n[ERROR] Could not execute downloader:\n{e}")
            self.finished_signal.emit(-1)


class MTUOCManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MTUOC-server Manager")
        self.resize(1200, 800)

        # Determinar el directori base absolut
        self.base_dir = os.path.dirname(os.path.abspath(__file__)) if __file__ in locals() else os.getcwd()

        self.process = None
        self.config_files = []
        self.filtered_configs = []
        self.stop_reader = threading.Event()
        self.log_thread = None

        # Variables de control del servidor
        self.current_port = "8000"
        self.current_type = "MTUOC"
        self.current_ip = "127.0.0.1"
        self.associated_model_yaml = None
        self.current_aux_file = None
        self.current_server_file = None
        self.last_selected_config = None

        # Variables de receptes
        self.all_recipes = []
        self.filtered_recipes = []

        # Interfície principal de pestanyes (QTabWidget)
        self.notebook = QTabWidget()
        self.setCentralWidget(self.notebook)

        # Crear les 5 pestanyes principals
        self.setup_control_tab()
        self.setup_test_tab()
        self.setup_editor_tab()
        self.setup_aux_editor_tab()
        self.setup_recipes_tab()

        # Càrregues inicials
        self.refresh_configs()
        self.load_recipes_from_repo()

    # --- PESTANYA 1: CONTROL ---
    def setup_control_tab(self):
        tab_control = QWidget()
        layout = QVBoxLayout()

        top_group = QGroupBox(" Local Server Manager ")
        top_layout = QHBoxLayout()
        
        lbl_title = QLabel("MTUOC-server manager")
        lbl_title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        btn_refresh = QPushButton("REFRESH LOCAL CONFIGS")
        btn_refresh.clicked.connect(self.refresh_configs)

        top_layout.addWidget(lbl_title)
        top_layout.addStretch()
        top_layout.addWidget(btn_refresh)
        top_group.setLayout(top_layout)
        layout.addWidget(top_group)

        search_layout = QHBoxLayout()
        lbl_search = QLabel("Filter configurations: ")
        lbl_search.setStyleSheet("font-weight: bold;")
        self.entry_config_search = QLineEdit()
        self.entry_config_search.textChanged.connect(self.filter_configs)
        search_layout.addWidget(lbl_search)
        search_layout.addWidget(self.entry_config_search)
        layout.addLayout(search_layout)

        lbl_list = QLabel("Available server configurations (YAML):")
        layout.addWidget(lbl_list)

        self.listbox_configs = QListWidget()
        self.listbox_configs.setStyleSheet("background-color: #ffffff; color: #000000;")
        self.listbox_configs.itemSelectionChanged.connect(self.on_config_selected)
        layout.addWidget(self.listbox_configs)

        actions_layout = QHBoxLayout()
        self.btn_start = QPushButton("START SERVER")
        self.btn_start.clicked.connect(self.start_server)
        
        self.btn_stop = QPushButton("STOP SERVER")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_server)

        actions_layout.addWidget(self.btn_start)
        actions_layout.addWidget(self.btn_stop)
        layout.addLayout(actions_layout)

        self.lbl_status = QLabel("Status: Terminated / Stopped")
        self.lbl_status.setStyleSheet("color: red; font-weight: bold; font-size: 11pt;")
        layout.addWidget(self.lbl_status)

        lbl_log = QLabel("Live Server Console Output (Select text to copy):")
        layout.addWidget(lbl_log)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("background-color: #1e1e1e; color: #ffffff; font-family: Courier;")
        layout.addWidget(self.txt_log)

        tab_control.setLayout(layout)
        self.notebook.addTab(tab_control, " Control ")

    # --- PESTANYA 2: TEST ---
    def setup_test_tab(self):
        tab_test = QWidget()
        layout = QVBoxLayout()

        lbl_test_title = QLabel("Test model")
        lbl_test_title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(lbl_test_title)

        layout.addWidget(QLabel("Source Text Segment:"))
        self.test_text_source = QTextEdit()
        layout.addWidget(self.test_text_source)

        layout.addWidget(QLabel("Target Output Translation:"))
        self.test_text_target = QTextEdit()
        self.test_text_target.setStyleSheet("background-color: #f9f9f9;")
        layout.addWidget(self.test_text_target)

        btn_layout = QHBoxLayout()
        self.btn_translate = QPushButton("TRANSLATE")
        self.btn_translate.clicked.connect(self.translate_test)
        self.btn_clear_test = QPushButton("CLEAR")
        self.btn_clear_test.clicked.connect(self.clear_test)

        btn_layout.addWidget(self.btn_translate)
        btn_layout.addWidget(self.btn_clear_test)
        layout.addLayout(btn_layout)

        tab_test.setLayout(layout)
        self.notebook.addTab(tab_test, " Test ")

    # --- PESTANYA 3: EDITOR DE CONFIGURACIÓ ---
    def setup_editor_tab(self):
        tab_editor = QWidget()
        layout = QVBoxLayout()

        self.btn_load_yaml = QPushButton("LOAD SERVER CONFIGURATION & LINKED MODEL CONFIG...")
        self.btn_load_yaml.clicked.connect(self.load_yaml_to_editor)
        layout.addWidget(self.btn_load_yaml)

        self.editor_notebook = QTabWidget()

        subtab_server = QWidget()
        layout_srv = QVBoxLayout()
        self.lbl_editing_file_server = QLabel("No Server file loaded.")
        self.lbl_editing_file_server.setStyleSheet("color: gray; font-style: italic;")
        self.txt_editor_server = QTextEdit()
        self.txt_editor_server.setStyleSheet("font-family: Courier; background-color: #ffffff; color: #000000;")
        self.btn_save_server = QPushButton("SAVE SERVER CONFIGURATION AS...")
        self.btn_save_server.clicked.connect(self.save_server_yaml)

        layout_srv.addWidget(self.lbl_editing_file_server)
        layout_srv.addWidget(self.txt_editor_server)
        layout_srv.addWidget(self.btn_save_server)
        subtab_server.setLayout(layout_srv)

        subtab_model = QWidget()
        layout_mdl = QVBoxLayout()
        self.lbl_editing_file_model = QLabel("No nested model configuration detected.")
        self.lbl_editing_file_model.setStyleSheet("color: gray; font-style: italic;")
        self.txt_editor_model = QTextEdit()
        self.txt_editor_model.setStyleSheet("font-family: Courier; background-color: #ffffff; color: #000000;")
        self.btn_save_model = QPushButton("SAVE MODEL CONFIGURATION AS...")
        self.btn_save_model.setEnabled(False)
        self.btn_save_model.clicked.connect(self.save_model_yaml)

        layout_mdl.addWidget(self.lbl_editing_file_model)
        layout_mdl.addWidget(self.txt_editor_model)
        layout_mdl.addWidget(self.btn_save_model)
        subtab_model.setLayout(layout_mdl)

        self.editor_notebook.addTab(subtab_server, " 1. Server Configuration (Main) ")
        self.editor_notebook.addTab(subtab_model, " 2. Model Configuration (Linked) ")
        layout.addWidget(self.editor_notebook)

        tab_editor.setLayout(layout)
        self.notebook.addTab(tab_editor, " Configuration Editor ")

    # --- PESTANYA 4: EDITOR AUXILIAR ---
    def setup_aux_editor_tab(self):
        tab_aux = QWidget()
        layout = QVBoxLayout()

        lbl_aux_title = QLabel("Auxiliary Configuration Editor")
        lbl_aux_title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(lbl_aux_title)

        self.lbl_aux_file_status = QLabel("No active auxiliary file loaded. Use 'OPEN FILE' to begin.")
        self.lbl_aux_file_status.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.lbl_aux_file_status)

        self.txt_editor_aux = QTextEdit()
        self.txt_editor_aux.setStyleSheet("font-family: Courier; background-color: #ffffff; color: #000000;")
        layout.addWidget(self.txt_editor_aux)

        btn_layout = QHBoxLayout()
        self.btn_open_aux = QPushButton("OPEN FILE...")
        self.btn_open_aux.clicked.connect(self.open_aux_file)
        self.btn_save_as_aux = QPushButton("SAVE FILE AS...")
        self.btn_save_as_aux.clicked.connect(self.save_as_aux_file)

        btn_layout.addWidget(self.btn_open_aux)
        btn_layout.addWidget(self.btn_save_as_aux)
        layout.addLayout(btn_layout)

        tab_aux.setLayout(layout)
        self.notebook.addTab(tab_aux, " Aux. editor ")

    # --- PESTANYA 5: RECEPTES ---
    def setup_recipes_tab(self):
        tab_recipes = QWidget()
        layout = QVBoxLayout()

        repo_group = QGroupBox(" Recipe Repository (Hugging Face Dataset ID) ")
        repo_layout = QHBoxLayout()
        self.entry_repo = QLineEdit("aoliverg/MTUOC-recipes")
        btn_connect = QPushButton("CONNECT / REFRESH")
        btn_connect.clicked.connect(self.load_recipes_from_repo)

        repo_layout.addWidget(self.entry_repo)
        repo_layout.addWidget(btn_connect)
        repo_group.setLayout(repo_layout)
        layout.addWidget(repo_group)

        search_layout = QHBoxLayout()
        lbl_search = QLabel("Filter recipes: ")
        lbl_search.setStyleSheet("font-weight: bold;")
        self.entry_search = QLineEdit()
        self.entry_search.textChanged.connect(self.filter_recipes)
        search_layout.addWidget(lbl_search)
        search_layout.addWidget(self.entry_search)
        layout.addLayout(search_layout)

        layout.addWidget(QLabel("Available recipes (YAML):"))
        self.listbox_recipes = QListWidget()
        self.listbox_recipes.setStyleSheet("background-color: #ffffff; color: #000000;")
        layout.addWidget(self.listbox_recipes)

        self.btn_download_recipe = QPushButton("DOWNLOAD SELECTED RECIPE")
        self.btn_download_recipe.clicked.connect(self.start_download_thread)
        layout.addWidget(self.btn_download_recipe)

        layout.addWidget(QLabel("Download Console Output:"))
        self.txt_recipe_console = QTextEdit()
        self.txt_recipe_console.setReadOnly(True)
        self.txt_recipe_console.setStyleSheet("background-color: #1e1e1e; color: #ffffff; font-family: Courier;")
        layout.addWidget(self.txt_recipe_console)

        tab_recipes.setLayout(layout)
        self.notebook.addTab(tab_recipes, " Recipes ")

    # --- FUNCIONALITATS I MÈTODES DEL SERVIDOR ---
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

    def filter_configs(self):
        search_text = self.entry_config_search.text().lower()
        self.listbox_configs.clear()
        self.filtered_configs = [c for c in self.config_files if search_text in c.lower()]
        
        if self.filtered_configs:
            self.listbox_configs.addItems(self.filtered_configs)
            if self.last_selected_config in self.filtered_configs:
                idx = self.filtered_configs.index(self.last_selected_config)
                self.listbox_configs.setCurrentRow(idx)
            else:
                self.listbox_configs.setCurrentRow(0)
            self.btn_start.setEnabled(True)
        else:
            self.listbox_configs.addItem("No matching configuration files found")
            self.btn_start.setEnabled(False)

    def on_config_selected(self):
        selected_item = self.listbox_configs.currentItem()
        if selected_item:
            text = selected_item.text()
            if not text.startswith("No matching"):
                self.last_selected_config = text

    def get_selected_config(self):
        selected_item = self.listbox_configs.currentItem()
        if not selected_item:
            return self.last_selected_config
        selected_text = selected_item.text()
        if selected_text.startswith("No matching"):
            return None
        self.last_selected_config = selected_text
        return selected_text

    def log_message(self, message):
        self.txt_log.append(message.rstrip('\n'))

    def start_server(self):
        selected_config = self.get_selected_config()
        if not selected_config:
            QMessageBox.warning(self, "Warning", "Please select a valid configuration file from the list.")
            return

        config_full_path = os.path.join(self.base_dir, selected_config)
        try:
            with open(config_full_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                self.current_port = content["MTUOCServer"].get("port", "8000")
                self.current_type = content["MTUOCServer"].get("type", "MTUOC")
        except Exception as e:
            QMessageBox.critical(self, "Parsing Error", f"Could not map initialization metadata: {e}")
            return

        try:
            self.txt_log.clear()
            self.log_message(f"--- Initializing {self.current_type} server on port {self.current_port} ---")
            
            self.stop_reader.clear()

            self.log_file_path = os.path.join(self.base_dir, "server_output.log")
            with open(self.log_file_path, "w", encoding="utf-8") as f_init:
                f_init.write("")

            self.server_log_file = open(self.log_file_path, "a", encoding="utf-8")

            if getattr(sys, 'frozen', False):
                binary_name = "MTUOC-server.exe" if sys.platform.startswith('win') else "MTUOC-server"
                server_path = os.path.join(self.base_dir, binary_name)
                cmd = [server_path, config_full_path]
            else:
                cmd = [sys.executable, "-u", "MTUOC-server.py", config_full_path]

            env_unbuffered = os.environ.copy()
            env_unbuffered["PYTHONUNBUFFERED"] = "1"

            self.process = subprocess.Popen(
                cmd,
                stdout=self.server_log_file,
                stderr=self.server_log_file,
                cwd=self.base_dir,
                env=env_unbuffered
            )
            
            self.lbl_status.setText(f"Status: ACTIVE | Engine Type: {self.current_type} | Port Allocation: {self.current_port}\nListening environment: http://localhost:{self.current_port}")
            self.lbl_status.setStyleSheet("color: green; font-weight: bold; font-size: 11pt;")
            
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            
            self.log_thread = LogReaderThread(self.log_file_path, self.process, self.stop_reader)
            self.log_thread.new_log_line.connect(self.log_message)
            self.log_thread.process_finished.connect(self.on_server_unexpected_exit)
            self.log_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Initialization Error", f"Failed to instantiate server subprocess:\n{e}")

    def on_server_unexpected_exit(self):
        self.lbl_status.setText("Status: Terminated / Stopped")
        self.lbl_status.setStyleSheet("color: red; font-weight: bold; font-size: 11pt;")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def stop_server(self):
        self.log_message("\n--- Dispatching termination signal to server... ---")
        try:
            self.stop_reader.set()
            if self.log_thread:
                self.log_thread.wait(1000)
            
            selected_config = self.get_selected_config()
            if selected_config:
                config_full_path = os.path.join(self.base_dir, selected_config)
                shutil.copy(config_full_path, os.path.join(self.base_dir, "config-server.yaml"))
                
                try:
                    with open(config_full_path, 'r', encoding='utf-8') as f:
                        content = yaml.safe_load(f)
                    server_type = content.get("MTUOCServer", {}).get("type", "")
                    engine_name = content.get("MTengine", "")
                    if "ollama" in server_type.lower() or "ollama" in str(engine_name).lower():
                        self.log_message("[INFO] Note: Ollama engine detected. VRAM will be automatically freed by Ollama in 5 minutes if inactive.")
                except Exception as e_yaml:
                    print(f"Ollama log check skip: {e_yaml}")

            if getattr(sys, 'frozen', False):
                binary_stop_name = "MTUOC-stop-server.exe" if sys.platform.startswith('win') else "MTUOC-stop-server"
                stop_path = os.path.join(self.base_dir, binary_stop_name)
                cmd_stop = [stop_path, selected_config if selected_config else ""]
            else:
                cmd_stop = [sys.executable, "MTUOC-stop-server.py", selected_config if selected_config else ""]

            subprocess.run(cmd_stop, capture_output=True, text=True, cwd=self.base_dir)
            
            if self.process: 
                try:
                    self.process.terminate()
                    self.process.wait(timeout=2)
                except Exception:
                    pass
                self.process = None
                
            self.lbl_status.setText("Status: Terminated / Stopped")
            self.lbl_status.setStyleSheet("color: red; font-weight: bold; font-size: 11pt;")
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            
        except Exception as e:
            QMessageBox.critical(self, "Termination Error", f"An anomaly occurred while shutting down the server:\n{e}")

    # --- MÈTODES DE LA PESTANYA TEST ---
    def clear_test(self):
        self.test_text_source.clear()
        self.test_text_target.clear()

    def translate_test(self):
        segment = self.test_text_source.toPlainText().strip()
        if not segment:
            return
        
        self.test_text_target.setText("Processing translation request...")
        
        self.trans_thread = TranslationThread(self, segment)
        self.trans_thread.translation_done.connect(self.update_target_text)
        self.trans_thread.start()

    def update_target_text(self, text):
        self.test_text_target.setText(text)

    def perform_translation(self, segment):
        translation = ""
        custom_timeout = 60
        selected_config = self.get_selected_config()
        if selected_config:
            try:
                config_full_path = os.path.join(self.base_dir, selected_config)
                with open(config_full_path, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                if "MTUOCServer" in content and "timeout" in content["MTUOCServer"]:
                    custom_timeout = int(content["MTUOCServer"]["timeout"])
            except Exception as e_timeout:
                print(f"Could not read custom timeout, using default value: {e_timeout}")

        try:
            if self.current_type == "MTUOC":
                url = f"http://{self.current_ip}:{self.current_port}/translate"
                params = {"id": random.randint(0, 10000), "src": segment, "srcLang": "any", "tgtLang": "any"}
                response = requests.post(url, json=params, timeout=custom_timeout)
                translation = response.json().get("tgt", "Error: Missing target translation field.")
            elif self.current_type == "Moses":
                proxy = xmlrpc.client.ServerProxy(f"http://{self.current_ip}:{self.current_port}/RPC2")
                import socket
                socket.setdefaulttimeout(custom_timeout)
                result = proxy.translate({"text": segment})
                translation = result.get('text', '')
            elif self.current_type == "OpenNMT":
                url = f"http://{self.current_ip}:{self.current_port}/translator/translate"
                response = requests.post(url, json=[{"src": segment}], timeout=custom_timeout)
                translation = response.json()[0][0].get("tgt", "")
            elif self.current_type == "NMTWizard":
                url = f"http://{self.current_ip}:{self.current_port}/translate"
                response = requests.post(url, json={"src": [{"text": segment}]}, timeout=custom_timeout)
                translation = response.json()["tgt"][0][0].get("text", "")
            elif self.current_type == "ModernMT":
                url = f"http://{self.current_ip}:{self.current_port}/translate"
                response = requests.get(url, params={'q': segment}, timeout=custom_timeout)
                translation = response.json().get('data', {}).get("translation", "")
        except Exception as e:
            translation = f"Network Connection Error: {str(e)}"
        
        return translation

    # --- MÈTODES DE L'EDITOR DE CONFIGURACIÓ ---
    def load_yaml_to_editor(self):
        selected_config = self.get_selected_config()
        initial_file = os.path.join(self.base_dir, selected_config) if selected_config else self.base_dir

        chosen_file, _ = QFileDialog.getOpenFileName(
            self, "Open Server Configuration", initial_file, "YAML Configurations (*.yaml *.yml);;All Files (*)"
        )
        if not chosen_file:
            return

        try:
            with open(chosen_file, "r", encoding="utf-8") as f:
                server_raw = f.read()
            self.txt_editor_server.setText(server_raw)
            self.lbl_editing_file_server.setText(f"Server Configuration File: {chosen_file}")
            self.lbl_editing_file_server.setStyleSheet("color: blue;")

            self.current_server_file = chosen_file
            self.associated_model_yaml = None
            self.txt_editor_model.clear()
            self.lbl_editing_file_model.setText("No nested model configuration detected.")
            self.lbl_editing_file_model.setStyleSheet("color: gray;")
            self.btn_save_model.setEnabled(False)

            try:
                parsed_srv = yaml.safe_load(server_raw)
                if isinstance(parsed_srv, dict) and "model_config" in parsed_srv:
                    raw_path = parsed_srv["model_config"]
                    if raw_path.startswith("./") or raw_path.startswith(".\\"):
                        raw_path = raw_path[2:]
                    self.associated_model_yaml = os.path.normpath(os.path.join(os.path.dirname(chosen_file), raw_path))
            except Exception as e_yaml:
                print(f"YAML Parsing Alert: {e_yaml}")

            if self.associated_model_yaml:
                if os.path.exists(self.associated_model_yaml):
                    with open(self.associated_model_yaml, "r", encoding="utf-8") as f:
                        model_raw = f.read()
                    self.txt_editor_model.setText(model_raw)
                    self.lbl_editing_file_model.setText(f"Model Configuration File: {self.associated_model_yaml}")
                    self.lbl_editing_file_model.setStyleSheet("color: blue;")
                    self.btn_save_model.setEnabled(True)
                else:
                    self.lbl_editing_file_model.setText(f"File referenced in model_config not found: {self.associated_model_yaml}")
                    self.lbl_editing_file_model.setStyleSheet("color: orange;")
        except Exception as e:
            QMessageBox.critical(self, "File I/O Error", f"Unable to read files:\n{str(e)}")

    def save_server_yaml(self):
        selected_config = self.get_selected_config()
        initial_file = os.path.join(self.base_dir, selected_config if selected_config else "config-server.yaml")

        raw_text = self.txt_editor_server.toPlainText()
        try:
            yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            QMessageBox.critical(self, "YAML Syntax Error (Server File)", f"Invalid structure rules detected:\n\n{str(exc)}")
            return

        target_save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Server Configuration As", initial_file, "YAML Configurations (*.yaml *.yml);;All Files (*)"
        )
        if not target_save_path:
            return

        try:
            with open(target_save_path, "w", encoding="utf-8") as f:
                f.write(raw_text)
            self.lbl_editing_file_server.setText(f"Server Configuration File: {target_save_path}")
            self.lbl_editing_file_server.setStyleSheet("color: blue;")
            self.current_server_file = target_save_path
            QMessageBox.information(self, "Persistence Status", f"Server parameters committed successfully to:\n{os.path.basename(target_save_path)}")
            self.refresh_configs()
        except Exception as e:
            QMessageBox.critical(self, "Persistence Error", f"Failed to save:\n{e}")

    def save_model_yaml(self):
        initial_file = os.path.join(self.base_dir, os.path.basename(self.associated_model_yaml) if self.associated_model_yaml else "config-model.yaml")

        raw_text = self.txt_editor_model.toPlainText()
        try:
            yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            QMessageBox.critical(self, "YAML Syntax Error (Model File)", f"Invalid structure rules detected:\n\n{str(exc)}")
            return

        target_save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Model Configuration As", initial_file, "YAML Configurations (*.yaml *.yml);;All Files (*)"
        )
        if not target_save_path:
            return

        try:
            with open(target_save_path, "w", encoding="utf-8") as f:
                f.write(raw_text)
            self.associated_model_yaml = target_save_path
            self.lbl_editing_file_model.setText(f"Model Configuration File: {target_save_path}")
            self.lbl_editing_file_model.setStyleSheet("color: blue;")
            QMessageBox.information(self, "Persistence Status", "Model parameters committed successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Persistence Error", f"Failed to save:\n{e}")

    # --- MÈTODES DE L'EDITOR AUXILIAR ---
    def open_aux_file(self):
        selected_config = self.get_selected_config()
        initial_file = os.path.join(self.base_dir, selected_config) if selected_config else self.base_dir

        chosen_file, _ = QFileDialog.getOpenFileName(
            self, "Open Custom/Secondary Configuration", initial_file, "YAML Configurations (*.yaml *.yml);;All Files (*)"
        )
        if not chosen_file:
            return
        try:
            with open(chosen_file, "r", encoding="utf-8") as f:
                file_content = f.read()
            self.txt_editor_aux.setText(file_content)
            self.current_aux_file = chosen_file
            self.lbl_aux_file_status.setText(f"Currently inspecting auxiliary source: {chosen_file}")
            self.lbl_aux_file_status.setStyleSheet("color: blue;")
        except Exception as e:
            QMessageBox.critical(self, "File I/O Error", f"Could not open target file:\n{e}")

    def save_as_aux_file(self):
        raw_text = self.txt_editor_aux.toPlainText()
        try:
            yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            QMessageBox.critical(self, "YAML Syntax Violation", f"Structural anomalies detected. Aborting save sequence:\n\n{str(exc)}")
            return

        selected_config = self.get_selected_config()
        if self.current_aux_file:
            initial_file = self.current_aux_file
        elif selected_config:
            initial_file = os.path.join(self.base_dir, selected_config)
        else:
            initial_file = os.path.join(self.base_dir, "custom-config.yaml")

        target_save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Auxiliary Document As", initial_file, "YAML Configurations (*.yaml *.yml);;All Files (*)"
        )
        if not target_save_path:
            return

        try:
            with open(target_save_path, "w", encoding="utf-8") as f:
                f.write(raw_text)
            self.current_aux_file = target_save_path
            self.lbl_aux_file_status.setText(f"Currently inspecting auxiliary source: {target_save_path}")
            self.lbl_aux_file_status.setStyleSheet("color: blue;")
            QMessageBox.information(self, "Persistence Status", "Auxiliary data successfully saved.")
            self.refresh_configs()
        except Exception as e:
            QMessageBox.critical(self, "Persistence Error", f"An anomaly prevented saving the document:\n{e}")

    # --- MÈTODES DE RECEPTES (CORREGITS AMB QTHREAD) ---
    def recipe_log(self, message):
        self.txt_recipe_console.append(message.rstrip('\n'))

    def load_recipes_from_repo(self):
        repo_id = self.entry_repo.text().strip()
        if "huggingface.co/datasets/" in repo_id:
            repo_id = repo_id.split("huggingface.co/datasets/")[-1].split("/tree")[0]
            self.entry_repo.setText(repo_id)

        self.txt_recipe_console.clear()
        self.recipe_log(f"Connecting to Hugging Face Dataset repository: '{repo_id}'...\n")

        # Ús de RecipeFetchThread (QThread) per evitar Segmentation Fault al carregar receptes
        self.fetch_thread = RecipeFetchThread(repo_id)
        self.fetch_thread.recipes_fetched.connect(self.on_recipes_fetched)
        self.fetch_thread.error_occurred.connect(self.on_recipes_fetch_error)
        self.fetch_thread.start()

    def on_recipes_fetched(self, recipes):
        self.all_recipes = recipes
        self.update_recipe_listbox()

    def on_recipes_fetch_error(self, error_msg):
        self.recipe_log(f"Connection error: {error_msg}\n")
        QMessageBox.critical(self, "Connection Error", f"Could not access the recipe repository:\n{error_msg}")

    def update_recipe_listbox(self):
        self.filter_recipes()
        self.recipe_log(f"Found {len(self.all_recipes)} available recipes.\n")

    def filter_recipes(self):
        search_text = self.entry_search.text().lower()
        self.listbox_recipes.clear()
        self.filtered_recipes = [r for r in self.all_recipes if search_text in r.lower()]
        self.listbox_recipes.addItems(self.filtered_recipes)

    def start_download_thread(self):
        selected_item = self.listbox_recipes.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Warning", "Please select a recipe from the list.")
            return

        selected_recipe = selected_item.text()
        repo_id = self.entry_repo.text().strip()
        remote_yaml_url = f"https://huggingface.co/datasets/{repo_id}/raw/main/{selected_recipe}"

        self.btn_download_recipe.setEnabled(False)
        self.txt_recipe_console.clear()
        self.recipe_log(f"Initializing download from: {remote_yaml_url}\n\n")

        if getattr(sys, 'frozen', False):
            binary_downloader = "MTUOC-downloader.exe" if sys.platform.startswith('win') else "MTUOC-downloader"
            cmd = [os.path.join(self.base_dir, binary_downloader), remote_yaml_url]
        else:
            cmd = [sys.executable, "-u", "MTUOC-downloader.py", remote_yaml_url]

        self.dl_thread = RecipeDownloadThread(cmd, self.base_dir)
        self.dl_thread.log_signal.connect(self.recipe_log)
        self.dl_thread.finished_signal.connect(self.on_download_finished)
        self.dl_thread.start()

    def on_download_finished(self, return_code):
        self.btn_download_recipe.setEnabled(True)
        if return_code == 0:
            self.recipe_log("\n[SUCCESS] The recipe model and configurations have been successfully downloaded.")
            self.refresh_configs()
        else:
            self.recipe_log(f"\n[ERROR] The downloader exited with an error code: {return_code}")

    # Captura del tancament de finestra per a la sortida neta del procés
    def closeEvent(self, event):
        if self.process and self.process.poll() is None:
            self.stop_server()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MTUOCManagerApp()
    window.show()
    sys.exit(app.exec())
