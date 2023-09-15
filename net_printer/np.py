# Copyright (C) 2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author: Zak Nafziger, AMD
#
# SPDX-License-Identifier: MIT
#

import os
import sys
import capnp
import gzip
import argparse

# Add the interchange/ subdirectory from fpga-interchange-schema submodule at the root
# of the repository to Python's sys.path so that capnp can search it from *.capnp files
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(THIS_DIR, '..','fpga-interchange-schema','interchange'))
import PhysicalNetlist_capnp

def read_phys_netlist(phys_name):
    phys = None
    with open(phys_name, 'rb') as f:
        magic = f.read(2)
        f.seek(0)
        if magic == b'\x1f\x8b':
            f = gzip.GzipFile(fileobj=f)
        with PhysicalNetlist_capnp.PhysNetlist.from_bytes(f.read(), traversal_limit_in_words=sys.maxsize, nesting_limit=2**20) as phys_netlist:
            phys = phys_netlist
    return phys

def net_printer(phys, route_branch, first, trunk=False):
    prefix = "    "
    if first:
        if trunk:
            prefix += "[{"
        else:
            prefix += " {"
    else:
            prefix += "  "
    prefix += "   "
    if len(route_branch.branches) == 0:
        if trunk:
            prefix += "}] "
        else:
            prefix += "}  "
    else:
        prefix += "   "
    print(prefix, end='')

    sl = phys.strList
    rs = route_branch.routeSegment
    w = rs.which()
    print("%-7s " % w, end='')
    if w == 'belPin':
        print(sl[rs.belPin.site], sl[rs.belPin.bel], sl[rs.belPin.pin])
    elif w == 'sitePin':
        print(sl[rs.sitePin.site], sl[rs.sitePin.pin])
    elif w == 'pip':
        print(sl[rs.pip.tile], sl[rs.pip.wire0], sl[rs.pip.wire1], rs.pip.forward, rs.pip.isFixed)
    elif w == 'sitePIP':
        print(sl[rs.sitePIP.site], sl[rs.sitePIP.bel], sl[rs.sitePIP.pin], rs.sitePIP.isFixed)

    if len(route_branch.branches) >= 2:
        for b in range(len(route_branch.branches))[1:]:
            net_printer(phys, route_branch.branches[b], True)
    if len(route_branch.branches) > 0:
        net_printer(phys, route_branch.branches[0], False, trunk)

def print_net(phys, to_print):
    first = True
    for n in phys.physNets:
        if phys.strList[n.name] in to_print:
            if first:
                print("============================================================")
                first = False
            print("Route tree for net:", phys.strList[n.name])
            for i in range(len(n.sources)):
                print()
                print("    Source:", i)
                net_printer(phys, n.sources[i], True, True)
            for i in range(len(n.stubs)):
                print()
                print("    Stub:", i)
                net_printer(phys, n.stubs[i], True, True)
            print("============================================================")

def main():
    parser = argparse.ArgumentParser(
        prog="np",
        description="Print nets as they appear in the physical netlist file")

    parser.add_argument('physical_netlist', type=str, help="physical netlist to process")
    parser.add_argument('nets', type=str, nargs='+', help="list of net names to print")

    args = parser.parse_args()

    phys = read_phys_netlist(args.physical_netlist)
    print_net(phys, args.nets)

if __name__ == "__main__":
    main()
