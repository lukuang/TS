"""
get performance for runs and normalize them based on one of the runs
"""

import os
import json
import sys
import re
import argparse

def get_performances(eval_file):
    performances = {}

    with open(eval_file) as f:
        for line in f:
            parts = line.split()
            if parts[0] != "AVG" or parts[1] == "ALL":
                continue
            else:
                run_id = parts[2]
                e = float(parts[4])
                c = float(parts[5])
                l = float(parts[7])
                h = float(parts[6])
                performances[run_id] = {"e":e, "c":c, "h":h, "l":l}
                
    return performances


def normalize(performances, target_run_id):
    standard_e = performances[target_run_id]["e"]
    standard_c = performances[target_run_id]["c"]
    standard_l = performances[target_run_id]["l"]
    standard_h = performances[target_run_id]["h"]
    for run_id in performances:
        performances[run_id]["e"] /= standard_e
        performances[run_id]["c"] /= standard_c
        performances[run_id]["l"] /= standard_l
        performances[run_id]["h"] /= standard_h


def show(performances):
    sorted_performances = sorted(performances.items(), key=lambda x : x[1]["h"], reverse=True)
    for (run_id,score) in sorted_performances:
        print "%s\t%f\t%f\t%f\t%f" %(run_id, performances[run_id]["e"],performances[run_id]["c"],performances[run_id]["l"],performances[run_id]["h"])

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("eval_file")
    parser.add_argument("run_id")
    args=parser.parse_args()
  
    performances =  get_performances(args.eval_file)

    normalize(performances,args.run_id)

    show(performances)


if __name__=="__main__":
    main()

