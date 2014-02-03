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
#include "test_STR.hpp"

#include <gmock/gmock.h>
using ::testing::Eq;
#include <gtest/gtest.h>
using ::testing::Test;

namespace magphys {
    namespace testing {       
        class ModelDataLoad : public Test {
            protected:
                ModelDataLoad() {}
                ~ModelDataLoad() {}

                virtual void SetUp() {}
                virtual void TearDown() {}

                ModelData modelData {0.0037000};
        };

        TEST_F(ModelDataLoad, modelInfrared) {
            bool result = modelData.loadFilters("../../../src/unit_test/data/filters05.dat");
            EXPECT_TRUE(result);
            vector<Filter>& filters = *modelData.filters();
            EXPECT_EQ(11, filters.size());

            EXPECT_EQ(9, modelData.nfilt_sfh());
            EXPECT_EQ(2, modelData.nfilt_mix());
            EXPECT_EQ(4, modelData.nfilt_ir());

            result = modelData.loadModelInfrared("../../../src/unit_test/data/infrared_dce08_z0.0100.lbr");
            EXPECT_TRUE(result);

            ModelInfrared& model = *modelData.modelInfrared(0);
            double* flux = modelData.fluxInfrared(0);

            EXPECT_DOUBLE_EQ(0.038, model.fmu_ir);
            EXPECT_DOUBLE_EQ(0.031388, model.fmu_ism);
            EXPECT_DOUBLE_EQ(38.052, model.tbg1);
            EXPECT_DOUBLE_EQ(18.623, model.tbg2);
            EXPECT_DOUBLE_EQ(0.0209526, model.xi1);
            EXPECT_DOUBLE_EQ(0.1538143, model.xi2);
            EXPECT_DOUBLE_EQ(0.7938451, model.xi3);
            EXPECT_DOUBLE_EQ(3.104E-04, model.mdust);
            
            EXPECT_EQ(e_str(2.9554232857e-17), e_str(flux[0]));
            EXPECT_EQ(e_str(8.11969452594e-17), e_str(flux[1]));
            EXPECT_EQ(e_str(3.89421289735e-15), e_str(flux[2]));
            EXPECT_EQ(e_str(7.29087564383e-15), e_str(flux[3]));
            
            
            model = *modelData.modelInfrared(1);
            flux = modelData.fluxInfrared(1);
            EXPECT_DOUBLE_EQ(0.764, model.fmu_ir);
            EXPECT_DOUBLE_EQ(0.566888, model.fmu_ism);
            EXPECT_DOUBLE_EQ(32.412, model.tbg1);
            EXPECT_DOUBLE_EQ(22.175, model.tbg2);
            EXPECT_DOUBLE_EQ(0.1360236, model.xi1);
            EXPECT_DOUBLE_EQ(0.0844138, model.xi2);
            EXPECT_DOUBLE_EQ(0.2129106, model.xi3);
            EXPECT_DOUBLE_EQ(9.863E-04, model.mdust);
            
            EXPECT_EQ(e_str(1.81042146778e-16), e_str(flux[0]));
            EXPECT_EQ(e_str(1.91716587819e-16), e_str(flux[1]));
            EXPECT_EQ(e_str(5.20019573545e-15), e_str(flux[2]));
            EXPECT_EQ(e_str(3.7571600065e-15), e_str(flux[3]));
            
            
            model = *modelData.modelInfrared(2);
            flux = modelData.fluxInfrared(2);
            EXPECT_DOUBLE_EQ(0.238, model.fmu_ir);
            EXPECT_DOUBLE_EQ(0.168504, model.fmu_ism);
            EXPECT_DOUBLE_EQ(37.248, model.tbg1);
            EXPECT_DOUBLE_EQ(17.715, model.tbg2);
            EXPECT_DOUBLE_EQ(0.1715728, model.xi1);
            EXPECT_DOUBLE_EQ(0.1936094, model.xi2);
            EXPECT_DOUBLE_EQ(0.4655518, model.xi3);
            EXPECT_DOUBLE_EQ(1.132E-03, model.mdust);
            
            EXPECT_EQ(e_str(2.24812104325e-16), e_str(flux[0]));
            EXPECT_EQ(e_str(2.7095657299e-16), e_str(flux[1]));
            EXPECT_EQ(e_str(8.46407866029e-15), e_str(flux[2]));
            EXPECT_EQ(e_str(8.93263710462e-15), e_str(flux[3]));
            
            
            model = *modelData.modelInfrared(3);
            flux = modelData.fluxInfrared(3);
            EXPECT_DOUBLE_EQ(0.474, model.fmu_ir);
            EXPECT_DOUBLE_EQ(0.437028, model.fmu_ism);
            EXPECT_DOUBLE_EQ(54.388, model.tbg1);
            EXPECT_DOUBLE_EQ(22.040, model.tbg2);
            EXPECT_DOUBLE_EQ(0.0250686, model.xi1);
            EXPECT_DOUBLE_EQ(0.0880153, model.xi2);
            EXPECT_DOUBLE_EQ(0.4498881, model.xi3);
            EXPECT_DOUBLE_EQ(7.304E-04, model.mdust);
            
            EXPECT_EQ(e_str(3.46688703462e-17), e_str(flux[0]));
            EXPECT_EQ(e_str(6.21984684304e-17), e_str(flux[1]));
            EXPECT_EQ(e_str(2.56956548914e-15), e_str(flux[2]));
            EXPECT_EQ(e_str(7.24669012336e-15), e_str(flux[3]));
            
            
            model = *modelData.modelInfrared(4);
            flux = modelData.fluxInfrared(4);
            EXPECT_DOUBLE_EQ(0.783, model.fmu_ir);
            EXPECT_DOUBLE_EQ(0.580203, model.fmu_ism);
            EXPECT_DOUBLE_EQ(30.199, model.tbg1);
            EXPECT_DOUBLE_EQ(16.818, model.tbg2);
            EXPECT_DOUBLE_EQ(0.13302135, model.xi1);
            EXPECT_DOUBLE_EQ(0.092659175, model.xi2);
            EXPECT_DOUBLE_EQ(0.194116475, model.xi3);
            EXPECT_DOUBLE_EQ(4.923E-03, model.mdust);
            
            EXPECT_EQ(e_str(1.77721385701e-16), e_str(flux[0]));
            EXPECT_EQ(e_str(1.91628319393e-16), e_str(flux[1]));
            EXPECT_EQ(e_str(5.31397725001e-15), e_str(flux[2]));
            EXPECT_EQ(e_str(4.12495951815e-15), e_str(flux[3]));
            
            
            model = *modelData.modelInfrared(49995);
            flux = modelData.fluxInfrared(49995);
            EXPECT_DOUBLE_EQ(0.957, model.fmu_ir);
            EXPECT_DOUBLE_EQ(0.6699, model.fmu_ism);
            EXPECT_DOUBLE_EQ(38.391, model.tbg1);
            EXPECT_DOUBLE_EQ(24.592, model.tbg2);
            EXPECT_DOUBLE_EQ(0.162291, model.xi1);
            EXPECT_DOUBLE_EQ(0.0814895, model.xi2);
            EXPECT_DOUBLE_EQ(0.0863195, model.xi3);
            EXPECT_DOUBLE_EQ(5.747E-04, model.mdust);
            
            EXPECT_EQ(e_str(2.17580359903e-16), e_str(flux[0]));
            EXPECT_EQ(e_str(2.23038425597e-16), e_str(flux[1]));
            EXPECT_EQ(e_str(5.79988911763e-15), e_str(flux[2]));
            EXPECT_EQ(e_str(3.59533771734e-15), e_str(flux[3]));
            
            
            model = *modelData.modelInfrared(49996);
            flux = modelData.fluxInfrared(49996);
            EXPECT_DOUBLE_EQ(0.694, model.fmu_ir);
            EXPECT_DOUBLE_EQ(0.54132, model.fmu_ism);
            EXPECT_DOUBLE_EQ(44.318, model.tbg1);
            EXPECT_DOUBLE_EQ(16.326, model.tbg2);
            EXPECT_DOUBLE_EQ(0.088564, model.xi1);
            EXPECT_DOUBLE_EQ(0.084827, model.xi2);
            EXPECT_DOUBLE_EQ(0.285289, model.xi3);
            EXPECT_DOUBLE_EQ(5.382E-03, model.mdust);
            
            EXPECT_EQ(e_str(1.18932265255e-16), e_str(flux[0]));
            EXPECT_EQ(e_str(1.36263547366e-16), e_str(flux[1]));
            EXPECT_EQ(e_str(4.04668771351e-15), e_str(flux[2]));
            EXPECT_EQ(e_str(4.20668207363e-15), e_str(flux[3]));
            
            
            model = *modelData.modelInfrared(49997);
            flux = modelData.fluxInfrared(49997);
            EXPECT_DOUBLE_EQ(0.631, model.fmu_ir);
            EXPECT_DOUBLE_EQ(0.581782, model.fmu_ism);
            EXPECT_DOUBLE_EQ(42.923, model.tbg1);
            EXPECT_DOUBLE_EQ(24.657, model.tbg2);
            EXPECT_DOUBLE_EQ(0.0281769, model.xi1);
            EXPECT_DOUBLE_EQ(0.09176295, model.xi2);
            EXPECT_DOUBLE_EQ(0.29827815, model.xi3);
            EXPECT_DOUBLE_EQ(5.199E-04, model.mdust);
            
            EXPECT_EQ(e_str(3.88382533848e-17), e_str(flux[0]));
            EXPECT_EQ(e_str(6.72635354794e-17), e_str(flux[1]));
            EXPECT_EQ(e_str(2.7108138184e-15), e_str(flux[2]));
            EXPECT_EQ(e_str(4.52918114622e-15), e_str(flux[3]));
            
            
            model = *modelData.modelInfrared(49998);
            flux = modelData.fluxInfrared(49998);
            EXPECT_DOUBLE_EQ(0.064, model.fmu_ir);
            EXPECT_DOUBLE_EQ(0.060288, model.fmu_ism);
            EXPECT_DOUBLE_EQ(33.611, model.tbg1);
            EXPECT_DOUBLE_EQ(22.696, model.tbg2);
            EXPECT_DOUBLE_EQ(0.0319936, model.xi1);
            EXPECT_DOUBLE_EQ(0.0796448, model.xi2);
            EXPECT_DOUBLE_EQ(0.8271376, model.xi3);
            EXPECT_DOUBLE_EQ(4.295E-04, model.mdust);
            
            EXPECT_EQ(e_str(4.28173407163e-17), e_str(flux[0]));
            EXPECT_EQ(e_str(6.69113343654e-17), e_str(flux[1]));
            EXPECT_EQ(e_str(2.54600757114e-15), e_str(flux[2]));
            EXPECT_EQ(e_str(3.71860193369e-15), e_str(flux[3]));
            
            
            model = *modelData.modelInfrared(49999);
            flux = modelData.fluxInfrared(49999);
            EXPECT_DOUBLE_EQ(0.882, model.fmu_ir);
            EXPECT_DOUBLE_EQ(0.644742, model.fmu_ism);
            EXPECT_DOUBLE_EQ(43.283, model.tbg1);
            EXPECT_DOUBLE_EQ(17.828, model.tbg2);
            EXPECT_DOUBLE_EQ(0.1309639, model.xi1);
            EXPECT_DOUBLE_EQ(0.06736995, model.xi2);
            EXPECT_DOUBLE_EQ(0.15704215, model.xi3);
            EXPECT_DOUBLE_EQ(3.772E-03, model.mdust);
            
            EXPECT_EQ(e_str(1.75412157724e-16), e_str(flux[0]));
            EXPECT_EQ(e_str(1.80309949105e-16), e_str(flux[1]));
            EXPECT_EQ(e_str(4.70608417403e-15), e_str(flux[2]));
            EXPECT_EQ(e_str(3.10412849694e-15), e_str(flux[3]));
        }

        TEST_F(ModelDataLoad, modelOptical) {
            bool result = modelData.loadFilters("../../../src/unit_test/data/filters05.dat");
            EXPECT_TRUE(result);
            vector<Filter>& filters = *modelData.filters();
            EXPECT_EQ(11, filters.size());

            EXPECT_EQ(9, modelData.nfilt_sfh());
            EXPECT_EQ(2, modelData.nfilt_mix());
            EXPECT_EQ(4, modelData.nfilt_ir());

            result = modelData.loadModelOptical("../../../src/unit_test/data/starformhist_cb07_z0.0100.lbr");
            EXPECT_TRUE(result);

            ModelOptical& model = *modelData.modelOptical(0);
            double* flux = modelData.fluxOptical(0);
                       
            EXPECT_DOUBLE_EQ(0.9180, model.fmu_sfh);
            EXPECT_DOUBLE_EQ(2.5511, model.mstr1);
            EXPECT_EQ(f_str(0.921171259457), f_str(model.ldust));
            EXPECT_EQ(f_str(-0.0356596204843), f_str(model.logldust));
            EXPECT_DOUBLE_EQ(0.7220, model.mu);
            EXPECT_DOUBLE_EQ(4.2970, model.tauv);
            EXPECT_DOUBLE_EQ(2.96E-11, model.ssfr);
            EXPECT_EQ(f_str(-10.5287082889), f_str(model.lssfr));
            EXPECT_DOUBLE_EQ(3.102434, model.tvsim);
            
            EXPECT_EQ(e_str(7.75411447095e-21), e_str(flux[0]));
            EXPECT_EQ(e_str(7.87575518951e-20), e_str(flux[1]));
            EXPECT_EQ(e_str(1.74635369745e-18), e_str(flux[2]));
            EXPECT_EQ(e_str(1.54985906585e-17), e_str(flux[3]));
            EXPECT_EQ(e_str(5.31584376116e-17), e_str(flux[4]));
            EXPECT_EQ(e_str(1.06977441759e-16), e_str(flux[5]));
            EXPECT_EQ(e_str(1.91554433464e-16), e_str(flux[6]));
            EXPECT_EQ(e_str(5.57868973145e-16), e_str(flux[7]));
            EXPECT_EQ(e_str(4.16228877735e-16), e_str(flux[8]));
            
            
            model = *modelData.modelOptical(1);
            flux = modelData.fluxOptical(1);
            
            EXPECT_DOUBLE_EQ(0.9850, model.fmu_sfh);
            EXPECT_DOUBLE_EQ(0.9455, model.mstr1);
            EXPECT_EQ(f_str(0.946589106293), f_str(model.ldust));
            EXPECT_EQ(f_str(-0.0238384978651), f_str(model.logldust));
            EXPECT_DOUBLE_EQ(0.4799, model.mu);
            EXPECT_DOUBLE_EQ(1.5080, model.tauv);
            EXPECT_DOUBLE_EQ(2.06E-12, model.ssfr);
            EXPECT_EQ(f_str(-11.6861327796), f_str(model.lssfr));
            EXPECT_DOUBLE_EQ(0.7236892, model.tvsim);
            
            EXPECT_EQ(e_str(2.33344816318e-17), e_str(flux[0]));
            EXPECT_EQ(e_str(5.17699991215e-17), e_str(flux[1]));
            EXPECT_EQ(e_str(1.8951262954e-16), e_str(flux[2]));
            EXPECT_EQ(e_str(6.55176267587e-16), e_str(flux[3]));
            EXPECT_EQ(e_str(1.0116683367e-15), e_str(flux[4]));
            EXPECT_EQ(e_str(1.41957439591e-15), e_str(flux[5]));
            EXPECT_EQ(e_str(1.99985338573e-15), e_str(flux[6]));
            EXPECT_EQ(e_str(1.7158454113e-15), e_str(flux[7]));
            EXPECT_EQ(e_str(1.13730816645e-15), e_str(flux[8]));
            
            
            model = *modelData.modelOptical(2);
            flux = modelData.fluxOptical(2);
            
            EXPECT_DOUBLE_EQ(0.1570, model.fmu_sfh);
            EXPECT_DOUBLE_EQ(0.307, model.mstr1);
            EXPECT_EQ(f_str(4.20195439739), f_str(model.ldust));
            EXPECT_EQ(f_str(0.623451334822), f_str(model.logldust));
            EXPECT_DOUBLE_EQ(0.0702, model.mu);
            EXPECT_DOUBLE_EQ(0.9018, model.tauv);
            EXPECT_DOUBLE_EQ(1.67E-10, model.ssfr);
            EXPECT_EQ(f_str(-9.77728352885), f_str(model.lssfr));
            EXPECT_DOUBLE_EQ(0.06330636, model.tvsim);
            
            EXPECT_EQ(e_str(1.0779566978e-15), e_str(flux[0]));
            EXPECT_EQ(e_str(1.22124082884e-15), e_str(flux[1]));
            EXPECT_EQ(e_str(1.94339604837e-15), e_str(flux[2]));
            EXPECT_EQ(e_str(4.50693521471e-15), e_str(flux[3]));
            EXPECT_EQ(e_str(5.65876052561e-15), e_str(flux[4]));
            EXPECT_EQ(e_str(7.21242508696e-15), e_str(flux[5]));
            EXPECT_EQ(e_str(9.50782797222e-15), e_str(flux[6]));
            EXPECT_EQ(e_str(5.02992275165e-15), e_str(flux[7]));
            EXPECT_EQ(e_str(3.05774535645e-15), e_str(flux[8]));
            
            
            model = *modelData.modelOptical(3);
            flux = modelData.fluxOptical(3);
            
            EXPECT_DOUBLE_EQ(0.9920, model.fmu_sfh);
            EXPECT_DOUBLE_EQ(0.7528, model.mstr1);
            EXPECT_EQ(f_str(0.274973432519), f_str(model.ldust));
            EXPECT_EQ(f_str(-0.560709264962), f_str(model.logldust));
            EXPECT_DOUBLE_EQ(0.3180, model.mu);
            EXPECT_DOUBLE_EQ(4.5052, model.tauv);
            EXPECT_DOUBLE_EQ(2.59E-13, model.ssfr);
            EXPECT_EQ(f_str(-12.5867002359), f_str(model.lssfr));
            EXPECT_DOUBLE_EQ(1.4326536, model.tvsim);
            
            EXPECT_EQ(e_str(3.94839033698e-20), e_str(flux[0]));
            EXPECT_EQ(e_str(1.30526917037e-19), e_str(flux[1]));
            EXPECT_EQ(e_str(3.97356279249e-18), e_str(flux[2]));
            EXPECT_EQ(e_str(3.52224920985e-17), e_str(flux[3]));
            EXPECT_EQ(e_str(1.08697631344e-16), e_str(flux[4]));
            EXPECT_EQ(e_str(1.9524507169e-16), e_str(flux[5]));
            EXPECT_EQ(e_str(3.0984185236e-16), e_str(flux[6]));
            EXPECT_EQ(e_str(4.65779189007e-16), e_str(flux[7]));
            EXPECT_EQ(e_str(3.24205277681e-16), e_str(flux[8]));
            
            
            model = *modelData.modelOptical(49308);
            flux = modelData.fluxOptical(49308);
            
            EXPECT_DOUBLE_EQ(0.9100, model.fmu_sfh);
            EXPECT_DOUBLE_EQ(0.7109, model.mstr1);
            EXPECT_EQ(f_str(3.60106906738), f_str(model.ldust));
            EXPECT_EQ(f_str(0.556431451084), f_str(model.logldust));
            EXPECT_DOUBLE_EQ(0.7684, model.mu);
            EXPECT_DOUBLE_EQ(3.4571, model.tauv);
            EXPECT_DOUBLE_EQ(3.56E-11, model.ssfr);
            EXPECT_EQ(f_str(-10.448550002), f_str(model.lssfr));
            EXPECT_DOUBLE_EQ(2.65643564, model.tvsim);
            
            EXPECT_EQ(e_str(2.03578156157e-19), e_str(flux[0]));
            EXPECT_EQ(e_str(2.43181860383e-18), e_str(flux[1]));
            EXPECT_EQ(e_str(2.65198569159e-17), e_str(flux[2]));
            EXPECT_EQ(e_str(1.58464205146e-16), e_str(flux[3]));
            EXPECT_EQ(e_str(3.26836970695e-16), e_str(flux[4]));
            EXPECT_EQ(e_str(5.21112122977e-16), e_str(flux[5]));
            EXPECT_EQ(e_str(8.27582267585e-16), e_str(flux[6]));
            EXPECT_EQ(e_str(1.96015843856e-15), e_str(flux[7]));
            EXPECT_EQ(e_str(1.51137131944e-15), e_str(flux[8]));
            
            
            model = *modelData.modelOptical(49309);
            flux = modelData.fluxOptical(49309);
            
            EXPECT_DOUBLE_EQ(0.2220, model.fmu_sfh);
            EXPECT_DOUBLE_EQ(0.4644, model.mstr1);
            EXPECT_EQ(f_str(1.26399655469), f_str(model.ldust));
            EXPECT_EQ(f_str(0.101745890181), f_str(model.logldust));
            EXPECT_DOUBLE_EQ(0.3335, model.mu);
            EXPECT_DOUBLE_EQ(0.1394, model.tauv);
            EXPECT_DOUBLE_EQ(1.63E-10, model.ssfr);
            EXPECT_EQ(f_str(-9.7878123956), f_str(model.lssfr));
            EXPECT_DOUBLE_EQ(0.0464899, model.tvsim);
            
            EXPECT_EQ(e_str(9.30352394482e-16), e_str(flux[0]));
            EXPECT_EQ(e_str(1.03296945534e-15), e_str(flux[1]));
            EXPECT_EQ(e_str(1.48281673812e-15), e_str(flux[2]));
            EXPECT_EQ(e_str(3.35496102844e-15), e_str(flux[3]));
            EXPECT_EQ(e_str(4.40116326836e-15), e_str(flux[4]));
            EXPECT_EQ(e_str(5.45315044853e-15), e_str(flux[5]));
            EXPECT_EQ(e_str(6.96895210404e-15), e_str(flux[6]));
            EXPECT_EQ(e_str(4.77185765043e-15), e_str(flux[7]));
            EXPECT_EQ(e_str(3.08210535279e-15), e_str(flux[8]));
            
            
            model = *modelData.modelOptical(49310);
            flux = modelData.fluxOptical(49310);
            
            EXPECT_DOUBLE_EQ(0.4790, model.fmu_sfh);
            EXPECT_DOUBLE_EQ(0.2587, model.mstr1);
            EXPECT_EQ(f_str(8.9679165056), f_str(model.ldust));
            EXPECT_EQ(f_str(0.952691556174), f_str(model.logldust));
            EXPECT_DOUBLE_EQ(0.5718, model.mu);
            EXPECT_DOUBLE_EQ(2.0988, model.tauv);
            EXPECT_DOUBLE_EQ(1.92E-10, model.ssfr);
            EXPECT_EQ(f_str(-9.7166987713), f_str(model.lssfr));
            EXPECT_DOUBLE_EQ(1.20009384, model.tvsim);
            
            EXPECT_EQ(e_str(4.45967552923e-17), e_str(flux[0]));
            EXPECT_EQ(e_str(1.20498949859e-16), e_str(flux[1]));
            EXPECT_EQ(e_str(3.57423630716e-16), e_str(flux[2]));
            EXPECT_EQ(e_str(1.04911539995e-15), e_str(flux[3]));
            EXPECT_EQ(e_str(1.61801767724e-15), e_str(flux[4]));
            EXPECT_EQ(e_str(2.21892826388e-15), e_str(flux[5]));
            EXPECT_EQ(e_str(3.12279346659e-15), e_str(flux[6]));
            EXPECT_EQ(e_str(4.43183172544e-15), e_str(flux[7]));
            EXPECT_EQ(e_str(3.18730234364e-15), e_str(flux[8]));
            
            
            model = *modelData.modelOptical(49311);
            flux = modelData.fluxOptical(49311);
            
            EXPECT_DOUBLE_EQ(1.0000, model.fmu_sfh);
            EXPECT_DOUBLE_EQ(1.0672, model.mstr1);
            EXPECT_EQ(f_str(0.413230884558), f_str(model.ldust));
            EXPECT_EQ(f_str(-0.383807227105), f_str(model.logldust));
            EXPECT_DOUBLE_EQ(0.4940, model.mu);
            EXPECT_DOUBLE_EQ(3.1263, model.tauv);
            EXPECT_DOUBLE_EQ(1.81E-14, model.ssfr);
            EXPECT_EQ(f_str(-13.7423214251), f_str(model.lssfr));
            EXPECT_DOUBLE_EQ(1.5443922, model.tvsim);
            
            EXPECT_EQ(e_str(2.40421816552e-20), e_str(flux[0]));
            EXPECT_EQ(e_str(3.13916305304e-19), e_str(flux[1]));
            EXPECT_EQ(e_str(9.59873217754e-18), e_str(flux[2]));
            EXPECT_EQ(e_str(6.17637809755e-17), e_str(flux[3]));
            EXPECT_EQ(e_str(1.63701958108e-16), e_str(flux[4]));
            EXPECT_EQ(e_str(2.76219207069e-16), e_str(flux[5]));
            EXPECT_EQ(e_str(4.2124414179e-16), e_str(flux[6]));
            EXPECT_EQ(e_str(5.45875841249e-16), e_str(flux[7]));
            EXPECT_EQ(e_str(3.48637319806e-16), e_str(flux[8]));
            
            
            model = *modelData.modelOptical(49312);
            flux = modelData.fluxOptical(49312);
            
            EXPECT_DOUBLE_EQ(0.7600, model.fmu_sfh);
            EXPECT_DOUBLE_EQ(0.4805, model.mstr1);
            EXPECT_EQ(f_str(1.28199791883), f_str(model.ldust));
            EXPECT_EQ(f_str(0.10788732016), f_str(model.logldust));
            EXPECT_DOUBLE_EQ(0.5172, model.mu);
            EXPECT_DOUBLE_EQ(4.7424, model.tauv);
            EXPECT_DOUBLE_EQ(2.20E-11, model.ssfr);
            EXPECT_EQ(f_str(-10.6575773192), f_str(model.lssfr));
            EXPECT_DOUBLE_EQ(2.45276928, model.tvsim);
            
            EXPECT_EQ(e_str(1.88298256497e-19), e_str(flux[0]));
            EXPECT_EQ(e_str(9.79504191542e-19), e_str(flux[1]));
            EXPECT_EQ(e_str(7.64480300514e-18), e_str(flux[2]));
            EXPECT_EQ(e_str(4.32799049972e-17), e_str(flux[3]));
            EXPECT_EQ(e_str(1.13785336655e-16), e_str(flux[4]));
            EXPECT_EQ(e_str(2.02920675231e-16), e_str(flux[5]));
            EXPECT_EQ(e_str(3.31807576729e-16), e_str(flux[6]));
            EXPECT_EQ(e_str(6.37978875521e-16), e_str(flux[7]));
            EXPECT_EQ(e_str(4.37447862509e-16), e_str(flux[8]));
        }
    }
} //namespace magphys
