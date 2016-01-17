import json
import sys
import time
import re
import codecs
import argparse
import os

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
                uid = result[1]
                m = re.search("^\d+-(.+?)$", uid)
                if m is None:
                    print "wrong uid",uid
                    print "error line:\n", line
                    sys.exit(-1)
                else:
                    sub_uid = m.group(1)
                dupid = result[5]
                if dupid == "NULL":
                    pass
                else:
                    m = re.search("\d+-(.+?-\d+)", dupid)
                    if m is not None:
                        dupdid = m.group(1)
                        #print "dupid is",dupdid
                        if dupdid in matches[qid]:
                            if sub_uid in matches[qid]:
                                #print did,"already in matches!!!"
                                continue
                            matches[qid][sub_uid] = matches[qid][dupdid]
                            #print "dup update",did,"for",dupdid,"not relevant"
                        else:
                            pass
                            #print "dup update",did,"for",dupdid,"not relevant"

                    else:
                        print "wrong dupid"
                        print "line"
                        sys.exit(-1)
                if qid not in docs:
                    docs[qid] = {}
                docs[qid][sub_uid] = 1
    return docs

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
                    print nid,"not in nuggets file"
                    continue
                if qid not in matches:
                    matches[qid]= {}
                m = re.search("^\d+-(.+?)$", uid)
                if m is None:
                    print "wrong uid",uid
                    print "error line:\n", line
                else:
                    sub_uid = m.group(1)
                    if sub_uid not in matches[qid]:
                        #print "new doc id",did
                        matches[qid][sub_uid] = []
                    matches[qid][sub_uid].append(nid)
                    #if qid == "TS14.13":
                        #print "insert nid",nid,"for did",did
                    #matches[qid][did] = 1 
    return matches


def output(json_path, sentences, out_file, run_file, matches, updates, requried_qid):
    out_dic = {}
    for doc_name in sentences:
        m = re.search("^(\d+)-", doc_name)
        if m is None:
            print "doc name error", doc_name
            sys.exit(-1)
        else:
            #print "the time is", m.group(1)
            global time
            t = time.gmtime(float(m.group(1)))
            file_name = time.strftime('%Y-%m-%d-%H', t)
            if file_name not in out_dic:
                out_dic[file_name] = {}
            out_dic[file_name][doc_name] = {}

    print "got file names"

    for file_name in out_dic:
        documents = json.load(open(os.path.join(json_path,file_name)))
        for single in documents:
            if single[0] not in sentences:
                continue
            else:
                #print "Found!"
                doc = single[1]
                #print "sentences:"
                doc_sentences = single[1]["sentences"]
                for sid in sentences[single[0]]:
                    sentences[single[0]][sid] = doc_sentences[sid]

    print "got sentence strings"
    index = 0
    f = codecs.open(out_file,"w", "utf-8-sig")
    unsampled = 0
    relevant = 0
    non_relevant = 0
    with open(run_file) as run_f:
        for line in run_f:

            try:
                qid , gid, sub_run_id, doc_name, sid, time, score = (line.rstrip()).split()
                
            except:
                print "wrong line at file", run_file,
                print "line is\n", line
                sys.exit(-1)
            m = re.search("\d+-(.+)$",doc_name)
            if m is None:
                print "error doc name",doc_name
                sys.exit(-1)
            else:
                did = m.group(1)
            qid = "TS14."+qid
            if qid != requried_qid:
                continue
            uid = did + "-" + sid
            if uid not in updates[qid] :
                judge_string = "unsampled"
                unsampled += 1 
            elif uid not in matches[qid]:
                judge_string = "non-relevant"
                non_relevant += 1
            else:
                judge_string = "relevant"
                relevant += 1
            doc_string = "%s %s %s %s %s\n" %(qid, doc_name, sid, judge_string, sentences[doc_name][sid])
            f.write(doc_string)
            index += 1
            if (index%100 == 0):
                print "processed %d lines" %(index)
        
    f.close()
    size = unsampled + non_relevant + relevant
    print "there are %d sentences in total\n%d are unsampled, %d are non_relevant, %d are relevant"\
                  %(size,unsampled,non_relevant,relevant)


def read_results(requried_qid, run_file):
    sentences  = {}
    with open(run_file) as f:
        for line in f:
            try:
                qid , gid, sub_run_id, doc_name, sid, time, score = (line.rstrip()).split()
                
            except:
                print "wrong line at file", run_file,
                print "line is\n", line
            
                sys.exit(-1)
            qid = "TS14."+qid
            if qid != requried_qid:
                continue
            if (doc_name not in sentences):
                sentences[doc_name] = {}
            sentences[doc_name][sid] = 1
    return sentences

def main(args):
    nuggets = get_nuggets(args.nuggets)
    print len(nuggets),"nuggets"
    matches = get_matches(args.matches, nuggets)
    print "got matches"
    updates = get_docs_from_updates_with_duplicate(args.updates,matches)
    #updates = get_docs_from_updates(args.update_file)
    print "got updates"
    sentences = read_results(args.requried_qid, args.run_file)
    print "got sentences"
    output(args.json_path, sentences, args.out_file, args.run_file, matches, updates, args.requried_qid)
    print "finished"

if __name__ == '__main__':
  try:
    argparser = argparse.ArgumentParser(description='Fetch all sentences for one query of a run')
    argparser.add_argument('-j', '--json_path', help='json corpus path', default="/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/json_corpus")
    argparser.add_argument('-n', '--nuggets', help='Nuggets File', default="/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/TS14-data/nuggets.tsv")
    argparser.add_argument('-u', '--updates', help='Updates File', default="/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/TS14-data/updates_sampled.extended.tsv")
    argparser.add_argument('-m', '--matches', help='Matches File', default="/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/TS14-data/matches.tsv")
    argparser.add_argument('requried_qid', help='qid to evaluate')
    argparser.add_argument('run_file', help='run file')
    argparser.add_argument('out_file', help='out file')
    main(argparser.parse_args())
  except KeyboardInterrupt:
    print '\nGoodbye!'
    