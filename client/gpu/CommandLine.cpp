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
#include <fstream>
#include <cstdlib>
#include "CommandLine.hpp"

namespace magphys {

CommandLine::CommandLine() {
	redshift_ = 0;
	startingLine_ = 0;
}

CommandLine::~CommandLine() {
}

/*
 * Load the command line arguments
 */
bool CommandLine::loadArguments(const vector<string>& args) {
	// Do we have the correct number of arguments?
	if (args.size() == 5 || args.size() == 6) {
        // We do have the right number
        redshift_ = atof(args[0].c_str());
        observationsFile_ = args[1];
        filtersFile_ = args[2];
        modelInfraredFile_ = args[3];
        modelOpticalFile_ = args[4];

        if (args.size() == 6) {
            startingLine_ = atoi(args[5].c_str());
        }

        return checkFiles();
	}
    return false;
}

/*
 * Check the files exist
 */
bool CommandLine::checkFiles() {
	bool ok = true;

    std::ifstream obsFile(observationsFile_.c_str() );
	if ( !obsFile.good() ) {
		std::cerr << "The file " << observationsFile_ << " does not exist." << std::endl;
		ok = false;
	}

    std::ifstream filtFile(filtersFile_.c_str() );
	if ( !filtFile.good() ) {
		std::cerr << "The file " << filtersFile_ << " does not exist."
				<< std::endl;
		ok = false;
	}

    std::ifstream irFile(modelInfraredFile_.c_str() );
	if ( !irFile.good() ) {
		std::cerr << "The file " << modelInfraredFile_ << " does not exist."
				<< std::endl;
		ok = false;
	}

    std::ifstream sfhFile(modelOpticalFile_.c_str() );
	if ( !sfhFile.good() ) {
		std::cerr << "The file " << modelOpticalFile_ << " does not exist."
				<< std::endl;
		ok = false;
	}

	return ok;
}
} //namespace magphys
