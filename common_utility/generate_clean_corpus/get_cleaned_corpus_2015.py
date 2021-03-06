"""
use goose to get cleaned corpus for 2015 data
in a per query basis
"""

import os
import json
import sys
import re
import argparse
import streamcorpus
import Levenshtein
from sentence_generator import Sentence_generator
from myStemmer import pstem as stem


def get_done_list(record_file):
    done_list = []
    if os.path.exists(record_file):
        with open(record_file) as f:
            for line in f:
                line = line.rstrip()
                if len(line) != 0:
                    done_list.append(line)
    return done_list


def get_sub_doc_list(doc_list,run_id,total,done_list,debug):
    required_doc_list =[]
    all_list = []
    with open(doc_list) as f:
        for line in f:
            line = line.rstrip()
            all_list.append(line)


    gap = len(all_list)//total

    if run_id != total:
        required_doc_list = all_list[(run_id-1)*gap:run_id*gap]
    else:
        required_doc_list = all_list[(run_id-1)*gap:]

    if debug:
        print "there are %d dirs" %len(all_list)
        print "%d dirs need to be processed" %len(required_doc_list)
    return set(required_doc_list) - set(done_list)


def get_doc_list(source_dir,debug):
    required_doc_list = os.walk(source_dir).next()[1]
    required_doc_list = [os.path.join(source_dir,x) for x in required_doc_list]
    if debug:
        print "%d dirs need to be processed" %(len(required_doc_list))
    return required_doc_list



def get_doc(si):
    if ("serif" in si.body.sentences):
        tag="serif"
    elif ("lingpipe" in si.body.sentences):
        tag="lingpipe"
    else:
        return None ,None, None
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
            sentence += token.token+" "
        #print type(sentence)
        document["sentences"][sentence_index_string] = sentence.decode("utf-8",'ignore')
    document["time"]=int(si.stream_time.epoch_ticks)

    raw_html = si.body.clean_html
    return document_id, document, raw_html


def clean_document(document,sentences):
    indecis = set()
    all_indecis = set(document["sentences"].keys())
    for s in sentences:
        max_score = 0.0
        max_index = -1
        for index in document["sentences"]:
            #print "types are %s %s" %(type(s),type(document["sentences"][index]))
            score = Levenshtein.ratio(s,document["sentences"][index])
            if score > max_score:
                max_score = score
                max_index = index
        indecis.add(max_index)
        #document["sentences"][max_index] = s

    for index in (all_indecis - indecis):
        document["sentences"].pop(index,None)

def stem_sentence(sentence):
    all_words = re.findall("\w+",sentence.lower())
    all_words = map(stem,all_words)
    return " ".join(all_words)


def stem_document(document):
    for index in document["sentences"]:
        document["sentences"][index] = stem_sentence(document["sentences"][index])

def write_docs(dest_file,docs):
    with open(dest_file,"w") as f:
        f.write(json.dumps(docs))



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corenlp_path","-c",
        default = '/home/1546/myEV/lib/python2.7/site-packages/corenlp')
    parser.add_argument("--source_dir","-s",
        default = "/lustre/scratch/lukuang/Temporal_Summerization/TS-2015/data/raw")
    parser.add_argument("--dest_dir","-d",
        default = "/lustre/scratch/lukuang/Temporal_Summerization/TS-2015/data/cleaned_corpus")
    parser.add_argument("--debug","-de",action="store_true",default = False)
    parser.add_argument("--use_nlp","-n",action="store_true",default = False)
    parser.add_argument("qid",choices=map(str,range(26,47)))

    args=parser.parse_args()

    
    #set up generator
    if args.use_nlp:
        os.chdir(args.corenlp_path)
    generator = Sentence_generator(args.use_nlp)

    source_dir = os.path.join(args.source_dir,args.qid)
    dest_dir = os.path.join(args.dest_dir,args.qid)
    if not os.path.exists(dest_dir):
        os.mkdir(dest_dir)
    
    required_doc_list = get_doc_list(source_dir,args.debug)
    #print "dest dir is %s" %args.dest_dir
    for dir_name in required_doc_list:
        print "process %s" %dir_name
        docs = {}
        num = 0
        #print "dest dir is %s" %args.dest_dir
        dest_file = os.path.join(dest_dir,os.path.basename(dir_name) )
        if os.path.exists(dest_file):
            continue
        #print "dest file is %s" %dest_file
        for doc_name in os.listdir(dir_name):
            m1=re.search("MAINSTREAM_NEWS",doc_name)
            m2=re.search("news-",doc_name)
            #m3=re.search("WEBLOG-",doc)
            if(m1==None and m2==None ):
                #print "discard",doc
                pass
            else:
                source_file = os.path.join(dir_name,doc_name)
                for si in streamcorpus.Chunk(path = source_file ):
                    document_id, document, raw_html = get_doc(si)
                    #debug purpose
                    
                    if document_id is not None:
                        #print "for document id %s" %(document_id)
                        num += 1
                        #print "It's number %d document" %(num)
                        if args.debug:
                            print "there are %d sentences in original document %s" %(len(document["sentences"]),document_id)
                            print "original document:",document_id
                            dids=document["sentences"].keys()
                            dids.sort()
                            for key in dids:
                                print "%s: %s" %(key, document["sentences"][key]) 
                        sentences = generator.get_sentences(raw_html)
                        if sentences is None:
                            continue
                        clean_document(document,sentences)
                        stem_document(document)
                        docs[document_id] = document
                    else:
                        print "skip no did document"
                        print "-"*20
                        continue
                    if args.debug:
                        print "there are %d sentences in new document %s" %(len(document["sentences"]),document_id)

                        print "new document:",document_id
                        dids=document["sentences"].keys()
                        dids.sort()
                        for key in dids:
                           print "%s: %s" %(key, document["sentences"][key])
        if args.debug:
            sys.exit(-1)

        write_docs(dest_file,docs)
        #sys.exit(-1)
    print "finished"







if __name__=="__main__":

    reload(sys)  
    sys.setdefaultencoding('utf8')
    main()

