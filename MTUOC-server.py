#    MTUOC-server v 2606
#    Description: an MTUOC server using Sentence Piece as preprocessing step
#    Copyright (C) 2026  Antoni Oliver
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
import codecs
import os
import platform
from pathlib import Path
import requests
import stat
import shutil
import importlib.util

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from MTUOC_misc import get_IP_info
from MTUOC_misc import printLOG

# --- FUNCIÓ AUXILIAR PER CARREGAR TOKENITZADORS DINÀMICAMENT ---
# 2. Auxiliary function to dynamically load any MTUOC-compliant tokenizer script
def load_tokenizer(tokenizer_setting, lang_code):
    if not tokenizer_setting or tokenizer_setting in ["None", "False", False]:
        return None
    
    tokenizer_str = str(tokenizer_setting).strip()
    
    # Check if the file actually exists on the disk
    if not os.path.exists(tokenizer_str):
        raise FileNotFoundError(
            f"\n[MTUOC ERROR] Tokenizer file not found at the specified path: '{tokenizer_str}'\n"
            f"Please check your YAML configuration files and verify the file path."
        )
    
    # Extract directory and add it to sys.path to resolve internal module imports
    tokenizer_dir = os.path.dirname(os.path.abspath(tokenizer_str))
    if tokenizer_dir not in sys.path:
        sys.path.append(tokenizer_dir)
    
    module_name = os.path.basename(tokenizer_str).replace(".py", "")
    
    # Load the Python file dynamically
    spec = importlib.util.spec_from_file_location(module_name, tokenizer_str)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Instantiate based on the tokenizer type requirements
    if "Mosestokenizer" in module_name:
        return module.Tokenizer(lang=lang_code if lang_code else "en")
    elif "SpacyTokenizer" in module_name:
        # The Spacy wrapper uses SpacyMTUOCTokenizer class name instead of Tokenizer
        return module.SpacyMTUOCTokenizer(model_name=lang_code if lang_code else "en")
    else:
        # Standard MTUOC custom tokenizers
        return module.Tokenizer()


if len(sys.argv)>1:
    configfile=sys.argv[1]
else:
    configfile="config-server.yaml"

# 1. Comprovar si el fitxer existeix
if not os.path.exists(configfile):
    print(
        f"ERROR: configuration file '{configfile}' does not exist.",
        file=sys.stderr,
    )
    sys.exit(1)  # Surt del programa amb un codi d'error

# 2. Si existeix, intentem llegir-lo de forma segura
try:
    with open(configfile, "r", encoding="utf-8") as stream:
        configYAML = yaml.full_load(stream)
except yaml.YAMLError as exc:
    print(
        f"Format error in YAML file: {exc}", file=sys.stderr
    )
    sys.exit(1)
except Exception as e:
    print(
        f"Unexpected error opening file: {e}", file=sys.stderr
    )
    sys.exit(1)


MTUOCServer_MTengine=configYAML["MTengine"]
system_name=configYAML["system_name"]
model_config=configYAML["model_config"]

dopreprocess=configYAML["dopreprocess"]
preprocess_yaml = configYAML.get("preprocess_config")
dotokenization=configYAML["dotokenization"]
tokenizationyaml=configYAML["tokenization_config"]
dopostprocess=configYAML["dopostprocess"]

configPreprocessYAML = {}
preprocessor=None
if dopreprocess and preprocess_yaml and os.path.exists(preprocess_yaml):
    try:
        with open(preprocess_yaml, "r", encoding="utf-8") as p_stream:
            configPreprocessYAML = yaml.full_load(p_stream)
    except Exception as e:
        print(f"WARNING: Error al llegir el fitxer de preprocessament '{preprocess_yaml}': {e}", file=sys.stderr)

    # Instanciem el preprocessor passant-li el diccionari del fitxer independent
    # El constructor que vam fer ja sap buscar la clau "Preprocess" a dins.
    from MTUOC_Preprocessor import Preprocessor
    preprocessor = Preprocessor(configPreprocessYAML)
    truecaser=None
    # Si el canvi de paraules està actiu i apunta a un fitxer, es carregaria aquí
    if preprocessor.config.get("changes_input"):
        try:
            entrada=codecs.open(preprocessor.config["changes_input_file"],"r",encoding="utf-8")
            llista_canvis=[]
            for linia in entrada:
                linia=linia.strip()
                camps=linia.split("\t")
                llista_canvis.append(camps)
            preprocessor.set_changes_input(llista_canvis)
        except:
            printLOG(1,"Error reading changes input file:",sys.exc_info())
    if preprocessor.config.get("truecase"):
        if preprocessor.config.get("truecaser_type")=="MTUOC":
            from MTUOC_truecaser import Truecaser
            truecaser=Truecaser(tokenizer=preprocessor.config.get("truecaser_tokenizer"),tc_model=preprocessor.config.get("truecase_model"))
            preprocessor.config["truecaser"]=truecaser
        if preprocessor.config.get("truecaser_type")=="Moses":
            from MTUOC_Mosestruecaser import Truecaser
            preprocessor.config["truecaser"]=truecaser
            
if dotokenization:
    stream = open(tokenizationyaml, 'r',encoding="utf-8")
    configtokenizationYAML=yaml.full_load(stream)
    sentencepiece=configtokenizationYAML["sentencepiece"]
    if sentencepiece:
        from SentencePieceTokenizer import SentencePieceTokenizer
        sentencepiecetokenizer=SentencePieceTokenizer()
        spmodel=configtokenizationYAML["spmodel"]
        sentencepiecetokenizer.set_spmodel(spmodel)
        spvocab=configtokenizationYAML["spvocab"]
        sentencepiecetokenizer.set_spvocab(spvocab)
        
dopostprocess = configYAML.get("dopostprocess", False)
if dopreprocess and preprocess_yaml and os.path.exists(preprocess_yaml):
    postprocess_yaml = configYAML.get("postprocess_config")

    try:
        with open(postprocess_yaml, "r", encoding="utf-8") as stream:
            postprocessYAML = yaml.full_load(stream)
    except yaml.YAMLError as exc:
        print(
            f"Format error in YAML file: {exc}", file=sys.stderr
        )
        sys.exit(1)
    if dopostprocess:
        postprocessPPYAML=postprocessYAML["Postprocess"]
        postprocessRestoreYAML=postprocessYAML["Restore_tags"]
    else:
        postprocessRestoreYAML=None
wordaligner = None 
postprocessor = None
restore_tags = None
restorationtype = None
if dopostprocess and postprocess_yaml and os.path.exists(postprocess_yaml):
    restore_tags=postprocessRestoreYAML["restore_tags"]
    restorationtype=postprocessRestoreYAML["type"]
    from MTUOC_Postprocessor import Postprocessor
    postprocessor = Postprocessor(postprocessPPYAML)
    if postprocessor.config.get("changes_output"):
        try:
            entrada=codecs.open(postprocessor.config["changes_output_file"],"r",encoding="utf-8")
            llista_canvis=[]
            for linia in entrada:
                linia=linia.strip()
                camps=linia.split("\t")
                llista_canvis.append(camps)
            postprocessor.set_changes_output(llista_canvis)
        except:
            printLOG(1,"Error reading changes output file:",sys.exc_info())
            
    if postprocessor.config.get("changes_translation"):
        try:
            entrada=codecs.open(postprocessor.config["changes_translation_file"],"r",encoding="utf-8")
            llista_canvis=[]
            for linia in entrada:
                linia=linia.strip()
                camps=linia.split("\t")
                llista_canvis.append(camps)
            postprocessor.set_changes_translation(llista_canvis)
        except:
            printLOG(1,"Error reading changes translation file:",sys.exc_info())
    
    wordaligner = None
    if restore_tags:
        # Segons el teu format llegit des del YAML: postprocessRestoreYAML
        restorationtype = postprocessRestoreYAML.get("type", "fast_align")
        
        if restorationtype == "fast_align":
            fwd_params = postprocessRestoreYAML["fwd_params_file"]
            fwd_err = postprocessRestoreYAML["fwd_err_file"]
            rev_params = postprocessRestoreYAML["rev_params_file"]
            rev_err = postprocessRestoreYAML["rev_err_file"]

            from GetWordAlignments_fast_align import WordAligner

            # Llegim les noves opcions dinàmiques del YAML
            tokenizer_sl_setting = postprocessRestoreYAML.get("tokenizerSL")
            tokenizer_tl_setting = postprocessRestoreYAML.get("tokenizerTL")
            sl_code = postprocessRestoreYAML.get("tokenizerSLcode", "es")
            tl_code = postprocessRestoreYAML.get("tokenizerTLcode", "ca")

            # Cridem la funció de càrrega dinàmica en comptes d'escriure tok_src fix
            tok_src = load_tokenizer(tokenizer_sl_setting, sl_code)
            tok_tgt = load_tokenizer(tokenizer_tl_setting, tl_code)

            # Creem el wordaligner passant els codis dinàmics
            wordaligner = WordAligner(fwd_params, fwd_err, rev_params, rev_err, sl_code, tl_code)
            wordaligner.set_src_tokenizer(tok_src)
            wordaligner.set_tgt_tokenizer(tok_tgt)


#Server type
MTUOCServer_type=configYAML["MTUOCServer"]["type"]
MTUOCServer_port=configYAML["MTUOCServer"]["port"]
verbosity_level = int(configYAML["MTUOCServer"]["verbosity_level"])
log_file = configYAML["MTUOCServer"]["log_file"]

if log_file == "None":
    log_file_active = False
    sortidalog = None
else:
    sortidalog = codecs.open(log_file, "a", encoding="utf-8")
    log_file_active = True

# --- ENREGISTREM ELS VALORS DE LOG A MTUOC_misc (INJECCIÓ NETA) ---
from MTUOC_misc import setup_logging
setup_logging(verbosity_level, log_file_active, sortidalog)
    

###OPUSMT
if MTUOCServer_MTengine == "OpusMT":
    from TransformersTranslator import TransformersTranslator
    
    # Instanciem directament a la nostra variable de control
    translator_engine = TransformersTranslator(config_path=model_config)
    #TransformersTranslator = translator_engine
    Transformers_model_path = translator_engine.model_path
    
    printLOG(1,"Translating with OpusMT models", Transformers_model_path)
    
elif MTUOCServer_MTengine == "NLLB":
    from NLLBTranslator import NLLBTranslator
    
    # Instanciem el motor de NLLB passant-li el fitxer de configuració
    translator_engine = NLLBTranslator(config_path=model_config)
    
    # Extraiem la ruta del model (o nom) directament de l'atribut de la classe
    NLLB_model_path = translator_engine.model_name
    
    printLOG(1,"Translating with NLLB models", NLLB_model_path)
    
elif MTUOCServer_MTengine == "HuggingFace":
    from HFTranslator import HFTranslator
    
    # Instanciem el motor de HuggingFace generatiu passant el config actual
    translator_engine = HFTranslator(config_path=model_config)
    HF_model_path = translator_engine.model_path
    
    printLOG(1,"Translating with HuggingFace:", HF_model_path)
    
elif MTUOCServer_MTengine == "ctranslate2":
    from ctranslate2Translator import ctranslate2Translator
    
    # Instanciem el motor de NLLB passant-li el fitxer de configuració
    translator_engine = ctranslate2Translator(config_path=model_config)
    
    # Extraiem la ruta del model (o nom) directament de l'atribut de la classe
    ctranslate2Translator = translator_engine.model_name
    
    printLOG(1,"Translating with ctranslate2 model", ctranslate2Translator)

elif MTUOCServer_MTengine == "M2M100":
    from M2M100Translator import M2M100Translator
    
    # Instanciem el motor M2M100 generatiu passant el config actual
    translator_engine = M2M100Translator(config_path=model_config)
    M2M100_model_path = translator_engine.model_path
    
    printLOG(1,"Translating with M2M100:", M2M100_model_path)

elif MTUOCServer_MTengine == "Apertium":
    from ApertiumTranslator import ApertiumTranslator
    
    # Instanciem el motor de NLLB passant-li el fitxer de configuració
    translator_engine = ApertiumTranslator(config_path=model_config)
    
    printLOG(1,"Translating with Apertium")
    
elif MTUOCServer_MTengine == "Ollama":
    from OllamaTranslator import OllamaTranslator
    
    # Instanciem el motor d'Ollama passant el config actual
    translator_engine = OllamaTranslator(config_path=model_config)
    Ollama_model_path = translator_engine.model_path
    
    printLOG(1,"Translating with Ollama models:", Ollama_model_path)
    
elif MTUOCServer_MTengine == "GoogleT":
    from GoogleTranslateTranslator import GoogleTranslateTranslator
    import yaml
    import os

    # 1. Carreguem el YAML des del servidor per configurar la variable d'entorn i paràmetres
    with open(model_config, 'r', encoding="utf-8") as stream:
        config_yaml = yaml.load(stream, Loader=yaml.FullLoader)
    google_cfg = config_yaml.get("GoogleTranslate", config_yaml)

    # 2. Configurem les credencials de Google de manera dinàmica
    json_path = google_cfg.get("jsonfile")
    if json_path and os.path.exists(json_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_path
    else:
        print(f"WARNING: No s'ha trobat el fitxer de credencials JSON a: {json_path}")

    # 3. Instanciem el motor
    translator_engine = GoogleTranslateTranslator()
    
    # 4. Passem la configuració utilitzant els mètodes "set_" de la teva classe
    translator_engine.set_sllang(google_cfg.get("sllang", "en"))
    translator_engine.set_tllang(google_cfg.get("tllang", "es"))
    
    glossary_val = google_cfg.get("glossary")
    translator_engine.set_glossary(None if glossary_val == "None" else glossary_val)
    
    translator_engine.set_project_id(google_cfg.get("project_id"))
    translator_engine.set_location(google_cfg.get("location", "global"))
    translator_engine.set_jsonfile(json_path)
    
    # 5. Estandarditzem la propietat model_path per al log del servidor
    translator_engine.model_path = f"GoogleAPI ({google_cfg.get('project_id')})"
    Google_model_path = translator_engine.model_path

    printLOG(1,"Translating with Google Translate API via project:", Google_model_path)

elif MTUOCServer_MTengine == "DeepL":
    from DeepLTranslator import DeepLTranslator
    import yaml

    # 1. Carreguem el YAML des del servidor
    with open(model_config, 'r', encoding="utf-8") as stream:
        config_yaml = yaml.load(stream, Loader=yaml.FullLoader)
    deepl_cfg = config_yaml.get("DeepL", config_yaml)

    # 2. Instanciem el motor
    translator_engine = DeepLTranslator()
    
    # 3. Configurem els paràmetres passant el config de manera dinàmica
    translator_engine.set_API_key(deepl_cfg.get("API_key"))
    translator_engine.set_sllang(deepl_cfg.get("sllang", "en"))
    translator_engine.set_tllang(deepl_cfg.get("tllang", "es"))
    translator_engine.set_formality(deepl_cfg.get("formality", "default"))
    translator_engine.set_split_sentences(str(deepl_cfg.get("split_sentences", "off")))
    
    glossary_val = deepl_cfg.get("glossary")
    translator_engine.set_glossary(None if glossary_val == "None" else glossary_val)
    
    # 4. Inicialitzem l'objecte connector de l'API oficial de DeepL
    translator_engine.createTranslator()
    
    # 5. Estandarditzem la propietat model_path per al log del servidor
    translator_engine.model_path = f"DeepL_API"
    DeepL_model_path = translator_engine.model_path

    printLOG(1,"Translating with DeepL API:", DeepL_model_path)

elif MTUOCServer_MTengine == "Eole":
    from EoleTranslator import EoleTranslator
    
    # Instanciem el motor resident d'Eole passant el teu fitxer config.yaml
    translator_engine = EoleTranslator(config_path=model_config)
    Eole_model_path = translator_engine.model_path
    
    printLOG(1,"Translating with Eole:", Eole_model_path)
    
elif MTUOCServer_MTengine == "Marian":
    from MarianTranslator import MarianTranslator
    # Instanciem directament a la nostra variable de control
    translator_engine = MarianTranslator(config_path=model_config)
    marian_model_path = translator_engine.model_path
    printLOG(1,"Translating with Marian models", marian_model_path) 

else:
    
    print(f"ERROR: El motor '{MTUOCServer_MTengine}' no està reconegut al servidor.")
    sys.exit(1)
    
translationMemory=None

try:
    useTranslationMemory=configYAML["TranslationMemory"]["use"]
except:
    useTranslationMemory=False

if useTranslationMemory:
    from MTUOC_TranslationMemory import MTUOC_TranslationMemory
    memo=configYAML["TranslationMemory"]["memo"] 
    minsim=float(configYAML["TranslationMemory"]["minsim"])
    translationMemory=MTUOC_TranslationMemory(memo)
    printLOG(1,"Using translation memory:",memo)
else:
    minsim=100



# Acabem d'afegir el postprocessor a la llista d'injecció de context del servidor
server_context = {
    "translationMemory": translationMemory,
    "minsim": minsim,
    "translator_engine": translator_engine,
    "preprocessor": preprocessor,
    "wordaligner": wordaligner,
    "postprocessor": postprocessor,
    "dopreprocess": dopreprocess,
    "dopostprocess": dopostprocess,
    "restore_tags": restore_tags,
    "sentencepiece_tokenizer": sentencepiecetokenizer if (dotokenization and sentencepiece) else None,
    "system_name": system_name,
    "port": int(MTUOCServer_port)
}

# Llancem el servidor injectant el context sencer
if MTUOCServer_type == "MTUOC":
    from MTUOC_typeMTUOC import start_MTUOC_server
    start_MTUOC_server(server_context)
    
elif MTUOCServer_type=="Moses":
    from MTUOC_typeMoses import start_Moses_server
    start_Moses_server(server_context)
elif MTUOCServer_type=="OpenNMT":
    from MTUOC_typeOpenNMT import start_OpenNMT_server
    server_context["ONMT_url_root"]="/translator"
    start_OpenNMT_server(server_context)
elif MTUOCServer_type=="NMTWizard":
    from MTUOC_typeNMTWizard import start_NMTWizard_server
    start_NMTWizard_server(server_context)
elif MTUOCServer_type=="ModernMT":
    from MTUOC_typeModernMT import start_ModernMT_server
    start_ModernMT_server(server_context)
