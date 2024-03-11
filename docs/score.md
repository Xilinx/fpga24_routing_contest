# Scoring Criteria
Teams will be scored as follows:

1. After running each team's submission on each benchmark in the suite of
   hidden evaluation benchmarks, compute a score according to:
   - Benchmark Score = 0.9 * Wall Clock Runtime + 0.1 * [Critical-Path Wirelength](#critical-path-wirelength)
   - Lower scores are better
   - Each team's submission will be run multiple times, and the lowest score
     will be taken
   - If a submitted router fails to pass `CheckPhysNetlist` then a score of infinity will be assigned for that benchmark
2. For each benchmark rank all teams based on their score
   - If multiple teams achieve an identical score (e.g. `inf`) assign the same rank to each
3. For each team compute the arithmetic mean of all rankings
   - Lower mean ranking is better
4. Sort teams by mean ranking, and assign prizes in ascending order

> ℹ️ **NOTE**  
> The contest organizers reserve the right to disqualify poorly performing routers.

An implementation of the above scoring algorithm is provided in the
[scoring_formula](https://github.com/Xilinx/fpga24_routing_contest/tree/master/scoring_formula)
directory of the competition GitHub repository, along with a series of test
cases that illustrate how the algorithm will rank teams in a variety of
scenarios.

Over time, we plan to release a number of additional public benchmarks on which
all competing routers will be evaluated. Contestants will also be evaluated on
a set of hidden benchmarks which will not be made public until after the contest
has concluded.

## Critical-Path Wirelength

A small component of the score will be assigned based on
"Critical-Path Wirelength". Critical-Path Wirelength is defined as the
wirelength of the longest combinatorial path present in a routed Physical
Netlist. This metric is an easy to compute proxy for the Critical-Path Delay
considered by timing driven routers (such as Vivado). The goal of including
Critical-Path Wirelength in the scoring criteria is twofold: first, it
encourages competitors to not completely sacrifice quality of results in favour
of runtime, and second, it will serve as a means to differentiate between
solutions with similar wall clock times.

Similar to static timing analysis, a path in this context is a collection of
cells separated by nets:
```
cell 1 -> net 1 -> cell 2 -> net 2 -> cell 3 -> ...
```
Within an FPGAIF Physical Netlist, each cell is placed onto a physical resource
called a Basic Element of Logic or BEL. Thus, each physical net along the path
starts at a BEL output pin and terminates at one or more BEL input pins.

Each routed physical net is composed of FPGAIF routeSegments. The wirelength
between a BEL output pin and a BEL input pin is simply the sum of the
wirelength of every routeSegment that must be traced through to reach the input
from the output.
For the purposes of the contest, only routeSegments of the type `pip` can
affect the wirelength.
In almost all cases, these `pip` routeSegments exist in interconnect
tiles (which have names starting with the `INT` prefix) and are the only way for
signals to be routed between non-interconnect tiles.
Since `pip`s are the only type of routeSegment that can connect multiple tiles, all other types of
routeSegment (`belPin`, `sitePin`, `sitePIP`) are assumed to have a wirelength
of zero. Thus for a portion of a path that looks like this:
```
output belPin -> ... -> pip1 -> pip2 -> ... -> pipN -> ... -> input belPin
      0           0      w       x       y       z      0          0
```
The wirelength from the output to the input would be `w+x+y+z`.

Each `pip` represents a connection that causes `wire0` to drive `wire1`;
such connections incur a wirelength score based on the type of wire indicated
by `wire1`. The following table presents regular expression patterns to be
matched against the `wire1` name of PIPs with a tile name prefix of `INT`
and its associated wirelength score.

| Wire Type         | Regex Pattern           | Wirelength Score |
|-------------------|-------------------------|------------------|
| Single Horizontal |`[EW]{2}1_[EW]_BEG[0-7]`<br>`WW1_E_7_FT0` |1<br>1|
| Single Vertical   |`[NS]{2}1_[EW]_BEG[0-7]` |                 1|
| Double Horizontal |`[EW]{2}2_[EW]_BEG[0-7]` |                 5|
| Double Vertical   |`[NS]{2}2_[EW]_BEG[0-7]` |                 3|
| Quad Horizontal   |`[EW]{2}4_[EW]_BEG[0-7]` |                10|
| Quad Vertical     |`[NS]{2}4_[EW]_BEG[0-7]` |                 5|
| Long Horizontal   |`[EW]{2}12_BEG[0-7]`     |                14|
| Long Vertical     |`[NS]{2}12_BEG[0-7]`     |                12|
| All others (e.g. Bounce) | (no matches above) |               0|

Each of the wirelength scores in the previous table are taken from Table 1 in
[An Open-source Lightweight Timing Model for RapidWright](https://www.rapidwright.io/docs/_downloads/6610b931d8a2e053e69a499d3923077f/FPT19-TimingModel.pdf);
our wirelength model can be considered a further simplification of this prior model
by omitting all logic cell delays, as well as omitting the intrinsic delay constant (k<sub>0</sub>)
and considerations for grid discontinuities (k<sub>2</sub>) from net delays.
Thus, despite being dimensionless, the score produced by the wirelength
analyzer should correlate with the net delay reported by a timing analyzer for
the same path.

Next, let us consider how paths are formed from sequences of nets. BELs in an
FPGA can be made up of combinatorial logic -- where a change in the value at a
BEL input pin has the potential to immediately alter the value at the
corresponding BEL output pin, e.g. a lookup table. Alternatively, BELs may be
sequential -- where a change in the value at a BEL input will only be reflected
at the BEL output after a clock event. Finally,  BELs may have input pins that
have a mix of combinatorial and sequential effects. Where a combinatorial
connection between a BEL input and output pin exists, the nets associated with
those pins form a path. If no such combinatorial connection exists then one
path terminates at the input pin and a new path begins at the output pin. The
following tables describe the combinatorial connectivity that exists between
BEL input and output pins for each type of PhysCell.

| Cell Type                                                                                | Connectivity <br> (BEL output pin(s) <- BEL input pin(s)) | Description |
|------------------------------------------------------------------------------------------|-------------------------------|--------------------|
|`FDRE`, `FDCE`, `FDSE`, `FDPE`                                                            | (none) <- (none)              | Flip-flop          |
|`SRL16E`                                                                                  | `O5` and `O6` <- `A0` to `A3` | Shift Register     |
|`SRLC32E`                                                                                 | `O6` <- `A0` to `A4`          | Shift Register     |
|`RAMD32`, `RAMS32`                                                                        | `O5` and `O6` <- `A0` to `A4` | Distributed Memory |
|`RAMD64E`, `RAMS64E`                                                                      | `O6` <- `A0` to `A5`          | Distributed Memory |
|`RAMB36E2`, `RAMB18E2`                                                                    | (none) <- (none)              | Block Memory       |
|`URAM288`                                                                                 | (none) <- (none)              | UltraRAM Memory    |
|`MMCME4_ADV`                                                                              | (none) <- (none)              | Clock Manager      |
|`LUT1`, `LUT2`, `LUT3`, `LUT4`, `LUT5`, `LUT6`                                            | (all) <- (all)                | Look Up Table      |
|`CARRY8`                                                                                  | [see table CARRY8](#carry8-connectivity) | Fast Carry Logic |
|`MUXF7`, `MUXF8`, `MUXF9`                                                                 | (all) <- (all)                | Intrasite Mux      |
|`IBUFCTRL`, `INBUF`, `OBUFT`, `DIFFINBUF`, `IBUFDS_GTE4`                                  | (all) <- (all)                | I/O Buffer         |
|`DSP_A_B_DATA`, `DSP_C_DATA`, `DSP_M_DATA`,<br>`DSP_PREADD_DATA`, `DSP_OUTPUT`, `DSP_ALU` | (none) <- (none) [see note](#dsp-cell-connectivity) | DSP Logic |
|`DSP_MULTIPLIER`, `DSP_PREADD`                                                            | (all) <- (all) [see note](#dsp-cell-connectivity) | DSP Logic |
|`PCIE40E4`                                                                                | (none) <- (none)              | PCIe Hard Macro    |
|`GTYE4_CHANNEL`,`GTYE4_COMMON`                                                            | (none) <- (none)              | Gigabit Transceiver Components |
|`STARTUPE3`,`ICAPE3`                                                                      | (none) <- (none)              | Device Configuration Components |

### CARRY8 Connectivity
| BEL output pin | BEL input pins                     |
|------------|----------------------------------------|
| `O0`       | `CIN`, `S0`                            |
| `CO0`      | {input pins from `O0`} and `DI0`, `AX` |
| `O1`       | {input pins from `CO0`} and `S1`       |
| `CO1`      | {input pins from `O1`} and `DI1`, `BX` |
| `O2`       | {input pins from `C01`} and `S2`       |
| `CO2`      | {input pins from `O2`} and `DI2`, `CX` |
| `O3`       | {input pins from `CO2`} and `S3`       |
| `CO3`      | {input pins from `O3`} and `DI3`, `DX` |
| `O4`       | {input pins from `CO3`} and `S4`       |
| `CO4`      | {input pins from `O4`} and `DI4`, `EX` |
| `O5`       | {input pins from `CO4`} and `S5`       |
| `CO5`      | {input pins from `O5`} and `DI5`, `FX` |
| `O6`       | {input pins from `CO5`} and `S6`       |
| `CO6`      | {input pins from `O6`} and `DI6`, `GX` |
| `O7`       | {input pins from `CO6`} and `S7`       |
| `CO7`      | {input pins from `O7`} and `DI7`, `HX` |

### DSP Cell Connectivity
DSP cells are unique in that they can be configured with a number of internal
pipelining registers that can make them fully combinatorial, fully sequential,
or a mix of both. Further, the register configuration is only captured in the
FPGAIF Logical Netlist which is beyond the scope of this routing contest. For
this reason we optimistically assume that all DSP cells with pipelining
registers are configured such that they can be treated as fully sequential.
