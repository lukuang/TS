"""
post analysis - perform t test on 2015 runs
"""

import os
import json
import sys
import re
import argparse
from scipy import stats


def calc_ttest( p_array1, p_array2):
    return stats.ttest_rel(p_array1, p_array2)

def get_per_query_performance(eval_file):
    performances = {}
    no_need = ["AVG","MIN","MAX","STD"]
    with open(eval_file) as f:
        for line in f:
            parts = line.split()
            if parts[0].isdigit() and parts[0] not in no_need:
                run_id = parts[2]
                h = float(parts[6])
                qid = int(parts[0])
                if run_id not in performances:
                    performances[run_id] = [0.0] * 21
                performances[run_id][qid-26] = h
    return performances


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("eval_file")
    args=parser.parse_args()
    performances = get_per_query_performance(args.eval_file)
    for k in performances:
        for l in performances:
            if k!=l:
                t,p = calc_ttest(performances[k],performances[l])
                print "for %s and %s:" %(k,l)
                print p
                print "-"*20
                #sys.exit(0) #for debugging purpose, end the program 

        



if __name__=="__main__":
    main()

