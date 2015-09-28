import argparse
import json
import os,re
import subprocess

def generate_query_file(out_dir, index, file_name, query_string):
    start_part = re.sub(" +","_",query_string.lower())
    query_file_name = os.path.join(out_dir ,start_part +"-" + file_name )
    print query_file_name
    f = open(query_file_name,"w")
    f.write("<parameters>\n")
    f.write("<index>"+index+"</index>\n")
    f.write("<count>20</count>\n")
    f.write("<trecFormat>true</trecFormat>\n")
    f.write("<runID>100-doc-test</runID>\n")
    f.write("<query>\n")
    f.write("<number>" + start_part +"-" +file_name + "</number>\n")
    f.write("<text>\n")
    f.write(" #combine(" + query_string + ") \n")
    f.write("</text>\n")
    f.write("</query>\n")
    f.write("</parameters>\n")
    return query_file_name


def main():
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument('--out_dir',"-o", default = "/lustre/scratch/lukuang/Temporal_Summerization/TS-2015/data/simple_query_disaster_profile/porter_index/simple_queries")
    parser.add_argument('--disaster_dictionary_file',"-d",default = "/home/1546/data/changed_disaster_dictionary")
    parser.add_argument('--result_dir',"-r",default = "/lustre/scratch/lukuang/Temporal_Summerization/TS-2015/data/simple_query_disaster_profile/porter_index/simple_query_results")
    args = parser.parse_args()
    query_strings = json.load(open(args.disaster_dictionary_file))
    indexs = {"apw":"/lustre/scratch/lukuang/AQUAINT/index/apw",
              "nyt": "/lustre/scratch/lukuang/AQUAINT/index/nyt",
              "xie":"/lustre/scratch/lukuang/AQUAINT/index/xie",
              "nyt-before":"/lustre/scratch/lukuang/new-archives/index/before",
              "ap":"/lustre/scratch/lukuang/ap/p_index",
              "wsj":"/lustre/scratch/lukuang/wsj/p_index"}
    run_args = []
    run_args.append("IndriRunQuery")
    run_args.append("file_name")
    for q in query_strings:
        for file_name in indexs:
            index = indexs[file_name]
            run_args[1] = generate_query_file(args.out_dir, index, file_name, q)
            p = subprocess.Popen(run_args, stdout=subprocess.PIPE)
            text = p.communicate()[0]
            qid =  os.path.split(run_args[1])[1]
            

            out_file = os.path.join( args.result_dir,  qid)
            #print out_file
            with open(out_file,"w") as f:
                f.write(text)




if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print '\nGoodbye!'
