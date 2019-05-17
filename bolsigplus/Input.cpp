#include <iostream> 
#include <fstream> 
  
using namespace std; 

int main() 
{ 
    fstream fio; 
    string line; 
  
    // by default openmode = ios::in|ios::out mode 
    // Automatically overwrites the content of file, To append 
    // the content, open in ios:app 
    // fio.open("sample.txt", ios::in|ios::out|ios::app) 
    // ios::trunc mode delete all conetent before open 
    fio.open("sample.txt", ios::trunc | ios::out | ios::in); 
	
	fio >> line;
    cout << line;
    while (fio) {
        getline(cin, line);
        if (line == "-1") 
            break;
        fio << line << endl; 
    } 

    fio.seekg(0, ios::beg); 
  
    while (fio) {
        getline(fio, line); 
        cout << line << endl; 
    } 
    fio.close(); 
  
    return 0; 
} 
