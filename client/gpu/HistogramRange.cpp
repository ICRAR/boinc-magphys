

#include <iostream>
using std::cerr;
using std::cout;
using std::endl;

#include <cmath>
#include <fstream>
#include "Parser.hpp"
#include "HistogramRange.hpp"

namespace magphys {

HistogramRange::HistogramRange() {
    binValue_ = NULL;
    // binContent_ = NULL;
}

HistogramRange::~HistogramRange() {
    // Clean up
    //cout << "term Histogram" << endl;
    if (binValue_ != NULL) {
        delete[] binValue_;
    }
    // if (binContent_ != NULL) {
    //     delete[] binContent_;
    // }
}

// Build histogram Range grid
HistogramRange::HistogramRange(string histogramName, int maxBins, double minValue, double maxValue, double stepValue) {
    double lowValue, highValue;

    histogramName_ = histogramName;
    binCount_ = 0;
    minValue_ = minValue;
    maxValue_ = maxValue;
    valueRange_ = maxValue - minValue;

    binValue_ = new double[maxBins];
    //binContent_ = new double[maxBins]; //Only need this by Observation

    lowValue = minValue;
    highValue = lowValue + stepValue;
    while (highValue <= maxValue ) {
        binValue_[ binCount_ ] = 0.5f*(lowValue + highValue);
        //binContent_[ binCount_ ] = 0.0;
        lowValue = lowValue + stepValue;
        highValue = lowValue + stepValue;
        binCount_++;
    }

}




}// namespace magphys
