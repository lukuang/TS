from __future__ import division
import sys
import os
import lxml.etree as ET
#import xml.etree.ElementTree as ET
import re
from stemming.porter import stem
import time
from statistics import Statistics, Document, Query 
#from guppy import hpy
import gc
import operator
import argparse
import json
import math
import heapq

def pos_earlier(first,second):
    first=int(first)
    second=int(second)
    if(first>second):
        return 1
    elif(first<second):
        return 2
    else:
        return 0


def is_earlier(dir_name,actual_time):
    m=re.match('(\d+)-(\d+)-(\d+)-(\d+)',dir_name)
    check=pos_earlier(m.group(1),actual_time.tm_year)
    if(check==0):
        check=pos_earlier(m.group(2),actual_time.tm_mon)
        if(check==0):
            #print "check",m.group(3)
            check=pos_earlier(m.group(3),actual_time.tm_mday)
            if(check==0):
                #print "check",m.group(4)
                check=pos_earlier(m.group(4),actual_time.tm_hour)
                return check
            else:
                return check
        else:
            return check
    else:
        return check

def find_directories(start,end,file_name):
    dirs=[]
    begin=False
    with open(file_name,'r') as f:
        for line in f:
            #print line
            if(not begin):
                check=is_earlier(line.rstrip(),start)
                #print "the return is", check
                if(check!=2):
                    begin=True
                    #print "start to insert"
                    dirs.append(line.rstrip())
            else:
                check=is_earlier(line.rstrip(),end)
                #print "return is", check
                if(check!=1):
                    dirs.append(line.rstrip())
                    #print "insert:", line.lstrip()
                else:
                    break
    return dirs

def get_queries(file_path, doc_dir_list, requried_qid):
    tree = ET.parse(file_path)
    root = tree.getroot()
    queries = {}
    for event in root.iter("event"):
        qid = event.find("id").text
        if qid!= requried_qid:
            continue
        start = event.find("start").text
        end = event.find("end").text
        
        word_string =event.find("query").text+" "+event.find("title").text
        all_words = re.findall("\w+",word_string)
        temp_words=[]
        word_hash = {}
        for word in all_words:
            if word not in word_hash:
                word_hash[word] = 1
                temp_words.append(word.lower())
        temp=map(stem, temp_words)
        words = {}
        for w in temp:
            if w not in words:
                words[w] = 1
        dirs=find_directories(time.gmtime(float(start)),time.gmtime(float(end)),doc_dir_list)
        query=Query(start, end, words, dirs)
        queries[qid]=query

    return queries

def repl(m):
    text = re.sub("(http[s]?://)?([A-Za-z0-9\$\-\_\@\&]+\.)+([A-Za-z]+)(/[A-Za-z0-9$-_@&+]+)*", "", m.group(2))
    text = re.sub("[^A-Za-z0-9 \.]", " ",  text)
    return m.group(1) + text.lower() + m.group(3)

def get_documents_scores(doc_dir_path, start, end, single_dir, statistics, query_words):
    file_path = doc_dir_path+single_dir
    #h=hpy()
    #print h.heap()
    print "open file:"+ file_path
    data = json.load(open(file_path))
    documents = {}
    already_in  = {}
    #h=hpy()
    #print h.heap()
    #del data
    #h=hpy()
    #print h.heap()
    #print "size is:", size
    for single_doc in data:
        did = single_doc[0]
        sub_data = single_doc[1]
        time = int(sub_data['time']) 
        sentences_dict={}
        if time > int(start) and time < int(end):
            for sid in sub_data["sentences"]:
                sentences_dict[sid] = sub_data["sentences"][sid]
                    #print sentence.find("id").text,":",sentence.find("text").text
                #print "get Document:",did

            temp_doc = Document(sentences_dict,time,statistics, statistics._query_model )
            if temp_doc._needed == False:
                #print "discard document",did
                continue
            m = re.search("^(\d+)-(.+)", did)
            if m is not None:
                if m.group(2) in already_in:
                    continue
                else:
                    already_in[m.group(2)] = 1
            else:
                print "error did", did
                sys.exit(-1)
            documents[did] = compute_score(statistics._query_model , temp_doc._model)

        else:
            continue
    return documents    

def load_score(word_score_file):
    word_score ={}
    with open(word_score_file) as f:
        for line in f:
            m = re.search("([^ ]+) (.+)", line)
            if m is not None:
                word_score[m.group(1)] = float(m.group(2))
                
            else:
                print "error line",line
                sys.exit(-1)
    return word_score

def prepare_data(alpha, belta, distribution, words, background, expansion_terms):
    background_model = load_score(background)
    print "size of background is %d" %(len(background_model))
    #print background_model
    raw_model = json.load(open(distribution))

    expansion_sum = sum(expansion_terms.values())
    for w  in expansion_terms:
        expansion_terms[w] = expansion_terms[w]*1.0/expansion_sum


    feedback_model = {}
    raw_sum = .0
    for w in raw_model:
        if raw_model[w] > 0.001:
            feedback_model[w] = raw_model[w] 
            raw_sum += raw_model[w]
        else:
            pass
    sorted_feedback_model = sorted(feedback_model.items(), key = lambda x: x[1], reverse = True)
    query_model = {}
    words_sum = .0
    for w in words:
        words_sum += words[w]
    for w in words:
        words[w] /= words_sum
    for w,s in sorted_feedback_model:
        query_model[w] = alpha*feedback_model[w]/raw_sum

    for w in words:
        if w in query_model:
            query_model[w] += words[w]*(1-alpha-belta)
        else:
            query_model[w] = words[w]*(1-alpha-belta)

    for w in expansion_terms:
        if w in query_model:
            query_model[w] += expansion_terms[w]*belta
        else:
            query_model[w] = expansion_terms[w]*belta

    
    

    return query_model, background_model

def rank_documents(sorted_documents, statistics):
    doc_scores = {}
    for did, single_doc in sorted_documents:
        doc_scores[did] = compute_score(statistics._query_model, single_doc._model)
    return doc_scores

def compute_score(query_model,document_model):
    score = 0.0
    for w in query_model:
        if w in document_model:
            score += math.log(document_model[w])*query_model[w]
        else:
            print "error!"
            print w,"is not in background_model!!!"
            sys.exit(-1)
    #print "return score",score
    return score       

def parse_args(para_file, data_dir,qid):
    tree = ET.parse(para_file)
    root = tree.getroot()
    para = {}
    para["doc_dir_list"] = root.find("doc_dir_list").text
    #para["all_distribution_file"] = root.find("all_distribution_file").text
    para["query_file"] = root.find("query_file").text
    para["doc_dir_path"] = root.find("doc_dir_path").text
    para["distribution"] = os.path.join(data_dir,qid,root.find("distribution").text)
    para["background"] = os.path.join(data_dir,qid,root.find("background").text)
    #para["output_dir"] = root.find("output_dir").text
    #para["alpha"] = float(root.find("alpha").text)
    #para["mu"] = float(root.find("mu").text)
    return para

def heap_update(result_list, documents):
    for did in documents:
        heapq.heappushpop(result_list, (documents[did], did))
    return 1000

def heap_build(result_list, documents):
    size = 20
    start_update =False
    processed = 0
    for did in documents:
        if(start_update):
            heapq.heappushpop(result_list, (documents[did], did))
        else:
            heapq.heappush(result_list, (documents[did], did))
            processed += 1
            if(processed >= size):
                start_update = True
    return len(result_list)

def get_expansion_terms(term_dir):
    expansion_terms = {}
    for f in list( os.walk(term_dir) )[0][2]:
        expansion_terms[f] = json.load( open( os.path.join(term_dir,f) ) )
    return expansion_terms

def get_matches(match_file):
    matches = {}
    index = 0
    with open(match_file) as f:
        for line in f:
            index += 1
            if index == 1:
                continue
            else:
                qid, uid, nid, m_start, m_end, is_auto = line.split("\t")
                if qid not in matches:
                    matches[qid]= {}
                m = re.search("(.+?)-\d+$", uid)
                if m is None:
                    print "wrong uid",uid
                    print "error line:\n", line
                else:
                    did = m.group(1)
                    if did not in matches[qid]:
                        matches[qid][did] = []
                    matches[qid][did].append(nid)
                
    return matches

def main():
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("para_file")
    parser.add_argument("--data_dir", "-d", default = "NEED TO CHANGE")
    parser.add_argument("qid")
    parser.add_argument("alpha",type=int)
    parser.add_argument("belta",type=int)
    parser.add_argument("run_id",type=int)
    #parser.add_argument("mu",type=int)
    parser.add_argument("--term_dir", "-r", default = "NEED TO CHANGE")
    args = parser.parse_args()
    #matches = get_matches(args.match_file)
    #rel_docs = matches["TS14.13"]
    para = parse_args(args.para_file,args.data_dir, args.qid)
    para["output_dir"] = os.path.join("./",str(args.alpha)+"_"+str(args.belta),args.qid)
    para["mu"] = 8000
    #para["mu"]=args.mu*2000
    para["alpha"]=args.alpha*0.2
    para["belta"]=args.belta*0.2

    queries = get_queries(para["query_file"], para["doc_dir_list"], args.qid)

    expansion_terms = get_expansion_terms(args.term_dir)
    #result_dirs = 
    for qid in queries:
        
        if qid != args.qid:
            continue
        doc_result_list = []
        size = 0
        query_model, background_model = prepare_data(para["alpha"], para["belta"], para["distribution"], queries[qid]._words, para["background"], expansion_terms[qid])
        statistics = Statistics(query_model, background_model, para["mu"])
        dirs_needed = {}
        #print "len is", len(queries[qid]._dirs)
        #continue
        index = 0
        size = len(queries[qid]._dirs)
        gap = size//59
        for i in range(1,60):
            dirs_needed[i] = []
            if i != 59:
                for j in range(gap):
                    dirs_needed[i].append(queries[qid]._dirs[index])
                    index += 1
            else:
                for j in range(size - gap*58):
                    dirs_needed[i].append(queries[qid]._dirs[index])
                    index += 1
        print "size is", len(dirs_needed[int(args.run_id)])

        for single_dir in dirs_needed[int(args.run_id)]:

            documents = get_documents_scores(para["doc_dir_path"], queries[qid]._start, queries[qid]._end, single_dir, statistics, queries[qid]._words)
            #score_string = json.dumps(documents)
            #sorted_documents = sorted(documents.items(), key = lambda x: x[1])
            #doc_scores = rank_documents(sorted_documents, statistics)
            size = heap_build(doc_result_list, documents)
            with open(os.path.join(para['output_dir'], single_dir),"w") as f:
                for i in range(len(doc_result_list)):
                    item = heapq.heappop(doc_result_list)
                    f.write(str(item[0]) +" "+ str(item[1]) +"\n")
            doc_result_list = []
            """
            for did in documents:

                if did in doc_result_list:
                    print "dup doc id",did,"is ignored"
                    doc_result_list.pop(did)
                    continue
                else:
                    doc_result_list[did] = documents[did]
            """
            #with open(para["output_file"],"a") as f:
                #f.write(score_string)
            gc.collect()
        break
    print "finished"


if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print '\nGoodbye!'

