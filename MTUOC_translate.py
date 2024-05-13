#    MTUOC_translate v 2402
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

import config
import sys
import re
import string as stringmodule


import srx_segmenter

from MTUOC_misc import printLOG
from MTUOC_misc import capitalizeMTUOC

if config.MTUOCServer_MTengine=="Marian":
    from MTUOC_Marian import translate_segment_Marian
if config.MTUOCServer_MTengine=="GoogleTranslate":
    from MTUOC_GoogleTranslate import Google_translate
if config.MTUOCServer_MTengine=="DeepL":
    from MTUOC_DeepL import DeepL_translate
if config.MTUOCServer_MTengine=="Lucy":
    from MTUOC_Lucy import Lucy_translate

from MTUOC_Moses import translate_segment_Moses

from MTUOC_preprocess import preprocess_segment
from MTUOC_preprocess import postprocess_segment
from MTUOC_preprocess import postprocess_translation
#from MTUOC_preprocess import restore_EMAILs
#from MTUOC_preprocess import restore_URLs
#from MTUOC_preprocess import restore_NUMs

from MTUOC_preprocess import tokenizationSL
from MTUOC_preprocess import tokenizationTL
from MTUOC_preprocess import detokenizationSL
from MTUOC_preprocess import detokenizationTL

def segmenta(cadena):
    segmenter = srx_segmenter.SrxSegmenter(config.rules[config.SRXlang],cadena)
    segments=segmenter.extract()
    resposta=[]
    return(segments)
    
def is_first_letter_upper(segment):
    for character in segment:
        if character.isalpha() and character.isupper():
            return(True)
        elif character.isalpha() and character.islower():
            return(False)
    return(False)

def upper_case_first_letter(segment):
    pos=0
    for character in segment:
        if character.isalpha() and character.islower():
            llista=list(segment)
            llista[pos]=llista[pos].upper()
            segment="".join(llista)
            return(segment)
        elif character.isalpha() and character.isupper():
            return(segment)
        pos+=1
    return(segment)
    
###URLs EMAILs

def remove_tags(segment):
        segmentnotags=re.sub('(<[^>]+>)', "",segment)
        segmentnotags=re.sub('({[0-9]+})', "",segmentnotags)
        segmentnotags=" ".join(segmentnotags.split())
        return(segmentnotags)

def findEMAILs(string):
    email=re.findall('\S+@\S+', string)
    email2=[]
    for em in email: 
        if em[-1] in stringmodule.punctuation: em=em[0:-1]
        em=remove_tags(em)
        email2.append(em)
    return email2

'''
def findURLs(string): 
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string)       
    return [x[0] for x in url] 
'''

def findURLs(text):
    # Regular expression for identifying URLs
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    # Find all matches using the regular expression
    matches = re.findall(url_pattern, text)
    return(matches)

def replace_EMAILs(string,code="@EMAIL@"):
    EMAILs=findEMAILs(string)   
    for EMAIL in EMAILs:
        string=string.replace(EMAIL,code)
    return(string)

def replace_URLs(string,code="@URL@"):
    URLs=findURLs(string)
    for URL in URLs:
        string=string.replace(URL,code)
    return(string)
    
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
    equil={}
    for xifra in xifres:
        xifrastr=str(xifra)
        xifrasplit=xifra.split()
        xifra2=joiner.join(xifra)
        segment=segment.replace(xifra,xifra2)
        if xifra2.find(" ")>-1:
            equil[xifra2]=xifra
    return(segment,equil)
    
def desplitnumbers(segment,equil):
    for xifra2 in equil:
        segment=segment.replace(xifra2,equil[xifra2])
    return(segment)


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

def translate_para(paragraph):
    if config.segment_input:
        (segments,separators)=segmenta(paragraph)
        translations=[]
        src_tokens=[]
        tgt_tokens=[]
        alignments=[]
        alternate_translations=[]
        for i in range(0,len(segments)):
            segment=segments[i]
            separator=separators[i]
            translation=translate_segment(segment)
            alternate_translations.append(translation)
            translations.append(translation["tgt"])
            src_tokens.append(translation["src_tokens"])
            tgt_tokens.append(translation["tgt_tokens"])
            alignments.append(translation["alignments"])       
            
            if config.fix_xml:
                try:
                    translation["tgt"]=config.tagrestorer.fix_xml_tags(translation["tgt"])
                except:
                    translation["tgt"]=translation["tgt"]
        translationstr=separators[0]
        src_token=separators[0]
        tgt_token=separators[0]
        alignment=separators[0]
        for i in range(0,len(segments)):
            translationstr+=translations[i]+separators[i+1]
            src_token+=src_tokens[i]+separators[i+1]
            tgt_token+=tgt_tokens[i]+separators[i+1]
            alignment+=alignments[i]+separators[i+1]
            
        translation={}
        translation["tgt"]=translationstr
        translation["src_tokens"]=src_token
        translation["tgt_tokens"]=tgt_token
        translation["alignments"]=alignment
        translation["alternate_translations"]=alternate_translations
        
    else:

        translation=translate_segment(paragraph)
    return(translation)


def change_output(translation):
    if not config.change_output_files[0]=="None":
        printLOG(3,"CHANGES OUTPUT:")
        printLOG(3,"ORIGINAL:",translation['tgt'])
        for change in config.changes_output:
            tofind=change[0]
            tochange=change[1]
            regexp="\\b"+tofind+"\\b"
            trobat=re.findall(regexp,translation['tgt'])
            if trobat: 
                translation['tgt']=re.sub(regexp, tochange, translation['tgt'])
                printLOG(3,tofind,tochange)
            for i in range(0,len(translation["alternate_translations"])):
                trobat=re.findall(regexp,translation["alternate_translations"][i]['tgt'])
                if trobat: 
                    translation["alternate_translations"][i]['tgt']=re.sub(regexp, tochange, translation["alternate_translations"][i]['tgt'])
                
        printLOG(3,"CHANGED:",translation['tgt'])
    return(translation)
    

def change_translation(translation):
    if not config.change_translation_files[0]=="None":
        printLOG(3,"CHANGES TRANSLATION:")
        printLOG(3,"ORIGINAL SOURCE:",translation['src'])
        printLOG(3,"ORIGINAL TARGET:",translation['tgt'])
        for change in config.changes_translation:
            try:
                tofindSOURCE=change[0]
                tofindTARGET=change[1]
                tochange=change[2]
                regexpSOURCE="\\b"+tofindSOURCE+"\\b"
                regexpTARGET="\\b"+tofindTARGET+"\\b"
                trobatSOURCE=re.findall(regexpSOURCE,translation['src'])
                trobatTARGET=re.findall(regexpTARGET,translation['tgt'])
                if trobatSOURCE and trobatTARGET: 
                    translation['tgt']=re.sub(regexpTARGET, tochange, translation['tgt'])
                    trobat=re.findall(regexp,translation["alternate_translations"][i]['tgt'])
                    printLOG(3,tofindTARGET,tochange)
                for i in range(0,len(translation["alternate_translations"])):
                    trobatSOURCE=re.findall(regexpSOURCE,translation['src'])
                    trobatTARGET=re.findall(regexpTARGET,translation['src'])
                    if trobatSOURCE and trobatTARGET: 
                        translation=re.sub(regexpTARGET, tochange, translation['src'])
                        printLOG(3,tofindTARGET,tochange)           
            except:
                pass
        printLOG(3,"CHANGED TARGET:",translation['tgt'])
    return(translation)
    
def translate_segment(segment):
    toupperfinal=False
    config.segmentORIG=segment
    config.segmentNOTAGS=config.tagrestorer.remove_tags(config.segmentORIG)
    printLOG(3,"segmentORIG",config.segmentORIG)
    printLOG(3,"segmentNOTAGS",config.segmentNOTAGS)
    config.hastags=config.tagrestorer.has_tags(segment)
    config.originaltags=config.tagrestorer.get_tags(segment)
    printLOG(3,"HAS TAGS",config.hastags)
    printLOG(3,"TAGS",config.originaltags)
    if not config.change_input_files[0]=="None":
        printLOG(3,"CHANGES INPUT:")
        printLOG(3,"ORIGINAL:",config.segmentORIG)
        for change in config.changes_input:
            tofind=change[0]
            tochange=change[1]
            regexp="\\b"+tofind+"\\b"
            trobat=re.findall(regexp,config.segmentORIG)
            if trobat:    
                config.segmentORIG=re.sub(regexp, tochange, config.segmentORIG)
                printLOG(3,tofind,tochange)
        printLOG(3,"CHANGED:",config.segmentORIG)
    if config.MTUOCServer_MTengine=="Marian":
        if config.hastags:
            (config.segmentTAGSMOD,config.TAGSEQUIL)=config.tagrestorer.replace_tags(config.segmentORIG)
            (config.segmentNOTIF,config.STARTINGTAG,config.CLOSINGTAG)=config.tagrestorer.remove_start_end_tag(config.segmentTAGSMOD)
            printLOG(3,"segmentNOTIF",config.segmentNOTIF)
            printLOG(3,"STARTINGTAG",config.STARTINGTAG)
            printLOG(3,"CLOSINGTAG",config.CLOSINGTAG)
        else:
            config.segmentTAGSMOD=config.segmentORIG
            config.TAGSEQUIL={}
            config.segmentNOTIF=config.segmentORIG
            config.STARTINGTAG=""
            config.CLOSINGTAG=""
        
            
        
    else:
        if config.remove_tags:
            config.segmentTAGSMOD=config.segmentNOTAGS
            
        else:
            config.segmentTAGSMOD=config.segmentORIG
        config.TAGSEQUIL={}
    

    if config.checkistranslatable:
        printLOG(3,"Checking if is translatable:","")
        try:
            segmentverificar=replace_URLs(config.segmentNOTAGS,config.code_URLs)
            segmentverificar=replace_EMAILs(segmentverificar,config.code_EMAILs)
            segmentverificar=config.tagrestorer.remove_tags(segmentverificar)
            tokens=tokenizationSL(segmentverificar)
            if not is_translatable(tokens): 
                printLOG(3,"segment not translatable",segment)
                response={}
                response["src"]=segment
                response["src_tokens"]="None"
                response["tgt_tokens"]="None"
                response["tgt"]=segment
                response["alignments"]="None"
                response["alternate_translations"]=[]
                return(response)
        except:
            printLOG(3,"ERROR cheking if is translatable:",sys.exc_info())
    if config.detect_language and not config.fasttext_model==None:
        printLOG(3,"Detecting language:","")
        try:
            DL1=config.modelFT.predict(config.segmentNOTAGS.replace("\n",""), k=1)
            L1=DL1[0][0].replace("__label__","")
            confL1=DL1[1][0]
            printLOG(1,"Detected language:",L1)
            printLOG(1,"Language detection confidence:",confL1)
            if not L1==config.sl_lang:#_lang and confL1>=config.fasttext_min_confidence:
                response={}
                response["src"]=segment
                response["src_tokens"]="None"
                response["tgt_tokens"]="None"
                response["tgt"]=segment
                response["alignments"]="None"
                response["alternate_translations"]=[]
                return(response)
        except:
            printLOG(3,"ERROR detecting language:",sys.exc_info())
    if config.MTUOCServer_MTengine=="Marian":
        config.segmentTOTRANSLATE=config.segmentNOTIF
    else:
        config.segmentTOTRANSLATE=config.segmentTAGSMOD
    if not config.change_input_files[0]=="None":
        printLOG(3,"CHANGES INPUT:")
        printLOG(3,"ORIGINAL:",config.segmentTOTRANSLATE)
        segmentcanvis=config.segmentTOTRANSLATE
        
        for change in config.changes_input:
            tofind=change[0]
            tochange=change[1]
            regexp="\\b"+tofind+"\\b"
            trobat=re.findall(regexp,segment)
            if trobat:    
                segmentcanvis=re.sub(regexp, tochange, segmentcanvis)
                printLOG(3,tofind,tochange)
        config.segmentTOTRANSLATE=segmentcanvis
        printLOG(3,"CHANGED:",config.segmentTOTRANSLATE)
    config.segmentNOTAGS=config.tagrestorer.remove_tags(config.segmentTOTRANSLATE)
    if config.MTUOCServer_MTengine=="OpusMT":
        try:
            printLOG(3,"Translating with OpusMT:",config.segmentTOTRANSLATE)
            config.translation=config.OpusMT_translator.translate(config.segmentTOTRANSLATE)
            printLOG(3,"Translation:",config.translation)
        except:
            printLOG(3,"Error translating segment with OpusMT",sys.exc_info())
        return(config.translation)
        
    if config.MTUOCServer_MTengine=="NLLB":
        try:
            printLOG(3,"Translating with NLLB:",config.segmentTOTRANSLATE)
            config.translation=config.NLLB_translator.translate(config.segmentTOTRANSLATE)
            printLOG(3,"Translation:",config.translation)
        except:
            printLOG(3,"Error translating segment with NLLB",sys.exc_info())
        return(config.translation)
    
    if config.MTUOCServer_MTengine=="Softcatalà":
        try:
            printLOG(3,"Translating with Softcatalà:",config.segmentTOTRANSLATE)
            config.translation=config.softcatala_translator.translate(config.segmentTOTRANSLATE)
            printLOG(3,"Translation:",config.translation)
        except:
            printLOG(3,"Error translating segment with Softcatalà",sys.exc_info())
        return(config.translation)
        
    if config.MTUOCServer_MTengine=="Aina":
        try:
            printLOG(3,"Translating with Aina:",config.segmentTOTRANSLATE)
            config.translation=config.aina_translator.translate(config.segmentTOTRANSLATE)
            printLOG(3,"Translation:",config.translation)
        except:
            printLOG(3,"Error translating segment with Aina",sys.exc_info())
        return(config.translation)
        
    if config.MTUOCServer_MTengine=="GoogleTranslate":
        printLOG(3,"Translating with GoogleTranslate:",config.segmentTOTRANSLATE)
        config.translation=Google_translate(config.segmentTOTRANSLATE)
        printLOG(3,"Translation:",config.translation)
        return(config.translation)

        
    if config.MTUOCServer_MTengine=="DeepL":
        printLOG(3,"Translating with DeepL:",config.segmentTOTRANSLATE)
        config.translation=DeepL_translate(segment)
        printLOG(3,"Translation:",config.translation)
        return(config.translation)
        
    elif config.MTUOCServer_MTengine=="Lucy":
        printLOG(3,"Translating with Lucy:",config.segmentTOTRANSLATE)
        translation=Lucy_translate(segment)
        printLOG(3,"Translation:",translation)
        return(translation)
        
    if config.MTUOCServer_MTengine=="Marian":
        
        if config.remove_tags:
            config.segmentTOTRANSLATE=config.segmentNOTAGS
        if config.replace_EMAILs:
            config.segmentTOTRANSLATE=replace_EMAILs(config.segmentTOTRANSLATE,config.code_EMAILs)
            printLOG(3,"Replacing EMAILs:",config.segmentTOTRANSLATE)
        
        if config.replace_URLs: 
            config.segmentTOTRANSLATE=replace_URLs(config.segmentTOTRANSLATE,config.code_URLs)
            printLOG(3,"Replacing URLs:",config.segmentTOTRANSLATE)
        
        if config.replace_NUMs: 
            config.segmentTOTRANSLATE=replace_NUMs(config.segmentTOTRANSLATE,config.code_NUMs)
            printLOG(3,"Replacing NUMs:",config.segmentTOTRANSLATE)
            
        if config.split_NUMs:
            config.segmentTOTRANSLATE=split_NUMs(config.segmentTOTRANSLATE,config.code_NUMs)
            printLOG(3,"Splitting NUMs:",config.segmentTOTRANSLATE)

        printLOG(3,"Preprocessing segment: ",config.segmentTOTRANSLATE)
        config.segmentTOTRANSLATE=preprocess_segment(config.segmentTOTRANSLATE)
        if not config.multilingual=="None":
            config.segmentTOTRANSLATE=config.multilingual+" "+config.segmentTOTRANSLATE
            print("***config.segmentTOTRANSLATE",config.segmentTOTRANSLATE)
        config.translationPRE=translate_segment_Marian(config.segmentTOTRANSLATE)
        printLOG(3,"Translation PRE",config.translationPRE)
        config.translationPOST=postprocess_translation(config.translationPRE)
        printLOG(3,"Translation POST",config.translationPOST)
        config.translation=config.translationPOST
        config.translation['src']=config.segmentORIG
        if not config.translation['tgt'][0]==config.translation['tgt'][0].upper() and config.segmentNOTAGS[0]==config.segmentNOTAGS[0].upper():
            toupperfinal=True        
        if toupperfinal:
            config.translation['tgt']=config.translation['tgt'][0].upper()+config.translation['tgt'][1:]
        if config.hastags and config.restore_tags:
            printLOG(3,"Restoring tags","")
            SOURCENOTAGSTOK=config.translation['src_tokens']
            segmentNOTIFMOD=replace_EMAILs(config.segmentNOTIF)
            segmentNOTIFMOD=replace_URLs(segmentNOTIFMOD)
            SOURCETAGSTOK=preprocess_segment(config.tagrestorer.addspacetags(segmentNOTIFMOD))
            SELECTEDALIGNMENT=config.translation['alignments']
            TARGETNOTAGSTOK=config.translation['tgt_tokens']
            printLOG(3,"SOURCENOTAGSTOK",SOURCENOTAGSTOK)
            printLOG(3,"SOURCETAGSTOK",SOURCETAGSTOK)
            printLOG(3,"SELECTEDALIGNMENT",SELECTEDALIGNMENT)
            printLOG(3,"TARGETNOTAGSTOK",TARGETNOTAGSTOK)
            config.translation['tgt']=config.tagrestorer.restore_tags(SOURCENOTAGSTOK, SOURCETAGSTOK, SELECTEDALIGNMENT, TARGETNOTAGSTOK)
            config.translation['tgt']=config.spTL.decode(config.translation['tgt'].split())
            if config.tokenizerSL and not config.tokenizerTL==None:
                config.translation['tgt']=config.tokenizerTL.detokenize(config.translation['tgt'])
        config.translation['tgt']=config.leading_spaces*" "+config.translation['tgt']+config.trailing_spaces*" "
        config.translation['tgt']=config.STARTINGTAG+config.translation['tgt']+config.CLOSINGTAG
        if config.hastags:
            for t in config.TAGSEQUIL:
                try:
                    config.translation['tgt']=config.translation['tgt'].replace(t,config.TAGSEQUIL[t],1)
                except:
                    pass
            config.translation['tgt']=config.tagrestorer.repairSpacesTags(config.segmentORIG,config.translation['tgt']) 
        if config.replace_EMAILs:
            config.translation['tgt']=restore_EMAILs(config.segmentORIG,config.translation['tgt'],code=config.code_EMAILs)
        
        if config.replace_URLs:
            config.translation['tgt']=restore_URLs(config.segmentORIG,config.translation['tgt'],code=config.code_URLs)
        if config.segmentNOTAGS==config.segmentNOTAGS.upper() and config.truecase in ["upper","all"]:
            toupperfinal=True
            toreplace={}
            for t in config.originaltags:
                toreplace[t.upper()]=t
            config.translation['tgt']=config.translation['tgt'].upper()
            for t in toreplace:
                config.translation['tgt']=config.translation['tgt'].replace(t,toreplace[t],1)
        ###CHECKING FINAL TAGS
        finaltags=config.tagrestorer.get_tags(config.translation['tgt'])
        checktags=config.originaltags
        controlcheck=True
        for tag in finaltags:
            try:
                checktags.remove(tag)
            except:
                controlcheck=False
                pass
        if len(checktags)>0 and controlcheck:
            print("ERROR RETRIEVING TAGS. ACTION:",config.missing_tags)
            if config.missing_tags=="ignore":
                pass
            elif config.missing_tags=="add_beginning":
                for tag in checktags:
                    config.translation['tgt']=tag+config.translation['tgt']
            elif config.missing_tags=="add_end":
                for tag in checktags:
                    config.translation['tgt']=config.translation['tgt']+tag
            elif config.missing_tags=="delete_all":
                config.translation['tgt']=config.tagrestorer.remove_tags(config.translation['tgt'])
        #Now for all the alternate_translations        
        for i in range(0,len(config.translation["alternate_translations"])):
            if toupperfinal:
                try:
                    config.translation["alternate_translations"][i]['tgt']=config.translation["alternate_translations"][i]['tgt'][0].upper()+config.translation["alternate_translations"][i]['tgt'][1:]
                except:
                    pass
            
            try:
                if config.hastags and config.restore_tags:
                    SOURCENOTAGSTOK=config.translation['src_tokens']
                    SOURCETAGSTOK=preprocess_segment(config.tagrestorer.addspacetags(config.segmentNOTIF))
                    SELECTEDALIGNMENT=config.translation["alternate_translations"][i]['alignments']
                    TARGETNOTAGSTOK=config.translation["alternate_translations"][i]['tgt_tokens']
                    config.translation["alternate_translations"][i]['tgt']=config.tagrestorer.restore_tags(SOURCENOTAGSTOK, SOURCETAGSTOK, SELECTEDALIGNMENT, TARGETNOTAGSTOK)
                    config.translation["alternate_translations"][i]['tgt']=config.spTL.decode(config.translation["alternate_translations"][i]['tgt'].split())
                    if config.tokenizerSL and not config.tokenizerTL==None:
                        config.translation["alternate_translations"][i]['tgt']=config.tokenizerTL.detokenize(config.translation["alternate_translations"][i]['tgt'])
                config.translation["alternate_translations"][i]['tgt']=config.leading_spaces*" "+config.translation["alternate_translations"][i]['tgt']+config.trailing_spaces*" "
                config.translation["alternate_translations"][i]['tgt']=config.STARTINGTAG+config.translation["alternate_translations"][i]['tgt']+config.CLOSINGTAG
                for t in config.TAGSEQUIL:
                    try:
                        config.translation["alternate_translations"][i]['tgt']=config.translation["alternate_translations"][i]['tgt'].replace(t,config.TAGSEQUIL[t],1)
                    except:
                        pass
                config.translation["alternate_translations"][i]['tgt']=config.tagrestorer.repairSpacesTags(config.segmentORIG,config.translation["alternate_translations"][i]['tgt']) 
                if config.replace_EMAILs:
                    config.translation["alternate_translations"][i]['tgt']=restore_EMAILs(config.segmentORIG,config.translation["alternate_translations"][i]['tgt'],code=config.code_EMAILs)
                if config.replace_URLs:
                    config.translation["alternate_translations"][i]['tgt']=restore_URLs(config.segmentORIG,config.translation["alternate_translations"][i]['tgt'],code=config.code_URLs)
                if config.segmentNOTAGS==config.segmentNOTAGS.upper() and config.truecase in ["upper","all"]:
                    toreplace={}
                    for t in config.originaltags:
                        toreplace[t.upper()]=t
                    config.translation["alternate_translations"][i]['tgt']=config.translation["alternate_translations"][i]['tgt'].upper()
                    for t in toreplace:
                        config.translation["alternate_translations"][i]['tgt']=config.translation["alternate_translations"][i]['tgt'].replace(t,toreplace[t],1)
                        
                ####CHECKING TAGS
                ###CHECKING FINAL TAGS
                finaltags=config.tagrestorer.get_tags(config.translation["alternate_translations"][i]['tgt'])
                checktags=config.originaltags
                controlcheck=True
                for tag in finaltags:
                    try:
                        checktags.remove(tag)
                    except:
                        controlcheck=False
                        pass
                if len(checktags)>0 and controlcheck:
                    print("ERROR RETRIEVING TAGS. ACTION:",config.missing_tags)
                    if config.missing_tags=="ignore":
                        pass
                    elif config.missing_tags=="add_beginning":
                        for tag in checktags:
                            config.translation["alternate_translations"][i]['tgt']=tag+config.translation["alternate_translations"][i]['tgt']
                    elif config.missing_tags=="add_end":
                        for tag in checktags:
                            config.translation["alternate_translations"][i]['tgt']=config.translation["alternate_translations"][i]['tgt']+tag
                    elif config.missing_tags=="delete_all":
                        config.translation["alternate_translations"][i]['tgt']=config.tagrestorer.remove_tags(config.translation["alternate_translations"][i]['tgt'])
                
            except:
                print("Error MTUOC_translate alternate translations",sys.exc_info())
            
        config.translation=change_output(config.translation)    
        config.translation=change_translation(config.translation)    
        printLOG(3,"Translation:",config.translation)
        return(config.translation)    

    
def is_translatable(tokens):    
    translatable=False
    for token in tokens.split():
        transtoken=True
        for character in token:
            if str(character) in ["0","1","2","3","4","5","6","7","8","9"]:
                transtoken=False
                break
        if transtoken:
            translatable=True
    return(translatable) 

def select_best_candidate(translation_candidates,strategy):
    '''To implement several strategies to select the best candidate. Now it r,eturns the first one.'''
    if strategy=="First":
        best_translation=translation_candidates["translationTAGS"][0]
    return(best_translation)

    

  
