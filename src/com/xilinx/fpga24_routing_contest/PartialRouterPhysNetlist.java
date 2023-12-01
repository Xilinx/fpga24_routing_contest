/*
 * Copyright (C) 2023, Advanced Micro Devices, Inc.  All rights reserved.
 *
 * Author: Eddie Hung, AMD
 *
 * SPDX-License-Identifier: MIT
 *
 */

package com.xilinx.fpga24_routing_contest;

import com.xilinx.rapidwright.design.Design;
import com.xilinx.rapidwright.design.Net;
import com.xilinx.rapidwright.design.SitePinInst;
import com.xilinx.rapidwright.interchange.PhysNetlistReader;
import com.xilinx.rapidwright.interchange.PhysNetlistWriter;
import com.xilinx.rapidwright.rwroute.PartialRouter;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class PartialRouterPhysNetlist {
    public static void main(String[] args) throws IOException {
        if (args.length != 2) {
            System.err.println("USAGE: <input.phys> <output.phys>");
            return;
        }

        // Disable verbose Physical Netlist checks
        PhysNetlistReader.CHECK_CONSTANT_ROUTING_AND_NET_NAMING = false;
        PhysNetlistReader.CHECK_AND_CREATE_LOGICAL_CELL_IF_NOT_PRESENT = false;
        PhysNetlistReader.VALIDATE_MACROS_PLACED_FULLY = false;
        PhysNetlistReader.CHECK_MACROS_CONSISTENT = false;

        // Read the Physical Netlist
        Design design = PhysNetlistReader.readPhysNetlist(args[0]);

        // Apply PartialRouter (subclass of RWRoute)
        List<SitePinInst> pinsToRoute = new ArrayList<>();
        for (Net net : design.getNets()) {
            if (net.getSource() == null && !net.isStaticNet()) {
                // Source-less nets may exist since this is an out-of-context design
                continue;
            }
            if (!net.hasPIPs()) {
                // Route only nets with no PIPs
                pinsToRoute.addAll(net.getSinkPins());
            }
        }

        String[] routerArgs = new String[] {
                // Same options as PartialRouter.routeDesignPartialNonTimingDriven()
                "--fixBoundingBox",
                "--useUTurnNodes",
                "--nonTimingDriven",
                "--verbose",
                // These options are set to their default value, a subset of which are duplicated here
                // to ease modification; full documentation is available in RWRouteConfig.java
                "--maxIterations", "100",
                "--wirelengthWeight", "0.8",
                "--initialPresentCongestionFactor", "0.5",
                "--presentCongestionMultiplier", "2",
                "--historicalCongestionFactor", "1",
                // Optionally, enable LUT pin swapping where all inputs of a LUT are considered
                // to be equivalent
                "--lutPinSwapping",
        };

        if (Arrays.asList(routerArgs).contains("--lutPinSwapping")) {
            // Ask RWRoute not to perform any intra-site routing updates to reflect
            // any LUT pin swapping that occurs during routing, to fulfill the
            // contest requirement that only PIPs may be modified.
            // Instead, this updates is deferred until CheckPhysNetlist.
            System.setProperty("rapidwright.rwroute.lutPinSwapping.deferIntraSiteRoutingUpdates", "true");

            // Ask PhysNetlistWriter to simulate LUT pin swapping such that any
            // routes that service an incorrect LUT input site pin are allowed to have
            // a fake branch to the correct site pin on the same LUT for the
            // purposes of simulating (prior to applying deferred updates) a fully
            // routed net.
            // Such fake branches are discarded by CheckPhysNetlist and does not
            // affect the deferred update process.
            System.setProperty("rapidwright.physNetlistWriter.simulateSwappedLutPins", "true");
        }

        boolean softPreserve = false;
        PartialRouter.routeDesignWithUserDefinedArguments(design, routerArgs,
                pinsToRoute, softPreserve);

        // Write routed result to new Physical Netlist
        PhysNetlistWriter.writePhysNetlist(design, args[1]);
    }
}

