#    MTUOC-server v 2507
#    Description: an MTUOC server using Sentence Piece as preprocessing step
#    Copyright (C) 2025  Antoni Oliver
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


import yaml
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
    
import sys
import config
import codecs


from MTUOC_misc import printLOG
from MTUOC_misc import get_IP_info
from MTUOC_Preprocessor import Preprocessor
from MTUOC_Postprocessor import Postprocessor


if len(sys.argv)>1:
    configfile=sys.argv[1]
else:
    configfile="config-server.yaml"

stream = open(configfile, 'r',encoding="utf-8")
configYAML=yaml.load(stream, Loader=yaml.FullLoader)

config.preprocessor=Preprocessor()
config.postprocessor=Postprocessor()

config.system_name=configYAML["system_name"]
config.MTUOCServer_MTengine=configYAML["MTengine"]


config.MTUOCServer_type=configYAML["MTUOCServer"]["type"]
config.MTUOCServer_port=configYAML["MTUOCServer"]["port"]



config.verbosity_level=int(configYAML["MTUOCServer"]["verbosity_level"])
config.log_file=configYAML["MTUOCServer"]["log_file"]

if config.log_file=="None":
    config.log_file=False
else:
    config.sortidalog=codecs.open(config.log_file,"a",encoding="utf-8")
    config.log_file=True
    
config.max_segment_chars=1000000000
config.checkistranslatable=False
config.use_MosesPunctNormalizer=False
config.mpn = None
tokenize=False
tokenizer=None
MosesTokenizerLang=None
config.tokenizerSL=None
config.truecase=False
truecaser=None
truecaser_tokenizer=None
tcmodel=None
MosesTokenizerLang=None
config.remove_tags=False
config.segment=False
config.srxfiles=None
config.srxlang=None
config.segmenters=[]

config.splitlongsegments=False
config.maxlong=100000000
config.separators=None
change_input_files=None
change_input_delimiter=None
change_input_quote=None
changes_input=[]
config.preprocessor.set_changes_input(changes_input)
change_output_files=None
change_output_delimiter=None
change_output_quote=None
changes_output=[]
config.postprocessor.set_changes_output(changes_output)
change_translation_files=None
change_translation_delimiter=None
change_translation_quote=None
changes_translation=[]
config.postprocessor.set_changes_translation(changes_translation)
config.remove_control_characters=False
config.remove_non_printable=False
config.remove_non_latin_extended_chars=False
config.remove_non_unicode_script_chars=False
config.sentencepiece=False
config.spmodel=None
config.restore_case=False
config.restore_tags=False
config.numeric_check=False
config.GetWordAlignments_type=None
config.GetWordAlignments_tokenizerSL=None
config.GetWordAlignments_tokenizerTL=None
GetWordAlignments_tokenizerSLcode=None
GetWordAlignments_tokenizerTLcode=None
GetWordAlignments_fwd_params_file=None
GetWordAlignments_fwd_err_file=None
GetWordAlignments_rev_params_file=None
GetWordAlignments_rev_err_file=None
    
config.max_segment_chars=configYAML["Preprocess"]["max_segment_chars"]
config.checkistranslatable=configYAML["Preprocess"]["checkistranslatable"]
config.use_MosesPunctNormalizer=configYAML["Preprocess"]["use_MosesPunctNormalizer"]
if config.use_MosesPunctNormalizer:
    from sacremoses import MosesPunctNormalizer
    config.mpn = MosesPunctNormalizer()
    

tokenize=configYAML["Preprocess"]["tokenize"]
tokenizer=configYAML["Preprocess"]["tokenizer"]
MosesTokenizerLang=configYAML["Preprocess"]["MosesTokenizerLang"]

if tokenize and tokenizer=="Moses":
    from sacremoses import MosesTokenizer, MosesDetokenizer
    config.tokenizerSL=MosesTokenizer(lang=MosesTokenizerLang)

if tokenizer.startswith("MTUOC"):
    import importlib.util
    if not tokenizer.endswith(".py"): tokenizer=tokenizer+".py"
    spec = importlib.util.spec_from_file_location('', tokenizer)
    tokenizermod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tokenizermod)
    config.tokenizerSL=tokenizermod.Tokenizer()

config.truecase=configYAML["Preprocess"]["truecase"]
truecaser=configYAML["Preprocess"]["truecaser"]
truecaser_tokenizer=configYAML["Preprocess"]["truecaser_tokenizer"]
tcmodel=configYAML["Preprocess"]["tcmodel"]
MosesTokenizerLang=configYAML["Preprocess"]["MosesTokenizerLang"]
    

    
config.unescape_html=configYAML["Preprocess"]["unescape_html"]
config.fixencoding=configYAML["Preprocess"]["fixencoding"]
config.escapeforMoses=configYAML["Preprocess"]["escapeforMoses"]



config.remove_tags=configYAML["Preprocess"]["remove_tags"]

config.segment=configYAML["Preprocess"]["segment"]
config.srxfiles=configYAML["Preprocess"]["srxfiles"].split(" ")
config.srxlang=configYAML["Preprocess"]["srxlang"]

config.segmenters=[]
if config.segment:
    from MTUOC_SRXSegmenter import InputSegmenter
    config.segmenters=[]
    for srxfile in config.srxfiles:
        segmenter=InputSegmenter()
        segmenter.set_srx_file(srxfile,config.srxlang)
        config.segmenters.append(segmenter)


config.splitlongsegments=configYAML["Preprocess"]["splitlongsegments"]
config.maxlong=configYAML["Preprocess"]["maxlong"]
config.separators=configYAML["Preprocess"]["separators"].split()

change_input_files=configYAML["Preprocess"]["change_input_files"].split(" ")
change_input_delimiter=configYAML["Preprocess"]["change_input_delimiter"]
change_input_quote=configYAML["Preprocess"]["change_input_quote"]
changes_input=[]
if not change_input_files[0]=="None":
    config.change_input=True
    import csv
    for ci in change_input_files:
        with open(ci) as csvfile:
            csvreader = csv.reader(csvfile, delimiter=change_input_delimiter, quotechar=change_input_quote)
            for row in csvreader:
                changes_input.append(row)

config.preprocessor.set_changes_input(changes_input)

change_output_files=configYAML["Postprocess"]["change_output_files"].split(" ")
change_output_delimiter=configYAML["Postprocess"]["change_output_delimiter"]
change_output_quote=configYAML["Postprocess"]["change_output_quote"]
changes_output=[]
if not change_output_files[0]=="None":
    config.change_output=True
    import csv
    for ci in change_output_files:
        with open(ci) as csvfile:
            csvreader = csv.reader(csvfile, delimiter=change_output_delimiter, quotechar=change_output_quote)
            for row in csvreader:
                changes_output.append(row)

config.postprocessor.set_changes_output(changes_output)

change_translation_files=configYAML["Postprocess"]["change_translation_files"].split(" ")
change_translation_delimiter=configYAML["Postprocess"]["change_translation_delimiter"]
change_translation_quote=configYAML["Postprocess"]["change_output_quote"]
changes_translation=[]
if not change_translation_files[0]=="None":
    config.change_translation=True
    import csv
    for ci in change_translation_files:
        with open(ci) as csvfile:
            csvreader = csv.reader(csvfile, delimiter=change_translation_delimiter, quotechar=change_translation_quote)
            for row in csvreader:
                changes_translation.append(row)

config.postprocessor.set_changes_translation(changes_translation)

config.remove_control_characters=configYAML["Preprocess"]["remove_control_characters"]
config.remove_non_printable=configYAML["Preprocess"]["remove_non_printable"]
config.remove_non_latin_extended_chars=configYAML["Preprocess"]["remove_non_latin_extended_chars"]
config.remove_non_unicode_script_chars=configYAML["Preprocess"]["remove_non_unicode_script_chars"]


config.restore_case=configYAML["Postprocess"]["restore_case"]
config.restore_tags=configYAML["Postprocess"]["restore_tags"]
config.numeric_check=configYAML["Postprocess"]["numeric_check"]
config.GetWordAlignments_type=configYAML["GetWordAlignments"]["type"]


config.GetWordAlignments_tokenizerSL=configYAML["GetWordAlignments"]["tokenizerSL"]
config.GetWordAlignments_tokenizerTL=configYAML["GetWordAlignments"]["tokenizerTL"]
GetWordAlignments_tokenizerSLcode=configYAML["GetWordAlignments"]["tokenizerSLcode"]
GetWordAlignments_tokenizerTLcode=configYAML["GetWordAlignments"]["tokenizerTLcode"]


GetWordAlignments_fwd_params_file=configYAML["GetWordAlignments"]["fwd_params_file"]
GetWordAlignments_fwd_err_file=configYAML["GetWordAlignments"]["fwd_err_file"]

GetWordAlignments_rev_params_file=configYAML["GetWordAlignments"]["rev_params_file"]
GetWordAlignments_rev_err_file=configYAML["GetWordAlignments"]["rev_err_file"]

###
#sbertscorer
config.calculate_sbert=configYAML["Scoring"]["calculate_sbert"]
if config.calculate_sbert:
    from sbertScorer import *
    config.sbertScorer=sbertScorer()
    config.sbertScorer.set_model()
    config.sort_by_sbert=configYAML["Scoring"]["sort_by_sbert"]

####
#Automatic postedition
config.AutomaticPostedition=configYAML["AutomaticPostedition"]["type"]
config.postedition_sbert_threshold=configYAML["AutomaticPostedition"]["sbert_threshold"]
if config.calculate_sbert and config.postedition_sbert_threshold:
    config.calculate_sbert=True
if config.AutomaticPostedition=="HFPosteditor":
    from HFPosteditor import *
    stream2 = open("config-HFPosteditor.yaml", 'r',encoding="utf-8")
    configYAML2=yaml.load(stream2, Loader=yaml.FullLoader)
    config.HFP_model=configYAML2["model"]
    config.HFP_sourceLanguage=configYAML2["sourceLanguage"]
    config.HFP_targetLanguage=configYAML2["targetLanguage"]
    config.HFP_template=configYAML2["template"]
    config.HFPosteditor=HFPosteditor()
    config.HFPosteditor.set_model(config.HFP_model)
    config.HFPosteditor.set_sourceLanguage(config.HFP_sourceLanguage)
    config.HFPosteditor.set_targetLanguage(config.HFP_targetLanguage)
    config.HFPosteditor.set_template(config.HFP_template)
elif config.AutomaticPostedition=="OllamaPosteditor":
    from OllamaPosteditor import *
    stream2 = open("config-OllamaPosteditor.yaml", 'r',encoding="utf-8")
    configYAML2=yaml.load(stream2, Loader=yaml.FullLoader)
    config.OllamaPosteditor_model=configYAML2["model"]
    config.OllamaPosteditor_sourceLanguage=configYAML2["sourceLanguage"]
    config.OllamaPosteditor_targetLanguage=configYAML2["targetLanguage"]
    config.OllamaPosteditor_role_user=configYAML2["role_user"]
    config.OllamaPosteditor_role_system=configYAML2["role_system"]
    config.OllamaPosteditor_role_assistant=configYAML2["role_assistant"]
    config.OllamaPosteditor_extract_regex=configYAML2["extract_regex"]
    config.OllamaPosteditor_temperature=configYAML2["temperature"]
    config.OllamaPosteditor_top_p=configYAML2["top_p"]
    config.OllamaPosteditor_top_k=configYAML2["top_k"]
    config.OllamaPosteditor_repeat_penalty=configYAML2["repeat_penalty"]
    config.OllamaPosteditor_seed=configYAML2["seed"]
    config.OllamaPosteditor_num_predict=configYAML2["num_predict"]
    config.OllamaPosteditor_json=configYAML2["json"]
    
    config.OllamaPosteditor=OllamaPosteditor()
    config.OllamaPosteditor.set_model(config.OllamaPosteditor_model)
    config.OllamaPosteditor.set_sourceLanguage(config.OllamaPosteditor_sourceLanguage)
    config.OllamaPosteditor.set_targetLanguage(config.OllamaPosteditor_targetLanguage)
    config.OllamaPosteditor.set_role_user(config.OllamaPosteditor_role_user)
    config.OllamaPosteditor.set_role_system(config.OllamaPosteditor_role_system)
    config.OllamaPosteditor.set_role_assistant(config.OllamaPosteditor_role_assistant)
    
    config.OllamaPosteditor.set_extract_regex(config.OllamaPosteditor_extract_regex)
    config.OllamaPosteditor.set_temperature(config.OllamaPosteditor_temperature)
    config.OllamaPosteditor.set_top_p(config.OllamaPosteditor_top_p)
    config.OllamaPosteditor.set_top_k(config.OllamaPosteditor_top_k)
    config.OllamaPosteditor.set_repeat_penalty(config.OllamaPosteditor_repeat_penalty)
    config.OllamaPosteditor.set_seed(config.OllamaPosteditor_seed)
    config.OllamaPosteditor.set_num_predict(config.OllamaPosteditor_num_predict)
    config.OllamaPosteditor.set_json(config.OllamaPosteditor_json)
    
    

    

    
    
###
if config.MTUOCServer_MTengine=="Marian":
    stream2 = open("config-Marian.yaml", 'r',encoding="utf-8")
    configYAML2=yaml.load(stream2, Loader=yaml.FullLoader)
    from MarianTranslator import MarianTranslator
    config.startMarianServer=configYAML2["Marian"]["startMarianServer"]
    config.startMarianCommand=configYAML2["Marian"]["startMarianCommand"]
    config.MarianIP=configYAML2["Marian"]["IP"]
    config.MarianPort=configYAML2["Marian"]["port"]
    config.MarianTranslator=MarianTranslator()
    config.sentencepiece=configYAML2["Preprocess"]["sentencepiece"]
    config.spmodel=configYAML2["Preprocess"]["spmodel"]
    if config.sentencepiece:
        from SentencePieceTokenizer import SentencePieceTokenizer
        config.sentencepiecetokenizer=SentencePieceTokenizer()
        config.sentencepiecetokenizer.set_spmodel(config.spmodel)
    if config.startMarianServer:
        MarianTranslator.start_marian_server()
        
    config.MarianTranslator.connect_to_Marian()

if config.MTUOCServer_MTengine=="OpusMT":
    stream2 = open("config-OpusMT.yaml", 'r',encoding="utf-8")
    configYAML2=yaml.load(stream2, Loader=yaml.FullLoader)
    from transformers import MarianMTModel, MarianTokenizer
    import torch
    from TransformersTranslator import TransformersTranslator
    config.TransformersTranslator=TransformersTranslator()
    config.Transformers_model_path=configYAML2["OpusMT"]["model_path"]
    config.TransformersTranslator.set_model(config.Transformers_model_path)
    config.Transformers_beam_size=configYAML2["OpusMT"]["beam_size"]
    config.Transformers_num_hypotheses=configYAML2["OpusMT"]["num_hypotheses"]
    config.multilingual=configYAML2["OpusMT"]["multilingual_prefix"]
    config.TransformersTranslator=TransformersTranslator()
    config.TransformersTranslator.set_model(config.Transformers_model_path)
    config.TransformersTranslator.set_beam_size(config.Transformers_beam_size)
    config.TransformersTranslator.set_num_hypotheses(config.Transformers_num_hypotheses)
    printLOG(1,"Translating with OpusMT models",config.Transformers_model_path)

elif config.MTUOCServer_MTengine=="NLLB":
    stream2 = open("config-NLLB.yaml", 'r',encoding="utf-8")
    configYAML2=yaml.load(stream2, Loader=yaml.FullLoader)
    from NLLBTranslator import *
    config.NLLB_model=configYAML2["NLLB"]["model"]
    config.NLLB_beam_size=configYAML2["NLLB"]["beam_size"]
    config.NLLB_num_hypotheses=configYAML2["NLLB"]["num_hypotheses"]
    config.NLLB_src_lang=configYAML2["NLLB"]["src_lang"]
    config.NLLB_tgt_lang=configYAML2["NLLB"]["tgt_lang"]
    config.NLLB_device=configYAML2["NLLB"]["device"]
    config.NLLB_translator=NLLBTranslator()
    config.NLLB_translator.set_device(config.NLLB_device)
    config.NLLB_translator.set_model(config.NLLB_model,config.NLLB_src_lang,config.NLLB_tgt_lang)
    config.NLLB_translator.set_beam_size(config.NLLB_beam_size)
    config.NLLB_translator.set_num_hypotheses(config.NLLB_num_hypotheses)
    printLOG(1,"Translating with NLLB models",config.NLLB_model)
    
elif config.MTUOCServer_MTengine=="Ollama":

    stream2 = open("config-OllamaTranslator.yaml", 'r',encoding="utf-8")
    configYAML2=yaml.load(stream2, Loader=yaml.FullLoader)
    from  OllamaTranslator import *
    config.ollamaTranslator=OllamaTranslator()
    
    config.ollama_model=configYAML2["OllamaTranslator"]["model"]
    config.ollama_role_user=configYAML2["OllamaTranslator"]["role_user"]
    config.ollama_extract_regex=configYAML2["OllamaTranslator"]["extract_regex"]
    config.ollama_role_system=configYAML2["OllamaTranslator"]["role_system"]
    config.ollama_role_assistant=configYAML2["OllamaTranslator"]["role_assistant"]
    
    config.ollama_temperature=configYAML2["OllamaTranslator"]["temperature"]
    config.ollama_top_p=configYAML2["OllamaTranslator"]["top_p"]      
    config.ollama_top_k=configYAML2["OllamaTranslator"]["top_k"]       
    config.ollama_repeat_penalty=configYAML2["OllamaTranslator"]["repeat_penalty"]  
    config.ollama_seed=configYAML2["OllamaTranslator"]["seed"]         
    config.ollama_num_predict=configYAML2["Ollama"]["num_predict"]
    config.ollama_json=configYAML2["OllamaTranslator"]["json"]
    
    config.ollamaTranslator.set_model(config.ollama_model)
    config.ollamaTranslator.set_role_user(config.ollama_role_user)
    config.ollamaTranslator.set_role_system(config.ollama_role_system)
    config.ollamaTranslator.set_role_assistant(config.ollama_role_assistant)
    config.ollamaTranslator.set_extract_regex(config.ollama_extract_regex)
    config.ollamaTranslator.set_temperature(config.ollama_temperature)
    config.ollamaTranslator.set_top_p(config.ollama_top_p)
    config.ollamaTranslator.set_top_k(config.ollama_top_k)
    config.ollamaTranslator.set_repeat_penalty(config.ollama_repeat_penalty)
    config.ollamaTranslator.set_seed(config.ollama_seed)
    config.ollamaTranslator.set_num_predict(config.ollama_num_predict)
    config.ollamaTranslator.set_json(config.ollama_json)
    


    

elif config.MTUOCServer_MTengine=="ctranslate2":
    stream2 = open("config-ctranslate2.yaml", 'r',encoding="utf-8")
    configYAML2=yaml.load(stream2, Loader=yaml.FullLoader)
    from ctranslate2Translator import *
    config.ctranslate2_translation_model=configYAML2["ctranslate2"]["translation_model"]
    config.ctranslate2_SL_spmodel=configYAML2["ctranslate2"]["SL_spmodel"]
    config.ctranslate2_TL_spmodel=configYAML2["ctranslate2"]["TL_spmodel"]
    config.ctranslate2_src_lang=configYAML2["ctranslate2"]["src_lang"]
    config.ctranslate2_tgt_lang=configYAML2["ctranslate2"]["tgt_lang"]
    config.ctranslate2_beam_size=configYAML2["ctranslate2"]["beam_size"]
    config.ctranslate2_num_hypotheses=configYAML2["ctranslate2"]["num_hypotheses"]
    config.ctranslate2_device=configYAML2["ctranslate2"]["device"]
    config.ctranslate2_translator=ctranslate2Translator()
    config.ctranslate2_translator.set_translation_model(config.ctranslate2_translation_model)
    config.ctranslate2_translator.set_SL_sp_model(config.ctranslate2_SL_spmodel)
    config.ctranslate2_translator.set_TL_sp_model(config.ctranslate2_TL_spmodel)
    config.ctranslate2_translator.set_beam_size(config.ctranslate2_beam_size)
    config.ctranslate2_translator.set_num_hypotheses(config.ctranslate2_num_hypotheses)
    config.ctranslate2_translator.set_device(config.ctranslate2_device)
    config.ctranslate2_translator.set_src_lang(config.ctranslate2_src_lang)
    config.ctranslate2_translator.set_tgt_lang(config.ctranslate2_tgt_lang)
    config.ctranslate2_translator.start_translator()
    #test=config.ctranslate2_translator.translate("Esto es una traducción de prueba")
   

elif config.MTUOCServer_MTengine=="Aina":
    
    config.truecase="upper"
    truecaser="MTUOC"
    
    config.unescape_html=True
    config.fixencoding=True
    config.escapeforMoses=False
    config.remove_tags=True
    config.segment=True
    
    config.splitlongsegments=configYAML["Preprocess"]["splitlongsegments"]
    config.maxlong=configYAML["Preprocess"]["maxlong"]
    config.separators=configYAML["Preprocess"]["separators"].split()


    config.strategy="bysegments"
    config.remove_control_characters=True
    config.remove_non_printable=True
    config.remove_non_latin_extended_chars=False
    config.remove_non_unicode_script_chars=False

    config.restore_case=True
    config.restore_tags=True
    config.numeric_check=False
    config.GetWordAlignments_type="fast_align"
    
    stream2 = open("config-Aina.yaml", 'r',encoding="utf-8")
    configYAML2=yaml.load(stream2, Loader=yaml.FullLoader)
    
    import ctranslate2
    import pyonmttok
    from huggingface_hub import snapshot_download
    from AinaTranslator import AinaTranslator
    model=configYAML2["Aina"]["model"]
    config.AinaTranslator_revision=configYAML2["Aina"]["revision"]
    config.AinaTranslator_beam_size=configYAML2["Aina"]["beam_size"]
    config.AinaTranslator_num_hypotheses=configYAML2["Aina"]["num_hypotheses"]
    if model=="ca-en":
        aina_repo="projecte-aina/aina-translator-ca-en"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-ca-en"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-ca"
        config.AinaTranslator_model_path="./aina-translator-ca-en"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_cat"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_eng"
        GetWordAlignments_fwd_params_file="./aina-translator-ca-en/ca-en.params"
        GetWordAlignments_fwd_err_file="./aina-translator-ca-en/ca-en.err"

        GetWordAlignments_rev_params_file="./aina-translator-ca-en/en-ca.params"
        GetWordAlignments_rev_err_file="./aina-translator-ca-en/en-ca.err"
        truecaser_tokenizer="MTUOC_tokenizer_cat"
        tcmodel="./aina-translator-ca-en/tc.ca"
        config.srxfiles=["segment.srx"]
        config.srxlang="Catalan"
    elif model=="en-ca":
        aina_repo="projecte-aina/aina-translator-en-ca"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-ca-en"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-en"
        config.AinaTranslator_model_path="./aina-translator-en-ca"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_eng"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_cat"
        GetWordAlignments_fwd_params_file="./aina-translator-en-ca/en-ca.params"
        GetWordAlignments_fwd_err_file="./aina-translator-en-ca/en-ca.err"

        GetWordAlignments_rev_params_file="./aina-translator-en-ca/ca-en.params"
        GetWordAlignments_rev_err_file="./aina-translator-en-ca/ca-en.err"
        truecaser_tokenizer="MTUOC_tokenizer_eng"
        tcmodel="./aina-translator-en-ca/tc.en"
        config.srxfiles=["segment.srx"]
        config.srxlang="English"
    if model=="ca-de":
        aina_repo="projecte-aina/aina-translator-ca-de"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-ca-de"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-de"
        config.AinaTranslator_model_path="./aina-translator-ca-de"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_cat"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_deu"
        GetWordAlignments_fwd_params_file="./aina-translator-ca-de/ca-de.params"
        GetWordAlignments_fwd_err_file="./aina-translator-ca-de/ca-de.err"

        GetWordAlignments_rev_params_file="./aina-translator-ca-de/de-ca.params"
        GetWordAlignments_rev_err_file="./aina-translator-ca-de/de-ca.err"
        truecaser_tokenizer="MTUOC_tokenizer_cat"
        tcmodel="./aina-translator-ca-de/tc.de"    
        config.srxfiles=["segment.srx"]
        config.srxlang="Catalan"
        
    elif model=="de-ca":
        aina_repo="projecte-aina/aina-translator-de-ca"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-ca-de"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-de"
        config.AinaTranslator_model_path="./aina-translator-de-ca"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_deu"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_cat"
        GetWordAlignments_fwd_params_file="./aina-translator-de-ca/de-ca.params"
        GetWordAlignments_fwd_err_file="./aina-translator-de-ca/de-ca.err"

        GetWordAlignments_rev_params_file="./aina-translator-de-ca/ca-de.params"
        GetWordAlignments_rev_err_file="./aina-translator-de-ca/ca-de.err"
        truecaser_tokenizer="MTUOC_tokenizer_deu"
        tcmodel="./aina-translator-de-ca/tc.de"
        config.srxfiles=["segment.srx"]
        config.srxlang="German"
        
    if model=="ca-es":
        aina_repo="projecte-aina/aina-translator-ca-es"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-ca-es"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-ca"
        config.AinaTranslator_model_path="./aina-translator-ca-es"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_cat"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_spa"
        GetWordAlignments_fwd_params_file="./aina-translator-ca-es/ca-es.params"
        GetWordAlignments_fwd_err_file="./aina-translator-ca-es/ca-es.err"

        GetWordAlignments_rev_params_file="./aina-translator-ca-es/es-ca.params"
        GetWordAlignments_rev_err_file="./aina-translator-ca-es/es-ca.err"
        truecaser_tokenizer="MTUOC_tokenizer_cat"
        tcmodel="./aina-translator-ca-es/tc.ca"   
        config.srxfiles=["segment.srx"]
        config.srxlang="Catalan" 
    
    elif model=="es-ca":
        aina_repo="projecte-aina/aina-translator-es-ca"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-ca-es"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-es"
        config.AinaTranslator_model_path="./aina-translator-es-ca"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_spa"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_cat"
        GetWordAlignments_fwd_params_file="./aina-translator-es-ca/es-ca.params"
        GetWordAlignments_fwd_err_file="./aina-translator-es-ca/es-ca.err"

        GetWordAlignments_rev_params_file="./aina-translator-es-ca/ca-es.params"
        GetWordAlignments_rev_err_file="./aina-translator-es-ca/ca-es.err"
        truecaser_tokenizer="MTUOC_tokenizer_spa"
        tcmodel="./aina-translator-es-ca/tc.es"
        config.srxfiles=["segment.srx"]
        config.srxlang="Spanish"
    
    elif model=="ca-pt":
        aina_repo="projecte-aina/aina-translator-ca-pt"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-ca-pt"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-ca"
        config.AinaTranslator_model_path="./aina-translator-ca-pt"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_cat"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_por"
        GetWordAlignments_fwd_params_file="./aina-translator-ca-pt/ca-pt.params"
        GetWordAlignments_fwd_err_file="./aina-translator-ca-pt/ca-pt.err"

        GetWordAlignments_rev_params_file="./aina-translator-ca-pt/pt-ca.params"
        GetWordAlignments_rev_err_file="./aina-translator-ca-pt/pt-ca.err"
        truecaser_tokenizer="MTUOC_tokenizer_cat"
        tcmodel="./aina-translator-ca-pt/tc.ca"
        config.srxfiles=["segment.srx"]
        config.srxlang="Catalan"
    
    elif model=="pt-ca":
        aina_repo="projecte-aina/aina-translator-pt-ca"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-ca-pt"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-pt"
        config.AinaTranslator_model_path="./aina-translator-pt-ca"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_por"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_cat"
        GetWordAlignments_fwd_params_file="./aina-translator-pt-ca/pt-ca.params"
        GetWordAlignments_fwd_err_file="./aina-translator-pt-ca/pt-ca.err"

        GetWordAlignments_rev_params_file="./aina-translator-pt-ca/ca-pt.params"
        GetWordAlignments_rev_err_file="./aina-translator-pt-ca/ca-pt.err"   
        truecaser_tokenizer="MTUOC_tokenizer_por"
        tcmodel="./aina-translator-pt-ca/tc.pt"
        config.srxfiles=["segment.srx"]
        config.srxlang="Portuguese"
        
    elif model=="ca-it":
        aina_repo="projecte-aina/aina-translator-ca-it"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-ca-it"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-ca"
        config.AinaTranslator_model_path="./aina-translator-ca-it"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_cat"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_ita"
        GetWordAlignments_fwd_params_file="./aina-translator-ca-it/ca-it.params"
        GetWordAlignments_fwd_err_file="./aina-translator-ca-it/ca-it.err"

        GetWordAlignments_rev_params_file="./aina-translator-ca-it/it-ca.params"
        GetWordAlignments_rev_err_file="./aina-translator-ca-it/it-ca.err"
        truecaser_tokenizer="MTUOC_tokenizer_cat"
        tcmodel="./aina-translator-ca-it/tc.ca"
        config.srxfiles=["segment.srx"]
        config.srxlang="Catalan"
    
    elif model=="it-ca":
        aina_repo="projecte-aina/aina-translator-it-ca"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-ca-it"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-it"
        config.AinaTranslator_model_path="./aina-translator-it-ca"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_ita"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_cat"
        GetWordAlignments_fwd_params_file="./aina-translator-it-ca/it-ca.params"
        GetWordAlignments_fwd_err_file="./aina-translator-it-ca/it-ca.err"

        GetWordAlignments_rev_params_file="./aina-translator-it-ca/ca-it.params"
        GetWordAlignments_rev_err_file="./aina-translator-it-ca/ca-it.err"   
        truecaser_tokenizer="MTUOC_tokenizer_ita"
        tcmodel="./aina-translator-it-ca/tc.it"
        config.srxfiles=["segment.srx"]
        config.srxlang="Italian"
    
    elif model=="gl-ca":
        aina_repo="projecte-aina/aina-translator-gl-ca"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-ca-gl"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-gl"
        config.AinaTranslator_model_path="./aina-translator-gl-ca"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_glg"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_cat"
        GetWordAlignments_fwd_params_file="./aina-translator-gl-ca/gl-ca.params"
        GetWordAlignments_fwd_err_file="./aina-translator-gl-ca/gl-ca.err"

        GetWordAlignments_rev_params_file="./aina-translator-gl-ca/ca-gl.params"
        GetWordAlignments_rev_err_file="./aina-translator-gl-ca/ca-gl.err"   
        truecaser_tokenizer="MTUOC_tokenizer_glg"
        tcmodel="./aina-translator-gl-ca/tc.gl"
        config.srxfiles=["segment.srx"]
        config.srxlang="Galician"
        
    elif model=="ca-fr":
        aina_repo="projecte-aina/aina-translator-ca-fr"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-ca-fr"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-ca"
        config.AinaTranslator_model_path="./aina-translator-ca-fr"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_cat"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_fra"
        GetWordAlignments_fwd_params_file="./aina-translator-ca-fr/ca-fr.params"
        GetWordAlignments_fwd_err_file="./aina-translator-ca-fr/ca-fr.err"

        GetWordAlignments_rev_params_file="./aina-translator-ca-fr/fr-ca.params"
        GetWordAlignments_rev_err_file="./aina-translator-ca-fr/fr-ca.err"
        truecaser_tokenizer="MTUOC_tokenizer_cat"
        tcmodel="./aina-translator-ca-fr/tc.ca"
        config.srxfiles=["segment.srx"]
        config.srxlang="Catalan"
    
    elif model=="fr-ca":
        aina_repo="projecte-aina/aina-translator-fr-ca"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-ca-fr"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-fr"
        config.AinaTranslator_model_path="./aina-translator-fr-ca"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_fra"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_cat"
        GetWordAlignments_fwd_params_file="./aina-translator-fr-ca/fr-ca.params"
        GetWordAlignments_fwd_err_file="./aina-translator-fr-ca/fr-ca.err"

        GetWordAlignments_rev_params_file="./aina-translator-fr-ca/ca-fr.params"
        GetWordAlignments_rev_err_file="./aina-translator-fr-ca/ca-fr.err"   
        truecaser_tokenizer="MTUOC_tokenizer_fra"
        tcmodel="./aina-translator-fr-ca/tc.fr"
        config.srxfiles=["segment.srx"]
        config.srxlang="French"
        
    elif model=="eu-ca":
        aina_repo="projecte-aina/aina-translator-eu-ca"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-ca-eu"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-eu"
        config.AinaTranslator_model_path="./aina-translator-eu-ca"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_spa"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_cat"
        GetWordAlignments_fwd_params_file="./aina-translator-eu-ca/eu-ca.params"
        GetWordAlignments_fwd_err_file="./aina-translator-eu-ca/eu-ca.err"

        GetWordAlignments_rev_params_file="./aina-translator-eu-ca/ca-eu.params"
        GetWordAlignments_rev_err_file="./aina-translator-eu-ca/ca-eu.err"   
        truecaser_tokenizer="MTUOC_tokenizer_spa"
        tcmodel="./aina-translator-eu-ca/tc.eu"
        config.srxfiles=["segment.srx"]
        config.srxlang="Spanish"
        
    elif model=="es-oc_aran":
        aina_repo="projecte-aina/aina-translator-es-oc"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-es-oc_aran"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-es"
        config.AinaTranslator_model_path="./aina-translator-es-oc"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_spa"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_cat"
        GetWordAlignments_fwd_params_file="./aina-translator-es-oc/es-oc_aran.params"
        GetWordAlignments_fwd_err_file="./aina-translator-es-oc/es-oc_aran.err"

        GetWordAlignments_rev_params_file="./aina-translator-es-oc/oc_aran-es.params"
        GetWordAlignments_rev_err_file="./aina-translator-es-oc/oc_aran-es.err"   
        truecaser_tokenizer="MTUOC_tokenizer_spa"
        tcmodel="./aina-translator-es-oc/tc.es"
        config.srxfiles=["segment.srx"]
        config.srxlang="Spanish"
        config.MTUOCServer_MTengine="NLLB"
        
    elif model=="es-ast":
        aina_repo="projecte-aina/aina-translator-es-ast"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-es-ast"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-es"
        config.AinaTranslator_model_path="./aina-translator-es-ast"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_spa"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_ast"
        GetWordAlignments_fwd_params_file="./aina-translator-es-ast/es-ast.params"
        GetWordAlignments_fwd_err_file="./aina-translator-es-ast/es-ast.err"

        GetWordAlignments_rev_params_file="./aina-translator-es-ast/ast-es.params"
        GetWordAlignments_rev_err_file="./aina-translator-es-ast/ast-es.err"   
        truecaser_tokenizer="MTUOC_tokenizer_spa"
        tcmodel="./aina-translator-es-ast/tc.es"
        config.srxfiles=["segment.srx"]
        config.srxlang="Spanish"
        config.MTUOCServer_MTengine="NLLB"
        
    elif model=="es-an":
        aina_repo="projecte-aina/aina-translator-es-an"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-es-an"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-es"
        config.AinaTranslator_model_path="./aina-translator-es-an"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_spa"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_arg"
        GetWordAlignments_fwd_params_file="./aina-translator-es-an/es-an.params"
        GetWordAlignments_fwd_err_file="./aina-translator-es-an/es-an.err"

        GetWordAlignments_rev_params_file="./aina-translator-es-an/an-es.params"
        GetWordAlignments_rev_err_file="./aina-translator-es-an/an-es.err"   
        truecaser_tokenizer="MTUOC_tokenizer_spa"
        tcmodel="./aina-translator-es-an/tc.es"
        config.srxfiles=["segment.srx"]
        config.srxlang="Spanish"
        config.MTUOCServer_MTengine="NLLB"
        
    elif model=="zh-ca":
        aina_repo="projecte-aina/aina-translator-zh-ca"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-ca-zh"
        truecaser_repo=None
        config.AinaTranslator_model_path="./aina-translator-zh-ca"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_zho_jieba"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_cat"
        GetWordAlignments_fwd_params_file="./aina-translator-zh-ca/zh-ca.params"
        GetWordAlignments_fwd_err_file="./aina-translator-zh-ca/zh-ca.err"

        GetWordAlignments_rev_params_file="./aina-translator-zh-ca/ca-zh.params"
        GetWordAlignments_rev_err_file="./aina-translator-zh-ca/ca-zh.err"   
        truecaser_tokenizer=None
        tcmodel=None
        config.srxfiles=["segment.srx"]
        config.srxlang="Generic"
        config.MTUOCServer_MTengine="M2M100"
        
    elif model=="ca-zh":
        aina_repo="projecte-aina/aina-translator-ca-zh"
        alignment_repo="aoliverg/MTUOC-Aina-alignment_model-ca-zh"
        truecaser_repo="aoliverg/MTUOC-Aina-truecasing-model-ca"
        config.AinaTranslator_model_path="./aina-translator-ca-zh"
        config.GetWordAlignments_tokenizerSL="MTUOC_tokenizer_cat"
        config.GetWordAlignments_tokenizerTL="MTUOC_tokenizer_zho_jieba"
        GetWordAlignments_fwd_params_file="./aina-translator-ca-zh/ca-zh.params"
        GetWordAlignments_fwd_err_file="./aina-translator-ca-zh/ca-zh.err"

        GetWordAlignments_rev_params_file="./aina-translator-ca-zh/zh-ca.params"
        GetWordAlignments_rev_err_file="./aina-translator-ca-zh/zh-ca.err"   
        truecaser_tokenizer=None
        tcmodel="./aina-translator-ca-zh/tc.ca"
        config.srxfiles=["segment.srx"]
        config.srxlang="Catalan"
        config.MTUOCServer_MTengine="M2M100"
      
        
    config.segmenters=[]
    if config.segment:
        from MTUOC_SRXSegmenter import InputSegmenter
        config.segmenters=[]
        for srxfile in config.srxfiles:
            segmenter=InputSegmenter()
            segmenter.set_srx_file(srxfile,config.srxlang)
            config.segmenters.append(segmenter)
    
    print("Downloading translation model.")
    model_dir = snapshot_download(repo_id=aina_repo, 
                               revision=config.AinaTranslator_revision, 
                               local_dir=config.AinaTranslator_model_path)
                               
    print("Downloading alignment model.")                           
    ali_model_dir = snapshot_download(repo_id=alignment_repo, 
                               revision="main", 
                               local_dir=config.AinaTranslator_model_path) 
    
    
    if not truecaser_repo==None:
        try:
            print("Downloading truecaser model.")
            truecaser_repo_dir = snapshot_download(repo_id=truecaser_repo, 
                                       revision="main", 
                                       local_dir=config.AinaTranslator_model_path) 
        except:
            print("Error  downloading truecaser model from ",truecaser_repo,sys.exec_info())
     
    if config.MTUOCServer_MTengine=="Aina":
        config.AinaTranslator_num_hypotheses=configYAML2["Aina"]["num_hypotheses"]
        config.AinaTranslator=AinaTranslator()
        config.AinaTranslator.set_model(config.AinaTranslator_model_path,config.AinaTranslator_revision)
        config.AinaTranslator.set_beam_size(config.AinaTranslator_beam_size)
        config.AinaTranslator.set_num_hypotheses(config.AinaTranslator_num_hypotheses)
    elif config.MTUOCServer_MTengine=="NLLB":
        from NLLBTranslator import *
        if model=="es-oc_aran":
            config.NLLB_model="./aina-translator-es-oc"
            config.NLLB_beam_size=config.AinaTranslator_beam_size
            config.NLLB_num_hypotheses=config.AinaTranslator_num_hypotheses
            config.NLLB_src_lang="spa_Latn"
            config.NLLB_tgt_lang="oci_Latn"
        elif model=="es-ast":
            config.NLLB_model="./aina-translator-es-ast"
            config.NLLB_beam_size=config.AinaTranslator_beam_size
            config.NLLB_num_hypotheses=config.AinaTranslator_num_hypotheses
            config.NLLB_src_lang="spa_Latn"
            config.NLLB_tgt_lang="ast_Latn"
        elif model=="es-an":
            config.NLLB_model="./aina-translator-es-an"
            config.NLLB_beam_size=config.AinaTranslator_beam_size
            config.NLLB_num_hypotheses=config.AinaTranslator_num_hypotheses
            config.NLLB_src_lang="spa_Latn"
            config.NLLB_tgt_lang="arg_Latn"
        config.NLLB_translator=NLLBTranslator()
        config.NLLB_translator.set_model(config.NLLB_model,config.NLLB_src_lang,config.NLLB_tgt_lang)
        config.NLLB_translator.set_beam_size(config.NLLB_beam_size)
        config.NLLB_translator.set_num_hypotheses(config.NLLB_num_hypotheses)
        
    elif config.MTUOCServer_MTengine=="M2M100":
        from M2M100Translator import *
        if model=="zh-ca":
            config.M2M100_model="./aina-translator-zh-ca"
            config.M2M100_beam_size=config.AinaTranslator_beam_size
            config.M2M100_num_hypotheses=config.AinaTranslator_num_hypotheses
            config.M2M100_translator=M2M100Translator()
            config.M2M100_translator.set_model(config.M2M100_model)
            config.M2M100_translator.set_beam_size(config.M2M100_beam_size)
            config.M2M100_translator.set_num_hypotheses(config.M2M100_num_hypotheses)
        elif model=="ca-zh":
            config.M2M100_model="./aina-translator-ca-zh"
            config.M2M100_beam_size=config.AinaTranslator_beam_size
            config.M2M100_num_hypotheses=config.AinaTranslator_num_hypotheses
            config.M2M100_translator=M2M100Translator()
            config.M2M100_translator.set_model(config.M2M100_model)
            config.M2M100_translator.set_beam_size(config.M2M100_beam_size)
            config.M2M100_translator.set_num_hypotheses(config.M2M100_num_hypotheses)

    printLOG(1,"Translating with Aina models",config.AinaTranslator_model_path)

elif config.MTUOCServer_MTengine=="Llama":
    import torch
    from transformers import pipeline
    from LlamaTranslator import *
    
    stream2 = open("config-Llama.yaml", 'r',encoding="utf-8")
    configYAML2=yaml.load(stream2, Loader=yaml.FullLoader)
    
    config.Llama_model=configYAML2["Llama"]["model"]
    config.Llama_role=configYAML2["Llama"]["role"]
    config.Llama_max_new_tokens=configYAML2["Llama"]["max_new_tokens"]
    config.Llama_instruct_prefix=configYAML2["Llama"]["instruct_prefix"]
    config.Llama_instruct_postfix=configYAML2["Llama"]["instruct_postfix"]
    
    config.Llama_translator=LlamaTranslator(config.Llama_model)

    config.Llama_translator.set_role(config.Llama_role)
    config.Llama_translator.set_max_new_tokens(config.Llama_max_new_tokens)   
    
elif config.MTUOCServer_MTengine=="Apertium":
    import apertium
        
    stream2 = open("config-Apertium.yaml", 'r',encoding="utf-8")
    configYAML2=yaml.load(stream2, Loader=yaml.FullLoader)
    
    config.apertium_sl=configYAML2["Apertium"]["sl"]
    config.apertium_tl=configYAML2["Apertium"]["tl"]
    apertium_mark_unknown=configYAML2["Apertium"]["mark_unknown"]
    config.apertium_translator=apertium.translation.Translator(config.apertium_sl,config.apertium_tl)
    langpair=config.apertium_sl+"->"+config.apertium_tl
    printLOG(1,"Translating with Apertium",langpair)

elif config.MTUOCServer_MTengine=="SalamandraTA":
    config.truecase="upper"
    truecaser="MTUOC"
    
    config.unescape_html=True
    config.fixencoding=True
    config.escapeforMoses=False
    config.remove_tags=True
    config.segment=True
    
    config.splitlongsegments=configYAML["Preprocess"]["splitlongsegments"]
    config.maxlong=configYAML["Preprocess"]["maxlong"]
    config.separators=configYAML["Preprocess"]["separators"].split()


    config.strategy="bysegments"
    config.remove_control_characters=True
    config.remove_non_printable=True
    config.remove_non_latin_extended_chars=False
    config.remove_non_unicode_script_chars=False

    config.restore_case=True
    config.restore_tags=False
    config.numeric_check=False
    config.GetWordAlignments_type="fast_align"
    
    stream2 = open("config-SalamandraTA.yaml", 'r',encoding="utf-8")
    configYAML2=yaml.load(stream2, Loader=yaml.FullLoader)
    
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from SalamandraTATranslator import SalamandraTATranslator
    
    config.SalamandraTATranslator_src_lang=configYAML2["SalamandraTA"]["src_lang"]
    config.SalamandraTATranslator_tgt_lang=configYAML2["SalamandraTA"]["tgt_lang"]
    config.SalamandraTATranslator_model_id=configYAML2["SalamandraTA"]["model_id"]
    config.SalamandraTATranslator_beam_size=configYAML2["SalamandraTA"]["beam_size"]
    config.SalamandraTATranslator_num_hypotheses=configYAML2["SalamandraTA"]["num_hypotheses"]
    
    config.SalamandraTATranslator=SalamandraTATranslator()
    config.SalamandraTATranslator.set_src_lang(config.SalamandraTATranslator_src_lang)
    config.SalamandraTATranslator.set_tgt_lang(config.SalamandraTATranslator_tgt_lang)
    config.SalamandraTATranslator.set_model_id(config.SalamandraTATranslator_model_id)
    config.SalamandraTATranslator.set_beam_size(config.SalamandraTATranslator_beam_size)
    config.SalamandraTATranslator.set_num_hypotheses(config.SalamandraTATranslator_num_hypotheses)

    config.truecase="never"
    config.GetWordAlignments_type=None    
    
    
#TRUECASER

createtruecaser=True

if config.truecase=="never":
    createtruecaser=False
if tcmodel=="None":
    createtruecaser=False
    config.truecase="never"
    
if createtruecaser and truecaser.startswith("MTUOC"):
    from MTUOC_truecaser import Truecaser
    config.truecaser=Truecaser(tokenizer=truecaser_tokenizer,tc_model=tcmodel)
    
if config.GetWordAlignments_type=="None":
    config.GetWordAlignments_type=None
elif config.GetWordAlignments_type=="fast_align":
    from GetWordAlignments_fast_align import WordAligner
    config.wordaligner=WordAligner(GetWordAlignments_fwd_params_file,GetWordAlignments_fwd_err_file,GetWordAlignments_rev_params_file, GetWordAlignments_rev_err_file, GetWordAlignments_tokenizerSLcode, GetWordAlignments_tokenizerTLcode)


if not config.GetWordAlignments_type==None and config.GetWordAlignments_tokenizerSL=="Moses":
    from sacremoses import MosesTokenizer, MosesDetokenizer
    GetWordAlignments_tokenizerSL=MosesTokenizer(lang=GetWordAlignments_tokenizerSLcode)
    config.wordaligner.set_src_tokenizer(GetWordAlignments_tokenizerSL)

    
if not config.GetWordAlignments_type==None and config.GetWordAlignments_tokenizerTL=="Moses":
    from sacremoses import MosesTokenizer, MosesDetokenizer
    GetWordAlignments_tokenizerTL=MosesTokenizer(lang=GetWordAlignments_tokenizerTLcode)
    config.wordaligner.set_tgt_tokenizer(GetWordAlignments_tokenizerTL)


if not config.GetWordAlignments_type==None and config.GetWordAlignments_tokenizerSL.startswith("MTUOC"):
    import importlib.util
    if not config.GetWordAlignments_tokenizerSL.endswith(".py"): config.GetWordAlignments_tokenizeSL=config.GetWordAlignments_tokenizerSL+".py"
    spec = importlib.util.spec_from_file_location('', config.GetWordAlignments_tokenizeSL)
    tokenizermod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tokenizermod)
    config.GetWordAlignments_tokenizerSL=tokenizermod.Tokenizer()
    config.wordaligner.set_src_tokenizer(config.GetWordAlignments_tokenizerSL)
    
if not config.GetWordAlignments_type==None and config.GetWordAlignments_tokenizerTL.startswith("MTUOC"):
    import importlib.util
    if not config.GetWordAlignments_tokenizerTL.endswith(".py"): config.GetWordAlignments_tokenizerTL=config.GetWordAlignments_tokenizerTL+".py"
    spec = importlib.util.spec_from_file_location('', config.GetWordAlignments_tokenizerTL)
    tokenizermod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tokenizermod)
    config.GetWordAlignments_tokenizerTL=tokenizermod.Tokenizer()
    config.wordaligner.set_tgt_tokenizer(config.GetWordAlignments_tokenizerTL)
    
    
if config.MTUOCServer_type=="MTUOC":
    from MTUOC_typeMTUOC import start_MTUOC_server
    start_MTUOC_server()
elif config.MTUOCServer_type=="Moses":
    from MTUOC_typeMoses import start_Moses_server
    start_Moses_server()
elif config.MTUOCServer_type=="OpenNMT":
    from MTUOC_typeOpenNMT import start_OpenNMT_server
    config.MTUOCServer_ONMT_url_root=configYAML["MTUOCServer"]["ONMT_url_root"]
    start_OpenNMT_server()
elif config.MTUOCServer_type=="NMTWizard":
    from MTUOC_typeNMTWizard import start_NMTWizard_server
    start_NMTWizard_server()
elif config.MTUOCServer_type=="ModernMT":
    from MTUOC_typeModernMT import start_ModernMT_server
    start_ModernMT_server()
