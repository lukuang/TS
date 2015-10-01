import sys
import re,os
import argparse
from os import listdir
from os.path import isfile, join
#import numpy as np


def get_docs_from_updates(update_file):
    docs = {}
    with open(update_file) as f:
        for line in f:
            result= (line.rstrip()).split()
            m = re.search("^TS", line)
            if m is None:
                print "avoid first line"
                print line
            else:
                qid = result[0]
                doc_name = result[2]
                m = re.search("\d+-(.+)$",doc_name)
                if m is None:
                    print "error doc name",doc_name
                    sys.exit(-1)
                else:
                    did = m.group(1)
                if qid not in docs:
                    docs[qid] = {}
                docs[qid][did] = 1
    return docs

def get_docs_from_updates_with_duplicate(update_file, matches):
    docs = {}
    with open(update_file) as f:
        for line in f:
            result= (line.rstrip()).split()
            m = re.search("^TS", line)
            if m is None:
                print "avoid first line"
                print line
            else:
                qid = result[0]
                doc_name = result[2]
                m = re.search("\d+-(.+)$",doc_name)
                if m is None:
                    print "error doc name",doc_name
                    sys.exit(-1)
                else:
                    did = m.group(1)
                dupid = result[5]
                if dupid == "NULL":
                    pass
                else:
                    m = re.search("\d+-(.+?)-\d+", dupid)
                    if m is not None:
                        dupdid = m.group(1)
                        #print "dupid is",dupdid
                        if dupdid in matches[qid]:
                            if did in matches[qid]:
                                #print did,"already in matches!!!"
                                continue
                            matches[qid][did] = matches[qid][dupdid]
                            #print "dup update",did,"for",dupdid,"not relevant"
                        else:
                            pass
                            #print "dup update",did,"for",dupdid,"not relevant"

                    else:
                        print "wrong dupid"
                        print "line"
                if qid not in docs:
                    docs[qid] = {}
                docs[qid][did] = 1
    return docs


def get_results_other_run(result_dir):
    results = {}
    tf_files = [ f for f in listdir(result_dir) if isfile(join(result_dir,f)) ]
    for a_file in tf_files:
        print "for", a_file
        run_id, single_result = get_single_results(join(result_dir, a_file))
        results[run_id] = single_result
        #sys.exit(-1)
    return results

def get_single_results(result_file):
    single_result = {}
    run_id  = ""
    with open(result_file) as f:
        for line in f:
            try:
                qid , gid, sub_run_id, doc_name, sid, time, score = (line.rstrip()).split()
                
            except:
                print "wrong line at file", result_file,
                print "line is\n", line
            
                sys.exit(-1)
            qid = "TS14."+qid
            run_id = gid + "-" + sub_run_id
            m = re.search("\d+-(.+)$",doc_name)
            if m is None:
                print "error doc name",doc_name
                sys.exit(-1)
            else:
                did = m.group(1)
            if qid not in single_result:
                single_result[qid] = {}
            single_result[qid][did] = score

    return run_id, single_result

def get_nuggets(nuggets_file):
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
    print "size of nuggets", len(nuggets)
    return nuggets



def get_matches(match_file, nuggets):
    matches = {}
    index = 0
    with open(match_file) as f:
        for line in f:
            index += 1
            if index == 1:
                continue
            else:
                qid, uid, nid, m_start, m_end, is_auto = line.split("\t")
                if nid not in nuggets[qid]:
                    continue
                if qid not in matches:
                    matches[qid]= {}
                m = re.search("(.+?)-\d+$", uid)
                if m is None:
                    print "wrong uid",uid
                    print "error line:\n", line
                else:
                    doc_name = m.group(1)
                    m = re.search("\d+-(.+)$",doc_name)
                    if m is None:
                        print "error doc name",doc_name
                        sys.exit(-1)
                    else:
                        did = m.group(1)
                    #print "new doc id",did
                    if did not in matches[qid]:
                        #print "new doc id",did
                        matches[qid][did] = []
                    matches[qid][did].append(nid)
                    #if qid == "TS14.13":
                        #print "insert nid",nid,"for did",did
                    #matches[qid][did] = 1 
    return matches

def get_results(result_file, dids):
    index = 0
    with open(result_file) as f:
        for line in reversed(f.readlines()):
            m =  re.search("(.+?) (.+)", line)
            if m is None:
                print "error line in result file"
                print line
                sys.exit(-1)
            else:
                score = m.group(1)
                doc_name = m.group(2)
                m = re.search("\d+-(.+)$",doc_name)
                if m is None:
                    print "error doc name",doc_name
                    sys.exit(-1)
                else:
                    did = m.group(1)
                    index += 1
                    if index <=5:
                        dids["5"].append(did)
                    if index <=10:
                        dids["10"].append(did)
                    if index <=15:
                        dids["15"].append(did)
                    if index <=20:
                        dids["20"].append(did)






def eval(dids, matches, updates, nuggets, recall_map, num_of_qids):
    catched_nuggets = {}
    nugget_doc_dict = {}
    for did in matches:
        for nid in matches[did]:
            if nid not in nugget_doc_dict:
                #print "new nid",nid
                nugget_doc_dict[nid] = {}
                nugget_doc_dict[nid]["ids"] = {}
                nugget_doc_dict[nid]["text"] = nuggets[nid]
            if did not in nugget_doc_dict[nid]["ids"]:
                nugget_doc_dict[nid]["ids"][did] = 1
                #print "new did",did,"for nid",nid

    for level in dids:
        catched_nuggets[level] = {}
        for did in dids[level]:
            if did in matches:
                for nid in matches[did]:
                    #print "nugget",nid, "in document",did,"added"
                    if nid not in catched_nuggets[level]:
                        catched_nuggets[level][nid] = 1
    #print "-"*20
    #print "total matches",catch,"out of",len(matches)
    for level in catched_nuggets:
        #print "there are %d nuggest at %s" %( len(catched_nuggets[level]),level)
        recall_map[level] += ( len(catched_nuggets[level])*1.0/len(nugget_doc_dict) )/num_of_qids
        #recall_map[level] += ( len(catched_nuggets[level])*1.0/len(dids[level]) )/num_of_qids
    #raw_input("OK")

def compute_recall(q_result_dir, nuggets, matches, updates, recall_map, num_of_qids):
    dids = {}
    dids["5"] = []
    dids["10"] = []
    dids["15"] = []
    dids["20"] = []
    #print "in",q_result_dir
    for result_file in list(os.walk(q_result_dir))[0][2]:
        result_file = os.path.join(q_result_dir,result_file)
        get_results(result_file, dids)
    #for k in dids:
        #print "%d dids in %s" %(len(dids[k]),k)
    eval(dids, matches, updates, nuggets, recall_map, num_of_qids)


def main():
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("result_dir")
    parser.add_argument('-n', '--nuggets_file', help='Nuggets File', default="/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/TS14-data/nuggets.tsv")
    parser.add_argument('-u', '--update_file', help='Updates File', default="/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/TS14-data/updates_sampled.extended.tsv")
    parser.add_argument('-m', '--match_file', help='Matches File', default="/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/TS14-data/matches.tsv")
    args = parser.parse_args()

    num_of_qids = 15
    nuggets = get_nuggets(args.nuggets_file)
    #print len(nuggets),"nuggets"
    matches = get_matches(args.match_file, nuggets)
    print "got matches"
    updates = get_docs_from_updates_with_duplicate(args.update_file,matches)
    #updates = get_docs_from_updates(args.update_file)
    print "got updates"
    print "evaluation"

    average_recall = {}
    

    for run_dir in list(os.walk(args.result_dir))[0][1]:
        m = re.search("\d",run_dir)
        if m is None:
            print "skip",run_dir  
            continue
        recall_map = {}
        recall_map["5"] = 0
        recall_map["10"] = 0
        recall_map["15"] = 0
        recall_map["20"] = 0
        print "run dir",os.path.join(args.result_dir,run_dir)
        for qid in list(os.walk(os.path.join(args.result_dir,run_dir)))[0][1]:
            q_result_dir = os.path.join(args.result_dir,run_dir,qid)
            qid = "TS14."+qid
            compute_recall(q_result_dir, nuggets[qid], matches[qid], updates[qid], recall_map, num_of_qids)

        average_recall[run_dir+"_5"] = recall_map["5"]
        average_recall[run_dir+"_10"] = recall_map["10"]
        average_recall[run_dir+"_15"] = recall_map["15"]
        average_recall[run_dir+"_20"] = recall_map["20"]

    sorted_recall = sorted(average_recall.items(), key = lambda x: x[1], reverse=True)
    for tag, recall in sorted_recall:
        print "%s: %f" %(tag,recall)


if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print '\nGoodbye!'

