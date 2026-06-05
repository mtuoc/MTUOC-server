import sentencepiece as spm


class SentencePieceTokenizer():
    def __init__(self):
        self.spmodel=None
        self.spvocab=None
        self.sp=None
        
    def set_spmodel(self,spmodel):
        self.spmodel=spmodel
        self.sp=spm.SentencePieceProcessor(model_file=self.spmodel)
        
    def set_spvocab(self,spvocab):
        self.spvocab=spvocab
        
    def tokenize(self, segment):
        tokenized=" ".join(self.sp.encode(segment, out_type=str))
        return(tokenized)
        
    def detokenize(self,tokenized):
        segment=self.sp.decode(tokenized.split(" "))
        #segment=tokenized.replace(" ","").replace("▁"," ")
        return(segment)
    
