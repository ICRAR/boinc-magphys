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

#include "ModelData.hpp"
#include "Fit.hpp"
#include "test_STR.hpp"

#include <boost/test/unit_test.hpp>

BOOST_AUTO_TEST_SUITE(ConvertToLnuTests)

BOOST_AUTO_TEST_CASE( goodObservationFile) {
    magphys::ModelData modelData { 0.0037000 };
    magphys::Fit fit { 0.0037000 };
    bool result = modelData.loadFilters(path + "filters03.dat");
    BOOST_REQUIRE(result);

    vector<magphys::Filter>& filters = *modelData.filters();
    BOOST_REQUIRE_EQUAL(6, filters.size());
    BOOST_REQUIRE_EQUAL(6, modelData.nfilt_sfh());
    BOOST_REQUIRE_EQUAL(0, modelData.nfilt_mix());
    BOOST_REQUIRE_EQUAL(0, modelData.nfilt_ir());

    result = modelData.loadObservations(path + "observations.dat");
    BOOST_REQUIRE(result);

    vector<magphys::ObservationLine>& observationLines = *modelData.observationLines();
    BOOST_REQUIRE_EQUAL(17, observationLines.size());
    BOOST_CHECK_EQUAL("pix109931946", observationLines[0].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000 , observationLines[0].redshift__);
    BOOST_CHECK_EQUAL("pix109931947", observationLines[1].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000 , observationLines[1].redshift__);
    BOOST_CHECK_EQUAL("pix109931948", observationLines[2].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000 , observationLines[2].redshift__);
    BOOST_CHECK_EQUAL("pix109931949", observationLines[3].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000 , observationLines[3].redshift__);
    BOOST_CHECK_EQUAL("pix109931950", observationLines[4].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000 , observationLines[4].redshift__);
    BOOST_CHECK_EQUAL("pix109931951", observationLines[5].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000 , observationLines[5].redshift__);
    BOOST_CHECK_EQUAL("pix109931952", observationLines[6].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000 , observationLines[6].redshift__);
    BOOST_CHECK_EQUAL("pix109931953", observationLines[7].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000 , observationLines[7].redshift__);
    BOOST_CHECK_EQUAL("pix109931954", observationLines[8].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000 , observationLines[8].redshift__);
    BOOST_CHECK_EQUAL("pix109931955", observationLines[9].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000 , observationLines[9].redshift__);
    BOOST_CHECK_EQUAL("pix109931956", observationLines[10].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000 , observationLines[10].redshift__);
    BOOST_CHECK_EQUAL("pix109931957", observationLines[11].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000 , observationLines[11].redshift__);
    BOOST_CHECK_EQUAL("pix109931958", observationLines[12].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000 , observationLines[12].redshift__);
    BOOST_CHECK_EQUAL("pix109931959", observationLines[13].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000 , observationLines[13].redshift__);
    BOOST_CHECK_EQUAL("pix109931960", observationLines[14].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000 , observationLines[14].redshift__);
    BOOST_CHECK_EQUAL("pix109931961", observationLines[15].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000 , observationLines[15].redshift__);
    BOOST_CHECK_EQUAL("pix109931962", observationLines[16].galaxyName__);
    BOOST_CHECK_EQUAL(0.0037000 , observationLines[16].redshift__);

    BOOST_CHECK_EQUAL(0 , observationLines[0].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0 , observationLines[0].observations__[0].sigma__);
    BOOST_CHECK_CLOSE(8.12205939837e-07, observationLines[0].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(4.27777990808e-07, observationLines[0].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.06016011361e-06, observationLines[0].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(7.29802763999e-07, observationLines[0].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(1.55258362611e-06, observationLines[0].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(8.13435690361e-07, observationLines[0].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.54790279541e-06, observationLines[0].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(1.70986049852e-06, observationLines[0].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_EQUAL(0 , observationLines[0].observations__[5].flux_obs__);
    BOOST_CHECK_EQUAL(0 , observationLines[0].observations__[5].sigma__);

    BOOST_CHECK_EQUAL(0 , observationLines[1].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0 , observationLines[1].observations__[0].sigma__);
    BOOST_CHECK_CLOSE(7.64728497415e-07, observationLines[1].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(4.74621401736e-07, observationLines[1].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.13877979149e-06, observationLines[1].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(7.08565721652e-07, observationLines[1].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(1.79323569682e-06, observationLines[1].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(8.3227240566e-07 , observationLines[1].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(3.24324855683e-06, observationLines[1].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(1.75896093424e-06, observationLines[1].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(5.96150721321e-06, observationLines[1].observations__[5].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.91164394387e-06, observationLines[1].observations__[5].sigma__, 0.0001);

    BOOST_CHECK_EQUAL(0 , observationLines[16].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0 , observationLines[16].observations__[0].sigma__);
    BOOST_CHECK_CLOSE(8.15084661099e-07, observationLines[16].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(4.63788921934e-07, observationLines[16].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(1.346352974e-06 , observationLines[16].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(7.37903803838e-07, observationLines[16].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.43530689659e-06, observationLines[16].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(7.42995439396e-07, observationLines[16].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(4.96190205013e-06, observationLines[16].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(2.48763626587e-06, observationLines[16].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_EQUAL(0 , observationLines[16].observations__[5].flux_obs__);
    BOOST_CHECK_EQUAL(0 , observationLines[16].observations__[5].sigma__);

    fit.initialise();
    BOOST_CHECK_CLOSE(4.89847438071e+25, fit.dist(), 0.0001);
    observationLines = *modelData.observationLines();
    for(size_t i = 0; i < observationLines.size(); i++) {
        // Correct the fluxes for this observation
        magphys::ObservationLine& observationLine = observationLines[i];
        modelData.convertToLnu(fit.dist(), observationLine);
    }
    observationLines = *modelData.observationLines();

    BOOST_CHECK_EQUAL(0, observationLines[0].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[0].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[0].observations__[0].w__);

    BOOST_CHECK_CLOSE(6.39939982422e-11, observationLines[0].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.37047818159e-11, observationLines[0].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(8.80272145651e+20, observationLines[0].observations__[1].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.62320756624e-10, observationLines[0].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.75014223681e-11, observationLines[0].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(3.02442503792e+20, observationLines[0].observations__[2].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.22328622541e-10, observationLines[0].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(6.40908907284e-11, observationLines[0].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.43448658186e+20, observationLines[0].observations__[3].w__, 0.0001);

    BOOST_CHECK_CLOSE(2.00750178019e-10, observationLines[0].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(1.34720523909e-10, observationLines[0].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(5.50975736197e+19, observationLines[0].observations__[4].w__, 0.0001);

    BOOST_CHECK_EQUAL(0, observationLines[0].observations__[5].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[0].observations__[5].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[0].observations__[5].w__);

    BOOST_CHECK_EQUAL(0, observationLines[1].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[1].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[1].observations__[0].w__);

    BOOST_CHECK_CLOSE(6.02532334707e-11, observationLines[1].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.73955910178e-11, observationLines[1].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(7.15087517621e+20, observationLines[1].observations__[1].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.68515229333e-10, observationLines[1].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.58281481602e-11, observationLines[1].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(3.20843728965e+20, observationLines[1].observations__[2].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.41289685782e-10, observationLines[1].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(6.55750423045e-11, observationLines[1].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.32553479096e+20, observationLines[1].observations__[3].w__, 0.0001);

    BOOST_CHECK_CLOSE(2.55536720756e-10, observationLines[1].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(1.38589164906e-10, observationLines[1].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(5.20644691034e+19, observationLines[1].observations__[4].w__, 0.0001);

    BOOST_CHECK_CLOSE(4.69709298358e-10, observationLines[1].observations__[5].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.08199833799e-10, observationLines[1].observations__[5].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(1.05277411843e+19, observationLines[1].observations__[5].w__, 0.0001);

    BOOST_CHECK_EQUAL(0, observationLines[2].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[2].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[2].observations__[0].w__);

    BOOST_CHECK_CLOSE(1.0691317757e-10, observationLines[2].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(4.0204890886e-11, observationLines[2].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(6.18646021595e+20, observationLines[2].observations__[1].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.86746960966e-10, observationLines[2].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.89283897312e-11, observationLines[2].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.87972391079e+20, observationLines[2].observations__[2].w__, 0.0001);

    BOOST_CHECK_CLOSE(2.74952480899e-10, observationLines[2].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(6.68581086052e-11, observationLines[2].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.237133119e+20, observationLines[2].observations__[3].w__, 0.0001);

    BOOST_CHECK_CLOSE(5.07747047307e-10, observationLines[2].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(2.01393213778e-10, observationLines[2].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.46553025024e+19, observationLines[2].observations__[4].w__, 0.0001);

    BOOST_CHECK_CLOSE(6.03727631661e-10, observationLines[2].observations__[5].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.38227206722e-10, observationLines[2].observations__[5].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(8.74143881434e+18, observationLines[2].observations__[5].w__, 0.0001);

    BOOST_CHECK_EQUAL(0, observationLines[3].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[3].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[3].observations__[0].w__);

    BOOST_CHECK_CLOSE(5.99508486552e-11, observationLines[3].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.5443277288e-11, observationLines[3].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(7.96035168583e+20, observationLines[3].observations__[1].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.06788463316e-10, observationLines[3].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.73510674797e-11, observationLines[3].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(3.04030384163e+20, observationLines[3].observations__[2].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.61757818177e-10, observationLines[3].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(6.16937265484e-11, observationLines[3].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.6273503684e+20, observationLines[3].observations__[3].w__, 0.0001);

    BOOST_CHECK_CLOSE(3.49054621832e-10, observationLines[3].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(1.77559435734e-10, observationLines[3].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(3.17184888016e+19, observationLines[3].observations__[4].w__, 0.0001);

    BOOST_CHECK_EQUAL(0, observationLines[3].observations__[5].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[3].observations__[5].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[3].observations__[5].w__);

    BOOST_CHECK_EQUAL(0, observationLines[4].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[4].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[4].observations__[0].w__);

    BOOST_CHECK_CLOSE(9.6851595584e-11, observationLines[4].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(4.013765644e-11, observationLines[4].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(6.20720340997e+20, observationLines[4].observations__[1].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.08692866009e-10, observationLines[4].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.7246055086e-11, observationLines[4].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(3.05146836356e+20, observationLines[4].observations__[2].w__, 0.0001);

    BOOST_CHECK_CLOSE(2.4478490633e-10, observationLines[4].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(6.62533479315e-11, observationLines[4].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.27816062777e+20, observationLines[4].observations__[3].w__, 0.0001);

    BOOST_CHECK_CLOSE(3.61962309753e-10, observationLines[4].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(1.95159812092e-10, observationLines[4].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.62554349612e+19, observationLines[4].observations__[4].w__, 0.0001);

    BOOST_CHECK_CLOSE(7.12543527928e-10, observationLines[4].observations__[5].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.36106052215e-10, observationLines[4].observations__[5].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(8.85212085067e+18, observationLines[4].observations__[5].w__, 0.0001);

    BOOST_CHECK_EQUAL(0, observationLines[5].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[5].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[5].observations__[0].w__);

    BOOST_CHECK_CLOSE(7.29278715384e-11, observationLines[5].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(4.01152270432e-11, observationLines[5].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(6.21414654656e+20, observationLines[5].observations__[1].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.46704163676e-10, observationLines[5].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.55540553773e-11, observationLines[5].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(3.24017498788e+20, observationLines[5].observations__[2].w__, 0.0001);

    BOOST_CHECK_CLOSE(2.92045777324e-10, observationLines[5].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(6.64839389708e-11, observationLines[5].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.2623850156e+20, observationLines[5].observations__[3].w__, 0.0001);

    BOOST_CHECK_CLOSE(5.36835216111e-10, observationLines[5].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(2.04251331623e-10, observationLines[5].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.39701199206e+19, observationLines[5].observations__[4].w__, 0.0001);

    BOOST_CHECK_CLOSE(5.12643176823e-10, observationLines[5].observations__[5].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.49811273593e-10, observationLines[5].observations__[5].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(8.17207599601e+18, observationLines[5].observations__[5].w__, 0.0001);

    BOOST_CHECK_EQUAL(0, observationLines[6].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[6].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[6].observations__[0].w__);

    BOOST_CHECK_CLOSE(8.34480782574e-11, observationLines[6].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.92812368589e-11, observationLines[6].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(6.48081600721e+20, observationLines[6].observations__[1].w__, 0.0001);

    BOOST_CHECK_CLOSE(9.60347319998e-11, observationLines[6].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(4.47497011637e-11, observationLines[6].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(4.99366864178e+20, observationLines[6].observations__[2].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.51042747115e-10, observationLines[6].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(6.24062898543e-11, observationLines[6].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.56769403503e+20, observationLines[6].observations__[3].w__, 0.0001);

    BOOST_CHECK_CLOSE(3.65489995254e-10, observationLines[6].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(1.9443578328e-10, observationLines[6].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.64513359899e+19, observationLines[6].observations__[4].w__, 0.0001);

    BOOST_CHECK_EQUAL(0, observationLines[6].observations__[5].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[6].observations__[5].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[6].observations__[5].w__);

    BOOST_CHECK_EQUAL(0, observationLines[7].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[7].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[7].observations__[0].w__);

    BOOST_CHECK_CLOSE(6.5858034291e-11, observationLines[7].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.58765726577e-11, observationLines[7].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(7.76923226141e+20, observationLines[7].observations__[1].w__, 0.0001);

    BOOST_CHECK_CLOSE(7.39387977753e-11, observationLines[7].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(4.69642144529e-11, observationLines[7].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(4.53383671422e+20, observationLines[7].observations__[2].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.70317391956e-10, observationLines[7].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(6.13521485116e-11, observationLines[7].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.65668735056e+20, observationLines[7].observations__[3].w__, 0.0001);

    BOOST_CHECK_CLOSE(2.17041050232e-10, observationLines[7].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(1.69652661309e-10, observationLines[7].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(3.47439064138e+19, observationLines[7].observations__[4].w__, 0.0001);

    BOOST_CHECK_CLOSE(5.12381118343e-10, observationLines[7].observations__[5].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(2.46340363502e-10, observationLines[7].observations__[5].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(1.64789237467e+19, observationLines[7].observations__[5].w__, 0.0001);

    BOOST_CHECK_EQUAL(0, observationLines[8].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[8].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[8].observations__[0].w__);

    BOOST_CHECK_CLOSE(1.17020603666e-10, observationLines[8].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(4.03917472887e-11, observationLines[8].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(6.12935420106e+20, observationLines[8].observations__[1].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.03639703843e-10, observationLines[8].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(4.29066344512e-11, observationLines[8].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(5.43189166169e+20, observationLines[8].observations__[2].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.17884932655e-10, observationLines[8].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(6.09796360012e-11, observationLines[8].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.68924484434e+20, observationLines[8].observations__[3].w__, 0.0001);

    BOOST_CHECK_CLOSE(2.37667102062e-10, observationLines[8].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(1.68758745939e-10, observationLines[8].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(3.51129583314e+19, observationLines[8].observations__[4].w__, 0.0001);

    BOOST_CHECK_EQUAL(0, observationLines[8].observations__[5].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[8].observations__[5].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[8].observations__[5].w__);

    BOOST_CHECK_EQUAL(0, observationLines[9].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[9].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[9].observations__[0].w__);

    BOOST_CHECK_CLOSE(7.6552310686e-11, observationLines[9].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.93223917565e-11, observationLines[9].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(6.4672574349e+20, observationLines[9].observations__[1].w__, 0.0001);

    BOOST_CHECK_CLOSE(9.79660159306e-11, observationLines[9].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(4.78701462109e-11, observationLines[9].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(4.36385681314e+20, observationLines[9].observations__[2].w__, 0.0001);

    BOOST_CHECK_CLOSE(9.31860821554e-11, observationLines[9].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.59380244367e-11, observationLines[9].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(3.19584532143e+20, observationLines[9].observations__[3].w__, 0.0001);

    BOOST_CHECK_CLOSE(3.45627223682e-10, observationLines[9].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(2.02038721787e-10, observationLines[9].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.449800819e+19, observationLines[9].observations__[4].w__, 0.0001);

    BOOST_CHECK_CLOSE(6.47590646099e-10, observationLines[9].observations__[5].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.53061028054e-10, observationLines[9].observations__[5].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(8.02232841636e+18, observationLines[9].observations__[5].w__, 0.0001);

    BOOST_CHECK_EQUAL(0, observationLines[10].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[10].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[10].observations__[0].w__);

    BOOST_CHECK_CLOSE(6.15445809126e-11, observationLines[10].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.50572233876e-11, observationLines[10].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(8.13663750134e+20, observationLines[10].observations__[1].w__, 0.0001);

    BOOST_CHECK_CLOSE(7.26991167715e-11, observationLines[10].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.12545442339e-11, observationLines[10].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(3.80658251089e+20, observationLines[10].observations__[2].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.08046614534e-10, observationLines[10].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.8713424923e-11, observationLines[10].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.9008493188e+20, observationLines[10].observations__[3].w__, 0.0001);

    BOOST_CHECK_CLOSE(2.24640817809e-10, observationLines[10].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(1.60943391012e-10, observationLines[10].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(3.86059020986e+19, observationLines[10].observations__[4].w__, 0.0001);

    BOOST_CHECK_EQUAL(0, observationLines[10].observations__[5].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[10].observations__[5].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[10].observations__[5].w__);

    BOOST_CHECK_EQUAL(0, observationLines[11].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[11].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[11].observations__[0].w__);

    BOOST_CHECK_CLOSE(6.68267441751e-11, observationLines[11].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.83295057773e-11, observationLines[11].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(6.80665221655e+20, observationLines[11].observations__[1].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.63430348918e-10, observationLines[11].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.62567565563e-11, observationLines[11].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(3.15973470866e+20, observationLines[11].observations__[2].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.71282662188e-10, observationLines[11].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.9257606519e-11, observationLines[11].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.84781509887e+20, observationLines[11].observations__[3].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.99027091561e-10, observationLines[11].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(1.5047151409e-10, observationLines[11].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(4.41663406719e+19, observationLines[11].observations__[4].w__, 0.0001);

    BOOST_CHECK_CLOSE(5.25084576932e-10, observationLines[11].observations__[5].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.21305337533e-10, observationLines[11].observations__[5].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(9.68643837318e+18, observationLines[11].observations__[5].w__, 0.0001);

    BOOST_CHECK_EQUAL(0, observationLines[12].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[12].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[12].observations__[0].w__);

    BOOST_CHECK_CLOSE(6.50560982587e-11, observationLines[12].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.37543275832e-11, observationLines[12].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(8.77689854545e+20, observationLines[12].observations__[1].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.32062344789e-10, observationLines[12].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.81235335777e-11, observationLines[12].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.96002910879e+20, observationLines[12].observations__[2].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.2932326219e-10, observationLines[12].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.81731577224e-11, observationLines[12].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.95498120466e+20, observationLines[12].observations__[3].w__, 0.0001);

    BOOST_CHECK_CLOSE(3.20074228787e-10, observationLines[12].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(1.75924364952e-10, observationLines[12].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(3.23108226865e+19, observationLines[12].observations__[4].w__, 0.0001);

    BOOST_CHECK_EQUAL(0, observationLines[12].observations__[5].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[12].observations__[5].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[12].observations__[5].w__);

    BOOST_CHECK_EQUAL(0, observationLines[13].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[13].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[13].observations__[0].w__);

    BOOST_CHECK_CLOSE(7.18852404892e-11, observationLines[13].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.48597479552e-11, observationLines[13].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(8.22908436102e+20, observationLines[13].observations__[1].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.32647336422e-10, observationLines[13].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(6.40147615576e-11, observationLines[13].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.44028042205e+20, observationLines[13].observations__[2].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.78734273925e-10, observationLines[13].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.84246598749e-11, observationLines[13].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.92959519358e+20, observationLines[13].observations__[3].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.86193266582e-10, observationLines[13].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(1.77448166578e-10, observationLines[13].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(3.17582795313e+19, observationLines[13].observations__[4].w__, 0.0001);

    BOOST_CHECK_CLOSE(6.37882658538e-10, observationLines[13].observations__[5].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.73035373336e-10, observationLines[13].observations__[5].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(7.18621105318e+18, observationLines[13].observations__[5].w__, 0.0001);

    BOOST_CHECK_EQUAL(0, observationLines[14].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[14].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[14].observations__[0].w__);

    BOOST_CHECK_CLOSE(1.00040914286e-10, observationLines[14].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.75198372463e-11, observationLines[14].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(7.10359361737e+20, observationLines[14].observations__[1].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.15637039515e-10, observationLines[14].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.80019633805e-11, observationLines[14].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.97245035868e+20, observationLines[14].observations__[2].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.77137576759e-10, observationLines[14].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.69726161954e-11, observationLines[14].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(3.08082957248e+20, observationLines[14].observations__[3].w__, 0.0001);

    BOOST_CHECK_CLOSE(2.84809788765e-10, observationLines[14].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(1.56862924786e-10, observationLines[14].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(4.06405318918e+19, observationLines[14].observations__[4].w__, 0.0001);

    BOOST_CHECK_CLOSE(7.52690786729e-10, observationLines[14].observations__[5].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.71449944613e-10, observationLines[14].observations__[5].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(7.24768657608e+18, observationLines[14].observations__[5].w__, 0.0001);

    BOOST_CHECK_EQUAL(0, observationLines[15].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[15].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[15].observations__[0].w__);

    BOOST_CHECK_CLOSE(8.94357777247e-11, observationLines[15].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.81527130436e-11, observationLines[15].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(6.86987994783e+20, observationLines[15].observations__[1].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.02518816233e-10, observationLines[15].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.19725178256e-11, observationLines[15].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(3.70213700164e+20, observationLines[15].observations__[2].w__, 0.0001);

    BOOST_CHECK_CLOSE(2.38728127187e-10, observationLines[15].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(6.01643937113e-11, observationLines[15].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.76261846863e+20, observationLines[15].observations__[3].w__, 0.0001);

    BOOST_CHECK_CLOSE(3.45738940709e-10, observationLines[15].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(1.89300866679e-10, observationLines[15].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.7905820437e+19, observationLines[15].observations__[4].w__, 0.0001);

    BOOST_CHECK_EQUAL(0, observationLines[15].observations__[5].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[15].observations__[5].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[15].observations__[5].w__);

    BOOST_CHECK_EQUAL(0, observationLines[16].observations__[0].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[16].observations__[0].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[16].observations__[0].w__);

    BOOST_CHECK_CLOSE(6.42208137262e-11, observationLines[16].observations__[1].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(3.65420960365e-11, observationLines[16].observations__[1].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(7.48881480313e+20, observationLines[16].observations__[1].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.06079635257e-10, observationLines[16].observations__[2].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.81397062119e-11, observationLines[16].observations__[2].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.95838256419e+20, observationLines[16].observations__[2].w__, 0.0001);

    BOOST_CHECK_CLOSE(1.91878706638e-10, observationLines[16].observations__[3].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(5.85408780096e-11, observationLines[16].observations__[3].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.91797479636e+20, observationLines[16].observations__[3].w__, 0.0001);

    BOOST_CHECK_CLOSE(3.90950047888e-10, observationLines[16].observations__[4].flux_obs__, 0.0001);
    BOOST_CHECK_CLOSE(1.96001756472e-10, observationLines[16].observations__[4].sigma__, 0.0001);
    BOOST_CHECK_CLOSE(2.60303539425e+19, observationLines[16].observations__[4].w__, 0.0001);

    BOOST_CHECK_EQUAL(0, observationLines[16].observations__[5].flux_obs__);
    BOOST_CHECK_EQUAL(0, observationLines[16].observations__[5].sigma__);
    BOOST_CHECK_EQUAL(0, observationLines[16].observations__[5].w__);
}

BOOST_AUTO_TEST_SUITE_END()
