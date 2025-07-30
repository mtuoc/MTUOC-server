#    LlamaTranslator v 2411
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
from transformers import pipeline

class LlamaTranslator:
    def __init__(self,model_name):
        self.model=model_name
        self.torch_dtype=torch.bfloat16
        self.device_map="auto"
        self.pipe= pipeline(
            "text-generation",
            model=self.model,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            )
        self.role=None
        self.max_new_tokens=256
        
    def set_role(self,role):
        self.role=role
        
    def set_max_new_tokens(self, mnt):
        self.max_new_tokens=mnt

    def generate(self,text):
        messages = [
            {"role": "system", "content": self.role},
            {"role": "user", "content": text}
        ]
        outputs = self.pipe(
            messages,
            max_new_tokens=self.max_new_tokens,
        )
        self.answer=outputs[0]["generated_text"][-1]['content']
        self.alternate_translations=[]
        self.response={}
        self.response["src_tokens"]=text
        self.response["tgt_tokens"]=self.answer
        self.response["src_subwords"]=text
        self.response["tgt_subwords"]=self.answer
        self.response["tgt"]=self.answer
        self.response["alignment"]="None"
        self.response["alternate_translations"]=self.alternate_translations
        return(self.response)
        
