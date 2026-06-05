from MTUOC_misc import printLOG
import os
from google.cloud import translate as translateGoogle
from google.cloud import translate
import sys

class GoogleTranslateTranslator:
    
    def __init__(self):
        self.sllang = None
        self.tllang = None
        self.glossary = None
        self.project_id = None
        self.location = None
        self.jsonfile = None
        self.client = None      # <--- No l'instanciem aquí per evitar errors de credencials buides
        self.parent = None
        self.model_path = "GoogleTranslate" # <--- Variable de control compatible amb MTUOC-server
        
    def set_sllang(self, dada):
        self.sllang = dada     # <--- CORREGIT: Abans posava self.sllang = None
        
    def set_tllang(self, dada):
        self.tllang = dada
        
    def set_glossary(self, dada):
        self.glossary = dada
        
    def set_project_id(self, dada):
        self.project_id = dada
        
    def set_location(self, dada):
        self.location = dada
        
    def set_jsonfile(self, dada):
        self.jsonfile = dada

    def translate_text_with_glossary(self, text):
        # El client s'assegura d'estar instanciat un cop les variables d'entorn ja estan llestes
        if self.client is None:
            self.client = translateGoogle.TranslationServiceClient()

        # Al teu codi utilitzes self.glossary_id que no existia, usem self.glossary directament
        glossary_path = self.client.glossary_path(
            self.project_id, self.location, self.glossary 
        )

        glossary_config = translateGoogle.TranslateTextGlossaryConfig(glossary=glossary_path)

        response = self.client.translate_text(
            request={
                "contents": [text],
                "target_language_code": self.tllang,
                "source_language_code": self.sllang,
                "parent": self.parent,
                "glossary_config": glossary_config,
            }
        )
        translation = response.glossary_translations[0]
        return translation.translated_text

    def translate_text(self, text):
        try:
            if self.client is None:
                self.client = translateGoogle.TranslationServiceClient()

            response = self.client.translate_text(
                parent=self.parent,
                contents=[text],
                mime_type="text/plain",
                source_language_code=self.sllang,
                target_language_code=self.tllang,
            )
            translation = response.translations[0]
            return translation.translated_text
        except:
            print("ERROR:", sys.exc_info())
            return ""

    def translate(self, segment):
        self.parent = f"projects/{self.project_id}/locations/{self.location}"
        segment = segment.rstrip()
        
        if self.glossary is None:                    
            translation = self.translate_text(segment)
        else:
            translation = self.translate_text_with_glossary(segment)
            
        self.response = {}
        # Mantenim l'estructura buida de tokens ja que Google és un servei extern API Blackbox
        self.response["src_tokens"] = segment
        self.response["tgt_tokens"] = translation
        self.response["src_subwords"] = segment
        self.response["tgt_subwords"] = translation
        self.response["tgt"] = translation
        self.response["alignment"] = "None"
        self.response["alternate_translations"] = []
        return self.response
