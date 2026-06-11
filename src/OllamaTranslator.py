from ollama_engine import OllamaModelEngine
import sys

class OllamaTranslator:
    def __init__(self, config_path="config-OllamaTranslator.yaml"):
        # Inicialitzem primer els atributs per evitar de forma absoluta l'AttributeError si algun 'return' salta
        self.prompt_cfg = {}
        self.alternate_translations = []
        self.model_path = None 
        
        self.engine = OllamaModelEngine(config_path)
        
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
        # Seguretat en cas d'inicialització fallida
        if not self.prompt_cfg:
            return {
                "src_tokens": SLsegment,
                "tgt_tokens": "ERROR",
                "src_subwords": SLsegment,
                "tgt_subwords": "ERROR",
                "tgt": "ERROR: OllamaTranslator no s'ha inicialitzat correctament.",
                "alignment": "",
                "alternate_translations": []
            }

        prompt_template = self.prompt_cfg.get("prompt_template", "Translate: {SLsegment}")
        prompt = prompt_template.format(SLsegment=SLsegment)
        role_system = "" 
        role_assistant = "" 
        regex = self.prompt_cfg.get("regex_pattern", "None")
        
        # L'engine ja fa el post_process internament i te'l torna a la posició [1]
        raw_text, translation_cleaned = self.engine.generate(prompt, role_system, role_assistant, override_regex=regex)
        
        self.alternate_translations = []
        
        # Retornem el diccionari complet que MTUOC necessita per poder fer modificacions internes
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
