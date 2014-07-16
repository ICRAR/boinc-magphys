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


#ifndef MODEL_DATA_HPP
#define MODEL_DATA_HPP

namespace magphys {

class ModelData {
public:
	ModelData();
	~ModelData();
    void initialise(double redshift);


	bool loadFilters(const string& filename);
	bool loadObservations(const string& filename);
	bool loadModelInfrared(const string& filename);
	bool loadModelOptical(const string& filename);
	//void convertToLnu(double distance, ObservationLine& observationLine);

	inline vector<Filter>* filters() {
		return filters_;
	}
	inline int nfilt_pureStellar() const {
		return nfilt_pureStellar_;
	}
	inline int nfilt_pureDust() const {
		return nfilt_pureDust_;
	}
	inline int nfilt_pureDust_start() const {
		return nfilt_pureDust_start_;
	}
	inline int nfilt_mixed() const {
		return nfilt_mixed_;
	}
	inline int nfilt_mixed_start() const {
		return nfilt_mixed_start_;
	}
	inline int nfilt_stellarMixed() const {
		return nfilt_stellarMixed_;
	}
	inline int nfilt_dustMixed() const {
		return nfilt_dustMixed_;
	}

	inline int n_sfh() const {
		return n_sfh_;
	}
	inline int n_ir() const {
		return n_ir_;
	}
	inline ModelInfrared* modelInfrared(int model_number) {
		return &modelInfrared_[model_number];
	}
	inline ModelOptical* modelOptical(int model_number) {
		return &modelOptical_[model_number];
	}

	inline double* fluxInfrared(int model_number) {
    	return &flux_ir_[model_number * nfilt_dustMixed_];
	}
	inline double* fluxOptical(int model_number) {
		return &flux_sfh_[model_number * nfilt_stellarMixed_];
	}

	inline double redshift() const {
		return redshift_;
	}


private:
	vector<Filter>* filters_ ;

	double redshift_;
	int n_sfh_ ;
	int n_ir_ ;

	int nfilt_pureStellar_ ;

	int nfilt_mixed_start_;
    int nfilt_mixed_;

    int nfilt_pureDust_start_;
    int nfilt_pureDust_;

	int nfilt_stellarMixed_ ;
	int nfilt_dustMixed_ ;

	double* flux_ir_ ;
	ModelInfrared* modelInfrared_ ;
	
	double* flux_sfh_ ;
	ModelOptical* modelOptical_ ;


}; // Class ModelData
} // namespace magphys

#endif
