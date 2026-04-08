import yaml
import sys
import torch
import re
from transformers import T5ForConditionalGeneration, T5Tokenizer

class MadladTranslator:
    def __init__(self, config_path="config-MadladTranslator.yaml"):
        self.config = self.load_config(config_path)
        self.alternate_translations = []
        # Inicialitzem a None per evitar l'AttributeError si falla la càrrega
        self.tokenizer = None
        self.model = None
        
        if self.config:
            m_cfg = self.config['model_settings']
            try:
                self.model_name = m_cfg.get('name', 'google/madlad400-3b-mt')
                self.device_type = m_cfg.get('device', 'cuda')
                
                # Per a MADLAD és recomanable legacy=False si la versió de transformers ho permet
                self.tokenizer = T5Tokenizer.from_pretrained(self.model_name, legacy=False)
                
                if self.device_type == "cuda" and torch.cuda.is_available():
                    device_map = "auto"
                    # bfloat16 és el format natiu de MADLAD, molt més estable que float16 simple
                    dtype = torch.bfloat16 
                else:
                    device_map = None
                    dtype = torch.float32 # Més segur per a CPU
                
                self.model = T5ForConditionalGeneration.from_pretrained(
                    self.model_name,
                    device_map=device_map,
                    torch_dtype=dtype,
                    trust_remote_code=m_cfg.get('trust_remote_code', True)
                )
                
                if device_map is None:
                    self.model = self.model.to("cpu")
                    
                print(f"Model {self.model_name} carregat correctament a {self.device_type}")
            except Exception as e:
                print(f"ERROR crític carregant el model: {e}")

    def load_config(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def translate(self, SLsegment):
        # Comprovació de seguretat
        if self.tokenizer is None or self.model is None:
            return {"tgt": "ERROR: El model o el tokenitzador no s'han carregat."}

        l_cfg = self.config["lang_settings"]
        g_cfg = self.config["generation_params"]
        
        # Gestió del tag de llengua
        target_tag = l_cfg.get('default_target_tag', '<2es>')
        if l_cfg.get("dynamic", False) and re.match(r"^<2\w+>", SLsegment):
            full_input = SLsegment
        else:
            full_input = f"{target_tag} {SLsegment}"

        # Tokenització amb Attention Mask (crucial per evitar els "10000...")
        inputs = self.tokenizer(full_input, return_tensors="pt").to(self.model.device)
        
        # Generació
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs.get("attention_mask"),
                max_new_tokens=g_cfg.get("max_new_tokens", 512),
                temperature=g_cfg.get("temperature", 0.1),
                repetition_penalty=g_cfg.get("repetition_penalty", 1.2),
                num_beams=g_cfg.get("num_beams", 5),
                do_sample=True if g_cfg.get("temperature", 0.1) > 0 else False
            )
        
        translation_cleaned = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return {
            "src_tokens": SLsegment,
            "tgt_tokens": translation_cleaned,
            "src_subwords": SLsegment,
            "tgt_subwords": translation_cleaned,
            "tgt": translation_cleaned,
            "alignment": "",
            "alternate_translations": self.alternate_translations
        }
