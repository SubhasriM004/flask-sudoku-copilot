// Client-side rendering and interaction for the Flask-backed Sudoku
const SIZE = 9;
const LEADERBOARD_STORAGE_KEY = 'sudoku-leaderboard';
const THEME_STORAGE_KEY = 'sudoku-theme';
let puzzle = [];
let lockedCells = new Set();
let timerInterval = null;
let elapsedSeconds = 0;
let leaderboardEntries = [];
let scoreRecordedForCurrentGame = false;
let hintedCellIndexes = new Set();
let liveConflictIndexes = new Set();
let checkConflictIndexes = new Set();

function getPreferredTheme() {
  try {
    const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (storedTheme === 'dark' || storedTheme === 'light') {
      return storedTheme;
    }
  } catch (error) {
    // Fall back to the system preference when storage is unavailable.
  }

  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(theme) {
  document.body.dataset.theme = theme;
  const toggleButton = document.getElementById('theme-toggle');
  if (toggleButton) {
    toggleButton.innerText = theme === 'dark' ? 'Light Mode' : 'Dark Mode';
    toggleButton.setAttribute('aria-pressed', String(theme === 'dark'));
  }
}

function initializeTheme() {
  const theme = getPreferredTheme();
  applyTheme(theme);
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch (error) {
    // Ignore storage failures.
  }
}

function toggleTheme() {
  const nextTheme = document.body.dataset.theme === 'dark' ? 'light' : 'dark';
  applyTheme(nextTheme);
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
  } catch (error) {
    // Ignore storage failures.
  }
}

function updateTimerDisplay() {
  const timerEl = document.getElementById('timer-display');
  if (!timerEl) {
    return;
  }
  const minutes = Math.floor(elapsedSeconds / 60).toString().padStart(2, '0');
  const seconds = (elapsedSeconds % 60).toString().padStart(2, '0');
  timerEl.innerText = `Time: ${minutes}:${seconds}`;
}

function startTimer() {
  clearInterval(timerInterval);
  elapsedSeconds = 0;
  updateTimerDisplay();
  timerInterval = window.setInterval(() => {
    elapsedSeconds += 1;
    updateTimerDisplay();
  }, 1000);
}

function stopTimer() {
  clearInterval(timerInterval);
  timerInterval = null;
}

function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, '0');
  const seconds = (totalSeconds % 60).toString().padStart(2, '0');
  return `${minutes}:${seconds}`;
}

function loadLeaderboardFromStorage() {
  try {
    const stored = window.localStorage.getItem(LEADERBOARD_STORAGE_KEY);
    if (!stored) {
      return [];
    }
    const parsed = JSON.parse(stored);
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    return [];
  }
}

function saveLeaderboardToStorage(entries) {
  window.localStorage.setItem(LEADERBOARD_STORAGE_KEY, JSON.stringify(entries));
}

function renderLeaderboard(entries = leaderboardEntries) {
  const listEl = document.getElementById('leaderboard-list');
  if (!listEl) {
    return;
  }

  listEl.innerHTML = '';
  if (!entries.length) {
    const item = document.createElement('li');
    item.innerText = 'No completed games yet.';
    listEl.appendChild(item);
    return;
  }

  entries.forEach((entry, index) => {
    const item = document.createElement('li');
    item.innerText = `${index + 1}. ${entry.player_name} — ${formatTime(entry.completion_time)} — ${entry.difficulty}`;
    listEl.appendChild(item);
  });
}

async function loadLeaderboard() {
  const storedEntries = loadLeaderboardFromStorage();
  leaderboardEntries = storedEntries;
  renderLeaderboard();

  try {
    const res = await fetch('/leaderboard');
    const data = await res.json();
    if (Array.isArray(data.leaderboard) && data.leaderboard.length > 0) {
      leaderboardEntries = data.leaderboard;
      saveLeaderboardToStorage(leaderboardEntries);
      renderLeaderboard();
    }
  } catch (error) {
    // Keep the locally stored leaderboard visible if the server is unavailable.
  }
}

async function addLeaderboardEntry(playerName, completionTime, difficulty) {
  const entry = {
    player_name: playerName,
    completion_time: completionTime,
    difficulty,
  };

  const updatedEntries = [...leaderboardEntries, entry]
    .sort((a, b) => a.completion_time - b.completion_time)
    .slice(0, 10);
  leaderboardEntries = updatedEntries;
  saveLeaderboardToStorage(leaderboardEntries);
  renderLeaderboard();

  try {
    const res = await fetch('/leaderboard', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(entry),
    });
    const data = await res.json();
    if (Array.isArray(data.leaderboard)) {
      leaderboardEntries = data.leaderboard;
      saveLeaderboardToStorage(leaderboardEntries);
      renderLeaderboard();
    }
  } catch (error) {
    // The in-browser storage already has the new score.
  }
}

function collectBoardFromInputs() {
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv ? boardDiv.getElementsByTagName('input') : [];
  const board = [];
  for (let i = 0; i < SIZE; i++) {
    board[i] = [];
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = inputs[idx].value;
      board[i][j] = val ? parseInt(val, 10) : 0;
    }
  }
  return board;
}

function applyBoardVisualState({ conflictIndexes = [], hintIndexes = [] } = {}) {
  const boardDiv = document.getElementById('sudoku-board');
  if (!boardDiv) {
    return;
  }

  const inputs = boardDiv.getElementsByTagName('input');
  const hintSet = new Set((hintIndexes || []).map((value) => Number(value)));
  const conflictSet = new Set((conflictIndexes || []).map((value) => Number(value)));

  for (let idx = 0; idx < inputs.length; idx++) {
    const inp = inputs[idx];
    const classes = ['sudoku-cell'];

    if (inp.disabled) {
      classes.push('prefilled');
    }

    if (hintSet.has(idx)) {
      classes.push('hint');
    }

    if (conflictSet.has(idx)) {
      classes.push('live-conflict');
    }

    inp.className = classes.join(' ');
  }
}

async function validateBoardLive() {
  const board = collectBoardFromInputs();

  try {
    const res = await fetch('/validate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({board}),
    });
    const data = await res.json();
    const conflicts = Array.isArray(data.conflicts) ? data.conflicts : [];
    const conflictIndexes = conflicts.map(([row, col]) => row * SIZE + col);
    const activeIndex = Number(document.activeElement?.dataset?.row) * SIZE + Number(document.activeElement?.dataset?.col);
    liveConflictIndexes = new Set(conflictIndexes.includes(activeIndex) ? [activeIndex] : []);
    applyBoardVisualState({
      conflictIndexes: [...liveConflictIndexes, ...checkConflictIndexes],
      hintIndexes: [...hintedCellIndexes],
    });
  } catch (error) {
    liveConflictIndexes.clear();
    applyBoardVisualState({
      conflictIndexes: [...checkConflictIndexes],
      hintIndexes: [...hintedCellIndexes],
    });
  }
}

function createBoardElement() {
  const boardDiv = document.getElementById('sudoku-board');
  boardDiv.innerHTML = '';
  for (let i = 0; i < SIZE; i++) {
    const rowDiv = document.createElement('div');
    rowDiv.className = 'sudoku-row';
    for (let j = 0; j < SIZE; j++) {
      const input = document.createElement('input');
      input.type = 'text';
      input.maxLength = 1;
      input.className = 'sudoku-cell';
      input.dataset.row = i;
      input.dataset.col = j;
      input.dataset.square = `${Math.floor(i / 3) * 3 + Math.floor(j / 3)}`;
      input.setAttribute('aria-label', `Row ${i + 1}, Column ${j + 1}`);
      input.addEventListener('input', async (e) => {
        const val = e.target.value.replace(/[^1-9]/g, '');
        e.target.value = val;
        const row = Number(e.target.dataset.row);
        const col = Number(e.target.dataset.col);
        const idx = row * SIZE + col;
        if (hintedCellIndexes.has(idx)) {
          hintedCellIndexes.delete(idx);
        }
        await validateBoardLive();
      });
      rowDiv.appendChild(input);
    }
    boardDiv.appendChild(rowDiv);
  }
}

function renderPuzzle(puz, locked = []) {
  puzzle = puz;
  lockedCells = new Set(locked.map(([row, col]) => row * SIZE + col));
  createBoardElement();
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  for (let i = 0; i < SIZE; i++) {
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = puzzle[i][j];
      const inp = inputs[idx];
      const isLocked = lockedCells.has(idx);
      if (val !== 0) {
        inp.value = val;
        inp.disabled = true;
      } else {
        inp.value = '';
        inp.disabled = false;
      }
      if (isLocked && val !== 0) {
        inp.disabled = true;
      }
    }
  }

  liveConflictIndexes.clear();
  checkConflictIndexes.clear();
  applyBoardVisualState({ conflictIndexes: [], hintIndexes: [...hintedCellIndexes] });
}

async function newGame() {
  const difficulty = document.getElementById('difficulty-select').value;
  scoreRecordedForCurrentGame = false;
  hintedCellIndexes.clear();
  liveConflictIndexes.clear();
  checkConflictIndexes.clear();
  const res = await fetch(`/new?difficulty=${encodeURIComponent(difficulty)}`);
  const data = await res.json();
  renderPuzzle(data.puzzle);
  document.getElementById('message').innerText = '';
  elapsedSeconds = data.timer?.elapsed_seconds || 0;
  updateTimerDisplay();
  if (data.timer?.running) {
    startTimer();
  } else {
    stopTimer();
  }
}

async function hint() {
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  const board = [];
  for (let i = 0; i < SIZE; i++) {
    board[i] = [];
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = inputs[idx].value;
      board[i][j] = val ? parseInt(val, 10) : 0;
    }
  }

  const res = await fetch('/hint', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({board})
  });
  const data = await res.json();
  const msg = document.getElementById('message');
  if (data.error) {
    msg.style.color = 'var(--message-error)';
    msg.innerText = data.error;
    return;
  }
  if (data.row !== undefined && data.col !== undefined) {
    hintedCellIndexes.add(data.row * SIZE + data.col);
  }
  renderPuzzle(data.puzzle, data.locked_cells || []);
  msg.style.color = 'var(--message-success)';
  msg.innerText = 'Hint applied.';
}

async function checkSolution() {
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  const board = [];
  for (let i = 0; i < SIZE; i++) {
    board[i] = [];
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = inputs[idx].value;
      board[i][j] = val ? parseInt(val, 10) : 0;
    }
  }

  const res = await fetch('/check', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({board})
  });
  const data = await res.json();
  const msg = document.getElementById('message');

  if (data.error) {
    msg.style.color = 'var(--message-error)';
    msg.innerText = data.error;
    return;
  }

  const conflicts = Array.isArray(data.conflicts) ? data.conflicts : [];
  const conflictIndexes = conflicts.map(([row, col]) => row * SIZE + col);
  checkConflictIndexes = new Set(conflictIndexes);
  liveConflictIndexes.clear();
  applyBoardVisualState({ conflictIndexes: [...checkConflictIndexes], hintIndexes: [...hintedCellIndexes] });

  if (conflicts.length === 0) {
    stopTimer();
    if (!scoreRecordedForCurrentGame) {
      const playerName = window.prompt('Enter your name for the leaderboard:');
      const name = (playerName || '').trim() || 'Player';
      await addLeaderboardEntry(name, elapsedSeconds, document.getElementById('difficulty-select').value);
      scoreRecordedForCurrentGame = true;
    }
    msg.style.color = 'var(--message-success)';
    msg.innerText = 'Congratulations! You solved it!';
  } else {
    msg.style.color = 'var(--message-error)';
    msg.innerText = 'Some cells are incorrect.';
  }
}

// Wire buttons
window.addEventListener('load', () => {
  document.getElementById('new-game').addEventListener('click', newGame);
  document.getElementById('hint').addEventListener('click', hint);
  document.getElementById('check-solution').addEventListener('click', checkSolution);
  document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
  initializeTheme();
  // initialize
  loadLeaderboard();
  newGame();
});