# FPGA Interchange Format Physical Netlist Wirelength Analyzer `wa.py`
For this competition a custom open-source wirelength analyzer, called `wa.py`
has been written in Python and leverages the NetworkX graph library. The basic
usage of this tool is:

```
python3 wa.py [-h] [-v VERBOSITY] [--mode MODE] physical_netlist
```

The tool has three levels of verbosity and can operate in three different
modes. The most basic form of operation is to simply supply the tool with the
path to a routed Physical Netlist:

```
$ python3 wa.py ../vtr_mcml_rwroute.phys
Building Graph
Loaded Physical Netlist in: 0.6s
Added nets to graph in: 28.6s

Finding Critical Path:
Joined nets in: 8.0s
============================================================
Routing path for Critical Path
Wirelength: 663
Segment | Running |
Length  |  Total  | Segment Name
--------+---------+-----------------------------------------
        |        0| cell    u_calc/dropSpin/scattererReflector/squareRoot1_6/res__3_q_reg[40]
       0|         | belPin  SLICE_X71Y84 AFF Q (start of net: u_calc/dropSpin/scattererReflector/squareRoot1_6/res__3_q[40])
      46|         | ...
       0|         | belPin  SLICE_X69Y92 CARRY8 AX
        |       46| cell    u_calc/dropSpin/scattererReflector/squareRoot1_6/op__7_q_reg[63]_i_376__0
       0|         | belPin  SLICE_X69Y92 CARRY8 CO7 (start of net: u_calc/dropSpin/scattererReflector/squareRoot1_6/op__7_q_reg[63]_i_376__0_n_0)
       0|         | ...
       0|         | belPin  SLICE_X69Y93 CARRY8 CIN
        |       46| cell    u_calc/dropSpin/scattererReflector/squareRoot1_6/op__7_q_reg[63]_i_283__0
       0|         | belPin  SLICE_X69Y93 CARRY8 O0 (start of net: u_calc/dropSpin/scattererReflector/squareRoot1_6/op__42[48])
      52|         | ...
       0|         | belPin  SLICE_X70Y94 A6LUT A2
        |       98| cell    u_calc/dropSpin/scattererReflector/squareRoot1_6/op__7_q[63]_i_188__0
<Truncated for brevity>
```

By default the tool runs in `critical-path` mode with verbosity level 1. As
seen above this produces a table describing the path with the longest
wirelength. The header of the table includes the total wirelength of
the critical path, in the example above this is 663. All wirelength numbers
reported by `wa.py` are dimensionless scores, for further detail about how
these scores are computed and a description of the wirelength analyzer's
algorithm see the [Scoring Criteria page](https://xilinx.github.io/fpga24_routing_contest/score.html).
Each subsequent line in the table corresponds to one or more FPGA Interchange
Format routeSegments, or combinatorial logic cells. The first column (`Segment
Length`) contains the wirelength of the routeSegments. The second column
(`Running Total`) contains the running total wirelength and is indicated at
every cell along the path. The final column (`Segment Name`) shows the name of
the routeSegment or cell. For routeSegments that are the source of a net the
name of the net is also indicated in the third column. At verbosity level 1 The
detailed routing between cells is hidden, and `...` is printed to indicate that
this line corresponds to many routeSegments. Running the previous example with
verbosity level 2 produces the following output:

```
$ python3 wa.py .. /vtr_mcml_rwroute.phys -v=2
Building Graph
Loaded Physical Netlist in: 0.6s
Added nets to graph in: 28.5s

Finding Critical Path:
Joined nets in: 8.2s
============================================================
Routing path for Critical Path
Wirelength: 663
Segment | Running |
Length  |  Total  | Segment Name
--------+---------+-----------------------------------------
        |        0| cell    u_calc/dropSpin/scattererReflector/squareRoot1_6/res__3_q_reg[40]
       0|         | belPin  SLICE_X71Y84 AFF Q (start of net: u_calc/dropSpin/scattererReflector/squareRoot1_6/res__3_q[40])
       0|         | belPin  SLICE_X71Y84 AQ AQ
       0|         | sitePin SLICE_X71Y84 AQ
       0|         | pip     INT_X46Y84 LOGIC_OUTS_E14 INT_NODE_SDQ_17_INT_OUT0 True False
       5|         | pip     INT_X46Y84 INT_NODE_SDQ_17_INT_OUT0 EE2_E_BEG3 True False
       0|         | pip     INT_X47Y84 EE2_E_END3 INT_NODE_SDQ_14_INT_OUT0 True False
       3|         | pip     INT_X47Y84 INT_NODE_SDQ_14_INT_OUT0 NN2_E_BEG2 True False
       0|         | pip     INT_X47Y86 NN2_E_END2 INT_NODE_SDQ_13_INT_OUT0 True False
      10|         | pip     INT_X47Y86 INT_NODE_SDQ_13_INT_OUT0 WW4_E_BEG2 True False
      12|         | pip     INT_X45Y86 WW4_E_END2 NN12_BEG3 True False
       0|         | pip     INT_X45Y98 NN12_END3 INT_NODE_SDQ_12_INT_OUT0 True False
       1|         | pip     INT_X45Y98 INT_NODE_SDQ_12_INT_OUT0 NN1_E_BEG2 True False
       0|         | pip     INT_X45Y99 NN1_E_END2 INT_NODE_SDQ_8_INT_OUT0 True False
       1|         | pip     INT_X45Y99 INT_NODE_SDQ_8_INT_OUT0 EE1_E_BEG1 True False
       0|         | pip     INT_X46Y99 EE1_E_END1 INT_NODE_SDQ_53_INT_OUT0 True False
       1|         | pip     INT_X46Y99 INT_NODE_SDQ_53_INT_OUT0 SS1_W_BEG1 True False
       0|         | pip     INT_X46Y98 SS1_W_END1 INT_NODE_SDQ_50_INT_OUT0 True False
       0|         | pip     INT_X46Y98 INT_NODE_SDQ_50_INT_OUT0 INT_INT_SDQ_60_INT_OUT1 True False
       0|         | pip     INT_X46Y98 INT_INT_SDQ_60_INT_OUT1 INT_NODE_SDQ_1_INT_OUT0 True False
       3|         | pip     INT_X46Y98 INT_NODE_SDQ_1_INT_OUT0 SS2_E_BEG0 True False
       0|         | pip     INT_X46Y96 SS2_E_END0 INT_NODE_SDQ_22_INT_OUT0 True False
       5|         | pip     INT_X46Y96 INT_NODE_SDQ_22_INT_OUT0 SS4_E_BEG0 True False
       0|         | pip     INT_X46Y91 SS4_E_BLS_0_FT0 SDQNODE_E_93_FT0 True False
       5|         | pip     INT_X46Y92 SDQNODE_E_BLN_93_FT1 WW2_E_BEG0 True False
       0|         | pip     INT_X45Y91 WW2_E_BLS_0_FT0 INODE_E_62_FT0 True False
       0|         | pip     INT_X45Y92 INODE_E_BLN_62_FT1 BOUNCE_E_0_FT1 True False
       0|         | sitePin SLICE_X69Y92 AX
       0|         | belPin  SLICE_X69Y92 AX AX
       0|         | belPin  SLICE_X69Y92 CARRY8 AX
        |       46| cell    u_calc/dropSpin/scattererReflector/squareRoot1_6/op__7_q_reg[63]_i_376__0
<Truncated for brevity>
```

As seen above at this level of verbosity the `...` is replaced with the detailed
path taken between two cells. The lowest verbosity level, level 0, prints the
total wirelength and omits all other output.

The second mode, `longest-single-net` mode, produces an identical output at
each level of verbosity, except that the path printed is the longest that is
contained entirely in a single net. Finally, the third mode, `both` simply runs
`longest-single-net` mode and then `critical-path` mode consecutively.
