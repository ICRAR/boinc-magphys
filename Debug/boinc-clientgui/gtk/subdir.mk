################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
/Users/rob/development/boinc/clientgui/gtk/taskbarex.cpp 

OBJS += \
./boinc-clientgui/gtk/taskbarex.o 

CPP_DEPS += \
./boinc-clientgui/gtk/taskbarex.d 


# Each subdirectory must supply rules for building sources it contributes
boinc-clientgui/gtk/taskbarex.o: /Users/rob/development/boinc/clientgui/gtk/taskbarex.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


