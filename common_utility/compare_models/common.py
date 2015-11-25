"""
commonly used functions
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

def normalize_model(model):
    occurance = sum(model.values())
    for w in model:
        model[w] /= 1.0*occurance