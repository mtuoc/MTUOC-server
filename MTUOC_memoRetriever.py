# memoRetriever_ngram.py

import os
import sqlite3
import re
from rapidfuzz import fuzz
import re





class memoRetriever:
    def __init__(self, db_path="memoria.sqlite", nmin=4, nmax=8):
        if not os.path.exists(db_path):
            raise FileNotFoundError("Base de dades no trobada.")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cur = self.conn.cursor()
        self.sl = None
        self.tl = None
        self.fuzzy = True
        self.nmin = nmin
        self.nmax = nmax

    def set_languages(self, sl, tl):
        self.sl = sl
        self.tl = tl
        
    def disable_fuzzy(self):
        self.fuzzy = False

    def strip_tags(self, text):
        return re.sub(r'<[^>]+>', '', text)
        
    def replace_numbers(self, text):
        """
        Reemplaça expressions numèriques per @NUM@ i retorna:
          - el text amb els reemplaçaments
          - una llista amb les expressions numèriques trobades (ordre d'aparició)
        """
        numbers = []

        def replacer(match):
            num = match.group(0)
            numbers.append(num)
            return "@NUM@"

        # Regex que captura nombres enters i decimals (123, 123.45, 1.234, etc.)
        # Pots adaptar-lo segons el que consideris "expressió numèrica"
        pattern = re.compile(r"\d+(?:[\.,]\d+)*")
        new_text = pattern.sub(replacer, text)

        return new_text, numbers

    def restoreNUM(self, text, numbers):
        """
        Reemplaça seqüencialment els placeholders @NUM@ del text
        pels valors de la llista 'numbers'.

        - text: string amb un o més @NUM@
        - numbers: llista d'expressions numèriques
        """
        numbers_iter = iter(numbers)
    
        def replacer(_):
            try:
                return next(numbers_iter)
            except StopIteration:
                # Si hi ha més @NUM@ que nombres, els deixem tal qual
                return "@NUM@"

        return re.sub(r"@NUM@", replacer, text)


    def generate_char_ngrams(self, text, nmin=4, nmax=8):
        text = self.strip_tags(text)
        ngram_set = set()
        for n in range(nmin, nmax + 1):
            for i in range(len(text) - n + 1):
                ngram_set.add(text[i:i+n])
        return list(ngram_set)

    def retrieve(self, sl_input, min_sim=70, max_results=5, prefer_exact=True):
        # Normalitza l’entrada de la mateixa manera que ho facis quan guardes
        sl_clean = self.strip_tags(sl_input)
        sl_clean, numbers = self.replace_numbers(sl_clean)
        # 1) Coincidència exacta (via índex compost ON memory(sl_lang, tl_lang, sl_segment))
        #    IMPORTANT: assegura't que el valor a memory.sl_segment té la mateixa normalització
        #    que 'sl_clean'. Si guardes amb etiquetes, canvia 'sl_clean' per 'sl_input'.
        results = []
        if prefer_exact or not self.fuzzy:
            self.cur.execute("""
                SELECT sl_segment, tl_segment, count
                FROM memory
                WHERE sl_lang = ? AND tl_lang = ? AND sl_segment = ?
                ORDER BY count DESC
                LIMIT ?
            """, (self.sl, self.tl, sl_clean, max_results))
            exact_rows = self.cur.fetchall()
            if exact_rows:
                # puntuació 100 per match exacte
                #return [(row[0], row[1], 100.0) for row in exact_rows]
                for row in exact_rows:
                    recuperatSL=self.restoreNUM(row[0],numbers)
                    recuperatTL=self.restoreNUM(row[1],numbers)
                    results.append((recuperatSL, recuperatTL, 100))
        # 2) Recuperació aproximada per n-grams (amb JOIN per filtrar llengües aviat)
        if self.fuzzy and len(results)==0:
            ngrams = self.generate_char_ngrams(sl_input)
            if not ngrams:
                return []
            freqDist={}
            for ngram in ngrams:
                self.cur.execute("SELECT segmentid FROM ngrams WHERE ngram = ?", (ngram,))
                ids = self.cur.fetchall()
                for resultat in ids:
                    if not resultat[0] in freqDist:
                        freqDist[resultat[0]]=1
                    else:
                        freqDist[resultat[0]]+=1
            matches={}
            for clau in sorted(freqDist, key=freqDist.get, reverse=True):
                self.cur.execute("SELECT sl_segment, tl_segment FROM memory WHERE id = ?", (clau,))
                retrieved = self.cur.fetchone()
                slmatch=retrieved[0]
                tlmatch=retrieved[1]
                score = fuzz.ratio(sl_input,slmatch) 
                matches[retrieved]=score
            ordered_keys = sorted(matches, key=matches.get, reverse=True)
            contmatches=0
            for key in ordered_keys:
                contmatches+=1
                if matches[key]<min_sim or contmatches>=max_results:
                    break
                print(matches[key],key)
                results.append((key[0], key[1], matches[key]))
        # Ordena per similitud (per si cal)
        results.sort(key=lambda x: x[2], reverse=True)
        
        return results[:max_results]
                
    def retrieveMTUOC(self, sl_input, min_sim=70, max_results=5, prefer_exact=True):
        matches=self.retrieve(sl_input, min_sim=70, max_results=5, prefer_exact=True)
        if len(matches)>0:
            self.alternate_translations=[]
            self.response={}
            self.response["system_name"]="TranslationMemory"
            self.response["src_tokens"]=sl_input
            self.response["tgt_tokens"]=matches[0][1]
            self.response["src_subwords"]=sl_input
            self.response["tgt_subwords"]=matches[0][1]
            self.response["tgt"]=matches[0][1]
            self.response["alignment"]=""
            self.response["alternate_translations"]=self.alternate_translations
        else:
            self.response=None
        return(self.response)
        
