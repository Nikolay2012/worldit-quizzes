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
    const lineColor = getMyColor("--quiz-correct-accent")
    const fillColor = getMyColor("--quiz-correct-bg")
    const pointBorder = getMyColor("--quiz-card")

    myChart.options.scales.y.ticks.color = tickColor
    myChart.options.scales.y.grid.color = gridColor
    myChart.options.scales.x.ticks.color = tickColor

    myChart.data.datasets[0].borderColor = lineColor
    myChart.data.datasets[0].pointBackgroundColor = lineColor
    myChart.data.datasets[0].pointBorderColor = pointBorder
    myChart.data.datasets[0].backgroundColor = fillColor

    myChart.update()
}


function drawMyLabels(chart) {
    const ctx = chart.ctx
    const values = chart.data.datasets[0].data
    const points = chart.getDatasetMeta(0).data

    ctx.font = "700 11px Inter"
    ctx.fillStyle = chart.data.datasets[0].borderColor
    ctx.textAlign = "center"
    ctx.textBaseline = "bottom"

    points.forEach((point, index) => {
        ctx.fillText(`${values[index]}%`, point.x, point.y - 12)
    })
}


function drawMyChart(data) {
    const labels = []

    data.accuracy_by_question.forEach((value, index) => {
        labels.push(index + 1)
    })

    const gridColor = getMyColor("--quiz-my-grid")
    const tickColor = getMyColor("--quiz-my-tick")
    const lineColor = getMyColor("--quiz-correct-accent")
    const fillColor = getMyColor("--quiz-correct-bg")
    const pointBorder = getMyColor("--quiz-card")

    myChart = new Chart(myChartCanvas, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                data: data.accuracy_by_question,
                borderColor: lineColor,
                borderWidth: 2,
                fill: true,
                backgroundColor: fillColor,
                pointRadius: 5,
                pointBackgroundColor: lineColor,
                pointBorderColor: pointBorder,
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
                        color: tickColor,
                        font: { size: 10 },
                        padding: 8,
                        callback: (value) => `${value}%`,
                    },
                    grid: { color: gridColor, lineWidth: 1, drawTicks: false },
                    border: { display: false },
                },
                x: {
                    ticks: { color: tickColor, font: { size: 11 } },
                    grid: { display: false },
                    border: { display: false },
                },
            },
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false },
            },
        },
        plugins: [{ afterDatasetsDraw: drawMyLabels }],
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