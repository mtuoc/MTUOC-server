import pyonmttok
import ctranslate2
import sentencepiece as spm

class ctranslate2Translator:
    def __init__(self):
        self.translation_model=None
        self.translator=None
        self.tokenizer=None
        self.SL_sp_model=None
        self.TL_sp_model=None
        self.src_lang=None
        self.tgt_lang=None
        self.beam_size=1
        self.num_hypotheses=1
        self.device=None
        self.alternate_translations=[]

    def set_translation_model(self,translation_model):
        self.translation_model=translation_model
        
    def set_SL_sp_model(self,SL_sp_model):
        self.SL_sp_model=SL_sp_model
        
    def set_TL_sp_model(self,TL_sp_model):
        self.TL_sp_model=TL_sp_model
        
    def set_src_lang(self,src_lang):
        self.src_lang=src_lang
    
    def set_tgt_lang(self,tgt_lang):
        self.tgt_lang=tgt_lang
    
    def set_beam_size(self,beam_size):
        self.beam_size=beam_size
    
    def set_num_hypotheses(self,num_hypotheses):
        self.num_hypotheses=num_hypotheses
        
    def set_device(self,device):
        self.device=device
        
    def clean(self,llista):
        self.llista=llista
        for item in ["<s>","</s>","<pad>"]:
            c = self.llista.count(item) 
            for i in range(c): 
                self.llista.remove(item) 
        return(self.llista)

     
    def translate(self,text):


        # Load the source SentecePiece model
        spSL = spm.SentencePieceProcessor()
        spSL.load(self.SL_sp_model)

        spTL = spm.SentencePieceProcessor()
        spTL.load(self.TL_sp_model)
        
        translator = ctranslate2.Translator(self.translation_model, self.device)

        source_sentences = [text.strip()]
        if self.tgt_lang==None: self.tgt_lang=""
        target_prefix = [[self.tgt_lang]] * len(source_sentences)
        
        # Subword the source sentences
        source_sents_subworded = spSL.encode_as_pieces(source_sentences)
        if not self.src_lang==None:
            source_sents_subworded = [[self.src_lang] + source_sents_subworded[0] + ["</s>"]]
        else:
            source_sents_subworded = [source_sents_subworded[0] + ["</s>"]]
        
        # Translate the source sentences
        translations_subworded = translator.translate_batch(source_sents_subworded, batch_type="tokens", max_batch_size=2024, beam_size=self.beam_size, num_hypotheses=self.num_hypotheses, target_prefix=target_prefix)
        translations_subworded = translations_subworded[0].hypotheses#[0] for translation in translations_subworded]
               
        
        #Delete language codes
        source_sent_subworded=source_sents_subworded[0]
        if source_sent_subworded[-1]=="</s>": source_sent_subworded=source_sent_subworded[0:-1]
        if not self.src_lang==None:
            source_sent_subworded=" ".join(source_sent_subworded[1:])
        else:
            source_sent_subworded=" ".join(source_sent_subworded)
        
        
        aux=translations_subworded
        translations_subworded=[]
        for a in aux:
            if not self.tgt_lang==None:
                a=a[1:]
            translations_subworded.append(a)
        
        translations = spTL.decode(translations_subworded)
                
        aux=translations_subworded
        translations_subworded=[]
        for a in aux:
            translations_subworded.append(" ".join(a))
        
        self.response={}
        self.response["src"]=text
        self.response["src_tokens"]=source_sent_subworded
        self.response["src_subwords"]=source_sent_subworded
        self.response["tgt"]=translations[0]
        self.response["tgt_tokens"]=translations_subworded[0]
        self.response["tgt_subwords"]=translations_subworded[0]
        self.response["alignment"]=""
        self.response["alternate_translations"]=[]
        
        for i in range(1,len(translations)):
            self.alternate_translation={}
            self.alternate_translation["tgt"]=translations[i]
            self.alternate_translation["tgt_tokens"]=translations_subworded[i]
            self.alternate_translation["tgt_subwords"]=translations_subworded[i]
            self.alternate_translation["alignment"]=""
            self.response["alternate_translations"].append(self.alternate_translation)        
        return(self.response)
