################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
/Users/rob/development/boinc/db/boinc_db.cpp \
/Users/rob/development/boinc/db/db_base.cpp 

OBJS += \
./boinc-db/boinc_db.o \
./boinc-db/db_base.o 

CPP_DEPS += \
./boinc-db/boinc_db.d \
./boinc-db/db_base.d 


# Each subdirectory must supply rules for building sources it contributes
boinc-db/boinc_db.o: /Users/rob/development/boinc/db/boinc_db.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boinc-db/db_base.o: /Users/rob/development/boinc/db/db_base.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


