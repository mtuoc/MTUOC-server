#    TransformersTranslator v 2409
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


from transformers import MarianMTModel, MarianTokenizer
import torch
import config

class TransformersTranslator:
    def __init__(self):
        self.model=None
        self.tokenizer=None
        self.device= torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.multilingual=False
        self.target_language=None
        self.translator=None
        self.beam_size=1
        self.num_hypotheses=1
        self.alternate_translations=[]
        
    def set_model(self,model_path):
        self.model = MarianMTModel.from_pretrained(model_path)
        self.tokenizer = MarianTokenizer.from_pretrained(model_path)
         
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
        
    def translate(self, text, max_length=128):
        # Tokenize the input text and move it to the GPU
        inputs = self.tokenizer(text, return_tensors="pt", max_length=max_length, truncation=True).to(self.device)
        src_subword_units = self.tokenizer.tokenize(text) 
    
        # Ensure the model is on the GPU
        self.model.to(self.device)
    
        # Generate translation
        with torch.no_grad():
            output = self.model.generate(**inputs, 
                                         num_beams=self.beam_size, 
                                         num_return_sequences=self.num_hypotheses, 
                                         early_stopping=True)
        
        # Decode the generated tokens
        translated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
        tgt_subword_units = self.tokenizer.convert_ids_to_tokens(output[0]) 
        
        self.response = {}
        self.response["src_tokens"] = " ".join(src_subword_units)
        self.response["tgt_tokens"] = " ".join(tgt_subword_units)
        self.response["src_subwords"] = " ".join(src_subword_units)
        self.response["tgt_subwords"] = " ".join(tgt_subword_units)
        self.response["tgt"] = translated_text
        self.response["alignment"] = "None"
        self.response["alternate_translations"] = []
    
        for i in range(0, len(output)):
            translated_text = self.tokenizer.decode(output[i], skip_special_tokens=True)
            tgt_subword_units = self.tokenizer.convert_ids_to_tokens(output[i]) 
            self.alternate_translation = {}
            self.alternate_translation["tgt_tokens"] = " ".join(tgt_subword_units)
            self.alternate_translation["tgt_subwords"] = " ".join(tgt_subword_units)
            self.alternate_translation["alignments"] = "None"
            self.alternate_translation["tgt"] = translated_text
            self.response["alternate_translations"].append(self.alternate_translation)
        
        '''
        if config.GetWordAlignments_type == "fast_align":
            alignment, src_tokens, tgt_tokens = config.WordAligner.align_sentence_pair(text, translated_text)
            self.response["alignments"] = alignment
            self.response["src_tokens"] = src_tokens
            self.response["tgt_tokens"] = tgt_tokens
        '''
        return self.response

