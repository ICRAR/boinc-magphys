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

#ifdef __cplusplus
extern "C" {
#endif

// Open the connect to the BOINC DB - this is effectively a singleton to be
// used for all DB operations.
// Return errval if it fails
int db_open();

// Close the connect to the BOINC DB
int db_close();

// Transaction functions
int transaction_start();
int transaction_rollback();
int transaction_commit();

// Create a work unit
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
    char* additional_xml,
    int opaque,
    int priority,
    int size_class,
    char** input_files,
    int number_input_files);

#ifdef __cplusplus
}
#endif
