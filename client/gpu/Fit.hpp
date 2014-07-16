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

#include "Constants.hpp"
#include "Observation.hpp"
#include "HistogramRange.hpp"
#include "ModelData.hpp"

#ifndef FIT_HPP
#define FIT_HPP

namespace magphys {

class Fit {
public:
    Fit();
    ~Fit();

    void initialise(double redshift);
    void fit(ModelData* modelData);

    double calculateDistance(double redshift);
    inline double dist() const {
        return dist_;
    }

    void initializeOptical(ModelOptical* modelOptical, int n_sfh);
    void initializeInfrared(ModelInfrared* modelInfrared, int n_ir);

    bool loadObservations(const string& filename, 
        vector<Filter>* filters, int pureStellar, int mixed, int pureDust);
private:
    void initialiseHistogramRanges();
    double calculateDistLumiosityScale(double a, double b, double s, double npts);
    double invertedCubeOmegaMatter(double x);

    static double const cosmoHubbleConstant_ = 70.0f;
    static double const cosmoOmega_ = 0.30f;
    static double const cosmoOmegaLamba_ = 0.70f;
    double cosmoDecelerationParameter_ ; //Calculated in Initalize from cosmo* constants
    double cosmoOmegaMatter_ ;           //Calculated in Initalize from cosmo* constants
    double redshift_;
    double dist_ ;

    vector<Observation>* observations_ ;

    ModelOpticalBinIndex* modelOpticalBinIndex_ ;
    ModelInfraredBinIndex* modelInfraredBinIndex_ ;

    HistogramRange* histSFH_fmu_high_ ;     //psfh
    HistogramRange* histSFH_mu_high_ ;      //pmu
    HistogramRange* histSFH_tv_high_ ;      //ptv tauv (dust optical depth)
    HistogramRange* histSFH_tvism_high_ ;   //ptvism tauv Inter stellar matter
    HistogramRange* histSFH_lssfr_high_ ;   //plssfr
    
    HistogramRange* histIR_fmu_high_ ;      //pir
    HistogramRange* histIR_bgBc_high_ ;     //ptbg1 T_BGs (BC)
    HistogramRange* histIR_bgIsm_high_ ;    //ptbg2 T_BGs (ISM)
    HistogramRange* histIR_ism_high_ ;      //pism  fmu_ism 
    HistogramRange* histIR_xiPah_high_ ;    //pxi1 xi's PAHs
    HistogramRange* histIR_xiMir_high_ ;    //pxi2 xi's VSGs
    HistogramRange* histIR_xiW_high_ ;      //pxi3 xi's BGs
    
    HistogramRange* hist_mstars_high_ ;     //pa
    HistogramRange* hist_sfr_high_ ;        //psfr
    HistogramRange* hist_ldust_high_ ;      //pldust
    HistogramRange* hist_mdust_high_ ;      //pmd

    HistogramRange* histSFH_fmu_low_ ;     //psfh
    HistogramRange* histSFH_mu_low_ ;      //pmu
    HistogramRange* histSFH_tv_low_ ;      //ptv tauv (dust optical depth)
    HistogramRange* histSFH_tvism_low_ ;   //ptvism tauv Inter stellar matter
    HistogramRange* histSFH_lssfr_low_ ;   //plssfr
    
    HistogramRange* histIR_fmu_low_ ;      //pir
    HistogramRange* histIR_bgBc_low_ ;     //ptbg1 T_BGs (BC)
    HistogramRange* histIR_bgIsm_low_ ;    //ptbg2 T_BGs (ISM)
    HistogramRange* histIR_ism_low_ ;      //pism  fmu_ism 
    HistogramRange* histIR_xiPah_low_ ;    //pxi1 xi's PAHs
    HistogramRange* histIR_xiMir_low_ ;    //pxi2 xi's VSGs
    HistogramRange* histIR_xiW_low_ ;      //pxi3 xi's BGs
    
    HistogramRange* hist_mstars_low_ ;     //pa
    HistogramRange* hist_sfr_low_ ;        //psfr
    HistogramRange* hist_ldust_low_ ;      //pldust
    HistogramRange* hist_mdust_low_ ;      //pmd

};

}

#endif
