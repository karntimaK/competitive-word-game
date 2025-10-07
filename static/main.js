document.addEventListener("DOMContentLoaded", () => {
  const socket = io("http://localhost:5000");

  let roomId = null;
  let playerName = "";
  let opponentName = "";
  let playerGuessCount = 0;
  let opponentGuessCount = 0;

  let statusDiv = document.createElement("div");
  statusDiv.id = "status_message";
  document.body.appendChild(statusDiv);

  function updateStatus(message) {
    statusDiv.innerText = message;
  }

  socket.on("connect", () => updateStatus("Connected to server"));

  window.findMatch = function() {
    playerName = document.getElementById("username").value || "Anonymous";
    const resultDiv = document.getElementById("result_message");
    if(resultDiv) resultDiv.innerText = "";
    updateStatus("Finding match...");
    socket.emit("find_match", { username: playerName });
  };

  socket.on("matched", (data) => {
    roomId = data.room;
    const players = data.players;
    opponentName = players.find(name => name !== playerName);

    document.body.innerHTML = `
      <h2>Competitive Word Game</h2>
      <div>Player: ${playerName}</div>
      <div>Opponent: ${opponentName}</div>

      <div id="timer">Time left: 5:00</div>

      <div id="board">
        <table id="player_board"></table>
        <div style="margin-top:5px;">
          <input type="text" id="guess_input" maxlength="5">
          <button id="submit_btn">Submit</button>
        </div>
      </div>

      <div id="opponent_board">
        <h4>Opponent</h4>
        <table id="opponent_table"></table>
      </div>

      <div id="status_message"></div>
    `;

    document.getElementById("submit_btn").addEventListener("click", submitGuess);
    createBoard("player_board");
    createBoard("opponent_table", true);
    playerGuessCount = 0;
    opponentGuessCount = 0;
  });

  function createBoard(tableId, isOpponent=false) {
    const table = document.getElementById(tableId);
    table.innerHTML = "";
    for (let r = 0; r < 6; r++) {
      const tr = document.createElement("tr");
      for (let c = 0; c < 5; c++) {
        const td = document.createElement("td");
        td.style.border = "1px solid #000";
        td.style.width = "30px";
        td.style.height = "30px";
        td.style.textAlign = "center";
        td.style.verticalAlign = "middle";
        td.style.backgroundColor = isOpponent ? "#eee" : "#fff";
        tr.appendChild(td);
      }
      table.appendChild(tr);
    }
  }

  window.submitGuess = function() {
    const input = document.getElementById("guess_input");
    const guess = input.value.toUpperCase();
    if (!guess || guess.length !== 5) { alert("Enter a 5-letter word"); return; }
    if (!roomId) { updateStatus("You are not in a room yet."); return; }
    updateStatus(`Submitting guess: ${guess}`);
    socket.emit("submit_guess", { room: roomId, guess: guess });
    input.value = "";
  };

  socket.on("update_board", (data) => {
    const table = document.getElementById("player_board");
    const row = table.rows[playerGuessCount];
    if (row) {
      for (let i = 0; i < 5; i++) {
        row.cells[i].innerText = data.guess[i];
        row.cells[i].style.backgroundColor = data.feedback[i] === "G" ? "green"
          : data.feedback[i] === "Y" ? "yellow" : "#ccc";
      }
    }
    playerGuessCount++;
  });

  socket.on("update_opponent_board", (data) => {
    const table = document.getElementById("opponent_table");
    const row = table.rows[opponentGuessCount];
    if (row) {
      for (let i = 0; i < 5; i++) {
        row.cells[i].style.backgroundColor = data.feedback[i] === "G" ? "green"
          : data.feedback[i] === "Y" ? "yellow" : "#aaa";
      }
    }
    opponentGuessCount++;
  });

  socket.on("time_update", (data) => {
    const minutes = Math.floor(data.seconds / 60);
    const seconds = data.seconds % 60;
    const timerDiv = document.getElementById("timer");
    if (timerDiv) timerDiv.innerText = `Time left: ${minutes}:${seconds.toString().padStart(2,'0')}`;
  });

  socket.on("status", (data) => { if (data.message) updateStatus(data.message); });
  socket.on("invalid_word", data => { alert(`"${data.word}" is not in the dictionary`); });

  socket.on("game_result", (data) => {
    const inputField = document.getElementById("guess_input");
    const submitBtn = document.getElementById("submit_btn");
    if(inputField) inputField.disabled = true;
    if(submitBtn) submitBtn.disabled = true;

    let message = "";
    if (data.result === "win") message = "You win!";
    else if (data.result === "lose") message = "You lose!";

    if(data.reason === "turns_exhausted") message += " (turns exhausted)";

    document.body.innerHTML = `
      <h2>Competitive Word Game</h2>
      <input type="text" id="username" placeholder="Enter your name">
      <button id="find_button">Find Match</button>
      <div id="result_message" style="margin-top:10px; font-weight:bold;">${message}</div>
      <div id="status_message"></div>
    `;

    statusDiv = document.getElementById("status_message");
    document.getElementById("find_button").addEventListener("click", findMatch);
  });
});
