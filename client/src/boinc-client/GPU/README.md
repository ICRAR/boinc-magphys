# fit_sed C/C++ GPU client

Here you will find the code for the C/C++ version of fit_sed. It includes both standard CPU and OpenCL 
instruction. Please read these notes:

- Makefiles have been included for compiling on different platforms. E.g. Makefile.mac for Mac OSX.

- OpenCL code does not get called in unless -DUSE_OPENCL is specified as a compiler option. This 
happens automatically in the Makefiles. You will see that a non-OpenCL client gets compiled as 
well as the OpenCL version when using make all.

- The actual OpenCL kernel code can be found at fit_sed_skynet.cl and is compiled JIT.

- OpenCL conforms with version 1.1 standard and uses C++ bindings through the opencl.hpp header file.

- OpenCL header files for Linux and Windows in "CL" folder. A copy has been made in "OpenCL" folder 
for compiling on Mac.
