import sys
import html
import regex  # Fem servir 'regex' en lloc de 're' pel seu suport Unicode complet
import unicodedata
from ftfy import fix_encoding

class Preprocessor:
    
    # Compilem les expressions regulars una sola vegada a nivell de classe per eficiència
    # TAG_XML: Captura <tag>, </tag> o <tag/> de forma segura evitant el backtracking
    _TAG_XML_PATTERN = r'</?[^>]+>'
    # TAG_BRACKETS: Captura {0}, {12}, etc.
    _TAG_BRACKETS_PATTERN = r'\{[0-9]+\}'
    
    # Unió de les dues expressions en una de sola fent servir l'operador OR (|)
    _ANY_TAG_PATTERN = regex.compile(f'(?:{_TAG_XML_PATTERN}|{_TAG_BRACKETS_PATTERN})')
    
    def __init__(self, config_dict: dict = None):
        """
        Inicialitza el Preprocessor carregant la secció 'Preprocess' del YAML.
        """
        self.changes_input = []
        
        # Configuració base per defecte
        self.config = {
            "changes_input": False,
            "fix_encode": True,
            "unescape_html": True,
            "escape_html": False,
            "remove_null_bytes": True,
            "remove_nonprintable": True,
            "clean_unicode_nonscript": True,
            "normalize_spaces": True,
            "remove_tags": False,
            "truecase": False,
            "truecaser_type": None,
            "truecase_model": None,
            "truecase_event": "never",
            "truecaser": None
        }
        self.uppercasetranslation=False
        # Si ens passen la configuració del sub-yaml, l'apliquem de manera dinàmica
        if config_dict:
            if "Preprocess" in config_dict:
                self.config.update(config_dict["Preprocess"])
            else:
                self.config.update(config_dict)
                
        
    def set_changes_input(self, changes):
        """Defineix la llista de substitucions ad-hoc: [[buscar, canviar], ...]"""
        self.changes_input = changes

    def preprocess(self, segment: str) -> str:
        """
        Executa d'una sola passada i en l'ordre lògic correcte tots els passos 
        de preprocessament i neteja definits per l'usuari al fitxer YAML.
        """
        if not segment:
            return ""

        # Funció interna per assegurar que avaluem True/False de forma robusta
        # fins i tot si el YAML conté espais estranys o cadenes com "True "
        def is_active(key):
            val = self.config.get(key, False)
            if isinstance(val, str):
                return val.strip().lower() in ['true', '1', 'yes', 'on']
            return bool(val)

        try:
            # 1. Reparació d'encoding (mojibake) i entitats de text
            if is_active("fix_encode"):
                segment = self.fix_encoding(segment)
            if is_active("unescape_html"):
                segment = self.unescape_html(segment)
            if is_active("escape_html"):
                segment = self.escape_html(segment)

            # 2. Eliminació de tags (XML o placeholders)
            if is_active("remove_tags"):
                segment = self.remove_tags(segment)

            # 3. Eliminació de brossa binària i de control (Equivalents comandes SED)
            if is_active("remove_null_bytes"):
                segment = self.remove_null_bytes(segment)
            if is_active("remove_nonprintable"):
                segment = self.remove_nonprintable(segment)

            # 4. Filtratge de caràcters per scripts Unicode vàlids
            if is_active("clean_unicode_nonscript"):
                segment = self.clean_unicode_nonscript(segment)

            # 5. Substitucions de paraules ad-hoc de l'usuari
            if is_active("changes_input") and self.changes_input:
                segment = self.change_input_custom(segment)

            # 6. Normalització d'espais duplicats (Sempre al final)
            if is_active("normalize_spaces"):
                segment = self.normalize_spaces(segment)
            isupper=False
            if segment.isupper(): isupper=True
            
            if is_active("truecase"):
                if self.config["truecase_event"]=="always":
                    segment=self.config["truecaser"].truecase(segment)
                    if isupper: 
                        self.uppercasetranslation=True
                    else:
                        self.uppercasetranslation=False
                if isupper and self.config["truecase_event"]=="upper":
                    segment=self.config["truecaser"].truecase(segment)
                    self.uppercasetranslation=True
                else:
                    self.uppercasetranslation=False

            return segment

        except Exception as e:
            print(f"ERROR in Preprocessor global preprocess: {e}", sys.exc_info())
            return segment

        except Exception as e:
            print(f"ERROR in Preprocessor global preprocess: {e}", sys.exc_info())
            return segment

    def fix_encoding(self, segment: str) -> str:
        """Repara problemes de codificació de caràcters (mojibake) com MÃ³n -> Món."""
        if not segment: return ""
        return fix_encoding(segment)

    def unescape_html(self, segment: str) -> str:
        """Converteix entitats HTML en caràcters reals (ex: &quot; -> ", &amp; -> &)."""
        if not segment: return ""
        return html.unescape(segment)

    def escape_html(self, segment: str) -> str:
        """Converteix caràcters especials en les seves entitats HTML segures (ex: < -> &lt;)."""
        if not segment: return ""
        return html.escape(segment)

    def remove_null_bytes(self, segment: str) -> str:
        """Equival al sed: s/\x00//g (Elimina caràcters nuls)."""
        if not segment: return ""
        return segment.replace("\x00", "")

    def remove_nonprintable(self, segment: str) -> str:
        r"""Equival al sed: s/[^[:print:]]//g (Elimina caràcters de control \p{C})."""
        if not segment: return ""
        return regex.sub(r'\p{C}', '', segment)

    def clean_unicode_nonscript(self, segment: str) -> str:
        """Conserva NOMÉS lletres, xifres, puntuació i espais de qualsevol script Unicode."""
        if not segment: return ""
        pattern = regex.compile(r'[^\p{L}\p{N}\p{P}\p{Z}]')
        return pattern.sub('', segment)

    def normalize_spaces(self, segment: str) -> str:
        """Normalitza els espais en blanc duplicats i fa un .strip()."""
        if not segment: return ""
        cleaned = regex.sub(r'\s+', ' ', segment)
        return cleaned.strip()
        
    def change_input_custom(self, segment: str) -> str:
        """Aplica les substitucions de paraules definides de l'usuari respectant word boundaries."""
        if not segment or not self.changes_input: return segment
        for tofind, tochange in self.changes_input:
            regexp = r"\b" + regex.escape(tofind) + r"\b"
            segment = regex.sub(regexp, tochange, segment)
        return segment
            
    def has_tags(self, segment: str) -> bool:
        """Comprova si el segment conté alguna etiqueta."""
        if not segment: return False
        return bool(self._ANY_TAG_PATTERN.search(segment))

    def get_tags(self, segment: str) -> list:
        """Retorna una llista amb totes les etiquetes trobades al segment."""
        if not segment: return []
        return self._ANY_TAG_PATTERN.findall(segment)

    def remove_tags(self, segment: str) -> str:
        """Elimina les etiquetes del segment netejant espais duplicats."""
        if not segment: return ""
        segment = regex.sub(r'<[A-Z0-9]+>\s*n\s*(?:<[A-Z0-9]+>|\s*)', ' ', segment)
        segment = self._ANY_TAG_PATTERN.sub(' ', segment)
        segment = " ".join(segment.split())
        return segment

    def addspacetags(self, segment: str) -> str:
        """Assegura que totes les etiquetes tinguin un espai abans i després."""
        if not segment: return ""
        try:
            pattern_replace = regex.compile(f'\\s*({self._ANY_TAG_PATTERN.pattern})\\s*')
            segment = pattern_replace.sub(r' \1 ', segment)
            segment = segment.strip()
        except Exception as e:
            print("ERROR in MTUOC_tags addspacetags", sys.exc_info())
        return segment
    
    def leading_trailing_spaces(self, s: str) -> tuple:
        """Extreu els espais inicials, finals i el text net d'un segment de forma reversible."""
        if not s: return "", "", ""
        stripped_string = s.strip()
        if not stripped_string: return s, "", ""
        start_idx = s.find(stripped_string)
        end_idx = start_idx + len(stripped_string)
        return s[:start_idx], s[end_idx:], stripped_string
        
    def contains_letters(self, s: str) -> bool:
        """Comprova si la cadena conté alguna lletra en qualsevol alfabet Unicode."""
        if not s: return False
        return bool(regex.search(r'\p{L}', s))

    def is_translatable(self, s: str) -> bool:
        """Determina si un segment és traduïble (té lletres un cop eliminats els tags)."""
        if not s: return False
        return self.contains_letters(self.remove_tags(s))

    def analyze_segment_case(self, s: str) -> str:
        """Analitza l'estat de les majúscules/minúscules del segment (sense tags)."""
        s = self.remove_tags(s).strip()
        if not self.contains_letters(s): return "no_case"
        if s.isupper(): return "upper"
        if s.islower(): return "lower"
        if s.istitle(): return "upperfirst"
        return "mixed"

    def split_long_strings(self, strings: list, separators: list = [";", ":", ","], max_length: int = 50) -> list:
        """Divideix cadenes de text llargues basant-se en una llista de separadors."""
        final_result = []
        for s in strings:
            segments_to_process = [s]
            while segments_to_process:
                current = segments_to_process.pop(0)
                if len(current) <= max_length:
                    final_result.append(current)
                    continue
                splitted = False
                for sep in separators:
                    if sep in current:
                        parts = current.split(sep, 1)
                        part_1 = parts[0] + sep
                        part_2 = parts[1]
                        if len(part_1) <= max_length:
                            final_result.append(part_1)
                        else:
                            segments_to_process.insert(0, part_1)
                        segments_to_process.insert(1, part_2)
                        splitted = True
                        break
                if not splitted:
                    final_result.append(current)
        return final_result
