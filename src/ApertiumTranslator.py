# apertium_translator_main.py
# ---------------------------------------------------------------------------------------
#   ApertiumTranslator v 2511 (Autonomous & Direct Config Loading)
#   Description: an MTUOC server component using Apertium python wrapper
#   Copyright (C) 2025  Antoni Oliver
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
# ---------------------------------------------------------------------------------------

import os
import codecs
from typing import Dict, Any
import apertium
import sys


class ApertiumTranslator:
    """Clase principal per a gestionar la traducció directa amb Apertium de manera autònoma."""
    
    def __init__(self, config_path: str = None):
        # Atributs bàsics inicials
        self.sl = "spa"
        self.tl = "cat"
        self.mark_unknown = True
        
        # Atribut d'identificació de model requerit pel servidor MTUOC principal
        self.model_name = "None"
        
        # Objecte de connexió amb l'enginy Apertium
        self.apertium_eng = None
        self.response = {}

        # 📄 Carreguem el fitxer de configuració YAML si s'aporta el camí
        if config_path and os.path.exists(config_path):
            self._load_config(path=config_path)
            
        # 🚀 Inicialitzem el connector d'Apertium
        self.start_translator()

    def _load_config(self, path: str):
        """Parseja el fitxer de configuració del model Apertium."""
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

        # Assignació directa de dades
        self.sl = cfg_data.get('sl', 'spa')
        self.tl = cfg_data.get('tl', 'cat')
        
        # Definim l'atribut d'identificació (el parell d'idiomes estil spa-cat)
        self.model_name = f"{self.sl}-{self.tl}"
        
        # Processament del booleà de mark_unknown
        mark = cfg_data.get('mark_unknown', 'True')
        self.mark_unknown = mark.lower() in ['true', '1', 'yes']

    def start_translator(self):
        """Inicialitza l'objecte traductor d'Apertium amb els dos idiomes per separat."""
        pair = f"{self.sl}-{self.tl}"
        print(f"START APERTIUM ENGINE (pair): {pair} | Mark Unknown: {self.mark_unknown}")
        try:
            self.apertium_eng = apertium.Translator(self.sl, self.tl)
        except Exception as e:
            print(f"ERROR: No s'ha pogut carregar el parell Apertium '{pair}'. Revisa si està instal·lat al sistema: {e}")
    def translate(self, text: str) -> Dict[str, Any]:
        # Protecció si el text arriba buit
        if not text or not text.strip():
            return {
                "system_name": "Apertium", "src_tokens": text, "tgt_tokens": "", 
                "src_subwords": text, "tgt_subwords": "", "tgt": "", 
                "alignment": "None", "alternate_translations": []
            }
            
        if self.apertium_eng is None:
            print("ERROR: El traductor d'Apertium no està inicialitzat.")
            return {}

        try:
            # Executem la traducció nativa
            translation = self.apertium_eng.translate(text)
            
            # 🧼 Si l'usuari ha demanat explicitament NO marcar els desconeguts (mark_unknown: False)
            # i el motor d'Apertium de sistema col·loca els asteriscs (*paraula), els netegem a mà:
            if not self.mark_unknown and translation:
                translation = translation.replace('*', '')
                
        except Exception as e:
            print(f"Error traduint amb Apertium: {e}")
            translation = text  # Fallback en cas d'error

        # Estructuració de la resposta per a MTUOC
        self.response = {
            "system_name": "Apertium",
            "src_tokens": text,
            "tgt_tokens": translation,
            "src_subwords": text,
            "tgt_subwords": translation,
            "tgt": translation,
            "alignment": "None",
            "alternate_translations": []
        }
        
        return self.response
