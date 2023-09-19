# Benchmarks

This page describes the suite of benchmark designs that are used to assess
routing performance. The full list of benchmark designs, along with links to
the original sources and some basic statistics is provided in the following
table:

|Source Benchmark Suite|Benchmark Name|LUTs|FFs|DSPs|BRAMs|
|----------------------|--------------|----|---|----|-----|
| [VTR](https://docs.verilogtorouting.org/en/latest/vtr/benchmarks/#vtr-benchmarks)|`mcml`|43k|15k|105|142|
| [Rosetta](https://github.com/cornell-zhang/rosetta)|`fd` (face-detection)|46k|39k|72|62|
| [Koios 2.0](https://docs.verilogtorouting.org/en/latest/vtr/benchmarks/#koios-2-0-benchmarks)|`dla_like_large` (dla_like.large)|189k|362k|2209|192|
| [ISPD 2016](https://www.ispd.cc/contests/16/ispd2016_contest.html)|`example2`|289k|234k|200|384|
| [BOOM](https://docs.boom-core.org/en/latest/sections/intro-overview/boom.html)|`soc`|227k|98k|61|161|

Each of the benchmarks targets the `xcvu3p` device wich has the following statistics:
|LUTs  |FFs   |DSPs|BRAMs|
|------|------|----|-----|
|394080|788160|2280|720  |

Throughout the contest framework design files associated with
the benchmarks are named as follows:

```
<source benchmark suite>_<benchmark name>_<file description>.<file extension>
```

For example the file name `vtr_mcml_unrouted.phys` denotes an unrouted FPGAIF
Physical Netlist corresponding to the `mcml` design from the VTR benchmark
suite.


