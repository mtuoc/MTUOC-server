#    NLLBTranslator v 2602
#    Description: an MTUOC server using Sentence Piece as preprocessing step
#    Copyright (C) 2024  Antoni Oliver
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.


from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM, NllbTokenizerFast
import torch

class NLLBTranslator:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = -1  # Per defecte a CPU
        self.src_lang = None
        self.tgt_lang = None
        self.translator = None
        self.beam_size = 1
        self.num_hypotheses = 1
        self.response = {}

    def clean(self, llista):
        # Filtrem els tokens especials de la llista
        special_tokens = ["<s>", "</s>", self.src_lang, self.tgt_lang, "<pad>"]
        return [item for item in llista if item not in special_tokens]

    def set_device(self, device):
        if device == "auto":
            self.device = 0 if torch.cuda.is_available() else -1
        elif device == "cpu":
            self.device = -1
        elif device == "gpu":
            self.device = 0 if torch.cuda.is_available() else -1
        # Nota: En pipelines de 'transformers', el device es defineix per ID (0, 1...) o -1 (CPU)

    '''
    def set_model(self, model_name, src_lang, tgt_lang):
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        
        # Carreguem model i tokenizer explícitament
        # Afegim tie_word_embeddings=False per silenciar els avisos
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name, tie_word_embeddings=False)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, src_lang=self.src_lang, tgt_lang=self.tgt_lang)
        
        # Movem el model al dispositiu correcte (GPU o CPU)
        if self.device != -1:
            self.model = self.model.to(f"cuda:{self.device}" if isinstance(self.device, int) else self.device)
        
        # Ja no necessitem self.translator = pipeline(...)
    '''
    

    def set_model(self, model_name, src_lang, tgt_lang):
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        
        # Carreguem el tokenizer de NLLB forçant el mode Fast
        # src_lang per a NLLB sol ser de l'estil 'spa_Latn', 'ocn_Latn', etc.
        self.tokenizer = NllbTokenizerFast.from_pretrained(
            model_name, 
            src_lang=self.src_lang, 
            tgt_lang=self.tgt_lang,
            use_fast=True
        )
        
        # Carreguem el model
        # Ara que el tokenizer és correcte, la mida del vocabulari quadrarà
        # i els pesos d'embed_tokens NO apareixeran com a MISSING.
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        if self.device != -1:
            device_str = f"cuda:{self.device}" if isinstance(self.device, int) else self.device
            self.model = self.model.to(device_str)

    def translate(self, text):
        self.alternate_translations = []
        
        # 1. Preparem els inputs
        inputs = self.tokenizer(text, return_tensors="pt")
        # Ens assegurem que tot estigui al mateix dispositiu (CPU o GPU)
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        #src_tokens per a la resposta
        self.src_tokens = self.clean(self.tokenizer.convert_ids_to_tokens(inputs['input_ids'][0]))

        # 2. Identificació robusta de l'ID de l'idioma
        # Intentem obtenir l'ID. Si no existeix, el servidor petarà aquí amb un error clar.
        if self.tgt_lang not in self.tokenizer.get_vocab():
            # Això ens avisarà si el codi d'idioma (ex: 'cat_Latn') no és el que el model espera
            print(f"ERROR: L'idioma {self.tgt_lang} no està al vocabulari del tokenizer!")
            # Opcional: imprimir els primers 10 idiomes disponibles per ajudar a debuguejar
            # print("Idiomes disponibles:", [t for t in self.tokenizer.additional_special_tokens if '_' in t][:10])
        
        tgt_lang_id = self.tokenizer.convert_tokens_to_ids(self.tgt_lang)

        # 3. Generació directa
        try:
            generated_tokens = self.model.generate(
                input_ids=inputs['input_ids'],
                attention_mask=inputs.get('attention_mask'),
                forced_bos_token_id=tgt_lang_id,
                max_length=1024,
                num_beams=self.beam_size,
                num_return_sequences=self.num_hypotheses
            )
        except Exception as e:
            print(f"Error a model.generate: {e}")
            raise e

        # 4. Processament de resultats
        for i in range(len(generated_tokens)):
            alternate_translation = {}
            token_ids = generated_tokens[i]
            
            # Decodificació neta
            tgt_text = self.tokenizer.decode(token_ids, skip_special_tokens=True)
            
            # Tokens per al format MTUOC
            tgt_tokens_list = self.tokenizer.convert_ids_to_tokens(token_ids)
            tgt_tokens_list = self.clean(tgt_tokens_list)
            
            alternate_translation["tgt_tokens"] = " ".join(tgt_tokens_list)
            alternate_translation["alignments"] = "None"
            alternate_translation["tgt"] = tgt_text
            self.alternate_translations.append(alternate_translation)

        # 5. Resposta final
        self.response = {
            "src_tokens": " ".join(self.src_tokens),
            "tgt_tokens": self.alternate_translations[0]["tgt_tokens"],
            "src_subwords": " ".join(self.src_tokens),
            "tgt_subwords": self.alternate_translations[0]["tgt_tokens"],
            "tgt": self.alternate_translations[0]["tgt"],
            "alignment": "None",
            "alternate_translations": self.alternate_translations
        }
        return self.response
        
    def set_beam_size(self, beam_size):
        self.beam_size = beam_size

    def set_num_hypotheses(self, num_hypotheses):
        self.num_hypotheses = num_hypotheses

    
