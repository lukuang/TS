"""
get the per-query performances of the run with the best performance 
"""

import os,sys
import argparse
import re
from scipy import stats


class Performances:

    class InstanceCreationError (Exception):
        def __init__(self):
            self.value = "At least one of the parameter must be sepcified"

        def __init__(self, args):
            self.value = "Cannot define both of run_dir and all_dir\n"
                 

        def __str__(self):
            return repr(self.value)

    class ContainNoEval (Exception):
        def __init__(self, abspath):
            self.value = "%s contains no evaluation file" %(abspath)
        def __str__(self):
            return repr(self.value)

    class FileFormatError (Exception):
        def __init__(self, file_path):
            self.value = "The format of %s is not correct" %(file_path)
        def __str__(self):
            return repr(self.value)


    def __init__(self,args):
        self._performance_array = {}
        if not args.compare:
            if args.run_dir is not None:
                if args.all_dir is None:
                    self.insert_run(args.run_dir)
                else:
                    raise Performances.InstanceCreationError(args)

            elif args.all_dir is not None:
                for single_dir in os.walk(args.all_dir).next()[1]:
                    self.insert_run(os.path.join(args.all_dir,single_dir) )

            else:
                raise Performances.InstanceCreationError()
        else:
            self.insert_run(args.run_dir)
            self.insert_run(args.run_dir2)


    def insert_run(self,run_dir):
        
        
        abspath = os.path.abspath(run_dir)
        basename = os.path.basename(abspath)
        if basename in self._performance_array:
            return
        try:
            self.get_p_array_per_run(abspath,basename)
        except Performances.ContainNoEval as e:
            print e
        # else:
        #     self._performance_array[basename] = {}
        #     self._performance_array[basename]["abspath"] = abspath
        #     self._performance_array[basename]["array"] = single_performance


    def get_p_array_per_run(self,abspath,basename):
        found = False
        for f in os.walk(abspath).next()[2]:
            if f.endswith("eval"):
                found = True
                self.get_array(os.path.join(abspath,f),basename)

        if not found:
            raise Performances.ContainNoEval(abspath)

    def get_array(self,file_path,basename):
        p_array = []
        best = -100
        found_best = False
        for line in reversed(open(file_path).readlines()):
            parts = line.rstrip().split()
            if not found_best:
                if parts[0]=="TS14.25":
                    found_best = True
                if parts[0]=="AVG":
                    best= float(parts[6])
                    run_id = parts[2] 
            else:
                if best == -100:
                    raise FileFormatError(file_path)
                else:
                    if parts[2] == run_id:
                        p_array.append(float(parts[6]))
        self._performance_array[basename] = {}
        self._performance_array[basename]["run_id"] = run_id
        self._performance_array[basename]["abspath"] = file_path
        self._performance_array[basename]["array"] = list(reversed(p_array))
        self._performance_array[basename]["best"] = best

    def show(self):
        print "There are %d runs" %(len(self._performance_array))
        for basename in self._performance_array:
            print "-"*20
            print "run %s" %basename
            print "best performance: %f" %self._performance_array[basename]["best"] 
            for v in enumerate(self._performance_array[basename]["array"]):
                print "query %d with performace %f" %(v[0]+11,v[1])

    def get_run_ids(self):
        return self._performance_array.keys()

    def calc_ttest(self, id1, id2):
        #print "shape of %s is %d" %(id1, len(self._performance_array[id1]["array"]))
        #print "shape of %s is %d" %(id2, len(self._performance_array[id2]["array"]))
        return stats.ttest_rel(self._performance_array[id1]["array"], self._performance_array[id2]["array"])


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument("--all_dir","-a",default=None)
    parser.add_argument("--run_dir","-r",default=None)
    parser.add_argument("--compare","-c",action ='store_true')
    parser.add_argument("--run_dir2","-r2",default=None)
    args = parser.parse_args()
    performance_array={}
    performances = Performances(args)
    performances.show()
    run_ids = performances.get_run_ids()
    for k in run_ids:
        for l in run_ids:
            if k!=l:
                t,p = performances.calc_ttest(k,l)
                print "for %s and %s:" %(k,l)
                print p
                print "-"*20
                #sys.exit(0) #for debugging purpose, end the program 

if __name__ == "__main__":
    main()
