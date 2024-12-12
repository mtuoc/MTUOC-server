#    MarianTranslator v 2410
#    Description: an MTUOC server component
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



import websocket
import socket
import time
import sys
import config
import os

from MTUOC_misc import printLOG

from SentencePieceTokenizer import SentencePieceTokenizer


class MarianTranslator():
    def __init__(self):
        self.model=None
        self.sl_vocab=None
        self.tl_vocab=None
        self.subword_type=None
        self.subword_model=None
        self.tokenizer=None
        self.beam_size=1
        self.num_hypotheses=1
        self.alternate_translations=[]
        
    
    def set_model(self,model):
        self.model=model
        
    def set_sl_vocab(self,sl_vocab):
        self.sl_vocab=sl_vocab
        
    def set_tl_vocab(self,tl_vocab):
        self.tl_vocab=tl_vocab
        
    def set_subword_type(self,subword_type):
        self.subword_type=subword_type
        
    def set_subword_model(self,subword_model):
        self.subword_model=subword_model
        self.tokenizer=SentencePieceTokenizer()
        self.tokenizer.set_spmodel(self.subword_model)
        
        
    def start_marian_server():
        printLOG(1, "START MT ENGINE:", config.startMarianCommand)
        os.system(config.startMarianCommand)


    def connect_to_Marian(self):
        printLOG(1,"CONNECT TO MARIAN.","")
        from websocket import create_connection
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            conn=s.connect_ex((config.MarianIP, config.MarianPort))
            if conn == 0:marianstarted=True
        service="ws://"+config.MarianIP+":"+str(config.MarianPort)+"/translate"
        error=True
        while error:
            try:
                config.ws = create_connection(service)
                printLOG(1,"Connection with Marian Server created","")
                error=False
            except:
                printLOG(1,"Error: waiting for Marian server to start. Retrying in 2 seconds.",sys.exc_info())
                time.sleep(2)
                error=True
                
    def translate(self,text):
        self.alternate_translations=[]
        self.tokenized=self.tokenizer.tokenize(text)
        #self.translation = self.translator.translate_batch([self.tokenized[0]],beam_size=self.beam_size,num_hypotheses=self.num_hypotheses)
        try:
            config.ws.send(self.tokenized)
        except:
            printLOG(1,"Error sending segment to Marian.",sys.exc_info())
        translations = config.ws.recv()
        tc_aux=translations.split("\n")
        for i in range(0,len(tc_aux)-1):
            segmentaux=tc_aux[i].split(" ||| ")[1].strip()
            alignmentaux=tc_aux[i].split(" ||| ")[2].strip()
            self.alternate_translation={}
            self.alternate_translation["tgt_tokens"]=segmentaux
            self.alternate_translation["tgt_subwords"]=segmentaux
            self.alternate_translation["alignment"]=alignmentaux
            self.alternate_translation["tgt"]=self.tokenizer.detokenize(segmentaux)
            self.alternate_translations.append(self.alternate_translation)

        self.response={}
        
        self.response["src_tokens"]=self.tokenized
        self.response["tgt_tokens"]=self.alternate_translations[0]["tgt_tokens"]
        self.response["src_subwords"]=self.tokenized
        self.response["tgt_subwords"]=self.alternate_translations[0]["tgt_tokens"]
        self.response["tgt"]=self.alternate_translations[0]["tgt"]
        self.response["alignment"]=self.alternate_translations[0]["alignment"]
        self.response["alternate_translations"]=self.alternate_translations
        return(self.response)
        
    
def translate_segment_Marian(segmentPre):
    translation_candidates={}
    translation_candidates["segmentNOTAGSPre"]=segmentPre
    lseg=len(segmentPre)
    try:
        config.ws.send(segmentPre)
    except:
        printLOG(1,"Error sending segment to Marian.",sys.exc_info())
    #translations = config.ws.recv()
    '''
    tc_aux=translations.split("\n")
    translation_candidates["translationNOTAGSPre"]=[]
    translation_candidates["alignments"]=[]
    for tca in tc_aux:
        printLOG(3,"TCA:",tca)
        try:
            segmentaux=tca.split(" ||| ")[1].strip()
            alignmentaux=tca.split(" ||| ")[2].strip()
            translation_candidates["translationNOTAGSPre"].append(segmentaux)
            translation_candidates["alignments"].append(alignmentaux)
        except:
            pass
    '''
    alternate_translations=[]
    translations = config.ws.recv()
    tc_aux=translations.split("\n")
    for i in range(0,len(tc_aux)-1):
        segmentaux=tc_aux[i].split(" ||| ")[1].strip()
        alignmentaux=tc_aux[i].split(" ||| ")[2].strip()
        alternate_translation={}
        alternate_translation["tgt_tokens"]=segmentaux
        alternate_translation["alignments"]=alignmentaux
        alternate_translation["tgt"]="None"
        #if alternate_translation["translation"].startswith(" ") and not text.startswith(" "): alternate_translation["translation"]=alternate_translation["translation"][1:]
        alternate_translations.append(alternate_translation)

    response={}
    response["src_tokens"]=segmentPre
    response["tgt_tokens"]=alternate_translations[0]["tgt_tokens"]
    response["tgt"]="None"
    response["alignments"]=alternate_translations[0]["alignments"]
    response["alternate_translations"]=alternate_translations
    return(response)

    #return(translation_candidates)
