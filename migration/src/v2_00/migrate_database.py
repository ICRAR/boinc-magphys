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

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)


def correct_pixel_results(connection):
    connection.execute('ALTER TABLE pixel_result CHANGE COLUMN x_w_tot xi_w_tot DOUBLE NULL DEFAULT NULL')
    connection.execute('ALTER TABLE pixel_result REMOVE PARTITIONING')


def correct_parameter_name(connection):
    connection.execute("ALTER TABLE parameter_name ADD COLUMN column_name VARCHAR(20) NOT NULL DEFAULT ''")
    connection.execute("UPDATE parameter_name SET column_name = 'fmu_sfh' WHERE parameter_name_id = 1")
    connection.execute("UPDATE parameter_name SET column_name = 'fmu_ir' WHERE parameter_name_id = 2")
    connection.execute("UPDATE parameter_name SET column_name = 'mu' WHERE parameter_name_id = 3")
    connection.execute("UPDATE parameter_name SET column_name = 'tauv' WHERE parameter_name_id = 4")
    connection.execute("UPDATE parameter_name SET column_name = 's_sfr' WHERE parameter_name_id = 5")
    connection.execute("UPDATE parameter_name SET column_name = 'm' WHERE parameter_name_id = 6")
    connection.execute("UPDATE parameter_name SET column_name = 'ldust' WHERE parameter_name_id = 7")
    connection.execute("UPDATE parameter_name SET column_name = 't_c_ism' WHERE parameter_name_id = 8")
    connection.execute("UPDATE parameter_name SET column_name = 't_w_bc' WHERE parameter_name_id = 9")
    connection.execute("UPDATE parameter_name SET column_name = 'xi_c_tot' WHERE parameter_name_id = 10")
    connection.execute("UPDATE parameter_name SET column_name = 'xi_pah_tot' WHERE parameter_name_id = 11")
    connection.execute("UPDATE parameter_name SET column_name = 'xi_mir_tot' WHERE parameter_name_id = 12")
    connection.execute("UPDATE parameter_name SET column_name = 'xi_w_tot' WHERE parameter_name_id = 13")
    connection.execute("UPDATE parameter_name SET column_name = 'tvism' WHERE parameter_name_id = 14")
    connection.execute("UPDATE parameter_name SET column_name = 'mdust' WHERE parameter_name_id = 15")
    connection.execute("UPDATE parameter_name SET column_name = 'sfr' WHERE parameter_name_id = 16")


def delete_tables(connection):
    connection.execute('drop table pixel_histogram')
    connection.execute('drop table pixel_parameter')
    connection.execute('drop table pixel_filter')
    connection.execute('drop table run_file')
    connection.execute('drop table docmosis_task_galaxy')
    connection.execute('drop table docmosis_task')


def correct_galaxy(connection):
    connection.execute('ALTER TABLE galaxy ADD COLUMN status_time TIMESTAMP NULL')


def migrate_database(connection):
    LOG.info('Migrating the database')
    correct_galaxy(connection)
    correct_pixel_results(connection)
    delete_tables(connection)
    correct_parameter_name(connection)

