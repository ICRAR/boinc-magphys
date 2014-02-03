########################################################################
# Build the C++ version of MAGPHYS

add_executable(fit_sed_c Main.cpp)
target_link_libraries(fit_sed_c 
                      fit_sed_core
                      boost_filesystem
                      boost_system)

add_library(fit_sed_core 
            CommandLine.cpp
			CommandLine.hpp
            Fit.cpp
			Fit.hpp
            ModelData.cpp
			ModelData.hpp
			Constants.hpp			
            fit_sed_skynet.cpp
            fit_sed_skynet.f)

add_subdirectory(unit_test)
