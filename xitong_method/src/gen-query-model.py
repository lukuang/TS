"""
generate ML estimation of queries
"""

import re,sys,os
import json
import lxml.etree as ET
import argparse
from myStemmer import pstem as stem

def rep(match):
    return match.group(1)+" "+match.group(2)

def read_query(query_file):
    tree = ET.parse(query_file)
    root = tree.getroot()
    models = {}
    length = {}
    for event in root.iter("event"):
        qid = event.find("id").text
        models[qid] = {}
        length[qid] = 0
        word_string = event.find("title").text
        #print "query is", word_string
        word_string = re.sub("[^A-Za-z0-9]+"," ", word_string.lower())
        word_string = re.sub("([a-z])([A-Z])", rep, word_string)
        all_words = re.findall("\w+",word_string)
        length[qid] = 0
        for word in all_words:
            #if word in stopwords:
            #    continue
            word = stem( word.lower() )
            if word not in models[qid]:
                models[qid][word] = 0
            models[qid][word] += 1
            length[qid] += 1
        for w in models[qid]:
            models[qid][w] = models[qid][w]*1.0/length[qid]
    return models,length
            
def read_stopwords(stopword_file):
    stopwords = {}
    with open(stopword_file) as f:
        for line in f:
            line = line.rstrip()
            m = re.search("^\w+$",line)
            if m is not None:
                stopwords[line] = 0
            else:
                print "skip line in stopword file %s" %line
    return stopwords




def main():
    parser = argparse.ArgumentParser(usage = __doc__)
    parser.add_argument('--query_file', "-q", default = "/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/TS14-data/trec2014-ts-topics-test.xml")
    parser.add_argument("--output_file", "-o", default = "data/query_ml")
    #parser.add_argument("--stopword_file", "-s", default = "data/stoplist")

    args = parser.parse_args()

    #stopwords = read_stopwords(args.stopword_file)
    models, length = read_query(args.query_file)

    with open(args.output_file,"w") as f:
        for qid in sorted(models.keys()):
            f.write("%s %d\n" %(qid,length[qid]) )
            for term in models[qid]:
                f.write("%s %f\n" %(term,models[qid][term]) )
            f.write("\n") # just in compliance of the original file to avoid potential problems of loading the map file       


if __name__ == '__main__':
    main()
