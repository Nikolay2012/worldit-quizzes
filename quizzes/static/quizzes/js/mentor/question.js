const nextButton = document.querySelector(".next-btn")
const finishButton = document.querySelector(".finish-btn")
const panelSub = document.querySelector(".panel-sub")
const questionHint = document.querySelector(".question-card .info-meta")

nextButton.addEventListener("click", () => {
    roomSocket.send(JSON.stringify({ action: "next_question" }))
})

finishButton.addEventListener("click", () => {
    roomSocket.send(JSON.stringify({ action: "finish" }))
})

document.addEventListener("question:changed", (event) => {
    const data = event.detail
    panelSub.textContent = `Запитання ${data.number} з ${data.total}`
    questionHint.textContent = data.type
})