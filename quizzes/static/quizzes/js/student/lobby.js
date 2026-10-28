roomSocket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data)

    if (data.action == "quiz_started") {
        window.location.href = data.url
    }
})