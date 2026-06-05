import sys
import html
import regex as re  # Mantenim l'àlies per compatibilitat i millor suport Unicode
from collections import Counter

class Postprocessor:
    
    def __init__(self, config_dict: dict = None):
        """
        Inicialitza el Postprocessor aplegant la secció simplificada del YAML.
        """
        self.taglist = [f"<tag{i}>" for i in range(51)] + [f"</tag{i}>" for i in range(51)]
        self.changes_output = []
        self.changes_translation = []
        
        # Diccionari base estilitzat (només el que ha quedat al YAML)
        self.config = {
            "change_output_files": None,
            "restore_tags": True,
            "type": "fast_align",
            "tokenizerSL": None,
            "tokenizerTL": None,
            "tokenizerSLcode": "en",
            "tokenizerTLcode": "es",
            "fwd_params_file": None,
            "fwd_err_file": None,
            "rev_params_file": None,
            "rev_err_file": None
        }
        
        # Extracció flexible i neta per a les dues seccions restants
        if config_dict:
            if "Postprocess" in config_dict and isinstance(config_dict["Postprocess"], dict):
                self.config.update(config_dict["Postprocess"])
            if "Restore_tags" in config_dict and isinstance(config_dict["Restore_tags"], dict):
                self.config.update(config_dict["Restore_tags"])
            
            # Aplanament de seguretat per si de cas
            self.config.update({k: v for k, v in config_dict.items() if k not in ["Postprocess", "Restore_tags"]})

    def set_changes_translation(self, changes):
        self.changes_translation = changes
        
    def set_changes_output(self, changes):
        self.changes_output = changes

    def is_active(self, key: str) -> bool:
        """Valida si una opció del YAML està activa."""
        val = self.config.get(key, False)
        if isinstance(val, str):
            return val.strip().lower() in ['true', '1', 'yes', 'on']
        return bool(val)

    # -----------------------------------------------------------------
    # MÈTODE GLOBAL INTEGRAT (SENSE LIARES, RESPECTANT EL TEU CORRENT NET)
    # -----------------------------------------------------------------
    def postprocess(self, translation_data: dict, src_original: str, server_context: dict = None) -> dict:
        if not translation_data or "tgt" not in translation_data:
            return translation_data

        try:
            # 1. Substitucions de traducció inicials si n'hi ha
            if self.changes_translation:
                translation_data = self.change_translation(translation_data)

            restore_active = self.config.get("restore_tags", True)
            alignment_type = self.config.get("type", "fast_align")

            if isinstance(alignment_type, str):
                alignment_type = alignment_type.strip().lower()

            # 2. Reinserció de tags (Equival a l'antic insert_tags)
            if restore_active:
                TARGETNOTAGS = translation_data["tgt"]

                # Generem la frase modificada emmascarada i les equivalències
                segmentTAGSMOD, TAGSEQUIL = self.replace_tags(src_original)
                segmentNOTIF, STARTINGTAG, CLOSINGTAG = self.remove_start_end_tag(segmentTAGSMOD)
                
                # Generem un text d'origen completament NET de tags per a fast_align
                src_clean = src_original
                for t in TAGSEQUIL:
                    src_clean = src_clean.replace(TAGSEQUIL[t], "")
                src_clean = " ".join(src_clean.split())

                # Inicialitzem variables de control per defecte
                SELECTEDALIGNMENT = ""
                SOURCENOTAGSTOK = ""
                SOURCETAGSTOK = ""
                TARGETNOTAGSTOK = ""

                # -----------------------------------------------------------------
                # BLOC D'ALINEAMENT AMB EL PROPORCIONADOR DE CONTEXT
                # -----------------------------------------------------------------
                if alignment_type == "fast_align" and server_context and server_context.get("word_aligner"):
                    aligner = server_context["word_aligner"]
                    
                    # A) Demanem l'alineament enviant les dues cadenes NETES
                    alignment, sourceL, targetL = aligner.align_sentence_pair(src_clean, TARGETNOTAGS)
                    SELECTEDALIGNMENT = alignment
                    
                    # B) EXTRACCIÓ TRADICIONAL EXACTA: Re-tokenitzem emprant els connectors injectats!
                    if aligner.src_tokenizer is not None:
                        SOURCETAGSTOK = aligner.src_tokenizer.tokenize(segmentNOTIF)
                    else:
                        SOURCETAGSTOK = segmentNOTIF

                    if aligner.tgt_tokenizer is not None:
                        TARGETNOTAGSTOK = aligner.tgt_tokenizer.tokenize(TARGETNOTAGS)
                    else:
                        TARGETNOTAGSTOK = TARGETNOTAGS

                    # SOURCENOTAGSTOK hereta la cadena de text pur provinent del WordAligner
                    if isinstance(sourceL, list):
                        SOURCENOTAGSTOK = " ".join(sourceL)
                    else:
                        SOURCENOTAGSTOK = sourceL
                    
                else:
                    # Fallback clàssic si no hi ha alineador actiu
                    SOURCENOTAGSTOK = translation_data.get("src_tokens", src_original)
                    TARGETNOTAGSTOK = translation_data.get("tgt_tokens", TARGETNOTAGS)
                    raw_alignment = translation_data.get("alignment", "None")
                    SELECTEDALIGNMENT = " ".join(re.findall(r'\b\d+-\d+\b', raw_alignment))
                    SOURCETAGSTOK = segmentNOTIF
                # -----------------------------------------------------------------
                
                # Executem restore_tags tal com es feia en el mètode original d'èxit
                translation_tags = self.restore_tags(SOURCENOTAGSTOK, SOURCETAGSTOK, SELECTEDALIGNMENT, TARGETNOTAGS, TARGETNOTAGSTOK)
                
                # Unim els tags marginals extrets
                translation_tags = STARTINGTAG + " " + translation_tags + " " + CLOSINGTAG
                
                # Sincronització i restauració de les equivalències de tags reals
                srcEQUILTAGS = src_original
                for t in TAGSEQUIL:
                    srcEQUILTAGS = srcEQUILTAGS.replace(TAGSEQUIL[t], t, 1)
                    
                translation_tags = self.repairSpacesTags(srcEQUILTAGS, translation_tags)
                
                for t in TAGSEQUIL:
                    translation_tags = translation_tags.replace(t, TAGSEQUIL[t], 1)
                
                # Es desa el text restaurat i s'aplica el detokenizer si calgués (simulat per align_spacing)
                translation_data["tgt"] = translation_tags
                translation_data["tgt"] = self.align_spacing(TARGETNOTAGS, translation_data["tgt"])

            # 3. Fixació i normalització numèrica final
            translation_data["tgt"] = self.check_and_replace_numeric(src_original, translation_data["tgt"])

            # 4. Substitucions de sortida directes (changes_output)
            if self.changes_output:
                translation_data = self.change_output(translation_data)

            return translation_data

        except Exception as e:
            print(f"ERROR in Postprocessor global postprocess: {e}")
            return translation_data

    # -----------------------------------------------------------------
    # MÈTODES INTERNS COMPATIBLES
    # -----------------------------------------------------------------
    def lreplace(self, pattern, sub, string):
        return re.sub(f'^{re.escape(pattern)}', sub, string)

    def rreplace(self, pattern, sub, string):
        return re.sub(f'{re.escape(pattern)}$', sub, string)
    
    def has_tags(self, segment: str) -> bool:
        if not segment: return False
        return bool(re.search(r'</?[^>]+>|\{[0-9]+\}', segment))
        
    def get_tags(self, segment: str) -> list:
        if not segment: return []
        return re.findall(r'</?[^>]+>|\{[0-9]+\}', segment)
        
    def get_name(self, tag: str) -> str:
        if not tag: return ""
        return tag.replace("<", "").replace(">", "").replace("/", "").split()[0]
    
    def closest_value(self, input_list, input_value):
        if not input_list: return 0
        return min(input_list, key=lambda x: abs(x - input_value))
        
    def numerate(self, segment: str) -> str:
        if not segment: return ""
        numeratedsegment = []
        cont = 0
        tag_set = set(self.taglist) 
        
        for token in segment.split():
            tokenmod = token.replace("▁", "").strip()
            if tokenmod not in tag_set:
                tokenmod = f"{token}▂{cont}"
                cont += 1
            else:
                tokenmod = token
            numeratedsegment.append(tokenmod)
        return " ".join(numeratedsegment)
        
    def repairSpacesTags(self, slsegment, tlsegment, delimiters=[" ", ".", ",", ":", ";", "?", "!"]):
        sltags = self.get_tags(slsegment)
        tltags = self.get_tags(tlsegment)
        commontags = list((Counter(sltags) & Counter(tltags)).elements())
        
        for tag in commontags:
            try:
                if tag not in slsegment or tag not in tlsegment:
                    continue
                tagaux, tagmod = tag, tag
                idx_sl, idx_tl = slsegment.index(tag), tlsegment.index(tag)
                
                chbfSL = slsegment[idx_sl - 1] if idx_sl > 0 else ""
                chbfTL = tlsegment[idx_tl - 1] if idx_tl > 0 else ""
                
                if chbfSL in delimiters and chbfTL not in delimiters: tagmod = " " + tagmod
                if chbfSL not in delimiters and chbfTL in delimiters: tagaux = " " + tagaux
                
                chafSL = slsegment[idx_sl + len(tag)] if (idx_sl + len(tag)) < len(slsegment) else ""
                chafTL = tlsegment[idx_tl + len(tag)] if (idx_tl + len(tag)) < len(tlsegment) else ""
                
                if chafSL in delimiters and chafTL not in delimiters: tagmod = tagmod + " "
                if chafSL not in delimiters and chafTL in delimiters: tagaux = tagaux + " "
                
                tlsegment = tlsegment.replace(tagaux, tagmod, 1)
                tlsegment = tlsegment.replace(f"  {tag}", f" {tag}", 1)
                tlsegment = tlsegment.replace(f"{tag}  ", f"{tag} ", 1)
            except Exception:
                print("ERROR MTUOC_Postprocessor REPAIRING SPACES:", sys.exc_info())
        return tlsegment
        
    def insert_before(self, segment_list, insertposition, tag):
        for position, token in enumerate(segment_list):
            if "▂" in token and int(token.split("▂")[-1]) == insertposition:
                segment_list.insert(position, tag)
                break
        return segment_list
        
    def insert_after(self, segment_list, insertposition, tag):
        for position, token in enumerate(segment_list):
            if "▂" in token and int(token.split("▂")[-1]) == insertposition:
                segment_list.insert(position + 1, tag)
                break
        return segment_list
        
    def retrieve_indexes(self, segment: str) -> tuple:
        indexes = []
        for token in segment.split():            
            if "▂" in token:
                try: indexes.append(int(token.split("▂")[-1]))
                except ValueError: pass
        if not indexes: return 0, 0
        return min(indexes), max(indexes)
        
    def insert_opentag(self, target_tokens, position, opentag):
        return self.insert_before(target_tokens, max(0, position), opentag)
        
    def insert_closingtag(self, target_tokens, position, closingtag):
        return self.insert_after(target_tokens, max(0, position), closingtag)
        
    def insert_open_close(self, target_tokens, opentag, closetag, minpos, maxpos):
        opendone, closedone = False, False
        for position, token in enumerate(list(target_tokens)): 
            if "▂" in token:
                num = int(token.split("▂")[-1])
                if num == minpos and not opendone:
                    target_tokens.insert(position, opentag)
                    opendone = True
                elif num == maxpos and not closedone:
                    target_tokens.insert(position + 1, closetag)
                    closedone = True
        return target_tokens 
            
    def is_opening_tag(self, tag: str) -> bool:
        if tag.startswith("<") and tag.endswith(">"):
            return not tag[1:-1].strip().startswith("/")
        return False
    
    def is_closing_tag(self, tag: str) -> bool:
        return tag.startswith("</") and tag.endswith(">")

    def create_closing_tag(self, opening_tag: str) -> str:
        if opening_tag.startswith("<") and opening_tag.endswith(">"):
            return f"</{opening_tag[1:-1].split()[0]}>"
        raise ValueError("Invalid opening tag format")
    
    def create_starting_tag(self, closing_tag: str) -> str:
        if closing_tag.startswith("</") and closing_tag.endswith(">"):
            return f"<{closing_tag[2:-1].split()[0]}>"
        raise ValueError("Invalid closing tag format")
            
    def align_spacing(self, string1: str, string2: str) -> str:
        PUNCTUATION = ".,:;(){}[]!¿?«»'\"‘’’“”"
        safe_punc_for_set = ']' + PUNCTUATION.replace(']', '')
        PUNCTUATION_REGEX = f"([{safe_punc_for_set}])"

        tokens1 = re.split(PUNCTUATION_REGEX, string1)
        tokens2 = re.split(PUNCTUATION_REGEX, string2)
        if tokens1[1::2] != tokens2[1::2]: return string2

        new_tokens = []
        for i, token in enumerate(tokens2):
            if i % 2 == 1:
                new_tokens.append(token)
                continue
            current_text = token
            if i < len(tokens1) - 1:
                if tokens1[i].endswith(' ') and not current_text.endswith(' '): current_text += ' '
                elif not tokens1[i].endswith(' ') and current_text.endswith(' '): current_text = current_text.rstrip(' ')
            if i > 0:
                if tokens1[i].startswith(' ') and not current_text.startswith(' '): current_text = ' ' + current_text
                elif not tokens1[i].startswith(' ') and current_text.startswith(' '): current_text = current_text.lstrip(' ')
            new_tokens.append(current_text)
        return "".join(new_tokens)    
        
    def restore_tags(self, SOURCENOTAGSTOK, SOURCETAGSTOK, SELECTEDALIGNMENT, TARGETNOTAGS, TARGETNOTAGSTOK):
        SOURCETAGSTOK = SOURCETAGSTOK.replace(" ▁ ", " ")
        if TARGETNOTAGSTOK.startswith("<s>") and not SOURCENOTAGSTOK.startswith("<s>"):
            SOURCENOTAGSTOK = "<s> " + SOURCENOTAGSTOK
        
        ali = {}
        for a in SELECTEDALIGNMENT.split():
            a1, a2 = map(int, a.split("-"))
            if a1 not in ali: ali[a1] = a2
        if not ali: return TARGETNOTAGS

        nmin, nmax = min(ali.keys()), max(ali.keys())
        inv_ali = {v: k for k, v in ali.items()}
        nonexisting = [i for i in range(nmin, nmax) if i not in ali]
        inv_nonexisting = [i for i in range(min(ali.values()), max(ali.values())) if i not in inv_ali]
        
        for ne in nonexisting: ali[ne] = self.closest_value(inv_nonexisting, ne)

        SOURCETAGSTOKNUM = self.numerate(SOURCETAGSTOK)
        TARGETNOTAGSTOKNUM = self.numerate(TARGETNOTAGSTOK)
        TARGETTAGSTOKNUM = TARGETNOTAGSTOKNUM.split(" ")
        tags_presents = set(re.findall(r'<tag\d+>', SOURCETAGSTOK))
        
        for tag in list(tags_presents):
            tag_id = tag.replace("<tag", "").replace(">", "")
            opentag, closetag = f"<tag{tag_id}>", f"</tag{tag_id}>"
            regexp = f"{opentag}(.*?){closetag}"
            trobat = re.findall(regexp, SOURCETAGSTOKNUM, re.DOTALL)
            if trobat:
                minpos, maxpos = self.retrieve_indexes(trobat[0])
                TARGETTAGSTOKNUM = self.insert_open_close(
                    TARGETTAGSTOKNUM, opentag, closetag, ali.get(minpos, 0), ali.get(maxpos, 0)
                )
                tags_presents.remove(opentag)

        for opentag in list(tags_presents):
            trobat = re.findall(f"{opentag} [^\\s]+", SOURCETAGSTOKNUM, re.DOTALL)
            if trobat:
                posttoken = trobat[0].replace(opentag, "").strip()
                if "▂" in posttoken and int(posttoken.split("▂")[-1]) in ali:
                    TARGETTAGSTOKNUM = self.insert_opentag(TARGETTAGSTOKNUM, ali[int(posttoken.split("▂")[-1])], opentag)

        for tag in set(re.findall(r'</tag\d+>', SOURCETAGSTOK)):
            trobat = re.findall(f"[^\\s]+ {tag}", SOURCETAGSTOKNUM, re.DOTALL)
            if trobat:
                pretoken = trobat[0].replace(tag, "").strip()
                if "▂" in pretoken and int(pretoken.split("▂")[-1]) in ali:
                    TARGETTAGSTOKNUM = self.insert_closingtag(TARGETTAGSTOKNUM, ali[int(pretoken.split("▂")[-1])], tag)

        TARGETTAGS = " ".join([token.split("▂")[0] for token in TARGETTAGSTOKNUM])
        return self.align_spacing(TARGETNOTAGS, TARGETTAGS)
        
    def replace_tags(self, segment: str) -> tuple:
        equil = {}
        if not self.has_tags(segment): return segment, equil
        tagsA = re.findall(r'</?.+?/?>+', segment)
        tagsB = re.findall(r'\{[0-9]+\}+', segment)
        tags = list(dict.fromkeys(tagsA + tagsB))
        
        conttag = 0
        for tag in tags:
            tagrep = f"</tag{conttag}>" if "</" in tag else f"<tag{conttag}>"
            segment = segment.replace(tag, tagrep, 1)
            equil[tagrep] = tag
            if tag in tagsA:
                tagclose = f"</{self.get_name(tag)}>"
                if tagclose in segment:
                    segment = segment.replace(tagclose, f"</tag{conttag}>", 1)
                    equil[f"</tag{conttag}>"] = tagclose
                    if tagclose in tags: tags.remove(tagclose)
            conttag += 1
        return segment, equil
        
    def remove_start_end_tag(self, segment: str) -> tuple:
        starttags, endtags = [], []
        while True:
            trobat = False
            starttag_match = re.match(r"(</?tag[0-9]+>)", segment)
            endtag_match = re.search(r"(</?tag[0-9]+>)$", segment)
            starttag = starttag_match.group() if starttag_match else ""
            endtag = endtag_match.group() if endtag_match else ""
            
            if starttag:
                segment = self.lreplace(starttag, "", segment)
                starttags.append(starttag)
                trobat = True
            if endtag:
                segment = self.rreplace(endtag, "", segment)
                endtags.insert(0, endtag)
                trobat = True
            if not trobat: break
        return segment, "".join(starttags), "".join(endtags)
            
    def change_output(self, translation: dict) -> dict:
        for tofind, tochange in self.changes_output:
            regexp = f"\\b{re.escape(tofind)}\\b"
            translation['tgt'] = re.sub(regexp, tochange, translation['tgt'])
            for alt in translation.get("alternate_translations", []):
                alt['tgt'] = re.sub(regexp, tochange, alt['tgt'])
        return translation
        
    def change_translation(self, translation: dict) -> dict:
        for change in self.changes_translation:
            try:
                tofindSOURCE, tofindTARGET, tochange = change[0], change[1], change[2]
                regexpSOURCE, regexpTARGET = f"\\b{re.escape(tofindSOURCE)}\\b", f"\\b{re.escape(tofindTARGET)}\\b"
                if re.search(regexpSOURCE, translation['src']) and re.search(regexpTARGET, translation['tgt']):
                    translation['tgt'] = re.sub(regexpTARGET, tochange, translation['tgt'])
                if re.search(regexpSOURCE, translation['src']):
                    for alt in translation.get("alternate_translations", []):
                        alt['tgt'] = re.sub(regexpTARGET, tochange, alt['tgt'])
            except Exception:
                print("ERROR MTUOC_Postprocessor change translation:", sys.exc_info())
        return translation
        
    def escape_html(self, text: str) -> str:
        return html.escape(text)
            
    def normalize_number(self, num_str: str) -> str:
        return re.sub(r'[,.\s]', '', num_str)

    def check_and_replace_numeric(self, source: str, target: str) -> str:
        number_pattern = r'[-+]?\d+(?:[\.,\s]\d+)*'
        source_numbers = re.findall(number_pattern, source)
        if not source_numbers: return re.sub(number_pattern, '', target).strip()
        target_numbers = re.findall(number_pattern, target)

        for i, source_num in enumerate(source_numbers):
            if i < len(target_numbers):
                if self.normalize_number(source_num) != self.normalize_number(target_numbers[i]):
                    target = target.replace(target_numbers[i], source_num, 1)
            else:
                target += f" {source_num}"
        if len(target_numbers) > len(source_numbers):
            for i in range(len(source_numbers), len(target_numbers)):
                target = target.replace(target_numbers[i], '', 1)
        return re.sub(r'\s+', ' ', target).strip()
