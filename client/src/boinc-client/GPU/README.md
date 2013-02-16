# fit_sed C/C++ based and GPU client

- Here you will find the code for the C/C++ version of fit_sed. It includes OpenCL instruction to run on GPUs.

- Makefiles have been included for compiling on different platforms. E.g. Makefile.mac for Mac OSX.

- OpenCL code does not get compiled in unless -DUSE_OPENCL is specified as a compiler option. This happens automatically in the Makefiles.

- OpenCL conforms with version 1.1 standard and uses C++ bindings through the opencl.hpp header file.

- OpenCL header files for Linux and Windows in "CL" folder. A copy has been made in "OpenCL" folder for compiling on Mac.
