import re
import config
import sys
from collections import Counter
import csv
from MTUOC_misc import printLOG


class Postprocessor:
    
    def __init__(self):
        self.taglist=["<tag0>","<tag1>","<tag2>","<tag3>","<tag4>","<tag5>","<tag6>","<tag7>","<tag8>","<tag9>","<tag10>","<tag11>","<tag12>","<tag13>","<tag14>","<tag15>","<tag16>","<tag17>","<tag18>","<tag19>","<tag20>","<tag21>","<tag22>","<tag23>","<tag24>","<tag25>","<tag26>","<tag27>","<tag28>","<tag29>","<tag30>","<tag31>","<tag32>","<tag33>","<tag34>","<tag35>","<tag36>","<tag37>","<tag38>","<tag39>","<tag40>","<tag41>","<tag42>","<tag43>","<tag44>","<tag45>","<tag46>","<tag47>","<tag48>","<tag49>","<tag50>","</tag0>","</tag1>","</tag2>","</tag3>","</tag4>","</tag5>","</tag6>","</tag7>","</tag8>","</tag9>","</tag10>","</tag11>","</tag12>","</tag13>","</tag14>","</tag15>","</tag16>","</tag17>","</tag18>","</tag19>","</tag20>","</tag21>","</tag22>","</tag23>","</tag24>","</tag25>","</tag26>","</tag27>","</tag28>","</tag29>","</tag30>","</tag31>","</tag32>","</tag33>","</tag34>","</tag35>","</tag36>","</tag37>","</tag38>","</tag39>","</tag40>","</tag41>","</tag42>","</tag43>","</tag44>","</tag45>","</tag46>","</tag47>","</tag48>","</tag49>","</tag50>"]
        self.changes_output=[]
        self.changes_translation=[]
        
    def set_changes_translation(self,changes):
        self.changes_translation=changes
        
    def set_changes_output(self,changes):
        self.changes_output=changes
        
    
    def lreplace(self, pattern, sub, string):
        """
        Replaces 'pattern' in 'string' with 'sub' if 'pattern' starts 'string'.
        """
        return re.sub('^%s' % pattern, sub, string)

    def rreplace(self, pattern, sub, string):
        """
        Replaces 'pattern' in 'string' with 'sub' if 'pattern' ends 'string'.
        """
        return re.sub('%s$' % pattern, sub, string)
    
    '''
    def has_tags(self, segment):
        response=False
        tagsA = re.findall(r'</?.+?/?>', segment)
        tagsB = re.findall(r'\{[0-9]+\}', segment)
        if len(tagsA)>0 or len(tagsB)>0:
            response=True
        return(response)
    '''    
    def get_tags(self, segment):
        tagsA = re.findall(r'</?.+?/?>', segment)
        tagsB = re.findall(r'\{[0-9]+\}', segment)
        tags=tagsA.copy()
        tags.extend(tagsB)
        return(tags)
        
    def get_name(self, tag):
        name=tag.split(" ")[0].replace("<","").replace(">","").replace("/","")
        return(name)
    
    def closest_value(self,input_list, input_value):
        difference = lambda input_list : abs(input_list - input_value)
        try:
            res = min(input_list, key=difference)
        except:
            res=""
        return res  
        
    def numerate(self,segment):
        numeratedsegment=[]
        cont=0
        for token in segment.split():
            tokenmod=token.replace("▁","").strip()
            condicio=tokenmod in self.taglist
            if not condicio:
                tokenmod=token+"▂"+str(cont)
                cont+=1
            else:
                tokenmod=token
            numeratedsegment.append(tokenmod)
        return(" ".join(numeratedsegment))
        
    def repairSpacesTags(self,slsegment,tlsegment,delimiters=[" ",".",",",":",";","?","!"]):
        tlsegmentR=tlsegment
        sltags=self.get_tags(slsegment)
        tltags=self.get_tags(tlsegment)
        commontags= list((Counter(sltags) & Counter(tltags)).elements())
        for tag in commontags:
            try:
                tagaux=tag
                chbfSL=slsegment[slsegment.index(tag)-1]
                chbfTL=tlsegment[tlsegment.index(tag)-1]
                tagmod=tag
                if chbfSL in delimiters and chbfTL not in delimiters:
                    tagmod=" "+tagmod
                if not chbfSL in delimiters and chbfTL in delimiters:
                    tagaux=" "+tagaux
                try:
                    chafSL=slsegment[slsegment.index(tag)+len(tag)]
                except:
                    chafSL=""
                try:
                    chafTL=tlsegment[tlsegment.index(tag)+len(tag)]
                except:
                    chafTL=""
                if chafSL in delimiters and not chafTL in delimiters:
                    tagmod=tagmod+" "
                if not chafSL in delimiters and chafTL in delimiters:
                    tagaux=tagaux+" "
                try:
                    tlsegment=tlsegment.replace(tagaux,tagmod,1)
                    tlsegment=tlsegment.replace("  "+tag," "+tag,1)
                    tlsegment=tlsegment.replace(tag+"  ",tag+" ",1)
                except:
                    pass

                
            except:
                printLOG(2,"ERROR MTUOC_Postprocessor REPAIRING SPACES:".sys.exc_info())
                tlsegmentR=tlsegment
        return(tlsegment)
        
    def insert_before(self, segment,insertposition,opentag):
        position=0
        num=-1
        for token in segment:
            if token.find("▂")>-1:
                parts=token.split("▂")
                try:
                    num=int(parts[-1])
                except:
                    num=-1
            if num==insertposition:
                segment.insert(position,opentag)
                break
            position+=1
        return(segment)
        
    def insert_after(self, segment,insertposition,opentag):
        position=0
        num=-1
        for token in segment:
            if token.find("▂")>-1:
                parts=token.split("▂")
                try:
                    num=int(parts[-1])
                except:
                    num=-1
            if num==insertposition:
                segment.insert(position+1,opentag)
                break
            position+=1
        return(segment)
        
    def retrieve_indexes(self, segment):
        indexes=[]
        for token in segment.split():            
            if token.find("▂")>-1:
                parts=token.split("▂")
                try:
                    index=int(parts[-1])
                    indexes.append(index)
                except:
                    pass
        if len(indexes)==0:
            min_value=0
            max_value=0
        else:
            min_value=min(indexes)
            max_value=max(indexes)
        return(min_value,max_value)
        
    def insert_opentag(self, TARGETTAGSTOKNUM, position, opentag):
        alreadydone=[]
        position2=0
        num=-1
        for token in TARGETTAGSTOKNUM:
            if token.find("▂")>-1:
                parts=token.split("▂")
                try:
                    num=int(parts[-1])
                except:
                    num=-1
                position2+=1
            if num==position and not opentag in alreadydone:
                insertposition=position
                if insertposition<0: insertposition=0
                TARGETTAGSTOKNUM=self.insert_before(TARGETTAGSTOKNUM,insertposition,opentag)
                alreadydone.append(opentag)
        return(TARGETTAGSTOKNUM)
        
    def insert_closingtag(self, TARGETTAGSTOKNUM, position, closingtag):
        alreadydone=[]
        position2=0
        num=-1
        for token in TARGETTAGSTOKNUM:
            if token.find("▂")>-1:
                parts=token.split("▂")
                try:
                    num=int(parts[-1])
                except:
                    num=-1
                position2+=1
            if num==position and not closingtag in alreadydone:
                insertposition=position
                if insertposition<0: insertposition=0
                TARGETTAGSTOKNUM=self.insert_after(TARGETTAGSTOKNUM,insertposition,closingtag)
                alreadydone.append(closingtag)
        return(TARGETTAGSTOKNUM)
        
    def insert_open_close(self, TARGETTAGSTOKNUM,opentag,closetag,minpos,maxpos):
        position=0 
        num=-1
        opendone=False
        closedone=False
        for token in TARGETTAGSTOKNUM:
            if token.find("▂")>-1:
                parts=token.split("▂")
                try:
                    num=int(parts[-1])
                except:
                    num=-1
            if num==minpos and not opendone:
                TARGETTAGSTOKNUM.insert(position,opentag)
                opendone=True
            elif num==maxpos and not closedone:
                TARGETTAGSTOKNUM.insert(position+1,closetag)
                closedone=True
            position+=1
        return(TARGETTAGSTOKNUM) 
        
    
            
    def is_opening_tag(self,tag):
        if tag.startswith("<") and tag.endswith(">"):
            tag_name = tag[1:-1].split()[0]  # Extracting the tag name from the tag
            return not tag_name.startswith("/")
        else:
            return False
    
    def is_closing_tag(self,tag):
        if tag.startswith("</") and tag.endswith(">"):
            tag_name = tag[2:-1].split()[0]  # Extracting the tag name from the closing tag
            return True
        else:
            return False 
    def create_closing_tag(self,opening_tag):
        if opening_tag.startswith("<") and opening_tag.endswith(">"):
            tag_name = opening_tag[1:-1].split()[0]  # Extracting the tag name from the opening tag
            closing_tag = f"</{tag_name}>"
            return closing_tag
        else:
            raise ValueError("Invalid opening tag format")
    
    def create_starting_tag(self,closing_tag):
        if closing_tag.startswith("</") and closing_tag.endswith(">"):
            tag_name = closing_tag[2:-1].split()[0]  # Extracting the tag name from the closing tag
            starting_tag = f"<{tag_name}>"
            return starting_tag
        else:
            raise ValueError("Invalid closing tag format")
            
    def align_spacing(self, string1: str, string2: str) -> str:
        """
        Ajusta els espais al voltant dels caràcters de puntuació en 'string2'
        perquè siguin idèntics als de 'string1'.

        La funció assumeix que la seqüència de caràcters de puntuació
        és la mateixa en ambdós strings.

        Args:
            string1: L'string de referència amb l'espaiat correcte.
            string2: L'string que es vol modificar.

        Returns:
            Un nou string basat en 'string2' amb l'espaiat corregit.
            Si la seqüència de puntuació no coincideix, retorna 'string2' original.
        """
        # --- LÍNIES CORREGIDES ---
        # Defineix els caràcters de puntuació com un string simple.
        PUNCTUATION = ".,:;(){}[]!¿?«»'\"‘’’“”"
        
        # Per crear una expressió regular de tipus "set" ([...]) de forma segura,
        # el caràcter ']' ha de ser el primer de la llista per ser interpretat literalment.
        safe_punc_for_set = ']' + PUNCTUATION.replace(']', '')
        
        # Construeix l'expressió regular final: un grup de captura () que conté un set [].
        PUNCTUATION_REGEX = f"([{safe_punc_for_set}])"
        # --- FI DE LA CORRECCIÓ ---

        # 1. Divideix els strings en text i caràcters de puntuació.
        tokens1 = re.split(PUNCTUATION_REGEX, string1)
        tokens2 = re.split(PUNCTUATION_REGEX, string2)

        # 2. Comprova si la seqüència de puntuació és la mateixa.
        # Els signes de puntuació es troben a les posicions senars de la llista.
        punc_sequence1 = tokens1[1::2]
        punc_sequence2 = tokens2[1::2]

        if punc_sequence1 != punc_sequence2:
            print("Atenció: La seqüència de signes de puntuació no coincideix. "
                  "No es pot realitzar l'ajust.")
            return string2

        # 3. Reconstrueix el string2 amb l'espaiat de string1.
        new_tokens = []
        for i, token in enumerate(tokens2):
            # Si el token és un signe de puntuació, s'afegeix directament.
            if i % 2 == 1:
                new_tokens.append(token)
                continue

            # Si és un fragment de text, s'ajusta l'espaiat.
            current_text = token

            # Ajusta l'espai al final del text (abans del següent signe).
            if i < len(tokens1) - 1:
                text_from_s1 = tokens1[i]
                has_space_in_s1 = text_from_s1.endswith(' ')
                
                if has_space_in_s1 and not current_text.endswith(' '):
                    current_text += ' '
                elif not has_space_in_s1 and current_text.endswith(' '):
                    current_text = current_text.rstrip(' ')

            # Ajusta l'espai al principi del text (després del signe anterior).
            if i > 0:
                text_from_s1 = tokens1[i]
                has_space_in_s1 = text_from_s1.startswith(' ')

                if has_space_in_s1 and not current_text.startswith(' '):
                    current_text = ' ' + current_text
                elif not has_space_in_s1 and current_text.startswith(' '):
                    current_text = current_text.lstrip(' ')
            
            new_tokens.append(current_text)
        return "".join(new_tokens)    
        
    def restore_tags(self,SOURCENOTAGSTOK, SOURCETAGSTOK, SELECTEDALIGNMENT, TARGETNOTAGS, TARGETNOTAGSTOK):
        SOURCETAGSTOK=SOURCETAGSTOK.replace(" ▁ "," ")
        if TARGETNOTAGSTOK.startswith("<s>") and not SOURCENOTAGSTOK.startswith("<s>"):
            SOURCENOTAGSTOK="<s> "+SOURCENOTAGSTOK
        ali={}
        nmax=0
        nmin=100000
        mmax=0
        mmin=100000
        for a in SELECTEDALIGNMENT.split():
            (a1,a2)=a.split("-")
            a1=int(a1)
            a2=int(a2)
            
            if not a1 in ali: ####AFEGIT AIXÒ
                ali[a1]=a2
            if a1>nmax: nmax=a1
            if a1<nmin: nmin=a1
            if a2>mmax: mmax=a2
            if a2<mmin: mmin=a2
        #chek is all alignments exists
        nonexisting=[]
        for i in range(nmin,nmax):
            try:
                b=ali[i]
            except:
                nonexisting.append(i)
        inv_ali = {v: k for k, v in ali.items()}
        inv_nonexisting=[]
        for i in range(mmin,mmax):
            try:
                b=inv_ali[i]
            except:
                inv_nonexisting.append(i)
        for ne in nonexisting:
            closest=self.closest_value(inv_nonexisting,ne)
            ali[ne]=closest
        SOURCENOTAGSTOKNUM=self.numerate(SOURCENOTAGSTOK)
        SOURCETAGSTOKNUM=self.numerate(SOURCETAGSTOK)
        TARGETNOTAGSTOKNUM=self.numerate(TARGETNOTAGSTOK)
        TARGETTAGSTOKNUM=TARGETNOTAGSTOKNUM.split(" ")
        taglist=self.taglist.copy()
        #finding open-close pairs
        for n in range(0,51):
            try:
                opentag="<tag"+str(n)+">"
                closetag="</tag"+str(n)+">"
                regexp=opentag+"(.*?)"+closetag
                trobat=re.findall(regexp, SOURCETAGSTOKNUM, re.DOTALL)
                if len(trobat)>0 and opentag in taglist and closetag in taglist:
                    (minpos,maxpos)=self.retrieve_indexes(trobat[0])
                    postrad=[]
                    postrad.append(ali[minpos])
                    postrad.append(ali[maxpos])
                    minpostrad=min(postrad)
                    maxpostrad=max(postrad)
                    TARGETTAGSTOKNUM=self.insert_open_close(TARGETTAGSTOKNUM,opentag,closetag,minpostrad,maxpostrad)
                    taglist.remove(opentag)
                    taglist.remove(closetag)
            except:
                printLOG(2,"MTUOC_Postprocessor restore_tags:",sys.exc_info())
        #finding open tags
        for n in range(0,51):
            try:
                opentag="<tag"+str(n)+">"
                regexp=opentag+" [^\s]+"
                trobat=re.findall(regexp, SOURCETAGSTOKNUM, re.DOTALL)
                if len(trobat)>0 and opentag in taglist:
                    posttoken=trobat[0].replace(opentag,"").strip()
                    try:
                        #postnum=int(posttoken.split("▂")[1])
                        postnum=int(posttoken.split("▂")[-1])
                    except:
                        postnum=None
                    if not postnum==None and opentag in taglist:
                        try:
                            TARGETTAGSTOKNUM=self.insert_opentag(TARGETTAGSTOKNUM, ali[postnum], opentag)
                        except:
                            printLOG(2,"ERROR MTUOC_Postprocessor restore_tags:",sys.exc_info())
                        taglist.remove(opentag)
            except:
                printLOG(2,"ERROR MTUOC:Postprocessor restore_tags:",sys.exc_info())
        #finding closing tags
        for n in range(0,51):
            try:
                closingtag="</tag"+str(n)+">"
                regexp="[^\s]+ "+closingtag
                trobat=re.findall(regexp, SOURCETAGSTOKNUM, re.DOTALL)
                if len(trobat)>0 and closingtag in taglist:
                    pretoken=trobat[0].replace(closingtag,"").strip()
                    try:
                        prenum=int(pretoken.split("▂")[1])
                    except:
                        prenum=None
                    if not prenum==None and closingtag in taglist:
                        TARGETTAGSTOKNUM=self.insert_closingtag(TARGETTAGSTOKNUM, ali[prenum], closingtag)
                        taglist.remove(closingtag)
            except:
                printLOG(2,"ERROR MTUOC_Postprocessor restore_tags:",sys.exc_info())
        #removing numbering     
        TARGETTAGS=[]
        for token in TARGETTAGSTOKNUM:
            TARGETTAGS.append(token.split("▂")[0])
        TARGETTAGS=" ".join(TARGETTAGS)
        TARGETTAGS=self.align_spacing(TARGETNOTAGS,TARGETTAGS)
        return(TARGETTAGS)
        
    def has_tags(self, segment):
        # Assumiré una implementació bàsica per a l'exemple
        return bool(re.search(r'</?.+?/?>|\{[0-9]+\}', segment))
    '''
    def replace_tags(self, segment):
        """
        Reemplaça grups de tags consecutius (HTML o placeholders) per un
        únic tag genèric i retorna el segment modificat i un diccionari
        amb les equivalències.
        
        Per exemple: '<a><b>{0}' es converteix en '<tag0>'
        """
        equil = {}
        counter = [0]

        def replacer(match):
            original_tags_group = match.group(0)
            new_tag = f"<tag{counter[0]}>"
            equil[new_tag] = original_tags_group
            counter[0] += 1
            return new_tag

        if not self.has_tags(segment):
            return segment, equil

        # --- LÍNIA CORREGIDA ---
        # Hem canviat les cometes simples externes ' per cometes dobles "
        html_tag_pattern = r"</?[\w\s='/.:-]+?>"
        placeholder_pattern = r'\{[0-9]+\}'
        
        consecutive_tags_regex = re.compile(f'((?:{html_tag_pattern}|{placeholder_pattern})+)')
        
        modified_segment = consecutive_tags_regex.sub(replacer, segment)

        return modified_segment, equil
    '''
    def get_tag_info(self, tag_string):
        """
        Analitza un string de tag i retorna el seu nom i tipus.
        Exemples:
        - '<p class="important">' -> ('p', 'open')
        - '</p>'                 -> ('p', 'close')
        - '<br/>'                -> ('br', 'self-closing')
        - '{0}'                  -> ('{0}', 'placeholder')
        """
        if tag_string.startswith('{') and tag_string.endswith('}'):
            return tag_string, 'placeholder'
        
        if tag_string.startswith('</'):
            match = re.match(r'</([a-zA-Z0-9]+)', tag_string)
            return (match.group(1), 'close') if match else (None, None)
        
        if tag_string.endswith('/>'):
            match = re.match(r'<([a-zA-Z0-9]+)', tag_string)
            return (match.group(1), 'self-closing') if match else (None, None)
        
        if tag_string.startswith('<'):
            match = re.match(r'<([a-zA-Z0-9]+)', tag_string)
            return (match.group(1), 'open') if match else (None, None)
            
        return None, None

    def replace_tags(self, segment):
        """
        Reemplaça tags de manera intel·ligent, aparellant obertures i tancaments.
        Utilitza una pila (stack) per recordar els tags oberts.
        """
        if not self.has_tags(segment):
            return segment, {}

        equil = {}
        tag_stack = []  # Pila per guardar els tags oberts i els seus números
        new_string_parts = []
        counter = 0
        last_pos = 0
        ###ADHOC EP <tag>n<tag>
        ep_pattern=r"<[A-Z0-9]+>\s*n\s*<[A-Z0-9]+>"
        ep_pattern2=r"<[A-Z0-9]+>\s*n\s+"

        # Patró per trobar QUALSEVOL tag individual
        html_tag_pattern = r"</?[\w\s='/.:-]+?>"
        placeholder_pattern = r'\{[0-9]+\}'
        single_tag_pattern = f"({ep_pattern}|{ep_pattern2}|{html_tag_pattern}|{placeholder_pattern})"
        
        for match in re.finditer(single_tag_pattern, segment):
            # 1. Afegeix el text pla que hi ha entre l'últim tag i l'actual
            new_string_parts.append(segment[last_pos:match.start()])
            
            original_tag = match.group(0)
            tag_name, tag_type = self.get_tag_info(original_tag)
            
            new_tag = original_tag # Per si no podem processar-lo

            if tag_type == 'open':
                new_tag = f"<tag{counter}>"
                tag_stack.append((tag_name, counter))
                counter += 1
            elif tag_type == 'self-closing' or tag_type == 'placeholder':
                new_tag = f"<tag{counter}>"
                # O f"<tag{counter}/>" si vols mantenir la forma autotancada
                counter += 1
            elif tag_type == 'close':
                # Busca a la pila el tag d'obertura corresponent
                if tag_stack and tag_stack[-1][0] == tag_name:
                    # Trobada correspondència, utilitzem el mateix número
                    _name, number = tag_stack.pop()
                    new_tag = f"</tag{number}>"
                else:
                    # Tag de tancament sense obertura, el tractem com un tag simple
                    new_tag = f"<tag{counter}>"
                    counter += 1
            
            new_string_parts.append(new_tag)
            equil[new_tag] = original_tag
            last_pos = match.end()

        # 2. Afegeix la resta del text després de l'últim tag
        new_string_parts.append(segment[last_pos:])
        
        final_segment = "".join(new_string_parts)
        return final_segment, equil
    '''
    def replace_tags(self, segment):
        equil={}
        if self.has_tags(segment):
            tagsA = re.findall(r'</?.+?/?>+', segment)
            tagsB = re.findall(r'\{[0-9]+\}+', segment)
            tags=tagsA.copy()
            tags.extend(tagsB)
            conttag=0
            for tag in tags:
                if tag.find("</")>-1:
                    tagrep="</tag"+str(conttag)+">"
                else:
                    tagrep="<tag"+str(conttag)+">"
                segment=segment.replace(tag,tagrep,1)
                equil[tagrep]=tag
                if tag in tagsA:
                    tagclose="</"+self.get_name(tag)+">"
                    tagcloserep="</tag"+str(conttag)+">"
                    if segment.find(tagclose)>-1:
                        segment=segment.replace(tagclose,tagcloserep,1)
                        equil[tagcloserep]=tagclose
                        tags.remove(tagclose)
                conttag+=1
                
            return(segment,equil)
            
        else:
            return(segment,equil)
    
    '''
    def remove_start_end_tag(self, segment):
        alltags=self.get_tags(segment)
        starttags=[]
        endtags=[]
        while 1:
            trobat=False
            try:
                starttag=re.match("(</?tag[0-9]+>)",segment)
                starttag=starttag.group()
            except:            
                starttag=""
            try:
                endtag=re.search("(</?tag[0-9]+>)$",segment)
                endtag=endtag.group()
            except:
                endtag=""
            
            if starttag:
                todelete=False
                alltagsmod=alltags
                try:
                    alltagsmod.remove(endtag)
                except:
                    pass
                if self.is_opening_tag(starttag) and self.create_closing_tag(starttag)==endtag:
                    todelete=True
                if self.is_opening_tag(starttag) and not self.create_closing_tag(starttag) in alltagsmod:
                    todelete=True
                if self.is_closing_tag(starttag):
                    todelete=True
                
                if todelete:
                    segment=self.lreplace(starttag,"",segment)
                    starttags.append(starttag)
                    trobat=True
                else:
                    starttag=""
            if endtag:
                todelete=False
                alltagsmod=alltags
                if self.is_closing_tag(endtag) and self.create_starting_tag(endtag)==starttag:
                    todelete=True
                if self.is_closing_tag(endtag) and not self.create_starting_tag(endtag) in alltagsmod:
                    todelete=True
                if self.is_opening_tag(endtag):
                    todelete=True
                if todelete:
                    segment=self.rreplace(endtag,"",segment)
                    trobat=True
                    endtags.insert(0,endtag)
                else:
                    endtag=""
            if not trobat: break
        return(segment,"".join(starttags),"".join(endtags))
            
    def insert_tags(self):
        
        try:
            
            (segmentTAGSMOD,TAGSEQUIL)=self.replace_tags(config.src)
            (segmentNOTIF,STARTINGTAG,CLOSINGTAG)=self.remove_start_end_tag(segmentTAGSMOD)
            SOURCENOTAGSTOK=config.translation["src_tokens"]
            SOURCETAGSTOK=config.GetWordAlignments_tokenizerSL.tokenize(segmentNOTIF)
            SELECTEDALIGNMENT=config.translation["alignment"]
            TARGETNOTAGS=config.translation["tgt"]
            TARGETNOTAGSTOK=config.GetWordAlignments_tokenizerTL.tokenize(config.translation["tgt"])
            translation_tags=self.restore_tags(SOURCENOTAGSTOK, SOURCETAGSTOK, SELECTEDALIGNMENT, TARGETNOTAGS, TARGETNOTAGSTOK)
            
            translation_tags=STARTINGTAG+" "+translation_tags+" "+CLOSINGTAG
            
            
            srcEQUILTAGS=config.src
            for t in TAGSEQUIL:
                srcEQUILTAGS=srcEQUILTAGS.replace(TAGSEQUIL[t],t,1)
            translation_tags=self.repairSpacesTags(srcEQUILTAGS,translation_tags) #
            for t in TAGSEQUIL:
                try:
                    translation_tags=translation_tags.replace(t,TAGSEQUIL[t],1)
                except:
                    printLOG(2,"ERROR in MTUOC_Postprocessor insert tags:",sys.exc_info())
            config.translation["tgt"]=translation_tags
            config.translation["tgt"]=config.GetWordAlignments_tokenizerTL.detokenize(config.translation["tgt"])
            config.translation["tgt"]=self.align_spacing(TARGETNOTAGS,config.translation["tgt"])
                    
            
        except:
            printLOG(2,"Error MTUOC_Postprocessor insert tags",sys.exc_info())
            
    def change_output(self, translation):
        for change in self.changes_output:
            tofind=change[0]
            tochange=change[1]
            regexp="\\b"+tofind+"\\b"
            trobat=re.findall(regexp,translation['tgt'])
            if trobat: 
                translation['tgt']=re.sub(regexp, tochange, translation['tgt'])
            for i in range(0,len(translation["alternate_translations"])):
                trobat=re.findall(regexp,translation["alternate_translations"][i]['tgt'])
                if trobat: 
                    translation["alternate_translations"][i]['tgt']=re.sub(regexp, tochange, translation["alternate_translations"][i]['tgt'])
        return(translation)
        
    def change_translation(self, translation):
        for change in self.changes_translation:
            try:
                tofindSOURCE=change[0]
                tofindTARGET=change[1]
                tochange=change[2]
                regexpSOURCE="\\b"+tofindSOURCE+"\\b"
                regexpTARGET="\\b"+tofindTARGET+"\\b"
                trobatSOURCE=re.findall(regexpSOURCE,translation['src'])
                trobatTARGET=re.findall(regexpTARGET,translation['tgt'])
                if trobatSOURCE and trobatTARGET: 
                    translation['tgt']=re.sub(regexpTARGET, tochange, translation['tgt'])
                    #trobat=re.findall(regexp,translation["alternate_translations"][i]['tgt'])
                
                if trobatSOURCE:
                    for i in range(0,len(translation["alternate_translations"])):
                        trobatTARGET=re.findall(regexpTARGET,translation["alternate_translations"][i]['tgt'])
                        if trobatTARGET: 
                            translation["alternate_translations"][i]['tgt']=re.sub(regexpTARGET, tochange, translation["alternate_translations"][i]['tgt'])

            except:
                printLOG(2,"ERROR MTUOC_Postprocessor change translation:",sys.exc_info())
        return(translation)
        
    def escape_html(self,text):
        # This dictionary provides a mapping of Unicode code points to HTML entities
        codepoint_to_entity = {v: f"&{k};" for k, v in html.entities.codepoint2name.items()}
        
        def replace_with_entity(match):
            char = match.group(0)
            if ord(char) in codepoint_to_entity:
                return codepoint_to_entity[ord(char)]
            return char
        
        # Use regex to find any non-ASCII characters and replace them with their HTML entities
        return re.sub(r'[^\x00-\x7F]', replace_with_entity, text)
            
    def normalize_number(self, num_str):
        """
        Normalizes a number by removing ',' and '.' to make the comparison culture-agnostic.
        """
        return re.sub(r'[,.]', '', num_str)

    def check_and_replace_numeric(self, source, target):
        # Define a regex pattern to find numbers (including decimals and commas)
        number_pattern = r'[-+]?\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d+)?'
        
        # Find all numeric expressions in the source and target
        source_numbers = re.findall(number_pattern, source)
        target_numbers = re.findall(number_pattern, target)
        
        # If there are no numbers in the source, remove any numbers in the target
        if not source_numbers:
            target = re.sub(number_pattern, '', target).strip()
            return target

        # Replace incorrect numbers in the target
        for i, source_num in enumerate(source_numbers):
            if i < len(target_numbers):
                # Normalize both numbers (remove ',' and '.' for comparison)
                normalized_source_num = self.normalize_number(source_num)
                normalized_target_num = self.normalize_number(target_numbers[i])

                # If the numbers don't match after normalization, replace the target number with the source number
                if normalized_source_num != normalized_target_num:
                    target = re.sub(re.escape(target_numbers[i]), source_num, target, count=1)
            else:
                # If the source has more numbers than the target, append the missing number
                target += f" {source_num}"

        # Remove any extra numbers in the target that are not in the source
        for i in range(len(source_numbers), len(target_numbers)):
            target = re.sub(re.escape(target_numbers[i]), '', target, count=1).strip()

        # Remove any unnecessary extra spaces
        target = re.sub(r'\s+', ' ', target)
        
        return target
