const socket = io("http://localhost:5000");

let myUsername = "";
let opponentUsername = "";

socket.on("connect", () => {
  console.log("Connected to server");
  document.getElementById("status").innerText = "Connected to server.";
});

function findMatch() {
  myUsername = document.getElementById("username").value || "Anonymous";
  socket.emit("find_match", { username: myUsername });
  document.getElementById("status").innerText = "Finding a match...";
}

socket.on("status", (data) => {
  document.getElementById("status").innerText = data.message;
});

socket.on("matched", (data) => {
  // ซ่อนหน้า lobby / input username
  document.getElementById("lobby").style.display = "none";
  // แสดงหน้าเกม
  document.getElementById("game").style.display = "block";

  // แก้ชื่อ player / opponent ให้ตรง
  if (data.players[0] === myUsername) {
    opponentUsername = data.players[1];
  } else {
    opponentUsername = data.players[0];
  }

  document.getElementById("player-name").innerText = myUsername;
  document.getElementById("opponent-name").innerText = opponentUsername;

  // สร้างตาราง placeholder
  generatePlayerTable();
  generateOpponentTable();
});

function generatePlayerTable() {
  const table = document.getElementById("player-table");
  table.innerHTML = ""; // reset
  for (let i = 0; i < 6; i++) {
    const tr = document.createElement("tr");
    for (let j = 0; j < 5; j++) {
      const td = document.createElement("td");
      td.style.width = "30px";
      td.style.height = "30px";
      td.style.border = "1px solid #000";
      td.style.textAlign = "center";
      td.style.backgroundColor = "#fff"; // placeholder สี
      td.innerText = ""; // ยังไม่เชื่อม logic
      tr.appendChild(td);
    }
    table.appendChild(tr);
  }
}

function generateOpponentTable() {
  const table = document.getElementById("opponent-table");
  table.innerHTML = ""; // reset
  for (let i = 0; i < 6; i++) {
    const tr = document.createElement("tr");
    for (let j = 0; j < 5; j++) {
      const td = document.createElement("td");
      td.style.width = "15px";
      td.style.height = "15px";
      td.style.border = "1px solid #000";
      td.style.textAlign = "center";
      td.style.backgroundColor = "#ccc"; // placeholder สี opponent
      tr.appendChild(td);
    }
    table.appendChild(tr);
  }
}

function submitGuess() {
  const input = document.getElementById("guess-input").value.toUpperCase();
  if (!input) return;
  console.log("Submitted guess:", input);
  document.getElementById("guess-input").value = "";

  const table = document.getElementById("player-table");
  for (let row of table.rows) {
    for (let cell of row.cells) {
      if (cell.innerText === "") {
        for (let i = 0; i < 5; i++) {
          cell.innerText = input[i] || "";
        }
        return;
      }
    }
  }
}
