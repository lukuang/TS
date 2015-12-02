"""
Compare different query models with the models of the
standard models, e.g. the nuggets model, sentence model, and document models.
"""

import re
import os
import math
import sys,time,json,argparse
from common import *
from get_query_model import *
from get_judgement_models import GoldModels


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judgement_files_dir",'-j',default = "/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/TS14-data")
    parser.add_argument("--corpus_dir","-c",default = "/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/json_corpus")
    parser.add_argument("--stopword_file","-s",default = "/home/1546/data/new_stopwords")

    args=parser.parse_args()
    stopwords = read_stopwords(args.stopword_file)

     
    judgement_models = GoldModels(args.judgement_files_dir,args.corpus_dir,stopwords)

    for i in xrange(11,26):
        print "for query %d" %i
        qid = str(i)
        query_model = judgement_models.get_document_model(qid)
        with open(qid+".json","w") as f:
            f.write(json.dumps(query_model))


if __name__=="__main__":
    main()
