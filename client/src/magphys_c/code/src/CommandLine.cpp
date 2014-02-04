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
#include <boost/filesystem.hpp>
#include "CommandLine.hpp"

namespace magphys {

CommandLine::CommandLine() {
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
        redshift__ = atof(args[0].c_str());
        observationsFile__ = args[1];
        filtersFile__ = args[2];
        modelInfraredFile__ = args[3];
        modelOpticalFile__ = args[4];

        if (args.size() == 6) {
            startingLine__ = atoi(args[5].c_str());
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
	if (!boost::filesystem::exists(observationsFile__)) {
		std::cerr << "The file " << observationsFile__ << " does not exist."
				<< std::endl;
		ok = false;
	}
	if (!boost::filesystem::exists(filtersFile__)) {
		std::cerr << "The file " << filtersFile__ << " does not exist."
				<< std::endl;
		ok = false;
	}
	if (!boost::filesystem::exists(modelInfraredFile__)) {
		std::cerr << "The file " << modelInfraredFile__ << " does not exist."
				<< std::endl;
		ok = false;
	}
	if (!boost::filesystem::exists(modelOpticalFile__)) {
		std::cerr << "The file " << modelOpticalFile__ << " does not exist."
				<< std::endl;
		ok = false;
	}

	return ok;
}
} //namespace magphys
