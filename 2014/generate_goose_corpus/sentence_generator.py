"""
use goose to get cleaned sentences for a html string
"""

import os
import json
import sys
import re
from goose import Goose, Configuration
from corenlp import*

class Sentence_generator(object):
    """
    use goose to parse raw html and
    use corenlp to tokenize text to sentences
    """
    def __init__(self,corenlp_path):

        #set up goose
        config = Configuration()
        config.enable_image_fetching = False
        self._g = Goose(config)

        #set up corenlp
        self._corenlp = StanfordCoreNLP(corenlp_path = corenlp_path)

    def get_sentences(self,raw_html):
        #get cleaned text
        article = self._g.extract(raw_html = raw_html)
        text = article.cleaned_text

        #get sentences using corenlp
        nlp_data = json.loads( corenlp.parse(text) )

        sentences = [x["text"] for x in nlp_data["sentences"]]

        return sentences
