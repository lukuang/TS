"""
compare text in original TS corpus and parsed by goose
"""
import sys
import streamcorpus
import os
import re
import logging
import json
import time
from goose import Goose



def find_text_in_doc(si, document_id):
    if ("serif" in si.body.sentences):
        tag="serif"
    elif ("lingpipe" in si.body.sentences):
        tag="lingpipe"
    else:
        return None ,None
    # unique document id
    did = si.stream_id
    if did != document_id
        return None ,None

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
        if(m1==None and m2==None and m3==None):
            #print "discard",doc
            pass
        else:
            for si in streamcorpus.Chunk(path = os.path.join(dir_name,doc) ):
                origin_text, goose_text=find_text_in_doc(si,document_id)
                if origin_text is not None:
                    return origin_text, goose_text
    return None ,None

def get_dir_name(document_id):
    m = re.search("^(\d+)-", doc_name)
    if m is None:
        print "doc name error", doc_name
        sys.exit(-1)

    else:

        dir_name = time.strftime('%Y-%m-%d-%H', time.gmtime(float(m.group(1))))
        return dir_name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir")
    parser.add_argument("document_id")
    args = parser.parse_args()
    dir_name = get_dir_name(args.document_id)
    dir_name = os.path.join(args.source_dir,dir_name)
    origin_text, goose_text = get_tex(dir_name,args.document_id)
    if origin_text is None:
        print "not text is found!"
    else:
        print "original:"
        print origin_text
        print "-"*20
        print "goose:"
        print goose_text


if __name__ == "__main__":
    main()