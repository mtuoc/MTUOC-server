#    MTUOC_tokenizer_cat 5.0
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


import string
import re
import sys
import html

QUOTES = (
#adapted from: https://gist.github.com/goodmami/ quotes.py
    '\u0022'  # quotation mark (")
    '\u0027'  # apostrophe (')
    '\u00ab'  # left-pointing double-angle quotation mark
    '\u00bb'  # right-pointing double-angle quotation mark
    '\u2018'  # left single quotation mark
    '\u2019'  # right single quotation mark
    '\u201a'  # single low-9 quotation mark
    '\u201b'  # single high-reversed-9 quotation mark
    '\u201c'  # left double quotation mark
    '\u201d'  # right double quotation mark
    '\u201e'  # double low-9 quotation mark
    '\u201f'  # double high-reversed-9 quotation mark
    '\u2039'  # single left-pointing angle quotation mark
    '\u203a'  # single right-pointing angle quotation mark
    '\u300c'  # left corner bracket
    '\u300d'  # right corner bracket
    '\u300e'  # left white corner bracket
    '\u300f'  # right white corner bracket
    '\u301d'  # reversed double prime quotation mark
    '\u301e'  # double prime quotation mark
    '\u301f'  # low double prime quotation mark
    '\ufe41'  # presentation form for vertical left corner bracket
    '\ufe42'  # presentation form for vertical right corner bracket
    '\ufe43'  # presentation form for vertical left corner white bracket
    '\ufe44'  # presentation form for vertical right corner white bracket
    '\uff02'  # fullwidth quotation mark
    '\uff07'  # fullwidth apostrophe
    '\uff62'  # halfwidth left corner bracket
    '\uff63'  # halfwidth right corner bracket
)

HYPENS = ('\u2010','\u2011','\u2012','\u2013')

class Tokenizer():
    def __init__(self):
        self.specialchars=["¿","¡",]
        self.specialchars.extend(QUOTES)
        self.specialchars.extend(HYPENS)
        self.subs=[]
        self.re_num = re.compile(r'[\d\,\.]+')
        self.abr=["cм.","абл.","абс.","абх.","авар.","авг.","австр.","австрал.","авт.","агр.","адж.","адм.","адыг.","азерб.","акад.","акк.","акц.","алб.","алг.","алж.","алт.","алф.","альм.","альп.","амер.","анат.","анг.","англ.","ангол.","аннот.","антич.","ап.","апр.","арам.","аргент.","арифм.","арт.","архим.","архип.","асс.","ассир.","асср","астр.","ат.","атм.","афг.","афр.","б.","балк.","балт.","башк.","безв.","безл.","бельг.","библ.","биогр.","биол.","бирм.","бол.","болг.","буд.","бывш.","бюдж.","бюлл.","в.","вал.","вв.","в.д.","вдхр.","вед.","вел.","венг.","вкл.","вл.","внеш.","внутр.","вод. ст.","воен.","возв.","возд.","воскр.","вост.","вт.","вьетн.","г.","га.","гав.","газ.","гвин.","гвт.","гг.","ггц.","ген.","ген. л.","ген. м.","ген. п.","геогр.","геод.","геол.","геом.","герм.","г­жа.","гл.","гор.","гос.","госп.","гр.","град.","гражд.","греч.","груз.","губ.","гц.","гэв.","дб.","д. б. н.","д. в.","д. г.­м. н.","д. г. н.","деепр.","действ.","дек.","дер.","дж.","диак.","диал.","диам.","див.","диз.","д. и. н.","дир.","д. иск.","дисс.","дист.","дифф.","дкг.","дкл.","дкм.","дм.","д. м. н.","д. н.","д. о.","доб.","док.","докт.","долл.","доп.","доц.","д. п.","дптр.","др.","драм.","д. т. н.","дубл.","д. ф.­м. н.","д. ф. н.","д. х. н.","д. ч.","евр.","европ.","егип.","ед.","ед. ч.","ежедн.","ежемес.","еженед.","ефр.","ж.","ж. д.","жен.","женск.","жит.","журн.","зав.","зав. хоз.","загл.","зал.","зам.","заруб.","засл. арт.","з. д.","з.д.","зем.","зол.","игум.","иером.","им.","инд.","индонез.","иностр.","и. о.","и.о.","итал.","канд.","кв.","ква.","квт.","кг.","кгс.","кгц.","кд.","кдж.","кирг.","ккал.","кл.","км.","кмоль.","книжн.","коп.","корп.","кэв.","лаб.","лат.","латв.","лейт.","лит.","л.с.","м.","макс.","мат.","матем.","маш.","м­во.","мгц.","мдж.","мед.","мес.","мин.","мин­во.","митр.","мка.","мкал.","мкв.","мквт.","мкм.","мкмк.","мком.","мкпа.","мкр.","мкф.","мкюри.","мл.","млк.","млн.","млрд.","м.н.с.","мн.ч.","моск.","мпа.","м­р.","мс.","муж.","мужск.","мэв.","нем.","н.э.","обл.","пер.","пл.","пос.","пр.","р.","рис.","род.","св.","сокр.","ст.","ст.н.с.","стр.","с.ш.","т.","т.д.","т.е.","тел.","т.к.","т.н.","т.о.","тов.","т.п.","трлн.","т.с.","тыс.","ул.","ум.","фр.","франц.","ч.","чел."]
        abr_aux=[]
        for a in self.abr:
            am1=a.capitalize()
            am2=a.upper()
            abr_aux.append(am1)
            abr_aux.append(am2)
        self.abr.extend(abr_aux)
        self.setabr=set(self.abr)
        self.abrsig=()
    def split_numbers(self,segment):
        xifres = re.findall(self.re_num,segment)
        for xifra in xifres:
            xifrastr=str(xifra)
            xifrasplit=xifra.split()
            xifra2=[]
            contpos=0
            for x in xifrastr:
                if not contpos==0: xifra2.append(" ￭")
                xifra2.append(x)
                contpos+=1
            xifra2="".join(xifra2)
            segment=segment.replace(xifra,xifra2)
        return(segment)



    def protect_tags(self, segment):
        tags=re.findall(r'<[^>]+>',segment)
        for tag in tags:
            ep=False
            ef=False
            if segment.find(" "+tag)==-1:ep=True
            if segment.find(tag+" ")==-1:ef=True
            tagmod=tag.replace("<","&#60;").replace(">","&#62;").replace("=","&#61;").replace("'","&#39;").replace('"',"&#34;").replace("/","&#47;").replace(" ","&#32;")
            if ep: tagmod=" ￭"+tagmod
            if ef: tagmod=tagmod+"￭ "
            segment=segment.replace(tag,tagmod)
        tags=re.findall(r'\{[0-9]+\}',segment)
        for tag in tags:
            ep=False
            ef=False
            if segment.find(" "+tag)==-1:ep=True
            if segment.find(tag+" ")==-1:ef=True
            tagmod=tag.replace("{","&#123;").replace("}","&#125;")
            if ep: tagmod=" ￭"+tagmod
            if ef: tagmod=tagmod+"￭ "
            segment=segment.replace(tag,tagmod)
        return(segment) 
    
    def protect_abr(self,cadena):
        setcadena=set(cadena.split(" "))
        common=(self.setabr & setcadena)
        self.abrsig=list(common)
        for a in common:
            amod=a+" "
            apro=a.replace(".","&#46;")
            cadena=cadena.replace(amod,apro)
        sigles=re.findall(r'((\w\.){2,})',cadena)
        for s in sigles:
            a=s[0]
            self.abrsig.append(a)
            amod=a+" "
            apro=a.replace(".","&#46;")
            cadena=cadena.replace(amod,apro)
        return(cadena)
    
    def unprotect(self, cadena):
        cadena=cadena.replace("&#39;","'").replace("&#45;","-").replace("&#60;","<").replace("&#62;",">").replace("&#34;",'"').replace("&#61;","=").replace("&#32;","▁").replace("&#47;","/").replace("&#123;","{").replace("&#125;","}")
        return(cadena)
    
    def unprotect_tags(self, cadena):
        cadena=cadena.replace("&#60;","<").replace("&#62;",">")
        return(cadena)
    
    def unprotect_abr(self,cadena):
        for a in self.abrsig:
            amod=a+" "
            apro=a.replace(".","&#46;")
            cadena=cadena.replace(apro,amod)
        return(cadena)

    def main_tokenizer(self,segment):
        segment=" "+segment+" "
        cadena=self.protect_tags(segment)
        cadena=self.protect_abr(cadena)
        for s in self.subs:
            sA=s.replace("￭","")
            sB=s.replace("'","&#39;").replace("-","&#45;")
            if s.startswith("￭"):sB=" "+sB
            if s.endswith("￭"):sB=sB+" "
            cadena = re.sub(sA+r'\b', sB, cadena)
            cadena = re.sub(r'\b'+sA, sB, cadena)
            cadena = re.sub(sA.upper()+r'\b', sB.upper(), cadena)
            cadena = re.sub(r'\b'+sA.upper(), sB.upper(), cadena)
        punt=list(string.punctuation)
        exceptions=["&",";","#"]
        for e in exceptions:
            punt.remove(e)
        
        for p in punt:
            ppre=" ￭"+p
            ppost=p+"￭ "
            try:
                expr1="(\\S)\\"+p+"(\\s)"
                expr2=r"\1"+ppre+r"\2"
                cadena = re.sub(expr1,expr2, cadena)
                expr1="(\\s)\\"+p+"(\\S)"
                expr2=r"\1"+ppost+r"\2"
                cadena = re.sub(expr1,expr2, cadena)
            except:
                pass
        cadena=self.unprotect_tags(cadena)
        cadena=self.unprotect_abr(cadena)
        
        for p in self.specialchars:
            pmod=p+" "
            if cadena.find(pmod)>=-1:
                pmod2=p+"￭ "
                cadena=cadena.replace(p,pmod2)
            pmod=" "+p
            if cadena.find(pmod)>=-1:
                pmod2=" ￭"+p
                cadena=cadena.replace(p,pmod2)

        cadena=self.unprotect(cadena)
        
        for p in exceptions:
            pmod=p+" "
            if cadena.find(pmod)>=-1:
                pmod2=p+"￭ "
                cadena=cadena.replace(p,pmod2)
            pmod=" "+p
            if cadena.find(pmod)>=-1:
                pmod2=" ￭"+p
                cadena=cadena.replace(p,pmod2)    
        
        cadena=cadena.replace("▁"," ")
        cadena=' '.join(cadena.split())   
        return(cadena)

    def tokenize(self,segment):
        tokenized=self.main_tokenizer(segment)
        tokenized=tokenized.replace("￭","")
        tokenized=' '.join(tokenized.split()) 
        return(tokenized)
        
    def detokenize(self, segment):
        for sub in self.subs:
            subA=sub.replace("￭"," ")
            subB=sub.replace("￭","")
            segment=segment.replace(subA,subB)
            segment=segment.replace(subA.capitalize(),subB.capitalize())
            segment=segment.replace(subA.upper(),subB.upper())
        segment=segment.replace(" .",".")
        segment=segment.replace(" ,",",")
        segment=segment.replace(" :",":")
        segment=segment.replace(" ;",";")
        segment=segment.replace(" :",":")
        segment=segment.replace(" )",")")
        segment=segment.replace("( ","(")
        segment=segment.replace(" ]","]")
        segment=segment.replace("[ ","[")
        segment=segment.replace(" }","}")
        segment=segment.replace("{ ","{")
        segment=segment.replace(" !","!")
        segment=segment.replace("¡ ","¡")
        segment=segment.replace(" ?","?")
        segment=segment.replace("¿ ","¿")
        segment=segment.replace(" »","»")
        segment=segment.replace("« ","«")
        segment=segment.replace("‘ ","‘")
        segment=segment.replace(" ’","’")
        segment=segment.replace("“ ","“")
        segment=segment.replace(" ”","”")
        segment=' '.join(segment.split()) 
        return(segment)

    def tokenize_j(self,segment):
        tokenized=self.main_tokenizer(segment)
        tokenized=' '.join(tokenized.split()) 
        return(tokenized)

    def detokenize_j(self,segment):
        segment=segment.replace(" ￭","")
        segment=segment.replace("￭ ","")
        segment=segment.replace("￭","")
        detok=segment
        detok=' '.join(detok.split()) 
        return(detok)
        
    def tokenize_jn(self,segment):
        tokenized=self.tokenize_j(segment)
        tokenized=self.split_numbers(tokenized)
        tokenized=' '.join(tokenized.split()) 
        return(tokenized)

    def detokenize_jn(self,segment):
        segment=self.detokenize_j(segment)
        return(segment)
        
    def tokenize_s(self,segment):
        tokenized=self.main_tokenizer(segment)
        tokenized=tokenized.replace("￭ ","￭")
        tokenized=tokenized.replace(" ￭","￭")
        tokenized=tokenized.replace(" "," ▁")
        tokenized=tokenized.replace("￭"," ")
        tokenized=' '.join(tokenized.split()) 
        return(tokenized)
        
    def detokenize_s(self,segment):
        segment=segment.replace(" ","")
        segment=segment.replace("▁"," ")
        detok=segment
        detok=' '.join(detok.split()) 
        return(detok)

    def tokenize_sn(self,segment):
        tokenized=self.main_tokenizer(segment)
        tokenized=self.split_numbers(tokenized)
        tokenized=tokenized.replace("￭ ","￭")
        tokenized=tokenized.replace(" ￭","￭")
        tokenized=tokenized.replace(" "," ▁")
        tokenized=tokenized.replace("￭"," ")
        tokenized=' '.join(tokenized.split()) 
        return(tokenized)

    def detokenize_sn(self,segment):
        segment=self.detokenize_s(segment)
        return(segment)        
    
def print_help():
    print("MTUOC_tokenizer_cat.py A tokenizer for Russian, usage:")
    print("Simple tokenization:")
    print('    cat "sentence to tokenize." | python3 MTUOC_tokenizer_rus.py tokenize')
    print('    python3 MTUOC_tokenizer_rus.py tokenize < file_to_tokenize > tokenized_file')
    print()
    print("Simple detokenization:")
    print('    cat "sentence to tokenize." | python3 MTUOC_tokenizer_cat.py detokenize')
    print('    python3 MTUOC_tokenizer_rus.py detokenize < file_to_detokenize > detokenized_file')
    print()
    print("Advanced options:")
    print("    tokenization/detokenization with joiner marks (￭): tokenize_j / detokenize_j")
    print("    tokenization/detokenization with joiner marks (￭) and number splitting: tokenize_jn / detokenize_jn")
    print("    tokenization/detokenization with splitter marks (▁): tokenize_s / detokenize_s")
    print("    tokenization/detokenization with splitter marks (▁) and number splitting: tokenize_sn / detokenize_sn")
        

if __name__ == "__main__":
    if len(sys.argv)>1:
        if sys.argv[1]=="-h" or sys.argv[1]=="--help":
            print_help()
            sys.exit()
        action=sys.argv[1]
    else:
        action="tokenize"
    tokenizer=Tokenizer()
    for line in sys.stdin:
        line=line.strip()
        #normalization of apostrophe
        line=line.replace("’","'")
        line=html.unescape(line)
        if action=="tokenize":
            outsegment=tokenizer.tokenize(line)
        elif action=="detokenize":
            outsegment=tokenizer.detokenize(line)
        
        elif action=="tokenize_s":
            outsegment=tokenizer.tokenize_s(line)
        elif action=="detokenize_s":
            outsegment=tokenizer.detokenize_s(line)
        elif action=="tokenize_sn":
            outsegment=tokenizer.tokenize_sn(line)
        elif action=="detokenize_sn":
            outsegment=tokenizer.detokenize_sn(line)
        
        elif action=="tokenize_j":
            outsegment=tokenizer.tokenize_j(line)
        elif action=="detokenize_j":
            outsegment=tokenizer.detokenize_j(line)
        elif action=="tokenize_jn":
            outsegment=tokenizer.tokenize_jn(line)
        elif action=="detokenize_jn":
            outsegment=tokenizer.detokenize_jn(line)
        
        print(outsegment)
        
