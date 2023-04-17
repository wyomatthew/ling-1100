import os, json

from dataclasses import dataclass, field
import sys
from typing import Optional

from EtymonlineAPI import lookup_origin, hot_list

from nltk.metrics import edit_distance

@dataclass
class LanguageTagger(object):
    lookup_path: Optional[str] = None
    _lookup_dict: dict[str, tuple[str, str]] = field(default_factory=dict)

    def __post_init__(self):
        if self.lookup_path is not None and os.path.isfile(self.lookup_path):
            with open(self.lookup_path, 'r') as fp:
                lookup_dict = json.load(fp)
        
            self._lookup_dict.update(lookup_dict)
    
    def tag_tokens(self, tokens: list[str], lookup_new: bool = True, output_progress: bool = True) -> list[Optional[str]]:
        out = list()

        i = 0
        milestones = [int(len(tokens) / 10 * i) for i in range(1, 11)]
        for tok in tokens:
            lang = None
            
            if tok in self._lookup_dict.keys() and self._lookup_dict[tok] is not None:
                lang = self._lookup_dict[tok]["language"]
            elif lookup_new:
                origin = lookup_origin(tok)
                if origin is not None:
                    self._lookup_dict[tok] = {
                        "index_word": origin[0],
                        "language": origin[1]
                    }
                    lang = origin[1]
            
            out.append(lang)
            if output_progress and i in milestones:
                print(f"{i / len(tokens) * 100:.2f}% completed...")
            i += 1
        
        return out

    def dump_dict(self, path: str):
        with open(path, 'w') as fp:
            json.dump(self._lookup_dict, fp)

if __name__ == "__main__":
    if len(sys.argv) > 1 and  os.path.isfile(sys.argv[1]):
        path = sys.argv[1]
    else:
        print()
        print(f"Could not locate file path from arguments...")
        exit(1)
    
    tagger = LanguageTagger(path)

    potential_mistakes = {word: origin for word, origin in tagger._lookup_dict.items() if origin is None or word != origin["index_word"]}
    for word, origin in sorted(potential_mistakes.items(), key=lambda tup: 0 if tup[1] is None else edit_distance(tup[0], tup[1]["index_word"]), reverse=True):
        print()
        print(word, origin)

        prompt = f"type 's' to skip, 'n' for none, 'q' to quit, otherwise provide a language of origin for {word}\n"
        user_input = input(prompt)
        if user_input.strip() == 's':
            pass
        elif user_input.strip() == 'n':
            tagger._lookup_dict[word] = None
        elif user_input.strip() == 'q':
            break
        else:
            if user_input in hot_list:
                tagger._lookup_dict[word] = {'index_word': word, "language": user_input.strip()}
            else:
                origin = lookup_origin(user_input)
                while origin is None:
                    prompt = f"No origin detected for {user_input}... 'q' to quit or try again\n"
                    user_input = input(prompt)
                    if user_input.strip() == 'q':
                        break
                    origin = lookup_origin(user_input)
                
                if user_input.strip() == 'q':
                    continue
                else:
                    tagger._lookup_dict[word] = {'index_word': origin[0], "language": origin[1]}

    tagger.dump_dict(path)
