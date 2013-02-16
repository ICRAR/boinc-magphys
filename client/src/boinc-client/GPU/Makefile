all: fit_sed fit_sed_opencl

fit_sed:
	g++ -Wall -Ofast -fsingle-precision-constant -static -o fit_sed fit_sed_skynet.cpp

fit_sed_opencl:
#	g++ -Wall -Ofast -fsingle-precision-constant -DUSE_OPENCL -I. -I/usr/local/cuda/include -L/usr/local/cuda/lib64 -o fit_sed_opencl fit_sed_skynet.cpp -lOpenCL
	g++ -Wall -Ofast -fsingle-precision-constant -DUSE_OPENCL -I. -L/usr/lib -o fit_sed_opencl fit_sed_skynet.cpp -lOpenCL

clean:
	rm -f fit_sed
	rm -f fit_sed_opencl
