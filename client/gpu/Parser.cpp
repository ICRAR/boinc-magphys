#include "Parser.hpp"

Parser::Parser(std::string file)
{
	input.open(file.c_str());
	ignoring = -1;

	//if( !input.is_open() )
	// throw ExcFailed( L"[Parser] Could not open file " + file + L"\n" );
}

void Parser::Ignore(const std::string& start, const std::string& end)
{
	excludeDelims.push_back(start);
	includeDelims.push_back(end);
}

void Parser::Rewind(void)
{
	input.seekg(0, ios::beg);
	input.clear();

	ignoring = -1;
	line.clear();
}

void Parser::Next(void)
{
	getline(input, line);

	if (!input.good())
		return;

	if (line.empty())
	{
		Next();
		return;
	}

	TrimLine(line);
	if (line.empty())
	{
		Next();
		return;
	}
}

void Parser::GetLine(std::string& _line)
{
	_line = line;
}

void Parser::GetTokens(vector<std::string>& tokens)
{
	tokens.clear();
	string buff;

	size_t from = 0;
	while (from < line.length())
	{
		GetNextToken(buff, from);
		tokens.push_back(buff);
	}
}

bool Parser::Good(void)
{
	return input.good();
}

//Could use some work to remove trailing spaces (observation files)
void Parser::TrimLine(string& line)
{
	if (ignoring != -1)
	{
		size_t incPos = line.find(includeDelims[ignoring]);
		if (incPos != string::npos)
		{
			line = line.substr(incPos, line.length());
			ignoring = -1;
			TrimLine(line);
		}
		else
			line.clear();
	}
	else
	{
		for (size_t i = 0; i < excludeDelims.size(); i++)
		{
			size_t excPos = line.find(excludeDelims[i]);
			if (excPos != string::npos)
			{
				string tail = line.substr(excPos, line.length());
				line = line.substr(0, excPos);

				// If the includeDelim is the end of the line just return the head.
				if (includeDelims[i] == "\n")
					return;

				ignoring = i;
				TrimLine(tail);
				line += tail;
				return;
			}
		}
	}
}

void Parser::GetNextToken(std::string& container, size_t& from)
{
	size_t to = from;
	while (from != line.length() && (line[from] == ' ' || line[from] == '\t' || line[from] == '\r'))
		from++;

	to = from + 1;
	while (to != line.length() && line[to] != ' ' && line[to] != '\t' && line[to] != '\r')
		to++;

	container = line.substr(from, to - from);

	from = to;
}