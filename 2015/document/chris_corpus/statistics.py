from __future__ import division
import re

class Statistics:
    def __init__(self, query_model, background, mu):
        self._mu = mu
        self._query_model = query_model
        self._background = background
        min = 1000
        for term in background:
            if background[term] != 0.0 and min > background[term]:
                min = background[term]
        print "min is", min
        for term in self._background:
            if self._background[term] == 0.0:
                 self._background[term] = min      

class Sentence:
    def __init__(self, sentence_string):
        self._terms = {}
        self._length = 0
        #print "the sentence is:",sentence_string
        for word in re.findall("\w+",sentence_string):
            if word not in self._terms:
                self._terms[word] = 1
            else:
                self._terms[word] += 1
            self._length += 1
        #for t in self._terms:
        #    print t,":",self._terms[t]
        #print "_"*20

    
class Document:
    def __init__(self, sentences_dict, time, s, query_words):
        terms = {}
        self._model = {}
        self._length = 0
        self._time = time
        self._sentences = {}
        self._needed = False
        for key in sentences_dict:
            #print "get sentence:", key
            if sentences_dict[key] == None:
                continue
            self._sentences[key]=Sentence(sentences_dict[key])
            for term in self._sentences[key]._terms:
                if term not in terms:
                    terms[term] = self._sentences[key]._terms[term]
                else:
                    terms[term] = self._sentences[key]._terms[term] + terms[term]
                self._length += self._sentences[key]._terms[term]
        self._needed = False
        for t in query_words:
            if t in terms:
                self._needed  = True
        if not self._needed:    
            return None
        for term in s._background:
            if term in terms :
                self._model[term] = (terms[term] + s._mu*s._background[term])/(self._length + s._mu)
            else:
                self._model[term] = s._mu*s._background[term]/(self._length + s._mu)
        #print "distinct terms:", len(self._terms)
        #print "length:", self._length
        #print "number of sentences", len(self._sentences)

class Query:
    def __init__ (self, start, end, words, dirs):
        self._start, self._end, self._words, self._dirs = start, end, words, dirs
