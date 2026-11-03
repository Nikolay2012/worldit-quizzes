const pauseButton = document.querySelector(".pause-btn")
const addTimeButton = document.querySelector(".add-time-btn")


function setPauseButton(paused) {
    const icon = pauseButton.querySelector(".pause-icon")
    const text = pauseButton.querySelector(".pause-text")

    if (paused) {
        icon.src = pauseButton.dataset.playIcon
        text.textContent = pauseButton.dataset.playText
    } else {
        icon.src = pauseButton.dataset.pauseIcon
        text.textContent = pauseButton.dataset.pauseText
    }
}


pauseButton.addEventListener("click", () => {
    roomSocket.send(JSON.stringify({ action: "pause" }))
})

// +15 секунд
addTimeButton.addEventListener("click", () => {
    roomSocket.send(JSON.stringify({ action: "add_time" }))
})


roomSocket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data)

    if (data.action === "time_changed") {
        setPauseButton(data.paused)
    }
})

document.addEventListener("question:changed", () => {
    setPauseButton(false)
})