################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
/Users/rob/development/boinc/clientgui/msw/taskbarex.cpp 

OBJS += \
./boinc-clientgui/msw/taskbarex.o 

CPP_DEPS += \
./boinc-clientgui/msw/taskbarex.d 


# Each subdirectory must supply rules for building sources it contributes
boinc-clientgui/msw/taskbarex.o: /Users/rob/development/boinc/clientgui/msw/taskbarex.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


