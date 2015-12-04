"""
get the cropus generated by Chris
"""

import sys
import streamcorpus
import os
import re
import logging
import json
import time
import argparse

def get_doc_list(queries_file,run_id,source_dir,debug):
    queries = json.load(open(queries_file))
    q_name = queries[run_id]
    required_doc_list = []
    for file_name in os.listdir(source_dir):
        if re.search("\.sc$",file_name) is not None:
            if file_name.find(q_name) != -1:
                required_doc_list.append(os.path.join(source_dir,file_name) )
            else:
                if debug:
                    print "skip no query file %s" %(file_name)
        else:
            if debug:
                print "skip no sc file %s" %(file_name)
    return required_doc_list, q_name



def get_dir_name(document_id):
    m = re.search("^(\d+)-", document_id)
    if m is None:
        print "doc name error", document_id
        sys.exit(-1)

    else:

        dir_name = time.strftime('%Y-%m-%d-%H', time.gmtime(float(m.group(1))))
        return dir_name




def get_doc(si):
    if ("goose" in si.body.sentences):
        tag="goose"
    else:
        return None ,None
    # unique document id
    document = {}
    document_id = si.stream_id
    # seconds from 1970 (UTC)
    document["time"] = "%d"%(si.stream_time.epoch_ticks)
    # sentence index
    document["sentences"] = {}
    for sentence_index in range(len(si.body.sentences[tag])):
        sentence_index_string = "%d"%(sentence_index)
        # sentence tokens
        sentence_tokens = si.body.sentences[tag][sentence_index].tokens
        # concatenate token strings into a sentence
        sentence=""
        for token in sentence_tokens:
            sentence = "%s%s "%(sentence,token.token)
        document["sentences"][sentence_index_string] = sentence
    document["time"]=int(si.stream_time.epoch_ticks)
    return document_id, document



def write_2_doc(required_doc_list):
    docs={}
    for file_name in required_doc_list:
        for si in streamcorpus.Chunk(path=file_name):
            did, single_doc=get_doc(si)
            if (single_doc!=None):
                dir_name = get_dir_name(did)
                if dir_name not in docs:
                    docs[dir_name] = {}
                docs[dir_name][did] = single_doc
    #sorted_docs = sorted(docs.items(), key = lambda x: x[1]["time"])
    return docs



def output(docs,dest_dir,q_name):
    query_dir = os.path.join(dest_dir,q_name)
    if not os.path.exists(query_dir):
        os.makedirs(query_dir)

    for hour in docs:
        dest_file = os.path.join(query_dir,hour)
        with open(dest_file,"w") as f:
            f.write(json.dumps(docs[hour]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries_file","-q",
        default = "/lustre/scratch/lukuang/Temporal_Summerization/TS-2015/data/chris_data/trec-data/deduped-articles/goose/2014_serif_only/0.8/queries")
    parser.add_argument("--source_dir","-s",
        default = "/lustre/scratch/lukuang/Temporal_Summerization/TS-2015/data/chris_data/trec-data/deduped-articles/goose/2014_serif_only/0.8")
    parser.add_argument("--dest_dir","-d",
        default = "/lustre/scratch/lukuang/Temporal_Summerization/TS-2015/data/chris_data/2014")
    parser.add_argument("--debug","-de",action="store_true",default = False)
    parser.add_argument("run_id",type=int)

    args=parser.parse_args()

    args.run_id -= 1
    required_doc_list,q_name = get_doc_list(args.queries_file,args.run_id,args.source_dir,args.debug)

    docs = write_2_doc(required_doc_list)

    output(docs,args.dest_dir,q_name)
    print "finished"




if __name__=="__main__":
    main()