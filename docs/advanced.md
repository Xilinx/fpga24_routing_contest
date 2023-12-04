# Advanced Routing Topics

## LUT Pin Swapping

An FPGA's Look-Up Tables can typically be used to implement any logical function
up to its maximum number of inputs.
For example, a 3-input LUT can be configured to perform an AND function, an OR,
a 2:1 multiplexer, etc.

From a logical perspective, all LUT inputs can be considered equivalent in that
this LUT configuration can be rotated to match any input ordering.
Thus, when the routing sink is a LUT input it may prove beneficial to consider
all LUT inputs as eligible targets.

For completeness, it is worth mentioning that from a timing perspective each LUT
input will have different delay cost and which should be factored in when performing
timing-driven routing.
Within the scope of this contest though, which considers only the critical-path
wirelength, swapping LUT pins will have no effect. 

The AMD UltraScale+ architecture contains 6-input LUTs which can support any
1-bit output function of up to 6-inputs.
However, such 6-input LUTs can also be *fractured* into two 5-input LUTs
that must share up to 5-inputs -- the 6th input will be routed to VCC.
A table of some example scenarios are shown below:

|Primary LUT|Secondary LUT|Equivalent BEL pins|
|-----------|-------------|-------------------|
| LUT6      | n/a         | A1-A6             |
| LUT5      | (empty)     | A1-A6             |
| LUT3      | (empty)     | A1-A6             |
| LUT5      | LUT5        | A1-A5             |
| LUT2      | LUT2        | A1-A5             |
| (empty)`*`| LUT5        | A1-A5             |

`*` It is possible for the primary LUT to be empty and only the secondary LUT
    be used. In such a scenario (since in this contest the placement cannot be
    modified) LUT pin swapping can only occur across `A1`-`A5` as `A6` will
    still need to be tied to VCC.

Once the router has found a fully legal routing solution, normally it would be
necessary to update the FPGAIF Physical Netlist's intra-site routing and
`PinMapping` details within the `CellPlacement` to reflect the new pin ordering.
However, contest rules state that the input placement and intra-site routing
cannot be modified.
To resolve this conflict, these updates will be performed during the
[`CheckPhysNetlist`](https://github.com/Xilinx/fpga24_routing_contest/blob/main/src/com/xilinx/fpga24_routing_contest/CheckPhysNetlist.java)
process ahead of using Vivado to validate the design.

To ensure that
[`CheckPhysNetlist`](https://github.com/Xilinx/fpga24_routing_contest/blob/main/src/com/xilinx/fpga24_routing_contest/CheckPhysNetlist.java)
and the
[`wirelength_analyzer`](https://github.com/Xilinx/fpga24_routing_contest/blob/master/wirelength_analyzer/wa.py)
can process pin-swapped outputs correctly, contest routers are required to connect
the final `pip` routeSegment of the route to the original (pre-swap) `sitePin` even
when the `pip` does not normally drive the site pin's associated routing node.
Doing so will simulate full connectivity, and the contest infrastructure above will
be able to perform all necessary intra-site routing and pin mapping updates to
reflect the pin swapped result.

The [baseline RWRoute](https://github.com/Xilinx/fpga24_routing_contest/blob/master/src/com/xilinx/fpga24_routing_contest/PartialRouterPhysNetlist.java)
provided as part of this contest supports LUT pin swapping functionality in the
above manner, which was added in the following
[pull request](https://github.com/Xilinx/fpga24_routing_contest/pull/47).
As discussed at this link, this option is not enabled by default since it does not
universally improve routing runtime.
Contestants who wish to experiment with pin swapping or improve it can enable swapping
by uncommenting the `--lutPinSwapping` line.

