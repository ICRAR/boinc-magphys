// Test wrapper for magphys_validator.cpp

#include <iostream>
#include <stdlib.h>
#include <vector>

using namespace std;

#include "wrapper.h"

int main(int argc, char **argv)
{
    vector<RESULT> results;

    for (int i = 1; i < argc; i++) {
	RESULT	*r = new RESULT(argv[i]);
	int retval = init_result(*r, r->data);
	if (retval) {
	    cerr << "init_result() failed for '" << argv[i] << "': " <<
		retval << endl;
	    exit(1);
	}
	results.push_back(*r);
    }

    vector<RESULT>::iterator i, j;
    for (i = results.begin(); i < results.end(); i++) {
	for (j = i + 1; j < results.end(); j++) {
	    bool res;
	    int retval = compare_results(*i, i->data, *j, j->data, res);
	    if (retval) {
		cerr << "comparing '" << j->name << "' with '" << i->name
		     << "' failed: " << retval << endl;
		exit(1);
	    }
	    cout << i->name << (res ? " == " : " != ") << j->name << endl;
	}
    }

    for (i = results.begin(); i < results.end(); i++)
	cleanup_result(*i, i->data);

    exit(0);
}
