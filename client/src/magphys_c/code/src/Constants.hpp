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

#include <cstdlib>

#ifndef CONSTANTS_HPP
#define CONSTANTS_HPP

#define NMAX 50
#define NMOD 50001
#define NPROP_SFH 24
#define NPROP_IR 8
#define NZMAX 5000
#define NBINMAX1 3000
#define NBINMAX2 300
#define MIN_HPBV 0.00001

/*
 * As this could is based one the MAGPHYS code I've tried to use the same variable names.
 * The main difference is I postfix them with __
 */

namespace magphys {

struct Filter {
    string filterName__;
    double lambdaEff__;
    int filterId__;
    int fit__;
};

struct Observation {
    double flux_obs__ = 0;
    double sigma__ = 0;
    double w__ = 0;
};

struct ObservationLine {
    string galaxyName__;
    double redshift__;
    vector<Observation> observations__;
};

struct ModelOptical {
    double fmu_sfh__;     // fmu parameter Ld(ISM)/Ld(tot) - optical
    double mstr1__;       // stellar mass
    double ldust__;       // total luminosity of dust (normalize to Mstar)
    double logldust__;    // log(ldust__)
    double mu__;          // mu parameter (CF00 model)
    double tauv__;        // optical V-band depth tauV (CF00 model)
    double ssfr__;        // recent SSFR_0.01Gyr / stellar mass
    double lssfr__;       // log(SSFR_0.01Gyr)
    double tvsim__;       // mu*tauV=V-band optical depth for ISM
};

struct ModelInfrared {
    double fmu_ir__;      // fmu parameter Ld(ISM)/Ld(tot) - infrared
    double fmu_ism__;     // xi_C^ISM [cont. cold dust to Ld(ISM)]
    double tbg1__;        // T_W^BC [eq. temp. warm dust in birth clouds]
    double tbg2__;        // T_C^ISM [eq. temp. cold dust in ISM]
    double xi1__;         // xi_PAH^BC Ld(PAH)/Ld(BC)
    double xi2__;         // xi_MIR^BC Ld(MIR)/Ld(BC)
    double xi3__;         // xi_W^BC Ld(warm)/Ld(BC)
    double mdust__;       // dust mass
};
} //namespace magphys

#endif
