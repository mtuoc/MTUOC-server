#    AinaTranslator v 2502
#    Description: an MTUOC server using Sentence Piece as preprocessing step
#    Copyright (C) 2025  Antoni Oliver
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


import ctranslate2
import pyonmttok
import os
from MTUOC_misc import printLOG
import config


class AinaTranslator:
    def __init__(self):
        self.model_dir=None
        self.translator=None
        self.tokenizer=None
        self.beam_size=1
        self.num_hypotheses=1
        self.alternate_translations=[]
        
    def set_model(self,model_dir,revision):
        current_directory = os.getcwd()
        model_dir=os.path.join(current_directory,model_dir)
        try:
            self.tokenizer=pyonmttok.Tokenizer(mode="none", sp_model_path = model_dir + "/spm.model")
        except:
            self.tokenizer=pyonmttok.Tokenizer(mode="none", sp_model_path = model_dir + "/sentencepiece.bpe.model")
        self.translator= ctranslate2.Translator(model_dir)
        
    def set_beam_size(self,beam_size):
        self.beam_size=beam_size
    
    def set_num_hypotheses(self,num_hypotheses):
        self.num_hypotheses=num_hypotheses
        
    def clean(self,llista):
        self.llista=llista
        for item in ["<s>","</s>","<pad>"]:
            c = self.llista.count(item) 
            for i in range(c): 
                self.llista.remove(item) 
        return(self.llista)
        
    def translate(self,text):
        printLOG(3,"TRANSLATING WITH AINA:",text)
        
        self.alternate_translations=[]
        self.tokenized=self.tokenizer.tokenize(text)
        printLOG(4,"TOKENIZED:",self.tokenized)
        self.translation = self.translator.translate_batch([self.tokenized[0]],beam_size=self.beam_size,num_hypotheses=self.num_hypotheses)
        printLOG(3,"TRANSLATED WITH AINA:",self.translation)
        
        for i in range(0,len(self.translation[0].hypotheses)):
            self.alternate_translation={}
            self.alternate_translation["tgt_tokens"]=self.translation[0].hypotheses[i]
            self.alternate_translation["tgt_tokens"]=self.clean(self.alternate_translation["tgt_tokens"])
            self.alternate_translation["tgt_subwords"]=self.alternate_translation["tgt_tokens"]                    
            self.alternate_translation["alignment"]="None"
            self.alternate_translation["tgt"]="".join(self.alternate_translation["tgt_tokens"]).replace("▁"," ")
            self.alternate_translation["tgt_tokens"]=" ".join(self.alternate_translation["tgt_tokens"])
            self.alternate_translation["tgt_subwords"]=" ".join(self.alternate_translation["tgt_subwords"])
            if self.alternate_translation["tgt"].startswith(" ") and not text.startswith(" "): self.alternate_translation["tgt"]=self.alternate_translation["tgt"][1:]
            self.alternate_translations.append(self.alternate_translation)

        self.response={}
        
        self.response["src_tokens"]=" ".join(self.tokenized[0])
        self.response["tgt_tokens"]=self.alternate_translations[0]["tgt_tokens"]
        self.response["src_subwords"]=" ".join(self.tokenized[0])
        self.response["tgt_subwords"]=self.alternate_translations[0]["tgt_tokens"]
        self.response["tgt"]=self.alternate_translations[0]["tgt"]
        self.response["alignment"]=self.alternate_translations[0]["alignment"]
        #self.alternate_translations.append(self.response)
        self.response["alternate_translations"]=self.alternate_translations
        printLOG(4,"RESPONSE:",self.response)
        return(self.response)
        

