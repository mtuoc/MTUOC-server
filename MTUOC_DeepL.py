#    MTUOC_DeepL
#    Copyright (C) 2023  Antoni Oliver
#    v. 07/06/2023
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


import config
from MTUOC_misc import printLOG

###DeepL imports
import deepl

def DeepL_translate(segment):
    if config.DeepL_glossary==None:
        cadena="Translating without glossary from "+config.DeepL_sl_lang+" to "+config.DeepL_tl_lang
        printLOG(3,cadena)
        cadena="Source segment: "+segment
        printLOG(3,cadena)
        try:
            translation = config.DeepLtranslator.translate_text(segment, source_lang=config.DeepL_sl_lang, target_lang=config.DeepL_tl_lang,formality=config.DeepL_formality,split_sentences=config.DeepL_split_sentences)
        except:
            printLOG(1,"ERROR DeepL:",sys.exc_info())
        cadena="Translation:    "+translation.text
        printLOG(3,cadena)
    else:
        cadena="Translating with glossary "+config.DeepL_glossary_name,DeepL_glossary+" from "+config.DeepL_sl_lang+" to "+config.DeepL_tl_lang
        printLOG(3,cadena)
        cadena="Source segment: "+segment
        printLOG(3,cadena)
        try:
            translation = config.DeepLtranslator.translate_text(segment, source_lang=config.DeepL_sl_lang, target_lang=config.DeepL_tl_lang, glossary=config.DeepL_glossary, formality=config.DeepL_formality, split_sentences=config.DeepL_split_sentences)
        except:
            printLOG(1,"ERROR DeepL:",sys.exc_info())
        cadena="Translation:    "+translation.text
        printLOG(3,cadena)

    try:
        alternate_translations=[]
        alternate_translation={}
        alternate_translation["tgt_tokens"]="None"
        alternate_translation["alignments"]="None"
        alternate_translation["tgt"]=translation.text
        alternate_translations.append(alternate_translation)
        response={}
        response["src_tokens"]="None"
        response["tgt_tokens"]="None"
        response["tgt"]=translation.text
        response["alignments"]="None"
        response["alternate_translations"]=alternate_translations
    except:
        printLOG(3,"Error translating with Google Translate",sys.exc_info())
            
        ###
    return(response)

