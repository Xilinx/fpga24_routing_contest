# Copyright (C) 2023-2024, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author: Eddie Hung, AMD
#
# SPDX-License-Identifier: MIT
#

SHELL := /bin/bash -o pipefail

# List of all benchmarks (default to all)
BENCHMARKS ?= logicnets_jscl		\
              boom_med_pb		\
              vtr_mcml			\
              rosetta_fd		\
              corundum_25g		\
              finn_radioml		\
              vtr_lu64peeng		\
              corescore_500		\
              corescore_500_pb		\
              mlcad_d181_lefttwo3rds	\
              koios_dla_like_large 	\
              boom_soc			\
              ispd16_example2


BENCHMARKS_URL = https://github.com/Xilinx/fpga24_routing_contest/releases/latest/download/benchmarks.tar.gz

# Inherit proxy settings from the host if they exist
HTTPHOST=$(firstword $(subst :, ,$(subst http:,,$(subst /,,$(HTTP_PROXY)))))
HTTPPORT=$(lastword $(subst :, ,$(subst http:,,$(subst /,,$(HTTP_PROXY)))))
HTTPSHOST=$(firstword $(subst :, ,$(subst http:,,$(subst /,,$(HTTPS_PROXY)))))
HTTPSPORT=$(lastword $(subst :, ,$(subst http:,,$(subst /,,$(HTTPS_PROXY)))))
JAVA_PROXY=$(if $(HTTPHOST),-Dhttp.proxyHost=$(HTTPHOST) -Dhttp.proxyPort=$(HTTPPORT),) \
$(if $(HTTPSHOST),-Dhttps.proxyHost=$(HTTPSHOST) -Dhttps.proxyPort=$(HTTPSPORT),)

# Choice of router (default to rwroute)
# (other supported values: nxroute-poc)
ROUTER ?= rwroute

# Make /usr/bin/time only print out wall-clock and user time in seconds
TIME = Wall-clock time (sec): %e
# Note that User-CPU time is for information purposes only (not used for scoring)
TIME += \nUser-CPU time (sec): %U
export TIME

# Existence of the VERBOSE environment variable indicates whether router/
# checker outputs will be displayed on screen
VERBOSE ?= 0
ifneq ($(VERBOSE), 0)
    log_and_or_display = 2>&1 | tee $(1)
else
    log_and_or_display = > $(1) 2>&1
endif

ifdef GITHUB_ACTIONS
    # Limit Java heap size inside GitHub Actions to 6G
    JVM_HEAP = -Xms6g -Xmx6g
else
    # If not specified, limit Java heap size ~32G
    JVM_HEAP ?= -Xms32736m -Xmx32736m
endif

export RAPIDWRIGHT_PATH = $(abspath RapidWright)

# Default recipe: route and score all given benchmarks
.PHONY: run-$(ROUTER)
run-$(ROUTER): score-$(ROUTER)

.PHONY: setup
setup: compile-java setup-net_printer setup-wirelength_analyzer setup-benchmarks

.PHONY: setup-benchmarks
setup-benchmarks: $(addsuffix _unrouted.phys,$(BENCHMARKS)) $(addsuffix .netlist,$(BENCHMARKS))

.PHONY: compile-java
.PHONY: install-python-deps
ifneq ($(APPTAINER_NETWORK),none)

# Use Gradle to compile Java source code in this repository as well as the RapidWright repository.
# Also download/generate all device files necessary for the xcvu3p device
compile-java:
	_JAVA_OPTIONS="$(JAVA_PROXY)" ./gradlew compileJava
	_JAVA_OPTIONS="$(JAVA_PROXY)" RapidWright/bin/rapidwright Jython -c "FileTools.ensureDataFilesAreStaticInstallFriendly('xcvu3p')"
install-python-deps:
	pip install -q -r requirements.txt --pre --user
else
compile-java install-python-deps:
	@echo "$@ target skipped since network disabled inside apptainer"
endif

JAVA_CLASSPATH_TXT = java-classpath.txt
.INTERMEDIATE: $(JAVA_CLASSPATH_TXT)
$(JAVA_CLASSPATH_TXT): compile-java
	echo "$$(./gradlew -quiet --offline runtimeClasspath):build/classes/java/main" > $@

# Download and unpack all benchmarks
.PHONY: download-benchmarks
download-benchmarks:
	curl -L $(BENCHMARKS_URL) | tar -xz

.PRECIOUS: %_unrouted.phys %.netlist
%_unrouted.phys %.netlist:
	$(MAKE) download-benchmarks

# Since the FPGA Interchange Schema is set up for generating Java code,
# ensure that the Capnp Java package is present
fpga-interchange-schema/interchange/capnp/java.capnp:
	mkdir -p $(@D)
	wget https://raw.githubusercontent.com/capnproto/capnproto-java/master/compiler/src/main/schema/capnp/java.capnp -O $@

# Gradle is used to invoke the CheckPhysNetlist class' main method with arguments
# $^ (%.netlist and %_rwroute.phys), and display/redirect all output to $@.log (%_rwroute.check.log).
# The exit code of Gradle determines if 'PASS' or 'FAIL' is written to $@ (%_rwroute.check)
%_$(ROUTER).check: %.netlist %_$(ROUTER).phys %_unrouted.phys | $(JAVA_CLASSPATH_TXT)
	if java -cp $$(cat $(JAVA_CLASSPATH_TXT)) $(JVM_HEAP) com.xilinx.fpga24_routing_contest.CheckPhysNetlist $^ $(call log_and_or_display,$@.log); then \
            echo "PASS" > $@; \
        else \
            echo "FAIL" > $@; \
        fi

%_$(ROUTER).wirelength: %_$(ROUTER).phys | setup-wirelength_analyzer
	if [[ "$(WIRELENGTH_ANALYZER_MOCK_RESULT)" == "true" ]]; then \
            echo "::warning file=$<::wirelength_analyzer not run because WIRELENGTH_ANALYZER_MOCK_RESULT is set"; \
	    echo "Wirelength: inf" > $@; \
	else \
	    python3 wirelength_analyzer/wa.py $< $(call log_and_or_display,$@); \
	fi

.PHONY: score-$(ROUTER)
score-$(ROUTER): $(foreach b,$(BENCHMARKS),$b_$(ROUTER).wirelength $b_$(ROUTER).check)
	python3 ./compute-score.py $(addsuffix _$(ROUTER), $(BENCHMARKS))

.PRECIOUS: %.device
%.device: | compile-java
	_JAVA_OPTIONS="-Xms14g -Xmx14g" RapidWright/bin/rapidwright DeviceResourcesExample $*

.PHONY: setup-net_printer setup-wirelength_analyzer
setup-net_printer setup-wirelength_analyzer: | install-python-deps fpga-interchange-schema/interchange/capnp/java.capnp

clean:
	rm -f *.{check,wirelength,sif}* *_$(ROUTER).phys*

distclean: clean
	rm -rf *.device *.phys *.netlist*
	rm -f *.dcp *_load.tcl
	rm -rf workdir .gradle .local .cache .wget-hsts
	rm -rf .Xilinx


#### BEGIN ROUTER RECIPES

## RWROUTE
# /usr/bin/time is used to measure the wall clock time
# Gradle is used to invoke the PartialRouterPhysNetlist class' main method with arguments
# $< (%_unrouted.phys) and $@ (%_rwroute.phys), and display/redirect all output into %_rwroute.phys.log
%_rwroute.phys: %_unrouted.phys | $(JAVA_CLASSPATH_TXT)
	(/usr/bin/time java -cp $$(cat $(JAVA_CLASSPATH_TXT)) $(JVM_HEAP) com.xilinx.fpga24_routing_contest.PartialRouterPhysNetlist $< $@) $(call log_and_or_display,$@.log)


## NXROUTE-POC
%_nxroute-poc.phys: %_unrouted.phys xcvu3p.device | install-python-deps fpga-interchange-schema/interchange/capnp/java.capnp
	(/usr/bin/time python3 networkx-proof-of-concept-router/nxroute-poc.py $< $@) $(call log_and_or_display,$@.log)

## EXAMPLEROUTE
## (please only modify '<custom router here>' to ensure that all contest infrastructure remains in place)
# %_exampleroute.phys: %_unrouted.phys
# 	(/usr/bin/time <custom router here> $< $@) $(call log_and_or_display,$@.log)

#### END ROUTER RECIPES

#### BEGIN CONTEST SUBMISSION RECIPES

# Required Apptainer args:
# --pid: ensures all processes apptainer spawns are killed with the container
# --containall: isolate the container from the host environment
# --env: propagate certain env vars despite --containall
# --workdir: working directory for /tmp, etc. inside container
# --home: map present working directory as /home inside container
APPTAINER_RUN_ARGS = --pid --containall --env GITHUB_ACTIONS=$(GITHUB_ACTIONS) --workdir `pwd`/workdir --home `pwd`:/home
ifneq ($(wildcard /tools),)
    # Mount the host system's `/tools` directory to the container's `/tools` directory,
    # which allows the container to access the host Vivado installation
    APPTAINER_RUN_ARGS += --bind /tools
endif

# Default Apptainer args. Contestants may modify as necessary.
# --rocm --bind /etc/OpenCL: enables OpenCL access in the container
APPTAINER_RUN_ARGS += --rocm
ifneq ($(wildcard /etc/OpenCL),)
    APPTAINER_RUN_ARGS += --bind /etc/OpenCL --bind /opt/amdgpu/share
endif

# In addition, disable network access when running router
APPTAINER_RUN_ARGS_NO_NETWORK = $(APPTAINER_RUN_ARGS)
APPTAINER_RUN_ARGS_NO_NETWORK += --network none --env APPTAINER_NETWORK=none

# Build an Apptainer image from a definition file in the final_submission directory
%_container.sif: final_submission/%_container.def
	apptainer build $@ $<

.PHONY: workdir
workdir:
	# Clear out the per-session workdir subdirectory
	rm -rf workdir && mkdir workdir

# Use the <ROUTER>_container.sif to perform all necessary setup that requires network access
# (including all setup required for contest infrastructure)
.PHONY: setup-container
setup-container: $(ROUTER)_container.sif | workdir
	apptainer exec $(APPTAINER_RUN_ARGS) $< make setup BENCHMARKS="$(BENCHMARKS)"

# Use the <ROUTER>_container.sif Apptainer image to run all benchmarks without network access
.PHONY: run-container
run-container: $(ROUTER)_container.sif | setup-container
	apptainer exec $(APPTAINER_RUN_ARGS_NO_NETWORK) $< make ROUTER="$(ROUTER)" BENCHMARKS="$(BENCHMARKS)" VERBOSE="$(VERBOSE)" -k

# Use the <ROUTER>_container.sif Apptainer image to run a single small benchmark for testing
.PHONY: test-container
test-container: $(ROUTER)_container.sif | setup-container
	apptainer exec $(APPTAINER_RUN_ARGS_NO_NETWORK) $< make ROUTER="$(ROUTER)" BENCHMARKS="boom_med_pb" VERBOSE="$(VERBOSE)"

SUBMISSION_NAME = $(ROUTER)_submission_$(shell date +%Y%m%d%H%M%S)

# distclean the repo and create an archive ready for submission
# Submission name is <ROUTER NAME>_submission_<timestamp>
.PHONY: distclean-and-package-submission
distclean-and-package-submission: distclean
	tar -czf ../$(SUBMISSION_NAME).tar.gz .
	mv ../$(SUBMISSION_NAME).tar.gz .

#### END CONTEST SUBMISSION RECIPES

#### BEGIN EXAMPLE RECIPES

# Build and run an example OpenCL application in an Apptainer container
opencl_example_container.sif: final_submission/opencl_example/opencl_example_container.def
	apptainer build $@ $<

.PHONY: run-opencl-example
run-opencl-example: opencl_example_container.sif | workdir
	apptainer run $(APPTAINER_RUN_ARGS_NO_NETWORK) $<

#### END EXAMPLE RECIPES

# Tell make to not treat routed results as intermediate files (which would get deleted)
.PRECIOUS: %_$(ROUTER).phys
