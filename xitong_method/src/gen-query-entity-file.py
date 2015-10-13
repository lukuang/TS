import re,sys,os
import json
import lxml.etree as ET
import argparse
from stemming.porter import stem

def rep(match):
    return match.group(1)+" "+match.group(2)

def get_possible_entities(all_words):
    possible_entities = []
    size = len(all_words)
    for i in xrange(0,size):
        for j in xrange(i,size):
            if i==j:
                possible_entities.append(all_words[i])
                continue
            word = ""
            for k in xrange(i,j+1):
                word += " "+all_words[k]
            #print "add", word
            possible_entities.append(word.lstrip())
    return possible_entities
            


def read_query(query_file):
    tree = ET.parse(query_file)
    root = tree.getroot()
    queries = {}
    query_entity_map = {}
    id_entity_map = {}
    for event in root.iter("event"):
        qid = event.find("id").text
        
        word_string = event.find("query").text
        #print "query is", word_string
        word_string = re.sub("[^A-Za-z0-9]+"," ", word_string.lower())
        word_string = re.sub("([a-z])([A-Z])", rep, word_string)
        all_words = re.findall("\w+",word_string)
        #print all_words
        possible_entities = get_possible_entities(all_words)
        #print "for query",qid,"the possible entities are:\n",possible_entities
        id_entity_map[qid]= possible_entities
        for e in possible_entities:
            stem_entity = stem(e)
            if e not in query_entity_map:
                query_entity_map[stem_entity] = e
    print json.dumps(id_entity_map, indent=4, sort_keys=True)
    print json.dumps(query_entity_map, indent=4, sort_keys=True)
    #raw_input("ok now!")
    return query_entity_map, id_entity_map



def process_phrase(phrase):
    word_string = re.sub("[^A-Za-z0-9]+"," ", phrase.lower())
    word_string = re.sub("([a-z])([A-Z])", rep, word_string)
    word_string = re.sub(" +"," ", word_string)
    return_string = ""
    for word in re.findall("\w+",word_string):
        return_string += stem(word) + " "
    return return_string.strip()




def find_wiki_entities(query_entities, link_file):
    wiki_entites = {}
    i = 0
    with open(link_file) as f:
        for line in f:
            m = re.search("<(http://dbpedia.org/resource/(.+?))> <http://dbpedia.org/ontology/wikiPageWikiLink> <(http://dbpedia.org/resource/(.+?))>", line)
            if m is None:
                print "worng line in link file!"
                print line
                print sys.exit(-1)
            else:
                entity1 = process_phrase(m.group(2))
                entity2 = process_phrase(m.group(4))
                #print "found entities k%sk and k%sk" %(entity1, entity2)
                if entity1 in query_entities:
                    print "found entity %s and %s" %(m.group(1),m.group(2))
                    if entity1 not in wiki_entites:
                        wiki_entites[query_entities[entity1]] = m.group(1)
                if entity2 in query_entities:
                    if entity2 not in wiki_entites:
                        wiki_entites[query_entities[entity2]] = m.group(3)

            i +=1
            if (i%1000000 == 0):
                print "processed %d lines in link file" %i
    return wiki_entites






def main():
    parser = argparse.ArgumentParser(usage = __doc__)
    parser.add_argument('--query_file', "-q", default = "/lustre/scratch/lukuang/Temporal_Summerization/streamcorpus-2014-v0_3_0-ts-filtered/TS14-data/trec2014-ts-topics-test.xml")
    parser.add_argument("--link_file","-l", default = "/lustre/scratch/lukuang/dbpedia/src/page_links_en.nt")
    parser.add_argument("--output_file", "-o", default = "query-ent-dbpedia.map")
    parser.add_argument("--output_json", "-j", default = "query-ent-dbpedia.json")

    args = parser.parse_args()
    query_entity_map, id_entity_map = read_query(args.query_file)
    raw_entites = find_wiki_entities(query_entity_map, args.link_file)
    with open(args.output_json,"w") as f:
        f.write(json.dumps(raw_entites))

    print json.dumps(raw_entites, indent=4, sort_keys=True)

    with open(args.output_file,"w") as f:
        for qid in id_entity_map:
            for key in id_entity_map[qid]:
                if key in raw_entites:
                    f.write("%s : %s : %s\n" %(qid,key,raw_entites[key]) )
            f.write("\n") # just in compliance of the original file to avoid potential problems of loading the map file       


if __name__ == '__main__':
    main()
