#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012
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
Migrate the database
"""
import logging
from v2_00 import DRY_RUN

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)


def execute(connection, sql):
    if DRY_RUN:
        LOG.info('DRY_RUN: execute: {0}'.format(sql))
    else:
        connection.execute(sql)


def correct_pixel_results(connection):
    execute(connection, 'ALTER TABLE pixel_result CHANGE COLUMN x_w_tot xi_w_tot DOUBLE NULL DEFAULT NULL')
    execute(connection, 'ALTER TABLE pixel_result REMOVE PARTITIONING')


def correct_parameter_name(connection):
    execute(connection, "ALTER TABLE parameter_name ADD COLUMN column_name VARCHAR(20) NOT NULL DEFAULT ''")
    execute(connection, "UPDATE parameter_name SET column_name = 'fmu_sfh' WHERE parameter_name_id = 1")
    execute(connection, "UPDATE parameter_name SET column_name = 'fmu_ir' WHERE parameter_name_id = 2")
    execute(connection, "UPDATE parameter_name SET column_name = 'mu' WHERE parameter_name_id = 3")
    execute(connection, "UPDATE parameter_name SET column_name = 'tauv' WHERE parameter_name_id = 4")
    execute(connection, "UPDATE parameter_name SET column_name = 's_sfr' WHERE parameter_name_id = 5")
    execute(connection, "UPDATE parameter_name SET column_name = 'm' WHERE parameter_name_id = 6")
    execute(connection, "UPDATE parameter_name SET column_name = 'ldust' WHERE parameter_name_id = 7")
    execute(connection, "UPDATE parameter_name SET column_name = 't_c_ism' WHERE parameter_name_id = 8")
    execute(connection, "UPDATE parameter_name SET column_name = 't_w_bc' WHERE parameter_name_id = 9")
    execute(connection, "UPDATE parameter_name SET column_name = 'xi_c_tot' WHERE parameter_name_id = 10")
    execute(connection, "UPDATE parameter_name SET column_name = 'xi_pah_tot' WHERE parameter_name_id = 11")
    execute(connection, "UPDATE parameter_name SET column_name = 'xi_mir_tot' WHERE parameter_name_id = 12")
    execute(connection, "UPDATE parameter_name SET column_name = 'xi_w_tot' WHERE parameter_name_id = 13")
    execute(connection, "UPDATE parameter_name SET column_name = 'tvism' WHERE parameter_name_id = 14")
    execute(connection, "UPDATE parameter_name SET column_name = 'mdust' WHERE parameter_name_id = 15")
    execute(connection, "UPDATE parameter_name SET column_name = 'sfr' WHERE parameter_name_id = 16")


def delete_tables(connection):
    execute(connection, 'drop table pixel_histogram')
    execute(connection, 'drop table pixel_parameter')
    execute(connection, 'drop table pixel_filter')
    execute(connection, 'drop table run_file')
    execute(connection, 'drop table docmosis_task_galaxy')
    execute(connection, 'drop table docmosis_task')


def correct_galaxy(connection):
    execute(connection, 'ALTER TABLE galaxy ADD COLUMN status_time TIMESTAMP NULL')


def migrate_database(connection):
    LOG.info('Migrating the database')
    correct_galaxy(connection)
    correct_pixel_results(connection)
    delete_tables(connection)
    correct_parameter_name(connection)

