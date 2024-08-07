#    MTUOC_tags v 2402
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

import re
from collections import Counter
from bs4 import BeautifulSoup


def lreplace(pattern, sub, string):
    """
    Replaces 'pattern' in 'string' with 'sub' if 'pattern' starts 'string'.
    """
    return re.sub('^%s' % pattern, sub, string)

def rreplace(pattern, sub, string):
    """
    Replaces 'pattern' in 'string' with 'sub' if 'pattern' ends 'string'.
    """
    return re.sub('%s$' % pattern, sub, string)

class TagRestorer():
    def __init__(self):
        self.taglist=["<tag0>","<tag1>","<tag2>","<tag3>","<tag4>","<tag5>","<tag6>","<tag7>","<tag8>","<tag9>","<tag10>","</tag0>","</tag1>","</tag2>","</tag3>","</tag4>","</tag5>","</tag6>","</tag7>","</tag8>","</tag9>","</tag10>"]
        
    def has_tags(self, segment):
        response=False
        tagsA = re.findall(r'</?.+?/?>', segment)
        tagsB = re.findall(r'\{[0-9]+\}', segment)
        if len(tagsA)>0 or len(tagsB)>0:
            response=True
        return(response)
    
    def get_name(self, tag):
        name=tag.split(" ")[0].replace("<","").replace(">","").replace("/","")
        return(name)
    
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
            printLOG(3,"ERROR in MTUOC_tags addspacetags",sys.exc_info())
        return(segment)
                
        
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
    
    def remove_tags(self, segment):
        segmentnotags=re.sub('(<[^>]+>)', "",segment)
        segmentnotags=re.sub('({[0-9]+})', "",segmentnotags)
        segmentnotags=" ".join(segmentnotags.split())
        return(segmentnotags)
        
    def restore_tags_old(self,SOURCENOTAGSTOK, SOURCETAGSTOK, SELECTEDALIGNMENT, TARGETNOTAGSTOK):
        TARGETTAGLIST=TARGETNOTAGSTOK.split(" ")
        ali={}
        for a in SELECTEDALIGNMENT.split():
            (a1,a2)=a.split("-")
            a1=int(a1)
            a2=int(a2)
            ali[a1]=a2
        position=0
        tagpos={}
        posacu=0
        SOURCETAGSTOKLIST=SOURCETAGSTOK.split()
        try:
            while "▁" in SOURCETAGSTOKLIST: SOURCETAGSTOKLIST.remove("▁")
        except:
            pass
        SOURCENOTAGSTOKLIST=SOURCENOTAGSTOK.split()
        tagsposition={}
        cont=0
        acumulat=0
        for token in SOURCETAGSTOKLIST:
            if self.isSTag(token) or self.isSClosingTag(token):
                if not token in ["<s>","</s>"]:
                    tagsposition[token]=cont
                    TARGETTAGLIST.insert(cont,token)
                    acumulat+=1
            cont+=1
        targettags=" ".join(TARGETTAGLIST)
        return(targettags) 
    
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
                    segment=lreplace(starttag,"",segment)
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
                    segment=rreplace(endtag,"",segment)
                    trobat=True
                    endtags.insert(0,endtag)
                else:
                    endtag=""
            if not trobat: break
        return(segment,"".join(starttags),"".join(endtags))
        
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
                printLOG(3,"ERROR REPAIRING SPACES:".sys.exc_info())
                tlsegmentR=tlsegment
        return(tlsegment)
        
    def numerate(self,segment):
        numeratedsegment=[]
        cont=0
        for token in segment.split():
            if not token.replace("▁","").strip() in self.taglist:
                tokenmod=token+"▂"+str(cont)
                cont+=1
            else:
                tokenmod=token
            numeratedsegment.append(tokenmod)
        return(" ".join(numeratedsegment))
        
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
                
                
                
                
        return(TARGETTAGSTOKNUM) 

    def closest_value(self,input_list, input_value):
        difference = lambda input_list : abs(input_list - input_value)
        try:
            res = min(input_list, key=difference)
        except:
            res=""
        return res                             
        
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
        for n in range(0,11):
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
                pass
        #finding open tags
        for n in range(0,11):
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
                            pass
                        taglist.remove(opentag)
            except:
                pass
        #finding closing tags
        for n in range(0,11):
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
                pass
        #removing numbering     
        TARGETTAGS=[]
        for token in TARGETTAGSTOKNUM:
            TARGETTAGS.append(token.split("▂")[0])
        
        TARGETTAGS=" ".join(TARGETTAGS)   
        return(TARGETTAGS)
        
    def fix_xml_tags(self,myxml):
        if self.has_tags(myxml):
            tagsPRE=self.get_tags(myxml)
            myxml2="<fix_xml>"+myxml+"</fix_xml>"
            soup = BeautifulSoup(myxml2,'xml')
            fixed=str(soup).replace("<fix_xml>","").replace("</fix_xml>","").split("\n")[-1]
            tags=self.get_tags(fixed)
            for TP in tagsPRE:
                if not TP in tags:
                    return(myxml)
            for tag in tags:
                tag2=tag.replace('"',"'")
                if myxml.find(tag)==-1 and myxml.find(tag2)==-1:
                    fixed=fixed.replace(tag,"")
            
            if not self.remove_tags(myxml)==self.remove_tags(fixed):
                fixed=myxml
        else:
            fixed=myxml
        return(fixed)
                
                
            
        
