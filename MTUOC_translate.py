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
import regex
import unicodedata
import html
from ftfy import fix_encoding

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
if config.MTUOCServer_MTengine=="Apertium":
    from ApertiumTranslator import ApertiumTranslator


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
    
def remove_control_characters(cadena):
    return regex.sub(r'\p{C}', '', cadena)
    
def is_printable(char):
    category = unicodedata.category(char)
    return not (category.startswith('C') or category in ['Zl', 'Zp', 'Cc'])
    
def remove_non_printable(string):
    cleaned_string = ''.join(c for c in string if is_printable(c))
    return(cleaned_string)
    
def remove_non_latin_extended_chars(text):
    # Define the pattern to match only allowed characters
    # This includes basic Latin letters, Latin Extended characters, spaces, and common punctuation marks
    #pattern = re.compile(r'''[^0-9A-Za-z\u00C0-\u00FF\u0100-\u024F\u1E00-\u1EFF\uA720-\uA7FF\s.,:;!?'"“”‘’«»()\-@#\$%\^&\*\+\/\\_\|~<>{}\[\]=]''', re.VERBOSE)
    pattern = re.compile(r'''[^0-9\s.,:;!?'"“”‘’«»()\-@#\$%\^&\*\+\/\\_\|~<>{}\[\]=]\u0000-\u007F\u0080-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\u2C60-\u2C7F\uA720-\uA7FF\uAB30-\uAB6F''', re.VERBOSE)
    cleaned_text = pattern.sub('', text)
    return cleaned_text

def remove_non_unicode_script_chars(text):
    """
    Remove characters that are not in the specified Unicode ranges for all scripts.

    Parameters:
    text (str): The input text to be cleaned.

    Returns:
    str: The cleaned text with only allowed characters.
    """
    # Define the pattern to match only allowed characters from all Unicode scripts
    pattern = re.compile(r'''[^\u0000-\u007F\u0080-\u00FF\u0100-\u017F\u0180-\u024F\u0250-\u02AF\u02B0-\u02FF
                             \u0300-\u036F\u0370-\u03FF\u0400-\u04FF\u0500-\u052F\u0530-\u058F\u0590-\u05FF
                             \u0600-\u06FF\u0700-\u074F\u0750-\u077F\u0780-\u07BF\u07C0-\u07FF\u0800-\u083F
                             \u0840-\u085F\u0860-\u086F\u08A0-\u08FF\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F
                             \u0A80-\u0AFF\u0B00-\u0B7F\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF\u0D00-\u0D7F
                             \u0D80-\u0DFF\u0E00-\u0E7F\u0E80-\u0EFF\u0F00-\u0FFF\u1000-\u109F\u10A0-\u10FF
                             \u1100-\u11FF\u1200-\u137F\u1380-\u139F\u13A0-\u13FF\u1400-\u167F\u1680-\u169F
                             \u16A0-\u16FF\u1700-\u171F\u1720-\u173F\u1740-\u175F\u1760-\u177F\u1780-\u17FF
                             \u1800-\u18AF\u18B0-\u18FF\u1900-\u194F\u1950-\u197F\u1980-\u19DF\u19E0-\u19FF
                             \u1A00-\u1A1F\u1A20-\u1AAF\u1AB0-\u1AFF\u1B00-\u1B7F\u1B80-\u1BBF\u1BC0-\u1BFF
                             \u1C00-\u1C4F\u1C50-\u1C7F\u1C80-\u1C8F\u1C90-\u1CBF\u1CC0-\u1CCF\u1CD0-\u1CFF
                             \u1D00-\u1D7F\u1D80-\u1DBF\u1DC0-\u1DFF\u1E00-\u1EFF\u1F00-\u1FFF\u2000-\u206F
                             \u2070-\u209F\u20A0-\u20CF\u20D0-\u20FF\u2100-\u214F\u2150-\u218F\u2190-\u21FF
                             \u2200-\u22FF\u2300-\u23FF\u2400-\u243F\u2440-\u245F\u2460-\u24FF\u2500-\u257F
                             \u2580-\u259F\u25A0-\u25FF\u2600-\u26FF\u2700-\u27BF\u27C0-\u27EF\u27F0-\u27FF
                             \u2800-\u28FF\u2900-\u297F\u2980-\u29FF\u2A00-\u2AFF\u2B00-\u2BFF\u2C00-\u2C5F
                             \u2C60-\u2C7F\u2C80-\u2CFF\u2D00-\u2D2F\u2D30-\u2D7F\u2D80-\u2DDF\u2DE0-\u2DFF
                             \u2E00-\u2E7F\u2E80-\u2EFF\u2F00-\u2FDF\u2FF0-\u2FFF\u3000-\u303F\u3040-\u309F
                             \u30A0-\u30FF\u3100-\u312F\u3130-\u318F\u3190-\u319F\u31A0-\u31BF\u31C0-\u31EF
                             \u31F0-\u31FF\u3200-\u32FF\u3300-\u33FF\u3400-\u4DBF\u4DC0-\u4DFF\u4E00-\u9FFF
                             \uA000-\uA48F\uA490-\uA4CF\uA4D0-\uA4FF\uA500-\uA63F\uA640-\uA69F\uA6A0-\uA6FF
                             \uA700-\uA71F\uA720-\uA7FF\uA800-\uA82F\uA830-\uA83F\uA840-\uA87F\uA880-\uA8DF
                             \uA8E0-\uA8FF\uA900-\uA92F\uA930-\uA95F\uA960-\uA97F\uA980-\uA9DF\uA9E0-\uA9FF
                             \uAA00-\uAA5F\uAA60-\uAA7F\uAA80-\uAADF\uAAE0-\uAAFF\uAB00-\uAB2F\uAB30-\uAB6F
                             \uAB70-\uABBF\uABC0-\uABFF\uAC00-\uD7AF\uD7B0-\uD7FF\uD800-\uDB7F\uDB80-\uDBFF
                             \uDC00-\uDFFF\uE000-\uF8FF\uF900-\uFAFF\uFB00-\uFB4F\uFB50-\uFDFF\uFE00-\uFE0F
                             \uFE10-\uFE1F\uFE20-\uFE2F\uFE30-\uFE4F\uFE50-\uFE6F\uFE70-\uFEFF\uFF00-\uFFEF
                             \uFFF0-\uFFFF]''', re.VERBOSE)

    # Substitute non-matching characters with an empty string
    cleaned_text = pattern.sub('', text)

    return cleaned_text
    
    

def normalize_apos(segment):
    segment=segment.replace("’","'")
    segment=segment.replace("`","'")
    segment=segment.replace("‘","'")
    return(segment)
    
def unescape_html(segment):
    segmentUN=html.unescape(segment)
    return(segmentUN)
    
def unescape_html(segment):
    segmentUN=html.unescape(segment)
    return(segmentUN)

def translate_para(paragraph):
    if config.remove_control_characters:
        paragraph=remove_control_characters(paragraph)
    if config.remove_non_printable:
        paragraph=remove_non_printable(paragraph)
    if config.remove_non_latin_extended_chars:
        paragraph=remove_non_latin_extended_chars(paragraph)
    if config.remove_non_unicode_script_chars:
        paragraph=remove_non_unicode_script_chars(paragraph)
    if config.norm_apos:
        paragraph=normalize_apos(paragraph)
    if config.norm_apos:
        paragraph=unescape_html(paragraph)
    if config.fixencoding:
        paragraph=fix_encoding(paragraph)
    if config.escapeforMoses:
        paragraph=unescape_html(paragraph)
        
    if config.segment_input:
        try:
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
        except:
            print("****ERROR:",sys.exc_info())
        
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
        
    if config.MTUOCServer_MTengine=="NLLB":
        try:
            printLOG(3,"Translating with NLLB:",config.segmentTOTRANSLATE)
            config.translation=config.NLLB_translator.translate(config.segmentTOTRANSLATE)
            printLOG(3,"Translation:",config.translation)
        except:
            printLOG(3,"Error translating segment with NLLB",sys.exc_info())
        return(config.translation)
        
    if config.MTUOCServer_MTengine=="Apertium":
        try:
            printLOG(3,"Translating with Apertium:",config.segmentTOTRANSLATE)
            config.translation=config.apertium_translator.translate(config.segmentTOTRANSLATE)
            printLOG(3,"Translation:",config.translation)
        except:
            printLOG(3,"Error translating segment with NLLB",sys.exc_info())
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

    

  
