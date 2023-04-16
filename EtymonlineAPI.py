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
