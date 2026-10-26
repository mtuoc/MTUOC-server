#    MTUOC-vLLM-test-server (PyQt6 version)
#    Copyright (C) 2026  Antoni Oliver / Extended for vLLM
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

import sys
import os
import yaml
import json

# IMPORTS FOR PYQT6 INTERFACE
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget,
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QTextEdit, QPushButton, QMessageBox, QFileDialog,
    QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# IMPORTS FOR VLLM CLIENT VIA OPENAI API
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def safe_int(val, default=None):
    """Safely converts a value to int if possible."""
    if val is None:
        return default
    try:
        val_str = str(val).strip()
        if not val_str or val_str.lower() == "none" or val_str.lower() == "null":
            return default
        return int(val_str)
    except (ValueError, TypeError):
        return default


def safe_float(val, default=0.0):
    """Safely converts a value to float if possible."""
    if val is None:
        return default
    try:
        val_str = str(val).strip()
        if not val_str or val_str.lower() == "none" or val_str.lower() == "null":
            return default
        return float(val_str)
    except (ValueError, TypeError):
        return default


class TranslationThread(QThread):
    """Background thread to handle translation requests without freezing the GUI."""
    translation_done = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, config, text):
        super().__init__()
        self.config = config
        self.text = text

    def run(self):
        if OpenAI is None:
            self.error_occurred.emit("The 'openai' library is not installed. Please run 'pip install openai'.")
            return

        try:
            host = self.config.get('host', '127.0.0.1').strip()
            port = safe_int(self.config.get('port'), 8000)
            
            base_url = f"http://{host}:{port}/v1"
            client = OpenAI(
                base_url=base_url,
                api_key=self.config.get('api_key', 'EMPTY') or "EMPTY"
            )

            curr_src = self.config.get('src_lang', 'English')
            curr_tgt = self.config.get('tgt_lang', 'Catalan')

            system_prompt = self.config.get('system_prompt', '')
            user_template = self.config.get('user_prompt_template', 'Translate the following text from {src_lang} to {tgt_lang}.\n{src_lang}: {text}\n{tgt_lang}:')

            formatted_system = system_prompt.format(src_lang=curr_src, tgt_lang=curr_tgt) if system_prompt else ""
            formatted_user = user_template.format(text=self.text, src_lang=curr_src, tgt_lang=curr_tgt)

            messages = []
            if formatted_system.strip():
                messages.append({"role": "system", "content": formatted_system})
            messages.append({"role": "user", "content": formatted_user})

            # Payload construction with safe type conversion
            payload = {
                "model": self.config.get('model_name', 'default'),
                "messages": messages,
                "temperature": safe_float(self.config.get('temperature'), 0.0),
                "max_tokens": safe_int(self.config.get('max_tokens'), 512),
                "top_p": safe_float(self.config.get('top_p'), 1.0),
                "presence_penalty": safe_float(self.config.get('presence_penalty'), 0.0),
                "frequency_penalty": safe_float(self.config.get('frequency_penalty'), 0.0),
                "n": safe_int(self.config.get('n'), 1)
            }

            # Optional parameters
            stop_val = self.config.get('stop')
            if stop_val:
                payload['stop'] = stop_val

            seed_val = safe_int(self.config.get('seed'))
            if seed_val is not None:
                payload['seed'] = seed_val

            # Additional vLLM parameters passed through extra_body
            extra_body = {}
            top_k_val = safe_int(self.config.get('top_k'))
            if top_k_val is not None and top_k_val != -1:
                extra_body['top_k'] = top_k_val

            rep_pen_val = safe_float(self.config.get('repetition_penalty'), 1.0)
            if rep_pen_val != 1.0:
                extra_body['repetition_penalty'] = rep_pen_val

            ignore_eos_str = str(self.config.get('ignore_eos', 'False')).lower()
            if ignore_eos_str in ['true', '1', 'yes']:
                extra_body['ignore_eos'] = True

            if extra_body:
                payload['extra_body'] = extra_body

            response = client.chat.completions.create(**payload)
            translation = response.choices[0].message.content.strip()
            self.translation_done.emit(translation)

        except Exception as e:
            self.error_occurred.emit(f"Error connecting to vLLM server:\n{str(e)}")


class MainWindow(QMainWindow):
    def __init__(self, initial_yaml_path=None):
        super().__init__()
        self.setWindowTitle("MTUOC vLLM Test Client v. 2610")
        self.resize(650, 750)

        # Main notebook widget
        self.notebook = QTabWidget()
        self.setCentralWidget(self.notebook)

        # Form fields container
        self.fields = {}

        # --- TAB 1: SERVER & SAMPLING CONFIG ---
        self.setup_server_tab()

        # --- TAB 2: TEST ---
        self.setup_test_tab()

        # Load initial configuration if provided and valid
        if initial_yaml_path and os.path.exists(initial_yaml_path):
            self.load_yaml_file(initial_yaml_path)

    def setup_server_tab(self):
        server_widget = QWidget()
        main_layout = QVBoxLayout()

        # Top button to load a YAML file
        btn_load_yaml = QPushButton("Load YAML Config...")
        btn_load_yaml.setStyleSheet("font-weight: bold; padding: 6px;")
        btn_load_yaml.clicked.connect(self.select_yaml_file)
        main_layout.addWidget(btn_load_yaml)

        # Scrollable area for configuration parameters
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        form_layout = QFormLayout()

        # Default parameters list
        default_params = [
            ("host", "213.73.43.8"),
            ("port", "8002"),
            ("api_key", "EMPTY"),
            ("model_name", "salamandraTA"),
            ("src_lang", "English"),
            ("tgt_lang", "Catalan"),
            ("system_prompt", ""),
            ("user_prompt_template", "Translate the following text from {src_lang} to {tgt_lang}.\n{src_lang}: {text}\n{tgt_lang}:"),
            ("temperature", "0.0"),
            ("max_tokens", "512"),
            ("top_p", "1.0"),
            ("top_k", "-1"),
            ("presence_penalty", "0.0"),
            ("frequency_penalty", "0.0"),
            ("repetition_penalty", "1.0"),
            ("stop", ""),
            ("seed", ""),
            ("ignore_eos", "False")
        ]

        for key, def_val in default_params:
            if "prompt" in key:
                field = QTextEdit()
                field.setPlainText(def_val)
                field.setMaximumHeight(70)
            else:
                field = QLineEdit(def_val)
            
            self.fields[key] = field
            form_layout.addRow(QLabel(f"{key}:"), field)

        scroll_content.setLayout(form_layout)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        server_widget.setLayout(main_layout)
        self.notebook.addTab(server_widget, "vLLM Config")

    def setup_test_tab(self):
        self.test_frame = QWidget()
        test_layout = QVBoxLayout()

        test_layout.addWidget(QLabel("Source Text:"))
        self.test_text_source = QTextEdit()
        self.test_text_source.setPlaceholderText("Enter source text to translate here...")
        test_layout.addWidget(self.test_text_source)

        test_layout.addWidget(QLabel("vLLM Target Translation:"))
        self.test_text_target = QTextEdit()
        self.test_text_target.setPlaceholderText("Translation output will appear here...")
        test_layout.addWidget(self.test_text_target)

        btn_layout = QHBoxLayout()
        self.test_B_Clear = QPushButton("Clear")
        self.test_B_Clear.setFixedWidth(120)
        self.test_B_Clear.clicked.connect(self.clear_test)

        self.test_B_translate = QPushButton("Translate")
        self.test_B_translate.setFixedWidth(120)
        self.test_B_translate.setStyleSheet("font-weight: bold;")
        self.test_B_translate.clicked.connect(self.translate_test)

        btn_layout.addWidget(self.test_B_Clear)
        btn_layout.addWidget(self.test_B_translate)
        test_layout.addLayout(btn_layout)

        self.test_frame.setLayout(test_layout)
        self.notebook.addTab(self.test_frame, "TEST")

    def select_yaml_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open vLLM YAML Configuration", "", "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if file_path:
            self.load_yaml_file(file_path)

    def load_yaml_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as stream:
                config_yaml = yaml.safe_load(stream)

            vllm_config = config_yaml.get("VLLM", config_yaml)

            for key, field in self.fields.items():
                if key in vllm_config and vllm_config[key] is not None:
                    val = str(vllm_config[key])
                    if isinstance(field, QTextEdit):
                        field.setPlainText(val)
                    else:
                        field.setText(val)

            QMessageBox.information(self, "Success", f"Configuration successfully loaded from:\n{os.path.basename(file_path)}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load YAML configuration file:\n{str(e)}")

    def get_current_config(self):
        """Reads current field values from the configuration tab."""
        config = {}
        for key, field in self.fields.items():
            if isinstance(field, QTextEdit):
                val = field.toPlainText().strip()
            else:
                val = field.text().strip()
            config[key] = val
        return config

    def clear_test(self):
        self.test_text_source.clear()
        self.test_text_target.clear()

    def translate_test(self):
        sourcetext = self.test_text_source.toPlainText().strip()
        if not sourcetext:
            return

        self.test_text_target.setText("Processing translation with vLLM...")
        self.test_B_translate.setEnabled(False)

        current_config = self.get_current_config()

        # Execute translation in background thread
        self.trans_thread = TranslationThread(current_config, sourcetext)
        self.trans_thread.translation_done.connect(self.on_translation_success)
        self.trans_thread.error_occurred.connect(self.on_translation_error)
        self.trans_thread.start()

    def on_translation_success(self, translation):
        self.test_text_target.setText(translation)
        self.test_B_translate.setEnabled(True)

    def on_translation_error(self, error_message):
        self.test_text_target.clear()
        self.test_B_translate.setEnabled(True)
        QMessageBox.critical(self, "Translation Error", error_message)


if __name__ == "__main__":
    initial_yaml = sys.argv[1] if len(sys.argv) > 1 else "configVllmTranslator.yaml"

    app = QApplication(sys.argv)
    window = MainWindow(initial_yaml)
    window.show()
    sys.exit(app.exec())
