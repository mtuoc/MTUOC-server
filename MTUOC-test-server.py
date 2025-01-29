#    MTUOC-test-server
#    Copyright (C) 2025  Antoni Oliver
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
from tkinter import ttk
import tkinter.scrolledtext as scrolledtext


import srx_segmenter


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

import socket

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
    server_type=server_info_showType_E.get()
    server_IP=server_info_showIP_E.get()
    server_Port=server_info_showPort_E.get()
    if server_type=="MTUOC":
        try:
            global urlMTUOC
            urlMTUOC = "http://"+server_IP.strip()+":"+str(server_Port)+"/translate"
        except:
            errormessage="Error connecting to MTUOC: \n"+ str(sys.exc_info()[1])
            messagebox.showinfo("Error", errormessage) 
            
            
    elif server_type=="Moses":
        try:
            global proxyMoses
            proxyMoses = xmlrpc.client.ServerProxy("http://"+connecto_E_Server.get().strip()+":"+str(connecto_E_Port.get())+"/RPC2")
        except:
            errormessage="Error connecting to Moses: \n"+ str(sys.exc_info()[1])
            messagebox.showinfo("Error", errormessage)      
            
    elif server_type=="OpenNMT":
        try:
            global urlOpenNMT
            urlOpenNMT = "http://"+server_IP.strip()+":"+str(server_Port)+"/translator/translate"
        except:
            errormessage="Error connecting to OpenNMT: \n"+ str(sys.exc_info()[1])
            messagebox.showinfo("Error", errormessage)   
    elif server_type=="NMTWizard":
        try:
            global urlNMTWizard
            urlNMTWizard = "http://"+server_IP.strip()+":"+str(server_Port)+"/translate"
        except:
            errormessage="Error connecting to NMTWizard: \n"+ str(sys.exc_info()[1])
            messagebox.showinfo("Error", errormessage)           
    elif server_type=="ModernMT":
        try:
            global urlModernMT
            urlModernMT = "http://"+server_IP.strip()+":"+str(server_Port)+"/translate"
        except:
            errormessage="Error connecting to ModernMT: \n"+ str(sys.exc_info()[1])
            messagebox.showinfo("Error", errormessage)
            
   
   
def clear_test():
    test_text_source.delete(1.0,END)
    test_text_target.delete(1.0,END)


def translate_segment_MTUOC(segment,id=101,srcLang="en-US",tgtLang="es-ES",):
    import random
    global urlMTUOC
    translation=""
    try:
        headers = {'content-type': 'application/json'}
        #params = [{ "id" : id},{ "src" : segment},{ "srcLang" : srcLang},{"tgtLang" : tgtLang}]
        params={}
        params["id"]=random.randint(0, 10000)
        params["src"]=segment
        params["srcLang"]=srcLang
        params["tgtLang"]=tgtLang
        response = requests.post(urlMTUOC, json=params, headers=headers)
        
        target = response.json()
        translation=target["tgt"]
    except:
        errormessage="Error retrieving translation from MTUOC: \n"+ str(sys.exc_info()[1])
        messagebox.showinfo("Error", errormessage)
    return(translation)
    
def translate_segment_OpenNMT(segment):
    global urlOpenNMT
    translation=""
    try:
        headers = {'content-type': 'application/json'}
        params = [{ "src" : segment}]
        response = requests.post(urlOpenNMT, json=params, headers=headers)
        target = response.json()
        translation=target[0][0]["tgt"]
    except:
        errormessage="Error retrieving translation from OpenNMT: \n"+ str(sys.exc_info()[1])
        messagebox.showinfo("Error", errormessage)
    return(translation)

    
def translate_segment_NMTWizard(segment):
    global urlNMTWizard
    translation=""
    try:
        headers = {'content-type': 'application/json'}
        params={ "src": [  {"text": segment}]}
        response = requests.post(urlNMTWizard, json=params, headers=headers)
        target = response.json()
        translation=target["tgt"][0][0]["text"]
    except:
        errormessage="Error retrieving translation from NMTWizard: \n"+ str(sys.exc_info()[1])
        messagebox.showinfo("Error", errormessage)
    return(translation)
    
def translate_segment_ModernMT(segment):
    global urlModernMT
    params={}
    params['q']=segment
    response = requests.get(urlModernMT,params=params)
    target = response.json()
    translation=target['data']["translation"]
    return(translation)
        
def translate_segment_Moses(segment):

    translation=""
    try:
        param = {"text": segment}
        result = proxyMoses.translate(param)
        translation=result['text']
    except:
        errormessage="Error retrieving translation from Moses: \n"+ str(sys.exc_info()[1])
        messagebox.showinfo("Error", errormessage)
    return(translation)
    
def translate_segment(segment):
    MTEngine=server_type
    if MTEngine=="MTUOC":
        translation=translate_segment_MTUOC(segment)
    elif MTEngine=="OpenNMT":
        translation=translate_segment_OpenNMT(segment)
    elif MTEngine=="NMTWizard":
        translation=translate_segment_NMTWizard(segment)
    elif MTEngine=="ModernMT":
        translation=translate_segment_ModernMT(segment)
    elif MTEngine=="Moses":
        translation=translate_segment_Moses(segment)
    translation=translation.replace("\n"," ")
    return(translation)


def translate_test():
    connect()
    sourcetext=test_text_source.get("1.0",END)
    traduccio=translate_segment(sourcetext)
    test_text_target.delete(1.0,END)
    test_text_target.insert(1.0,traduccio)

#YAML 


try:
    stream = open('config-server.yaml', 'r',encoding="utf-8")
    config=yaml.load(stream,Loader=Loader)
    server_Port=config['Server']['port']
    server_IP=config['Server']['ip']
    server_type=config['Server']['type']
except:
    server_Port="8000"
    server_IP=get_local_IP()
    server_type="MTUOC"
    

###GRAPHICAL INTERFACE
main_window = Tk()
main_window.title("MTUOC test server v 0.1")



notebook = ttk.Notebook(main_window)

#TEST
test_frame = Frame(notebook)
test_text_source=scrolledtext.ScrolledText(test_frame,height=5)
test_text_target=scrolledtext.ScrolledText(test_frame,height=5)
test_text_source.grid(row=0,column=0)
test_text_target.grid(row=1,column=0)
test_B_Clear=Button(test_frame, text = str("Clear"), command=clear_test,width=10)
test_B_Clear.grid(row=2,column=0)
test_B_translate=Button(test_frame, text = str("Translate"), command=translate_test,width=10)
test_B_translate.grid(row=3,column=0)

#SERVER INFO
server_info = Frame(notebook)

server_info_showIP_L = Label(server_info, text="IP:")
server_info_showIP_L.grid(row=0,column=0, sticky='E')
server_info_showIP_E = Entry(server_info, width=20)
server_info_showIP_E.grid(row=0,column=1)

server_info_showPort_L = Label(server_info, text="Port:")
server_info_showPort_L.grid(row=1,column=0, sticky='E')
server_info_showPort_E = Entry(server_info, width=20)
server_info_showPort_E.grid(row=1,column=1)

server_info_showType_L = Label(server_info, text="Server type:")
server_info_showType_L.grid(row=2,column=0, sticky='E')
server_info_showType_E = Entry(server_info, width=20)
server_info_showType_E.grid(row=2,column=1)

server_info_showIP_E.insert(0,server_IP)
server_info_showPort_E.insert(0,server_Port)
server_info_showType_E.insert(0,server_type)



'''
#TEXT
text_frame = Frame(notebook)
text_frame_B_source=Button(text_frame, text = str("Select source file"), command=open_source_text_file,width=15)
text_frame_B_source.grid(row=0,column=0)
text_frame_E_source = Entry(text_frame,  width=50)
text_frame_E_source.grid(row=0,column=1)
text_frame_B_target=Button(text_frame, text = str("Select target file"), command=open_target_text_file,width=15)
text_frame_B_target.grid(row=1,column=0)
text_frame_E_target = Entry(text_frame,  width=50)
text_frame_E_target.grid(row=1,column=1)
text_frame_Check_TMX = ttk.Checkbutton(text_frame, text="Export TMX")
text_frame_Check_TMX.grid(row=2,column=0)
text_frame_B_TMX=Button(text_frame, text = str("Select TMX file"), command=open_TMX_file,width=15)
text_frame_B_TMX.grid(row=3,column=0)
text_frame_E_TMX = Entry(text_frame,  width=50)
text_frame_E_TMX.grid(row=3,column=1)
text_frame_B_translate=Button(text_frame, text = str("Translate"), command=translate_text_file,width=15)
text_frame_B_translate.grid(row=4,column=0)


#XLIFF
xliff_frame = Frame(notebook)
xliff_frame_B_source=Button(xliff_frame, text = str("Select source file"), command=open_source_xliff_file,width=15)
xliff_frame_B_source.grid(row=0,column=0)
xliff_frame_E_source = Entry(xliff_frame,  width=50)
xliff_frame_E_source.grid(row=0,column=1)
xliff_frame_B_target=Button(xliff_frame, text = str("Select target file"), command=open_target_xliff_file,width=15)
xliff_frame_B_target.grid(row=1,column=0)
xliff_frame_E_target = Entry(xliff_frame,  width=50)
xliff_frame_E_target.grid(row=1,column=1)
xliff_frame_Check_TMX = ttk.Checkbutton(xliff_frame, text="Export TMX")
xliff_frame_Check_TMX.grid(row=2,column=0)
xliff_frame_B_TMX=Button(xliff_frame, text = str("Select TMX file"), command=open_TMX_file,width=15)
xliff_frame_B_TMX.grid(row=3,column=0)
xliff_frame_E_TMX = Entry(xliff_frame,  width=50)
xliff_frame_E_TMX.grid(row=3,column=1)
xliff_frame_B_translate=Button(xliff_frame, text = str("Translate"), command=translate_xliff_file,width=15)
xliff_frame_B_translate.grid(row=4,column=0)
'''
#notebook.add(connecto_frame, text="Connect to", padding=30)
server_info
notebook.add(server_info, text="Server", padding=30)
notebook.add(test_frame, text="TEST", padding=30)
#notebook.add(text_frame, text="TEXT FILE", padding=30)
#notebook.add(xliff_frame, text="XLIFF",padding=30)



notebook.pack()
notebook.pack_propagate(0) #Don't allow the widgets inside to determine the frame's width / height
notebook.pack(fill=BOTH, expand=1)

notebook.select(test_frame)
connect()
main_window.mainloop()
