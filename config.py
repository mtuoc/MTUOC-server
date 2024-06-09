segment_input=False
SRX_file=None

remove_control_characters=False
remove_non_printable=False
norm_apos=False
unescape_html=False
fixencoding=False
escapeforMoses=False

change_input_files=None
change_output_files=None
change_translation_files=None
changes_input=[]
changes_output=[]
changes_translation=[]

alternate_translations=True

checkistranslatable=False

multilingual=None



remove_tags: False
tagrestorer=None
missing_tags: "ignore"
hastags=False
segmentORIG=""
segmentORIGMOD=""
segmentPRETAGS=""
equil={}
segmentNOTAGS=""
segmentTOTRANSLATE=""
segmentTAGSMOD=""
TAGSEQUIL={}
segmentNOTIF=""
STARTINGTAG=""
CLOSINGTAG=""


translationPRE=""
translationPOST=""
translation={}
segmentTOTRANSLATE=""
detruecasePOST=False

tagInici=""
tagFinal=""
originaltags=[]

detect_language=False
fasttext_model="lid.176.bin"
fasttext_min_confidence: 0.75
sl_lang=None
#Marian
startMarianCommand=None
MarianIP=None
MarianPort=None


MTUOCServer_port=""
MTUOCServer_MTengine=""
startMTEngineV=False
startMTEngineCommand=""
MTUOCServer_type=""
MTEngineIP=""
MTEnginePort=""
verbosity_level=0
log_file=""
sortidalog=""
min_len_factor=0.5
min_chars_segment=1
tag_restoration=False
fix_xml=False

SRXfile=None
SRXlang=None
rules=None

#preprocessing

tokenize_SL=False
tokenize_TL=False
sl_tokenizer=None
tl_tokenizer=None
tokenizerSLType=""
tokenizerTLType=""
tokenizerSL=None
tokenizerTL=None

tcmodel=""
truecase=""
truecaser=None
isupper=False

replace_URLs=False
replace_EMAILs=False

code_URLs="@URL@"
code_EMAILs="@EMAIL@"

replace_NUMs=False
code_NUMs="@NUM@"
split_NUMs=False

#sentencepiece
sentencepiece=""
spmodelSL=""
spmodelTL=""
sp_splitter=""

bos_annotate=False
bos_symbol="<s>"
#None or <s> (or other)
eos_annotate=False
eos_symbol="</s>"

spSL=None
spTL=None

#BPE
BPE=""
bpecodes=""
bpe_joiner=""
bpeobject=None


leading_spaces=0
trailing_spaces=0

MTUOCServer_NUMs=False
MTUOCServer_splitNUMs=False

escape_html_input=False
unescape_html_input=True

translation_selection_strategy="First"

Google_sllang=""
Google_tllang=""
Google_glossary=""
Google_project_id=""
Google_location=""
Google_jsonfile=""
client=None
parent=None

DeepL_API_key=""
DeepL_sl_lang=""
DeepL_tl_lang=""
DeepL_formality=""
DeepL_split_sentences=""
DeepL_glossary=""
DeepLtranslator=None

Lucy_url=""
Lucy_TRANSLATION_DIRECTION=""
Lucy_MARK_UNKNOWNS=""
Lucy_MARK_ALTERNATIVES=""
Lucy_MARK_COMPOUNDS=""
Lucy_CHARSET=""

MTUOCServer_ONMT_url_root=None

proxyMoses=None

OpusMT_model=None
OpusMT_multilingual=False
OpusMT_target_language=None
OpusMT_translator=None
OpusMT_beam_size=1
OpusMT_num_hypotheses=1

NLLB_model=None
NLLB_beam_size=1
NLLB_num_hypotheses=1
NLLB_src_lang=None
NLLB_tgt_lang=None
NLLB_translator=None

softcatala_model_dir=None
softcatala_translator=None
softcatala_beam_size=1
softcatala_num_hypotheses=1

apertium_sl=None
apertium_tl=None
apertium_translator=None

