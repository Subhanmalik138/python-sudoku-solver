"""Tests for the Sudoku solver engine and CLI."""

import pytest

from sudoku_solver import (
    compact_board,
    count_solutions,
    estimate_difficulty,
    format_board,
    parse_puzzle,
    solve,
    solve_with_stats,
    validate_board,
)
from sudoku_solver.cli import main

EASY = (
    "530070000600195000098000060800060003400803001700020006"
    "060000280000419005000080079"
)
EASY_SOLUTION = (
    "534678912672195348198342567859761423426853791713924856"
    "961537284287419635345286179"
)
HARD = (
    "800000000003600000070090200050007000000045700000100030"
    "001000068008500010090000400"
)
# Valid but unsolvable: cell (0, 8) needs a 9, but its row, column,
# and box each already contain one.
UNSOLVABLE = "123456780" + "000000009" + "0" * 63


def test_solves_canonical_easy_puzzle_exactly():
    solved = solve(parse_puzzle(EASY))
    assert solved is not None
    assert compact_board(solved) == EASY_SOLUTION


def test_solution_respects_givens_and_is_valid():
    board = parse_puzzle(HARD)
    solved = solve(board)
    assert solved is not None
    assert validate_board(solved)
    for row in range(9):
        for col in range(9):
            if board[row][col] != 0:
                assert solved[row][col] == board[row][col]
    assert all(value != 0 for row in solved for value in row)


def test_solve_does_not_mutate_input():
    board = parse_puzzle(EASY)
    original = [row[:] for row in board]
    solve(board)
    assert board == original


def test_already_solved_board_is_returned_unchanged():
    board = parse_puzzle(EASY_SOLUTION)
    assert compact_board(solve(board)) == EASY_SOLUTION


def test_unsolvable_board_returns_none():
    assert solve(parse_puzzle(UNSOLVABLE)) is None


def test_invalid_board_raises():
    board = parse_puzzle(EASY)
    board[0][1] = board[0][0]  # duplicate in the first row
    assert not validate_board(board)
    with pytest.raises(ValueError):
        solve(board)


def test_empty_board_has_more_than_one_solution():
    assert count_solutions(parse_puzzle("0" * 81), limit=2) == 2


def test_unique_puzzle_counts_exactly_one_solution():
    assert count_solutions(parse_puzzle(EASY), limit=2) == 1


def test_parse_rejects_wrong_length_and_bad_characters():
    with pytest.raises(ValueError):
        parse_puzzle("123")
    with pytest.raises(ValueError):
        parse_puzzle("x" * 81)


def test_parse_accepts_dots_and_multiline_grid():
    grid = "\n".join(EASY[i : i + 9] for i in range(0, 81, 9))
    board = parse_puzzle(grid.replace("0", "."))
    assert compact_board(solve(board)) == EASY_SOLUTION


def test_hard_puzzle_needs_more_search_than_easy_one():
    _, easy_stats = solve_with_stats(parse_puzzle(EASY))
    _, hard_stats = solve_with_stats(parse_puzzle(HARD))
    assert hard_stats.nodes > easy_stats.nodes
    assert estimate_difficulty(parse_puzzle(EASY)) in ("Easy", "Medium", "Hard")


def test_format_round_trips_through_parse():
    board = parse_puzzle(EASY)
    assert parse_puzzle(format_board(board)) == board


def test_cli_solves_and_reports_no_solution(capsys):
    assert main([EASY]) == 0
    out = capsys.readouterr().out
    assert "534678912" in out.replace(" ", "").replace("\n", "").replace("|", "")
    assert main([UNSOLVABLE]) == 1


def test_cli_requires_exactly_one_input():
    assert main([]) == 2
    assert main([EASY, "--file", "examples/puzzles.txt"]) == 2
