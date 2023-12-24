# Copyright (C) 2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author: Eddie Hung, AMD
#
# SPDX-License-Identifier: MIT
#

"""
This file demonstrates how a bare-bones Python-based router (that returns
a partially valid solution) can be built which derives all its data from FPGA
Interchange inputs.
We DO NOT recommend this proof-of-concept implementation be used as the
baseline for any contest entry, but merely as a reference example.

Specifically, this code demonstrates how a FPGA Interchange DeviceResources
file can be parsed to extract the complete routing graph, as well as how an
Interchange PhysicalNetlist can be parsed to determine the source and sink
pins/nodes to be routed, the routing resources already occupied by pre-routed
nets, and how to insert the routed result back into the output PhysicalNetlist.

We use the NetworkX package to capture the routing graph, and also employ
its shortest-path algorithms to find routing solutions. Since NetworkX is a
pure Python package, runtime and memory performance is expected to be poor.
For this reason, by default only a subset of the FPGA routing graph is
constructed, and by extension only those pins entirely contained within are
routed. Furthermore, since this is a proof-of-concept there is no effort to
eliminate overlaps (nodes driven by more than one net) leading to a partially
valid solution.

Please see the contest website for more information and example output.

To reiterate, we DO NOT RECOMMEND this implementation be used as the starting
point for any contest entry.
"""

import sys
import os
import time
import capnp
import gzip
import networkx as nx
import re
import resource
from contextlib import contextmanager

# Tell pycapnp to search for schema files inside the
# FPGA Interchange Schema repository
sys.path.append('fpga-interchange-schema/interchange')

class NxRoutingGraph(nx.DiGraph):
        """NetworkX-based Routing Graph

        By parsing an FPGA Interchange DeviceResources file, this class builds a
        NetworkX DiGraph (which is inherited) such that graph nodes represent a
        routing node (collection of wires from potentially-differing tiles) and graph
        edges represent programmable connections between such nodes (the exact PIP
        to do this is attached as an edge attribute).

        Parsing also builds a set of dictionaries that will aid in computing site pin
        to graph node and edge to PIP lookups.
        """

        # Clock Region X2Y1 (requires ~5GB RAM)
        MIN_X = 36
        MAX_X = 56
        MIN_Y = 60
        MAX_Y = 119

        # Entire device (requires ~50GB RAM)
        # MIN_X = 0
        # MAX_X = sys.maxsize
        # MIN_Y = 0
        # MAX_Y = sys.maxsize

        class CustomEdgeAttribute:
                """By default, networkx uses a dict object as the container for all edge attributes.
                   Since our graph exclusively and compulsorily stores a single 'pip' edge attribute,
                   improve memory efficiency by using a custom slotted class that implements the bare
                   minimum of methods"""
                __slots__ = 'tile','pipDataIndex'
                def update(self, other):
                        self.tile,self.pipDataIndex = other['pip']
                def __contains__(self, key):
                        return key == 'pip'
                def get(self, key, default=None):
                        return getattr(self, key, default)
                def __getitem__(self, key):
                        if key == 'pip':
                                return (self.tile,self.pipDataIndex)
                        raise KeyError(key)
        edge_attr_dict_factory = CustomEdgeAttribute

        class CustomNodeAttribute:
                """By default, networkx uses a dict object as the container for all node attributes.
                   Since only a small subset of graph nodes will contain node attributes (e.g. 'sp'
                   attribute indicating a sink site pin, and <netName> indicating the name of the net
                   routing through this node) improve memory efficiency by using a custom slotted
                   class with a lazily-initialized dictionary"""
                __slots__ = ('lazyDict',)
                emptyDict = {}
                def __init__(self):
                        self.lazyDict = None
                def _write(self):
                        if self.lazyDict is not None:
                                return self.lazyDict
                        self.lazyDict = {}
                        return self.lazyDict
                def _read(self):
                        return self.lazyDict if self.lazyDict is not None else self.emptyDict
                def update(self, other):
                        if not other:
                                return
                        self._write().update(self, other)
                def __setitem__(self, key, value):
                        self._write().__setitem__(key, value)
                def setdefault(self, key, default):
                        return self._write().setdefault(key, default)
                def __getitem__(self, key):
                        return self._read().__getitem__(key)
                def get(self, key, default=None):
                        return self._read().get(key, default)
                def __contains__(self, key):
                        return key in self._read()
        node_attr_dict_factory = CustomNodeAttribute

        def build(self, filename):
                print('Building routing graph...')
                # The following mapping is used by getNodeFromSitePin()
                #   Mapping from tileType to (siteType,pinName) to wire
                self.tileType2SiteTypePinName2wire = {}
                #   Mapping from site to tile and tile/site types
                self.site2tileAndTypes = {}
                #   Mapping from tile to wire to node
                self.tile2wire2node = {}
                # The following mapping used by getPIP()
                #   Mapping from pipDataIndex to (wire0Name,wire1Name,forward)
                self.pipData = []

                # Read the DeviceResources file from disk and un-gzip into memory
                tstart = time.time()
                with open(filename, 'rb') as f:
                        f = gzip.GzipFile(fileobj=f)
                        data = f.read()
                # Parse the loaded file using pycapnp
                # Load 'DeviceResources.capnp'
                import DeviceResources_capnp
                with DeviceResources_capnp.Device.from_bytes(data, traversal_limit_in_words=sys.maxsize) as device:
                        tend = time.time()
                        print('\tRead DeviceResources: %.1fs' % (tend-tstart))
                        tstart = time.time()
                        s = CachedTextList(device.strList)

                        # Build a dictionary of all in-bounds tiles
                        tileNames = set()
                        tiles = []
                        reTileNameXY = re.compile(r'[A-Z0-9_]+_X(\d+)Y(\d+)')
                        MIN_X,MAX_X,MIN_Y,MAX_Y = self.MIN_X,self.MAX_X,self.MIN_Y,self.MAX_Y
                        for tile in device.tileList:
                                m = reTileNameXY.match(s[tile.name])
                                x = int(m.group(1))
                                if x < MIN_X or x > MAX_X:
                                        continue
                                y = int(m.group(2))
                                if y < MIN_Y or y > MAX_Y:
                                        continue
                                tileNames.add(tile.name)
                                tiles.append(tile)

                        # Insert nodes into graph (and build self.tile2wire2node)
                        wires = device.wires
                        add_node = self.add_node
                        tile2wire2nodeSetdefault = self.tile2wire2node.setdefault
                        # Note that DeviceResources provides a node -> wire mapping;
                        # here we have to build our own wire -> node
                        for nodeIdx,node in enumerate(device.nodes):
                                # Treat the first wire of a node as the 'base' wire
                                baseWireIdx = node.wires[0]
                                baseWire = wires[baseWireIdx]
                                if baseWire.tile not in tileNames:
                                        # Node is in an out-of-bounds tile
                                        continue
                                add_node(nodeIdx)
                                for wireIdx in node.wires:
                                        wire = wires[wireIdx]
                                        tileName = wire.tile
                                        wireName = wire.wire
                                        tile2wire2nodeSetdefault(tileName, {})[wireName] = nodeIdx
                        tend = time.time()
                        print('\tBuild %d graph nodes: %.1fs' % (self.number_of_nodes(),tend-tstart))
                        tstart = time.time()

                        # Insert edges into graph (and build self.pipData)
                        pipData2index = {}
                        tile2wire2nodeGet = self.tile2wire2node.get
                        tileTypes = device.tileTypeList
                        pipData = self.pipData
                        add_edge = self.add_edge
                        pipData2indexSetdefault = pipData2index.setdefault
                        for tile in tiles:
                                wire2node = tile2wire2nodeGet(tile.name)
                                if wire2node is None:
                                        # No nodes in this tile
                                        continue
                                wire2nodeGet = wire2node.get
                                tileName = s[tile.name]
                                isCleOrRclkTile = tileName.startswith('CLE') or tileName.startswith('RCLK')
                                tileType = tileTypes[tile.type]
                                tileWires = tileType.wires
                                # Note that the tileType determines the (superset) of all
                                # PIPs that can exist; certain conditions (e.g. tiles at
                                # the boundary of the device, or CLB tiles that border
                                # non-CLB tiles) may result irregularity which is captured
                                # by the fact that either wire on the PIP does not have a
                                # corresponding node
                                for pip in tileType.pips:
                                        if isCleOrRclkTile and pip.which() != 'conventional':
                                                # Ignore non-conventional PIPs on CLE tiles
                                                # (LUT route-thrus that traverse an entire site)
                                                # and on RCLK tiles (BUFCE route-thrus that access
                                                # the global routing network)
                                                continue
                                        wire0Name = tileWires[pip.wire0]
                                        node0Idx = wire2nodeGet(wire0Name)
                                        if node0Idx is None:
                                                # At least one wire does not exist, thus PIP cannot exist
                                                continue
                                        wire1Name = tileWires[pip.wire1]
                                        node1Idx = wire2nodeGet(wire1Name)
                                        if node1Idx is None:
                                                # At least one wire does not exist, thus PIP cannot exist
                                                continue
                                        # Add to self.pipData if not already seen
                                        forward = True
                                        pipDataIndex = pipData2indexSetdefault((wire0Name,wire1Name,forward), len(pipData))
                                        if pipDataIndex == len(pipData):
                                                pipData.append((s[wire0Name],s[wire1Name],forward))
                                        add_edge(node0Idx, node1Idx, pip=(tileName,pipDataIndex))
                                        # Add reverse edge for bidirectional PIPs
                                        if not pip.directional:
                                                forward = False
                                                pipDataIndex = pipData2indexSetdefault((wire0Name,wire1Name,forward), len(pipData))
                                                if pipDataIndex == len(pipData):
                                                        pipData.append((s[wire0Name],s[wire1Name],forward))
                                                add_edge(node1Idx, node0Idx, pip=(tileName,pipDataIndex))
                        tend = time.time()
                        print('\tBuild %d graph edges: %.1fs' % (self.number_of_edges(),tend-tstart))

                        tstart = time.time()
                        # Build mapping from siteType to pinIndex to pinName
                        siteTypePinNames = {}
                        for siteTypeIdx,siteType in enumerate(device.siteTypeList):
                                siteTypePinNames[siteTypeIdx] = [s[pin.name] for pin in siteType.pins]

                        # Build self.tileType2SiteTypePinName2wire
                        for tileTypeIdx,tileType in enumerate(device.tileTypeList):
                                for siteTypeIdx,siteType in enumerate(tileType.siteTypes):
                                        pinNames = siteTypePinNames[siteType.primaryType]
                                        for pinIndex,wireName in enumerate(siteType.primaryPinsToTileWires):
                                                pinName = pinNames[pinIndex]
                                                self.tileType2SiteTypePinName2wire.setdefault(tileTypeIdx, {})[siteTypeIdx,pinName] = s[wireName]

                        # Build self.site2tileAndTypes
                        for tile in tiles:
                                if not tile.sites:
                                        continue
                                for site in tile.sites:
                                        siteName = s[site.name]
                                        tileName = s[tile.name]
                                        self.site2tileAndTypes[siteName] = (tileName,tile.type,site.type)

                        # Convert self.tile2wire2node from having integer keys to string keys
                        # so that it can be used without access to device.strList
                        self.tile2wire2node = {s[k]: {s[k2]:v2
                                for k2,v2 in v.items()}
                                for k,v in self.tile2wire2node.items()}
                        tend = time.time()
                        print('\tBuild lookups: %.1fs' % (tend-tstart))

        def getNodeFromSitePin(self, siteName, pinName):
                tileAndTypes = self.site2tileAndTypes.get(siteName)
                if not tileAndTypes:
                        # Site must be out-of-bounds
                        return None
                tileName,tileTypeIdx,siteTypeIdx = tileAndTypes
                wireName = self.tileType2SiteTypePinName2wire[tileTypeIdx][siteTypeIdx,pinName]
                return self.tile2wire2node[tileName][wireName]

        def getPIP(self, u, v):
                tileName,wirePairIdx = self[u][v]['pip']
                wire0Name,wire1Name,forward = self.pipData[wirePairIdx]
                return (tileName,wire0Name,wire1Name,forward)

class NxRouter:
        """NetworkX-based Router

        Given a DeviceResources and a PhysicalNetlist, build a NxRoutingGraph
        object from DeviceResources, route all unrouted signal nets in the
        provided PhysicalNetlist and output the result into a new PhysicalNetlist.

        Usage is through a with-statement context manager returned by the create() method.
        """

        @contextmanager
        def create(deviceResourcesFilename, physNetlistFilename):
                """Return a with-statement context manager instance of NxRouter
                   with the routing graph built and the design parsed"""
                router = NxRouter(deviceResourcesFilename)

                print('Parsing design...')
                tstart = time.time()
                with open(physNetlistFilename, 'rb') as f:
                        f = gzip.GzipFile(fileobj=f)
                        data = f.read()
                # Load 'DeviceResources.capnp'
                import PhysicalNetlist_capnp
                with PhysicalNetlist_capnp.PhysNetlist.from_bytes(data, traversal_limit_in_words=sys.maxsize, nesting_limit=2**16) as netlist:
                        tend = time.time()
                        print('\tRead PhysicalNetlist: %.1fs' % (tend-tstart))
                        router.parse(netlist)
                        yield router

        def __init__(self, deviceResourcesFilename):
                self.G = NxRoutingGraph()
                self.G.build(deviceResourcesFilename)

        def parse(self, netlist):
                tstart = time.time()
                self.netlist = netlist

                # Mapping from net to (a) source pin to node mapping,
                # (b) list of sink nodes
                self.net2pin2node = {}

                s = CachedTextList(netlist.strList)

                for net in self.netlist.physNets:
                        assert len(net.stubNodes) == 0
                        if net.type == 'signal' and net.stubs:
                                sinkPins = self.extractSitePins(net.stubs)

                                # Net is a signal net (not vcc/gnd) and
                                # has some stub branches (unrouted site pins)
                                if not sinkPins:
                                        continue

                                # Build source pin to node mapping
                                sourcePin2node = {}
                                for sp in self.extractSitePins(net.sources):
                                        siteName,sinkName = s[sp.site],s[sp.pin]
                                        sourceNode = self.G.getNodeFromSitePin(siteName, sinkName)
                                        if sourceNode is None:
                                                continue
                                        sourcePin2node[siteName,sinkName] = sourceNode

                                # Collect list of all sink nodes from sink pins
                                sinkNodes = []
                                for sp in sinkPins:
                                        siteName,sinkName = s[sp.site],s[sp.pin]
                                        sinkNode = self.G.getNodeFromSitePin(siteName, sinkName)
                                        if sinkNode is None:
                                                continue
                                        if not sourcePin2node:
                                                # This net has no sources and is unrouteable; remove its
                                                # sink pin nodes from the graph to block other nets from
                                                # using them
                                                assert sinkNode in self.G
                                                self.G.remove_node(sinkNode)
                                        else:
                                                sinkNodes.append(sinkNode)

                                                sinkNodeAttr = self.G.nodes[sinkNode]
                                                assert 'sp' not in sinkNodeAttr
                                                sinkNodeAttr['sp'] = (siteName,sinkName)

                                                # Remove all outgoing edges from sink nodes;
                                                # Most importantly, this prevents other nets from using this node (which
                                                # would cause Vivado to flag it as site pin conflict) but an unfortunate
                                                # side-effect is that it also prevents other sinks on the same net from
                                                # doing so too if this is a pinbounce node
                                                self.G.remove_edges_from(list(self.G.out_edges(sinkNode)))

                                if not sinkNodes:
                                        continue
                                assert sourcePin2node

                                self.net2pin2node[net.name] = (sourcePin2node,sinkNodes)
                        else:
                                # This is a non-signal net (i.e. gnd/vcc) or it has no routing
                                # stubs (meaning it is fully routed). Walk its routing tree
                                # to identify all used routing resources and remove them from
                                # the routing graph so that no other nets will conflict.

                                tile2wire2nodeGet = self.G.tile2wire2node.get
                                queue = list(net.sources)
                                while queue:
                                        rb = queue.pop()
                                        rs = rb.routeSegment
                                        if rs.which() == 'pip':
                                                # Remove driven node from graph so no other nets can drive it
                                                pip = rs.pip
                                                wire2node = tile2wire2nodeGet(s[pip.tile])
                                                if wire2node:
                                                        blockedNode = wire2node.get(s[pip.wire1 if pip.forward else pip.wire0])
                                                        if blockedNode is not None:
                                                                self.G.remove_node(blockedNode)
                                                else:
                                                        # Tile must be out of bounds
                                                        pass
                                        queue.extend(rb.branches)
                del self.G.tileType2SiteTypePinName2wire
                del self.G.site2tileAndTypes
                del self.G.tile2wire2node
                tend = time.time()
                print('\tPrepare site pins: %.1fs' % (tend-tstart))

        def route(self):
                tstart = time.time()
                totalPinsToRoute = sum(len(sinkNodes) for (_,sinkNodes) in self.net2pin2node.values())
                print('Routing %d pins...' % totalPinsToRoute)

                numPinsRouted = 0
                hiddenEdges = []
                s = self.netlist.strList
                nodes = self.G.nodes
                for netName,(sourcePin2node,sinkNodes) in self.net2pin2node.items():
                        sourceNodes = sourcePin2node.values()
                        multiSink = len(sinkNodes) > 1
                        for sinkNode in sinkNodes:
                                path = None
                                # For every sink node, try all source nodes until one with a routing
                                # path is found
                                # Note that nx.shortest_path() only accepts a single source node; other
                                # implementations may wish to consider all sources simultaneously
                                for sourceNode in sourceNodes:
                                        try:
                                                path = nx.shortest_path(self.G, sourceNode, sinkNode)
                                        except nx.NetworkXNoPath:
                                                continue
                                        break
                                if not path:
                                        print('Unable to route sink pin ' + str(nodes[sinkNode]['sp']) + ' on net ' + s[netName])
                                        continue
                                numHiddenEdges = len(hiddenEdges)
                                for u,v in zip(path[:-1],path[1:]):
                                        # Key the next node of the path with the net name
                                        nodes[u].setdefault(netName, set()).add(v)
                                        if multiSink:
                                                # In order to prevent nodes with two different drivers from the same
                                                # net (breaking the requirement that a net's routing has to be a tree)
                                                # temporarily remove all incoming edges of used nodes
                                                # Note that trees from different nets may drive the same node, causing an overlap
                                                hiddenEdges.extend([edge for edge in self.G.in_edges(v, data=True) if edge[0] != u])
                                if hiddenEdges:
                                        self.G.remove_edges_from(hiddenEdges[numHiddenEdges:])
                                numPinsRouted += 1
                                if numPinsRouted % 10000 == 0:
                                        tend = time.time()
                                        print('\tRouted %d pins: %.1fs' % (numPinsRouted,tend-tstart))
                        # After routing all sinks of this net, restore all temporarily hidden
                        # edges so that they are available for other nets to use
                        for u,v,d in hiddenEdges:
                                self.G.add_edge(u, v, pip=d['pip'])
                        hiddenEdges.clear()
                tend = time.time()
                print('\tRouted %d pins: %.1fs' % (numPinsRouted,tend-tstart))

        def write(self, filename):
                print('Writing design...')
                tstart = time.time()
                # Copy the PhysicalNetlist from a pycapnp Reader of an existing design
                # into a Builder
                self.netlist = self.netlist.as_builder()

                # Build the string to stringIdx dictionary for all strings used in
                # existing design
                self.strings = {}
                for i,string in enumerate(self.netlist.strList):
                        self.strings[string] = i

                numPIPs = 0
                s = self.netlist.strList
                for net in self.netlist.physNets:
                        pin2node = self.net2pin2node.get(net.name)
                        if not pin2node:
                                # Net was not routed; nothing to update
                                continue
                        sourcePin2node = pin2node[0]

                        # Disown all sink pins from the stubs list
                        sinkPin2orphan = {}
                        for i,rb in enumerate(net.stubs):
                                rs = rb.routeSegment
                                assert rs.which() == 'sitePin'
                                sp = rs.sitePin
                                sinkPin2orphan[s[sp.site],s[sp.pin]] = net.stubs.disown(i)
                        net.disown('stubs')

                        # Walk through all net sources until a source site pin
                        # is found
                        queue = list(net.sources)
                        while queue:
                                rb = queue.pop()
                                queue.extend(rb.branches)
                                rs = rb.routeSegment
                                if rs.which() != 'sitePin':
                                        continue
                                sp = rb.routeSegment.sitePin
                                sourceNode = sourcePin2node[s[sp.site],s[sp.pin]]
                                if net.name not in self.G.nodes[sourceNode]:
                                        # Source pin was not used by this net
                                        continue

                                # Starting at this source node, walk forward through
                                # the graph following the next-nodes used by this net
                                graphQueue = [(rb,sourceNode)]
                                while graphQueue:
                                        rb,currNode = graphQueue.pop()
                                        assert not rb.branches
                                        currNodeAttr = self.G.nodes[currNode]
                                        nextNodes = currNodeAttr.get(net.name, [])
                                        sp = currNodeAttr.get('sp')
                                        if sp is not None:
                                                # This node is a sink site pin that must be present on this net:
                                                # move its corresponding stub as this node's last branch
                                                branches = rb.init('branches', len(nextNodes) + 1)
                                                orphan = sinkPin2orphan.pop(sp)
                                                # Adopting this orphan corrupts orphan.get().branches; copy it instead
                                                #branches.adopt(len(branches) - 1, orphan)
                                                branches[-1] = orphan.get()
                                        else:
                                                # Not a site pin, must have nextNodes
                                                assert nextNodes
                                                branches = rb.init('branches', len(nextNodes))
                                        # For every edge to a next-node, recover the PIP and add it
                                        # as a routing branch
                                        for i,nextNode in enumerate(nextNodes):
                                                nextRb = branches[i]
                                                pip = nextRb.routeSegment.init('pip')
                                                tileName,wire0Name,wire1Name,forward = self.G.getPIP(currNode,nextNode)
                                                pip.tile = self.getStringIndex(tileName)
                                                pip.wire0 = self.getStringIndex(wire0Name)
                                                pip.wire1 = self.getStringIndex(wire1Name)
                                                pip.forward = forward
                                                graphQueue.append((nextRb,nextNode))
                                                numPIPs += 1

                        if sinkPin2orphan:
                                # Compact the stubs list with all unrouted pins
                                newStubList = net.init('stubs', len(sinkPin2orphan))
                                for i,orphan in enumerate(sinkPin2orphan.values()):
                                        # Adopting this orphan corrupts orphan.get().branches; copy it instead
                                        #newStubList.adopt(i, orphan)
                                        newStubList[i] = orphan.get()

                # Initialize a new strList entry (capnp does not support resizing
                # an existing list).
                # Rather than copying the underlying string text, detach the pointer
                # ("disown") them from the existing list and reference ("adopt")
                # them in the new list.
                orphanStrList = []
                for i in range(len(s)):
                        orphanStrList.append(s.disown(i))
                newStrList = self.netlist.init('strList', len(self.strings))
                for string,i in self.strings.items():
                        if i < len(orphanStrList):
                                newStrList.adopt(i, orphanStrList[i])
                        else:
                                # New string that didn't exist in the unrouted design
                                newStrList[i] = string
                numStr = len(self.strings) - len(orphanStrList)
                del orphanStrList

                tend = time.time()
                print('\tInserting %d PIPs and %d strings: %.1fs' % (numPIPs,numStr,tend-tstart))
                tstart = time.time()

                # Write gzipped to disk
                with gzip.open(filename, 'wb', compresslevel=6) as f:
                        f.write(self.netlist.to_bytes())

                tend = time.time()
                print('\tWrite PhysicalNetlist: %.1fs' % (tend-tstart))

        def extractSitePins(self, branches):
                sitePins = []
                queue = list(branches)
                while queue:
                        rb = queue.pop()
                        rs = rb.routeSegment
                        if rs.which() == 'sitePin':
                                sitePins.append(rs.sitePin)
                        queue.extend(rb.branches)
                return sitePins

        def getStringIndex(self, string):
                return self.strings.setdefault(string, len(self.strings))

class CachedTextList:
        """Drop-in class for wrapping capnp's 'List<Text>' objects where
           gotten strings are cached rather than deep copied on each lookup"""
        def __init__(self, s):
                self.s = s
                self.i = [None] * len(s)
        def __getitem__(self, k):
                v = self.i[k]
                if v is None:
                        v = self.i[k] = self.s[k]
                return v


if len(sys.argv) != 3:
        print('USAGE: <unrouted.phys> <routed.phys>')
        sys.exit(1)

with NxRouter.create('xcvu3p.device', sys.argv[1]) as router:
        router.route()
        router.write(sys.argv[2])

print('Peak memory:', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, 'KB')
