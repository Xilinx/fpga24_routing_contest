# Frequently Asked Questions


## Team Questions

### Can undergraduate students not in our research lab be part of a team?

Yes.

### Can recent graduates qualify to be members of a team?

Yes, being a student is not a requirement.

### Is there a constraint on the number of Team members?

Currently, the team limit is 6 members (not counting the advisor(s)).

### Can the team have two advisors?

Yes.

### Can we have more than one team?

Yes, as long as team members belong exclusively to a single team.  However, advisors can advise more than one team.

### Can we collaborate with another University as a single team for the contest?

Yes.

## Contest Objective Questions

### The main objective of the contest appears to optimizing routing speed. However, should the router be timing-driven or wire-length driven? More specifically, should the criticality of nets be computed within the router to influence routing order?

A timing-driven router will not be required, the competition is mostly focused on wirelength driven approaches.  There will be a scoring tool provided that will calculate the critical path via wirelength, however, as noted in the scoring criteria, this critical path length will be a smaller portion of the overall score.  As you have noted, it is primarily focused runtime of generating a legal routing solution.

### Can we use existing routers (i.e., VPR Pathfinder) as a starting point or should the team build a custom router from scratch.

Yes, any existing solutions or solutions built from scratch and/or modified are welcome.

### How are we going to be evaluated and ranked against other contestants?

All team solutions will be measured using the same criteria, hardware platform, and constraints.  A scoring tool will be provided that will measure the results of each team’s submission and will generate a score based on the scoring criteria.  

### Can teams change the placement solution provided to improve the running time of the router?

The placement of the designs will remain fixed and should not be changed as part of the routing solution.  The scoring tool will ensure that the placement has not changed during the course of routing.  Any placement changes will flag a result as being not legal and will not be considered.  There will likely be some flexibility as to LUT input permutations, but details are still forthcoming.

### Must the router be iterative, or will an mixed-integer programming solver be made available to support concurrent routing approaches?

Any router provided that generates a legal solution will be accepted.  We welcome a diversity of approaches.

## Approach and Technique Questions

### Transformative technologies, like ML and DL, require large amounts of
training data. Will you be providing training data to enable such approaches, or are you only interested in traditional algorithmic approaches?

We welcome and are interested in any ML and DL approaches.  We recognize the need for large amounts of training data and will provide ways of generating many more benchmark designs beyond the examples that are provided.  For example, any placed and routed DCP from Vivado can be converted via the FPGA Interchange Format to serve as training data.  

### Will you provide access to ML/DL libraries to support inference? 

Although the specific mechanics of solution delivery are still being finalized, teams will be able to provide containerized solutions (e.g. Docker) where teams can configure their environment to include the necessary libraries to run their solution.  

### What software and hardware resources will be supplied towards parallelization?

As noted in the key details of the contest description, “Contestants can expect to be evaluated on an AMD multi-core Linux platform with >=32 cores, >=64GB RAM, and no internet connectivity”.  As mentioned in the previous answer, software enabling a container-like environment will allow contestants to build and configure their setup to meet their own requirements.  

### What libraries, if any, will be provided to support parallel patterns like those employed in the book by McCool (https://www.sciencedirect.com/book/9780124159938/structured-parallel-programming) 

Any library that can be specified/delivered via the team’s container and can be run on the platform should be available.

## Submission Questions

### How many submission variants will be permitted from each team?

Each team will be allowed _ number of submission(2) in the final round.

