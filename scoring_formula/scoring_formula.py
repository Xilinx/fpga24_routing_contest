# Copyright (C) 2023-2024, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author: Zak Nafziger, AMD
#
# SPDX-License-Identifier: MIT
#

def score_benchmark_results(check, runtime, cpw):
    """
    Score a router's performance on a given benchmark based on:
    1. the status returned by CheckPhysNetlist
    2. the total runtime
    3. the critical-path wirelength reported by wa.py

    Args:
        check: boolean result of CheckPhysNetlist
        runtime: runtime in seconds
        cpw: critical-path wirelength score reported by wa.py
    Returns:
        A final score
    """
    if check:
        return 0.9*runtime + 0.1*cpw
    else:
        return float('inf')

def rank_benchmark_scores(scores):
    """
    For each benchmark assign each team a rank based on the score achieved on
    that benchmark. Allows multiple teams to achieve the same rank, if scores
    are identical.

    Args:
        scores: A dictionary of scores. Keys are team names, values are a list
        of benchmark scores.
    returns:
        A dictionary of ranks. Keys are team names, values are a list of
        rankings.
    """

    num_benchmarks = None
    for score in scores.values():
        if num_benchmarks is None:
            num_benchmarks = len(score)
        else:
            assert num_benchmarks == len(score)

    rankings = {k:[] for k in scores}

    for b in range(num_benchmarks):
        scores_for_b = {}
        for team, score in scores.items():
            scores_for_b.setdefault(score[b], {team}).add(team)
        ranking_for_b = sorted(scores_for_b)
        for rank, score in enumerate(ranking_for_b):
            for team in scores_for_b[score]:
                rankings[team].append(rank + 1)
    return rankings

def rank_teams(rankings):
    """
    For each team compute the arithmetic mean of the rank achieved on each
    benchmark. Sort teams by their mean rank.

    Args:
        rankings: A dictionary of ranks. Keys are team names, values are a list
        of rankings.
    returns:
        An ordered list of sets. Each set represents a "place" (e.g. first,
        second, third, etc) and contains the names of all teams that achieved
        that place.
    """

    avg_rank = {}
    for team, ranks in rankings.items():
        avg = sum(ranks)/len(ranks)
        avg_rank.setdefault(avg, {team}).add(team)

    order = sorted(avg_rank)
    results = []
    for place in order:
        results.append(avg_rank[place])

    return results
