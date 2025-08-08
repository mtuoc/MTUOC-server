import config
import sys
from MTUOC_misc import printLOG
import re

if config.segment:
    from srx_segmenter import SrxSegmenter,parse

def merge_translations(translations):
    merged_translation={}
    if len(translations)==1:
        merged_translation["src"]=translations[0]["src"]
        merged_translation["tgt"]=translations[0]["tgt"]
        merged_translation["src_tokens"]=translations[0]["src_tokens"]
        merged_translation["tgt_tokens"]=translations[0]["tgt_tokens"]
        merged_translation["src_subwords"]=translations[0]["src_subwords"]
        merged_translation["tgt_subwords"]=translations[0]["tgt_subwords"]
        merged_translation["alignment"]=translations[0]["alignment"]
        merged_translation["alternate_translations"]=translations[0]["alternate_translations"]
    else:
        
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
        merged_translation["alternate_translations"]={}
        merged_translation["alternate_translations"]["tgt"]=[]
        merged_translation["alternate_translations"]["src_tokens"]=[]
        merged_translation["alternate_translations"]["tgt_tokens"]=[]
        merged_translation["alternate_translations"]["src_subwords"]=[]
        merged_translation["alternate_translations"]["tgt_subwords"]=[]
        

        contS=1
        for tr in translations:
            srcM.append(tr["src"])
            tgtM.append(tr["tgt"])
            
            srcM_tokens.append(tr["src_tokens"])
            tgtM_tokens.append(tr["tgt_tokens"])
            
            srcM_subwords.append(tr["src_subwords"])
            tgtM_subwords.append(tr["tgt_subwords"])

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
        merged_translation["alternate_translations"]=[]
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
    config.translation["system_name"]=config.system_name
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
                #if config.sentencepiece:
                #    ssegment=config.sentencepiecetokenizer.tokenize(ssegment)
                #if config.strategy=="bysegments":
                translation_segment=translate_segment(ssegment)
                #elif config.strategy=="bychunks":
                #    translation_segment=translate_chunks(ssegment)
                    
                translation_segment=add_leading_trailing_spances(translation_segment,lSsegment,tSsegment)
                translations.append(translation_segment)
            translation=merge_translations(translations)
        else:
            if config.sentencepiece:
                sparagraph=config.sentencepiecetokenizer.tokenize(sparagraph)
            translation=translate_segment(sparagraph)
        
    except:
        printLOG(2,"ERROR in MTUOC_translate translate_para:",sys.exc_info())
    translation=add_leading_trailing_spances(translation,lSpara,tSpara)
    
    translation["system_name"]=config.system_name
    printLOG(4,"TRANSLATION PARA:",translation)
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

'''
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
'''

def translate_string(segment, segment_notags):
    
    if config.sentencepiece:
        segment=config.sentencepiecetokenizer.tokenize(segment)
        segment_notags=config.sentencepiecetokenizer.tokenize(segment_notags)
    
            
    if config.MTUOCServer_MTengine=="Transformers" or config.MTUOCServer_MTengine=="OpusMT":
        try:
            if config.remove_tags:
                translationSTR=config.TransformersTranslator.translate(segment_notags)
            else:
                translationSTR=config.TransformersTranslator.translate(segment)
        except:
            printLOG(2,"Error translating segment with Transformers",sys.exc_info())
            
    
    elif config.MTUOCServer_MTengine=="NLLB":
        try:
            if config.remove_tags:
                translationSTR=config.NLLB_translator.translate(segment_notags)
            else:
                translationSTR=config.NLLB_translator.translate(segment)
        except:
            printLOG(2,"Error translating segment with NLLB",sys.exc_info())
        return(translationSTR)
        
    elif config.MTUOCServer_MTengine=="Marian":
        try:
            if config.remove_tags:
                translationSTR=config.MarianTranslator.translate(segment_notags)
            else:
                translationSTR=config.MarianTranslator.translate(segment)
        except:
            printLOG(2,"Error translating segment with Marian",sys.exc_info())  
        
    
    elif config.MTUOCServer_MTengine=="Ollama":
        try:
            if config.remove_tags:
                translationSTR=config.ollamaTranslator.translate(segment_notags)
            else:
                translationSTR=config.ollamaTranslator.translate(segment)
        except:
            printLOG(2,"Error translating segment with Ollama",sys.exc_info())  
    
    elif config.MTUOCServer_MTengine=="Aina":
        try:
            if config.remove_tags:
                translationSTR=config.AinaTranslator.translate(segment_notags)
            else:
                translationSTR=config.AinaTranslator.translate(segment)
        except:
            printLOG(2,"Error translating segment with Aina",sys.exc_info())
    
    elif config.MTUOCServer_MTengine=="SalamandraTA":

        try:
            if config.remove_tags:
                translationSTR=config.SalamandraTATranslator.translate(segment_notags)
            else:
                translationSTR=config.SalamandraTATranslator.translate(segment)                
        except:
            printLOG(2,"Error translating segment with SalamandraTA",sys.exc_info())

            


    elif config.MTUOCServer_MTengine=="M2M100":
        try:
            if config.remove_tags:
                translationSTR=config.M2M100_translator.translate(segment_notags)
            else:
                translationSTR=config.M2M100_translator.translate(segment)
        except:
            printLOG(2,"Error translating segment with M2M100",sys.exc_info())
        return(translationSTR)


    elif config.MTUOCServer_MTengine=="Softcatalà" or config.MTUOCServer_MTengine=="Softcatala":
        try:
            if config.remove_tags:
                translationSTR=config.softcatala_translator.translate(segment_notags)
            else:
                translationSTR=config.softcatala_translator.translate(segment)
        except:
            printLOG(2,"Error translating segment with Softcatalà",sys.exc_info())
        return(translationSTR)
        
    elif config.MTUOCServer_MTengine=="ctranslate2":
        try:
            if config.remove_tags:
                translationSTR=config.ctranslate2_translator.translate(segment_notags)
            else:
                translationSTR=config.ctranslate2_translator.translate(segment)
        except:
            printLOG(2,"Error translating segment with ctranslate2",sys.exc_info())
        
        
    elif config.MTUOCServer_MTengine=="Apertium":
        try:
            
            if config.remove_tags:
                translationSTR=config.apertium_translator.translate(segment_notags)
            else:
                translationSTR=config.apertium_translator.translate(segment)
        except:
            printLOG(3,"Error translating segment with Apertium",sys.exc_info())
            
    elif config.MTUOCServer_MTengine=="Llama":
        try:
            
            if config.remove_tags:
                totranslate=config.Llama_instruct_prefix+" "+segment_notags+" "+config.Llama_instruct_postfix
                translationSTR=config.Llama_translator.generate(totranslate)
            else:
                totranslate=config.Llama_instruct_prefix+" "+segment+" "+config.Llama_instruct_postfix
                translationSTR=config.Llama_translator.generate(totranslate)
        except:
            printLOG(3,"Error translating segment with Llama",sys.exc_info())
        
            
    return(translationSTR)

def translate_segment(segment):
    printLOG(2,"SEGMENT:",segment)
    if config.multilingual:
        config.src=config.multilingual+" "+segment
    else:
        config.src=segment
    config.translation={}
    config.casetype=config.preprocessor.analyze_segment_case(segment)
    config.translation["system_name"]=config.system_name
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
    if len(segment)>=config.max_segment_chars:
        config.translation["tgt"]=segment
        printLOG(2,"TRANSLATION SEGMENT LENGTH EXCEEDED:",config.translation["tgt"])
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
    if config.sentencepiece:
        config.translation["tgt"]=config.sentencepiecetokenizer.detokenize(config.translation["tgt"])
        for tr in config.translation["alternate_translations"]:
            tr["tgt"]=config.sentencepiecetokenizer.detokenize(tr["tgt"])
    if config.restore_case and config.casetype=="upper":
        config.translation["tgt"]=config.translation["tgt"].upper()
        for tr in config.translation["alternate_translations"]:
            tr["tgt"]=tr["tgt"].upper()
    
    config.translation["src"]=segment        
    '''
    if config.calculate_sbert:
        
        temptranslations=[]
        for trans in config.translation["alternate_translations"]:
            temptranslations.append(trans["tgt"])
        
        sberts=config.sbert_scorer.sbertScoreStrLst(config.translation["src"],temptranslations)
        config.translation["sbert"]=sberts[0]
        
        cont=0
        for trans in config.translation["alternate_translations"]:
            trans["sbert"]=sberts[cont]
            cont+=1

    if config.calculate_sbert and config.sort_by_sbert:
        sorted_alternate_translations = sorted(config.translation["alternate_translations"], key=lambda x: x['sbert'], reverse=True)
        config.translation["alternate_translations"]=sorted_alternate_translations
        config.translation["tgt"]=config.translation["alternate_translations"][0]["tgt"]
        config.translation["tgt_tokens"]=config.translation["alternate_translations"][0]["tgt_tokens"]
        config.translation["tgt_subwords"]=config.translation["alternate_translations"][0]["tgt_subwords"]
        config.translation["alignment"]=config.translation["alternate_translations"][0]["alignment"]
        config.translation["sbert"]=config.translation["alternate_translations"][0]["sbert"]
    '''
    if config.calculate_sbert:
        sbertindex=config.sbertScorer.sbertScoreStrStr(config.translation["src"],config.translation["tgt"])
        printLOG(2,"SBERT",sbertindex)
    
    if config.AutomaticPostedition=="HFPosteditor" and sbertindex<=config.postedition_sbert_threshold:
        printLOG(2,"POSTEDITING",sbertindex)
        posteditedTranslation=config.HFPosteditor.postedit(config.src_notags,config.translation["tgt"])
        printLOG(2,config.translation["tgt"],posteditedTranslation)
        if config.translation["tgt"].strip()==posteditedTranslation.strip():
            printLOG(2,"NO CHANGES IN POSTEDITION",sbertindex)
        config.translation["tgt"]=posteditedTranslation
        
    if config.AutomaticPostedition=="OllamaPosteditor" and sbertindex<=config.postedition_sbert_threshold:
        printLOG(2,"POSTEDITING",sbertindex)
        posteditedTranslation=config.OllamaPosteditor.postedit(config.src_notags,config.translation["tgt"])
        printLOG(2,config.translation["tgt"],posteditedTranslation)
        if config.translation["tgt"].strip()==posteditedTranslation.strip():
            printLOG(2,"NO CHANGES IN POSTEDITION",sbertindex)
        config.translation["tgt"]=posteditedTranslation
    
    if config.restore_tags:# and config.strategy=="bysegments":
        try:
            config.postprocessor.insert_tags()
        except:
            printLOG(2,"Error postprocessing",sys.exc_info())
    
    '''
    if config.numeric_check:
        config.translation["tgt"]=config.postprocessor.check_and_replace_numeric(config.translation["src"], config.translation["tgt"])
        
        for tr in config.translation["alternate_translations"]:
            tr["tgt"]=config.postprocessor.check_and_replace_numeric(config.translation["src"], tr["tgt"])
    '''
    
    if config.change_output:
        config.translation=config.postprocessor.change_output(config.translation)
    if config.change_translation:
        config.translation=config.postprocessor.change_translation(config.translation)
    printLOG(2,"TRANSLATION SEGMENT:",config.translation["tgt"])
    return(config.translation)    
