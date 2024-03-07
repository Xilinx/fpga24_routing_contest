# Runtime-First FPGA Interchange Routing Contest @ FPGA’24

Please see website at https://xilinx.github.io/fpga24_routing_contest.

| ℹ️ **NOTE:** | This contest has now concluded!<br>[Link to the results and details from our top 5 teams](https://github.com/Xilinx/fpga24_routing_contest/tree/master/docs/results.md). |
| - | - |

Please report all issues using the GitHub [Issues](https://github.com/Xilinx/fpga24_routing_contest/issues) feature, and ask questions under [Discussions](https://github.com/Xilinx/fpga24_routing_contest/discussions).

---
All content in this repository, except for third-party software otherwise attributed (e.g. [Gradle](https://gradle.org), benchmark assets, etc.) is licensed under:
```
SPDX-License-Identifier: MIT
```
---

Utilities:
* [`net_printer`](https://github.com/Xilinx/fpga24_routing_contest/tree/master/net_printer) -- inspect the routing of nets in a Physical Netlist.
* [`DcpToFPGAIF`](https://github.com/Xilinx/fpga24_routing_contest/pull/10) -- process a DCP into FPGAIF Logical and Physical Netlists for use with this contest.
* [`wirelength_analyzer`](https://github.com/Xilinx/fpga24_routing_contest/tree/master/wirelength_analyzer) -- compute a [critical-path wirelength](https://xilinx.github.io/fpga24_routing_contest/score.html#critical-path-wirelength) for a routed FPGAIF Physical Netlist.
* [`DiffPhysNetlist`](https://github.com/Xilinx/fpga24_routing_contest/pull/66) -- display any illegal differences (placement, intra-site routing, global/static inter-site routing) between two FPGAIF Physical Netlists.
