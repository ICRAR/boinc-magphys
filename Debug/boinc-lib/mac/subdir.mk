################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
/Users/rob/development/boinc/lib/mac/mac_backtrace.cpp 

C_SRCS += \
/Users/rob/development/boinc/lib/mac/QBacktrace.c \
/Users/rob/development/boinc/lib/mac/QCrashReport.c \
/Users/rob/development/boinc/lib/mac/QMachOImage.c \
/Users/rob/development/boinc/lib/mac/QMachOImageList.c \
/Users/rob/development/boinc/lib/mac/QSymbols.c \
/Users/rob/development/boinc/lib/mac/QTaskMemory.c 

OBJS += \
./boinc-lib/mac/QBacktrace.o \
./boinc-lib/mac/QCrashReport.o \
./boinc-lib/mac/QMachOImage.o \
./boinc-lib/mac/QMachOImageList.o \
./boinc-lib/mac/QSymbols.o \
./boinc-lib/mac/QTaskMemory.o \
./boinc-lib/mac/mac_backtrace.o 

C_DEPS += \
./boinc-lib/mac/QBacktrace.d \
./boinc-lib/mac/QCrashReport.d \
./boinc-lib/mac/QMachOImage.d \
./boinc-lib/mac/QMachOImageList.d \
./boinc-lib/mac/QSymbols.d \
./boinc-lib/mac/QTaskMemory.d 

CPP_DEPS += \
./boinc-lib/mac/mac_backtrace.d 


# Each subdirectory must supply rules for building sources it contributes
boinc-lib/mac/QBacktrace.o: /Users/rob/development/boinc/lib/mac/QBacktrace.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boinc-lib/mac/QCrashReport.o: /Users/rob/development/boinc/lib/mac/QCrashReport.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boinc-lib/mac/QMachOImage.o: /Users/rob/development/boinc/lib/mac/QMachOImage.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boinc-lib/mac/QMachOImageList.o: /Users/rob/development/boinc/lib/mac/QMachOImageList.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boinc-lib/mac/QSymbols.o: /Users/rob/development/boinc/lib/mac/QSymbols.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boinc-lib/mac/QTaskMemory.o: /Users/rob/development/boinc/lib/mac/QTaskMemory.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boinc-lib/mac/mac_backtrace.o: /Users/rob/development/boinc/lib/mac/mac_backtrace.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


