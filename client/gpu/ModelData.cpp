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
#include "Parser.hpp"
#include "ModelData.hpp"


namespace magphys {
    ModelData::ModelData() {
        filters_ = NULL;

        flux_ir_ = NULL;
        modelInfrared_ = NULL;
        flux_sfh_ = NULL;
        modelOptical_ = NULL;

    }

ModelData::~ModelData() {
    cout << "term ModelData" << endl;
    // Clean up
    // if (filters_ != NULL) //Vectors handle memory themselves.
    // if (observations_ != NULL) 
    if (flux_ir_ != NULL) {
        cout << " delete flux_ir_" << endl;
        delete[] flux_ir_;
    }
    if (modelInfrared_ != NULL) {
        cout << " delete modelInfrared_" << endl;
        delete[] modelInfrared_;
    }
    if (flux_sfh_ != NULL) {
        cout << " delete flux_sfh_" << endl;
        delete[] flux_sfh_;
    }
    if (modelOptical_ != NULL) {
        cout << " delete modelOptical_" << endl;
        delete[] modelOptical_;
    }

}

void ModelData::initialise(double redshift) {
    redshift_ = redshift;
}

/*
 * Load the filters
 */
bool ModelData::loadFilters(const string& filename) {

    Parser filterParser(filename);
    filterParser.Ignore("#", "\n");
    bool result = true;

    cout << "Reading Filters..." << endl;

    filters_ = new vector<Filter>;
    vector<Filter>& filters = *filters_;

    vector<string> elements;
    while (filterParser.Good())
    {
        filterParser.Next();

        filterParser.GetTokens(elements);
        if(elements.size() > 0 ) {
            if (elements.size() != 4) {
                cerr << "Incorrect number of entries on the line. Expected: 4 Actual: " << elements.size() << endl;
                result = false;
            } else {
                Filter filter;
                filter.filterName = elements[0];
                filter.lambdaEff = atof(elements[1].c_str());
                filter.filterId = atoi(elements[2].c_str());
                filter.filterEnabled = atoi(elements[3].c_str());
                filters.push_back(filter);
            }
        }
    }

    // Now we have the filters
    //BIG assumption that Filters are Sorted by Pure Stellar, Mixed, Pure Dust.
    // ---------------------------------------------------------------------------
    // What part of the SED are the filters sampling at the redshift of the galaxy?
    //  - lambda(rest-frame) < 2.5 mic : emission purely stellar (attenuated by dust)
    //  - 2.5 mic < lambda(rest-frame) < 10 mic : stellar + dust emission
    //  - lambda(rest-frame) > 10 mic : emission purely from dust
    // ---------------------------------------------------------------------------
    nfilt_pureStellar_ = 0;
    nfilt_mixed_ = 0;
    nfilt_pureDust_ = 0;

    for (size_t i = 0; i < filters.size(); i++) {
        double lambda_rest = filters[i].lambdaEff / (1.0f + redshift_);
        if (lambda_rest <= 2.5f) {
            nfilt_pureStellar_++;
        } else if (lambda_rest > 2.5f && lambda_rest <= 10.0f) {
            nfilt_mixed_++;
        } else if (lambda_rest > 10.0f) {
            nfilt_pureDust_++;
        }

    }

    nfilt_stellarMixed_ = nfilt_pureStellar_ + nfilt_mixed_;
    nfilt_pureDust_start_ = nfilt_pureStellar_ + nfilt_mixed_;

    nfilt_mixed_start_ = nfilt_pureStellar_;
    nfilt_dustMixed_ = nfilt_mixed_ + nfilt_pureDust_;

    cout << "   " << endl;
    cout << "At this redshift: " << endl;

    for (int k = 0; k < nfilt_pureStellar_; k++) {
        cout << "purely stellar... " << filters[k].filterName << endl;
    }

    for (int k = nfilt_mixed_start_; k < nfilt_mixed_start_ + nfilt_mixed_ ; k++) {
        cout << "mix stars+dust... " << filters[k].filterName << endl;
    }
    for (size_t k = nfilt_pureDust_start_; k < nfilt_pureDust_start_ + nfilt_pureDust_; k++) {
        cout << "purely dust... " << filters[k].filterName << endl;
    }
    
    cout << "  Done." << endl;
    return result;
}

/*
 * Load the infrared model
 */
bool ModelData::loadModelInfrared(const string& filename) {
    Parser irParser(filename);
    irParser.Ignore("#", "\n");

    // Allocate the space
    if (nfilt_dustMixed_ > 0) {
        flux_ir_ = new double[NMOD * nfilt_dustMixed_];
    }
    modelInfrared_ = new ModelInfrared[NMOD];

    cout << "Reading IR dust emission library..." << endl;
    bool result = true;

    n_ir_ = 0;
    vector<string> elements;
    while (irParser.Good())
    {
        irParser.Next();
        irParser.GetTokens(elements);
        if (elements.size() > 0) {
            ModelInfrared& model = modelInfrared_[n_ir_];
            model.fmu_ir = atof(elements[0].c_str());     // fmu parameter Ld(ISM)/Ld(tot) - infrared
            model.fmu_ism = atof(elements[1].c_str());    // xi_C^ISM [cont. cold dust to Ld(ISM)]
            model.tbg1 = atof(elements[2].c_str());       // T_W^BC [eq. temp. warm dust in birth clouds]
            model.tbg2 = atof(elements[3].c_str());       // T_C^ISM [eq. temp. cold dust in ISM]
            model.xi1 = atof(elements[4].c_str());        // xi_PAH^BC Ld(PAH)/Ld(BC)
            model.xi2 = atof(elements[5].c_str());        // xi_MIR^BC Ld(MIR)/Ld(BC)
            model.xi3 = atof(elements[6].c_str());        // xi_W^BC Ld(warm)/Ld(BC)
            model.mdust = atof(elements[7].c_str());      // dust mass
            model.logmdust = log10( model.mdust );        // log10 dust mass

            // Only if we have the data
            if (nfilt_dustMixed_ > 0) {
                double flux[nfilt_dustMixed_];
                for (int j = 0; j < nfilt_dustMixed_; j++) {
                    flux[j] = atof(elements[8 + j].c_str());
                }

                int index = n_ir_ * nfilt_dustMixed_;
                for (int j = 0; j < nfilt_dustMixed_; j++) {
                    flux[j] = 3.117336e+6f * pow(10, -0.4f * (flux[j] + 48.6f));
                    // ary[i][j] is then rewritten as
                    // ary[i*sizeY+j]
                    flux_ir_[index + j] = flux[j] / (1 + redshift_);
                }
            }

            model.xi1 = model.xi1 * (1 - model.fmu_ir) + 0.550f * (1 - model.fmu_ism) * model.fmu_ir;
            model.xi2 = model.xi2 * (1 - model.fmu_ir) + 0.275f * (1 - model.fmu_ism) * model.fmu_ir;
            model.xi3 = model.xi3 * (1 - model.fmu_ir) + 0.175f * (1 - model.fmu_ism) * model.fmu_ir;
            model.fmu_ism = model.fmu_ism * model.fmu_ir;

            n_ir_++;
        }
    }
    cout << "  Done." << endl;
    return result;
}


/*
 * Load the optical model
 */
bool ModelData::loadModelOptical(const string& filename) {
    Parser sfhParser(filename);
    sfhParser.Ignore("#", "\n");

    // Allocate the space
    if (nfilt_stellarMixed_ > 0) {
        flux_sfh_ = new double[NMOD * nfilt_stellarMixed_];
    }
    modelOptical_ = new ModelOptical[NMOD];

    cout << "Reading SFH library..." << endl;
    bool result = true;
    n_sfh_ = 0;
    int i_line = 0;
    vector<string> elements;
    while (sfhParser.Good()) {
        sfhParser.Next();
        i_line++;

        if (i_line > 1){ //Skip One Line to Match Fortran Bug.
            sfhParser.GetTokens(elements);
            if (elements.size() > 0) {

                ModelOptical& model = modelOptical_[n_sfh_];
                model.fmu_sfh = atof(elements[21].c_str());               // fmu parameter Ld(ISM)/Ld(tot) - optical
                model.mstr1 = atof(elements[5].c_str());                  // stellar mass
                model.ldust = atof(elements[20].c_str()) / model.mstr1;   // total luminosity of dust (normalize to Mstar)
                model.logldust = log10(model.ldust);                      // log(Ldust)
                model.mu = atof(elements[4].c_str());                     // mu parameter (CF00 model)
                model.tauv = atof(elements[3].c_str());                   // optical V-band depth tauV (CF00 model)
                model.ssfr = atof(elements[9].c_str());                   // recent SSFR_0.01Gyr / stellar mass

                model.tvism = model.mu * model.tauv;                      // mu*tauV=V-band optical depth for ISM
                model.lssfr = log10(model.ssfr);                          // log(SSFR_0.01Gyr)

                // Only if we have the data
                if ( nfilt_stellarMixed_ > 0) {
                    double flux[ nfilt_stellarMixed_ ];
                    for (int j = 0; j < nfilt_stellarMixed_; j++) {
                        flux[j] = atof(elements[25 + j].c_str());
                    }

                    int index = n_sfh_ * nfilt_stellarMixed_;
                    for (int j = 0; j < nfilt_stellarMixed_; j++) {
                        flux[j] = 3.117336e+6f * pow(10, -0.4f * (flux[j] + 48.6f));
                        flux[j] = flux[j] / model.mstr1;
                        // ary[i][j] is then rewritten as
                        // ary[i*sizeY+j]
                        flux_sfh_[index + j] = flux[j] / (1 + redshift_);

                    }
                }

                n_sfh_++;
            }
        }
    }
    cout << "  Done." << endl;
    return result;
}
}