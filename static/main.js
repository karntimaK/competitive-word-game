const socket = io("http://localhost:5000");

let roomId = null;
let playerName = "";
let opponentName = "";

// connect
socket.on("connect", () => {
  console.log("Connected to server");
  document.getElementById("status").innerText = "Connected to server.";
});

// find match
function findMatch() {
  playerName = document.getElementById("username").value || "Anonymous";
  socket.emit("find_match", { username: playerName });
  document.getElementById("status").innerText = "Finding a match...";
}

// matched
socket.on("matched", (data) => {
  roomId = data.room;
  const players = data.players;
  opponentName = players.find(name => name !== playerName);

  document.body.innerHTML = `
    <h2>Competitive Word Game</h2>
    <div>Player: ${playerName}</div>
    <div>Opponent: ${opponentName}</div>

    <div id="board">
      <table id="player_board"></table>
      <div>
        <input type="text" id="guess_input" maxlength="5">
        <button onclick="submitGuess()">Submit</button>
      </div>
    </div>

    <div id="opponent_board">
      <h4>Opponent</h4>
      <table id="opponent_table"></table>
    </div>
  `;

  createBoard("player_board");
  createBoard("opponent_table", true);
});

// create 6x5 table
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
function submitGuess() {
  const input = document.getElementById("guess_input");
  const guess = input.value.toUpperCase();
  if (!guess || guess.length !== 5) {
    alert("Enter a 5-letter word");
    return;
  }

  // ส่งไป server
  socket.emit("submit_guess", { room: roomId, guess: guess });

  input.value = "";
}

// รับ update จาก server → update ตารางผู้เล่นตัวเอง
socket.on("update_board", (data) => {
  const guess = data.guess;
  const table = document.getElementById("player_board");

  // วางคำในแถวถัดไป
  const rowIndex = table.rows.length - 6 + roomsGuessLength(table); // row ถัดไป
  const row = table.rows[rowIndex];

  if (row) {
    for (let i = 0; i < 5; i++) {
      const cell = row.cells[i];
      cell.innerText = guess[i];
      cell.style.backgroundColor = "#ccc"; // placeholder สีเทา
    }
  }
});

// helper: นับคำเดาที่มีใน table
function roomsGuessLength(table) {
  let count = 0;
  for (let r = 0; r < 6; r++) {
    let rowEmpty = table.rows[r].cells[0].innerText === "";
    if (!rowEmpty) count++;
  }
  return count;
}
