#    NLLBTranslator v 2602
#    Description: an MTUOC server using Sentence Piece as preprocessing step
#    Copyright (C) 2024  Antoni Oliver
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


import yaml
import torch
from transformers import AutoModelForSeq2SeqLM, NllbTokenizerFast

class NLLBTranslator:
    def __init__(self, config_path=None):
        self.model = None
        self.tokenizer = None
        self.device = -1  # Per defecte a CPU (-1)
        self.src_lang = None
        self.tgt_lang = None
        self.model_name = None
        self.beam_size = 1
        self.num_hypotheses = 1
        self.response = {}
        self.alternate_translations = []

        # Si ens passen la ruta del config, la processem automàticament
        if config_path:
            self.load_from_config(config_path)

    def load_from_config(self, config_path):
        """Llegeix el fitxer YAML de NLLB i ho configura tot de cop."""
        try:
            print("Loading config inside NLLB class: ", config_path)
            with open(config_path, 'r', encoding="utf-8") as stream:
                config_yaml = yaml.load(stream, Loader=yaml.FullLoader)
            
            # Seguretat: gestionem si el YAML té el node "NLLB:" o si està a l'arrel
            if isinstance(config_yaml, dict) and "NLLB" in config_yaml:
                nllb_config = config_yaml["NLLB"]
            else:
                nllb_config = config_yaml
            
            self.model_name = nllb_config.get("model", "./nllb-200-distilled-600M")
            self.model_path = self.model_name  # <--- Afegit per compatibilitat amb OpusMT al servidor
            self.src_lang = nllb_config.get("src_lang", "eng_Latn")
            self.tgt_lang = nllb_config.get("tgt_lang", "cat_Latn")
            self.beam_size = nllb_config.get("beam_size", 5)
            self.num_hypotheses = nllb_config.get("num_hypotheses", 5)
            
            # Configurem primer el dispositiu
            device_type = nllb_config.get("device", "gpu")
            self.set_device(device_type)
            
            # Carreguem el model amb els paràmetres obtinguts
            self.set_model(self.model_name, self.src_lang, self.tgt_lang)
            
        except Exception as e:
            print(f"ERROR: No s'ha pogut carregar la configuració de NLLB des de {config_path}. Error: {e}")

    def clean(self, llista):
        # Filtrem els tokens especials de la llista
        special_tokens = ["<s>", "</s>", self.src_lang, self.tgt_lang, "<pad>"]
        return [item for item in llista if item not in special_tokens]

    def set_device(self, device):
        if device == "auto":
            self.device = 0 if torch.cuda.is_available() else -1
        elif device == "cpu":
            self.device = -1
        elif device == "gpu":
            self.device = 0 if torch.cuda.is_available() else -1
        
        # Si el model ja s'hagués carregat, el movem ara
        if self.model is not None and self.device != -1:
            device_str = f"cuda:{self.device}"
            self.model = self.model.to(device_str)

    def set_model(self, model_name, src_lang, tgt_lang):
        self.model_name = model_name
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        
        # Carreguem el tokenizer de NLLB forçant el mode Fast
        self.tokenizer = NllbTokenizerFast.from_pretrained(
            self.model_name, 
            src_lang=self.src_lang, 
            tgt_lang=self.tgt_lang,
            use_fast=True
        )
        
        # Carreguem el model
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        
        if self.device != -1:
            device_str = f"cuda:{self.device}" if isinstance(self.device, int) else self.device
            self.model = self.model.to(device_str)

    def translate(self, text):
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model not loaded. Call set_model() or init with a valid config_path first.")

        self.alternate_translations = []
        
        # 1. Preparem els inputs
        inputs = self.tokenizer(text, return_tensors="pt")
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        # src_tokens per a la resposta
        self.src_tokens = self.clean(self.tokenizer.convert_ids_to_tokens(inputs['input_ids'][0]))

        # 2. Identificació robusta de l'ID de l'idioma
        if self.tgt_lang not in self.tokenizer.get_vocab():
            print(f"ERROR: L'idioma {self.tgt_lang} no està al vocabulari del tokenizer!")
        
        tgt_lang_id = self.tokenizer.convert_tokens_to_ids(self.tgt_lang)

        # 3. Generació directa
        try:
            generated_tokens = self.model.generate(
                input_ids=inputs['input_ids'],
                attention_mask=inputs.get('attention_mask'),
                forced_bos_token_id=tgt_lang_id,
                max_length=1024,
                num_beams=self.beam_size,
                num_return_sequences=self.num_hypotheses
            )
        except Exception as e:
            print(f"Error a model.generate: {e}")
            raise e

        # 4. Processament de resultats
        for i in range(len(generated_tokens)):
            alternate_translation = {}
            token_ids = generated_tokens[i]
            
            tgt_text = self.tokenizer.decode(token_ids, skip_special_tokens=True)
            
            tgt_tokens_list = self.tokenizer.convert_ids_to_tokens(token_ids)
            tgt_tokens_list = self.clean(tgt_tokens_list)
            
            alternate_translation["tgt_tokens"] = " ".join(tgt_tokens_list)
            alternate_translation["alignments"] = "None"
            alternate_translation["tgt"] = tgt_text
            self.alternate_translations.append(alternate_translation)

        # 5. Resposta final
        self.response = {
            "src_tokens": " ".join(self.src_tokens),
            "tgt_tokens": self.alternate_translations[0]["tgt_tokens"],
            "src_subwords": " ".join(self.src_tokens),
            "tgt_subwords": self.alternate_translations[0]["tgt_tokens"],
            "tgt": self.alternate_translations[0]["tgt"],
            "alignment": "None",
            "alternate_translations": self.alternate_translations
        }
        return self.response
        
    def set_beam_size(self, beam_size):
        self.beam_size = beam_size

    def set_num_hypotheses(self, num_hypotheses):
        self.num_hypotheses = num_hypotheses
