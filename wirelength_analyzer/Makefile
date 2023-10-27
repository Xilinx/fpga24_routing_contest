# Copyright (C) 2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author: Zak Nafziger, AMD
#
# SPDX-License-Identifier: MIT
#

ASSETS_URL = https://github.com/Xilinx/fpga24_routing_contest/releases/latest/download/test_assets.tar.gz
ASSETS_DIR = test/data
.PHONY: get-test-data
get-test-data:
	mkdir -p $(ASSETS_DIR)
	curl -L $(ASSETS_URL) | tar -xzv -C $(ASSETS_DIR)

.PHONY: run-unittests
run-unittests: get-test-data
	python3 -m unittest discover -s test -v
