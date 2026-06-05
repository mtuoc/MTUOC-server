import yaml
import sys
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

class M2M100Translator:
    def __init__(self, config_path="config-M2M100Translator.yaml"):
        self.config = self.load_config(config_path)
        self.alternate_translations = []
        self.model_path = None  # Variable de control de ruta per a MTUOC-server
        
        self.model = None
        self.tokenizer = None
        self.device = torch.cuda.current_device() if torch.cuda.is_available() else -1
        self.beam_size = 5 # Valor per defecte segons el teu mètode translate original
        self.num_hypotheses = 1

        if self.config:
            m_cfg = self.config['model_settings']
            self.model_path = m_cfg['name']  # Guardem el path aquí per a MTUOC-server
            
            # Recuperem paràmetres addicionals de configuració si existeixen
            if 'beam_size' in m_cfg:
                self.beam_size = m_cfg['beam_size']
            if 'num_hypotheses' in m_cfg:
                self.num_hypotheses = m_cfg['num_hypotheses']

            try:
                # Carreguem el model i el tokenizer directament aquí utilitzant la config
                self.model = AutoModelForSeq2SeqLM.from_pretrained(m_cfg['name'])
                self.tokenizer = AutoTokenizer.from_pretrained(m_cfg['name'])
                
                # Enviem el model al dispositiu correcte (cuda / cpu)
                device_str = m_cfg.get('device', 'cuda')
                if device_str == 'cuda' and torch.cuda.is_available():
                    self.model = self.model.to("cuda")
            except: 
                print("ERROR loading model:", sys.exc_info())

    def load_config(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def clean(self, llista):
        self.llista = llista
        for item in ["<s>", "</s>", "<pad>"]:
            c = self.llista.count(item) 
            for i in range(c): 
                self.llista.remove(item) 
        return self.llista

    def set_model(self, model_name):
        """Es manté per retrocompatibilitat si MTUOC-server el crida explicitament"""
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model_path = model_name
    
    def set_beam_size(self, beam_size):
        self.beam_size = beam_size
    
    def set_num_hypotheses(self, num_hypotheses):
        self.num_hypotheses = num_hypotheses
    
    def translate(self, SLsegment):
        # Mantenim la coherència amb el nom de variable de la classe de referència (SLsegment)
        text = SLsegment 
        
        # Obtenim els paràmetres de generació des del fitxer de configuració si existeixen,
        # si no, fem servir els que s'han definit per defecte a l'init o via mètodes set_
        g_cfg = self.config.get("generation_params", {})
        max_length = g_cfg.get("max_length", 200)
        num_beams = g_cfg.get("num_beams", self.beam_size)
        num_return_sequences = g_cfg.get("num_return_sequences", self.num_hypotheses)

        # Moure els inputs al mateix dispositiu que el model
        inputs = self.tokenizer(text, return_tensors="pt")
        if next(self.model.parameters()).is_cuda:
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        output_ids = self.model.generate(
            inputs["input_ids"], 
            max_length=max_length, 
            num_beams=num_beams, 
            num_return_sequences=num_return_sequences
        )

        generated_translation = self.tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
        self.alternate_translations = []
        
        for i in range(0, len(output_ids)):
            alternate_translation = self.tokenizer.decode(output_ids[i], skip_special_tokens=True).strip()
            alt_dict = {
                "src_tokens": text,
                "tgt_tokens": alternate_translation,
                "src_subwords": text,
                "tgt_subwords": alternate_translation,
                "tgt": alternate_translation,
                "alignment": "None"
            }
            self.alternate_translations.append(alt_dict)
        
        response_data = {
            "src_tokens": text,
            "tgt_tokens": generated_translation,
            "src_subwords": text,
            "tgt_subwords": generated_translation,
            "tgt": generated_translation,
            "alignment": "None",
            "alternate_translations": self.alternate_translations
        }
        return response_data
