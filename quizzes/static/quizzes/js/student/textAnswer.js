const textAnswerBox = document.querySelector(".text-answer")
const textAnswerForm = textAnswerBox.querySelector(".text-answer-form")
const textAnswerInput = textAnswerBox.querySelector(".text-answer-input")
const textAnswerButton = textAnswerBox.querySelector(".text-answer-button")
const choiceAnswersBlock = document.querySelector(".answers")
const questionHint = document.querySelector(".info-meta")

let isTextAnswered = textAnswerBox.dataset.answered === "true"


function lockTextAnswer() {
    textAnswerInput.disabled = true
    textAnswerButton.disabled = true
}


function unlockTextAnswer() {
    if (isTextAnswered) {
        return
    }

    textAnswerInput.disabled = false
    textAnswerButton.disabled = false
}


function showQuestionType(isText, isMany) {
    choiceAnswersBlock.classList.toggle("hidden", isText)
    textAnswerBox.classList.toggle("hidden", !isText)

    if (isText) {
        questionHint.textContent = textAnswerBox.dataset.textHint
    } else if (isMany) {
        questionHint.textContent = textAnswerBox.dataset.manyHint
    } else {
        questionHint.textContent = textAnswerBox.dataset.choiceHint
    }
}


textAnswerForm.addEventListener("submit", (event) => {
    event.preventDefault()

    const text = textAnswerInput.value.trim()

    if (!text || isTextAnswered) {
        return
    }

    isTextAnswered = true
    lockTextAnswer()

    roomSocket.send(JSON.stringify({
        action: "answer",
        text: text,
    }))
})

document.addEventListener("question:changed", (event) => {
    isTextAnswered = false
    textAnswerInput.value = ""

    showQuestionType(event.detail.is_text, event.detail.is_many)
    unlockTextAnswer()
})

document.addEventListener("question:timeup", () => {
    lockTextAnswer()
})

roomSocket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data)

    if (data.action === "time_changed" && !data.paused && data.time_left > 0) {
        unlockTextAnswer()
    }
})