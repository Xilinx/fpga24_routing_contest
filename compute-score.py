# Copyright (C) 2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author: Eddie Hung, AMD
#
# SPDX-License-Identifier: MIT
#

import sys
import re

reWallClockSeconds = re.compile(r'Wall-clock time \(sec\): ([0-9.]+)')

total_rt = 0
total_cpw = 0
rt_format = '{:.2f}'
cpw_format = '{:.0f}'
results = []
results.append(('Benchmark', 'Pass', 'Wall Clock (sec)', 'Critical-Path Wirelength'))
for benchmark in sys.argv[1:]:
    runtime = float('inf')
    cpw = float('inf')
    check = True
    try:
        with open(benchmark + '.check') as fp:
            if fp.readline().rstrip() != 'PASS':
                check = False
        with open(benchmark + '.phys.log') as fp:
            last = fp.readlines()[-1].rstrip()
        m = reWallClockSeconds.match(last)
        if not m:
            continue
        runtime = float(m.group(1))
        with open(benchmark + '.wirelength') as fp:
            lines = fp.readlines()
            for l in lines:
                if 'Wirelength: ' in l:
                    cpw = float(l.split()[-1])
    finally:
        results.append((benchmark,check,rt_format.format(runtime),cpw_format.format(cpw)))
        total_rt += runtime
        total_cpw += cpw

results.append(('Total', '', rt_format.format(total_rt), cpw_format.format(total_cpw)))

column_widths = [0]*len(results[0])
for row in results:
    for index, item in enumerate(row):
        if len(str(item)) > column_widths[index]:
            column_widths[index] = len(str(item))

sep = '|'
header_format_str = sep
body_format_str = sep
horiz = '+'
for index, width in enumerate(column_widths):
    header_format_str += ' %-' + str(width) + 's ' + sep
    horiz += '-' + '-'*width + '-' + '+'
    if index == 0:
        body_format_str += ' %-' + str(width) + 's ' + sep
    else:
        body_format_str += ' %' + str(width) + 's ' + sep

print(horiz)
print(header_format_str % results[0])
print(horiz)
for row in results[1:-1]:
    print(body_format_str % row)
print(horiz)
print(body_format_str % results[-1])
print(horiz)
