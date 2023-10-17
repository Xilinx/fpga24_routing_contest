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
import com.xilinx.rapidwright.design.DesignTools;
import com.xilinx.rapidwright.design.SitePinInst;
import com.xilinx.rapidwright.design.Net;
import com.xilinx.rapidwright.interchange.LogNetlistWriter;
import com.xilinx.rapidwright.interchange.PhysNetlistWriter;
import com.xilinx.rapidwright.util.FileTools;

import java.io.IOException;

public class DcpToFPGAIF {
    public static void main(String[] args) throws IOException {
        if (args.length != 3) {
            System.err.println("USAGE: <input.dcp> <output.netlist> <output.phys>");
            System.exit(1);
        }

        Design design = Design.readCheckpoint(args[0]);

        // Even though the design is fully placed-and-routed, still need to call this to
        // infer any unrouted SitePinInst-s from nets with hierarchical ports --- not for
        // routing to since they are out-of-context ports --- but so that it's clear to
        // other nets that those nodes are off limits
        DesignTools.createMissingSitePinInsts(design);

        for (Net net : design.getNets()) {
            if (net.isStaticNet() || net.isClockNet()) {
                continue;
            }

            // Where a net only has a single source, try and discover if an alternate
            // source exists
	    SitePinInst altSource = net.getAlternateSource();
	    if (altSource == null) {
	            altSource = DesignTools.getLegalAlternativeOutputPin(net);
	            if (altSource != null) {
                            net.addPin(altSource);
                            // Commit this pin to the SiteInst
                            altSource.getSiteInst().addPin(altSource);
                            DesignTools.routeAlternativeOutputSitePin(net, altSource);
	            }
	    }

            net.unroute();
        }

        PhysNetlistWriter.writePhysNetlist(design, args[2]);

        // Write logical netlist after physical since it collapses macros
        LogNetlistWriter.writeLogNetlist(design.getNetlist(), args[1]);
    }
}

