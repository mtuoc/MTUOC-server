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
                torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32
            )
            self.tokenizer = self.pipe.tokenizer
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

    def generate(self, user_text, gen_config):
        if not self.pipe: return "Error: Model not loaded"

        # Generalització: usem el template del model (ChatML per Salamandra)
        messages = [{"role": "user", "content": user_text}]
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        # Mapegem els paràmetres que venen del YAML (via HFTranslator)
        gen_args = {
            "max_new_tokens": gen_config.get('max_new_tokens', 128),
            "do_sample": float(gen_config.get('temperature', 0.0)) > 0,
            "repetition_penalty": float(gen_config.get('repetition_penalty', 1.0)),
            "no_repeat_ngram_size": int(gen_config.get('no_repeat_ngram_size', 0)),
            "return_full_text": False,
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id if gen_config.get('use_eos_token', True) else None
        }

        if gen_args["do_sample"]:
            gen_args["temperature"] = float(gen_config.get('temperature'))
            gen_args["top_k"] = gen_config.get('top_k', 40)
            gen_args["top_p"] = gen_config.get('top_p', 0.9)

        if gen_config.get('num_beams', 1) > 1:
            gen_args["num_beams"] = gen_config['num_beams']
            gen_args["early_stopping"] = True

        # Stop sequences per tallar la sobregeneració
        stops = [s.replace("\\n", "\n") for s in gen_config.get('stop_sequences', [])]
        if stops:
            gen_args["stop_strings"] = stops
            gen_args["tokenizer"] = self.tokenizer

        res = self.pipe(prompt, **gen_args)
        return res[0]['generated_text'].strip()

    def post_process(self, text):
        # Neteja bàsica de possibles tokens residuals
        return text.replace("<|im_end|>", "").strip()
