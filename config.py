MTUOCServer_port=""
MTUOCServer_MTengine=""
multilingual=False
verbosity_level=3
log_file="log.log"
sortidalog=""

SLcode=""
TLcode=""

src=""
src_modtags=""
src_notags=""
src_tokens=""
src_notags_tokens=""
translation={}

#Preprocess
checkistranslatable=False

preprocessor=None
remove_tags=True
tokenizerSL=None
tokenizerTL=None

tokenize=False
truecase="never"

use_MosesPunctNormalizer=False
mpn=None
fixencoding=False
unescape_html=False

#segment with SRX file
segment=True
segmenter=None
srxfiles=[]
srxlang=""
segmenters=[]
strategy="bysegments"

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

#Transformers
TransformersTranslator=None
Transformers_model_path=None
Transformers_beam_size=1
Transformers_num_hypotheses=1

#NLLB
NLLB_model=None
NLLB_beam_size=1
NLLB_num_hypotheses=1
NLLB_src_lang=None
NLLB_tgt_lang=None
NLLB_translator=None


#GetWordAlignments
GetWordAlignments_type="fast_align"
wordaligner=None
GetWordAlignments_tokenizerSL=None
GetWordAlignments_tokenizerTL=None
