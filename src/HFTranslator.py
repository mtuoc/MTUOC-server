import yaml
import sys
import traceback
from hf_engine import HFModelEngine 

class HFTranslator:
    def __init__(self, config_path="config-HFTranslator.yaml"):
        self.hf_engine = HFModelEngine(debug=False)
        self.config = self.load_config(config_path)
        self.alternate_translations = []
        self.model_path = None
        
        if self.config:
            m_cfg = self.config.get('model_settings', {})
            self.model_path = m_cfg.get('name')
            
            # Intentem carregar el model
            success = self.hf_engine.load_model(
                model_name=m_cfg['name'],
                device=m_cfg.get('device', 'cuda'),
                trust_remote_code=m_cfg.get('trust_remote_code', True)
            )
            
            if not success:
                print(f"[ERROR HFTranslator] No s'ha pogut carregar el model des de: {self.model_path}")

    def load_config(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def translate(self, SLsegment):
        if not SLsegment or not str(SLsegment).strip():
            return self._build_response("", "")

        p_cfg = self.config.get("prompt_settings", {})
        g_cfg = self.config.get("generation_params", {})
        
        raw_segment = str(SLsegment).strip()
        
        # 1. Preparem el prompt segons la plantilla del YAML
        prompt_template = p_cfg.get("template", "{SLsegment}")
        prompt_content = prompt_template.format(SLsegment=raw_segment)
        
        # 2. Executem la generació
        try:
            translation = self.hf_engine.generate(prompt_content, g_cfg)
        except Exception as e:
            print(f"[ERROR a HFTranslator.translate]: {e}")
            traceback.print_exc()
            translation = ""
        
        # Guardem la seguretat que translation sigui sempre una cadena de text (str)
        if translation is None:
            translation = ""
            
        # 3. Post-processat bàsic (retallar espais/salts de línia residuals)
        translation_cleaned = self.hf_engine.post_process(translation)
        
        return self._build_response(raw_segment, translation_cleaned)

    def _build_response(self, src_text, tgt_text):
        return {
            "src_tokens": src_text,
            "tgt_tokens": tgt_text,
            "src_subwords": src_text,
            "tgt_subwords": tgt_text,
            "tgt": tgt_text,
            "alignment": "",
            "alternate_translations": self.alternate_translations
        } 
