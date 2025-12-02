# glossary_scorer.py
from typing import List, Dict, Any, Optional

class GlossaryScorer:
    """Calcula un bonus si el segment font i el segment candidat contenen un terme de glossari coincident."""
    def __init__(self):
        # Aquesta classe no necessita carregar cap recurs al __init__
        pass

    def score(self, detokenized_source: str, candidates: List[Dict[str, Any]], glossary: Optional[Dict[str, str]] = None) -> None:
        """Afegeix la puntuació 'glossary_hit' a cada candidat (1.0 si hi ha coincidència, 0.0 altrament)."""
        if not glossary:
            for cand in candidates:
                cand['glossary_hit'] = 0.0
            return

        for cand in candidates:
            cand['glossary_hit'] = 0.0 # Valor per defecte
            for src_term, tgt_term in glossary.items():
                # Comprovem si el terme font és a la frase font i el terme objectiu és a la frase candidata
                if src_term in detokenized_source and tgt_term in cand['detokenized_text']:
                    cand['glossary_hit'] += 1.0 # Bonus complet
                    #break
            
