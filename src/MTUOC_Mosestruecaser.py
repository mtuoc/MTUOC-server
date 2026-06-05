from sacremoses import MosesTruecaser, MosesDetruecaser
from collections import defaultdict
import re

class Truecaser():
    def __init__(self):
        self.tc_model=None
        self.mtr=MosesTruecaser()
        self.mdtr=MosesDetruecaser()
        self.training_corpus=None
        self.possiblyUseFirstToken=True
        
    def set_tc_model(self, model):
        self.tc_model=model
    
    def set_training_corpus(self, training_corpus):
        self.training_corpus=training_corpus
        
    def load_tc_model(self,model):
        self.mtr = MosesTruecaser(model)
        
    def set_possiblyUseFirstToken(self,possiblyUseFirstToken):
        self.possiblyUseFirstToken=possiblyUseFirstToken
        
    def split_xml(self,line):
        words = []
        markup = []
        markup_segment = ""
        
        while line.strip():
            # XML tag
            match = re.match(r'^\s*(<\S[^>]*>)(.*)$', line)
            if match:
                markup_segment += match.group(1) + " "
                line = match.group(2)
            # non-XML text
            elif re.match(r'^\s*([^\s<>]+)(.*)$', line):
                word_match = re.match(r'^\s*([^\s<>]+)(.*)$', line)
                words.append(word_match.group(1))
                markup.append(markup_segment)
                markup_segment = ""
                line = word_match.group(2)
            # '<' or '>' occurs in word, but it's not an XML tag
            else:
                other_match = re.match(r'^\s*(\S+)(.*)$', line)
                words.append(other_match.group(1))
                markup.append(markup_segment)
                markup_segment = ""
                line = other_match.group(2)
        
        markup.append(markup_segment.rstrip())
        return words, markup
        
    def train(self):
        CASING = defaultdict(lambda: defaultdict(float))
        SENTENCE_END = {".": 1, ":": 1, "?": 1, "!": 1}
        DELAYED_SENTENCE_START = {"(": 1, "[": 1, "\"": 1, "'": 1, "&apos;": 1, "&quot;": 1, "&#91;": 1, "&#93;": 1}

        # Open the corpus file
        with open(self.training_corpus, 'r', encoding='utf-8') as corpus_file:
            for line in corpus_file:
                line = line.strip()
                words, markup = self.split_xml(line)
                
                # Skip delayed sentence start tokens
                start = 0
                while start < len(words) and words[start] in DELAYED_SENTENCE_START:
                    start += 1
                
                first_word_of_sentence = True
                for i in range(start, len(words)):
                    current_word = words[i]

                    # Check if the word ends the previous sentence
                    if not first_word_of_sentence and words[i - 1] in SENTENCE_END:
                        first_word_of_sentence = True
                    
                    # Skip words with no letters to case
                    if not re.search(r'[a-zA-Z]', current_word):
                        first_word_of_sentence = False
                        continue
                    
                    current_word_weight = 0
                    if not first_word_of_sentence:
                        current_word_weight = 1
                    elif self.possiblyUseFirstToken:
                        first_char = current_word[0]
                        # If the first character is lowercase, count it as full evidence
                        if first_char.lower() == first_char:
                            current_word_weight = 1
                        # If it's the only token, count it as partial evidence (10%)
                        elif len(words) == 1:
                            current_word_weight = 0.1
                    
                    if current_word_weight > 0:
                        # Update casing frequencies
                        lowercase_word = current_word.lower()
                        CASING[lowercase_word][current_word] += current_word_weight
                    
                    first_word_of_sentence = False

        # Save the recaser model
        with open(self.tc_model, 'w', encoding='utf-8') as model_file:
            for lowercase_word, casings in CASING.items():
                best_word = max(casings, key=casings.get)
                best_score = casings[best_word]
                total = sum(casings.values())

                model_file.write(f"{best_word} ({int(best_score)}/{int(total)})")
                
                # Write alternate casings
                for word, score in casings.items():
                    if word != best_word:
                        scoreINT=int(score)
                        model_file.write(f" {word} ({scoreINT})")
                model_file.write("\n")
        
    def truecase(self,sentence):
        truecased=" ".join(self.mtr.truecase(sentence))
        return(truecased)
        
    def detruecase(self,truecased):
        detruecased=" ".join(self.mdtr.detruecase(truecased))
        return(detruecased)
