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
#include <ctime>

#include "Constants.hpp"
#include "CommandLine.hpp"
#include "Fit.hpp"
#include "ModelData.hpp"

int main(int argc, char* argv[]) {
    clock_t startedAt = clock();

#if defined(WIN32)
    //Required as windows default is 3 digit exponent.
    _set_output_format(_TWO_DIGIT_EXPONENT);
#endif

    // Convert the args to a list
    vector<string> args;
    for(int i = 1; i < argc; i++) {
        args.push_back(argv[i]);
    }

    magphys::CommandLine commandLine;
    if(!commandLine.loadArguments(args)) {
        return 1;
    }

    // Load the filters we are using
    magphys::ModelData modelData;
    modelData.initialise(  commandLine.redshift() );

    if(!modelData.loadFilters(commandLine.filtersFile())) {
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

    magphys::Fit fit;
    //TODO: I would like redshift to be based on the observation instead of command line, unless we are going to use it to filter out observations that don't match...
    fit.initialise( commandLine.redshift() );
    fit.initializeOptical( modelData.modelOptical(0), modelData.n_sfh() );
    fit.initializeInfrared( modelData.modelInfrared(0), modelData.n_ir() );

    // Load the observations
    if(!fit.loadObservations(commandLine.observationsFile(), 
            modelData.filters(), modelData.nfilt_pureStellar(), modelData.nfilt_mixed(), modelData.nfilt_pureDust() )) {
        return 1;
    }

    fit.fit( &modelData );
    
    std::cout << " Time: " << ((clock() - startedAt)/ (double)CLOCKS_PER_SEC) << endl;

    return 0;
}
