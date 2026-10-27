"""Command-line interface: solve a Sudoku puzzle from text or a file.

Examples:
    sudoku-solve 530070000600195000098000060800060003400803001700020006060000280000419005000080079
    sudoku-solve --file examples/puzzles.txt --stats
    sudoku-solve --file puzzle.txt --count --limit 2
"""

from __future__ import annotations

import argparse
import sys

from .solver import (
    compact_board,
    count_solutions,
    estimate_difficulty,
    format_board,
    parse_puzzle,
    solve_with_stats,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sudoku-solve",
        description="Solve a Sudoku puzzle (81 cells: digits, 0 or . for empty).",
    )
    parser.add_argument("puzzle", nargs="?", help="puzzle as one 81-cell string")
    parser.add_argument("--file", "-f", help="read the puzzle from a file")
    parser.add_argument(
        "--format",
        choices=["grid", "compact"],
        default="grid",
        help="output format (default: grid)",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        help="count solutions instead of solving (stops at --limit)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=2,
        help="solution-count cap for --count (default: 2)",
    )
    parser.add_argument(
        "--stats", action="store_true", help="print search nodes/backtracks"
    )
    parser.add_argument(
        "--difficulty",
        action="store_true",
        help="print the estimated difficulty of the puzzle",
    )
    return parser


def _render(board, fmt: str) -> str:
    return format_board(board) if fmt == "grid" else compact_board(board)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if bool(args.puzzle) == bool(args.file):
        print(
            "error: give exactly one of PUZZLE or --file",
            file=sys.stderr,
        )
        return 2
    try:
        if args.file:
            with open(args.file, encoding="utf-8") as handle:
                board = parse_puzzle(handle.read())
        else:
            board = parse_puzzle(args.puzzle or "")
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.count:
        try:
            found = count_solutions(board, limit=args.limit)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(f"solutions (up to {args.limit}): {found}")
        return 0

    solved, stats = solve_with_stats(board)
    if solved is None:
        print("no solution", file=sys.stderr)
        return 1
    print(_render(solved, args.format))
    if args.stats:
        print(f"nodes: {stats.nodes}, backtracks: {stats.backtracks}")
    if args.difficulty:
        print(f"difficulty: {estimate_difficulty(board)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
