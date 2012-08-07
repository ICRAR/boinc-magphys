// Validator for magphys FIT files
#include <stdlib.h>
#include <math.h>

#include <iostream>
#include <fstream>
#include <string>
#include <vector>
//using std::iostream;
//using std::fstream;
//using std::string;
//using std::vector;

using namespace std;

#include "gzstream.h"
#include "error_numbers.h"
#include "boinc_db.h"
#include "sched_util.h"
#include "validate_util.h"
#include "sched_msgs.h"

const std::string whiteSpaces( " \f\n\r\t\v" );


void trimRight( std::string& str,
      const std::string& trimChars = whiteSpaces )
{
    std::string::size_type pos = str.find_last_not_of( trimChars );
    str.erase( pos + 1 );
}

class fit_number {
private:
    double val;
    static const double fuzz;	// Relative comparison tolerance

public:
    fit_number(double x) { val = x; }
    friend bool operator==(const fit_number &x, const fit_number &y);
    //    bool operator==(const fit_number &x);
};

const double fit_number::fuzz = 1e-4;	// Relative comparison tolerance

// Each FIT record comprises either a comment (which is compared as a
// string) or a set of numbers (store as a vector of doubles)
class fit_record {
private:
    enum { INIT, COMMENT, DATA, NUMERIC } ftrec_type;
    string ftrec_str;
    vector<fit_number> ftrec_num;
    void ident_type();
    void parse(size_t len);

public:
    fit_record(string &str) : ftrec_type(INIT), ftrec_str(str), ftrec_num() {}
    //friend bool operator==(fit_record &x, fit_record &y);
    bool operator==(fit_record &x);
};

typedef vector<fit_record> fit_file;

// The standard <vector>== uses const, whick breaks the lazy evaluation
inline bool operator==(vector<fit_record>& x, vector<fit_record>& y)
{
    return (x.size() == y.size() && std::equal(x.begin(), x.end(), y.begin()));
}

inline bool operator==(vector<fit_number>& x, vector<fit_number>& y)
{
    return (x.size() == y.size() && std::equal(x.begin(), x.end(), y.begin()));
}
// Fuzzily compare two fit_numbers.
#if 0
bool fit_number::operator==(const fit_number &x)
{
    // NaN is not equal to anything else
    if (isnan(this->val) || isnan(x.val))
        return (false);

    // Infinities are equal
    if (isinf(this->val))
        return (isinf(x.val));
    // this->val is finite
    if (isinf(x.val))
        return (false);

    // If one side is zero, allow the other side to be <= fuzz
    if (this->val == 0.0)
        return (fabs(x.val) <= fuzz);
    if (x.val == 0.0)
        return (fabs(this->val) <= fuzz);

    // Both values must have the same sign
    if (signbit(this->val) != signbit(x.val))
        return false;

    // given X > Y, allow equal if Y > (X * (1 - fuzz))
    double a = fabs(this->val);
    double b = fabs(x.val);

    double c = fmax(a, b);
    double d = fmin(a, b);

    return (d >= c * (1.0 - fuzz));
}
#else
bool operator==(const fit_number &x, const fit_number &y)
{
    // NaN is not equal to anything else
    if (isnan(x.val) || isnan(y.val))
        return (false);

    // Infinities are equal
    if (isinf(x.val))
        return (isinf(y.val));
    // x.val is finite
    if (isinf(y.val))
        return (false);

    // If one side is zero, allow the other side to be <= fuzz
    if (x.val == 0.0)
        return (fabs(y.val) <= fit_number::fuzz);
    if (y.val == 0.0)
        return (fabs(x.val) <= fit_number::fuzz);

    // Both values must have the same sign
    if (signbit(x.val) != signbit(y.val))
        return false;

    // given X > Y, allow equal if Y > (X * (1 - fuzz))
    double a = fabs(x.val);
    double b = fabs(y.val);

    double c = fmax(a, b);
    double d = fmin(a, b);

    return (d >= c * (1.0 - fit_number::fuzz));
}
#endif

// Initial identification of record type - data or comment
void fit_record::ident_type()
{
    size_t pos = this->ftrec_str.find_first_not_of(" \t");
    this->ftrec_type = (pos == string::npos || this->ftrec_str[pos] == '#') ?
               COMMENT : DATA;
}

// Parse the record into ftrec_num.  'len' is an estimate of the number
// of numbers.
void fit_record::parse(size_t len)
{
    this->ftrec_num.reserve(len);
    const char *s = this->ftrec_str.c_str();
    while (*s) {
        char *ep;
        double val = strtod(s, &ep);
        if (s == ep || (*ep != ' ' && *ep != '\t' && *ep != '\0')) {
            this->ftrec_num.push_back(NAN);
            break;
        }
        this->ftrec_num.push_back(val);
        s = ep;
    }
}

// Compare two records
#if 1
bool fit_record::operator==(fit_record &x)
{
    log_messages.printf(MSG_DEBUG, "'%s' == '%s'\n", this->ftrec_str.c_str(), x.ftrec_str.c_str());

    // If one side hasn't been parsed, start with a string compare
    if ((this->ftrec_type == INIT || x.ftrec_type == INIT)
        && this->ftrec_str == x.ftrec_str) {
        log_messages.printf(MSG_DEBUG, "Match 01\n");
        return true;
    }

    // Identify COMMENT or DATA as needed for each side
    if (this->ftrec_type == INIT)
        this->ident_type();
    if (x.ftrec_type == INIT)
        x.ident_type();

    // comment fields must compare identical
    if (this->ftrec_type == COMMENT) {
        log_messages.printf(MSG_DEBUG, "Match 02\n");
        return (x.ftrec_type == COMMENT && this->ftrec_str == x.ftrec_str);
    }

    // At this point, 'this' is data.  'x' has to be to match
    if (x.ftrec_type != DATA && x.ftrec_type != NUMERIC) {
        log_messages.printf(MSG_DEBUG, "Match 03\n");
        return (false);
    }

    // Accept if bytewise identical
    if (this->ftrec_str == x.ftrec_str) {
        log_messages.printf(MSG_DEBUG, "Match 04\n");
        return (true);
    }

    // Parse records as necessary.
    if (this->ftrec_type == DATA)
        this->parse(x.ftrec_num.size());
    if (x.ftrec_type == DATA)
        x.parse(this->ftrec_num.size());

    // Do fuzzy numeric compare
    log_messages.printf(MSG_DEBUG, "Match 05\n");
    return (this->ftrec_num == x.ftrec_num);
}
#else
bool operator==(fit_record &x, fit_record &y)
{
    // If one side hasn't been parsed, start with a string compare
    if ((x.ftrec_type == fit_record::INIT || y.ftrec_type == fit_record::INIT)
        && x.ftrec_str == y.ftrec_str)
        return true;

    // Identify COMMENT or DATA as needed for each side
    if (x.ftrec_type == fit_record::INIT)
        x.ident_type();
    if (y.ftrec_type == fit_record::INIT)
        y.ident_type();

    // comment fields must compare identical
    if (x.ftrec_type == fit_record::COMMENT)
        return (y.ftrec_type == fit_record::COMMENT && x.ftrec_str == y.ftrec_str);

    // At this point, 'this' is data.  'x' has to be to match
    if (y.ftrec_type != fit_record::DATA && y.ftrec_type != fit_record::NUMERIC)
        return (false);

    // Accept if bytewise identical
    if (x.ftrec_str == y.ftrec_str)
        return (true);

    // Parse records as necessary.
    if (x.ftrec_type == fit_record::DATA)
        x.parse(y.ftrec_num.size());
    if (y.ftrec_type == fit_record::DATA)
        y.parse(x.ftrec_num.size());

    // Do fuzzy numeric compare
    return (x.ftrec_num == y.ftrec_num);
}
#endif

// This takes a result, reads its output file(s), parses them into a
// memory structure, and returns (via the 'data' argument) a pointer
// to this structure. It returns:
//  Zero on success,
//  ERR_OPENDIR if there was a transient error, e.g. the output file
//   is on a network volume that is not available. The validator will
//   try this result again later.
//  Any other return value indicates a permanent error. Example: an
//   output file is missing, or has a syntax error. The result will be
//   marked as invalid.
int init_result(RESULT& result, void*& data)
{
    log_messages.printf(MSG_DEBUG, "init_result\n");
    string fname;
    int retval;

    retval = get_output_file_path(result, fname);
    if (retval)
        return retval;

    string line;
    igzstream infile(fname.c_str());

    if (!infile.good())
        return ERR_FOPEN;

    fit_file *ft = new fit_file;

    while (infile.good()) {
      getline(infile, line);
      trimRight(line);
      ft->push_back(line);
    }
    infile.close();

    data = (void*)ft;
    return (0);
}

// compare_results() takes two results and their associated memory structures.
// It returns (via the 'match' argument) true if the two results are
// equivalent (within the tolerances of the application).
int compare_results(RESULT& r1, void* data1, RESULT const& r2, void* data2, bool& match)
{
    log_messages.printf(MSG_DEBUG, "compare_result\n");
    fit_file *a = (fit_file *)data1;
    fit_file *b = (fit_file *)data2;

    match = *a == *b;
    return (0);
}

// Destroy the structure at date
int cleanup_result(RESULT const& r, void* data)
{
    log_messages.printf(MSG_DEBUG, "cleanup_result\n");
    delete (fit_file *)data;
    return (0);
}
