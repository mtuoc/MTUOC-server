from ollama_engine import OllamaModelEngine
import sys

class OllamaTranslator:
    def __init__(self, config_path="config-OllamaTranslator.yaml"):
        self.engine = OllamaModelEngine(config_path)
        if not self.engine.config:
            print("ERROR: No s'ha pogut carregar la configuració.")
            return
        self.prompt_cfg = self.engine.config.get("prompt_settings", {})
        if not self.engine.initialize_client(status_callback=print):
            return
        if not self.engine.ensure_model_exists(status_callback=print):
            return
    def translate(self, SLsegment):
        prompt_template = self.prompt_cfg["prompt_template"]
        prompt = prompt_template.format(SLsegment=SLsegment)
        role_system = "" #self.prompt_cfg["role_system"]
        role_assistant = "" #self.prompt_cfg["role_assistant"]
        regex = self.prompt_cfg["regex_pattern"]
        response= self.engine.generate(prompt, role_system, role_assistant, override_regex=regex)
        translation=response[1]
        tranlationpostp=self.engine.post_process(translation)
        self.alternate_translations=[]
        response_data = {
            "src_tokens": SLsegment,
            "tgt_tokens": tranlationpostp,
            "src_subwords": SLsegment,
            "tgt_subwords": tranlationpostp,
            "tgt": tranlationpostp,
            "alignment": "",
            "alternate_translations": self.alternate_translations
        }
        return response_data
