import copy
import random

SIZE = 9
EMPTY = 0
DIFFICULTY_SETTINGS = {
    "Easy": 45,
    "Medium": 36,
    "Hard": 27,
}


def deep_copy(board):
    return copy.deepcopy(board)


def create_empty_board():
    return [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]


def is_safe(board, row, col, num):
    for x in range(SIZE):
        if board[row][x] == num or board[x][col] == num:
            return False

    start_row = row - row % 3
    start_col = col - col % 3
    for i in range(3):
        for j in range(3):
            if board[start_row + i][start_col + j] == num:
                return False
    return True


def find_conflicts(board):
    conflicts = set()

    for row in range(SIZE):
        for col in range(SIZE):
            value = board[row][col]
            if value == EMPTY:
                continue

            for other_col in range(SIZE):
                if other_col != col and board[row][other_col] == value:
                    conflicts.add((row, col))
                    conflicts.add((row, other_col))

            for other_row in range(SIZE):
                if other_row != row and board[other_row][col] == value:
                    conflicts.add((row, col))
                    conflicts.add((other_row, col))

            start_row = (row // 3) * 3
            start_col = (col // 3) * 3
            for box_row in range(start_row, start_row + 3):
                for box_col in range(start_col, start_col + 3):
                    if (box_row, box_col) != (row, col) and board[box_row][box_col] == value:
                        conflicts.add((row, col))
                        conflicts.add((box_row, box_col))

    return [[row, col] for row, col in sorted(conflicts)]


def fill_board(board):
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == EMPTY:
                possible = list(range(1, SIZE + 1))
                random.shuffle(possible)
                for candidate in possible:
                    if is_safe(board, row, col, candidate):
                        board[row][col] = candidate
                        if fill_board(board):
                            return True
                        board[row][col] = EMPTY
                return False
    return True


def count_solutions(board, limit=2):
    board_copy = deep_copy(board)
    count = 0

    def search():
        nonlocal count
        if count >= limit:
            return

        row = -1
        col = -1
        for i in range(SIZE):
            for j in range(SIZE):
                if board_copy[i][j] == EMPTY:
                    row = i
                    col = j
                    break
            if row != -1:
                break

        if row == -1:
            count += 1
            return

        for candidate in random.sample(range(1, SIZE + 1), SIZE):
            if is_safe(board_copy, row, col, candidate):
                board_copy[row][col] = candidate
                search()
                if count >= limit:
                    return
                board_copy[row][col] = EMPTY

    search()
    return count


def is_unique_solution(board):
    return count_solutions(board, limit=2) == 1


def normalize_difficulty(difficulty):
    if difficulty is None:
        return None
    if isinstance(difficulty, str):
        normalized = difficulty.strip().capitalize()
        if normalized in DIFFICULTY_SETTINGS:
            return normalized
    return None


def generate_puzzle(clues=35, difficulty=None):
    normalized_difficulty = normalize_difficulty(difficulty)
    target_clues = clues
    if target_clues is None:
        target_clues = DIFFICULTY_SETTINGS.get(normalized_difficulty, 35)
    elif normalized_difficulty is not None and clues == 35:
        target_clues = DIFFICULTY_SETTINGS.get(normalized_difficulty, 35)

    board = create_empty_board()
    fill_board(board)
    solution = deep_copy(board)

    puzzle = deep_copy(board)
    cells = list(range(SIZE * SIZE))
    random.shuffle(cells)

    while len(cells) > 0 and sum(cell != EMPTY for row in puzzle for cell in row) > target_clues:
        idx = cells.pop()
        row, col = divmod(idx, SIZE)
        if puzzle[row][col] == EMPTY:
            continue

        original = puzzle[row][col]
        puzzle[row][col] = EMPTY
        if not is_unique_solution(puzzle):
            puzzle[row][col] = original

    if not is_unique_solution(puzzle):
        return generate_puzzle(clues=clues, difficulty=difficulty)

    return puzzle, solution
