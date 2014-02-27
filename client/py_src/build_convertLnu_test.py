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
The expect output
"""
from calc_distance import get_distance


def correct_flux_and_sigma(flux, sigma, distance):
    flux = float(flux)
    sigma = float(sigma)
    w = 0

    if flux > 0:
        flux = flux * 1.0e-23 * 3.283608731e-33 * pow(distance, 2)
        sigma = sigma * 1.0e-23 * 3.283608731e-33 * pow(distance, 2)

    if sigma < 0.05 * flux:
        sigma = 0.05 * flux

    if sigma > 0.0:
        w = 1.0 / (pow(sigma, 2))

    return flux, sigma, w


def build_flux_sigma_w_tuple(elements):
    redshift = float(elements[1])
    distance = get_distance(redshift)
    count = 0
    fsw_tuple = []
    for i in range(2, len(elements), 2):
        flux, sigma, w = correct_flux_and_sigma(elements[i], elements[i+1], distance)
        fsw_tuple.append([flux, sigma, w, count])
        count += 1

    return fsw_tuple


def build_line(line_number, line):
    """
    Build the line
    """
    line = line.strip()
    elements = line.split()
    elements = build_flux_sigma_w_tuple(elements)
    for fsw_tuple in elements:
        if fsw_tuple[0] == 0:
            print '''BOOST_CHECK_EQUAL(0, observationLines[{0}].observations__[{1}].flux_obs__);
BOOST_CHECK_EQUAL(0, observationLines[{0}].observations__[{1}].sigma__);
BOOST_CHECK_EQUAL(0, observationLines[{0}].observations__[{1}].w__);
'''.format(line_number, fsw_tuple[3])
        else:
            print '''BOOST_CHECK_CLOSE({1}, observationLines[{0}].observations__[{4}].flux_obs__, 0.0001);
BOOST_CHECK_CLOSE({2}, observationLines[{0}].observations__[{4}].sigma__, 0.0001);
BOOST_CHECK_CLOSE({3}, observationLines[{0}].observations__[{4}].w__, 0.0001);
'''.format(line_number, fsw_tuple[0], fsw_tuple[1], fsw_tuple[2], fsw_tuple[3])


def main():
    """
    Build the lines
    """
    build_line(0, 'pix109931946 0.0037000 0  0  8.12205939837e-07  4.27777990808e-07  2.06016011361e-06  7.29802763999e-07  1.55258362611e-06  8.13435690361e-07  2.54790279541e-06  1.70986049852e-06  0  0')
    build_line(1, 'pix109931947 0.0037000 0  0  7.64728497415e-07  4.74621401736e-07  2.13877979149e-06  7.08565721652e-07  1.79323569682e-06  8.3227240566e-07  3.24324855683e-06  1.75896093424e-06  5.96150721321e-06  3.91164394387e-06')
    build_line(2, 'pix109931948 0.0037000 0  0  1.35693221637e-06  5.10276777277e-07  2.37017525251e-06  7.47913702526e-07  3.4896715988e-06  8.48556965138e-07  6.44427882435e-06  2.55606414612e-06  7.66245557315e-06  4.29274859925e-06')
    build_line(3, 'pix109931949 0.0037000 0  0  7.60890657148e-07  4.49842815442e-07  1.35534935453e-06  7.27894473584e-07  2.05301535061e-06  7.83011103067e-07  4.43016915597e-06  2.2535680273e-06  0  0')
    build_line(4, 'pix109931950 0.0037000 0  0  1.22923154322e-06  5.09423443873e-07  1.37951985835e-06  7.26561665942e-07  3.10678751703e-06  8.4088139829e-07  4.59399234387e-06  2.47695038524e-06  9.04353692022e-06  4.26582710134e-06')
    build_line(5, 'pix109931951 0.0037000 0  0  9.25593838019e-07  5.09138772031e-07  1.86195575225e-06  7.05086961261e-07  3.70661814486e-06  8.43808038553e-07  6.81346318743e-06  2.59233911493e-06  6.50642004985e-06  4.43977251052e-06')
    build_line(6, 'pix109931952 0.0037000 0  0  1.0591153341e-06  4.98553845318e-07  1.21886398574e-06  5.67959091313e-07  1.91702065422e-06  7.92054891008e-07  4.6387654038e-06  2.46776107815e-06  0  0')
    build_line(7, 'pix109931953 0.0037000 0  0  8.35864113924e-07  4.55342160421e-07  9.38424420838e-07  5.96065490299e-07  2.16165267375e-06  7.78675826041e-07  2.75466504718e-06  2.15321597352e-06  6.50309402772e-06  3.1265292364e-06')
    build_line(8, 'pix109931954 0.0037000 0  0  1.48521473875e-06  5.12648341555e-07  1.3153855889e-06  5.44567058114e-07  1.49618472278e-06  7.73947931521e-07  3.01644899992e-06  2.14187048186e-06  0  0')
    build_line(9, 'pix109931955 0.0037000 0  0  9.71594886323e-07  4.99076179494e-07  1.24337566376e-06  6.07563492849e-07  1.18270918392e-06  7.09960261247e-07  4.38666893388e-06  2.56425687439e-06  8.21916091809e-06  4.48101809525e-06')
    build_line(10, 'pix109931956 0.0037000 0  0  7.81118160376e-07  4.44943054845e-07  9.22690503558e-07  6.50517961276e-07  1.37131769407e-06  7.45185388951e-07  2.85112059828e-06  2.04267871595e-06  0  0')
    build_line(11, 'pix109931957 0.0037000 0  0  8.48158890676e-07  4.86474561967e-07  2.07424295695e-06  7.14005579994e-07  2.17390379476e-06  7.52092091716e-07  2.52603354056e-06  1.9097706172e-06  6.66432515573e-06  4.07797779189e-06')
    build_line(12, 'pix109931958 0.0037000 0  0  8.2568601556e-07  4.28406821129e-07  1.67612313362e-06  7.37698542252e-07  1.6413589492e-06  7.38328367333e-07  4.06235267292e-06  2.23281585932e-06  0  0')
    build_line(13, 'pix109931959 0.0037000 0  0  9.12360860639e-07  4.4243671482e-07  1.68354779362e-06  8.12469465927e-07  2.26847896556e-06  7.4152040952e-07  2.36314781432e-06  2.2521558094e-06  8.09594803286e-06  4.73453064842e-06')
    build_line(14, 'pix109931960 0.0037000 0  0  1.26971008285e-06  4.7619832344e-07  1.4676546698e-06  7.36155584491e-07  2.24821383199e-06  7.23091204691e-07  3.61477964361e-06  1.9908898139e-06  9.55308223638e-06  4.71440853289e-06')
    build_line(15, 'pix109931961 0.0037000 0  0  1.13511066502e-06  4.84230724851e-07  1.30115938646e-06  6.59630416067e-07  3.02991543322e-06  7.63600951359e-07  4.38808683612e-06  2.40258918893e-06  0  0')
    build_line(16, 'pix109931962 0.0037000 0  0  8.15084661099e-07  4.63788921934e-07  1.346352974e-06  7.37903803838e-07  2.43530689659e-06  7.42995439396e-07  4.96190205013e-06  2.48763626587e-06  0  0')

if __name__ == '__main__':
    main()
