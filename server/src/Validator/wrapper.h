class RESULT {
 public:
    string	name;
    void	*data;

    RESULT(string str) : name(str), data(NULL) {}
};

inline int get_output_file_path(RESULT& result, string& fname)
{
    fname = result.name;
    return (0);
}

#define ERR_FOPEN (-1)

int init_result(RESULT& result, void*& data);
int compare_results(RESULT& r1, void* data1, RESULT const& r2, void* data2, bool& match);
int cleanup_result(RESULT const& r, void* data);
