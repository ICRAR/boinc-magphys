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

BOOST_AUTO_TEST_SUITE(ModelDataLoadTests)

BOOST_AUTO_TEST_CASE(modelInfrared) {
    magphys::ModelData modelData { 0.0037000 };
    bool result = modelData.loadFilters(path + "filters05.dat");
    BOOST_REQUIRE(result);
    vector<magphys::Filter>& filters = *modelData.filters();
    BOOST_REQUIRE_EQUAL(11, filters.size());

    BOOST_REQUIRE_EQUAL(9, modelData.nfilt_sfh());
    BOOST_REQUIRE_EQUAL(2, modelData.nfilt_mix());
    BOOST_REQUIRE_EQUAL(4, modelData.nfilt_ir());

    result = modelData.loadModelInfrared(path + "infrared_dce08_z0.0100.lbr");
    BOOST_REQUIRE(result);

    // Checking line 0
    magphys::ModelInfrared& model = *modelData.modelInfrared(0);
    double* flux = modelData.fluxInfrared(0);

    // The body of line 0
    BOOST_CHECK_CLOSE(0.038, model.fmu_ir__, 0.001);
    BOOST_CHECK_CLOSE(0.031388, model.fmu_ism__, 0.001);
    BOOST_CHECK_CLOSE(38.052, model.tbg1__, 0.001);
    BOOST_CHECK_CLOSE(18.623, model.tbg2__, 0.001);
    BOOST_CHECK_CLOSE(0.0209526, model.xi1__, 0.001);
    BOOST_CHECK_CLOSE(0.1538143, model.xi2__, 0.001);
    BOOST_CHECK_CLOSE(0.7938451, model.xi3__, 0.001);
    BOOST_CHECK_CLOSE(3.104E-04, model.mdust__, 0.001);

    BOOST_CHECK_CLOSE(2.9554232857e-17, flux[0], 0.001);
    BOOST_CHECK_CLOSE(8.11969452594e-17, flux[1], 0.001);
    BOOST_CHECK_CLOSE(3.89421289735e-15, flux[2], 0.001);
    BOOST_CHECK_CLOSE(7.29087564383e-15, flux[3], 0.001);


    // Checking line 1
    model = *modelData.modelInfrared(1);
    flux = modelData.fluxInfrared(1);

    // The body of line 1
    BOOST_CHECK_CLOSE(0.764, model.fmu_ir__, 0.001);
    BOOST_CHECK_CLOSE(0.566888, model.fmu_ism__, 0.001);
    BOOST_CHECK_CLOSE(32.412, model.tbg1__, 0.001);
    BOOST_CHECK_CLOSE(22.175, model.tbg2__, 0.001);
    BOOST_CHECK_CLOSE(0.1360236, model.xi1__, 0.001);
    BOOST_CHECK_CLOSE(0.0844138, model.xi2__, 0.001);
    BOOST_CHECK_CLOSE(0.2129106, model.xi3__, 0.001);
    BOOST_CHECK_CLOSE(9.863E-04, model.mdust__, 0.001);

    BOOST_CHECK_CLOSE(1.81042146778e-16, flux[0], 0.001);
    BOOST_CHECK_CLOSE(1.91716587819e-16, flux[1], 0.001);
    BOOST_CHECK_CLOSE(5.20019573545e-15, flux[2], 0.001);
    BOOST_CHECK_CLOSE(3.7571600065e-15, flux[3], 0.001);


    // Checking line 2
    model = *modelData.modelInfrared(2);
    flux = modelData.fluxInfrared(2);

    // The body of line 2
    BOOST_CHECK_CLOSE(0.238, model.fmu_ir__, 0.001);
    BOOST_CHECK_CLOSE(0.168504, model.fmu_ism__, 0.001);
    BOOST_CHECK_CLOSE(37.248, model.tbg1__, 0.001);
    BOOST_CHECK_CLOSE(17.715, model.tbg2__, 0.001);
    BOOST_CHECK_CLOSE(0.1715728, model.xi1__, 0.001);
    BOOST_CHECK_CLOSE(0.1936094, model.xi2__, 0.001);
    BOOST_CHECK_CLOSE(0.4655518, model.xi3__, 0.001);
    BOOST_CHECK_CLOSE(1.132E-03, model.mdust__, 0.001);

    BOOST_CHECK_CLOSE(2.24812104325e-16, flux[0], 0.001);
    BOOST_CHECK_CLOSE(2.7095657299e-16, flux[1], 0.001);
    BOOST_CHECK_CLOSE(8.46407866029e-15, flux[2], 0.001);
    BOOST_CHECK_CLOSE(8.93263710462e-15, flux[3], 0.001);


    // Checking line 3
    model = *modelData.modelInfrared(3);
    flux = modelData.fluxInfrared(3);

    // The body of line 3
    BOOST_CHECK_CLOSE(0.474, model.fmu_ir__, 0.001);
    BOOST_CHECK_CLOSE(0.437028, model.fmu_ism__, 0.001);
    BOOST_CHECK_CLOSE(54.388, model.tbg1__, 0.001);
    BOOST_CHECK_CLOSE(22.040, model.tbg2__, 0.001);
    BOOST_CHECK_CLOSE(0.0250686, model.xi1__, 0.001);
    BOOST_CHECK_CLOSE(0.0880153, model.xi2__, 0.001);
    BOOST_CHECK_CLOSE(0.4498881, model.xi3__, 0.001);
    BOOST_CHECK_CLOSE(7.304E-04, model.mdust__, 0.001);

    BOOST_CHECK_CLOSE(3.46688703462e-17, flux[0], 0.001);
    BOOST_CHECK_CLOSE(6.21984684304e-17, flux[1], 0.001);
    BOOST_CHECK_CLOSE(2.56956548914e-15, flux[2], 0.001);
    BOOST_CHECK_CLOSE(7.24669012336e-15, flux[3], 0.001);


    // Checking line 4
    model = *modelData.modelInfrared(4);
    flux = modelData.fluxInfrared(4);

    // The body of line 4
    BOOST_CHECK_CLOSE(0.783, model.fmu_ir__, 0.001);
    BOOST_CHECK_CLOSE(0.580203, model.fmu_ism__, 0.001);
    BOOST_CHECK_CLOSE(30.199, model.tbg1__, 0.001);
    BOOST_CHECK_CLOSE(16.818, model.tbg2__, 0.001);
    BOOST_CHECK_CLOSE(0.13302135, model.xi1__, 0.001);
    BOOST_CHECK_CLOSE(0.092659175, model.xi2__, 0.001);
    BOOST_CHECK_CLOSE(0.194116475, model.xi3__, 0.001);
    BOOST_CHECK_CLOSE(4.923E-03, model.mdust__, 0.001);

    BOOST_CHECK_CLOSE(1.77721385701e-16, flux[0], 0.001);
    BOOST_CHECK_CLOSE(1.91628319393e-16, flux[1], 0.001);
    BOOST_CHECK_CLOSE(5.31397725001e-15, flux[2], 0.001);
    BOOST_CHECK_CLOSE(4.12495951815e-15, flux[3], 0.001);


    // Checking line 49995
    model = *modelData.modelInfrared(49995);
    flux = modelData.fluxInfrared(49995);

    // The body of line 49995
    BOOST_CHECK_CLOSE(0.957, model.fmu_ir__, 0.001);
    BOOST_CHECK_CLOSE(0.6699, model.fmu_ism__, 0.001);
    BOOST_CHECK_CLOSE(38.391, model.tbg1__, 0.001);
    BOOST_CHECK_CLOSE(24.592, model.tbg2__, 0.001);
    BOOST_CHECK_CLOSE(0.162291, model.xi1__, 0.001);
    BOOST_CHECK_CLOSE(0.0814895, model.xi2__, 0.001);
    BOOST_CHECK_CLOSE(0.0863195, model.xi3__, 0.001);
    BOOST_CHECK_CLOSE(5.747E-04, model.mdust__, 0.001);

    BOOST_CHECK_CLOSE(2.17580359903e-16, flux[0], 0.001);
    BOOST_CHECK_CLOSE(2.23038425597e-16, flux[1], 0.001);
    BOOST_CHECK_CLOSE(5.79988911763e-15, flux[2], 0.001);
    BOOST_CHECK_CLOSE(3.59533771734e-15, flux[3], 0.001);


    // Checking line 49996
    model = *modelData.modelInfrared(49996);
    flux = modelData.fluxInfrared(49996);

    // The body of line 49996
    BOOST_CHECK_CLOSE(0.694, model.fmu_ir__, 0.001);
    BOOST_CHECK_CLOSE(0.54132, model.fmu_ism__, 0.001);
    BOOST_CHECK_CLOSE(44.318, model.tbg1__, 0.001);
    BOOST_CHECK_CLOSE(16.326, model.tbg2__, 0.001);
    BOOST_CHECK_CLOSE(0.088564, model.xi1__, 0.001);
    BOOST_CHECK_CLOSE(0.084827, model.xi2__, 0.001);
    BOOST_CHECK_CLOSE(0.285289, model.xi3__, 0.001);
    BOOST_CHECK_CLOSE(5.382E-03, model.mdust__, 0.001);

    BOOST_CHECK_CLOSE(1.18932265255e-16, flux[0], 0.001);
    BOOST_CHECK_CLOSE(1.36263547366e-16, flux[1], 0.001);
    BOOST_CHECK_CLOSE(4.04668771351e-15, flux[2], 0.001);
    BOOST_CHECK_CLOSE(4.20668207363e-15, flux[3], 0.001);


    // Checking line 49997
    model = *modelData.modelInfrared(49997);
    flux = modelData.fluxInfrared(49997);

    // The body of line 49997
    BOOST_CHECK_CLOSE(0.631, model.fmu_ir__, 0.001);
    BOOST_CHECK_CLOSE(0.581782, model.fmu_ism__, 0.001);
    BOOST_CHECK_CLOSE(42.923, model.tbg1__, 0.001);
    BOOST_CHECK_CLOSE(24.657, model.tbg2__, 0.001);
    BOOST_CHECK_CLOSE(0.0281769, model.xi1__, 0.001);
    BOOST_CHECK_CLOSE(0.09176295, model.xi2__, 0.001);
    BOOST_CHECK_CLOSE(0.29827815, model.xi3__, 0.001);
    BOOST_CHECK_CLOSE(5.199E-04, model.mdust__, 0.001);

    BOOST_CHECK_CLOSE(3.88382533848e-17, flux[0], 0.001);
    BOOST_CHECK_CLOSE(6.72635354794e-17, flux[1], 0.001);
    BOOST_CHECK_CLOSE(2.7108138184e-15, flux[2], 0.001);
    BOOST_CHECK_CLOSE(4.52918114622e-15, flux[3], 0.001);


    // Checking line 49998
    model = *modelData.modelInfrared(49998);
    flux = modelData.fluxInfrared(49998);

    // The body of line 49998
    BOOST_CHECK_CLOSE(0.064, model.fmu_ir__, 0.001);
    BOOST_CHECK_CLOSE(0.060288, model.fmu_ism__, 0.001);
    BOOST_CHECK_CLOSE(33.611, model.tbg1__, 0.001);
    BOOST_CHECK_CLOSE(22.696, model.tbg2__, 0.001);
    BOOST_CHECK_CLOSE(0.0319936, model.xi1__, 0.001);
    BOOST_CHECK_CLOSE(0.0796448, model.xi2__, 0.001);
    BOOST_CHECK_CLOSE(0.8271376, model.xi3__, 0.001);
    BOOST_CHECK_CLOSE(4.295E-04, model.mdust__, 0.001);

    BOOST_CHECK_CLOSE(4.28173407163e-17, flux[0], 0.001);
    BOOST_CHECK_CLOSE(6.69113343654e-17, flux[1], 0.001);
    BOOST_CHECK_CLOSE(2.54600757114e-15, flux[2], 0.001);
    BOOST_CHECK_CLOSE(3.71860193369e-15, flux[3], 0.001);


    // Checking line 49999
    model = *modelData.modelInfrared(49999);
    flux = modelData.fluxInfrared(49999);

    // The body of line 49999
    BOOST_CHECK_CLOSE(0.882, model.fmu_ir__, 0.001);
    BOOST_CHECK_CLOSE(0.644742, model.fmu_ism__, 0.001);
    BOOST_CHECK_CLOSE(43.283, model.tbg1__, 0.001);
    BOOST_CHECK_CLOSE(17.828, model.tbg2__, 0.001);
    BOOST_CHECK_CLOSE(0.1309639, model.xi1__, 0.001);
    BOOST_CHECK_CLOSE(0.06736995, model.xi2__, 0.001);
    BOOST_CHECK_CLOSE(0.15704215, model.xi3__, 0.001);
    BOOST_CHECK_CLOSE(3.772E-03, model.mdust__, 0.001);

    BOOST_CHECK_CLOSE(1.75412157724e-16, flux[0], 0.001);
    BOOST_CHECK_CLOSE(1.80309949105e-16, flux[1], 0.001);
    BOOST_CHECK_CLOSE(4.70608417403e-15, flux[2], 0.001);
    BOOST_CHECK_CLOSE(3.10412849694e-15, flux[3], 0.001);
}

BOOST_AUTO_TEST_CASE(modelOptical) {
    magphys::ModelData modelData { 0.0037000 };
    bool result = modelData.loadFilters(path + "filters05.dat");
    BOOST_REQUIRE(result);
    vector<magphys::Filter>& filters = *modelData.filters();
    BOOST_REQUIRE_EQUAL(11, filters.size());

    BOOST_REQUIRE_EQUAL(9, modelData.nfilt_sfh());
    BOOST_REQUIRE_EQUAL(2, modelData.nfilt_mix());
    BOOST_REQUIRE_EQUAL(4, modelData.nfilt_ir());

    result = modelData.loadModelOptical(path + "starformhist_cb07_z0.0100.lbr");
    BOOST_REQUIRE(result);

    // Checking line 0
    magphys::ModelOptical& model = *modelData.modelOptical(0);
    double* flux = modelData.fluxOptical(0);

    // The body of line 0
    BOOST_CHECK_CLOSE(0.9180, model.fmu_sfh__, 0.001);
    BOOST_CHECK_CLOSE(2.5511, model.mstr1__, 0.001);
    BOOST_CHECK_CLOSE(0.921171259457, model.ldust__, 0.001);
    BOOST_CHECK_CLOSE(-0.0356596204843, model.logldust__, 0.001);
    BOOST_CHECK_CLOSE(0.7220, model.mu__, 0.001);
    BOOST_CHECK_CLOSE(4.2970, model.tauv__, 0.001);
    BOOST_CHECK_CLOSE(2.96E-11, model.ssfr__, 0.001);
    BOOST_CHECK_CLOSE(-10.5287082889, model.lssfr__, 0.001);
    BOOST_CHECK_CLOSE(3.102434, model.tvsim__, 0.001);

    BOOST_CHECK_CLOSE(7.75411447095e-21, flux[0], 0.001);
    BOOST_CHECK_CLOSE(7.87575518951e-20, flux[1], 0.001);
    BOOST_CHECK_CLOSE(1.74635369745e-18, flux[2], 0.001);
    BOOST_CHECK_CLOSE(1.54985906585e-17, flux[3], 0.001);
    BOOST_CHECK_CLOSE(5.31584376116e-17, flux[4], 0.001);
    BOOST_CHECK_CLOSE(1.06977441759e-16, flux[5], 0.001);
    BOOST_CHECK_CLOSE(1.91554433464e-16, flux[6], 0.001);
    BOOST_CHECK_CLOSE(5.57868973145e-16, flux[7], 0.001);
    BOOST_CHECK_CLOSE(4.16228877735e-16, flux[8], 0.001);


    // Checking line 1
    model = *modelData.modelOptical(1);
    flux = modelData.fluxOptical(1);

    // The body of line 1
    BOOST_CHECK_CLOSE(0.9850, model.fmu_sfh__, 0.001);
    BOOST_CHECK_CLOSE(0.9455, model.mstr1__, 0.001);
    BOOST_CHECK_CLOSE(0.946589106293, model.ldust__, 0.001);
    BOOST_CHECK_CLOSE(-0.0238384978651, model.logldust__, 0.001);
    BOOST_CHECK_CLOSE(0.4799, model.mu__, 0.001);
    BOOST_CHECK_CLOSE(1.5080, model.tauv__, 0.001);
    BOOST_CHECK_CLOSE(2.06E-12, model.ssfr__, 0.001);
    BOOST_CHECK_CLOSE(-11.6861327796, model.lssfr__, 0.001);
    BOOST_CHECK_CLOSE(0.7236892, model.tvsim__, 0.001);

    BOOST_CHECK_CLOSE(2.33344816318e-17, flux[0], 0.001);
    BOOST_CHECK_CLOSE(5.17699991215e-17, flux[1], 0.001);
    BOOST_CHECK_CLOSE(1.8951262954e-16, flux[2], 0.001);
    BOOST_CHECK_CLOSE(6.55176267587e-16, flux[3], 0.001);
    BOOST_CHECK_CLOSE(1.0116683367e-15, flux[4], 0.001);
    BOOST_CHECK_CLOSE(1.41957439591e-15, flux[5], 0.001);
    BOOST_CHECK_CLOSE(1.99985338573e-15, flux[6], 0.001);
    BOOST_CHECK_CLOSE(1.7158454113e-15, flux[7], 0.001);
    BOOST_CHECK_CLOSE(1.13730816645e-15, flux[8], 0.001);


    // Checking line 2
    model = *modelData.modelOptical(2);
    flux = modelData.fluxOptical(2);

    // The body of line 2
    BOOST_CHECK_CLOSE(0.1570, model.fmu_sfh__, 0.001);
    BOOST_CHECK_CLOSE(0.307, model.mstr1__, 0.001);
    BOOST_CHECK_CLOSE(4.20195439739, model.ldust__, 0.001);
    BOOST_CHECK_CLOSE(0.623451334822, model.logldust__, 0.001);
    BOOST_CHECK_CLOSE(0.0702, model.mu__, 0.001);
    BOOST_CHECK_CLOSE(0.9018, model.tauv__, 0.001);
    BOOST_CHECK_CLOSE(1.67E-10, model.ssfr__, 0.001);
    BOOST_CHECK_CLOSE(-9.77728352885, model.lssfr__, 0.001);
    BOOST_CHECK_CLOSE(0.06330636, model.tvsim__, 0.001);

    BOOST_CHECK_CLOSE(1.0779566978e-15, flux[0], 0.001);
    BOOST_CHECK_CLOSE(1.22124082884e-15, flux[1], 0.001);
    BOOST_CHECK_CLOSE(1.94339604837e-15, flux[2], 0.001);
    BOOST_CHECK_CLOSE(4.50693521471e-15, flux[3], 0.001);
    BOOST_CHECK_CLOSE(5.65876052561e-15, flux[4], 0.001);
    BOOST_CHECK_CLOSE(7.21242508696e-15, flux[5], 0.001);
    BOOST_CHECK_CLOSE(9.50782797222e-15, flux[6], 0.001);
    BOOST_CHECK_CLOSE(5.02992275165e-15, flux[7], 0.001);
    BOOST_CHECK_CLOSE(3.05774535645e-15, flux[8], 0.001);


    // Checking line 3
    model = *modelData.modelOptical(3);
    flux = modelData.fluxOptical(3);

    // The body of line 3
    BOOST_CHECK_CLOSE(0.9920, model.fmu_sfh__, 0.001);
    BOOST_CHECK_CLOSE(0.7528, model.mstr1__, 0.001);
    BOOST_CHECK_CLOSE(0.274973432519, model.ldust__, 0.001);
    BOOST_CHECK_CLOSE(-0.560709264962, model.logldust__, 0.001);
    BOOST_CHECK_CLOSE(0.3180, model.mu__, 0.001);
    BOOST_CHECK_CLOSE(4.5052, model.tauv__, 0.001);
    BOOST_CHECK_CLOSE(2.59E-13, model.ssfr__, 0.001);
    BOOST_CHECK_CLOSE(-12.5867002359, model.lssfr__, 0.001);
    BOOST_CHECK_CLOSE(1.4326536, model.tvsim__, 0.001);

    BOOST_CHECK_CLOSE(3.94839033698e-20, flux[0], 0.001);
    BOOST_CHECK_CLOSE(1.30526917037e-19, flux[1], 0.001);
    BOOST_CHECK_CLOSE(3.97356279249e-18, flux[2], 0.001);
    BOOST_CHECK_CLOSE(3.52224920985e-17, flux[3], 0.001);
    BOOST_CHECK_CLOSE(1.08697631344e-16, flux[4], 0.001);
    BOOST_CHECK_CLOSE(1.9524507169e-16, flux[5], 0.001);
    BOOST_CHECK_CLOSE(3.0984185236e-16, flux[6], 0.001);
    BOOST_CHECK_CLOSE(4.65779189007e-16, flux[7], 0.001);
    BOOST_CHECK_CLOSE(3.24205277681e-16, flux[8], 0.001);


    // Checking line 49308
    model = *modelData.modelOptical(49308);
    flux = modelData.fluxOptical(49308);

    // The body of line 49308
    BOOST_CHECK_CLOSE(0.9100, model.fmu_sfh__, 0.001);
    BOOST_CHECK_CLOSE(0.7109, model.mstr1__, 0.001);
    BOOST_CHECK_CLOSE(3.60106906738, model.ldust__, 0.001);
    BOOST_CHECK_CLOSE(0.556431451084, model.logldust__, 0.001);
    BOOST_CHECK_CLOSE(0.7684, model.mu__, 0.001);
    BOOST_CHECK_CLOSE(3.4571, model.tauv__, 0.001);
    BOOST_CHECK_CLOSE(3.56E-11, model.ssfr__, 0.001);
    BOOST_CHECK_CLOSE(-10.448550002, model.lssfr__, 0.001);
    BOOST_CHECK_CLOSE(2.65643564, model.tvsim__, 0.001);

    BOOST_CHECK_CLOSE(2.03578156157e-19, flux[0], 0.001);
    BOOST_CHECK_CLOSE(2.43181860383e-18, flux[1], 0.001);
    BOOST_CHECK_CLOSE(2.65198569159e-17, flux[2], 0.001);
    BOOST_CHECK_CLOSE(1.58464205146e-16, flux[3], 0.001);
    BOOST_CHECK_CLOSE(3.26836970695e-16, flux[4], 0.001);
    BOOST_CHECK_CLOSE(5.21112122977e-16, flux[5], 0.001);
    BOOST_CHECK_CLOSE(8.27582267585e-16, flux[6], 0.001);
    BOOST_CHECK_CLOSE(1.96015843856e-15, flux[7], 0.001);
    BOOST_CHECK_CLOSE(1.51137131944e-15, flux[8], 0.001);


    // Checking line 49309
    model = *modelData.modelOptical(49309);
    flux = modelData.fluxOptical(49309);

    // The body of line 49309
    BOOST_CHECK_CLOSE(0.2220, model.fmu_sfh__, 0.001);
    BOOST_CHECK_CLOSE(0.4644, model.mstr1__, 0.001);
    BOOST_CHECK_CLOSE(1.26399655469, model.ldust__, 0.001);
    BOOST_CHECK_CLOSE(0.101745890181, model.logldust__, 0.001);
    BOOST_CHECK_CLOSE(0.3335, model.mu__, 0.001);
    BOOST_CHECK_CLOSE(0.1394, model.tauv__, 0.001);
    BOOST_CHECK_CLOSE(1.63E-10, model.ssfr__, 0.001);
    BOOST_CHECK_CLOSE(-9.7878123956, model.lssfr__, 0.001);
    BOOST_CHECK_CLOSE(0.0464899, model.tvsim__, 0.001);

    BOOST_CHECK_CLOSE(9.30352394482e-16, flux[0], 0.001);
    BOOST_CHECK_CLOSE(1.03296945534e-15, flux[1], 0.001);
    BOOST_CHECK_CLOSE(1.48281673812e-15, flux[2], 0.001);
    BOOST_CHECK_CLOSE(3.35496102844e-15, flux[3], 0.001);
    BOOST_CHECK_CLOSE(4.40116326836e-15, flux[4], 0.001);
    BOOST_CHECK_CLOSE(5.45315044853e-15, flux[5], 0.001);
    BOOST_CHECK_CLOSE(6.96895210404e-15, flux[6], 0.001);
    BOOST_CHECK_CLOSE(4.77185765043e-15, flux[7], 0.001);
    BOOST_CHECK_CLOSE(3.08210535279e-15, flux[8], 0.001);


    // Checking line 49310
    model = *modelData.modelOptical(49310);
    flux = modelData.fluxOptical(49310);

    // The body of line 49310
    BOOST_CHECK_CLOSE(0.4790, model.fmu_sfh__, 0.001);
    BOOST_CHECK_CLOSE(0.2587, model.mstr1__, 0.001);
    BOOST_CHECK_CLOSE(8.9679165056, model.ldust__, 0.001);
    BOOST_CHECK_CLOSE(0.952691556174, model.logldust__, 0.001);
    BOOST_CHECK_CLOSE(0.5718, model.mu__, 0.001);
    BOOST_CHECK_CLOSE(2.0988, model.tauv__, 0.001);
    BOOST_CHECK_CLOSE(1.92E-10, model.ssfr__, 0.001);
    BOOST_CHECK_CLOSE(-9.7166987713, model.lssfr__, 0.001);
    BOOST_CHECK_CLOSE(1.20009384, model.tvsim__, 0.001);

    BOOST_CHECK_CLOSE(4.45967552923e-17, flux[0], 0.001);
    BOOST_CHECK_CLOSE(1.20498949859e-16, flux[1], 0.001);
    BOOST_CHECK_CLOSE(3.57423630716e-16, flux[2], 0.001);
    BOOST_CHECK_CLOSE(1.04911539995e-15, flux[3], 0.001);
    BOOST_CHECK_CLOSE(1.61801767724e-15, flux[4], 0.001);
    BOOST_CHECK_CLOSE(2.21892826388e-15, flux[5], 0.001);
    BOOST_CHECK_CLOSE(3.12279346659e-15, flux[6], 0.001);
    BOOST_CHECK_CLOSE(4.43183172544e-15, flux[7], 0.001);
    BOOST_CHECK_CLOSE(3.18730234364e-15, flux[8], 0.001);


    // Checking line 49311
    model = *modelData.modelOptical(49311);
    flux = modelData.fluxOptical(49311);

    // The body of line 49311
    BOOST_CHECK_CLOSE(1.0000, model.fmu_sfh__, 0.001);
    BOOST_CHECK_CLOSE(1.0672, model.mstr1__, 0.001);
    BOOST_CHECK_CLOSE(0.413230884558, model.ldust__, 0.001);
    BOOST_CHECK_CLOSE(-0.383807227105, model.logldust__, 0.001);
    BOOST_CHECK_CLOSE(0.4940, model.mu__, 0.001);
    BOOST_CHECK_CLOSE(3.1263, model.tauv__, 0.001);
    BOOST_CHECK_CLOSE(1.81E-14, model.ssfr__, 0.001);
    BOOST_CHECK_CLOSE(-13.7423214251, model.lssfr__, 0.001);
    BOOST_CHECK_CLOSE(1.5443922, model.tvsim__, 0.001);

    BOOST_CHECK_CLOSE(2.40421816552e-20, flux[0], 0.001);
    BOOST_CHECK_CLOSE(3.13916305304e-19, flux[1], 0.001);
    BOOST_CHECK_CLOSE(9.59873217754e-18, flux[2], 0.001);
    BOOST_CHECK_CLOSE(6.17637809755e-17, flux[3], 0.001);
    BOOST_CHECK_CLOSE(1.63701958108e-16, flux[4], 0.001);
    BOOST_CHECK_CLOSE(2.76219207069e-16, flux[5], 0.001);
    BOOST_CHECK_CLOSE(4.2124414179e-16, flux[6], 0.001);
    BOOST_CHECK_CLOSE(5.45875841249e-16, flux[7], 0.001);
    BOOST_CHECK_CLOSE(3.48637319806e-16, flux[8], 0.001);


    // Checking line 49312
    model = *modelData.modelOptical(49312);
    flux = modelData.fluxOptical(49312);

    // The body of line 49312
    BOOST_CHECK_CLOSE(0.7600, model.fmu_sfh__, 0.001);
    BOOST_CHECK_CLOSE(0.4805, model.mstr1__, 0.001);
    BOOST_CHECK_CLOSE(1.28199791883, model.ldust__, 0.001);
    BOOST_CHECK_CLOSE(0.10788732016, model.logldust__, 0.001);
    BOOST_CHECK_CLOSE(0.5172, model.mu__, 0.001);
    BOOST_CHECK_CLOSE(4.7424, model.tauv__, 0.001);
    BOOST_CHECK_CLOSE(2.20E-11, model.ssfr__, 0.001);
    BOOST_CHECK_CLOSE(-10.6575773192, model.lssfr__, 0.001);
    BOOST_CHECK_CLOSE(2.45276928, model.tvsim__, 0.001);

    BOOST_CHECK_CLOSE(1.88298256497e-19, flux[0], 0.001);
    BOOST_CHECK_CLOSE(9.79504191542e-19, flux[1], 0.001);
    BOOST_CHECK_CLOSE(7.64480300514e-18, flux[2], 0.001);
    BOOST_CHECK_CLOSE(4.32799049972e-17, flux[3], 0.001);
    BOOST_CHECK_CLOSE(1.13785336655e-16, flux[4], 0.001);
    BOOST_CHECK_CLOSE(2.02920675231e-16, flux[5], 0.001);
    BOOST_CHECK_CLOSE(3.31807576729e-16, flux[6], 0.001);
    BOOST_CHECK_CLOSE(6.37978875521e-16, flux[7], 0.001);
    BOOST_CHECK_CLOSE(4.37447862509e-16, flux[8], 0.001);
}

BOOST_AUTO_TEST_SUITE_END()
