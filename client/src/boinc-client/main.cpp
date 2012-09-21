#ifdef _WIN32
#include "boinc_win.h"
#else
#include "config.h"
#include <cstdio>
#include <cctype>
#include <ctime>
#include <cstring>
#include <cstdlib>
#include <csignal>
#include <unistd.h>
#endif

#include "str_util.h"
#include "util.h"
#include "filesys.h"
#include "boinc_api.h"
#include "mfile.h"

#define CHECKPOINT_FILE "checkpoint_state"
#define INPUT_FILENAME "observation.dat"
#define FILTERS_FILENAME "filters.dat"

int do_checkpoint(int pixel, long loopPosition) {
    fprintf(stderr, "APP: checkpointing\n");
    FILE* f = fopen("temp", "w");
    if (!f)
        return 1;
    fprintf(f, "%d %ld", pixel, loopPosition);
    fclose(f);

    string resolved_name;
    boinc_resolve_filename_s(CHECKPOINT_FILE, resolved_name);
    int retval = boinc_rename("temp", resolved_name.c_str());
    if (retval)
        return retval;

    return 0;
}

int get_number_pixels(FILE* infile) {
    char line [ 1024 ];
    int count = 0;
    while ( fgets ( line, sizeof line, file ) != NULL ) {
        if (line[0] == '#') {
            // Ignore it
        }
        else if (strlen(line) > 10) {
            count++;
        }
    }

    return count;
}

int main(int argc, char **argv) {
    int retval = boinc_init();
    if (retval) {
        fprintf(stderr, "%s boinc_init returned %d\n", boinc_msg_prefix(buf, sizeof(buf)), retval);
        exit(retval);
    }

    // open the input file (resolve logical name first)
    char input_path[1024];
    boinc_resolve_filename(INPUT_FILENAME, input_path, sizeof(input_path));
    FILE* infile = boinc_fopen(input_path, "r");
    if (!infile) {
        fprintf(stderr, "%s Couldn't find input file, resolved name %s.\n", boinc_msg_prefix(buf, sizeof(buf)), input_path
        );
        exit(-1);
    }

    // Get the number of pixels
    int num_pixels = get_number_pixels(infile);
    fclose(infile);     // The Fortran does the reading so make sure the file is closed

    // See if there's a valid checkpoint file.
    // If so seek input file and truncate output file
    char chkpt_path[1024];
    boinc_resolve_filename(CHECKPOINT_FILE, chkpt_path, sizeof(chkpt_path));
    FILE* state = boinc_fopen(chkpt_path, "r");
    int pixel = 1;
    long loopPosition = 0;
    if (state) {
        int n = fscanf(state, "%d %ld", &pixel, &loopPosition);
        fclose(state);
    }

    // main loop - read characters, convert to UC, write
    for (int i = pixel; i <= num_pixels; i++) {
        if (boinc_time_to_checkpoint()) {
            retval = do_checkpoint(out, i, 0);
            if (retval) {
                fprintf(stderr, "%s APP: checkpoint failed %d\n",
                    boinc_msg_prefix(buf, sizeof(buf)), retval
                );
                exit(retval);
            }
            boinc_checkpoint_completed();
        }

        double fd = (double)i/(double)num_pixels;
        boinc_fraction_done(fd);

        // Call the F77 to do the heavy lifting
        //callF77(i, );

        boinc_send_trickle_up(
            const_cast<char*>("example_app"),
            const_cast<char*>("sample trickle message")
        );
    }

    // Build the output file which we gzip as old clients can't do it
    concat(num_pixels);

    boinc_fraction_done(1);
    boinc_finish(0);
}

#ifdef _WIN32
int WINAPI WinMain(HINSTANCE hInst, HINSTANCE hPrevInst, LPSTR Args, int WinMode) {
    LPSTR command_line;
    char* argv[100];
    int argc;

    command_line = GetCommandLine();
    argc = parse_command_line( command_line, argv );
    return main(argc, argv);
}
#endif

