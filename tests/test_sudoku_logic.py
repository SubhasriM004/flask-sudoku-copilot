import sudoku_logic


def test_create_empty_board_returns_nine_by_nine_grid():
    board = sudoku_logic.create_empty_board()

    assert board == [[0 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]


def test_is_safe_detects_row_and_column_conflicts():
    board = sudoku_logic.create_empty_board()
    board[0][0] = 1
    board[0][1] = 1

    assert sudoku_logic.is_safe(board, 0, 2, 1) is False
    assert sudoku_logic.is_safe(board, 1, 0, 1) is False


def test_find_conflicts_reports_duplicate_values():
    board = sudoku_logic.create_empty_board()
    board[0][0] = 1
    board[0][1] = 1
    board[1][0] = 1

    conflicts = sudoku_logic.find_conflicts(board)

    assert [0, 0] in conflicts
    assert [0, 1] in conflicts
    assert [1, 0] in conflicts


def test_generate_puzzle_returns_unique_solution_board():
    puzzle, solution = sudoku_logic.generate_puzzle(clues=30)

    assert len(puzzle) == sudoku_logic.SIZE
    assert len(solution) == sudoku_logic.SIZE
    assert sudoku_logic.is_unique_solution(puzzle)
    assert sudoku_logic.count_solutions(puzzle) == 1


def test_count_solutions_returns_zero_for_unsatisfiable_board():
    board = sudoku_logic.create_empty_board()
    board[0][0] = 1
    board[0][1] = 1

    assert sudoku_logic.count_solutions(board, limit=2) == 0


def test_count_solutions_returns_one_for_single_solution_board():
    board = [
        [1, 2, 3, 4, 5, 6, 7, 8, 9],
        [4, 5, 6, 7, 8, 9, 1, 2, 3],
        [7, 8, 9, 1, 2, 3, 4, 5, 6],
        [2, 3, 4, 5, 6, 7, 8, 9, 1],
        [5, 6, 7, 8, 9, 1, 2, 3, 4],
        [8, 9, 1, 2, 3, 4, 5, 6, 7],
        [3, 4, 5, 6, 7, 8, 9, 1, 2],
        [6, 7, 8, 9, 1, 2, 3, 4, 5],
        [9, 1, 2, 3, 4, 5, 6, 7, 8],
    ]
    board[0][0] = 0

    assert sudoku_logic.count_solutions(board, limit=2) == 1


def test_count_solutions_stops_after_two_solutions_for_multiple_solution_board():
    board = sudoku_logic.create_empty_board()

    assert sudoku_logic.count_solutions(board, limit=2) == 2
