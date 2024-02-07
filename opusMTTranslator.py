#    opusMTTranslator v 2402
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


from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import sentencepiece as spm


class opusMTTranslator:
    def __init__(self):
        self.model=None
        self.tokenizer=None
        self.device=device = torch.cuda.current_device() if torch.cuda.is_available() else -1
        self.multilingual=False
        self.target_language=None
        self.translator=None
        self.beam_size=1
        self.num_hypotheses=1
        self.alternate_translations=[]
        
    def set_model(self,model_name):
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.translator=pipeline('translation', model=self.model, tokenizer=self.tokenizer, return_tensors =True, device=self.device) 
        
    def set_multilingual(self,ml):
        self.multilingual=ml
        
    def set_target_language(self,target_language):
        self.target_language=target_language
        
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
        self.alternate_translations=[]
        self.src_tokens=self.tokenizer.convert_ids_to_tokens(self.tokenizer.encode(text))
        self.src_tokens=self.clean(self.src_tokens)
        if self.multilingual:
            text=">>"+self.target_language+"<< "+text
        self.summary = self.translator(text,max_length=1024, num_beams=self.beam_size, num_return_sequences=self.num_hypotheses)
        for i in range(0,len(self.summary)):
            self.alternate_translation={}
            self.alternate_translation["tgt_tokens"]=self.tokenizer.convert_ids_to_tokens(self.summary[i]['translation_token_ids'])
            self.alternate_translation["tgt_tokens"]=self.clean(self.alternate_translation["tgt_tokens"])
            self.alternate_translation["alignments"]="None"
            self.alternate_translation["tgt"]="".join(self.alternate_translation["tgt_tokens"]).replace("▁"," ")
            if self.alternate_translation["tgt"].startswith(" ") and not text.startswith(" "): self.alternate_translation["tgt"]=self.alternate_translation["tgt"][1:]
            self.alternate_translations.append(self.alternate_translation)

        self.response={}
        self.response["src_tokens"]=" ".join(self.src_tokens)
        self.response["tgt_tokens"]=" ".join(self.alternate_translations[0]["tgt_tokens"])
        self.response["tgt"]=self.alternate_translations[0]["tgt"]
        self.response["alignments"]="None"
        self.response["alternate_translations"]=self.alternate_translations
        return(self.response)
        

