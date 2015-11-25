"""
get model for nuggests of a given query id
"""

import re
import os
from myStemmer import pstem as stem 
import sys,time,json

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



class GoldModels(object):
    def __init__(self, judgement_files_dir,corpus_dir):
        self._nuggest_file = os.path.join(judgement_files_dir,"nuggets.tsv")
        self._match_file = os.path.join(judgement_files_dir,"matches.tsv")
        self._update_file = os.path.join(judgement_files_dir,"updates_sampled.extended.tsv")
        self._corpus_dir = corpus_dir
        self._document_model = {}
        self._sentence_model = {}
        self._sentence_model_discounted = {}
        self._nuggests_model = {}
        self._update_ids = {}
        self._document_ids = {}
        self._update_ids_with_nid = {}

    def get_sentences_from_documents(self,doc_name):
        m = re.search("^(\d+)-", doc_name)
        if m is None:
            print "doc name error", doc_name
            return None

        else:
            file_name = time.strftime('%Y-%m-%d-%H', time.gmtime(float(m.group(1))))
            print "file_name is", file_name
            documents = json.load(open(os.path.join( self._corpus_dir,file_name) ) )
            for did in documents:
                if doc_name != did:
                    continue
                else:
                    print "Found!"
                    doc = documents[did]
                    #print "sentences:"
                    sentence_struct = doc["sentences"]
                    sentences = []
                    for sid in sentence_struct:
                        sentences.append(sentences[sid]["text"])
                    return sentences


    def get_update_id(self,qid):
        qid = process_qid(qid)
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

    def get_document_id(self,qid):
        qid = process_qid(qid)
        if qid not in self._update_ids:
            self.get_update_id(qid)
        if qid not in self._document_ids:
            self._document_ids[qid] = set()
            with open(self._update_file) as f:
                for line in f:
                    parts = line.rstrip().split()
                    if parts[0] == qid:
                        uid = parts[1]
                        did = parts[2]
                        duid = parts[5]
                        if uid in self._update_ids[qid] or duid in self._update_ids[qid]:
                            self._document_ids[qid].add(did)




    def get_nuggest_model(self,qid):
        qid = process_qid(qid)
        if qid not in self._nuggests_model:
            self._nuggests_model[qid] = {}
            with open(self._nuggest_file) as f:
                for line in f: 
                    parts = line.rstrip().split()
                    if parts[0]==qid:
                        sentence = parts[5]
                        update_model(sentence,self._nuggests_model[qid])
            normalize_model(self._nuggests_model[qid])
        return self._nuggests_model[qid]



    



    def get_sentence_model(self,qid):
        qid = process_qid(qid)
        if qid not in self._sentence_model:
            self._sentence_model[qid] = {}
            self.get_update_id(qid)
            with open(self._update_file) as f:
                for line in f:
                    parts = line.rstrip().split()
                    if parts[0] == qid:
                        uid = parts[1]

                        if uid in self._update_ids[qid]:
                            sentence = parts[6]
                            update_model(sentence,self._sentence_model[qid])
                normalize_model(self._sentence_model[qid])
        return self._sentence_model[qid]





    def get_sentence_model_discounted(self,qid):
        qid = process_qid(qid)
        if qid not in self._sentence_model_discounted:
            self._sentence_model_discounted[qid] = {}
            self.get_update_id(qid)
            with open(self._update_file) as f:
                for line in f:
                    parts = line.rstrip().split()
                    if parts[0] == qid:
                        uid = parts[1]

                        if uid in self._update_ids[qid]:
                            sentence = parts[6]
                            update_model(sentence,self._sentence_model_discounted[qid],self._update_ids[qid][uid])
            normalize_model(self._sentence_model_discounted[qid])
        return self._sentence_model_discounted[qid]


    def get_document_model(self,qid):
        qid = process_qid(qid)
        if qid not in self._document_model:
            self._document_model[qid] = {}
            self.get_update_id(qid)
            self.get_document_id(qid)
            for did in self._document_ids[qid]:
                print "for did %s" %did
                for sentence in self.get_sentences_from_documents(did):
                    update_model(sentence,self._document_model[qid])
        return self._document_model[qid]