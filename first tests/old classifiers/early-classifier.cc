#include <iostream>
#include <fstream>
#include <string>
#include <iomanip>

using namespace std;

string get_last_line() {
    string result = "";
    ifstream fin("/usr/local/share/freeling/en/senses31.src");

    if(fin.is_open()) {
        fin.seekg(0,std::ios_base::end);      //Start at end of file
        char ch = ' ';                        //Init ch not equal to '\n'
        while(ch != '\n'){
            fin.seekg(-2,std::ios_base::cur); //Two steps back, this means we
                                              //will NOT check the last character
            if((int)fin.tellg() <= 0){        //If passed the start of the file,
                fin.seekg(0);                 //this is the start of the line
                break;
            }
            fin.get(ch);                      //Check the next character
        }

        getline(fin,result);
        fin.close();
    }
    return result;
}



int main()
{
    //system(rapper  --input turtle prova.ttl >pars.txt)
    //http://librdf.org/raptor/rapper.html
    //IMPLEMENT TERM SELECTION
    //IMPLEMENT SEARCH
    string cat, term;
    term = "cybersecurity";
    cat = "#Cybersecurity";

    string code = get_last_line();

    int num = stoi(code);
    ++num;
    string code_wn = to_string(num) + "-n";
    code = code_wn + " " + term;

    ofstream myfile;
    myfile.open("/usr/local/share/freeling/en/senses31.src", std::ios_base::app);
    myfile << code;
    myfile.close();

    string code2 = code_wn + " - - - " + cat + "= -";
    myfile.open("/usr/local/share/freeling/common/wn30.src", std::ios_base::app);
    myfile << code2;
    myfile.close();

    //system("/usr/local/bin/analyze -f en.cfg --outlv semgraph --nec --ner --loc --sense ukb --output xml <file.txt >res.xml");
}