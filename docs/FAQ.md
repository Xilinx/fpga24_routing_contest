# Frequently Asked Questions


## Team Questions

### Can undergraduate students not in our research lab be part of a team?

Yes.

### Can recent graduates qualify to be members of a team?

Yes, being a student is not a requirement.

### Is there a constraint on the number of team members?

Currently, the team limit is 6 members (not counting the advisor(s)).

### Can the team have two advisors?

Yes.

### Can we have more than one team?

Yes, as long as team members belong exclusively to a single team.  However, advisors can advise more than one team.

### Can we collaborate with another University as a single team for the contest?

Yes.

## Contest Objective Questions

### The main objective of the contest appears to optimizing routing speed. However, should the router be timing-driven or wire-length driven? More specifically, should the criticality of nets be computed within the router to influence routing order?

Indeed, the biggest focus of this contest is on producing a legal solution within the shortest possible wall-clock time. A secondary, smaller, component of the score is to optimize the critical-path (not the total) wirelength. This metric is similar to the critical-path delay that a timing-driven router would be expected to optimize for, but instead of considering the path with the maximum total logic and net delay from a timing startpoint to a timing endpoint (including through combinatorial elements such as LUTs) only the path with the maximum total net wirelength is considered. The intention is for critical-path wirelength to be much easier to compute. For further details about Critical-Path Wirelength refer to the [Scoring Criteria](score.html#critical-path-wirelength) webpage.

### Can we use existing routers (i.e., VPR Pathfinder) as a starting point or should the team build a custom router from scratch.

Yes, any existing solutions or solutions built from scratch and/or derived from prior work are welcome.

### How are we going to be evaluated and ranked against other contestants?

All team solutions will be measured using the same criteria, hardware platform, and constraints.  Detailed information about how solutions will be scored and how teams will be ranked is available on the [Scoring Criteria](score.html) webpage.

### Can teams change the placement solution provided to improve the running time of the router?

The placement of the designs must remain fixed and can not be changed as part of the routing solution. Any placement changes will flag a result as being not legal and will not be considered.  There will likely be some flexibility around LUT input permutations, but details are still forthcoming.

### Must the router be iterative, or will an mixed-integer programming solver be made available to support concurrent routing approaches?

Any router provided that generates a legal solution will be accepted.  We welcome a diversity of approaches.

## Approach and Technique Questions

### Transformative technologies, like ML and DL, require large amounts of training data. Will you be providing training data to enable such approaches, or are you only interested in traditional algorithmic approaches?

We welcome and are interested in any ML and DL approaches.  We recognize the need for large amounts of training data and will provide ways of generating many more benchmark designs beyond the examples that are provided.  For example, Vivado can be used to synthesize and place any compatible design onto the contest device, and [RapidWright](https://github.com/Xilinx/RapidWright) used to convert that into the FPGA Interchange Format to serve as training data.  

*EDIT (2023/10/11):* The [`DcpToFPGAIF`](https://github.com/Xilinx/fpga24_routing_contest/pull/10) utility can now process any DCP into FPGAIF Logical and Physical Netlists for use with this contest.

### Will you provide access to ML/DL libraries to support inference? 

Although the specific mechanics of solution delivery are still being finalized, teams will be able to provide containerized solutions (e.g. Docker) where teams can configure their environment to include the necessary libraries to run their solution.  

### What software and hardware resources will be supplied towards parallelization?

As noted in the [Contest Details](details.html#key-details) "Contestants can expect to be evaluated on an AMD multi-core Linux platform with >=32 cores, >=64GB RAM, and no internet connectivity".  As mentioned in the previous answer, software enabling a container-like environment will allow contestants to build and configure their setup (including necessary libraries) to meet their own requirements.  

### Is serial equivalency a requirement (i.e., producing identical results regardless of the number of cores/threads used)?

No. In this contest, we hope to push the limits of how fast FPGA routing can be achieved and adding serial equivalency would create an additional burden on that goal, so it is not a requirement.

### We find that it takes a large amount of time to load the xcvu3p device into our routing resource map. We wonder that is it legal to dump the device information into an RRG and store it into another file so that our router can directly load the dumped RRG instead of building it from the device information?

The device file is intended to be invariant (https://github.com/Xilinx/fpga24_routing_contest/releases/latest/download/xcvu3p.device, same as what should be generated locally) and to be used as a reference, rather than an efficient database for data-driven use. You are free to transform any information inside the device file relevant to your router into whatever format you wish -- for example, into something more optimized to your router implementation, and then submit your custom preprocessed device file as an asset alongside your router.


## Submission Questions

### How many submission variants will be permitted from each team?

For the final submission, only the last submission made before the [final submission deadline](index.html#important-dates) will be accepted.
Prior to this, as part of the alpha submission process we intend to work with contestants to ensure that their submission runs as expected on our machine.

## More Questions?

Please post questions in our [Discussion](https://github.com/Xilinx/fpga24_routing_contest/discussions) forum.
