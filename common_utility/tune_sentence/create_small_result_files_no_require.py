"""
for each threshold score of the sentences, create result files assiciated with it
so that to tune the score threshold parameter
Note that only the result with highest top_percent is needed.  
"""
from __future__ import division
import re
import os
import argparse
import sys
import json 

class Result_struct:

    def __init__(self,line):
        self.qid, self.grp_tag, self.run_tag, self.did, self.sid, self.time,self.score = line.split()
        self.score = float(self.score)
        self.qid = "TS14."+self.qid


def update_matches_with_duplicate_update(update_file, matches):
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
                m = re.search("^\d+-(.+?-\d+)$",uid)
                if m is None:
                    print "error uid",uid
                    sys.exit(-1)
                else:
                    new_uid = m.group(1)
                dupid = result[5]
                if dupid == "NULL":
                    pass
                else:
                    m = re.search("\d+-(.+?-\d+)", dupid)
                    if m is not None:
                        new_dupdid = m.group(1)
                        #print "dupid is",dupdid
                        if new_dupdid in matches[qid]:
                            matches[qid][new_uid] = matches[qid][new_dupdid]
                            #print "dup update",did,"for",dupdid,"not relevant"
                        else:
                            pass
                            #print "dup update",did,"for",dupdid,"not relevant"

                    else:
                        print "wrong dupid"
                        print "line"
    #return docs

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
                m = re.search("^\d+-(.+?-\d+)$", uid)
                if m is None:
                    print "wrong uid",uid
                    print "error line:\n", line
                else:
                    new_uid = m.group(1)
                    if new_uid not in matches[qid]:
                        #print "new doc id",did
                        matches[qid][new_uid] = nid
                    #matches[qid][did].append(did+"")
                    #if qid == "TS14.13":
                        #print "insert nid",nid,"for did",did
                    #matches[qid][did] = 1 
    return matches


#get all files in the result dir
def get_result_file_list(result_dir):
    files = []
    for f in list(os.walk(result_dir))[0][2]:
        #m = re.search("test-0.1", f)
        #if m is None:
        #    continue
        files.append(os.path.join(result_dir,f))
        #break #for debugging purpose

    return files

def get_best_map_per_file(result_file,matches,nuggets):
    high = -1000
    low = 1000
    results = []
    score_map = {}
    with open(result_file) as f:
        for line in f:

            single_result = Result_struct(line)
            m = re.search("^\d+-(.+?)$", single_result.did)
            if m is None:
                print >>sys.stderr,"wrong result line in file %s" %result_file
                print >>sys.stderr,"the line is %s" %line
                sys.exit(-1)
            else:
                uid = m.group(1)+"-"+single_result.sid
                qid = single_result.qid
                if uid in matches[qid]:
                    score_map[single_result.score] = 0
            results.append(single_result)
    print "the size of score map is %d" %len(score_map)
   
    max_map = -1000
    max_at_score = 0 
    local_nugget = {}
    num_of_result = {}
    for i in xrange(11,26):
        qid = "TS14."+str(i)
        local_nugget[qid] = {}
        num_of_result[qid] = 0
    record_score = 0
    need_record = False 
    for single_result in sorted(results, key = lambda x:x.score, reverse=True):
        qid = single_result.qid
        num_of_result[qid] +=1
        m = re.search("^\d+-(.+?)$", single_result.did)
        if m is not None:
            uid =  m.group(1)+"-"+single_result.sid
            if uid in matches[qid]:
                local_nugget[qid][ matches[qid][uid] ] = 0
            if need_record:
                if single_result.score != record_score:
                    precision = .0
                    recall = .0
                    needed = True
                    for qid in local_nugget:
                        #if num_of_result[qid] == 0:
                        #    needed = False
                        #    continue
                        precision += (len(local_nugget[qid])*1.0/num_of_result[qid]) / 15
                        recall += (len(local_nugget[qid])*1.0/len(nuggets[qid])) / 15
                    #now_map = 2.0/(1.0/precision + 1.0/recall)
                    if needed:
                        now_map = 2.0/(1.0/precision + 1.0/recall)
                    else:
                        now_map = 0
                    score_map[record_score] = now_map
                    if now_map > max_map:
                        max_map = now_map
                        max_at_score = record_score
                    #print "the map for %f is %f" %(record_score,now_map)
                    if single_result.score not in score_map:
                        need_record = False

                    record_score = single_result.score
            if single_result.score in score_map:
                need_record = True
                record_score = single_result.score
    if need_record :
        precision = .0
        recall = .0
        for qid in local_nugget:
            precision += (len(local_nugget[qid])*1.0/num_of_result[qid]) / 15
            recall += (len(local_nugget[qid])*1.0/len(nuggets[qid])) / 15
        now_map = 2.0/(1.0/precision + 1.0/recall)
        if now_map > max_map:
            max_map = now_map
            max_at_score = record_score
        #score_map[record_score] = now_map
        #print "the map for %f is %f" %(record_score,now_map)
    #print "the max map for %f is %f" %(max_at_score,max_map)
    return max_at_score, max_map
    #sys.exit(0)



    # for score in score_map:
    #     #score = (high-low)*i/5.0+low
    #     #print "score",str(score)
    #     out_results = []
    #     file_name = ""
    #     for result in results:
    #         if result.score >= score:
    #             file_name = result.run_tag+"-"+str(score)
    #             result_string = "\t".join([result.qid, result.grp_tag, result.run_tag+"-"+str(score), result.did, result.sid, result.time,str(result.score)])+"\n"
    #             out_results.append(result_string)
    #     with open(os.path.join(dest_dir,file_name), "w") as f:
    #         for result_string in out_results:
    #             f.write(result_string)

    #     #sys.exit(0) #debug purpose



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-n', '--nuggets_file', help='Nuggets File', default="/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/TS14-data/nuggets.tsv")
    parser.add_argument('-u', '--update_file', help='Updates File', default="/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/TS14-data/updates_sampled.extended.tsv")
    parser.add_argument('-m', '--match_file', help='Matches File', default="/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/TS14-data/matches.tsv")
    parser.add_argument("result_dir")
    parser.add_argument("--out_file", "-o", default="score_threshold.json")

    args = parser.parse_args()
    thresholds = {}
    nuggets = get_nuggets(args.nuggets_file)
    print len(nuggets),"nuggets"
    matches = get_matches(args.match_file, nuggets)
    print "got matches"
    update_matches_with_duplicate_update(args.update_file,matches)

    result_files = get_result_file_list(args.result_dir)
    for f in result_files:
        print "the file is %s" %f
        best_score, best_map = get_best_map_per_file(f, matches,nuggets)
        print "for %s the best map is %f and the threshold is %f" %(os.path.split(f)[1], best_map,best_score)
        thresholds[ os.path.split(f)[1] ] = best_score
        #break
    with open(args.out_file,"w") as f:
        f.write(json.dumps(thresholds))
    


if __name__ ==  "__main__":
    main()
