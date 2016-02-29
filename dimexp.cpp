// Dimensional Expansion by Jory Schossau 2013 (joryschossau@gmail.com)

//description: converts 1D index into higher D indices (0-based indices)
//output: space separated list of dimension indices large dim to small
//input: <1D index integer> <list of dimension sizes until n-1>...
//example:
        //input: dimexp 115 10
        //output: 11 5

#include <iostream>
#include <sstream>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <algorithm>

void showHelp(char* progname);

using namespace std;

bool getRangePair(const char* token, char lower[], char upper[]) {
	char* pos = (char*)strpbrk(token, ":");
	if (pos == NULL) {
		upper=strcpy(upper,token);
		upper[strlen(token)]='\0';
		lower[0]='\0';
		return false;
	}
	strncpy(lower, token, pos-token);
	lower[pos-token]='\0';
	strcpy(upper, pos+1);
	upper[strlen(pos)]='\0';
	if (strlen(upper) == 0)
		return false;
	return true;
}

struct triple{
	int first, second, third;
	triple(int one, int two, int three): first(one), second(two), third(three) {}
};


int main (int argc, char**argv) {

	unsigned int index = 0;
	unsigned int maxSize = 0;
	char lower[16];
	char upper[16];
	vector<triple> ranges;
	int indexToExtract = 0;

	if (argc<3) {
		showHelp(argv[0]);
		return 0;
	}

	bool queriedForTotal=false; // true if user arguments: ? #:# #:# ...

	if ((strcmp(argv[1],"q") == 0) || (strcmp(argv[1],"?") == 0))
		queriedForTotal=true;
	else
		index = atoi(argv[1]);

	for (int i=2; i<argc; i++) {
		if (getRangePair(argv[i], lower, upper)) {
			if (atoi(upper) >= atoi(lower)) {
			//cout << "[" << lower << ":" << upper << "]" << endl;
			ranges.push_back(triple(atoi(lower), atoi(upper), atoi(upper)+1-atoi(lower)));
			} else {
				cout << "warning: range backwards? argument " << i << ": '" << argv[i] << "'" << endl;
				cout << "\tassuming you meant " << upper << ":" << lower << endl;
				//cout << "[" << upper << ":" << lower << "]" << endl;
				//ranges.push_back(make_pair(atoi(upper), atoi(lower)));
			}
		} else {
			if (strlen(lower)==0) {
				indexToExtract = atoi(upper);
			} else
				cout << "input error with argument " << i << ": '" << argv[i] << "'" << endl;
		}
	}

	maxSize=1;
	for (auto &p: ranges) {
		maxSize*=(p.third);
	}
	if (queriedForTotal) {
		cout << maxSize << endl;
	} else { // user wants the indices or an index
		vector<int> result;
		vector<int> resultReversed;
		//stringstream result;
		int dynDimUnit=0;
		int dimIndex=0;
		int rem=index-1;

		if ((index < 1) || (index > maxSize)) {
			cout << "error: index '" << index << "' out of range ('1:" << maxSize << "')" << endl;
			return 1;
		}

		for (int n=ranges.size()-1; n>=0; --n) {
			dynDimUnit=1;
			for (int v=n; v>=0; --v) {
				dynDimUnit*=ranges[v].third;
			}
			dimIndex=rem/dynDimUnit;
			result.push_back(dimIndex);
			rem=rem-dynDimUnit*dimIndex;
		}
		result.push_back(rem);

		resultReversed.resize(result.size()-1);
		reverse_copy(result.begin()+1, result.end(), resultReversed.begin());
		
		if (indexToExtract > 0)
			if (indexToExtract < argc-2)
				cout << resultReversed[indexToExtract-1]+ranges[indexToExtract-1].first;
			else
				cout << "error: target index '" << indexToExtract << "' out of range '1:" << argc-3 << "'" << endl;
		else {
			for (int i=0; i< resultReversed.size(); i++)
				cout << resultReversed[i]+ranges[i].first << " ";
			cout << endl;
		}
	}
	return 0;
}

void showHelp(char* progname) {
	cout << endl;
	cout << "\tDescription: Expands a 1-dimensional number into" << endl;
	cout << "\tan n-dimensional number given specific ranges and an index." << endl;
	cout << "\tindex is 0-based and all numbers are inclusive." << endl;
	cout << "\t useful for performing sweeps of all combinations." << endl;
	cout << endl;
	cout << "\tUsage: " << uppercase << progname << nouppercase
		<< " index start:end start:end start:end..." << endl;
	cout << endl;
	cout << "\tExamples: " << endl;
	cout << "\tInput: " <<  uppercase << progname << nouppercase
		<< " 15 1:9 8:10" << endl;
	cout << "\tOutput: 5 10" << endl;
	cout << endl;
	cout << "\tInput: " << uppercase << progname << nouppercase
		<< " 52 8:10 1:9" << endl;
	cout << "\tOutput: 0 0" << endl;
	cout << "\t(index out of range)" << endl;
	cout << endl;
	cout << "\tInput: " << uppercase << progname << nouppercase
		<< " ? 8:10 1:9" << endl;
	cout << "\tOutput: 27" << endl;
	cout << "\t(number of valid indices)" << endl;
	cout << endl;
}
