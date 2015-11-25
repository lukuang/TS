"""
get model for nuggests of a given query id
"""

import re
import os
from myStemmer import pstem as stem 


def process_qid(qid):
    if qid.find("TS") == -1:
            qid = "TS14." + qid
    return qid


def update_model(sentence,model,factor=1):
    words = re.findall("\w+",setence)
    words = map(stem,words)
    if factor==1:
        for w in words:
            if w not in model:
                model[w] = 0 
            model[w] += 1
    else:
        for w in words:
            if w not in model:
                model[w] = 0 
            model[w] += 1.0/factor 



class GoldModels(object):
    def __init__(self, judgement_files_dir):
        self._nuggest_file = os.path.join(judgement_files_dir,"nuggets.tsv")
        self._match_file = os.path.join(judgement_files_dir,"matches.tsv")
        self._update_file = os.path.join(judgement_files_dir,"updates_sampled.extended.tsv")
        self._sentence_model = {}
        self._sentence_model_discounted = {}
        self._nuggests_model = {}
        self._update_ids = {}
        self._update_ids_with_nid = {}


    def get_nuggest_model(self,qid):
        qid = process_qid(qid)
        if qid not in self._nuggests_model:
            self._nuggests_model[qid] = {}
            with open(self._nuggest_file) as f:
                for line in f: 
                    parts = line.rstrip().split()
                    if parts[0]==qid:
                        setence = parts[5]
                        update_model(sentence,self._nuggests_model[qid])
        return self._nuggests_model[qid]


    def get_update_id_with_nid(self,qid):
        if len(self._update_ids_with_nid[qid]) != 0:
            for uid in self._update_ids[qid]:
                self._update_ids[qid][uid] = False
        else:
            self._update_ids[qid]= {}
            with open(self._match_file) as f:
                    for line in f:
                        parts = line.rstrip().split()
                        if parts[0] == qid:
                            self._update_ids[qid][parts[1]] = False

    def get_update_id(self,qid):
        nugget_matches = {}
        uid_nid_matches = {}
        if qid not in self._update_ids:
            self._update_ids[qid]= {}
            with open(self._match_file) as f:
                for line in f:
                    parts = line.rstrip().split()
                    if parts[0] == qid:
                        uid = parts[1]
                        nid = parts[2]
                        if nid not in nugget_matches:
                            nugget_matches[nid] = 0
                        nugget_matches[nid] += 1
                        uid_nid_matches[uid] = nid
            for uid in uid_nid_matches:
                self._update_ids[qid][uid] = nugget_matches[uid_nid_matches[uid]]


    def get_sentence_model(self,qid):
        qid = process_qid(qid)
        if qid not in self._sentence_model:
            self._sentence_model[qid] = {}
            self.get_update_id(self,qid)
            with open(self._update_file) as f:
                parts = line.rstrip().split()
                if parts[0] == qid:
                    uid = parts[1]

                    if uid in self._update_ids[qid]:
                        sentence = parts[6]
                        update_model(sentence,self._sentence_model[qid])

        return self._sentence_model[qid]





    def get_sentence_model_discounted(self,qid):
        qid = process_qid(qid)
        if qid not in self._sentence_model_discounted:
            self._sentence_model_discounted[qid] = {}
            self.get_update_id(self,qid)
            with open(self._update_file) as f:
                parts = line.rstrip().split()
                if parts[0] == qid:
                    uid = parts[1]

                    if uid in self._update_ids[qid]:
                        sentence = parts[6]
                        update_model(sentence,self._sentence_model_discounted[qid],self._update_ids[qid][uid])

        return self._sentence_model_discounted[qid]

