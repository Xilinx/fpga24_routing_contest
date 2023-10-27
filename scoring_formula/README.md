# Scoring Formula and Ranking Algorithm
This directory contains an implementation of the contest scoring formula,
ranking algorithm, and a series of test cases that illustrate how contest
results will be computed in a variety of cases. A detailed description of how
teams will be scored and ranked is presented on the
[Scoring Criteria](https://xilinx.github.io/fpga24_routing_contest/score.html)
webpage.

## `scoring_formula.py`
`scoring_formula.py` provides a collection of methods that

1. Compute a score based on the per-benchmark performance of a router
2. Rank teams based on a collection of per-benchmark scores
3. Determine the final ordering of teams based on their per-benchmar ranks

`scoring_formula.py` is not expected to be run directly, and is instead
provided as a utility for other scripts (such as `compute-score.py`).

## `test_scoring_formula.py`
`test_scoring_formula.py` provides a set of test cases to illustrate how
scores are computed and how teams are ranked. Each test case includes a brief
description of the scenario presented. The command line to run these test cases
is:

```
python3 -m unittest test_scoring_formula.py -v
```

By default all test cases should pass.
