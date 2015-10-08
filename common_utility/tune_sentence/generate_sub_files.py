"""
generate sub result files with highest map,
as found by create_smaller_result_files_for_tuning.py
"""
import argparse
import os
import re
import json

class Result_struct:

    def __init__(self,line):
        self.qid, self.grp_tag, self.run_tag, self.did, self.sid, self.time,self.score = line.split()
        self.score = float(self.score)
        #self.qid = "TS14."+self.qid


#get all files in the result dir with top_threshold as 0.1
def get_result_file_list(result_dir):
    files = []
    for f in list(os.walk(result_dir))[0][2]:
        #m = re.search("test-0.1", f)
        #if m is None:
        #    continue
        files.append(os.path.join(result_dir,f))
        #break #for debugging purpose

    return files

def generate_sub_file(result_file,score_threshold,out_dir):
    results = []
    file_name = os.path.split(result_file)[1]+"-"+str(score_threshold)
    with open(result_file) as f:
        with open(os.path.join(out_dir,file_name), "w") as f_out:    
            for line in f:
                single_result = Result_struct(line)
                if single_result.score >= score_threshold:
                    
                    result_string = "\t".join([single_result.qid, single_result.grp_tag, file_name, single_result.did, single_result.sid, single_result.time,str(single_result.score)])+"\n"
                    f_out.write(result_string)




def main():
    parser = argparse.ArgumentParser(description=__doc__)
    
    parser.add_argument("result_dir")
    parser.add_argument("--score_json","-s",default="score_threshold.json")
    parser.add_argument("out_dir")

    args = parser.parse_args()
    thresholds = json.load(open(args.score_json))
    

    result_files = get_result_file_list(args.result_dir)
    for f in result_files:
        score_threshold = thresholds[ os.path.split(f)[1] ]
        generate_sub_file(f,score_threshold,args.out_dir)


if __name__ ==  "__main__":
    main()
