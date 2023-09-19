# FPGA Interchange Format Physical Netlist Net Printer `np.py`

`np.py` is a simple Python program for printing out net routing from an FPGAIF `*.phys`
file. This program is provided to aid in the development of a contestant router,
by providing some visibility into the input and output files that contestant
routers consume and emit.

Consider the following example output:

```
$ python3 np.py ../vtr_mcml_rwroute.phys u_calc/boundaryChecker/r_ux__57_reg[21]_srl27___u_calc_dropSpin_photon29_o_sleftz_reg_r_n_0
============================================================
Route tree for net: u_calc/boundaryChecker/r_ux__57_reg[21]_srl27___u_calc_dropSpin_photon29_o_sleftz_reg_r_n_0

    Source: 0
    [{      belPin  SLICE_X84Y94 C6LUT O6
     {      belPin  SLICE_X84Y94 OUTMUXC D6
            sitePIP SLICE_X84Y94 OUTMUXC D6 False
            belPin  SLICE_X84Y94 OUTMUXC OUT
            belPin  SLICE_X84Y94 CMUX CMUX
         }  sitePin SLICE_X84Y94 CMUX
            belPin  SLICE_X84Y94 C_O C_O
            sitePin SLICE_X84Y94 C_O
            pip     INT_X54Y94 LOGIC_OUTS_W4 INT_NODE_SDQ_49_INT_OUT1 True False
            pip     INT_X54Y94 INT_NODE_SDQ_49_INT_OUT1 EE2_W_BEG1 True False
            pip     INT_X55Y94 EE2_W_END1 INT_NODE_SDQ_49_INT_OUT1 True False
            pip     INT_X55Y94 INT_NODE_SDQ_49_INT_OUT1 SS1_W_BEG1 True False
            pip     INT_X55Y93 SS1_W_END1 INT_NODE_SDQ_50_INT_OUT1 True False
            pip     INT_X55Y93 INT_NODE_SDQ_50_INT_OUT1 SS2_W_BEG1 True False
            pip     INT_X55Y91 SS2_W_END1 INT_NODE_SDQ_54_INT_OUT0 True False
            pip     INT_X55Y91 INT_NODE_SDQ_54_INT_OUT0 EE4_W_BEG1 True False
            pip     INT_X57Y91 EE4_W_END1 INT_NODE_SDQ_53_INT_OUT1 True False
            pip     INT_X57Y91 INT_NODE_SDQ_53_INT_OUT1 EE2_W_BEG2 True False
            pip     INT_X58Y91 EE2_W_END2 INT_NODE_IMUX_37_INT_OUT0 True False
            pip     INT_X58Y91 INT_NODE_IMUX_37_INT_OUT0 BYPASS_W8 True False
            sitePin SLICE_X90Y91 EX
            belPin  SLICE_X90Y91 EX EX
            belPin  SLICE_X90Y91 FFMUXE1 BYP
            sitePIP SLICE_X90Y91 FFMUXE1 BYP False
            belPin  SLICE_X90Y91 FFMUXE1 OUT1
         }] belPin  SLICE_X90Y91 EFF D
============================================================
```

In this example `np.py` is invoked on the netlist `vtr_mcml_rwroute.phys` (This
netlist that can be generated from a global `make`,
see [the contest website](https://xilinx.github.io/fpga24_routing_contest/index.html))
in order to print out the net named `u_calc/boundaryChecker/r_ux__57_reg[21]_srl27___u_calc_dropSpin_photon29_o_sleftz_reg_r_n_0`.
Since this is a fully routed net the output shows one source (`Source: 0`) and
no stubs. Following the source is a list of all of the FPGAIF
routeSegments in the route tree. Much like Vivado's `report_route_status` command, the symbol `[{` indicates the root of a new tree.
The symbol `{` indicates the beginning of a branch and the symbol `}` indicates
the end of a branch. Finally, the symbol `}]` indicates the end of the tree.

Each line of ouput displays all of the fields in the [FPGAIF routeSegment](https://github.com/chipsalliance/fpga-interchange-schema/blob/c985b4648e66414b250261c1ba4cbe45a2971b1c/interchange/PhysicalNetlist.capnp#L104).
In each line the first column is the type of object (e.g. one of `belPin`,
`sitePin`, `pip`, `sitePip`). The second column is the location of the object
(e.g. one of `site` or `tile`). Finally, the remaining columns differ depending
on object type but correspond exactly to fields in the FPGAIF schema.

In the example above we see that the first routeSegment in the tree is:
```
belPin  SLICE_X84Y94 C6LUT O6
```
which is immediately followed by a branch containing the routeSegments:
```
belPin  SLICE_X84Y94 OUTMUXC D6
sitePIP SLICE_X84Y94 OUTMUXC D6 False
belPin  SLICE_X84Y94 OUTMUXC OUT
belPin  SLICE_X84Y94 CMUX CMUX
sitePin SLICE_X84Y94 CMUX
```
Before we return to the main branch:
```
belPin  SLICE_X84Y94 C_O C_O
sitePin SLICE_X84Y94 C_O
```

Thus, if you were to draw the first part of the above tree it would look like:
```
(belPin  SLICE_X84Y94 C6LUT O6)------------+
           |                               |
           V                               V
(belPin  SLICE_X84Y94 C_O C_O)  (belPin  SLICE_X84Y94 OUTMUXC D6)
           |                               |
           V                               V
(sitePin SLICE_X84Y94 C_O)      (sitePIP SLICE_X84Y94 OUTMUXC D6 False)
           |                               |
           V                               V
          ...                   (belPin  SLICE_X84Y94 OUTMUXC OUT)
                                           |
                                           V
                                (belPin  SLICE_X84Y94 CMUX CMUX)
                                           |
                                           V
                                (sitePin SLICE_X84Y94 CMUX)
```

`np.py` can also print out unrouted nets, for example:
```
$ python3 np.py ../vtr_mcml_unrouted.phys u_calc/boundaryChecker/r_ux__57_reg[21]_srl27___u_calc_dropSpin_photon29_o_sleftz_reg_r_n_0
============================================================
Route tree for net: u_calc/boundaryChecker/r_ux__57_reg[21]_srl27___u_calc_dropSpin_photon29_o_sleftz_reg_r_n_0

    Source: 0
    [{      belPin  SLICE_X84Y94 C6LUT O6
     {      belPin  SLICE_X84Y94 OUTMUXC D6
            sitePIP SLICE_X84Y94 OUTMUXC D6 False
         }  belPin  SLICE_X84Y94 OUTMUXC OUT
            belPin  SLICE_X84Y94 C_O C_O
         }] sitePin SLICE_X84Y94 C_O

    Stub: 0
    [{      sitePin SLICE_X90Y91 EX
            belPin  SLICE_X90Y91 EX EX
            belPin  SLICE_X90Y91 FFMUXE1 BYP
            sitePIP SLICE_X90Y91 FFMUXE1 BYP False
            belPin  SLICE_X90Y91 FFMUXE1 OUT1
         }] belPin  SLICE_X90Y91 EFF D
============================================================
```

This is the same net as in the first example, however no inter-site routing (using PIPs)
has been done. As a result we see a source and a stub. `Source: 0` shows the
intra-site routing leading from the net's driver and `Stub: 0` shows the intra-site routing
leading into the net's sink. This example shows a net with only one sink for simplicity,
but a net may have many sinks. Printing such an unrouted net would produce a
list of stubs.

Finally, note that `np.py` can be invoked with a list of net names (which will
print them one after the other) and that the names provided must exactly match
the net names in the `*.phys`.
