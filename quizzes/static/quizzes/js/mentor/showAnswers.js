const showAnswersBtn = document.querySelector(".show-answers-btn")
const showAnswersText = document.querySelector(".show-answers-text")
const answerCards = document.querySelectorAll(".answer")

let answersShown = false

showAnswersBtn.addEventListener("click", () => {
    answersShown = !answersShown

    answerCards.forEach((card) => {
        const isCorrect = card.dataset.correct === "true"

        card.classList.toggle("correct", answersShown && isCorrect)
        card.classList.toggle("wrong", answersShown && !isCorrect)
    })

    if (answersShown) {
        showAnswersText.textContent = "Сховати відповіді"
    } else {
        showAnswersText.textContent = "Переглянути відповіді"
    }
})