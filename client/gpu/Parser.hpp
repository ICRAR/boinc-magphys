#include <vector>
#include <sstream>
#include <fstream>
#include <iostream>
#include <sstream>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <cstring>
#include <string>
#include <cctype>
#include <stdlib.h>

using namespace std;

class Parser
{
public:
	Parser(std::string file);

	virtual void Ignore(const std::string& start, const std::string& end);
	virtual void Rewind(void);
	virtual void Next(void);
	virtual void GetLine(std::string& line);
	virtual void GetTokens(vector<std::string>& tokens);
	virtual bool Good(void);
	virtual void GetNextToken(std::string& container, size_t& from);

	std::stringstream		 stream;

protected:
	void                     TrimLine(std::string& line);

	int                      ignoring;
	vector<std::string> 	 excludeDelims;
	vector<std::string> 	 includeDelims;
	ifstream            	 input;
	std::string				 line;
};