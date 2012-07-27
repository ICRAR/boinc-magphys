################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
../server/src/Validator/sample_bitwise_validator.cpp \
../server/src/Validator/validate_util.cpp \
../server/src/Validator/validate_util2.cpp \
../server/src/Validator/validator.cpp 

OBJS += \
./server/src/Validator/sample_bitwise_validator.o \
./server/src/Validator/validate_util.o \
./server/src/Validator/validate_util2.o \
./server/src/Validator/validator.o 

CPP_DEPS += \
./server/src/Validator/sample_bitwise_validator.d \
./server/src/Validator/validate_util.d \
./server/src/Validator/validate_util2.d \
./server/src/Validator/validator.d 


# Each subdirectory must supply rules for building sources it contributes
server/src/Validator/%.o: ../server/src/Validator/%.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -I/usr/local/mysql-5.5.13-osx10.6-x86_64/include -I/Users/rob/development/boinc/db -I/Users/rob/development/boinc/api -I/Users/rob/development/boinc/sched -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


