const answersBlock = document.querySelector(".answers")
const answerCorrectModal = document.getElementById("answerCorrectModal")
const answerWrongModal = document.getElementById("answerWrongModal")
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

if (answersBlock) {
    answersBlock.addEventListener("click", (event) => {
        const card = event.target.closest(".answer")

        if (!card || isAnswered) {
            return
        }

        if (answersBlock.classList.contains("locked")) {
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

document.addEventListener("question:changed", (event) => {
    const data = event.detail

    isAnswered = false
    chosenAt = 0

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