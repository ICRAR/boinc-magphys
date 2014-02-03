/*
 *    (c) UWA, The University of Western Australia
 *    M468/35 Stirling Hwy
 *    Perth WA 6009
 *    Australia
 *
 *    Copyright by UWA, 2012-2013
 *    All rights reserved
 *
 *    This library is free software; you can redistribute it and/or
 *    modify it under the terms of the GNU Lesser General Public
 *    License as published by the Free Software Foundation; either
 *    version 2.1 of the License, or (at your option) any later version.
 *
 *    This library is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *    Lesser General Public License for more details.
 *
 *    You should have received a copy of the GNU Lesser General Public
 *    License along with this library; if not, write to the Free Software
 *    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
 *    MA 02111-1307  USA
 */

#include <string>
using std::string;
#include <vector>
using std::vector;

#include "Constants.hpp"

#ifndef FIT_HPP
#define FIT_HPP

namespace magphys {

    class Fit {
        public:
            Fit(double redshift) :
                redshift_ {redshift} {

            }
            ~Fit();

            void initialise();
            void fit();
        
            double dist() const {
                return dist_;
            }

        private:
            void cosmol_c();
            void calculateDistance();
            double get_dl();
            double get_funl(double x);
            double get_midpnt(double a, double b, double s, double n);
        
            const double redshift_;
            const double h_ = 70.0;
            const double omega_ = 0.30;
            const double omega_lambda_ = 0.70;
            double q_;
            double dist_;
            double omega0_ = 0;     // TODO: Same as Omega
    };

}

#endif
