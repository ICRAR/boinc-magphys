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

#include <iostream>
using std::cerr;
using std::cout;
using std::endl;

#include <cmath>
#include <fstream>
#include "Fit.hpp"
#include "Parser.hpp"

namespace magphys {
    Fit::Fit() {
        // Setup cosmological variables.
        if (cosmoOmegaLamba_ == 0){
            cosmoDecelerationParameter_ = cosmoOmega_ / 2;
        } else {
            cosmoDecelerationParameter_ = (3 * cosmoOmega_ / 2) - 1;
        }

        cosmoOmegaMatter_ = (2 * (cosmoDecelerationParameter_ + 1)) / 3;

        redshift_ = 0;
        observations_ = NULL;

        histSFH_fmu_high_ = NULL;
        histSFH_mu_high_ = NULL;
        histSFH_tv_high_ = NULL;
        histSFH_tvism_high_ = NULL;
        histSFH_lssfr_high_ = NULL;
        histIR_fmu_high_ = NULL;
        histIR_bgBc_high_ = NULL;
        histIR_bgIsm_high_ = NULL;
        histIR_ism_high_ = NULL;
        histIR_xiPah_high_ = NULL;
        histIR_xiMir_high_ = NULL;
        histIR_xiW_high_ = NULL;
        hist_mstars_high_ = NULL;
        hist_sfr_high_ = NULL;
        hist_ldust_high_ = NULL;
        hist_mdust_high_ = NULL;

        histSFH_fmu_low_ = NULL;
        histSFH_mu_low_ = NULL;
        histSFH_tv_low_ = NULL;
        histSFH_tvism_low_ = NULL;
        histSFH_lssfr_low_ = NULL;
        histIR_fmu_low_ = NULL;
        histIR_bgBc_low_ = NULL;
        histIR_bgIsm_low_ = NULL;
        histIR_ism_low_ = NULL;
        histIR_xiPah_low_ = NULL;
        histIR_xiMir_low_ = NULL;
        histIR_xiW_low_ = NULL;
        hist_mstars_low_ = NULL;
        hist_sfr_low_ = NULL;
        hist_ldust_low_ = NULL;
        hist_mdust_low_ = NULL;

        modelOpticalBinIndex_ = NULL;
        modelInfraredBinIndex_ = NULL;

    }

    Fit::~Fit() {
        // Clean up
        cout << "term fit" << endl;
        if (histSFH_fmu_high_ != NULL) delete [] histSFH_fmu_high_;
        if (histSFH_mu_high_ != NULL) delete [] histSFH_mu_high_;
        if (histSFH_tv_high_ != NULL) delete [] histSFH_tv_high_;
        if (histSFH_tvism_high_ != NULL) delete [] histSFH_tvism_high_;
        if (histSFH_lssfr_high_ != NULL) delete [] histSFH_lssfr_high_;

        if (histIR_fmu_high_ != NULL) delete [] histIR_fmu_high_;
        if (histIR_bgBc_high_ != NULL) delete [] histIR_bgBc_high_;
        if (histIR_bgIsm_high_ != NULL) delete [] histIR_bgIsm_high_;
        if (histIR_ism_high_ != NULL) delete [] histIR_ism_high_;
        if (histIR_xiPah_high_ != NULL) delete [] histIR_xiPah_high_;
        if (histIR_xiMir_high_ != NULL) delete [] histIR_xiMir_high_;
        if (histIR_xiW_high_ != NULL) delete [] histIR_xiW_high_;

        if (hist_mstars_high_ != NULL) delete [] hist_mstars_high_;
        if (hist_sfr_high_ != NULL) delete [] hist_sfr_high_;
        if (hist_ldust_high_ != NULL) delete [] hist_ldust_high_;
        if (hist_mdust_high_ != NULL) delete [] hist_mdust_high_;

        if (histSFH_fmu_low_ != NULL) delete [] histSFH_fmu_low_;
        if (histSFH_mu_low_ != NULL) delete [] histSFH_mu_low_;
        if (histSFH_tv_low_ != NULL) delete [] histSFH_tv_low_;
        if (histSFH_tvism_low_ != NULL) delete [] histSFH_tvism_low_;
        if (histSFH_lssfr_low_ != NULL) delete [] histSFH_lssfr_low_;

        if (histIR_fmu_low_ != NULL) delete [] histIR_fmu_low_;
        if (histIR_bgBc_low_ != NULL) delete [] histIR_bgBc_low_;
        if (histIR_bgIsm_low_ != NULL) delete [] histIR_bgIsm_low_;
        if (histIR_ism_low_ != NULL) delete [] histIR_ism_low_;
        if (histIR_xiPah_low_ != NULL) delete [] histIR_xiPah_low_;
        if (histIR_xiMir_low_ != NULL) delete [] histIR_xiMir_low_;
        if (histIR_xiW_low_ != NULL) delete [] histIR_xiW_low_;

        if (hist_mstars_low_ != NULL) delete [] hist_mstars_low_;
        if (hist_sfr_low_ != NULL) delete [] hist_sfr_low_;
        if (hist_ldust_low_ != NULL) delete [] hist_ldust_low_;
        if (hist_mdust_low_ != NULL) delete [] hist_mdust_low_;

        if (modelOpticalBinIndex_ != NULL) delete [] modelOpticalBinIndex_;
        if (modelInfraredBinIndex_ != NULL) delete [] modelInfraredBinIndex_;
    }

    void Fit::initialise(double redshift) {
        redshift_ = redshift;
        dist_ = calculateDistance(redshift_);
        initialiseHistogramRanges();
    }



    // ---------------------------------------------------------------------------
    // Computes luminosity distance corresponding to a redshift z.
    // Uses Mattig formulae for qo both 0 and non 0
    // Revised January 1991 to implement cosmolgical constant
    // Ho in km/sec/Mpc, DL is in Mpc
    double Fit::calculateDistance(double redshift) {
        double distLumiosity= 0;
        double s = 0;

        if(redshift <= 0) {
            distLumiosity = 1.0e-5f;
        }

        if(cosmoDecelerationParameter_ == 0) { //Taylor Expansion
            distLumiosity = ((3.0e5f * redshift) * (1 + (redshift / 2))) / cosmoHubbleConstant_;
        }
        else if(cosmoDecelerationParameter_ > 0) { //Terrel Formula
            double d1 = (cosmoHubbleConstant_ * redshift) + ((cosmoDecelerationParameter_ - 1) * (sqrt(1 + ((2 * cosmoDecelerationParameter_) * redshift)) - 1));
            double d2 = ((cosmoHubbleConstant_ * cosmoDecelerationParameter_) * cosmoDecelerationParameter_) / 3.0e5f;
            distLumiosity = d1 / d2;
        }
        else if(cosmoDecelerationParameter_ < 0) { 
            double aa = 1;
            double bb = 1 + redshift;
            bool success = false;
            double s0 = 1.0e-10f;
            int npts = 0;
            do {
                npts++;
                s = calculateDistLumiosityScale(aa, bb, s, npts);
                double epsr = fabs(s - s0) / s0;
                if(epsr < 1.0e-4f) {
                    success = true;
                } else {
                    s0 = s;
                }
            } while(!success);
            double dd1 = s;
            double dd2 = (3.0e5f * (1 + redshift)) / (cosmoHubbleConstant_ * sqrt(cosmoOmegaMatter_));
            distLumiosity = dd1 * dd2;
        }

        return ( distLumiosity * (3.086e+24f) / sqrt(1 + redshift) );
    }

    double Fit::calculateDistLumiosityScale(double a, double b, double s, double npts) {
        //cout << "calculateDistLumiosityScale " << a << " " << b << " " << s << " " << npts << endl;
        double result;
        if(npts == 1) {
            result = (b - a) * invertedCubeOmegaMatter(0.5 * (a + b));
        } else {
            int it = pow(3, (npts - 2));
            double tnm = it;
            double del = (b - a) / (3 * tnm);
            double ddel = del + del;
            double x = a + 0.5 * del;
            double sum = 0;
            for(int j = 0; j < it; j++) {
                sum = sum + invertedCubeOmegaMatter(x);
                x = x + ddel;
                sum = sum + invertedCubeOmegaMatter(x) ;
                x = x + del;
            }
            result = (s + (b - a) * sum / tnm) / 3;
        }
        return result;
    }

    //part of calculateDistLumiosityScale in Mattig formula when decelartion is not zero.
    double Fit::invertedCubeOmegaMatter(double x) {
        double omegainv = 1 / cosmoOmegaMatter_;
        return (1 / sqrt(((x * x * x) + omegainv) - 1));
    }

    void Fit::initialiseHistogramRanges() {
        // ---------------------------------------------------------------------------
        // Compute histogram grids of the parameter likelihood distributions.
        // ---------------------------------------------------------------------------

        histSFH_fmu_high_ = new HistogramRange("f_mu (SFH)",NHISTOGRAMBINHIGH, 0.0f, 1.0005f, 0.001f);      //psfh
        histSFH_mu_high_ = new HistogramRange("mu parameter",NHISTOGRAMBINHIGH, 0.0f, 1.0005f, 0.001f);     //pmu
        histSFH_tv_high_ = new HistogramRange("tau_V",NHISTOGRAMBINHIGH, 0.0f, 6.0025f, 0.005f);            //ptv tauv (dust optical depth)
        histSFH_tvism_high_ = new HistogramRange("tau_V^ISM",NHISTOGRAMBINHIGH, 0.0f, 6.0025f, 0.005f);     //ptvism tauv Inter stellar matter
        histSFH_lssfr_high_ = new HistogramRange("sSFR_0.1Gyr",NHISTOGRAMBINHIGH, -13.0f, -5.9975f, 0.05f); //plssfr

        histIR_fmu_high_ = new HistogramRange("f_mu (IR)",NHISTOGRAMBINHIGH, 0.0f, 1.0005f, 0.001f);        //pir
        histIR_bgBc_high_ = new HistogramRange("T_W^BC",NHISTOGRAMBINHIGH, 30.0f, 60.0125f, 0.025f);        //ptbg1 T_BGs (BC)
        histIR_bgIsm_high_ = new HistogramRange("T_C^ISM",NHISTOGRAMBINHIGH, 15.0f, 25.0125f, 0.025f);      //ptbg2 T_BGs (ISM)
        histIR_ism_high_ = new HistogramRange("xi_C^tot",NHISTOGRAMBINHIGH, 0.0f, 1.0005f, 0.001f);         //pism  fmu_ism 
        histIR_xiPah_high_ = new HistogramRange("xi_PAH^tot",NHISTOGRAMBINHIGH, 0.0f, 1.0001f, 0.001f);     //pxi1 xi's PAHs
        histIR_xiMir_high_ = new HistogramRange("xi_MIR^tot",NHISTOGRAMBINHIGH, 0.0f, 1.0001f, 0.001f);     //pxi2 xi's VSGs
        histIR_xiW_high_ = new HistogramRange("xi_W^tot",NHISTOGRAMBINHIGH, 0.0f, 1.0001f, 0.001f);         //pxi3 xi's BGs

        hist_mstars_high_ = new HistogramRange("M(stars)",NHISTOGRAMBINHIGH, 2.0f, 13.0025f, 0.005f);       //pa
        hist_sfr_high_ = new HistogramRange("SFR_0.1Gyr",NHISTOGRAMBINHIGH, -8.0f, 3.5005f, 0.005f);        //psfr
        hist_ldust_high_ = new HistogramRange("Ldust",NHISTOGRAMBINHIGH, 2.0f, 13.0025f, 0.005f);           //pldust
        hist_mdust_high_ = new HistogramRange("M(dust)",NHISTOGRAMBINHIGH, -2.0f, 9.0f, 0.005f);            //pmd


        histSFH_fmu_low_ = new HistogramRange("f_mu (SFH)",NHISTOGRAMBINLOW, 0.0f, 1.025f, 0.05f);           //psfh
        histSFH_mu_low_ = new HistogramRange("mu parameter",NHISTOGRAMBINLOW, 0.0f, 1.025f, 0.05f);          //pmu
        histSFH_tv_low_ = new HistogramRange("tau_V",NHISTOGRAMBINLOW, 0.0f, 6.0f, 0.075f);                  //ptv tauv (dust optical depth)
        histSFH_tvism_low_ = new HistogramRange("tau_V^ISM",NHISTOGRAMBINLOW, 0.0f, 6.0375f, 0.075f);        //ptvism tauv Inter stellar matter
        histSFH_lssfr_low_ = new HistogramRange("sSFR_0.1Gyr",NHISTOGRAMBINLOW, -13.0f, -6.05f, 0.10f);      //plssfr

        histIR_fmu_low_ = new HistogramRange("f_mu (IR)",NHISTOGRAMBINLOW, 0.0f, 1.025f, 0.05f);             //pir
        histIR_bgBc_low_ = new HistogramRange("T_W^BC",NHISTOGRAMBINLOW, 30.0f, 60.5f, 1.0f);                //ptbg1 T_BGs (BC)
        histIR_bgIsm_low_ = new HistogramRange("T_C^ISM",NHISTOGRAMBINLOW, 15.0f, 25.5f, 1.0f);              //ptbg2 T_BGs (ISM)
        histIR_ism_low_ = new HistogramRange("xi_C^tot",NHISTOGRAMBINLOW, 0.0f, 1.025f, 0.05f);              //pism  fmu_ism 
        histIR_xiPah_low_ = new HistogramRange("xi_PAH^tot",NHISTOGRAMBINLOW, 0.0f, 1.025f, 0.05f);          //pxi1 xi's PAHs
        histIR_xiMir_low_ = new HistogramRange("xi_MIR^tot",NHISTOGRAMBINLOW, 0.0f, 1.025f, 0.05f);          //pxi2 xi's VSGs
        histIR_xiW_low_ = new HistogramRange("xi_W^tot",NHISTOGRAMBINLOW, 0.0f, 1.025f, 0.05f);              //pxi3 xi's BGs

        hist_mstars_low_ = new HistogramRange("M(stars)",NHISTOGRAMBINLOW, 2.0f, 13.05f, 0.10f);             //pa
        hist_sfr_low_ = new HistogramRange("SFR_0.1Gyr",NHISTOGRAMBINLOW, -8.0f, 3.05f, 0.10f);              //psfr
        hist_ldust_low_ = new HistogramRange("Ldust",NHISTOGRAMBINLOW, 2.0f, 13.05f, 0.10f);                 //pldust
        hist_mdust_low_ = new HistogramRange("M(dust)",NHISTOGRAMBINLOW, -2.0f, 9.05f, 0.10f);               //pmd
    }



void Fit::initializeOptical(ModelOptical* modelOptical, int n_sfh) {
    //Here I need an build array based on optical size.
    // Allocate the space, Initialize Optical Bin Indexes.
    modelOpticalBinIndex_ = new ModelOpticalBinIndex[NMOD];

    for (int idx_sfh = 0; idx_sfh < n_sfh; idx_sfh++){
        ModelOpticalBinIndex& model = modelOpticalBinIndex_[idx_sfh];
        model.histSFH_fmu_high_binIndex = histSFH_fmu_high_->binIndexPosition( modelOptical[idx_sfh].fmu_sfh );
        model.histSFH_mu_high_binIndex = histSFH_mu_high_->binIndexPosition( modelOptical[idx_sfh].mu );
        model.histSFH_tv_high_binIndex = histSFH_tv_high_->binIndexPosition( modelOptical[idx_sfh].tauv );
        model.histSFH_tvism_high_binIndex = histSFH_tvism_high_->binIndexPosition( modelOptical[idx_sfh].tvism );
        model.histSFH_lssfr_high_binIndex = histSFH_lssfr_high_->binIndexPosition( modelOptical[idx_sfh].lssfr );

        //Fix Mininum of Optical Model.
        if (modelOptical[idx_sfh].lssfr < histSFH_lssfr_high_->minValue() ) {
            modelOptical[idx_sfh].lssfr = histSFH_lssfr_high_->minValue();
        }
    }

}

void Fit::initializeInfrared(ModelInfrared* modelInfrared, int n_ir) {
    //Here I need an build array based on infrared size.
    // Allocate the space, Initialize Infrared Bin Indexes.
    modelInfraredBinIndex_ = new ModelInfraredBinIndex[NMOD];

    for (int idx_ir = 0; idx_ir < n_ir; idx_ir++){
        ModelInfraredBinIndex& model = modelInfraredBinIndex_[idx_ir];
        model.histIR_fmu_high_binIndex = histIR_fmu_high_->binIndexPosition( modelInfrared[idx_ir].fmu_ir );
        model.histIR_bgBc_high_binIndex = histIR_bgBc_high_->binIndexPosition( modelInfrared[idx_ir].tbg1 );
        model.histIR_bgIsm_high_binIndex = histIR_bgIsm_high_->binIndexPosition( modelInfrared[idx_ir].tbg2 );
        model.histIR_ism_high_binIndex = histIR_ism_high_->binIndexPosition( modelInfrared[idx_ir].fmu_ism );
        model.histIR_xiPah_high_binIndex = histIR_xiPah_high_->binIndexPosition( modelInfrared[idx_ir].xi1 );
        model.histIR_xiMir_high_binIndex = histIR_xiMir_high_->binIndexPosition( modelInfrared[idx_ir].xi2 );
        model.histIR_xiW_high_binIndex = histIR_xiW_high_->binIndexPosition( modelInfrared[idx_ir].xi3 );
    }

}    

/*
 * Load the observations
 */
bool Fit::loadObservations(const string& filename, 
    vector<Filter>* pfilters, int pureStellar, int mixed, int pureDust) {

    Parser obsParser(filename);
    obsParser.Ignore("#", "\n");

    cout << "Reading Observations to process..." << endl;

    observations_ = new vector<Observation>;
    vector<Observation>& observations = *observations_;
    vector<Filter>& filters = *pfilters;

    bool result = true;

    vector<string> elements;
    while (obsParser.Good())
    {
        obsParser.Next();

        obsParser.GetTokens(elements);
        if(elements.size() > 0 ) {
            // We expect 2 entries per filter + the name and redshift

            //Parser Returns an extra blank element at the moment because of trailing spaces in observation file.
            // if (elements.size() != (filters.size() * 2) + 2) {

            //     cerr << "Incorrect number of entries on the line. Expected: " << (filters.size() * 2) + 2 << " Actual: " << elements.size() << endl;
            //      result = false;
            //      for (size_t i = 0; i < elements.size(); i++) {
            //          cout << "Element " << i << " value " << elements[i] << endl;
            //      }
            // }

            Observation observation;
            observation.galaxyName_ = elements[0];
            observation.redshift_ = atof(elements[1].c_str());
            observation.numberFluxes_ = 0;

            observation.observationFiltersPureStellar_ = new vector<ObservationFilter>;
            vector<ObservationFilter>& observationFiltersPureStellar = *observation.observationFiltersPureStellar_;

            for (int filterIdx = 0; filterIdx < pureStellar; filterIdx++) {
                ObservationFilter observationFilter;
                int index = (filterIdx * 2) + 2;

                if (filters[filterIdx].filterEnabled == 0) {
                    observationFilter.flux_obs = -99;
                    observationFilter.sigma = -99;
                } else {
                    observationFilter.flux_obs = atof(elements[index].c_str());
                    observationFilter.sigma = atof(elements[index + 1].c_str());
                }
                if (observationFilter.flux_obs > 0 ) observation.numberFluxes_++;
                observationFiltersPureStellar.push_back(observationFilter);
            }

            observation.observationFiltersMixed_ = new vector<ObservationFilter>;
            vector<ObservationFilter>& observationFiltersMixed = *observation.observationFiltersMixed_;
            
            for (int filterIdx = pureStellar; filterIdx < pureStellar + mixed; filterIdx++) {
                ObservationFilter observationFilter;
                int index = (filterIdx * 2) + 2;

                if (filters[filterIdx].filterEnabled == 0) {
                    observationFilter.flux_obs = -99;
                    observationFilter.sigma = -99;
                } else {
                    observationFilter.flux_obs = atof(elements[index].c_str());
                    observationFilter.sigma = atof(elements[index + 1].c_str());
                }
                if (observationFilter.flux_obs > 0 ) observation.numberFluxes_++;
                observationFiltersMixed.push_back(observationFilter);
            }

            observation.observationFiltersPureDust_ = new vector<ObservationFilter>;
            vector<ObservationFilter>& observationFiltersPureDust = *observation.observationFiltersPureDust_;
            
            for (int filterIdx = pureStellar + mixed; filterIdx < pureStellar + mixed + pureDust; filterIdx++) {
                ObservationFilter observationFilter;
                int index = (filterIdx * 2) + 2;

                if (filters[filterIdx].filterEnabled == 0) {
                    observationFilter.flux_obs = -99;
                    observationFilter.sigma = -99;
                } else {
                    observationFilter.flux_obs = atof(elements[index].c_str());
                    observationFilter.sigma = atof(elements[index + 1].c_str());
                }
                if (observationFilter.flux_obs > 0 ) observation.numberFluxes_++;
                observationFiltersPureDust.push_back(observationFilter);
            }

            if ( observation.numberFluxes_ >= 4 ) {
                observations.push_back(observation);    //Creating Copy of Observation in vector (observation runs ::~Observation)
            } else {
                std::cout << "Skipping Observation " << observation.galaxyName_ << " number fluxes = " << observation.numberFluxes_ << std::endl;
            }
        }
    }
    cout << "  Done." << endl;
    return result;
}

bool isObservationFluxLow(Observation observation) {
   static int k = 1;

   if(observation.numberFluxes() < 4 )
       return true;
   else 
       return false; 
 }

void Fit::fit(ModelData* modelData) {
    cout << "Initializing Fit..." << endl;
//process nbrOfObservationToProcess observations at a time? instead of all.

//Hmm, if we removed disabled filters then we wouldn't have to check flux_obs > 0 all the time?
    //Nope, But we could create flux arrays more specific to each observation and then get rid of flux_obs > 0

    // For each observation
    vector<Observation>& observations = *observations_;

    for(size_t i = 0; i < observations.size(); i++) {
        Observation& observation = observations[i];
        // Correct the fluxes for this observation
        observation.convertToLnu( dist_ );

        //Calc Optical values that dont change per observation
        observation.initializeOptical( modelData->modelOptical(0), modelData->n_sfh(), 
            modelData->fluxOptical(0), modelData->nfilt_stellarMixed(), modelData->nfilt_pureStellar() );

        //Calc Infrared values that dont change per observation
        observation.initializeInfrared( modelData->modelInfrared(0), modelData->n_ir() );

        //Initialize Histogram for observation
        observation.initializeHistogram();
    }

    cout << "Starting Fit..." << endl;
    int writePercentage = 25;

    //Calc Grid
    double prob = 0;
    for(int i_sfh = 0; i_sfh < modelData->n_sfh(); i_sfh++) {
        magphys::ModelOptical* modelOptical = modelData->modelOptical( i_sfh );
        double* fluxOpticalModel = modelData->fluxOptical( i_sfh );
        int n_irbysfh=0;

        for(int i_ir = 0; i_ir < modelData->n_ir(); i_ir++) {
            magphys::ModelInfrared* modelInfrared = modelData->modelInfrared( i_ir );
            if(fabs(modelOptical->fmu_sfh - modelInfrared->fmu_ir) <= 1.5f) {

                if ( (modelData->nfilt_dustMixed()==0 && n_irbysfh == 1)||(modelData->nfilt_dustMixed()!=0)) {
                    double* fluxInfraredModel = modelData->fluxInfrared( i_ir );

                    for(size_t i = 0; i < observations.size(); i++) {
                        Observation& observation = observations[i];

                        double scaleTotal = observation.modelOptical_scaleTotal( i_sfh );
                        double scaleDensity = observation.modelOptical_scaleDensity( i_sfh );
                        vector<magphys::ObservationFilter>& observationFiltersMixed= *observation.observationFiltersMixed();
                        if ( modelData->nfilt_dustMixed() > 0 ) {
                            for(int k = 0; k < modelData->nfilt_dustMixed(); k++) {
                                if ( observationFiltersMixed[k].flux_obs > 0 ) {
                                    double flux_mod = fluxOpticalModel[k + modelData->nfilt_pureStellar() ] * fluxInfraredModel[k];
                                    scaleTotal += flux_mod * observationFiltersMixed[k].flux_obs * observationFiltersMixed[k].w;
                                    scaleDensity += (flux_mod * flux_mod) * observationFiltersMixed[k].w;
                                }
                            }                        
                        }

                        vector<magphys::ObservationFilter>& observationFiltersPureDust= *observation.observationFiltersPureDust();
                        if ( modelData->nfilt_pureDust() > 0 ) {
                            for(int k = 0; k < modelData->nfilt_pureDust(); k++) {
                                if ( observationFiltersPureDust[k].flux_obs > 0 ) {
                                    double flux_mod = modelOptical->ldust * fluxInfraredModel[k];
                                    scaleTotal += flux_mod * observationFiltersPureDust[k].flux_obs * observationFiltersPureDust[k].w;
                                    scaleDensity += (flux_mod * flux_mod) * observationFiltersPureDust[k].w;
                                }
                            }                        
                        }

                        double scale = scaleTotal / scaleDensity;
                        double chi2 = 0;
                        vector<magphys::ObservationFilter>& observationFiltersPureStellar= *observation.observationFiltersPureStellar();
                        for(int k = 0; k < modelData->nfilt_pureStellar(); k++) {
                            if ( observationFiltersPureStellar[k].flux_obs > 0 ) {
                                chi2 += (( observationFiltersPureStellar[k].flux_obs - (scale * fluxOpticalModel[k])) * 
                                    ( observationFiltersPureStellar[k].flux_obs - (scale * fluxOpticalModel[k])) ) * observationFiltersPureStellar[k].w;
                            }
                        }                        
                        if ( modelData->nfilt_dustMixed() > 0 ) {
                            for(int k = 0; k < modelData->nfilt_dustMixed(); k++) {
                                if ( observationFiltersMixed[k].flux_obs > 0 ) {
                                    double flux_mod = fluxOpticalModel[k + modelData->nfilt_pureStellar() ] * fluxInfraredModel[k];
                                    chi2 += (( observationFiltersMixed[k].flux_obs - (scale * flux_mod)) * 
                                             ( observationFiltersMixed[k].flux_obs - (scale * flux_mod)) ) * observationFiltersMixed[k].w;
                                }
                            }
                        }
                        if ( chi2 < 600.0f && modelData->nfilt_pureDust() > 0 ) {
                            vector<magphys::ObservationFilter>& observationFiltersPureDust= *observation.observationFiltersPureDust();
                            for(int k = 0; k < modelData->nfilt_pureDust(); k++) {
                                if ( observationFiltersPureDust[k].flux_obs > 0 ) {
                                    double flux_mod = fluxOpticalModel[k + modelData->nfilt_pureStellar() ] * fluxInfraredModel[k];
                                    chi2 += (( observationFiltersPureStellar[k].flux_obs - (scale * fluxInfraredModel[k + modelData->nfilt_dustMixed()])) * 
                                             ( observationFiltersPureStellar[k].flux_obs - (scale * fluxInfraredModel[k + modelData->nfilt_dustMixed()])) ) * observationFiltersPureStellar[k].w;
                                }
                            }
                        }                    
                        observation.prob_ = exp(-0.5 * chi2);

                        //Best CHI Check
                        scale = log10(scale);
                        observation.logldustscale_=modelOptical->logldust + log10(exp(scale*2.30258509299404568402)); //Part of MDust calc
                        observation.scale_ = scale;
                    } 
                }
                n_irbysfh++; 

                if ( modelData->nfilt_dustMixed()!=0 ){
                    for(size_t i = 0; i < observations.size(); i++) {
                        Observation& observation = observations[i];
                        observation.ptot_ += observation.prob_;
                        //SFH
                        observation.hist_optical_binContent_[i_sfh] += observation.prob_;
                        //MStar
                        observation.hist_mstars_high_binContent_[ hist_mstars_high_->binIndexPosition(observation.scale_) ] += observation.prob_;
                        //SFR
                        observation.hist_sfr_high_binContent_[ hist_sfr_high_->binIndexPosition(modelOptical->lssfr+observation.scale_) ] += observation.prob_;
                        //Ldust
                        observation.hist_ldust_high_binContent_[ hist_ldust_high_->binIndexPosition(modelOptical->logldust+observation.scale_) ] += observation.prob_;
                    }                        
                } //has dust

                //Calculate IR Specific Data
                for(size_t i = 0; i < observations.size(); i++) {
                    Observation& observation = observations[i];
                    //IR
                    observation.hist_infrared_binContent_[i_ir] += observation.prob_;
                    //Mdust
                    observation.hist_mdust_high_binContent_[ hist_mdust_high_->binIndexPosition( modelInfrared->logmdust + observation.logldustscale_ ) ] += observation.prob_;
                }  
     

            } // df Check.

        } //ir

        if ( modelData->nfilt_dustMixed()==0 ){
            for(size_t i = 0; i < observations.size(); i++) {
                Observation& observation = observations[i];
                double probMultipleAllIR = observation.prob_ * n_irbysfh;
                observation.ptot_ += probMultipleAllIR;
                //SFH
                observation.hist_optical_binContent_[i_sfh] += probMultipleAllIR;
                //MStar
                observation.hist_mstars_high_binContent_[ hist_mstars_high_->binIndexPosition(observation.scale_) ] += probMultipleAllIR;
                //SFR
                observation.hist_sfr_high_binContent_[ hist_sfr_high_->binIndexPosition(modelOptical->lssfr+observation.scale_) ] += probMultipleAllIR;
                //Ldust
                observation.hist_ldust_high_binContent_[ hist_ldust_high_->binIndexPosition(modelOptical->logldust+observation.scale_) ] += probMultipleAllIR;
            }
        }

        if ((i_sfh) * 100 / modelData->n_sfh() > writePercentage){
            std::cout << "\r " << writePercentage << "% done... " << (modelData->n_sfh() * writePercentage) / 100 << "/" << modelData->n_sfh() << " opt. models" << endl;
            writePercentage += 25;
        }

        //If we had to write a checkpoint, it would be better to expandOpticalHistogram and expandInfraredHistogram, 
        //and use those values since it would result in a smaller checkpoint file per observation.
        //16 Bins *2304=36864 doubles, 288kb, vs 2 Models 100032 + 4bins 9216 109248, 853kb

    } //sfh
    std::cout << "\r100% done... " << modelData->n_sfh() << "/" << modelData->n_sfh() << " opt. models" << endl;

    for(size_t i = 0; i < observations.size(); i++) {
        Observation& observation = observations[i];
        cout << observation.galaxyName_ << " Probability " << observation.ptot_ << endl;
    }

    //Expand Optical and Infrared to Histogram
    for(size_t i = 0; i < observations.size(); i++) {
        Observation& observation = observations[i];
        observation.expandOpticalHistogram(&modelOpticalBinIndex_[0], modelData->n_sfh());
        observation.expandInfraredHistogram(&modelInfraredBinIndex_[0], modelData->n_ir());
        observation.finalizeHistogram();
        //Degrade Histogram
        //Write Histogram
    }



//Loop nbrOfObservationToProcess?

} //Fit

} //namespace magphys
