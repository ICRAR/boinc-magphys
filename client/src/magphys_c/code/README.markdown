# MAGPHYS C++ Code

## Prerequisites

* Boost

This uses the standard c++11 

## Build

The code is built using CMake

$ mkdir build
$ cd build
$ cmake -G "Unix Makefiles" ..
$ make 

## Code Layout

The code is laid out using astyle

$ astyle -A2 --recursive "\*.cpp" "\*.hpp"

The double quotes are important.

To remove the .orig files
$ find . -name "*.orig" -exec rm -- {} +

