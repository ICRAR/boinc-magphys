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

#define NMOD 50016
#define NHISTOGRAMBINHIGH 2304
#define NHISTOGRAMBINLOW 128

#define MIN_HPBV 0.00001f

/*
 * As this could is based one the MAGPHYS code I've tried to use the same variable names.
 * 
 */

// inline double pow2(double* x) 
// {
//     return (x * x);
// }


namespace magphys {

struct Filter {
    string filterName;
    double lambdaEff;
    int filterId;
    int filterEnabled;
};


struct ModelOptical {
    double fmu_sfh;     // fmu parameter Ld(ISM)/Ld(tot) - optical
    double mstr1;       // stellar mass
    double ldust;       // total luminosity of dust (normalize to Mstar)
    double logldust;    // log(ldust_)
    double mu;          // mu parameter (CF00 model)
    double tauv;        // optical V-band depth tauV (CF00 model)
    double ssfr;        // recent SSFR_0.01Gyr / stellar mass
    double lssfr;       // log(SSFR_0.01Gyr)
    double tvism;       // mu*tauV=V-band optical depth for ISM
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
    double logmdust;    // log(mass_)
};

struct ModelOpticalBinIndex {
    int histSFH_fmu_high_binIndex;
    int histSFH_mu_high_binIndex;
    int histSFH_tv_high_binIndex;
    int histSFH_tvism_high_binIndex;
    int histSFH_lssfr_high_binIndex;
};

struct ModelInfraredBinIndex {
    int histIR_fmu_high_binIndex;
    int histIR_bgBc_high_binIndex;
    int histIR_bgIsm_high_binIndex;
    int histIR_ism_high_binIndex;
    int histIR_xiPah_high_binIndex;
    int histIR_xiMir_high_binIndex;
    int histIR_xiW_high_binIndex;
};
    
} //namespace magphys

#endif
