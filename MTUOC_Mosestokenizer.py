from sacremoses import MosesTokenizer, MosesDetokenizer
import sys
import re


class Tokenizer():
    def __init__(self,lang):
        self.lang=lang
        self.tokenizer=MosesTokenizer(lang=lang)
        self.detokenizer=MosesDetokenizer(lang=lang)
        self.protected_patterns=[r'<[^>]+>']

        
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
            pass
        return(segment)
        
    def tokenize(self,segment):
        if self.has_tags(segment):
            segment=self.addspacetags(segment)
        segmenttok=" ".join(self.tokenizer.tokenize(segment,escape=False,protected_patterns=self.protected_patterns))
        return(segmenttok)
        
    def detokenize(self,segment):
        segmentdetok=self.detokenizer.detokenize(segment.split())
        return(segmentdetok)
        
                    
    


def print_help():
    print("MTUOC_Mosestokenizer.py A tokenizer for using Moses, usage:")
    print("Tokenization:")
    print("   python3 MTUOC_Mosestokenizer.py en < text.txt")
    print("   cat text.txt | python3 MTUOC_Mosestokenizer.py en")
    print("Deokenization:")
    print("   python3 MTUOC_Mosestokenizer.py en detokenize < text.txt")
    print("   cat text.txt | python3 MTUOC_Mosestokenizer.py en detokenize")
    
        

if __name__ == "__main__":
    if len(sys.argv)<2:
        print_help()
        sys.exit()
    elif sys.argv[1]=="-h" or sys.argv[1]=="--help":
            print_help()
            sys.exit()
        
    else:
        lang=sys.argv[1]
        if len(sys.argv)==2: action="tokenize"
        elif sys.argv[2]=="tokenize": action="tokenize"
        elif sys.argv[2]=="detokenize": action="detokenize"
        tokenizer=Tokenizer(lang)
        if action=="tokenize":
            for line in sys.stdin:
                line=line.rstrip()
                outsegment=tokenizer.tokenize(line)
                print(outsegment)

        elif action=="detokenize":
            for line in sys.stdin:
                line=line.rstrip()
                outsegment=tokenizer.detokenize(line.split())
                print(outsegment)


