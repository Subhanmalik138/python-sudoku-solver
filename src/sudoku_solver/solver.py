"""Sudoku solving engine.

A Sudoku board is a 9x9 grid of ints: ``0`` means empty, ``1``-``9`` are
givens. The solver uses depth-first backtracking with two standard
speed-ups that matter in practice:

* MRV (minimum remaining values): always branch on the empty cell with
  the fewest legal candidates, so dead ends are found early.
* Forward checking: a cell with zero candidates fails immediately
  instead of after a deeper, doomed search.

The engine is deliberately dependency-free and side-effect-free: every
public function works on a copy of the board it is given, so callers
never have to worry about a solved board mutating their input.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SIZE = 9
BOX = 3
EMPTY = 0

Board = list[list[int]]


@dataclass
class SolveStats:
    """Counters from a single solve, useful for difficulty estimates."""

    nodes: int = 0  # recursive calls made
    backtracks: int = 0  # candidate placements that were undone
    solutions_found: int = 0


def copy_board(board: Board) -> Board:
    return [row[:] for row in board]


def validate_board(board: Board) -> bool:
    """Return True if the board is well-formed with no duplicate givens.

    Shape errors, out-of-range values, and duplicates in any row,
    column, or 3x3 box all make a board invalid. An invalid board is
    not the same as an unsolvable one: invalid boards are rejected
    before the search starts.
    """
    if len(board) != SIZE or any(len(row) != SIZE for row in board):
        return False
    for row in board:
        for value in row:
            if not isinstance(value, int) or not 0 <= value <= SIZE:
                return False
    for group in _all_groups(board):
        seen = [v for v in group if v != EMPTY]
        if len(seen) != len(set(seen)):
            return False
    return True


def _all_groups(board: Board) -> list[list[int]]:
    groups: list[list[int]] = []
    groups.extend(board)  # rows
    groups.extend([[board[r][c] for r in range(SIZE)] for c in range(SIZE)])
    for box_row in range(0, SIZE, BOX):
        for box_col in range(0, SIZE, BOX):
            groups.append(
                [
                    board[r][c]
                    for r in range(box_row, box_row + BOX)
                    for c in range(box_col, box_col + BOX)
                ]
            )
    return groups


def candidates(board: Board, row: int, col: int) -> set[int]:
    """Legal digits for an empty cell, given the current board."""
    if board[row][col] != EMPTY:
        return set()
    used = set(board[row])
    used.update(board[r][col] for r in range(SIZE))
    box_row, box_col = row - row % BOX, col - col % BOX
    used.update(
        board[r][c]
        for r in range(box_row, box_row + BOX)
        for c in range(box_col, box_col + BOX)
    )
    return set(range(1, SIZE + 1)) - used


def _select_cell(board: Board) -> tuple[int, int, set[int]] | None:
    """Pick the next cell by MRV; return None when the board is full.

    Raises nothing: a cell with zero candidates is returned with an
    empty set, which the search treats as an immediate dead end.
    """
    best: tuple[int, int, set[int]] | None = None
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] != EMPTY:
                continue
            cell_candidates = candidates(board, row, col)
            if not cell_candidates:
                return row, col, cell_candidates
            if best is None or len(cell_candidates) < len(best[2]):
                best = row, col, cell_candidates
                if len(cell_candidates) == 1:
                    return best
    return best


def solve(board: Board) -> Board | None:
    """Return a solved copy of ``board``, or None if it has no solution.

    Raises ValueError for an invalid board (see :func:`validate_board`).
    """
    solved, _ = solve_with_stats(board)
    return solved


def solve_with_stats(board: Board) -> tuple[Board | None, SolveStats]:
    """Solve like :func:`solve`, also returning search statistics."""
    if not validate_board(board):
        raise ValueError("invalid Sudoku board: bad shape, value, or duplicate")
    working = copy_board(board)
    stats = SolveStats()
    if _search(working, stats):
        return working, stats
    return None, stats


def _search(board: Board, stats: SolveStats) -> bool:
    stats.nodes += 1
    picked = _select_cell(board)
    if picked is None:
        return True  # no empty cells left: solved
    row, col, cell_candidates = picked
    if not cell_candidates:
        return False
    for value in sorted(cell_candidates):
        board[row][col] = value
        if _search(board, stats):
            return True
        board[row][col] = EMPTY
        stats.backtracks += 1
    return False


def count_solutions(board: Board, limit: int = 2) -> int:
    """Count solutions up to ``limit`` (default 2: enough to test uniqueness).

    Counting stops early once ``limit`` is reached, so checking whether
    a puzzle has a unique solution is cheap even for under-constrained
    boards. Raises ValueError for an invalid board.
    """
    if limit < 1:
        raise ValueError("limit must be at least 1")
    if not validate_board(board):
        raise ValueError("invalid Sudoku board: bad shape, value, or duplicate")
    working = copy_board(board)
    stats = SolveStats()
    _count(working, stats, limit)
    return stats.solutions_found


def _count(board: Board, stats: SolveStats, limit: int) -> None:
    if stats.solutions_found >= limit:
        return
    picked = _select_cell(board)
    if picked is None:
        stats.solutions_found += 1
        return
    row, col, cell_candidates = picked
    for value in sorted(cell_candidates):
        board[row][col] = value
        _count(board, stats, limit)
        board[row][col] = EMPTY
        if stats.solutions_found >= limit:
            return


def estimate_difficulty(board: Board) -> str:
    """Rough difficulty label from the search effort a puzzle needs.

    This is a heuristic, not a human difficulty rating: "Easy" puzzles
    fall out with almost no backtracking, "Hard" ones force the solver
    to explore. Givens alone are a poor proxy, which is why the label
    is derived from the actual search instead of the clue count.
    """
    _, stats = solve_with_stats(board)
    if stats.backtracks == 0:
        return "Easy"
    if stats.backtracks < 100:
        return "Medium"
    return "Hard"


def parse_puzzle(text: str) -> Board:
    """Parse a puzzle from text into a 9x9 board.

    Accepts the compact 81-character form (digits, ``0`` or ``.`` for
    empties) and the multi-line grid form. Whitespace and the common
    grid separators ``|``, ``-``, ``+`` are ignored. Anything else, or
    a length other than 81 cells, raises ValueError.
    """
    cleaned = "".join(ch for ch in text if not ch.isspace())
    cleaned = cleaned.replace("|", "").replace("-", "").replace("+", "")
    if len(cleaned) != SIZE * SIZE:
        raise ValueError(f"expected 81 cells, got {len(cleaned)}")
    if any(ch not in "0123456789." for ch in cleaned):
        raise ValueError("puzzle may only contain digits, 0, or '.'")
    digits = [0 if ch == "." else int(ch) for ch in cleaned]
    board = [digits[r * SIZE : (r + 1) * SIZE] for r in range(SIZE)]
    if not validate_board(board):
        raise ValueError("puzzle contains a duplicate given")
    return board


def format_board(board: Board) -> str:
    """Render a board as a human-readable grid with 3x3 box dividers."""
    lines: list[str] = []
    for row in range(SIZE):
        cells = []
        for col in range(SIZE):
            value = board[row][col]
            cells.append(str(value) if value != EMPTY else ".")
            if col in (2, 5):
                cells.append("|")
        lines.append(" ".join(cells))
        if row in (2, 5):
            lines.append("-" * 21)
    return "\n".join(lines)


def compact_board(board: Board) -> str:
    """Render a board as a single 81-character string (``.`` = empty)."""
    return "".join(
        str(value) if value != EMPTY else "."
        for row in board
        for value in row
    )
