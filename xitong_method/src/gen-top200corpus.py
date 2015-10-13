import os,argparse
import sys
import re
import subprocess
import codecs

def get_docid(result_file):
    docids = {}
    with open(result_file) as f:
        for line in f:
            parts = line.split()
            if parts[2] not in docids:
                docids[parts[2]] = 1
    print "there are %d documents" %len(docids)
    return docids

def store_docs(docids,index,dest_file):
    args = []
    args.append("IndriGetText")
    args.append(index)
    args.append("DID")
    with codecs.open(dest_file, 'wb', 'utf-8') as f:
        for did in docids:
            args[2] = did
            p = subprocess.Popen(args,  stdout=subprocess.PIPE)
            output = p.communicate()[0]
            f.write(output+"\n")


def main():
    parser = argparse.ArgumentParser(usage = __doc__)
    parser.add_argument("--result_file", "-r", default = "ret/top.2000")
    parser.add_argument("--index", "-i", default = "/lustre/scratch/lukuang/all_index/p_index/")
    parser.add_argument("--dest_file", "-d", default = "/lustre/scratch/lukuang/Temporal_Summerization/xitong_method_data/top.2000")
    args = parser.parse_args()

    docids = get_docid(args.result_file)
    store_docs(docids,args.index,args.dest_file)
    print "finished!\n"

if __name__ == '__main__':
    main()