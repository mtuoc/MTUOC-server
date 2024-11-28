import config
import sys
from MTUOC_misc import printLOG
import re

if config.segment:
    from srx_segmenter import SrxSegmenter,parse

def merge_translations(translations):
    merged_translation={}
    srcM=[]
    tgtM=[]
    srcM_tokens=[]
    tgtM_tokens=[]
    srcM_subwords=[]
    tgtM_subwords=[]
    merged_translation["src"]=""
    merged_translation["tgt"]=""
    merged_translation["src_tokens"]=""
    merged_translation["tgt_tokens"]=""
    merged_translation["src_subwords"]=""
    merged_translation["tgt_subwords"]=""
    merged_translation["alignment"]="" 
    merged_translation["alternate_translations"]=[]

    contS=1
    for tr in translations:
        srcM.append(tr["src"])
        tgtM.append(tr["tgt"])
        
        srcM_tokens.append(tr["src_tokens"])
        tgtM_tokens.append(tr["tgt_tokens"])
        
        srcM_subwords.append(tr["src_subwords"])
        tgtM_subwords.append(tr["tgt_subwords"])
        

        
        merged_translation["alternate_translations"].append(tr)
        
        contS+=1
        
    srcM="".join(srcM)
    tgtM="".join(tgtM)
    merged_translation["src"]=srcM
    merged_translation["tgt"]=tgtM
    
    srcM_tokens="".join(srcM_tokens)
    tgtM_tokens="".join(tgtM_tokens)
    merged_translation["src_tokens"]=srcM_tokens
    merged_translation["tgt_tokens"]=srcM_tokens
    
    srcM_subwords="".join(srcM_subwords)
    tgtM_subwords="".join(tgtM_subwords)
    merged_translation["src_subwords"]=srcM_subwords
    merged_translation["tgt_subwords"]=srcM_subwords
    
    return(merged_translation)
        
    
def add_leading_trailing_spances(translation,lS,tS):
    translation["tgt"]=lS+translation["tgt"]+tS
    return(translation)
    
    

def translate_para(paragraph):
    printLOG(2,"PARAGRAPH:",paragraph)
    
    if config.fixencoding:
        paragraph=config.preprocessor.fix_encoding(paragraph)
    
    if config.remove_control_characters: paragraph=config.preprocessor.remove_control_characters(paragraph)
    if config.remove_non_printable: paragraph=config.preprocessor.remove_non_printable(paragraph)
    if config.remove_non_latin_extended_chars: paragraph=config.preprocessor.remove_non_latin_extended_chars(paragraph)
    if config.remove_non_unicode_script_chars: paragraph=config.preprocessor.remove_control_characters(paragraph)
    
    if config.unescape_html:
        paragraph=config.preprocessor.unescape_html(paragraph)
    
    if config.use_MosesPunctNormalizer:
        paragraph=config.mpn.normalize(paragraph)
    if config.change_input:
        paragraph=config.preprocessor.change_input(paragraph)
    
    config.translation["src"]=paragraph
    config.translation["tgt"]=""
    config.translation["src_tokens"]=""
    config.translation["tgt_tokens"]=""
    config.translation["src_subwords"]=""
    config.translation["tgt_subwords"]=""
    config.translation["alignment"]=""
    config.translation["alternate_translations"]=[]
    if not config.preprocessor.is_translatable(paragraph):
        config.translation["tgt"]=paragraph
        printLOG(2,"TRANSLATION PARAGRAPH:",config.translation["tgt"])
        return(config.translation)
    
    (lSpara,tSpara,sparagraph)=config.preprocessor.leading_trailing_spaces(paragraph)
    
    paralist=[sparagraph]
    try:
        if config.segment:
            for segmenter in config.segmenters:
                paralist=segmenter.segmentList(paralist)
            if config.splitlongsegments:
                paralist=config.preprocessor.split_long_strings(paralist,separators=config.separators, max_length=config.maxlong)
            translations=[]
            for segment in paralist:
                (lSsegment,tSsegment,ssegment)=config.preprocessor.leading_trailing_spaces(segment)
                if config.strategy=="bysegments":
                    translation_segment=translate_segment(ssegment)
                elif config.strategy=="bychunks":
                    translation_segment=translate_chunks(ssegment)
                    
                translation_segment=add_leading_trailing_spances(translation_segment,lSsegment,tSsegment)
                translations.append(translation_segment)
            translation=merge_translations(translations)
        else:
            translation=translate_segment(sparagraph)
        
    except:
        printLOG(2,"ERROR in MTUOC_translate translate_para:",sys.exc_info())
    translation=add_leading_trailing_spances(translation,lSpara,tSpara)
    printLOG(2,"TRANSLATION PARA:",translation["tgt"])
    return(translation)

def get_tag_chunks(input_str):
    # Regular expression to match HTML tags or text
    pattern = r'(<[^>]+>|[^<]+)'

    # Use re.findall to extract all matching parts
    parts = re.findall(pattern, input_str)

    return parts

def is_tag(tag):
    # Regular expression to match a valid XML tag
    pattern = r'^</?[a-zA-Z_][\w\-.]*(\s+[^<>]*)?\s*/?>$'
   
    # Use re.match to check if the tag matches the pattern
    return re.match(pattern, tag) is not None

def translate_chunks(segment):
    printLOG(2,"SEGMENT:",segment)
       
    config.src=segment
    config.translation={}
    config.casetype=config.preprocessor.analyze_segment_case(segment)
    
    config.translation["src"]=""
    config.translation["tgt"]=""
    config.translation["src_tokens"]=""
    config.translation["tgt_tokens"]=""
    config.translation["src_subwords"]=""
    config.translation["tgt_subwords"]=""
    config.translation["alignment"]=""
    config.translation["alternate_translations"]=[]
    config.src_modtags=config.src 
    if not config.preprocessor.is_translatable(segment):
        config.translation["tgt"]=segment
        printLOG(2,"TRANSLATION SEGMENT:",config.translation["tgt"])
        return(config.translation)
    translation=[]
    chunks=get_tag_chunks(config.src_modtags)
    printLOG(2,"CHUNKS:",chunks)
    for chunk in chunks:
        printLOG(2,"CHUNK:",chunk)
        if is_tag(chunk) or chunk.strip()=="":
            translation.append(chunk)
            printLOG(2,"TRANSLATION CHUNK:",chunk)
        else:
            translation_chunk=translate_string(chunk, chunk)
            translation.append(translation_chunk["tgt"])
            printLOG(2,"TRANSLATION CHUNK:",translation_chunk["tgt"])
    translation=" ".join(translation)+" "
    translation=config.postprocessor.repairSpacesTags(segment,translation)
    config.translation["tgt"]=translation
    printLOG(2,"TRANSLATION SEGMENT:",config.translation["tgt"])
    return(config.translation)
    
def translate_string(segment, segment_notags):
    if config.MTUOCServer_MTengine=="Marian":
        try:
            if config.remove_tags:
                translationSTR=config.MarianTranslator.translate(segment_notags)
            else:
                translationSTR=config.MarianTranslator.translate(segment)
        except:
            printLOG(2,"Error translating segment with Marian",sys.exc_info())

    if config.MTUOCServer_MTengine=="Aina":
        try:
            if config.remove_tags:
                translationSTR=config.AinaTranslator.translate(segment_notags)
            else:
                translationSTR=config.AinaTranslator.translate(segment)
        except:
            printLOG(2,"Error translating segment with Aina",sys.exc_info())
    
    
    if config.MTUOCServer_MTengine=="Transformers":
        try:
            if config.remove_tags:
                translationSTR=config.TransformersTranslator.translate(segment_notags)
            else:
                translationSTR=config.TransformersTranslator.translate(segment)
        except:
            printLOG(2,"Error translating segment with Transformers",sys.exc_info())
            
    if config.MTUOCServer_MTengine=="NLLB":
        try:
            if config.remove_tags:
                translationSTR=config.NLLB_translator.translate(segment_notags)
            else:
                translationSTR=config.NLLB_translator.translate(segment)
        except:
            printLOG(2,"Error translating segment with NLLB",sys.exc_info())
        return(translationSTR)
        
    if config.MTUOCServer_MTengine=="Softcatalà" or config.MTUOCServer_MTengine=="Softcatala":
        try:
            if config.remove_tags:
                translationSTR=config.softcatala_translator.translate(segment_notags)
            else:
                translationSTR=config.softcatala_translator.translate(segment)
        except:
            printLOG(2,"Error translating segment with Softcatalà",sys.exc_info())
        return(translationSTR)
            
    return(translationSTR)

def translate_segment(segment):
    printLOG(2,"SEGMENT:",segment)
    if config.multilingual:
        config.src=config.multilingual+" "+segment
    else:
        config.src=segment
    config.translation={}
    config.casetype=config.preprocessor.analyze_segment_case(segment)
    
    config.translation["src"]=""
    config.translation["tgt"]=""
    config.translation["src_tokens"]=""
    config.translation["tgt_tokens"]=""
    config.translation["src_subwords"]=""
    config.translation["tgt_subwords"]=""
    config.translation["alignment"]=""
    config.translation["alternate_translations"]=[]
    
    if not config.preprocessor.is_translatable(segment):
        config.translation["tgt"]=segment
        printLOG(2,"TRANSLATION SEGMENT:",config.translation["tgt"])
        return(config.translation)
    
    config.src_modtags=config.src
    if config.preprocessor.has_tags(config.src):
        config.src_notags=config.preprocessor.remove_tags(config.src)
        config.src_notags_tokens=config.tokenizerSL.tokenize(config.src_notags)
        config.src_tokens=config.preprocessor.addspacetags(config.src)
        config.src_tokens=config.tokenizerSL.tokenize(config.src_tokens)

    else:
        config.src_notags=config.src
        config.src_notags_tokens_=config.src_tokens
        config.src_tokens=config.src_notags_tokens
        
    dotruecase=False
    if config.truecase=="always": dotruecase=True
    elif config.truecase=="upper" and config.casetype=="upper": dotruecase=True
    if dotruecase:
        config.src_notags=config.truecaser.truecase(config.src_notags)    
    
    config.translation=translate_string(config.src, config.src_notags)
    
    if not config.GetWordAlignments_type==None:
        try:
            toaligntokensSL=config.GetWordAlignments_tokenizerSL.tokenize(config.src_notags)
            toaligntokensTL=config.GetWordAlignments_tokenizerTL.tokenize(config.translation["tgt"])
            alignment,sourceL,targetL=config.wordaligner.align_sentence_pair(toaligntokensSL,toaligntokensTL)
            config.translation["alignment"]=alignment
            config.translation["src_tokens"]=sourceL
            config.translation["tgt_tokens"]=targetL       
        except:
            printLOG(2,"ERROR MTUOC_translate translate_segment GetWordAlignments:",sys.exc_info())
            
        #try:
        '''
        contalternate=0
        for tr in config.translation["alternate_translations"]:
            toaligntokensSL=config.GetWordAlignments_tokenizerSL.tokenize(config.src_notags)
            toaligntokensTL=config.GetWordAlignments_tokenizerTL.tokenize(tr["tgt"])
            alignment,sourceL,targetL=config.wordaligner.align_sentence_pair(toaligntokensSL,toaligntokensTL)
            config.translation["alternate_translations"][contalternate]["alignment"]=alignment
            config.translation["alternate_translations"][contalternate]["src_tokens"]=sourceL
            config.translation["alternate_translations"][contalternate]["tgt_tokens"]=targetL
            contalternate+=1
        #except:
        #    print("ERROR MTUOC_translate translate_segment GetWordAlignments:",sys.exc_info())
        '''
    if config.restore_case and config.casetype=="upper":
        config.translation["tgt"]=config.translation["tgt"].upper()
        for tr in config.translation["alternate_translations"]:
            tr["tgt"]=tr["tgt"].upper()
    
    if config.restore_tags and config.strategy=="bysegments":
        try:
            config.postprocessor.insert_tags()
        except:
            printLOG(2,"Error postprocessing",sys.exc_info())
    config.translation["src"]=segment
    if config.numeric_check:
        config.translation["tgt"]=config.postprocessor.check_and_replace_numeric(config.translation["src"], config.translation["tgt"])
        '''
        for tr in config.translation["alternate_translations"]:
            tr["tgt"]=config.postprocessor.check_and_replace_numeric(config.translation["src"], tr["tgt"])
        '''
    if config.change_output:
        config.translation=config.postprocessor.change_output(config.translation)
    if config.change_translation:
        config.translation=config.postprocessor.change_translation(config.translation)
    printLOG(2,"TRANSLATION SEGMENT:",config.translation["tgt"])
    return(config.translation)    
