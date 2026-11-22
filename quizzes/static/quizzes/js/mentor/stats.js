const statsCard = document.querySelector(".stats-card")
const statsQuestionCard = document.querySelector(".question-card")
const statsPanel = document.querySelector(".mentor-panel")
const statsPageTitle = document.querySelector(".page-title h2")

const quizTitle = statsPageTitle.textContent

const statsUrl = statsCard.dataset.statsUrl
const statsLink = document.querySelector(".stats-link")
const statsBackButton = statsCard.querySelector(".stats-back-btn")

const statsBadge = statsCard.querySelector(".stats-badge")
const donutCanvas = statsCard.querySelector(".stats-donut-canvas")
const donutTotal = statsCard.querySelector(".stats-donut-total")
const correctCount = statsCard.querySelector(".stats-correct-count")
const wrongCount = statsCard.querySelector(".stats-wrong-count")
const noneCount = statsCard.querySelector(".stats-none-count")
const choicesSub = statsCard.querySelector(".stats-choices-sub")
const barsBox = statsCard.querySelector(".stats-bars")
const barsCanvas = statsCard.querySelector(".stats-bars-canvas")
const choiceLegend = statsCard.querySelector(".stats-choice-legend")
const textAnswersBox = statsCard.querySelector(".stats-text-answers")
const accuracySub = statsCard.querySelector(".stats-accuracy-sub")
const lineCanvas = statsCard.querySelector(".stats-line-canvas")
const lineCurrent = statsCard.querySelector(".stats-line-current")
const lineLeft = statsCard.querySelector(".stats-line-left")

const COLOR_GREEN = "#00865F"
const COLOR_RED = "#DC3545"
const COLOR_GRAY = "#D1D1DB"
const COLOR_BAR_CORRECT = "#00BC7D"
const COLOR_BAR_WRONG = "#E8A0A9"
const COLOR_META = "#83859F"
const COLOR_GRID = "#E2E1EC"
const COLOR_AREA = "#ECFDF5"

const TEXT_ANSWER_SKIPPED = "Пропустив"

const STATUS_TEXT = {
    correct: "Правильно",
    wrong: "Неправильно",
    none: "Без відповіді",
}

let donutChart = null
let barsChart = null
let lineChart = null

let statsState = "none"


Chart.defaults.font.family = "Inter"


const valueLabelsPlugin = {
    id: "valueLabels",

    afterDatasetsDraw(chart, args, options) {
        const context = chart.ctx
        const values = chart.data.datasets[0].data
        const elements = chart.getDatasetMeta(0).data

        context.save()
        context.font = options.font
        context.fillStyle = options.color
        context.textAlign = "center"
        context.textBaseline = "bottom"

        elements.forEach((element, index) => {
            const value = values[index]

            if (value === null) {
                return
            }

            context.fillText(`${value}${options.suffix}`, element.x, element.y - options.offset)
        })

        context.restore()
    },
}


function getStatsColor(name) {
    return getComputedStyle(document.body).getPropertyValue(name).trim()
}


function updateStatsTheme() {
    if (donutChart !== null) {
        donutChart.data.datasets[0].borderColor = getStatsColor("--quiz-inner")
        donutChart.update()
    }

    if (barsChart !== null) {
        barsChart.options.plugins.valueLabels.color = getStatsColor("--quiz-text")
        barsChart.update()
    }
}


function fillTexts(stats) {
    statsBadge.textContent = `${stats.question_text} · Запитання ${stats.number} із ${stats.questions_total}`

    donutTotal.textContent = stats.total
    correctCount.textContent = stats.correct
    wrongCount.textContent = stats.wrong
    noneCount.textContent = stats.no_answer

    accuracySub.textContent = `Частка правильних відповідей серед ${stats.total} учасників`

    const currentPercent = stats.accuracy_by_question[stats.accuracy_by_question.length - 1]
    lineCurrent.textContent = `Поточне запитання: ${stats.correct} правильні відповіді з ${stats.total} — ${currentPercent}%`

    const nextNumber = stats.number + 1

    if (nextNumber > stats.questions_total) {
        lineLeft.textContent = ""
    } else if (nextNumber === stats.questions_total) {
        lineLeft.textContent = `Запитання ${nextNumber} ще не проведене`
    } else {
        lineLeft.textContent = `Запитання ${nextNumber}–${stats.questions_total} ще не проведені`
    }
}


function drawDonut(stats) {
    if (donutChart) {
        donutChart.destroy()
    }

    const values = [stats.wrong, stats.no_answer, stats.correct]

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

    donutChart = new Chart(donutCanvas, {
        type: "doughnut",
        data: {
            datasets: [{
                data: values,
                backgroundColor: [COLOR_RED, COLOR_GRAY, COLOR_GREEN],
                borderColor: getStatsColor("--quiz-inner"),
                borderWidth: gapWidth,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "67%",
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false },
            },
        },
    })
}


function buildTextAnswer(item) {
    const block = document.createElement("div")
    block.classList.add("stats-text-answer", item.status)

    const name = document.createElement("p")
    name.classList.add("stats-text-name")
    name.textContent = item.name

    const answer = document.createElement("p")
    answer.classList.add("stats-text-value")

    if (item.status === "none") {
        answer.textContent = TEXT_ANSWER_SKIPPED
    } else {
        answer.textContent = item.text
    }

    block.appendChild(name)
    block.appendChild(answer)

    return block
}


function drawChoices(stats) {
    if (barsChart) {
        barsChart.destroy()
        barsChart = null
    }

    barsBox.classList.toggle("hidden", stats.is_text)
    choiceLegend.classList.toggle("hidden", stats.is_text)
    textAnswersBox.classList.toggle("hidden", !stats.is_text)

    if (stats.is_text) {
        choicesSub.textContent = "Відповіді учнів"
        textAnswersBox.innerHTML = ""

        if (stats.text_answers.length === 0) {
            const empty = document.createElement("p")
            empty.classList.add("stats-text-empty")
            empty.textContent = "Ще немає відповідей"
            textAnswersBox.appendChild(empty)
        }

        stats.text_answers.forEach((item) => {
            textAnswersBox.appendChild(buildTextAnswer(item))
        })

        return
    }

    choicesSub.textContent = "Кількість відповідей"

    const labels = []
    const counts = []
    const colors = []

    choiceLegend.innerHTML = ""

    stats.choices.forEach((choice) => {
        labels.push(choice.letter)
        counts.push(choice.count)

        if (choice.is_correct) {
            colors.push(COLOR_BAR_CORRECT)
        } else {
            colors.push(COLOR_BAR_WRONG)
        }

        const legendRow = document.createElement("p")
        legendRow.textContent = `${choice.letter} — ${choice.text}`
        choiceLegend.appendChild(legendRow)
    })

    barsChart = new Chart(barsCanvas, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: colors,
                maxBarThickness: 45,
                borderRadius: 4,
                borderSkipped: false,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: { top: 18 } },
            scales: {
                y: {
                    min: 0,
                    max: Math.max(stats.total, 1),
                    ticks: { stepSize: 1, color: COLOR_META, font: { size: 11 } },
                    grid: { color: COLOR_GRID, lineWidth: 1 },
                    border: { display: false },
                },
                x: {
                    ticks: { color: COLOR_META, font: { size: 12 } },
                    grid: { display: false },
                    border: { display: false },
                },
            },
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false },
                valueLabels: { font: "700 12px Inter", color: getStatsColor("--quiz-text"), offset: 4, suffix: "" },
            },
        },
        plugins: [valueLabelsPlugin],
    })
}

function checkLastQuestion(stats){
    if (stats.is_last === true){
        const finishBtn = document.querySelector(".finish-btn")
        const nextQuestion = document.querySelector(".next-btn")

        if (finishBtn && nextQuestion){
            finishBtn.classList.add("hover")
            nextQuestion.textContent = finishBtn.textContent
        }
    }
}

function drawLine(stats) {
    if (lineChart) {
        lineChart.destroy()
    }

    const labels = []
    const values = []

    for (let index = 0; index < stats.questions_total; index++) {
        labels.push(index + 1)

        if (index < stats.accuracy_by_question.length) {
            values.push(stats.accuracy_by_question[index])
        } else {
            values.push(null)
        }
    }

    lineChart = new Chart(lineCanvas, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                data: values,
                borderColor: COLOR_GREEN,
                borderWidth: 2,
                fill: true,
                backgroundColor: COLOR_AREA,
                pointRadius: 5,
                pointBackgroundColor: COLOR_GREEN,
                pointBorderColor: "#FFFFFF",
                pointBorderWidth: 2,
                tension: 0,
                clip: false,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: { top: 28, right: 10 } },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    ticks: {
                        stepSize: 25,
                        color: COLOR_META,
                        font: { size: 10 },
                        padding: 8,
                        callback: (value) => `${value}%`,
                    },
                    grid: { color: COLOR_GRID, lineWidth: 1, drawTicks: false },
                    border: { display: false },
                },
                x: {
                    ticks: { color: COLOR_META, font: { size: 11 } },
                    grid: { display: false },
                    border: { display: false },
                },
            },
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false },
                valueLabels: { font: "700 11px Inter", color: COLOR_GREEN, offset: 16, suffix: "%" },
            },
        },
        plugins: [valueLabelsPlugin],
    })
}


function paintRating(students) {
    students.forEach((student) => {
        const row = document.querySelector(`.rating-row[data-student-id="${student.student_id}"]`)

        if (!row) {
            return
        }

        const status = row.querySelector(".rating-status")
        status.classList.remove("done", "correct", "wrong", "none")
        status.classList.add(student.status)
        status.textContent = STATUS_TEXT[student.status]
    })
}


async function loadStats() {
    const response = await fetch(statsUrl)

    if (!response.ok) {
        return null
    }

    const stats = await response.json()

    checkLastQuestion(stats)
    fillTexts(stats)
    drawDonut(stats)
    drawChoices(stats)
    drawLine(stats)

    return stats
}

function openStatsCard() {
    statsQuestionCard.classList.add("hidden")
    statsCard.classList.remove("hidden")
}

function closeStatsCard() {
    statsCard.classList.add("hidden")
    statsCard.classList.remove("preview")
    statsQuestionCard.classList.remove("hidden")
}

async function showPreview() {
    if (statsState !== "none") {
        return
    }

    statsState = "preview"
    statsCard.classList.add("preview")
    openStatsCard()

    const stats = await loadStats()

    if (stats === null) {
        hidePreview()
    }
}

function hidePreview() {
    if (statsState !== "preview") {
        return
    }

    statsState = "none"
    closeStatsCard()
}

async function showStats() {
    if (statsState === "final") {
        return
    }

    statsState = "final"
    statsCard.classList.remove("preview")
    openStatsCard()
    statsPanel.classList.add("stats-mode")
    statsPageTitle.textContent = "Статистика запитання"

    const stats = await loadStats()

    if (stats === null) {
        hideStats()
        return
    }

    paintRating(stats.students)
}

function hideStats() {
    statsState = "none"

    closeStatsCard()
    statsPanel.classList.remove("stats-mode")
    statsPageTitle.textContent = quizTitle

    document.querySelectorAll(".rating-status").forEach((status) => {
        status.classList.remove("correct", "wrong", "none")
    })
}


statsLink.addEventListener("click", (event) => {
    event.preventDefault()
    showPreview()
})

statsBackButton.addEventListener("click", () => {
    hidePreview()
})

roomSocket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data)

    if (data.action !== "answered") {
        return
    }

    if (data.total > 0 && data.answered >= data.total) {
        showStats()
        return
    }

    if (statsState === "preview") {
        loadStats()
    }
})

document.addEventListener("question:timeup", () => {
    showStats()
})

document.addEventListener("question:changed", () => {
    hideStats()
})

if (statsCard.dataset.finished === "true") {
    showStats()
}

const statsThemeObserver = new MutationObserver(updateStatsTheme)
statsThemeObserver.observe(document.body, { attributes: true, attributeFilter: ["class"] })