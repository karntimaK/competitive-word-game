document.addEventListener("DOMContentLoaded", () => {
  const socket = io("http://localhost:5000");

  let roomId = null;
  let playerName = "";
  let opponentName = "";
  let playerGuessCount = 0;
  let opponentGuessCount = 0;

  // สร้าง div สำหรับแสดง status message
  let statusDiv = document.createElement("div");
  statusDiv.id = "status_message";
  document.body.appendChild(statusDiv);

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
          const resultDiv = document.getElementById("result_message");
          if(resultDiv) resultDiv.innerText = ""; // เคลียร์ข้อความเดิม
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

    createBoard("player_board");
    createBoard("opponent_table", true);

    // reset guess counts
    playerGuessCount = 0;
    opponentGuessCount = 0;
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
        td.style.backgroundColor = isOpponent ? "#eee" : "#fff";
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
  });

  // update opponent board (feedback สีเท่านั้น)
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
        else cell.style.backgroundColor = "#aaa";
      }
    }
    opponentGuessCount++;
  });

  // status message update จาก server
  socket.on("status", (data) => {
    if (data.message) updateStatus(data.message);
  });

  // game result
  // กลับไปหน้าหาห้อง พร้อมแสดงผล
        socket.on("game_result", (data) => {
          let resultMessage = "";
          if (data.result === "win") resultMessage = "You win!";
          else if (data.result === "lose") resultMessage = "You lose!";

          document.body.innerHTML = `
                <h2>Competitive Word Game</h2>
                <input type="text" id="username" placeholder="Enter your name">
                <button id="find_button">Find Match</button>
                <div id="result_message" style="margin-top:10px; font-weight:bold;">${resultMessage}</div>
                <div id="status_message"></div>
          `;

          // สร้าง reference ใหม่ให้ statusDiv
          statusDiv = document.getElementById("status_message");

          // attach event
          document.getElementById("find_button").addEventListener("click", () => {
                findMatch();
          });
        });
});
