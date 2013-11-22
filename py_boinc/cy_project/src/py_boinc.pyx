#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2013
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#
"""
Setup the wrappers around the BOINC 'C' libraries
"""
cdef extern from "c_project/create_work.h":
    int db_open()

    int db_close()

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
                    char** input_files)

def boinc_db_close():
    return db_close()

def boinc_db_open():
    return db_open()

def boinc_create_work(char* app_name,
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
                      char** input_files):
    return create_work(app_name,
                       min_quorom,
                       max_success_results,
                       delay_bound,
                       target_nresults,
                       wu_name,
                       wu_template,
                       result_template,
                       rsc_fpops_est,
                       rsc_fpops_bound,
                       rsc_memory_bound,
                       rsc_disk_bound,
                       additional_xml,
                       opaque,
                       priority,
                       input_files)
