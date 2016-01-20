"""
compare document result differences
"""

import os
import json
import sys
import re
import argparse


def get_hour_result(file_name):
    hour_result = []
    count = 0 
    limit = 0
    with open(file_name) as f:
        for line in f:
            m = re.search(".*? (.*?)$", line)
            if m is None:
                print "error line in",file_name
                print "the error line is", line
                sys.exit(-1)
            else:
                did = m.group(1)
                #print "add did %s" %(did)
                hour_result.append(did)
                count += 1
                if count >= 10:
                    break
    return hour_result

def get_result(data_dir):
    result = {}
    for qid in map(str,range(26,47)):
        result[qid] = []
        query_dir = os.path.join(data_dir, qid)
        for hour_file in os.listdir(query_dir):
            hour_file = os.path.join(query_dir, hour_file)
            if os.path.isfile(hour_file):
                result[qid] += get_hour_result(hour_file)
    return result

def output(result1,result2):
    all_common = 0
    all_unique = 0
    for qid in map(str,range(26,47)):
        common = 0
        unique = 0
        for did in result1[qid]:
            if did not in result2[qid]:
                unique += 1
            else:
                common += 1
        all_common += common
        all_unique += unique
       
        print "\tfor query %s" %qid
        print "\tcommon %d, unique: %d" %(common,unique)
    print "all common %d" %(all_common)
    print "all unique %d" %(all_unique)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dir1")
    parser.add_argument("dir2")
    args=parser.parse_args()
    result1 = get_result(args.dir1)
    result2 = get_result(args.dir2)
    print "difference between %s and %s" %(args.dir1, args.dir2)
    output(result1,result2)





if __name__=="__main__":
    main()

