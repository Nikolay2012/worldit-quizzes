const timerBox = document.querySelector(".lobby")
const startSeconds = Number(timerBox.dataset.timeLeft)
const isAllAnswered = timerBox.dataset.timeStopped === "true"
const isPaused = timerBox.dataset.paused === "true"

let timerId = null


function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60)
    const rest = seconds % 60

    const mm = String(minutes).padStart(2, "0")
    const ss = String(rest).padStart(2, "0")

    return `${mm}:${ss}`
}


function showTime(seconds) {
    const timers = document.querySelectorAll(".timer-value")

    timers.forEach((timer) => {
        timer.textContent = formatTime(seconds)
    })
}


function timeUp() {
    const answers = document.querySelector(".answers")
    answers.classList.add("locked")

    document.dispatchEvent(new CustomEvent("question:timeup"))
}


function startTimer(seconds) {
    clearInterval(timerId)

    const endTime = Date.now() + seconds * 1000

    function tick() {
        const left = Math.ceil((endTime - Date.now()) / 1000)

        if (left <= 0) {
            showTime(0)
            clearInterval(timerId)
            timeUp()
            return
        }

        showTime(left)
    }

    tick()
    timerId = setInterval(tick, 250)
}

function stopTimer() {
    clearInterval(timerId)
}

function unlockAnswers() {
    const answers = document.querySelector(".answers")

    if (answers.querySelector(".chosen")) {
        return
    }

    answers.classList.remove("locked")
}

function applyTimeChange(data) {
    if (data.paused) {
        stopTimer()
        showTime(data.time_left)
        return
    }

    if (data.time_left > 0) {
        unlockAnswers()
    }

    startTimer(data.time_left)
}



if (isAllAnswered || isPaused) {
    showTime(startSeconds)
} else {
    startTimer(startSeconds)
}

document.addEventListener("question:changed", (event) => {
    startTimer(event.detail.time_left)
})

roomSocket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data)

    if (data.action === "answered") {
        if (data.total > 0 && data.answered >= data.total) {
            stopTimer()
        }
        return
    }

    if (data.action === "time_changed") {
        applyTimeChange(data)
    }
})