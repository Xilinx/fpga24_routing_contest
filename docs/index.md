# Runtime-First FPGA Interchange Routing Contest @ [FPGA'24](https://www.isfpga.org/)

## The Challenge

Given a pre-placed design in the [FPGA Interchange Format](https://fpga-interchange-schema.readthedocs.io)
and a multi-core machine with an AMD GPU, build a router that focuses on minimizing the wall-clock time required to return
a legal, fully routed solution.

## Introduction

Compilation times for FPGA technology have long been a pain point, compounded by the trend that FPGA devices are only
getting bigger.
Routing is one of the last steps of this compilation flow, involving the search for a set of non-overlapping paths
through the FPGA's routing graph connecting all source pins to all sink pins.
Since processor core counts continue to grow rapidly (the latest AMD EPYC processors have up to 128 cores in a single
socket) alongside the evolution of GPU technology, can a FPGA router be built to take advantage of all this compute?

As most FPGA vendor tools are provided as closed-source binaries, it can be difficult to innovate
at the backend (i.e. place and route) with many researchers resorting to evaluating their algorithms on theoretical
rather than commercial architectures.
To lower the barrier and cost to future innovation, in this contest we use the open-source
[FPGA Interchange Format](https://fpga-interchange-schema.readthedocs.io) (FPGAIF) as the intermediate representation
for device model and design exchange.

**The goals of this contest are:**
1. To promote and demonstrate the [FPGA Interchange Format](https://fpga-interchange-schema.readthedocs.io) as an
   efficient and robust intermediate representation for working on backend FPGA problems --- even at industrial scales.
2. To encourage innovation in FPGA routing algorithms that prioritize runtime, a metric that can be especially
   important in some application domains such as ASIC emulation.


To this end, the biggest component of the contest score will be wall-clock time (in contrast to user-CPU time, which
is the time that each CPU core was busy summed across all cores).
*In other words: we'll provide the (AMD) CPU cores and the GPUs -- use them or lose them!*

Developed as part of the [CHIPS Alliance](https://www.chipsalliance.org/), the open-source
[FPGA Interchange Format](https://fpga-interchange-schema.readthedocs.io) (FPGAIF) can describe
(a) the layout of all available device resources present on an FPGA,
(b) the hierarchical logical netlist produced post-synthesis, and
(c) the flat physical netlist capturing how and where each FPGA resource is configured/placed
and how they are connected/routed together.
The overarching vision for the FPGAIF is to act as the intermediate representation for a
common set of FPGA tools -- fundamentally, the placement and routing problems across many devices
share many similarities -- as well as efficient mix-and-matching from different tool stacks.

The input and output of a competing router will be an FPGAIF physical netlist, as shown below:
[![image](flow-simple.png)](flow-simple.png)
More information can be found in [Contest Details](details.html).



## Important Dates

|Date | |
|-----------------|-------|
|September 2023   | Contest Announced |
|20 October 2023  | Registration Deadline ([mandatory, see below](#registration))|
|20 December 2023 | Alpha Submission (details to be announced)|
|31 January 2024  | Final Submission (details to be announced)|
|3-5 March 2024   | Prizes awarded to top 5 teams at [FPGA 2024 conference](https://www.isfpga.org/)|

Deadlines refer to Anywhere On Earth.

## Prizes 

Prizes will be awarded to the top 5 finalists:

| Rank | Prize (USD) |
|------|-------------|
| 1st  | **$2500** |
| 2nd  | **$1500** |
| 3rd  | **$1000** |
| 4th & 5th | **$500** |

Prize amounts subject to change.

***Note 1:*** *50% of the prize money is conditional on the winning entry being made open source under a permissive license (BSD, MIT, Apache) within 30 days of award announcement. This is to encourage participants to help the FPGA backend community and ecosystem grow faster.*  
***Note 2:*** *Applicable taxes may be assessed on and deducted from award payments, subject to U.S. and/or local government policies.*

## Registration 

Contest registration is mandatory to be eligible for alpha submission and final prizes. To register, please [send an email](mailto:eddie.hung@amd.com) with the following information:
* Subject: `FPGA24 Contest Registration`
* Body:
  ```
  Team name: <TEAM NAME>
  Team members and affiliation:
    <NAME> (<AFFILIATION>)
    <NAME> (<AFFILIATION>)
  Advising Professor (if applicable): <NAME> (<AFFILIATION>)
  Single corresponding email: <NAME@AFFILIATION.COM>
  ```

A Vivado license is not mandatory for router development, however, eligible teams from academia can ask their advising professor to register through the export compliant [Xilinx University Program](https://www.xilinx.com/support/university/donation-program.html) for a license. See [Contest Details](details.html) for more details on how Vivado is used in this contest.

## Disclaimer

The organizers reserve the rights to revise or modify any aspect of this contest at any time.
