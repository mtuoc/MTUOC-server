# OllamaPosteditor.py
# Author: Antoni Oliver
# Description: Translator class using Ollama local LLMs with custom prompt templates
# License: GPLv3 or later

import ollama
import subprocess
import requests
import time
import re
import ast
import json
import sys

from MTUOC_misc import printLOG


class OllamaPosteditor:
    def __init__(self):
        self.model = None
        self.beam_size = 1
        self.sourceLanguage = None
        self.targetLanguage = None
        self.role_user = None
        self.role_system = None
        self.role_assistant = None
        self.extract_regex = None
        self.role = None
        
        self.temperature=0.9  
        self.top_p=0.9        
        self.top_k=40         
        self.repeat_penalty=1.1  
        self.seed: None
        self.num_predict=-1 
        self.json=False
        
        self.alternate_translations = []

        self.ensure_ollama_server_running()

    def ensure_ollama_server_running(self):
        try:
            response = requests.get('http://localhost:11434')
            if response.status_code == 200:
                printLOG(1,"Ollama server is already running.","")
                return
        except Exception:
            printLOG(1,"Ollama server not detected. Attempting to start...","")

        try:
            subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            printLOG(1,"Starting Ollama server...","")
            time.sleep(5)
        except Exception as e:
            printLOG(1,f"Could not start Ollama server: {e}","")

    def set_model(self, model):
        self.model = model
        try:
            printLOG(1,f"Pulling model '{self.model}' if not present...","")
            ollama.pull(self.model)
        except Exception as e:
            printLOG(1,f"Failed to pull model: {e}","")

    def set_beam_size(self, beam_size):
        self.beam_size = beam_size  # No usada però mantinguda per compatibilitat si cal
        
    def set_sourceLanguage(self, language):
        self.sourceLanguage=language
        
    def set_targetLanguage(self, language):
        self.targetLanguage=language

    def set_role_user(self, cadena):
        if '{source}' not in cadena or '{target}' not in cadena or '{source_sentence}' not in cadena or '{machine_translation}' not in cadena:
            raise ValueError("The prompt template must include the placeholders: {source}, {target}, {source_sentence}, {machine_translation}")
        self.role_user = cadena
        
    def set_role_system(self, cadena):
        self.role_system = cadena
        
    def set_role_assistant(self, cadena):
        self.role_assistant = cadena
        
    def set_extract_regex(self, extractregex):
        self.extract_regex=extractregex
        
    def set_role(self,content):
        self.role=content
        

    def extract_match(self, text: str, pattern: str) -> str:
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1) if match else text
        
    def set_temperature(self,value):
        self.temperature=value
        
    def set_top_p(self,value):
        self.top_p=value
        
    def set_top_k(self,value):
        self.top_k=value
        
    def set_repeat_penalty(self,value):
        self.repeat_penalty=value
        
    def set_seed(self,value):
        self.seed=value
        
    def set_num_predict(self,value):
        self.num_predict=value
        
    def set_json(self,value:bool):
        self.json=value
        
    def send_prompt(self,source,MT):
        messages = []
        if self.role_system:
            messages.append({"role": "system", "content": self.role_system.strip()})
        if self.role_assistant:
            messages.append({"role": "assistant", "content": self.role_assistant.strip()})
        if self.role_user:
            prompt = self.role_user.format(source=self.sourceLanguage,target=self.targetLanguage,source_sentence=source,machine_translation=MT)
            messages.append({"role": "user", "content": prompt})
        options = {
            "model": self.model,
            "messages": messages,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "repeat_penalty": self.repeat_penalty,
                "num_predict": self.num_predict
            }
        }
        try:
            options["options"]["seed"] = int(self.seed)
        except:
            pass
        try:
            response = ollama.chat(**options)
            if self.json:
                if hasattr(response, "model_dump"):
                    data = response.model_dump()
                elif hasattr(response, "dict"):
                    data = response.dict()
                else:
                    data = dict(response)
                response_text=json.dumps(data, indent=2)
            else:
                content = response['message']['content']
                response_text=content
            return(response_text)
        except Exception as e:
            printLOG(1,"Error Ollama", f"Failed to get response: {e}","")

    def postedit(self, sourcesentence, mt):
        try:
            generated_text=self.send_prompt(sourcesentence, mt)      
            
        except:
            printLOG(1,"ERROR Ollama generating text:",sys.exc_info())
        if self.extract_regex:
            postedited=self.extract_match(generated_text, self.extract_regex)
        else:
            postedited=generated_text
                
        return postedited
