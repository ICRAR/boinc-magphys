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

#include <gmock/gmock.h>
using ::testing::Eq;
#include <gtest/gtest.h>
using ::testing::Test;

namespace magphys {
    namespace testing {
        class ModelDataTest : public Test {
            protected:
                ModelDataTest() {}
                ~ModelDataTest() {}

                virtual void SetUp() {}
                virtual void TearDown() {}

                ModelData modelData {0.0037000};
        };

        TEST_F(ModelDataTest, goodFilterFile) {
            bool result = modelData.loadFilters("../../../src/unit_test/data/filters01.dat");
            EXPECT_TRUE(result);

            vector<Filter>& filters = *modelData.filters();
            EXPECT_EQ(11,         filters.size());
            EXPECT_EQ("GALEXFUV", filters[0].filterName);
            EXPECT_EQ(0.152     , filters[0].lambdaEff);
            EXPECT_EQ(123       , filters[0].filterId);
            EXPECT_EQ("GALEXNUV", filters[1].filterName);
            EXPECT_EQ(0.231     , filters[1].lambdaEff);
            EXPECT_EQ(124       , filters[1].filterId);
            EXPECT_EQ("WISEW3"  , filters[9].filterName);
            EXPECT_EQ(12.0      , filters[9].lambdaEff);
            EXPECT_EQ(282       , filters[9].filterId);
            EXPECT_EQ("WISEW4"  , filters[10].filterName);
            EXPECT_EQ(22.0      , filters[10].lambdaEff);
            EXPECT_EQ(283       , filters[10].filterId);

            EXPECT_EQ(9, modelData.nfilt_sfh());
            EXPECT_EQ(2, modelData.nfilt_mix());
            EXPECT_EQ(4, modelData.nfilt_ir());
        }

        TEST_F(ModelDataTest, badFilterFile) {
            bool result = modelData.loadFilters("../../../src/unit_test/data/filters02bad.dat");
            EXPECT_FALSE(result);
        }

        TEST_F(ModelDataTest, goodObservationFile) {
            bool result = modelData.loadFilters("../../../src/unit_test/data/filters03.dat");
            EXPECT_TRUE(result);

            vector<Filter>& filters = *modelData.filters();
            EXPECT_EQ(6, filters.size());
            EXPECT_EQ(6, modelData.nfilt_sfh());
            EXPECT_EQ(0, modelData.nfilt_mix());
            EXPECT_EQ(0, modelData.nfilt_ir());

            result = modelData.loadObservations("../../../src/unit_test/data/observations.dat");
            EXPECT_TRUE(result);

            vector<ObservationLine>& observationLines = *modelData.observationLines();
            std::cerr << "observationLines: " << &observationLines << std::endl;
            EXPECT_EQ(17, observationLines.size());
            EXPECT_EQ("pix109931946", observationLines[0].galaxyName);
            EXPECT_EQ(0.0037000     , observationLines[0].redshift);
            EXPECT_EQ("pix109931947", observationLines[1].galaxyName);
            EXPECT_EQ(0.0037000     , observationLines[1].redshift);
            EXPECT_EQ("pix109931948", observationLines[2].galaxyName);
            EXPECT_EQ(0.0037000     , observationLines[2].redshift);
            EXPECT_EQ("pix109931949", observationLines[3].galaxyName);
            EXPECT_EQ(0.0037000     , observationLines[3].redshift);
            EXPECT_EQ("pix109931950", observationLines[4].galaxyName);
            EXPECT_EQ(0.0037000     , observationLines[4].redshift);
            EXPECT_EQ("pix109931951", observationLines[5].galaxyName);
            EXPECT_EQ(0.0037000     , observationLines[5].redshift);
            EXPECT_EQ("pix109931952", observationLines[6].galaxyName);
            EXPECT_EQ(0.0037000     , observationLines[6].redshift);
            EXPECT_EQ("pix109931953", observationLines[7].galaxyName);
            EXPECT_EQ(0.0037000     , observationLines[7].redshift);
            EXPECT_EQ("pix109931954", observationLines[8].galaxyName);
            EXPECT_EQ(0.0037000     , observationLines[8].redshift);
            EXPECT_EQ("pix109931955", observationLines[9].galaxyName);
            EXPECT_EQ(0.0037000     , observationLines[9].redshift);
            EXPECT_EQ("pix109931956", observationLines[10].galaxyName);
            EXPECT_EQ(0.0037000     , observationLines[10].redshift);
            EXPECT_EQ("pix109931957", observationLines[11].galaxyName);
            EXPECT_EQ(0.0037000     , observationLines[11].redshift);
            EXPECT_EQ("pix109931958", observationLines[12].galaxyName);
            EXPECT_EQ(0.0037000     , observationLines[12].redshift);
            EXPECT_EQ("pix109931959", observationLines[13].galaxyName);
            EXPECT_EQ(0.0037000     , observationLines[13].redshift);
            EXPECT_EQ("pix109931960", observationLines[14].galaxyName);
            EXPECT_EQ(0.0037000     , observationLines[14].redshift);
            EXPECT_EQ("pix109931961", observationLines[15].galaxyName);
            EXPECT_EQ(0.0037000     , observationLines[15].redshift);
            EXPECT_EQ("pix109931962", observationLines[16].galaxyName);
            EXPECT_EQ(0.0037000     , observationLines[16].redshift);

            EXPECT_EQ(0                , observationLines[0].observations[0].flux_obs);
            EXPECT_EQ(0                , observationLines[0].observations[0].sigma);
            EXPECT_EQ(8.12205939837e-07, observationLines[0].observations[1].flux_obs);
            EXPECT_EQ(4.27777990808e-07, observationLines[0].observations[1].sigma);
            EXPECT_EQ(2.06016011361e-06, observationLines[0].observations[2].flux_obs);
            EXPECT_EQ(7.29802763999e-07, observationLines[0].observations[2].sigma);
            EXPECT_EQ(1.55258362611e-06, observationLines[0].observations[3].flux_obs);
            EXPECT_EQ(8.13435690361e-07, observationLines[0].observations[3].sigma);
            EXPECT_EQ(2.54790279541e-06, observationLines[0].observations[4].flux_obs);
            EXPECT_EQ(1.70986049852e-06, observationLines[0].observations[4].sigma);
            EXPECT_EQ(0                , observationLines[0].observations[5].flux_obs);
            EXPECT_EQ(0                , observationLines[0].observations[5].sigma);

            EXPECT_EQ(0                , observationLines[1].observations[0].flux_obs);
            EXPECT_EQ(0                , observationLines[1].observations[0].sigma);
            EXPECT_EQ(7.64728497415e-07, observationLines[1].observations[1].flux_obs);
            EXPECT_EQ(4.74621401736e-07, observationLines[1].observations[1].sigma);
            EXPECT_EQ(2.13877979149e-06, observationLines[1].observations[2].flux_obs);
            EXPECT_EQ(7.08565721652e-07, observationLines[1].observations[2].sigma);
            EXPECT_EQ(1.79323569682e-06, observationLines[1].observations[3].flux_obs);
            EXPECT_EQ(8.3227240566e-07 , observationLines[1].observations[3].sigma);
            EXPECT_EQ(3.24324855683e-06, observationLines[1].observations[4].flux_obs);
            EXPECT_EQ(1.75896093424e-06, observationLines[1].observations[4].sigma);
            EXPECT_EQ(5.96150721321e-06, observationLines[1].observations[5].flux_obs);
            EXPECT_EQ(3.91164394387e-06, observationLines[1].observations[5].sigma);

            EXPECT_EQ(0                , observationLines[16].observations[0].flux_obs);
            EXPECT_EQ(0                , observationLines[16].observations[0].sigma);
            EXPECT_EQ(8.15084661099e-07, observationLines[16].observations[1].flux_obs);
            EXPECT_EQ(4.63788921934e-07, observationLines[16].observations[1].sigma);
            EXPECT_EQ(1.346352974e-06  , observationLines[16].observations[2].flux_obs);
            EXPECT_EQ(7.37903803838e-07, observationLines[16].observations[2].sigma);
            EXPECT_EQ(2.43530689659e-06, observationLines[16].observations[3].flux_obs);
            EXPECT_EQ(7.42995439396e-07, observationLines[16].observations[3].sigma);
            EXPECT_EQ(4.96190205013e-06, observationLines[16].observations[4].flux_obs);
            EXPECT_EQ(2.48763626587e-06, observationLines[16].observations[4].sigma);
            EXPECT_EQ(0                , observationLines[16].observations[5].flux_obs);
            EXPECT_EQ(0                , observationLines[16].observations[5].sigma);
        }

        TEST_F(ModelDataTest, goodObservationFileWithMissingFilters) {
            bool result = modelData.loadFilters("../../../src/unit_test/data/filters04.dat");
            EXPECT_TRUE(result);

            vector<Filter>& filters = *modelData.filters();
            EXPECT_EQ(6, filters.size());

            result = modelData.loadObservations("../../../src/unit_test/data/observations.dat");
            EXPECT_TRUE(result);

            vector<ObservationLine>& observationLines = *modelData.observationLines();
            EXPECT_EQ(17, observationLines.size());
            EXPECT_EQ("pix109931946",   observationLines[0].galaxyName);
            EXPECT_DOUBLE_EQ(0.0037000, observationLines[0].redshift);
            EXPECT_EQ("pix109931947",   observationLines[1].galaxyName);
            EXPECT_DOUBLE_EQ(0.0037000, observationLines[1].redshift);
            EXPECT_EQ("pix109931948",   observationLines[2].galaxyName);
            EXPECT_DOUBLE_EQ(0.0037000, observationLines[2].redshift);
            EXPECT_EQ("pix109931949",   observationLines[3].galaxyName);
            EXPECT_DOUBLE_EQ(0.0037000, observationLines[3].redshift);
            EXPECT_EQ("pix109931950",   observationLines[4].galaxyName);
            EXPECT_DOUBLE_EQ(0.0037000, observationLines[4].redshift);
            EXPECT_EQ("pix109931951",   observationLines[5].galaxyName);
            EXPECT_DOUBLE_EQ(0.0037000, observationLines[5].redshift);
            EXPECT_EQ("pix109931952",   observationLines[6].galaxyName);
            EXPECT_DOUBLE_EQ(0.0037000, observationLines[6].redshift);
            EXPECT_EQ("pix109931953",   observationLines[7].galaxyName);
            EXPECT_DOUBLE_EQ(0.0037000, observationLines[7].redshift);
            EXPECT_EQ("pix109931954",   observationLines[8].galaxyName);
            EXPECT_DOUBLE_EQ(0.0037000, observationLines[8].redshift);
            EXPECT_EQ("pix109931955",   observationLines[9].galaxyName);
            EXPECT_DOUBLE_EQ(0.0037000, observationLines[9].redshift);
            EXPECT_EQ("pix109931956",   observationLines[10].galaxyName);
            EXPECT_DOUBLE_EQ(0.0037000, observationLines[10].redshift);
            EXPECT_EQ("pix109931957",   observationLines[11].galaxyName);
            EXPECT_DOUBLE_EQ(0.0037000, observationLines[11].redshift);
            EXPECT_EQ("pix109931958",   observationLines[12].galaxyName);
            EXPECT_DOUBLE_EQ(0.0037000, observationLines[12].redshift);
            EXPECT_EQ("pix109931959",   observationLines[13].galaxyName);
            EXPECT_DOUBLE_EQ(0.0037000, observationLines[13].redshift);
            EXPECT_EQ("pix109931960",   observationLines[14].galaxyName);
            EXPECT_DOUBLE_EQ(0.0037000, observationLines[14].redshift);
            EXPECT_EQ("pix109931961",   observationLines[15].galaxyName);
            EXPECT_DOUBLE_EQ(0.0037000, observationLines[15].redshift);
            EXPECT_EQ("pix109931962",   observationLines[16].galaxyName);
            EXPECT_DOUBLE_EQ(0.0037000, observationLines[16].redshift);

            EXPECT_EQ(0                       , observationLines[0].observations[0].flux_obs);
            EXPECT_EQ(0                       , observationLines[0].observations[0].sigma);
            EXPECT_DOUBLE_EQ(8.12205939837e-07, observationLines[0].observations[1].flux_obs);
            EXPECT_DOUBLE_EQ(4.27777990808e-07, observationLines[0].observations[1].sigma);
            EXPECT_EQ(-99                     , observationLines[0].observations[2].flux_obs);
            EXPECT_EQ(-99                     , observationLines[0].observations[2].sigma);
            EXPECT_DOUBLE_EQ(1.55258362611e-06, observationLines[0].observations[3].flux_obs);
            EXPECT_DOUBLE_EQ(8.13435690361e-07, observationLines[0].observations[3].sigma);
            EXPECT_EQ(-99                     , observationLines[0].observations[4].flux_obs);
            EXPECT_EQ(-99                     , observationLines[0].observations[4].sigma);
            EXPECT_EQ(0                       , observationLines[0].observations[5].flux_obs);
            EXPECT_EQ(0                       , observationLines[0].observations[5].sigma);

            EXPECT_EQ(0                       , observationLines[1].observations[0].flux_obs);
            EXPECT_EQ(0                       , observationLines[1].observations[0].sigma);
            EXPECT_DOUBLE_EQ(7.64728497415e-07, observationLines[1].observations[1].flux_obs);
            EXPECT_DOUBLE_EQ(4.74621401736e-07, observationLines[1].observations[1].sigma);
            EXPECT_EQ(-99                     , observationLines[1].observations[2].flux_obs);
            EXPECT_EQ(-99                     , observationLines[1].observations[2].sigma);
            EXPECT_DOUBLE_EQ(1.79323569682e-06, observationLines[1].observations[3].flux_obs);
            EXPECT_DOUBLE_EQ(8.3227240566e-07 , observationLines[1].observations[3].sigma);
            EXPECT_EQ(-99                     , observationLines[1].observations[4].flux_obs);
            EXPECT_EQ(-99                     , observationLines[1].observations[4].sigma);
            EXPECT_DOUBLE_EQ(5.96150721321e-06, observationLines[1].observations[5].flux_obs);
            EXPECT_DOUBLE_EQ(3.91164394387e-06, observationLines[1].observations[5].sigma);

            EXPECT_EQ(0                       , observationLines[16].observations[0].flux_obs);
            EXPECT_EQ(0                       , observationLines[16].observations[0].sigma);
            EXPECT_DOUBLE_EQ(8.15084661099e-07, observationLines[16].observations[1].flux_obs);
            EXPECT_DOUBLE_EQ(4.63788921934e-07, observationLines[16].observations[1].sigma);
            EXPECT_EQ(-99                     , observationLines[16].observations[2].flux_obs);
            EXPECT_EQ(-99                     , observationLines[16].observations[2].sigma);
            EXPECT_DOUBLE_EQ(2.43530689659e-06, observationLines[16].observations[3].flux_obs);
            EXPECT_DOUBLE_EQ(7.42995439396e-07, observationLines[16].observations[3].sigma);
            EXPECT_EQ(-99                     , observationLines[16].observations[4].flux_obs);
            EXPECT_EQ(-99                     , observationLines[16].observations[4].sigma);
            EXPECT_EQ(0                       , observationLines[16].observations[5].flux_obs);
            EXPECT_EQ(0                       , observationLines[16].observations[5].sigma);
        }
    }
}
