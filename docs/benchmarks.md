# Benchmark Details

This page describes the suite of benchmark designs that are used to assess
routing performance. The full list of benchmark designs, along with links to
the original sources and some utilization numbers is provided in the following
table:

|Source Benchmark Suite|Benchmark Name|LUTs|FFs|DSPs|BRAMs|OOC [1]|
|----------------------|--------------|----|---|----|-----|-------|
| [LogicNets](https://github.com/Xilinx/logicnets)                                                                        |`jscl` (Jet Substructure Classification L)         |31k |2k  |0   |0  |Y   |
| [BOOM](https://docs.boom-core.org/en/latest/sections/intro-overview/boom.html)                                          |`med_pb` (MediumBoomConfig with area constraint)   |36k |17k |24  |142|N   |
| [VTR](https://docs.verilogtorouting.org/en/latest/vtr/benchmarks/#vtr-benchmarks)                                       |`mcml`                                             |43k |15k |105 |142|Y   |
| [Rosetta](https://github.com/cornell-zhang/rosetta)                                                                     |`fd` (face-detection)                              |46k |39k |72  |62 |Y   |
| [Corundum](https://github.com/corundum/corundum)                                                                        |`25g` (ADM_PCIE_9V3 25G)                           |73k |96k |0   |221|N   |
| [FINN](https://github.com/Xilinx/finn)                                                                                  |`radioml`                                          |74k |46k |0   |25 |Y   |
| [VTR](https://github.com/verilog-to-routing/vtr-verilog-to-routing/blob/master/vtr_flow/benchmarks/verilog/LU64PEEng.v) |`lu64peeng`                                        |90k |36k |128 |303|Y   |
| [CoreScore](https://github.com/olofk/corescore)                                                                         |`500` (500 SERV cores)                             |96k |116k|0   |250|N   |
| [CoreScore](https://github.com/olofk/corescore)                                                                         |`500_pb` (500 SERV cores with area constraint)     |96k |116k|0   |250|N   |
| [MLCAD](https://mlcad-workshop.org/1st-mlcad-contest/)                                                                  |`d181_lefttwo3rds` (left two thirds of Design 181) |155k|203k|1344|405|N[2]|
| [Koios 2.0](https://docs.verilogtorouting.org/en/latest/vtr/benchmarks/#koios-2-0-benchmarks)                           |`dla_like_large` (dla_like.large)                  |189k|362k|2209|192|Y   |
| [BOOM](https://docs.boom-core.org/en/latest/sections/intro-overview/boom.html)                                          |`soc` (LargeBoomConfig)                            |227k|98k |61  |161|Y   |
| [ISPD 2016](https://www.ispd.cc/contests/16/ispd2016_contest.html)                                                      |`example2`                                         |289k|234k|200 |384|N   |

[1] OOC refers to [Out-Of-Context Synthesis](https://docs.xilinx.com/r/en-US/ug949-vivado-design-methodology/Out-of-Context-Synthesis),
whereby the benchmark is not compiled as a top-level module and thus will not have I/O buffers inserted on its top-level ports.
As a consequence, these top-level ports are nets that require no routing, and where the clock net is also derived from such a top-level
port, this net (which would otherwise be promoted to use the global routing network) will not require routing either.

[2] The original design is in context, and all I/Os in the original design were
preserved when 'cutting out' the 2/3rds. However, the cut out part is now out
of context, since everything that was left undriven because of the deleted
third became an out of context port.

Each of the benchmarks targets the `xcvu3p` device which has the following resources:

|LUTs|FFs |DSPs|BRAMs|
|----|----|----|-----|
|394k|788k|2280|720  |

Throughout the contest framework design files associated with
the benchmarks are named as follows:

```
<source benchmark suite>_<benchmark name>_<file description>.<file extension>
```

For example the file name `vtr_mcml_unrouted.phys` denotes an unrouted FPGAIF
Physical Netlist corresponding to the `mcml` design from the VTR benchmark
suite.

More benchmarks may be released as the contest progresses.
Entrants will also be evaluated on a set of hidden benchmarks which will not be made public.

