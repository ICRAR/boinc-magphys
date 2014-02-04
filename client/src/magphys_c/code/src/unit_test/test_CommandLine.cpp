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

#include <boost/test/unit_test.hpp>

#include "test_STR.hpp"
#include "CommandLine.hpp"

BOOST_AUTO_TEST_SUITE(CommandLineTests)

BOOST_AUTO_TEST_CASE(one_arg) {
    vector<string> args;
    args.push_back("0.123");
    magphys::CommandLine commandLine;
    bool result = commandLine.loadArguments(args);

    BOOST_REQUIRE(!result);
}

BOOST_AUTO_TEST_CASE(four_args) {
    vector<string> args;
    args.push_back("0.123");
    args.push_back(path + "observations.dat");
    args.push_back(path + "filters01.dat");
    args.push_back(path + "model_infrared.dat");
    args.push_back(path + "model_optical.dat");
    magphys::CommandLine commandLine;
    bool result = commandLine.loadArguments(args);

    BOOST_REQUIRE(result);
    BOOST_CHECK_EQUAL(0.123, commandLine.redshift());
    BOOST_CHECK_EQUAL(path + "observations.dat", commandLine.observationsFile());
    BOOST_CHECK_EQUAL(path + "filters01.dat", commandLine.filtersFile());
    BOOST_CHECK_EQUAL(path + "model_infrared.dat", commandLine.modelInfraredFile());
    BOOST_CHECK_EQUAL(path + "model_optical.dat", commandLine.modelOpticalFile());
    BOOST_CHECK_EQUAL(0, commandLine.startingLine());
}

BOOST_AUTO_TEST_CASE(five_args) {
    vector<string> args;
    args.push_back("0.123");
    args.push_back(path + "observations.dat");
    args.push_back(path + "filters01.dat");
    args.push_back(path + "model_infrared.dat");
    args.push_back(path + "model_optical.dat");
    args.push_back("5");
    magphys::CommandLine commandLine;
    bool result = commandLine.loadArguments(args);

    BOOST_REQUIRE(result);
    BOOST_CHECK_EQUAL(0.123, commandLine.redshift());
    BOOST_CHECK_EQUAL(path + "observations.dat", commandLine.observationsFile());
    BOOST_CHECK_EQUAL(path + "filters01.dat", commandLine.filtersFile());
    BOOST_CHECK_EQUAL(path + "model_infrared.dat", commandLine.modelInfraredFile());
    BOOST_CHECK_EQUAL(path + "model_optical.dat", commandLine.modelOpticalFile());
    BOOST_CHECK_EQUAL(5, commandLine.startingLine());
}

BOOST_AUTO_TEST_SUITE_END()
