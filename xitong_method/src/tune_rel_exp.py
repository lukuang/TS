"""
generate multiple expansions for rel-exp-query-v2.pl
"""
import os,sys

dest_dir = sys.argv[1]
model = "/lustre/scratch/lukuang/Temporal_Summerization/TS/xitong_method/data/query_ml"
entity_list = "/lustre/scratch/lukuang/Temporal_Summerization/TS/xitong_method/res/ent/text.txt"
ent_num = [1,3,5,7,9,11,13,15];
lambdas = [0.0,0.2,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0]

for num in ent_num:
    for l in lambdas:
        save = os.path.join(dest_dir,str(num)+"-"+str(l))
        execute = "perl src/rel-exp-query-v2.pl %s %s %s %s %s" %(entity_list, str(num), str(l), model, save)
        print execute
        os.system( execute)