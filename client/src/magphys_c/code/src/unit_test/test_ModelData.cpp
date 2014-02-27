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

#include "ModelData.hpp"
#include "test_STR.hpp"

BOOST_AUTO_TEST_SUITE(ModelDataTests)

BOOST_AUTO_TEST_CASE(goodFilterFile) {
    magphys::ModelData modelData { 0.0037000 };
    bool result = modelData.loadFilters(path + "filters01.dat");
    BOOST_REQUIRE(result);

    vector<magphys::Filter>& filters = *modelData.filters();
    BOOST_CHECK_EQUAL(11, filters.size());
    BOOST_CHECK_EQUAL("GALEXFUV", filters[0].filterName__);
    BOOST_CHECK_EQUAL(0.152, filters[0].lambdaEff__);
    BOOST_CHECK_EQUAL(123, filters[0].filterId__);
    BOOST_CHECK_EQUAL("GALEXNUV", filters[1].filterName__);
    BOOST_CHECK_EQUAL(0.231, filters[1].lambdaEff__);
    BOOST_CHECK_EQUAL(124, filters[1].filterId__);
    BOOST_CHECK_EQUAL("WISEW3", filters[9].filterName__);
    BOOST_CHECK_EQUAL(12.0, filters[9].lambdaEff__);
    BOOST_CHECK_EQUAL(282, filters[9].filterId__);
    BOOST_CHECK_EQUAL("WISEW4", filters[10].filterName__);
    BOOST_CHECK_EQUAL(22.0, filters[10].lambdaEff__);
    BOOST_CHECK_EQUAL(283, filters[10].filterId__);

    BOOST_CHECK_EQUAL(9, modelData.nfilt_sfh());
    BOOST_CHECK_EQUAL(2, modelData.nfilt_mix());
    BOOST_CHECK_EQUAL(4, modelData.nfilt_ir());
}

BOOST_AUTO_TEST_CASE(badFilterFile) {
    magphys::ModelData modelData { 0.0037000 };
    bool result = modelData.loadFilters(path + "filters02bad.dat");
    BOOST_REQUIRE(!result);
}

BOOST_AUTO_TEST_CASE(goodObservationFile) {
    magphys::ModelData modelData { 0.0037000 };
    bool result = modelData.loadFilters(path + "filters03.dat");
    BOOST_REQUIRE(result);

    vector<magphys::Filter>& filters = *modelData.filters();
    BOOST_REQUIRE_EQUAL(6, filters.size());
    BOOST_CHECK_EQUAL(6, modelData.nfilt_sfh());
    BOOST_CHECK_EQUAL(0, modelData.nfilt_mix());
    BOOST_CHECK_EQUAL(0, modelData.nfilt_ir());

    result = modelData.loadObservations(path + "observations.dat");
    BOOST_REQUIRE(result);

    vector<magphys::ObservationLine>& observationLines = *modelData.observationLines();
    BOOST_CHECK_EQUAL(17, observationLines.size());
    BOOST_CHECK_EQUAL("pix109931946", observationLines[0].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[0].redshift__);
    BOOST_CHECK_EQUAL("pix109931947", observationLines[1].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[1].redshift__);
    BOOST_CHECK_EQUAL("pix109931948", observationLines[2].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[2].redshift__);
    BOOST_CHECK_EQUAL("pix109931949", observationLines[3].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[3].redshift__);
    BOOST_CHECK_EQUAL("pix109931950", observationLines[4].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[4].redshift__);
    BOOST_CHECK_EQUAL("pix109931951", observationLines[5].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[5].redshift__);
    BOOST_CHECK_EQUAL("pix109931952", observationLines[6].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[6].redshift__);
    BOOST_CHECK_EQUAL("pix109931953", observationLines[7].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[7].redshift__);
    BOOST_CHECK_EQUAL("pix109931954", observationLines[8].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[8].redshift__);
    BOOST_CHECK_EQUAL("pix109931955", observationLines[9].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[9].redshift__);
    BOOST_CHECK_EQUAL("pix109931956", observationLines[10].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[10].redshift__);
    BOOST_CHECK_EQUAL("pix109931957", observationLines[11].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[11].redshift__);
    BOOST_CHECK_EQUAL("pix109931958", observationLines[12].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[12].redshift__);
    BOOST_CHECK_EQUAL("pix109931959", observationLines[13].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[13].redshift__);
    BOOST_CHECK_EQUAL("pix109931960", observationLines[14].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[14].redshift__);
    BOOST_CHECK_EQUAL("pix109931961", observationLines[15].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[15].redshift__);
    BOOST_CHECK_EQUAL("pix109931962", observationLines[16].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[16].redshift__);

    BOOST_CHECK_EQUAL(0, observationLines[0].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[0].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(8.12205939837e-07, observationLines[0].observations__[1].flux_obs__);
    BOOST_CHECK_EQUAL(4.27777990808e-07, observationLines[0].observations__[1].sigma__);
    BOOST_CHECK_EQUAL(2.06016011361e-06, observationLines[0].observations__[2].flux_obs__);
    BOOST_CHECK_EQUAL(7.29802763999e-07, observationLines[0].observations__[2].sigma__);
    BOOST_CHECK_EQUAL(1.55258362611e-06, observationLines[0].observations__[3].flux_obs__);
    BOOST_CHECK_EQUAL(8.13435690361e-07, observationLines[0].observations__[3].sigma__);
    BOOST_CHECK_EQUAL(2.54790279541e-06, observationLines[0].observations__[4].flux_obs__);
    BOOST_CHECK_EQUAL(1.70986049852e-06, observationLines[0].observations__[4].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[0].observations__[5].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[0].observations__[5].sigma__);

    BOOST_CHECK_EQUAL(0, observationLines[1].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[1].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(7.64728497415e-07, observationLines[1].observations__[1].flux_obs__);
    BOOST_CHECK_EQUAL(4.74621401736e-07, observationLines[1].observations__[1].sigma__);
    BOOST_CHECK_EQUAL(2.13877979149e-06, observationLines[1].observations__[2].flux_obs__);
    BOOST_CHECK_EQUAL(7.08565721652e-07, observationLines[1].observations__[2].sigma__);
    BOOST_CHECK_EQUAL(1.79323569682e-06, observationLines[1].observations__[3].flux_obs__);
    BOOST_CHECK_EQUAL(8.3227240566e-07, observationLines[1].observations__[3].sigma__);
    BOOST_CHECK_EQUAL(3.24324855683e-06, observationLines[1].observations__[4].flux_obs__);
    BOOST_CHECK_EQUAL(1.75896093424e-06, observationLines[1].observations__[4].sigma__);
    BOOST_CHECK_EQUAL(5.96150721321e-06, observationLines[1].observations__[5].flux_obs__);
    BOOST_CHECK_EQUAL(3.91164394387e-06, observationLines[1].observations__[5].sigma__);

    BOOST_CHECK_EQUAL(0, observationLines[16].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[16].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(8.15084661099e-07, observationLines[16].observations__[1].flux_obs__);
    BOOST_CHECK_EQUAL(4.63788921934e-07, observationLines[16].observations__[1].sigma__);
    BOOST_CHECK_EQUAL(1.346352974e-06, observationLines[16].observations__[2].flux_obs__);
    BOOST_CHECK_EQUAL(7.37903803838e-07, observationLines[16].observations__[2].sigma__);
    BOOST_CHECK_EQUAL(2.43530689659e-06, observationLines[16].observations__[3].flux_obs__);
    BOOST_CHECK_EQUAL(7.42995439396e-07, observationLines[16].observations__[3].sigma__);
    BOOST_CHECK_EQUAL(4.96190205013e-06, observationLines[16].observations__[4].flux_obs__);
    BOOST_CHECK_EQUAL(2.48763626587e-06, observationLines[16].observations__[4].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[16].observations__[5].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[16].observations__[5].sigma__);
}

BOOST_AUTO_TEST_CASE(goodObservationFileWithMissingFilters) {
    magphys::ModelData modelData { 0.0037000 };
    bool result = modelData.loadFilters(path + "filters04.dat");
    BOOST_REQUIRE(result);

    vector<magphys::Filter>& filters = *modelData.filters();
    BOOST_REQUIRE_EQUAL(6, filters.size());

    result = modelData.loadObservations(path + "observations.dat");
    BOOST_REQUIRE(result);

    vector<magphys::ObservationLine>& observationLines = *modelData.observationLines();
    BOOST_CHECK_EQUAL(17, observationLines.size());
    BOOST_CHECK_EQUAL("pix109931946", observationLines[0].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[0].redshift__);
    BOOST_CHECK_EQUAL("pix109931947", observationLines[1].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[1].redshift__);
    BOOST_CHECK_EQUAL("pix109931948", observationLines[2].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[2].redshift__);
    BOOST_CHECK_EQUAL("pix109931949", observationLines[3].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[3].redshift__);
    BOOST_CHECK_EQUAL("pix109931950", observationLines[4].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[4].redshift__);
    BOOST_CHECK_EQUAL("pix109931951", observationLines[5].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[5].redshift__);
    BOOST_CHECK_EQUAL("pix109931952", observationLines[6].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[6].redshift__);
    BOOST_CHECK_EQUAL("pix109931953", observationLines[7].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[7].redshift__);
    BOOST_CHECK_EQUAL("pix109931954", observationLines[8].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[8].redshift__);
    BOOST_CHECK_EQUAL("pix109931955", observationLines[9].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[9].redshift__);
    BOOST_CHECK_EQUAL("pix109931956", observationLines[10].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[10].redshift__);
    BOOST_CHECK_EQUAL("pix109931957", observationLines[11].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[11].redshift__);
    BOOST_CHECK_EQUAL("pix109931958", observationLines[12].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[12].redshift__);
    BOOST_CHECK_EQUAL("pix109931959", observationLines[13].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[13].redshift__);
    BOOST_CHECK_EQUAL("pix109931960", observationLines[14].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[14].redshift__);
    BOOST_CHECK_EQUAL("pix109931961", observationLines[15].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[15].redshift__);
    BOOST_CHECK_EQUAL("pix109931962", observationLines[16].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000, observationLines[16].redshift__);

    BOOST_CHECK_EQUAL(0, observationLines[0].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[0].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(8.12205939837e-07, observationLines[0].observations__[1].flux_obs__);
    BOOST_CHECK_EQUAL(4.27777990808e-07, observationLines[0].observations__[1].sigma__);
    BOOST_CHECK_EQUAL(-99, observationLines[0].observations__[2].flux_obs__);
    BOOST_CHECK_EQUAL(-99, observationLines[0].observations__[2].sigma__);
    BOOST_CHECK_EQUAL(1.55258362611e-06, observationLines[0].observations__[3].flux_obs__);
    BOOST_CHECK_EQUAL(8.13435690361e-07, observationLines[0].observations__[3].sigma__);
    BOOST_CHECK_EQUAL(-99, observationLines[0].observations__[4].flux_obs__);
    BOOST_CHECK_EQUAL(-99, observationLines[0].observations__[4].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[0].observations__[5].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[0].observations__[5].sigma__);

    BOOST_CHECK_EQUAL(0, observationLines[1].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[1].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(7.64728497415e-07, observationLines[1].observations__[1].flux_obs__);
    BOOST_CHECK_EQUAL(4.74621401736e-07, observationLines[1].observations__[1].sigma__);
    BOOST_CHECK_EQUAL(-99, observationLines[1].observations__[2].flux_obs__);
    BOOST_CHECK_EQUAL(-99, observationLines[1].observations__[2].sigma__);
    BOOST_CHECK_EQUAL(1.79323569682e-06, observationLines[1].observations__[3].flux_obs__);
    BOOST_CHECK_EQUAL(8.3227240566e-07, observationLines[1].observations__[3].sigma__);
    BOOST_CHECK_EQUAL(-99, observationLines[1].observations__[4].flux_obs__);
    BOOST_CHECK_EQUAL(-99, observationLines[1].observations__[4].sigma__);
    BOOST_CHECK_EQUAL(5.96150721321e-06, observationLines[1].observations__[5].flux_obs__);
    BOOST_CHECK_EQUAL(3.91164394387e-06, observationLines[1].observations__[5].sigma__);

    BOOST_CHECK_EQUAL(0, observationLines[16].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[16].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(8.15084661099e-07, observationLines[16].observations__[1].flux_obs__);
    BOOST_CHECK_EQUAL(4.63788921934e-07, observationLines[16].observations__[1].sigma__);
    BOOST_CHECK_EQUAL(-99, observationLines[16].observations__[2].flux_obs__);
    BOOST_CHECK_EQUAL(-99, observationLines[16].observations__[2].sigma__);
    BOOST_CHECK_EQUAL(2.43530689659e-06, observationLines[16].observations__[3].flux_obs__);
    BOOST_CHECK_EQUAL(7.42995439396e-07, observationLines[16].observations__[3].sigma__);
    BOOST_CHECK_EQUAL(-99, observationLines[16].observations__[4].flux_obs__);
    BOOST_CHECK_EQUAL(-99, observationLines[16].observations__[4].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[16].observations__[5].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[16].observations__[5].sigma__);
}

BOOST_AUTO_TEST_SUITE_END()
