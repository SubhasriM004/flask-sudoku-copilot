from flask import Blueprint, jsonify, render_template, request

import sudoku_logic
from utils import CURRENT, update_current_game

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/new")
def new_game():
    clues_arg = request.args.get("clues")
    difficulty = request.args.get("difficulty")

    if clues_arg is None:
        puzzle, solution = sudoku_logic.generate_puzzle(difficulty=difficulty)
    else:
        puzzle, solution = sudoku_logic.generate_puzzle(clues=int(clues_arg), difficulty=difficulty)

    update_current_game(puzzle, solution)
    return jsonify({
        "puzzle": puzzle,
        "timer": {
            "elapsed_seconds": CURRENT.get("elapsed_seconds", 0),
            "running": CURRENT.get("timer_running", False),
        },
    })


@bp.route("/validate", methods=["POST"])
def validate_board():
    data = request.get_json(silent=True) or {}
    board = data.get("board")

    if not isinstance(board, list) or len(board) != sudoku_logic.SIZE:
        return jsonify({"error": "Invalid board"}), 400

    for row in board:
        if not isinstance(row, list) or len(row) != sudoku_logic.SIZE:
            return jsonify({"error": "Invalid board"}), 400

    conflicts = sudoku_logic.find_conflicts(board)
    return jsonify({"conflicts": conflicts})


@bp.route("/check", methods=["POST"])
def check_solution():
    data = request.json
    board = data.get("board")
    solution = CURRENT.get("solution")
    if solution is None:
        return jsonify({"error": "No game in progress"}), 400

    incorrect = []
    for i in range(sudoku_logic.SIZE):
        for j in range(sudoku_logic.SIZE):
            if board[i][j] != solution[i][j]:
                incorrect.append([i, j])

    conflicts = sudoku_logic.find_conflicts(board)

    if len(incorrect) == 0:
        CURRENT["timer_running"] = False
    else:
        CURRENT["timer_running"] = CURRENT.get("timer_running", False)

    return jsonify({
        "incorrect": incorrect,
        "conflicts": conflicts,
        "solved": len(incorrect) == 0,
        "timer": {
            "elapsed_seconds": CURRENT.get("elapsed_seconds", 0),
            "running": CURRENT.get("timer_running", False),
        },
    })


@bp.route("/hint", methods=["POST"])
def get_hint():
    solution = CURRENT.get("solution")
    if solution is None:
        return jsonify({"error": "No game in progress"}), 400

    data = request.get_json(silent=True) or {}
    board = data.get("board")
    if board is None:
        board = sudoku_logic.deep_copy(CURRENT.get("puzzle") or [])
    else:
        board = [row[:] for row in board]

    if not isinstance(board, list) or len(board) != sudoku_logic.SIZE:
        return jsonify({"error": "Invalid board"}), 400

    for i in range(sudoku_logic.SIZE):
        if not isinstance(board[i], list) or len(board[i]) != sudoku_logic.SIZE:
            return jsonify({"error": "Invalid board"}), 400

    empty_cells = []
    for i in range(sudoku_logic.SIZE):
        for j in range(sudoku_logic.SIZE):
            if board[i][j] == 0:
                empty_cells.append((i, j))

    if not empty_cells:
        return jsonify({"error": "No empty cells remaining"}), 400

    CURRENT["hints_used"] = CURRENT.get("hints_used", 0) + 1

    row, col = empty_cells[0]
    value = solution[row][col]
    board[row][col] = value
    CURRENT["puzzle"] = board
    if [row, col] not in CURRENT["locked_cells"]:
        CURRENT["locked_cells"].append([row, col])

    return jsonify({
        "row": row,
        "col": col,
        "value": value,
        "puzzle": board,
        "locked_cells": CURRENT["locked_cells"],
        "timer": {
            "elapsed_seconds": CURRENT.get("elapsed_seconds", 0),
            "running": CURRENT.get("timer_running", False),
        },
    })


@bp.route("/leaderboard", methods=["GET", "POST"])
def leaderboard():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        player_name = (data.get("player_name") or "").strip() or "Player"
        completion_time = data.get("completion_time")
        difficulty = (data.get("difficulty") or "Medium").strip() or "Medium"
        hints_used = data.get("hints_used", CURRENT.get("hints_used", 0))

        if completion_time is None:
            return jsonify({"error": "completion_time is required"}), 400

        try:
            completion_time = int(completion_time)
        except (TypeError, ValueError):
            return jsonify({"error": "completion_time must be an integer"}), 400

        try:
            hints_used = int(hints_used)
        except (TypeError, ValueError):
            hints_used = 0

        entry = {
            "player_name": player_name,
            "completion_time": completion_time,
            "difficulty": difficulty,
            "hints_used": hints_used,
        }
        leaderboard_entries = CURRENT.get("leaderboard", [])
        leaderboard_entries.append(entry)
        leaderboard_entries = sorted(leaderboard_entries, key=lambda item: item["completion_time"])
        CURRENT["leaderboard"] = leaderboard_entries[:10]
        return jsonify({"leaderboard": CURRENT["leaderboard"]})

    return jsonify({"leaderboard": CURRENT.get("leaderboard", [])})
