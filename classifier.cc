#include <iostream>
#include <string>
#include <fstream>
#include <vector>
#include <map>
#include <utility>
#include <stdexcept>
#include <sstream> 
#include <numeric>
#include <algorithm>
#include <sys/stat.h>
#include "pugixml.hpp"

using namespace std;
using namespace pugi;

vector<string> pars;
vector<string> found_cat;
map<string, vector<string> > semantic_data;

double min_ratio = 0.96;

vector<string> cso_topics;
map<string, vector<string> >  broaders;
map<string, vector<string> >  narrowers;
map<string, vector<string> >  same_as;
map<string, string> primary_labels;

vector<string> queries;
vector<string> tokens;

string eraseSubStr(string mainStr, string toErase, bool brackets)
{
    size_t pos = mainStr.find(toErase);
    if (pos != std::string::npos) {
        mainStr.erase(pos, toErase.length());
    }
    if (brackets) {
        mainStr.erase(0, 1);
        mainStr.erase(mainStr.size() - 1);
    }
    return mainStr;
}

bool endsWith (string const &fullString, string const &ending) {
    if (fullString.length() >= ending.length()) {
        return (0 == fullString.compare (fullString.length() - ending.length(), ending.length(), ending));
    } else {
        return false;
    }
}

void map_cso (vector<vector<string> > cso) {
    for (int i = 0; i < cso.size(); i++) {
        vector<string> triple = cso[i];

        if (triple[1] == "superTopicOf") {
            broaders[triple[2]].push_back(triple[0]);
            narrowers[triple[0]].push_back(triple[2]);
        }
        else if (triple[1] == "relatedEquivalent")
        {
            same_as[triple[2]].push_back(triple[0]);

        }
        else if (endsWith(triple[1],"rdf-schema#label"))
        {
            cso_topics.push_back(triple[0]);
        }
        else if (triple[1] == "preferentialEquivalent")
        {
            primary_labels[triple[0]] = triple[2];
        }
    }
}


vector<string> read_categories(string filename){
    vector<string> result;

    ifstream myFile(filename);
    if(!myFile.is_open()) throw runtime_error("Could not open file");
    string line;

    //MERGE WITH READ CSO CHANGES
    //FIX LAST COLUMN STRING
    while(getline(myFile, line))
    {
        stringstream ss(line);
        string token;
        vector<string> part;
        while (getline(ss, token, ' ')) {
            part.push_back(token);
        }
        result.push_back(part[0]);
    
    }

    myFile.close();

    return result;
}

vector<vector<string> > read_cso(string filename){
    vector<vector<string> >  result;

    ifstream myFile(filename);
    if(!myFile.is_open()) throw runtime_error("Could not open file");
    string line;

    //FIX LAST COLUMN STRING
    while(getline(myFile, line))
    {
        stringstream ss(line);
        string token;
        vector<string> part;
        int i = 0;
        string ipart;
        while (getline(ss, token, ' ')) {
            if (token != ".") {
                if (i < 2) {
                    part.push_back(token);
                    i++;
                }
                else {
                    ipart.append(token);
                    ipart.append("_");
                }

            }
            else {
                ipart.erase(ipart.size() - 1);
                part.push_back(ipart);
            }

        }
        result.push_back(part);
    
    }

    myFile.close();

    return result;
}
 
template <typename StringType>
size_t levenshtein_distance(const StringType& s1, const StringType& s2) {
    const size_t m = s1.size();
    const size_t n = s2.size();
    if (m == 0)
        return n;
    if (n == 0)
        return m;
    std::vector<size_t> costs(n + 1);
    std::iota(costs.begin(), costs.end(), 0);
    size_t i = 0;
    for (auto c1 : s1) {
        costs[0] = i + 1;
        size_t corner = i;
        size_t j = 0;
        for (auto c2 : s2) {
            size_t upper = costs[j + 1];
            costs[j + 1] = (c1 == c2) ? corner
                : 1 + std::min(std::min(upper, corner), costs[j]);
            corner = upper;
            ++j;
        }
        ++i;
    }
    return costs[n];
}

string lowcase (string s) {
    transform(s.begin(), s.end(), s.begin(), ::tolower);
    return s;
}

double check_sim (string s1, string s2) {
    s1 = lowcase(s1);
    s2 = lowcase(s2);
    size_t distance = levenshtein_distance(s1, s2);

    size_t l1 = s1.size();
    size_t l2 = s2.size();
    size_t lsum = l1 + l2;
    double ratio = ((double)lsum - distance) / (lsum);

    return ratio;
}

void insert_dep(xml_object_range<xml_node_iterator> childs){

    vector<string> sibwords;
    for (xml_node_iterator it3 = childs.begin(); it3 != childs.end(); ++it3) {
        xml_attribute word = it3->last_attribute();
        sibwords.push_back(word.value());
    }

    xml_node parent = childs.begin()->parent();
    string parent_sibword = parent.next_sibling().last_attribute().value();  

    for (xml_node_iterator it3 = childs.begin(); it3 != childs.end(); ++it3) {
        //cout << "Nth Dependency Node: ";        

        string word = it3->last_attribute().value();

        const char_t* att = "token";
        string token = it3->attribute(att).value();
        tokens.push_back(token);

        vector<string> targets = pars;

        //SINGLE
        //queries.push_back("---SINGLE---");
        string checkword = word;
        queries.push_back(checkword);
        for (int i = 0; i < targets.size(); ++i) {
            if (check_sim(checkword, targets[i]) > min_ratio) found_cat.push_back(targets[i]);
        }

        //PARENT
        //SIBLINGS + PARENT???
        //queries.push_back("---PARENT---");
        string parentword = it3->parent().last_attribute().value();
        checkword = word + "_" + parentword;
        queries.push_back(checkword);
        for (int i = 0; i < targets.size(); ++i) {
            if (check_sim(checkword, targets[i]) > min_ratio) found_cat.push_back(targets[i]);
        }

        //SIBLINGS
        //queries.push_back("---SIBLINGS---");
        for (int i = 0; i < sibwords.size(); ++i) {
            if(sibwords[i] != word) {
                checkword = word + "_" + sibwords[i];
                queries.push_back(checkword);

                for (int i = 0; i < targets.size(); ++i) {
                    if (check_sim(checkword, targets[i]) > min_ratio) found_cat.push_back(targets[i]);
                }
            }
        }

        //PARENT SIBLINGS
        //queries.push_back("---PARENT SIBLINGS---");
        xml_node parent = childs.begin()->parent().parent();
        vector<string> parent_sibwords;
        for (xml_node_iterator it3 = parent.begin(); it3 != parent.end(); ++it3) {
            xml_attribute word = it3->last_attribute();
            parent_sibwords.push_back(word.value());
        }

        for (int i = 0; i < parent_sibwords.size(); ++i) {
            if(parent_sibwords[i] != word) {
                checkword = word + "_" + parent_sibwords[i];
                queries.push_back(checkword);

                for (int i = 0; i < targets.size(); ++i) {
                    if (check_sim(checkword, targets[i]) > min_ratio) found_cat.push_back(targets[i]);
                }
            }
        }

        //PARENT NEXT SIBLING
        //queries.push_back("---PARENT NEXT SIBLINGS---");
        checkword = word + "_" + parent_sibword;
        queries.push_back(checkword);
        for (int i = 0; i < targets.size(); ++i) {
            if (check_sim(checkword, targets[i]) > min_ratio) found_cat.push_back(targets[i]);
        }

        /* parent and sibiling words output check
        if (word == "artificial") {
            cout << "Parent Word Nth Dependency Node: ";
            cout << parentword << endl;

            cout << "Sibling Words Nth Dependency Node: ";
            for (int i = 0; i < sibwords.size(); i++) {
                if(sibwords[i] != word) cout << sibwords[i] << endl; 
            }
            cout << endl;
            
            cout << "Parent Sibling Words Nth Dependency Node: ";
            for (int i = 0; i < parent_sibwords.size(); i++) {
                if(parent_sibwords[i] != word) cout << parent_sibwords[i] << endl; 
            }
            
            cout << "Parent Sibling Word Nth Dependency Node: ";
            cout << parent_sibword << endl;
        }
        */

        xml_object_range<xml_node_iterator> childsrec = it3->children();
        
        /*
        queries.push_back("---------------------");
        queries.push_back("---NEXT DEPENDENCY---");
        queries.push_back("---------------------");
        */
       
        //it->empty();
        if (childsrec.begin() != childsrec.end()) {
            insert_dep(childsrec);
        }
        else {
            //cout << "End of Nth Dependency Node." << endl;
        }

    }
}

inline bool file_exists (const std::string& name) {
  struct stat buffer;   
  return (stat (name.c_str(), &buffer) == 0); 
}

int main()
{
    if (!file_exists("pars.nt")) {
        if (!file_exists("topics.ttl")) {
            cout << "import a topics ontology to classify the file" << endl;
            return -1;
        }
        else system("rapper  --input turtle topics.ttl >pars.nt");
    }

    if (!file_exists("res.xml")) {
        if (!file_exists("file.txt")) {
            cout << "create a file.txt with the description to start analyzing" << endl;
            return -1;
        }
        else system("/usr/local/bin/analyze -f en.cfg --outlv semgraph --nec --ner --loc --sense ukb --output xml <file.txt >res.xml");
    }

    if (!file_exists("cso.nt")) {
        cout << "add the cso.nt with the cso ontology to start analyzing" << endl;
        return -1;
    }

    //AI4EU ONTOLOGY PROCESSING
    cout << "\nProcessing AI4EU ontology data...\n\n";

    pars = read_categories("pars.nt");
    
    for (int i = 0; i < pars.size(); i++) {
        pars[i] = eraseSubStr(pars[i], "http://www.ai4eu.eu/ontologies/ai4eu-categories#", true);
    }

    sort( pars.begin(), pars.end() );
    pars.erase( unique( pars.begin(), pars.end() ), pars.end() );

    /* matcher check
    string s1 = "machine_learning";
    string s2 = "MachineLearning";
    cout << check_sim(s1,s2) << endl;
    */

    /*
    //CSO ONTOLOGY PROCESSING
    cout << "\nProcessing CSO ontology data...\n\n";

    vector<vector<string> > cso = read_cso("cso.nt");

    for (int i = 0; i < cso.size(); i++) {
        cso[i][0] = eraseSubStr(cso[i][0], "https://cso.kmi.open.ac.uk/topics/", true);
    }
    
    for (int i = 0; i < cso.size(); i++) {
        cso[i][1] = eraseSubStr(cso[i][1], "http://cso.kmi.open.ac.uk/schema/cso#", true);
    }
    
    for (int i = 0; i < cso.size(); i++) {
        cso[i][2] = eraseSubStr(cso[i][2], "@en", true);
        cso[i][2] = eraseSubStr(cso[i][2], "https://cso.kmi.open.ac.uk/topics/", false);
    }

    map_cso (cso);
    */

    /* cso check
    string out = primary_labels["cyber security"];
    cout << "cso" << out << endl;
    
    for (int i = 0; i < out.size(); i++) {
        cout << out[i] << endl;
    }
    */

    xml_document doc;

    if (!doc.load_file("res.xml")) return -1;

    cout << "\nExtracting semantic data data...\n\n";

    xml_node semantic = doc.child("document").child("semantic_graph");
    
    //FIX LEMMAS
    for (xml_node_iterator it = semantic.begin(); it != semantic.end(); ++it){
        string section = it->name();
        if (section == "entity") {
            const char_t* att = "lemma";
            //const char_t* att = "token";

            string entity = it->attribute(att).value();
            //string entity = it->first_attribute().next_attribute().value();

            xml_object_range<xml_node_iterator> syn = it->children();

            for (xml_node_iterator it2 = syn.begin(); it2 != syn.end(); ++it2) {
                string sinonim = it2->name();
                if (sinonim == "synonym") {
                    string word_syn = it2->first_attribute().value();

                    if (word_syn != entity) {
                        semantic_data[entity].push_back(word_syn);
                        //cout << word_syn << endl;
                    } 
                }
            }
        }

    }

    xml_node tools = doc.child("document").child("paragraph");

    cout << "\nExtracting dependency data...\n\n";

    for (xml_node_iterator it = tools.begin(); it != tools.end(); ++it){
        //cout << "sentence: ";
        xml_attribute sentnum = it->first_attribute();
        //cout << sentnum.value() << endl;
        
        xml_node deps = it->select_node("dependencies").node();

        for (xml_node_iterator it2 = deps.begin(); it2 != deps.end(); ++it2) {
            //cout << "Root Dependency Node: ";
            xml_attribute word = it2->last_attribute();
            //cout << word.value() << endl;

            xml_object_range<xml_node_iterator> childs = it2->children();

            for (xml_node_iterator it3 = childs.begin(); it3 != childs.end(); ++it3) {
                //cout << "Interior Dependency Node: ";
                word = it3->last_attribute();
                //cout << word.value() << endl;

                xml_object_range<xml_node_iterator> childsrec = it3->children();

                insert_dep(childsrec);

            }
        }
    }

    sort( found_cat.begin(), found_cat.end() );
    found_cat.erase( unique( found_cat.begin(), found_cat.end() ), found_cat.end() );

    //AI4EU
    cout << "AI4EU CATEGORIES:" << endl;
    for (int i = 0; i<found_cat.size(); ++i) {
        cout << found_cat[i] << endl;;
    }

    /* CSO
    else {
        for (int i = 0; i<found_cat.size(); ++i) {
            if (!primary_labels[found_cat[i]].empty()) found_cat[i] = primary_labels[found_cat[i]];
        }

        sort( found_cat.begin(), found_cat.end() );
        found_cat.erase( unique( found_cat.begin(), found_cat.end() ), found_cat.end() );    
        
        bool found;
        vector <string> not_found;

        cout << "AI4EU CATEGORIES:" << endl;
        for (int i = 0; i<found_cat.size(); ++i) {
            found = false;

            for (int j = 0; j<pars.size(); ++j) {
                if(check_sim(found_cat[i], pars[j]) > min_ratio) {
                    cout << pars[j] << " (Match) -> ";
                    found = true;
                }

                vector <string> comp = broaders[found_cat[i]];
                for (int k = 0; k<comp.size(); ++k) {
                    if(check_sim(comp[k], pars[j]) > min_ratio) {
                        cout << pars[j] << " (Broad) -> ";
                        found = true;
                    }
                }

                comp = narrowers[found_cat[i]];
                for (int k = 0; k<comp.size(); ++k) {
                    if(check_sim(comp[k], pars[j]) > min_ratio) {
                        cout << pars[j] << " (Narrow) -> ";
                        found = true;
                    }
                }

                comp = same_as[found_cat[i]];
                for (int k = 0; k<comp.size(); ++k) {
                    if(check_sim(comp[k], pars[j]) > min_ratio) {
                        cout << pars[j] << " (Equivalent) -> ";
                        found = true;
                    }
                }
            }
            if (found) cout << found_cat[i] << endl;
            else not_found.push_back(found_cat[i]);
        }
        cout << endl;
        cout << "SUGGESTED CATEGORIES:" << endl;
        for (int i = 0; i<not_found.size(); ++i) {
            cout << not_found[i] << endl;
        }
    }
    */
    
    queries.erase( unique( queries.begin(), queries.end() ), queries.end() );
    tokens.erase( unique( tokens.begin(), tokens.end() ), tokens.end() );

    ofstream queries_file ("queries.txt");
    for (int i = 0; i < queries.size(); ++i) {
        queries_file << queries[i] << endl;
    }
    queries_file.close();

    ofstream tokens_file ("tokens.txt");
    for (int i = 0; i < tokens.size(); ++i) {
        tokens_file << tokens[i] << endl;
    }
    tokens_file.close();

    return 0;
}