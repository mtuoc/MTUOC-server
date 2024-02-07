#    MTUOC_Marian v 2402
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



import websocket
import socket
import time
import sys
import config

from MTUOC_misc import printLOG


def connect_to_Marian():
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
