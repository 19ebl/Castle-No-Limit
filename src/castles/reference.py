"""Slow, obviously correct reference scorer (claude-code).

Written independently of engine.py and rules.py: it must not import either.
Everything is in integer units of 1/12 point, so all splits are exact.

Game 1: two players, each castle's points go to the larger count; ties split.
Game 2: four players, each castle's points go to the largest count; k-way ties
split value/k. Players are ranked by total castle points and paid 9/4/2/0 by
place; players tied on total share the payouts of the places they occupy.
"""
from __future__ import annotations

from fractions import Fraction

R_VALUES = (1, 2, 3, 4, 5)
R_TOTAL = 100
R_UNIT = 12
R_PAYOUTS = (9, 4, 2, 0)  # in points; converted to units below


def check_alloc(x) -> tuple[int, ...]:
    raw = tuple(x)
    for v in raw:
        if int(v) != v:
            raise ValueError(f"non-integer count {v!r} in {raw}")
    x = tuple(int(v) for v in raw)
    if len(x) != 5:
        raise ValueError(f"need 5 castles, got {len(x)}")
    if any(v < 0 for v in x):
        raise ValueError(f"negative count in {x}")
    if sum(x) != R_TOTAL:
        raise ValueError(f"allocation {x} sums to {sum(x)}, not {R_TOTAL}")
    return x


def castle_units(players) -> list[int]:
    """Castle points of each player in a group of any size, in 1/12 units."""
    players = [check_alloc(p) for p in players]
    n = len(players)
    pts = [0] * n
    for j, value in enumerate(R_VALUES):
        counts = [p[j] for p in players]
        top = max(counts)
        winners = [i for i in range(n) if counts[i] == top]
        share = Fraction(value * R_UNIT, len(winners))
        assert share.denominator == 1, "castle share not integral"
        for i in winners:
            pts[i] += int(share)
    return pts


def game1_units(a, b) -> tuple[int, int]:
    """Game 1 head to head: castle points of a and b, in 1/12 units."""
    pa, pb = castle_units([a, b])
    return pa, pb


def payout_units(totals) -> list[int]:
    """Place payouts for a group of 4 given their totals, in 1/12 units."""
    if len(totals) != 4:
        raise ValueError("Game 2 groups have exactly 4 players")
    pay_units = [p * R_UNIT for p in R_PAYOUTS]
    order = sorted(range(4), key=lambda i: -totals[i])
    out = [0] * 4
    place = 0
    while place < 4:
        t = totals[order[place]]
        tied = [i for i in order if totals[i] == t]
        occupied = pay_units[place:place + len(tied)]
        share = Fraction(sum(occupied), len(tied))
        assert share.denominator == 1, "payout share not integral"
        for i in tied:
            out[i] = int(share)
        place += len(tied)
    return out


def game2_units(group) -> tuple[list[int], list[int]]:
    """Game 2 four-way battle: (castle units, payout units) per player."""
    if len(group) != 4:
        raise ValueError("Game 2 groups have exactly 4 players")
    pts = castle_units(group)
    return pts, payout_units(pts)
