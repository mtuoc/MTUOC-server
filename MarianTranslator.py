# marian_translator_main.py
# ---------------------------------------------------------------------------------------
#   MarianTranslator v 2511
#   Description: an MTUOC server component
#   Copyright (C) 2024  Antoni Oliver
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ---------------------------------------------------------------------------------------

import socket
import time
import sys
import config
import os
import re
import subprocess
import platform

from MTUOC_misc import printLOG

from typing import List, Dict, Optional, Any
import codecs



    
    
    
    



class MarianReranker:
    """Processa i reordena la sortida de Marian amb una lògica de pesos intel·ligent,
    coordinant els scorers externs."""
    
    def __init__(self, sbert_weight,glossary_weight,neologism_weight, sbert_model_name: str = 'None', source_lang: str = 'es'):
        
        self.useSbertScorer=True
        self.useGlossaryScorer=True
        self.useNeologismScorer=True
        try:
            from MTUOC_SbertScorer import SbertScorer 
        except:
            self.useSbertScorer=False
        try:
            from MTUOC_GlossaryScorer import GlossaryScorer
        except:
            self.useGlossaryScorer=False
        try:
            from MTUOC_NeologismScorer import NeologismScorer
        except:
            self.useNeologismScorer=False
    
        # 🎯 Inicialització dels Scorers externs
        if not sbert_model_name=="None" and not sbert_model_name==None and self.useSbertScorer:
            self.sbert_scorer = SbertScorer(sbert_model_name)
        else:
            self.sbert_scorer = None
        if glossary_weight>0 and self.useGlossaryScorer:
            self.glossary_scorer = GlossaryScorer()
        else:
            self.glossary_scorer = None
        if neologism_weight>0 and self.useNeologismScorer:
            self.neologism_scorer = NeologismScorer(source_lang)
        else:
            self.neologism_scorer = None
     
    def _detokenize(self, sp_text: str) -> str:
        # Funció de detokenització sense modificacions
        detokenized=sp_text.replace(' ', '').replace('▁', ' ').strip()
        return detokenized
     
    def _parse_single_output(self, marian_output_str: str) -> List[Dict[str, Any]]:
        # Funció de parseig de Marian sense modificacions
        candidates = []
        for line in marian_output_str.strip().split('\n'):
            parts = line.split('|||')
            if len(parts) < 3: continue
            try:
                text = parts[1].strip()
                # El score es troba al darrer element després de l'últim '='
                score = float(parts[2].split('=')[-1].strip())
                candidates.append({'sp_text': text, 'marian_score': score})
            except (ValueError, IndexError): pass
        return candidates
        
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalitza les puntuacions entre 0 i 1."""
        min_score, max_score = min(scores), max(scores)
        if min_score == max_score: return [1.0] * len(scores)
        return [(score - min_score) / (max_score - min_score) for score in scores]

    def combine_scores(self, candidates: List[Dict[str, Any]], weights: Dict[str, float]) -> List[Dict[str, Any]]:
        """Aplica la normalització de Marian i calcula el score combinat."""
        if not candidates: return []
        
        marian_scores = [cand['marian_score'] for cand in candidates]
        normalized_marian_scores = self._normalize_scores(marian_scores)

        for i, cand in enumerate(candidates):
            glossary_bonus = cand.get('glossary_hit', 0.0)
            neologism_score = cand.get('neologism_score', 0.0)
            sbert_score = cand['sbert_score']
            cand['marian_score_normalized'] = normalized_marian_scores[i]
            
            # Càlcul del score combinat
            cand['combined_score'] = (weights.get('marian', 0.0) * normalized_marian_scores[i]) + \
                                     (weights.get('sbert', 0.0) * sbert_score) + \
                                     (weights.get('glossary', 0.0) * glossary_bonus) + \
                                     (weights.get('neologism', 0.0) * neologism_score)
                                     
        return sorted(candidates, key=lambda x: x['combined_score'], reverse=True)


    def rerank(
        self,
        sp_marian_output: str,
        sp_source_sentence: str,
        weights: Dict[str, float],
        glossary: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Mètode principal que reordena la sortida de Marian utilitzant els scorers modulars."""
         
        candidates = self._parse_single_output(sp_marian_output)      
        if not candidates: return []
          
        detokenized_source = self._detokenize(sp_source_sentence)
        candidate_texts = []
        
        # Preparació dels candidats per als scorers
        for cand in candidates:
            cand['detokenized_text'] = self._detokenize(cand['sp_text'])
            candidate_texts.append(cand['detokenized_text'])
            # Inicialitzem les puntuacions que calcularan els altres Scorers
            cand['glossary_hit'] = 0.0
            cand['neologism_score'] = 0.0

        # 1. Puntuació SBERT (Similitud Semàntica)
        try:
            if not self.sbert_scorer==None and self.useSbertScorer:
                sbert_scores = self.sbert_scorer.score(detokenized_source, candidate_texts)
                for i, cand in enumerate(candidates):
                    cand['sbert_score'] = sbert_scores[i]
       
            else:
                for i, cand in enumerate(candidates):
                    cand['sbert_score'] = 0
        except:
            pass
                
        # 2. Puntuació Glossari
        
        if weights.get('glossary', 0) > 0 and self.useGlossaryScorer:
            try:
                self.glossary_scorer.score(detokenized_source, candidates, glossary)
            except:
                pass
            
           
        # 3. Puntuació Neologisme
        if weights.get('neologism', 0) > 0 and self.useNeologismScorer:
            try:
                self.neologism_scorer.score(detokenized_source, candidates)
            except:
                pass

        # 4. Combinació i Reordenació Final
        # SbertScorer s'encarrega de la normalització de Marian i la combinació final
        #return self.sbert_scorer.combine_scores(candidates, weights)
        return self.combine_scores(candidates, weights)

    def format_as_marian_output(self, sorted_candidates: List[Dict[str, Any]], sentence_id: int = 0) -> str:
        # Aquest mètode es manté igual
        output_lines = []
        for cand in sorted_candidates:
            # Utilitzem el marian_score original (no el normalitzat) per mantenir el format de Marian
            score_str = f"{cand['marian_score']:.4f}" 
            line = f"{sentence_id} ||| {cand['sp_text']} ||| F0= {score_str} ||| {score_str}"
            output_lines.append(line)
        return "\n".join(output_lines)


class MarianTranslator:
    """Clase principal per a gestionar la connexió i traducció amb Marian, incloent el reranker."""
    
    def __init__(self):
        self.model=None
        self.sl_vocab=None
        self.tl_vocab=None
        self.prefix=None
        self.reranker=None
        self.reranker_SL=None
        self.reranker_glossary_separator=None
        self.reranker_glossary_file=None
        self.alternate_translations=[]
        self.GLOSSARY = {}
        self.CUSTOM_WEIGHTS = {}
         
    def lreplace(self, pattern, sub, string):
        """Reemplaça 'pattern' si comença 'string'."""
        return re.sub('^%s' % pattern, sub, string)

    def rreplace(self, pattern, sub, string):
        """Reemplaça 'pattern' si acaba 'string'."""
        return re.sub('%s$' % pattern, sub, string)
         
    def set_model(self,model):
        self.model=model
         
    def set_sl_vocab(self,sl_vocab):
        self.sl_vocab=sl_vocab
         
    def set_tl_vocab(self,tl_vocab):
        self.tl_vocab=tl_vocab
         
    def set_prefix(self,prefix):
        self.prefix=prefix
         
    def set_rescorer(self,sbertmodel,reranking_source_language,reranking_glossary_file,reranking_glossary_separator,marian_weight,sbert_weight,glossary_weight,neologism_weight):

        # Carregant pesos:
        self.CUSTOM_WEIGHTS = {
        'marian': marian_weight,
        'sbert': sbert_weight,
        'glossary': glossary_weight,
        'neologism': neologism_weight }
       
        if not reranking_glossary_file==None and glossary_weight>0: 
            try:
                with codecs.open(reranking_glossary_file,"r",encoding="utf-8") as glfile:
                    for linia in glfile:
                        linia=linia.rstrip()
                        camps=linia.split(reranking_glossary_separator)
                        if len(camps)==2:
                            self.GLOSSARY[camps[0]]=camps[1]
            except FileNotFoundError:
                 printLOG(1,f"AVÍS: Fitxer de glossari no trobat a: {reranking_glossary_file}")
            except Exception as e:
                 printLOG(1,f"ERROR carregant el glossari: {e}")
        
             
        self.reranker = MarianReranker(sbert_weight,glossary_weight,neologism_weight, sbertmodel, reranking_source_language)
        
    def start_marian_server(self):
        printLOG(1, "START MT ENGINE:", config.startMarianCommand)
         
        if platform.system() == "Windows":
            subprocess.Popen(config.startMarianCommand) 
        else:
            os.system(config.startMarianCommand)


    def connect_to_Marian(self):
        printLOG(1,"CONNECT TO MARIAN.","")
        from websocket import create_connection
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            conn=s.connect_ex((config.MarianIP, config.MarianPort))
            if conn == 0: marianstarted=True
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
        #if self.prefix:
        #    text="▁ "+self.prefix+" "+text
        print("*********",text)
        try:
            config.ws.send(text)
        except:
            printLOG(1,"Error sending segment to Marian.",sys.exc_info())
            
        translations = config.ws.recv()
        # ⚙️ Apliquem el Reranker si està configurat
        if self.reranker is not None:
            final_reranked_list = self.reranker.rerank(translations, text, weights=self.CUSTOM_WEIGHTS, glossary=self.GLOSSARY)
             
            # 🔄 Formatem la sortida repuntuada al format de Marian per a mantenir la compatibilitat
            formatted_output = self.reranker.format_as_marian_output(final_reranked_list)
            translations=formatted_output
        # 📝 Processament final de les candidates (ja siguin originals o repuntuades)
        tc_aux=translations.split("\n")
        print(tc_aux)
        for i in range(0,len(tc_aux)):
            # Evitem línies buides al final si n'hi ha
            if not tc_aux[i].strip(): continue 

            # Separació: [ID] ||| [Text] ||| [Score Info]
            parts = tc_aux[i].split(" ||| ")
            if len(parts) < 3: continue
            
            segmentaux = parts[1].strip()
            alignmentaux = parts[2].strip()

            # Neteja de tokens <s> i </s>
            if segmentaux.startswith("<s> "):
                segmentaux=self.lreplace("<s> ","",segmentaux)
            if segmentaux.endswith("</s>"):
                segmentaux=self.rreplace("</s>","",segmentaux)   
                
            self.alternate_translation={}
            self.alternate_translation["tgt_tokens"]=segmentaux
            self.alternate_translation["tgt_subwords"]=segmentaux # En Marian s'utilitza sovint el mateix
            self.alternate_translation["alignment"]=alignmentaux
            self.alternate_translation["tgt"]=segmentaux
            self.alternate_translations.append(self.alternate_translation)

        self.response={}
        if self.alternate_translations:
            # La primera és la millor (repuntuada o original si no hi ha reranker)
            best_translation = self.alternate_translations[0]
            self.response["system_name"]=config.system_name
            self.response["src_tokens"]=text
            self.response["tgt_tokens"]=best_translation["tgt_tokens"]
            self.response["src_subwords"]=text
            self.response["tgt_subwords"]=best_translation["tgt_tokens"]
            self.response["tgt"]=best_translation["tgt"]
            self.response["alignment"]=best_translation["alignment"]
            self.response["alternate_translations"]=self.alternate_translations
        else:
            # Gestió si no hi ha traduccions vàlides
            self.response["system_name"]=config.system_name
            self.response["src_tokens"]=text
            self.response["tgt_tokens"]=""
            self.response["src_subwords"]=text
            self.response["tgt_subwords"]=""
            self.response["tgt"]=""
            self.response["alignment"]=""
            self.response["alternate_translations"]=[]
            
        return(self.response)
         
    
def translate_segment_Marian(segmentPre):
    # Funció original sense reranking (si MarianTranslator.translate ja té el reranking, aquesta pot ser redundant o utilitzada només per models sense reranking)
    translation_candidates={}
    translation_candidates["segmentNOTAGSPre"]=segmentPre
    lseg=len(segmentPre)
    try:
        config.ws.send(segmentPre)
    except:
        printLOG(1,"Error sending segment to Marian.",sys.exc_info())
        
    alternate_translations=[]
    translations = config.ws.recv()
    tc_aux=translations.split("\n")
    for i in range(0,len(tc_aux)):
        if not tc_aux[i].strip(): continue
        
        parts = tc_aux[i].split(" ||| ")
        if len(parts) < 3: continue
        
        segmentaux=parts[1].strip()
        alignmentaux=parts[2].strip()
        
        alternate_translation={}
        alternate_translation["tgt_tokens"]=segmentaux
        alternate_translation["alignments"]=alignmentaux
        alternate_translation["tgt"]="None"
        alternate_translations.append(alternate_translation)

    response={}
    response["src_tokens"]=segmentPre
    if alternate_translations:
        response["tgt_tokens"]=alternate_translations[0]["tgt_tokens"]
        response["tgt"]="None"
        response["alignments"]=alternate_translations[0]["alignments"]
        response["alternate_translations"]=alternate_translations
    else:
        response["tgt_tokens"]=""
        response["tgt"]="None"
        response["alignments"]=""
        response["alternate_translations"]=[]
        
    return(response)
