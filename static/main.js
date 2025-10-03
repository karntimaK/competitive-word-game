document.addEventListener("DOMContentLoaded", () => {
  const socket = io("http://localhost:5000");

  let roomId = null;
  let playerName = "";
  let opponentName = "";
  let playerGuessCount = 0;
  let opponentGuessCount = 0;

  // สร้าง div สำหรับแสดง status message
  const statusDiv = document.createElement("div");
  statusDiv.id = "status_message";
  document.body.appendChild(statusDiv);

  // update status helper
  function updateStatus(message) {
    statusDiv.innerText = message;
  }

  // สถานะเชื่อมต่อ server
  socket.on("connect", () => {
    updateStatus("Connected to server");
  });

  // find match
  window.findMatch = function() {
    playerName = document.getElementById("username").value || "Anonymous";
    updateStatus("Finding match...");
    socket.emit("find_match", { username: playerName });
  };

  // matched
  socket.on("matched", (data) => {
    roomId = data.room;
    const players = data.players;
    opponentName = players.find(name => name !== playerName);

    updateStatus(`Matched with ${opponentName}!`);

    document.body.innerHTML = `
      <h2>Competitive Word Game</h2>
      <div>Player: ${playerName}</div>
      <div>Opponent: ${opponentName}</div>

      <div id="board">
        <table id="player_board"></table>
        <div style="margin-top:5px;">
          <input type="text" id="guess_input" maxlength="5">
          <button onclick="submitGuess()">Submit</button>
        </div>
      </div>

      <div id="opponent_board">
        <h4>Opponent</h4>
        <table id="opponent_table"></table>
      </div>

      <div id="status_message"></div>
    `;

    // สร้างตาราง
    createBoard("player_board");
    createBoard("opponent_table", true);
  });

  // สร้างตาราง
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
        td.style.backgroundColor = isOpponent ? "#ddd" : "#fff";
        td.innerText = "";
        tr.appendChild(td);
      }
      table.appendChild(tr);
    }
  }

  // submit guess
  window.submitGuess = function() {
    const input = document.getElementById("guess_input");
    const guess = input.value.toUpperCase();
    if (!guess || guess.length !== 5) {
      alert("Enter a 5-letter word");
      return;
    }

    if (!roomId) {
      updateStatus("You are not in a room yet.");
      return;
    }

    updateStatus(`Submitting guess: ${guess}`);
    socket.emit("submit_guess", { room: roomId, guess: guess });
    input.value = "";
  };

  // update board player
  socket.on("update_board", (data) => {
    const guess = data.guess;
    const feedback = data.feedback;
    const table = document.getElementById("player_board");
    const rowIndex = playerGuessCount;
    const row = table.rows[rowIndex];

    if (row) {
      for (let i = 0; i < 5; i++) {
        const cell = row.cells[i];
        cell.innerText = guess[i];
        if (feedback[i] === "G") cell.style.backgroundColor = "green";
        else if (feedback[i] === "Y") cell.style.backgroundColor = "yellow";
        else cell.style.backgroundColor = "#ccc"; // GREY
      }
    }

    playerGuessCount++;
    updateStatus(`Last guess: ${guess}`);
  });

  // update opponent board (แสดง feedback ล่าสุด)
  socket.on("update_opponent_board", (data) => {
    const feedback = data.feedback;
    const table = document.getElementById("opponent_table");
    const rowIndex = opponentGuessCount;
    const row = table.rows[rowIndex];

    if (row) {
      for (let i = 0; i < 5; i++) {
        const cell = row.cells[i];
        if (feedback[i] === "G") cell.style.backgroundColor = "green";
        else if (feedback[i] === "Y") cell.style.backgroundColor = "yellow";
        else cell.style.backgroundColor = "#ccc";
      }
    }

    opponentGuessCount++;
  });

  // status message update จาก server
  socket.on("status", (data) => {
    if (data.message) updateStatus(data.message);
  });
});
