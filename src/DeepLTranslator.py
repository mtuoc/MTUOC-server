from MTUOC_misc import printLOG
import os
import deepl
import sys

class DeepLTranslator:
    
    def __init__(self):
        self.sllang = None
        self.tllang = None
        self.glossary = None
        self.formality = None
        self.API_key = None
        self.split_sentences = "off"
        self.DeepLtranslator = None
        self.model_path = "DeepL"  # <--- Variable compatible amb MTUOC-server
        
    def set_sllang(self, dada):
        self.sllang = dada        # <--- CORREGIT: Abans posava self.sllang = None
        
    def set_tllang(self, dada):
        self.tllang = dada

    def set_glossary(self, dada):
        self.glossary = dada

    def set_formality(self, dada):
        self.formality = dada

    def set_split_sentences(self, dada):
        self.split_sentences = dada

    def set_API_key(self, dada):
        self.API_key = dada

    def createTranslator(self):
        self.DeepLtranslator = deepl.Translator(self.API_key)

    def translate(self, segment):
        print("TRANSLATE:", segment, self.DeepLtranslator)
        translation_text = ""
        
        # Upper case per a codis d'idioma ISO si l'API de DeepL es posa exigent (ex: 'EN', 'HR')
        src = self.sllang.upper() if self.sllang else None
        tgt = self.tllang.upper() if self.tllang else None
        
        # DeepL demana que si passem 'en' o 'pt', especifiquem variant (ex: EN-US, EN-GB). 
        # Si a vegades falla per això al teu entorn, recorda posar 'en-us' o 'en-gb' al teu fitxer YAML
        
        if self.glossary is None:
            try:
                translation = self.DeepLtranslator.translate_text(
                    segment, 
                    source_lang=src, 
                    target_lang=tgt,
                    formality=self.formality,
                    split_sentences=self.split_sentences
                )
                translation_text = translation.text
            except Exception as e:
                print("ERROR DeepL:", sys.exc_info(), e)
        else:
            try:
                translation = self.DeepLtranslator.translate_text(
                    segment, 
                    source_lang=src, 
                    target_lang=tgt, 
                    glossary=self.glossary, 
                    formality=self.formality, 
                    split_sentences=self.split_sentences
                )
                translation_text = translation.text
            except Exception as e:
                print("ERROR DeepL:", sys.exc_info(), e)
            
        self.response = {}
        self.response["src_tokens"] = segment
        self.response["tgt_tokens"] = translation_text
        self.response["src_subwords"] = segment
        self.response["tgt_subwords"] = translation_text
        self.response["tgt"] = translation_text
        self.response["alignment"] = "None"
        self.response["alternate_translations"] = []
        return self.response
