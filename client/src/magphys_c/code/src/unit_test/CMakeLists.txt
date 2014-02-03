#
#   (c) UWA, The University of Western Australia
#   M468/35 Stirling Hwy
#   Perth WA 6009
#   Australia
#
#   Copyright by UWA, 2012-2013
#   All rights reserved
#
#   This library is free software; you can redistribute it and/or
#   modify it under the terms of the GNU Lesser General Public
#   License as published by the Free Software Foundation; either
#   version 2.1 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public
#   License along with this library; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#   MA 02111-1307  USA
#

add_gmock_test(fit_sed_test 
               test_STR.cpp
               test_STR.hpp
               test_CommandLine.cpp
               test_ModelData.cpp
               test_ModelDataLoad.cpp
               test_Fit.cpp
               test_ConvertToLnu.cpp)

target_link_libraries(fit_sed_test 
                      fit_sed_core
                      boost_filesystem
                      boost_system)
