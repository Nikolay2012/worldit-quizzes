const finishBox = document.querySelector(".lobby.finish")
const finishPageTitle = document.querySelector(".finish-page-title")
const finishStudents = document.querySelector(".my-result")
const finishSummary = document.querySelector(".my-summary")
const quizTitle = finishPageTitle.textContent

const resultUrl = finishBox.dataset.resultUrl

const myCourse = document.querySelector(".my-course")
const myPoints = document.querySelector(".my-points")
const myAccuracy = document.querySelector(".my-accuracy")
const myTime = document.querySelector(".my-time")
const myBadgeCorrect = document.querySelector(".my-badge-correct")
const myBadgeWrong = document.querySelector(".my-badge-wrong")
const myBadgeNone = document.querySelector(".my-badge-none")
const myRows = document.querySelector(".my-rows")
const myChartPercent = document.querySelector(".my-chart-percent")
const myChartTotal = document.querySelector(".my-chart-total")
const myChartCanvas = document.querySelector(".my-chart-canvas")
const myTotalCorrect = document.querySelector(".my-total-correct")
const myTotalWrong = document.querySelector(".my-total-wrong")
const myTotalNone = document.querySelector(".my-total-none")

const MY_RESULT_TEXTS = {
    correct: "Правильно",
    wrong: "Неправильно",
    none: "Пропущено",
}

const MY_LINE_COLOR = "#F78030"

let myChart = null


function formatMyTime(seconds) {
    if (seconds === null) {
        return "—"
    }

    return `${seconds} с`
}


function buildMyRow(row) {
    const line = document.createElement("div")
    line.classList.add("my-row")

    const number = document.createElement("span")
    number.classList.add("my-col-number")
    number.textContent = row.number

    const question = document.createElement("span")
    question.classList.add("my-col-question")
    question.textContent = row.question
    question.title = row.question

    const answer = document.createElement("span")
    answer.classList.add("my-col-answer")

    if (row.answer) {
        answer.textContent = row.answer
        answer.title = row.answer
    } else {
        answer.textContent = "Відповідь не надана"
    }

    const result = document.createElement("span")
    result.classList.add("my-col-result", row.status)
    result.textContent = MY_RESULT_TEXTS[row.status]

    line.appendChild(number)
    line.appendChild(question)
    line.appendChild(answer)
    line.appendChild(result)

    return line
}


function fillMyResult(data) {
    if (data.course_name) {
        myCourse.textContent = data.course_name
        myCourse.classList.remove("finish-hidden")
    }

    const points = data.points.toLocaleString("uk-UA")
    const maxPoints = data.max_points.toLocaleString("uk-UA")
    myPoints.textContent = `${points} / ${maxPoints}`

    myAccuracy.textContent = `${data.accuracy}%`
    myTime.textContent = formatMyTime(data.average_time)

    myBadgeCorrect.textContent = `✓ ${data.correct}`
    myBadgeWrong.textContent = `× ${data.wrong}`
    myBadgeNone.textContent = `-${data.no_answer}`

    myRows.innerHTML = ""

    data.rows.forEach((row) => {
        myRows.appendChild(buildMyRow(row))
    })

    myChartPercent.textContent = `${data.accuracy}%`
    myChartTotal.textContent = `${data.correct} із ${data.rows.length} відповідей — правильні`

    myTotalCorrect.textContent = data.correct
    myTotalWrong.textContent = data.wrong
    myTotalNone.textContent = data.no_answer
}


function getMyColor(name) {
    return getComputedStyle(document.body).getPropertyValue(name).trim()
}


function updateMyTheme() {
    if (myChart === null) {
        return
    }

    const gridColor = getMyColor("--quiz-my-grid")
    const tickColor = getMyColor("--quiz-my-tick")

    myChart.options.scales.y.ticks.color = tickColor
    myChart.options.scales.y.grid.color = gridColor
    myChart.options.scales.y.border.color = gridColor
    myChart.options.scales.x.ticks.color = tickColor
    myChart.options.scales.x.border.color = gridColor
    myChart.update()
}


function drawMyChart(data) {
    const labels = []

    data.accuracy_by_question.forEach((value, index) => {
        labels.push(index + 1)
    })

    const gridColor = getMyColor("--quiz-my-grid")
    const tickColor = getMyColor("--quiz-my-tick")

    myChart = new Chart(myChartCanvas, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                data: data.accuracy_by_question,
                borderColor: MY_LINE_COLOR,
                borderWidth: 2,
                pointRadius: 2.5,
                pointBackgroundColor: MY_LINE_COLOR,
                pointBorderWidth: 0,
                tension: 0,
                fill: false,
                clip: false,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: { top: 4, right: 6 } },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    ticks: {
                        stepSize: 20,
                        color: tickColor,
                        font: { size: 10 },
                    },
                    grid: { color: gridColor, lineWidth: 0.6, drawTicks: false },
                    border: { display: true, color: gridColor, width: 1 },
                },
                x: {
                    ticks: { color: tickColor, font: { size: 10 }, maxRotation: 0 },
                    grid: { display: false },
                    border: { display: true, color: gridColor, width: 1 },
                },
            },
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false },
            },
        },
    })
}


async function loadMyResult() {
    const response = await fetch(resultUrl)

    if (!response.ok) {
        return
    }

    const data = await response.json()

    fillMyResult(data)
    drawMyChart(data)
}


Chart.defaults.font.family = "Inter"

loadMyResult()


const myThemeObserver = new MutationObserver(updateMyTheme)
myThemeObserver.observe(document.body, { attributes: true, attributeFilter: ["class"] })