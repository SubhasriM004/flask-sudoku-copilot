CURRENT = {
    "puzzle": None,
    "solution": None,
    "locked_cells": [],
    "timer_running": False,
    "elapsed_seconds": 0,
    "leaderboard": [],
    "hints_used": 0,
}


def update_current_game(puzzle, solution):
    CURRENT["puzzle"] = puzzle
    CURRENT["solution"] = solution
    CURRENT["locked_cells"] = []
    CURRENT["timer_running"] = True
    CURRENT["elapsed_seconds"] = 0
    CURRENT["hints_used"] = 0
