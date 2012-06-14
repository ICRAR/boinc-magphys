CXX=g++
CXXFLAGS=-g -O2 -Wall

all: wrapper

wrapper: wrapper.o magphys_validator.o
	${CXX} ${CXXFLAGS} -o $@ $^
