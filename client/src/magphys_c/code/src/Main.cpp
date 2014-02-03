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
#include "Constants.hpp"
#include "CommandLine.hpp"
#include "Fit.hpp"
#include "ModelData.hpp"

int main(int argc, char* argv[]) {

#if defined(WIN32)
    //Required as windows default is 3 digit exponent.
    _set_output_format(_TWO_DIGIT_EXPONENT);
#endif

    // Convert the args to a list
    vector<string> args;
    for(int i = 1; i < argc; i++) {
        args.push_back(argv[1]);
    }

    magphys::CommandLine commandLine;
    if(!commandLine.loadArguments(args)) {
        return 1;
    }

    // Load the filters we are using
    magphys::ModelData modelData {commandLine.redshift()};
    if(!modelData.loadFilters(commandLine.filtersFile())) {
        return 1;
    }

    // Load the observations
    if(!modelData.loadObservations(commandLine.observationsFile())) {
        return 1;
    }

    // Load the IR Model
    if(!modelData.loadModelInfrared(commandLine.modelInfraredFile())) {
        return 1;
    }

    // Load the Optical Model
    if(!modelData.loadModelOptical(commandLine.modelOpticalFile())) {
        return 1;
    }

    magphys::Fit fit {modelData.redshift()};
    fit.initialise();

    // For each observation
    vector<magphys::ObservationLine>& observationLines = *modelData.observationLines(); 
    for(size_t i = 0; i < observationLines.size(); i++) {
        magphys::ObservationLine& observationLine = observationLines[i];
        // Check we have enough fluxes to work on
        int numberFluxes = 0;
        for(auto& observation : observationLine.observations) {
            if(observation.flux_obs > 0) {
                numberFluxes++;
            }
        }

        // If we haven't enough fluxes ignore
        std::cout << "number fluxes = " << numberFluxes << std::endl;
        if(numberFluxes < 4) {
            continue;
        }

        // Correct the fluxes for this observation
        modelData.convertToLnu(fit.dist(), observationLine);
        
    }

    return 0;
}
