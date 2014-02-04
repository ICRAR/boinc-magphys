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
#include <boost/algorithm/string.hpp>
#include "ModelData.hpp"

namespace magphys {

ModelData::~ModelData() {
    // Clean up
    if (filters__ != nullptr) {
        delete filters__;
    }
    if (observationLines__ != nullptr) {
        delete observationLines__;
    }
    if (flux_ir__ != nullptr) {
        delete[] flux_ir__;
    }
    if (modelInfrared__ != nullptr) {
        delete[] modelInfrared__;
    }
    if (flux_sfh__ != nullptr) {
        delete[] flux_sfh__;
    }
    if (modelOptical__ != nullptr) {
        delete[] modelOptical__;
    }
}

/*
 * Load the filters
 */
bool ModelData::loadFilters(const string& filename) {
    // {F77}       open(22,file=filters,status='old')
    // {F77}       do i=1,1
    // {F77}          read(22,*)
    // {F77}       enddo
    // {F77}       io=0
    // {F77}       ifilt=0
    // {F77}       do while(io.eq.0)
    // {F77}          ifilt=ifilt+1
    // {F77}          read(22,*,iostat=io) filt_name(ifilt),lambda_eff(ifilt),filt_id(ifilt),fit(ifilt)
    // {F77}       enddo
    // {F77}       nfilt=ifilt-1
    // {F77}       close(22)
    std::ifstream in_file;
    in_file.open(filename, std::ios_base::in);
    if (!in_file) {
        cerr << "Unable to open file " << filename << endl;
        return false;
    }

    filters__ = new vector<Filter>;
    vector<Filter>& filters = *filters__;
    bool result = true;
    string line;
    while (getline(in_file, line)) {
        boost::trim(line);
        if (line.length() > 0) {
            if (line[0] != '#') {
                vector<string> elements;
                boost::split(elements, line, boost::is_any_of(" \t"), boost::token_compress_on);
                if (elements.size() != 4) {
                    cerr << "Incorrect number of entries on the line. Expected: 4 Actual: " << elements.size() << endl << line << endl;
                    result = false;
                }

                Filter filter;
                filter.filterName__ = elements[0];
                filter.lambdaEff__ = atof(elements[1].c_str());
                filter.filterId__ = atoi(elements[2].c_str());
                filter.fit__ = atoi(elements[3].c_str());
                filters.push_back(filter);
            }
        }
    }
    in_file.close();

    // Now we have the filters
    // {F77} c     ---------------------------------------------------------------------------
    // {F77} c     What part of the SED are the filters sampling at the redshift of the galaxy?
    // {F77} c     - lambda(rest-frame) < 2.5 mic : emission purely stellar (attenuated by dust)
    // {F77} c     - 2.5 mic < lambda(rest-frame) < 10 mic : stellar + dust emission
    // {F77} c     - lambda(rest-frame) > 10 mic : emission purely from dust
    // {F77} c     ---------------------------------------------------------------------------
    nfilt_sfh__ = 0;
    nfilt_ir__ = 0;
    nfilt_mix__ = 0;

    for (size_t i = 0; i < filters.size(); i++) {
        double lambda_rest = filters[i].lambdaEff__ / (1.0 + redshift__);
        if (lambda_rest < 10) {
            nfilt_sfh__++;
        }
        if (lambda_rest > 2.5) {
            nfilt_ir__++;
        }
        if (lambda_rest > 2.5 && lambda_rest <= 10) {
            nfilt_mix__++;
        }
    }
    cout << "   " << endl;
    cout << "At this redshift: " << endl;
    // {F77}
    // {F77}          do k=1,nfilt_sfh-nfilt_mix
    // {F77}             write(*,*) 'purely stellar... ',filt_name(k)
    // {F77}          enddo
    // {F77}          do k=nfilt_sfh-nfilt_mix+1,nfilt_sfh
    // {F77}             write(*,*) 'mix stars+dust... ',filt_name(k)
    // {F77}          enddo
    // {F77}          do k=nfilt_sfh+1,nfilt
    // {F77}             write(*,*) 'purely dust... ',filt_name(k)
    // {F77}          enddo
    for (int k = 0; k < (nfilt_sfh__ - nfilt_mix__); k++) {
        cout << "purely stellar... " << filters[k].filterName__ << endl;
    }

    for (int k = nfilt_sfh__ - nfilt_mix__; k < nfilt_sfh__; k++) {
        cout << "mix stars+dust... " << filters[k].filterName__ << endl;
    }
    for (size_t k = nfilt_sfh__; k < filters.size(); k++) {
        cout << "purely dust... " << filters[k].filterName__ << endl;
    }

    return result;
}

/*
 * Load the observations
 */
bool ModelData::loadObservations(const string& filename) {
    std::ifstream in_file;
    in_file.open(filename, std::ios_base::in);
    if (!in_file) {
        cerr << "Unable to open file " << filename << endl;
        return false;
    }

    // {F77}       open(20,file=obs,status='old')
    // {F77}       do i=1,1
    // {F77}          read(20,*)
    // {F77}       enddo
    // {F77}       io=0
    // {F77}       n_obs=0
    // {F77}       do while(io.eq.0)
    // {F77}          n_obs=n_obs+1
    // {F77}          read(20,*,iostat=io) gal_name(n_obs),redshift(n_obs),
    // {F77}      +        (flux_obs(n_obs,k),sigma(n_obs,k),k=1,nfilt)
    // {F77}       enddo
    // {F77}       n_obs=n_obs-1
    observationLines__ = new vector<ObservationLine>;
    vector<ObservationLine>& observationLines = *observationLines__;
    vector<Filter>& filters = *filters__;
    bool result = true;
    string line;
    while (getline(in_file, line)) {
        boost::trim(line);
        if (line.length() > 0) {
            if (line[0] != '#') {
                vector<string> elements;
                boost::split(elements, line, boost::is_any_of(" \t"), boost::token_compress_on);

                // We expect 2 entries per filter + the name and redshift
                if (elements.size() != (filters.size() * 2) + 2) {
                    cerr << "Incorrect number of entries on the line. Expected: " << (filters.size() * 2) + 2 << " Actual: " << elements.size() << endl << line << endl;
                    result = false;
                }

                ObservationLine observationLine;
                observationLine.galaxyName__ = elements[0];
                observationLine.redshift__ = atof(elements[1].c_str());
                for (size_t i = 0; i < filters.size(); i++) {
                    Observation observation;
                    int index = (i * 2) + 2;

                    // Do we actually want to fit this observation
                    // {F77}          if (fit(ifilt).eq.0) then
                    // {F77}             flux_obs(i_gal,ifilt)=-99.
                    // {F77}             sigma(i_gal,ifilt)=-99.
                    // {F77}          endif
                    if (filters[i].fit__ == 0) {
                        observation.flux_obs__ = -99;
                        observation.sigma__ = -99;
                    }
                    else {
                        observation.flux_obs__ = atof(elements[index].c_str());
                        observation.sigma__ = atof(elements[index + 1].c_str());
                    }
                    observationLine.observations__.push_back(observation);
                }

                observationLines.push_back(observationLine);
            }
        }
    }

    in_file.close();
    return result;
}

/*
 * Load the infrared model
 */
bool ModelData::loadModelInfrared(const string& filename) {
    std::ifstream in_file;
    in_file.open(filename, std::ios_base::in);
    if (!in_file) {
        cerr << "Unable to open file " << filename << endl;
        return false;
    }

    // Allocate the space
    if (nfilt_ir__ > 0) {
        flux_ir__ = new double[NMOD * nfilt_ir__];
    }
    modelInfrared__ = new ModelInfrared[NMOD];

    cout << "Reading IR dust emission library..." << endl;
    bool result = true;
    string line;
    n_ir__ = 0;
    // {F77}             open(20,file=irlib,status='old')
    // {F77}             do i=1,2
    // {F77}                read(20,*)  !2 lines of header
    // {F77}             enddo
    // {F77}             write(*,*) 'Reading IR dust emission library...'
    // {F77}             i_ir=0
    // {F77}             io=0
    // {F77}             do while(io.eq.0)
    // {F77}                i_ir=i_ir+1
    // {F77}                read(20,*,iostat=io) (fprop_ir(i_ir,j),j=1,nprop_ir),
    // {F77}      +              (flux_ir(i_ir,j),j=1,nfilt_ir)
    // {F77} c     IR model parameters
    // {F77}                fmu_ir(i_ir)=fprop_ir(i_ir,1)       ! fmu parameter Ld(ISM)/Ld(tot) - infrared
    // {F77}                fmu_ism(i_ir)=fprop_ir(i_ir,2)      ! xi_C^ISM [cont. cold dust to Ld(ISM)]
    // {F77}                tbg2(i_ir)=fprop_ir(i_ir,4)         ! T_C^ISM [eq. temp. cold dust in ISM]
    // {F77}                tbg1(i_ir)=fprop_ir(i_ir,3)         ! T_W^BC [eq. temp. warm dust in birth clouds]
    // {F77}                xi1(i_ir)=fprop_ir(i_ir,5)          ! xi_PAH^BC Ld(PAH)/Ld(BC)
    // {F77}                xi2(i_ir)=fprop_ir(i_ir,6)          ! xi_MIR^BC Ld(MIR)/Ld(BC)
    // {F77}                xi3(i_ir)=fprop_ir(i_ir,7)          ! xi_W^BC Ld(warm)/Ld(BC)
    // {F77}                mdust(i_ir)=fprop_ir(i_ir,8) !dust mass
    while (getline(in_file, line)) {
        // We need to remove the white space for split to work
        boost::trim(line);
        if (line.length() > 0) {
            if (line[0] != '#') {
                vector<string> elements;
                boost::split(elements, line, boost::is_any_of(" \t"), boost::token_compress_on);
                ModelInfrared& model = modelInfrared__[n_ir__];
                model.fmu_ir__ = atof(elements[0].c_str());     // fmu parameter Ld(ISM)/Ld(tot) - infrared
                model.fmu_ism__ = atof(elements[1].c_str());    // xi_C^ISM [cont. cold dust to Ld(ISM)]
                model.tbg1__ = atof(elements[2].c_str());       // T_W^BC [eq. temp. warm dust in birth clouds]
                model.tbg2__ = atof(elements[3].c_str());       // T_C^ISM [eq. temp. cold dust in ISM]
                model.xi1__ = atof(elements[4].c_str());        // xi_PAH^BC Ld(PAH)/Ld(BC)
                model.xi2__ = atof(elements[5].c_str());        // xi_MIR^BC Ld(MIR)/Ld(BC)
                model.xi3__ = atof(elements[6].c_str());        // xi_W^BC Ld(warm)/Ld(BC)
                model.mdust__ = atof(elements[7].c_str());      // dust mass

                // Only if we have the data
                if (nfilt_ir__ > 0) {
                    double flux[nfilt_ir__];
                    for (int j = 0; j < nfilt_ir__; j++) {
                        flux[j] = atof(elements[8 + j].c_str());
                    }

                    // {F77} c     .lbr contains absolute AB magnitudes -> convert to fluxes Fnu in Lo/Hz
                    // {F77} c     Convert all magnitudes to Lo/Hz
                    // {F77}                do k=1,nfilt_ir
                    // {F77}                   flux_ir(i_ir,k)=3.117336e+6
                    // {F77}      +                 *10**(-0.4*(flux_ir(i_ir,k)+48.6))
                    // {F77}                   flux_ir(i_ir,k)=flux_ir(i_ir,k)/(1+redshift(i_gal))
                    // {F77}                enddo
                    int index = n_ir__ * nfilt_ir__;
                    for (int j = 0; j < nfilt_ir__; j++) {
                        flux[j] = 3.117336e+6 * pow(10, -0.4 * (flux[j] + 48.6));
                        // ary[i][j] is then rewritten as
                        // ary[i*sizeY+j]
                        flux_ir__[index + j] = flux[j] / (1 + redshift__);
                    }
                }
                // {F77} c     Re-define IR parameters: xi^tot
                // {F77}                xi1(i_ir)=xi1(i_ir)*(1.-fmu_ir(i_ir))+
                // {F77}      +              0.550*(1-fmu_ism(i_ir))*fmu_ir(i_ir) ! xi_PAH^tot Ld(PAH)/Ld(tot)
                // {F77}                xi2(i_ir)=xi2(i_ir)*(1.-fmu_ir(i_ir))+
                // {F77}      +              0.275*(1-fmu_ism(i_ir))*fmu_ir(i_ir) ! xi_MIR^tot Ld(MIR)/Ld(tot)
                // {F77}                xi3(i_ir)=xi3(i_ir)*(1.-fmu_ir(i_ir))+
                // {F77}      +              0.175*(1-fmu_ism(i_ir))*fmu_ir(i_ir) ! xi_W^tot Ld(warm)/Ld(tot)
                // {F77}                fmu_ism(i_ir)=fmu_ism(i_ir)*fmu_ir(i_ir)  ! xi_C^tot Ld(cold)/Ld(tot)
                model.xi1__ = model.xi1__ * (1 - model.fmu_ir__) + 0.550 * (1 - model.fmu_ism__) * model.fmu_ir__;
                model.xi2__ = model.xi2__ * (1 - model.fmu_ir__) + 0.275 * (1 - model.fmu_ism__) * model.fmu_ir__;
                model.xi3__ = model.xi3__ * (1 - model.fmu_ir__) + 0.175 * (1 - model.fmu_ism__) * model.fmu_ir__;
                model.fmu_ism__ = model.fmu_ism__ * model.fmu_ir__;

                n_ir__++;
            }
        }
    }

    in_file.close();
    return result;
}

/*
 * Load the optical model
 */
bool ModelData::loadModelOptical(const string& filename) {
    std::ifstream in_file;
    in_file.open(filename, std::ios_base::in);
    if (!in_file) {
        cerr << "Unable to open file " << filename << endl;
        return false;
    }

    // Allocate the space
    if (nfilt_sfh__ > 0) {
        flux_sfh__ = new double[NMOD * nfilt_sfh__];
    }
    modelOptical__ = new ModelOptical[NMOD];

    cout << "Reading SFH library..." << endl;
    bool result = true;
    string line;
    n_sfh__ = 0;
    // {F77}             open(21,file=optlib,status='old')
    // {F77}             do i=1,2
    // {F77}                read(21,*) !2 lines of header
    // {F77}             enddo
    // {F77}             write(*,*) 'Reading SFH library...'
    // {F77}             i_sfh=0
    // {F77}             io=0
    // {F77}             do while(io.eq.0)
    // {F77}                i_sfh=i_sfh+1
    // {F77}                read(21,*,iostat=io) indx(i_sfh),(fprop_sfh(i_sfh,j),j=1,nprop_sfh),
    // {F77}      +              (flux_sfh(i_sfh,j),j=1,nfilt_sfh)
    // {F77}                if (io.eq.0) then
    // {F77} c     Relevant physical parameters
    // {F77}                   fmu_sfh(i_sfh)=fprop_sfh(i_sfh,22)            ! fmu parameter Ld(ISM)/Ld(tot) - optical
    // {F77}                   mstr1(i_sfh)=fprop_sfh(i_sfh,6)               ! stellar mass
    // {F77}                   ldust(i_sfh)=fprop_sfh(i_sfh,21)/mstr1(i_sfh) ! total luminosity of dust (normalize to Mstar)
    // {F77}                   logldust(i_sfh)=dlog10(ldust(i_sfh))          ! log(Ldust)
    // {F77}                   mu(i_sfh)=fprop_sfh(i_sfh,5)                  ! mu parameter (CF00 model)
    // {F77}                   tauv(i_sfh)=fprop_sfh(i_sfh,4)                ! optical V-band depth tauV (CF00 model)
    // {F77}                   ssfr(i_sfh)=fprop_sfh(i_sfh,10)/mstr1(i_sfh)  ! recent SSFR_0.01Gyr / stellar mass
    // {F77}                   lssfr(i_sfh)=dlog10(ssfr(i_sfh))              ! log(SSFR_0.01Gyr)
    // {F77}                   tvism(i_sfh)=mu(i_sfh)*tauv(i_sfh)            ! mu*tauV=V-band optical depth for ISM
    while (getline(in_file, line)) {
        // We need to remove the white space for split to work
        boost::trim(line);
        if (line.length() > 0) {
            if (line[0] != '#') {
                vector<string> elements;
                boost::split(elements, line, boost::is_any_of(" \t"), boost::token_compress_on);
                ModelOptical& model = modelOptical__[n_sfh__];

                model.fmu_sfh__ = atof(elements[22].c_str());               // fmu parameter Ld(ISM)/Ld(tot) - optical
                model.mstr1__ = atof(elements[6].c_str());                  // stellar mass
                model.ldust__ = atof(elements[21].c_str()) / model.mstr1__; // total luminosity of dust (normalize to Mstar)
                model.logldust__ = log10(model.ldust__);                    // log(Ldust)
                model.mu__ = atof(elements[5].c_str());                     // mu parameter (CF00 model)
                model.tauv__ = atof(elements[4].c_str());                   // optical V-band depth tauV (CF00 model)
                model.ssfr__ = atof(elements[10].c_str());                  // recent SSFR_0.01Gyr / stellar mass
                model.lssfr__ = log10(model.ssfr__);                        // log(SSFR_0.01Gyr)
                model.tvsim__ = model.mu__ * model.tauv__;                  // mu*tauV=V-band optical depth for ISM

                // Only if we have the data
                if (nfilt_sfh__ > 0) {
                    double flux[nfilt_sfh__];
                    for (int j = 0; j < nfilt_sfh__; j++) {
                        flux[j] = atof(elements[25 + j].c_str());
                    }

                    // {F77} c     .lbr contains absolute AB magnitudes -> convert to fluxes Fnu in Lo/Hz
                    // {F77} c     Convert all magnitudes to Lo/Hz (except H lines luminosity: in Lo)
                    // {F77} c     Normalise SEDs to stellar mass
                    // {F77}                   do k=1,nfilt_sfh
                    // {F77}                      flux_sfh(i_sfh,k)=3.117336e+6
                    // {F77}      +                    *10**(-0.4*(flux_sfh(i_sfh,k)+48.6))
                    // {F77}                      flux_sfh(i_sfh,k)=flux_sfh(i_sfh,k)/mstr1(i_sfh)
                    // {F77} c     1+z factor which is required in model fluxes
                    // {F77}                      flux_sfh(i_sfh,k)=flux_sfh(i_sfh,k)/(1+redshift(i_gal))
                    // {F77}                   enddo
                    // {F77}                endif
                    // {F77}             enddo
                    int index = n_sfh__ * nfilt_sfh__;
                    for (int j = 0; j < nfilt_sfh__; j++) {
                        flux[j] = 3.117336e+6 * pow(10, -0.4 * (flux[j] + 48.6));
                        flux[j] = flux[j] / model.mstr1__;
                        // ary[i][j] is then rewritten as
                        // ary[i*sizeY+j]
                        flux_sfh__[index + j] = flux[j] / (1 + redshift__);
                    }
                }
                n_sfh__++;
            }
        }
    }
    in_file.close();
    return result;
}

void ModelData::convertToLnu(double distance, ObservationLine& observationLine) {
    // {F77} c     ---------------------------------------------------------------------------
    // {F77} c     COMPARISON BETWEEN MODELS AND OBSERVATIONS:
    // {F77} c
    // {F77} c     Compare everything in the sample units:
    // {F77} c     Lnu (i.e. luminosity per unit frequency) in Lsun/Hz
    // {F77} c
    // {F77} c     Model fluxes: already converted from AB mags to Lnu in Lsun/Hz
    // {F77} c     Fluxes and physical parameters from optical library per unit Mstar=1 Msun
    // {F77} c     Fluxes and physical parameters from infrared library per unit Ldust=1 Lsun
    // {F77} c
    // {F77} c     Observed fluxes & uncertainties
    // {F77} c     Convert from Fnu in Jy to Lnu in Lo/Hz [using luminosity distance dist(i_gal)]
    // {F77} c     ---------------------------------------------------------------------------
    // {F77}
    // {F77} c     Observed fluxes: Jy -> Lsun/Hz
    // {F77}          do k=1,nfilt
    // {F77}             if (flux_obs(i_gal,k).gt.0) then
    // {F77}                flux_obs(i_gal,k)=flux_obs(i_gal,k)*1.e-23
    // {F77}      +              *3.283608731e-33*(dist(i_gal)**2)
    // {F77}                sigma(i_gal,k)=sigma(i_gal,k)*1.e-23
    // {F77}      +              *3.283608731e-33*(dist(i_gal)**2)
    // {F77}             endif
    // {F77}             if (sigma(i_gal,k).lt.0.05*flux_obs(i_gal,k)) then
    // {F77}                sigma(i_gal,k)=0.05*flux_obs(i_gal,k)
    // {F77}             endif
    // {F77}          enddo
    // {F77}
    // {F77}          do k=1,nfilt
    // {F77}             if (sigma(i_gal,k).gt.0.0) then
    // {F77}                w(i_gal,k) = 1.0 / (sigma(i_gal,k)**2)
    // {F77}             endif
    // {F77}          enddo
    for (auto& observation : observationLine.observations__) {
        if (observation.flux_obs__ > 0) {
            observation.flux_obs__ = observation.flux_obs__ * 1.0e-23 * 3.283608731e-33 * pow(distance, 2);
            observation.sigma__ = observation.sigma__ * 1.0e-23 * 3.283608731e-33 * pow(distance, 2);
        }
        if (observation.sigma__ < 0.05 * observation.flux_obs__) {
            observation.sigma__ = 0.05 * observation.flux_obs__;
        }
    }
    for (auto& observation : observationLine.observations__) {
        if (observation.sigma__ > 0.0) {
            observation.w__ = 1.0 / (pow(observation.sigma__, 2));
        }
    }
}
}
