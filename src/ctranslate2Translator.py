# ctranslate2_translator_main.py
# ---------------------------------------------------------------------------------------
#   ctranslate2Translator v 2511 (Bilingual None-Text Fix)
#   Description: a ctranslate2 and sentencepiece component for MTUOC
#   Copyright (C) 2026  Antoni Oliver
# ---------------------------------------------------------------------------------------

import os
import codecs
from typing import List, Dict, Any
import ctranslate2
import sentencepiece as spm
import time


class ctranslate2Translator:
    """Clase principal per a gestionar la traducció directa amb CTranslate2 i SentencePiece."""
    
    def __init__(self, config_path: str = None):
        self.translation_model = None
        self.model_name = "None"
        self.SL_sp_model = None
        self.TL_sp_model = None
        self.src_lang = None
        self.tgt_lang = None
        self.beam_size = 1
        self.num_hypotheses = 1
        self.device = "cpu"
        self.compute_type = "default"
        
        self.translator = None
        self.spSL = None
        self.spTL = None
        self.alternate_translations = []
        self.response = {}

        if config_path and os.path.exists(config_path):
            self._load_config(path=config_path)
            
        self.start_translator()

    def _load_config(self, path: str):
        """Parseja el fitxer de configuració del model."""
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

        self.translation_model = cfg_data.get('translation_model', None)
        self.model_name = self.translation_model if self.translation_model else "None"
        self.SL_sp_model = cfg_data.get('SL_spmodel', None)
        self.TL_sp_model = cfg_data.get('TL_spmodel', None)
        
        # 🌟 EL TRUC: Si al YAML hi diu "None", None, o "", ho convertim en un objecte None de Python
        src = cfg_data.get('src_lang', 'None')
        self.src_lang = None if src in ["None", "none", ""] else src
        
        tgt = cfg_data.get('tgt_lang', 'None')
        self.tgt_lang = None if tgt in ["None", "none", ""] else tgt

        self.beam_size = int(cfg_data.get('beam_size', 1))
        self.num_hypotheses = int(cfg_data.get('num_hypotheses', 1))
        self.device = cfg_data.get('device', 'cpu')
        self.compute_type = cfg_data.get('compute_type', 'default')

    def start_translator(self):
        if self.translation_model:
            print(f"START CTRANSLATE2 ENGINE ({self.device} - {self.compute_type}): {self.translation_model}")
            self.translator = ctranslate2.Translator(
                self.translation_model, 
                device=self.device, 
                compute_type=self.compute_type
            )

        if self.SL_sp_model and os.path.exists(self.SL_sp_model):
            self.spSL = spm.SentencePieceProcessor()
            self.spSL.load(self.SL_sp_model)

        if self.TL_sp_model and os.path.exists(self.TL_sp_model):
            self.spTL = spm.SentencePieceProcessor()
            self.spTL.load(self.TL_sp_model)

    def translate(self, text: str) -> Dict[str, Any]:
        if not self.translator or not self.spSL or not self.spTL:
            print("ERROR: Models no inicialitzats.")
            return {}

        source_sentences = [text.strip()]
        
        # 🌟 GESTIÓ DE PREFIX DE DESTÍ PURA:
        # Si és un autèntic None, passem la variable com a None a translate_batch.
        # Així CTranslate2 no afegeix ABSOLUTAMENT RES davant (ni tan sols cadenes buides).
        target_prefix = None
        if self.tgt_lang is not None:
            target_prefix = [[self.tgt_lang]] * len(source_sentences)
        
        # Tokenització en peces
        source_sents_subworded = self.spSL.encode_as_pieces(source_sentences[0])
        
        # Gestió del codi d'idioma font
        if self.src_lang is not None:
            source_sents_subworded = [[self.src_lang] + source_sents_subworded + ["</s>"]]
        else:
            source_sents_subworded = [source_sents_subworded + ["</s>"]]
            
        # Traducció directe per l'enginy de ctranslate2
        translations_subworded_raw = self.translator.translate_batch(
            source_sents_subworded, 
            batch_type="tokens", 
            max_batch_size=2024, 
            beam_size=self.beam_size, 
            num_hypotheses=self.num_hypotheses, 
            target_prefix=target_prefix
        )
        
        hypotheses = translations_subworded_raw[0].hypotheses
        
        # Neteja i preparació de la visualització de tokens de la frase font per a la resposta
        source_sent_subworded = source_sents_subworded[0]
        if source_sent_subworded and source_sent_subworded[-1] == "</s>": 
            source_sent_subworded = source_sent_subworded[0:-1]
        if self.src_lang is not None and source_sent_subworded:
            source_sent_subworded = source_sent_subworded[1:]
        source_sent_str = " ".join(source_sent_subworded)
        
        # Neteja de la llista de tokens de sortida
        cleaned_hypotheses_tokens = []
        for h in hypotheses:
            # Només eliminem el codi si realment s'havia definit un prefix al YAML
            if self.tgt_lang is not None and len(h) > 0:
                h = h[1:]
            
            # Eliminem tokens de control residuals (si n'hi hagués cap de natiu de control)
            filtrats = [token for token in h if token not in ["<s>", "</s>", "<pad>"]]
            cleaned_hypotheses_tokens.append(filtrats)
        
        # Des-tokenització (Decode) amb el model de SentencePiece de destí
        translations = self.spTL.decode(cleaned_hypotheses_tokens)
                
        translations_subworded_strings = []
        for tokens_list in cleaned_hypotheses_tokens:
            translations_subworded_strings.append(" ".join(tokens_list))

        # Estructuració de la resposta final per a MTUOC
        self.response = {}
        self.response["src"] = text
        self.response["src_tokens"] = source_sent_str
        self.response["src_subwords"] = source_sent_str
        self.response["tgt"] = translations[0] if translations else ""
        self.response["tgt_tokens"] = translations_subworded_strings[0] if translations_subworded_strings else ""
        self.response["tgt_subwords"] = translations_subworded_strings[0] if translations_subworded_strings else ""
        self.response["alignment"] = ""
        self.response["alternate_translations"] = []
        
        # Afegim les opcions n-best alternatives generades pel beam_size
        for i in range(1, len(translations)):
            self.alternate_translation = {
                "tgt": translations[i],
                "tgt_tokens": translations_subworded_strings[i],
                "tgt_subwords": translations_subworded_strings[i],
                "alignment": ""
            }
            self.response["alternate_translations"].append(self.alternate_translation)        
        time.sleep(0.1)    
        return self.response
