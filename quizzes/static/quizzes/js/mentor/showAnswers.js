const showAnswersBtn = document.querySelector(".show-answers-btn")
const showAnswersText = document.querySelector(".show-answers-text")

let answersShown = false

function paintAnswers() {
    document.querySelectorAll(".answer").forEach((card) => {
        const isCorrect = card.dataset.correct === "true"
        card.classList.toggle("correct", answersShown && isCorrect)
        card.classList.toggle("wrong", answersShown && !isCorrect)
    })

    if (answersShown) {
        showAnswersText.textContent = "Сховати відповіді"
        showCorrectAnswer()
    } else {
        showAnswersText.textContent = "Переглянути відповіді"
        hideCorrectAnswer()
    }
}

showAnswersBtn.addEventListener("click", () => {
    answersShown = !answersShown
    paintAnswers()
})

document.addEventListener("question:changed", () => {
    answersShown = false
    paintAnswers()
})