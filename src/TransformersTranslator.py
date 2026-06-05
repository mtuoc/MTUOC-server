#    TransformersTranslator v 2409 (GPU Optimized)
#    Description: an MTUOC server using Sentence Piece as preprocessing step
#    Copyright (C) 2024  Antoni Oliver
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.


import yaml
import torch
from transformers import MarianMTModel, MarianTokenizer

class TransformersTranslator:
    def __init__(self, config_path=None):
        self.model = None
        self.tokenizer = None
        
        # Valors per defecte si no es passa config_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.beam_size = 1
        self.num_hypotheses = 1
        self.multilingual = ""
        self.model_path = None
        
        self.alternate_translations = []
        
        print(f"INFO: TransformersTranslator started (Auto-device: {self.device})")
        
        # Si ens passen la ruta del config, la processem automàticament
        if config_path:
            self.load_from_config(config_path)

    def load_from_config(self, config_path):
        """Llegeix el fitxer YAML i configura tots els paràmetres de cop."""
        try:
            print("Loading config inside class: ", config_path)
            with open(config_path, 'r', encoding="utf-8") as stream:
                config_yaml = yaml.load(stream, Loader=yaml.FullLoader)
            
            # Extraiem les variables de la secció "OpusMT"
            opus_config = config_yaml.get("OpusMT", {})
            
            self.model_path = opus_config.get("model_path", "./opus-mt-en-es")
            self.beam_size = opus_config.get("beam_size", 5)
            self.num_hypotheses = opus_config.get("num_hypotheses", 5)
            self.multilingual = opus_config.get("multilingual_prefix", "")
            
            # Configurem el dispositiu segons el fitxer (guardant compatibilitat amb l'auto-detect)
            device_type = opus_config.get("device", "cuda")
            self.set_device(device_type)
            
            # Carreguem el model amb la ruta obtinguda
            self.set_model(self.model_path)
            
        except Exception as e:
            print(f"ERROR: No s'ha pogut carregar la configuració des de {config_path}. Error: {e}")

    def set_device(self, device_type):
        """Permet establir o canviar el dispositiu (cuda/cpu)."""
        if device_type == "cuda" and not torch.cuda.is_available():
            print("WARNING: CUDA no disponible. Es manté el dispositiu actual (CPU).")
            self.device = torch.device("cpu")
            return

        self.device = torch.device(device_type)
        
        if self.model is not None:
            self.model.to(self.device)
            print(f"INFO: Model moved to {self.device}")
        else:
            print(f"INFO: Device changed to {self.device} (the model will be loaded here)")

    def set_model(self, model_path):
        """Carrega el model i el tokenizer a la memòria."""
        self.model = MarianMTModel.from_pretrained(model_path)
        self.tokenizer = MarianTokenizer.from_pretrained(model_path)
        self.model.to(self.device)
         
    def set_beam_size(self, beam_size):
        self.beam_size = beam_size
        
    def set_num_hypotheses(self, num_hypotheses):
        self.num_hypotheses = num_hypotheses
        
    def clean(self, llista):
        self.llista = llista
        for item in ["<s>", "</s>", "<pad>"]:
            c = self.llista.count(item) 
            for i in range(c): 
                self.llista.remove(item) 
        return self.llista
        
    def translate(self, text, max_length=128):
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model not loaded. Call set_model() or init with a valid config_path first.")

        inputs = self.tokenizer(text, return_tensors="pt", max_length=max_length, truncation=True).to(self.device)
        src_subword_units = self.tokenizer.tokenize(text) 
        
        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                num_beams=self.beam_size,
                num_return_sequences=self.num_hypotheses,
                early_stopping=True
            )
        
        translated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
        tgt_subword_units = self.tokenizer.convert_ids_to_tokens(output[0]) 
        
        self.response = {
            "src_tokens": " ".join(src_subword_units),
            "tgt_tokens": " ".join(tgt_subword_units),
            "src_subwords": " ".join(src_subword_units),
            "tgt_subwords": " ".join(tgt_subword_units),
            "tgt": translated_text,
            "alignment": "None",
            "alternate_translations": []
        }
        
        for i in range(len(output)):
            t_text = self.tokenizer.decode(output[i], skip_special_tokens=True)
            t_subwords = self.tokenizer.convert_ids_to_tokens(output[i]) 
            
            self.response["alternate_translations"].append({
                "tgt_tokens": " ".join(t_subwords),
                "tgt_subwords": " ".join(t_subwords),
                "alignments": "None",
                "tgt": t_text
            })
            
        return self.response
