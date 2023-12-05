# Copyright (C) 2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author: Eddie Hung, AMD
#
# SPDX-License-Identifier: MIT
#

SHELL := /bin/bash -o pipefail

# List of all benchmarks (default to all)
BENCHMARKS ?= boom_med_pb		\
              vtr_mcml			\
              rosetta_fd		\
              corundum_25g		\
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

# Make /usr/bin/time only print out wall-clock time in seconds
export TIME=Wall-clock time (sec): %e

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

# Use Gradle to compile Java source code in this repository as well as the RapidWright repository.
# Also download/generate all device files necessary for the xcvu3p device
.PHONY: compile-java
compile-java:
	./gradlew $(JAVA_PROXY) compileJava
	_JAVA_OPTIONS="$(JAVA_PROXY)" RapidWright/bin/rapidwright Jython -c "FileTools.ensureDataFilesAreStaticInstallFriendly('xcvu3p')"

.PHONY: install-python-deps
install-python-deps:
	pip install -q -r requirements.txt --pre --user

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
%_$(ROUTER).check: %.netlist %_$(ROUTER).phys | compile-java
	if ./gradlew -DjvmArgs="-Xms6g -Xmx6g" -Dmain=com.xilinx.fpga24_routing_contest.CheckPhysNetlist :run --args='$^' $(call log_and_or_display,$@.log); then \
            echo "PASS" > $@; \
        else \
            echo "FAIL" > $@; \
        fi

%_$(ROUTER).wirelength: %_$(ROUTER).phys | setup-wirelength_analyzer
	if [[ "$(WIRELENGTH_ANALYZER_MOCK_RESULT)" == "true" ]]; then \
            echo "::warning file=$@::wirelength_analyzer not run because WIRELENGTH_ANALYZER_MOCK_RESULT is set"; \
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
	rm -f *.{phys,check,wirelength,sif}*

distclean: clean
	rm -rf *.device *_unrouted.phys *.netlist*


#### BEGIN ROUTER RECIPES

## RWROUTE
# /usr/bin/time is used to measure the wall clock time
# Gradle is used to invoke the PartialRouterPhysNetlist class' main method with arguments
# $< (%_unrouted.phys) and $@ (%_rwroute.phys), and display/redirect all output into %_rwroute.phys.log
%_rwroute.phys: %_unrouted.phys | compile-java
	(/usr/bin/time ./gradlew -DjvmArgs="$(JVM_HEAP)" -Dmain=com.xilinx.fpga24_routing_contest.PartialRouterPhysNetlist :run --args='$< $@') $(call log_and_or_display,$@.log)

## NXROUTE-POC
%_nxroute-poc.phys: %_unrouted.phys xcvu3p.device | install-python-deps fpga-interchange-schema/interchange/capnp/java.capnp
	(/usr/bin/time python3 networkx-proof-of-concept-router/nxroute-poc.py $< $@) $(call log_and_or_display,$@.log)

## EXAMPLEROUTE
# %_exampleroute.phys: %_unrouted.phys | fpga-interchange-schema/interchange/capnp/java.capnp
# 	(/usr/bin/time <custom router here> $< $@) > $@.log $(call log_and_or_display,$@.log)

#### END ROUTER RECIPES

#### BEGIN CONTEST SUBMISSION RECIPES

# Required Apptainer args:
# --pid: ensures all processes apptainer spawns are killed with the container
# --home `pwd`: overrides the home directory inside the container to be the current dir
APPTAINER_RUN_ARGS = --pid --home `pwd`
ifneq ($(wildcard /tools),)
    # Creates a read-only mount of the host system's `/tools` directory to the container's
    # /tools` directory, which allows the container to access the host Vivado installation
    APPTAINER_RUN_ARGS += --mount src=/tools/,dst=/tools/,ro
endif

# Default Apptainer args. Contestants may modify as necessary.
# --rocm --bind /etc/OpenCL: enables OpenCL access in the container
APPTAINER_RUN_ARGS += --rocm
ifneq ($(wildcard /etc/OpenCL),)
    APPTAINER_RUN_ARGS += --bind /etc/OpenCL
endif

# Build an Apptainer image from a definition file in the alpha_submission directory
%_container.sif: alpha_submission/%_container.def
	apptainer build $@ $<

# Use the <ROUTER>_container.sif Apptainer image to run all benchmarks
.PHONY: run-container
run-container: $(ROUTER)_container.sif
	apptainer run $(APPTAINER_RUN_ARGS) $< make ROUTER="$(ROUTER)" BENCHMARKS="$(BENCHMARKS)" VERBOSE="$(VERBOSE)"

# Use the <ROUTER>_container.sif Apptainer image to run a single small benchmark for testing
.PHONY: test-container
test-container: $(ROUTER)_container.sif
	apptainer run $(APPTAINER_RUN_ARGS) $< make ROUTER="$(ROUTER)" BENCHMARKS="boom_med_pb" VERBOSE="$(VERBOSE)"

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
opencl_example_container.sif: alpha_submission/opencl_example/opencl_example_container.def
	apptainer build $@ $<

.PHONY: run-opencl-example
run-opencl-example: opencl_example_container.sif
	apptainer run $(APPTAINER_RUN_ARGS) $<

#### END EXAMPLE RECIPES

# Tell make to not treat routed results as intermediate files (which would get deleted)
.PRECIOUS: %_$(ROUTER).phys
