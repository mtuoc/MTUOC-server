import pyonmttok
import ctranslate2

class SoftcatalaTranslator:
    def __init__(self):
        self.model_dir=None
        self.translator=None
        self.tokenizer=None
        self.sp_model=None
        self.ctranslatedir=None
        self.beam_size=1
        self.num_hypotheses=1
        self.alternate_translations=[]

    def set_model_dir(self,model_dir):
        if model_dir.endswith("/"):model_dir=model_dir[0:-1]
        self.model_dir=model_dir
        self.ctranslatedir=self.model_dir+"/ctranslate2"
        self.translator=ctranslate2.Translator(self.ctranslatedir)
        self.sp_model=self.model_dir+"/tokenizer/sp_m.model"
        self.tokenizer = pyonmttok.Tokenizer(mode="none", sp_model_path = self.sp_model)
        
    def set_beam_size(self,beam_size):
        self.beam_size=beam_size
    
    def set_num_hypotheses(self,num_hypotheses):
        self.num_hypotheses=num_hypotheses
        
    def clean(self,llista):
        self.llista=llista
        for item in ["<s>","</s>","<pad>"]:
            c = self.llista.count(item) 
            for i in range(c): 
                self.llista.remove(item) 
        return(self.llista)
    '''    
    def translate(self,text):
        self.alternate_translations=[]
        self.tokenized=self.tokenizer.tokenize(text)
        self.translation = self.translator.translate_batch([self.tokenized[0]],beam_size=self.beam_size,num_hypotheses=self.num_hypotheses)
        for i in range(0,len(self.translation[0].hypotheses)):
            self.alternate_translation={}
            self.alternate_translation["tgt_tokens"]=self.translation[0].hypotheses[i]
            self.alternate_translation["tgt_tokens"]=self.clean(self.alternate_translation["tgt_tokens"])
            self.alternate_translation["alignments"]="None"
            self.alternate_translation["tgt"]="".join(self.alternate_translation["tgt_tokens"]).replace("▁"," ")
            if self.alternate_translation["tgt"].startswith(" ") and not text.startswith(" "): self.alternate_translation["tgt"]=self.alternate_translation["tgt"][1:]
            self.alternate_translations.append(self.alternate_translation)

        self.response={}
        self.response["src_tokens"]=" ".join(self.tokenized[0])
        self.response["tgt_tokens"]=" ".join(self.alternate_translations[0]["tgt_tokens"])
        self.response["tgt"]=self.alternate_translations[0]["tgt"]
        self.response["alignments"]="None"
        self.response["alternate_translations"]=self.alternate_translations
        return(self.response)
     '''   
     
    def translate(self,text):
        self.alternate_translations=[]
        self.tokenized=self.tokenizer.tokenize(text)
        self.translation = self.translator.translate_batch([self.tokenized[0]],beam_size=self.beam_size,num_hypotheses=self.num_hypotheses)
        
        for i in range(0,len(self.translation[0].hypotheses)):
            self.alternate_translation={}
            self.alternate_translation["tgt_tokens"]=self.translation[0].hypotheses[i]
            self.alternate_translation["tgt_tokens"]=self.clean(self.alternate_translation["tgt_tokens"])
            self.alternate_translation["tgt_subwords"]=self.alternate_translation["tgt_tokens"]                    
            self.alternate_translation["alignment"]="None"
            self.alternate_translation["tgt"]="".join(self.alternate_translation["tgt_tokens"]).replace("▁"," ")
            self.alternate_translation["tgt_tokens"]=" ".join(self.alternate_translation["tgt_tokens"])
            self.alternate_translation["tgt_subwords"]=" ".join(self.alternate_translation["tgt_subwords"])
            if self.alternate_translation["tgt"].startswith(" ") and not text.startswith(" "): self.alternate_translation["tgt"]=self.alternate_translation["tgt"][1:]
            self.alternate_translations.append(self.alternate_translation)

        self.response={}
        
        self.response["src_tokens"]=" ".join(self.tokenized[0])
        self.response["tgt_tokens"]=self.alternate_translations[0]["tgt_tokens"]
        self.response["src_subwords"]=" ".join(self.tokenized[0])
        self.response["tgt_subwords"]=self.alternate_translations[0]["tgt_tokens"]
        self.response["tgt"]=self.alternate_translations[0]["tgt"]
        self.response["alignment"]=self.alternate_translations[0]["alignment"]
        self.response["alternate_translations"]=self.alternate_translations
        return(self.response)
        
