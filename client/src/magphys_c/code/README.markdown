# MAGPHYS C++ Code

## Prerequisites

* Boost

The code uses the standard c++11 so you'll need a compiler that supports this.

## Build

The code is built using CMake and Eclipse. 
To build the eclipse project from CMake do the following:

```bash
mkdir build

cd build

cmake -G "Eclipse CDT4 - Unix Makefiles" -D_ECLIPSE_VERSION=4.3 -DCMAKE_BUILD_TYPE=Debug  ../code/

make 
```

## Tests

The testing framework uses the *Boost Unit Test Framework*.
The only reason to use it is Eclipse can parse the header files and not give syntax errors. 
It has problems with GMock

##Debugging

Unfortunately under OS X Mavericks - Apple have removed the gdb and moved everything to clang and lldb. 
This means that eclipse CDT can't debug the code as it (at the time of writing)