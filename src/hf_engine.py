import torch
import traceback
from transformers import AutoTokenizer, AutoModelForCausalLM

class HFModelEngine:
    def __init__(self, debug=False):
        self.model = None
        self.tokenizer = None
        self.device = None
        self.debug = debug
        
        if self.debug:
            print(f"[DEBUG ENGINE] HFModelEngine instance created. (Instance ID: {id(self)})")

    def load_model(self, model_name, device='cuda', trust_remote_code=True):
        if self.debug:
            print(f"[DEBUG ENGINE] Starting load_model() for: '{model_name}' on device: '{device}'")
            
        try:
            # 1. Device selection
            if (device == 'mps' or device == 'cuda') and torch.backends.mps.is_available():
                self.device = torch.device("mps")
                dtype = torch.float16
                device_map = None
            elif device == 'cuda' and torch.cuda.is_available():
                self.device = torch.device("cuda")
                dtype = torch.bfloat16
                device_map = "auto"
            else:
                self.device = torch.device("cpu")
                dtype = torch.float32
                device_map = None

            if self.debug:
                print(f"[DEBUG ENGINE] Assigned device: {self.device}, Dtype: {dtype}")

            # 2. Load Tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name, 
                trust_remote_code=trust_remote_code
            )
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # 3. Load Model
            load_kwargs = {
                "dtype": dtype,
                "trust_remote_code": trust_remote_code,
                "low_cpu_mem_usage": True
            }
            if device_map:
                load_kwargs["device_map"] = device_map

            self.model = AutoModelForCausalLM.from_pretrained(model_name, **load_kwargs)

            if device_map is None:
                self.model.to(self.device)

            if self.debug:
                print("[DEBUG ENGINE] Model loaded successfully! (self.model is valid)")
            return True

        except Exception as e:
            print(f"[ERROR ENGINE] Critical error loading model: {e}")
            if self.debug:
                traceback.print_exc()
            self.model = None
            self.tokenizer = None
            return False

    def generate(self, user_text, gen_config):
        if self.debug:
            print(f"[DEBUG ENGINE] Calling generate(). Instance ID: {id(self)}")
        
        if self.model is None or self.tokenizer is None:
            return "Error: Model not loaded"

        try:
            messages = [{"role": "user", "content": user_text}]
            prompt = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            input_length = inputs.input_ids.shape[1]

            num_beams = int(gen_config.get('num_beams', 1))
            temp = float(gen_config.get('temperature', 0.0))
            use_eos = gen_config.get('use_eos_token', True)

            # 1. Paràmetres base
            gen_args = {
                "max_new_tokens": gen_config.get('max_new_tokens', 128),
                "repetition_penalty": float(gen_config.get('repetition_penalty', 1.0)),
                "no_repeat_ngram_size": int(gen_config.get('no_repeat_ngram_size', 0)), # AFEDIT
                "pad_token_id": self.tokenizer.pad_token_id,
                "eos_token_id": self.tokenizer.eos_token_id if use_eos else None,       # ACTUALITZAT
            }

            # 2. Estratègia de cerca / sampling
            if num_beams > 1:
                gen_args["num_beams"] = num_beams
                gen_args["early_stopping"] = True
                gen_args["do_sample"] = False
            elif temp > 0.0:
                gen_args["do_sample"] = True
                gen_args["temperature"] = temp
                gen_args["top_k"] = int(gen_config.get('top_k', 40))                    # AFEDIT
                gen_args["top_p"] = float(gen_config.get('top_p', 0.9))
            else:
                gen_args["do_sample"] = False

            # 3. Stop sequences (afegides de forma segura si existeixen al YAML)
            stops = gen_config.get('stop_sequences', [])
            if stops:
                # Formatitzem les seqüències de parada (p. ex. convertint \n literals)
                clean_stops = [s.replace("\\n", "\n") for s in stops]
                gen_args["stop_strings"] = clean_stops
                gen_args["tokenizer"] = self.tokenizer                                   # Requerit per a stop_strings

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    **gen_args
                )

            generated_tokens = outputs[0][input_length:]
            translation = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
            return translation.strip()

        except Exception as e:
            print(f"[ERROR ENGINE] Exception during generation: {e}")
            if self.debug:
                traceback.print_exc()
            return ""

    def post_process(self, text):
        return text.strip()
