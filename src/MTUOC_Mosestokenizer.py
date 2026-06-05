#    MTUOC_tokenizer_moses 5.0
#    Adaptació del tokenitzador de Moses per a la compatibilitat amb MTUOC
#    Copyright (C) 2026 MTUOC Project / Adaptació Moses

import sys
import re
import html
from sacremoses import MosesTokenizer, MosesDetokenizer

class Tokenizer():
    def __init__(self, lang='en'):
        self.lang = lang
        self.mt = MosesTokenizer(lang=self.lang)
        self.md = MosesDetokenizer(lang=self.lang)
        self.re_num = re.compile(r'[\d\,\.]+')

    def split_numbers(self, segment):
        xifres = re.findall(self.re_num, segment)
        for xifra in xifres:
            xifrastr = str(xifra)
            xifra2 = []
            contpos = 0
            for x in xifrastr:
                if not contpos == 0: xifra2.append(" ￭")
                xifra2.append(x)
                contpos += 1
            xifra2 = "".join(xifra2)
            segment = segment.replace(xifra, xifra2)
        return segment

    def tokenize(self, segment):
        # Moses retorna una llista de tokens, els unim amb espais simples
        tokens = self.mt.tokenize(segment, escape=False)
        return ' '.join(tokens)
        
    def detokenize(self, segment):
        tokens = segment.split()
        return self.md.detokenize(tokens)

    def tokenize_j(self, segment):
        # El format joiner (￭) de MTUOC indica que el token anava enganxat.
        # Com que Moses no ens diu on hi havia espais originals, recreem la lògica 
        # marcant els caràcters especials i de puntuació típics que es desenganxen.
        tokens = self.mt.tokenize(segment, escape=False)
        res = []
        for t in tokens:
            if len(t) == 1 and t in '.,;:!?()[]{}«»“”‘’"\'':
                res.append(f"￭{t}￭")
            else:
                res.append(t)
        tokenized = ' '.join(res)
        # Netegem dobles joiners o espais absurds que hagin pogut quedar
        tokenized = tokenized.replace("￭ ￭", "￭￭").replace("￭  ￭", "￭￭")
        return ' '.join(tokenized.split())

    def detokenize_j(self, segment):
        segment = segment.replace(" ￭", "").replace("￭ ", "").replace("￭", "")
        return ' '.join(segment.split())
        
    def tokenize_jn(self, segment):
        tokenized = self.tokenize_j(segment)
        tokenized = self.split_numbers(tokenized)
        return ' '.join(tokenized.split())

    def detokenize_jn(self, segment):
        return self.detokenize_j(segment)
        
    def tokenize_s(self, segment):
        # En el format splitter (▁), els espais reals es tornen ' ▁' i els tokens s'ajunten.
        # Ho emulem unint els tokens obtinguts de Moses amb el marcador.
        tokens = self.mt.tokenize(segment, escape=False)
        tokenized = " ▁".join(tokens)
        return ' '.join(tokenized.split())
        
    def detokenize_s(self, segment):
        segment = segment.replace(" ", "")
        segment = segment.replace("▁", " ")
        return ' '.join(segment.split())

    def tokenize_sn(self, segment):
        tokens = self.mt.tokenize(segment, escape=False)
        intermig = " ".join(tokens)
        intermig = self.split_numbers(intermig)
        
        # Convertim el resultat numèric fragmentat al format splitter de MTUOC
        intermig = intermig.replace("￭ ", "￭").replace(" ￭", "￭")
        intermig = intermig.replace(" ", " ▁")
        intermig = intermig.replace("￭", " ")
        return ' '.join(intermig.split())

    def detokenize_sn(self, segment):
        return self.detokenize_s(segment)


def print_help():
    print("MTUOC_Mosestokenizer.py A wrapper for Moses implementing MTUOC API, usage:")
    print("Simple tokenization:")
    print('    cat text.txt | python3 MTUOC_Mosestokenizer.py tokenize en')
    print('    python3 MTUOC_Mosestokenizer.py tokenize en < text.txt > tokenized.txt')
    print()
    print("Advanced options:")
    print("    tokenize_j, detokenize_j, tokenize_jn, detokenize_jn")
    print("    tokenize_s, detokenize_s, tokenize_sn, detokenize_sn")


if __name__ == "__main__":
    # Parsea arguments a l'estil MTUOC: [acció] [idioma]
    action = "tokenize"
    lang = "en"  # per defecte
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print_help()
            sys.exit()
        action = sys.argv[1]
        
    if len(sys.argv) > 2:
        lang = sys.argv[2]

    tokenizer = Tokenizer(lang=lang)

    for line in sys.stdin:
        line = line.strip()
        line = line.replace("’", "'")
        line = html.unescape(line)
        
        if action == "tokenize":
            outsegment = tokenizer.tokenize(line)
        elif action == "detokenize":
            outsegment = tokenizer.detokenize(line)
        elif action == "tokenize_j":
            outsegment = tokenizer.tokenize_j(line)
        elif action == "detokenize_j":
            outsegment = tokenizer.detokenize_j(line)
        elif action == "tokenize_jn":
            outsegment = tokenizer.tokenize_jn(line)
        elif action == "detokenize_jn":
            outsegment = tokenizer.detokenize_jn(line)
        elif action == "tokenize_s":
            outsegment = tokenizer.tokenize_s(line)
        elif action == "detokenize_s":
            outsegment = tokenizer.detokenize_s(line)
        elif action == "tokenize_sn":
            outsegment = tokenizer.tokenize_sn(line)
        elif action == "detokenize_sn":
            outsegment = tokenizer.detokenize_sn(line)
        else:
            # Si per error es passa l'idioma primer, reajusta l'acció
            outsegment = tokenizer.tokenize(line)
            
        print(outsegment)
