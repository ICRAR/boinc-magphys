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
	ModelData(double redshift) :
			redshift_ { redshift } {

	}
	~ModelData();

	bool loadFilters(const string& filename);
	bool loadObservations(const string& filename);
	bool loadModelInfrared(const string& filename);
	bool loadModelOptical(const string& filename);
	void convertToLnu(double distance, ObservationLine& observationLine);

	inline vector<Filter>* filters() {
		return &filters_;
	}
	inline vector<ObservationLine>* observationLines() {
		return &observations_;
	}
	inline int nfilt_sfh() const {
		return nfilt_sfh_;
	}
	inline int nfilt_ir() const {
		return nfilt_ir_;
	}
	inline int nfilt_mix() const {
		return nfilt_mix_;
	}
	inline ModelInfrared* modelInfrared(int model_number) {
		return &modelInfrared_[model_number];
	}
	inline ModelOptical* modelOptical(int model_number) {
		return &modelOptical_[model_number];
	}
	inline double* fluxInfrared(int model_number) {
		return &flux_ir_[model_number * nfilt_ir_];
	}
	inline double* fluxOptical(int model_number) {
		return &flux_sfh_[model_number * nfilt_sfh_];
	}
	inline double redshift() const {
		return redshift_;
	}

private:
	vector<Filter> filters_;
	vector<ObservationLine> observations_;

	const double redshift_;
	int nfilt_sfh_ = 0;
	int nfilt_ir_ = 0;
	int nfilt_mix_ = 0;
	double* flux_ir_ = nullptr;
	ModelInfrared* modelInfrared_ = nullptr;
	double* flux_sfh_ = nullptr;
	ModelOptical* modelOptical_ = nullptr;
}; // Class ModelData
} // namespace magphys

#endif
