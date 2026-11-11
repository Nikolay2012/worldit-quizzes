const answersBlock = document.querySelector(".answers")
const sendAnswersButton = document.querySelector(".send-answers-btn")
const answerCorrectModal = document.getElementById("answerCorrectModal")
const answerWrongModal = document.getElementById("answerWrongModal")
const timeUpModal = document.getElementById("timeUpModal")
const modalCoverElement = document.getElementById("modalCover")
const modals = [answerCorrectModal, answerWrongModal]

const CARD_ANIMATION_TIME = 800

let isAnswered = false
let chosenAt = 0
let modalTimer = null

if (answersBlock && answersBlock.classList.contains("locked")) {
    isAnswered = true
}

function formatPoints(modal) {
    const pointsValue = modal.querySelector(".points-value")
    pointsValue.textContent = Number(pointsValue.textContent).toLocaleString("uk-UA")
}

function hasAnswered() {
    return isAnswered || isTextAnswered
}

function isManyQuestion() {
    return answersBlock.classList.contains("many")
}

function updateSendButton() {
    const chosenCount = answersBlock.querySelectorAll(".answer.chosen").length
    sendAnswersButton.disabled = chosenCount === 0 || isAnswered
}

if (answersBlock) {
    answersBlock.addEventListener("click", (event) => {
        const card = event.target.closest(".answer")

        if (!card || isAnswered) {
            return
        }

        if (answersBlock.classList.contains("locked")) {
            return
        }

        if (isManyQuestion()) {
            card.classList.toggle("chosen")
            updateSendButton()
            return
        }

        isAnswered = true
        chosenAt = Date.now()

        card.classList.add("chosen")
        answersBlock.classList.add("locked")

        roomSocket.send(JSON.stringify({
            action: "answer",
            answer_id: card.dataset.answerId,
        }))
    })
}

sendAnswersButton.addEventListener("click", () => {
    const chosenCards = answersBlock.querySelectorAll(".answer.chosen")

    if (chosenCards.length === 0 || isAnswered) {
        return
    }

    const answerIds = []
    chosenCards.forEach((card) => {
        answerIds.push(card.dataset.answerId)
    })

    isAnswered = true
    chosenAt = Date.now()

    answersBlock.classList.add("locked")
    sendAnswersButton.disabled = true

    roomSocket.send(JSON.stringify({
        action: "answer",
        answer_ids: answerIds,
    }))
})

roomSocket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data)

    if (data.action != "answer_result") {
        return
    }

    let modal
    if (data.is_correct) {
        modal = answerCorrectModal
    } else {
        modal = answerWrongModal
    }

    modal.querySelector(".points-value").textContent = data.points
    formatPoints(modal)
    modal.querySelector(".correct-text").textContent = data.correct_text

    const passed = Date.now() - chosenAt
    const wait = Math.max(0, CARD_ANIMATION_TIME - passed)

    modalTimer = setTimeout(() => {
        openModal(modal)
    }, wait)
})

roomSocket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data)

    if (data.action != "time_changed") {
        return
    }

    if (data.paused || data.time_left <= 0) {
        return
    }

    if (timeUpModal.style.display === "flex") {
        closeModal()
    }
})

document.addEventListener("question:timeup", () => {
    if (hasAnswered()) {
        return
    }

    answersBlock.querySelectorAll(".answer.chosen").forEach((card) => {
        card.classList.remove("chosen")
    })
    updateSendButton()

    openModal(timeUpModal)
})

document.addEventListener("question:changed", (event) => {
    const data = event.detail

    isAnswered = false
    chosenAt = 0

    sendAnswersButton.classList.toggle("hidden", !data.is_many)
    updateSendButton()

    clearTimeout(modalTimer)
    if (modalCoverElement.style.display === "flex") {
        closeModal()
    }

    document.querySelectorAll(".progress-step").forEach((step, index) => {
        step.classList.toggle("done", index < data.number)
    })
})


modals.forEach((modal) => {
    if (modal.dataset.openOnLoad === "true") {
        formatPoints(modal)
        openModal(modal)
    }
})

if (timeUpModal.dataset.openOnLoad === "true") {
    openModal(timeUpModal)
}