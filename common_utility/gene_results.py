import subprocess
import os,sys,re




dest_dir = sys.argv[1]
result_prefix = {}
for f in list(os.walk("./"))[0][2]:
        m = re.search("(test-.+?-result)",f)
        if m is not None:
            if m.group(1) not in result_prefix:
                result_prefix[m.group(1)] = []
            result_prefix[m.group(1)].append(f)
        
for prefix in result_prefix:
        target = os.path.join(dest_dir,prefix)
        #print source,target
        lines = []
        for single_file in result_prefix[prefix]:
             with open(single_file) as f:
                 for line in f:
                     m = re.search("^(.+infolab )\S+(.+\n)$", line)
                     if m is not None:
                         lines.append(m.group(1)+prefix+m.group(2))
                     else:
                         print "error line:"
                         print line
                         sys.exit(-1)
                     
        with open(target,"w") as f:
            for line in lines:
                f.write(line)

