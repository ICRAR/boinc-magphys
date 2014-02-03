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

"""
from math import sqrt, fabs

h_ = 70.0
omega_ = 0.30
omega_lambda_ = 0.70


def cosmol_c():
    if omega_lambda_ == 0:
        q_ = omega_ / 2
    else:
        q_ = (3 * omega_ / 2) - 1

    omega0_ = (2 * (q_ + 1)) / 3
    return q_, omega0_


def get_funl(x, omega0_):
    omegainv = 1 / omega0_
    return 1 / sqrt(((x * x * x) + omegainv) - 1)


def get_midpnt(a, b, s, n, omega0_):
    if n == 1:
        result = (b - a) * get_funl(0.5 * (a + b), omega0_)
    else:
        it = pow(3, (n - 2))
        tnm = it
        delta = (b - a) / (3 * tnm)
        ddel = delta + delta
        x = a + 0.5 * delta
        sum = 0
        for j in range(0, it):
            sum = sum + get_funl(x, omega0_)
            x = x + ddel
            sum = sum + get_funl(x, omega0_)
            x = x + delta

        result = (s + (b - a) * sum / tnm) / 3
    return result


def get_dl(q_, redshift_, omega0_):
    dl = 0.0
    s = 0.0

    if redshift_ <= 0:
        return 1.0e-5

    if q_ == 0:
        dl = ((3.0e5 * redshift_) * (1 + (redshift_ / 2))) / h_

    elif q_ > 0:
        d1 = (q_ * redshift_) + ((q_ - 1) * (sqrt(1 + ((2 * q_) * redshift_)) - 1))
        d2 = ((h_ * q_) * q_) / 3.0e5
        dl = d1 / d2

    elif q_ < 0:
        aa = 1.0
        bb = 1 + redshift_
        success = False
        s0 = 1.0e-10
        npts = 0
        while not success:
            npts += 1
            s = get_midpnt(aa, bb, s, npts, omega0_)
            epsr = fabs(s - s0) / s0
            if epsr < 1.0e-4:
                success = True
            else:
                s0 = s

        dd1 = s
        dd2 = (3.0e5 * (1 + redshift_)) / (h_ * sqrt(omega0_))
        dl = dd1 * dd2
    return dl


def main(redshift):
    q_, omega0_ = cosmol_c()
    dist_ = get_dl(q_, redshift, omega0_) * 3.086e+24 / sqrt(1 + redshift)
    print dist_

if __name__ == '__main__':
    main(0.0037000)
    main(0.02)
    main(0.03)
