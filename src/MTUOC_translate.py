import sys
import re

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
        
    
def add_leading_trailing_spaces(translation,lS,tS):
    translation["tgt"]=lS+translation["tgt"]+tS
    return(translation)
    
    

def translate_para(paragraph, server_context):
    # Extraiem el preprocessador del context actiu
    preprocessor = server_context["preprocessor"]
    if preprocessor:
        lSpara, tSpara, sparagraph = preprocessor.leading_trailing_spaces(paragraph)
    else:
        lSpara=""
        sparagraph=paragraph
        tSpara=""
    
    # Passem el segment i el context al següent nivell
    translation = translate_segment(sparagraph, server_context)
    # Reconstruïm els espais (assegura't que tens add_leading_trailing_spaces importada/definida)
    translation = add_leading_trailing_spaces(translation, lSpara, tSpara)
    
    # Assignem metadades locals
    translation["system_name"] = server_context["system_name"]
    translation["src"] = paragraph
    
    return translation

def has_tags(segment):
        return bool(re.search(r'</?.+?/?>|\{[0-9]+\}', segment))

def translate_segment(segment, server_context):
    return translate_string(segment, server_context)
    
def translate_string(segment, server_context):
    preprocessor = server_context["preprocessor"]
    postprocessor = server_context["postprocessor"] 
    tokenizer = server_context["sentencepiece_tokenizer"]
    translator = server_context["translator_engine"]
    
    dopreprocess = server_context.get("dopreprocess", False)
    dopostprocess = server_context.get("dopostprocess", False) # <--- CONTROL BOOLEÀ GLOBAL
    translationMemory = server_context.get("translationMemory", False)
    #TRANSLATION MEMORY
    if not translationMemory==None:
        minsim = server_context.get("minsim", 100)
        retrieved=translationMemory.search(segment, min_similarity=minsim, max_candidates=1)
        if len(retrieved)>0:
            retrieved=retrieved[0][0]
            realsim=retrieved[0][0]
            translation_data = {
                "src": segment,
                "tgt": retrieved, 
                "tmsim": realsim,
                "src_tokens": "", "tgt_tokens": "", 
                "src_subwords": "", "tgt_subwords": "", 
                "alignment": "None", "alternate_translations": []
            }
            return(translation_data)
            
    # 1. Pas del Preprocessor
    segment_to_translate = segment
    if dopreprocess:
        segment_to_translate = preprocessor.preprocess(segment)

    # 2. Tokenització de subparaules (SentencePiece)
    if tokenizer is not None:
        segment_to_translate = tokenizer.tokenize(segment_to_translate)
    
    try:
        # 3. Cridem el motor de traducció resident (Marian)
        translation_data = translator.translate(segment_to_translate)
        translation_data["src"]=segment
    except Exception as e:
        print(f"Error crític a translator_engine: {e}", sys.exc_info())
        translation_data = {
            "tgt": segment, 
            "src_tokens": "", "tgt_tokens": "", 
            "src_subwords": "", "tgt_subwords": "", 
            "alignment": "None", "alternate_translations": []
        }
    
    # 4. Detokenitzem primer abans de fer qualsevol operació de text a la sortida
    if tokenizer is not None:
        translation_data["tgt"] = tokenizer.detokenize(translation_data["tgt"])
        for tr in translation_data.get("alternate_translations", []):
            tr["tgt"] = tokenizer.detokenize(tr["tgt"])
            

    postprocessor=server_context["postprocessor"]
    wordaligner=server_context["wordaligner"]
    
    if preprocessor and preprocessor.uppercasetranslation:
        translation_data["tgt"] = translation_data["tgt"].upper()
        for tr in translation_data.get("alternate_translations", []):
            tr["tgt"] = tr["tgt"].upper()
    if postprocessor:
        
        if has_tags(segment):
            ###EL PRINCIPAL
            if wordaligner:
                src_notags = segment_to_translate
                target_notags = translation_data["tgt"]
                SELECTEDALIGNMENT, sourceL, targetL = wordaligner.align_sentence_pair(src_notags, target_notags)
            else:
                SELECTEDALIGNMENT=translation_data["alignment"]
            if server_context["restore_tags"]:
                SOURCETAGS=segment
                TARGETNOTAGS=target_notags
                TARGETTAGS=postprocessor.insert_tags(SOURCETAGS,TARGETNOTAGS,SELECTEDALIGNMENT,wordaligner)
            
            translation_data["tgt"]=TARGETTAGS
            ###TOTES LES ALTERNATE_TRANSLATIONS
            try:
                for tr in translation_data.get("alternate_translations", []):
                    tradalt=tr["tgt"]
                    if wordaligner:
                        src_notags = segment_to_translate
                        target_notags = tr["tgt"]
                        SELECTEDALIGNMENT, sourceL, targetL = wordaligner.align_sentence_pair(src_notags, target_notags)
                    else:
                        SELECTEDALIGNMENT=tr["alignment"]
                    if server_context["restore_tags"]:
                        SOURCETAGS=segment
                        target_notags = tr["tgt"]
                        TARGETNOTAGS=target_notags
                        TARGETTAGS=postprocessor.insert_tags(SOURCETAGS,TARGETNOTAGS,SELECTEDALIGNMENT,wordaligner)
                    tr["tgt"]=TARGETTAGS
            except:
                print("ERROR ALIGNMENT ALTERNATE:", sys.exc_info())
        
        postprocessor.postprocess(translation_data)
            
    
    return translation_data
        
        
        
