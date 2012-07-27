################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
../server/src/Assimilator/assimilator.cpp \
../server/src/Assimilator/sample_assimilator.cpp 

OBJS += \
./server/src/Assimilator/assimilator.o \
./server/src/Assimilator/sample_assimilator.o 

CPP_DEPS += \
./server/src/Assimilator/assimilator.d \
./server/src/Assimilator/sample_assimilator.d 


# Each subdirectory must supply rules for building sources it contributes
server/src/Assimilator/%.o: ../server/src/Assimilator/%.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -I/usr/local/mysql-5.5.13-osx10.6-x86_64/include -I/Users/rob/development/boinc/db -I/Users/rob/development/boinc/api -I/Users/rob/development/boinc/sched -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


