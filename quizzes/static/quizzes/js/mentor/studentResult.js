const studentUrl = finishBox.dataset.studentUrl

const finishPageTitle = document.querySelector(".finish-page-title")
const finishActions = document.querySelector(".finish-actions")
const studentTitleBadge = document.querySelector(".student-title-badge")
const finishStudents = document.querySelector(".finish-students")
const finishSummary = document.querySelector(".finish-summary")
const studentResult = document.querySelector(".student-result")

const studentBack = document.querySelector(".student-back")
const studentCourse = document.querySelector(".student-course")
const studentName = document.querySelector(".student-name")
const studentPoints = document.querySelector(".student-points")
const studentAccuracy = document.querySelector(".student-accuracy")
const studentTime = document.querySelector(".student-time")
const studentBadgeCorrect = document.querySelector(".student-badge-correct")
const studentBadgeWrong = document.querySelector(".student-badge-wrong")
const studentBadgeNone = document.querySelector(".student-badge-none")
const studentRows = document.querySelector(".student-rows")

const studentSummary = document.querySelector(".student-summary")
const studentChartTotal = document.querySelector(".student-chart-total")
const studentChartCanvas = document.querySelector(".student-chart-canvas")
const studentTotalCorrect = document.querySelector(".student-total-correct")
const studentTotalWrong = document.querySelector(".student-total-wrong")
const studentTotalNone = document.querySelector(".student-total-none")

let studentChart = null

const quizTitle = finishPageTitle.textContent

const STUDENT_TITLE = "Результат учня"

const RESULT_TEXTS = {
    correct: "Правильно",
    wrong: "Неправильно",
    none: "Без відповіді",
}


function showStudentView() {
    finishPageTitle.textContent = STUDENT_TITLE

    finishActions.classList.add("finish-hidden")
    finishStudents.classList.add("finish-hidden")
    finishSummary.classList.add("finish-hidden")

    studentTitleBadge.classList.remove("finish-hidden")
    studentResult.classList.remove("finish-hidden")
    studentSummary.classList.remove("finish-hidden")

    finishBox.classList.add("student-mode")
}


function showFinishView() {
    finishPageTitle.textContent = quizTitle

    finishActions.classList.remove("finish-hidden")
    finishStudents.classList.remove("finish-hidden")
    finishSummary.classList.remove("finish-hidden")

    studentTitleBadge.classList.add("finish-hidden")
    studentResult.classList.add("finish-hidden")
    studentSummary.classList.add("finish-hidden")

    finishBox.classList.remove("student-mode")

    finishSelect.value = ""
}


function formatTime(seconds) {
    if (seconds === null) {
        return "—"
    }

    return `${seconds} с`
}


function buildStudentRow(row) {
    const line = document.createElement("div")
    line.classList.add("student-row")

    const number = document.createElement("span")
    number.classList.add("student-col-number")
    number.textContent = row.number

    const question = document.createElement("span")
    question.classList.add("student-col-question")
    question.textContent = row.question
    question.title = row.question

    const answer = document.createElement("span")
    answer.classList.add("student-col-answer")

    if (row.answer) {
        answer.textContent = row.answer
        answer.title = row.answer
    } else {
        answer.textContent = "—"
    }

    const result = document.createElement("span")
    result.classList.add("student-col-result", row.status)
    result.textContent = RESULT_TEXTS[row.status]

    line.appendChild(number)
    line.appendChild(question)
    line.appendChild(answer)
    line.appendChild(result)

    return line
}


function fillStudentResult(data) {
    if (data.course_name) {
        studentCourse.textContent = data.course_name
        studentCourse.classList.remove("finish-hidden")
    } else {
        studentCourse.classList.add("finish-hidden")
    }

    studentName.textContent = data.name

    const points = data.points.toLocaleString("uk-UA")
    const maxPoints = data.max_points.toLocaleString("uk-UA")
    studentPoints.textContent = `${points} / ${maxPoints}`

    studentAccuracy.textContent = `${data.accuracy}%`
    studentTime.textContent = formatTime(data.average_time)

    studentBadgeCorrect.textContent = `✓ ${data.correct}`
    studentBadgeWrong.textContent = `× ${data.wrong}`
    studentBadgeNone.textContent = `-${data.no_answer}`

    studentRows.innerHTML = ""

    data.rows.forEach((row) => {
        studentRows.appendChild(buildStudentRow(row))
    })

    studentRows.scrollTop = 0

    studentChartTotal.textContent = `${data.correct} із ${data.rows.length} відповідей — правильні`

    studentTotalCorrect.textContent = data.correct
    studentTotalWrong.textContent = data.wrong
    studentTotalNone.textContent = data.no_answer
}


function getStudentColor(name) {
    return getComputedStyle(document.body).getPropertyValue(name).trim()
}


function updateStudentTheme() {
    if (studentChart === null) {
        return
    }

    const gridColor = getStudentColor("--quiz-my-grid")
    const tickColor = getStudentColor("--quiz-my-tick")
    const lineColor = getStudentColor("--quiz-correct-accent")
    const fillColor = getStudentColor("--quiz-correct-bg")
    const pointBorder = getStudentColor("--quiz-card")

    studentChart.options.scales.y.ticks.color = tickColor
    studentChart.options.scales.y.grid.color = gridColor
    studentChart.options.scales.x.ticks.color = tickColor

    studentChart.data.datasets[0].borderColor = lineColor
    studentChart.data.datasets[0].pointBackgroundColor = lineColor
    studentChart.data.datasets[0].pointBorderColor = pointBorder
    studentChart.data.datasets[0].backgroundColor = fillColor

    studentChart.update()
}


function drawStudentLabels(chart) {
    const ctx = chart.ctx
    const values = chart.data.datasets[0].data
    const points = chart.getDatasetMeta(0).data

    ctx.font = "700 11px Inter"
    ctx.fillStyle = chart.data.datasets[0].borderColor
    ctx.textAlign = "center"
    ctx.textBaseline = "bottom"

    points.forEach((point, index) => {
        const text = `${values[index]}%`
        const halfWidth = ctx.measureText(text).width / 2

        let labelX = point.x

        if (labelX + halfWidth > chart.width) {
            labelX = chart.width - halfWidth
        }

        if (labelX - halfWidth < 0) {
            labelX = halfWidth
        }

        ctx.fillText(text, labelX, point.y - 16)
    })
}


function drawStudentChart(data) {
    if (studentChart !== null) {
        studentChart.destroy()
    }

    const labels = []

    data.accuracy_by_question.forEach((value, index) => {
        labels.push(index + 1)
    })

    const gridColor = getStudentColor("--quiz-my-grid")
    const tickColor = getStudentColor("--quiz-my-tick")
    const lineColor = getStudentColor("--quiz-correct-accent")
    const fillColor = getStudentColor("--quiz-correct-bg")
    const pointBorder = getStudentColor("--quiz-card")

    studentChart = new Chart(studentChartCanvas, {
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
            layout: { padding: { top: 28, right: 8 } },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    ticks: {
                        stepSize: 25,
                        color: tickColor,
                        font: { size: 10 },
                        padding: 8,
                        crossAlign: "far",
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
        plugins: [{ afterDatasetsDraw: drawStudentLabels }],
    })
}


async function openStudentResult(studentId) {
    const url = studentUrl.replace("/student/0/", `/student/${studentId}/`)
    const response = await fetch(url)

    if (!response.ok) {
        return
    }

    const data = await response.json()

    fillStudentResult(data)
    showStudentView()
    drawStudentChart(data)
}


finishRows.addEventListener("click", (event) => {
    const row = event.target.closest(".finish-row")

    if (row === null) {
        return
    }

    openStudentResult(row.dataset.studentId)
})

finishSelect.addEventListener("change", () => {
    if (finishSelect.value === "") {
        return
    }

    openStudentResult(finishSelect.value)
})

studentBack.addEventListener("click", showFinishView)


const studentThemeObserver = new MutationObserver(updateStudentTheme)
studentThemeObserver.observe(document.body, { attributes: true, attributeFilter: ["class"] })