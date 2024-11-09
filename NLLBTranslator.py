#    NLLBTranslator v 2411
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

class NLLBTranslator:
    def __init__(self):
        self.model=None
        self.tokenizer=None
        self.device=device = torch.cuda.current_device() if torch.cuda.is_available() else -1
        self.multilingual=False
        self.src_lang=None
        self.tgt_lang=None
        self.translator=None
        self.src_tokens=None
        self.tgt_tokens=None
        self.beam_size=1
        self.num_hypotheses=1

    def clean(self,llista):
        self.llista=llista
        for item in ["<s>","</s>",self.src_lang,self.tgt_lang,"<pad>"]:
            c = self.llista.count(item) 
            for i in range(c): 
                self.llista.remove(item) 
        return(self.llista)

    def set_model(self,model_name, src_lang, tgt_lang):
        self.src_lang=src_lang
        self.tgt_lang=tgt_lang
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, src_lang=self.src_lang, tgt_lang=self.tgt_lang)
        self.translator= pipeline('translation', model=self.model, tokenizer=self.tokenizer,src_lang=self.src_lang, tgt_lang=self.tgt_lang,device=self.device) 
    
    def set_beam_size(self,beam_size):
        self.beam_size=beam_size
    
    def set_num_hypotheses(self,num_hypotheses):
        self.num_hypotheses=num_hypotheses
    
    def translate(self,text):
        self.alternate_translations=[]
        self.src_tokens=self.tokenizer.convert_ids_to_tokens(self.tokenizer.encode(text))
        self.src_tokens=self.clean(self.src_tokens)
        
        self.translator = pipeline('translation', model=self.model, tokenizer=self.tokenizer, return_tensors =True, src_lang=self.src_lang, tgt_lang=self.tgt_lang,device=self.device, num_beams=self.beam_size, num_return_sequences=self.num_hypotheses) 
        self.target_seq_Tok = self.translator(text, max_length=1024)
        
        for i in range(0,len(self.target_seq_Tok)):
            self.alternate_translation={}
            self.alternate_translation["tgt_tokens"]=self.tokenizer.convert_ids_to_tokens(self.target_seq_Tok[i]['translation_token_ids'])
            self.alternate_translation["tgt_tokens"]=self.clean(self.alternate_translation["tgt_tokens"])
            self.alternate_translation["alignments"]="None"
            self.alternate_translation["tgt"]="".join(self.alternate_translation["tgt_tokens"]).replace("▁"," ")
            self.alternate_translation["tgt_tokens"]=" ".join(self.alternate_translation["tgt_tokens"])
            if self.alternate_translation["tgt"].startswith(" ") and not text.startswith(" "): self.alternate_translation["tgt"]=self.alternate_translation["tgt"][1:]
            self.alternate_translations.append(self.alternate_translation)

        
        self.response={}
        self.response["src_tokens"]=" ".join(self.src_tokens)
        self.response["tgt_tokens"]=self.alternate_translations[0]["tgt_tokens"]
        self.response["src_subwords"]=" ".join(self.src_tokens)
        self.response["tgt_subwords"]=self.alternate_translations[0]["tgt_tokens"]
        self.response["tgt"]=self.alternate_translations[0]["tgt"]
        self.response["alignment"]="None"
        return(self.response)
       
