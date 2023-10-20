# Copyright (C) 2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author: Zak Nafziger, AMD
#
# SPDX-License-Identifier: MIT
#

ASSETS_URL = https://github.com/zakn-amd/fpga24_routing_contest/releases/download/test_assets_v1/test_assets.tar.gz
ASSETS_DIR = test/data
.PHONY: get-test-data
get-test-data:
	mkdir -p $(ASSETS_DIR)
	curl -L $(ASSETS_URL) | tar -xzv -C $(ASSETS_DIR)

.PHONY: run-unittests
run-unittests: get-test-data
	python3 -m unittest discover -s test
