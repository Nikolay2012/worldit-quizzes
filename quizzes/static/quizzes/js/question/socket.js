const lobby = document.querySelector(".lobby")
const roomId = lobby.dataset.roomId
const finishUrl = lobby.dataset.finishUrl

const protocol = window.location.protocol === "https:" ? "wss" : "ws"
const roomSocket = new WebSocket(`${protocol}://${window.location.host}/ws/quizzes/room/${roomId}/`)

const LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H"]

const RATING_MOVE_TIME = 500

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
        sortRating(true)
    }
}

function getRowScore(row) {
    const points = parseInt(row.querySelector(".rating-points").textContent) || 0
    const accuracy = parseInt(row.querySelector(".rating-accuracy").textContent) || 0

    return { points: points, accuracy: accuracy }
}

function sortRating(animate) {
    const list = document.querySelector(".rating-list")

    if (!list) {
        return
    }

    const rows = Array.from(list.querySelectorAll(".rating-row"))

    if (rows.length === 0 || !rows[0].querySelector(".rating-points")) {
        return
    }

    const oldTops = new Map()

    rows.forEach((row) => {
        oldTops.set(row, row.getBoundingClientRect().top)
    })

    const sortedRows = [...rows].sort((first, second) => {
        const firstScore = getRowScore(first)
        const secondScore = getRowScore(second)

        if (secondScore.points !== firstScore.points) {
            return secondScore.points - firstScore.points
        }

        return secondScore.accuracy - firstScore.accuracy
    })

    sortedRows.forEach((row, index) => {
        list.appendChild(row)
        row.querySelector(".rating-number").textContent = index + 1
    })

    if (!animate) {
        return
    }

    const movedRows = []

    sortedRows.forEach((row) => {
        const shift = oldTops.get(row) - row.getBoundingClientRect().top

        if (shift === 0) {
            return
        }

        row.style.transition = "none"
        row.style.transform = `translateY(${shift}px)`

        if (shift > 0) {
            row.style.zIndex = "1"
        }

        movedRows.push(row)
    })

    list.getBoundingClientRect()

    movedRows.forEach((row) => {
        row.style.transition = `transform ${RATING_MOVE_TIME}ms ease`
        row.style.transform = ""
    })

    setTimeout(() => {
        movedRows.forEach((row) => {
            row.style.transition = ""
            row.style.zIndex = ""
        })
    }, RATING_MOVE_TIME)
}

function buildAnswerCard(answer, index, isMany) {
    const card = document.createElement("div")
    card.classList.add("answer")
    card.dataset.answerId = answer.id

    if (isMany) {
        const check = document.createElement("span")
        check.classList.add("answer-check")
        card.appendChild(check)
    }

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
    answersBlock.classList.toggle("many", data.is_many)

    data.answers.forEach((answer, index) => {
        answersBlock.appendChild(buildAnswerCard(answer, index, data.is_many))
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

sortRating(false)