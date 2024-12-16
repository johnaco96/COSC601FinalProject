const socket = io();

document.getElementById("send-btn").addEventListener("click", () => {
    const userInput = document.getElementById("user-input").value;
    if (userInput.trim() !== "") {
        addMessage("user", userInput);
        socket.emit("message", { message: userInput });
        document.getElementById("user-input").value = "";
    }
});

socket.on("response", (data) => {
    addMessage("bot", data.message);
});

function addMessage(sender, message) {
    const chatbox = document.getElementById("chatbox");
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${sender}`;
    msgDiv.textContent = message;
    chatbox.appendChild(msgDiv);
    chatbox.scrollTop = chatbox.scrollHeight;
}
