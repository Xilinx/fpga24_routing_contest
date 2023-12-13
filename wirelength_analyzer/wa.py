# Copyright (C) 2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author: Zak Nafziger, AMD
#
# SPDX-License-Identifier: MIT
#

import sys
import os
import time
import capnp
import gzip
import argparse
import networkx as nx
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(THIS_DIR, '..','fpga-interchange-schema','interchange'))
import PhysicalNetlist_capnp
import warnings
import itertools
from xcvup_device_data import xcvupDeviceData
import re

class WirelengthAnalyzer:
    """
    NetworkX-based wirelength analyzer

    Given a routed FPGA Interchange Format Physical Netlist this class builds a
    graph containing trees corresponding to physical nets. Each edge in these
    trees represents an electrical connection between the corresponding net's
    source and sink and is assigned a wirelength based on the routing resources
    traversed along that path.

    Next, paths between sequential cells (e.g. FDRE flip-flops) are created by
    adding edges through all combinatorial cells (e.g. LUTs) which in turn
    transforms the graph from a forest of independent trees into a directed
    acyclic graph.

    Lastly, networkx is used to find the longest wirelength path -- from any
    sequential element/top-level port through to any other element/port -- in
    the graph. We term the length of this path as the 'critical-path
    wirelength' and can be considered a proxy for the critical-path delay that
    would be found by a timing analyzer.

    Note that this class assumes that the routed solution is valid -- it does
    not check for overlaps, existence of PIPs, full source-sink connectivity,
    etc.
    """

    class CustomEdgeAttribute:
        """
        By default, networkx uses a dict object as the container for all edge
        attributes. Since our edges only ever need a single edge attribute we
        can improve memory efficiency by using a custom slotted class that
        implements the bare minimum of methods
        """
        __slots__ = 'wirelength'
        def update(self, other):
            self.wirelength = other['wirelength']
        def get(self, key, default=None):
            return getattr(self, key, default)
        def __getitem__(self, key):
            if key == 'wirelength':
                return self.wirelength
            raise KeyError(key)

    class CustomNodeAttribute:
        """
        By default, networkx uses a dict object as the container for all node
        attributes. Since our nodes only ever need net_index and segment
        attributes we can improve memory efficiency by using a custom slotted
        class that implements the bare minimum of methods
        """
        __slots__ = 'net_index', 'segment'
        def update(self, other):
            self.net_index = other.get('net_index')
            self.segment = other['segment']
        def get(self, key, default=None):
            return getattr(self, key, default)
        def __getitem__(self, key):
            if key == 'net_index':
                return self.net_index
            if key == 'segment':
                return self.segment
            raise KeyError(key)


    def __init__(self, netlist, verbosity=0):
        """
        Initialize all of the major data structures required for wirelength
        analysis, from the provided netlist.

        Args:
            netlist: filepath of the FPGA Interchange Format Physical Netlist
            to analyze
            verbosity: control the verbosity of the output. Higher numbers
            produce more detailed output, but may take longer to run
        """
        self.nodeid = itertools.count()
        self.G = nx.DiGraph()
        self.G.edge_attr_dict_factory = WirelengthAnalyzer.CustomEdgeAttribute
        self.G.node_attr_dict_factory = WirelengthAnalyzer.CustomNodeAttribute
        self.verbosity = verbosity
        self.print_timing_commands = False
        self.start_time = None
        self.joined = False
        self.roots = []
        self.leaves = []
        xcvup = xcvupDeviceData()
        self.cells = xcvup.cells
        self.pips = xcvup.pips
        self.tile_root_name_regex = xcvup.tile_root_name_regex
        self.tile_types = xcvup.tile_types
        self.global_net_drivers = xcvup.global_net_drivers
        self.pip_cache = {}
        self.tile_cache = {}
        if self.verbosity > 0:
            print("Building Graph")
        self.phys = self.read_phys_netlist(netlist)
        self.placements = {}
        for c in self.phys.placements:
            self.placements[(c.site, c.bel)] = c
        self.add_all_nets_to_graph()

    def tstart(self):
        """
        Record the time that this function was called at.
        """
        self.start_time = time.time()

    def tstop(self, message):
        """
        Depending on the verbosity level, print the message and the time since
        self.tstart was called.

        Args:
            message: message to print
        """
        tend = time.time()
        if self.verbosity > 0:
            print(message + " in: %.1fs" % (tend - self.start_time))

    def read_phys_netlist(self, phys_name):
        """
        Read the provided FPGA Interchange Format Physical Netlist,
        decompressing it with gzip if necessary

        Args:
            phys_name: filepath of the FPGA Ingerchange Format Physical Netlist
            to consume
        """
        self.tstart()
        phys = None
        with open(phys_name, 'rb') as f:
            magic = f.read(2)
            f.seek(0)
            if magic == b'\x1f\x8b':
                f = gzip.GzipFile(fileobj=f)
            with PhysicalNetlist_capnp.PhysNetlist.from_bytes(f.read(), traversal_limit_in_words=sys.maxsize, nesting_limit=2**20) as phys_netlist:
                phys = phys_netlist
        self.tstop("Loaded Physical Netlist")
        return phys

    def format_segment(self, seg):
        """
        Build a formatted string describing an FPGA Interchange Format
        RouteBranch.routeSegment object.

        Args:
            seg: an FPGA Interchange Format RouteBranch.routeSegment object

        Returns:
            a formatted string
        """
        if seg is None:
            return 'NULL'
        sl = self.phys.strList
        w = seg.which()
        fw = "%-7s" % w
        if w == 'belPin':
            return ' '.join([fw, sl[seg.belPin.site], sl[seg.belPin.bel], sl[seg.belPin.pin]])
        elif w == 'sitePin':
            return ' '.join([fw, sl[seg.sitePin.site], sl[seg.sitePin.pin]])
        elif w == 'pip':
            return ' '.join([fw, sl[seg.pip.tile], sl[seg.pip.wire0], sl[seg.pip.wire1], str(seg.pip.forward), str(seg.pip.isFixed)])
        elif w == 'sitePIP':
            return ' '.join([fw, sl[seg.sitePIP.site], sl[seg.sitePIP.bel], sl[seg.sitePIP.pin], str(seg.sitePIP.isFixed)])

    def net_index_to_name(self, net_index):
        """
        Return the name of the net located in the list of physical nets at the
        provided index as a string

        Args:
            net_index: integer index for the list of physical nets

        Returns:
            the name of the net as a string
        """
        sl = self.phys.strList
        nets = self.phys.physNets
        net_name = sl[nets[net_index].name]
        return net_name

    def find_net_name_from_edge(self, edge):
        """
        Given an edge in the graph return the name of the net it is a part of.
        No assumption is made about edge direction. If the edge does not have
        a net associated with it (i.e. it is the result of a join) return the
        name of the nearest net if it exists, otherwise return the string NULL.
        This method exists to improve readability of error messages.

        Args:
            edge: an ordered collection of two nodes

        Returns:
            the name of the associated net as a string
        """
        net_index = self.G.nodes[edge[0]]['net_index']
        if net_index is None:
            net_index = self.G.nodes[edge[1]]['net_index']
            if net_index is None:
                return 'NULL'
        net_name = self.net_index_to_name(net_index)
        return net_name

    def segment_to_wirelength(self, seg):
        """
        Determine the wirelength associated with an FPGA Interchange Format
        RouteBranch.routeSegment based on the architectural information
        supplied when the class was initialized.

        If the provided routeSegment is not a pip (e.g. an intrasite wire)
        return 0. If the routeSegment is a pip in an intersite switchbox check
        the table of pips provided in the architecture file to determine the
        wirelength associated with this pip. Since checking the table of pips
        requires an expensive regex operation, cache the result of the lookup
        to reduce runtime of subsequent look ups.

        Further, since determining if a pip is in an intersite switchbox
        requires an expensive string comparison we also cache these results.

        Args:
            seg: FPGA Interchange Format RouteBranch.routeSegment to determine
            wirelength of

        Returns:
            wirelength as an interger

        Raises:
            AssertionError: if the input routeSegment is a pip, and is not in
            the table of pips.
        """
        if seg.which() == 'pip':
            wire1 = seg.pip.wire1
            tile  = seg.pip.tile
            sl = self.phys.strList
            wire1_name = sl[wire1]
            tile_name = sl[tile]

            is_int_tile = self.tile_cache.get(tile)
            if is_int_tile is None:
                is_int_tile = tile_name.startswith('INT_')
                self.tile_cache[tile] = is_int_tile
                if not is_int_tile and self.tile_root_name_regex.match(tile_name).group(1) not in self.tile_types:
                    raise ValueError("Unrecognized tile on PIP: " + tile_name + ',' +  sl[seg.pip.wire0] + ',' + wire1_name)

            if is_int_tile:
                wl = self.pip_cache.get(wire1)
                if wl is not None:
                    return wl
                for p in self.pips:
                    if p[0].fullmatch(wire1_name):
                        self.pip_cache[wire1] = p[1]
                        return p[1]
                assert False, "Found unrecognized pip wire1: "+wire1_name+" in tile: "+tile_name
            else:
                return 0
        return 0

    def add_net_to_graph(self, source, route_branch):
        """
        Perform a Depth First Search of the net rooted at route_branch. As
        the net is traversed, the wirelength of all its PIPs is accumulated.
        When a leaf is encountered add a new node to the graph, with an edge
        from the source to this new node, with the wirelength as an attribute.
        Also add the new node to the list of leaves.

        Args:
            source: the nodeid of this net's source
            route_branch: the source FPGA Interchange Formate RouteBranch

        Raises:
            ValueError: if a leaf segment that is not a sitePin or belPin is
            discovered
        """
        stack = [(b, 0) for b in route_branch.branches]
        while len(stack) != 0:
            branch = stack.pop()
            route_branch = branch[0]
            wirelength = branch[1]
            seg = route_branch.routeSegment
            wirelength += self.segment_to_wirelength(seg)
            if len(route_branch.branches) == 0:
                sink = next(self.nodeid)
                self.G.add_node(sink, segment=seg)
                self.G.add_edge(source, sink, wirelength=wirelength)
                if seg.which() == 'sitePin':
                    pass
                elif seg.which() != 'belPin':
                    raise ValueError("Leaf segment: "+self.format_segment(seg)+" on net: "+self.find_net_name_from_edge((source, sink))+" not a belPin or sitePin")
                else:
                    self.leaves.append(sink)
            else:
                for b in route_branch.branches:
                    stack.append((b, wirelength))

    def add_all_nets_to_graph(self):
        """
        Add each physical signal net in the netlist to the graph. Ignore global
        nets (as determined by its source pin originating on a global buffer)
        since we don't consider their wirelength. This method emits warnings
        for signal nets with multiple sources or unrouted stubs. Finally, this
        method also ignores source-less or sink-less nets, since they cannot
        contribute to overall wirelength.

        Raises:
            AssertionError: if an unknown net type is found
            AssertionError: if a net with a non belPin source is found
        """
        self.tstart()
        sl = self.phys.strList
        nets_with_stubs = 0
        stub_count = 0
        nets_with_multiple_sources = 0
        multisource_count = 0
        for net_index, n in enumerate(self.phys.physNets):
            this_net = sl[n.name]
            if n.type != "signal":
                assert n.type in ('gnd', 'vcc')
                continue
            if this_net == 'GLOBAL_USEDNET':
                continue
            if len(n.stubs) != 0:
                if len(n.sources) == 0:
                    # Nets with stubs but no sources are assumed to be hierarchical ports
                    continue
                nets_with_stubs += 1
                stub_count += len(n.stubs)
            if len(n.sources) > 1:
                nets_with_multiple_sources += 1
                multisource_count += len(n.sources)
            for branch in n.sources:
                w = branch.routeSegment.which()
                assert w == 'belPin', "Found root edge of type "+w+" on net "+this_net
                # Omit source (BELPins) that don't have any fanout
                if len(branch.branches) == 0:
                    continue
                if sl[branch.routeSegment.belPin.bel] in self.global_net_drivers:
                    # don't analyze global (e.g. clk, rst) nets
                    if self.verbosity > 1:
                        print("Skipping global net:",this_net)
                else:
                    source = next(self.nodeid)
                    self.roots.append(source)
                    self.G.add_node(source, net_index=net_index, segment=branch.routeSegment)
                    self.add_net_to_graph(source, branch)
        if nets_with_stubs != 0:
            warnings.warn("Found "+str(stub_count)+" stubs across "+str(nets_with_stubs)+" nets")
        if nets_with_multiple_sources != 0:
            warnings.warn("Found "+str(multisource_count)+" sources across "+str(nets_with_multiple_sources)+" nets")
        self.tstop("Added nets to graph")

    def join_nets(self):
        """
        For each BEL/cell collect all of the leaves that drive its inputs. Then
        for each root driven by the BEL/cell add edges between the inputs and
        ouputs according to the connectivity rule defined in the device data
        file.

        Raises:
            AssertionError: if unrecognized cells are found
        """

        self.tstart()
        join_points = {}
        unrecognized_cells = {}

        sl = self.phys.strList
        for l in self.leaves:
            leaf = self.G.nodes[l]['segment']
            bel = (leaf.belPin.site, leaf.belPin.bel)
            join_points.setdefault(bel, {})[sl[leaf.belPin.pin]] = l

        for r in self.roots:
            root = self.G.nodes[r]['segment']
            bel = (root.belPin.site, root.belPin.bel)
            bel_inputs = join_points.get(bel)
            if not bel_inputs:
                continue
            cell_type = sl[self.placements[bel].type]
            join_fn = self.cells.get(cell_type)
            if join_fn is None:
                unrecognized_cells.setdefault((cell_type, sl[bel[1]]), []).append(self.find_net_name_from_edge(list(self.G.out_edges(r))[0]))
                continue
            connections = join_fn(sl[root.belPin.pin])
            for i in bel_inputs.keys():
                if i in connections:
                    self.G.add_edge(bel_inputs[i], r, wirelength=0)

        assert len(unrecognized_cells) == 0, "Found unrecognized cell(s): "+str(unrecognized_cells)
        self.joined = True
        self.tstop("Joined nets")

    def find_longest_path(self):
        """
        Use networkx to find the longest path in the graph

        Returns:
            a list of nodes that form the longest path in the graph
        """
        self.tstart()
        lp = nx.dag_longest_path(self.G, weight='wirelength')

        # NetworkX's longest path algorithm will return the longest path by
        # wirelength, but it is not necessarily a path that terminates in a
        # timing endpoint (e.g. a FF).
        # Consider the example where the tail of such a longest path consists
        # of a LUT followed by an intra-site connection to a FF.
        # NetworkX will return a path that terminates at the LUT, since the
        # intra-site connection to the FF incurs no additional wirelength.
        # Rather than present this truncated path to the user, attempt to
        # extend this longest path to include connections to downstream cells.

        def search_for_first_valid_sink(source, path=[]):
            """
            Run a Depth First Search from the provided source returning the
            first path found to a cell that is not a combinatorial driver for
            any further routeSegments.

            Args:
                source: the source node to begin searching from
                path: the current list of nodes leading to source
            Returns:
                a list of nodes (starting at the source node) forming a path
                to the first sink, empty list if one cannot be found.
            """
            out_edges = self.G.out_edges(source)
            path = path + [source]
            if len(out_edges) == 0:
                source_seg = self.G.nodes[source]['segment']
                if source_seg.which() == 'belPin':
                    if (source_seg.belPin.site, source_seg.belPin.bel) in self.placements:
                        return path
                return []
            for oe in out_edges:
                ret = search_for_first_valid_sink(oe[1], path)
                if ret:
                    return ret
            return []

        last = lp[-1]
        tail = search_for_first_valid_sink(last)
        if tail:
            lp = lp + tail[1:]
        else:
            seg = self.G.nodes[last]['segment']
            cell = self.placements[(seg.belPin.site, seg.belPin.bel)]
            sl = self.phys.strList
            warnings.warn("No valid sink found from cell " + sl[cell.cellName] + "; assuming that it drives a hierarchical port.")
        return lp

    def expand_edge(self, source, sink):
        """
        add_net_to_graph() does not retain detailed routing information about
        each net, since doing so would produce a very large graph. Thus, once
        the longest path has been found, if the detailed routing information is
        required (e.g. for verbose printing) each of the edges along the path
        must be "expanded".

        To do this a Depth First Search from the net's source is performed.
        Once the sink is found the list of routeSegments that connect the
        source to the target sink is returned. This list is the "expanded"
        edge.

        Args:
            source: the nodeid of the source in the net to expand
            sink: the nodeid of the target sink in the net to expand

        Returns:
            a tuple of FPGA Interchange Format routeSegments that correspond to
            the path from the source to the sink, if such a path exists. None
            otherwise
        """
        sl = self.phys.strList
        nets = self.phys.physNets
        net = nets[self.G.nodes[source]['net_index']]
        sink_segment = self.G.nodes[sink]['segment']

        def search_for_sink(route_branch, sink, path=()):
            """
            Recursive Depth First Search of the net rooted at route_branch that
            returns the path between route_branch and the target sink.

            Args:
                route_branch: route_branch to begin searching from
                sink: the target RouteBranch.routeSegment
                path: empty tuple where the detailed routing will be stored

            Returns:
                a tuple of FPGA Interchange Format routeSegments
            """
            segment = route_branch.routeSegment
            path = (*path, segment)
            if len(route_branch.branches) == 0:
                # This is a workaround for a capnp limitation:
                # https://github.com/capnproto/pycapnp/issues/74#issuecomment-120534892
                if segment.to_dict() == sink.to_dict():
                    return path
                return None
            else:
                for b in route_branch.branches:
                    ret = search_for_sink(b, sink, path=path)
                    if ret is not None:
                        return ret
                return None

        return search_for_sink(net.sources[0], sink_segment)

    def pretty_print_path(self, path, path_name):
        """
        Format and print out the provided path.

        For verbosity > 0, the path is printed without detailed routing (i.e.
        only the sources and sinks of nets along the path are printed). The
        names of each net along the path are also printed, as well as a running
        count of wirelength and the names of cells that provide a combinatorial
        connection between nets.

        For verbosity > 1, the path is printed with detailed routing
        information (i.e. all routeSegments along the path are printed). A
        slight runtime penalty is incurred in this mode since expand_edge()
        must be run for each net in the path. everything from the previous
        level is also printed as well as the wire length of each intermediate
        routeSegment.

        Args:
            path: list of nodes forming a path through the graph
            path_name: the name of the path to be printed
        """
        length = 0
        formatted_path = []
        sl = self.phys.strList
        edges = zip(path[0::2], path[1::2])
        cells_on_path = []

        def append_path_line(w, l, s, n):
            """
            Helper function to append formatted row to the path

            Args:
                w: integer, (segment wirelength)
                l: integer, (running total wirelength)
                s: string, (segment name)
                n: string, (net name)
            """
            sep = '|'
            pl = '   '
            if w is not None:
                pl += '%5s' % w
            else:
                pl += '     '
            pl += sep
            if l is not None:
                pl += '    %5s' % l
            else:
                pl += '         '
            pl += sep
            if s is not None:
                pl += ' %s' % s
            else:
                pass
            if n is not None:
                pl += ' %s' % n
            else:
                pass
            formatted_path.append(pl)

        formatted_path.append('Segment | Running |')
        formatted_path.append('Length  |  Total  | Segment Name')
        formatted_path.append('--------+---------+-----------------------------------------')

        # display the cell that drives the first net on the path
        first_source_seg = self.G.nodes[path[0]]['segment']
        first_cell = self.placements[(first_source_seg.belPin.site, first_source_seg.belPin.bel)]
        append_path_line(None, length, 'cell    '+sl[first_cell.cellName], None)
        cells_on_path.append(sl[first_cell.cellName])

        for e in edges:
            u = e[0]
            v = e[1]
            edge_data = self.G.get_edge_data(u, v)
            wl = edge_data['wirelength']
            length += wl

            if self.verbosity < 1:
                continue

            net_name = self.net_index_to_name(self.G.nodes[u]['net_index'])
            source_seg = self.G.nodes[u]['segment']
            sink_seg = self.G.nodes[v]['segment']
            source = self.format_segment(source_seg)
            sink   = self.format_segment(sink_seg)

            source_len = self.segment_to_wirelength(source_seg)
            sink_len = self.segment_to_wirelength(sink_seg)

            # display this edge's source segment
            this_net = '(start of net: '+net_name+')'
            append_path_line(source_len, None, source, this_net)

            # display either abbreviated or detailed routing for this edge
            if self.verbosity <= 1:
                append_path_line(wl, None, '...', None)
            else:
                expanded_edge = self.expand_edge(u, v)
                for seg in expanded_edge[1:-1]:
                    wl = self.segment_to_wirelength(seg)
                    append_path_line(wl, None, self.format_segment(seg), None)

            # display this edge's sink segment
            append_path_line(sink_len, None, sink, None)

            # display the cell that this connects this edge to the next one
            join_cell = self.placements[(sink_seg.belPin.site, sink_seg.belPin.bel)]
            cells_on_path.append(sl[join_cell.cellName])
            append_path_line(None, length, 'cell    '+sl[join_cell.cellName], None)

        if self.verbosity < 1:
            print(path_name,"Wirelength:",length)
            return

        print("============================================================")
        print("Routing path for", path_name)
        print("Wirelength:",length)
        for l in formatted_path:
            print(l)
        print('')
        print("============================================================")
        if self.print_timing_commands:
            tcl = self.vivado_timing_commands(cells_on_path)
            print()
            for cmd in tcl:
                print(cmd)
                print()

    def vivado_timing_commands(self, cells_on_path):
        """
        Given a list of cell names return a list of Vivado Tcl commands. The
        first command in the list reports timing through the list of cells, and
        the second commmand in the list selects all of the cells in device
        veiw.

        Args:
            cells_on_path: a list of cell names on a path
        Returns:
            a list of two Vivado Tcl commands
        """
        cmds = []
        tcl_cmd = "report_timing -from {"+cells_on_path[0]+"} "
        for cell in cells_on_path[1:]:
            tcl_cmd += "-through {"+cell+"} "
        tcl_cmd += "-delay_type min_max -max_paths 10 -sort_by group -input_pins -routable_nets -name timing_1"
        cmds.append(tcl_cmd)
        tcl_cmd = "select_objects [get_cells {"
        for cell in cells_on_path:
            tcl_cmd += cell + " "
        tcl_cmd += "}]"
        cmds.append(tcl_cmd)
        return cmds

    def find_lsn(self):
        """
        Find the Longest Single Net in the graph. This method can only be
        run before nets are joined.

        If verbosity is set to 0 only the path name, the net the path is on and
        total wirelength of the path are printed. For higher verbosity levels
        the pretty printer is called.
        """
        if self.verbosity > 0:
            print()
            print("Finding Longest Single Net:")
        assert self.joined == False, "Cannot find Longest Single Net after joining"
        self.lsn = self.find_longest_path()
        lsn_name = self.find_net_name_from_edge((self.lsn[0], self.lsn[1]))
        self.pretty_print_path(self.lsn, "Longest Single Net ("+lsn_name+")")

    def find_critical_wirelength(self):
        """
        Find the critical path in the graph.

        If verbosity is set to 0 only the path name and wirelength are printed.
        For higher verbosity levels the pretty printer is called.
        """
        if self.verbosity > 0:
            print()
            print("Finding Critical Path:")
        self.join_nets()
        self.critical_path = self.find_longest_path()
        self.pretty_print_path(self.critical_path, "Critical Path")

def main():
    """
    The main entry point for the wirelength analyzer.
    """
    parser = argparse.ArgumentParser(
        prog="wa",
        description="Compute the longest wirelength in a routed FPGA Interchange Format Physical Netlist",
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('physical_netlist',
                        type=str,
                        help="FPGAIF Physical Netlist to process")
    parser.add_argument('-v',
                        '--verbosity',
                        type=int,
                        help="output verbosity level",
                        default=1)
    parser.add_argument('--mode',
                        metavar = 'MODE',
                        choices=['lsn', 'cp', 'longest-single-net', 'critical-path', 'both'],
                        default='cp',
                        help=
                        "MODE is 'cp' or 'critical-path' (default)\n"+
                        "    compute the length of the critical path\n"+
                        "MODE is 'lsn' or 'longest-single-net'\n"+
                        "    compute the length of the longest single routed net\n"+
                        "MODE is 'both'\n"+
                        "    run both previous modes consecutively.")

    args = parser.parse_args()

    wa = WirelengthAnalyzer(args.physical_netlist, args.verbosity)

    if args.mode in ['lsn', 'longest-single-net', 'both']:
        wa.find_lsn()
    if args.mode in ['cp', 'critical-path', 'both']:
        wa.find_critical_wirelength()

if __name__ == "__main__":
    main()
