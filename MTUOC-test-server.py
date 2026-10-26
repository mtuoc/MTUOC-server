#    MTUOC-test-server (PyQt6 version)
#    Copyright (C) 2026  Antoni Oliver
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

# GENERIC IMPORTS
import sys
import re
import codecs
import os

from xml.etree.ElementTree import Element, SubElement, Comment, tostring
import xml.etree.ElementTree as ET
from xml.etree import ElementTree
from xml.dom import minidom

# IMPORTS FOR PYQT6 INTERFACE
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget,
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QTextEdit, QPushButton, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from MTUOC_misc import get_IP_info
except ImportError:
    def get_IP_info():
        return "127.0.0.1"

# IMPORTS FOR YAML
import yaml
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
    
# IMPORTS FOR MTUOC CLIENT
from websocket import create_connection
import socket

# IMPORTS FOR MOSES CLIENT
import xmlrpc.client

# IMPORTS FOR OPENNMT / MODERNMT CLIENT
import requests

# ENGINE GLOBAL VARIABLES
MTEngine = "MTUOC"
urlMTUOC = ""
proxyMoses = None
urlOpenNMT = ""
urlNMTWizard = ""
urlModernMT = ""


def get_local_IP():
    try:
        host_name = socket.gethostname()
        local_ip = socket.gethostbyname(host_name)
        return local_ip
    except socket.error:
        return "127.1.1.1"


def prettify(elem):
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


class MainWindow(QMainWindow):
    def __init__(self, initial_ip, initial_port, initial_type):
        super().__init__()
        self.setWindowTitle("MTUOC Test Server v. 2610")
        self.resize(550, 450)

        # Main notebook widget
        self.notebook = QTabWidget()
        self.setCentralWidget(self.notebook)

        # --- TAB 1: SERVER INFO ---
        self.server_info_widget = QWidget()
        server_layout = QVBoxLayout()
        
        # Load YAML Button
        btn_load_yaml = QPushButton("Load YAML Config...")
        btn_load_yaml.setStyleSheet("font-weight: bold; padding: 6px;")
        btn_load_yaml.clicked.connect(self.select_yaml_file)
        server_layout.addWidget(btn_load_yaml)

        form_layout = QFormLayout()
        self.server_info_showIP_E = QLineEdit(initial_ip)
        self.server_info_showPort_E = QLineEdit(str(initial_port))
        self.server_info_showType_E = QLineEdit(str(initial_type))

        form_layout.addRow(QLabel("IP:"), self.server_info_showIP_E)
        form_layout.addRow(QLabel("Port:"), self.server_info_showPort_E)
        form_layout.addRow(QLabel("Server type:"), self.server_info_showType_E)
        
        server_layout.addLayout(form_layout)
        server_layout.addStretch()
        self.server_info_widget.setLayout(server_layout)

        # --- TAB 2: TEST ---
        self.test_frame = QWidget()
        test_layout = QVBoxLayout()

        self.test_text_source = QTextEdit()
        self.test_text_source.setPlaceholderText("Source text...")
        
        self.test_text_target = QTextEdit()
        self.test_text_target.setPlaceholderText("Translation...")

        self.test_B_Clear = QPushButton("Clear")
        self.test_B_Clear.setFixedWidth(100)
        self.test_B_Clear.clicked.connect(self.clear_test)

        self.test_B_translate = QPushButton("Translate")
        self.test_B_translate.setFixedWidth(100)
        self.test_B_translate.clicked.connect(self.translate_test)

        # Add components to TEST layout
        test_layout.addWidget(self.test_text_source)
        test_layout.addWidget(self.test_text_target)
        
        btn_layout_1 = QHBoxLayout()
        btn_layout_1.addWidget(self.test_B_Clear, alignment=Qt.AlignmentFlag.AlignCenter)
        test_layout.addLayout(btn_layout_1)

        btn_layout_2 = QHBoxLayout()
        btn_layout_2.addWidget(self.test_B_translate, alignment=Qt.AlignmentFlag.AlignCenter)
        test_layout.addLayout(btn_layout_2)

        self.test_frame.setLayout(test_layout)

        # Add tabs
        self.notebook.addTab(self.server_info_widget, "Server")
        self.notebook.addTab(self.test_frame, "TEST")

        # Select TEST tab by default
        self.notebook.setCurrentWidget(self.test_frame)

        # Initial connection
        self.connect_server()

    def select_yaml_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Server YAML Configuration", "", "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if file_path:
            self.load_yaml_config(file_path)

    def load_yaml_config(self, config_file_path):
        try:
            with open(config_file_path, 'r', encoding="utf-8") as stream:
                config_data = yaml.load(stream, Loader=Loader)
                
            server_info = config_data.get('MTUOCServer', {})
            port = server_info.get('port', '8000')
            server_type = server_info.get('type', 'MTUOC')
            ip = get_IP_info()

            self.server_info_showIP_E.setText(str(ip))
            self.server_info_showPort_E.setText(str(port))
            self.server_info_showType_E.setText(str(server_type))

            self.connect_server()
            QMessageBox.information(self, "Success", f"Configuration successfully loaded from:\n{os.path.basename(config_file_path)}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load YAML configuration:\n{str(e)}")

    def connect_server(self):
        global urlMTUOC, proxyMoses, urlOpenNMT, urlNMTWizard, urlModernMT, MTEngine
        
        server_type = self.server_info_showType_E.text().strip()
        server_IP = self.server_info_showIP_E.text().strip()
        server_Port = self.server_info_showPort_E.text().strip()
        
        MTEngine = server_type
        
        try:
            if server_type == "MTUOC":
                urlMTUOC = f"http://{server_IP}:{server_Port}/translate"
            elif server_type == "Moses":
                proxyMoses = xmlrpc.client.ServerProxy(f"http://{server_IP}:{server_Port}/RPC2")
            elif server_type == "OpenNMT":
                urlOpenNMT = f"http://{server_IP}:{server_Port}/translator/translate"
            elif server_type == "NMTWizard":
                urlNMTWizard = f"http://{server_IP}:{server_Port}/translate"
            elif server_type == "ModernMT":
                urlModernMT = f"http://{server_IP}:{server_Port}/translate"
        except Exception as e:
            errormessage = f"Error connecting to {server_type}:\n{sys.exc_info()[1]}"
            QMessageBox.information(self, "Error", errormessage)

    def clear_test(self):
        self.test_text_source.clear()
        self.test_text_target.clear()

    def translate_segment_MTUOC(self, segment, id=101, srcLang="en-US", tgtLang="es-ES"):
        import random
        global urlMTUOC
        translation = ""
        try:
            headers = {'content-type': 'application/json'}
            params = {
                "id": random.randint(0, 10000),
                "src": segment,
                "srcLang": srcLang,
                "tgtLang": tgtLang
            }
            response = requests.post(urlMTUOC, json=params, headers=headers)
            target = response.json()
            translation = target["tgt"]
        except Exception:
            errormessage = f"Error retrieving translation from MTUOC:\n{sys.exc_info()[1]}"
            QMessageBox.information(self, "Error", errormessage)
        return translation

    def translate_segment_OpenNMT(self, segment):
        global urlOpenNMT
        translation = ""
        try:
            headers = {'content-type': 'application/json'}
            params = [{"src": segment}]
            response = requests.post(urlOpenNMT, json=params, headers=headers)
            target = response.json()
            translation = target[0][0]["tgt"]
        except Exception:
            errormessage = f"Error retrieving translation from OpenNMT:\n{sys.exc_info()[1]}"
            QMessageBox.information(self, "Error", errormessage)
        return translation

    def translate_segment_NMTWizard(self, segment):
        global urlNMTWizard
        translation = ""
        try:
            headers = {'content-type': 'application/json'}
            params = {"src": [{"text": segment}]}
            response = requests.post(urlNMTWizard, json=params, headers=headers)
            target = response.json()
            translation = target["tgt"][0][0]["text"]
        except Exception:
            errormessage = f"Error retrieving translation from NMTWizard:\n{sys.exc_info()[1]}"
            QMessageBox.information(self, "Error", errormessage)
        return translation

    def translate_segment_ModernMT(self, segment):
        global urlModernMT
        translation = ""
        try:
            params = {'q': segment}
            response = requests.get(urlModernMT, params=params)
            target = response.json()
            translation = target['data']["translation"]
        except Exception:
            errormessage = f"Error retrieving translation from ModernMT:\n{sys.exc_info()[1]}"
            QMessageBox.information(self, "Error", errormessage)
        return translation

    def translate_segment_Moses(self, segment):
        global proxyMoses
        translation = ""
        try:
            param = {"text": segment}
            result = proxyMoses.translate(param)
            translation = result['text']
        except Exception:
            errormessage = f"Error retrieving translation from Moses:\n{sys.exc_info()[1]}"
            QMessageBox.information(self, "Error", errormessage)
        return translation

    def translate_segment(self, segment):
        global MTEngine
        translation = ""
        
        if MTEngine == "MTUOC":
            translation = self.translate_segment_MTUOC(segment)
        elif MTEngine == "OpenNMT":
            translation = self.translate_segment_OpenNMT(segment)
        elif MTEngine == "NMTWizard":
            translation = self.translate_segment_NMTWizard(segment)
        elif MTEngine == "ModernMT":
            translation = self.translate_segment_ModernMT(segment)
        elif MTEngine == "Moses":
            translation = self.translate_segment_Moses(segment)
            
        translation = translation.replace("\n", " ")
        return translation

    def translate_test(self):
        self.connect_server()
        sourcetext = self.test_text_source.toPlainText()
        traduccio = self.translate_segment(sourcetext)
        self.test_text_target.setText(traduccio)


# INITIAL YAML LOADING
if len(sys.argv) > 1:
    configfile = sys.argv[1]
else:
    configfile = "config-server.yaml"

server_Port = "8000"
server_IP = get_IP_info()
server_type = "MTUOC"

if os.path.exists(configfile):
    try:
        with open(configfile, 'r', encoding="utf-8") as stream:
            config = yaml.load(stream, Loader=Loader)
            server_Port = config['MTUOCServer']['port']
            server_type = config['MTUOCServer']['type']
    except Exception as e:
        print(f"ERROR reading YAML file '{configfile}': {sys.exc_info()}", file=sys.stderr)
else:
    print(f"WARNING: Configuration file '{configfile}' not found. Using default values.", file=sys.stderr)

# APPLICATION EXECUTION
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow(server_IP, server_Port, server_type)
    window.show()
    sys.exit(app.exec())
