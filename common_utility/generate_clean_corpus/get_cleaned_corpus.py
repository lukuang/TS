"""
use goose to get cleaned corpus
"""

import os
import json
import sys
import re
import argparse
import streamcorpus
import Levenshtein
from sentence_generator import Sentence_generator


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


def get_doc_list(record_file,doc_list,run_id,total,debug):
    done_list = get_done_list(record_file)
    if debug:
        print "length of done list %d" %len(done_list)
    required_doc_list = get_sub_doc_list(doc_list,run_id,total,done_list,debug)
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


def write_docs(dest_file,docs,record_file,dir_name):
    with open(dest_file,"w") as f:
        f.write(json.dumps(docs))

    with open(record_file,"a") as f:
        f.write(dir_name+"\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corenlp_path","-c",
        default = '/home/1546/myEV/lib/python2.7/site-packages/corenlp')
    parser.add_argument("--doc_list","-l",
        default = "/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/new_d_name.list")
    parser.add_argument("--source_dir","-s",
        default = "/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/")
    parser.add_argument("--dest_dir","-d",
        default = "/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/goose_corpus/")
    parser.add_argument("--debug","-de",action="store_true",default = False)
    parser.add_argument("--use_nlp","-n",action="store_true",default = False)
    parser.add_argument("total",type=int)
    parser.add_argument("run_id",type=int)

    args=parser.parse_args()

    
    #set up generator
    if args.use_nlp:
        os.chdir(args.corenlp_path)
    generator = Sentence_generator(args.use_nlp)

    #get document list needed to be generated
    record_file = os.path.join(args.dest_dir,"record"+str(args.run_id))
    required_doc_list = get_doc_list(record_file,args.doc_list,args.run_id,args.total,args.debug)
    #print "dest dir is %s" %args.dest_dir
    for dir_name in required_doc_list:
        print "process %s" %dir_name
        docs = {}
        num = 0
        #print "dest dir is %s" %args.dest_dir
        dest_file = os.path.join(args.dest_dir,os.path.basename(dir_name) )
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

        write_docs(dest_file,docs,record_file,dir_name)
        #sys.exit(-1)
    print "finished"







if __name__=="__main__":

    reload(sys)  
    sys.setdefaultencoding('utf8')
    main()

