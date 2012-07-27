################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
/Users/rob/development/boinc/clientgui/common/wxFlatNotebook.cpp \
/Users/rob/development/boinc/clientgui/common/wxPieCtrl.cpp 

OBJS += \
./boinc-clientgui/common/wxFlatNotebook.o \
./boinc-clientgui/common/wxPieCtrl.o 

CPP_DEPS += \
./boinc-clientgui/common/wxFlatNotebook.d \
./boinc-clientgui/common/wxPieCtrl.d 


# Each subdirectory must supply rules for building sources it contributes
boinc-clientgui/common/wxFlatNotebook.o: /Users/rob/development/boinc/clientgui/common/wxFlatNotebook.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boinc-clientgui/common/wxPieCtrl.o: /Users/rob/development/boinc/clientgui/common/wxPieCtrl.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


