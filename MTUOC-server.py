#    MTUOC-server v 2410
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

config.MTUOCServer_type=configYAML["MTUOCServer"]["type"]
config.MTUOCServer_port=configYAML["MTUOCServer"]["port"]

config.SLcode=configYAML["MTEngine"]["SLcode"]
config.TLcode_port=configYAML["MTEngine"]["TLcode"]

config.MTUOCServer_MTengine=configYAML["MTEngine"]["MTengine"]
if config.MTUOCServer_MTengine=="OpusMT": config.MTUOCServer_MTengine="Transformers"

config.multilingual=configYAML["MTEngine"]["multilingual"]

config.verbosity_level=int(configYAML["MTUOCServer"]["verbosity_level"])
config.log_file=configYAML["MTUOCServer"]["log_file"]


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
    
if not config.truecase=="never" and truecaser.startswith("MTUOC"):
    from MTUOC_truecaser import Truecaser
    config.truecaser=Truecaser(tokenizer=truecaser_tokenizer,tc_model=tcmodel)
    
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


config.strategy=configYAML["Preprocess"]["strategy"]

'''
if config.strategy=="bychunks":
    from MTUOC_TagsSegmenter import TagsSegmenter
    segmenter=TagsSegmenter()
    config.segmenters.append(segmenter)
'''



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

###SBERT SCORER


config.calculate_sbert=configYAML["Scoring"]["calculate_sbert"]
config.sort_by_sbert=configYAML["Scoring"]["sort_by_sbert"]
sbert_model=configYAML["Scoring"]["sbert_model"]

if config.calculate_sbert:
    from sbertScorer import sbertScorer
    config.sbert_scorer=sbertScorer()
    config.sbert_scorer.set_model(sbert_model)

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
    if not config.GetWordAlignments_tokenizerSL.endswith(".py"): config.GetWordAlignments_tokenizerSL=config.GetWordAlignments_tokenizerSL+".py"
    spec = importlib.util.spec_from_file_location('', config.GetWordAlignments_tokenizerSL)
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


'''
if config.GetWordAlignments_tokenizer=="MTUOC_Mosestokenizer":
    from MTUOC_Mosestokenizer import Tokenizer
    config.GetWordAlignments_tokenizerSL = Tokenizer(lang=config.GetWordAlignments_tokenizerSLcode)
    config.GetWordAlignments_tokenizerTL = Tokenizer(lang=config.GetWordAlignments_tokenizerTLcode)
'''


    
if config.log_file=="None":
    config.log_file=False
else:
    config.sortidalog=codecs.open(config.log_file,"a",encoding="utf-8")
    config.log_file=True
    
if config.MTUOCServer_MTengine=="Marian":
    from MarianTranslator import MarianTranslator
    config.startMarianServer=configYAML["Marian"]["startMarianServer"]
    config.startMarianCommand=configYAML["Marian"]["startMarianCommand"]
    config.MarianIP=configYAML["Marian"]["IP"]
    config.MarianPort=configYAML["Marian"]["port"]
    config.MarianTranslator=MarianTranslator()
    config.Marian_subword_type=configYAML["Marian"]["subword_type"]
    config.Marian_subword_model=configYAML["Marian"]["subword_model"]
    config.MarianTranslator.set_subword_type(config.Marian_subword_type)
    config.MarianTranslator.set_subword_model(config.Marian_subword_model)
    
    if config.startMarianServer:
        MarianTranslator.start_marian_server()
        
    config.MarianTranslator.connect_to_Marian()


if config.MTUOCServer_MTengine=="Aina":
    import ctranslate2
    import pyonmttok
    #from huggingface_hub import snapshot_download
    from AinaTranslator import AinaTranslator
    config.AinaTranslator_model_path=configYAML["Aina"]["model_path"]
    config.AinaTranslator_revision=configYAML["Aina"]["revision"]
    config.AinaTranslator_beam_size=configYAML["Aina"]["beam_size"]
    config.AinaTranslator_num_hypotheses=configYAML["Aina"]["num_hypotheses"]
    config.AinaTranslator=AinaTranslator()
    config.AinaTranslator.set_model(config.AinaTranslator_model_path,config.AinaTranslator_revision)
    config.AinaTranslator.set_beam_size(config.AinaTranslator_beam_size)
    config.AinaTranslator.set_num_hypotheses(config.AinaTranslator_num_hypotheses)
    printLOG(1,"Translating with Aina models",config.AinaTranslator_model_path)
    
if config.MTUOCServer_MTengine=="Transformers":
    from transformers import MarianMTModel, MarianTokenizer
    import torch
    from TransformersTranslator import TransformersTranslator
    config.TransformersTranslator=TransformersTranslator()
    config.Transformers_model_path=configYAML["Transformers"]["model_path"]
    config.TransformersTranslator.set_model(config.Transformers_model_path)
    config.Transformers_beam_size=configYAML["Transformers"]["beam_size"]
    config.Transformers_num_hypotheses=configYAML["Transformers"]["num_hypotheses"]
    config.TransformersTranslator=TransformersTranslator()
    config.TransformersTranslator.set_model(config.Transformers_model_path)
    config.TransformersTranslator.set_beam_size(config.Transformers_beam_size)
    config.TransformersTranslator.set_num_hypotheses(config.Transformers_num_hypotheses)
    printLOG(1,"Translating with Transformers models",config.Transformers_model_path)
    
elif config.MTUOCServer_MTengine=="NLLB":
    from NLLBTranslator import *
    config.NLLB_model=configYAML["NLLB"]["model"]
    config.NLLB_beam_size=configYAML["NLLB"]["beam_size"]
    config.NLLB_num_hypotheses=configYAML["NLLB"]["num_hypotheses"]
    config.NLLB_src_lang=configYAML["NLLB"]["src_lang"]
    config.NLLB_tgt_lang=configYAML["NLLB"]["tgt_lang"]
    config.NLLB_translator=NLLBTranslator()
    config.NLLB_translator.set_model(config.NLLB_model,config.NLLB_src_lang,config.NLLB_tgt_lang)
    config.NLLB_translator.set_beam_size(config.NLLB_beam_size)
    config.NLLB_translator.set_num_hypotheses(config.NLLB_num_hypotheses)
    printLOG(1,"Translating with NLLB models",config.NLLB_model)
    
elif config.MTUOCServer_MTengine=="Softcatalà" or config.MTUOCServer_MTengine=="Softcatala":
    from SoftcatalaTranslator import *
    config.softcatala_model_dir=configYAML["Softcatala"]["model_dir"]
    config.softcatala_translator=SoftcatalaTranslator()
    config.softcatala_translator.set_model_dir(config.softcatala_model_dir)
    config.softcatala_beam_size=configYAML["Softcatala"]["beam_size"]
    config.softcatala_num_hypotheses=configYAML["Softcatala"]["num_hypotheses"]
    printLOG(1,"Translating with Softcatalà models",config.softcatala_model_dir)
    
  
elif config.MTUOCServer_MTengine=="ctranslate2":
    from ctranslate2Translator import *
    config.ctranslate2_translation_model=configYAML["ctranslate2"]["translation_model"]
    config.ctranslate2_SL_spmodel=configYAML["ctranslate2"]["SL_spmodel"]
    config.ctranslate2_TL_spmodel=configYAML["ctranslate2"]["TL_spmodel"]
    config.ctranslate2_src_lang=configYAML["ctranslate2"]["src_lang"]
    if config.ctranslate2_src_lang=="None":
        config.ctranslate2_src_lang=None
    config.ctranslate2_tgt_lang=configYAML["ctranslate2"]["tgt_lang"]
    if config.ctranslate2_tgt_lang=="None":
        config.ctranslate2_tgt_lang=None
    config.ctranslate2_beam_size=configYAML["ctranslate2"]["beam_size"]
    config.ctranslate2_num_hypotheses=configYAML["ctranslate2"]["num_hypotheses"]
    config.ctranslate2_device=configYAML["ctranslate2"]["device"]
    config.ctranslate2_translator=ctranslate2Translator()
    config.ctranslate2_translator.set_translation_model(config.ctranslate2_translation_model)
    #config.ctranslate2_translator.set_tokenizer(config.ctranslate2_spmodel)
    config.ctranslate2_translator.set_SL_sp_model(config.ctranslate2_SL_spmodel)
    config.ctranslate2_translator.set_TL_sp_model(config.ctranslate2_TL_spmodel)
    config.ctranslate2_translator.set_beam_size(config.ctranslate2_beam_size)
    config.ctranslate2_translator.set_num_hypotheses(config.ctranslate2_num_hypotheses)
    config.ctranslate2_translator.set_device(config.ctranslate2_device)
    config.ctranslate2_translator.set_src_lang(config.ctranslate2_src_lang)
    config.ctranslate2_translator.set_tgt_lang(config.ctranslate2_tgt_lang)
    
    
    printLOG(1,"Translating with ctranslate2 models",config.softcatala_model_dir)  


if config.MTUOCServer_MTengine=="Apertium":
    import apertium
    from ApertiumTranslator import ApertiumTranslator
    config.apertium_sl=configYAML["Apertium"]["sl"]
    config.apertium_tl=configYAML["Apertium"]["tl"]
    config.apertium_translator=ApertiumTranslator(config.apertium_sl,config.apertium_tl)
    printLOG(1,"Translating with Apertium",config.softcatala_model_dir)

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
