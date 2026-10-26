# VllmTranslator v 2610 (vLLM Extended Sampling Parameters)
# Description: An MTUOC translator client supporting all vLLM/OpenAI generation parameters
# Copyright (C) 2026 Antoni Oliver / Extended for vLLM full parameters

import yaml
from openai import OpenAI

class VllmTranslator:
    def __init__(self, config_path=None):
        self.client = None
        self.host = "127.0.0.1"
        self.port = 8000
        self.api_key = "EMPTY"
        self.model_name = ""
        
        # Prompts i llengües
        self.src_lang = "English"
        self.tgt_lang = "Catalan"
        self.system_prompt = ""
        self.user_prompt_template = "Translate the following text from {src_lang} to {tgt_lang}.\n{src_lang}: {text}\n{tgt_lang}:"

        # Diccionari per emmagatzemar tots els paràmetres de generació vLLM
        self.sampling_params = {}

        print("INFO: VllmTranslator client initialized")

        if config_path:
            self.load_from_config(config_path)

    def load_from_config(self, config_path):
        """Llegeix el fitxer YAML i inicialitza la connexió i els paràmetres amb el servidor vLLM."""
        try:
            print("Loading config inside class: ", config_path)
            with open(config_path, 'r', encoding="utf-8") as stream:
                config_yaml = yaml.load(stream, Loader=yaml.FullLoader)

            vllm_config = config_yaml.get("VLLM", {})

            # Connexió i configuració de xarxa
            self.host = vllm_config.get("host", "127.0.0.1")
            self.port = vllm_config.get("port", 8000)
            self.api_key = vllm_config.get("api_key", "EMPTY")
            self.model_name = vllm_config.get("model_name", "default-model")
            
            # Prompts i idiomes
            self.src_lang = vllm_config.get("src_lang", self.src_lang)
            self.tgt_lang = vllm_config.get("tgt_lang", self.tgt_lang)
            self.system_prompt = vllm_config.get("system_prompt", self.system_prompt)
            self.user_prompt_template = vllm_config.get("user_prompt_template", self.user_prompt_template)

            # Carrega de tots els paràmetres de mostratge/generació
            self.sampling_params = {
                "temperature": vllm_config.get("temperature", 0.0),
                "max_tokens": vllm_config.get("max_tokens", 512),
                "top_p": vllm_config.get("top_p", 1.0),
                "presence_penalty": vllm_config.get("presence_penalty", 0.0),
                "frequency_penalty": vllm_config.get("frequency_penalty", 0.0),
                "stop": vllm_config.get("stop", None),
                "seed": vllm_config.get("seed", None),
                "n": vllm_config.get("n", 1),
                "logprobs": vllm_config.get("logprobs", None),
                "top_logprobs": vllm_config.get("top_logprobs", None),
                "logit_bias": vllm_config.get("logit_bias", None),
                "user": vllm_config.get("user", None),
                "response_format": vllm_config.get("response_format", None),
            }

            # Paràmetres addicionals específics de vLLM (es passen a través d'extra_body)
            extra_body = {}
            vllm_extra_keys = [
                "top_k", "min_p", "repetition_penalty", "length_penalty",
                "stop_token_ids", "ignore_eos", "use_beam_search",
                "early_stopping", "best_of", "spaces_between_special_tokens"
            ]

            for key in vllm_extra_keys:
                val = vllm_config.get(key, None)
                if val is not None:
                    extra_body[key] = val

            if extra_body:
                self.sampling_params["extra_body"] = extra_body

            # Inicialitzem el client d'OpenAI apuntant a l'endpoint de vLLM
            base_url = f"http://{self.host}:{self.port}/v1"
            self.client = OpenAI(
                base_url=base_url,
                api_key=self.api_key
            )
            print(f"INFO: Connected to vLLM server at {base_url} (Model: {self.model_name})")

        except Exception as e:
            print(f"ERROR: No s'ha pogut carregar la configuració des de {config_path}. Error: {e}")

    def translate(self, text, src_lang=None, tgt_lang=None, **override_kwargs):
        """
        Realitza la traducció del text passat per paràmetre.
        Permet sobreescriure dinàmicament qualsevol paràmetre de generació a través d'override_kwargs.
        """
        if self.client is None:
            raise ValueError("vLLM Client not initialized. Provide a valid config_path first.")

        # Permet sobreescriure els idiomes dinàmicament
        curr_src = src_lang if src_lang else self.src_lang
        curr_tgt = tgt_lang if tgt_lang else self.tgt_lang

        # Formatem els prompts
        formatted_system_prompt = self.system_prompt.format(src_lang=curr_src, tgt_lang=curr_tgt)
        formatted_user_prompt = self.user_prompt_template.format(text=text, src_lang=curr_src, tgt_lang=curr_tgt)

        messages = []
        if formatted_system_prompt.strip():
            messages.append({"role": "system", "content": formatted_system_prompt})
        messages.append({"role": "user", "content": formatted_user_prompt})

        # Combinem els paràmetres del YAML amb els que es puguin passar en cridar translate()
        payload = {k: v for k, v in self.sampling_params.items() if v is not None}
        payload.update({k: v for k, v in override_kwargs.items() if v is not None})

        # Execució de la petició al servidor vLLM
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **payload
        )

        translated_text = response.choices[0].message.content.strip()

        # Adaptació de la resposta al format estàndard que espera MTUOC
        src_tokens = text.split()
        tgt_tokens = translated_text.split()

        self.response = {
            "src_tokens": " ".join(src_tokens),
            "tgt_tokens": " ".join(tgt_tokens),
            "src_subwords": " ".join(src_tokens),
            "tgt_subwords": " ".join(tgt_tokens),
            "tgt": translated_text,
            "alignment": "None",
            "alternate_translations": [
                {
                    "tgt_tokens": " ".join(tgt_tokens),
                    "tgt_subwords": " ".join(tgt_tokens),
                    "alignments": "None",
                    "tgt": translated_text
                }
            ]
        }

        return self.response
