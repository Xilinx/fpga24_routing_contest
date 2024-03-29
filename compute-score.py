# Copyright (C) 2023-2024, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author: Eddie Hung, AMD
#
# SPDX-License-Identifier: MIT
#

import sys
import re
import argparse
from scoring_formula.scoring_formula import score_benchmark_results

def route_result(checkfile):
    """
    Read the result of CheckPhysNetlist.

    Args:
        checkfile: the name of the file containing the output of
        CheckPhysNetlist
    Returns:
        True if the checkfile has the result 'PASS' False otherwise
    """
    try:
        with open(checkfile) as fp:
            return fp.readline().rstrip() == 'PASS'
    except FileNotFoundError:
        return False

def runtime_results(physlogfile):
    """
    Read the runtime of the router being scored.

    Args:
        physlogfile: the name of the Physical Netlist log file
    Returns:
        the wall clock and user-cpu runtimes in seconds as floating
        point numbers if available.
        Floating point infinity otherwise.
    """
    reWallClockSeconds = re.compile(r'Wall-clock time \(sec\): ([0-9.]+)')
    reUserCpuSeconds = re.compile(r'User-CPU time \(sec\): ([0-9.]+)')
    result = [float('inf')] * 2
    try:
        with open(physlogfile) as fp:
            last2,last1 = fp.readlines()[-2:]
        m2 = reWallClockSeconds.match(last2)
        if m2:
            result[0] = float(m2.group(1))
            m1 = reUserCpuSeconds.match(last1)
            if m1:
                result[1] = float(m1.group(1))
    except FileNotFoundError:
        pass
    return result

def wirelength_result(wirelengthfile):
    """
    Read the Critical-Path Wirelength of the routed Physical Netlist.

    Args:
        wirelengthfile: the name of the wirelength file generated by running
        wa.py on the final Physical Netlist
    Returns:
        The Critical-Path Wirelength as a floating point number if available.
        Floating point infinity otherwise.
    """
    try:
        with open(wirelengthfile) as fp:
            lines = fp.readlines()
            for l in lines:
                if 'Wirelength: ' in l:
                    return float(l.split()[-1])
    except FileNotFoundError:
        pass
    return float('inf')

def print_results_table(results):
    """
    Given a list of results print a nice table.

    Args:
        results: a list of tuples. Each tuple is assumed to be the same length.
        Items in each tuple are placed in individual columns
    """
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
    for row in results[1:]:
        print(body_format_str % row)
    print(horiz)

def main():
    """
    Main entry point to compute-score. This program reads the `.check`,
    `.phys.log` and `.wirelength` files associated with each of the benchmarks
    passed on the commandline. Based on the results collected from these files
    a score for each benchmark is computed according the the contest scoring
    rules. Finally a table showing each benchmark, the scoring data and the
    final score is printed.
    """
    parser = argparse.ArgumentParser(
        prog="compute-score",
        description="Compute the score achieved on a set of benchmarks by a router",
    )
    parser.add_argument('benchmarks',
                        metavar="<benchmark name>_<router name>",
                        type=str,
                        nargs='+',
                        help="List of data file prefixes")
    args = parser.parse_args()

    rt_format = '{:.2f}'
    cpw_format = '{:.0f}'
    score_format = '{:.2f}'
    results = [('Benchmark', 'Pass', 'User CPU (sec)', 'Wall Clock (sec)', 'Critical-Path Wirelength', 'Score')]
    for benchmark in args.benchmarks:
        check = route_result(benchmark + '.check')
        (walltime,usertime) = runtime_results(benchmark + '.phys.log')
        cpw = wirelength_result(benchmark + '.wirelength')
        score = score_benchmark_results(check, walltime, cpw)
        results.append((benchmark,check,rt_format.format(usertime),rt_format.format(walltime),cpw_format.format(cpw),score_format.format(score)))

    print_results_table(results)

if __name__ == '__main__':
    main()
