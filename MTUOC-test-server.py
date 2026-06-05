#    MTUOC-test-server
#    Copyright (C) 2026  Antoni Oliver
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

#GENERIC IMPORTS
import sys
import re
import codecs
import os

from xml.etree.ElementTree import Element, SubElement, Comment, tostring
import xml.etree.ElementTree as ET
from xml.etree import ElementTree
from xml.dom import minidom

#IMPORTS FOR GRAPHICAL INTERFACE
from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter import messagebox
import tkinter.scrolledtext as scrolledtext

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from MTUOC_misc import get_IP_info

#IMPORTS FOR YAML
import yaml
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
    
#IMPORTS FOR MTUOC CLIENT
from websocket import create_connection
import socket

#IMPORTS FOR MOSES CLIENT
import xmlrpc.client

#IMPORTS FOR OPENNMT / MODERNMT CLIENT
import requests

# VARIABLES GLOBALS DELS MOTORS
MTEngine = "MTUOC"
urlMTUOC = ""
proxyMoses = None
urlOpenNMT = ""
urlNMTWizard = ""
urlModernMT = ""

def get_local_IP():
    try:
        # Obtiene el nombre del host local
        nombre_host = socket.gethostname()
        # Resuelve la dirección IP del host
        ip_local = socket.gethostbyname(nombre_host)
        return ip_local
    except socket.error as e:
        return "127.1.1.1"

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def connect():
    global urlMTUOC, proxyMoses, urlOpenNMT, urlNMTWizard, urlModernMT, MTEngine
    
    # Llegim directament els valors actuals de les caixes de text de la interfície
    server_type = server_info_showType_E.get().strip()
    server_IP = server_info_showIP_E.get().strip()
    server_Port = server_info_showPort_E.get().strip()
    
    # Actualitzem el motor de traducció global actiu
    MTEngine = server_type
    
    if server_type == "MTUOC":
        try:
            urlMTUOC = "http://" + server_IP + ":" + str(server_Port) + "/translate"
        except:
            errormessage = "Error connecting to MTUOC: \n" + str(sys.exc_info()[1])
            messagebox.showinfo("Error", errormessage) 
            
    elif server_type == "Moses":
        try:
            proxyMoses = xmlrpc.client.ServerProxy("http://" + server_IP + ":" + str(server_Port) + "/RPC2")
        except:
            errormessage = "Error connecting to Moses: \n" + str(sys.exc_info()[1])
            messagebox.showinfo("Error", errormessage)      
            
    elif server_type == "OpenNMT":
        try:
            urlOpenNMT = "http://" + server_IP + ":" + str(server_Port) + "/translator/translate"
        except:
            errormessage = "Error connecting to OpenNMT: \n" + str(sys.exc_info()[1])
            messagebox.showinfo("Error", errormessage)   
            
    elif server_type == "NMTWizard":
        try:
            urlNMTWizard = "http://" + server_IP + ":" + str(server_Port) + "/translate"
        except:
            errormessage = "Error connecting to NMTWizard: \n" + str(sys.exc_info()[1])
            messagebox.showinfo("Error", errormessage)           
            
    elif server_type == "ModernMT":
        try:
            urlModernMT = "http://" + server_IP + ":" + str(server_Port) + "/translate"
        except:
            errormessage = "Error connecting to ModernMT: \n" + str(sys.exc_info()[1])
            messagebox.showinfo("Error", errormessage)
            
   
def clear_test():
    test_text_source.delete(1.0, END)
    test_text_target.delete(1.0, END)


def translate_segment_MTUOC(segment, id=101, srcLang="en-US", tgtLang="es-ES"):
    import random
    global urlMTUOC
    translation = ""
    try:
        headers = {'content-type': 'application/json'}
        params = {}
        params["id"] = random.randint(0, 10000)
        params["src"] = segment
        params["srcLang"] = srcLang
        params["tgtLang"] = tgtLang
        response = requests.post(urlMTUOC, json=params, headers=headers)
        
        target = response.json()
        translation = target["tgt"]
    except:
        errormessage = "Error retrieving translation from MTUOC: \n" + str(sys.exc_info()[1])
        messagebox.showinfo("Error", errormessage)
    return translation
    
def translate_segment_OpenNMT(segment):
    global urlOpenNMT
    translation = ""
    try:
        headers = {'content-type': 'application/json'}
        params = [{ "src" : segment}]
        response = requests.post(urlOpenNMT, json=params, headers=headers)
        target = response.json()
        translation = target[0][0]["tgt"]
    except:
        errormessage = "Error retrieving translation from OpenNMT: \n" + str(sys.exc_info()[1])
        messagebox.showinfo("Error", errormessage)
    return translation

    
def translate_segment_NMTWizard(segment):
    global urlNMTWizard
    translation = ""
    try:
        headers = {'content-type': 'application/json'}
        params = { "src": [  {"text": segment}]}
        response = requests.post(urlNMTWizard, json=params, headers=headers)
        target = response.json()
        translation = target["tgt"][0][0]["text"]
    except:
        errormessage = "Error retrieving translation from NMTWizard: \n" + str(sys.exc_info()[1])
        messagebox.showinfo("Error", errormessage)
    return translation
    
def translate_segment_ModernMT(segment):
    global urlModernMT
    translation = ""
    try:
        params = {}
        params['q'] = segment
        response = requests.get(urlModernMT, params=params)
        target = response.json()
        translation = target['data']["translation"]
    except:
        errormessage = "Error retrieving translation from ModernMT: \n" + str(sys.exc_info()[1])
        messagebox.showinfo("Error", errormessage)
    return translation
        
def translate_segment_Moses(segment):
    global proxyMoses
    translation = ""
    try:
        param = {"text": segment}
        result = proxyMoses.translate(param)
        translation = result['text']
    except:
        errormessage = "Error retrieving translation from Moses: \n" + str(sys.exc_info()[1])
        messagebox.showinfo("Error", errormessage)
    return translation
    
def translate_segment(segment):
    global MTEngine
    translation = ""
    
    if MTEngine == "MTUOC":
        translation = translate_segment_MTUOC(segment)
    elif MTEngine == "OpenNMT":
        translation = translate_segment_OpenNMT(segment)
    elif MTEngine == "NMTWizard":
        translation = translate_segment_NMTWizard(segment)
    elif MTEngine == "ModernMT":
        translation = translate_segment_ModernMT(segment)
    elif MTEngine == "Moses":
        translation = translate_segment_Moses(segment)
        
    translation = translation.replace("\n", " ")
    return translation


def translate_test():
    # Primer forcem la reconexió/actualització llegint els de la pestanya "Server"
    connect()
    sourcetext = test_text_source.get("1.0", END)
    traduccio = translate_segment(sourcetext)
    test_text_target.delete(1.0, END)
    test_text_target.insert(1.0, traduccio)


#YAML 
if len(sys.argv) > 1:
    configfile = sys.argv[1]
else:
    configfile = "config-server.yaml"

# 1. Comprovar si el fitxer existeix
if not os.path.exists(configfile):
    print(
        f"ERROR: configuration file '{configfile}' does not exist.",
        file=sys.stderr,
    )
    sys.exit(1)

# 2. Si existeix, intentem llegir-lo de forma segura
try:
    with open(configfile, "r", encoding="utf-8") as stream:
        configYAML = yaml.full_load(stream)
except yaml.YAMLError as exc:
    print(
        f"Format error in YAML file: {exc}", file=sys.stderr
    )
    sys.exit(1)
except Exception as e:
    print(
        f"Unexpected error opening file: {e}", file=sys.stderr
    )
    sys.exit(1)


try:
    stream = open(configfile, 'r', encoding="utf-8")
    config = yaml.load(stream, Loader=Loader)
    server_Port = config['MTUOCServer']['port']
    server_IP = get_IP_info()
    server_type = config['MTUOCServer']['type']
except:
    print("ERROR", sys.exc_info())
    server_Port = "8000"
    server_IP = get_IP_info()
    server_type = "MTUOC"
    

###GRAPHICAL INTERFACE
main_window = Tk()
main_window.title("MTUOC test server v. 2504")

notebook = ttk.Notebook(main_window)

#TEST
test_frame = Frame(notebook)
test_text_source = scrolledtext.ScrolledText(test_frame, height=5)
test_text_target = scrolledtext.ScrolledText(test_frame, height=5)
test_text_source.grid(row=0, column=0)
test_text_target.grid(row=1, column=0)
test_B_Clear = Button(test_frame, text="Clear", command=clear_test, width=10)
test_B_Clear.grid(row=2, column=0)
test_B_translate = Button(test_frame, text="Translate", command=translate_test, width=10)
test_B_translate.grid(row=3, column=0)

#SERVER INFO
server_info = Frame(notebook)

server_info_showIP_L = Label(server_info, text="IP:")
server_info_showIP_L.grid(row=0, column=0, sticky='E')
server_info_showIP_E = Entry(server_info, width=20)
server_info_showIP_E.grid(row=0, column=1)

server_info_showPort_L = Label(server_info, text="Port:")
server_info_showPort_L.grid(row=1, column=0, sticky='E')
server_info_showPort_E = Entry(server_info, width=20)
server_info_showPort_E.grid(row=1, column=1)

server_info_showType_L = Label(server_info, text="Server type:")
server_info_showType_L.grid(row=2, column=0, sticky='E')
server_info_showType_E = Entry(server_info, width=20)
server_info_showType_E.grid(row=2, column=1)

server_info_showIP_E.insert(0, server_IP)
server_info_showPort_E.insert(0, server_Port)
server_info_showType_E.insert(0, server_type)


notebook.add(server_info, text="Server", padding=30)
notebook.add(test_frame, text="TEST", padding=30)

notebook.pack()
notebook.pack_propagate(0) 
notebook.pack(fill=BOTH, expand=1)

notebook.select(test_frame)

# Connexió inicial amb les dades del YAML/defecte carregades als inputs
connect()

main_window.mainloop()
