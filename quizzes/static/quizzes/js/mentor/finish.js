const finishBox = document.querySelector(".lobby.finish")
const finishUrl = finishBox.dataset.statsUrl
const avatarUrl = finishBox.dataset.avatar

const finishInfo = document.querySelector(".finish-info")
const finishCount = document.querySelector(".finish-count")
const finishSelect = document.querySelector(".finish-select-input")
const finishNumbers = document.querySelector(".finish-numbers")
const finishRows = document.querySelector(".finish-rows")
const finishPercent = document.querySelector(".finish-percent")
const finishDonutCanvas = document.querySelector(".finish-donut-canvas")
const finishDonutTotal = document.querySelector(".finish-donut-total")
const finishGroupsList = document.querySelector(".finish-groups-list")
const finishTotal = document.querySelector(".finish-total")
const finishNote = document.querySelector(".finish-note")

const GROUP_COLORS = ["#00BC7D", "#00865F", "#767B9C", "#FF9B54", "#DC3545"]

const EMPTY_COLOR = "#F5F5F8"

let finishDonutChart = null

const RESULT_MARKS = {
    correct: "✓",
    wrong: "×",
    none: "–",
}


function questionsWord(count) {
    const lastDigit = count % 10
    const lastTwo = count % 100

    if (lastDigit >= 1 && lastDigit <= 4 && (lastTwo < 12 || lastTwo > 14)) {
        return "запитання"
    }

    return "запитань"
}


function fillHead(stats) {
    const questionsText = `${stats.questions_count} ${questionsWord(stats.questions_count)}`

    if (stats.course_name) {
        finishInfo.textContent = `${stats.course_name} · ${questionsText}`
    } else {
        finishInfo.textContent = questionsText
    }

    finishCount.textContent = stats.students_count
}


function fillSelect(students) {
    students.forEach((student) => {
        const option = document.createElement("option")
        option.value = student.student_id
        option.textContent = student.name
        finishSelect.appendChild(option)
    })
}


function buildNumbers(questionsCount) {
    finishNumbers.innerHTML = ""

    for (let number = 1; number <= questionsCount; number++) {
        const cell = document.createElement("span")
        cell.classList.add("finish-cell")
        cell.textContent = number
        finishNumbers.appendChild(cell)
    }
}


function buildRow(student) {
    const row = document.createElement("div")
    row.classList.add("finish-row")
    row.dataset.studentId = student.student_id

    const nameCol = document.createElement("div")
    nameCol.classList.add("finish-name-col")

    const avatar = document.createElement("img")
    avatar.classList.add("finish-avatar")
    avatar.src = avatarUrl
    avatar.alt = ""

    const name = document.createElement("p")
    name.classList.add("finish-name")
    name.textContent = student.name

    nameCol.appendChild(avatar)
    nameCol.appendChild(name)

    const cells = document.createElement("div")
    cells.classList.add("finish-cells")

    student.results.forEach((result) => {
        const cell = document.createElement("span")
        cell.classList.add("finish-cell", result)
        cell.textContent = RESULT_MARKS[result]
        cells.appendChild(cell)
    })

    const points = document.createElement("span")
    points.classList.add("finish-points-col")
    points.textContent = student.points.toLocaleString("uk-UA")

    const accuracy = document.createElement("span")
    accuracy.classList.add("finish-accuracy-col")
    accuracy.textContent = `${student.accuracy}%`

    row.appendChild(nameCol)
    row.appendChild(cells)
    row.appendChild(points)
    row.appendChild(accuracy)

    return row
}


function buildTable(stats) {
    buildNumbers(stats.questions_count)

    finishRows.innerHTML = ""

    stats.students.forEach((student) => {
        finishRows.appendChild(buildRow(student))
    })
}


function getFinishColor(name) {
    return getComputedStyle(document.body).getPropertyValue(name).trim()
}


function updateFinishTheme() {
    if (finishDonutChart === null) {
        return
    }

    finishDonutChart.data.datasets[0].borderColor = getFinishColor("--quiz-card")
    finishDonutChart.update()
}


function drawFinishDonut(stats) {
    let values = []
    let colors = []

    stats.groups.forEach((group, index) => {
        values.push(group.count)
        colors.push(GROUP_COLORS[index])
    })

    if (stats.students_count === 0) {
        values = [1]
        colors = [EMPTY_COLOR]
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

    finishDonutChart = new Chart(finishDonutCanvas, {
        type: "doughnut",
        data: {
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: getFinishColor("--quiz-card"),
                borderWidth: gapWidth,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "70%",
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false },
            },
        },
    })

    finishDonutTotal.textContent = stats.students_count
}


function buildGroups(stats) {
    finishGroupsList.innerHTML = ""

    stats.groups.forEach((group, index) => {
        const row = document.createElement("div")
        row.classList.add("finish-group")

        const label = document.createElement("span")
        label.classList.add("finish-group-label")
        label.textContent = group.label

        const track = document.createElement("div")
        track.classList.add("finish-group-track")

        const fill = document.createElement("div")
        fill.classList.add("finish-group-fill")
        fill.style.backgroundColor = GROUP_COLORS[index]

        let percent = 0
        if (stats.students_count > 0) {
            percent = group.count / stats.students_count * 100
        }
        fill.style.width = `${percent}%`

        track.appendChild(fill)

        const count = document.createElement("span")
        count.classList.add("finish-group-count")
        count.textContent = `${group.count} / ${stats.students_count}`

        row.appendChild(label)
        row.appendChild(track)
        row.appendChild(count)

        finishGroupsList.appendChild(row)
    })
}


function fillTotals(stats) {
    finishPercent.textContent = `${stats.total_percent}%`
    finishTotal.textContent = `${stats.total_correct} із ${stats.total_answers} відповідей — правильні`

    let sectorPercent = 0
    if (stats.students_count > 0) {
        sectorPercent = Math.round(100 / stats.students_count)
    }

    finishNote.textContent = `Точність = правильні відповіді / усі запитання. Кожен сектор діаграми — 1 студент (${sectorPercent}%).`
}


async function loadFinishStats() {
    const response = await fetch(finishUrl)

    if (!response.ok) {
        return
    }

    const stats = await response.json()

    fillHead(stats)
    fillSelect(stats.students)
    buildTable(stats)
    drawFinishDonut(stats)
    buildGroups(stats)
    fillTotals(stats)
}


Chart.defaults.font.family = "Inter"

loadFinishStats()


const finishThemeObserver = new MutationObserver(updateFinishTheme)
finishThemeObserver.observe(document.body, { attributes: true, attributeFilter: ["class"] })