BOINC_DIR = /home/ec2-user/boinc
BOINC_API_DIR = $(BOINC_DIR)/api
BOINC_LIB_DIR = $(BOINC_DIR)/lib
BOINC_SRC_DIR = $(BOINC_DIR)/sched

CXX=g++
CXXFLAGS1=-g -O2 -Wall
PROGS = magphys_validator
CXXFLAGS = -Wall -Wextra -Wshadow -Wredundant-decls -Wdisabled-optimization -Wpointer-arith -Wstrict-aliasing -g -O2 -Wall -static
LIBS = $(BOINC_SRC_DIR)/libsched.la $(BOINC_LIB_DIR)/libboinc_crypt.la $(BOINC_LIB_DIR)/libboinc.la -L/usr/lib64/mysql -lmysqlclient -lpthread -lz -lm -lrt -lssl -lcrypto -ldl

all: $(PROGS)

wrapper: wrapper.o magphys_validator.o
	$(CXX) $(CXXFLAGS1) -o $@ $^

magphys_validator: magphys_validator.o $(BOINC_SRC_DIR)/credit.o $(BOINC_SRC_DIR)/validator.o $(BOINC_SRC_DIR)/validate_util.o $(BOINC_SRC_DIR)/validate_util2.o
	/bin/sh $(BOINC_DIR)/libtool --tag=CXX --mode=link $(CXX) $(CXXFLAGS) -o $@ $^ $(LIBS)
