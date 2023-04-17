import os, string
from dataclasses import dataclass

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

@dataclass()
class DocProcessor(object):
    path: str

    def read(self) -> str:
        with open(self.path, 'r') as fp:
            return fp.read().encode().decode("ascii", errors="ignore")
        
    def tokenize(self, lower: bool = False, rm_punct: bool = False, rm_stop_words: bool = False, rm_numbers: bool = False, stem: bool = False) -> list[str]:
        toks = word_tokenize(self.read())

        if rm_numbers:
            toks = filter(lambda tok: not tok.isnumeric(), toks)
        if lower:
            toks = [tok.lower() for tok in toks]
        if rm_punct:
            punctuation = set(string.punctuation)
            for mark in punctuation:
                toks = [tok.replace(mark, "") for tok in toks]
            toks = list(filter(lambda tok: tok not in punctuation and len(tok) > 0, toks))
        if rm_stop_words:
            stop_words = set(stopwords.words('english'))
            toks = list(filter(lambda tok: tok not in stop_words, toks))
        if stem:
            lemma = WordNetLemmatizer()
            toks = [lemma.lemmatize(tok) for tok in toks]
            pass

        return toks

if __name__ == "__main__":
    test_path = "corpus/the_outsiders.txt"
    doc = DocProcessor(test_path)
    print(doc.tokenize(True, True, True, True))
    pass
