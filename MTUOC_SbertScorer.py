# sbert_scorer.py
import torch
from sentence_transformers import SentenceTransformer, util
from typing import List, Dict, Any
from MTUOC_misc import printLOG

class SbertScorer:
    """Calcula la similitud semàntica entre la font i les candidates de traducció."""
    def __init__(self, model_name: str = 'None'):
        printLOG(1,f"Carregant el model SBERT: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        printLOG(1,f"Model SBERT carregat correctament al dispositiu: {self.device}")

    def score(self, source_sentence: str, candidate_texts: List[str]) -> List[float]:
        """Calcula les puntuacions de similitud semàntica (cosinus)."""
        if not candidate_texts:
            return []
            
        source_embedding = self.model.encode(source_sentence, convert_to_tensor=True)
        candidate_embeddings = self.model.encode(candidate_texts, convert_to_tensor=True)
        
        # util.cos_sim retorna un tensor, agafem el primer element i el convertim a llista
        sbert_scores = util.cos_sim(source_embedding, candidate_embeddings)[0].tolist()
        return sbert_scores
    '''
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
    '''
