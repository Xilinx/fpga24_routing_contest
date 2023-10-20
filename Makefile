# Copyright (C) 2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author: Eddie Hung, AMD
#
# SPDX-License-Identifier: MIT
#

# List of all benchmarks (default to all)
BENCHMARKS ?= vtr_mcml			\
              rosetta_fd		\
              koios_dla_like_large 	\
              ispd16_example2 		\
              boom_soc

BENCHMARKS_URL = https://github.com/Xilinx/fpga24_routing_contest/releases/latest/download/benchmarks.tar.gz

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
    SHELL := /bin/bash -o pipefail
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


# Default recipe: route and score all given benchmarks
.PHONY: run-$(ROUTER)
run-$(ROUTER): score-$(ROUTER)

# Use Gradle to compile Java source code in this repository
# as well as the RapidWright repository
.PHONY: compile-java
compile-java:
	./gradlew compileJava

.PHONY: install-python-deps
install-python-deps:
	pip install -q -r requirements.txt

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
        elif [[ "$(CHECK_PHYS_NETLIST_MOCK_PASS)" == "true" && -f "$(patsubst %.check,%.dcp,$@)" ]]; then \
            echo "::warning file=$@::CheckPhysNetlist returned FAIL but CHECK_PHYS_NETLIST_MOCK_PASS is set"; \
            echo "PASS" > $@; \
        else \
            echo "FAIL" > $@; \
        fi

%_$(ROUTER).wirelength: %_$(ROUTER).phys | install-python-deps
	python3 wirelength_analyzer/wa.py $< $(call log_and_or_display,$@)

.PHONY: score-$(ROUTER)
score-$(ROUTER): $(addsuffix _$(ROUTER).wirelength, $(BENCHMARKS)) $(addsuffix _$(ROUTER).check, $(BENCHMARKS))
	python ./compute-score.py $(addsuffix _$(ROUTER), $(BENCHMARKS))

.PRECIOUS: %.device
%.device: | compile-java
	RapidWright/bin/rapidwright DeviceResourcesExample $*

.PHONY: net_printer
setup-net_printer: | install-python-deps fpga-interchange-schema/interchange/capnp/java.capnp

clean:
	rm -f *.{phys,check,wirelength}*

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

# Tell make to not treat routed results as intermediate files (which would get deleted)
.PRECIOUS: %_$(ROUTER).phys
