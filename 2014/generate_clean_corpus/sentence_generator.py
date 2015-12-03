"""
use goose to get cleaned sentences for a html string
"""

import os
import json
import sys
import re
import string
from goose import Goose, Configuration
from corenlp.corenlp import*
from nltk.tokenize import sent_tokenize
import lxml

class Sentence_generator(object):
    """
    use goose to parse raw html and
    use corenlp to tokenize text to sentences
    """
    def __init__(self,use_nlp=True):
        self._use_nlp = use_nlp
        
        #set up goose
        config = Configuration()
        config.enable_image_fetching = False
        self._g = Goose(config)

        if use_nlp:    
            #set up corenlp
            self._corenlp = StanfordCoreNLP()

    def get_sentences(self,raw_html):
        #get cleaned text
        try:
            article = self._g.extract(raw_html = raw_html)
        except lxml.etree.ParserError as e:
            print e
            print "the raw html is:"
            print "_"*20
            print raw_html
            sys.exit(-1)
        text = article.cleaned_text
        if self._use_nlp:
            return self.corenlp_get_sentences(text)

        else:
            return self.nltk_get_sentences(text)

        

    def nltk_get_sentences(self,text):
        return sent_tokenize(text)


    def corenlp_get_sentences(self,text):
        temp_data = self._corenlp.parse(text)
        
        nlp_data = json.loads( temp_data)

        try:
            sentences = [x["text"] for x in nlp_data["sentences"]]
        except Exception as e:
            print e
            print nlp_data

        return sentences