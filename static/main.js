document.addEventListener("DOMContentLoaded", () => {
  const socket = io("http://localhost:5000");

  let roomId = null;
  let playerName = "";
  let opponentName = "";
  let playerGuessCount = 0;
  let opponentGuessCount = 0;

  const appRoot = document.createElement("div");
  appRoot.id = "app_root";
  document.body.appendChild(appRoot);

  const statusDiv = document.createElement("div");
  statusDiv.id = "status_message";
  appRoot.appendChild(statusDiv);

  function updateStatus(message) {
    // ล้าง class สีเก่าออกก่อนอัปเดตข้อความสถานะปกติ
    statusDiv.className = "";
    statusDiv.innerText = message || "";
  }

  function renderLobby() {
    appRoot.innerHTML = "";
    appRoot.appendChild(statusDiv);
    updateStatus(""); // เคลียร์สถานะเมื่อกลับมาที่ล็อบบี้

    const title = document.createElement("h2");
    title.innerText = "Competitive Word Game";
    appRoot.appendChild(title);

    const lobby = document.createElement("div");
    lobby.id = "lobby";

    const input = document.createElement("input");
    input.id = "username";
    input.type = "text";
    input.placeholder = "Enter your name";


    const findBtn = document.createElement("button");
    findBtn.id = "find_btn";
    findBtn.innerText = "Find Match";
    findBtn.addEventListener("click", () => {
      playerName = document.getElementById("username").value || "Anonymous";
      updateStatus("Finding match...");
      socket.emit("find_match", { username: playerName });
    });

    const createBtn = document.createElement("button");
    createBtn.id = "create_btn";
    createBtn.innerText = "Create Room (Private)";
    createBtn.addEventListener("click", () => {
      playerName = document.getElementById("username").value || "Anonymous";
      socket.emit("create_room", { username: playerName });
      updateStatus("Creating room...");
    });

    const joinBtn = document.createElement("button");
    joinBtn.id = "show_join_btn";
    joinBtn.innerText = "Join Room";
    joinBtn.addEventListener("click", () => {
      showJoinInput();
    });

    const joinContainer = document.createElement("div");
    joinContainer.id = "join_container";
    joinContainer.style.display = "none";

    const joinInput = document.createElement("input");
    joinInput.id = "join_code_input";
    joinInput.type = "text";
    joinInput.placeholder = "6-digit code";

    const joinSend = document.createElement("button");
    joinSend.innerText = "Join";
    joinSend.addEventListener("click", () => {
      const code = document.getElementById("join_code_input").value.trim();
      playerName = document.getElementById("username").value || "Anonymous";
      if (!/^\d{6}$/.test(code)) {
        alert("Enter a 6-digit code");
        return;
      }
      updateStatus(`Joining room ${code}...`);
      socket.emit("join_room_code", { code: code, username: playerName });
    });

    joinContainer.appendChild(joinInput);
    joinContainer.appendChild(joinSend);

    lobby.appendChild(input);
    lobby.appendChild(findBtn);
    lobby.appendChild(createBtn);
    lobby.appendChild(joinBtn);
    lobby.appendChild(joinContainer);

    appRoot.appendChild(lobby);
  }

  function showJoinInput() {
    const cont = document.getElementById("join_container");
    if (cont) cont.style.display = "block";
  }

  renderLobby();

  socket.on("connect", () => updateStatus("Connected to server"));

  socket.on("room_created", (data) => {
    roomId = data.room;
    const code = data.code;
    updateStatus(`Room created. Share code: ${code}. Waiting for opponent...`);
    renderWaitingRoom(code);
  });

  socket.on("join_failed", (data) => {
    updateStatus(data.message || "Failed to join room");
    alert(data.message || "Failed to join room");
  });

  socket.on("matched", (data) => {
    roomId = data.room;
    const players = data.players;
    opponentName = players.find(name => name !== playerName) || "Opponent";
    renderGameUI();
    updateStatus(`Matched with ${opponentName}`);
  });

  socket.on("status", (data) => {
    if (data && data.message) updateStatus(data.message);
  });

  socket.on("invalid_word", (data) => {
    alert(`"${data.word}" is not in the dictionary`);
  });

  socket.on("time_update", (data) => {
    const timerEl = document.getElementById("timer");
    if (timerEl) {
      const minutes = Math.floor(data.seconds / 60);
      const seconds = data.seconds % 60;
      timerEl.innerText = `${minutes}:${seconds.toString().padStart(2,'0')}`;
    }
  });

  /**
   * ============== 🎯 ส่วนที่แก้ไข 🎯 ==============
   * แก้ไขการแสดงผลลัพธ์ของเกม
   */
  socket.on("game_result", (data) => {
    const input = document.getElementById("guess_input");
    const submit = document.getElementById("submit_btn");
    if (input) input.disabled = true;
    if (submit) submit.disabled = true;

    let msg = "";
    if (data.result === "win") msg = "🎇🎇🥳You win🎇🥳🙌";
    else if (data.result === "lose") msg = "🥀🥀😭You lose😭😭💔";
    if (data.reason === "time_expired" || data.reason === "timeout") msg = "Time's up — both lose!";
    if (data.reason === "turns_exhausted") msg += " (turns exhausted)";
    if (data.reason === "opponent_disconnected") msg = "Opponent disconnected — You win!";

    // --- ย้ายการแสดงผลลัพธ์ไปที่ statusDiv ด้านบน ---
    statusDiv.innerText = msg;
    statusDiv.className = ""; // เคลียร์ class เก่า
    if (data.result === "win" || data.reason === "opponent_disconnected") {
        statusDiv.classList.add("status-win");
    } else {
        statusDiv.classList.add("status-lose");
    }
    
    // --- สร้างปุ่มกลับล็อบบี้ ---
    const backBtn = document.createElement("button");
    backBtn.id = "back_lobby_btn";
    backBtn.innerText = "Back to Lobby";
    backBtn.style.marginTop = "16px";
    backBtn.addEventListener("click", () => {
      socket.emit("leave_room", {});
      renderLobby();
      roomId = null;
      playerGuessCount = 0;
      opponentGuessCount = 0;
    });

    // --- เพิ่มปุ่มไว้ใต้กระดานของผู้เล่น ---
    const playerColumn = document.getElementById("player_column");
    if (playerColumn) {
        playerColumn.appendChild(backBtn);
    } else {
      // กรณีฉุกเฉิน หากหา playerColumn ไม่เจอ
      const boardWrapper = document.getElementById("board_wrapper");
      if (boardWrapper) {
          boardWrapper.appendChild(backBtn);
      } else {
          alert(msg);
          renderLobby();
      }
    }
  });
  
  socket.on("player_disconnected", (data) => {
    updateStatus(data.message || "Opponent disconnected");
  });

  function renderWaitingRoom(code) {
    appRoot.innerHTML = "";
    appRoot.appendChild(statusDiv);
    const title = document.createElement("h2");
    title.innerText = "Private Room Created";
    appRoot.appendChild(title);
    const codeDiv = document.createElement("div");
    codeDiv.innerHTML = `<strong>Room code:</strong> ${code} <br/>Share with your friend to join.`;
    appRoot.appendChild(codeDiv);
    const cancelBtn = document.createElement("button");
    cancelBtn.innerText = "Cancel and Back";
    cancelBtn.addEventListener("click", () => {
      socket.emit("leave_room", {});
      renderLobby();
    });
    appRoot.appendChild(cancelBtn);
  }
  
  /**
   * ============== 🎯 ส่วนที่แก้ไข 🎯 ==============
   * ลบแถวแสดงชื่อ Player/Opponent ออก
   */
  function renderGameUI() {
    appRoot.innerHTML = "";
    appRoot.appendChild(statusDiv);

    const title = document.createElement("h2");
    title.innerText = "Competitive Word Game";
    appRoot.appendChild(title);

    // --- [ลบออก] แถวแสดงชื่อ Player และ Opponent ---

    const timerDiv = document.createElement("div");
    timerDiv.id = "timer";
    timerDiv.innerText = "5:00";
    appRoot.appendChild(timerDiv);

    const boardWrapper = document.createElement("div");
    boardWrapper.id = "board_wrapper";

    const playerColumn = document.createElement("div");
    playerColumn.id = "player_column";

    const playerBoard = document.createElement("table");
    playerBoard.id = "player_board";
    
    const inputRow = document.createElement("div");
    inputRow.style.marginTop = "16px";
    inputRow.style.display = "flex";
    inputRow.style.gap = "8px";

    const guessInput = document.createElement("input");
    guessInput.id = "guess_input";
    guessInput.type = "text";
    guessInput.maxLength = 5;
    guessInput.placeholder = "Type guess";
    guessInput.style.flex = "1";

    const submitBtn = document.createElement("button");
    submitBtn.id = "submit_btn";
    submitBtn.innerText = "Submit";
    submitBtn.addEventListener("click", submitGuess);

    inputRow.appendChild(guessInput);
    inputRow.appendChild(submitBtn);

    playerColumn.appendChild(playerBoard);
    playerColumn.appendChild(inputRow);

    // --- ส่วนของคู่ต่อสู้ ---
    const oppWrap = document.createElement("div");
    const oppTitle = document.createElement("h4");
    // --- [แก้ไข] เปลี่ยน Title ของกระดานเป็นชื่อ Opponent ---
    oppTitle.innerText = `${opponentName}'s Board`; 
    oppTitle.style.marginLeft = "15px";

    const oppTable = document.createElement("table");
    oppTable.id = "opponent_table";
    
    oppWrap.appendChild(oppTitle);
    oppWrap.appendChild(oppTable);

    boardWrapper.appendChild(playerColumn);
    boardWrapper.appendChild(oppWrap);

    appRoot.appendChild(boardWrapper);

    createBoard("player_board");
    createBoard("opponent_table", true);

    playerGuessCount = 0;
    opponentGuessCount = 0;
  }

  function createBoard(tableId, isOpponent=false) {
    const table = document.getElementById(tableId);
    table.innerHTML = "";
    for (let r = 0; r < 6; r++) {
      const tr = document.createElement("tr");
      for (let c = 0; c < 5; c++) {
        const td = document.createElement("td");
        tr.appendChild(td);
      }
      table.appendChild(tr);
    }
  }

  /**
   * ============== 🎯 ส่วนที่แก้ไข 🎯 ==============
   * ลบการอัปเดตสถานะ "Submitting guess" ออก
   */
  function submitGuess() {
    const input = document.getElementById("guess_input");
    const guess = (input && input.value) ? input.value.toUpperCase().trim() : "";
    if (!guess || guess.length !== 5) {
      alert("Enter a 5-letter word");
      return;
    }
    if (!roomId) {
      updateStatus("You are not in a room yet.");
      return;
    }
    // --- [ลบออก] บรรทัดอัปเดตสถานะตอนส่งคำตอบ ---
    socket.emit("submit_guess", { room: roomId, guess: guess });
    if (input) input.value = "";
  }

  socket.on("update_board", (data) => {
    const guess = data.guess;
    const feedback = data.feedback;
    const table = document.getElementById("player_board");
    const row = table.rows[playerGuessCount];
    if (row) {
      for (let i = 0; i < 5; i++) {
        const cell = row.cells[i];
        cell.innerText = guess[i];
        if (feedback[i] === "G") cell.className = "green";
        else if (feedback[i] === "Y") cell.className = "yellow";
        else cell.className = "gray";
      }
    }
    playerGuessCount++;
  });

  socket.on("update_opponent_board", (data) => {
    const feedback = data.feedback;
    const table = document.getElementById("opponent_table");
    const row = table.rows[opponentGuessCount];
    if (row) {
      for (let i = d = 0; i < 5; i++) {
        const cell = row.cells[i];
        if (feedback[i] === "G") cell.className = "green";
        else if (feedback[i] === "Y") cell.className = "yellow";
        else cell.className = "gray";
      }
    }
    opponentGuessCount++;
  });

});
