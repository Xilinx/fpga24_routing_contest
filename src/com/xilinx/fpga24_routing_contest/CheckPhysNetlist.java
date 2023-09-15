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
import com.xilinx.rapidwright.edif.EDIFNetlist;
import com.xilinx.rapidwright.interchange.LogNetlistReader;
import com.xilinx.rapidwright.interchange.PhysNetlistReader;
import com.xilinx.rapidwright.util.FileTools;
import com.xilinx.rapidwright.util.ReportRouteStatusResult;
import com.xilinx.rapidwright.util.VivadoTools;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

public class CheckPhysNetlist {
    public static void main(String[] args) throws IOException {
        if (args.length != 2) {
            System.err.println("USAGE: <input.netlist> <input.phys>");
            return;
        }

        // Disable verbose Physical Netlist checks
        PhysNetlistReader.CHECK_CONSTANT_ROUTING_AND_NET_NAMING = false;
        PhysNetlistReader.CHECK_AND_CREATE_LOGICAL_CELL_IF_NOT_PRESENT = false;
        PhysNetlistReader.VALIDATE_MACROS_PLACED_FULLY = false;
        PhysNetlistReader.CHECK_MACROS_CONSISTENT = false;


        // Read the Logical Netlist
        EDIFNetlist netlist = LogNetlistReader.readLogNetlist(args[0]);

        // Read the Physical Netlist
        Design design = PhysNetlistReader.readPhysNetlist(args[1]);

        // Combine Physical Netlist with Logical
        design.setNetlist(netlist);
        design.setName(netlist.getName());

        // Add encrypted EDIF cells to the design if found
        Path ednDirectory = Paths.get(args[0] + ".edn");
        if (Files.exists(ednDirectory) && Files.isDirectory(ednDirectory)) {
            List<String> encryptedCells = new ArrayList<>();
            for (String fileName : new File(ednDirectory.toString()).list()) {
                encryptedCells.add(ednDirectory.resolve(fileName).toAbsolutePath().toString());
            }
            netlist.addEncryptedCells(encryptedCells);
        }

        // Write design to Vivado Design Checkpoint (DCP)
        Path outputDcp = Paths.get(FileTools.removeFileExtension(args[1]) + ".dcp");
        design.writeCheckpoint(outputDcp);

        // Call Vivado's `report_route_status` command on this DCP
        List<String> encryptedCells = netlist.getEncryptedCells();
        boolean encrypted = encryptedCells != null && !encryptedCells.isEmpty();
        ReportRouteStatusResult rrs = VivadoTools.reportRouteStatus(outputDcp, encrypted);

        // Exit code 0 only if Vivado reported that it was fully routed
        System.exit(rrs.isFullyRouted() ? 0 : 1);
    }
}

