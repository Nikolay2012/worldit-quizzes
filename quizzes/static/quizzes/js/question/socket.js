const lobby = document.querySelector(".lobby")
const roomId = lobby.dataset.roomId
const finishUrl = lobby.dataset.finishUrl

const protocol = window.location.protocol === "https:" ? "wss" : "ws"
const roomSocket = new WebSocket(`${protocol}://${window.location.host}/ws/quizzes/room/${roomId}/`)

const LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H"]

function markAnswered(data) {
    const count = document.querySelector(".answered-count")
    count.textContent = `${data.answered} / ${data.total}`

    const fill = document.querySelector(".progress-fill")
    if (data.total > 0) {
        fill.style.width = `${data.answered / data.total * 100}%`
    }

    const row = document.querySelector(`.rating-row[data-student-id="${data.student_id}"]`)
    if (!row) {
        return
    }

    const status = row.querySelector(".rating-status")
    status.textContent = "✓ Готово"
    status.classList.add("done")

    if (data.total_points !== undefined) {
        row.querySelector(".rating-points").textContent = data.total_points
        row.querySelector(".rating-accuracy").textContent = `${data.accuracy}%`
    }
}

function buildAnswerCard(answer, index) {
    const card = document.createElement("div")
    card.classList.add("answer")
    card.dataset.answerId = answer.id

    const head = document.createElement("div")
    head.classList.add("answer-head")

    const letter = document.createElement("span")
    letter.classList.add("answer-letter")
    letter.textContent = LETTERS[index]
    head.appendChild(letter)

    if (answer.is_correct !== undefined) {
        card.dataset.correct = String(answer.is_correct)

        const status = document.createElement("span")
        status.classList.add("answer-status")
        if (answer.is_correct) {
            status.textContent = "✓ Правильно"
        } else {
            status.textContent = "× Неправильно"
        }
        head.appendChild(status)
    }

    const text = document.createElement("p")
    text.classList.add("answer-text")
    text.textContent = answer.text

    card.appendChild(head)
    card.appendChild(text)

    return card
}

function renderQuestion(data) {
    document.querySelector(".info-title").textContent = `Запитання ${data.number} / ${data.total}`
    document.querySelector(".main-info-text").textContent = data.text

    const answersBlock = document.querySelector(".answers")
    answersBlock.innerHTML = ""
    answersBlock.classList.remove("locked")

    data.answers.forEach((answer, index) => {
        answersBlock.appendChild(buildAnswerCard(answer, index))
    })

    document.querySelector(".answered-count").textContent = `0 / ${data.participants_total}`
    document.querySelector(".progress-fill").style.width = "0%"

    document.querySelectorAll(".rating-status").forEach((status) => {
        status.textContent = status.dataset.defaultText
        status.classList.remove("done")
    })

    document.dispatchEvent(new CustomEvent("question:changed", { detail: data }))
}

roomSocket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data)

    if (data.action == "answered") {
        markAnswered(data)
    }

    if (data.action == "next_question") {
        renderQuestion(data)
    }

    if (data.action == "finished") {
        window.location.href = finishUrl
    }
})