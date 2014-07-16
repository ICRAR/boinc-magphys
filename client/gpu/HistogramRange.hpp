
#include <string>
using std::string;
#include <vector>
using std::vector;
#include <cmath>
using std::min;
using std::max;

#include "Constants.hpp"

#ifndef HISTOGRAMRANGE_HPP
#define HISTOGRAMRANGE_HPP

namespace magphys {

class HistogramRange {
public:
	HistogramRange();
	HistogramRange(string histogramName, int maxBins, double minValue, double maxValue, double stepValue) ;
	~HistogramRange();

	inline double minValue() const {
		return minValue_;
	}
	inline double maxValue() const {
		return maxValue_;
	}
	inline double valueRange() const {
		return valueRange_;
	}
	inline double binCount() const {
		return binCount_;
	}
	inline double stepValue() const {
		return stepValue_;
	}

	inline int binIndexPosition(double checkValue) {
		double binIndexPosition = ( (checkValue - minValue_ ) / valueRange_ ) * binCount_;
		return max(0, min((int)(binIndexPosition), binCount_ - 1));
	}

private:
	string histogramName_;
	int binCount_;
	double minValue_;
	double maxValue_;
	double valueRange_;
	double stepValue_;
	double* binValue_ ;
	// double* binContent_ ; //Only need this by Observation

}; // Class Histogram

} // namespace magphys

#endif
