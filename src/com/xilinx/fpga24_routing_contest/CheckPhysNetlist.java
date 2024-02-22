/*
 * Copyright (C) 2023-2024, Advanced Micro Devices, Inc.  All rights reserved.
 *
 * Author: Eddie Hung, AMD
 *
 * SPDX-License-Identifier: MIT
 *
 */

package com.xilinx.fpga24_routing_contest;

import com.xilinx.rapidwright.design.Design;
import com.xilinx.rapidwright.design.compare.DesignComparator;
import com.xilinx.rapidwright.design.tools.LUTTools;
import com.xilinx.rapidwright.edif.EDIFNetlist;
import com.xilinx.rapidwright.edif.EDIFTools;
import com.xilinx.rapidwright.interchange.LogNetlistReader;
import com.xilinx.rapidwright.interchange.PhysNetlistReader;
import com.xilinx.rapidwright.util.FileTools;
import com.xilinx.rapidwright.util.ReportRouteStatusResult;
import com.xilinx.rapidwright.util.VivadoTools;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.lang.InterruptedException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpRequest.BodyPublishers;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.zip.Deflater;
import java.util.zip.ZipOutputStream;
import java.util.zip.ZipEntry;

public class CheckPhysNetlist {
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 3) {
            System.err.println("USAGE: <input.netlist> <routed.phys> <unrouted.phys>");
            System.exit(1);
        }

        // Disable verbose Physical Netlist checks
        PhysNetlistReader.CHECK_CONSTANT_ROUTING_AND_NET_NAMING = false;
        PhysNetlistReader.CHECK_AND_CREATE_LOGICAL_CELL_IF_NOT_PRESENT = false;
        PhysNetlistReader.VALIDATE_MACROS_PLACED_FULLY = false;
        PhysNetlistReader.CHECK_MACROS_CONSISTENT = false;

        // Read the routed and unrouted Physical Netlists
        Design routedDesign = PhysNetlistReader.readPhysNetlist(args[1]);
        int numDiffs = 0;
        if ("true".equals(System.getenv("CHECK_PHYS_NETLIST_DIFF_MOCK_RESULT"))) {
            System.out.println("::warning file=" + args[1] + "::CheckPhysNetlist's DesignComparator not run because CHECK_PHYS_NETLIST_DIFF_MOCK_RESULT is set");
        } else {
            Design unroutedDesign = PhysNetlistReader.readPhysNetlist(args[2]);

            DesignComparator dc = new DesignComparator();
            // Only compare PIPs on static and clock nets
            dc.setComparePIPs((net) -> net.isStaticNet() || net.isClockNet());
            numDiffs = dc.compareDesigns(unroutedDesign, routedDesign);
        }
        if (numDiffs == 0) {
            System.out.println("INFO: No differences found between routed and unrouted netlists");
        } else {
            System.err.println("ERROR: Detected " + numDiffs + " differences between " + args[1] + " and " + args[2]);
        }

        // Read the Logical Netlist
        EDIFNetlist netlist = LogNetlistReader.readLogNetlist(args[0]);

        // Combine Physical Netlist with Logical
        routedDesign.setNetlist(netlist);
        routedDesign.setName(netlist.getName());

        // Add encrypted EDIF cells to the design if found
        Path ednDirectory = Paths.get(args[0] + ".edn");
        if (Files.exists(ednDirectory) && Files.isDirectory(ednDirectory)) {
            List<String> encryptedCells = new ArrayList<>();
            for (String fileName : new File(ednDirectory.toString()).list()) {
                encryptedCells.add(ednDirectory.resolve(fileName).toAbsolutePath().toString());
            }
            netlist.addEncryptedCells(encryptedCells);
        }

        // Examine the design routing and perform any necessary LUT pin swaps
        LUTTools.swapLutPinsFromPIPs(routedDesign);

        // Write design to Vivado Design Checkpoint (DCP)
        Path outputDcp = Paths.get(FileTools.removeFileExtension(args[1]) + ".dcp");
        routedDesign.writeCheckpoint(outputDcp);

        // Call Vivado's `report_route_status` command on this DCP
        ReportRouteStatusResult rrs = null;
        String reportRouteStatusUrl = System.getenv("REPORT_ROUTE_STATUS_URL");
        if (reportRouteStatusUrl == null || reportRouteStatusUrl.isEmpty()) {
            // Call local Vivado
            if (!FileTools.isVivadoOnPath()) {
                System.err.println("ERROR: `vivado` not detected on $PATH");
                System.exit(1);
            }

            List<String> encryptedCells = netlist.getEncryptedCells();
            boolean encrypted = encryptedCells != null && !encryptedCells.isEmpty();
            rrs = VivadoTools.reportRouteStatus(outputDcp, encrypted);
        } else {
            // Upload DCP/ZIP-with-encrpyted-cells to a remote URL
            Path uploadFile = outputDcp;
            if (!netlist.getEncryptedCells().isEmpty()) {
                // For designs with encrypted cells, create and upload a zip file
                // containing those encrpyted cells and the *_load.tcl script along
                // with the DCP 
                uploadFile = Paths.get(outputDcp.toString() + ".zip");
                reportRouteStatusUrl += "-zip";
                try (FileOutputStream fos = new FileOutputStream(uploadFile.toString());
                        ZipOutputStream zos = new ZipOutputStream(fos)) {
                    zos.setLevel(Deflater.NO_COMPRESSION);
                    zos.putNextEntry(new ZipEntry(outputDcp.toString()));
                    Files.copy(outputDcp, zos);
                    for (String fileName : netlist.getEncryptedCells()) {
                        zos.putNextEntry(new ZipEntry(fileName));
                        Files.copy(Paths.get(fileName), zos);
                    }
                    Path loadTclPath = FileTools.replaceExtension(outputDcp, EDIFTools.LOAD_TCL_SUFFIX);
                    zos.putNextEntry(new ZipEntry(loadTclPath.toString()));
                    Files.copy(loadTclPath, zos);
                }
            }

            System.out.println("Uploading " + uploadFile + " ...");
            HttpClient client = HttpClient.newHttpClient();

            String reportRouteStatusAuth = System.getenv("REPORT_ROUTE_STATUS_AUTH");
            String auth = "Basic " + Base64.getEncoder().encodeToString(reportRouteStatusAuth.getBytes());

            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(reportRouteStatusUrl))
                .PUT(BodyPublishers.ofFile(uploadFile))
                .setHeader("Authorization", auth)
                .build();

            HttpResponse<InputStream> response = client.send(request, HttpResponse.BodyHandlers.ofInputStream());
            System.out.println("Status code: " + response.statusCode());
            List<String> lines = new ArrayList<>();
            System.out.println("Response:");
            try (InputStream is = response.body();
                 BufferedReader br = new BufferedReader(new InputStreamReader(is))) {
                String line;
                while ((line = br.readLine()) != null) {
                    System.out.println(line);
                    lines.add(line);
                }
                System.out.println("<EOF>");
            }
            rrs = new ReportRouteStatusResult(lines);
        }

        // Exit code 0 only if Vivado reported that it was fully routed
        System.exit(numDiffs == 0 && rrs.logicalNets > 0 && rrs.isFullyRouted() ? 0 : 1);
    }
}

