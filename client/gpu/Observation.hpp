
#include <string>
using std::string;
#include <vector>
using std::vector;

#include "Constants.hpp"

#ifndef OBSERVATION_HPP
#define OBSERVATION_HPP

namespace magphys {

struct ObservationFilter {
	double flux_obs;
	double sigma ;
	double w ;
};


class Observation {
public:
	Observation();
	~Observation();

	void convertToLnu(double distance);

	void initializeOptical(ModelOptical* modelOptical, int n_sfh, 
		double* fluxOptical, int nfilt_stellarMixed_, int n_nfilt_pureStellar_);
	void initializeInfrared(ModelInfrared* modelInfrared, int n_ir);
	void initializeHistogram();
	void expandOpticalHistogram(ModelOpticalBinIndex* modelOpticalBinIndex, int n_sfh);
	void expandInfraredHistogram(ModelInfraredBinIndex* modelInfraredIndex, int n_ir);
	void finalizeHistogram();

	inline double redshift() const {
		return redshift_;
	}
	inline vector<ObservationFilter>* observationFiltersPureStellar() {
		return observationFiltersPureStellar_ ;
	}
	inline vector<ObservationFilter>* observationFiltersMixed() {
		return observationFiltersMixed_ ;
	}
	inline vector<ObservationFilter>* observationFiltersPureDust() {
		return observationFiltersPureDust_ ;
	}
	inline int numberFluxes() const {
		return numberFluxes_;
	}
	inline double modelOptical_scaleTotal(int model_number) {
    	return modelOptical_scaleTotal_[model_number];
	}
	inline double modelOptical_scaleDensity(int model_number) {
    	return modelOptical_scaleDensity_[model_number];
	}

	string galaxyName_;
	double redshift_;
	int numberFluxes_;	
	double ptot_;
	vector<ObservationFilter>* observationFiltersPureStellar_ ;
	vector<ObservationFilter>* observationFiltersMixed_ ;
	vector<ObservationFilter>* observationFiltersPureDust_ ;

	//Some Temp variables stored during fit.
	double prob_;
	double logldustscale_;
	double scale_;

	//Histogram values calculated during fit.
	double* hist_infrared_binContent_ ;
	double* hist_optical_binContent_ ;

	double* hist_mstars_high_binContent_ ;
	double* hist_sfr_high_binContent_ ;
	double* hist_ldust_high_binContent_ ;
	double* hist_mdust_high_binContent_ ;

private:
	void get_percentiles(double probability[], int percIdx[]);

	//Histogram values Expanded.
    double* histSFH_fmu_high_binContent_;
    double* histSFH_mu_high_binContent_;
    double* histSFH_tv_high_binContent_;
    double* histSFH_tvism_high_binContent_;
    double* histSFH_lssfr_high_binContent_;

    double* histIR_fmu_high_binContent_;
    double* histIR_bgBc_high_binContent_;
    double* histIR_bgIsm_high_binContent_;
    double* histIR_ism_high_binContent_;
    double* histIR_xiPah_high_binContent_;
    double* histIR_xiMir_high_binContent_;
    double* histIR_xiW_high_binContent_;

	double* modelOptical_scaleTotal_;
	double* modelOptical_scaleDensity_;

	int percIdx_mstars_[5], percIdx_sfr_[5], percIdx_ldust_[5], percIdx_mdust_[5];
    int percIdxSFH_fmu_[5], percIdxSFH_mu_[5], percIdxSFH_tv_[5], percIdxSFH_tvism_[5], percIdxSFH_lssfr_[5];
    int percIdxIR_fmu_[5], percIdxIR_bgBc_[5], percIdxIR_bgIsm_[5], percIdxIR_ism_[5];
    int percIdxIR_xiPah_[5], percIdxIR_xiMir_[5], percIdxIR_xiW_[5];

}; // Class Observation
} // namespace magphys

#endif
