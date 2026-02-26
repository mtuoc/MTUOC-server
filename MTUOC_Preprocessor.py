import re
import regex
import unicodedata
from ftfy import fix_encoding
import html
from MTUOC_misc import printLOG


class Preprocessor:
    def __init__(self):
        self.changes_input=[]
        
    def set_changes_input(self,changes):
        self.changes_input=changes
        
    def has_tags(self, segment):
        response=False
        tagsA = re.findall(r'</?.+?/?>', segment)
        tagsB = re.findall(r'\{[0-9]+\}', segment)
        if len(tagsA)>0 or len(tagsB)>0:
            response=True
        return(response)
        
    def remove_tags(self, segment):
        #ep_pattern=r"<[A-Z0-9]+>\s*n\s*<[A-Z0-9]+>"
        #ep_pattern2=r"<[A-Z0-9]+>\s*n\s+"
        #segmentnotags=re.sub('(<[A-Z[0-9]+>n<[A-Z][0-9]+>)', " ",segment) #AD HOC EP
        segmentnotags=re.sub(r'(<[A-Z0-9]+>\s*n\s*<[A-Z0-9]+>)', " ",segment) #AD HOC EP
        segmentnotags=re.sub(r'(<[A-Z0-9]+>\s*n\s+)', " ",segment) #AD HOC EP
        segmentnotags=re.sub(r'(<[^>]+>)', " ",segmentnotags)
        segmentnotags=re.sub(r'({[0-9]+})', " ",segmentnotags)
        segmentnotags=" ".join(segmentnotags.split())
        return(segmentnotags)
        
    def get_tags(self, segment):
        tagsA = re.findall(r'</?.+?/?>', segment)
        tagsB = re.findall(r'\{[0-9]+\}', segment)
        tags=tagsA.copy()
        tags.extend(tagsB)
        return(tags)
    
    def addspacetags(self,segment):
        alltags=self.get_tags(segment)
        try:
            for t in alltags:
                cB=" "+t
                if segment.find(cB)==-1:
                    segment=segment.replace(t,cB)
                cA=t+" "
                if segment.find(cA)==-1:
                    segment=segment.replace(t,cA)
        except:
            printLOG(2,"ERROR in MTUOC_tags addspacetags",sys.exc_info())
        return(segment)
                
    def leading_trailing_spaces(self, s):
        # Use regex to find leading and trailing whitespace characters
        leading_spaces = re.match(r'^\s*', s).group()  # Matches leading whitespace
        trailing_spaces = re.search(r'\s*$', s).group()  # Matches trailing whitespace
        
        # Remove leading and trailing whitespace from the string
        stripped_string = s.strip()
        
        return leading_spaces, trailing_spaces, stripped_string
        
    def remove_control_characters(self,cadena):
        return regex.sub(r'\p{C}', ' ', cadena)
        
    def is_printable(self, char):
        category = unicodedata.category(char)
        return not (category.startswith('C') or category in ['Zl', 'Zp', 'Cc'])
        
    def remove_non_printable(self, string):
        cleaned_string = ''.join(c if self.is_printable(c) else ' ' for c in string)
        return(cleaned_string)
        
    def remove_non_latin_extended_chars(self, text):
        # Define the pattern to match only allowed characters
        # This includes basic Latin letters, Latin Extended characters, spaces, and common punctuation marks
        #pattern = re.compile(r'''[^0-9A-Za-z\u00C0-\u00FF\u0100-\u024F\u1E00-\u1EFF\uA720-\uA7FF\s.,:;!?'"“”‘’«»()\-@#\$%\^&\*\+\/\\_\|~<>{}\[\]=]''', re.VERBOSE)
        pattern = re.compile(r'''[^0-9\s.,:;!?'"“”‘’«»()\-@#\$%\^&\*\+\/\\_\|~<>{}\[\]=]\u0000-\u007F\u0080-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\u2C60-\u2C7F\uA720-\uA7FF\uAB30-\uAB6F''', re.VERBOSE)
        cleaned_text = pattern.sub(' ', text)
        return cleaned_text

    def remove_non_unicode_script_chars(self, text):
        """
        Remove characters that are not in the specified Unicode ranges for all scripts.

        Parameters:
        text (str): The input text to be cleaned.

        Returns:
        str: The cleaned text with only allowed characters.
        """
        # Define the pattern to match only allowed characters from all Unicode scripts
        pattern = re.compile(r'''[^\u0000-\u007F\u0080-\u00FF\u0100-\u017F\u0180-\u024F\u0250-\u02AF\u02B0-\u02FF
                                 \u0300-\u036F\u0370-\u03FF\u0400-\u04FF\u0500-\u052F\u0530-\u058F\u0590-\u05FF
                                 \u0600-\u06FF\u0700-\u074F\u0750-\u077F\u0780-\u07BF\u07C0-\u07FF\u0800-\u083F
                                 \u0840-\u085F\u0860-\u086F\u08A0-\u08FF\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F
                                 \u0A80-\u0AFF\u0B00-\u0B7F\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF\u0D00-\u0D7F
                                 \u0D80-\u0DFF\u0E00-\u0E7F\u0E80-\u0EFF\u0F00-\u0FFF\u1000-\u109F\u10A0-\u10FF
                                 \u1100-\u11FF\u1200-\u137F\u1380-\u139F\u13A0-\u13FF\u1400-\u167F\u1680-\u169F
                                 \u16A0-\u16FF\u1700-\u171F\u1720-\u173F\u1740-\u175F\u1760-\u177F\u1780-\u17FF
                                 \u1800-\u18AF\u18B0-\u18FF\u1900-\u194F\u1950-\u197F\u1980-\u19DF\u19E0-\u19FF
                                 \u1A00-\u1A1F\u1A20-\u1AAF\u1AB0-\u1AFF\u1B00-\u1B7F\u1B80-\u1BBF\u1BC0-\u1BFF
                                 \u1C00-\u1C4F\u1C50-\u1C7F\u1C80-\u1C8F\u1C90-\u1CBF\u1CC0-\u1CCF\u1CD0-\u1CFF
                                 \u1D00-\u1D7F\u1D80-\u1DBF\u1DC0-\u1DFF\u1E00-\u1EFF\u1F00-\u1FFF\u2000-\u206F
                                 \u2070-\u209F\u20A0-\u20CF\u20D0-\u20FF\u2100-\u214F\u2150-\u218F\u2190-\u21FF
                                 \u2200-\u22FF\u2300-\u23FF\u2400-\u243F\u2440-\u245F\u2460-\u24FF\u2500-\u257F
                                 \u2580-\u259F\u25A0-\u25FF\u2600-\u26FF\u2700-\u27BF\u27C0-\u27EF\u27F0-\u27FF
                                 \u2800-\u28FF\u2900-\u297F\u2980-\u29FF\u2A00-\u2AFF\u2B00-\u2BFF\u2C00-\u2C5F
                                 \u2C60-\u2C7F\u2C80-\u2CFF\u2D00-\u2D2F\u2D30-\u2D7F\u2D80-\u2DDF\u2DE0-\u2DFF
                                 \u2E00-\u2E7F\u2E80-\u2EFF\u2F00-\u2FDF\u2FF0-\u2FFF\u3000-\u303F\u3040-\u309F
                                 \u30A0-\u30FF\u3100-\u312F\u3130-\u318F\u3190-\u319F\u31A0-\u31BF\u31C0-\u31EF
                                 \u31F0-\u31FF\u3200-\u32FF\u3300-\u33FF\u3400-\u4DBF\u4DC0-\u4DFF\u4E00-\u9FFF
                                 \uA000-\uA48F\uA490-\uA4CF\uA4D0-\uA4FF\uA500-\uA63F\uA640-\uA69F\uA6A0-\uA6FF
                                 \uA700-\uA71F\uA720-\uA7FF\uA800-\uA82F\uA830-\uA83F\uA840-\uA87F\uA880-\uA8DF
                                 \uA8E0-\uA8FF\uA900-\uA92F\uA930-\uA95F\uA960-\uA97F\uA980-\uA9DF\uA9E0-\uA9FF
                                 \uAA00-\uAA5F\uAA60-\uAA7F\uAA80-\uAADF\uAAE0-\uAAFF\uAB00-\uAB2F\uAB30-\uAB6F
                                 \uAB70-\uABBF\uABC0-\uABFF\uAC00-\uD7AF\uD7B0-\uD7FF\uD800-\uDB7F\uDB80-\uDBFF
                                 \uDC00-\uDFFF\uE000-\uF8FF\uF900-\uFAFF\uFB00-\uFB4F\uFB50-\uFDFF\uFE00-\uFE0F
                                 \uFE10-\uFE1F\uFE20-\uFE2F\uFE30-\uFE4F\uFE50-\uFE6F\uFE70-\uFEFF\uFF00-\uFFEF
                                 \uFFF0-\uFFFF]''', re.VERBOSE)

        # Substitute non-matching characters with an empty string
        cleaned_text = pattern.sub(' ', text)
        return cleaned_text
        
    def change_input(self,segment):
        segment.replace("\x10"," ")
        
        for change in self.changes_input:
            tofind=change[0]
            tochange=change[1]
            regexp="\\b"+tofind+"\\b"
            trobat=re.findall(regexp,segment)
            if trobat: 
                segment=re.sub(regexp, tochange, segment)
        return(segment)
        
    def fix_encoding(self, segment):
        segment=fix_encoding(segment)
        return(segment)
        
    def unescape_html(self, segment):
        segment=html.unescape(segment)
        return(segment)
        
    def analyze_segment_case(self, s: str) -> str:
        #REMOVE TAGS
        s=self.remove_tags(s)
        
        # Check if the string is empty or contains no alphabetic characters
        if not any(c.isalpha() for c in s):
            return "no_case"

        # Check for 'upperfirst' (first character uppercase, rest lowercase)
        if s[0].isupper() and s[1:].islower():
            return "upperfirst"
        
        # Check if all characters are uppercase
        if s.isupper():
            return "upper"
        
        # Check if all characters are lowercase
        if s.islower():
            return "lower"
        
        # Check if the string mixes uppercase and lowercase
        if any(c.islower() for c in s) and any(c.isupper() for c in s):
            return "mixed"
        
        # For scripts that don't have upper and lower case, treat as "no_case"
        return "no_case"
    
    
    def split_long_strings(self, strings, separators=[";", ":", ","], max_length=50):
        def split_string(s):
            queue = [s]
            result = []
            while queue:
                current = queue.pop(0)
                if len(current) <= max_length:
                    result.append(current)
                else:
                    for sep in separators:
                        if sep in current:
                            parts = current.split(sep, 1)
                            result.append(parts[0] + sep)
                            queue.insert(0, parts[1])
                            break
                    else:
                        # If no separators are found, add the entire string and stop further splitting
                        result.append(current)
                        break
            return result

        final_result = []
        for s in strings:
            final_result.extend(split_string(s))
        return final_result
        
    def contains_letters(self, s: str) -> bool:
        # Check if the string contains any letter in any script (Unicode property \p{L})
        return bool(regex.search(r'\p{L}', s))
        
    def is_translatable(self, s: str) -> bool:
        s=self.remove_tags(s)
        if self.contains_letters(s):
            return(True)
        else:
            return(False)
        
        

        
