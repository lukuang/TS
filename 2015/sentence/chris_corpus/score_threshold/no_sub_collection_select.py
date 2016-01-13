from __future__ import division
import sys
import lxml.etree as ET
from os import listdir
from os.path import isfile, join
import os
#import xml.etree.ElementTree as ET
import re
from myStemmer import pstem as stem
import time
from statistics import Statistics, Document, Query 
#from guppy import hpy
import gc
import operator
import argparse
import json
import math
import heapq
import calendar

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

def get_dir(doc_dir_path):
    onlyfiles = [ f for f in listdir(doc_dir_path) if isfile(join(doc_dir_path,f)) ]
    onlyfiles.sort()
    return onlyfiles

def get_queries(file_path, doc_dir_path, requried_qid,stopwords):
    tree = ET.parse(file_path)
    root = tree.getroot()
    queries = {}
    for event in root.iter("event"):
        qid = event.find("id").text
        if qid!= requried_qid:
            continue
        start = event.find("start").text
        end = event.find("end").text
        

        dir_name = event.find("query").text.lower()
        dir_name = re.sub(" ","_",dir_name)
        word_string =event.find("query").text
        all_words = re.findall("\w+",word_string)
        temp_words=[]
        word_hash = {}
        for word in all_words:
            if word not in word_hash:
                word_hash[word] = 1
                temp_words.append(word.lower())
        temp = map(stem,temp_words)
        words = {}
        #print " ".join(temp_words)
        #print "query words"
        for w in temp:
            #print w
            if w in stopwords:
                continue
            if w not in words:
                words[w] = 1
        doc_dir_path = os.path.join(doc_dir_path,dir_name)
        dirs =  os.listdir(doc_dir_path)
        query=Query(start, end, words, dirs)
        queries[qid]=query

    return queries,doc_dir_path



def repl(m):
    text = re.sub("(http[s]?://)?([A-Za-z0-9\$\-\_\@\&]+\.)+([A-Za-z]+)(/[A-Za-z0-9$-_@&+]+)*", "", m.group(2))
    text = re.sub("[^A-Za-z0-9 \.]", " ",  text)
    return m.group(1) + text.lower() + m.group(3)


def get_sentence_score(s, sentence):
    sentence_model = {}
    for term in s._background:
        if s._background[term] == 0.0:
            continue
        if term in sentence._terms :
            sentence_model[term] = (sentence._terms[term] + s._sentence_mu*s._background[term])/(sentence._length + s._sentence_mu)
        else:
            sentence_model[term] = s._sentence_mu*s._background[term]/(sentence._length + s._sentence_mu)
    #print "sentence score", compute_score(sentence_model, s._query_model)
    return compute_score(s._query_model, sentence_model) 


def filter_document(doc_dir_path, doc_list_path, start, end, single_dir, statistics):
    file_path = os.path.join(doc_dir_path,single_dir)
    candidate_dids = {}
    list_for_hour = join(doc_list_path,single_dir)
    if not isfile(list_for_hour):
        return None
    with open(list_for_hour) as f:
        for line in f:
            m = re.search(".*? (.*?)$", line)
            if m is None:
                print "error line in",list_for_hour
                print "the error line is", line
                sys.exit(-1)
            else:
                did = m.group(1)
                if did not in candidate_dids:
                    candidate_dids[did] = 1
    #h=hpy()
    #print h.heap()
    if len(candidate_dids) == 0:
        return None
    print "open file:" + file_path
    data = json.load(open(file_path))
    
    all_sentences = []
    #h=hpy()
    #print h.heap()
    #del data
    #h=hpy()
    #print h.heap()
    #print "size is:", size
    all_documents = []
    for did in data:

        if did not in candidate_dids:
            continue
        #print "new document", did
        sub_data = data[did]
        time = int(sub_data['time']) 
        
        sentences_dict={}
        if time > int(start) and time < int(end):
            for sid in sub_data["sentences"]:
                sentences_dict[sid] = sub_data["sentences"][sid]
                    #print sentence.find("id").text,":",sentence.find("text").text
                #print "get Document:",did

            temp_doc = Document(sentences_dict,time,statistics)
            documents_score = compute_score(statistics._query_model , temp_doc._model)
            a_document = {}
            a_document["did"] = did
            a_document["doc"] = temp_doc
            a_document["score"] = documents_score
            #print "document",did,"with score",documents_score
            all_documents.append(a_document)
    #print len(all_documents),"documents"
    #return all_documents
    sorted_documents = sorted(all_documents, key = lambda x: x["score"], reverse =True )
    returned_documents = []
    print "there are",len(sorted_documents)
    print "need",min(statistics._doc_num,len(all_documents))
    #for i in range(min(statistics._doc_num, len(sorted_documents))):
    for i in range(min(statistics._doc_num,len(all_documents))):
        returned_documents.append(sorted_documents[i])
    #print len(returned_documents),"documents are chosen"
    return returned_documents

def select_sentence(documents, statistics, words, secs):  
#print "document score for",did, "is", documents_score
    all_sentences =  []
    for doc in documents:
        documents_score = doc["score"]
        did = doc["did"]
        doc_sentences = []
        for sid in doc["doc"]._sentences:
            
            if doc["doc"]._sentences[sid]._length > 25 or doc["doc"]._sentences[sid]._length < 4:
                continue
            sentence_score =  statistics._a*documents_score\
                + statistics._b*get_sentence_score(statistics, doc["doc"]._sentences[sid])
                
            single_sentence = {}
            single_sentence["sid"] = sid
            single_sentence["did"] = did
            single_sentence["time"] = secs
            single_sentence["model"] = doc["doc"]._sentences[sid]._terms
            needed = False
            for term in  single_sentence["model"]:
                if term in words:
                    needed = True
            if not needed:
                continue
            single_sentence["score"] = sentence_score
            #print "add sentence"
            #print did,sid,len(single_doc["model"])
            doc_sentences.append(single_sentence)
        if len(doc_sentences) == 0:
            continue

        purified_sentences = purify_sentence(doc_sentences, statistics)
        all_sentences.extend(purified_sentences)

    
    sorted_sentences = sorted(all_sentences, key = lambda x: x["score"], reverse = True)
    index = 0
    candidate_sentences = []
    for data in sorted_sentences:
        if data["score"] >= statistics._score_thresold:
            candidate_sentences.append(data)
        else:
            break
    #print "get",len(candidate_sentences),"new sentences"
    if len(candidate_sentences) == 0:
        if len(sorted_sentences) != 0:
            candidate_sentences.append(sorted_sentences[0])
    else:
        candidate_sentences = purify_sentence(candidate_sentences, statistics)
    return candidate_sentences    





def load_score(word_score_file):
    word_score ={}
    with open(word_score_file) as f:
        for line in f:
            m = re.search("([^ ]+) (.+)", line)
            if m is not None:
                word_score[m.group(1)] = float(m.group(2))
                word_score[stem(m.group(1))] = float(m.group(2))
                
            else:
                print "error line",line
                sys.exit(-1)
    return word_score

def read_stopwords(stopword_file):
    stopwords = {}
    with open(stopword_file) as f:
        for line in f:
            m = re.search("(\w+)", line)
            if m is not None:
                stopwords[stem(m.group(1).lower())] = 1
    return stopwords

def prepare_data(alpha, beta, distribution, words, background, stopwords, expansion_terms):
    background_model = load_score(background)
    raw_model = json.load(open(distribution))

    expansion_sum = sum(expansion_terms.values())
    for w  in expansion_terms:
        expansion_terms[w] = expansion_terms[w]*1.0/expansion_sum


    feedback_model = {}
    raw_sum = .0
    for w in raw_model:
        if raw_model[w] > 0.001:
            if w in stopwords:
                continue
            feedback_model[w] = raw_model[w] 
            raw_sum += raw_model[w]
        else:
            pass
    query_model = {}
    words_sum = .0
    for w in words:
        words_sum += words[w]
    for w in words:
        words[w] /= words_sum
    for w in feedback_model:
        query_model[w] = alpha*feedback_model[w]/raw_sum
    for w in words:
        if w in query_model:
            query_model[w] += words[w]*(1-alpha-beta)
        else:
            query_model[w] = words[w]*(1-alpha-beta)
    
    for w in expansion_terms:
        if w in query_model:
            query_model[w] += expansion_terms[w]*beta
        else:
            query_model[w] = expansion_terms[w]*beta    

    return query_model, background_model



def compute_score(query_model,document_model):
    score = 0.0
    for w in query_model:
        if w in document_model:
            score += math.log(document_model[w])*query_model[w]
        else:
            pass
            print "error!"
            print w,"is not in background_model!!!"
            sys.exit(-1)
    #print "return score",score
    return score       

def parse_args(para_file, required_qid):
    tree = ET.parse(para_file)
    root = tree.getroot()
    para = {}
    #para["doc_dir_list"] = root.find("doc_dir_list").text
    #para["all_distribution_file"] = root.find("all_distribution_file").text
    para["query_file"] = root.find("query_file").text
    para["doc_dir_path"] = root.find("doc_dir_path").text
    data_dir = os.path.join(root.find("data_dir").text,required_qid)
    para["distribution"] = os.path.join(data_dir,root.find("distribution").text)
    para["background"] = os.path.join(data_dir,root.find("background").text)
    para["output_file"] =  root.find("output_file").text + "-" + required_qid
    para["doc_list_path"] = os.path.join(root.find("doc_list_path").text, required_qid)
    para["alpha"] = float(root.find("alpha").text)
    para["beta"] = float(root.find("beta").text)
    para["stopwords"] = root.find("stopwords").text
    para["mu"] = float(root.find("mu").text)
    return para

def heap_update(result_list, documents):
    for did in documents:
        heapq.heappushpop(result_list, (documents[did], did))
    return 1000

def heap_build(result_list, documents):
    size = len(documents)*0.05
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

def get_length(sentence_model):
    score =.0
    #print "_"*20
    for w in sentence_model:
        #print w,sentence_model[w]
        score += sentence_model[w]*sentence_model[w]
    #print "the length is",score
    return math.sqrt(score)


def cosine_sim(candidate_sentence_model, result_sentence_model):
    score = .0
    for w in candidate_sentence_model:
        #print "word",w
        if w in result_sentence_model:
            #print w, candidate_sentence_model[w], result_sentence_model[w]
            score +=  candidate_sentence_model[w] * result_sentence_model[w]
            #print "score now is", score
    #print  "length:\n",get_length(candidate_sentence_model), get_length(result_sentence_model)

    length = get_length(candidate_sentence_model)*get_length(result_sentence_model)
    if length == 0:
        return 1
    score /= length
    #print "returned score", score
    #sys.exit(0)
    return score

def check_novelty(candidate_sentence_model, result_sentence_model, sim_threshold):
    return (cosine_sim(candidate_sentence_model, result_sentence_model) < sim_threshold)


def single_sentence_check(sentence, sentences_already, statistics):
    duplicate = False
    for single_sentence in sentences_already:
        #print "check novel",sentence["did"], sentence["sid"],single_sentence["did"], single_sentence["sid"]
        if not check_novelty(sentence["model"],single_sentence["model"],\
                statistics._sim_threshold):
                duplicate = True
                #print "discard sentence", sentence["sid"],"in document",sentence["did"], "duplicate with",single_sentence["sid"],"in document",single_sentence["did"]
    return (not duplicate)



def purify_sentence(candidate_sentences, statistics):
    purified_sentences = []
    candidate_sentences.sort(key = lambda x: x["score"], reverse = True)
    purified_sentences.append(candidate_sentences[0])
    for single_sentence in candidate_sentences[1:]:
        if single_sentence_check(single_sentence,purified_sentences, statistics):
            purified_sentences.append(single_sentence)
        else:
            pass
            #print "discard sentence", single_sentence["sid"],"in document",single_sentence["did"]
    #print "there are", len(purified_sentences), "remain new sentences"
    return purified_sentences

def get_expansion_terms(term_dir):
    expansion_terms = {}
    for f in list( os.walk(term_dir) )[0][2]:
        temp = json.load( open( os.path.join(term_dir,f) ) )
        expansion_terms[f] = {}
        for w in temp:
            expansion_terms[f][stem(w)] = temp[w]  
    return expansion_terms    

def update_result(out_sentences, candidate_sentences, statistics):
    #print "start update result"
    #print "old result",len(out_sentences),"sentences"
    old_sentences = list(out_sentences)
    #purified_sentences = purify_sentence(candidate_sentences, statistics)
    #print "there are", len(purified_sentences), "remain new sentences"
    candidate_sentences.sort(key = lambda x: x["score"], reverse = True)
    for single_sentence in candidate_sentences:
        if single_sentence_check(single_sentence, old_sentences, statistics):
            out_sentences.append(single_sentence)
        else:
            pass
            #print "discard sentence", single_sentence["sid"],"in document",single_sentence["did"], "duplicate with",
    return len(out_sentences)

def main():
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("para_file")
    
    #parser.add_argument("b")
    parser.add_argument("--sim_threshold",type=float,default=)
    parser.add_argument("--score_thresold",type=float,default=)
    parser.add_argument("--term_dir", "-r", default = "/lustre/scratch/lukuang/dbpedia/src/expand_query_with_top_terms_in_wiki_doc/newer_2015")
    parser.add_argument("--sentence_mu", type=int,default=)
    parser.add_argument("--a", type=float,default=)
    parser.add_argument("required_qid")
    args = parser.parse_args()
    #if args.required_qid != "11" and args.required_qid != "15":
    #    return None
    #matches = get_matches(args.match_file)
    #rel_docs = matches["TS14.13"]
    #a = int(args.a)*0.1
    score_thresold = args.score_thresold
    sim_threshold = args.sim_threshold
    #b = int(args.b)*0.1
    a = args.a
    b = 1-a
    para = parse_args(args.para_file, args.required_qid)
    stopwords = read_stopwords(para["stopwords"])

    sentence_mu = args.sentence_mu
    run_id = "%f-%f-%d-%f" %(score_thresold,sim_threshold,sentence_mu,a) 
    #run_id = "info_simple"
    para["output_file"] = "test-%f-%f-%d-%f-%s" %(score_thresold, sim_threshold, sentence_mu,a,para["output_file"])
    #top_percent = 0.02
    #sim_threshold = 0.5
    doc_num = 10
    #doc_num = int(args.doc_num)
    expansion_terms = get_expansion_terms(args.term_dir)
    queries, para["doc_dir_path"]= get_queries(para["query_file"], para["doc_dir_path"], args.required_qid,stopwords)
    #result_dirs = 
    out_sentences = {}
    for qid in queries:
        
        if qid != args.required_qid:
            continue
        out_sentences[qid] = []
        doc_result_list = []
        print "required_qid is", args.required_qid
        print "dirs are:"
        for d in queries[qid]._dirs:
            print d
        query_model, background_model = prepare_data(para["alpha"], para["beta"],para["distribution"], queries[qid]._words, para["background"], stopwords, expansion_terms[qid])
            
        statistics = Statistics(query_model, background_model, para["mu"], a, b,\
            sentence_mu, score_thresold, sim_threshold, doc_num, stopwords)
        for single_dir in queries[qid]._dirs:
            string_time = single_dir + "-59-59"
            t = time.strptime(string_time, "%Y-%m-%d-%H-%M-%S")
            secs = calendar.timegm(t)
            candidate_documents = filter_document(para["doc_dir_path"], para["doc_list_path"], queries[qid]._start, queries[qid]._end, single_dir, statistics)
            if candidate_documents == None:
                continue
            candidate_sentences = select_sentence(candidate_documents, statistics, queries[qid]._words,secs)
            if len(candidate_sentences) == 0:
                continue 
            if len(out_sentences[qid]) == 0:
                out_sentences[qid] = list(candidate_sentences)
                size = len(out_sentences[qid])
            else:
                size = update_result(out_sentences[qid], candidate_sentences, statistics)
            #print "now there are",size,"result sentences"
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
            #gc.collect()
            #break
        with open(para["output_file"],"w") as f:
            for sentence in out_sentences[qid]:
                out_string = "%s infolab %s %s %s %s %f\n" %(qid, run_id, sentence["did"], \
                    sentence["sid"], sentence["time"], sentence["score"])
                f.write(out_string)
        break
    print "finished"


if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print '\nGoodbye!'

