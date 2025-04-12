#    SalamandraTATranslarto v 2502
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


import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
#from huggingface_hub import snapshot_download


class SalamandraTATranslator:
    def __init__(self):
        
        self.SalamandraTATranslator_src_lang=None
        self.SalamandraTATranslator_tgt_lang=None
        self.SalamandraTATranslator_model_id=None
        self.SalamandraTATranslator_beam_size=1
        self.SalamandraTATranslator_num_hypotheses=1
        self.alternate_translations=[]
        
    def set_src_lang(self,src_lang):
        self.src_lang=src_lang
    
    def set_tgt_lang(self,tgt_lang):
        self.tgt_lang=tgt_lang
        
    def set_model_id(self,model_id):
        self.model_id=model_id
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        
        self.model = AutoModelForCausalLM.from_pretrained(self.model_id)
    
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
        
    def translate(self,sentence):
        self.alternate_translations=[]
        # Load tokenizer and model
        
        self.tokenized=" ".join(self.tokenizer.tokenize(sentence))
        

        # Move model to GPU if available
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(device)

        src_lang_code = self.src_lang
        tgt_lang_code = self.tgt_lang

        prompt = f'[{src_lang_code}] {sentence} \n[{tgt_lang_code}]'
        # Tokenize and move inputs to the same device as the model
        input_ids = self.tokenizer(prompt, return_tensors='pt').input_ids.to(device)
        output_ids = self.model.generate(input_ids, max_length=500, num_beams=self.beam_size)
        input_length = input_ids.shape[1]

        generated_text = self.tokenizer.decode(output_ids[0, input_length:], skip_special_tokens=True).strip()
        
        
        '''
        self.tokenized=self.tokenizer.tokenize(text)
        self.translation = self.translator.translate_batch([self.tokenized[0]],beam_size=self.beam_size,num_hypotheses=self.num_hypotheses)
        
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
        '''
        self.response={}
        
        
        
        
        self.response["src_tokens"]=self.tokenized
        self.response["tgt_tokens"]=generated_text
        self.response["src_subwords"]=self.tokenized
        self.response["tgt_subwords"]=generated_text
        self.response["tgt"]=generated_text
        self.response["alignment"]=""
        self.response["alternate_translations"]=self.alternate_translations
        print(self.response)
        return(self.response)
        

