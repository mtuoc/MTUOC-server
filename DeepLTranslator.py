from MTUOC_misc import printLOG
import os
import deepl
import sys


class DeepLTranslator:
    
    def __init__(self):
        self.sllang=None
        self.tllang=None
        self.glossary=None
        self.formality=None
        self.API_key=None
        self.split_sentences="off"
        self.DeepLtranslator=None
        
        
        
    def set_sllang(self,dada):
        self.sllang=None
        
    def set_tllang(self,dada):
        self.tllang=dada
    def set_glossary(self,dada):
        self.glossary=dada
    def set_formality(self,dada):
        self.formality=dada
    def set_split_sentences(self,dada):
        self.split_sentences=dada
    def set_API_key(self,dada):
        self.API_key=dada
    def createTranslator(self):
        self.DeepLtranslator = deepl.Translator(self.API_key)

    def translate(self,segment):
        print("TRANSLATE:",segment,self.DeepLtranslator)
        if self.glossary==None:
            try:
                translation = self.DeepLtranslator.translate_text(segment, source_lang=self.sllang, target_lang=self.tllang,formality=self.formality,split_sentences=self.split_sentences)
            except:
                print("ERROR DeepL:",sys.exc_info())
        else:
            try:
                translation = self.DeepLtranslator.translate_text(segment, source_lang=self.sllang, target_lang=self.tllang, glossary=self.glossary, formality=self.formality, split_sentences=self.split_sentences)
            except:
                print("ERROR DeepL:",sys.exc_info())
            
 
        self.response={}
        self.response["src_tokens"]=""
        self.response["tgt_tokens"]=""
        self.response["src_subwords"]=""
        self.response["tgt_subwords"]=""
        self.response["tgt"]=translation.text
        self.response["alignment"]="None"
        self.response["alternate_translations"]=[]
        return(self.response)
