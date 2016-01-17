import json
import argparse
import time
import re
import os
import codecs

def read_results(required_qid, run_file):
    sentences  = {}
    with open(run_file) as f:
        for line in f:
            try:
                qid , gid, sub_run_id, doc_name, sid, time, score = (line.rstrip()).split()
                
            except:
                print "wrong line at file", run_file,
                print "line is\n", line
            
                sys.exit(-1)
            if required_qid != qid:
                continue
            if (doc_name not in sentences):
                sentences[doc_name] = {}
            sentences[doc_name][sid] = 1
    print "there are %d sentences" %(len(sentences))
    return sentences


def output(data_dir, sentences, out_file, run_file, required_qid):
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
        documents = json.load(open(os.path.join(data_dir,file_name)))
        for doc_name in out_dic[file_name]:
            for sid in sentences[doc_name]:

                # debug only
                #print "doc_name",doc_name
                #print "sid",sid
   
                #store sentence text 
                sentences[doc_name][sid] = documents[doc_name]["sentences"][sid]["text"]

    print "got sentence strings"

    # write sentence text out
    index = 0
    f = codecs.open(out_file,"w", "utf-8-sig")
    with open(run_file) as run_f:
        for line in run_f:

            try:
                qid , gid, sub_run_id, doc_name, sid, time, score = (line.rstrip()).split()
                
            except:
                print "wrong line at file", run_file,
                print "line is\n", line
                sys.exit(-1)
            if qid != required_qid:
                continue
            doc_string = "%s %s %s %s\n" %(qid, doc_name, sid, sentences[doc_name][sid])
            f.write(doc_string)
            index += 1
            if (index%100 == 0):
                print "processed %d lines" %(index)
        
    f.close()


def main(args):
    args.out_file = args.out_file + args.qid
    args.data_dir = os.path.join(args.data_dir + args.qid)
    sentences = read_results(args.qid, args.run_file)
    print "got sentences"
    output(args.data_dir, sentences, args.out_file, args.run_file, args.qid)
    print "finished"




if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='Fetch all sentences for one query of a run (for TS2015)')
    argparser.add_argument("run_file")
    argparser.add_argument("qid")
    argparser.add_argument("--out_file", "-o", default = "anotated-")
    argparser.add_argument("--data_dir", "-d", default = "/lustre/scratch/lukuang/Temporal_Summerization/TS-2015/data/corpus/") 
    main(argparser.parse_args())
