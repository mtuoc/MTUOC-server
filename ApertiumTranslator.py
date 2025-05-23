#    ApertiumTranslator v 2501
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


import apertium

class ApertiumTranslator:
    def __init__(self, sl, tl):
        self.sl=sl
        self.tl=tl
        
    def translate(self,text):
        self.translation=config.apertium_translator(text, mark_unknown=config.apertium_mark_unknown)
        self.response={}
        self.response["src_tokens"]=text
        self.response["tgt_tokens"]=self.translation
        self.response["src_subwords"]=text
        self.response["tgt_subwords"]=self.translation
        self.response["tgt"]=self.translation
        self.response["alignment"]="None"
        self.response["alternate_translations"]=[]
        
        return(self.response)
        

