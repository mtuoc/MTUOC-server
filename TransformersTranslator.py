#    TransformersTranslator v 2409 (GPU Optimized)
#    Description: an MTUOC server using Sentence Piece as preprocessing step
#    Copyright (C) 2024  Antoni Oliver
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.


from transformers import MarianMTModel, MarianTokenizer
import torch
import config

class TransformersTranslator:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        # Per defecte, detectem automàticament la millor opció
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.multilingual = False
        self.target_language = None
        self.translator = None
        self.beam_size = 1
        self.num_hypotheses = 1
        self.alternate_translations = []
        
        print(f"INFO: TransformersTranslator inicialitzat (Auto-device: {self.device})")

    def set_device(self, device_type):
        """
        Permet forçar el dispositiu des de fora. 
        device_type pot ser 'cuda', 'cpu' o un objecte torch.device.
        """
        if device_type == "cuda" and not torch.cuda.is_available():
            print("WARNING: CUDA no disponible. Es manté el dispositiu actual.")
            return

        self.device = torch.device(device_type)
        
        # Si el model ja està carregat, l'hem de moure al nou dispositiu
        if self.model is not None:
            self.model.to(self.device)
            print(f"INFO: Model mogut a {self.device}")
        else:
            print(f"INFO: Dispositiu canviat a {self.device} (el model es carregarà aquí)")

    def set_model(self, model_path):
        self.model = MarianMTModel.from_pretrained(model_path)
        self.tokenizer = MarianTokenizer.from_pretrained(model_path)
        
        # Assegurem que el model es carrega al dispositiu configurat actualment
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
        return(self.llista)
        
    def translate(self, text, max_length=128):
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model no carregat. Crida a set_model() primer.")

        # Enviem els tensors al dispositiu actual (self.device)
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
