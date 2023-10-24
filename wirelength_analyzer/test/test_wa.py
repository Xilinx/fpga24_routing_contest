# Copyright (C) 2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author: Zak Nafziger, AMD
#
# SPDX-License-Identifier: MIT
#

import os
import unittest
from wa import WirelengthAnalyzer
from test.parse_vivado_route_tree import ParseVivadoRouteTree
from test.find_vivado_critical_path_in_wirelength_graph import FindVivadoCriticalPathInWirelengthGraph

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

class TestWirelengthAnalyzer(unittest.TestCase):
    """
    This class provides some test cases for the wirelength analyzer module.
    """

    benchmarks = [
        'vtr_mcml_rwroute',
        'rosetta_fd_rwroute',
    ]

    def data_path(self, d):
        """
        return a path to file in the test data directory

        Args:
            d: test datafile name
        Returns:
            absolute path to test datafile
        """
        return os.path.join(THIS_DIR, 'data/wirelength_analyzer', d)

    def test_lsn(self):
        """
        Test that the Longest Single Net found in a physical netlist exists
        in a corresponding Vivado route tree

        The basic idea is to compare a path found by the wirelength analyzer
        module to the Vivado route tree rooted at the same point. If the path
        found by the wirelength anaylzer module is found in the vivado route
        tree then we assume that th wirelength analyzer module is loading
        routed designs correctly, and properly interpreting its internal graph.
        The below flowchart describes the process:

        routed DCP ---> RapidWright ---> routed physical netlist (.phys) ---> wirelength analyzer
          |                                                                             |
          +---------> Vivado ---> route tree (.txt)                                     |
                                         |                                              |
                                         +------------------------+---------------------+
                                                                  |
                                                                  V
                                                         comparison (these tests)

        Note that the route trees are not generated automatically (i.e. these
        tests don't depend on Vivado) instead they are pre-generated and stored
        as external test inputs.
        """
        data = [(self.data_path(x+'.phys'), self.data_path(x+'_lsn.txt'), x) for x in self.benchmarks]
        for config in data:
            with self.subTest(config = config):
                print(config)
                self.compare_lsn(config[0], config[1])

    def compare_lsn(self, phys_fname, vrt_fname):
        """
        Ensure that the Longest Single Net (lsn) found in the physical
        netlist exists in the Vivado route tree (vrt) rooted at the same
        sitePin

        Args:
            phys_fname: filename of a placed and routed physical netlist
            vrt_fname: filename of the Vivado route tree, generated with:
            report_route_status -of_object <net_name> -file <vrt_fname>
        """
        # build a graph of the Vivado route tree
        vrt = ParseVivadoRouteTree(vrt_fname)
        vrt.build_tree_from_net()

        # compute the Longest Single Net
        wa = WirelengthAnalyzer(phys_fname, 0)
        wa.find_lsn()

        # in single net mode the wirelength analyzer should return a path with
        # exactly one edge
        self.assertTrue(len(wa.lsn) == 2, msg="Found single net path with multiple edges")

        # we then expand this edge to get the detailed routing along the lsn.
        # note we omit the routeSegment at the beginning and the end of the
        # lsn, however the vrt only contains intersite routing, and we assume
        # a well formed lsn should have intrasite routeSegments at either end
        lsn = wa.expand_edge(wa.lsn[0], wa.lsn[1])

        # for each edge in the Longest Single Net found in the physical
        # netlist, ensure that the edge exists in the Vivado route tree
        matched_edges = []
        print("List of matching route segments:")
        print("Wirelength Analyzer == Vivado Route Tree")
        for lsn_seg in lsn:
            lsn_seg_txt = wa.format_segment(lsn_seg).split()
            if lsn_seg_txt[0] == 'pip': # only check pips
                found_edge = False
                for vrt_edge in vrt.G.edges:
                    vrt_seg = vrt.G.get_edge_data(*vrt_edge)['segment']
                    if lsn_seg_txt[1:4] == [*vrt_seg]:
                        matched_edges.append(vrt_edge)
                        found_edge = True
                        print(' '.join(lsn_seg_txt[1:4]), '==', ' '.join(vrt_seg))
                        break
                self.assertTrue(found_edge, msg=wa.format_segment(lsn_seg))

        self.assertTrue(len(matched_edges) != 0, msg="No common path found")

        # ensure that the edges found in the Vivado route tree form a path
        last_node = None
        for e in matched_edges:
            if last_node != None:
                self.assertEqual(e[0], last_node, msg=e[0] + " != " + last_node)
            last_node = e[1]

    def test_crit_path(self):
        """
        Check to see if the critical path found by Vivado exists in the graph
        created by the wirelength analyzer.

        Most of the functionality of this test is in
        FindVivadoCriticalPathInWirelengthGraph
        """
        data = [(self.data_path(x+'_timing.txt'), self.data_path(x+'.phys'), x) for x in self.benchmarks]

        for config in data:
            with self.subTest(config = config):
                test = FindVivadoCriticalPathInWirelengthGraph(config[0], config[1], config[2])
                self.assertTrue(test.success, "Could Not Find Vivado Critical Path in "+config[2])
