# Copyright (C) 2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author: Eddie Hung, AMD
#
# SPDX-License-Identifier: MIT
#

import sys
import re

reWallClockSeconds = re.compile(r'Wall-clock time \(sec\): ([0-9.]+)')

print('%-30s %10s' % ('Benchmark','Wall Clock (sec)'))
print('-----------------------------------------')

total = 0
for benchmark in sys.argv[1:]:
	value = float('inf')
	try:
		with open(benchmark + '.check') as fp:
			if fp.readline().rstrip() != 'PASS':
				continue
		with open(benchmark + '.phys.log') as fp:
			last = fp.readlines()[-1].rstrip()
		m = reWallClockSeconds.match(last)
		if not m:
			continue
		value = m.group(1)
	finally:
		total += float(value)
		print('%-30s %10s' % (benchmark,value))
print('-----------------------------------------')
print('%-30s %10.2f' % ('Total',total))
