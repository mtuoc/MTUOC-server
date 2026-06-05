import yaml
import json
import logging
import os
from eole.bin.run.predict import PredictConfig
from eole.inference_engine import InferenceEnginePY
import time

logger = logging.getLogger("MTUOC_Eole_Engine")

class EoleTranslator:
    def __init__(self, config_path=None):
        self.engine = None
        self.model_path = None
        self.alternate_translations = []
        
        # Definim els fitxers de treball a l'arrel del servidor
        self.tmp_src = "eole_server_input.txt"
        self.tmp_tgt = "eole_server_output.txt"
        
        print("INFO: EoleTranslator started (Stable Production Architecture)")
        if config_path:
            self.load_from_config(config_path)

    def load_from_config(self, config_path):
        """Llegeix el YAML, injecta l'engine i inicialitza el motor resident."""
        try:
            print("Loading config inside class: ", config_path)
            with open(config_path, 'r', encoding="utf-8") as stream:
                config_yaml = yaml.load(stream, Loader=yaml.FullLoader)
            
            eole_config = config_yaml.get("model_specs", config_yaml.get("EoleMT", {}))
            
            self.model_path = eole_config.get("model_dir", "./eole-general-cat-eng/")
            eole_json_config = eole_config.get("config_path", "./predict_config.json")
            vocab_path = eole_config.get("vocab_path", "./eole-general-cat-eng/shared.vocab.txt")
            gpu_id = eole_config.get("gpu_id", 0)
            motor_triat = eole_config.get("engine", "eole")
            
            print(f"INFO: Selected MT engine from YAML: {motor_triat}")
            
            with open(eole_json_config, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                
            full_data = {
                "model": config_data.get("model", {}),
                "model_path": self.model_path,
                "src_subword_vocab": vocab_path,
                "gpu_ranks": [gpu_id] if gpu_id is not None else [],
                "engine": motor_triat,
                "verbose": False,
                "src": "fictici.txt" 
            }
            
            self.config = PredictConfig.model_validate(full_data)
            self.engine = InferenceEnginePY(self.config)
            print(f"INFO: Resident Eole Engine successfully loaded.")
            
        except Exception as e:
            print(f"ERROR: No s'ha pogut carregar la configuració d'Eole. Error: {e}")

    def translate(self, text, max_length=128):
        """
        Tradueix utilitzant obertura i tancament manual estricte de fitxers fixos.
        Garanteix que Linux mai es quedi sense descriptors de fitxer oberts.
        """
        if self.engine is None:
            raise ValueError("Eole engine not loaded. Check your config_path.")

        # 1. Escrivim el segment obrint i tancant el fitxer manualment al moment
        f_in = open(self.tmp_src, "w", encoding="utf-8")
        f_in.write(text + "\n")
        f_in.close()  # <-- Alliberat de la memòria a l'acte

        # 2. Injectem les rutes fixes a la configuració del motor
        self.engine.config.src = self.tmp_src
        self.engine.config.output = self.tmp_tgt

        # 3. Executem la inferència oficial d'Eole (llegeix i escriu directament)
        self.engine.infer_file()

        # 4. Llegim el text resultant obrint i tancant immediatament
        translated_text_raw = ""
        if os.path.exists(self.tmp_tgt):
            f_out = open(self.tmp_tgt, "r", encoding="utf-8")
            translated_text_raw = f_out.read().strip()
            f_out.close()  # <-- Alliberat de la memòria a l'acte

        # 5. Neteja física preventiva del fitxer de sortida per a la pròxima frase
        try:
            os.remove(self.tmp_tgt)
        except Exception:
            pass

        # 6. Mapegem la resposta al format exacte en brut que demana l'MTUOC
        src_tokens = text
        tgt_tokens = translated_text_raw
        
        self.response = {
            "src_tokens": src_tokens,
            "tgt_tokens": tgt_tokens,
            "src_subwords": src_tokens,
            "tgt_subwords": tgt_tokens,
            "tgt": translated_text_raw,
            "alignment": "None",
            "alternate_translations": [
                {
                    "tgt_tokens": tgt_tokens,
                    "tgt_subwords": tgt_tokens,
                    "alignments": "None",
                    "tgt": translated_text_raw
                }
            ]
        }
        time.sleep(0.1)
        return self.response
