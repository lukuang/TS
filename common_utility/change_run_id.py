"""
change run id for runs
"""

import os
import json
import sys
import re
import argparse

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_file")
    parser.add_argument("new_runid")
    parser.add_argument("dest_file")
    args=parser.parse_args()
    
    new_lines=[]
    with open(args.run_file) as f:
        for line in f:
            line = line.rstrip()
            parts = line.split()
            parts[2] = args.new_runid
            new_lines.append("\t".join(parts)+"\n") 

    with open(args.dest_file,"w") as f:
        for line in new_lines:
            f.write(line)



if __name__=="__main__":
    main()

