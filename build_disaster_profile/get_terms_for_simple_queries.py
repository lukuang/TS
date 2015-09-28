import argparse
import json
import os,re
import subprocess

def main():
    parser = argparse.ArgumentParser(usage=__doc__)

    parser.add_argument("--code_file","-c", default = "/home/1546/code/context_info/get_top_words_in_wiki_doc/get_top_words_in_wiki_doc/get_word_distribution")
    parser.add_argument("--stopword_file","-s", default = "/home/1546/data/new_stopwords")
    parser.add_argument('--result_dir',"-r",default = "/lustre/scratch/lukuang/Temporal_Summerization/TS-2015/data/simple_query_disaster_profile/porter_index/simple_query_results")
    parser.add_argument('--output_dir',"-o",default = "/lustre/scratch/lukuang/Temporal_Summerization/TS-2015/data/simple_query_disaster_profile/porter_index/terms")
    args = parser.parse_args()


    indexs = {"apw":"/lustre/scratch/lukuang/AQUAINT/index/apw",
              "nyt": "/lustre/scratch/lukuang/AQUAINT/index/nyt",
              "xie":"/lustre/scratch/lukuang/AQUAINT/index/xie",
              "nyt-before":"/lustre/scratch/lukuang/new-archives/index/before",
              "ap":"/lustre/scratch/lukuang/ap/p_index",
              "wsj":"/lustre/scratch/lukuang/wsj/p_index"}

    run_args = []
    run_args.append(args.code_file)
    run_args.append("need_index")
    run_args.append("need_result")
    run_args.append(args.stopword_file)
    run_args.append("qid")

    for f in list(os.walk(args.result_dir))[0][2]:
        for suffix in indexs:
            if f.find(suffix) != -1:
                index = indexs[suffix]
                print index
                run_args[1] = index
                run_args[2] = os.path.join(args.result_dir,f)
                run_args[4] = f
                p = subprocess.Popen(run_args, stdout=subprocess.PIPE)
                text = p.communicate()[0]
                terms = {}
                for m in re.finditer("(.+?) (.+?)\n",text):
                    terms[m.group(1)] = float(m.group(2))
                sorted_terms = sorted(terms.items(), key =lambda x: x[1] ,reverse=True)
                out_file = os.path.join(args.output_dir,f)
                with open (out_file,"w") as of:
                    for term_tuple in sorted_terms:
                        of.write(term_tuple[0] + " " +str(term_tuple[1]) + "\n")
                break

if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print '\nGoodbye!'
