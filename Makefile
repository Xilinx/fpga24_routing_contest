# Copyright (C) 2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author: Eddie Hung, AMD
#
# SPDX-License-Identifier: MIT
#

# List of all download-benchmarks (default to all)
BENCHMARKS ?= boom_soc 			\
              ispd16_example2 		\
              koios_dla_like_large 	\
              rosetta_fd 		\
              vtr_mcml

BENCHMARKS_URL = https://github.com/Xilinx/fpga24_routing_contest/releases/download/v1.0/benchmarks.tar.gz

# Choice of router (default to rwroute)
# (other supported values: nxroute-poc)
ROUTER ?= rwroute

# Make /usr/bin/time only print out wall-clock time in seconds
export TIME=Wall-clock time (sec): %e

# Default recipe: route and score all given download-benchmarks
.PHONY: run-$(ROUTER)
run-$(ROUTER): score-$(ROUTER)

# Use Gradle to compile Java source code in this repository
# as well as the RapidWright repository
.PHONY: compile-java
compile-java:
	./gradlew compileJava

.PHONY: nxroute-deps
nxroute-deps:
	pip install -q -r networkx-proof-of-concept-router/requirements.txt

# Download and unpack all benchmarks
.PHONY: download-benchmarks
download-benchmarks:
	curl -L $(BENCHMARKS_URL) | tar -xzv

.PRECIOUS: %_unrouted.phys %.netlist
%_unrouted.phys %.netlist:
	$(MAKE) download-benchmarks

# Since the FPGA Interchange Schema is set up for generating Java code,
# ensure that the Capnp Java package is present
fpga-interchange-schema/interchange/capnp/java.capnp:
	mkdir -p $(@D)
	wget https://raw.githubusercontent.com/capnproto/capnproto-java/master/compiler/src/main/schema/capnp/java.capnp -O $@

# Gradle is used to invoke the CheckPhysNetlist class' main method with arguments
# $^ (%.netlist and %_rwroute.phys), and redirecting all output to $@.log (%_rwroute.check.log).
# The exit code of Gradle determines if 'PASS' or 'FAIL' is written to $@ (%_rwroute.check)
%_$(ROUTER).check: %.netlist %_$(ROUTER).phys | compile-java
	( ( ./gradlew -Dmain=com.xilinx.fpga24_routing_contest.CheckPhysNetlist :run --args='$^' &> $@.log && echo "PASS" ) || echo "FAIL") > $@

.PHONY: score-$(ROUTER)
score-$(ROUTER): $(addsuffix _$(ROUTER).check, $(BENCHMARKS))
	python ./compute-score.py $(addsuffix _$(ROUTER), $(BENCHMARKS))

.PRECIOUS: %.device
%.device: | compile-java
	RapidWright/bin/rapidwright DeviceResourcesExample $*

clean:
	rm -f *.{phys,check}*

distclean: clean
	rm -rf *.device *_unrouted.phys *.netlist*


#### BEGIN ROUTER RECIPES

## RWROUTE
# _JAVA_OPTIONS="-Xms32736m -Xmx32736m" sets the initial and maximum heap size of the JVM to be ~32GB
# /usr/bin/time is used to measure the wall clock time
# Gradle is used to invoke the PartialRouterPhysNetlist class' main method with arguments
# $< (%_unrouted.phys) and $@ (%_rwroute.phys), and redirecting all output into %_rwroute.phys.log
%_rwroute.phys: %_unrouted.phys | compile-java
	_JAVA_OPTIONS="-Xms32736m -Xmx32736m" /usr/bin/time ./gradlew -Dmain=com.xilinx.fpga24_routing_contest.PartialRouterPhysNetlist :run --args='$< $@' &> $@.log

## NXROUTE-POC
%_nxroute-poc.phys: %_unrouted.phys xcvu3p.device | nxroute-deps fpga-interchange-schema/interchange/capnp/java.capnp
	/usr/bin/time python3 networkx-proof-of-concept-router/nxroute-poc.py $< $@ &> $@.log

## EXAMPLEROUTE
# %_exampleroute.phys: %_unrouted.phys | fpga-interchange-schema/interchange/capnp/java.capnp
# 	/usr/bin/time <custom router here> $< $@ &> $@.log

#### END ROUTER RECIPES

# Tell make to not treat routed results as intermediate files (which would get deleted)
.PRECIOUS: %_$(ROUTER).phys
