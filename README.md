# Sudoku Solver

A dependency-free Sudoku solver in Python: backtracking search with
MRV cell selection and forward checking, solution counting (including
uniqueness checks), difficulty estimation, and a small CLI.

## The problem

Naive Sudoku backtracking tries cells in row order and wastes most of
its time in branches that were doomed from the start. This solver
picks its battles: it always branches on the most constrained empty
cell first, and it fails fast the moment any cell runs out of legal
candidates.

## Design decisions

1. **MRV ordering.** The search always branches on the empty cell with
   the fewest legal candidates. This finds contradictions early and is
   the single biggest speedup over row-order backtracking.
2. **Forward checking, not full propagation.** A zero-candidate cell
   aborts the branch immediately. Full constraint propagation (e.g.
   hidden singles) would be faster on the hardest puzzles, but it
   complicates the code far more than it helps at this scale — MRV
   plus forward checking already solves hard published puzzles
   instantly.
3. **Pure functions, copied boards.** `solve()` never mutates its
   input; it returns a new solved board or `None`. That makes the
   solver trivially testable and safe to call from a loop or a server.
4. **Counting with an early cap.** `count_solutions(board, limit=2)`
   stops as soon as the cap is reached, so testing uniqueness costs
   little even for under-constrained boards with millions of
   solutions.

## Usage

```bash
pip install .
sudoku-solve 530070000600195000098000060800060003400803001700020006060000280000419005000080079
sudoku-solve --file examples/hard.txt --stats --difficulty
```

Use `0` or `.` for empty cells. Puzzles can also be given in
multi-line grid form; see `examples/easy.txt` and `examples/hard.txt`.

Count solutions instead of solving (the default cap of 2 answers
"is this puzzle unique?"):

```bash
sudoku-solve --file examples/easy.txt --count
# solutions (up to 2): 1
```

Or use it as a library:

```python
from sudoku_solver import parse_puzzle, solve, count_solutions

board = parse_puzzle("530070000600195000098000060800060003400803001"
                     "700020006060000280000419005000080079")
solved = solve(board)  # a new 9x9 list of lists, or None
assert count_solutions(board, limit=2) == 1  # unique solution
```

Exit codes: `0` solved/counted, `1` no solution, `2` bad input.

## Running tests

```bash
pip install pytest
python -m pytest
```

## Tech stack

Python 3.10+ standard library only — no runtime dependencies.
