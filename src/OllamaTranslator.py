from ollama_engine import OllamaModelEngine
import sys

class OllamaTranslator:
    def __init__(self, config_path="config-OllamaTranslator.yaml"):
        self.engine = OllamaModelEngine(config_path)
        self.alternate_translations = []
        self.model_path = None 
        
        if not self.engine.config:
            print("ERROR: No s'ha pogut carregar la configuració.")
            return
            
        # Extraiem el nom del model per exposar-lo al servidor principal
        ollama_cfg = self.engine.config.get("ollama_settings", {})
        self.model_path = ollama_cfg.get("model", "gemma:2b")  # <--- Desa el nom del model (ex: "gemma:2b")
        
        self.prompt_cfg = self.engine.config.get("prompt_settings", {})
        if not self.engine.initialize_client(status_callback=print):
            return
        if not self.engine.ensure_model_exists(status_callback=print):
            return
    def translate(self, SLsegment):
        prompt_template = self.prompt_cfg["prompt_template"]
        prompt = prompt_template.format(SLsegment=SLsegment)
        role_system = "" 
        role_assistant = "" 
        regex = self.prompt_cfg["regex_pattern"]
        
        # L'engine ja fa el post_process internament i te'l torna a la posició [1]
        raw_text, translation_cleaned = self.engine.generate(prompt, role_system, role_assistant, override_regex=regex)
        self.alternate_translations = []
        response_data = {
            "src_tokens": SLsegment,
            "tgt_tokens": translation_cleaned,
            "src_subwords": SLsegment,
            "tgt_subwords": translation_cleaned,
            "tgt": translation_cleaned,
            "alignment": "",
            "alternate_translations": self.alternate_translations
        }
        return response_data
