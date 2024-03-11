# Benchmark Details

This page describes the suite of benchmark designs that are used to assess
routing performance. The full list of benchmark designs, along with links to
the original sources and some utilization numbers is provided in the following
tables:

## Benchmarks published during contest

Available from [https://github.com/Xilinx/fpga24_routing_contest/releases/latest/download/benchmarks.tar.gz](https://github.com/Xilinx/fpga24_routing_contest/releases/latest/download/benchmarks.tar.gz)

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
| [MLCAD 2023](https://mlcad-workshop.org/1st-mlcad-contest/)                                                             |`d181_lefttwo3rds` (left two thirds of Design 181) |155k|203k|1344|405|N[2]|
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

## Benchmarks used for final evaluation

Available from [https://github.com/Xilinx/fpga24_routing_contest/releases/latest/download/benchmarks-evaluation.tar.gz](https://github.com/Xilinx/fpga24_routing_contest/releases/latest/download/benchmarks-evaluation.tar.gz)

|Source Benchmark Suite|Benchmark Name|LUTs|FFs|DSPs|BRAMs|OOC [1]|
|----------------------|--------------|----|---|----|-----|-------|
| [RapidWright](https://github.com/Xilinx/RapidWright)                                                                    |`picoblaze_array` (660 PicoBlaze cores)                |76k |77k  |0   |0  |Y   |
| [Corundum](https://github.com/corundum/corundum)                                                                        |`100g` (ADM_PCIE_9V3 25G)                              |76k |104k |0   |290|N   |
| [Koios 2.0](https://docs.verilogtorouting.org/en/latest/vtr/benchmarks/#koios-2-0-benchmarks)                           |`clstm_like_large` (clstm_like.large)                  |89k |184k |1289|370|Y   |
| [Titan23](https://docs.verilogtorouting.org/en/latest/vtr/benchmarks/#titan-benchmarks)                                 |`orig_gsm_x6` (Original gsm_switch replicated 6 times) |133k|160k |0   |432|Y   |
| [CoreScore](https://github.com/olofk/corescore)                                                                         |`900` (900 SERV cores)                                 |174k|210k |0   |451|N   |
| [Koios 2.0](https://docs.verilogtorouting.org/en/latest/vtr/benchmarks/#koios-2-0-benchmarks)                           |`dla_like_large_v2` (dla_like.large, different placement)|189k|363k |2209|192|Y   |
| [FINN](https://github.com/Xilinx/finn)                                                                                  |`mobilenetv1`                                          |202k|140k |48  |562|Y   |
| [ISPD 2016](https://www.ispd.cc/contests/16/ispd2016_contest.html)                                                      |`fpga03`                                               |214k|168k |500 |590|N   |
| [MLCAD 2023](https://mlcad-workshop.org/1st-mlcad-contest/)                                                             |`d181` (Design 181)                                    |229k|303k |1824|576|N   |
| [BOOM](https://docs.boom-core.org/en/latest/sections/intro-overview/boom.html)                                          |`soc_v2` (LargeBoomConfig, different placement)        |229k|99k  |61  |161|Y   |
| [CoreScore](https://github.com/olofk/corescore)                                                                         |`1200` (1200 SERV cores)                               |233k|280k |0   |601|N   |
| [ISPD 2016](https://www.ispd.cc/contests/16/ispd2016_contest.html)                                                      |`example2_v2` (example2, different placement)          |254k|234k |200 |384|N   |
| [CoreScore](https://github.com/olofk/corescore)                                                                         |`1500` (1500 SERV cores)                               |292k|350k |0   |720|N   |
| [Titan23](https://docs.verilogtorouting.org/en/latest/vtr/benchmarks/#titan-benchmarks)                                 |`orig_dart_x4` (Original dart replicated 4 times)      |299k|176k |0   |0  |Y   |
| [CoreScore](https://github.com/olofk/corescore)                                                                         |`1700` (1700 SERV cores)                               |344k|399k |0   |720|N   |

## Details

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
