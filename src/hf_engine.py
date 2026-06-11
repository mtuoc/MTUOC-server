import torch
from transformers import pipeline, GenerationConfig

class HFModelEngine:
    def __init__(self):
        self.pipe = None
        self.tokenizer = None

    def load_model(self, model_name, device='cuda', trust_remote_code=True):
        try:
            # Determinem el mapa de dispositius: 'auto' utilitzarà la GPU si està disponible
            dev_map = "auto" if torch.cuda.is_available() and device == 'cuda' else None
            
            self.pipe = pipeline(
                "text-generation",
                model=model_name,
                device_map=dev_map,  # Canviat 'device=0' per 'device_map="auto"'
                trust_remote_code=trust_remote_code,
                torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32 # Canviat 'dtype' per 'torch_dtype'
            )
            self.tokenizer = self.pipe.tokenizer
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

    def generate(self, user_text, gen_config):
        if not self.pipe: 
            return "Error: Model not loaded"

        # 1. Preparar el prompt amb el format de xat (ChatML)
        messages = [{"role": "user", "content": user_text}]
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        # 2. Extraure valors de configuració per decidir l'estratègia
        temp_value = float(gen_config.get('temperature', 0.0))
        num_beams = int(gen_config.get('num_beams', 1))
        
        # 3. Construir els arguments base en un diccionari net
        # Afegim "clean_up_tokenization_spaces" aquí directament
        pipeline_kwargs = {
            "clean_up_tokenization_spaces": False
        }

        # Creem el diccionari de paràmetres de generació pur
        generation_kwargs = {
            "max_new_tokens": gen_config.get('max_new_tokens', 128),
            "repetition_penalty": float(gen_config.get('repetition_penalty', 1.0)),
            "no_repeat_ngram_size": int(gen_config.get('no_repeat_ngram_size', 0)),
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id if gen_config.get('use_eos_token', True) else None,
        }

        # 4. Lògica d'estratègia
        if num_beams > 1:
            generation_kwargs["do_sample"] = False
            generation_kwargs["num_beams"] = num_beams
            generation_kwargs["early_stopping"] = True
        elif temp_value > 0:
            generation_kwargs["do_sample"] = True
            generation_kwargs["temperature"] = temp_value
            generation_kwargs["top_k"] = gen_config.get('top_k', 40)
            generation_kwargs["top_p"] = gen_config.get('top_p', 0.9)
        else:
            generation_kwargs["do_sample"] = False

        # 5. Afegir Stop Sequences si n'hi ha
        stops = [s.replace("\\n", "\n") for s in gen_config.get('stop_sequences', [])]
        if stops:
            generation_kwargs["stop_strings"] = stops
            # El tokenizer és necessari si s'usen stop_strings amb GenerationConfig
            pipeline_kwargs["tokenizer"] = self.tokenizer 

        # --- AQUÍ ESTÀ LA SOLUCIÓ ALS WARNINGS ---
        # 1. Instanciem un objecte GenerationConfig buit i net (així evitem max_length=20)
        gen_config_obj = GenerationConfig()
        
        # 2. Hi bolquem tots els nostres paràmetres de generació
        for key, value in generation_kwargs.items():
            setattr(gen_config_obj, key, value)
        
        # 3. Forcem que max_length sigui None per evitar que s'autocalculi o xoqui amb max_new_tokens
        gen_config_obj.max_length = None
        # ----------------------------------------

        # 6. Execució de la pipeline passant el bloc de configuració separat
        try:
            res = self.pipe(
                prompt, 
                generation_config=gen_config_obj, # Enviem l'objecte oficial de configuració
                return_full_text=False,
                **pipeline_kwargs                  # Paràmetres exclusius de la pipeline (com els espais)
            )
            return res[0]['generated_text'].strip()
        except Exception as e:
            print(f"Error durant la generació: {e}")
            return ""

    def post_process(self, text):
        return text.replace("<|im_end|>", "").strip()
