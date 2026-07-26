import app as app_module
import sudoku_logic


def test_create_app_returns_flask_application():
    from app_factory import create_app

    app = create_app()

    assert app is not None


def test_index_renders_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Sudoku Game" in response.data
    assert b"Check Puzzle" in response.data


def test_index_renders_theme_toggle_button(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'theme-toggle' in response.data
    assert b"Dark Mode" in response.data


def test_new_game_returns_puzzle_and_sets_current_game(client):
    response = client.get("/new?clues=40")
    assert response.status_code == 200
    data = response.get_json()
    assert "puzzle" in data
    assert len(data["puzzle"]) == sudoku_logic.SIZE
    assert len(data["puzzle"][0]) == sudoku_logic.SIZE
    assert app_module.CURRENT["puzzle"] == data["puzzle"]
    assert app_module.CURRENT["solution"] is not None
    assert data["timer"] == {"elapsed_seconds": 0, "running": True}
    assert app_module.CURRENT["timer_running"] is True
    assert app_module.CURRENT["elapsed_seconds"] == 0


def test_check_solution_without_active_game_returns_error(client):
    response = client.post(
        "/check",
        json={"board": [[1 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]},
    )
    assert response.status_code == 400
    assert response.get_json() == {"error": "No game in progress"}


def test_check_solution_returns_incorrect_cells(client):
    puzzle, solution = sudoku_logic.generate_puzzle(35)
    app_module.CURRENT["puzzle"] = puzzle
    app_module.CURRENT["solution"] = solution

    board = [row[:] for row in solution]
    board[0][0] = board[0][0] + 1 if board[0][0] < 9 else 1

    response = client.post("/check", json={"board": board})
    assert response.status_code == 200
    assert response.get_json()["incorrect"] == [[0, 0]]


def test_check_solution_returns_solved_state_for_correct_board(client):
    puzzle, solution = sudoku_logic.generate_puzzle(35)
    app_module.CURRENT["puzzle"] = puzzle
    app_module.CURRENT["solution"] = solution
    app_module.CURRENT["timer_running"] = True
    app_module.CURRENT["elapsed_seconds"] = 12

    response = client.post("/check", json={"board": solution})
    assert response.status_code == 200
    assert response.get_json()["solved"] is True
    assert response.get_json()["incorrect"] == []
    assert response.get_json()["timer"] == {"elapsed_seconds": 12, "running": False}
    assert app_module.CURRENT["timer_running"] is False


def test_check_solution_returns_conflicts_alongside_incorrect_cells(client):
    puzzle, solution = sudoku_logic.generate_puzzle(35)
    app_module.CURRENT["puzzle"] = puzzle
    app_module.CURRENT["solution"] = solution

    board = [row[:] for row in solution]
    board[0][0] = board[0][1]

    response = client.post("/check", json={"board": board})
    assert response.status_code == 200
    assert response.get_json()["incorrect"] == [[0, 0]]
    assert [0, 1] in response.get_json()["conflicts"]


def test_hint_returns_solution_value_and_marks_cell_locked(client):
    puzzle, solution = sudoku_logic.generate_puzzle(35)
    app_module.CURRENT["puzzle"] = puzzle
    app_module.CURRENT["solution"] = solution

    response = client.post("/hint")
    assert response.status_code == 200
    data = response.get_json()
    assert "row" in data and "col" in data and "value" in data
    assert data["value"] == solution[data["row"]][data["col"]]
    assert app_module.CURRENT["puzzle"][data["row"]][data["col"]] == data["value"]
    assert [data["row"], data["col"]] in app_module.CURRENT["locked_cells"]


def test_difficulty_levels_generate_unique_puzzles_with_expected_clue_counts():
    puzzle_easy, solution_easy = sudoku_logic.generate_puzzle(difficulty="Easy")
    puzzle_medium, solution_medium = sudoku_logic.generate_puzzle(difficulty="Medium")
    puzzle_hard, solution_hard = sudoku_logic.generate_puzzle(difficulty="Hard")

    assert sudoku_logic.count_solutions(puzzle_easy) == 1
    assert sudoku_logic.count_solutions(puzzle_medium) == 1
    assert sudoku_logic.count_solutions(puzzle_hard) == 1

    clues_easy = sum(cell != 0 for row in puzzle_easy for cell in row)
    clues_medium = sum(cell != 0 for row in puzzle_medium for cell in row)
    clues_hard = sum(cell != 0 for row in puzzle_hard for cell in row)

    assert clues_easy > clues_medium > clues_hard
    assert clues_easy >= 40
    assert clues_medium >= 30
    assert clues_hard >= 20


def test_generated_puzzle_is_validated_as_having_a_unique_solution():
    puzzle, solution = sudoku_logic.generate_puzzle(clues=30)

    assert sudoku_logic.is_unique_solution(puzzle)
    assert sudoku_logic.count_solutions(puzzle) == 1
    assert solution is not None


def test_validate_endpoint_reports_conflicting_cells(client):
    board = [[0 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]
    board[0][0] = 1
    board[0][1] = 1

    response = client.post("/validate", json={"board": board})
    assert response.status_code == 200
    assert set(tuple(cell) for cell in response.get_json()["conflicts"]) == {(0, 0), (0, 1)}


def test_validate_endpoint_returns_conflicts_for_duplicate_entries(client):
    puzzle, solution = sudoku_logic.generate_puzzle(35)
    app_module.CURRENT["puzzle"] = puzzle
    app_module.CURRENT["solution"] = solution

    board = [row[:] for row in puzzle]
    board[0][0] = 5
    board[0][1] = 5

    response = client.post("/validate", json={"board": board})
    assert response.status_code == 200
    assert [0, 0] in response.get_json()["conflicts"]


def test_leaderboard_endpoint_adds_and_sorts_entries(client):
    app_module.CURRENT["leaderboard"] = []

    first_response = client.post(
        "/leaderboard",
        json={"player_name": "Ava", "completion_time": 90, "difficulty": "Easy"},
    )
    assert first_response.status_code == 200
    assert first_response.get_json()["leaderboard"][0]["player_name"] == "Ava"

    second_response = client.post(
        "/leaderboard",
        json={"player_name": "Ben", "completion_time": 60, "difficulty": "Hard"},
    )

    assert second_response.status_code == 200
    leaderboard = second_response.get_json()["leaderboard"]
    assert leaderboard[0]["player_name"] == "Ben"
    assert leaderboard[0]["completion_time"] == 60
    assert leaderboard[1]["player_name"] == "Ava"
