import argparse
import json
import os,re,sys
from math import log

def main():
    parser = argparse.ArgumentParser(usage=__doc__)

    parser.add_argument('--disaster_dictionary_file',"-dic",default = "/home/1546/data/changed_disaster_dictionary")
    parser.add_argument('--term_score_dir',"-t",default = "/lustre/scratch/lukuang/Temporal_Summerization/TS-2015/data/simple_query_disaster_profile/porter_index/terms_per_doc")
    parser.add_argument('--query_output_dir',"-q",default = "/lustre/scratch/lukuang/Temporal_Summerization/TS-2015/data/simple_query_disaster_profile/porter_index/json_format/top_terms_per_query")
    parser.add_argument("--num_of_terms","-n",type=int,default = 50)
    args = parser.parse_args()

    indexs = {"apw":"/lustre/scratch/lukuang/AQUAINT/index/apw",
              "nyt": "/lustre/scratch/lukuang/AQUAINT/index/nyt",
              "xie":"/lustre/scratch/lukuang/AQUAINT/index/xie",
              "nyt-before":"/lustre/scratch/lukuang/new-archives/index/before",
              "ap":"/lustre/scratch/lukuang/ap/p_index",
              "wsj":"/lustre/scratch/lukuang/wsj/p_index"}


    #create directories for every index/corpus
    for i in indexs:
        need_d = os.path.join(args.query_output_dir,i)
        if not os.path.exists(need_d):
            os.mkdir(need_d)


    it = os.walk(args.term_score_dir)
    it.next()
    for path_tuple in it:
        #print path_tuple[0]
        #print path_tuple[2]

        num_of_doc = len(path_tuple[2])
        #print "there are",num_of_doc,"documents"
        score_map = {}
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

        
        name = os.path.split(path_tuple[0])[1]
        
        pos = name.find("-")
        if pos == -1:
            print "wrong file name",name
            sys.exit(-1)
        else:
            file_name = name[:pos]
            index_name_dir = name[pos+1:] 

        if len(score_map) == 0:
            print "skip", name
            continue
        

        term_scores = sorted(score_map.items(), key =lambda x: x[1] ,reverse=True)

        i = 0
        #print args.query_output_dir
        #print path_tuple[0]
        with open( os.path.join(args.query_output_dir, index_name_dir, file_name), "w" ) as f:
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





if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print '\nGoodbye!'