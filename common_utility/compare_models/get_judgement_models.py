"""
get model for nuggests of a given query id
"""

import re
import os
import lxml.etree as ET
import sys,time,json
from common import *




class GoldModels(object):
    def __init__(self, judgement_files_dir,corpus_dir,stopwords):
        self._nuggest_file = os.path.join(judgement_files_dir,"nuggets.tsv")
        self._match_file = os.path.join(judgement_files_dir,"matches.tsv")
        self._update_file = os.path.join(judgement_files_dir,"updates_sampled.extended.tsv")
        self._query_file = os.path.join(judgement_files_dir,"trec2014-ts-topics-test.xml")
        self._corpus_dir = corpus_dir
        self._stopwords = stopwords
        self._document_model = {}
        self._original_query_model = {}
        self._sentence_model = {}
        self._sentence_model_discounted = {}
        self._nuggests_model = {}
        self._update_ids = {}
        self._document_ids = {}
        self._update_ids_with_nid = {}
        self.parse_query_file()

    def get_sentences_from_documents(self,doc_name):
        m = re.search("^(\d+)-", doc_name)
        if m is None:
            print "doc name error", doc_name

        else:
            file_name = time.strftime('%Y-%m-%d-%H', time.gmtime(float(m.group(1))))
            #print "file_name is", file_name
            data = json.load(open(os.path.join( self._corpus_dir,file_name) ) )
            for single_doc in data:
                did = single_doc[0]
                if doc_name != did:
                    continue
                else:
                    #print "Found!"
                    sub_data = single_doc[1]
                    sentences = []
                    for sid in sub_data["sentences"]:
                        sentences.append(sub_data["sentences"][sid])
                    
                    # doc = documents[did]
                    
                    # sentence_struct = doc["sentences"]
                    
                    # for sid in sentence_struct:
                    #     sentences.append(sentences[sid]["text"])
                    return sentences
        return None


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


    def get_original_query_model(self,qid):
        
        qid = process_qid(qid)

        return self._original_query_model[qid]

    def parse_query_file(self):
        tree = ET.parse(self._query_file)
        root = tree.getroot()
        for event in root.iter("event"):
            qid = process_qid(event.find("id").text)
            self._original_query_model[qid] = {}
            word_string = event.find("title").text + " "+ event.find("query").text
            word_string = " ".join( set(word_string.findall("\w+",word_string.lower()) ) )
            update_model(word_string,self._original_query_model[qid])
            normalize_model(self._original_query_model[qid],self._stopwords)


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
            normalize_model(self._nuggests_model[qid],self._stopwords)
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
                normalize_model(self._sentence_model[qid],self._stopwords)
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
            normalize_model(self._sentence_model_discounted[qid],self._stopwords)
        return self._sentence_model_discounted[qid]


    def get_document_model(self,qid):
        qid = process_qid(qid)
        if qid not in self._document_model:
            self._document_model[qid] = {}
            self.get_update_id(qid)
            self.get_document_id(qid)
            for did in self._document_ids[qid]:
                #print "for did %s" %did
                sentences = self.get_sentences_from_documents(did)

                #skip when did not find the document or the document
                #name is in error format
                if sentences is None:
                    continue
                for sentence in sentences:
                    update_model(sentence,self._document_model[qid])
            normalize_model(self._document_model[qid],self._stopwords)
        return self._document_model[qid]