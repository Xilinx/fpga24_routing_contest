/*
 * Copyright (C) 2024, Advanced Micro Devices, Inc.  All rights reserved.
 *
 * Author: Eddie Hung, AMD
 *
 * SPDX-License-Identifier: MIT
 *
 */

package com.xilinx.fpga24_routing_contest;

import com.xilinx.rapidwright.design.Design;
import com.xilinx.rapidwright.design.compare.DesignComparator;
import com.xilinx.rapidwright.interchange.PhysNetlistReader;

import java.io.IOException;

public class DiffPhysNetlist {
    public static void main(String[] args) throws IOException {
        if (args.length != 2) {
            System.err.println("USAGE: <routed.phys> <unrouted.phys>");
            return;
        }

        // Disable verbose Physical Netlist checks
        PhysNetlistReader.CHECK_CONSTANT_ROUTING_AND_NET_NAMING = false;
        PhysNetlistReader.CHECK_AND_CREATE_LOGICAL_CELL_IF_NOT_PRESENT = false;
        PhysNetlistReader.VALIDATE_MACROS_PLACED_FULLY = false;
        PhysNetlistReader.CHECK_MACROS_CONSISTENT = false;

        // Read the routed and unrouted Physical Netlists
        Design routedDesign = PhysNetlistReader.readPhysNetlist(args[0]);
        Design unroutedDesign = PhysNetlistReader.readPhysNetlist(args[1]);

        DesignComparator dc = new DesignComparator();
        // Only compare PIPs on static and clock nets
        dc.setComparePIPs((net) -> net.isStaticNet() || net.isClockNet());
        int numDiffs = dc.compareDesigns(unroutedDesign, routedDesign);
        if (numDiffs == 0) {
            System.out.println("INFO: No differences found between routed and unrouted netlists");
        } else {
            dc.printDiffReport(System.out);
        }

        System.exit(numDiffs == 0 ? 0 : 1);
    }
}

