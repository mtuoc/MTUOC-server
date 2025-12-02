#    M2M100Translator v 2411
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

class M2M100Translator:
    def __init__(self):
        self.model=None
        self.tokenizer=None
        self.device=device = torch.cuda.current_device() if torch.cuda.is_available() else -1
        self.multilingual=False
        self.translator=None
        self.src_tokens=None
        self.tgt_tokens=None
        self.beam_size=1
        self.num_hypotheses=1

    def clean(self,llista):
        self.llista=llista
        for item in ["<s>","</s>","<pad>"]:
            c = self.llista.count(item) 
            for i in range(c): 
                self.llista.remove(item) 
        return(self.llista)

    def set_model(self,model_name):
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        #self.translator= pipeline('translation', model=self.model, tokenizer=self.tokenizer,device=self.device) 
    
    def set_beam_size(self,beam_size):
        self.beam_size=beam_size
    
    def set_num_hypotheses(self,num_hypotheses):
        self.num_hypotheses=num_hypotheses
    
    def translate(self,text):
        input_ids = self.tokenizer(text, return_tensors="pt").input_ids
        output_ids = self.model.generate(input_ids, max_length=200, num_beams=5, num_return_sequences=self.num_hypotheses)

        generated_translation= self.tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
        self.alternate_translations=[]

        
        for i in range(0,len(output_ids)):
            alternate_translation= self.tokenizer.decode(output_ids[i], skip_special_tokens=True).strip()
            self.alternate_translation={}
            self.alternate_translation["src_tokens"]=text
            self.alternate_translation["tgt_tokens"]=alternate_translation
            self.alternate_translation["src_subwords"]=text
            self.alternate_translation["tgt_subwords"]=alternate_translation
            self.alternate_translation["tgt"]=alternate_translation
            self.alternate_translation["alignment"]="None"
            self.alternate_translations.append(self.alternate_translation)
        
        self.response={}
        self.response["src_tokens"]=text
        self.response["tgt_tokens"]=generated_translation
        self.response["src_subwords"]=text
        self.response["tgt_subwords"]=generated_translation
        self.response["tgt"]=generated_translation
        self.response["alignment"]="None"
        self.response["alternate_translations"]=self.alternate_translations
        return(self.response)
       
