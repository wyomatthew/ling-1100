import re
import time
from re import match
from typing import Optional
from functools import lru_cache

import bs4
import requests as r
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.metrics import edit_distance

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

def get_etymonline_search(word: str) -> list[tuple[str, str]]:
    url = f"{BASE_URL}/search"
    res = make_request(url, params={"q": word})

    soup = BeautifulSoup(res.text, features="html.parser")
    target_class = "word--C9UPa"
    tags: list[bs4.Tag] = soup.find_all("div", {"class": target_class})
    outputs = [(tag.find("div").find("a").get_text().split("\xa0")[0], tag.find("div").find("div").find("section").find("p").get_text()) for tag in tags]

    return sorted(outputs, key=lambda tup: edit_distance(word, tup[0], substitution_cost=2)) 

def find_language(words: list[str]) -> Optional[str]:
    for word in words:
        for hot_word in hot_list:
            if hot_word in word:
                return word
    
    return None

@lru_cache(maxsize=None)
def lookup_origin(word: str) -> Optional[tuple[str, str]]:
    etymons: list[tuple[str, str]] = list()
    try:
        etymonline_desc = get_etymonline_description(word)
        etymons.append((word, etymonline_desc))
    except ConnectionError:
        for tup in get_etymonline_search(word):
            etymons.append(tup)

    for word, description in etymons:
        text = description.lower()
        tokens = word_tokenize(text)
        words = list(filter(lambda word: match(r"\w+", word) is not None, tokens))

        language = find_language(words)
        if language is not None:
            return (word, language)

    return None
