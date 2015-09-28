import argparse
import json
import os,re,sys
import subprocess

def main():
    parser = argparse.ArgumentParser(usage=__doc__)

    parser.add_argument("--code_file","-c", default = "/home/1546/code/simple_queries/get_words_per_doc/get_tf_for_documents")
    parser.add_argument('--disaster_dictionary_file',"-d",default = "/home/1546/data/changed_disaster_dictionary")
    parser.add_argument("--stopword_file","-s", default = "/home/1546/data/new_stopwords")
    parser.add_argument('--result_dir',"-r",default = "/lustre/scratch/lukuang/Temporal_Summerization/TS-2015/data/simple_query_disaster_profile/porter_index/simple_query_results")
    parser.add_argument('--output_dir',"-o",default = "/lustre/scratch/lukuang/Temporal_Summerization/TS-2015/data/simple_query_disaster_profile/porter_index/terms_per_doc")
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

    for f in list(os.walk(args.result_dir))[0][2]:
      m = re.match("(\w+?)-(.+)",f)
      if m is None:
        print "wrong file name",f
        sys.exit(-1)
      else:
        index = indexs[m.group(2)]
        dest_dir = os.path.join(args.output_dir,f)
        if not os.path.isdir(dest_dir):
          os.mkdir(dest_dir)
        os.chdir(dest_dir)
        run_args[1] = index 
        run_args[2] = os.path.join(args.result_dir,f)
        subprocess.call(run_args)

if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print '\nGoodbye!'
