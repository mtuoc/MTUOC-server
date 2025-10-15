configfile=None
MTUOCServer_port=""
MTUOCServer_MTengine=""



multilingual=False
verbosity_level=3
log_file="log.log"
sortidalog=None

SLcode=""
TLcode=""

src=""
src_modtags=""
src_notags=""
src_tokens=""
src_notags_tokens=""
translation={}

#Preprocess
max_segment_chars=1000
checkistranslatable=False

preprocessor=None
remove_tags=True
tokenizerSL=None
tokenizerTL=None

tokenize=False
truecase="never"
truecaser=None
use_MosesPunctNormalizer=False
mpn=None
fixencoding=False
unescape_html=False

sentencepiece=False
spmodel=None
sentencepiecetokenizer=None

#segment with SRX file
segment=True
segmenter=None
srxfiles=[]
srxlang=""
segmenters=[]

splitlongsegments=False
maxlong=10000
separators=[";",":",","]


change_input=False


remove_control_characters=True
remove_non_printable=True
remove_non_latin_extended_chars=False
remove_non_unicode_script_chars=True

hastags=False

casetype=None

#Postproces
postprocessor=None
restore_case=False
restore_tags=False

numeric_check=False

change_output=False
change_translation=False

calculate_sbert=False
sbertScorer=None
sort_by_sbert=False

#Marian
ws=None
MarianTranslator=None
startMarianServer=False
startMarianCommand=""
MarianIP=""
MarianPort=""
Marian_model=""
Marian_sl_vocab=""
Marian_tl_vocab=""

Marian_subword_type=None
Marian_subword_model=None

#Aina
AinaTranslator=None
AinaTranslator_model_path=""
AinaTranslator_revision=""
AinaTranslator_beam_size=1
AinaTranslator_num_hypotheses=1

#SalamandraTA
SalamandraTATranslator=None
SalamandraTATranslator_src_lang=""
SalamandraTATranslator_tgt_lang=""
SalamandraTATranslator_model_id=""
SalamandraTATranslator_beam_size=1
SalamandraTATranslator_num_hypotheses=1

#Transformers
TransformersTranslator=None
Transformers_model_path=None
Transformers_beam_size=1
Transformers_num_hypotheses=1

#NLLB
NLLB_model=None
NLLB_device="cpu"
NLLB_beam_size=1
NLLB_num_hypotheses=1
NLLB_src_lang=None
NLLB_tgt_lang=None
NLLB_translator=None

#M2M100
M2M100_model=None
M2M100_beam_size=1
M2M100_num_hypotheses=1
M2M100_translator=None

#Softcatalà

softcatala_model_dir=None
softcatala_translator=None
softcatala_beam_size=1
softcatala_num_hypotheses=1

#ctranslate2
ctranslate2_translation_model=None
ctranslate2_SL_spmodel=None
ctranslate2_TL_spmodel=None
ctranslate2_src_lang=None
ctranslate2_tgt_lang=None
beam_size=None
num_hypotheses=None
ctranslate2_translator=None
ctranslate2_SL_sp=None
ctranslate2_TL_sp=None
ctranslate2_device="cpu"

#Llama
Llama_translator=None
Llama_model=None
Llama_role=None
Llama_max_new_tokens=256
Llama_instruct_prefix=None
Llama_instruct_postfix=None

#Apertium

apertium_mark_unknown=False

#GetWordAlignments
GetWordAlignments_type="fast_align"
wordaligner=None
GetWordAlignments_tokenizerSL=None
GetWordAlignments_tokenizerTL=None

#type OpenMT
MTUOCServer_ONMT_url_root=None

#Ollama
ollamaTranslator=None
ollama_model=None
ollama_role_use=None
ollama_role_system=None
ollama_role_assistan=None
ollama_extract_regex=None
ollama_system_content=None
ollama_temperature: 0.8  
ollama_top_p: 0.9        
ollama_top_k: 40         
ollama_repeat_penalty: 1.1  
ollama_seed: None          
ollama_num_predict: -1
ollama_json: False

#HF-Posteditor
AutomaticPostedition: False
postedition_sbert_threshold: 1


HFPosteditor: None

HFP_model: None
HFP_sourceLanguage: None
HFP_targetLanguage: None
HFP_template: None

#Ollama Posteditor:
OllamaPosteditor=None
OllamaPosteditor_model=None
OllamaPosteditor_sourceLanguage=None
OllamaPosteditor_targetLanguage=None
OllamaPosteditor_role_user=None
OllamaPosteditor_role_system=None
OllamaPosteditor_role_assistant=None
OllamaPosteditor_extract_regex=None
OllamaPosteditor_temperature=0.8
OllamaPosteditor_top_p=0.9
OllamaPosteditor_top_k=40
OllamaPosteditor_repeat_penalty=1.1
OllamaPosteditor_seed=None
OllamaPosteditor_num_predict=-1
OllamaPosteditor_json=False
