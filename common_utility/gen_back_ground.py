"""
read result indri query file from the axiomatic approach and generate a file for generating backgroud
file for my method
"""

import re,os
import json,argparse
import lxml.etree as ET



def get_queries(query_file):
    queries = {}
    tree = ET.parse(query_file)
    root = tree.getroot()
    queries = {}
    for event in root.iter("query"):
        qid = event.find("number").text
        word_string =event.find("text").text
        queries[qid] = {}
        m= re.search("weight\((.+?)\)",word_string)
        if m is not None:
            word_string = m.group(1)
            for it in re.finditer("(\d+\.\d+) ([a-z]+)",word_string):
                queries[qid][it.group(2)] = float(it.group(1))
        else:
            print "error text field"
            print word_string
            sys.exit(-1)
    return queries

def main():
    parser =  argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query_file")
    parser.add_argument("background_dir")
    parser.add_argument("output_file")
    args = parser.parse_args()
    queries = get_queries(args.query_file)
    #print queries
    with open(args.output_file,"w") as f:
        for qid in queries:
            f.write("%s %d\n" %(qid,len(queries[qid])))
            for w in queries[qid]:
                f.write("%s %f\n" %(w,queries[qid][w]) )
    with open(os.path.join(args.background_dir,"temp"),'w') as f:
        for qid in queries:
            for w in queries[qid]:
                f.write("%s %f\n" %(w,queries[qid][w]) )

if __name__ == "__main__":
    main()