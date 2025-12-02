# neologism_scorer.py
from typing import List, Dict, Any, Optional
from spellchecker import SpellChecker
import Levenshtein
import config
from MTUOC_misc import printLOG

class NeologismScorer:
    """Calcula una puntuació basada en la detecció de neologismes (paraules desconegudes) en la font."""
    def __init__(self, source_lang: str = 'es'):
        printLOG(1,f"Carregant diccionari per a la detecció de neologismes: '{source_lang}'...")
        try:
            # Per defecte, la classe SpellChecker de Python
            self.spell_checker = SpellChecker(language=source_lang)
            printLOG(1,"Diccionari de neologismes carregat correctament.")
        except Exception as e:
            printLOG(1,f"AVÍS: No s'ha pogut carregar el diccionari per a '{source_lang}'. Detecció desactivada. Error: {e}")
            self.spell_checker = None

    def _find_neologisms(self, sentence: str) -> List[str]:
        """Troba paraules desconegudes (neologismes) a la frase font."""
        if not self.spell_checker: return []
        # Utilitzem el tokenitzador de la configuració si hi és, altrament separem per espais
        tokenizer = getattr(config, 'reranktokenizerSL', None) 
        if tokenizer:
            words = tokenizer.tokenize(sentence.lower()).split()
        else:
            words = sentence.lower().split()
            
        return [str(n) for n in self.spell_checker.unknown(words)]

    def _char_similarity(self, s1: str, s2: str) -> float:
        """Calcula la similitud de caràcters (Levenshtein) entre dues cadenes."""
        if not s1 or not s2: return 0.0
        distance = Levenshtein.distance(s1, s2)
        max_len = max(len(s1), len(s2))
        return 1.0 - (distance / max_len)

    def score(self, detokenized_source: str, candidates: List[Dict[str, Any]]) -> None:
        """Afegeix la puntuació 'neologism_score' a cada candidat (similitud màxima amb el neologisme trobat)."""
        
        if not self.spell_checker:
            for cand in candidates:
                cand['neologism_score'] = 0.0
            return

        source_neologisms = self._find_neologisms(detokenized_source)
        
        for cand in candidates:
            cand['neologism_score'] = 0.0 # Valor per defecte
            
            if source_neologisms:
                best_similarity = 0.0
                candidate_words = cand['detokenized_text'].lower().split()
                
                # Per cada neologisme de la font, busquem la paraula més similar en la traducció candidata
                for neo in source_neologisms:
                    similarities = [self._char_similarity(neo, cw) for cw in candidate_words]
                    if similarities: 
                        best_similarity = max(best_similarity, max(similarities))
                        
                cand['neologism_score'] = best_similarity
