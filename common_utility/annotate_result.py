import sys
import re
import argparse
from os import listdir
from os.path import isfile, join
import numpy as np
#import matplotlib.pyplot as plt

def read_updates(update_file, matches):
    updates = {}
    with open(update_file) as f:
        for line in f:
            result= (line.rstrip()).split()
            m = re.search("^(TS)?\d+", line)
            if m is None:
                print "avoid first line"
                print line
            else:
                qid = result[0]
                if qid not in updates:
                    updates[qid] = {}
                original_upid = result[1]

                m = re.search("^\d+-(.+?-\d+)", original_upid)
                if m is None:
                    print "error upid", original_upid
                    print line
                    sys.exit(0)
                else:
                    upid = m.group(1)
                if result[5] == "NULL":
                    dupid = None
                else:
                    original_dupid = result[5]
                    m = re.search("^\d+-(.+?-\d+)", original_dupid)
                    if m is None:
                        print "error uid", original_dupid
                        print line
                        sys.exit(0)
                    else:
                        dupid = m.group(1)
                    if upid not in matches[qid]:
                        if dupid in matches[qid]:
                            matches[qid][upid] = matches[qid][dupid] 
                updates[qid][upid]= dupid
    return updates

def read_nuggets(nuggets_file):
    nuggets = {}
    index = 0
    with open(nuggets_file) as f:
        for line in f:
            index += 1
            if index == 1:
                continue
            else:
                qid, nid, time, importance, length, text = line.split("\t")
                #print  qid, nid, time, importance, length, text
                if qid not in nuggets:
                    nuggets[qid] = {}
                nuggets[qid][nid] = text
    return nuggets


def read_matches(match_file):
    matches = {}
    index = 0
    with open(match_file) as f:
        for line in f:
            index += 1
            if index == 1:
                continue
            else:
                qid, original_uid, nid, m_start, m_end, is_auto = line.split("\t")
                if qid not in matches:
                    matches[qid]= {}
                m = re.search("^\d+-(.+?-\d+)", original_uid)
                if m is None:
                    print "error uid", original_uid
                    print line
                    sys.exit(0)
                else:
                    uid = m.group(1)
                    #print "uid",uid
                if uid not in matches[qid]:
                    matches[qid][uid] = {}
                if nid not in matches[qid][uid]:
                    matches[qid][uid][nid] = 1
                    #print "nid",nid
                    #if qid == "TS14.13":
                        #print "insert nid",nid,"for did",did
                    #matches[qid][did] = 1 
    #sys.exit(0)
    return matches




def main():
    parser = argparse.ArgumentParser(usage=__doc__)
    #parser.add_argument("result_file")
    
    parser.add_argument("-m","--match_file", help="Match File", default = "/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/TS14-data/matches.tsv")
    parser.add_argument("-u","--update_file", help="Update File", default = "/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/TS14-data/updates_sampled.extended.tsv")
    parser.add_argument("-q","--required_qid", help="Required Query Id", default = "TS14.13")
    parser.add_argument("result_file", help="Run Result File",)
    parser.add_argument('-n', '--nuggets_file', help='Nuggets File', default="/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/TS14-data/nuggets.tsv")
    parser.add_argument("-o","--out_file",help="Output File", default="./result_annotated")
    args = parser.parse_args()
    matches = read_matches(args.match_file)
    nuggets = read_nuggets(args.nuggets_file)
    updates = read_updates(args.update_file, matches)
    out_file = args.required_qid +"-annotated"
    f_out = open(out_file,"w")
    with open(args.result_file) as f:
        matched_nuggets = {}
        for line in f:
            line_original = line.rstrip()
            sampled = "none"
            relevant = "none"
            duplicate = "none"
            parts = (line_original).split()
            try:
                qid = "TS14.%d" % int(parts[0])
            except:
                print "error qid", parts[0]
                sys.exit(-1)
            if qid != args.required_qid:
                continue
            m = re.match("\d+-(.+)", parts[3])
            whole_uid = "%s-%s" %(parts[3],parts[4])
            if m is None:
                print "wrong parts 3",parts[3]
                print "wrong result line:"
                print line_original
                sys.exit(-1)
            else:
                did = m.group(1)
                sid = parts[4]
                uid = "%s-%s" %(did,sid)
                if uid not in updates[qid]:
                    sampled  = "false"
                else:
                    sampled = "true"
                    if uid in matches[qid]:
                        relevant = "true"
                        dup = True
                        for nid in matches[qid][uid]:
                            if nid not in matched_nuggets:
                                dup = False
                        if dup :
                            duplicate = "duplicate"
                        else:
                            duplicate = "new"
                    else:
                        relevant = "false"
            f_out.write("\t".join([qid,whole_uid,sampled,relevant,duplicate])+"\n")





if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print '\nGoodbye!'
