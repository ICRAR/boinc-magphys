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
			redshift__ { redshift } {
	}
	~ModelData();

	bool loadFilters(const string& filename);
	bool loadObservations(const string& filename);
	bool loadModelInfrared(const string& filename);
	bool loadModelOptical(const string& filename);
	void convertToLnu(double distance, ObservationLine& observationLine);

	inline vector<Filter>* filters() {
		return filters__;
	}
	inline vector<ObservationLine>* observationLines() {
		return observationLines__;
	}
	inline int nfilt_sfh() const {
		return nfilt_sfh__;
	}
	inline int nfilt_ir() const {
		return nfilt_ir__;
	}
	inline int nfilt_mix() const {
		return nfilt_mix__;
	}
	inline int n_sfh() const {
		return n_sfh__;
	}
	inline int n_ir() const {
		return n_ir__;
	}
	inline ModelInfrared* modelInfrared(int model_number) {
		return &modelInfrared__[model_number];
	}
	inline ModelOptical* modelOptical(int model_number) {
		return &modelOptical__[model_number];
	}
	inline double* fluxInfrared(int model_number) {
		return &flux_ir__[model_number * nfilt_ir__];
	}
	inline double* fluxOptical(int model_number) {
		return &flux_sfh__[model_number * nfilt_sfh__];
	}
	inline double redshift() const {
		return redshift__;
	}

private:
	vector<Filter>* filters__ = nullptr;
	vector<ObservationLine>* observationLines__ = nullptr;

	const double redshift__;
	int nfilt_sfh__ = 0;
	int nfilt_ir__ = 0;
	int nfilt_mix__ = 0;
	int n_sfh__ = 0;
	int n_ir__ = 0;
	double* flux_ir__ = nullptr;
	ModelInfrared* modelInfrared__ = nullptr;
	double* flux_sfh__ = nullptr;
	ModelOptical* modelOptical__ = nullptr;
}; // Class ModelData
} // namespace magphys

#endif
