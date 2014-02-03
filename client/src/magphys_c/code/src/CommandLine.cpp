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
        if(args.size() != 5) {
            return false;
        }

        // We do have the right number
        redshift_ = atof(args[0].c_str());
        observationsFile_ = args[1];
        filtersFile_ = args[2];
        modelInfraredFile_ = args[3];
        modelOpticalFile_ = args[4];
        return checkFiles();
    }


    /*
     * Check the files exist
     */
    bool CommandLine::checkFiles() {
        bool ok = true;
        if(!boost::filesystem::exists(observationsFile_)) {
            std::cerr << "The file " << observationsFile_ << " does not exist." << std::endl;
            ok = false;
        }
        if(!boost::filesystem::exists(filtersFile_)) {
            std::cerr << "The file " << filtersFile_ << " does not exist." << std::endl;
            ok = false;
        }
        if(!boost::filesystem::exists(modelInfraredFile_)) {
            std::cerr << "The file " << modelInfraredFile_ << " does not exist." << std::endl;
            ok = false;
        }
        if(!boost::filesystem::exists(modelOpticalFile_)) {
            std::cerr << "The file " << modelOpticalFile_ << " does not exist." << std::endl;
            ok = false;
        }

        return ok;
    }
} //namespace magphys
