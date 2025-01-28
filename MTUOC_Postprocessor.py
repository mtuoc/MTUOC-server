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
    
    def has_tags(self, segment):
        response=False
        tagsA = re.findall(r'</?.+?/?>', segment)
        tagsB = re.findall(r'\{[0-9]+\}', segment)
        if len(tagsA)>0 or len(tagsB)>0:
            response=True
        return(response)
        
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
            
    
        
    def restore_tags(self,SOURCENOTAGSTOK, SOURCETAGSTOK, SELECTEDALIGNMENT, TARGETNOTAGSTOK):
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
        return(TARGETTAGS)
    
    def replace_tags(self, segment):
        equil={}
        if self.has_tags(segment):
            tagsA = re.findall(r'</?.+?/?>', segment)
            tagsB = re.findall(r'\{[0-9]+\}', segment)
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
            TARGETNOTAGSTOK=config.GetWordAlignments_tokenizerTL.tokenize(config.translation["tgt"])
            translation_tags=self.restore_tags(SOURCENOTAGSTOK, SOURCETAGSTOK, SELECTEDALIGNMENT, TARGETNOTAGSTOK)
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
