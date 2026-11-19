const questionsUrl = finishBox.dataset.questionsUrl

const questionsOpenBtn = document.querySelector(".finish-controls .finish-questions-btn")
const questionsBackBtn = document.querySelector(".questions-back-btn")
const questionsList = document.querySelector(".questions-list")
const questionsStudentsCount = document.querySelector(".questions-students-count")
const questionsCount = document.querySelector(".questions-count")
const questionsAccuracy = document.querySelector(".questions-accuracy")
const questionsPoints = document.querySelector(".questions-points")
const questionsGrid = document.querySelector(".questions-grid")

const QUESTIONS_TITLE = "Результат тестування"

const QUESTION_GREEN = "#00865F"
const QUESTION_RED = "#DC3545"
const QUESTION_GRAY = "#D1D1DB"
const QUESTION_EMPTY = "#F5F5F8"

const QUESTION_SKIPPED = "Пропустив"

let questionsCharts = []


function getQuestionsColor(name) {
    return getComputedStyle(document.body).getPropertyValue(name).trim()
}


function updateQuestionsTheme() {
    questionsCharts.forEach((chart) => {
        chart.data.datasets[0].borderColor = getQuestionsColor("--quiz-inner")
        chart.update()
    })
}


function showQuestionsView() {
    finishPageTitle.textContent = QUESTIONS_TITLE

    finishStudents.classList.add("finish-hidden")
    finishSummary.classList.add("finish-hidden")
    questionsList.classList.remove("finish-hidden")

    finishBox.classList.add("questions-mode")
}


function hideQuestionsView() {
    finishPageTitle.textContent = quizTitle

    finishStudents.classList.remove("finish-hidden")
    finishSummary.classList.remove("finish-hidden")
    questionsList.classList.add("finish-hidden")

    finishBox.classList.remove("questions-mode")
}


function padNumber(number) {
    if (number < 10) {
        return `0${number}`
    }

    return `${number}`
}


function createElement(tag, className, text) {
    const element = document.createElement(tag)
    element.classList.add(...className.split(" "))

    if (text !== undefined) {
        element.textContent = text
    }

    return element
}


function buildLegendRow(type, label, value) {
    const row = createElement("div", "questions-legend-row")
    const name = createElement("div", "questions-legend-name")

    name.appendChild(createElement("span", `questions-dot ${type}`))
    name.appendChild(createElement("span", "questions-legend-label", label))

    row.appendChild(name)
    row.appendChild(createElement("span", "questions-legend-value", value))

    return row
}


function buildLeft(item) {
    const left = createElement("div", "questions-item-left")

    const donut = createElement("div", "questions-donut")
    const chartBox = createElement("div", "questions-donut-chart")
    const canvas = createElement("canvas", "questions-donut-canvas")
    const center = createElement("div", "questions-donut-center")

    center.appendChild(createElement("span", "questions-donut-percent", `${item.percent}%`))
    center.appendChild(createElement("span", "questions-donut-label", "Вірно"))

    chartBox.appendChild(canvas)
    chartBox.appendChild(center)
    donut.appendChild(chartBox)

    const legend = createElement("div", "questions-legend")
    legend.appendChild(buildLegendRow("correct", "Правильно", item.correct))
    legend.appendChild(buildLegendRow("wrong", "Не правильно", item.wrong))
    legend.appendChild(buildLegendRow("none", "Без відповіді", item.no_answer))

    left.appendChild(donut)
    left.appendChild(legend)

    return { left, canvas }
}


function buildOptions(item, studentsCount) {
    const options = createElement("div", "questions-options")

    item.options.forEach((option) => {
        const block = createElement("div", "questions-option")
        const label = createElement("p", "questions-option-label", option.text)
        label.title = option.text

        const row = createElement("div", "questions-option-row")
        const track = createElement("div", "questions-option-track")

        let fillType = "wrong"
        if (option.is_correct) {
            fillType = "correct"
        }

        const fill = createElement("div", `questions-option-fill ${fillType}`)

        let percent = 0
        if (studentsCount > 0) {
            percent = option.count / studentsCount * 100
        }
        fill.style.width = `${percent}%`

        track.appendChild(fill)
        row.appendChild(track)
        row.appendChild(createElement("span", "questions-option-count", option.count))

        block.appendChild(label)
        block.appendChild(row)
        options.appendChild(block)
    })

    return options
}


function buildTextAnswers(item) {
    const list = createElement("div", "questions-text-answers")

    if (item.text_answers.length === 0) {
        list.appendChild(createElement("p", "questions-text-empty", "Ще немає відповідей"))
        return list
    }

    item.text_answers.forEach((answer) => {
        const block = createElement("div", `questions-text-answer ${answer.status}`)

        if (answer.name) {
            block.appendChild(createElement("p", "questions-text-name", answer.name))
        }

        let text = answer.text
        if (answer.status === "none") {
            text = QUESTION_SKIPPED
        }

        block.appendChild(createElement("p", "questions-text-value", text))
        list.appendChild(block)
    })

    return list
}


function buildCorrect(item) {
    const box = createElement("div", "questions-correct")
    const text = createElement("p", "questions-correct-text", item.correct_text)
    text.title = item.correct_text

    box.appendChild(createElement("p", "questions-correct-label", "Правильна відповідь"))
    box.appendChild(text)

    return box
}


function buildQuestionCard(item, studentsCount) {
    const card = createElement("div", "questions-item")

    const head = createElement("div", "questions-item-head")
    const titleRow = createElement("div", "questions-item-title-row")
    const title = createElement("p", "questions-item-title", item.text)
    title.title = item.text

    titleRow.appendChild(createElement("span", "questions-item-number", padNumber(item.number)))
    titleRow.appendChild(title)

    head.appendChild(titleRow)
    head.appendChild(createElement("p", "questions-item-sub", "Середня точність групи"))

    const body = createElement("div", "questions-item-body")
    const leftPart = buildLeft(item)
    const right = createElement("div", "questions-item-right")

    if (item.is_text) {
        right.appendChild(buildTextAnswers(item))
    } else {
        right.appendChild(buildOptions(item, studentsCount))
    }

    right.appendChild(buildCorrect(item))

    body.appendChild(leftPart.left)
    body.appendChild(right)

    card.appendChild(head)
    card.appendChild(body)

    return { card, canvas: leftPart.canvas }
}


function drawQuestionDonut(canvas, item) {
    let values = [item.wrong, item.no_answer, item.correct]
    let colors = [QUESTION_RED, QUESTION_GRAY, QUESTION_GREEN]

    if (item.correct + item.wrong + item.no_answer === 0) {
        values = [1]
        colors = [QUESTION_EMPTY]
    }

    let filledParts = 0
    values.forEach((value) => {
        if (value > 0) {
            filledParts += 1
        }
    })

    let gapWidth = 0
    if (filledParts > 1) {
        gapWidth = 2
    }

    const chart = new Chart(canvas, {
        type: "doughnut",
        data: {
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: getQuestionsColor("--quiz-inner"),
                borderWidth: gapWidth,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "71%",
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false },
            },
        },
    })

    questionsCharts.push(chart)
}


function fillQuestionsStats(data) {
    questionsStudentsCount.textContent = data.students_count
    questionsCount.textContent = data.questions_count
    questionsAccuracy.textContent = `${data.total_percent}%`

    const pointsSum = data.points_sum.toLocaleString("uk-UA")
    const pointsMax = data.points_max.toLocaleString("uk-UA")
    questionsPoints.textContent = `${pointsSum}/${pointsMax}`
}


function fillQuestionsGrid(data) {
    questionsCharts.forEach((chart) => {
        chart.destroy()
    })
    questionsCharts = []

    questionsGrid.innerHTML = ""

    data.questions.forEach((item) => {
        const built = buildQuestionCard(item, data.students_count)

        questionsGrid.appendChild(built.card)
        drawQuestionDonut(built.canvas, item)
    })

    questionsGrid.scrollTop = 0
}


async function openQuestionsList() {
    const response = await fetch(questionsUrl)

    if (!response.ok) {
        return
    }

    const data = await response.json()

    showQuestionsView()
    fillQuestionsStats(data)
    fillQuestionsGrid(data)
}


questionsOpenBtn.addEventListener("click", openQuestionsList)
questionsBackBtn.addEventListener("click", hideQuestionsView)

const questionsThemeObserver = new MutationObserver(updateQuestionsTheme)
questionsThemeObserver.observe(document.body, { attributes: true, attributeFilter: ["class"] })