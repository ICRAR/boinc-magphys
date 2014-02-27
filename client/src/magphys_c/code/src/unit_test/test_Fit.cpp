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


#include "Fit.hpp"
#include "test_STR.hpp"

#include <boost/test/unit_test.hpp>


BOOST_AUTO_TEST_SUITE( FitTests )

BOOST_AUTO_TEST_CASE(initialise) {
    magphys::Fit fit1__ { 0.0037000 };
    magphys::Fit fit2__ { 0.02 };
    magphys::Fit fit3__ { 0.03 };

    fit1__.initialise();
    fit2__.initialise();
    fit3__.initialise();

    BOOST_CHECK_CLOSE(4.89847438071e+25, fit1__.dist(), 0.0001);
    BOOST_CHECK_CLOSE(2.65939226237e+26, fit2__.dist(), 0.0001);
    BOOST_CHECK_CLOSE(3.99944349871e+26, fit3__.dist(), 0.0001);
}

BOOST_AUTO_TEST_SUITE_END()
