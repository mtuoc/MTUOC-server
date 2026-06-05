import spacy
import sys
import html
import argparse
from spacy.util import is_package

class SpacyMTUOCTokenizer:
    def __init__(self, model_name):
        """
        Initializes the tokenizer.
        :param model_name: Name of the spaCy model or language code (e.g., 'ca_core_news_sm' or 'is').
        """
        self.model_name = model_name
        self.joiner = "￭"
        self.splitter = "▁"
        self.nlp = self._load_or_download_model(model_name)

    def _load_or_download_model(self, model_name):
        """
        Smart loading:
        1. Try to load as a full package.
        2. If missing and is a model name, download and load.
        3. If it fails, try to initialize as a blank language (e.g., 'is').
        """
        # 1. Direct load attempt
        if is_package(model_name):
            try:
                return spacy.load(model_name, disable=["parser", "ner", "lemmatizer"])
            except Exception:
                pass

        # 2. If it's a full model name (like en_core_web_sm), try to download it
        if "_" in model_name:
            print(f"Model '{model_name}' not found. Downloading...", file=sys.stderr)
            try:
                spacy.cli.download(model_name)
                return spacy.load(model_name, disable=["parser", "ner", "lemmatizer"])
            except Exception as e:
                print(f"Download failed for '{model_name}': {e}", file=sys.stderr)

        # 3. Fallback to blank language model (e.g., 'is', 'ca', 'en')
        try:
            print(f"Initializing blank language model for '{model_name}'...", file=sys.stderr)
            return spacy.blank(model_name)
        except Exception:
            print(f"Error: '{model_name}' is not a valid model or language code.", file=sys.stderr)
            sys.exit(1)

    def tokenize(self, text, mode="tokenize"):
        doc = self.nlp(text)
        
        if mode == "tokenize":
            return " ".join([t.text for t in doc])
        
        elif mode == "tokenize_j":
            tokens = []
            for i, token in enumerate(doc):
                t_text = token.text
                if not token.whitespace_ and i < len(doc) - 1:
                    t_text += self.joiner
                tokens.append(t_text)
            return " ".join(tokens).replace(self.joiner + " ", self.joiner)

        elif mode == "tokenize_s":
            res = []
            for token in doc:
                res.append(token.text)
                if token.whitespace_:
                    res.append(self.splitter)
            return " ".join(res).strip()
            
        return text

    def detokenize_j(self, text):
        return text.replace(self.joiner + " ", "").replace(self.joiner, "").strip()

def main():
    parser = argparse.ArgumentParser(description="MTUOC Tokenizer wrapper for spaCy.")
    parser.add_argument("action", nargs="?", default="tokenize",
                        choices=["tokenize", "tokenize_j", "tokenize_s", "detokenize_j"],
                        help="Action to perform (default: %(default)s).")
    parser.add_argument("-m", "--model", required=True,
                        help="spaCy model (ca_core_news_sm) or language code (is, ca, en).")

    args = parser.parse_args()
    tokenizer = SpacyMTUOCTokenizer(args.model)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            print("")
            continue
        line = html.unescape(line).replace("’", "'")
        if args.action.startswith("tokenize"):
            print(tokenizer.tokenize(line, mode=args.action))
        elif args.action == "detokenize_j":
            print(tokenizer.detokenize_j(line))

if __name__ == "__main__":
    main()
