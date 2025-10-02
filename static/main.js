const socket = io("http://localhost:5000");

socket.on("connect", () => {
  console.log("Connected to server");
  document.getElementById("status").innerText = "Connected to server.";
});

function findMatch() {
  const username = document.getElementById("username").value || "Anonymous";
  socket.emit("find_match", { username: username });
  document.getElementById("status").innerText = "Finding a match...";
}
