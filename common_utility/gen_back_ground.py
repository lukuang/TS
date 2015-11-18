"""
read result indri query file from the axiomatic approach and generate a file for generating backgroud
file for my method
"""

import re
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
        m= re.search("weight\((.+?)\)",word_string)
        if m is not None:
            word_string = m.group(1)
            all_words = re.findall("\w+",word_string)
            queries[qid] = all_words
        else:
            print "error text field"
            print word_string
            sys.exit(-1)
    return queries

def main():
    parser =  argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query_file")
    parser.add_argument("dest_dir")
    args = parser.parse_args()
    queries = get_queries(args.query_file)
    print queries

if __name__ = "__main__":
    main()