"""
generate multiple expansions for different expansion methods

src/ent-exp-query-v3.pl : entity name based expansion
src/rel-exp-query-v2.pl : entity relation based expansion
"""
import os,sys

program_file = sys.argv[1]
dest_dir = sys.argv[2]
model = "/lustre/scratch/lukuang/Temporal_Summerization/TS/xitong_method/data/query_ml_no_stem"
entity_list = "/lustre/scratch/lukuang/Temporal_Summerization/TS/xitong_method/res/ent/text.txt"
ent_num = [1,3,5,7,9,11,13,15];
lambdas = [0.0,0.2,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0]

for num in ent_num:
    for l in lambdas:
        save = os.path.join(dest_dir,str(num)+"-"+str(l))
        execute = "perl %s %s %s %s %s %s" %(program_file, entity_list, str(num), str(l), model, save)
        print execute
        os.system( execute)
