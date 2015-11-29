"""
Compare different query models with the models of the
standard models, e.g. the nuggets model, sentence model, and document models.
"""

import re
import os
import math
import sys,time,json
from common import *
from get_judgement_models import GoldModels


def numerical_compare_models(model1,model2,entropy=False):
    if entropy:
        score = .0
        for w in model1:
            if w in model2:
                score += math.log(model2[w]) * model1   
        return score
    else:
        count = 0
        for w in model1
            if w in model2:
                count += 1
        return count*1.0/len(model1) 

def show_common_words(model1,model2):
    results = []
    for w in model1:
        if w in model2:
            results.append[w]
    return results



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judgement_files_dir",'-j',default = "/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/TS14-data")
    parser.add_argument("--corpus_dir","-c",default = "/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/json_corpus")
    parser.add_argument("--stopword_file","-s",default = "/home/1546/data/new_stopwords")

    args=parser.parse_args()
    stopwords = read_stopwords(args.stopword_file)
    judgement_models = GoldModels(args.judgement_files_dir,args.corpus_dir,stopwords)
    judgement_candidates = {
        "q":"original_query",
        "d":"document",
        "n":"nuggests",
        "s":"sentence",
        "sd":"sentence_discounted"
    }

    query_candidates = {
        "o":"other_model",
        "s":"single_expansion",
        "d":"single_expansion"
    }

    while(True):
        qid = raw_input("qid:")

        #get model from judgement files
        judgement_model = raw_input("judgement_model:")
        if judgement_model not in judgement_candidates
            print "wrong input, need to be one of the:"
            for k in judgement_candidates:
                print "%s: %s" %(k,judgement_candidates[k])
            print "start over\n"+"-"*20
            continue

        if judgement_model == "q":
            model1 = judgement_models.get_original_query_model(qid)    
        elif judgement_model == "d":
            model1 = judgement_models.get_document_model(qid)    
        elif judgement_model == "n":
            model1 = judgement_models.get_nuggest_model(qid)    
        elif judgement_model == "s":    
            model1 = judgement_models.get_sentence_model(qid)    
        else:    
            model1 = judgement_models.get_sentence_model_discounted(qid)    


        #get query expansion model
        query_model = raw_input("query_model:")
        if query_model not in query_candidates
            print "wrong input, need to be one of the:"
            for k in query_candidates:
                print "%s: %s" %(k,query_candidates[k])
            print "start over\n"+"-"*20
            continue

        if query_model == "o":
            expansion_path = raw_input("expansion_path",qid)
            model2 = get_other_query_model(expansion_path)    
        elif query_model == "s":
            expansion_path = raw_input("expansion_path")
            expansion_model = get_my_expansion_model(expansion_path)
            alpha = float(raw_input("alpha"))
            model2 =  get_single_expansion_query_model(judgement_models.get_original_query_model(qid),expansion_model,alpha) 
        else:
            expansion_path1 = raw_input("expansion_path1")
            expansion_model1 = get_my_expansion_model(expansion_path1)
            alpha = float(raw_input("alpha"))
            expansion_path2 = raw_input("expansion_path2")
            expansion_model2 = get_my_expansion_model(expansion_path2)
            beta = float(raw_input("beta"))
            model2 = get_double_expansion_query_model(judgement_models.get_original_query_model(qid),expansion_model1,
       alpha,expansion_model2,beta)  

        entropy = raw_input("entropy?")
        print numerical_compare_models(model1,model2)
        if entropy.lower() == "n":
            show = raw_input("show?")
            if show.lower() == "y":
                result = show_common_words(model1,model2)
                print "common words are:"
                print result
                print "there are %d number of common words" %(len(result))



if __name__=="__main__":
    main()
