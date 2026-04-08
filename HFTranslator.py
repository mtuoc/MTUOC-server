import yaml
import sys
from hf_engine import HFModelEngine 

class HFTranslator:
    def __init__(self, config_path="config-HFTranslator.yaml"):
        self.hf_engine = HFModelEngine()
        self.config = self.load_config(config_path)
        self.alternate_translations = []
        
        if self.config:
            m_cfg = self.config['model_settings']
            try:
                self.hf_engine.load_model(
                    model_name=m_cfg['name'],
                    device=m_cfg.get('device', 'cuda'),
                    trust_remote_code=m_cfg.get('trust_remote_code', True)
                )
            except: 
                print("ERROR loading model:", sys.exc_info())

    def load_config(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def translate(self, SLsegment):
        p_cfg = self.config["prompt_settings"]
        g_cfg = self.config["generation_params"]
        
        # Preparem el text de la instrucció
        prompt_content = p_cfg["template"].format(SLsegment=SLsegment)
        
        # Cridem a l'engine passant-li la configuració de generació
        translation = self.hf_engine.generate(prompt_content, g_cfg)
        
        # Apliquem el post-process (neteja)
        translation_cleaned = self.hf_engine.post_process(translation)
        
        # Mantenim el format de retorn que el teu sistema MTUOC necessita
        response_data = {
            "src_tokens": SLsegment,
            "tgt_tokens": translation_cleaned,
            "src_subwords": SLsegment,
            "tgt_subwords": translation_cleaned,
            "tgt": translation_cleaned,
            "alignment": "",
            "alternate_translations": self.alternate_translations
        }
        print("response_data", response_data)
        return response_data
