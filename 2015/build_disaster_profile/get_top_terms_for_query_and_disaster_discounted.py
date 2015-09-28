import argparse
import json
import os,re,sys
from math import log

def main():
    parser = argparse.ArgumentParser(usage=__doc__)

    parser.add_argument('--disaster_dictionary_file',"-dic",default = "/home/1546/data/changed_disaster_dictionary")
    parser.add_argument('--term_score_dir',"-t",default = "/lustre/scratch/lukuang/Temporal_Summerization/TS-2015/data/simple_query_disaster_profile/porter_index/terms_per_doc")
    parser.add_argument('--query_output_dir',"-q",default = "/lustre/scratch/lukuang/Temporal_Summerization/TS-2015/data/simple_query_disaster_profile/porter_index/discounted/json_format/top_terms_per_query")
    parser.add_argument('--disaster_output_dir',"-d",default = "/lustre/scratch/lukuang/Temporal_Summerization/TS-2015/data/simple_query_disaster_profile/porter_index/discounted/json_format/top_terms_per_disaster")
    parser.add_argument("--num_of_terms","-n",type=int,default = 50)
    args = parser.parse_args()

    indexs = {"apw":"/lustre/scratch/lukuang/AQUAINT/index/apw",
              "nyt": "/lustre/scratch/lukuang/AQUAINT/index/nyt",
              "xie":"/lustre/scratch/lukuang/AQUAINT/index/xie",
              "nyt-before":"/lustre/scratch/lukuang/new-archives/index/before",
              "ap":"/lustre/scratch/lukuang/ap/p_index",
              "wsj":"/lustre/scratch/lukuang/wsj/p_index"}



    it = os.walk(args.term_score_dir)
    it.next()
    query_score_map = {}
    for path_tuple in it:
        #print path_tuple[0]
        #print path_tuple[2]

        num_of_doc = len(path_tuple[2])
        #print "there are",num_of_doc,"documents"
        score_map = {}
        frequency_map = {}
        for term_file in path_tuple[2]:
            with open( os.path.join(path_tuple[0],term_file) ) as f:
                for line in f:
                    m = re.search("(\w+) (.+)",line )
                    if m is None:
                        pass
                    else:
                        if m.group(1) not in score_map:
                            score_map[m.group(1)] = 0
                    
                        score_map[m.group(1)] += float(m.group(2))/num_of_doc
                        if m.group(1) not in frequency_map:
                            frequency_map[m.group(1)] = 0
                        frequency_map[m.group(1)] +=1  
        
        name = os.path.split(path_tuple[0])[1]
        
        for t in score_map:
            if frequency_map[t] >= num_of_doc*1.0/2:
                score_map[t] *= log(frequency_map[t]+1,num_of_doc+1)
            else:
                score_map[t] = 0
        if len(score_map) == 0:
            print "skip", name
            continue
        

        query_score_map[name] = score_map
        term_scores = sorted(score_map.items(), key =lambda x: x[1] ,reverse=True)

        i = 0
        #print args.query_output_dir
        #print path_tuple[0]
        with open( os.path.join(args.query_output_dir, name), "w" ) as f:
            out = {}
            for score_tuple in term_scores:
                #f.write(score_tuple[0]+" "+str(score_tuple[1]) +"\n" )
                out[score_tuple[0]] = score_tuple[1]
                i += 1
                if i == args.num_of_terms:
                    break
            out_sum = sum(out.values())
            for t in out:
                out[t] /= out_sum
            f.write(json.dumps(out))


    num_of_index = len(indexs)

    query_strings = json.load(open(args.disaster_dictionary_file))
    for q in query_strings:
        q = q.lower()
        start_part =  re.sub(" +","_",q.lower())
        q_score = {}
        t_frequncy = {}
        num_of_files = 0
        for file_name in indexs:
            
            query_file_name = start_part +"-" + file_name
            print query_file_name
            if query_file_name not in query_score_map:
                continue
            num_of_files +=1  
            for t in query_score_map[query_file_name]:
                if t not in q_score:
                    q_score[t] = 0
                q_score[t] += query_score_map[query_file_name][t]/num_of_index
                if t not in  t_frequncy:
                    t_frequncy[t] = 0
                t_frequncy[t] +=1

        for t in q_score:
            if t_frequncy[t] >= num_of_files*1.0/2:
                q_score[t] *= log(t_frequncy[t],num_of_files)
            else:
                q_score[t] = 0

        if len(q_score) == 0:
            continue

        term_scores = sorted(q_score.items(), key =lambda x: x[1] ,reverse=True)
        i = 0
        #raw_input("press Enter to continue......")

        with open( os.path.join(args.disaster_output_dir,start_part ), "w" ) as f:
            out = {}
            for score_tuple in term_scores:
                #f.write(score_tuple[0]+" "+str(score_tuple[1]) +"\n" )
                out[score_tuple[0]] = score_tuple[1]
                i += 1
                if i == args.num_of_terms:
                    break
            out_sum = sum(out.values())
            if out_sum == 0:
                print q_score
            for t in out:
                out[t] /= out_sum
            f.write(json.dumps(out))


if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print '\nGoodbye!'