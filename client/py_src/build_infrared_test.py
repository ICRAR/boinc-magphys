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
redshift = 0.0037000


def correct_flux(flux):
    flux = float(flux)
    flux = 3.117336e+6 * pow(10, -0.4 * (flux + 48.6))
    return flux / (1 + redshift)


def correct_xi(xi, fmu_ir, fmu_ism, const):
    xi = float(xi)
    fmu_ir = float(fmu_ir)
    fmu_ism = float(fmu_ism)
    return xi * (1 - fmu_ir) + const * (1 - fmu_ism) * fmu_ir


def build_line(line_number, line, first=False):
    line = line.strip()
    elements = line.split()
    if first:
        print '''
// Checking line {0}
magphys::ModelInfrared& model = *modelData.modelInfrared({0});
double* flux = modelData.fluxInfrared({0});
'''.format(line_number)
    else:
        print '''
// Checking line {0}
model = *modelData.modelInfrared({0});
flux = modelData.fluxInfrared({0});
'''.format(line_number)
    print '''// The body of line {0}
BOOST_CHECK_CLOSE({1}, model.fmu_ir__, 0.001);
BOOST_CHECK_CLOSE({2}, model.fmu_ism__, 0.001);
BOOST_CHECK_CLOSE({3}, model.tbg1__, 0.001);
BOOST_CHECK_CLOSE({4}, model.tbg2__, 0.001);
BOOST_CHECK_CLOSE({5}, model.xi1__, 0.001);
BOOST_CHECK_CLOSE({6}, model.xi2__, 0.001);
BOOST_CHECK_CLOSE({7}, model.xi3__, 0.001);
BOOST_CHECK_CLOSE({8}, model.mdust__, 0.001);

BOOST_CHECK_CLOSE({9}, flux[0], 0.001);
BOOST_CHECK_CLOSE({10}, flux[1], 0.001);
BOOST_CHECK_CLOSE({11}, flux[2], 0.001);
BOOST_CHECK_CLOSE({12}, flux[3], 0.001);
'''.format(line_number,
           elements[0],
           float(elements[1]) * float(elements[0]),
           elements[2],
           elements[3],
           correct_xi(elements[4], elements[0], elements[1], 0.550),
           correct_xi(elements[5], elements[0], elements[1], 0.275),
           correct_xi(elements[6], elements[0], elements[1], 0.175),
           elements[7],
           correct_flux(elements[8]),
           correct_flux(elements[9]),
           correct_flux(elements[10]),
           correct_flux(elements[11]),
           )


def main():
    """
    Build the code
    """
    build_line(0, '     0.038     0.826    38.052    18.623     0.018     0.158     0.824   3.104E-04    8.9539    7.8566    3.6544    2.9735', True)
    build_line(1, '     0.764     0.742    32.412    22.175     0.117     0.128     0.756   9.863E-04    6.9860    6.9238    3.3404    3.6933')
    build_line(2, '     0.238     0.708    37.248    17.715     0.175     0.229     0.595   1.132E-03    6.7509    6.5482    2.8115    2.7530')
    build_line(3, '     0.474     0.922    54.388    22.040     0.009     0.148     0.843   7.304E-04    8.7806    8.1460    4.1058    2.9801')
    build_line(4, '     0.783     0.741    30.199    16.818     0.099     0.170     0.731   4.923E-03    7.0061    6.9243    3.3169    3.5919')
    build_line(49995, '     0.957     0.700    38.391    24.592     0.102     0.059     0.839   5.747E-04    6.7864    6.7595    3.2219    3.7411')
    build_line(49996, '     0.694     0.780    44.318    16.326     0.015     0.140     0.845   5.382E-03    7.4422    7.2945    3.6127    3.5706')
    build_line(49997, '     0.631     0.922    42.923    24.657     0.003     0.212     0.785   5.199E-04    8.6573    8.0610    4.0477    3.4904')
    build_line(49998, '     0.064     0.942    33.611    22.696     0.032     0.084     0.883   4.295E-04    8.5514    8.0667    4.1158    3.7045')
    build_line(49999, '     0.882     0.731    43.283    17.828     0.004     0.018     0.979   3.772E-03    7.0203    6.9904    3.4488    3.9006')



if __name__ == '__main__':
    main()
