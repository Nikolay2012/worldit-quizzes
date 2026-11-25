const mentorTextBox = document.querySelector(".mentor-text-answer")
const mentorTextTitle = mentorTextBox.querySelector(".mentor-text-answer-title")
const mentorTextButton = mentorTextBox.querySelector(".mentor-text-answer-button")
const mentorChoiceAnswers = document.querySelector(".answers")
const mentorQuestionHint = document.querySelector(".info-meta")

let isMentorAnswerShown = false


function getCorrectText(answers) {
    const texts = []

    answers.forEach((answer) => {
        if (answer.is_correct) {
            texts.push(answer.text)
        }
    })

    return texts.join(", ")
}


function hideCorrectAnswer() {
    isMentorAnswerShown = false
    mentorTextTitle.textContent = mentorTextBox.dataset.hiddenText
    mentorTextButton.textContent = "Показати відповідь"
}


function showCorrectAnswer() {
    isMentorAnswerShown = true
    mentorTextTitle.textContent = mentorTextTitle.dataset.correct
    mentorTextButton.textContent = "Сховати відповідь"
}

function showMentorQuestionType(isText, typeText) {
    mentorChoiceAnswers.classList.toggle("hidden", isText)
    mentorTextBox.classList.toggle("hidden", !isText)

    if (isText) {
        mentorQuestionHint.textContent = mentorTextBox.dataset.textHint
    } else {
        mentorQuestionHint.textContent = typeText
    }
}


mentorTextButton.addEventListener("click", () => {
    answersShown = !answersShown
    paintAnswers()
})

document.addEventListener("question:changed", (event) => {
    const data = event.detail

    mentorTextTitle.dataset.correct = getCorrectText(data.answers)
    hideCorrectAnswer()

    showMentorQuestionType(data.is_text, data.type)
})