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
Link to create_work.h
"""

cdef extern from "create_work.h":
    # Open the connect to the BOINC DB
    int boinc_db_open()

    # Close the connect to the BOINC DB
    int boinc_db_close()

    # Create a work unit
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
