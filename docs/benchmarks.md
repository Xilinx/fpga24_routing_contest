# Benchmark Details

This page describes the suite of benchmark designs that are used to assess
routing performance. The full list of benchmark designs, along with links to
the original sources and some utilization numbers is provided in the following
table:

|Source Benchmark Suite|Benchmark Name|LUTs|FFs|DSPs|BRAMs|OOC [1]|
|----------------------|--------------|----|---|----|-----|-------|
| [VTR](https://docs.verilogtorouting.org/en/latest/vtr/benchmarks/#vtr-benchmarks)|`mcml`|43k|15k|105|142|Y|
| [Rosetta](https://github.com/cornell-zhang/rosetta)|`fd` (face-detection)|46k|39k|72|62|Y|
| [Koios 2.0](https://docs.verilogtorouting.org/en/latest/vtr/benchmarks/#koios-2-0-benchmarks)|`dla_like_large` (dla_like.large)|189k|362k|2209|192|Y|
| [ISPD 2016](https://www.ispd.cc/contests/16/ispd2016_contest.html)|`example2`|289k|234k|200|384|N|
| [BOOM](https://docs.boom-core.org/en/latest/sections/intro-overview/boom.html)|`soc` (LargeBoomConfig)|227k|98k|61|161|Y|

[1] OOC refers to [Out-Of-Context Synthesis](https://docs.xilinx.com/r/en-US/ug949-vivado-design-methodology/Out-of-Context-Synthesis),
whereby the benchmark is not compiled as a top-level module and thus will not have I/O buffers inserted on its top-level ports.
As a consequence, these top-level ports are nets that require no routing, and where the clock net is also derived from such a top-level
port, this net (which would otherwise be promoted to use the global routing network) will not require routing either.

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


