# marian_translator_main.py
# ---------------------------------------------------------------------------------------
#   MarianTranslator v 2511 (Autonomous & Console Flow Fixed)
#   Description: an MTUOC server component
#   Copyright (C) 2024  Antoni Oliver
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
# ---------------------------------------------------------------------------------------

import socket
import time
import sys
import os
import re
import subprocess
import platform
import codecs
from typing import List, Dict, Any


class MarianTranslator:
    """Clase principal per a gestionar la connexió i traducció directa amb Marian."""
    
    # Atribut de classe compartit per subministrar el socket a funcions externes aïllades
    _ws_shared = None
    
    def __init__(self, config_path: str = None):
        # Atributs d'identificació del model requerits per l'script de control de MTUOC
        self.model_path = "None"
        self.model = None
        self.sl_vocab = None
        self.tl_vocab = None
        self.prefix = None
        
        # Atributs de configuració i xarxa interns de la instància
        self.marian_ip = "localhost"
        self.marian_port = 8260
        self.start_marian_command = ""
        self.system_name = "Marian"
        self.ws = None
        
        # Variable de control per saber si hem d'aixecar el binari de Marian
        self.should_start_server = False
        
        self.alternate_translations = []
        self.response = {}

        # 📄 Carreguem i processem el fitxer de configuració del model
        if config_path and os.path.exists(config_path):
            self._load_config(path=config_path)
            
        # 🚀 Arrancada automatitzada del servidor en segon pla si s'ha activat al YAML
        if self.should_start_server:
            self.start_marian_server()

    def _load_config(self, path: str):
        """Parseja el fitxer de configuració d'acord amb el Sistema Operatiu actiu."""
        cfg_data = {}
        try:
            with codecs.open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"): continue
                    if ":" in line:
                        k, v = line.split(":", 1)
                        cfg_data[k.strip()] = v.strip().strip('"').strip("'")
        except Exception as e:
            print(f"Error llegint el fitxer de configuració {path}: {e}")
            return

        # 1. Determinar el Sistema Operatiu i triar la comanda de l'arxiu YAML
        current_os = platform.system()
        if current_os == "Windows":
            self.start_marian_command = cfg_data.get('startMarianCommandWindows', '')
        elif current_os == "Darwin":  # Mac
            self.start_marian_command = cfg_data.get('startMarianCommandMac', '')
        else:  # Linux o altres
            self.start_marian_command = cfg_data.get('startMarianCommand', '')

        # Fallback de seguretat si la comanda de l'OS no Birds eye està definida
        if not self.start_marian_command:
            self.start_marian_command = cfg_data.get('startMarianCommand', '')

        # 2. Extreure la ruta real del model (-m) i vocabularis (-v) de la comanda triada
        match = re.search(r'-m\s+([^\s]+)', self.start_marian_command)
        if match:
            self.model_path = match.group(1)
            self.model = self.model_path

        match_v = re.findall(r'-v\s+([^\s]+)\s+([^\s]+)', self.start_marian_command)
        if match_v:
            self.sl_vocab = match_v[0][0]
            self.tl_vocab = match_v[0][1]

        if cfg_data.get('prefix'):
            self.prefix = cfg_data.get('prefix')

        # 3. Guardar IPs, Ports, dades del sistema i estat d'arrencada
        self.marian_ip = cfg_data.get('IP', 'localhost')
        self.marian_port = int(cfg_data.get('port', 8260))
        self.system_name = cfg_data.get('system_name', 'Marian')
        
        if 'startMarianServer' in cfg_data:
            self.should_start_server = cfg_data['startMarianServer'].lower() in ['true', '1', 'yes']

    def lreplace(self, pattern, sub, string):
        """Reemplaça 'pattern' si comença 'string'."""
        return re.sub('^%s' % pattern, sub, string)

    def rreplace(self, pattern, sub, string):
        """Reemplaça 'pattern' si acaba 'string'."""
        return re.sub('%s$' % pattern, sub, string)

    def start_marian_server(self):
        """Executa el binari de marian-server en el sistema operatiu."""
        print("START MT ENGINE:", self.start_marian_command)
        if not self.start_marian_command:
            print("ERROR: start_marian_command està buit.")
            return
            
        if platform.system() == "Windows":
            subprocess.Popen(self.start_marian_command) 
        else:
            os.system(self.start_marian_command)

    def connect_to_Marian(self):
        """Gestiona el bucle d'espera invisible i mostra la IP/Port només quan connecta."""
        from websocket import create_connection
        
        # Intent de connexió raw inicial silenciós
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect_ex((self.marian_ip, self.marian_port))
            
        service = f"ws://{self.marian_ip}:{self.marian_port}/translate"
        
        # Missatge elegant inicial mentre s'espera
        print("Waiting for Marian server to initialize components...", end="", flush=True)
        
        error = True
        while error:
            try:
                self.ws = create_connection(service)
                MarianTranslator._ws_shared = self.ws
                error = False
                
                # 🌟 EL CANVI ÉS AQUÍ: Passem a la línia següent i mostrem l'èxit amb les dades reals
                print("\n" + "="*60)
                print(f"SERVER STATUS: Marian server has started successfully!")
                print(f"CONNECTED TO : {service}")
                print("="*60)
                
            except:
                # Si falla, imprimim un puntet d'espera per indicar que segueix viu sense omplir la pantalla de text
                print(".", end="", flush=True)
                time.sleep(2)
                error = True
               
    def translate(self, text):
        """Envia text al motor i retorna les respostes alternatives directes de Marian."""
        self.alternate_translations = []
        
        try:
            # Recuperació automàtica: si es crida a traduir sense haver connectat, ho fem aquí
            if self.ws is None:
                self.connect_to_Marian()
            self.ws.send(text)
        except Exception as e:
            print("Error sending segment to Marian a translate().", sys.exc_info()[1])
            return {
                "system_name": self.system_name, "src_tokens": text, "tgt_tokens": "", 
                "src_subwords": text, "tgt_subwords": "", "tgt": "", 
                "alignment": "", "alternate_translations": []
            }
            
        try:
            translations = self.ws.recv()
        except Exception as e:
            print("Error receiving from Marian a translate().", sys.exc_info()[1])
            return {
                "system_name": self.system_name, "src_tokens": text, "tgt_tokens": "", 
                "src_subwords": text, "tgt_subwords": "", "tgt": "", 
                "alignment": "", "alternate_translations": []
            }
        
        # Separació i processament de les n-best candidates retornades per Marian
        tc_aux = translations.split("\n")
        for i in range(0, len(tc_aux)):
            if not tc_aux[i].strip(): continue 

            parts = tc_aux[i].split(" ||| ")
            if len(parts) < 3: continue
            
            segmentaux = parts[1].strip()
            alignmentaux = parts[2].strip()

            if segmentaux.startswith("<s> "):
                segmentaux = self.lreplace("<s> ", "", segmentaux)
            if segmentaux.endswith("</s>"):
                segmentaux = self.rreplace("</s>", "", segmentaux)   
                
            alternate_translation = {
                "tgt_tokens": segmentaux,
                "tgt_subwords": segmentaux,
                "alignment": alignmentaux,
                "tgt": segmentaux
            }
            self.alternate_translations.append(alternate_translation)

        # Resposta final estructurada per al servidor pare de MTUOC
        self.response = {}
        if self.alternate_translations:
            best_translation = self.alternate_translations[0]
            self.response["system_name"] = self.system_name
            self.response["src_tokens"] = text
            self.response["tgt_tokens"] = best_translation["tgt_tokens"]
            self.response["src_subwords"] = text
            self.response["tgt_subwords"] = best_translation["tgt_tokens"]
            self.response["tgt"] = best_translation["tgt"]
            self.response["alignment"] = best_translation["alignment"]
            self.response["alternate_translations"] = self.alternate_translations
        else:
            self.response["system_name"] = self.system_name
            self.response["src_tokens"] = text
            self.response["tgt_tokens"] = ""
            self.response["src_subwords"] = text
            self.response["tgt_subwords"] = ""
            self.response["tgt"] = ""
            self.response["alignment"] = ""
            self.response["alternate_translations"] = []
            
        return self.response


def translate_segment_Marian(segmentPre):
    """Funció de retrocompatibilitat que utilitza la connexió creada per la instància class."""
    try:
        if MarianTranslator._ws_shared is None:
            return {"src_tokens": segmentPre, "tgt_tokens": "", "tgt": "", "alignments": "", "alternate_translations": []}
        MarianTranslator._ws_shared.send(segmentPre)
    except Exception as e:
        return {"src_tokens": segmentPre, "tgt_tokens": "", "tgt": "", "alignments": "", "alternate_translations": []}
        
    alternate_translations = []
    try:
        translations = MarianTranslator._ws_shared.recv()
    except Exception as e:
        return {"src_tokens": segmentPre, "tgt_tokens": "", "tgt": "", "alignments": "", "alternate_translations": []}
        
    tc_aux = translations.split("\n")
    for i in range(0, len(tc_aux)):
        if not tc_aux[i].strip(): continue
        parts = tc_aux[i].split(" ||| ")
        if len(parts) < 3: continue
        
        segmentaux = parts[1].strip()
        alignmentaux = parts[2].strip()
        
        alternate_translation = {
            "tgt_tokens": segmentaux,
            "alignments": alignmentaux,
            "tgt": segmentaux
        }
        alternate_translations.append(alternate_translation)

    response = {"src_tokens": segmentPre}
    if alternate_translations:
        response["tgt_tokens"] = alternate_translations[0]["tgt_tokens"]
        response["tgt"] = alternate_translations[0]["tgt"]
        response["alignments"] = alternate_translations[0]["alignments"]
        response["alternate_translations"] = alternate_translations
    else:
        response["tgt_tokens"] = ""
        response["tgt"] = ""
        response["alignments"] = ""
        response["alternate_translations"] = []
        
    return response
