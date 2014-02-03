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


namespace magphys {

    struct Filter {
        string filterName;
        double lambdaEff;
        int filterId;
        int fit;
    };

    struct Observation {
        double flux_obs;
        double sigma;
        double w = 0;
    };

    struct ObservationLine {
        string galaxyName;
        double redshift;
        vector<Observation> observations;
    };

    struct ModelOptical {
        double fmu_sfh;     // fmu parameter Ld(ISM)/Ld(tot) - optical
        double mstr1;       // stellar mass
        double ldust;       // total luminosity of dust (normalize to Mstar)
        double logldust;    // log(ldust)
        double mu;          // mu parameter (CF00 model)
        double tauv;        // optical V-band depth tauV (CF00 model)
        double ssfr;        // recent SSFR_0.01Gyr / stellar mass
        double lssfr;       // log(SSFR_0.01Gyr)
        double tvsim;       // mu*tauV=V-band optical depth for ISM
    };

    struct ModelInfrared {
        double fmu_ir;      // fmu parameter Ld(ISM)/Ld(tot) - infrared
        double fmu_ism;     // xi_C^ISM [cont. cold dust to Ld(ISM)]
        double tbg1;        // T_W^BC [eq. temp. warm dust in birth clouds]
        double tbg2;        // T_C^ISM [eq. temp. cold dust in ISM]
        double xi1;         // xi_PAH^BC Ld(PAH)/Ld(BC)
        double xi2;         // xi_MIR^BC Ld(MIR)/Ld(BC)
        double xi3;         // xi_W^BC Ld(warm)/Ld(BC)
        double mdust;       // dust mass
    };
} //namespace magphys

#endif
