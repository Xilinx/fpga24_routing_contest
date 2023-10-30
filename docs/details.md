# Contest Details

## Key Details

* The target device for this contest will be the AMD/Xilinx UltraScale+ xcvu3p.
* Competing routers must consume a pre-placed and partially-routed
 [FPGA Interchange Format](http://www.rapidwright.io/docs/FPGA_Interchange_Format.html) Physical Netlist
  and emit a fully routed Physical Netlist formed by enabling some number of routing switches (termed PIPs).
* The exact scoring criteria is presented on the [Scoring Criteria](score.html)
  webpage. In general, contestant routers are expected, in order of importance, to:
    1. Produce a legal routing solution ...
    2. ... in as little wall-clock time as possible ...
    3. ... with as low a [Critical-Path Wirelength](score.html#critical-path-wirelength-algorithm) as possible
* Contestants can expect to be evaluated on an AMD multi-core Linux platform with >=32 cores, >=64GB RAM,
  and no internet connectivity.
  We are working on providing access to AMD compute and GPU resources for benchmarking purposes;
  more details will be released and communicated to registered teams in due course.

## Framework

As stated in the [Introduction](index.html#introduction), the input to the router will be a pre-placed
but partially routed FPGAIF design.
Specifically, to lower the barrier to entry, only signal nets are required to be routed -- all global (e.g. clock) and
static (VCC/GND) nets are pre-routed and **must** be fully preserved (i.e. cannot be ripped up and rerouted).
Furthermore, the existing placement (including all intra-site routing) **must** also be fully preserved.
Violation of these requirements result in being ranked last on such benchmarks.
A more detailed look at the contest flow is shown below: 

[![image](flow-detailed.png)](flow-detailed.png)

#### Pre-routing
Starting from benchmarks described in RTL, Vivado is used to synthesize, place, and route each design.
[RapidWright](https://www.rapidwright.io/) then takes that fully-routed Vivado result, unroutes all signal
nets (preserving only global, VCC and GND nets) and writes this result out into FPGA Interchange Format
Logical and Physical Netlists.
These steps are not mandatory for contestants to run -- a number of FPGAIF benchmarks are provided (with more
to follow).

Should contestants wish to test/train with more benchmarks than those that are provided, the 
[`DcpToFPGAIF`](https://github.com/Xilinx/fpga24_routing_contest/pull/10) utility is provided.

#### Router
With just the pre-placed but partially-routed input Physical Netlist, competitors are required to route all
signal nets while preserving all existing placement and routing. In practice this
is achieved by only inserting FPGAIF routeSegment objects of the type `pip` into the
netlist. This fully-routed result must then be written out as a new Physical Netlist.

#### Post-routing
Once this fully-routed Physical Netlist is ready, RapidWright takes it again and combines it with the previous
Logical Netlist in order to reconstitute a Vivado Design Checkpoint.
Here, Vivado’s `report_route_status` command is used to verify that the design is indeed fully-routed --
that no nodes have multiple drivers (overlaps), and that all there is complete connectivity from all source
pins to all sink pins. Returning the design into Vivado allows us to take advantage of its robust legality
checking capabilities, as well as demonstrating that the FPGAIF is able to capture all the design state required
to interface with an industrial tool.
In addition, for the cases where a contestant’s router does not behave as expected, one can also leverage the
GUI and other capabilities of Vivado to aid debugging.

The output Physical Netlist will also be analyzed to compute its critical-path wirelength, which will make up
a small weight of the score.
This metric serves as a simple-to-compute proxy for critical-path delay thus incentivizing contestants to not
give up on quality-of-results entirely.
The details of how Critical-Path Wirelength will be computed are presented on
the [Scoring Criteria](score.html#critical-path-wirelength-algorithm) webpage.
Additionally a tool to compute this Critical-Path Wirelength, called `wa.py` is
supplied in the [GitHub repository](https://github.com/Xilinx/fpga24_routing_contest/tree/master/wirelength_analyzer).

Finally, all scoring components – legality of routing solution, wall-clock
router runtime, and critical-path wirelength will be combined to produce a per-benchmark
score. These scores will be used to rank each team and averaged to
determine the overall winners of the contest. The exact scoring formula and
ranking algorithm is described in detail on the [Scoring Criteria](score.html)
webpage.

## Getting Started

Get started [here](start.html)!
