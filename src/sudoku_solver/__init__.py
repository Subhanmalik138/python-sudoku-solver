"""Sudoku solver: MRV backtracking, solution counting, and a CLI."""

from .solver import (
    SolveStats,
    compact_board,
    count_solutions,
    estimate_difficulty,
    format_board,
    parse_puzzle,
    solve,
    solve_with_stats,
    validate_board,
)

__all__ = [
    "SolveStats",
    "compact_board",
    "count_solutions",
    "estimate_difficulty",
    "format_board",
    "parse_puzzle",
    "solve",
    "solve_with_stats",
    "validate_board",
]
