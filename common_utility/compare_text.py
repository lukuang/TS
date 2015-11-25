# -*- encoding: utf-8 -*-
"""
compare text in original TS corpus and parsed by goose
"""
import sys
import streamcorpus
import os
import re
import argparse
import logging
import json
import time
from goose import Goose
import codecs


def find_text_in_doc(si, document_id):
    if ("serif" in si.body.sentences):
        tag="serif"
    elif ("lingpipe" in si.body.sentences):
        tag="lingpipe"
    else:
        return None ,None
    # unique document id
    did = si.stream_id
    if did != document_id:
        #print "wrong document id: %s" %did
        return None ,None
    print "document id found!"

    # get original text
    origin_text = ""
    for sentence_index in range(len(si.body.sentences[tag])):
        sentence_index_string = "%d"%(sentence_index)
        # sentence tokens
        sentence_tokens = si.body.sentences[tag][sentence_index].tokens
        # concatenate token strings into a sentence
        sentence=""
        for token in sentence_tokens:
            sentence = "%s%s "%(sentence,token.token)
        origin_text += " %s" %(sentence)
    
    raw_html = si.body.clean_html
    g =  Goose()
    article = g.extract(raw_html = raw_html)

    return origin_text, article.cleaned_text

def get_tex(dir_name,document_id):
    for doc in os.listdir(dir_name):
        m1=re.search("MAINSTREAM_NEWS",doc)
        m2=re.search("news-",doc)
        #m3=re.search("WEBLOG-",doc)
        if(m1==None and m2==None ):
            #print "discard",doc
            pass
        else:
            for si in streamcorpus.Chunk(path = os.path.join(dir_name,doc) ):
                origin_text, goose_text=find_text_in_doc(si,document_id)
                if origin_text is not None:
                    return origin_text, goose_text
    return None ,None

def get_dir_name(document_id):
    m = re.search("^(\d+)-", document_id)
    if m is None:
        print "doc name error", document_id
        sys.exit(-1)

    else:

        dir_name = time.strftime('%Y-%m-%d-%H', time.gmtime(float(m.group(1))))
        return dir_name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir")
    parser.add_argument("document_id")
    parser.add_argument("dest_file")
    args = parser.parse_args()
    dir_name = get_dir_name(args.document_id)
    dir_name = os.path.join(args.source_dir,dir_name)
    print "found dir path %s" %(dir_name)
    origin_text, goose_text = get_tex(dir_name,args.document_id)
    if origin_text is None:
        print "not text is found!"
    else:
        with codecs.open(args.dest_file,"w","utf-8") as f:
            f.write("original:\n")
            origin_text = origin_text.decode("utf-8")
            f.write(origin_text+"\n")
            f.write("-"*20+"\n")
            f.write("goose:"+"\n")
            #goose_text = goose_text.decode("utf-8")
            f.write(goose_text+"\n")


if __name__ == "__main__":
    main()
