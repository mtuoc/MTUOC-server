# HFPosteditor.py
# Author: Antoni Oliver
# Description: Translator class using Ollama local LLMs with custom prompt templates
# License: GPLv3 or later

import os
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers.utils import cached_file, EntryNotFoundError
import torch

from MTUOC_misc import printLOG


class HFTranslator:
    def __init__(self):
        self.model = None
        self.sourceLanguage=None
        self.targetLanguage=None
        self.template=None
        self.device=None
        self.tokenier=None
        self.device,self.torch_dtype=self.set_device()
        
    def set_device(self):
        # Detección automática del dispositivo y tipo de precisión
        if torch.cuda.is_available():
            device = torch.device("cuda")
            capability = torch.cuda.get_device_capability()
            # Prioriza bfloat16 si está soportado (Ampere y posteriores: 8.0+)
            if capability >= (8, 0):
                torch_dtype = torch.bfloat16
            else:
                torch_dtype = torch.float16
        else:
            device = torch.device("cpu")
            torch_dtype = torch.float32
        return(device,torch_dtype)
        
    def load_model_and_tokenizer(self,model_id):
        # Detectar dispositivo y tipo de precisión
        if torch.cuda.is_available():
            device = torch.device("cuda")
            capability = torch.cuda.get_device_capability()
            torch_dtype = torch.bfloat16 if capability >= (8, 0) else torch.float16
            device_map = "auto"
        else:
            device = torch.device("cpu")
            torch_dtype = torch.float32
            device_map = None

        # Verificar si el modelo está en caché local
        try:
            _ = cached_file(model_id, "config.json")
            print(f"✅ El modelo '{model_id}' ya está descargado.")
        except EntryNotFoundError:
            print(f"⬇️ Descargando el modelo '{model_id}' de Hugging Face...")
        
        # Cargar modelo y tokenizador
        
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map=device_map,
            torch_dtype=torch_dtype
        )
        model.to(device)

        return tokenizer, model, device
                
    def set_model(self, model):        
        self.tokenizer, self.model, self.device = self.load_model_and_tokenizer(model)
        
    def set_sourceLanguage(self, language): 
        self.sourceLanguage=language
        
    def set_targetLanguage(self, language): 
        self.targetLanguage=language
        
    def set_template(self, template):
        self.template=template
        
    def translate(self, SLsegment):
        user_prompt = prompt=self.template.format(SLsegment=SLsegment)
        # Preparar mensaje y fecha
        message = [{"role": "user", "content": user_prompt}]
        date_string = datetime.today().strftime('%Y-%m-%d')

        '''
        # Tokenizador
        tokenizer = AutoTokenizer.from_pretrained(self.model)

        

        # Carga del modelo
        model = AutoModelForCausalLM.from_pretrained(
            self.model,
            device_map="auto" if torch.cuda.is_available() else None,
            torch_dtype=self.torch_dtype
        )
        self.model.to(device)
        '''
        # Construcción del prompt
        prompt = self.tokenizer.apply_chat_template(
            message,
            tokenize=False,
            add_generation_prompt=True,
            date_string=date_string
        )

        # Tokenización + attention mask
        inputs = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)
        input_length = input_ids.shape[1]

        # Generación
        outputs = self.model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=400,
            early_stopping=True,
            num_beams=5
        )

        # Decodificación del resultado
        generated_text = self.tokenizer.decode(outputs[0, input_length:], skip_special_tokens=True)
        return(generated_text)

        
    
