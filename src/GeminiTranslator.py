# -*- coding: utf-8 -*-
import os
import sys
import requests
import json
import yaml

class GeminiTranslator:
    
    def __init__(self, config_path="config-GeminiTranslator.yaml"):
        self.api_key = None
        self.alternate_translations = []
        
        self.config = self.load_config(config_path)
        
        self.model_name = "gemini-2.5-flash"
        self.generation_config = {}
        self.jsonfile = None
        
        if self.config:
            g_cfg = self.config.get('Gemini', self.config)
            
            if 'model_name' in g_cfg and str(g_cfg['model_name']).strip().lower() != "none":
                self.model_name = str(g_cfg['model_name']).strip()
                
            self.jsonfile = g_cfg.get('jsonfile', None)
            
            try:
                if 'temperature' in g_cfg and g_cfg['temperature'] is not None:
                    self.generation_config["temperature"] = float(g_cfg['temperature'])
                if 'max_output_tokens' in g_cfg and g_cfg['max_output_tokens'] is not None:
                    self.generation_config["maxOutputTokens"] = int(g_cfg['max_output_tokens'])
                if 'top_p' in g_cfg and g_cfg['top_p'] is not None:
                    self.generation_config["topP"] = float(g_cfg['top_p'])
                if 'top_k' in g_cfg and g_cfg['top_k'] is not None:
                    self.generation_config["topK"] = int(g_cfg['top_k'])
            except (ValueError, TypeError) as e:
                print(f"[DEBUG CONFIG] Error parsejant paràmetres numèrics del YAML: {e}")

    def load_config(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"ERROR obrint el fitxer de configuració {path}: {e}")
            return None

    def _load_api_key(self):
        if self.api_key:
            return
        
        self.api_key = os.environ.get("GEMINI_API_KEY")
        
        if self.jsonfile and os.path.exists(self.jsonfile):
            try:
                with open(self.jsonfile, "r", encoding="utf-8") as f:
                    contingut = f.read().strip()
                    if contingut.startswith("{"):
                        js_data = json.loads(contingut)
                        self.api_key = js_data.get("api_key", js_data.get("private_key", self.api_key))
                    else:
                        self.api_key = contingut
            except Exception as e:
                print(f"[DEBUG KEY] Error llegint el fitxer de clau {self.jsonfile}: {e}")

        if not self.api_key:
            print("GeminiTranslator ERROR: No s'ha trobat la clau API.")
            raise ValueError("Falta la GEMINI_API_KEY per poder utilitzar GeminiTranslator.")

    def translate_text(self, full_prompt):
        try:
            self._load_api_key()
            
            model = self.model_name
            if not model.startswith("models/"):
                model = f"models/{model}"
                
            url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": str(full_prompt)}]
                }],
                "generationConfig": self.generation_config
            }
            
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            
            if response.status_code == 200:
                res_json = response.json()
                translation = res_json['candidates'][0]['content']['parts'][0]['text']
                return translation.strip()
            else:
                print(f"[DEBUG ERROR] Resposta de Google: {response.text}")
                return full_prompt
                
        except Exception as e:
            print(f"[EXCEPCIÓ EN TRANSLATE_TEXT]: {e}")
            import traceback
            traceback.print_exc()
            return full_prompt

    def translate(self, SLsegment):
        
        p_cfg = self.config.get("prompt_settings", {})
        template = p_cfg.get("template", "{SLsegment}")
        
        prompt_content = template.format(SLsegment=SLsegment)
        
        translation = self.translate_text(prompt_content)
        response_data = {
            "src_tokens": SLsegment,
            "tgt_tokens": translation,
            "src_subwords": SLsegment,
            "tgt_subwords": translation,
            "tgt": translation,
            "alignment": "",
            "alternate_translations": self.alternate_translations
        }
        
        return response_data
