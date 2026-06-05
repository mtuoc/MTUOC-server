import torch
from transformers import pipeline

class HFModelEngine:
    def __init__(self):
        self.pipe = None
        self.tokenizer = None

    def load_model(self, model_name, device='cuda', trust_remote_code=True):
        try:
            self.pipe = pipeline(
                "text-generation",
                model=model_name,
                device=0 if torch.cuda.is_available() and device == 'cuda' else -1,
                trust_remote_code=trust_remote_code,
                dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32
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
        
        # 3. Construir els arguments base (comuns a totes les estratègies)
        gen_args = {
            "max_new_tokens": gen_config.get('max_new_tokens', 128),
            "repetition_penalty": float(gen_config.get('repetition_penalty', 1.0)),
            "no_repeat_ngram_size": int(gen_config.get('no_repeat_ngram_size', 0)),
            "return_full_text": False,
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id if gen_config.get('use_eos_token', True) else None
        }

        # 4. Lògica d'estratègia: Seleccionem només els flags vàlids
        if num_beams > 1:
            # ESTRATÈGIA: Beam Search (Determinista, cerca múltiple)
            gen_args["do_sample"] = False
            gen_args["num_beams"] = num_beams
            gen_args["early_stopping"] = True
            # En Beam Search NO s'ha de passar temperature, top_k ni top_p
        
        elif temp_value > 0:
            # ESTRATÈGIA: Sampling (Amb aleatorietat/creativitat)
            gen_args["do_sample"] = True
            gen_args["temperature"] = temp_value
            gen_args["top_k"] = gen_config.get('top_k', 40)
            gen_args["top_p"] = gen_config.get('top_p', 0.9)
        
        else:
            # ESTRATÈGIA: Greedy Search (Determinista, tria sempre la més probable)
            gen_args["do_sample"] = False
            # En Greedy Search NO s'ha de passar temperature ni paràmetres de sampling

        # 5. Afegir Stop Sequences si n'hi ha
        stops = [s.replace("\\n", "\n") for s in gen_config.get('stop_sequences', [])]
        if stops:
            gen_args["stop_strings"] = stops
            gen_args["tokenizer"] = self.tokenizer

        # 6. Execució de la pipeline
        try:
            res = self.pipe(prompt, **gen_args)
            return res[0]['generated_text'].strip()
        except Exception as e:
            print(f"Error durant la generació: {e}")
            return ""

    def post_process(self, text):
        # Neteja bàsica de possibles tokens residuals
        return text.replace("<|im_end|>", "").strip()
