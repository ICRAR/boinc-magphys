################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
/Users/rob/development/boinc/sched/antique_file_deleter.cpp \
/Users/rob/development/boinc/sched/assimilator.cpp \
/Users/rob/development/boinc/sched/census.cpp \
/Users/rob/development/boinc/sched/credit.cpp \
/Users/rob/development/boinc/sched/credit_test.cpp \
/Users/rob/development/boinc/sched/db_dump.cpp \
/Users/rob/development/boinc/sched/db_purge.cpp \
/Users/rob/development/boinc/sched/delete_file.cpp \
/Users/rob/development/boinc/sched/edf_sim.cpp \
/Users/rob/development/boinc/sched/feeder.cpp \
/Users/rob/development/boinc/sched/file_deleter.cpp \
/Users/rob/development/boinc/sched/file_upload_handler.cpp \
/Users/rob/development/boinc/sched/get_file.cpp \
/Users/rob/development/boinc/sched/handle_request.cpp \
/Users/rob/development/boinc/sched/hr.cpp \
/Users/rob/development/boinc/sched/hr_info.cpp \
/Users/rob/development/boinc/sched/make_work.cpp \
/Users/rob/development/boinc/sched/message_handler.cpp \
/Users/rob/development/boinc/sched/plan_class_spec.cpp \
/Users/rob/development/boinc/sched/put_file.cpp \
/Users/rob/development/boinc/sched/sample_assimilator.cpp \
/Users/rob/development/boinc/sched/sample_bitwise_validator.cpp \
/Users/rob/development/boinc/sched/sample_dummy_assimilator.cpp \
/Users/rob/development/boinc/sched/sample_trivial_validator.cpp \
/Users/rob/development/boinc/sched/sample_work_generator.cpp \
/Users/rob/development/boinc/sched/sched_array.cpp \
/Users/rob/development/boinc/sched/sched_assign.cpp \
/Users/rob/development/boinc/sched/sched_config.cpp \
/Users/rob/development/boinc/sched/sched_customize.cpp \
/Users/rob/development/boinc/sched/sched_driver.cpp \
/Users/rob/development/boinc/sched/sched_hr.cpp \
/Users/rob/development/boinc/sched/sched_limit.cpp \
/Users/rob/development/boinc/sched/sched_locality.cpp \
/Users/rob/development/boinc/sched/sched_main.cpp \
/Users/rob/development/boinc/sched/sched_msgs.cpp \
/Users/rob/development/boinc/sched/sched_resend.cpp \
/Users/rob/development/boinc/sched/sched_result.cpp \
/Users/rob/development/boinc/sched/sched_score.cpp \
/Users/rob/development/boinc/sched/sched_send.cpp \
/Users/rob/development/boinc/sched/sched_shmem.cpp \
/Users/rob/development/boinc/sched/sched_timezone.cpp \
/Users/rob/development/boinc/sched/sched_types.cpp \
/Users/rob/development/boinc/sched/sched_util.cpp \
/Users/rob/development/boinc/sched/sched_version.cpp \
/Users/rob/development/boinc/sched/show_shmem.cpp \
/Users/rob/development/boinc/sched/single_job_assimilator.cpp \
/Users/rob/development/boinc/sched/target_batch.cpp \
/Users/rob/development/boinc/sched/time_stats_log.cpp \
/Users/rob/development/boinc/sched/transitioner.cpp \
/Users/rob/development/boinc/sched/trickle_credit.cpp \
/Users/rob/development/boinc/sched/trickle_echo.cpp \
/Users/rob/development/boinc/sched/trickle_handler.cpp \
/Users/rob/development/boinc/sched/update_stats.cpp \
/Users/rob/development/boinc/sched/validate_util.cpp \
/Users/rob/development/boinc/sched/validate_util2.cpp \
/Users/rob/development/boinc/sched/validator.cpp \
/Users/rob/development/boinc/sched/validator_test.cpp \
/Users/rob/development/boinc/sched/wu_check.cpp 

OBJS += \
./boincched/antique_file_deleter.o \
./boincched/assimilator.o \
./boincched/census.o \
./boincched/credit.o \
./boincched/credit_test.o \
./boincched/db_dump.o \
./boincched/db_purge.o \
./boincched/delete_file.o \
./boincched/edf_sim.o \
./boincched/feeder.o \
./boincched/file_deleter.o \
./boincched/file_upload_handler.o \
./boincched/get_file.o \
./boincched/handle_request.o \
./boincched/hr.o \
./boincched/hr_info.o \
./boincched/make_work.o \
./boincched/message_handler.o \
./boincched/plan_class_spec.o \
./boincched/put_file.o \
./boincched/sample_assimilator.o \
./boincched/sample_bitwise_validator.o \
./boincched/sample_dummy_assimilator.o \
./boincched/sample_trivial_validator.o \
./boincched/sample_work_generator.o \
./boincched/sched_array.o \
./boincched/sched_assign.o \
./boincched/sched_config.o \
./boincched/sched_customize.o \
./boincched/sched_driver.o \
./boincched/sched_hr.o \
./boincched/sched_limit.o \
./boincched/sched_locality.o \
./boincched/sched_main.o \
./boincched/sched_msgs.o \
./boincched/sched_resend.o \
./boincched/sched_result.o \
./boincched/sched_score.o \
./boincched/sched_send.o \
./boincched/sched_shmem.o \
./boincched/sched_timezone.o \
./boincched/sched_types.o \
./boincched/sched_util.o \
./boincched/sched_version.o \
./boincched/show_shmem.o \
./boincched/single_job_assimilator.o \
./boincched/target_batch.o \
./boincched/time_stats_log.o \
./boincched/transitioner.o \
./boincched/trickle_credit.o \
./boincched/trickle_echo.o \
./boincched/trickle_handler.o \
./boincched/update_stats.o \
./boincched/validate_util.o \
./boincched/validate_util2.o \
./boincched/validator.o \
./boincched/validator_test.o \
./boincched/wu_check.o 

CPP_DEPS += \
./boincched/antique_file_deleter.d \
./boincched/assimilator.d \
./boincched/census.d \
./boincched/credit.d \
./boincched/credit_test.d \
./boincched/db_dump.d \
./boincched/db_purge.d \
./boincched/delete_file.d \
./boincched/edf_sim.d \
./boincched/feeder.d \
./boincched/file_deleter.d \
./boincched/file_upload_handler.d \
./boincched/get_file.d \
./boincched/handle_request.d \
./boincched/hr.d \
./boincched/hr_info.d \
./boincched/make_work.d \
./boincched/message_handler.d \
./boincched/plan_class_spec.d \
./boincched/put_file.d \
./boincched/sample_assimilator.d \
./boincched/sample_bitwise_validator.d \
./boincched/sample_dummy_assimilator.d \
./boincched/sample_trivial_validator.d \
./boincched/sample_work_generator.d \
./boincched/sched_array.d \
./boincched/sched_assign.d \
./boincched/sched_config.d \
./boincched/sched_customize.d \
./boincched/sched_driver.d \
./boincched/sched_hr.d \
./boincched/sched_limit.d \
./boincched/sched_locality.d \
./boincched/sched_main.d \
./boincched/sched_msgs.d \
./boincched/sched_resend.d \
./boincched/sched_result.d \
./boincched/sched_score.d \
./boincched/sched_send.d \
./boincched/sched_shmem.d \
./boincched/sched_timezone.d \
./boincched/sched_types.d \
./boincched/sched_util.d \
./boincched/sched_version.d \
./boincched/show_shmem.d \
./boincched/single_job_assimilator.d \
./boincched/target_batch.d \
./boincched/time_stats_log.d \
./boincched/transitioner.d \
./boincched/trickle_credit.d \
./boincched/trickle_echo.d \
./boincched/trickle_handler.d \
./boincched/update_stats.d \
./boincched/validate_util.d \
./boincched/validate_util2.d \
./boincched/validator.d \
./boincched/validator_test.d \
./boincched/wu_check.d 


# Each subdirectory must supply rules for building sources it contributes
boincched/antique_file_deleter.o: /Users/rob/development/boinc/sched/antique_file_deleter.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/assimilator.o: /Users/rob/development/boinc/sched/assimilator.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/census.o: /Users/rob/development/boinc/sched/census.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/credit.o: /Users/rob/development/boinc/sched/credit.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/credit_test.o: /Users/rob/development/boinc/sched/credit_test.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/db_dump.o: /Users/rob/development/boinc/sched/db_dump.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/db_purge.o: /Users/rob/development/boinc/sched/db_purge.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/delete_file.o: /Users/rob/development/boinc/sched/delete_file.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/edf_sim.o: /Users/rob/development/boinc/sched/edf_sim.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/feeder.o: /Users/rob/development/boinc/sched/feeder.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/file_deleter.o: /Users/rob/development/boinc/sched/file_deleter.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/file_upload_handler.o: /Users/rob/development/boinc/sched/file_upload_handler.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/get_file.o: /Users/rob/development/boinc/sched/get_file.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/handle_request.o: /Users/rob/development/boinc/sched/handle_request.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/hr.o: /Users/rob/development/boinc/sched/hr.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/hr_info.o: /Users/rob/development/boinc/sched/hr_info.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/make_work.o: /Users/rob/development/boinc/sched/make_work.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/message_handler.o: /Users/rob/development/boinc/sched/message_handler.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/plan_class_spec.o: /Users/rob/development/boinc/sched/plan_class_spec.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/put_file.o: /Users/rob/development/boinc/sched/put_file.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sample_assimilator.o: /Users/rob/development/boinc/sched/sample_assimilator.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sample_bitwise_validator.o: /Users/rob/development/boinc/sched/sample_bitwise_validator.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sample_dummy_assimilator.o: /Users/rob/development/boinc/sched/sample_dummy_assimilator.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sample_trivial_validator.o: /Users/rob/development/boinc/sched/sample_trivial_validator.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sample_work_generator.o: /Users/rob/development/boinc/sched/sample_work_generator.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_array.o: /Users/rob/development/boinc/sched/sched_array.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_assign.o: /Users/rob/development/boinc/sched/sched_assign.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_config.o: /Users/rob/development/boinc/sched/sched_config.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_customize.o: /Users/rob/development/boinc/sched/sched_customize.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_driver.o: /Users/rob/development/boinc/sched/sched_driver.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_hr.o: /Users/rob/development/boinc/sched/sched_hr.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_limit.o: /Users/rob/development/boinc/sched/sched_limit.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_locality.o: /Users/rob/development/boinc/sched/sched_locality.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_main.o: /Users/rob/development/boinc/sched/sched_main.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_msgs.o: /Users/rob/development/boinc/sched/sched_msgs.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_resend.o: /Users/rob/development/boinc/sched/sched_resend.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_result.o: /Users/rob/development/boinc/sched/sched_result.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_score.o: /Users/rob/development/boinc/sched/sched_score.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_send.o: /Users/rob/development/boinc/sched/sched_send.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_shmem.o: /Users/rob/development/boinc/sched/sched_shmem.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_timezone.o: /Users/rob/development/boinc/sched/sched_timezone.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_types.o: /Users/rob/development/boinc/sched/sched_types.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_util.o: /Users/rob/development/boinc/sched/sched_util.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/sched_version.o: /Users/rob/development/boinc/sched/sched_version.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/show_shmem.o: /Users/rob/development/boinc/sched/show_shmem.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/single_job_assimilator.o: /Users/rob/development/boinc/sched/single_job_assimilator.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/target_batch.o: /Users/rob/development/boinc/sched/target_batch.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/time_stats_log.o: /Users/rob/development/boinc/sched/time_stats_log.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/transitioner.o: /Users/rob/development/boinc/sched/transitioner.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/trickle_credit.o: /Users/rob/development/boinc/sched/trickle_credit.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/trickle_echo.o: /Users/rob/development/boinc/sched/trickle_echo.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/trickle_handler.o: /Users/rob/development/boinc/sched/trickle_handler.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/update_stats.o: /Users/rob/development/boinc/sched/update_stats.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/validate_util.o: /Users/rob/development/boinc/sched/validate_util.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/validate_util2.o: /Users/rob/development/boinc/sched/validate_util2.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/validator.o: /Users/rob/development/boinc/sched/validator.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/validator_test.o: /Users/rob/development/boinc/sched/validator_test.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

boincched/wu_check.o: /Users/rob/development/boinc/sched/wu_check.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


