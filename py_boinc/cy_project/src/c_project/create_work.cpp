//
//    (c) UWA, The University of Western Australia
//    M468/35 Stirling Hwy
//    Perth WA 6009
//    Australia
//
//    Copyright by UWA, 2012-2013
//    All rights reserved
//
//    This library is free software; you can redistribute it and/or
//    modify it under the terms of the GNU Lesser General Public
//    License as published by the Free Software Foundation; either
//    version 2.1 of the License, or (at your option) any later version.
//
//    This library is distributed in the hope that it will be useful,
//    but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
//    Lesser General Public License for more details.
//
//    You should have received a copy of the GNU Lesser General Public
//    License along with this library; if not, write to the Free Software
//    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
//    MA 02111-1307  USA
//


// This file is based on create_work.cpp which is part of BOINC.
// http://boinc.berkeley.edu
// Copyright (C) 2008 University of California
//
// BOINC is free software; you can redistribute it and/or modify it
// under the terms of the GNU Lesser General Public License
// as published by the Free Software Foundation,
// either version 3 of the License, or (at your option) any later version.
//
// BOINC is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
// See the GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with BOINC.  If not, see <http://www.gnu.org/licenses/>.

// Create a workunit.
// Input files must be in the download dir.
// See the docs for a description of WU and result template files
// This program must be run in the project's root directory
//

#include "config.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <string>
#include <sys/param.h>
#include <unistd.h>

#include "boinc_db.h"
#include "common_defs.h"
#include "crypt.h"
#include "filesys.h"
#include "sched_config.h"
#include "str_replace.h"
#include "util.h"

#include "backend_lib.h"

#ifdef __cplusplus
extern "C" {
#endif
/**
 * Make a DB connection to the BOINC database.
 *
 * The connection is effectively a singleton stored in boinc_db
 */
int db_open() {
    int retval;
    const char* config_dir = 0;
    char download_dir[256], db_name[256], db_passwd[256];
    char db_user[256],db_host[256];

    retval = config.parse_file(config_dir);
    if (retval) {
        fprintf(stderr, "Can't parse config file: %s\n", boincerror(retval));
        return(retval);
    }

    strcpy(db_name, config.db_name);
    strcpy(db_passwd, config.db_passwd);
    strcpy(db_user, config.db_user);
    strcpy(db_host, config.db_host);
    strcpy(download_dir, config.download_dir);

    retval = boinc_db.open(db_name, db_host, db_user, db_passwd);
    if (retval) {
        fprintf(stderr,
            "create_work: error opening database: %s\n", boincerror(retval)
        );
        return(retval);
    }

    return 0;
}

/**
 * Close the DB connection to the BOINC database
 */
int db_close() {
    boinc_db.close();

    return 0;
}

/**
 * Create a work unit
 */
int create_work(char* app_name,
        int min_quorom,
        int max_success_results,
        int delay_bound,
        int target_nresults,
        char* wu_name,
        char* wu_template,
        char* result_template,
        float rsc_fpops_est,
        float rsc_fpops_bound,
        float rsc_memory_bound,
        float rsc_disk_bound,
        char* additional_xml_in,
        int opaque,
        int priority,
        char** input_files,
        int number_input_files) {
    DB_APP app;
    DB_WORKUNIT wu;
    int retval;
    char wu_template_file[256], result_template_file[256], result_template_path[MAXPATHLEN];
    const char* command_line=NULL;
    int ninfiles;
    char buf[256];
    char additional_xml[256];

    safe_strcpy(wu_template_file, wu_template);
    safe_strcpy(result_template_file, result_template);
    safe_strcpy(app.name, app_name);
    strcpy(additional_xml, additional_xml_in);
    ninfiles = number_input_files;

    // defaults (in case they're not in WU template)
    wu.clear();
    wu.id = 0;
    wu.min_quorum = min_quorom;
    wu.target_nresults = target_nresults;
    wu.max_error_results = 3;
    wu.max_total_results = 10;
    wu.max_success_results = 6;
    wu.rsc_fpops_est = rsc_fpops_est;
    wu.rsc_fpops_bound =  rsc_fpops_bound;
    wu.rsc_memory_bound = rsc_memory_bound;
    wu.rsc_disk_bound = rsc_disk_bound;
    wu.rsc_bandwidth_bound = 0.0;
    wu.delay_bound = delay_bound;
    wu.priority = priority;
    wu.max_success_results = max_success_results;
    wu.opaque = opaque;
    safe_strcpy(wu.name, wu_name);

    int dl = 3;
    log_messages.set_debug_level(dl);
    if (dl ==4) g_print_queries = true;

    sprintf(buf, "where name='%s'", app.name);
    retval = app.lookup(buf);
    if (retval) {
        fprintf(stderr, "create_work: app not found\n");
        return(retval);
    }

    retval = read_filename(wu_template_file, wu_template, sizeof(wu_template));
    if (retval) {
        fprintf(stderr,
            "create_work: can't open input template %s\n", wu_template_file
        );
        return(retval);
    }

    wu.appid = app.id;

    strcpy(result_template_path, "./");
    strcat(result_template_path, result_template_file);
    retval = create_work(
        wu,
        wu_template,
        result_template_file,
        result_template_path,
        const_cast<const char **>(input_files),
        ninfiles,
        config,
        command_line,
        additional_xml
    );
    if (retval) {
        fprintf(stderr, "create_work: %s\n", boincerror(retval));
        return(retval);
    }

    return 0;
}

#ifdef __cplusplus
}
#endif
