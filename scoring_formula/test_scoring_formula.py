# Copyright (C) 2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author: Zak Nafziger, AMD
#
# SPDX-License-Identifier: MIT
#

import unittest
import scoring_formula

class TestScoringFormula(unittest.TestCase):
    def run_test(self, results, expected_results):
        """
        Given a dictionary of results from running many routers (each
        corresponding to a team) across a benchmark suite, and a list of sets
        of team names ordered from first place to last place ensure that the
        scoring procedure produces the same ordering.

        Args:
            results: A dictionary of results. Keys are team/router names. Values
            are lists of 3-tuples. Each 3-tuple is:
            (status of CheckPhysNetlist, Runtime, critical-path wirelength).
            expected_results: A list of sets of team/router names in order from
            first to last place.
        """
        scores = dict.fromkeys(results)
        for team, result in results.items():
            scores[team] = list(map(lambda x: scoring_formula.score_benchmark_results(*x), result))
        ranking = scoring_formula.rank_benchmark_scores(scores)
        results = scoring_formula.rank_teams(ranking)
        if results != expected_results:
            print(results)
        self.assertEqual(results, expected_results)

    def test_invalid_routing(self):
        """
        Ensure that a team that produces a result with invalid routing loses
        even if it runs faster and reports a lower critical-path wirelength.

        The result of CheckPhysNetlist for TEAM A is False, indicating that
        some nets had routing errors. TEAM B should therefore win, even though
        it took longer to produce a result, and has a larger critical-path
        wirelength.
        """
        results = {
            'TEAM A':[(False, 500, 450)],
            'TEAM B':[(True, 700, 455)],
        }

        self.run_test(results, [{'TEAM B'}, {'TEAM A'}])

    def test_catastrophic_failure(self):
        """
        Ensure that a router that fails catastrophically loses to one that
        runs without error.

        `results1` indicates that TEAM A failed to produce a properly routed
        design (CheckPhyNetlist failed, and no wirelength could be computed)
        and its (very low) runtime should be ignored. This set of results might
        be expected if TEAM A's router crashed without producing results. In
        this case TEAM B should win.

        `results2` indicates that TEAM A failed to run, since no runtime was
        recorded, and no results that could be analyzed were produced. This set
        of results might be expected if TEAM A's router could not be compiled.
        Again TEAM B should win.
        """
        results1 = {
            'TEAM A':[(False, 2, None)],
            'TEAM B':[(True, 700, 455)],
        }

        results2 = {
            'TEAM A':[(False, None, None)],
            'TEAM B':[(True, 700, 455)],
        }

        self.run_test(results1, [{'TEAM B'}, {'TEAM A'}])
        self.run_test(results2, [{'TEAM B'}, {'TEAM A'}])

    def test_multiple_failure(self):
        """
        Ensure that no priority is assigned to catastrophic failure vs. failure
        due to invalid results.

        In this case TEAM A and TEAM B recieve a joint last-place result
        despite TEAM A failing catastrophically, and TEAM B merely producing
        invalid results.
        """
        results = {
            'TEAM A':[(False, 3, None)],
            'TEAM B':[(False, 500, 450)],
            'TEAM C':[(True, 700, 455)],
        }

        self.run_test(results, [{'TEAM C'}, {'TEAM A', 'TEAM B'}])

    def test_exact_tie(self):
        """
        Ensure that in the (very unlikely) event that multiple teams achieve an
        identical score no priority is given to one or the other.

        In this case TEAM A and TEAM B recieve a joint first-place result.
        """
        results = {
            'TEAM A':[(True, 500, 450)],
            'TEAM B':[(True, 500, 450)],
            'TEAM C':[(True, 700, 455)],
        }

        self.run_test(results, [{'TEAM A', 'TEAM B'}, {'TEAM C'}])

    def test_clear_winner(self):
        """
        Determine the ordering of three teams (A, B, C) when one team (B)
        achieves the fastest runtime on all benchmarks.

        Given the results in this test expect TEAM A to win since it achieves
        the lowest runtime on each benchmark (despite having generally worse
        critical-path wirelength). Expect TEAM C to come second since it
        achieves runtimes between A and B on all benchmarks. Expect A to come
        last.
        """
        results = {
            'TEAM A':[(True, 452,  642),
                      (True, 311,  894),
                      (True, 678,  555),
                      (True, 970,  993),
                      (True, 2295, 1786)],
            'TEAM B':[(True, 317,  642),
                      (True, 101,  946),
                      (True, 377,  937),
                      (True, 301,  1476),
                      (True, 963,  2210)],
            'TEAM C':[(True, 402,  468),
                      (True, 269,  747),
                      (True, 666,  570),
                      (True, 830,  947),
                      (True, 1450, 1485)],
        }

        self.run_test(results, [{'TEAM B'}, {'TEAM C'}, {'TEAM A'}])

    def test_dominant_team_single_failure(self):
        """
        Determine the order of three teams (A, B, C) when one team (B) achieves
        the fastest runtime on 4/5 benchmarks, but fails to produce a result on
        the fifth.

        Results are as in `test_clear_winner`, except that TEAM B fails to
        produce a valid result for benchmark 5. Expect TEAM B to still achieve
        first place since it achieved better runtimes on all benchmarks for
        which a valid result was produced. This test demonstrates that the
        scoring procedure tolerates a small number of failures (e.g. due to
        an unexpected bug).
        """
        results = {
            'TEAM A':[(True, 452,  642),
                      (True, 311,  894),
                      (True, 678,  555),
                      (True, 970,  993),
                      (True, 2295, 1786)],
            'TEAM B':[(True, 317,  642),
                      (True, 101,  946),
                      (True, 377,  937),
                      (True, 301,  1476),
                      (False, None,  None)],
            'TEAM C':[(True, 402,  468),
                      (True, 269,  747),
                      (True, 666,  570),
                      (True, 830,  947),
                      (True, 1450, 1485)],
        }

        self.run_test(results, [{'TEAM B'}, {'TEAM C'}, {'TEAM A'}])

    def test_dominant_team_double_failure(self):
        """
        Determine the order of three teams (A, B, C) when one team (B) achieves
        good results on some benchmarks, but fails to produce a result on
        multiple other benchmarks.

        Results are as in `test_clear_winner`, except that TEAM B fails to
        produce a results on two benchmarks. In this case TEAM C is expected to win
        overall, and TEAM B to place second. This test demonstrates that the
        scoring procedure penalizes repeated failures.
        """
        results = {
            'TEAM A':[(True, 452,  642),
                      (True, 311,  894),
                      (True, 678,  555),
                      (True, 970,  993),
                      (True, 2295, 1786)],
            'TEAM B':[(True, 317,  642),
                      (True, 101,  946),
                      (True, 377,  937),
                      (False, None,  None),
                      (False, None,  None)],
            'TEAM C':[(True, 402,  468),
                      (True, 269,  747),
                      (True, 666,  570),
                      (True, 830,  947),
                      (True, 1450, 1485)],
        }

        self.run_test(results, [{'TEAM C'}, {'TEAM B'}, {'TEAM A'}])

