import re
import time
from re import match
from typing import Optional
from functools import lru_cache

import bs4
import requests as r
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize

BASE_URL = "https://www.etymonline.com"
hot_list = ["french", "latin", "german", "english"]

def make_request(url: str, params: dict = None, headers: dict = None) -> r.Response:
    """Makes a request.
    
    Returns
    -------
    Response
        request object
        
    Throws
    ------
    ConnectionError
        On any non-ok response code"""
    res = r.get(url, params=params, headers=headers)
    with open("out.html", "w") as fp:
        fp.write(res.text)
    if not res.ok:
        raise ConnectionError(f"Failed to reach {url}, received {res.status_code} : {res.reason}\n{res.text}")

    return res

def tokenize(text: str, skip_punctuation: bool = True) -> list[str]:
    tokens = word_tokenize(text)
    if skip_punctuation:
        tokens = filter(lambda word: match(r"\w+", word) is not None, tokens)

    return list(tokens)

def get_etymonline_description(word: str) -> str:
    res = make_request(BASE_URL + f"/word/{word}")
    soup = BeautifulSoup(res.text, features="html.parser")

    etymology_text = soup.body.find("section").p.get_text()
    return etymology_text

def get_etymonline_search(word: str) -> list[str]:
    url = f"{BASE_URL}/search"
    res = make_request(url, params={"q": word})

    soup = BeautifulSoup(res.text, features="html.parser")
    return [tag.get_text() for tag in soup.find_all("section")]

def find_language(words: list[str]) -> Optional[str]:
    for word in words:
        for hot_word in hot_list:
            if hot_word in word:
                return word
    
    return None

def lookup_origin(word: str) -> Optional[str]:
    etymology_texts = get_etymonline_search(word)
    for text in etymology_texts:
        text = text.lower()
        tokens = word_tokenize(text)
        words = list(filter(lambda word: match(r"\w+", word) is not None, tokens))

        language = find_language(words)
        if language is not None:
            return language
    
    return None

def add_prefix_to_lookup(out: dict[str, list[str]], prefix_char):
    url = f"https://anglish.fandom.com/wiki/English_Wordbook/{prefix_char}"
    
    res = make_request(url)
    soup = BeautifulSoup(res.text, features="html.parser")

    rows: list[bs4.Tag] = soup.body.find("table").find_all("tr")
    start_index = 3
    from_index = 0
    to_index = 2
    for row in rows[start_index:]:
        data_cols: list[bs4.Tag] = row.find_all("td")
        if len(data_cols) > to_index:
            from_tag = data_cols[from_index]
            if from_tag.b is not None:
                from_str = from_tag.b.get_text()
            else:
                from_str = from_tag.getText()
            to_str = data_cols[to_index].get_text()

            if to_str.strip() == "-":
                continue

            out[from_str] = [to_option.strip() for to_option in re.split(r"[\s;,:]+", to_str) if len(to_option.strip()) > 0]


def get_anglish_lookup() -> dict[str, list[str]]:
    A_code = 65
    num_chars = 26
    prefixes = [chr(num) for num in range(A_code, A_code + num_chars)]
    out: dict[str, list[str]] = dict()

    for prefix_char in prefixes:
        add_prefix_to_lookup(out, prefix_char)
    
    return out

translation_cache: dict[str, str] = dict()
def translate_word(word: str, lookup: dict[str, list[str]], interactive: bool = False) -> str:
    if word in translation_cache.keys():
        return translation_cache[word]

    if word.lower() in lookup.keys():
        if interactive:
            prompt = f"Please select a substitute for '{word}':\n" + "\n".join([f"{index}: '{sub}'" for index, sub in enumerate(lookup[word.lower()])]) + "\n"
            choice = int(input(prompt))
        else:
            print(f"Looking up a new word for '{word}'...")
            choice = 0
        out_word = lookup[word.lower()][choice]
    else:
        if interactive:
            prompt = f"Please provide a substitute for '{word}':\n"
            out_word = input(prompt)
        else:
            print(f"Could not find a translation for '{word}'...")
            out_word = f"**{word}**"
    
    translation_cache[word] = out_word
    return out_word


def translate_text(txt: str, lookup: dict[str, list[str]], interactive: bool = False) -> str:
    words = tokenize(txt)
    out = list()
    for word in words:
        origin = lookup_origin(word.lower())
        if origin is not None and ("french" in origin or "latin" in origin):
            try:
                out_word = translate_word(word, lookup, interactive)
            except Exception as err:
                print(f"Error translating '{word}': {str(err)}")
                out_word = "****"
        else:
            out_word = word
        
        out.append(out_word)
    
    return " ".join(out)

def mod_fname(fname: str) -> str:
    split_fname = fname.split('.')
    return ".".join(split_fname[:-1]) + "_translated" + "." + split_fname[-1]

if __name__ == "__main__":
    fname = "gettysburg_last_sentence.txt"
    with open(fname, 'r') as fp:
        txt = fp.read()
    
    print(f"Building lookup dictionary...")
    start_time = time.perf_counter()
    anglish_lookup = get_anglish_lookup()
    print(f"Built lookup dictionary in {time.perf_counter() - start_time:.3f}s!")

    translated = translate_text(txt, anglish_lookup, True)

    out_fname = mod_fname(fname)
    with open(out_fname, 'w') as fp:
        fp.write(translated)
