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

#include "CommandLine.hpp"

#include <gmock/gmock.h>
using ::testing::Eq;
#include <gtest/gtest.h>
using ::testing::Test;


namespace magphys {
    namespace testing {

        class CommandLineTest : public Test {
            protected:
                CommandLineTest() {}
                ~CommandLineTest() {}

                virtual void SetUp() {}
                virtual void TearDown() {}

                CommandLine commandLine;
        };


        TEST_F(CommandLineTest, one_arg) {
            vector<string> args;
            args.push_back("0.123");
            bool result = commandLine.loadArguments(args);

            EXPECT_FALSE(result);
        }

        TEST_F(CommandLineTest, four_args) {
            vector<string> args;
            args.push_back("0.123");
            args.push_back("../../../src/unit_test/data/observations.dat");
            args.push_back("../../../src/unit_test/data/filters01.dat");
            args.push_back("../../../src/unit_test/data/model_infrared.dat");
            args.push_back("../../../src/unit_test/data/model_optical.dat");
            bool result = commandLine.loadArguments(args);

            EXPECT_TRUE(result);
            EXPECT_DOUBLE_EQ(0.123, commandLine.redshift());
            EXPECT_EQ("../../../src/unit_test/data/observations.dat", commandLine.observationsFile());
            EXPECT_EQ("../../../src/unit_test/data/filters01.dat", commandLine.filtersFile());
            EXPECT_EQ("../../../src/unit_test/data/model_infrared.dat", commandLine.modelInfraredFile());
            EXPECT_EQ("../../../src/unit_test/data/model_optical.dat", commandLine.modelOpticalFile());
        }
    }
}
