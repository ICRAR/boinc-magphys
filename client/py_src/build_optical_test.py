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
Build the GTest code I need
"""
from math import log10

redshift = 0.0037000


def correct_flux(flux, mstr1):
    flux = float(flux)
    flux = 3.117336e+6 * pow(10, -0.4 * (flux + 48.6))
    flux = flux / mstr1
    return flux / (1 + redshift)


def build_line(line_number, line, first=False):
    line = line.strip()
    elements = line.split()
    mstr1 = float(elements[6])
    if first:
        print '''
// Checking line {0}
magphys::ModelOptical& model = *modelData.modelOptical({0});
double* flux = modelData.fluxOptical({0});
'''.format(line_number)
    else:
        print '''
// Checking line {0}
model = *modelData.modelOptical({0});
flux = modelData.fluxOptical({0});
'''.format(line_number)
    print '''// The body of line {0}
BOOST_CHECK_CLOSE({1}, model.fmu_sfh__, 0.001);
BOOST_CHECK_CLOSE({2}, model.mstr1__, 0.001);
BOOST_CHECK_CLOSE({3}, model.ldust__, 0.001);
BOOST_CHECK_CLOSE({4}, model.logldust__, 0.001);
BOOST_CHECK_CLOSE({5}, model.mu__, 0.001);
BOOST_CHECK_CLOSE({6}, model.tauv__, 0.001);
BOOST_CHECK_CLOSE({7}, model.ssfr__, 0.001);
BOOST_CHECK_CLOSE({8}, model.lssfr__, 0.001);
BOOST_CHECK_CLOSE({9}, model.tvsim__, 0.001);

BOOST_CHECK_CLOSE({10}, flux[0], 0.001);
BOOST_CHECK_CLOSE({11}, flux[1], 0.001);
BOOST_CHECK_CLOSE({12}, flux[2], 0.001);
BOOST_CHECK_CLOSE({13}, flux[3], 0.001);
BOOST_CHECK_CLOSE({14}, flux[4], 0.001);
BOOST_CHECK_CLOSE({15}, flux[5], 0.001);
BOOST_CHECK_CLOSE({16}, flux[6], 0.001);
BOOST_CHECK_CLOSE({17}, flux[7], 0.001);
BOOST_CHECK_CLOSE({18}, flux[8], 0.001);
'''.format(line_number,
           elements[22],
           mstr1,
           float(elements[21]) / mstr1,
           log10(float(elements[21]) / mstr1),
           elements[5],
           elements[4],
           elements[10],
           log10(float(elements[10])),
           float(elements[5]) * float(elements[4]),
           correct_flux(elements[25], mstr1),
           correct_flux(elements[26], mstr1),
           correct_flux(elements[27], mstr1),
           correct_flux(elements[28], mstr1),
           correct_flux(elements[29], mstr1),
           correct_flux(elements[30], mstr1),
           correct_flux(elements[31], mstr1),
           correct_flux(elements[32], mstr1),
           correct_flux(elements[33], mstr1),
           )


def main():
    """
    Build the code
    """
    build_line(    0, '   1      1.15E+10    0.1291    1.3307    4.2970    0.7220    2.5511    4.7204  2.94E-11  2.95E-11  2.96E-11  6.28E-11  4.94E-11  5.33E+08  0.00E+00  0.00E+00  0.00E+00  7.72E-03  7.72E-03  5.11E+09  4.42E+09  2.35E+00    0.9180  1.10E-05  8.13E-07   16.8898   14.3729   11.0083    8.6379    7.2997    6.5404    5.9079    4.7473    5.0653', True)
    build_line(    1, '   2      1.31E+10    0.4039    0.2871    1.5080    0.4799    0.9455    1.7636  2.02E-12  2.02E-12  2.06E-12  2.15E-10  1.10E-10  2.46E+08  0.00E+00  0.00E+00  0.00E+00  1.47E-01  1.47E-01  7.91E+09  3.33E+09  8.95E-01    0.9850  3.81E-05  7.58E-06    9.2713    8.4061    6.9972    5.6504    5.1787    4.8109    4.4388    4.6051    5.0516')
    build_line(    2, '   3      2.13E+09    0.3335    0.1012    0.9018    0.0702    0.3070    0.5087  1.64E-10  1.64E-10  1.67E-10  1.94E-10  2.32E-10  2.13E+09  0.00E+00  0.00E+00  0.00E+00  0.00E+00  0.00E+00  1.18E+09  8.06E+08  1.29E+00    0.1570  1.20E-03  3.25E-04    6.3311    6.1956    5.6912    4.7779    4.5308    4.2674    3.9674    4.6587    5.1991')
    build_line(    3, '   4      1.27E+10    0.6155    1.8815    4.5052    0.3180    0.7528    1.4754  2.51E-13  2.52E-13  2.59E-13  3.45E-13  4.91E-13  7.42E+09  0.00E+00  0.00E+00  0.00E+00  0.00E+00  0.00E+00  1.11E+10  1.08E+10  2.07E-01    0.9920  1.50E-07  9.89E-09   16.4477   15.1495   11.4408    9.0717    7.8482    7.2123    6.7109    6.2683    6.6617')
    build_line(49308, '   24996  7.30E+09    0.0519    1.2929    3.4571    0.7684    0.7109    1.1748  3.55E-11  3.55E-11  3.56E-11  6.84E-10  3.60E-10  3.40E+08  0.00E+00  0.00E+00  0.00E+00  5.89E-01  5.89E-01  2.34E+09  8.28E+08  2.56E+00    0.9100  9.35E-06  1.00E-06   14.7291   12.0361    9.4420    7.5011    6.7151    6.2086    5.7064    4.7702    5.0525')
    build_line(49309, '   24997  2.14E+09    0.6862    0.5288    0.1394    0.3335    0.4644    0.7701  1.58E-10  1.58E-10  1.63E-10  2.26E-10  3.37E-10  2.14E+09  0.00E+00  0.00E+00  0.00E+00  0.00E+00  0.00E+00  1.32E+09  9.12E+08  5.87E-01    0.2220  8.80E-03  2.92E-03    6.0416    5.9280    5.5355    4.6490    4.3543    4.1216    3.8553    4.2665    4.7411')
    build_line(49310, '   24998  1.66E+09    0.3217    1.6933    2.0988    0.5718    0.2587    0.4133  1.89E-10  1.89E-10  1.92E-10  2.23E-10  2.49E-10  1.66E+09  0.00E+00  0.00E+00  0.00E+00  0.00E+00  0.00E+00  8.97E+08  5.73E+08  2.32E+00    0.4790  1.09E-03  1.75E-04    9.9752    8.8960    7.7155    6.5464    6.0760    5.7331    5.3621    4.9820    5.3399')
    build_line(49311, '   24999  1.33E+10    0.8080    0.5194    3.1263    0.4940    1.0672    2.0722  1.74E-14  1.75E-14  1.81E-14  2.68E-14  2.02E-11  1.12E+09  0.00E+00  0.00E+00  0.00E+00  0.00E+00  2.27E-02  1.07E+10  9.30E+09  4.41E-01    1.0000  7.35E-08  7.95E-09   16.6074   13.8178   10.1043    8.0830    7.0247    6.4567    5.9985    5.7171    6.2039')
    build_line(49312, '   25000  1.27E+10    0.1543    0.5779    4.7424    0.5172    0.4805    0.9063  2.18E-11  2.18E-11  2.20E-11  2.36E-11  2.55E-11  3.72E+09  0.00E+00  0.00E+00  0.00E+00  0.00E+00  0.00E+00  8.00E+09  5.19E+09  6.16E-01    0.7600  8.43E-08  6.47E-09   15.2391   13.4487   11.2178    9.3355    8.2860    7.6579    7.1240    6.4142    6.8239')


if __name__ == '__main__':
    main()
