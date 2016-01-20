"""
commonly used functions for compare different query models
"""
from myStemmer import pstem as stem 
import re

def process_qid(qid):
    if qid.find("TS") == -1:
            qid = "TS14." + qid
    return qid


def update_model(sentence,model,factor=1):
    words = re.findall("\w+",sentence.lower())
    words = map(stem,words)
    if factor==1:
        for w in words:
            if w.isdigit():
                continue
            if w not in model:
                model[w] = 0 
            model[w] += 1
    else:
        for w in words:
            if w.isdigit():
                continue
            if w not in model:
                model[w] = 0 
            model[w] += 1.0/factor 


def read_stopwords(stopword_file):
    stopwords = set()
    with open(stopword_file) as f:
        for line in f:
            m = re.search("(\w+)", line)
            if m is not None:
                stopwords.add(stem(m.group(1).lower())) 
    return stopwords

def remove_stopwords(model,stopwords):
    for k in model.keys():
        if k in stopwords:
            model.pop(k, None)

def normalize_model(model,stopwords):
    
    remove_stopwords(model,stopwords)

    occurance = 0
    for w in occurance:
        occurance += model[w]*model[w]
    for w in model:
        model[w] /= 1.0*occurance
