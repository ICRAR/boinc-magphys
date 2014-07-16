

#include <iostream>
using std::cerr;
using std::cout;
using std::endl;

#include <cmath>
#include <fstream>
#include "Parser.hpp"
#include "Observation.hpp"

namespace magphys {

Observation::Observation() {
    observationFiltersPureStellar_ = NULL;
    observationFiltersMixed_ = NULL;
    observationFiltersPureDust_ = NULL;
    numberFluxes_ = 0;

    hist_infrared_binContent_ = NULL;
    hist_optical_binContent_ = NULL;

    hist_mstars_high_binContent_ = NULL;
    hist_sfr_high_binContent_ = NULL;
    hist_ldust_high_binContent_ = NULL;
    hist_mdust_high_binContent_ = NULL;

    histSFH_fmu_high_binContent_ = NULL;
    histSFH_mu_high_binContent_ = NULL;
    histSFH_tv_high_binContent_ = NULL;
    histSFH_tvism_high_binContent_ = NULL;
    histSFH_lssfr_high_binContent_ = NULL;

    histIR_fmu_high_binContent_ = NULL;
    histIR_bgBc_high_binContent_ = NULL;
    histIR_bgIsm_high_binContent_ = NULL;
    histIR_ism_high_binContent_ = NULL;
    histIR_xiPah_high_binContent_ = NULL;
    histIR_xiMir_high_binContent_ = NULL;
    histIR_xiW_high_binContent_ = NULL;

    modelOptical_scaleTotal_ = NULL;
    modelOptical_scaleDensity_ = NULL;

}

Observation::~Observation() {
    // Clean up
    //cout << "term Observation " << galaxyName_ << endl;
    if (modelOptical_scaleTotal_ != NULL) delete[] modelOptical_scaleTotal_;
    if (modelOptical_scaleDensity_ != NULL) delete[] modelOptical_scaleDensity_;

    if (hist_infrared_binContent_ != NULL) delete[] hist_infrared_binContent_;
    if (hist_optical_binContent_ != NULL) delete[] hist_optical_binContent_;

    if (hist_mstars_high_binContent_ != NULL) delete[] hist_mstars_high_binContent_;
    if (hist_sfr_high_binContent_ != NULL) delete[] hist_sfr_high_binContent_;
    if (hist_ldust_high_binContent_ != NULL) delete[] hist_ldust_high_binContent_;
    if (hist_mdust_high_binContent_ != NULL) delete[] hist_mdust_high_binContent_;

    if (histSFH_fmu_high_binContent_ != NULL) delete[] histSFH_fmu_high_binContent_;
    if (histSFH_mu_high_binContent_ != NULL) delete[] histSFH_mu_high_binContent_;
    if (histSFH_tv_high_binContent_ != NULL) delete[] histSFH_tv_high_binContent_;
    if (histSFH_tvism_high_binContent_ != NULL) delete[] histSFH_tvism_high_binContent_;
    if (histSFH_lssfr_high_binContent_ != NULL) delete[] histSFH_lssfr_high_binContent_;

    if (histIR_fmu_high_binContent_ != NULL) delete[] histIR_fmu_high_binContent_;
    if (histIR_bgBc_high_binContent_ != NULL) delete[] histIR_bgBc_high_binContent_;
    if (histIR_bgIsm_high_binContent_ != NULL) delete[] histIR_bgIsm_high_binContent_;
    if (histIR_ism_high_binContent_ != NULL) delete[] histIR_ism_high_binContent_;
    if (histIR_xiPah_high_binContent_ != NULL) delete[] histIR_xiPah_high_binContent_;
    if (histIR_xiMir_high_binContent_ != NULL) delete[] histIR_xiMir_high_binContent_;
    if (histIR_xiW_high_binContent_ != NULL) delete[] histIR_xiW_high_binContent_;

}

void Observation::convertToLnu(double distance) {
    // ---------------------------------------------------------------------------
    // COMPARISON BETWEEN MODELS AND OBSERVATIONS:
    //
    // Compare everything in the sample units:
    // Lnu (i.e. luminosity per unit frequency) in Lsun/Hz
    //
    // Model fluxes: already converted from AB mags to Lnu in Lsun/Hz
    // Fluxes and physical parameters from optical library per unit Mstar=1 Msun
    // Fluxes and physical parameters from infrared library per unit Ldust=1 Lsun
    //
    // Observed fluxes & uncertainties
    // Convert from Fnu in Jy to Lnu in Lo/Hz [using luminosity distance dist
    // ---------------------------------------------------------------------------
    if(numberFluxes_ >= 4) {
        vector<ObservationFilter>& observationFiltersPureStellar = *observationFiltersPureStellar_;
        for (size_t i = 0; i < observationFiltersPureStellar.size(); i++) {
            if (observationFiltersPureStellar[i].flux_obs > 0) {
                observationFiltersPureStellar[i].flux_obs = observationFiltersPureStellar[i].flux_obs * 1.0e-23f * 3.283608731e-33f * pow(distance, 2);
                observationFiltersPureStellar[i].sigma = observationFiltersPureStellar[i].sigma * 1.0e-23f * 3.283608731e-33f * pow(distance, 2);
            }
            if (observationFiltersPureStellar[i].sigma < 0.05f * observationFiltersPureStellar[i].flux_obs) {
                observationFiltersPureStellar[i].sigma = 0.05f * observationFiltersPureStellar[i].flux_obs;
            }
        }
        for (size_t i = 0; i < observationFiltersPureStellar.size(); i++) {
            if (observationFiltersPureStellar[i].sigma > 0.0f) {
                observationFiltersPureStellar[i].w = 1.0f / (pow(observationFiltersPureStellar[i].sigma, 2));
            }
        }

        vector<ObservationFilter>& observationFiltersMixed= *observationFiltersMixed_;
        for (size_t i = 0; i < observationFiltersMixed.size(); i++) {
            if (observationFiltersMixed[i].flux_obs > 0) {
                observationFiltersMixed[i].flux_obs = observationFiltersMixed[i].flux_obs * 1.0e-23f * 3.283608731e-33f * pow(distance, 2);
                observationFiltersMixed[i].sigma = observationFiltersMixed[i].sigma * 1.0e-23f * 3.283608731e-33f * pow(distance, 2);
            }
            if (observationFiltersMixed[i].sigma < 0.05f * observationFiltersMixed[i].flux_obs) {
                observationFiltersMixed[i].sigma = 0.05f * observationFiltersMixed[i].flux_obs;
            }
        }
        for (size_t i = 0; i < observationFiltersMixed.size(); i++) {
            if (observationFiltersMixed[i].sigma > 0.0f) {
                observationFiltersMixed[i].w = 1.0f / (pow(observationFiltersMixed[i].sigma, 2));
            }
        }

        vector<ObservationFilter>& observationFiltersPureDust = *observationFiltersPureDust_;
        for (size_t i = 0; i < observationFiltersPureDust.size(); i++) {
            if (observationFiltersPureDust[i].flux_obs > 0) {
                observationFiltersPureDust[i].flux_obs = observationFiltersPureDust[i].flux_obs * 1.0e-23f * 3.283608731e-33f * pow(distance, 2);
                observationFiltersPureDust[i].sigma = observationFiltersPureDust[i].sigma * 1.0e-23f * 3.283608731e-33f * pow(distance, 2);
            }
            if (observationFiltersPureDust[i].sigma < 0.05f * observationFiltersPureDust[i].flux_obs) {
                observationFiltersPureDust[i].sigma = 0.05f * observationFiltersPureDust[i].flux_obs;
            }
        }
        for (size_t i = 0; i < observationFiltersPureDust.size(); i++) {
            if (observationFiltersPureDust[i].sigma > 0.0f) {
                observationFiltersPureDust[i].w = 1.0f / (pow(observationFiltersPureDust[i].sigma, 2));
            }
        }

    }
}

void Observation::initializeOptical(ModelOptical* modelOptical, int n_sfh, 
    double* fluxOptical, int nfilt_stellarMixed, int n_nfilt_pureStellar ) {
    //Here I need an build array based on optical size.
    // Allocate the space
    modelOptical_scaleTotal_ = new double[NMOD];
    modelOptical_scaleDensity_ = new double[NMOD];
    hist_optical_binContent_ = new double[NMOD];

    for (int idx_sfh = 0; idx_sfh < n_sfh; idx_sfh++){
        hist_optical_binContent_[idx_sfh] = 0.0;
        modelOptical_scaleTotal_[idx_sfh] = 0.0;
        modelOptical_scaleDensity_[idx_sfh] = 0.0;
        double* fluxOpticalModel = &fluxOptical[idx_sfh * nfilt_stellarMixed ];
        vector<ObservationFilter>& observationFilters = *observationFiltersPureStellar_;
        for (int k = 0; k < n_nfilt_pureStellar; k++){
            if ( observationFilters[k].flux_obs > 0 ) {
                modelOptical_scaleTotal_[idx_sfh] += fluxOpticalModel[k] * observationFilters[k].flux_obs * observationFilters[k].w ; 
                modelOptical_scaleDensity_[idx_sfh] += (fluxOpticalModel[k] * fluxOpticalModel[k]) * observationFilters[k].w ; 
            }
        }
    }

}

void Observation::initializeInfrared(ModelInfrared* modelInfrared, int n_ir) {
    //Here I need an build array based on optical size.
    // Allocate the space
    hist_infrared_binContent_ = new double[NMOD];

    for (int idx_ir = 0; idx_ir < n_ir; idx_ir++){
        hist_infrared_binContent_[idx_ir] = 0.0;
    }
}

void Observation::initializeHistogram() {

    hist_mstars_high_binContent_ = new double[NHISTOGRAMBINHIGH];
    hist_sfr_high_binContent_ = new double[NHISTOGRAMBINHIGH];
    hist_ldust_high_binContent_ = new double[NHISTOGRAMBINHIGH];
    hist_mdust_high_binContent_ = new double[NHISTOGRAMBINHIGH];

    histSFH_fmu_high_binContent_ = new double[NHISTOGRAMBINHIGH];
    histSFH_mu_high_binContent_ = new double[NHISTOGRAMBINHIGH];
    histSFH_tv_high_binContent_ = new double[NHISTOGRAMBINHIGH];
    histSFH_tvism_high_binContent_ = new double[NHISTOGRAMBINHIGH];
    histSFH_lssfr_high_binContent_ = new double[NHISTOGRAMBINHIGH];

    histIR_fmu_high_binContent_ = new double[NHISTOGRAMBINHIGH];
    histIR_bgBc_high_binContent_ = new double[NHISTOGRAMBINHIGH];
    histIR_bgIsm_high_binContent_ = new double[NHISTOGRAMBINHIGH];
    histIR_ism_high_binContent_ = new double[NHISTOGRAMBINHIGH];
    histIR_xiPah_high_binContent_ = new double[NHISTOGRAMBINHIGH];
    histIR_xiMir_high_binContent_ = new double[NHISTOGRAMBINHIGH];
    histIR_xiW_high_binContent_ = new double[NHISTOGRAMBINHIGH];
}

void Observation::expandOpticalHistogram(ModelOpticalBinIndex* modelOpticalBinIndex, int n_sfh) {
    for (int idx_sfh = 0; idx_sfh < n_sfh; idx_sfh++){
        histSFH_fmu_high_binContent_[ modelOpticalBinIndex[idx_sfh].histSFH_fmu_high_binIndex ] += hist_optical_binContent_[idx_sfh];
        histSFH_mu_high_binContent_[ modelOpticalBinIndex[idx_sfh].histSFH_mu_high_binIndex ] += hist_optical_binContent_[idx_sfh];
        histSFH_tv_high_binContent_[ modelOpticalBinIndex[idx_sfh].histSFH_tv_high_binIndex ] += hist_optical_binContent_[idx_sfh];
        histSFH_tvism_high_binContent_[ modelOpticalBinIndex[idx_sfh].histSFH_tvism_high_binIndex ] += hist_optical_binContent_[idx_sfh];
        histSFH_lssfr_high_binContent_[ modelOpticalBinIndex[idx_sfh].histSFH_lssfr_high_binIndex ] += hist_optical_binContent_[idx_sfh];

        hist_optical_binContent_[idx_sfh] = 0.0;
    }
}

void Observation::expandInfraredHistogram(ModelInfraredBinIndex* modelInfraredIndex, int n_ir) {
    for (int idx_ir = 0; idx_ir < n_ir; idx_ir++){
        histIR_fmu_high_binContent_[ modelInfraredIndex[idx_ir].histIR_fmu_high_binIndex ] += hist_infrared_binContent_[idx_ir];
        histIR_bgBc_high_binContent_[ modelInfraredIndex[idx_ir].histIR_bgBc_high_binIndex ]  += hist_infrared_binContent_[idx_ir];
        histIR_bgIsm_high_binContent_[ modelInfraredIndex[idx_ir].histIR_bgIsm_high_binIndex ]  += hist_infrared_binContent_[idx_ir];
        histIR_ism_high_binContent_[ modelInfraredIndex[idx_ir].histIR_ism_high_binIndex ]  += hist_infrared_binContent_[idx_ir];
        histIR_xiPah_high_binContent_[ modelInfraredIndex[idx_ir].histIR_xiPah_high_binIndex ]  += hist_infrared_binContent_[idx_ir];
        histIR_xiMir_high_binContent_[ modelInfraredIndex[idx_ir].histIR_xiMir_high_binIndex ]  += hist_infrared_binContent_[idx_ir];
        histIR_xiW_high_binContent_[ modelInfraredIndex[idx_ir].histIR_xiW_high_binIndex ]  += hist_infrared_binContent_[idx_ir];

        hist_infrared_binContent_[idx_ir] = 0.0;
    }
}

void Observation::finalizeHistogram() {
    //Convert binContent from total to Percentages.
    for (int idx_hires = 0; idx_hires < NHISTOGRAMBINHIGH; idx_hires++){
        hist_mstars_high_binContent_[idx_hires] = hist_mstars_high_binContent_[idx_hires] / ptot_;
        hist_sfr_high_binContent_[idx_hires] = hist_sfr_high_binContent_[idx_hires] / ptot_;
        hist_ldust_high_binContent_[idx_hires] = hist_ldust_high_binContent_[idx_hires] / ptot_;
        hist_mdust_high_binContent_[idx_hires] = hist_mdust_high_binContent_[idx_hires] / ptot_;

        histSFH_fmu_high_binContent_[idx_hires] = histSFH_fmu_high_binContent_[idx_hires] / ptot_;
        histSFH_mu_high_binContent_[idx_hires] = histSFH_mu_high_binContent_[idx_hires] / ptot_;
        histSFH_tv_high_binContent_[idx_hires] = histSFH_tv_high_binContent_[idx_hires] / ptot_;
        histSFH_tvism_high_binContent_[idx_hires] = histSFH_tvism_high_binContent_[idx_hires] / ptot_;
        histSFH_lssfr_high_binContent_[idx_hires] = histSFH_lssfr_high_binContent_[idx_hires] / ptot_;

        histIR_fmu_high_binContent_[idx_hires] = histIR_fmu_high_binContent_[idx_hires] / ptot_;
        histIR_bgBc_high_binContent_[idx_hires] = histIR_bgBc_high_binContent_[idx_hires] / ptot_;
        histIR_bgIsm_high_binContent_[idx_hires] = histIR_bgIsm_high_binContent_[idx_hires] / ptot_;
        histIR_ism_high_binContent_[idx_hires] = histIR_ism_high_binContent_[idx_hires] / ptot_;
        histIR_xiPah_high_binContent_[idx_hires] = histIR_xiPah_high_binContent_[idx_hires] / ptot_;
        histIR_xiMir_high_binContent_[idx_hires] = histIR_xiMir_high_binContent_[idx_hires] / ptot_;
        histIR_xiW_high_binContent_[idx_hires] = histIR_xiW_high_binContent_[idx_hires] / ptot_;
    }

    //Get Percentiles For Each.
    get_percentiles(hist_mstars_high_binContent_, percIdx_mstars_);
    get_percentiles(hist_sfr_high_binContent_, percIdx_sfr_);
    get_percentiles(hist_ldust_high_binContent_, percIdx_ldust_);
    get_percentiles(hist_mdust_high_binContent_, percIdx_mdust_);

    get_percentiles(histSFH_fmu_high_binContent_, percIdxSFH_fmu_);
    get_percentiles(histSFH_mu_high_binContent_, percIdxSFH_mu_);
    get_percentiles(histSFH_tv_high_binContent_, percIdxSFH_tv_);
    get_percentiles(histSFH_tvism_high_binContent_, percIdxSFH_tvism_);
    get_percentiles(histSFH_lssfr_high_binContent_, percIdxSFH_lssfr_);

    get_percentiles(histIR_fmu_high_binContent_, percIdxIR_fmu_);
    get_percentiles(histIR_bgBc_high_binContent_, percIdxIR_bgBc_);
    get_percentiles(histIR_bgIsm_high_binContent_, percIdxIR_bgIsm_);
    get_percentiles(histIR_ism_high_binContent_, percIdxIR_ism_);
    get_percentiles(histIR_xiPah_high_binContent_, percIdxIR_xiPah_);
    get_percentiles(histIR_xiMir_high_binContent_, percIdxIR_xiMir_);
    get_percentiles(histIR_xiW_high_binContent_, percIdxIR_xiW_);
}

// ---------------------------------------------------------------------------
// Calculates percentiles of the probability distibution
// for a given parameter: 2.5, 16, 50 (median), 84, 97.5
// 1. Sort the parameter + the probability array
// 2. Find the parameter value M for which:
//    P (x < M) = P (x > M) = percentiles
// ---------------------------------------------------------------------------
// probability : vector with prob of each parameter value (or bin)
//  percentile : vector containing 5 percentiles described above
void Observation::get_percentiles(double probability[], int percIdx[]){
    double limit[5] = { 0.025f, 0.16f, 0.50f, 0.84f, 0.975f };

    for (int limitIdx = 0; limitIdx<5; limitIdx++){
        double sumProbability = 0.0;
        int probIdx = 0;
        while (sumProbability <= limit[limitIdx]){
            sumProbability += probability[ probIdx ];
            probIdx++;
        }
        probIdx--;
        percIdx[limitIdx] = probIdx;
    }
}

// ---------------------------------------------------------------------------
// Degrades the resolution of the histograms containing the likelihood
// distribution of the parameters: to facilitate storage & visualization
// ---------------------------------------------------------------------------
// void Observation::degrade_hist(HistogramRange* hist_low, HistogramRange* hist_high, double prob_high[], double prob_low[]){
//     for (int highIdx = 0; highIdx < hist_high.binCount(); highIdx++){
//         prob_low[ hist_low.binIndexPosition( hist_high.binValue(highIdx) ) ] += prob_high[ highIdx ];
//     }
// }


// //Find the bin with the highest probability value
// double get_hpbv(double hist1[], double hist2[], int nbin){
//     double max_pr = 0;
//     double hpbv = 0;
//     for (int ibin = 0; ibin<nbin; ibin++){
//         if (ibin == 0){
//             max_pr = hist1[ibin];
//             hpbv = hist2[ibin];
//         }
//         else if (hist1[ibin] > max_pr){
//             max_pr = hist1[ibin];
//             hpbv = hist2[ibin];
//         }
//     }
//     return hpbv;
// }

} // namespace magphys
