#! /usr/bin/env python2.7
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
Get the data about an area
"""
import argparse
import logging
from sqlalchemy.engine import create_engine
from sqlalchemy.sql import select
from config import DB_LOGIN
from database.database_support_core import AREA, PIXEL_RESULT, PIXEL_PARAMETER, PARAMETER_NAME

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser('Get details about the area')
parser.add_argument('area_id', nargs='+', type=int, help='the area_ids')
args = vars(parser.parse_args())


ENGINE = create_engine(DB_LOGIN)
connection = ENGINE.connect()

# Get the Parameter Map
MAP_PARAMETER_NAMES = {}
for parameter_name in connection.execute(select([PARAMETER_NAME])):
    MAP_PARAMETER_NAMES[parameter_name[PARAMETER_NAME.c.parameter_name_id]] = parameter_name[PARAMETER_NAME.c.name]

for area_id in args['area_id']:
    area = connection.execute(select([AREA]).where(AREA.c.area_id == area_id)).first()

    print '######################################'
    print '######################################'
    print '      Area  top_x  top_y  bottom_x  bottom_y  workunit_id'
    print '{0:>10} {1:>6} {2:>6} {3:>9} {4:>9} {5:>12}'.format(area_id,
        area[AREA.c.top_x],
        area[AREA.c.top_y],
        area[AREA.c.bottom_x],
        area[AREA.c.bottom_y],
        area[AREA.c.workunit_id])

    for pixel_result in connection.execute(select([PIXEL_RESULT]).where(PIXEL_RESULT.c.area_id == area[AREA.c.area_id]).order_by(PIXEL_RESULT.c.pxresult_id)):
        print '****'
        #                    0     1     2            3         4        5       6         7         8         9      10      11         12          13           14      15       16        17          18          19       20       21       22         23         24
        print '    pxresult_id     x     y  workunit_id     i_sfh     i_ir    chi2  redshift   fmu_sfh    fmu_ir      mu    tauv      s_sfr           m        ldust  t_w_bc  t_c_ism  xi_c_tot  xi_pah_tot  xi_mir_tot  x_w_tot    tvism    mdust        sfr      i_opt'
        print '{0:>15} {1:>5} {2:>5} {3:>12} {4:>9} {5:>7} {6:>8} {7:>9} {8:>9} {9:>9} {10:>7} {11:>7} {12:>10} {13:>10} {14:>12} {15:>7} {16:>8} {17:>9} {18:>11} {19:>11} {20:>8} {21:>8} {22:>8} {23:>10} {24:>10}'.format(pixel_result[PIXEL_RESULT.c.pxresult_id],
            pixel_result[PIXEL_RESULT.c.x],
            pixel_result[PIXEL_RESULT.c.y],
            pixel_result[PIXEL_RESULT.c.workunit_id],
            pixel_result[PIXEL_RESULT.c.i_sfh],
            pixel_result[PIXEL_RESULT.c.i_ir],
            pixel_result[PIXEL_RESULT.c.chi2],
            pixel_result[PIXEL_RESULT.c.redshift],
            pixel_result[PIXEL_RESULT.c.fmu_sfh],
            pixel_result[PIXEL_RESULT.c.fmu_ir],
            pixel_result[PIXEL_RESULT.c.mu],
            pixel_result[PIXEL_RESULT.c.tauv],
            pixel_result[PIXEL_RESULT.c.s_sfr],
            pixel_result[PIXEL_RESULT.c.m],
            pixel_result[PIXEL_RESULT.c.ldust],
            pixel_result[PIXEL_RESULT.c.t_w_bc],
            pixel_result[PIXEL_RESULT.c.t_c_ism],
            pixel_result[PIXEL_RESULT.c.xi_c_tot],
            pixel_result[PIXEL_RESULT.c.xi_pah_tot],
            pixel_result[PIXEL_RESULT.c.xi_mir_tot],
            pixel_result[PIXEL_RESULT.c.x_w_tot],
            pixel_result[PIXEL_RESULT.c.tvism],
            pixel_result[PIXEL_RESULT.c.mdust],
            pixel_result[PIXEL_RESULT.c.sfr],
            pixel_result[PIXEL_RESULT.c.i_opt])

        #                    00        01       02
        print '          dmstar  dfmu_aux       dz'
        print '{0:>15} {1:>9} {2:>8}'.format(pixel_result[PIXEL_RESULT.c.dmstar],
            pixel_result[PIXEL_RESULT.c.dfmu_aux],
            pixel_result[PIXEL_RESULT.c.dz])

        print '******'
        print ' parameter_name  percentile2_5  percentile16  percentile50  percentile84  percentile97_5  high_prob_bin  first_prob_bin  last_prob_bin  bin_step'
        for pixel_parameter in connection.execute(select([PIXEL_PARAMETER]).where(PIXEL_PARAMETER.c.pxresult_id == pixel_result[PIXEL_RESULT.c.pxresult_id]).order_by(PIXEL_PARAMETER.c.parameter_name_id)):
            print '{0:>15} {1:>14} {2:>13} {3:>13} {4:>13} {5:>15} {6:>14} {7:>15} {8:>14} {9:>9}'.format(MAP_PARAMETER_NAMES[pixel_parameter[PIXEL_PARAMETER.c.parameter_name_id]],
                pixel_parameter[PIXEL_PARAMETER.c.percentile2_5],
                pixel_parameter[PIXEL_PARAMETER.c.percentile16],
                pixel_parameter[PIXEL_PARAMETER.c.percentile50],
                pixel_parameter[PIXEL_PARAMETER.c.percentile84],
                pixel_parameter[PIXEL_PARAMETER.c.percentile97_5],
                pixel_parameter[PIXEL_PARAMETER.c.high_prob_bin],
                pixel_parameter[PIXEL_PARAMETER.c.first_prob_bin],
                pixel_parameter[PIXEL_PARAMETER.c.last_prob_bin],
                pixel_parameter[PIXEL_PARAMETER.c.bin_step])
