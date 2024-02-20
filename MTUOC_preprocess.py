#    MTUOC_preprocess v. 24.02
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



import config
from MTUOC_misc import printLOG
import regex as rx
import re
import html
import sys
import string as stringmodule


    
def remove_control_characters(cadena):
    return rx.sub(r'\p{C}', '', cadena)
    
re_num = re.compile(r'[\d,\.]+')

def replace_NUMs(segment,code="@NUM@"):
    trobatsEXPRNUM=re.finditer(re_num,segment)
    for trobat in trobatsEXPRNUM:
        if not trobat.group(0) in [".",","]:
            segment=segment.replace(trobat.group(0),code,1)
    return(segment)
    
def splitnumbers(segment,joiner=""):
    joiner=joiner+" "
    xifres = re.findall(re_num,segment)
    for xifra in xifres:
        xifrastr=str(xifra)
        xifrasplit=xifra.split()
        xifra2=joiner.join(xifra)
        segment=segment.replace(xifra,xifra2)
    return(segment)

def findEMAILs(string):
    try:
        email=re.findall('\S+@\S+', string)
        email2=[]
        for em in email: 
            if em[-1] in stringmodule.punctuation: em=em[0:-1]
            email2.append(em)
    except:
        print("ERROR:",sys.exc_info())
    return email2
    
def findURLs(string): 
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string)       
    return [x[0] for x in url] 

def restore_EMAILs(stringA,stringB,code="@EMAIL@"):
    EMAILs=findEMAILs(stringA)
    for email in EMAILs:
        stringB=stringB.replace(code,email,1)
    return(stringB)
    
def restore_URLs(stringA,stringB,code="@URL@"):
    URLs=findURLs(stringA)
    for url in URLs:
        stringB=stringB.replace(code,url,1)
    return(stringB)
    
def restore_NUMs(segmentSL,segmentTL,code="@NUM@"):
    trobatsEXPRNUM=re.finditer(re_num,segmentSL)
    position=0
    for trobat in trobatsEXPRNUM:
        if not trobat.group(0) in [".",","]:
            segmentTL=segmentTL.replace(code,trobat.group(0),1)
    return(segmentTL)

def preprocess_segment(segment):
    if config.escape_html_input:
        segment=html.escape(segment)
    if config.unescape_html_input:
        segment=html.unescape(segment)
    #segment=segment.replace(" <tag0>"," <tag0> ")
    #segment=segment.replace(" </tag0>"," </tag0> ")
    segment=remove_control_characters(segment) 
    
    #leading and trailing spaces
    config.leading_spaces=len(segment)-len(segment.lstrip())
    config.trailing_spaces=len(segment)-len(segment.rstrip())-1
    segment=segment.lstrip().rstrip()
    config.isupper=False
    if segment==segment.upper() and config.truecase in ["upper","all"]:
        segment=config.truecaser.truecase(segment, ucf=True, restoreCase=False)
        config.segmentNOTIF=config.truecaser.truecase(config.segmentNOTIF, ucf=True, restoreCase=False)
        printLOG(3,"TRUECASED:",segment)
        config.isupper=True
        config.detruecasePOST=True
    if config.replace_NUMs:
        segment=replace_NUMs(segment)
    if config.split_NUMs:
        segment=splitnumbers(segment)
    segment=tokenizationSL(segment)
    if config.sentencepiece:
        try:
            segmentPre=" ".join(config.spSL.encode(segment))
        except:
            printLOG(1,"ERROR preprocess segment:",sys.exc_info())
    else:
        segmentPre=segment
    return(segmentPre)


def postprocess_translation(translationData):
    translationData["tgt"]=postprocess_segment(translationData["tgt_tokens"])
    
    for i in range(0,len(translationData["alternate_translations"])):
        translationData["alternate_translations"][i]["tgt"]=postprocess_segment(translationData["alternate_translations"][i]["tgt_tokens"])
    return(translationData)
    
    
        

def postprocess_segment(segmentPre):
    segmentPost=segmentPre
    try:
        if config.sentencepiece:
            segmentPost=config.spTL.decode(segmentPre.split())
    except:
            printLOG(1,"ERROR preprocess segment:",sys.exc_info())
    if config.isupper and config.truecase in ["upper","all"]:
        segmentPost=segmentPost.upper()
    elif config.truecase in ["all"]:
        segmentPost=config.truecaser.truecase(segmentPost)
    if config.replace_EMAILs:
        segmentPost=restore_EMAILs(config.segmentORIG,segmentPost,code=config.code_EMAILs)
    if config.replace_URLs:
        segmentPost=restore_URLs(config.segmentORIG,segmentPost,code=config.code_URLs)
    segmentPost=detokenizationTL(segmentPost)
    return(segmentPost)

def tokenizationSL(segment):
    if config.tokenize_SL and not config.tokenizerSL==None:
        if config.tokenizerSLType=="MTUOC":
            tokens=config.tokenizerSL.tokenize(segment)
        elif config.tokenizerSLType=="Moses":
            tokens=" ".join(config.tokenizerSL(segment))        
    else:
        tokens=segment
    

    return(tokens)
        
def tokenizationTL(segment):
    if config.tokenize_TL and not config.tokenizerTL==None:
        tokens=config.tokenizerTL.tokenize(segment)
    else:
        tokens=segment  
    return(tokens)

def detokenizationSL(tokens):
    if not config.tokenizerSL==None:
        segment=config.tokenizerSL.detokenize(tokens)
    else:
        segment=tokens   
    return(tokens)
        
def detokenizationTL(tokens):
    if not config.tokenizerTL==None:
        segment=config.tokenizerTL.detokenize(tokens)
    else:
        segment=tokens   
    return(tokens)
