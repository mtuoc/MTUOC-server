from MTUOC_misc import printLOG
import os
from google.cloud import translate as translateGoogle
from google.cloud import translate
import sys

class GoogleTranslateTranslator:
    
    def __init__(self):
        self.sllang=None
        self.tllang=None
        self.glossary=None
        self.project_id=None
        self.location=None
        self.jsonfile=None
        
        self.client = translateGoogle.TranslationServiceClient()
        self.client = translateGoogle.TranslationServiceClient()
        
        self.parent=None
        
        
    def set_sllang(self,dada):
        self.sllang=None
        
    def set_tllang(self,dada):
        self.tllang=dada
    def set_glossary(self,dada):
        self.glossary=dada
    def set_project_id(self,dada):
        self.project_id=dada
    def set_location(self,dada):
        self.location=dada
    def set_jsonfile(self,dada):
        self.jsonfile=dada


    def translate_text_with_glossary(self, text):

        glossary = self.client.glossary_path(
            self.project_id, self.location, self.glossary_id 
        )

        glossary_config = translateGoogle.TranslateTextGlossaryConfig(glossary=self.glossary)

        # Supported language codes: https://cloud.google.com/translate/docs/languages
        response = self.client.translate_text(
            request={
                "contents": [text],
                "target_language_code": self.tllang,
                "source_language_code": self.sllang,
                "parent": self.parent,
                "glossary_config": glossary_config,
            }
        )
        translation=response.glossary_translations[0]
        return(translation.translated_text)

    def translate_text(self, text):
        try:
            """Translating Text."""
            # Detail on supported types can be found here:
            # https://cloud.google.com/translate/docs/supported-formats
            response = self.client.translate_text(
                parent=self.parent,
                contents=[text],
                mime_type="text/plain",  # mime types: text/plain, text/html
                source_language_code=self.sllang,
                target_language_code=self.tllang,
            )
            # Display the translation for each input text provided
            translation=response.translations[0]
            return(translation.translated_text)
        except:
            print("ERROR:",sys.exc_info())

    
    def translate(self, segment):
        self.parent = f"projects/{self.project_id}/locations/{self.location}"
        segment=segment.rstrip()
        if self.glossary==None:                    
            translation=self.translate_text(segment)
        else:
            translation=self.translate_text_with_glossary(segment)
        self.response={}
        self.response["src_tokens"]=""
        self.response["tgt_tokens"]=""
        self.response["src_subwords"]=""
        self.response["tgt_subwords"]=""
        self.response["tgt"]=translation
        self.response["alignment"]="None"
        self.response["alternate_translations"]=[]
        return(self.response)
