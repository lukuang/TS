"""
change run id for runs in a directory
"""

import os
import json
import sys
import re
import argparse

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir")
    #parser.add_argument("prefix")
    parser.add_argument("new_prefix")
    parser.add_argument("dest_dir")
    args=parser.parse_args()

    for single_file in os.walk(args.source_dir).next()[2]:
        m = re.search("^(test)(-.+)$",single_file)
        if m is not None:

            run_file = os.path.join(args.source_dir,single_file)
            new_runid = args.new_prefix+m.group(2)
            print "change %s to %s" %()
            dest_file = os.path.join(args.dest_dir,new_runid)
            change_runid_for_single_file(run_file,new_runid,dest_file)
        else:
            print "skip no result file %s" %single_file



def change_runid_for_single_file(run_file,new_runid,dest_file):    
    new_lines=[]
    with open(run_file) as f:
        for line in f:
            line = line.rstrip()
            parts = line.split()
            parts[2] = new_runid
            new_lines.append("\t".join(parts)+"\n") 

    with open(dest_file,"w") as f:
        for line in new_lines:
            f.write(line)



if __name__=="__main__":
    main()

