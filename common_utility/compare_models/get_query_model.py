"""
get query models
"""

import os,json,re

from common import *


def get_other_query_model(query_model_file,required_qid):
    """
    get expanded query model for xitong's method and
    axiomatic method
    """
    query_model = {}
    required_qid = process_qid(required_qid)
    with open(query_model_file) as f:
        for line in f:
            line = line.rstrip()
            m = re.search("(^\d+)\s+\d+$",line)
            if m is not None:
                qid = process_qid(m.group(1))
                if required_qid==qid:
                    found_query = True
                else:
                    found_query = False
            else:
                if found_query:

                    m = re.search("^(.+?)\s+([\d\.]+)$",line)
                    if m is None:
                        print "error line in model file"
                        print "line is:",line
                        sys.exit(-1)
                    else:
                        if m.group(1) in query_model:
                            print "key %s occur twice in query %s" %(m.group.qid)
                            sys.exit(-1)
                        query_model[m.group(1)] = float(m.group(2))
    return query_model




def get_my_expansion_model(expansion_file,stopwords):
    expansion_model = json.load(open(expansion_file))
    normalize_model(expansion_model,stopwords)
    return expansion_model



def get_single_expansion_query_model(query_model,expansion_model,alpha):
    single_expansion_query_model = {}
    for w in expansion_model:
        single_expansion_query_model[w] = alpha*expansion_model[w]

    for w in query_model:
        if w in single_expansion_query_model:
            single_expansion_query_model[w] += (1-alpha)*query_model[w]
        else:
            single_expansion_query_model[w] = (1-alpha)*query_model[w]

    return single_expansion_query_model


def get_double_expansion_query_model(query_model,expansion_model_a,
       alpha,expansion_model_b,beta):

    double_expansion_query_model = {}
    for w in expansion_model_a:
        double_expansion_query_model[w] = alpha*expansion_model_a[w]

    for w in expansion_model_b:
        if w in double_expansion_query_model:
            double_expansion_query_model[w] += beta*expansion_model_b[w]
        else:
            double_expansion_query_model[w] = beta*expansion_model_b[w]

    for w in query_model:
        if w in double_expansion_query_model:
            double_expansion_query_model[w] += (1-alpha-beta)*query_model[w]
        else:
            double_expansion_query_model[w] = (1-alpha-beta)*query_model[w]

    return double_expansion_query_model