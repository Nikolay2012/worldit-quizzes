const resultBox = document.querySelector(".result-box")
const correctValue = resultBox.querySelector(".result-value.correct")
const wrongValue = resultBox.querySelector(".result-value.wrong")
const skippedValue = resultBox.querySelector(".result-value.skipped")
const accuracyValue = resultBox.querySelector(".result-accuracy")
const resultPointsValue = resultBox.querySelector(".points-value")


function formatNumber(number) {
    return Number(number).toLocaleString("uk-UA")
}


function showStats(stats) {
    correctValue.textContent = stats.correct
    wrongValue.textContent = stats.wrong
    skippedValue.textContent = stats.skipped
    accuracyValue.textContent = stats.accuracy
    resultPointsValue.textContent = formatNumber(stats.points)
}


resultPointsValue.textContent = formatNumber(resultPointsValue.textContent)

roomSocket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data)

    if (data.action === "answer_result" && data.stats) {
        showStats(data.stats)
    }
})

document.addEventListener("question:changed", (event) => {
    if (event.detail.stats) {
        showStats(event.detail.stats)
    }
})