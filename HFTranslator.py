from hf_engine import HFModelEngine 
import sys

class HFTranslator:
    def __init__(self, config_path="config-HFTranslator.yaml"):
        self.hf_engine=HFModelEngine()
        self.config = self.hf_engine.load_config(config_path)
        self.alternate_translations=[]
        try:
            self.hf_engine.load_model()
        except: 
            print("ERROR in HFTranslator loading model:",sys.exc_info())


    def translate(self, SLsegment):
        prompt_cfg = self.config["prompt_settings"]
        prompt_template = prompt_cfg["template"]
        regex = prompt_cfg["regex_pattern"]
        if regex=="None": regex=None
        prompt = prompt_template.format(SLsegment=SLsegment)
        response = self.hf_engine.generate(prompt,override_regex=regex)
        translation=response[1]
        tranlationpostp=self.hf_engine.post_process(translation)
        response_data = {
            "src_tokens": SLsegment,
            "tgt_tokens": tranlationpostp,
            "src_subwords": SLsegment,
            "tgt_subwords": tranlationpostp,
            "tgt": tranlationpostp,
            "alignment": "",
            "alternate_translations": self.alternate_translations
        }
        print("response_data",response_data)
        return response_data
     
