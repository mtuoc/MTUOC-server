from sentence_transformers import SentenceTransformer, util


class sbertScorer():
    def __init__(self):
        self.model=None
        
    def set_model(self,model="LaBSE"):
        self.model = SentenceTransformer(model)
    
    def sbertScoreStrStr(self,segment1,segment2):
        embeddings1 = self.model.encode([segment1], convert_to_tensor=False)
        embeddings2 = self.model.encode([segment2], convert_to_tensor=False)
        cosine_scores = util.cos_sim(embeddings1, embeddings2)
        cosine_score = cosine_scores[0][0].item()
        return(cosine_score)
    def sbertScoreStrLst(self,segment1,segments2):
        segments1=[]
        for i in range(len(segments2)):
            segments1.append(segment1)            
        embeddings1 = self.model.encode(segments1, convert_to_tensor=False)
        embeddings2 = self.model.encode(segments2, convert_to_tensor=False)        
        cosine_scores = util.cos_sim(embeddings1, embeddings2)
        results=[]
        for i in range(len(segments2)):                   
            results.append(cosine_scores[i][i].item())        
        return(results)
        
    def sbertScoreLstLst(self,segments1,segments2):
        embeddings1 = self.model.encode(segments1, convert_to_tensor=False)
        embeddings2 = self.model.encode(segments2, convert_to_tensor=False)        
        cosine_scores = util.cos_sim(embeddings1, embeddings2)
        results=[]
        for i in range(len(segments2)):                   
            results.append(cosine_scores[i][i].item())        
        return(results)
