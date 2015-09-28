#include "indri/Repository.hpp"
#include "indri/CompressedCollection.hpp"
#include "indri/LocalQueryServer.hpp"
#include "indri/ScopedLock.hpp"
#include "indri/QueryEnvironment.hpp"
#include <dirent.h>
#include <iostream>
#include <typeinfo>
#include <algorithm>
#include <map>
#include <fstream>
#include <dirent.h>
using namespace std;

map<string,float> get_words( string result_dir){
    ifstream result_file;
    map <string, float> words;
    DIR *dir;
    struct dirent *ent;
    if ( ( dir=opendir( result_dir.c_str() ) ) != NULL ){
        while( (ent = readdir (dir) ) != NULL ){
            string file_name = ent->d_name;
            result_file.open((result_dir + "/" + file_name).c_str());
            if(result_file.is_open()){
                string result_line;
                while(getline(result_file,result_line)){
                    //cout<<result_line<<endl;
                    size_t found =  result_line.find_first_of(" ");
                    if(found==string::npos){
                        cout<<"error line: "<<result_line<<endl;
                        continue;
                    } 
                    string term = result_line.substr(0,found);
                    if(words.find(term)==words.end()){
                        words[term] = 0.0;
                    }
                    
                }
                result_file.close();
            }
            else{
                cout<<"cannot open result "<<file_name<<endl;
            }
        }
        closedir(dir);
    }
    else{
        cout<<result_dir<<endl;
        perror("open dir error!");
        exit(-1);
    }

  return words;
}

map<string,float> get_query_words(char* original_query_file){
    ifstream original_query;
    string line;
    string need_string = "0123456789qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM ";
    bool start = false; 
    map<string,float> words; 
    original_query.open(original_query_file);
    size_t found;
    if(original_query.is_open()){
        while(getline(original_query, line)){

            found = line.find("</title>");
            if (found != string::npos){
                string subline = line.substr(0,found);
                found = subline.find(">");
                string query = subline.substr(found+1);
                found = query.find_first_not_of(need_string);
                while (found != string::npos){
                    query = query.substr(0,found) +" "+ query.substr(found+1);
                   found = query.find_first_not_of(need_string); 
                }
                found = query.find(" ");
                while(found != string::npos){
                    string word =  query.substr(0,found);
                    //cout<<"query term"<<word<<endl;
                    words[word] = .0;
                    query = query.substr(found+1);
                    found = query.find(" ");
                }
                if (query.length()>1){
                    //cout<<"query term"<<query<<endl;
                    words[query] = .0;
                }
            }
            found = line.find("</query>");
            if (found != string::npos){
                string subline = line.substr(0,found);
                found = subline.find(">");
                string query = subline.substr(found+1);
                found = query.find_first_not_of(need_string);
                while (found != string::npos){
                    query = query.substr(0,found) +" "+ query.substr(found+1);
                   found = query.find_first_not_of(need_string); 
                }
                found = query.find(" ");
                while(found != string::npos){
                    string word =  query.substr(0,found);
                    words[word] = .0;
                    query = query.substr(found+1);
                    found = query.find(" ");
                }
                if (query.length()>1){
                    //cout<<"query term"<<query<<endl;
                    words[query] = .0;
                }
            }
        }
    }
    return words;
}

void get_idf(indri::collection::Repository& r, map<string,float>& word_score){
    indri::server::LocalQueryServer local(r);
    int total_doc = local.documentCount();
    for(map<string,float>::iterator it = word_score.begin(); it!=word_score.end(); ++it){
        float idf_score = total_doc*1.0/local.documentCount(it->first);
        //cout<<"term is "<<it->first<<endl;
        //cout<<it->first<<" "<< idf_score<<endl;
        it->second = idf_score;
    }
}

void get_possibility(indri::collection::Repository& r, map<string,float>& word_score, map<string,float>& query_words){
        for(map<string,float>::iterator it = query_words.begin(); it!=query_words.end(); ++it){
        string data = it->first;
        transform(data.begin(), data.end(), data.begin(), ::tolower);
        string stem = r.processTerm( data );
        if(word_score.find(stem)==word_score.end()){
            word_score[stem] = .0;
            //cout<<"insert term"<<data<<endl;
        }
    }
    indri::server::LocalQueryServer local(r);
    int total_term = local.termCount();
    UINT64 totalCount = local.termCount();
    float minimum = 1.0/totalCount;
    for(map<string,float>::iterator it = word_score.begin(); it!=word_score.end(); ++it){
        float possibility_score = 1.0*local.stemCount(it->first)/total_term;
        //cout<<"term is "<<it->first<<endl;
        //cout<<it->first<<" "<< possibility_score<<endl;
        it->second = possibility_score;
        if (possibility_score==0.0){
		it->second = minimum;
        }
    }
    
}

int main(int argc, char** argv){
    indri::collection::Repository r;
    string rep_name = argv[1];
    //int percent_threshold = atoi(argv[2]);
    //string idf_term  = argv[3];
    //float variance_threshold = atof(argv[4]);

    string result_dir = argv[2];
    char* original_query_file = argv[3];
    
    r.openRead( rep_name );
    map<string,float> word_score = get_words( result_dir);
    map<string,float> query_words = get_query_words(original_query_file);
    if (word_score.size()!=0){
        //get_idf(r, word_score);
        get_possibility(r, word_score, query_words);
    }
    for(map<string,float>::iterator it = word_score.begin(); it!=word_score.end(); ++it){
        cout<<it->first<<" "<<it->second<<endl;
    }
    r.close();
}
